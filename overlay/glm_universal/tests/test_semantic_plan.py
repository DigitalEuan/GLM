"""Tests for the typed planner and its held-out measurement.

What is pinned here is the *discipline* before the score: a plan is only
ever an operation the machine already has or an exact computation over a
declared definition; the answer is given only when every licensed plan
agrees; with no licensed plan the answer is the grammar's own; and nothing on
the path constructs a float.  The machine-checked counterparts are in
``RequestProject/GLM/SemanticPlan.lean`` -- ``accept_perm``,
``accept_eq_answered_iff``, ``disagreement_is_ambiguous``,
``planned_conservative`` and the two refutations of the first-licensed rule.

The score is pinned only where it is a safety claim: no wrong answer on the
adversarial set, and the stress set's first run frozen as it was taken.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.evaluation import heldout as HO
from glm_universal.reasoning import typed_plans as TP
from glm_universal.runtime import semantic_plan as SP
from glm_universal.runtime.session import GeometricSession

LEAN = (Path(__file__).resolve().parents[3]
        / "RequestProject" / "GLM" / "SemanticPlan.lean")


@pytest.fixture(scope="module")
def session():
    return GeometricSession()


def _outcome(licensed: bool, value: str, name: str = "p") -> SP.Outcome:
    plan = SP.Plan(name, "field", (), query=name)
    return SP.Outcome(plan, licensed, value, value)


class TestCleaning:

    def test_number_words_become_digits(self):
        assert SP.clean("is ninety-one prime?") == "is 91 prime"
        assert SP.clean("add two and two") == "add 2 and 2"

    def test_american_metre_is_folded(self):
        assert SP.clean("convert 3 meters into feet") == \
            "convert 3 metres into feet"

    def test_numbers_are_exact(self):
        assert SP.parse_number("3/2") == Fraction(3, 2)
        assert SP.parse_number("2.5") == Fraction(5, 2)
        assert SP.parse_number("-7") == Fraction(-7)
        assert SP.parse_number("1/0") is None


class TestExactComputation:

    def test_rounding_is_half_even_and_integer(self):
        assert SP.decimal_places(Fraction(1250, 127), 4) == "9.8425"
        assert SP.decimal_places(Fraction(1, 8), 2) == "0.12"
        assert SP.decimal_places(Fraction(3, 8), 2) == "0.38"

    def test_prime_witness(self):
        assert SP.prime_witness(91) == 7
        assert SP.prime_witness(97) is None
        assert SP.prime_witness(1000003) is None

    def test_every_unit_factor_is_a_positive_rational(self, subtests):
        for unit in SP.UNITS:
            with subtests.test(unit=unit.name):
                assert isinstance(unit.factor, Fraction)
                assert unit.factor > 0
                assert unit.source

    def test_the_international_foot_is_exact(self):
        assert SP.unit_named("feet").factor == Fraction(3048, 10000)


class TestTheLicensingRule:
    """The shipped form of ``GLM.SemanticPlan.accept``."""

    def test_agreement_answers(self):
        verdict, chosen, _ = SP.accept([_outcome(True, "6", "a"),
                                        _outcome(True, "6", "b"),
                                        _outcome(False, "", "c")])
        assert verdict == "answered" and chosen.value == "6"

    def test_disagreement_is_ambiguous(self):
        verdict, chosen, reason = SP.accept([_outcome(True, "True", "a"),
                                             _outcome(True, "False", "b")])
        assert verdict == "ambiguous" and chosen is None
        assert "disagree" in reason

    def test_order_does_not_matter(self):
        outcomes = [_outcome(True, "x", "a"), _outcome(False, "", "b"),
                    _outcome(True, "y", "c")]
        assert SP.accept(outcomes)[0] == SP.accept(outcomes[::-1])[0]

    def test_no_plan_falls_through_and_no_licence_refuses(self):
        assert SP.accept([])[0] == "fallthrough"
        assert SP.accept([_outcome(False, "")])[0] == "refused"

    def test_the_lean_file_states_the_rule(self):
        text = LEAN.read_text(encoding="utf-8")
        for name in ("accept_perm", "accept_eq_answered_iff",
                     "disagreement_is_ambiguous", "planned_conservative",
                     "planned_sound", "planned_refuses_only_on_disagreement",
                     "first_licensed_order_dependent",
                     "first_licensed_answers_a_disagreement"):
            assert f"theorem {name}" in text
        assert "sorry" not in text


class TestPlansOverTheSession:

    @pytest.mark.parametrize("question, fragment", [
        ("what is the atomic weight of carbon?", "12.011"),
        ("is 91 prime?", "not prime"),
        ("convert 3 metres to feet", "9.8425"),
        ("is energy more abstract than water?", "energy is more abstract"),
        ("what is the derivative of position?", "velocity"),
        ("which element has the largest atomic weight?", "og"),
    ])
    def test_a_question_reaches_its_operation(self, session, question,
                                              fragment):
        solution = SP.ask_planned(session, question)
        assert solution.ok
        assert fragment in solution.answer.lower()
        assert solution.expected["plan"]

    @pytest.mark.parametrize("question, reason", [
        ("what is 7 divided by 0?", "division by zero"),
        ("is 3/2 prime?", "integers"),
        ("convert 3 metres to kilograms", "different quantities"),
    ])
    def test_a_failed_precondition_is_named(self, session, question, reason):
        solution = SP.ask_planned(session, question)
        assert not solution.ok
        assert reason in (solution.error or "")

    def test_two_layers_that_disagree_are_refused(self, session):
        solution = SP.ask_planned(
            session, "does energy have the same dimensions as torque?")
        assert not solution.ok
        assert solution.payload["verdict"] == "ambiguous"

    def test_no_plan_is_the_grammar_exactly(self, session):
        text = "why is the sky blue?"
        assert SP.candidate_plans(text, SP.Grounder(session)) == ()
        bare, planned = session.ask(text), SP.ask_planned(session, text)
        assert (bare.ok, bare.answer) == (planned.ok, planned.answer)

    def test_the_session_method_is_the_planner(self, session):
        assert session.ask_planned("what is 7 times 8?").answer == \
            SP.ask_planned(session, "what is 7 times 8?").answer


class TestTheHeldOutSets:

    def test_the_declared_sizes(self):
        assert len(HO.PARAPHRASES) == 60
        assert len(HO.COMPOSITIONS) == 30
        assert len(HO.ADVERSARIAL) == 20
        assert len(HO.STRESS) == 47

    def test_keys_are_unique(self):
        keys = [q.key for s in HO.ALL_SETS.values() for q in s]
        assert len(keys) == len(set(keys))

    def test_scoring_rule(self):
        item = HO.HeldOut("k", "q", ("6",))
        assert HO.score_answer(item, True, "gcd = 6") == "correct"
        assert HO.score_answer(item, True, "gcd = 7") == "wrong"
        assert HO.score_answer(item, False, "") == "refused"
        refuse = HO.HeldOut("k", "q", None)
        assert HO.score_answer(refuse, True, "x") == "wrong"
        assert HO.score_answer(refuse, False, "") == "correct-refusal"


@pytest.fixture(scope="module")
def report():
    data = TP.current()
    if data is None:
        pytest.fail("the typed-plans cache is stale; run "
                    "`python3 -m glm_universal.tools plans --write`")
    return data


class TestTheMeasurement:

    def test_no_wrong_answer_on_the_adversarial_set(self, report):
        assert report["tallies"]["adversarial"]["planned"]["wrong"] == 0

    def test_no_wrong_answer_on_the_stress_set(self, report):
        assert report["tallies"]["stress"]["planned"]["wrong"] == 0

    def test_the_first_stress_run_is_frozen(self):
        assert dict(TP.STRESS_FIRST_RUN) == {
            "correct": 28, "wrong": 0, "refused": 13, "correct-refusal": 6}

    def test_the_probe_pass_mark_is_read_not_asserted(self, report):
        probe = report["frozen_probe"]
        mark = report["pass_mark"]
        assert report["probe_passed"] == (
            probe["correct"] >= mark["correct_at_least"]
            and probe["wrong"] <= mark["wrong_at_most"])

    def test_every_gain_is_classified(self, report):
        assert report["gained_total"] == sum(
            1 for row in report["rows"]
            if row["gained"] and row["verdict"] == "answered")
        assert set(report["gains"]) == {"table", "address", "derive"}
