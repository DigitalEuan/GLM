#!/usr/bin/env python3
r"""qsqrt2 — exact arithmetic in Q(sqrt 2), and the exact gate for mixed sentences.

RUN 83.  The expressiveness ladder (`28`) measures an interface: the Lambda_24
predicate is an *integrality* test, the tilted rows' geometry lives in Q(sqrt 2),
and no scale makes an irrational pose integral (if s*(1+sqrt 2) were rational for
rational s != 0 then sqrt 2 would be rational).  This module keeps the predicate
and lifts the alphabet instead of projecting it: every coordinate, half-extent and
separating projection is an exact pair (a, b) meaning a + b*sqrt(2) with a, b in Q.
The 0-degree word and the 45-degree word are then equally first-class, and the gate
between them is decided by signs, never by tolerances.

WHAT IS EXACT HERE
------------------
  sign(a + b sqrt 2)   by comparing a^2 with 2 b^2 in the mixed-sign cases, so a
                       contact is exactly zero and a 1e-300 overlap is an overlap
  + - * /              field operations on Fraction pairs (no float anywhere)
  gate(state, words)   the SAT predicate: the pair is separated iff some axis q of
                       either square has |d.q| >= 1/2 + ext_other(q); the same
                       predicate packlib.verify implements in floats
  side(state, words)   the container side, in Q(sqrt 2)

The gate is a *judge*, not a search: it says yes or no about a sentence.  Where a
sentence comes from (a construction, a lattice, a modulator) is not its business.
"""
from __future__ import annotations

import math
import sys
from decimal import Decimal, getcontext
from fractions import Fraction as F

from exact_field import REFUSED, Quad, audit_module, no_float_calls

getcontext().prec = 70

ONE = None       # assigned at the end of the class body
HALF = None


class Q2(Quad):
    """a + b*sqrt(2) with a, b in Q — the ℚ(√2) instance of the scalar tower.

    The ring logic (sign, ordering, floor, arithmetic, the float refusal) lives
    in `exact_field.Quad`; this subclass fixes `d = 2` and keeps the display the
    project's documents use, so `str` still reads `2 + 1/2√2`.
    """

    d = 2
    __slots__ = ()

    def decimal(self, places=12) -> str:
        """A 12-dp shadow of the exact value (display only, via Decimal)."""
        return Quad.decimal(self, places)


def _q2(x) -> Q2:
    """Coerce to Q2.  A float is refused: nothing in this module is approximate."""
    if isinstance(x, Q2):
        return x
    if isinstance(x, REFUSED):
        raise TypeError("no floats: pass int, Fraction or Q2")
    return Q2(x)


ONE = Q2(1)
HALF = Q2(F(1, 2))


def sqrt2() -> Q2:
    return Q2(0, 1)


# ------------------------------------------------------------------- words
AXIS = (Q2(1), Q2(0))


def word_45():
    """cos = sin = sqrt 2 / 2, i.e. t = tan(theta/2) = sqrt 2 - 1."""
    return (Q2(0, F(1, 2)), Q2(0, F(1, 2)))


def word_t(t):
    """The rational t-basis word t = tan(theta/2) in Q, so cos, sin are rational."""
    t = t if isinstance(t, F) else F(t)
    d = 1 + t * t
    return (Q2((1 - t * t) / d), Q2(2 * t / d))


def is_rational_word(word) -> bool:
    return word[0].b == 0 and word[1].b == 0


# -------------------------------------------------------------------- gate
def field_of(state, cls=None):
    """The field class of a sentence: declared, or read off its first coordinate.

    The gate is one procedure over any `exact_field.Quad(d)`; `Q2` is only its default.
    Reading the class off the state means `gate(state, words)` keeps working unchanged for
    every existing caller, while a Q(sqrt 5) or Q(sqrt 7) sentence passes `cls` explicitly.
    """
    if cls is not None:
        return cls
    for p in state:
        if p is not None:
            return type(p[0])
    return Q2


def frame_extent(c, s, cls=None):
    """Half-extent of the unit square with frame (c, s) along the x axis."""
    cls = cls or field_of([(c,)])
    return (abs(c) + abs(s)) * cls(F(1, 2))


def axis_extent(c, s, qx, qy, cls=None):
    """Half-extent of the unit square with frame (c, s) along the unit axis q."""
    # edges u = (c, s), v = (-s, c); extent = (|u.q| + |v.q|) / 2
    cls = cls or field_of([(c,)])
    return (abs(c * qx + s * qy) + abs(c * qy - s * qx)) * cls(F(1, 2))


