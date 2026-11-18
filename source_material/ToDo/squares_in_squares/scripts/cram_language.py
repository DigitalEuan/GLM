#!/usr/bin/env python3
r"""cram_language.py — Run 40: the language as the objective, the stir as a
collective move.

WHAT RUN 39 LEFT, AND WHAT THIS TESTS.  `06-CRAM-RELAX.md` measured the four
CRAM mechanisms and found one transfer (A: the learned relation cost ranks
seeds — AUC 1.000 against an angle control, 0.794 against a position control,
Spearman 0.37-0.74 with where relaxation lands) and two refusals (B: the
calibrated threshold is degenerate at tau = 0; C: focused relaxation is *worse*
at n = 240 with 6x the per-body moves).  The reading taken from it is that the
packing energy is a **gate, not a landscape**: E = 0 *is* feasibility, so every
feasible packing is a global minimum and E cannot prefer the deeper
arrangement.  What distinguishes a grid from a record is which *relations* the
packing uses — and that quantity is graded.

This instrument tests the two consequences:

  PL-1  THE GRADED OBJECTIVE.  Descend

            F = E(state, L) + lam * cbar(state)

        where cbar is the mean learned relation cost of the near pairs
        (`cram_relax.table_score`, the instrument idea A was measured with).
        Two schedules:
          graded  lam applies throughout the chain.
          tail    lam applies only in the improving-only polish tail:
                  feasibility first, then the language — the "constraint,
                  not objective" form the run-39 reading actually implies.
        lam = 0 is the control and **must reproduce run 39's `full` column**;
        `--check` tests exactly that before any lam > 0 arm is trusted.

  PL-2  THE STIR.  A collective move: a body and its k nearest neighbours move
        together, rigidly (translation, and a rotation about the patch
        centroid with probability 0.3).  This is the move a focused Gibbs step
        cannot make and the move run 39's negative names — the interior is
        load-bearing, so a rearrangement needs *coordinated* displacement
        rather than a frozen subset.  Equal move budget and k = 4, so the arm
        receives 4x the body displacements of the single-body arms: a loss is
        strong evidence, a win is provisional and is labelled so.

THE ENERGY, unchanged from run 39.  `cram_relax.energy` — the W36/W37 hinge
with translation-free walls (the container is the packing's own bounding box):

    E(state, L) = sum_{i<j} max(0, pen_ij)^2 + max(0, w-L)^2 + max(0, h-L)^2

and the near-pair relation cost is `cram_relax`'s `NEAR = 1.35` radius, the
six angle bins x three distance bins of the idea-A table, fitted at the
delivered solutions over rows n <= 120.

ONE INHERITED CONVENTION, RECORDED RATHER THAN SILENTLY FIXED.  The run-39
sampler's acceptance quantity uses `0.5 * d_local` for the pair increment
(`cram_relax.relax`), which is half the true increment even though its
*absolute* value is E.  Reproducing it exactly is what makes the lam = 0
control bit-identical, so it is reproduced here; every number this instrument
*reports* is `cram_relax.energy` on the returned state, never the proxy.

EXACTNESS DISCIPLINE.  Float arithmetic measures; `packlib.finalize` +
`packlib.verify` decide.  Every reported feasibility is the gate's, and the
gate's L is reported beside the instrument's E.

DETERMINISM.  `RandomState` seeded from the puzzle count and the seed index,
the run-39 derivation (`7951 * n + 104729 * (s + 1) + n`) with its own offset
per arm, no wall clock.

Usage:
    python3 scripts/cram_language.py --check          # recovery test (lam = 0)
    python3 scripts/cram_language.py --graded --write # PL-1
    python3 scripts/cram_language.py --patch --write  # PL-2
    python3 scripts/cram_language.py --all --write
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
sys.path.insert(0, HERE)
import cram_relax as CR                                    # noqa: E402

OUTDIR = CR.OUTDIR
STORED = os.path.join(OUTDIR, "cram_relax.json")
LEDGER = os.path.join(OUTDIR, "cram_language.json")

#: Mean relation cost is O(0.6 .. 7.4); E at these cells is O(6e-4 .. 1.2).
#: lam spans "slightly" (0.01) to "the language dominates" (1.0).
LAMS = (0.0, 0.01, 0.1, 1.0)
TAIL_LAMS = (0.1, 1.0)
PATCH_LAMS = (0.0, 0.1)
#: PL-10: the smoothed potential's weights.  The step function saturated by
#: 1e-3; a continuous potential has a real range, so these span both sides of
#: the measured crossover (dE ~ 1e-5 per move, d cbar_smooth ~ 1e-5 .. 1e-3).
SMOOTH_LAMS = (0.0, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0)

TRAIN_AMPS = (0.002, 0.005, 0.01, 0.02, 0.06)
#: The λ grid the training cells are measured on.  It runs to 1e8 because the
#: min-max fit sat at the old 1e4 clamp: a fit that cannot look above its own
#: ceiling has not found an interior optimum.
TRAIN_LAMS = (0.0, 1.0, 10.0, 100.0, 1e3, 1e4, 1e6, 1e8)
#: The lifted clamp for both the rule and the fit.
LAM_MAX = 1e12
#: Patch size for the collective move (the stir's smallest collective unit).
PATCH_K = 4
#: The near-pair radius of the idea-A table, as `table_score` uses it.
NEAR = 1.35


# ------------------------------------------------------------ the language
def _pair_cost(ti, xi, yi, tj, xj, yj, w) -> tuple:
    """(learned cost, 1) for a near pair, (0, 0) for a non-pair."""
    d = math.hypot(xj - xi, yj - yi)
    if d > NEAR:
        return 0.0, 0
    dth = (tj - ti) % CR.PHI
    b_th = min(int(dth / CR.PHI * 6.0), 5)
    x = (min(max(d, 1.0), CR.SQ2) - 1.0) / (CR.SQ2 - 1.0)
    b_d = min(int(x * 3.0), 2)
    return float(w[b_th, b_d]), 1


def _cost_from_table(w):
    """The run-40 step-function cost, as a callable of the same shape."""
    def f(ti, xi, yi, tj, xj, yj):
        return _pair_cost(ti, xi, yi, tj, xj, yj, w)
    return f


def local_lang(k: int, X, Y, TH, cost) -> tuple:
    """(sum of learned costs, count) over body k's near pairs."""
    n = len(X)
    s, c = 0.0, 0
    for j in range(n):
        if j == k:
            continue
        a, b = cost(TH[k], X[k], Y[k], TH[j], X[j], Y[j])
        s += a
        c += b
    return s, c


def total_lang(X, Y, TH, cost) -> tuple:
    """(sum, count) over every unordered near pair of the state."""
    n = len(X)
    s, c = 0.0, 0
    for i in range(n):
        for j in range(i + 1, n):
            a, b = cost(TH[i], X[i], Y[i], TH[j], X[j], Y[j])
            s += a
            c += b
    return s, c


def _patch_lang_delta(P, X, Y, TH, X0, Y0, TH0, cost) -> tuple:
    """Delta (sum, count) over every pair touching the patch.  O(k n)."""
    n = len(X)
    inP = {int(i) for i in P}
    dS, dC = 0.0, 0
    for i in sorted(inP):
        for j in range(n):
            if j in inP and j <= i:
                continue
            a_new, b_new = cost(TH[i], X[i], Y[i], TH[j], X[j], Y[j])
            a_old, b_old = cost(TH0[i], X0[i], Y0[i], TH0[j], X0[j], Y0[j])
            dS += a_new - a_old
            dC += b_new - b_old
    return dS, dC


# ------------------------------------- PL-10: the C1 potential (kernel density)
#: The fine grid the smoothed potential lives on, and the kernel widths: one
#: half of each histogram bin, so the smoothing is the smallest one that
#: removes the discontinuity the run-40 slope probe measured.
G_TH, G_D = 360, 240
H_TH_DEG = 7.5
H_D = 0.069


def fit_smooth(table: dict, max_n: int = 120) -> dict:
    """Kernel-density version of the idea-A table: a potential with a slope.

    The histogram table of run 39/40 is piecewise constant, so its local
    behaviour is a jump and no weight `lam` exists at which it acts as a
    gradient (run 40, `--slope`).  This fits the same 21,602 contacts as a
    probability *density* over (relative angle, contact distance) on a fine
    grid, smoothed by a Gaussian with one half-bin of bandwidth, and returns
    `U = -log p`.  The gradient is then nonzero everywhere, and `lam` can be
    tuned through a genuine intermediate regime.
    """
    from scipy.ndimage import gaussian_filter

    counts = np.zeros((G_TH, G_D))
    total = 0
    for n in sorted(table):
        if n > max_n:
            break
        st = table[n]
        if n < 2:
            continue
        pen = CR.margin_matrix(st)
        for i in range(n):
            xi_, yi_ = st[i, 0], st[i, 1]
            for j in range(i + 1, n):
                if abs(pen[i, j]) > 1e-6:
                    continue
                dth = (st[j, 2] - st[i, 2]) % CR.PHI
                d = math.hypot(st[j, 0] - xi_, st[j, 1] - yi_)
                a = min(int(dth / CR.PHI * G_TH), G_TH - 1)
                b = min(int((d - 1.0) / (CR.SQ2 - 1.0) * G_D), G_D - 1)
                counts[a, b] += 1.0
                total += 1
    sig = (H_TH_DEG / 90.0 * G_TH, H_D / (CR.SQ2 - 1.0) * G_D)
    dens = gaussian_filter(counts, sigma=sig, mode=("wrap", "nearest"))
    cell_area = (CR.PHI / G_TH) * ((CR.SQ2 - 1.0) / G_D)
    dens = dens / (max(total, 1) * cell_area)
    U = -np.log(dens + 1e-9)
    return {"U": U, "contacts": total, "sigma_bins": [round(s, 3) for s in sig],
            "cell_area": cell_area, "range": [float(U.min()), float(U.max())],
            "grid": [G_TH, G_D]}


