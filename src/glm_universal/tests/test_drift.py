"""Tests for ``reasoning/drift`` and its runtime wiring.

The module iterates ``X_(n+1) = r X_n - 1/p`` two hundred times from
``X_0 = 1/p``, for each odd prime and each of the two rules, in three regimes:
exact rational arithmetic, binary64, and binary64 truncated to a display
precision.  The gap between the exact orbit and the others is the drift the
external study tabulates.

Nothing here uses the host's floating point.  The binary64 regime is the
package's own IEEE-754 model (``reasoning/mantissa``), which is why the figures
are exact rationals rather than approximations of approximations.  The Lean
counterpart is ``RequestProject/GLM/Mantissa.lean``: the exact orbit of ``1/p``
under doubling is periodic with period ``ord_2(p)`` while a double's orbit
always collapses to a fixed point -- the same loss, located one step earlier
than this module measures it.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import drift as dft
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def report():
    return dft.drift_report()


@pytest.fixture(scope="module")
def rows(report):
    return {(row["prime"], row["rule"]): row for row in report["table"]}


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


# ===========================================================================
# 1.  ROUNDING, IN INTEGERS ONLY
# ===========================================================================

class TestSignificantRound:

    def test_it_keeps_the_stated_number_of_significant_digits(self):
        assert dft.significant_round(Fraction(1234567, 1000), 4) \
            == Fraction(12350, 10)
        assert dft.significant_round(Fraction(-1, 3), 6) \
            == Fraction(-333333, 10 ** 6)

    def test_zero_is_its_own_rounding(self):
        assert dft.significant_round(Fraction(0), 6) == 0

    def test_a_non_positive_digit_count_is_refused(self):
        with pytest.raises(ValueError):
            dft.significant_round(Fraction(1, 3), 0)


# ===========================================================================
# 2.  THE RECURRENCE
# ===========================================================================

class TestRecurrence:

    def test_the_exact_step_is_the_stated_map(self):
        assert dft.step_exact(Fraction(1, 3), 3, "contractive") \
            == Fraction(2, 3) * Fraction(1, 3) - Fraction(1, 3)
        assert dft.step_exact(Fraction(1, 3), 3, "accumulative") \
            == Fraction(4, 3) * Fraction(1, 3) - Fraction(1, 3)

    def test_an_even_or_too_small_modulus_is_refused(self):
        with pytest.raises(ValueError):
            dft.step_exact(Fraction(1, 2), 2, "contractive")
        with pytest.raises(ValueError):
            dft.step_exact(Fraction(1, 2), 4, "contractive")

    def test_an_unknown_rule_is_refused(self):
        with pytest.raises(ValueError):
            dft.step_exact(Fraction(1, 3), 3, "sideways")

    def test_the_orbit_starts_at_one_over_p_and_has_one_more_point(self):
        orbit = dft.orbit(3, "contractive", 10)
        assert len(orbit) == 11
        assert orbit[0] == Fraction(1, 3)

    def test_the_double_regime_stays_on_the_dyadic_grid(self):
        orbit = dft.orbit(3, "contractive", 20, regime="double")
        for value in orbit:
            denominator = value.denominator
            assert denominator & (denominator - 1) == 0


# ===========================================================================
# 3.  THE DRIFT TABLE
# ===========================================================================

class TestDriftTable:

    def test_the_table_covers_every_prime_and_rule(self, report):
        assert len(report["table"]) == len(dft.ODD_PRIMES) * len(dft.RULES)
        assert report["steps"] == 200

    def test_the_contractive_rule_stays_inside_its_own_resolution(self, report):
        assert report["contractive_stays_under_its_ceiling"]

    def test_truncating_the_display_never_helps(self, report):
        assert report["truncation_never_helps"]
        for row in report["table"]:
            assert row["display4_drift"] >= row["display6_drift"]
            assert row["display6_drift"] >= row["lossless_drift"]

    def test_the_studys_accumulative_figures_are_reproduced(self, rows):
        expected = {
            3: ("7.49e+10", "6.05e+19", "2.22e+22"),
            5: ("4.19e+1", "1.65e+10", "2.05e+12"),
            23: ("2.94e-11", "7.92e-2", "1.53e+0"),
        }
        for prime, (lossless, display6, display4) in expected.items():
            row = rows[(prime, "accumulative")]
            assert row["lossless_drift_sci"] == lossless
            assert row["display6_drift_sci"] == display6
            assert row["display4_drift_sci"] == display4

    def test_the_drift_is_not_the_value(self, rows):
        """The study labels 7.5e10 ``X_200``; it is the row's drift."""
        row = rows[(3, "accumulative")]
        assert row["lossless_drift_sci"] == "7.49e+10"
        assert row["exact_final_sci"] == "-6.48e+24"

    def test_the_contractive_lossless_drift_is_small_but_not_zero(self, rows):
        """The study records ``0.0 exact`` at p = 23; it is not exact."""
        row = rows[(23, "contractive")]
        assert row["lossless_drift"] > 0
        assert row["lossless_drift"] < Fraction(1, 10 ** 16)


# ===========================================================================
# 4.  WHEN THE DRIFT BECOMES MEANINGFUL
# ===========================================================================

class TestOnset:

    def test_the_lossless_regime_survives_to_step_46_at_three(self, report):
        assert report["lossless_onset_at_three"] == 46

    def test_the_lossless_regime_never_diverges_at_the_large_primes(self):
        for prime in (17, 23):
            assert dft.divergence_onset(prime, "accumulative", None) is None

    def test_the_display_regimes_diverge_almost_at_once(self, report):
        """The study says step 1 or 2 everywhere; p = 5 is the exception."""
        assert not report["display_diverges_by_step_two"]
        exceptions = {(e["prime"], e["rule"]): e
                      for e in report["display_onset_exceptions"]}
        assert set(exceptions) == {(5, "contractive"), (5, "accumulative")}
        for entry in exceptions.values():
            assert entry["display6"] == 6
            assert entry["display4"] == 4


# ===========================================================================
# 5.  THE REPORT AND ITS WIRING
# ===========================================================================

class TestReport:

    def test_the_report_is_recomputed_rather_than_stored(self):
        first = dft.drift_report((3,), 20)
        second = dft.drift_report((3,), 20)
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
        assert "drift" in REPORT_SUBJECTS

    def test_the_query_answers(self, sess):
        solution = sess.ask("report drift")
        assert solution.kind == "report"
        assert "truncation never helps" in solution.answer
        assert len(solution.steps) == 4

    @pytest.mark.parametrize("surface", ["report iteration drift",
                                         "report prime drift",
                                         "report divergence"])
    def test_the_aliases_reach_the_same_subject(self, sess, surface):
        assert sess.ask(surface).kind == "report"

    def test_the_generated_script_reproduces_column_two(self, sess):
        """Column 3 recomputes the drift table in a fresh interpreter."""
        solution = sess.ask("report drift")
        trace = tct.verify_trace(tct.build_trace(solution))
        assert trace.verdict is not None
        assert trace.verdict.executed
        assert trace.verdict.returncode == 0
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()
        assert trace.verdict.missing_keys == ()

    def test_the_payload_is_json_serialisable(self, sess):
        import json
        json.dumps(sess.ask("report drift").payload)
