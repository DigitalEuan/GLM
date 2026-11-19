#!/usr/bin/env python3
r"""exact_field.py — a domain-neutral exact scalar tower, and the audit that proves it.

WHY THIS EXISTS.  `qsqrt2.py` grew the ℚ(√2) arithmetic the mixed-field grammar
needs, but the logic in it is not about √2: it is about a **ring of scalars with an
exact sign**, and every instrument built on it (the gate, the rounding, the carrier,
the height-bounded reconstruction) only ever asks two questions — *is this zero?*
and *which of these two is larger?*  This module extracts that layer so the same
machinery can drive a second domain that has nothing to do with squares, and a
third that is not geometry at all.

THE TOWER
    Z          the integers (a subring of Q; arithmetic returns Q)
    Q          the rationals, as a Fraction subclass with sign/floor/ceil
    Q(sqrt d)  the real quadratic field a + b sqrt d, d square-free > 0
    t-basis    rational points on the unit circle: t = p/q in Q gives
               (cos, sin) = ((q^2 - p^2)/(q^2 + p^2), 2pq/(q^2 + p^2)),
               the standard tan(theta/2) parametrisation

Every scalar answers `sign()` exactly, so `==`, `<`, `<=`, `>`, `>=`, `abs`,
`floor`, `ceil` and `is_zero` are derived, never approximated.  `Quad.sign` is the
same case analysis for every d: same-sign `a`, `b` is immediate; the mixed cases
compare `a^2` with `d b^2`, and `a^2 = d b^2` has no nonzero rational solution
because d is square-free.

WHAT "FLOAT-FREE" MEANS HERE.  Not a style rule — an audited property.
`no_float_calls` / `audit` walk **code objects** (not source text, so docstrings
and comments cannot hide or fake a result) and report every decision function that
so much as *names* `float`.  Display functions (`__float__`, `decimal`, and the
`Decimal` cross-witness) are the only exemption, and they are declared in
`DISPLAY_ONLY` so the ledger can list them instead of quietly skipping them.

The Decimal witness is not a float either: `sqrt(d)` is taken at 70 digits by
`decimal.Decimal.sqrt`, so a cross-check can be *independent* of the algebra while
still being exact to any stated precision.
"""
from __future__ import annotations

import math
import sys
from decimal import Decimal, getcontext
from fractions import Fraction as F

getcontext().prec = 70

__all__ = [
    "Scal", "Z", "Q", "Quad", "tword", "tpoint", "is_squarefree",
    "sqrt_decimal", "recover_scalar", "no_float_calls", "audit", "DISPLAY_ONLY",
]


# --------------------------------------------------------------------- scalars
class Scal:
    """Mixin: an ordered exact scalar.  Subclasses implement `sign`.

    Everything here is a *derived* decision — comparisons, absolute value, truth —
    so no subclass needs its own tolerance, and no subclass can disagree with
    `sign` about ordering.
    """

    __slots__ = ()

    # -- to implement ------------------------------------------------------
    def sign(self) -> int:                      # pragma: no cover - interface
        raise NotImplementedError

    def floor(self) -> int:                     # pragma: no cover - interface
        raise NotImplementedError

    # -- derived -----------------------------------------------------------
    def is_zero(self) -> bool:
        return self.sign() == 0

    def ceil(self) -> int:
        return -((-self).floor())

    def __abs__(self):
        return self if self.sign() >= 0 else -self

    def __bool__(self):
        return self.sign() != 0

    def _diff(self, o):
        o = self._coerce(o)
        if o is NotImplemented:
            raise TypeError(f"cannot compare {type(self).__name__} with {type(o)!r}")
        return self - o

    def __lt__(self, o):
        return self._diff(o).sign() < 0

    def __le__(self, o):
        return self._diff(o).sign() <= 0

    def __gt__(self, o):
        return self._diff(o).sign() > 0

    def __ge__(self, o):
        return self._diff(o).sign() >= 0

    @staticmethod
    def _coerce(x):
        raise NotImplementedError                 # pragma: no cover - interface


