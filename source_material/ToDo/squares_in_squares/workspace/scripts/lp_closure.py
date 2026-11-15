#!/usr/bin/env python3
"""lp_closure.py — Phase 1 of the Run 7 strategic plan: exact closure of
the lift engine's residual frontier by linear programming.

Method (plan section 5.2): the compiled Lorentzian-lift engine (Run 7)
drives open targets to residual penetrations of 1.5e-4..8e-3 — the basin
is right, the closure is missing. For FIXED angles (the engine only ever
sets 0 or pi/4, per the 45-degree directive) the remaining problem in the
positions is a set of linear constraints:

  pair (i, j): choose the binding SAT axis a* (the one with the smallest
  margin = the axis the pair is closest to being separated on) and the
  sign sigma of the current projection; require
      sigma * ((c_i - c_j) . a*) >= ext_i(a*) + ext_j(a*)
  (linear in the positions; sigma and a* are taken from the near-state,
  where the projections are O(1) away from zero, so both are robust);

  walls: c_i +- hw_i within [0, L] (hw_i fixed by the angle);

  locality: |delta| <= dmax per coordinate, so pairs already separated by
  more than 2*dmax on their best axis can never collide and are omitted
  (guard = 0.05 > 2*dmax = 0.04).

The LP is a pure feasibility problem (HiGHS, primal feasibility 1e-11).
If feasible, the state is finalized (clearance scale 2e-9) and verified by
packlib; a find is accepted only if packlib says ok with worst_pen <= 0.

Commands:
  phase1        the 10 probe targets (grid-0.002 / grid-0.02 x {6,12,13,695,803})
  sweep         LOW band (69) then MID band (433), deepest-first per n
  apply [file]  merge finds into table.json (gobel pattern), re-assemble
                submission.csv, re-score; then regenerate the residue audit
  status        print the finds ledger
"""
import json
import math
import os
import subprocess
import sys
import time
from math import ceil, sqrt

import numpy as np
from scipy.optimize import linprog

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import packlib as P
from cent_engines import (sat_margins, pen_matrix, out_amounts, hw,
                          objective, engine_p11_piezo)
from lorentz_lift import engine_lorentz, seed_local

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

TAB = ROOT + "/workspace/submission/table.json"
PUSH = ROOT + "/workspace/push"
AUD = ROOT + "/download/residue_audit.json"


# ------------------------------------------------------------- near state
def near_state(n, L, seed, rounds=None, polish_iters=None):
    """engine + terminal pure descent. Returns (obj, X, Y, TH)."""
    if rounds is None:
        rounds = 3 if n < 100 else 2
    rng = np.random.RandomState(seed)
    X, Y, TH = seed_local(n, L, seed)
    obj, X, Y, TH = engine_lorentz(X, Y, TH, L, rng, rounds=rounds)
    if polish_iters is None:
        polish_iters = 500 if n < 100 else 240
    o2, X, Y, TH = engine_p11_piezo(X, Y, TH, L, rng,
                                    iters=polish_iters, eta=0.05, T0=0.0)
    if o2 < obj:
        obj = o2
    return obj, X, Y, TH