def side(state, words, cls=None):
    """The container side: max over the two axes of the state's extent."""
    cls = field_of(state, cls)
    n = len(state)
    ex = [frame_extent(w[0], w[1], cls) for w in words]
    xs = [state[i][0] + ex[i] for i in range(n)]
    xn = [state[i][0] - ex[i] for i in range(n)]
    ys = [state[i][1] + ex[i] for i in range(n)]
    yn = [state[i][1] - ex[i] for i in range(n)]
    return max(max(xs) - min(xn), max(ys) - min(yn))


def pair_axes(state, words, i, j, cls=None):
    """The four SAT (axis, slack, need, owner) quadruples of a pair, exactly.

    `slack = |d.q| - (1/2 + ext_other(q))`; the pair is separated iff some slack
    is >= 0, and the pair's distance from contact is the LARGEST of the four.
    """
    cls = field_of(state, cls)
    half = cls(F(1, 2))
    dx = state[j][0] - state[i][0]
    dy = state[j][1] - state[i][1]
    out = []
    for owner, other in ((i, j), (j, i)):
        c, s = words[owner]
        oc, os_ = words[other]
        for qx, qy in ((c, s), (-s, c)):
            proj = abs(dx * qx + dy * qy)
            need = half + axis_extent(oc, os_, qx, qy, cls)
            out.append(((qx, qy), proj - need, need, owner))
    return out


def gate(state, words, cls=None, stop=False):
    """The exact SAT sentence gate.

    Args:
        state: list of (x, y) pairs of `cls` — square centres.
        words: list of (cos, sin) pairs of `cls` — one word per square.
        cls:   the field class (`Q2`, or any `exact_field.Quad(d)`); default read off
               the state, so every existing caller is unchanged.

    Returns:
        dict with
          ok          True iff every pair is separated on some axis (exact)
          L           the container side, exactly
          clearance   the worst pair's best axis slack, exactly: >= 0 iff ok,
                      and 0 means at least one pair is in exact contact
          contacts    the number of pairs whose tightest axis is exactly touching
          violations  the number of overlapping pairs

    Pairs whose centres differ by 2 or more on either axis are skipped: every
    half-extent is at most sqrt(2)/2, so such a pair is separated on that axis by
    a     margin of at least 2 - sqrt(2) > 0.5 and cannot be the worst pair.  The
    prune is exact (it is decided by a field comparison), not a tolerance.

    `stop=True` returns at the first overlapping pair: `ok` is the same
    predicate, decided by the same loop, but `violations` is then 1 and
    `contacts` / `clearance` describe only the pairs already scanned.  The
    default `False` scans every pair.
    """
    cls = field_of(state, cls)
    n = len(state)
    if n != len(words):
        raise ValueError("state and words disagree on the number of squares")
    if n == 0:
        return {"ok": True, "L": cls(0), "clearance": None, "contacts": 0,
                "violations": 0}
    L = side(state, words, cls)
    two = cls(2)
    worst = None
    contacts = violations = 0
    for i in range(n):
        xi, yi = state[i]
        for j in range(i + 1, n):
            if abs(state[j][0] - xi) >= two or abs(state[j][1] - yi) >= two:
                continue
            best = None
            for _q, slack, _need, _owner in pair_axes(state, words, i, j, cls):
                if best is None or slack > best:
                    best = slack
            if best == 0:
                contacts += 1
            if best < cls(0):          # a comparison, so a plain `Fraction` also gates
                violations += 1
                if stop:               # the same verdict, not scanned further
                    return {"ok": False, "L": L, "clearance": best,
                            "contacts": contacts, "violations": violations}
            if worst is None or best < worst:
                worst = best
    return {"ok": violations == 0, "L": L, "clearance": worst,
            "contacts": contacts, "violations": violations}


# ----------------------------------------------------- exact rounding (no float)
def floor_q2(z: Q2) -> int:
    """floor(a + b*sqrt 2), exactly.  Bracket from a and |b|, then bisect on
    exact sign tests; sqrt 2 < 2 gives a - 2|b| - 1 <= z <= a + 2|b| + 1."""
    return z.floor()


def grid_round(z: Q2, M: int) -> F:
    """The nearest multiple of 1/M to z, decided by exact comparison."""
    return F(floor_q2(z * Q2(M) + HALF), M)


