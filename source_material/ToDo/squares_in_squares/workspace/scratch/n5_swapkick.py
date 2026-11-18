"""Scratch: does the swap+rotate collective kick escape the n=5 attractor?"""
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
    return bool(r["ok"]), float(r["worst_pen"]), float(r["L"])


def strain(q, L):
    st = np.stack([q[:N], q[N:2 * N], q[2 * N:]], axis=1)
    return CR.local_strain(st, L)


def kick(q, L, rng, mode):
    """Most strained bodies swapped/rotated, inside the box."""
    s = q.copy()
    m = 1 + rng.randint(3)
    order = list(np.argsort(strain(q, L))[::-1][:m])
    if mode == "swap":
        pos = np.stack([s[order], s[N + np.array(order)]], axis=1)
        perm = rng.permutation(len(order))
        for a, i in enumerate(order):
            s[i], s[N + i] = pos[perm[a]]
    elif mode == "reslot":
        for i in order:
            att = (rng.choice([0.0, PHI / 2, PHI / 4, -PHI / 4])) % PHI
            hw = 0.5 * (abs(math.cos(att)) + abs(math.sin(att)))
            s[i] = rng.uniform(hw, L - hw)
            s[N + i] = rng.uniform(hw, L - hw)
            s[2 * N + i] = att
    for i in order:                                   # rotate
        s[2 * N + i] = (s[2 * N + i] + rng.choice([-1, 1]) * PHI / 4) % PHI
    # keep inside the box
    th = s[2 * N:]
    hw = 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))
    s[:N] = np.clip(s[:N], hw, L - hw)
    s[N:2 * N] = np.clip(s[N:2 * N], hw, L - hw)
    return s


rng = np.random.RandomState(2026)
q = np.concatenate([rng.uniform(0.6, LT - 0.6, N), rng.uniform(0.6, LT - 0.6, N),
                    rng.uniform(0, PHI, N)])
q, e = lbfgs(q, LT)
q, e = lbfgs(q, LT)
print("attractor:", gate_st(q), f"E={e:.4e}", flush=True)
t0 = time.time()
for mode in ("swap", "reslot"):
    feas = 0
    best = 1e9
    for k in range(150):
        q2, e2 = lbfgs(kick(q, LT, rng, mode), LT)
        ok, wp, L = gate_st(q2)
        best = min(best, e2)
        if e2 < 1e-12:
            feas += 1
            print(f"  {mode} FEASIBLE trial {k}: ok={ok} L={L:.9f}", flush=True)
    print(f"{mode}: {feas}/150 feasible, min E={best:.3e} "
          f"[{time.time()-t0:.0f}s]", flush=True)
