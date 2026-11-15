#!/usr/bin/env python3
"""Packing engine v3 — experimental instrument (DECLARED MEASURED, not exact).
Continuation shrink (established: Gensane-Ryckelynck inflation family) with:
  - angles FROZEN during position settling (Gauss-Seidel along SAT axes)
  - angle rescue (LCG-declared Metropolis) ONLY at infeasibility, always
    followed by re-settling positions
  - deterministic LCG (declared seed) — reproducible, no system randomness
Certification of candidates: 04_verify_packing.py (measured, margin 1e-9).
"""
import math

class LCG:
    def __init__(self, seed):
        self.s = seed & 0x7FFFFFFF or 1
    def next(self):
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return self.s
    def uni(self, a, b):
        return a + (b - a) * (self.next() / 0x7FFFFFFF)

def half_extent(theta):
    return 0.5 * (abs(math.cos(theta)) + abs(math.sin(theta)))

def sat_best(ci, ti, cj, tj):
    """(penetration, unit axis i->j) for two unit squares; pen<=0 => separated."""
    dx, dy = cj[0] - ci[0], cj[1] - ci[1]
    best_pen, best_axis = 0.0, None
    for th in (ti, tj):
        ca, sa = math.cos(th), math.sin(th)
        for ax, ay in ((ca, sa), (-sa, ca)):
            d = dx * ax + dy * ay
            hi = 0.5 * (abs(math.cos(ti) * ax + math.sin(ti) * ay)
                        + abs(-math.sin(ti) * ax + math.cos(ti) * ay))
            hj = 0.5 * (abs(math.cos(tj) * ax + math.sin(tj) * ay)
                        + abs(-math.sin(tj) * ax + math.cos(tj) * ay))
            pen = hi + hj - abs(d)
            if pen <= 0:
                return 0.0, None
            if best_axis is None or pen < best_pen:
                best_pen = pen
                sgn = 1.0 if d >= 0 else -1.0
                best_axis = (ax * sgn, ay * sgn)
    return best_pen, best_axis

def total_energy(state, L):
    e = 0.0
    n = len(state)
    for i in range(n):
        x, y, t = state[i]
        h = half_extent(t)
        e += (max(0.0, h - x) ** 2 + max(0.0, x + h - L) ** 2
              + max(0.0, h - y) ** 2 + max(0.0, y + h - L) ** 2)
    for i in range(n):
        xi, yi, ti = state[i]
        for j in range(i + 1, n):
            xj, yj, tj = state[j]
            if abs(xi - xj) > 2.2 or abs(yi - yj) > 2.2:
                continue
            p, _ = sat_best((xi, yi), ti, (xj, yj), tj)
            if p > 0:
                e += p * p
    return e

def settle_positions(state, L, iters):
    """angles frozen; wall projection + Gauss-Seidel separation along SAT axes.
    Fast path: per-square trig precomputed once (angles constant here)."""
    n = len(state)
    for _ in range(iters):
        ca = [math.cos(t) for _, _, t in state]
        sa = [math.sin(t) for _, _, t in state]
        hh = [0.5 * (abs(c) + abs(s)) for c, s in zip(ca, sa)]
        for i in range(n):
            x, y, t = state[i]
            h = hh[i]
            state[i] = (min(max(x, h), L - h), min(max(y, h), L - h), t)
        for i in range(n):
            xi, yi, ti = state[i]
            ci, si = ca[i], sa[i]
            for j in range(i + 1, n):
                xj, yj, tj = state[j]
                if abs(xi - xj) > 2.2 or abs(yi - yj) > 2.2:
                    continue
                cj, sj = ca[j], sa[j]
                dx, dy = xj - xi, yj - yi
                best_pen, bax, bay = 0.0, 0.0, 0.0
                sep = False
                for (ax, ay) in ((ci, si), (-si, ci), (cj, sj), (-sj, cj)):
                    d = dx * ax + dy * ay
                    hi = 0.5 * (abs(ci * ax + si * ay) + abs(-si * ax + ci * ay))
                    hj = 0.5 * (abs(cj * ax + sj * ay) + abs(-sj * ax + cj * ay))
                    pen = hi + hj - abs(d)
                    if pen <= 0:
                        sep = True
                        break
                    if bax == 0.0 and bay == 0.0 or pen < best_pen:
                        best_pen = pen
                        sgn = 1.0 if d >= 0 else -1.0
                        bax, bay = ax * sgn, ay * sgn
                if not sep:
                    d = best_pen * 0.5 + 1e-11
                    xi -= bax * d; yi -= bay * d
                    xj += bax * d; yj += bay * d
                    state[j] = (xj, yj, tj)
            state[i] = (xi, yi, ti)
    return state

