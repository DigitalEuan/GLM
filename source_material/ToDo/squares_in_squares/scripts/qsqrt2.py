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


def gate(state, words):
    """The exact SAT sentence gate.

    Args:
        state: list of (x, y) pairs of Q2 — square centres.
        words: list of (cos, sin) pairs of Q2 — one word per square.

    Returns:
        dict with
          ok         True iff every pair is separated on some axis (exact)
          L          the container side, exactly
          clearance  the worst pair's best axis slack, exactly: >= 0 iff ok,
                     and 0 means at least one pair is in exact contact
          contacts   the number of pairs whose tightest axis is exactly touching
    """
    n = len(state)
    if n != len(words):
        raise ValueError("state and words disagree on the number of squares")
    if n == 0:
        return {"ok": True, "L": Q2(0), "clearance": None, "contacts": 0}
    L = side(state, words)
    worst = None
    contacts = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = state[j][0] - state[i][0]
            dy = state[j][1] - state[i][1]
            best = None
            for owner, other in ((i, j), (j, i)):
                c, s = words[owner]
                for qx, qy in ((c, s), (-s, c)):
                    proj = abs(dx * qx + dy * qy)
                    oc, os_ = words[other]
                    need = HALF + axis_extent(oc, os_, qx, qy)
                    slack = proj - need
                    if best is None or slack > best:
                        best = slack
            if best == 0:
                contacts += 1
            if worst is None or best < worst:
                worst = best
            if best.sign() < 0:
                return {"ok": False, "L": L, "clearance": best,
                        "contacts": contacts, "first_bad": (i, j)}
    return {"ok": True, "L": L, "clearance": worst, "contacts": contacts}


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

    print(f"selftest: OK ({n_checks} controls)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
