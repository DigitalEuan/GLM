"""Tests for Reverse Three Column Thinking, round three (Phase 69): the integer
sort -- floor quotient and remainder split into residue cases, rows tightened
over ℤ, refutations certified by their derivation, integer witnesses, and the
named refusal where integer elimination stops -- held to the marks
``studies/REVERSE_TCT_STUDY.md`` §10 declared before any round-three code."""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.evaluation import reverse_tct_int_cases as C
from glm_universal.reasoning import reverse_tct as rt
from glm_universal.reasoning import reverse_tct_int as ri
from glm_universal.runtime import python_tct as pt
from glm_universal.runtime import router
from glm_universal.runtime.tct_engine import package_root

ROOT = Path(__file__).resolve().parents[3]


def _verdict(a):
    return a.refusal or a.verdict


class TestTheResidueSplit(unittest.TestCase):

    def test_a_remainder_splits_into_one_case_per_residue(self):
        s, _ = rt.parse_any("x % 3 == 1")
        self.assertEqual(len(ri.int_cases([s])), 3)
        s, _ = rt.parse_any("x % -4 == -1")
        self.assertEqual(len(ri.int_cases([s])), 4)

    def test_the_quotient_is_shared_by_floor_quotient_and_remainder(self):
        s, _ = rt.parse_any("x // 5 + x % 5 == 3")
        cases = ri.int_cases([s])
        self.assertEqual(len(cases), 5)
        for case in cases:
            self.assertEqual(rt._variables(tuple(x for _, a, b in case
                                                 for x in (a, b))),
                             ["_q1", "x"])

    def test_the_refusals_carry_their_names(self):
        for src, name in (("(x * x) % 3 == 1", "NONLINEAR"),
                          ("x % Fraction(1, 2) == 0", "NOT_INTEGER"),
                          ("(x / 2) % 3 == 0", "NOT_INTEGER"),
                          ("x % y == 0", "NOT_POLYNOMIAL"),
                          ("x % 100 == 1", "NOT_IN_FRAGMENT")):
            with self.subTest(src=src):
                s, _ = rt.parse_any(src)
                with self.assertRaises(rt.ReverseRefusal) as ctx:
                    ri.int_cases([s])
                self.assertEqual(ctx.exception.name, name)


class TestTightening(unittest.TestCase):

    def test_strict_rows_and_the_gcd(self):
        # 2x - 1 < 0  ->  2x <= 0 over the integers -> x <= 0
        self.assertEqual(ri.tighten({"x": Fraction(2)}, Fraction(-1), True),
                         ((("x", 1),), 0))
        # 2x - 1 <= 0  ->  x + ceil(-1/2) = x <= 0
        self.assertEqual(ri.tighten({"x": Fraction(2)}, Fraction(-1), False),
                         ((("x", 1),), 0))
        # -2x + 1 <= 0 -> -x + 1 <= 0
        self.assertEqual(ri.tighten({"x": Fraction(-2)}, Fraction(1), False),
                         ((("x", -1),), 1))
        # x/2 + 1/3 <= 0 -> 3x + 2 <= 0 -> x + ceil(2/3) = x + 1 <= 0
        self.assertEqual(ri.tighten({"x": Fraction(1, 2)}, Fraction(1, 3),
                                    False), ((("x", 1),), 1))

    def test_the_tightening_is_exact_on_a_range(self):
        for a in range(-6, 7):
            for k in range(-9, 10):
                for strict in (False, True):
                    if not a:
                        continue
                    row = ri.tighten({"x": Fraction(a, 2)}, Fraction(k, 3),
                                     strict)
                    for x in range(-12, 13):
                        e = Fraction(a, 2) * x + Fraction(k, 3)
                        want = e < 0 if strict else e <= 0
                        got = sum(c * x for _, c in row[0]) + row[1] <= 0
                        self.assertEqual(got, want)


