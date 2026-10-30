"""``glm_universal.evaluation.reverse_tct_two_cases`` -- round two's corpus.

The held-out corpus of ``studies/REVERSE_TCT_STUDY.md`` §7 (round two),
written and committed before the round-two realiser, reader, operations or
relay existed.  Every expected answer below was worked by hand from the
widened grammar of §7.1.  The Phase 67 corpus
(:mod:`glm_universal.evaluation.reverse_tct_cases`) is left exactly as it was
declared; the four of its cases whose declared answer the widening changes on
purpose are listed in :data:`SUPERSEDED` with the answer they must now give.

* :data:`SAY_CASES` -- source, and the column-1 sentence it must realise to,
  word for word.
* :data:`SAY_REFUSALS` -- sources outside the widened fragment, with the
  refusal.
* :data:`READ_REFUSALS` -- sentences outside the widened grammar.
* :data:`ENTAIL_CASES`, :data:`BOUNDS_CASES`, :data:`EQUIVALENCE_CASES`,
  :data:`NEGATE_CASES` -- the operations over disjunctions and piecewise
  linear terms.
* :data:`DIALECT_INSIDE` -- the Phase 64 value programs the widened fragment
  must speak and read back to the dialect's value (W2).
* :data:`RELAY_CASES` -- the planner loop (W6): question and verdict or
  refusal.
* :data:`SUPERSEDED` -- Phase 67 cases whose declared answer changes.
* :data:`WIDE_BATTERY_ATOMS`, :data:`WIDE_BATTERY_DEPTH`,
  :data:`MASK_BATTERY_ATOMS` -- the W1 batteries.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["SAY_CASES", "SAY_REFUSALS", "READ_REFUSALS", "ENTAIL_CASES",
           "BOUNDS_CASES", "EQUIVALENCE_CASES", "NEGATE_CASES",
           "DIALECT_INSIDE", "RELAY_CASES", "SUPERSEDED",
           "WIDE_BATTERY_ATOMS", "WIDE_BATTERY_DEPTH", "MASK_BATTERY_ATOMS",
           "NEW_REFUSAL_NAMES", "RELAY_PLACES", "RELAY_LIMIT"]

#: Refusal names round two adds to the eight of Phase 67.
NEW_REFUSAL_NAMES: Tuple[str, ...] = (
    "NOT_INTEGER", "NEGATIVE_SHIFT", "SORT_MISMATCH", "NOTHING_TO_RELAY",
    "OUT_OF_RANGE")


SAY_CASES: Tuple[Tuple[str, str, str], ...] = (
    # -- the integer layer ------------------------------------------------
    ("floordiv", "-17 // 5", "the floor quotient of negative seventeen and five"),
    ("mod", "-17 % 5", "the remainder of negative seventeen and five"),
    ("mod-var", "x % 2", "the remainder of x and two"),
    ("abs", "abs(Fraction(-5, 7))",
     "the absolute value of the fraction negative five over seven"),
    ("min", "min(x, 1)", "the minimum of x and one"),
    ("max-three", "max(Fraction(2, 7), Fraction(3, 10), Fraction(5, 17))",
     "the maximum of the fraction two over seven and the maximum of the "
     "fraction three over ten and the fraction five over seventeen"),
    ("neg-exponent", "Fraction(2, 3) ** -2",
     "the power of the fraction two over three with exponent negative two"),
    ("bit-and", "0b110110 & 0b011011",
     "the bitwise and of fifty-four and twenty-seven"),
    ("bit-or", "5 | 3", "the bitwise or of five and three"),
    ("bit-xor", "5 ^ 3", "the exclusive or of five and three"),
    ("bit-not", "~10", "the complement of ten"),
    ("shift-left", "37 << 5", "the left shift of thirty-seven and five"),
    ("shift-right", "1000 >> 3", "the right shift of one thousand and three"),
    ("pow-mod", "pow(3, 4, 5)",
     "the remainder of the power of three with exponent four and five"),
    ("sum-tuple", "sum((Fraction(1, 2), Fraction(1, 3)))",
     "the sum of the fraction one over two and the fraction one over three"),
    # -- Golay masks --------------------------------------------------------
    ("mask", "frozenset({3, 1, 2})", "the mask of three positions one, two, three"),
    ("mask-empty", "frozenset()", "the empty mask"),
    ("mask-one", "frozenset({5})", "the mask of one position five"),
    ("mask-and", "frozenset({1, 2, 3}) & frozenset({3, 4})",
     "the intersection of the mask of three positions one, two, three and "
     "the mask of two positions three, four"),
    ("mask-size", "len(frozenset({1, 2}) | frozenset({2, 9}))",
     "the size of the union of the mask of two positions one, two and the "
     "mask of two positions two, nine"),
    ("mask-distance", "hamming(frozenset({1, 2, 3}), frozenset({3, 4}))",
     "the distance between the mask of three positions one, two, three and "
     "the mask of two positions three, four"),
    ("mask-member", "5 in frozenset({1, 5, 9})",
     "five is in the mask of three positions one, five, nine"),
    ("mask-subset", "frozenset({1, 2}) <= frozenset({1, 2, 3})",
     "the mask of two positions one, two is contained in the mask of three "
     "positions one, two, three"),
    ("mask-diff", "frozenset({1, 2, 3}) - frozenset({2})",
     "the set difference of the mask of three positions one, two, three and "
     "the mask of one position two"),
    ("mask-xor", "frozenset({1, 2}) ^ frozenset({2, 3})",
     "the symmetric difference of the mask of two positions one, two and the "
     "mask of two positions two, three"),
    # -- disjunction ------------------------------------------------------
    ("or", "x < 0 or x > 2",
     "either x is less than zero, or x is greater than two"),
    ("or-and", "x < 0 or x > 2 and y == 1",
     "either x is less than zero, or x is greater than two, and either x is "
     "less than zero, or y equals one"),
    ("not", "not (x < 1)", "x is at least one"),
    # -- programs ---------------------------------------------------------
    ("unpack", "a, b = 3, Fraction(1, 4)\na * b",
     "let a be three. let b be the fraction one over four. the result is the "
     "product of a and b."),
)


SAY_REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("fraction-and", "Fraction(1, 2) & 1", "NOT_INTEGER"),
    ("negative-shift", "1 << -1", "NEGATIVE_SHIFT"),
    ("mask-outside", "frozenset({3, 24})", "NOT_IN_FRAGMENT"),
    ("mask-plus-number", "frozenset({1}) + 1", "SORT_MISMATCH"),
    ("symbolic-exponent", "x ** y", "NOT_IN_FRAGMENT"),
    ("floordiv-zero", "7 // 0", "DIVISION_BY_ZERO"),
    ("zero-negative-power", "0 ** -1", "DIVISION_BY_ZERO"),
    ("unpack-self", "a, b = b, 1\na", "NOT_IN_FRAGMENT"),
    ("float", "1.5 + x", "NOT_IN_FRAGMENT"),
)


READ_REFUSALS: Tuple[Tuple[str, str], ...] = (
    ("mask-count", "the mask of three positions one, two"),
    ("mask-order", "the mask of two positions two, one"),
    ("mask-number", "the mask of one positions five"),
    ("mask-range", "the mask of two positions one, twenty-four"),
    ("either-alone", "either x is less than zero"),
    ("or-alone", "x is less than zero, or x is greater than two"),
    ("negative-zero-exponent", "the power of x with exponent negative zero"),
)


# (id, premises, conclusion, expected)
ENTAIL_CASES: Tuple[Tuple[str, Tuple[str, ...], str, str], ...] = (
    ("d01", ("x < 0 or x > 2",), "x != 1", "ENTAILS"),
    ("d02", ("x < 0 or x > 2", "x >= 0"), "x > 2", "ENTAILS"),
    ("d03", ("x < 0 or x > 2",), "x > 2", "INDEPENDENT"),
    ("d04", ("x < 0 or x > 2",), "x == 1", "CONTRADICTS"),
    ("d05", ("x >= 0",), "x > 1 or x < 2", "ENTAILS"),
    ("d06", ("x == 1 or x == 2",), "x >= 1 and x <= 2", "ENTAILS"),
    ("d07", ("x == 1 or x == 2",), "x == 1", "INDEPENDENT"),
    ("d08", ("x == 1 or x == 2", "x != 1"), "x == 2", "ENTAILS"),
    ("d09", ("x < 0 or y < 0", "x >= 0"), "y < 0", "ENTAILS"),
    ("d10", ("x < 0 or x > 5", "x > 1", "x < 4"), "x == 0",
     "INCONSISTENT_PREMISES"),
    ("d11", ("abs(x) <= 1",), "x <= 1", "ENTAILS"),
    ("d12", ("abs(x) <= 1",), "x >= -1 and x <= 1", "ENTAILS"),
    ("d13", ("abs(x) <= 1",), "x > 2", "CONTRADICTS"),
    ("d14", ("abs(x - 3) < 2",), "x > 1 and x < 5", "ENTAILS"),
    ("d15", ("abs(x) >= 2",), "x >= 2", "INDEPENDENT"),
    ("d16", ("abs(x) >= 2",), "x >= 2 or x <= -2", "ENTAILS"),
    ("d17", ("min(x, y) >= 1",), "x + y >= 2", "ENTAILS"),
    ("d18", ("max(x, y) <= 3", "x + y == 6"), "x == 3", "ENTAILS"),
    ("d19", ("max(x, y) <= 3",), "x + y <= 5", "INDEPENDENT"),
    ("d20", ("x > 0",), "abs(x) == x", "ENTAILS"),
    ("d21", ("x // 2 == 1",), "x >= 2", "NOT_POLYNOMIAL"),
    ("d22", ("x % 2 == 0",), "x == 0", "NOT_POLYNOMIAL"),
    ("d23", ("x & 1 == 1",), "x > 0", "NOT_POLYNOMIAL"),
    ("d24", ("x > 7 // 2",), "x > 3", "ENTAILS"),
    ("d25", ("x <= abs(-5)",), "x < 6", "ENTAILS"),
    ("d26", ("x * abs(x) >= 1",), "x > 0", "NONLINEAR"),
    ("d27", ("5 in frozenset({1, 5})",), "x == x", "NOT_IN_FRAGMENT"),
    ("d28", ("not x > 3",), "x <= 3", "ENTAILS"),
    ("d29", ("not (x > 0 and y > 0)", "x > 0"), "y <= 0", "ENTAILS"),
)


# (id, variable, premises, expected sentence or refusal name)
BOUNDS_CASES: Tuple[Tuple[str, str, Tuple[str, ...], str], ...] = (
    ("c01", "x", ("abs(x) <= 3",),
     "x is at least negative three, and x is at most three"),
    ("c02", "x", ("abs(x - 1) < 2",),
     "x is greater than negative one, and x is less than three"),
    ("c03", "x", ("x == 1 or x == 4",),
     "x is at least one, and x is at most four"),
    ("c04", "x", ("x < 0 or x > 10", "x > -5", "x < 20"),
     "x is greater than negative five, and x is less than twenty"),
    ("c05", "y", ("max(x, y) <= 2",), "y is at most two"),
    ("c06", "x", ("min(x, 5) >= 2",), "x is at least two"),
    ("c07", "x", ("abs(x) >= 1",), "nothing bounds x"),
    ("c08", "x", ("x // 3 == 1",), "NOT_POLYNOMIAL"),
)


# (id, first, second, expected)
EQUIVALENCE_CASES: Tuple[Tuple[str, str, str, str], ...] = (
    ("r01", "abs(x)", "max(x, -x)", "SAME"),
    ("r02", "min(x, y) + max(x, y)", "x + y", "SAME"),
    ("r03", "abs(x)", "x", "DIFFERENT"),
    ("r04", "x < 0 or x > 0", "x != 0", "SAME"),
    ("r05", "not (x < 1 and y < 1)", "x >= 1 or y >= 1", "SAME"),
    ("r06", "abs(x) <= 2", "x >= -2 and x <= 2", "SAME"),
    ("r07", "x // 2", "(x - x % 2) / 2", "NOT_POLYNOMIAL"),
    ("r08", "7 // 2", "3", "SAME"),
    ("r09", "-7 % 3", "2", "SAME"),
    ("r10", "abs(x - y)", "max(x - y, y - x)", "SAME"),
    ("r11", "min(x, 1)", "x", "DIFFERENT"),
    ("r12", "x == 1 or x == 2", "x >= 1 and x <= 2", "DIFFERENT"),
)


# (id, source, expected negation sentence or refusal)
NEGATE_CASES: Tuple[Tuple[str, str, str], ...] = (
    ("m01", "x >= 0 and y >= 0",
     "either x is less than zero, or y is less than zero"),
    ("m02", "x < 0 or x > 2", "x is at least zero, and x is at most two"),
    ("m03", "x == 1 or x == 2",
     "x does not equal one, and x does not equal two"),
    ("m04", "(x < 0 or x > 2) and y == 1",
     "either x is at least zero, or y does not equal one, and either x is "
     "at most two, or y does not equal one"),
    ("m05", "abs(x) <= 1", "the absolute value of x is greater than one"),
    ("m06", "not x < 3", "x is less than three"),
    ("m07", "x < 3", "x is at least three"),
)


#: W2: the Phase 64 value programs the widened fragment must speak, read
#: back, and evaluate to the dialect's value (the 8 of Phase 67 and 28 more).
DIALECT_INSIDE: Tuple[str, ...] = (
    "frac-add", "frac-mixed", "frac-div", "frac-int-div", "frac-pow",
    "frac-compare", "frac-chain", "int-big",
    "frac-floor", "frac-mod", "frac-neg-pow", "frac-abs", "frac-sum",
    "frac-max", "int-floordiv-neg", "int-mod-neg", "int-pow-mod",
    "int-shift-left", "int-shift-right", "int-shift-neg", "bit-and",
    "bit-or", "bit-xor", "bit-not", "bit-neg", "bit-wide", "bit-neg-or",
    "tuple-unpack", "fs-and", "fs-or", "fs-xor", "fs-diff", "fs-subset",
    "fs-len", "fs-hamming", "fs-member",
)


#: W6: decimal places of every value handoff, and the magnitude bound on a
#: handed-off numerator or denominator (at and above it: OUT_OF_RANGE).
RELAY_PLACES = 20
RELAY_LIMIT = 10 ** 12

# (id, question, expected verdict or refusal)
RELAY_CASES: Tuple[Tuple[str, str, str], ...] = (
    ("l01", "relay: say: Fraction(1, 3) + Fraction(1, 6)", "RELAYED"),
    ("l02", "relay: say: -17 // 5", "RELAYED"),
    ("l03", "relay: say: Fraction(7, 2) % Fraction(4, 3)", "RELAYED"),
    ("l04", "relay: say: Fraction(-7, 3)", "RELAYED"),
    ("l05", "relay: say: abs(Fraction(-5, 7))", "RELAYED"),
    ("l06", "relay: say: max(Fraction(2, 7), Fraction(3, 10), Fraction(5, 17))",
     "RELAYED"),
    ("l07", "relay: say: 0b110110 & 0b011011", "RELAYED"),
    ("l08", "relay: say: len(frozenset({1, 2, 3}) ^ frozenset({2, 3, 4}))",
     "RELAYED"),
    ("l09", "relay: solve for x: 3 * x - 1 == x + 4", "RELAYED"),
    ("l10", "relay: bounds of x: x + y == 10 ; x - y == 2", "RELAYED"),
    ("l11", "relay: bounds of x: abs(x - 1) < 2", "RELAYED"),
    ("l12", "relay: say: Fraction(1, 3) < Fraction(34, 100)", "RELAYED"),
    ("l13", "relay: say: 7 // 2 == 3", "RELAYED"),
    ("l14", "relay: entails: x > 3 ; x > 5", "RELAYED"),
    ("l15", "relay: say: 2 ** 100 + 1", "OUT_OF_RANGE"),
    ("l16", "relay: entails: x > 3 ; x > 2", "NOTHING_TO_RELAY"),
    ("l17", "relay: say: x + 1", "NOTHING_TO_RELAY"),
    ("l18", "relay: solve for x: x ** 2 == 4", "NONLINEAR"),
    ("l19", "relay: say: 5 in frozenset({1, 5, 9})", "NOTHING_TO_RELAY"),
    ("l20", "relay: say: Fraction(2, 3)", "RELAYED"),
)


#: Phase 67 cases whose declared answer round two changes on purpose:
#: ``(corpus, id, new expected)``.
SUPERSEDED: Tuple[Tuple[str, str, str], ...] = (
    ("SAY_REFUSALS", "modulo", "the remainder of x and two"),
    ("SAY_REFUSALS", "negative-exponent",
     "the power of x with exponent negative one"),
    ("SAY_REFUSALS", "or",
     "either x is greater than one, or x is less than zero"),
    ("NEGATE_CASES", "n04",
     "either x is less than zero, or y is less than zero"),
)


#: W1: every term of depth at most two over these atoms with every unary
#: (negation, absolute value, complement) and binary operator of the widened
#: fragment (the four of Phase 67, floor quotient, remainder, minimum,
#: maximum, bitwise and, bitwise or, exclusive or, left and right shift).
WIDE_BATTERY_ATOMS: Tuple[str, ...] = ("x", "1", "Fraction(1, 2)")
WIDE_BATTERY_DEPTH = 2

#: W1: every mask term of depth at most two over these mask literals with
#: the four set operators.
MASK_BATTERY_ATOMS: Tuple[str, ...] = ("frozenset()", "frozenset({0})",
                                       "frozenset({1, 23})",
                                       "frozenset({0, 5, 23})")
