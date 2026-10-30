"""``glm_universal.evaluation.stepwise_three_cases`` -- round three of the
stepwise planner: the declared corpus.

The declared corpus of ``studies/STEPWISE_THREE_STUDY.md`` (Phase 84),
written and committed before any code of the round.  Every expected answer
was worked by hand from the element table the planner already reads (its
``z``, ``atomic_weight_u``, ``density_g_per_cm3``, ``year_discovered``,
``valence_electrons``, ``melting_point_K``, ``boiling_point_K``,
``electronegativity_pauling`` and ``group_block`` columns), from the axioms
of the ten formula wheels under the junction table, and from the exact SI
prefix definitions.

Round two (Phase 73, ``studies/STEPWISE_TWO_STUDY.md`` §6) named the
widenings this round takes -- candidate O7 of ``STATUS.md`` §3.4:

* :data:`COMPARATIVE_CASES` -- *heavier / lighter / denser / older / newer*
  as comparatives with a declared register field, in the *which is ...,
  A or B* and *is A ... than B* frames; a comparative with no declared field
  is refused ``COMPARATIVE_UNDECLARED`` rather than guessed.
* :data:`COUNT_CASES` -- *how many more* over further count nouns: the
  electrons of the neutral atom and the valence electrons.  Neutrons still
  need a nuclide register and stay refused.
* :data:`PREFIX_CASES` -- the tera- and pico- prefixes in givens and asked
  units.  Exa- is still not declared.
* :data:`FOLD_CASES` -- sums, means and parity counts over a whole column:
  every element, or a declared class of the register's ``group_block``
  column (*the noble gases*, *the halogens* ...).  A column with a missing
  reading is refused ``COLUMN_HOLE``, with the missing rows named; a class
  the table does not declare is refused ``SET_UNDECLARED``.
* :data:`FOLLOW_UP_CASES` -- ``then ...`` over a round-three chain.

An expected verdict is ``("ANSWER", value)``, ``("AMBIGUOUS",)`` or
``("REFUSED", NAME)``; a value is written as round one writes it, and the
answer of *which is heavier, A or B* is the row as the question names it.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["COMPARATIVE_CASES", "COUNT_CASES", "PREFIX_CASES", "FOLD_CASES",
           "FOLLOW_UP_CASES", "NEW_REFUSAL_NAMES", "HOLE_CONTROL_AT_LEAST"]

#: The named refusals this round adds to rounds one and two.
NEW_REFUSAL_NAMES: Tuple[str, ...] = (
    "COMPARATIVE_UNDECLARED",  # a comparative with no declared field
    "VALUE_MISSING",           # the register records the value as missing
    "COLUMN_HOLE",             # a fold over a column with a missing reading
    "SET_UNDECLARED",          # a fold over a class the table does not declare
)

#: Mark V5: the *fold the rows that are present* control must answer at
#: least this many of the declared ``COLUMN_HOLE`` cases (each with a value
#: that is not the column's, since the column's is not determined).
HOLE_CONTROL_AT_LEAST = 3

Verdict = Tuple[str, ...]

# (id, question, expected verdict)
COMPARATIVE_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("c01", "which is heavier, iron or copper", ("ANSWER", "copper")),
    ("c02", "which is lighter, gold or lead", ("ANSWER", "gold")),
    ("c03", "is gold heavier than lead", ("ANSWER", "False")),
    ("c04", "is lead heavier than gold", ("ANSWER", "True")),
    ("c05", "which is denser, gold or lead", ("ANSWER", "gold")),
    ("c06", "which is older, oxygen or hydrogen", ("ANSWER", "hydrogen")),
    ("c07", "which is newer, oxygen or hydrogen", ("ANSWER", "oxygen")),
    ("c08", "is oxygen older than hydrogen", ("ANSWER", "False")),
    ("c09", "which is older, iron or oxygen", ("REFUSED", "VALUE_MISSING")),
    ("c10", "which is stronger, iron or copper",
     ("REFUSED", "COMPARATIVE_UNDECLARED")),
    ("c11", "is iron harder than copper",
     ("REFUSED", "COMPARATIVE_UNDECLARED")),
    ("c12", "which is heavier, iron or unobtainium",
     ("REFUSED", "UNKNOWN_STEP")),
    ("c13", "is copper lighter than iron", ("ANSWER", "False")),
    ("c14", "which is lighter, hydrogen or helium", ("ANSWER", "hydrogen")),
    ("c15", "is nitrogen newer than chlorine", ("ANSWER", "False")),
    ("c16", "how much heavier is gold than iron",
     ("ANSWER", "14112657/100000")),
    ("c17", "how much lighter is iron than gold",
     ("ANSWER", "14112657/100000")),
    ("c18", "how much heavier is iron than gold",
     ("REFUSED", "DIFFERENCE_REVERSED")),
)

# (id, question, expected verdict)
COUNT_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("n01", "how many more electrons does iron have than carbon",
     ("ANSWER", "20")),
    ("n02", "how many more valence electrons does oxygen have than carbon",
     ("ANSWER", "2")),
    ("n03", "how many more electrons does carbon have than iron",
     ("REFUSED", "DIFFERENCE_REVERSED")),
    ("n04", "how many more neutrons does iron have than carbon",
     ("REFUSED", "UNKNOWN_STEP")),
    ("n05", "how many more valence electrons does palladium have than "
            "carbon", ("REFUSED", "VALUE_MISSING")),
    ("n06", "how many more valence electrons does fluorine have than "
            "nitrogen, then is it even", ("ANSWER", "True")),
)

# (id, question, expected verdict, the quantities a correct answer stitches)
PREFIX_CASES: Tuple[Tuple[str, str, Verdict, Tuple[str, ...]], ...] = (
    ("p01", "given frequency = 3 terahertz and wavelength = 100 micrometres, "
            "what is the wave speed", ("ANSWER", "300000000"), ()),
    ("p02", "given charge = 4 picocoulombs and voltage = 3 volts, what is the "
            "energy in picojoules", ("ANSWER", "6"), ("capacitance",)),
    ("p03", "given wavelength = 500 picometres and frequency = 2 terahertz, "
            "what is the wave speed", ("ANSWER", "1000"), ()),
    ("p04", "given power = 3 terawatts and voltage = 1 megavolt, what is the "
            "current in kiloamperes", ("ANSWER", "3000"), ()),
    ("p05", "given voltage = 12 exavolts and resistance = 4 ohms, what is the "
            "power", ("REFUSED", "UNKNOWN_UNIT"), ()),
    ("p06", "given frequency = 2 terametres and wavelength = 3 metres, what "
            "is the wave speed", ("REFUSED", "UNIT_MISMATCH"), ()),
)

# (id, question, expected verdict)
FOLD_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("f01", "what is the average atomic number of the noble gases",
     ("ANSWER", "324/7")),
    ("f02", "what is the sum of the atomic numbers of the halogens",
     ("ANSWER", "316")),
    ("f03", "how many of the transition metals have an even atomic number",
     ("ANSWER", "20")),
    ("f04", "is the sum of the atomic numbers of the halogens even",
     ("ANSWER", "True")),
    ("f05", "what is the average melting point of the alkaline earth metals",
     ("ANSWER", "2207/2")),
    ("f06", "what is the average electronegativity of the noble gases",
     ("REFUSED", "COLUMN_HOLE")),
    ("f07", "what is the sum of the atomic numbers of all the elements",
     ("ANSWER", "7021")),
    ("f08", "what is the average of the valence electrons of the alkali "
            "metals", ("ANSWER", "1")),
    ("f09", "what is the average atomic number of the metals",
     ("REFUSED", "SET_UNDECLARED")),
    ("f10", "how many of the halogens have an odd atomic weight",
     ("REFUSED", "NOT_AN_INTEGER")),
    ("f11", "what is the sum of the atomic numbers of the noble gases, then "
            "is it prime", ("ANSWER", "not prime")),
    ("f12", "what is the average melting point of all the elements",
     ("REFUSED", "COLUMN_HOLE")),
    ("f13", "how many of the lanthanides have an odd atomic number",
     ("ANSWER", "8")),
    ("f14", "what is the average boiling point of the metalloids",
     ("ANSWER", "16160/7")),
    ("f15", "what is the mean atomic weight of the alkaline earth metals",
     ("ANSWER", "524372593/6000000")),
    ("f16", "how many of the noble gases have an odd atomic number",
     ("ANSWER", "0")),
    ("f17", "what is the average density of the halogens",
     ("REFUSED", "COLUMN_HOLE")),
)

# (id, first turn, second turn, expected verdict of the second turn)
FOLLOW_UP_CASES: Tuple[Tuple[str, str, str, Verdict], ...] = (
    ("w01", "what is the sum of the atomic numbers of the halogens",
     "then is it even", ("ANSWER", "True")),
    ("w02", "how many more electrons does gold have than iron",
     "then is it prime", ("ANSWER", "prime")),
)
