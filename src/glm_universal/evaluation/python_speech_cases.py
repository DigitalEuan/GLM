"""``glm_universal.evaluation.python_speech_cases`` -- the declared corpus.

The held-out corpus of ``studies/PYTHON_SPEECH_STUDY.md`` §2, written and
committed before :mod:`glm_universal.reasoning.python_speech` existed.

* :data:`VALUE_CASES` -- sources the GLM must answer. The expected value is
  not written here: CPython computes it, from the same source and the same
  pure-Python prelude, and the GLM must agree with it in type and value.
* :data:`REFUSAL_CASES` -- sources the GLM must refuse, with the refusal name
  it must give.
* :data:`EQUIVALENT_PAIRS` -- expressions that must share one AST address.
* :data:`DISTINCT_EXPRESSIONS` -- structurally distinct expressions, which
  must not collide.
* :data:`BITWISE_OPERANDS` -- operand pairs for the register check.

The names ``Fraction``, ``unit``, ``classify``, ``golay_encode``,
``hamming``, ``ds_bits`` and ``plane`` are the dialect's prelude; everything
else is ordinary Python 3.11.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["VALUE_CASES", "REFUSAL_CASES", "PHASE64_REFUSAL_CASES",
           "SUPERSEDED_BY_PHASE94", "EQUIVALENT_PAIRS",
           "DISTINCT_EXPRESSIONS", "BITWISE_OPERANDS"]


VALUE_CASES: Tuple[Tuple[str, str], ...] = (
    # -- rational layer --------------------------------------------------
    ("frac-add", "Fraction(1, 3) + Fraction(1, 6)"),
    ("frac-mixed", "(Fraction(1, 3) + 2) * 3"),
    ("frac-div", "Fraction(7, 3) / Fraction(14, 9)"),
    ("frac-int-div", "Fraction(5) / 2"),
    ("frac-floor", "Fraction(-7, 2) // 1"),
    ("frac-mod", "Fraction(7, 2) % Fraction(4, 3)"),
    ("frac-pow", "Fraction(2, 3) ** 5"),
    ("frac-neg-pow", "Fraction(2, 3) ** -2"),
    ("frac-string", "Fraction('3/12') + Fraction('0.25')"),
    ("frac-parts", "Fraction(10, -4).numerator * 100 + Fraction(10, -4).denominator"),
    ("frac-abs", "abs(Fraction(-5, 7))"),
    ("frac-compare", "Fraction(1, 3) < Fraction(34, 100)"),
    ("frac-chain", "Fraction(1, 3) < Fraction(1, 2) <= Fraction(2, 4) != 1"),
    ("frac-sum", "sum((Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)))"),
    ("frac-max", "max(Fraction(2, 7), Fraction(3, 10), Fraction(5, 17))"),
    # -- integer layer ---------------------------------------------------
    ("int-big", "2 ** 100 + 1"),
    ("int-floordiv-neg", "-17 // 5"),
    ("int-mod-neg", "-17 % 5"),
    ("int-divmod", "divmod(-17, 5)"),
    ("int-pow-mod", "pow(3, 200, 1000003)"),
    ("int-plane", "plane(Fraction(5, 3), 4)"),
    ("int-plane-neg", "plane(Fraction(-5, 3), 4)"),
    ("int-shift-left", "37 << 5"),
    ("int-shift-right", "1000 >> 3"),
    ("int-shift-neg", "-1000 >> 3"),
    ("int-bit-length", "(2 ** 70 - 1).bit_length()"),
    ("int-bit-count", "(0b101101110).bit_count()"),
    # -- substrate layer: bool and bitwise --------------------------------
    ("bool-and", "True and not False"),
    ("bool-arith", "True + True + False"),
    ("bit-and", "0b110110 & 0b011011"),
    ("bit-or", "0b110110 | 0b011011"),
    ("bit-xor", "0xABCDEF ^ 0x123456"),
    ("bit-not", "~0b1010"),
    ("bit-neg", "-6 & 0xFF"),
    ("bit-wide", "(2 ** 50 + 12345) ^ (2 ** 40 + 999)"),
    ("bit-neg-or", "-100 | 37"),
    ("bit-mixed-bool", "True ^ True"),
    # -- strings and slicing ---------------------------------------------
    ("str-slice", "'geometric language machine'[2:20:3]"),
    ("str-reverse", "'Leech lattice'[::-1]"),
    ("str-neg-slice", "'abcdefghij'[-2:1:-3]"),
    ("str-clamp", "'short'[1:100]"),
    ("str-index", "'Golay'[-1]"),
    ("str-ord", "ord('Λ')"),
    ("str-chr", "chr(955) + chr(65)"),
    ("str-concat", "'MOG' + '-' + 'cube' * 2"),
    ("str-len", "len('Mathieu group M24')"),
    ("str-compare", "'apple' < 'apricot'"),
    ("str-in", "'lattice' in 'the Leech lattice'"),
    ("str-long-slice", "('0123456789' * 5)[7:45:6]"),
    # -- tuples ----------------------------------------------------------
    ("tuple-slice", "(1, 2, 3, 4, 5, 6, 7, 8)[1::2]"),
    ("tuple-concat", "(1, Fraction(1, 2)) + (True, 'x')"),
    ("tuple-compare", "(1, 2, 3) < (1, 2, 4)"),
    ("tuple-nested", "((1, 2), (3, (4, 5)))[1][1][0]"),
    ("tuple-len", "len(tuple(range(24)))"),
    ("tuple-unpack", "a, b = 3, Fraction(1, 4)\na * b"),
    # -- frozensets ------------------------------------------------------
    ("fs-and", "frozenset({1, 2, 3, 4}) & frozenset({3, 4, 5})"),
    ("fs-or", "frozenset({0, 23}) | frozenset({5})"),
    ("fs-xor", "frozenset({1, 2, 3}) ^ frozenset({2, 3, 4})"),
    ("fs-diff", "frozenset({1, 2, 3}) - frozenset({2})"),
    ("fs-subset", "frozenset({1, 2}) <= frozenset({1, 2, 3})"),
    ("fs-len", "len(frozenset((7, 8, 9, 7)))"),
    ("fs-hamming", "hamming(frozenset({1, 2, 3}), frozenset({3, 4}))"),
    ("fs-member", "5 in frozenset({1, 5, 9})"),
    # -- comparisons and units -------------------------------------------
    ("unit-compare", "unit(3, 'm') < unit(Fraction(7, 2), 'm')"),
    ("unit-add", "unit(3, 'm') + unit(Fraction(1, 2), 'm') == unit(Fraction(7, 2), 'm')"),
    ("cmp-mixed", "Fraction(4, 2) == 2 == True + True"),
    # -- range and the delta-sigma loop -----------------------------------
    ("range-sum", "sum(range(3, 100, 7))"),
    ("range-len", "len(range(10, -10, -3))"),
    ("range-tuple", "tuple(range(5, 0, -2))"),
    ("range-index", "range(0, 1000, 7)[50]"),
    ("ds-bits", "ds_bits(Fraction(3, 8), 16)"),
    ("ds-sum", "sum(ds_bits(Fraction(2, 7), 21))"),
    # -- statements, functions, loops, match -------------------------------
    ("loop-acc", "total = 0\nfor k in range(1, 11):\n    total += Fraction(1, k * (k + 1))\ntotal"),
    ("while-gcd", "a, b = 1071, 462\nwhile b:\n    a, b = b, a % b\na"),
    ("def-fact", "def fact(n):\n    if n == 0:\n        return 1\n    return n * fact(n - 1)\nfact(25)"),
    ("def-harmonic", "def h(n):\n    s = Fraction(0)\n    for k in range(1, n + 1):\n        s += Fraction(1, k)\n    return s\nh(12)"),
    ("if-else", "x = Fraction(5, 3)\ny = 'big' if x > 1 else 'small'\ny"),
    ("match-literal", "def kind(v):\n    match v:\n        case 0:\n            return 'zero'\n        case 1 | 2 | 3:\n            return 'small'\n        case (a, b):\n            return 'pair'\n        case _:\n            return 'other'\n(kind(0), kind(2), kind((4, 5)), kind(99))"),
    ("match-guard", "def sign(v):\n    match v:\n        case n if n < 0:\n            return -1\n        case 0:\n            return 0\n        case _:\n            return 1\n(sign(Fraction(-1, 2)), sign(0), sign(7))"),
    ("classify-exact", "c1 = golay_encode(1)\nc2 = golay_encode(2)\nclassify(c2, c1, c2)"),
    ("classify-corrected", "c1 = golay_encode(5)\nc2 = golay_encode(9)\nclassify(c1 ^ 0b1011, c1, c2)"),
    ("classify-match", "c1 = golay_encode(3)\nc2 = golay_encode(12)\nmatch classify(c2 ^ (1 << 20), c1, c2):\n    case 0:\n        r = 'first'\n    case 1:\n        r = 'second'\nr"),
    ("comprehension-free", "len('abc') * 8 == 24"),
)


PHASE64_REFUSAL_CASES: Tuple[Tuple[str, str, str], ...] = (
    ("float-literal", "1.5 + 2", "FLOAT"),
    ("float-call", "float(3)", "FLOAT"),
    ("float-truediv", "7 / 2", "FLOAT"),
    ("float-neg-pow", "2 ** -1", "FLOAT"),
    ("float-frac-pow", "Fraction(1, 4) ** Fraction(1, 2)", "FLOAT"),
    ("float-fraction-of-float", "Fraction(0.1)", "FLOAT"),
    ("float-in-loop", "s = 0\nfor k in range(3):\n    s += k / 2\ns", "FLOAT"),
    ("nondet-hash", "hash('glm')", "NONDETERMINISTIC"),
    ("nondet-random", "import random\nrandom.randint(1, 6)", "NONDETERMINISTIC"),
    ("nondet-time", "import time\ntime.time_ns()", "NONDETERMINISTIC"),
    ("nondet-id", "id(3)", "NONDETERMINISTIC"),
    ("deep-hole", "c1 = golay_encode(1)\nc2 = golay_encode(2)\nclassify(c1 ^ 0b1111, c1, c2)", "AMBIGUOUS"),
    ("uncorrectable", "c1 = golay_encode(1)\nc2 = golay_encode(2)\nclassify(golay_encode(7) ^ 1, c1, c2)", "UNCORRECTABLE"),
    ("scale-mismatch", "unit(3, 'm') < unit(3, 'km')", "SCALE_MISMATCH"),
    ("scale-undeclared", "unit(3, 'm') < 5", "SCALE_MISMATCH"),
    ("set-iteration", "t = 0\nfor x in frozenset({1, 9}):\n    t = t * 10 + x\nt", "ORDER_UNDEFINED"),
    ("fs-outside", "frozenset({'a', 'b'})", "OUTSIDE_SUBSTRATE"),
    ("fs-outside-range", "frozenset({3, 24})", "OUTSIDE_SUBSTRATE"),
    ("tuple-overflow", "tuple(range(25))", "CARRIER_OVERFLOW"),
    ("list-literal", "[1, 2, 3]", "MUTABLE_CONTAINER"),
    ("step-zero", "'abc'[::0]", "PYTHON_ERROR"),
    ("shift-negative", "1 << -1", "PYTHON_ERROR"),
    ("zero-division", "Fraction(1, 0)", "PYTHON_ERROR"),
    ("runaway-loop", "n = 0\nwhile True:\n    n += 1\nn", "BUDGET"),
    ("unsupported-lambda", "(lambda x: x)(3)", "UNSUPPORTED"),
    ("unsupported-attribute", "'abc'.upper()", "UNSUPPORTED"),
)

#: Phase 94 (``studies/THIRD_SORT_STUDY.md``, ``third_sort_cases.
#: SUPERSEDED_REFUSALS``) admits list literals and string methods, so these
#: two Phase 64 refusals are answered on purpose; the record above is kept
#: as it was declared, and :data:`REFUSAL_CASES` is the set still in force.
SUPERSEDED_BY_PHASE94: Tuple[str, ...] = ("list-literal",
                                          "unsupported-attribute")
REFUSAL_CASES: Tuple[Tuple[str, str, str], ...] = tuple(
    c for c in PHASE64_REFUSAL_CASES if c[0] not in SUPERSEDED_BY_PHASE94)


EQUIVALENT_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("a + b", "b + a"),
    ("(a + b) * c", "c * (b + a)"),
    ("((a))", "a"),
    ("a*b+c", "c + (b * a)"),
    ("x & y | z", "z | (y & x)"),
    ("f(a, b) + 1", "1 + f(a, b)"),
    ("a == b", "b == a"),
    ("(p + q) ** 2", "(q+p)**2"),
    ("x + y * z", "u + v * w"),
    ("s[1:5:2]", "t[1:5:2]"),
)


DISTINCT_EXPRESSIONS: Tuple[str, ...] = (
    "a + b", "a - b", "a * b", "a // b", "a % b", "a ** b", "a << b",
    "a >> b", "a & b", "a | b", "a ^ b", "-a", "~a", "not a",
    "a + b + c", "a + b * c", "(a + b) * c", "a - b - c",
    "a - (b - c)", "a ** b ** c", "(a ** b) ** c", "a < b", "a <= b",
    "a == b", "a != b", "a < b < c", "a and b", "a or b",
    "a if b else c", "s[a]", "s[a:b]", "s[a:b:c]", "s[::a]", "f(a)",
    "f(a, b)", "f(g(a))", "(a, b)", "(a, b, c)", "a + 1", "a + 2",
    "a * 2", "2 * a + 1", "Fraction(1, 3)", "Fraction(1, 2)",
    "'x'", "'y'", "True", "False", "0", "1", "len(s)", "a + a",
    "a * a", "(a + b) - c", "a - (b + c)", "a in s", "a not in s",
)


BITWISE_OPERANDS: Tuple[Tuple[int, int], ...] = (
    (0, 0), (1, 0), (0b110110, 0b011011), (0xABCDEF, 0x123456),
    (0xFFFFFF, 0x000001), (2 ** 24 - 1, 2 ** 24 - 1), (2 ** 24, 1),
    (2 ** 50 + 12345, 2 ** 40 + 999), (-1, 0), (-6, 255), (-100, 37),
    (-(2 ** 30) - 7, 2 ** 29 + 3), (-1, -1), (123456789, -987654321),
    (2 ** 72 - 1, 2 ** 48 + 1), (7, -8),
)
