"""Tests for ``reasoning/noise_lab`` and its runtime wiring.

The module stops using the delta-sigma wobble to *represent* a value and
starts using it as the computation: a loop driven by interacting tones rather
than by a constant, the exact condition under which its orbit closes, a
cascaded second loop whose error is a second difference, and dither traded
against an idle tone.

Every claim these tests pin has a machine-checked counterpart in
``RequestProject/GLM/Cascade.lean`` -- ``mAverage_error_le``,
``mState_periodic``, ``casOut_error``, ``casDouble_sum``,
``casTriangular_error_lt`` and ``firstOrder_triangular_error_ge`` -- so what is
checked here is that the code implements the recurrence those theorems are
about, on real inputs, in exact arithmetic.

The vector loop is the same story one dimension up: several coordinates
modulated at once with the quantisation error returned through a rational
matrix, whose three statements are proved in
``RequestProject/GLM/Feedback.lean`` -- ``efAverage_error_le_identity``,
``halfFeedback_dead_zone`` and ``efOut_equivariant``.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import noise_lab as NL
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def report():
    return NL.noise_report()


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


# ===========================================================================
# 1.  SIGNALS
# ===========================================================================

class TestSignals:

    def test_a_square_tone_has_the_offset_as_its_exact_mean(self):
        tone = NL.square_tone(8, Fraction(1, 4), offset=Fraction(1, 2))
        assert tone.period == 8
        assert tone.mean == Fraction(1, 2)
        assert set(tone.values) == {Fraction(3, 4), Fraction(1, 4)}

    def test_a_triangle_tone_has_the_offset_as_its_exact_mean(self):
        tone = NL.triangle_tone(12, Fraction(1, 3), offset=Fraction(1, 2))
        assert tone.period == 12
        assert tone.mean == Fraction(1, 2)

    def test_an_odd_period_is_refused(self):
        with pytest.raises(ValueError):
            NL.square_tone(7, Fraction(1, 4))
        with pytest.raises(ValueError):
            NL.triangle_tone(5, Fraction(1, 4))

    def test_mixing_two_tones_beats_at_the_least_common_multiple(self):
        mix = NL.mix_tones(
            Fraction(1, 2),
            (NL.square_tone(4, Fraction(1, 8), offset=Fraction(0)),
             NL.triangle_tone(6, Fraction(1, 6), offset=Fraction(0))))
        assert mix.period == 12
        assert mix.in_unit_interval

    def test_every_sample_is_exact(self):
        mix = NL.demonstration_mix()
        for value in mix.values:
            assert isinstance(value, Fraction)
            assert not isinstance(value, float)

    def test_a_float_is_refused_outright(self):
        with pytest.raises(TypeError):
            NL.constant_signal(0.5)


# ===========================================================================
# 2.  THE LOOP, DRIVEN BY A SIGNAL
# ===========================================================================

class TestSignalTracking:

    def test_the_accumulator_never_leaves_the_unit_interval(self):
        run = NL.run_signal(NL.demonstration_mix(), 200)
        assert run.state_stayed_in_range
        assert all(0 <= s < 1 for s in run.states)

    def test_the_bits_track_the_input_mean_to_one_over_n(self):
        mix = NL.demonstration_mix()
        for ticks in (16, 64, 128, 251):
            run = NL.run_signal(mix, ticks)
            assert run.error <= Fraction(1, ticks)
            assert run.within_bound

    def test_a_constant_signal_reproduces_the_classical_loop(self):
        from glm_universal.reasoning import exact_real as XR
        target = Fraction(3, 7)
        run = NL.run_signal(NL.constant_signal(target), 64)
        assert run.bits == XR.delta_sigma_bits(target, 64)

    def test_an_input_outside_the_unit_interval_is_refused(self):
        bad = NL.Signal("bad", (Fraction(3, 2),))
        with pytest.raises(ValueError):
            NL.run_signal(bad, 8)

    def test_zero_ticks_is_refused(self):
        with pytest.raises(ValueError):
            NL.run_signal(NL.demonstration_mix(), 0)


# ===========================================================================
# 3.  CLOSED ORBITS
# ===========================================================================

class TestOrbitClosure:

    def test_a_whole_period_sum_closes_the_orbit(self):
        signal = NL.mix_tones(
            Fraction(1, 2),
            (NL.square_tone(4, Fraction(1, 4), offset=Fraction(0)),))
        result = NL.orbit_closure(signal, periods=5)
        assert result["period_sum"] == Fraction(2)
        assert result["period_sum_is_integer"]
        assert result["orbit_closed"]
        assert result["bits_repeat_with_the_period"]
        assert result["criterion_agrees"]

    def test_a_fractional_period_sum_does_not(self):
        signal = NL.mix_tones(
            Fraction(1, 3),
            (NL.square_tone(4, Fraction(1, 8), offset=Fraction(0)),))
        result = NL.orbit_closure(signal, periods=4)
        assert not result["period_sum_is_integer"]
        assert not result["orbit_closed"]
        assert result["criterion_agrees"]

    def test_the_criterion_agrees_on_a_battery_of_signals(self):
        for base in (Fraction(1, 2), Fraction(1, 3), Fraction(3, 8),
                     Fraction(1, 4)):
            for amplitude in (Fraction(1, 8), Fraction(1, 4)):
                signal = NL.mix_tones(
                    base,
                    (NL.square_tone(4, amplitude, offset=Fraction(0)),))
                result = NL.orbit_closure(signal, periods=3)
                if result["period_sum_is_integer"]:
                    assert result["orbit_closed"]


# ===========================================================================
# 4.  THE CASCADE
# ===========================================================================

class TestCascade:

    def test_the_error_is_a_second_difference_at_every_tick(self):
        for target in (Fraction(1, 3), Fraction(2, 5), Fraction(7, 16),
                       Fraction(1, 2)):
            run = NL.cascade_run(target, 96)
            assert run.second_difference_holds

    def test_the_doubly_accumulated_error_is_stage_twos_state(self):
        for target in (Fraction(1, 3), Fraction(3, 7), Fraction(5, 12)):
            for ticks in (8, 33, 64):
                run = NL.cascade_run(target, ticks)
                assert run.double_sum_equals_state
                assert 0 <= run.double_sum < 1

    def test_the_triangular_window_stays_inside_the_proved_bound(self):
        for target in (Fraction(1, 3), Fraction(2, 5), Fraction(9, 20)):
            for ticks in (8, 16, 32, 64, 128):
                run = NL.cascade_run(target, ticks)
                assert run.triangular_error < NL.cascade_bound(ticks)
                assert run.within_bound

    def test_the_output_alphabet_is_within_minus_one_to_two(self):
        for target in (Fraction(1, 3), Fraction(4, 5), Fraction(1, 8)):
            run = NL.cascade_run(target, 64)
            assert all(-1 <= symbol <= 2 for symbol in run.output)

    def test_the_single_loop_stays_above_its_floor_on_one_half(self):
        for ticks in (8, 16, 32, 64, 128, 256):
            error = abs(NL.first_order_triangular(Fraction(1, 2), ticks)
                        - Fraction(1, 2))
            assert error >= NL.first_order_bound(ticks)

    def test_the_cascade_beats_the_single_loop_by_an_order(self, report):
        for row in report["convergence_third"]:
            if row["cascade_error"] == 0:
                continue
            assert row["ratio_single_to_cascade"] == row["window"] - 1

    def test_a_target_outside_the_unit_interval_is_refused(self):
        with pytest.raises(ValueError):
            NL.cascade_run(Fraction(3, 2), 16)

    def test_one_tick_is_refused_since_the_window_needs_two(self):
        with pytest.raises(ValueError):
            NL.cascade_run(Fraction(1, 3), 1)


# ===========================================================================
# 5.  IDLE TONES AND DITHER
# ===========================================================================

class TestToneAndDither:

    def test_the_walsh_spectrum_is_exact_and_integral(self):
        bits = NL.run_signal(NL.constant_signal(Fraction(1, 2)), 64).bits
        spectrum = NL.walsh_spectrum(bits)
        assert len(spectrum) == 64
        assert all(isinstance(c, int) for c in spectrum)

    def test_a_non_power_of_two_window_is_refused(self):
        with pytest.raises(ValueError):
            NL.walsh_spectrum([0, 1, 0])

    def test_one_half_is_a_pure_idle_tone(self):
        bits = NL.run_signal(NL.constant_signal(Fraction(1, 2)), 128).bits
        strength = NL.tone_strength(bits)
        assert strength["peak_fraction"] == Fraction(1)

    def test_the_dither_sequence_is_equidistributed_and_exact(self):
        seq = NL.equidistributed(NL.DITHER_ALPHA, 256)
        assert len(seq) == 256
        assert all(isinstance(x, Fraction) and 0 <= x < 1 for x in seq)
        assert len(set(seq)) == 256

    def test_dither_reduces_the_tone_and_states_its_bias(self):
        run = NL.dither_experiment(Fraction(1, 2), 256, Fraction(3, 4))
        assert run["tone_reduced"]
        assert run["dithered_peak_fraction"] < run["plain_peak_fraction"]
        assert isinstance(run["bias"], Fraction)
        assert run["dithered_within_1_over_N"]

    def test_the_tone_falls_monotonically_with_the_amplitude(self, report):
        sweep = report["dither_sweep"]
        assert sweep["monotone_in_amplitude"]
        assert sweep["amplitudes_that_reduce_the_tone"] == \
            sweep["amplitudes_tried"]
        assert sweep["lowest_peak_fraction"] < \
            sweep["undithered_peak_fraction"]


# ===========================================================================
# 6.  THE REPORT AND ITS WIRING
# ===========================================================================

class TestReport:

    def test_every_measured_identity_holds(self, report):
        assert report["signal_tracking"]["within_bound"]
        assert report["signal_tracking"]["state_stayed_in_range"]
        assert report["cascade"]["second_difference_holds"]
        assert report["cascade"]["double_sum_equals_state"]
        assert report["cascade"]["within_bound"]
        assert report["orbit_closure"]["closing"]["criterion_agrees"]
        assert report["orbit_closure"]["not_closing"]["criterion_agrees"]

    def test_the_report_is_recomputed_rather_than_stored(self):
        first = NL.noise_report()
        second = NL.noise_report()
        assert first == second
        assert first is not second

    def test_no_float_appears_anywhere_in_the_report(self, report):
        def walk(value):
            if isinstance(value, float):
                raise AssertionError(f"a float reached the report: {value!r}")
            if isinstance(value, dict):
                for item in value.values():
                    walk(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    walk(item)
        walk(report)

    def test_the_named_theorems_are_the_ones_that_are_proved(self, report):
        assert set(report["theorems"].values()) == {
            "GLM.Info.mAverage_error_le",
            "GLM.Info.mState_periodic",
            "GLM.Info.casOut_error",
            "GLM.Info.casDouble_sum",
            "GLM.Info.casTriangular_error_lt",
            "GLM.Info.firstOrder_triangular_error_ge",
            "GLM.Feedback.efAverage_error_le_identity",
            "GLM.Feedback.efErr_abs_le_half",
            "GLM.Feedback.halfFeedback_dead_zone",
            "GLM.Feedback.efOut_equivariant",
        }

    def test_the_report_carries_the_error_feedback_section(self, report):
        feedback = report["feedback"]
        assert set(feedback) == {"tracking", "equivariant",
                                 "not_equivariant", "dead_zone"}
        assert feedback["tracking"]["within_bound"]
        assert feedback["tracking"]["errors_bounded"]
        assert feedback["equivariant"]["outputs_permute"]
        assert not feedback["not_equivariant"]["outputs_permute"]
        assert feedback["dead_zone"]["contracting_outputs_all_zero"]


class TestErrorFeedback:
    """The vector loop of ``RequestProject/GLM/Feedback.lean``."""

    def test_the_quantiser_rounds_to_nearest_with_ties_upward(self):
        assert NL.quantise(Fraction(1, 3)) == 0
        assert NL.quantise(Fraction(1, 2)) == 1
        assert NL.quantise(Fraction(-1, 2)) == 0
        assert NL.quantise(Fraction(3, 4)) == 1
        assert NL.quantise(Fraction(-3, 4)) == -1

    def test_the_instantaneous_error_never_leaves_the_half_interval(self):
        """``efErr_abs_le_half``, whatever the feedback matrix is."""
        matrix = NL.scaled_matrix(3, Fraction(7, 3))
        inputs = [(Fraction(k, 7), Fraction(1, 3), Fraction(-2, 5))
                  for k in range(32)]
        run = NL.feedback_run(matrix, inputs)
        assert run.errors_bounded
        for row in run.errors:
            for value in row:
                assert abs(value) <= Fraction(1, 2)

    def test_identity_feedback_tracks_every_coordinate_to_the_bound(self):
        """``efAverage_error_le_identity``: `1/(2N)`, coordinate by coordinate."""
        targets = (Fraction(1, 3), Fraction(2, 5), Fraction(3, 4),
                   Fraction(1, 8))
        run = NL.feedback_tracking(targets, 64)
        assert run.identity_feedback
        assert run.bound == Fraction(1, 128)
        assert run.within_bound
        for target, mean, error in zip(targets, run.input_means,
                                       run.coordinate_errors):
            assert mean == target
            assert error <= run.bound

    def test_the_bound_is_the_one_the_theorem_states(self):
        for ticks in (8, 16, 64):
            run = NL.feedback_tracking((Fraction(1, 3), Fraction(5, 7)), ticks)
            assert run.bound == Fraction(1, 2 * ticks)
            assert run.within_bound

    def test_contracting_the_feedback_kills_the_loop(self):
        """``halfFeedback_dead_zone``: not slower, silent."""
        dead = NL.dead_zone(64)
        assert dead["contracting_outputs_all_zero"]
        assert dead["contracting_error"] == Fraction(1, 4)
        assert not dead["contracting_within_bound"]
        assert dead["identity_fires"]
        assert dead["identity_within_bound"]

    def test_an_invariant_matrix_makes_the_trajectory_equivariant(self):
        """``efOut_equivariant``, and the hypothesis doing work."""
        inputs = [(Fraction(1, 3), Fraction(2, 5), Fraction(3, 4),
                   Fraction(1, 8))] * 32
        permutation = (1, 2, 3, 0)
        symmetric = NL.equivariance_check(NL.identity_matrix(4), inputs,
                                          permutation)
        assert symmetric["matrix_invariant"]
        assert symmetric["outputs_permute"]

        skewed = [[Fraction(1) if i == j else Fraction(0) for j in range(4)]
                  for i in range(4)]
        skewed[0][1] = Fraction(1, 2)
        asymmetric = NL.equivariance_check(skewed, inputs, permutation)
        assert not asymmetric["matrix_invariant"]
        assert not asymmetric["outputs_permute"]

    def test_a_non_permutation_is_refused(self):
        inputs = [(Fraction(1, 3), Fraction(2, 5))] * 4
        with pytest.raises(ValueError):
            NL.equivariance_check(NL.identity_matrix(2), inputs, (0, 0))

    def test_no_float_is_constructed_by_the_feedback_section(self):
        def walk(value):
            if isinstance(value, float):
                raise AssertionError(f"a float reached the report: {value!r}")
            if isinstance(value, dict):
                for item in value.values():
                    walk(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    walk(item)
        walk(NL.feedback_experiment(32))


class TestRuntimeWiring:

    def test_the_subject_is_registered(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        assert "noise" in REPORT_SUBJECTS

    def test_the_query_answers(self, sess):
        solution = sess.ask("report noise")
        assert solution.kind == "report"
        assert "second difference" in solution.answer
        assert "triangular window" in solution.answer
        assert len(solution.steps) == 6

    def test_the_error_feedback_step_is_reported(self, sess):
        solution = sess.ask("report noise")
        assert "error feedback" in solution.steps[-1].label
        assert solution.expected["feedback_within_bound"] == "True"
        assert solution.expected["feedback_equivariant"] == "True"
        assert solution.expected["feedback_not_equivariant"] == "False"
        assert solution.expected["feedback_dead_zone_silent"] == "True"

    @pytest.mark.parametrize("surface", ["report wobble", "report dither",
                                         "report cascade", "report wiggle"])
    def test_the_aliases_reach_the_same_subject(self, sess, surface):
        assert sess.ask(surface).kind == "report"

    def test_the_generated_script_reproduces_column_two(self, sess):
        """Column 3 recomputes the laboratory in a fresh interpreter."""
        solution = sess.ask("report noise")
        trace = tct.verify_trace(tct.build_trace(solution))
        assert trace.verdict is not None
        assert trace.verdict.executed
        assert trace.verdict.returncode == 0
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()
        assert trace.verdict.missing_keys == ()

    def test_the_payload_is_json_serialisable(self, sess):
        import json
        solution = sess.ask("report noise")
        json.dumps(solution.payload)
