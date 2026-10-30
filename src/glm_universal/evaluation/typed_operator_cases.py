"""``glm_universal.evaluation.typed_operator_cases`` -- typed operators: the
declared corpus.

The declared corpus of ``studies/TYPED_OPERATORS_STUDY.md`` (Phase 90, round 3
of the order of work, candidate F), written and committed before any code of
the round.  Every expected answer was worked by hand, in exact fractions, from
two conventions and nothing else:

* **Complex power** (IEC 60050-131, IEEE Std 1459-2010): with RMS phasors
  ``V`` and ``I`` (Gaussian rationals), the complex power is
  ``S = V * conj(I)``; the real (active) power is ``P = Re S`` in watts, the
  reactive power ``Q = Im S`` in vars, the apparent power ``|S| =
  sqrt(P^2 + Q^2)`` in volt-amperes, and the power factor ``P / |S|``,
  *lagging* when ``Q > 0`` (an inductive load: the current lags the
  voltage), *leading* when ``Q < 0``, *unity* when ``Q = 0``.  Through an
  impedance ``Z``: ``S = |V|^2 / conj(Z) = |I|^2 Z``.  The watt, the var and
  the volt-ampere are one dimension and three kinds: the watt is used for
  real power only, the var for reactive power only, the volt-ampere for
  apparent and complex power only (IEC 60050-131-11-42/-44/-45, and the SI
  Brochure's note that special names mark the kind of quantity).
* **Vector operators** over three rational components: the work of a
  force over a displacement, and the power of a force at a velocity, are the
  *dot* product (a scalar, in joules or watts); the torque of a force about a
  point is the *cross* product ``r x F`` of the position with the force (a
  vector, in newton metres), and its magnitude is ``sqrt(|r x F|^2)``.

Monomial wheels (``power = voltage * current``, ``work = force *
displacement``, ``torque = force * distance``) multiply magnitudes and so
answer the apparent power for all three powers and ``|F| |d|`` for the work:
that is the naive control.

Three groups:

* :data:`PHASOR_CASES` -- complex, real, reactive and apparent power and the
  power factor, from phasors, from an impedance, or from two sides of the
  power triangle.
* :data:`KIND_CASES` -- the three powers' units as kind-restricted names.
* :data:`VECTOR_CASES` -- the dot product (work, mechanical power) against the
  cross product (torque).

An expected verdict is ``("ANSWER", value)`` (with a third field
``"lagging"``, ``"leading"`` or ``"unity"`` for a power factor),
``("AMBIGUOUS",)`` or ``("REFUSED", NAME)``.  A value is a ``Fraction``, a
complex ``("complex", re, im)``, a surd ``("surd", b, c)`` meaning
``b * sqrt(c)`` with ``c`` square-free, or a vector ``("vector", x, y, z)``.
Values are in the coherent unit unless a unit is asked for.
"""

from __future__ import annotations

from fractions import Fraction as F
from typing import Tuple

__all__ = ["PHASOR_CASES", "KIND_CASES", "VECTOR_CASES", "ALL_CASES",
           "NEW_REFUSAL_NAMES", "NAIVE_WRONG_AT_LEAST", "GRID"]

#: The named refusals this round adds.
NEW_REFUSAL_NAMES: Tuple[str, ...] = (
    "PF_SENSE_UNDECLARED",          # the sign of Q needs lagging / leading
    "POWER_TRIANGLE_VIOLATED",      # |P| or |Q| greater than |S|
    "POWER_FACTOR_OUT_OF_RANGE",    # a power factor outside [-1, 1]
    "VECTOR_LENGTH_MISMATCH",       # a cross product of unequal lengths
)

#: Mark T4: the naive (monomial) control must answer at least this many of
#: the answered phasor and vector cases, each wrongly.
NAIVE_WRONG_AT_LEAST = 12

#: Mark T7: the census grid -- every Gaussian integer ``a + bj`` with
#: ``|a|, |b| <= GRID`` for ``V`` and ``I``, and every integer vector with
#: components in ``[-GRID, GRID]`` (on a sparser sample) for ``r`` and ``F``.
GRID = 3

_V = "phasor voltage V = 120 + 0j V and phasor current I = 3 - 4j A"

