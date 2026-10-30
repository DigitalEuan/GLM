"""Phase 114 -- roots with no expression in radicals in composite degree, and
on the ``modes.higher`` route.

``studies/PRIMITIVE_RADICAL_STUDY.md`` measures the branch layer against marks
P1-P10 (:mod:`glm_universal.evaluation.primitive_radical_cases`).  These tests
hold the facts the round rests on; the full measurement is
``python3 -m glm_universal.tools primitive-radical``.
"""

from __future__ import annotations

import unittest
from fractions import Fraction as F

from glm_universal.evaluation import primitive_radical_cases as C
from glm_universal.reasoning import symbolic_factor as Z
from glm_universal.runtime import primitive_radical_report as R
from glm_universal.runtime import symbolic_frames as SF


class TestShapes(unittest.TestCase):

    def test_jordan_power(self):
        # one 2-cycle beside a 3-cycle: the cube is a transposition
        self.assertEqual(Z.jordan_power([1, 2, 3]), (2, 3))
        # a transposition itself
        self.assertEqual(Z.jordan_power([1, 1, 1, 1, 2]), (2, 1))
        # one 3-cycle beside a 4-cycle: the 4th power is a 3-cycle
        self.assertEqual(Z.jordan_power([3, 4]), (3, 4))
        # two 2-cycles, or a 2-cycle beside a 4-cycle: neither length works
        for degs in ([2, 2, 1, 1], [2, 4], [3, 3], [6], [1, 5]):
            self.assertIsNone(Z.jordan_power(degs), degs)

    def test_long_cycle(self):
        self.assertTrue(Z.is_long_cycle([1, 5]))
        self.assertTrue(Z.is_long_cycle([1, 9]))
        for degs in ([6], [1, 1, 4], [2, 4], [1, 2, 3]):
            self.assertFalse(Z.is_long_cycle(degs), degs)

    def test_every_cycle_type(self):
        got = R.shape_marks()
        self.assertTrue(got["met"], got)


class TestCertificate(unittest.TestCase):

    def test_certifies_x6_minus_x_minus_1(self):
        got = Z.radical_free_primitive([F(-1), F(-1), F(0), F(0), F(0), F(0),
                                        F(1)])
        self.assertIsNotNone(got)
        self.assertIn(Z.PRIMITIVE_LEAN, got)
        self.assertIn("Dedekind's theorem is not checked in Lean", got)
        q1, degs1, q2, degs2, ell, m = Z.primitive_pattern(
            [-1, -1, 0, 0, 0, 0, 1])
        self.assertEqual(degs1, [1, 5])
        self.assertEqual((ell, Z.jordan_power(degs2)), (ell, (ell, m)))

    def test_prime_degree_left_to_phase_113(self):
        quintic = [F(-1), F(-1), F(0), F(0), F(0), F(1)]
        self.assertIsNone(Z.radical_free_primitive(quintic))
        self.assertEqual(Z.radical_free_galois(quintic),
                         Z.radical_free_frobenius(quintic))

    def test_withheld_for_solvable_groups(self):
        for f in ([-2, 0, 0, 0, 0, 0, 1], [1, 1, 1, 1, 1, 1, 1],
                  [1, 0, 0, 1, 0, 0, 1], [-1, 0, -1, 0, 0, 0, 1],
                  [-1, 0, 0, -1, 0, 0, 0, 0, 0, 1]):
            self.assertIsNone(Z.certify_numeric_any(f), f)

    def test_withheld_for_the_imprimitive_limit(self):
        # x^10 - x^2 - 1 = g(x^2), g = y^5 - y - 1: not solvable, imprimitive,
        # so this round's certificate is silent; since Phase 115 the
        # composition certificate answers it instead
        # (studies/COMPOSED_RADICAL_STUDY.md).
        f = [-1, 0, -1, 0, 0, 0, 0, 0, 0, 0, 1]
        self.assertIsNone(Z.radical_free_primitive([F(c) for c in f]))
        got = Z.certify_numeric_any(f)
        self.assertIsNotNone(got)
        self.assertIn(Z.COMPOSED_LEAN, got)

    def test_withheld_when_reducible(self):
        # (x^3 - 2)(x^3 - x - 1)
        self.assertIsNone(Z.certify_numeric_any([2, 2, 0, -3, -1, 0, 1]))


class TestLayer(unittest.TestCase):

    def test_sextic_answer_carries_statement(self):
        rd = SF.read_system(C.PRIMITIVE[0])
        self.assertTrue(rd.answered)
        self.assertIn(R.PRIMITIVE_MARK, rd.column2)

    def test_sextic_trinomial_in_letters_refused_with_reason(self):
        rd = SF.read_system("solve symbolically for x: x^6 + a*x = b")
        self.assertFalse(rd.answered)
        self.assertEqual(rd.code, "NONLINEAR")
        self.assertIn(R.PRIMITIVE_MARK, rd.value)

    def test_modes_route_states_the_reason(self):
        got = R.modes_marks()
        self.assertTrue(got["met"], got)

    def test_lean_file(self):
        got = R.lean_mark()
        self.assertTrue(got["met"], got)


class TestBatteries(unittest.TestCase):

    def test_soundness(self):
        got = R.soundness_battery()
        self.assertTrue(got["met"], got)

    def test_reach(self):
        got = R.reach_battery()
        self.assertTrue(got["met"], got)


if __name__ == "__main__":
    unittest.main()
