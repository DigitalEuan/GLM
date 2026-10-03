"""The stepwise planner, round three (Phase 84): declared comparatives,
further count nouns, the tera- and pico- prefixes, and folds over a column,
against the marks declared in ``studies/STEPWISE_THREE_STUDY.md`` before any
code.

The column-3 census over every answered chain (mark V6) and the
non-interference census (mark V7) are exhaustive; a sample runs by default.
"""

from __future__ import annotations

import io
import unittest
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.runtime.frame_declarations import declared_verdict

from glm_universal.evaluation import stepwise_three_cases as C
from glm_universal.reasoning import stepwise_script as ss
from glm_universal.runtime import declared_frames as df
from glm_universal.runtime import quantity_units as qu
from glm_universal.runtime import router, stepwise as sw
from glm_universal.runtime import stepwise_three as st
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


def case(cases, cid):
    return next(c for c in cases if c[0] == cid)


class TestComparatives(unittest.TestCase):
    """V1: every comparative case as declared; round two answers none."""

    def test_every_declared_comparative_case(self):
        for cid, q, want in C.COMPARATIVE_CASES:
            with self.subTest(case=cid):
                got = verdict(sw.answer(session(), q))
                self.assertEqual(want, got[:len(want)])

    def test_round_two_answers_none_of_them(self):
        with st.round_two_reader():
            answered = [cid for cid, q, _ in C.COMPARATIVE_CASES
                        if sw.answer(session(), q).answered]
        self.assertEqual([], answered)

    def test_the_answer_is_the_row_as_named(self):
        a = sw.answer(session(), case(C.COMPARATIVE_CASES, "c01")[1])
        last = a.chain.steps[-1]
        self.assertEqual(("comparative", "copper"), (last.op, last.value))
        self.assertEqual(["iron", "copper"], last.detail["rows"])
        self.assertEqual(("lookup", "lookup"),
                         tuple(a.chain.steps[j - 1].op for j in last.inputs))

    def test_older_is_the_earlier_year(self):
        self.assertEqual(("year discovered", "<"),
                         df.COMPARATIVES["older"][:2])

    def test_an_undeclared_comparative_is_named(self):
        a = sw.answer(session(), case(C.COMPARATIVE_CASES, "c10")[1])
        self.assertIn("stronger", a.reason)

    def test_a_missing_value_is_named(self):
        a = sw.answer(session(), case(C.COMPARATIVE_CASES, "c09")[1])
        self.assertEqual("VALUE_MISSING", a.refusal)
        self.assertIn("year", a.reason)


class TestCounts(unittest.TestCase):
    """V2: the further count nouns."""

    def test_every_declared_count_case(self):
        for cid, q, want in C.COUNT_CASES:
            with self.subTest(case=cid):
                got = verdict(sw.answer(session(), q))
                self.assertEqual(want, got[:len(want)])

    def test_neutrons_stay_undeclared(self):
        self.assertNotIn("neutrons", df.COUNT_NOUNS)
        self.assertEqual({"electrons": "atomic number",
                          "valence electrons": "valence electrons"},
                         df.COUNT_NOUNS)


class TestPrefixes(unittest.TestCase):
    """V3: tera and pico."""

    def test_every_declared_prefix_case(self):
        for cid, q, want, stitch in C.PREFIX_CASES:
            moved = declared_verdict("stepwise_three", cid, want) != want
            want = declared_verdict("stepwise_three", cid, want)
            with self.subTest(case=cid):
                a = sw.answer(session(), q)
                self.assertEqual(want, verdict(a)[:len(want)])
                if a.answered and not moved:
                    self.assertEqual(stitch, sw.stitched_of(a))

    def test_the_prefixes_are_exact_and_switchable(self):
        self.assertEqual(Fraction(10 ** 12), qu.read_unit("terahertz").factor)
        self.assertEqual(Fraction(1, 10 ** 12),
                         qu.read_unit("picometres").factor)
        with st.round_two_reader():
            with self.assertRaises(qu.UnitRefused):
                qu.read_unit("terahertz")
        self.assertTrue(qu.WIDEN)


class TestFolds(unittest.TestCase):
    """V4: folds over a column."""

    def test_every_declared_fold_case(self):
        for cid, q, want in C.FOLD_CASES:
            want = declared_verdict("stepwise_three", cid, want)
            with self.subTest(case=cid):
                got = verdict(sw.answer(session(), q))
                self.assertEqual(want, got[:len(want)])

    def test_a_fold_is_one_step_over_one_lookup_per_member(self):
        a = sw.answer(session(), case(C.FOLD_CASES, "f02")[1])
        last = a.chain.steps[-1]
        self.assertEqual("fold", last.op)
        rows = [a.chain.steps[j - 1].detail["row"] for j in last.inputs]
        self.assertEqual(["F", "Cl", "Br", "I", "At", "Ts"], rows)

    def test_a_hole_names_the_missing_rows(self):
        a = sw.answer(session(), case(C.FOLD_CASES, "f06")[1])
        self.assertEqual("COLUMN_HOLE", a.refusal)
        for row in ("He", "Ne", "Ar", "Rn", "Og"):
            self.assertIn(row, a.reason)

    def test_the_sets_are_the_registers_classes(self):
        self.assertIsNone(df.DECLARED_SETS["elements"])
        self.assertEqual("Noble gas", df.DECLARED_SETS["noble gases"])
        self.assertNotIn("metals", df.DECLARED_SETS)


