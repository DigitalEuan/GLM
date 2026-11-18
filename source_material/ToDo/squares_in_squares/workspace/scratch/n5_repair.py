"""Scratch: big-neighbourhood repair at n=5.

Move = keep the least strained bodies, re-place the m most strained ones at the
best free (position, 45-degree angle) slots, then re-settle cold.
Score of a slot: (total penetration, bbox extent) lexicographic.
"""
import math
import sys
import time

import numpy as np

sys.path.insert(0, "scripts")
import packlib as P
import cram_relax as CR
from cent_discovery import rsa_seed

N = 5
LT = 2.7081
PHI = math.pi / 2
HWS = {a: 0.5 * (abs(math.cos(a)) + abs(math.sin(a)))
       for a in np.linspace(0, PHI, 37)}


def gate(st):
    r = P.verify([(float(a), float(b), float(c)) for a, b, c in np.asarray(st, float)])
    return bool(r["ok"]), float(r["worst_pen"]), float(r["L"])


def settle(st, L, moves=2500, t0=0.05):
    s = CR.relax(np.asarray(st, float), L, moves=moves, seed=1, t0=t0)
    s = CR.coordinate_polish(s, L, sweeps=6)
    if isinstance(s, tuple):
        s = s[0]
    return np.asarray(s, float)


def pen_one(st, i, x, y, att):
    """Penetration of body i at (x,y,att) against the others; bbox extents."""
    n = len(st)
    best = 0.0
    for j in range(n):
        if j == i:
            continue
        dx, dy = x - st[j, 0], y - st[j, 1]
        thj = st[j, 2]
        hw_i = 0.5 * (abs(math.cos(att)) + abs(math.sin(att)))
        hw_j = 0.5 * (abs(math.cos(thj)) + abs(math.sin(thj)))
        ov = 1e9
        for a in (att, att + PHI, thj, thj + PHI):
            ax, ay = math.cos(a), math.sin(a)
            r1 = 0.5 * (abs(math.cos(a - att)) + abs(math.sin(a - att)))
            r2 = 0.5 * (abs(math.cos(a - thj)) + abs(math.sin(a - thj)))
            ov = min(ov, r1 + r2 - abs(dx * ax + dy * ay))
        best = max(best, ov)
    return best


def place(st, i, grid=25, angles=None, L=None):
    """Best (x, y, theta) for body i: min (penetration, bbox extent)."""
    if angles is None:
        angles = [0.0, PHI / 4, PHI / 2]
    others = np.array([j for j in range(len(st)) if j != i])
    xs = np.linspace(0.0, L, grid)
    best, bestk = None, None
    for att in angles:
        hw = 0.5 * (abs(math.cos(att)) + abs(math.sin(att)))
        for x in xs:
            if x - hw < -1e-9 or x + hw > L + 1e-9:
                continue
            for y in xs:
                if y - hw < -1e-9 or y + hw > L + 1e-9:
                    continue
                p = pen_one(st, i, x, y, att)
                # bbox extent of the resulting configuration
                trial = st.copy()
                trial[i] = (x, y, att)
                e = 0.5 * (np.abs(np.cos(trial[:, 2])) + np.abs(np.sin(trial[:, 2])))
                w = float((trial[:, 0] + e).max() - (trial[:, 0] - e).min())
                h = float((trial[:, 1] + e).max() - (trial[:, 1] - e).min())
                key = (round(max(p, 0.0) / 0.02), round(max(w, h) / 0.05))
                if bestk is None or key < bestk:
                    bestk, best = key, (x, y, att)
    return best


def repair(st, L, m):
    s = st.copy()
    order = list(np.argsort(CR.local_strain(st, L))[::-1])
    bad = order[:m]
    for i in bad:                       # most strained placed last
        x, y, att = place(s, i, grid=25, L=L)
        s[i] = (x, y, att)
    return s


def search(L, rounds=250, seed=7919 * N + 1):
    rng = np.random.RandomState(seed)
    q = rsa_seed(N, L + 0.45, rng)
    st = np.stack([q[:N], q[N:2 * N], q[2 * N:]], axis=1) % math.pi
    best = settle(st, L, moves=8000)
    bok, bwp, bL = gate(best)
    eb = CR.energy(best, L)
    t0 = time.time()
    for r in range(rounds):
        m = 1 + (r % 3)
        cand = settle(repair(best, L, m), L, moves=2500)
        ok, wp, Lc = gate(cand)
        ec = CR.energy(cand, L)
        if (ok and Lc < bL) or (ec < eb - 1e-12):
            best, bok, bwp, bL, eb = cand, ok, wp, Lc, ec
            print(f"  r={r:<4} m={m} IMPROVE ok={ok} L={Lc:.6f} E={ec:.3e} "
                  f"[{time.time()-t0:.0f}s]", flush=True)
        if ok and Lc <= L:
            print("FOUND repair at round", r)
            print(np.array2string(cand, precision=4))
            return cand
    return best


print("target", LT, flush=True)
for sd in (1, 2):
    print(f"seed {sd}")
    st = search(LT, rounds=120, seed=7919 * N + sd)
    print("  final:", gate(st), "E=", CR.energy(st, LT), flush=True)
