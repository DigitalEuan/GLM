"""Phase 98 -- symbolic parameters (formulas in letters).

``studies/SYMBOLIC_PARAMETERS_STUDY.md`` declares marks S1-S8 before any code
(:mod:`glm_universal.evaluation.symbolic_cases`).  These tests hold the facts
the round rests on at a sampled scale; the full measurement is
``python3 -m glm_universal.tools symbolic`` (add ``--battery`` for the
post-hoc random linear-system battery).
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.evaluation import symbolic_cases as C
from glm_universal.reasoning import symbolic as S
from glm_universal.runtime import question_frames as qf
from glm_universal.runtime import symbolic_frames as SF


def _identity(a: S.RF, b: S.RF) -> bool:
    return (a - b).is_zero()


class TestPolynomialLayer(unittest.TestCase):

    def test_gcd_and_lowest_terms(self):
        p, q = S.Poly.var("p"), S.Poly.var("q")
        g = S.poly_gcd((p + q) * (p - q), (p + q) * (p * q + 1))
        self.assertEqual(g, S._monic(p + q))
        f = S.RF((p + q) * (p - q), (p + q) * 2)
        self.assertEqual(f.den, S.Poly.const(1))

    def test_trivial_gcd_certificate_is_sound(self):
        p, q, r = (S.Poly.var(x) for x in "pqr")
        # coprime: the certificate may say so
        self.assertEqual(S.poly_gcd(p * q + r, p - r * r), S.Poly.const(1))
        # a shared factor: the certificate must not hide it
        a, b = (p * q + r) * (p + 1), (p * q + r) * (q - r)
        self.assertFalse(S._gcd_is_trivial(a, b))
        self.assertEqual(S.poly_gcd(a, b), S._monic(p * q + r))

    def test_bareiss_determinant(self):
        p, q = S.Poly.var("p"), S.Poly.var("q")
        one = S.Poly.const(1)
        m = [[p, one, S.Poly()], [one, q, one], [S.Poly(), one, p]]
        # p*(q*p - 1) - 1*(p) = p^2 q - 2p
        self.assertEqual(S._bareiss_det(m), p * p * q - p * 2)

    def test_printed_formula_reads_back_to_itself(self):
        """The printer and the parser agree (the denominator's numeric factor
        over a sum is the case a Phase 98 battery caught)."""
        lcg = S.Lcg(98)
        xs = [S.Poly.var(v) for v in "pqr"]
        for _ in range(60):
            def poly():
                out = S.Poly.const(lcg.next() % 5 - 2)
                for _ in range(3):
                    out = out + xs[lcg.next() % 3] * xs[lcg.next() % 3] * \
                        Fraction(lcg.next() % 7 - 3, 1 + lcg.next() % 4)
                return out
            n, d = poly(), poly()
            if d.is_zero():
                continue
            f = S.RF(n, d)
            self.assertTrue(_identity(S.parse(S.to_text(f)), f),
                            S.to_text(f))


class TestSolveSymbolically(unittest.TestCase):

    def test_declared_systems_sample(self):
        for cid, q, expected in C.SYSTEMS[:6]:
            sol, _, _, _ = SF.solve_text(q)
            for t, exp in expected.items():
                k, v = sol.values[t]
                self.assertEqual(k, 1, cid)
                self.assertTrue(_identity(v, S.parse(exp)), cid)

    def test_answers_pass_their_gate_and_mutants_fail(self):
        for cid, q, _ in C.SYSTEMS[:4]:
            r = SF.read_system(q)
            self.assertTrue(r.answered, cid)
            self.assertTrue(qf.run_gate(r.script)[0], cid)
            m = SF.mutated(q)
            self.assertFalse(qf.run_gate(m.script)[0], cid)

    def test_refusals_by_name(self):
        for cid, q, code in C.REFUSALS:
            self.assertEqual(SF.read_system(q).code, code, cid)

    def test_four_unknowns_by_cramer(self):
        q = ("solve symbolically for a, b, c, d, e: a + b = p; b + c = q; "
             "c + d = r; d + e = s; e + a*k = t")
        r = SF.read_system(q)
        self.assertTrue(r.answered)
        self.assertIn("/(k + 1)", r.value)
        self.assertTrue(qf.run_gate(r.script)[0])

    def test_singular_four_by_four_is_refused(self):
        q = ("solve symbolically for a, b, c, d: a + b = p; b + c = q; "
             "c + d = r; d + a = s")
        r = SF.read_system(q)
        self.assertFalse(r.answered)
        self.assertEqual(r.code, "OVERDETERMINED")

    def test_two_by_two_with_content_in_the_denominator(self):
        q = ("solve symbolically for x1, x2: (-2*r)*x1 + (2*p)*x2 = q; "
             "(-1)*x1 + (1*r)*x2 = r")
        sol, _, _, _ = SF.solve_text(q)
        expected = S.parse("(2*r^2 - q)/(2*r^2 - 2*p)")
        self.assertTrue(_identity(sol.values["x2"][1], expected))
        r = SF.read_system(q)
        self.assertTrue(qf.run_gate(r.script)[0])


class TestOutsideFrames(unittest.TestCase):

    def test_two_outside_frames(self):
        from glm_universal.evaluation import question_set_b_cases as qc
        for i in (10, 33):
            text = qc.outside()[i].text
            rd = qf.read(text)
            self.assertIsNotNone(rd, i)
            self.assertTrue(rd.answered, i)
            self.assertTrue(rd.gate and rd.gate[0], i)
            self.assertIn(C.OUTSIDE_S[i], rd.value, i)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
