"""Tests for the connected machine (Phase 66): the router
(:mod:`glm_universal.runtime.router`), the toolbox
(:mod:`glm_universal.runtime.toolbox`) and derivation across a declared union
of formula wheels (:mod:`glm_universal.engineering.union`), held to the marks
``studies/CONNECTED_MACHINE_STUDY.md`` declared before any of them existed."""

from __future__ import annotations

import io
import re
import unittest
from pathlib import Path

import pytest

from glm_universal.engineering import speak as es
from glm_universal.engineering import union as un
from glm_universal.evaluation import connected_cases as cc
from glm_universal.runtime import router, toolbox

ROOT = Path(__file__).resolve().parents[3]
LEAN = ROOT / "overlay" / "glm_lean" / "RequestProject" / "GLM" / "ConnectedMachine.lean"
STUDY = ROOT / "studies" / "CONNECTED_MACHINE_STUDY.md"


class TestTheRouterReadsOnlyWhatItShould(unittest.TestCase):
    """C1 and the routing half of C2, by the non-interference rule."""

    @classmethod
    def setUpClass(cls):
        cls.census = router.reads_census()

    def test_no_contract_case_is_diverted(self):
        c = self.census["contract"]
        self.assertEqual(c["planner"], sum(c.values()))
        self.assertEqual(c["planner"], 177)

    def test_every_engineering_question_reaches_engineering(self):
        self.assertEqual(self.census["engineering"]["engineering"], 63)
        self.assertEqual(sum(self.census["engineering"].values()), 63)

    def test_every_cognition_question_reaches_the_planner(self):
        self.assertEqual(self.census["cognition"]["planner"], 33)
        self.assertEqual(sum(self.census["cognition"].values()), 33)

    def test_every_python_program_reaches_python(self):
        self.assertEqual(self.census["python"]["python"], 109)
        self.assertEqual(sum(self.census["python"].values()), 109)

    def test_the_declared_mixed_texts(self):
        for text, surface in cc.ROUTED_MIXED:
            with self.subTest(text=text):
                self.assertEqual(router.reader_of(text), surface)

    def test_english_that_parses_as_python_is_not_python(self):
        for text in ("what is energy", "what is 2 + 2", "golay",
                     "x is y", "not golay"):
            with self.subTest(text=text):
                self.assertFalse(router.python_reads(text))

    def test_bound_names_make_a_program(self):
        self.assertTrue(router.python_reads("x = 3\nx * x"))
        self.assertTrue(router.python_reads("def f(a):\n    return a\nf(2)"))
        self.assertTrue(router.python_reads("import random\nrandom.randint(1, 6)"))
        self.assertFalse(router.python_reads("y * 2"))

    def test_the_order_is_the_catalogues(self):
        self.assertEqual(router.ORDER, ("toolbox", "reverse", "python",
                                        "frames", "engineering", "planner"))


class TestPythonThroughTheRouter(unittest.TestCase):
    """C2, Python half: the same verdicts as ``--python``."""

    def test_values_and_refusals(self):
        got = router.python_through_router()
        self.assertEqual(got["values_ok"], got["values"])
        self.assertEqual(got["refusals_ok"], got["refusals"])
        #  26 until Phase 94, which answers two of them
        #  (``SUPERSEDED_BY_PHASE94``); the census above still reads all 26.
        self.assertEqual((got["values"], got["refusals"]), (83, 24))


class TestEngineeringThroughTheRouter(unittest.TestCase):
    """C2, engineering half: the same verdicts as ``--eng``."""

    def test_scores(self):
        from glm_universal.runtime.session import GeometricSession
        got = router.engineering_through_router(GeometricSession())
        self.assertEqual(got, {"correct": 53, "wrong": 0, "refused": 0,
                               "correct-refusal": 10})


class TestTheToolbox(unittest.TestCase):
    """C4: the eight modules the wiring audit found unreached."""

    def test_one_tool_per_module(self):
        # The eight modules of Phase 66, the native-parity instrument added
        # by Phase 70, the native-words reader added by Phase 71 and the law
        # register added by Phase 74.
        modules = {t.module.split(".")[-1] for t in toolbox.TOOLS}
        self.assertEqual(modules, {"deep_dive", "llvq", "moonshine", "pcgs",
                                   "salvage", "salvage_second", "stability",
                                   "tie_break", "native_parity",
                                   "native_words", "law_register"})

    def test_every_tool_names_a_lean_file_and_a_study_that_exist(self):
        for t in toolbox.TOOLS:
            with self.subTest(tool=t.name):
                self.assertTrue((ROOT / t.study).exists(), t.study)
                for f in t.lean:
                    self.assertTrue((ROOT / "overlay" / "glm_lean" / f).exists(), f)
        for s in toolbox.SURFACES:
            with self.subTest(surface=s.name):
                self.assertTrue((ROOT / s.study).exists(), s.study)
                for f in s.lean:
                    self.assertTrue((ROOT / "overlay" / "glm_lean" / f).exists(), f)

    def test_the_cheap_tools_answer_with_their_fragment(self):
        for question, fragment in cc.TOOL_QUESTIONS[:6]:
            with self.subTest(question=question):
                got = toolbox.run_tool(question)
                self.assertTrue(got.ok, got.text)
                self.assertIn(fragment, got.text)

    def test_the_per_declaration_tools(self):
        for question, fragment in cc.TOOL_QUESTIONS[6:]:
            with self.subTest(question=question):
                got = toolbox.run_tool(question)
                self.assertTrue(got.ok, got.text)
                self.assertIn(fragment, got.text)

    def test_refusals_are_named(self):
        self.assertFalse(toolbox.run_tool("tool nonsense").ok)
        self.assertFalse(toolbox.run_tool("tool stability").ok)
        self.assertFalse(toolbox.run_tool("tool tie break No.Such.Name").ok)

    def test_the_catalogue_lists_every_surface_and_tool(self):
        text = toolbox.run_tool("tools").text
        for s in toolbox.SURFACES:
            self.assertIn(s.name, text)
        for t in toolbox.TOOLS:
            self.assertIn(f"tool {t.name}", text)


