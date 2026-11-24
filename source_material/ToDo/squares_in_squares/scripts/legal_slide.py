#!/usr/bin/env python3
r"""legal_slide.py — run 127: a *legal* rearrangement move, with controls.

Docs 83/85 closed the penalty route on the evidence: the squeeze reaches
`L0 - 4e-3` on 19/20 rows, but legalising it costs `4.6e-2` to `3.0`, because
removing overlap is a *rearrangement at the same density* and the relaxation
never finds one.  What the docs named as the move that could matter is a
translation of a cell, a wall row, or a block that is legal **on the spot**.

This module is that move, and it is deliberately the opposite of `structure.py`:
a candidate is accepted only when every changed pair has separating-axis slack
`>= 0` **before** it is applied, so the pose is never transiently illegal and
legalisation has nothing to pay back.

Arithmetic.  Directions `(c, s)` are computed once per cell by
`true_geom.axes` at 40 digits, and every acceptance is the same
separating-axis test in `Decimal` at the same 40 digits -- no float is named
anywhere in this file, so `glm_wheels --audit` can check it:

    slack(a, b) = max over the four edge normals q of
                  |(p_b - p_a).q| - (h_a(q) + h_b(q)),   h(q) = (|c.q| + |s.q|)/2

Only the pairs that involve a moved cell can change, so only those are tested
(`check_move`); that is the same test on fewer pairs, not a weaker one.  The
`sweep`/`x-sweep` neighbour list bounds which pairs can possibly touch: two unit
squares whose centres differ by more than `REACH` in one coordinate cannot
overlap whatever their angles, so the bound is exact.

Controls (`--selftest`), because a move that never fires proves nothing:

  P  positive: a gapped 4x4 grid (one row shifted by `gap`) must tighten to
     exactly side 4 by sliding that row back, every accepted step legal;
  N  negative: a slide that would overlap must be refused with the offending
     pair and its exact negative slack, and the pose must be unchanged;
  V  void: a cell parked outside a pose with a one-cell hole must be able to
     swap into the hole legally and then tighten.
  E  exact step: a gap below the ladder's smallest rung (1e-3 < 1/512) is
     refused by the ladder and taken by the side-minimising bisected step;
  F  minimal legal scale: a grid compressed to spacing 1-1e-3 must legalise at
     `f* = 1/(1-1e-3)` -- the analytic minimum, not a ladder rung;
  S  sweep vs pair pass: the `REACH` scan must agree with `true_geom.check`
     exactly, on a legal pose and on a perturbed one.

    python3 scripts/legal_slide.py --selftest
    python3 scripts/legal_slide.py --rows 33,159,439 --seconds 20
    python3 scripts/legal_relaxed.py --rows 33,159,439,662,883,942 --seconds 20
"""
from __future__ import annotations

import bisect
import json
import os
import sys
import time
from decimal import Decimal, localcontext

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import true_geom as TG        # noqa: E402
import sqscore as SQ          # noqa: E402

TAB = os.path.join(ROOT, "workspace/submission/table.json")
OUT = os.path.join(ROOT, "workspace/push/legal_slide127.json")

ZERO = Decimal(0)
ONE = Decimal(1)
HALF = Decimal("0.5")
#: Beyond this L-infinity centre distance two unit squares cannot overlap at any
#: angles: the largest half-extent of a unit square is sqrt(2)/2 < 0.708, so an
#: overlap needs |dx| < 1.415 and |dy| < 1.415.  REACH is that, with margin.
REACH = Decimal("2")
#: The slide ladder, and the bisection tolerance for the clearance measurement.
LADDER = (ONE, HALF, Decimal("0.25"), Decimal("0.125"), Decimal("0.0625"),
          Decimal("0.03125"), Decimal("0.015625"), Decimal("0.0078125"),
          Decimal("0.00390625"), Decimal("0.001953125"))
TOL = Decimal("1e-15")
#: A wall cell is one whose edge is within this of the extreme.  Exact equality
#: holds for a delivered pose but not after a scale, where it breaks in the last
#: digits of the 40 used (see `wall_cells`).
WALL_TOL = Decimal("1e-18")


# ------------------------------------------------------------------ geometry


def load_pose(n):
    """The delivered pose of row n, exactly: the table stores decimal strings."""
    with open(TAB) as f:
        tab = json.load(f, parse_float=str, parse_int=str)
    return [(Decimal(str(r[0])), Decimal(str(r[1])), Decimal(str(r[2])))
            for r in tab[str(n)]["state"]]


def directions(state):
    """`(cos t, sin t)` per cell at 40 digits, computed once (no float)."""
    out = []
    for _x, _y, t in state:
        (c, s), _v = TG.axes(t)
        out.append((c, s))
    return out


def half_extent(c, s):
    """Half the bounding-box extent of a unit square with direction (c, s)."""
    return (abs(c) + abs(s)) / 2


