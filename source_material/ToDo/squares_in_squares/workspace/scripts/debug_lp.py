#!/usr/bin/env python3
"""debug_lp.py — diagnose the two Phase 1 failure modes.

A) n=12/13: LP feasible but the find was rejected — print the post-LP
   packlib worst_pen/out, the micro-descent effect, and the finalize
   result, to identify which acceptance gate blocked it.
B) n=6/695: LP infeasible — sweep (guard, dmax) variants, and if all
   fail, run a min-violation LP (shared slack s) to name the conflicting
   constraints; print their full 4-axis margins to see whether an
   alternative binding axis is plausible."""
import sys

import numpy as np
from scipy.optimize import linprog

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

sys.path.insert(0, ROOT + "/scripts")
import packlib as P
from cent_engines import (sat_margins, pen_matrix, out_amounts, hw,
                          engine_p11_piezo)
from lp_closure import lp_close, near_state, seeds_for


def show_state(X, Y, TH, L, tag):
    st = [(float(X[i]), float(Y[i]), float(TH[i])) for i in range(len(X))]
    r = P.verify(st)
    out = out_amounts(X, Y, hw(TH), L)
    print(f"  [{tag}] packlib worst_pen={r['worst_pen']:.3e} ok={r['ok']} "
          f"L={r['L']:.9f} max_out={float(np.max(out)):.3e}")
    return r


def part_a():
    print("=== A) n=13 @ 3.998, seed 7919*13+1 ===")
    n, L = 13, 3.998
    seed = seeds_for(n)[0]
    obj, X, Y, TH = near_state(n, L, seed)
    show_state(X, Y, TH, L, "engine+polish")
    ok, X2, Y2 = lp_close(X, Y, TH, L)
    print(f"  lp_close: {ok}")
    if ok:
        show_state(X2, Y2, TH, L, "post-LP")
        rng = np.random.RandomState(seed + 1)
        o3, X3, Y3, TH3 = engine_p11_piezo(X2, Y2, TH, L, rng,
                                           iters=150, eta=0.02, T0=0.0)
        show_state(X3, Y3, TH, L, "post-descent")
        st = [(float(X3[i]), float(Y3[i]), float(TH[i])) for i in range(n)]
        stf, rf = P.finalize(st, gap=2e-9)
        print(f"  finalize: ok={rf['ok']} worst_pen={rf['worst_pen']:.3e} "
              f"L={rf['L']:.12f} (target {L}, gate L+1e-6)")
        rr = P.verify(stf)
        print(f"  reverify finalized: worst_pen={rr['worst_pen']:.3e} "
              f"L={rr['L']:.12f}")


def lp_min_violation(X, Y, TH, L, dmax, guard):
    """Phase-I style: shared slack s >= 0; minimize s. Returns
    (status, s*, rows_info) where rows_info lists per-constraint
    violation at the optimum."""
    n = len(X)
    stack, dUi, dVi, dUj, dVj, Eu, EuT = sat_margins(X, Y, TH)
    pairval = stack.min(axis=0)
    B = stack.argmin(axis=0)
    cs, sn = np.cos(TH), np.sin(TH)
    iu = np.triu_indices(n, k=1)
    inc = pairval[iu] > -guard
    rows, rhs, meta = [], [], []
    EX = hw(TH)
    for t in range(len(iu[0])):
        if not inc[t]:
            continue
        i, j = int(iu[0][t]), int(iu[1][t])
        k = int(B[i, j])
        if k == 0:
            ax, ay, sig = cs[i], sn[i], np.sign(dUi[i, j]) or 1.0
            aname = f"u_{i}"
        elif k == 1:
            ax, ay, sig = -sn[i], cs[i], np.sign(dVi[i, j]) or 1.0
            aname = f"v_{i}"
        elif k == 2:
            ax, ay, sig = cs[j], sn[j], np.sign(dUj[i, j]) or 1.0
            aname = f"u_{j}"
        else:
            ax, ay, sig = -sn[j], cs[j], np.sign(dVj[i, j]) or 1.0
            aname = f"v_{j}"
        need = pairval[i, j]
        w = np.zeros(2 * n)
        w[2 * i] = -sig * ax; w[2 * i + 1] = -sig * ay
        w[2 * j] = sig * ax; w[2 * j + 1] = sig * ay
        rows.append(w)
        rhs.append(-need)
        meta.append((i, j, aname, need))
    lox = np.maximum(-dmax, EX - X)
    hix = np.minimum(dmax, L - EX - X)
    loy = np.maximum(-dmax, EX - Y)
    hiy = np.minimum(dmax, L - EX - Y)
    lo = np.empty(2 * n); lo[0::2] = lox; lo[1::2] = loy
    hi = np.empty(2 * n); hi[0::2] = hix; hi[1::2] = hiy
    if np.any(lo > hi + 1e-15):
        return "wall-bounds-empty", None, []
    A = np.array(rows)
    b = np.array(rhs)
    m = A.shape[0]
    A2 = np.hstack([A, -np.ones((m, 1))])
    c = np.zeros(2 * n + 1)
    c[-1] = 1.0
    res = linprog(c=c, A_ub=A2, b_ub=b,
                  bounds=list(zip(lo, hi)) + [(0, None)],
                  method="highs")
    if res.status != 0:
        return f"lp-status-{res.status}", None, []
    s = res.x[-1]
    viol = A @ res.x[:2 * n] - b
    info = [(meta[t][0], meta[t][1], meta[t][2], meta[t][3],
             float(viol[t])) for t in range(m)]
    info.sort(key=lambda r: -r[4])
    return "optimal", float(s), info


def part_b(n, L, label):
    print(f"=== B) n={n} @ {L} ({label}) ===")
    seed = seeds_for(n)[0]
    obj, X, Y, TH = near_state(n, L, seed)
    show_state(X, Y, TH, L, "engine+polish")
    for guard, dmax in ((0.05, 0.02), (0.025, 0.01), (0.02, 0.008),
                        (0.12, 0.05)):
        ok, _, _ = lp_close(X, Y, TH, L, dmax=dmax, guard=guard)
        print(f"  lp_close guard={guard} dmax={dmax}: "
              f"{'feasible' if ok else 'infeasible'}")
    status, s, info = lp_min_violation(X, Y, TH, L, dmax=0.02, guard=0.05)
    print(f"  min-violation LP: {status}, s*={s}")
    if s is not None and s > 0:
        stack, *_ = sat_margins(X, Y, TH)
        print(f"  top conflicting pairs (violation > 0.4*s*):")
        for (i, j, aname, need, v) in info:
            if v < 0.4 * s:
                break
            m4 = [stack[k][i, j] for k in range(4)]
            print(f"    pair ({i},{j}) binding={aname} need={need:.6f} "
                  f"viol={v:.6f}; margins u_i={m4[0]:.6f} v_i={m4[1]:.6f} "
                  f"u_j={m4[2]:.6f} v_j={m4[3]:.6f}")


if __name__ == "__main__":
    part_a()
    part_b(6, 2.998, "seed1")
    part_b(695, 26.998, "seed1")