class TestTheUnionOfWheels(unittest.TestCase):
    """U2-U3 on the declared questions, and the declared junction table."""

    def test_the_junction_table_is_the_declared_one(self):
        self.assertEqual(un.JUNCTIONS, cc.JUNCTIONS_DECLARED)

    def test_every_declared_union_question(self):
        for key, question, expected in cc.UNION_QUESTIONS:
            with self.subTest(key=key):
                verdict, got, reason = es.answer(question)
                if expected == "refuse":
                    self.assertEqual(verdict, "refused", got and got.text)
                else:
                    self.assertEqual(verdict, "answered", reason)
                    self.assertEqual(got.values["formula"], expected)
                    self.assertEqual(got.frame, "union")

    def test_in_wheel_derive_is_unchanged(self):
        verdict, _, _ = es.answer("derive power from pressure and volume "
                                  "flow rate")
        self.assertEqual(verdict, "refused")

    def test_a_refusal_names_the_naive_answer_it_declines(self):
        got = un.derive_across("energy", "mass", "speed_of_light")
        self.assertFalse(got.answered)
        self.assertEqual(got.naive, "2 * mass * speed_of_light^2")
        self.assertIn("photon", got.reason)

    def test_hydraulic_power_names_the_junction(self):
        got = un.derive_across("power", "pressure", "volume_flow_rate")
        self.assertEqual(got.wheels, ("W5", "W6"))
        self.assertIn("force (W5=W6)", got.junctions)

    def test_splitting_only_adds_names(self):
        split, naive = un.split_system(True), un.split_system(False)
        self.assertEqual(len(split.relations), len(naive.relations))
        self.assertGreater(len(split.labels), len(naive.labels))
        self.assertEqual({un.base_name(l) for l in split.labels},
                         set(naive.labels))

    @pytest.mark.exhaustive
    def test_the_census(self):
        got = un.union_census(cc.UNION_LABELS)
        self.assertEqual((got["naive_new"], got["naive_right"],
                          got["naive_wrong"]), (161, 3, 158))
        self.assertEqual((got["licensed_answered"], got["licensed_right"],
                          got["licensed_wrong"]), (3, 3, 0))
        self.assertEqual(got["in_wheel_agree"], got["in_wheel"])


class TestTheCommandLine(unittest.TestCase):

    def _run(self, *args):
        import GLM as cli
        out = io.StringIO()
        code = cli.main(list(args), out=out)
        return code, out.getvalue()

    def test_ask_names_the_surface(self):
        code, text = self._run("-c", "1", "--ask", "tool moonshine", "--ask",
                               "Fraction(1, 3) + Fraction(1, 6)", "--ask",
                               "derive power from pressure and volume flow "
                               "rate across wheels")
        self.assertEqual(code, 0, text)
        self.assertIn("SURFACE toolbox", text)
        self.assertIn("SURFACE python", text)
        self.assertIn("SURFACE engineering", text)
        self.assertIn("pressure * volume_flow_rate", text)

    def test_a_refusal_exits_one(self):
        code, text = self._run("--ask", "derive energy from mass and speed "
                               "of light across wheels")
        self.assertEqual(code, 1)
        self.assertIn("REFUSED", text)


class TestTheSpecification(unittest.TestCase):
    """D8: the Lean file states what the module relies on."""

    def test_the_cited_theorems_exist(self):
        text = LEAN.read_text(encoding="utf-8")
        for name in ("route_cons_none", "route_prefix_none",
                     "route_append_of_some", "route_total", "derivable_mono",
                     "licensed_sound", "not_derivable_of_functional",
                     "emc2_naive", "emc2_refused_split",
                     "emc2_refused_split_photon", "hydraulic_licensed"):
            with self.subTest(name=name):
                self.assertRegex(text, rf"theorem {name}\b")
        self.assertNotIn("sorry", text)

    def test_the_study_exists(self):
        self.assertTrue(STUDY.exists())
