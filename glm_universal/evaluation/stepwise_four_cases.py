"""``glm_universal.evaluation.stepwise_four_cases`` -- round four of the
stepwise planner: the declared corpus.

The declared corpus of ``studies/HOLE_FOLDS_STUDY.md`` (Phase 85), written
and committed before any code of the round.  Every expected value was
worked from the element table the planner already reads -- sorted, counted
and averaged exactly from the register's own readings by a throwaway
computation that shares no code with the module it tests -- and every
bounded answer from the rule of §1 of the study.

Round three (Phase 84, ``studies/STEPWISE_THREE_STUDY.md`` §6) and the
extremum round (``studies/COLUMN_EXTREMUM_STUDY.md`` §7) left the same
question named: what a fold other than a sum or a mean does with a hole, and
the narrower question beside ``COLUMN_HOLE`` -- *of the rows that are filled
in, what is the answer?* -- asked as its own question.  This round takes
both (candidate 2 and the present-rows item of candidate O7 of
``STATUS.md`` §3.4):

* :data:`ORDER_CASES` -- the median, the largest and the smallest value of
  a column over a declared set, on columns with no hole, and the refusals
  where a hole leaves an end unbounded.
* :data:`BOUNDED_CASES` -- the median over a column **with** holes: the
  exact interval every completion of the holes lands in, answered as
  ``between A and B``; a single value when the interval closes (the holes
  cannot move it); ``COLUMN_HOLE`` when the holes leave it unbounded.
* :data:`RANK_CASES` -- the rank of one row by a column within a declared
  set, largest first, ties sharing the better rank; bounded the same way
  when the column has holes.
* :data:`PRESENT_CASES` -- the present-rows question asked as that
  question (*the noble gases that have one*, *the transition metals with a
  recorded density*), answered over the rows that hold a reading with the
  missing rows named in the answer.
* :data:`FOLLOW_UP_CASES` -- ``then ...`` over a round-four chain.

An expected verdict is ``("ANSWER", value)`` or ``("REFUSED", NAME)``, and a
value is written as round one writes it.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["ORDER_CASES", "BOUNDED_CASES", "RANK_CASES", "PRESENT_CASES",
           "FOLLOW_UP_CASES", "NEW_REFUSAL_NAMES", "COMPLETIONS_PER_ANSWER"]

#: The named refusals this round adds to rounds one to three.
NEW_REFUSAL_NAMES: Tuple[str, ...] = (
    "NOT_A_MEMBER",    # a rank asked of a row outside the declared set
    "COLUMN_EMPTY",    # a present-rows question over a set with no reading
)

#: Mark H5: every bounded answer is checked against this many completions
#: of its holes (both extreme completions among them).
COMPLETIONS_PER_ANSWER = 200

Verdict = Tuple[str, ...]

# (id, question, expected verdict)
ORDER_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("o01", "what is the median atomic number of the halogens",
     ("ANSWER", "44")),
    ("o02", "what is the median melting point of the alkaline earth metals",
     ("ANSWER", "1025")),
    ("o03", "what is the largest atomic weight of the noble gases",
     ("ANSWER", "36902/125")),
    ("o04", "what is the highest melting point of the lanthanides",
     ("ANSWER", "1936")),
    ("o05", "what is the lowest density of the metalloids",
     ("ANSWER", "1456/625")),
    ("o06", "what is the median atomic weight of all the elements",
     ("ANSWER", "14257383/100000")),
    ("o07", "what is the median of the valence electrons of the alkali "
            "metals", ("ANSWER", "1")),
    ("o08", "what is the smallest boiling point of the noble gases",
     ("REFUSED", "COLUMN_HOLE")),
    ("o09", "what is the largest density of the transition metals",
     ("REFUSED", "COLUMN_HOLE")),
    ("o10", "what is the median atomic number of the metals",
     ("REFUSED", "SET_UNDECLARED")),
    ("o11", "what is the median atomic number of the halogens, then is it "
            "even", ("ANSWER", "True")),
)

# (id, question, expected verdict)
BOUNDED_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("b01", "what is the median density of the halogens",
     ("ANSWER", "between 1556607/1000000 and 201/50")),
    ("b02", "what is the median melting point of all the elements",
     ("ANSWER", "between 1091 and 266133/200")),
    ("b03", "what is the median of the valence electrons of the transition "
            "metals", ("ANSWER", "2")),
    ("b04", "what is the median of the valence electrons of all the "
            "elements", ("ANSWER", "2")),
    ("b05", "what is the median electronegativity of the noble gases",
     ("REFUSED", "COLUMN_HOLE")),
    ("b06", "what is the median boiling point of the actinides",
     ("REFUSED", "COLUMN_HOLE")),
    ("b07", "what is the median electronegativity of the lanthanides",
     ("ANSWER", "between 57/50 and 123/100")),
    ("b08", "what is the median of the valence electrons of the "
            "post-transition metals", ("ANSWER", "between 3 and 4")),
)

# (id, question, expected verdict)
RANK_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("r01", "what is the rank of iron by atomic weight among the transition "
            "metals", ("ANSWER", "33")),
    ("r02", "what is the rank of xenon by atomic number among the noble "
            "gases", ("ANSWER", "3")),
    ("r03", "what is the rank of gold by density among the transition "
            "metals", ("ANSWER", "between 6 and 15")),
    ("r04", "what is the rank of osmium by density among all the elements",
     ("ANSWER", "between 1 and 23")),
    ("r05", "what is the rank of iron by electronegativity among the "
            "transition metals", ("ANSWER", "between 17 and 26")),
    ("r06", "what is the rank of iron by density among the noble gases",
     ("REFUSED", "NOT_A_MEMBER")),
    ("r07", "what is the rank of tennessine by density among the halogens",
     ("REFUSED", "VALUE_MISSING")),
    ("r08", "what is the rank of iron by hardness among the transition "
            "metals", ("REFUSED", "UNKNOWN_STEP")),
)

# (id, question, expected verdict)
PRESENT_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("q01", "what is the average electronegativity of the noble gases that "
            "have one", ("ANSWER", "14/5")),
    ("q02", "what is the largest density of the transition metals with a "
            "recorded density", ("ANSWER", "2257/100")),
    ("q03", "what is the median melting point of the elements that have one",
     ("ANSWER", "1191")),
    ("q04", "what is the sum of the atomic numbers of the halogens that have "
            "one", ("ANSWER", "316")),
    ("q05", "what is the average electron affinity of the alkaline earth "
            "metals that have one", ("REFUSED", "COLUMN_EMPTY")),
    ("q06", "what is the rank of gold by density among the transition metals "
            "with a recorded density", ("ANSWER", "6")),
    ("q07", "what is the average density of the halogens with a recorded "
            "density", ("ANSWER", "1504491/500000")),
)

# (id, first turn, second turn, expected verdict of the second turn)
FOLLOW_UP_CASES: Tuple[Tuple[str, str, str, Verdict], ...] = (
    ("w01", "what is the average electronegativity of the noble gases that "
            "have one", "then is it larger than 2", ("ANSWER", "True")),
    ("w02", "what is the median density of the halogens",
     "then is it larger than 2", ("REFUSED", "NOT_A_NUMBER")),
)
