"""``glm_universal.evaluation.celsius_register_cases`` -- the Celsius
register: the declared corpus.

The declared corpus of ``studies/CELSIUS_REGISTER_STUDY.md`` (Phase 99),
written and committed before any code of the round.  The round adds the
first register that holds a reading in degrees Celsius -- the fourteen
fixed points of the International Temperature Scale of 1990 that have an
assigned temperature (triple, melting and freezing points; the helium and
hydrogen vapour-pressure points are ranges, not points, and are left out) --
and the first row of the scale table with an offset, so the half of
``GLM.ScaleConversion.cmpQ_apply`` that an offset exercises is shipped.

Every expected answer was worked by hand, in exact fractions, from:

* the ITS-90 assigned values, as the register holds them, in degrees
  Celsius (:data:`ITS90_CELSIUS`), and the same points in kelvin
  (:data:`ITS90_KELVIN`), which the register does *not* hold and which mark
  C1 checks the offset row against;
* the SI Brochure's ``t / degree Celsius = T / K - 273.15``, exact;
* the element register's melting and boiling points in kelvin (zinc
  ``692.68``, aluminium ``933.437``, mercury ``234.32`` and ``629.88``,
  gallium ``302.91``, neon ``24.56``);
* the axioms of the formula wheels: ``entropy = energy / temperature`` reads
  a thermodynamic temperature (a level), and ``energy = mass * specific heat
  capacity * temperature`` reads a temperature difference.

Four groups: :data:`ORDER_CASES` (the ordering operation across the offset
row), :data:`COLUMN_CASES` (the extremum operation on the new table),
:data:`PLANNER_CASES` (the stepwise planner reading a Celsius register value
as a level) and the register itself (:data:`ITS90_CELSIUS`).

An ordering verdict is ``lt`` / ``gt`` / ``eq`` or the refusal reason; a
column verdict is ``("answer", row)`` or the refusal reason; a planner
verdict is ``("ANSWER", value)`` or ``("REFUSED", NAME)`` -- ``("REFUSED",)``
when any named refusal is acceptable -- with values in the coherent SI unit
unless a unit is asked for.  Nothing in an earlier corpus is amended.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["ITS90_CELSIUS", "ITS90_KELVIN", "ORDER_CASES", "COLUMN_CASES",
           "PLANNER_CASES", "NAIVE_FLIPS", "NAIVE_PLANNER_WRONG"]

#: The register as declared: row key -> t90 in degrees Celsius, as an exact
#: decimal string (ITS-90, Preston-Thomas, Metrologia 27 (1990) 3, Table 1).
ITS90_CELSIUS: Tuple[Tuple[str, str], ...] = (
    ("hydrogen triple point", "-259.3467"),
    ("neon triple point", "-248.5939"),
    ("oxygen triple point", "-218.7916"),
    ("argon triple point", "-189.3442"),
    ("mercury triple point", "-38.8344"),
    ("water triple point", "0.01"),
    ("gallium melting point", "29.7646"),
    ("indium freezing point", "156.5985"),
    ("tin freezing point", "231.928"),
    ("zinc freezing point", "419.527"),
    ("aluminium freezing point", "660.323"),
    ("silver freezing point", "961.78"),
    ("gold freezing point", "1064.18"),
    ("copper freezing point", "1084.62"),
)

#: The same points in kelvin, T90, as the same table states them.  Not held
#: by the register: mark C1 requires the offset row to carry every Celsius
#: reading onto exactly this value.
ITS90_KELVIN: Tuple[Tuple[str, str], ...] = (
    ("hydrogen triple point", "13.8033"),
    ("neon triple point", "24.5561"),
    ("oxygen triple point", "54.3584"),
    ("argon triple point", "83.8058"),
    ("mercury triple point", "234.3156"),
    ("water triple point", "273.16"),
    ("gallium melting point", "302.9146"),
    ("indium freezing point", "429.7485"),
    ("tin freezing point", "505.078"),
    ("zinc freezing point", "692.677"),
    ("aluminium freezing point", "933.473"),
    ("silver freezing point", "1234.93"),
    ("gold freezing point", "1337.33"),
    ("copper freezing point", "1357.77"),
)

# (id, (field, left, other field, right), expected)
ORDER_CASES: Tuple[Tuple[str, Tuple[str, str, str, str], str], ...] = (
    # 692.677 K against 692.68 K
    ("o01", ("temperature_C", "zinc freezing point", "melting_point_K",
             "zinc"), "lt"),
    # 933.437 K against 933.473 K
    ("o02", ("melting_point_K", "aluminum", "temperature_C",
             "aluminium freezing point"), "lt"),
    # 273.16 K against 234.32 K; with the offset dropped, 0.01 against 234.32
    ("o03", ("temperature_C", "water triple point", "melting_point_K",
             "mercury"), "gt"),
    # 302.9146 K against 302.91 K; with the offset dropped, 29.7646 against
    # 302.91
    ("o04", ("temperature_C", "gallium melting point", "melting_point_K",
             "gallium"), "gt"),
    # 234.3156 K against 234.32 K
    ("o05", ("temperature_C", "mercury triple point", "melting_point_K",
             "mercury"), "lt"),
    # 1357.77 K against 629.88 K
    ("o06", ("temperature_C", "copper freezing point", "boiling_point_K",
             "mercury"), "gt"),
    # 13.8033 K against 24.56 K
    ("o07", ("temperature_C", "hydrogen triple point", "melting_point_K",
             "neon"), "lt"),
    # one scale, no conversion: 231.928 against 156.5985 degrees Celsius
    ("o08", ("temperature_C", "tin freezing point", "temperature_C",
             "indium freezing point"), "gt"),
    # a temperature and a mass: still refused
    ("o09", ("temperature_C", "zinc freezing point", "atomic_weight_u",
             "zinc"), "different-scale"),
    # no such row in any register
    ("o10", ("temperature_C", "lead freezing point", "melting_point_K",
             "lead"), "unreadable"),
)

#: Mark C5: the cases whose verdict the offset-dropped control must flip.
NAIVE_FLIPS: Tuple[str, ...] = ("o03", "o04")

# (id, (field, end, table), expected)
COLUMN_CASES: Tuple[Tuple[str, Tuple[str, str, str], Tuple[str, ...]], ...] = (
    ("k01", ("temperature_C", "largest", "fixed_point"),
     ("answer", "copper freezing point")),
    ("k02", ("temperature_C", "smallest", "fixed_point"),
     ("answer", "hydrogen triple point")),
    # gathered by quantity over every table: the element register's holes
    # still make the column incomplete, as declared by Phase 55
    ("k03", ("temperature", "largest", ""), ("incomplete",)),
)

# (id, question, expected verdict)
PLANNER_CASES: Tuple[Tuple[str, str, Tuple[str, ...]], ...] = (
    ("p01", "given the temperature of the water triple point and energy = "
            "2731600, what is the entropy", ("ANSWER", "10000")),
    ("p02", "given the temperature of the gallium melting point and entropy "
            "= 2, what is the energy", ("ANSWER", "1514573/2500")),
    ("p03", "given temperature = the temperature of the zinc freezing point "
            "and entropy = 3, what is the energy", ("ANSWER", "2078031/1000")),
    ("p04", "given the temperature of the water triple point and entropy = "
            "2, what is the energy in kilojoules", ("ANSWER", "6829/12500")),
    ("p05", "given the temperature of the copper freezing point, mass = 2 "
            "and specific heat capacity = 385, what is the energy",
     ("REFUSED", "LEVEL_AS_DIFFERENCE")),
    ("p06", "given temperature change = the temperature of the tin freezing "
            "point, mass = 1 and specific heat capacity = 228, what is the "
            "energy", ("REFUSED", "LEVEL_AS_DIFFERENCE")),
    ("p07", "given the temperature of the mercury triple point and energy = "
            "4686312, what is the entropy", ("ANSWER", "20000")),
    ("p08", "given the temperature of the lead freezing point and entropy = "
            "2, what is the energy", ("REFUSED",)),
    ("p09", "given the temperature of the silver freezing point and entropy "
            "= 1, what is the energy", ("ANSWER", "123493/100")),
)

#: Mark C5: with the offset dropped (a Celsius reading taken as kelvins),
#: every answered planner case must be answered, and answered wrongly.
NAIVE_PLANNER_WRONG: Tuple[str, ...] = ("p01", "p02", "p03", "p04", "p07",
                                        "p09")
