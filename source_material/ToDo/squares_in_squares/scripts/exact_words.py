#!/usr/bin/env python3
r"""exact_words.py — which rows are exact sentences, and in which quadratic field.

WHY THIS EXISTS.  Run 151 rebuilt a delivered row as an exact pose only when every cell's
angle was the 0-degree or the 45-degree word, i.e. an element of Q(sqrt 2): 519 of the 1000
rows qualified and 481 were refused as "not in this field".  That refusal was too coarse.
A square's orientation is a point of the unit circle, and the circle's *algebraic* points are
exactly the words this audit can carry:

  * **Q** — the rational points.  Every Pythagorean word (3-4-5, 5-12-13, 8-15-17, ...) and
    every half-angle parametrisation t = p/q is rational, i.e. `(cos, sin) = ((q^2-p^2)/D,
    2pq/D)`, D = p^2+q^2.  A quarter turn (pi/2, pi, 3pi/2) is the axis word: the unit square
    is invariant, so those angles are the *same* word, not a new one.
  * **Q(sqrt k)** for square-free k > 1 — the words with `cos^2` and `sin^2` rational.  The
    45-degree word is k = 2; a lattice rotated by atan(1/2) has `cos^2 = 4/5`, k = 5; by
    atan(1/3), k = 10; 30/60 degrees have `cos^2 = 3/4`, k = 3.
  * **not a word** — any other angle.  Its cosine is not this kind of number, and a pose
    carrying it cannot be rebuilt exactly for less than a full algebraic-number tower.

THE RULE IS DECIDED, NOT FITTED BLINDLY.  `classify` returns a word only when `cos^2` is
within 10^-10 of a rational with denominator <= 2000 — 100x above the CSV's 12-decimal
angle's own error (a truncated radian angle perturbs `cos^2` by ~10^-12) and 1000x below a
coincidence (a random real misses every such rational by ~10^-7).  `sin^2` is then not fitted
but taken as its exact complement, so `cos^2 + sin^2 = 1` holds by construction, and the
complement must match the measured `sin^2` to the same 10^-10.  Everything after that is
exact: the word is built as an element
of `Q(sqrt k)` by `sqrt(a/b) = sqrt(a b) / b` with the squarefree part extracted from an
integer, and `classify` then *checks* `c^2 + s^2 = 1` in the field before returning it.

WHY A MISIDENTIFIED WORD CANNOT INVENT A WIN.  A base is only a seed.  Whatever word is
chosen, the pose it builds is a genuine exact packing of n unit squares, gated pairwise in
that field, and the candidate's side is that pose's side — so a strict beat is a real
packing's side, never a fitted number's.  `base_of` additionally requires the rebuilt side to
reproduce the delivered row's side to 10^-6, so a wrong word is visible in the census rather
than silently changing what "the row" means.

    python3 scripts/exact_words.py --selftest
"""
from __future__ import annotations

import math
import os
import sys
from decimal import Decimal, getcontext, localcontext
from fractions import Fraction as F
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import exact_field as EF          # noqa: E402
import true_geom as TG            # noqa: E402

getcontext().prec = 60

__all__ = ["quad", "sqfree", "root_in", "Word", "classify", "embed",
           "ANGLE_TOL", "FIT_TOL", "DEN_MAX", "selftest"]

#: an angle is a declared word when it is within this many radians of it (the CSV
#: carries 12 decimals of the radian angle, so this is 1000x its own rounding)
ANGLE_TOL = Decimal("1e-9")
#: |cos^2 - a/b| must be below this for the rational fit to be a decision: above the
#: 12-decimal angle's own 10^-12 perturbation, far below a random real's 10^-7
FIT_TOL = F(1, 10 ** 10)
#: and the fit's denominator is bounded, so a random real cannot pass
DEN_MAX = 2000


# --------------------------------------------------------------- the field tower
def sqfree(m: int) -> int:
    """The square-free part of a positive integer: `m = sqfree(m) * t^2`."""
    if m <= 0:
        raise ValueError(f"sqfree needs a positive integer, got {m}")
    out, p = 1, 2
    while p * p <= m:
        while m % (p * p) == 0:
            m //= p * p
        p += 1
    return m


@lru_cache(maxsize=None)
def quad(k: int):
    """`Q(sqrt k)` as a class.  k = 1 has no `Quad` (d must be square-free > 1), so
    rational words are carried in `Q2` with zero radical part and named "Q" separately."""
    if k < 2 or not EF.is_squarefree(k):
        raise ValueError(f"quad needs a square-free k > 1, got {k}")
    return type(f"Q{k}", (EF.Quad,), {"d": k})


