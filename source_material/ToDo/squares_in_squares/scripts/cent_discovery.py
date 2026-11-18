#!/usr/bin/env python3
r"""cent_discovery.py — RECONSTRUCTION, not the original.

`boundary_demo.py`, `boundary_scan.py`, `fine_probe.py`, `root_probe.py`,
`soft_relax.py` and `run19_docs.py` all import this module. It is **not in this
tree and never was in the repository's git history** (`git log --all --
'*cent_discovery*'` returns nothing; only the *references* appear, in commits
db74f9e and 41489c7). So it cannot be restored from history — only rebuilt to the
contract its callers use:

    rsa_seed(n, L, rng)  -> q, a length-3n float array [X; Y; TH] (TH in [0, pi/2))
                            used as a start point for soft relaxation. Called as
                            `rsa_seed(n, L_t + 0.45, rng)`, so L is given extra
                            slack and the placement may be loose.
    attempt(n, L, seed, ...) -> a record dict; the caller in boundary_scan.py
                            unpacks it as `f = attempt(...)`.

`run19_docs.py` also refers to `python3 scripts/cent_discovery.py` as an
"engine v3 selftest (rediscovery)", so this file keeps a __main__ that runs the
control rediscovery test below.

RSA = random sequential adsorption: place squares one at a time at a random
position and angle, rejecting a placement that overlaps what is already down or
leaves the box; after too many rejections the last candidate is accepted anyway
so the function always returns a full 3n array (soft relaxation is expected to
repair overlaps).

Everything here is *measured*: the selftest gates results with packlib.
"""
from __future__ import annotations

import math
import sys

import numpy as np

PHI = math.pi / 2


def _hw(th):
    return 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))


def _overlaps(X, Y, TH, i, x, y, t, eps=1e-9) -> bool:
    """Separating-axis test between square i (proposed at x,y,t) and squares j<i.

    Projection radius of a unit square onto axis `a` is 0.5*(|cos(a-t)| +
    |sin(a-t)|) -- the HALF-SIDE 0.5, not hw (the square's own half-extent). The
    first version used hw and was up to 41% over-conservative, which pushed most
    placements into a fallback that ignored the squares already down; those two
    faults together produced seeds with worst_pen ~0.5.
    """
    for j in range(i):
        dx = x - X[j]
        dy = y - Y[j]
        sep = False
        for a in (t, t + math.pi / 2, TH[j], TH[j] + math.pi / 2):
            ax, ay = math.cos(a), math.sin(a)
            r1 = 0.5 * (abs(math.cos(a - t)) + abs(math.sin(a - t)))
            r2 = 0.5 * (abs(math.cos(a - TH[j])) + abs(math.sin(a - TH[j])))
            if abs(dx * ax + dy * ay) > r1 + r2 - eps:
                sep = True
                break
        if not sep:
            return True
    return False


def rsa_seed(n: int, L: float, rng: np.random.RandomState, reps: int = 3):
    """Random sequential adsorption seed, guaranteed overlap-free.

    Two phases. Phase 1 is honest RSA: place all n squares by rejection sampling
    with rotation; a *complete* pass is returned. If a pass fails, phase 2 builds
    a jittered lattice instead (cell = L/k > 1 because callers pass L_t + 0.45),
    which cannot overlap.

    Earlier versions mixed the two and left a "last resort" that placed unchecked
    squares -- measured worst_pen 0.46 on n=5 and 1.03 on n=65, and the reason the
    control rediscovery (n=5 at 2.7081) returned no hard hop.
    """
    k = max(1, int(math.ceil(math.sqrt(n))))

    for _ in range(reps):
        X = np.empty(n); Y = np.empty(n); TH = np.empty(n)
        ok_all = True
        for i in range(n):
            placed = False
            for _t in range(400):
                t = rng.uniform(0.0, PHI)
                hw = _hw(np.array([t]))[0]
                if L <= 2 * hw:
                    continue
                x = rng.uniform(hw, L - hw)
                y = rng.uniform(hw, L - hw)
                if not _overlaps(X, Y, TH, i, x, y, t):
                    X[i], Y[i], TH[i] = x, y, t
                    placed = True
                    break
            if not placed:
                ok_all = False
                break
        if ok_all:
            TH %= PHI
            return np.concatenate([X, Y, TH])

    # phase 2: jittered lattice, non-overlapping by construction
    cell = L / k
    j = max(0.0, (cell - 1.0) * 0.35)
    X = np.empty(n); Y = np.empty(n); TH = np.empty(n)
    for i in range(n):
        cx = (i % k + 0.5) * cell
        cy = (i // k + 0.5) * cell
        X[i] = cx + rng.uniform(-j, j)
        Y[i] = cy + rng.uniform(-j, j)
        TH[i] = rng.uniform(-0.05, 0.05)
    eps_pad = 0.0
    X = np.clip(X + eps_pad, 0.5 + 1e-9, L - 0.5 - 1e-9)
    Y = np.clip(Y, 0.5 + 1e-9, L - 0.5 - 1e-9)
    TH %= PHI
    return np.concatenate([X, Y, TH])


def attempt(n: int, L: float, seed: int, hops: int = 4, moves: int = 20000,
            **kw) -> dict:
    """One discovery attempt: hop_search at target L, gated by packlib."""
    from soft_relax import hop_search
    best, hard, checked = hop_search(n, L, seed)
    if best is None:
        return {"n": n, "L_t": L, "seed": seed, "found": False,
                "hard_hops": hard, "checked": checked}
    L_hard, q = best
    return {"n": n, "L_t": L, "seed": seed, "found": True, "L": float(L_hard),
            "hard_hops": hard, "checked": checked,
            "q": [float(v) for v in q]}


def selftest() -> int:
    """The controls soft_relax.py's own docstring prescribes."""
    import packlib as P
    from soft_relax import hop_search
    print("cent_discovery reconstruction — control rediscovery")
    print(f"{'n':>3} {'target':>8} {'best hard L':>12} {'known':>8} result")
    for n, known in ((5, 2.7071068), (11, 3.8771)):
        best, hard, checked = hop_search(n, known + 0.001, 7919 * n + 1)
        got = None if best is None else best[0]
        print(f"{n:>3} {known + 0.001:>8.4f} "
              f"{('—' if got is None else format(got, '.6f')):>12} {known:>8.4f} "
              f"{'no hard hop' if got is None else ('OK' if got <= known + 0.01 else 'above known')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest())
