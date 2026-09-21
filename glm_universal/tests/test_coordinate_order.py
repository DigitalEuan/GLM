"""Tests for the ordering operation: two readings of one coordinate, ordered
or refused.

What is pinned here is the *mechanism*, not the score.  The operation must
read a coordinate off a row only where the row itself holds it, carry the
scale it was read on, order two readings exactly when -- and only when -- they
share that scale, refuse at three named boundaries, and name a pole only where
the register declares one.  The measurement's numbers are deliberately not
asserted: what is asserted is that every declared comparison came out as it
was declared before the run, that the frozen oracle table is left alone, and
that no probe question outside the one this round was about changes class.

The machine-checked counterparts are in
``RequestProject/GLM/CoordinateOrder.lean``.  Directive D7 -- no float
anywhere -- is checked statically.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.data_objects.semantic_lexicon import SEMANTIC_PRIMITIVES
from glm_universal.reasoning import coordinate_order as CO
from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import field_surface as FS
from glm_universal.reasoning import probe_oracle as PO
from glm_universal.runtime import parser as PA
from glm_universal.runtime.session import GeometricSession

LEAN = (Path(__file__).resolve().parents[3]
        / "RequestProject" / "GLM" / "CoordinateOrder.lean")


@pytest.fixture(scope="module")
def session():
    return GeometricSession()


@pytest.fixture(scope="module")
def surface(session):
    return session.field_surface


@pytest.fixture(scope="module")
def report(session):
    return CO.comparison_report(session)


class TestReadings:

    def test_a_held_coordinate_is_read_exactly(self, surface):
        read = CO.reading(surface, "atomic_weight_u", "carbon")
        assert read.row == "C"
        assert read.value == Fraction(12011, 1000)
        assert read.scale == "element:atomic_weight_u"

    def test_a_derived_coordinate_says_that_it_is_derived(self, surface):
        read = CO.reading(surface, "molar_mass_u", "water")
        assert read.derived and read.rule
        assert read.value == Fraction(3603, 200)

    def test_a_coordinate_inside_a_mapping_field_is_read_as_a_coordinate(
            self, surface):
        """The lexicon holds its ten primitives as one mapping field."""
        read = CO.reading(surface, "abstract_concrete", "energy")
        assert read.value == Fraction(1, 4)
        assert read.field == "primitives.abstract_concrete"
        assert read.scale == "carrier:lexicon:primitives.abstract_concrete"

    def test_the_scale_is_the_table_and_the_field(self, surface):
        read = CO.reading(surface, "line", "GLM.NormFamily.family_tower")
        assert read.scale == "lean:line"

    def test_a_label_is_not_a_reading(self, surface):
        with pytest.raises(CO.OrderingError) as caught:
            CO.reading(surface, "kind", "energy")
        assert caught.value.reason == "not-ordered"

    def test_a_row_the_surface_does_not_hold_is_restated_not_reclassified(
            self, surface):
        with pytest.raises(CO.OrderingError) as caught:
            CO.reading(surface, "name", "unobtainium")
        assert caught.value.reason == "unreadable"
        assert "nearest rows" in str(caught.value)

    def test_a_boolean_is_a_label_rather_than_a_number(self):
        assert CO.as_exact(True) is None
        assert CO.as_exact(1) == Fraction(1)
        assert CO.as_exact("1/4") == Fraction(1, 4)
        assert CO.as_exact("-3") == Fraction(-3)
        assert CO.as_exact("Halogen") is None
        assert CO.as_exact("1.5") is None


class TestTheOperation:

    def test_the_probe_question_is_answered_at_the_pole(self, surface):
        result = CO.order(surface, "abstract_concrete", "energy", "water")
        assert result.verdict == "lt"
        assert result.difference == Fraction(3, 4)
        assert result.pole == "abstract"
        assert result.pole_row == "energy"

    def test_the_gap_is_the_exact_difference(self, surface):
        result = CO.order(surface, "atomic_weight_u", "carbon", "oxygen")
        assert result.difference == (Fraction(15999, 1000)
                                     - Fraction(12011, 1000))

    def test_equal_readings_are_level_and_name_no_pole(self, surface):
        result = CO.order(surface, "animate_inanimate", "energy", "water")
        assert result.verdict == "eq"
        assert result.pole_row == ""
        assert "level with" in result.sentence

    def test_asking_the_other_way_round_swaps_the_verdict(self, surface):
        one = CO.order(surface, "atomic_weight_u", "carbon", "oxygen")
        two = CO.order(surface, "atomic_weight_u", "oxygen", "carbon")
        assert (one.verdict, two.verdict) == ("lt", "gt")
        assert one.difference == -two.difference
        assert one.pole_row == two.pole_row == ""

    def test_two_scales_are_refused_rather_than_compared(self, surface):
        with pytest.raises(CO.OrderingError) as caught:
            CO.order(surface, "line", "GLM.NormFamily.family_tower",
                     "rung_audit")
        assert caught.value.reason == "different-scale"
        assert "lean:line" in str(caught.value)
        assert "python:line" in str(caught.value)

    def test_a_coordinate_one_row_does_not_hold_is_unreadable(self, surface):
        with pytest.raises(CO.OrderingError) as caught:
            CO.order(surface, "atomic_weight_u", "carbon", "water")
        assert caught.value.reason == "unreadable"

    def test_every_refusal_carries_a_declared_reason(self, surface):
        seen = set()
        for field, left, right in (("kind", "energy", "water"),
                                   ("line", "GLM.NormFamily.family_tower",
                                    "rung_audit"),
                                   ("atomic_weight_u", "carbon", "water")):
            with pytest.raises(CO.OrderingError) as caught:
                CO.order(surface, field, left, right)
            seen.add(caught.value.reason)
        assert seen == set(CO.REFUSAL_REASONS)

    def test_the_sentence_names_the_scale_both_were_read_on(self, surface):
        result = CO.order(surface, "molar_mass_u", "water", "ethanol")
        assert "molecule:molar_mass_u" in result.sentence


class TestWhyTheSideConditionIsSameScale:
    """The Python mirror of ``GLM.CoordinateOrder``'s §4.

    Rescaling a whole scale by a positive factor leaves every verdict on it
    alone (``order_scale_invariant``), and comparing the raw numbers of two
    readings that are *not* on one scale is not scale-free
    (``naive_order_is_not_scale_free``) -- which is why the refusal is a
    result rather than fussiness.
    """

    VALUES = (Fraction(0), Fraction(1, 4), Fraction(1), Fraction(-3, 2),
              Fraction(100), Fraction(997, 250))
    FACTORS = (Fraction(1, 100), Fraction(1, 2), Fraction(3), Fraction(1000))

    @staticmethod
    def _sign(a: Fraction, b: Fraction) -> int:
        return (a > b) - (a < b)

    def test_a_shared_positive_rescaling_changes_no_verdict(self, subtests):
        for c in self.FACTORS:
            for a in self.VALUES:
                for b in self.VALUES:
                    with subtests.test(c=str(c), a=str(a), b=str(b)):
                        assert self._sign(c * a, c * b) == self._sign(a, b)

    def test_rescaling_one_side_alone_flips_a_verdict(self):
        a, b, c = Fraction(100), Fraction(2), Fraction(1, 100)
        assert self._sign(a, b) == 1
        assert self._sign(c * a, b) == -1


class TestThePoles:

    def test_the_poles_are_the_registers_own_ten_primitives(self):
        assert set(CO.POLES) == set(SEMANTIC_PRIMITIVES)

    def test_every_primitive_declares_two_distinct_ends(self):
        for name, (low, high) in CO.POLES.items():
            assert low and high and low != high, name

    def test_a_coordinate_with_no_declared_pole_names_none(self, surface):
        result = CO.order(surface, "atomic_weight_u", "carbon", "oxygen")
        assert result.pole == "" and result.pole_row == ""
        assert "the more" not in result.sentence


class TestTheQueryKind:

    def test_the_kind_is_registered_once(self):
        assert "ordering" in PA.KINDS
        assert PA.KINDS.count("ordering") == 1

    def test_the_question_is_cut_into_a_coordinate_and_two_rows(self):
        parsed = PA.parse_query("order abstract_concrete of energy and water")
        assert parsed.kind == "ordering"
        assert parsed.options["name"] == "abstract_concrete"
        assert parsed.options["left"] == "energy"
        assert parsed.options["right"] == "water"

    def test_the_solver_answers_at_the_pole(self, session):
        solution = session.ask("order abstract_concrete of energy and water")
        assert solution.ok
        assert solution.expected["verdict"] == "lt"
        assert solution.expected["pole_row"] == "energy"
        assert solution.expected["difference"] == "3/4"

    def test_the_solver_states_the_boundary_rather_than_guessing(self,
                                                                 session):
        solution = session.ask(
            "order line of GLM.NormFamily.family_tower and rung_audit")
        assert not solution.ok
        assert "different-scale" in str(solution.error)

    def test_a_question_missing_a_row_is_refused_with_the_shape(self,
                                                                session):
        solution = session.ask("order abstract_concrete of energy")
        assert not solution.ok
        assert "two rows" in str(solution.error)

    def test_the_answer_names_the_faculty_it_is(self, session):
        solution = session.ask("order abstract_concrete of energy and water")
        labels = " ".join(step.mathematics for step in solution.steps)
        assert "faculty = derivation and refusal" in labels


class TestTheMeasurement:

    def test_every_declared_comparison_came_out_as_declared(self, report,
                                                            subtests):
        for row in report["rows"]:
            with subtests.test(key=row["key"]):
                assert row["as_declared"], row["detail"]

    def test_the_declared_set_covers_both_halves(self, report):
        assert report["answered"] + report["refused"] == report["declared"]
        assert set(report["refusal_reasons"]) == set(CO.REFUSAL_REASONS)

    def test_the_frozen_oracle_table_is_not_edited(self):
        frozen = {row.key: row for row in PO.TRANSLATIONS}
        for key in FS.SURFACE_KEYS:
            assert frozen[key].query is None

    def test_only_the_one_question_this_round_was_about_moves(self, report):
        assert report["moved"] == ("nl-compare",)

    def test_the_question_that_moved_is_scored_at_the_row_it_names(self):
        rows = {row.key: row for row in CO.order_translations()}
        moved = rows["nl-compare"]
        assert moved.locus == "pole_row"
        assert moved.query == "order abstract_concrete of energy and water"
        assert moved.note

    def test_nothing_is_smuggled_into_the_question_it_is_scored_on(self):
        audit = FS.smuggling_audit(CO.order_translations())
        assert [row for row in audit if row["smuggled"]] == []
        assert any(row["key"] == "nl-compare" for row in audit)

    def test_the_rest_of_the_table_is_the_one_the_last_round_measured(self):
        after = {row.key: row for row in CO.order_translations()}
        for row in FS.translations_after():
            if row.key != "nl-compare":
                assert after[row.key] is row

    def test_no_question_outside_the_held_class_changes(self, report):
        assert report["before"]["absent"] == report["after"]["absent"]
        assert (report["after"]["parsed"] - report["before"]["parsed"]
                == len(report["moved"]))

    def test_the_verdict_is_stated_with_its_caveat(self, report):
        assert str(report["answered"]) in report["verdict"]
        assert "parses English" in report["caveat"]


class TestTheProvedHalf:

    def test_the_lean_file_states_what_the_module_cites(self):
        text = LEAN.read_text(encoding="utf-8")
        for name in ("order_eq_none_iff", "order_isSome_iff",
                     "order_lt_iff", "order_gt_iff", "order_eq_iff",
                     "order_sound", "order_swap", "order_trans",
                     "order_scale_invariant",
                     "naive_order_is_not_scale_free",
                     "energy_below_water_on_abstract_concrete",
                     "across_scales_is_refused"):
            assert f"theorem {name}" in text
        assert "sorry" not in text

    def test_the_proved_reading_is_the_shipped_one(self, surface):
        """The two values the Lean file states are the register's own."""
        text = LEAN.read_text(encoding="utf-8")
        energy = CO.reading(surface, "abstract_concrete", "energy")
        water = CO.reading(surface, "abstract_concrete", "water")
        assert (energy.value, water.value) == (Fraction(1, 4), Fraction(1))
        assert "1 / 4" in text and "abstract_concrete" in text


class TestExactness:

    def test_no_float_is_constructed(self):
        assert ex.module_float_sites(Path(CO.__file__)) == {}
