"""Tests for the extremum operation: one coordinate over every row of one
table, folded or refused.

What is pinned here is the *mechanism*, not the score.  The operation must
gather a column by reading the coordinate off every row of one declared table,
refuse a column that has a hole in it and a column that was gathered from more
than one scale, fold exactly, and name **every** row that attains the end
rather than picking one of them.  The refusals are the point of it: an
extremum taken over the rows that happen to be filled in is a wrong answer
rather than a partial one, and the extremum of two scales together is a fact
about neither.

The machine-checked counterparts are in
``RequestProject/GLM/ColumnExtremum.lean``.  Directive D7 -- no float anywhere
-- is checked statically.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import column_extremum as CX
from glm_universal.reasoning import exactness as ex
from glm_universal.runtime import parser as PA
from glm_universal.runtime.session import GeometricSession

LEAN = (Path(__file__).resolve().parents[3]
        / "RequestProject" / "GLM" / "ColumnExtremum.lean")


@pytest.fixture(scope="module")
def session():
    return GeometricSession()


@pytest.fixture(scope="module")
def surface(session):
    return session.field_surface


@pytest.fixture(scope="module")
def report(session):
    return CX.extremum_report(session)


class TestTheColumn:

    def test_a_column_is_every_row_of_one_table(self, surface):
        found = CX.column(surface, "atomic_weight_u", "element")
        assert found.rows == 118
        assert found.table == "element"
        assert found.scale == "element:atomic_weight_u"

    def test_every_reading_of_a_column_is_on_its_one_scale(self, surface):
        found = CX.column(surface, "atomic_weight_u", "element")
        assert {r.scale for r in found.readings} == {found.scale}

    def test_a_coordinate_inside_a_mapping_field_is_a_column_too(self,
                                                                 surface):
        """The lexicon holds its ten primitives as one mapping field."""
        found = CX.column(surface, "abstract_concrete", "carrier:lexicon")
        assert found.rows == 149
        assert found.scale == "carrier:lexicon:primitives.abstract_concrete"

    def test_a_derived_column_is_recomputed_rather_than_stored(self, surface):
        found = CX.column(surface, "molar_mass_u", "molecule")
        assert all(r.derived and r.rule for r in found.readings)

    def test_the_rows_of_a_column_are_read_in_a_determinate_order(self,
                                                                  surface):
        once = CX.column(surface, "atomic_weight_u", "element")
        twice = CX.column(surface, "atomic_weight_u", "element")
        assert ([r.row for r in once.readings]
                == [r.row for r in twice.readings])


class TestWhatItRefuses:
    """Four named reasons, and the two the operation exists for."""

    def test_a_column_with_a_hole_in_it_is_refused(self, surface):
        with pytest.raises(CX.ExtremumError) as caught:
            CX.extremum(surface, "electronegativity_pauling", "largest",
                        "element")
        assert caught.value.reason == "incomplete"

    def test_the_refusal_names_what_is_missing(self, surface):
        with pytest.raises(CX.ExtremumError) as caught:
            CX.extremum(surface, "electronegativity_pauling", "largest",
                        "element")
        message = str(caught.value)
        assert "23 of 118 rows" in message
        assert "element:Ar" in message

    def test_a_column_gathered_from_two_scales_is_refused(self, surface):
        with pytest.raises(CX.ExtremumError) as caught:
            CX.extremum(surface, "line", "largest")
        assert caught.value.reason == "mixed-scale"
        assert "lean:line" in str(caught.value)
        assert "python:line" in str(caught.value)

    def test_naming_one_table_asks_for_one_of_the_two_scales(self, surface):
        """The mixed-scale refusal is about the *gathering*, not the field."""
        found = CX.extremum(surface, "line", "largest", "lean")
        assert found.scale == "lean:line"

    def test_a_column_of_labels_has_no_extremum(self, surface):
        with pytest.raises(CX.ExtremumError) as caught:
            CX.extremum(surface, "name", "largest", "element")
        assert caught.value.reason == "not-ordered"

    def test_a_coordinate_no_row_holds_is_not_a_column(self, surface):
        with pytest.raises(CX.ExtremumError) as caught:
            CX.extremum(surface, "boiling_point", "largest", "element")
        assert caught.value.reason == "no-such-column"

    def test_an_undeclared_table_is_refused_where_the_names_are_visible(
            self, surface):
        with pytest.raises(CX.ExtremumError) as caught:
            CX.extremum(surface, "atomic_weight_u", "largest", "elements")
        assert caught.value.reason == "no-such-column"

    def test_an_end_that_is_not_an_end_is_refused(self, surface):
        with pytest.raises(CX.ExtremumError) as caught:
            CX.extremum(surface, "atomic_weight_u", "middle", "element")
        assert caught.value.reason == "no-such-column"
        assert "largest and smallest" in str(caught.value)

    def test_every_declared_reason_is_reachable(self, surface, subtests):
        seen = set()
        for field, table in (("electronegativity_pauling", "element"),
                             ("line", None),
                             ("name", "element"),
                             ("boiling_point", "element")):
            with subtests.test(field=field):
                with pytest.raises(CX.ExtremumError) as caught:
                    CX.extremum(surface, field, "largest", table)
                seen.add(caught.value.reason)
        assert seen == set(CX.REFUSAL_REASONS)


class TestTheFold:

    def test_the_value_returned_is_a_value_of_the_column(self, surface):
        found = CX.extremum(surface, "atomic_weight_u", "largest", "element")
        values = [r.value for r in
                  CX.column(surface, "atomic_weight_u", "element").readings]
        assert found.value in values

    def test_nothing_in_the_column_is_past_the_end_it_returns(self, surface,
                                                              subtests):
        for end, beyond in (("largest", lambda v, m: v > m),
                            ("smallest", lambda v, m: v < m)):
            with subtests.test(end=end):
                found = CX.extremum(surface, "atomic_weight_u", end,
                                    "element")
                column = CX.column(surface, "atomic_weight_u", "element")
                assert not any(beyond(r.value, found.value)
                               for r in column.readings)

    def test_the_two_ends_name_different_rows(self, surface):
        top = CX.extremum(surface, "atomic_weight_u", "largest", "element")
        bottom = CX.extremum(surface, "atomic_weight_u", "smallest",
                             "element")
        assert [r.row for r in top.winners] == ["Og"]
        assert [r.row for r in bottom.winners] == ["H"]
        assert bottom.value < top.value

    def test_every_row_attaining_the_end_is_named_and_only_those(self,
                                                                 surface):
        found = CX.extremum(surface, "abstract_concrete", "largest",
                            "carrier:lexicon")
        column = CX.column(surface, "abstract_concrete", "carrier:lexicon")
        assert (sorted(r.row for r in found.winners)
                == sorted(r.row for r in column.readings
                          if r.value == found.value))

    def test_a_tie_is_reported_rather_than_resolved(self, surface):
        found = CX.extremum(surface, "abstract_concrete", "largest",
                            "carrier:lexicon")
        assert len(found.winners) == 14
        assert "14 rows" in found.sentence

    def test_the_gap_is_the_exact_distance_to_the_next_distinct_value(
            self, surface):
        found = CX.extremum(surface, "abstract_concrete", "largest",
                            "carrier:lexicon")
        assert found.value == Fraction(1)
        assert found.runner_up == Fraction(3, 4)
        assert found.gap == Fraction(1, 4)

    def test_a_column_with_one_distinct_value_has_no_runner_up(self):
        """Constructed, because no shipped column is constant."""
        assert CX.Extremum(
            field="f", table="t", scale="t:f", end="largest",
            value=Fraction(1), rendered="1", winners=(), rows=1,
            runner_up=None, derived=False).gap is None

    def test_a_derived_column_folds_on_the_same_terms(self, surface):
        found = CX.extremum(surface, "molar_mass_u", "largest", "molecule")
        assert found.derived
        assert [r.row for r in found.winners] == ["iron(III) sulfate"]

    def test_the_sentence_states_the_scale_every_row_was_read_on(self,
                                                                 surface):
        found = CX.extremum(surface, "atomic_weight_u", "largest", "element")
        assert "element:atomic_weight_u" in found.sentence
        assert "118 rows" in found.sentence


class TestWhyAHoleIsRefusedRatherThanSkipped:
    """The Python mirror of ``GLM.ColumnExtremum``'s §6.

    ``extremum_over_present_is_not_the_extremum`` exhibits a column whose
    extremum over the rows that are filled in is not its extremum once the
    hole is filled.  The shipped operation therefore refuses rather than
    folding over what is left -- and the refusal is checked here to be a
    refusal of the *column*, not a report of a failed search.
    """

    @staticmethod
    def _present_max(surface, field, table):
        rows = surface.table_by_name(table).rows()
        values = [v for v in (row.get(field) for row in rows.values())
                  if v is not None]
        return max(Fraction(str(v)) for v in values)

    def test_the_rows_that_are_filled_in_do_have_a_maximum(self, surface):
        assert self._present_max(surface, "electronegativity_pauling",
                                 "element") == Fraction(398, 100)

    def test_and_the_operation_declines_to_return_it(self, surface):
        with pytest.raises(CX.ExtremumError) as caught:
            CX.extremum(surface, "electronegativity_pauling", "largest",
                        "element")
        assert "3.98" not in str(caught.value)
        assert "wrong answer rather than a partial one" in str(caught.value)

    def test_filling_a_hole_can_move_the_answer(self):
        """The witness the Lean file exhibits, in the shipped arithmetic."""
        present = [Fraction(1)]
        filled = present + [Fraction(3)]
        assert max(present) == Fraction(1)
        assert max(filled) == Fraction(3)


class TestWhyTheSideConditionIsOneScale:
    """The Python mirror of ``GLM.ColumnExtremum``'s §5.

    Carrying the whole column by a positive factor moves the value by that
    factor and leaves the winners alone (``extremum_scale_invariant``);
    carrying *one row* -- which is exactly what gathering a column from two
    scales permits -- moves the winner
    (``extremum_not_invariant_under_one_row_rescaling``).
    """

    COLUMN = (("a", Fraction(3)), ("b", Fraction(4)), ("c", Fraction(4)))
    FACTORS = (Fraction(1, 100), Fraction(1, 2), Fraction(3), Fraction(100))

    @classmethod
    def _winners(cls, column):
        best = max(v for _row, v in column)
        return best, sorted(row for row, v in column if v == best)

    def test_rescaling_the_whole_column_keeps_every_winner(self, subtests):
        best, winners = self._winners(self.COLUMN)
        for k in self.FACTORS:
            with subtests.test(k=str(k)):
                carried = [(row, k * v) for row, v in self.COLUMN]
                assert self._winners(carried) == (k * best, winners)

    def test_rescaling_one_row_alone_moves_the_winner(self):
        _best, winners = self._winners(self.COLUMN)
        assert winners == ["b", "c"]
        one_row = [("a", Fraction(100) * Fraction(3)), ("b", Fraction(4)),
                   ("c", Fraction(4))]
        assert self._winners(one_row) == (Fraction(300), ["a"])


class TestTheQueryKind:

    def test_the_kind_is_registered_once(self):
        assert "extremum" in PA.KINDS
        assert PA.KINDS.count("extremum") == 1

    def test_the_question_is_cut_into_an_end_a_coordinate_and_a_table(self):
        parsed = PA.parse_query("largest atomic_weight_u in element")
        assert parsed.kind == "extremum"
        assert parsed.options["end"] == "largest"
        assert parsed.options["name"] == "atomic_weight_u"
        assert parsed.options["table"] == "element"

    def test_the_end_is_read_off_the_keyword(self, subtests):
        for word, end in (("largest", "largest"), ("highest", "largest"),
                          ("maximum", "largest"), ("smallest", "smallest"),
                          ("lowest", "smallest"), ("minimum", "smallest")):
            with subtests.test(word=word):
                parsed = PA.parse_query(f"{word} atomic_weight_u in element")
                assert parsed.kind == "extremum"
                assert parsed.options["end"] == end

    def test_a_question_naming_no_table_is_a_question_not_an_error(self):
        parsed = PA.parse_query("largest line")
        assert parsed.kind == "extremum"
        assert parsed.options["name"] == "line"
        assert parsed.options["table"] == ""

    def test_the_keyword_governs_only_where_it_opens_the_question(self):
        """`smallest` is an ordinary adjective of these registers."""
        parsed = PA.parse_query("describe the smallest vector of the leech "
                                "lattice")
        assert parsed.kind != "extremum"

    def test_the_solver_folds_the_column(self, session):
        solution = session.ask("largest atomic_weight_u in element")
        assert solution.ok
        assert solution.expected["winners"] == "Og"
        assert solution.expected["rows"] == "118"
        assert solution.expected["scale"] == "element:atomic_weight_u"

    def test_the_solver_states_the_boundary_rather_than_guessing(self,
                                                                 session):
        solution = session.ask("largest electronegativity_pauling in element")
        assert not solution.ok
        assert "incomplete" in str(solution.error)

    def test_the_solver_refuses_a_column_gathered_from_two_scales(self,
                                                                  session):
        solution = session.ask("largest line")
        assert not solution.ok
        assert "mixed-scale" in str(solution.error)

    def test_the_answer_names_the_faculty_it_is(self, session):
        solution = session.ask("largest atomic_weight_u in element")
        labels = " ".join(step.mathematics for step in solution.steps)
        assert "faculty = derivation and refusal" in labels

    def test_the_script_recomputes_the_answer_it_reports(self, session):
        solution = session.ask("largest atomic_weight_u in element")
        from glm_universal.runtime import tct_engine as tct
        assert solution.script_spec["template"] == "extremum"
        script = tct.render_script(solution)
        assert "column_extremum" in script
        assert "reason == \"incomplete\"" in script

    def test_the_kind_has_a_declared_one_rung_ladder(self):
        from glm_universal.runtime import escalation_loop as el
        assert el.ladder_for("extremum") == ("L1",)


class TestTheMeasurement:

    def test_every_declared_column_came_out_as_declared(self, report,
                                                        subtests):
        for row in report["rows"]:
            with subtests.test(key=row["key"]):
                assert row["as_declared"], row["detail"]

    def test_the_declared_set_covers_both_halves(self, report):
        assert report["answered"] + report["refused"] == report["declared"]
        assert set(report["refusal_reasons"]) == set(CX.REFUSAL_REASONS)

    def test_the_declared_set_exercises_every_refusal_reason(self, report):
        assert report["reasons_declared"] == len(CX.REFUSAL_REASONS)
        assert len(report["refusal_reasons"]) == report["reasons_declared"]

    def test_a_tie_is_among_the_declared_answers(self, report):
        assert report["ties"] >= 1

    def test_the_verdict_is_stated_with_its_caveat(self, report):
        assert str(report["answered"]) in report["verdict"]
        assert str(report["refused"]) in report["caveat"]
        assert "parses English" in report["caveat"]

    def test_the_declared_set_is_written_down_before_it_is_run(self):
        keys = [row[0] for row in CX.DECLARED_EXTREMA]
        assert len(keys) == len(set(keys))
        for _key, end, field, _table, expected in CX.DECLARED_EXTREMA:
            assert end in CX.ENDS
            assert field
            assert expected == "answer" or expected in CX.REFUSAL_REASONS


class TestTheProvedHalf:

    def test_the_lean_file_states_what_the_module_cites(self, subtests):
        text = LEAN.read_text(encoding="utf-8")
        for name in ("extremum_eq_none_iff", "extremum_isSome_iff",
                     "extremum_value_mem", "le_extremum",
                     "mem_extremum_winners_iff", "extremum_winners_ne_nil",
                     "extremum_scale_invariant",
                     "extremum_not_invariant_under_one_row_rescaling",
                     "extremum_over_present_is_not_the_extremum",
                     "trough_eq_none_iff", "trough_names_the_smallest"):
            with subtests.test(name=name):
                assert f"theorem {name}" in text
        assert "sorry" not in text

    def test_the_proved_refusals_are_the_shipped_ones(self):
        """The Lean file refuses on a hole and on a second scale, and the
        module's reasons say the same two things in its own words."""
        text = LEAN.read_text(encoding="utf-8")
        assert "holes" in text and "scales" in text
        assert "incomplete" in CX.REFUSAL_REASONS
        assert "mixed-scale" in CX.REFUSAL_REASONS


class TestExactness:

    def test_no_float_is_constructed(self):
        assert ex.module_float_sites(Path(CX.__file__)) == {}
