#!/usr/bin/env python3
r"""oracle_basin.py — RECONSTRUCTION, not the original.

Imported by `boundary_demo.py`, `fine_probe.py`, `lattice_scan.py`,
`p1p_insert31.py`, `p2_seed_polish.py`, `root_probe.py` and `soft_relax.py`.
**Absent from this tree and from the repository's git history** (`git log --all --
'*oracle_basin*'` returns nothing), so it is rebuilt to the calls used:

    settle_to(q, L_t, iters=250)          -> (q, f)   gradient cold-settle
    ramp_settle(q, L0, L1, steps=...)     -> (q, f)   settle along a side ramp

The energy is the W36 hinge: squared pair penetration plus squared wall
violation, so a settled state means the same thing it means everywhere else in
this project.

WHY THE n = 5 CONTROL NEEDED A COLLECTIVE MOVE (measured, 2026-11-18).
`s(5) = 2 + 1/sqrt(2) = 2.7071068` (Goebel 1979) is attained only by four
upright squares in the container's corners with the fifth turned 45 degrees
between them -- at that side the corner squares are exactly `1 + sqrt(2)/2`
apart, so the central square's diagonal (sqrt 2) is the cross gap.  Every
single-body descent and every fixed-side anneal stalls on a *different*
configuration: from rsa seeds at L_t = 2.7081 the relaxer stops at
L = 2.97-3.08, a 3+2 row whose bbox is 2.97 x 2.13 -- wide, not square.  A hot
anneal (400k moves, t0 0.15/0.35) stalls at L = 2.78, and 300 single-body
45-degree rotation kicks from the E = 0.034082 attractor produce **0** feasible
states.  The attractor is a genuine trap:

    (2.194, 0.500, 90) (0.644, 2.237, 90) (0.561, 1.353, 90)
    (1.916, 1.558, 7.4) (0.506, 0.470, 90)

L-BFGS-B on the hinge is strong enough to *hold* the feasible set (uniform
random starts reach it in 7/300 tries, 2.3%) but not to reach it from a row.
What escapes the trap is the **collective kick** implemented here: take the m
most strained bodies, swap their positions among themselves, turn each by
+/-45 degrees, re-slot each into a fresh position inside [0, L]^2 with high
probability, and re-settle.  Measured at n = 5, L = 2.7081 from the attractor:
**25/150 kicks reach a packlib-feasible state** (17%), all at L = 2.70801..2.70810
<= L_t.  With the 12-round loop below the settle returns a feasible state at
the control side; `soft_relax.hop_search(5, 2.7071068 + 0.001, ...)` then passes
its own control without ever being seeded from the answer.

Two settles are used, because their costs differ:
  * 3n <= 90 variables: L-BFGS-B on the hinge at the fixed box [0, L]^2 (the
    measured solver above; ftol 1e-16).
  * larger n: the project's own vectorised Gibbs descent, `cram_relax.relax`
    + `coordinate_polish`, whose cost is O(n) per move rather than the
    O(n^2 * 3n) of a numerical-gradient quasi-Newton step.  The collective kick
    is solver-agnostic and runs in both.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import minimize

import sa_push as SA

#: Wall weight of the hinge, as in `sa_push.OUTW`.
OUTW = 4.0

#: Above this many variables the numerical-gradient L-BFGS is dropped for the
#: vectorised Gibbs descent (3n = 90 at n = 30).
LB_MAX_VARS = 90


def _unpack(q, n):
    return q[:n].copy(), q[n:2 * n].copy(), q[2 * n:].copy()


def energy(q, L, weight: float = 1.0) -> float:
    n = q.size // 3
    X, Y, TH = _unpack(q, n)
    HW = SA.hw_vals(TH % (np.pi / 2))
    return float(SA.total_pen(X, Y, TH % (np.pi / 2), HW, L, weight=weight))


def _hinge(q, L, weight: float = 1.0) -> float:
    """The W36 hinge at the fixed box [0, L]^2: squared positive penetration
    over unordered pairs plus OUTW * squared wall violation.

    This is the objective the L-BFGS branch minimises (and the one measured
    above).  `energy` keeps the project's `total_pen` scale, which counts the
    ordered pairs, so it is twice this on the pair term.
    """
    import cram_relax as CR
    n = q.size // 3
    X, Y, TH = _unpack(q, n)
    st = np.stack([X, Y, TH % (np.pi / 2)], axis=1)
    pen = np.maximum(CR.margin_matrix(st), 0.0)
    iu = np.triu_indices(n, 1)
    HW = 0.5 * (np.abs(np.cos(st[:, 2])) + np.abs(np.sin(st[:, 2])))
    wx = np.maximum(np.maximum(HW - X, X + HW - L), 0.0)
    wy = np.maximum(np.maximum(HW - Y, Y + HW - L), 0.0)
    wall = wx + wy
    return float(weight * np.dot(pen[iu], pen[iu]) + OUTW * np.dot(wall, wall))


def _lbfgs(st, L: float, weight: float = 1.0, maxiter: int = 400):
    """L-BFGS-B on the hinge; the best point visited is returned, never a hot one."""
    n = len(st)
    q0 = np.concatenate([st[:, 0], st[:, 1], st[:, 2]])
    best = [q0.copy(), _hinge(q0, L, weight)]

    def f(v):
        e = _hinge(v, L, weight)
        if e < best[1] - 1e-18:
            best[0], best[1] = np.asarray(v, float).copy(), e
        return e

    res = minimize(f, q0, method="L-BFGS-B",
                   options={"maxiter": maxiter, "ftol": 1e-16, "gtol": 1e-12})
    q = res.x if res.fun <= best[1] else best[0]
    # only the ANGLES are taken mod pi: wrapping the whole (n, 3) array wraps
    # the positions too, which is invisible at n = 5 (the box is smaller than
    # pi) and destroys every packing above it (n = 65 went to E = 8.98).
    out = np.stack([q[:n], q[n:2 * n], q[2 * n:] % np.pi], axis=1)
    return out, float(min(res.fun, best[1]))


def _gibbs(st, L: float, iters: int):
    """The project's vectorised descent: single-body Gibbs + coordinate polish."""
    import cram_relax as CR
    moves = max(400, int(iters) * 12)
    try:
        st = CR.relax(np.asarray(st, float), L, moves=moves)
    except Exception:                                   # noqa: BLE001
        pass
    try:
        pol = CR.coordinate_polish(st, L, sweeps=4)
        st = pol[0] if isinstance(pol, tuple) else pol
    except Exception:                                   # noqa: BLE001
        pass
    return np.asarray(st, float), CR.energy(np.asarray(st, float), L)


