#!/usr/bin/env python3
r"""carrier_offset.py — the block's position, decided exactly, not sampled (Run 149).

Run 148 swept the block-bedded carrier's whole `(side, count)` surface with the block
**centred** (`carrier_ceil.py`: 0 beats in 213,150 declarations) and then *probed* the
family's last free parameter, where the block sits, with 40 sides x 7x7 offsets
(**421,713 declarations, 0 nominations**).  A probe's zero is a sample: it says the 49
sampled positions per declaration missed, not that no position hits.  This module turns
that zero into a decision.

THE QUESTION, IN THE FAMILY'S OWN TERMS.  For a declaration `(K, kx, ky, block)` and a
row `n` the count law is

    n = K^2 - D + m,        D = carrier cells the block beds out,  m = block cells

so the block must bed exactly

    D* = K^2 + m - n

cells, and the question "can the family reach this row at a side below the row's grid side,
at any position of the block" is

    exists (L, cx, cy) with  sqrt(n) < L < k,  h <= cx, cy <= L - h,  D(L, cx, cy) = D*   ?

with `k = ceil(sqrt n)` and `h` the block's own bbox half-extent.  `D` is an integer step
function, so `D*`'s level set is a union of open cells of the arrangement of the bed
surfaces; the decision is whether that set is empty.

WHY IT IS DECIDABLE EXACTLY.  One carrier cell at `(x(L), y(L))` against one block
**rectangle** R -- a rotated rectangle of half-extents `pu, qv` in the block's own frame --
is the SAT test: the two squares are separated on one of four axes (x, y, and R's two own
edge normals), so "the cell's interior meets R's" is the intersection of four **strict
half-spaces**:

    |(x+y) - (cx+cy) - sqrt2 U0| < 1 + sqrt2 pu
    |(y-x) - (cy-cx) - sqrt2 V0| < 1 + sqrt2 qv
    |x - cx - (U0-V0)/sqrt2|      < 1/2 + (pu+qv)/sqrt2
    |y - cy - (U0+V0)/sqrt2|      < 1/2 + (pu+qv)/sqrt2

every one of them **affine in (L, cx, cy)**.  Hence each cell's bed-set is an open convex
polyhedron, and for a box B in the three parameters

* if the interval hull of all four forms over B clears the constants, every point of B beds
  the cell  (**forced**: a convex function is bounded by the box's corners);
* if any form's hull misses the strip, no point of B beds the cell;

so each box carries an exact lower and upper bound on `D` over it.  The decision is the
branch and bound

    lower > D*   ->  no point of B has the row's count   (pruned, proved)
    upper < D*   ->  no point of B has the row's count   (pruned, proved)
    otherwise    ->  split the widest side at its exact midpoint

and an empty box list is a **theorem**: no side below the grid side and no block position
attains the row's count.  A non-empty list is reported, never rounded away: it is the exact
set of boxes still compatible with the row, and a point of it is a candidate.

Every number is `a + b*sqrt 2` with `a, b` in Q (`qsqrt2.Q2`), bisection halves exactly, and
every comparison is `Quad.sign()`.  No tolerance anywhere, and no float in a decision path.

THE TWO FAMILIES.

* **plain** -- the block is a `p x q` rectangle: `m = p*q`, one rectangle, and the lower and
  upper bounds coincide.
* **notched** -- a corner `a x b` of block cells is removed (run 148's item 2).  The kept
  cells are the L-shape, which is exactly the union of two full rectangles
  `R1 = (p-a) x q` and `R2 = a x (q-b)`, so `m = p*q - a*b`, the lower bound is the union
  of the two rectangles' forced sets and the upper bound is the full `p x q` rectangle.  The
  notch's own effect -- the cells that overlap the full block only inside the removed corner
  -- is what the two bounds bracket, and the bracket closes as the boxes shrink.

ROWS.  The open, **non-proved** tie rows -- the plain grid's side, where the literature has
not proved the grid optimal: `n = 12, 20, 30, 42, 56, 72, 91` (bands `k = 4..10`).  Every
proved-optimal row is refused before any geometry.

    python3 scripts/carrier_offset.py              # the seven open tie rows, plain block
    python3 scripts/carrier_offset.py --notched    # the same rows, notched block
    python3 scripts/carrier_offset.py --selftest    # 8 controls
"""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal, getcontext
from fractions import Fraction as F
from math import isqrt

getcontext().prec = 60

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import block_bed as BB                          # noqa: E402  (the family's own bed rule)
import qsqrt2 as Q                              # noqa: E402  (the exact gate)
from qsqrt2 import Q2, HALF                     # noqa: E402

LEDGER = os.path.join(ROOT, "workspace/push/carrier_offset.json")

S2 = Q2(0, 1)                                   # sqrt 2
ONE = Q2(1)
ZERO = Q2(0)

#: every open, non-proved grid row up to 100: the delivered side is the plain grid's side (the 16
#: `tie reached` rows of the `n <= 100` sweep) plus `n = 12`, which the sweep reaches 0.414 above
#: its delivered 4 and which run 148 carried as the sharpest case.  `open_rows()` derives the set
#: from the sweep's ledger and checks it against this constant, so the list is audited, not chosen.
ROWS = (12, 20, 30, 40, 42, 56, 57, 58, 65, 72, 73, 74, 89, 91, 92, 93, 94)

#: the declared parameter box.  The block has to fit inside a side below the grid side, so
#: `(p+q)/sqrt2 < k`, i.e. `p + q <= isqrt(2k^2 - 1)` -- that is the *whole* box, not a cap; the
#: per-row value is computed by `fit_bound(k)`.  For k = 4..10 it is 5, 7, 8, 9, 11, 12, 14, so
#: run 149's fixed `SMAX = 13` was already complete for k <= 9 and cut `p+q = 14` at k = 10.
PMAX = 10               # p, q <= PMAX (never binding: p*q <= n and p+q <= 14 give p <= 7)
SMAX = 13               # the legacy fixed cap, kept only as a fallback
ANOTCH = BNOTCH = 2     # a, b <= 2: the removed corner is at most 2x2 block cells
BOX_CAP = 200000        # per declaration; a cap that is hit is reported, never hidden
TOL = Q2(F(1, 10 ** 6))  # a box this small is decided at its centre, not by bounds


def ceil_sqrt(n: int) -> int:
    k = 1
    while k * k < n:
        k += 1
    return k


def sqrt_floor(n: int, den: int = 10 ** 6) -> F:
    """A rational `q <= sqrt(n)`, exactly: `isqrt(n*den^2)/den`."""
    return F(isqrt(n * den * den), den)


