"""Tests for ``reasoning/measure_view`` -- the relative reading of a measure word.

``test_comparison_classes.py`` pins the register this is built on.  What is
pinned here is the *view*: the reading, the audit that says adding it is a
widening rather than a replacement, the conversion of the ``related_to``
residue, and -- the point of step 5 of
``studies/RELATIVE_MEASURE_PROPOSAL.md`` -- the refusals at the boundary.

Four things could go wrong and each has a class:

* the reading could be wrong, or built from a float (``TestTheReading``);
* the widening could quietly *lose* something the static reading had, which
  is exactly what the rejected replacement does (``TestTheWidening``);
* the ``related_to`` conversion could guess (``TestTheRelationRepair``);
* the query could answer where the registers hold nothing, instead of
  refusing with the reason (``TestTheRefusals``, ``TestTheQuery``).

The machine-checked counterparts are in ``RequestProject/GLM/MeasureView.lean``:
``measureLayer_refines_staticLayer`` (the widening loses nothing),
``measureReading_not_refines_staticLayer`` (the replacement does),
``boundary_empty_of_unmeasured`` (there is nothing to answer with at the
boundary) and ``magnitude_strictMono`` (a higher word is a larger magnitude).
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.data_objects import comparison_classes as cc
from glm_universal.data_objects import physics as ph
from glm_universal.reasoning import measure_view as mvw
from glm_universal.runtime import parser as PA
from glm_universal.runtime.session import GeometricSession, SolverError


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


@pytest.fixture(scope="module")
def audit():
    return mvw.widening_audit()


@pytest.fixture(scope="module")
def repair():
    return mvw.relation_repair()


@pytest.fixture(scope="module")
def report():
    return mvw.measure_report()


class TestWhichWordsCanBeMeasured:
    """Twelve lexicon adjectives, and the registers now measure all twelve."""

    def test_twelve_adjectives_all_of_them_scaled(self):
        words = mvw.measure_words()
        assert len(words) == 12
        assert len(mvw.scaled_words()) == 12
        assert len(mvw.unscaled_words()) == 0

    def test_the_three_words_the_size_and_light_classes_closed(self):
        """``large``, ``small`` and ``dark`` used to have no measurement."""
        words = {w.word: w for w in mvw.measure_words()}
        assert words["large"].quantity == "volume"
        assert words["small"].quantity == "volume"
        assert words["dark"].quantity == "illuminance"
        for word in ("large", "small", "dark"):
            assert words[word].status == "scaled"
            assert words[word].reason == ""

    def test_the_lexicon_s_own_name_is_still_reported(self):
        """The alias resolves a name; it does not rewrite the lexicon."""
        assert mvw.lexicon_quantity("large") == "size"
        assert mvw.lexicon_quantity("small") == "size"
        assert mvw.lexicon_quantity("dark") == "light"
        assert mvw.lexicon_quantity("hot") == "temperature"
        assert mvw.lexicon_quantity("no_such_word") is None

    def test_the_quantity_is_the_lexicon_s_own(self, subtests):
        for word in mvw.scaled_words():
            with subtests.test(word=word.word):
                assert word.quantity is not None
                assert ph.quantity_by_name(word.quantity).name == word.quantity
                assert cc.degree_word(word.word) == (word.quantity,
                                                     word.position)

    def test_a_scale_word_that_is_not_a_concept_is_still_a_measure_word(self):
        warm = mvw.word_by_name("warm")
        assert warm.scaled is True
        assert warm.quantity == "temperature"

    def test_a_word_on_no_scale_at_all_is_a_boundary(self):
        with pytest.raises(mvw.MeasureBoundary) as raised:
            mvw.word_by_name("expensive")
        assert raised.value.reason == "no such measure word"


class TestTheReading:
    """``low + position * (high - low)``, exactly."""

    def test_hot_is_a_different_temperature_in_each_class(self):
        assert mvw.read("hot", "tea").magnitude == Fraction(363)
        assert mvw.read("hot", "stellar_surface").magnitude == Fraction(44000)
        assert mvw.read("cold", "stellar_surface").magnitude == Fraction(8000)

    def test_the_reading_is_the_bracket_formula(self, subtests):
        for word in mvw.scaled_words():
            assert word.quantity is not None
            for klass in cc.classes_for_quantity(word.quantity):
                with subtests.test(word=word.word, klass=klass.name):
                    reading = mvw.read(word.word, klass.name)
                    assert reading.magnitude == (
                        klass.low + reading.position * (klass.high - klass.low))
                    assert isinstance(reading.magnitude, Fraction)
                    assert reading.unit == klass.unit

    def test_the_unit_and_dimension_are_the_physics_register_s(self):
        reading = mvw.read("hot", "tea")
        registered = ph.quantity_by_name("temperature")
        assert reading.unit == registered.unit
        assert reading.dimension == ph.dimension_string(registered.exps_ext10)

    def test_a_higher_word_is_a_larger_magnitude(self, subtests):
        for quantity, scale in cc.measure_scales().items():
            for klass in cc.classes_for_quantity(quantity):
                magnitudes = [klass.magnitude_at(w.position)
                              for w in scale.words]
                with subtests.test(klass=klass.name):
                    assert magnitudes == sorted(magnitudes)
                    assert len(set(magnitudes)) == len(magnitudes)

    def test_classify_is_the_other_direction(self):
        found = mvw.classify(Fraction(300), "tea")
        assert found["quantity"] == "temperature"
        assert found["inside_bracket"] is True
        assert found["position"] == Fraction(7, 80)
        assert found["word"] == "cold"

    def test_a_magnitude_outside_the_bracket_is_said_to_be_outside(self):
        found = mvw.classify(Fraction(1000), "tea")
        assert found["inside_bracket"] is False
        assert found["position"] > 1

    def test_words_on_one_scale_are_ordered_and_others_are_not(self):
        verdict = mvw.compare_words("hot", "cold")
        assert verdict["order"] == 1
        assert verdict["quantity"] == "temperature"
        with pytest.raises(mvw.MeasureBoundary):
            mvw.compare_words("hot", "fast")

    def test_the_derived_relations_are_all_of_the_measure_family(self):
        relations = mvw.measure_relations("hot")
        assert relations
        assert {predicate for predicate, _ in relations} <= set(
            mvw.MEASURE_RELATIONS)
        assert ("measures", "temperature") in relations
        assert ("measures_relative_to", "tea") in relations
        assert ("opposite_pole", "cold") in relations


class TestTheWidening:
    """Adding the reading gains 108 pairs and loses none."""

    def test_the_use_set(self, audit):
        assert audit["uses"] == 56
        assert audit["measured_uses"] == 56
        assert audit["words"] == 12
        assert audit["unmeasured_words"] == []

    def test_the_three_views_and_what_each_resolves(self, audit):
        views = {view["name"]: view for view in audit["views"]}
        assert views["static"]["resolution"] == 12
        assert views["measure"]["resolution"] == 56
        assert views["measure_only"]["resolution"] == 56

    def test_the_widening_gains_and_loses_nothing(self, audit):
        boundary = audit["boundary"]
        assert boundary["gained"] == 108
        assert boundary["violations"] == 0
        assert boundary["refines"] is True
        assert boundary["example_violation"] is None

    def test_the_static_view_is_the_layer_and_not_an_idealisation(self, audit):
        agreement = audit["static_agreement"]
        assert agreement["agrees"] is True
        assert agreement["disagreements"] == []
        assert agreement["pairs_checked"] == 56 * 55 // 2

    def test_the_measure_view_is_a_pair_whose_first_half_is_the_static_one(
            self, subtests):
        for use in mvw.uses():
            with subtests.test(use=use.name):
                widened = mvw.measure_view(use)
                assert widened[0] == mvw.static_view(use)
                assert widened[1] == mvw.measure_only_view(use)

    def test_the_widening_never_conflates_what_the_static_view_told_apart(
            self, subtests):
        entries = mvw.uses()
        for i, a in enumerate(entries):
            for b in entries[i + 1:]:
                if mvw.static_view(a) != mvw.static_view(b):
                    with subtests.test(pair=(a.name, b.name)):
                        assert mvw.measure_view(a) != mvw.measure_view(b)

    def test_the_shipped_data_no_longer_refutes_the_replacement(self, audit):
        """Not because it became sound: there is no unmeasured word left."""
        assert audit["unmeasured_words"] == []
        assert audit["non_cumulative"]["violations"] == 0

    def test_the_replacement_still_fails_on_an_unmeasured_use(self):
        """One use of each word with no class: they all read alike to it."""
        witness = mvw.replacement_witness()
        assert witness["shipped_violations"] == 0
        assert witness["unmeasured_uses"] == 12
        assert witness["uses"] == 56 + 12
        assert witness["widening"]["violations"] == 0
        assert witness["widening"]["refines"] is True
        assert witness["replacement"]["refines"] is False
        assert witness["replacement"]["violations"] == 12 * 11 // 2

    def test_an_unmeasured_use_reads_as_nothing_at_all(self):
        unmeasured = [mvw.Use(w.word, "") for w in mvw.measure_words()]
        assert {mvw.measure_only_view(u) for u in unmeasured} == {None}
        assert len({mvw.static_view(u) for u in unmeasured}) == 12

    def test_no_two_measured_uses_share_a_magnitude(self, audit):
        assert audit["magnitude_collisions"]["count"] == 0


class TestTheRelationRepair:
    """27 of 66 ``related_to`` triples convert; the other 39 give a reason.

    The counts moved from 15/51 when the quantity-alias table grew from two
    entries to seven: an endpoint that was being declined for the *spelling*
    of its name -- *heat*, *weight*, *illumination*, *distance*,
    *magnetic_field* -- now resolves to a quantity the physics register holds,
    and the dimensional test can then decide the triple.
    """

    def test_the_counts(self, repair):
        assert repair["triples"] == 380
        assert repair["related_to"] == 66
        assert repair["converted"] == 27
        assert repair["residue"] == 39
        assert repair["converted"] + repair["residue"] == repair["related_to"]

    def test_by_predicate(self, repair):
        assert repair["by_predicate"] == {"same_dimension_as": 6,
                                          "differs_by": 21}
        assert sum(repair["by_predicate"].values()) == repair["converted"]

    def test_every_residue_triple_carries_its_reason(self, repair):
        reasons = repair["residue_reasons"]
        assert sum(reasons.values()) == repair["residue"] == 39
        assert all(reason and count > 0 for reason, count in reasons.items())

    def test_the_factor_basis_is_all_registered_quantities(self, repair,
                                                           subtests):
        for name in repair["factor_basis"]:
            with subtests.test(quantity=name):
                assert ph.quantity_by_name(name).name == name

    def test_every_conversion_is_checkable_from_the_register(self, repair,
                                                             subtests):
        for row in repair["conversions"]:
            with subtests.test(triple=(row["subject"], row["object"])):
                if row["predicate"] == "same_dimension_as":
                    assert row["witness"] is None
                else:
                    assert row["predicate"] == "differs_by"
                    assert row["witness"]
                    assert str(row["object"]) in str(row["witness"])


class TestTheRefusals:
    """Where the registers hold nothing, the reason is the answer."""

    @pytest.mark.parametrize("word,klass,reason", [
        ("large", "room", "quantity mismatch"),
        ("dark", "room", "quantity mismatch"),
        ("hot", "walking", "quantity mismatch"),
        ("expensive", "market", "no such measure word"),
    ])
    def test_the_four_refusals_and_their_reasons(self, word, klass, reason):
        with pytest.raises(mvw.MeasureBoundary) as raised:
            mvw.read(word, klass)
        assert raised.value.reason == reason

    @pytest.mark.parametrize("word,klass,magnitude", [
        ("large", "room_volume", Fraction(1755, 4)),
        ("small", "room_volume", Fraction(285, 4)),
        ("dark", "indoor_lighting", Fraction(675, 4)),
    ])
    def test_two_of_the_refusals_are_now_measurements(self, word, klass,
                                                      magnitude):
        """The same words, against a class of the quantity they measure."""
        assert mvw.read(word, klass).magnitude == magnitude

    def test_an_unregistered_class_is_refused_with_the_alternatives(self):
        with pytest.raises(mvw.MeasureBoundary) as raised:
            mvw.read("hot", "no_such_class")
        assert raised.value.reason == "no such comparison class"
        assert "tea" in str(raised.value)

    def test_the_report_records_the_refusals(self, report):
        refusals = {row["word"]: row for row in report["refusals"]}
        assert set(refusals) == {"large", "dark", "hot", "expensive"}
        assert all(row["reason"] != "answered" for row in refusals.values())


class TestTheReport:
    """``measure_report`` recomputes the study; nothing is quoted."""

    def test_the_report_agrees_with_its_parts(self, report, audit, repair):
        assert report["scaled"] == 12
        assert report["unscaled"] == 0
        assert report["widening"] == audit
        assert report["relation_repair"] == repair
        assert report["register"] == dict(cc.register_summary())
        assert report["lexicon_agreement"]["agrees"] is True

    def test_the_examples_are_readings(self, report):
        examples = {(row["word"], row["comparison_class"]): row
                    for row in report["examples"]}
        assert examples[("hot", "tea")]["magnitude"] == Fraction(363)
        assert examples[("hot", "stellar_surface")]["magnitude"] == Fraction(
            44000)
        assert all(isinstance(row["magnitude"], Fraction)
                   for row in report["examples"])


class TestTheQuery:
    """The runtime path: three shapes that answer, and the ones that refuse."""

    def test_a_word_against_a_class(self, sess):
        solution = sess.ask("measure hot in tea")
        assert solution.ok is True
        assert solution.kind == "measure"
        assert "363" in solution.answer
        assert solution.payload["reading"]["magnitude"] == "363/1"

    def test_a_magnitude_against_a_class(self, sess):
        solution = sess.ask("measure 300 in tea")
        assert solution.ok is True
        assert solution.payload["verdict"]["word"] == "cold"

    def test_a_word_against_every_class_of_its_quantity(self, sess):
        solution = sess.ask("measure hot")
        assert solution.ok is True
        readings = solution.payload["readings"]
        assert len(readings) == 6
        assert len({row["magnitude"] for row in readings}) == 6

    @pytest.mark.parametrize("query", [
        "measure large in room",
        "measure dark in room",
        "measure hot in walking",
        "measure expensive in market",
    ])
    def test_the_query_refuses_at_the_boundary(self, sess, query):
        solution = sess.ask(query)
        assert solution.ok is False
        assert solution.error is not None
        assert solution.error.startswith("measure: ")

    def test_the_solver_itself_raises_the_refusal(self, sess):
        """``solve`` reports it as a failed solution; the solver raises it."""
        query = PA.parse_query("measure large in room", sess.index)
        with pytest.raises(SolverError):
            sess._solve_measure(query)

    def test_the_report_subject_is_reachable(self, sess):
        solution = sess.ask("report measure")
        assert solution.ok is True
        assert solution.payload["report"]["scaled"] == 12

    def test_the_parser_classifies_the_kind(self, sess):
        query = PA.parse_query("measure hot in tea", sess.index)
        assert query.kind == "measure"
        assert query.options["subject"] == "hot"
        assert query.options["class"] == "tea"

    def test_measure_is_a_declared_query_kind(self):
        assert "measure" in PA.KINDS
