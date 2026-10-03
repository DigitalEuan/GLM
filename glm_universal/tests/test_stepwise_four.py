"""The stepwise planner, round four (Phase 85): folds with a hole -- the
median, the ends and the rank of a column, bounded exactly where the register
is silent, and the present-rows question asked as its own -- against the marks
declared in ``studies/HOLE_FOLDS_STUDY.md`` before any code.

The column-3 census over every answered chain (mark H6) and the
non-interference census (mark H7) are exhaustive; a sample runs by default.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.runtime.frame_declarations import declared_verdict

from glm_universal.evaluation import stepwise_four_cases as C
from glm_universal.reasoning import stepwise_script as ss
from glm_universal.runtime import router, stepwise as sw
from glm_universal.runtime import stepwise_four as s4
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


def fold_step(chain):
    return next(s for s in reversed(chain.steps) if s.op == "fold")


class TestTheRule(unittest.TestCase):
    """The rule of §1 on small columns, against brute force."""

    def test_median_interval_contains_every_completion(self):
        present = [Fraction(v) for v in (1, 2, 3, 5, 7)]
        lo, hi = Fraction(5, 2), Fraction(4)
        self.assertEqual("between 5/2 and 4",
                         ss.fold_value("median", present, 1))
        for fill in range(-5, 12):
            got = s4.completed_value("median", present + [Fraction(fill)])
            self.assertTrue(lo <= got <= hi, fill)

    def test_an_interval_that_closes_is_one_value(self):
        present = [Fraction(v) for v in (2, 2, 2, 2, 9)]
        self.assertEqual(Fraction(2), ss.fold_value("median", present, 2))

    def test_an_open_side_is_none(self):
        present = [Fraction(v) for v in (1, 2)]
        self.assertIsNone(ss.fold_value("median", present, 5))
        self.assertIsNone(ss.fold_value("max", present, 1))
        self.assertIsNone(ss.fold_value("min", present, 1))
        self.assertIsNone(ss.fold_value("mean", present, 1))

    def test_rank_interval(self):
        present = [Fraction(v) for v in (9, 5, 3)]
        self.assertEqual("between 2 and 4",
                         ss.fold_value("rank", present, 2, Fraction(5)))
        self.assertEqual(Fraction(2),
                         ss.fold_value("rank", present, 0, Fraction(5)))


class TestOrders(unittest.TestCase):
    """H1: the order folds; round three answers none."""

    def test_every_declared_order_case(self):
        for cid, q, want in C.ORDER_CASES:
            want = declared_verdict("stepwise_four", cid, want)
            with self.subTest(case=cid):
                got = verdict(sw.answer(session(), q))
                self.assertEqual(want, got[:len(want)])

    def test_round_three_answers_none_of_the_corpus(self):
        with s4.round_three_reader():
            answered = [cid for cid, q, _ in
                        C.ORDER_CASES + C.BOUNDED_CASES + C.RANK_CASES
                        + C.PRESENT_CASES
                        if sw.answer(session(), q).answered]
        self.assertEqual([], answered)

    def test_an_open_end_names_its_side(self):
        a = sw.answer(session(), case(C.ORDER_CASES, "o09")[1])
        self.assertEqual("COLUMN_HOLE", a.refusal)
        self.assertIn("open above", a.reason)
        self.assertIn("Hs", a.reason)


class TestBounded(unittest.TestCase):
    """H2: the median over a column with holes."""

    def test_every_declared_bounded_case(self):
        for cid, q, want in C.BOUNDED_CASES:
            with self.subTest(case=cid):
                got = verdict(sw.answer(session(), q))
                self.assertEqual(want, got[:len(want)])

    def test_a_bounded_fold_records_its_holes(self):
        a = sw.answer(session(), case(C.BOUNDED_CASES, "b01")[1])
        step = fold_step(a.chain)
        self.assertTrue(step.detail["bounded"])
        self.assertEqual(["Ts"], step.detail["missing"])
        self.assertIn("with 1 missing (Ts)", ss.sentence(step))


class TestRanks(unittest.TestCase):
    """H3: the rank of a row."""

    def test_every_declared_rank_case(self):
        for cid, q, want in C.RANK_CASES:
            with self.subTest(case=cid):
                got = verdict(sw.answer(session(), q))
                self.assertEqual(want, got[:len(want)])


class TestPresent(unittest.TestCase):
    """H4: the present-rows question, with the missing rows named."""

    def test_every_declared_present_case(self):
        for cid, q, want in C.PRESENT_CASES:
            with self.subTest(case=cid):
                got = verdict(sw.answer(session(), q))
                self.assertEqual(want, got[:len(want)])

    def test_the_missing_rows_are_named(self):
        r = s4.present_report(session())
        self.assertEqual(len(r["named"]), r["named_ok"], r["named"])
        a = sw.answer(session(), case(C.PRESENT_CASES, "q01")[1])
        line = ss.sentence(fold_step(a.chain))
        self.assertIn("(missing: He, Ne, Ar, Rn, Og)", line)

    def test_another_column_is_not_a_present_filter(self):
        a = sw.answer(session(), "what is the average density of the "
                                 "halogens with a recorded melting point")
        self.assertFalse(a.answered)

    def test_follow_ups(self):
        r = s4.follow_ups_report(session())
        self.assertEqual(r["cases"], r["met"], r["rows"])


class TestCompletions(unittest.TestCase):
    """H5: sound and sharp on the register."""

    def test_completions(self):
        r = s4.completions_report(session(), per_answer=40)
        self.assertTrue(r["met"], r)
        self.assertEqual(9, len(r["bounded"]))
        self.assertEqual(4, len(r["refusals"]))


class TestScripts(unittest.TestCase):
    """H6: every answered chain's script, and every mutation of it."""

    SAMPLE = (("q01", C.PRESENT_CASES), ("b01", C.BOUNDED_CASES),
              ("r03", C.RANK_CASES), ("o01", C.ORDER_CASES))

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

    def test_the_hole_lie_applies(self):
        chain = sw.answer(session(), case(C.PRESENT_CASES, "q01")[1]).chain
        self.assertIn("hole-lie", ss.mutants(chain))

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
        r = s4.scripts_report(session())
        self.assertEqual([], r["failed"])
        self.assertEqual(r["steps"], r["aligned"])
        self.assertEqual([], r["escaped"])
        self.assertGreater(r["mutants"]["hole-lie"], 0)


