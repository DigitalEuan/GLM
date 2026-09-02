"""Tests for ``reasoning/wobble`` and its runtime wiring.

The module recomputes the spectral signature the external studies tabulate for
a constant -- entropy, run lengths, transitions, one-density, autocorrelation
-- and checks each measured column against the closed form that produces it.
Those closed forms are theorems of ``RequestProject/GLM/Sturmian.lean``:
``dsBit_eq_floor_diff`` (the stream is the mechanical word of the target),
``dsOnes_eq_floor`` (the ones in ``N`` ticks are exactly ``floor(N t)``),
``ds_zero_run_length_lt`` and ``ds_one_run_length_lt`` (the run bounds),
``dsTransitions_eq``, ``dsMeanRunLength_tendsto``, and
``ds_wobbleEntropy_zero_iff_silent`` together with ``ds_resonance_lock``.

What is checked here is that the code runs the recurrence those theorems are
about, on the studies' own targets, in exact arithmetic -- and that the
measured column and the predicted one agree.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import wobble as wb
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def report():
    return wb.wobble_report()


@pytest.fixture(scope="module")
def table(report):
    return {row["name"]: row for row in report["signatures"]}


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


# ===========================================================================
# 1.  THE STREAM AND ITS COUNT
# ===========================================================================

class TestStream:

    def test_the_stream_is_the_mechanical_word_of_the_target(self):
        """``GLM.Info.dsBit_eq_floor_diff``, checked tick by tick."""
        target = Fraction(3, 7)
        bits = wb.stream_bits(target, 200)
        for n, bit in enumerate(bits):
            lower = ((n + 1) * target).numerator // ((n + 1) * target).denominator
            upper = (n * target).numerator // (n * target).denominator
            assert bit == lower - upper

    def test_the_first_bit_is_always_zero(self):
        """``GLM.Info.dsBit_zero_eq_zero``: the accumulator has to fill."""
        for target in (Fraction(1, 3), Fraction(9, 10), Fraction(1, 2)):
            assert wb.stream_bits(target, 4)[0] == 0

    def test_the_ones_count_is_exactly_the_floor(self):
        """``GLM.Info.dsOnes_eq_floor``: no error term at all."""
        for target in (Fraction(1, 3), Fraction(5, 8), Fraction(97, 100)):
            law = wb.ones_count_law(target, 500)
            assert law["measured"] == law["predicted"]
            assert law["law_holds"]

    def test_a_target_outside_the_unit_interval_is_refused(self):
        with pytest.raises(ValueError):
            wb.stream_bits(Fraction(1, 3), 0)


# ===========================================================================
# 2.  RUNS, TRANSITIONS AND MEAN RUN LENGTH
# ===========================================================================

class TestRuns:

    def test_no_run_reaches_its_bound(self, table):
        """``ds_zero_run_length_lt`` and ``ds_one_run_length_lt``."""
        for row in table.values():
            assert row["longest_zero_run"] <= row["longest_zero_run_bound"]
            assert row["longest_one_run"] <= row["longest_one_run_bound"]

    def test_the_catalogue_maximum_runs_are_reproduced(self, table):
        expected = {"sqrt(2) - 1": 2, "phi - 1": 2, "1/3": 2, "e - 2": 3,
                    "pi - 3": 7, "alpha": 137, "e**pi - pi": 1110}
        for name, longest in expected.items():
            row = table[name]
            assert max(row["longest_zero_run"], row["longest_one_run"]) \
                == longest

    def test_a_low_density_target_never_fires_twice_running(self):
        """``ds_no_adjacent_ones`` for ``t < 1/2``."""
        bits = wb.stream_bits(Fraction(2, 7), 300)
        assert all(not (a and b) for a, b in zip(bits, bits[1:]))

    def test_the_transition_count_matches_its_closed_form(self):
        """``GLM.Info.dsTransitions_eq``."""
        for target in (Fraction(1, 3), Fraction(2, 7), Fraction(1, 5)):
            law = wb.transition_law(target, 400)
            assert law["measured"] == law["predicted"]
            assert law["law_holds"]

    def test_the_mean_run_length_approaches_its_limit(self):
        """``GLM.Info.dsMeanRunLength_tendsto``."""
        law = wb.mean_run_length_law(Fraction(1, 3))
        measured = wb.mean_run_length(wb.stream_bits(Fraction(1, 3), 9999))
        assert abs(measured - law) < Fraction(1, 100)


# ===========================================================================
# 3.  ENTROPY
# ===========================================================================

class TestEntropy:

    def test_entropy_is_zero_exactly_at_the_two_ends(self):
        """``GLM.Info.ds_wobbleEntropy_zero_iff_silent``."""
        assert wb.entropy_bits(Fraction(0))["value"] == 0
        assert wb.entropy_bits(Fraction(1))["value"] == 0
        assert wb.entropy_bits(Fraction(1, 2))["value"] > 0

    def test_entropy_is_maximal_and_equal_to_one_at_a_half(self):
        bracket = wb.entropy_bits(Fraction(1, 2))
        assert abs(bracket["value"] - 1) <= bracket["error"]

    def test_entropy_is_symmetric_under_complementing_the_density(self):
        left = wb.entropy_bits(Fraction(3, 10))
        right = wb.entropy_bits(Fraction(7, 10))
        assert abs(left["value"] - right["value"]) \
            <= left["error"] + right["error"]

    def test_the_catalogue_entropy_column_is_reproduced(self, table):
        expected = {"sqrt(2) - 1": "0.979", "phi - 1": "0.959",
                    "1/3": "0.918", "e - 2": "0.858", "pi - 3": "0.588",
                    "Liouville": "0.500", "alpha": "0.062",
                    "e**pi - pi": "0.011"}
        for name, value in expected.items():
            assert table[name]["entropy_rounded"] == value


# ===========================================================================
# 4.  RENDERING, WHICH NEVER BUILDS A FLOAT
# ===========================================================================

class TestRendering:

    def test_round_str_rounds_half_up(self):
        assert wb.round_str(Fraction(1, 2), 0) == "1"
        assert wb.round_str(Fraction(-1, 2), 0) == "-1"
        assert wb.round_str(Fraction(1, 3), 4) == "0.3333"

    def test_sci_str_renormalises_a_carried_mantissa(self):
        assert wb.sci_str(Fraction(9999, 10000)) == "1.00e+0"
        assert wb.sci_str(Fraction(1, 10 ** 6)) == "1.00e-6"
        assert wb.sci_str(Fraction(0)) == "0"
        assert wb.sci_str(Fraction(-123456)) == "-1.23e+5"


# ===========================================================================
# 5.  THE OSCILLATOR
# ===========================================================================

class TestOscillator:

    def test_the_snr_table_is_the_entropy_of_the_density(self, report):
        expected = {"pure signal": "0.000", "SNR 40 dB": "0.011",
                    "SNR 20 dB": "0.081", "SNR 10 dB": "0.469",
                    "SNR 0 dB": "1.000"}
        for row in report["oscillator"]:
            assert row["entropy_rounded"] == expected[row["condition"]]

    def test_at_lock_the_loop_emits_nothing_but_ones(self, report):
        """``GLM.Info.ds_resonance_lock`` and ``ds_resonance_entropy``."""
        lock = report["resonance"]
        assert lock["first_bit"] == 0
        assert lock["all_ones_after_the_first"]
        assert lock["resonant_entropy"] == 0
        assert lock["entropy_is_zero_only_at_the_ends"]

    def test_the_gain_is_exactly_one_at_resonance(self):
        assert wb.resonance_gain(Fraction(1)) == 1
        assert wb.resonance_gain(Fraction(9, 10)) < 1

    def test_a_non_positive_ratio_or_quality_factor_is_refused(self):
        with pytest.raises(ValueError):
            wb.resonance_gain(Fraction(0))
        with pytest.raises(ValueError):
            wb.resonance_gain(Fraction(1), Fraction(0))

    def test_the_entropy_dip_is_local_to_the_band(self, report):
        rows = {row["ratio"]: row for row in report["resonance_sweep"]}
        assert rows[Fraction(1)]["entropy"] == 0
        assert rows[Fraction(1)]["locked"]
        assert rows[Fraction(9, 10)]["entropy"] > 0
        assert rows[Fraction(11, 10)]["entropy"] > 0
        # ... but far off resonance the gain is near zero and the loop goes
        # quiet again, so the dip is not a global signature.
        assert rows[Fraction(1, 2)]["entropy"] < rows[Fraction(9, 10)]["entropy"]

    def test_no_quality_factor_gives_both_off_resonance_figures(self, report):
        scan = report["resonance_q_scan"]
        assert scan["hits"] == ()
        assert not scan["any_hit"]
        assert scan["best_low_entropy"] == "0.985"
        assert scan["best_high_entropy"] != "0.996"

    def test_a_non_positive_scan_step_is_refused(self):
        with pytest.raises(ValueError):
            wb.resonance_q_scan(step=Fraction(0))


# ===========================================================================
# 6.  THE REPORT AND ITS WIRING
# ===========================================================================

class TestReport:

    def test_every_law_holds_on_every_target(self, report):
        assert report["all_laws_hold"]
        assert report["targets"] == 9
        assert all(row["laws_hold"] for row in report["signatures"])

    def test_the_report_is_recomputed_rather_than_stored(self):
        first = wb.wobble_report(64)
        second = wb.wobble_report(64)
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


class TestRuntimeWiring:

    def test_the_subject_is_registered(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        assert "signature" in REPORT_SUBJECTS

    def test_the_query_answers(self, sess):
        solution = sess.ask("report signature")
        assert solution.kind == "report"
        assert "floor(N t)" in solution.answer
        assert len(solution.steps) == 5

    @pytest.mark.parametrize("surface", ["report spectral", "report resonance",
                                         "report oscillator", "report snr"])
    def test_the_aliases_reach_the_same_subject(self, sess, surface):
        assert sess.ask(surface).kind == "report"

    def test_the_generated_script_reproduces_column_two(self, sess):
        """Column 3 recomputes the signature table in a fresh interpreter."""
        solution = sess.ask("report signature")
        trace = tct.verify_trace(tct.build_trace(solution))
        assert trace.verdict is not None
        assert trace.verdict.executed
        assert trace.verdict.returncode == 0
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()
        assert trace.verdict.missing_keys == ()

    def test_the_payload_is_json_serialisable(self, sess):
        import json
        json.dumps(sess.ask("report signature").payload)
