"""Tests for the graded definitions and the word addresses (Phase 155,
``studies/CORPUS_DEFINITIONS_STUDY.md``): :mod:`glm_universal.knowledge.glossary`,
:mod:`~glm_universal.knowledge.word_address` and
:mod:`~glm_universal.knowledge.definitions_study`.

Fast and synthetic: a corpus of a few invented Markdown documents is read
with :func:`glm_universal.knowledge.reader.read_bytes` and counted with
:func:`glm_universal.knowledge.model.build`, and graded against a three-entry
glossary of its own, so the real corpus is never loaded, no measurement is
re-taken and nothing is written (a corpus built in memory keeps its address
book in memory).

*Created 31 October 2026 (repository check).*

*Reconstructed 31 October 2026 (repository check): the original
tests/test_corpus_definitions.py (18 tests, named by MASTER_PLAN.md Phase 155
and studies/CORPUS_DEFINITIONS_STUDY.md §6) was lost in the October 2026
reorganisation; rebuilt from studies/CORPUS_DEFINITIONS_STUDY.md (§§2.1-2.3,
5, 7) and the reconstructed modules.*
"""
from __future__ import annotations

import re
import unittest
from fractions import Fraction

from glm_universal import constants
from glm_universal.knowledge import answer as ans
from glm_universal.knowledge import definitions_study as cds
from glm_universal.knowledge import glossary as gl
from glm_universal.knowledge import model as mdl
from glm_universal.knowledge import reader as rd
from glm_universal.knowledge import study as cks
from glm_universal.knowledge import word_address as wa
from glm_universal.reasoning import lean_address as la


# ---------------------------------------------------------------------------
#  A synthetic corpus and its glossary
# ---------------------------------------------------------------------------

ENTRIES = (("Widget frame", "A rigid steel box that holds the gears"),
           ("Sprocket wheel", "A toothed steel wheel that drives the chain"),
           ("Flywheel", "A heavy wheel that stores energy"))

NUMBERS = cks.NUMBER_WORDS
TREES = tuple("oak pine elm ash birch maple cedar larch rowan alder hazel willow".split())


def _md(path: str, paragraphs) -> rd.Document:
    doc = rd.read_bytes(path, "\n\n".join(paragraphs).encode("utf-8"))
    assert doc is not None, path
    return doc


def _documents():
    docs = []
    for tree in TREES:
        lines = [f"There are {n} gears in the {tree} box." for n in NUMBERS]
        lines += [f"We counted {n} wheels near the {tree} shed." for n in NUMBERS]
        docs.append(_md(f"notes/trees/{tree}.md", lines))
    docs.append(_md("notes/paper.md", [
        "## Appendix E: Glossary",
        "\n".join(f"- **{term}:** {gloss}" for term, gloss in ENTRIES),
    ]))
    docs.append(_md("notes/frames.md", [
        "# Widget frame",
        "We built a widget frame yesterday.",
        "The widget frame is a steel box for the gears.",
        "Widget frame: a light cage.",
        "A widget frame holds steel gears in a rigid box.",
        "Sprocket wheel: a toothed steel wheel that drives the chain.",
        "Sprocket wheel, a wheel with teeth.",
        "Every sprocket wheel has steel teeth for the chain.",
        "Flywheel is heavy.",
    ]))
    return tuple(docs)


DOCS = _documents()
KNOWLEDGE = mdl.build(DOCS, digest="synthetic-corpus-definitions")
# the first line of notes/frames.md is a heading of that (synthetic) document
gl._HEADINGS["notes/frames.md"] = frozenset({"Widget frame"})
HELD = gl.hold_out(KNOWLEDGE, ENTRIES)


# ---------------------------------------------------------------------------
#  The Lean file (studies/CORPUS_DEFINITIONS_STUDY.md §5)
# ---------------------------------------------------------------------------

class TestLeanFile(unittest.TestCase):

    def test_theorems_and_no_sorry(self):
        path = constants.lean_file("CorpusDefinitions.lean")
        if not path.is_file():
            self.skipTest(f"{path.name} is not in the tree")
        text = path.read_text(encoding="utf-8")
        for name in ("grade_comm", "grade_le_left", "grade_le_right", "grade_mono",
                     "heldout_clean", "heldout_keeps", "coord_le_cap", "coord_mono"):
            self.assertRegex(text, rf"\btheorem {name}\b", name)
        self.assertIsNone(re.search(r"\bsorry\b", text))


# ---------------------------------------------------------------------------
#  glossary.py
# ---------------------------------------------------------------------------

