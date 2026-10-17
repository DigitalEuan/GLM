"""Tests for the operations ladder and GLM-BAT (Phase 125).

``studies/OPERATIONS_LADDER_STUDY.md`` pre-registered nine marks.  These
tests pin:

* the **Lean file** (O1): it exists, states the twelve theorems the mark
  names, and has no ``sorry``;
* the **register** (O2, O3): the 97 terms are the supplied note's, every
  composition is layered and grounded, and every carrier round-trips;
* the **machine battery** (O4), the **language** (O5) and the **questions**
  (O6), each as declared and with no wrong answer;
* the **certificates** (O7) on a sample, and the refusal names;
* the **ladder's reasoning** and the cross-overs (O8), and hypothesis H as
  measured;
* **non-interference** (O9): the tools read none of the router's declared
  question sets, and the tools answer through the toolbox.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

from glm_universal.reasoning import batch_machine as bm
from glm_universal.reasoning import batch_speech as bs
from glm_universal.reasoning import operations as op
from glm_universal.reasoning import ops_ladder as ol
from glm_universal.runtime import toolbox

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "overlay" / "glm_lean" / op.LEAN_FILE


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in op.LEAN_THEOREMS:
        assert re.search(rf"^theorem {name}\b", text, re.MULTILINE), name
    assert "sorry" not in text
    assert "axiom " not in text


def test_the_register_is_the_note_layered_and_grounded():
    note = ol.note_check()
    assert note["terms"] == note["terms_in_note"] == 97
    assert note["tiers_in_note"] == 10
    assert note["mismatched_tiers"] == []
    assert note["layering_violations"] == []
    assert note["ungrounded"] == []
    assert note["idle_primitives"] == []
    for term in ol.term_ids():
        for part in ol.parts_of(term):
            assert ol.rank(part) < ol.rank(term)


def test_every_carrier_round_trips_and_is_distinct():
    census = ol.carrier_census()
    assert census["round_trips"] == census["distinct"] == 97
    assert census["distinct_ground_sets"] == 43
    objs = ol.operations_objects()
    assert all(o.domain == "operations" for o in objs)
    assert all(isinstance(x, (int, Fraction)) for o in objs for x in o.carrier)


def test_the_machine_battery_as_declared():
    report = op.machine_marks(scripts=False)
    assert report["runs"] == 25
    assert report["wrong"] == 0, [r for r in report["rows"]
                                  if not r["as_declared"]]


def test_the_language_reads_every_line_back():
    report = op.english_marks()
    assert report["read_back"] == report["lines_said"] == 78
    assert report["programs_as_declared"] == 6
    assert bs.read_english('add 1 to N. go to the end.') == [
        "SET /A N=N+1", "GOTO :EOF"]


def test_the_questions_as_declared():
    report = op.question_marks(scripts=False)
    assert report["questions"] == 18
    assert report["wrong"] == 0, [r for r in report["rows"]
                                  if not r["as_declared"]]


def test_a_cycle_certificate_verifies_and_its_mutations_fail():
    lines = list(op.M13)
    run = bm.run_program(bm.parse_program(lines))
    assert run.status == "never" and run.certificate == (2, 4)
    claim = {"kind": "never", "certificate": [2, 4]}
    assert bs.run_script(bs.column3_script(lines, claim))[0]
    for mut in bs.mutations(claim):
        assert not bs.run_script(bs.column3_script(lines, mut))[0], mut


def test_a_run_claim_verifies_and_its_mutations_fail():
    a = bs.answer("what does it print?", "\n".join(op.M7))
    assert a.answered and a.verified
    for mut in bs.mutations(a.claim):
        assert not bs.run_script(bs.column3_script(list(op.M7), mut))[0], mut


def test_refusals_are_named():
    assert bs.answer("what does it print?", "FORMAT C:").refusal == \
        "UNKNOWN_COMMAND"
    assert bs.answer("what does it print?", "ECHO %HOME%").refusal == \
        "UNDEFINED_VARIABLE"
    assert bs.answer("what is it for?", "ECHO hi").refusal == \
        "UNREAD_QUESTION"
    # Phase 126 (studies/INERT_COUNTER_STUDY.md, I5): M15's counter is inert,
    # so M15 is certified never to halt; a growing counter that a line reads
    # is still refused by that rule.  Phase 130
    # (studies/COUNTER_LASSO_STUDY.md, C5) moves that loop (N2): its counter
    # comes back translated, and no comparison on the pass changes, so it is
    # certified never to halt by a counter lasso; a growing variable that is
    # not a counter is still refused.
    assert bs.answer("does it halt?", "\n".join(op.M15)).claim["kind"] == \
        "never_inert"
    n2 = "SET /A N=0\n:UP\nSET /A N=N+1\nECHO %N%\nGOTO UP"
    assert bs.answer("does it halt?", n2, jump=False).refusal == \
        "UNDECIDED_WITHIN_BUDGET"
    assert bs.answer("does it halt?", n2).claim["kind"] == "never_lasso"
    # Phase 142 (studies/QUADRATIC_LASSO_STUDY.md) moves L12: B is an
    # accumulator, and no comparison on the quadratic pass ever changes.
    l12 = ("SET /A A=0\nSET /A B=0\n:UP\n"
           "SET /A A=A+1\nSET /A B=B+A\nIF %B% GTR -1 GOTO UP")
    assert bs.answer("does it halt?", l12, quadratic=False).refusal == \
        "UNDECIDED_WITHIN_BUDGET"
    assert bs.answer("does it halt?", l12).claim["kind"] == "never_lasso"
    assert bs.answer("what does it print?", "\n".join(op.M13)).refusal == \
        "NEVER_HALTS"
    assert set(bs.REFUSALS) >= {"UNKNOWN_COMMAND", "UNDEFINED_VARIABLE",
                                "UNDECIDED_WITHIN_BUDGET", "UNREAD_QUESTION"}


def test_the_ladder_reasoning_and_the_crossovers():
    marks = op.ladder_marks()
    assert marks["O8"], marks["relations"]
    assert ol.relation("pipe", "feedback_loop")["chain"] == (
        "feedback_loop", "pipeline", "pipe")
    assert all(r["resolves"] for r in ol.crossover_census())
    assert ol.resolve("exit code") == "exit_code"
    assert ol.resolve("Feedback Loop") == "feedback_loop"


def test_hypothesis_h_as_measured():
    proj = ol.projection_census()
    assert proj["every_term_projected"] and proj["every_target_known"]
    assert (proj["monotone"], proj["edges"]) == (185, 242)
    assert proj["holds"]


def test_the_tools_answer_and_read_no_declared_question():
    got = toolbox.run_tool("tool ladder pipe and feedback loop")
    assert got.ok and "Feedback Loop ⊃ Pipeline ⊃ Pipe" in got.text
    got = toolbox.run_tool("tool machine what does it print? :: ECHO hello")
    assert got.ok and '"hello"' in got.text and "verified" in got.text
    assert not toolbox.run_tool("tool ladder nonsense").ok
    assert not toolbox.run_tool("tool machine what does it print?").ok
    assert op.noninterference()["O9_routing"]
