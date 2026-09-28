"""``glm_universal.evaluation.stepwise_cases`` -- the stepwise planner's corpus.

The declared corpus of ``studies/STEPWISE_PLANNER_STUDY.md`` (Phase 72),
written and committed before any stepwise code.  Every expected answer was
worked by hand from the register values the planner already reads (the
element and molecule tables) and from the axioms of the ten formula wheels
(:data:`glm_universal.engineering.wheels.WHEELS`) under the junction table of
:mod:`glm_universal.engineering.union`.

* :data:`COMPOSITION_CASES` -- compound questions whose parts are questions
  the planner answers one at a time: an arithmetic or predicate step over
  sub-answers, chained with ``then`` and ``it``.
* :data:`GOAL_CASES` -- ``given A = x and B = y, what is T`` over the wheels:
  the steps between the givens and the target are not asked for and must be
  found (stitched) by searching forwards from the givens and backwards from
  the target.
* :data:`NARRATIVE_CASES` -- the same, with the steps asked for in an order
  that cannot be taken as written: a step that cannot be taken yet is
  deferred, a later one is taken first, and gaps are stitched.
* :data:`FOLLOW_UP_CASES` -- two-turn conversations: a ``then ...`` turn that
  extends the last chain, and ``why?`` which replays it.

An expected verdict is ``("ANSWER", value)``, ``("AMBIGUOUS",)`` or
``("REFUSED", NAME)``.  A value is an exact rational written ``n`` or
``n/d``, ``prime`` / ``not prime``, ``True`` / ``False``, or, for *which is
larger, A or B*, the winning phrase.
"""

from __future__ import annotations

from typing import Dict, Tuple

__all__ = ["COMPOSITION_CASES", "GOAL_CASES", "NARRATIVE_CASES",
           "FOLLOW_UP_CASES", "REFUSAL_NAMES", "MAX_OPERATORS",
           "MAX_DERIVATIONS"]

#: The named refusals of the stepwise layer.
REFUSAL_NAMES: Tuple[str, ...] = (
    "UNKNOWN_STEP",          # a part the planner does not answer
    "NOT_A_NUMBER",          # a part answered with something not a number
    "NOT_AN_INTEGER",        # an integer operation given a non-integer
    "DIVISION_BY_ZERO",      # a quotient, or an axiom solved through a zero
    "TOO_MANY_READINGS",     # more operator words than the reading budget
    "UNKNOWN_QUANTITY",      # a given or target named in no wheel
    "NO_DERIVATION",         # no chain of axiom steps reaches the target
    "INCONSISTENT_GIVENS",   # a given re-derived from the others disagrees
    "DERIVATIONS_DISAGREE",  # two derivations of the target disagree
)

#: More operator words than this in one question is refused
#: ``TOO_MANY_READINGS`` rather than bracketed every way.
MAX_OPERATORS = 5

#: More derivation trees than this for one target is refused rather than
#: enumerated.
MAX_DERIVATIONS = 512

Verdict = Tuple[str, ...]

