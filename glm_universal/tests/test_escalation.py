"""Tests for ``reasoning/escalation`` -- the layer stack at register scale.

``test_information_loss.py`` pins the seven-carrier audit.  This module pins
the same audit run on the machine's own data, and in particular the one thing
that could make the scaled numbers wrong: the audit is *keyed* rather than
pairwise, so what has to be checked is that the key partition and the layers'
own ``measure`` say the same thing.  Two classes do that -- one against the
slow functions of ``information_loss`` on a mixed carrier set, one on the
report's own sample -- and the rest pin the findings the scale produced:

* resolution rises 415 -> 544 -> 757 and then stops, because the top three
  layers hold the carrier itself;
* every boundary is a refinement, on a thousand carriers rather than seven;
* the ceiling -- 757 distinct carriers under 1,040 named entries, so 283
  entries are beyond every layer, all of the collisions inside one register;
* addition descends exactly where the view is the carrier;
* the rejected SI7-only reading breaks refinement at scale, in bulk.

The machine-checked counterparts are in ``RequestProject/GLM/Escalation.lean``:
``entryResolution_le_distinct`` (the ceiling), ``entryResolution_mono``
(resolution rises), ``glmRationalLayer_congruentOn`` (descent where the layer
is lossless) and ``substrate_addition_not_congruent`` (and its integer-layer
twin) for the half-unit witness.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import dimension_layers as DL
from glm_universal.reasoning import escalation as esc
from glm_universal.reasoning import information_loss as IL
from glm_universal.runtime.session import GeometricSession

STACK = ("substrate", "integer", "rational", "griess", "universal")


@pytest.fixture(scope="module")
def entries():
    return esc.register_carriers()


@pytest.fixture(scope="module")
def report():
    return esc.escalation_report()


@pytest.fixture(scope="module")
def mixed():
    """A small carrier set the slow audit can still be run on.

    The report's own verification sample, plus the seven fixture carriers of
    ``information_loss``, so both the register data and the hand-picked
    boundary cases are covered.
    """
    sample = esc.verification_sample(esc.register_carriers())
    return [e.carrier for e in sample] + list(IL.sample_carriers())


class TestTheKeysAreTheZeroSets:
    """The fast path agrees with the layers themselves, quantity by quantity."""

    @pytest.mark.exhaustive
    def test_classes_agree_with_the_pairwise_audit(self, mixed, subtests):
        for layer in list(DL.LAYERS) + [DL.LAYER_INTEGER_RAW]:
            with subtests.test(layer=layer.name):
                assert (esc.keyed_classes(layer.name, mixed)
                        == IL.classes(layer, mixed))

    def test_boundary_and_violation_counts_agree(self, mixed, subtests):
        for lower, higher in zip(STACK, STACK[1:]):
            low = DL.LAYER_BY_NAME[lower]
            high = DL.LAYER_BY_NAME[higher]
            found = esc.boundary_at_scale(lower, higher, mixed)
            with subtests.test(boundary=f"{lower}->{higher}"):
                assert found["gained"] == len(IL.boundary(low, high, mixed))
                assert found["violations"] == len(
                    IL.refinement_violations(low, high, mixed))

    @pytest.mark.exhaustive
    def test_congruence_agrees_with_the_quartic_search(self, mixed, subtests):
        for layer in DL.LAYERS:
            with subtests.test(layer=layer.name):
                witness = esc.congruence_witness_at_scale(
                    layer.name, mixed, exhaustive=True)
                assert (witness is None) == IL.is_congruent(layer, mixed)

    def test_report_checks_the_keys_and_they_hold(self, report):
        agreement = report["key_agreement"]
        assert agreement["agrees"] is True
        assert agreement["disagreements"] == []
        assert agreement["pairs_checked"] == (
            len(esc.KEYED_LAYERS)
            * agreement["sample_size"] * (agreement["sample_size"] - 1) // 2)

    def test_a_wrong_key_would_be_caught(self, entries):
        """The check is not vacuous: break the key and it reports the pair."""
        original = esc.class_key
        try:
            esc.class_key = lambda name, carrier: 0        # everything one class
            broken = esc.key_agreement(esc.verification_sample(entries))
        finally:
            esc.class_key = original
        assert broken["agrees"] is False
        assert broken["disagreements"]


class TestTheCarrierSet:
    """The carriers are the registers, whole and in a fixed order."""

    def test_one_carrier_per_named_object(self, entries):
        sizes = esc.register_sizes(entries)
        assert sizes == {"physics": 726, "chemistry": 118, "molecules": 51,
                         "mathematics": 22, "harmonics": 28, "lexicon": 95}
        assert len(entries) == sum(sizes.values()) == 1040

    def test_every_carrier_is_24_exact_rationals(self, entries):
        for entry in entries:
            assert len(entry.carrier) == 24
            assert all(isinstance(x, Fraction) for x in entry.carrier)

    def test_the_order_is_deterministic(self):
        first = [e.name for e in esc.register_carriers()]
        esc._CARRIER_CACHE.clear()
        second = [e.name for e in esc.register_carriers()]
        assert first == second

    def test_the_sample_is_spread_over_every_register(self, entries):
        sample = esc.verification_sample(entries)
        assert len(sample) == esc.VERIFY_PER_REGISTER * len(esc.REGISTERS)
        assert {e.register for e in sample} == set(esc.REGISTERS)


class TestResolutionAtScale:
    """What each layer resolves, and that the order cannot invert."""

    def test_the_measured_column(self, report, subtests):
        expected = {"substrate": 415, "integer": 544, "rational": 757,
                    "griess": 757, "universal": 757, "integer_raw": 359}
        for layer in report["layers"]:
            with subtests.test(layer=layer["name"]):
                assert layer["resolution"] == expected[layer["name"]]
                assert (layer["loss_count"]
                        == report["carrier_count"] - layer["resolution"])

    def test_resolution_rises_up_the_stack(self, report):
        stack = [l for l in report["layers"] if l["name"] in STACK]
        resolutions = [l["resolution"] for l in stack]
        assert resolutions == sorted(resolutions)

    def test_the_top_three_layers_resolve_the_distinct_carriers(self, report):
        distinct = report["ceiling"]["distinct_carriers"]
        for name in ("rational", "griess", "universal"):
            found = next(l for l in report["layers"] if l["name"] == name)
            assert found["resolution"] == distinct


class TestEveryBoundaryIsARefinement:
    """The chain holds on a thousand carriers, and the gains are counted."""

    def test_chain_intact(self, report):
        assert report["refinement_chain_intact"] is True
        for boundary in report["boundaries"]:
            assert boundary["violations"] == 0
            assert boundary["example_violation"] is None

    def test_the_gains(self, report):
        gains = {(b["lower"], b["higher"]): b["gained"]
                 for b in report["boundaries"]}
        assert gains[("substrate", "integer")] == 5883
        assert gains[("integer", "rational")] == 5475
        assert gains[("rational", "griess")] == 0
        assert gains[("griess", "universal")] == 0

    def test_pair_counts_are_consistent(self, report, entries):
        carriers = [e.carrier for e in entries]
        for boundary in report["boundaries"]:
            counts = esc.pair_counts(boundary["lower"], boundary["higher"],
                                     carriers)
            assert boundary["gained"] == counts["lower"] - counts["both"]
            assert boundary["violations"] == counts["higher"] - counts["both"]


class TestTheCeiling:
    """What escalation cannot reach, because the naming is not injective."""

    def test_the_measured_ceiling(self, report):
        ceiling = report["ceiling"]
        assert ceiling["entries"] == 1040
        assert ceiling["distinct_carriers"] == 757
        assert ceiling["unreachable"] == 283
        assert ceiling["collision_classes"] == 104
        assert ceiling["cross_register"] == 0
        assert ceiling["within_register"] == 104

    def test_the_largest_class_is_the_dimensionless_quantities(self, report):
        ceiling = report["ceiling"]
        assert ceiling["largest_class_size"] == 78
        assert ceiling["largest_class_register"] == "physics"
        assert "albedo" in ceiling["largest_class_examples"]

    def test_the_ceiling_is_almost_all_the_physics_register(self, report):
        rows = {r["register"]: r for r in report["by_register"]}
        assert rows["physics"]["unreachable"] == 275
        assert rows["mathematics"]["unreachable"] == 8
        for register in ("chemistry", "molecules", "harmonics", "lexicon"):
            assert rows[register]["unreachable"] == 0
        assert (sum(r["unreachable"] for r in report["by_register"])
                == report["ceiling"]["unreachable"])

    def test_each_register_row_is_that_register_audited_alone(
            self, report, entries, subtests):
        for row in report["by_register"]:
            carriers = [e.carrier for e in entries
                        if e.register == row["register"]]
            with subtests.test(register=row["register"]):
                assert row["entries"] == len(carriers)
                assert row["substrate"] == esc.keyed_resolution(
                    "substrate", carriers)
                assert row["integer"] == esc.keyed_resolution(
                    "integer", carriers)
                assert row["distinct_carriers"] == len(set(carriers))

    def test_colliding_entries_are_indistinguishable_at_every_layer(
            self, entries, subtests):
        groups = {}
        for entry in entries:
            groups.setdefault(entry.carrier, []).append(entry)
        collision = max(groups.values(), key=len)
        a, b = collision[0].carrier, collision[1].carrier
        for layer in DL.LAYERS:
            with subtests.test(layer=layer.name):
                assert IL.indistinguishable(layer, a, b) is True


class TestDescent:
    """Addition descends exactly where the view is the carrier."""

    def test_which_layers_descend(self, report):
        descends = {l["name"]: l["addition_descends"]
                    for l in report["layers"]}
        assert descends == {"substrate": False, "integer": False,
                            "rational": True, "griess": True,
                            "universal": True, "integer_raw": False}

    def test_the_witness_is_a_real_one(self, report, entries):
        carriers = [e.carrier for e in entries]
        for layer in report["layers"]:
            witness = layer["congruence_witness"]
            if witness is None:
                continue
            a, a2, b = (carriers[witness["a"]], carriers[witness["a2"]],
                        carriers[witness["b"]])
            name = layer["name"]
            assert esc.class_key(name, a) == esc.class_key(name, a2)
            assert (esc.class_key(name, IL.carrier_sum(a, b))
                    != esc.class_key(name, IL.carrier_sum(a2, b)))

    def test_a_half_unit_is_what_breaks_the_substrate(self):
        """The Lean witness, run here: floors do not add."""
        half = [Fraction(0)] * 24
        half[0] = Fraction(1, 2)
        vacuum = [Fraction(0)] * 24
        assert esc.class_key("substrate", half) == esc.class_key(
            "substrate", vacuum)
        assert (esc.class_key("substrate", IL.carrier_sum(half, half))
                != esc.class_key("substrate", IL.carrier_sum(vacuum, half)))


class TestTheRejectedReadingAtScale:
    """What the non-cumulative SI7 reading costs when the data is real."""

    def test_it_breaks_refinement_in_bulk(self, report):
        raw = report["non_cumulative"]
        assert raw["refines_substrate"] is False
        assert raw["violations"] == 11176
        assert raw["resolution"] == 359
        assert raw["cumulative_refines_substrate"] is True
        assert raw["cumulative_resolution"] == 544

    def test_the_example_pair_is_a_real_violation(self, report, entries):
        raw = report["non_cumulative"]
        i, j = raw["example_violation"]
        a, b = entries[i].carrier, entries[j].carrier
        assert esc.class_key("integer_raw", a) == esc.class_key(
            "integer_raw", b)
        assert esc.class_key("substrate", a) != esc.class_key("substrate", b)
        assert raw["example_violation_names"] == [entries[i].name,
                                                  entries[j].name]


class TestTheReportSubject:
    """``report escalation`` states what the module computes."""

    def test_the_subject_is_registered(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        assert "escalation" in REPORT_SUBJECTS

    def test_the_solution_states_the_measured_figures(self, report):
        session = GeometricSession()
        solution = session.ask("report escalation")
        expected = solution.expected
        assert expected["carriers"] == str(report["carrier_count"])
        assert expected["distinct_carriers"] == "757"
        assert expected["unreachable"] == "283"
        assert expected["chain_intact"] == "True"
        assert expected["addition_descends"] == "rational,griess,universal"
        assert expected["key_agreement"] == "True"
        assert len(solution.steps) == 8

    def test_the_column_three_template_exists(self):
        from glm_universal.runtime import tct_engine as te
        assert "report_escalation" in te.TEMPLATES

    @pytest.mark.parametrize("surface", ["report escalation", "report scale",
                                         "report ceiling",
                                         "report registers"])
    def test_the_aliases_reach_the_same_subject(self, surface):
        session = GeometricSession()
        assert session.ask(surface).kind == "report"

    @pytest.mark.exhaustive
    def test_the_generated_script_reproduces_column_two(self):
        from glm_universal.runtime import tct_engine as tct
        session = GeometricSession()
        trace = tct.verify_trace(
            tct.build_trace(session.ask("report escalation")))
        assert trace.verdict is not None
        assert trace.verdict.executed
        assert trace.verdict.returncode == 0
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()
        assert trace.verdict.missing_keys == ()

    def test_the_payload_is_json_serialisable(self):
        import json
        session = GeometricSession()
        json.dumps(session.ask("report escalation").payload)
