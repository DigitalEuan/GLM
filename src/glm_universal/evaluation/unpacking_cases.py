"""``glm_universal.evaluation.unpacking_cases`` -- the declared cases of Phase 97.

The probes and marks of ``studies/UNPACKING_RESCORE_STUDY.md`` §2, written and
committed before any code of the round.  Phase 96 (round 8 of the order of
work, *second readings*) closed with 7 of 9 marks met.  Its two misses were
both misses of the declaration rather than of the register:

* **V8** -- the declared program ``read_views(*store_views(...))`` was refused
  because the Python dialect had never admitted argument unpacking.  This
  round adds argument unpacking to the dialect -- ``f(*xs)`` at a call and
  ``def f(a, *rest)`` at a definition -- and re-scores that program as a
  fresh declared case (U1), beside fresh programs that use the construct
  (U2, U3) and the refusals that must stay (U4).
* **V4** -- X1's probe through the two-view register was declared on a false
  analogy: the register's second view reads X1's second error *rotated*.
  Under independent faults the frame cannot help at all (each view's error
  is its own, and a rotation is a bijection on the four-sets), so the mark
  is re-declared correctly on a fresh probe (R4-R7), with the third view.

The round also asks whether the register's reads can be made cheaper without
changing an answer: the **third view on demand** (R1-R3) reads views 0 and 1,
and reads view 3 only when the first two leave the fork open.

Nothing here is random (D7): every probe is a fixed stride or a full census.

* :data:`RESCORED` -- U1: the Phase 96 program, re-scored as a fresh case.
* :data:`CALL_CASES` -- U2: ``(id, source)`` with unpacking at a call.
* :data:`VARARG_CASES` -- U3: ``(id, source)`` with ``*rest`` at a definition.
* :data:`UNPACK_REFUSALS` -- U4: ``(id, source, refusal name)``.
* :data:`FRESH_CODEWORD_OFFSET` -- R4-R6: the codewords at indices
  ``32 + 64 i``, ``i < 64`` (X1's began at 0).
* :data:`FRESH_ERROR_START` / :data:`FRESH_ERROR_STRIDE` /
  :data:`FRESH_ERROR_COUNT` -- R4-R6: the weight-4 errors at indices
  ``5 + 883 j``, ``j < 12``, of the 10,626 four-sets in lexicographic order.
* :data:`CENSUS_STRIDE` -- R7: the first errors at indices ``442 j``,
  ``j < 24``.
* :data:`OPEN_SECONDS` -- R7: the declared number of second errors that leave
  two views open, for every first error and every single second frame.
* :data:`SCOPED` -- figures computed while the round was scoped, before this
  file; reported as such and never scored as results.
"""

from __future__ import annotations

from typing import Dict, Tuple

__all__ = ["RESCORED", "CALL_CASES", "VARARG_CASES", "UNPACK_REFUSALS",
           "FRESH_CODEWORD_OFFSET", "FRESH_CODEWORD_STRIDE",
           "FRESH_ERROR_START", "FRESH_ERROR_STRIDE", "FRESH_ERROR_COUNT",
           "CENSUS_STRIDE", "CENSUS_COUNT", "OPEN_SECONDS",
           "PREDICTED_COMMON", "SCOPED", "MARKS"]

#: The declared marks, by name; the study's §2 states each in full.
MARKS: Tuple[str, ...] = (
    "U1 the refused Phase 96 program, re-scored: equal to CPython, column 3 "
    "verified, mutant rejected; all of Phase 96's dialect cases as declared",
    "U2 unpacking at a call: every declared program equal to CPython, "
    "scripts verified, mutants rejected",
    "U3 *rest at a definition: every declared program equal to CPython, "
    "scripts verified, mutants rejected",
    "U4 the declared refusals, each by its declared name",
    "U5 no regression: no earlier declared dialect case moves, and the "
    "differential battery is unchanged",
    "R1 the third view on demand: the same answer as three views on every "
    "common-mode four-error read, the third view read only where two leave "
    "the fork open",
    "R2 inside the packing radius the third view is never read",
    "R3 the price outside the fault model: on weight-5 bursts the on-demand "
    "register gives the two-view register's verdicts",
    "R4 independent faults, two views, fresh probe: live count predicted, "
    "0 wrong",
    "R5 independent faults, three views, fresh probe: live count predicted, "
    "0 wrong",
    "R6 independent faults, on demand: the three-view answer on every read",
    "R7 the frame cannot help two views under independent faults: 346 open "
    "second errors for every first error and every frame",
)

#: U1.  Phase 96's ``views-clean``, refused then as ``UNSUPPORTED``.
RESCORED: Tuple[str, str] = (
    "views-clean-rescored",
    "read_views(*store_views(golay_encode(1234)))")

