"""``glm_universal.evaluation.nonlinear_cases`` -- the declared cases of
Phase 103, nonlinear elimination (the first item of
``studies/SYMBOLIC_PARAMETERS_STUDY.md`` §6: "a system where an unknown
appears in a product or in two powers is refused ``NONLINEAR``, even when it
has a closed solution").

Written and committed **before** any code of the round.  The scorer is
:mod:`glm_universal.runtime.nonlinear_report`.

* :data:`SYSTEMS` -- systems the substitution layer of Phase 98 refuses
  ``NONLINEAR``, each with **every** real solution derived by hand, as a
  list of branches (one dictionary per solution).  A branch is matched as an
  identity of rational functions in which ``sqrt(R)`` is a formal generator
  with ``sqrt(R)^2 = R``; the radicand is written primitive, with its square
  factors pulled out (``sqrt(v^2 - 2*g*h)``, not ``sqrt(4*v^2 - 8*g*h)``).
  The machine must give exactly these branches: one missing is a lost
  solution, one more is a wrong answer.
* :data:`REFUSALS` -- systems the new layer must still refuse, with the code.
* :data:`MARKS` -- the ladder.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

__all__ = ["SYSTEMS", "REFUSALS", "MARKS"]

Branch = Dict[str, str]

#: ``(id, question, [branch, ...])``.
SYSTEMS: Tuple[Tuple[str, str, List[Branch]], ...] = (
    # Phase 98's two NONLINEAR refusals, now owed an answer.
    ("quadratic",
     "solve symbolically for x: x^2 + x = c",
     [{"x": "(-1 + sqrt(4*c + 1))/2"}, {"x": "(-1 - sqrt(4*c + 1))/2"}]),
    ("product-of-unknowns",
     "solve symbolically for x, y: x*y = 1; x + y = 3",
     [{"x": "(3 + sqrt(5))/2", "y": "(3 - sqrt(5))/2"},
      {"x": "(3 - sqrt(5))/2", "y": "(3 + sqrt(5))/2"}]),
    # A product of unknowns in letters.
    ("sum-and-product",
     "solve symbolically for x, y: x*y = p; x + y = s",
     [{"x": "(s + sqrt(s^2 - 4*p))/2", "y": "(s - sqrt(s^2 - 4*p))/2"},
      {"x": "(s - sqrt(s^2 - 4*p))/2", "y": "(s + sqrt(s^2 - 4*p))/2"}]),
    # Momentum and kinetic energy together: the classic elastic collision.
    ("elastic-collision",
     "solve symbolically for v1, v2 in terms of m1, m2, u: "
     "m1*v1 + m2*v2 = m1*u; m1*v1^2 + m2*v2^2 = m1*u^2",
     [{"v1": "u", "v2": "0"},
      {"v1": "u*(m1 - m2)/(m1 + m2)", "v2": "2*m1*u/(m1 + m2)"}]),
    # The time at which a thrown body is at height h.
    ("projectile-time",
     "solve symbolically for t in terms of v, g, h: h = v*t - g*t^2/2",
     [{"t": "(v + sqrt(v^2 - 2*g*h))/g"},
      {"t": "(v - sqrt(v^2 - 2*g*h))/g"}]),
    # A rectangle of given area and perimeter.
    ("rectangle",
     "solve symbolically for l, w in terms of A, P: l*w = A; 2*l + 2*w = P",
     [{"l": "(P + sqrt(P^2 - 16*A))/4", "w": "(P - sqrt(P^2 - 16*A))/4"},
      {"l": "(P - sqrt(P^2 - 16*A))/4", "w": "(P + sqrt(P^2 - 16*A))/4"}]),
    # A line through the origin meets a circle.
    ("circle-and-line",
     "solve symbolically for x, y in terms of r, m: x^2 + y^2 = r^2; y = m*x",
     [{"x": "r*sqrt(m^2 + 1)/(m^2 + 1)", "y": "m*r*sqrt(m^2 + 1)/(m^2 + 1)"},
      {"x": "-r*sqrt(m^2 + 1)/(m^2 + 1)",
       "y": "-m*r*sqrt(m^2 + 1)/(m^2 + 1)"}]),
    # A product isolated through an unknown coefficient, then a quartic
    # that splits over the rationals into four real roots.
    ("hyperbola-and-circle",
     "solve symbolically for x, y: x^2 + y^2 = 5; x*y = 2",
     [{"x": "1", "y": "2"}, {"x": "2", "y": "1"},
      {"x": "-1", "y": "-2"}, {"x": "-2", "y": "-1"}]),
    # A quartic with two rational real roots and a factor with none.
    ("parabola-and-circle",
     "solve symbolically for x, y: x^2 + y^2 = 2; y = x^2",
     [{"x": "1", "y": "1"}, {"x": "-1", "y": "1"}]),
    # No unknown can be isolated in either equation: an elimination by
    # resultant, whose back-substitution offers extraneous pairs that must
    # be discarded.
    ("two-conics",
     "solve symbolically for x, y: x^2 + y^2 = 13; x^2 - x*y + y^2 = 7",
     [{"x": "2", "y": "3"}, {"x": "3", "y": "2"},
      {"x": "-2", "y": "-3"}, {"x": "-3", "y": "-2"}]),
)

#: ``(id, question, refusal code)``.
REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("cubic-in-letters",
     "solve symbolically for x: x^3 + p*x = q", "NONLINEAR"),
    ("no-real-root",
     "solve symbolically for x: x^2 + 1 = 0", "NO_REAL_ROOT"),
    ("product-alone",
     "solve symbolically for x, y: x*y = 1", "UNDERDETERMINED"),
    ("nested-radical",
     "solve symbolically for u, v in terms of a, b: u^2 + v^2 = a; u*v = b",
     "NONLINEAR"),
    ("products-disagree",
     "solve symbolically for x, y: x*y = 1; x*y = 2", "INCONSISTENT"),
)

MARKS: Tuple[Tuple[str, str], ...] = (
    ("E1", "every system of SYSTEMS answered with exactly the declared "
           "branches (none lost, none added), each target an identity of "
           "rational functions with its declared expression"),
    ("E2", "every system of REFUSALS refused with the declared code"),
    ("E3", "every answered reading's column-3 script verifies, and rejects "
           "the same script with the first target of every branch altered"),
    ("E4", "no regression: every Phase 98 system and refusal other than the "
           "two NONLINEAR refusals reads exactly as before, and the Phase 98 "
           "report is unchanged when the new layer is switched off"),
    ("E5", "a planted battery: 60 random systems of two quadratic equations "
           "in two unknowns, each built to pass through a chosen rational "
           "point; every answered branch verified by its script (0 wrong), "
           "and the planted point among the branches of at least 45"),
    ("E6", "the substitution layer is untouched: the new layer runs only "
           "on a NONLINEAR refusal, and switching it off restores every "
           "Phase 98 refusal"),
    ("E7", "a Lean file proves what the layer rests on (the quadratic's two "
           "branches are its only roots, conjugation carries a branch to a "
           "branch, a common root makes the resultant vanish, the elastic "
           "collision's two branches are its only solutions) with no sorry"),
)