def smooth_cost(pot: dict):
    """The smoothed potential as a per-pair cost, bilinearly interpolated."""
    U = pot["U"]
    gth, gd = U.shape
    dspan = CR.SQ2 - 1.0

    def f(ti, xi, yi, tj, xj, yj):
        d = math.hypot(xj - xi, yj - yi)
        if d > NEAR:
            return 0.0, 0
        u = (tj - ti) % CR.PHI / CR.PHI * gth - 0.5
        i0 = int(math.floor(u))
        fu = u - i0
        i0 %= gth
        i1 = (i0 + 1) % gth
        v = (min(max(d, 1.0), CR.SQ2) - 1.0) / dspan * (gd - 1)
        j0 = min(max(int(math.floor(v)), 0), gd - 2)
        fv = min(max(v - j0, 0.0), 1.0)
        j1 = j0 + 1
        a = U[i0, j0] * (1.0 - fu) + U[i1, j0] * fu
        b = U[i0, j1] * (1.0 - fu) + U[i1, j1] * fu
        return float(a * (1.0 - fv) + b * fv), 1
    return f


def smooth_mean(st: np.ndarray, cost) -> float:
    """Mean smoothed cost of the near pairs — the same functional as `cbar`."""
    n = len(st)
    s, c = 0.0, 0
    for i in range(n):
        for j in range(i + 1, n):
            a, b = cost(st[i, 2], st[i, 0], st[i, 1], st[j, 2], st[j, 0], st[j, 1])
            s += a
            c += b
    return s / c if c else 0.0


def grade(st: np.ndarray, L: float, w: np.ndarray) -> tuple:
    """(E, cbar) at a state — the two quantities every table reports."""
    return CR.energy(st, L), CR.table_score(st, w)


# ------------------------------------------------- PL-1: the graded descent
def relax_graded(state: np.ndarray, L: float, w: np.ndarray, lam: float,
                 moves: int = CR.MOVES, seed: int = 0, t0: float = 0.02,
                 tail_only: bool = False, cost=None,
                 rotate_frac: float = 0.3,
                 rot_amp: float | None = None) -> np.ndarray:
    """Single-body Gibbs on F = E + lam * cbar.  lam = 0 is run 39's `full`.

    The move grammar, the temperature schedule, the RNG call order and the
    acceptance convention are `cram_relax.relax`'s, so that lam = 0 returns
    the same chain bit for bit and a lam > 0 difference is a difference of
    objective alone.
    """
    X = state[:, 0].copy()
    Y = state[:, 1].copy()
    TH = state[:, 2].copy()
    n = len(X)
    HW = CR.hw_vals(TH)
    rng = np.random.RandomState(seed)
    cand = np.arange(n, dtype=int)
    if cost is None:
        cost = _cost_from_table(w)

    S, C = total_lang(X, Y, TH, cost)

    def point_cost() -> float:
        return CR.wall_cost(X, Y, HW, L) + 0.5 * sum(
            CR.local_pair_cost(i, X, Y, TH, HW) for i in range(n))

    cur = point_cost()
    cbar = (S / C) if C else 0.0
    F = cur + lam * cbar
    best = F
    best_state = state.copy()
    t_sa = int(moves * 0.85)
    T = t0
    decay = (1e-5 / t0) ** (1.0 / max(1, t_sa - 1))
    for it in range(moves):
        polish = it >= t_sa
        if it == t_sa and tail_only:
            # Entering the tail: the objective changes, so the incumbent is
            # re-decided on the new one.  The annealer's best and the current
            # point are both scored with the *same* function, and the better
            # is kept — a plain restart would discard the annealer's best and
            # read as a property of the objective, which it is not.
            cur_st = np.stack([X, Y, TH], axis=1)
            S, C = total_lang(X, Y, TH, cost)
            cbar = (S / C) if C else 0.0
            e_cur, c_cur = grade(cur_st, L, w)
            e_b, c_b = grade(best_state, L, w)
            F_cur = e_cur + lam * c_cur
            F_b = e_b + lam * c_b
            cur, cbar = e_cur, c_cur
            if F_b <= F_cur:
                F, best = F_cur, F_b
            else:
                F = best = F_cur
                best_state = cur_st.copy()
        lam_it = 0.0 if (tail_only and not polish) else lam
        k_i = int(cand[rng.randint(len(cand))])
        ps = 0.0015 if polish else max(1e-5, 0.6 * T)
        as_ = 0.0015 if polish else max(1e-5, 0.9 * T)
        old_x, old_y, old_t, old_hw = X[k_i], Y[k_i], TH[k_i], HW[k_i]
        pk = CR.pair_pen_row(k_i, X, Y, TH, HW)
        old_local = float(np.dot(pk, pk))
        old_wall = CR.wall_cost(X, Y, HW, L)
        s_old, c_old = local_lang(k_i, X, Y, TH, cost) if lam_it else (0.0, 0)
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
            # PL-19: the angle step was tied to the anneal temperature (0.9*T)
            # and collapsed to +/-0.0015 rad in polish, so angles were frozen
            # where the jam formed.  `rot_amp` overrides that amplitude; the
            # default reproduces the old behaviour bit for bit.
            amp_rot = as_ if rot_amp is None else rot_amp
            TH[k_i] = old_t + rng.uniform(-amp_rot, amp_rot)
            HW[k_i] = CR.hw_vals(np.array([TH[k_i]]))[0]
        pk_new = CR.pair_pen_row(k_i, X, Y, TH, HW)
        d_local = float(np.dot(pk_new, pk_new)) - old_local
        d_wall = CR.wall_cost(X, Y, HW, L) - old_wall
        if lam_it:
            s_new, c_new = local_lang(k_i, X, Y, TH, cost)
            S2, C2 = S + (s_new - s_old), C + (c_new - c_old)
            d_cbar = ((S2 / C2) if C2 else 0.0) - cbar
        else:
            s_new = c_new = 0.0
            d_cbar = 0.0
        dF = 0.5 * d_local + d_wall + lam_it * d_cbar
        if dF <= 0 or (not polish and rng.uniform() < math.exp(-dF / max(T, 1e-12))):
            cur += 0.5 * d_local + d_wall
            if lam_it:
                S, C = S + (s_new - s_old), C + (c_new - c_old)
                cbar = (S / C) if C else 0.0
            F = cur + lam_it * cbar
            if F < best - 1e-18:
                best = F
                best_state = np.stack([X, Y, TH], axis=1)
        else:
            X[k_i], Y[k_i], TH[k_i], HW[k_i] = old_x, old_y, old_t, old_hw
        if not polish:
            T = max(T * decay, 1e-5)
    return best_state.copy()