PHASOR_CASES: Tuple[Tuple[str, str, tuple], ...] = (
    ("a01", f"With {_V}, what is the complex power?",
     ("ANSWER", ("complex", F(360), F(480)))),
    ("a02", f"With {_V}, what is the real power?", ("ANSWER", F(360))),
    ("a03", f"With {_V}, what is the reactive power?", ("ANSWER", F(480))),
    ("a04", f"With {_V}, what is the apparent power?", ("ANSWER", F(600))),
    ("a05", f"With {_V}, what is the power factor?",
     ("ANSWER", F(3, 5), "lagging")),
    ("a06", "With phasor voltage V = 10 + 10j V and phasor current "
            "I = 1 + 1j A, what is the reactive power?", ("ANSWER", F(0))),
    ("a07", "With phasor voltage V = 50 + 0j V and phasor current "
            "I = 1 + 2j A, what is the power factor?",
     ("ANSWER", ("surd", F(1, 5), 5), "leading")),
    ("a08", "With phasor voltage V = 50 + 0j V and phasor current "
            "I = 1 + 2j A, what is the apparent power?",
     ("ANSWER", ("surd", F(50), 5))),
    ("a09", "A phasor voltage V = 230 + 0j V is across an impedance "
            "Z = 30 + 40j ohm; what is the complex power?",
     ("ANSWER", ("complex", F(3174, 5), F(4232, 5)))),
    ("a10", "A phasor voltage V = 230 + 0j V is across an impedance "
            "Z = 30 + 40j ohm; what is the power factor?",
     ("ANSWER", F(3, 5), "lagging")),
    ("a11", "A phasor current I = 2 + 0j A flows through an impedance "
            "Z = 3 - 4j ohm; what is the reactive power?",
     ("ANSWER", F(-16))),
    ("a12", "Given real power = 300 W and reactive power = 400 var, what is "
            "the apparent power?", ("ANSWER", F(500))),
    ("a13", "Given real power = 300 W and reactive power = -400 var, what "
            "is the power factor?", ("ANSWER", F(3, 5), "leading")),
    ("a14", "Given apparent power = 500 VA and power factor = 3/5 lagging, "
            "what is the reactive power?", ("ANSWER", F(400))),
    ("a15", "Given apparent power = 500 VA and power factor = 0.6 leading, "
            "what is the reactive power?", ("ANSWER", F(-400))),
    ("a16", "Given apparent power = 500 VA and power factor = 3/5, what is "
            "the reactive power?", ("REFUSED", "PF_SENSE_UNDECLARED")),
    ("a17", "Given apparent power = 500 VA and power factor = 3/5, what is "
            "the real power?", ("ANSWER", F(300))),
    ("a18", "Given real power = 300 W and apparent power = 500 VA, what is "
            "the reactive power?", ("REFUSED", "PF_SENSE_UNDECLARED")),
    ("a19", "Given real power = 300 W and apparent power = 500 VA, lagging, "
            "what is the reactive power?", ("ANSWER", F(400))),
    ("a20", "Given real power = 600 W and apparent power = 500 VA, what is "
            "the power factor?", ("REFUSED", "POWER_TRIANGLE_VIOLATED")),
    ("a21", "Given apparent power = 500 VA and power factor = 6/5 lagging, "
            "what is the real power?", ("REFUSED", "POWER_FACTOR_OUT_OF_RANGE")),
    ("a22", f"With {_V}, what is the power?", ("AMBIGUOUS",)),
)

KIND_CASES: Tuple[Tuple[str, str, tuple], ...] = (
    ("k01", f"With {_V}, what is the reactive power in watts?",
     ("REFUSED", "KIND_MISMATCH")),
    ("k02", f"With {_V}, what is the apparent power in watts?",
     ("REFUSED", "KIND_MISMATCH")),
    ("k03", f"With {_V}, what is the real power in volt-amperes?",
     ("REFUSED", "KIND_MISMATCH")),
    ("k04", f"With {_V}, what is the real power in vars?",
     ("REFUSED", "KIND_MISMATCH")),
    ("k05", f"With {_V}, what is the reactive power in kilovars?",
     ("ANSWER", F(12, 25))),
    ("k06", f"With {_V}, what is the apparent power in kilovolt-amperes?",
     ("ANSWER", F(3, 5))),
    ("k07", "Given real power = 300 VA and reactive power = 400 var, what is "
            "the apparent power?", ("REFUSED", "KIND_MISMATCH")),
    ("k08", "Given real power = 300 kW and reactive power = 400 kvar, what "
            "is the apparent power in kVA?", ("ANSWER", F(500))),
    ("k09", f"With {_V}, what is the complex power in watts?",
     ("REFUSED", "KIND_MISMATCH")),
)

VECTOR_CASES: Tuple[Tuple[str, str, tuple], ...] = (
    ("v01", "A force F = (1, 2, 3) N acts over a displacement d = (4, 5, 6) "
            "m; what is the work?", ("ANSWER", F(32))),
    ("v02", "A force F = (0, 2, 0) N acts at position r = (1, 0, 0) m; what "
            "is the torque?", ("ANSWER", ("vector", F(0), F(0), F(2)))),
    ("v03", "A force F = (4, 5, 6) N acts at position r = (1, 2, 3) m; what "
            "is the torque?", ("ANSWER", ("vector", F(-3), F(6), F(-3)))),
    ("v04", "A force F = (4, 5, 6) N acts at position r = (1, 2, 3) m; what "
            "is the magnitude of the torque?", ("ANSWER", ("surd", F(3), 6))),
    ("v05", "A force F = (0, 4, 0) N acts at position r = (3, 0, 0) m; what "
            "is the magnitude of the torque?", ("ANSWER", F(12))),
    ("v06", "A force F = (1, 2, 3) N acts over a displacement d = (4, 5, 6) "
            "m; what is the work in newton metres?",
     ("REFUSED", "KIND_MISMATCH")),
    ("v07", "A force F = (4, 5, 6) N acts at position r = (1, 2, 3) m; what "
            "is the torque in joules?", ("REFUSED", "KIND_MISMATCH")),
    ("v08", "A force F = (2, 0, 0) N acts over a displacement d = (0, 3, 0) "
            "m; what is the work?", ("ANSWER", F(0))),
    ("v09", "A force F = (3, 0, 4) N acts at velocity v = (1, 2, 2) m/s; "
            "what is the power?", ("ANSWER", F(11))),
    ("v10", "A force F = (2, 4, 6) N acts at position r = (1, 2, 3) m; what "
            "is the torque?", ("ANSWER", ("vector", F(0), F(0), F(0)))),
    ("v11", "A force F = (3, 4, 5) N acts at position r = (1, 2) m; what is "
            "the torque?", ("REFUSED", "VECTOR_LENGTH_MISMATCH")),
    ("v12", "A force F = (1, 2) N acts over a displacement d = (3, 4) m; "
            "what is the work?", ("ANSWER", F(11))),
)

ALL_CASES = PHASOR_CASES + KIND_CASES + VECTOR_CASES
