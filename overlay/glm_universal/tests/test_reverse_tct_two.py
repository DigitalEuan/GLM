"""Tests for Reverse Three Column Thinking, round two (Phase 68): the widened
fragment (integer layer, bitwise operators, masks), disjunction and
De Morgan-closed negation, piecewise case splits, and the relay into the
planner -- held to the marks ``studies/REVERSE_TCT_STUDY.md`` §7 declared
before any round-two code."""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.evaluation import reverse_tct_two_cases as C
from glm_universal.reasoning import reverse_tct as rt
from glm_universal.reasoning import reverse_tct_script as rs
from glm_universal.runtime import python_tct as pt
from glm_universal.runtime import reverse_relay as rr
from glm_universal.runtime import router
from glm_universal.runtime.tct_engine import package_root

ROOT = Path(__file__).resolve().parents[3]


def _got(a):
    return a.sentence if a.answered else a.refusal


class TestW1TheWidenedGrammar(unittest.TestCase):

    def test_say_cases_word_for_word_and_read_back(self):
        for cid, src, want in C.SAY_CASES:
            with self.subTest(case=cid):
                a = rt.say(src)
                self.assertTrue(a.answered, a.reason)
                self.assertEqual(a.sentence, want)
                self.assertEqual(rt.read(want), rt.from_source(src))

    def test_refusals_carry_their_names(self):
        for cid, src, name in C.SAY_REFUSALS:
            with self.subTest(case=cid):
                self.assertEqual(rt.say(src).refusal, name)
        for cid, s in C.READ_REFUSALS:
            with self.subTest(case=cid):
                with self.assertRaises(rt.ReverseRefusal) as ctx:
                    rt.read(s)
                self.assertEqual(ctx.exception.name, "UNREADABLE")

    def test_python_floor_and_remainder_are_spoken_with_their_values(self):
        a = rt.say("-17 // 5")
        self.assertEqual(a.certificate["value"], ["lit", "-4/1"])
        a = rt.say("-17 % 5")
        self.assertEqual(a.certificate["value"], ["lit", "3/1"])

    def test_depth_one_wide_battery(self):
        terms = rs.wide_battery(C.WIDE_BATTERY_ATOMS, 1, rs.WIDE_UNARY,
                                rs.WIDE_BINARY)
        got = rs._round_trip(terms)
        self.assertEqual(got["round_trips"], got["terms"])
        self.assertEqual(got["collisions"], 0)

    @pytest.mark.exhaustive
    def test_the_declared_batteries(self):
        r = rs.reverse_two_report(batteries=True)
        for key, n in (("wide_battery", 216723), ("mask_battery", 18500)):
            with self.subTest(battery=key):
                self.assertEqual(r[key]["terms"], n)
                self.assertEqual(r[key]["round_trips"], n)
                self.assertEqual(r[key]["collisions"], 0)
        nb = r["negation_battery"]
        self.assertEqual(nb["statements"], 650)
        self.assertEqual(nb["answered"], 650)
        self.assertEqual(nb["double_negation_certified"], 650)
        self.assertEqual(nb["grid_exact"], 650)


class TestW2TheDialect(unittest.TestCase):

    def test_thirty_six_programs_inside_and_agreeing(self):
        d = rs.reverse_two_report(batteries=False)["dialect"]
        self.assertEqual(d["inside"], 36)
        self.assertEqual(d["agree"], 36)
        self.assertEqual(d["listed_inside"], d["listed"])
        self.assertEqual(d["unlisted_inside"], [])


class TestW3DisjunctionAndNegation(unittest.TestCase):

    def test_negate_cases(self):
        for cid, s, want in C.NEGATE_CASES:
            with self.subTest(case=cid):
                self.assertEqual(_got(rt.negate(s)), want)

    def test_compound_negation_is_no_longer_refused(self):
        a = rt.negate("x >= 0 and y >= 0")
        self.assertTrue(a.answered)
        self.assertNotEqual(a.refusal, "NOT_IN_FRAGMENT")

    def test_simplification_keeps_meaning(self):
        s = "(x < 1 or y < 1) and x < 1"
        a = rt.negate(s)
        self.assertTrue(a.answered)
        self.assertEqual(rt.equivalent("not (" + s + ")",
                                       "x >= 1").verdict, "SAME")


