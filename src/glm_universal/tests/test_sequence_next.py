"""Tests for the ``next`` reading of the sequence kind -- *what comes next in
1, 1, 2, 5, 14, 42* (:func:`glm_universal.wheels.sequence_query.resolve_query`,
the solver ``_solve_sequence`` and its column 3) -- and for the next-term
battery (:mod:`glm_universal.wheels.next_term_battery`).

*Created 1 November 2026 (Phase 186: intake absorption).  Altered the same
day: the two evaluation cases that put the ``next`` reading to the command
line (``sequence-next-catalan``, ``sequence-next-junction``) are the only
cases it may claim.*

What is pinned:

* **Answers are right.**  The expected next term of every positive case is
  computed here, by a closed form or a recurrence (Fibonacci, Lucas, Pell,
  tribonacci, Catalan, primes by trial division, squares, cubes, triangular
  numbers, powers, factorials), never read from the wheel's data.
* **The soundness rule.**  A next term is said only when every entry that
  starts with the claim and runs past it agrees, and every entry holding the
  claim from its second stored term agrees too; otherwise the question is
  refused as a junction naming the competing ids and their next terms, or as
  not on the wheel.  ``locate`` is never the source of a next term.
* **Nothing else moves.**  The existing readings answer as before, and no
  question of the evaluation set is newly claimed by the sequence kind
  except the two cases written for the ``next`` reading.
* **Column 3 verifies** an answer, and the battery's figures are pinned.

Plain test functions (runnable by ``glm_universal.intake.fallback_tests``).
"""
from __future__ import annotations

from math import comb

from glm_universal.wheels import provisional_status
from glm_universal.wheels import sequence_query as sq
from glm_universal.wheels import next_term_battery as nb

_SESSION = None


def _session():
    global _SESSION
    if _SESSION is None:
        from glm_universal.runtime.session import GeometricSession
        _SESSION = GeometricSession()
    return _SESSION


def _verified(solution) -> bool:
    from glm_universal.runtime import tct_engine as T
    trace = T.verify_trace(T.build_trace(solution))
    verdict = trace.verdict
    return (verdict is not None and verdict.returncode == 0
            and verdict.matches_column2 and not verdict.missing_keys)


def _text(terms) -> str:
    return ", ".join(str(t) for t in terms)


# ---------------------------------------------------------------------------
# Independent rules (no wheel data)
# ---------------------------------------------------------------------------

def _recurrence(seed, step, n):
    out = list(seed)
    while len(out) < n:
        out.append(step(out))
    return out[:n]


def _fib(n):
    return _recurrence([0, 1], lambda s: s[-1] + s[-2], n)


def _lucas(n):
    return _recurrence([2, 1], lambda s: s[-1] + s[-2], n)


def _pell(n):
    return _recurrence([0, 1], lambda s: 2 * s[-1] + s[-2], n)


def _tribonacci(n):
    return _recurrence([0, 0, 1], lambda s: s[-1] + s[-2] + s[-3], n)


