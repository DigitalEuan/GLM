"""Tests for ``reasoning/shell_sigma`` -- delta-sigma on the Leech shells.

The delta-sigma family in ``noise_lab`` emits from a small alphabet, and
``HullExpansion.lean`` records the price: a target outside the hull of the
alphabet is unreachable.  This module widens the alphabet to a shell of the
Leech lattice -- 196,560 points, finite, and covering nothing -- and then to
the whole lattice.

The machine-checked counterparts are in ``RequestProject/GLM/ShellSigma.lean``:

* ``sState_norm_le`` / ``sAverage_error_le`` -- a covering alphabet tracks any
  target at ``rho/N``;
* ``shState_norm_le`` / ``shAverage_error_le`` -- a finite, non-covering
  alphabet tracks a target at ``B/N`` provided the target is inside the hull
  with margin ``mu``, with ``B = D^2/(2 mu) + D``;
* ``gibbsWeight_uniform`` / ``gibbsWeight_le_inv`` / ``gibbsFreq_error_le`` --
  the Gibbs weights and their deterministic realisation.

What is checked here is that the code runs those recurrences on real Leech
data in exact arithmetic, and that the closed-form support function agrees
with a full sweep of the shell.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import shell_sigma as shs
from glm_universal.runtime.session import GeometricSession
from glm_universal.substrate import leech2


@pytest.fixture(scope="module")
def report():
    return shs.shell_sigma_report()


class TestSupportFunction:
    """The shell's support function, in closed form and against a sweep."""

    def test_support_of_a_coordinate_direction_is_four(self):
        direction = [0] * 24
        direction[0] = 1
        result = shs.shell_support(direction)
        assert result["support"] == 4
        assert result["shape"] == "(+-4^2, 0^22)"
        assert result["argmax_norm2"] == 32
        assert result["argmax_in_leech"] is True

    def test_argmax_is_always_on_the_shell(self):
        for probe in shs._sweep(11, 5, 5):
            result = shs.shell_support(probe)
            assert leech2.norm2(result["argmax"]) == 32
            assert leech2.in_leech(result["argmax"]) is True

    def test_support_is_attained_by_its_own_argmax(self):
        for probe in shs._sweep(23, 5, 7):
            result = shs.shell_support(probe)
            v = result["argmax"]
            assert sum(probe[i] * v[i] for i in range(24)) \
                == result["support"]

    def test_closed_form_agrees_with_the_full_sweep(self):
        agreement = shs.support_agreement(2)
        assert agreement["all_agree"] is True
        assert agreement["shell_size"] == 196560

    def test_support_is_positively_homogeneous(self):
        probe = shs._sweep(5, 1, 4)[0]
        base = shs.shell_support(probe)["support"]
        scaled = shs.shell_support([3 * x for x in probe])["support"]
        assert scaled == 3 * base


class TestInsideTheHull:
    """A target strictly inside the hull is tracked at 1/N."""

    def test_target_is_a_shrunk_mean_of_shell_points(self):
        target = shs.inside_target(3)
        assert len(target) == 24
        assert all(isinstance(x, Fraction) for x in target)

    def test_accumulator_stays_bounded(self, report):
        run = report["inside"]["run"]
        assert run["all_on_shell"] is True
        assert run["max_state_norm2"] == max(run["state_norm2_trace"])
        assert run["max_state_norm2"] < 32

    def test_margin_hypothesis_holds_at_every_visited_direction(self, report):
        run = report["inside"]["run"]
        assert run["slack_nonnegative"] is True
        assert run["observed_margin2"] > 0

    def test_error_falls_like_one_over_n(self, report):
        inside = report["inside"]
        # squared error quartering is the 1/N law on the error itself
        assert inside["run"]["error_norm2"] * 4 \
            == inside["half_run_error_norm2"]
        assert inside["error_fell"] is True

    def test_certified_inner_ball_is_exact(self):
        ball = shs.certified_inner_ball()
        assert ball["radius_squared"] == Fraction(2, 3)
        assert ball["tight"] is False


