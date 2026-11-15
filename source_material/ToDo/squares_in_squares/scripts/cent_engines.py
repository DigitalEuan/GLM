#!/usr/bin/env python3
r"""cent_engines.py — Run 6: the four cent isomorphisms, compiled.

Source specs: glm-repo/source_material/cent_compiler_v12/applications/
  proposal_04_mechanical__oscillator_w4w5.md   (W4<->W5,  ¢_sqrt)
  proposal_05_optical_pll_w9w19.md             (W9<->W19, ¢_div)
  proposal_11_stressstrain_transducer_w20_piezoelectric.md (W20, ¢_mult)
  proposal_12_fracture_toughness_calculator_w21_griffith.md (W21, ¢_sqrt)

Compilation map (physics relation -> search dynamics). All four run on
one shared substrate: the exact vectorized SAT penalty (same math as
packlib.verify: penetration = min over the 4 edge-normal axes of
ext_i + ext_j - |d.axis|; overlap iff > 0), so every engine's products
are verified by the same authority as the submission itself.

  P04 flywheel  angular_velocity = (2E/I)^(1/2):
      collective rotation moves.  Contact clusters (union-find over
      pairs with SAT margin > -1e-6) rotate as rigid bodies around
      their centroid; the rotation step is sized by the physics:
      dtheta = omega * tau with omega = sqrt(2 E_c / I_c),
      E_c = the cluster's elastic energy (sum of squared penetrations
      + container violations), I_c = moment of inertia of the unit
      masses about the centroid.  Jammed (high stress) -> large
      collective swings; relaxed -> omega -> 0 -> convergence mode.
      This is the engine that can move a RIGID_WALL without breaking
      it, because the wall rotates as ONE object.

  P05 optical PLL  wavelength = speed / frequency:
      angle phase-locking.  Each square's tilt is a phase; a discrete
      reference set PHI (the crystalline angles of the certificate
      program + the survey's record angles) are the interference
      minima.  Moves: (a) PLL update theta_i += K sin(2(phi_i -
      theta_i))  (factor 2: a square is 4-fold symmetric, the detector
      locks to phi or phi + 90 deg); (b) reassignment: square i
      re-locks to the reference that minimizes its local stress;
      (c) small positional jitter (positions still need a channel).

  P11 piezo  stress = youngs_modulus * strain:
      elastic relaxation.  Deterministic damped dynamics: every
      square feels a Hookean restoring force proportional to its
      overlap strain: along each binding SAT axis, push = eta *
      penetration, direction = away from the partner; container walls
      push inward the same way.  Positions relax like an elastic
      solid under anisotropic strain; a small thermal layer keeps it
      exploring (parasitic layer of the spec).

  P12 Griffith  stress_intensity = stress * crack_length^(1/2):
      crack propagation.  A random crack plane (angle psi, offset)
      splits the configuration in two; the two sides translate apart
      along the plane normal by delta/2 each (the crack opens,
      stress discharges along the plane).  delta is sized by the
      stress-intensity relation: delta = min(DELTA_MAX,
      KAPPA * sigma_bar * sqrt(pi * a)), a = container/4 (crack
      length scale), sigma_bar = mean penetration stress.  A short
      piezo relaxation follows each crack (energy release).

Campaign: targets = the 69 LOW-band counterexamples' small-n head
{6, 12, 13, 20, 21, 22, 30..33} + the roomy MID-band set
{695, 696, 748, 749, 803, 804, 862, 922, 983, 984}; containers =
grid - 0.002 (marginal beat) and grid - 0.02 (real beat).  A find is
a state with max pairwise overlap < 1e-10, zero container violation,
that then passes packlib.finalize + packlib.verify.  Nothing else is
ever recorded.  Checkpointed queue (workspace/push/cent_campaign.json);
run with --time-budget N until the queue is empty.
"""
import argparse
import json
import math
import os
import sys
import time
from math import ceil, sqrt

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import packlib as P
from sa_push import grid_seed, OUTW

