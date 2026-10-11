"""``glm_universal.reasoning.symbolic_algebraic`` -- exact real algebraic
numbers for the branch layer (Phase 104,
``studies/CUBIC_RADICAL_STUDY.md``).

Why it exists
-------------
Phase 103's branch layer solved an equation left in one unknown only when it
was linear or quadratic.  A cubic with no rational root was refused
``NONLINEAR``, and that was most of what its planted battery refused: two
conics through a rational point leave a cubic.  A cubic with three real roots
has no expression in real radicals at all (the *casus irreducibilis*), so the
honest exact object is not a formula but a **real algebraic number**: an
irreducible polynomial over the rationals together with an interval with
rational ends that holds exactly one of its roots.  Arithmetic on such a
number is arithmetic modulo its polynomial, which is a field because the
polynomial is irreducible, so a value is zero exactly when its remainder is.

What it holds
-------------
Univariate polynomials over :class:`fractions.Fraction`, as coefficient
lists from the constant term up, and on them:

* :func:`sturm_chain`, :func:`count_roots`, :func:`isolate_real_roots` --
  Sturm's theorem: the number of distinct real roots of a squarefree
  polynomial in ``(a, b]`` is the drop in sign changes of its Sturm chain;
  bisection then gives one interval per real root.
* :func:`factor_rational` -- the irreducible factors over the rationals of a
  polynomial with no rational root (degree up to 6 here, up to 24 since
  Phase 112 through :mod:`.symbolic_factor`): the degrees a factor
  could have are read off its factorisations modulo small primes (distinct-
  degree factorisation over F_p); when a split is still possible, a factor of
  that degree is searched for by Kronecker's interpolation.  Past degree 6,
  or when Kronecker's search runs out of budget, Zassenhaus's algorithm
  (:mod:`glm_universal.reasoning.symbolic_factor`, Phase 112) is used.
  Undecided cases return ``None`` and the caller refuses.
* :func:`refine`, :func:`decimal_text`, :func:`sign_at` -- the sign of a
  polynomial expression in the root, decided by exact interval arithmetic on
  a shrinking interval (it ends because a nonzero element of the field is
  nonzero at the root).

No float is used, and nothing is looked up.
``RequestProject/GLM/CubicRadicals.lean`` proves that a cubic with no
rational root is irreducible and that a sign change brackets a root.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from math import gcd
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = ["UPoly", "trim", "pdivmod", "pgcd", "pmul", "psub", "padd",
           "pderiv", "peval", "sturm_chain", "count_roots",
           "isolate_real_roots", "refine", "decimal_text", "factor_rational",
           "possible_factor_degrees", "sign_at", "powers_mod",
           "MAX_FACTOR_DEGREE"]

UPoly = List[Fraction]

#: Above this degree Kronecker's search is not tried; since Phase 112 such a
#: polynomial is factored by Zassenhaus's algorithm
#: (:mod:`glm_universal.reasoning.symbolic_factor`, up to its own caps), and
#: only past those does the caller refuse.
MAX_FACTOR_DEGREE = 6
#: Interpolations Kronecker's search may try before giving up.
KRONECKER_BUDGET = 200000


# ===========================================================================
# 1.  ARITHMETIC ON COEFFICIENT LISTS
# ===========================================================================

def trim(p: Sequence) -> UPoly:
    out = [Fraction(c) for c in p]
    while out and out[-1] == 0:
        out.pop()
    return out


def padd(a: UPoly, b: UPoly) -> UPoly:
    n = max(len(a), len(b))
    return trim([(a[i] if i < len(a) else 0) + (b[i] if i < len(b) else 0)
                 for i in range(n)])


def psub(a: UPoly, b: UPoly) -> UPoly:
    return padd(a, [-c for c in b])


def pmul(a: UPoly, b: UPoly) -> UPoly:
    if not a or not b:
        return []
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                out[i + j] += x * y
    return trim(out)


def pdivmod(a: UPoly, b: UPoly) -> Tuple[UPoly, UPoly]:
    a, b = trim(a), trim(b)
    if not b:
        raise ZeroDivisionError("division by the zero polynomial")
    q = [Fraction(0)] * max(len(a) - len(b) + 1, 0)
    r = list(a)
    lb = b[-1]
    while len(r) >= len(b) and r:
        c = r[-1] / lb
        s = len(r) - len(b)
        q[s] = c
        for i, y in enumerate(b):
            r[s + i] -= c * y
        r = trim(r)
    return trim(q), r


def monic(p: UPoly) -> UPoly:
    p = trim(p)
    return [c / p[-1] for c in p] if p else p


def pgcd(a: UPoly, b: UPoly) -> UPoly:
    a, b = trim(a), trim(b)
    while b:
        a, b = b, pdivmod(a, b)[1]
    return monic(a)


def pderiv(p: UPoly) -> UPoly:
    return trim([i * p[i] for i in range(1, len(p))])


def peval(p: UPoly, x: Fraction) -> Fraction:
    v = Fraction(0)
    for c in reversed(p):
        v = v * x + c
    return v


def primitive_int(p: UPoly) -> List[int]:
    """The integer multiple of ``p`` with content 1 and positive leading
    coefficient."""
    p = trim(p)
    den = 1
    for c in p:
        den = den * c.denominator // gcd(den, c.denominator)
    ints = [int(c * den) for c in p]
    g = 0
    for c in ints:
        g = gcd(g, c)
    ints = [c // g for c in ints]
    if ints[-1] < 0:
        ints = [-c for c in ints]
    return ints


# ===========================================================================
# 2.  STURM'S THEOREM AND REAL-ROOT ISOLATION
# ===========================================================================

def sturm_chain(p: UPoly) -> List[UPoly]:
    chain = [trim(p), pderiv(p)]
    while chain[-1]:
        r = pdivmod(chain[-2], chain[-1])[1]
        if not r:
            break
        chain.append([-c for c in r])
    return chain


def _variations(chain: List[UPoly], x: Fraction) -> int:
    signs = [peval(q, x) for q in chain]
    signs = [s for s in signs if s != 0]
    return sum(1 for a, b in zip(signs, signs[1:]) if (a > 0) != (b > 0))


def count_roots(chain: List[UPoly], a: Fraction, b: Fraction) -> int:
    """Distinct real roots of a squarefree ``chain[0]`` in ``(a, b]``."""
    return _variations(chain, a) - _variations(chain, b)


def root_bound(p: UPoly) -> Fraction:
    """Cauchy's bound: every real root has absolute value below it."""
    p = trim(p)
    return 1 + max(abs(c / p[-1]) for c in p[:-1]) if len(p) > 1 \
        else Fraction(1)


