"""Tests for constant bounds and repeated output in GLM-BAT (Phase 131).

``studies/CONSTANT_BOUND_STUDY.md`` pre-registered seven marks.  These tests
pin:

* the **Lean file** (B1): it exists, states the theorems the mark names, and
  has no ``sorry``;
* the **rule**: a constant operand is read at its step, a pass that writes a
  counter is not jumped, the output bound, and Phase 130's reading kept
  behind ``extended=False``;
* the **battery** (B2) as measured -- eight programs exactly as declared, and
  K6 and K10 as declared in everything but the pass jumped (the declared
  jumps were worked out by hand at the wrong recurrence) -- and the
  **questions** (B3);
* the **certificates** (B4): claims verify under ``python3 -I`` and every
  mutation fails;
* **non-interference** (B5) and the **soundness control** (B6).
"""

from __future__ import annotations

import re
from pathlib import Path

from glm_universal.reasoning import batch_machine as bm
from glm_universal.reasoning import batch_speech as bs
from glm_universal.reasoning import constant_bound as cb

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "src" / "lean" / cb.LEAN_FILE


def _p(text: str):
    return bm.parse_program(text.split(" / "))


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in cb.LEAN_THEOREMS:
        assert re.search(rf"^(?:@\[simp\] )?theorem {re.escape(name)}(?=\s)",
                         text, re.MULTILINE), name
    assert "sorry" not in text
    assert "axiom " not in text


def test_phase_130_reading_is_kept_behind_the_flag():
    for ident in ("K1", "K2"):
        program = bm.parse_program(cb._battery_lines(ident))
        assert bm.run_program(program, extended=False).status == "undecided"
        assert bm.run_program(program).status == "halted"


def test_a_constant_is_read_at_its_step():
    # The bound is set on the pass, before the comparison reads it.
    run = bm.run_program(_p("SET /A N=0 / SET L=5 / :UP / SET L=12000 / "
                            "SET /A N=N+1 / IF %N% LSS %L% GOTO UP / "
                            "ECHO %N%"))
    assert run.halted and run.out == ("12000",)
    assert run.steps == bm.plain_run(_p(
        "SET /A N=0 / SET L=5 / :UP / SET L=12000 / SET /A N=N+1 / "
        "IF %N% LSS %L% GOTO UP / ECHO %N%"), budget=100_000).steps


def test_a_pass_writing_a_counter_is_not_jumped():
    # Phase 131's rule; Phase 132's affine reading jumps it (P1).
    run = bm.run_program(bm.parse_program(cb._battery_lines("K5")),
                         affine=False)
    assert run.status == "undecided" and run.jumps == ()


def test_the_output_bound():
    assert bm.OUTPUT_CAP == 100_000
    run = bm.run_program(bm.parse_program(cb._battery_lines("K4")),
                         affine=False)
    assert run.status == "undecided"


def test_the_battery():
    marks = cb.battery_marks()
    assert marks["wrong_apart_from_jumps"] == 0, marks["rows"]
    assert marks["jumps_differ"] == ("K6", "K10")
    assert marks["wrong"] == 2 and not marks["B2"]
    got = {r["id"]: r["got"] for r in marks["rows"]}
    assert got["K6"][-1] == ((4, 7, 29999),)
    assert got["K10"][-1] == ((4, 7, 29999),)


def test_the_questions():
    marks = cb.question_marks()
    assert marks["B3"], [r for r in marks["rows"] if not r["as_declared"]]


def test_a_writing_jump_claim_verifies_and_its_mutations_fail():
    lines = list(cb._battery_lines("K1"))
    a = bs.answer("does it halt?", "\n".join(lines))
    assert a.answered and a.verified and a.value is True
    assert a.text == ("yes, it halts after 60002 steps with exit code 0 (the "
                      "pass from step 2 to step 5 adds 1 to N, and was taken "
                      "19999 times in one jump, writing 1 line each time, "
                      "until IF %N% LSS 20000 GOTO UP changed)")
    assert a.claim["jumps"] == [[2, 5, 19999]]
    assert a.claim["out"] == ["tick"] * 20000
    canon = [bm.render_line(i) for i in bm.parse_program(lines)]
    muts = bs.mutations(a.claim, canon)
    assert len(muts) == 7
    for mut in muts:
        assert not bs.run_script(bs.column3_script(canon, mut))[0]


def test_a_constant_bound_lasso_claim_verifies():
    lines = list(cb._battery_lines("K7"))
    a = bs.answer("does it halt?", "\n".join(lines))
    assert a.answered and a.verified and a.value is False
    assert a.claim == {"kind": "never_lasso", "certificate": [3, 5],
                       "d": {"N": 1}, "jumps": [], "budget": bm.BUDGET}


def test_certificates():
    marks = cb.certificate_marks()
    assert marks["B4"], marks
    assert marks["scripts"] == 18 and marks["mutations"] == 112


def test_noninterference():
    marks = cb.noninterference_marks()
    assert marks["B5"], marks
    assert marks["generated_kept"] == 300
    assert marks["generated_new_jumps"] == 0


def test_the_soundness_control():
    marks = cb.soundness_marks()
    assert marks["B6"], marks
    assert marks["halts_agree"] == ("K1", "K2", "K3", "K6", "K9", "K10")
    assert marks["never_hold"] == ("K7", "G206")
