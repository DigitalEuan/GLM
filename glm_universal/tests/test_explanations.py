"""Phase 120 -- outside questions that ask *why*, answered where a register or
an exact derivation decides them (track E).

``studies/EXPLANATION_ANCHOR_STUDY.md`` measures the explanation frames
against marks E1-E10 (:mod:`glm_universal.evaluation.explanation_cases`).
These tests hold the facts the round rests on at the anchor layer
(:mod:`glm_universal.reasoning.explanation_anchors`) and the nuclide register
(:mod:`glm_universal.data_objects.nuclides`); the full measurement through
the router is ``python3 -m glm_universal.tools explanations``.

The tests stay below the frames on purpose: everything that imports the
frame layer takes the whole Lean development into its closure
(``ITERATION_COST_STUDY.md`` §5k).
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.data_objects import nuclides as N
from glm_universal.evaluation import explanation_cases as C
from glm_universal.evaluation import question_set_b_cases as qc
from glm_universal.reasoning import explanation_anchors as EA

LEAN_FILE = (Path(__file__).resolve().parents[2] / "glm_lean" /
             "RequestProject" / "GLM" / "ExplanationAnchors.lean")


def _gate(script: str) -> bool:
    got = subprocess.run([sys.executable, "-I", "-c", script],
                         capture_output=True, text=True, timeout=30)
    lines = [ln for ln in got.stdout.splitlines() if ln.strip()]
    return got.returncode == 0 and bool(lines) and \
        lines[-1].endswith("VERIFIED True")


def _topic(key: str) -> EA.Topic:
    return next(tp for tp in EA.TOPICS if tp.key == key)


class TestTheDeclaredQuestions(unittest.TestCase):
    """E1-E5 at the anchor layer."""

    @classmethod
    def setUpClass(cls):
        items = {it.index: it for it in qc.outside()}
        cls.answers = {}
        for idx, topic, *_ in C.EXPLANATION_QUESTIONS:
            tp = EA.topic_of(items[idx].text)
            cls.answers[idx] = (tp, EA.read_topic(tp, items[idx].text)
                                if tp else None)

    def test_every_question_has_its_topic(self):
        for idx, topic, *_ in C.EXPLANATION_QUESTIONS:
            with self.subTest(index=idx):
                tp, _ = self.answers[idx]
                self.assertIsNotNone(tp)
                self.assertEqual(tp.key, topic)

    def test_answers_hold_the_fragment_and_the_scope(self):
        for idx, _, scope, frag, *_ in C.EXPLANATION_QUESTIONS:
            with self.subTest(index=idx):
                _, ans = self.answers[idx]
                self.assertTrue(ans.answered, ans.value)
                self.assertIn(frag, ans.value)
                self.assertEqual("refused EXPLANATION" in ans.value,
                                 scope == "ANCHORED")

    def test_registers_are_named(self):
        markers = {"elements": ("element",),
                   "nuclides": ("AME2020", "NUBASE2020"),
                   "proof_search": ("proof_search",),
                   "integer_decision": ("integer_decision",),
                   "none": ("no register row",)}
        for idx, _, _, _, regs, _ in C.EXPLANATION_QUESTIONS:
            with self.subTest(index=idx):
                _, ans = self.answers[idx]
                where = ans.column2 + " " + ans.backing
                for g in regs:
                    self.assertTrue(any(m in where for m in markers[g]),
                                    where)

    def test_disputes_exactly_as_declared(self):
        for idx, *_, disputes in C.EXPLANATION_QUESTIONS:
            with self.subTest(index=idx):
                _, ans = self.answers[idx]
                self.assertEqual(len(ans.disputes), len(disputes))
                for d in disputes:
                    self.assertTrue(any(d in x for x in ans.disputes))

    def test_every_script_verifies(self):
        for idx, *_ in C.EXPLANATION_QUESTIONS:
            with self.subTest(index=idx):
                _, ans = self.answers[idx]
                self.assertTrue(_gate(ans.script))


class TestTheControls(unittest.TestCase):
    """E4's controls: a false claim or an altered register row fails."""

    def test_every_control_that_applies_fails(self):
        applied = 0
        for idx, topic, *_ in C.EXPLANATION_QUESTIONS:
            tp = _topic(topic)
            for kind in EA.MUTATION_KINDS:
                ans = EA.mutated(tp, kind)
                if ans is None:
                    continue
                applied += 1
                with self.subTest(index=idx, kind=kind):
                    self.assertFalse(_gate(ans.script))
        self.assertGreater(applied, len(C.EXPLANATION_QUESTIONS))