class TestGlossary(unittest.TestCase):

    def test_parse(self):
        text = ("# Paper\n\n- **Not:** in the appendix\n\n## Appendix E: Glossary\n\n"
                "- **Carrier:** A 24-tuple of exact rationals\n"
                "- **Construction A/B/C:** The three-tiered ladder\n\n"
                "## Appendix F\n- **After:** not read\n")
        self.assertEqual(gl.parse_glossary(text),
                         (("Carrier", "A 24-tuple of exact rationals"),
                          ("Construction A/B/C", "The three-tiered ladder")))

    def test_paper_glossary(self):
        # the paper's Appendix E, read at import (27 terms when the paper is present)
        if gl.GLOSSARY:
            self.assertEqual(len(gl.GLOSSARY), 27)
            self.assertIn("Golay code", [t for t, _ in gl.GLOSSARY])

    def test_hold_out_is_complete(self):
        removed = gl.held_out_ids(KNOWLEDGE, ENTRIES)
        self.assertEqual([KNOWLEDGE.sentences[i].address for i in removed],
                         ["notes/paper.md#p1.s0", "notes/frames.md#p5.s0"])
        self.assertEqual(len(HELD.sentences), len(KNOWLEDGE.sentences) - 2)
        # heldout_clean: no surviving sentence holds a gloss
        self.assertEqual(gl.leaks([s.tokens for s in HELD.sentences], ENTRIES), 0)
        # heldout_keeps: nothing else is removed
        kept = {s.address for s in HELD.sentences}
        self.assertTrue(all(s.address in kept for i, s in enumerate(KNOWLEDGE.sentences)
                            if i not in removed))
        # the postings index the kept sentences
        for sid in HELD.sentence_ids("widget"):
            self.assertIn("widget", HELD.sentences[sid].tokens)

    def test_grade(self):
        term = ("widget", "frame")
        gloss = ans.tokens_of("A rigid steel box that holds the gears")
        answer = ans.tokens_of("The widget frame is a steel box for the gear.")
        self.assertEqual(gl.grade(answer, gloss, term), 3)      # steel, box, gear(s)
        self.assertEqual(gl.grade(answer, gloss, term), gl.grade(gloss, answer, term))
        self.assertLessEqual(gl.grade(answer, gloss, term),
                             len(ans.content_set(answer, term)))
        self.assertEqual(gl.grade(("widget", "frame"), gloss, term), 0)   # the term's own words
        self.assertTrue(gl.agrees(answer, gloss, term))
        self.assertFalse(gl.agrees(ans.tokens_of("a steel cage"), gloss, term))

    def test_mismatched_gloss(self):
        self.assertEqual(gl.mismatched_gloss("Widget frame", ENTRIES), ENTRIES[1])
        self.assertEqual(gl.mismatched_gloss("Flywheel", ENTRIES), ENTRIES[0])
        self.assertEqual(gl.mismatched_gloss("Nothing", ENTRIES), ("", ""))

    def test_first_mention_skips_headings(self):
        got = gl.first_mention("widget frame", HELD)
        self.assertEqual(got["address"], "notes/frames.md#p1.s0")
        self.assertTrue(gl.is_heading(HELD.sentences[[s.address for s in HELD.sentences]
                                                     .index("notes/frames.md#p0.s0")]))
        self.assertIsNone(gl.first_mention("zyxwv", HELD))
        # a real document's headings are read from the file itself
        heads = gl._heading_texts("studies/CORPUS_DEFINITIONS_STUDY.md")
        if heads:
            self.assertIn("2.1 The graded definitions", heads)

    def test_grade_definitions_pattern(self):
        graded = gl.grade_definitions(HELD, "pattern", ENTRIES)
        self.assertEqual((graded["terms"], graded["answered"]), (3, 3))
        self.assertEqual((graded["total_grade"], graded["control_total"]), (1, 1))
        self.assertEqual(graded["leaks"], 0)
        first = graded["rows"][0]
        self.assertEqual(first["address"], "notes/frames.md#p3.s0")   # "Widget frame: a light cage."
        self.assertEqual(first["quality"]["pattern"], "gloss::")

    def test_context_ranking_grades_higher(self):
        pattern = gl.grade_definitions(HELD, "pattern", ENTRIES)
        context = gl.grade_definitions(HELD, "context", ENTRIES)
        self.assertEqual(context["rows"][0]["address"], "notes/frames.md#p2.s0")
        self.assertEqual(context["rows"][0]["grade"], 3)
        self.assertGreater(context["total_grade"], pattern["total_grade"])
        self.assertEqual((context["wins"], context["losses"]), (1, 0))
        self.assertEqual(context["leaks"], 0)
        self.assertEqual(gl.context_ranking("widget frame", HELD)["address"],
                         "notes/frames.md#p2.s0")

    def test_marks(self):
        base = {"total_grade": 26, "control_total": 17, "wins": 9, "losses": 5,
                "agree": 7, "agree_top": 11, "mismatched_total": 9}
        self.assertEqual(gl.marks(base), {"G1": True, "G2": False, "G3": False, "G4": True})
        self.assertFalse(gl.marks(dict(base, mismatched_total=14))["G4"])
        self.assertFalse(gl.marks(dict(base, wins=5))["G1"])


