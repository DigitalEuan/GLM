"""Tests for the friction study (Phase 156, ``studies/FRICTION_STUDY.md``):
:mod:`glm_universal.knowledge.friction`, :mod:`~.friction_survey` and
:mod:`~.friction_study`.

Fast and synthetic: a corpus of a few dozen invented sentences in three
folders is built with :func:`glm_universal.knowledge.model.build`, so the
real corpus is never loaded, the CLI is never run and nothing is written.

*Reconstructed 31 October 2026 (repository check): the original
tests/test_friction.py was lost in the October 2026 reorganisation; rebuilt
from studies/FRICTION_STUDY.md (§§2.1-2.5) and the reconstructed modules.*
"""
from __future__ import annotations

import unittest
from collections import namedtuple
from fractions import Fraction

from glm_universal.knowledge import friction as fr
from glm_universal.knowledge import friction_study as fst
from glm_universal.knowledge import friction_survey as fsv
from glm_universal.knowledge import model as mdl
from glm_universal.knowledge import reader as rd


# ---------------------------------------------------------------------------
#  A synthetic corpus
# ---------------------------------------------------------------------------

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


_COPPER = [f"the copper wire carries current through the {w} board today"
           for w in ("circuit", "printed", "test", "main", "spare", "logic")]
_RIVER = [f"the river water carries silt through the {w} valley today"
          for w in ("green", "deep", "wide", "north", "lower", "quiet")]
_STAR = [f"the bright star emits light across the {w} sky tonight"
         for w in ("dark", "winter", "summer", "southern", "clear", "night")]

DOCS = (
    _doc("alpha/wires/notes.txt", _COPPER),
    _doc("beta/rivers/notes.txt", _RIVER),
    _doc("gamma/stars/notes.txt", _STAR),
)


def knowledge():
    return mdl.build(DOCS, digest="synthetic")


# ---------------------------------------------------------------------------
#  friction.py
# ---------------------------------------------------------------------------

class TestSizeRule(unittest.TestCase):

    def test_qualifies(self):
        self.assertTrue(fr.qualifies(rd._tokenise(_COPPER[0])))
        self.assertFalse(fr.qualifies(("a", "b", "c")))
        # eight tokens but too few content words
        self.assertFalse(fr.qualifies(tuple("the of in on at to by it".split())))

    def test_content_words_distinct_in_order(self):
        self.assertEqual(fr.content_words(["the", "wire", "a", "wire", "board"]),
                         ["wire", "board"])

    def test_contact_score(self):
        self.assertEqual(fr.contact_score(3, 2), 9)
        self.assertEqual(fr.contact_score(3, 2, fr.LOAD), 30)

    def test_qualifying_and_sample(self):
        k = knowledge()
        ids = fr.qualifying(k)
        self.assertEqual(len(ids), 18)
        self.assertEqual(len(fr.sample(k, size=6)), 6)


class TestHeldOut(unittest.TestCase):

    def setUp(self):
        self.k = knowledge()
        self.held = (self.k.sentences[0],)
        self.m = fr.HeldOut(self.k.model, [s.tokens for s in self.held])

    def test_held_sentence_subtracted(self):
        self.assertEqual(self.k.model.unigram["circuit"], 1)
        self.assertEqual(self.m.unigram("circuit"), 0)
        self.assertEqual(self.m.unigram("copper"), 5)
        self.assertNotIn("circuit", self.m.row(("the",)))

    def test_patch_refuses_on_tie(self):
        # after "through the" the six board words tie at one each (the held
        # sentence's removed): a tie, so the patch refuses
        self.assertIsNone(fr.patch_predict(self.m, ["through", "the"]))
        self.assertEqual(fr.patch_predict(self.m, ["the", "copper"]), "wire")

    def test_contact_and_loaded_answer_unique(self):
        self.assertEqual(fr.contact_predict(self.m, ["the", "copper"]), "wire")
        self.assertEqual(fr.loaded_predict(self.m, ["the", "copper"]), "wire")
        self.assertEqual(fr.tiebreak_predict(self.m, ["the", "copper"]), "wire")

    def test_predict_positions_counts(self):
        r = fr.predict_positions(fr.patch_predict, self.m, self.held[0].tokens)
        self.assertEqual(r["positions"], len(self.held[0].tokens) - 2)
        self.assertLessEqual(r["correct"], r["answered"])
        self.assertLessEqual(r["answered"], r["positions"])


