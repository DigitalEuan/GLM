"""The confidence floor, pinned.

``glm_universal.reasoning.confidence_floor`` gives ``resolve`` and ``agree``
a graded answer (the value with its confidence) and a floor (``BELOW_FLOOR``
under a declared confidence); ``confidence_floor_marks`` is the computational
half of ``studies/CONFIDENCE_FLOOR_STUDY.md`` (Phase 80): an exact channel
census, and a declared grid of thresholds hunted over it.  The promise it
checks is a theorem of ``RequestProject/GLM/ConfidenceFloor.lean`` (F7).
Everything is exact.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import carried_fork as cf
from glm_universal.reasoning import confidence_floor as cfl
from glm_universal.reasoning import confidence_floor_marks as cfm
from glm_universal.reasoning import decoder_confidence as dc
from glm_universal.reasoning import python_speech as sp
from glm_universal.reasoning import python_substrate as ps

P1 = Fraction(1, 100)
P10 = Fraction(1, 10)
g = ps.golay_encode


class TestTheGradedAnswer(unittest.TestCase):

    def test_bands(self):
        self.assertEqual(cfl.band(Fraction(1)), "near-certain")
        self.assertEqual(cfl.band(Fraction(999, 1000)), "near-certain")
        self.assertEqual(cfl.band(Fraction(99, 100)), "confident")
        self.assertEqual(cfl.band(Fraction(9, 10)), "probable")
        self.assertEqual(cfl.band(Fraction(89, 100)), "uncertain")

    def test_graded_resolve_is_the_phase_77_confidence(self):
        cases = [g(1), g(2), g(3), g(4)]
        r = cfl.graded_resolve(g(1) ^ 0b1111, P10, cases)
        self.assertEqual(r["value"], g(1))
        self.assertEqual(r["confidence"], Fraction(531441, 531604))
        self.assertEqual(r["band"], "near-certain")

    def test_graded_never_refuses_on_confidence(self):
        # a second reading far below any floor is still answered, graded
        c = g(9)
        r = cfl.graded_agree([c ^ 0b111], P10)
        self.assertEqual(r["value"], c)
        self.assertEqual(r["band"], "uncertain")

    def test_graded_refuses_where_the_reading_refuses(self):
        with self.assertRaises(dc.ConfidenceRefusal) as ctx:
            cfl.graded_resolve(g(1) ^ 0b1111, P1, [g(2), g(3)])
        self.assertEqual(ctx.exception.name, "UNCORRECTABLE")


class TestTheFloor(unittest.TestCase):

    def test_below_floor_names_the_confidence(self):
        cases = [g(1), g(2), g(3), g(4)]
        with self.assertRaises(dc.ConfidenceRefusal) as ctx:
            cfl.floor_resolve(g(1) ^ 0b1111, P10, Fraction(9999, 10000),
                              cases)
        self.assertEqual(ctx.exception.name, "BELOW_FLOOR")
        self.assertIn("531441/531604", ctx.exception.reason)

    def test_above_floor_answers(self):
        r = cfl.floor_resolve(g(1) ^ 0b1111, P10, Fraction(999, 1000),
                              [g(1), g(2), g(3), g(4)])
        self.assertEqual(r["value"], g(1))
        self.assertEqual(r["floor"], Fraction(999, 1000))

    def test_floor_is_checked(self):
        for bad in (0, Fraction(3, 2), True, -1):
            with self.assertRaises(dc.ConfidenceRefusal) as ctx:
                cfl.floor_check(bad)
            self.assertEqual(ctx.exception.name, "FLOOR_OUT_OF_RANGE")
        self.assertEqual(cfl.floor_check(1), 1)


class TestTheCensus(unittest.TestCase):

    def test_the_decoder_sums_to_one(self):
        r = cfm.f1_census(brute_stride=4001)
        self.assertTrue(all(row["sum"] == 1 for row in r["decoder"]))

    def test_the_census_counts_k1(self):
        for k in (2, 4):
            n = sum(c for (m, _), c in cfm.context_census(k) if m == 4)
            k1 = cf.k1_context((k,))["rows"][0]["answered"]
            self.assertEqual(n, k1)

    def test_census_confidence_is_the_runtime(self):
        cases = cf.case_set(8)
        p = Fraction(1, 20)
        w = dc.int_weights(p)
        (m, others), _ = cfm.context_census(8)[-1]
        # a representative read of the last group, found by search
        for v in cases:
            for e, we in cfm._errors_up_to_four():
                r = v ^ e
                ds = sorted((r ^ s).bit_count() for s in cases if s != v)
                if we == m and tuple(ds) == others:
                    conf = Fraction(w[m], w[m] + sum(w[d] for d in ds))
                    self.assertEqual(
                        dc.decode_confidence(r, p, cases)["confidence"], conf)
                    return
        self.fail("no representative read")

    def test_unfloored_readings_are_not_certain(self):
        # the decoder at 1/10 answers wrong about 6.7 % of the time
        c = cfm.cell("decoder", P10, None)
        self.assertTrue(Fraction(6, 100) < c["p_wrong"] < Fraction(7, 100))
        self.assertEqual(c["retention"], 1)


class TestTheHunt(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.h = cfm.hunt()

    def test_the_promise_holds_everywhere(self):
        self.assertTrue(cfm.f2_promise(self.h)["passed"])

    def test_the_working_thresholds(self):
        r = cfm.f3_hunt(self.h)
        self.assertTrue(r["passed"])
        self.assertEqual(r["working"], {
            "1/1000": "9999/10000", "1/100": "9999/10000",
            "1/50": "9999/10000", "1/20": "999/1000", "1/10": None})
        self.assertEqual(r["recommended"]["1/10"], "graded")
        # the owner's two candidates both work up to 1/20, neither at 1/10
        for t in ("99/100", "999/1000"):
            self.assertEqual(r["owner_candidates_work_at"][t],
                             ["1/1000", "1/100", "1/50", "1/20"])

    def test_the_decoder_is_what_fails_at_one_tenth(self):
        rows = [row for row in self.h["rows"] if row["rate"] == P10]
        self.assertTrue(all(row["least_retention_reading"] == "decoder"
                            for row in rows))
        per = cfm.per_reading_working()
        self.assertIsNone(per["decoder"]["1/10"])
        self.assertEqual(per["S_2"]["1/10"], "999/1000")


class TestTheDeclaredRate(unittest.TestCase):

    def test_overdeclared_is_safe_and_underdeclared_is_not(self):
        r = cfm.f4_declared_rate()
        self.assertTrue(r["passed"])
        self.assertEqual(r["overdeclared_broken"], 0)
        self.assertEqual(r["underdeclared_broken"], 30)


class TestTheDialect(unittest.TestCase):

    def test_the_builtins_are_declared(self):
        for name in ("resolve_at", "agree_at", "resolve_floor",
                     "agree_floor"):
            self.assertIn(name, sp.BUILTINS)
        for name in ("BELOW_FLOOR", "FLOOR_OUT_OF_RANGE"):
            self.assertIn(name, ps.REFUSAL_NAMES)

    def test_resolve_at_prints_the_confidence_beside_the_answer(self):
        p = sp.speak("resolve_at(Fraction(1, 10), golay_encode(1) ^ 0b1111, "
                     "golay_encode(1), golay_encode(2), golay_encode(3), "
                     "golay_encode(4))")
        self.assertIsNone(p.refusal, p.reason)
        self.assertEqual(p.value, (0, Fraction(531441, 531604)))
        self.assertTrue(any("near-certain" in s.language for s in p.steps))
        self.assertTrue(sp.verify_payload(p)["verified"])

    def test_below_floor_carries_a_checked_certificate(self):
        p = sp.speak("resolve_floor(Fraction(1, 10), Fraction(9999, 10000), "
                     "golay_encode(1) ^ 0b1111, golay_encode(1), "
                     "golay_encode(2), golay_encode(3), golay_encode(4))")
        self.assertEqual(p.refusal, "BELOW_FLOOR")
        self.assertIn("resolve_at(", p.certificate)
        self.assertTrue(sp.verify_payload(p)["verified"])

    def test_the_declared_programs(self):
        r = cfm.f5_runtime()
        self.assertEqual(r["programs"], 16)
        # one declaration was wrong (study §2.5): recorded, not re-read
        self.assertEqual(r["as_declared"], 15)
        missed = [row for row in r["rows"] if not row["as_declared"]]
        self.assertEqual(len(missed), 1)
        self.assertEqual((missed[0]["expected"], missed[0]["got"]),
                         ("BELOW_FLOOR", "answer"))

    def test_the_prelude_agrees_with_the_runtime(self):
        ns = {}
        exec(ps.PRELUDE, ns)
        for src in ("resolve_at(Fraction(1, 20), golay_encode(9) ^ 0b11, "
                    "golay_encode(9), golay_encode(10))",
                    "agree_at(Fraction(1, 20), golay_encode(9) ^ 0b11)",
                    "resolve_floor(Fraction(1, 20), Fraction(9, 10), "
                    "golay_encode(9) ^ 0b11, golay_encode(9))"):
            self.assertEqual(ns["run_source"](src), sp.speak(src).value)

    def test_the_old_builtins_do_not_move(self):
        self.assertTrue(cfm.f6_unchanged()["passed"])


class TestTheRecord(unittest.TestCase):

    def test_the_lean_file_states_every_theorem(self):
        self.assertTrue(cfm._lean_has(cfm.LEAN_THEOREMS))


if __name__ == "__main__":
    unittest.main()
