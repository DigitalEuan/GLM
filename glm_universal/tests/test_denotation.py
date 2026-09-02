"""Tests for the denotation register and the second pass over the residue.

``test_measure_words.py`` pins the first pass: 27 of the lexicon's 66
``related_to`` triples convert from the physics register alone and 39 do not,
38 of them because an endpoint reaches no dimension.  That last sentence is a
statement about a *lookup*, and this round replaces it with a statement about
the *words*: ``data_objects/denotation.py`` decides, one name at a time and
with a written reason, what each of those endpoints denotes.

Four things could go wrong and each has a class:

* the register could invent a quantity, or shadow one it already has
  (``TestTheRegisterIsAudited``);
* it could decide names nobody asked about, or miss names the residue needs
  (``TestTheDecisionCoversTheResidue``);
* the second pass could *manufacture* relations -- naming a denotation is not
  a way of producing conversions -- or repair on a rule that is a guess
  (``TestWhatTheDecisionChanges``);
* the claim the round is here to earn could be quietly false
  (``TestTheClosure``), or unreachable from the runtime
  (``TestTheQuery``).
"""

from __future__ import annotations

import pytest

from glm_universal.data_objects import denotation as dn
from glm_universal.data_objects import physics as ph
from glm_universal.reasoning import denotation_view as dvw
from glm_universal.reasoning import measure_view as mvw
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


@pytest.fixture(scope="module")
def summary():
    return dn.register_summary()


@pytest.fixture(scope="module")
def passes():
    return dvw.second_pass()


class TestTheRegisterIsAudited:
    """A decision may reach the physics register; it may never extend it."""

    def test_the_audit_is_sound(self, summary):
        assert summary["audit"]["sound"] is True

    def test_the_shape_of_the_register(self, summary):
        assert summary["entries"] == 36
        assert summary["by_verdict"] == {
            "quantity": 1, "ambiguous": 3, "polymorphic": 4,
            "carrier": 9, "process": 11, "abstraction": 8}
        assert sum(summary["by_verdict"].values()) == summary["entries"]

    def test_only_one_name_is_dimensional(self, summary):
        assert summary["dimensional"] == {"gravity": "gravitational_field"}
        assert dn.denotes_quantity("gravity") == "gravitational_field"

    def test_a_dimensional_verdict_names_a_registered_quantity(self, summary,
                                                               subtests):
        for name, quantity in summary["dimensional"].items():
            with subtests.test(name=name):
                assert ph.quantity_by_name(quantity).name == quantity

    def test_no_decided_name_shadows_a_register_entry(self, subtests):
        """A denotation reaches the register; it never stands in front of it."""
        for name in dn.decided_names():
            with subtests.test(name=name):
                with pytest.raises(KeyError):
                    ph.quantity_by_name(name)

    def test_every_ambiguity_is_between_things_the_register_holds(
            self, summary, subtests):
        for name, candidates in summary["ambiguous"].items():
            with subtests.test(name=name):
                assert len(candidates) >= 2
                for candidate in candidates:
                    assert ph.quantity_by_name(candidate).name == candidate

    def test_no_verdict_but_quantity_reaches_a_dimension(self, subtests):
        for entry in dn.DENOTATIONS:
            with subtests.test(name=entry.name):
                reached = dn.denotes_quantity(entry.name)
                assert (reached is not None) is entry.dimensional

    def test_every_entry_carries_its_reason(self, subtests):
        for entry in dn.DENOTATIONS:
            with subtests.test(name=entry.name):
                assert len(entry.justification) >= 40
                assert entry.verdict in dn.VERDICTS


class TestTheDecisionCoversTheResidue:
    """Exactly the names the data asks about -- none missing, none idle."""

    def test_coverage_is_complete(self):
        cover = dvw.coverage()
        assert cover["undecided"] == ()
        assert cover["idle"] == ()
        assert cover["complete"] is True
        assert cover["needed"] == cover["decided"] == 36

    def test_every_decided_name_is_an_undimensioned_residue_endpoint(
            self, subtests):
        endpoints = set()
        for row in mvw.relation_repair()["residue_rows"]:
            endpoints.add(row["subject"])
            endpoints.add(row["object"])
        for name in dn.decided_names():
            with subtests.test(name=name):
                assert name in endpoints
                assert mvw._dimension_of(name) is None

    def test_the_decision_does_not_move_the_first_pass(self):
        """``relation_repair`` is untouched: 27 convert, 39 remain."""
        repair = mvw.relation_repair()
        assert repair["converted"] == 27
        assert repair["residue"] == 39