class TestOutsideTheHull:
    """A separating functional is a proof of unreachability."""

    def test_the_certificate(self, report):
        outside = report["outside"]
        assert outside["support_in_direction"] == 4
        assert outside["target_in_direction"] == 5
        assert outside["separated"] is True
        assert outside["gap"] == 1

    def test_accumulator_grows_at_the_gap_per_tick(self, report):
        outside = report["outside"]
        ticks = outside["run"]["ticks"]
        gap = outside["gap"]
        assert outside["run"]["final_state_norm2"] == (gap * ticks) ** 2
        assert outside["state_grew"] is True

    def test_error_does_not_fall(self, report):
        assert report["outside"]["run"]["error_norm2"] == 1


class TestWholeLattice:
    """Widening from the shell to the lattice takes the wall down."""

    def test_accumulator_inside_the_covering_ball(self, report):
        lattice = report["lattice"]
        assert lattice["within_covering_radius"] is True
        assert lattice["max_state_norm2"] <= lattice["covering_radius2"]

    def test_the_unreachable_target_is_reached(self, report):
        lattice = report["lattice"]
        assert lattice["within_bound"] is True
        assert lattice["error_norm2"] <= lattice["error_bound_norm2"]
        assert lattice["all_in_leech"] is True


class TestGibbsRule:
    """Temperature-weighted selection, realised without randomness."""

    def test_uniform_at_temperature_one(self):
        weights = shs.gibbs_weights([0, 1, 2, 5], 1)
        assert weights == (Fraction(1, 4),) * 4

    def test_weights_sum_to_one_and_are_monotone(self):
        for t in (1, 2, 7):
            weights = shs.gibbs_weights([0, 1, 1, 4], t)
            assert sum(weights, Fraction(0)) == 1
            assert weights[0] >= weights[1] == weights[2] >= weights[3]

    def test_non_minimal_weight_is_at_most_one_over_t(self):
        limits = shs.gibbs_limits([0, 2, 3], (1, 2, 8, 64))
        assert limits["uniform_at_t_one"] is True
        for row in limits["rows"]:
            assert row["sums_to_one"] is True
            assert row["monotone_in_energy"] is True
            assert row["within_bound"] is True

    def test_scheduler_hits_its_bound(self):
        weights = shs.gibbs_weights([0, 1, 2, 2], 3)
        sched = shs.gibbs_schedule(weights, 48)
        assert sum(sched["counts"]) == 48
        assert sched["within_bound"] is True
        assert sched["state_sums_to_zero"] is True
        assert sched["state_above_minus_one"] is True

    def test_scheduler_is_exact_on_rational_weights(self):
        sched = shs.gibbs_schedule(
            (Fraction(1, 2), Fraction(1, 4), Fraction(1, 4)), 40)
        assert sched["counts"] == (20, 10, 10)
        assert sched["max_frequency_error"] == 0

    def test_geometric_instance(self, report):
        gibbs = report["gibbs"]
        assert gibbs["all_on_shell"] is True
        assert gibbs["energies"][0] == 0
        for row in gibbs["rows"]:
            assert row["within_bound"] is True
        assert gibbs["rows"][0]["max_frequency_error"] == 0

    def test_falling_temperature_concentrates(self, report):
        rows = report["gibbs"]["rows"]
        assert rows[0]["weights"][0] < rows[-1]["weights"][0]


class TestRuntimeWiring:
    """``report shells`` reaches the study and reproduces it."""

    def test_subject_is_registered(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        assert "shells" in REPORT_SUBJECTS

    def test_report_answers(self):
        session = GeometricSession()
        solution = session.ask("report shells")
        assert solution.kind == "report"
        assert "support function" in solution.answer
        assert "unreachable" in solution.answer
        assert len(solution.steps) == 6

    def test_expected_values_carry_the_headline_numbers(self):
        session = GeometricSession()
        expected = session.ask("report shells").expected
        assert expected["shell_size"] == "196560"
        assert expected["outside_separated"] == "True"
        assert expected["outside_support"] == "4/1"
        assert expected["lattice_within_bound"] == "True"
        assert expected["gibbs_within_bound"] == "True"

    def test_aliases_reach_the_same_solver(self):
        session = GeometricSession()
        head = session.ask("report shells").answer
        for alias in ("report gibbs", "report leech noise",
                      "report lattice alphabet"):
            assert session.ask(alias).answer == head
