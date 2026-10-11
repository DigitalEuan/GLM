"""The document tree as a third native book (Phase 102), on the frozen corpus
declared in ``studies/DOCUMENT_TREE_STUDY.md``.

The census figures are read from the stored measurement when it is current
(``tools document-tree --write``); the 60-query spread is re-taken from the
snapshot here and must equal the stored one (mark F1).
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.reasoning import document_tree as dtr
from glm_universal.substrate.mog import GOLAY

ROOT = Path(__file__).resolve().parents[3]
LEAN = ROOT / "overlay" / "glm_lean" / dtr.LEAN_FILE

_REPORT = None


def report():
    global _REPORT
    if _REPORT is None:
        _REPORT = dtr.current() or dtr.document_tree_report()
    return _REPORT


class TestTheSnapshot(unittest.TestCase):

    def test_intact_and_exact(self):
        state = dtr.frozen_state()
        self.assertTrue(state["present"])
        self.assertTrue(state["intact"])
        self.assertEqual(1506, state["units"])
        self.assertEqual({"addresses": 3012, "failures": 0},
                         dtr.readback_check())

    def test_every_unit_has_a_relative(self):
        units = dtr.frozen()["units"]
        counts = {}
        for u in units:
            counts[u["document"]] = counts.get(u["document"], 0) + 1
        self.assertTrue(all(counts[u["document"]] >= 2 for u in units))

    def test_the_stored_measurement_is_current(self):
        self.assertEqual("fresh", dtr.state()["verdict"])


class TestTheWords(unittest.TestCase):

    def test_place_message(self):
        self.assertEqual(0, dtr.place_message(0, 1))
        self.assertEqual(1 + 8 * 1, dtr.place_message(1, 3))
        self.assertEqual(7 + 8 * 7, dtr.place_message(20, 40))
        with self.assertRaises(ValueError):
            dtr.place_message(3, 3)

    def test_every_place_word_is_a_codeword(self):
        for n in range(1, 20):
            for i in range(n):
                self.assertTrue(GOLAY.is_codeword(dtr.place_word(i, n)))

    def test_distinct_positions_are_eight_apart(self):
        words = {dtr.place_word(i, n) for n in range(1, 20) for i in range(n)}
        self.assertEqual(64, len(words))
        least = min(dtr.hamming(a, b) for a in words for b in words if a != b)
        self.assertEqual(8, least)

    def test_the_books(self):
        books = dtr.book_check()
        self.assertEqual(0, books["non_codewords"])
        self.assertTrue(books["path_injective"])
        self.assertEqual(136, books["documents"])
        self.assertEqual(61, books["place_words"])
        # the one three-section document's three place words name it: F2 not met
        self.assertEqual(3, books["place_words_naming_one_document"])
        self.assertFalse(books["met"])


class TestTheMeasurement(unittest.TestCase):

    def test_the_spread_re_taken_equals_the_stored_one(self):
        stored = report()["sample"]
        live = dtr.tally(dtr.sample_names())
        for rid, _ in dtr.RANKINGS:
            with self.subTest(ranking=rid):
                self.assertEqual(stored[rid], live[rid])

    def test_the_census(self):
        census = report()["census"]
        self.assertEqual(1506, census["path_first"]["hit@1"])
        self.assertEqual(323, census["lexical_raw"]["hit@5"])
        self.assertEqual(414, census["lexical_raw"]["relatives@5"])
        self.assertEqual(324, census["lexical_native3"]["hit@5"])
        self.assertEqual(413, census["lexical_native3"]["relatives@5"])
        self.assertEqual(census["lexical_native2"], census["lexical_native3"])
        self.assertEqual(census["lexical_native3"], census["lexical_raw3"])
        self.assertEqual(319, census["lexical_place2"]["hit@5"])
        self.assertEqual(325, census["path3"]["hit@5"])

    def test_the_ceiling(self):
        ties = report()["ties"]
        self.assertEqual(30, ties["tie_at_boundary"])
        self.assertEqual(7, ties["top5_changed_by_place"])

    def test_the_discordances(self):
        d = report()["discordances"]
        self.assertEqual((7, 6, Fraction(1)),
                         (d["native3_vs_raw"]["first_only"],
                          d["native3_vs_raw"]["second_only"],
                          d["native3_vs_raw"]["sign_test"]))
        self.assertEqual((3, 7, Fraction(11, 32)),
                         (d["place2_vs_raw"]["first_only"],
                          d["place2_vs_raw"]["second_only"],
                          d["place2_vs_raw"]["sign_test"]))
        self.assertEqual((0, 0), (d["native3_vs_native2"]["first_only"],
                                  d["native3_vs_native2"]["second_only"]))
        self.assertEqual((1, 0), (d["path3_vs_native2"]["first_only"],
                                  d["path3_vs_native2"]["second_only"]))

    def test_the_marks(self):
        outcomes = {k: v["outcome"] for k, v in report()["marks"].items()}
        self.assertEqual({"F1": "met", "F2": "not met", "F3": "met",
                          "F4": "not met", "F5": "met", "F6": "not met"},
                         outcomes)


class TestTheLeanFile(unittest.TestCase):

    def test_names_the_theorems(self):
        text = LEAN.read_text(encoding="utf-8")
        for name in ("separating_key_head", "injective_word_separates",
                     "map_eq_of_perm_sorted", "take_perm_of_gap",
                     "census_signs"):
            with self.subTest(name=name):
                self.assertIn(f"theorem {name}", text)
        self.assertNotIn("sorry", text)


if __name__ == "__main__":
    unittest.main()