def isolate_real_roots(p: UPoly) -> List[Tuple[Fraction, Fraction]]:
    """One interval ``(lo, hi)`` per real root of the squarefree ``p``,
    increasing, with ``p(lo)`` and ``p(hi)`` nonzero and of opposite signs
    and exactly one root inside."""
    p = trim(p)
    chain = sturm_chain(p)
    b = root_bound(p)
    out: List[Tuple[Fraction, Fraction]] = []
    todo = [(-b, b)]
    while todo:
        lo, hi = todo.pop()
        n = count_roots(chain, lo, hi)
        if n == 0:
            continue
        if n == 1 and peval(p, hi) != 0 and peval(p, lo) != 0:
            out.append((lo, hi))
            continue
        mid = (lo + hi) / 2
        k = 1
        while peval(p, mid) == 0:
            # never a root at a cut: move the cut off it
            mid = (lo + hi) / 2 + (hi - lo) / (4 * (k + 2))
            k += 1
        todo.append((lo, mid))
        todo.append((mid, hi))
    return sorted(out)


def refine(p: UPoly, lo: Fraction, hi: Fraction, width: Fraction
           ) -> Tuple[Fraction, Fraction]:
    """Bisect ``(lo, hi)`` (a sign change of ``p``) below ``width``."""
    slo = peval(p, lo) > 0
    while hi - lo > width:
        mid = (lo + hi) / 2
        v = peval(p, mid)
        if v == 0:
            e = (hi - lo) / 8
            return mid - e, mid + e
        if (v > 0) == slo:
            lo = mid
        else:
            hi = mid
    return lo, hi


def decimal_text(p: UPoly, lo: Fraction, hi: Fraction, digits: int = 6
                 ) -> str:
    """The root as a decimal to ``digits`` places (from an exact interval
    narrower than half a unit of the last place)."""
    w = Fraction(1, 10 ** digits) / 4
    lo, hi = refine(p, lo, hi, w)
    mid = (lo + hi) / 2
    scaled = round(mid * 10 ** digits)
    sign = "-" if scaled < 0 else ""
    s = str(abs(scaled)).rjust(digits + 1, "0")
    return f"{sign}{s[:-digits]}.{s[-digits:]}"


