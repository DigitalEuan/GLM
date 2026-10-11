"""Phase 109 -- the three items left open by the sharpening pass.

Recorded in ``STATUS.md`` and ``MASTER_PLAN.md`` (Phase 109) and in
``studies/CUBIC_TRIG_STUDY.md`` §5 (the Phase 109 addendum).  These tests hold:

* **four or more degrees of freedom, stepwise** (decision point
  ``modes.higher``): a definite quartic is answered by the depressed
  quartic, its resolvent cubic and the half-sums of square roots (Ferrari),
  a definite polynomial of degree five or more by named roots with their sum
  and product; the column-3 script verifies both and rejects a mutant; the
  formulas the answer prints are checked exactly on a quartic with rational
  roots;
* **the discriminant's sign by factorisation** (``reasoning/sign_factor.py``):
  a discriminant that is a square times a plainly signed factor is decided,
  the route follows, the script verifies, and switching the decider off
  restores the case split;
* **the ``report routes`` subject**: every decision point, its routes, and
  the route each reference problem takes, with a column-3 script that
  recomputes them.
"""

from __future__ import annotations

import time
from pathlib import Path
import unittest
from fractions import Fraction as F

from glm_universal.reasoning import derivation as D
from glm_universal.reasoning import routes as R
from glm_universal.reasoning import sign_factor as SG
from glm_universal.reasoning import symbolic as S
from glm_universal.runtime import derivation_frames as DF
from glm_universal.runtime import question_frames as qf
from glm_universal.runtime import route_report as RR
from glm_universal.runtime import symbolic_frames as SF

PEND4 = ("Find the normal modes of a quadruple pendulum with masses m1, m2, "
         "m3, m4 and lengths l1, l2, l3, l4")
PEND5 = "Find the normal modes of an identical quintuple pendulum"


def _chain():
    return next(f for f in DF.OUTSIDE_P_FRAMES if f.name == "chain_pendulum")