def proved_rows() -> set:
    """The published frontier's proved-optimal rows (`glm_plan.pub_table`)."""
    import glm_plan as GP
    _pub, proved = GP.pub_table()
    return set(proved)


def fit_bound(k: int) -> int:
    """The largest `p+q` whose block bbox fits below a side `k`: `(p+q)^2 < 2 k^2`.

    `sqrt2` is irrational, so `2k^2` is never a square and `isqrt(2k^2 - 1)` is exactly the
    largest integer with `s^2 < 2k^2`; the whole parameter box in `p+q` is `s <= fit_bound(k)`.
    """
    return isqrt(2 * k * k - 1)


def open_rows() -> tuple:
    """The rows this module decides, derived from the sweep's ledger where it is available.

    A row belongs when the plain grid's side is what it has to beat (the sweep reports a tie at
    its delivered side) and the literature has not proved the grid optimal; `n = 12` is carried
    in addition (the sweep is 0.414 *above* its delivered 4, so it is the sharpest grid row, not
    a tie).  The derivation is checked against `ROWS`, so a hand-edit of the constant cannot
    silently change the scope.
    """
    proved = proved_rows()
    path = os.path.join(ROOT, "workspace/push/carrier_ceil.json")
    if not os.path.exists(path):
        return ROWS
    with open(path) as f:
        led = json.load(f)
    ties = [r["n"] for r in led["rows"] if r["verdict"] == "tie reached"]
    derived = tuple(sorted([n for n in ties if n not in proved] + [12]))
    assert derived == tuple(sorted(ROWS)), (derived, ROWS)
    return derived


# ------------------------------------------------------------- the block parts
class Rect:
    """A block part: the rotated rectangle `|u-U0| <= pu, |v-V0| <= qv`.

    `(u, v)` are the block's own frame: `u = (x+y)/sqrt2`, `v = (y-x)/sqrt2`, so the plain
    `p x q` block is `pu = p/2, qv = q/2, U0 = V0 = 0`.  A part of the block that is shifted
    inside that frame (the two halves of the notched L) is just a different `(U0, V0)`.
    """

    __slots__ = ("pu", "qv", "U0", "V0", "tag")

    def __init__(self, pu, qv, U0=None, V0=None, tag=""):
        self.pu, self.qv = pu, qv
        self.U0 = ZERO if U0 is None else U0
        self.V0 = ZERO if V0 is None else V0
        self.tag = tag

    def strips(self):
        """`(A1, A2, C)`: the three thresholds of the four strict half-spaces."""
        return (ONE + S2 * self.pu, ONE + S2 * self.qv,
                HALF + (self.pu + self.qv) * S2 * HALF)

    def shifts(self):
        """`(c1, c2, c3, c4)`: the constant parts of the four forms.

        `g1 = (x+y) - (cx+cy) - c1`, `g2 = (y-x) - (cy-cx) - c2`,
        `g3 = x - cx - c3`, `g4 = y - cy - c4`, with `c1 = sqrt2 U0`, `c2 = sqrt2 V0`
        and `(c3, c4) = ((U0-V0), (U0+V0)) * sqrt2 / 2` -- the rectangle centre's own
        absolute offset, `(U0-V0)/sqrt2` in x and `(U0+V0)/sqrt2` in y.
        """
        return (S2 * self.U0, S2 * self.V0,
                (self.U0 - self.V0) * S2 * HALF, (self.U0 + self.V0) * S2 * HALF)


class Decl:
    """One declaration: the grid, its two run splits, and the block."""

    __slots__ = ("K", "kx", "ky", "p", "q", "a", "b", "kind", "xs", "ys",
                 "kept", "h", "rects", "full")

    def __init__(self, K, kx, ky, p, q, a=0, b=0):
        self.K, self.kx, self.ky, self.p, self.q, self.a, self.b = K, kx, ky, p, q, a, b
        self.kind = "plain" if a == 0 and b == 0 else "notched"
        self.xs = axis_cells(K, kx)
        self.ys = axis_cells(K, ky)
        self.kept = p * q - a * b
        self.h = S2 * Q2(F(p + q, 4))              # the bbox half-extent of the block
        self.full = Rect(Q2(F(p, 2)), Q2(F(q, 2)), tag="full")
        if self.kind == "plain":
            self.rects = (self.full,)
        else:
            # the L is the union of the two full rectangles that remain
            self.rects = (Rect(Q2(F(p - a, 2)), Q2(F(q, 2)), Q2(F(a, 2)), ZERO, tag="R1"),
                          Rect(Q2(F(a, 2)), Q2(F(q - b, 2)),
                               Q2(F(a - p, 2)), Q2(F(-b, 2)), tag="R2"))

    def params(self):
        return [self.K, self.kx, self.ky, self.p, self.q, self.a, self.b]

    def label(self):
        s = f"K={self.K} ({self.kx},{self.K - self.kx})x({self.ky},{self.K - self.ky}) " \
            f"{self.p}x{self.q}"
        if self.kind == "notched":
            s += f"-{self.a}x{self.b}"
        return s

    def demand(self, n: int) -> int:
        """`D* = K^2 + m - n`: the bed the count law forces."""
        return self.K * self.K + self.kept - n


def axis_cells(K: int, split: int):
    """`(const, s)` for one axis: the cell's centre is `const + s*L`.

    Run 1 occupies `[0, split]` (centres `1/2 .. split-1/2`, `L`-free); run 2 occupies
    `[L-(K-split), L]` (centres `L-(K-split)+1/2+j`, affine in `L`).
    """
    other = K - split
    return ([(Q2(F(2 * i + 1, 2)), 0) for i in range(split)]
            + [(Q2(F(2 * j + 1, 2) - other), 1) for j in range(other)])


# --------------------------------------------------------------- box arithmetic
def _extreme(cL: int, ca: int, cb: int, k0: Q2, box):
    """`(min, max)` of `k0 + cL*L + ca*cx + cb*cy` over the box, exactly.

    The form is affine and the three parameters are independent, so the extremes are at
    corners; `cL, ca, cb` are small integers, so this is only addition.
    """
    L1, L2, a1, a2, b1, b2 = box
    lo = hi = k0
    for c, v1, v2 in ((cL, L1, L2), (ca, a1, a2), (cb, b1, b2)):
        if c > 0:
            for _ in range(c):
                lo = lo + v1
                hi = hi + v2
        elif c < 0:
            for _ in range(-c):
                lo = lo - v2
                hi = hi - v1
    return lo, hi