#: U2.  Unpacking at a call: user functions, builtins, a method, the
#: register's builtins; tuples, lists, ranges, strings and dicts unpacked.
CALL_CASES: Tuple[Tuple[str, str], ...] = (
    ("star-user-fn",
     "def f(a, b, c):\n    return a * 100 + b * 10 + c\nf(*(1, 2, 3))"),
    ("star-mixed",
     "def f(a, b, c, d):\n    return (a, b, c, d)\nf(1, *(2, 3), 4)"),
    ("star-two",
     "def f(a, b, c, d):\n    return a - b + c - d\nf(*(10, 3), *[4, 1])"),
    ("star-range", "max(*range(3, 40, 7))"),
    ("star-string", "min(*'glm')"),
    ("star-dict",
     "def f(a, b):\n    return a + b\nf(*{'x': 1, 'y': 2})"),
    ("star-empty", "def f():\n    return 7\nf(*())"),
    ("star-divmod", "divmod(*(17, 5))"),
    ("star-fraction", "Fraction(*(6, 4))"),
    ("star-returned",
     "def g():\n    return (3, 4)\n"
     "def h(a, b):\n    return a * a + b * b\nh(*g())"),
    ("star-pow", "pow(*(3, 4, 5))"),
    ("star-method", "'-'.join(*[('a', 'b', 'c')])"),
    ("star-views-two",
     "w = store_views(golay_encode(300))\n"
     "read_views(*(w[0] ^ 0b100010001, w[1] ^ 0b100010001))"),
    ("star-views-slice",
     "w = list(store_views(golay_encode(55)))\nread_views(*w[:2])"),
)

#: U3.  ``*rest`` at a definition, alone and after positional parameters,
#: with loops, recursion and the register's builtins.
VARARG_CASES: Tuple[Tuple[str, str], ...] = (
    ("vararg-tuple", "def f(*args):\n    return args\nf(1, 2, 3)"),
    ("vararg-none", "def f(*args):\n    return len(args)\nf()"),
    ("vararg-after",
     "def f(a, *rest):\n    return (a, rest)\nf(1, 2, 3)"),
    ("vararg-loop",
     "def total(*xs):\n    s = 0\n    for x in xs:\n        s = s + x\n"
     "    return s\ntotal(*range(1, 11))"),
    ("vararg-string", "def f(*args):\n    return args\nf(*'abc')"),
    ("vararg-recursive",
     "def mx(a, *rest):\n    if not rest:\n        return a\n"
     "    m = mx(*rest)\n    return a if a > m else m\nmx(3, 9, 2, 7)"),
    ("vararg-fraction",
     "def f(a, b, *rest):\n    return sum(rest) - a * b\n"
     "f(2, 3, Fraction(1, 2), Fraction(1, 3))"),
    ("vararg-views",
     "def wrap(*views):\n    return read_views(*views)\n"
     "w = store_views(golay_encode(1234))\n"
     "wrap(w[0] ^ 0b1111, w[1] ^ 0b1111, w[2] ^ 0b1111)"),
)

#: U4.  What must still be refused, and by which name.
UNPACK_REFUSALS: Tuple[Tuple[str, str, str], ...] = (
    ("star-not-iterable", "max(*5)", "PYTHON_ERROR"),
    ("star-too-many",
     "def f(a, b):\n    return a + b\nf(*(1, 2, 3))", "PYTHON_ERROR"),
    ("vararg-missing",
     "def f(a, *rest):\n    return rest\nf()", "PYTHON_ERROR"),
    ("kwargs-def", "def f(**kw):\n    return 1\nf()", "UNSUPPORTED"),
    ("kwonly-def", "def f(*args, k):\n    return k\nf(1)", "UNSUPPORTED"),
    ("kwargs-call",
     "def f(a):\n    return a\nf(**{'a': 1})", "UNSUPPORTED"),
    ("star-set", "len(*frozenset({1, 2}))", "ORDER_UNDEFINED"),
    ("star-display", "[*range(3)]", "UNSUPPORTED"),
    ("vararg-overflow",
     "def f(*a):\n    return a\nf(*range(30))", "CARRIER_OVERFLOW"),
    ("default-def", "def f(a=1):\n    return a\nf()", "UNSUPPORTED"),
)

#: R4-R6: the fresh codeword probe (X1's began at index 0).
FRESH_CODEWORD_OFFSET = 32
FRESH_CODEWORD_STRIDE = 64

#: R4-R6: the fresh error list.
FRESH_ERROR_START = 5
FRESH_ERROR_STRIDE = 883
FRESH_ERROR_COUNT = 12

#: R7: the first errors of the census, and how many.
CENSUS_STRIDE = 442
CENSUS_COUNT = 24

#: R7: second errors that leave two views open, per first error, any frame:
#: the five octads through the first error hold 70 four-sets each, any two
#: of them share only the first error itself, so 5 * 69 + 1.
OPEN_SECONDS = 346

#: R1-R3: what the on-demand register is predicted to do on Phase 96's
#: probe (64 codewords at stride 64), from Phase 96's measured figures: the
#: third view is read on the 174 open bursts of every codeword, never inside
#: the radius, and on weight 5 it stops where two views stop.
PREDICTED_COMMON: Dict[str, int] = {
    "reads": 680_064,
    "third_reads": 174 * 64,
    "inside_third_reads": 0,
    "weight5_reads": 2_720_256,
    "weight5_wrong": 384,
}

#: Figures computed while the round was scoped, before this file was
#: written: over all ordered pairs of independent weight-4 errors, two views
#: leave 3,676,596 of 112,911,876 open (3.26 %), whatever the frame; over all
#: ordered triples three views leave 260,294,496 of 1,199,801,594,376 open
#: (0.0217 %).  Both by inclusion-exclusion over the size of the union.
SCOPED: Dict[str, int] = {
    "pair_open_all": 3_676_596,
    "pair_total_all": 112_911_876,
    "triple_open_all": 260_294_496,
    "triple_total_all": 1_199_801_594_376,
}
