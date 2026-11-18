"""Scratch: empirical kick family search at n=5, target L=2.7081.

Goal: find which collective move (rotate/swap the most strained bodies, then
re-settle cold) actually reaches 4-upright + 1-diamond.  No use of the answer.
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
RNG = np.random.RandomState(11)


def gate(st):
    r = P.verify([(float(a), float(b), float(c)) for a, b, c in np.asarray(st, float)])
    return bool(r["ok"]), float(r["worst_pen"]), float(r["L"])


def settle(st, L, moves=2500, t0=0.05):
    s = CR.relax(np.asarray(st, float), L, moves=moves, seed=1, t0=t0)
    s, fixed, sw = CR.coordinate_polish(s, L, sweeps=6)
    return np.asarray(s, float)


def strain(st, L):
    return CR.local_strain(st, L)


def top(st, L, m):
    return list(np.argsort(strain(st, L))[::-1][:m])


def clear_point(st, i, ang, box):
    """Point maximizing clearance for body i at angle `ang`, among the others."""
    others = [j for j in range(len(st)) if j != i]
    trial = st.copy()
    trial[i, 2] = ang
    best, bestp = None, None
    for x in np.linspace(box[0], box[1], 41):
        for y in np.linspace(box[0], box[1], 41):
            trial[i, 0], trial[i, 1] = x, y
            pen = CR.margin_matrix(trial)
            cost = float(np.sum(np.maximum(0.0, pen[others, i]) ** 2))
            d = float(np.min(np.hypot(st[others, 0] - x, st[others, 1] - y)))
            key = (round(cost, 12), -d)
            if bestp is None or key < bestp:
                bestp, best = key, (x, y)
    return best


def kick(st, L):
    """One collective move: most strained bodies swapped/rotated, then settled."""
    s = st.copy()
    kind = RNG.randint(6)
    if kind == 0:                                  # rotate top-1 in place
        for i in top(st, L, 1):
            s[i, 2] = (s[i, 2] + RNG.choice([1, -1]) * math.pi / 4) % PHI
    elif kind == 1:                                # rotate top-2 in place
        for i in top(st, L, 2):
            s[i, 2] = (s[i, 2] + RNG.choice([1, -1]) * math.pi / 4) % PHI
    elif kind == 2:                                # swap top-2 slots, rotate both
        t = top(st, L, 2)
        pos = s[t, :2].copy()
        s[t[0], :2] = pos[1]
        s[t[1], :2] = pos[0]
        s[t, 2] = math.pi / 4
    elif kind == 3:                                # swap worst overlapping pair
        pen = np.maximum(CR.margin_matrix(st), 0.0)
        np.fill_diagonal(pen, 0.0)
        i, j = np.unravel_index(int(np.argmax(pen)), pen.shape)
        if i != j:
            p, q = s[i, :2].copy(), s[j, :2].copy()
            s[i, :2], s[j, :2] = q, p
            s[[i, j], 2] = math.pi / 4
    elif kind == 4:                                # hole insert at 45 deg
        i = top(st, L, 1)[0]
        box = (0.0, L)
        x, y = clear_point(s, i, math.pi / 4, box)
        s[i, 0], s[i, 1], s[i, 2] = x, y, math.pi / 4
    else:                                          # rotate top-3 about centroid
        t = top(st, L, 3)
        c = s[t, :2].mean(axis=0)
        ang = RNG.choice([1, -1]) * math.pi / 4
        R = np.array([[math.cos(ang), -math.sin(ang)],
                      [math.sin(ang), math.cos(ang)]])
        s[t, :2] = (s[t, :2] - c) @ R.T + c
        s[t, 2] = (s[t, 2] + ang) % PHI
    return s


def search(L, rounds=400, seed=7919 * N + 1, verbose=True):
    rng = np.random.RandomState(seed)
    q = rsa_seed(N, L + 0.45, rng)
    st = np.stack([q[:N], q[N:2 * N], q[2 * N:]], axis=1) % math.pi
    st = settle(st, L, moves=6000)
    best = settle(st, L, moves=12000)
    best = st
    bok, bwp, bL = gate(best)
    t0 = time.time()
    for r in range(rounds):
        cand = settle(kick(best, L), L, moves=2500)
        ok, wp, Lc = gate(cand)
        ec = CR.energy(cand, L)
        eb = CR.energy(best, L)
        if (ok and Lc < bL) or (not ok and ec < eb):
            best, bok, bwp, bL = cand, ok, wp, Lc
        if verbose and (r % 25 == 0 or (ok and Lc <= L)):
            print(f"  r={r:<4} ok={ok} L={Lc:.6f} E={ec:.3e} | best ok={bok} "
                  f"L={bL:.6f} E={CR.energy(best, L):.3e} [{time.time()-t0:.0f}s]",
                  flush=True)
        if ok and Lc <= L:
            print("FOUND kick at round", r)
            print(np.array2string(cand, precision=4))
            return cand
    return best


print("target", LT, flush=True)
for sd in (1, 2, 3):
    print(f"seed {sd}")
    st = search(LT, rounds=140, seed=7919 * N + sd)
    print("  final:", gate(st), " E=", CR.energy(st, LT), flush=True)
