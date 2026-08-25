"""Tests for ``reasoning/information_loss`` and its runtime wiring.

The module measures *where a layer's truth ends*: what each layer of the
dimension stack cannot tell apart, which pairs the layer above it splits, and
whether a law computed above can be computed below.  These tests pin the
measured numbers on the fixed carrier set, all four boundaries of the
five-layer stack, the cumulativity that makes the stack a refinement chain --
together with the non-cumulative reading that is not one, kept beside it and
still measured -- and the ``report information loss`` query end to end.

The counterpart machine-checked development is in ``RequestProject/GLM/``:
``Layers.lean`` proves the general theory and ``Stack.lean`` the concrete
three-layer stack whose numbers this module reproduces on real carriers.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import dimension_layers as DL
from glm_universal.reasoning import information_loss as IL
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def carriers():
    return IL.sample_carriers()


@pytest.fixture(scope="module")
def report():
    return IL.information_loss_report()


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


# The seven fixed carriers, by index.
VACUUM, HALF, UNIT, TWO, FAR, AXIS_A, AXIS_B = 0, 1, 2, 3, 4, 5, 6


# ===========================================================================
# 1.  THE CARRIER SET
# ===========================================================================

class TestSampleCarriers:

    def test_seven_carriers_of_twenty_four_exact_coordinates(self, carriers):
        assert len(carriers) == 7
        for carrier in carriers:
            assert len(carrier) == 24
            for coordinate in carrier:
                assert isinstance(coordinate, Fraction)

    def test_no_float_is_constructed(self, carriers):
        """Exactness: every coordinate is a Fraction, never a float."""
        for carrier in carriers:
            for coordinate in carrier:
                assert not isinstance(coordinate, float)

    def test_the_carriers_are_the_intended_ones(self, carriers):
        assert all(x == 0 for x in carriers[VACUUM])
        assert carriers[HALF][0] == Fraction(1, 2)
        assert carriers[UNIT][0] == Fraction(1)
        assert carriers[TWO][0] == Fraction(2)
        assert carriers[FAR][10] == Fraction(1)
        assert carriers[AXIS_A] != carriers[AXIS_B]
        assert (carriers[AXIS_B][0] - carriers[AXIS_A][0]) == Fraction(1, 7)

    def test_the_axis_pair_shares_one_2a_axis(self, carriers):
        """Two distinct carriers, one Griess axis: the pair that forces the
        Griess measure to carry the carrier term as well as the algebra."""
        views = [DL.LAYER_GRIESS.perceive(carriers[i])
                 for i in (AXIS_A, AXIS_B)]
        assert views[0]["is_2a_axis"] and views[1]["is_2a_axis"]
        assert views[0]["leech_class"] == views[1]["leech_class"]
        assert DL.griess_semantic_component(views[0], views[1]) == 0


# ===========================================================================
# 2.  THE RELATION, AND THE RESOLUTION IT INDUCES
# ===========================================================================

class TestIndistinguishability:

    def test_indistinguishability_is_reflexive(self, carriers):
        for layer in (DL.LAYER_SUBSTRATE, DL.LAYER_INTEGER,
                      DL.LAYER_RATIONAL):
            for carrier in carriers:
                assert IL.indistinguishable(layer, carrier, carrier)

    def test_indistinguishability_is_symmetric(self, carriers):
        for layer in (DL.LAYER_SUBSTRATE, DL.LAYER_INTEGER,
                      DL.LAYER_RATIONAL):
            for a in carriers:
                for b in carriers:
                    assert (IL.indistinguishable(layer, a, b)
                            == IL.indistinguishable(layer, b, a))

    def test_classes_partition_the_carriers(self, carriers):
        for layer in (DL.LAYER_SUBSTRATE, DL.LAYER_INTEGER,
                      DL.LAYER_RATIONAL):
            parts = IL.classes(layer, carriers)
            seen = sorted(i for part in parts for i in part)
            assert seen == list(range(len(carriers)))

    def test_resolution_plus_loss_is_the_carrier_count(self, carriers):
        for layer in (DL.LAYER_SUBSTRATE, DL.LAYER_INTEGER,
                      DL.LAYER_RATIONAL):
            assert (IL.resolution(layer, carriers)
                    + IL.loss_count(layer, carriers) == len(carriers))


class TestMeasuredResolution:
    """The measured numbers, layer by layer."""

    def test_substrate_resolves_three_of_seven(self, carriers):
        assert IL.resolution(DL.LAYER_SUBSTRATE, carriers) == 3
        assert IL.loss_count(DL.LAYER_SUBSTRATE, carriers) == 4

    def test_substrate_conflates_the_even_amplitudes(self, carriers):
        """Parity cannot see an even amplitude, so 0, 1/2, 2 and the two
        even-coordinate axis carriers are one thing to it."""
        assert IL.classes(DL.LAYER_SUBSTRATE, carriers) == (
            (VACUUM, HALF, TWO, AXIS_A, AXIS_B), (UNIT,), (FAR,))

    def test_integer_resolves_five_of_seven(self, carriers):
        assert IL.resolution(DL.LAYER_INTEGER, carriers) == 5
        assert IL.loss_count(DL.LAYER_INTEGER, carriers) == 2

    def test_integer_conflates_only_what_truncation_loses(self, carriers):
        """Truncation loses the half and the seventh of a unit; the parity
        bits the cumulative view carries keep coordinate 10 apart."""
        assert IL.classes(DL.LAYER_INTEGER, carriers) == (
            (VACUUM, HALF), (UNIT,), (TWO,), (FAR,), (AXIS_A, AXIS_B))

    def test_rational_loses_nothing(self, carriers):
        assert IL.resolution(DL.LAYER_RATIONAL, carriers) == 7
        assert IL.loss_count(DL.LAYER_RATIONAL, carriers) == 0
        assert IL.classes(DL.LAYER_RATIONAL, carriers) == tuple(
            (i,) for i in range(7))

    def test_griess_and_universal_lose_nothing_either(self, carriers):
        for layer in (DL.LAYER_GRIESS, DL.LAYER_UNIVERSAL):
            assert IL.loss_count(layer, carriers) == 0


class TestViewCache:
    """The cache must be an optimisation only, never a change of answer."""

    def test_clearing_the_cache_does_not_change_the_verdicts(self, carriers):
        before = tuple(IL.classes(layer, carriers)
                       for layer in (DL.LAYER_SUBSTRATE, DL.LAYER_INTEGER,
                                     DL.LAYER_RATIONAL))
        IL.clear_view_cache()
        after = tuple(IL.classes(layer, carriers)
                      for layer in (DL.LAYER_SUBSTRATE, DL.LAYER_INTEGER,
                                    DL.LAYER_RATIONAL))
        assert before == after

    def test_a_cached_view_equals_a_fresh_perceive(self, carriers):
        layer = DL.LAYER_INTEGER
        cached = IL.view(layer, carriers[UNIT])
        assert cached == layer.perceive(carriers[UNIT])


# ===========================================================================
# 3.  CAPACITY -- the pigeonhole reason the substrate must lose something
# ===========================================================================

class TestCapacity:

    def test_only_the_substrate_is_finite(self):
        assert IL.capacity(DL.LAYER_SUBSTRATE) == 2 ** 24
        assert IL.capacity(DL.LAYER_INTEGER) is None
        assert IL.capacity(DL.LAYER_RATIONAL) is None

    def test_capacity_bounds_the_substrate_resolution(self, carriers):
        bound = IL.capacity(DL.LAYER_SUBSTRATE)
        assert bound is not None
        assert IL.resolution(DL.LAYER_SUBSTRATE, carriers) <= bound


# ===========================================================================
# 4.  THE BOUNDARIES
# ===========================================================================

class TestBoundaries:

    def test_substrate_to_integer_boundary(self, carriers):
        """Everything the exponents add to the parity view, listed."""
        assert IL.boundary(DL.LAYER_SUBSTRATE, DL.LAYER_INTEGER,
                           carriers) == ((VACUUM, TWO), (VACUUM, AXIS_A),
                                         (VACUUM, AXIS_B), (HALF, TWO),
                                         (HALF, AXIS_A), (HALF, AXIS_B),
                                         (TWO, AXIS_A), (TWO, AXIS_B))

    def test_integer_to_rational_boundary(self, carriers):
        """What truncation loses: the half, and the seventh of a unit."""
        assert IL.boundary(DL.LAYER_INTEGER, DL.LAYER_RATIONAL,
                           carriers) == ((VACUUM, HALF), (AXIS_A, AXIS_B))

    def test_a_boundary_is_never_symmetric_in_its_two_layers(self, carriers):
        """Lost-at-a-boundary is directional: it is not the same set back."""
        forward = IL.boundary(DL.LAYER_INTEGER, DL.LAYER_RATIONAL, carriers)
        backward = IL.boundary(DL.LAYER_RATIONAL, DL.LAYER_INTEGER, carriers)
        assert forward
        assert backward == ()

    def test_nothing_is_lost_above_the_rational_layer(self, carriers):
        """The rational layer already separates every carrier."""
        assert IL.boundary(DL.LAYER_RATIONAL, DL.LAYER_GRIESS,
                           carriers) == ()


# ===========================================================================
# 5.  THE REFINEMENT CHAIN -- and the reading that would break it
# ===========================================================================

class TestRefinementChain:
    """Every layer sees at least as much as the one below it."""

    def test_every_consecutive_pair_refines(self, carriers):
        for lower, higher in zip(DL.LAYERS, DL.LAYERS[1:]):
            assert IL.refinement_violations(lower, higher, carriers) == (), (
                f"{lower.name} -> {higher.name}")
            assert IL.refines(higher, lower, carriers)

    def test_refinement_is_transitive_across_the_whole_stack(self, carriers):
        top = DL.LAYERS[-1]
        for lower in DL.LAYERS[:-1]:
            assert IL.refines(top, lower, carriers)

    def test_the_report_records_the_chain_as_intact(self, report):
        assert report["refinement_chain_intact"] is True
        for edge in report["boundaries"]:
            assert edge["refines"] is True
            assert edge["refinement_violations"] == []


class TestCumulativity:
    """*Why* the chain is intact: each view keeps the one below it."""

    def test_the_integer_view_carries_the_substrate_reading(self, carriers):
        for carrier in carriers:
            integer = DL.LAYER_INTEGER.perceive(carrier)
            substrate = DL.LAYER_SUBSTRATE.perceive(carrier)
            assert integer["substrate_bits"] == substrate["bits"]
            assert integer["hamming_weight"] == substrate["hamming_weight"]

    def test_the_integer_measure_dominates_the_substrate_one(self, carriers):
        """Zero at the integer layer forces zero at the substrate."""
        for a in carriers:
            for b in carriers:
                integer = DL.LAYER_INTEGER.measure(
                    DL.LAYER_INTEGER.perceive(a),
                    DL.LAYER_INTEGER.perceive(b))
                substrate = DL.LAYER_SUBSTRATE.measure(
                    DL.LAYER_SUBSTRATE.perceive(a),
                    DL.LAYER_SUBSTRATE.perceive(b))
                assert integer >= substrate

    def test_the_griess_measure_keeps_the_carrier_term(self, carriers):
        """The axis pair is one axis to the algebra and two to the layer."""
        a, b = carriers[AXIS_A], carriers[AXIS_B]
        va, vb = (DL.LAYER_GRIESS.perceive(a), DL.LAYER_GRIESS.perceive(b))
        assert DL.griess_semantic_component(va, vb) == 0
        assert DL.LAYER_GRIESS.measure(va, vb) > 0
        assert not IL.indistinguishable(DL.LAYER_GRIESS, a, b)

    def test_parity_bits_has_one_definition(self, carriers):
        for carrier in carriers:
            assert (DL.parity_bits(carrier)
                    == DL.LAYER_SUBSTRATE.perceive(carrier)["bits"])


class TestNonCumulativeReading:
    """The reading the stack does *not* use, and what it would have cost.

    ``LAYER_INTEGER_RAW`` takes the seven SI exponents and discards the
    substrate's view instead of adding to it.  The substrate separates a unit
    on coordinate 10 from the vacuum; the raw reading, blind to coordinates
    7-23, conflates them.  Escalating to it would therefore *lose* a
    distinction the layer below already had -- which is why the layer in the
    stack carries both readings.
    """

    def test_the_raw_reading_is_not_in_the_stack(self):
        assert DL.LAYER_INTEGER_RAW not in DL.LAYERS
        assert DL.LAYER_INTEGER_RAW.name == "integer_raw"

    def test_the_raw_reading_does_not_refine_the_substrate(self, carriers):
        holes = IL.refinement_violations(
            DL.LAYER_SUBSTRATE, DL.LAYER_INTEGER_RAW, carriers)
        assert holes == ((VACUUM, FAR), (HALF, FAR))

    def test_the_cumulative_layer_repairs_exactly_those_pairs(self,
                                                              carriers):
        for i, j in ((VACUUM, FAR), (HALF, FAR)):
            assert IL.indistinguishable(DL.LAYER_INTEGER_RAW,
                                        carriers[i], carriers[j])
            assert not IL.indistinguishable(DL.LAYER_INTEGER,
                                            carriers[i], carriers[j])

    def test_the_raw_reading_resolves_strictly_less(self, carriers):
        assert (IL.resolution(DL.LAYER_INTEGER_RAW, carriers)
                < IL.resolution(DL.LAYER_INTEGER, carriers))

    def test_the_report_measures_the_difference(self, report):
        raw = report["non_cumulative"]
        assert raw["layer"] == "integer_raw"
        assert raw["refines_substrate"] is False
        assert raw["violation_count"] == 2
        assert raw["violating_pairs"] == [[VACUUM, FAR], [HALF, FAR]]
        assert raw["cumulative_layer"] == "integer"
        assert raw["cumulative_refines_substrate"] is True
        assert raw["resolution"] == 4
        assert raw["cumulative_resolution"] == 5


# ===========================================================================
# 6.  THE REACH OF A LAW
# ===========================================================================

class TestCongruence:

    def test_addition_does_not_descend_to_the_substrate(self, carriers):
        witness = IL.congruence_witness(DL.LAYER_SUBSTRATE, carriers)
        assert witness is not None
        assert witness.layer == "substrate"

    def test_addition_does_not_descend_to_the_integer_layer(self, carriers):
        witness = IL.congruence_witness(DL.LAYER_INTEGER, carriers)
        assert witness is not None
        assert witness.layer == "integer"

    def test_addition_descends_to_the_rational_layer(self, carriers):
        assert IL.congruence_witness(DL.LAYER_RATIONAL, carriers) is None
        assert IL.is_congruent(DL.LAYER_RATIONAL, carriers)

    def test_a_witness_really_is_a_witness(self, carriers):
        """Check the witness against the definition rather than trusting it."""
        for layer in (DL.LAYER_SUBSTRATE, DL.LAYER_INTEGER):
            witness = IL.congruence_witness(layer, carriers)
            assert witness is not None
            assert IL.indistinguishable(layer, witness.a, witness.a2)
            assert IL.indistinguishable(layer, witness.b, witness.b2)
            assert not IL.indistinguishable(
                layer,
                IL.carrier_sum(witness.a, witness.b),
                IL.carrier_sum(witness.a2, witness.b2))

    def test_witness_serialises_exactly(self, carriers):
        witness = IL.congruence_witness(DL.LAYER_SUBSTRATE, carriers)
        assert witness is not None
        data = witness.as_dict()
        assert data["layer"] == "substrate"
        for key in ("a", "a2", "b", "b2"):
            assert len(data[key]) == 24
            for entry in data[key]:
                assert isinstance(entry, str)

    def test_carrier_sum_is_exact_and_coordinatewise(self, carriers):
        total = IL.carrier_sum(carriers[HALF], carriers[HALF])
        assert total[0] == Fraction(1)
        assert all(isinstance(x, Fraction) for x in total)


# ===========================================================================
# 7.  THE REPORT
# ===========================================================================

class TestReport:

    def test_report_covers_five_layers_and_four_boundaries(self, report):
        assert [layer["name"] for layer in report["layers"]] == [
            "substrate", "integer", "rational", "griess", "universal"]
        assert [(b["lower"], b["higher"]) for b in report["boundaries"]] == [
            ("substrate", "integer"), ("integer", "rational"),
            ("rational", "griess"), ("griess", "universal")]

    def test_report_numbers_match_the_direct_computation(self, report,
                                                         carriers):
        by_name = {layer["name"]: layer for layer in report["layers"]}
        for layer in (DL.LAYER_SUBSTRATE, DL.LAYER_INTEGER,
                      DL.LAYER_RATIONAL):
            entry = by_name[layer.name]
            assert entry["resolution"] == IL.resolution(layer, carriers)
            assert entry["loss_count"] == IL.loss_count(layer, carriers)
            assert entry["addition_descends"] == IL.is_congruent(layer,
                                                                 carriers)

    def test_report_is_recomputed_not_quoted(self, carriers):
        """Feeding it a different carrier set changes the answer."""
        smaller = carriers[:2]
        other = IL.information_loss_report(smaller)
        assert other["carrier_count"] == 2
        by_name = {layer["name"]: layer for layer in other["layers"]}
        # Nothing separates the vacuum from a half at the integer layer.
        assert by_name["integer"]["resolution"] == 1
        assert by_name["rational"]["resolution"] == 2

    def test_report_is_json_shaped(self, report):
        """Every leaf is a str, int, bool, None, list or dict."""

        def check(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    assert isinstance(key, str)
                    check(item)
            elif isinstance(value, list):
                for item in value:
                    check(item)
            else:
                assert isinstance(value, (str, int, bool)) or value is None

        check(report)


# ===========================================================================
# 8.  RUNTIME WIRING -- `report information loss`
# ===========================================================================

class TestReportQuery:

    def test_the_query_is_answered(self, sess):
        sol = sess.ask("report information loss")
        assert sol.ok
        assert sol.kind == "report"

    def test_the_aliases_all_reach_the_same_solver(self, sess):
        answers = {sess.ask(f"report {alias}").answer
                   for alias in ("information loss", "loss", "boundaries")}
        assert len(answers) == 1

    def test_the_expected_values_are_the_measured_ones(self, sess):
        sol = sess.ask("report information loss")
        assert sol.expected["carrier_count"] == "7"
        assert sol.expected["resolution_substrate"] == "3"
        assert sol.expected["resolution_integer"] == "5"
        assert sol.expected["resolution_rational"] == "7"
        assert sol.expected["loss_substrate"] == "4"
        assert sol.expected["loss_integer"] == "2"
        assert sol.expected["loss_rational"] == "0"
        assert sol.expected["addition_descends_substrate"] == "False"
        assert sol.expected["addition_descends_integer"] == "False"
        assert sol.expected["addition_descends_rational"] == "True"
        assert sol.expected["lost_count_substrate_to_integer"] == "8"
        assert sol.expected["lost_count_integer_to_rational"] == "2"
        assert sol.expected["refines_substrate_to_integer"] == "True"
        assert sol.expected["refines_integer_to_rational"] == "True"
        assert sol.expected["refines_rational_to_griess"] == "True"
        assert sol.expected["refines_griess_to_universal"] == "True"
        assert sol.expected["refinement_chain_intact"] == "True"
        assert sol.expected["non_cumulative_refines_substrate"] == "False"
        assert sol.expected["non_cumulative_violations"] == "2"
        assert sol.expected["cumulative_refines_substrate"] == "True"

    def test_the_five_steps_are_present(self, sess):
        sol = sess.ask("report information loss")
        assert len(sol.steps) == 5

    def test_the_subject_list_mentions_the_new_subject(self, sess):
        sol = sess.ask("report")
        assert not sol.ok
        assert "information loss" in sol.answer
        sol = sess.ask("report nonsense subject")
        assert not sol.ok
        assert "information loss" in sol.answer

    def test_the_generated_script_is_exact(self, sess):
        sol = sess.ask("report information loss")
        source = tct.render_script(sol)
        ok, offenders = tct.script_is_exact(source)
        assert ok, offenders

    def test_the_generated_script_reproduces_column_two(self, sess):
        """Column 3 recomputes the study in a fresh interpreter and agrees."""
        sol = sess.ask("report information loss")
        trace = tct.verify_trace(tct.build_trace(sol))
        assert trace.verdict is not None
        assert trace.verdict.executed
        assert trace.verdict.returncode == 0
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()
        assert trace.verdict.missing_keys == ()


# ===========================================================================
# 9.  PACKAGE EXPORTS
# ===========================================================================

class TestExports:

    def test_the_module_is_exported_from_the_reasoning_package(self):
        from glm_universal import reasoning
        assert "information_loss" in reasoning.__all__
        assert reasoning.information_loss is IL
        assert reasoning.information_loss_report is IL.information_loss_report

    def test_every_name_in_dunder_all_exists(self):
        for name in IL.__all__:
            assert hasattr(IL, name), name