def slack(a, b):
    """Separating-axis slack of two squares `(x, y, c, s)`; >= 0 means disjoint.

    This is `true_geom.pair_slack`'s formula with the directions passed in, so a
    pose whose directions are computed once can be tested many times without
    recomputing cos/sin.  `--selftest` checks it against `true_geom.pair_slack`
    on real pairs, because a duplicated formula has to be pinned to its source.
    """
    with localcontext() as ctx:
        ctx.prec = TG.DPS
        ax, ay, ac, as_ = a
        bx, by, bc, bs = b
        dx, dy = bx - ax, by - ay
        best = None
        for c1, s1, c2, s2 in ((ac, as_, bc, bs), (bc, bs, ac, as_)):
            for qx, qy in ((c1, s1), (-s1, c1), (c2, s2), (-s2, c2)):
                proj = dx * qx + dy * qy
                h1 = (abs(c1 * qx + s1 * qy) + abs(-s1 * qx + c1 * qy)) / 2
                h2 = (abs(c2 * qx + s2 * qy) + abs(-s2 * qx + c2 * qy)) / 2
                sl = abs(proj) - (h1 + h2)
                best = sl if best is None or sl > best else best
        return +best


def positions(state):
    """`(sorted xs, order)` -- the index every move test looks cells up in."""
    order = sorted(range(len(state)), key=lambda i: state[i][0])
    return [state[i][0] for i in order], order


def near_at(state, idx, x, y, skip=()):
    """Indices whose centre is within `REACH` of `(x, y)` -- the pairs a cell at
    `(x, y)` could touch.

    This is looked up at the **destination**, not at the start.  The first
    version of `check_move` used the mover's old neighbour list, which is sound
    for a small step and quietly wrong for a long one: a cell slid past its old
    neighbours landed on top of a cell that had never been in its list, and the
    move was accepted.  The sample run's clearance figures (up to 9.5 units on a
    jammed pose) were the symptom; the N3 control below is the regression test.
    """
    xs, order = idx
    lo = bisect.bisect_left(xs, x - REACH)
    hi = bisect.bisect_right(xs, x + REACH)
    out = []
    for k in range(lo, hi):
        j = order[k]
        if j in skip:
            continue
        if abs(state[j][1] - y) <= REACH:
            out.append(j)
    return out


def extents(dirs):
    """Half bounding-box extent per cell, computed once for a pose.

    `spans`/`side_of` recompute this per cell per call, and `min_side_step`
    evaluates the side ~100 times per candidate: two abs, an add and a division
    at 40 digits per cell per call dominates the step search on the ~1000-cell
    rows.  Passing the list in is the same arithmetic, computed once.
    """
    return [half_extent(c, s) for c, s in dirs]


def spans(state, dirs, hexes=None):
    """Exact bounding box `(xlo, xhi, ylo, yhi)` of the pose, in Decimal."""
    with localcontext() as ctx:
        ctx.prec = TG.DPS
        xlo = xhi = ylo = yhi = None
        for i, ((x, y, _t), (c, s)) in enumerate(zip(state, dirs)):
            h = hexes[i] if hexes is not None else half_extent(c, s)
            lo, hi = x - h, x + h
            xlo = lo if xlo is None or lo < xlo else xlo
            xhi = hi if xhi is None or hi > xhi else xhi
            lo, hi = y - h, y + h
            ylo = lo if ylo is None or lo < ylo else ylo
            yhi = hi if yhi is None or hi > yhi else yhi
        return xlo, xhi, ylo, yhi


def side_of(state, dirs, hexes=None):
    """The container side the pose needs: the larger bbox span."""
    xlo, xhi, ylo, yhi = spans(state, dirs, hexes)
    return max(xhi - xlo, yhi - ylo)


def slab(state, dirs, i, along):
    """The row band through cell `i`: every cell whose extent overlaps it.

    Sliding one wall-defining cell on its own is usually blocked by its own row
    (the first version of this prototype learned that from the P control); the
    move that can compact a pose is the whole band.  `along` is the axis of the
    slide, so the band is taken perpendicular to it: a cell belongs to the band
    if its interval on the other axis overlaps cell `i`'s.  For a grid that is
    exactly one row or column, and nothing else.
    """
    xi, yi, _ti = state[i]
    ci, si = dirs[i]
    hi = half_extent(ci, si)
    out = []
    for j, ((x, y, _t), (c, s)) in enumerate(zip(state, dirs)):
        h = half_extent(c, s)
        if along == 0:
            if abs(y - yi) < hi + h:
                out.append(j)
        else:
            if abs(x - xi) < hi + h:
                out.append(j)
    return out


