"""``glm_universal.evaluation.ast_index_cases`` -- the declared cases of
Phase 105: the AST address as a retrieval key (round 9's item I3,
``studies/AST_INDEX_STUDY.md``).

Written and committed **before** any measuring code of the round.  The
scorer is :mod:`glm_universal.runtime.ast_index_report`.

* :data:`MATCH_PAIRS` -- pairs of expressions with the declared verdict of
  *structural equality*: equal up to a one-to-one renaming of variables and
  the order of the operands of ``+ * & | ^ == !=``, and nothing else (no
  associativity, no constant folding, no algebra).  Worked out by hand.
* :data:`QUESTIONS` -- questions for the new operation, each with the
  corpus it must search.  No count is declared: the operation must answer
  (a list of sites, possibly empty) and its column-3 script must verify.
* :data:`REFUSALS` -- questions the operation must refuse, with the code.
* :data:`MARKS` -- the ladder.
"""

from __future__ import annotations

from typing import Tuple

__all__ = ["MATCH_PAIRS", "QUESTIONS", "REFUSALS", "MARKS", "STRIDE",
           "PERTURBATIONS", "DECLARATION_ERRORS"]

#: Every ``STRIDE``-th site of the frozen index, in its stored order, is a
#: query site.
STRIDE = 25

#: The meaning-preserving perturbations applied to a query site's text.
PERTURBATIONS: Tuple[Tuple[str, str], ...] = (
    ("rename", "every variable renamed to a fresh name, one to one"),
    ("commute", "the operands of every + * & | ^ == != swapped"),
    ("both", "rename, then commute"),
)

#: ``(left, right, structurally_equal)``.
MATCH_PAIRS: Tuple[Tuple[str, str, bool], ...] = (
    # equal
    ("a + b", "b + a", True),
    ("a * b + c", "c + b * a", True),
    ("x * x + y * y", "q * q + p * p", True),
    ("(n * (n + 1)) // 2", "(m * (1 + m)) // 2", True),
    ("a - b", "x - y", True),
    ("f(a) + g(b)", "g(c) + f(d)", True),
    ("u.norm(k) * 2", "2 * w.norm(k)", True),
    ("a & mask | b", "b | mask2 & a", True),
    ("a if a > b else b", "x if x > y else y", True),
    ("t[i + 1] - t[i]", "s[j + 1] - s[j]", True),
    ("round(x * 3, ndigits=2)", "round(3 * y, ndigits=2)", True),
    ("(a == b) + 1", "1 + (b == a)", True),
    ("-a * b", "b * -a", True),
    ("p ** 2 % q", "r ** 2 % s", True),
    ("(a + b) * (a - b)", "(a - b) * (b + a)", True),
    ("x * y + y * x", "a * b + b * a", True),
    ("x * y + y * z", "b * c + a * b", True),
    ("v >> 3 ^ v", "w ^ w >> 3", True),
    ("a + 0.5", "0.5 + z", True),
    ("len(s) - 1", "len(t) - 1", True),
    # not equal
    ("a - b", "b - a", True),          # a renaming swaps them: still equal
    ("a - a", "a - b", False),
    ("a * b", "a * a", False),
    ("(a + b) + c", "a + (b + c)", False),   # no associativity
    ("a // b", "a / b", False),
    ("x ** 2", "x * x", False),              # no algebra
    ("f(a) + 1", "g(a) + 1", False),         # function names are fixed
    ("u.norm(k)", "u.size(k)", False),       # attribute names are fixed
    ("round(x, ndigits=2)", "round(x, ndigits=3)", False),
    ("round(x, ndigits=2)", "round(x)", False),
    ("a + 0.5", "a + 0.25", False),          # constants are exact
    ("a + 1", "a + True", False),
    ("a < b", "b < a", True),                # a renaming swaps them: equal
    ("a < b", "a > b", False),
    ("a and b", "b and a", True),            # a renaming swaps them: equal
    ("a and b or c", "a and (b or c)", False),
    ("t[i] + t[j]", "t[i] + s[j]", False),
    ("x * y + y * z", "a * b + c * d", False),
    ("a - b * c", "a - c * b + 0", False),
    ("-a", "~a", False),
)

