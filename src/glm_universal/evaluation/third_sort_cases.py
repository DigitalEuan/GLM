"""``glm_universal.evaluation.third_sort_cases`` -- the declared cases of Phase 94.

The held-out corpus of ``studies/THIRD_SORT_STUDY.md`` §2, written and
committed before :mod:`glm_universal.reasoning.reverse_tct_seq` and before the
dialect widening in :mod:`glm_universal.reasoning.python_speech` existed.
Every expected sentence below was worked by hand from the grammar of the
study's §1.

Two halves, one sort.

* **The third sort in the reverse grammar** (candidate M): strings, tuples
  and ranges as terms with count-first literals.

  - :data:`SAY_CASES` -- ``(id, source, sentence)``: the column-1 sentence
    the reverse surface must generate, word for word.  The value or truth it
    carries is CPython's, computed from the source, so it is not written here.
  - :data:`SAY_REFUSALS` -- ``(id, source, refusal)``.
  - :data:`READ_REFUSALS` -- ``(id, sentence)``: sentences outside the
    grammar, refused ``UNREADABLE``.
  - :data:`DIALECT_INSIDE` -- the Phase 64 value programs on strings, tuples
    and ranges that must now be spoken and read back to CPython's value;
    :data:`DIALECT_OUTSIDE` the one declared to stay outside, with why.
  - :data:`SEQ_BATTERY_ATOMS` -- the round-trip battery's atoms.

* **The dialect widened** (candidate I1): string methods over code points,
  and list and dict literals as immutable snapshots.

  - :data:`STRING_METHOD_CASES`, :data:`LIST_CASES`, :data:`DICT_CASES` --
    ``(id, source)``; CPython is the reference for type and value.
  - :data:`DIALECT_REFUSALS` -- ``(id, source, refusal)``.
  - :data:`SUPERSEDED_REFUSALS` -- the two Phase 64 refusal cases whose
    declared refusal this round removes on purpose, with the old name; each
    must now be answered and equal CPython.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["SAY_CASES", "SAY_REFUSALS", "READ_REFUSALS", "DIALECT_INSIDE",
           "DIALECT_OUTSIDE", "SEQ_BATTERY_ATOMS", "NEW_REFUSAL_NAMES",
           "STRING_METHOD_CASES", "LIST_CASES", "DICT_CASES",
           "DIALECT_REFUSALS", "SUPERSEDED_REFUSALS"]

#: Refusal names the third sort adds to the reverse study's.
NEW_REFUSAL_NAMES: Tuple[str, ...] = (
    "INDEX_OUT_OF_RANGE", "NOT_A_CHARACTER", "EMPTY_SEQUENCE", "ZERO_STEP")


# ===========================================================================
# 1.  THE THIRD SORT IN THE REVERSE GRAMMAR
# ===========================================================================

SAY_CASES: Tuple[Tuple[str, str, str], ...] = (
    # -- literals ---------------------------------------------------------
    ("str-literal", "'Golay'",
     "the string of five characters capital g, small o, small l, small a, "
     "small y"),
    ("str-empty", "''", "the empty string"),
    ("str-digits-space", "'M 24'",
     "the string of four characters capital m, space, digit two, digit four"),
    ("str-code-point", "'Λx'",
     "the string of two characters code point nine hundred twenty-three, "
     "small x"),
    ("tuple-literal", "(1, Fraction(1, 2))",
     "the tuple of two entries one, the fraction one over two"),
    ("tuple-one", "(5,)", "the tuple of one entry five"),
    ("tuple-empty", "()", "the empty tuple"),
    ("range-literal", "range(3, 100, 7)",
     "the range from three to one hundred by seven"),
    ("range-short", "range(4)", "the range from zero to four by one"),
    # -- sequence terms ---------------------------------------------------
    ("str-concat", "'ab' + 'c'",
     "the concatenation of the string of two characters small a, small b and "
     "the string of one character small c"),
    ("str-repeat", "'ab' * 3",
     "the repetition of the string of two characters small a, small b times "
     "three"),
    ("str-reverse", "'abc'[::-1]",
     "the slice of the string of three characters small a, small b, small c "
     "from the default to the default by negative one"),
    ("str-slice", "'abcdef'[1:4]",
     "the slice of the string of six characters small a, small b, small c, "
     "small d, small e, small f from one to four by one"),
    ("str-index", "'abc'[-1]",
     "the item of the string of three characters small a, small b, small c "
     "at negative one"),
    ("tuple-nested", "((1, 2), 3)[0]",
     "the item of the tuple of two entries the tuple of two entries one, "
     "two, three at zero"),
    ("str-chr", "chr(97)", "the character of ninety-seven"),
    ("range-entries", "tuple(range(3))",
     "the entries of the range from zero to three by one"),
    # -- numbers of sequences ---------------------------------------------
    ("str-len", "len('abc')",
     "the length of the string of three characters small a, small b, small c"),
    ("str-ord", "ord('A')", "the code point of the string of one character "
     "capital a"),
    ("range-total", "sum(range(1, 11))",
     "the total of the range from one to eleven by one"),
    ("range-greatest", "max(range(2, 30, 9))",
     "the greatest entry of the range from two to thirty by nine"),
    ("str-least", "min('golay')",
     "the least entry of the string of five characters small g, small o, "
     "small l, small a, small y"),
    ("mixed", "len('abc') * 8 == 24",
     "the product of the length of the string of three characters small a, "
     "small b, small c and eight equals twenty-four"),
    # -- statements -------------------------------------------------------
    ("str-in", "'ice' in 'lattice'",
     "the string of three characters small i, small c, small e is in the "
     "string of seven characters small l, small a, small t, small t, small i, "
     "small c, small e"),
    ("str-less", "'apple' < 'apricot'",
     "the string of five characters small a, small p, small p, small l, "
     "small e is less than the string of seven characters small a, small p, "
     "small r, small i, small c, small o, small t"),
    ("tuple-equal", "(1, 2) == (1, 2)",
     "the tuple of two entries one, two equals the tuple of two entries one, "
     "two"),
    ("range-member", "10 in range(0, 20, 5)",
     "ten is in the range from zero to twenty by five"),
    # -- a program --------------------------------------------------------
    ("prog-seq", "s = 'ab'\nlen(s + s)",
     "let s be the string of two characters small a, small b. the result is "
     "the length of the concatenation of s and s."),
)


SAY_REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("seq-free-variable", "'ab'[x]", "NOT_IN_FRAGMENT"),
    ("str-plus-tuple", "'a' + (1,)", "SORT_MISMATCH"),
    ("total-of-string", "sum('ab')", "SORT_MISMATCH"),
    ("index-out", "'abc'[5]", "INDEX_OUT_OF_RANGE"),
    ("ord-two", "ord('ab')", "NOT_A_CHARACTER"),
    ("chr-out", "chr(1114112)", "NOT_A_CHARACTER"),
    ("min-empty", "min(range(0))", "EMPTY_SEQUENCE"),
    ("range-zero-step", "range(1, 5, 0)", "ZERO_STEP"),
    ("range-fraction", "range(Fraction(1, 2))", "NOT_INTEGER"),
    ("bool-entry", "(True, 'x')", "NOT_IN_FRAGMENT"),
)


READ_REFUSALS: Tuple[Tuple[str, str], ...] = (
    ("count-short", "the string of three characters small a, small b"),
    ("count-long", "the tuple of one entry one, two"),
    ("noncanonical-code-point",
     "the string of one character code point ninety-seven"),
    ("character-plural", "the string of two character small a, small b"),
    ("empty-count", "the string of zero characters"),
    ("capital-word", "the string of one character capital ab"),
    ("digit-ten", "the string of one character digit ten"),
    ("slice-default-step",
     "the slice of the empty string from one to two by the default"),
    ("tuple-zero", "the tuple of zero entries"),
)


#: The Phase 64 value programs acting on strings, tuples or ranges (22 of the
#: 47 the reverse grammar left outside in Phase 68), less the one below.
DIALECT_INSIDE: Tuple[str, ...] = (
    "str-slice", "str-reverse", "str-neg-slice", "str-clamp", "str-index",
    "str-ord", "str-chr", "str-concat", "str-len", "str-compare", "str-in",
    "str-long-slice", "comprehension-free", "tuple-slice", "tuple-compare",
    "tuple-nested", "tuple-len", "range-sum", "range-len", "range-tuple",
    "range-index",
)

#: Declared to stay outside, and why.
DIALECT_OUTSIDE: Tuple[Tuple[str, str], ...] = (
    ("tuple-concat", "it carries the boolean True, and booleans have no "
                     "sentence in the grammar yet"),
)

#: The battery: every term of depth at most two over these atoms (read as
#: dialect source) with the sequence operators of the study's §1.
SEQ_BATTERY_ATOMS: Tuple[str, ...] = (
    "'ab'", "''", "'Λ'", "(1, Fraction(1, 2))", "()", "range(0, 6, 2)",
)


# ===========================================================================
# 2.  THE DIALECT WIDENED
# ===========================================================================

STRING_METHOD_CASES: Tuple[Tuple[str, str], ...] = (
    ("upper", "'Golay code'.upper()"),
    ("lower", "'MOG Cube'.lower()"),
    ("upper-lower", "'Leech'.upper().lower() == 'leech'"),
    ("find", "'the leech lattice'.find('lattice')"),
    ("find-missing", "'abc'.find('z')"),
    ("find-empty", "'hello'.find('')"),
    ("index", "'abc'.index('c')"),
    ("count", "'banana'.count('an')"),
    ("count-overlap", "'aaaa'.count('aa')"),
    ("count-empty", "'banana'.count('')"),
    ("startswith", "'geometric'.startswith('geo')"),
    ("endswith", "'geometric'.endswith('ric')"),
    ("split-sep", "'a-b-c'.split('-')"),
    ("split-empty-fields", "'a,b,,c'.split(',')"),
    ("split-whitespace", "'  spaced   out words '.split()"),
    ("join-tuple", "'-'.join(('a', 'b', 'c'))"),
    ("join-list", "''.join(['x', 'y'])"),
    ("replace", "'banana'.replace('an', 'AN')"),
    ("replace-shrink", "'mississippi'.replace('ss', 's')"),
    ("replace-empty", "'ab'.replace('', '-')"),
    ("strip", "'  pad  '.strip()"),
    ("strip-chars", "'xxhixx'.strip('x')"),
    ("isdigit", "'2024'.isdigit()"),
    ("isalpha", "'abc1'.isalpha()"),
)

LIST_CASES: Tuple[Tuple[str, str], ...] = (
    ("literal", "[1, 2, 3]"),
    ("concat", "[1, Fraction(1, 2)] + [3]"),
    ("repeat", "[0] * 4"),
    ("index", "[5, 3, 9][1]"),
    ("reverse", "[5, 3, 9][::-1]"),
    ("len", "len([1, 2, 3])"),
    ("sum", "sum([Fraction(1, 2), Fraction(1, 3)])"),
    ("max", "max([4, 11, 7])"),
    ("sorted", "sorted([3, 1, 2])"),
    ("sorted-string", "sorted('golay')"),
    ("sorted-tuples", "sorted([(2, 'b'), (1, 'z'), (2, 'a')])"),
    ("list-range", "list(range(4))"),
    ("list-string", "list('abc')"),
    ("equal", "[1, 2] == [1, 2]"),
    ("not-a-tuple", "[1, 2] == (1, 2)"),
    ("order", "[1, 2] < [1, 3]"),
    ("member", "2 in [1, 2, 3]"),
    ("loop", "t = 0\nfor x in [3, 4, 5]:\n    t += x\nt"),
    ("unpack", "a, b = [1, 2]\na + b"),
    ("nested", "[(1, 'a'), (2, 'b')][1][1]"),
    ("snapshot", "xs = [1, 2]\nys = xs + [3]\n(xs, ys)"),
    ("to-tuple", "tuple([1, 2])"),
    ("split-then-add", "'a-b'.split('-') + ['c']"),
)

DICT_CASES: Tuple[Tuple[str, str], ...] = (
    ("index", "{'a': 1, 'b': 2}['b']"),
    ("bound", "d = {1: 'one', 2: 'two'}\nd[2]"),
    ("len", "len({'x': 1, 'y': 2})"),
    ("member", "'x' in {'x': 1}"),
    ("get-default", "{'a': 1}.get('z', 0)"),
    ("get", "{'a': 1}.get('a')"),
    ("equal-keys", "{1: 'a', True: 'b'}"),
    ("list-keys", "list({'b': 2, 'a': 1})"),
    ("sorted-keys", "sorted({'b': 2, 'a': 1})"),
    ("order-free-equality", "{'a': 1, 'b': 2} == {'b': 2, 'a': 1}"),
    ("loop", "d = {'a': 1, 'b': 2}\nt = 0\nfor k in d:\n    t += d[k]\nt"),
    ("items", "tuple({'a': 1, 'b': 2}.items())"),
    ("keys", "list({'a': 1}.keys())"),
    ("values", "sum({'a': 3, 'b': 4}.values())"),
    ("tuple-key", "{(1, 2): 'pair'}[(1, 2)]"),
    ("list-value", "{'k': [1, 2]}['k'][1]"),
)

DIALECT_REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("list-append", "a = [1, 2]\na.append(3)\na", "MUTABLE_CONTAINER"),
    ("list-item-assign", "a = [1, 2]\na[0] = 5\na", "MUTABLE_CONTAINER"),
    ("list-augassign", "a = [1]\na += [2]\na", "MUTABLE_CONTAINER"),
    ("dict-assign", "d = {}\nd['k'] = 1\nd", "MUTABLE_CONTAINER"),
    ("dict-update", "d = {'a': 1}\nd.update({'b': 2})\nd",
     "MUTABLE_CONTAINER"),
    ("set-literal", "{1, 2}", "MUTABLE_CONTAINER"),
    ("list-comprehension", "[x for x in range(3)]", "MUTABLE_CONTAINER"),
    ("list-overflow", "list(range(25))", "CARRIER_OVERFLOW"),
    ("upper-non-ascii", "'straße'.upper()", "OUTSIDE_SUBSTRATE"),
    ("split-non-ascii", "'a\\u00a0b'.split()", "OUTSIDE_SUBSTRATE"),
    ("dict-missing", "{'a': 1}['b']", "PYTHON_ERROR"),
    ("list-unhashable", "{[1]: 2}", "PYTHON_ERROR"),
    ("index-missing", "'abc'.index('z')", "PYTHON_ERROR"),
    ("split-empty-sep", "'abc'.split('')", "PYTHON_ERROR"),
    ("join-non-string", "'-'.join((1, 2))", "PYTHON_ERROR"),
    ("method-unsupported", "'abc'.encode()", "UNSUPPORTED"),
    ("dict-view-value", "{'a': 1}.keys()", "UNSUPPORTED"),
)

#: Phase 64 refusal cases this round answers on purpose: (id, source, the
#: refusal Phase 64 declared).
SUPERSEDED_REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("list-literal", "[1, 2, 3]", "MUTABLE_CONTAINER"),
    ("unsupported-attribute", "'abc'.upper()", "UNSUPPORTED"),
)
