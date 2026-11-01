"""Tests for ``glm_universal.corpus.study_index`` -- the studies as
something the GLM can reason over, and ``answer_study_query``.

*Created 31 October 2026 (repository check of the YAML study system).*
"""
from __future__ import annotations

import unittest

try:
    import yaml as _yaml
except ImportError:  # pragma: no cover
    _yaml = None

from glm_universal.corpus import study_index as si


def _m(sid, phase, title, preds=(), code=(), test=(), lean=(), held=(),
       missing=(), status="closed", marks=None, follow=(), directives=(),
       question="", verdict="", figure=""):
    return {
        "schema": "glm-study-manifest/v1", "id": sid, "phase": phase,
        "title": title, "status": status, "question": question or title,
        "verdict": verdict or "Yes.", "deciding_figure": figure,
        "recomputed_by": "", "faculty": "unknown",
        "predecessors": list(preds), "related": [],
        "directives": list(directives),
        "marks": marks or {"declared": [], "met": [], "missed": [],
                           "amended": []},
        "follow_ups": list(follow),
        "sections": [{"heading": "Tier 0 — the coarse read",
                      "anchor": "tier-0"}],
        "file_refs": {"prose": sid + ".md", "code": list(code),
                      "test": list(test), "lean": list(lean),
                      "lean_held": list(held), "lean_missing": list(missing),
                      "missing": []},
    }


SMALL = {
    "GOLAY_CODE_STUDY": _m("GOLAY_CODE_STUDY", 10, "The Golay code counted",
                           code=["reasoning/golay.py"], lean=["GolayCode"],
                           test=["test_golay.py"], directives=["D7"]),
    "LEECH_SHELLS_STUDY": _m("LEECH_SHELLS_STUDY", 20,
                             "The Leech shells from the Golay census",
                             preds=["GOLAY_CODE_STUDY"],
                             code=["reasoning/leech_shells.py"],
                             missing=["LeechShells"],
                             marks={"declared": ["L1", "S1"], "met": ["S1"],
                                    "missed": ["L1"], "amended": []}),
    "LEECH_SHELL_COUNT_STUDY": _m("LEECH_SHELL_COUNT_STUDY", 30,
                                  "Every Leech shell, counted and proved",
                                  preds=["LEECH_SHELLS_STUDY"],
                                  lean=["LeechShellCount"],
                                  held=["LeechShellCount"]),
    "DIALOGUE_STUDY": _m("DIALOGUE_STUDY", 40, "An open dialogue",
                         status="open",
                         follow=[{"question": "a reply after two turns",
                                  "status": "open"}]),
}


class TestSmallIndex(unittest.TestCase):

    def setUp(self):
        self.idx = si.StudyIndex(SMALL)

    def test_resolve(self):
        for text in ("LEECH_SHELLS_STUDY", "leech shells", "the Leech shells "
                     "study", "studies/LEECH_SHELLS_STUDY.md", "Leech-Shells"):
            self.assertEqual(self.idx.resolve(text), "LEECH_SHELLS_STUDY", text)
        self.assertIsNone(self.idx.resolve("no such thing"))

    def test_bearing_on_ranks_title_first(self):
        hits = self.idx.bearing_on("the Golay code")
        self.assertEqual(hits[0].sid, "GOLAY_CODE_STUDY")
        self.assertEqual(hits[0].matched, hits[0].of)
        self.assertEqual(self.idx.bearing_on("of the"), [])

    def test_files(self):
        self.assertEqual(self.idx.by_code("reasoning/leech_shells.py"),
                         ["LEECH_SHELLS_STUDY"])
        self.assertEqual(self.idx.by_code("leech_shells"),
                         ["LEECH_SHELLS_STUDY"])
        self.assertEqual(self.idx.by_code("glm_universal.reasoning.golay"),
                         ["GOLAY_CODE_STUDY"])
        self.assertEqual(self.idx.by_lean("LeechShells.lean"),
                         ["LEECH_SHELLS_STUDY"])
        self.assertEqual(self.idx.by_lean("RequestProject.GLM.LeechShellCount"),
                         ["LEECH_SHELL_COUNT_STUDY"])
        self.assertEqual(self.idx.by_test("test_golay"), ["GOLAY_CODE_STUDY"])

    def test_graph(self):
        self.assertEqual(self.idx.predecessors("LEECH_SHELL_COUNT_STUDY"),
                         ["LEECH_SHELLS_STUDY"])
        self.assertEqual(self.idx.ancestors("LEECH_SHELL_COUNT_STUDY"),
                         ["GOLAY_CODE_STUDY", "LEECH_SHELLS_STUDY"])
        self.assertEqual(self.idx.successors("GOLAY_CODE_STUDY"),
                         ["LEECH_SHELLS_STUDY"])
        self.assertEqual(self.idx.descendants("GOLAY_CODE_STUDY"),
                         ["LEECH_SHELLS_STUDY", "LEECH_SHELL_COUNT_STUDY"])

    def test_gaps_and_open(self):
        self.assertEqual(self.idx.lean_gaps(),
                         [("LEECH_SHELLS_STUDY", "LeechShells", "missing"),
                          ("LEECH_SHELL_COUNT_STUDY", "LeechShellCount",
                           "held")])
        self.assertEqual(self.idx.open_studies(),
                         [("DIALOGUE_STUDY", "status open")])
        self.assertEqual(self.idx.by_directive("d7"), ["GOLAY_CODE_STUDY"])
        self.assertEqual(self.idx.by_phase(20), ["LEECH_SHELLS_STUDY"])


