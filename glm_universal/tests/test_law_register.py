"""The UBP law register re-read, pinned.

``glm_universal.reasoning.law_register`` is the computational half of
``studies/LAW_REGISTER_STUDY.md``; the decoder facts it rests on are theorems of
``RequestProject/GLM/LawRegister.lean`` (the specification, D8).  This file
fixes the numbers so that a change to the substrate or to the frozen register
that moved any of them fails here rather than quietly rewriting the study.
Everything is exact (D7).
"""

from __future__ import annotations

import re
import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.reasoning import law_register as lr
from glm_universal.runtime import toolbox as tb

ROOT = Path(__file__).resolve().parents[3]


class TestRegister(unittest.TestCase):

    def test_sixty_five_rows(self):
        rows = lr.register_rows()
        self.assertEqual(len(rows), 65)
        verdicts = [r["verdict"] for r in rows]
        self.assertEqual(verdicts.count("RETAINED-EXACT"), 16)
        self.assertEqual(verdicts.count("RETAINED-NUM"), 49)

    def test_frozen_copy_is_the_supplied_file(self):
        supplied = ROOT / lr.SOURCE_PATH
        if supplied.exists():
            self.assertEqual(supplied.read_bytes(), lr.DATA_PATH.read_bytes())

    def test_every_row_is_graded_once(self):
        for r in lr.register_rows():
            table = lr.EXACT_GRADES if r["verdict"] == "RETAINED-EXACT" else lr.NUMERIC_GRADES
            self.assertIn(r["ubp_id"], table)
        self.assertEqual(len(lr.EXACT_GRADES), 16)
        self.assertEqual(len(lr.NUMERIC_GRADES), 49)


