"""``glm_universal.reasoning.symbolic_factor`` -- factoring over the
rationals past degree 6 (Phase 112, ``studies/QUINTIC_RADICAL_STUDY.md``).

Why it exists
-------------
Phase 104's :func:`~glm_universal.reasoning.symbolic_algebraic.factor_rational`
reads the possible factor degrees off factorisations modulo small primes and
then searches for a factor by Kronecker's interpolation.  Kronecker's search
grows with the product of the divisor counts of ``k + 1`` values, so the layer
stopped at degree 6 and refused anything higher (``x^7 - 3*x + 1 = 0`` was
refused ``NONLINEAR``).  This module is the standard algorithm that does not
have that growth, Zassenhaus's:

1. pick a prime ``p`` not dividing the leading coefficient for which the
   polynomial stays squarefree, the one with the fewest factors among the
   first few;
2. factor it completely modulo ``p`` (distinct-degree factorisation, then
   Cantor and Zassenhaus's equal-degree splitting, its trials drawn from a
   fixed deterministic sequence so the answer is the same every run);
3. lift that factorisation to ``p^k`` with Hensel's lemma, ``p^k`` past twice
   the Mignotte bound on the coefficients of any factor;
4. recombine: every subset of the lifted factors, smallest first, times the
   leading coefficient, reduced to the symmetric range, is tried as a factor
   by exact division over the integers.

Step 4 is exponential in the number of factors modulo ``p``, not in the
degree; it is capped by :data:`MAX_MODULAR_FACTORS` and an over-cap case
returns ``None`` (the caller refuses).  Every factor returned has been checked
by exact division, and the last one is irreducible because no subset of its
modular factors divides it, so a wrong factorisation cannot be returned --
only an undecided one.

No float and nothing looked up; the equal-degree splitting draws its
trial polynomials from the package's deterministic generator
(:class:`glm_universal.reasoning.symbolic.Lcg`), never from ``random``.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from math import gcd, isqrt
from typing import List, Optional, Tuple

from .symbolic import Lcg

__all__ = ["zassenhaus", "factor_mod_p", "as_fraction_factors",
           "radical_free", "certify_numeric", "RADICAL_FREE_LEAN",
           "frobenius_degrees", "frobenius_pattern", "radical_free_frobenius",
           "non_affine_power",
           "certify_numeric_any", "FROBENIUS_LEAN", "FROBENIUS_PRIME_BOUND",
           "jordan_power", "is_long_cycle", "primitive_pattern",
           "radical_free_primitive", "radical_free_galois", "PRIMITIVE_LEAN",
           "decompose", "decompositions", "compose", "radical_free_composed",
           "COMPOSED_LEAN", "is_prime_power", "long_cycle_prime",
           "radical_free_degree", "DEGREE_LEAN",
           "MAX_MODULAR_FACTORS", "MAX_DEGREE"]

#: Above this many factors modulo ``p`` the recombination is not tried.
MAX_MODULAR_FACTORS = 16
#: Above this degree nothing is factored, and the caller refuses.
MAX_DEGREE = 24

_PRIMES = (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61,
           67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113)


# -- polynomials modulo a prime, coefficient lists from the constant up -----

def _trim(a: List[int]) -> List[int]:
    while a and a[-1] == 0:
        a.pop()
    return a


def _mod(a: List[int], b: List[int], m: int) -> List[int]:
    a = _trim([x % m for x in a])
    inv = pow(b[-1], -1, m)
    while len(a) >= len(b) and a:
        c = a[-1] * inv % m
        s = len(a) - len(b)
        for i, y in enumerate(b):
            a[s + i] = (a[s + i] - c * y) % m
        _trim(a)
    return a


def _divmod(a: List[int], b: List[int], m: int
            ) -> Tuple[List[int], List[int]]:
    a = _trim([x % m for x in a])
    inv = pow(b[-1], -1, m)
    q = [0] * max(len(a) - len(b) + 1, 0)
    while len(a) >= len(b) and a:
        c = a[-1] * inv % m
        s = len(a) - len(b)
        q[s] = c
        for i, y in enumerate(b):
            a[s + i] = (a[s + i] - c * y) % m
        _trim(a)
    return _trim(q), a


def _mul(a: List[int], b: List[int], m: int) -> List[int]:
    if not a or not b:
        return []
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                out[i + j] += x * y
    return _trim([x % m for x in out])


def _sub(a: List[int], b: List[int], m: int) -> List[int]:
    n = max(len(a), len(b))
    return _trim([((a[i] if i < len(a) else 0) -
                   (b[i] if i < len(b) else 0)) % m for i in range(n)])


def _add(a: List[int], b: List[int], m: int) -> List[int]:
    n = max(len(a), len(b))
    return _trim([((a[i] if i < len(a) else 0) +
                   (b[i] if i < len(b) else 0)) % m for i in range(n)])


def _monic(a: List[int], m: int) -> List[int]:
    inv = pow(a[-1], -1, m)
    return [x * inv % m for x in a]


def _gcd(a: List[int], b: List[int], p: int) -> List[int]:
    a, b = _trim([x % p for x in a]), _trim([x % p for x in b])
    while b:
        a, b = b, _mod(a, b, p)
    return _monic(a, p) if a else a


def _xgcd(a: List[int], b: List[int], p: int
          ) -> Tuple[List[int], List[int], List[int]]:
    """``(g, s, t)`` with ``s a + t b = g`` monic, modulo the prime ``p``."""
    r0, r1 = _trim([x % p for x in a]), _trim([x % p for x in b])
    s0, s1, t0, t1 = [1], [], [], [1]
    while r1:
        q, r = _divmod(r0, r1, p)
        r0, r1 = r1, r
        s0, s1 = s1, _sub(s0, _mul(q, s1, p), p)
        t0, t1 = t1, _sub(t0, _mul(q, t1, p), p)
    inv = pow(r0[-1], -1, p)
    return ([x * inv % p for x in r0], [x * inv % p for x in s0],
            [x * inv % p for x in t0])


def _powmod(base: List[int], e: int, f: List[int], p: int) -> List[int]:
    out = [1]
    b = _mod(base, f, p)
    while e:
        if e & 1:
            out = _mod(_mul(out, b, p), f, p)
        b = _mod(_mul(b, b, p), f, p)
        e >>= 1
    return out


def _deriv(a: List[int], p: int) -> List[int]:
    return _trim([(i * a[i]) % p for i in range(1, len(a))])


def _squarefree_mod(f: List[int], p: int) -> bool:
    fp = _trim([x % p for x in f])
    if len(fp) != len(f):
        return False
    return len(_gcd(fp, _deriv(fp, p), p)) == 1


def _ddf(f: List[int], p: int) -> List[Tuple[int, List[int]]]:
    """Distinct-degree factorisation of a monic squarefree ``f`` modulo
    ``p``: ``(d, product of its irreducible factors of degree d)``."""
    out = []
    h = [0, 1]
    d = 0
    f = list(f)
    while len(f) > 1:
        d += 1
        if 2 * d > len(f) - 1:
            out.append((len(f) - 1, f))
            break
        h = _powmod(h, p, f, p)
        g = _gcd(_sub(h, [0, 1], p), f, p)
        if len(g) > 1:
            out.append((d, g))
            f = _divmod(f, g, p)[0]
            h = _mod(h, f, p)
    return out


def _edf(f: List[int], d: int, p: int, rng: Lcg) -> List[List[int]]:
    """Cantor and Zassenhaus's equal-degree splitting of a monic
    squarefree ``f`` all of whose factors modulo the odd prime ``p`` have
    degree ``d``."""
    n = len(f) - 1
    if n == d:
        return [f]
    e = (p ** d - 1) // 2
    while True:
        a = _trim([rng.next() % p for _ in range(n)])
        if len(a) < 2:
            continue
        g = _gcd(a, f, p)
        if 1 < len(g) < len(f):
            break
        b = _sub(_powmod(a, e, f, p), [1], p)
        g = _gcd(b, f, p)
        if 1 < len(g) < len(f):
            break
    return (_edf(g, d, p, rng) +
            _edf(_divmod(f, g, p)[0], d, p, rng))


def factor_mod_p(f: List[int], p: int, seed: int = 0) -> List[List[int]]:
    """The monic irreducible factors modulo the odd prime ``p`` of an
    integer polynomial squarefree modulo ``p`` (``p`` not dividing its
    leading coefficient), sorted."""
    rng = Lcg(20260 + seed)
    fm = _monic(_trim([x % p for x in f]), p)
    out: List[List[int]] = []
    for d, g in _ddf(fm, p):
        out.extend(_edf(g, d, p, rng))
    return sorted(out, key=lambda q: (len(q), q))


# -- Hensel lifting ----------------------------------------------------------

def _hensel_pair(F: List[int], g: List[int], h: List[int], p: int, k: int
                 ) -> Tuple[List[int], List[int]]:
    """Lift ``F = g h`` modulo ``p`` (``g``, ``h`` monic and coprime modulo
    ``p``, ``F`` monic modulo ``p^k``) to ``F = G H`` modulo ``p^k``."""
    _, s, t = _xgcd(g, h, p)
    M = p ** k
    m = p
    G, H = list(g), list(h)
    for _ in range(1, k):
        diff = _sub(F, _mul(G, H, M), M)
        e = [(x // m) % p for x in diff]
        _trim(e)
        if e:
            q, r = _divmod(_mul(t, e, p), g, p)          # t e = q g + r
            dg = r
            dh = _add(_mul(s, e, p), _mul(q, h, p), p)   # s e + q h
            G = _add(G, [x * m for x in dg], M)
            H = _add(H, [x * m for x in dh], M)
        m *= p
    return G, H


def _hensel_all(F: List[int], facs: List[List[int]], p: int, k: int
                ) -> List[List[int]]:
    """Lift a complete factorisation modulo ``p`` of the monic-modulo-``p^k``
    ``F`` to one modulo ``p^k``."""
    if len(facs) == 1:
        return [_monic(_trim([x % p ** k for x in F]), p ** k)]
    g = facs[0]
    h = [1]
    for q in facs[1:]:
        h = _mul(h, q, p)
    G, H = _hensel_pair(F, g, h, p, k)
    return [G] + _hensel_all(H, facs[1:], p, k)


# -- the integer side --------------------------------------------------------

def _int_divmod(a: List[int], b: List[int]) -> Optional[List[int]]:
    """``a / b`` over the integers when it is exact, else ``None``."""
    a = list(a)
    q = [0] * max(len(a) - len(b) + 1, 0)
    lb = b[-1]
    while len(a) >= len(b) and a:
        c, r = divmod(a[-1], lb)
        if r:
            return None
        s = len(a) - len(b)
        q[s] = c
        for i, y in enumerate(b):
            a[s + i] -= c * y
        _trim(a)
    return _trim(q) if not a else None


def _primitive(a: List[int]) -> List[int]:
    g = 0
    for x in a:
        g = gcd(g, x)
    a = [x // g for x in a]
    return [-x for x in a] if a[-1] < 0 else a


def _mignotte(f: List[int]) -> int:
    """A bound on the absolute value of every coefficient of every factor
    of ``f`` over the integers: ``2^n * sqrt(n + 1) * max|a_i| * |a_n|``
    (Mignotte), rounded up."""
    n = len(f) - 1
    norm = (isqrt((n + 1) * max(abs(x) for x in f) ** 2) + 1)
    return (2 ** n) * norm * abs(f[-1])


def _choose_prime(f: List[int]) -> Optional[Tuple[int, List[List[int]]]]:
    best = None
    tried = 0
    for p in _PRIMES:
        if f[-1] % p == 0 or not _squarefree_mod(f, p):
            continue
        facs = factor_mod_p(f, p)
        if best is None or len(facs) < len(best[1]):
            best = (p, facs)
        tried += 1
        if len(facs) == 1 or tried >= 5:
            break
    return best


def zassenhaus(ints: List[int]) -> Optional[List[List[int]]]:
    """The irreducible factors over the integers of a squarefree primitive
    integer polynomial with positive leading coefficient (coefficients from
    the constant up), each primitive with positive leading coefficient; or
    ``None`` when the degree or the number of modular factors is over its
    cap."""
    f = _primitive(list(ints))
    n = len(f) - 1
    if n <= 1:
        return [f]
    if n > MAX_DEGREE:
        return None
    chosen = _choose_prime(f)
    if chosen is None:
        return None
    p, facs = chosen
    if len(facs) == 1:
        return [f]
    if len(facs) > MAX_MODULAR_FACTORS:
        return None
    bound = 2 * _mignotte(f) + 1
    k = 1
    while p ** k <= bound:
        k += 1
    M = p ** k
    F = [x * pow(f[-1], -1, M) % M for x in f]
    lifted = _hensel_all(F, facs, p, k)
    out: List[List[int]] = []
    rest = list(range(len(lifted)))
    s = 1
    while 2 * s <= len(rest):
        found = False
        for sub in combinations(rest, s):
            g = [f[-1] % M]
            for i in sub:
                g = _mul(g, lifted[i], M)
            g = [x - M if x > M // 2 else x for x in g]
            g = _primitive(_trim(g))
            q = _int_divmod(f, g)
            if q is None:
                continue
            out.append(g)
            f = _primitive(q)
            rest = [i for i in rest if i not in sub]
            found = True
            break
        if not found:
            s += 1
    out.append(f)
    return sorted(out, key=lambda q: (len(q), q))


def as_fraction_factors(p: List[Fraction]) -> Optional[List[List[Fraction]]]:
    """:func:`zassenhaus` for a polynomial over the rationals: its monic
    irreducible factors, or ``None``."""
    den = 1
    for c in p:
        den = den * c.denominator // gcd(den, c.denominator)
    ints = [int(c * den) for c in p]
    got = zassenhaus(ints)
    if got is None:
        return None
    return [[Fraction(c, g[-1]) for c in g] for g in got]


# -- no root in radicals (Phase 112) ------------------------------------------

#: The Lean declaration every radical-free statement cites.
RADICAL_FREE_LEAN = "GLM.QuinticRadicals.no_radical_root_of_prime_degree"


def _is_prime(n: int) -> bool:
    return n >= 2 and all(n % d for d in range(2, isqrt(n) + 1))


def radical_free(f: List[Fraction], real_roots: int,
                 irreducible: bool = True) -> Optional[str]:
    """The reason no root of ``f`` is expressible in radicals, or ``None``
    when the certificate does not apply: ``f`` irreducible over the
    rationals, of prime degree ``n >= 5``, with exactly ``n - 2`` distinct
    real roots (so two non-real ones).  Its Galois group is then the full
    symmetric group on ``n`` letters, which is not solvable
    (:data:`RADICAL_FREE_LEAN`)."""
    n = len(f) - 1
    if not irreducible or n < 5 or not _is_prime(n) or real_roots != n - 2:
        return None
    return (f"no root of it is expressible in radicals: irreducible over the "
            f"rationals, of prime degree {n}, with exactly two non-real "
            f"roots, so its Galois group is the full symmetric group on "
            f"{n} roots, which is not solvable ({RADICAL_FREE_LEAN})")


def certify_numeric(ints: List[int]) -> Optional[str]:
    """:func:`radical_free` for an integer polynomial, deciding every
    hypothesis itself: squarefree, irreducible (by :func:`zassenhaus`), and
    the real roots counted by a Sturm chain."""
    from .symbolic_algebraic import isolate_real_roots, pderiv, pgcd
    n = len(ints) - 1
    if n < 5 or not _is_prime(n):
        return None
    fq = [Fraction(c) for c in ints]
    if len(pgcd(fq, pderiv(fq))) > 1:
        return None
    facs = zassenhaus(ints)
    if facs is None or len(facs) != 1:
        return None
    return radical_free(fq, len(isolate_real_roots(fq)))


# -- no root in radicals, read from a Frobenius element (Phase 113) -----------

#: The Lean declaration every Frobenius radical-free statement cites.
FROBENIUS_LEAN = "GLM.FrobeniusRadicals.no_radical_root_of_frobenius_shape"
#: Primes up to this bound are tried, in increasing order.
FROBENIUS_PRIME_BOUND = 1000


def frobenius_degrees(ints: List[int], q: int) -> Optional[List[int]]:
    """The degrees of the irreducible factors modulo the prime ``q`` of the
    integer polynomial ``ints`` (coefficients from the constant up), sorted;
    ``None`` when ``q`` divides the leading coefficient or the polynomial is
    not squarefree modulo ``q`` (that is, when ``q`` divides the
    discriminant).  By Dedekind's theorem these degrees are then the cycle
    type, on the roots, of the Frobenius element at ``q``.  Only the
    distinct-degree factorisation is needed: a block of degree ``k d`` with
    factors of degree ``d`` holds ``k`` of them."""
    f = _trim(list(ints))
    if f[-1] % q == 0 or not _squarefree_mod(f, q):
        return None
    out: List[int] = []
    for d, g in _ddf(_monic(_trim([x % q for x in f]), q), q):
        out.extend([d] * ((len(g) - 1) // d))
    return sorted(out)


def non_affine_power(degs: List[int]) -> Optional[Tuple[int, int]]:
    """``(m, s)`` when a permutation with cycle lengths ``degs`` (fixed
    points as 1) is of non-affine shape (``GLM.FrobeniusRadicals.
    NotAffineShape``): its ``m``-th power is not the identity and fixes the
    ``s >= 2`` points lying in cycles of length dividing ``m``.  Either it
    moves something and fixes two points (``m = 1``), or two cycle lengths
    ``k, k' >= 2`` have ``k'`` not dividing ``k`` (``m = k``, the smallest
    such).  ``None`` for the affine shapes: the identity, one cycle through
    every point, one fixed point with every other cycle of one length."""
    moved = [d for d in degs if d > 1]
    if not moved:
        return None
    if degs.count(1) >= 2:
        return 1, degs.count(1)
    for k in sorted(set(moved)):
        if any(k % k2 for k2 in moved):
            return k, sum(d for d in degs if k % d == 0)
    return None


def frobenius_pattern(ints: List[int], bound: int = FROBENIUS_PRIME_BOUND
                      ) -> Optional[Tuple[int, List[int], int, int]]:
    """``(q, degrees, m, s)`` for the first prime ``q < bound`` at which the
    factor degrees modulo ``q`` are of non-affine shape
    (:func:`non_affine_power`); ``None`` when no prime below the bound gives
    one."""
    for q in range(2, bound):
        if not _is_prime(q):
            continue
        degs = frobenius_degrees(ints, q)
        if degs is None:
            continue
        got = non_affine_power(degs)
        if got is not None:
            return (q, degs) + got
    return None


def _power_words(m: int) -> str:
    """``its square``, ``its cube``, ``its 4th power``, ``its 21st power``."""
    if m == 2:
        return "its square"
    if m == 3:
        return "its cube"
    suffix = ("th" if 10 <= m % 100 <= 20 else
              {1: "st", 2: "nd", 3: "rd"}.get(m % 10, "th"))
    return f"its {m}{suffix} power"


def _as_ints(f: List[Fraction]) -> List[int]:
    den = 1
    for c in f:
        den = den * Fraction(c).denominator // gcd(den, Fraction(c).denominator)
    return [int(Fraction(c) * den) for c in f]


def radical_free_frobenius(f: List[Fraction], irreducible: bool = True,
                           bound: int = FROBENIUS_PRIME_BOUND
                           ) -> Optional[str]:
    """Phase 113, ``studies/FROBENIUS_RADICAL_STUDY.md``: the reason no root
    of ``f`` is expressible in radicals, read from one Frobenius element, or
    ``None`` when it does not apply.  ``f`` irreducible over the rationals of
    prime degree ``n``, and a prime ``q`` at which the factor degrees are of
    non-affine shape: by Dedekind's theorem the Galois group holds an element
    of that cycle type, a power of it moves some roots and fixes two, and in
    a solvable transitive group of prime degree only the identity fixes two
    points (Galois), so the group is not solvable
    (:data:`FROBENIUS_LEAN`).  Dedekind's theorem itself is not checked in
    Lean; the factorisation modulo ``q`` is decided here."""
    n = len(f) - 1
    if not irreducible or not _is_prime(n):
        return None
    got = frobenius_pattern(_as_ints(list(f)), bound)
    if got is None:
        return None
    q, degs, m, fixed = got
    which = ("it moves some roots and fixes " if m == 1 else
             f"{_power_words(m)} moves some roots and fixes ")
    return (f"no root of it is expressible in radicals: irreducible over the "
            f"rationals, of prime degree {n}; modulo {q} it factors into "
            f"irreducible factors of degrees "
            f"{', '.join(str(d) for d in degs)}, so by Dedekind's theorem its "
            f"Galois group holds an element of that cycle type; {which}"
            f"{fixed} of them, and in a solvable group of prime degree only "
            f"the identity fixes two roots, so the group is not solvable "
            f"({FROBENIUS_LEAN}; Dedekind's theorem is not checked in Lean)")


# -- no root in radicals in composite degree (Phase 114) ----------------------

#: The Lean declaration every composite-degree radical-free statement cites.
PRIMITIVE_LEAN = "GLM.PrimitiveRadicals.no_radical_root_of_primitive_pattern"


def _lcm(values: List[int]) -> int:
    out = 1
    for v in values:
        out = out * v // gcd(out, v)
    return out


def jordan_power(degs: List[int]) -> Optional[Tuple[int, int]]:
    """``(l, m)`` when a permutation with cycle lengths ``degs`` (fixed
    points as 1) has exactly one cycle of length ``l``, ``l`` being 2 or 3,
    and every other cycle length prime to ``l``: its ``m``-th power, ``m``
    the least common multiple of the other lengths, is then a single
    ``l``-cycle -- a transposition or a 3-cycle
    (``GLM.FrobeniusRadicals.exists_pow_cycleType_singleton``).  2 is tried
    first.  ``None`` otherwise."""
    for ell in (2, 3):
        if degs.count(ell) == 1 and all(d % ell for d in degs if d != ell):
            return ell, _lcm([d for d in degs if d != ell])
    return None


def is_long_cycle(degs: List[int]) -> bool:
    """A cycle through every point but one: cycle type ``(n - 1, 1)``."""
    return sorted(degs) == [1, sum(degs) - 1] and sum(degs) >= 3


def primitive_pattern(ints: List[int], bound: int = FROBENIUS_PRIME_BOUND
                      ) -> Optional[Tuple[int, List[int], int, List[int],
                                          int, int]]:
    """``(q1, degrees1, q2, degrees2, l, m)``: the first prime ``q1 < bound``
    at which the factor degrees are ``(1, n - 1)`` (:func:`is_long_cycle`)
    and the first prime ``q2 < bound`` at which they pass
    :func:`jordan_power` with ``(l, m)``; ``None`` when either is missing."""
    long_at: Optional[Tuple[int, List[int]]] = None
    jordan_at: Optional[Tuple[int, List[int], int, int]] = None
    for q in range(2, bound):
        if not _is_prime(q):
            continue
        degs = frobenius_degrees(ints, q)
        if degs is None:
            continue
        if long_at is None and is_long_cycle(degs):
            long_at = (q, degs)
        if jordan_at is None:
            got = jordan_power(degs)
            if got is not None:
                jordan_at = (q, degs) + got
        if long_at is not None and jordan_at is not None:
            return long_at + jordan_at
    return None


def radical_free_primitive(f: List[Fraction], irreducible: bool = True,
                           bound: int = FROBENIUS_PRIME_BOUND
                           ) -> Optional[str]:
    """Phase 114, ``studies/PRIMITIVE_RADICAL_STUDY.md``: the reason no root
    of ``f`` is expressible in radicals when ``f`` is irreducible over the
    rationals of composite degree ``n >= 6``, read from two Frobenius
    elements, or ``None`` when it does not apply.  One of cycle type
    ``(n - 1, 1)`` makes the transitive Galois group primitive; one with a
    power that is a transposition or a 3-cycle then gives, by Jordan's
    theorem, the alternating group inside it, which is not solvable
    (:data:`PRIMITIVE_LEAN`).  Prime degree is left to
    :func:`radical_free_frobenius`, which needs one element and whose
    wording is unchanged.  Dedekind's theorem is not checked in Lean."""
    n = len(f) - 1
    if not irreducible or n < 5 or _is_prime(n):
        return None
    got = primitive_pattern(_as_ints(list(f)), bound)
    if got is None:
        return None
    q1, degs1, q2, degs2, ell, m = got
    kind = "a transposition" if ell == 2 else "a 3-cycle"
    which = (f"which is itself {kind}" if m == 1 else
             f"{_power_words(m).replace('its ', 'whose ', 1)} is {kind}")
    return (f"no root of it is expressible in radicals: irreducible over the "
            f"rationals, of degree {n}; modulo {q1} it factors into "
            f"irreducible factors of degrees "
            f"{', '.join(str(d) for d in degs1)} and modulo {q2} into "
            f"degrees {', '.join(str(d) for d in degs2)}, so by Dedekind's "
            f"theorem its Galois group holds an element fixing one root and "
            f"cycling the other {n - 1}, which makes the group primitive, and "
            f"an element {which}; a primitive group holding {kind} contains "
            f"the alternating group, which is not solvable "
            f"({PRIMITIVE_LEAN}; Dedekind's theorem is not checked in Lean)")