class TestControls(unittest.TestCase):
    """V5: the present-rows control, and the partition of the column."""

    def test_present_rows_answers_the_holes(self):
        r = st.controls_report(session())
        self.assertGreaterEqual(len(r["present_rows_answers"]),
                                C.HOLE_CONTROL_AT_LEAST)
        self.assertTrue(r["partition"]["met"], r["partition"])
        self.assertTrue(r["met"])


class TestFollowUps(unittest.TestCase):

    def test_follow_ups(self):
        r = st.follow_ups_report(session())
        self.assertEqual(r["cases"], r["met"], r["rows"])


class TestScripts(unittest.TestCase):
    """V6: every answered chain's script, and every mutation of it."""

    SAMPLE = (("c01", C.COMPARATIVE_CASES), ("c04", C.COMPARATIVE_CASES),
              ("f01", C.FOLD_CASES), ("p01", C.PREFIX_CASES))

    def test_a_sample_of_chains_verifies_and_rejects_its_mutations(self):
        root = str(package_root())
        for cid, cases in self.SAMPLE:
            chain = sw.answer(session(), case(cases, cid)[1]).chain
            got = run_column3(ss.render_script(chain, root))
            self.assertTrue(got["verified"], got["stdout"])
            for kind, data in ss.mutants(chain).items():
                with self.subTest(case=cid, mutation=kind):
                    bad = run_column3(ss.render_script(chain, root, data))
                    self.assertFalse(bad["verified"])

    def test_the_new_mutations_apply(self):
        fold = sw.answer(session(), case(C.FOLD_CASES, "f01")[1]).chain
        comp = sw.answer(session(), case(C.COMPARATIVE_CASES, "c01")[1]).chain
        self.assertIn("member-lie", ss.mutants(fold))
        self.assertIn("word-lie", ss.mutants(comp))

    def test_the_readers_invert_the_new_templates(self):
        for cid, cases in self.SAMPLE:
            a = sw.answer(session(), case(cases, cid)[1])
            for s in a.chain.steps:
                want = (s.index, s.op, s.inputs, ss.render_value(s.value))
                self.assertEqual(want, ss.read_sentence(ss.sentence(s)))
                self.assertEqual(want, ss.read_equation(
                    ss.equation(s, a.chain.steps)))

    @pytest.mark.exhaustive
    def test_every_answered_chain_verifies(self):
        r = st.scripts_report(session())
        self.assertEqual([], r["failed"])
        self.assertEqual(r["steps"], r["aligned"])
        self.assertEqual([], r["escaped"])
        self.assertGreater(r["mutants"]["member-lie"], 0)
        self.assertGreater(r["mutants"]["word-lie"], 0)


class TestWiring(unittest.TestCase):
    """V7 and the router."""

    def test_the_router_hands_the_new_frames_to_the_stepwise_planner(self):
        r = router.route(session(), "which is older, oxygen or hydrogen")
        self.assertTrue(r.answered)
        self.assertEqual("hydrogen", r.text)
        self.assertEqual("stepwise", r.solution.kind)

    @pytest.mark.exhaustive
    def test_non_interference(self):
        r = st.interference_report(session())
        self.assertTrue(r["round_one_held"], r)
        self.assertTrue(r["round_two_held"], r)
        self.assertEqual([], r["turned_into_answers"])
        self.assertEqual([], r["declared_refusals_answered"])

    def test_the_command_line(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_glm_cli", package_root() / "GLM.py")
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        out = io.StringIO()
        code = cli.main(["--steps", "what is the sum of the atomic numbers "
                                    "of the halogens"], out=out)
        self.assertEqual(0, code)
        self.assertIn("ANSWER  316", out.getvalue())

    def test_the_lean_file_and_the_surface(self):
        lean = ROOT / "overlay/glm_lean/RequestProject/GLM/StepwiseWiden.lean"
        self.assertTrue(lean.exists())
        text = lean.read_text(encoding="utf-8")
        for name in ("winner_swap", "winner_flip_ne", "winner_eq_none_iff",
                     "fold_sum_partition", "even_sum_iff_even_odd_count",
                     "odd_count_add_even_count", "mean_cons_eq_iff",
                     "hole_mean_injective"):
            self.assertIn(f"theorem {name}", text)
        self.assertNotIn("sorry", text)
        planner = next(s for s in toolbox.SURFACES if s.name == "planner")
        self.assertIn("RequestProject/GLM/StepwiseWiden.lean", planner.lean)


if __name__ == "__main__":
    unittest.main()
