"""The loop through the planner -- ``derive``, ``ask`` and ``solve`` as
dialect values, questions about a Python expression through a frame, and the
column-3 script that re-runs every sub-answer's own script, pinned.

``glm_universal.runtime.planner_bridge`` is the bridge
(``studies/PLANNER_LOOP_STUDY.md``, Phase 88);
``glm_universal.runtime.planner_loop_report`` measures the declared corpus of
``glm_universal.evaluation.planner_loop_cases``.  The facts the round rests
on are theorems of ``RequestProject/GLM/PlannerLoop.lean`` (W8).  Exact.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.evaluation import planner_loop_cases as C
from glm_universal.reasoning import python_speech as sp
from glm_universal.reasoning import python_substrate as ps
from glm_universal.runtime import planner_loop_report as lr
from glm_universal.runtime import router
from glm_universal.runtime.planner_bridge import PlannerBridge, frame_of
from glm_universal.runtime.session import GeometricSession

_STATE = []


def state():
    if not _STATE:
        s = GeometricSession()
        _STATE.append((s, PlannerBridge(s)))
    return _STATE[0]


class TestTheDeclarations(unittest.TestCase):

    def test_new_refusals_are_dialect_refusals(self):
        for name in C.NEW_REFUSAL_NAMES:
            self.assertIn(name, ps.REFUSAL_NAMES)

    def test_the_builtins_are_declared_on_both_sides(self):
        ns = {}
        exec(ps.PRELUDE, ns)
        for name in ("derive", "ask", "solve"):
            self.assertIn(name, sp.BUILTINS)
            self.assertIn(name, ns["PRELUDE_NAMES"])

    def test_the_question_is_built_alike_on_both_sides(self):
        ns = {}
        exec(ps.PRELUDE, ns)
        q = ns["derive_question"]("power", (("voltage", 12),
                                            ("resistance", Fraction(3, 2))))
        self.assertEqual(q, "given voltage = 12 and resistance = 3/2, what "
                            "is the power")
        self.assertEqual(ns["solve_question"]("t", "p * t == 1",
                                              (("p", Fraction(-1, 2)),)),
                         "solve for t: (-1/2) * t == 1")

    def test_the_dialect_alone_refuses_by_name(self):
        p = sp.speak('derive("power", ("voltage", 12), ("resistance", 4))')
        self.assertEqual(p.refusal, "BRIDGE_UNAVAILABLE")


class TestThePrograms(unittest.TestCase):

    def _group(self, cases):
        s, b = state()
        got = lr.program_rows(s, cases, b)
        self.assertEqual(got["met"], got["cases"],
                         [r for r in got["rows"] if not r["ok"]])
        self.assertEqual(got["wrong"], 0)
        self.assertEqual(got["bridge_off_answers"], 0)
        self.assertEqual(got["machine_answered_before"], 0)
        self.assertEqual(got["machine_answers_now"], got["answered"])

    def test_w1_derive(self):
        self._group(C.DERIVE_CASES)

    def test_w2_ask(self):
        self._group(C.ASK_CASES)

    def test_w2_solve(self):
        self._group(C.SOLVE_CASES)

    def test_w3_loops(self):
        self._group(C.LOOP_CASES)

    def test_a_loop_asks_each_question_once(self):
        s, b = state()
        p = sp.speak(dict((c[0], c[1]) for c in C.LOOP_CASES)["l02"],
                     bridge=b)
        self.assertEqual(p.value, 13)
        self.assertEqual(len(p.bridge), 13)
        self.assertEqual(len({r["question"] for r in p.bridge}), 13)


class TestTheFrames(unittest.TestCase):

    def test_w4_frames(self):
        s, _b = state()
        got = lr.frames_report(s)
        self.assertEqual(got["met"], got["cases"],
                         [r for r in got["rows"] if not r["ok"]])

    def test_a_frame_needs_dialect_text(self):
        self.assertIsNone(frame_of("what does `the atomic number of iron` "
                                   "return?"))
        self.assertEqual(frame_of("evaluate `1 + 1`"), ("value", "1 + 1"))

    def test_w4_census(self):
        got = lr.census_report()
        self.assertTrue(got["met"], got["moved"][:5])

    def test_switches_are_restored(self):
        with lr.switched(BRIDGE=False, FRAMES=False):
            self.assertFalse(router.BRIDGE)
        self.assertTrue(router.BRIDGE and router.FRAMES)


class TestTheScripts(unittest.TestCase):

    def test_w5_scripts_sample(self):
        s, b = state()
        got = lr.scripts_report(s, b, limit=3)
        self.assertEqual(got["verified"], got["programs"], got["failed"])
        self.assertEqual(got["escaped"], [])
        self.assertEqual(got["caught_at_check"]["bridge-lie"], [3])
        self.assertEqual(got["caught_at_check"]["chain-lie"], [2])


class TestTheUtilityGateReading(unittest.TestCase):

    def test_the_router_answers_no_paraphrase(self):
        s, _b = state()
        self.assertEqual(lr.paraphrase_report(s)["answered"], 0)


class TestTheLeanFile(unittest.TestCase):

    def test_w8_lean_file_has_no_sorry(self):
        root = Path(__file__).resolve().parents[2]
        path = root / "glm_lean" / "RequestProject" / "GLM" / \
            "PlannerLoop.lean"
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in ("run_eq_of_agree", "run_restrict",
                     "isSome_of_run_eq_some", "run_eq_none_of_refused",
                     "affine_root_unique", "affine_slope_ne_zero",
                     "least_resistance_thirteen"):
            self.assertIn(name, text)


if __name__ == "__main__":
    unittest.main()