# ===========================================================================
# 3.  FACTORISATION OVER THE RATIONALS (small degree)
# ===========================================================================

def _pm_trim(a: List[int]) -> List[int]:
    while a and a[-1] == 0:
        a.pop()
    return a


def _pm_mod(a: List[int], b: List[int], m: int) -> List[int]:
    a = [x % m for x in a]
    _pm_trim(a)
    inv = pow(b[-1], m - 2, m)
    while len(a) >= len(b) and a:
        c = a[-1] * inv % m
        s = len(a) - len(b)
        for i, y in enumerate(b):
            a[s + i] = (a[s + i] - c * y) % m
        _pm_trim(a)
    return a


def _pm_mul(a: List[int], b: List[int], m: int) -> List[int]:
    if not a or not b:
        return []
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] = (out[i + j] + x * y) % m
    return _pm_trim(out)


def _pm_gcd(a: List[int], b: List[int], m: int) -> List[int]:
    a, b = _pm_trim([x % m for x in a]), _pm_trim([x % m for x in b])
    while b:
        a, b = b, _pm_mod(a, b, m)
    if a:
        inv = pow(a[-1], m - 2, m)
        a = [x * inv % m for x in a]
    return a


def _pm_div(a: List[int], b: List[int], m: int) -> List[int]:
    a = [x % m for x in a]
    _pm_trim(a)
    inv = pow(b[-1], m - 2, m)
    q = [0] * max(len(a) - len(b) + 1, 0)
    while len(a) >= len(b) and a:
        c = a[-1] * inv % m
        s = len(a) - len(b)
        q[s] = c
        for i, y in enumerate(b):
            a[s + i] = (a[s + i] - c * y) % m
        _pm_trim(a)
    return _pm_trim(q)


def _pm_powmod(base: List[int], e: int, f: List[int], m: int) -> List[int]:
    out = [1]
    b = _pm_mod(base, f, m)
    while e:
        if e & 1:
            out = _pm_mod(_pm_mul(out, b, m), f, m)
        b = _pm_mod(_pm_mul(b, b, m), f, m)
        e >>= 1
    return out


