"""The second reading's channel, pinned.

``glm_universal.reasoning.agree_channel_marks`` is the computational half of
``studies/AGREE_CHANNEL_STUDY.md`` (Phase 81): an exact census over every pair
of reads of one carrier, reduced by code automorphisms that it finds and
verifies, and the second reading (``agree``) placed in Phase 80's
confidence-floor hunt.  The facts it rests on are theorems of
``RequestProject/GLM/Agree.lean`` (G8).  Everything is exact.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from math import comb

from glm_universal.reasoning import agree_channel_marks as acm
from glm_universal.reasoning import confidence_floor_marks as cfm
from glm_universal.reasoning import decoder_confidence as dc
from glm_universal.substrate.mog import GOLAY_MASKS, GOLAY_SET

P10 = Fraction(1, 10)
P20 = Fraction(1, 20)


class TestTheSymmetry(unittest.TestCase):

    def test_automorphisms_preserve_the_code(self):
        for g in acm.automorphisms():
            self.assertEqual(sorted(g), list(range(24)))
            for c in GOLAY_MASKS[::17]:
                self.assertIn(acm._apply(g, c), GOLAY_SET)

    def test_transitive_on_every_weight_up_to_four(self):
        orbits = acm.transitive_on_weights()
        for w, n in orbits.items():
            self.assertEqual(n, comb(24, w))


class TestTheCensus(unittest.TestCase):

    def test_every_resolved_pair_counted_once(self):
        pairs = sum(n for _w1, _w2, _h, n in acm.pair_census())
        self.assertEqual(pairs, 12951 ** 2 - acm.OCTAD_PAIRS)
        self.assertEqual(acm.OCTAD_PAIRS, 3676596)

    def test_strict_and_mixed_agreement_by_a_second_route(self):
        for p in (Fraction(1, 1000), P10):
            s = acm.strict_masses(p)
            self.assertEqual(acm._census_mass(p, "strict"), s["strict"])
            self.assertEqual(acm._census_mass(p, "mixed"), s["mixed"])

    def test_census_confidence_is_the_runtime_confidence(self):
        v = GOLAY_MASKS[40]
        l1, l2 = 0b111, 0b111 << 3
        key = acm.pair_key(l1, l2)
        hist = acm._histogram_of_key()[key]
        conf = acm._conf(hist, acm._pair_weights(P10))
        r = dc.agree_confidence([v ^ l1, v ^ l2], P10)
        self.assertEqual(r["value"], v)
        self.assertEqual(r["confidence"], conf)
        self.assertEqual(conf, dc.brute_posterior((v ^ l1, v ^ l2), v,
                                                  GOLAY_MASKS, P10))

    def test_the_class_collapse(self):
        g2 = acm.g2_class_collapse()
        self.assertEqual(g2["keys_split"], 0)
        self.assertEqual(g2["coarse_split"], 9)

    def test_the_case_sets_are_not_subgroups(self):
        g1 = acm.g1_census(stride=5000)
        self.assertTrue(g1["passed"])
        self.assertFalse(any(g1["case_sets_subgroups"].values()))


class TestTheHunt(unittest.TestCase):

    def test_the_promise_in_every_cell(self):
        self.assertTrue(acm.g3_promise()["passed"])

    def test_agree_has_a_working_floor_at_one_tenth(self):
        works = acm.agree_cell(P10, Fraction(999, 1000))
        self.assertGreaterEqual(works["retention"], Fraction(9, 10))
        self.assertLessEqual(works["residual"], Fraction(1, 1000))
        fails = acm.agree_cell(P10, Fraction(9999, 10000))
        self.assertLess(fails["retention"], Fraction(9, 10))

    def test_agreement_lowers_the_residual(self):
        for p in (P20, P10):
            a = acm.agree_cell(p, None)
            d = cfm.cell("decoder", p, None)
            self.assertLess(a["residual"], d["residual"])
            self.assertEqual(a["p_right"] + a["p_wrong"] + a["p_refused"], 1)

    def test_the_seven_reading_hunt(self):
        g4 = acm.g4_hunt()
        self.assertTrue(g4["passed"])
        self.assertEqual(g4["working_agree"]["1/10"], "999/1000")
        self.assertIsNone(g4["working_seven"]["1/10"])

    def test_overdeclared_is_safe(self):
        g6 = acm.g6_declared_rate()
        self.assertEqual(g6["overdeclared_broken"], 0)
        self.assertEqual(g6["underdeclared_broken"], 4)


class TestTheRuntime(unittest.TestCase):

    def test_every_program_as_computed(self):
        g7 = acm.g7_runtime()
        self.assertEqual(g7["wrong"], 0)
        self.assertEqual(g7["programs"], len(acm.DECLARED_PROGRAMS))

    def test_the_lean_file(self):
        self.assertTrue(acm._lean_has(acm.LEAN_THEOREMS))


if __name__ == "__main__":
    unittest.main()