# -- no root in radicals in a degree that is not a prime power (Phase 116) -----

#: The Lean declaration every non-prime-power-degree statement cites.
DEGREE_LEAN = ("GLM.PrimitiveDegree."
               "no_radical_root_of_long_cycle_of_not_isPrimePow")


def is_prime_power(n: int) -> bool:
    """``n = p^k`` for a prime ``p`` and ``k >= 1`` (so 1 is not)."""
    if n < 2:
        return False
    p = 2
    while p * p <= n:
        if n % p == 0:
            while n % p == 0:
                n //= p
            return n == 1
        p += 1
    return True


def long_cycle_prime(ints: List[int], bound: int = FROBENIUS_PRIME_BOUND
                     ) -> Optional[Tuple[int, List[int]]]:
    """``(q, degrees)``: the first prime ``q < bound`` (not dividing the
    discriminant or the leading coefficient) at which the factor degrees are
    ``(1, n - 1)`` (:func:`is_long_cycle`); ``None`` when there is none."""
    for q in range(2, bound):
        if not _is_prime(q):
            continue
        degs = frobenius_degrees(ints, q)
        if degs is not None and is_long_cycle(degs):
            return q, degs
    return None


def radical_free_degree(f: List[Fraction], irreducible: bool = True,
                        bound: int = FROBENIUS_PRIME_BOUND) -> Optional[str]:
    """Phase 116, ``studies/PRIMITIVE_DEGREE_STUDY.md``: the reason no root
    of ``f`` is expressible in radicals when ``f`` is irreducible over the
    rationals of a degree ``n >= 6`` that is not a prime power and its Galois
    group holds an element of cycle type ``(n - 1, 1)``, or ``None``.  That
    element makes the transitive group primitive, and a solvable primitive
    group has prime-power degree (Galois), so the group is not solvable
    (:data:`DEGREE_LEAN`).  Unlike Phase 114 no second element is needed, so
    this reaches ``PGL(2, 5)`` and ``PSL(2, 5)`` on six points.  In
    prime-power degree it is silent: the affine groups there are solvable,
    primitive and hold ``(n - 1, 1)`` elements.  Dedekind's theorem is not
    checked in Lean."""
    n = len(f) - 1
    if not irreducible or n < 6 or is_prime_power(n):
        return None
    got = long_cycle_prime(_as_ints(list(f)), bound)
    if got is None:
        return None
    q, degs = got
    return (f"{_OPENING}irreducible over the rationals, of degree {n}, which "
            f"is not a prime power; modulo {q} it factors into irreducible "
            f"factors of degrees {', '.join(str(d) for d in degs)}, so by "
            f"Dedekind's theorem its Galois group holds an element fixing one "
            f"root and cycling the other {n - 1}, which makes the group "
            f"primitive; a solvable primitive group has prime-power degree "
            f"(Galois), so the group is not solvable ({DEGREE_LEAN}; "
            f"Dedekind's theorem is not checked in Lean)")


