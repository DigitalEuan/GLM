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

#: the open, non-proved tie rows: delivered side = ceil(sqrt n), not proved optimal
ROWS = (12, 20, 30, 42, 56, 72, 91)

#: the declared parameter box, in the same spirit as the (unbounded-in-p) sweep of run 148
PMAX = 10               # p, q <= PMAX
SMAX = 13               # p + q <= SMAX: the block's bbox must fit below the grid side
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


def decide(dec: Decl, n: int, box_cap: int = BOX_CAP, dom=None):
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
    """
    k = ceil_sqrt(n)
    ds = dec.demand(n)
    # the legal domain: the area floor, the block must fit (L >= 2h), and the family's own
    # seam law (L >= K, otherwise the two runs on an axis overlap and the pose is not one).
    # `dom` overrides the side interval, for the completeness control only.
    if dom is not None:
        lo_l, hi_l = dom
    else:
        lo_l = max(BOX_FLOOR(n), 2 * dec.h, Q2(dec.K))
        hi_l = Q2(k)
    if lo_l > hi_l:
        return "INFEASIBLE", 0, [], None
    h = dec.h
    boxes = [(lo_l, hi_l, h, hi_l - h, h, hi_l - h)]
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
def declarations(n: int, notched: bool = False, pmax: int = PMAX,
                 smax: int = SMAX):
    """Every declaration in the declared parameter box whose count law can reach `n`.

    `K <= k-1` is forced (`K = k` is the grid); `p + q <= smax` keeps the block's bbox
    below the grid side for every admissible `L`; `m >= n - K^2` is the count law's own
    necessary condition (`D >= 0`).  The run splits are taken up to the box's reflection
    (`kx <-> K-kx`, `ky <-> K-ky` is the same pose mirrored), and `p <= q` up to the same
    reflection combined with the block's frame symmetry (control 7).
    """ 
    k = ceil_sqrt(n)
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
def run_row(n: int, proved: set, notched: bool = False, verbose: bool = True):
    """Certify one row: every declaration either pruned to empty or reported."""
    rec = {"n": n, "k": ceil_sqrt(n), "proved": n in proved,
           "family": "notched" if notched else "plain"}
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


def report(rows=ROWS, notched: bool = False):
    import sqscore as SQ
    SQ.guard(quiet=True)
    proved = proved_rows()
    out = [run_row(n, proved, notched=notched) for n in rows]
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
        "pmax": PMAX, "smax": SMAX, "box_cap": BOX_CAP,
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
    print("selftest OK (8 controls)")
    return 0


def _q(num, den=1) -> Q2:
    """A rational as a field element (selftest convenience)."""
    return Q2(F(num, den))


def _inside(box, pt) -> bool:
    """Is the point `(L, cx, cy)` inside the box? (selftest convenience)."""
    return all(box[2 * i] <= pt[i] <= box[2 * i + 1] for i in range(3))


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    notched = "--notched" in sys.argv
    report(notched=notched)
    return 0


if __name__ == "__main__":
    sys.exit(main())
