"""Two baselines at n = 39: (a) the existing solver with a long budget, (b) deflation."""
import math
import sys
import time

import numpy as np

sys.path.insert(0, "scripts")
import proposal_anneal as PA


def defect_at(n, L):
    m = max(1, int(math.ceil(math.sqrt(n))))
    p = L / m
    sites = [(i, j) for j in range(m) for i in range(m)]
    edge = {s: min(s[0], s[1], m - 1 - s[0], m - 1 - s[1]) for s in sites}
    keep = sorted(sites, key=lambda s: (edge[s], s[1], s[0]))[:n]
    cells = [((i + 0.5) * p, (j + 0.5) * p) for i, j in keep]
    return cells, [(1.0, 0.0)] * len(cells)


def deflate(n, L0, L1, steps=70, iters=250, quench_iters=1200):
    cells, words = defect_at(n, L0)
    u = PA.to_u(cells, words)
    for L in np.linspace(L0, L1, steps):
        u, _e = PA.relax(u, n, float(L), iters)
        cc, ww = PA.from_u(u, n)
        cc = PA.quench(cc, ww, float(L), iters=quench_iters, damping=0.2)
        u = PA.to_u(cc, ww)
    cc, ww = PA.from_u(u, n)
    return PA.max_pen(cc, ww)


def long_run(n, L, seconds):
    rng = np.random.default_rng(11)
    t0 = time.time()
    best = None
    seeds = ["corner", "defect", "strip", "random"]
    rep = 0
    while time.time() - t0 < seconds:
        cap = min(25.0, seconds - (time.time() - t0))
        if cap <= 1.0:
            break
        r = PA.solve(n, L, seeds[rep % len(seeds)], rng, steps=4000, cap_seconds=cap)
        rep += 1
        if best is None or r["pen"] < best["pen"]:
            best = r
        print(f"   restart {rep} seed={r['seed']}: pen={r['pen']:+.4e} ({r['seconds']}s) "
              f"best={best['pen']:+.4e}", flush=True)
    return best


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    if which in ("deflate", "both"):
        for steps, iters in ((70, 250), (140, 400)):
            t0 = time.time()
            p = deflate(39, 7.0, 6.85, steps=steps, iters=iters)
            print(f"deflate 7.00 -> 6.85 (steps={steps}, iters={iters}): pen={p:+.4e} "
                  f"({time.time() - t0:.1f}s)", flush=True)
    if which in ("long", "both"):
        b = long_run(39, 6.85, 150)
        print(f"long run best: pen={b['pen']:+.4e} seed={b['seed']}")
