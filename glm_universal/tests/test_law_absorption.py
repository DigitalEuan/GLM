"""The UBP laws absorbed, pinned.

``glm_universal.reasoning.law_absorption`` is the computational half of
``studies/LAW_ABSORPTION_STUDY.md`` (Phase 75); the two corrections it answers
with are theorems of ``RequestProject/GLM/LawAbsorption.lean`` (D8).  This file
fixes the fates, the declared questions and the retests, so that a change to
the substrate, the planner or the frozen register that moved any of them fails
here rather than quietly rewriting the study.  Everything is exact (D7).
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.evaluation import law_absorption_cases as C
from glm_universal.reasoning import law_absorption as la
from glm_universal.reasoning import law_register as lr
from glm_universal.runtime import semantic_plan as sp


class TestFates(unittest.TestCase):

    def test_one_fate_per_law(self):
        table = la.ABSORPTION()
        self.assertEqual(len(table), 65)
        self.assertEqual(set(table), {r["ubp_id"] for r in lr.register_rows()})
        self.assertTrue(all(v[0] in la.FATES for v in table.values()))

    def test_census(self):
        self.assertEqual(la.fate_census(), {"absorbed": 11, "already GLM": 2,
                                            "retested": 3, "retired": 49})

    def test_every_absorbed_law_names_a_fact(self):
        for law, (fate, _said, keys) in la.ABSORPTION().items():
            if fate == "absorbed":
                self.assertTrue(keys, law)
                self.assertTrue(all(k in la.FACTS for k in keys), law)
                self.assertTrue(all(law in la.FACTS[k].laws for k in keys))

    def test_the_absorbed_laws_are_the_ones_that_held(self):
        absorbed = {k for k, v in la.ABSORPTION().items() if v[0] == "absorbed"}
        structural = {k for k, v in lr.EXACT_GRADES.items()
                      if v[0] in ("structural", "overclaimed")}
        self.assertEqual(absorbed, structural | {"LAW_STORAGE_HARDENED_001"})


class TestFacts(unittest.TestCase):

    def test_facts_agree_with_phase_74_and_lean(self):
        self.assertEqual(la.fact_value("codewords")[0], "4096")
        self.assertEqual(la.fact_value("rate")[0], "1/2")
        self.assertEqual(la.fact_value("min-distance")[0], "8")
        self.assertEqual(la.fact_value("covering-radius")[0], "4")
        self.assertEqual(la.fact_value("corrects")[0], "3")
        self.assertEqual(la.fact_value("unique-fraction")[0], "2325/4096")
        self.assertEqual(la.fact_value("kissing")[0], "196560")
        self.assertEqual(la.fact_value("weight-count", 12)[0], "2576")
        self.assertEqual(la.fact_value("perfect", 23)[0], "True")
        self.assertEqual(la.fact_value("perfect", 24)[0], "False")

    def test_outcome_by_weight(self):
        got = [la.fact_value("outcome", k)[0] for k in range(9)]
        # weight 7 is always miscorrected too: every 7-set lies in exactly
        # one octad, so its coset has weight 1
        self.assertEqual(got, ["right"] * 4 + ["refused", "wrong", "mixed",
                                               "wrong", "mixed"])

    def test_storage_law_corrected(self):
        self.assertEqual(la.fact_value("always-right", Fraction(0))[0], "True")
        for p in (Fraction(1, 10 ** 6), Fraction(3, 100), Fraction(1, 2)):
            self.assertEqual(la.fact_value("always-right", p)[0], "False")

    def test_confidence_equals_brute_force(self):
        for row in la.brute_checks():
            self.assertTrue(row["equal"], row)

    def test_confidence_refusals(self):
        with self.assertRaises(la.FactRefusal) as tie:
            la.confidence(4, Fraction(1, 100))
        self.assertEqual(tie.exception.name, "TIE")
        with self.assertRaises(la.FactRefusal) as far:
            la.confidence(5, Fraction(1, 100))
        self.assertEqual(far.exception.name, "BEYOND_COVERING_RADIUS")
        with self.assertRaises(la.FactRefusal) as rate:
            la.confidence(1, Fraction(3, 2))
        self.assertEqual(rate.exception.name, "NOT_A_PROBABILITY")

    def test_confidence_falls_with_noise_and_distance(self):
        p = Fraction(1, 20)
        values = [la.confidence(d, p) for d in range(4)]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertGreater(la.confidence(3, Fraction(1, 100)),
                           la.confidence(3, Fraction(1, 10)))


class TestDeclaredQuestions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = la.law_absorption_report()

    def test_every_mark_met(self):
        self.assertEqual(self.report["marks"],
                         {m: True for m in ("A1", "A2", "A3", "A4", "A5",
                                            "A6", "A7", "A8")})

    def test_declared_set(self):
        self.assertEqual(self.report["declared_total"], len(C.CASES))
        self.assertEqual(self.report["declared_ok"], len(C.CASES))
        self.assertEqual(self.report["declared_wrong"], 0)

    def test_through_the_planner_and_the_control(self):
        self.assertEqual(self.report["planner"]["as_declared"], len(C.CASES))
        self.assertEqual(self.report["planner"]["wrong"], 0)
        self.assertEqual(self.report["control"]["answered"], 0)

    def test_frame_reads_nothing_else(self):
        for text in C.NOT_READ:
            self.assertIsNone(la.read_question(sp.clean(text)), text)
        self.assertEqual(self.report["evaluation_sweep"]["read"], [])

    def test_frame_is_in_the_planner(self):
        self.assertIn("substrate", [name for name, _ in sp.FRAMES])


class TestRetests(unittest.TestCase):

    def test_three_retests_all_refused(self):
        rows = {r["law"]: r for r in la.retests()}
        self.assertEqual(set(rows), {"LAW_FORCE_003", "LAW_FORCE_005",
                                     "LAW_CHEM_002"})
        self.assertEqual({k: r["p_decimal"] for k, r in rows.items()},
                         {"LAW_FORCE_003": "0.9077", "LAW_FORCE_005": "0.9925",
                          "LAW_CHEM_002": "0.4705"})
        self.assertFalse(any(r["admitted"] for r in rows.values()))

    def test_the_inverse_y_cancels(self):
        rows = {r["law"]: r for r in la.retests()}
        self.assertEqual(rows["LAW_FORCE_003"]["value"], "0.875000")
        self.assertEqual(rows["LAW_FORCE_005"]["value"], "1.379629")  # truncated, as Phase 74 displays


if __name__ == "__main__":
    unittest.main()
