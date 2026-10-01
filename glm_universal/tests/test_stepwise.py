"""The stepwise planner (Phase 72): the typed planner as the executive of a
chain of steps, against the marks declared in
``studies/STEPWISE_PLANNER_STUDY.md`` before the module existed.

The column-3 census over every answered chain (mark S5) is exhaustive: it
starts one fresh interpreter per chain and mutation.  A sample of three
chains runs by default.
"""

from __future__ import annotations

import io
import unittest
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.evaluation import stepwise_cases as C
from glm_universal.reasoning import stepwise_script as ss
from glm_universal.runtime import router, stepwise as sw, toolbox
from glm_universal.runtime.python_tct import run_column3
from glm_universal.runtime.session import GeometricSession
from glm_universal.runtime.tct_engine import package_root

ROOT = Path(__file__).resolve().parents[3]

_SESSION = None


def session():
    global _SESSION
    if _SESSION is None:
        _SESSION = GeometricSession()
    return _SESSION


def verdict(a):
    return sw._verdict_of(a)


class TestComposition(unittest.TestCase):
    """S1: every composition case as declared, 0 wrong."""

    def test_every_declared_composition_case(self):
        for cid, q, want in C.COMPOSITION_CASES:
            with self.subTest(case=cid):
                got = verdict(sw.answer(session(), q))
                self.assertEqual(want, got[:len(want)])

    def test_the_bare_planner_answers_none_of_them(self):
        from glm_universal.runtime import semantic_plan as sp
        answered = [cid for cid, q, _ in C.COMPOSITION_CASES
                    if sp.ask_planned(session(), q).ok]
        self.assertLessEqual(len(answered), 2, answered)

    def test_a_sum_of_three_is_answered_although_it_has_two_readings(self):
        a = sw.answer(session(), C.COMPOSITION_CASES[11][1])
        self.assertEqual(2, len(a.readings))
        self.assertEqual({"40"}, {v for _, v in a.readings})

    def test_disagreeing_readings_are_named_in_the_refusal(self):
        a = sw.answer(session(), C.COMPOSITION_CASES[10][1])
        self.assertEqual("ambiguous", a.verdict)
        self.assertIn("-> 28", a.reason)
        self.assertIn("-> 20", a.reason)

    def test_a_single_question_is_not_read(self):
        self.assertEqual("unread", sw.answer(
            session(), "what is the atomic number of iron").verdict)

    def test_it_with_nothing_before_it_is_not_read(self):
        self.assertEqual("unread", sw.answer(session(),
                                             "is it prime").verdict)

    def test_every_step_passes_the_gate(self):
        a = sw.answer(session(), "what is the atomic number of copper, then "
                                 "multiply it by 3, then is it prime")
        ok, notes = ss.chain_check(a.chain)
        self.assertTrue(ok, notes)
        self.assertEqual(["lookup", "literal", "mul", "prime"],
                         [s.op for s in a.chain.steps])


class TestGoals(unittest.TestCase):
    """S2 and S3: goals over the wheels, stitching, and the veto."""

    def test_every_declared_goal_case(self):
        for cid, q, want, stitch in C.GOAL_CASES:
            with self.subTest(case=cid):
                a = sw.answer(session(), q)
                self.assertEqual(want, verdict(a)[:len(want)])
                if a.answered:
                    self.assertEqual(stitch, sw.stitched_of(a))

    def test_the_veto_matters(self):
        r = sw.controls_report(session())
        self.assertGreaterEqual(r["first_found_answers_refused"], 3)
        self.assertGreaterEqual(r["naive_answers_ambiguous"], 1)

    def test_a_cross_wheel_goal_names_both_wheels(self):
        a = sw.answer(session(), "given pressure = 5, area = 2 and velocity "
                                 "= 3, what is the power")
        wheels = [s.detail["wheel"] for s in a.chain.steps
                  if s.op == "axiom"]
        self.assertEqual(["W6", "W5"], wheels)

    def test_an_inconsistent_given_is_named_with_its_derivation(self):
        a = sw.answer(session(), C.GOAL_CASES[9][1])
        self.assertEqual("INCONSISTENT_GIVENS", a.refusal)
        self.assertIn("voltage = current * resistance", a.reason)


