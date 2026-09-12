"""Tests for ``reasoning/wobble_landscape`` -- the pre-registered study.

The study document ``studies/WOBBLE_LANDSCAPE_STUDY.md`` fixes one statistic,
two nulls, a two-sided tail and a gate before any measurement.  These tests pin
the parts of that machinery which have to be *right* rather than merely
reported:

* the **closed-form gap spectrum** against a finite simulated run -- and, so
  that a passing comparison is evidence rather than a tautology, the same
  comparison against a *perturbed* closed form, which must fail;
* the **exact Golay null**: ``4096 * (1 + 24 + 276 + 2024) = 9,523,200`` of
  ``2**24``, a probability of ``2325/4096``, recomputed from the code's own
  coset census (``GLM.Landscape.golay_code_ball_count``);
* the **bit score recomputed from its own tables**: the tail is re-derived by
  counting the null again from scratch, and ``B`` is re-derived from that tail;
* **chance in closed form**: the ``k``-sweep null has ``S = 1/k`` exactly, so
  its tail can be written down without enumerating anything, and the two
  agree;
* **no float anywhere** in the module, by the static instrument of directive
  D7.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import transcendental as tr
from glm_universal.reasoning import wobble as wb
from glm_universal.reasoning import wobble_landscape as wl
from glm_universal.substrate import golay_decode as gd
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession, REPORT_SUBJECTS


@pytest.fixture(scope="module")
def report():
    return wl.landscape_report()


# ---------------------------------------------------------------------------
#  1.  The closed-form gap spectrum, against the run
# ---------------------------------------------------------------------------

def test_gap_spectrum_matches_simulation_for_alpha():
    check = wl.gap_spectrum_check(wl.ALPHA, 20_000)
    assert check["short_gap"] == 137
    assert check["long_gap"] == 138
    assert check["distinct_lengths"] == (137, 138)
    assert check["lengths_hold"]
    assert check["long_observed"] == check["long_closed_form"]
    assert check["holds"]


@pytest.mark.parametrize("slope", [
    Fraction(1, 3), Fraction(2, 7), Fraction(355, 113) - 3,
    Fraction(17, 71), Fraction(4, 9),
])
def test_gap_spectrum_matches_simulation_across_slopes(slope):
    check = wl.gap_spectrum_check(slope, 2_000)
    assert check["holds"]
    assert set(check["distinct_lengths"]) <= {check["short_gap"],
                                              check["long_gap"]}


def test_the_comparison_would_catch_a_wrong_closed_form():
    """A perturbed closed form must disagree with the run.

    Without this the agreement above would be untested machinery: a comparison
    that cannot fail is not a check.
    """
    slope = Fraction(17, 71)
    observed = wl.simulated_gaps(slope, 2_000)
    short = wl.gap_spectrum(slope)["short_gap"]
    long_observed = sum(1 for gap in observed if gap == short + 1)
    honest = wl.long_gap_count(slope, len(observed))
    assert long_observed == honest
    assert long_observed != honest + 1
    #  and the two-length bound is refutable too: a stream really can be
    #  checked against the wrong pair of lengths
    assert not all(gap in (short + 3, short + 4) for gap in observed)


def _ceil(value: Fraction) -> int:
    return -((-value.numerator) // value.denominator)


def test_long_gap_count_is_the_telescoping_sum():
    """``ceil((K+1) t_1) - 1`` is the sum of the gaps minus ``K a_0``."""
    for target in (Fraction(1, 7), Fraction(3, 41), wl.ALPHA):
        t = wl.slope(target)
        spectrum = wl.gap_spectrum(t)
        reciprocal = 1 / t
        for gaps in (1, 5, 37, 200):
            total = sum(_ceil((j + 1) * reciprocal) - _ceil(j * reciprocal)
                        for j in range(1, gaps + 1))
            expected = total - gaps * spectrum["short_gap"]
            assert wl.long_gap_count(t, gaps) == expected


def test_ostrowski_ladder_is_the_continued_fraction():
    ladder = wl.ostrowski_ladder(wl.slope(wl.ALPHA), 6)
    quotients = tuple(row["short_gap"] for row in ladder)
    assert quotients == wl.continued_fraction(1 / wl.ALPHA, 6)
    assert quotients[0] == 137


def test_continued_fraction_of_one_over_alpha():
    """Computed, not copied: the brief's ``[137; 28, 1, 1, 2, 1, 1, 4]`` is not
    the expansion of the CODATA 2022 value."""
    expansion = wl.continued_fraction(1 / wl.ALPHA, 8)
    assert expansion[:3] == (137, 27, 1)
    assert expansion[1] != 28


def test_depth_profile_settles_on_the_closed_form():
    rows = wl.depth_profile(wl.ALPHA)
    assert tuple(row["gaps"] for row in rows) == wl.DEPTH_SWEEP
    assert rows[-1]["error"] < rows[0]["error"]
    for row in rows:
        assert row["error"] <= Fraction(1, row["gaps"])


# ---------------------------------------------------------------------------
#  2.  The statistic, and the entropy it replaces
# ---------------------------------------------------------------------------

def test_statistic_is_the_fractional_part_of_the_reciprocal():
    assert wl.statistic(wl.ALPHA) == 1 / wl.ALPHA - 137
    assert wl.deviation(wl.ALPHA) == abs(wl.statistic(wl.ALPHA)
                                         - Fraction(1, 2))


def test_entropy_is_only_the_magnitude_and_is_not_the_statistic(report):
    """The catalogue's 0.062 is `H2(alpha)`, correctly computed and empty."""
    assert report["entropy_rounded"] == "0.062"
    shifted = wb.entropy_bits(wl.slope(wl.ALPHA + 1000))
    assert wb.round_str(shifted["value"], 3) == "0.062"
    #  two numbers with the same fractional part share it to the last bit
    assert wl.statistic(wl.ALPHA) == wl.statistic(wl.ALPHA + 1000)