def root_in(cls, A: F):
    """`sqrt(A)` as an element of `cls` (A >= 0 rational), or refuse.

    A = a/b = (a b)/b^2, so sqrt(A) = sqrt(a b)/b; with a b = k m^2 that is (m/b) sqrt(k).
    """
    if A < 0:
        raise ValueError(f"root_in needs A >= 0, got {A}")
    if A == 0:
        return cls(0)
    m = A.numerator * A.denominator
    k = sqfree(m)
    t = math.isqrt(m // k)
    if k * t * t != m:                       # can't happen; kept because it is cheap
        raise ValueError(f"squarefree decomposition failed for {A}")
    if k == 1:
        return cls(F(t, A.denominator))
    if k != cls.d:
        raise ValueError(f"sqrt({A}) is in Q(sqrt {k}), not Q(sqrt {cls.d})")
    return cls(0, F(t, A.denominator))


class Word:
    """An exact unit-circle point: `k = 1` means rational (Fractions), else `quad(k)`."""

    __slots__ = ("k", "c", "s", "name")

    def __init__(self, k, c, s, name):
        self.k, self.c, self.s, self.name = k, c, s, name

    @property
    def cls(self):
        return F if self.k == 1 else quad(self.k)

    def check(self):
        """`c^2 + s^2 = 1` exactly in the word's own field."""
        one = self.cls(1)
        return self.c * self.c + self.s * self.s == one

    def element(self, k):
        """The same word carried in `Q(sqrt k)` (k >= 2): rationals embed."""
        cls = quad(k)
        if self.k == 1:
            return cls(self.c), cls(self.s)
        if self.k != k:
            raise ValueError(f"cannot carry a Q(sqrt {self.k}) word into Q(sqrt {k})")
        return self.c, self.s

    def __repr__(self):
        return f"Word(k={self.k}, {self.name})"


def _ratio(dec: Decimal) -> F | None:
    """The rational `a/b`, b <= DEN_MAX, within FIT_TOL of `dec` — or None."""
    val = F(dec)
    near = val.limit_denominator(DEN_MAX)
    return near if abs(near - val) <= FIT_TOL else None


def _word_from_squares(A: F, B: F, name: str = ""):
    """The word with `cos^2 = A`, `sin^2 = B` (A + B = 1), or None if the field is mixed."""
    ka, kb = sqfree(A.numerator * A.denominator), sqfree(B.numerator * B.denominator)
    if ka == kb:
        k = ka
    elif ka == 1:
        k = kb
    elif kb == 1:
        k = ka
    else:
        return None                       # two different radicals: Q(sqrt ka, sqrt kb)
    if k == 1:
        return Word(1, root_in(F, A), root_in(F, B), name or "Q")
    cls = quad(k)
    return Word(k, root_in(cls, A), root_in(cls, B), name or f"Q(sqrt {k})")


def classify(a: Decimal):
    """The exact `Word` of a CSV angle (radians), or None if it is not a declared word."""
    with localcontext() as ctx:                     # callers set their own precision
        ctx.prec = 50
        q = a / TG.HALF_PI
        m = q.to_integral_value()
        off = (q - m) * TG.HALF_PI
        if abs(off) <= ANGLE_TOL:                   # a quarter turn: the axis word
            return Word(1, F(1), F(0), "axis")
        if abs(abs(q - m) - Decimal("0.5")) * TG.HALF_PI <= ANGLE_TOL:
            return Word(2, root_in(quad(2), F(1, 2)), root_in(quad(2), F(1, 2)), "45")
        c, s = TG.cos_sin(a)
        cc, ss = c * c, s * s
    A = _ratio(cc)
    if A is None or not (0 < A < 1):
        return None
    B = 1 - A                                       # exact: the circle's identity
    if B <= 0 or abs(B - F(ss)) > FIT_TOL:
        return None
    w = _word_from_squares(A, B)
    if w is None or not w.check():
        return None
    return w


# ------------------------------------------------------------------- selftest
def selftest() -> int:
    checks = 0
    assert sqfree(1) == 1 and sqfree(8) == 2 and sqfree(45) == 5 and sqfree(10) == 10
    print("  1. the square-free part: 1, 8 = 2*2^2, 45 = 5*3^2, 10")
    checks += 1

    # the Pythagorean catalogue, including the tan(theta/2) parametrisation
    for t, (c, s) in ((F(1, 2), (F(3, 5), F(4, 5))),
                      (F(2), (F(-3, 5), F(4, 5))),
                      (F(1, 3), (F(4, 5), F(3, 5)))):
        w = Word(1, c, s, "t")
        assert w.check(), (t, (c, s))
    print("  2. rational words satisfy c^2 + s^2 = 1 exactly: 3-4-5 at t = 1/2 and 2, "
          "4-3-5 at t = 1/3")
    checks += 1

    # the CSV's own angles of row 50 (0 and atan(3/4)) and a 45-degree cell
    w0 = classify(Decimal("0"))
    w34 = classify(Decimal("0.643501108793"))
    w45 = classify(Decimal("0.785398163397"))
    assert w0 is not None and w0.k == 1 and w0.s == 0, w0
    assert w34 is not None and w34.k == 1 and (w34.c, w34.s) == (F(4, 5), F(3, 5)), w34
    assert w45 is not None and w45.k == 2 and w45.check(), w45
    print("  3. the classifier on real CSV angles: 0 is axis, 0.643501108793 is the "
          "3-4-5 word (4/5, 3/5), 0.785398163397 is 45 degrees in Q(sqrt 2)")
    checks += 1

    # quarter turns are the axis word, and a quarter turn plus 45 is still 45
    for txt in ("1.570796326795", "-1.570796326795", "3.141592653590", "4.712388980385"):
        w = classify(Decimal(txt))
        assert w is not None and w.k == 1 and w.s == 0, (txt, w)
    w = classify(Decimal("2.356194490192"))         # 135 degrees
    assert w is not None and w.k == 2, w
    print("  4. quarter turns are the *same* word: pi/2, -pi/2, pi, 3pi/2 all classify axis, "
          "and 3pi/4 classifies 45 degrees")
    checks += 1

    # atan(1/2) and atan(1/3) and 30 degrees: other quadratic fields, measured
    a_half = Decimal("0.463647609001")              # atan(1/2), cos^2 = 4/5
    a_third = Decimal("0.321750554397")             # atan(1/3), cos^2 = 9/10
    a_30 = Decimal("0.523598775598")                # 30 degrees, cos^2 = 3/4
    for txt, k, A in ((a_half, 5, F(4, 5)), (a_third, 10, F(9, 10)), (a_30, 3, F(3, 4))):
        w = classify(txt)
        assert w is not None and w.k == k, (txt, w)
        assert w.c * w.c == w.cls(A) and w.check(), (txt, w.c * w.c, A)
    print("  5. other quadratic words, recovered from the angle alone: atan(1/2) in "
          "Q(sqrt 5) with cos^2 = 4/5, atan(1/3) in Q(sqrt 10) with 9/10, 30 degrees in "
          "Q(sqrt 3) with 3/4")
    checks += 1

    # a mixed-radical word and a random angle are both refused
    mixed = _word_from_squares(F(1, 3), F(2, 3))
    assert mixed is None, mixed
    for txt in ("0.7", "1.0", "0.123456789012"):
        assert classify(Decimal(txt)) is None, txt
    print("  6. refusals are decided: cos^2 = 1/3 with sin^2 = 2/3 needs Q(sqrt 3, sqrt 6) "
          "and is refused; 0.7, 1.0, 0.123456789012 are not words")
    checks += 1

    # embedding a rational word into a quadratic field preserves it
    cls = quad(5)
    c5, s5 = w34.element(5)
    assert c5 * c5 + s5 * s5 == cls(1), (c5, s5)
    try:
        classify(Decimal("0.463647609001")).element(3)
    except ValueError:
        pass
    else:
        raise AssertionError("a Q(sqrt 5) word must not embed into Q(sqrt 3)")
    print("  7. embedding: the 3-4-5 word is carried into Q(sqrt 5) exactly, and a "
          "Q(sqrt 5) word is refused by Q(sqrt 3)")
    checks += 1

    checked, offenders, skipped = EF.audit_module(
        sys.modules[__name__], exempt=EF.AUDIT_EXEMPT + ("selftest",))
    assert offenders == [], offenders
    print(f"  8. bytecode audit: {checked} decision functions, 0 naming float "
          f"(exempt {skipped})")
    checks += 1
    print(f"exact_words selftest OK ({checks} controls)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    print(__doc__.strip().splitlines()[0])
    print("usage: python3 scripts/exact_words.py --selftest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
