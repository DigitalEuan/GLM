"""``glm_universal.wheels.next_term_battery`` -- a pre-registered battery of
next-term questions (*what comes next in 1, 1, 2, 5, 14, 42*) and its
measurement over the ``sequence`` kind.

*Created 1 November 2026 (Phase 186: intake absorption).*
*Last altered 1 November 2026 (Phase 186: the ``next`` reading's offset-0/1
junction rule added after the first measurement, which answered control
``C05``; both measurements are kept -- see "The measured figures" below.  The
questions, the expected terms and the controls are unchanged).*

Pre-registration
----------------
The questions, their expected next terms and the negative controls below were
written **before** the ``next`` reading of
:func:`glm_universal.wheels.sequence_query.resolve_query` existed and before
any of them was put to it: they were chosen as well-known integer sequences
(and well-known traps), not by asking which ones the wheel answers.  The
author had seen the list of the wheel's entries (the reading has to be written
against it), so some battery sequences are on the wheel and some are not; a
sequence whose stored terms begin at a different index (the Fibonacci numbers
from ``F(0) = 0``, the squares from ``0``) is asked from both ends on purpose.
Nothing was removed or re-worded after the measurement.

The expected next term of every question is computed **here**, by a closed
form or a recurrence of the sequence (trial division for the primes and the
composites, the Bell triangle, Euler's pentagonal recurrence for the
partitions, ...), never read from the wheel's data; the question text is
built from the same computation, so text and answer cannot drift apart.

The negative controls are questions whose correct outcome is a refusal:
arbitrary lists no standard rule continues, prefixes of fewer than three
terms, and *junctions* -- short prefixes that two standard sequences share and
then continue differently.  For every junction control the module computes
both rules and checks that they agree on the prefix and disagree on the next
term (:func:`check_battery`).  One junction control (``1, 2, 4, 8, 16``:
powers of 2 give 32, Moser's circle regions give 31) involves a rule the
wheel does not hold; the battery keeps it, so the measurement shows what the
junction rule cannot see.

The measurement
---------------
:func:`measure_next_terms` puts every question to three readers and counts,
in exact integers:

* **with the wheels** -- :func:`resolve_query` as it is now, the ``next``
  reading included (an answer is the next term it states);
* **with the wheels, first rule** -- the same with
  ``offset_junctions=False``: the ``next`` reading as it was first written and
  first measured (prefix entries only), kept so that measurement can be
  reproduced;
* **without the new reading** -- :func:`resolve_query` with
  ``next_terms=False``: the ``sequence`` kind as it was before Phase 186, the
  path the command line took.  An identification it gives (a question worded
  with *sequence*, e.g. *continue the sequence ...*) is credited with the term
  its reply states after the claim, the most generous reading of it; every
  other question is unrecognised by the sequence kind.  Before the new
  reading was written (1 November 2026), ``src/GLM.py -q`` was run on all 58
  questions of the battery: the 52 not worded with *sequence* were refused
  (``unrecognised query``, or, for *what is the next term / number ...*, a
  refusal that the text names no carrier), and of the six worded *continue
  the sequence* the ``sequence`` kind identified five (stating what follows
  the claim) and refused ``9, 9, 9, 1`` -- the split this baseline counts.

The measured figures (1 November 2026, after the battery above was fixed)
--------------------------------------------------------------------------
*First measurement, first rule* (an answer only when every entry whose stored
terms start with the claim agrees on the next term): positives 27 right,
0 wrong, 18 refused; controls 11 refused (right), 2 answered (wrong) --
``C05`` (``1, 1, 2, 3, 5`` was said to continue with 7, the partition
numbers: the wheel stores the Fibonacci numbers from ``F(0) = 0``, so their
``1, 1, 2, 3, 5`` is held from the second stored term, which the prefix rule
did not see) and ``C08`` (``1, 2, 4, 8, 16`` with 32).

*The rule amended after that measurement*, because ``C05`` was answered: an
entry that holds the claim from its second stored term -- the same claim
under the other indexing convention (offset 0 or 1) -- and continues
differently, or stops at the claim, makes a junction, and the question is
refused; such an entry is never the source of an answer.  This was added
after seeing the first figures, and is reported as such.  *Second
measurement, amended rule*: positives 27 right, 0 wrong, 18 refused (no
positive moved); controls 12 refused (right), 1 answered (wrong) -- ``C08``,
which stays answered: Moser's circle regions (``1, 2, 4, 8, 16, 31``) are not
on the wheel, so the wheel sees no junction there and says 32.  That is a
genuine limit of a junction rule: it sees only the sequences the wheel holds.

*Without the new reading*: positives 5 right, 0 wrong, 40 refused; controls
13 refused (the five right are the questions worded *continue the sequence*
that the identification reading continued; one of them, ``N19``, was a run
inside the triangular numbers, which the ``next`` reading refuses).

``tests/test_sequence_next.py`` pins these figures.

A positive question is *right* when the reader states its expected next term,
*wrong* when it states another, *refused* when it states none.  A negative
control is *right* when refused and *wrong* when any next term is stated.

Exact throughout (directive D7): integers and strings only; deterministic.
"""
from __future__ import annotations