# ------------------------------------------------ PL-2: the collective stir
def relax_patch(state: np.ndarray, L: float, w: np.ndarray, lam: float,
                moves: int = CR.MOVES, seed: int = 0, t0: float = 0.02,
                k: int = PATCH_K, cost=None) -> np.ndarray:
    """Metropolis on F over a *collective* proposal: k bodies move together.

    The patch is a random body plus its k-1 nearest neighbours, moved rigidly
    (translation; a rotation about the centroid with probability 0.3).  The
    boundary of the patch is untouched, so this is the coordinated motion a
    one-body move cannot produce — the thing run 39's focused arm removed by
    freezing the interior.
    """
    X = state[:, 0].copy()
    Y = state[:, 1].copy()
    TH = state[:, 2].copy()
    n = len(X)
    HW = CR.hw_vals(TH)
    rng = np.random.RandomState(seed)
    k = min(k, n)
    if cost is None:
        cost = _cost_from_table(w)

    S, C = total_lang(X, Y, TH, cost)

    def point_cost() -> float:
        return CR.wall_cost(X, Y, HW, L) + 0.5 * sum(
            CR.local_pair_cost(i, X, Y, TH, HW) for i in range(n))

    cur = point_cost()
    cbar = (S / C) if C else 0.0
    F = cur + lam * cbar
    best = F
    best_state = state.copy()
    t_sa = int(moves * 0.85)
    T = t0
    decay = (1e-5 / t0) ** (1.0 / max(1, t_sa - 1))
    for it in range(moves):
        polish = it >= t_sa
        ps = 0.0015 if polish else max(1e-5, 0.6 * T)
        as_ = 0.0015 if polish else max(1e-5, 0.9 * T)
        i0 = int(rng.randint(n))
        d2 = (X - X[i0]) ** 2 + (Y - Y[i0]) ** 2
        P = np.argsort(d2)[:k]
        X0, Y0, TH0 = X.copy(), Y.copy(), TH.copy()
        old_wall = CR.wall_cost(X, Y, HW, L)
        old_terms = 0.0
        for i in P:
            pk = CR.pair_pen_row(int(i), X, Y, TH, HW)
            old_terms += float(np.dot(pk, pk))
        dx = rng.uniform(-ps, ps)
        dy = rng.uniform(-ps, ps)
        do_rot = rng.uniform() < 0.3
        if do_rot:
            dth = rng.uniform(-as_, as_)
            co, si = math.cos(dth), math.sin(dth)
            cx, cy = float(X[P].mean()), float(Y[P].mean())
            rx, ry = X[P] - cx, Y[P] - cy
            X[P] = cx + co * rx - si * ry + dx
            Y[P] = cy + si * rx + co * ry + dy
            TH[P] = TH[P] + dth
        else:
            X[P] += dx
            Y[P] += dy
        HW[P] = CR.hw_vals(TH[P])
        new_terms = 0.0
        for i in P:
            pk = CR.pair_pen_row(int(i), X, Y, TH, HW)
            new_terms += float(np.dot(pk, pk))
        d_wall = CR.wall_cost(X, Y, HW, L) - old_wall
        d_cbar = 0.0
        dS = dC = 0.0
        if lam:
            dS, dC = _patch_lang_delta(P, X, Y, TH, X0, Y0, TH0, cost)
            S2, C2 = S + dS, C + dC
            d_cbar = ((S2 / C2) if C2 else 0.0) - cbar
        dF = 0.5 * (new_terms - old_terms) + d_wall + lam * d_cbar
        if dF <= 0 or (not polish and rng.uniform() < math.exp(-dF / max(T, 1e-12))):
            cur += 0.5 * (new_terms - old_terms) + d_wall
            if lam:
                S, C = S + dS, C + dC
                cbar = (S / C) if C else 0.0
            F = cur + lam * cbar
            if F < best - 1e-18:
                best = F
                best_state = np.stack([X, Y, TH], axis=1)
        else:
            X[P], Y[P], TH[P] = X0[P], Y0[P], TH0[P]
            HW[P] = CR.hw_vals(TH[P])
        if not polish:
            T = max(T * decay, 1e-5)
    return best_state.copy()


# ------------------------------------------------------------- the campaign
def _arm(st0, w, L_t, amp, moves, seeds, n, name: str, fn, lam: float,
         tail_only: bool = False, cost=None) -> dict:
    """One arm over one cell: the same corrupted seeds, the same budget."""
    res = []
    for s in range(seeds):
        rng = np.random.RandomState(7919 * n + 104729 * (s + 1) + 3)
        seed_state = CR.perturb(st0, rng, angle=amp, shift=amp / 4.0)
        kw = {"moves": moves, "seed": 104729 * (s + 1) + n}
        if tail_only:
            kw["tail_only"] = True
        if cost is not None:
            kw["cost"] = cost
        st = fn(seed_state, L_t, w, lam, **kw)
        c_raw = float(CR.table_score(st, w))
        rec = CR.settle_and_gate(st, L_t)
        rec["cbar_final"] = round(c_raw, 6)
        rec["e_seed"] = round(CR.energy(seed_state, L_t), 12)
        rec["cbar_seed"] = round(float(CR.table_score(seed_state, w)), 6)
        st2, fixed, sweeps_used = CR.coordinate_polish(st, L_t)
        pol = CR.settle_and_gate(st2, L_t)
        e_pol, c_pol = grade(st2, L_t, w)
        rec["e_polished"] = round(float(e_pol), 12)
        rec["cbar_polished"] = round(float(c_pol), 6)
        if cost is not None:
            rec["cbar_smooth_seed"] = round(float(smooth_mean(seed_state, cost)), 6)
            rec["cbar_smooth_final"] = round(float(smooth_mean(st, cost)), 6)
            rec["cbar_smooth_polished"] = round(float(smooth_mean(st2, cost)), 6)
        rec["fixed_point"] = bool(fixed)
        rec["polish_sweeps"] = sweeps_used
        rec["gated_L_polished"] = pol["gated_L"]
        res.append(rec)
    finals = [r["e"] for r in res]
    pols = [r["e_polished"] for r in res]
    cbars = [r["cbar_polished"] for r in res]
    seedsE = [r["e_seed"] for r in res]
    med_f = float(np.median(finals))
    med_s = float(np.median(seedsE))
    return {
        "arm": name,
        "lam": lam,
        "tail_only": tail_only,
        "median_final_E": round(med_f, 12),
        "median_polished_E": round(float(np.median(pols)), 12),
        "median_seed_E": round(med_s, 12),
        "median_cbar_seed": round(float(np.median([r["cbar_seed"] for r in res])), 6),
        "median_cbar_final": round(float(np.median([r["cbar_final"] for r in res])), 6),
        "median_cbar_polished": round(float(np.median(cbars)), 6),
        "reduction_factor": round(med_s / med_f, 4) if med_f > 0 else None,
        "recovered_at_1e-6": sum(1 for e in finals if e <= 1e-6),
        "recovered_after_polish": sum(1 for e in pols if e <= 1e-6),
        "fixed_points": sum(1 for r in res if r["fixed_point"]),
        "feasible_at_target": sum(1 for r in res if r["feasible_at_target"]),
        "best_gated_L": min([x for x in (r["gated_L_polished"] or r["gated_L"]
                                         for r in res) if x is not None], default=None),
        "median_cbar_smooth_polished": (
            round(float(np.median([r["cbar_smooth_polished"] for r in res])), 6)
            if cost is not None else None),
    }


def campaign(table: dict, w: np.ndarray, arm: str, lams, tail_only: bool,
             cells=CR.CELLS, amps=CR.AMPS, moves: int = CR.MOVES,
             seeds: int = CR.SEEDS, cost=None, label: str | None = None) -> dict:
    fn = relax_patch if arm == "patch" else relax_graded
    lab = label or arm
    out = {"arm": arm, "label": lab, "moves": moves, "seeds": seeds,
           "lams": list(lams), "cost": ("smooth" if cost is not None else "table"),
           "cells": []}
    for n in cells:
        if n not in table:
            continue
        st0 = table[n]
        L0 = CR.record_L(st0)
        for amp in amps:
            entry = {"n": n, "L_record": round(L0, 9), "target_L": round(L0, 9),
                     "amp": amp, "arms": []}
            for lam in lams:
                entry["arms"].append(_arm(st0, w, L0, amp, moves, seeds, n,
                                          arm, fn, lam, tail_only, cost))
            out["cells"].append(entry)
            print(f"  {lab:<9} n={n:<4} amp={amp:<5} " + "  ".join(
                f"lam={a['lam']}: E={a['median_final_E']:.2e} "
                f"cbar={a['median_cbar_polished']:.3f}" for a in entry["arms"]),
                flush=True)
    return out


# --------------------------------------------------------- the recovery test
def check(table: dict, w: np.ndarray, probes=((20, 0.01), (110, 0.04))) -> dict:
    """lam = 0 must reproduce run 39's `full` column exactly.

    Failure 14 of this project's own ledger: a heuristic is only trustworthy
    after it recovers a known answer.  This is that test for the new loop.
    """
    with open(STORED) as f:
        stored = json.load(f)
    ref = {(c["n"], c["amp"]): c["variants"]["full"] for c in stored["matrix"]["cells"]}
    rows = []
    for n, amp in probes:
        st0 = table[n]
        L0 = CR.record_L(st0)
        got = _arm(st0, w, L0, amp, CR.MOVES, CR.SEEDS, n, "graded",
                   relax_graded, 0.0)
        exp = ref[(n, amp)]
        ok = (abs(got["median_final_E"] - exp["median_final_E"]) < 1e-12
              and abs(got["median_polished_E"] - exp["median_polished_E"]) < 1e-12
              and got["recovered_at_1e-6"] == exp["recovered_at_1e-6"])
        rows.append({"n": n, "amp": amp,
                     "stored_final_E": exp["median_final_E"],
                     "reproduced_final_E": got["median_final_E"],
                     "stored_polished_E": exp["median_polished_E"],
                     "reproduced_polished_E": got["median_polished_E"],
                     "recovered": [exp["recovered_at_1e-6"], got["recovered_at_1e-6"]],
                     "match": bool(ok)})
        print(f"  check n={n} amp={amp}: stored {exp['median_final_E']:.3e} "
              f"-> {got['median_final_E']:.3e}  "
              f"{'MATCH' if ok else 'MISMATCH'}", flush=True)
    return {"probes": rows, "all_match": all(r["match"] for r in rows)}