class TestContinuation(unittest.TestCase):

    def test_stops(self):
        m = None
        self.assertEqual(fr.continuation(lambda mm, h: None, m, ["x"])["stop"],
                         "refusal")
        self.assertEqual(fr.continuation(lambda mm, h: ".", m, ["x"])["stop"],
                         "end")
        c = fr.continuation(lambda mm, h: "a", m, ["x"])
        self.assertEqual((c["tokens"], c["stop"]), (["a", "a"], "cycle"))
        c = fr.continuation(lambda mm, h: f"w{len(h)}", m, ["x"])
        self.assertEqual((len(c["tokens"]), c["stop"]), (fr.MAX_TOKENS, "limit"))

    def test_overlap_is_multiset(self):
        self.assertEqual(fr.overlap(["a", "b", "a"], ["a", "a", "c"]), 2)

    def test_continuation_on_corpus(self):
        k = knowledge()
        m = fr.HeldOut(k.model, [])
        c = fr.continuation(fr.patch_predict, m, ["the", "copper"])
        self.assertEqual(c["tokens"][:3], ["wire", "carries", "current"])


class TestReaders(unittest.TestCase):

    STEPS = [({"A": 4}, "A"), ({"A": 4, "B": 5}, "B"), ({"A": 4, "B": 6}, "B")]

    def test_margin_reader_quarter(self):
        # moves only when S(leader) > (1 + 1/4) S(held): 5 > 5 no, 6 > 5 yes
        self.assertEqual(fr.margin_reader(self.STEPS, Fraction(1, 4)),
                         ["A", "A", "B"])
        self.assertEqual(fr.keep_or_move(self.STEPS, lambda t, h, l: True),
                         ["A", "B", "B"])

    def test_reading_stats(self):
        self.assertEqual(fr.reading_stats(["A", "B", "A", "C"], "C"),
                         {"switches": 3, "returns": 1, "into_truth": 1,
                          "final_correct": 1})
        self.assertEqual(fr.reading_stats([], "C")["final_correct"], 0)

    def test_folder_evidence(self):
        k = knowledge()
        ev = fr.FolderEvidence(k, "top")
        self.assertEqual(ev.folders, ("alpha", "beta", "gamma"))
        s = k.sentences[0]
        # "copper" is held by alpha only: height 3 - 1 = 2
        self.assertEqual(ev.height("copper", s), (2, ("alpha",)))
        # "circuit" is only in the held sentence itself: no folder holds it
        self.assertEqual(ev.height("circuit", s), (3, ()))
        lead = fr.leaders(ev, s)
        self.assertEqual(lead["truth"], "alpha")
        self.assertEqual(lead["leaders"][-1], "alpha")
        st = fr.sticking_reader(ev, s)
        self.assertEqual(st[-1], "alpha")
        d = fr.FolderEvidence(k, "directory")
        self.assertEqual(d.folder(s), "alpha/wires")
        with self.assertRaises(ValueError):
            fr.FolderEvidence(k, "planet")


# ---------------------------------------------------------------------------
#  friction_survey.py
# ---------------------------------------------------------------------------

Case = namedtuple("Case", "id kind expect question")
Res = namedtuple("Res", "passed outcome answer")


