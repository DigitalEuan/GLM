"""Tests for the second friction round (Phase 157,
``studies/FRICTION_TWO_STUDY.md``): :mod:`glm_universal.knowledge.friction_two`
(worn contact, the noise-set reader) and :mod:`~.friction_two_study` (the
offline did-you-mean, wear, the margin, the frozen path, the marks).

Fast and synthetic: an invented corpus built with
:func:`glm_universal.knowledge.model.build`; the respelling is read through
the stored table (``runtime/_data/respell_table.json``, a fraction of a
second) or a stand-in reader; nothing is written and the CLI is never run.

*Reconstructed 31 October 2026 (repository check): the original
tests/test_friction_two.py was lost in the October 2026 reorganisation;
rebuilt from studies/FRICTION_TWO_STUDY.md (§§2.1-2.6) and the
reconstructed modules.*
"""
from __future__ import annotations

import unittest
from collections import namedtuple

from glm_universal.knowledge import friction as fr
from glm_universal.knowledge import friction_two as f2
from glm_universal.knowledge import friction_two_study as f2s
from glm_universal.knowledge import model as mdl
from glm_universal.knowledge import reader as rd


def _doc(path, texts):
    folder = path.rsplit("/", 1)[0]
    sents = tuple(rd.Sentence(tokens=rd._tokenise(t), address=f"{path}#p{i}.s0",
                              tier0=False, folder=folder, text=t,
                              document=path, paragraph=i)
                  for i, t in enumerate(texts))
    paras = tuple(rd.Paragraph(index=i, sentences=(s,), tier0=False, text=s.text)
                  for i, s in enumerate(sents))
    return rd.Document(path=path, digest="0" * 64, sentences=sents,
                       paragraphs=paras)


DOCS = (
    _doc("alpha/wires/notes.txt",
         [f"the copper wire carries current through the {w} board today"
          for w in ("circuit", "printed", "test", "main", "spare", "logic")]),
    _doc("beta/rivers/notes.txt",
         [f"the river water carries silt through the {w} valley today"
          for w in ("green", "deep", "wide", "north", "lower", "quiet")]),
    _doc("gamma/stars/notes.txt",
         [f"the bright star emits light across the {w} sky tonight"
          for w in ("dark", "winter", "summer", "southern", "clear", "night")]),
)


def knowledge():
    return mdl.build(DOCS, digest="synthetic")


Respelt = namedtuple("Respelt", "text")


class TestLeanFile(unittest.TestCase):

    def test_friction_two_lean_theorems_no_sorry(self):
        from glm_universal.engineering import domains as dmn
        c = dmn.lean_check("FrictionTwo.lean", (
            "reread_keeps_answer", "noise_switches_le", "worn_touches_le"))
        if not c["present"]:
            self.skipTest("FrictionTwo.lean is not present")
        self.assertEqual((c["missing"], c["sorry"]), ([], 0))


class TestWornContact(unittest.TestCase):

    def setUp(self):
        self.m = fr.HeldOut(knowledge().model, [])

    def test_worn_equals_contact_with_fresh_budget(self):
        prefix = ["the", "copper"]
        choice, spent = f2.worn_contact_predict(self.m, prefix)
        self.assertEqual(choice, fr.contact_predict(self.m, prefix))
        self.assertTrue(set(spent) <= set(fr.content_words(prefix)))

    def test_spent_words_stop_counting(self):
        prefix = ["copper", "wire", "carries"]
        used = {w: f2.BUDGET for w in fr.content_words(prefix)}
        choice, spent = f2.worn_contact_predict(self.m, prefix, used=used)
        self.assertEqual(spent, [])
        self.assertEqual(choice, fr.patch_predict(self.m, prefix))

    def test_worn_continuation_touches_bounded(self):
        c = f2.worn_continuation(self.m, ["the", "copper", "wire"])
        used = c["state"].get("used", {})
        self.assertTrue(all(n <= f2.BUDGET for n in used.values()))
        self.assertEqual(c["state"].get("touches", 0), sum(used.values()))
        self.assertIn(c["stop"], fr.STOPS)


class TestNoiseReader(unittest.TestCase):

    def test_noise_threshold_grows_with_changes(self):
        steps = [({"A": 8}, "A"), ({"A": 8, "B": 9}, "B"),
                 ({"A": 8, "B": 10}, "B")]
        # step 1: r = 1, moves when 8*9 > 9*8: no; step 2: r = 1, 80 > 72: yes
        self.assertEqual(f2.noise_reader(steps, 8), ["A", "A", "B"])
        flip = [({"A": 8}, "A"), ({"A": 8, "B": 10}, "B"),
                ({"A": 12, "B": 10}, "A"), ({"A": 12, "B": 15}, "B")]
        # r(t) = 1, 2, 3: 80 > 72 move; held B, A leads: 96 > 100? no;
        # B leads again: held B
        self.assertEqual(f2.noise_reader(flip, 8), ["A", "B", "B", "B"])

    def test_never_switches_more_than_the_leader(self):
        ev = fr.FolderEvidence(knowledge(), "directory")
        for s in knowledge().sentences:
            lead = fr.leaders(ev, s)
            n = fr.reading_stats(f2.noise_reader(lead["steps"]), lead["truth"])
            f = fr.reading_stats(lead["leaders"], lead["truth"])
            self.assertLessEqual(n["switches"], f["switches"])


