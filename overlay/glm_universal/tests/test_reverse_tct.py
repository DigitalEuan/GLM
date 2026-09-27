"""Tests for Reverse Three Column Thinking
(:mod:`glm_universal.reasoning.reverse_tct`): the language column generated
from the mathematics and the script, held to the marks
``studies/REVERSE_TCT_STUDY.md`` declared before the module existed."""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.evaluation import reverse_tct_cases as C
from glm_universal.evaluation import reverse_tct_two_cases as C2
from glm_universal.reasoning import reverse_tct as rt
from glm_universal.reasoning import reverse_tct_script as rs
from glm_universal.runtime import python_tct as pt
from glm_universal.runtime import router
from glm_universal.runtime.tct_engine import package_root

ROOT = Path(__file__).resolve().parents[3]


def _got(a):
    return a.sentence if a.answered else a.refusal


#: Phase 67 cases whose declared answer round two (Phase 68) changed:
#: (set, case id) -> the new declared answer.
_SUPERSEDED = {(k, cid): new for k, cid, new in C2.SUPERSEDED}


class TestNumberWords(unittest.TestCase):

    def test_spelling(self):
        self.assertEqual(rt.number_words(0), ["zero"])
        self.assertEqual(rt.number_words(105), ["one", "hundred", "five"])
        self.assertEqual(rt.number_words(21), ["twenty-one"])
        self.assertEqual(rt.number_words(10 ** 12), ["1000000000000"])

    def test_every_number_below_twenty_thousand_reads_back(self):
        for n in range(20000):
            words = rt.number_words(n)
            got, end = rt._read_natural(words, 0)
            self.assertEqual((got, end), (n, len(words)))


class TestV1RoundTrip(unittest.TestCase):

    def test_say_cases_word_for_word(self):
        for cid, src, want in C.SAY_CASES:
            with self.subTest(case=cid):
                a = rt.say(src)
                self.assertTrue(a.answered, a.reason)
                self.assertEqual(a.sentence, want)
                self.assertEqual(rt.read(want), rt.from_source(src))

    def test_depth_one_battery(self):
        for t in rs.battery_terms(C.BATTERY_ATOMS, 1):
            self.assertEqual(rt.read(rt.realise(t)), t)

    @pytest.mark.exhaustive
    def test_the_declared_battery(self):
        b = rs.reverse_report()["battery"]
        self.assertEqual(b["terms"], 176617)
        self.assertEqual(b["round_trips"], b["terms"])
        self.assertEqual(b["collisions"], 0)
        self.assertEqual(b["infix_collisions"], 5684)

    def test_refusals(self):
        for cid, src, name in C.SAY_REFUSALS:
            with self.subTest(case=cid):
                new = _SUPERSEDED.get(("SAY_REFUSALS", cid))
                self.assertEqual(_got(rt.say(src)), new or name)
        for cid, s in C.READ_REFUSALS:
            with self.subTest(case=cid):
                with self.assertRaises(rt.ReverseRefusal) as ctx:
                    rt.read(s)
                self.assertEqual(ctx.exception.name, "UNREADABLE")


class TestV2Control(unittest.TestCase):

    def test_infix_is_ambiguous_scoped_is_not(self):
        a = rt.from_source("(x + y) + 1")
        b = rt.from_source("x + (y + 1)")
        self.assertNotEqual(a, b)
        self.assertEqual(rs.infix_realise(a), rs.infix_realise(b))
        self.assertNotEqual(rt.realise(a), rt.realise(b))


class TestV4ToV6TheOperations(unittest.TestCase):

    def test_entailment(self):
        for cid, ps, c, want in C.ENTAIL_CASES:
            with self.subTest(case=cid):
                self.assertEqual(rt.entails(list(ps), c).verdict, want)

    def test_solve(self):
        for cid, v, s, want in C.SOLVE_CASES:
            with self.subTest(case=cid):
                self.assertEqual(_got(rt.solve(v, s)), want)

    def test_bounds(self):
        for cid, v, ps, want in C.BOUNDS_CASES:
            with self.subTest(case=cid):
                self.assertEqual(_got(rt.bounds(v, list(ps))), want)

    def test_equivalence(self):
        for cid, a, b, want in C.EQUIVALENCE_CASES:
            with self.subTest(case=cid):
                self.assertEqual(rt.equivalent(a, b).verdict, want)

    def test_negation(self):
        for cid, s, want in C.NEGATE_CASES:
            with self.subTest(case=cid):
                want = _SUPERSEDED.get(("NEGATE_CASES", cid), want)
                self.assertEqual(_got(rt.negate(s)), want)

    def test_paraphrases_are_certified_and_plural(self):
        for cid, s in C.PARAPHRASE_CASES:
            with self.subTest(case=cid):
                a = rt.paraphrase(s)
                self.assertTrue(a.answered)
                self.assertGreaterEqual(len(a.column1) - 1, 2)
                for p in a.column1[1:]:
                    self.assertEqual(rt.equivalent(s, p).verdict, "SAME")

    def test_witnesses_are_real_points(self):
        a = rt.entails(["x > 3"], "x > 5")
        self.assertEqual(a.verdict, "INDEPENDENT")
        h = {v: Fraction(*map(int, x.split("/")))
             for v, x in a.certificate["holds_at"].items()}
        f = {v: Fraction(*map(int, x.split("/")))
             for v, x in a.certificate["fails_at"].items()}
        self.assertTrue(h["x"] > 5 and 3 < f["x"] <= 5)


