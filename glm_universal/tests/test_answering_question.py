"""Tests for the question in the answering path (Phase 146).

``studies/ANSWERING_QUESTION_STUDY.md`` pre-registered ten marks.  These
tests pin:

* the **Lean file** (L1): it states the theorems the reply turn relies on and
  has no ``sorry``;
* **replies**: the request grammar, matching a reply to the question put, the
  next question, the confirming question, the refusals;
* the **answering path**: a ``locate`` junction answer ends with its question;
  replies narrow it; a contradiction is refused; column 3 agrees;
* the **conversation**: a reply is read only right after a question, and is
  rewritten to the previous query with the reply added;
* the answering path's loop on the full registers (Q1).
"""

from __future__ import annotations

import re
from pathlib import Path

from glm_universal.reasoning import answering_question as aq
from glm_universal.reasoning import timed_question as tq
from glm_universal.runtime.conversation import (Conversation, question_put,
                                                reply_rewrite)
from glm_universal.runtime.session import GeometricSession

LEAN = (Path(__file__).resolve().parents[2] / "glm_lean" / tq.ANSWER_LEAN_FILE)

_SESSION = None


def _session():
    global _SESSION
    if _SESSION is None:
        _SESSION = GeometricSession()
    return _SESSION


def test_lean_file_states_the_theorems_without_sorry():
    text = LEAN.read_text(encoding="utf-8")
    assert not re.search(r"\bsorry\b", text)
    for name in tq.ANSWER_LEAN_THEOREMS:
        assert re.search(rf"theorem {re.escape(name)}\b", text), name


# -- replies -----------------------------------------------------------------

def test_split_and_join_given():
    place, given = tq.split_given(
        "albedo given word:absorbed is no; confirm:physics:albedo is yes")
    assert place == "albedo"
    assert given == [("word:absorbed", "no"),
                     ("confirm:physics:albedo", "yes")]
    assert tq.join_given(place, given) == \
        "albedo given word:absorbed is no; confirm:physics:albedo is yes"
    assert tq.split_given("C moved 8 by 1/2") == ("C moved 8 by 1/2", [])


def test_malformed_reply_is_refused():
    for text in ("albedo given word:absorbed", "albedo given ;",
                 "albedo given is no", "albedo given word:absorbed=no"):
        try:
            tq.split_given(text)
        except tq.GivenError as error:
            assert error.reason == "malformed-reply"
        else:                                   # pragma: no cover
            raise AssertionError(text)


def test_next_question_then_confirmation():
    tie = tq.junction_tie(["physics:absorptance", "physics:albedo"])
    q = tq.pending_question(tie)
    assert q.key == "word:absorbed" and tie.splits(q)
    tq.apply_given(tie, [("word:absorbed", "no")])
    assert tie.status == "resolved" and tie.value == "physics:albedo"
    q = tq.pending_question(tie)
    assert q.kind == "confirm" and q.key == "confirm:physics:albedo"
    tq.apply_given(tie, [("confirm:physics:albedo", "yes")])
    assert tq.pending_question(tie) is None


def test_reply_order_does_not_matter():
    members = ["physics:acoustic_absorption",
               "physics:acoustic_intensity_level",
               "physics:acoustic_power_level"]
    a = tq.apply_given(tq.junction_tie(members),
                       [("attr:unit", "dB"), ("word:intensity", "no")])
    b = tq.apply_given(tq.junction_tie(members),
                       [("word:intensity", "no"), ("attr:unit", "dB")])
    assert a.live == b.live == ("physics:acoustic_power_level",)


def test_match_reply():
    tie = tq.junction_tie(["physics:absorptance", "physics:albedo"])
    record = tq.question_record(tie, tq.pending_question(tie))
    assert tq.match_reply(record, "No") == "no"
    assert tq.match_reply(record, "2") == "no"
    assert tq.match_reply(record, "yes.") == "yes"
    assert tq.match_reply(record, "maybe") is None
    assert tq.match_reply(record, "3") is None