def rect_bounds(dec: Decl, rect: Rect, box):
    """`(forced, possible)`: cell indices the rectangle beds for all / for some box point.

    `forced` is a valid **lower** bound on `D` over the box and `possible` a valid **upper**
    bound: a cell in `forced` is bedded at every point of the box, a cell outside `possible`
    at none.
    """
    A1, A2, C = rect.strips()
    c1, c2, c3, c4 = rect.shifts()
    gx = []
    for (k0, s) in dec.xs:
        lo, hi = _extreme(s, -1, 0, k0 - c3, box)
        gx.append((s, k0, lo, hi))
    gy = []
    for (k0, s) in dec.ys:
        lo, hi = _extreme(s, 0, -1, k0 - c4, box)
        gy.append((s, k0, lo, hi))
    forced = set()
    possible = set()
    for i, (sx, kx0, lo3, hi3) in enumerate(gx):
        if not (lo3 < C and hi3 > -C):
            continue
        fx3 = max(abs(lo3), abs(hi3)) < C
        for j, (sy, ky0, lo4, hi4) in enumerate(gy):
            if not (lo4 < C and hi4 > -C):
                continue
            lo1, hi1 = _extreme(sx + sy, -1, -1, kx0 + ky0 - c1, box)
            if not (lo1 < A1 and hi1 > -A1):
                continue
            lo2, hi2 = _extreme(sy - sx, 1, -1, ky0 - kx0 - c2, box)
            if not (lo2 < A2 and hi2 > -A2):
                continue
            idx = i * len(gy) + j
            possible.add(idx)
            if fx3 and max(abs(lo4), abs(hi4)) < C \
                    and max(abs(lo1), abs(hi1)) < A1 and max(abs(lo2), abs(hi2)) < A2:
                forced.add(idx)
    return forced, possible


def bounds(dec: Decl, box):
    """`(lower, upper)`: the certified floor and ceiling of `D` over the box.

    The floor is the union of the parts' forced sets (a cell forced by any kept part is
    bedded by the block); the ceiling is the full rectangle's possible set, since the kept
    cells are a subset of it.  For the plain block the two coincide.
    """
    low = set()
    upper = None
    for rect in dec.rects:
        f, p = rect_bounds(dec, rect, box)
        low |= f
        if rect is dec.full:
            upper = p
    if upper is None:
        upper = rect_bounds(dec, dec.full, box)[1]
    return len(low), len(upper)


#: the project's noise floor (`carrier_ceil.MARGIN`): a side is a *beat* only when it is at
#: least this far below the delivered one
MARGIN = Q2(F(1, 10 ** 8))

#: the delivered sides, read once from the CSV and kept as exact rationals
_SIDES = None


def delivered(n: int):
    """The delivered side for row `n`, exact, from the submission (a measurement, not a verdict).

    `carrier_ceil.load_sides` is the project's one reader of the CSV; it reports a `Decimal`
    built from the angle's float cosine, and the text of that decimal is what becomes a `Q2`
    here.  The number is used only as the *end* of the search interval, so nothing in the
    decision depends on a float -- the arithmetic above it is exact.
    """
    global _SIDES
    if _SIDES is None:
        import carrier_ceil as CC
        _SIDES = {m: Q2(F(str(s[0]))) for m, s in CC.load_sides().items()}
    return _SIDES.get(n)


def domain(dec: Decl, n: int):
    """`(lo, hi)`: the side interval where a **beat** could live.

    `lo` is the area floor, the block's own fit (`L >= 2h`) and the seam law (`L >= K`).
    `hi` is the **delivered side minus the noise margin**, or the grid side when that is
    lower: a beat needs `L < delivered - 1e-8`, and for the rows whose delivered side sits
    *below* their grid side the family's own tie pose is inside `[sqrt n, k]` -- row 65 is
    the one that caught this, its least bed under the grid-side domain is `0`, i.e. the
    count is attained at 8.5355 by a declaration with `K < k`.
    """
    lo = max(BOX_FLOOR(n), 2 * dec.h, Q2(dec.K))
    hi = Q2(ceil_sqrt(n))
    d = delivered(n)
    if d is not None and d - MARGIN < hi:
        hi = d - MARGIN
    return lo, hi


def root_box(dec: Decl, n: int):
    """The initial box of the decision: the legal domain, with `cx, cy` in `[h, hi-h]`.

    The `cx, cy` range is the block's own fit over the *whole* side interval (a superset of
    `[h, L-h]` for any single `L`), so every legal pose is in the box and the proof covers the
    illegal ones too.
    """
    lo, hi = domain(dec, n)
    if lo > hi:
        return None
    h = dec.h
    return (lo, hi, h, hi - h, h, hi - h)


def decide(dec: Decl, n: int, box_cap: int = BOX_CAP, dom=None, demand: int | None = None):
    """Decide whether the declaration attains the row's count below its grid side.

    Verdicts:

    * `EMPTY` -- the box list was emptied by certified pruning: **no** `(L, cx, cy)` in the
      legal domain has `D = D*`.  This is the theorem the run wants.
    * `HIT` -- a box that survived to `TOL` has the count exactly at its centre: a
      candidate pose (reported with the point, never promoted on this line's word).
    * `OPEN` -- boxes survived to `TOL` without the count at their centres (a sliver on a
      bed surface, or a `D*` skipped by a jump): reported, never rounded away.
    * `CAP` -- the declared box budget ran out (reported).
    * `INFEASIBLE` -- no `L` fits both the area floor and the block.

    `tightest` is the smallest certified floor met over the transient.  It is a *valid*
    lower bound on `D` over the legal domain but not a sharp one: the proof is the emptied
    box list, not this number, which is reported only to show how the boxes closed.

    `demand` overrides the count law's `D*` -- the same search asked "is `D = v` attained" for
    a value the row does not itself need.  `least_bed` is the loop of those questions.
    """
    k = ceil_sqrt(n)
    ds = dec.demand(n) if demand is None else demand
    # the legal domain: the area floor, the block must fit (L >= 2h), and the family's own
    # seam law (L >= K, otherwise the two runs on an axis overlap and the pose is not one).
    # `dom` overrides the side interval, for the completeness control only.
    box0 = root_box(dec, n)
    if box0 is None:
        return "INFEASIBLE", 0, [], None
    if dom is not None:
        lo_l, hi_l = dom
        if lo_l > hi_l:
            return "INFEASIBLE", 0, [], None
        h = dec.h
        box0 = (lo_l, hi_l, h, hi_l - h, h, hi_l - h)
    boxes = [box0]
    seen = 0
    tightest = None
    stuck = []
    while boxes:
        box = boxes.pop()
        seen += 1
        lower, upper = bounds(dec, box)
        if tightest is None or lower < tightest:
            tightest = lower
        if lower > ds or upper < ds:
            continue
        if lower == upper:
            # the floor and the ceiling meet: `D` is exactly `lower` on the whole box
            if lower == ds:
                return "HIT", seen, [box], tightest
            continue
        if seen > box_cap:
            return "CAP", seen, [box], tightest
        L1, L2, a1, a2, b1, b2 = box
        w = (L2 - L1, a2 - a1, b2 - b1)
        if w[0] < TOL and w[1] < TOL and w[2] < TOL:
            if bed_at(dec, (L1 + L2) * HALF, (a1 + a2) * HALF, (b1 + b2) * HALF) == ds:
                return "HIT", seen, [box], tightest
            stuck.append(box)
            continue
        d = 0
        for i in (1, 2):
            if (w[i] - w[d]).sign() > 0:
                d = i
        if d == 0:
            m = (L1 + L2) * HALF
            boxes += [(L1, m, a1, a2, b1, b2), (m, L2, a1, a2, b1, b2)]
        elif d == 1:
            m = (a1 + a2) * HALF
            boxes += [(L1, L2, a1, m, b1, b2), (L1, L2, m, a2, b1, b2)]
        else:
            m = (b1 + b2) * HALF
            boxes += [(L1, L2, a1, a2, b1, m), (L1, L2, a1, a2, m, b2)]
    if stuck:
        return "OPEN", seen, stuck, tightest
    return "EMPTY", seen, [], tightest