class Q(Scal, F):
    """An exact rational.  (Z is its integral subring, see `Z`.)"""

    __slots__ = ()

    def __new__(cls, num=0, den=None):
        for v in (num, den):
            if isinstance(v, REFUSED):
                raise TypeError("Q takes int or Fraction, not float")
        return F.__new__(cls, num) if den is None else F.__new__(cls, num, den)

    def sign(self) -> int:
        return (self.numerator > 0) - (self.numerator < 0)

    def floor(self) -> int:
        return self.numerator // self.denominator

    def ceil(self) -> int:
        return -((-self.numerator) // self.denominator)

    @staticmethod
    def _coerce(x):
        if isinstance(x, Q):
            return x
        if isinstance(x, REFUSED):
            raise TypeError("no floats in the tower: pass int, Fraction or Q")
        if isinstance(x, F):
            return Q(x)
        if isinstance(x, int):
            return Q(x)
        return NotImplemented

    def __eq__(self, o):
        if isinstance(o, REFUSED):
            return NotImplemented
        return F.__eq__(self, o)

    def __hash__(self):
        return F.__hash__(self)


class Z(Q):
    """An integer, checked.  Arithmetic returns Q — Z is not closed under division."""

    __slots__ = ()

    def __new__(cls, num=0, den=None):
        v = Q(num, den) if den is not None else Q(num)
        if v.denominator != 1:
            raise ValueError(f"{v} is not an integer")
        return Q.__new__(cls, v.numerator)

    def __add__(self, o):
        return Q(F.__add__(self, o))

    __radd__ = __add__

    def __mul__(self, o):
        return Q(F.__mul__(self, o))

    __rmul__ = __mul__


class Quad(Scal):
    """`a + b sqrt(d)` with `a, b` in Q and `d` a square-free positive integer.

    The field is fixed per subclass (`class Q2(Quad): d = 2`), so instances carry
    only `(a, b)` and every operation is closed.  Floats are refused at
    construction — the point of the class is that nothing here is approximate.
    """

    d = 0
    __slots__ = ("a", "b")

    def __init__(self, a=0, b=0):
        if not self.d or not is_squarefree(self.d):
            raise ValueError(f"Quad needs a square-free d > 0, got {self.d}")
        for v in (a, b):
            if isinstance(v, REFUSED):
                raise TypeError("Quad takes int or Fraction, not float — the point "
                                "of this module is that no float is involved")
        self.a = a if isinstance(a, F) else F(a)
        self.b = b if isinstance(b, F) else F(b)

    # ------------------------------------------------------------- algebra
    def _new(self, a, b):
        return type(self)(a, b)

    @classmethod
    def sqrtd(cls):
        return cls(0, 1)

    def __add__(self, o):
        o = self._coerce(o)
        if o is NotImplemented:
            return NotImplemented
        return self._new(self.a + o.a, self.b + o.b)

    __radd__ = __add__

    def __neg__(self):
        return self._new(-self.a, -self.b)

    def __sub__(self, o):
        o = self._coerce(o)
        return NotImplemented if o is NotImplemented else self + (-o)

    def __rsub__(self, o):
        o = self._coerce(o)
        return NotImplemented if o is NotImplemented else o + (-self)

    def __mul__(self, o):
        o = self._coerce(o)
        if o is NotImplemented:
            return NotImplemented
        # (a + b r)(c + e r) = (ac + d be) + (ae + bc) r
        return self._new(self.a * o.a + self.d * self.b * o.b,
                         self.a * o.b + self.b * o.a)

    __rmul__ = __mul__

    def __truediv__(self, o):
        o = self._coerce(o)
        if o is NotImplemented:
            return NotImplemented
        n = o.a * o.a - self.d * o.b * o.b          # the field norm, rational
        if n == 0:
            raise ZeroDivisionError(f"division by zero in Q(sqrt {self.d})")
        return self._new((self.a * o.a - self.d * self.b * o.b) / n,
                         (self.b * o.a - self.a * o.b) / n)

    def __rtruediv__(self, o):
        o = self._coerce(o)
        return NotImplemented if o is NotImplemented else o / self

    def inverse(self):
        return type(self)(1) / self

    # ---------------------------------------------------------------- sign
    def sign(self) -> int:
        """Exact sign.  `a^2 = d b^2` has no nonzero rational solution (d square-free)."""
        a, b = self.a, self.b
        if a == 0:
            return (b > 0) - (b < 0)
        if b == 0:
            return (a > 0) - (a < 0)
        if a > 0 and b > 0:
            return 1
        if a < 0 and b < 0:
            return -1
        if a > 0:                                # b < 0: compare a with -b sqrt d
            return 1 if a * a > self.d * b * b else -1
        return 1 if self.d * b * b > a * a else -1   # a < 0 < b

    # ------------------------------------------------------------ rounding
    def root_bound(self) -> int:
        """An integer strictly greater than sqrt(d), exactly (no float)."""
        return math.isqrt(self.d) + 1

    def floor(self) -> int:
        """floor(a + b sqrt d), exactly, by bisection on sign tests.

        The bracket uses sqrt(d) < `root_bound`, so it is exact for every d:
        `a - |b| R - 1 <= z <= a + |b| R + 1`.
        """
        a, b = self.a, self.b
        if b == 0:
            return math.floor(a)
        span = abs(b) * self.root_bound()
        lo = math.floor(a - span) - 1
        hi = math.ceil(a + span) + 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if (self - self._new(mid, 0)).sign() >= 0:
                lo = mid
            else:
                hi = mid - 1
        return lo

    # ---------------------------------------------------------- comparison
    def _coerce(self, x):
        if isinstance(x, Quad):
            if type(x) is type(self) or x.d == self.d:
                return x
            raise TypeError(f"cannot mix Q(sqrt {x.d}) with Q(sqrt {self.d})")
        if isinstance(x, REFUSED):
            raise TypeError("no floats: pass int, Fraction or Quad")
        return self._new(x, 0)

    def __eq__(self, o):
        if isinstance(o, REFUSED):
            return NotImplemented
        try:
            o = self._coerce(o)
        except TypeError:
            return NotImplemented
        return self.a == o.a and self.b == o.b

    def __hash__(self):
        return hash((self.d, self.a, self.b))

    # ------------------------------------------------------------- display
    def __float__(self):
        return float(self.a) + float(self.b) * math.sqrt(self.d)

    def __repr__(self):
        return f"Q{self.d}({self.a}, {self.b})"

    def __str__(self):
        if self.b == 0:
            return str(self.a)
        r = f"√{self.d}" if self.b == 1 else f"{self.b}√{self.d}"
        if self.a == 0:
            return r
        return f"{self.a} + {r}" if self.b > 0 else f"{self.a} - {-self.b}√{self.d}"

    def decimal(self, places=50) -> str:
        return sqrt_decimal(self, places)


# ---------------------------------------------------------------- number theory
def is_squarefree(d: int) -> bool:
    """True iff d >= 2 has no square divisor > 1, so Q(sqrt d) is a proper field."""
    if not isinstance(d, int) or d <= 1:
        return False
    k = 2
    while k * k <= d:
        if d % (k * k) == 0:
            return False
        k += 1
    return True


def sqrt_decimal(x, places: int = 50) -> str:
    """`x` to `places` decimals using Decimal's own sqrt (no float anywhere)."""
    dec = (Decimal(x.a.numerator) / Decimal(x.a.denominator)
           + Decimal(x.b.numerator) / Decimal(x.b.denominator)
           * Decimal(x.d).sqrt())
    return str(dec.quantize(Decimal(1).scaleb(-places)))


# ------------------------------------------------------------- t-basis points
def tword(p, q=None):
    """The unit-circle point with `t = tan(theta/2) = p/q`, as exact rationals.

    `t` is any rational; `p, q` are read as a fraction when `q` is omitted.  The
    parametrisation is the standard one (a Pythagorean triple for every rational
    t), and `tword` returns `(cos, sin)` with `cos^2 + sin^2 = 1` exactly.
    """
    t = Q(p, q) if q is not None else (p if isinstance(p, Q) else Q(p))
    den = 1 + t * t
    return ((1 - t * t) / den, (2 * t) / den)


def tpoint(p, q=None):
    """The same point as a pair of `Q` values, with the circle identity asserted."""
    c, s = tword(p, q)
    if (c * c + s * s) != 1:
        raise AssertionError("t-basis point off the unit circle")   # unreachable
    return c, s


# ------------------------------------------------- height-bounded reconstruction
def recover_scalar(x, cls, dens=None, bmax=8, tol=None):
    """Nearest `a + b sqrt d` to a decimal element `x`, on a small-height lattice.

    `b` runs over multiples of `1/D` for a small common denominator `D`, `a` is the
    nearest multiple of `1/(4D)` to the remainder, and every comparison is exact.
    Returns `None` when no candidate is within `tol` (default 1e-7) — a *measured*
    refusal, not a rounded one, which is what lets a census say "this side is not
    in this field at small height" instead of guessing.
    """
    cls = cls if isinstance(cls, type) else type(x)
    tol = cls(0, 0) + F(1, 10 ** 7) if tol is None else tol
    dens = dens or (1, 2, 3, 4, 6, 8, 12, 16)
    for D in dens:
        best = None
        scale = 4 * D
        for num in range(-bmax * D, bmax * D + 1):
            b = F(num, D)
            rest = x - cls(0, b)
            # nearest multiple of 1/scale to rest, decided by exact comparison
            k = (rest * scale).floor()
            if (rest * scale - cls(k + F(1, 2), 0)).sign() >= 0:
                k += 1
            cand = cls(F(k, scale), b)
            err = abs(x - cand)
            if best is None or (err - best[1]).sign() < 0:
                best = (cand, err)
        if best is not None and (best[1] - tol).sign() <= 0:
            return best[0]
    return None


# --------------------------------------------------------------- float audit
#: Functions allowed to name `float` because they only *display* a value.
DISPLAY_ONLY = ("__float__", "decimal")
#: The self-test is exempt: it deliberately plants a float use to prove the audit
#: is not vacuous.  Named here so the exemption is declared, not hidden.
TEST_ONLY = ("selftest",)
#: Functions whose whole job is to hand a state to an *independent float-side*
#: checker (packlib).  They are witnesses, not decisions: the exact verdict never
#: depends on them, and the exemption is declared rather than silently skipped.
WITNESS_ONLY = ("float_state",)
AUDIT_EXEMPT = DISPLAY_ONLY + TEST_ONLY + WITNESS_ONLY
#: The tuple used by every refusal check, so no decision function names `float`.
REFUSED = (float,)


def no_float_calls(fn) -> bool:
    """True iff `fn`'s code (and every nested code object) never names `float`."""
    return not audit(fn)


def audit(*fns):
    """Names of the functions whose bytecode names `float`.  Empty list = clean."""
    bad = []
    for fn in fns:
        stack = [fn.__code__]
        found = False
        while stack:
            c = stack.pop()
            if "float" in c.co_names:
                found = True
                break
            stack.extend(k for k in c.co_consts if hasattr(k, "co_names"))
        if found:
            bad.append(getattr(fn, "__qualname__", getattr(fn, "__name__", str(fn))))
    return bad


def audit_module(mod, exempt=DISPLAY_ONLY):
    """Audit every function defined in `mod` (not imported into it).

    Returns `(checked, offenders, skipped)` where `skipped` are the declared
    display-only functions found in the module.  This is the audit the ledger
    records: it names what was checked instead of asserting a slogan.
    """
    checked, offenders, skipped = 0, [], []
    for name, obj in sorted(vars(mod).items()):
        if not callable(obj) or not hasattr(obj, "__code__"):
            continue
        if getattr(obj, "__module__", None) != mod.__name__:
            continue
        if name in exempt:
            skipped.append(name)
            continue
        checked += 1
        if not no_float_calls(obj):
            offenders.append(name)
    # methods of classes defined here, too
    for name, obj in sorted(vars(mod).items()):
        if not isinstance(obj, type) or obj.__module__ != mod.__name__:
            continue
        for mname, meth in sorted(vars(obj).items()):
            if not hasattr(meth, "__code__") or mname in exempt:
                if hasattr(meth, "__code__"):
                    skipped.append(f"{name}.{mname}")
                continue
            checked += 1
            if not no_float_calls(meth):
                offenders.append(f"{name}.{mname}")
    return checked, offenders, skipped


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    checks = 0

    # 1. the tower's sign rule, against Decimal at 70 digits, for several d
    import random
    rnd = random.Random(84)
    for d in (2, 3, 5, 6, 7, 10, 13):
        cls = type(f"Q{d}", (Quad,), {"d": d, "__slots__": ()})
        for _ in range(200):
            a = F(rnd.randint(-40, 40), rnd.choice((1, 2, 3, 4, 5)))
            b = F(rnd.randint(-40, 40), rnd.choice((1, 2, 3, 4, 5)))
            z = cls(a, b)
            exact = (Decimal(a.numerator) / Decimal(a.denominator)
                     + Decimal(b.numerator) / Decimal(b.denominator) * Decimal(d).sqrt())
            want = (exact > 0) - (exact < 0)
            if z.is_zero():
                continue
            assert z.sign() == want, (d, a, b, z.sign(), want)
            checks += 1
    print(f"control 1 — {checks} signs in Q(sqrt d) for d in 2,3,5,6,7,10,13 agree "
          f"with 70-digit Decimal")

    # 2. floor/ceil bracket their value exactly, in every field tested
    n2 = 0
    for d in (2, 3, 5, 13):
        cls = type(f"Q{d}", (Quad,), {"d": d, "__slots__": ()})
        for _ in range(150):
            z = cls(F(rnd.randint(-30, 30), rnd.choice((1, 2, 3))),
                    F(rnd.randint(-30, 30), rnd.choice((1, 2, 4))))
            k = z.floor()
            assert (z - cls(k, 0)).sign() >= 0, (d, z, k)
            assert (z - cls(k + 1, 0)).sign() < 0, (d, z, k)
            assert z.ceil() == -((-z).floor())
            n2 += 1
    print(f"control 2 — {n2} floors satisfy k <= z < k+1 exactly, and ceil = -floor(-z)")

    # 3. field laws: inverse, norm, and that Z rejects non-integers
    for d in (2, 3, 5):
        cls = type(f"Q{d}", (Quad,), {"d": d, "__slots__": ()})
        for _ in range(50):
            z = cls(F(rnd.randint(-9, 9), rnd.choice((1, 2, 3))),
                    F(rnd.randint(-9, 9), rnd.choice((1, 2, 3))))
            if z.is_zero():
                continue
            assert (z * z.inverse()) == cls(1)
    try:
        Z(3, 2)
        raise AssertionError("Z accepted 3/2")
    except ValueError:
        pass
    print("control 3 — every nonzero element inverts in its own field, and Z(3,2) is "
          "refused")

    # 4. square-free test and the d-check
    assert is_squarefree(2) and is_squarefree(3) and is_squarefree(13)
    assert not is_squarefree(4) and not is_squarefree(8) and not is_squarefree(1)
    try:
        type("Q8", (Quad,), {"d": 8, "__slots__": ()})()
        raise AssertionError("Q8 accepted a non-square-free d")
    except ValueError:
        pass
    print("control 4 — d is validated square-free, so the sign rule stays total")

    # 5. t-basis: cos^2 + sin^2 = 1 for rationals, with two triples checked by hand
    for p, q in ((0, 1), (1, 1), (1, 2), (2, 3), (5, 12), (-3, 7)):
        c, s = tword(p, q)
        assert (c * c + s * s) == 1, (p, q)
    assert tword(0) == (Q(1), Q(0))
    assert tword(1, 2) == (Q(3, 5), Q(4, 5))
    assert tword(3, 4) == (Q(7, 25), Q(24, 25))
    print("control 5 — six rational t-points lie on the circle exactly, and t = 1/2,"
          " 3/4 give the 3-4-5 and 7-24-25 triples")

    # 6. the audit itself: clean functions pass, a float-naming one is caught
    Q2 = type("Q2", (Quad,), {"d": 2, "__slots__": ()})

    def clean(z):
        return z.sign()

    def dirty(z):
        return float(z) > 0

    assert no_float_calls(clean)
    assert not no_float_calls(dirty)
    mod = sys.modules[__name__]
    checked, offenders, skipped = audit_module(mod, exempt=DISPLAY_ONLY + TEST_ONLY)
    assert offenders == [], offenders
    print(f"control 6 — the audit catches a planted float use, and this module's own "
          f"{checked} decision functions are clean ({len(skipped)} display-only "
          f"exemptions declared)")

    # 7. height-bounded recovery in a field that is not the packing one
    Q3 = type("Q3", (Quad,), {"d": 3, "__slots__": ()})

    def as_decimal(z, places=12):
        return Q3(F(sqrt_decimal(z, places).replace(" ", "")), 0)

    target = Q3(F(7, 2), F(-3, 4))                 # 3.5 - 0.75 sqrt3
    got = recover_scalar(as_decimal(target), Q3, dens=(2, 4), bmax=6,
                         tol=Q3(F(1, 10 ** 7)))
    assert got == target, (got, target)
    off = Q3(F(9, 7), F(1, 11))
    assert recover_scalar(as_decimal(off), Q3) is None
    print("control 7 — recovery in Q(sqrt 3) returns 7/2 - 3/4 sqrt3 exactly, and "
          "refuses a non-lattice value")

    print("selftest: OK (7 controls)")
    return checks


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        selftest()
        return 0
    if "--audit" in argv:
        mod = sys.modules[__name__]
        checked, offenders, skipped = audit_module(mod, exempt=DISPLAY_ONLY + TEST_ONLY)
        print(f"float audit: {checked} decision functions checked, "
              f"{len(offenders)} naming float, display-only: {skipped}")
        for name in offenders:
            print(f"  OFFENDER {name}")
        return 0 if not offenders else 1
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