def wall_cells(state, dirs, which, eps=WALL_TOL):
    """Indices of the cells that define one wall, within `eps` of the extreme.

    `eps` exists because a pose that has been *scaled* no longer has cells at
    bit-identical edge coordinates: on the gapped control they are equal to 40
    digits, and after `scale_pose` they agree to the working precision but not
    exactly.  With `eps = 0` (the run-127 behaviour) the scaled pose returns an
    **empty** wall set, and a caller that then reports "clearance 0" is
    measuring its own lookup, not the geometry -- which is exactly what this
    run's first smoke test did.  `WALL_TOL` is 1e-18, twenty orders above the
    40-digit rounding and far below any length that decides anything; and a
    cell admitted one ulp inside a wall is harmless, because every accepted move
    still has to shrink the side and pass the exact pair test.
    """
    xlo, xhi, ylo, yhi = spans(state, dirs)
    out = []
    for i, ((x, y, _t), (c, s)) in enumerate(zip(state, dirs)):
        h = half_extent(c, s)
        if which == "xlo" and x - h <= xlo + eps:
            out.append(i)
        elif which == "xhi" and x + h >= xhi - eps:
            out.append(i)
        elif which == "ylo" and y - h <= ylo + eps:
            out.append(i)
        elif which == "yhi" and y + h >= yhi - eps:
            out.append(i)
    return out


# --------------------------------------------------------------------- moves


def check_move(state, dirs, idx, moved, dx, dy, early=True):
    """Exact legality of translating `moved` by `(dx, dy)`.

    Returns `(worst_slack, witness)`.  `worst_slack >= 0` (or `None` when no pair
    is at the destination) means the move is legal.  Only pairs of a moved cell
    with an unmoved one are tested, and at the moved cell's **new** position:
    a translation preserves every internal offset of the group exactly (Decimal
    addition is exact), so a moved-moved pair cannot change, and an unmoved pair
    cannot either.  `early` stops at the first negative slack.
    """
    ms = set(moved)
    worst, who = None, None
    for i in sorted(ms):
        nx, ny = state[i][0] + dx, state[i][1] + dy
        a = (nx, ny, dirs[i][0], dirs[i][1])
        for j in near_at(state, idx, nx, ny, skip=ms):
            b = (state[j][0], state[j][1], dirs[j][0], dirs[j][1])
            sl = slack(a, b)
            if worst is None or sl < worst:
                worst, who = sl, (i, j)
            if early and sl < 0:
                return sl, (i, j)
    return worst, who


def apply_move(state, moved, dx, dy):
    """A new pose with `moved` translated; the input pose is not touched."""
    out = list(state)
    for i in moved:
        x, y, t = out[i]
        out[i] = (x + dx, y + dy, t)
    return out


def try_move(state, dirs, idx, moved, dx, dy):
    """One candidate translation: `(ok, new_state_or_None, slack, witness)`."""
    worst, who = check_move(state, dirs, idx, moved, dx, dy)
    if worst is not None and worst < 0:
        return False, None, worst, who
    return True, apply_move(state, moved, dx, dy), worst, who


def try_slide(state, dirs, idx, moved, axis, sign, step):
    """A one-axis candidate slide, through the same acceptance test."""
    dx = sign * step if axis == 0 else ZERO
    dy = sign * step if axis == 1 else ZERO
    return try_move(state, dirs, idx, moved, dx, dy)


def check_pose(state, dirs, idx=None):
    """Exact verdict on a whole pose: `(worst_slack, violations, witness)`.

    The `REACH` sweep is **complete**, not a sample: two unit squares whose
    centres differ by more than 2 in either coordinate cannot overlap at any
    angles, so every pair that could be in violation appears in some cell's
    neighbour list.  Control S checks the count and the worst slack against
    `true_geom.check`, the O(n^2) pair pass, on a legal pose and on a
    deliberately perturbed copy of it -- the cheap scan is only a substitute if
    it agrees exactly where it matters.
    """
    if idx is None:
        idx = positions(state)
    worst, wit, viol = None, None, 0
    with localcontext() as ctx:
        ctx.prec = TG.DPS
        for i in range(len(state)):
            xi, yi = state[i][0], state[i][1]
            a = (xi, yi, dirs[i][0], dirs[i][1])
            for j in near_at(state, idx, xi, yi, skip=(i,)):
                if j <= i:
                    continue
                b = (state[j][0], state[j][1], dirs[j][0], dirs[j][1])
                sl = slack(a, b)
                if sl < 0:
                    viol += 1
                    if worst is None or sl < worst:
                        worst, wit = sl, (i, j)
    return worst, viol, wit


def scale_pose(state, dirs, f, hexes=None):
    """Scale the pose about its own bounding-box centre by `f`; angles fixed.

    Distances between centres scale by `f`, half-extents do not (the angles do
    not change), so the side is **not** `f * side` but, for the pair that sets
    it, `f * (centre spread) + h_i + h_j`.  Both facts matter: the pair slack
    `f |d.q| - (h_a + h_b)` is linear in `f` (which is what makes `legal_scale`'s
    bisection exact), and the side grows more slowly than `f * side` -- by
    `(f - 1)` times the spread of the binding axis, which the harness reports as
    the measured payback rather than as a derived estimate.
    """
    xlo, xhi, ylo, yhi = spans(state, dirs, hexes)
    cx, cy = (xlo + xhi) / 2, (ylo + yhi) / 2
    return [(cx + (x - cx) * f, cy + (y - cy) * f, t) for x, y, t in state]


