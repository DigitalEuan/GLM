"""Tests for inert variables in GLM-BAT (Phase 126).

``studies/INERT_COUNTER_STUDY.md`` pre-registered seven marks.  These tests
pin:

* the **Lean file** (I1): it exists, states the three theorems the mark
  names, and has no ``sorry``;
* the **rule**: the largest closed set of inert variables, and the order of
  use (a program the Phase 125 run decides is not re-read);
* the **battery** (I2) and the **questions** (I3), as declared;
* the **certificates** (I4): a ``never_inert`` claim verifies under
  ``python3 -I`` and every mutation fails;
* **non-interference** on Phase 125 (I5) and the **soundness control** (I6).
"""

from __future__ import annotations

import re
from pathlib import Path

from glm_universal.reasoning import batch_machine as bm
from glm_universal.reasoning import batch_speech as bs
from glm_universal.reasoning import inert_counter as ic
from glm_universal.reasoning import operations as op

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "overlay" / "glm_lean" / ic.LEAN_FILE


def _p(text: str):
    return bm.parse_program(text.split(" / "))


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in ic.LEAN_THEOREMS:
        assert re.search(rf"^theorem {name}\b", text, re.MULTILINE), name
    assert "sorry" not in text
    assert "axiom " not in text


def test_the_largest_closed_set():
    assert bm.inert_variables(_p("SET /A N=0 / :UP / SET /A N=N+1 / GOTO UP")) \
        == ("N",)
    assert bm.inert_variables(_p(
        "SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / SET /A B=B+A / "
        "IF %B% GTR -1 GOTO UP")) == ()
    assert bm.inert_variables(_p(
        "SET /A N=1 / :UP / SET /A N=N*2 / SET /A Q=10/N / GOTO UP")) == ()
    prog = _p("SET /A N=0 / SET /A M=0 / :UP / SET /A N=N+1 / "
              "SET /A M=M+N / GOTO UP")
    assert bm.is_closed_inert(prog, ("M", "N"))
    assert bm.is_closed_inert(prog, ("M",))
    assert not bm.is_closed_inert(prog, ("N",))
    assert not bm.is_closed_inert(prog, ("ERRORLEVEL",))


def test_a_redirected_assignment_is_not_inert():
    assert bm.inert_variables(_p("SET /A N=0 / :UP / SET S=%N%> f.txt / "
                                 "SET /A N=N+1 / GOTO UP")) == ()


def test_the_order_of_use():
    run = bm.run_program(bm.parse_program(op.M13))
    assert run.status == "never" and run.certificate == (2, 4)
    assert run.forgotten == ()
    assert bm.inert_variables(bm.parse_program(op.M13)) == ("X",)
    old = bm.run_program(bm.parse_program(op.M15), inert=False)
    assert old.status == "undecided"


def test_the_battery():
    marks = ic.battery_marks()
    assert marks["I2"], [r for r in marks["rows"] if not r["as_declared"]]


def test_the_questions():
    marks = ic.question_marks()
    assert marks["I3"], [r for r in marks["rows"] if not r["as_declared"]]


def test_a_never_inert_claim_verifies_and_its_mutations_fail():
    lines = [bm.render_line(i) for i in bm.parse_program(op.M15)]
    a = bs.answer("does it halt?", "\n".join(op.M15))
    assert a.answered and a.verified and a.value is False
    assert a.claim == {"kind": "never_inert", "certificate": [2, 4],
                       "forgotten": ["N"]}
    muts = bs.mutations(a.claim, lines)
    assert len(muts) == 5
    for mut in muts:
        assert not bs.run_script(bs.column3_script(lines, mut))[0], mut


def test_the_mutation_adds_a_name_a_line_reads():
    lines = ["SET /A N=0", ":UP", "SET /A N=N+1", "ECHO %W%", "GOTO UP"]
    claim = {"kind": "never_inert", "certificate": [2, 5], "forgotten": ["N"]}
    assert bs.mutations(claim, lines)[-1]["forgotten"] == ["N", "W"]


def test_noninterference_on_phase_125():
    marks = ic.noninterference_marks()
    assert marks["I5"], marks
    assert marks["generated_kept"] == 299


def test_the_soundness_control():
    marks = ic.soundness_marks()
    assert marks["I6"], marks
    assert marks["certified"] == ("N1", "N4", "N7", "N8")
