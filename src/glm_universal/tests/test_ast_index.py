"""The AST address as a retrieval key (Phase 105), on the frozen index
declared in ``studies/AST_INDEX_STUDY.md``.

The census figures are read from the stored report when it is current
(``tools ast-index --write``); the measurement is re-taken from the snapshot
here once and must equal the stored one (mark A1).
"""

from __future__ import annotations

import unittest
from pathlib import Path

from glm_universal.evaluation import ast_index_cases as C
from glm_universal.reasoning import ast_index as ai
from glm_universal.runtime import ast_index_frames as aif
from glm_universal.runtime import ast_index_report as air
from glm_universal.runtime import question_frames as qf

ROOT = Path(__file__).resolve().parents[3]
LEAN = ROOT / "src" / "lean" / ai.LEAN_FILE

_REPORT = None


def report():
    global _REPORT
    if _REPORT is None:
        _REPORT = air.current() or air.ast_index_report()
    return _REPORT


class TestTheSnapshot(unittest.TestCase):

    def test_intact(self):
        state = ai.frozen_state()
        self.assertTrue(state["present"])
        self.assertTrue(state["intact"])
        self.assertEqual(11669, state["sites"])
        self.assertEqual({"live": 3438, "archive": 8231}, state["per_corpus"])

    def test_every_site_is_admitted(self):
        for row in ai.sites()[::97]:
            ai.admitted_form(row[4])

    def test_the_stored_report_is_current(self):
        self.assertEqual("fresh", air.state()["verdict"])

    def test_measurement_retaken_equals_stored(self):
        stored = report()["measure"]
        self.assertEqual(stored, _json_round(ai.measure(stride=C.STRIDE)))


def _json_round(obj):
    import json
    return json.loads(json.dumps(obj, sort_keys=True, default=str))


class TestTheRelation(unittest.TestCase):

    def test_declared_pairs(self):
        errors = {(a, b) for a, b, _ in C.DECLARATION_ERRORS}
        for a, b, declared in C.MATCH_PAIRS:
            got = ai.structurally_equal(a, b)
            self.assertEqual(got, ai.reference_equal(a, b), (a, b))
            if (a, b) in errors:
                self.assertNotEqual(declared, got)
            else:
                self.assertEqual(declared, got, (a, b))

    def test_witness_renaming(self):
        f = ai.admitted_form("x * x + y * y")
        g = ai.admitted_form("q * q + p * p")
        self.assertEqual({"x": "q", "y": "p"}, ai.match(f, g))

    def test_bucket_key_invariant(self):
        text = "counts.get(row['class'], 0) + 1 * k"
        key = ai.bucket_key(ai.admitted_form(text))
        for kind, _ in C.PERTURBATIONS:
            other = ai.perturb(text, kind)
            self.assertEqual(key, ai.bucket_key(ai.admitted_form(other)))
            self.assertTrue(ai.structurally_equal(text, other))

    def test_function_names_are_not_renamed(self):
        self.assertEqual("len(zq0_) - 1", ai.rename_text("len(s) - 1"))

    def test_refusal_codes(self):
        for text, code in (("a +", "NOT_AN_EXPRESSION"),
                           ("[x for x in y]", "OUTSIDE_INDEX"),
                           ("f(x)", "NO_ARITHMETIC"), ("-x", "TOO_SMALL")):
            with self.assertRaises(ai.IndexRefusal) as got:
                ai.admitted_form(text)
            self.assertEqual(code, got.exception.code)


class TestTheMeasurement(unittest.TestCase):

    def test_figures(self):
        m = report()["measure"]
        self.assertEqual(467, m["queries"])
        self.assertEqual({"bucket": 467, "match": 467, "v1": 373},
                         m["invariance"]["both"])
        self.assertEqual(467, m["hits"]["ast_v2"]["1"])
        self.assertEqual(343, m["hits"]["text"]["1"])
        self.assertEqual(0, m["audit"]["disagreements"])
        self.assertEqual(0, m["soundness"]["failures"])
        self.assertEqual(23, m["v1_false_merges"])

    def test_marks(self):
        outcomes = {k: v["outcome"] for k, v in report()["marks"].items()}
        self.assertEqual({"A1": "met", "A2": "not met", "A3": "met",
                          "A4": "not met", "A5": "met", "A6": "met",
                          "A7": "met"}, outcomes)


class TestTheOperation(unittest.TestCase):

    Q = "where is `x * x + y * y` computed?"

    def test_answer_and_gate(self):
        reading = qf.read(self.Q)
        self.assertTrue(reading.answered)
        self.assertTrue(reading.value.startswith("6 sites"))
        self.assertTrue(reading.gate[0])

    def test_mutant_fails(self):
        self.assertFalse(qf.run_gate(aif.mutated(self.Q).script)[0])

    def test_empty_answer_verifies_and_its_mutant_fails(self):
        q = "where is `zz_unused_name * 7919 + 104729` computed?"
        reading = qf.read(q)
        self.assertTrue(reading.value.startswith("no site"))
        self.assertTrue(reading.gate[0])
        self.assertFalse(qf.run_gate(aif.mutated(q).script)[0])

    def test_corpus_phrasings(self):
        self.assertEqual("archive", aif.match_raw(
            "where in the archive is `a + b * 2` computed?")["corpus"])
        self.assertEqual("live", aif.match_raw(
            "where in the live code is `a + b * 2` computed?")["corpus"])
        self.assertIsNone(aif.match_raw("where is the golay code computed?"))

    def test_switch_restores_the_layer(self):
        qf.AST_INDEX = False
        try:
            got = qf.frame_of(self.Q)
            self.assertTrue(got is None or got[0].name != "ast_index")
        finally:
            qf.AST_INDEX = True


class TestLean(unittest.TestCase):

    def test_lean_file(self):
        text = LEAN.read_text(encoding="utf-8")
        for name in ("structEq_sound", "bucket_complete", "key_rename",
                     "key_commEq", "key_sub_ne_add", "sub_not_comm",
                     "string_append_not_comm", "assoc_by_renaming"):
            self.assertIn(f"theorem {name}", text)
        self.assertNotIn("sorry", text)


if __name__ == "__main__":
    unittest.main()