class TestPerturbations(unittest.TestCase):

    def test_seven_declared(self):
        self.assertEqual(fsv.PERTURBATIONS, ("qmark", "capital", "spaces",
                                             "please", "tellme", "typo",
                                             "drop_the"))
        self.assertEqual(fsv.SURFACE, ("qmark", "capital", "spaces"))

    def test_typo_swaps_second_and_third_of_longest(self):
        self.assertEqual(fsv._typo("describe the wheel"), "dsecribe the wheel")
        # a tie: the first longest word
        self.assertEqual(fsv._typo("abcde fghij"), "acbde fghij")
        self.assertIsNone(fsv._typo("is it hot"))       # no word of 5 letters
        self.assertIsNone(fsv._typo("a seems b"))       # the swap changes nothing

    def test_perturb(self):
        q = "what is the mass of the earth"
        self.assertEqual(fsv.perturb(q, "qmark"), q + "?")
        self.assertIsNone(fsv.perturb(q + "?", "qmark"))
        self.assertEqual(fsv.perturb(q, "capital"), "W" + q[1:])
        self.assertEqual(fsv.perturb(q, "spaces"), q.replace(" ", "  "))
        self.assertEqual(fsv.perturb(q, "please"), "please " + q)
        self.assertEqual(fsv.perturb(q, "tellme"), "can you tell me " + q)
        self.assertEqual(fsv.perturb(q, "drop_the"), "what is mass of the earth")
        self.assertIsNone(fsv.perturb("define entropy", "drop_the"))
        with self.assertRaises(KeyError):
            fsv.perturb(q, "shout")

    def test_classify_and_tally(self):
        self.assertEqual(fsv.classify("answer", "correct"), "hold")
        self.assertEqual(fsv.classify("refusal", "refused_as_expected"), "hold")
        self.assertEqual(fsv.classify("answer", "unexpected_refusal"), "stick")
        self.assertEqual(fsv.classify("answer", "wrong_answer"), "slip")
        self.assertEqual(fsv.classify("refusal", "unexpected_answer"), "slip")
        t = fsv.tally([{"perturbation": "typo", "class": "stick"}])
        self.assertEqual(t["typo"], {"runs": 1, "hold": 0, "stick": 1, "slip": 0})
        self.assertEqual(list(t), list(fsv.PERTURBATIONS))

    def test_refusal_reread(self):
        self.assertTrue(fsv.refusal_reread("REFUSED: no frame\n"))
        self.assertFalse(fsv.refusal_reread("REFUSED: x\nANSWER: y\n"))

    def test_survey_with_stand_ins(self):
        cases = [Case("c1", "k", "answer", "what is the mass of the earth"),
                 Case("c2", "k", "refusal", "describe the colour of seven"),
                 Case("c3", "k", "answer", "broken base")]

        def run_case(case, timeout):
            if case.id == "c3":
                return Res(False, "wrong_answer", "x")
            if case.question.startswith("please"):
                return Res(False, "unexpected_refusal" if case.expect == "answer"
                           else "unexpected_answer", "")
            if case.question != case.question.lower():
                return Res(False, "error", "")
            ok = "correct" if case.expect == "answer" else "refused_as_expected"
            return Res(True, ok, "a")

        got = fsv.survey(cases, jobs=1, run_case=run_case,
                         output=lambda q, t: (0, "REFUSED: no frame\n"))
        self.assertEqual((got["cases"], got["base_passing"]), (3, 2))
        self.assertEqual(got["base_failing"], ["c3"])
        bp = got["by_perturbation"]
        self.assertEqual(bp["please"], {"runs": 2, "hold": 0, "stick": 1, "slip": 1})
        self.assertEqual(bp["capital"]["slip"], 2)       # errors are slips ...
        self.assertEqual(got["rescored"]["capital"]["slip"], 0)  # ... re-read
        self.assertEqual(got["rescored"]["capital"]["stick"], 1)
        self.assertEqual(got["rescored"]["capital"]["hold"], 1)
        self.assertEqual(got["refusal_slips"], 2)
        self.assertEqual(got["refusal_slips_rescored"], 1)