# ------------------------------------------------------------- LP closure
def lp_close(X, Y, TH, L, dmax=0.02, guard=0.05):
    """Feasibility LP for the positions, angles fixed.
    Returns (True, X2, Y2) or (False, None, None)."""
    n = len(X)
    stack, dUi, dVi, dUj, dVj, Eu, EuT = sat_margins(X, Y, TH)
    pairval = stack.min(axis=0)          # min margin over the 4 axes
    B = stack.argmin(axis=0)             # binding axis index per pair
    cs, sn = np.cos(TH), np.sin(TH)
    iu = np.triu_indices(n, k=1)
    inc = pairval[iu] > -guard           # include: near/separated by < guard
    rows, rhs = [], []
    EX = hw(TH)
    for t in range(len(iu[0])):
        if not inc[t]:
            continue
        i, j = int(iu[0][t]), int(iu[1][t])
        k = int(B[i, j])
        if k == 0:      # axis u_i
            ax, ay = cs[i], sn[i]
            sig = np.sign(dUi[i, j]) or 1.0
        elif k == 1:    # axis v_i
            ax, ay = -sn[i], cs[i]
            sig = np.sign(dVi[i, j]) or 1.0
        elif k == 2:    # axis u_j
            ax, ay = cs[j], sn[j]
            sig = np.sign(dUj[i, j]) or 1.0
        else:           # axis v_j
            ax, ay = -sn[j], cs[j]
            sig = np.sign(dVj[i, j]) or 1.0
        need = pairval[i, j]             # current margin on the binding axis
        w = np.zeros(2 * n)
        w[2 * i] = -sig * ax; w[2 * i + 1] = -sig * ay
        w[2 * j] = sig * ax; w[2 * j + 1] = sig * ay
        rows.append(w)
        rhs.append(-need)
    # walls + locality as variable bounds (INTERLEAVED: variable 2i is
    # x_i, 2i+1 is y_i — the wall bounds must follow that order)
    lox = np.maximum(-dmax, EX - X)
    hix = np.minimum(dmax, L - EX - X)
    loy = np.maximum(-dmax, EX - Y)
    hiy = np.minimum(dmax, L - EX - Y)
    lo = np.empty(2 * n); lo[0::2] = lox; lo[1::2] = loy
    hi = np.empty(2 * n); hi[0::2] = hix; hi[1::2] = hiy
    if np.any(lo > hi + 1e-15):
        return False, None, None         # wall violation beyond dmax
    A = np.array(rows) if rows else np.zeros((0, 2 * n))
    b = np.array(rhs) if rhs else np.zeros(0)
    res = linprog(c=np.zeros(2 * n), A_ub=A, b_ub=b,
                  bounds=list(zip(lo, hi)), method="highs",
                  options={"primal_feasibility_tolerance": 1e-10})
    if res.status != 0:
        return False, None, None
    d = res.x
    X2 = X + d[0::2].copy()
    Y2 = Y + d[1::2].copy()
    return True, X2, Y2


# ------------------------------------------------------------- repair search
def _axis_vec(k, i, j, cs, sn):
    if k == 0:
        return cs[i], sn[i]
    if k == 1:
        return -sn[i], cs[i]
    if k == 2:
        return cs[j], sn[j]
    return -sn[j], cs[j]


def _sig_for(k, i, j, dUi, dVi, dUj, dVj):
    if k == 0:
        return float(np.sign(dUi[i, j]) or 1.0)
    if k == 1:
        return float(np.sign(dVi[i, j]) or 1.0)
    if k == 2:
        return float(np.sign(dUj[i, j]) or 1.0)
    return float(np.sign(dVj[i, j]) or 1.0)


def pair_meta(X, Y, TH, guard=0.05, guard2=0.01):
    """Per included pair: binding axis data + alternative (2nd-best axis)
    when that axis is also near-binding (a genuine tie — flip candidate)."""
    n = len(X)
    stack, dUi, dVi, dUj, dVj, Eu, EuT = sat_margins(X, Y, TH)
    pairval = stack.min(axis=0)
    srt = np.argsort(stack, axis=0)      # per pair: axes by margin ascending
    B = stack.argmin(axis=0)
    cs, sn = np.cos(TH), np.sin(TH)
    iu = np.triu_indices(n, k=1)
    inc = pairval[iu] > -guard
    meta = []
    for t in range(len(iu[0])):
        if not inc[t]:
            continue
        i, j = int(iu[0][t]), int(iu[1][t])
        k = int(B[i, j])
        ax, ay = _axis_vec(k, i, j, cs, sn)
        sig = _sig_for(k, i, j, dUi, dVi, dUj, dVj)
        e = {"i": i, "j": j, "k": k, "ax": float(ax), "ay": float(ay),
             "sig": sig, "need": float(pairval[i, j])}
        k2 = int(srt[1, i, j])
        m2 = float(stack[k2, i, j])
        if m2 < guard2:
            ax2, ay2 = _axis_vec(k2, i, j, cs, sn)
            sig2 = _sig_for(k2, i, j, dUi, dVi, dUj, dVj)
            # the alternative carries the ORIGINAL as its own alt (reversible)
            e["alt"] = (k2, float(ax2), float(ay2), sig2, m2)
        meta.append(e)
    return meta


