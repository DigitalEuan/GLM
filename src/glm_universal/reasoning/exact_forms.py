"""``glm_universal.reasoning.exact_forms`` -- closed forms the question frames
of Phase 89 answer in.

Three small exact algebras, each with a rendering a reader can check and a
rendering :mod:`glm_universal.reasoning.real_expr` can read back (so every
decimal the frames print is a truncation of a convergent exact process, never
a float):

``Surd``      ``a + b*sqrt(c)`` with rational ``a, b`` and square-free ``c``:
              the magnitudes of Gaussian-rational quantities (``|Gamma|``,
              VSWR, ``omega = sqrt(8)``).
``LogForm``   ``r + sum_p c_p * log_B(p)`` over primes ``p``, rational ``r``,
              ``c_p``: every entropy, mutual information and capacity of a
              distribution with rational masses is exactly one of these
              (``log2 3`` is irrational, ``3/2 - 3/4*log2(3)`` is exact).
              :func:`log_identity_holds` checks a claimed ``LogForm`` value of
              ``sum_i w_i log_B(q_i)`` by raising both sides to a common
              integer power -- integer arithmetic only, no series.
``Poly``      polynomials with rational coefficients as coefficient tuples,
              with products, Routh's cubic condition and exact root isolation
              by Sturm sequences (used where a root is irrational: the
              equilibrium of an ``x^3/(1-x)^2 = K`` balance).

Standard library only; no float anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from math import gcd, isqrt
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = ["Surd", "sqrt_of", "factor", "LogForm", "log_of", "entropy",
           "log_identity_holds", "scientific", "poly_mul", "poly_eval", "poly_add",
           "sturm_roots", "decimal"]


# ===========================================================================
# 1.  INTEGERS
# ===========================================================================

def factor(n: int) -> Dict[int, int]:
    """Prime factorisation of a positive integer (trial division; the frames
    only meet small numbers)."""
    if n < 1:
        raise ValueError("factor: a positive integer is needed")
    out: Dict[int, int] = {}
    p = 2
    while p * p <= n:
        while n % p == 0:
            out[p] = out.get(p, 0) + 1
            n //= p
        p += 1
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


def decimal(q: Fraction, places: int = 6) -> str:
    """A rational truncated (toward zero) to ``places`` decimals."""
    q = Fraction(q)
    sign = "-" if q < 0 else ""
    q = abs(q)
    whole = (q.numerator * 10 ** places) // q.denominator
    digits = str(whole).rjust(places + 1, "0")
    return f"{sign}{digits[:-places]}.{digits[-places:]}" if places else \
        sign + digits


def scientific(q: Fraction, digits: int = 4) -> str:
    """A positive rational as ``m.mmmme-N`` (mantissa truncated, exact
    exponent); ``0`` as ``0``."""
    q = Fraction(q)
    if q == 0:
        return "0"
    sign = "-" if q < 0 else ""
    q = abs(q)
    e = len(str(q.numerator)) - len(str(q.denominator))
    if Fraction(10) ** e > q:
        e -= 1
    if Fraction(10) ** (e + 1) <= q:
        e += 1
    return f"{sign}{decimal(q / Fraction(10) ** e, digits)}e{e:+d}"


# ===========================================================================
# 2.  SURDS
# ===========================================================================

@dataclass(frozen=True)
class Surd:
    """``a + b*sqrt(c)``, ``c`` a square-free positive integer (``c = 1``
    means rational)."""

    a: Fraction
    b: Fraction = Fraction(0)
    c: int = 1

    def is_rational(self) -> bool:
        return self.b == 0 or self.c == 1

    def rational(self) -> Fraction:
        return self.a + (self.b if self.c == 1 else 0)

    def text(self) -> str:
        if self.is_rational():
            return str(self.rational())
        root = f"sqrt({self.c})"
        b = self.b
        term = root if b == 1 else (f"-{root}" if b == -1 else f"{b}*{root}")
        if self.a == 0:
            return term
        if b < 0:
            neg = root if b == -1 else f"{-b}*{root}"
            return f"{self.a} - {neg}"
        return f"{self.a} + {term}"

    def expr(self) -> str:
        """The rendering :func:`real_expr.parse_expression` reads."""
        if self.is_rational():
            r = self.rational()
            return f"({r.numerator}/{r.denominator})"
        return (f"(({self.a.numerator}/{self.a.denominator}) + "
                f"({self.b.numerator}/{self.b.denominator})*sqrt({self.c}))")

    def square_parts(self) -> Tuple[Fraction, Fraction]:
        """``(a^2 + b^2 c, 2ab)``: the square as ``x + y*sqrt(c)``."""
        return (self.a * self.a + self.b * self.b * self.c,
                2 * self.a * self.b)


def sqrt_of(r: Fraction) -> Surd:
    """``sqrt(r)`` for a rational ``r >= 0`` as ``b*sqrt(c)``."""
    r = Fraction(r)
    if r < 0:
        raise ValueError("sqrt_of: negative")
    n = r.numerator * r.denominator           # sqrt(n/d) = sqrt(n d)/d
    out, rest = 1, 1
    for p, k in factor(n).items() if n else ():
        out *= p ** (k // 2)
        rest *= p ** (k % 2)
    if n == 0:
        return Surd(Fraction(0))
    coef = Fraction(out, r.denominator)
    if rest == 1:
        return Surd(coef)
    return Surd(Fraction(0), coef, rest)


# ===========================================================================
# 3.  LOGARITHMS OF RATIONALS
# ===========================================================================

@dataclass(frozen=True)
class LogForm:
    """``rational + sum_p coeffs[p] * log_base(p)``; with ``base == 2`` the
    prime ``2`` folds into the rational part, with ``base == "e"`` it is a
    term like any other."""

    rational: Fraction
    coeffs: Tuple[Tuple[int, Fraction], ...]
    base: object = 2

    @staticmethod
    def make(rational: Fraction, coeffs: Dict[int, Fraction],
             base: object = 2) -> "LogForm":
        coeffs = dict(coeffs)
        if base == 2 and 2 in coeffs:
            rational += coeffs.pop(2)
        return LogForm(Fraction(rational),
                       tuple(sorted((p, Fraction(c)) for p, c in
                                    coeffs.items() if c != 0)), base)

    def __add__(self, other: "LogForm") -> "LogForm":
        d = dict(self.coeffs)
        for p, c in other.coeffs:
            d[p] = d.get(p, 0) + c
        return LogForm.make(self.rational + other.rational, d, self.base)

    def __neg__(self) -> "LogForm":
        return LogForm.make(-self.rational, {p: -c for p, c in self.coeffs},
                            self.base)

    def __sub__(self, other: "LogForm") -> "LogForm":
        return self + (-other)

    def scale(self, k: Fraction) -> "LogForm":
        return LogForm.make(self.rational * k,
                            {p: c * k for p, c in self.coeffs}, self.base)

    def is_rational(self) -> bool:
        return not self.coeffs

    def _log(self, p: int) -> str:
        return f"log2({p})" if self.base == 2 else f"ln({p})"

    def text(self) -> str:
        parts: List[str] = []
        if self.rational != 0 or not self.coeffs:
            parts.append(str(self.rational))
        for p, c in self.coeffs:
            mag = abs(c)
            term = self._log(p) if mag == 1 else f"{mag}*{self._log(p)}"
            if not parts:
                parts.append(term if c > 0 else f"-{term}")
            else:
                parts.append(("+ " if c > 0 else "- ") + term)
        return " ".join(parts)

    def expr(self) -> str:
        """The rendering :func:`real_expr.parse_expression` reads."""
        out = f"({self.rational.numerator}/{self.rational.denominator})"
        for p, c in self.coeffs:
            log = f"log(2, {p})" if self.base == 2 else f"ln({p})"
            out += f" + ({c.numerator}/{c.denominator})*{log}"
        return out


def log_of(q: Fraction, base: object = 2) -> LogForm:
    """``log_base(q)`` of a positive rational, exactly."""
    q = Fraction(q)
    if q <= 0:
        raise ValueError("log_of: a positive rational is needed")
    d: Dict[int, Fraction] = {}
    for p, k in factor(q.numerator).items():
        d[p] = d.get(p, 0) + k
    for p, k in factor(q.denominator).items():
        d[p] = d.get(p, 0) - k
    return LogForm.make(Fraction(0), d, base)


def entropy(masses: Sequence[Fraction], base: object = 2) -> LogForm:
    """``H = -sum m log m`` of a distribution with rational masses (zero
    masses contribute nothing, by ``0 log 0 = 0``)."""
    total = LogForm.make(Fraction(0), {}, base)
    for m in masses:
        m = Fraction(m)
        if m < 0:
            raise ValueError("entropy: a negative mass")
        if m:
            total = total - log_of(m, base).scale(m)
    return total


def log_identity_holds(terms: Sequence[Tuple[Fraction, Fraction]],
                       claim: LogForm) -> bool:
    """Check ``sum_i w_i * log2(q_i) == claim`` with integer arithmetic only.

    Both sides are logarithms of products of rational powers; raising to the
    least common denominator ``D`` of every exponent turns each into an
    integer-exponent product of rationals, compared exactly."""
    if claim.base != 2:
        raise ValueError("log_identity_holds: base 2 only")
    exps = [Fraction(w) for w, _ in terms] + [claim.rational] + \
        [c for _, c in claim.coeffs]
    D = 1
    for e in exps:
        D = D * e.denominator // gcd(D, e.denominator)
    lhs = Fraction(1)
    for w, q in terms:
        k = Fraction(w) * D
        lhs *= Fraction(q) ** int(k)
    rhs = Fraction(2) ** int(claim.rational * D)
    for p, c in claim.coeffs:
        rhs *= Fraction(p) ** int(c * D)
    return lhs == rhs


# ===========================================================================
# 4.  POLYNOMIALS
# ===========================================================================

Poly = Tuple[Fraction, ...]          # coefficients, constant term first


def _trim(p: Sequence[Fraction]) -> Poly:
    p = [Fraction(x) for x in p]
    while len(p) > 1 and p[-1] == 0:
        p.pop()
    return tuple(p)


def poly_mul(a: Sequence[Fraction], b: Sequence[Fraction]) -> Poly:
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += Fraction(x) * Fraction(y)
    return _trim(out)


def poly_add(a: Sequence[Fraction], b: Sequence[Fraction]) -> Poly:
    n = max(len(a), len(b))
    return _trim([(Fraction(a[i]) if i < len(a) else 0)
                  + (Fraction(b[i]) if i < len(b) else 0) for i in range(n)])


def poly_eval(p: Sequence[Fraction], x: Fraction) -> Fraction:
    acc = Fraction(0)
    for c in reversed(p):
        acc = acc * x + c
    return acc


def _poly_rem(a: Poly, b: Poly) -> Poly:
    a = list(a)
    while len(a) >= len(b) and any(a):
        k = a[-1] / b[-1]
        shift = len(a) - len(b)
        for i, c in enumerate(b):
            a[shift + i] -= k * c
        a = list(_trim(a))
        if len(a) < len(b) or (len(a) == 1 and a[0] == 0):
            break
    return _trim(a)


def _deriv(p: Poly) -> Poly:
    return _trim([i * c for i, c in enumerate(p)][1:] or [Fraction(0)])


def _sturm(p: Poly) -> List[Poly]:
    seq = [_trim(p), _deriv(_trim(p))]
    while len(seq[-1]) > 1 or seq[-1][0] != 0:
        r = _poly_rem(seq[-2], seq[-1])
        if len(r) == 1 and r[0] == 0:
            break
        seq.append(tuple(-c for c in r))
        if len(seq[-1]) == 1:
            break
    return seq


def _changes(seq: List[Poly], x: Fraction) -> int:
    signs = [s for s in (poly_eval(q, x) for q in seq) if s != 0]
    return sum(1 for u, v in zip(signs, signs[1:]) if (u > 0) != (v > 0))


def sturm_roots(p: Sequence[Fraction], lo: Fraction, hi: Fraction,
                width: Fraction = Fraction(1, 10 ** 12)
                ) -> List[Tuple[Fraction, Fraction]]:
    """Every real root of square-free ``p`` in ``(lo, hi]``, each isolated in
    an interval of width at most ``width`` (an exact root ``r`` is returned
    as ``(r, r)``)."""
    p = _trim(p)
    seq = _sturm(p)
    out: List[Tuple[Fraction, Fraction]] = []
    stack = [(Fraction(lo), Fraction(hi))]
    while stack:
        a, b = stack.pop()
        n = _changes(seq, a) - _changes(seq, b)
        if n == 0:
            continue
        if n == 1 and b - a <= width:
            out.append((a, b))
            continue
        m = (a + b) / 2
        if poly_eval(p, m) == 0 and n == 1:
            out.append((m, m))
            continue
        stack.append((m, b))
        stack.append((a, m))
    return sorted(out)