def test_run_length_is_the_leading_partial_quotient(report):
    assert report["run_length"] == 137
    assert report["run_length"] == wl.continued_fraction(1 / wl.ALPHA, 1)[0]


# ---------------------------------------------------------------------------
#  3.  The nulls, and chance in closed form
# ---------------------------------------------------------------------------

def test_stride_null_is_exhaustive_and_inside_the_interval():
    members = wl.stride_null()
    assert len(members) == 1066
    assert all(wl.NULL_LOW < member < wl.NULL_HIGH for member in members)
    assert all(member.denominator <= wl.STRIDE for member in members)
    #  nothing is missing: the count is the number of integers in the range
    low = wl.STRIDE * wl.NULL_LOW
    high = wl.STRIDE * wl.NULL_HIGH
    first = low.numerator // low.denominator + 1
    last = -((-high.numerator) // high.denominator) - 1
    assert len(members) == last - first + 1


def test_k_sweep_statistic_is_one_over_k_exactly():
    """Chance in closed form: for ``1/(137 + 1/k)`` the statistic is ``1/k``.

    ``k = 1`` is the one degenerate member -- ``[137; 1]`` is the integer 138,
    the word is periodic and there is only one gap length -- and the module
    reports a long-gap frequency of zero for it rather than raising.
    """
    for k in (2, 27, 28, 100):
        member = 1 / (Fraction(137) + Fraction(1, k))
        assert wl.statistic(member) == Fraction(1, k)
    assert wl.statistic(1 / (Fraction(137) + 1)) == 0


def test_k_sweep_tail_matches_its_closed_form():
    members = wl.k_sweep_null()
    measured = wl.null_tail(members, wl.deviation(wl.ALPHA))
    spread = wl.deviation(wl.ALPHA)
    closed = sum(1 for k in range(1, wl.K_SWEEP + 1)
                 if abs((Fraction(1, k) if k > 1 else Fraction(0))
                        - Fraction(1, 2)) >= spread)
    assert measured["at_least_as_extreme"] == closed
    assert measured["tail"] == Fraction(closed, wl.K_SWEEP)


def test_primary_tail_recounted_from_scratch(report):
    """The bit score is recomputed from its own tables, not quoted."""
    primary = report["primary"]["primary_null"]
    spread = wl.deviation(wl.ALPHA)
    recount = sum(1 for member in wl.stride_null()
                  if abs(wl.statistic(member) - Fraction(1, 2)) >= spread)
    assert primary["at_least_as_extreme"] == recount
    assert primary["tail"] == Fraction(recount, primary["members"])
    assert primary["tail"] == Fraction(77, 1066)


def test_bit_score_recomputed_from_the_tail(report):
    primary = report["primary"]["primary_null"]
    fresh = wl.bit_score(primary["tail"], wl.STATISTICS_TRIED)
    assert fresh["raw"] == primary["score"]["raw"]
    assert fresh["corrected"] == primary["score"]["corrected"]
    #  and the bracket really does contain log2(1/p)
    inverse = 1 / primary["tail"]
    reference = (tr.rational_log_approx(inverse, 60)
                 / tr.log_two_approx(60))
    assert abs(fresh["raw"] - reference) <= fresh["raw_error"]
    assert fresh["corrected"] == fresh["raw"] - wl.log2_bracket(
        Fraction(wl.STATISTICS_TRIED))["value"]


def test_bit_score_is_antitone_and_pinned_at_one():
    assert wl.bit_score(Fraction(1), 1)["raw"] == 0
    previous = None
    for tail in (Fraction(1, 1000), Fraction(1, 100), Fraction(1, 10),
                 Fraction(1, 2), Fraction(1)):
        score = wl.bit_score(tail, 1)["raw"]
        if previous is not None:
            assert score <= previous
        previous = score


def test_log2_bracket_agrees_with_powers_of_two():
    for exponent in range(1, 12):
        bracket = wl.log2_bracket(Fraction(2 ** exponent))
        assert abs(bracket["value"] - exponent) <= bracket["error"]


def test_gate_is_the_pre_registered_decision_tree(report):
    gate = report["gate"]
    assert gate["weak_gate"] == 1 and gate["continue_gate"] == 3
    assert wl.gate_decision(Fraction(1, 2))["verdict"] == "not evidence"
    assert wl.gate_decision(Fraction(2))["verdict"] == "weak"
    assert wl.gate_decision(Fraction(4))["enumerate"]
    assert not gate["enumerate"]
    assert gate["verdict"] == "weak"


# ---------------------------------------------------------------------------
#  4.  The Golay null, exactly
# ---------------------------------------------------------------------------

def test_golay_sphere_count_is_exact(report):
    null = report["golay_null"]
    assert null["sphere_terms"] == (1, 24, 276, 2024)
    assert null["sphere_size"] == 2325
    assert null["within_three"] == 4096 * 2325 == 9523200
    assert null["space"] == 16777216
    assert null["within_three_probability"] == Fraction(2325, 4096)
    assert null["within_three_probability"] > Fraction(1, 2)


def test_golay_null_comes_from_the_code_itself(report):
    null = report["golay_null"]
    census = gd.coset_census()
    assert null["cosets_by_weight"] == census["cosets_by_leader_weight"]
    assert sum(null["cosets_by_weight"].values()) == 4096
    assert null["cumulative"][3] == Fraction(2325, 4096)
    assert null["cumulative"][4] == 1


def test_golay_within_three_is_worth_less_than_one_bit(report):
    bits = report["golay_null"]["within_three_bits"]
    assert 0 < bits < 1
    assert wb.round_str(bits, 3) == "0.817"


def test_alpha_word_is_all_zero_for_magnitude_reasons(report):
    alpha_row = next(row for row in report["golay"] if row["name"] == "alpha")
    assert alpha_row["all_zero"]
    assert alpha_row["d_min"] == 0
    assert all(row["depth"] in wl.GOLAY_DEPTHS for row in alpha_row["rows"])


def test_golay_signal_vanishes_against_the_magnitude_matched_null(report):
    magnitude = report["golay_magnitude"]
    assert magnitude["members"] == 1066
    assert magnitude["by_distance"] == {0: 1066}
    assert magnitude["tail"] == 1
    assert magnitude["score"]["raw"] == 0


# ---------------------------------------------------------------------------
#  5.  The comparison rows
# ---------------------------------------------------------------------------

def test_every_target_is_exact():
    for _name, _notation, value in wl.targets():
        assert isinstance(value, Fraction)


def test_comparison_table_covers_the_named_constants(report):
    names = {row["name"] for row in report["comparison"]}
    for expected in ("alpha", "m_p/m_e", "sin^2 theta_W", "alpha_s(M_Z)",
                     "(g-2)/2", "pi", "e", "phi", "Y", "Q", "MONAD"):
        assert expected in names
    ranks = [row["rank"] for row in report["comparison"]]
    assert ranks == sorted(ranks)


def test_alpha_leads_the_comparison_on_the_statistic(report):
    rows = report["comparison"]
    alpha_row = next(row for row in rows if row["name"] == "alpha")
    assert alpha_row["rank"] == 1
    assert alpha_row["short_gap"] == 137 and alpha_row["long_gap"] == 138
    assert all(row["deviation"] <= alpha_row["deviation"] for row in rows)


# ---------------------------------------------------------------------------
#  6.  Exactness, the cache, and the wiring
# ---------------------------------------------------------------------------

def test_no_float_is_constructed_in_the_module():
    path = Path(wl.__file__)
    assert ex.module_float_sites(path) == {}
    assert ex.module_digest_uses(path) == 0


def test_the_cache_is_present_and_fresh():
    condition = wl.state()
    assert condition["present"]
    assert condition["fresh"], (
        "the measurement cache is stale; re-take it with "
        "python3 -m glm_universal.reasoning.wobble_landscape --remeasure")
    stored = wl.current()
    assert stored is not None
    assert stored["source_digest"] == wl.module_digest()


def test_the_cache_holds_the_figures_the_study_quotes():
    stored = wl.current()
    assert stored is not None
    assert stored["primary"]["primary_null"]["tail"] == Fraction(77, 1066)
    assert stored["gate"]["verdict"] == "weak"
    assert stored["golay_null"]["within_three"] == 9523200


def test_the_subject_is_wired_and_answers():
    assert "landscape" in REPORT_SUBJECTS
    session = GeometricSession()
    solution = session.ask("report landscape")
    assert solution.kind == "report"
    assert "not a derivation of alpha" in solution.answer
    assert solution.expected["tail"] == "77/1066"
    assert solution.expected["verdict"] == "weak"


def test_column_three_renders_for_the_subject():
    session = GeometricSession()
    solution = session.ask("report landscape")
    script = tct.render_script(solution)
    assert "wobble_landscape" in script
    assert "landscape_report" in script