TAB = "/home/z/my-project/workspace/submission/table.json"
PUSH = "/home/z/my-project/workspace/push"
CAMP = os.path.join(PUSH, "cent_campaign.json")
os.makedirs(PUSH, exist_ok=True)

# crystalline reference phases (degrees, mod 90): the certificate
# program's angle families + the survey's record angles (Trump 40.18)
PHI_DEG = [0.0, 15.0, 22.5, 24.29, 26.565, 30.0, 36.870, 40.18, 45.0]
PHI = np.array([math.radians(p) for p in PHI_DEG])


# ------------------------------------------------------------- substrate
def sat_margins(X, Y, TH):
    """The four SAT margin matrices (packlib math, independent code):
    m_a = ext_i(a) + ext_j(a) - |(c_i - c_j).a|  for a in
    {u_i, v_i, u_j, v_j}; margin > 0 = overlap depth on that axis.
    Returns (stack, dUi, dVi, dUj, dVj, Eu, EuT) with
    stack[k] = margin matrix for axis k, k = 0..3."""
    n = len(X)
    cs, sn = np.cos(TH), np.sin(TH)
    xy = np.stack([X, Y], axis=1)
    Q = np.stack([cs, sn], axis=1) @ xy.T          # Q[i,j] = c_j . u_i
    R = np.stack([-sn, cs], axis=1) @ xy.T         # R[i,j] = c_j . v_i
    Eu = 0.5 * (np.abs(np.outer(cs, cs) + np.outer(sn, sn))
                + np.abs(np.outer(-sn, cs) + np.outer(cs, sn)))
    dUi = np.diag(Q)[:, None] - Q                  # (c_i - c_j) . u_i
    dVi = np.diag(R)[:, None] - R                  # (c_i - c_j) . v_i
    dUj = Q.T - np.diag(Q)[None, :]                # (c_i - c_j) . u_j
    dVj = R.T - np.diag(R)[None, :]                # (c_i - c_j) . v_j
    m_u0 = 0.5 + Eu - np.abs(dUi)
    m_v0 = 0.5 + Eu - np.abs(dVi)
    m_u1 = 0.5 + Eu.T - np.abs(dUj)
    m_v1 = 0.5 + Eu.T - np.abs(dVj)
    stack = np.stack([m_u0, m_v0, m_u1, m_v1])
    return stack, dUi, dVi, dUj, dVj, Eu, Eu.T


def pen_matrix(X, Y, TH):
    """Positive penetration matrix P (0 for clear pairs) + signed pair
    margin matrix M (negative = separation gap)."""
    stack, *_ = sat_margins(X, Y, TH)
    M = stack.min(axis=0) + stack.min(axis=0).T
    M = M * 0.5          # each pair counted from both sides; average
    iu = np.triu_indices(len(X), k=1)
    Mp = np.zeros_like(M)
    Mp[iu] = M[iu]
    Mp = Mp + Mp.T
    Pp = np.maximum(Mp, 0.0)
    return Pp, Mp


def hw(TH):
    return 0.5 * (np.abs(np.cos(TH)) + np.abs(np.sin(TH)))


def out_amounts(X, Y, HW, L):
    left = np.maximum(HW - X, 0)
    right = np.maximum(X + HW - L, 0)
    bottom = np.maximum(HW - Y, 0)
    top = np.maximum(Y + HW - L, 0)
    return left + right + bottom + top


def objective(Pp, out, weight=OUTW):
    iu = np.triu_indices(Pp.shape[0], k=1)
    pairs = float(np.sum(Pp[iu] ** 2))
    return pairs + weight * float(np.sum(out ** 2))