# ---------------------------------------------------------------------------
#  The fixes of §2.5 (GLM.py's settle_question)
# ---------------------------------------------------------------------------

def _cli_module():
    import importlib.util
    from pathlib import Path
    import glm_universal
    path = Path(glm_universal.__file__).resolve().parent.parent / "GLM.py"
    spec = importlib.util.spec_from_file_location("_glm_cli_for_tests", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestSettleQuestion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.settle = staticmethod(_cli_module().settle_question)

    def test_identity_on_every_evaluation_question(self):
        from glm_universal.evaluation.cases import CASES
        moved = [c.question for c in CASES
                 if self.settle(c.question) != c.question]
        self.assertEqual(moved, [])

    def test_settles_spaces_and_a_leading_tell_me(self):
        self.assertEqual(self.settle("what  is\tthe  mass "), "what is the mass")
        self.assertEqual(self.settle("can you tell me meaning of water"),
                         "can you meaning of water")
        self.assertEqual(self.settle("tell me the mass of the earth"),
                         "the mass of the earth")

    def test_leaves_the_rest_alone(self):
        for q in ("tell me about entropy", "tell me whether 7 is prime",
                  "tell me if 9 is a square", 'define  "a  b"',
                  "run `x  = 1`", "line one\nline  two"):
            self.assertEqual(self.settle(q), q)


# ---------------------------------------------------------------------------
#  friction_study.py
# ---------------------------------------------------------------------------

class TestLeanFile(unittest.TestCase):

    def test_friction_lean_theorems_no_sorry(self):
        from glm_universal.engineering import domains as dmn
        c = dmn.lean_check("Friction.lean", (
            "held_switches_le", "stick_switches_le", "held_within_margin",
            "contact_keeps_large_lead", "contact_empty_prompt"))
        if not c["present"]:
            self.skipTest("Friction.lean is not present")
        self.assertEqual((c["missing"], c["sorry"]), ([], 0))


class TestStudy(unittest.TestCase):

    def test_marks_missed_without_evidence(self):
        self.assertFalse(any(fst.survey_marks(None).values()))
        self.assertFalse(any(fst.corpus_marks(None).values()))
        fx = fst.fix_marks(None, None, None)
        self.assertEqual(fx, {"X1": False, "X2": False, "X3": False, "X4": False})

    def test_survey_marks_from_tallies(self):
        bp = {p: {"runs": 100, "hold": 100, "stick": 0, "slip": 0}
              for p in fsv.PERTURBATIONS}
        sv = {"by_perturbation": bp, "rescored": bp, "refusal_runs": 100,
              "refusal_slips": 1, "refusal_slips_rescored": 0}
        self.assertTrue(all(fst.survey_marks(sv).values()))
        sv["refusal_slips"] = 2
        self.assertFalse(fst.survey_marks(sv)["F1"])

    def test_corpus_measure_runs_on_a_synthetic_corpus(self):
        data = fst.corpus_measure(knowledge())
        self.assertEqual(data["contact"]["sentences"], 18)
        self.assertEqual(set(data["contact"]["correct"]), set(fst.PREDICTORS))
        self.assertEqual(data["stickslip"]["folders"], 3)
        self.assertEqual(data["stickslip"]["violations"]["stick 1/4"], 0)
        marks = fst.corpus_marks(data)
        self.assertTrue(marks["S1"])                    # proved: never more switches
        got = fst._assemble(data, None)
        self.assertEqual(got["taken"], len(fst.MARKS))
        self.assertTrue(any("survey is not stored" in u for u in got["unmeasured"]))

    def test_report_without_a_current_measurement(self):
        r = fst.friction_report()
        if not r["available"]:
            self.assertIn("--write", r["reasons"][0])
        else:
            self.assertIn("marks", r)


if __name__ == "__main__":
    unittest.main()
