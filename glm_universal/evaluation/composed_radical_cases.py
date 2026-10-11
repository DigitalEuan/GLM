"""``glm_universal.evaluation.composed_radical_cases`` -- the cases and marks
of Phase 115 (``studies/COMPOSED_RADICAL_STUDY.md``).

Phase 114's certificates need a primitive Galois group: one Frobenius element
of prime degree, or one of cycle type ``(n - 1, 1)``.  A composition
``f = g(h(x))`` never has one -- its roots fall into blocks, one for each root
of ``g`` -- so ``x^10 - x^2 - 1 = g(x^2)``, ``g = y^5 - y - 1``, was the
declared silent case of Phase 114.  This round decomposes ``f`` exactly and
certifies ``g`` instead: if no root of ``g`` is expressible in radicals, no
root of ``f`` is, because ``h(x)`` would be one
(``GLM.ComposedRadicals.no_radical_root_of_comp``).

**How the marks were set.**  These cases and marks were written before the
decomposition was written or tried.  The irreducibility of each declared
polynomial was checked with the existing factoring
(:func:`glm_universal.reasoning.symbolic_factor.zassenhaus`), which this round
does not change.  The declared values are otherwise mathematics: ``y^5 - y -
1``, ``y^5 - 4y + 2`` and ``y^6 - y - 1`` have the full symmetric group
(Phases 112-114 certify them); ``y^5 - 5y + 12`` (dihedral of order 10),
``y^5 + 15y + 12`` (the Frobenius group of order 20), the real quintic of the
eleventh roots of unity ``y^5 + y^4 - 4y^3 - 3y^2 + 3y + 1`` (cyclic) and the
pure powers ``y^5 - c`` have solvable groups, and a composition of
polynomials with solvable groups has a solvable group (it lies in a wreath
product of the two), so no certificate may fire on them.

Marks:

* **C1** every declared composition with a non-solvable outer polynomial is
  answered and carries the composition statement;
* **C2** no solvable control carries any radical-free statement;
* **C3** the letter cases, both refused ``NONLINEAR``: ``x^10 + a*x^2 = b``
  with the composition reason; ``x^10 + a*x^5 = b`` (a quadratic in
  ``x^5``, solvable at every point) with no radical-free reason whether or
  not it is answered;
* **C4** the soundness battery (compositions with a solvable outer
  polynomial of degree 5, and Phase 114's own soundness battery): no
  certificate given;
* **C5** the reach battery (random irreducible compositions ``g(h(x))``, ``g``
  monic of degree 5, 6 or 7, ``h`` monic of degree 2 or 3): at least 95 %
  certified;
* **C6** the decomposition is exact: on every composition built for C4 and
  C5, a decomposition with the inner degree used to build it is found, and
  recomposed it equals the polynomial;
* **C7** ``RequestProject/GLM/ComposedRadicals.lean`` holds every named
  theorem and no ``sorry``;
* **C8** the earlier reports: Phase 114's still meets 10 of 10 (its P3, which
  declared ``x^10 - x^2 - 1`` silent, narrowed to its own certificate's
  wording) and Phase 112's 7 of 7.
"""

from __future__ import annotations

from typing import Tuple

#: Questions whose answer must carry the composition statement:
#: ``(question, outer polynomial g, inner polynomial h)`` with coefficient
#: lists from the constant up.
COMPOSED: Tuple[Tuple[str, Tuple[int, ...], Tuple[int, ...]], ...] = (
    ("solve symbolically for x: x^10 - x^2 - 1 = 0",
     (-1, -1, 0, 0, 0, 1), (0, 0, 1)),
    ("solve symbolically for x: x^10 - 4*x^2 + 2 = 0",
     (2, -4, 0, 0, 0, 1), (0, 0, 1)),
    ("solve symbolically for x: x^15 - x^3 - 1 = 0",
     (-1, -1, 0, 0, 0, 1), (0, 0, 0, 1)),
    ("solve symbolically for x: x^12 - x^2 - 1 = 0",
     (-1, -1, 0, 0, 0, 0, 1), (0, 0, 1)),
    ("solve symbolically for x: x^10 + 5*x^9 + 10*x^8 + 10*x^7 + 5*x^6 + "
     "x^5 - x^2 - x - 1 = 0",
     (-1, -1, 0, 0, 0, 1), (0, 1, 1)),
)

#: Solvable controls: compositions whose outer polynomial has a solvable
#: group (degree at most 4, or a solvable quintic), and pure powers.
SOLVABLE: Tuple[str, ...] = (
    "solve symbolically for x: x^6 - x^2 - 1 = 0",
    "solve symbolically for x: x^8 - x^2 - 1 = 0",
    "solve symbolically for x: x^9 - x^3 - 1 = 0",
    "solve symbolically for x: x^10 - 5*x^2 + 12 = 0",
    "solve symbolically for x: x^10 - 2 = 0",
    "solve symbolically for x: x^10 + 5*x^9 + 10*x^8 + 10*x^7 + 5*x^6 + "
    "x^5 - 2 = 0",
)

#: ``(id, question, reason expected)``, the reason ``"composed"`` or None.
LETTERS: Tuple[Tuple[str, str, object], ...] = (
    ("decic-in-x-squared-letters", "solve symbolically for x: x^10 + a*x^2 = b",
     "composed"),
    ("decic-quadratic-in-x-fifth", "solve symbolically for x: x^10 + a*x^5 = b",
     None),
)

#: Solvable quintics for the soundness battery, coefficients from the
#: constant up: dihedral, Frobenius of order 20, cyclic, and pure powers.
SOLVABLE_QUINTICS: Tuple[Tuple[int, ...], ...] = (
    (12, -5, 0, 0, 0, 1),
    (12, 15, 0, 0, 0, 1),
    (1, 3, -3, -4, 1, 1),
    (-2, 0, 0, 0, 0, 1),
    (-3, 0, 0, 0, 0, 1),
    (-6, 0, 0, 0, 0, 1),
)
#: ``(inner degrees, inner polynomials per quintic and degree, seed,
#: coefficient bound)``: each solvable quintic composed with that many random
#: monic inner polynomials of each degree.
SOUNDNESS_INNER = ((2, 3), 5, 115, 6)

#: ``(count, seed, coefficient bound)`` of the reach battery: compositions
#: ``g(h(x))``, ``(deg g, deg h)`` cycling through :data:`REACH_SHAPES`, ``g``
#: and ``h`` monic with coefficients drawn by the package's generator,
#: irreducible ones only.
REACH_BATTERY = (120, 115, 9)
REACH_SHAPES: Tuple[Tuple[int, int], ...] = ((5, 2), (5, 3), (6, 2), (6, 3),
                                            (7, 2))
#: The certified share mark C5 requires, as a fraction.
REACH_SHARE = (95, 100)
