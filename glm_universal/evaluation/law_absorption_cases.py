"""``glm_universal.evaluation.law_absorption_cases`` -- the laws absorbed:
the declared corpus.

The declared question set of ``studies/LAW_ABSORPTION_STUDY.md`` §1.3
(Phase 75), written and committed before the planner frame that reads it.
Every expected value was worked from the facts the retained UBP laws state
once corrected (``studies/LAW_REGISTER_STUDY.md`` §2), from the Lean theorems
cited there, and -- for the two confidence questions -- from the weight
enumerators of the cosets of weight 0 and 3 (``1, 759, 2576, 759, 1`` and
``1, 21, 168, 640, 1218, 1218, 640, 168, 21, 1``).

An expected verdict is ``("ANSWER", value)`` or ``("REFUSED", NAME)``.  A value
written with a decimal point is compared after rounding the exact answer
half-even to the same number of places; every other value is compared as
written.  The outcome of complete decoding for an error weight is ``right``
(every pattern corrected), ``refused`` (every pattern lands on a six-way tie),
``wrong`` (every pattern miscorrected) or ``mixed``.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["CASES", "REFUSAL_NAMES", "NOT_READ"]

#: The named refusals of the frame.
REFUSAL_NAMES: Tuple[str, ...] = (
    "WEIGHT_OUT_OF_RANGE",      # an error weight or codeword weight not in 0..24
    "NOT_A_PROBABILITY",        # a bit-flip rate outside [0, 1]
    "TIE",                      # a confidence asked where six codewords tie
    "BEYOND_COVERING_RADIUS",   # no 24-bit word lies that far from the code
)

Verdict = Tuple[str, ...]

# (id, question, expected verdict, the law or laws it is absorbed from)
CASES: Tuple[Tuple[str, str, Verdict, str], ...] = (
    ("s01", "how many codewords does the golay code have",
     ("ANSWER", "4096"), "LAW_COMP_009"),
    ("s02", "how many codewords are there in the extended golay code",
     ("ANSWER", "4096"), "LAW_COMP_009"),
    ("s03", "what is the rate of the golay code",
     ("ANSWER", "1/2"), "LAW_COMP_009"),
    ("s04", "how many octads are there in the golay code",
     ("ANSWER", "759"), "LAW_RELATION_ORTHO_001"),
    ("s05", "how many dodecads does the golay code have",
     ("ANSWER", "2576"), "LAW_RELATION_ORTHO_001"),
    ("s06", "how many codewords of weight 16 does the golay code have",
     ("ANSWER", "759"), "LAW_RELATION_ORTHO_001"),
    ("s07", "how many codewords of weight 10 does the golay code have",
     ("ANSWER", "0"), "LAW_RELATION_ORTHO_001"),
    ("s08", "what is the minimum distance of the golay code",
     ("ANSWER", "8"), "LAW_RELATION_002"),
    ("s09", "what is the covering radius of the golay code",
     ("ANSWER", "4"), "LAW_FOURTH_FLIP_001"),
    ("s10", "how many bit errors can the golay code correct",
     ("ANSWER", "3"), "LAW_COMP_005"),
    ("s11", "can the golay decoder correct 3 bit errors",
     ("ANSWER", "right"), "LAW_COMP_005"),
    ("s12", "can the golay decoder correct 4 bit errors",
     ("ANSWER", "refused"), "LAW_FOURTH_FLIP_001"),
    ("s13", "what happens when a golay codeword has 5 bit errors",
     ("ANSWER", "wrong"), "LAW_COMP_005"),
    ("s14", "what happens when a golay codeword has 1 bit error",
     ("ANSWER", "right"), "LAW_COMP_005"),
    ("s15", "what happens when a golay codeword has 8 bit errors",
     ("ANSWER", "mixed"), "LAW_FOURTH_FLIP_001"),
    # Amended after the frame ran (study §2.3): declared as 0.994678, copied
    # from Phase 74's table, which truncates; the exact value 0.99467897...
    # rounds half-even to 0.994679 under this file's own comparison rule.
    ("s16", "what is the probability that the golay decoder is right at a "
            "bit-flip rate of 3%", ("ANSWER", "0.994679"),
     "LAW_STORAGE_HARDENED_001"),
    ("s17", "what is the probability that the golay decoder is wrong at a "
            "bit-flip rate of 3%", ("ANSWER", "0.0005925"),
     "LAW_STORAGE_HARDENED_001"),
    ("s18", "what is the probability that the golay decoder refuses at a "
            "bit-flip rate of 1/100", ("ANSWER", "0.000087"),
     "LAW_STORAGE_HARDENED_001"),
    ("s19", "is the golay decoder always right at a bit-flip rate of 3%",
     ("ANSWER", "False"), "LAW_STORAGE_HARDENED_001"),
    ("s20", "is the golay decoder always right at a bit-flip rate of 0",
     ("ANSWER", "True"), "LAW_STORAGE_HARDENED_001"),
    ("s21", "how likely is a golay decoding at distance 3 to be right at a "
            "bit-flip rate of 1/100", ("ANSWER", "0.997860"),
     "LAW_FOURTH_FLIP_001"),
    ("s22", "how likely is a golay decoding at distance 0 to be right at a "
            "bit-flip rate of 1/10", ("ANSWER", "0.999982"),
     "LAW_COMP_005"),
    ("s23", "what fraction of 24-bit words decode uniquely under the golay "
            "code", ("ANSWER", "2325/4096"), "LAW_GATEWAY_002"),
    ("s24", "is the golay code perfect", ("ANSWER", "False"),
     "LAW_GOLAY_UNIQUENESS_001"),
    ("s25", "is the golay code of length 23 perfect", ("ANSWER", "True"),
     "LAW_GOLAY_UNIQUENESS_001"),
    ("s26", "what is the kissing number of the leech lattice",
     ("ANSWER", "196560"), "LAW_KISSING_EXPANSION_001"),
    ("s27", "how many minimal vectors does the leech lattice have",
     ("ANSWER", "196560"), "LAW_KISSING_EXPANSION_001"),
    ("s28", "is the xor of two golay codewords a codeword",
     ("ANSWER", "always"), "LAW_LOGIC_GEO_001"),
    ("s29", "is the and of two golay codewords a codeword",
     ("ANSWER", "not always"), "LAW_LOGIC_GEO_001"),
    ("s30", "is the or of two golay codewords a codeword",
     ("ANSWER", "not always"), "LAW_LOGIC_GEO_001"),
    ("s31", "does greedy descent always reach the nearest golay codeword in "
            "d steps", ("ANSWER", "False"), "LAW_PATH_LEAST_ACTION"),
    ("r01", "what happens when a golay codeword has 25 bit errors",
     ("REFUSED", "WEIGHT_OUT_OF_RANGE"), "LAW_COMP_005"),
    ("r02", "what is the probability that the golay decoder is right at a "
            "bit-flip rate of 3/2", ("REFUSED", "NOT_A_PROBABILITY"),
     "LAW_STORAGE_HARDENED_001"),
    ("r03", "how likely is a golay decoding at distance 4 to be right at a "
            "bit-flip rate of 1/100", ("REFUSED", "TIE"),
     "LAW_FOURTH_FLIP_001"),
    ("r04", "how likely is a golay decoding at distance 5 to be right at a "
            "bit-flip rate of 1/100", ("REFUSED", "BEYOND_COVERING_RADIUS"),
     "LAW_FOURTH_FLIP_001"),
    ("r05", "how many codewords of weight 25 does the golay code have",
     ("REFUSED", "WEIGHT_OUT_OF_RANGE"), "LAW_RELATION_ORTHO_001"),
)

#: Texts that name the substrate but have none of the frame's shapes: the
#: frame must not read them (mark A4).
NOT_READ: Tuple[str, ...] = (
    "golay",
    "address of golay",
    "describe golay",
    "golay_encode(5) ^ golay_encode(3)",
    "report golay decoding",
    "report leech distribution",
)
