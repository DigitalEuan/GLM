"""``glm_universal.evaluation.cubic_trig_cases`` -- the declared cases of
Phase 108: a cubic in letters with three real roots (the first item of
``studies/CUBIC_RADICAL_STUDY.md`` §8).

Written **before** any code of the round.  The scorer is
:mod:`glm_universal.runtime.cubic_trig_report`.

Phase 104 refused a cubic in letters whose discriminant is negative for
every value of the letters (``NONLINEAR``: "no real radical form (three real
roots)"), and that refusal blocks the normal modes of a three-degree-of-
freedom system.  When the discriminant was negative but not recognised as
such (it is not a square times a negative number as written), Phase 104
printed Cardano's root under a condition no value of the letters satisfies.
This round answers both by two routes:

* **homogeneous** -- the cubic in ``u`` is ``s^3 f(u/s)`` for a ratio ``s``
  of the letters and a cubic ``f`` with rational coefficients: every real
  root is ``s`` times a root of ``f`` (an algebraic number, a square root or
  a rational), all three listed;
* **trigonometric** (Viete) -- otherwise, with the depressed form
  ``t^3 + P t + Q = 0``, ``P < 0`` and ``4P^3 + 27Q^2 < 0``: the three roots
  are ``t_k = 2 sqrt(-P/3) cos(acos(K)/3 - 2 pi k/3)``, ``k = 0, 1, 2``,
  ``K = (3Q/(2P)) sqrt(-3/P)``, in decreasing order.

* :data:`HOMOGENEOUS` -- ``(id, question, [branch, ...])``: each branch is
  ``{unknown: expression}`` in the letters, with the algebraic numbers
  written as twelve-decimal strings (read exactly).  A machine branch
  matches when every target agrees with the declared expression to one part
  in 10^9 at three sample points.
* :data:`VIETE` -- ``(id, question, unknown, shift, r^2, K)``: the declared
  branches are ``shift + 2 r c_k`` with ``c_k`` the ``k``-th largest root of
  ``4c^3 - 3c = K`` (Lean: ``vieta_cos_strictly_ordered``); matched the
  same way at sample points where ``|K| < 1``.
* :data:`MOTION` -- ``(id, question, [declared squared frequency, ...])``.
* :data:`UNCHANGED` -- questions whose reading must be the same text as
  before the round.
* :data:`MARKS` -- the ladder.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

__all__ = ["HOMOGENEOUS", "VIETE", "MOTION", "UNCHANGED", "MARKS",
           "VIETE_BATTERY", "HOMOGENEOUS_BATTERY", "OUTSIDE_MOVED"]

#: The triple pendulum's modes: lambda^3 - 9 lambda^2 + 18 lambda - 6 = 0.
_L0, _L1, _L2 = "6.289945082937", "2.294280360279", "0.415774556783"
#: mu^3 - 3 mu + 1 = 0.
_M0, _M1, _M2 = "1.532088886238", "0.347296355334", "-1.879385241572"

HOMOGENEOUS: Tuple[Tuple[str, str, List[Dict[str, str]]], ...] = (
    ("scaled-casus",
     "solve symbolically for x in terms of a: x^3 - 3*a^2*x + a^3 = 0",
     [{"x": f"{_M0}*a"}, {"x": f"{_M1}*a"}, {"x": f"{_M2}*a"}]),
    ("triple-pendulum-cubic",
     "solve symbolically for w in terms of g, l: "
     "l^3*w^3 - 9*g*l^2*w^2 + 18*g^2*l*w - 6*g^3 = 0",
     [{"w": f"{_L0}*g/l"}, {"w": f"{_L1}*g/l"}, {"w": f"{_L2}*g/l"}]),
    ("three-masses-cubic",
     "solve symbolically for x in terms of k, m: "
     "m^3*x^3 - 6*k*m^2*x^2 + 10*k^2*m*x - 4*k^3 = 0",
     [{"x": "2*k/m"}, {"x": "(2 + sqrt(2))*k/m"},
      {"x": "(2 - sqrt(2))*k/m"}]),
    ("two-ratio-casus",
     "solve symbolically for y in terms of p, q: "
     "q^3*y^3 - 3*p^2*q*y + p^3 = 0",
     [{"y": f"{_M0}*p/q"}, {"y": f"{_M1}*p/q"}, {"y": f"{_M2}*p/q"}]),
)

#: ``(id, question, unknown, shift, r^2 = -P/3, K)``.
VIETE: Tuple[Tuple[str, str, str, str, str, str], ...] = (
    ("plainly-negative",
     "solve symbolically for x in terms of a: "
     "x^3 - 3*(a^2 + 1)*x + 2*a*(a^2 + 1) = 0",
     "x", "0", "a^2 + 1", "-a/sqrt(a^2 + 1)"),
    ("plainly-negative-shifted",
     "solve symbolically for x in terms of b: "
     "x^3 - 3*x^2 - 3*b^2*x + 2*b^3 + 3*b^2 + 2*b + 2 = 0",
     "x", "1", "b^2 + 1", "-b/sqrt(b^2 + 1)"),
    ("plainly-negative-two-letters",
     "solve symbolically for x in terms of a, b: "
     "x^3 - 3*(a^2 + b^2 + 1)*x + 2*a*(a^2 + b^2 + 1) = 0",
     "x", "0", "a^2 + b^2 + 1", "-a/sqrt(a^2 + b^2 + 1)"),
)

#: ``(id, question, [squared frequency, ...])``.
MOTION: Tuple[Tuple[str, str, List[str]], ...] = (
    ("triple-pendulum",
     "A triple pendulum of three identical bobs of mass m on strings of "
     "identical length l: formulate the Lagrangian and the equations of "
     "motion using the small-angle approximation.",
     [f"{_L0}*g/l", f"{_L1}*g/l", f"{_L2}*g/l"]),
    ("three-masses-four-springs",
     "derive equations of motion for x1, x2, x3, small oscillations: "
     "L = (1/2)*m*(x1_dot^2 + x2_dot^2 + x3_dot^2) "
     "- (1/2)*k*(x1^2 + (x2 - x1)^2 + (x3 - x2)^2 + x3^2)",
     ["(2 - sqrt(2))*k/m", "2*k/m", "(2 + sqrt(2))*k/m"]),
)

#: Readings that must not move: Cardano in letters (sign of the
#: discriminant not decided), a numeric cubic, the quintic refusal.
UNCHANGED: Tuple[str, ...] = (
    "solve symbolically for x in terms of p, q: x^3 + p*x = q",
    "solve symbolically for x: x^3 - 3*x + 1 = 0",
    "solve symbolically for x: x^3 + x + 1 = 0",
    "solve symbolically for x: x^5 + p*x = q",
    "solve symbolically for x in terms of a: x^3 + a*x + 1 = 0",
)

#: Random cubics ``y^3 - 3 A y + 2 B A`` shifted by a random integer, with
#: ``A = B^2 + C``, ``B`` an integer times a monomial in ``a, b`` and ``C`` a
#: positive integer times the square of a monomial plus a positive integer,
#: so that ``-D = A^2 C`` is a sum of even powers with positive
#: coefficients (``D = Q^2/4 + P^3/27`` of the depressed form):
#: ``(count, seed)``.
VIETE_BATTERY: Tuple[int, int] = (30, 10801)

#: Random integer cubics with three real roots and no rational root,
#: homogenised by a ratio of two letters: ``(count, seed)``.
HOMOGENEOUS_BATTERY: Tuple[int, int] = (30, 10802)

#: The outside texts the round is expected to move: the triple pendulum
#: (its answer gains the normal modes).  Every other text must read as
#: before.
OUTSIDE_MOVED: Tuple[str, ...] = ("triple pendulum",)

MARKS: Tuple[Tuple[str, str], ...] = (
    ("T1", "every case of HOMOGENEOUS answered with exactly the declared "
           "branches (three each), matched at three sample points"),
    ("T2", "every case of VIETE answered with exactly the three declared "
           "branches, matched at three sample points where |K| < 1, each "
           "answer stating 4P^3 + 27Q^2 < 0 and the trigonometric form"),
    ("T3", "every answered reading of HOMOGENEOUS and VIETE verifies by its "
           "column-3 script, and the script with the first target doubled "
           "is rejected"),
    ("T4", "MOTION: the identical triple pendulum gives the three declared "
           "squared frequencies and the three masses on four springs give "
           "the three declared ones; both motion scripts verify and both "
           "mutants are rejected"),
    ("T5", "no regression: every UNCHANGED reading has the same text as "
           "before the round, every Phase 104 mark reads as before (K1-K5, "
           "K8), and every Phase 106 motion case reads as before"),
    ("T6", "the Viete battery: every cubic answered with three branches "
           "whose scripts verify, and at a sample point the three values "
           "are three distinct roots of the cubic (residual below 10^-9)"),
    ("T7", "the homogeneous battery: every cubic answered with three "
           "branches whose scripts verify, matched to the three roots at a "
           "sample point"),
    ("T8", "a Lean file proves the trigonometric root, |K| <= 1 exactly when "
           "4P^3 + 27Q^2 <= 0, the strict order of the three cosines, that "
           "three distinct roots of a depressed cubic are all its roots, and "
           "the homogeneous scaling, with no sorry"),
    ("T9", "outside texts: only the texts of OUTSIDE_MOVED change reading, "
           "and the evaluation cases read as before"),
)
