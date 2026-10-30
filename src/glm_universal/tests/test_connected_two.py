"""Tests for the second connected-machine round (Phase 136): the new tools of
:mod:`glm_universal.runtime.toolbox`, the English openings the router reads
after a refusal, the wiring census, and the marks of
``studies/CONNECTED_MACHINE_TWO_STUDY.md``
(:mod:`glm_universal.evaluation.connected_two_cases`)."""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.evaluation import connected_two_cases as c2
from glm_universal.reasoning import exact_real as xr
from glm_universal.reasoning import substrate_cognition as sc
from glm_universal.runtime import router, toolbox

ROOT = Path(__file__).resolve().parents[3]
LEAN = ROOT / "src" / "lean" / c2.LEAN_FILE
STUDY = ROOT / "studies" / "CONNECTED_MACHINE_TWO_STUDY.md"


class TestTheWiringCensus(unittest.TestCase):
    """W1: every reasoning module is reached from the answering path or
    declared measurement-only, with a reason."""

    def test_no_module_is_left_behind(self):
        c = toolbox.wiring_census()
        self.assertEqual(c["undeclared"], [])
        self.assertEqual(c["stale_declarations"], [])
        self.assertEqual(c["reached"] + len(c["declared"]), c["reasoning"])

    def test_every_declaration_has_a_reason(self):
        for name, reason in toolbox.MEASUREMENT_ONLY.items():
            with self.subTest(module=name):
                self.assertTrue((ROOT / "src" / "glm_universal" /
                                 "reasoning" / f"{name}.py").exists())
                self.assertGreater(len(reason), 20)


class TestTheLeanFile(unittest.TestCase):
    """W2: the formal half exists, names its theorems and has no sorry."""

    def test_file(self):
        text = LEAN.read_text(encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in c2.LEAN_THEOREMS:
            with self.subTest(theorem=name):
                self.assertIn(f"theorem {name} ", text)

    def test_the_tools_cite_it(self):
        for name in ("continued fraction", "mobius"):
            self.assertIn(c2.LEAN_FILE, toolbox.tool_named(name).lean)


class TestTheStreams(unittest.TestCase):
    """W3-W5 on small samples; the full batteries are the marks."""

    def test_surds_against_the_integer_recurrence(self):
        for n in (2, 3, 7, 13, 19, 31, 43):
            with self.subTest(n=n):
                got = sc.cf_certified(xr.parse_real(f"sqrt({n})"), 16)
                self.assertTrue(got[2])
                self.assertEqual(got[0], c2.quadratic_cf(0, n, 1, 16))

    def test_pi_and_e(self):
        self.assertEqual(sc.cf_certified(xr.parse_real("pi"), 20)[0],
                         c2.PI_TERMS)
        self.assertEqual(sc.cf_certified(xr.parse_real("e"), 20)[0],
                         c2.e_terms(20))

    def test_mobius_against_the_quadratic_recurrence(self):
        for a, b, c, d, n in c2.MOBIUS_CASES[:6]:
            with self.subTest(case=(a, b, c, d, n)):
                got = toolbox.run_tool(f"tool mobius {a} {b} {c} {d} of "
                                       f"sqrt({n}) terms 12")
                self.assertTrue(got.ok, got.text)
                self.assertEqual(tuple(got.figures["terms"]),
                                 c2.mobius_quadratic_cf(a, b, c, d, n, 12))
                self.assertTrue(got.figures["direct_agrees"])

    def test_a_rational_expression_never_gets_a_wrong_term(self):
        for text, value in c2.RATIONAL_EXPRESSIONS:
            with self.subTest(text=text):
                terms, _, complete = sc.cf_certified(xr.parse_real(text), 6,
                                                     max_bits=1024)
                self.assertFalse(complete)
                self.assertEqual(terms, xr.continued_fraction(
                    value, 12)[:len(terms)])

    def test_a_written_rational_is_expanded_exactly(self):
        got = toolbox.run_tool("tool continued fraction 415/93")
        self.assertTrue(got.ok)
        self.assertEqual(got.figures["terms"],
                         list(xr.continued_fraction(Fraction(415, 93), 10)))


class TestTheToolBattery(unittest.TestCase):
    """W8, tool half: every declared tool question as declared."""

    def test_cases(self):
        for question, ok, fragment in c2.TOOL_CASES:
            with self.subTest(question=question):
                got = toolbox.run_tool(question)
                self.assertEqual(got.ok, ok, got.text)
                self.assertIn(fragment, got.text)

    def test_the_catalogue_lists_the_new_tools(self):
        text = toolbox.run_tool("tools").text
        for name in ("continued fraction", "mobius", "bind", "gates",
                     "tag length", "wiring"):
            self.assertIn(f"tool {name}", text)


class TestTheOpenings(unittest.TestCase):
    """W6 and W7: the openings change no declared verdict, and read the
    declared English."""

    def test_no_declared_text_matches_an_opening(self):
        sets = router._declared_sets()
        for texts in sets.values():
            for text in texts:
                self.assertIsNone(toolbox.phrase_tool(text), text)

    def test_openings(self):
        self.assertEqual(toolbox.phrase_tool("What is the continued fraction "
                                             "of pi?"),
                         "tool continued fraction pi")
        self.assertEqual(toolbox.phrase_tool("the first 7 terms of the "
                                             "continued fraction of e"),
                         "tool continued fraction e terms 7")
        self.assertEqual(toolbox.phrase_tool("can 0x7 reach 0x3"),
                         "tool gates 0x7 to 0x3")
        self.assertIsNone(toolbox.phrase_tool("describe energy"))

    def test_the_phrased_battery_through_the_router(self):
        from glm_universal.runtime.session import GeometricSession
        session = GeometricSession()
        for question, expect in c2.PHRASED:
            with self.subTest(question=question):
                r = router.route(session, question)
                if expect == "refuse":
                    self.assertFalse(r.answered, r.text)
                else:
                    self.assertTrue(r.answered, r.text)
                    self.assertEqual(r.surface, "toolbox")
                    self.assertIn(expect, r.text)


class TestTheStudy(unittest.TestCase):

    def test_the_study_exists_and_names_its_marks(self):
        text = STUDY.read_text(encoding="utf-8")
        for mark in ("W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"):
            self.assertIn(mark, text)


if __name__ == "__main__":
    unittest.main()
