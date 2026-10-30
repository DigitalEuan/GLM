"""Tests for the tool-values round (Phase 137): a tool's number taken by the
stepwise planner (:mod:`glm_universal.runtime.tool_values`), the convergent
and best-approximation tools (:mod:`glm_universal.reasoning.rational_approx`),
and the marks of ``studies/TOOL_VALUES_STUDY.md``
(:mod:`glm_universal.evaluation.tool_values_cases`)."""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.evaluation import tool_values_cases as tvc
from glm_universal.reasoning import exact_real as xr
from glm_universal.reasoning import rational_approx as ra
from glm_universal.runtime import router, stepwise, tool_values, toolbox
from glm_universal.runtime.session import GeometricSession

ROOT = Path(__file__).resolve().parents[3]
LEAN = ROOT / "src" / "lean" / tvc.LEAN_FILE
STUDY = ROOT / "studies" / "TOOL_VALUES_STUDY.md"


class TestTheLeanFile(unittest.TestCase):
    """V1: the formal half exists, names its theorems and has no sorry."""

    def test_file(self):
        text = LEAN.read_text(encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in tvc.LEAN_THEOREMS:
            with self.subTest(theorem=name):
                self.assertIn(f"theorem {name} ", text)

    def test_the_tools_cite_it(self):
        for name in ("convergent", "best approximation"):
            self.assertIn(tvc.LEAN_FILE, toolbox.tool_named(name).lean)


class TestTheReader(unittest.TestCase):
    """The noun phrases a tool value reads, and the selectors."""

    def test_reads(self):
        cases = {
            "the third term of the continued fraction of pi":
                ("tool continued fraction pi terms 3", ("index", "terms", 2)),
            "the fourth convergent of pi":
                ("tool convergent 4 of pi", ("value", "value")),
            "the denominator of the fourth convergent of pi":
                ("tool convergent 4 of pi",
                 ("part", "value", "denominator")),
            "the closest fraction to e with denominator below 100":
                ("tool best approximation e denominator 99",
                 ("value", "value")),
            "the sum of the first five terms of the continued fraction of e":
                ("tool continued fraction e terms 5",
                 ("fold", "terms", "sum", 5)),
        }
        for phrase, (text, sel) in cases.items():
            with self.subTest(phrase=phrase):
                got = tool_values.read_value(phrase)
                self.assertIsNotNone(got)
                self.assertEqual(got.tool_text, text)
                self.assertEqual(got.selector, sel)

    def test_unread(self):
        for phrase in ("the atomic number of iron", "the colour of pi",
                       "the third term of the sequence"):
            with self.subTest(phrase=phrase):
                self.assertIsNone(tool_values.read_value(phrase))

    def test_selectors(self):
        figs = {"terms": [3, 7, 15, 1], "value": "355/113",
                "m": {"16": 196560}}
        self.assertEqual(tool_values.select(figs, ("index", "terms", 2)), 15)
        self.assertEqual(tool_values.select(figs, ("fold", "terms", "max",
                                                   4)), 15)
        self.assertEqual(tool_values.select(figs, ("fold", "terms", "mean",
                                                   4)), Fraction(13, 2))
        self.assertEqual(tool_values.select(figs, ("part", "value",
                                                   "numerator")), 355)
        self.assertEqual(tool_values.select(figs, ("entry", "m", "16")),
                         196560)
        with self.assertRaises(ValueError):
            tool_values.select(figs, ("index", "terms", 9))


class TestRationalApproximation(unittest.TestCase):
    """V4-V5 on small samples; the full grids are the marks."""

    def test_convergents_of_pi(self):
        terms = (3, 7, 15, 1, 292)
        self.assertEqual([str(ra.convergent(terms, k)) for k in range(1, 6)],
                         ["3", "22/7", "333/106", "355/113", "103993/33102"])

    def test_best_against_exhaustive(self):
        for x, n in (("pi", 1000), ("sqrt(2)", 100), ("e", 300),
                     ("sqrt(3)", 50), ("2^(1/3)", 77)):
            with self.subTest(x=x, n=n):
                real = xr.parse_real(x)
                got = ra.best_approximation(real, n)
                self.assertTrue(got["ok"])
                self.assertEqual(got["value"],
                                 ra.exhaustive_nearest(real, n)["value"])

    def test_exact_input(self):
        got = ra.best_approximation(xr.from_fraction(Fraction(22, 7)), 10)
        self.assertEqual(got["value"], Fraction(22, 7))

    def test_tool_refusals(self):
        self.assertFalse(toolbox.run_tool("tool convergent 3 of 7/3").ok)
        self.assertFalse(toolbox.run_tool("tool convergent 4 of banana").ok)
        self.assertFalse(toolbox.run_tool(
            "tool best approximation pi denominator 0").ok)


class TestComposition(unittest.TestCase):
    """V2, V6 and V7 on samples."""

    @classmethod
    def setUpClass(cls):
        cls.session = GeometricSession()

    def test_composed(self):
        for q, want in tvc.COMPOSED[:6]:
            with self.subTest(q=q):
                a = stepwise.answer(self.session, q)
                self.assertEqual(a.value if a.answered else "refuse", want)

    def test_tool_refusal_is_the_chain_refusal(self):
        a = stepwise.answer(self.session,
                            "twice the 50th term of the continued fraction "
                            "of pi")
        self.assertFalse(a.answered)

    def test_switch_off_restores_the_refusal(self):
        q = "twice the third term of the continued fraction of pi"
        stepwise.TOOL_VALUES = False
        try:
            self.assertFalse(stepwise.answer(self.session, q).answered)
        finally:
            stepwise.TOOL_VALUES = True
        self.assertTrue(stepwise.answer(self.session, q).answered)

    def test_single_value_through_the_router(self):
        r = router.route(self.session, "what is the fourth convergent of pi")
        self.assertTrue(r.answered)
        self.assertEqual(r.surface, "toolbox")
        self.assertIn("355/113", r.text)

    def test_no_declared_text_is_read(self):
        sets = router._declared_sets()
        for texts in sets.values():
            for t in texts:
                with self.subTest(t=t):
                    self.assertIsNone(tool_values.read_value(t))


class TestTheStudy(unittest.TestCase):

    def test_study_exists_and_names_the_marks(self):
        text = STUDY.read_text(encoding="utf-8")
        for mark in ("V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8"):
            self.assertIn(mark, text)


if __name__ == "__main__":
    unittest.main()
