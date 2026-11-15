#!/usr/bin/env python3
"""debug_lorentz.py — resolve the obj/pen discrepancy in the Lorentz probe.

For the probe state: print (a) the engine's claimed obj, (b) a freshly
recomputed objective on the returned arrays, (c) packlib's worst_pen, and
(d) the worst pair (positions, angles) with its 4 SAT margins computed by
hand from both codes. Decides whether the substrate (pen_matrix) or the
engine bookkeeping disagrees with packlib."""
import math
import sys

import numpy as np

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

sys.path.insert(0, ROOT + "/scripts")
import packlib as P
from cent_engines import pen_matrix, out_amounts, hw, objective
from lorentz_lift import engine_lorentz, seed_local


def margins_pair(c0, t0, c1, t1):
    """4-axis SAT margins of pair (c0,t0),(c1,t1), by direct formula:
    margin_a = ext_i(a) + ext_j(a) - |(c_i - c_j).a| over the 4 edge
    normals a of the two squares."""
    e = [(math.cos(t0), math.sin(t0)), (-math.sin(t0), math.cos(t0)),
         (math.cos(t1), math.sin(t1)), (-math.sin(t1), math.cos(t1))]
    d = (c0[0] - c1[0], c0[1] - c1[1])
    out = []
    for (ux, uy) in e:                     # axis a = u
        hi = 0.5 * (abs(ux * e[0][0] + uy * e[0][1])
                    + abs(ux * e[1][0] + uy * e[1][1]))
        hj = 0.5 * (abs(ux * e[2][0] + uy * e[2][1])
                    + abs(ux * e[3][0] + uy * e[3][1]))
        out.append(hi + hj - abs(d[0] * ux + d[1] * uy))
    return out


def main():
    n, L, seed = 6, 2.998, 7919 * 6 + 1
    rng = np.random.RandomState(seed)
    X, Y, TH = seed_local(n, L, seed)
    obj, bX, bY, bTH = engine_lorentz(X, Y, TH, L, rng, rounds=3)
    stf = [(float(bX[i]), float(bY[i]), float(bTH[i]) % (math.pi / 2))
           for i in range(n)]
    r = P.verify(stf, tol=1e-9)
    fresh = objective(pen_matrix(bX, bY, bTH)[0],
                       out_amounts(bX, bY, hw(bTH), L))
    print(f"engine obj claim : {obj:.6e}")
    print(f"fresh objective  : {fresh:.6e}")
    print(f"packlib worst_pen: {r['worst_pen']:.6e}  ok={r['ok']} L={r['L']:.6f}")
    Pp, Mp = pen_matrix(bX, bY, bTH)
    iu = np.triu_indices(n, k=1)
    k = int(np.argmax(Pp[iu]))
    i, j = int(iu[0][k]), int(iu[1][k])
    print(f"worst pair by pen_matrix: ({i},{j}) pen={Pp[i, j]:.6f}")
    print(f"  square {i}: pos=({bX[i]:.6f},{bY[i]:.6f}) th={bTH[i] % (math.pi/2):.6f}")
    print(f"  square {j}: pos=({bX[j]:.6f},{bY[j]:.6f}) th={bTH[j] % (math.pi/2):.6f}")
    print(f"  hand 4-axis margins: "
          f"{[round(m, 6) for m in margins_pair((bX[i], bY[i]), bTH[i] % (math.pi/2), (bX[j], bY[j]), bTH[j] % (math.pi/2))]}")
    # packlib-side: worst pen per pair via its own verify on 2-square states
    for (a, b) in [(i, j)]:
        two = [(float(bX[a]), float(bY[a]), float(bTH[a]) % (math.pi / 2)),
               (float(bX[b]), float(bY[b]), float(bTH[b]) % (math.pi / 2))]
        rr = P.verify(two, tol=1e-9)
        print(f"  packlib on the isolated pair: worst_pen={rr['worst_pen']:.6e}")
    # per-pair scan: does any pair show pen_matrix > 0?
    tot = float(np.sum(Pp[iu] ** 2))
    print(f"pen_matrix total pair pen^2 = {tot:.6e}; "
          f"max = {float(np.max(Pp[iu])):.6e}")
    # packlib per-pair scan: find THE pair packlib says overlaps by 0.578
    print("packlib per-pair scan (worst_pen > 0.05):")
    for a in range(n):
        for b in range(a + 1, n):
            two = [(float(bX[a]), float(bY[a]), float(bTH[a]) % (math.pi / 2)),
                   (float(bX[b]), float(bY[b]), float(bTH[b]) % (math.pi / 2))]
            rr = P.verify(two, tol=1e-9)
            if rr["worst_pen"] > 0.05:
                hm = margins_pair((bX[a], bY[a]), bTH[a] % (math.pi / 2),
                                  (bX[b], bY[b]), bTH[b] % (math.pi / 2))
                print(f"  pair ({a},{b}): packlib={rr['worst_pen']:.6f} "
                      f"pen_matrix={Pp[a, b]:.6f} "
                      f"th=({bTH[a] % (math.pi/2):.4f},{bTH[b] % (math.pi/2):.4f}) "
                      f"pos=({bX[a]:.4f},{bY[a]:.4f})({bX[b]:.4f},{bY[b]:.4f}) "
                      f"handmargins={[round(m, 4) for m in hm]}")


if __name__ == "__main__":
    main()
