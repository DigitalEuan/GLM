"""Phase 118 -- the second derivation study's section 6.

``studies/DERIVATION_THREE_STUDY.md`` declares marks N1-N10 before any code
(:mod:`glm_universal.evaluation.derivation_three_cases`).  These tests stay
below the frames (:mod:`glm_universal.runtime.derivation_three_marks`) and
hold the facts the round rests on at a sampled scale; the full measurement
is ``python3 -m glm_universal.tools derivation-three``.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.evaluation import derivation_three_cases as C
from glm_universal.reasoning import hamming_rd as HR
from glm_universal.reasoning import info_inequality as II
from glm_universal.reasoning import non_shannon as NS
from glm_universal.reasoning import robin as RB
from glm_universal.runtime import derivation_three_marks as M


class TestNonShannon(unittest.TestCase):

    def test_zhang_yeung_is_proved_past_shannon(self):
        pr, v, b, kind = M.decide_all(C.INEQUALITIES[0][1].split(":", 1)[1])
        self.assertEqual(v.kind, "NOT_SHANNON")
        self.assertEqual(kind, "proved_non_shannon")
        self.assertTrue(M.exec_script(M.inequality_script(pr, v, b)))

    def test_ingleton_has_an_entropic_counterexample(self):
        q = dict((c, t) for c, t, _ in C.INEQUALITIES)["ingleton"]
        pr, v, b, kind = M.decide_all(q.split(":", 1)[1])
        self.assertEqual(kind, "NOT_VALID_ENTROPIC")
        self.assertTrue(M.exec_script(M.inequality_script(pr, v, b)))

    def test_exact_log_signs(self):
        self.assertEqual(NS.lf_sign(NS.factor_log2(Fraction(3, 2))), 1)
        self.assertEqual(NS.lf_sign(NS.factor_log2(Fraction(2, 3))), -1)
        self.assertEqual(NS.lf_sign(NS.factor_log2(Fraction(1))), 0)

    def test_declared_inequalities(self):
        self.assertTrue(M.inequality_marks()["met"])

    def test_battery_sample(self):
        out = M.inequality_battery(30)
        self.assertEqual(out["unsound"], 0)
        self.assertEqual(out["inconsistent"], 0)
        self.assertEqual(out["script_failures"], 0)


class TestRateDistortion(unittest.TestCase):

    def test_pieces_tile_to_d_max(self):
        r = HR.hamming_rd("[1/2, 1/3, 1/6]")
        self.assertEqual(r.pieces[0].lo, 0)
        self.assertEqual(r.pieces[-1].hi, r.d_max)
        for a, b in zip(r.pieces, r.pieces[1:]):
            self.assertEqual(a.hi, b.lo)
        self.assertLess(r.slb_end, r.d_max)

    def test_declared_sources(self):
        self.assertTrue(M.rd_marks()["met"])

    def test_battery_sample(self):
        out = M.rd_battery(12, iters=1500)
        self.assertTrue(out["met"], out)


class TestRobin(unittest.TestCase):

    def test_phase_107_robin_root(self):
        r = RB.robin_problem("d2(y)/dx2 + lambda*y = 0",
                             ["y(0) = 0", "d(y)/dx(1) + 1*y(1) = 0"])
        lo, hi = r.roots[0]
        # tan k = -k: first root about 2.0288
        self.assertLess(lo, Fraction(20289, 10000))
        self.assertGreater(hi, Fraction(20287, 10000))

    def test_declared_problems(self):
        self.assertTrue(M.robin_marks()["met"])

    def test_battery_sample(self):
        self.assertTrue(M.robin_battery(12)["met"])


class TestRefusalsAndLean(unittest.TestCase):

    def test_refusals_at_the_layer(self):
        self.assertTrue(M.refusal_marks_low()["met"])

    def test_lean_file(self):
        out = M.lean_mark()
        self.assertTrue(out["met"], out)


if __name__ == "__main__":
    unittest.main()
