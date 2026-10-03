"""``glm_universal.evaluation.stepwise_five_cases`` -- round five of the
stepwise planner: the declared corpus.

The declared corpus of ``studies/DECLARED_FRAMES_STUDY.md`` (Phase 91),
written and committed before any code of the round.  Every expected value
was worked from the register the planner already reads -- sorted, counted
and summed exactly from the register's own readings by a throwaway
computation that shares no code with the module it tests -- and every
bounded answer from the rules of §1 of the study.

Round four of the order of work (``STATUS.md`` §3.4, ``studies/
ROADMAP_STUDY.md``) is the planner widenings: H's E6 first (frames generated
from a declaration rather than written by hand), then what O7 and candidate
2 left (``studies/STEPWISE_THREE_STUDY.md`` §6, ``studies/HOLE_FOLDS_STUDY.md``
§6).  Every widening below is meant to be a **declaration entry**, read by a
reader generated from the declaration, not a new hand-written frame:

* :data:`ORDER_CASES` -- further order statistics: the *k*-th largest or
  smallest value and the lower and upper quartiles (the declared convention:
  the median of the lower or upper half, the middle value left out of both
  halves when the count is odd), bounded exactly under a hole by round
  four's rule; ``ORDER_OUT_OF_RANGE`` when *k* exceeds the set.
* :data:`SUPERLATIVE_CASES` -- superlatives of the declared comparatives
  (*heaviest*, *lightest*, *densest*, *oldest*, *newest*) naming the row or
  the top *k* rows of a declared set, largest first; ``TOP_K_TIE`` when the
  *k*-th and the (*k* + 1)-th rows tie; ``COLUMN_HOLE`` over a column with a
  hole (a hole can always be filled into the top *k*); answered over the
  present rows when asked for them.
* :data:`BOUND_CASES` -- the present-rows parity count, and *what are the
  bounds on ...*: a parity count under a hole is bounded by the present
  count and that plus the holes; a sum or a mean under a hole is bounded
  only through a declared physical range of its column (``RANGE_UNDECLARED``
  otherwise).
* :data:`CLASS_CASES` -- classes the register does not hold as one value:
  *the metals* (a declared union of six of its classes) and *the rare
  earths* (the lanthanides with scandium and yttrium).
* :data:`PREFIX_CASES` -- the remaining exact SI prefixes (peta, exa, zetta,
  yotta, ronna, quetta; femto, atto, zepto, yocto, ronto, quecto).
* :data:`MOLECULE_CASES` -- the declared comparatives over the molecule
  table: *heavier* and *lighter* are the molar mass there;
  ``TABLE_MISMATCH`` for a row of each table.
* :data:`FOLLOW_UP_CASES` -- ``then ...`` over a round-five chain.

:data:`MOVED` names the three verdicts of earlier corpora this round is
declared to move -- each was a refusal that named exactly the declaration
this round adds -- with the verdict each is declared to move to.

An expected verdict is ``("ANSWER", value)`` or ``("REFUSED", NAME)``, and a
value is written as round one writes it; a row is named as the register
names it, in lower case.
"""

from __future__ import annotations

from typing import Dict, Tuple

__all__ = ["ORDER_CASES", "SUPERLATIVE_CASES", "BOUND_CASES", "CLASS_CASES",
           "PREFIX_CASES", "MOLECULE_CASES", "FOLLOW_UP_CASES", "MOVED",
           "NEW_REFUSAL_NAMES", "COMPLETIONS_PER_ANSWER", "all_cases"]

#: The named refusals this round adds to rounds one to four.
NEW_REFUSAL_NAMES: Tuple[str, ...] = (
    "ORDER_OUT_OF_RANGE",  # a k-th value or top k past the size of the set
    "TOP_K_TIE",           # the k-th and (k+1)-th rows of a top k tie
    "RANGE_UNDECLARED",    # bounds on a sum or mean of a column with no range
    "TABLE_MISMATCH",      # a comparative over a row of each table
)

#: Every bounded answer is checked against this many completions of its
#: holes (both extreme completions among them).
COMPLETIONS_PER_ANSWER = 200

Verdict = Tuple[str, ...]