class TestNarratives(unittest.TestCase):
    """S4: deferral, reordering and stitching in an asked order."""

    def test_every_declared_narrative(self):
        r = sw.narratives_report(session())
        for row in r["rows"]:
            with self.subTest(case=row["id"]):
                self.assertTrue(row["ok"], row)

    def test_a_deferred_step_is_marked(self):
        a = sw.answer(session(), C.NARRATIVE_CASES[0][1])
        origins = {s.label: s.origin for s in a.chain.steps}
        self.assertEqual("moved earlier", origins["current"])
        self.assertEqual("deferred", origins["power"])


class TestFollowUps(unittest.TestCase):
    """S7: then-turns and why, under the exact key."""

    def test_every_declared_follow_up(self):
        r = sw.follow_ups_report(session())
        for row in r["rows"]:
            with self.subTest(case=row["id"]):
                self.assertTrue(row["ok"], row)

    def test_the_key_is_the_whole_conversation(self):
        conv = sw.StepwiseConversation(session())
        conv.ask("what is the atomic number of iron times 2")
        self.assertIsNotNone(conv.last())
        conv.turns.append("something else")
        self.assertIsNone(conv.last())


class TestScripts(unittest.TestCase):
    """S5 on a sample; the census is exhaustive."""

    SAMPLE = ("is the atomic number of iron prime",
              "given voltage = 12 and resistance = 4, what is the power",
              "convert 3 miles to metres, then divide it by 1000")

    def test_the_sample_verifies_and_every_mutation_is_caught(self):
        root = str(package_root())
        for q in self.SAMPLE:
            chain = sw.answer(session(), q).chain
            got = run_column3(ss.render_script(chain, root))
            self.assertTrue(got["verified"], got)
            self.assertIn(f"ALIGNED {len(chain.steps)} of "
                          f"{len(chain.steps)}", got["stdout"])
            for kind, data in ss.mutants(chain).items():
                with self.subTest(question=q, mutation=kind):
                    bad = run_column3(ss.render_script(chain, root, data))
                    self.assertFalse(bad["verified"])

    def test_the_readers_invert_the_templates(self):
        a = sw.answer(session(), "what is the gcd of the atomic number of "
                                 "iron and the atomic number of oxygen")
        for s in a.chain.steps:
            want = (s.index, s.op, s.inputs, ss.render_value(s.value))
            self.assertEqual(want, ss.read_sentence(ss.sentence(s)))
            self.assertEqual(want, ss.read_equation(
                ss.equation(s, a.chain.steps)))

    @pytest.mark.exhaustive
    def test_every_answered_chain_verifies(self):
        r = sw.scripts_report(session())
        self.assertEqual([], r["failed"])
        self.assertEqual(r["steps"], r["aligned"])
        self.assertEqual([], r["escaped"])
        for kind in ss.MUTATION_KINDS[:4]:
            self.assertEqual(r["chains"], r["mutants"][kind])


class TestWiring(unittest.TestCase):
    """S6 and the router: consulted only on a planner refusal."""

    def test_the_router_hands_a_refusal_to_the_stepwise_planner(self):
        r = router.route(session(), "is the atomic number of iron prime")
        self.assertEqual("planner", r.surface)
        self.assertTrue(r.answered)
        self.assertEqual("not prime", r.text)
        self.assertEqual("stepwise", r.solution.kind)

    def test_an_answered_question_is_untouched(self):
        r = router.route(session(), "what is the atomic number of iron")
        self.assertNotEqual("stepwise", r.solution.kind)

    def test_no_declared_refusal_becomes_an_answer(self):
        r = sw.interference_report(session())
        self.assertEqual([], r["turned_into_answers"])

    def test_the_command_line(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_glm_cli", package_root() / "GLM.py")
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        out = io.StringIO()
        code = cli.main(["--steps", "is the atomic number of nitrogen prime"],
                        out=out)
        self.assertEqual(0, code)
        self.assertIn("ANSWER  prime", out.getvalue())

    def test_the_lean_file_and_the_surface(self):
        lean = ROOT / "overlay/glm_lean/RequestProject/GLM/StepwisePlanner.lean"
        self.assertTrue(lean.exists())
        text = lean.read_text(encoding="utf-8")
        for name in ("eval_eq_model", "disagreement_refutes_model",
                     "rederived_given_refutes_model", "sum_bracketings_agree",
                     "agreed_perm", "checked_iff_recomputed",
                     "fallback_conservative"):
            self.assertIn(f"theorem {name}", text)
        self.assertNotIn("sorry", text)
        planner = next(s for s in toolbox.SURFACES if s.name == "planner")
        self.assertIn("RequestProject/GLM/StepwisePlanner.lean", planner.lean)


if __name__ == "__main__":
    unittest.main()
