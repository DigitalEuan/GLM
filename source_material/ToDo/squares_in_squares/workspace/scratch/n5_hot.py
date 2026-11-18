"""Scratch: can a hot SA / kick loop reach n=5 at L=2.7081?"""
import math
import sys
import time

import numpy as np

sys.path.insert(0, "scripts")
import packlib as P
import cram_relax as CR
from cent_discovery import rsa_seed
from sa_push import anneal, grid_seed

N = 5
LT = 2.7081
PHI = math.pi / 2


def gate(st):
    r = P.verify([(float(a), float(b), float(c)) for a, b, c in np.asarray(st, float)])
    return bool(r["ok"]), float(r["worst_pen"]), float(r["L"])


t0 = time.time()
print("=== hot SA, 6 seeds x 400k moves from grid seed ===", flush=True)
bestall = None
for sd in range(1, 7):
    for tt in (0.15, 0.35):
        X, Y, TH = grid_seed(N, LT, 7919 * N + sd)
        anneal(X, Y, TH, LT, 400000, 7919 * N + sd + 13 * int(tt * 100),
               t0=tt, tend=1e-6, rotate_frac=0.5)
        st = np.column_stack([X, Y, TH])
        ok, wp, L = gate(st)
        print(f"  seed{sd} t0={tt}: ok={ok} worst_pen={wp:+.3e} L={L:.6f} "
              f"[{time.time()-t0:.0f}s]", flush=True)
        if bestall is None or (ok, -L) > bestall[0]:
            bestall = ((ok, -L), st)
        if ok and L <= LT:
            print("   FOUND from SA")
            print("   " + np.array2string(st, precision=4))
print("SA best:", gate(bestall[1]), f"[{time.time()-t0:.0f}s]")
