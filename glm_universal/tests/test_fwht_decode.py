"""Tests for :mod:`glm_universal.reasoning.fwht_decode`.

Three things are pinned here, and each is the sort of claim that would
otherwise be a sentence in a README:

* the **identity** -- the 4,096 Golay coset costs the Leech decoder
  minimises really are one Walsh-Hadamard transform, on the generator this
  package actually uses;
* the **agreement** -- the transform-driven decoder returns exactly what the
  existing complete decoder returns, argmin sets included, so nothing is
  resolved silently by the faster route;
* the **certificate** -- the constant-time tier is never wrong when it
  certifies, always fires on a flat profile, and its rate on spread profiles
  is measured rather than asserted.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import analogy as an
from glm_universal.reasoning import fwht_decode as fd
from glm_universal.substrate import golay_decode as gdc
from glm_universal.substrate.linalg import popcount
from glm_universal.substrate.mog import GOLAY, GOLAY_MASKS


def _profile(seed: int, spread: Fraction) -> list:
    return fd._profile(fd._Sweep(seed), spread)


# ===========================================================================
# 1.  THE GENERATOR COLUMN MAP
# ===========================================================================

class TestColumns(unittest.TestCase):

    def test_columns_reproduce_every_codeword_bit(self):
        """Bit k of the codeword of m is the parity of column k against m."""
        cols = fd.message_columns()
        self.assertEqual(len(cols), 24)
        for m in range(0, 4096, 97):
            word = GOLAY.encode_mask(m)
            for k in range(24):
                with self.subTest(message=m, coordinate=k):
                    self.assertEqual((word >> k) & 1,
                                     popcount(cols[k] & m) & 1)

    def test_message_of_codeword_inverts_encode(self):
        for m in range(0, 4096, 311):
            self.assertEqual(fd.message_of_codeword(GOLAY.encode_mask(m)), m)

    def test_message_of_a_non_codeword_is_refused(self):
        non_codeword = next(w for w in range(1 << 24)
                            if not GOLAY.is_codeword(w))
        with self.assertRaises(ValueError):
            fd.message_of_codeword(non_codeword)


# ===========================================================================
# 2.  THE TRANSFORM IDENTITY
# ===========================================================================

class TestTransformIdentity(unittest.TestCase):

    def test_transform_reproduces_the_direct_support_sums(self):
        delta = _profile(3, Fraction(4))
        direct = fd.support_sums_direct(delta)
        transformed = fd.support_sums_fwht(delta)
        self.assertEqual(len(direct), 4096)
        self.assertEqual(direct, transformed)

    def test_support_sums_are_the_actual_sums_over_supports(self):
        """Not just self-consistent: they are the sums they claim to be."""
        delta = [Fraction(k * k % 13 - 6, k + 2) for k in range(24)]
        sums = fd.support_sums_fwht(delta)
        for m in (0, 1, 17, 512, 4095):
            word = GOLAY.encode_mask(m)
            want = sum((delta[k] for k in range(24) if (word >> k) & 1),
                       Fraction(0))
            self.assertEqual(sums[m], want)

    def test_a_wrong_length_is_refused(self):
        with self.assertRaises(ValueError):
            fd.support_sums_fwht([Fraction(1)] * 23)

    def test_integer_butterfly_agrees_with_the_general_fwht(self):
        report = fd.agreement_report(samples=1)
        self.assertEqual(report["integer_butterfly_failures"], 0)
        self.assertEqual(report["integer_butterfly_checked"], 4096)


# ===========================================================================
# 3.  OPERATION COUNTS
# ===========================================================================

class TestOperationCounts(unittest.TestCase):

    def test_direct_count_is_the_summed_codeword_weight(self):
        counts = fd.operation_counts()
        self.assertEqual(counts["direct_adds"],
                         sum(popcount(w) for w in GOLAY_MASKS))
        self.assertEqual(counts["direct_adds"], 49152)

    def test_the_two_routes_cost_the_same_because_n_is_twice_k(self):
        """The honest finding: no speed-up for this code, and why."""
        counts = fd.operation_counts()
        self.assertEqual(counts["direct_adds"], counts["fwht_ops"])
        self.assertEqual(counts["ratio_direct_over_fwht"], Fraction(1))
        self.assertTrue(counts["equal_because_n_equals_2k"])
        self.assertEqual(counts["n"], 2 * counts["k"])


# ===========================================================================
# 4.  THE CERTIFIED CONSTANT-TIME TIER
# ===========================================================================

class TestCertificate(unittest.TestCase):

    def test_flat_profile_always_certifies(self):
        """With every magnitude equal the bound is 8 - w0 >= w0, w0 <= 4."""
        for seed in (1, 2, 3, 4, 5):
            delta = _profile(seed, Fraction(0))
            with self.subTest(seed=seed):
                self.assertTrue(fd.certified_lookup(delta)["certified"])

    def test_certified_answers_match_the_exact_transform(self):
        checked = 0
        for seed in range(1, 40):
            delta = _profile(seed, Fraction(3))
            fast = fd.certified_lookup(delta)
            if not fast["certified"]:
                continue
            checked += 1
            sums = fd.support_sums_fwht(delta)
            best = min(sums)
            self.assertEqual(fast["cost"], best)
            if fast["tie_set_certified"]:
                exact = tuple(m for m in range(4096) if sums[m] == best)
                self.assertEqual(fast["messages"], exact)
        self.assertGreater(checked, 0, "no profile certified -- test is vacuous")

    def test_the_lookup_answer_is_in_the_coset_of_the_hard_decision(self):
        delta = _profile(11, Fraction(1))
        fast = fd.certified_lookup(delta)
        for codeword in fast["codewords"]:
            self.assertTrue(GOLAY.is_codeword(codeword))
            self.assertEqual(gdc.coset_weight(codeword ^ fast["hard_decision"]),
                             fast["coset_weight"])

    def test_declining_is_not_failing(self):
        """When the certificate declines, decode_soft still answers exactly."""
        declined = None
        for seed in range(1, 60):
            delta = _profile(seed, Fraction(99))
            if not fd.certified_lookup(delta)["tie_set_certified"]:
                declined = delta
                break
        self.assertIsNotNone(declined, "no profile declined -- test is vacuous")
        got = fd.decode_soft(declined)
        self.assertEqual(got["route"], "transform")
        direct = fd.support_sums_direct(declined)
        best = min(direct)
        self.assertEqual(got["cost"], best)
        self.assertEqual(tuple(got["messages"]),
                         tuple(m for m in range(4096) if direct[m] == best))

    def test_the_measured_rate_falls_as_the_spread_widens(self):
        report = fd.certificate_rate_report(samples=40)
        rates = [r["certified_fraction"] for r in report["regimes"]]
        self.assertEqual(rates[0], Fraction(1))
        self.assertGreater(rates[0], rates[-1])
        self.assertEqual(report["certified_but_wrong"], 0)
        self.assertTrue(report["flat_profile_always_certifies"])


# ===========================================================================
# 5.  EXACT AGREEMENT WITH THE EXISTING DECODER
# ===========================================================================

class TestAgreement(unittest.TestCase):

    def test_nearest_lattice_point_agrees_point_for_point(self):
        sweep = fd._Sweep(99)
        for case in range(6):
            vector = [Fraction(sweep.between(-12, 13), sweep.between(1, 5))
                      for _ in range(24)]
            with self.subTest(case=case):
                want = an.nearest_lattice_point(vector)
                got = fd.nearest_lattice_point_fwht(vector)
                self.assertEqual(want.point, got.point)
                self.assertEqual(want.distance2, got.distance2)
                self.assertEqual(want.leech_class, got.leech_class)
                self.assertEqual(want.norm2, got.norm2)
                self.assertEqual(want.is_2a_axis, got.is_2a_axis)
                self.assertTrue(got.in_leech)

    def test_a_lattice_point_decodes_to_itself(self):
        point = list(an.nearest_lattice_point([Fraction(0)] * 23
                                              + [Fraction(1)]).point)
        got = fd.nearest_lattice_point_fwht(point)
        self.assertEqual(list(got.point), point)
        self.assertEqual(got.distance2, 0)
        self.assertTrue(got.exact_hit)

    def test_the_sextet_tie_survives_the_transform(self):
        """A flat profile at the covering radius has six equal answers."""
        report = fd.tie_set_agreement_report(samples=4)
        self.assertEqual(report["failures"], 0)
        self.assertEqual(report["sextet_case_tie_size"], 6)
        self.assertTrue(report["sextet_case_is_sixfold"])
        self.assertEqual(gdc.coset_weight(report["sextet_case_word"]), 4)


# ===========================================================================
# 6.  THE REPORT
# ===========================================================================

class TestReport(unittest.TestCase):

    def test_report_recomputes_and_agrees(self):
        report = fd.fwht_decode_report(samples=20)
        self.assertTrue(report["agreement"]["all_agree"])
        self.assertTrue(report["tie_sets"]["all_tie_sets_agree"])
        self.assertEqual(report["certificate_rates"]["certified_but_wrong"], 0)
        self.assertTrue(
            report["operation_counts"]["equal_because_n_equals_2k"])

    def test_report_states_its_limits(self):
        report = fd.fwht_decode_report(samples=4)
        self.assertIn("not a speed-up", report["what_the_transform_buys"])
        self.assertIn("sufficient condition", report["honest_limits"])

    def test_no_float_is_constructed(self):
        report = fd.fwht_decode_report(samples=4)

        def walk(value):
            self.assertNotIsInstance(value, float)
            if isinstance(value, dict):
                for item in value.values():
                    walk(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    walk(item)

        walk(report)


if __name__ == "__main__":
    unittest.main()
