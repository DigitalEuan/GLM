"""``glm_universal.reasoning.sign_factor`` -- deciding the sign of a
polynomial in letters by factorisation (Phase 109).

Why it exists
-------------
The cubic route (``reasoning/routes.py``, decision point ``cubic.letters``)
picks Viete, Cardano or a split into cases from the sign of the cubic's
discriminant.  Until Phase 109 that sign was read off the *surface* of the
expanded polynomial: plainly non-negative when every term is an even power
with a positive coefficient, plainly non-positive when minus it is.  An
expanded square fails that test at once -- ``(a - b)^2 = a^2 - 2ab + b^2``
has a negative term -- so a discriminant such as ``(a - b)^6 (c^2 + 1)``,
positive for every real ``a, b, c``, was reported undecided and answered as
two cases, one of which no value of the letters reaches.

What it does
------------
:func:`square_free` splits a polynomial into ``c * prod f_i^e_i`` with a
rational constant ``c``, the monomial content as single-letter factors, and
square-free, pairwise coprime ``f_i`` (Yun's algorithm, variable by
variable, with the package's exact multivariate gcd).  :func:`decided_sign`
then reads the sign off the factors: a factor to an even power is ``>= 0``;
a factor to an odd power must pass the surface test itself, one way or the
other.  The answer is ``+1`` (the polynomial is ``>= 0`` for every real value
of the letters), ``-1`` (``<= 0``) or ``None`` (not decided) -- never a guess.

It is still a sufficient test, not a decision procedure: a factor such as
``a^2 - a + 1`` (positive, but not plainly so) leaves the sign undecided.
``RequestProject/GLM/SignFactor.lean`` proves the rule it applies.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Optional, Tuple

from .symbolic import Poly, divide_exact, poly_gcd, to_text, RF, _dpoly

__all__ = ["square_free", "decided_sign", "surface_sign", "factored_text",
           "MAX_TERMS"]

#: Above this many terms the factorisation is not attempted: the gcds it
#: runs are exact and recursive, and a discriminant this large is not one a
#: reader would check by hand either.  The surface test still runs.
MAX_TERMS = 400


def surface_sign(p: Poly) -> Optional[int]:
    """``+1`` when every term is an even power with a positive coefficient,
    ``-1`` when that holds of ``-p``, ``None`` otherwise (``p`` nonzero)."""
    if p.is_zero():
        return None

    def plain(q: Poly) -> bool:
        return all(c > 0 and all(e % 2 == 0 for _, e in m)
                   for m, c in q.t.items())

    if plain(p):
        return 1
    if plain(-p):
        return -1
    return None


def _yun(f: Poly, v: str) -> List[Tuple[Poly, int]]:
    """Square-free decomposition of ``f``, primitive in ``v`` and of positive
    degree in it: ``[(a_i, i)]`` with ``f = const * prod a_i^i``."""
    out: List[Tuple[Poly, int]] = []
    df = _dpoly(f, v)
    a0 = poly_gcd(f, df)
    b = divide_exact(f, a0)
    c = divide_exact(df, a0)
    if b is None or c is None:            # pragma: no cover - gcd divides
        return [(f, 1)]
    d = c - _dpoly(b, v)
    i = 1
    while not b.is_const():
        a = poly_gcd(b, d)
        if not a.is_const():
            out.append((a, i))
        nb = divide_exact(b, a)
        nc = divide_exact(d, a)
        if nb is None or nc is None:      # pragma: no cover - gcd divides
            out.append((b, i))
            break
        b, c = nb, nc
        d = c - _dpoly(b, v)
        i += 1
    return out


def square_free(p: Poly) -> Tuple[Fraction, List[Tuple[Poly, int]]]:
    """``(c, [(f, e), ...])`` with ``p == c * prod f^e``.

    Single letters come first (the monomial content), then the square-free
    parts found variable by variable.  Raises ``ValueError`` for the zero
    polynomial.
    """
    if p.is_zero():
        raise ValueError("the zero polynomial has no sign")
    factors: List[Tuple[Poly, int]] = []
    mono = dict(p.monomial_content())
    rest = p
    if mono:
        for v, e in sorted(mono.items()):
            factors.append((Poly.var(v), e))
        den = Poly({tuple(sorted(mono.items())): Fraction(1)})
        rest = divide_exact(p, den)
    pending = [rest]
    while pending:
        q = pending.pop()
        if q.is_const():
            continue
        v = max(q.vars())
        cont = Poly()
        for coeff in q.coeffs(v).values():
            cont = poly_gcd(cont, coeff)
            if cont.is_const():
                break
        if not cont.is_const():
            prim = divide_exact(q, cont)
            pending.append(cont)
        else:
            prim = q
        if v in prim.vars():
            factors.extend(_yun(prim, v))
        else:                              # pragma: no cover - v is in q
            pending.append(prim)
    factors = [(_primitive(f), e) for f, e in factors]
    product = Poly.const(1)
    for f, e in factors:
        product = product * f ** e
    quotient = divide_exact(p, product)
    if quotient is None or not quotient.is_const():   # pragma: no cover
        raise ValueError("the factors do not multiply back to the polynomial")
    return quotient.const_value(), factors


def _primitive(f: Poly) -> Poly:
    """``f`` scaled to coprime integer coefficients, the leading one
    positive (the constant this moves is recovered by the caller)."""
    from math import gcd as _gcd
    lcm = 1
    for c in f.t.values():
        lcm = lcm * c.denominator // _gcd(lcm, c.denominator)
    ints = [int(c * lcm) for c in f.t.values()]
    g = 0
    for n in ints:
        g = _gcd(g, abs(n))
    scale = Fraction(lcm, g or 1)
    if f.leading()[1] < 0:
        scale = -scale
    return f.scale(scale)


def decided_sign(p: Poly) -> Tuple[Optional[int], str]:
    """The sign of ``p`` for every real value of its letters, and why.

    ``(+1, why)``: ``p >= 0`` everywhere; ``(-1, why)``: ``p <= 0``
    everywhere; ``(None, why)``: not decided by the surface of the
    polynomial nor by the surfaces of its square-free factors.
    """
    s = surface_sign(p)
    if s is not None:
        return s, "plainly " + ("non-negative" if s > 0 else "non-positive")
    if len(p.t) > MAX_TERMS:
        return None, f"not factorised (over {MAX_TERMS} terms)"
    try:
        c, factors = square_free(p)
    except ValueError:
        return None, "not factorised"
    sign = 1 if c > 0 else -1
    for f, e in factors:
        if e % 2 == 0:
            continue
        fs = surface_sign(f)
        if fs is None:
            return None, (f"its factor {to_text(RF(f))} has no evident "
                          f"sign: {factored_text(c, factors)}")
        sign *= fs
    return sign, ("by factorisation, " + factored_text(c, factors) + ", " +
                  ("non-negative" if sign > 0 else "non-positive") +
                  " for every real value of the letters")


def factored_text(c: Fraction, factors: List[Tuple[Poly, int]]) -> str:
    """``c*(f1)^e1*(f2)^e2...`` as a reader would write it."""
    parts = []
    for f, e in factors:
        body = to_text(RF(f))
        if len(f.t) > 1:
            body = f"({body})"
        parts.append(body if e == 1 else f"{body}^{e}")
    head = "" if c == 1 else ("-" if c == -1 else
                              (f"{c}*" if c.denominator == 1 and c > 0
                               else f"({c})*"))
    if head == "-" and parts:
        return "-" + "*".join(parts)
    return head + "*".join(parts) if parts else str(c)
