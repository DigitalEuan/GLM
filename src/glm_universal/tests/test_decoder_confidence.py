"""Decoder confidence, pinned.

``glm_universal.reasoning.decoder_confidence`` attaches the absorbed
confidence law to the decoder's own readings; ``decoder_confidence_marks`` is
the computational half of ``studies/DECODER_CONFIDENCE_STUDY.md`` (Phase 77),
and the floor it checks is a theorem of
``RequestProject/GLM/DecoderConfidence.lean`` (C6).  Everything is exact.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import carried_fork as cf
from glm_universal.reasoning import decoder_confidence as dc
from glm_universal.reasoning import decoder_confidence_marks as dcm
from glm_universal.reasoning import law_absorption as la
from glm_universal.reasoning import python_speech as sp
from glm_universal.reasoning import python_substrate as ps
from glm_universal.substrate.mog import GOLAY_MASKS

P1 = Fraction(1, 100)
P10 = Fraction(1, 10)
g = ps.golay_encode


class TestTheDecoder(unittest.TestCase):

    def test_confidence_is_the_law_and_the_brute_sum(self):
        for e, d in ((0, 0), (0b1, 1), (0b11, 2), (0b111, 3)):
            r = dc.decode_confidence(g(5) ^ e, P10)
            self.assertEqual(r["coset_weight"], d)
            self.assertEqual(r["value"], g(5))
            self.assertEqual(r["confidence"], la.confidence(d, P10))
            self.assertEqual(r["confidence"], dc.brute_posterior(
                (g(5) ^ e,), g(5), GOLAY_MASKS, P10))

    def test_a_deep_hole_is_a_tie(self):
        with self.assertRaises(dc.ConfidenceRefusal) as ctx:
            dc.decode_confidence(g(5) ^ 0b1111, P1)
        self.assertEqual(ctx.exception.name, "TIE")

    def test_the_rate_is_checked(self):
        for bad in (0, Fraction(1, 2), Fraction(3, 4), True):
            with self.assertRaises(dc.ConfidenceRefusal) as ctx:
                dc.decode_confidence(g(5), bad)
            self.assertEqual(ctx.exception.name, "RATE_OUT_OF_RANGE")

    def test_weight_three_at_ten_percent_is_far_from_sure(self):
        # a read at coset weight 3 is right about 78% of the time at p = 1/10
        c = la.confidence(3, P10)
        self.assertTrue(Fraction(77, 100) < c < Fraction(78, 100))


class TestTheContextStage(unittest.TestCase):

    def test_resolved_fork_confidence_and_its_floor(self):
        cases = [g(1), g(2), g(3), g(4)]
        r = dc.decode_confidence(g(1) ^ 0b1111, P10, cases)
        self.assertEqual(r["value"], g(1))
        self.assertEqual(r["confidence"], Fraction(531441, 531604))
        self.assertEqual(r["confidence"], dc.brute_posterior(
            (g(1) ^ 0b1111,), g(1), cases, P10))
        self.assertGreaterEqual(r["gap"], 2)
        self.assertGreaterEqual(r["confidence"], r["bound"])
        self.assertIn("closed world", r["assumption"])

    def test_the_refusals_follow_resolve(self):
        with self.assertRaises(dc.ConfidenceRefusal) as ctx:
            dc.decode_confidence(g(1) ^ 0b1111, P1, [g(2), g(3)])
        self.assertEqual(ctx.exception.name, "UNCORRECTABLE")
        with self.assertRaises(dc.ConfidenceRefusal) as ctx:
            dc.decode_confidence(0b1111, P1, [5])
        self.assertEqual(ctx.exception.name, "OUTSIDE_SUBSTRATE")

    def test_every_resolved_read_on_a_stride_meets_the_floor(self):
        r = dcm.c2_context(sizes=(2, 32), stride=97)
        self.assertTrue(r["passed"])
        for row in r["rows"]:
            self.assertEqual(row["least_gap"], 2)
            self.assertEqual(row["brute_disagreements"], 0)
            self.assertEqual(row["below_bound"], 0)
        # the floor is attained with a single rival
        two = [row for row in r["rows"] if row["k"] == 2]
        self.assertTrue(all(row["least"] == row["bound"] for row in two))


class TestTheSecondReading(unittest.TestCase):

    def test_agreed_codeword_by_the_product_of_likelihoods(self):
        c = g(5)
        reads = (c ^ 0b1111, c ^ 0b111000000000000000000001)
        r = dc.agree_confidence(reads, P1)
        self.assertEqual(r["value"], c)
        self.assertEqual(r["confidence"],
                         dc.brute_posterior(reads, c, GOLAY_MASKS, P1))

    def test_the_witness_is_an_exact_tie_below_one_half(self):
        m = dcm._witness_masks()
        c0 = GOLAY_MASKS[0]
        reads = (c0 ^ m["e1"], c0 ^ m["e2"])
        a = dc.brute_posterior(reads, c0, GOLAY_MASKS, P1)
        b = dc.brute_posterior(reads, c0 ^ m["octad"], GOLAY_MASKS, P1)
        self.assertEqual(a, b)
        self.assertLess(a, Fraction(1, 2))
        with self.assertRaises(dc.ConfidenceRefusal) as ctx:
            dc.agree_confidence(reads, P1)
        self.assertEqual(ctx.exception.name, "AMBIGUOUS")


class TestTheDialect(unittest.TestCase):

    def test_the_builtins_are_declared(self):
        self.assertIn("decode_confidence", sp.BUILTINS)
        self.assertIn("agree_confidence", sp.BUILTINS)
        for name in ("TIE", "RATE_OUT_OF_RANGE"):
            self.assertIn(name, ps.REFUSAL_NAMES)

    def test_an_answer_carries_a_verified_script(self):
        p = sp.speak("decode_confidence(Fraction(1, 100), golay_encode(1) ^ "
                     "0b1111, golay_encode(1), golay_encode(2))")
        self.assertIsNone(p.refusal, p.reason)
        self.assertEqual(p.value, Fraction(96059601, 96059602))
        self.assertTrue(sp.verify_payload(p)["verified"])
        self.assertTrue(any("closed-world" in s.language for s in p.steps))

    def test_the_declared_refusals(self):
        masks = dcm._witness_masks()
        for source, expected in dcm.DECLARED_PROGRAMS:
            if expected == "answer":
                continue
            with self.subTest(source=source):
                p = sp.speak(source.format(**masks))
                self.assertEqual(p.refusal, expected, p.reason)

    def test_the_prelude_agrees_with_the_runtime(self):
        ns = {}
        exec(ps.PRELUDE, ns)
        src = "decode_confidence(Fraction(1, 20), golay_encode(9) ^ 0b11)"
        self.assertEqual(ns["run_source"](src), sp.speak(src).value)


class TestTheRecord(unittest.TestCase):

    def test_the_lean_file_states_every_theorem(self):
        self.assertTrue(dcm._lean_has(dcm.LEAN_THEOREMS))

    def test_the_carried_fork_figures_are_the_stated_ones(self):
        self.assertEqual(dcm.CARRIED_FORK_FIGURES["K2"], (4224, 4224, 0))
        k2 = cf.k2_second_reading()
        self.assertEqual((k2["double_reads"], k2["answered"], k2["wrong"]),
                         dcm.CARRIED_FORK_FIGURES["K2"])


if __name__ == "__main__":
    unittest.main()
