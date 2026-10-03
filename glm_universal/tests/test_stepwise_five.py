"""The stepwise planner, round five (Phase 91): fold frames generated from a
declaration rather than written by hand, and the widenings the last two
rounds left -- further order statistics, superlatives and the top k, bounds
under a declared range, classes the register does not hold as one value,
the remaining SI prefixes and the comparatives over the molecule table --
written as entries in it, against the marks declared in
``studies/DECLARED_FRAMES_STUDY.md`` before any code.

The column-3 census over every answered chain (mark D7) and the
non-interference census (mark D8) are exhaustive; a sample runs by default.
"""

from __future__ import annotations

import itertools
import unittest
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.evaluation import stepwise_five_cases as C
from glm_universal.reasoning import stepwise_script as ss
from glm_universal.runtime import declared_frames as df
from glm_universal.runtime import frame_declarations as fd
from glm_universal.runtime import quantity_units as qu
from glm_universal.runtime import router, stepwise as sw
from glm_universal.runtime import stepwise_five as s5
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


class TestTheRules(unittest.TestCase):
    """The rules of §1 on small columns, against brute force."""

    def test_positions_against_sorting(self):
        for n in range(1, 12):
            col = [Fraction(3 * i * i - 7 * i + 1) for i in range(n)]
            for fn in ("median", "max", "min", "q1", "q3", "max:2", "min:3"):
                pos = ss.order_positions(fn, n)
                if fn in ("q1", "q3") and n < 2 or \
                        fn == "max:2" and n < 2 or fn == "min:3" and n < 3:
                    self.assertIsNone(pos, (fn, n))
                    continue
                p = sorted(col)
                got = sum((p[k] for k in pos), Fraction(0)) / len(pos)
                self.assertEqual(s5.completed(fn, col), got, (fn, n))

    def test_order_statistic_bounds_hold_over_completions(self):
        present = [Fraction(v) for v in (1, 2, 3, 5, 7, 11)]
        for fn in ("q1", "q3", "max:2", "min:2", "median"):
            value = ss.fold_value(fn, present, 1)
            if value is None:
                continue
            lo, hi = s5._interval(value)
            for fill in range(-5, 15):
                got = s5.completed(fn, present + [Fraction(fill)])
                self.assertTrue(lo <= got <= hi, (fn, fill))

    def test_a_count_under_holes(self):
        present = [Fraction(v) for v in (1, 2, 3, 5)]
        self.assertEqual("between 3 and 5",
                         ss.fold_value("odd", present, 2, bounds=True))
        for fills in itertools.product(range(4), repeat=2):
            got = s5.completed("odd", present + [Fraction(f) for f in fills])
            self.assertTrue(3 <= got <= 5)

    def test_a_ranged_mean(self):
        present = [Fraction(3), Fraction(13, 5)]
        rng = (Fraction(0), Fraction(398, 100))
        self.assertEqual("between 4/5 and 51/14",
                         ss.fold_value("mean", present, 5, rng=rng,
                                       bounds=True))
        self.assertIsNone(ss.fold_value("mean", present, 5, bounds=True))

    def test_top_rows_and_ties(self):
        pairs = [(Fraction(3), "a"), (Fraction(9), "b"), (Fraction(5), "c")]
        self.assertEqual(["b", "c"], ss.top_rows(pairs, 2, ">"))
        self.assertEqual(["a"], ss.top_rows(pairs, 1, "<"))
        tied = pairs + [(Fraction(5), "d")]
        self.assertIsNone(ss.top_rows(tied, 2, ">"))
        self.assertIsNone(ss.top_rows(pairs, 4, ">"))


class TestTheDeclaration(unittest.TestCase):
    """D1: the frames are one declaration, and the reader is generated."""

    def test_every_frame_names_a_builder_and_a_round(self):
        for f in fd.FRAMES:
            self.assertIn(f.build, ("fold4", "fold", "top", "bounds"))
            self.assertIn(f.round, (3, 4, 5))
            for name, scope in f.vocab:
                self.assertIn(name, fd.VOCABULARIES)
                self.assertIn(scope, ("whole", "present"))

    def test_the_ranges_hold_of_every_present_reading(self):
        rows = session().field_surface.table_by_name("element").rows()
        for field, (lo, hi, why) in fd.RANGES.items():
            self.assertTrue(why)
            for k, r in rows.items():
                v = r.get(field)
                if v is not None:
                    self.assertTrue(lo <= Fraction(v) <= hi, (field, k))

    def test_every_superlative_is_of_a_declared_comparative(self):
        for word, comp in fd.SUPERLATIVES.items():
            self.assertIn(comp, df.COMPARATIVES)

    def test_the_unions(self):
        names = [n for _k, n in df.members(session().field_surface,
                                           "rare earths")]
        self.assertEqual(17, len(names))
        self.assertIn("Scandium", names)
        self.assertIn("Yttrium", names)
        metals = df.members(session().field_surface, "metals")
        self.assertEqual(91, len(metals))
        self.assertNotIn("metals", df.DECLARED_SETS)

    def test_the_prefixes_are_exact_and_hang_on_the_entries(self):
        self.assertEqual(Fraction(10 ** 18), qu.read_unit("exavolts").factor)
        self.assertEqual(Fraction(1, 10 ** 15),
                         qu.read_unit("femtocoulombs").factor)
        with s5.without_round_five_entries():
            with self.assertRaises(qu.UnitRefused):
                qu.read_unit("exavolts")
        self.assertTrue(fd.DECLARE_ROUND_FIVE)

    def test_the_generated_reader_is_the_hand_written_one(self):
        r = s5.generated_report()
        self.assertEqual(r["texts"], r["identical"], r["differ"][:3])
        self.assertGreater(r["fold_texts"], 0)
        self.assertEqual(0, r["emptied_fold_reads"])
        self.assertTrue(r["met"])


