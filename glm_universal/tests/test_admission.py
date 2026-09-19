"""Tests for the door a new name comes in by.

"Open vocabulary" stood for several rounds as a *commitment* rather than a
mechanism: the vocabulary is exactly the registers, there is no coordinate for
*justice*, and the semantics layer refuses rather than inventing one.  The
commitment is right and it was never the whole story -- what was missing is
how a name gets **in**, as a criterion someone could check.

``reasoning/admission.py`` states the criterion and the routes.  The things
that could go wrong with such a door each have a class here:

* it could admit a name without coordinates, or refuse one and give it
  coordinates anyway (``TestTheCriterion``);
* a route could steal a name from an earlier one, or leave a name with no
  route at all (``TestTheRoutesAreTriedInOrder``);
* an admitted name could be quietly written into a register, which would make
  the vocabulary grow behind the reader's back (``TestNothingIsWrittenBack``);
* a refusal could be a refusal of a *kind* of word rather than a conditional
  one that names its condition (``TestWhatARefusalIsARefusalOf``);
* the coordinates could disagree with the register they claim to come from
  (``TestTheCoordinatesAreTheRegisters``);
* and the whole thing could be unreachable from the runtime
  (``TestTheRuntime``).
"""

from __future__ import annotations

import pytest

from glm_universal.data_objects import physics as ph
from glm_universal.reasoning import admission as adm
from glm_universal.reasoning import term_arithmetic as ta
from glm_universal.reasoning import units as un
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def report():
    return adm.admission_report()


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


class TestTheCriterion:
    """Stated, reproducible, grounded -- and the third is the one that refuses."""

    def test_the_criterion_has_three_clauses(self, report):
        assert [row["clause"] for row in report["criteria"]] == \
            ["stated", "reproducible", "grounded"]
        for row in report["criteria"]:
            assert row["says"]

    def test_every_probe_is_routed_exactly_once(self, report):
        audit = report["audit"]
        assert audit["every_probe_routed"] is True
        assert sum(audit["counts"].values()) == audit["probes"] == \
            len(adm.PROBES)

    def test_an_admitted_probe_has_coordinates_or_a_register_without_them(
            self, report):
        for row in report["audit"]["rows"]:
            if row.admitted:
                assert row.source
                # A register that does not dimension its carriers (an element,
                # a chord, a word) admits by ``held`` without coordinates;
                # the two computing routes always produce them.
                if row.route in ("unit", "arithmetic"):
                    assert row.coordinates is not None
                    assert len(row.coordinates) == 10

    def test_no_refused_probe_is_given_coordinates(self, report):
        assert report["audit"]["no_coordinates_without_a_register"] is True
        for row in report["audit"]["rows"]:
            if not row.admitted:
                assert row.coordinates is None
                assert row.source == ""

    def test_every_decision_carries_its_reason(self, report):
        for row in report["audit"]["rows"]:
            assert row.reason
            assert row.name in row.reason

    def test_asking_twice_gives_the_same_answer(self, report):
        assert report["audit"]["determinate"] is True
        first = adm.admit("kg*m/s^2")
        second = adm.admit("kg*m/s^2")
        assert first.route == second.route
        assert first.coordinates == second.coordinates

    def test_the_audit_holds(self, report):
        assert report["audit"]["holds"] is True

    def test_the_measured_split(self, report):
        assert report["audit"]["counts"] == \
            {"held": 11, "unit": 5, "arithmetic": 4, "refused": 7}
        assert report["audit"]["admitted"] == 20
        assert report["audit"]["refused"] == 7


class TestTheRoutesAreTriedInOrder:
    """Four routes, tried in a fixed order, of which only the last refuses."""

    def test_the_order_is_the_stated_one(self):
        assert adm.ROUTES == ("held", "unit", "arithmetic", "refused")

    def test_a_held_name_is_not_stolen_by_a_computing_route(self):
        # ``J`` is not a carrier, but ``energy`` is: the held route takes it
        # even though the arithmetic route would also reach it.
        assert adm.admit("energy").route == "held"
        assert adm.admit("energy").source == "physics"

    def test_the_unit_route_comes_before_the_arithmetic_one(self):
        assert adm.admit("J").route == "unit"
        assert adm.admit("N*m").route == "unit"

    def test_the_arithmetic_route_reaches_what_neither_of_the_others_does(self):
        row = adm.admit("energy divided by time")
        assert row.route == "arithmetic"
        assert row.source == "term_arithmetic"
        assert "energy divided by time" not in adm.vocabulary()

    def test_a_name_no_route_reaches_is_refused_rather_than_crashing(self):
        for name in adm.UNGROUNDED:
            assert adm.admit(name).route == "refused"

    def test_the_vocabulary_is_the_nine_registers(self):
        held = adm.vocabulary()
        assert len(held) == 1147
        assert set(held.values()) == {
            "physics", "chemistry", "molecules", "mathematics", "harmonics",
            "economics", "comparison", "lexicon", "semantic_lexicon",
            "conjugate_pairs"}

    def test_a_name_in_two_registers_is_reported_under_the_first(self):
        # The order is part of the door, so the answer does not depend on
        # dictionary iteration.
        assert adm.vocabulary()["temperature"] == "physics"


