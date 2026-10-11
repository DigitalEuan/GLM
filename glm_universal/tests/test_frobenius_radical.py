"""Phase 113 -- roots with no expression in radicals, read from one Frobenius
element.

``studies/FROBENIUS_RADICAL_STUDY.md`` measures the branch layer against marks
F1-F9 (:mod:`glm_universal.evaluation.frobenius_radical_cases`).  These tests
hold the facts the round rests on; the full measurement is
``python3 -m glm_universal.tools frobenius-radical``.
"""

from __future__ import annotations

import unittest
from fractions import Fraction as F

from glm_universal.evaluation import frobenius_radical_cases as C
from glm_universal.reasoning import symbolic_factor as Z
from glm_universal.runtime import frobenius_radical_report as R
from glm_universal.runtime import symbolic_frames as SF


class TestFrobeniusDegrees(unittest.TestCase):

    def test_x5_minus_x_minus_1_mod_2(self):
        # x^5 + x + 1 = (x^2 + x + 1)(x^3 + x^2 + 1) modulo 2
        self.assertEqual(Z.frobenius_degrees([-1, -1, 0, 0, 0, 1], 2), [2, 3])

    def test_prime_dividing_discriminant_refused(self):
        # x^2 - 2 is a square modulo 2
        self.assertIsNone(Z.frobenius_degrees([-2, 0, 1], 2))
        # leading coefficient divisible by q
        self.assertIsNone(Z.frobenius_degrees([1, 1, 3], 3))

    def test_non_affine_power(self):
        # x^5 - x - 1 modulo 2: its square is a transposition fixing 2 + ...
        self.assertEqual(Z.non_affine_power([2, 3]), (2, 2))
        # two fixed points and a 3-cycle: the element itself
        self.assertEqual(Z.non_affine_power([1, 1, 3]), (1, 2))
        # a 4-cycle beside a 2-cycle: the square fixes three points
        self.assertEqual(Z.non_affine_power([1, 2, 4]), (2, 3))
        # the affine shapes
        for degs in ([1, 1, 1, 1, 1], [5], [1, 2, 2], [1, 3, 3], [1, 1, 1]):
            self.assertIsNone(Z.non_affine_power(degs), degs)

    def test_ddf_and_shapes(self):
        got = R.ddf_agreement()
        self.assertTrue(got["met"], got)
        self.assertEqual(got["shapes"], got["shapes_ok"])


class TestCertificate(unittest.TestCase):

    def test_certifies_x5_minus_x_minus_1(self):
        got = Z.radical_free_frobenius([F(-1), F(-1), F(0), F(0), F(0), F(1)])
        self.assertIsNotNone(got)
        self.assertIn(Z.FROBENIUS_LEAN, got)
        self.assertIn("Dedekind's theorem is not checked in Lean", got)

    def test_a5_has_no_transposition_but_is_certified(self):
        got = Z.frobenius_pattern([16, 20, 0, 0, 0, 1])
        self.assertIsNotNone(got)
        self.assertNotIn(2, got[1])

    def test_withheld_for_solvable_groups(self):
        for f in ([12, -5, 0, 0, 0, 1], [12, 15, 0, 0, 0, 1],
                  [1, 3, -3, -4, 1, 1], [-2, 0, 0, 0, 0, 1]):
            self.assertIsNone(Z.certify_numeric_any(f), f)

    def test_withheld_for_composite_degree_and_reducible(self):
        self.assertIsNone(Z.radical_free_frobenius(
            [F(3), F(-6), F(0), F(0), F(0), F(0), F(1)]))
        self.assertIsNone(Z.radical_free_frobenius(
            [F(-1), F(-1), F(0), F(0), F(0), F(1)], irreducible=False))
        # (x^2 - 2)(x^3 - 3): reducible quintic
        self.assertIsNone(Z.certify_numeric_any([6, 0, -2, -3, 0, 1]))

    def test_trinks_septic_is_certified(self):
        # PSL(2, 7): no transposition, no 3-cycle, but an element fixing
        # three roots
        q, degs, m, s = Z.frobenius_pattern([3, -7, 0, 0, 0, 0, 0, 1])
        self.assertEqual((q, degs, m, s), (13, [1, 2, 4], 2, 3))

    def test_conjugation_certificate_keeps_its_words(self):
        got = Z.certify_numeric_any([2, -4, 0, 0, 0, 1])
        self.assertIn("exactly two non-real roots", got)


class TestLayer(unittest.TestCase):

    def test_case_marks(self):
        cm = R.case_marks()
        for key in ("F1", "F2", "F3"):
            self.assertTrue(cm[key]["met"], cm[key])

    def test_letter_marks(self):
        self.assertTrue(R.letter_marks()["met"])

    def test_septic_letters_reason(self):
        rd = SF.read_system("solve symbolically for x: x^7 + a*x = b")
        self.assertFalse(rd.answered)
        self.assertEqual(rd.code, "NONLINEAR")
        self.assertIn("no formula in radicals of a, b", rd.value)
        self.assertIn(R.FROBENIUS_MARK, rd.value)

    def test_soundness_battery(self):
        sb = R.soundness_battery()
        self.assertTrue(sb["met"], sb)
        self.assertGreater(sb["of"], 100)


class TestLean(unittest.TestCase):

    def test_lean_file(self):
        lm = R.lean_mark()
        self.assertTrue(lm["met"], lm)
        self.assertEqual(len(R.LEAN_THEOREMS), 9)


if __name__ == "__main__":
    unittest.main()