class TestTheCorpus(unittest.TestCase):
    """D2-D5: every declared case; round four's reader answers none."""

    def test_every_declared_case(self):
        for cid, q, want in C.all_cases():
            with self.subTest(case=cid):
                got = verdict(sw.answer(session(), q))
                self.assertEqual(want, got[:len(want)])

    def test_round_four_answers_none_of_the_corpus(self):
        with s5.round_four_reader():
            answered = [cid for cid, q, _ in C.all_cases()
                        if sw.answer(session(), q).answered]
        self.assertEqual([], answered)

    def test_the_entries_carry_every_widening(self):
        for cid, q, _want in C.all_cases():
            with s5.round_four_reader():
                before = verdict(sw.answer(session(), q))
            with s5.without_round_five_entries():
                bare = verdict(sw.answer(session(), q))
            with self.subTest(case=cid):
                self.assertEqual(before, bare)

    def test_follow_ups(self):
        r = s5.follow_ups_report(session())
        self.assertEqual(r["cases"], r["met"], r["rows"])

    def test_a_top_k_names_its_rows_in_order(self):
        a = sw.answer(session(), case(C.SUPERLATIVE_CASES, "s04")[1])
        step = fold_step(a.chain)
        self.assertEqual("top", step.detail["fn"])
        self.assertEqual(3, step.detail["k"])
        self.assertIn("top 3 by heaviest", ss.sentence(step))

    def test_a_ranged_bound_names_its_range(self):
        a = sw.answer(session(), case(C.BOUND_CASES, "p04")[1])
        step = fold_step(a.chain)
        self.assertEqual(["0", "199/50"], step.detail["range"])
        self.assertIn("declared range 0 to 199/50", ss.sentence(step))

    def test_the_moves_are_as_declared(self):
        r = s5.moved_report(session())
        self.assertEqual(r["cases"], r["met"], r["rows"])


class TestCompletions(unittest.TestCase):
    """D6: sound and sharp on the register."""

    def test_completions(self):
        r = s5.completions_report(session(), per_answer=40)
        self.assertTrue(r["met"], r)
        self.assertEqual(10, len(r["bounded"]))


class TestScripts(unittest.TestCase):
    """D7: every answered chain's script, and every mutation of it."""

    SAMPLE = (("k06", C.ORDER_CASES), ("s06", C.SUPERLATIVE_CASES),
              ("p04", C.BOUND_CASES), ("m02", C.MOLECULE_CASES),
              ("c01", C.CLASS_CASES))

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
        r = s5.scripts_report(session())
        self.assertEqual([], r["failed"])
        self.assertEqual(r["steps"], r["aligned"])
        self.assertEqual([], r["escaped"])


class TestWiring(unittest.TestCase):
    """D8 and the router."""

    def test_the_router_hands_the_new_frames_to_the_stepwise_planner(self):
        r = router.route(session(), case(C.SUPERLATIVE_CASES, "s01")[1])
        self.assertTrue(r.answered)
        self.assertEqual("oganesson", r.text)
        self.assertEqual("stepwise", r.solution.kind)

    @pytest.mark.exhaustive
    def test_non_interference(self):
        r = s5.interference_report(session())
        self.assertTrue(r["met"], {k: v for k, v in r.items()
                                   if k != "moved"})

    def test_the_lean_file_and_the_surface(self):
        lean = ROOT / "overlay/glm_lean/RequestProject/GLM/DeclaredFrames.lean"
        self.assertTrue(lean.exists())
        text = lean.read_text(encoding="utf-8")
        for name in ("countP_append_bounds", "countP_fill_low",
                     "countP_fill_high", "oddCount_fill_even",
                     "oddCount_fill_odd", "oddCount_append_bounds",
                     "sum_append_bounds", "sum_fill_const",
                     "mean_append_bounds", "quartilePositions_lt",
                     "quartile_halves", "kthLargest_pos_lt",
                     "orderStat_bounds", "top_open", "top_drops"):
            self.assertIn(f"theorem {name}", text)
        self.assertNotIn("sorry", text)
        planner = next(s for s in toolbox.SURFACES if s.name == "planner")
        self.assertIn("RequestProject/GLM/DeclaredFrames.lean", planner.lean)


if __name__ == "__main__":
    unittest.main()
