"""``glm_universal.evaluation.reverse_tct_cases`` -- the declared corpus.

The held-out corpus of ``studies/REVERSE_TCT_STUDY.md`` §2, written and
committed before :mod:`glm_universal.reasoning.reverse_tct` existed.  Every
expected answer below was worked by hand from the grammar of the study's §1.

Sources may be given in the Phase 64 dialect's syntax (column 3 in) or as a
sentence of the reverse grammar (column 1 in); each operation accepts both.

* :data:`SAY_CASES` -- source, and the column-1 sentence it must realise to,
  word for word.
* :data:`SAY_REFUSALS` -- sources outside the fragment, with the refusal.
* :data:`READ_REFUSALS` -- sentences outside the grammar (``UNREADABLE``).
* :data:`ENTAIL_CASES` -- premises, conclusion, and the verdict or refusal.
* :data:`SOLVE_CASES` -- variable, statement, and the answer sentence or
  refusal.
* :data:`BOUNDS_CASES` -- variable, premises, and the answer sentence or
  refusal.
* :data:`EQUIVALENCE_CASES` -- two sources, and ``SAME``, ``DIFFERENT`` or a
  refusal.
* :data:`PARAPHRASE_CASES` -- sources to paraphrase.
* :data:`NEGATE_CASES` -- source, and the negation sentence or refusal.
* :data:`BATTERY_ATOMS`, :data:`BATTERY_DEPTH` -- the V1/V2 battery: every
  term of depth at most two over these atoms with ``+ - * /`` and unary
  ``-``.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["SAY_CASES", "SAY_REFUSALS", "READ_REFUSALS", "ENTAIL_CASES",
           "SOLVE_CASES", "BOUNDS_CASES", "EQUIVALENCE_CASES",
           "PARAPHRASE_CASES", "NEGATE_CASES", "BATTERY_ATOMS",
           "BATTERY_DEPTH", "REFUSAL_NAMES"]

#: Every refusal name the study declares.
REFUSAL_NAMES: Tuple[str, ...] = (
    "NOT_IN_FRAGMENT", "UNREADABLE", "DIVISION_BY_ZERO", "NOT_POLYNOMIAL",
    "NONLINEAR", "NONCONSTANT_COEFFICIENT", "NO_UNIQUE_SOLUTION",
    "INCONSISTENT_PREMISES")


SAY_CASES: Tuple[Tuple[str, str, str], ...] = (
    ("sum", "2 + 3", "the sum of two and three"),
    ("affine", "2 * x + 3", "the sum of the product of two and x and three"),
    ("scoped", "2 * (x + 3)", "the product of two and the sum of x and three"),
    ("left-assoc", "x - y - 1",
     "the difference of the difference of x and y and one"),
    ("right-group", "x - (y - 1)",
     "the difference of x and the difference of y and one"),
    ("fraction", "Fraction(1, 2) * x",
     "the product of the fraction one over two and x"),
    ("negation", "-x", "the negation of x"),
    ("negative-literal", "-3 + x", "the sum of negative three and x"),
    ("square", "x ** 2 - 4", "the difference of the square of x and four"),
    ("cube", "(x + 1) ** 3", "the cube of the sum of x and one"),
    ("power", "2 ** 10", "the power of two with exponent ten"),
    ("quotient", "x / (y + 1)", "the quotient of x and the sum of y and one"),
    ("equation", "2 * x + 3 == 7",
     "the sum of the product of two and x and three equals seven"),
    ("disequation", "x != 0", "x does not equal zero"),
    ("chain", "0 < x <= 10", "zero is less than x, and x is at most ten"),
    ("conjunction", "x >= 2 and y > x",
     "x is at least two, and y is greater than x"),
    ("million", "1000000 + 21", "the sum of one million and twenty-one"),
    ("words", "123456",
     "one hundred twenty-three thousand four hundred fifty-six"),
    ("negative-fraction", "Fraction(-7, 3)",
     "the fraction negative seven over three"),
    ("normalised", "Fraction(6, 3)", "two"),
    ("program", "x = 3\ny = 2 * x + 1\ny",
     "let x be three. let y be the sum of the product of two and x and one. "
     "the result is y."),
    ("big-power", "10 ** 12", "the power of ten with exponent twelve"),
    ("digits", "1000000000000", "1000000000000"),
    ("two-fractions", "Fraction(1, 2) + Fraction(1, 3)",
     "the sum of the fraction one over two and the fraction one over three"),
)


SAY_REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("modulo", "x % 2", "NOT_IN_FRAGMENT"),
    ("float", "1.5 + x", "NOT_IN_FRAGMENT"),
    ("symbolic-exponent", "x ** y", "NOT_IN_FRAGMENT"),
    ("call", "f(x)", "NOT_IN_FRAGMENT"),
    ("reserved-name", "sum + 1", "NOT_IN_FRAGMENT"),
    ("negative-exponent", "x ** -1", "NOT_IN_FRAGMENT"),
    ("or", "x > 1 or x < 0", "NOT_IN_FRAGMENT"),
)


READ_REFUSALS: Tuple[Tuple[str, str], ...] = (
    ("short", "the sum of two"),
    ("infix", "two plus three"),
    ("trailing", "the sum of two and three and four"),
    ("no-right-side", "x equals"),
    ("bad-number", "the sum of twenty twenty and one"),
)


# (id, premises, conclusion, expected)
ENTAIL_CASES: Tuple[Tuple[str, Tuple[str, ...], str, str], ...] = (
    ("e01", ("x > 3",), "x > 2", "ENTAILS"),
    ("e02", ("x > 3",), "x < 2", "CONTRADICTS"),
    ("e03", ("x > 3",), "x > 5", "INDEPENDENT"),
    ("e04", ("x >= 3", "x <= 3"), "x == 3", "ENTAILS"),
    ("e05", ("x + y == 10", "x - y == 2"), "x == 6", "ENTAILS"),
    ("e06", ("x + y == 10", "x - y == 2"), "y == 5", "CONTRADICTS"),
    ("e07", ("x + y == 10", "x - y == 2"), "y == 4", "ENTAILS"),
    ("e08", ("x < y", "y < z"), "x < z", "ENTAILS"),
    ("e09", ("x < y", "y < z"), "z < x", "CONTRADICTS"),
    ("e10", ("x <= y",), "x < y", "INDEPENDENT"),
    ("e11", ("2 * x + 3 == 7",), "x == 2", "ENTAILS"),
    ("e12", ("x != 0",), "x > 0", "INDEPENDENT"),
    ("e13", ("x > 0",), "x != 0", "ENTAILS"),
    ("e14", ("x == 0",), "x != 0", "CONTRADICTS"),
    ("e15", ("x > 1", "x < 1"), "x == 5", "INCONSISTENT_PREMISES"),
    ("e16", ("x * y > 0",), "x > 0", "NONLINEAR"),
    ("e17", ("x ** 2 == 4",), "x == 2", "NONLINEAR"),
    ("e18", ("x / y == 1",), "x == y", "NOT_POLYNOMIAL"),
    ("e19", ("x / 0 == 1",), "x == 1", "DIVISION_BY_ZERO"),
    ("e20", ("Fraction(1, 2) * x + Fraction(1, 3) * y <= 1", "x >= 0",
             "y >= 0"), "x <= 2", "ENTAILS"),
    ("e21", ("Fraction(1, 2) * x + Fraction(1, 3) * y <= 1", "x >= 0",
             "y >= 0"), "y <= 3", "ENTAILS"),
    ("e22", ("Fraction(1, 2) * x + Fraction(1, 3) * y <= 1", "x >= 0",
             "y >= 0"), "x + y <= 2", "INDEPENDENT"),
    ("e23", ("x >= 0", "y >= 0", "x + y <= 1"), "x - y <= 1", "ENTAILS"),
    ("e24", ("x >= 0", "y >= 0", "x + y <= 1"), "x + y >= 2", "CONTRADICTS"),
    ("e25", ("x is greater than three",), "x is at least three", "ENTAILS"),
    ("e26", ("the sum of x and y equals ten", "x equals four"),
     "y equals six", "ENTAILS"),
    ("e27", ("x is less than two",),
     "the product of two and x is less than four", "ENTAILS"),
    ("e28", ("x > 2",), "x ** 2 > 4", "NONLINEAR"),
    ("e29", ("x == 3",), "(x + 1) * 2 == 8", "ENTAILS"),
    ("e30", ("x * x - x * x + x == 1",), "x == 1", "ENTAILS"),
    ("e31", ("x > 0",), "y > 0", "INDEPENDENT"),
    ("e32", ("0 < x < 1",), "x != 1", "ENTAILS"),
    ("e33", ("x > 0",), "x == x", "ENTAILS"),
    ("e34", ("x > 0",), "1 == 2", "CONTRADICTS"),
)


# (id, variable, statement, expected sentence or refusal name)
SOLVE_CASES: Tuple[Tuple[str, str, str, str], ...] = (
    ("s01", "x", "2 * x + 3 == 7", "x equals two"),
    ("s02", "x", "3 * x - 1 == x + 4", "x equals the fraction five over two"),
    ("s03", "y", "x + y == 10", "y equals the sum of the negation of x and ten"),
    ("s04", "x", "Fraction(1, 2) * x == 3", "x equals six"),
    ("s05", "x", "2 * x + 1 < 7", "x is less than three"),
    ("s06", "x", "-3 * x + 1 <= 7", "x is at least negative two"),
    ("s07", "x", "x + 1 == x + 2", "NO_UNIQUE_SOLUTION"),
    ("s08", "x", "y == 3", "NO_UNIQUE_SOLUTION"),
    ("s09", "x", "x * y == 3", "NONCONSTANT_COEFFICIENT"),
    ("s10", "x", "x ** 2 == 4", "NONLINEAR"),
    ("s11", "x", "x / 2 + x / 3 == 5", "x equals six"),
    ("s12", "x", "x != 3", "x does not equal three"),
    ("s13", "z", "2 * z - x + y == 0",
     "z equals the difference of the product of the fraction one over two "
     "and x and the product of the fraction one over two and y"),
    ("s14", "x", "x > x + 1", "NO_UNIQUE_SOLUTION"),
)


# (id, variable, premises, expected sentence or refusal name)
BOUNDS_CASES: Tuple[Tuple[str, str, Tuple[str, ...], str], ...] = (
    ("b01", "x", ("x > 3", "x <= 10"),
     "x is greater than three, and x is at most ten"),
    ("b02", "x", ("x + y == 10", "y >= 4"), "x is at most six"),
    ("b03", "x", ("x + y == 10", "x - y == 2"), "x equals six"),
    ("b04", "y", ("x >= 0", "y >= 0", "x + y <= 1"),
     "y is at least zero, and y is at most one"),
    ("b05", "x", ("y > 0",), "nothing bounds x"),
    ("b06", "x", ("x > 1", "x < 1"), "INCONSISTENT_PREMISES"),
    ("b07", "x", ("x * y >= 1",), "NONLINEAR"),
    ("b08", "t", ("2 * t + 1 >= 0", "3 * t <= 4", "t != 0"),
     "t is at least the fraction negative one over two, and t is at most "
     "the fraction four over three"),
    ("b09", "x", ("x == 2 * y", "y == 3"), "x equals six"),
    ("b10", "x", ("x < 5",), "x is less than five"),
)


# (id, first, second, expected)
EQUIVALENCE_CASES: Tuple[Tuple[str, str, str, str], ...] = (
    ("q01", "2 * (x + 3)", "2 * x + 6", "SAME"),
    ("q02", "(x + 1) ** 2", "x ** 2 + 2 * x + 1", "SAME"),
    ("q03", "(x + 1) ** 2", "x ** 2 + 1", "DIFFERENT"),
    ("q04", "x - y", "y - x", "DIFFERENT"),
    ("q05", "x / 2 + x / 2", "x", "SAME"),
    ("q06", "x / y * y", "x", "NOT_POLYNOMIAL"),
    ("q07", "(x - y) * (x + y)", "x ** 2 - y ** 2", "SAME"),
    ("q08", "x < 3", "3 > x", "SAME"),
    ("q09", "2 * x < 6", "x < 3", "SAME"),
    ("q10", "x < 3", "x <= 3", "DIFFERENT"),
    ("q11", "-x >= -3", "x <= 3", "SAME"),
    ("q12", "x == 3", "2 * x == 6", "SAME"),
    ("q13", "x + y == 1 and x - y == 1", "x == 1 and y == 0", "SAME"),
    ("q14", "x != 3", "3 != x", "SAME"),
    ("q15", "x ** 2 >= 0", "x == x", "NONLINEAR"),
    ("q16", "x * y == y * x", "x == x", "SAME"),
    ("q17", "the sum of x and x", "the product of two and x", "SAME"),
    ("q18", "x is less than three", "three is greater than x", "SAME"),
)


PARAPHRASE_CASES: Tuple[Tuple[str, str], ...] = (
    ("p01", "2 * x + 3 == 7"),
    ("p02", "x < y"),
    ("p03", "the sum of x and the product of three and y"),
    ("p04", "(x + 1) ** 2"),
    ("p05", "x >= 0 and y >= 0"),
    ("p06", "x - y != 4"),
)


NEGATE_CASES: Tuple[Tuple[str, str, str], ...] = (
    ("n01", "x < 3", "x is at least three"),
    ("n02", "x == y", "x does not equal y"),
    ("n03", "the sum of x and one is at most y",
     "the sum of x and one is greater than y"),
    ("n04", "x >= 0 and y >= 0", "NOT_IN_FRAGMENT"),
)


#: The V1/V2 battery: atoms as dialect source.
BATTERY_ATOMS: Tuple[str, ...] = ("x", "y", "0", "1", "2", "-1",
                                  "Fraction(1, 2)")
BATTERY_DEPTH = 2