#: ``(id, question, corpus)``; corpus is ``"all"``, ``"live"`` or
#: ``"archive"``.
QUESTIONS: Tuple[Tuple[str, str, str], ...] = (
    ("Q1", "where is `n * (n + 1) // 2` computed?", "all"),
    ("Q2", "where is `x * x + y * y` computed?", "all"),
    ("Q3", "where else is `(lo + hi) // 2` computed?", "all"),
    ("Q4", "where in the archive is `a ^ b >> 1` computed?", "archive"),
    ("Q5", "where in the live code is `q.numerator * 2` computed?", "live"),
    ("Q6", "where is `(a - b) % m` computed?", "all"),
    ("Q7", "where in the archive is `x * 2 ** k` computed?", "archive"),
    ("Q8", "where is `len(s) - 1` computed?", "all"),
    ("Q9", "where in the live code is `(a + b) * (a - b)` computed?", "live"),
    ("Q10", "where is `w >> 12 & 4095` computed?", "all"),
    ("Q11", "where in the archive is `sum(row) / len(row)` computed?",
     "archive"),
    ("Q12", "where is `zz_unused_name * 7919 + 104729` computed?", "all"),
)

#: ``(question, code)``.
REFUSALS: Tuple[Tuple[str, str], ...] = (
    ("where is `a + ` computed?", "NOT_AN_EXPRESSION"),
    ("where is `[x * 2 for x in xs]` computed?", "OUTSIDE_INDEX"),
    ("where is `lambda x: x + 1` computed?", "OUTSIDE_INDEX"),
    ("where is `f(x)` computed?", "NO_ARITHMETIC"),
    ("where is `x` computed?", "NO_ARITHMETIC"),
)

#: ``(id, statement)`` -- the ladder, as declared.
MARKS: Tuple[Tuple[str, str], ...] = (
    ("A1", "frozen: the snapshot's digest matches its content, and the "
           "measurement re-taken from it equals the stored measurement"),
    ("A2", "the matcher is right: every declared pair gets its declared "
           "verdict, and the matcher agrees with the brute-force reference "
           "on every pair of query and candidate it is asked about in the "
           "measurement (0 disagreements)"),
    ("A3", "the bucket key is invariant: under every perturbation of every "
           "query site, the perturbed text has the source's bucket key and "
           "matches the source structurally (100 %)"),
    ("A4", "the Phase 64 address is nearly invariant: its canonical form "
           "is unchanged under `both` on at least 95 % of query sites"),
    ("A5", "retrieval: under `both`, the structural key has a site "
           "structurally equal to the source at rank 1 on every query, and "
           "the token-overlap baseline at rank 1 on at most 75 % of them, "
           "with a sign test at most 0.05"),
    ("A6", "soundness: on every structural class of the index with two "
           "different spellings whose nodes are all integer arithmetic, the "
           "matcher's renaming gives equal values on every one of the "
           "declared integer environments (0 failures)"),
    ("A7", "the operation: every declared question answered and every "
           "declared refusal refused by its code; every answer's column-3 "
           "script verifies and every mutated script fails"),
)


#: Added after the first measurement, never edited into the pairs above: a
#: declared verdict the matcher and the reference both contradict, with why
#: the declaration, not the matcher, is wrong.  Mark A2 is scored against
#: the pairs as declared.
DECLARATION_ERRORS: Tuple[Tuple[str, str, str], ...] = (
    ("(a + b) + c", "a + (b + c)",
     "declared not equal as 'no associativity', but with three different "
     "variables the two are structurally equal: swap the outer operands of "
     "the second, `(b + c) + a`, and rename b->a, c->b, a->c.  Associativity "
     "is not used; renaming does the work."),
)