class TestWhatTheDecisionChanges:
    """Measured, not asserted -- and mostly it changes the reasons."""

    def test_the_second_pass_accounts_for_every_residue_triple(self, passes):
        assert passes["residue"] == 39
        assert (passes["converted"] + passes["decided"]
                + passes["declined"]) == 39

    def test_naming_a_denotation_manufactures_no_conversions(self, passes):
        """Deciding what a word denotes is not a way of making relations."""
        assert passes["converted"] == 0
        assert passes["conversions"] == ()

    def test_the_one_newly_dimensioned_name_still_declines(self, passes):
        """*gravity* reaches a dimension and its triple is still refused.

        ``gravity related_to mass`` joins ``entropy related_to temperature``:
        two genuine quantities that no single factor of the basis carries one
        to the other.  That is the honest outcome of the decision, and it is
        pinned so that a later change to the basis is visible here.
        """
        kinds = passes["declined_by_kind"]
        assert kinds["no_single_factor"] == 2
        declined = {(row["subject"], row["object"]): row
                    for row in passes["declined_rows"]}
        assert declined[("gravity", "mass")]["kind"] == "no_single_factor"

    def test_the_process_rule_is_the_only_repair(self, passes, subtests):
        assert dvw.DECIDED_RELATIONS == ("names_process_of",)
        assert passes["decided"] == 6
        for row in passes["decided_relations"]:
            with subtests.test(triple=(row["subject"], row["object"])):
                assert row["predicate"] == "names_process_of"
                assert dn.verdict_of(row["subject"]) == "process"
                assert dvw.dimension_of(row["object"]) is not None

    def test_the_repaired_processes_are_the_expected_ones(self, passes):
        repaired = {(row["subject"], row["object"])
                    for row in passes["decided_relations"]}
        assert repaired == {("attract", "force"), ("rotate", "angle"),
                            ("move", "velocity"), ("predict", "time"),
                            ("change", "time")}

    def test_a_carrier_beside_a_quantity_is_not_repaired(self, passes):
        """The rule that would be right half the time is not applied.

        ``magnetic_field related_to magnet`` and ``photon related_to light``
        have the same shape -- a carrier and a dimensioned endpoint -- and a
        magnet bears a flux density where a photon bears no illuminance.  Both
        are declined.
        """
        declined = {(row["subject"], row["object"])
                    for row in passes["declined_rows"]}
        assert ("magnetic_field", "magnet") in declined
        assert ("photon", "light") in declined

    def test_every_decline_names_what_its_endpoint_is(self, passes, subtests):
        for row in passes["declined_rows"]:
            with subtests.test(triple=(row["subject"], row["object"])):
                assert row["reason"]
                assert "undecided" not in row["kind"]
                assert "reaches no dimension" not in row["reason"]

    def test_the_declines_split_by_what_was_decided(self, passes):
        kinds = passes["declined_by_kind"]
        assert sum(kinds.values()) == passes["declined"] == 33
        assert kinds["ambiguous"] == 5
        assert kinds["polymorphic"] == 4


class TestTheClosure:
    """No triple is declined any longer for want of an entry."""

    def test_the_residue_is_decided(self):
        closed = dvw.closure()
        assert closed["decided"] is True
        assert closed["accounted"] == closed["residue"] == 39
        assert closed["undecided_endpoints"] == ()
        assert closed["lookup_failures"] == ()

    def test_the_report_is_its_parts(self):
        report = dvw.denotation_report()
        assert report["register"] == dn.register_summary()
        assert report["coverage"] == dvw.coverage()
        assert report["second_pass"] == dvw.second_pass()
        assert report["closure"] == dvw.closure()


class TestTheQuery:
    """The decision is reachable from the runtime, and it is checked there."""

    @pytest.mark.parametrize("subject", [
        "report denotations", "report denotation", "report residue",
        "report vocabulary",
    ])
    def test_the_subject_answers(self, sess, subject):
        solution = sess.ask(subject)
        assert solution.ok is True
        assert solution.payload["denotation"]["closure"]["decided"] in (
            True, "True")

    def test_the_report_states_the_decision(self, sess):
        solution = sess.ask("report measure")
        assert solution.expected["denotations"] == "36"
        assert solution.expected["denotation_closed"] == "True"
        assert solution.expected["denotation_complete"] == "True"
        assert solution.expected["denotation_converted"] == "0"
        assert solution.expected["denotation_decided"] == "6"
        assert solution.expected["denotation_declined"] == "33"