# (id, question, expected verdict)
COMPOSITION_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("c01", "what is the atomic number of iron plus the atomic number of "
            "oxygen", ("ANSWER", "34")),
    ("c02", "what is the atomic number of iron times 2", ("ANSWER", "52")),
    ("c03", "what is the atomic weight of carbon plus the atomic weight of "
            "oxygen", ("ANSWER", "2801/100")),
    ("c04", "what is the atomic weight of iron divided by the atomic weight "
            "of oxygen", ("ANSWER", "55840/15999")),
    ("c05", "is the atomic number of iron prime", ("ANSWER", "not prime")),
    ("c06", "is the atomic number of nitrogen prime", ("ANSWER", "prime")),
    ("c07", "what is the gcd of the atomic number of iron and the atomic "
            "number of oxygen", ("ANSWER", "2")),
    ("c08", "what is the lcm of the atomic numbers of carbon and oxygen",
     ("ANSWER", "24")),
    ("c09", "is the atomic weight of carbon larger than the atomic weight of "
            "nitrogen", ("ANSWER", "False")),
    ("c10", "which is larger, the melting point of iron or the melting point "
            "of copper", ("ANSWER", "the melting point of iron")),
    ("c11", "what is 2 times the atomic number of carbon plus the atomic "
            "number of oxygen", ("AMBIGUOUS",)),
    ("c12", "what is the atomic number of carbon plus the atomic number of "
            "oxygen plus the atomic number of iron", ("ANSWER", "40")),
    ("c13", "what is the atomic number of carbon, then is it prime",
     ("ANSWER", "not prime")),
    ("c14", "what is the atomic number of iron minus the atomic number of "
            "carbon, then is it prime", ("ANSWER", "not prime")),
    ("c15", "convert 3 miles to metres, then divide it by 1000",
     ("ANSWER", "75438/15625")),
    ("c16", "what is the molar mass of water times 2", ("ANSWER", "3603/100")),
    ("c17", "what is the square of the atomic number of iron",
     ("ANSWER", "676")),
    ("c18", "what is the sum of the atomic numbers of sodium and chlorine",
     ("ANSWER", "28")),
    ("c19", "what is the gcd of the atomic number of iron plus 4 and 12",
     ("ANSWER", "6")),
    ("c20", "what is the atomic number of gold minus the atomic number of "
            "copper minus the atomic number of carbon", ("AMBIGUOUS",)),
    ("c21", "what is the density of gold times 1000", ("ANSWER", "19282")),
    ("c22", "what is the atomic number of copper, then multiply it by 3, "
            "then is it prime", ("ANSWER", "not prime")),
    ("c23", "is the melting point of iron greater than the boiling point of "
            "nitrogen", ("ANSWER", "True")),
    ("c24", "what is the ratio of the atomic number of iron to the atomic "
            "number of carbon", ("ANSWER", "13/3")),
    # -- declared refusals ---------------------------------------------------
    ("r01", "what is the atomic number of iron plus the atomic number of "
            "unobtainium", ("REFUSED", "UNKNOWN_STEP")),
    ("r02", "is the atomic weight of iron prime", ("REFUSED",
                                                   "NOT_AN_INTEGER")),
    ("r03", "what is the atomic number of iron divided by 0",
     ("REFUSED", "DIVISION_BY_ZERO")),
    ("r04", "what is the atomic number of iron plus the symbol of iron",
     ("REFUSED", "NOT_A_NUMBER")),
    ("r05", "what is the gcd of the atomic weight of carbon and 6",
     ("REFUSED", "NOT_AN_INTEGER")),
    ("r06", "what is the atomic number of iron, then is it prime, then add 1 "
            "to it", ("REFUSED", "NOT_A_NUMBER")),
)

