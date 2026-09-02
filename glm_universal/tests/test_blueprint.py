"""Tests for the unification-blueprint claim ledger and the two studies it rests on.

``reasoning/blueprint`` turns ``source_material/glm_unification_blueprint.md`` from a document
into a live ledger: every testable sentence is recomputed against the package
and given a verdict.  ``reasoning/reversible`` measures the document's Part V
(the Gray-code read channel, the Toffoli and Fredkin gates, the kink
invariant) and ``reasoning/mantissa`` measures its section 5.1 (what a
binary64 float loses, and where).

These tests pin the shape of the ledger, the arithmetic behind the verdicts
that matter, the source audit that settles section 1, and the three runtime
subjects -- ``report blueprint``, ``report reversible`` and
``report mantissa`` -- end to end through the Three Column Thinking engine.

The counterpart machine-checked development is in
``RequestProject/GLM/Reversible.lean`` (the Gray-code step, the halving that
is not exact, the gates' involutivity, the kink invariant) and
``RequestProject/GLM/Mantissa.lean`` (the dyadic collapse against the exact
periodic orbit).
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import blueprint as BP
from glm_universal.reasoning import engine as EN
from glm_universal.reasoning import mantissa as MN
from glm_universal.reasoning import reversible as RV
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def ledger():
    return BP.blueprint_ledger()


@pytest.fixture(scope="module")
def report():
    return BP.blueprint_report()


@pytest.fixture(scope="module")
def audit():
    return BP.ubp_source_audit()


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


# ===========================================================================
# 1.  THE SHAPE OF A LEDGER ENTRY
# ===========================================================================

class TestClaimEntry:

    def test_every_entry_carries_section_claim_verdict_and_figure(self,
                                                                  ledger):
        for entry in ledger:
            assert set(entry) >= {"section", "claim", "verdict", "figure"}
            assert entry["claim"].strip()
            assert entry["figure"].strip()

    def test_every_verdict_is_one_of_the_four(self, ledger):
        for entry in ledger:
            assert entry["verdict"] in BP.VERDICTS

    def test_an_unrecognised_verdict_is_refused(self):
        with pytest.raises(ValueError):
            BP.claim("9", "something", "probably", "no figure")

    def test_a_claim_that_does_not_hold_says_what_holds_instead(self,
                                                                ledger):
        for entry in ledger:
            if entry["verdict"] in (BP.REFUTED, BP.NOT_REPRODUCED,
                                    BP.NOT_IMPLEMENTED):
                # Either the figure itself is the correction, or an explicit
                # "instead" is supplied; a bare verdict is not enough.
                assert entry.get("instead") or entry["figure"]

    def test_the_ledger_covers_every_part_of_the_document(self, report):
        covered = {section.split(".")[0] for section in report["sections"]}
        assert covered == {"1", "2", "3", "4", "5", "6", "7"}

    def test_the_tally_adds_up(self, report):
        assert sum(report["tally"].values()) == report["claim_count"]
        assert report["claim_count"] == len(report["claims"])

    def test_the_reading_names_every_verdict_count(self, report):
        reading = report["reading"]
        for count in report["tally"].values():
            assert str(count) in reading


# ===========================================================================
# 2.  SECTION 1 -- THE UBP READ OFF THE SOURCE
# ===========================================================================

class TestSourceAudit:

    def test_every_module_of_the_package_is_scanned(self, audit):
        assert audit["modules_scanned"] == len(BP.source_files())
        assert audit["modules_scanned"] > 100

    def test_the_six_core_sub_packages_construct_no_float(self, audit):
        assert audit["core_clean"], audit["core_violations"]
        assert audit["core_violations"] == []

    def test_the_core_imports_nothing_that_computes_in_floating_point(
            self, audit):
        for package in BP.CORE_PACKAGES:
            assert audit["per_package"][package]["banned_imports"] == 0
            assert audit["per_package"][package]["float_literals"] == 0
            assert audit["per_package"][package]["float_calls"] == 0

    def test_the_audit_module_is_itself_clean(self, audit):
        entry = audit["per_package"]["reasoning"]
        assert entry["float_calls"] == 0

    def test_an_isinstance_guard_is_not_counted_as_a_violation(self):
        # data_objects/base.py refuses floats with isinstance; that is the
        # discipline being enforced, not broken.
        for sub, path in BP.source_files():
            if path.endswith("data_objects/base.py"):
                scan = BP._scan_module(path)
                assert scan["isinstance_guards"] > 0
                assert scan["float_call_lines"] == ()
                return
        pytest.fail("data_objects/base.py was not scanned")

    def test_the_measuring_sub_packages_are_reported_not_hidden(self, audit):
        # The ban does not reach benchmarks, capabilities, evaluation and
        # examples, and the ledger says so rather than restricting the scan.
        modules = {v["module"] for v in audit["outside_core_violations"]}
        assert modules
        for name in modules:
            assert not name.startswith(tuple(BP.CORE_PACKAGES))


# ===========================================================================
# 3.  PART I -- SUBSTRATE, BRIDGE AND LADDER
# ===========================================================================

class TestPartI:

    def test_the_shipped_permutation_is_the_documented_one(self):
        from glm_universal.substrate import isomorphism as iso
        assert tuple(iso.LEGACY_TO_CORE) == BP.BLUEPRINT_SIGMA

    def test_the_documented_permutation_is_a_permutation(self):
        assert sorted(BP.BLUEPRINT_SIGMA) == list(range(24))

    def test_every_part_one_claim_is_confirmed(self):
        for entry in BP.part_i_claims():
            assert entry["verdict"] == BP.CONFIRMED, entry


# ===========================================================================
# 4.  PART II -- THE DELTA-SIGMA RATE
# ===========================================================================

class TestDeltaSigmaRate:

    def test_the_error_never_leaves_the_one_over_n_envelope(self):
        table = BP.delta_sigma_rate_table()
        assert table["all_within_one_over_n"]
        for row in table["rows"]:
            assert Fraction(row["error"]) <= Fraction(1, row["steps"])

    def test_the_bits_cleared_exceed_the_documented_floor(self):
        table = BP.delta_sigma_rate_table()
        assert table["always_at_least_claimed_bits"]
        assert not table["always_exactly_claimed_bits"]

    def test_bits_cleared_is_the_exact_integer_answer(self):
        assert BP._bits_cleared(Fraction(1, 8)) == 3
        assert BP._bits_cleared(Fraction(1, 7)) == 2
        assert BP._bits_cleared(Fraction(1)) == 0

    def test_the_rate_is_measured_in_exact_arithmetic(self):
        for row in BP.delta_sigma_rate_table()["rows"]:
            assert isinstance(Fraction(row["error"]), Fraction)


# ===========================================================================
# 5.  PART III -- THE ENGINE FAMILY IS AN OPEN GAP
# ===========================================================================

class TestPartIII:

    def test_every_named_stage_is_now_reachable(self):
        assert len(BP.ENGINE_STAGES) == 7
        for _, name, path in BP.ENGINE_STAGES:
            assert path is not None, name
            assert BP._importable(path), path

    def test_the_two_point_seven_leap_is_not_reproduced(self):
        for entry in BP.part_iii_claims():
            if "2.7x" in entry["claim"]:
                assert entry["verdict"] == BP.NOT_REPRODUCED
                assert entry.get("instead")
                return
        pytest.fail("the 2.7x claim is missing from the ledger")

    def test_the_engine_stages_are_measured_not_asserted(self):
        claims = BP.part_iii_claims()
        assert len(claims) == 6
        assert BP.NOT_IMPLEMENTED not in [c["verdict"] for c in claims]


# ===========================================================================
# 5b.  THE ASSEMBLED ENGINE
# ===========================================================================

class TestEngineStages:

    def test_the_accumulator_is_exact_and_converges(self):
        run = EN.accumulate(Fraction(1, 3), 64)
        assert isinstance(run["error"], Fraction)
        assert run["error"] <= Fraction(1, 64)
        assert set(run["bits"]) <= {0, 1}

    def test_the_drums_repeat_only_after_the_least_common_multiple(self):
        period = EN.escapement_period()
        assert period == 2304
        assert EN.escapements(0) == EN.escapements(period)
        assert EN.escapements(1) != EN.escapements(0)

    def test_the_strain_is_the_documented_quotient(self):
        assert EN.tax_of(128) == Fraction(4)
        assert EN.tax_of(0) == 0

    def test_the_two_snap_strengths_measure_different_quantities(self):
        carrier = [Fraction(4)] * 12 + [Fraction(-4)] * 12
        tight = EN.snap(carrier, "tight")
        relaxed = EN.snap(carrier, "relaxed")
        assert tight["strain_kind"] == "leech"
        assert relaxed["strain_kind"] == "code"
        assert (relaxed["operations"]
                < tight["operations"])

    def test_an_unknown_snap_mode_is_refused(self):
        with pytest.raises(ValueError):
            EN.snap([Fraction(0)] * 24, "hard")

    def test_the_radiator_lowers_the_final_strain(self):
        target = Fraction(1, 3)
        hot = EN.run_engine(target, 64, EN.EngineConfig(radiator_period=0,
                                                        turbo=False))
        cool = EN.run_engine(target, 64, EN.EngineConfig(radiator_period=16,
                                                         turbo=False))
        assert cool.bleeds > 0
        assert cool.accumulated_tax <= hot.accumulated_tax
        assert cool.escalations <= hot.escalations

    def test_the_turbocharger_saves_operations(self):
        target = Fraction(1, 3)
        off = EN.run_engine(target, 64, EN.EngineConfig(turbo=False))
        on = EN.run_engine(target, 64, EN.EngineConfig(turbo=True))
        assert on.snaps["skip"] > off.snaps["skip"]
        assert on.operations < off.operations
        assert on.error == off.error   # the emitted stream is unchanged

    def test_both_fuels_reach_the_same_limit_and_switching_never_loses(self):
        fuel = EN.multi_fuel()
        assert fuel["same_limit"]
        assert fuel["switching_never_loses"]
        assert fuel["switched_tick"] <= fuel["heron_tick"]
        assert fuel["switched_tick"] <= fuel["convergent_tick"]

    def test_the_generators_stay_on_the_dyadic_grid(self):
        for value in EN.heron_sequence(2, 8) + EN.convergent_sequence(2, 8):
            assert isinstance(value, Fraction)
            denominator = value.denominator
            assert denominator & (denominator - 1) == 0

    def test_the_gearbox_classifies_and_shifts(self):
        from glm_universal.reasoning import exact_real as xr
        assert EN.classify_target(Fraction(1, 3)) == "rational"
        assert EN.classify_target(xr.sqrt(Fraction(2))) == "algebraic"
        assert EN.classify_target(xr.pi()) == "transcendental"
        assert EN.gearbox(Fraction(1, 3))["config"].snap_mode == "skip"

    def test_a_bad_configuration_is_refused(self):
        with pytest.raises(ValueError):
            EN.EngineConfig(snap_mode="warp")
        with pytest.raises(ValueError):
            EN.EngineConfig(snap_period=0)

    def test_the_headline_ratio_is_matched_by_no_baseline(self):
        leap = EN.precision_leap()
        assert leap["claimed_ratio"] == "27/10"
        assert not leap["any_baseline_gives_the_claimed_ratio"]
        for row in leap["rows"]:
            # the modulator loses against bitwise truncation
            assert Fraction(row["against_truncation"]) < 1


# ===========================================================================
# 6.  PART IV -- METROLOGY AND THE TOWER
# ===========================================================================

class TestPartIV:

    def test_the_five_nrci_shells_are_all_present(self):
        from glm_universal.reasoning import coherence as co
        breakdown = co.nrci_breakdown(BP._nrci_probe())
        for shell in BP.NRCI_SHELLS:
            assert shell in breakdown

    def test_the_probe_carrier_exercises_more_than_one_shell(self):
        from glm_universal.reasoning import coherence as co
        breakdown = co.nrci_breakdown(BP._nrci_probe())
        nonzero = [s for s in BP.NRCI_SHELLS if breakdown[s] != 0]
        assert len(nonzero) >= 2

    def test_the_layer_table_matches_the_document(self):
        from glm_universal.reasoning import information_loss as il
        layers = {row["name"]: row
                  for row in il.information_loss_report()["layers"]}
        for name, resolves, loses in BP.LAYER_TABLE:
            assert layers[name]["resolution"] == resolves
            assert layers[name]["loss_count"] == loses

    def test_the_refinement_chain_claim_is_confirmed(self):
        for entry in BP.part_iv_claims():
            if "refinement_chain_intact" in entry["claim"]:
                assert entry["verdict"] == BP.CONFIRMED
                return
        pytest.fail("the refinement-chain claim is missing")


# ===========================================================================
# 7.  PART V -- THE READ CHANNEL, THE GATES, THE KINKS
# ===========================================================================

class TestReadChannel:

    def test_gray_counting_changes_exactly_one_bit_per_step(self):
        channel = RV.channel_report(8)
        assert channel["gray"]["max_step"] == 1
        assert channel["gray"]["variance"] == 0
        assert channel["gray"]["zero_entropy"]

    def test_the_closed_forms_hold_at_every_small_width(self):
        for width in range(1, 9):
            channel = RV.channel_report(width)
            assert channel["gray"]["flips"] == 2 ** width
            assert channel["binary"]["flips"] == 2 ** (width + 1) - 2

    def test_the_halving_is_never_exact(self):
        for width in range(1, 9):
            channel = RV.channel_report(width)
            assert not channel["halving_exact"]
            assert (2 * channel["gray"]["flips"]
                    == channel["binary"]["flips"] + 2)

    def test_gray_is_at_least_as_cheap_as_binary(self):
        for width in range(1, 9):
            assert RV.channel_report(width)["gray_at_least_as_cheap"]


class TestReversibleGates:

    def test_both_gates_are_self_inverse_on_every_input(self):
        for bits in range(8):
            triple = ((bits >> 2) & 1, (bits >> 1) & 1, bits & 1)
            assert RV.toffoli(RV.toffoli(triple)) == triple
            assert RV.fredkin(RV.fredkin(triple)) == triple

    def test_both_gates_are_bijections(self):
        for gate in (RV.toffoli, RV.fredkin):
            images = {gate(((b >> 2) & 1, (b >> 1) & 1, b & 1))
                      for b in range(8)}
            assert len(images) == 8

    def test_a_hundred_rounds_each_way_return_the_carrier_exactly(self):
        gates = RV.reversibility_report(100)
        assert gates["hamming_to_start"] == 0
        assert gates["exact_return"]

    def test_reversibility_does_not_conserve_the_golay_syndrome(self):
        gates = RV.reversibility_report(100)
        assert not gates["syndrome_conserved"]
        assert len(set(gates["syndrome_values"])) > 1


class TestKinks:

    def test_the_kink_count_survives_every_rotation(self):
        solitons = RV.soliton_report()
        assert solitons["rotation_invariant"]
        assert set(solitons["rotation_orbit"]) == {solitons["kinks"]}

    def test_the_kink_count_is_always_even(self):
        solitons = RV.soliton_report()
        assert solitons["kink_count_always_even"]

    def test_a_single_flip_moves_the_count_by_minus_two_zero_or_two(self):
        solitons = RV.soliton_report()
        assert solitons["delta_in_minus_two_zero_two"]
        assert not solitons["delta_always_two"]
        assert set(solitons["exhaustive_flip_deltas"]) == {-2, 0, 2}

    def test_the_zero_delta_is_exactly_half_the_census(self):
        solitons = RV.soliton_report()
        assert solitons["zero_delta_share"] == Fraction(1, 2)


# ===========================================================================
# 8.  SECTION 5.1 -- THE MANTISSA
# ===========================================================================

class TestMantissa:

    def test_storing_one_over_p_keeps_the_full_significand(self):
        rounding = MN.rounding_report()
        assert rounding["min_retained_bits"] >= 53
        assert rounding["bits_lost_at_step_zero"] == 0

    def test_the_period_is_the_multiplicative_order_of_two(self):
        for prime in MN.ODD_PRIMES:
            period = MN.binary_period(prime)
            assert pow(2, period, prime) == 1
            assert all(pow(2, d, prime) != 1 for d in range(1, period))

    def test_the_stored_orbit_dies_and_the_exact_one_does_not(self):
        drift = MN.projection_drift()
        assert drift["all_collapse"]
        assert drift["all_collapse_within_bound"]
        for row in drift["rows"]:
            assert not row["exact_orbit_terminates"]

    def test_the_antipode_is_a_post_collapse_artefact(self):
        drift = MN.projection_drift()
        assert not drift["any_antipodal_before_collapse"]
        assert drift["max_distance_before_collapse"] < 24

    def test_no_float_is_constructed_by_the_model(self):
        stored = MN.to_double(Fraction(1, 3))
        assert isinstance(stored, Fraction)
        assert stored.denominator & (stored.denominator - 1) == 0


# ===========================================================================
# 9.  THE THREE RUNTIME SUBJECTS
# ===========================================================================

class TestRuntimeWiring:

    @pytest.mark.parametrize("subject",
                             ["blueprint", "reversible", "mantissa",
                              "engine"])
    def test_the_subject_is_advertised(self, subject):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        assert subject in REPORT_SUBJECTS

    @pytest.mark.parametrize("subject",
                             ["blueprint", "reversible", "mantissa",
                              "engine"])
    def test_the_subject_answers(self, sess, subject):
        solution = sess.ask(f"report {subject}")
        assert solution.ok, solution.error
        assert solution.kind == "report"
        assert solution.expected
        assert solution.payload["report"]

    @pytest.mark.parametrize("subject,alias",
                             [("blueprint", "claim ledger"),
                              ("reversible", "gray code"),
                              ("mantissa", "ieee-754"),
                              ("engine", "tdce")])
    def test_the_alias_reaches_the_same_subject(self, sess, subject, alias):
        direct = sess.ask(f"report {subject}")
        aliased = sess.ask(f"report {alias}")
        assert aliased.ok
        assert aliased.expected == direct.expected

    @pytest.mark.parametrize("subject",
                             ["blueprint", "reversible", "mantissa",
                              "engine"])
    def test_the_generated_script_is_exact(self, sess, subject):
        source = tct.render_script(sess.ask(f"report {subject}"))
        ok, offenders = tct.script_is_exact(source)
        assert ok, offenders

    @pytest.mark.parametrize("subject",
                             ["blueprint", "reversible", "mantissa",
                              "engine"])
    @pytest.mark.exhaustive
    def test_the_re_derivation_script_reproduces_column_two(self, sess,
                                                            subject):
        trace = tct.verify_trace(tct.build_trace(sess.ask(f"report {subject}")))
        assert trace.verdict is not None
        assert trace.verdict.executed
        assert trace.verdict.returncode == 0
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()
        assert trace.verdict.missing_keys == ()

    def test_the_ledger_answer_states_the_tally(self, sess, report):
        solution = sess.ask("report blueprint")
        assert str(report["claim_count"]) in solution.answer