def _wall_bounds(X, Y, TH, L, dmax):
    EX = hw(TH)
    lox = np.maximum(-dmax, EX - X)
    hix = np.minimum(dmax, L - EX - X)
    loy = np.maximum(-dmax, EX - Y)
    hiy = np.minimum(dmax, L - EX - Y)
    lo = np.empty(2 * len(X)); lo[0::2] = lox; lo[1::2] = loy
    hi = np.empty(2 * len(X)); hi[0::2] = hix; hi[1::2] = hiy
    if np.any(lo > hi + 1e-15):
        return None, None
    return lo, hi


def _rows_from(meta, n):
    A = np.zeros((len(meta), 2 * n))
    b = np.zeros(len(meta))
    for t, e in enumerate(meta):
        i, j = e["i"], e["j"]
        ax, ay, sig = e["ax"], e["ay"], e["sig"]
        A[t, 2 * i] = -sig * ax; A[t, 2 * i + 1] = -sig * ay
        A[t, 2 * j] = sig * ax;  A[t, 2 * j + 1] = sig * ay
        b[t] = -e["need"]
    return A, b


def _solve_min(A, b, lo, hi):
    """min-violation LP: shared slack s >= 0 on all pair rows."""
    m = A.shape[0]
    A2 = np.hstack([A, -np.ones((m, 1))])
    c = np.zeros(A2.shape[1]); c[-1] = 1.0
    res = linprog(c=c, A_ub=A2, b_ub=b,
                  bounds=list(zip(lo, hi)) + [(0, None)],
                  method="highs",
                  options={"primal_feasibility_tolerance": 1e-10})
    if res.status != 0:
        return None, None, None
    viol = A @ res.x[:len(lo)] - b
    return float(res.x[-1]), res.x[:len(lo)], viol


def repair_close(X, Y, TH, L, dmax=0.02, guard=0.05, guard2=0.01,
                 max_iter=15, cand=3):
    """Binding-axis repair: while the min-violation LP is blocked, flip
    the most-conflicted near-tied pairs to their second axis; accept a
    flip only if it strictly lowers s*. Returns
    (ok, X2, Y2, info) with info in {'direct', 'trivial', 'walls', 'lp',
    'lp2', ('stuck', s)}."""
    n = len(X)
    lo, hi = _wall_bounds(X, Y, TH, L, dmax)
    if lo is None:
        return False, None, None, "walls"
    meta = pair_meta(X, Y, TH, guard, guard2)
    if not meta:
        return True, X.copy(), Y.copy(), "trivial"
    A, b = _rows_from(meta, n)
    s, x, viol = _solve_min(A, b, lo, hi)
    if s is None:
        return False, None, None, "lp"
    n_flip = 0
    for it in range(max_iter):
        if s <= 1e-9:
            break
        order_rows = sorted(range(len(meta)), key=lambda t: -viol[t])
        cands = [t for t in order_rows
                 if viol[t] > 0.3 * s and "alt" in meta[t]][:cand]
        if not cands:
            break
        best = None
        for t in cands:
            e = dict(meta[t])
            k2, ax2, ay2, sig2, m2 = e["alt"]
            old = (e["k"], e["ax"], e["ay"], e["sig"], e["need"])
            e.update(k=k2, ax=ax2, ay=ay2, sig=sig2, need=m2, alt=old)
            meta2 = meta[:t] + [e] + meta[t + 1:]
            A2r, b2 = _rows_from(meta2, n)
            s2, x2, viol2 = _solve_min(A2r, b2, lo, hi)
            if s2 is not None and (best is None or s2 < best[0]):
                best = (s2, t, meta2, x2, viol2)
            if s2 is not None and s2 <= 1e-9:
                break
        if best is None or best[0] >= s - 1e-12:
            break
        s, _, meta, _, viol = best
        n_flip += 1
    if s <= 1e-9:
        A, b = _rows_from(meta, n)
        res = linprog(c=np.zeros(2 * n), A_ub=A, b_ub=b,
                      bounds=list(zip(lo, hi)), method="highs",
                      options={"primal_feasibility_tolerance": 1e-10})
        if res.status == 0:
            d = res.x
            return True, X + d[0::2], Y + d[1::2], f"repair:{n_flip}"
        return False, None, None, "lp2"
    return False, None, None, ("stuck", round(s, 9), n_flip)


