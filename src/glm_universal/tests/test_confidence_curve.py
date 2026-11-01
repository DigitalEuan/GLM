"""Tests for the corpus confidence curve (Phase 168,
``studies/CONFIDENCE_CURVE_STUDY.md``): :mod:`glm_universal.knowledge.confidence_curve`.

Fast and synthetic: the guards are scored on a hand-made position table, the
position table on a hand-counted model, the quality description on a define
answer of a corpus built in memory, and the measurement's compute runs once on
a few invented documents, so the real corpus is never loaded, no measurement
is re-taken and nothing is written.

*Created 31 October 2026 (repository check).*

*Reconstructed 31 October 2026 (repository check): the original
tests/test_confidence_curve.py (named by MASTER_PLAN.md Phase 168) was lost in
the October 2026 reorganisation; rebuilt from
studies/CONFIDENCE_CURVE_STUDY.md (§§1-4) and the reconstructed module.*
"""
from __future__ import annotations

import unittest
from collections import Counter
from fractions import Fraction

from glm_universal import integrity
from glm_universal.knowledge import answer as ans
from glm_universal.knowledge import confidence_curve as ccv
from glm_universal.knowledge import model as mdl
from glm_universal.knowledge import reader as rd


def _md(path: str, paragraphs) -> rd.Document:
    doc = rd.read_bytes(path, "\n\n".join(paragraphs).encode("utf-8"))
    assert doc is not None, path
    return doc


#: A position table by hand: ``(total, top, right)`` -> positions, 40 positions.
TABLE = {"positions": 40,
         "guarded": Counter({(5, 4, True): 10, (5, 4, False): 2, (1, 1, True): 3,
                             (10, 3, False): 5})}


class TestConfidenceCurve(unittest.TestCase):

    def test_folds_by_path_digest(self):
        for path in ("STATUS.md", "studies/A.md", "src/x.py"):
            fold = ccv.fold_of(path)
            self.assertIn(fold, range(ccv.FOLDS))
            self.assertEqual(fold, int(integrity.sha256_hex(path.encode("utf-8")), 16) % 5)
        self.assertEqual((ccv.HELD_FOLD, ccv.CALIBRATION_FOLD), (4, 3))

    def test_guard_grid(self):
        self.assertEqual(len(ccv.GUARDS), 143)
        self.assertIn((2, Fraction(0)), ccv.GUARDS)          # Phase 154's guarded reading
        self.assertIn((3, Fraction(1, 2)), ccv.GUARDS)       # its majority guard
        self.assertTrue(all(isinstance(s, Fraction) for _, s in ccv.GUARDS))

    def test_guard_score(self):
        everything = ccv.guard_score(TABLE, (1, Fraction(0)))
        self.assertEqual((everything["answered"], everything["right"]), (20, 13))
        half = ccv.guard_score(TABLE, (2, Fraction(1, 2)))
        self.assertEqual((half["answered"], half["right"]), (12, 10))
        self.assertEqual((half["precision"], half["coverage"]), (Fraction(5, 6), Fraction(3, 10)))
        # the winner must hold MORE than the share: 4 of 5 is not more than 4/5
        self.assertEqual(ccv.guard_score(TABLE, (5, Fraction(4, 5)))["answered"], 0)

    def test_choose(self):
        # greatest coverage at the bar; ties to the higher precision, then the
        # smaller c, then the smaller s
        self.assertEqual(ccv.choose(TABLE, Fraction(5, 6)), (1, Fraction(1, 3)))
        self.assertEqual(ccv.choose(TABLE, Fraction(1)), (1, Fraction(4, 5)))
        self.assertIsNone(ccv.choose(TABLE, Fraction(2)))

    def test_position_table(self):
        model = mdl.Model()
        for toks in (("a", "b", "c"), ("a", "b", "c"), ("a", "b", "d")):
            model.add_sentence(toks, with_window=False)
        table = ccv.position_table(model, [("a", "b", "c"), ("a", "x")])
        self.assertEqual(table["positions"], 4 + 3)
        # a b c </s> all right; a right, x wrong, </s> after x unseen
        self.assertEqual(table["unguarded_right"], 5)
        self.assertEqual(table["candidate_covered"], 6)
        self.assertEqual(table["candidate_hits"], 5)
        self.assertEqual(sum(table["guarded"].values()), 6)
        self.assertEqual(table["guarded"][(3, 2, True)], 1)     # c after "a b": 2 of 3
        self.assertEqual(table["guarded"][(3, 3, False)], 1)    # x after "<s> a"

    def test_quality(self):
        docs = (_md("notes/a.md", ["The widget frame is a steel box for gears.",
                                   "A widget frame holds steel gears.",
                                   "Each widget frame keeps steel gears apart."]),)
        knowledge = mdl.build(docs, digest="synthetic-confidence-curve")
        got = ccv.quality(ans.define("widget frame", knowledge))
        self.assertTrue(got["described"])
        for field in ("witness", "address", "pattern", "strength", "source", "support",
                      "grade"):
            self.assertIn(field, got)
        self.assertEqual(got["grade"], ans.grade_of(got["strength"], got["support"]))
        self.assertEqual(ccv.quality(ans.define("zyxwv", knowledge)), {"described": False})

    def test_compute_shape(self):
        trees = ("oak", "pine", "elm", "ash", "birch", "maple", "cedar", "larch")
        docs = tuple(_md(f"notes/{t}.md", [f"There are {n} gears in the {t} box."
                                          for n in ("one", "two", "three", "four")])
                     for t in trees)
        got = ccv.compute(mdl.build(docs, digest="synthetic-confidence-curve-folds"))
        self.assertEqual(sorted(got["marks"]), ["C1", "C2", "C3", "C4", "C5", "C6", "D1", "D2"])
        self.assertEqual(sum(got["folds"]["sizes"]), len(docs))
        self.assertEqual(got["met"], sum(got["marks"].values()))
        for name in ("sure", "balanced"):
            mode = got["modes"][name]
            if not mode["chosen"]:
                self.assertFalse(got["marks"]["C5"])

    def test_report_is_honest(self):
        report = ccv.confidence_curve_report()
        state = ccv.state()
        if report.get("available"):
            self.assertTrue(state["fresh"])
        else:
            self.assertIn(state["verdict"], ("absent", "stale"))
            self.assertIn("--write", report["reason"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