# -- no root in radicals through a composition (Phase 115) --------------------

#: The Lean declaration every composition radical-free statement cites.
COMPOSED_LEAN = "GLM.ComposedRadicals.no_radical_root_of_comp"

#: The words every radical-free statement opens with; a nested reason drops
#: them.
_OPENING = "no root of it is expressible in radicals: "


def _qtrim(a: List[Fraction]) -> List[Fraction]:
    a = list(a)
    while len(a) > 1 and a[-1] == 0:
        a.pop()
    return a


def _qmul(a: List[Fraction], b: List[Fraction]) -> List[Fraction]:
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                out[i + j] += x * y
    return _qtrim(out)


def _qdivmod(a: List[Fraction], b: List[Fraction]
             ) -> Tuple[List[Fraction], List[Fraction]]:
    """Division with remainder by ``b`` (leading coefficient non-zero)."""
    r = list(a)
    db = len(b) - 1
    if len(r) - 1 < db:
        return [Fraction(0)], _qtrim(r)
    q = [Fraction(0)] * (len(r) - db)
    for i in range(len(r) - 1 - db, -1, -1):
        c = r[i + db] / b[-1]
        q[i] = c
        if c:
            for j, y in enumerate(b):
                r[i + j] -= c * y
    return _qtrim(q), _qtrim(r[:db] or [Fraction(0)])


