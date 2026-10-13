"""Tests for passes that print a counter, long output and the diagnosis of a
refusal in GLM-BAT (Phase 132).

``studies/AFFINE_OUTPUT_STUDY.md`` pre-registered nine marks.  These tests
pin:

* the **Lean file** (A1): it exists, states the theorems the mark names, and
  has no ``sorry``;
* the **rule**: an ``ECHO`` naming a counter is read as a template, the
  affine output bound, run form above 100,000 lines, and Phase 131's reading
  kept behind ``affine=False``;
* the **battery** (A2) and the **questions** (A3) as measured -- nineteen of
  twenty as declared, P8's printed text in the declared encoder's segments
  rather than the hand-worked ones;
* the **diagnosis** (A5) and its closed forms (A6), with the NRCI reported
  and read by nothing;
* the **certificates** (A4), **non-interference** (A7) and the **soundness
  control** (A8).
"""

from __future__ import annotations

import re
from pathlib import Path

from glm_universal.reasoning import affine_output as ao
from glm_universal.reasoning import batch_machine as bm
from glm_universal.reasoning import batch_speech as bs

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "overlay" / "glm_lean" / ao.LEAN_FILE


def _p(text: str):
    return bm.parse_program(text.split(" / "))


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in ao.LEAN_THEOREMS:
        assert re.search(rf"^(?:@\[simp\] )?theorem {re.escape(name)}(?=\s)",
                         text, re.MULTILINE), name
    assert "sorry" not in text
    assert "axiom " not in text


def test_phase_131_reading_is_kept_behind_the_flag():
    program = bm.parse_program(ao._battery_lines("P1"))
    assert bm.run_program(program, affine=False).status == "undecided"
    run = bm.run_program(program)
    assert run.halted and run.jumps[0][6] == ("N",)


def test_a_template_reads_the_counter_at_its_step():
    run = bm.run_program(_p("SET /A N=0 / SET W=x / :UP / SET /A N=N+1 / "
                            "ECHO %W%%N%-%W% / SET /A N=N+1 / "
                            "IF %N% LSS 30000 GOTO UP"))
    plain = bm.plain_run(_p("SET /A N=0 / SET W=x / :UP / SET /A N=N+1 / "
                            "ECHO %W%%N%-%W% / SET /A N=N+1 / "
                            "IF %N% LSS 30000 GOTO UP"), budget=200_000)
    assert run.halted and run.jumps
    assert (run.steps, run.out) == (plain.steps, plain.out)
    assert run.out[:2] == ("x1-x", "x3-x")


def test_the_run_form_round_trips():
    lines = (["tick"] * 7 + [f"N={n}" for n in range(5, -6, -1)]
             + [x for n in range(4) for x in ("a", f"{n}:{2 * n}")]
             + ["007", "7", "-0", "x"])
    segs = bs.output_runs(lines)
    assert bs.decode_runs(segs) == lines
    assert segs[0] == [["tick"], 7, []]
    assert bs.say_runs(["1", "2", "3"]) == '"1" … "3" (3 lines; the number steps by 1)'


def test_the_output_bound_and_the_run_form():
    assert bm.AFFINE_OUTPUT_CAP == 1_000_000
    run = bm.run_program(bm.parse_program(ao._battery_lines("P2")))
    claim = bs._run_claim(run, {})
    assert "out" not in claim
    assert claim["out_runs"] == [[["tick"], 500000, []], [["500000"], 1, [0]]]
    assert claim["err_runs"] == []


def test_the_battery():
    marks = ao.battery_marks()
    assert marks["A2"], [r for r in marks["rows"] if not r["as_declared"]]


def test_the_questions():
    marks = ao.question_marks()
    assert marks["wrong"] == 1 and not marks["A3"]
    assert marks["missed"] == ("P8: what does it print?",)
    p8 = next(r for r in marks["rows"] if r["id"] == "P8"
              and r["question"] == "what does it print?")
    assert '"3333" … "9999" (67 lines; the number steps by 101)' in p8["text"]


def test_the_diagnosis_and_its_nrci():
    marks = ao.diagnosis_marks()
    assert marks["A5"], [r for r in marks["rows"] if not r["as_declared"]]
    assert marks["l12_b_nrci"] == "0.999993"
    assert marks["nrci_micro"]["L12.B"] > 990_000
    assert marks["nrci_micro"]["G2.N"] < 200_000


def test_the_nrci_decides_nothing():
    # The diagnosis is the same whatever the NRCI says: the refusal and the
    # shape come from exact differences alone.
    a = bs.answer("why is it undecided?", ao._program_text("L12"))
    b = bs.answer("does it halt?", ao._program_text("L12"))
    assert a.answered and a.verified and "NRCI 1.0000" in a.text
    assert "B" in a.claim["shapes"] and "nrci" not in a.claim
    assert not b.answered and b.refusal == "UNDECIDED_WITHIN_BUDGET"


def test_the_closed_forms_predict():
    marks = ao.prediction_marks()
    assert marks["A6"] and marks["variables"] == 8


def test_certificates():
    marks = ao.certificate_marks()
    assert marks["verified"] == marks["scripts"] == 33
    assert marks["rejected"] == marks["mutations"]
    assert marks["undecided_generated"] == 0
    assert marks["p2_claim_bytes"] < 1000
    assert marks["p2_script_bytes"] > 10_000 and not marks["A4"]


def test_noninterference():
    marks = ao.noninterference_marks()
    assert marks["A7"], marks
    assert marks["generated_kept"] == 300
    assert marks["generated_new_jumps"] == 0


def test_the_soundness_control():
    marks = ao.soundness_marks()
    assert marks["A8"], marks
    assert len(marks["halts_agree"]) == 8
