"""Tests for the tool-verdicts round (Phase 138): a tool's yes/no answer as a
stepwise step, the conditional that builds only the branch it takes, the
unrolled search with no iteration cap, the widened value phrasings, and the
nearest-fraction tool's Farey certificate (``studies/TOOL_VERDICTS_STUDY.md``,
:mod:`glm_universal.evaluation.tool_verdicts_cases`)."""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.evaluation import tool_verdicts_cases as tvd
from glm_universal.reasoning import exact_real as xr
from glm_universal.reasoning import rational_approx as ra
from glm_universal.reasoning import stepwise_script as ss
from glm_universal.runtime import stepwise, tool_values, toolbox
from glm_universal.runtime.session import GeometricSession

ROOT = Path(__file__).resolve().parents[3]
LEAN = ROOT / "src" / "lean" / tvd.LEAN_FILE


class TestTheLeanFile(unittest.TestCase):
    """T1: the classical theorem, the certificate and the search measure."""

    def test_file(self):
        text = LEAN.read_text(encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in tvd.LEAN_THEOREMS:
            with self.subTest(theorem=name):
                self.assertIn(f"theorem {name} ", text)

    def test_the_tool_cites_it(self):
        self.assertIn(tvd.LEAN_FILE,
                      toolbox.tool_named("best approximation").lean)


class TestTheFareyCertificate(unittest.TestCase):
    """The 20,000 bound is gone: every answer carries a certificate."""

    def test_no_cap_left(self):
        self.assertFalse(hasattr(ra, "EXHAUSTIVE_CAP"))
        self.assertFalse(hasattr(ra, "MAX_DENOMINATOR"))

    def test_far_past_the_old_bound(self):
        got = ra.best_approximation(xr.parse_real("pi"), 10 ** 40)
        self.assertTrue(got["ok"])
        self.assertTrue(got["certificate"]["ok"])
        self.assertIn(got["certificate"]["det"], (1, -1))
        self.assertGreater(got["certificate"]["denominator_sum"], 10 ** 40)

    def test_small_case(self):
        got = ra.best_approximation(xr.parse_real("pi"), 1000)
        self.assertEqual(got["value"], Fraction(355, 113))

    def test_certificate_rejects(self):
        pi = xr.parse_real("pi")
        # not Farey neighbours (1 * 13 - 3 * 3 = 4)
        bad = ra.farey_certificate(pi, Fraction(3, 1), Fraction(13, 3), 3)
        self.assertFalse(bad["ok"])
        # denominators do not pass the bound
        low = ra.farey_certificate(pi, Fraction(3, 1), Fraction(22, 7), 8)
        self.assertFalse(low["ok"])
        # the value is not between them
        out = ra.farey_certificate(pi, Fraction(22, 7), Fraction(19, 6), 10)
        self.assertFalse(out["ok"])
        good = ra.farey_certificate(pi, Fraction(3, 1), Fraction(22, 7), 7)
        self.assertTrue(good["ok"])

    def test_tool_text(self):
        r = toolbox.run_tool("tool best approximation sqrt(2) denominator "
                             "1000000")
        self.assertTrue(r.ok)
        self.assertIn("farey_certificate", r.text)
        self.assertNotIn("exhaustive", r.figures)


class TestTheVerdictReader(unittest.TestCase):

    def test_reads(self):
        cases = {
            "is 0xff reachable from 0x0":
                ("tool gates 0x0 to 0xff", ("flag", "reachable")),
            "can 0x7 reach 0x3 by gate moves":
                ("tool gates 0x7 to 0x3", ("flag", "reachable")),
            "is 0x3 unreachable from 0x7":
                ("tool gates 0x7 to 0x3", ("flag-not", "reachable")),
            "is the module affine_output reached by a query":
                ("tool wiring affine_output", ("flag", "reached")),
            "is 7 the second term of the continued fraction of pi":
                ("tool continued fraction pi terms 2",
                 ("equals", "index", "terms", 1, "7")),
        }
        for phrase, (text, test) in cases.items():
            with self.subTest(phrase=phrase):
                got = tool_values.read_verdict(phrase)
                self.assertIsNotNone(got)
                self.assertEqual(got.tool_text, text)
                self.assertEqual(got.test, test)

    def test_malformed_word_is_no_verdict(self):
        v = tool_values.read_verdict("is zz reachable from 0x0")
        with self.assertRaises(ValueError):
            tool_values.decide(v)

    def test_not_a_verdict(self):
        for phrase in ("the third term of the continued fraction of pi",
                       "is 113 prime", "what is 2 plus 3"):
            with self.subTest(phrase=phrase):
                self.assertIsNone(tool_values.read_verdict(phrase))


class TestTheWidenedValues(unittest.TestCase):
    """Phase 137's two held-out misses, read by the general rule."""

    def test_reads(self):
        a = tool_values.read_value("the second partial quotient of pi")
        self.assertEqual((a.tool_text, a.selector),
                         ("tool continued fraction pi terms 2",
                          ("index", "terms", 1)))
        b = tool_values.read_value("the convergent number 4 of pi")
        self.assertEqual((b.tool_text, b.selector),
                         ("tool convergent 4 of pi", ("value", "value")))


class TestTheChains(unittest.TestCase):
    """Verdicts, conditionals and the search through the stepwise planner."""

    @classmethod
    def setUpClass(cls):
        cls.session = GeometricSession()

    def ask(self, q):
        return stepwise.answer(self.session, q)

    def test_verdict(self):
        a = self.ask("is 0xff reachable from 0x0 by gate moves")
        self.assertTrue(a.answered)
        self.assertEqual(a.value, "False")
        self.assertEqual(a.chain.steps[0].detail["recompute"][0], "verdict")

    def test_conditional_builds_only_the_branch_taken(self):
        a = self.ask("if 0xff is reachable from 0x0, the number of gate moves "
                     "from 0x0 to 0xff, otherwise -1")
        self.assertEqual(a.value, "-1")
        ops = [s.op for s in a.chain.steps]
        self.assertEqual(ops, ["planned", "literal", "choose"])

    def test_conditional_on_a_planner_verdict(self):
        self.assertEqual(self.ask("if 113 is prime, 1, otherwise 0").value,
                         "1")

    def test_branch_that_refuses_refuses(self):
        a = self.ask("if 0xff is reachable from 0x0, 1, otherwise the number "
                     "of gate moves from 0x0 to 0xff")
        self.assertFalse(a.answered)

    def test_search(self):
        a = self.ask("the first convergent of sqrt(2) whose denominator "
                     "exceeds 100")
        self.assertEqual(a.value, "239/169")
        last = a.chain.steps[-1]
        self.assertEqual(last.op, "first")
        tests = [a.chain.steps[j - 1].value for j in last.inputs[:-1]]
        self.assertEqual(tests[-1], "True")
        self.assertTrue(all(t == "False" for t in tests[:-1]))

    def test_search_on_an_ending_expansion_refuses(self):
        a = self.ask("the first convergent of 22/7 whose denominator is "
                     "above 100")
        self.assertFalse(a.answered)
        self.assertIn("expansion", a.reason)

    def test_step_gate_rejects_a_wrong_branch(self):
        a = self.ask("if 113 is prime, 1, otherwise 0")
        choose = a.chain.steps[-1]
        from dataclasses import replace
        lied = replace(choose, detail=dict(choose.detail, branch="otherwise"))
        steps = list(a.chain.steps[:-1]) + [lied]
        ok, _why = ss.step_check(lied, steps)
        self.assertFalse(ok)


class TestTheHeldOutSheets(unittest.TestCase):

    def test_shapes(self):
        self.assertEqual(len(tvd.REWORDINGS_TWO), 16)
        self.assertEqual(len(tvd.VERDICTS_HELD_OUT), 14)
        ids = [c[0] for c in tvd.REWORDINGS_TWO + tvd.VERDICTS_HELD_OUT]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