class TestWiring(unittest.TestCase):
    """H7 and the router."""

    def test_the_router_hands_the_new_frames_to_the_stepwise_planner(self):
        r = router.route(session(), case(C.RANK_CASES, "r02")[1])
        self.assertTrue(r.answered)
        self.assertEqual("3", r.text)
        self.assertEqual("stepwise", r.solution.kind)

    @pytest.mark.exhaustive
    def test_non_interference(self):
        r = s4.interference_report(session())
        self.assertTrue(r["round_three_held"], r)
        self.assertTrue(r["round_two_held"], r)
        self.assertTrue(r["round_one_held"], r)
        self.assertEqual([], r["turned_into_answers"])
        self.assertEqual([], r["declared_refusals_answered"])

    def test_the_lean_file_and_the_surface(self):
        lean = ROOT / "overlay/glm_lean/RequestProject/GLM/HoleBounds.lean"
        self.assertTrue(lean.exists())
        text = lean.read_text(encoding="utf-8")
        for name in ("kth_le_iff", "kth_append_le", "le_kth_append",
                     "kth_append_eq_low", "kth_append_eq_high",
                     "kth_fill_below", "kth_fill_const_low",
                     "kth_fill_const_high", "rank_append_bounds",
                     "rank_append_eq_low", "rank_append_eq_high",
                     "mid_bounds"):
            self.assertIn(f"theorem {name}", text)
        self.assertNotIn("sorry", text)
        planner = next(s for s in toolbox.SURFACES if s.name == "planner")
        self.assertIn("RequestProject/GLM/HoleBounds.lean", planner.lean)


if __name__ == "__main__":
    unittest.main()
