"""``glm_universal.evaluation.stepwise_two_cases`` -- round two of the
stepwise planner: the declared corpus.

The declared corpus of ``studies/STEPWISE_TWO_STUDY.md`` (Phase 73), written
and committed before any code of the round.  Every expected answer was worked
by hand from the register values the planner already reads (the element
table), from the axioms of the ten formula wheels
(:data:`glm_universal.engineering.wheels.WHEELS`) under the junction table of
:mod:`glm_universal.engineering.union`, and from the exact definitions of the
units named (the SI prefixes, the 1959 yard and pound, the hour).

Round one (Phase 72, ``studies/STEPWISE_PLANNER_STUDY.md`` §4.1) found four
questions it could not read: *how many more*, parity, averages, and givens
written with units.  Its §6 also named register values feeding a wheel
derivation.  This corpus is those, and nothing else:

* :data:`FRAME_CASES` -- the three frames the leaves lacked, over register
  values: *how many more ... than*, *is ... odd / even*, *the average of*.
* :data:`UNIT_CASES` -- goal questions whose givens (and targets) carry
  units, read through a declared exact unit table and converted into the
  coherent SI unit of each wheel quantity before the wheels are read.
* :data:`REGISTER_CASES` -- goal questions a given of which is a register
  value (*temperature = the melting point of iron*), carried into SI through
  the declared scale table of Phase 55 and fed to the wheel derivation.
* :data:`NARRATIVE_CASES` -- the narrative mode over both.
* :data:`FOLLOW_UP_CASES` -- ``then ...`` over a round-two chain.

An expected verdict is ``("ANSWER", value)``, ``("AMBIGUOUS",)`` or
``("REFUSED", NAME)``; a value is written as round one writes it (``n``,
``n/d``, ``True`` / ``False``, ``prime`` / ``not prime``).  A value asked
``in <unit>`` is stated in that unit; otherwise in the coherent SI unit.
"""

from __future__ import annotations

from typing import Dict, Tuple

__all__ = ["FRAME_CASES", "UNIT_CASES", "REGISTER_CASES", "NARRATIVE_CASES",
           "ORIGINAL_UNIT_CASES", "ORIGINAL_REGISTER_CASES",
           "ORIGINAL_NARRATIVE_CASES",
           "FOLLOW_UP_CASES", "NEW_REFUSAL_NAMES", "COUNT_NOUNS",
           "NAIVE_WRONG_AT_LEAST", "NAIVE_REFUSALS_ANSWERED_AT_LEAST"]

#: The named refusals this round adds to round one's.
NEW_REFUSAL_NAMES: Tuple[str, ...] = (
    "DIFFERENCE_REVERSED",  # "how many more A than B" where A has fewer
    "UNKNOWN_UNIT",         # a unit the declared table does not hold
    "UNIT_MISMATCH",        # a unit (or scale) of another dimension
    "UNIT_INEXACT",         # a unit whose SI factor is not an exact rational
    "OFFSET_UNIT",          # a unit with an offset (degrees Celsius)
    "SCALE_UNDECLARED",     # a register value on no declared scale
)

#: *How many more X does A have than B*: the count nouns the frame reads,
#: each mapped to the register phrase that counts it.  Declared, not
#: inferred: the number of protons is the atomic number by definition.
COUNT_NOUNS: Dict[str, str] = {
    "protons": "atomic number",
}

#: Mark T4: the *strip the units* control must answer wrongly at least this
#: many of the answered unit and register cases ...
NAIVE_WRONG_AT_LEAST = 5
#: ... and answer at least this many of the declared unit refusals.
NAIVE_REFUSALS_ANSWERED_AT_LEAST = 4

Verdict = Tuple[str, ...]