def _ddf_degrees(ints: List[int], m: int) -> Optional[List[int]]:
    """The degrees of the irreducible factors of ``ints`` modulo the prime
    ``m`` (distinct-degree factorisation), or ``None`` if ``m`` divides the
    leading coefficient or the reduction is not squarefree."""
    f = [x % m for x in ints]
    _pm_trim(f)
    if len(f) != len(ints):
        return None
    df = _pm_trim([(i * ints[i]) % m for i in range(1, len(ints))])
    if len(_pm_gcd(f, df, m)) > 1:
        return None
    degs: List[int] = []
    h = [0, 1]
    d = 0
    while len(f) > 1:
        d += 1
        if 2 * d > len(f) - 1:
            degs.append(len(f) - 1)
            break
        h = _pm_powmod(h, m, f, m)
        hx = list(h) + [0] * max(0, 2 - len(h))
        hx[1] = (hx[1] - 1) % m
        g = _pm_gcd(_pm_trim(hx), f, m)
        if len(g) > 1:
            degs.extend([d] * ((len(g) - 1) // d))
            f = _pm_div(f, g, m)
            h = _pm_mod(h, f, m)
    return degs


def _subset_sums(degs: List[int]) -> set:
    sums = {0}
    for d in degs:
        sums |= {s + d for s in sums}
    return sums


_PRIMES = (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61,
           67, 71, 73, 79, 83, 89, 97)


def possible_factor_degrees(p: UPoly) -> set:
    """Degrees ``1 <= k < deg p`` a factor over the rationals could have,
    read off the factorisations modulo the primes of :data:`_PRIMES`."""
    ints = primitive_int(p)
    n = len(ints) - 1
    possible = set(range(1, n))
    for m in _PRIMES:
        degs = _ddf_degrees(ints, m)
        if degs is None:
            continue
        possible &= _subset_sums(degs)
        if not possible:
            break
    return possible


def _divisors(n: int) -> List[int]:
    n = abs(n)
    out = []
    i = 1
    while i * i <= n:
        if n % i == 0:
            out.append(i)
            if i * i != n:
                out.append(n // i)
        i += 1
    return sorted(out)


def _interpolate(xs: List[int], ys: List[int]) -> UPoly:
    out: UPoly = []
    for i, (xi, yi) in enumerate(zip(xs, ys)):
        term: UPoly = [Fraction(yi)]
        for j, xj in enumerate(xs):
            if j != i:
                term = pmul(term, [Fraction(-xj, xi - xj),
                                   Fraction(1, xi - xj)])
        out = padd(out, term)
    return out


def _kronecker(p: UPoly, k: int) -> Optional[UPoly]:
    """A factor of degree ``k`` of ``p`` over the rationals, ``[]`` if there
    is none, ``None`` if the search ran out of budget."""
    ints = primitive_int(p)
    pts = []
    for x in sorted(range(-12, 13), key=abs):
        v = sum(c * x ** i for i, c in enumerate(ints))
        if v != 0:
            pts.append((len(_divisors(v)), x, v))
    pts.sort()
    chosen = pts[:k + 1]
    xs = [x for _, x, _ in chosen]
    divs = [[d for d in _divisors(v)] for _, _, v in chosen]
    work = 1
    for d in divs:
        work *= 2 * len(d)
    if work > KRONECKER_BUDGET:
        return None
    pp = [Fraction(c) for c in ints]
    for combo in product(*divs):
        for signs in product((1, -1), repeat=k):
            ys = [combo[0]] + [s * c for s, c in zip(signs, combo[1:])]
            q = _interpolate(xs, ys)
            if len(q) - 1 != k:
                continue
            if any(c.denominator != 1 for c in q):
                continue
            quo, rem = pdivmod(pp, q)
            if not rem:
                return monic(q)
    return []


def factor_rational(p: UPoly) -> Optional[List[UPoly]]:
    """The monic irreducible factors over the rationals of a squarefree
    ``p`` with no rational root (degree at most :data:`MAX_FACTOR_DEGREE`),
    or ``None`` when that could not be decided."""
    p = monic(p)
    n = len(p) - 1
    if n <= 3:
        return [p]
    if n > MAX_FACTOR_DEGREE:
        # Phase 112: past Kronecker's reach, Zassenhaus's algorithm
        # (modular factoring, Hensel lifting, recombination).
        return _zassenhaus_factors(p)
    possible = {k for k in possible_factor_degrees(p) if 2 <= k <= n - 2}
    for k in sorted(possible):
        if 2 * k > n:
            break
        q = _kronecker(p, k)
        if q is None:
            return _zassenhaus_factors(p)
        if q:
            rest = pdivmod(p, q)[0]
            a, b = factor_rational(q), factor_rational(rest)
            if a is None or b is None:
                return None
            return a + b
    return [p]


def _zassenhaus_factors(p: UPoly) -> Optional[List[UPoly]]:
    """The monic irreducible factors of ``p`` by
    :func:`glm_universal.reasoning.symbolic_factor.zassenhaus` (Phase 112),
    or ``None`` over its caps."""
    from .symbolic_factor import as_fraction_factors
    return as_fraction_factors(p)


# ===========================================================================
# 4.  ARITHMETIC IN THE FIELD OF ONE ROOT
# ===========================================================================

def powers_mod(m: UPoly, top: int) -> List[UPoly]:
    """``t^e mod m`` for ``e = 0 .. top`` (``m`` monic)."""
    out: List[UPoly] = []
    cur: UPoly = [Fraction(1)]
    for _ in range(top + 1):
        out.append(cur)
        cur = pdivmod([Fraction(0)] + cur, m)[1]
    return out


def _interval_eval(e: UPoly, lo: Fraction, hi: Fraction
                   ) -> Tuple[Fraction, Fraction]:
    a = b = Fraction(0)
    for c in reversed(e):
        prods = (a * lo, a * hi, b * lo, b * hi)
        a, b = min(prods) + c, max(prods) + c
    return a, b


def sign_at(e: UPoly, m: UPoly, lo: Fraction, hi: Fraction) -> int:
    """The sign of ``e(r)`` at the root ``r`` of the irreducible ``m`` in
    ``(lo, hi)``: ``e`` is reduced modulo ``m``; if the remainder is zero the
    sign is 0, otherwise the interval is halved until ``e`` keeps one sign
    on it."""
    e = pdivmod(e, m)[1]
    if not e:
        return 0
    for _ in range(4000):
        a, b = _interval_eval(e, lo, hi)
        if a > 0:
            return 1
        if b < 0:
            return -1
        lo, hi = refine(m, lo, hi, (hi - lo) / 2)
    raise ArithmeticError("sign not decided")
