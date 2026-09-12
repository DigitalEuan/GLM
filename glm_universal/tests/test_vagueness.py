"""Tests for the standing rule that decides a vague ``related_to`` triple.

Two earlier rounds took the 66 vague triples the lexicon holds down to nothing
waiting on a lookup: ``measure_view.relation_repair`` converts the ones the
physics register decides, and ``data_objects/denotation.py`` decides the rest
*by hand*.  What stayed open was the next triple -- every addition brought the
hand work back.

``reasoning/vagueness.py`` is the rule that replaces it, and the things that
could go wrong with such a rule each have a class here:

* the routes could overlap or leave a triple undecided
  (``TestEveryTripleIsRoutedExactlyOnce``);
* a proposer rule could be admitted on a majority rather than on agreement,
  which would let a wrong verdict in (``TestTheProposerGate``);
* the conjugate route could invent a relation between two names that are
  placed in different rows (``TestTheConjugateRoute``);
* a referral could be a bare failure rather than a decision to ask
  (``TestAReferralCarriesItsEvidence``);
* and the whole thing could be unreachable from the runtime
  (``TestTheRuntime``).
"""

from __future__ import annotations

import pytest

from glm_universal.data_objects import conjugate_pairs as cp
from glm_universal.data_objects import denotation as dn
from glm_universal.reasoning import vagueness as vgn
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def report():
    return vgn.vagueness_report()


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


class TestEveryTripleIsRoutedExactlyOnce:
    """The routing is total and its counts add up."""

    def test_the_triples_are_the_lexicon_s_own(self):
        triples = vgn.related_to_triples()
        assert len(triples) == 66
        assert len(set(triples)) == len(triples)

    def test_every_triple_gets_a_route(self, report):
        routing = report["routing"]
        assert routing["every_triple_routed"] is True
        assert len(routing["rows"]) == routing["triples"] == 66

    def test_every_route_named_is_one_of_the_four(self, report):
        for row in report["routing"]["rows"]:
            assert row["route"] in vgn.ROUTES

    def test_the_counts_partition_the_triples(self, report):
        counts = report["routing"]["counts"]
        assert sum(counts.values()) == 66
        assert counts["dimensional"] + counts["conjugate"] + \
            counts["proposed"] == report["routing"]["decided_without_a_person"]
        assert counts["referred"] == report["routing"]["referred"]

    def test_the_measured_split(self, report):
        counts = report["routing"]["counts"]
        assert counts == {"dimensional": 27, "conjugate": 1,
                          "proposed": 6, "referred": 32}

    def test_most_of_the_hand_work_is_still_needed_and_that_is_stated(
            self, report):
        # The rule is honest about not deciding everything.
        assert report["routing"]["referred"] > 0
        assert "referred" in report["limits"]

    def test_the_routes_are_tried_in_the_stated_order(self):
        assert vgn.ROUTES == ("dimensional", "conjugate", "proposed",
                              "referred")

    def test_a_dimensional_pair_is_not_stolen_by_a_later_route(self):
        # heat/temperature is decided dimensionally even though the conjugate
        # register also places both endpoints.
        row = vgn.route_of("heat", "temperature")
        assert row["route"] == "dimensional"


class TestTheProposerGate:
    """A rule is admitted for agreeing with every hand decision it fires on."""

    def test_four_rules_are_tried(self, report):
        assert report["proposer"]["rules_tried"] == 4
        assert len(vgn.PROPOSER_RULES) == 4

    def test_one_rule_is_admitted(self, report):
        assert report["proposer"]["admitted"] == ("verb_is_a_process",)

    def test_an_admitted_rule_has_no_disagreement(self, report):
        for row in report["proposer"]["rules"]:
            if row["admitted"]:
                assert row["disagreements"] == ()
                assert row["agreed"] == row["fired_on"]

    def test_an_admitted_rule_fired_often_enough(self, report):
        for row in report["proposer"]["rules"]:
            if row["admitted"]:
                assert row["fired_on"] >= vgn.PROPOSER_MINIMUM

    def test_every_refused_rule_names_a_disagreement_or_is_untested(
            self, report):
        for row in report["proposer"]["rules"]:
            if not row["admitted"]:
                assert row["disagreements"] or \
                    row["fired_on"] < vgn.PROPOSER_MINIMUM

    def test_the_refusals_are_the_measured_ones(self, report):
        refused = {row["rule"]: row for row in report["proposer"]["rules"]
                   if not row["admitted"]}
        assert set(refused) == {"nominalisation_of_a_verb",
                                "abstract_noun_is_an_abstraction",
                                "mass_noun_is_a_carrier"}

    def test_a_majority_would_not_have_been_enough(self, report):
        # mass_noun_is_a_carrier agrees on 5 of 7 -- a clear majority, and
        # still refused.  This is the gate doing work rather than describing
        # an outcome it would have reached anyway.
        row = next(r for r in report["proposer"]["rules"]
                   if r["rule"] == "mass_noun_is_a_carrier")
        assert row["agreed"] * 2 > row["fired_on"]
        assert row["admitted"] is False

    def test_the_admitted_rule_never_contradicts_the_hand_register(self):
        for entry in dn.DENOTATIONS:
            proposal = vgn.propose(entry.name)
            if proposal is not None:
                assert proposal.verdict == entry.verdict

    def test_the_proposer_abstains_rather_than_guessing(self):
        assert vgn.propose("a-name-the-lexicon-does-not-hold") is None

    def test_the_proposer_decides_some_of_the_hand_work(self, report):
        proposer = report["proposer"]
        assert proposer["decided_by_rule"] == 10
        assert proposer["decided_by_rule"] + proposer["still_by_hand"] == \
            proposer["decided_names"]

    def test_every_proposal_carries_its_evidence(self):
        for entry in dn.DENOTATIONS:
            proposal = vgn.propose(entry.name)
            if proposal is not None:
                assert proposal.evidence
                assert proposal.rule in \
                    {rule.name for rule in vgn.PROPOSER_RULES}


