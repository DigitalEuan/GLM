"""``glm_universal.evaluation.measurand_cases`` -- measurands: the declared
corpus.

The declared corpus of ``studies/MEASURANDS_STUDY.md`` (Phase 86), written
and committed before any code of the round.  Every expected answer was worked
from the SI Brochure (9th edition, 2019): the exact defining constants
``h = 6.62607015e-34 J s``, ``c = 299792458 m/s`` and
``e = 1.602176634e-19 C``; the kelvin and the degree Celsius
(``t / °C = T / K - 273.15``, and a Celsius *interval* equal to a kelvin);
the degree Fahrenheit (``T / K = (t_F / °F + 459.67) * 5/9``, an interval of
5/9 K); and the rules that restrict a special unit name to one kind of
quantity (the hertz only for periodic frequency, not angular velocity; the
radian per second for angular velocity; the newton metre for torque rather
than the joule).  The wheels are the ten formula wheels of
:data:`glm_universal.engineering.wheels.WHEELS`.

* :data:`KIND_CASES` -- a unit whose dimension matches the quantity but whose
  kind does not: refused ``KIND_MISMATCH``, and the same questions asked in
  the unit of the right kind, answered.
* :data:`TEMPERATURE_CASES` -- temperatures in degrees Celsius and
  Fahrenheit, read as a level or as a difference by the quantity they feed,
  and the three conflations refused: a level used as a difference, a
  difference used as a level, and one temperature used as both.
* :data:`CONSTANT_CASES` -- the defining constants of the SI supplied when
  the givens alone derive nothing.

An expected verdict is ``("ANSWER", value)`` or ``("REFUSED", NAME)``; a value
is in the coherent SI unit unless a unit is asked for.

:data:`AMENDED` lists every earlier declared case whose verdict this round
changes, with the reason; nothing else in the earlier corpora may move.
"""

from __future__ import annotations

from typing import Dict, Tuple

__all__ = ["KIND_CASES", "TEMPERATURE_CASES", "CONSTANT_CASES",
           "NEW_REFUSAL_NAMES", "AMENDED", "CONTROL_KIND_ANSWERS_AT_LEAST"]

Verdict = Tuple[str, ...]

#: The named refusals this round adds.
NEW_REFUSAL_NAMES: Tuple[str, ...] = (
    "KIND_MISMATCH",         # a unit of the right dimension, wrong kind
    "LEVEL_AS_DIFFERENCE",   # a temperature level fed to a difference
    "DIFFERENCE_AS_LEVEL",   # a temperature difference fed to a level
    "KIND_CONFLATION",       # one temperature read as level and difference
    "BELOW_ABSOLUTE_ZERO",   # a level below 0 K
)

#: The kinds-off control must answer at least this many of the declared
#: ``KIND_MISMATCH`` refusals (it answers them by dimension alone).
CONTROL_KIND_ANSWERS_AT_LEAST = 4

# (id, question, expected verdict)
KIND_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("k01", "given angular velocity = 50 hertz and moment of inertia = 2, "
            "what is the angular momentum", ("REFUSED", "KIND_MISMATCH")),
    ("k02", "given frequency = 50 radians per second and wavelength = 2, "
            "what is the wave speed", ("REFUSED", "KIND_MISMATCH")),
    ("k03", "given torque = 5 joules and angular velocity = 2, what is the "
            "power", ("REFUSED", "KIND_MISMATCH")),
    ("k04", "given energy = 10 newton metres and temperature = 5, what is the "
            "entropy", ("REFUSED", "KIND_MISMATCH")),
    ("k05", "given torque = 5 newton metres and angular velocity = 2 radians "
            "per second, what is the power", ("ANSWER", "10")),
    ("k06", "given frequency = 5 kilohertz and wavelength = 2 millimetres, "
            "what is the wave speed", ("ANSWER", "10")),
    ("k07", "given angular velocity = 4 radians per second and moment of "
            "inertia = 3, what is the angular momentum", ("ANSWER", "12")),
    ("k08", "given power = 10 watts and angular velocity = 2 radians per "
            "second, what is the torque in joules",
     ("REFUSED", "KIND_MISMATCH")),
    ("k09", "given power = 10 watts and angular velocity = 2 radians per "
            "second, what is the torque in newton metres", ("ANSWER", "5")),
    ("k10", "given energy = 3 kilojoules and temperature = 300 kelvins, what "
            "is the entropy", ("ANSWER", "10")),
)