def collective_kick(st, L: float, rng: np.random.RandomState, m: int | None = None):
    """The most strained bodies swapped, turned 45 degrees, re-slotted, re-settled.

    * swap   -- the chosen bodies' positions are permuted among themselves
                (a collective move: no single body's local descent does this);
    * rotate -- each chosen body is turned by +/- pi/4 (the angle the n = 5
                optimum needs, and the only angle a square's extent does not
                feel: hw is identical at th and th + pi/2, so +/- pi/4 moves
                the body off the parallel family without growing the box);
    * re-slot-- each chosen body is, with probability 0.85, dropped at a fresh
                uniform position inside the container.  This is what actually
                escapes the measured trap: a pure rotation kick lands back on
                the same attractor (0/300), a re-slot kick does not (25/150).
    """
    n = len(st)
    s = np.asarray(st, float).copy()
    if n < 2:
        return s
    if m is None:
        m = 1 + int(rng.randint(min(3, n - 1)))
    m = int(max(1, min(m, n - 1)))
    import cram_relax as CR
    order = list(np.argsort(CR.local_strain(s, L))[::-1][:m])
    # swap the chosen bodies' slots among themselves
    pos = s[order, :2].copy()
    perm = rng.permutation(len(order))
    s[order, :2] = pos[perm]
    # re-slot radius: 1.2 mean body spacings.  At n=5 that is most of the box
    # (a near restart, which is what finds the n=5 cross); at n=65..626 it is a
    # local move, because a uniform re-slot inside a dense packing is
    # unrecoverable for a Gibbs settle (measured: n=65 went to worst_pen 0.57).
    rad = 1.2 * L / math.sqrt(n)
    for i in order:
        att = float((s[i, 2] + rng.choice([-1.0, 1.0]) * np.pi / 4) % (np.pi / 2))
        if rng.uniform() < 0.85:                        # re-slot
            hw = 0.5 * (abs(np.cos(att)) + abs(np.sin(att)))
            if L > 2 * hw:
                s[i, 0] = min(max(s[i, 0] + rng.uniform(-rad, rad), hw), L - hw)
                s[i, 1] = min(max(s[i, 1] + rng.uniform(-rad, rad), hw), L - hw)
        s[i, 2] = att
    hw = 0.5 * (np.abs(np.cos(s[:, 2])) + np.abs(np.sin(s[:, 2])))
    s[:, 0] = np.clip(s[:, 0], hw, np.maximum(hw, L - hw))
    s[:, 1] = np.clip(s[:, 1], hw, np.maximum(hw, L - hw))
    return s


