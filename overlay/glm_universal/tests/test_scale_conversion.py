"""Tests for the declared table of conversions between scales.

What is pinned here is the *mechanism* and the discipline, not the score.  A
conversion must be a declaration -- one row per scale, a positive factor, an
exact rational, a source written beside it -- and it must not change anything
the two operations underneath it already did: the ordering operation's seven
declared comparisons and the extremum operation's eight declared columns come
out exactly as they did before the table existed, which is the shipped form of
``GLM.ScaleConversion.orderWith_conservative``.  What it may do is turn a
refusal into an answer, and only where a row of the table says how.

The machine-checked counterparts are in
``RequestProject/GLM/ScaleConversion.lean``.  Directive D7 -- no float
anywhere -- is checked statically.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import column_extremum as CX
from glm_universal.reasoning import coordinate_order as CO
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import scale_conversion as SC
from glm_universal.runtime import parser as PA
from glm_universal.runtime.session import GeometricSession

LEAN = (Path(__file__).resolve().parents[3]
        / "RequestProject" / "GLM" / "ScaleConversion.lean")


@pytest.fixture(scope="module")
def session():
    return GeometricSession()


@pytest.fixture(scope="module")
def surface(session):
    return session.field_surface


@pytest.fixture(scope="module")
def report(session):
    return SC.conversion_report(session)


class TestTheDeclaredTable:

    def test_every_row_declares_a_quantity_the_table_knows(self, subtests):
        for row in SC.CONVERSIONS:
            with subtests.test(scale=row.scale):
                assert row.quantity in SC.CANONICAL
                assert row.unit == SC.CANONICAL[row.quantity]

    def test_every_factor_is_positive(self, subtests):
        """A factor at or below zero is a re-ordering, not a conversion:
        ``GLM.ScaleConversion.negative_factor_flips_the_verdict``."""
        for row in SC.CONVERSIONS:
            with subtests.test(scale=row.scale):
                assert row.factor > 0

    def test_every_number_is_exact(self, subtests):
        for row in SC.CONVERSIONS:
            with subtests.test(scale=row.scale):
                assert isinstance(row.factor, Fraction)
                assert isinstance(row.offset, Fraction)

    def test_each_scale_is_declared_once(self):
        scales = [row.scale for row in SC.CONVERSIONS]
        assert len(scales) == len(set(scales))

    def test_each_row_names_where_its_numbers_came_from(self, subtests):
        for row in SC.CONVERSIONS:
            with subtests.test(scale=row.scale):
                assert len(row.source) > 20

    def test_each_quantity_has_a_row_already_in_its_canonical_unit(
            self, subtests):
        for quantity in SC.QUANTITIES:
            with subtests.test(quantity=quantity):
                rows = [SC.declared(scale)
                        for scale in SC.scales_of_quantity(quantity)]
                assert any(row.is_identity for row in rows if row)

    def test_every_declared_scale_is_a_scale_the_surface_holds(self, surface):
        held = set(SC.numeric_scales(surface))
        assert {row.scale for row in SC.CONVERSIONS} <= held

    def test_the_electronvolt_factor_is_the_si_definition(self):
        """``N_A e`` in kJ/mol, from two constants that are exact by
        definition -- no measurement enters it."""
        assert SC.EV_PER_MOLE_IN_KJ == (
            Fraction(1602176634, 10 ** 28) * Fraction(602214076 * 10 ** 15)
            / 1000)
        assert abs(float(SC.EV_PER_MOLE_IN_KJ) - 96.485332) < 1e-5


class TestWhatTheTableRelates:

    def test_two_scales_of_one_quantity_are_related(self):
        assert SC.relates("element:atomic_weight_u", "molecule:molar_mass_u")

    def test_two_scales_of_two_quantities_are_not(self):
        assert not SC.relates("element:atomic_weight_u",
                              "element:melting_point_K")

    def test_a_scale_the_table_does_not_mention_is_not_related_to_anything(
            self):
        assert not SC.relates("lean:line", "python:line")
        assert SC.declared("lean:line") is None

    def test_bridging_an_undeclared_scale_says_so(self):
        with pytest.raises(SC.ConversionError) as caught:
            SC.bridge("lean:line", "python:line")
        assert caught.value.reason == "undeclared"

    def test_bridging_two_quantities_says_so(self):
        with pytest.raises(SC.ConversionError) as caught:
            SC.bridge("element:atomic_weight_u", "element:melting_point_K")
        assert caught.value.reason == "different-quantity"

    def test_a_conversion_is_applied_exactly(self):
        row = SC.declared("element:ionization_energy_eV")
        assert row is not None
        assert SC.apply(row, Fraction(1)) == SC.EV_PER_MOLE_IN_KJ
        assert isinstance(SC.apply(row, Fraction(13598, 1000)), Fraction)


class TestTheOrderingOperationWidened:

    def test_one_quantity_under_two_field_names_is_ordered(self, surface):
        result = CO.order(surface, "atomic_weight_u", "carbon", "water",
                          other_field="molar_mass_u")
        assert result.verdict == "lt"
        assert result.converted
        assert result.scale == "u"

    def test_the_answer_says_which_conversions_it_used(self, surface):
        result = CO.order(surface, "ionization_energy_eV", "hydrogen",
                          "hydrogen",
                          other_field="homonuclear_bde_kJ_per_mol")
        assert "declared conversion" in result.sentence
        assert result.scale == "kJ/mol"

    def test_the_gap_is_exact_and_in_the_unit_it_was_taken_in(self, surface):
        result = CO.order(surface, "ionization_energy_eV", "hydrogen",
                          "hydrogen",
                          other_field="homonuclear_bde_kJ_per_mol")
        left = SC.apply(SC.declared("element:ionization_energy_eV"),
                        result.left.value)
        right = SC.apply(SC.declared("element:homonuclear_bde_kJ_per_mol"),
                         result.right.value)
        assert result.difference == right - left
        assert isinstance(result.difference, Fraction)

    def test_two_scales_the_table_does_not_relate_are_still_refused(
            self, surface):
        with pytest.raises(CO.OrderingError) as caught:
            CO.order(surface, "line", "GLM.NormFamily.family_tower",
                     "rung_audit")
        assert caught.value.reason == "different-scale"

    def test_two_quantities_are_still_refused(self, surface):
        with pytest.raises(CO.OrderingError) as caught:
            CO.order(surface, "atomic_weight_u", "carbon", "iron",
                     other_field="melting_point_K")
        assert caught.value.reason == "different-scale"
        assert "measures mass" in str(caught.value)

    def test_a_comparison_on_one_scale_is_untouched(self, surface):
        result = CO.order(surface, "abstract_concrete", "energy", "water")
        assert not result.converted
        assert result.scale == "carrier:lexicon:primitives.abstract_concrete"
        assert result.verdict == "lt"

    def test_the_earlier_declared_set_is_unchanged(self, session):
        before = CO.comparison_report(session)
        assert before["as_declared"] == before["declared"]


class TestTheColumnWidened:

    def test_a_column_may_be_gathered_by_quantity(self, surface):
        found = CX.column(surface, "mass")
        assert found.rows == 169
        assert found.scale == "u"
        assert "element" in found.table and "molecule" in found.table

    def test_every_gathered_reading_keeps_where_it_came_from(self, surface):
        found = CX.column(surface, "mass")
        assert all(reading.origin for reading in found.readings)
        assert any("element:atomic_weight_u" in reading.origin
                   for reading in found.readings)
        assert any("molecule:molar_mass_u" in reading.origin
                   for reading in found.readings)

    def test_the_gathered_extremum_is_a_row_of_one_of_the_two_tables(
            self, surface):
        found = CX.extremum(surface, "mass")
        assert found.winners
        values = [r.value for r in CX.column(surface, "mass").readings]
        assert found.value == max(values)

    def test_a_quantity_with_a_hole_in_it_is_still_refused(self, surface):
        with pytest.raises(CX.ExtremumError) as caught:
            CX.extremum(surface, "temperature")
        assert caught.value.reason == "incomplete"

    def test_a_column_of_two_undeclared_scales_is_still_refused(self, surface):
        with pytest.raises(CX.ExtremumError) as caught:
            CX.extremum(surface, "line")
        assert caught.value.reason == "mixed-scale"

    def test_naming_a_table_asks_for_that_table_alone(self, surface):
        found = CX.column(surface, "atomic_weight_u", "element")
        assert found.rows == 118
        assert found.scale == "element:atomic_weight_u"

    def test_the_earlier_declared_set_is_unchanged(self, session):
        after = CX.extremum_report(session)
        assert after["as_declared"] == after["declared"]


class TestTheQueryKind:

    def test_the_second_side_may_name_its_own_coordinate(self):
        query = PA.parse_query("order atomic_weight_u of carbon and "
                         "molar_mass_u of water")
        assert query.kind == "ordering"
        assert query.options["name"] == "atomic_weight_u"
        assert query.options["left"] == "carbon"
        assert query.options["right_name"] == "molar_mass_u"
        assert query.options["right"] == "water"

    def test_the_one_coordinate_shape_is_unchanged(self):
        query = PA.parse_query("order abstract_concrete of energy and water")
        assert query.options["name"] == "abstract_concrete"
        assert query.options["left"] == "energy"
        assert query.options["right"] == "water"
        assert "right_name" not in query.options

    def test_the_solver_answers_across_two_field_names(self, session):
        solution = session.ask("order atomic_weight_u of carbon and "
                               "molar_mass_u of water")
        assert solution.ok
        assert solution.expected["verdict"] == "lt"
        assert solution.payload["converted"] is True

    def test_the_solver_gathers_a_column_by_quantity(self, session):
        solution = session.ask("largest mass")
        assert solution.ok
        assert solution.expected["scale"] == "u"

    def test_the_script_recomputes_a_converted_answer(self, session):
        from glm_universal.runtime import tct_engine as tct
        solution = session.ask("order atomic_weight_u of carbon and "
                               "molar_mass_u of water")
        script = tct.render_script(solution)
        assert "scale_conversion" in script
        assert "other_field='molar_mass_u'" in script


class TestTheMeasurement:

    def test_every_declared_question_came_out_as_declared(self, report,
                                                          subtests):
        for row in report["rows"]:
            with subtests.test(key=row["key"]):
                assert row["as_declared"], row["detail"]

    def test_the_declared_set_covers_both_halves(self, report):
        assert report["answered"] + report["refused"] == report["declared"]
        assert report["answered"] >= 1 and report["refused"] >= 1

    def test_the_census_counts_the_pairs_it_reaches(self, report):
        census = report["census"]
        assert census["bridged"] + census["refused"] == census["pairs"]
        assert census["bridged"] == sum(
            len(SC.scales_of_quantity(q)) * (len(SC.scales_of_quantity(q)) - 1)
            // 2 for q in SC.QUANTITIES)

    def test_the_census_is_a_small_part_of_the_surface(self, report):
        """The table reaches what someone declared and nothing else."""
        census = report["census"]
        assert census["bridged"] < census["refused"]

    def test_the_two_operations_underneath_are_unchanged(self, report):
        assert report["ordering_as_declared"] == report["ordering_declared"]
        assert report["extremum_as_declared"] == report["extremum_declared"]

    def test_the_verdict_is_stated_with_its_caveat(self, report):
        assert str(report["declared_rows"]) in report["verdict"]
        assert "declaration and not a derivation" in report["caveat"]
        assert "parses English" in report["caveat"]

    def test_the_declared_set_is_written_down_before_it_is_run(self):
        keys = [row[0] for row in SC.DECLARED_BRIDGES]
        assert len(keys) == len(set(keys))
        for _key, kind, operands, expected in SC.DECLARED_BRIDGES:
            assert kind in ("order", "column")
            assert operands[0]
            assert expected in (
                "lt", "gt", "eq", "answer",
                *CO.REFUSAL_REASONS, *CX.REFUSAL_REASONS)


class TestTheProvedHalf:

    def test_the_lean_file_states_what_the_module_cites(self, subtests):
        text = LEAN.read_text(encoding="utf-8")
        for name in ("apply_lt_iff", "cmpQ_apply", "order_conversion_invariant",
                     "orderWith_nil", "orderWith_conservative",
                     "orderWith_eq_none_iff", "orderWith_across_scales",
                     "verdict_independent_of_target_scale",
                     "negative_factor_flips_the_verdict",
                     "the_table_carries_the_claim",
                     "extremum_convert_invariant",
                     "gathered_winner_is_a_row_of_one_of_the_two_columns",
                     "raw_gather_names_the_wrong_row"):
            with subtests.test(name=name):
                assert f"theorem {name}" in text
        assert "sorry" not in text

    def test_the_proved_side_condition_is_the_shipped_one(self):
        """Lean requires the factor positive; the table declares it so."""
        text = LEAN.read_text(encoding="utf-8")
        assert "0 < c.factor" in text
        assert all(row.factor > 0 for row in SC.CONVERSIONS)


class TestExactness:

    def test_no_float_is_constructed(self):
        assert ex.module_float_sites(Path(SC.__file__)) == {}
