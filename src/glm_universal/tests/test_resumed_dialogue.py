"""Tests for the open tie kept across turns (Phase 172).

*Created 20 October 2026.*

``studies/RESUMED_DIALOGUE_STUDY.md`` pre-registered its marks.  These tests
pin:

* the **Lean file**: ``ResumedDialogue.lean`` states its theorems and has no
  ``sorry``;
* the **mechanism**: a reply after an unrelated turn is read against the
  question put before it, and binds exactly the query it would have bound at
  once; with ``RESUME_OPEN_TIE`` off the old reading comes back;
* a question is **answered once**: after the reply closes it, an unrelated
  turn does not re-open it;
* the **newest question supersedes** an older one;
* no **whole query** of the evaluation set is taken for a reply;
* the **stored measurement**, when current, meets every mark.
"""

from __future__ import annotations

from pathlib import Path

from glm_universal.reasoning import resumed_dialogue_study as rds
from glm_universal.runtime.conversation import Conversation

_LEAN = (Path(__file__).resolve().parents[2] / "lean" / rds.LEAN_FILE)
_LOCATE = "locate physics:albedo"


def _conv() -> Conversation:
    return Conversation(session=rds.ad._session())


def test_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in rds.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text
    assert rds.lean_marks()["met"]


def test_reply_after_unrelated_turns_binds_the_same_query():
    at_once = _conv()
    at_once.ask(_LOCATE)
    direct = at_once.resolve("no")
    resumed = _conv()
    resumed.ask(_LOCATE)
    for text in rds.INTERJECTIONS:
        resumed.ask(text)
    assert resumed.open_tie() is not None
    assert resumed.open_tie().index == 0
    binding = resumed.resolve("no")
    assert binding.shape == "reply"
    assert binding.antecedent_turn == 0
    assert binding.rewritten == direct.rewritten


def test_switch_off_restores_the_previous_turn_reading():
    conv = _conv()
    conv.ask(_LOCATE)
    conv.ask(rds.INTERJECTIONS[0])
    assert conv.shape_of("no") == "reply"
    with rds.switch(False):
        assert conv.open_tie() is None
        assert conv.shape_of("no") is None


def test_a_question_is_answered_once():
    conv = _conv()
    conv.ask(_LOCATE)
    conv.ask("no")                      # puts the confirming question
    conv.ask("yes")                     # confirms; no question left open
    assert conv.open_tie() is None
    conv.ask(rds.INTERJECTIONS[0])
    for text in ("no", "yes"):
        assert conv.shape_of(text) is None, text


def test_the_newest_question_supersedes():
    conv = _conv()
    conv.ask(_LOCATE)
    conv.ask(rds.INTERJECTIONS[0])
    conv.ask("locate physics:acoustic_absorption")
    newest = conv.open_tie()
    assert newest is not None and newest.index == 2


def test_no_evaluation_question_is_taken_for_a_reply():
    from glm_universal.evaluation.cases import CASES
    conv = _conv()
    conv.ask(_LOCATE)
    conv.ask(rds.INTERJECTIONS[0])
    assert conv.open_tie() is not None
    assert [c.question for c in CASES
            if conv.shape_of(c.question) == "reply"] == []


def test_stored_measurement_meets_every_mark():
    report = rds.current()
    if report is None:
        return
    assert report["met"] == report["taken"]