class TestW4TheOperations(unittest.TestCase):

    def test_entailment(self):
        for cid, ps, c, want in C.ENTAIL_CASES:
            with self.subTest(case=cid):
                self.assertEqual(rt.entails(list(ps), c).verdict, want)

    def test_bounds(self):
        for cid, v, ps, want in C.BOUNDS_CASES:
            with self.subTest(case=cid):
                self.assertEqual(_got(rt.bounds(v, list(ps))), want)

    def test_equivalence(self):
        for cid, a, b, want in C.EQUIVALENCE_CASES:
            with self.subTest(case=cid):
                self.assertEqual(rt.equivalent(a, b).verdict, want)


class TestW8PhaseSixtySevenStillRight(unittest.TestCase):

    def test_every_phase_67_case_right_or_declared_superseded(self):
        p = rs.reverse_two_report(batteries=False)["phase67"]
        self.assertEqual(p["wrong"], 0, p["wrong_ids"])
        self.assertEqual(p["superseded"], 4)


class TestW5Scripts(unittest.TestCase):

    def test_one_script_of_each_new_kind_and_its_mutant(self):
        root = str(package_root())
        for a in (rt.say("-17 % 5"),
                  rt.say("len(frozenset({1, 2}) ^ frozenset({2, 3}))"),
                  rt.entails(["x < 0 or x > 2", "x > 1"], "x > 2"),
                  rt.negate("x >= 0 and y >= 0"),
                  rt.equivalent("abs(x)", "max(x, -x)")):
            with self.subTest(op=a.operation, verdict=a.verdict):
                self.assertTrue(a.answered, a.reason)
                self.assertTrue(pt.run_column3(
                    rs.render_script(a, root))["verified"])
                bad = rs.mutated_script(a, root)
                if bad is not None:
                    self.assertFalse(pt.run_column3(bad)["verified"])

    @pytest.mark.exhaustive
    def test_every_round_two_script(self):
        got = pt.reverse_two_scripts()
        self.assertEqual(got["scripts"], 92)
        self.assertEqual(got["verified"], got["scripts"])
        self.assertEqual(got["mutants"], 84)
        self.assertEqual(got["caught"], got["mutants"])


class TestW6TheRelay(unittest.TestCase):

    def test_one_relay(self):
        a = rr.answer_any("relay: say: Fraction(1, 3) + Fraction(1, 6)")
        self.assertTrue(a.answered, a.reason)
        self.assertEqual(a.verdict, "RELAYED")
        hs = a.certificate["handoffs"]
        self.assertEqual(len(hs), 2)
        for h in hs:
            self.assertEqual(h["surface"], "planner")
            self.assertEqual(h["status"], "AGREES")

    def test_nothing_to_relay_and_out_of_range_are_refused(self):
        a = rr.answer_any("relay: entails: x > 3 ; x > 2")
        self.assertIn(a.refusal, ("NOTHING_TO_RELAY",))
        a = rr.answer_any("relay: say: 10 ** 13")
        self.assertEqual(a.refusal, "OUT_OF_RANGE")

    def test_the_nearest_decimal_rounds_half_away(self):
        self.assertEqual(rr.nearest_decimal(Fraction(2, 3), 5), "0.66667")
        self.assertEqual(rr.nearest_decimal(Fraction(-7, 3), 3), "-2.333")

    def test_the_router_sends_relay_to_the_reverse_surface(self):
        self.assertEqual(router.reader_of("relay: say: 2 + 3"), "reverse")

    @pytest.mark.exhaustive
    def test_the_declared_relay_cases_and_controls(self):
        r = rr.relay_report()
        self.assertEqual(r["cases"], 20)
        self.assertEqual(r["right"], 20, r["wrong"])
        self.assertEqual(r["handoffs_ok"], r["handoffs"])
        self.assertEqual(r["disagrees"], 0)
        self.assertEqual(r["questions_read_back"], r["handoffs"])
        self.assertEqual(r["control_verbatim"]["answered"], 0)


class TestTheLeanFile(unittest.TestCase):

    def test_the_proved_names_are_there(self):
        text = (ROOT / "RequestProject/GLM/ReverseTCTTwo.lean").read_text(
            encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in ("render_prefix_free", "render_injective",
                     "renderCNF_injective", "negate_product_exact",
                     "simplify_preserves", "abs_split", "min_split",
                     "max_split", "entails_of_cases_refuted",
                     "floor_mod_identity", "mod_sign_bounds",
                     "chain_floor_misses"):
            self.assertIn(f"theorem {name}", text)

    def test_the_catalogue_names_the_new_lean_file(self):
        from glm_universal.runtime import toolbox
        s = next(x for x in toolbox.SURFACES if x.name == "reverse")
        self.assertIn("RequestProject/GLM/ReverseTCTTwo.lean", s.lean)


if __name__ == "__main__":
    unittest.main()
