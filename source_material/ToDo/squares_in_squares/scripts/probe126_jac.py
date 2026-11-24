#!/usr/bin/env python3
r"""probe126_jac.py — is the batched gradient the same gradient, and cheaper?

Two questions, kept apart because they fail differently:

  correct  compare `patch_problem`'s jac at z0 with scipy's own 2-point
           `approx_derivative` on the same objective at the same point;
  cost     time one objective call, one batched jac call and one scipy
           finite-difference gradient, and report the pair count so a slow
           batch is explained by numbers rather than guessed at.

Run:  python3 scripts/probe126_jac.py [n ...]
"""
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import structure as ST       # noqa: E402
from scipy.optimize._numdiff import approx_derivative  # noqa: E402


def main(ns):
    for n in ns:
        X, Y, T, L0 = ST.load_pose(n)
        lo_x, hi_x, lo_y, hi_y = ST.box_for(float(L0), X, Y, T)
        idx = max(ST.patches(X, Y), key=len)
        obj, jac, z0, comp, c = ST.patch_problem(X, Y, T, idx, lo_x, hi_x, 1e5)
        V = 3 * c
        g_mod = np.asarray(jac(z0))
        g_ref = approx_derivative(obj, z0, method="2-point")
        denom = np.maximum(1.0, np.abs(g_ref))
        print(f"n={n:4d}  patch {c}  near {len(comp) - c}  vars {V}  "
              f"f(z0) {obj(z0):.6e}")
        print(f"  gradient: max|diff| {np.max(np.abs(g_mod - g_ref)):.3e}  "
              f"max rel {np.max(np.abs(g_mod - g_ref) / denom):.3e}  "
              f"|g|_inf {np.max(np.abs(g_ref)):.3e}  "
              f"shape {g_mod.shape}")

        reps = 20
        t0 = time.monotonic()
        for _ in range(reps):
            obj(z0)
        t_f = (time.monotonic() - t0) / reps
        t0 = time.monotonic()
        for _ in range(reps):
            jac(z0)
        t_j = (time.monotonic() - t0) / reps
        t0 = time.monotonic()
        for _ in range(5):
            approx_derivative(obj, z0, method="2-point")
        t_s = (time.monotonic() - t0) / 5
        print(f"  cost: obj {t_f * 1e3:.3f} ms  batched jac {t_j * 1e3:.3f} ms  "
              f"scipy FD {t_s * 1e3:.3f} ms  -> {t_s / t_j:.2f}x", flush=True)


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or [33, 439, 942])
