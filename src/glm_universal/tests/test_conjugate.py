"""Tests for the energy-conjugate register and the transport that uses it.

``heat : temperature :: force : ?`` was the standing example of a question the
machine could not answer, and the reason had two halves: no relation the
registers state transports from ``force``, and the three terms share no
register that dimensions them.  ``data_objects/conjugate_pairs.py`` supplies a
register whose rows run across the domains, and ``reasoning/conjugate.py``
carries a relation along it under a rule it states.

Five things could go wrong, and each has a class:

* a row could be wrong -- an effort paired with something that is not its
  extent -- and the register would have no way of knowing
  (``TestTheRowsAreChecked``);
* a name could occupy two columns, which would make a relation
  many-valued and the answer a choice (``TestTheRolesAreUnique``);
* the transport could answer where it should decline, or decline where it
  should answer (``TestTheTransport``);
* the refusals could be vague rather than criterion-named
  (``TestTheRefusalsNameTheirCriterion``);
* and the whole thing could be unreachable from the runtime
  (``TestTheRuntime``).

The Lean development proves the properties this file measures:
``GLM.Conjugate.dimensionally_sound``, ``roles_unique_table``,
``rel_functional``/``rel_injective``, ``no_answer_of_unplaced`` and
``answer_heat_temperature_force``.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.data_objects import conjugate_pairs as cp
from glm_universal.data_objects import physics as ph
from glm_universal.reasoning import analogy_models as am
from glm_universal.reasoning import conjugate as cj
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def audit():
    return cp.conjugate_audit()


@pytest.fixture(scope="module")
def report():
    return cj.conjugate_report()


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


class TestTheRowsAreChecked:
    """The grounding criterion: a row is decided against the physics register."""

    def test_every_effort_and_extent_is_a_register_quantity(self, audit):
        assert audit["endpoints_in_register"]
        for row in cp.rows():
            ph.quantity_by_name(row.effort)
            ph.quantity_by_name(row.extent)

    def test_effort_times_extent_is_an_energy(self, subtests):
        energy = ph.quantity_by_name(cp.ENERGY_QUANTITY)
        for row in cp.rows():
            with subtests.test(domain=row.domain):
                effort = ph.quantity_by_name(row.effort)
                extent = ph.quantity_by_name(row.extent)
                assert tuple(x + y for x, y in zip(effort.exps_ext10,
                                                   extent.exps_ext10)) \
                    == energy.exps_ext10
                assert effort.scale + extent.scale == energy.scale

    def test_the_exponents_are_exact_rationals(self):
        for row in cp.rows():
            for name in (row.effort, row.extent):
                for exponent in ph.quantity_by_name(name).exps_ext10:
                    assert isinstance(exponent, Fraction)

    def test_a_wrong_pairing_would_be_caught(self):
        """Pressure with area, rather than with volume, fails the check."""
        energy = ph.quantity_by_name(cp.ENERGY_QUANTITY)
        pressure = ph.quantity_by_name("pressure")
        area = ph.quantity_by_name("area")
        assert tuple(x + y for x, y in zip(pressure.exps_ext10,
                                           area.exps_ext10)) \
            != energy.exps_ext10

    def test_every_row_carries_a_definition_and_a_justification(self):
        for row in cp.rows():
            assert row.definition
            assert len(row.justification) > 40

    def test_the_audit_says_the_table_is_sound(self, audit):
        assert audit["all_dimensional"]
        assert audit["sound"]


class TestTheRolesAreUnique:
    """The role and functional criteria: a name determines its column."""

    def test_no_name_occupies_two_columns(self, audit):
        assert audit["duplicated_names"] == ()
        assert audit["roles_unique"]

    def test_the_name_count_is_three_per_row(self, audit):
        assert audit["names"] == 3 * audit["row_count"]

    def test_two_names_never_stand_in_two_relations(self, audit):
        assert audit["pairs_in_two_relations"] == ()
        assert audit["relations_disjoint"]

    def test_role_of_agrees_with_the_table(self):
        for row in cp.rows():
            assert cp.role_of(row.effort) == "effort"
            assert cp.role_of(row.extent) == "extent"
            assert cp.role_of(row.transfer) == "transfer"
            assert cp.row_of_name(row.transfer) is row

    def test_a_name_the_register_does_not_hold_has_no_role(self):
        assert cp.role_of("justice") is None
        assert cp.row_of_name("justice") is None


class TestTheTransport:
    """What the register answers, and in which direction."""

    def test_the_headline_question(self):
        result = cj.transport("heat", "temperature", "force")
        assert result is not None
        assert result.answer == "work"
        assert result.relation == "effort_of"
        assert result.direction == "reverse"
        assert result.unique

    def test_the_forward_direction(self):
        result = cj.transport("temperature", "heat", "voltage")
        assert result is not None
        assert result.answer == "electrical_work"
        assert result.direction == "forward"

    def test_the_second_relation(self):
        result = cj.transport("temperature", "entropy", "force")
        assert result is not None
        assert result.relation == "conjugate_of"
        assert result.answer == "length"

    def test_the_model_declines_when_no_row_relates_a_and_b(self):
        """Declining is not refusing: another model may still recognise it."""
        assert cj.transport("length", "wavenumber", "time") is None
        assert cj.transport("hot", "cold", "fast") is None

    def test_the_answer_is_the_one_the_register_reaches(self, subtests):
        for a, b, c, expected, _failure in cj.REPORT_CASES:
            if not expected:
                continue
            with subtests.test(question=f"{a} : {b} :: {c}"):
                result = cj.transport(a, b, c)
                assert result is not None and result.answer == expected

    def test_every_report_case_comes_out_as_the_register_requires(self, report):
        assert report["cases_as_expected"] == report["cases_total"]
        assert report["answered"] + report["refused"] == report["cases_total"]


class TestTheRefusalsNameTheirCriterion:
    """A refusal is a fact about the register, with the criterion named."""

    def test_an_extent_cannot_enter_a_transfer_effort_relation(self):
        result = cj.transport("heat", "temperature", "entropy")
        assert result is not None
        assert result.answer is None
        assert result.failed == "role_typed"
        assert "extent column" in result.refusal

    def test_an_unknown_word_is_refused_at_the_same_criterion(self):
        result = cj.transport("heat", "temperature", "justice")
        assert result is not None
        assert result.answer is None
        assert result.failed == "role_typed"
        assert "occupies no column" in result.refusal

    def test_a_term_in_the_same_row_returns_an_operand_and_is_refused(self):
        result = cj.transport("heat", "temperature", "temperature")
        assert result is not None
        assert result.answer is None
        assert result.failed == "functional"

    def test_the_four_criteria_are_stated_with_their_checks(self):
        criteria = cj.admissibility()
        assert [c["criterion"] for c in criteria] == [
            "determinate", "role_typed", "functional", "grounded"]
        for criterion in criteria:
            assert criterion["statement"] and criterion["checked_by"]

    def test_related_to_fails_the_first_criterion_by_name(self):
        """The vague relation is excluded by name, in the analogy layer."""
        assert "related_to" in am.VAGUE_RELATIONS


class TestTheRuntime:
    """The register is reachable as a model and as a report subject."""

    def test_the_model_is_offered_by_the_layer(self):
        assert "conjugate_pair" in am.MODEL_NAMES
        assert am.conjugate_pair in am.MODELS_BY_DOMAIN["lexicon"]
        assert am.MODELS_BY_DOMAIN["lexicon"][0] is am.conjugate_pair

    def test_the_analogy_is_answered_end_to_end(self, sess):
        sol = sess.ask("heat : temperature :: force : ?")
        assert sol.ok
        assert sol.answer.endswith(": work")
        assert sol.payload["model"]["model"] == "conjugate_pair"

    def test_the_report_subject_answers(self, sess):
        sol = sess.ask("report conjugates")
        assert sol.ok
        assert "heat : temperature :: force : work" in sol.answer
        assert sol.expected["sound"] == "True"
        assert sol.expected["headline_answer"] == "work"

    def test_the_report_is_recomputed_rather_than_quoted(self, sess):
        """Two computations of the report agree, and neither is cached text."""
        first = cj.conjugate_report()
        second = cj.conjugate_report()
        assert first["cases"] == second["cases"]

    def test_the_answer_names_the_relation_in_its_steps(self, sess):
        sol = sess.ask("heat : temperature :: force : ?")
        text = " ".join(step.language for step in sol.steps)
        assert "effort_of" in text
        assert "bijection" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
