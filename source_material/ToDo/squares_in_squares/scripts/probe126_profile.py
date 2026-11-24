#!/usr/bin/env python3
r"""probe126_profile.py — where does a patch solve's ~400 ms go?

Run 125 measured one relaxation sweep at 5.3 s (n=33), 72.6 s (n=439) and
163.3 s (n=942), i.e. 374-410 ms per patch solve, against a 3 s per-attempt
budget.  Before changing the solver this probe attributes that time to named
stages, so the speedup is measured rather than assumed:

  near      the python loop that decides which outside cells a patch touches
  patching  `structure.patches` (the cell-to-patch masks, rebuilt per sweep)
  pen       `resqueeze.total_pen` (the O(n^2) pair pass, once per sweep)
  solve     `solve_patch_w` (L-BFGS-B with finite-difference gradients)

Each number is wall clock averaged over a few patches of the real pose.
"""
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import structure as ST       # noqa: E402
import resqueeze as RS       # noqa: E402


def probe(n, reps=3):
    X, Y, T, L0 = ST.load_pose(n)
    t0 = time.monotonic()
    order = ST.patches(X, Y)          # NOT (X, Y, T): T would land in `size`
    t_patches = time.monotonic() - t0
    sizes = [len(i) for i in order]

    # near-set cost, exactly as solve_patch_w builds it
    t0 = time.monotonic()
    total_near = 0
    for idx in order[:reps]:
        others = np.setdiff1d(np.arange(len(X)), idx)
        near = [o for o in others
                if np.min(np.abs(X[idx] - X[o]) + np.abs(Y[idx] - Y[o])) <= 2.6]
        total_near += len(near)
    t_near = (time.monotonic() - t0) / reps

    lo_x, hi_x, lo_y, hi_y = ST.box_for(float(L0), X, Y, T)
    t0 = time.monotonic()
    for idx in order[:reps]:
        ST.solve_patch_w(X, Y, T, idx, lo_x, hi_x, 1e5)
    t_solve = (time.monotonic() - t0) / reps

    t0 = time.monotonic()
    RS.total_pen(X, Y, T)
    t_pen = time.monotonic() - t0

    print(f"n={n:4d}  patches {len(order):4d}  cells/patch "
          f"min {min(sizes)} med {int(np.median(sizes))} max {max(sizes)}")
    print(f"  patches()   {t_patches * 1e3:8.1f} ms  (and it runs once per sweep)")
    print(f"  near loop   {t_near * 1e3:8.1f} ms  (avg {total_near / reps:.0f} near cells)")
    print(f"  solve_patch {t_solve * 1e3:8.1f} ms")
    print(f"  total_pen   {t_pen * 1e3:8.1f} ms  (once per sweep)")
    print(f"  -> per-patch total {(t_near + t_solve) * 1e3:.1f} ms; "
          f"sweep est {len(order) * (t_near + t_solve) + t_patches + t_pen:.1f} s",
          flush=True)
    return dict(n=n, patches=len(order), cells=[min(sizes), float(np.median(sizes)),
                                                max(sizes)],
                t_patches=t_patches, t_near=t_near, t_solve=t_solve, t_pen=t_pen)


if __name__ == "__main__":
    ns = [int(a) for a in sys.argv[1:]] or [33, 439, 942]
    for n in ns:
        probe(n)