# ------------------------------------------------- the symbolic perception lift
def recover_side(Ldec: Q2, tol=None, bdens=(1, 2, 4, 8, 16),
                 adens=(16, 8, 4, 2, 1), bmax=16):
    """Recover the exact side of a decimal sentence by height-bounded search.

    Every candidate is `a + b*sqrt2` with a and b on small dyadic grids; the
    nearest such element to the decimal side is found by exact comparison.  The
    search is a PSLQ-shaped recovery: the decimal plays the role of the value and
    the height bound is what makes the answer unique (the grids are 1/8 apart, so
    at most one candidate lies within 1e-9 of the decimal).

    Returns (L, residual, b) or (None, residual, None) when nothing is close.
    """
    tol = Q2(F(1, 10 ** 7)) if tol is None else tol
    # three stages, cheapest first: the common sides are 2k + sqrt2/2 on a half
    # grid; then rational b with a small denominator (a real row in the table has
    # side 3 + 4/3 sqrt2, so the dyadic grid alone cannot see it); then the wide
    # dyadic search of the first run-83 experiment.
    #
    # The third stage is the one run 85 had to add: when `b` has denominator d,
    # `a` must be allowed denominator d as well.  Two delivered rows have sides
    # `16/3 + 5/3 sqrt2` and `22/3 + 22/3 sqrt2`, and a grid of 1/8 or 1/64 can
    # never see them — the refusal they produced was a gap in the search, not a
    # theorem about the table (corrected in run 85, doc 48 §4).
    tries = (((1, 2), 8, (4, 2)),
             ("match", 8, None),
             (bdens, bmax, adens))
    best = (None, None, None)
    for bds, bm, ads in tries:
        for bd in ((1, 2, 3, 4, 5, 6, 7, 8) if bds == "match" else bds):
            for num in range(-bm * bd, bm * bd + 1):
                b = F(num, bd)
                rest = Ldec - Q2(0, b)
                for ad in (ads if ads is not None else (4 * bd,)):
                    a = F(floor_q2(rest * Q2(ad) + HALF), ad)
                    cand = Q2(a) + Q2(0, b)
                    err = abs(Ldec - cand)
                    if best[0] is None or err < best[1]:
                        best = (cand, err, b)
        if best[0] is not None and best[1] <= tol:
            return best
    return (None, best[1], None)


def recover_point(x: Q2, tol=None, dens=None, bmax=8):
    """Recover a small-height `a + b*sqrt2` nearest to x, or None.

    The same PSLQ-shaped search as `recover_side`, for one coordinate: b runs over
    multiples of 1/D for a small common denominator D, a is the nearest multiple
    of 1/(4D) to the remainder, and every comparison is exact.  Uniqueness comes
    from the height bound: candidates on a 1/(4D) grid are far apart compared to
    the 1e-7 acceptance tolerance, so at most one can be accepted.
    """
    tol = Q2(F(1, 10 ** 7)) if tol is None else tol
    dens = dens or (1, 2, 3, 4, 6, 8, 12, 16)
    for D in dens:
        best = (None, None)
        for num in range(-bmax * D, bmax * D + 1):
            b = F(num, D)
            rest = x - Q2(0, b)
            a = F(floor_q2(rest * Q2(4 * D) + HALF), 4 * D)
            cand = Q2(a) + Q2(0, b)
            err = abs(x - cand)
            if best[0] is None or err < best[1]:
                best = (cand, err)
        if best[0] is not None and best[1] <= tol:
            return best[0]
    return None


def lattice_den(*sides):
    """Common denominator for the coordinates of a row with these side(s).

    A sentence built from steps of the side and unit moves has coordinates in
    `(1/D) Z + (1/D) Z sqrt2`; the `2` covers the 45-degree word's
    `(1 + sqrt2)/2` steps.
    """
    D = 2
    for s in sides:
        for v in (s.a, s.b):
            D = D * v.denominator // math.gcd(D, v.denominator)
    return D


def height_bound(*sides):
    """How large `|b|` can be in a row of this size, exactly.

    A long diagonal strip moves a square by many `(1 + sqrt2)/2` steps, so `|b|`
    reaches about `L` (a big row has coordinates like `31/2 + 21/2 sqrt2`).
    """
    hb = 8
    for s in sides:
        hb = max(hb, int(abs(s.a) + 2 * abs(s.b)) + 4)
    return hb


def recover_leftovers(pos, shift, tol, dens, bmax, budget=None):
    """Place every still-unplaced square by height recovery in place.

    Tries the row's own lattice first and the generic small denominators second,
    and returns `(miss, exhausted)` — how many squares are still unrecovered (0 on
    success) and whether a declared work `budget` stopped the search.

    `budget` counts `recover_point` calls (two per square per density round), so it
    is a *deterministic* bound on the search: the same sentence always stops in the
    same place, and no clock or tolerance is involved.  `None` is the unbounded
    search every earlier caller had.
    """
    calls = 0
    for round_dens in ((dens, 2 * dens, 4 * dens), (1, 2, 3, 4, 6, 8, 12, 16)):
        miss = 0
        for j in range(len(pos)):
            if pos[j] is not None:
                continue
            if budget is not None and calls + 2 > budget:
                return sum(1 for p in pos if p is None), True
            calls += 2
            x = recover_point(shift[j][0], tol=tol, dens=round_dens, bmax=bmax)
            y = recover_point(shift[j][1], tol=tol, dens=round_dens, bmax=bmax)
            if x is None or y is None:
                miss += 1
            else:
                pos[j] = (x, y)
        if miss == 0:
            return 0, False
    return miss, False


