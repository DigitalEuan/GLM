#!/usr/bin/env python3
r"""rotation_lp.py — the two levers the failures named (GLM round, 15 Nov 2026).

The contact-graph LP compacted 400 frontier puzzles without improving one.  That
is not a failed search, it is a *measurement*: a record packing is contact-tight,
so its polytope minimum is the value it already has.  Two things were frozen
there that the packing never asked to freeze:

1. **Orientation.**  Every engine in this tree held θ still while it moved
   centres.  Here θ moves too.  With δ_i the rotation of square i and axis u_i,
   the pair condition

       σ (c_j − c_i)·u_i  ≥  ½ + ½ f(Δ),      f(Δ) = |cos Δ| + |sin Δ|,  Δ = θ_j − θ_i

   is linear to first order, because a rotation only bends the *support* of the
   other square (the square's own support along its own edge is ½, exactly):

       σ[(c_j − c_i)·u_i + d·v_i δ_i]  −  ½f'(Δ)(δ_j − δ_i)  ≥  ½ + ½f(Δ)

   and the walls bend the same way, x_i + h(θ_i) ≤ L with h(θ) = ½(|cos θ|+|sin θ|).
   Variables are (Δx, Δy, δ, ΔL).  The LP is solved, the *exact* verifier judges
   the result, and a rejected step retries with half the rotation budget — so the
   first-order model can never buy a phantom improvement.

2. **Contact topology.**  Axis and sign of every pair were read off the current
   geometry and then frozen.  A rewire move *rewrites* those specs: for a few
   near contacts the pair is re-specified on another SAT axis or on the opposite
   side, and the LP solves the arrangement that would satisfy that contact graph.
   This is the move a family template structurally cannot make — it changes who
   touches whom, not a parameter.  (Two closed forms in this tree once produced
   185 and 90+ phantom wins by getting exactly this wrong; the verifier is the
   only authority here.)

Accepted states go through `packlib.finalize` + `packlib.verify`.

Usage:
    python3 scripts/rotation_lp.py --selftest
    python3 scripts/rotation_lp.py --run --max-n 200 --rounds 5
    python3 scripts/rotation_lp.py --run --max-n 60 --rewire 12
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import packlib as P                                      # noqa: E402


# --------------------------------------------------------------- geometry kit
def support(t: float) -> float:
    return 0.5 * (abs(math.cos(t)) + abs(math.sin(t)))


def dsupport(t: float) -> float:
    c, s = math.cos(t), math.sin(t)
    return 0.5 * (-s * math.copysign(1.0, c) + c * math.copysign(1.0, s))


def fang(d: float) -> float:
    return abs(math.cos(d)) + abs(math.sin(d))


def dfang(d: float) -> float:
    h = 1e-7
    return (fang(d + h) - fang(d - h)) / (2 * h)


def bbox_L(state) -> float:
    xs = np.array([s[0] for s in state]); ys = np.array([s[1] for s in state])
    e = np.array([support(s[2]) for s in state])
    return float(max(np.max(xs + e) - np.min(xs - e), np.max(ys + e) - np.min(ys - e)))


def contact_table(state, touch: float):
    """Per near pair: (i, j, fam, sigma, margin, d0, axis(ax,ay), perp(vx,vy), E0, Eang)."""
    cur = np.asarray(state, dtype=float)
    n = len(cur)
    ct = cur[:, 2]
    cth, sth = np.cos(ct), np.sin(ct)
    xy = cur[:, :2]
    PU = np.stack([cth, sth], axis=1) @ xy.T             # PU[i,j] = c_j . u_i
    PV = np.stack([-sth, cth], axis=1) @ xy.T
    Eu = 0.5 * (np.abs(np.outer(cth, cth) + np.outer(sth, sth))
                + np.abs(np.outer(-sth, cth) + np.outer(cth, sth)))
    dU = np.diag(PU)[:, None] - PU                       # dU[i,j] = (c_i - c_j).u_i
    dV = np.diag(PV)[:, None] - PV
    M = np.stack([np.abs(dU) - (0.5 + Eu), np.abs(dV) - (0.5 + Eu),
                  (np.abs(dU) - (0.5 + Eu)).T, (np.abs(dV) - (0.5 + Eu)).T])
    D = np.stack([dU, dV, dU.T, dV.T])
    best = np.argmax(M, axis=0)
    margin = np.take_along_axis(M, best[None], 0)[0]
    dval = np.take_along_axis(D, best[None], 0)[0]
    ii, jj = np.where(np.triu(margin, 1) <= touch)
    out = []
    for i, j in zip(ii, jj):
        f = int(best[i, j]); i = int(i); j = int(j)
        sg = math.copysign(1.0, float(dval[i, j]))
        if f < 2:
            owner, other = i, j
            d0 = xy[j] - xy[i]
            ax, ay = (cth[i], sth[i]) if f == 0 else (-sth[i], cth[i])
            delta = ct[j] - ct[i]
        else:
            owner, other = j, i
            d0 = xy[i] - xy[j]
            ax, ay = (cth[j], sth[j]) if f == 2 else (-sth[j], cth[j])
            delta = ct[i] - ct[j]
        E0 = 0.5 + 0.5 * fang(delta)
        Eang = 0.5 * dfang(delta)
        out.append({"i": i, "j": j, "fam": f, "sigma": sg, "margin": float(margin[i, j]),
                    "d0": (float(d0[0]), float(d0[1])), "axis": (float(ax), float(ay)),
                    "owner": owner, "other": other, "E0": E0, "Eang": Eang})
    return out


# ------------------------------------------------------------------- the LP
def step_lp(state, rot: float, touch: float, overrides=None, pos: float = 0.08):
    """One linearised compaction step with rotation free; None if infeasible."""
    cur = np.asarray(state, dtype=float)
    n = len(cur)
    ct = cur[:, 2]
    rows, b = [], []

    def add(pairs, rhs):
        v = np.zeros(3 * n + 1)
        for k, c in pairs:
            v[k] += c
        rows.append(v); b.append(rhs)

    # walls:  dx_i + h' δ_i − t ≤ L0 − x_i − h ;  −dx_i + h' δ_i ≤ x_i − h
    L0 = bbox_L([tuple(map(float, q)) for q in cur])
    for i in range(n):
        x, y, t = cur[i]
        h, hd = support(t), dsupport(t)
        add([(i, 1.0), (2 * n + i, hd), (3 * n, -1.0)], L0 - x - h)
        add([(i, -1.0), (2 * n + i, hd)], x - h)
        add([(n + i, 1.0), (2 * n + i, hd), (3 * n, -1.0)], L0 - y - h)
        add([(n + i, -1.0), (2 * n + i, hd)], y - h)

    for c in contact_table(cur, touch):
        i, j, own, oth = c["i"], c["j"], c["owner"], c["other"]
        sg, E0, Eang = c["sigma"], c["E0"], c["Eang"]
        ax, ay = c["axis"]
        d0 = c["d0"]
        if overrides and (i, j) in overrides:
            f2, sg2 = overrides[(i, j)]
            own2, oth2 = (i, j) if f2 < 2 else (j, i)
            d2 = (cur[j, :2] - cur[i, :2]) if f2 < 2 else (cur[i, :2] - cur[j, :2])
            ax2 = ((math.cos(ct[own2]), math.sin(ct[own2])) if f2 % 2 == 0
                   else (-math.sin(ct[own2]), math.cos(ct[own2])))
            delta = ct[oth2] - ct[own2]
            own, oth, sg = own2, oth2, sg2
            ax, ay = ax2
            d0 = (float(d2[0]), float(d2[1]))
            E0 = 0.5 + 0.5 * fang(delta)
            Eang = 0.5 * dfang(delta)
        base = sg * (d0[0] * ax + d0[1] * ay)
        vx, vy = -ay, ax
        d_dot_v = d0[0] * vx + d0[1] * vy
        # H = σ[base + (dx_oth − dx_own)·a + (d0·v) δ_own] − E0 − Eang δ_oth + Eang δ_own
        coefs = [(own, sg * ax), (oth, -sg * ax),
                 (n + own, sg * ay), (n + oth, -sg * ay),
                 (2 * n + own, sg * d_dot_v + Eang),
                 (2 * n + oth, -Eang)]
        add([(k, -v) for k, v in coefs], sg * base - E0)

    cvec = np.zeros(3 * n + 1); cvec[-1] = 1.0
    bounds = [(-pos, pos)] * (2 * n) + [(-rot, rot)] * n + [(None, None)]
    res = linprog(cvec, A_ub=np.array(rows), b_ub=np.array(b), bounds=bounds,
                  method="highs")
    if not res.success:
        return None
    out = cur.copy()
    out[:, 0] += res.x[:n]
    out[:, 1] += res.x[n:2 * n]
    out[:, 2] += res.x[2 * n:3 * n]
    return out


def separate(state, iters: int = 300, step: float = 0.5):
    """Geometric repair: push overlapping pairs apart along their binding axis.

    The linearised LP cannot repair a badly overlapped state (its position bounds
    are per step, and infeasibility returns nothing), so a state that starts
    overlapped — an injected grain, a random start — is relaxed here first.
    """
    cur = np.asarray(state, dtype=float).copy()
    n = len(cur)
    for _ in range(iters):
        r = P.verify([tuple(map(float, q)) for q in cur])
        if r["ok"]:
            return cur, r
        cs = contact_table(cur, touch=1.0)
        moved = False
        for c in cs:
            if c["margin"] >= -1e-12:
                continue
            i, j = c["i"], c["j"]
            ax, ay = c["axis"]
            sg = c["sigma"]
            pen = -c["margin"]
            # owner sits on the +sigma*a side: push it further out, the other in
            own, oth = (i, j) if c["owner"] == i else (j, i)
            cur[own, 0] += sg * ax * pen * step
            cur[own, 1] += sg * ay * pen * step
            cur[oth, 0] -= sg * ax * pen * step
            cur[oth, 1] -= sg * ay * pen * step
            moved = True
        if not moved:
            break
    return cur, P.verify([tuple(map(float, q)) for q in cur])


def compact(state, rounds: int = 5, touch: float = 0.06, rot: float = 0.02,
            overrides=None, pos: float = 0.08):
    """Iterate the rotation-relaxed LP; accepted steps are exactly verified."""
    cur = np.asarray(state, dtype=float)
    start = P.verify([tuple(map(float, q)) for q in cur])
    if not start["ok"]:
        cur, start = separate(cur)
    # an overlapping start is legal here: the linearised constraints *are*
    # separation conditions, so the LP repairs the state as part of compacting it
    best = start if start["ok"] else None
    bestL = start["L"] if start["ok"] else float("inf")
    log = []
    for _ in range(rounds):
        trial, r = None, None
        for attempt in range(3):
            cand = step_lp(cur, rot / (2 ** attempt), touch, overrides, pos)
            if cand is None:
                continue
            r = P.verify([tuple(map(float, q)) for q in cand])
            if r["ok"]:
                trial = cand
                break
        if trial is None:
            break
        if r["L"] >= bestL - 1e-12:
            if best is not None:
                break
            cur, log = trial, log + [(round(r["L"], 9), rot)]   # repair step
            continue
        cur, best, bestL = trial, r, r["L"]
        log.append((round(r["L"], 9), rot))
    if best is None:
        best = P.verify([tuple(map(float, q)) for q in cur])
    return cur, best, log


def rewire(state, trials: int = 12, rounds: int = 2, touch: float = 0.06,
           seed: int = 0, max_flip: int = 2):
    """Contact-topology search: rewrite a few contact specs, re-solve, verify."""
    rng = np.random.default_rng(seed)
    cur = np.asarray(state, dtype=float)
    best = P.verify([tuple(map(float, q)) for q in cur])
    cs = contact_table(cur, touch)
    if not cs:
        return cur, best, 0
    for _ in range(trials):
        picks = rng.choice(len(cs), size=min(max_flip, len(cs)), replace=False)
        ov = {}
        for p in picks:
            c = cs[int(p)]
            ov[(c["i"], c["j"])] = (int(rng.integers(0, 4)),
                                    -c["sigma"] if rng.random() < 0.5 else c["sigma"])
        cand, r, _ = compact(cur, rounds=rounds, touch=touch, overrides=ov)
        if r["ok"] and r["L"] < best["L"] - 1e-12:
            best, cur = r, cand
    return cur, best, trials


# --------------------------------------------------------------------- driver
def run(max_n: int, rounds: int, touch: float, rot: float, rew: int,
        min_n: int = 1) -> int:
    sub = P.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    tab = {n: P.verify(sub[n])["L"] for n in range(1, 1001)
           if n in sub and len(sub[n]) == n}
    wins, tried, moved = [], 0, 0
    t0 = time.time()
    for n in sorted(tab):
        if n > max_n or n < min_n:
            continue
        tried += 1
        state = np.array([(x, y, t) for x, y, t in sub[n]], dtype=float)
        before = tab[n]
        cand, r, log = compact(state, rounds=rounds, touch=touch, rot=rot)
        if rew:
            cand2, r2, _ = rewire(cand, trials=rew, rounds=2, touch=touch, seed=n)
            if r2["ok"] and r2["L"] < r["L"] - 1e-12:
                cand, r = cand2, r2
        if r["ok"] and r["L"] < before - 1e-9:
            fin, rr = P.finalize([tuple(map(float, q)) for q in cand])
            if rr["ok"] and rr["L"] < before - 1e-9:
                gain = (before - rr["L"]) / math.sqrt(n)
                wins.append({"n": n, "L_before": before, "L_after": rr["L"],
                             "gain": gain,
                             "state": [[float(a), float(b), float(c)] for a, b, c in fin]})
                print(f"  WIN n={n}: {before:.9f} -> {rr['L']:.9f} gain {gain:.3e}"
                      f" ({time.time()-t0:.0f}s)", flush=True)
        if log:
            moved += 1
    path = os.path.join(ROOT, "workspace/push/rotation_lp_results.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"found": wins, "rows_tried": tried, "rows_compacted": moved,
               "score_gain": sum(w["gain"] for w in wins)},
              open(path, "w"), indent=1)
    print(f"rows tried: {tried}; rows that compacted: {moved}; wins: {len(wins)}; "
          f"gain {sum(w['gain'] for w in wins):.9f}; wrote {path}")
    return 0


def selftest() -> int:
    st = [(0.5, 0.5, 0.0), (1.5, 0.5, 0.0)]
    cand, r, _ = compact(np.array(st), rounds=3)
    assert r["ok"], r
    print(f"selftest pair: ok={r['ok']} L={r['L']:.6f}")
    k, g = P.grid_packing(9)
    cand, r, _ = compact(np.array([(x, y, t) for x, y, t in g]), rounds=3)
    assert r["ok"], r
    assert r["L"] >= 3.0 - 1e-9, r
    print(f"selftest grid9: ok={r['ok']} L={r['L']:.6f} (grid 3.0)")
    # a deliberately loose state must compact back toward the grid
    loose = [(x * 1.3, y * 1.3, t) for x, y, t in g]
    cand, r, _ = compact(np.array(loose), rounds=5)
    print(f"selftest loose grid9: L={r['L']:.6f} ok={r['ok']}")
    assert r["ok"] and r["L"] < 3.0 * 1.3, r
    print("selftests passed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--max-n", type=int, default=200)
    ap.add_argument("--min-n", type=int, default=1)
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--touch", type=float, default=0.06)
    ap.add_argument("--rot", type=float, default=0.02)
    ap.add_argument("--rewire", type=int, default=0)
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.run:
        return run(args.max_n, args.rounds, args.touch, args.rot, args.rewire,
                   args.min_n)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