# ------------------------------- PL-11: the weight as a rule, not a selection
#: The rule: `lam = (excess / e0)^2`, where `excess` is the seed's own mean
#: learned cost minus the record's (both under the smoothed potential).  The
#: square is the shape a density maximum gives: near the maximum the potential
#: rises quadratically with the departure, so a force that tracks the
#: departure grows quadratically in the excess.  `e0` is the only free
#: constant and it is fitted on a grid DISJOINT from the 16 test cells.
RULE_E0_DEFAULT = 0.01


def auto_lambda(seed_state: np.ndarray, record_state: np.ndarray, cost,
                e0: float = RULE_E0_DEFAULT) -> float:
    """The weight the rule assigns, from the seed and the record alone."""
    excess = smooth_mean(seed_state, cost) - smooth_mean(record_state, cost)
    return float(min(LAM_MAX, max(1e-9, (max(excess, 0.0) / e0) ** 2)))


def fit_rule(table: dict, w: np.ndarray, cost, cells=(30, 80, 150, 300),
             amps=(0.02, 0.06), lams=(0.1, 1.0, 10.0, 100.0, 1000.0),
             moves: int = CR.MOVES, seeds: int = CR.SEEDS) -> dict:
    """Fit `e0` on cells that are not the test cells.

    For each training cell the λ grid is measured once; the rule's predicted λ
    is then read off that grid by log-log interpolation, and `e0` minimises the
    mean |log ratio| over the training cells.  One parameter, disjoint cells.
    """
    grid = []
    for n in cells:
        if n not in table:
            continue
        st0 = table[n]
        L0 = CR.record_L(st0)
        for amp in amps:
            e_seed, e_lam = [], []
            base_e = None
            for lam in (0.0,) + tuple(lams):
                es = []
                for s in range(seeds):
                    rng = np.random.RandomState(7919 * n + 104729 * (s + 1) + 3)
                    s0 = CR.perturb(st0, rng, angle=amp, shift=amp / 4.0)
                    if lam == 0.0 and s == 0:
                        e_seed.append(smooth_mean(s0, cost))
                    st = relax_graded(s0, L0, w, lam, moves=moves,
                                      seed=104729 * (s + 1) + n, cost=cost)
                    st2, _, _ = CR.coordinate_polish(st, L0)
                    es.append(CR.energy(st2, L0))
                med = float(np.median(es))
                if lam == 0.0:
                    base_e = med
                else:
                    e_lam.append((lam, med))
            excess = float(np.median(e_seed)) - smooth_mean(st0, cost)
            grid.append({"n": n, "amp": amp, "excess": excess,
                         "base_e": base_e,
                         "arms": [{"lam": l, "e": e} for l, e in e_lam]})
            print(f"  fit n={n:<4} amp={amp:<5} excess={excess:+.4f} "
                  + " ".join(f"{l}:{e/base_e:.2f}x" for l, e in e_lam), flush=True)

    def predicted_log_ratio(e0: float) -> float:
        tot, k = 0.0, 0
        for g in grid:
            lams_ = np.log10([a["lam"] for a in g["arms"]])
            rats = np.log10([a["e"] / g["base_e"] for a in g["arms"]])
            lam_hat = min(1e4, max(1e-3, (max(g["excess"], 0.0) / e0) ** 2))
            tot += abs(float(np.interp(math.log10(lam_hat), lams_, rats)))
            k += 1
        return tot / max(k, 1)

    cands = np.logspace(-4.5, -0.5, 120)
    scores = [(predicted_log_ratio(float(c)), float(c)) for c in cands]
    best = min(scores, key=lambda z: z[0])
    return {"e0": best[1], "mean_abs_log_ratio": round(best[0], 6),
            "cells": grid, "train_cells": list(cells), "train_amps": list(amps),
            "candidates": [round(float(c), 6) for c in cands]}


def _regret(g: dict, e0: float) -> float:
    """How far a given `e0` lands from the cell's own best λ, in log10.

    Regret, not |log ratio|: the ratio at λ -> 0 is 1.0 by construction, so
    minimising |log ratio| is minimised by switching the term off — which is
    exactly what the first fit did (it chose e0 at the top of its range).
    Regret is measured against each cell's best measured λ, so 'do nothing'
    has regret |log best| > 0.
    """
    lams_ = np.log10([a["lam"] for a in g["arms"]])
    rats = np.log10([a["e"] / g["base_e"] for a in g["arms"]])
    lam_hat = min(LAM_MAX, max(1e-9, (max(g["excess"], 0.0) / e0) ** 2))
    return float(np.interp(math.log10(lam_hat), lams_, rats)) - float(np.min(rats))


def refit_from_grid(grid: list, criterion: str = "minmax") -> dict:
    """Refit `e0` on the SAME measured training grid, changing only the criterion.

    minmax  minimise the maximum regret over the training cells — seek the
            intersection of their plateaus rather than their centre.
    mean    minimise the mean regret (reported for comparison).
    """
    def score(e0: float) -> tuple:
        regs = [_regret(g, e0) for g in grid]
        return (max(regs) if criterion == "minmax" else float(np.mean(regs))), regs

    cands = np.logspace(-9.0, 2.0, 331)
    best = min(((score(float(c))[0], float(c)) for c in cands), key=lambda z: z[0])
    e0 = best[1]
    _, regs = score(e0)
    lams = [min(LAM_MAX, max(1e-9, (max(g["excess"], 0.0) / e0) ** 2)) for g in grid]
    # the degeneracy the old criterion suffered, shown rather than asserted
    def mean_abs_log(e0x: float) -> float:
        tot = 0.0
        for g in grid:
            lams_ = np.log10([a["lam"] for a in g["arms"]])
            rats = np.log10([a["e"] / g["base_e"] for a in g["arms"]])
            lam_hat = min(LAM_MAX, max(1e-9, (max(g["excess"], 0.0) / e0x) ** 2))
            tot += abs(float(np.interp(math.log10(lam_hat), lams_, rats)))
        return tot / len(grid)

    return {"criterion": criterion, "e0": e0,
            "max_regret": round(best[0], 6),
            "mean_regret": round(float(np.mean(regs)), 6),
            "regret_by_cell": [round(r, 6) for r in regs],
            "lam_by_cell": [round(l, 4) for l in lams],
            "excess_by_cell": [round(g["excess"], 6) for g in grid],
            "mean_abs_log_ratio_at_fit": round(mean_abs_log(e0), 6),
            "mean_abs_log_ratio_at_e0_10": round(mean_abs_log(10.0), 6),
            "degeneracy_note": ("mean |log ratio| falls as e0 grows (λ -> 0, ratio "
                                "-> 1.0), so it is minimised by switching the term "
                                "off; the first fit chose the top of its range"),
            "cells": grid}


_W: dict = {}


def _init_worker(table, w, cost, moves):
    _W.update(table=table, w=w, cost=cost, moves=moves)


def _cell_task(args):
    """One (n, amp) cell: the whole λ ladder, seeds inside."""
    n, amp, lams, seeds = args
    table, w, cost, moves = _W["table"], _W["w"], _W["cost"], _W["moves"]
    st0 = table[n]
    L0 = CR.record_L(st0)
    c_rec = smooth_mean(st0, cost)
    arms = []
    base_e = None
    e_seed = []
    for lam in lams:
        es = []
        for s in range(seeds):
            rng = np.random.RandomState(7919 * n + 104729 * (s + 1) + 3)
            s0 = CR.perturb(st0, rng, angle=amp, shift=amp / 4.0)
            if lam == 0.0 and s == 0:
                e_seed.append(smooth_mean(s0, cost))
            st = relax_graded(s0, L0, w, lam, moves=moves,
                              seed=104729 * (s + 1) + n, cost=cost)
            st2, _, _ = CR.coordinate_polish(st, L0)
            es.append(CR.energy(st2, L0))
        med = float(np.median(es))
        if lam == 0.0:
            base_e = med
        else:
            arms.append({"lam": lam, "e": med})
    return {"n": n, "amp": amp, "excess": float(np.median(e_seed)) - c_rec,
            "base_e": base_e, "arms": arms}


def proven_rows_all() -> list:
    """The full proved set: every row in `proven_floors` (156 rows, 1..961)."""
    path = os.path.join(os.path.dirname(HERE), "workspace/push/root_audit38.json")
    with open(path) as f:
        return sorted(int(k) for k in json.load(f)["proven_floors"])


