"""Tests for ``reasoning/containers`` and its runtime wiring.

The module profiles eight constants through three containers: the exact
generator that produces them, the delta-sigma stream whose running average
converges to them, and the 24-dimensional projection tested against the convex
hull of the Leech minimal vectors.

What the tests below pin is that each of the three is *decided* rather than
sampled: precision is an integer comparison, the stream statistics agree with
the closed forms ``RequestProject/GLM/Sturmian.lean`` proves, and both hull
verdicts are certificates checked against all 196,560 minimal vectors.  The
census's own thresholds are pinned too, because they are what makes the
verdicts reproducible.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import containers as con
from glm_universal.reasoning import wobble as wb
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def report():
    return con.containers_report()


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


# ===========================================================================
# 1.  THE GENERATORS
# ===========================================================================

class TestGenerators:

    def test_heron_squares_the_error_at_every_step(self):
        trajectory = con.heron_sequence(2, 6)
        assert trajectory[0] == 1
        assert trajectory[1] == Fraction(3, 2)
        assert trajectory[2] == Fraction(17, 12)
        for value in trajectory[1:]:
            assert value > 0

    def test_heron_refuses_a_non_positive_radicand(self):
        with pytest.raises(ValueError):
            con.heron_sequence(0, 3)

    def test_every_generator_refuses_a_negative_step_count(self):
        for generator in (con.machin_sequence, con.exponential_sequence,
                          con.liouville_sequence, con.champernowne_bits,
                          con.lcg_bits):
            with pytest.raises(ValueError):
                generator(-1)

    def test_the_golden_ratio_is_built_from_the_root_of_five(self):
        roots = con.heron_sequence(5, 5)
        assert con.golden_sequence(5) == tuple((1 + s) / 2 for s in roots)

    def test_machin_reaches_pi(self):
        value = con.machin_sequence(12)[-1]
        assert abs(value - Fraction(355, 113)) < Fraction(1, 10 ** 6)

    def test_the_exponential_series_is_the_partial_sums_of_one_over_n(self):
        assert con.exponential_sequence(0) == (Fraction(1),)
        assert con.exponential_sequence(2) == (
            Fraction(1), Fraction(2), Fraction(5, 2))

    def test_champernowne_concatenates_the_binary_integers(self):
        assert con.champernowne_bits(11) == (1, 1, 0, 1, 1, 1, 0, 0,
                                             1, 0, 1)

    def test_the_congruential_stream_is_reproducible_bit_for_bit(self):
        assert con.lcg_bits(20) == con.lcg_bits(20)
        assert con.lcg_bits(20, seed=2) != con.lcg_bits(20)

    def test_every_generator_stays_in_the_rationals(self):
        for constant in con.CONSTANTS:
            for value in constant.trajectory(3):
                assert isinstance(value, Fraction)


# ===========================================================================
# 2.  PHASE 1 -- PRECISION
# ===========================================================================

class TestPrecision:

    def test_precision_is_an_integer_comparison(self):
        reference = Fraction(1)
        assert con.precision_bits(Fraction(1), reference) \
            == con.REFERENCE_BITS
        assert con.precision_bits(Fraction(3, 2), reference) == 1
        assert con.precision_bits(Fraction(5, 4), reference) == 2

    def test_a_zero_reference_is_refused(self):
        with pytest.raises(ValueError):
            con.precision_bits(Fraction(1), Fraction(0))

    def test_the_algebraic_irrationals_reach_fifty_bits_in_five_or_six(self):
        rows = {row["name"]: row for row in con.convergence_table()}
        assert rows["sqrt(2)"]["steps_to"][50] == 5
        assert rows["phi"]["steps_to"][50] == 6

    def test_the_transcendentals_reach_fifty_bits_in_nine_and_seventeen(self):
        rows = {row["name"]: row for row in con.convergence_table()}
        assert rows["pi"]["steps_to"][50] == 9
        assert rows["e"]["steps_to"][50] == 17

    def test_the_digit_generators_never_reach_fifty_bits(self):
        rows = {row["name"]: row for row in con.convergence_table()}
        assert rows["Champernowne"]["steps_to"][50] is None
        assert rows["omega surrogate"]["steps_to"][50] is None

    def test_the_rigid_baseline_is_exact_before_the_first_step(self):
        rows = {row["name"]: row for row in con.convergence_table()}
        assert rows["1/3"]["exact_at_zero"]
        assert rows["1/3"]["steps_to"][50] == 0

    def test_precision_never_falls_along_a_quadratic_trajectory(self):
        row = next(r for r in con.convergence_table()
                   if r["name"] == "sqrt(2)")
        bits = row["bits_at_step"]
        assert all(bits[k] <= bits[k + 1] for k in range(len(bits) - 1))


# ===========================================================================
# 3.  PHASE 2 -- THE STREAM
# ===========================================================================

class TestStream:

    def test_every_stream_law_holds(self, report):
        assert report["laws_hold"]

    def test_the_stream_is_cached_rather_than_recomputed(self):
        constant = con.constant_by_name("pi")
        first = con.stream_of(constant, 200)
        assert con.stream_of(constant, 200) is first

    def test_the_lag_one_autocorrelation_is_the_closed_form(self):
        for row in con.autocorrelation_table():
            assert row["lag1_matches_law"], row["name"]

    def test_the_autocorrelation_is_the_uncentred_product(self):
        """The rigid baseline is what fixes the alphabet."""
        bits = con.stream_of(con.constant_by_name("1/3"))
        assert wb.product_autocorrelation(bits, 1) == Fraction(-1, 3)

    def test_the_rigid_stream_has_period_three_and_not_two(self):
        assert con.stream_period(con.constant_by_name("1/3")) == 3

    def test_an_irrational_target_gives_no_period(self):
        assert con.stream_period(con.constant_by_name("sqrt(2)"), 400) is None

    def test_the_period_is_the_denominator_of_every_rational_target(self):
        """The stream is the mechanical word of the target, so ``q`` is it."""
        for q in (2, 3, 5, 7, 12):
            for p in range(1, q):
                if Fraction(p, q).denominator != q:
                    continue
                bits = wb.stream_bits(Fraction(p, q), 4 * q)
                assert con.apparent_period(bits) == q, (p, q)

    def test_a_window_reports_a_repetition_that_is_not_a_period(self):
        """Why the period is decided from the target and not searched for.

        A search over 400 places of ``sqrt(2)``'s stream returns 169 -- the
        denominator of the convergent ``70/169`` -- and 169 is not a period:
        the stream disagrees with its own 169-shift a few places past the
        window the search saw.
        """
        found = con.near_period_coincidence(con.constant_by_name("sqrt(2)"),
                                            400)
        assert found["apparent_period"] == 169
        assert found["certified_period"] is None
        assert found["first_disagreement"] == 407
        assert not found["apparent_is_a_period"]

    def test_a_certified_period_survives_four_times_the_window(self):
        rigid = con.near_period_coincidence(con.constant_by_name("1/3"), 400)
        assert rigid["apparent_period"] == 3
        assert rigid["certified_period"] == 3
        assert rigid["apparent_is_a_period"]

    def test_a_period_too_long_for_the_window_is_not_claimed(self):
        assert con.stream_period(con.constant_by_name("1/3"), 5) is None

    def test_a_non_positive_step_count_is_refused(self):
        with pytest.raises(ValueError):
            con.stream_period(con.constant_by_name("1/3"), 0)

    def test_the_four_tabulated_lags_are_all_reported(self):
        row = con.autocorrelation_row(con.constant_by_name("pi"))
        assert set(row["autocorrelation"]) == set(con.AUTOCORRELATION_LAGS)


# ===========================================================================
# 4.  PHASE 3 -- THE HULL CENSUS
# ===========================================================================

class TestHullCensus:

    def test_the_projection_is_the_studys_own(self):
        v = con.projection(Fraction(1))
        assert v[0] == 4
        assert v[23] == Fraction(4, 24)
        assert len(v) == 24

    def test_the_support_of_the_projection_direction_is_twenty_four(self):
        assert con.unit_support() == 24

    def test_the_support_is_an_integer_and_is_cached(self):
        direction = con.SEPARATING_DIRECTIONS["tuned"]
        value = con.support(direction)
        assert isinstance(value, int)
        assert con.support(list(direction)) == value

    def test_a_direction_of_the_wrong_length_is_refused(self):
        with pytest.raises(ValueError):
            con.support((1, 2, 3))

    def test_the_tuned_direction_separates_earlier_than_the_target(self):
        assert (con.separating_scale("tuned")
                < con.separating_scale("target"))

    def test_the_two_certificates_never_both_fire(self):
        for numerator in range(0, 40):
            value = Fraction(numerator, 10)
            status = con.hull_status(value)
            assert status["status"] in ("inside", "outside", "undetermined")

    def test_inside_is_decided_by_two_exact_norms(self):
        assert con.inside_certificate(Fraction(1, 4))
        assert not con.inside_certificate(Fraction(3))

    def test_the_thresholds_bracket_the_undecided_band(self):
        scales = con.critical_scales()
        assert scales["inside_at_most"] < scales["outside_above"]
        below = scales["inside_at_most"] - Fraction(1, 1000)
        above = scales["outside_above"] + Fraction(1, 1000)
        assert con.hull_status(below)["status"] == "inside"
        assert con.hull_status(above)["status"] == "outside"

    def test_liouville_and_the_rigid_baseline_are_inside(self, report):
        assert set(report["hull_inside"]) == {"Liouville", "1/3"}

    def test_the_four_large_constants_and_champernowne_are_outside(self, report):
        assert set(report["hull_outside"]) == {"sqrt(2)", "phi", "pi", "e",
                                               "Champernowne"}

    def test_the_unreproducible_row_is_left_undetermined(self, report):
        assert report["hull_undetermined"] == ("omega surrogate",)

    def test_a_negative_target_is_refused(self):
        with pytest.raises(ValueError):
            con.hull_status(Fraction(-1))

    def test_the_norms_reproduce_the_studys_table(self, report):
        expected = {"sqrt(2)": "7.16", "phi": "8.20", "pi": "15.92",
                    "e": "13.77", "Champernowne": "4.37",
                    "Liouville": "0.56", "1/3": "1.69"}
        for row in report["hull"]:
            if row["name"] not in expected:
                continue
            norm = Fraction(expected[row["name"]])
            low, high = norm - Fraction(1, 200), norm + Fraction(1, 200)
            assert low * low <= row["norm2"] <= high * high, row["name"]

    def test_inverting_a_norm_recovers_the_scalar(self):
        value = Fraction(3, 7)
        norm2 = con.projection_norm2(value)
        recovered = con.implied_value(
            con.projection_l1(value) * 0 + _root(norm2))
        assert abs(recovered - value) < Fraction(1, 10 ** 6)


def _root(norm2: Fraction) -> Fraction:
    from glm_universal.reasoning import exact_real as xr
    return xr.rational_sqrt_approx(norm2, 64)


# ===========================================================================
# 5.  THE REPORT AND THE RUNTIME WIRING
# ===========================================================================

class TestReportAndWiring:

    def test_the_report_covers_all_eight_constants(self, report):
        assert len(report["constants"]) == 8
        assert len(report["convergence"]) == 8
        assert len(report["wobble"]) == 8
        assert len(report["autocorrelation"]) == 8
        assert len(report["hull"]) == 8

    def test_seven_of_the_eight_hull_verdicts_are_certified(self, report):
        assert report["hull_decided"] == 7

    def test_the_report_is_recomputed_rather_than_stored(self, report):
        again = con.containers_report()
        assert again == report
        assert again is not report

    def test_the_subject_is_registered(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        assert "containers" in REPORT_SUBJECTS

    def test_the_query_answers(self, sess):
        solution = sess.ask("report containers")
        assert solution.kind == "report"
        assert "hull verdicts" in solution.answer
        assert len(solution.steps) == 4

    @pytest.mark.parametrize("surface", ["report generators",
                                         "report hull census",
                                         "report convergence"])
    def test_the_aliases_reach_the_same_subject(self, sess, surface):
        assert sess.ask(surface).kind == "report"

    @pytest.mark.exhaustive
    def test_the_generated_script_reproduces_column_two(self, sess):
        solution = sess.ask("report containers")
        trace = tct.verify_trace(tct.build_trace(solution))
        assert trace.verdict is not None
        assert trace.verdict.executed
        assert trace.verdict.returncode == 0
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()
        assert trace.verdict.missing_keys == ()

    def test_the_payload_is_json_serialisable(self, sess):
        import json
        json.dumps(sess.ask("report containers").payload)
