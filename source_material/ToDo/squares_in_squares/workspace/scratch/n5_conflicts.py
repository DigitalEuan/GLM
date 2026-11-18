"""Scratch: min-conflicts re-placement at n=5, L=2.7081.

Move: pick the most strained bodies, swap/rotate them into the widest free
slots inside the box, re-settle cold.  Generic: no knowledge of the answer.
Logs every improvement so a killed run still reports.
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
LOG = open("workspace/scratch/log_conflicts.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")
    LOG.flush()


def gate(st):
    r = P.verify([(float(a), float(b), float(c)) for a, b, c in np.asarray(st, float)])
    return bool(r["ok"]), float(r["worst_pen"]), float(r["L"])


def settle(st, L, moves=1500, t0=0.06):
    s = CR.relax(np.asarray(st, float), L, moves=moves, seed=1, t0=t0)
    s = CR.coordinate_polish(s, L, sweeps=6)
    if isinstance(s, tuple):
        s = s[0]
    return np.asarray(s, float)


ANGLES = np.array([0.0, PHI / 4, PHI / 2, -PHI / 4])


def slot_scores(st, i, L, G=81):
    """cost[p,a,gx,gy] = max penetration of body i there; and min distance."""
    grid = np.linspace(0.5, L - 0.5, G)
    GX, GY = np.meshgrid(grid, grid, indexing="ij")
    others = [j for j in range(len(st)) if j != i]
    costs = np.full((len(ANGLES), G, G), -1e9)
    mind = np.full((len(ANGLES), G, G), 1e9)
    for ai, att in enumerate(ANGLES):
        hw = 0.5 * (abs(math.cos(att)) + abs(math.sin(att)))
        inside = (GX >= hw - 1e-12) & (GX <= L - hw + 1e-12) & \
                 (GY >= hw - 1e-12) & (GY <= L - hw + 1e-12)
        cost = np.full((G, G), -1e9)
        md = np.full((G, G), 1e9)
        for j in others:
            dx = GX - st[j, 0]
            dy = GY - st[j, 1]
            thj = st[j, 2]
            ov = np.full((G, G), 1e9)
            for a in (att, att + PHI, thj, thj + PHI):
                ax, ay = math.cos(a), math.sin(a)
                r1 = 0.5 * (abs(math.cos(a - att)) + abs(math.sin(a - att)))
                r2 = 0.5 * (abs(math.cos(a - thj)) + abs(math.sin(a - thj)))
                ov = np.minimum(ov, r1 + r2 - np.abs(dx * ax + dy * ay))
            cost = np.maximum(cost, ov)
            md = np.minimum(md, np.hypot(dx, dy))
        cost = np.where(inside, cost, 1e9)
        md = np.where(inside, md, -1e9)
        costs[ai], mind[ai] = cost, md
    return costs, mind, grid


def best_slot(st, i, L, rng, spread=0.0, G=81):
    costs, mind, grid = slot_scores(st, i, L, G)
    flat = costs.ravel()
    pmin = flat.min()
    if pmin > 1e8:
        return None
    ok = np.abs(flat - pmin) <= 1e-9
    # among the least-overlapping slots, prefer the widest one (max clearance);
    # `spread` mixes in a random pick among the top few for diversity
    idx = np.where(ok)[0]
    md = mind.ravel()[idx]
    order = idx[np.argsort(-md)]
    if spread > 0 and rng.uniform() < spread:
        pick = order[rng.randint(min(6, len(order)))]
    else:
        pick = order[0]
    ai, gx, gy = np.unravel_index(pick, costs.shape)
    return float(grid[gx]), float(grid[gy]), float(ANGLES[ai]), float(pmin)


def run(L, seed, rounds=160):
    rng = np.random.RandomState(seed)
    q = rsa_seed(N, L + 0.45, rng)
    st = np.stack([q[:N], q[N:2 * N], q[2 * N:]], axis=1) % math.pi
    best = settle(st, L, moves=6000)
    bok, bwp, bL = gate(best)
    eb = CR.energy(best, L)
    say(f"seed {seed}: start ok={bok} L={bL:.6f} E={eb:.3e}")
    t0 = time.time()
    for r in range(rounds):
        s = best.copy()
        m = 1 + rng.randint(3)
        order = list(np.argsort(CR.local_strain(s, L))[::-1][:m])
        rng.shuffle(order)
        for i in order:
            sl = best_slot(s, i, L, rng, spread=0.5)
            if sl is None:
                continue
            x, y, att, _p = sl
            s[i] = (x, y, att)
        cand = settle(s, L, moves=1500)
        ok, wp, Lc = gate(cand)
        ec = CR.energy(cand, L)
        if (ok and Lc < bL + 1e-12) or ec < eb - 1e-12:
            best, bok, bwp, bL, eb = cand, ok, wp, Lc, ec
            say(f"  r={r:<4} m={m} ok={ok} L={Lc:.6f} wp={wp:+.2e} E={ec:.3e} "
                f"[{time.time()-t0:.0f}s]")
        if ok and Lc <= L + 1e-12:
            say("FOUND at round", r)
            say(np.array2string(cand, precision=5))
            return cand, True
    return best, False


say("target", LT)
found = None
for sd in (1, 2, 3, 4):
    st, hit = run(LT, 7919 * N + sd)
    say(f"seed {sd} final:", gate(st), "E=", CR.energy(st, LT))
    if hit:
        found = st
        break
say("HIT" if found is not None else "NO HIT")