# ---------------------------------------------------------------------------
#  word_address.py
# ---------------------------------------------------------------------------

class TestWordAddress(unittest.TestCase):

    def test_floor_log2(self):
        for value, k in ((Fraction(1), 0), (Fraction(2), 1), (Fraction(3), 1),
                         (Fraction(1024), 10), (Fraction(1, 2), -1),
                         (Fraction(3, 4), -1), (Fraction(1, 3), -2),
                         (Fraction(1023, 1024), -1)):
            self.assertEqual(wa.floor_log2(value), k, value)
            self.assertTrue(Fraction(2) ** k <= value < Fraction(2) ** (k + 1))
        with self.assertRaises(ValueError):
            wa.floor_log2(Fraction(0))

    def test_positional_anchors(self):
        model = KNOWLEDGE.model
        got = wa.anchors(model, "positional")
        self.assertEqual(len(got), wa.POSITIONAL_ANCHORS)
        ranked = sorted(model.unigram, key=lambda w: (-model.unigram[w], w))
        self.assertEqual(got, tuple(ranked[:wa.POSITIONAL_ANCHORS]))
        with self.assertRaises(ValueError):
            wa.anchors(model, "nowhere")

    def test_coordinates_bounded(self):
        book = wa.address_book(KNOWLEDGE, "positional")
        for vector in book["vectors"].values():
            self.assertEqual(len(vector), 24)
            self.assertTrue(all(0 <= c <= wa.CAP for c in vector))
        window = wa.address_book(KNOWLEDGE, "window")
        self.assertEqual(window["vectors"]["gears"][window["anchors"].index("gears")], wa.CAP)

    def test_locate_reads_back(self):
        got = wa.locate("seven", KNOWLEDGE, "positional")
        self.assertTrue(got["ok"])
        self.assertTrue(got["readback"])
        self.assertEqual(tuple(la.describe_address(got["address"])["recovered"]),
                         tuple(got["coordinates"].values()))
        self.assertEqual(got["coordinates"]["are _"], 9)
        self.assertEqual(got["coordinates"]["_ gears"], 9)
        # the other number words fill the same slots: the same point
        self.assertTrue(all(w in NUMBERS and d == 0 for w, d in got["neighbours"]))
        self.assertFalse(wa.locate("zyxwv", KNOWLEDGE, "positional")["ok"])

    def test_control_is_a_permutation(self):
        book = wa.address_book(KNOWLEDGE, "positional")
        control = wa.control_addresses(book)
        self.assertEqual(sorted(control.values()), sorted(book["addresses"].values()))
        self.assertEqual(set(control), set(book["addresses"]))

    def test_compute_marks(self):
        got = wa.compute(KNOWLEDGE, "positional")
        self.assertEqual(got["readback"], got["words"])        # W1
        self.assertEqual(got["distinct_vectors"], got["distinct_addresses"])   # W4
        self.assertEqual(got["number_share"], 1)
        self.assertTrue(got["marks"]["W1"] and got["marks"]["W4"])
        self.assertIsInstance(got["number_control_share"], Fraction)


# ---------------------------------------------------------------------------
#  definitions_study.py
# ---------------------------------------------------------------------------

class TestDefinitionsStudy(unittest.TestCase):

    def test_compute_shape(self):
        got = cds.compute(KNOWLEDGE)
        self.assertEqual(sorted(got["marks"]), ["G1", "G2", "G3", "G4", "W1", "W2", "W3", "W4"])
        self.assertEqual(sorted(got["amended"]), ["G1'", "G2'", "G3'", "G4'", "W2'", "W3'"])
        self.assertEqual(got["met"], sum(got["marks"].values()))
        self.assertEqual(got["glossary"]["leaks"], 0)
        self.assertTrue(got["marks"]["W1"])

    def test_report_is_honest(self):
        report = cds.corpus_definitions_report()
        state = cds.state()
        if report.get("available"):
            self.assertTrue(state["fresh"])
        else:
            self.assertIn(state["verdict"], ("absent", "stale"))
            self.assertIn("--write", report["reason"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
