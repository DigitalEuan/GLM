"""``glm_universal.evaluation.quintic_radical_cases`` -- the cases and marks
of Phase 112 (``studies/QUINTIC_RADICAL_STUDY.md``).

The cubic radical study's §8 left two limits: numeric polynomials above
degree 6 were refused (``NONLINEAR``, factors not decided), and the quintic in
letters ``x^5 + p*x = q`` was refused with no reason beyond its degree.  This
round factors past degree 6 (Zassenhaus) and states, with a proved reason,
when a root has no expression in radicals.

**How the marks were set.**  Unlike Phase 104, these cases were written after
the code had been tried on a handful of them (the study says which); the
declared values below are mathematics, not readings of the layer: the number
of real roots of each high-degree case follows from its planted factors, and
which cases carry the radical-free certificate follows from the theorem.

Marks:

* **R1** every high-degree case answered, with exactly the declared number of
  real roots, its column-3 script verified, and every root's bracket holding
  a sign change of the question's own polynomial (checked exactly);
* **R2** every certificate case carries the radical-free statement;
* **R3** no control case carries it;
* **R4** the letter cases: refused ``NONLINEAR`` in every case, with the
  no-radical-formula reason exactly where declared;
* **R5** the planted battery of degrees 7 to 16: no wrong answer (a wrong
  answer is a branch count other than the planted real-root count, or a
  failed script) and at least 90 % answered;
* **R6** the control: Zassenhaus's factors equal Kronecker's on every
  polynomial of degree 4 to 6 in the agreement battery;
* **R7** ``RequestProject/GLM/QuinticRadicals.lean`` holds every named
  theorem and no ``sorry``.
"""

from __future__ import annotations

from typing import Tuple

#: ``(id, question, real roots)``: numeric polynomials past degree 6.
HIGH: Tuple[Tuple[str, str, int], ...] = (
    # irreducible septic trinomial: three real roots (Descartes: at most
    # two positive, one negative; signs at -2, 0, 1, 2 give three)
    ("septic-trinomial", "solve symbolically for x: x^7 - 3*x + 1 = 0", 3),
    # (x^4 - 2)(x^4 - 3): the real fourth roots of 2 and 3
    ("octic-biquartic", "solve symbolically for x: x^8 - 5*x^4 + 6 = 0", 4),
    # (x^3 - 2)(x^5 - 4x + 2): one real cube root, three real quintic roots
    ("octic-mixed",
     "solve symbolically for x: x^8 - 2*x^5 - 4*x^4 + 2*x^3 + 8*x - 4 = 0",
     4),
    # (x^5 - 6x + 3)(x^5 - x - 1): three real roots, then one
    ("decic-two-quintics",
     "solve symbolically for x: x^10 - 7*x^6 + 2*x^5 + 6*x^2 + 3*x - 3 = 0",
     4),
    # (x^4 - 2)(x^4 - 3)(x^4 - 5): six real fourth roots
    ("dodecic-three-quartics",
     "solve symbolically for x: x^12 - 10*x^8 + 31*x^4 - 30 = 0", 6),
    # (x^2 - 2)(x^7 - 9x^3 + 4x - 1): two square roots and five septic roots
    ("nonic-septic-factor",
     "solve symbolically for x: x^9 - 2*x^7 - 9*x^5 + 22*x^3 - x^2 - 8*x + "
     "2 = 0", 7),
)

#: Questions whose answer must carry the radical-free certificate.
CERTIFIED: Tuple[str, ...] = (
    "solve symbolically for x: x^5 - 4*x + 2 = 0",
    "solve symbolically for x: x^5 - 6*x + 3 = 0",
    "solve symbolically for x: x^7 - 9*x^3 + 4*x - 1 = 0",
    "solve symbolically for x: x^8 - 2*x^5 - 4*x^4 + 2*x^3 + 8*x - 4 = 0",
    "solve symbolically for x: x^9 - 2*x^7 - 9*x^5 + 22*x^3 - x^2 - 8*x + "
    "2 = 0",
)

#: Controls that must not carry it: ``x^5 - x - 1`` (Galois group S5, but
#: one real root: the certificate is sufficient, not necessary),
#: ``x^5 - 5*x + 12`` (solvable, one real root), ``x^7 - 3*x + 1`` (three
#: real roots of seven), a cubic and a sextic.
UNCERTIFIED: Tuple[str, ...] = (
    "solve symbolically for x: x^5 - x - 1 = 0",
    "solve symbolically for x: x^5 - 5*x + 12 = 0",
    "solve symbolically for x: x^7 - 3*x + 1 = 0",
    "solve symbolically for x: x^3 - 3*x + 1 = 0",
    "solve symbolically for x: x^6 - 6*x + 3 = 0",
)

#: ``(id, question, reason expected)``: polynomials in letters, every one
#: refused ``NONLINEAR``.  De Moivre's quintic is solvable in radicals for
#: every value of its letters, so no reason may be given for it; the septic
#: trinomial never has five real roots, so the certificate cannot reach it.
LETTERS: Tuple[Tuple[str, str, bool], ...] = (
    ("quintic-in-letters", "solve symbolically for x: x^5 + p*x = q", True),
    ("quintic-quadratic-term", "solve symbolically for x: x^5 + a*x^2 = b",
     True),
    ("de-moivre", "solve symbolically for x: x^5 - 5*a*x^3 + 5*a^2*x = b",
     False),
    ("septic-trinomial-letters", "solve symbolically for x: x^7 + a*x = b",
     False),
)

#: ``(count, seed, lowest degree, highest degree)`` of the planted battery.
PLANTED_BATTERY = (40, 112, 7, 16)
#: ``(count, seed)`` of the Zassenhaus-against-Kronecker agreement battery.
AGREEMENT_BATTERY = (200, 1120)
#: The answered share mark R5 requires, as a fraction.
ANSWERED_SHARE = (9, 10)