def lift_sentence(state, words, tol=None, budget=None):
    """Exact algebraic reconstruction of a decimal sentence.

    Three exact steps, and the decimals are used only to choose the topology:

      1. **side.**  The container side is recovered by height-bounded search
         (`recover_side`), so the box is [0, L] with L in the field.
      2. **anchors.**  Every square that rests on a face of that box is placed
         exactly: `x = ex` on the left, `x = L - ex` on the right, and likewise
         in y.  This is what pins the boundary layer; a gauge alone does not.
      3. **peeling.**  every other square from two independent equations to
         already placed squares (contact on a SAT axis, sign as the decimals have
         it) by 2x2 Cramer over Q2.

    Then the gate judges the whole sentence, including the contacts that were not
    used to build it.  Nothing is rounded to a grid and no tolerance is used for
    any final decision.

    Returns {"status": "lifted" | "overlap" | "underdetermined" |
             "side-not-recovered" | "empty", "state", "L", "clearance",
             "contacts", "violations", "used", "placed", "side_residual"}.

    `budget` bounds the *leftover recovery* in work units (see
    `recover_leftovers`); it never changes a placed square, only how far the
    search for the unpinned ones runs.  A refusal that a budget cut short says so
    in `budget_exhausted`.
    """
    n = len(state)
    if tol is None:
        tol = Q2(F(1, 10 ** 7))
    if n == 0:
        return {"status": "empty", "state": [], "L": Q2(0), "clearance": None,
                "contacts": 0, "violations": 0, "used": 0, "placed": 0,
                "side_residual": Q2(0)}

    ex = [frame_extent(*w) for w in words]
    lo = [min(state[i][ax] - ex[i] for i in range(n)) for ax in (0, 1)]
    hi = [max(state[i][ax] + ex[i] for i in range(n)) for ax in (0, 1)]
    # the box is the bbox of the state, and it need not start at the origin: work
    # in the translated frame [0, W] x [0, H] and recover W and H separately
    W, residW, _b = recover_side(hi[0] - lo[0], tol=tol)
    H, residH, _b2 = recover_side(hi[1] - lo[1], tol=tol)
    if W is None or H is None:
        return {"status": "side-not-recovered", "state": None, "L": None,
                "clearance": None, "contacts": 0, "violations": 0, "used": 0,
                "placed": 0, "side_residual": residW if W is None else residH,
                "side_decimal": side(state, words)}
    shift = [(state[i][0] - lo[0], state[i][1] - lo[1]) for i in range(n)]

    pos = [None] * n
    wall_eq = [[] for _ in range(n)]
    for i in range(n):
        fixed = {}
        for ax in (0, 1):
            e = (Q2(1), Q2(0)) if ax == 0 else (Q2(0), Q2(1))
            span = W if ax == 0 else H
            if abs(shift[i][ax] - ex[i]) <= tol:
                wall_eq[i].append((e, ex[i]))
                fixed[ax] = ex[i]
            if abs(shift[i][ax] - (span - ex[i])) <= tol:
                wall_eq[i].append((e, span - ex[i]))
                fixed.setdefault(ax, span - ex[i])
        if len(fixed) == 2:
            pos[i] = (fixed[0], fixed[1])

    # pair contacts: (q, sign, need) for every touching pair, from the decimals
    links = [[] for _ in range(n)]
    for i in range(n):
        xi, yi = shift[i]
        for j in range(i + 1, n):
            if abs(shift[j][0] - xi) >= Q2(2) or abs(shift[j][1] - yi) >= Q2(2):
                continue
            axes = pair_axes(shift, words, i, j)
            q, slack, need, _owner = max(axes, key=lambda t: t[1])
            if abs(slack) <= tol:
                dx = shift[j][0] - xi
                dy = shift[j][1] - yi
                sg = Q2(1) if (dx * q[0] + dy * q[1]).sign() >= 0 else Q2(-1)
                # directed: the equation for the TARGET square from the equation
                # (c_j - c_i).q = sg * need is c_target.q = c_ref.q - sg * need
                links[i].append((j, q, -sg, need))
                links[j].append((i, q, sg, need))

    used = 2 * sum(1 for p in pos if p is not None)
    progress = True
    while progress:
        progress = False
        for j in range(n):
            if pos[j] is not None:
                continue
            eqs = list(wall_eq[j])
            for (i, q, sg, need) in links[j]:
                if pos[i] is not None:
                    eqs.append((q, pos[i][0] * q[0] + pos[i][1] * q[1] + sg * need))
            done = False
            for a in range(len(eqs)):
                q1, r1 = eqs[a]
                for b in range(a + 1, len(eqs)):
                    q2, r2 = eqs[b]
                    det = q1[0] * q2[1] - q1[1] * q2[0]
                    if det.sign() == 0:
                        continue
                    x = (r1 * q2[1] - r2 * q1[1]) / det
                    y = (q1[0] * r2 - q2[0] * r1) / det
                    pos[j] = (x, y)
                    used += 2
                    done = progress = True
                    break
                if done:
                    break
    placed = sum(1 for p in pos if p is not None)
    recovered = 0
    if placed < n:
        # the leftover squares are the ones the contact graph does not pin; recover
        # each coordinate by its own height-bounded search, and let the gate judge
        miss, exhausted = recover_leftovers(pos, shift, tol, lattice_den(W, H),
                                            height_bound(W, H), budget)
        recovered = sum(1 for p in pos if p is not None) - placed
        if miss:
            return {"status": "not-on-lattice", "state": None,
                    "L": W if W > H else H, "clearance": None, "contacts": 0,
                    "violations": 0, "used": used, "placed": placed,
                    "recovered": recovered, "unrecovered": miss,
                    "budget_exhausted": exhausted,
                    "pos": pos, "lo": lo,
                    "side_residual": residW if residW > residH else residH}
    g = gate(pos, words)
    return {"status": "lifted" if g["ok"] else "overlap", "state": pos,
            "L": g["L"], "clearance": g["clearance"],
            "contacts": g["contacts"], "violations": g["violations"],
            "used": used, "placed": placed, "recovered": recovered,
            "pos": pos, "lo": lo,
            "side_residual": residW if residW > residH else residH}