# (id, question, expected verdict)
ORDER_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("k01", "what is the second largest atomic weight of the noble gases",
     ("ANSWER", "11100879/50000")),
    ("k02", "what is the third smallest atomic number of the halogens",
     ("ANSWER", "35")),
    ("k03", "what is the 2nd highest melting point of the lanthanides",
     ("ANSWER", "1818")),
    ("k04", "what is the lower quartile of the atomic numbers of the noble "
            "gases", ("ANSWER", "10")),
    ("k05", "what is the upper quartile atomic weight of the halogens",
     ("ANSWER", "4199743/20000")),
    ("k06", "what is the second largest density of the halogens",
     ("ANSWER", "between 493/100 and 7")),
    ("k07", "what is the lower quartile of the melting points of all the "
            "elements", ("ANSWER", "between 30159/100 and 577")),
    ("k08", "what is the third largest boiling point of the noble gases",
     ("ANSWER", "between 11993/100 and 16503/100")),
    ("k09", "what is the second smallest density of the transition metals",
     ("REFUSED", "COLUMN_HOLE")),
    ("k10", "what is the ninth largest atomic number of the halogens",
     ("REFUSED", "ORDER_OUT_OF_RANGE")),
    ("k11", "what is the lower quartile electronegativity of the transition "
            "metals", ("ANSWER", "between 61/50 and 33/20")),
    ("k12", "what is the upper quartile of the melting points of the alkali "
            "metals", ("ANSWER", "7419/20")),
)

# (id, question, expected verdict)
SUPERLATIVE_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("s01", "which is the heaviest of the noble gases",
     ("ANSWER", "oganesson")),
    ("s02", "which is the lightest of the halogens", ("ANSWER", "fluorine")),
    ("s03", "which is the oldest of the noble gases", ("ANSWER", "helium")),
    ("s04", "what are the three heaviest alkali metals",
     ("ANSWER", "francium, cesium, rubidium")),
    ("s05", "what are the two densest transition metals",
     ("REFUSED", "COLUMN_HOLE")),
    ("s06", "what are the two densest transition metals with a recorded "
            "density", ("ANSWER", "osmium, iridium")),
    ("s07", "which is the newest of the halogens", ("ANSWER", "tennessine")),
    ("s08", "which is the oldest of the alkali metals",
     ("REFUSED", "TOP_K_TIE")),
    ("s09", "which is the strongest of the halogens",
     ("REFUSED", "COMPARATIVE_UNDECLARED")),
    ("s10", "what are the twenty heaviest noble gases",
     ("REFUSED", "ORDER_OUT_OF_RANGE")),
    ("s11", "which is the heaviest of the metals",
     ("ANSWER", "livermorium")),
    ("s12", "what are the two newest actinides",
     ("ANSWER", "lawrencium, nobelium")),
)

# (id, question, expected verdict)
BOUND_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("p01", "how many of the transition metals that have one have an odd "
            "year discovered", ("ANSWER", "20")),
    ("p02", "how many of the post-transition metals that have one have an "
            "even year discovered", ("ANSWER", "3")),
    ("p03", "how many of the alkaline earth metals that have one have an odd "
            "electron affinity", ("REFUSED", "COLUMN_EMPTY")),
    ("p04", "what are the bounds on the average electronegativity of the "
            "noble gases", ("ANSWER", "between 4/5 and 51/14")),
    ("p05", "what are the bounds on the total ionization energy of the "
            "actinides", ("ANSWER", "between 86353/1000 and 5547/50")),
    ("p06", "what are the bounds on how many of the elements have an odd "
            "year discovered", ("ANSWER", "between 51 and 64")),
    ("p07", "what are the bounds on the average atomic number of the "
            "halogens", ("ANSWER", "158/3")),
    ("p08", "what are the bounds on the average density of the halogens",
     ("REFUSED", "RANGE_UNDECLARED")),
    ("p09", "what are the bounds on how many of the alkaline earth metals "
            "have an even year discovered", ("ANSWER", "between 5 and 6")),
    ("p10", "what are the bounds on the mean ionization energy of all the "
            "elements", ("ANSWER", "between 20393/2950 and 151139/14750")),
    ("p11", "what are the bounds on the total electronegativity of the noble "
            "gases", ("ANSWER", "between 28/5 and 51/2")),
    ("p12", "what are the bounds on how many of the halogens have an odd "
            "density", ("REFUSED", "NOT_AN_INTEGER")),
)