# (id, question, expected verdict)
TEMPERATURE_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("t01", "given energy = 100 joules and temperature = 25 degrees celsius, "
            "what is the entropy", ("ANSWER", "2000/5963")),
    ("t02", "given entropy = 2 and temperature = 27 degrees celsius, what is "
            "the energy", ("ANSWER", "6003/10")),
    ("t03", "given mass = 2 kilograms, specific heat capacity = 450 and "
            "temperature change = 10 degrees celsius, what is the energy",
     ("ANSWER", "9000")),
    ("t04", "given mass = 2, specific heat capacity = 450 and temperature "
            "rise = 18 degrees fahrenheit, what is the energy",
     ("ANSWER", "9000")),
    ("t05", "given energy = 100 joules and temperature = 77 degrees "
            "fahrenheit, what is the entropy", ("ANSWER", "2000/5963")),
    ("t06", "given mass = 2 kilograms, specific heat capacity = 450 and "
            "temperature = 25 degrees celsius, what is the energy",
     ("REFUSED", "LEVEL_AS_DIFFERENCE")),
    ("t07", "given mass = 2, specific heat capacity = 450 and temperature = "
            "the melting point of iron, what is the energy",
     ("REFUSED", "LEVEL_AS_DIFFERENCE")),
    ("t08", "given mass = 2, specific heat capacity = 450 and temperature = "
            "the melting point of iron, what is the entropy",
     ("REFUSED", "LEVEL_AS_DIFFERENCE")),
    ("t09", "given energy = 100 and temperature change = 10 kelvins, what is "
            "the entropy", ("REFUSED", "DIFFERENCE_AS_LEVEL")),
    ("t10", "given mass = 2, specific heat capacity = 450 and temperature = "
            "300, what is the entropy", ("REFUSED", "KIND_CONFLATION")),
    ("t11", "given mass = 2, specific heat capacity = 450 and temperature = "
            "300, what is the energy", ("ANSWER", "270000")),
    ("t12", "given temperature = the boiling point of nitrogen and entropy = "
            "2, what is the energy", ("ANSWER", "3868/25")),
    ("t13", "given mass = 2, specific heat capacity = 450 and temperature "
            "change = the melting point of iron, what is the energy",
     ("REFUSED", "LEVEL_AS_DIFFERENCE")),
    ("t14", "given energy = 100 joules and temperature = -300 degrees "
            "celsius, what is the entropy", ("REFUSED", "BELOW_ABSOLUTE_ZERO")),
    ("t15", "given entropy = 2 and temperature = 0 degrees celsius, what is "
            "the energy in kilojoules", ("ANSWER", "5463/10000")),
)

# (id, question, expected verdict)
CONSTANT_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("c01", "given frequency = 5 terahertz, what is the energy",
     ("ANSWER", "132521403/40000000000000000000000000000")),
    ("c02", "given energy = 2 electronvolts, what is the frequency",
     ("ANSWER", "21362355120000000000000/44173801")),
    ("c03", "given energy = 3 joules, what is the momentum",
     ("ANSWER", "3/299792458")),
    ("c04", "given wavelength = 500 nanometres, what is the energy",
     ("REFUSED", "NO_DERIVATION")),
    ("c05", "given frequency = 5 terahertz and energy = 1 joule, what is the "
            "momentum", ("REFUSED", "INCONSISTENT_GIVENS")),
    ("c06", "given frequency = 600 terahertz, what is the energy in "
            "electronvolts", ("ANSWER", "220869005/89009813")),
)

#: Earlier declared cases whose verdict this round changes:
#: ``(corpus module, case id) -> (new verdict, reason)``.
AMENDED: Dict[Tuple[str, str], Tuple[Verdict, str]] = {
    ("stepwise_two_cases", "u13"): (
        ("REFUSED", "LEVEL_AS_DIFFERENCE"),
        "25 degrees Celsius is a temperature level (298.15 K); the heat "
        "axiom reads a temperature difference, so the level is refused by "
        "that name rather than the offset unit being refused outright"),
    ("stepwise_two_cases", "g01"): (
        ("REFUSED", "LEVEL_AS_DIFFERENCE"),
        "the melting point of iron is a temperature level; energy = mass * "
        "specific heat capacity * temperature reads a temperature "
        "difference, and a level is a difference only from absolute zero, "
        "which the question does not say"),
    ("stepwise_two_cases", "g03"): (
        ("REFUSED", "LEVEL_AS_DIFFERENCE"),
        "as g01, and the entropy step then reads the same temperature as a "
        "level: the answer 900 was mass times specific heat capacity, the "
        "entropy of heating from absolute zero at constant specific heat, "
        "which diverges"),
    ("stepwise_two_cases", "g11"): (
        ("REFUSED", "LEVEL_AS_DIFFERENCE"),
        "as g01, with the boiling point of oxygen"),
    ("stepwise_two_cases", "m02"): (
        ("REFUSED", "LEVEL_AS_DIFFERENCE"),
        "the narrative form of g03"),
}