# -------------------------------------------------- cage segment (run 87)
class Refusal(Exception):
    """A cage that cannot be swept, with the law that says why."""

    def __init__(self, law, detail):
        super().__init__(f"{law}: {detail}")
        self.law, self.detail = law, detail



def _dec(z):
    """A field element as a 70-digit Decimal (sqrt by Decimal, never a float)."""
    return (Decimal(z.a.numerator) / Decimal(z.a.denominator)
            + Decimal(z.b.numerator) / Decimal(z.b.denominator)
            * Decimal(z.d).sqrt())


def _affine_project(trial, i, j, q):
    """(a, b, c) with (c_j - c_i).q = a*x_j + b*y_j + c, exactly.

    The projection is affine in square j's position, so three evaluations pin it --
    no algebra on the frame, and no assumption about which word j carries.
    """
    def proj(p):
        return (p[0] - trial[i][0]) * q[0] + (p[1] - trial[i][1]) * q[1]
    v0 = proj((Q2(0), Q2(0)))
    v1 = proj((Q2(1), Q2(0)))
    v2 = proj((Q2(0), Q2(1)))
    return (v1 - v0, v2 - v0, v0)


def cage_segment(state, words, pos, L, j, dens=(8, 16, 32), bmax=8, tol=None,
                 legacy=False):
    """The exact feasible segment for a square the contact graph leaves free.

    This is run 86's probe promoted to an instrument: no monkeypatching, no hand-typed
    bounds, and no tolerance in any decision.  `state` holds the *stored* decimals in
    the lift's frame, `pos` the exactly placed squares with None at `j`.

    The contact equations of `j` are collected from the stored pose (the stored decimals
    choose which SAT axis is in contact and on which side; the coefficients are exact)
    and reduced to their rank:

      * rank 2 -- the topology pins the square; returned as `point`;
      * rank 1 -- one linear law, so a free parameter sweeps a segment.  The segment is
        found by bisection on the 70-digit Decimal slack against every placed square,
        then every Q(sqrt2) value on it at the declared denominators and heights is
        tested with the exact per-pair predicate.  Only placements that clear every
        pair with `j` and the container are returned, sorted by distance to the stored
        pose so the first is canonical;
      * rank 0 -- refused (`cage_unconstrained`): there is no law to sweep.
    """
    tol = Q2(F(1, 10 ** 7)) if tol is None else tol
    trial = list(pos)
    trial[j] = state[j]
    ex = frame_extent(*words[j])
    rows = []
    for i in range(len(pos)):
        if i == j or pos[i] is None:
            continue
        axes = pair_axes(trial, words, i, j)
        best = min(axes, key=lambda t: abs(t[1]) if t[1].sign() >= 0 else -t[1])
        if abs(best[1]) > tol:
            continue
        q, _slack, need, _owner = best
        a, b, c = _affine_project(trial, i, j, q)
        v = a * trial[j][0] + b * trial[j][1] + c
        rhs = (need - c) if v.sign() >= 0 else (Q2(0) - need - c)
        rows.append((a, b, rhs, i))

    def parallel(r, s):
        det = r[0] * s[1] - s[0] * r[1]
        return det.sign() == 0

    dirs = []
    for row in rows:
        if not any(parallel(row, d) for d in dirs):
            dirs.append(row)
    if not dirs:
        raise Refusal("cage_unconstrained",
                      f"square {j} touches nothing in the stored pose")
    out = {"j": j, "rank": len(dirs), "equations": len(rows),
           "partners": [row[3] for row in rows], "dens": list(dens), "bmax": bmax}
    if len(dirs) >= 2:
        (a1, b1, c1, _), (a2, b2, c2, _) = dirs[0], dirs[1]
        det = a1 * b2 - a2 * b1
        if det.sign() == 0:
            raise Refusal("cage_degenerate", f"square {j}: singular 2x2")
        out["point"] = ((c1 * b2 - c2 * b1) / det, (a1 * c2 - b1 * c1) / det)
        out["law"] = None
        out["placements"] = [out["point"]]
        return out

    a, b, c, _partner = dirs[0]
    # normalise so that the free coordinate's partner coefficient is 1: y = c - a*x
    if b.sign() == 0:
        law_a, law_b, law_c = Q2(1), Q2(0), c / a          # x is pinned, y sweeps
    else:
        law_a, law_b, law_c = a / b, Q2(1), c / b          # y = law_c - law_a * x
    out["law"] = {"a": str(law_a), "b": str(law_b), "c": str(law_c)}
    out["law_str"] = (f"{law_b}*y - ({law_a})*x = {law_c}" if b.sign() != 0
                      else f"x = {law_c}")

    # Decimal slack of square j at a trial point, against every placed square
    wd = [(_dec(w[0]), _dec(w[1])) for w in words]
    half_dec = Decimal(1) / 2

    def extent_dec(k, qx, qy):
        cx, sx = wd[k]
        return (abs(cx * qx + sx * qy) + abs(cx * qy - sx * qx)) * half_dec

    def feasible(p):
        if p[0] - ex < Q2(0) or p[0] + ex > L or p[1] - ex < Q2(0) or p[1] + ex > L:
            return False
        px, py = _dec(p[0]), _dec(p[1])
        for i in range(len(pos)):
            if i == j or pos[i] is None:
                continue
            dx = px - _dec(pos[i][0])
            dy = py - _dec(pos[i][1])
            best = None
            for owner, other in ((i, j), (j, i)):
                cx, sx = wd[owner]
                for qx, qy in ((cx, sx), (-sx, cx)):
                    s = abs(dx * qx + dy * qy) - (half_dec + extent_dec(other, qx, qy))
                    best = s if best is None else max(best, s)
            if best is None or best < 0:
                return False
        return True

    def line_point(t):
        return (t, law_c - law_a * t) if b.sign() != 0 else (law_c, t)

    seed = _dec(state[j][0] if b.sign() != 0 else state[j][1])

    def boundary(direction, step=Decimal("1e-12")):
        good, bad, s = seed, None, step
        for _ in range(60):
            t = seed + direction * s
            if not feasible(line_point(Q2(t))):
                bad = t
                break
            good, s = t, s * 2
        if bad is None:
            return good
        for _ in range(200):
            mid = (good + bad) / 2
            if mid == good or mid == bad:
                break
            if feasible(line_point(Q2(mid))):
                good = mid
            else:
                bad = mid
        return good

    lo_dec = boundary(-1)
    hi_dec = boundary(1)
    out["segment"] = (str(lo_dec), str(hi_dec))
    out["width"] = str(hi_dec - lo_dec)

    found = []
    band = []
    guard = 0
    for D in dens:
        for pn in range(int(lo_dec * D) - 1, int(hi_dec * D) + 2):
            for rn in range(-bmax * D, bmax * D + 1):
                t = Q2(F(pn, D), F(rn, D))
                # two different readings, both recorded: `t` the field value, which is
                # what the cage is; and run 86's `t.a` the rational part only, which is
                # what the 173 figure counted.  Keeping both is how a control can
                # reproduce the old number *and* say why it was too generous.
                in_band = Q2(lo_dec) <= Q2(F(t.a, 1)) <= Q2(hi_dec)
                in_segment = Q2(lo_dec) <= t <= Q2(hi_dec)
                if not (in_band or in_segment):
                    continue
                cand = line_point(t)
                guard += 1
                if not legacy and (cand[0] - ex < Q2(0) or cand[0] + ex > L):
                    continue
                if cand[1] - ex < Q2(0) or cand[1] + ex > L:
                    continue
                trial[j] = cand
                ok = True
                for i in range(len(pos)):
                    if i == j or pos[i] is None:
                        continue
                    if not any(s.sign() >= 0 for _q, s, _n, _o
                               in pair_axes(trial, words, i, j)):
                        ok = False
                        break
                if ok:
                    d = abs(cand[0] - state[j][0]) + abs(cand[1] - state[j][1])
                    band.append((d, cand))
                    if (legacy and in_band) or (not legacy and in_segment):
                        found.append((d, cand))
    for seq in (found, band):
        seq.sort(key=lambda t: (t[0], t[1][0], t[1][1]))
    out["tested"] = guard
    out["placements"] = [p for _d, p in found]        # inside the cage segment
    out["count"] = len(found)
    out["placements_band"] = [p for _d, p in band]    # the rational-part reading
    out["count_band"] = len(band)
    out["legacy"] = legacy
    out["nearest"] = band[0][1] if band else None
    out["nearest_distance"] = band[0][0] if band else None
    return out