def angle_search(X, Y, TH, L, dmax=0.02, guard=0.05, guard2=0.01,
                 max_iter=20, cand=4):
    """Small-n fallback: try flipping each square 0 <-> pi/4 (the two
    45-degree family members); brief polish; LP+repair. Keep the best
    obstruction s. Returns (ok, X2, Y2, TH2, info)."""
    n = len(X)
    best = None

    def ladder(X0, Y0, TH0):
        ok, X2, Y2 = lp_close(X0, Y0, TH0, L, dmax=dmax, guard=guard)
        if ok:
            return ok, X2, Y2, "lp"
        ok, X2, Y2, info = repair_close(X0, Y0, TH0, L, dmax=dmax,
                                        guard=guard, guard2=guard2,
                                        max_iter=max_iter, cand=cand)
        return ok, X2, Y2, info

    ok, X2, Y2, info = ladder(X, Y, TH)
    if ok:
        return ok, X2, Y2, TH, info
    if isinstance(info, tuple):
        best = (info[1], X, Y, TH, info)
    for i in range(n):
        TH2 = TH.copy()
        TH2[i] = (math.pi / 4.0) if TH2[i] == 0.0 else 0.0
        # nudge off the exact site so the descent can move it
        rng = np.random.RandomState(1000 + i)
        X3, Y3 = X.copy(), Y.copy()
        X3[i] += rng.normal(0, 0.01); Y3[i] += rng.normal(0, 0.01)
        o, X3, Y3, TH3 = engine_p11_piezo(X3, Y3, TH2, L, rng,
                                          iters=120, eta=0.1, T0=0.0)
        ok, X4, Y4, info = ladder(X3, Y3, TH3)
        if ok:
            return ok, X4, Y4, TH3, info
        if isinstance(info, tuple) and best is not None and info[1] < best[0]:
            best = (info[1], X3, Y3, TH3, info)
    if best is not None:
        return False, None, None, None, ("best_stuck", best[0])
    return False, None, None, None, "no_alt"