class TestV8TheDialect(unittest.TestCase):

    def test_programs_inside_the_fragment_agree(self):
        d = rs.reverse_report()["dialect"]
        # 8 at Phase 67; 36 once round two (Phase 68) widened the fragment.
        self.assertEqual(d["inside"], 36)
        self.assertEqual(d["agree"], d["inside"])


class TestTheSurface(unittest.TestCase):

    def test_the_router_reads_only_the_prefixes(self):
        self.assertEqual(router.reader_of("say: 2 + 3"), "reverse")
        self.assertEqual(router.reader_of("entails: x > 3 ; x > 2"), "reverse")
        self.assertEqual(router.reader_of("solve for x: 2 * x == 4"),
                         "reverse")
        self.assertNotEqual(router.reader_of("what is 2 + 2"), "reverse")
        self.assertNotEqual(router.reader_of("x = 3\nx * x"), "reverse")

    def test_routed_answer(self):
        r = router.route(None, "entails: x + y == 10 ; x - y == 2 ; y == 4")
        self.assertEqual(r.surface, "reverse")
        self.assertTrue(r.answered)
        self.assertIn("ENTAILS", r.text)

    def test_no_declared_question_of_earlier_rounds_is_diverted(self):
        census = router.reads_census()
        for name, counts in census.items():
            with self.subTest(set=name):
                self.assertEqual(counts["reverse"], 0)

    def test_the_catalogue_names_the_lean_file_and_study(self):
        from glm_universal.runtime import toolbox
        s = next(x for x in toolbox.SURFACES if x.name == "reverse")
        self.assertTrue((ROOT / s.study).exists())
        for f in s.lean:
            self.assertTrue((ROOT / f).exists())


class TestV3Scripts(unittest.TestCase):

    def test_one_script_of_each_kind_and_its_mutant(self):
        root = str(package_root())
        for a in (rt.say("2 * x + 3 == 7"),
                  rt.entails(["x > 0"], "x != 0"),
                  rt.entails(["x > 3"], "x > 5"),
                  rt.bounds("x", ["x + y == 10", "y >= 4"]),
                  rt.solve("x", "-3 * x + 1 <= 7"),
                  rt.equivalent("(x + 1) ** 2", "x ** 2 + 2 * x + 1"),
                  rt.paraphrase("x - y != 4"),
                  rt.negate("x < 3")):
            with self.subTest(op=a.operation, verdict=a.verdict):
                self.assertTrue(pt.run_column3(
                    rs.render_script(a, root))["verified"])
                bad = rs.mutated_script(a, root)
                if bad is not None:
                    self.assertFalse(pt.run_column3(bad)["verified"])

    @pytest.mark.exhaustive
    def test_every_declared_script(self):
        got = pt.reverse_scripts()
        self.assertEqual(got["verified"], got["scripts"])
        self.assertEqual(got["scripts"], 95)
        self.assertEqual(got["caught"], got["mutants"])

    @pytest.mark.exhaustive
    def test_the_control(self):
        got = pt.reverse_control()
        self.assertEqual(got["control_correct"], 0)
        self.assertEqual(got["reverse_correct"], got["questions"])


class TestTheLeanFile(unittest.TestCase):

    def test_the_proved_names_are_there(self):
        text = (ROOT / "RequestProject/GLM/ReverseTCT.lean").read_text(
            encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in ("render_prefix_free", "render_injective",
                     "renderStmt_injective", "renderConj_injective",
                     "infix_not_injective", "negate_exact", "farkas_refutes",
                     "entails_of_refuted", "pairing_lt", "solve_eq",
                     "grid_identity"):
            self.assertIn(f"theorem {name}", text)


if __name__ == "__main__":
    unittest.main()