from math import comb
from typing import Callable, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "RULES", "FORMS", "QUESTIONS", "CONTROLS", "JUNCTIONS",
    "battery_questions", "battery_controls", "check_battery",
    "measure_next_terms",
]


# ---------------------------------------------------------------------------
# The rules: the first ``n`` terms of each sequence, from index 0
# ---------------------------------------------------------------------------

def _is_prime(n: int) -> bool:
    """Trial division."""
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


def _is_squarefree(n: int) -> bool:
    d = 2
    while d * d <= n:
        if n % (d * d) == 0:
            return False
        d += 1
    return True


def _scan(pred: Callable[[int], bool], first: int, n: int) -> List[int]:
    out: List[int] = []
    k = first
    while len(out) < n:
        if pred(k):
            out.append(k)
        k += 1
    return out


def _linear(a: int, b: int, step: Callable[[int, int], int], n: int) -> List[int]:
    out = [a, b]
    while len(out) < n:
        out.append(step(out[-2], out[-1]))
    return out[:n]


def _fibonacci(n: int) -> List[int]:
    """F(0) = 0, F(1) = 1, F(k) = F(k-1) + F(k-2)."""
    return _linear(0, 1, lambda x, y: x + y, n)


def _lucas(n: int) -> List[int]:
    """L(0) = 2, L(1) = 1, L(k) = L(k-1) + L(k-2)."""
    return _linear(2, 1, lambda x, y: x + y, n)


def _pell(n: int) -> List[int]:
    """P(0) = 0, P(1) = 1, P(k) = 2 P(k-1) + P(k-2)."""
    return _linear(0, 1, lambda x, y: 2 * y + x, n)


def _tribonacci(n: int) -> List[int]:
    """T(0) = T(1) = 0, T(2) = 1, T(k) = T(k-1) + T(k-2) + T(k-3)."""
    out = [0, 0, 1]
    while len(out) < n:
        out.append(out[-1] + out[-2] + out[-3])
    return out[:n]