# ------------------------------------------------------------- engines
def contact_clusters(Mp, n):
    """union-find over pairs with margin > -1e-6 (touching or worse)."""
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    iu0, iu1 = np.where(Mp > -1e-6)
    for a, b in zip(iu0, iu1):
        if a < b:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def engine_p04_flywheel(X, Y, TH, L, rng, iters, T0=0.004):
    """Collective cluster rotation, step sized by omega = sqrt(2E/I)."""
    X, Y, TH = X.copy(), Y.copy(), TH.copy()
    HW = hw(TH)
    Pp, Mp = pen_matrix(X, Y, TH)
    out = out_amounts(X, Y, HW, L)
    obj = objective(Pp, out)
    best = (obj, X.copy(), Y.copy(), TH.copy())
    for it in range(iters):
        T = T0 * (1 - it / iters) + 1e-6
        n = len(X)
        clusters = contact_clusters(Mp, n)
        big = [c for c in clusters if len(c) >= 2]
        if not big:
            # no contacts: fall back to single-square rotation moves
            i = rng.randint(n)
            dth = rng.normal(0, 0.1)
            TH[i] += dth
        else:
            c = big[rng.randint(len(big))]
            idx = np.array(c)
            # cluster energy: its pair + container share
            sub = Pp[np.ix_(idx, idx)]
            e_pairs = float(np.sum(np.maximum(sub, 0) ** 2)) * 0.5
            e_out = float(np.sum(out[idx] ** 2)) * OUTW * 0.5
            E = e_pairs + e_out + 1e-12
            cx, cy = float(X[idx].mean()), float(Y[idx].mean())
            I = float(np.sum((X[idx] - cx) ** 2 + (Y[idx] - cy) ** 2)) + 1e-9
            omega = math.sqrt(2.0 * E / I)
            dth = omega * 0.02 * rng.choice((-1.0, 1.0))
            dth = math.copysign(min(abs(dth), 0.08), dth)
            # rotate cluster members about the centroid
            ca, sa = math.cos(dth), math.sin(dth)
            dx, dy = X[idx] - cx, Y[idx] - cy
            X[idx] = cx + dx * ca - dy * sa
            Y[idx] = cy + dx * sa + dy * ca
            TH[idx] += dth
        # tiny thermal jitter, every 3rd iter only (parasitic layer)
        if it % 3 == 0:
            j = rng.randint(n)
            X[j] += rng.normal(0, T) ; Y[j] += rng.normal(0, T)
        HW = hw(TH)
        Pp, Mp = pen_matrix(X, Y, TH)
        out = out_amounts(X, Y, HW, L)
        obj = objective(Pp, out)
        if obj < best[0]:
            best = (obj, X.copy(), Y.copy(), TH.copy())
    return best


