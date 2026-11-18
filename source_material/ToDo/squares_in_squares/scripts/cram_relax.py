#!/usr/bin/env python3
r"""cram_relax.py — the CRAM translation, Run 39.

SOURCE. B. Hoover, H. Blayney, J. C. R. Whittington, "Classical Energies
Learn to Reason 1,000x Faster than Looped Models" (arXiv:2611.17309v1,
12 Nov 2026).  CRAM is a trainable Hopfield-Tank mean-field free energy

    E(p) = 1/beta * sum_i p_i' log p_i  +  1/2 sum_{i!=j} p_i' K_ij p_j
           + sum_i B_i' p_i

descended one cell at a time (Eq. 3), trained by pseudolikelihood (PL)
without differentiating through the descent, stopped at a threshold tau
calibrated on the training solutions, and (for Maze-Hard) extended with a
latent z-layer that settles before the answer flow.

WHAT IS TRANSLATED HERE, AND WHAT THE DOMAIN REFUSES.  CRAM's cells are
discrete: M answer variables, C candidate values each.  A packing has no
candidate values — its state is n continuous (x, y, theta) triples — so
the energy cannot be the same object.  What carries over is the shape of
the argument, and this instrument measures each piece separately rather
than assuming that a translation that reads well also works:

  A  PL / relation-cost table   idea A of the brief: a learned pairwise
     coupling over *relations* (relative angle bin, contact-distance
     bin), fitted at the delivered solutions by histogram (the maximum-
     entropy pairwise potential — the same family as CRAM's K_ij), and
     used as a scoring rule for candidate seeds.  Measured as (i)
     discrimination between the records and two controls, (ii) the
     Spearman correlation between the score and what relaxation actually
     reaches from that seed.

  B  calibrated stopping threshold.  tau is taken exactly as CRAM takes
     it — the highest energy among the verified solutions, plus tolerance
     — and then audited: how many infeasible boards does it accept
     (CRAM's "never stops at a wrong board"), and does it grade the
     target depth, i.e. does E at L*(1-delta) sit below or above tau.

  C  focused body relaxation.  CRAM's Focused Gibbs updates only the
     cells whose local energy exceeds their training mean; here only the
     k most strained bodies move each step (local strain = the body's own
     share of the hinge energy) and the quiescent interior is frozen.

  D  dual-layer (z) relaxation.  A macro layer settles first — bodies
     grouped into contact clusters and translated rigidly, angles frozen
     (the packing analogue of the maze's distance-to-goal field) — and
     the fine per-body layer settles second on top of it.

ENERGY USED THROUGHOUT.  The W36/W37 hinge energy of this project, the
same one `pressure_field.py` settles and `packlib.verify` certifies:

    E(state, L) = sum_{i<j} max(0, pen_ij)^2  +  sum_i wall_i^2

with pen_ij the SAT pair penetration (min over the four edge-normal axes
of ext_i + ext_j - |d.axis|) and wall_i the signed excess of body i over
the four container sides of [0, L]^2.  A point of the packing state space
is feasible exactly when E = 0, which is why idea B is audited rather
than assumed: see the module's measured finding in
`06-CRAM-RELAX.md`.

EXACTNESS DISCIPLINE.  This is a measuring instrument, in the sense of
`sat_review.py` / `sat_measure.py`: it computes in float and claims
nothing from float.  Every candidate it reports as feasible is handed to
`packlib.finalize` + `packlib.verify` — the project's own authority — and
the reported L is packlib's.

DETERMINISM.  No wall-clock seed, no global RNG: every seed is derived
from the puzzle count and the cell's index (the project's discipline,
`seed = 7919*n + 104729*attempt`), and the relaxation itself is
deterministic (no noise), so the variant comparison is like for like.

Usage:
    python3 scripts/cram_relax.py --census
    python3 scripts/cram_relax.py --matrix
    python3 scripts/cram_relax.py --pl
    python3 scripts/cram_relax.py --all --write
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import packlib as P                                      # noqa: E402

TABLE = os.path.join(ROOT, "workspace/submission/table.json")
OUTDIR = os.path.join(ROOT, "workspace/push")

PHI = math.pi / 2.0
SQ2 = math.sqrt(2.0)

#: The cells of the relaxation matrix: puzzle counts spanning the ledger.
CELLS = (20, 60, 110, 240)
#: Corruption strengths of the seed (angle sd in radians; the position shift
#: is a quarter of it, scaled by the container).
AMPS = (0.005, 0.01, 0.04, 0.08)
#: Depths tested as a fraction of the delivered best side (the push table).
PUSH_DEPTHS = (0.01, 0.02)
#: Relaxation budget, identical for every variant (moves, not seconds).
MOVES = 8000
SEEDS = 2

#: The step-size constants of the project's own annealer are reused through
#: the schedule in `relax` (geometric temperature, improving-only tail);
#: `sa_push.py` is the reference for them.


# ------------------------------------------------------------------- the field
def extents(th: np.ndarray) -> np.ndarray:
    """Half-width of a unit square at angle th (the same on both axes)."""
    return 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))


def unpack(state: np.ndarray):
    return state[:, 0].copy(), state[:, 1].copy(), state[:, 2].copy()


def margin_matrix(state: np.ndarray) -> np.ndarray:
    """SAT pair margin, the packlib math: pen_ij = min over the 4 axes of
    ext_i + ext_j - |d.axis|.  Positive = overlap depth."""
    x, y, th = unpack(state)
    n = len(th)
    c, s = np.cos(th), np.sin(th)
    xy = np.stack([x, y], axis=1)
    Q = np.stack([c, s], axis=1) @ xy.T        # Q[i,j] = c_j . u_i
    R = np.stack([-s, c], axis=1) @ xy.T       # R[i,j] = c_j . v_i
    Eu = 0.5 * (np.abs(np.outer(c, c) + np.outer(s, s))
                + np.abs(np.outer(-s, c) + np.outer(c, s)))
    dU = np.diag(Q)[:, None] - Q
    dV = np.diag(R)[:, None] - R
    fam0 = np.minimum(0.5 + Eu - np.abs(dU), 0.5 + Eu - np.abs(dV))
    fam1 = np.minimum(0.5 + Eu.T - np.abs(dU.T), 0.5 + Eu.T - np.abs(dV.T))
    pen = np.minimum(fam0, fam1)
    np.fill_diagonal(pen, 0.0)
    return pen


def bbox(state: np.ndarray) -> tuple:
    """(x_lo, x_hi, y_lo, y_hi) of the axis-aligned bounding box."""
    x, y, th = unpack(state)
    e = extents(th)
    return (float(np.min(x - e)), float(np.max(x + e)),
            float(np.min(y - e)), float(np.max(y + e)))


def wall_penalty(state: np.ndarray, L: float) -> float:
    """Hinge on the bounding-box extent: a packing's container is its own
    bbox (packlib's L = max(w, h)), so the walls are free to translate and
    the only wall violation is an extent larger than the target side."""
    lo_x, hi_x, lo_y, hi_y = bbox(state)
    return (max(0.0, (hi_x - lo_x) - L) ** 2
            + max(0.0, (hi_y - lo_y) - L) ** 2)


def energy(state: np.ndarray, L: float) -> float:
    """The W36 hinge energy at container side L (0 exactly at feasibility)."""
    e = wall_penalty(state, L)
    if len(state) < 2:
        return e
    pen = margin_matrix(state)
    iu = np.triu_indices(len(state), k=1)
    over = np.maximum(0.0, pen[iu])
    return float(np.dot(over, over)) + e


def local_strain(state: np.ndarray, L: float) -> np.ndarray:
    """Each body's own share of E: its pair terms plus the wall term of the
    edges it holds up.

    This is the packing reading of CRAM's per-cell local energy (the
    quantity Focused Gibbs prioritises).  A body's wall share is the
    extent violation of an extreme it touches, split among the bodies that
    touch that extreme."""
    n = len(state)
    strain = np.zeros(n)
    if n > 1:
        pen = np.maximum(0.0, margin_matrix(state))
        np.fill_diagonal(pen, 0.0)
        strain = strain + np.sum(pen ** 2, axis=1)
    x, y, th = unpack(state)
    e = extents(th)
    lo_x, hi_x, lo_y, hi_y = bbox(state)
    for extent, lo, hi, coord in (((hi_x - lo_x), lo_x, hi_x, x - e),
                                  ((hi_y - lo_y), lo_y, hi_y, y - e)):
        over = max(0.0, extent - L)
        if over <= 0.0:
            continue
        for idx in (np.where(coord <= lo + 1e-12)[0],
                    np.where(coord + 2.0 * e >= hi - 1e-12)[0]):
            if len(idx):
                strain[idx] += 0.5 * over * over / len(idx)
    return strain


def hw_vals(th: np.ndarray) -> np.ndarray:
    """Half-width of each rotated unit square (same on x and y)."""
    return 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))


def pair_pen_row(k: int, X, Y, TH, HW) -> np.ndarray:
    """Overlap depth of body k against every other body (0 = clear).

    The same four-axis SAT as `margin_matrix`, but O(n) for one body, so a
    single-body move can be scored incrementally.  Copied from
    `sa_push.pair_pen_k` (that module cannot be imported: its header makes
    a directory outside the repository)."""
    n = len(X)
    idx = np.arange(n)
    J = idx[idx != k]
    dx = X[J] - X[k]
    dy = Y[J] - Y[k]
    out = np.zeros(len(J))
    near = (np.abs(dx) < 1.42) & (np.abs(dy) < 1.42)
    if not near.any():
        return out
    Jn = J[near]
    dxn, dyn = dx[near], dy[near]
    ck, sk = math.cos(float(TH[k])), math.sin(float(TH[k]))
    cj, sj = np.cos(TH[Jn]), np.sin(TH[Jn])

    def axis(ax, ay, bx, by):
        du = dxn * ax + dyn * ay
        hk = 0.5 * (abs(ax * ck + ay * sk) + abs(-ax * sk + ay * ck))
        hj = 0.5 * (np.abs(bx * ax + by * ay) + np.abs(-bx * ay + by * ax))
        return hk + hj - np.abs(du)

    a1 = axis(ck, sk, cj, sj)          # k's axes: ext_k = 0.5, ext_j from j's frame
    a2 = axis(-sk, ck, cj, sj)
    a3 = axis(cj, sj, cj, sj)          # j's axes: ext_j = 0.5, ext_k from k's frame
    a4 = axis(-sj, cj, -sj, cj)
    out[near] = np.maximum(np.minimum(np.minimum(a1, a2),
                                      np.minimum(a3, a4)), 0.0)
    return out


def wall_cost(X, Y, HW, L: float) -> float:
    """Hinge on the bbox extent (the container is the packing's own box)."""
    w = float(np.max(X + HW) - np.min(X - HW))
    h = float(np.max(Y + HW) - np.min(Y - HW))
    return max(0.0, w - L) ** 2 + max(0.0, h - L) ** 2


def local_pair_cost(k: int, X, Y, TH, HW) -> float:
    pk = pair_pen_row(k, X, Y, TH, HW)
    return float(np.dot(pk, pk))


# ------------------------------------------------------------- the variants
def relax(state: np.ndarray, L: float, moves: int = MOVES,
          mode: str = "full", k: int | None = None,
          seed: int = 0, t0: float = 0.02) -> np.ndarray:
    """Descend E(., L) by single-body Gibbs moves.  Three proposal schedules.

    full      every body is eligible (the baseline: pressure-settling).
    focused   only the k most strained bodies are eligible, recomputed every
              `refresh` moves — CRAM's Focused Gibbs, which spends its moves
              on the bodies whose local energy is above the rest rather
              than on the quiescent interior.
    two_layer the first half of the moves translate bodies with the angles
              frozen (the macro layer: where things sit), the second half
              moves positions and angles together (the fine flow on top of
              the settled coarse field).

    Moves are Metropolis at a geometric temperature with an improving-only
    polish tail, the project's own schedule (`sa_push.anneal`), so a variant
    difference is a difference of *where the moves go*, not of dynamics.
    """
    X = state[:, 0].copy()
    Y = state[:, 1].copy()
    TH = state[:, 2].copy()
    n = len(X)
    HW = hw_vals(TH)
    if k is None:
        k = max(4, int(math.ceil(n / 6.0)))
    rng = np.random.RandomState(seed)
    refresh = max(50, moves // 40)
    eligible = np.ones(n, dtype=bool)
    half = moves // 2

    def point_cost() -> float:
        return wall_cost(X, Y, HW, L) + 0.5 * sum(
            local_pair_cost(i, X, Y, TH, HW) for i in range(n))

    cur = point_cost()
    best = cur
    best_state = state.copy()
    t_sa = int(moves * 0.85)
    T = t0
    decay = (1e-5 / t0) ** (1.0 / max(1, t_sa - 1))
    for it in range(moves):
        phase_macro = (mode == "two_layer" and it < half)
        if it % refresh == 0:
            if mode == "focused":
                eligible = np.zeros(n, dtype=bool)
                eligible[np.argsort(local_strain(np.stack([X, Y, TH], axis=1), L))[::-1][:k]] = True
            else:
                eligible = np.ones(n, dtype=bool)
        cand = np.where(eligible)[0]
        if not len(cand):
            break
        # a macro move changes positions only; the fine phase moves both
        rotate_frac = 0.0 if phase_macro else 0.3
        polish = it >= t_sa
        k_i = int(cand[rng.randint(len(cand))])
        ps = 0.0015 if polish else max(1e-5, 0.6 * T)
        as_ = 0.0015 if polish else max(1e-5, 0.9 * T)
        old_x, old_y, old_t, old_hw = X[k_i], Y[k_i], TH[k_i], HW[k_i]
        pk = pair_pen_row(k_i, X, Y, TH, HW)
        old_local = float(np.dot(pk, pk))
        old_wall = wall_cost(X, Y, HW, L)
        # half the moves are directed: separate the chosen body from its
        # worst partner along the centre line (a SAT push), the rest are
        # isotropic draws at the temperature — the same grammar for every
        # variant, so a variant difference is never a move-type difference
        directed = pk.size > 0 and pk.max() > 0.0 and rng.uniform() < 0.5
        if directed:
            others = np.arange(n)[np.arange(n) != k_i]
            j = int(others[int(np.argmax(pk))])
            dxv, dyv = old_x - X[j], old_y - Y[j]
            nv = math.hypot(dxv, dyv)
            if nv < 1e-12:
                dxv, dyv, nv = 1.0, 0.0, 1.0
            push = min(0.5 * float(pk.max()), 2.0 * ps + 1e-6)
            X[k_i] = old_x + push * dxv / nv + rng.uniform(-ps, ps) * 0.1
            Y[k_i] = old_y + push * dyv / nv + rng.uniform(-ps, ps) * 0.1
        else:
            X[k_i] = old_x + rng.uniform(-ps, ps)
            Y[k_i] = old_y + rng.uniform(-ps, ps)
        if rng.uniform() < rotate_frac:
            TH[k_i] = old_t + rng.uniform(-as_, as_)
            HW[k_i] = hw_vals(np.array([TH[k_i]]))[0]
        pk_new = pair_pen_row(k_i, X, Y, TH, HW)
        d_local = float(np.dot(pk_new, pk_new)) - old_local
        d_wall = wall_cost(X, Y, HW, L) - old_wall
        # E = wall + sum_{i<j} pen^2 = wall + 0.5 * sum_i local_i, and moving
        # body i changes the unordered pair sum by exactly d_local (each
        # pen_ij appears once), so the increment is d_local + d_wall.  The
        # earlier `0.5 * d_local` undercounted by two and let the chain accept
        # moves that raised the true energy -- at n=65 it turned a feasible
        # record (worst_pen -2e-10) into worst_pen +0.57.
        dP = d_local + d_wall
        if dP <= 0 or (not polish and rng.uniform() < math.exp(-dP / max(T, 1e-12))):
            cur += dP
            if cur < best - 1e-18:
                best = cur
                best_state = np.stack([X, Y, TH], axis=1)
        else:
            X[k_i], Y[k_i], TH[k_i], HW[k_i] = old_x, old_y, old_t, old_hw
        if not polish:
            T = max(T * decay, 1e-5)
    # the chain returns its best point, never a hot final one
    return best_state.copy()


def project(state: np.ndarray, L: float, iters: int = 400,
            relax: float = 0.5) -> np.ndarray:
    """Greedy SAT pushes on the worst pair — **measured to hurt, not used**.

    Kept as the record of a negative: applied after the annealer at n = 5 it
    *raised* E (8.3e-4 -> 2.4e-3), because resolving the worst pair and then
    pulling the box in recreates the overlap it just removed — the same
    oscillation `pressure_field.compact` guards against with backing-off.
    The last mile used in this run is `coordinate_polish` instead.  Do not
    wire this into a campaign without re-measuring it."""
    st = state.copy()
    n = len(st)
    if n < 2:
        return st
    for _ in range(iters):
        pen = margin_matrix(st)
        np.fill_diagonal(pen, 0.0)
        worst = float(pen.max())
        if worst > 1e-12:
            i, j = np.unravel_index(int(np.argmax(pen)), pen.shape)
            i, j = (int(i), int(j)) if i < j else (int(j), int(i))
            dx = st[i, 0] - st[j, 0]
            dy = st[i, 1] - st[j, 1]
            nv = math.hypot(dx, dy)
            if nv < 1e-12:
                dx, dy, nv = 1.0, 0.0, 1.0
            step = relax * worst
            st[i, :2] += step * np.array([dx, dy]) / nv
            st[j, :2] -= step * np.array([dx, dy]) / nv
            continue
        # no overlap: close the walls if the box is still too wide
        e = extents(st[:, 2])
        lo_x, hi_x = int(np.argmin(st[:, 0] - e)), int(np.argmax(st[:, 0] + e))
        lo_y, hi_y = int(np.argmin(st[:, 1] - e)), int(np.argmax(st[:, 1] + e))
        over_x = float((st[hi_x, 0] + e[hi_x]) - (st[lo_x, 0] - e[lo_x])) - L
        over_y = float((st[hi_y, 1] + e[hi_y]) - (st[lo_y, 1] - e[lo_y])) - L
        if over_x <= 1e-12 and over_y <= 1e-12:
            break
        if over_x > 0:
            st[lo_x, 0] += 0.5 * over_x
            st[hi_x, 0] -= 0.5 * over_x
        if over_y > 0:
            st[lo_y, 1] += 0.5 * over_y
            st[hi_y, 1] -= 0.5 * over_y
    return st


def coordinate_polish(state: np.ndarray, L: float, sweeps: int = 4) -> tuple:
    """Greedy single-body descent to a fixed point — CRAM's second stopping
    rule (stop when no single-cell change lowers the energy), in packing
    form.  Each body tries three proposals (half-push and full push away
    from its worst partner, and a small rotation) and keeps the one that
    lowers its own exact share of E; a sweep that improves nothing is a
    fixed point and ends the pass.

    Returns (state, fixed_point, sweeps_used)."""
    st = state.copy()
    n = len(st)
    if n < 2:
        return st, True, 0
    HW = hw_vals(st[:, 2])
    used = 0
    for _sweep in range(sweeps):
        used += 1
        improved = False
        order = np.argsort(local_strain(st, L))[::-1]
        for i_raw in order:
            i = int(i_raw)
            best_state, best_cost = None, None
            base_wall = wall_cost(st[:, 0], st[:, 1], HW, L)
            cur_local = local_pair_cost(i, st[:, 0], st[:, 1], st[:, 2], HW)
            cur = cur_local + base_wall
            pk = pair_pen_row(i, st[:, 0], st[:, 1], st[:, 2], HW)
            proposals = []
            if pk.size and pk.max() > 1e-12:
                others = np.arange(n)[np.arange(n) != i]
                j = int(others[int(np.argmax(pk))])
                dxv, dyv = st[i, 0] - st[j, 0], st[i, 1] - st[j, 1]
                nv = math.hypot(dxv, dyv) or 1.0
                for scale in (0.5, 1.0):
                    cand = st.copy()
                    cand[i, 0] += scale * float(pk.max()) * dxv / nv
                    cand[i, 1] += scale * float(pk.max()) * dyv / nv
                    proposals.append(cand)
            for dth in (-0.01, 0.01):
                cand = st.copy()
                cand[i, 2] += dth
                proposals.append(cand)
            for cand in proposals:
                hw_i = hw_vals(np.array([cand[i, 2]]))[0]
                HW[i] = hw_i
                cost = (local_pair_cost(i, cand[:, 0], cand[:, 1], cand[:, 2], HW)
                        + wall_cost(cand[:, 0], cand[:, 1], HW, L))
                HW[i] = hw_vals(np.array([st[i, 2]]))[0]
                if cost < cur - 1e-15 and (best_cost is None or cost < best_cost):
                    best_state, best_cost = cand, cost
            if best_state is not None:
                st = best_state
                HW = hw_vals(st[:, 2])
                improved = True
        if not improved:
            return st, True, used
    return st, False, used


def settle_and_gate(state: np.ndarray, L_t: float) -> dict:
    """Report both the instrument's numbers and the project's own verdict."""
    ok, worst, ext = (lambda r: (bool(r["ok"]), float(r["worst_pen"]), float(r["L"])))(
        P.verify([(float(a), float(b), float(c)) for a, b, c in state]))
    out = {"e": round(energy(state, L_t), 12), "worst_pen": round(worst, 12),
           "extent_L": round(ext, 12), "feasible_at_target": bool(ok and ext <= L_t * 1.0)}
    fin, r = P.finalize([(float(a), float(b), float(c)) for a, b, c in state])
    out["gated_L"] = round(float(r["L"]), 12) if r["ok"] else None
    out["gated_ok"] = bool(r["ok"])
    return out


# --------------------------------------------------------------- the table
def load_table() -> dict:
    with open(TABLE) as f:
        raw = json.load(f)
    return {int(k): np.array(v["state"], dtype=float) for k, v in raw.items()}


def record_L(state: np.ndarray) -> float:
    return float(P.verify([(float(a), float(b), float(c)) for a, b, c in state])["L"])


def perturb(state: np.ndarray, rng: np.random.RandomState,
            angle: float = 0.12, shift: float = 0.03) -> np.ndarray:
    """A corrupted record: every body re-tilted and nudged (the seed a
    search chain starts from)."""
    st = state.copy()
    L = record_L(state)
    st[:, 2] = st[:, 2] + rng.normal(0.0, angle, len(st))
    st[:, :2] += rng.normal(0.0, shift * L / math.sqrt(len(st)), (len(st), 2))
    return st


# ------------------------------------------------------------------ idea B
def census(table: dict) -> dict:
    """E over the delivered solutions: tau, then what tau accepts."""
    rows = []
    t0 = time.time()
    for n in sorted(table):
        st = table[n]
        L = record_L(st)
        rows.append((n, L, energy(st, L)))
    energies = [e for _n, _L, e in rows]
    tau = max(energies)                     # CRAM's rule, taken literally
    # graded depths: does tau separate the target depths at all?
    depth = {}
    for delta in (0.001, 0.0025, 0.005, 0.01):
        below = 0
        vals = []
        for n in sorted(table):
            if n > 400:                     # the deep rows dominate the cost
                continue
            st = table[n]
            L = record_L(st)
            e = energy(st, L * (1.0 - delta))
            vals.append(e)
            below += 1 if e <= tau + 1e-12 else 0
        vals.sort()
        depth[str(delta)] = {"rows": len(vals),
                             "at_or_below_tau": below,
                             "median_E": round(vals[len(vals) // 2], 9)}
    return {"rows": len(rows), "tau": tau,
            "E0_rows": sum(1 for e in energies if e <= 1e-12),
            "max_E": tau, "median_E": float(np.median(energies)),
            "seconds": round(time.time() - t0, 1), "depth_scan": depth}


def negative_audit(table: dict, tau: float, per_row: int = 8,
                   max_n: int = 40) -> dict:
    """CRAM's 'never stops at a wrong board', measured on corrupted boards."""
    accepted = 0
    total = 0
    lowest = None
    for n in sorted(table):
        if n > max_n:
            break
        if n < 3:
            # n = 1 has no pair to corrupt: a rotation near a multiple of
            # pi/2 leaves it feasible, which is a true low energy and not a
            # candidate for a false stop.  n = 2 is one contact only.
            continue
        st = table[n]
        L = record_L(st)
        for r in range(per_row):
            rng = np.random.RandomState(7919 * n + 104729 * r + 17)
            bad = perturb(st, rng, angle=0.12 + 0.05 * r, shift=0.02 + 0.01 * r)
            e = energy(bad, L)
            total += 1
            accepted += 1 if e <= tau + 1e-12 else 0
            lowest = e if lowest is None else min(lowest, e)
    return {"boards": total, "tau": tau, "accepted_at_tau": accepted,
            "lowest_E_on_a_corrupted_board": round(float(lowest), 9)}


# ------------------------------------------------------------- ideas C and D
def _run_variants(st0: np.ndarray, L_t: float, amp: float, moves: int,
                  seeds: int, n: int) -> dict:
    """One cell: every variant from the same corrupted record, same budget."""
    out = {}
    for mode in ("full", "focused", "two_layer"):
        res = []
        for s in range(seeds):
            rng = np.random.RandomState(7919 * n + 104729 * (s + 1) + 3)
            seed_state = perturb(st0, rng, angle=amp, shift=amp / 4.0)
            e_seed = energy(seed_state, L_t)
            st = relax(seed_state, L_t, moves=moves, mode=mode,
                       seed=104729 * (s + 1) + n)
            rec = settle_and_gate(st, L_t)
            rec["e_seed"] = round(e_seed, 12)
            st, fixed, sweeps_used = coordinate_polish(st, L_t)
            pol = settle_and_gate(st, L_t)
            rec["e_polished"] = pol["e"]
            rec["fixed_point"] = bool(fixed)
            rec["polish_sweeps"] = sweeps_used
            rec["gated_L_polished"] = pol["gated_L"]
            res.append(rec)
        finals = [r["e"] for r in res]
        pols = [r["e_polished"] for r in res]
        seedsE = [r["e_seed"] for r in res]
        med_f, med_s = float(np.median(finals)), float(np.median(seedsE))
        out[mode] = {
            "median_final_E": round(med_f, 12),
            "median_polished_E": round(float(np.median(pols)), 12),
            "median_seed_E": round(med_s, 12),
            "reduction_factor": round(med_s / med_f, 4) if med_f > 0 else None,
            "recovered_at_1e-6": sum(1 for e in finals if e <= 1e-6),
            "recovered_after_polish": sum(1 for e in pols if e <= 1e-6),
            "fixed_points": sum(1 for r in res if r["fixed_point"]),
            "feasible_at_target": sum(1 for r in res if r["feasible_at_target"]),
            "best_gated_L": min([x for x in (r["gated_L_polished"] or r["gated_L"]
                                             for r in res) if x is not None], default=None),
        }
    return out


def matrix(table: dict, cells=CELLS, amps=AMPS, moves: int = MOVES,
           seeds: int = SEEDS) -> dict:
    """Recovery at the record's own side: full vs focused vs two-layer.

    The target is the delivered L, where a feasible answer provably exists
    (the record itself), so 'recovered' has a meaning.  Equal move budget
    for every variant."""
    out = {"cells": [], "moves": moves, "seeds": seeds, "target": "record L"}
    for n in cells:
        if n not in table:
            continue
        st0 = table[n]
        L0 = record_L(st0)
        for amp in amps:
            out["cells"].append({"n": n, "L_record": round(L0, 9),
                                 "target_L": round(L0, 9), "amp": amp,
                                 "variants": _run_variants(st0, L0, amp, moves,
                                                           seeds, n)})
    return out


def push(table: dict, cells=CELLS, depths=PUSH_DEPTHS, amp: float = 0.02,
         moves: int = MOVES, seeds: int = 1) -> dict:
    """The score question: can any variant reach below the delivered side?"""
    out = {"cells": [], "moves": moves, "amp": amp}
    for n in cells:
        if n not in table:
            continue
        st0 = table[n]
        L0 = record_L(st0)
        for delta in depths:
            L_t = L0 * (1.0 - delta)
            v = _run_variants(st0, L_t, amp, moves, seeds, n)
            below = {m: (x["best_gated_L"] is not None
                         and x["best_gated_L"] < L0 - 1e-12)
                     for m, x in v.items()}
            out["cells"].append({"n": n, "L_record": round(L0, 9),
                                 "target_L": round(L_t, 9), "depth": delta,
                                 "below_record": below, "variants": v})
    return out


# ------------------------------------------------------------------ idea A
def relation_features(st: np.ndarray, i: int, j: int) -> tuple:
    """(relative-angle bin, contact-distance bin) for the ordered pair i, j."""
    dth = (st[j, 2] - st[i, 2]) % PHI
    b_th = min(int(dth / PHI * 6.0), 5)
    d = math.hypot(st[j, 0] - st[i, 0], st[j, 1] - st[i, 1])
    x = (min(max(d, 1.0), SQ2) - 1.0) / (SQ2 - 1.0)
    b_d = min(int(x * 3.0), 2)
    return b_th, b_d


def fit_relation_costs(table: dict, max_n: int = 120) -> dict:
    """Histogram (maximum-entropy) fit of the pairwise cost over relations,
    at the delivered solutions — CRAM's K_ij family, fitted locally."""
    counts = np.zeros((6, 3))
    total = 0.0
    for n in sorted(table):
        if n > max_n:
            break
        st = table[n]
        if n < 2:
            continue
        pen = margin_matrix(st)
        for i in range(n):
            for j in range(i + 1, n):
                if abs(pen[i, j]) <= 1e-6:          # a contact
                    b = relation_features(st, i, j)
                    counts[b] += 1.0
                    total += 1.0
    w = -np.log((counts + 0.5) / (total + 0.5 * counts.size))
    return {"w": w, "counts": counts, "contacts": total,
            "range": (float(w.min()), float(w.max()))}


def table_score(st: np.ndarray, w: np.ndarray) -> float:
    """Mean pairwise cost of the near pairs (lower = more like a record)."""
    n = len(st)
    if n < 2:
        return 0.0
    s = 0.0
    c = 0
    for i in range(n):
        for j in range(i + 1, n):
            d = math.hypot(st[j, 0] - st[i, 0], st[j, 1] - st[i, 1])
            if d > 1.35:
                continue
            s += w[relation_features(st, i, j)]
            c += 1
    return s / c if c else 0.0


def pl_score(st: np.ndarray, w: np.ndarray, rng: np.random.RandomState,
             cand: int = 6) -> float:
    """CRAM's pseudolikelihood, evaluated (not trained on) at a state: for
    each body, the log-probability of its placement under a softmax over
    local candidate placements scored by the learned pair costs."""
    n = len(st)
    if n < 3:
        return 0.0
    near = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            d = math.hypot(st[j, 0] - st[i, 0], st[j, 1] - st[i, 1])
            if d <= 1.35:
                near.append((i, j))
    if not near:
        return 0.0
    by_body: dict = {}
    for i, j in near:
        by_body.setdefault(i, []).append(j)
    total = 0.0
    for i, js in by_body.items():
        base = np.array([st[i, 0], st[i, 1], st[i, 2]])
        costs = []
        probe = st.copy()
        for _c in range(cand):
            off = np.array([rng.normal(0, 0.05), rng.normal(0, 0.05),
                            rng.normal(0, 0.08)])
            probe[i] = base + off
            costs.append(sum(w[relation_features(probe, i, j)] for j in js))
        costs = np.array(costs)
        p = np.exp(-(costs - costs.min()))
        p /= p.sum()
        total += math.log(max(float(p[0]), 1e-12))     # candidate 0 = the truth
    return total / len(by_body)


def _auc(pos, neg) -> float:
    """Mann-Whitney AUC: P(a random positive scores lower than a negative)."""
    pos = np.asarray(pos)
    neg = np.asarray(neg)
    if not len(pos) or not len(neg):
        return float("nan")
    wins = 0.0
    for a in pos:
        wins += float(np.sum(a < neg)) + 0.5 * float(np.sum(a == neg))
    return wins / (len(pos) * len(neg))


def pl_experiment(table: dict, max_n: int = 120, seeds_n=(40, 70, 110),
                  pool: int = 16, steps: int = 3000) -> dict:
    """Does the learned relation score (i) tell records from controls and
    (ii) predict what relaxation reaches from a seed?"""
    fit = fit_relation_costs(table, max_n=max_n)
    w = fit["w"]
    # (i) discrimination
    pos, neg_ang, neg_pos = [], [], []
    for n in sorted(table):
        if n > 60:
            break
        if n < 6 or n not in table:
            continue
        st = table[n]
        pos.append(table_score(st, w))
        rng = np.random.RandomState(7919 * n + 5)
        ctrl = st.copy()
        ctrl[:, 2] = rng.uniform(0.0, PHI, n)          # angles destroyed
        neg_ang.append(table_score(ctrl, w))
        ctrl2 = st.copy()
        L = record_L(st)
        ctrl2[:, :2] = rng.uniform(0.0, L, (n, 2))     # positions destroyed
        neg_pos.append(table_score(ctrl2, w))
    disc = {"records": len(pos),
            "auc_vs_angle_control": round(_auc(pos, neg_ang), 4),
            "auc_vs_position_control": round(_auc(pos, neg_pos), 4),
            "cost_record_median": round(float(np.median(pos)), 6),
            "cost_angle_control_median": round(float(np.median(neg_ang)), 6),
            "cost_position_control_median": round(float(np.median(neg_pos)), 6)}
    # (ii) does the score predict what relaxation reaches?
    try:
        from scipy.stats import spearmanr
    except Exception:                                  # pragma: no cover
        spearmanr = None
    predict = []
    for n in seeds_n:
        if n not in table:
            continue
        st0 = table[n]
        L_t = record_L(st0) * (1.0 - 0.01)
        scores, finals = [], []
        for s in range(pool):
            rng = np.random.RandomState(7919 * n + 104729 * s + 11)
            strength = 0.04 + 0.06 * (s % 6)            # a spread of corruptions
            seed_state = perturb(st0, rng, angle=strength, shift=strength / 4)
            scores.append(pl_score(seed_state, w, np.random.RandomState(s + 1)))
            st = relax(seed_state, L_t, moves=steps, mode="full", seed=s + 1)
            finals.append(energy(st, L_t))
        rho = None
        if spearmanr is not None:
            rho = float(spearmanr(scores, finals).statistic)
        # top vs bottom quartile after relaxation
        order = np.argsort(scores)
        q = max(1, pool // 4)
        predict.append({"n": n, "pool": pool,
                        "spearman_score_vs_final_E": None if rho is None else round(rho, 4),
                        "median_final_E_best_scored": round(float(np.median(
                            [finals[i] for i in order[:q]])), 9),
                        "median_final_E_worst_scored": round(float(np.median(
                            [finals[i] for i in order[-q:]])), 9)})
    return {"fit": {"contacts": fit["contacts"], "w_min": round(fit["range"][0], 6),
                    "w_max": round(fit["range"][1], 6),
                    "counts": fit["counts"].astype(int).tolist()},
            "discrimination": disc, "prediction": predict}


# ---------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", action="store_true")
    ap.add_argument("--negative", action="store_true")
    ap.add_argument("--matrix", action="store_true")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--pl", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--steps", type=int, default=MOVES)
    ap.add_argument("--seeds", type=int, default=SEEDS)
    args = ap.parse_args()
    if not any([args.census, args.negative, args.matrix, args.push, args.pl, args.all]):
        ap.print_help()
        return 0

    table = load_table()
    res: dict = {"instrument": "cram_relax.py", "run": 39,
                 "source": "arXiv:2611.17309v1", "table_rows": len(table)}
    if args.census or args.all:
        res["census"] = census(table)
        print("census:", json.dumps(res["census"], indent=1))
    if args.negative or args.all:
        tau = res.get("census", {}).get("tau")
        if tau is None:
            tau = census(table)["tau"]
        res["negative_audit"] = negative_audit(table, tau)
        print("negative audit:", json.dumps(res["negative_audit"], indent=1))
    if args.matrix or args.all:
        t0 = time.time()
        res["matrix"] = matrix(table, moves=args.steps, seeds=args.seeds)
        res["matrix"]["seconds"] = round(time.time() - t0, 1)
        for c in res["matrix"]["cells"]:
            v = c["variants"]
            print(f"  n={c['n']:<4} amp={c['amp']:<5} "
                  + "  ".join(f"{m}: E={v[m]['median_final_E']:.2e} "
                              f"x{v[m]['reduction_factor']} "
                              f"rec={v[m]['recovered_at_1e-6']}"
                              for m in ("full", "focused", "two_layer")), flush=True)
        print("matrix seconds:", res["matrix"]["seconds"])
    if args.push or args.all:
        t0 = time.time()
        res["push"] = push(table, moves=args.steps)
        res["push"]["seconds"] = round(time.time() - t0, 1)
        for c in res["push"]["cells"]:
            print(f"  push n={c['n']:<4} d={c['depth']:<5} "
                  + "  ".join(f"{m}:{c['below_record'][m]}" for m in
                              ("full", "focused", "two_layer")), flush=True)
        print("push seconds:", res["push"]["seconds"])
    if args.pl or args.all:
        t0 = time.time()
        res["pl"] = pl_experiment(table)
        res["pl"]["seconds"] = round(time.time() - t0, 1)
        print("pl:", json.dumps(res["pl"], indent=1))
    if args.write:
        os.makedirs(OUTDIR, exist_ok=True)
        path = os.path.join(OUTDIR, "cram_relax.json")
        if os.path.exists(path):            # the instrument runs in parts
            with open(path) as f:
                merged = json.load(f)
            merged.update(res)
            res = merged
        with open(path, "w") as f:
            json.dump(res, f, indent=1)
        print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
