"""``glm_universal.evaluation.primitive_degree_cases`` -- the cases and marks
of Phase 116 (``studies/PRIMITIVE_DEGREE_STUDY.md``).

Phase 114's certificate needs two Frobenius elements: one of cycle type
``(n - 1, 1)``, which makes the Galois group primitive, and one with a power
that is a transposition or a 3-cycle (Jordan).  ``PGL(2, 5)`` and ``PSL(2, 5)``
acting on the six points of the projective line over ``F_5`` are primitive,
not solvable (they are ``S_5`` and ``A_5``), and hold no element of the second
kind, so a sextic with either group was the declared silent case of Phase 114
(``PRIMITIVE_RADICAL_STUDY.md`` §4).

This round uses Galois's theorem instead of Jordan's: a solvable primitive
group has prime-power degree
(``GLM.PrimitiveDegree.isPrimePow_card_of_isPreprimitive_of_isSolvable``).  In
a degree that is not a prime power the first element alone then rules
solvability out (``GLM.PrimitiveDegree.no_radical_root_of_long_cycle_of_not_isPrimePow``).

**Where the declared sextics come from.**  For an irreducible quintic
``x^5 + a x + b`` with roots ``x_1 .. x_5``, the six values of
``theta = (sum of x_i x_j over the edges of a pentagon - the same over its
pentagram)^2`` are permuted by the Galois group as ``S_5`` permutes the six
pentagons, which is the action of ``PGL(2, 5)`` on six points.  Their monic
polynomial (Cayley's resolvent, in this normalisation) is :func:`cayley_sextic`:

    theta^6 - 40 a theta^5 + 880 a^2 theta^4 - 8960 a^3 theta^3
            + 44800 a^4 theta^2 - (108544 a^5 + 3200000 b^4) theta
            + 102400 a^6.

It was read off high-precision numerical roots at four points and checked at
five more before these cases were written (``mpmath``, outside the package;
every coefficient is fixed by weight: ``theta`` and ``a`` weigh 4, ``b``
weighs 5).  When the quintic's group is not solvable (``S_5`` or ``A_5``) the
sextic is irreducible with group ``PGL(2, 5)`` or ``PSL(2, 5)``; when it is
solvable (inside the Frobenius group of order 20, which fixes one pentagon)
the sextic has a rational root.  Mark D5 uses exactly this: a quintic whose
sextic is irreducible has a non-solvable group, so its sextic has group
``PGL(2, 5)`` or ``PSL(2, 5)``.

**How the marks were set.**  These cases and marks were written before the
new certificate was written or tried.  The irreducibility of the declared
sextics was checked with the existing factoring
(:func:`glm_universal.reasoning.symbolic_factor.zassenhaus`), which this round
does not change, and their real-root counts with ``mpmath``.

Marks:

* **D1** every declared sextic is answered and carries the new statement
  (its Lean citation);
* **D2** no solvable control carries any radical-free statement;
* **D3** the groups themselves: ``PGL(2, 5)`` and ``PSL(2, 5)`` built as
  permutations of the projective line over ``F_5`` have orders 120 and 60,
  are transitive, hold an element of cycle type ``(5, 1)``, and hold no
  element that Phase 114's Jordan reading accepts; and on the declared
  sextics Phase 114's certificate is silent;
* **D4** the soundness battery (Phase 114's and Phase 115's, every
  polynomial with a solvable group): no certificate given;
* **D5** the reach battery (Cayley sextics of random trinomial quintics, both
  irreducible): at least 95 % certified by the new statement, and none by
  Phase 114's;
* **D6** the degree gate: the prime-power test agrees with a count by trial
  division on every ``n`` from 1 to 512, and on every polynomial of degree 8
  or 9 in Phase 114's reach battery the new certificate is silent;
* **D7** ``RequestProject/GLM/PrimitiveDegree.lean`` holds every named
  theorem and no ``sorry``;
* **D8** the earlier reports: Phase 115's still meets 8 of 8 (which re-reads
  Phase 114's 10 of 10 and Phase 112's 7 of 7).
"""

from __future__ import annotations

from typing import List, Tuple


def cayley_sextic(a: int, b: int) -> List[int]:
    """Cayley's sextic resolvent of ``x^5 + a x + b``, coefficients from the
    constant up (see the module docstring)."""
    return [102400 * a ** 6, -(108544 * a ** 5 + 3200000 * b ** 4),
            44800 * a ** 4, -8960 * a ** 3, 880 * a ** 2, -40 * a, 1]


#: Questions whose answer must carry the new statement: ``(question, the
#: quintic x^5 + a x + b it is the resolvent of, as (a, b), the scale theta =
#: s u)``.  Groups: ``x^5 - x - 1`` and ``x^5 + 2x - 1`` have ``S_5``, so their
#: sextics ``PGL(2, 5)``; ``x^5 + 20x + 16`` has ``A_5``, so ``PSL(2, 5)``.
DEGREE: Tuple[Tuple[str, Tuple[int, int], int], ...] = (
    ("solve symbolically for x: x^6 + 10*x^5 + 55*x^4 + 140*x^3 + 175*x^2 "
     "- 3019*x + 25 = 0", (-1, -1), 4),
    ("solve symbolically for x: x^6 - 10*x^5 + 55*x^4 - 140*x^3 + 175*x^2 "
     "- 170*x + 25 = 0", (20, 16), 80),
    ("solve symbolically for x: x^6 - 20*x^5 + 220*x^4 - 1120*x^3 + "
     "2800*x^2 - 6517*x + 1600 = 0", (2, -1), 4),
)

#: Solvable controls of degree 6: pure powers, the cyclotomic polynomials of
#: 7 and 9, a composition with a cubic, and the Cayley sextic of the
#: Frobenius quintic ``x^5 + 15x + 12`` (it has the rational root 180).
SOLVABLE: Tuple[str, ...] = (
    "solve symbolically for x: x^6 - 2 = 0",
    "solve symbolically for x: x^6 - 3 = 0",
    "solve symbolically for x: x^6 + x^5 + x^4 + x^3 + x^2 + x + 1 = 0",
    "solve symbolically for x: x^6 + x^3 + 1 = 0",
    "solve symbolically for x: x^6 - x^2 - 1 = 0",
    "solve symbolically for x: x^6 - 600*x^5 + 198000*x^4 - 30240000*x^3 + "
    "2268000000*x^2 - 148780800000*x + 1166400000000 = 0",
)

#: ``(count, seed, coefficient bound)`` of the reach battery: ``(a, b)`` drawn
#: by the package's generator from ``[-bound, bound]``, ``b != 0``, kept when
#: ``x^5 + a x + b`` and its Cayley sextic are both irreducible.
REACH_BATTERY = (60, 116, 12)
#: The certified share mark D5 requires, as a fraction.
REACH_SHARE = (95, 100)
#: The range mark D6 checks the prime-power test over.
PRIME_POWER_RANGE = range(1, 513)