def compose(g: List[Fraction], h: List[Fraction]) -> List[Fraction]:
    """``g(h(x))``, coefficient lists from the constant up (Horner)."""
    out = [Fraction(g[-1])]
    for c in reversed(g[:-1]):
        out = _qmul(out, [Fraction(x) for x in h])
        out[0] += c
    return _qtrim(out)


def decompose(f: List[Fraction], inner: int
              ) -> Optional[Tuple[List[Fraction], List[Fraction]]]:
    """``(g, h)`` with ``f = g(h(x))``, ``deg h = inner``, ``h`` monic with
    ``h(0) = 0``, or ``None`` when no such decomposition exists.

    Over the rationals such an ``h`` is unique when it exists: ``h^r`` (``r =
    deg f / inner``) must agree with ``f / lc(f)`` in its top ``inner``
    coefficients, which fixes the coefficients of ``h`` one at a time from
    the top (the approximate ``r``-th root).  ``g`` is then read off the
    ``h``-adic expansion of ``f``: divide by ``h`` repeatedly, and every
    remainder must be a constant.  Exact arithmetic throughout, and the
    answer is checked by recomposing, so a decomposition returned is a
    decomposition."""
    f = _qtrim([Fraction(c) for c in f])
    n = len(f) - 1
    if inner < 2 or n % inner or n == inner:
        return None
    r = n // inner
    lead = f[-1]
    monic = [c / lead for c in f]
    h = [Fraction(0)] * inner + [Fraction(1)]
    for j in range(1, inner):
        trial = list(h)
        power = [Fraction(1)]
        for _ in range(r):
            power = _qmul(power, trial)
        got = power[n - j] if n - j < len(power) else Fraction(0)
        h[inner - j] = (monic[n - j] - got) / r
    h[0] = Fraction(0)
    g: List[Fraction] = []
    rest = monic
    for _ in range(r + 1):
        q, rem = _qdivmod(rest, h)
        if len(rem) > 1:
            return None
        g.append(rem[0])
        rest = q
        if len(rest) == 1 and rest[0] == 0:
            break
    if len(rest) != 1 or rest[0] != 0 or len(g) != r + 1:
        return None
    g = [c * lead for c in g]
    if compose(g, h) != f:
        return None
    return g, h


