"""Tests for the plan store: a resolved follow-up kept against a digest.

What is pinned here is the contract a cache has to keep, not the saving.  A
store may save work and may never change an answer, so the tests that matter
are the ones that would catch it changing one: every declared follow-up comes
out of a stored conversation exactly as it comes out of a fresh one, refusals
with their reason and their wording; a plan whose stored content does not
match the request is a miss rather than a hit; and the coarse key -- the
control, which keys a plan by its follow-up text alone -- is shown to answer
one conversation with another's antecedent rather than merely suspected of it.

The machine-checked counterparts are in ``RequestProject/GLM/PlanStore.lean``
-- ``lookup_record``, ``refusal_survives_replay``, ``replay_agrees_with_run``,
``replay_preserves_refusal``, ``exactKey_injective`` and
``coarse_key_answers_the_wrong_question``.  Directive D7 -- no float anywhere
-- is checked statically.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from glm_universal.reasoning import exactness as ex
from glm_universal.runtime import conversation as CV
from glm_universal.runtime import plan_store as PS
from glm_universal.runtime.session import GeometricSession

LEAN = (Path(__file__).resolve().parents[3]
        / "RequestProject" / "GLM" / "PlanStore.lean")


@pytest.fixture(scope="module")
def session():
    return GeometricSession()


@pytest.fixture(scope="module")
def report(session):
    return PS.plan_store_report(session)


def _plan(prefix, text, outcome="C", reason=""):
    return PS.Plan(prefix=tuple(prefix), text=text, shape="pronoun",
                   outcome=outcome, reason=reason,
                   message=reason and f"{text!r}: {reason}")


class TestTheKey:

    def test_the_same_conversation_gives_the_same_key(self):
        assert (PS.plan_key(("describe carbon",), "describe it")
                == PS.plan_key(("describe carbon",), "describe it"))

    def test_a_different_conversation_gives_a_different_key(self):
        """``GLM.PlanStore.exactKey_injective``."""
        assert (PS.plan_key(("describe carbon",), "describe it")
                != PS.plan_key(("describe water",), "describe it"))

    def test_the_coarse_key_cannot_tell_them_apart(self):
        assert (PS.plan_key(("describe carbon",), "describe it", PS.COARSE)
                == PS.plan_key(("describe water",), "describe it", PS.COARSE))

    def test_an_undeclared_rule_is_refused(self):
        with pytest.raises(ValueError):
            PS.plan_key((), "describe it", "whatever")


class TestWhatIsRecordedComesBack:

    def test_a_binding_is_replayed(self):
        """``GLM.PlanStore.lookup_record``."""
        store = PS.PlanStore()
        plan = _plan(("describe carbon",), "describe it")
        store.put(plan)
        assert store.get(("describe carbon",), "describe it") == plan

    def test_a_refusal_is_replayed_with_its_reason(self):
        """``GLM.PlanStore.refusal_survives_replay``."""
        store = PS.PlanStore()
        plan = _plan((), "describe it", outcome="no-antecedent",
                     reason="no-antecedent")
        store.put(plan)
        back = store.get((), "describe it")
        assert back is not None and back.refused
        assert back.reason == "no-antecedent"
        assert back.message == plan.message

    def test_an_unrecorded_follow_up_is_a_miss(self):
        store = PS.PlanStore()
        assert store.get(("describe carbon",), "describe it") is None
        assert store.misses == 1

    def test_a_hit_whose_content_does_not_match_is_a_miss(self):
        """The digest addresses integrity and never meaning (**D3**): the
        stored plan carries its own prefix and text, and they are compared."""
        store = PS.PlanStore()
        plan = _plan(("describe carbon",), "describe it")
        store._plans[store.key_of(("describe water",), "describe it")] = plan
        assert store.get(("describe water",), "describe it") is None
        assert store.mismatches == 1


class TestAgainstTheShippedLayer:

    def test_every_declared_follow_up_replays_unchanged(self, report,
                                                        subtests):
        for row in report["rows"]:
            with subtests.test(follow_up=row["key"]):
                assert row["replays"], row["outcome"]
        assert report["replayed"] == report["declared"]

    def test_every_declared_outcome_is_still_the_declared_one(self, report,
                                                              subtests):
        for row in report["rows"]:
            with subtests.test(follow_up=row["key"]):
                assert row["outcome"] == row["expected"]

    def test_every_refusal_is_replayed(self, report):
        """``GLM.PlanStore.replay_preserves_refusal`` -- the case the round
        was taken for."""
        assert report["refusals_replayed"] == report["refusals"]
        assert report["refusals"] == 7

    def test_a_replay_costs_no_licensing_trials(self, report):
        assert report["trials_replayed"] == 0
        assert report["trials_saved"] == report["trials_first"]

    def test_the_worst_follow_up_is_the_tie(self, report):
        """The fourteen-row tie is the expensive case, and it is a refusal --
        which is exactly what the supplied store, keeping successes only,
        would not have kept."""
        worst = max(report["rows"], key=lambda row: row["trials_first"])
        assert worst["key"] == "pronoun-tie-refused"
        assert worst["refused"]
        assert worst["trials_first"] == report["worst_case_trials"]

    def test_a_store_changes_no_answer(self, session, subtests):
        """The same conversation with and without a store, turn by turn."""
        store = PS.PlanStore()
        for key, script, _expected, _note in CV.DECLARED_FOLLOW_UPS:
            with subtests.test(follow_up=key):
                plain = _outcome(CV.Conversation(session), script)
                stored = _outcome(CV.Conversation(session, store=store),
                                  script)
                again = _outcome(CV.Conversation(session, store=store),
                                 script)
                assert plain == stored == again

    def test_the_coarse_key_answers_the_wrong_question(self, report):
        """``GLM.PlanStore.coarse_key_answers_the_wrong_question``."""
        assert report["coarse_wrong"] == 8
        assert "describe it" in report["shared_texts"]


def _outcome(conversation, script):
    for text in script[:-1]:
        conversation.ask(text)
    try:
        binding = conversation.resolve(script[-1])
    except CV.FollowUpError as error:
        return ("refused", error.reason, str(error))
    return ("bound", binding.name, binding.rewritten)


class TestTheDiscipline:

    def test_no_float_is_constructed(self):
        assert ex.module_float_sites(Path(PS.__file__)) == {}
        assert ex.module_float_sites(Path(CV.__file__)) == {}

    def test_the_lean_file_names_what_the_module_cites(self, subtests):
        text = LEAN.read_text(encoding="utf-8")
        for theorem in ("lookup_record", "refusal_survives_replay",
                        "lookup_record_of_ne", "sound_record",
                        "replay_agrees_with_run", "replay_preserves_refusal",
                        "exactKey_injective",
                        "coarse_key_answers_the_wrong_question",
                        "exact_key_separates_the_two_conversations"):
            with subtests.test(theorem=theorem):
                assert f"theorem {theorem}" in text

    def test_the_lean_file_has_no_sorry(self):
        assert "sorry" not in LEAN.read_text(encoding="utf-8")
