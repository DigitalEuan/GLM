"""Tests for ``glm_universal.corpus.navigate`` -- one question in, and
everything that bears on it out.

*Created 13 November 2026 (platform round).*

The navigator is checked against a small injected index and a small injected
shortlist, so every figure here is the test's own and no test depends on the
corpus growing or shrinking.
"""
from __future__ import annotations

import json
import unittest
from fractions import Fraction

from glm_universal.corpus import address as ad
from glm_universal.corpus import navigate as nv
from glm_universal.corpus import study_index as si


def _manifest(sid, title, question="", verdict="Yes.", code=(), test=(),
              lean=(), held=(), missing=(), preds=(), phase=1):
    return {
        "schema": "glm-study-manifest/v1", "id": sid, "phase": phase,
        "title": title, "status": "closed",
        "question": question or title, "verdict": verdict,
        "deciding_figure": "", "recomputed_by": "", "faculty": "unknown",
        "predecessors": list(preds), "related": [], "directives": [],
        "marks": {"declared": [], "met": [], "missed": [], "amended": []},
        "follow_ups": [],
        "sections": [{"heading": "Tier 0 — the coarse read", "anchor": "t0"}],
        "file_refs": {
            "prose": sid + ".md", "code": list(code), "test": list(test),
            "lean": list(lean), "lean_held": list(held),
            "lean_missing": list(missing), "missing": [], "wheel": [],
        },
    }


MANIFESTS = {
    "SHELL_STUDY": _manifest(
        "SHELL_STUDY", "Every shell counted from the lattice",
        question="Can every shell be counted?", code=("reasoning/shells.py",),
        test=("test_shells.py",), lean=("Shells",), preds=()),
    "SHELL_COUNT_STUDY": _manifest(
        "SHELL_COUNT_STUDY", "The shell count proved",
        question="Is the count proved?", code=("reasoning/shells.py",),
        test=("test_shell_count.py",), lean=("ShellCount",),
        missing=("ShellMissing",), preds=("SHELL_STUDY",), phase=2),
    "CORPUS_STUDY": _manifest(
        "CORPUS_STUDY", "The corpus read finely",
        question="How is the corpus read?", code=("corpus/read.py",),
        test=("test_corpus.py",), lean=(), phase=3),
}


def _shortlist(question, feature_radius=2):
    return {
        "answered": True, "complete": True, "corpus_units": 3,
        "guarantee": "GLM.Retrieval.complete_shortlist",
        "units": (
            ad.Found(name="a", document="studies/SHELL_STUDY.md",
                     heading="3. The count", squared_distance=1,
                     overlap=Fraction(1, 4)),
            ad.Found(name="b", document="studies/CORPUS_STUDY.md",
                     heading="6. Files", squared_distance=2,
                     overlap=Fraction(0)),
        ),
    }


class TestBearingStudies(unittest.TestCase):
    def setUp(self):
        self.index = si.StudyIndex(MANIFESTS)

    def _nav(self, question, **kwargs):
        return nv.navigate(question, index=self.index, shortlist=_shortlist,
                           **kwargs)

    def test_a_title_that_claims_the_question_is_flagged(self):
        nav = self._nav("shell count")
        self.assertIn("SHELL_COUNT_STUDY", nav["covering"])
        card = next(c for c in nav["studies"] if c["id"] == "SHELL_COUNT_STUDY")
        self.assertTrue(card["covering"])
        self.assertEqual(card["shared"], "1")   # 2/2, kept exact
        self.assertEqual(card["shared_words"], 2)

    def test_counting_fields_rather_than_words_does_not_make_a_claim(self):
        # ``corpus`` is in one study's id but not its title, so it bears on
        # the question without claiming it.
        nav = self._nav("corpus")
        self.assertEqual(nav["covering"], [])

    def test_covering_studies_are_shown_first(self):
        nav = self._nav("shell count", study_limit=3)
        ids = [c["id"] for c in nav["studies"]]
        covering = [i for i in ids if i in nav["covering"]]
        self.assertEqual(ids[:len(covering)], covering)

    def test_the_limit_is_the_number_shown_not_the_number_matched(self):
        nav = self._nav("shell", study_limit=1)
        self.assertEqual(len(nav["studies"]), 1)
        self.assertGreaterEqual(nav["studies_matched"], 2)

    def test_a_question_of_stop_words_only_answers_nothing(self):
        nav = self._nav("the of which")
        self.assertEqual(nav["studies"], [])
        self.assertEqual(nav["covering"], [])

    def test_marks_and_neighbours_are_carried(self):
        nav = self._nav("shell count")
        card = next(c for c in nav["studies"] if c["id"] == "SHELL_COUNT_STUDY")
        self.assertEqual(card["predecessors"], ["SHELL_STUDY"])
        self.assertEqual(card["successors"], [])
        self.assertIn("met", card["marks"])


class TestSections(unittest.TestCase):
    def setUp(self):
        self.index = si.StudyIndex(MANIFESTS)

    def test_sections_that_share_a_word_come_first(self):
        nav = nv.navigate("shell count", index=self.index,
                          shortlist=_shortlist)
        self.assertEqual(nav["sections"][0]["document"],
                         "studies/SHELL_STUDY.md")
        self.assertEqual(nav["sections_shared"], 1)
        self.assertEqual(nav["sections_without_share"], 1)

    def test_an_absent_address_book_is_said_rather_than_guessed(self):
        def missing(question, feature_radius=2):
            return {"answered": False, "units": (), "corpus_units": 0,
                    "guarantee": ""}
        nav = nv.navigate("shell", index=self.index, shortlist=missing)
        self.assertFalse(nav["sections_complete"])
        self.assertIn("address book does not describe",
                      nv.render(nav))


class TestReuse(unittest.TestCase):
    def setUp(self):
        self.index = si.StudyIndex(MANIFESTS)

    def test_the_files_the_nearest_studies_name_are_reused_once_each(self):
        nav = nv.navigate("shell count", index=self.index,
                          shortlist=_shortlist)
        self.assertEqual(nav["reuse"]["code"], ["reasoning/shells.py"])
        self.assertIn("test_shells.py", nav["reuse"]["test"])
        self.assertIn("test_shell_count.py", nav["reuse"]["test"])
        self.assertNotIn("prose", nav["reuse"])

    def test_a_lean_file_a_study_is_owed_is_reported(self):
        nav = nv.navigate("shell count", index=self.index,
                          shortlist=_shortlist)
        self.assertIn({"study": "SHELL_COUNT_STUDY", "lean": "ShellMissing",
                       "kind": "lean_missing"}, nav["gaps"])


class TestExactness(unittest.TestCase):
    def test_no_float_anywhere_in_the_navigation(self):
        nav = nv.navigate("shell count", index=si.StudyIndex(MANIFESTS),
                          shortlist=_shortlist)

        def walk(value):
            if isinstance(value, float):  # pragma: no cover - a failure
                raise AssertionError(f"float in the navigation: {value!r}")
            if isinstance(value, dict):
                for item in value.values():
                    walk(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    walk(item)

        walk(nav)
        json.dumps(nav)  # it is serialisable as it stands

    def test_the_render_names_the_studies_and_the_files(self):
        nav = nv.navigate("shell count", index=si.StudyIndex(MANIFESTS),
                          shortlist=_shortlist)
        text = nv.render(nav)
        self.assertIn("SHELL_COUNT_STUDY", text)
        self.assertIn("reasoning/shells.py", text)
        self.assertIn("ALREADY CLAIMED BY", text)
        self.assertIn("GLM.Retrieval.complete_shortlist", text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
