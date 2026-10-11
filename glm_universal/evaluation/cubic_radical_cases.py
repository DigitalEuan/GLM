"""``glm_universal.evaluation.cubic_radical_cases`` -- the declared cases of
Phase 104: cubics, nested square roots and the positive-root convention (the
follow-ups of ``studies/NONLINEAR_ELIMINATION_STUDY.md`` §6).

Written and committed **before** any code of the round.  The scorer is
:mod:`glm_universal.runtime.cubic_radical_report`.

* :data:`ALGEBRAIC` -- systems whose solutions are real algebraic numbers of
  degree 3 or more (no rational root, no square-root form the layer could
  print).  Each branch is declared as ``{unknown: approximate value}``, worked
  out by hand before the code; a machine branch matches when every unknown
  is within 1e-4 of its declared value.  Every real root must be found and no other.
* :data:`RADICAL` -- systems in letters (or with square roots) whose
  solutions are square roots, nested square roots or Cardano's cube roots.
  Each branch is a dictionary of expressions; a machine branch matches when
  every target agrees with the declared expression to 1e-9 at three sample
  points of the parameters at which every radicand is positive.
* :data:`REFUSALS` -- systems the layer must still refuse, with the code.
* :data:`DUAL` -- questions Phase 98's substitution answers by a convention
  (a positive root) or with a target that holds an unknown it does not
  print.  Under the owner's rule ("keep both tracks active; default to the
  stronger") the branch layer is consulted too, its full set of solutions is
  the default answer, and the substitution reading is kept beside it.  Each
  entry declares the number of branches the default answer must have.
* :data:`MARKS` -- the ladder.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

__all__ = ["ALGEBRAIC", "RADICAL", "REFUSALS", "DUAL", "MARKS",
           "BATTERY_SEEDS", "CUBIC_BATTERY"]

AlgBranch = Dict[str, str]

#: ``(id, question, [branch, ...])``; a branch gives each unknown's value
#: to six decimals, as a decimal string read exactly (``Fraction("1.414214")``;
#: written as float literals when first committed, and changed to strings
#: with the same digits so that the package stays float-free).
ALGEBRAIC: Tuple[Tuple[str, str, List[AlgBranch]], ...] = (
    # Three real roots: the casus irreducibilis (no real radical form).
    ("cubic-three-real",
     "solve symbolically for x: x^3 - 3*x + 1 = 0",
     [{"x": "-1.879385"}, {"x": "0.347296"}, {"x": "1.532089"}]),
    # One real root, two complex.
    ("cubic-one-real",
     "solve symbolically for x: x^3 + x + 1 = 0",
     [{"x": "-0.682328"}]),
    # A hyperbola and a parabola: a cubic in x, y a polynomial in the root.
    ("hyperbola-and-parabola",
     "solve symbolically for x, y: x*y = 1; y = x^2 - 3",
     [{"x": "-1.532089", "y": "-0.652704"},
      {"x": "-0.347296", "y": "-2.879385"},
      {"x": "1.879385", "y": "0.532089"}]),
    # A circle and a parabola through (1, 1) whose other meeting point is
    # the one real root of t^3 - t^2 + 3*t + 1 (Phase 103 refused this
    # shape: a cubic was left).
    ("conics-leaving-a-cubic",
     "solve symbolically for x, y: x^2 + y^2 = 2; y = x^2 - x + 1",
     [{"x": "1.0", "y": "1.0"}, {"x": "-0.295598", "y": "1.382976"}]),
    # A quartic with no rational root that splits into two quadratics over
    # the rationals: four square roots, found by factoring.
    ("quartic-two-quadratics",
     "solve symbolically for x: x^4 - 5*x^2 + 6 = 0",
     [{"x": "-1.414214"}, {"x": "1.414214"}, {"x": "-1.732051"},
      {"x": "1.732051"}]),
    # An irreducible quartic with four real roots (Eisenstein at 2).
    ("quartic-irreducible",
     "solve symbolically for x: x^4 - 4*x^2 + 2 = 0",
     [{"x": "-1.847759"}, {"x": "-0.765367"}, {"x": "0.765367"},
      {"x": "1.847759"}]),
)

#: ``(id, question, [branch, ...])``.
RADICAL: Tuple[Tuple[str, str, List[Dict[str, str]]], ...] = (
    # Phase 103's declared nested-radical refusal, now owed four branches.
    ("biquadratic-sum-product",
     "solve symbolically for u, v in terms of a, b: u^2 + v^2 = a; u*v = b",
     [{"u": "(sqrt(a + 2*b) + sqrt(a - 2*b))/2",
       "v": "(sqrt(a + 2*b) - sqrt(a - 2*b))/2"},
      {"u": "(sqrt(a + 2*b) - sqrt(a - 2*b))/2",
       "v": "(sqrt(a + 2*b) + sqrt(a - 2*b))/2"},
      {"u": "(-sqrt(a + 2*b) + sqrt(a - 2*b))/2",
       "v": "(-sqrt(a + 2*b) - sqrt(a - 2*b))/2"},
      {"u": "(-sqrt(a + 2*b) - sqrt(a - 2*b))/2",
       "v": "(-sqrt(a + 2*b) + sqrt(a - 2*b))/2"}]),
    # A biquadratic whose constant is not a square: a genuine tower.
    ("biquadratic-tower",
     "solve symbolically for x in terms of p, q: x^4 - 2*p*x^2 + q = 0",
     [{"x": "sqrt(p + sqrt(p^2 - q))"}, {"x": "-sqrt(p + sqrt(p^2 - q))"},
      {"x": "sqrt(p - sqrt(p^2 - q))"}, {"x": "-sqrt(p - sqrt(p^2 - q))"}]),
    # A quadratic whose coefficients hold a square root, with a
    # discriminant free of it.
    ("radical-coefficient",
     "solve symbolically for x, y in terms of a: x^2 = a; y^2 - x*y - a = 0",
     [{"x": "sqrt(a)", "y": "(sqrt(a) + sqrt(5*a))/2"},
      {"x": "sqrt(a)", "y": "(sqrt(a) - sqrt(5*a))/2"},
      {"x": "-sqrt(a)", "y": "(-sqrt(a) + sqrt(5*a))/2"},
      {"x": "-sqrt(a)", "y": "(-sqrt(a) - sqrt(5*a))/2"}]),
    # Phase 103's declared cubic refusal: Cardano's formula, the only real
    # root when 4*p^3 + 27*q^2 > 0 (the sample points are taken there).
    ("cardano-depressed",
     "solve symbolically for x in terms of p, q: x^3 + p*x = q",
     [{"x": "cbrt(q/2 + sqrt(q^2/4 + p^3/27)) + "
            "cbrt(q/2 - sqrt(q^2/4 + p^3/27))"}]),
)

#: ``(id, question, refusal code)``.
REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("quintic-in-letters", "solve symbolically for x: x^5 + p*x = q",
     "NONLINEAR"),
    ("quartic-no-real-root", "solve symbolically for x: x^4 + x^2 + 1 = 0",
     "NO_REAL_ROOT"),
    ("cubic-no-real-pair",
     "solve symbolically for x, y: x^2 + y^2 = -1; y = x^3", "NO_REAL_ROOT"),
    ("cubic-family", "solve symbolically for x, y: x^3 + x*y = 1",
     "UNDERDETERMINED"),
)

#: ``(id, question, branches the default answer must have)``.
DUAL: Tuple[Tuple[str, str, int], ...] = (
    ("circle-and-line",
     "solve symbolically for x, y in terms of r, m: x^2 + y^2 = r^2; y = m*x",
     2),
    ("kinetic-energy",
     "solve symbolically for v in terms of m, E: E = (1/2)*m*v^2", 2),
    ("pendulum",
     "solve symbolically for T in terms of L, g: T^2 = 4*pi^2*L/g", 2),
    ("hidden-unknown",
     "solve symbolically for x in terms of a: z^2 = a; x = 2*z", 2),
    ("two-squares",
     "solve symbolically for x, y: x^2 + y^2 = 4; x^2 - y^2 = 1", 4),
    ("square-root-of-four", "solve symbolically for x: x^2 = 4", 2),
)

#: Planted batteries of two conics through a rational point: Phase 103's
#: own seed, then one fresh seed declared here.
BATTERY_SEEDS: Tuple[int, ...] = (10301, 10401)

#: Random integer cubics with no rational root: ``(count, seed)``.
CUBIC_BATTERY: Tuple[int, int] = (40, 10402)

MARKS: Tuple[Tuple[str, str], ...] = (
    ("K1", "every system of ALGEBRAIC answered with exactly the declared "
           "branches: each real root found once, none added"),
    ("K2", "every system of RADICAL answered with exactly the declared "
           "branches"),
    ("K3", "every system of REFUSALS refused with the declared code"),
    ("K4", "every answered reading of ALGEBRAIC, RADICAL and DUAL verifies "
           "by its column-3 script, and the script of the same reading with "
           "the first target of every branch doubled is rejected"),
    ("K5", "every DUAL question: the default answer is the branch set with "
           "the declared number of branches, the substitution reading is "
           "kept beside it, and the substitution answer is one of the "
           "branches"),
    ("K6", "no regression: with Phase 104's additions off, every Phase 103 "
           "declared system and refusal reads exactly as Phase 103 left it; "
           "with them on, every Phase 98 reading without a positive root or "
           "a hidden unknown is unchanged, and every Phase 103 answered "
           "system keeps its branch set"),
    ("K7", "both planted batteries: 0 wrong (a failed script or a lost "
           "planted point) and the planted point found in at least 45 of 60 "
           "each"),
    ("K8", "the cubic battery: each of the 40 cubics answered with three "
           "branches when its discriminant is positive and one when it is "
           "negative, every script verified"),
    ("K9", "a Lean file proves what the additions rest on (Cardano's root "
           "and its uniqueness when 4p^3 + 27q^2 > 0, the biquadratic's "
           "four branches, the even quartic's factorisation, a cubic with no "
           "rational root is irreducible, a sign change brackets a root) "
           "with no sorry"),
)
