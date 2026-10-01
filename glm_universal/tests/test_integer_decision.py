"""Tests for the complete integer decision (Phase 79): the Omega test behind
round three's ``INTEGER_UNDECIDED``, its refutation trees and their checker,
held to the marks ``studies/INTEGER_DECISION_STUDY.md`` declared before any
code of the round."""

from __future__ import annotations

import itertools
import unittest
from pathlib import Path

import pytest

from glm_universal.evaluation import integer_decision_cases as C
from glm_universal.reasoning import integer_decision as idc
from glm_universal.reasoning import reverse_tct as rt
from glm_universal.reasoning import reverse_tct_int as ri
from glm_universal.runtime import python_tct as pt
from glm_universal.runtime.tct_engine import package_root

ROOT = Path(__file__).resolve().parents[3]
LEAN = ROOT / "overlay" / "glm_lean" / "RequestProject" / "GLM" / \
    "IntegerDecision.lean"

PUGH = [idc.tight({"x": 11, "y": 13}, -45), idc.tight({"x": -11, "y": -13}, 27),
        idc.tight({"x": 7, "y": -9}, -4), idc.tight({"x": -7, "y": 9}, -10)]


def _lcg(seed):
    state = seed
    while True:
        state = (6364136223846793005 * state + 1442695040888963407) % (1 << 64)
        yield state >> 33


def _systems(seed, count, box):
    gen = _lcg(seed)

    def pick(lo, hi):
        return lo + next(gen) % (hi - lo + 1)

    for _ in range(count):
        vs = ("x", "y") if pick(0, 1) else ("x", "y", "z")
        rows = []
        for _ in range(pick(2, 4)):
            co = {v: pick(-9, 9) for v in vs}
            k = pick(-30, 30)
            rows.append(idc.tight(co, k))
            if pick(0, 3) == 0:
                rows.append(idc.tight({v: -c for v, c in co.items()}, -k))
        for v in vs:
            rows += [idc.tight({v: 1}, -box), idc.tight({v: -1}, -box)]
        yield vs, rows


def _feasible(rows, vs, box):
    return any(all(sum(c * dict(zip(vs, d))[v] for v, c in r[0]) + r[1] <= 0
                   for r in rows)
               for d in itertools.product(range(-box, box + 1),
                                          repeat=len(vs)))


class TestTheDecision(unittest.TestCase):

    def test_pugh_is_refuted_and_the_tree_checks(self):
        status, node = idc.decide_rows(PUGH)
        self.assertEqual(status, "unsat")
        self.assertTrue(idc.check_node(PUGH, node))
        self.assertFalse(idc.check_node(PUGH, idc.mutate_node(node)))
        self.assertEqual(ri._refute(PUGH)[0], "open")

    def test_agrees_with_enumeration_on_bounded_systems(self):
        for vs, rows in _systems(7, 400, 5):
            with self.subTest(rows=rows):
                status, got = idc.decide_rows(rows)
                self.assertEqual(status == "sat", _feasible(rows, vs, 5))
                if status == "unsat":
                    self.assertTrue(idc.check_node(rows, got))
                    self.assertFalse(idc.check_node(rows,
                                                    idc.mutate_node(got)))
                else:
                    self.assertTrue(all(idc._holds(r, got) for r in rows))

    def test_rows_must_be_tightened(self):
        with self.assertRaises(ValueError):
            idc.decide_rows([((("x", 2),), 1)])

    def test_the_limit_is_the_declared_one(self):
        self.assertEqual(idc.NODE_LIMIT, C.NODE_LIMIT)
        saved = idc.NODE_LIMIT
        try:
            idc.NODE_LIMIT = 1
            with self.assertRaises(idc.DecisionLimit):
                idc.decide_rows(PUGH)
        finally:
            idc.NODE_LIMIT = saved


