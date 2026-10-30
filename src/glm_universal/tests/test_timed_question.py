"""Tests for time and the question: a tie held open until information that
arrives later -- waited for, or asked for -- resolves it (Phase 145).

``studies/TIMED_QUESTION_STUDY.md`` pre-registered nine marks.  These tests
pin:

* the **Lean file** (L1): it states the theorems the open tie relies on and
  has no ``sorry``;
* the **open tie**: information only removes, its order does not matter, the
  ledger partitions the candidates, an empty tie is ``contradicted``;
* **asking**: the minimax question, ``splits_iff``, the direct choice when no
  question splits, the confirming question;
* the **Golay fork**: waiting resolves to the transmitted word, set questions
  resolve in at most ``clog2 6 = 3`` questions;
* the **junctions**: coordinate observations never resolve, the vocabulary
  does;
* the **dialogues** and the full report's marks.
"""

from __future__ import annotations

import re
from pathlib import Path

from glm_universal.reasoning import timed_question as tq

LEAN = (Path(__file__).resolve().parents[2] / "lean" / tq.LEAN_FILE)


def test_lean_file_states_the_theorems_without_sorry():
    text = LEAN.read_text(encoding="utf-8")
    assert not re.search(r"\bsorry\b", text)
    for name in tq.LEAN_THEOREMS:
        assert re.search(rf"theorem {re.escape(name)}\b", text), name


def test_clog2():
    assert [tq.clog2(n) for n in (1, 2, 3, 4, 5, 6, 8, 9, 78)] == \
        [0, 1, 2, 2, 3, 3, 3, 4, 7]


def _parity_tie():
    tie = tq.OpenTie(tuple(range(8)))
    even = tq.Question("even", "Is it even?", lambda c: c % 2 == 0)
    small = tq.Question("small", "Is it below 4?", lambda c: c < 4)
    return tie, even, small


def test_information_only_removes_and_order_does_not_matter():
    a, even, small = _parity_tie()
    a.apply("waited", even, True, "a later step")
    a.apply("asked", small, False, "developer")
    b, even, small = _parity_tie()
    b.apply("asked", small, False, "developer")
    b.apply("waited", even, True, "a later step")
    assert a.live == b.live == (4, 6)
    assert a.partition_holds() and b.partition_holds()
    assert a.status == "open"


def test_contradiction_is_reported_not_resolved():
    tie, even, _small = _parity_tie()
    tie.apply("asked", even, True, "developer")
    tie.apply("asked", even, False, "developer")
    assert tie.status == "contradicted" and tie.value is None
    assert tie.partition_holds()


def test_minimax_question_and_splits():
    tie = tq.OpenTie(tuple(range(6)))
    useless = tq.Question("u", "Is it a number?", lambda c: True)
    lopsided = tq.Question("l", "Is it 0?", lambda c: c == 0)
    halving = tq.Question("h", "Is it below 3?", lambda c: c < 3)
    assert not tie.splits(useless)
    assert tie.best_question([useless, lopsided, halving]) is halving
    assert tie.best_question([useless]) is None


def test_direct_choice_when_nothing_splits():
    tie = tq.OpenTie(("x", "y"))
    useless = tq.Question("u", "Is it a letter?", lambda c: True)
    tq.resolve(tie, lambda t: (useless,), tq.DeclaredInformant("y"))
    assert tie.status == "resolved" and tie.value == "y"
    assert tie.ledger[0].question.startswith("Which of these do you mean")


def test_confirmation_turns_a_false_answer_into_a_contradiction():
    tie = tq.OpenTie(tuple(range(4)))
    vocab = lambda t: (tq.Question("h", "Is it below 2?", lambda c: c < 2),
                       tq.Question("o", "Is it odd?", lambda c: c % 2 == 1))
    tq.resolve(tie, vocab, tq.LyingInformant(3, lie_at=1), confirm=True)
    assert tie.status == "contradicted"
    assert tie.counts()["confirmed"] == 1


def test_golay_fork_waiting_and_asking():
    forks = tq.probe_forks()[:24]
    assert len(tq.probe_forks()) == 768
    g1 = tq.g1_waiting(forks)
    assert g1["resolved"] == 24 and g1["wrong"] == 0
    assert g1["reports"]["max"] <= 17
    g3 = tq.g3_set_questions(forks)
    assert g3["resolved"] == 24 and g3["wrong"] == 0
    assert g3["questions"]["max"] <= 3
    g2 = tq.g2_coordinate_questions(forks)
    assert g2["resolved"] == 24 and g2["questions"]["max"] <= 5


def test_junction_coordinates_never_resolve_and_the_vocabulary_does():
    junctions = tq.register_junctions()
    assert len(junctions) == 104
    small = [m for m in junctions if len(m) <= 3][:6]
    assert tq.r1_coordinates(small)["unchanged"] == len(small)
    rr = tq.r2_r3_asking(small)
    assert rr["resolved"] == rr["runs"] and rr["wrong"] == 0


def test_dialogues():
    d1 = tq.d1_dialogues()
    assert d1["as_declared"] == d1["declared"] == 6, d1["missed"]


def test_interactive_informant_reads_an_option():
    replies = iter(["2"])
    shown = []
    inf = tq.InteractiveInformant(read=lambda _p: next(replies),
                                  write=shown.append)
    q = tq.Question("o", "Is it odd?", lambda c: c % 2 == 1)
    assert inf.answer(q, (True, False)) is False
    assert shown[0] == "GLM asks: Is it odd?"


def test_report_marks():
    report = tq.timed_question_report()
    assert report["met"] == report["taken"] == 8, report["marks"]