class TestAnswerStudyQuery(unittest.TestCase):

    def setUp(self):
        self.idx = si.StudyIndex(SMALL)

    def ask(self, text):
        return si.answer_study_query(text, self.idx)

    def test_questions(self):
        cases = [
            ("which studies bear on the Golay code", 0, "GOLAY_CODE_STUDY"),
            ("golay", 0, "GOLAY_CODE_STUDY"),
            ("study LEECH_SHELLS_STUDY", 0, "Builds on: GOLAY_CODE_STUDY"),
            ("LEECH_SHELLS_STUDY", 0, "Lean missing: LeechShells"),
            ("what does LEECH_SHELL_COUNT_STUDY depend on", 0,
             "LEECH_SHELLS_STUDY"),
            ("what builds on GOLAY_CODE_STUDY", 0, "LEECH_SHELLS_STUDY"),
            ("marks of LEECH_SHELLS_STUDY", 0, "missed: L1"),
            ("follow-ups of DIALOGUE_STUDY", 0, "a reply after two turns"),
            ("which studies have a missing or held Lean file", 0,
             "LeechShellCount.lean (held)"),
            ("which studies have a held Lean file", 0, "LeechShellCount"),
            ("open studies", 0, "DIALOGUE_STUDY"),
            ("which studies cite reasoning/leech_shells.py", 0,
             "LEECH_SHELLS_STUDY"),
            ("LeechShellCount.lean", 0, "LEECH_SHELL_COUNT_STUDY"),
            ("test_golay.py", 0, "GOLAY_CODE_STUDY"),
            ("directive D7", 0, "GOLAY_CODE_STUDY"),
            ("phase 30", 0, "LEECH_SHELL_COUNT_STUDY"),
        ]
        for text, code, needle in cases:
            got_code, reply = self.ask(text)
            self.assertEqual(got_code, code, (text, reply))
            self.assertIn(needle, reply, text)

    def test_refusals_are_said(self):
        code, reply = self.ask("study NO_SUCH_STUDY")
        self.assertEqual(code, 1)
        self.assertIn("no study is named", reply)
        code, reply = self.ask("which studies bear on thermodynamics")
        self.assertEqual(code, 1)
        self.assertIn("no study manifest bears on", reply)
        code, reply = self.ask("what does NO_SUCH_STUDY depend on")
        self.assertEqual(code, 1)
        self.assertEqual(self.ask("")[0], 2)
        self.assertEqual(self.ask("marks of DIALOGUE_STUDY")[0], 1)
        self.assertEqual(self.ask("what builds on DIALOGUE_STUDY"),
                         (0, "no later study builds on DIALOGUE_STUDY"))


@unittest.skipUnless(_yaml is not None, "PyYAML not installed")
class TestTheRepository(unittest.TestCase):

    def test_owner_questions(self):
        idx = si.study_index()
        self.assertGreater(len(idx.ids), 150)
        code, reply = si.answer_study_query(
            "which studies bear on the Golay code", idx)
        self.assertEqual(code, 0)
        self.assertIn("Golay", reply)
        code, reply = si.answer_study_query("study LORENTZIAN_MAJORITY_STUDY",
                                            idx)
        self.assertEqual(code, 0)
        self.assertIn("Phase 184", reply)
        self.assertIn("LorentzianMajority", reply)   # its Lean file, missing
        if idx.get("FOLD_MACHINE_STUDY") is not None:
            code, reply = si.answer_study_query(
                "what does FOLD_MACHINE_STUDY depend on", idx)
            self.assertEqual(code, 0)
            self.assertIn("FOLD_MACHINE_STUDY", reply)

    def test_cli(self):
        self.assertEqual(si.main(["golay"]), 0)
        self.assertEqual(si.main(["study", "NO_SUCH_STUDY"]), 1)


if __name__ == "__main__":
    unittest.main()