def _catalan(n):
    return [comb(2 * k, k) // (k + 1) for k in range(n)]


def _primes(n):
    out, k = [], 2
    while len(out) < n:
        if all(k % d for d in range(2, k) if d * d <= k):
            out.append(k)
        k += 1
    return out


def _factorials(n):
    out = [1]
    for k in range(1, n):
        out.append(out[-1] * k)
    return out


def _bell(n):
    out, row = [1], [1]
    while len(out) < n:
        new = [row[-1]]
        for x in row:
            new.append(new[-1] + x)
        row = new
        out.append(row[0])
    return out


#: ``(rule, terms)``: the question shows all but the last; the last is the
#: expected next term.
_POSITIVE = (
    ("fibonacci", _fib(8)),
    ("lucas", _lucas(7)),
    ("pell", _pell(7)),
    ("tribonacci", _tribonacci(9)),
    ("catalan", _catalan(7)),
    ("catalan, longer", _catalan(10)),
    ("primes", _primes(7)),
    ("primes, longer", _primes(12)),
    ("factorials", _factorials(7)),
    ("squares from 0", [k * k for k in range(6)]),
    ("cubes from 0", [k ** 3 for k in range(6)]),
    ("triangular from 0", [k * (k + 1) // 2 for k in range(7)]),
    ("powers of 2", [2 ** k for k in range(7)]),
    ("powers of 3", [3 ** k for k in range(6)]),
    ("odd numbers", [2 * k + 1 for k in range(7)]),
    ("bell", _bell(7)),
)


# ---------------------------------------------------------------------------
# Answers
# ---------------------------------------------------------------------------

def test_positive_cases_from_closed_forms():
    for rule, terms in _POSITIVE:
        claim, want = terms[:-1], terms[-1]
        r = sq.resolve_query(f"what comes next in {_text(claim)}")
        assert r.code == sq.ANSWERED, (rule, r.reply)
        assert r.kind == "next", rule
        assert r.next_term == want, (rule, r.next_term, want)
        assert r.claim == tuple(claim), rule
        assert list(r.ids) == sorted(r.ids) and r.ids, rule
        assert str(want) in r.reply and r.ids[0] in r.reply, rule


def test_every_wording_reads_the_same_claim():
    claim, want = _catalan(6), _catalan(7)[-1]
    forms = ("what comes next in {t}", "what comes next after {t}",
             "what is the next term of {t}", "what is the next number in {t}",
             "next term of {t}", "continue the sequence {t}",
             "What Comes Next In {t}?", "what is the next term of the sequence {t} ?",
             "  next   term of  {t}.")
    for form in forms:
        text = form.format(t=_text(claim))
        assert sq.next_claim(text) == tuple(claim), text
        r = sq.resolve_query(text)
        assert (r.code, r.kind, r.next_term) == (sq.ANSWERED, "next", want), text


def test_agreeing_entries_are_all_named_least_first():
    r = sq.resolve_query("what is the next number in 1, 2, 3, 4, 5, 6")
    assert r.code == sq.ANSWERED and r.next_term == 7
    assert len(r.ids) >= 2 and list(r.ids) == sorted(r.ids)
    for oid in r.ids:
        assert oid in r.reply


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------

def test_a_junction_names_the_competing_ids_and_terms():
    # Catalan and Bell share 1, 1, 2, 5 and then give 14 and 15.
    claim = _catalan(4)
    assert _bell(4) == claim
    r = sq.resolve_query(f"what comes next in {_text(claim)}")
    assert r.code == sq.UNANSWERED and r.kind == "next" and r.next_term is None
    values = {v for _, _, v in r.competing}
    assert {_catalan(5)[-1], _bell(5)[-1]} <= values
    assert len(values) >= 2
    assert "junction" in r.reply.lower()
    for oid, _, v in r.competing:
        assert oid in r.reply and str(v) in r.reply
    # Factorials and lcm(1..k) share 1, 1, 2, 6 and then give 24 and 12.
    r = sq.resolve_query("what comes next in 1, 1, 2, 6")
    assert r.code == sq.UNANSWERED and {24, 12} <= {v for _, _, v in r.competing}


def test_a_junction_through_the_other_indexing_convention():
    # 1, 1, 2, 3, 5: the partition numbers give 7; the Fibonacci numbers,
    # stored from F(0) = 0, hold the claim from their second term and give 8.
    fib = _fib(7)
    assert fib[1:6] == [1, 1, 2, 3, 5] and fib[6] == 8
    r = sq.resolve_query("what comes next in 1, 1, 2, 3, 5")
    assert r.code == sq.UNANSWERED and r.next_term is None
    assert ("A000045", 1, 8) in r.competing
    assert any(pos == 0 and v == 7 for _, pos, v in r.competing)
    # The first rule (prefix entries only) did not see it.
    first = sq.resolve_query("what comes next in 1, 1, 2, 3, 5", offset_junctions=False)
    assert first.code == sq.ANSWERED and first.next_term == 7


def test_an_entry_that_stops_at_the_claim_is_a_junction():
    fermat = [2 ** (2 ** k) + 1 for k in range(5)]
    r = sq.resolve_query(f"what comes next in {_text(fermat)}")
    assert r.code == sq.UNANSWERED
    assert any(v is None for _, _, v in r.competing)
    assert 2 ** 32 + 1 in {v for _, _, v in r.competing}


def test_what_no_entry_starts_with_is_refused():
    for text in ("what comes next in 7, 3, 9, 2, 8", "next term of 5, 17, 2, 31, 9",
                 "continue the sequence 9, 9, 9, 1"):
        r = sq.resolve_query(text)
        assert r.code == sq.UNANSWERED and r.kind == "next", text
        assert not r.competing and r.next_term is None, text
        assert "Nothing is guessed" in r.reply, text


def test_locate_is_never_the_source_of_a_next_term():
    w = sq._default_wheel()
    for claim in ([1, 1, 2, 3, 5, 8], [k * k for k in range(1, 6)],
                  [2 ** k for k in range(1, 6)], [3, 5, 7, 11, 13]):
        assert w.locate(tuple(claim)) is not None, claim     # a run exists
        r = sq.resolve_query(f"what comes next in {_text(claim)}")
        assert r.code == sq.UNANSWERED and r.next_term is None, (claim, r.reply)


def test_fewer_than_three_terms_are_refused():
    for text in ("what comes next in 1, 2", "next term of 2, 4", "what comes next in 5"):
        r = sq.resolve_query(text)
        assert r.code == sq.UNANSWERED and r.kind == "next", text
        assert "at least 3" in r.reply, text


def test_texts_outside_the_wordings_are_not_next_questions():
    for text in ("continue 1, 2, 3", "what comes next in the corpus",
                 "what comes next in 1, 2, x", "tell me what comes next in 1, 2, 3, 4",
                 "what comes next in 1.5, 2, 3"):
        assert sq.next_claim(text) is None, text


# ---------------------------------------------------------------------------
# Nothing else moves
# ---------------------------------------------------------------------------

def test_existing_readings_answer_as_before():
    texts = ("what sequence is 1, 1, 2, 3, 5, 8", "identify the sequence 2 3 5 7 11",
             "what sequence is 9, 17, 4, 1000, 3", "what sequence is 1, 2",
             "which sporadic group has order 7920",
             "which sporadic group has order 2^4 * 3^2 * 5 * 11",
             "what is the order of the Monster group", "what is the order of operations")
    for text in texts:
        assert sq.resolve_query(text) == sq.resolve_query(text, next_terms=False), text


#: The two evaluation cases added at Phase 186 to put the ``next`` reading
#: itself to the command line (one answered, one refused as too short).  They
#: are the only cases the reading may claim; every other case is untouched.
NEXT_READING_CASES = ("sequence-next-catalan", "sequence-next-junction")


def test_no_evaluation_question_is_newly_claimed():
    from glm_universal.evaluation.cases import CASES
    from glm_universal.runtime import lookup_kinds as lk
    ids = {case.id for case in CASES}
    assert set(NEXT_READING_CASES) <= ids
    for case in CASES:
        q = case.question
        if case.id in NEXT_READING_CASES:
            assert sq.next_claim(q) is not None, case.id
            assert case.kind == "sequence" and lk.reads_sequence(q), case.id
            continue
        assert sq.next_claim(q) is None, case.id
        assert (sq.resolve_query(q, wheel=lk.sequence_wheel())
                == sq.resolve_query(q, wheel=lk.sequence_wheel(), next_terms=False)), case.id
        assert lk.reads_sequence(q) == (case.kind == "sequence"), case.id


# ---------------------------------------------------------------------------
# The solver and column 3
# ---------------------------------------------------------------------------

def test_the_solver_answers_and_column_three_verifies():
    claim, want = _catalan(6), _catalan(7)[-1]
    sol = _session().ask(f"what comes next in {_text(claim)}")
    assert sol.ok, sol.answer
    assert sol.kind == "sequence"
    assert sol.answer.startswith(f"{want} ")
    assert sol.expected == {"ids": "A000108", "next": str(want), "claim": _text(claim)}
    assert sol.payload["reading"] == "next" and sol.payload["next_term"] == want
    note = provisional_status("wheels/sequence_query")
    if note:
        assert sol.answer.endswith(f"[{note}]")
    assert _verified(sol)


def test_column_three_verifies_agreeing_entries():
    sol = _session().ask("what is the next number in 1, 2, 3, 4, 5, 6?")
    assert sol.ok and sol.payload["next_term"] == 7
    assert _verified(sol)


def test_the_solver_refuses_a_junction_and_what_is_not_on_the_wheel():
    sol = _session().ask("what comes next in 1, 1, 2, 5")
    assert not sol.ok and "JUNCTION" in sol.answer
    sol = _session().ask("what comes next in 7, 3, 9, 2, 8")
    assert not sol.ok and "NOT_ON_THE_WHEEL" in sol.answer


# ---------------------------------------------------------------------------
# The battery
# ---------------------------------------------------------------------------

def test_the_battery_is_consistent():
    c = nb.check_battery()
    assert c["sequences"] >= 10 and c["questions"] >= 40 and c["controls"] >= 10
    assert c["bad_text"] == [] and c["bad_junctions"] == []


def test_the_battery_figures():
    m = nb.measure_next_terms()
    assert m["questions"] == 45 and m["controls"] == 13
    assert m["with_wheels"] == {"positive": {"right": 27, "wrong": 0, "refused": 18},
                                "controls": {"right": 12, "wrong": 1}}
    assert m["with_wheels_first_rule"] == {
        "positive": {"right": 27, "wrong": 0, "refused": 18},
        "controls": {"right": 11, "wrong": 2}}
    assert m["without_next"] == {"positive": {"right": 5, "wrong": 0, "refused": 40},
                                 "controls": {"right": 13, "wrong": 0}}
    rows = nb.measure_next_terms(rows=True)["rows"]
    answered = sorted((r["reader"], r["qid"]) for r in rows
                      if r["qid"].startswith("C") and r["stated"] is not None)
    assert answered == [("with_wheels", "C08"), ("with_wheels_first_rule", "C05"),
                        ("with_wheels_first_rule", "C08")]