class TestExactRows(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.exact = lr.exact_regrade()

    def test_census(self):
        self.assertEqual(self.exact["census"],
                         {"structural": 8, "overclaimed": 2, "definitional": 3,
                          "arithmetic": 2, "near-miss": 1})

    def test_r1_every_arithmetic_figure_reproduces(self):
        self.assertTrue(self.exact["arithmetic_reproduces"])

    def test_the_overclaims_fail_where_found(self):
        self.assertTrue(self.exact["overclaims_fail_as_found"])

    def test_the_evidence_column_was_boilerplate(self):
        # all sixteen rows of the supplied file carry one identical sentence
        self.assertTrue(self.exact["boilerplate_evidence"])

    def test_r2_every_cited_theorem_exists(self):
        for path, name in lr.lean_citations():
            text = (ROOT / "overlay" / "glm_lean" / path).read_text(
                encoding="utf-8")
            self.assertRegex(text, r"\btheorem\s+" + re.escape(name) + r"\b",
                             f"{name} in {path}")

    def test_structural_rows_cite_lean(self):
        for g in self.exact["rows"]:
            if g["class"] in ("structural", "overclaimed"):
                self.assertTrue(g["lean"], g["id"])


class TestDecoder(unittest.TestCase):

    def test_enumerators(self):
        e = lr.coset_enumerators()
        self.assertTrue(e["leaders_agree"])
        self.assertTrue(e["closes_to_binomial"])

    def test_outcome_table(self):
        d = lr.decoder_outcomes()
        self.assertTrue(d["exact"])
        # GLM.LawRegister.unique_leader_iff, wt_four_refused, wt_five_coset_three
        self.assertTrue(d["right_iff_le_three"])
        self.assertTrue(d["weight_four_all_refused"])
        self.assertTrue(d["weight_five_all_wrong"])
        six = d["by_weight"][6]
        self.assertEqual(six["right"], 0)
        self.assertEqual(six["refused"] + six["wrong"], 134596)

    def test_storage_hardened_is_refuted(self):
        s = lr.storage_hardened()
        self.assertFalse(s["holds"])
        self.assertEqual(s["not_right_decimal"], "0.005321")
        self.assertEqual(s["wrong_decimal"], "0.0005925")

    def test_refusal_price(self):
        rows = {r["p"]: r for r in lr.refusal_price()}
        self.assertEqual(rows["3/100"]["wrong_withheld"], "0.0039484")
        self.assertEqual(rows["3/100"]["right_given_up"], "0.0007800")
        for r in rows.values():
            self.assertGreaterEqual(Fraction(r["withheld_per_given_up"]), 5)

    def test_probabilities_sum_to_one(self):
        for p in (Fraction(1, 100), Fraction(1, 7)):
            probs = lr.outcome_probabilities(p)
            self.assertEqual(probs["right"] + probs["refused"] + probs["wrong"], 1)


class TestStatistics(unittest.TestCase):

    def test_seven_moments_agree_and_the_eighth_does_not(self):
        # GLM.LawRegister.moment_agree, moment_eight_differs
        m = lr.moment_census()
        self.assertEqual(m["agree_through"], 7)
        self.assertFalse(m["rows"][8]["equal"])

    def test_the_two_nrci_means_differ(self):
        # GLM.LawRegister.nrci_means_differ
        n = lr.nrci_means()
        self.assertFalse(n["equal"])
        self.assertTrue(n["agree_as_quoted"])
        self.assertEqual(n["difference"], "0.000000023478")

    def test_noise_floor(self):
        # GLM.LawRegister.nrci_floor
        n = lr.nrci_means()
        self.assertEqual(n["floor_w24"], "0.516736")
        self.assertTrue(n["floor_above_042"])

    def test_and_or_are_not_code_operations(self):
        c = lr.closure_census()
        self.assertEqual(c["octad_pairs"], 287661)
        self.assertEqual(c["and_codeword"], 11385)   # the disjoint pairs only
        self.assertEqual(c["or_closed_fraction"], Fraction(15, 379))

    def test_descent_claim_is_refuted(self):
        d = lr.descent_check()
        self.assertFalse(d["holds"])
        self.assertEqual(d["trapped"], 792)


class TestNumericRows(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.numeric = lr.numeric_regrade()

    def test_r7_census(self):
        self.assertEqual(self.numeric["census"],
                         {"external": 19, "unit-dependent": 7,
                          "not-a-measurement": 3, "KB-internal": 14,
                          "restatement": 1, "duplicate": 4, "structural": 1})

    def test_r8_admissions(self):
        self.assertEqual(self.numeric["formulas_tested"], 21)
        self.assertEqual(self.numeric["admitted"], ["lepton", "muon"])

    def test_decoys_are_calibrated(self):
        for key, c in self.numeric["decoy_controls"].items():
            self.assertLessEqual(c["rate"], Fraction(1, 20), key)

    def test_admitted_formulas_miss_the_measurement(self):
        for key, sigma in self.numeric["sigma_distance"].items():
            self.assertGreater(sigma, 100, key)

    def test_look_elsewhere_on_a_fresh_claim(self):
        # an exact claim has coverage zero and is admitted
        r = lr.look_elsewhere(lambda a: Fraction(a, 7), {"a": range(1, 25)},
                              {"a": 3}, Fraction(3, 7))
        self.assertEqual(r["p"], 0)
        self.assertTrue(r["admitted"])
        # a claim at 1% error from a dense template is refused
        r = lr.look_elsewhere(lambda a, b: Fraction(a, b),
                              {"a": range(1, 49), "b": range(1, 49)},
                              {"a": 1, "b": 3}, Fraction(1, 3) * Fraction(101, 100))
        self.assertFalse(r["admitted"])


class TestIntegration(unittest.TestCase):

    def test_r9_every_non_external_row_is_refused_by_name(self):
        for law, (category, _) in lr.NUMERIC_GRADES.items():
            if category == "external":
                continue
            v = lr.admit(law)
            self.assertEqual(v["verdict"], "refused", law)
            if category != "structural":
                self.assertTrue(v["reason"].startswith(category), law)

    def test_marks(self):
        self.assertTrue(all(lr.law_register_report()["marks"].values()))

    def test_toolbox(self):
        tool = tb.tool_named("law register")
        self.assertIsNotNone(tool)
        r = tool.run("LAW_FOURTH_FLIP_001")
        self.assertTrue(r.ok)
        self.assertIn("structural", r.text)
        self.assertFalse(tool.run("LAW_NOT_A_LAW").ok)


if __name__ == "__main__":
    unittest.main()