def engine_p05_pll(X, Y, TH, L, rng, iters, K=0.35, T0=0.004):
    """Optical phase-lock: angles lock to crystalline references PHI."""
    X, Y, TH = X.copy(), Y.copy(), TH.copy()
    n = len(X)
    # initial lock: nearest reference (mod pi/2)
    lock = np.array([int(np.argmin(np.abs(((PHI - t + math.pi / 4) %
                                            (math.pi / 2)) - math.pi / 4)))
                     for t in TH])
    HW = hw(TH)
    Pp, Mp = pen_matrix(X, Y, TH)
    out = out_amounts(X, Y, HW, L)
    obj = objective(Pp, out)
    best = (obj, X.copy(), Y.copy(), TH.copy())
    for it in range(iters):
        T = T0 * (1 - it / iters) + 1e-6
        # (a) PLL phase update on a random subset
        for _ in range(max(1, n // 10)):
            i = rng.randint(n)
            TH[i] += K * math.sin(2 * (PHI[lock[i]] - TH[i]))
        # (b) interference-minimum reassignment for one square:
        #     lock to the reference minimizing the SAT margin against
        #     its most-stressed partner (local O(1) per candidate)
        if n > 1:
            i = rng.randint(n)
            row = Mp[i]
            j = int(np.argmax(row))
            if row[j] > -1e-6:
                def pair_margin(ii, jj, th):
                    (ax, ay), (bx, by) = (math.cos(th[ii]), math.sin(th[ii])), \
                                         (math.cos(th[jj]), math.sin(th[jj]))
                    dx, dy = X[ii] - X[jj], Y[ii] - Y[jj]
                    best_m = None
                    for (ux, uy) in ((ax, ay), (-ay, ax), (bx, by), (-by, bx)):
                        hk = 0.5 * (abs(ux * ax + uy * ay) + abs(-ux * ay + uy * ax))
                        hj = 0.5 * (abs(ux * bx + uy * by) + abs(-ux * by + uy * bx))
                        m = hk + hj - abs(dx * ux + dy * uy)
                        if best_m is None or m < best_m:
                            best_m = m
                    return best_m
                cand = []
                for phi_i in range(len(PHI)):
                    Tt = TH.copy(); Tt[i] = PHI[phi_i]
                    cand.append(pair_margin(i, j, Tt))
                lock[i] = int(np.argmin(cand))
        # (c) positional jitter channel (every 3rd iter)
        if it % 3 == 0:
            for _ in range(max(1, n // 10)):
                i = rng.randint(n)
                X[i] += rng.normal(0, T); Y[i] += rng.normal(0, T)
        HW = hw(TH)
        Pp, Mp = pen_matrix(X, Y, TH)
        out = out_amounts(X, Y, HW, L)
        obj = objective(Pp, out)
        if obj < best[0]:
            best = (obj, X.copy(), Y.copy(), TH.copy())
    return best


def engine_p11_piezo(X, Y, TH, L, rng, iters, eta=0.15, T0=0.004):
    """Hookean elastic relaxation: push = eta * penetration along the
    binding SAT axis, away from the partner; walls push inward."""
    X, Y, TH = X.copy(), Y.copy(), TH.copy()
    n = len(X)
    HW = hw(TH)
    Pp, Mp = pen_matrix(X, Y, TH)
    out = out_amounts(X, Y, HW, L)
    obj = objective(Pp, out)
    best = (obj, X.copy(), Y.copy(), TH.copy())
    for it in range(iters):
        T = T0 * (1 - it / iters) + 1e-6
        stack, dUi, dVi, dUj, dVj, _, _ = sat_margins(X, Y, TH)
        B = stack.argmin(axis=0)                    # binding axis index
        cs, sn = np.cos(TH), np.sin(TH)
        D0x = np.sign(dUi) * cs[:, None]; D0y = np.sign(dUi) * sn[:, None]
        D1x = np.sign(dVi) * (-sn)[:, None]; D1y = np.sign(dVi) * cs[:, None]
        D2x = np.sign(dUj) * cs[None, :]; D2y = np.sign(dUj) * sn[None, :]
        D3x = np.sign(dVj) * (-sn)[None, :]; D3y = np.sign(dVj) * cs[None, :]
        Dx = (B == 0) * D0x + (B == 1) * D1x + (B == 2) * D2x + (B == 3) * D3x
        Dy = (B == 0) * D0y + (B == 1) * D1y + (B == 2) * D2y + (B == 3) * D3y
        # net Hookean push (row i sums over partners j)
        X += eta * (Pp * Dx).sum(axis=1)
        Y += eta * (Pp * Dy).sum(axis=1)
        # walls push inward with the same modulus
        X += eta * (np.maximum(HW - X, 0) - np.maximum(X + HW - L, 0))
        Y += eta * (np.maximum(HW - Y, 0) - np.maximum(Y + HW - L, 0))
        # small thermal layer (parasitic), every 3rd iter
        if it % 3 == 0:
            i = rng.randint(n)
            X[i] += rng.normal(0, T); Y[i] += rng.normal(0, T)
        HW = hw(TH)
        Pp, Mp = pen_matrix(X, Y, TH)
        out = out_amounts(X, Y, HW, L)
        obj = objective(Pp, out)
        if obj < best[0]:
            best = (obj, X.copy(), Y.copy(), TH.copy())
    return best


def engine_p12_griffith(X, Y, TH, L, rng, iters, KAPPA=0.9, T0=0.004):
    """Crack propagation: random plane splits the config; the sides
    translate apart along the normal; delta sized by K = sigma*sqrt(pi a).
    Followed by a short piezo discharge."""
    X, Y, TH = X.copy(), Y.copy(), TH.copy()
    n = len(X)
    HW = hw(TH)
    Pp, Mp = pen_matrix(X, Y, TH)
    out = out_amounts(X, Y, HW, L)
    obj = objective(Pp, out)
    best = (obj, X.copy(), Y.copy(), TH.copy())
    for it in range(iters):
        T = T0 * (1 - it / iters) + 1e-6
        # stress bar: mean penetration over stressed pairs
        iu = np.triu_indices(n, k=1)
        pen_v = Pp[iu]
        stressed = pen_v[pen_v > 0]
        sigma_bar = float(stressed.mean()) if stressed.size else 0.0
        a = max(L, 1.0) / 4.0                       # crack length scale
        delta = min(0.5, KAPPA * (sigma_bar + 0.02) * math.sqrt(math.pi * a))
        # propose a crack plane
        psi = rng.uniform(0, math.pi)
        ox = rng.uniform(0.15 * L, 0.85 * L)
        oy = rng.uniform(0.15 * L, 0.85 * L)
        nx, ny = math.cos(psi), math.sin(psi)
        side = (X - ox) * nx + (Y - oy) * ny
        A = side >= 0
        if 0 < A.sum() < n:                        # a genuine split
            Xn, Yn = X.copy(), Y.copy()
            Xn[A] += 0.5 * delta * nx; Yn[A] += 0.5 * delta * ny
            Xn[~A] -= 0.5 * delta * nx; Yn[~A] -= 0.5 * delta * ny
            Ppn, _ = pen_matrix(Xn, Yn, TH)
            outn = out_amounts(Xn, Yn, HW, L)
            objn = objective(Ppn, outn)
            if objn < obj or rng.uniform() < math.exp(-(objn - obj) / max(T, 1e-9)):
                X, Y = Xn, Yn
                obj = objn
                # short piezo discharge along the plane
                dis = engine_p11_piezo(X, Y, TH, L, rng, iters=6, eta=0.4, T0=0.0)
                if dis[0] < obj:
                    _, X, Y, TH = dis[0], dis[1], dis[2], dis[3]
                    obj = dis[0]
        # small jitter channel, every 3rd iter
        if it % 3 == 0:
            i = rng.randint(n)
            X[i] += rng.normal(0, T); Y[i] += rng.normal(0, T)
        HW = hw(TH)
        Pp, Mp = pen_matrix(X, Y, TH)
        out = out_amounts(X, Y, HW, L)
        obj = objective(Pp, out)
        if obj < best[0]:
            best = (obj, X.copy(), Y.copy(), TH.copy())
    return best


ENGINES = {
    "p04_flywheel": engine_p04_flywheel,
    "p05_pll": engine_p05_pll,
    "p11_piezo": engine_p11_piezo,
    "p12_griffith": engine_p12_griffith,
}


# ------------------------------------------------------------- campaign
def targets():
    small = [6, 12, 13, 20, 21, 22, 30, 31, 32, 33]
    roomy = [695, 696, 748, 749, 803, 804, 862, 922, 983, 984]
    return small, roomy


def seed_local(n, L, seed):
    """Gentle seed: near-grid positions, small angle jitter (±0.05 rad),
    tiny position jitter (±0.01).  Hostile seeds (±0.35 rad) bury the
    engines under self-inflicted overlap before physics starts."""
    rng = np.random.RandomState(seed)
    k = int(ceil(sqrt(n)))
    sc = L / k
    X, Y, TH = np.empty(n), np.empty(n), np.empty(n)
    for i in range(n):
        X[i] = (i % k + 0.5) * sc + rng.uniform(-0.01, 0.01)
        Y[i] = (i // k + 0.5) * sc + rng.uniform(-0.01, 0.01)
        TH[i] = rng.uniform(-0.05, 0.05)
    return X, Y, TH


def run_one(n, eng_name, L, seed, iters):
    rng = np.random.RandomState(seed)
    X, Y, TH = seed_local(n, L, seed)
    eng = ENGINES[eng_name]
    obj, bX, bY, bTH = eng(X, Y, TH, L, rng, iters)
    # terminal check on the BEST state
    stf = [(float(bX[i]), float(bY[i]), float(bTH[i]) % (math.pi / 2))
           for i in range(n)]
    r = P.verify(stf, tol=1e-9)
    worst_out = float(np.max(out_amounts(bX, bY, hw(bTH), L)))
    find = None
    if r["worst_pen"] <= 1e-10 and worst_out <= 1e-10 and r["ok"]:
        stf2, r2 = P.finalize(stf, gap=2e-9)
        if r2["ok"]:
            find = {"n": n, "engine": eng_name, "L": L, "seed": seed,
                    "state": stf2, "verified_L": round(r2["L"], 12)}
    return {"n": n, "engine": eng_name, "L": round(L, 6), "seed": seed,
            "iters": iters, "obj": round(float(obj), 12),
            "max_pen": round(float(r["worst_pen"]), 12),
            "max_out": round(worst_out, 12), "find": bool(find)}, find


def build_queue():
    small, roomy = targets()
    queue = []
    for n in small:
        g = ceil(sqrt(n))
        for eng in ENGINES:
            for L in (round(g - 0.002, 6), round(g - 0.02, 6)):
                for seed in (7919 * n + 1, 7919 * n + 2):
                    queue.append((n, eng, L, seed, 4500))
    for n in roomy:
        g = ceil(sqrt(n))
        for eng in ENGINES:
            for L in (round(g - 0.002, 6), round(g - 0.02, 6)):
                queue.append((n, eng, L, 7919 * n + 1, 700))
    queue.sort(key=lambda q: (q[0], list(ENGINES).index(q[1]), -q[2]))
    return queue


def load_camp():
    if os.path.exists(CAMP):
        return json.load(open(CAMP))
    return {"done": [], "runs": [], "finds": []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--time-budget", type=float, default=540)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        # engines must clear two FEASIBLE containers from grid seeds
        ok_all = True
        for (n, L) in ((10, 3.95), (13, 4.2)):
            for name, eng in ENGINES.items():
                r, f = run_one(n, name, L, 7919, 3000)
                tag = "FIND" if f else f"obj={r['obj']:.2e} pen={r['max_pen']:.2e}"
                print(f"  selftest n={n} L={L} {name}: {tag}")
                ok_all &= bool(f)
        print("SELFTEST", "PASS" if ok_all else "INCOMPLETE")
        return

    camp = load_camp()
    queue = build_queue()
    done = set(camp["done"])
    t0 = time.time()
    processed = 0
    for (n, eng, L, seed, iters) in queue:
        rid = f"{n}|{eng}|{L:.6f}|{seed}"
        if rid in done:
            continue
        if time.time() - t0 > args.time_budget:
            break
        r, f = run_one(n, eng, L, seed, iters)
        camp["done"].append(rid)
        camp["runs"].append(r)
        if f:
            camp["finds"].append(f)
            print(f"  *** FIND n={n} L={L} {eng} seed={seed} ***")
        print(f"  n={n} {eng} L={L:.4f} s={seed}: obj={r['obj']:.3e} "
              f"pen={r['max_pen']:.2e} out={r['max_out']:.2e}"
              + ("  FIND" if f else ""))
        processed += 1
        json.dump(camp, open(CAMP, "w"))
    remaining = sum(1 for q in queue
                    if f"{q[0]}|{q[1]}|{q[2]:.6f}|{q[3]}" not in set(camp["done"]))
    print(f"[campaign] processed {processed} this call; "
          f"done {len(camp['done'])}/{len(queue)}; remaining {remaining}; "
          f"finds {len(camp['finds'])}")
    if remaining == 0:
        json.dump(camp["finds"], open(os.path.join(PUSH, "cent_findings.json"), "w"),
                  indent=1)
        print("[campaign] queue empty; findings ->", 
              os.path.join(PUSH, "cent_findings.json"))


if __name__ == "__main__":
    main()