class TestNothingIsWrittenBack:
    """Admitting a name widens what can be asked, not what is stored."""

    def test_the_registers_are_unchanged_by_admission(self, report):
        assert report["audit"]["registers_unchanged"] is True

    def test_the_names_admitted_by_computation_are_still_not_carriers(
            self, report):
        widened = report["audit"]["widened_by"]
        assert widened
        held = adm.vocabulary()
        for name in widened:
            assert name not in held

    def test_the_vocabulary_size_does_not_move(self):
        before = len(adm.vocabulary())
        adm.admit("mol/L")
        adm.admit("force times length")
        assert len(adm.vocabulary()) == before


class TestWhatARefusalIsARefusalOf:
    """A refusal names its condition, and two refusals are of different shapes."""

    def test_justice_is_refused_conditionally(self, report):
        justice = report["justice"]
        assert justice["route"] == "refused"
        assert "conditional" in justice["reason"]
        assert "the moment a register that measures it is admitted" in \
            justice["reason"]

    def test_the_refusal_is_not_of_a_kind_of_word(self, report):
        # The claim being made is "there is no coordinate for justice", not
        # "justice is not the kind of thing that has coordinates".
        assert "the door needs no change for that" in \
            report["justice"]["reason"]

    def test_a_unit_gap_is_reported_as_a_gap_in_the_register(self, report):
        assert report["unit_gaps"] == ("km/h",)
        row = next(r for r in report["audit"]["rows"] if r.name == "km/h")
        assert "unknown unit symbol 'h'" in row.reason
        assert "gap in the register and not in the door" in row.reason

    def test_an_ungrounded_word_is_not_reported_as_a_missing_unit_symbol(self):
        # Without the near-miss clause every unknown word would be reported
        # as a missing unit symbol, which would be noise rather than a
        # finding.
        for name in adm.UNGROUNDED:
            assert "unknown unit symbol" not in adm.admit(name).reason

    def test_the_two_shapes_of_refusal_partition_the_refusals(self, report):
        assert set(report["unit_gaps"]) | set(report["ungrounded_refused"]) \
            == set(report["refusals"])
        assert set(report["unit_gaps"]) & set(report["ungrounded_refused"]) \
            == set()

    def test_admitting_the_missing_symbol_would_admit_the_name(self):
        # The claim in the km/h reason is checkable: the same expression over
        # a symbol the register does hold parses.
        assert adm.admit("km/s").route == "unit"

    def test_the_limits_say_what_the_door_does_not_widen(self, report):
        assert "measurable" in report["limits"]


class TestTheCoordinatesAreTheRegisters:
    """Grounded means the numbers come out of a register, not out of the door."""

    def test_a_unit_admission_agrees_with_the_unit_register(self):
        assert adm.admit("J").coordinates == tuple(un.parse_unit("J"))

    def test_a_unit_admission_agrees_with_the_physics_register(self):
        assert adm.admit("J").coordinates == \
            tuple(ph.quantity_by_name("energy").exps_ext10)

    def test_an_arithmetic_admission_agrees_with_term_arithmetic(self):
        name = "energy divided by time"
        assert adm.admit(name).coordinates == tuple(ta.evaluate(name).sense.exps)

    def test_an_arithmetic_admission_lands_on_the_register_quantity(self):
        assert adm.admit("energy divided by time").coordinates == \
            tuple(ph.quantity_by_name("power").exps_ext10)

    def test_a_held_physics_name_carries_its_own_exponents(self):
        assert adm.admit("torque").coordinates == \
            tuple(ph.quantity_by_name("torque").exps_ext10)

    def test_no_float_is_constructed(self, report):
        from fractions import Fraction
        for row in report["audit"]["rows"]:
            if row.coordinates is not None:
                for value in row.coordinates:
                    assert isinstance(value, Fraction)


class TestTheRuntime:
    """The subject is reachable, and its script recomputes what it reported."""

    def test_the_subject_answers(self, sess):
        sol = sess.ask("report admission")
        assert sol.kind == "report"
        assert sol.ok
        assert "admissible" in sol.answer

    def test_the_subject_has_aliases(self, sess):
        for phrasing in ("report open vocabulary", "report door",
                         "report admissible"):
            assert sess.ask(phrasing).kind == "report"
            assert sess.ask(phrasing).ok

    def test_the_answer_carries_the_counts(self, sess, report):
        sol = sess.ask("report admission")
        audit = report["audit"]
        assert str(audit["admitted"]) in sol.answer
        assert str(audit["probes"]) in sol.answer
        assert str(audit["vocabulary_size"]) in sol.answer

    def test_the_report_has_two_columns_for_every_step(self, sess):
        sol = sess.ask("report admission")
        assert len(sol.steps) == 4
        for step in sol.steps:
            assert step.language and step.mathematics

    def test_the_script_recomputes_the_report(self, sess):
        sol = sess.ask("report admission")
        assert sol.script_spec["template"] == "report_admission"
        assert set(sol.expected) == {
            "probes", "counts", "admitted", "refused", "vocabulary_size",
            "every_probe_routed", "determinate", "registers_unchanged",
            "holds", "unit_gaps"}
        exact, offenders = tct.script_is_exact(tct.render_script(sol))
        assert exact, offenders

    def test_the_subject_is_listed(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        assert "admission" in REPORT_SUBJECTS