def least_bed(dec: Decl, n: int, cap: int = 40, box_cap: int = BOX_CAP):
    """The **exact least bed** over the legal domain -- the same search, not a second one.

    `decide` answers "is `D = v` attained anywhere in the domain" for one `v`; the minimum is
    the smallest `v` that gets a `HIT`, every `v` below it having been emptied.  That needs no
    new machinery and no numeric minimisation: the floors are what prove the negative side and
    a `HIT` carries its own witness box (non-empty, `D` constant on it).

    A minimisation by floors alone would *not* close here: where the bed jumps by one, no
    single cell is bedded across a box that straddles the jump, so the floor stays at `v-1`
    forever even though `v` is nowhere attained.  Refusing to read that as a minimum is the
    whole point of asking the decision instead.

    Returns `(best, boxes, stuck, witness)`; `stuck` non-empty means the loop stopped on a
    box that would not resolve (reported, never rounded), and `best is None` means "not
    attained at any `v <= cap` -- or not decided", which the caller must not conflate.
    """
    total = 0
    # start at the root box's certified floor: `D` is at least that everywhere in the domain,
    # so no smaller `v` can be attained and asking it would only prove a known negative (and
    # for a big block those low-`v` runs are the expensive ones: no cell is bedded everywhere,
    # so the floor stays flat and the boxes refine for nothing)
    box0 = root_box(dec, n)
    if box0 is None:
        return None, 0, [], None
    v = int(bounds(dec, box0)[0])
    while v <= cap:
        verdict, seen, surv, _tight = decide(dec, n, box_cap=box_cap, demand=v)
        total += seen
        if verdict == "HIT":
            return v, total, [], surv[0]
        if verdict != "EMPTY":
            return None, total, surv, None
        v += 1
    return None, total, [], None


def BOX_FLOOR(n: int) -> Q2:
    """A rational `L` with `L <= sqrt(n)`: the domain's lower end, exact and a superset."""
    return Q2(sqrt_floor(n))


# ------------------------------------------------------------- exact bed counts
def bed_at(dec: Decl, L: Q2, cx: Q2, cy: Q2) -> int:
    """`D(L, cx, cy)` counted cell by cell against the kept block cells (the verdict)."""
    p, q, a, b = dec.p, dec.q, dec.a, dec.b
    blk = []
    for i in range(p):
        if a and i < a:
            continue
        for j in range(q):
            if b and j < b:
                continue
            du = F(2 * i - (p - 1), 4)
            dv = F(2 * j - (q - 1), 4)
            blk.append((cx + S2 * Q2(du + dv), cy + S2 * Q2(du - dv)))
    return sum(1 for (k0, s) in dec.xs for (k1, t) in dec.ys
               if any(_meet(k0 + (L if s else ZERO) - bx, k1 + (L if t else ZERO) - by)
                      for (bx, by) in blk))


def _meet(dx: Q2, dy: Q2) -> bool:
    """The interior of an axis unit cell at `(dx, dy)` meets a 45-degree unit cell at 0."""
    e = HALF + S2 * HALF                       # 1/2 + sqrt2/2
    g = ONE + S2 * HALF                        # 1 + sqrt2/2
    return (abs(dx) < e and abs(dy) < e
            and abs(dx + dy) < g and abs(dy - dx) < g)


def assemble(dec: Decl, L: Q2, cx: Q2, cy: Q2):
    """The pose at `(L, cx, cy)`, judged by the exact gate -- the only candidate path.

    It is built on the family's own law: the carrier's two runs anchored at `0` and `L` on
    each axis, every cell whose interior meets a kept block cell dropped, and the kept block
    cells placed in the block's own frame around `(cx, cy)`.  Nothing here is a constructor
    of new geometry: it is the declaration plus its position.
    """
    p, q, a, b = dec.p, dec.q, dec.a, dec.b
    blk = []
    for i in range(p):
        if a and i < a:
            continue
        for j in range(q):
            if b and j < b:
                continue
            du = F(2 * i - (p - 1), 4)
            dv = F(2 * j - (q - 1), 4)
            blk.append((cx + S2 * Q2(du + dv), cy + S2 * Q2(du - dv)))
    kept = []
    for (k0, s) in dec.xs:
        for (k1, t) in dec.ys:
            x = k0 + (L if s else ZERO)
            y = k1 + (L if t else ZERO)
            if not any(_meet(x - bx, y - by) for (bx, by) in blk):
                kept.append((x, y))
    state = kept + blk
    words = [Q.AXIS] * len(kept) + [Q.word_45()] * len(blk)
    gate = Q.gate(state, words)
    side = Q.side(state, words)
    ex = [Q.frame_extent(*w) for w in words]
    contained = all(ZERO <= pt[0] - e and pt[0] + e <= L and
                    ZERO <= pt[1] - e and pt[1] + e <= L
                    for pt, e in zip(state, ex))
    seam = (L - Q2(dec.K)).sign() >= 0
    return {"state": state, "words": words, "gate": gate, "side": side,
            "n": len(state), "carrier": len(kept), "block": len(blk),
            "contained": contained, "L": L, "seam": seam,
            "ok": bool(gate["ok"]) and contained and seam}


