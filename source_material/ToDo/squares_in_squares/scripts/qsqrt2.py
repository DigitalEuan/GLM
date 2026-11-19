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

getcontext().prec = 70

ONE = None       # assigned at the end of the class body
HALF = None


class Q2:
    """a + b*sqrt(2) with a, b in Q.  Exact; floats are refused at construction."""

    __slots__ = ("a", "b")

    def __init__(self, a=0, b=0):
        for v in (a, b):
            if isinstance(v, float):
                raise TypeError("Q2 takes int or Fraction, not float — the point "
                                "of this module is that no float is involved")
        self.a = a if isinstance(a, F) else F(a)
        self.b = b if isinstance(b, F) else F(b)

    # ------------------------------------------------------------- algebra
    def __add__(self, o):
        o = _q2(o)
        return Q2(self.a + o.a, self.b + o.b)

    __radd__ = __add__

    def __neg__(self):
        return Q2(-self.a, -self.b)

    def __sub__(self, o):
        return self + (-_q2(o))

    def __rsub__(self, o):
        return _q2(o) + (-self)

    def __mul__(self, o):
        o = _q2(o)
        # (a + b r)(c + d r) = (ac + 2bd) + (ad + bc) r
        return Q2(self.a * o.a + 2 * self.b * o.b,
                  self.a * o.b + self.b * o.a)

    __rmul__ = __mul__

    def __truediv__(self, o):
        o = _q2(o)
        n = o.a * o.a - 2 * o.b * o.b          # the field norm, rational
        if n == 0:
            raise ZeroDivisionError("Q2 division by zero")
        return Q2((self.a * o.a - 2 * self.b * o.b) / n,
                  (self.b * o.a - self.a * o.b) / n)

    def __rtruediv__(self, o):
        return _q2(o) / self

    def __abs__(self):
        return self if self.sign() >= 0 else -self

    def sign(self) -> int:
        """Exact sign.  sqrt 2 is irrational, so a^2 == 2b^2 only at (0, 0)."""
        a, b = self.a, self.b
        if a == 0:
            return 0 if b == 0 else (1 if b > 0 else -1)
        if b == 0:
            return 1 if a > 0 else -1
        if a > 0 and b > 0:
            return 1
        if a < 0 and b < 0:
            return -1
        if a > 0:                               # b < 0: compare a with b sqrt 2
            return 1 if a * a > 2 * b * b else -1
        return 1 if 2 * b * b > a * a else -1   # a < 0 < b

    # --------------------------------------------------------- comparison
    def __eq__(self, o):
        try:
            o = _q2(o)
        except TypeError:
            return NotImplemented
        return self.a == o.a and self.b == o.b

    def __hash__(self):
        return hash((self.a, self.b))

    def __lt__(self, o):
        return (self - _q2(o)).sign() < 0

    def __le__(self, o):
        return (self - _q2(o)).sign() <= 0

    def __gt__(self, o):
        return (self - _q2(o)).sign() > 0

    def __ge__(self, o):
        return (self - _q2(o)).sign() >= 0

    def __bool__(self):
        return not (self.a == 0 and self.b == 0)

    # ------------------------------------------------------------- display
    def __float__(self):
        return float(self.a) + float(self.b) * math.sqrt(2.0)

    def __repr__(self):
        return f"Q2({self.a}, {self.b})"

    def __str__(self):
        if self.b == 0:
            return str(self.a)
        r = "√2" if self.b == 1 else f"{self.b}√2"
        if self.a == 0:
            return r
        return f"{self.a} + {r}" if self.b > 0 else f"{self.a} - {-self.b}√2"

    def decimal(self, places=12) -> str:
        s = f"{float(self):+.{places}f}"
        return s


def _q2(x) -> Q2:
    if isinstance(x, Q2):
        return x
    if isinstance(x, float):
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
def frame_extent(c: Q2, s: Q2) -> Q2:
    """Half-extent of the unit square with frame (c, s) along the x axis."""
    return (abs(c) + abs(s)) * HALF


def axis_extent(c: Q2, s: Q2, qx: Q2, qy: Q2) -> Q2:
    """Half-extent of the unit square with frame (c, s) along the unit axis q."""
    # edges u = (c, s), v = (-s, c); extent = (|u.q| + |v.q|) / 2
    return (abs(c * qx + s * qy) + abs(c * qy - s * qx)) * HALF


def side(state, words) -> Q2:
    """The container side: max over the two axes of the state's extent."""
    n = len(state)
    ex = [frame_extent(*w) for w in words]
    xs = [state[i][0] + ex[i] for i in range(n)]
    xn = [state[i][0] - ex[i] for i in range(n)]
    ys = [state[i][1] + ex[i] for i in range(n)]
    yn = [state[i][1] - ex[i] for i in range(n)]
    return max(max(xs) - min(xn), max(ys) - min(yn))


