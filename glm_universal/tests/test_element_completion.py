"""Tests for the completed element view: every empty cell decided.

``element_coverage`` measures the register's sparsity -- 1,257 of 1,652 cells
carry a measurement -- and widens it without writing anything back.
``element_completion`` decides the rest: each of the 395 empty cells receives
exactly one of four dispositions, and the cells a rule fills are filled only
by rules that beat the field's own mean out of sample.

Five things could go wrong, and each has a class:

* a rule could be admitted on a score that means nothing
  (``TestTheGate``);
* an estimate could overwrite a measurement, or the measured layer could stop
  being the register (``TestTheRegisterIsNotDisturbed``);
* a cell could be left undecided, which is the failure the round exists to
  close (``TestEveryEmptyCellIsDecided``);
* the scores could be inexact, or the search could depend on the order it ran
  in (``TestExactAndDeterministic``);
* and the whole thing could be unreachable from the runtime
  (``TestTheRuntime``).

The Lean development proves what this file measures:
``GLM.Completion.cell_measured_iff``, ``readMeasured_eq_base``,
``estimated_of_empty``, ``coverage_monotone``, ``dispositions_exhaustive``
and ``admitted_halves_the_baseline``.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.data_objects import elements as el
from glm_universal.reasoning import element_completion as ecp
from glm_universal.reasoning import element_coverage as eco
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def report():
    return ecp.element_completion_report()


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


class TestTheGate:
    """A rule is admitted only for beating the field's own mean by a factor of two."""

    def test_the_gate_is_stated_once_and_is_not_per_field(self):
        assert ecp.GATE_SKILL == Fraction(1, 2)
        assert ecp.GATE_MINIMUM == 20

    def test_every_admitted_rule_passes_the_gate(self, subtests):
        for field, rule in ecp.admitted_rules().items():
            with subtests.test(field=field):
                assert rule.skill is not None
                assert rule.skill <= ecp.GATE_SKILL
                assert rule.scored_on >= ecp.GATE_MINIMUM
                assert 2 * rule.loo_error <= rule.baseline_error

    def test_a_field_whose_best_rule_fails_the_gate_takes_no_rule(self):
        """Homonuclear bond energy is the case: the best rule is not good enough."""
        best = ecp.rules_for_field("homonuclear_bde_kJ_per_mol")
        assert best
        assert best[0].skill > ecp.GATE_SKILL
        assert "homonuclear_bde_kJ_per_mol" not in ecp.admitted_rules()

    def test_no_rule_is_sought_for_a_field_that_is_not_derivable(self):
        assert "year_discovered" in ecp.NOT_DERIVABLE
        assert ecp.rules_for_field("year_discovered") == ()

    def test_no_rule_is_sought_for_a_field_with_no_empty_cell(self):
        gaps = ecp.empty_cells_by_field()
        for field, missing in gaps.items():
            if missing == 0:
                assert ecp.rules_for_field(field) == ()

    def test_the_scores_are_out_of_sample(self):
        """The reported error is a leave-one-out error, not an in-sample one.

        Refitting on everything and scoring on everything can only do better,
        so the leave-one-out error must be at least the in-sample one -- and
        for a real fit it is strictly larger.
        """
        rule = ecp.linear_rule("covalent_radius_pm", "atomic_radius_pm")
        assert rule is not None
        in_sample = eco.covalent_radius_model()
        assert rule.loo_error > in_sample["mean_absolute_residual_pm"]


class TestTheRegisterIsNotDisturbed:
    """The safety property, and the reason the completed view may be read at all."""

    def test_the_measured_layer_is_the_register(self, report):
        assert report["safety"]["holds"]
        assert report["safety"]["mismatched"] == ()

    def test_no_estimate_occupies_a_measured_cell(self, report):
        assert report["safety"]["overwritten"] == ()

    def test_reading_measurements_returns_exactly_the_register(self):
        elements = {e.symbol: e for e in el.load_element_register()}
        for cell in ecp.completed_table():
            registered = getattr(elements[cell.symbol], cell.field, None)
            if cell.provenance == "measured":
                assert cell.value == Fraction(registered)
            else:
                assert registered is None

    def test_estimate_declines_on_a_cell_the_register_fills(self):
        assert ecp.estimate("C", "atomic_radius_pm") is None

    def test_the_measured_count_is_the_coverage_table_s(self, report):
        assert report["coverage"]["measured"] == \
            eco.coverage_table()["filled_cells"]

    def test_coverage_only_rises(self, report):
        cover = report["coverage"]
        assert cover["filled"] >= cover["measured"]
        assert cover["filled"] == cover["measured"] + cover["estimated"]
        assert cover["filled"] + cover["empty"] == cover["total_cells"]


class TestEveryEmptyCellIsDecided:
    """The claim the round is here to earn."""

    def test_every_empty_cell_carries_a_disposition(self, report):
        ledger = report["dispositions"]
        assert ledger["accounted"]
        assert ledger["undecided"] == ()
        assert sum(ledger["counts"].values()) == ledger["empty_cells"]

    def test_the_dispositions_are_the_four_named_ones(self, report):
        assert set(report["dispositions"]["counts"]) <= set(ecp.DISPOSITIONS)

    def test_every_undecided_cell_carries_a_reason(self, report):
        assert report["dispositions"]["unexplained"] == ()
        for cell in ecp.completed_table():
            if cell.provenance == "":
                assert cell.basis

    def test_the_empty_cells_are_the_register_s_empty_cells(self, report):
        coverage = eco.coverage_table()
        assert report["dispositions"]["empty_cells"] == \
            coverage["total_cells"] - coverage["filled_cells"]

    def test_a_cell_is_never_both_filled_and_disposed(self):
        for cell in ecp.completed_table():
            assert bool(cell.provenance) != bool(cell.disposition)


class TestExactAndDeterministic:
    """Exact rational arithmetic, and an answer that does not depend on the run."""

    def test_every_value_is_a_fraction(self):
        for cell in ecp.completed_table():
            assert cell.value is None or isinstance(cell.value, Fraction)

    def test_the_rounded_scores_are_rationals_over_a_thousand(self):
        for rule in ecp.admitted_rules().values():
            rounded = ecp.round_to_thousandths(rule.skill)
            assert isinstance(rounded, Fraction)
            assert 1000 % rounded.denominator == 0

    def test_two_computations_agree(self):
        first = ecp.rule_table()
        second = ecp.rule_table()
        assert first == second

    def test_the_rules_are_ordered_by_skill(self):
        for field in ecp.FIELDS:
            rules = ecp.rules_for_field(field)
            skills = [r.skill for r in rules]
            assert skills == sorted(skills)


class TestTheRuntime:
    """The completed view is reachable, and says what it did."""

    def test_the_report_subject_answers(self, sess):
        sol = sess.ask("report completion")
        assert sol.ok
        assert sol.expected["accounted"] == "True"
        assert sol.expected["safety"] == "True"
        assert int(sol.expected["filled"]) > int(sol.expected["measured"])

    def test_the_answer_states_the_register_is_unchanged(self, sess):
        sol = sess.ask("report completion")
        assert "register itself unchanged" in sol.answer

    def test_the_subject_is_listed(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        assert "completion" in REPORT_SUBJECTS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