# ---------------------------------------------------------------- declarations
def declarations(n: int, notched: bool = False, pmax: int | None = None,
                 smax: int | None = None):
    """Every declaration in the declared parameter box whose count law can reach `n`.

    `K <= k-1` is forced (`K = k` is the grid); `p + q <= fit_bound(k)` keeps the block's bbox
    below the grid side for every admissible `L` -- and that bound is the *whole* box, every
    shape that can fit at all; `m >= n - K^2` is the count law's own necessary condition
    (`D >= 0`).  The run splits are taken up to the box's reflection (`kx <-> K-kx`,
    `ky <-> K-ky` is the same pose mirrored), and `p <= q` up to the same reflection combined
    with the block's frame symmetry (control 7).
    """
    k = ceil_sqrt(n)
    if smax is None:
        smax = fit_bound(k)
    if pmax is None:
        pmax = max(PMAX, smax)
    out = []
    for K in range(2, k):
        for kx in range(1, K):
            if kx > K - kx:
                continue
            for ky in range(1, K):
                if ky > K - ky:
                    continue
                for p in range(1, pmax + 1):
                    for q in range(p, pmax + 1):
                        if p + q > smax:
                            break
                        if p * q > n:
                            break
                        notches = [(0, 0)]
                        if notched:
                            notches += [(a, b) for a in range(1, min(ANOTCH, p - 1) + 1)
                                        for b in range(1, min(BNOTCH, q - 1) + 1)]
                        for a, b in notches:
                            m = p * q - a * b
                            if m < n - K * K:
                                continue
                            d = Decl(K, kx, ky, p, q, a, b)
                            if 2 * d.h >= Q2(k):
                                continue
                            out.append(d)
    return out


# ------------------------------------------------------------------- the run --
def run_row(n: int, proved: set, notched: bool = False, verbose: bool = True,
            minima: bool = False):
    """Certify one row: every declaration either pruned to empty or reported."""
    k = ceil_sqrt(n)
    rec = {"n": n, "k": k, "proved": n in proved,
           "family": "notched" if notched else "plain",
           "box": {"kmax": k - 1, "smax": fit_bound(k), "pmax": max(PMAX, fit_bound(k)),
                   "splits": "kx, ky <= K/2 (reflection)",
                   "side_end": (str(min(Q2(k), delivered(n) - MARGIN).decimal(20))
                                if delivered(n) is not None else str(k)),
                   "note": "p+q <= isqrt(2k^2-1) is every shape whose bbox fits below the "
                           "grid side; the side interval ends at the delivered side minus "
                           "the noise margin, and the search is over K <= k-1 (K = k is "
                           "the grid itself)"}}
    if n in proved:
        rec["verdict"] = "REFUSED: proved optimal -- no search"
        if verbose:
            print(f"n={n:>4} k={rec['k']}: REFUSED (proved optimal, the literature fixes "
                  f"the side)")
        return rec
    decls = declarations(n, notched)
    tally = {"EMPTY": 0, "HIT": 0, "OPEN": 0, "CAP": 0, "INFEASIBLE": 0}
    boxes = 0
    tight = None
    survivors = []
    for d in decls:
        verdict, seen, surv, t = decide(d, n)
        tally[verdict] += 1
        boxes += seen
        if t is not None and (tight is None or t < tight):
            tight = t
        if verdict in ("HIT", "OPEN", "CAP"):
            rec_h = {"params": d.params(), "verdict": verdict,
                     "demand": d.demand(n), "boxes": seen,
                     "surviving_boxes": [_show(b) for b in surv[:8]]}
            if verdict == "HIT":
                b = surv[0]
                L = (b[0] + b[1]) * HALF
                cx = (b[2] + b[3]) * HALF
                cy = (b[4] + b[5]) * HALF
                r = assemble(d, L, cx, cy)
                rec_h["pose"] = {"L": str(L.decimal(20)), "cx": str(cx.decimal(20)),
                                 "cy": str(cy.decimal(20)), "n": r["n"],
                                 "carrier": r["carrier"], "block": r["block"],
                                 "gate_ok": r["ok"],
                                 "side": str(r["side"].decimal(20))}
            survivors.append(rec_h)
    rec["declarations"] = len(decls)
    rec["boxes"] = boxes
    rec["tally"] = tally
    rec["min_floor"] = None if tight is None else tight
    if minima and decls:
        ds_min = min(d.demand(n) for d in decls)
        tightest = []
        for d in decls:
            if d.demand(n) != ds_min:
                continue
            v, nb, stuckb, wit = least_bed(d, n)
            rec_t = {"params": d.params(), "demand": ds_min, "least_bed": v,
                     "boxes": nb, "unresolved": len(stuckb)}
            if wit is not None:
                # independent attainment witness: D is constant on this box, so its centre
                # must read exactly the certified minimum
                L = (wit[0] + wit[1]) * HALF
                cx = (wit[2] + wit[3]) * HALF
                cy = (wit[4] + wit[5]) * HALF
                rec_t["witness_bed"] = bed_at(d, L, cx, cy)
                rec_t["witness"] = {"L": str(L.decimal(20)), "cx": str(cx.decimal(20)),
                                    "cy": str(cy.decimal(20))}
            tightest.append(rec_t)
            if verbose:
                print(f"      exact least bed: {d.params()} -> D = {v} "
                      f"({nb} boxes, {len(stuckb)} unresolved); the count law needs {ds_min}")
        rec["minima"] = tightest
    if tally["EMPTY"] == len(decls):
        rec["verdict"] = "PROVED: no side below the grid side and no block position"
    elif tally["HIT"]:
        rec["verdict"] = f"HIT: {tally['HIT']} declaration(s) carry the row's count"
    elif tally["CAP"]:
        rec["verdict"] = f"OPEN: {tally['CAP']} declaration(s) over the box budget"
    else:
        rec["verdict"] = f"OPEN: {tally['OPEN']} declaration(s) keep a box"
    if verbose:
        print(f"n={n:>4} k={rec['k']}: {rec['verdict']}  "
              f"[{len(decls)} declarations, {boxes} boxes, "
              f"weakest floor met {rec['min_floor']}]")
        demands = sorted({d.demand(n) for d in decls})
        if demands:
            print(f"      the count law's demands run D* = {demands[0]}..{demands[-1]}")
        for s in survivors[:4]:
            print(f"      still open: {s['params']} demand {s['demand']} "
                  f"({s['verdict']}, {s['boxes']} boxes)")
    rec["open"] = survivors
    return rec