class TestTheConjugateRoute:
    """The register converts within a row, and declines across rows."""

    def test_some_triples_are_converted(self, report):
        conj = report["conjugate"]
        assert conj["converted_count"] == 4
        assert conj["converted_only_here_count"] == 1

    def test_a_converted_relation_is_one_the_register_states(self, report):
        for row in report["conjugate"]["converted"]:
            assert row["relation"] in cp.RELATIONS

    def test_both_endpoints_of_a_conversion_lie_in_one_row(self, report):
        for row in report["conjugate"]["converted"]:
            left = cp.row_of_name(row["subject"])
            right = cp.row_of_name(row["object"])
            assert left is not None and right is not None
            assert left.domain == right.domain

    def test_names_placed_in_different_rows_are_not_converted(self, report):
        apart = report["conjugate"]["placed_in_different_rows"]
        assert len(apart) == 2
        for row in apart:
            assert cp.related(row["subject"], row["object"]) == ()
            assert row["reason"]

    def test_the_conversions_agree_with_the_dimensional_route(self, report):
        conj = report["conjugate"]
        assert conj["agreeing_with_the_dimensional_route"] == \
            conj["converted_count"] - conj["converted_only_here_count"]
        for row in conj["converted"]:
            if row["also_dimensional"]:
                # Both routes fire; neither is contradicted, the conjugate
                # one merely names the factor's role.
                assert row["relation"]

    def test_the_counts_are_consistent(self, report):
        conj = report["conjugate"]
        assert conj["converted_count"] + \
            conj["placed_in_different_rows_count"] + \
            conj["unplaced_count"] == conj["triples"] == 66


class TestAReferralCarriesItsEvidence:
    """A referral is a decision to ask, not a lookup that failed."""

    def test_every_referral_has_evidence(self, report):
        for row in report["routing"]["rows"]:
            if row["route"] == "referred":
                assert row["evidence"]
                assert row["relation"] == ""

    def test_the_evidence_says_what_each_endpoint_is(self, report):
        for row in report["routing"]["rows"]:
            if row["route"] == "referred":
                assert "conjugate register" in row["evidence"]
                assert "decided by hand already" in row["evidence"]

    def test_every_decided_route_names_a_relation(self, report):
        for row in report["routing"]["rows"]:
            if row["route"] != "referred":
                assert row["relation"]
                assert row["evidence"]


class TestTheRuntime:
    """The subject is reachable, and its script recomputes what it reported."""

    def test_the_subject_answers(self, sess):
        sol = sess.ask("report vagueness")
        assert sol.kind == "report"
        assert "related_to" in sol.answer

    def test_the_subject_has_aliases(self, sess):
        for phrasing in ("report vague", "report standing rule",
                         "report proposer"):
            assert sess.ask(phrasing).kind == "report"

    def test_the_answer_carries_the_counts(self, sess, report):
        sol = sess.ask("report vagueness")
        routing = report["routing"]
        assert str(routing["decided_without_a_person"]) in sol.answer
        assert str(routing["triples"]) in sol.answer

    def test_the_report_has_two_columns_for_every_step(self, sess):
        sol = sess.ask("report vagueness")
        assert len(sol.steps) == 4
        for step in sol.steps:
            assert step.language and step.mathematics

    def test_the_script_recomputes_the_report(self, sess):
        sol = sess.ask("report vagueness")
        assert sol.script_spec["template"] == "report_vagueness"
        assert set(sol.expected) == {
            "triples", "counts", "decided_without_a_person", "referred",
            "every_triple_routed", "rules_tried", "rules_admitted",
            "conjugate_converted"}