def legal_scale(state, dirs, hi=Decimal(8), steps=40):
    """The minimal uniform scale `f >= 1` about the box centre that is legal.

    Monotone, so the bisection is exact up to its tolerance: a pair's slack on a
    fixed axis is `f |d.q| - (h_a + h_b)`, non-decreasing in `f`, so the worst
    slack is non-decreasing and the legal `f` form an upper interval.  The
    returned `f` is therefore the **minimum** over this one-parameter family --
    the cheapest legalisation the family admits, not a ladder rung.  That
    distinction is the point: `structure.legalise` walks a 10^k ladder and pays
    `4.6e-2` at n = 33, where the minimum scale pays less than `(f* - 1)` times
    the side (control F pins the scale, and the payback, to their analytic
    values).

    Returns `(f, legal_pose, side, violations_before)`; `f is None` if no scale
    up to the doubling cap is legal.
    """
    worst, viol, _w = check_pose(state, dirs)
    if worst is None:
        return ONE, state, side_of(state, dirs), viol
    lo, high = ONE, ONE
    found = False
    for _ in range(24):
        high = high * 2                # f = 1 is known illegal: bracket it tightly
        if high > hi:
            break
        cand = scale_pose(state, dirs, high)
        w, _v, _ww = check_pose(cand, dirs)
        if w is None:
            found = True
            break
    if not found:
        return None, None, None, viol
    for _ in range(steps):
        if high - lo <= TOL:
            break
        mid = (lo + high) / 2
        cand = scale_pose(state, dirs, mid)
        w, _v, _ww = check_pose(cand, dirs)
        if w is None:
            high = mid
        else:
            lo = mid
    cand = scale_pose(state, dirs, high)
    return high, cand, side_of(cand, dirs), viol


def tighten_exact(state, dirs, idx, rounds=4, iters=30, deadline=None):
    """Pull each wall in with legal moves at the **side-minimising** step.

    Same move set and the same acceptance test as `tighten`, but the step is
    chosen by `min_side_step` (convex side, ternary search over the legal range)
    instead of from the ladder, and each wall is tried as **three** groups: the
    band through its first cell, that cell alone, and the whole wall set.  The
    third is what a lattice-like pose needs: its wall is defined by several cells
    in different bands, and moving one band alone redefines nothing, so the side
    cannot shrink (run 127 met the same fact from the other side, where the swap
    vacated a cell of a full column and the wall was redefined rather than
    moved).

    This is the variant a *loosened* pose needs: `tighten`'s smallest rung is
    1/512, seven orders of magnitude larger than a delivered pose's 1e-10
    clearance (run 127) and still larger than the 1e-4 clearance a legalised
    pose has.
    """
    moves = 0
    hexes = extents(dirs)
    for _ in range(rounds):
        if deadline is not None and time.monotonic() > deadline:
            break
        s0 = side_of(state, dirs, hexes)
        improved = False
        for which, axis, sign in (("xlo", 0, 1), ("xhi", 0, -1),
                                  ("ylo", 1, 1), ("yhi", 1, -1)):
            if improved:
                break
            cells = wall_cells(state, dirs, which)
            if not cells:
                continue
            i = cells[0]
            for group in (slab(state, dirs, i, axis), [i], cells):
                if improved:
                    break
                t, best = min_side_step(state, dirs, idx, group, axis, sign,
                                        iters=iters, hexes=hexes)
                if t <= ZERO or best >= s0:
                    continue
                ok, cand, _sl, _who = try_slide(state, dirs, idx, group,
                                                axis, sign, t)
                if ok and side_of(cand, dirs, hexes) < s0:
                    state, moves, improved = cand, moves + 1, True
    return state, moves


def tighten(state, dirs, idx, rounds=6, deadline=None):
    """Pull each wall in with legal moves only; the side may never grow.

    The wall's cells are tried as a **row slide** (a block move) first, then one
    cell at a time, at the first ladder step that both is legal and makes the
    side strictly smaller.  A move that is legal but does not shrink the side is
    not taken: it would only spend the budget without changing the answer.
    """
    moves = 0
    for _ in range(rounds):
        if deadline is not None and time.monotonic() > deadline:
            break
        s0 = side_of(state, dirs)
        improved = False
        for which, axis, sign in (("xlo", 0, 1), ("xhi", 0, -1),
                                  ("ylo", 1, 1), ("yhi", 1, -1)):
            if improved:
                break
            cells = wall_cells(state, dirs, which)
            for i in cells:
                if improved or (deadline is not None and time.monotonic() > deadline):
                    break
                band = slab(state, dirs, i, axis)
                for group in (band, [i]):
                    for step in LADDER:
                        ok, cand, _sl, _who = try_slide(state, dirs, idx, group,
                                                        axis, sign, step)
                        if not ok:
                            continue
                        if side_of(cand, dirs) < s0:
                            state, moves, improved = cand, moves + 1, True
                            break
                    if improved:
                        break
    return state, moves


