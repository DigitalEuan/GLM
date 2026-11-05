"""Certified rational enclosures (CentCalculus2 §9).

Exact rational arithmetic cannot express ``sqrt 2``, ``e`` or ``log 2``.  The
core therefore returns an :class:`Interval` with exact rational endpoints and
*proves* each enclosure by construction:

* ``sqrt``: scaled integer square root; endpoints satisfy ``lo² <= x <= hi²``
  exactly (checked before returning).
* ``exp``: Taylor series on a halved argument with the Lagrange remainder
  ``|R_N| <= e^{|y|} |y|^{N+1}/(N+1)! <= 2 |y|^{N+1}/(N+1)!`` for
  ``|y| <= 1/2``, then exact repeated squaring.
* ``log``: atanh series for ``log(m)``, ``m in [1,2)``, with the positive tail
  bound ``2 z^{2N+1}/((2N+1)(1-z²))`` for ``z <= 1/3``, plus ``k·log 2``.

Each routine takes a step budget and raises ``resource_budget_exhausted`` when
the requested width cannot be certified within it.  Nothing here is a float
computation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Optional

from .exact import (
    CentError,
    ErrorCode,
    Q,
    div,
    format_q,
    q,
)

_DEFAULT_PREC = 64
_MAX_TERMS = 4096


def _m(x: Any) -> Q:
    return x if isinstance(x, Fraction) else q(x)


@dataclass(frozen=True)
class Interval:
    """A closed rational enclosure ``[lo, hi]``."""

    lo: Q
    hi: Q

    def __post_init__(self) -> None:
        lo, hi = _m(self.lo), _m(self.hi)
        object.__setattr__(self, "lo", lo)
        object.__setattr__(self, "hi", hi)
        if lo > hi:
            raise CentError(
                ErrorCode.INVALID_INPUT,
                "interval lower endpoint exceeds upper endpoint",
                detail={"lo": str(lo), "hi": str(hi)},
            )

    # -- construction -----------------------------------------------------
    @staticmethod
    def point(x: Q) -> "Interval":
        x = _m(x)
        return Interval(x, x)

    @staticmethod
    def of(lo: Any, hi: Any) -> "Interval":
        return Interval(_m(lo), _m(hi))

    # -- observations -----------------------------------------------------
    @property
    def width(self) -> Q:
        return self.hi - self.lo

    @property
    def midpoint(self) -> Q:
        return (self.lo + self.hi) / 2

    @property
    def is_point(self) -> bool:
        return self.lo == self.hi

    def contains(self, x: Any) -> bool:
        x = _m(x)
        return self.lo <= x <= self.hi

    def contains_interval(self, other: "Interval") -> bool:
        return self.lo <= other.lo and other.hi <= self.hi

    def __contains__(self, x: Any) -> bool:
        return self.contains(x)

    # -- arithmetic -------------------------------------------------------
    def __add__(self, other: Any) -> "Interval":
        o = as_interval(other)
        return Interval(self.lo + o.lo, self.hi + o.hi)

    def __radd__(self, other: Any) -> "Interval":
        return as_interval(other) + self

    def __neg__(self) -> "Interval":
        return Interval(-self.hi, -self.lo)

    def __sub__(self, other: Any) -> "Interval":
        return self + (-as_interval(other))

    def __rsub__(self, other: Any) -> "Interval":
        return as_interval(other) - self

    def __mul__(self, other: Any) -> "Interval":
        o = as_interval(other)
        products = (self.lo * o.lo, self.lo * o.hi, self.hi * o.lo, self.hi * o.hi)
        return Interval(min(products), max(products))

    def __rmul__(self, other: Any) -> "Interval":
        return as_interval(other) * self

    def scale(self, k: Any) -> "Interval":
        k = _m(k)
        if k >= 0:
            return Interval(k * self.lo, k * self.hi)
        return Interval(k * self.hi, k * self.lo)

    def __truediv__(self, other: Any) -> "Interval":
        o = as_interval(other)
        if o.lo <= 0 <= o.hi:
            raise CentError(
                ErrorCode.DIVISION_BY_ZERO,
                "interval denominator contains zero",
                detail={"lo": str(o.lo), "hi": str(o.hi)},
            )
        return self * o.reciprocal()

    def reciprocal(self) -> "Interval":
        if self.lo <= 0 <= self.hi:
            raise CentError(ErrorCode.DIVISION_BY_ZERO, "interval contains zero")
        return Interval(1 / self.hi, 1 / self.lo)

    def abs(self) -> "Interval":
        if self.lo >= 0:
            return self
        if self.hi <= 0:
            return -self
        return Interval(Fraction(0), max(-self.lo, self.hi))

    def pow_int(self, n: int) -> "Interval":
        """Exact integer power; negative ``n`` requires an interval away from 0."""
        if not isinstance(n, int):
            raise CentError(ErrorCode.TYPE_ERROR, "interval power needs an integer exponent")
        if n == 0:
            return Interval.point(Fraction(1))
        if n < 0:
            return self.reciprocal().pow_int(-n)
        result = Interval.point(Fraction(1))
        base = self
        while n:
            if n & 1:
                result = result * base
            n >>= 1
            if n:
                base = base * base
        return result

    # -- certified transcendental functions -------------------------------
    def exp(self, prec_bits: int = _DEFAULT_PREC, max_terms: int = _MAX_TERMS) -> "Interval":
        """Enclosure of ``exp(x)`` for the whole interval."""
        if self.is_point:
            return exp_q(self.lo, prec_bits, max_terms)
        # Monotone: evaluate both endpoints.
        return exp_q(self.lo, prec_bits, max_terms) | exp_q(self.hi, prec_bits, max_terms)

    def log(self, prec_bits: int = _DEFAULT_PREC, max_terms: int = _MAX_TERMS) -> "Interval":
        """Enclosure of ``log(x)``; requires strictly positive endpoints."""
        if self.lo <= 0:
            raise CentError(ErrorCode.DOMAIN_ERROR, "log requires a strictly positive interval")
        if self.is_point:
            return log_q(self.lo, prec_bits, max_terms)
        return log_q(self.lo, prec_bits, max_terms) | log_q(self.hi, prec_bits, max_terms)

    def sqrt(self, prec_bits: int = _DEFAULT_PREC) -> "Interval":
        if self.lo < 0:
            raise CentError(ErrorCode.DOMAIN_ERROR, "sqrt requires a nonnegative interval")
        return sqrt_q(self.lo, prec_bits) | sqrt_q(self.hi, prec_bits)

    def __or__(self, other: "Interval") -> "Interval":
        """Convex hull of two enclosures."""
        return Interval(min(self.lo, other.lo), max(self.hi, other.hi))

    def __repr__(self) -> str:
        return f"Interval({format_q(self.lo)}, {format_q(self.hi)})"

    def as_dict(self) -> dict[str, Any]:
        return {"lo": str(self.lo), "hi": str(self.hi), "width": str(self.width)}


def as_interval(value: Any) -> Interval:
    if isinstance(value, Interval):
        return value
    return Interval.point(_m(value))


def point(x: Any) -> Interval:
    return as_interval(x)


# ---------------------------------------------------------------------------
# sqrt
# ---------------------------------------------------------------------------

def sqrt_q(x: Any, prec_bits: int = _DEFAULT_PREC) -> Interval:
    """Certified enclosure of ``sqrt(x)`` for a nonnegative rational.

    For ``x = n/d`` and precision ``p``, with ``S = isqrt(n·d·4^p)``:

    * ``(S/(d·2^p))² = S²/(d²·4^p) <= x``
    * ``((S+1)/(d·2^p))² > x``

    so the enclosure is exact by integer arithmetic.  A rational root is
    returned as a point interval.
    """
    x = _m(x)
    if x < 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "sqrt of a negative rational")
    if x == 0:
        return Interval.point(Fraction(0))
    n, d = x.numerator, x.denominator
    rn, rd = math.isqrt(n), math.isqrt(d)
    if rn * rn == n and rd * rd == d:
        return Interval.point(Fraction(rn, rd))

    if prec_bits <= 0 or prec_bits > 8192:
        raise CentError(ErrorCode.INVALID_INPUT, "prec_bits must be in 1..8192")

    scale = 1 << prec_bits
    s = math.isqrt(n * d * scale * scale)
    lo = Fraction(s, d * scale)
    hi = Fraction(s + 1, d * scale)
    if lo * lo > x or hi * hi <= x:  # pragma: no cover - defensive invariant
        raise CentError(ErrorCode.APPROXIMATION_UNPROVED, "sqrt enclosure invariant failed")
    return Interval(lo, hi)


# ---------------------------------------------------------------------------
# exp
# ---------------------------------------------------------------------------

def _exp_series(y: Q, tol: Q, max_terms: int) -> Interval:
    """Taylor enclosure of exp(y) for |y| <= 1/2, using e^|y| <= 2."""
    term = Fraction(1)
    total = Fraction(1)
    n = 0
    while True:
        n += 1
        term = term * y / n
        total += term
        remainder = 2 * abs(y) ** (n + 1) / math.factorial(n + 1)
        if remainder <= tol:
            return Interval(total, total + remainder)
        if n >= max_terms:
            raise CentError(
                ErrorCode.BUDGET_EXHAUSTED,
                "exp series did not reach the requested width",
                detail={"terms": n, "tol": format_q(tol)},
            )


def exp_q(x: Any, prec_bits: int = _DEFAULT_PREC, max_terms: int = _MAX_TERMS) -> Interval:
    """Certified enclosure of ``exp(x)`` for any rational ``x``."""
    x = _m(x)
    if x == 0:
        return Interval.point(Fraction(1))
    negative = x < 0
    a = -x if negative else x

    # Range reduction: a / 2^k <= 1/2.
    k = 0
    while a / (1 << k) > Fraction(1, 2):
        k += 1
    y = a / (1 << k)

    # Account for error amplification by k squarings (relative error doubles).
    tol = Fraction(1, 1 << (prec_bits + k + 4))
    interval = _exp_series(y, tol, max_terms)
    for _ in range(k):
        interval = Interval(interval.lo * interval.lo, interval.hi * interval.hi)
    if negative:
        interval = interval.reciprocal()
    # exp is strictly positive.
    return interval


# ---------------------------------------------------------------------------
# log
# ---------------------------------------------------------------------------

def _floor_log2(x: Q) -> int:
    """Exact floor(log2(x)) for x > 0."""
    n, d = x.numerator, x.denominator
    k = n.bit_length() - d.bit_length()
    if Fraction(2) ** k > x:
        k -= 1
    while Fraction(2) ** (k + 1) <= x:
        k += 1
    return k


def _atanh_series(z: Q, tol: Q, max_terms: int) -> Interval:
    """Enclosure of ``2·atanh(z)`` for ``0 <= z <= 1/3``.

    All series terms are nonnegative, so the partial sum is a lower bound and
    the positive tail bound is the upper bound.
    """
    z2 = z * z
    power = z
    partial = Fraction(0)
    n = 0
    while True:
        term = power / (2 * n + 1)
        partial += term
        remainder = 2 * (power * z2) / ((2 * n + 3) * (1 - z2))
        if remainder <= tol:
            return Interval(2 * partial, 2 * partial + remainder)
        if n >= max_terms:
            raise CentError(
                ErrorCode.BUDGET_EXHAUSTED,
                "log series did not reach the requested width",
                detail={"terms": n, "tol": format_q(tol)},
            )
        power *= z2
        n += 1


def _log2_interval(prec_bits: int, max_terms: int) -> Interval:
    return _atanh_series(Fraction(1, 3), Fraction(1, 1 << (prec_bits + 4)), max_terms)


def log_q(x: Any, prec_bits: int = _DEFAULT_PREC, max_terms: int = _MAX_TERMS) -> Interval:
    """Certified enclosure of the natural logarithm for ``x > 0``."""
    x = _m(x)
    if x <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "log requires a strictly positive argument")
    if x == 1:
        return Interval.point(Fraction(0))

    k = _floor_log2(x)
    m = x / (Fraction(2) ** k)  # in [1, 2)
    z = (m - 1) / (m + 1)       # in [0, 1/3)

    tol = Fraction(1, (1 << (prec_bits + 4)) * (abs(k) + 1))
    log_m = _atanh_series(z, tol, max_terms)
    log_2 = _log2_interval(prec_bits + 8, max_terms)
    scaled = log_2.scale(k)
    return log_m + scaled


# ---------------------------------------------------------------------------
# helpers used by the evaluator
# ---------------------------------------------------------------------------

def add(a: Any, b: Any) -> Interval:
    return as_interval(a) + as_interval(b)


def mul(a: Any, b: Any) -> Interval:
    return as_interval(a) * as_interval(b)


def div_interval(a: Any, b: Any) -> Interval:
    return as_interval(a) / as_interval(b)


def exp(x: Any, prec_bits: int = _DEFAULT_PREC) -> Interval:
    return exp_q(x, prec_bits)


def log(x: Any, prec_bits: int = _DEFAULT_PREC) -> Interval:
    return log_q(x, prec_bits)


def sqrt(x: Any, prec_bits: int = _DEFAULT_PREC) -> Interval:
    return sqrt_q(x, prec_bits)


def exp_constant(prec_bits: int = _DEFAULT_PREC) -> Interval:
    """Certified enclosure of Euler's number."""
    return exp_q(Fraction(1), prec_bits)


