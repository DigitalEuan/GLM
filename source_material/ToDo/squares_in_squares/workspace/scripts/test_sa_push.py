#!/usr/bin/env python3
"""Self-test for sa_push penalty machinery against packlib + engine dynamics
on the two real usage patterns (Stage A compress, Stage B grid attack)."""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import packlib as P
from sa_push import (pair_pen_k, hw_vals, out_pen, total_pen, anneal,
                     final_max_overlap, grid_seed, moves_for, try_container)
from math import ceil, sqrt

# ---- Test 1: penalty math vs packlib (exactness)
X = np.array([0.5, 1.0]); Y = np.array([0.5, 0.35]); TH = np.array([0.0, np.pi/4])
HW = hw_vals(TH)
pk = pair_pen_k(0, X, Y, TH, HW)
st = [(float(x), float(y), float(t)) for x, y, t in zip(X, Y, TH)]
r = P.verify(st, tol=0.0)
assert r["ok"] is False and abs(r["worst_pen"] - pk[0]) < 1e-9, (r["worst_pen"], pk[0])
print("test1 exact penalty vs packlib: OK")

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

tab = json.load(open(ROOT + "/workspace/submission/table.json"))

# ---- Test 4a: Stage-A pattern — table n=30, compress 0.004, anneal
rec = tab["30"]
L0 = rec["L"]
X = np.array([q[0] for q in rec["state"]]) * (L0 - 0.004) / L0
Y = np.array([q[1] for q in rec["state"]]) * (L0 - 0.004) / L0
TH = np.array([q[2] for q in rec["state"]])
Lt = L0 - 0.004
t0 = time.time()
fin = anneal(X, Y, TH, Lt, moves=min(60000, moves_for(30)), seed=1)
dt = time.time() - t0
mo, mx = final_max_overlap(X, Y, TH, Lt)
st = [(float(x), float(y), float(t)) for x, y, t in zip(X, Y, TH)]
r = P.verify(st, tol=1e-9)
print(f"test4a: n=30 L={Lt:.6f} (table {L0:.6f}) obj={fin:.2e} max_ov={mo:.2e} "
      f"max_out={mx:.2e} packlib ok={r['ok']} pen={r['worst_pen']:.2e} ({dt:.1f}s)")
assert r["ok"] and r["L"] <= Lt + 1e-9, "stage-A pattern failed"

# ---- Test 4b: Stage-B pattern — grid seed at L = g - 0.02 for n=30 (g=6)
n = 30
g = ceil(sqrt(n))
Lt = g - 0.02
X, Y, TH = grid_seed(n, Lt, seed=12345)
t0 = time.time()
fin = anneal(X, Y, TH, Lt, moves=moves_for(n), seed=1)
dt = time.time() - t0
mo, mx = final_max_overlap(X, Y, TH, Lt)
st = [(float(x), float(y), float(t)) for x, y, t in zip(X, Y, TH)]
r = P.verify(st, tol=1e-9)
print(f"test4b: n=30 L={Lt:.4f} obj={fin:.2e} max_ov={mo:.2e} max_out={mx:.2e} "
      f"packlib ok={r['ok']} pen={r['worst_pen']:.2e} L={r['L']:.6f} ({dt:.1f}s)")
assert r["ok"] and r["L"] <= Lt + 1e-9, "stage-B pattern failed"

# ---- Test 4c: try_container wrapper on grid seed
X, Y, TH = grid_seed(n, g - 0.001, 7)
ok, stc, mo, mx = try_container(X, Y, TH, g - 0.001, 0, n)
r = P.verify(stc, tol=1e-9)
print(f"test4c: try_container ok={ok} (ov={mo:.2e} out={mx:.2e}) packlib ok={r['ok']} L={r['L']:.6f}")
assert ok and r["ok"] and r["L"] <= g - 0.001 + 1e-9
print("ALL sa_push self-tests passed")