class TestTheChecker(unittest.TestCase):

    def test_a_substitution_needs_a_fresh_variable(self):
        rows = [idc.tight({"x": 2, "y": 1}, -1)]
        node = {"steps": [["subst", "x", "y", [], 0]],
                "end": ["contra", 0]}
        self.assertFalse(idc.check_node(rows, node))

    def test_indices_and_multipliers_are_checked(self):
        rows = [idc.tight({"x": 1}, 1), idc.tight({"x": -1}, 0)]
        good = {"steps": [["comb", 0, 1, 1, 1]], "end": ["contra", 2]}
        self.assertTrue(idc.check_node(rows, good))
        for bad in ({"steps": [["comb", 0, -1, 1, 1]], "end": ["contra", 2]},
                    {"steps": [["comb", -1, 1, 1, 1]], "end": ["contra", 2]},
                    {"steps": [["comb", 0, 1, 1, 1]], "end": ["contra", -1]},
                    {"steps": [], "end": ["contra", 0]}):
            with self.subTest(bad=bad):
                self.assertFalse(idc.check_node(rows, bad))

    def test_a_split_needs_every_child(self):
        # x >= 0, x <= 1, x <= -5: refuted in every child of a split of
        # -x <= 0 at K = 1 (x = 0, x = 1, x >= 2)
        rows = [idc.tight({"x": -1}, 0), idc.tight({"x": 1}, -1),
                idc.tight({"x": 1}, 5)]

        def leaf(n):
            return {"steps": [["comb", 2, 1, 0, 1]], "end": ["contra", n]}

        split = {"steps": [], "end": ["split", 0, 1,
                                      [leaf(5), leaf(5), leaf(4)]]}
        self.assertTrue(idc.check_node(rows, split))
        short = {"steps": [], "end": ["split", 0, 1, [leaf(5), leaf(5)]]}
        self.assertFalse(idc.check_node(rows, short))
        wrong = {"steps": [], "end": ["split", 0, 1,
                                      [leaf(5), leaf(4), leaf(4)]]}
        self.assertFalse(idc.check_node(rows, wrong))


class TestZ1NothingDecidedMoves(unittest.TestCase):

    def test_round_three_is_answered_as_declared_without_omega(self):
        rep = idc.decision_report(with_battery=False)["Z1"]
        self.assertEqual(rep["entails_right"], rep["entails_of"])
        self.assertEqual(rep["bounds_right"], rep["bounds_of"])
        self.assertEqual(rep["omega_certificates"], 0)


class TestZ2TheDeclaredCorpus(unittest.TestCase):

    def test_every_question_as_declared(self):
        rep = idc.decision_report(with_battery=False)["Z2"]
        self.assertEqual(rep["of"], 22)
        self.assertEqual(rep["right"], 22)
        self.assertEqual(rep["wrong"], [])
        self.assertEqual(rep["refused"], [])
        self.assertEqual(rep["undecided_before"], 22)


class TestZ4ColumnThree(unittest.TestCase):

    def test_every_script_verifies_and_every_omega_mutant_fails(self):
        root = str(package_root())
        for cid, a, _ in idc.decision_answers():
            with self.subTest(case=cid):
                self.assertTrue(pt.run_column3(
                    ri.render_script(a, root))["verified"])
                self.assertTrue(any("omega" in x for x in
                                    ri._case_certs(a.certificate)))
                bad = ri.mutated_script(a, root)
                self.assertIsNotNone(bad)
                self.assertFalse(pt.run_column3(bad)["verified"])


class TestZ3TheBattery(unittest.TestCase):

    @pytest.mark.exhaustive
    def test_the_battery_agrees_with_enumeration(self):
        now = idc.battery_report(True)
        then = idc.battery_report(False)
        for key in ("entails", "bounds"):
            with self.subTest(key=key):
                self.assertEqual(now[key]["questions"], 300)
                self.assertEqual(now[key]["agree"], 300)
                self.assertEqual(now[key]["undecided"], 0)
                self.assertEqual(then[key]["disagree"], [])
        self.assertEqual(then["entails"]["undecided"], 11)
        self.assertEqual(then["bounds"]["undecided"], 20)

    def test_the_battery_is_the_declared_draw(self):
        qs = C.battery_questions()
        self.assertEqual(len(qs), 300)
        self.assertEqual(qs[0][0], "z001")
        self.assertEqual(qs[0][3], "x <= 2")


class TestZ6TheLeanFile(unittest.TestCase):

    def test_the_proved_names_are_there(self):
        text = LEAN.read_text(encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in ("exact_shadow", "dark_shadow_gap", "splinter_count",
                     "splinter_tail", "split_cover", "substitution_bijective",
                     "pugh_no_integer_point", "pugh_in_box"):
            with self.subTest(name=name):
                self.assertIn(f"theorem {name}", text)


if __name__ == "__main__":
    unittest.main()
