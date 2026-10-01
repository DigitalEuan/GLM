"""Tests for the field surface: the tables, the query kind, and the round's
own measurement against the prediction that bought it.

What is pinned here is the *mechanism*, not the score.  The surface must
resolve a row only by a name the row itself holds, answer with the exact
value it holds, say so when a value is recomputed rather than stored, and
refuse at three named boundaries -- an unknown row, an unknown field of a
known row, and a field the register records as missing.  The measurement's
numbers are deliberately not asserted: what is asserted is that the frozen
oracle table is left alone, that the second table smuggles nothing, and that
no question outside the ten the prediction was about changes class.

Directive D7 -- no float anywhere -- is checked statically.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import field_surface as FS
from glm_universal.reasoning import lean_book
from glm_universal.reasoning import probe_oracle as PO
from glm_universal.runtime import fields as FL
from glm_universal.runtime import parser as PA
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def session():
    return GeometricSession()


@pytest.fixture(scope="module")
def surface(session):
    return session.field_surface


class TestRendering:

    def test_a_terminating_decimal_is_written_and_an_other_is_not(self):
        assert FL.exact_decimal(Fraction(12011, 1000)) == "12.011"
        assert FL.exact_decimal(Fraction(-3, 4)) == "-0.75"
        assert FL.exact_decimal(Fraction(7, 1)) == "7"
        assert FL.exact_decimal(Fraction(1, 3)) is None
        assert FL.exact_decimal(Fraction(2, 7)) is None

    def test_a_rational_carries_its_exact_form_first(self):
        assert FL.render_value(Fraction(12011, 1000)) == "12011/1000 (= 12.011)"
        assert FL.render_value(Fraction(1, 3)) == "1/3"

    def test_a_mapping_renders_in_sorted_key_order(self):
        assert FL.render_value({"b": 2, "a": 1}) == "a=1, b=2"

    def test_a_boolean_is_not_rendered_as_an_integer(self):
        assert FL.render_value(True) == "true"
        assert FL.render_value(1) == "1"


class TestTheTables:

    def test_every_table_declares_a_kind_a_gloss_and_a_provenance(self,
                                                                  surface):
        for table in surface.tables():
            assert table.kind in FL.TABLE_KINDS
            assert table.gloss and table.provenance

    def test_the_table_names_are_distinct(self, surface):
        names = [table.name for table in surface.tables()]
        assert len(names) == len(set(names))

    def test_a_session_surface_holds_one_carrier_table_per_register(
            self, session, surface):
        carrier = {table.name for table in surface.tables()
                   if table.kind == "carrier"}
        assert carrier == {f"carrier:{d}" for d in session.domains}

    def test_a_row_answers_only_to_a_name_it_holds_itself(self, surface):
        """No alias is invented: every alias is the key or a name field."""
        table = surface.table_by_name("element")
        for alias, key in table.aliases().items():
            row = table.rows()[key]
            held = {PA.normalise(str(row[name]))
                    for name in ("name", "symbol") if row.get(name)}
            assert alias in held | {PA.normalise(key), key.lower()}

    def test_only_declared_functions_are_reachable(self, surface):
        table = surface.table_by_name("function")
        assert set(table.rows()) == set(FL.FUNCTION_SURFACES)

    def test_the_lean_table_is_the_stored_book_and_not_the_development(
            self, surface):
        """Every Lean row is the book's row, field for field.

        The table used to parse the development on the runtime's own import
        path, which put all 120 Lean files into the closure of nearly every
        test unit and cost a round most of a release after one Lean edit
        (``studies/ITERATION_COST_STUDY.md`` 5e).  It answers from the
        generated book now, and this is the check that the answers did not
        change with the source they come from.
        """
        stored = lean_book.declaration_rows()
        rows = surface.table_by_name("lean").rows()
        assert rows == dict(stored)
        assert len(rows) > 3000
        for row in list(rows.values())[:50]:
            assert set(row) == {"file", "line", "kind", "namespace",
                                "statement"}

    def test_the_census_counts_what_the_tables_hold(self, surface):
        census = surface.census()
        assert census["tables"] == len(surface.tables())
        assert census["rows"] == sum(int(entry["rows"])
                                     for entry in census["per_table"])
        assert census["addressable_pairs"] >= census["rows"]


class TestLookup:

    def test_a_held_field_is_answered_exactly(self, surface):
        found = surface.field("atomic_weight_u", "carbon")
        assert found.row == "C"
        assert found.value == Fraction(12011, 1000)
        assert found.rendered == "12011/1000 (= 12.011)"
        assert found.table == "element"
        assert not found.derived

    def test_a_derived_field_says_that_it_is_derived(self, surface):
        found = surface.field("molar_mass_u", "water")
        assert found.derived and found.rule
        assert found.value == Fraction(3603, 200)

    def test_a_relation_is_a_field_of_the_word_it_relates(self, surface):
        found = surface.field("derivative_of", "velocity")
        assert "position" in found.rendered

    def test_a_declaration_is_a_row_of_the_address_book(self, surface):
        found = surface.field("file", "GLM.NormFamily.family_tower")
        assert found.rendered.endswith("NormFamily.lean")
        assert found.table_kind == "address"

    def test_a_declared_function_answers_by_key(self, surface):
        found = surface.field(
            "rungs", "glm_universal.substrate.norm_family.completeness")
        assert found.rendered == "25"

    def test_the_listing_shape_names_the_fields_and_nothing_else(self,
                                                                 surface):
        held = surface.fields(
            "glm_universal.substrate.norm_family.completeness")
        assert "complete" in held.names and "rungs" in held.names
        assert held.tables == ("function",)
        assert held.names == tuple(sorted(held.names))


class TestRefusals:

    def test_an_unknown_row_is_refused_with_the_nearest_rows(self, surface):
        with pytest.raises(FL.FieldError) as caught:
            surface.field("name", "unobtainium")
        assert "nearest rows" in str(caught.value)

    def test_an_unknown_field_is_refused_with_the_fields_held(self, surface):
        with pytest.raises(FL.FieldError) as caught:
            surface.field("boiling_point", "carbon")
        assert "boiling_point_K" in str(caught.value)

    def test_a_missing_value_is_refused_as_missing(self, surface):
        with pytest.raises(FL.FieldError) as caught:
            surface.field("electronegativity_pauling", "He")
        assert "missing" in str(caught.value)


class TestTheQueryKind:

    def test_the_kind_is_registered_once(self):
        assert "field" in PA.KINDS
        assert PA.KINDS.count("field") == 1

    def test_the_opening_governs_only_at_the_head_of_the_question(self):
        opened = PA.parse_query("field name of C")
        assert opened.kind == "field"
        buried = PA.parse_query("electric field strength")
        assert buried.kind != "field"

    def test_the_last_separator_cuts(self):
        parsed = PA.parse_query("field derivative_of of velocity")
        assert parsed.options["name"] == "derivative_of"
        assert parsed.options["row"] == "velocity"

    def test_the_listing_shape_parses_without_a_field(self):
        parsed = PA.parse_query("fields of water")
        assert parsed.kind == "field"
        assert parsed.options["list"] is True
        assert parsed.options["row"] == "water"

    def test_the_solver_answers_at_the_value(self, session):
        solution = session.ask("field group_block of chlorine")
        assert solution.ok
        assert solution.expected["value"] == "Halogen"
        assert solution.expected["row"] == "Cl"

    def test_the_solver_states_the_boundary_rather_than_guessing(self,
                                                                 session):
        solution = session.ask("field name of unobtainium")
        assert not solution.ok
        assert "nearest rows" in str(solution.error)

    def test_a_field_answer_names_the_faculty_it_is(self, session):
        solution = session.ask("field atomic_weight_u of carbon")
        labels = " ".join(step.mathematics for step in solution.steps)
        assert "faculty = table" in labels


class TestTheMeasurement:

    def test_the_frozen_table_is_not_edited(self):
        """The previous round's reading has to stay re-runnable."""
        frozen = {row.key: row for row in PO.TRANSLATIONS}
        for key in FS.SURFACE_KEYS:
            assert frozen[key].query is None

    def test_the_second_table_covers_exactly_the_surface_class(self):
        assert ({row.key for row in FS.FIELD_TRANSLATIONS}
                == set(FS.SURFACE_KEYS))

    def test_the_declared_unreachable_question_carries_no_query(self):
        rows = {row.key: row for row in FS.FIELD_TRANSLATIONS}
        for key in FS.DECLARED_UNREACHABLE:
            assert rows[key].query is None
            assert rows[key].note == FS.DECLARED_UNREACHABLE[key]

    def test_nothing_is_smuggled(self):
        assert [row for row in FS.smuggling_audit() if row["smuggled"]] == []

    def test_every_translation_says_why(self):
        for row in FS.FIELD_TRANSLATIONS:
            assert row.note

    def test_the_substituted_table_is_the_frozen_one_elsewhere(self):
        after = {row.key: row for row in FS.translations_after()}
        for row in PO.TRANSLATIONS:
            if row.key not in FS.SURFACE_KEYS:
                assert after[row.key] is row

    def test_the_reading_moves_only_the_class_it_was_about(self, session):
        report = FS.surface_report(session)
        assert report["unexpected_changes"] == ()
        assert report["smuggled"] == ()
        assert (len(report["moved"]) + len(report["still_surface"])
                == len(FS.SURFACE_KEYS))
        assert report["after"]["absent"] == report["before"]["absent"]

    def test_the_verdict_is_stated_with_its_caveat(self, session):
        report = FS.surface_report(session)
        assert "table" in report["caveat"]
        assert str(report["moved_count"]) in report["verdict"]


class TestExactness:

    def test_no_float_is_constructed(self):
        assert ex.module_float_sites(Path(FL.__file__)) == {}
        assert ex.module_float_sites(Path(FS.__file__)) == {}
