"""Tests for the conversation layer: the turn that refers back to an earlier
turn, bound by licensing or refused with a reason.

What is pinned here is the *mechanism*, not the score.  A follow-up must be
detected by one of three declared surface shapes and by nothing else; a
candidate must be admitted only when the query it produces actually solves;
recency must decide between turns and licensing within one; and the three
refusals must be reachable, named, and earned.  The point of the operation is
as much what it declines -- a fourteen-row tie has fourteen equally good
referents -- as what it binds.

Two controls are pinned with it: the same texts asked of a session with no
memory (which is the system as it was), and the recency rule that binds to the
most recent mention with no licensing test.

The machine-checked counterparts are in ``RequestProject/GLM/Conversation.lean``.
Directive D7 -- no float anywhere -- is checked statically.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from glm_universal.reasoning import exactness as ex
from glm_universal.runtime import conversation as CV
from glm_universal.runtime.session import GeometricSession

LEAN = (Path(__file__).resolve().parents[3]
        / "RequestProject" / "GLM" / "Conversation.lean")


@pytest.fixture(scope="module")
def session():
    return GeometricSession()


@pytest.fixture(scope="module")
def report(session):
    return CV.conversation_report(session)


def _talk(session, *texts):
    """A conversation over the shared session, up to but not past the last."""
    conversation = CV.Conversation(session)
    for text in texts:
        conversation.ask(text)
    return conversation


class TestWhatCountsAsAFollowUp:

    def test_a_whole_query_is_not_a_follow_up(self, session, subtests):
        conversation = CV.Conversation(session)
        for text in ("describe carbon", "largest atomic_weight_u in element",
                     "nearest 3 to oxygen", "H : He :: Li : ?"):
            with subtests.test(text=text):
                assert conversation.shape_of(text) is None

    def test_the_three_shapes_are_recognised(self, session, subtests):
        conversation = CV.Conversation(session)
        for text, shape in (("describe it", "pronoun"),
                            ("field molar_mass_u of it", "pronoun"),
                            ("and the smallest?", "end-flip"),
                            ("what about the largest", "end-flip"),
                            ("and oxygen?", "subject")):
            with subtests.test(text=text):
                assert conversation.shape_of(text) == shape

    def test_an_end_word_beats_the_subject_pattern(self, session):
        """*and the smallest?* matches both patterns; the order decides."""
        assert CV.Conversation(session).shape_of("and the smallest?") \
            == "end-flip"

    def test_a_continuation_naming_no_carrier_is_not_a_follow_up(self,
                                                                 session):
        assert CV.Conversation(session).shape_of("and then what") is None

    def test_a_whole_query_passes_straight_through(self, session):
        conversation = CV.Conversation(session)
        solution = conversation.ask("describe carbon")
        assert solution.ok
        assert conversation.turns[-1].binding is None
        assert conversation.turns[-1].asked == "describe carbon"

    def test_resolving_a_whole_query_is_refused_as_such(self, session):
        with pytest.raises(CV.FollowUpError) as caught:
            CV.Conversation(session).resolve("describe carbon")
        assert caught.value.reason == "not-a-follow-up"


class TestWhatATurnLeavesBehind:

    def test_a_subject_is_recorded_under_its_register_name(self, session):
        conversation = _talk(session, "describe carbon")
        assert [m.name for m in conversation.turns[-1].side("subject")] \
            == ["C"]

    def test_a_fold_records_the_rows_it_produced(self, session):
        conversation = _talk(session, "largest atomic_weight_u in element")
        assert [m.name for m in conversation.turns[-1].side("answer")] \
            == ["Og"]

    def test_a_tie_records_every_row_that_attained_the_end(self, session):
        conversation = _talk(session,
                             "largest abstract_concrete in carrier:lexicon")
        assert len(conversation.turns[-1].side("answer")) == 14

    def test_a_comparison_records_both_rows_and_no_answer(self, session):
        conversation = _talk(session,
                             "order atomic_weight_u of carbon and oxygen")
        turn = conversation.turns[-1]
        assert sorted(m.name for m in turn.side("subject")) == ["C", "O"]
        assert turn.side("answer") == ()

    def test_a_list_of_neighbours_is_not_a_name(self, session):
        conversation = _talk(session, "nearest 3 to oxygen")
        turn = conversation.turns[-1]
        assert turn.side("answer") == ()
        assert [m.name for m in turn.side("subject")] == ["O"]

    def test_a_refused_turn_leaves_nothing_behind(self, session):
        conversation = CV.Conversation(session)
        conversation.ask("describe unobtainium")
        assert conversation.turns[-1].mentions == ()


class TestLicensing:
    """The whole of the idea: a candidate is admitted when the query it
    produces solves, and by no other test."""

    def test_the_binding_walks_past_a_nearer_candidate_that_cannot_answer(
            self, session):
        conversation = _talk(session, "describe carbon", "describe water")
        binding = conversation.resolve("field electronegativity_pauling of it")
        assert binding.name == "C"
        assert binding.antecedent_turn == 0

    def test_the_same_conversation_binds_the_nearer_one_when_it_can_answer(
            self, session):
        conversation = _talk(session, "describe carbon", "describe water")
        binding = conversation.resolve("field molar_mass_u of it")
        assert binding.name == "water"
        assert binding.antecedent_turn == 1

    def test_the_answer_side_outranks_the_subject_side(self, session):
        conversation = _talk(session, "H : He :: Li : ?")
        binding = conversation.resolve("describe it")
        assert binding.name == "Ne"
        assert binding.side == "answer"

    def test_a_bound_query_is_the_text_with_the_pronoun_replaced(self,
                                                                 session):
        conversation = _talk(session, "describe carbon")
        binding = conversation.resolve("describe it")
        assert binding.rewritten == "describe C"

    def test_the_binding_is_answered_by_the_ordinary_solver(self, session):
        conversation = _talk(session, "largest atomic_weight_u in element")
        solution = conversation.ask("describe it")
        assert solution.ok
        assert solution.answer == session.ask("describe Og").answer


class TestWhatItRefuses:
    """Three named reasons, and the one the operation exists for."""

    def test_a_follow_up_with_nothing_to_follow_is_refused(self, session):
        with pytest.raises(CV.FollowUpError) as caught:
            CV.Conversation(session).resolve("describe it")
        assert caught.value.reason == "no-antecedent"

    def test_a_tie_is_refused_rather_than_resolved(self, session):
        conversation = _talk(session,
                             "largest abstract_concrete in carrier:lexicon")
        with pytest.raises(CV.FollowUpError) as caught:
            conversation.resolve("describe it")
        assert caught.value.reason == "ambiguous-antecedent"
        assert len(caught.value.considered) == 14

    def test_two_rows_of_one_comparison_are_refused(self, session):
        conversation = _talk(session,
                             "order atomic_weight_u of carbon and oxygen")
        with pytest.raises(CV.FollowUpError) as caught:
            conversation.resolve("describe it")
        assert caught.value.reason == "ambiguous-antecedent"

    def test_a_question_no_mentioned_carrier_answers_is_refused(self,
                                                                session):
        conversation = _talk(session, "describe energy")
        with pytest.raises(CV.FollowUpError) as caught:
            conversation.resolve("field electronegativity_pauling of it")
        assert caught.value.reason == "unlicensed"

    def test_an_end_flip_with_no_column_behind_it_is_refused(self, session):
        conversation = _talk(session, "describe carbon")
        with pytest.raises(CV.FollowUpError) as caught:
            conversation.resolve("and the smallest?")
        assert caught.value.reason == "no-antecedent"

    def test_a_substitution_into_a_two_row_question_is_refused(self, session):
        conversation = _talk(session,
                             "order atomic_weight_u of carbon and oxygen")
        with pytest.raises(CV.FollowUpError) as caught:
            conversation.resolve("and nitrogen?")
        assert caught.value.reason == "ambiguous-antecedent"

    def test_a_substitution_the_table_cannot_take_is_refused(self, session):
        conversation = _talk(session,
                             "field electronegativity_pauling of carbon")
        with pytest.raises(CV.FollowUpError) as caught:
            conversation.resolve("and water?")
        assert caught.value.reason == "unlicensed"

    def test_every_declared_reason_is_reachable(self, session, subtests):
        seen = set()
        for script in (("describe it",),
                       ("largest abstract_concrete in carrier:lexicon",
                        "describe it"),
                       ("describe energy",
                        "field electronegativity_pauling of it")):
            with subtests.test(script=script[-1]):
                conversation = _talk(session, *script[:-1])
                with pytest.raises(CV.FollowUpError) as caught:
                    conversation.resolve(script[-1])
                seen.add(caught.value.reason)
        assert seen == set(CV.REFUSAL_REASONS) - {"not-a-follow-up"}


class TestTheOtherTwoShapes:

    def test_an_end_flip_asks_the_same_column_at_the_other_end(self, session):
        conversation = _talk(session, "largest atomic_weight_u in element")
        binding = conversation.resolve("and the smallest?")
        assert binding.rewritten == "smallest atomic_weight_u in element"

    def test_a_substitution_asks_the_same_question_of_another_row(self,
                                                                  session):
        conversation = _talk(session, "field atomic_weight_u of carbon")
        binding = conversation.resolve("and oxygen?")
        assert binding.rewritten == "field atomic_weight_u of oxygen"

    def test_a_substitution_answers_what_the_written_out_query_answers(
            self, session):
        conversation = _talk(session, "field atomic_weight_u of carbon")
        solution = conversation.ask("and oxygen?")
        assert solution.answer \
            == session.ask("field atomic_weight_u of oxygen").answer


class TestTheMeasurement:

    def test_every_declared_follow_up_came_out_as_declared(self, report,
                                                           subtests):
        for row in report["rows"]:
            with subtests.test(key=row["key"]):
                assert row["as_declared"], row["detail"]

    def test_the_declared_set_covers_both_halves(self, report):
        assert report["answered"] + report["refused"] == report["declared"]
        assert (set(report["refusal_reasons"])
                == set(CV.REFUSAL_REASONS) - {"not-a-follow-up"})

    def test_no_declared_follow_up_is_answered_without_the_conversation(
            self, report):
        """The control that says what the capability is worth."""
        assert report["alone_answered"] == 0

    def test_the_recency_control_differs_where_licensing_bites(self, report):
        assert report["control_wrong"] >= 1
        assert "pronoun-licensing-skips" in report["control_wrong_keys"]

    def test_the_verdict_is_stated_with_its_caveat(self, report):
        assert str(report["answered"]) in report["verdict"]
        assert "no memory" in report["verdict"]
        assert "parses English" in report["caveat"]

    def test_the_declared_set_is_written_down_before_it_is_run(self):
        keys = [row[0] for row in CV.DECLARED_FOLLOW_UPS]
        assert len(keys) == len(set(keys))
        for _key, script, expected, note in CV.DECLARED_FOLLOW_UPS:
            assert len(script) >= 1 and all(script)
            assert expected
            assert note


class TestTheProvedHalf:

    def test_the_lean_file_states_what_the_module_cites(self, subtests):
        text = LEAN.read_text(encoding="utf-8")
        for name in ("resolve_bound_licensed", "resolve_bound_mem",
                     "resolve_noAntecedent_iff",
                     "resolve_unlicensed_all_refused",
                     "resolve_ambiguous_two_licensed",
                     "resolve_stable_under_unlicensed_turn",
                     "most_recent_mention_is_not_the_antecedent",
                     "tie_is_refused",
                     "nothing_said_yet_is_no_antecedent"):
            with subtests.test(name=name):
                assert f"theorem {name}" in text
        assert "sorry" not in text

    def test_the_proved_refusals_are_the_shipped_ones(self):
        text = LEAN.read_text(encoding="utf-8")
        for reason in ("noAntecedent", "ambiguous", "unlicensed"):
            assert reason in text
        for reason in ("no-antecedent", "ambiguous-antecedent", "unlicensed"):
            assert reason in CV.REFUSAL_REASONS


class TestExactness:

    def test_no_float_is_constructed(self):
        assert ex.module_float_sites(Path(CV.__file__)) == {}