def _atan_series(z: Q, tol: Q, max_terms: int = _MAX_TERMS) -> Interval:
    """Enclosure of ``arctan(z)`` for ``0 <= z <= 1``.

    The series is alternating with decreasing terms, so the partial sum plus
    the first omitted term brackets the value (Leibniz bound).
    """
    z2 = z * z
    power = z
    partial = Fraction(0)
    sign = 1
    n = 0
    while True:
        partial += sign * power / (2 * n + 1)
        next_power = power * z2
        remainder = next_power / (2 * n + 3)
        if remainder <= tol:
            if sign > 0:
                return Interval(partial - remainder, partial)
            return Interval(partial, partial + remainder)
        if n >= max_terms:
            raise CentError(
                ErrorCode.BUDGET_EXHAUSTED,
                "arctan series did not reach the requested width",
                detail={"terms": n, "tol": format_q(tol)},
            )
        power = next_power
        sign = -sign
        n += 1


def pi_interval(prec_bits: int = _DEFAULT_PREC) -> Interval:
    """Certified enclosure of π using Machin's formula.

    ``π = 16·arctan(1/5) − 4·arctan(1/239)``; both arctan series are alternating
    with a Leibniz remainder bound.  No float constant is used.
    """
    tol = Fraction(1, 1 << (prec_bits + 8))
    a = _atan_series(Fraction(1, 5), tol)
    b = _atan_series(Fraction(1, 239), tol)
    return Interval(16 * a.lo - 4 * b.hi, 16 * a.hi - 4 * b.lo)
