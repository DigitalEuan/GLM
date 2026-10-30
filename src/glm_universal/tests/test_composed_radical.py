"""Phase 115 -- roots with no expression in radicals through a composition
``g(h(x))``.

``studies/COMPOSED_RADICAL_STUDY.md`` measures the branch layer against marks
C1-C8 (:mod:`glm_universal.evaluation.composed_radical_cases`).  These tests
hold the facts the round rests on; the full measurement is
``python3 -m glm_universal.tools composed-radical``.
"""

from __future__ import annotations

import unittest
from fractions import Fraction as F

from glm_universal.evaluation import composed_radical_cases as C
from glm_universal.reasoning import symbolic_factor as Z
from glm_universal.runtime import composed_radical_report as R
from glm_universal.runtime import symbolic_frames as SF


def _q(ints):
    return [F(c) for c in ints]


class TestDecomposition(unittest.TestCase):

    def test_compose(self):
        # (x^2 + x)^2 - 1 = x^4 + 2x^3 + x^2 - 1
        self.assertEqual(Z.compose(_q([-1, 0, 1]), _q([0, 1, 1])),
                         _q([-1, 0, 1, 2, 1]))

    def test_decomposes_the_declared_cases(self):
        for _, g, h in C.COMPOSED:
            f = Z.compose(_q(g), _q(h))
            got = Z.decompose(f, len(h) - 1)
            self.assertIsNotNone(got)
            self.assertEqual(Z.compose(*got), f)
            # h is monic with h(0) = 0, so it is h itself here
            self.assertEqual(got[1], _q(h))
            self.assertEqual(got[0], _q(g))

    def test_normalises_the_inner_polynomial(self):
        # g(h + 3) with h = x^2 - x: found as g'(x^2 - x), g'(y) = g(y + 3)
        g, h = _q([-1, -1, 0, 0, 0, 1]), _q([3, -1, 1])
        f = Z.compose(g, h)
        got = Z.decompose(f, 2)
        self.assertEqual(got[1], _q([0, -1, 1]))
        self.assertEqual(Z.compose(*got), f)

    def test_non_monic_leading_coefficient(self):
        f = Z.compose(_q([1, 0, 0, 0, 0, 3]), _q([0, 2, 1]))
        got = Z.decompose(f, 2)
        self.assertIsNotNone(got)
        self.assertEqual(Z.compose(*got), f)

    def test_indecomposable(self):
        # x^10 - x - 1 is not a composition at any inner degree
        f = _q([-1, -1] + [0] * 8 + [1])
        self.assertEqual(Z.decompositions(f), [])
        self.assertIsNone(Z.decompose(f, 3))   # 3 does not divide 10


class TestCertificate(unittest.TestCase):

    def test_certifies_the_phase_114_limit(self):
        f = _q([-1, 0, -1, 0, 0, 0, 0, 0, 0, 0, 1])
        got = Z.radical_free_galois(f)
        self.assertIsNotNone(got)
        self.assertIn(Z.COMPOSED_LEAN, got)
        self.assertIn("g(y) = y^5 - y - 1", got)
        self.assertIn("h(x) = x^2", got)
        self.assertIn(Z.FROBENIUS_LEAN, got)

    def test_the_lean_instance_nests_the_conjugation_certificate(self):
        got = Z.radical_free_composed(_q([2, 0, -4, 0, 0, 0, 0, 0, 0, 0, 1]))
        self.assertIn(Z.RADICAL_FREE_LEAN, got)
        self.assertIn(Z.COMPOSED_LEAN, got)

    def test_withheld_for_solvable_outer_polynomials(self):
        for g in C.SOLVABLE_QUINTICS:
            f = [int(c) for c in Z.compose(_q(g), _q([0, 0, 1]))]
            self.assertIsNone(Z.certify_numeric_any(f), f)

    def test_withheld_for_outer_degree_below_five(self):
        # x^8 - x^2 - 1 = g(x^2), g a quartic
        self.assertIsNone(Z.radical_free_composed(
            _q([-1, 0, -1, 0, 0, 0, 0, 0, 1])))

    def test_primitive_wording_kept_where_it_applies(self):
        f = _q([-1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 1])     # x^10 - x - 1
        got = Z.radical_free_galois(f)
        self.assertIn(Z.PRIMITIVE_LEAN, got)
        self.assertNotIn(Z.COMPOSED_LEAN, got)


class TestLayer(unittest.TestCase):

    def test_cases(self):
        got = R.case_marks()
        self.assertTrue(got["C1"]["met"], got["C1"])
        self.assertTrue(got["C2"]["met"], got["C2"])

    def test_letters(self):
        got = R.letter_marks()
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

    def test_decompositions_exact(self):
        got = R.decomposition_mark()
        self.assertTrue(got["met"], got)


if __name__ == "__main__":
    unittest.main()