def float_state(state, words):
    """The same sentence as floats, for a cross-check against packlib.verify."""
    return [(float(x), float(y), math.atan2(float(s), float(c)))
            for (x, y), (c, s) in zip(state, words)]


def grid_side(n: int) -> Q2:
    k = math.isqrt(n)
    return Q2(k if k * k == n else k + 1)


# ---------------------------------------------------------------- selftest
def selftest() -> int:
    import random
    # run as a script, this module is __main__; let `import qsqrt2` find it, so a
    # second copy of the class is never created and isinstance keeps working
    sys.modules.setdefault("qsqrt2", sys.modules[__name__])
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    import packlib as P

    n_checks = 0

    # 1. field identities
    assert (Q2(1) + sqrt2()) * (Q2(1) - sqrt2()) == Q2(-1)
    assert word_45()[0] * word_45()[0] == HALF
    a, b = Q2(F(3, 7), F(-2, 5)), Q2(F(5, 11), F(4, 9))
    assert (a / b) * b == a
    assert Q2(0, 1) * Q2(0, 1) == Q2(2)
    assert word_t(F(1, 2))[0] == Q2(F(3, 5)) and word_t(F(1, 2))[1] == Q2(F(4, 5))
    print("control 1 — field identities: (1+√2)(1-√2) = -1, (√2/2)^2 = 1/2, "
          "division round-trips, t=1/2 gives (3/5, 4/5)")
    n_checks += 1

    # 2. the sign rule against 70-digit decimals, on every mixed quadrant
    bad = 0
    for a_num in range(-60, 61):
        for b_num in range(-60, 61):
            if a_num == 0 and b_num == 0:
                continue
            v = Q2(F(a_num, 7), F(b_num, 11))
            approx = Decimal(a_num) / 7 + Decimal(b_num) / 11 * Decimal(2).sqrt()
            want = 1 if approx > 0 else -1
            if v.sign() != want:
                bad += 1
    assert bad == 0, f"{bad} sign disagreements with 70-digit Decimal"
    print("control 2 — the sign rule agrees with 70-digit Decimal on 14,640 "
          "mixed elements (no tolerance anywhere)")
    n_checks += 1

    # 3. a rigid grid: exact side, exact contacts, no clearance
    st = [(Q2(i) + HALF, Q2(j) + HALF) for j in range(3) for i in range(3)]
    g = gate(st, [AXIS] * 9)
    assert g["ok"] and g["L"] == Q2(3) and g["clearance"] == 0
    # contacts include diagonal corner touches: 12 edge + 8 corner
    assert g["contacts"] == 20, g["contacts"]
    print("control 3 — a 3x3 rigid grid: L = 3 exactly, 20 exact contacts "
          "(12 edge + 8 corner), clearance exactly 0)")
    n_checks += 1

    # 4. the 45-degree pair at L = 1 + sqrt 2 is exactly tight, and one
    #    thousandth less is refused
    import mixed_field as M
    st5, w5, L5 = M.corner_glue(word_45())
    g = gate(st5, w5)
    assert g["ok"] and g["L"] == Q2(2) + sqrt2() * HALF, (g["L"], L5)
    assert g["clearance"] == 0
    st6, w6, L6 = M.corner_glue(word_45(), L=L5 - Q2(F(1, 1000)))
    assert not gate(st6, w6)["ok"]
    print(f"control 4 — the 45° corner glue at L = 2+√2/2 = {float(L5):.6f} is "
          "exactly tight; L - 1/1000 is refused")
    n_checks += 1

    # 5. agreement with packlib.verify where the float gate is unambiguous
    random.seed(83)
    agree = 0
    for _ in range(300):
        w = random.choice([AXIS, word_t(F(1, 2)), word_t(F(1, 3))])
        st = [(Q2(F(random.randint(-8, 8), 4)), Q2(F(random.randint(-8, 8), 4)))
              for _ in range(4)]
        ws = [w] * 4
        g = gate(st, ws)
        if g["clearance"] is None or abs(float(g["clearance"])) < 1e-3:
            continue
        f = P.verify(float_state(st, ws))
        assert bool(g["ok"]) == bool(f["ok"]), (st, g, f)
        agree += 1
    assert agree > 50, agree
    print(f"control 5 — the exact gate and packlib.verify agree on {agree} "
          "rational-word states with clearance at least 1e-3 from contact")
    n_checks += 1

    # 6. an overlapping pair is refused with an exactly negative clearance
    st = [(Q2(1, 0) + HALF, HALF), (Q2(1) + HALF, HALF)]
    g = gate(st, [AXIS, AXIS])
    assert not g["ok"] and g["clearance"] == Q2(-1)
    st = [(HALF, HALF), (Q2(1), HALF)]
    g = gate(st, [AXIS, AXIS])
    assert not g["ok"] and g["clearance"] == -HALF, g["clearance"]
    print("control 6 — overlaps are refused exactly: side-by-side by 1, "
          "half-overlap by 1/2")
    n_checks += 1

    # 7. the scorer's side and the exact side agree on a rational-word sentence
    st, w, L = M.two_corner(word_t(F(1, 2)))
    assert gate(st, w)["ok"]
    f = P.verify(float_state(st, w))
    std = abs(float(L) - f["L"])
    assert std < 1e-12, (float(L), f["L"])
    print(f"control 7 — the exact side {str(L)} = {float(L):.6f} matches "
          f"packlib's float side to {std:.1e}")
    n_checks += 1

    # 8. the exact floor and the grid rounding, against their own definitions
    import mixed_field as M
    st, w, L = M.corner_glue(word_45())
    for z in (Q2(F(7, 3)), Q2(F(-5, 4), F(3, 7)), L, L - Q2(10), Q2(0)):
        k = floor_q2(z)
        assert (z - Q2(k)).sign() >= 0 and (z - Q2(k + 1)).sign() < 0, z
    for Mstep in (2, 10, 1000):
        g = grid_round(L, Mstep)
        assert abs(L - Q2(g)) <= HALF * Q2(1) / Q2(Mstep)
    print("control 8 — floor(a+b√2) and the 1/M rounding are decided by exact "
          "comparisons (bracket k <= z < k+1 verified for each)")
    n_checks += 1

    # 9. the lifter: an exact sentence, written as 12-dp decimals, is recovered
    dec = [(Q2(F(f"{float(x):.12f}")), Q2(F(f"{float(y):.12f}")))
           for x, y in st]
    got = lift_sentence(dec, w)
    assert got["status"] == "lifted", got["status"]
    assert got["L"] == L, (got["L"], L)
    assert abs(float(got["clearance"])) < 1e-9
    print(f"control 9 — a 12-dp decimal copy of the 45° corner glue lifts back to "
          f"L = {str(L)} exactly ({got['used']} equations)")
    n_checks += 1

    # 10. and a state whose decimals do not come from a sentence does not lift
    bad = [(x, y) for x, y in dec]
    bad[4] = (dec[4][0] + Q2(F(3, 1000)), dec[4][1])
    got = lift_sentence(bad, w)
    assert got["status"] in ("overlap", "underdetermined", "not-on-lattice"), \
        got["status"]
    print(f"control 10 — a 3e-3 perturbation of the tilted square is "
          f"'{got['status']}', not 'lifted'")
    n_checks += 1

    # 11. the cage segment solver: n = 126's last square, exactly (no monkeypatching)
    import glm_wheels as GW
    rows = GW._delivered_rows()
    st126 = rows[126]
    ws126 = [GW._word_of(t) for _, _, t in st126]
    got = lift_sentence([(Q2(x), Q2(y)) for x, y, _ in st126], ws126)
    assert got["status"] == "not-on-lattice", got["status"]
    j = [i for i, p in enumerate(got["pos"]) if p is None][0]
    lo = got["lo"]
    frame = [(Q2(x) - lo[0], Q2(y) - lo[1]) for x, y, _ in st126]
    seg = cage_segment(frame, ws126, got["pos"], got["L"], j)
    assert seg["rank"] == 1, seg["rank"]
    assert seg["law"]["a"] == str(Q2(-1)) and seg["law"]["b"] == "1", seg["law"]
    assert seg["law"]["c"] == str(Q2(F(11, 2)) + Q2(0, F(5, 2))), seg["law"]
    assert seg["count"] == 4, seg["count"]               # inside the cage, in the box
    old = cage_segment(frame, ws126, got["pos"], got["L"], j, legacy=True)
    assert old["count"] == 173, old["count"]             # run 86's two flaws, replayed
    assert seg["nearest"][0] == Q2(F(43, 32)), seg["nearest"]
    trial = list(got["pos"])
    trial[j] = seg["nearest"]
    g = gate(trial, ws126)
    assert g["ok"] and g["clearance"] == 0, g
    print(f"control 11 — square {j} touches on one axis only (rank 1, "
          f"{seg['law_str']}); the segment is {seg['width'][:12]}... wide and holds "
          f"{seg['count']} placements at clearance 0 in the cage (run 86's rules give "
          f"{old['count']}), nearest "
          f"{seg['nearest']}")
    n_checks += 1

    print(f"selftest: OK ({n_checks} controls)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