def attempt(n, L, seeds, rounds=None, polish_iters=None, small_angle_search=True):
    """Try seeds until one closes. Ladder per seed:
    LP -> repair -> (small n) angle flips. Returns (record, find|None)."""
    rec = {"n": n, "L_target": L, "seeds": [], "find": None}

    def accept(X2, Y2, THv, seed):
        st = [(float(X2[i]), float(Y2[i]), float(THv[i])) for i in range(n)]
        r = P.verify(st, tol=1e-9)
        if not (r["ok"] and r["worst_pen"] <= 1e-10):
            rng = np.random.RandomState(seed + 1)
            o3, X3, Y3, TH3 = engine_p11_piezo(X2, Y2, THv, L, rng,
                                               iters=80, eta=0.03, T0=0.0)
            st = [(float(X3[i]), float(Y3[i]), float(TH3[i]))
                  for i in range(n)]
            r = P.verify(st, tol=1e-9)
            if r["ok"] and r["worst_pen"] <= 1e-10:
                X2, Y2, THv = X3, Y3, TH3
        if not (r["ok"] and r["worst_pen"] <= 1e-10):
            return None
        stf, rf = P.finalize(st, gap=2e-9)
        if rf["ok"] and rf["worst_pen"] <= 0 and rf["L"] < L + 1e-6:
            return {"n": n, "L": round(rf["L"], 12), "state": stf,
                    "src": f"lorentzLP:{L:.6f}", "seed": seed}
        return None

    for seed in seeds:
        t0 = time.time()
        obj, X, Y, TH = near_state(n, L, seed, rounds=rounds,
                                   polish_iters=polish_iters)
        Pp, _ = pen_matrix(X, Y, TH)
        worst_pen = float(np.max(Pp)) if Pp.size else 0.0
        out = out_amounts(X, Y, hw(TH), L)
        worst_out = float(np.max(out))
        ent = {"seed": seed, "obj": round(float(obj), 9),
               "pen": round(worst_pen, 9), "out": round(worst_out, 9)}
        ok, X2, Y2 = lp_close(X, Y, TH, L)
        mode = "lp"
        info = None
        if not ok:
            ok, X2, Y2, info = repair_close(X, Y, TH, L)
            mode = "repair"
        if not ok and small_angle_search and n <= 30:
            ok, X2, Y2, TH2, info = angle_search(X, Y, TH, L)
            mode = "angle"
        ent["mode"] = mode
        ent["info"] = info if not isinstance(info, tuple) else list(info)
        if ok:
            f = accept(X2, Y2, TH if mode != "angle" else TH2, seed)
            if f:
                ent["final_L"] = f["L"]
                rec["find"] = f
        ent["t"] = round(time.time() - t0, 1)
        rec["seeds"].append(ent)
        if rec["find"]:
            break
    return rec


# ------------------------------------------------------------- phases
def seeds_for(n, count=3):
    base = [7919 * n + 1, 104729 * n + 3, 32452843 * n + 7]
    return [s % 4294967295 for s in base[:count]]


def phase1():
    targets = []
    for n in (6, 12, 13, 695, 803):
        g = P.grid_L(n)
        targets.append((n, round(g - 0.02, 6)))
        targets.append((n, round(g - 0.002, 6)))
    only = int(sys.argv[2]) if len(sys.argv) > 2 else None
    if only:
        targets = [(n, L) for n, L in targets if n == only]
    out = []
    finds = []
    path = os.path.join(PUSH, "lp_phase1.json")
    # cheap first (small n), and within each n the 0.002 depth (phase gate)
    # before 0.02
    targets = sorted(targets, key=lambda t: (t[0], -t[1]))
    for n, L in targets:
        seeds = seeds_for(n)
        rec = attempt(n, L, seeds)
        out.append(rec)
        if rec["find"]:
            finds.append(rec["find"])
        json.dump({"phase": "1", "targets": out, "finds": finds},
                  open(path, "w"), indent=1)          # crash-safe progress
        f = rec["find"]
        for s in rec["seeds"]:
            print(f"  seed {s['seed']}: pen={s['pen']:.2e} mode={s['mode']} "
                  f"info={s.get('info')} t={s['t']}s"
                  + (f" -> L={f['L']:.9f}" if f else ""), flush=True)
        print(f"n={n} L={L}: "
              + (f"FIND L={f['L']:.9f}" if f else "no close"), flush=True)
    print(f"phase1: {len(finds)} finds of {len(targets)} targets")