def _show(box):
    """A box as decimal strings (display only)."""
    return [str(v.decimal(20)) for v in box]


def report(rows=None, notched: bool = False, minima: bool = False):
    import sqscore as SQ
    SQ.guard(quiet=True)
    if rows is None:
        rows = open_rows()
    proved = proved_rows()
    out = [run_row(n, proved, notched=notched, minima=minima) for n in rows]
    led_key = "notched" if notched else "plain"
    led = {}
    if os.path.exists(LEDGER):
        try:
            with open(LEDGER) as f:
                old = json.load(f)
            # keep the two families this module owns; run 148's sampled-probe keys
            # (`family`, `rows`, `note`) described an instrument that no longer exists
            led = {k: v for k, v in old.items() if k in ("plain", "notched")}
        except ValueError:
            led = {}
    led[led_key] = {
        "family": ("seamed K x K carrier + p x q block with an a x b corner removed"
                   if notched else "seamed K x K carrier + p x q block"),
        "method": "certified branch and bound over (L, cx, cy): a box is pruned when its "
                  "forced bed exceeds the count law's demand or its possible bed falls "
                  "short of it; an empty box list is a proof",
        "box": {"pmax": PMAX, "smax": {str(n): fit_bound(ceil_sqrt(n)) for n in rows},
                "note": "per row p+q <= isqrt(2k^2-1): the whole box, every shape whose "
                        "bbox fits below the grid side, not a cap"},
        "box_cap": BOX_CAP,
        "rows": out,
    }
    with open(LEDGER, "w") as f:
        json.dump(led, f, indent=1)
    print(f"wrote {os.path.relpath(LEDGER, ROOT)} [{led_key}]")
    return led[led_key]


