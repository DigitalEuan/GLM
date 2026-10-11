"""Phase 104 -- cubics, nested square roots and the positive-root dual track.

``studies/CUBIC_RADICAL_STUDY.md`` declares marks K1-K9 before any code
(:mod:`glm_universal.evaluation.cubic_radical_cases`).  These tests hold the
facts the round rests on at a sampled scale; the full measurement is
``python3 -m glm_universal.tools cubic-radical``.
"""

from __future__ import annotations

import unittest
from fractions import Fraction as F

from glm_universal.evaluation import cubic_radical_cases as C
from glm_universal.reasoning import symbolic_algebraic as A
from glm_universal.runtime import cubic_radical_report as R
from glm_universal.runtime import question_frames as qf
from glm_universal.runtime import symbolic_frames as SF


def _poly(*cs):
    return [F(c) for c in cs]


class TestAlgebraic(unittest.TestCase):

    def test_factor_rational_splits_a_quartic(self):
        fs = A.factor_rational(_poly(6, 0, -5, 0, 1))      # (x^2-2)(x^2-3)
        self.assertEqual(sorted(tuple(f) for f in fs),
                         [tuple(_poly(-3, 0, 1)), tuple(_poly(-2, 0, 1))])

    def test_factor_rational_keeps_an_irreducible_cubic(self):
        self.assertEqual(A.factor_rational(_poly(1, -3, 0, 1)),
                         [_poly(1, -3, 0, 1)])

    def test_sturm_isolates_three_roots(self):
        p = _poly(1, -3, 0, 1)
        ivs = A.isolate_real_roots(p)
        self.assertEqual(len(ivs), 3)
        for lo, hi in ivs:
            self.assertEqual(A.count_roots(A.sturm_chain(p), lo, hi), 1)

    def test_one_real_root(self):
        self.assertEqual(len(A.isolate_real_roots(_poly(1, 1, 0, 1))), 1)


class TestDeclared(unittest.TestCase):

    def test_algebraic_cases(self):
        out = R.algebraic_marks(run_scripts=False)
        self.assertEqual(out["passed"], out["of"])

    def test_radical_cases(self):
        out = R.radical_marks(run_scripts=False)
        self.assertEqual(out["passed"], out["of"])

    def test_refusals(self):
        out = R.refusal_marks()
        self.assertEqual(out["passed"], len(C.REFUSALS))

    def test_dual_cases(self):
        out = R.dual_marks(run_scripts=False)
        self.assertEqual(out["passed"], len(C.DUAL))


class TestTwoTracks(unittest.TestCase):
    """The owner's rule: keep both tracks; default to the stronger."""

    Q = "solve symbolically for x, y in terms of r, m: x^2 + y^2 = r^2; y = m*x"

    def test_circle_and_line_gives_both_points(self):
        rd = SF.read_system(self.Q)
        self.assertTrue(rd.answered)
        self.assertTrue(rd.value.startswith("2 solutions"))
        default = rd.value.split("[")[0]
        self.assertNotIn("x = y/m", default)
        self.assertNotIn("m != 0", default)
        self.assertIn("by substitution alone", rd.value)   # track kept
        self.assertTrue(qf.run_gate(rd.script)[0])

    def test_phase_103_reading_is_unchanged(self):
        rd = SF.read_system(self.Q, phase=103)
        self.assertIn("(the positive root)", rd.value)
        self.assertNotIn("solutions", rd.value)

    def test_mutant_rejected(self):
        self.assertFalse(qf.run_gate(SF.mutated(self.Q).script)[0])


class TestDefects(unittest.TestCase):

    def test_non_real_conjugate_dropped(self):
        rd = SF.read_system(
            "solve symbolically for x in terms of a: "
            "x^4 - 2*a^2*x^2 - a^4 = 0")
        self.assertTrue(rd.value.startswith("2 solutions"))
        self.assertNotIn("1 - 2^(1/2)", rd.value)

    def test_radical_power_prints_unambiguously(self):
        q = "solve symbolically for x, y: x^2 = 2; y^2 = x"
        rd = SF.read_system(q, phase=103)
        self.assertIn("(2^(1/4))^2", rd.value)
        self.assertTrue(qf.run_gate(rd.script)[0])

    def test_cubic_three_real_roots(self):
        rd = SF.read_system("solve symbolically for x: x^3 - 3*x + 1 = 0")
        self.assertTrue(rd.value.startswith("3 solutions"))
        self.assertTrue(qf.run_gate(rd.script)[0])


class TestLean(unittest.TestCase):

    def test_lean_file_present(self):
        self.assertTrue(R.lean_mark()["met"])


if __name__ == "__main__":
    unittest.main()
