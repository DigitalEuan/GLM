"""Tests for thermo-friction (Phase 159, ``studies/THERMO_FRICTION_STUDY.md``):
:mod:`glm_universal.knowledge.thermo_friction` (the bimetallic governor, A;
the thermoelectric prompt anchor, B) and :mod:`~.thermo_friction_study`
(the sintering measurement, C, and the marks).

Fast and synthetic: an invented corpus built with
:func:`glm_universal.knowledge.model.build` and a stand-in vocabulary table;
the stored respelling table and register lexicon are read only where a test
says so (a fraction of a second).  Nothing is written and the CLI is never
run.

*Reconstructed 31 October 2026 (repository check): the original
tests/test_thermo_friction.py was lost in the October 2026 reorganisation;
rebuilt from studies/THERMO_FRICTION_STUDY.md (§§2.1-2.3) and the
reconstructed modules.*
"""
from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.knowledge import friction as fr
from glm_universal.knowledge import model as mdl
from glm_universal.knowledge import reader as rd
from glm_universal.knowledge import thermo_friction as tf
from glm_universal.knowledge import thermo_friction_study as tfs
from glm_universal.runtime import respell as rs


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
          for w in ("circuit", "printed", "test", "main", "spare", "logic")]
         + ["copper wire and river silt share the valley board tonight"]),
    _doc("beta/rivers/notes.txt",
         [f"the river water carries silt through the {w} valley today"
          for w in ("green", "deep", "wide", "north", "lower", "quiet")]),
    _doc("gamma/stars/notes.txt",
         [f"the bright star emits light across the {w} sky tonight"
          for w in ("dark", "winter", "summer", "southern", "clear", "night")]),
)


def knowledge():
    return mdl.build(DOCS, digest="synthetic")


class TestGovernor(unittest.TestCase):

    def test_is_hot(self):
        self.assertTrue(tf.is_hot([10, 1, 1, 1, 1, 9]))     # 20 >= 14
        self.assertTrue(tf.is_hot([4]))
        self.assertFalse(tf.is_hot([3, 3, 3, 3, 3]))        # 6 < 15
        self.assertFalse(tf.is_hot([]))

    def test_repeats_reads_the_recent_window(self):
        self.assertTrue(tf.repeats(["q", "x", "q"], "x"))
        self.assertFalse(tf.repeats(["q", "x"], "q"))
        self.assertFalse(tf.repeats([], "x"))
        far = ["q", "x"] + [f"w{i}" for i in range(tf.RECENT)] + ["q"]
        self.assertFalse(tf.repeats(far, "x"))               # out of the window

    def test_penalty_divides_by_one_plus_heat(self):
        base = [("x", 10), ("y", 8)]
        hist = ["q", "x", "q"]
        hot = dict((c, s) for s, c in tf.governor_scores(base, hist, True, 1))
        self.assertEqual(hot, {"x": Fraction(5), "y": Fraction(8)})
        cold = dict((c, s) for s, c in tf.governor_scores(base, hist, False, 3))
        self.assertEqual(cold, {"x": Fraction(10), "y": Fraction(8)})
        static = dict((c, s) for s, c in
                      tf.governor_scores(base, hist, False, 0, static=True))
        self.assertEqual(static["x"], Fraction(5))

    def test_governor_tallies_and_cold_agreement(self):
        m = fr.HeldOut(knowledge().model, [])
        state = {}
        for prefix in (["the", "copper"], ["the", "river"], ["through", "the"]):
            tf.governor_choice(m, prefix, state)
        self.assertEqual(state.get("hot", 0) + state.get("cold", 0), 3)
        self.assertEqual(state.get("cold_disagree", 0), 0)   # A5 by construction
        c = tf.governed_continuation(m, ["the", "copper", "wire"])
        self.assertIn(c["stop"], fr.STOPS)
        p = tf.governed_positions(m, knowledge().sentences[0].tokens)
        self.assertLessEqual(p["correct"], p["answered"])


