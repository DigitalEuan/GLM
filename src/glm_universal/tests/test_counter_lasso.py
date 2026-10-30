"""Tests for counter lassos in GLM-BAT (Phase 130).

``studies/COUNTER_LASSO_STUDY.md`` pre-registered seven marks.  These tests
pin:

* the **Lean file** (C1): it exists, states the theorems the mark names, and
  has no ``sorry``;
* the **rule**: the counters of a program, the first change of a comparison
  along the passes, and the order of use (a program an earlier reading
  decides is not re-read);
* the **battery** (C2) and the **questions** (C3), as declared;
* the **certificates** (C4): a ``run_jump`` and a ``never_lasso`` claim
  verify under ``python3 -I`` and every mutation fails;
* **non-interference** on Phases 125 and 126 (C5) and the **soundness
  control** (C6).
"""

from __future__ import annotations

import re
from pathlib import Path

from glm_universal.reasoning import batch_machine as bm
from glm_universal.reasoning import batch_speech as bs
from glm_universal.reasoning import counter_lasso as cl
from glm_universal.reasoning import operations as op

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "src" / "lean" / cl.LEAN_FILE


def _p(text: str):
    return bm.parse_program(text.split(" / "))


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in cl.LEAN_THEOREMS:
        assert re.search(rf"^theorem {name}\b", text, re.MULTILINE), name
    assert "sorry" not in text
    assert "axiom " not in text


def test_the_counters_of_a_program():
    assert bm.counters(_p("SET /A N=0 / :UP / SET /A N=N+1 / GOTO UP")) \
        == ("N",)
    assert bm.counters(_p("SET /A I=I+3 / SET /A J=J-1 / SET /A K=K*2 / "
                          "SET /A B=B+A / SET /A M=N+1")) == ("I", "J")
    assert bm.counters(_p("SET /A N=N+1> f.txt")) == ()


def test_the_first_change_against_a_brute_force_read():
    for op_ in ("EQU", "NEQ", "LSS", "LEQ", "GTR", "GEQ"):
        for e0 in range(-12, 13):
            for b in range(-5, 6):
                truth = bm._CMP_TRUTH[op_]
                brute = next((m for m in range(1, 40)
                              if truth(e0 + b * m) != truth(e0)), None)
                assert bm.first_change(e0, b, op_) == brute, (op_, e0, b)


def test_the_order_of_use():
    run = bm.run_program(bm.parse_program(op.M15))
    assert run.status == "never" and run.forgotten == ("N",)
    assert run.lasso == () and run.jumps == ()
    short = bm.run_program(_p("SET /A N=0 / :UP / SET /A N=N+1 / "
                              "IF %N% LSS 5 GOTO UP / ECHO %N%"))
    assert short.halted and short.steps == 13 and short.jumps == ()


def test_the_battery():
    marks = cl.battery_marks()
    assert marks["C2"], [r for r in marks["rows"] if not r["as_declared"]]


def test_the_questions():
    marks = cl.question_marks()
    assert marks["C3"], [r for r in marks["rows"] if not r["as_declared"]]


def test_a_run_jump_claim_verifies_and_its_mutations_fail():
    lines = list(cl.BATTERY[0][1])
    a = bs.answer("does it halt?", "\n".join(lines))
    assert a.answered and a.verified and a.value is True
    assert a.text.startswith("yes, it halts after 40003 steps with exit "
                             "code 0 (the pass from step 2 to step 4 adds 1 "
                             "to N, and was taken 19999 times in one jump")
    assert a.claim["kind"] == "run_jump"
    assert a.claim["jumps"] == [[2, 4, 19999]]
    canon = [bm.render_line(i) for i in bm.parse_program(lines)]
    muts = bs.mutations(a.claim, canon)
    assert len(muts) == 6
    for mut in muts:
        assert not bs.run_script(bs.column3_script(canon, mut))[0], mut


def test_a_never_lasso_claim_verifies_and_its_mutations_fail():
    lines = list(cl.BATTERY[1][1])
    a = bs.answer("does it halt?", "\n".join(lines))
    assert a.answered and a.verified and a.value is False
    assert a.claim == {"kind": "never_lasso", "certificate": [2, 5],
                       "d": {"N": 1}, "jumps": [], "budget": bm.BUDGET}
    canon = [bm.render_line(i) for i in bm.parse_program(lines)]
    muts = bs.mutations(a.claim, canon)
    assert len(muts) == 4
    for mut in muts:
        assert not bs.run_script(bs.column3_script(canon, mut))[0], mut


def test_noninterference_on_phases_125_and_126():
    marks = cl.noninterference_marks()
    assert marks["C5"], marks
    assert marks["generated_kept"] == 299
    assert marks["generated_newly_decided_ids"] == (206,)


def test_the_soundness_control():
    marks = cl.soundness_marks()
    assert marks["C6"], marks
    assert marks["halts_agree"] == ("L1", "L3", "L4", "L5", "L7", "L8")
    assert marks["never_hold"] == ("L2", "L6", "G206")
    assert marks["controls"] == {"L9": ("halted", 60002),
                                 "L10": ("halted", 60002),
                                 "L11": ("halted", 40003)}
