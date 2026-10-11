"""``glm_universal.evaluation.primitive_radical_cases`` -- the cases and marks
of Phase 114 (``studies/PRIMITIVE_RADICAL_STUDY.md``).

Phase 113's Frobenius certificate needs prime degree, where a transitive
group is primitive and Galois's theorem applies; it is silent on
``x^6 - x - 1``.  This round reads two Frobenius elements instead: one of
cycle type ``(n - 1, 1)``, which makes the group primitive, and one with a
power that is a transposition or a 3-cycle; by Jordan's theorem a primitive
group holding one contains the alternating group, which is not solvable for
``n >= 5`` (``GLM.PrimitiveRadicals.no_radical_root_of_primitive_pattern``).
The same certificate is carried to the ``modes.higher`` route, whose roots
were named through the coefficients with no statement about radicals.

**How the marks were set.**  These cases and marks were written before the
code was tried on any of them.  The declared values are mathematics, not
readings of the layer: ``x^n - x - 1`` has the full symmetric group for
every ``n`` (Osada, 1987); the pure powers, the cyclotomic polynomials and
the compositions ``g(x^k)`` with ``g`` of degree at most 4 have solvable
groups (a composition's group lies in a wreath product of solvable groups);
``x^10 - x^2 - 1 = g(x^2)`` with ``g = y^5 - y - 1`` has a group mapping
onto ``S5``, so not solvable, but imprimitive, so it holds no element of
cycle type ``(9, 1)`` and the test cannot reach it; the identical chain
pendulum of ``n`` links has the characteristic polynomial ``n! L_n(x)`` in
``x = l w^2 / g`` (``L_n`` the Laguerre polynomial), whose Galois group is
the full symmetric group (Schur, 1931).

Marks:

* **P1** every ``x^n - x - 1`` of composite degree below carries the
  primitive statement;
* **P2** no solvable control of composite degree carries any radical-free
  statement;
* **P3** the declared limit, the imprimitive non-solvable ``x^10 - x^2 - 1``,
  is answered and carries none (narrowed at Phase 115 to this round's own
  certificate: the composition certificate of
  ``studies/COMPOSED_RADICAL_STUDY.md`` now answers it);
* **P4** the letter cases, both refused ``NONLINEAR``: the sextic trinomial
  ``x^6 + a*x = b`` with the primitive reason, the sextic ``x^6 + a*x^2 = b``
  (a cubic in ``x^2``, solvable at every point) with no radical-free reason
  whether or not it is answered;
* **P5** the soundness battery (composite-degree polynomials with solvable
  groups by construction): no certificate given;
* **P6** the reach battery (random irreducible monic polynomials of degree
  6, 8, 9 and 10): at least 95 % certified;
* **P7** the controls on the shape reading: on every cycle type of the
  declared degrees, the Jordan test fires exactly on the types with exactly
  one cycle of length 2 (or 3) and every other length odd (or prime to 3),
  and the power it names is, counted from the cycle type, a single 2-cycle
  (or 3-cycle); the long-cycle test fires exactly on ``(n - 1, 1)``;
* **P8** ``RequestProject/GLM/PrimitiveRadicals.lean`` holds every named
  theorem and no ``sorry``;
* **P9** the ``modes.higher`` route: the identical chain pendulums of five
  and six links, and the chain of five links with unequal masses and
  lengths, answer with a radical-free statement on their modes (the
  six-link chain needs the frame to read "sextuple", which it did not);
* **P10** Phase 113's own report still meets 9 of 9 (its F3, which declared
  the sextic silent, narrowed to its own certificate's wording).
"""

from __future__ import annotations

from typing import Tuple

#: Questions whose answer must carry the primitive radical-free statement:
#: ``x^n - x - 1``, group ``S_n`` (Osada).
PRIMITIVE: Tuple[str, ...] = (
    "solve symbolically for x: x^6 - x - 1 = 0",
    "solve symbolically for x: x^8 - x - 1 = 0",
    "solve symbolically for x: x^9 - x - 1 = 0",
    "solve symbolically for x: x^10 - x - 1 = 0",
    "solve symbolically for x: x^12 - x - 1 = 0",
)

#: Solvable controls of composite degree: no radical-free statement may
#: appear.  Pure powers, the cyclotomic polynomials of 7 and 9, and
#: compositions with a cubic or a quartic.
SOLVABLE: Tuple[str, ...] = (
    "solve symbolically for x: x^6 - 2 = 0",
    "solve symbolically for x: x^8 - 2 = 0",
    "solve symbolically for x: x^6 + x^5 + x^4 + x^3 + x^2 + x + 1 = 0",
    "solve symbolically for x: x^6 + x^3 + 1 = 0",
    "solve symbolically for x: x^6 - x^2 - 1 = 0",
    "solve symbolically for x: x^8 - x^2 - 1 = 0",
    "solve symbolically for x: x^9 - x^3 - 1 = 0",
)

#: The declared limit: not solvable, but imprimitive (blocks ``{r, -r}``),
#: so no element of cycle type ``(9, 1)`` exists and the test is silent.
LIMIT: Tuple[str, ...] = (
    "solve symbolically for x: x^10 - x^2 - 1 = 0",
)

#: ``(id, question, reason expected)``, the reason ``"primitive"`` or None.
LETTERS: Tuple[Tuple[str, str, object], ...] = (
    ("sextic-trinomial-letters", "solve symbolically for x: x^6 + a*x = b",
     "primitive"),
    ("sextic-in-x-squared", "solve symbolically for x: x^6 + a*x^2 = b",
     None),
)

#: The soundness battery.  Pure powers ``x^n - c`` for ``n`` in the first
#: tuple and ``c`` in the range; the cyclotomic polynomials of the orders
#: listed (degree 6, 8, 10 or 12); and compositions ``g(x^k)`` with ``g``
#: monic of degree ``e`` and coefficients drawn from ``[-bound, bound]`` by
#: the package's generator, ``(e, k)`` in the list, ``count`` of each.  Only
#: the irreducible ones are counted.
SOUNDNESS_POWERS = ((6, 8, 9, 10, 12), range(2, 13))
SOUNDNESS_CYCLOTOMIC = (7, 9, 11, 13, 15, 16, 20, 21, 24, 28, 36)
SOUNDNESS_COMPOSITIONS = (((3, 2), (3, 3), (4, 2), (3, 4), (4, 3)), 20, 114,
                          6)

#: ``(count, seed, coefficient bound)`` of the reach battery: monic integer
#: polynomials of degree 6, 8, 9 and 10 in turn, irreducible ones only.
REACH_BATTERY = (200, 114, 9)
REACH_DEGREES = (6, 8, 9, 10)
#: The certified share mark P6 requires, as a fraction.
REACH_SHARE = (95, 100)
#: Degrees over whose every cycle type mark P7 checks the shape reading.
SHAPE_DEGREES = (6, 8, 9, 10, 12)

#: The chain pendulums of mark P9: ``(links, problem text)``.
MODES: Tuple[Tuple[int, str], ...] = (
    (5, "small oscillations of an identical quintuple pendulum"),
    (6, "small oscillations of an identical sextuple pendulum"),
    (5, "small oscillations of a quintuple pendulum"),
)
