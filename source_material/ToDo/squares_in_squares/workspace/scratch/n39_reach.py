"""How close can the new move set actually get at n = 39? Structural screen + deflation floor."""
import math
import sys
import time

import numpy as np

sys.path.insert(0, "scripts")
import proposal_anneal as PA


def screen(n, L, trials=40, iters=500):
    """Many bridge variants, one short relaxation each: is ANY of them in the right basin?"""
    rng = np.random.default_rng(4242)
    best = None
    hist = []
    t0 = time.time()
    for t in range(trials):
        cells, words = PA.seed_bridge(n, L, rng)
        u = PA.to_u(cells, words)
        u, _e = PA.relax(u, n, L, iters)
        cc, ww = PA.from_u(u, n)
        cc = PA.quench(cc, ww, L, iters=1200, damping=0.25)
        p = PA.max_pen(cc, ww)
        hist.append(p)
        if best is None or p < best[0]:
            best = (p, t)
    print(f"screen n={n} L={L}: best {best[0]:+.4e} (trial {best[1]}), "
          f"median {np.median(hist):+.3e}, worst {max(hist):+.3e} in {time.time() - t0:.1f}s")
    return best[0]


def defect_at(n, L):
    m = max(1, int(math.ceil(math.sqrt(n))))
    p = L / m
    sites = [(i, j) for j in range(m) for i in range(m)]
    edge = {s: min(s[0], s[1], m - 1 - s[0], m - 1 - s[1]) for s in sites}
    keep = sorted(sites, key=lambda s: (edge[s], s[1], s[0]))[:n]
    return ([((i + 0.5) * p, (j + 0.5) * p) for i, j in keep], [(1.0, 0.0)] * n)


def deflate(n, L0, L1, steps=50, iters=250, q=1200):
    cells, words = defect_at(n, L0)
    u = PA.to_u(cells, words)
    for L in np.linspace(L0, L1, steps):
        u, _e = PA.relax(u, n, float(L), iters)
        cc, ww = PA.from_u(u, n)
        cc = PA.quench(cc, ww, float(L), iters=q, damping=0.2)
        u = PA.to_u(cc, ww)
    cc, ww = PA.from_u(u, n)
    return PA.max_pen(cc, ww)


if __name__ == "__main__":
    screen(39, 6.85, trials=40)
    for L in (6.95, 6.90, 6.87):
        t0 = time.time()
        p = deflate(39, 7.0, L)
        print(f"deflate 7.00 -> {L}: pen={p:+.4e}  ({time.time() - t0:.1f}s)", flush=True)
