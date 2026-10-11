"""Phase 112 -- factoring past degree 6, and roots with no expression in
radicals.

``studies/QUINTIC_RADICAL_STUDY.md`` measures the branch layer against marks
R1-R7 (:mod:`glm_universal.evaluation.quintic_radical_cases`).  These tests
hold the facts the round rests on; the full measurement is
``python3 -m glm_universal.tools quintic-radical``.
"""

from __future__ import annotations

import unittest
from fractions import Fraction as F

from glm_universal.evaluation import quintic_radical_cases as C
from glm_universal.reasoning import symbolic_algebraic as A
from glm_universal.reasoning import symbolic_factor as Z
from glm_universal.runtime import quintic_radical_report as R
from glm_universal.runtime import symbolic_frames as SF


def _mul(a, b):
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return out


class TestZassenhaus(unittest.TestCase):

    def test_splits_an_octic_into_two_quartics(self):
        self.assertEqual(Z.zassenhaus([6, 0, 0, 0, -5, 0, 0, 0, 1]),
                         [[-3, 0, 0, 0, 1], [-2, 0, 0, 0, 1]])

    def test_keeps_x4_plus_1_whole(self):
        # x^4 + 1 splits modulo every prime but is irreducible over Q:
        # the recombination must find no factor
        self.assertEqual(Z.zassenhaus([1, 0, 0, 0, 1]), [[1, 0, 0, 0, 1]])

    def test_product_of_factors_is_the_input(self):
        f = _mul(_mul([1, 0, 0, 0, 1], [-2, 0, 0, 1]),
                 [3, 1, 0, 0, 0, 0, 0, 2])
        got = Z.zassenhaus(f)
        prod = [1]
        for g in got:
            prod = _mul(prod, g)
        self.assertEqual(prod, f)
        self.assertEqual(sorted(len(g) - 1 for g in got), [1, 3, 4, 6])

    def test_modular_factors_multiply_back(self):
        f = [2, -4, 0, 0, 0, 1]
        for p in (3, 7, 11):
            facs = Z.factor_mod_p(f, p)
            prod = [1]
            for g in facs:
                prod = [x % p for x in _mul(prod, g)]
            self.assertEqual(prod, [x % p for x in f])

    def test_factor_rational_reaches_past_degree_six(self):
        fs = A.factor_rational([F(c) for c in (1, -3, 0, 0, 0, 0, 0, 1)])
        self.assertEqual(len(fs), 1)
        self.assertEqual(len(fs[0]) - 1, 7)

    def test_agrees_with_kronecker(self):
        self.assertTrue(R.agreement_battery()["met"])


class TestCertificate(unittest.TestCase):

    def test_certifies_the_trinomial(self):
        self.assertIsNotNone(Z.certify_numeric([2, -4, 0, 0, 0, 1]))

    def test_does_not_certify_one_real_root(self):
        # x^5 - x - 1 has Galois group S5, but only one real root: the
        # certificate is sufficient, not necessary
        self.assertIsNone(Z.certify_numeric([-1, -1, 0, 0, 0, 1]))

    def test_does_not_certify_a_composite_degree(self):
        self.assertIsNone(Z.certify_numeric([3, -6, 0, 0, 0, 0, 1]))

    def test_certificate_cites_the_lean_theorem(self):
        self.assertIn(Z.RADICAL_FREE_LEAN,
                      Z.certify_numeric([3, -6, 0, 0, 0, 1]))

    def test_certificate_and_controls(self):
        m = R.certificate_marks()
        self.assertTrue(m["R2"]["met"])
        self.assertTrue(m["R3"]["met"])


class TestReadings(unittest.TestCase):

    def test_high_degree_questions(self):
        self.assertTrue(R.high_marks(run_scripts=True)["met"])

    def test_letters(self):
        self.assertTrue(R.letter_marks()["met"])

    def test_quintic_in_letters_still_refused_nonlinear(self):
        rd = SF.read_system("solve symbolically for x: x^5 + p*x = q")
        self.assertFalse(rd.answered)
        self.assertEqual(rd.code, "NONLINEAR")
        self.assertIn("no formula in radicals of p, q", rd.value)

    def test_planted_battery(self):
        b = R.planted_battery(run_scripts=False)
        self.assertEqual(b["wrong"], 0)
        self.assertTrue(b["met"])

    def test_lean_file(self):
        self.assertTrue(R.lean_mark()["met"])

    def test_case_ids_are_unique(self):
        ids = [c[0] for c in C.HIGH] + [c[0] for c in C.LETTERS]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
