"""The sharpening pass after Phase 108 -- route selection and wiring.

Recorded in ``STATUS.md`` (§1 and §3.4) and ``MASTER_PLAN.md`` (the
sharpening pass after Phase 108), not in a study of its own.  These tests hold
what the pass changed:

* the route selector (``reasoning/routes.py``): a route is chosen by what is
  decided about the problem, recorded with its reason, and a route can be
  disabled for a measurement;
* a cubic in letters whose discriminant's sign is not decided is answered by
  cases (Cardano under ``D > 0``, Viete's three roots under ``D < 0``), with a
  column-3 script that verifies and a mutant that fails;
* a definite three-degree-of-freedom system whose characteristic cubic does
  not scale (the triple pendulum with unequal masses and lengths) is answered
  stepwise, quickly, with its script verifying and its mutant rejected;
* the double pendulum with unequal masses verifies (its frequencies hold a
  square root of an expression in the letters);
* plain phrasings reach the symbolic operation and the chain-pendulum frame;
* the monomial fast path of ``poly_gcd`` agrees with the general algorithm.
"""

from __future__ import annotations

import time
import unittest
from fractions import Fraction as F

from glm_universal.reasoning import derivation as D
from glm_universal.reasoning import routes as R
from glm_universal.reasoning import symbolic as S
from glm_universal.reasoning.symbolic import Poly
from glm_universal.runtime import derivation_frames as DF
from glm_universal.runtime import question_frames as qf
from glm_universal.runtime import symbolic_frames as SF

PEND3 = ("A triple pendulum with bobs of masses m1, m2, m3 on strings of "
         "lengths l1, l2, l3: formulate the Lagrangian and the equations of "
         "motion using the small-angle approximation.")
PEND2 = ("A double pendulum with masses m1, m2 and lengths l1, l2: formulate "
         "the Lagrangian and the equations of motion using the small-angle "
         "approximation.")
SPRINGS = ("derive equations of motion for x1, x2, x3, small oscillations: "
           "L = (1/2)*(m1*x1_dot^2 + m2*x2_dot^2 + m3*x3_dot^2) - (1/2)*("
           "k1*x1^2 + k2*(x2 - x1)^2 + k3*(x3 - x2)^2 + k4*x3^2)")
CUBIC = "solve symbolically for x in terms of p, q: x^3 + p*x = q"


class TestRoutes(unittest.TestCase):

    def test_first_holding_route_is_chosen_and_recorded(self):
        d = R.choose("test.point", [("a", False, "no"), ("b", True, "yes"),
                                    ("c", True, "also")])
        self.assertEqual((d.route, d.why), ("b", "yes"))
        self.assertEqual(R.trace()[-1], d)

    def test_disabled_route_is_skipped_inside_the_block_only(self):
        cands = [("a", True, "first"), ("b", True, "second")]
        with R.disabled("test.point:a"):
            self.assertEqual(R.choose("test.point", cands).route, "b")
        self.assertEqual(R.choose("test.point", cands).route, "a")

    def test_facts_nest_and_unwind(self):
        self.assertIsNone(R.fact("real_roots"))
        with R.facts(real_roots=True):
            self.assertTrue(R.fact("real_roots"))
            with R.facts(other=1):
                self.assertTrue(R.fact("real_roots"))
        self.assertIsNone(R.fact("real_roots"))

    def test_every_point_is_described(self):
        text = R.describe()
        for point in R.POINTS:
            self.assertIn(point, text)


class TestCaseSplit(unittest.TestCase):

    def test_undecided_discriminant_splits_into_cases(self):
        rd = SF.read_system(CUBIC)
        self.assertTrue(rd.answered)
        self.assertIn("by cases", rd.value)
        self.assertIn("> 0", rd.value)
        self.assertIn("< 0", rd.value)
        self.assertIn("route cases at cubic.letters", rd.column2)
        self.assertTrue(qf.run_gate(rd.script, 30)[0])
        bad = SF.read_system(CUBIC, scale_first=F(2))
        self.assertFalse(qf.run_gate(bad.script, 30)[0])

    def test_split_disabled_is_the_earlier_reading(self):
        with R.disabled("cubic.letters:cases"):
            rd = SF.read_system(CUBIC)
        self.assertTrue(rd.answered)
        self.assertNotIn("by cases", rd.value)
        self.assertIn("only real root", rd.value)

    def test_stated_real_roots_select_viete(self):
        from glm_universal.reasoning.symbolic_nonlinear import solve_nonlinear
        ctx = S.Context()
        eq = S.parse_equation("x^3 + p*x = q", ctx)
        with R.facts(real_roots=True):
            br = solve_nonlinear([eq], {"x"}, ["x"])
        self.assertEqual(len(br.solutions), 3)
        self.assertTrue(all(s.ext.trig for s in br.solutions))


