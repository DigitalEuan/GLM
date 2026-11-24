#!/usr/bin/env python3
r"""resqueeze.py — run 116: dynamic re-squeeze block substitution.

The lead the Director's Note opens: fixed-box substitution failed because the
block was asked to hold one more cell in its *own* compressed box (run 115:
short by 2.2e-5..8.9e-5, and s(7) = 3 makes the 3x3 case a theorem).  The
dynamic version lets the whole pose pay instead of the block:

  1. take the band's frontier pose (side L = k - delta, m* cells),
  2. insert one cell at the best free-space point (void_insert's exact scan),
  3. run PATCH-COORDINATE relaxation with the container hinged at k - margin:
     every cell is inside some patch (patches overlap 50 %), each patch is
     solved on its own 3 c variables against all its contacts, sweeps repeat in
     random orders.  Overlapping patches are what makes the squeeze *global*:
     room taken from one region is offered to the next, which a single local
     move cannot do.
  4. judge at 40 digits: legal and side < k is a beat; otherwise report the
     residual penetration, which is the honest distance to one.

Float use: discovery only (like relax_angles.py).  Verdicts are true_geom's.
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
from void_insert import load_pose, pen_vec, hmax_scan, refine, frontier_rows  # noqa: E402

TAB = os.path.join(ROOT, "workspace/submission/table.json")
OUT = os.path.join(ROOT, "workspace/push/resqueeze116.json")


def total_pen(X, Y, T, eps=1e-9, reach=1.9):
    """Penetration over the pairs that can matter (centres within reach)."""
    dx = np.abs(X[:, None] - X[None, :])
    dy = np.abs(Y[:, None] - Y[None, :])
    iu = np.triu(np.abs(dx) + np.abs(dy) <= reach, k=1)
    i, j = np.nonzero(iu)
    if len(i) == 0:
        return 0.0, 0.0
    pen = pen_vec(X[i], Y[i], T[i], X[j], Y[j], T[j], eps=eps)
    return float((pen ** 2).sum()), float(pen.max())


def patches(X, Y, size=3.0, step=1.5):
    """Overlapping square patches of cells, by centre position."""
    out = []
    lo_x, hi_x = X.min(), X.max()
    lo_y, hi_y = Y.min(), Y.max()
    x = lo_x
    while x < hi_x:
        y = lo_y
        while y < hi_y:
            idx = np.nonzero((X >= x) & (X <= x + size) & (Y >= y) & (Y <= y + size))[0]
            if len(idx) >= 2:
                out.append(idx)
            y += step
        x += step
    return out


def solve_patch(X, Y, T, idx, lo, hi, iters=140, eps=1e-9):
    """Relax one patch (3 c variables) against every cell it touches."""
    from scipy.optimize import minimize
    n = len(X)
    others = np.setdiff1d(np.arange(n), idx)
    near = []
    for o in others:
        if np.min(np.abs(X[idx] - X[o]) + np.abs(Y[idx] - Y[o])) <= 2.6:
            near.append(o)
    near = np.array(near, dtype=int)
    if len(near) == 0:
        return X, Y, T, 0.0
    c = len(idx)

    def obj(z):
        Xa, Ya, Ta = X.copy(), Y.copy(), T.copy()
        Xa[idx], Ya[idx], Ta[idx] = z[:c], z[c:2 * c], z[2 * c:]
        pen = pen_vec(np.repeat(Xa[idx], len(near)), np.repeat(Ya[idx], len(near)),
                      np.repeat(Ta[idx], len(near)),
                      np.tile(Xa[near], c), np.tile(Ya[near], c), np.tile(Ta[near], c),
                      eps=eps)
        hx = 0.5 * (np.abs(np.cos(Ta[idx])) + np.abs(np.sin(Ta[idx])))
        over = (np.clip(Xa[idx] + hx - hi, 0, None) ** 2
                + np.clip(lo - Xa[idx] + hx, 0, None) ** 2
                + np.clip(Ya[idx] + hx - hi, 0, None) ** 2
                + np.clip(lo - Ya[idx] + hx, 0, None) ** 2)
        return float((pen ** 2).sum() + 1e5 * over.sum())

    z0 = np.concatenate([X[idx], Y[idx], T[idx]])
    res = minimize(obj, z0, method="L-BFGS-B",
                   options={"maxiter": iters, "ftol": 1e-17, "gtol": 1e-13})
    Xa, Ya, Ta = X.copy(), Y.copy(), T.copy()
    Xa[idx], Ya[idx], Ta[idx] = res.x[:c], res.x[c:2 * c], res.x[2 * c:]
    return Xa, Ya, Ta, float(res.fun)


def global_obj(X, Y, T, lo, hi, eps=1e-9):
    """The whole pose's penalty: every pair plus the container."""
    pen, pmax = total_pen(X, Y, T, eps=eps)
    hx = 0.5 * (np.abs(np.cos(T)) + np.abs(np.sin(T)))
    over = float((np.clip(X + hx - hi, 0, None) ** 2 + np.clip(lo - X + hx, 0, None) ** 2
                  + np.clip(Y + hx - hi, 0, None) ** 2 + np.clip(lo - Y + hx, 0, None) ** 2).sum())
    return pen + 1e5 * over, pen, over