def decompositions(f: List[Fraction]
                   ) -> List[Tuple[List[Fraction], List[Fraction]]]:
    """Every decomposition :func:`decompose` finds, the inner degree
    smallest first (so the outer polynomial is of the highest degree)."""
    n = len(_qtrim([Fraction(c) for c in f])) - 1
    out = []
    for inner in range(2, n):
        if n % inner == 0:
            got = decompose(f, inner)
            if got is not None:
                out.append(got)
    return out


def _qtext(m: List[Fraction], var: str) -> str:
    from .symbolic_nonlinear import _upoly_text
    return _upoly_text(m, var)


def _outer_reason(g: List[Fraction], bound: int) -> Optional[str]:
    """A radical-free reason for the outer polynomial ``g`` (irreducible,
    since ``f`` is): complex conjugation (Phase 112), then the Frobenius
    certificates and, recursively, a further composition."""
    ints = _as_ints(list(g))
    got = certify_numeric(ints)
    if got is None:
        got = radical_free_galois([Fraction(c) for c in ints], True, bound)
    return got


def radical_free_composed(f: List[Fraction], irreducible: bool = True,
                          bound: int = FROBENIUS_PRIME_BOUND
                          ) -> Optional[str]:
    """Phase 115, ``studies/COMPOSED_RADICAL_STUDY.md``: the reason no root
    of ``f`` is expressible in radicals when ``f = g(h(x))`` and no root of
    ``g`` is, or ``None``.  A root ``x`` of ``f`` in radicals would make
    ``h(x)``, a root of ``g``, one too (:data:`COMPOSED_LEAN`).  ``f``
    irreducible makes ``g`` irreducible, which the outer certificates
    need.  Such an ``f`` has an imprimitive Galois group, so Phases 113 and
    114 are silent on it."""
    n = len(f) - 1
    if not irreducible or n < 10 or _is_prime(n):
        return None
    for g, h in decompositions(f):
        if len(g) - 1 < 5:
            continue
        inner = _outer_reason(g, bound)
        if inner is None:
            continue
        if inner.startswith(_OPENING):
            inner = inner[len(_OPENING):]
        return (f"{_OPENING}it is g(h(x)) with g(y) = {_qtext(g, 'y')} and "
                f"h(x) = {_qtext(h, 'x')}, and no root of g is expressible "
                f"in radicals ({inner}); a root x in radicals would make "
                f"h(x), a root of g, one too ({COMPOSED_LEAN})")
    return None


