"""Phase 117 -- questions about the GLM's own engineering, answered from the
project's own documents (track M).

``studies/META_QUESTIONS_STUDY.md`` measures the meta frames against marks
T1-T7 (:mod:`glm_universal.evaluation.meta_question_cases`).  These tests
hold the facts the round rests on at the evidence layer
(:mod:`glm_universal.reasoning.meta_evidence`), which the frames call; the
full measurement through the router is
``python3 -m glm_universal.tools meta-questions``.

The tests stay below the frames on purpose: everything that imports the
frame layer takes the whole Lean development into its closure
(``ITERATION_COST_STUDY.md`` §5k).
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

from glm_universal.evaluation import meta_question_cases as C
from glm_universal.evaluation import question_set_b_cases as qc
from glm_universal.reasoning import meta_evidence as ME

LEAN_FILE = (Path(__file__).resolve().parents[2] / "glm_lean" /
             "RequestProject" / "GLM" / "MetaAnswers.lean")


def _gate(script: str) -> bool:
    got = subprocess.run([sys.executable, "-I", "-c", script],
                         capture_output=True, text=True, timeout=30)
    lines = [ln for ln in got.stdout.splitlines() if ln.strip()]
    return got.returncode == 0 and bool(lines) and \
        lines[-1].endswith("VERIFIED True")


def _topic(key: str) -> ME.Topic:
    return next(tp for tp in ME.TOPICS if tp.key == key)


class TestTheDeclaredQuestions(unittest.TestCase):
    """T1-T3 at the evidence layer."""

    @classmethod
    def setUpClass(cls):
        items = qc.outside()
        cls.answers = {}
        for idx, topic, *_ in C.META_QUESTIONS:
            tp = ME.topic_of(ME.normalise(items[idx].text))
            cls.answers[idx] = (tp, ME.read_topic(tp, items[idx].text)
                                if tp else None)

    def test_every_question_has_its_topic(self):
        for idx, topic, *_ in C.META_QUESTIONS:
            with self.subTest(index=idx):
                tp, _ = self.answers[idx]
                self.assertIsNotNone(tp)
                self.assertEqual(tp.key, topic)

    def test_answers_hold_the_fragment(self):
        for idx, topic, verdict, frag, *_ in C.META_QUESTIONS:
            with self.subTest(index=idx):
                _, ans = self.answers[idx]
                self.assertTrue(ans.answered, ans.value)
                self.assertEqual(verdict, "ANSWER")
                self.assertIn(frag, ans.value)

    def test_quotes_and_theorems_are_cited(self):
        for idx, _, _, _, docs, lean, _ in C.META_QUESTIONS:
            with self.subTest(index=idx):
                _, ans = self.answers[idx]
                for d in docs:
                    self.assertIn(f"{d} §", ans.column2)
                for name in lean:
                    self.assertIn(name, ans.column2)

    def test_disputes_exactly_as_declared(self):
        for idx, *_, disputes in C.META_QUESTIONS:
            with self.subTest(index=idx):
                _, ans = self.answers[idx]
                got = tuple(d.split(":", 1)[0] for d in ans.disputes)
                self.assertEqual(got, tuple(disputes))

    def test_every_script_verifies(self):
        for idx, *_ in C.META_QUESTIONS:
            with self.subTest(index=idx):
                _, ans = self.answers[idx]
                self.assertTrue(_gate(ans.script))


class TestTheEvidenceIsRead(unittest.TestCase):
    """T4's controls: an answer never outlives its evidence."""

    def test_a_moved_quote_or_theorem_is_refused(self):
        items = qc.outside()
        for idx, topic, *_ in C.META_QUESTIONS:
            tp = _topic(topic)
            for kind in ("quote-moved", "lean-moved"):
                with self.subTest(index=idx, kind=kind):
                    ans = ME.mutated(tp, items[idx].text, kind)
                    self.assertFalse(ans.answered)
                    self.assertEqual(ans.code, "CITATION_MOVED")

    def test_a_mutated_script_fails(self):
        items = qc.outside()
        for idx, topic, *_ in C.META_QUESTIONS:
            tp = _topic(topic)
            for kind in ("script-quote", "script-claim"):
                with self.subTest(index=idx, kind=kind):
                    ans = ME.mutated(tp, items[idx].text, kind)
                    self.assertFalse(_gate(ans.script))

    def test_quote_takes_the_sentence_and_the_section(self):
        got = ME.quote(ME.PAPER, "a weight-5 error lies at distance 3")
        self.assertIsNotNone(got)
        self.assertIn("Complete Syndrome Decoding", got[0])
        self.assertTrue(got[1].startswith("**Beyond the covering radius"))
        self.assertIsNone(ME.quote(ME.PAPER, "a sentence nobody wrote here"))

    def test_lean_lookup_uses_the_stored_book(self):
        row = ME.lean_declaration("GLM.MetaAnswers.cayley_orthogonal")
        self.assertIsNotNone(row)
        self.assertEqual(row["file"], "MetaAnswers.lean")
        self.assertIsNone(ME.lean_declaration("GLM.MetaAnswers." + "no_such"))


class TestReading(unittest.TestCase):
    """T5 and T6 at the evidence layer."""

    def test_paraphrases_find_their_topic(self):
        for pid, text, topic in C.PARAPHRASES:
            with self.subTest(id=pid):
                tp = ME.topic_of(ME.normalise(text))
                self.assertIsNotNone(tp)
                self.assertEqual(tp.key, topic)

    def test_held_out_as_measured(self):
        # h92 ("coset weight is 4") is read by no cue: the recorded miss
        for pid, text, topic in C.HELD_OUT:
            with self.subTest(id=pid):
                tp = ME.topic_of(ME.normalise(text))
                if pid == "h92":
                    self.assertIsNone(tp)
                else:
                    self.assertEqual(tp.key if tp else None, topic)

    def test_near_misses_are_not_read(self):
        for text in C.NOT_READ:
            with self.subTest(text=text):
                self.assertIsNone(ME.topic_of(ME.normalise(text)))

    def test_the_other_outside_questions_are_not_read(self):
        declared = {x[0] for x in C.META_QUESTIONS}
        for it in qc.outside():
            if it.index in declared:
                continue
            with self.subTest(index=it.index):
                # not even by a cue an earlier frame would mask (questions
                # 35 and 95 were, on the first run; see the study §4)
                self.assertIsNone(ME.topic_of(ME.normalise(it.text)))


class TestLean(unittest.TestCase):
    """T7 (the source half; the build is ``lake build``)."""

    def test_named_theorems_and_no_sorry(self):
        src = LEAN_FILE.read_text(encoding="utf-8")
        code = re.sub(r"/-.*?-/", "", src, flags=re.S)
        code = re.sub(r"--[^\n]*", "", code)
        for name in C.LEAN_THEOREMS:
            with self.subTest(theorem=name):
                self.assertRegex(code, rf"theorem\s+{name}\b")
        self.assertNotRegex(code, r"\bsorry\b")


if __name__ == "__main__":
    unittest.main()
