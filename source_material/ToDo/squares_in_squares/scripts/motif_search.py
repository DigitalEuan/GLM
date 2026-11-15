#!/usr/bin/env python3
"""Motif-seeded search engine (Method 3 of the roadmap).

Unstructured pressure-settling jams at E~1e-2 because it cannot invent
crystalline tilted motifs.  This engine seeds the *analytic motif families*
directly and lets a physics-style relaxation polish them:

Seed families (all parameterized analytically):
  1. Göbel strip (a): staircase flanks + 45° central strip, side a+1+√2/2.
     Placed on the k×k grid inside side k+ε container — the classic
     small-residue improver.
  2. Tilted lattice (θ): all n squares on a θ-tilted lattice with row shear;
     the family that produces Trump-style packings.  Parameterized by tilt θ
     and lattice offset; relaxed with angle-free position settling.

Search: for each target (n, L_target), try seeds from each family, settle
positions (SAT-axis Gauss-Seidel, angles frozen), accept if E < 1e-10.
Deterministic LCG for reproducibility.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import packlib as P

# ---------------------------------------------------------------- LCG

class LCG:
    def __init__(self, seed):
        self.s = seed & 0x7FFFFFFF or 1
    def next(self):
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return self.s
    def uni(self, a, b):
        return a + (b - a) * (self.next() / 0x7FFFFFFF)

# ------------------------------------------------------- physics settling

def half_extent(t):
    return 0.5 * (abs(math.cos(t)) + abs(math.sin(t)))

def sat_pair(ci, ti, cj, tj):
    """(pen, axis) min over 4 SAT axes; pen<=0 separated."""
    dx, dy = cj[0] - ci[0], cj[1] - ci[1]
    best = None
    for th in (ti, tj):
        c, s = math.cos(th), math.sin(th)
        for ax, ay in ((c, s), (-s, c)):
            d = dx * ax + dy * ay
            hi = 0.5 * (abs(math.cos(ti) * ax + math.sin(ti) * ay)
                        + abs(-math.sin(ti) * ax + math.cos(ti) * ay))
            hj = 0.5 * (abs(math.cos(tj) * ax + math.sin(tj) * ay)
                        + abs(-math.sin(tj) * ax + math.cos(tj) * ay))
            pen = hi + hj - abs(d)
            if best is None or pen < best:
                best = pen
                sgn = 1.0 if d >= 0 else -1.0
                bax, bay = ax * sgn, ay * sgn
    return best, (bax, bay)

def settle(state, L, iters=120):
    """positions only (angles frozen): wall clamp + SAT Gauss-Seidel."""
    n = len(state)
    for _ in range(iters):
        moved = False
        for i in range(n):
            x, y, t = state[i]
            h = half_extent(t)
            nx, ny = min(max(x, h), L - h), min(max(y, h), L - h)
            if nx != x or ny != y:
                moved = True
            state[i] = (nx, ny, t)
        for i in range(n):
            xi, yi, ti = state[i]
            for j in range(i + 1, n):
                xj, yj, tj = state[j]
                if abs(xi - xj) > 2.5 or abs(yi - yj) > 2.5:
                    continue
                pen, (ax, ay) = sat_pair((xi, yi), ti, (xj, yj), tj)
                if pen > 0:
                    d = pen * 0.5 + 1e-12
                    state[i] = (xi - ax * d, yi - ay * d, ti)
                    state[j] = (xj + ax * d, yj + ay * d, tj)
                    moved = True
        if not moved:
            break
    return state

def energy(state, L):
    n = len(state)
    e = 0.0
    for i in range(n):
        x, y, t = state[i]
        h = half_extent(t)
        e += (max(0.0, h - x) ** 2 + max(0.0, x + h - L) ** 2
              + max(0.0, h - y) ** 2 + max(0.0, y + h - L) ** 2)
    for i in range(n):
        xi, yi, ti = state[i]
        for j in range(i + 1, n):
            xj, yj, tj = state[j]
            if abs(xi - xj) > 2.5 or abs(yi - yj) > 2.5:
                continue
            pen, _ = sat_pair((xi, yi), ti, (xj, yj), tj)
            if pen > 0:
                e += pen * pen
    return e

# ---------------------------------------------------------------- seeds

def seed_goebel_strip(n, L, rng):
    """staircase flanks + 45° strip: for n = (a+1)a + 2 + b with
    b = 1+floor((a-1)√2), side a+1+√2/2.  Generalized: pick a so the motif
    fits n squares: a = the largest with (a+1)a+2 <= n; remainder fills."""
    a = 0
    while (a + 2) * (a + 1) + 2 <= n:
        a += 1
    if a < 1:
        return None
    b = 1 + int(math.floor((a - 1) * math.sqrt(2))) if a > 1 else 1
    st = []
    s = a + 1 + math.sqrt(2) / 2
    # 45° central strip of b squares
    step = math.sqrt(2) / 2 + 0.5  # center spacing so squares touch along strip
    cx = (a + 1) / 2.0
    for i in range(b):
        off = (i - (b - 1) / 2.0) * step
        st.append((cx + off * 0.70710678, cx + off * 0.70710678, math.pi / 4))
    # staircase flanks: two staircases of a steps each side (mirror)
    for k in range(a):
        st.append((k + 0.5, k + 0.5, 0.0))                       # lower-left stair
        st.append((s - (k + 0.5), s - (k + 0.5), 0.0))            # upper-right stair
    rem = n - len(st)
    if rem < 0:
        st = st[:n]
    # leftover squares: fill from the bottom-right area on grid
    k = 0
    while len(st) < n and k < 400:
        x = k % a + 0.5
        y = k // a + 0.5
        if not any(abs(x - px) < 0.9 and abs(y - py) < 0.9 for px, py, _ in st):
            st.append((x, y, 0.0))
        k += 1
    if len(st) != n:
        return None
    return st

def seed_tilted(n, L, rng, theta):
    """all squares on a θ-tilted lattice: rows of ⌊W⌋ squares with row pitch
    1/ cos.. — approximates the tilted-row families (Trump/Hämäläinen style)."""
    c, s = math.cos(theta), math.sin(theta)
    # row pitch along y: 1 in the tilted frame -> dy = c; x-extent per row: 1/s
    if s < 0.35:
        return None
    # container side L; in tilted frame the usable width w = (L - 1*c) / s
    # rows: pitch c in y; per-row count: floor(L / s)?  simple layout:
    rows = max(1, int((L - 1.0) / max(c, 1e-3)) + 1)
    cols = max(1, int((L - 1.0) / max(s, 1e-3)) + 1)
    st = []
    for r in range(rows):
        for cc in range(cols):
            # center in tilted frame
            px = (cc + 0.5)
            py = (r + 0.5)
            # rotate into container frame
            x = px * c - py * s
            y = px * s + py * c
            st.append((x, y, theta))
    if len(st) < n:
        return None
    # keep n squares: drop from the end (top rows in tilted frame)
    st = st[:n]
    return st

def seed_grid(n, L, rng):
    k = int(math.ceil(math.sqrt(n)))
    st = [((i % k) + 0.5, (i // k) + 0.5, 0.0) for i in range(n)]
    return st

def seed_random(n, L, rng):
    st = [(rng.uni(0.3, L - 0.3), rng.uni(0.3, L - 0.3), rng.uni(-0.6, 0.6))
          for _ in range(n)]
    return st

# ---------------------------------------------------------------- engine

def try_target(n, L_target, seedbudget=24):
    """try to pack n squares in side L_target. Returns (state, E) best effort."""
    best_st, best_E = None, float("inf")
    for sd in range(seedbudget):
        rng = LCG(1000 * n + 77 * sd + 13)
        fam = sd % 4
        if fam == 0:
            st = seed_goebel_strip(n, L_target, rng)
        elif fam == 1:
            st = seed_tilted(n, L_target, rng, math.pi / 4.0)
        elif fam == 2:
            st = seed_tilted(n, L_target, rng, math.asin(0.6))
        else:
            st = seed_random(n, L_target, rng) if sd >= 8 else seed_grid(n, L_target, rng)
        if st is None:
            continue
        st = settle(st, L_target, 200)
        E = energy(st, L_target)
        if E < best_E:
            best_st, best_E = st, E
        if E < 1e-11:
            break
    return best_st, best_E

def pack(n, L_target, budget=None):
    return try_target(n, L_target, seedbudget=budget or 24)

if __name__ == "__main__":
    # smoke tests on known-possible targets
    import time
    for (n, L) in [(5, 2.8), (11, 3.98), (12, 3.99), (19, 4.89), (29, 5.94), (30, 5.95)]:
        t0 = time.time()
        st, E = try_target(n, L)
        print(f"n={n} L={L}: E={E:.2e} in {time.time()-t0:.1f}s",
              "FOUND" if E < 1e-10 else "jammed")
