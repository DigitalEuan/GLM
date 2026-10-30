"""``glm_universal.evaluation.imperative_cases`` -- the declared cases of Phase 95.

The held-out corpus of ``studies/IMPERATIVE_GRAMMAR_STUDY.md`` §2, written and
committed before :mod:`glm_universal.reasoning.reverse_tct_imp` existed.
Every expected sentence below was worked by hand from the grammar of the
study's §1.  CPython (with the dialect's prelude) is the reference for every
value.

The second half of round 7 of the order of work: M's imperative grammar --
sentences for assignment, loops, branches, functions and ``match``, so that
the Phase 64 programs with state have sentences.

* :data:`SAY_CASES` -- ``(id, source, sentence)``: the program sentence the
  reverse surface must generate, word for word.  The value it carries is
  CPython's, computed from the source, so it is not written here.
* :data:`PHASE64_STATE` -- the 7 Phase 64 value programs with state that
  were refused ``NOT_IN_FRAGMENT`` by every earlier sort; each must now be
  said, read back to the same structure, and carry CPython's value.
* :data:`PROGRAM_CASES` -- ``(id, source)``: further programs whose sentences
  were not worked by hand; each must be said, read back and equal CPython.
* :data:`SAY_REFUSALS` -- ``(id, source, refusal)``.
* :data:`READ_REFUSALS` -- ``(id, sentence)``: sentences outside the grammar,
  refused ``UNREADABLE``.
* :data:`NEW_REFUSAL_NAMES` -- the refusal names the round adds.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["SAY_CASES", "PHASE64_STATE", "PROGRAM_CASES", "SAY_REFUSALS",
           "READ_REFUSALS", "NEW_REFUSAL_NAMES", "LIMIT_SCALE"]

#: Refusal names the imperative grammar adds to the reverse study's.
NEW_REFUSAL_NAMES: Tuple[str, ...] = (
    "STEP_LIMIT", "DEPTH_LIMIT", "NO_RESULT", "UNBOUND", "ARITY")

#: Mark I9: every answer must be unchanged when both limits are multiplied
#: by this factor.
LIMIT_SCALE = 10


# ===========================================================================
# 1.  SENTENCES WORKED BY HAND
# ===========================================================================

SAY_CASES: Tuple[Tuple[str, str, str], ...] = (
    ("imp-for-sum",
     "s = 0\nfor k in range(4):\n    s += k\ns",
     "the program of two steps: set s to zero; for each k in the range from "
     "zero to four by one, do one step: set s to the sum of s and k. the "
     "result is s."),
    ("imp-while-halve",
     "n = 40\nc = 0\nwhile n > 1:\n    n = n // 2\n    c += 1\nc",
     "the program of three steps: set n to forty; set c to zero; while n is "
     "greater than one, do two steps: set n to the floor quotient of n and "
     "two; set c to the sum of c and one. the result is c."),
    ("imp-swap",
     "a, b = 3, 5\na, b = b, a\n(a, b)",
     "the program of two steps: set together two names a, b to three, five; "
     "set together two names a, b to b, a. the result is the tuple of two "
     "entries a, b."),
    ("imp-if-else",
     "x = 7\nif x % 2 == 0:\n    y = 'e'\nelse:\n    y = 'o'\ny",
     "the program of two steps: set x to seven; if the remainder of x and "
     "two equals zero, do one step: set y to the string of one character "
     "small e otherwise do one step: set y to the string of one character "
     "small o. the result is y."),
    ("imp-if-no-else",
     "x = -3\nif x < 0:\n    x = -x\nx",
     "the program of two steps: set x to negative three; if x is less than "
     "zero, do one step: set x to the negation of x otherwise do nothing. "
     "the result is x."),
    ("imp-def",
     "def sq(n):\n    return n * n\nsq(9)",
     "the program of one step: define sq of one parameter n as do one step: "
     "return the product of n and n. the result is the call of sq on one "
     "argument nine."),
    ("imp-choice",
     "x = 2\ny = 'big' if x > 1 else 'small'\ny",
     "the program of two steps: set x to two; set y to the choice of the "
     "string of three characters small b, small i, small g when x is greater "
     "than one, else the string of five characters small s, small m, small "
     "a, small l, small l. the result is y."),
    ("imp-match",
     "def kind(v):\n    match v:\n        case 0:\n            return 'z'\n"
     "        case _:\n            return 'n'\nkind(3)",
     "the program of one step: define kind of one parameter v as do one "
     "step: match v against two cases: in case the literal zero, do one "
     "step: return the string of one character small z; in case anything, "
     "do one step: return the string of one character small n. the result "
     "is the call of kind on one argument three."),
    ("imp-reserved-name",
     "total = 1\nfor k in range(3):\n    total *= 2\ntotal",
     "the program of two steps: set the variable total to one; for each k in "
     "the range from zero to three by one, do one step: set the variable "
     "total to the product of the variable total and two. the result is the "
     "variable total."),
    ("imp-string-loop",
     "out = ''\nfor ch in 'ab':\n    out = ch + out\nout",
     "the program of two steps: set out to the empty string; for each ch in "
     "the string of two characters small a, small b, do one step: set out to "
     "the concatenation of ch and out. the result is out."),
    ("imp-nested-loop",
     "c = 0\nfor i in range(3):\n    for j in range(i):\n        c += 1\nc",
     "the program of two steps: set c to zero; for each i in the range from "
     "zero to three by one, do one step: for each j in the range from zero "
     "to i by one, do one step: set c to the sum of c and one. the result "
     "is c."),
    ("imp-recursive-fib",
     "def fib(n):\n    if n < 2:\n        return n\n"
     "    return fib(n - 1) + fib(n - 2)\nfib(10)",
     "the program of one step: define fib of one parameter n as do two "
     "steps: if n is less than two, do one step: return n otherwise do "
     "nothing; return the sum of the call of fib on one argument the "
     "difference of n and one and the call of fib on one argument the "
     "difference of n and two. the result is the call of fib on one "
     "argument ten."),
    ("imp-two-params",
     "def area(w, h):\n    return w * h\narea(3, 4)",
     "the program of one step: define area of two parameters w, h as do one "
     "step: return the product of w and h. the result is the call of area "
     "on two arguments three, four."),
)


# ===========================================================================
# 2.  THE PHASE 64 PROGRAMS WITH STATE
# ===========================================================================

#: Ids in ``python_speech_cases.VALUE_CASES``.
PHASE64_STATE: Tuple[str, ...] = (
    "loop-acc", "while-gcd", "def-fact", "def-harmonic", "if-else",
    "match-literal", "match-guard")


# ===========================================================================
# 3.  FURTHER PROGRAMS -- VALUES AGAINST CPYTHON
# ===========================================================================

PROGRAM_CASES: Tuple[Tuple[str, str], ...] = (
    ("p-collatz",
     "n = 27\nc = 0\nwhile n != 1:\n    if n % 2 == 0:\n        n = n // 2\n"
     "    else:\n        n = 3 * n + 1\n    c += 1\nc"),
    ("p-gcd-func",
     "def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a\n"
     "gcd(1071, 462)"),
    ("p-power-mod",
     "def pm(b, e, m):\n    r = 1\n    while e > 0:\n        if e % 2 == 1:\n"
     "            r = r * b % m\n        b = b * b % m\n        e = e // 2\n"
     "    return r\npm(3, 200, 1000003)"),
    ("p-digit-sum",
     "n = 987654321\ns = 0\nwhile n > 0:\n    s += n % 10\n    n //= 10\ns"),
    ("p-reverse-string",
     "w = 'Golay'\nout = ''\nfor ch in w:\n    out = ch + out\nout"),
    ("p-count-vowels",
     "c = 0\nfor ch in 'geometric language':\n    if ch in 'aeiou':\n"
     "        c += 1\nc"),
    ("p-tuple-build",
     "t = ()\nfor k in range(5):\n    t = t + (k * k,)\nt"),
    ("p-max-loop",
     "best = 0\nfor x in (3, 9, 2, 7):\n    if x > best:\n        best = x\n"
     "best"),
    ("p-elif",
     "def grade(s):\n    if s >= 90:\n        return 'A'\n    elif s >= 80:\n"
     "        return 'B'\n    else:\n        return 'C'\n"
     "(grade(95), grade(85), grade(10))"),
    ("p-fact-iter",
     "f = 1\nfor k in range(1, 21):\n    f *= k\nf"),
    ("p-fib-iter",
     "a, b = 0, 1\nfor _ in range(50):\n    a, b = b, a + b\na"),
    ("p-basel-partial",
     "s = Fraction(0)\nfor k in range(1, 11):\n    s += Fraction(1, k * k)\ns"),
    ("p-match-str",
     "def color(c):\n    match c:\n        case 'r':\n            return 1\n"
     "        case 'g' | 'b':\n            return 2\n        case _:\n"
     "            return 0\n(color('r'), color('b'), color('x'))"),
    ("p-match-seq",
     "def first(p):\n    match p:\n        case (x, y):\n            return x\n"
     "        case (x, y, z):\n            return z\n    return 0\n"
     "(first((1, 2)), first((4, 5, 6)), first(7))"),
    ("p-ackermann",
     "def ack(m, n):\n    if m == 0:\n        return n + 1\n    if n == 0:\n"
     "        return ack(m - 1, 1)\n    return ack(m - 1, ack(m, n - 1))\n"
     "ack(2, 3)"),
    ("p-choice-nested",
     "x = 5\nlabel = 'neg' if x < 0 else ('zero' if x == 0 else 'pos')\n"
     "label"),
    ("p-triangle",
     "def tri(n):\n    t = 0\n    for k in range(n + 1):\n        t += k\n"
     "    return t\ntri(100)"),
    ("p-binary-digits",
     "def bits(n):\n    s = ''\n    while n > 0:\n"
     "        s = chr(48 + n % 2) + s\n        n //= 2\n    return s\n"
     "bits(37)"),
    ("p-sum-of-squares",
     "def sq(x):\n    return x * x\ndef sumsq(n):\n    t = 0\n"
     "    for k in range(1, n + 1):\n        t += sq(k)\n    return t\n"
     "sumsq(10)"),
    ("p-subtract-loop",
     "a, b = 10, 3\nwhile a >= b:\n    a = a - b\na"),
    ("p-every-other",
     "w = 'lattice'\nout = ''\nfor i in range(len(w)):\n    if i % 2 == 0:\n"
     "        out = out + w[i]\nout"),
)


# ===========================================================================
# 4.  REFUSALS
# ===========================================================================

SAY_REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("r-step-limit", "x = 0\nwhile 1:\n    x += 1\nx", "STEP_LIMIT"),
    ("r-depth", "def f(n):\n    return f(n + 1)\nf(0)", "DEPTH_LIMIT"),
    ("r-no-result", "def f(n):\n    x = n\nf(1)", "NO_RESULT"),
    ("r-unbound-local",
     "def f():\n    y = x + 1\n    x = 2\n    return y\nf()", "UNBOUND"),
    ("r-unbound-loop", "s = 0\nfor k in ():\n    s = 1\nk", "UNBOUND"),
    ("r-arity", "def f(a, b):\n    return a\nf(1)", "ARITY"),
    ("r-div-zero",
     "x = 0\nfor k in range(3):\n    x = Fraction(1, k - 2)\nx",
     "DIVISION_BY_ZERO"),
    ("r-truthy-string", "s = 'a'\nif s:\n    s = 'b'\ns", "SORT_MISMATCH"),
    ("r-sum-of-strings", "def f(s):\n    return s + s\nf('ab')",
     "SORT_MISMATCH"),
    ("r-index", "def g(t):\n    return t[5]\ng((1, 2))", "INDEX_OUT_OF_RANGE"),
    ("r-break", "c = 0\nfor k in range(3):\n    break\nc", "NOT_IN_FRAGMENT"),
    ("r-method-call", "xs = (1,)\nxs.append(2)\nxs", "NOT_IN_FRAGMENT"),
    ("r-nested-def",
     "def f(n):\n    def g(m):\n        return m\n    return g(n)\nf(1)",
     "NOT_IN_FRAGMENT"),
    ("r-return-top", "return 1", "NOT_IN_FRAGMENT"),
)

READ_REFUSALS: Tuple[Tuple[str, str], ...] = (
    ("count-mismatch",
     "the program of two steps: set x to one. the result is x."),
    ("bare-grammar-word",
     "the program of one step: set total to one. the result is total."),
    ("needless-variable",
     "the program of one step: set the variable x to one. the result is the "
     "variable x."),
    ("together-one",
     "the program of one step: set together one names x to one. the result "
     "is x."),
    ("missing-otherwise",
     "the program of one step: if x is less than one, do one step: set x to "
     "one. the result is x."),
    ("zero-steps",
     "the program of one step: define f of one parameter n as do zero steps. "
     "the result is one."),
    ("literal-pattern-variable",
     "the program of one step: match x against one case: in case the literal "
     "y, do one step: set x to one. the result is x."),
)