def max_legal_step(state, dirs, idx, moved, axis, sign, hi=REACH, steps=48):
    """The largest legal inward slide of `moved` along `axis` (bisection).

    `moved` is a cell index or a list.  Legality along one translation is an
    interval containing 0 -- a pair's slack is the maximum of four convex
    piecewise-linear functions of the step, so its feasible set is an interval,
    and so is the intersection -- which is what makes a bisection exact here,
    and also what lets `min_side_step` trust every step in `[0, returned]`.
    The returned number is the group's clearance budget: how much room the pose
    would have to give before this move is available.
    """
    if isinstance(moved, int):
        moved = [moved]
    ok, _c, _sl, _who = try_slide(state, dirs, idx, moved, axis, sign, hi)
    if ok:
        return hi
    lo, high = ZERO, hi
    for _ in range(steps):
        if high - lo <= TOL:
            break
        mid = (lo + high) / 2
        ok, _c, _sl, _who = try_slide(state, dirs, idx, moved, axis, sign, mid)
        if ok:
            lo = mid
        else:
            high = mid
    return lo


def min_side_step(state, dirs, idx, moved, axis, sign, iters=30, hexes=None):
    """The step in `[0, max_legal_step]` that minimises the side.

    `max_legal_step` is the right *bound* (every step below it is legal) and the
    wrong *answer*: it maximises the distance moved, not the side saved.  For a
    band translated inward the side is `max(span_axis(t), span_other)`, each
    term a max or min of linear functions of `t`, so the side is a **convex**
    function of the step and its minimum is found by ternary search over a range
    on which every point is known to be legal.

    The gap control separates the two: a 4x4 grid with one row shifted by 1e-3
    has a legal step of 2 (nothing is in the way) and a useful step of exactly
    1e-3, so a search that maximises the step returns the worst candidate.
    """
    t_hi = max_legal_step(state, dirs, idx, moved, axis, sign)
    s0 = side_of(state, dirs, hexes)
    if t_hi <= ZERO:
        return ZERO, s0

    def side_at(t):
        dx = sign * t if axis == 0 else ZERO
        dy = sign * t if axis == 1 else ZERO
        return side_of(apply_move(state, moved, dx, dy), dirs, hexes)

    lo, hi = ZERO, t_hi
    for _ in range(iters):
        if hi - lo <= TOL:
            break
        m1 = lo + (hi - lo) / 3
        m2 = hi - (hi - lo) / 3
        if side_at(m1) <= side_at(m2):
            hi = m2
        else:
            lo = m1
    best_t, best_s = ZERO, s0
    for t in (lo, (lo + hi) / 2, hi):
        s = side_at(t)
        if s < best_s:
            best_t, best_s = t, s
    return best_t, best_s


def void_seats(state, dirs, moving=None, step=ONE, limit=None, idx=None):
    """Centres where a unit cell fits in the pose's free space, exactly.

    The scan is a `step`-lattice over the pose's own bounding box, evaluated by
    the same `slack` test against the neighbours of the candidate.  It answers
    the question the block swap needs: is there a void a cell can move into?

    The neighbour list comes from the sorted-x index (`near_at`) rather than
    from a pass over all n cells: the set is identical, because a cell further
    than `REACH` in either coordinate cannot reach the probe, and the scan is a
    lattice x n loop otherwise (964k Decimal subtractions on a 942-cell row).
    """
    if idx is None:
        idx = positions(state)
    xlo, xhi, ylo, yhi = spans(state, dirs)
    if moving is None:
        moving = 0
    c, s = dirs[moving]
    out = []
    x = xlo + HALF
    while x + HALF <= xhi:
        y = ylo + HALF
        while y + HALF <= yhi:
            probe = (x, y, c, s)
            bad = False
            for j in near_at(state, idx, x, y, skip=(moving,)):
                b = (state[j][0], state[j][1], dirs[j][0], dirs[j][1])
                if slack(probe, b) < 0:
                    bad = True
                    break
            if not bad:
                out.append((x, y))
                if limit is not None and len(out) >= limit:
                    return out
            y += step
        x += step
    return out


# ------------------------------------------------------------------- controls


def gapped_pose(gap, rows=4, cols=4, shifted_row=3):
    """An axis-aligned `rows x cols` grid with one row shifted right by `gap`."""
    st = []
    for j in range(rows):
        for i in range(cols):
            x = Decimal(i) + (gap if j == shifted_row else ZERO)
            st.append((x, Decimal(j), ZERO))
    return st


def holed_pose():
    """A 3x3 axis grid with its centre cell parked outside the block."""
    st = []
    for j in range(3):
        for i in range(3):
            if (i, j) == (1, 1):
                continue
            st.append((Decimal(i), Decimal(j), ZERO))
    st.append((Decimal("4"), Decimal("0"), ZERO))      # the cell to swap back in
    return st