# (id, question, expected verdict, the steps a correct answer must stitch --
#  the quantities derived between the givens and the target, by base name)
GOAL_CASES: Tuple[Tuple[str, str, Verdict, Tuple[str, ...]], ...] = (
    ("g01", "given voltage = 12 and resistance = 4, what is the power",
     ("ANSWER", "36"), ("current",)),
    ("g02", "given voltage = 12 and current = 2, what is the resistance",
     ("ANSWER", "6"), ()),
    ("g03", "given power = 60 and voltage = 120, what is the resistance",
     ("ANSWER", "240"), ("current",)),
    ("g04", "given mass = 2 and velocity = 3, what is the momentum",
     ("ANSWER", "6"), ()),
    ("g05", "given mass = 2 and velocity = 3, what is the energy",
     ("ANSWER", "9"), ()),
    ("g06", "given pressure = 5, area = 2 and velocity = 3, what is the power",
     ("ANSWER", "30"), ("force",)),
    ("g07", "given torque = 4 and moment of inertia = 2, what is the angular "
            "acceleration", ("ANSWER", "2"), ()),
    ("g08", "given frequency = 5 and wavelength = 2, what is the wave speed",
     ("ANSWER", "10"), ()),
    ("g09", "given charge = 6 and voltage = 3, what is the energy",
     ("ANSWER", "9"), ("capacitance",)),
    ("g10", "given voltage = 12, current = 2 and resistance = 4, what is the "
            "power", ("REFUSED", "INCONSISTENT_GIVENS"), ()),
    ("g11", "given voltage = 12, resistance = 4 and power = 20, what is the "
            "current", ("REFUSED", "INCONSISTENT_GIVENS"), ()),
    ("g12", "given mass = 2, velocity = 3, capacitance = 1 and voltage = 2, "
            "what is the energy", ("AMBIGUOUS",), ()),
    ("g13", "given mass = 2, what is the power", ("REFUSED", "NO_DERIVATION"),
     ()),
    ("g14", "given voltage = 12 and flux capacitance = 3, what is the power",
     ("REFUSED", "UNKNOWN_QUANTITY"), ()),
    ("g15", "given energy = 8 and mass = 4, what is the velocity",
     ("REFUSED", "NO_DERIVATION"), ()),
    ("g16", "given power = 100 and angular velocity = 20, what is the torque",
     ("ANSWER", "5"), ()),
    ("g17", "given force = 12 and area = 3, what is the pressure",
     ("ANSWER", "4"), ()),
    ("g18", "given volume flow rate = 6, area = 2 and mass = 5, what is the "
            "momentum", ("ANSWER", "15"), ("velocity",)),
    ("g19", "given wave speed = 340 and wavelength = 2, what is the angular "
            "velocity", ("REFUSED", "NO_DERIVATION"), ()),
    ("g20", "given current = 3 and resistance = 5, what is the power",
     ("ANSWER", "45"), ("voltage",)),
    ("g21", "given voltage = 12 and current = 0, what is the resistance",
     ("REFUSED", "DIVISION_BY_ZERO"), ()),
)

# (id, question, expected verdict, expected values by base name,
#  the order the asked quantities are taken in, the stitched quantities)
NARRATIVE_CASES: Tuple[Tuple[str, str, Verdict, Dict[str, str],
                             Tuple[str, ...], Tuple[str, ...]], ...] = (
    ("n01", "given voltage = 12 and resistance = 4, find the power, then the "
            "current", ("ANSWER",), {"power": "36", "current": "3"},
     ("current", "power"), ()),
    ("n02", "given voltage = 12 and resistance = 4, find the current, then "
            "the power", ("ANSWER",), {"current": "3", "power": "36"},
     ("current", "power"), ()),
    ("n03", "given mass = 2 and velocity = 3, find the energy, then the "
            "momentum", ("ANSWER",), {"energy": "9", "momentum": "6"},
     ("energy", "momentum"), ()),
    ("n04", "given pressure = 5, area = 2 and velocity = 3, find the power",
     ("ANSWER",), {"power": "30"}, ("power",), ("force",)),
    ("n05", "given power = 60 and voltage = 120, find the resistance, then "
            "the current", ("ANSWER",), {"resistance": "240",
                                         "current": "1/2"},
     ("current", "resistance"), ()),
    ("n06", "given voltage = 12 and resistance = 4, find the power, then the "
            "flux", ("REFUSED", "UNKNOWN_QUANTITY"), {}, (), ()),
)

# (id, first turn, second turn, expected verdict of the second turn)
FOLLOW_UP_CASES: Tuple[Tuple[str, str, str, Verdict], ...] = (
    ("f01", "what is the atomic number of iron plus the atomic number of "
            "oxygen", "then is it prime", ("ANSWER", "not prime")),
    ("f02", "what is the atomic number of copper times 3",
     "then divide it by 29", ("ANSWER", "3")),
    ("f03", "given voltage = 12 and resistance = 4, what is the power",
     "why?", ("ANSWER", "36")),
    ("f04", "what is the atomic number of iron, then is it prime",
     "then add 1 to it", ("REFUSED", "NOT_A_NUMBER")),
)
