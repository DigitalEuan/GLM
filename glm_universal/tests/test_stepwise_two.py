"""The stepwise planner, round two (Phase 73): *how many more*, parity,
averages, givens with units, and register values fed to the wheels, against
the marks declared in ``studies/STEPWISE_TWO_STUDY.md`` before any code.

The column-3 census over every answered chain (mark T5) is exhaustive: it
starts one fresh interpreter per chain and mutation.  A sample runs by
default.
"""

from __future__ import annotations

import io
import unittest
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.evaluation import stepwise_two_cases as C
from glm_universal.reasoning import stepwise_script as ss
from glm_universal.runtime import quantity_units as qu
from glm_universal.runtime import router, stepwise as sw, stepwise_two as st
from glm_universal.runtime import toolbox
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


class TestFrames(unittest.TestCase):
    """T1: every frame case as declared, 0 wrong; round one answers none."""

    def test_every_declared_frame_case(self):
        for cid, q, want in C.FRAME_CASES:
            with self.subTest(case=cid):
                got = verdict(sw.answer(session(), q))
                self.assertEqual(want, got[:len(want)])

    def test_round_one_answers_none_of_them(self):
        with st.round_one_reader():
            answered = [cid for cid, q, _ in C.FRAME_CASES
                        if sw.answer(session(), q).answered]
        self.assertEqual([], answered)

    def test_a_reversed_difference_names_the_right_order(self):
        a = sw.answer(session(), C.FRAME_CASES[2][1])
        self.assertEqual("DIFFERENCE_REVERSED", a.refusal)
        self.assertIn("20 fewer protons", a.reason)

    def test_the_mean_is_one_step_over_every_item(self):
        a = sw.answer(session(), C.FRAME_CASES[10][1])
        last = a.chain.steps[-1]
        self.assertEqual("mean", last.op)
        self.assertEqual(3, len(last.inputs))
        self.assertEqual(Fraction(7), last.value)

    def test_parity_carries_its_witness(self):
        a = sw.answer(session(), C.FRAME_CASES[6][1])
        self.assertIn("79 = 2 x 39 + 1", ss.equation(a.chain.steps[-1],
                                                     a.chain.steps))

    def test_the_count_nouns_are_declared(self):
        self.assertEqual({"protons": "atomic number"}, C.COUNT_NOUNS)


class TestUnits(unittest.TestCase):
    """T2: givens (and targets) with units; the declared unit table."""

    def test_every_declared_unit_case(self):
        for cid, q, want, stitch in C.UNIT_CASES:
            with self.subTest(case=cid):
                a = sw.answer(session(), q)
                self.assertEqual(want, verdict(a)[:len(want)])
                if a.answered:
                    self.assertEqual(stitch, sw.stitched_of(a))

    def test_the_table_reads_compounds_exactly(self):
        self.assertEqual(Fraction(5, 18),
                         qu.read_unit("kilometres per hour").factor)
        self.assertEqual(Fraction(1000), qu.read_unit("kilohms").factor)
        self.assertEqual(qu.quantity_dimension("torque"),
                         qu.read_unit("newton metres").dimension)
        self.assertEqual(qu.quantity_dimension("acceleration"),
                         qu.read_unit("metres per second squared").dimension)

    def test_dimensions_are_derived_not_stored(self):
        # the volt is read through the register's own definition V = W/A
        self.assertEqual(qu.quantity_dimension("voltage"),
                         qu.read_unit("volts").dimension)

    def test_symbols_are_not_read(self):
        with self.assertRaises(qu.UnitRefused) as e:
            qu.read_unit("mw")
        self.assertEqual("UNKNOWN_UNIT", e.exception.name)

    def test_inexact_and_offset_units_are_named(self):
        for phrase, name in (("revolutions per minute", "UNIT_INEXACT"),
                             ("degrees", "UNIT_INEXACT"),
                             ("degrees celsius", "OFFSET_UNIT"),
                             ("fahrenheit", "OFFSET_UNIT")):
            with self.subTest(phrase=phrase):
                with self.assertRaises(qu.UnitRefused) as e:
                    qu.read_unit(phrase)
                self.assertEqual(name, e.exception.name)

    def test_a_given_with_a_unit_is_two_steps(self):
        a = sw.answer(session(), C.UNIT_CASES[1][1])
        ops = [s.op for s in a.chain.steps]
        self.assertEqual(["measured", "si", "measured", "si", "axiom"], ops)


class TestRegister(unittest.TestCase):
    """T3: register values fed to the wheels."""

    def test_every_declared_register_case(self):
        for cid, q, want, stitch in C.REGISTER_CASES:
            with self.subTest(case=cid):
                a = sw.answer(session(), q)
                self.assertEqual(want, verdict(a)[:len(want)])
                if a.answered:
                    self.assertEqual(stitch, sw.stitched_of(a))

    def test_the_register_entry_is_read_then_converted(self):
        a = sw.answer(session(), C.REGISTER_CASES[3][1])
        lookup, si = a.chain.steps[1], a.chain.steps[2]
        self.assertEqual(("lookup", "si"), (lookup.op, si.op))
        self.assertEqual("element:atomic_radius_pm", si.detail["from"])
        self.assertEqual(Fraction(194, 10 ** 12), si.value)

    def test_scales_carried_into_si(self):
        self.assertEqual(Fraction(1), qu.scale_into_si(
            "element:melting_point_K")[0])
        for scale, name in (("element:atomic_weight_u", "UNIT_INEXACT"),
                            ("element:z", "SCALE_UNDECLARED")):
            with self.subTest(scale=scale):
                with self.assertRaises(qu.UnitRefused) as e:
                    qu.scale_into_si(scale)
                self.assertEqual(name, e.exception.name)