def settle_to(q, L: float, iters: int = 250, weight: float = 1.0,
              kicks: int | None = None, seed: int = 0):
    """Cold settle at container side L. Returns (q, f).

    Cold settle (L-BFGS-B for 3n <= 90 variables, `cram_relax` above that),
    then `kicks` rounds of `collective_kick` + re-settle, keeping the lowest
    energy seen.  `f` is the hinge energy of the returned state at L.
    """
    a = np.asarray(q, float)
    n = a.size // 3
    st = np.stack([a[:n], a[n:2 * n], a[2 * n:] % np.pi], axis=1)
    small = 3 * n <= LB_MAX_VARS
    if kicks is None:
        # measured at n = 5: one kick is worth ~4% of a feasibility hit (the
        # attractor is a 3-in-a-line that the hinge prefers to the feasible
        # cross), so small n needs a real budget; large n is left cheap because
        # the sweep uses the Gibbs branch where a kick round costs O(n^2).
        kicks = 40 if n <= 12 else (16 if n <= 30 else (8 if n <= 200 else 3))
    rng = np.random.RandomState(int(seed) & 0x7FFFFFFF)
    if small:
        st, f = _lbfgs(st, L, weight)
    else:
        st, f = _gibbs(st, L, iters)
    for _ in range(int(kicks)):
        if f <= 1e-12:                                  # already feasible
            break
        cand = collective_kick(st, L, rng)
        if small:
            cand, fc = _lbfgs(cand, L, weight, maxiter=200)
        else:
            cand, fc = _gibbs(cand, L, iters)
        if fc < f - 1e-14:
            st, f = cand, fc
    out = np.concatenate([st[:, 0], st[:, 1], st[:, 2]])
    return out, float(f)


def ramp_settle(q, L0: float, L1: float, steps: int = 6, iters: int = 120):
    """Settle at a sequence of sides from L0 to L1 (the side ramp)."""
    best = (np.asarray(q, float).copy(), float("inf"))
    for L in np.linspace(L0, L1, max(2, steps)):
        qq, f = settle_to(q, float(L), iters=iters)
        q = qq
        best = (qq, f)
    return best


if __name__ == "__main__":
    from cent_discovery import rsa_seed
    rng = np.random.RandomState(1)
    q = rsa_seed(5, 3.2, rng)
    q, f = settle_to(q, 2.7081068)
    n = q.size // 3
    st = [(float(q[i]), float(q[n + i]), float(q[2 * n + i])) for i in range(n)]
    import packlib as P
    r = P.verify(st)
    print(f"settle smoke: n=5 E={f:.3e} ok={r['ok']} "
          f"worst_pen={r['worst_pen']:+.3e} L={r['L']:.9f}")