class TestModes(unittest.TestCase):

    def test_unequal_triple_pendulum_is_answered_stepwise(self):
        t0 = time.monotonic()
        rd = qf.read(PEND3)
        self.assertLess(time.monotonic() - t0, 60)
        self.assertTrue(rd.answered)
        self.assertIn("normal modes, stepwise", rd.value)
        self.assertIn("real and positive", rd.value)
        self.assertIn("route stepwise at modes.cubic", rd.column2)
        g = DF._m_chain_pendulum(qf.normalise(PEND3))
        self.assertFalse(qf.run_gate(DF.mutated_outside(
            next(f for f in DF.OUTSIDE_P_FRAMES
                 if f.name == "chain_pendulum"), g).script, 30)[0])

    def test_stepwise_sum_and_product_reduce_to_the_identical_case(self):
        mo = D.equations_of_motion(DF.chain_lagrangian(
            3, ["m1", "m2", "m3"], ["l1", "l2", "l3"]),
            ["th1", "th2", "th3"], True)
        c0, c1, c2, c3 = mo.modes_cubic
        pt = {"m1": F(1), "m2": F(1), "m3": F(1), "l1": F(1), "l2": F(1),
              "l3": F(1), "g": F(1)}
        # lambda^3 - 9 lambda^2 + 18 lambda - 6 (Phase 108's cubic)
        self.assertEqual((-c2 / c3).evaluate(pt), 9)
        self.assertEqual((c1 / c3).evaluate(pt), 18)
        self.assertEqual((-c0 / c3).evaluate(pt), 6)

    def test_unequal_springs_stepwise(self):
        rd = DF.read_operation(SPRINGS)
        self.assertTrue(rd.answered)
        self.assertIn("normal modes, stepwise", rd.value)
        self.assertTrue(qf.run_gate(rd.script, 30)[0])
        self.assertFalse(qf.run_gate(DF.mutated_operation(SPRINGS).script,
                                     30)[0])

    def test_identical_systems_keep_the_solver_route(self):
        rd = DF.read_operation(
            "derive equations of motion for x1, x2, x3, small oscillations: "
            "L = (1/2)*m*(x1_dot^2 + x2_dot^2 + x3_dot^2) - (1/2)*k*(x1^2 + "
            "(x2 - x1)^2 + (x3 - x2)^2 + x3^2)")
        self.assertIn("normal modes: w^2 = ", rd.value)
        self.assertIn("route solver at modes.cubic", rd.column2)

    def test_unequal_double_pendulum_verifies(self):
        rd = qf.read(PEND2)
        self.assertTrue(rd.answered, rd.value)
        self.assertIn("sqrt(", rd.value)


class TestPhrasings(unittest.TestCase):

    def test_plain_solve_phrasings(self):
        cases = {
            "solve x^3 - 3*x + 1 = 0": "solve symbolically for x: "
                                       "x^3 - 3*x + 1 = 0",
            "What are the roots of x^3 + p*x = q?":
                "solve symbolically for x: x^3 + p*x = q",
            "solve x + y = 3; x - y = 1 for x, y":
                "solve symbolically for x, y: x + y = 3; x - y = 1",
            "solve for x in terms of a: x^2 = a":
                "solve symbolically for x in terms of a: x^2 = a",
        }
        for text, want in cases.items():
            self.assertEqual(SF.canonical(text), want, text)

    def test_prose_is_not_read_as_algebra(self):
        for text in ("solve the problem of the triple pendulum",
                     "Solve this: what is the speed of light?",
                     "roots of unity", "solve for x: the area is 3"):
            self.assertIsNone(SF.canonical(text), text)

    def test_chain_pendulum_without_the_word_lagrangian(self):
        g = DF._m_chain_pendulum(qf.normalise(
            "Find the normal modes of a triple pendulum with masses m1, m2, "
            "m3 and lengths l1, l2, l3"))
        self.assertIsNotNone(g)
        self.assertTrue(g["small"])

    def test_reverse_refusal_is_handed_over(self):
        from glm_universal.runtime import router
        text = "solve for x: x^3 + p*x = q"
        self.assertEqual(router.reader_of(text), "reverse")
        self.assertEqual(router.handed_surface(text, "reverse"), "frames")
        r = router.route(None, text)
        self.assertEqual(r.surface, "frames")
        self.assertTrue(r.answered)


class TestGcdFastPath(unittest.TestCase):

    def test_monomial_gcd_agrees(self):
        x, y, z = Poly.var("x"), Poly.var("y"), Poly.var("z")
        mono = x * x * y * y * y * z
        others = [x * y + z, x * x * y * (x + z), x * x * y * y * y * z * 7,
                  y * y * (x * x - 2 * z), x + 1]
        wants = [Poly.const(1), x * x * y, mono, y * y, Poly.const(1)]
        for o, w in zip(others, wants):
            self.assertEqual(S.poly_gcd(mono, o), w)
            self.assertEqual(S.poly_gcd(o, mono), w)


if __name__ == "__main__":
    unittest.main()