# (id, question, expected verdict)
CLASS_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("c01", "what is the average atomic number of the rare earths",
     ("ANSWER", "60")),
    ("c02", "how many of the metals have an odd atomic number",
     ("ANSWER", "47")),
    ("c03", "what is the median atomic weight of the rare earth elements",
     ("ANSWER", "37991/250")),
    ("c04", "what is the average density of the metals",
     ("REFUSED", "COLUMN_HOLE")),
    ("c05", "what is the average atomic number of the semimetals",
     ("REFUSED", "SET_UNDECLARED")),
    ("c06", "what is the sum of the atomic numbers of the rare earths",
     ("ANSWER", "1020")),
)

# (id, question, expected verdict)
PREFIX_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("x01", "given voltage = 12 exavolts and resistance = 4 ohms, what is "
            "the power",
     ("ANSWER", "36000000000000000000000000000000000000")),
    ("x02", "given charge = 3 femtocoulombs and voltage = 2 volts, what is "
            "the energy in femtojoules", ("ANSWER", "3")),
    ("x03", "given power = 2 petawatts and voltage = 4 megavolts, what is "
            "the current in kiloamperes", ("ANSWER", "500000")),
    ("x04", "given wavelength = 3 attometres and frequency = 1 exahertz, "
            "what is the wave speed", ("ANSWER", "3")),
    ("x05", "given frequency = 5 petahertz and wavelength = 2 nanometres, "
            "what is the wave speed", ("ANSWER", "10000000")),
    ("x06", "given voltage = 12 bigavolts and resistance = 4 ohms, what is "
            "the power", ("REFUSED", "UNKNOWN_UNIT")),
)

# (id, question, expected verdict)
MOLECULE_CASES: Tuple[Tuple[str, str, Verdict], ...] = (
    ("m01", "which is heavier, water or ammonia", ("ANSWER", "water")),
    ("m02", "is carbon dioxide heavier than water", ("ANSWER", "True")),
    ("m03", "which is lighter, methane or ammonia", ("ANSWER", "methane")),
    ("m04", "which is denser, water or ammonia",
     ("REFUSED", "COMPARATIVE_UNDECLARED")),
    ("m05", "which is heavier, water or iron", ("REFUSED", "TABLE_MISMATCH")),
    ("m06", "is ethanol lighter than methanol", ("ANSWER", "False")),
)

# (id, first turn, second turn, expected verdict of the second turn)
FOLLOW_UP_CASES: Tuple[Tuple[str, str, str, Verdict], ...] = (
    ("w01", "what is the second largest atomic weight of the noble gases",
     "then is it larger than 200", ("ANSWER", "True")),
    ("w02", "what are the bounds on the average electronegativity of the "
            "noble gases", "then is it larger than 1",
     ("REFUSED", "NOT_A_NUMBER")),
)

#: ``(earlier corpus, case id) -> (question, verdict before, verdict now)``:
#: the earlier declared verdicts this round is declared to move.  Each was a
#: refusal naming exactly the declaration this round adds; with round five
#: switched off each must come back as it was.
MOVED: Dict[Tuple[str, str], Tuple[str, Verdict, Verdict]] = {
    ("stepwise_three", "f09"): (
        "what is the average atomic number of the metals",
        ("REFUSED", "SET_UNDECLARED"), ("ANSWER", "6023/91")),
    ("stepwise_four", "o10"): (
        "what is the median atomic number of the metals",
        ("REFUSED", "SET_UNDECLARED"), ("ANSWER", "68")),
    ("stepwise_three", "p05"): (
        "given voltage = 12 exavolts and resistance = 4 ohms, what is the "
        "power", ("REFUSED", "UNKNOWN_UNIT"),
        ("ANSWER", "36000000000000000000000000000000000000")),
}


def all_cases() -> Tuple[Tuple[str, str, Verdict], ...]:
    """Every single-turn case of the corpus, in the order declared."""
    return (ORDER_CASES + SUPERLATIVE_CASES + BOUND_CASES + CLASS_CASES
            + PREFIX_CASES + MOLECULE_CASES)