def local_energy(state, i, L):
    x, y, t = state[i]
    h = half_extent(t)
    val = (max(0.0, h - x) ** 2 + max(0.0, x + h - L) ** 2
           + max(0.0, h - y) ** 2 + max(0.0, y + h - L) ** 2)
    for j in range(len(state)):
        if j == i:
            continue
        xj, yj, tj = state[j]
        if abs(x - xj) > 2.2 or abs(y - yj) > 2.2:
            continue
        p, _ = sat_best((x, y), t, (xj, yj), tj)
        if p > 0:
            val += p * p
    return val

def angle_rescue(state, L, rng, temp, moves):
    """Metropolis on angles (LCG-declared); caller re-settles positions after."""
    n = len(state)
    for _ in range(moves):
        i = rng.next() % n
        x, y, t = state[i]
        e_old = local_energy(state, i, L)
        new_t = t + rng.uni(-1, 1) * temp
        state[i] = (x, y, new_t)
        e_new = local_energy(state, i, L)
        de = e_new - e_old
        if de > 0 and rng.uni(0, 1) > math.exp(-de / max(temp, 1e-9)):
            state[i] = (x, y, t)                    # revert
    return state

def pack(n, L_target, restarts=4, seed=42, shrink_delta=0.01, verbose=False):
    """return (state, energy) at L_target; energy ~0 => candidate packing."""
    grid_side = int(math.ceil(math.sqrt(n)))
    if L_target >= grid_side - 1e-12:
        st = [((k % grid_side) + 0.5, (k // grid_side) + 0.5, 0.0) for k in range(n)]
        return st, 0.0
    best_state, best_e = None, float('inf')
    for r in range(restarts):
        rng = LCG(seed * 7919 + r * 104729)
        side = grid_side
        st = [((k % side) + 0.5 + rng.uni(-0.03, 0.03),
               (k // side) + 0.5 + rng.uni(-0.03, 0.03),
               rng.uni(-0.05, 0.05) if r else 0.0) for k in range(n)]
        L = float(side)
        temp = 0.25
        delta = shrink_delta
        failed = False
        while True:
            target_step = max(L_target, L - delta)
            st = settle_positions(st, target_step, 80)
            e = total_energy(st, target_step)
            tries = 0
            while e > 1e-10 and tries < 8:
                st = angle_rescue(st, target_step, rng, temp, 20 * n)
                st = settle_positions(st, target_step, 80)
                e = total_energy(st, target_step)
                temp *= 0.9
                tries += 1
            if e > 1e-8:
                # jammed: retreat one step, refine delta, reheat
                delta *= 0.5
                temp = min(0.3, temp * 2 + 0.05)
                st = settle_positions(st, L, 40)
                if delta < 5e-5:
                    failed = True
                    break
                continue
            L = target_step
            if L <= L_target + 1e-12:
                break
        e = total_energy(st, L_target)
        if verbose:
            print(f"  restart {r}: L={L:.4f} E={e:.3e}")
        if e < best_e:
            best_e, best_state = e, [tuple(q) for q in st]
        if best_e < 1e-10:
            break
        if failed and best_e < 1e-8:
            break
    return best_state, best_e

if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    L = float(sys.argv[2]) if len(sys.argv) > 2 else 2.9
    sol, e = pack(n, L, restarts=6, seed=7, verbose=True)
    print(("FOUND" if e < 1e-8 else "NOT-FOUND"), "n=", n, "L=", L, "E=", e)