class TestHigherModes(unittest.TestCase):

    def test_quadruple_pendulum_is_answered_by_ferrari(self):
        t0 = time.monotonic()
        rd = qf.read(PEND4)
        self.assertLess(time.monotonic() - t0, 60)
        self.assertTrue(rd.answered, rd.value)
        self.assertIn("normal modes, stepwise", rd.value)
        self.assertIn("resolvent cubic", rd.value)
        self.assertIn("all four roots are real and positive", rd.value)
        self.assertIn("route ferrari at modes.higher", rd.column2)
        self.assertTrue(qf.run_gate(rd.script, 60)[0])
        g = DF._m_chain_pendulum(qf.normalise(PEND4))
        self.assertEqual(g["n"], 4)
        self.assertFalse(qf.run_gate(DF.mutated_outside(_chain(), g).script,
                                     60)[0])

    def test_quintuple_pendulum_names_its_roots(self):
        rd = qf.read(PEND5)
        self.assertTrue(rd.answered, rd.value)
        self.assertIn("no general solution in radicals", rd.value)
        self.assertIn("all five roots are real and positive", rd.value)
        self.assertIn("their sum is 25*g/l", rd.value)
        self.assertIn("their product 120*g^5/l^5", rd.value)
        self.assertIn("route named at modes.higher", rd.column2)
        self.assertTrue(qf.run_gate(rd.script, 60)[0])
        g = DF._m_chain_pendulum(qf.normalise(PEND5))
        self.assertFalse(qf.run_gate(DF.mutated_outside(_chain(), g).script,
                                     60)[0])

    def test_identical_quadruple_is_the_laguerre_quartic(self):
        mo = D.equations_of_motion(DF.chain_lagrangian(4, ["m"] * 4,
                                                       ["l"] * 4),
                                   [f"th{i}" for i in range(1, 5)], True)
        pt = {"m": F(1), "l": F(1), "g": F(1)}
        got = [c.evaluate(pt) for c in mo.modes_poly]
        # 24 L_4(x): x^4 - 16x^3 + 72x^2 - 96x + 24
        self.assertEqual(got, [24, -96, 72, -16, 1])
        self.assertEqual(mo.modes_method, "ferrari")

    def test_the_printed_ferrari_steps_are_right_on_rational_roots(self):
        # a quartic a*(w - 1)(w - 2)(w - 4)(w - 7) with a = 3
        a = F(3)
        roots = [F(1), F(2), F(4), F(7)]
        cs = [F(1)]
        for r in roots:
            cs = [F(0)] + cs
            for i in range(len(cs) - 1):
                cs[i] -= r * cs[i + 1]
        e, d, c, b, aa = [a * x for x in cs]
        self.assertEqual(aa, a)
        # step 1 -- the formulas exactly as the answer prints them
        p = (8 * a * c - 3 * b ** 2) / (8 * a ** 2)
        q = (b ** 3 - 4 * a * b * c + 8 * a ** 2 * d) / (8 * a ** 3)
        r = (16 * a * b ** 2 * c - 64 * a ** 2 * b * d - 3 * b ** 4 +
             256 * a ** 3 * e) / (256 * a ** 4)
        ys = [w + b / (4 * a) for w in roots]
        self.assertEqual(sum(ys), 0)
        for y in ys:
            self.assertEqual(y ** 4 + p * y ** 2 + q * y + r, 0)
        # step 2 -- the resolvent's roots are (y1 + yj)^2
        A, B, C = 2 * p, p * p - 4 * r, -q * q
        zs = sorted(((ys[0] + ys[j]) ** 2 for j in (1, 2, 3)), reverse=True)
        for z in zs:
            self.assertEqual(z ** 3 + A * z ** 2 + B * z + C, 0)
        # step 3 -- s1 = sqrt(z1), s2 = sqrt(z2), s3 = -q/(s1 s2)
        s1 = next(x for x in (ys[0] + ys[j] for j in (1, 2, 3))
                  if x * x == zs[0])
        s2 = next(x for x in (ys[0] + ys[j] for j in (1, 2, 3))
                  if x * x == zs[1])
        s1, s2 = abs(s1), abs(s2)
        s3 = -q / (s1 * s2)
        self.assertEqual(s3 * s3, zs[2])
        got = sorted(-b / (4 * a) + (u1 * s1 + u2 * s2 + u3 * s3) / 2
                     for u1, u2, u3 in ((1, 1, 1), (1, -1, -1), (-1, 1, -1),
                                        (-1, -1, 1)))
        self.assertEqual(got, roots)

    def test_the_answer_prints_those_formulas(self):
        rd = qf.read(PEND4)
        for piece in ("p = (8*a*c - 3*b^2)/(8*a^2)",
                      "q = (b^3 - 4*a*b*c + 8*a^2*d)/(8*a^3)",
                      "r = (16*a*b^2*c - 64*a^2*b*d - 3*b^4 + 256*a^3*e)/"
                      "(256*a^4)",
                      "A = 2*p, B = p^2 - 4*r, C = -q^2",
                      "s3 = -q/(s1*s2)",
                      "-b/(4*a) + (-s1 - s2 + s3)/2"):
            self.assertIn(piece, rd.value)

    def test_an_indefinite_mass_matrix_goes_to_the_solver(self):
        L = ("(1/2)*(a - b)*x1_dot^2 + (1/2)*x2_dot^2 + (1/2)*x3_dot^2 + "
             "(1/2)*x4_dot^2 - (1/2)*k*(x1^2 + x2^2 + x3^2 + x4^2)")
        mo = D.equations_of_motion(L, ["x1", "x2", "x3", "x4"], True)
        self.assertIn("route solver at modes.higher", mo.modes_route)
        self.assertIsNone(mo.modes_poly)
        self.assertEqual(len(mo.frequencies), 2)

    def test_the_frame_reads_four_and_five_links(self):
        for text, n in (("normal modes of a quadruple pendulum", 4),
                        ("normal modes of a four-link pendulum", 4),
                        ("normal modes of a 5-link pendulum", 5),
                        ("normal modes of a quintuple pendulum", 5)):
            g = DF._m_chain_pendulum(text)
            self.assertIsNotNone(g, text)
            self.assertEqual(g["n"], n, text)