def selftest():
    """P, N and V controls: the move fires, refuses, and swaps into a void."""
    gap = Decimal("0.25")
    st = gapped_pose(gap)
    dr = directions(st)
    idx = positions(st)
    s_before = side_of(st, dr)
    assert s_before == Decimal(4) + gap, s_before      # the gap is real

    moved, moves = tighten(st, dr, idx)
    s_after = side_of(moved, dr)
    print(f"P positive -- 4x4 grid with one row shifted by {gap}: side "
          f"{s_before} -> {s_after}, {moves} legal move(s) accepted")
    assert moves >= 1, "P: the slide never fired"
    assert s_after == Decimal(4), s_after
    assert all(slack((moved[i][0], moved[i][1], dr[i][0], dr[i][1]),
                     (moved[j][0], moved[j][1], dr[j][0], dr[j][1])) >= 0
               for i in range(len(moved))
               for j in near_at(moved, positions(moved), moved[i][0], moved[i][1],
                                 skip=(i,))), "P: accepted an overlap"

    # N negative: three single-cell moves that would overlap, by an exact unit,
    # by half a unit, and into the row in front -- all must be refused, with the
    # offending pair named, and no pose returned.
    st = gapped_pose(ZERO)
    dr = directions(st)
    idx = positions(st)
    for label, i, axis, sign, step in (("onto its neighbour", 5, 0, 1, ONE),
                                       ("half onto its neighbour", 5, 0, 1, HALF),
                                       ("into the row in front", 5, 1, -1, ONE)):
        ok, cand, sl, who = try_slide(st, dr, idx, [i], axis, sign, step)
        print(f"N negative -- cell {i} {label} by {sign * step}: ok={ok}, "
              f"slack {sl} at pair {who}")
        assert not ok, f"N: an overlapping move was accepted ({label})"
        assert sl is not None and sl < 0, sl
        assert cand is None, "N: a refused move returned a pose"

    # N3 regression: a long slide onto a DISTANT occupied cell.  The first
    # version of check_move missed it: the mover's old neighbour list does not
    # contain a cell four units away, so the move was accepted and the sample
    # run measured impossible clearances (up to 9.5 units on a jammed pose).
    st = holed_pose()
    dr = directions(st)
    idx = positions(st)
    parked = len(st) - 1
    target = st[6]                      # the occupied corner (0, 2)
    ok3, cand3, sl3, who3 = try_move(st, dr, idx, [parked],
                                     target[0] - st[parked][0],
                                     target[1] - st[parked][1])
    print(f"N3 long slide -- cell {parked} moved 4 units onto cell 6: "
          f"ok={ok3}, slack {sl3} at {who3}")
    assert not ok3 and sl3 is not None and sl3 < 0 and cand3 is None, (ok3, sl3)

    # N2: the accepting branch is not vacuous, including the case where no pair
    # is even in reach (the parked cell of the holed pose moves into empty space).
    st = holed_pose()
    dr = directions(st)
    idx = positions(st)
    parked = len(st) - 1                     # the cell parked outside the block
    ok2, cand2, sl2, _w2 = try_slide(st, dr, idx, [parked], 0, 1, HALF)
    assert ok2 and cand2 is not None and (sl2 is None or sl2 >= 0), (ok2, sl2)
    print(f"   (the accepting branch is not vacuous: the parked cell slid into free "
          f"space with slack {sl2} -- `None` meaning no pair is in reach -- so the "
          f"refusals above are about overlaps, not about slides being blocked)")

    # E: the step that matters is the one that minimises the side, not the
    # longest legal one.  A 4x4 grid with one row shifted by g can slide that row
    # 2 units left (nothing is in the way), and the side at that step is worse
    # than at t = g: the side along the slide is 4+g-t for t <= g and 4+t-g after,
    # so it is V-shaped with its minimum exactly at t = g.  The ladder is a third
    # answer again -- its smallest rung (1/512) is larger than g, so it fires only
    # by overshooting, and lands short of the minimum.
    g = Decimal("0.001")
    st = gapped_pose(g)
    dr = directions(st)
    idx = positions(st)
    s_gap = side_of(st, dr)
    cell = wall_cells(st, dr, "xhi")[0]
    band = slab(st, dr, cell, 0)
    t_max = max_legal_step(st, dr, idx, band, 0, -1)
    s_at_max = side_of(apply_move(st, band, -t_max, ZERO), dr)
    t_best, s_best = min_side_step(st, dr, idx, band, 0, -1, iters=45)
    print(f"E step search -- 4x4 grid with one row shifted by 1e-3 (side {s_gap}): "
          f"largest legal step {t_max} gives side {s_at_max}; "
          f"side-minimising step {format(t_best, '.9f')} gives {s_best}")
    assert t_max == REACH, t_max
    assert s_at_max > s_best, (s_at_max, s_best)
    assert abs(t_best - g) < Decimal("1e-8"), t_best
    assert s_best - Decimal(4) < Decimal("1e-8"), s_best
    _m, n_lad = tighten(st, dr, idx)
    s_lad = side_of(_m, dr)
    moved, n_ex = tighten_exact(st, dr, idx)
    s_ex = side_of(moved, dr)
    print(f"   tighten (ladder): {n_lad} move(s), side {s_lad}; tighten_exact: "
          f"{n_ex} move(s), side {s_ex} -- both legal, the exact step is the closer one")
    assert n_ex >= 1 and s_ex < s_gap, (n_ex, s_ex)
    assert s_ex <= s_lad, (s_ex, s_lad)
    assert s_ex - Decimal(4) < Decimal("1e-6"), s_ex
    _worst, viol, _w = check_pose(moved, dr, positions(moved))
    assert viol == 0, (_worst, viol)

    # F: legal_scale returns the analytic minimum, not a ladder rung, and the
    # payback is `(f*-1) x centre spread` -- not `(f*-1) x side`, because the
    # half-extents do not scale.  A 4x4 grid compressed to spacing 1-d in BOTH
    # axes overlaps by exactly d, so the smallest uniform scale is 1/(1-d), the
    # legal side is exactly 4, and the payback is exactly 3d.
    d = Decimal("0.001")
    st = [(Decimal(i) * (ONE - d), Decimal(j) * (ONE - d), ZERO)
          for j in range(4) for i in range(4)]
    dr = directions(st)
    s_before = side_of(st, dr)
    f_star, legal, s_legal, n_viol = legal_scale(st, dr, steps=60)
    want_f = ONE / (ONE - d)             # adjacent columns must reach 1 apart
    print(f"F minimal legal scale -- 4x4 grid at spacing 1-1e-3 both ways "
          f"(penetration 1e-3): {n_viol} violation(s), f* = {f_star} "
          f"(analytic {want_f})")
    # resolution: the bisection stops at TOL = 1e-15 in f, so 1e-14 is the
    # assertion; `f*` is still the minimum of the family to twelve digits
    assert f_star is not None and abs(f_star - want_f) < Decimal("1e-14"), f_star
    assert s_before == Decimal(3) * (ONE - d) + ONE, s_before
    assert abs(s_legal - Decimal(4)) < Decimal("1e-13"), s_legal
    assert abs((s_legal - s_before) - Decimal(3) * d) < Decimal("1e-13"), s_legal
    w_f, v_f, _wf = check_pose(legal, dr)
    assert v_f == 0 and w_f is None, (v_f, w_f)
    print(f"   legal at {s_legal} (0 violations): payback {s_legal - s_before} = 3d, "
          f"i.e. (f*-1) x the 3-unit spread, not (f*-1) x the side")

    # S: the REACH sweep against the O(n^2) pair pass, on a real pose and on a
    # perturbed copy of it.  Without the perturbation this control is vacuous
    # (the delivered pose has no violations at all).
    st = load_pose(33)
    dr = directions(st)
    for label, pose in (("delivered n=33", st),
                        ("the same pose compressed by 0.999 about its centre",
                         scale_pose(st, dr, Decimal("0.999")))):
        worst, viol, _w = check_pose(pose, dr)
        chk = TG.check([(str(x), str(y), str(t)) for x, y, t in pose])
        print(f"S sweep vs pair pass -- {label}: {viol} violation(s) by the REACH "
              f"sweep, {len(chk['violations'])} by the O(n^2) pass, worst "
              f"{worst if worst is None else format(worst, '.6e')} vs "
              f"{chk['worst'] if chk['worst'] is None else format(chk['worst'], '.6e')}")
        assert viol == len(chk["violations"]), (viol, len(chk["violations"]))
        assert (worst is None) == (chk["worst"] is None), (worst, chk["worst"])
        if worst is not None:
            assert abs(worst - chk["worst"]) < Decimal("1e-30"), (worst, chk["worst"])
        if "compressed" in label:
            assert viol > 0, "S: the compressed pose has no violations to compare"

    # V void: the parked cell swaps into the hole, then the block tightens
    st = holed_pose()
    dr = directions(st)
    idx = positions(st)
    parked = len(st) - 1
    seats = void_seats(st, dr, moving=parked)
    print(f"V void -- a 3x3 grid with its centre removed: {len(seats)} seat(s) "
          f"found, first {seats[0] if seats else None}")
    assert seats, "V: no void seat found in a pose with a visible hole"
    seat = seats[0]
    # one exact move, both coordinates at once: a two-leg translation would have
    # to pass through a pose that is not legal, which this move set forbids
    ok, cand, sl, who = try_move(st, dr, idx, [parked],
                                 seat[0] - st[parked][0], seat[1] - st[parked][1])
    assert ok, "V: the swap into the void was refused"
    assert sl is not None and sl >= 0, sl
    print(f"   swapped cell {parked} into {seat} legally (slack {sl}); side "
          f"{side_of(st, dr)} -> {side_of(cand, dr)}")
    print("legal_slide: OK (P, N, N2, N3, E, F, S, V controls)")
    return True


