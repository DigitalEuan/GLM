#!/usr/bin/env python3
r"""positive_control.py — can the settle engine EVER break grid from a
grid seed by pressure alone?

Targets: the two smallest open grid-tied n whose below-grid optima are
famous and simple:
  n=5:  optimum 2.7071 (45° square + 4 corner squares)
  n=11: optimum 3.8771 (literature value; atlas best.json line 198;
        imported as table 11 -> 3.877083591506)

CORRECTION (run 21): an earlier session mislabelled the 3.8771 value
as 'n=12: 45° 3x3 block + 3 corner squares'.  That construction is
geometrically impossible: a 3x3 block tilted 45° has bounding box
3*sqrt(2) = 4.2426 > 3.8771, and n=12's verified optimum is the
4.0 grid (run-20 stall law + atlas: 'no beat after finalize').  The
3.8771 value belongs to n=11; the control below therefore targets
n=5 (sub-grid optimum exists) and n=12 (no sub-grid optimum: the
honest target is the grid itself, 4.0).

Protocol: clean grid seed at L=grid-0.004 (S1-style, zero jitter), hot
settle (t0=0.02, rotate_frac=0.5), 40k moves/call (n small -> fast),
Delta-Sigma steps dL=4e-3, up to 10 calls, 3 seeds per target.
If even these fail, pressure-alone is structurally incapable of crossing
the wall anywhere in this problem — the honest verdict for the fork.
"""
import json
import sys
import time
from math import ceil, sqrt

import numpy as np

sys.path.insert(0, "/home/z/my-project/scripts")
from delta_sigma_push import DeltaSigma
from sa_push import anneal, final_max_overlap

TAB = "/home/z/my-project/workspace/submission/table.json"


def clean_grid_seed(n, L):
    k = int(ceil(sqrt(n)))
    X = np.empty(n); Y = np.empty(n); TH = np.empty(n)
    p = 0
    for i in range(n):
        X[p] = (i % k + 0.5)
        Y[p] = (i // k + 0.5)
        TH[p] = 0.0
        p += 1
    return X, Y, TH


def settle(n, grid, moves, calls_max, t0):
    L = float(grid) - 0.004
    L_floor = sqrt(n) + 1e-9
    best = None
    for seed_base in range(3):
        ds = DeltaSigma(4e-3)
        X, Y, TH = clean_grid_seed(n, grid)
        Lc = L
        jams = 0
        calls = 0
        while jams < 3 and calls < calls_max:
            L_try = max(Lc - ds.dl, L_floor)
            X2, Y2, T2 = X.copy(), Y.copy(), TH.copy()
            seed = 7919 * n + 104729 * calls + 13 * seed_base
            anneal(X2, Y2, T2, L_try, moves, seed, t0=t0, tend=1e-4,
                   rotate_frac=0.5)
            mo, mxo = final_max_overlap(X2, Y2, T2, L_try)
            calls += 1
            if mo < 1e-10 and mxo < 1e-12:
                Lc = L_try
                X, Y, TH = X2, Y2, T2
                jams = 0
                ds.step(True)
                best = (Lc, [[float(a), float(b), float(c)]
                             for a, b, c in zip(X2, Y2, T2)])
            else:
                jams += 1
                ds.step(False)
        if best is not None:
            return best, calls
    return best, calls


def main():
    tab = json.load(open(TAB))
    out = {}
    # n=5: sub-grid optimum exists (2.7071); n=12: no sub-grid optimum
    # exists (verified optimum is the grid 4.0) — the control measures
    # whether pressure can even reach grid-0.004 for n=12 (it should:
    # 3.996 > 4.0 is false; the honest expectation is FAIL, consistent
    # with the stall law)
    for n, grid, known in ((5, 3, 2.707106781), (12, 4, 4.0)):
        rec = tab[str(n)]
        t0 = time.time()
        best, calls = settle(n, grid, 40000, 10, 0.02)
        r = {"n": n, "grid": grid, "known": known, "table_L": rec["L"],
             "best_L": best[0] if best else None, "calls": calls,
             "seconds": round(time.time() - t0, 1)}
        out[str(n)] = r
        if best:
            print(f"n={n}: PRESSURE BROKE GRID: {grid} -> {best[0]:.6f} "
                  f"(known {known:.6f}) in {calls} calls, {r['seconds']}s")
        else:
            print(f"n={n}: FAILED (0/10 calls OK x3 seeds, {r['seconds']}s) "
                  f"— cannot reach {grid}-0.004; known optimum {known:.6f} "
                  f"({'sub-grid optimum exists' if known < grid else 'the grid itself — no sub-grid packing exists'})")
    json.dump(out, open("/tmp/positive_control.json", "w"), indent=1)


if __name__ == "__main__":
    main()
