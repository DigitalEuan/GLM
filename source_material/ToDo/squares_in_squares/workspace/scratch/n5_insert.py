"""Scratch: randomized farthest-point insertion at n=5, L=2.7081, then settle.

Generic heuristic: insert bodies one at a time at the widest free slot (least
overlap, then max clearance), angle from a small set; random order and random
first slot.  Then cold re-settle.  No knowledge of the answer is used.
"""
import math
import sys
import time

import numpy as np

sys.path.insert(0, "scripts")
import packlib as P
import cram_relax as CR

N = 5
LT = 2.7081
PHI = math.pi / 2
LOG = open("workspace/scratch/log_insert.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")
    LOG.flush()


def gate(st):
    r = P.verify([(float(a), float(b), float(c)) for a, b, c in np.asarray(st, float)])
    return bool(r["ok"]), float(r["worst_pen"]), float(r["L"])


def settle(st, L, moves=2500, t0=0.06):
    s = CR.relax(np.asarray(st, float), L, moves=moves, seed=1, t0=t0)
    s = CR.coordinate_polish(s, L, sweeps=8)
    if isinstance(s, tuple):
        s = s[0]
    return np.asarray(s, float)


ANGLES = np.array([0.0, PHI / 2, PHI / 4, -PHI / 4])


def slot_scores(st, placed, i, L, G=61):
    grid = np.linspace(0.5, L - 0.5, G)
    GX, GY = np.meshgrid(grid, grid, indexing="ij")
    costs = np.full((len(ANGLES), G, G), -1e9)
    mind = np.full((len(ANGLES), G, G), 1e9)
    for ai, att in enumerate(ANGLES):
        hw = 0.5 * (abs(math.cos(att)) + abs(math.sin(att)))
        inside = (GX >= hw - 1e-12) & (GX <= L - hw + 1e-12) & \
                 (GY >= hw - 1e-12) & (GY <= L - hw + 1e-12)
        cost = np.full((G, G), -1e9)
        md = np.full((G, G), 1e9)
        for j in placed:
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
        costs[ai] = np.where(inside, cost, 1e9)
        mind[ai] = np.where(inside, md, -1e9)
    return costs, mind, grid


def insert_all(L, rng, G=61):
    st = np.zeros((N, 3))
    order = list(range(N))
    rng.shuffle(order)
    placed = []
    for i in order:
        if not placed:
            # random first slot (nothing to clear yet)
            att = ANGLES[rng.randint(len(ANGLES))]
            hw = 0.5 * (abs(math.cos(att)) + abs(math.sin(att)))
            x = rng.uniform(hw, L - hw)
            y = rng.uniform(hw, L - hw)
            st[i] = (x, y, att)
            placed.append(i)
            continue
        costs, mind, grid = slot_scores(st, placed, i, L, G)
        flat = costs.ravel()
        pmin = flat.min()
        idx = np.where(np.abs(flat - pmin) <= 1e-9)[0]
        md = mind.ravel()[idx]
        order2 = idx[np.argsort(-md)]
        pick = order2[rng.randint(min(4, len(order2)))]
        ai, gx, gy = np.unravel_index(pick, costs.shape)
        st[i] = (grid[gx], grid[gy], ANGLES[ai])
        placed.append(i)
    return st


say("target", LT)
t0 = time.time()
best = None
bL = 1e9
hits = 0
for r in range(120):
    rng = np.random.RandomState(7919 * N + r)
    cand = insert_all(LT, rng)
    cand = settle(cand, LT)
    ok, wp, L = gate(cand)
    if ok and L < bL:
        bL = L
        best = cand
        say(f"  r={r} ok=True L={L:.6f} [{time.time()-t0:.0f}s]")
        say(np.array2string(cand, precision=5))
        if L <= LT + 1e-12:
            hits += 1
            say("HIT")
            break
    elif r % 20 == 0:
        say(f"  r={r} ok={ok} L={L:.6f} wp={wp:+.2e} [{time.time()-t0:.0f}s]")
say("hits", hits, "best L", bL, "secs", round(time.time() - t0, 1))