def test_match_reply_prefers_the_text_of_an_option_to_its_number():
    members = [f"mathematics:filled_{r}x{24 // r}"
               for r in (1, 2, 3, 4, 6, 8, 12, 24)]
    tie = tq.junction_tie(members)
    record = tq.question_record(tie, tq.pending_question(tie))
    assert record["key"] == "attr:cols"
    # "1" is the option whose text is 1 (filled_24x1), not the first option
    one = tq.match_reply(record, "1")
    keeps = [o["keeps"] for o in record["options"] if o["reply"] == one]
    assert keeps == [["mathematics:filled_24x1"]]


# -- the answering path ------------------------------------------------------

def test_junction_answer_ends_with_its_question():
    sol = _session().ask("locate albedo")
    assert sol.ok
    assert "the GLM asks: Does its description mention 'absorbed'?" in \
        sol.answer
    record = question_put(sol)
    assert record["key"] == "word:absorbed"
    assert [o["keeps"] for o in record["options"]] == \
        [["physics:absorptance"], ["physics:albedo"]]


def test_single_carrier_puts_no_question():
    sol = _session().ask("locate C")
    assert sol.ok and question_put(sol) is None
    assert "the GLM asks" not in sol.answer


def test_replies_narrow_and_confirm():
    s = _session()
    sol = s.ask("locate albedo given word:absorbed is no")
    assert sol.ok and sol.payload["tie"]["live"] == ("physics:albedo",)
    assert question_put(sol)["kind"] == "confirm"
    sol = s.ask("locate albedo given word:absorbed is no; "
                "confirm:physics:albedo is yes")
    assert sol.ok and question_put(sol) is None
    assert "the confirming reply agrees" in sol.answer


def test_refusals():
    s = _session()
    cases = {
        "locate albedo given word:absorbed is no; confirm:physics:albedo is no":
            "(contradicted)",
        "locate C given attr:unit is dB": "(no-tie)",
        "locate albedo given attr:nothing is 1": "(unknown-question)",
        "locate albedo given word:absorbed is maybe": "(not-an-option)",
    }
    for text, reason in cases.items():
        sol = s.ask(text)
        assert not sol.ok and reason in sol.error, text


def test_column_three_checks_the_replies():
    from glm_universal.runtime.tct_engine import build_trace, verify_trace
    import dataclasses
    sol = _session().ask("locate acoustic_power_level given attr:unit is dB")
    assert verify_trace(build_trace(sol)).verified
    bad = dict(sol.expected)
    bad["live"] = "physics:acoustic_absorption"
    assert not verify_trace(build_trace(
        dataclasses.replace(sol, expected=bad))).verified


# -- the conversation --------------------------------------------------------

def test_reply_is_the_next_turn():
    conv = Conversation(session=_session())
    conv.ask("locate albedo")
    assert conv.shape_of("no") == "reply"
    conv.ask("no")
    assert conv.turns[-1].asked == "locate albedo given word:absorbed is no"
    assert conv.turns[-1].binding.shape == "reply"
    conv.ask("yes")
    assert conv.turns[-1].asked.endswith("; confirm:physics:albedo is yes")
    assert conv.turns[-1].question is None


def test_reply_only_where_a_question_was_put():
    report = aq.r1_controls(_session())
    assert report["checked"] == 12 and report["read_as_reply"] == []


def test_reply_rewrite():
    record = {"key": "attr:unit"}
    assert reply_rewrite("locate x", record, "dB") == \
        "locate x given attr:unit is dB"
    assert reply_rewrite("locate x given a is 1", record, "dB") == \
        "locate x given a is 1; attr:unit is dB"


def test_dialogue_through_the_conversation():
    members = ["physics:acoustic_absorption",
               "physics:acoustic_intensity_level",
               "physics:acoustic_power_level"]
    run = aq.conversation_run(members, "physics:acoustic_power_level",
                              session=_session())
    assert run["status"] == "confirmed"
    assert run["value"] == "physics:acoustic_power_level"
    assert run["replies"] <= len(members) - 1
    lied = aq.conversation_run(members, "physics:acoustic_power_level",
                               lie=True, session=_session())
    assert lied["status"] == "contradicted"


def test_loop_on_the_full_registers():
    q1 = aq.q1_loop()
    assert q1["runs"] == q1["resolved"] == 387
    assert q1["wrong"] == 0 and q1["within_n_minus_1"] == 387
    assert q1["questions_total"] == 1280