class TestControls(unittest.TestCase):
    """T4: the strip-the-units reading answers wrongly and answers the
    unit refusals."""

    def test_strip_the_units_is_wrong_where_the_table_matters(self):
        r = st.controls_report(session())
        self.assertGreaterEqual(len(r["naive_wrong"]),
                                C.NAIVE_WRONG_AT_LEAST)
        self.assertGreaterEqual(len(r["naive_answers_unit_refusals"]),
                                C.NAIVE_REFUSALS_ANSWERED_AT_LEAST)
        self.assertTrue(r["met"])


class TestNarrativesAndFollowUps(unittest.TestCase):
    """T7."""

    def test_narratives(self):
        r = st.narratives_report(session())
        self.assertEqual(r["cases"], r["met"], r["rows"])

    def test_follow_ups(self):
        r = st.follow_ups_report(session())
        self.assertEqual(r["cases"], r["met"], r["rows"])


class TestScripts(unittest.TestCase):
    """T5: every answered chain's script, and every mutation of it."""

    def test_a_sample_of_chains_verifies_and_rejects_its_mutations(self):
        root = str(package_root())
        for q in (C.UNIT_CASES[2][1], C.REGISTER_CASES[3][1],
                  C.FRAME_CASES[12][1]):
            chain = sw.answer(session(), q).chain
            got = run_column3(ss.render_script(chain, root))
            self.assertTrue(got["verified"], got["stdout"])
            for kind, data in ss.mutants(chain).items():
                with self.subTest(question=q, mutation=kind):
                    bad = run_column3(ss.render_script(chain, root, data))
                    self.assertFalse(bad["verified"])

    def test_the_readers_invert_the_new_templates(self):
        for q in (C.UNIT_CASES[2][1], C.REGISTER_CASES[3][1],
                  C.FRAME_CASES[6][1], C.FRAME_CASES[10][1]):
            a = sw.answer(session(), q)
            for s in a.chain.steps:
                want = (s.index, s.op, s.inputs, ss.render_value(s.value))
                self.assertEqual(want, ss.read_sentence(ss.sentence(s)))
                self.assertEqual(want, ss.read_equation(
                    ss.equation(s, a.chain.steps)))

    def test_a_decimal_given_verifies(self):
        # round one's script re-read '1.5' as '1' and rejected a right chain
        a = sw.answer(session(), "given voltage = 1.5 and current = 3, what "
                                 "is the power")
        got = run_column3(ss.render_script(a.chain, str(package_root())))
        self.assertTrue(got["verified"], got["stdout"])

    @pytest.mark.exhaustive
    def test_every_answered_chain_verifies(self):
        r = st.scripts_report(session())
        self.assertEqual([], r["failed"])
        self.assertEqual(r["steps"], r["aligned"])
        self.assertEqual([], r["escaped"])
        self.assertGreater(r["mutants"]["unit-lie"], 0)


class TestWiring(unittest.TestCase):
    """T6 and the router."""

    def test_the_router_hands_the_new_frames_to_the_stepwise_planner(self):
        r = router.route(session(), "is the atomic number of gold odd")
        self.assertTrue(r.answered)
        self.assertEqual("True", r.text)
        self.assertEqual("stepwise", r.solution.kind)

    def test_round_one_questions_take_round_one_paths(self):
        for _cid, q, *_ in sw_goal_cases():
            with self.subTest(question=q):
                parsed = sw.parse_goal_two(q)
                self.assertTrue(parsed is None or not parsed[3])

    @pytest.mark.exhaustive
    def test_non_interference(self):
        r = st.interference_report(session())
        self.assertTrue(r["round_one_held"], r)
        self.assertEqual([], r["turned_into_answers"])

    def test_the_command_line(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_glm_cli", package_root() / "GLM.py")
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        out = io.StringIO()
        code = cli.main(["--steps", "given voltage = 12 volts and resistance "
                                    "= 4 kilohms, what is the current in "
                                    "milliamperes"], out=out)
        self.assertEqual(0, code)
        self.assertIn("ANSWER  3", out.getvalue())

    def test_the_lean_file_and_the_surface(self):
        lean = ROOT / "overlay/glm_lean/RequestProject/GLM/StepwiseFrames.lean"
        self.assertTrue(lean.exists())
        text = lean.read_text(encoding="utf-8")
        for name in ("mean_perm", "le_mean", "mean_le", "parity_witness",
                     "more_eq_none_iff", "monomial_rescale",
                     "invariant_iff_homogeneous", "offset_not_multiplicative",
                     "offset_changes_product", "veto_unit_free",
                     "register_feed_sound"):
            self.assertIn(f"theorem {name}", text)
        self.assertNotIn("sorry", text)
        planner = next(s for s in toolbox.SURFACES if s.name == "planner")
        self.assertIn("RequestProject/GLM/StepwiseFrames.lean", planner.lean)


def sw_goal_cases():
    from glm_universal.evaluation import stepwise_cases as one
    return one.GOAL_CASES + one.NARRATIVE_CASES


if __name__ == "__main__":
    unittest.main()