# (id, question, expected verdict)
FRAME_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("t01", "how many more protons does iron have than carbon",
     ("ANSWER", "20")),
    ("t02", "how many more protons does gold have than copper",
     ("ANSWER", "50")),
    ("t03", "how many more protons does carbon have than iron",
     ("REFUSED", "DIFFERENCE_REVERSED")),
    ("t04", "how much larger is the atomic number of gold than the atomic "
            "number of iron", ("ANSWER", "53")),
    ("t05", "how much higher is the melting point of iron than the melting "
            "point of copper", ("ANSWER", "45323/100")),
    ("t06", "how much higher is the melting point of copper than the "
            "melting point of iron", ("REFUSED", "DIFFERENCE_REVERSED")),
    ("t07", "is the atomic number of gold odd", ("ANSWER", "True")),
    ("t08", "is the atomic number of iron even", ("ANSWER", "True")),
    ("t09", "is the atomic number of carbon odd", ("ANSWER", "False")),
    ("t10", "is the atomic weight of carbon even",
     ("REFUSED", "NOT_AN_INTEGER")),
    ("t11", "what is the average of the atomic numbers of carbon, nitrogen "
            "and oxygen", ("ANSWER", "7")),
    ("t12", "what is the mean of the atomic numbers of iron and copper",
     ("ANSWER", "55/2")),
    ("t13", "what is the average of the melting points of iron, copper and "
            "gold", ("ANSWER", "45061/30")),
    ("t14", "what is the average of the atomic number of iron and 30",
     ("ANSWER", "28")),
    ("t15", "how many more protons does iron have than carbon, then is it "
            "prime", ("ANSWER", "not prime")),
    ("t16", "what is the average of the atomic numbers of sodium and "
            "chlorine, then is it odd", ("ANSWER", "False")),
    ("t17", "how many more neutrons does iron have than carbon",
     ("REFUSED", "UNKNOWN_STEP")),
    ("t18", "is the atomic number of iron plus the atomic number of carbon "
            "odd", ("ANSWER", "False")),
    ("t19", "what is the average of the atomic numbers of iron and "
            "unobtainium", ("REFUSED", "UNKNOWN_STEP")),
    ("t20", "how many more protons does gold have than iron, then halve it",
     ("ANSWER", "53/2")),
    ("t21", "how much lower is the melting point of copper than the melting "
            "point of iron", ("ANSWER", "45323/100")),
)

# (id, question, expected verdict, the quantities a correct answer stitches)
ORIGINAL_UNIT_CASES: Tuple[Tuple[str, str, Verdict, Tuple[str, ...]], ...] = (
    ("u01", "given voltage = 12 volts and resistance = 4 ohms, what is the "
            "power", ("ANSWER", "36"), ("current",)),
    ("u02", "given voltage = 12 kilovolts and current = 2 milliamperes, what "
            "is the power", ("ANSWER", "24"), ()),
    ("u03", "given voltage = 12 volts and resistance = 4 kilohms, what is the "
            "current in milliamperes", ("ANSWER", "3"), ()),
    ("u04", "given mass = 2 kilograms and velocity = 3 metres per second, "
            "what is the momentum", ("ANSWER", "6"), ()),
    ("u05", "given mass = 500 grams and velocity = 36 kilometres per hour, "
            "what is the energy", ("ANSWER", "25"), ()),
    ("u06", "given force = 12 newtons and area = 3 square metres, what is the "
            "pressure in kilopascals", ("ANSWER", "1/250"), ()),
    ("u07", "given power = 2 kilowatts and voltage = 250 volts, what is the "
            "resistance", ("ANSWER", "125/4"), ("current",)),
    ("u08", "given frequency = 5 kilohertz and wavelength = 2 millimetres, "
            "what is the wave speed", ("ANSWER", "10"), ()),
    ("u09", "given mass = 2 pounds and velocity = 3 metres per second, what "
            "is the momentum", ("ANSWER", "136077711/50000000"), ()),
    ("u10", "given voltage = 12 metres and resistance = 4 ohms, what is the "
            "power", ("REFUSED", "UNIT_MISMATCH"), ()),
    ("u11", "given voltage = 12 zorks and resistance = 4, what is the power",
     ("REFUSED", "UNKNOWN_UNIT"), ()),
    ("u12", "given angular velocity = 60 revolutions per minute and torque = "
            "5 newton metres, what is the power",
     ("REFUSED", "UNIT_INEXACT"), ()),
    ("u13", "given mass = 2 kilograms, specific heat capacity = 450 and "
            "temperature = 25 degrees celsius, what is the energy",
     ("REFUSED", "OFFSET_UNIT"), ()),
    ("u14", "given voltage = 12 kilovolts, current = 2 amperes and resistance "
            "= 4 ohms, what is the power",
     ("REFUSED", "INCONSISTENT_GIVENS"), ()),
    ("u15", "given voltage = 12 volts and resistance = 4 ohms, what is the "
            "power in metres", ("REFUSED", "UNIT_MISMATCH"), ()),
    ("u16", "given charge = 6 millicoulombs and voltage = 3 volts, what is "
            "the energy in millijoules", ("ANSWER", "9"), ("capacitance",)),
    ("u17", "given voltage = 12 volts and resistance = 4, what is the power",
     ("ANSWER", "36"), ("current",)),
    ("u18", "given voltage = 1.5 volts and current = 3 amperes, what is the "
            "power", ("ANSWER", "9/2"), ()),
)