class TestExactEnclosures(unittest.TestCase):
    """The outward-rounded enclosures the anchors compute with."""

    def test_enclosures_contain_their_value(self):
        lo, hi = EA.sqrt_bounds(Fraction(2))
        self.assertTrue(lo * lo <= 2 <= hi * hi and lo < hi)
        lo, hi = EA.cbrt_bounds(Fraction(3))
        self.assertTrue(lo ** 3 <= 3 <= hi ** 3 and lo < hi)
        lo, hi = EA.pi_bounds()
        self.assertTrue(Fraction(314159, 100000) < lo < hi
                        < Fraction(314160, 100000))
        lo, hi = EA.ln_bounds(Fraction(2))
        self.assertTrue(Fraction(6931, 10000) < lo < hi
                        < Fraction(6932, 10000))
        lo, hi = EA.exp_bounds(Fraction(1))
        self.assertTrue(Fraction(27182, 10000) < lo < hi
                        < Fraction(27183, 10000))


class TestTheNuclideRegister(unittest.TestCase):
    """E8: the read-back checks."""

    def test_read_back(self):
        reg = N.register()
        self.assertEqual(len(N.sources()), 2)
        self.assertEqual(EA.rnd(N.binding(1, 2), 3), "2224.566")
        measured = [(N.binding_per_nucleon(z, a), z, a)
                    for (z, a), v in reg.items()
                    if a > 1 and v.mass_excess_text and not v.estimated]
        self.assertEqual(max(measured)[1:], (28, 62))
        stable = sum(1 for v in reg.values() if v.half_life == "stbl")
        self.assertTrue(250 <= stable <= 260)

    def test_no_stable_technetium(self):
        self.assertFalse(any(N.is_stable(43, nu.a) for nu in N.isotopes(43)))


class TestReading(unittest.TestCase):
    """E6 and E7 at the anchor layer; the held-out record as measured."""

    def test_paraphrases_find_their_topic(self):
        for pid, text, topic in C.PARAPHRASES:
            with self.subTest(id=pid):
                tp = EA.topic_of(text)
                self.assertIsNotNone(tp)
                self.assertEqual(tp.key, topic)

    def test_held_out_as_measured(self):
        """Written after the first run, before any cue change: 5 of 35
        found their topic, and none found a wrong one."""
        found = [h for h, t, k in C.HELD_OUT if EA.topic_of(t)]
        wrong = [h for h, t, k in C.HELD_OUT
                 if EA.topic_of(t) and EA.topic_of(t).key != k]
        self.assertEqual(len(C.HELD_OUT), 35)
        self.assertEqual(wrong, [])
        self.assertGreaterEqual(len(found), 5)

    def test_near_misses_are_not_read(self):
        for i, text in enumerate(C.NOT_READ):
            with self.subTest(i=i):
                self.assertIsNone(EA.topic_of(text))

    def test_the_other_outside_questions_are_not_read(self):
        declared = {x[0] for x in C.EXPLANATION_QUESTIONS}
        for it in qc.outside():
            if it.index in declared:
                continue
            with self.subTest(index=it.index):
                self.assertIsNone(EA.topic_of(it.text))


class TestLean(unittest.TestCase):
    """E9 (the source half; the build is ``lake build``)."""

    @classmethod
    def setUpClass(cls):
        src = LEAN_FILE.read_text(encoding="utf-8")
        code = re.sub(r"/-.*?-/", "", src, flags=re.S)
        cls.code = re.sub(r"--[^\n]*", "", code)

    def test_named_theorems_and_no_sorry(self):
        for t in C.LEAN_THEOREMS:
            with self.subTest(theorem=t):
                self.assertRegex(self.code, rf"theorem\s+{t}\b")
        self.assertNotRegex(self.code, r"\bsorry\b")

    def test_technetium_table_is_the_register(self):
        rows = re.findall(r"\((\d+), \(([-\d/]+) : ℚ\), \(([-\d/]+) : ℚ\), "
                          r"\(([-\d/]+) : ℚ\)\)", self.code)
        self.assertEqual(len(rows), 28)
        for a, mo, tc, ru in rows:
            a = int(a)
            with self.subTest(a=a):
                for z, text in ((42, mo), (43, tc), (44, ru)):
                    self.assertEqual(Fraction(text),
                                     N.mass_excess(z, a,
                                                   allow_estimated=True))
                self.assertFalse(N.nuclide(43, a).estimated)


if __name__ == "__main__":
    unittest.main()