def _catalan(n: int) -> List[int]:
    """C(k) = binomial(2k, k) / (k + 1)."""
    return [comb(2 * k, k) // (k + 1) for k in range(n)]


def _bell(n: int) -> List[int]:
    """The Bell numbers, by the Bell triangle (each row starts with the last
    entry of the previous row; each entry adds its left neighbour and the
    entry above that neighbour)."""
    out = [1]
    row = [1]
    while len(out) < n:
        new = [row[-1]]
        for x in row:
            new.append(new[-1] + x)
        row = new
        out.append(row[0])
    return out[:n]


def _motzkin(n: int) -> List[int]:
    """M(0) = M(1) = 1, M(k) = M(k-1) + sum_{i=0}^{k-2} M(i) M(k-2-i)."""
    out = [1, 1]
    while len(out) < n:
        k = len(out)
        out.append(out[k - 1] + sum(out[i] * out[k - 2 - i] for i in range(k - 1)))
    return out[:n]


def _partitions(n: int) -> List[int]:
    """p(k), by Euler's pentagonal-number recurrence."""
    p = [1]
    for k in range(1, n):
        total, j = 0, 1
        while True:
            g1 = j * (3 * j - 1) // 2
            if g1 > k:
                break
            sign = 1 if j % 2 == 1 else -1
            total += sign * p[k - g1]
            g2 = j * (3 * j + 1) // 2
            if g2 <= k:
                total += sign * p[k - g2]
            j += 1
        p.append(total)
    return p[:n]


def _factorials(n: int) -> List[int]:
    out = [1]
    while len(out) < n:
        out.append(out[-1] * len(out))
    return out[:n]


def _lcm_prefix(n: int) -> List[int]:
    """lcm(1, ..., k) for k = 0, 1, ... (the empty lcm is 1)."""
    from math import gcd
    out = [1]
    value = 1
    for k in range(1, n):
        value = value * k // gcd(value, k)
        out.append(value)
    return out[:n]


def _mersenne_exponents(n: int) -> List[int]:
    """Primes p with 2^p - 1 prime (trial division of both)."""
    return _scan(lambda p: _is_prime(p) and _is_prime(2 ** p - 1), 2, n)


#: ``rule -> (description, first-n-terms function)``; index 0 is the first
#: term each description names.
RULES: Dict[str, Tuple[str, Callable[[int], List[int]]]] = {
    "fibonacci": ("the Fibonacci numbers from F(0) = 0", _fibonacci),
    "lucas": ("the Lucas numbers from L(0) = 2", _lucas),
    "catalan": ("the Catalan numbers C(k) = binomial(2k, k) / (k + 1)", _catalan),
    "primes": ("the primes, by trial division", lambda n: _scan(_is_prime, 2, n)),
    "squares": ("k^2 from k = 0", lambda n: [k * k for k in range(n)]),
    "triangular": ("k(k + 1)/2 from k = 0", lambda n: [k * (k + 1) // 2 for k in range(n)]),
    "powers_of_2": ("2^k from k = 0", lambda n: [2 ** k for k in range(n)]),
    "factorials": ("k! from k = 0", _factorials),
    "odd": ("2k + 1 from k = 0", lambda n: [2 * k + 1 for k in range(n)]),
    "powers_of_3": ("3^k from k = 0", lambda n: [3 ** k for k in range(n)]),
    "cubes": ("k^3 from k = 0", lambda n: [k ** 3 for k in range(n)]),
    "bell": ("the Bell numbers, by the Bell triangle", _bell),
    "tetrahedral": ("k(k + 1)(k + 2)/6 from k = 0",
                    lambda n: [k * (k + 1) * (k + 2) // 6 for k in range(n)]),
    "even": ("2k from k = 0", lambda n: [2 * k for k in range(n)]),
    "naturals": ("k from k = 0", lambda n: list(range(n))),
    "pell": ("the Pell numbers from P(0) = 0", _pell),
    "tribonacci": ("the tribonacci numbers from T(0) = T(1) = 0, T(2) = 1", _tribonacci),
    "motzkin": ("the Motzkin numbers from M(0) = 1", _motzkin),
    "powers_of_10": ("10^k from k = 0", lambda n: [10 ** k for k in range(n)]),
    "mersenne_numbers": ("2^k - 1 from k = 0", lambda n: [2 ** k - 1 for k in range(n)]),
    "oblong": ("k(k + 1) from k = 0", lambda n: [k * (k + 1) for k in range(n)]),
    "composites": ("the composite numbers, by trial division",
                   lambda n: _scan(lambda k: k > 3 and not _is_prime(k), 4, n)),
    "square_pyramidal": ("k(k + 1)(2k + 1)/6 from k = 0",
                         lambda n: [k * (k + 1) * (2 * k + 1) // 6 for k in range(n)]),
    "lazy_caterer": ("k(k + 1)/2 + 1 from k = 0",
                     lambda n: [k * (k + 1) // 2 + 1 for k in range(n)]),
    "hexagonal": ("k(2k - 1) from k = 0", lambda n: [k * (2 * k - 1) for k in range(n)]),
    "pentagonal": ("k(3k - 1)/2 from k = 0", lambda n: [k * (3 * k - 1) // 2 for k in range(n)]),
    # Rules used only by the junction controls.
    "partitions": ("the partition numbers p(k), by Euler's recurrence", _partitions),
    "lcm": ("lcm(1, ..., k) from k = 0", _lcm_prefix),
    "circle_regions": ("Moser's circle regions binomial(k, 4) + binomial(k, 2) + 1 from k = 1",
                       lambda n: [comb(k, 4) + comb(k, 2) + 1 for k in range(1, n + 1)]),
    "squarefree": ("the squarefree numbers, by trial division",
                   lambda n: _scan(_is_squarefree, 1, n)),
    "mersenne_exponents": ("primes p with 2^p - 1 prime, by trial division",
                           _mersenne_exponents),
}


# ---------------------------------------------------------------------------
# The questions (written before the measurement; see the module docstring)
# ---------------------------------------------------------------------------

#: The six wordings of a next-term question.
FORMS: Dict[str, str] = {
    "in": "what comes next in {terms}",
    "after": "what comes next after {terms}",
    "term": "what is the next term of {terms}",
    "number": "what is the next number in {terms}",
    "bare": "next term of {terms}",
    "continue": "continue the sequence {terms}",
}

#: ``(qid, form, rule, start, count, question mark)``: the question shows
#: terms ``start .. start + count - 1`` of the rule; the expected next term is
#: term ``start + count``.
QUESTIONS: Tuple[Tuple[str, str, str, int, int, bool], ...] = (
    ("N01", "in", "fibonacci", 0, 7, False),
    ("N02", "in", "fibonacci", 1, 6, True),
    ("N03", "term", "fibonacci", 2, 6, False),
    ("N04", "continue", "fibonacci", 0, 10, False),
    ("N05", "in", "lucas", 0, 6, False),
    ("N06", "term", "lucas", 1, 6, True),
    ("N07", "bare", "lucas", 0, 5, False),
    ("N08", "in", "catalan", 0, 6, True),
    ("N09", "number", "catalan", 1, 6, False),
    ("N10", "continue", "catalan", 0, 8, False),
    ("N11", "in", "primes", 0, 6, False),
    ("N12", "bare", "primes", 0, 8, False),
    ("N13", "number", "primes", 1, 5, True),
    ("N14", "in", "squares", 0, 5, False),
    ("N15", "in", "squares", 1, 5, True),
    ("N16", "bare", "squares", 2, 5, False),
    ("N17", "in", "triangular", 0, 6, False),
    ("N18", "term", "triangular", 1, 5, False),
    ("N19", "continue", "triangular", 1, 7, False),
    ("N20", "in", "powers_of_2", 0, 6, False),
    ("N21", "after", "powers_of_2", 1, 5, True),
    ("N22", "bare", "powers_of_2", 0, 8, False),
    ("N23", "in", "factorials", 0, 6, False),
    ("N24", "number", "factorials", 1, 5, False),
    ("N25", "continue", "factorials", 0, 5, True),
    ("N26", "in", "odd", 0, 6, False),
    ("N27", "in", "powers_of_3", 0, 5, False),
    ("N28", "bare", "powers_of_3", 1, 4, False),
    ("N29", "in", "cubes", 0, 5, False),
    ("N30", "after", "cubes", 1, 5, False),
    ("N31", "in", "bell", 0, 6, True),
    ("N32", "term", "tetrahedral", 1, 5, False),
    ("N33", "in", "even", 1, 5, False),
    ("N34", "number", "naturals", 1, 6, False),
    ("N35", "in", "pell", 0, 6, False),
    ("N36", "in", "tribonacci", 0, 8, False),
    ("N37", "term", "motzkin", 0, 6, False),
    ("N38", "in", "powers_of_10", 0, 4, True),
    ("N39", "in", "mersenne_numbers", 1, 5, False),
    ("N40", "continue", "oblong", 0, 5, False),
    ("N41", "in", "composites", 0, 6, False),
    ("N42", "after", "square_pyramidal", 1, 5, False),
    ("N43", "in", "lazy_caterer", 0, 6, False),
    ("N44", "number", "hexagonal", 1, 5, False),
    ("N45", "in", "pentagonal", 1, 5, True),
)

#: ``(qid, question, reason)``: negative controls, whose correct outcome is
#: a refusal.
CONTROLS: Tuple[Tuple[str, str, str], ...] = (
    ("C01", "what comes next in 7, 3, 9, 2, 8", "arbitrary digits"),
    ("C02", "what comes next in 4, 8, 15, 16, 23", "an arbitrary list"),
    ("C03", "what is the next number in 5, 17, 2, 31, 9", "an arbitrary list"),
    ("C04", "what comes next in 10, 20, 30, 50", "an arbitrary list"),
    ("C05", "what comes next in 1, 1, 2, 3, 5", "a junction: Fibonacci vs partitions"),
    ("C06", "what comes next in 1, 1, 2, 5", "a junction: Catalan vs Bell"),
    ("C07", "what comes next in 1, 1, 2, 6", "a junction: factorials vs lcm(1..k)"),
    ("C08", "what comes next in 1, 2, 4, 8, 16", "a junction: powers of 2 vs circle regions"),
    ("C09", "what comes next in 1, 2, 3", "a junction: the naturals vs the squarefree numbers"),
    ("C10", "what comes next in 2, 3, 5, 7", "a junction: primes vs Mersenne exponents"),
    ("C11", "what comes next in 1, 2", "two terms"),
    ("C12", "next term of 2, 4", "two terms"),
    ("C13", "continue the sequence 9, 9, 9, 1", "an arbitrary list"),
)

#: ``control qid -> ((rule, start), (rule, start))``: the two standard rules
#: a junction control's prefix belongs to, from the given index.
JUNCTIONS: Dict[str, Tuple[Tuple[str, int], Tuple[str, int]]] = {
    "C05": (("fibonacci", 1), ("partitions", 0)),
    "C06": (("catalan", 0), ("bell", 0)),
    "C07": (("factorials", 0), ("lcm", 0)),
    "C08": (("powers_of_2", 0), ("circle_regions", 0)),
    "C09": (("naturals", 1), ("squarefree", 0)),
    "C10": (("primes", 0), ("mersenne_exponents", 0)),
}


def _terms(rule: str, start: int, count: int) -> List[int]:
    return RULES[rule][1](start + count)[start:start + count]


def battery_questions() -> List[Dict[str, object]]:
    """Every positive question: ``{"qid", "question", "rule", "claim",
    "expected"}``, the text and the expected next term both computed from
    the rule."""
    out = []
    for qid, form, rule, start, count, mark in QUESTIONS:
        seq = RULES[rule][1](start + count + 1)
        claim = tuple(seq[start:start + count])
        text = FORMS[form].format(terms=", ".join(str(t) for t in claim))
        out.append({"qid": qid, "question": text + ("?" if mark else ""), "rule": rule,
                    "claim": claim, "expected": seq[start + count]})
    return out


def battery_controls() -> List[Dict[str, object]]:
    """Every negative control: ``{"qid", "question", "reason"}``."""
    return [{"qid": qid, "question": text, "reason": reason}
            for qid, text, reason in CONTROLS]


def check_battery() -> Dict[str, object]:
    """The battery's own consistency, independent of any wheel: at least ten
    sequences; the question texts show the rules' terms; every junction
    control's prefix is shared by its two rules, which then disagree."""
    from .sequence_query import sequence_terms
    questions = battery_questions()
    bad_text = [q["qid"] for q in questions
                if tuple(sequence_terms(str(q["question"]))) != q["claim"]]
    junctions: Dict[str, Tuple[int, int]] = {}
    bad_junctions: List[str] = []
    for qid, text, _ in CONTROLS:
        if qid not in JUNCTIONS:
            continue
        prefix = list(sequence_terms(text))
        (r1, s1), (r2, s2) = JUNCTIONS[qid]
        a = _terms(r1, s1, len(prefix) + 1)
        b = _terms(r2, s2, len(prefix) + 1)
        if a[:-1] != prefix or b[:-1] != prefix or a[-1] == b[-1]:
            bad_junctions.append(qid)
        junctions[qid] = (a[-1], b[-1])
    return {"questions": len(questions), "controls": len(CONTROLS),
            "sequences": len({q["rule"] for q in questions}),
            "bad_text": bad_text, "bad_junctions": bad_junctions,
            "junction_next_terms": junctions}


# ---------------------------------------------------------------------------
# The measurement
# ---------------------------------------------------------------------------

def _stated_next(result, wheel) -> Optional[int]:
    """The next term a reading states: the ``next`` reading's term, or for an
    identification the stored term right after the claim (the term its reply
    says comes *then*); ``None`` when it states none."""
    from . import sequence_query as sq
    if result.code != sq.ANSWERED:
        return None
    if result.kind == "next":
        return result.next_term
    if result.kind == "sequence" and result.ids and result.position is not None:
        terms = wheel.get(result.ids[0]).terms
        k = result.position + len(result.claim)
        return terms[k] if k < len(terms) else None
    return None


def _score(stated: Sequence[Optional[int]], expected: Sequence[Optional[int]]
           ) -> Dict[str, int]:
    out = {"right": 0, "wrong": 0, "refused": 0}
    for got, want in zip(stated, expected):
        if got is None:
            out["refused"] += 1
        elif got == want:
            out["right"] += 1
        else:
            out["wrong"] += 1
    return out


def measure_next_terms(wheel=None, rows: bool = False) -> Dict[str, object]:
    """Exact counts for the battery, with the wheels (the ``next`` reading as
    it is, and as first written: ``with_wheels_first_rule``) and without the
    new reading (the ``sequence`` kind before Phase 186).

    Returns ``{"questions", "controls", "with_wheels": {"positive": {...},
    "controls": {...}}, "with_wheels_first_rule": {...}, "without_next":
    {...}}`` where each ``positive`` holds
    ``right`` / ``wrong`` / ``refused`` and each ``controls`` holds ``right``
    (refused, as it should be) / ``wrong`` (a next term stated); with
    ``rows=True`` also every question's outcome under ``"rows"``.
    """
    from . import sequence_query as sq
    w = wheel if wheel is not None else sq._default_wheel()
    questions = battery_questions()
    controls = battery_controls()
    out: Dict[str, object] = {"questions": len(questions), "controls": len(controls)}
    table: List[Dict[str, object]] = []
    readers = (("with_wheels", True, True), ("with_wheels_first_rule", True, False),
               ("without_next", False, False))
    for label, flag, offset in readers:
        stated_q = [_stated_next(sq.resolve_query(str(q["question"]), wheel=w,
                                                  next_terms=flag,
                                                  offset_junctions=offset), w)
                    for q in questions]
        stated_c = [_stated_next(sq.resolve_query(str(c["question"]), wheel=w,
                                                  next_terms=flag,
                                                  offset_junctions=offset), w)
                    for c in controls]
        positive = _score(stated_q, [q["expected"] for q in questions])
        answered_controls = sum(1 for s in stated_c if s is not None)
        out[label] = {"positive": positive,
                      "controls": {"right": len(controls) - answered_controls,
                                   "wrong": answered_controls}}
        if rows:
            for q, s in zip(questions, stated_q):
                table.append({"reader": label, "qid": q["qid"], "expected": q["expected"],
                              "stated": s})
            for c, s in zip(controls, stated_c):
                table.append({"reader": label, "qid": c["qid"], "expected": None,
                              "stated": s})
    if rows:
        out["rows"] = tuple(table)
    return out
