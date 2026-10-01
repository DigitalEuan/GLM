"""``glm_universal.evaluation.integer_decision_cases`` -- the complete integer
decision's corpus.

The held-out corpus of ``studies/INTEGER_DECISION_STUDY.md`` (Phase 79),
written and committed before any code of the round.  Every question below is
one that round three of Reverse Three Column Thinking (``reverse_tct_int``,
Phase 69) refuses ``INTEGER_UNDECIDED``: its elimination with rounding is
sound but not complete, and no integer point turned up in its search.  Every
system is bounded -- by its own rows or by a declared box -- so the expected
answer is the exact truth, found by enumerating the box.

* :data:`BOX` -- the box every boxed question carries, per variable.
* :data:`ENTAIL_CASES` -- ``entails over the integers:`` questions: premises
  (the box is added for every variable when ``boxed`` is true), conclusion,
  declared verdict.
* :data:`BOUNDS_CASES` -- ``bounds over the integers of x:`` questions, with
  the declared answer sentence or refusal.
* :data:`BATTERY` -- the declared random battery (mark Z3): the generator's
  seed, size and ranges, fixed here so the battery cannot be re-drawn after
  the code exists.
* :data:`NODE_LIMIT` -- the declared resource limit; ``INTEGER_UNDECIDED``
  now means exactly that this limit was reached.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

__all__ = ["BOX", "ENTAIL_CASES", "BOUNDS_CASES", "BATTERY", "NODE_LIMIT",
           "boxed_premises", "battery_questions"]

#: The box a boxed question carries, per variable (inclusive).
BOX = (-10, 10)

#: Most search nodes (eliminations, substitutions and splinter cases) one
#: case may spend before the decision refuses ``INTEGER_UNDECIDED``.
NODE_LIMIT = 5000


def boxed_premises(premises: Tuple[str, ...], variables: Tuple[str, ...],
                   box: Tuple[int, int] = BOX) -> Tuple[str, ...]:
    """``premises`` followed by the box on every variable, in order."""
    lo, hi = box
    return tuple(premises) + tuple(
        s for v in variables for s in (f"{lo} <= {v}", f"{v} <= {hi}"))


# (id, premises, variables to box (empty: none), conclusion, verdict)
ENTAIL_CASES: Tuple[Tuple[str, Tuple[str, ...], Tuple[str, ...], str, str],
                    ...] = (
    # Pugh's example: a parallelogram with no integer point inside it.
    ("d01", ("27 <= 11 * x + 13 * y", "11 * x + 13 * y <= 45",
             "-10 <= 7 * x - 9 * y", "7 * x - 9 * y <= 4"), (),
     "x == 0", "INCONSISTENT_PREMISES"),
    ("d02", ("-6 * x + 7 * y == -2", "-9 * x - 7 * y <= -2"), ("x", "y"),
     "x <= 4", "CONTRADICTS"),
    ("d03", ("8 * x + 3 * y == 4", "-8 * x + 3 * y <= -11",
             "-9 * x - 8 * y >= -18"), ("x", "y"), "y >= -5", "ENTAILS"),
    ("d04", ("-9 * x - 3 * y <= 13", "9 * x + 9 * y <= -2",
             "6 * x + y <= -7"), ("x", "y"), "y >= 0", "CONTRADICTS"),
    ("d05", ("-2 * x - 5 * y >= -25", "-1 * x + 8 * y >= 23"), ("x", "y"),
     "x <= 3", "ENTAILS"),
    ("d06", ("7 * x - 9 * y == 10", "-9 * x + 6 * y <= 13"), ("x", "y"),
     "y >= -2", "ENTAILS"),
    ("d07", ("9 * x - 8 * y + 5 * z == 7", "4 * x - 9 * y - 5 * z <= -3"),
     ("x", "y", "z"), "x + y != 3", "ENTAILS"),
    ("d08", ("5 * x - 3 * y >= -13", "7 * x - 8 * y <= 1"), ("x", "y"),
     "y >= -4", "ENTAILS"),
    ("d09", ("-3 * x + 8 * y == 9", "-2 * x + 5 * y <= 17"), ("x", "y"),
     "y >= 0", "ENTAILS"),
    ("d10", ("4 * x - 3 * y <= 12", "8 * x - 3 * y == -1",
             "-2 * x + 8 * y <= 2"), ("x", "y"), "y >= 0", "CONTRADICTS"),
    ("d11", ("-9 * x - 2 * y <= 5", "7 * x - 4 * y == -16"), ("x", "y"),
     "x == 0", "ENTAILS"),
    ("d12", ("2 * x - 9 * y + 9 * z == -3", "8 * x + 4 * y - 2 * z <= 2",
             "4 * x - 3 * y - 4 * z <= 6"), ("x", "y", "z"), "x <= -3",
     "ENTAILS"),
    ("d13", ("-6 * x - 6 * y + 7 * z == -30", "-7 * x + 8 * y + 5 * z == -11"),
     ("x", "y", "z"), "x <= 4", "INCONSISTENT_PREMISES"),
    ("d14", ("6 * y <= 18", "7 * x - 4 * y == 22"), ("x", "y"), "y >= 1",
     "CONTRADICTS"),
    ("d15", ("-1 * x - 8 * y <= -30", "7 * x + 8 * y == -18"), ("x", "y"),
     "x == 0", "INCONSISTENT_PREMISES"),
    ("d16", ("3 * x - 8 * y == -28", "-3 * x + y >= 21"), ("x", "y"),
     "x <= 4", "INCONSISTENT_PREMISES"),
)


# (id, premises, variables to box, declared answer sentence or refusal)
BOUNDS_CASES: Tuple[Tuple[str, Tuple[str, ...], Tuple[str, ...], str], ...] = (
    ("e01", ("-9 * x - 1 * y + 9 * z <= -11", "-3 * x - 4 * y + 3 * z == 24"),
     ("x", "y", "z"), "x is at least negative six, and x is at most ten"),
    ("e02", ("6 * x + 5 * y - 7 * z == 17", "8 * x + 7 * y >= -29"),
     ("x", "y", "z"), "x is at least negative nine, and x is at most ten"),
    ("e03", ("-8 * x - 5 * y - 9 * z == -13", "5 * x - 8 * y - 7 * z <= -13",
             "-2 * x + 9 * y + 3 * z <= 21"), ("x", "y", "z"),
     "x is at least negative six, and x is at most negative three"),
    ("e04", ("-9 * x + 5 * y + 9 * z == -12", "7 * x + 2 * y - 2 * z >= 5",
             "x - 5 * y + z >= 20"), ("x", "y", "z"),
     "x is at least five, and x is at most eight"),
    ("e05", ("8 * x + 3 * y - 2 * z >= -10", "8 * x - 5 * y - 3 * z == -22",
             "-4 * x - 8 * y + 4 * z >= -4"), ("x", "y", "z"),
     "x equals zero"),
    ("e06", ("-5 * x + 3 * y - 8 * z == -17", "2 * x + 5 * y + 4 * z == 2"),
     ("x", "y", "z"), "INCONSISTENT_PREMISES"),
)


#: Z3: the declared random battery.  Each draw is one system of ``rows``
#: rows over two or three variables, coefficients and constants uniform in
#: the declared ranges, relation uniform over ``relations``, inside
#: ``box``; each system is asked once as an ``entails`` question (the
#: conclusion drawn from ``conclusions``) and once as ``bounds`` of ``x``.
BATTERY: Dict[str, object] = {
    "seed": 79,
    "draws": 300,
    "variables": (("x", "y"), ("x", "y", "z")),
    "rows": (2, 3),
    "coefficient": (-9, 9),
    "constant": (-30, 30),
    "relations": ("<=", ">=", "<=", ">=", "=="),
    "box": (-6, 6),
    "conclusions": ("x == 0", "x <= 2", "x + y != 1", "y >= -1"),
}


def _lcg(seed: int):
    """The battery's integer generator: the 64-bit linear congruential
    generator of Knuth's MMIX, top 31 bits out.  Declared with the battery so
    the draw is fixed before any code of the round exists."""
    state = seed
    while True:
        state = (6364136223846793005 * state + 1442695040888963407) % (1 << 64)
        yield state >> 33


def battery_questions() -> List[Tuple[str, Tuple[str, ...], Tuple[str, ...],
                                      str]]:
    """The declared battery, in order: ``(id, variables, premises (box
    included), conclusion)`` -- each system once, asked by the study as an
    ``entails`` question with this conclusion and as ``bounds`` of ``x``."""
    b = BATTERY
    gen = _lcg(b["seed"])

    def pick(lo: int, hi: int) -> int:
        return lo + next(gen) % (hi - lo + 1)

    out = []
    lo, hi = b["box"]
    for n in range(b["draws"]):
        vs = b["variables"][pick(0, len(b["variables"]) - 1)]
        rows = []
        for _ in range(b["rows"][pick(0, len(b["rows"]) - 1)]):
            co = [pick(*b["coefficient"]) for _ in vs]
            if not any(co):
                co[0] = 1
            terms = [f"{c} * {v}" for c, v in zip(co, vs) if c]
            k = pick(*b["constant"])
            rel = b["relations"][pick(0, len(b["relations"]) - 1)]
            rows.append(f"{' + '.join(terms)} {rel} {k}")
        concl = b["conclusions"][pick(0, len(b["conclusions"]) - 1)]
        out.append((f"z{n + 1:03d}", tuple(vs),
                    boxed_premises(tuple(rows), tuple(vs), (lo, hi)), concl))
    return out