class TestRespellOffline(unittest.TestCase):

    def test_typo_pairs(self):
        got = f2s.typo_pairs(["describe the wheel", "is it hot"])
        self.assertEqual(got, [("describe the wheel", "dsecribe the wheel")])

    def test_grade(self):
        self.assertEqual(f2s._grade("abc", "acb", "abc"), "restored")
        self.assertEqual(f2s._grade("abc", "acb", "acb"), "unchanged")
        self.assertEqual(f2s._grade("abc", "acb", "axe"), "different")

    def test_tally_with_a_stand_in_reader(self):
        pairs = [("describe it", "dsecribe it"), ("the river", "the rvier"),
                 ("a crane", "a carne")]
        fix = {"dsecribe it": "describe it", "the rvier": "the rover"}
        t = f2s.respell_tally(pairs, "use", tbl=object(),
                              reader=lambda text, company: Respelt(fix.get(text, text)))
        self.assertEqual((t["restored"], t["different"], t["unchanged"]), (1, 1, 1))
        self.assertEqual(t["different_examples"],
                         [["the rvier", "the rover", "the river"]])

    def test_stored_table_restores_a_typo(self):
        from glm_universal.runtime import respell as rs
        tbl = rs.table()
        if not tbl.present:
            self.skipTest("runtime/_data/respell_table.json is not present")
        t = f2s.respell_tally([("describe the wheel", "dsecribe the wheel")],
                              "loaded", tbl=tbl)
        self.assertEqual(t["restored"], 1)
        shorts = f2s.short_word_pairs(["what is the mass"], tbl=tbl)
        self.assertTrue(all(len(w) in (4, 5, 6) for _q, _m, w in shorts))
        self.assertTrue(all(not rs.known(w, tbl) for _q, _m, w in shorts))


class TestFrozenAndMarks(unittest.TestCase):

    def test_frozen_compare(self):
        before = {"results": [
            {"id": "a", "outcome": "correct", "answer": "1", "kind": "math"},
            {"id": "b", "outcome": "correct", "answer": "x", "kind": "corpus"},
            {"id": "c", "outcome": "wrong_answer", "answer": "2", "kind": "math"}]}
        after = {"results": [
            {"id": "a", "outcome": "correct", "answer": "1", "kind": "math"},
            {"id": "b", "outcome": "correct", "answer": "y", "kind": "corpus"},
            {"id": "c", "outcome": "correct", "answer": "3", "kind": "math"}]}
        fz = f2s.frozen_compare(before, after)
        self.assertEqual((fz["cases"], fz["passed_before"], fz["passed_after"]),
                         (3, 2, 3))
        self.assertEqual(fz["outcome_ids"], ["c"])
        self.assertEqual(fz["lines_untraced"], [])      # b is a corpus case
        self.assertFalse(f2s._frozen_holds(fz))
        self.assertTrue(f2s._frozen_holds(f2s.frozen_compare(before, before)))

    def test_restore_mark(self):
        self.assertTrue(f2s._restore_mark(
            {"restored": 85, "different": 2, "unchanged": 13}, 100))
        self.assertFalse(f2s._restore_mark(
            {"restored": 84, "different": 0, "unchanged": 16}, 100))
        self.assertFalse(f2s._restore_mark(
            {"restored": 90, "different": 3, "unchanged": 7}, 100))

    def test_marks_missed_without_evidence(self):
        got = f2s._assemble(None, None, None)
        self.assertEqual(got["met"], 0)
        self.assertEqual(got["taken"], len(f2s.MARKS))
        self.assertEqual(len(got["unmeasured"]), 2)

    def test_wear_and_noise_on_a_synthetic_corpus(self):
        k = knowledge()
        held = fr.sample(k)
        model = fr.hold_out_model(k, held)
        we = f2s.wear_measure(model, held)
        self.assertEqual(set(we["overlap"]),
                         {"patch", "contact", "worn", "loaded", "loaded_worn"})
        no = f2s.noise_measure(fr.FolderEvidence(k, "directory"), held)
        self.assertEqual(no["violations"], 0)
        self.assertEqual(no["folders"], 3)

    def test_report_without_a_current_measurement(self):
        r = f2s.friction_two_report()
        if not r["available"]:
            self.assertIn("--write", r["reasons"][0])
        else:
            self.assertIn("marks", r)


if __name__ == "__main__":
    unittest.main()
