"""Scratch: re-placement kick + L-BFGS-B settle at n=5, L=2.7081.

Kick: most strained bodies moved to the widest free slot (angle chosen from a
small set) -- swapped/rotated, then re-settled.  Settle: L-BFGS-B on the
project's squared-hinge penalty at the fixed box [0, L]^2.
"""
import math
import sys
import time

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, "scripts")
import packlib as P
import cram_relax as CR
from cent_discovery import rsa_seed

N = 5
LT = 2.7081
PHI = math.pi / 2
OUTW = 4.0
LOG = open("workspace/scratch/log_lbfgs.txt", "w")


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")
    LOG.flush()


def unpack(q):
    return q[:N].copy(), q[N:2 * N].copy(), q[2 * N:].copy()


def pen_and_wall(q, L):
    X, Y, TH = unpack(q)
    st = np.stack([X, Y, TH], axis=1)
    pen = np.maximum(CR.margin_matrix(st), 0.0)
    iu = np.triu_indices(N, 1)
    HW = 0.5 * (np.abs(np.cos(TH)) + np.abs(np.sin(TH)))
    w = np.maximum(np.maximum(HW - X, X + HW - L), 0.0)
    w2 = np.maximum(np.maximum(HW - Y, Y + HW - L), 0.0)
    return pen, iu, w + w2, HW


def energy(q, L):
    pen, iu, wall, _ = pen_and_wall(q, L)
    return float(np.dot(pen[iu], pen[iu]) + OUTW * np.dot(wall, wall))


def gate_st(st):
    r = P.verify([(float(a), float(b), float(c)) for a, b, c in np.asarray(st, float)])
    return bool(r["ok"]), float(r["worst_pen"]), float(r["L"])


def lbfgs(q, L, maxiter=400):
    best = [np.asarray(q, float).copy(), energy(q, L)]

    def f(v):
        e = energy(v, L)
        if e < best[1] - 1e-18:
            best[0], best[1] = np.asarray(v, float).copy(), e
        return e

    res = minimize(f, np.asarray(q, float), method="L-BFGS-B",
                   options={"maxiter": maxiter, "ftol": 1e-16, "gtol": 1e-12})
    return (res.x if res.fun <= best[1] else best[0]), float(min(res.fun, best[1]))


ANGLES = np.array([0.0, PHI / 2, PHI / 4, -PHI / 4])


def slot_scores(st, i, L, G=81):
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
        for j in range(len(st)):
            if j == i:
                continue
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


def best_slot(st, i, L, rng, G=81):
    costs, mind, grid = slot_scores(st, i, L, G)
    flat = costs.ravel()
    pmin = flat.min()
    if pmin > 1e8:
        return None
    idx = np.where(np.abs(flat - pmin) <= 1e-9)[0]
    md = mind.ravel()[idx]
    order = idx[np.argsort(-md)]
    pick = order[rng.randint(min(5, len(order)))]
    ai, gx, gy = np.unravel_index(pick, costs.shape)
    return float(grid[gx]), float(grid[gy]), float(ANGLES[ai])


def to_st(q):
    X, Y, TH = unpack(q)
    return np.stack([X, Y, TH], axis=1)


def from_st(st):
    return np.concatenate([st[:, 0], st[:, 1], st[:, 2]])


def run(L, seed, rounds=120):
    rng = np.random.RandomState(seed)
    q0 = rsa_seed(N, L + 0.45, rng)
    q, e = lbfgs(q0, L)
    q, e = lbfgs(q, L)
    bq, be = q.copy(), e
    ok, wp, Lc = gate_st(to_st(bq))
    say(f"seed {seed}: start ok={ok} L={Lc:.6f} wp={wp:+.2e} E={be:.3e}")
    t0 = time.time()
    for r in range(rounds):
        st = to_st(bq).copy()
        m = 1 + rng.randint(3)
        order = list(np.argsort(CR.local_strain(st, L))[::-1][:m])
        rng.shuffle(order)
        for i in order:
            sl = best_slot(st, i, L, rng)
            if sl is None:
                continue
            st[i] = sl
        q2, e2 = lbfgs(from_st(st), L)
        q2, e2 = lbfgs(q2, L)
        ok, wp, Lc = gate_st(to_st(q2))
        if e2 < be - 1e-14 or (ok and Lc < L + 1e-12):
            bq, be = q2.copy(), e2
            say(f"  r={r:<4} m={m} ok={ok} L={Lc:.6f} wp={wp:+.2e} E={e2:.3e} "
                f"[{time.time()-t0:.0f}s]")
        if ok and Lc <= L + 1e-12:
            say("HIT round", r)
            say(np.array2string(to_st(bq), precision=6))
            return bq, True
    return bq, False


say("target", LT)
hit = None
for sd in (1, 2, 3, 4):
    q, h = run(LT, 7919 * N + sd)
    say(f"seed {sd} final:", gate_st(to_st(q)), "E=", energy(q, LT))
    if h:
        hit = q
        break
say("HIT" if hit is not None else "NO HIT")
if hit is not None:
    np.save("workspace/scratch/n5_hit.npy", to_st(hit))