def probe_amp01(table: dict, w: np.ndarray, cost, e0: float, seeds: int = 6,
                cells=CR.CELLS, amp: float = 0.01,
                moves: int = CR.MOVES) -> dict:
    """PL-15: is the amp-0.01 failure variance or an n-resonance?

    Six seeds per cell, both arms from the *same* perturbed seed state, so a
    ratio is a paired comparison.  The 16-cell test reported medians over two
    seeds; if the quantity is a limit cycle whose phase depends on the seed,
    two seeds is not a sample of it.  This reports the whole distribution.
    """
    out = []
    for n in cells:
        st0 = table[n]
        L0 = CR.record_L(st0)
        lam = None
        rows = []
        for s in range(seeds):
            rng = np.random.RandomState(7919 * n + 104729 * (s + 1) + 3)
            s0 = CR.perturb(st0, rng, angle=amp, shift=amp / 4.0)
            if s == 0:
                lam = auto_lambda(s0, st0, cost, e0)
            e = []
            for L in (0.0, lam):
                st = relax_graded(s0, L0, w, L, moves=moves,
                                  seed=104729 * (s + 1) + n, cost=cost)
                st2, _, _ = CR.coordinate_polish(st, L0)
                e.append(CR.energy(st2, L0))
            rows.append({"seed": s, "e_ctl": e[0], "e_rule": e[1],
                         "ratio": e[1] / e[0] if e[0] > 0 else None})
        rs = [r["ratio"] for r in rows if r["ratio"]]
        geo = math.exp(sum(math.log(x) for x in rs) / len(rs)) if rs else None
        geo2 = (math.exp(sum(math.log(x) for x in rs[:2]) / 2)
                if len(rs) >= 2 else None)
        out.append({"n": n, "amp": amp, "lam": lam, "seeds": rows,
                    "geo6": geo, "geo_first2": geo2,
                    "spread": (max(rs) / min(rs)) if rs else None,
                    "n_worse": sum(1 for x in rs if x > 1.05),
                    "n_better": sum(1 for x in rs if x < 0.95)})
        print(f"  probe n={n:<4} lam={lam:<7.4g} geo6 {geo:.3f} (first2 {geo2:.3f}) "
              f"spread {max(rs)/min(rs):.1f}x  "
              + " ".join(f"{x:.2f}" for x in rs), flush=True)
    allr = [x for c in out for x in (r["ratio"] for r in c["seeds"] if r["ratio"])]
    return {"cells": out, "amp": amp, "seeds_per_cell": seeds,
            "geo_all": math.exp(sum(math.log(x) for x in allr) / len(allr)) if allr else None,
            "spread_all": (max(allr) / min(allr)) if allr else None}


JAM_STATES = os.path.join(OUTDIR, "jam_states.json")


def dump_jam_states(table: dict, w: np.ndarray, cost, e0: float,
                    cells=CR.CELLS, amp: float = 0.02,
                    depths=(0.01, 0.02), seeds: int = 2,
                    moves: int = CR.MOVES) -> dict:
    """Reproduce the eight jammed push states and persist them.

    The push table records energies, not states, so the ⅀Δ classifier has
    nothing to read.  This re-runs the identical chains (same perturb, same
    seed derivation, same budget, same rule) and writes the final states, so
    the contact order at the jam can be classified without guessing.
    """
    states = []
    for n in cells:
        st0 = table[n]
        L0 = CR.record_L(st0)
        for depth in depths:
            L_t = L0 * (1.0 - depth)
            for s in range(seeds):
                rng = np.random.RandomState(7919 * n + 104729 * (s + 1) + 3)
                s0 = CR.perturb(st0, rng, angle=amp, shift=amp / 4.0)
                lam = auto_lambda(s0, st0, cost, e0)
                st = relax_graded(s0, L_t, w, lam, moves=moves,
                                  seed=104729 * (s + 1) + n, cost=cost)
                st2, _, _ = CR.coordinate_polish(st, L_t)
                states.append({"n": n, "depth": depth, "seed": s,
                               "lam": float(lam), "L_target": float(L_t),
                               "e": float(CR.energy(st2, L_t)),
                               "state": st2.tolist()})
                print(f"  jam state n={n:<4} d={depth:.2f} seed={s} "
                      f"lam={lam:.3f} E={CR.energy(st2, L_t):.3e}", flush=True)
    out = {"amp": amp, "depths": list(depths), "seeds": seeds, "e0": e0,
           "moves": moves, "states": states}
    with open(JAM_STATES, "w") as f:
        json.dump(out, f)
    print("wrote", JAM_STATES)
    return {"path": JAM_STATES, "states": len(states)}


ROT_FRAC, ROT_AMP = 0.5, 0.05


def push_rotation(table: dict, w: np.ndarray, cost, e0: float,
                  cells=CR.CELLS, amp: float = 0.02,
                  depths=(0.01, 0.02), seeds: int = CR.SEEDS,
                  moves: int = CR.MOVES, rotate_frac: float = ROT_FRAC,
                  rot_amp: float = ROT_AMP) -> dict:
    """PL-19: the push with a rotation-rich grammar.

    PL-18 classified the jam as liquid in 12 of 16 states — a dense
    one-parameter family whose missing freedom is angular.  The graded
    annealer already rotates, but at 3% probability and, in the polish phase,
    at +/-0.0015 rad, i.e. the angles are frozen where the jam forms.  This
    runs the same eight cells four ways so the cause is attributable rather
    than merely absent:

      ctl       lam = 0, default grammar      (the run-39 baseline)
      rule      the full-set rule's lam       (reproduces push_proven_all)
      rot_only  lam = 0, rotation-rich        (rotation alone)
      rot_rule  lam, rotation-rich            (the PL-19 treatment)
    """
    out = []
    states = []
    tags = ("ctl", "rule", "rot_only", "rot_rule")
    for n in cells:
        st0 = table[n]
        L0 = CR.record_L(st0)
        for depth in depths:
            L_t = L0 * (1.0 - depth)
            arm_e = {t: [] for t in tags}
            arm_gate = {t: [] for t in tags}
            lam_med = []
            for s in range(seeds):
                rng = np.random.RandomState(7919 * n + 104729 * (s + 1) + 3)
                s0 = CR.perturb(st0, rng, angle=amp, shift=amp / 4.0)
                lam = auto_lambda(s0, st0, cost, e0)
                lam_med.append(lam)
                arms = (("ctl", 0.0, False), ("rule", lam, False),
                        ("rot_only", 0.0, True), ("rot_rule", lam, True))
                for tag, la, rich in arms:
                    kw = ({"rotate_frac": rotate_frac, "rot_amp": rot_amp}
                          if rich else {})
                    st = relax_graded(s0, L_t, w, la, moves=moves,
                                      seed=104729 * (s + 1) + n,
                                      cost=cost, **kw)
                    st2, _, _ = CR.coordinate_polish(st, L_t)
                    gate = CR.settle_and_gate(st2, L_t)
                    arm_e[tag].append(CR.energy(st2, L_t))
                    arm_gate[tag].append(gate["gated_L"])
                    if tag == "rot_rule":
                        states.append({"n": n, "depth": depth, "seed": s,
                                       "lam": float(lam), "L_target": float(L_t),
                                       "e": float(CR.energy(st2, L_t)),
                                       "state": st2.tolist()})
            rec = {"n": n, "depth": depth,
                   "L_target": round(float(L_t), 9),
                   "lam": round(float(np.median(lam_med)), 6)}
            for t in tags:
                rec[f"{t}_e"] = round(float(np.median(arm_e[t])), 12)
                rec[f"{t}_gated_L"] = min(
                    [g for g in arm_gate[t] if g is not None], default=None)
            for t in ("rule", "rot_only", "rot_rule"):
                rec[f"ratio_{t}"] = (round(rec[f"{t}_e"] / rec["ctl_e"], 4)
                                      if rec["ctl_e"] else None)
            out.append(rec)
            gated = sum(1 for t in tags if rec[f"{t}_gated_L"] is not None)
            print(f"  push-rot n={n:<4} d={depth:.2f} lam={rec['lam']:<7.4g} "
                  f"rule {rec['ratio_rule']}x rot_only {rec['ratio_rot_only']}x "
                  f"rot_rule {rec['ratio_rot_rule']}x gated_arms {gated}/4",
                  flush=True)
    path = os.path.join(OUTDIR, "jam_states_rot.json")
    with open(path, "w") as f:
        json.dump({"amp": amp, "depths": list(depths), "seeds": seeds,
                   "rotate_frac": rotate_frac, "rot_amp": rot_amp,
                   "states": states}, f)
    summary = {t: sum(1 for r in out if r[f"{t}_gated_L"] is not None)
               for t in tags}
    print("  gated cells by arm:", summary, "-> states", path, flush=True)
    return {"cells": out, "rotate_frac": rotate_frac, "rot_amp": rot_amp,
            "gated_by_arm": summary, "states_path": path}


def train_grid_parallel(table: dict, w: np.ndarray, cost, rows, amps,
                        lams, moves: int, seeds: int = 1,
                        workers: int = 8, ckpt: str = None) -> list:
    """`train_grid` over the full proved set, sharded by (n, amp) cell.

    Measured cost is ~0.077 * n^0.77 s per chain, so the full set at 5 amps and
    8 lambdas is ~10.6 h serial and ~1.3 h on 8 cores.  Sharding by cell keeps
    every worker's eight chains adjacent in n, which balances the load better
    than sharding by chain.
    """
    import multiprocessing as mp
    done = {}
    if ckpt and os.path.exists(ckpt):
        with open(ckpt) as f:
            for line in f:
                try:
                    c = json.loads(line)
                except ValueError:
                    continue
                done[(c["n"], c["amp"])] = c
        print(f"  resuming with {len(done)} cells from {ckpt}", flush=True)
    tasks = [(int(n), float(a), tuple(lams), int(seeds))
             for n in rows for a in amps if (int(n), float(a)) not in done]
    grid = list(done.values())
    t0 = time.time()
    fh = open(ckpt, "a") if ckpt else None
    ctx = mp.get_context("fork")
    with ctx.Pool(min(workers, max(1, len(tasks))), initializer=_init_worker,
                  initargs=(table, w, cost, moves)) as pool:
        for k, cell in enumerate(pool.imap_unordered(_cell_task, tasks), 1):
            grid.append(cell)
            if fh:
                fh.write(json.dumps(cell) + "\n")
                fh.flush()
            if k % 20 == 0 or k == len(tasks):
                el = time.time() - t0
                print(f"  [{k}/{len(tasks)}] {el/60:.1f} min, "
                      f"eta {el/k*(len(tasks)-k)/60:.1f} min", flush=True)
    if fh:
        fh.close()
    grid.sort(key=lambda g: (g["n"], g["amp"]))
    return grid