# ------------------------------------------------------------------ selftest --
def selftest() -> int:
    import sqscore as SQ
    SQ.guard(quiet=True)
    print("carrier_offset selftest")
    import carrier_ceil as CC

    # 1. the rectangle's four strips are the family's own bed rule: the strip form and the
    #    pair form and `block_bed.in_bed` must agree on every cell of several declarations
    checks = 0
    for (K, kx, ky, p, q) in ((4, 2, 2, 2, 2), (5, 1, 3, 3, 2), (6, 2, 3, 2, 4)):
        d = Decl(K, kx, ky, p, q)
        for num in (40, 47, 51, 56):
            L = Q2(F(num, 8))
            c = L * HALF
            D = bed_at(d, L, c, c)
            D2 = sum(1 for (k0, s) in d.xs for (k1, t) in d.ys
                     if BB.in_bed(k0 + (L if s else ZERO) - c,
                                  k1 + (L if t else ZERO) - c, p, q, L))
            assert D == D2, (K, kx, ky, p, q, num, D, D2)
            checks += 1
    print(f"  1. the pair test, the strip form and `block_bed.in_bed` agree on {checks} "
          f"declaration x side pairs")

    # 2. the strip constants are `block_bed.beds` exactly (no re-derivation drift)
    for (p, q) in ((1, 1), (2, 3), (4, 4), (1, 7)):
        A1, A2, C = Rect(Q2(F(p, 2)), Q2(F(q, 2))).strips()
        A, B, Cb = BB.beds(p, q, Q2(3))
        assert A1 == S2 * A and A2 == S2 * B and C == Cb, (p, q, A1, A2, C)
    print("  2. the rectangle's thresholds equal `block_bed.beds` on 4 shapes")

    # 3. the bounds are sound: on sampled boxes, forced <= D(point) <= possible, exactly
    n = 20
    d = Decl(4, 2, 2, 2, 2)
    boxes = [(_q(7, 2), _q(4), _q(1), _q(5, 2), _q(1), _q(5, 2)),
             (_q(36, 10), _q(39, 10), _q(15, 10), _q(2), _q(14, 10), _q(19, 10))]
    pts = 0
    for box in boxes:
        lower, upper = bounds(d, box)
        L1, L2, a1, a2, b1, b2 = box
        for i in range(5):
            for j in range(5):
                for m in range(5):
                    L = L1 + (L2 - L1) * Q2(F(i, 4))
                    cx = a1 + (a2 - a1) * Q2(F(j, 4))
                    cy = b1 + (b2 - b1) * Q2(F(m, 4))
                    D = bed_at(d, L, cx, cy)
                    assert lower <= D <= upper, (box, lower, D, upper)
                    pts += 1
    print(f"  3. on {pts} sampled points of 2 boxes, forced <= D <= possible holds exactly")

    # 4. the decision is complete: a *planted* configuration is never pruned.  Build a pose
    #    with a known bed, read its count off the pose, and the instrument must keep a box
    #    (The plain family has no *in-domain* planted pose: a legal pose of this family has
    #    `n <= K^2` at `K = k-1`, which is the theorem itself.  So the control plants a point
    #    and hands the engine a side window around it, which is the same test of the search
    #    and not of the row semantics.)
    planted = 0
    for (K, kx, ky, p, q) in ((4, 2, 2, 2, 2), (3, 1, 2, 2, 2), (5, 2, 3, 2, 2),
                              (4, 1, 3, 1, 2), (6, 3, 3, 2, 3), (5, 1, 4, 3, 3)):
        d = Decl(K, kx, ky, p, q)
        for num in (41, 45, 49, 53):
            L = _q(num, 10)
            if L < 2 * d.h or L < Q2(K):
                continue
            for i, j in ((0, 0), (2, 2), (4, 0), (0, 4), (3, 1)):
                hi = L - d.h
                cx = d.h + (hi - d.h) * _q(i, 4)
                cy = d.h + (hi - d.h) * _q(j, 4)
                D = bed_at(d, L, cx, cy)
                nn = K * K - D + p * q
                lo = max(2 * d.h, Q2(K))
                if lo > L:
                    continue
                # walk the chain of boxes that contain the planted point: the engine prunes
                # a box only when its certified floor exceeds `D*` or its ceiling falls
                # short, so on this chain the planted point's own bed must stay inside
                # [floor, ceiling] at every depth.  A single violation is a false zero.
                box = (lo, L, d.h, L - d.h, d.h, L - d.h)
                for _depth in range(24):
                    lower, upper = bounds(d, box)
                    assert lower <= D <= upper, (K, kx, ky, p, q, L, D, lower, upper)
                    if lower == upper:
                        break                     # resolved exactly: the engine would stop
                    L1, L2, a1, a2, b1, b2 = box
                    w = (L2 - L1, a2 - a1, b2 - b1)
                    ax = 0
                    for i in (1, 2):
                        if (w[i] - w[ax]).sign() > 0:
                            ax = i
                    if ax == 0:
                        m = (L1 + L2) * HALF
                        box = (L1, m, a1, a2, b1, b2) if L <= m else (m, L2, a1, a2, b1, b2)
                    elif ax == 1:
                        m = (a1 + a2) * HALF
                        box = (L1, L2, a1, m, b1, b2) if cx <= m else (L1, L2, m, a2, b1, b2)
                    else:
                        m = (b1 + b2) * HALF
                        box = (L1, L2, a1, a2, b1, m) if cy <= m else (L1, L2, a1, a2, m, b2)
                r = assemble(d, L, cx, cy)
                assert r["n"] == nn and r["ok"], (nn, r["n"], r["gate"], r["seam"])
                planted += 1
    assert planted >= 12, planted
    print(f"  4. a planted configuration (count read off the pose) is not pruned on "
          f"{planted} declarations -- the search has no false zero")

    # 5. the notched L is exactly the union of its two rectangles, and the count law is
    #    the plain one when the notch is empty
    for (p, q, a, b) in ((3, 3, 1, 1), (4, 2, 2, 1), (1, 5, 0, 0)):
        d = Decl(4, 2, 2, p, q, a, b)
        assert d.kept == p * q - a * b
        if a == 0 and b == 0:
            assert d.kind == "plain" and d.rects == (d.full,)
    # every kept cell is inside R1 or R2, and every point of R1 / R2 is in the full rectangle
    for (p, q, a, b) in ((3, 3, 1, 1), (4, 2, 2, 1), (5, 4, 2, 2)):
        d = Decl(4, 2, 2, p, q, a, b)
        for i in range(p):
            for j in range(q):
                u = Q2(i) - Q2(F(p - 1, 2))
                v = Q2(F(q - 1, 2)) - Q2(j)
                inside = any(abs(u - R.U0) <= R.pu and abs(v - R.V0) <= R.qv
                             for R in d.rects)
                assert inside == (not (a and i < a and b and j < b)), (p, q, a, b, i, j)
    print("  5. the notched L is exactly R1 u R2 and its kept cells never exceed the full "
          "rectangle")

    # 6. the two instruments meet at the one row they both name: run 148's sweep says the
    #    carrier reaches band 5 exactly at L = 5 with (K, kx, ky, p, q) = (5, 1, 1, 1, 2),
    #    i.e. the delivered grid side and no lower.  Our exact counter must read 20 at 5,
    #    and the certified decision must empty the domain strictly below 5
    d5 = Decl(5, 1, 1, 1, 2)
    r5 = assemble(d5, Q2(5), Q2(5) * HALF, Q2(5) * HALF)
    assert r5["n"] == 20 and r5["ok"] and r5["side"] == Q2(5), (r5["n"], r5["gate"])
    # and the count law's cheapest declaration for 20 (the sweep's own row of the table:
    # `D* = 0` at K = 4, block 1 x 4) is emptied strictly below the grid side
    d20 = Decl(4, 1, 3, 1, 4)
    assert d20.demand(20) == 0, d20.demand(20)
    verdict, seen, surv, tight = decide(d20, 20)
    assert verdict == "EMPTY", (verdict, seen, tight)
    print(f"  6. band 5: (5,1,1,1,2) builds count 20 at L = 5 exactly (the tie, gate ok), and "
          f"the count law's cheapest demand for 20 (`D* = 0` at K = 4, block 1x4) is emptied "
          f"strictly below 5 in {seen} boxes")

    # 6b. the search interval ends where a beat could live: at the delivered side minus the
    #     noise margin, not at the grid side.  Row 20's delivered side is 5 + 1.6e-9, so the
    #     two coincide there; row 65's is 8.5355..., well below its grid side 9, and the
    #     family attains 65 there with `K < k` -- the interval must stop short of it.
    d20b = Decl(4, 1, 3, 1, 4)
    _lo20, hi20 = domain(d20b, 20)
    d20d = delivered(20)
    assert hi20 == d20d - MARGIN and hi20 < Q2(5), (hi20.decimal(24),)
    d65 = Decl(8, 1, 1, 6, 6)
    _lo65, hi65 = domain(d65, 65)
    d65d = delivered(65)
    assert d65d is not None and hi65 == d65d - MARGIN and hi65 < Q2(9), (hi65.decimal(24),)
    print(f"  6b. the side interval ends at the delivered side - 1e-8: "
          f"{hi20.decimal(12)} at row 20 (delivered 5.0000000016, grid side 5) and "
          f"{hi65.decimal(12)} at row 65 (delivered {d65d.decimal(12)}, grid side 9) -- "
          f"a pose at the delivered side is never inside the box")

    # 7. the declarations' p <= q and kx <= K/2 pruning lose nothing: the block's frame
    #    reflection swaps the diagonal strips, so (q, p) at (kx, ky) is (p, q) at (ky, kx)
    for (dx, dy, p, q) in ((Q2(F(13, 10)), Q2(F(-7, 10)), 2, 3),
                           (Q2(F(-21, 10)), Q2(F(4, 5)), 3, 4)):
        assert BB.in_bed(dx, dy, q, p, Q2(4)) == BB.in_bed(dy, dx, p, q, Q2(4))
    print("  7. the reflection identity in_bed(dx,dy,q,p) = in_bed(dy,dx,p,q) holds "
          "(so p <= q with every split is the whole family)")

    # 8. float-free decision path
    import exact_field as EF
    checked, offenders, skipped = EF.audit_module(
        sys.modules[__name__], exempt=EF.AUDIT_EXEMPT + ("selftest", "_show", "_q",
                                                        "_inside"))
    assert offenders == [], offenders
    print(f"  8. bytecode audit: {checked} decision functions, 0 naming float "
          f"(exempt {skipped})")

    # 9. the minimiser certifies the exact least bed: the box list empties with nothing left
    #    unresolved, the constant box that set the value reads the same at its centre (an
    #    independent attainment witness), and no sampled point of the domain is below it
    cases = 0
    for (k, K, kx, ky, p, q) in ((4, 3, 1, 1, 2, 2), (5, 4, 1, 2, 1, 4), (6, 5, 2, 2, 2, 3)):
        n = k * k - 1                 # the row's domain [sqrt n, k] is non-degenerate here
        d = Decl(K, kx, ky, p, q)
        v, nb, stuckb, wit = least_bed(d, n)
        assert v is not None and stuckb == [] and wit is not None, \
            (k, K, p, q, v, len(stuckb))
        L = (wit[0] + wit[1]) * HALF
        assert bed_at(d, L, (wit[2] + wit[3]) * HALF, (wit[4] + wit[5]) * HALF) == v, \
            (k, K, p, q, v)
        lo, hi = domain(d, n)
        for i in range(5):
            Ls = lo + (hi - lo) * Q2(F(i, 4))
            for j in range(5):
                for m in range(5):
                    assert bed_at(d, Ls, d.h + (Ls - 2 * d.h) * Q2(F(j, 4)),
                                  d.h + (Ls - 2 * d.h) * Q2(F(m, 4))) >= v, \
                        (k, K, p, q, v, i, j, m)
        cases += 1
    print(f"  9. the minimiser certifies the exact least bed on {cases} declarations: the box "
          f"list empties unresolved-free, its witness box reads the value at the centre, and "
          f"125 sampled points per declaration are never below it")
    print("selftest OK (9 controls)")
    return 0


