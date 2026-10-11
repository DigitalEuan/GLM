"""Phase 108 -- a cubic in letters with three real roots.

``studies/CUBIC_TRIG_STUDY.md`` declares marks T1-T9 before any code
(:mod:`glm_universal.evaluation.cubic_trig_cases`).  These tests hold the
facts the round rests on at a sampled scale; the full measurement is
``python3 -m glm_universal.tools cubic-trig``.
"""

from __future__ import annotations

import unittest
from fractions import Fraction as F

from glm_universal.evaluation import cubic_trig_cases as C
from glm_universal.reasoning import symbolic_nonlinear as N
from glm_universal.runtime import cubic_trig_report as R
from glm_universal.runtime import symbolic_frames as SF


class TestDeclared(unittest.TestCase):

    def test_homogeneous_cases(self):
        out = R.homogeneous_marks(run_scripts=False)
        self.assertEqual(out["passed"], out["of"])

    def test_viete_cases(self):
        out = R.viete_marks(run_scripts=False)
        self.assertEqual(out["passed"], out["of"])

    def test_motion_cases(self):
        self.assertTrue(R.motion_marks()["met"])

    def test_scripts_verify_and_mutants_fail(self):
        for q in (C.HOMOGENEOUS[1][1], C.VIETE[0][1]):
            gate, rejected = R._run_scripts(q)
            self.assertTrue(gate, q)
            self.assertTrue(rejected, q)


class TestSwitch(unittest.TestCase):

    def test_switch_off_refuses_as_phase_104(self):
        q = C.HOMOGENEOUS[0][1]
        saved = N.TRIG
        try:
            N.TRIG = False
            rd = SF.read_system(q)
            self.assertFalse(rd.answered)
            self.assertEqual(rd.code, "NONLINEAR")
        finally:
            N.TRIG = saved
        self.assertTrue(SF.read_system(q).answered)

    def test_unchanged_readings(self):
        out = R.regression_mark(phase104=False)
        self.assertEqual(out["unchanged_moved"], [])
        self.assertEqual(out["motion_moved"], [])


class TestInstrument(unittest.TestCase):

    def test_viete_declared_value_is_a_root(self):
        # x^3 - 3*(a^2+1)*x + 2*a*(a^2+1) at a = 2: the three values are
        # roots, in decreasing order
        P = {"a": F(2)}
        vals = [R._viete_declared("0", "a^2 + 1", "-a/sqrt(a^2 + 1)", k, P)
                for k in range(3)]
        self.assertTrue(vals[0] > vals[1] > vals[2])
        for x in vals:
            self.assertLess(abs(x ** 3 - 15 * x + 20), F(1, 10 ** 9))

    def test_kth_largest(self):
        m = [F(1), F(-3), F(0), F(1)]
        xs = [R._kth_largest(m, k) for k in range(3)]
        self.assertTrue(xs[0] > xs[1] > xs[2])

    def test_batteries_sampled(self):
        self.assertTrue(R.viete_battery(count=4)["met"])
        self.assertTrue(R.homogeneous_battery(count=4)["met"])


class TestLean(unittest.TestCase):

    def test_lean_file(self):
        self.assertTrue(R.lean_mark()["met"])


if __name__ == "__main__":
    unittest.main()