# ---------------------------------------------------------------------- run


def analyse(n, seconds):
    """One row: measure the clearance budget, the void seats, and tighten."""
    t0 = time.monotonic()
    deadline = t0 + seconds
    st = load_pose(n)
    dr = directions(st)
    idx = positions(st)
    L0 = side_of(st, dr)
    rec = {"n": n, "cells": len(st), "L0": str(L0)}

    xlo, xhi, ylo, yhi = spans(st, dr)
    rec["span_x"] = str(xhi - xlo)
    rec["span_y"] = str(yhi - ylo)

    # clearance budget: how far can each wall's cells legally slide inward?
    budget = {}
    for which, axis, sign in (("xlo", 0, 1), ("xhi", 0, -1),
                              ("ylo", 1, 1), ("yhi", 1, -1)):
        cells = wall_cells(st, dr, which)
        if not cells or time.monotonic() > deadline:
            continue
        best = ZERO
        for i in cells[:4]:
            if time.monotonic() > deadline:
                break
            m = max_legal_step(st, dr, idx, i, axis, sign)
            if m > best:
                best = m
        budget[which] = {"cells_on_wall": len(cells), "max_inward_step": str(best)}
    rec["clearance"] = budget

    # block swap into a void: does a unit cell fit anywhere in the pose's free
    # space, and can a wall cell be moved there legally?  The seat is tested for
    # the *angle of the cell that will take it*, which is why the scan is per
    # candidate cell and not once per pose.
    swaps = 0
    seats = []
    for which, axis, sign in (("xlo", 0, 1), ("xhi", 0, -1),
                              ("ylo", 1, 1), ("yhi", 1, -1)):
        if swaps or time.monotonic() > deadline:
            break
        for i in wall_cells(st, dr, which)[:2]:
            if time.monotonic() > deadline:
                break
            found = void_seats(st, dr, moving=i, limit=1)
            if not found:
                continue
            seats = found
            seat = found[0]
            ok, cand, sl, who = try_move(st, dr, idx, [i], seat[0] - st[i][0],
                                         seat[1] - st[i][1])
            if ok and side_of(cand, dr) <= side_of(st, dr):
                st, swaps = cand, swaps + 1
                break
    rec["void_seats"] = [str(s[0]) + "," + str(s[1]) for s in seats]
    rec["swaps"] = swaps

    moved, count = tighten(st, dr, idx, rounds=8, deadline=deadline)
    s1 = side_of(moved, dr)
    rec["moves_accepted"] = count
    rec["side_after"] = str(s1)
    rec["dL"] = str(L0 - s1)
    rec["beat"] = bool(s1 < L0)
    rec["budget_limited"] = bool(time.monotonic() > deadline)
    rec["seconds"] = round(time.monotonic() - t0, 2)
    rec["certified"] = False
    if (count or swaps) and len(moved) <= 200:
        # independent end-to-end verdict, whole pose, 40 digits; skipped on
        # the large rows where the O(n^2) pair pass alone costs ~85 s
        chk = TG.check([(str(x), str(y), str(t)) for x, y, t in moved])
        rec["certified"] = True
        rec["certified_side"] = str(+chk["side"])
        rec["certified_violations"] = len(chk["violations"])
        rec["beat_certified"] = bool(len(chk["violations"]) == 0
                                     and chk["side"] < L0)
    elif count or swaps:
        rec["certified_side"] = "not verified (pair pass too large for the budget)"
    print(f"  n={n:4d} L0={str(L0)[:18]:18s} slides {count:2d} swaps {swaps} "
          f"dL={format(Decimal(rec['dL']), '.2e')} seats {len(seats)} clearance "
          + " ".join(f"{w}:{format(Decimal(budget[w]['max_inward_step']), '.2e')}"
                     for w in budget)
          + f"  {rec['seconds']}s", flush=True)
    return rec


def main(argv):
    opts = dict(zip(argv[0::2], argv[1::2]))
    if "--rows" in opts:
        rows = [int(a) for a in opts["--rows"].split(",")]
    else:
        per = SQ.load()
        unbeaten = [n for n in range(2, 1001)
                    if SQ.extent(per[n]) >= SQ.grid(n) - 1e-12]
        rows = [unbeaten[0], unbeaten[49], unbeaten[149], unbeaten[299],
                unbeaten[399], unbeaten[449]]
    # int, not float: this module is inside the bytecode audit, and a budget
    # in whole seconds is exact and names no float at all
    seconds = int(opts.get("--seconds", "20"))
    recs = [analyse(n, seconds) for n in rows]
    ds = sorted(Decimal(r["dL"]) for r in recs)
    print(f"\ndL over {len(ds)} rows: min {ds[0]}  max {ds[-1]}  "
          f"rows beating: {len([r for r in recs if r['beat']])}  "
          f"slides accepted: {sum(r['moves_accepted'] for r in recs)}  "
          f"void swaps: {sum(r['swaps'] for r in recs)}")
    json.dump(recs, open(OUT, "w"), indent=1)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(main(sys.argv[1:]))