def extend_grid(table: dict, w: np.ndarray, cost, grid: list,
                extra=(1e4, 1e5), moves: int = CR.MOVES,
                seeds: int = CR.SEEDS) -> list:
    """Measure the training grid above its current top λ.

    The min-max refit on the stored grid sat at the top of the measured range,
    which means it was extrapolating.  This measures the two λ values that
    bracket the question — does the language term keep helping as it becomes
    total, or does it turn over? — on the training cells only.
    """
    out = []
    for g in grid:
        n, amp = int(g["n"]), float(g["amp"])
        st0 = table[n]
        L0 = CR.record_L(st0)
        arms = list(g["arms"])
        for lam in extra:
            if any(abs(a["lam"] - lam) < 1e-12 for a in arms):
                continue
            es = []
            for s in range(seeds):
                rng = np.random.RandomState(7919 * n + 104729 * (s + 1) + 3)
                s0 = CR.perturb(st0, rng, angle=amp, shift=amp / 4.0)
                st = relax_graded(s0, L0, w, lam, moves=moves,
                                  seed=104729 * (s + 1) + n, cost=cost)
                st2, _, _ = CR.coordinate_polish(st, L0)
                es.append(CR.energy(st2, L0))
            arms.append({"lam": lam, "e": float(np.median(es))})
        arms.sort(key=lambda a: a["lam"])
        out.append({**g, "arms": arms})
        print(f"  extend n={n:<4} amp={amp:<5} "
              + " ".join(f"{a['lam']:g}:{a['e']/g['base_e']:.2f}x" for a in arms),
              flush=True)
    return out


def proven_census(table: dict, w: np.ndarray) -> dict:
    """What a training grid of *known optimal* packings actually contains.

    The owner's suggestion: train the relation language on all known optimal
    packings up to n = 10,000.  What exists locally is the delivered table, n
    <= 1000, of which the proven-optimal rows are the four infinite families
    plus the individual proofs (`root_audit38.json` -> `proven_floors`).  This
    census measures what those packings look like in the relation alphabet, so
    the question 'would that be a better training grid' has a number.
    """
    with open(os.path.join(OUTDIR, "root_audit38.json")) as f:
        ra = json.load(f)
    floors = sorted(int(k) for k in ra["proven_floors"])
    rows = [n for n in floors if n in table]

    def cell_share(row_set, cap=None):
        counts = np.zeros((6, 3))
        total = 0
        for n in row_set:
            if cap is not None and n > cap:
                continue
            st = table[n]
            if n < 2:
                continue
            pen = CR.margin_matrix(st)
            idx = np.argwhere(np.abs(pen) <= 1e-6)
            if not len(idx):
                continue
            iu, ju = idx[:, 0], idx[:, 1]
            keep = ju > iu
            iu, ju = iu[keep], ju[keep]
            dth = (st[ju, 2] - st[iu, 2]) % CR.PHI
            d = np.hypot(st[ju, 0] - st[iu, 0], st[ju, 1] - st[iu, 1])
            aa = np.minimum((dth / CR.PHI * 6.0).astype(int), 5)
            xx = (np.clip(d, 1.0, CR.SQ2) - 1.0) / (CR.SQ2 - 1.0)
            bb = np.minimum((xx * 3.0).astype(int), 2)
            for a1, b1 in zip(aa, bb):
                counts[a1, b1] += 1.0
            total += int(len(iu))
        vac = float(counts[0, 0] + counts[0, 2])
        return {"rows": len([n for n in row_set if cap is None or n <= cap]),
                "contacts": int(total),
                "vacuum_cells": int(vac),
                "vacuum_share": round(vac / total, 4) if total else None,
                "counts": counts.astype(int).tolist()}

    return {"proven_rows": len(rows), "proven_n_range": [min(rows), max(rows)] if rows else None,
            "table_max_n": max(table), "proven": cell_share(rows),
            "all_rows_le_120": cell_share(sorted(table), cap=120),
            "note": ("the proven-optimal set is the four infinite lattice families "
                     "(k^2, k^2-1..k^2-4) plus individual proofs; a training grid "
                     "built from it fits the vacuum, not the seam")}


def _rule_cell(st0, w, cost, e0, L_t, amp, moves, seeds, n, record=None) -> dict:
    """One cell, two chains per seed: lam = 0, and the rule's own lam."""
    rec = st0 if record is None else record
    out = []
    for s in range(seeds):
        rng = np.random.RandomState(7919 * n + 104729 * (s + 1) + 3)
        seed_state = CR.perturb(st0, rng, angle=amp, shift=amp / 4.0)
        lam = auto_lambda(seed_state, rec, cost, e0)
        row = {"lam": round(lam, 6), "e_seed": CR.energy(seed_state, L_t)}
        for tag, la in (("control", 0.0), ("rule", lam)):
            st = relax_graded(seed_state, L_t, w, la, moves=moves,
                              seed=104729 * (s + 1) + n, cost=cost)
            st2, fixed, _ = CR.coordinate_polish(st, L_t)
            gate = CR.settle_and_gate(st2, L_t)
            row[tag] = {"e_anneal": CR.energy(st, L_t), "e": CR.energy(st2, L_t),
                        "cbar": smooth_mean(st2, cost),
                        "gated_L": gate["gated_L"],
                        "feasible": gate["feasible_at_target"],
                        "fixed_point": bool(fixed)}
        out.append(row)
    med = lambda k: float(np.median([r[k]["e"] for r in out]))
    c0, c1 = med("control"), med("rule")
    return {"lam": round(float(np.median([r["lam"] for r in out])), 6),
            "control_e": round(c0, 12), "rule_e": round(c1, 12),
            "ratio": round(c1 / c0, 4) if c0 > 0 else None,
            "control_cbar": round(float(np.median([r["control"]["cbar"] for r in out])), 6),
            "rule_cbar": round(float(np.median([r["rule"]["cbar"] for r in out])), 6),
            "rule_gated_L": min([r["rule"]["gated_L"] for r in out
                                 if r["rule"]["gated_L"] is not None], default=None),
            "control_gated_L": min([r["control"]["gated_L"] for r in out
                                    if r["control"]["gated_L"] is not None], default=None),
            "rows": out}


def rule_campaign(table: dict, w: np.ndarray, cost, e0: float,
                  cells=CR.CELLS, amps=CR.AMPS, moves: int = CR.MOVES,
                  seeds: int = CR.SEEDS, depths=None) -> dict:
    """The rule applied once per cell — no per-cell choice, so no selection.

    With `depths` given, the target side is squeezed (the score question:
    aim below the record); otherwise the target is the record's own side.
    """
    out = {"e0": e0, "moves": moves, "seeds": seeds,
           "depths": list(depths) if depths else None, "cells": []}
    for n in cells:
        if n not in table:
            continue
        st0 = table[n]
        L0 = CR.record_L(st0)
        for amp in amps:
            for d in (depths if depths else (0.0,)):
                L_t = L0 * (1.0 - d)
                entry = _rule_cell(st0, w, cost, e0, L_t, amp, moves, seeds, n)
                entry.update({"n": n, "amp": amp, "depth": d,
                              "L_record": round(L0, 9), "target_L": round(L_t, 9)})
                if d:
                    entry["below_record"] = (entry["rule_gated_L"] is not None
                                             and entry["rule_gated_L"] < L0 - 1e-12)
                out["cells"].append(entry)
                print(f"  rule n={n:<4} amp={amp:<5} d={d:<5} lam={entry['lam']:<9.4g} "
                      f"E {entry['control_e']:.3e} -> {entry['rule_e']:.3e} "
                      f"({entry['ratio']:.2f}x) gated_L={entry['rule_gated_L']}", flush=True)
    return out