def run_band(k, m, sweeps=4, restarts=2, seed=116, size=3.0, step=1.5, margin=0.0,
             insert=True):
    """Patch-coordinate re-squeeze.  `insert=False` is the control: the pose
    alone must stay legal (pen 0) and keep its side, or the instrument is unsound."""
    per = SQ.load()
    x, y, t = load_pose(m)
    Lf = SQ.extent(per[m])
    if insert:
        st, box = hmax_scan(x, y, t, grid=110, angles=21)
        h, cx, cy, th = refine(x, y, t, st, box)
        X = np.append(x, cx)
        Y = np.append(y, cy)
        T = np.append(t, th)
    else:
        X, Y, T, h = x.copy(), y.copy(), t.copy(), 0.0
    lo, hi = None, None
    # The target is k itself, NOT k - margin: any side strictly below k is a beat,
    # and the frontier pose already sits at k - delta with delta ~ 1e-3..1e-2.  A
    # 1e-3 margin forces an impossible squeeze and the wall penalty then outweighs
    # the overlaps (the control caught exactly that: a legal pose destroyed, pen
    # 0.59, 234 violations).
    kk = SQ.grid(m + 1)
    half = (kk - margin) / 2.0
    xmid = 0.5 * (float(x.min()) + float(x.max()))
    ymid = 0.5 * (float(y.min()) + float(y.max()))
    lo_x, hi_x = xmid - half, xmid + half
    lo_y, hi_y = ymid - half, ymid + half
    lo, hi = lo_x, hi_x
    rng = np.random.RandomState(seed)
    best = None
    for r in range(restarts):
        Xa, Ya, Ta = X.copy(), Y.copy(), T.copy()
        if r:
            Xa = Xa + rng.normal(scale=2e-4, size=Xa.shape)
            Ya = Ya + rng.normal(scale=2e-4, size=Ya.shape)
        for s in range(sweeps):
            order = patches(Xa, Ya, size=size, step=step)
            rng.shuffle(order)
            g_old = global_obj(Xa, Ya, Ta, lo_x, hi_x)[0]
            accepted = 0
            for idx in order:
                Xn, Yn, Tn, _ = solve_patch(Xa, Ya, Ta, idx, lo_x, hi_x)
                g_new = global_obj(Xn, Yn, Tn, lo_x, hi_x)[0]
                if g_new < g_old - 1e-15:       # acceptance test: monotone, never diverge
                    Xa, Ya, Ta = Xn, Yn, Tn
                    g_old = g_new
                    accepted += 1
            pen, pmax = total_pen(Xa, Ya, Ta)
            side = float(max((Xa + 0.5 * (np.abs(np.cos(Ta)) + np.abs(np.sin(Ta)))).max()
                             - (Xa - 0.5 * (np.abs(np.cos(Ta)) + np.abs(np.sin(Ta)))).min(),
                             (Ya + 0.5 * (np.abs(np.cos(Ta)) + np.abs(np.sin(Ta)))).max()
                             - (Ya - 0.5 * (np.abs(np.cos(Ta)) + np.abs(np.sin(Ta)))).min()))
            print(f"    k={k} r={r} sweep {s}: pen {pen:.3e} (max {pmax:.2e}) side {side:.9f}"
                  f"  accepted {accepted}/{len(order)}", flush=True)
            if best is None or pen < best[0]:
                best = (pen, Xa.copy(), Ya.copy(), Ta.copy(), side)
            if pen < 1e-24:
                break
    pen, Xb, Yb, Tb, side = best
    rows = [(str(float(a)), str(float(b)), str(float(c))) for a, b, c in zip(Xb, Yb, Tb)]
    chk = TG.check(rows)
    rec = {"k": k, "frontier_n": m, "n": len(Xb), "insert_side": 2 * h,
           "L_frontier": Lf, "pen_final": pen, "side_float": side,
           "side40": str(+chk["side"]), "violations": len(chk["violations"]),
           "grid_k": kk,
           "beat": bool(len(chk["violations"]) == 0 and chk["side"] < kk)}
    return rec


def main():
    per = SQ.load()
    fr = dict(frontier_rows(per))
    ks = [int(a) for a in sys.argv[1:]] or [23, 32, 26]
    out = []
    for k in ks:
        print(f"  band k={k} (frontier {fr[k]}) ...", flush=True)
        rec = run_band(k, fr[k])
        print(f"  -> n={rec['n']} side40 {rec['side40']} viol {rec['violations']} "
              f"pen {rec['pen_final']:.3e}  {'BEAT' if rec['beat'] else 'no beat'}", flush=True)
        out.append(rec)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
