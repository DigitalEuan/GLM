"""Phase 103 -- nonlinear elimination (systems substitution cannot isolate).

``studies/NONLINEAR_ELIMINATION_STUDY.md`` declares marks E1-E7 before any
code (:mod:`glm_universal.evaluation.nonlinear_cases`).  These tests hold the
facts the round rests on at a sampled scale; the full measurement is
``python3 -m glm_universal.tools nonlinear``.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.evaluation import nonlinear_cases as C
from glm_universal.reasoning import symbolic as S
from glm_universal.reasoning import symbolic_nonlinear as N
from glm_universal.runtime import nonlinear_report as NR
from glm_universal.runtime import question_frames as qf
from glm_universal.runtime import symbolic_frames as SF


class TestAlgebra(unittest.TestCase):

    def test_resultant_of_two_lines(self):
        x, y = S.Poly.var("x"), S.Poly.var("y")
        # Res_x(x - y, x + y - 2) = (1)(-2 + y) - (-y)(1) up to sign: 2y - 2
        r = N.resultant(x - y, x + y - S.Poly.const(2), "x")
        self.assertEqual(S.RF(r) * S.RF(r), S.RF((y * 2 - 2) * (y * 2 - 2)))

    def test_resultant_vanishes_at_a_common_root(self):
        x, y = S.Poly.var("x"), S.Poly.var("y")
        f = x * x + y * y - S.Poly.const(13)
        g = x * x - x * y + y * y - S.Poly.const(7)
        r = N.resultant(f, g, "y")
        for x0 in (2, 3, -2, -3):
            self.assertEqual(r.evaluate({"x": Fraction(x0)}), 0)

    def test_poly_sqrt(self):
        a, b = S.Poly.var("a"), S.Poly.var("b")
        sq = (a * 3 - b * 2 + 1) * (a * 3 - b * 2 + 1)
        r = N.poly_sqrt(sq)
        self.assertIsNotNone(r)
        self.assertEqual(r * r, sq)
        self.assertIsNone(N.poly_sqrt(a * a + b * b))
        self.assertIsNone(N.poly_sqrt(a * a * 2))

    def test_square_part(self):
        r, m = S.Poly.var("r"), S.Poly.var("m")
        outer, rest = N._square_part(r * r * (m * m + 1) * 4)
        self.assertEqual(outer * outer * S.RF(rest),
                         S.RF(r * r * (m * m + 1) * 4))
        self.assertEqual(rest, m * m + 1)


class TestDeclared(unittest.TestCase):

    def test_every_declared_branch_set(self):
        for cid, q, declared in C.SYSTEMS:
            if cid == "circle-and-line":
                continue                  # read by substitution (study §3)
            br = SF.solve_branches(q, phase=103)[0]
            m = NR.branch_matches(br.solutions, declared)
            self.assertEqual((m["matched"], m["machine"]),
                             (len(declared), len(declared)), cid)

    def test_circle_and_line_by_the_branch_layer(self):
        cid, q, declared = [c for c in C.SYSTEMS
                            if c[0] == "circle-and-line"][0]
        m = NR.branch_matches(SF.solve_branches(q)[0].solutions, declared)
        self.assertEqual(m["matched"], 2)

    def test_refusals_by_name(self):
        for cid, q, code in C.REFUSALS:
            # the operation as Phase 103 shipped it; Phase 104 answers the
            # cubic and the nested radical (tests/test_cubic_radical.py)
            self.assertEqual(SF.read_system(q, phase=103).code, code, cid)

    def test_layer_off_restores_phase98(self):
        q = "solve symbolically for x, y: x*y = 1; x + y = 3"
        self.assertEqual(SF.read_system(q, nonlinear=False).code,
                         "NONLINEAR")
        self.assertTrue(SF.read_system(q).answered)

    def test_gate_and_mutant(self):
        q = ("solve symbolically for v1, v2 in terms of m1, m2, u: "
             "m1*v1 + m2*v2 = m1*u; m1*v1^2 + m2*v2^2 = m1*u^2")
        r = SF.read_system(q)
        self.assertTrue(r.answered)
        self.assertTrue(qf.run_gate(r.script)[0])
        self.assertFalse(qf.run_gate(SF.mutated(q).script)[0])

    def test_no_solution_lost_on_a_vanishing_coefficient(self):
        # (x - 1)(3x + 5 + 3y) = 0 with a second conic through (1, -2):
        # isolating y through 3x - 3 alone would lose x = 1
        q = ("solve symbolically for x, y: 3*x^2 + 3*x*y + 2*x + -3*y + -5 "
             "= 0; 3*x^2 + -1*x*y + -2*y^2 + 2*x + 3*y + 7 = 0")
        sols = SF.solve_branches(q)[0].solutions
        self.assertTrue(any(s.values["x"][1].const_value() == 1 and
                            s.values["y"][1].const_value() == -2
                            for s in sols))

    def test_even_root_of_a_negative_is_refused(self):
        # before Phase 103 the printer was handed sqrt(-1) and raised
        r = SF.read_system("solve symbolically for x: x^2 = -4",
                           nonlinear=False)
        self.assertEqual(r.code, "NO_REAL_ROOT")


if __name__ == "__main__":
    unittest.main()
