"""``glm_universal.evaluation.frobenius_radical_cases`` -- the cases and marks
of Phase 113 (``studies/FROBENIUS_RADICAL_STUDY.md``).

Phase 112's radical-free certificate reads the Galois group through complex
conjugation, so it needs exactly two non-real roots and is silent on
``x^5 - x - 1``.  This round reads it through one Frobenius element: factor
the polynomial modulo a prime ``q`` that does not divide its discriminant; by
Dedekind's theorem the factor degrees are the cycle type of an element of the
Galois group; when that cycle type is not of the affine shape, a power of the
element moves some roots and fixes two; and by Galois's theorem a solvable
group of prime degree has no such element
(``GLM.FrobeniusRadicals.no_radical_root_of_frobenius_shape``).

**How the marks were set.**  The code was tried on a handful of the cases
below before this file was written (the study says which).  The declared
values are mathematics, not readings of the layer: which cases have a
non-solvable Galois group, and which a solvable one, is classical
(``x^5 - 5x + 12`` is dihedral, ``x^5 + 15x + 12`` and the pure powers are
Frobenius groups, the quintic with roots ``2 cos(2 pi k / 11)`` is cyclic,
De Moivre's quintic is solvable at every point, and ``x^7 - 7x + 3`` is
Trinks's polynomial with group ``PSL(2, 7)``, not solvable).

Marks:

* **F1** every case with a non-solvable group carries the Frobenius
  statement;
* **F2** no solvable control carries any radical-free statement;
* **F3** the declared limit, a sextic, carries none: the test applies only
  to prime degree (since Phase 114, which certifies that sextic by two
  Frobenius elements, F3 reads only this certificate's wording);
* **F4** the letter cases, every one refused ``NONLINEAR``: the septic
  trinomial with the Frobenius reason, the quintic in letters still with
  Phase 112's reason, De Moivre's quintic with none;
* **F5** the soundness battery (polynomials with solvable groups by
  construction): no certificate given;
* **F6** the reach battery (random irreducible quintics and septics): at least
  95 % certified, and every one the conjugation certificate certifies is
  certified by the Frobenius test too;
* **F7** the controls on the modular reading: the factor degrees modulo each
  prime equal those of the complete modular factorisation, and on every cycle
  type of degree 5, 7, 11 and 13 the shape test fires exactly off the affine
  shapes, with a power that fixes at least two points and moves one;
* **F8** ``RequestProject/GLM/FrobeniusRadicals.lean`` holds every named
  theorem and no ``sorry``;
* **F9** Phase 112's own report still meets 7 of 7.
"""

from __future__ import annotations

from typing import Tuple

#: Questions whose answer must carry the Frobenius radical-free statement.
#: The groups are S5, S5, A5, S7, S11 and PSL(2, 7) (Trinks's septic, which
#: holds no transposition and no 3-cycle, but does hold elements fixing three
#: roots).
FROBENIUS: Tuple[str, ...] = (
    "solve symbolically for x: x^5 - x - 1 = 0",
    "solve symbolically for x: x^5 - x + 1 = 0",
    "solve symbolically for x: x^5 + 20*x + 16 = 0",
    "solve symbolically for x: x^7 - 3*x + 1 = 0",
    "solve symbolically for x: x^11 - x - 1 = 0",
    "solve symbolically for x: x^7 - 7*x + 3 = 0",
)

#: Solvable controls: no radical-free statement may appear.
SOLVABLE: Tuple[str, ...] = (
    "solve symbolically for x: x^5 - 5*x + 12 = 0",
    "solve symbolically for x: x^5 + 15*x + 12 = 0",
    "solve symbolically for x: x^5 + x^4 - 4*x^3 - 3*x^2 + 3*x + 1 = 0",
    "solve symbolically for x: x^5 - 2 = 0",
    "solve symbolically for x: x^7 - 2 = 0",
)

#: The declared limit: a composite degree, where the test does not apply
#: (transitivity gives primitivity only in prime degree).
LIMIT: Tuple[str, ...] = (
    "solve symbolically for x: x^6 - x - 1 = 0",
)

#: ``(id, question, reason expected)`` with reason one of ``"frobenius"``,
#: ``"conjugation"`` or ``None``.
LETTERS: Tuple[Tuple[str, str, object], ...] = (
    ("septic-trinomial-letters", "solve symbolically for x: x^7 + a*x = b",
     "frobenius"),
    ("quintic-in-letters", "solve symbolically for x: x^5 + p*x = q",
     "conjugation"),
    ("de-moivre", "solve symbolically for x: x^5 - 5*a*x^3 + 5*a^2*x = b",
     None),
)

#: The soundness battery: De Moivre's quintic ``x^5 - 5 a x^3 + 5 a^2 x - b``
#: at every integer point with ``a`` in the first range and ``b`` in the
#: second (both without 0), and the pure powers ``x^n - c`` for ``n`` in
#: ``(5, 7)`` and ``c`` in the third range; only the irreducible ones are
#: counted.
SOUNDNESS_DE_MOIVRE = (range(-4, 5), range(-8, 9))
SOUNDNESS_POWERS = ((5, 7), range(2, 31))

#: ``(count, seed, coefficient bound)`` of the reach battery: monic integer
#: quintics and septics (alternately), coefficients drawn from
#: ``[-bound, bound]``, irreducible ones only.
REACH_BATTERY = (200, 113, 9)
#: The certified share mark F6 requires, as a fraction.
REACH_SHARE = (95, 100)
#: Primes on which mark F7 compares the two modular readings.
DDF_PRIMES = (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47)
#: Degrees over whose every cycle type mark F7 checks the shape reading.
SHAPE_DEGREES = (5, 7, 11, 13)