class TestSignByFactorisation(unittest.TestCase):

    def _poly(self, text):
        rf = S.parse(text)
        return rf.num * rf.den

    def test_square_times_plain_factor_is_decided(self):
        cases = {"(a - b)^6*(c^2 + 1)": 1,
                 "-(a - b)^2*(2*a + b)^2*(a + 2*b)^2/108": -1,
                 "3*(a - b)^2*(a + b)^4": 1,
                 "-(a^2 + b^2)*(a - b)^2*c^2": -1,
                 "(a - b)^3": None, "a^2 - a + 1": None, "x*(x^2 + 1)": None}
        for text, want in cases.items():
            self.assertEqual(SG.decided_sign(self._poly(text))[0], want, text)

    def test_the_factors_multiply_back(self):
        for text in ("(a - b)^6*(c^2 + 1)", "x^2*y*(x - y)^3*(x + 2*y)",
                     "-(1/108)*(a - b)^2*(2*a + b)^2*(a + 2*b)^2"):
            p = self._poly(text)
            c, factors = SG.square_free(p)
            prod = S.Poly.const(c)
            for f, e in factors:
                prod = prod * f ** e
            self.assertTrue((prod - p).is_zero(), text)
            for i, (f, _) in enumerate(factors):
                for g, _ in factors[i + 1:]:
                    self.assertTrue(S.poly_gcd(f, g).is_const(), text)

    def test_a_decided_positive_discriminant_takes_cardano(self):
        text = "solve symbolically for x: x^3 + 3*(a - b)^2*x = 2*(a - b)^3"
        rd = SF.read_system(text)
        self.assertTrue(rd.answered, rd.value)
        self.assertNotIn("by cases", rd.value)
        self.assertIn("route cardano at cubic.letters", rd.column2)
        self.assertIn("by factorisation", rd.column2)
        self.assertTrue(qf.run_gate(rd.script, 30)[0])
        self.assertFalse(qf.run_gate(
            SF.read_system(text, scale_first=F(2)).script, 30)[0])

    def test_a_decided_negative_discriminant_takes_viete(self):
        text = ("solve symbolically for x: x^3 - (a^2 + a*b + b^2)*x + "
                "a*b*(a + b) = 0")
        rd = SF.read_system(text)
        self.assertTrue(rd.answered, rd.value)
        self.assertIn("route viete at cubic.letters", rd.column2)
        self.assertIn("by factorisation", rd.column2)
        self.assertTrue(qf.run_gate(rd.script, 30)[0])

    def test_switching_the_decider_off_restores_the_split(self):
        text = "solve symbolically for x: x^3 + 3*(a - b)^2*x = 2*(a - b)^3"
        with R.disabled("cubic.letters:factor"):
            rd = SF.read_system(text)
        self.assertIn("route cases at cubic.letters", rd.column2)
        self.assertNotIn("by factorisation", rd.column2)

    def test_the_undecided_case_still_splits(self):
        rd = SF.read_system("solve symbolically for x: x^3 + p*x = q")
        self.assertIn("by cases", rd.value)


class TestRouteReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from glm_universal.runtime.session import GeometricSession
        cls.solution = GeometricSession().ask("report routes")

    def test_the_subject_is_registered(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        self.assertIn("routes", REPORT_SUBJECTS)

    def test_every_point_and_every_route_is_listed(self):
        self.assertEqual(self.solution.kind, "report")
        self.assertEqual(self.solution.expected["points"], str(len(R.POINTS)))
        self.assertEqual(self.solution.expected["routes"],
                         str(sum(len(v) for v in R.POINTS.values())))
        text = " ".join(s.language for s in self.solution.steps) \
            if hasattr(self.solution.steps[0], "language") else \
            repr(self.solution.steps)
        for point, rows in R.POINTS.items():
            self.assertIn(point, text)
            for route, _ in rows:
                self.assertIn(route, text)

    def test_every_route_is_reached_by_a_reference_problem(self):
        self.assertEqual(self.solution.expected["holds"], "True")
        self.assertEqual(self.solution.expected["unreached"], "")
        self.assertEqual(self.solution.expected["as_expected"],
                         str(len(RR.REFERENCE)))

    def test_a_disabled_route_shows_in_the_report(self):
        # (a cubic route: with ferrari off the quartic in letters goes to
        # the branch layer, which is the minutes-long case Phase 109 avoids)
        with R.disabled("cubic.letters:viete"):
            report = RR.route_report()
        self.assertIn("cubic.letters:viete", report["disabled"])
        self.assertFalse(report["holds"])

    def test_column_three_recomputes_the_report(self):
        from glm_universal.runtime import tct_engine as tct
        script = tct.render_script(self.solution)
        self.assertIn("route_report", script)
        import json
        import subprocess
        import sys
        out = subprocess.run([sys.executable, "-c", script],
                             capture_output=True, text=True, timeout=300,
                             cwd=str(Path(tct.__file__).resolve()
                                     .parents[2])).stdout
        body = out.split("GLM_TCT_JSON_BEGIN", 1)[1].split(
            "GLM_TCT_JSON_END", 1)[0]
        got = json.loads(body)
        self.assertEqual(got["mismatches"], [])
        self.assertEqual(got["observed"]["holds"], "True")
