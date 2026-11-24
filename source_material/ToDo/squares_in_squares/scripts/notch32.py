#!/usr/bin/env python3
r"""notch32.py — run 117: the k = 32 notch with a HARD side constraint and a
contact-graph repair.

Run 116 left n = 999 at side 31.996876 (3.1e-3 inside k = 32, worth 9.9e-5) with
17 violations and max penetration 9.4e-2, using a *penalty* wall.  Two fixes,
both from the Director's Note:

  HARD PROJECTION.  The container is never a penalty here: after every move each
  cell is clamped exactly into the box
        x in [lo + hx, hi - hx],  hx = (|cos t| + |sin t|)/2,
  so a state is only ever reported that satisfies the side constraint exactly.
  The objective is penetration alone.

  CONTACT-GRAPH REPAIR.  After the sweeps, the violating pairs are read off the
  exact SAT separation, sorted by depth, and each is attacked by sliding one of
  its two cells by exactly the amount that closes that pair along its best
  separating axis, then re-projecting into the box.  A move is kept only if the
  total violation (count, then squared depth) strictly improves — a descent on
  the contact graph, not a re-sweep of a smooth penalty.

Judged by true_geom at 40 digits.  A legal state with side < 32 is a beat for
n = 999 and the candidate is written out for C1/C2.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sqscore as SQ                  # noqa: E402
import true_geom as TG                # noqa: E402
from void_insert import load_pose, pen_vec, hmax_scan, refine  # noqa: E402

TAB = os.path.join(ROOT, "workspace/submission/table.json")
OUT = os.path.join(ROOT, "workspace/push/notch32_117.json")
CAND = os.path.join(ROOT, "workspace/push/notch32_candidate.json")

K = 32
FRONTIER = 998          # band k = 32 frontier; n = 999 is the next row


def near_pairs(X, Y, reach=1.6):
    dx = np.abs(X[:, None] - X[None, :])
    dy = np.abs(Y[:, None] - Y[None, :])
    iu = np.triu(dx + dy <= reach, k=1)
    return np.nonzero(iu)


def violations(X, Y, T, eps=1e-9):
    """(penetration array, pair (i,j) arrays) for every overlapping pair."""
    i, j = near_pairs(X, Y)
    pen = pen_vec(X[i], Y[i], T[i], X[j], Y[j], T[j], eps=0.0)
    m = pen > eps
    return pen[m], i[m], j[m]


def clamp(X, Y, T, lo, hi):
    """HARD side projection: every cell's bbox is clamped into [lo, hi]^2."""
    h = 0.5 * (np.abs(np.cos(T)) + np.abs(np.sin(T)))
    X = np.clip(X, lo + h, hi - h)
    Y = np.clip(Y, lo + h, hi - h)
    return X, Y


def solve_patch(X, Y, T, idx, lo, hi, iters=140, eps=1e-9):
    """Penetration-only descent on one patch, then a hard clamp."""
    from scipy.optimize import minimize
    n = len(X)
    others = np.setdiff1d(np.arange(n), idx)
    near = [o for o in others
            if np.min(np.abs(X[idx] - X[o]) + np.abs(Y[idx] - Y[o])) <= 1.8]
    near = np.array(near, dtype=int)
    c = len(idx)
    if len(near) == 0:
        return X, Y, T

    def obj(z):
        Xa, Ya, Ta = X.copy(), Y.copy(), T.copy()
        Xa[idx], Ya[idx], Ta[idx] = z[:c], z[c:2 * c], z[2 * c:]
        pen = pen_vec(np.repeat(Xa[idx], len(near)), np.repeat(Ya[idx], len(near)),
                      np.repeat(Ta[idx], len(near)),
                      np.tile(Xa[near], c), np.tile(Ya[near], c), np.tile(Ta[near], c),
                      eps=eps)
        return float((pen ** 2).sum())

    z0 = np.concatenate([X[idx], Y[idx], T[idx]])
    res = minimize(obj, z0, method="L-BFGS-B",
                   options={"maxiter": iters, "ftol": 1e-17, "gtol": 1e-13})
    Xn, Yn, Tn = X.copy(), Y.copy(), T.copy()
    Xn[idx], Yn[idx], Tn[idx] = res.x[:c], res.x[c:2 * c], res.x[2 * c:]
    Xn, Yn = clamp(Xn, Yn, Tn, lo, hi)          # the constraint is never negotiated
    return Xn, Yn, Tn


def build(k=K, m=FRONTIER):
    per = SQ.load()
    x, y, t = load_pose(m)
    Lf = SQ.extent(per[m])
    st, box = hmax_scan(x, y, t, grid=140, angles=33)
    h, cx, cy, th = refine(x, y, t, st, box, rounds=6)
    X = np.append(x, cx)
    Y = np.append(y, cy)
    T = np.append(t, th)
    half = k / 2.0
    xmid = 0.5 * (float(x.min()) + float(x.max()))
    ymid = 0.5 * (float(y.min()) + float(y.max()))
    return X, Y, T, (xmid - half, xmid + half), Lf, 2 * h


def sweeps(X, Y, T, lo, hi, rounds=3, size=4.5, step=2.5, seed=117):
    rng = np.random.RandomState(seed)
    n = len(X)
    for r in range(rounds):
        order = []
        x = X.min()
        while x < X.max():
            y = Y.min()
            while y < Y.max():
                idx = np.nonzero((X >= x) & (X <= x + size) & (Y >= y) & (Y <= y + size))[0]
                if len(idx) >= 2:
                    order.append(idx)
                y += step
            x += step
        rng.shuffle(order)
        before = score(X, Y, T, 1e-9)
        accepted = 0
        for idx in order:
            Xn, Yn, Tn = solve_patch(X, Y, T, idx, lo, hi)
            got = score(Xn, Yn, Tn, 1e-9)
            if got < before:                    # monotone acceptance: never diverge
                X, Y, T, before = Xn, Yn, Tn, got
                accepted += 1
        print(f"    sweep {r}: viol {before[0]} sumsq {before[1]:.3e} max {before[2]:.3e}"
              f"  accepted {accepted}/{len(order)}", flush=True)
    return X, Y, T


