"""Phase 119 -- the third derivation study's section 6.

``studies/DERIVATION_FOUR_STUDY.md`` declares marks P1-P10 before any code
(:mod:`glm_universal.evaluation.derivation_four_cases`).  These tests stay
below the router (:mod:`glm_universal.runtime.derivation_four_marks`) and hold
the facts the round rests on at a sampled scale; the full measurement is
``python3 -m glm_universal.tools derivation-four``.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.evaluation import derivation_four_cases as C
from glm_universal.reasoning import copy_chain as CC
from glm_universal.reasoning import general_rd as GR
from glm_universal.reasoning import robin as RB
from glm_universal.reasoning import robin_two as R2
from glm_universal.runtime import derivation_four_marks as M


class TestCopiesAndFiveVariables(unittest.TestCase):

    def test_five_variable_shannon_claims(self):
        for cid in ("five-subadditivity", "five-markov-chain",
                    "five-conditioning-false"):
            q, want = {c: (t, w) for c, t, w in C.INEQUALITIES}[cid]
            kind, pr, data = M.decide_any(q.split(":", 1)[1])
            self.assertEqual(kind, want)
            self.assertTrue(M.exec_script(M.script_of(kind, pr, data)))

    def test_copy_conditions_shape(self):
        steps = [CC.ChainStep("R1", "A", ("B", "C")),
                 CC.ChainStep("R2", "A", ("B", "C", "R1"))]
        conds = CC.chain_conditions(["A", "B", "C", "D"], steps)
        # 4 + 1 for the first copy, 8 + 1 for the second
        self.assertEqual(len(conds), 14)

    def test_six_variables_refused(self):
        self.assertTrue(M.refusal_marks_low()["met"])


class TestGeneralRateDistortion(unittest.TestCase):

    def test_declared_sources(self):
        self.assertTrue(M.rd_marks()["met"])

    def test_log_bracket(self):
        lo, hi = GR.log2_bounds(Fraction(3))
        # log2(3) = 1.5849625007211...
        self.assertLess(lo, Fraction(1584962500722, 10 ** 12))
        self.assertGreater(hi, Fraction(1584962500721, 10 ** 12))
        self.assertLess(hi - lo, Fraction(1, 10 ** 18))

    def test_battery_sample(self):
        self.assertTrue(M.rd_battery(12)["met"])


class TestRobinTwo(unittest.TestCase):

    def test_both_ends_first_root(self):
        r = R2.robin_two("d2(y)/dx2 + lambda*y = 0",
                         ["d(y)/dx(0) - y(0) = 0", "d(y)/dx(1) + y(1) = 0"])
        lo, hi = r.roots[0]
        # tan k = 2k/(k^2 - 1): first root about 1.3065
        self.assertLess(lo, Fraction(13066, 10000))
        self.assertGreater(hi, Fraction(13064, 10000))

    def test_declared_problems(self):
        self.assertTrue(M.robin_marks()["met"])

    def test_battery_sample(self):
        self.assertTrue(M.robin_battery(6)["met"])

    def test_bounds_text(self):
        r = RB.robin_problem("d2(y)/dx2 + lambda*y = 0",
                             ["y(0) = 0", "d(y)/dx(L) + 2*y(L) = 0"])
        lo, hi = R2.bounds_for(r)
        self.assertIn("arctan(2*L/(n*pi))", lo)


class TestLean(unittest.TestCase):

    def test_lean_files(self):
        out = M.lean_mark()
        self.assertTrue(out["met"], out)


if __name__ == "__main__":
    unittest.main()
