"""Tests for the corpus source tiers (Phase 162, ``studies/SOURCE_TIERS_STUDY.md``):
:mod:`glm_universal.knowledge.source_tiers`.

Fast and synthetic: the tiers are read from invented paths, the policies are
scored on hand-counted models, and the measurement's compute runs once on a
corpus of fourteen invented documents built in memory, so the real corpus is
never loaded, no measurement is re-taken and nothing is written.

*Created 31 October 2026 (repository check).*

*Reconstructed 31 October 2026 (repository check): the original
tests/test_source_tiers.py (8 tests, named by MASTER_PLAN.md Phase 162 and
studies/SOURCE_TIERS_STUDY.md §7; recorded missing in its §7.6) was lost in
the October 2026 reorganisation; rebuilt from studies/SOURCE_TIERS_STUDY.md
(§§1-6) and the reconstructed module.*
"""
from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.knowledge import model as mdl
from glm_universal.knowledge import reader as rd
from glm_universal.knowledge import source_tiers as stt


def _md(path: str, paragraphs) -> rd.Document:
    doc = rd.read_bytes(path, "\n\n".join(paragraphs).encode("utf-8"))
    assert doc is not None, path
    return doc


NUMBERS = tuple("one two three four five six seven eight nine ten eleven twelve".split())
TREES = tuple("oak pine elm ash birch maple cedar larch rowan alder hazel willow".split())


def _documents():
    docs = []
    for i, tree in enumerate(TREES):
        folder = ("notes", "studies", "source_material", "archive")[i % 4]
        lines = [f"There are {n} gears in the {tree} box." for n in NUMBERS]
        lines.append(f"The {tree} ledger lists every gear by number.")
        side = "backwards" if folder in ("source_material", "archive") else "forwards"
        lines.append(f"The old ledger says the gears turn {side}.")
        docs.append(_md(f"{folder}/{tree}.md", lines))
    docs.append(rd.read_bytes("src/pkg/mod.py", b'"""The module counts gears in the oak box."""\n'))
    docs.append(rd.read_bytes("lean/Gears.lean",
                              b"/-- The lemma counts gears in the pine box. -/\n"
                              b"theorem x : True := trivial\n"))
    return tuple(docs)


DOCS = _documents()


def _model(*sentences) -> mdl.Model:
    model = mdl.Model()
    for toks in sentences:
        model.add_sentence(tuple(toks.split()), with_window=False)
    return model


class TestSourceTiers(unittest.TestCase):

    def test_tier_of(self):
        cases = {"STATUS.md": "core", "docs/guide.txt": "core",
                 "src/glm_universal/tools.py": "code", "src/lean/GLM/A.lean": "lean",
                 "studies/A.md": "studies", "src/x/_data/m.json": "studies",
                 "data/table.csv": "studies", "source_material/x.md": "supplied",
                 "archive/old.py": "supplied", "source_material/GLM-main.zip/a/b.py": "supplied"}
        for path, tier in cases.items():
            self.assertEqual(stt.tier_of(path), tier, path)
            self.assertIn(stt.tier_of(path), stt.TIERS)

    def test_slices(self):
        self.assertEqual(stt.SLICES, ("whole", "written", "supplied"))
        for path in ("STATUS.md", "archive/old.py"):
            self.assertTrue(stt.in_slice(path, "whole"))
            # written and supplied partition the corpus
            self.assertNotEqual(stt.in_slice(path, "written"), stt.in_slice(path, "supplied"))
        self.assertTrue(stt.in_slice("archive/old.py", "supplied"))

    def test_census(self):
        got = stt.census(DOCS)
        self.assertEqual({t: r["documents"] for t, r in got["tiers"].items()},
                         {"core": 3, "code": 1, "lean": 1, "studies": 3, "supplied": 6})
        self.assertEqual(got["total"]["documents"], len(DOCS))
        self.assertEqual(got["total"]["sentences"],
                         sum(r["sentences"] for r in got["tiers"].values()))
        self.assertEqual(got["tiers"]["core"]["sentences"], 3 * 14)

    def test_majority_guard(self):
        self.assertIsNone(stt._majority(None))
        self.assertIsNone(stt._majority({"a": 2}))                     # seen twice
        self.assertIsNone(stt._majority({"a": 2, "b": 2}))             # a tie
        self.assertIsNone(stt._majority({"a": 3, "b": 2, "c": 1}))     # not more than half
        self.assertEqual(stt._majority({"a": 2, "b": 1}), "a")
        self.assertEqual(stt._majority({"a": 2}, support=3), "a")      # support given apart

    def test_policies_hand_counted(self):
        written = _model("x y w", "x y w")
        supplied = _model("x y s", "x y s", "x y s")
        whole = written.merge(supplied)
        got = stt.guarded_scores({"whole": whole, "written": written, "supplied": supplied},
                                 [("x", "y", "w")])
        self.assertEqual(got["whole"], {"answered": 3, "right": 2})     # s wins after "x y"
        self.assertEqual(got["excluded"], {"answered": 0, "right": 0})  # written seen twice only
        self.assertEqual(got["downweighted"], {"answered": 4, "right": 4})
        self.assertEqual(got["downweighted_unweighted"], {"answered": 3, "right": 3})
        # confirm_witness: an answer the written tier never counted is not confirmed
        self.assertEqual(got["confirmed"], {"answered": 2, "right": 2})

    def test_slice_knowledge(self):
        knowledge = mdl.build(DOCS, digest="synthetic-source-tiers")
        written = stt._slice_knowledge(knowledge, "written")
        self.assertTrue(all(stt.in_slice(s.document, "written") for s in written.sentences))
        self.assertEqual(len(written.sentences),
                         sum(len(d.sentences) for d in DOCS if stt.in_slice(d.path, "written")))
        for sid in written.sentence_ids("ledger"):
            self.assertIn("ledger", written.sentences[sid].tokens)

    def test_compute_is_honest_about_unmeasured_marks(self):
        got = stt.compute(mdl.build(DOCS, digest="synthetic-source-tiers"))
        self.assertEqual(sorted(got["marks"]),
                         ["L1", "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"])
        for mark in ("T1", "T3", "T6", "T7", "T8"):
            self.assertFalse(got["marks"][mark], mark)
            self.assertIn(mark, got["unmeasured"])
        if not got["lean"]["present"]:
            self.assertFalse(got["marks"]["L1"])
        self.assertEqual(got["met"], sum(got["marks"].values()))
        self.assertEqual(got["prediction"]["training_documents"]
                         + got["prediction"]["held_documents"], len(DOCS))
        for name in stt.SLICES:
            self.assertIn(name, got["prediction"]["by_slice"])
            self.assertIsInstance(got["words"][name]["share"], Fraction)

    def test_report_is_honest(self):
        report = stt.source_tiers_report()
        state = stt.state()
        if report.get("available"):
            self.assertTrue(state["fresh"])
        else:
            self.assertIn(state["verdict"], ("absent", "stale"))
            self.assertTrue(report["reasons"])
            self.assertIn("--write", report["reasons"][0])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