def score(Xa, Ya, Ta, eps=1e-9):
    """(violating pairs, sum of squared depth, deepest) — the repair's descent."""
    pen, _, _ = violations(Xa, Ya, Ta, eps)
    return (len(pen), float((pen ** 2).sum()), float(pen.max()) if len(pen) else 0.0)


def repair(X, Y, T, lo, hi, passes=60, eps=1e-9, step_extra=1e-9, top=12):
    """Contact-graph descent: close the deepest violating pairs by exact slides.

    For a pair (a, b) the exact slide of `a` along the best separating axis q is
    `sign(proj) * (want + eps - |proj|)` with `want = h_a(q) + h_b(q)`, which makes
    that pair exactly tangent; the move is kept only if the whole pose's score
    (count, then squared depth) strictly improves.  Only the deepest `top` pairs
    are attempted per pass, so a pass stays cheap.
    """
    def local_score(Xa, Ya, Ta):
        pen, _, _ = violations(Xa, Ya, Ta, eps)
        return (len(pen), float((pen ** 2).sum()), float(pen.max()) if len(pen) else 0.0)

    cur = local_score(X, Y, T)
    for p in range(passes):
        pen, i, j = violations(X, Y, T, eps)
        if len(pen) == 0:
            break
        order = np.argsort(pen)[::-1][:top]
        improved = False
        for q in order:
            a, b = int(i[q]), int(j[q])
            for move in (a, b):
                other = b if move == a else a
                # the axis that separates this pair best, and the exact slide
                ct, st = math.cos(T[move]), math.sin(T[move])
                co, so = math.cos(T[other]), math.sin(T[other])
                best = None
                for (qx, qy) in ((ct, st), (-st, ct), (co, so), (-so, co)):
                    gA = abs(ct * qx + st * qy) + abs(-st * qx + ct * qy)
                    hB = 0.5 * (abs(co * qx + so * qy) + abs(-so * qx + co * qy))
                    proj = (X[move] - X[other]) * qx + (Y[move] - Y[other]) * qy
                    want = 0.5 * gA + hB + eps
                    need = want - abs(proj)
                    if best is None or need < best[0]:
                        best = (need, qx, qy, 1.0 if proj >= 0 else -1.0)
                need, qx, qy, sgn = best
                if need <= 0:
                    continue
                Xn, Yn, Tn = X.copy(), Y.copy(), T.copy()
                Xn[move] += sgn * (need + step_extra) * qx
                Yn[move] += sgn * (need + step_extra) * qy
                Xn, Yn = clamp(Xn, Yn, Tn, lo, hi)
                got = local_score(Xn, Yn, Tn)
                if got < cur:
                    X, Y, T, cur = Xn, Yn, Tn, got
                    improved = True
                    break
        print(f"    repair {p}: viol {cur[0]} sumsq {cur[1]:.3e} max {cur[2]:.3e}"
              f"{'  (improved)' if improved else '  (stuck — no single slide helps)'}", flush=True)
        if not improved:
            break
    return X, Y, T


def main():
    X, Y, T, (lo, hi), Lf, insert_side = build()
    print(f"  frontier 998 side {Lf:.9f}; inserted cell side {insert_side:.4f}; "
          f"box side {hi - lo:.6f} (= k = {K})", flush=True)
    pen0, _, _ = violations(X, Y, T)
    print(f"  start: viol {len(pen0)} max {pen0.max() if len(pen0) else 0:.3e}", flush=True)
    # repair first: the insertion is nearly legal (a handful of pairs), and a
    # penalty sweep is the wrong tool for a handful of exact slides
    X, Y, T = repair(X, Y, T, lo, hi)
    nv = len(violations(X, Y, T)[0])
    if nv:
        print(f"  still {nv} violations after repair — one constrained sweep", flush=True)
        X, Y, T = sweeps(X, Y, T, lo, hi, rounds=2)
        X, Y, T = repair(X, Y, T, lo, hi)
    pen, _, _ = violations(X, Y, T)
    rows = [(str(float(a)), str(float(b)), str(float(c))) for a, b, c in zip(X, Y, T)]
    chk = TG.check(rows)
    rec = {"k": K, "n": len(X), "L_frontier": Lf, "insert_side": insert_side,
           "violations_sat": int(len(pen)),
           "max_pen": float(pen.max()) if len(pen) else 0.0,
           "side40": str(+chk["side"]), "violations40": len(chk["violations"]),
           "beat": bool(len(chk["violations"]) == 0 and chk["side"] < K)}
    print(f"\n  FINAL n={rec['n']} side40 {rec['side40']}  "
          f"viol40 {rec['violations40']}  sat viol {rec['violations_sat']} "
          f"max pen {rec['max_pen']:.3e}  -> "
          f"{'BEAT (+%.3e score)' % ((K - float(chk['side'])) / math.sqrt(999)) if rec['beat'] else 'no beat'}",
          flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(rec, open(OUT, "w"), indent=1)
    if rec["beat"]:
        json.dump({"n": rec["n"], "state": rows, "side": rec["side40"]},
                  open(CAND, "w"), indent=1)
        print(f"  candidate written to {CAND}", flush=True)
    return rec


if __name__ == "__main__":
    main()