class TestAnchor(unittest.TestCase):

    def setUp(self):
        self.k = knowledge()
        self.ev = fr.FolderEvidence(self.k, "directory")

    def test_split_scores_prompt_is_first_three_content_words(self):
        s = self.k.sentences[6]       # "copper wire and river silt share ..."
        steps, prompt = tf.split_scores(self.ev, s)
        self.assertEqual(prompt, ["copper", "wire", "river"])
        P, G = steps[-1]
        S = tf._add(P, G)
        lead = fr.leaders(self.ev, s)
        self.assertEqual(S, lead["steps"][-1][0])         # P + G is S

    def test_anchor_readers(self):
        for s in self.k.sentences:
            got = tf.anchor_readers(self.ev, s, {"mismatched anchor": ["star"]})
            self.assertEqual(got["cold_off_leader"], 0)    # B5 by construction
            self.assertEqual(got["agree_hot"], 0)
            self.assertEqual(set(got["readings"]),
                             {"frictionless", "stick 1/4", "noise r/8",
                              "anchor", "mismatched anchor"})
            n = len(got["readings"]["frictionless"])
            self.assertTrue(all(len(r) == n for r in got["readings"].values()))


class TestSintering(unittest.TestCase):

    def test_recovery_set_rule(self):
        tbl = rs.Table(documents={"wire": 5, "river": 5, "mass": 9},
                       coordinates={})
        lex = frozenset({"millisecond", "wire", "mass", "ohm", "kelvin",
                         "abbey"})
        got = tfs.recovery_set(lex, tbl)
        # known words (wire, mass) and entries the typo cannot move (ohm:
        # under five letters; abbey: the swap changes nothing) are left out
        self.assertEqual(got, [("kelvin", "klevin"),
                               ("millisecond", "mlilisecond")])

    def test_prec_ge(self):
        self.assertTrue(tfs._prec_ge({"correct": 2, "answered": 4},
                                     {"correct": 1, "answered": 2}))
        self.assertFalse(tfs._prec_ge({"correct": 1, "answered": 4},
                                      {"correct": 1, "answered": 2}))

    def test_stored_lexicon_left_alone_by_sintering(self):
        from glm_universal.runtime import sinter as sn
        tbl, lex = rs.table(), sn.lexicon()
        if not tbl.present or not lex:
            self.skipTest("the respelling table or the register lexicon is absent")
        # an entry the shipped respelling changes into a commoner word
        # (the hazard of §7.3), left alone by the sintered reading
        self.assertEqual(sn.respell_sintered("bohm", tbl, lex).text, "bohm")
        self.assertTrue(sn.protected("x2") and sn.protected("fooBar"))


class TestMarks(unittest.TestCase):

    def test_marks_missed_without_evidence(self):
        got = tfs._assemble(None, None, None)
        self.assertEqual(got["met"], 0)
        self.assertEqual(got["taken"], len(tfs.MARKS))
        self.assertFalse(got["shipped"])
        self.assertEqual(len(got["unmeasured"]), 2)

    def test_governor_and_anchor_measures_on_a_synthetic_corpus(self):
        k = knowledge()
        held = fr.sample(k)
        gv = tfs.governor_measure(fr.hold_out_model(k, held), held)
        self.assertEqual(gv["undeclared_stops"], 0)
        self.assertEqual(gv["rows"]["cold_disagree"], 0)
        an = tfs.anchor_measure(fr.FolderEvidence(k, "directory"), held)
        self.assertEqual(an["cold_off_leader"], 0)
        self.assertIn("anchor", an["readers"])

    def test_report_without_a_current_measurement(self):
        r = tfs.thermo_friction_report()
        if not r["available"]:
            self.assertIn("--write", r["reasons"][0])
        else:
            self.assertIn("marks", r)


if __name__ == "__main__":
    unittest.main()
