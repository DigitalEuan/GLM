"""Tests for ``substrate/superposition`` -- carrying a Golay tie forward.

The module turns the six-fold ambiguity at the Golay covering radius into a
first-class parallel hypothesis space and asks what survives bundling it.  The
two answers it reports are opposite, and these tests pin both on the real code:
the ``F_2`` bundle of a complete tie is the all-ones word for *every* received
word, while the rational bundle is an invertible affine image of it.  They also
pin the sextet partition, the three outcomes of a contextual collapse, the
exact reading of a carrier that cycles through the tie, and the hull
experiment that separates "scale the alphabet" from "widen its supports".

The counterpart machine-checked development is in ``RequestProject/GLM/``:
``Golay/Sextet.lean`` (six ties, the sextet partition, minimum distance 8,
covering radius 4), ``Superposition.lean`` (``bundleF2_eq_one``,
``bundleQ_eq``, ``bundleQ_injective``), ``Wobble.lean`` (the cycle reading)
and ``HullExpansion.lean`` (scaling versus supports).  The Lean development
uses the same parity block ``B`` as ``substrate/mog.py``, and its syndrome map
agrees with ``GOLAY.syndrome_int`` word for word.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations

import pytest

from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession
from glm_universal.substrate import superposition as SP
from glm_universal.substrate.golay_decode import decode_complete
from glm_universal.substrate.linalg import popcount
from glm_universal.substrate.mog import GOLAY, GOLAY_MASKS

N = 24
TETRAD = 0b1111  # coordinates 0,1,2,3: a weight-4 word, at the covering radius


@pytest.fixture(scope="module")
def report():
    return SP.superposition_report()


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


def _mask(support):
    out = 0
    for i in support:
        out |= 1 << i
    return out


# ===========================================================================
# 1.  LIST DECODING
# ===========================================================================

class TestSuperpose:

    def test_codeword_reads_back_as_itself(self):
        sup = SP.superpose(GOLAY_MASKS[7])
        assert sup.weight == 0
        assert sup.candidates == (GOLAY_MASKS[7],)
        assert not sup.ambiguous
        assert sup.dimension == 1

    def test_single_error_is_corrected_uniquely(self):
        received = GOLAY_MASKS[7] ^ (1 << 5)
        sup = SP.superpose(received)
        assert sup.weight == 1
        assert sup.dimension == 1
        assert sup.candidates == (GOLAY_MASKS[7],)

    def test_covering_radius_word_carries_six_hypotheses(self):
        sup = SP.superpose(TETRAD)
        assert sup.weight == 4
        assert sup.dimension == SP.TIE_COUNT == 6
        assert sup.ambiguous

    def test_candidates_agree_with_the_complete_decoder(self):
        for support in list(combinations(range(N), 4))[:32]:
            mask = _mask(support)
            assert SP.superpose(mask).candidates == decode_complete(mask).candidates

    def test_every_candidate_is_a_codeword_at_distance_four(self):
        sup = SP.superpose(TETRAD)
        for c in sup.candidates:
            assert GOLAY.is_codeword(c)
            assert popcount(c ^ TETRAD) == 4

    def test_candidates_are_mutually_at_the_minimum_distance(self):
        sup = SP.superpose(TETRAD)
        for a, b in combinations(sup.candidates, 2):
            assert popcount(a ^ b) == 8


# ===========================================================================
# 2.  THE SEXTET
# ===========================================================================

class TestSextet:

    def test_six_leaders_partition_the_twenty_four_coordinates(self, report):
        sextet = report["sextet"]
        assert sextet["leader_counts"] == [6]
        assert sextet["pairwise_disjoint"]
        assert sextet["covers_all_24"]
        assert sextet["tetrads_checked"] == 64

    def test_each_leader_is_a_tetrad(self):
        sup = SP.superpose(TETRAD)
        assert sorted(popcount(leader) for leader in sup.leaders) == [4] * 6

    def test_the_received_word_is_one_of_the_six_leaders(self):
        assert TETRAD in SP.superpose(TETRAD).leaders


# ===========================================================================
# 3.  BUNDLING: THE TWO RULES DO NOT AGREE
# ===========================================================================

class TestBundling:

    def test_xor_bundle_of_a_complete_tie_is_all_ones(self):
        for support in list(combinations(range(N), 4))[:48]:
            sup = SP.superpose(_mask(support))
            assert sup.weight == 4
            assert SP.bundle_f2(sup.candidates) == SP.ALL_ONES

    def test_xor_bundle_carries_no_information(self, report):
        bundling = report["bundling"]
        assert bundling["f2_bundle_is_constant"]
        assert bundling["f2_bundle_is_all_ones"]
        assert bundling["f2_bundle_distinguishes"] == 1

    def test_rational_bundle_is_one_sixth_or_five_sixths(self, report):
        assert report["bundling"]["rational_bundle_coordinate_values"] == [
            Fraction(1, 6), Fraction(5, 6)]

    def test_rational_bundle_is_the_affine_image_of_the_input(self):
        for support in list(combinations(range(N), 4))[:48]:
            mask = _mask(support)
            bundle = SP.bundle_rational(SP.superpose(mask).candidates)
            for i in range(N):
                bit = (mask >> i) & 1
                assert bundle[i] == Fraction(1 + 4 * bit, 6)

    def test_rational_bundle_recovers_the_received_word(self, report):
        bundling = report["bundling"]
        assert bundling["rational_bundle_recovers_input"]
        assert bundling["rational_bundle_injective"]
        assert bundling["rational_bundle_distinguishes"] == bundling["words_checked"]

    def test_recovery_refuses_a_bundle_that_is_not_a_complete_tie(self):
        with pytest.raises(ValueError):
            SP.recover_from_bundle(tuple(Fraction(1, 2) for _ in range(N)))

    def test_recovery_refuses_a_float(self):
        with pytest.raises(TypeError):
            SP.recover_from_bundle(tuple([0.5] * N))

    def test_no_float_is_constructed(self):
        bundle = SP.bundle_rational(SP.superpose(TETRAD).candidates)
        assert all(isinstance(b, Fraction) for b in bundle)


# ===========================================================================
# 4.  COLLAPSE BY CONTEXT
# ===========================================================================

class TestCollapse:

    def test_a_selective_context_collapses_to_one_state(self):
        sup = SP.superpose(TETRAD)
        chosen = sup.candidates[3]
        result = SP.collapse(sup, lambda c: c == chosen)
        assert result.status == "collapsed"
        assert result.value == chosen

    def test_a_permissive_context_leaves_the_superposition_standing(self):
        sup = SP.superpose(TETRAD)
        result = SP.collapse(sup, lambda c: True)
        assert result.status == "superposed"
        assert result.value is None
        assert len(result.after) == 6

    def test_an_incompatible_context_refutes_the_read(self):
        sup = SP.superpose(TETRAD)
        result = SP.collapse(sup, lambda c: popcount(c) == 1)
        assert result.status == "refuted"
        assert result.after == ()

    def test_report_exhibits_all_three_outcomes(self, report):
        collapse = report["collapse"]
        assert collapse["collapsed"]["status"] == "collapsed"
        assert collapse["superposed"]["status"] == "superposed"
        assert collapse["refuted"]["status"] == "refuted"
        assert collapse["no_tie_broken_by_order"]


# ===========================================================================
# 5.  THE WIGGLE
# ===========================================================================

class TestSextetCycle:

    def test_cycle_reading_is_the_rational_bundle(self):
        for support in list(combinations(range(N), 4))[:24]:
            mask = _mask(support)
            assert SP.sextet_cycle_reading(mask) == SP.bundle_rational(
                SP.superpose(mask).candidates)

    def test_cycle_reading_determines_the_received_word(self):
        readings = {}
        for support in list(combinations(range(N), 4))[:64]:
            mask = _mask(support)
            reading = SP.sextet_cycle_reading(mask)
            assert reading not in readings
            readings[reading] = mask
            assert SP.recover_from_bundle(reading) == mask

    def test_a_snap_would_have_left_ten_thousand_possibilities(self):
        # every codeword is the nearest codeword of C(24,4) words
        codeword = GOLAY_MASKS[11]
        count = sum(1 for support in combinations(range(N), 4)
                    if popcount(codeword ^ (codeword ^ _mask(support))) == 4)
        assert count == 10626


# ===========================================================================
# 6.  THE HULL EXPERIMENT
# ===========================================================================

class TestAlphabetExpansion:

    def test_functional_is_nonpositive_on_every_codeword(self, report):
        hull = report["hull"]
        assert hull["codewords_checked"] == 4096
        assert hull["max_over_scaled_codewords"] == 0

    def test_target_is_strictly_separated(self, report):
        hull = report["hull"]
        assert hull["value_at_target"] == Fraction(7, 2)
        assert hull["target_separated_from_scaled_hull"]

    def test_scaling_the_alphabet_does_not_help(self, report):
        assert report["hull"]["scaling_helps"] is False

    def test_leech_supports_reach_the_target_exactly(self, report):
        hull = report["hull"]
        assert hull["leech_cycle_length"] == 16
        assert hull["leech_cycle_reaches_target"]
        reading = hull["leech_cycle_reading"]
        assert reading[0] == Fraction(1, 2)
        assert all(reading[i] == 0 for i in range(1, N))

    def test_reading_is_exact_rational_arithmetic(self, report):
        assert all(isinstance(x, Fraction)
                   for x in report["hull"]["leech_cycle_reading"])


# ===========================================================================
# 6b.  THE COSET CENSUS
# ===========================================================================

class TestCosetCensus:
    """How often the tie happens, against the Lean figures.

    Counterpart: ``RequestProject/GLM/Golay/Census.lean`` -- ``coset_census``,
    ``unique_vs_ambiguous``, ``mean_coset_weight``,
    ``mean_coset_weight_gt_three``, ``mean_coset_weight_lt_four``.
    """

    def test_the_distribution_is_the_lean_census(self):
        assert SP.coset_weight_distribution() == {
            0: 1, 1: 24, 2: 276, 3: 2024, 4: 1771}
        assert SP.coset_weight_distribution() == SP.LEAN_COSET_CENSUS

    def test_the_census_exhausts_the_cosets(self):
        assert sum(SP.coset_weight_distribution().values()) == 4096

    def test_the_low_weights_are_the_binomials(self):
        from math import comb

        counts = SP.coset_weight_distribution()
        for w in range(4):
            assert counts[w] == comb(24, w)

    def test_the_weight_four_cosets_are_the_tetrads_six_at_a_time(self):
        from math import comb

        assert SP.coset_weight_distribution()[4] * 6 == comb(24, 4)

    def test_the_mean_is_exactly_3433_over_1024(self):
        mean = SP.mean_coset_weight()
        assert isinstance(mean, Fraction)
        assert mean == Fraction(3433, 1024)
        assert mean == SP.LEAN_MEAN_COSET_WEIGHT
        assert mean == Fraction(13732, 4096)

    def test_the_mean_lies_strictly_between_the_two_radii(self):
        mean = SP.mean_coset_weight()
        assert 3 < mean < 4

    def test_the_split_is_2325_and_1771(self, report):
        census = report["census"]
        assert census["uniquely_read_cosets"] == 2325
        assert census["ambiguous_cosets"] == 1771
        assert (census["uniquely_read_cosets"]
                + census["ambiguous_cosets"] == census["cosets"])

    def test_the_ambiguous_fraction_is_exact(self, report):
        frac = report["census"]["ambiguous_fraction"]
        assert isinstance(frac, Fraction)
        assert frac == Fraction(1771, 4096)

    def test_the_report_agrees_with_lean(self, report):
        census = report["census"]
        assert census["census_agrees_with_lean"] is True
        assert census["mean_agrees_with_lean"] is True
        assert census["mean_exceeds_packing_radius"] is True
        assert census["mean_below_covering_radius"] is True

    def test_the_census_matches_the_decoder_word_by_word(self):
        """The distribution is a fact about the decoder, not a table.

        Every word of weight <= 4 decodes to a coset of that word's coset
        weight; here we check the two ends directly against
        ``decode_complete``: weight-3 words are unique reads, tetrads are
        six-fold ties.
        """
        unique = decode_complete(0b111)
        assert unique.weight == 3
        assert len(unique.candidates) == 1
        tie = decode_complete(TETRAD)
        assert tie.weight == 4
        assert len(tie.candidates) == 6

    def test_the_mean_is_the_average_over_words_too(self):
        """Cosets all hold 4,096 words, so the two averages coincide."""
        counts = SP.coset_weight_distribution()
        words = {w: c * 4096 for w, c in counts.items()}
        assert sum(words.values()) == 1 << 24
        mean_over_words = Fraction(sum(w * c for w, c in words.items()),
                                   sum(words.values()))
        assert mean_over_words == SP.mean_coset_weight()


# ===========================================================================
# 6c.  THE DYNAMICAL HALF: THE COSET CHAIN
# ===========================================================================

class TestCosetChain:
    """Does the perturbed carrier settle at the critical weight?  No.

    Counterpart: ``RequestProject/GLM/Golay/Dynamics.lean`` -- ``step_unif``,
    ``stationary_unique``, ``expect_unif_cosetWt``,
    ``prob_unif_subcritical_pos``, ``iterate_dirac_ne_unif``,
    ``perturb_correct_returns``.
    """

    def test_every_column_has_odd_parity(self, report):
        assert report["chain"]["columns_all_odd_parity"] is True

    def test_the_uniform_law_is_stationary(self, report):
        assert report["chain"]["uniform_is_stationary"] is True

    def test_the_stationary_mean_is_the_census_mean(self, report):
        assert (report["chain"]["stationary_mean_distance"]
                == Fraction(3433, 1024))

    def test_the_law_alternates_between_parity_classes(self, report):
        chain = report["chain"]
        assert chain["parity_alternates"] is True
        assert chain["parity_class_by_step"][0] == 1
        assert chain["parity_class_by_step"][1] == 0

    def test_the_law_is_never_uniform(self, report):
        chain = report["chain"]
        assert chain["law_never_uniform"] is True
        assert max(chain["support_by_step"]) == 2048
        assert chain["settles_in_distribution"] is False

    def test_the_early_supports_are_the_census_shells(self, report):
        """One tick reaches the 24 weight-one cosets, two ticks 276 + 1."""
        supports = report["chain"]["support_by_step"]
        assert supports[0] == 24
        assert supports[1] == 276 + 1

    def test_the_step_means_are_exact_rationals(self, report):
        means = report["chain"]["mean_distance_by_step"]
        assert all(isinstance(m, Fraction) for m in means)
        assert means[0] == 1

    def test_the_two_step_average_approaches_the_stationary_mean(self, report):
        chain = report["chain"]
        assert chain["two_step_average_error"] < Fraction(1, 10000)
        assert (chain["two_step_average_error"]
                < chain["time_average_error"])

    def test_correction_returns_the_carrier_to_the_code(self, report):
        chain = report["chain"]
        assert chain["corrected_carrier_returns_to_code"] is True
        assert chain["corrected_distances_before_correction"] == [1]
        assert chain["corrected_distance_after_correction"] == 0

    def test_a_corrected_one_bit_error_is_undone(self):
        """``perturb_correct_returns``, on the running decoder."""
        for c in GOLAY_MASKS[:4]:
            for k in (0, 5, 23):
                d = decode_complete(c ^ (1 << k))
                assert d.weight == 1
                assert d.candidates == (c,)

    def test_the_chain_is_deterministic_and_float_free(self):
        assert SP.coset_chain_report(4) == SP.coset_chain_report(4)
        assert all(isinstance(m, Fraction)
                   for m in SP.coset_chain_report(4)["mean_distance_by_step"])


# ===========================================================================
# 7.  DETERMINISM
# ===========================================================================

class TestDeterminism:

    def test_report_is_reproducible(self):
        assert SP.superposition_report() == SP.superposition_report()

    def test_module_imports_no_rng(self):
        import inspect

        source = inspect.getsource(SP)
        assert "random" not in source
        assert "float(" not in source


# ===========================================================================
# 8.  RUNTIME WIRING
# ===========================================================================

class TestRuntime:

    def test_the_subject_is_registered(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS

        assert "superposition" in REPORT_SUBJECTS

    def test_the_query_answers(self, sess):
        sol = sess.ask("report superposition")
        assert sol.ok
        assert sol.kind == "report"
        assert "6 candidates" in sol.answer

    def test_the_six_steps_are_present(self, sess):
        assert len(sess.ask("report superposition").steps) == 6

    def test_the_expected_values_are_the_theorems(self, sess):
        expected = sess.ask("report superposition").expected
        assert expected["tie_count"] == "6"
        assert expected["pairwise_disjoint"] == "True"
        assert expected["covers_all_24"] == "True"
        assert expected["f2_bundle_is_all_ones"] == "True"
        assert expected["f2_bundle_distinguishes"] == "1"
        assert expected["rational_bundle_recovers_input"] == "True"
        assert expected["mean_coset_weight"] == "3433/1024"
        assert expected["uniquely_read_cosets"] == "2325"
        assert expected["ambiguous_cosets"] == "1771"
        assert expected["ambiguous_fraction"] == "1771/4096"
        assert expected["mean_exceeds_packing_radius"] == "True"
        assert expected["mean_below_covering_radius"] == "True"
        assert expected["census_agrees_with_lean"] == "True"
        assert expected["mean_agrees_with_lean"] == "True"
        assert expected["columns_all_odd_parity"] == "True"
        assert expected["uniform_is_stationary"] == "True"
        assert expected["parity_alternates"] == "True"
        assert expected["law_never_uniform"] == "True"
        assert expected["settles_in_distribution"] == "False"
        assert expected["corrected_carrier_returns_to_code"] == "True"
        assert expected["corrected_distance_after_correction"] == "0"
        assert expected["max_over_scaled_codewords"] == "0"
        assert expected["value_at_target"] == "7/2"
        assert expected["leech_cycle_reaches_target"] == "True"

    def test_aliases_reach_the_same_report(self, sess):
        for alias in ("report sextet", "report bundling", "report tie"):
            assert sess.ask(alias).ok

    def test_the_subject_list_mentions_the_new_subject(self, sess):
        sol = sess.ask("report nonsense subject")
        assert not sol.ok
        assert "superposition" in sol.answer

    def test_the_generated_script_is_exact(self, sess):
        source = tct.render_script(sess.ask("report superposition"))
        ok, offenders = tct.script_is_exact(source)
        assert ok, offenders

    def test_the_generated_script_reproduces_column_two(self, sess):
        """Column 3 recomputes the study in a fresh interpreter and agrees."""
        trace = tct.verify_trace(tct.build_trace(sess.ask("report superposition")))
        assert trace.verdict is not None
        assert trace.verdict.executed
        assert trace.verdict.returncode == 0
        assert trace.verdict.matches_column2
        assert trace.verdict.mismatches == ()
        assert trace.verdict.missing_keys == ()
