"""Scratch: basin measurement at n=5, L=2.7081.

(1) random starts -> L-BFGS: how often is a feasible state found?
(2) from the E=0.034 attractor, random single-body 45-deg rotations -> L-BFGS:
    does any land in the feasible set?
"""
import math
import sys
import time

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, "scripts")
import packlib as P
import cram_relax as CR

N = 5
LT = 2.7081
PHI = math.pi / 2
OUTW = 4.0


def energy(q, L):
    X, Y, TH = q[:N], q[N:2 * N], q[2 * N:]
    st = np.stack([X, Y, TH], axis=1)
    pen = np.maximum(CR.margin_matrix(st), 0.0)
    iu = np.triu_indices(N, 1)
    HW = 0.5 * (np.abs(np.cos(TH)) + np.abs(np.sin(TH)))
    w = np.maximum(np.maximum(HW - X, X + HW - L), 0.0)
    w2 = np.maximum(np.maximum(HW - Y, Y + HW - L), 0.0)
    return float(np.dot(pen[iu], pen[iu]) + OUTW * np.dot(w + w2, w + w2))


def lbfgs(q, L, maxiter=300):
    best = [np.asarray(q, float).copy(), 1e18]

    def f(v):
        e = energy(v, L)
        if e < best[1] - 1e-18:
            best[0], best[1] = np.asarray(v, float).copy(), e
        return e

    res = minimize(f, np.asarray(q, float), method="L-BFGS-B",
                   options={"maxiter": maxiter, "ftol": 1e-16, "gtol": 1e-12})
    if res.fun < best[1]:
        return res.x, float(res.fun)
    return best[0], float(best[1])


def gate_st(q):
    st = np.stack([q[:N], q[N:2 * N], q[2 * N:]], axis=1)
    r = P.verify([(float(a), float(b), float(c)) for a, b, c in st])
    return bool(r["ok"]), float(r["worst_pen"]), float(r["L"]), st


t0 = time.time()
print("=== (1) random starts ===", flush=True)
rng = np.random.RandomState(2026)
es = []
feas = 0
for k in range(300):
    th = rng.uniform(0, PHI, N)
    hw = 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))
    x = rng.uniform(hw, LT - hw)
    y = rng.uniform(hw, LT - hw)
    q = np.concatenate([x, y, th])
    q, e = lbfgs(q, LT)
    es.append(e)
    if e < 1e-12:
        feas += 1
        print("FEASIBLE at start", k, gate_st(q)[:3], flush=True)
print(f"random starts: {feas}/300 feasible; median E={np.median(es):.3e} "
      f"min={min(es):.3e} [{time.time()-t0:.0f}s]", flush=True)

print("=== (2) rotations of the attractor ===", flush=True)
# rebuild the attractor: random start, L-BFGS (all seeds converge there)
th = rng.uniform(0, PHI, N)
q = np.concatenate([rng.uniform(0.6, LT - 0.6, N), rng.uniform(0.6, LT - 0.6, N), th])
q, e = lbfgs(q, LT)
q, e = lbfgs(q, LT)
ok, wp, L, st = gate_st(q)
print("attractor:", ok, f"wp={wp:+.4e} L={L:.6f} E={e:.4e}", flush=True)
print(np.array2string(st, precision=4), flush=True)
feas = 0
for k in range(300):
    q2 = q.copy()
    i = k % N
    q2[2 * N + i] = (q2[2 * N + i] + rng.choice([-1, 1]) * PHI / 4) % PHI
    q2, e2 = lbfgs(q2, LT)
    if e2 < 1e-12:
        feas += 1
        print("FEASIBLE via rotation", k, gate_st(q2)[:3], flush=True)
print(f"rotation kicks: {feas}/300 feasible [{time.time()-t0:.0f}s]", flush=True)
