"""Tests for several open ties at once (Phase 173).

*Created 20 October 2026.*

``studies/STACKED_DIALOGUE_STUDY.md`` pre-registered its marks.  These tests
pin:

* the **Lean file**: ``StackedDialogue.lean`` states its theorems and has no
  ``sorry``;
* the **stack**: a second question does not close the first; a reply that
  fits only the first is read against it, and closes it only;
* the **newest wins** when a reply fits both, and the binding names the
  other turn; a **named reply** (``turn N: <reply>``) is read against turn N;
* the **window**: a question survives ``OPEN_TIE_WINDOW`` unrelated turns and
  closes after one more, and a late reply is said to be late;
* with ``OPEN_TIE_STACK`` off the reading of Phase 172 comes back;
* the **stored measurement**, when current, meets every mark.
"""

from __future__ import annotations

from pathlib import Path

from glm_universal.reasoning import stacked_dialogue_study as sds
from glm_universal.runtime import conversation as cv
from glm_universal.runtime.conversation import Conversation

_LEAN = (Path(__file__).resolve().parents[2] / "glm_lean" / sds.LEAN_FILE)
_ALBEDO = "locate physics:albedo"                 # asks: mentions 'absorbed'?
_ACOUSTIC = "locate physics:acoustic_absorption"  # asks: what is its unit?


def _conv() -> Conversation:
    return Conversation(session=sds.ad._session())


def test_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in sds.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text
    assert sds.lean_marks()["met"]


def test_an_older_question_can_be_answered():
    conv = _conv()
    conv.ask(_ALBEDO)
    conv.ask(_ACOUSTIC)
    assert [t.index for t in conv.open_ties()] == [1, 0]
    binding = conv.resolve("no")          # fits the first question only
    assert binding.shape == "reply" and binding.antecedent_turn == 0
    conv.ask("no")
    open_now = [t.index for t in conv.open_ties()]
    assert 1 in open_now and 0 not in open_now


def test_stack_off_restores_the_newest_only_reading():
    conv = _conv()
    conv.ask(_ALBEDO)
    conv.ask(_ACOUSTIC)
    with sds.stack(False):
        assert [t.index for t in conv.open_ties()] == [1]
        assert conv.shape_of("no") is None


def test_the_newest_fitting_question_wins_and_the_other_is_named():
    conv = _conv()
    conv.ask(_ALBEDO)
    conv.ask(_ALBEDO)                     # the same question, twice open
    binding = conv.resolve("no")
    assert binding.antecedent_turn == 1
    assert binding.also == (0,)
    assert "turn 0" in binding.sentence


def test_a_named_reply_is_read_against_the_turn_it_names():
    conv = _conv()
    conv.ask(_ALBEDO)
    conv.ask(_ALBEDO)
    assert conv.resolve("turn 0: no").antecedent_turn == 0
    assert conv.shape_of("turn 5: no") is None       # no such question


def test_the_window_closes_a_question():
    conv = _conv()
    conv.ask(_ALBEDO)
    for text in sds._unrelated(cv.OPEN_TIE_WINDOW):
        conv.ask(text)
    assert conv.shape_of("no") == "reply"
    conv.ask(sds._unrelated(cv.OPEN_TIE_WINDOW + 1)[-1])
    assert conv.shape_of("no") is None
    assert conv.expired_fit("no") == (0,)       # said to be late
    assert conv.expired_fit("maybe") == ()


def test_stored_measurement_meets_every_mark():
    report = sds.current()
    if report is None:
        return
    assert report["met"] == report["taken"]