def radical_free_galois(f: List[Fraction], irreducible: bool = True,
                        bound: int = FROBENIUS_PRIME_BOUND) -> Optional[str]:
    """The Frobenius certificate for the degree of ``f``: Phase 113's in
    prime degree, Phase 114's in composite degree, and when that is silent,
    Phase 116's for a degree that is not a prime power, then Phase 115's
    composition certificate."""
    n = len(f) - 1
    if _is_prime(n):
        return radical_free_frobenius(f, irreducible, bound)
    got = radical_free_primitive(f, irreducible, bound)
    if got is None:
        got = radical_free_degree(f, irreducible, bound)
    if got is None:
        got = radical_free_composed(f, irreducible, bound)
    return got


def certify_numeric_any(ints: List[int],
                        bound: int = FROBENIUS_PRIME_BOUND) -> Optional[str]:
    """:func:`certify_numeric` (complex conjugation, Phase 112) and, when it
    does not apply, :func:`radical_free_galois` (one Frobenius element in
    prime degree, Phase 113; two in composite degree, Phase 114), every
    hypothesis decided here: squarefree, irreducible by :func:`zassenhaus`."""
    got = certify_numeric(ints)
    if got is not None:
        return got
    from .symbolic_algebraic import pderiv, pgcd
    n = len(ints) - 1
    if n < 5:
        return None
    fq = [Fraction(c) for c in ints]
    if len(pgcd(fq, pderiv(fq))) > 1:
        return None
    facs = zassenhaus(ints)
    if facs is None or len(facs) != 1:
        return None
    return radical_free_galois(fq, bound=bound)