def slope_probe(table: dict, w: np.ndarray, rows=(60, 240),
                eps=(1e-3, 1e-2, 1e-1), draws: int = 60) -> dict:
    """At what displacement does the learned cost acquire a slope at all?

    The relation cost is a step function of the pose: six 15-degree angle bins
    and three distance bins of width (sqrt2 - 1)/3 = 0.138.  A one-body move
    whose displacement does not cross a bin boundary leaves cbar *exactly*
    unchanged, so a descent on cbar has zero gradient there.  This measures
    the fraction of random perturbations of a delivered record that leave
    cbar identically unchanged, per step size — the resolution limit that
    decides whether "descend the language" is a well-posed instruction.
    """
    rows_out = []
    for n in rows:
        if n not in table:
            continue
        st = table[n]
        base = float(CR.table_score(st, w))
        for e in eps:
            rng = np.random.RandomState(7919 * n + int(round(e * 1e6)))
            zero = 0
            mags = []
            for _ in range(draws):
                st2 = st.copy()
                i = int(rng.randint(n))
                st2[i, 0] += rng.uniform(-e, e)
                st2[i, 1] += rng.uniform(-e, e)
                st2[i, 2] += rng.uniform(-e, e) * 0.9
                d = float(CR.table_score(st2, w)) - base
                if d == 0.0:
                    zero += 1
                mags.append(abs(d))
            rows_out.append({
                "n": n, "eps": e, "draws": draws,
                "zero_delta_fraction": round(zero / draws, 4),
                "median_abs_delta_cbar": float(np.median(mags)),
                "max_abs_delta_cbar": float(np.max(mags)),
            })
            print(f"  slope n={n:<4} eps={e:<7} zero-delta {zero/draws:.2f} "
                  f"median |d cbar| {float(np.median(mags)):.3e}", flush=True)
    return {"rows": rows_out}


#: Every action flag must leave a section behind.  A flag that parses but
#: produces nothing is the failure mode that let --dither sit dead in the CLI:
#: the audit below turns it into an error instead of a shrug.
FLAG_SECTION = {
    "slope": ("slope",),
    "check": ("recovery_check",),
    "graded": ("graded",),
    "tail": ("tail",),
    "patch": ("patch",),
    "smooth": ("smooth",),
    "patch_matched": ("patch_matched",),
    "fit_rule": ("rule_fit",),
    "rule": ("rule",),
    "push_rule": ("push_rule",),
    "refit_minmax": ("rule_fit_minmax",),
    "rule_minmax": ("rule_minmax",),
    "push_rule_minmax": ("push_rule_minmax",),
    "proven_census": ("proven_census",),
    "extend_lams": ("rule_fit", "extended_with"),
    "fit_proven_all": ("rule_fit_proven_all",),
    "rule_proven_all": ("rule_proven_all",),
    "push_proven_all": ("push_proven_all",),
    "probe_amp01": ("probe_amp01",),
    "dump_jam_states": ("jam_states_dump",),
    "push_rotation": ("push_rotation",),
}