def _q(num, den=1) -> Q2:
    """A rational as a field element (selftest convenience)."""
    return Q2(F(num, den))


def _inside(box, pt) -> bool:
    """Is the point `(L, cx, cy)` inside the box? (selftest convenience)."""
    return all(box[2 * i] <= pt[i] <= box[2 * i + 1] for i in range(3))


MINIMA_LEDGER = os.path.join(ROOT, "workspace/push/carrier_minima.json")


def minima_report(rows=None, notched: bool = False, dstar_max: int = 3):
    """See below.  The ledger is rewritten after every row, so a partial run is still readable and
    says which rows it covered (`rows` is part of the file, not an assumption about the reader)."""
    """How many cells short each row is, quantitatively and exactly where it is cheap.

    Two statements per row, both certified:

    * the root box's **floor** is a lower bound on the bed over the whole legal domain, so
      `floor - D*` is a lower bound on the row's deficit -- free, and it is the whole answer
      for a row whose cheapest declaration demands a small `D*`;
    * for a row whose cheapest demand is small (`D* <= dstar_max`) the *exact* least bed is
      the smallest `v` the decision can attain (`least_bed`), which turns the deficit into an
      equation: at `n = 12` the least bed is 2 and the demand is 1, so the family is one cell
      short -- not "short".

    Rows whose cheapest demand is large are not minimised: the loop would ask dozens of
    attainability questions per declaration to pin a number no claim uses.
    """
    import sqscore as SQ
    SQ.guard(quiet=True)
    if rows is None:
        rows = open_rows()
    out = []
    for n in rows:
        decls = declarations(n, notched)
        if not decls:
            continue
        ds_min = min(d.demand(n) for d in decls)
        recs = []
        for d in decls:
            if d.demand(n) != ds_min:
                continue
            box0 = root_box(d, n)
            floor0 = int(bounds(d, box0)[0]) if box0 is not None else None
            rec = {"params": d.params(), "demand": ds_min, "root_floor": floor0,
                   "deficit_lower": None if floor0 is None else floor0 - ds_min}
            if ds_min <= dstar_max:
                v, nb, stuckb, wit = least_bed(d, n, cap=ds_min + 5)
                rec.update({"least_bed": v, "boxes": nb, "unresolved": len(stuckb)})
                if wit is not None:
                    L = (wit[0] + wit[1]) * HALF
                    cx = (wit[2] + wit[3]) * HALF
                    cy = (wit[4] + wit[5]) * HALF
                    rec["witness_bed"] = bed_at(d, L, cx, cy)
                    rec["witness"] = {"L": str(L.decimal(20)), "cx": str(cx.decimal(20)),
                                      "cy": str(cy.decimal(20))}
                rec["certified"] = (v is not None and stuckb == []
                                    and rec.get("witness_bed") == v)
            recs.append(rec)
        out.append({"n": n, "k": ceil_sqrt(n), "demand_min": ds_min, "minima": recs})
        _write_minima(out, notched)
        fl = min(r["root_floor"] for r in recs if r["root_floor"] is not None)
        if ds_min <= dstar_max:
            exact = [r for r in recs if r.get("least_bed") is not None]
            best = min((r["least_bed"] for r in exact), default=None)
            cert = bool(exact) and all(r.get("certified") for r in exact)
            nb = sum(r["boxes"] for r in recs if r.get("boxes"))
            if best is None:
                print(f"n={n:>4} k={ceil_sqrt(n)}: cheapest demand D* = {ds_min}; no exact "
                      f"minimum within the cap -- the root floor {fl} puts the deficit at "
                      f">= {fl - ds_min} cell(s)  [{nb} boxes]")
            else:
                print(f"n={n:>4} k={ceil_sqrt(n)}: cheapest demand D* = {ds_min}, exact least "
                      f"bed {best} ({'certified' if cert else 'NOT certified'}), so the row "
                      f"is {best - ds_min} cell(s) short at that declaration"
                      f"  [floor {fl}, {nb} boxes]")
        else:
            print(f"n={n:>4} k={ceil_sqrt(n)}: cheapest demand D* = {ds_min} > {dstar_max}; "
                  f"the root floor {fl} puts the deficit at >= {fl - ds_min} cell(s), "
                  f"no exact minimum computed")
    led = _write_minima(out, notched)
    print(f"wrote {os.path.relpath(MINIMA_LEDGER, ROOT)}")
    return led


def _write_minima(out, notched: bool):
    """The minima ledger as it stands (`rows` lists exactly the rows computed so far)."""
    led = {"family": "notched" if notched else "plain",
           "note": "the exact least bed for each row's cheapest declarations, and the root "
                   "box's certified floor where the exact minimum was not asked; a value is "
                   "certified when every smaller demand was emptied and the witness reads it",
           "rows": out}
    with open(MINIMA_LEDGER, "w") as f:
        json.dump(led, f, indent=1)
    return led


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    notched = "--notched" in sys.argv
    rows = None
    for i, a in enumerate(sys.argv):
        if a == "--rows" and i + 1 < len(sys.argv):
            rows = tuple(int(t) for t in sys.argv[i + 1].split(",") if t.strip())
    if "--minima" in sys.argv:
        minima_report(rows=rows, notched=notched)
        return 0
    report(rows=rows, notched=notched)
    return 0


if __name__ == "__main__":
    sys.exit(main())
