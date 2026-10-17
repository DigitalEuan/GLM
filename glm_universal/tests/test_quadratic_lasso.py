"""Phase 142: quadratic lassos -- accumulators and the first change of a
quadratic comparison (``studies/QUADRATIC_LASSO_STUDY.md``)."""

from __future__ import annotations

from pathlib import Path

from glm_universal.reasoning import batch_machine as bm
from glm_universal.reasoning import batch_speech as bs
from glm_universal.reasoning import quadratic_lasso as ql

ROOT = Path(__file__).resolve().parents[3]


def _p(text: str):
    return bm.parse_program(text.split(" / "))


def test_the_lean_file_states_the_theorems():
    text = (ROOT / "overlay" / "glm_lean" / ql.LEAN_FILE).read_text()
    assert "sorry" not in text
    for name in ql.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name


def test_accumulators():
    program = _p("SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / "
                 "SET /A B=B+A / SET /A C=C+B / GOTO UP")
    assert bm.counters(program) == ("A",)
    # C is fed by an accumulator, so it is not one (cubic growth).
    assert bm.accumulators(program) == ("B",)
    assert bm.accumulators(_p("SET /A N=N+1 / SET /A M=M-%N%")) == ("M",)
    assert bm.accumulators(_p("SET /A N=N+1 / SET /A N=N+N")) == ()


def test_first_change_quadratic_small():
    # e(t) = -10 + t + C(t, 2): -10, -9, -7, -4, 0, 5
    assert bm.first_change_quadratic(-10, 1, 1, "LSS") == 4
    assert bm.first_change_quadratic(-10, 1, 1, "NEQ") == 4
    assert bm.first_change_quadratic(-10, 1, 1, "LEQ") == 5
    # 45 -> 55 skips 50: the sign changes, EQU never holds.
    assert bm.first_change_quadratic(1 - 50, 2, 1, "EQU") is None
    # a convex comparison that dips below zero and comes back
    assert bm.first_change_quadratic(5, -4, 1, "GTR") == 2
    assert bm.first_change_quadratic(3, 0, 0, "GTR") is None


def test_the_battery():
    marks = ql.battery_marks()
    assert marks["Q2"], [r for r in marks["rows"] if not r["as_declared"]]


def test_the_questions():
    marks = ql.question_marks()
    assert marks["wrong"] == 0 and marks["questions"] == 21
    # declared as twenty: the mark is missed on its declaration
    assert marks["Q3"] is False


def test_an_answer_states_the_growth():
    a = bs.answer("does it halt?", ql._program_text("Q1"))
    assert a.answered and a.verified and a.value is False
    assert "adding 1 more to B on each later pass" in a.text
    assert a.claim["g"] == {"B": 1}
    b = bs.answer("does it halt?", ql._program_text("Q1"), quadratic=False)
    assert b.refusal == "UNDECIDED_WITHIN_BUDGET"


def test_the_first_change_exhaustively():
    marks = ql.first_change_marks(e_range=12, b_range=4, c_range=3,
                                  horizon=120)
    assert marks["Q7"], marks["examples"]


def test_certificates():
    marks = ql.certificate_marks()
    assert marks["Q4"], (marks["failed"], marks["accepted"])
    assert marks["scripts"] == 18


def test_noninterference():
    marks = ql.noninterference_marks()
    assert marks["Q5"], marks["moved"]
    assert marks["generated_kept"] == 300


def test_the_soundness_control():
    marks = ql.soundness_marks()
    assert marks["Q6"], marks
