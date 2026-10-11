"""``glm_universal.reasoning.primitive_degree_groups`` -- the exact objects
Phase 116's marks are read against (``studies/PRIMITIVE_DEGREE_STUDY.md``).

The projective groups ``PGL(2, 5)`` and ``PSL(2, 5)`` as permutations of six
points, the cycle type of a permutation, the declared Cayley sextics rescaled
to small coefficients, the reach battery of Cayley sextics, and the
prime-power test's control by trial division.  Kept apart from
:mod:`glm_universal.runtime.primitive_degree_report`, which reads questions
through the frames, so that the unit tests of these facts do not reach the
router (and with it the whole Lean development; ``ITERATION_COST_STUDY.md``
§5k).  Nothing here uses a float.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Tuple

from ..evaluation import primitive_degree_cases as C

__all__ = ["projective_group", "cycle_degrees", "scaled_sextic",
           "irreducible", "reach_polys", "prime_power_by_division"]


def projective_group(special: bool) -> List[Tuple[int, ...]]:
    """``PGL(2, 5)`` (or ``PSL(2, 5)`` when ``special``) as permutations of
    the projective line over ``F_5``, points ``0 .. 4`` and ``5`` for
    infinity: ``z -> (a z + b) / (c z + d)``, ``ad - bc`` nonzero (a nonzero
    square for ``PSL``), one permutation per map."""
    p, inf = 5, 5
    squares = {(x * x) % p for x in range(1, p)}
    perms = set()
    for a in range(p):
        for b in range(p):
            for c in range(p):
                for d in range(p):
                    det = (a * d - b * c) % p
                    if det == 0 or (special and det not in squares):
                        continue
                    img = []
                    for z in range(p + 1):
                        if z == inf:
                            num, den = a, c
                        else:
                            num, den = (a * z + b) % p, (c * z + d) % p
                        img.append(inf if den == 0 else
                                   (num * pow(den, p - 2, p)) % p)
                    perms.add(tuple(img))
    return sorted(perms)


def cycle_degrees(perm: Tuple[int, ...]) -> List[int]:
    """The cycle lengths of a permutation of ``range(n)``, fixed points as 1,
    sorted."""
    seen, out = set(), []
    for s in range(len(perm)):
        if s in seen:
            continue
        k, x = 0, s
        while x not in seen:
            seen.add(x)
            x = perm[x]
            k += 1
        out.append(k)
    return sorted(out)


def scaled_sextic(a: int, b: int, s: int) -> List[int]:
    """The Cayley sextic of ``x^5 + a x + b`` in ``u = theta / s``,
    coefficients from the constant up (exact division; the declared scales
    divide)."""
    f = C.cayley_sextic(a, b)
    return [c // s ** (6 - i) for i, c in enumerate(f)]


def irreducible(ints: List[int]) -> bool:
    """Squarefree and irreducible over the rationals, by Zassenhaus."""
    from . import symbolic_algebraic as A
    from . import symbolic_factor as Z
    fq = [Fraction(c) for c in ints]
    if len(A.pgcd(fq, A.pderiv(fq))) > 1:
        return False
    facs = Z.zassenhaus(ints)
    return facs is not None and len(facs) == 1


def reach_polys() -> List[Tuple[Tuple[int, int], List[int]]]:
    """``((a, b), sextic)`` for the reach battery: ``x^5 + a x + b`` and its
    Cayley sextic both irreducible."""
    from . import symbolic as S
    count, seed, bound = C.REACH_BATTERY
    lcg = S.Lcg(seed)
    out: List[Tuple[Tuple[int, int], List[int]]] = []
    while len(out) < count:
        a = int(lcg.next() % (2 * bound + 1)) - bound
        b = int(lcg.next() % (2 * bound + 1)) - bound
        if b == 0 or any(ab == (a, b) for ab, _ in out):
            continue
        if not irreducible([b, a, 0, 0, 0, 1]):
            continue
        f = C.cayley_sextic(a, b)
        if not irreducible(f):
            continue
        out.append(((a, b), f))
    return out


def prime_power_by_division(n: int) -> bool:
    """``n`` has exactly one prime divisor, the primes found by trial
    division: the control for
    :func:`glm_universal.reasoning.symbolic_factor.is_prime_power`."""
    primes = [p for p in range(2, n + 1)
              if all(p % d for d in range(2, p))]
    return sum(1 for p in primes if n % p == 0) == 1