def audit_flags(args, res: dict) -> list:
    """Return the action flags that ran without leaving any output."""
    missing = []
    for flag, path in FLAG_SECTION.items():
        if not getattr(args, flag):
            continue
        node = res
        for key in path:
            node = node.get(key) if isinstance(node, dict) else None
        if node is None:
            missing.append("--" + flag.replace("_", "-"))
    return missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slope", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--graded", action="store_true")
    ap.add_argument("--tail", action="store_true")
    ap.add_argument("--patch", action="store_true")
    ap.add_argument("--smooth", action="store_true")
    ap.add_argument("--fit-rule", action="store_true")
    ap.add_argument("--rule", action="store_true")
    ap.add_argument("--push-rule", action="store_true")
    ap.add_argument("--refit-minmax", action="store_true",
                    help="refit e0 on the stored training grid, min-max regret")
    ap.add_argument("--rule-minmax", action="store_true")
    ap.add_argument("--push-rule-minmax", action="store_true")
    ap.add_argument("--proven-census", action="store_true")
    ap.add_argument("--extend-lams", action="store_true",
                    help="measure the training grid at lambda 1e4 and 1e5, then refit")
    ap.add_argument("--fit-proven-all", action="store_true",
                    help="PL-17: same grid, but all 156 proved rows, 8 workers")
    ap.add_argument("--rule-proven-all", action="store_true")
    ap.add_argument("--push-proven-all", action="store_true")
    ap.add_argument("--probe-amp01", action="store_true",
                    help="PL-15: six seeds at amp 0.01, rule arm vs control")
    ap.add_argument("--push-rotation", action="store_true",
                    help="PL-19: the push at d=1%/2% with a rotation-rich grammar")
    ap.add_argument("--dump-jam-states", action="store_true",
                    help="write the eight jammed push states for the sigma-delta "
                         "classifier (scripts/delta_sigma_push.py --from-states)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--patch-matched", action="store_true",
                    help="the patch arm at matched displacement (moves / k)")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--steps", type=int, default=CR.MOVES)
    ap.add_argument("--seeds", type=int, default=CR.SEEDS)
    ap.add_argument("--quick", action="store_true",
                    help="two cells only (a smoke run, never a result)")
    args = ap.parse_args()
    if not any([args.slope, args.check, args.graded, args.tail, args.patch,
                args.smooth, args.patch_matched, args.fit_rule, args.rule,
                args.push_rule, args.refit_minmax, args.rule_minmax,
                args.push_rule_minmax, args.proven_census, args.extend_lams,
                args.fit_proven_all, args.rule_proven_all, args.push_proven_all,
                args.probe_amp01, args.dump_jam_states, args.push_rotation,
                args.all]):
        ap.print_help()
        return 0

    table = CR.load_table()
    w = CR.fit_relation_costs(table)["w"]
    cells = (20, 240) if args.quick else CR.CELLS
    amps = (0.01, 0.08) if args.quick else CR.AMPS
    res: dict = {"instrument": "cram_language.py", "run": 40,
                 "source": "06-CRAM-RELAX.md -> PL-1, PL-2",
                 "near_radius": NEAR, "patch_k": PATCH_K,
                 "table_rows": len(table)}
    if args.slope or args.all:
        t0 = time.time()
        res["slope"] = slope_probe(table, w)
        res["slope"]["seconds"] = round(time.time() - t0, 1)
    if args.check or args.all:
        t0 = time.time()
        res["recovery_check"] = check(table, w)
        res["recovery_check"]["seconds"] = round(time.time() - t0, 1)
        print("recovery check all_match:", res["recovery_check"]["all_match"])
    if args.graded or args.all:
        t0 = time.time()
        res["graded"] = campaign(table, w, "graded", LAMS, False,
                                 cells=cells, amps=amps,
                                 moves=args.steps, seeds=args.seeds)
        res["graded"]["seconds"] = round(time.time() - t0, 1)
    if args.tail or args.all:
        t0 = time.time()
        res["tail"] = campaign(table, w, "graded", TAIL_LAMS, True,
                               cells=cells, amps=amps,
                               moves=args.steps, seeds=args.seeds)
        res["tail"]["seconds"] = round(time.time() - t0, 1)
    if args.patch or args.all:
        t0 = time.time()
        res["patch"] = campaign(table, w, "patch", PATCH_LAMS, False,
                                cells=cells, amps=amps,
                                moves=args.steps, seeds=args.seeds)
        res["patch"]["seconds"] = round(time.time() - t0, 1)
    if args.smooth or args.all:
        t0 = time.time()
        pot = fit_smooth(table)
        cost = smooth_cost(pot)
        res["smooth_fit"] = {k: v for k, v in pot.items() if k != "U"}
        print("smooth fit:", json.dumps(res["smooth_fit"]), flush=True)
        res["smooth"] = campaign(table, w, "graded", SMOOTH_LAMS, False,
                                 cells=cells, amps=amps, moves=args.steps,
                                 seeds=args.seeds, cost=cost, label="smooth")
        res["smooth"]["seconds"] = round(time.time() - t0, 1)
    if args.patch_matched or args.all:
        t0 = time.time()
        res["patch_matched"] = campaign(
            table, w, "patch", PATCH_LAMS, False, cells=cells, amps=amps,
            moves=max(1, args.steps // PATCH_K), seeds=args.seeds,
            label="patch/matched")
        res["patch_matched"]["seconds"] = round(time.time() - t0, 1)
    if args.proven_census:
        t0 = time.time()
        res["proven_census"] = proven_census(table, w)
        res["proven_census"]["seconds"] = round(time.time() - t0, 1)
        print("proven census:", json.dumps({k: v for k, v in res["proven_census"].items()
                                            if k in ("proven_rows", "proven_n_range",
                                                     "table_max_n")}), flush=True)
        for tag in ("proven", "all_rows_le_120"):
            c = res["proven_census"][tag]
            print(f"  {tag}: rows {c['rows']} contacts {c['contacts']} "
                  f"vacuum share {c['vacuum_share']}", flush=True)

    if (args.fit_rule or args.rule or args.push_rule or args.all
            or args.refit_minmax or args.rule_minmax or args.push_rule_minmax
            or args.fit_proven_all or args.rule_proven_all
            or args.push_proven_all or args.probe_amp01
            or args.dump_jam_states or args.push_rotation):
        pot = fit_smooth(table)
        cost = smooth_cost(pot)
        res["smooth_fit"] = {k: v for k, v in pot.items() if k != "U"}
        if args.probe_amp01:
            e0p = res.get("rule_fit_proven_all", {}).get("e0")
            if e0p is None and os.path.exists(LEDGER):
                with open(LEDGER) as f:
                    e0p = json.load(f).get("rule_fit_proven_all", {}).get("e0")
            if e0p is None:
                print("warning: no full-proven e0 available")
            else:
                t0 = time.time()
                res["probe_amp01"] = probe_amp01(table, w, cost, e0p,
                                                 cells=cells, moves=args.steps)
                res["probe_amp01"]["e0"] = e0p
                res["probe_amp01"]["seconds"] = round(time.time() - t0, 1)
                print("probe amp 0.01 over all cells: geo_all",
                      res["probe_amp01"]["geo_all"])
        if args.push_rotation:
            e0r = res.get("rule_fit_proven_all", {}).get("e0")
            if e0r is None and os.path.exists(LEDGER):
                with open(LEDGER) as f:
                    e0r = json.load(f).get("rule_fit_proven_all", {}).get("e0")
            if e0r is None:
                print("warning: no full-proven e0 available")
            else:
                t0 = time.time()
                res["push_rotation"] = push_rotation(table, w, cost, e0r,
                                                    cells=cells,
                                                    moves=args.steps,
                                                    seeds=args.seeds)
                res["push_rotation"]["seconds"] = round(time.time() - t0, 1)
        if args.dump_jam_states:
            e0j = res.get("rule_fit_proven_all", {}).get("e0")
            if e0j is None and os.path.exists(LEDGER):
                with open(LEDGER) as f:
                    e0j = json.load(f).get("rule_fit_proven_all", {}).get("e0")
            if e0j is None:
                print("warning: no full-proven e0 available")
            else:
                t0 = time.time()
                res["jam_states_dump"] = dump_jam_states(table, w, cost, e0j,
                                                         cells=cells,
                                                         moves=args.steps)
                res["jam_states_dump"]["seconds"] = round(time.time() - t0, 1)
        if args.fit_proven_all:
            t0 = time.time()
            rows_all = [r for r in proven_rows_all() if r in table]
            grid_a = train_grid_parallel(
                table, w, cost, rows_all, TRAIN_AMPS, TRAIN_LAMS, args.steps,
                seeds=1, workers=args.workers,
                ckpt=os.path.join(OUTDIR, "train_proven_all.jsonl"))
            res["rule_fit_proven_all"] = refit_from_grid(grid_a, "minmax")
            res["rule_fit_proven_all"].update({
                "train_rows": rows_all, "train_n": len(rows_all),
                "train_amps": list(TRAIN_AMPS), "train_lams": list(TRAIN_LAMS),
                "seeds": 1, "lam_max": LAM_MAX, "workers": args.workers,
                "seconds": round(time.time() - t0, 1)})
            f = res["rule_fit_proven_all"]
            print("full-proven refit: e0 =", f["e0"], "max regret", f["max_regret"],
                  "mean regret", f["mean_regret"], flush=True)
        if args.rule_proven_all or args.push_proven_all:
            e0a = res.get("rule_fit_proven_all", {}).get("e0")
            if e0a is None and os.path.exists(LEDGER):
                with open(LEDGER) as f:
                    e0a = json.load(f).get("rule_fit_proven_all", {}).get("e0")
            if e0a is None:
                print("warning: no full-proven e0 available")
            else:
                if args.rule_proven_all:
                    t0 = time.time()
                    res["rule_proven_all"] = rule_campaign(
                        table, w, cost, e0a, cells=cells, amps=amps,
                        moves=args.steps, seeds=args.seeds)
                    res["rule_proven_all"]["seconds"] = round(time.time() - t0, 1)
                if args.push_proven_all:
                    t0 = time.time()
                    res["push_proven_all"] = rule_campaign(
                        table, w, cost, e0a, cells=cells, amps=(0.02,),
                        moves=args.steps, seeds=args.seeds, depths=(0.01, 0.02))
                    res["push_proven_all"]["seconds"] = round(time.time() - t0, 1)
        if args.extend_lams:
            stored = {}
            if os.path.exists(LEDGER):
                with open(LEDGER) as f:
                    stored = json.load(f)
            grid_in = stored.get("rule_fit", {}).get("cells")
            if not grid_in:
                print("no stored training grid; measuring it now")
                grid_in = fit_rule(table, w, cost, moves=args.steps,
                                   seeds=args.seeds)["cells"]
            t0 = time.time()
            grid_x = extend_grid(table, w, cost, grid_in, moves=args.steps,
                                 seeds=args.seeds)
            res.setdefault("rule_fit", {})["cells"] = grid_x
            res["rule_fit"]["extended_with"] = [1e4, 1e5]
            res["rule_fit"]["seconds_extend"] = round(time.time() - t0, 1)
            res["rule_fit_minmax"] = refit_from_grid(grid_x, "minmax")
            res["rule_fit_meanregret"] = refit_from_grid(grid_x, "mean")
            print("extended minmax refit: e0 =", res["rule_fit_minmax"]["e0"],
                  "max regret", res["rule_fit_minmax"]["max_regret"],
                  "mean regret", res["rule_fit_minmax"]["mean_regret"])
            print("  lam by cell:", res["rule_fit_minmax"]["lam_by_cell"])
        if args.refit_minmax or args.all:
            stored = {}
            if os.path.exists(LEDGER):
                with open(LEDGER) as f:
                    stored = json.load(f)
            grid = stored.get("rule_fit", {}).get("cells")
            if not grid:
                print("no stored training grid; measuring it now")
                grid = fit_rule(table, w, cost, moves=args.steps,
                                seeds=args.seeds)["cells"]
            res["rule_fit_minmax"] = refit_from_grid(grid, "minmax")
            res["rule_fit_meanregret"] = refit_from_grid(grid, "mean")
            print("minmax refit: e0 =", res["rule_fit_minmax"]["e0"],
                  "max regret", res["rule_fit_minmax"]["max_regret"],
                  "mean regret", res["rule_fit_minmax"]["mean_regret"])
            print("  lam by cell:", res["rule_fit_minmax"]["lam_by_cell"])
            print("  mean|log ratio|: at fit",
                  res["rule_fit_minmax"]["mean_abs_log_ratio_at_fit"],
                  "at e0=10", res["rule_fit_minmax"]["mean_abs_log_ratio_at_e0_10"])
        if args.rule_minmax or args.push_rule_minmax or args.all:
            e0m = res.get("rule_fit_minmax", {}).get("e0")
            if e0m is None and os.path.exists(LEDGER):
                with open(LEDGER) as f:
                    e0m = json.load(f).get("rule_fit_minmax", {}).get("e0")
            if e0m is None:
                print("warning: no min-max e0 available")
            else:
                if args.rule_minmax or args.all:
                    t0 = time.time()
                    res["rule_minmax"] = rule_campaign(table, w, cost, e0m,
                                                       cells=cells, amps=amps,
                                                       moves=args.steps,
                                                       seeds=args.seeds)
                    res["rule_minmax"]["seconds"] = round(time.time() - t0, 1)
                if args.push_rule_minmax or args.all:
                    t0 = time.time()
                    res["push_rule_minmax"] = rule_campaign(
                        table, w, cost, e0m, cells=cells, amps=(0.02,),
                        moves=args.steps, seeds=args.seeds, depths=(0.01, 0.02))
                    res["push_rule_minmax"]["seconds"] = round(time.time() - t0, 1)
        if args.fit_rule or args.all:
            t0 = time.time()
            res["rule_fit"] = fit_rule(table, w, cost, moves=args.steps,
                                       seeds=args.seeds)
            res["rule_fit"]["seconds"] = round(time.time() - t0, 1)
            print("rule fit: e0 =", res["rule_fit"]["e0"],
                  "mean |log ratio| =", res["rule_fit"]["mean_abs_log_ratio"])
        e0 = res.get("rule_fit", {}).get("e0")
        if e0 is None and os.path.exists(LEDGER):
            with open(LEDGER) as f:
                e0 = json.load(f).get("rule_fit", {}).get("e0")
        if e0 is None:
            e0 = RULE_E0_DEFAULT
            print("warning: no fitted e0 on the ledger; using the default")
        if args.rule or args.all:
            t0 = time.time()
            res["rule"] = rule_campaign(table, w, cost, e0, cells=cells,
                                        amps=amps, moves=args.steps,
                                        seeds=args.seeds)
            res["rule"]["seconds"] = round(time.time() - t0, 1)
        if args.push_rule or args.all:
            t0 = time.time()
            res["push_rule"] = rule_campaign(table, w, cost, e0, cells=cells,
                                             amps=(0.02,), moves=args.steps,
                                             seeds=args.seeds,
                                             depths=(0.01, 0.02))
            res["push_rule"]["seconds"] = round(time.time() - t0, 1)
    missing = audit_flags(args, res)
    if missing:
        print("ERROR: action flags produced no output (silent no-op):",
              ", ".join(missing))
        return 2

    if args.write:
        os.makedirs(OUTDIR, exist_ok=True)
        merged = {}
        if os.path.exists(LEDGER):
            with open(LEDGER) as f:
                merged = json.load(f)
        merged.update(res)
        with open(LEDGER, "w") as f:
            json.dump(merged, f, indent=1)
        print("wrote", LEDGER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