def pair_axes(state, words, i, j):
    """The four SAT (axis, slack, need) triples of a pair, exactly.

    `slack = |d.q| - (1/2 + ext_other(q))`; the pair is separated iff some slack
    is >= 0, and the pair's distance from contact is the LARGEST of the four.
    """
    dx = state[j][0] - state[i][0]
    dy = state[j][1] - state[i][1]
    out = []
    for owner, other in ((i, j), (j, i)):
        c, s = words[owner]
        oc, os_ = words[other]
        for qx, qy in ((c, s), (-s, c)):
            proj = abs(dx * qx + dy * qy)
            need = HALF + axis_extent(oc, os_, qx, qy)
            out.append(((qx, qy), proj - need, need, owner))
    return out


def gate(state, words):
    """The exact SAT sentence gate.

    Args:
        state: list of (x, y) pairs of Q2 — square centres.
        words: list of (cos, sin) pairs of Q2 — one word per square.

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
    a margin of at least 2 - sqrt(2) > 0.5 and cannot be the worst pair.  The
    prune is exact (it is decided by a field comparison), not a tolerance.
    """
    n = len(state)
    if n != len(words):
        raise ValueError("state and words disagree on the number of squares")
    if n == 0:
        return {"ok": True, "L": Q2(0), "clearance": None, "contacts": 0,
                "violations": 0}
    L = side(state, words)
    two = Q2(2)
    worst = None
    contacts = violations = 0
    for i in range(n):
        xi, yi = state[i]
        for j in range(i + 1, n):
            if abs(state[j][0] - xi) >= two or abs(state[j][1] - yi) >= two:
                continue
            best = None
            for _q, slack, _need, _owner in pair_axes(state, words, i, j):
                if best is None or slack > best:
                    best = slack
            if best == 0:
                contacts += 1
            if best.sign() < 0:
                violations += 1
            if worst is None or best < worst:
                worst = best
    return {"ok": violations == 0, "L": L, "clearance": worst,
            "contacts": contacts, "violations": violations}


# ----------------------------------------------------- exact rounding (no float)
def floor_q2(z: Q2) -> int:
    """floor(a + b*sqrt 2), exactly.  Bracket from a and |b|, then bisect on
    exact sign tests; sqrt 2 < 2 gives a - 2|b| - 1 <= z <= a + 2|b| + 1."""
    a, b = z.a, z.b
    if b == 0:
        return math.floor(a)
    lo = math.floor(a) - 2 * math.ceil(abs(b)) - 1
    hi = math.floor(a) + 2 * math.ceil(abs(b)) + 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if (z - Q2(mid)).sign() >= 0:
            lo = mid
        else:
            hi = mid - 1
    return lo


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
    tries = (((1, 2), 8, (4, 2)),
             ((1, 2, 3, 4, 5, 6, 7, 8), 6, (8, 64)),
             (bdens, bmax, adens))
    best = (None, None, None)
    for bds, bm, ads in tries:
        for bd in bds:
            for num in range(-bm * bd, bm * bd + 1):
                b = F(num, bd)
                rest = Ldec - Q2(0, b)
                for ad in ads:
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


def recover_leftovers(pos, shift, tol, dens, bmax):
    """Place every still-unplaced square by height recovery in place.

    Tries the row's own lattice first and the generic small denominators second,
    and returns the number of squares still unrecovered (0 on success).
    """
    for round_dens in ((dens, 2 * dens, 4 * dens), (1, 2, 3, 4, 6, 8, 12, 16)):
        miss = 0
        for j in range(len(pos)):
            if pos[j] is not None:
                continue
            x = recover_point(shift[j][0], tol=tol, dens=round_dens, bmax=bmax)
            y = recover_point(shift[j][1], tol=tol, dens=round_dens, bmax=bmax)
            if x is None or y is None:
                miss += 1
            else:
                pos[j] = (x, y)
        if miss == 0:
            return 0
    return miss


def lift_sentence(state, words, tol=None):
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
        miss = recover_leftovers(pos, shift, tol, lattice_den(W, H), height_bound(W, H))
        recovered = sum(1 for p in pos if p is not None) - placed
        if miss:
            return {"status": "not-on-lattice", "state": None,
                    "L": W if W > H else H, "clearance": None, "contacts": 0,
                    "violations": 0, "used": used, "placed": placed,
                    "recovered": recovered, "unrecovered": miss,
                    "side_residual": residW if residW > residH else residH}
    g = gate(pos, words)
    return {"status": "lifted" if g["ok"] else "overlap", "state": pos,
            "L": g["L"], "clearance": g["clearance"],
            "contacts": g["contacts"], "violations": g["violations"],
            "used": used, "placed": placed, "recovered": recovered,
            "side_residual": residW if residW > residH else residH}


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

    print(f"selftest: OK ({n_checks} controls)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
