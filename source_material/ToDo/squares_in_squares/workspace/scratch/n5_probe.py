"""Scratch probe: what does a feasible n=5 state at L=2.7081 look like, and
which move reaches it?  Not part of the project's instruments."""
import math
import sys

import numpy as np

sys.path.insert(0, "scripts")
import packlib as P
import cram_relax as CR
from cent_discovery import rsa_seed
from sa_push import anneal, grid_seed
from oracle_basin import settle_to

N = 5
LT = 2.7081


def gate(st):
    r = P.verify([(float(a), float(b), float(c)) for a, b, c in np.asarray(st, float)])
    return bool(r["ok"]), float(r["worst_pen"]), float(r["L"])


def show(tag, st, f=None):
    ok, wp, L = gate(st)
    tagtxt = f"{tag:28s} E={f if f is None else round(f, 6)}"
    print(f"{tagtxt:50s} ok={ok} worst_pen={wp:+.3e} L={L:.6f}", flush=True)
    return ok, L


print("=== A: SA from grid seed, big budget ===")
for sd in range(1, 6):
    X, Y, TH = grid_seed(N, LT, 7919 * N + sd)
    anneal(X, Y, TH, LT, 120000, 7919 * N + sd, t0=0.05)
    st = np.column_stack([X, Y, TH])
    ok, L = show(f"sa seed{sd}", st)

print("=== B: rsa seed + settle_to ===")
for sd in range(1, 6):
    rng = np.random.RandomState(7919 * N + sd)
    q = rsa_seed(N, LT + 0.45, rng)
    q2, f = settle_to(q, LT, iters=250)
    st = np.column_stack([q2[:N], q2[N:2 * N], q2[2 * N:]])
    ok, L = show(f"rsa settle{sd}", st, f)

print("=== C: relax at hot t0 from rsa ===")
for sd in range(1, 6):
    rng = np.random.RandomState(7919 * N + sd)
    q = rsa_seed(N, LT + 0.45, rng)
    st = np.stack([q[:N], q[N:2 * N], q[2 * N:]], axis=1) % math.pi
    st = CR.relax(st, LT, moves=20000, seed=sd, t0=0.3)
    st, fixed, sw = CR.coordinate_polish(st, LT, sweeps=8)
    show(f"rsa hotrelax{sd}", st, CR.energy(st, LT))