# (id, question, expected verdict, the quantities a correct answer stitches)
ORIGINAL_REGISTER_CASES: Tuple[Tuple[str, str, Verdict, Tuple[str, ...]],
                              ...] = (
    ("g01", "given mass = 2, specific heat capacity = 450 and temperature = "
            "the melting point of iron, what is the energy",
     ("ANSWER", "1629900"), ()),
    ("g02", "given energy = 3622 and temperature = the melting point of iron, "
            "what is the entropy", ("ANSWER", "2"), ()),
    ("g03", "given mass = 2, specific heat capacity = 450 and temperature = "
            "the melting point of iron, what is the entropy",
     ("ANSWER", "900"), ("energy",)),
    ("g04", "given frequency = 5 and wavelength = the atomic radius of iron, "
            "what is the wave speed", ("ANSWER", "97/100000000000"), ()),
    ("g05", "given temperature = the boiling point of nitrogen and entropy = "
            "2, what is the energy", ("ANSWER", "3868/25"), ()),
    ("g06", "given mass = the atomic weight of iron and velocity = 3, what is "
            "the momentum", ("REFUSED", "UNIT_INEXACT"), ()),
    ("g07", "given density = the density of gold and volume = 2, what is the "
            "mass", ("REFUSED", "UNKNOWN_QUANTITY"), ()),
    ("g08", "given mass = 2, specific heat capacity = 450 and temperature = "
            "the melting point of unobtainium, what is the energy",
     ("REFUSED", "UNKNOWN_STEP"), ()),
    ("g09", "given temperature = the atomic number of iron and entropy = 2, "
            "what is the energy", ("REFUSED", "SCALE_UNDECLARED"), ()),
    ("g10", "given temperature = the melting point of iron, what is the "
            "energy", ("REFUSED", "NO_DERIVATION"), ()),
    ("g11", "given mass = 3 kilograms, specific heat capacity = 450 and "
            "temperature = the boiling point of oxygen, what is the energy in "
            "kilojoules", ("ANSWER", "12177/100"), ()),
    ("g12", "given temperature = the melting point of iron, energy = 3622 and "
            "entropy = 3, what is the mass",
     ("REFUSED", "INCONSISTENT_GIVENS"), ()),
    ("g13", "given the melting point of iron and entropy = 2, what is the "
            "energy", ("ANSWER", "3622"), ()),
    ("g14", "given the atomic radius of iron and frequency = 5, what is the "
            "wave speed", ("REFUSED", "UNKNOWN_QUANTITY"), ()),
)

# (id, question, expected verdict, expected values by base name -- in the
#  unit asked for, the order the asked quantities are taken in, stitched)
ORIGINAL_NARRATIVE_CASES: Tuple[Tuple[str, str, Verdict, Dict[str, str],
                             Tuple[str, ...], Tuple[str, ...]], ...] = (
    ("m01", "given voltage = 12 volts and resistance = 4 kilohms, find the "
            "power in milliwatts, then the current in milliamperes",
     ("ANSWER",), {"power": "36", "current": "3"}, ("current", "power"), ()),
    ("m02", "given mass = 2, specific heat capacity = 450 and temperature = "
            "the melting point of iron, find the entropy, then the energy",
     ("ANSWER",), {"entropy": "900", "energy": "1629900"},
     ("energy", "entropy"), ()),
)

# ---------------------------------------------------------------------------
# Amendments (Phase 86, ``studies/MEASURANDS_STUDY.md``).  The declared
# verdicts above are kept as written in Phase 73 (``ORIGINAL_*``).  Five of
# them read a temperature level as a temperature difference, and the kinds
# of quantity declared in Phase 86 refuse that; the verdicts measured from
# Phase 86 on are the amended ones, each with its reason in
# ``glm_universal.evaluation.measurand_cases.AMENDED``.  Nothing else moves.
# ---------------------------------------------------------------------------

def _amended(cid: str) -> Verdict:
    from .measurand_cases import AMENDED
    return AMENDED[("stepwise_two_cases", cid)][0]


def _amend(cases):
    from .measurand_cases import AMENDED
    out = []
    for case in cases:
        if ("stepwise_two_cases", case[0]) in AMENDED:
            want = _amended(case[0])
            if len(case) == 6:                  # a narrative case
                case = (case[0], case[1], want[:1], {}, (), ())
            else:
                case = (case[0], case[1], want, ())
        out.append(case)
    return tuple(out)


UNIT_CASES = _amend(ORIGINAL_UNIT_CASES)
REGISTER_CASES = _amend(ORIGINAL_REGISTER_CASES)
NARRATIVE_CASES = _amend(ORIGINAL_NARRATIVE_CASES)

# (id, first turn, second turn, expected verdict of the second turn)
FOLLOW_UP_CASES: Tuple[Tuple[str, str, str, Verdict], ...] = (
    ("v01", "how many more protons does gold have than copper",
     "then is it even", ("ANSWER", "True")),
    ("v02", "given voltage = 12 volts and resistance = 4 ohms, what is the "
            "power", "then divide it by 4", ("ANSWER", "9")),
)