def sweep(limit_per_class=None, time_budget=None, resume=True):
    aud = json.load(open(AUD))
    low = sorted(r["n"] for r in aud["rows"] if r["class"] == "LOW")
    # MID: largest blocks first (value per puzzle grows with k, per plan)
    mid = sorted((r["n"] for r in aud["rows"] if r["class"] == "MID"),
                 reverse=True)
    tab = json.load(open(TAB))
    groups = [("LOW", low), ("MID", mid)]
    if limit_per_class:
        groups = [(c, lst[:limit_per_class]) for c, lst in groups]
    results, finds = [], []
    t_start = time.time()
    path = os.path.join(PUSH, "lp_sweep.json")
    done = set()
    if resume and os.path.exists(path):
        old = json.load(open(path))
        results = old.get("results", [])
        finds = old.get("finds", [])
        done = {r["n"] for r in results}
        print(f"[sweep] resume: {len(done)} already done, "
              f"{len(finds)} finds on record")
    for cls, lst in groups:
        for n in lst:
            if n in done:
                continue
            if time_budget and time.time() - t_start > time_budget:
                print(f"[sweep] time budget reached at n={n} ({cls})")
                break
            cur = tab[str(n)]["L"]
            g = P.grid_L(n)
            best = None
            for L in (round(g - 0.002, 6), round(g - 0.02, 6)):
                if best:
                    break
                if L >= cur - 1e-9:
                    continue
                seeds = seeds_for(n, 2)
                rec = attempt(n, L, seeds)
                if rec["find"]:
                    best = rec["find"]
                    finds.append(best)
            results.append({"n": n, "class": cls, "cur": cur,
                            "find": best and best["L"]})
            json.dump({"results": results, "finds": finds},
                      open(path, "w"), indent=1)      # crash-safe progress
            tag = f"FIND {best['L']:.9f}" if best else "-"
            print(f"[sweep] {cls} n={n} cur={cur}: {tag}", flush=True)
    print(f"sweep: {len(finds)} finds; results -> {path}")


def apply(file=None):
    src = json.load(open(file or os.path.join(PUSH, "lp_sweep.json")))
    # accept either {"finds": [...]} (sweep) or the same key (phase1)
    finds = src["finds"] if isinstance(src, dict) else src
    tab = json.load(open(TAB))
    applied = []
    for f in finds:
        n = f["n"]
        cur = tab[str(n)]["L"]
        if f["L"] >= cur - 1e-9:
            continue
        stf = f["state"]
        assert len(stf) == n
        r = P.verify(stf)
        assert r["ok"] and r["worst_pen"] <= 0, (n, r)
        assert abs(r["L"] - f["L"]) < 1e-9, (n, r["L"], f["L"])
        tab[str(n)] = {"L": round(r["L"], 12), "state": stf,
                       "src": f["src"]}
        applied.append((n, cur, r["L"]))
    print(f"applied {len(applied)}:")
    for n, cur, new in applied:
        print(f"  n={n}: {cur:.9f} -> {new:.9f}")
    if applied:
        json.dump(tab, open(TAB, "w"))
        subprocess.run([sys.executable,
                        os.path.join(HERE, "final_assembly.py")], check=True)
        subprocess.run([sys.executable,
                        os.path.join(HERE, "score_submission.py")], check=True)
        subprocess.run([sys.executable,
                        os.path.join(HERE, "residue_audit.py")], check=True)


def status():
    for name in ("lp_phase1.json", "lp_sweep.json"):
        p = os.path.join(PUSH, name)
        if os.path.exists(p):
            d = json.load(open(p))
            print(f"{name}: {len(d.get('finds', []))} finds")
            for f in d.get("finds", []):
                print(f"  n={f['n']} L={f['L']} src={f['src']}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "phase1"
    if cmd == "phase1":
        phase1()
    elif cmd == "sweep":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
        budget = float(sys.argv[3]) if len(sys.argv) > 3 else None
        sweep(limit, budget)
    elif cmd == "apply":
        apply(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "status":
        status()
    else:
        print(__doc__)