class TestX1X2TheDeclaredCases(unittest.TestCase):

    def test_entailment_over_the_integers(self):
        for cid, ps, c, want in C.ENTAIL_CASES:
            with self.subTest(case=cid):
                self.assertEqual(_verdict(ri.entails_int(list(ps), c)), want)

    def test_bounds_over_the_integers(self):
        for cid, v, ps, want in C.BOUNDS_CASES:
            with self.subTest(case=cid):
                a = ri.bounds_int(v, list(ps))
                self.assertEqual(a.refusal or a.sentence, want)

    def test_the_rational_operations_are_unchanged(self):
        self.assertEqual(rt.entails(["x > 2"], "x >= 3").verdict,
                         "INDEPENDENT")
        self.assertEqual(rt.entails(["x // 3 == 1"], "x >= 3").refusal,
                         "NOT_POLYNOMIAL")

    def test_the_new_refusal_where_elimination_stops(self):
        # Pugh's example: no integer point, a rational one, and not refuted by
        # elimination with rounding.  Round three refused it
        # INTEGER_UNDECIDED; since Phase 79 the complete decision behind the
        # elimination refutes it (studies/INTEGER_DECISION_STUDY.md), and the
        # refusal is kept only for a case past the decision's declared limit.
        ps = ["27 <= 11*x + 13*y", "11*x + 13*y <= 45",
              "-10 <= 7*x - 9*y", "7*x - 9*y <= 4"]
        stmts = [rt.parse_any(p)[0] for p in ps]
        (case,) = ri.int_cases(stmts)
        self.assertEqual(ri._refute(ri._input_rows(case))[0], "open")
        a = ri.entails_int(ps, "x == 0")
        self.assertEqual(a.refusal, "INCONSISTENT_PREMISES")
        self.assertIn("omega", a.certificate["inconsistent"][0])
        from glm_universal.reasoning import integer_decision as idc
        saved = idc.NODE_LIMIT
        try:
            idc.NODE_LIMIT = 1
            self.assertEqual(ri.entails_int(ps, "x == 0").refusal,
                             "INTEGER_UNDECIDED")
        finally:
            idc.NODE_LIMIT = saved
        self.assertEqual(C.NEW_REFUSAL_NAMES, ("INTEGER_UNDECIDED",))


class TestX3ColumnThree(unittest.TestCase):

    def test_one_script_of_each_kind_and_its_mutant(self):
        root = str(package_root())
        for q in ("entails over the integers: x % 4 == 1 ; x % 2 == 1",
                  "entails over the integers: x // 3 == 2 ; x == 7",
                  "entails over the integers: 2 * x == 1 ; x == 0",
                  "bounds over the integers of x: x % 5 == 2 ; x >= 10 ; "
                  "x <= 30"):
            with self.subTest(q=q):
                a = rt.answer(q)
                self.assertTrue(pt.run_column3(
                    ri.render_script(a, root))["verified"])
                bad = ri.mutated_script(a, root)
                self.assertIsNotNone(bad)
                self.assertFalse(pt.run_column3(bad)["verified"])

    @pytest.mark.exhaustive
    def test_every_declared_script(self):
        got = pt.reverse_int_scripts()
        self.assertEqual(got["verified"], got["scripts"])
        self.assertEqual(got["caught"], got["mutants"])
        self.assertEqual(got["scripts"], 34)


class TestX4AgainstBruteForce(unittest.TestCase):

    def test_the_battery(self):
        got = ri.battery()
        for key in ("entails", "bounds"):
            with self.subTest(key=key):
                self.assertEqual(got[key]["disagree"], [])
                self.assertEqual(got[key]["other_refusals"], [])
        self.assertEqual(got["entails"]["questions"], 102)
        self.assertEqual(got["bounds"]["questions"], 14)


class TestX5TheControl(unittest.TestCase):

    def test_over_the_rationals(self):
        c = ri.int_report(with_battery=False)["control"]
        self.assertEqual(c["entails"]["not_polynomial"], 20)
        self.assertEqual(len(c["entails"]["different"]), 9)
        self.assertEqual(c["bounds"]["not_polynomial"], 5)
        self.assertEqual(len(c["bounds"]["different"]), 5)


class TestTheSurface(unittest.TestCase):

    def test_the_router_sends_the_integer_forms_to_the_reverse_surface(self):
        for q in ("entails over the integers: x > 2 ; x >= 3",
                  "bounds over the integers of x: x // 3 == 1"):
            with self.subTest(q=q):
                self.assertTrue(rt.reads(q))
                self.assertEqual(router.reader_of(q), "reverse")

    def test_a_malformed_integer_question_is_unreadable(self):
        self.assertEqual(rt.answer("entails over the integers: x > 2").refusal,
                         "UNREADABLE")

    def test_the_catalogue_names_the_new_lean_file(self):
        from glm_universal.runtime import toolbox
        s = next(x for x in toolbox.SURFACES if x.name == "reverse")
        self.assertIn("RequestProject/GLM/ReverseTCTThree.lean", s.lean)


class TestTheLeanFile(unittest.TestCase):

    def test_the_proved_names_are_there(self):
        text = (ROOT / "overlay/glm_lean/RequestProject/GLM/ReverseTCTThree.lean").read_text(
            encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in ("residue_split_pos", "residue_split_neg",
                     "residue_exists_pos", "residue_exists_neg",
                     "strict_tighten", "gcd_tighten", "combine_sound",
                     "step_sound", "derivation_sound", "refuted_no_point",
                     "rational_refutation_suffices", "two_x_eq_one"):
            self.assertIn(f"theorem {name}", text)


if __name__ == "__main__":
    unittest.main()
