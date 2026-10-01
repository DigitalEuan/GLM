"""Tests for the carried fork (:mod:`glm_universal.reasoning.carried_fork`):
the six deep-hole candidates carried until a later decision resolves them,
held to the marks ``studies/CARRIED_FORK_STUDY.md`` declared before the
module existed, and the Python-dialect builtins that reach it."""

from __future__ import annotations

import unittest
from fractions import Fraction

import pytest

from glm_universal.reasoning import carried_fork as cf
from glm_universal.reasoning import python_speech as sp
from glm_universal.reasoning import python_substrate as ps
from glm_universal.substrate.mog import GOLAY_MASKS


def _octad_split():
    octad = next(w for w in GOLAY_MASKS if bin(w).count("1") == 8)
    sup = [i for i in range(24) if (octad >> i) & 1]
    return (octad, sum(1 << i for i in sup[:4]), sum(1 << i for i in sup[4:]))


class TestTheObject(unittest.TestCase):

    def test_a_deep_hole_read_carries_six(self):
        fork = cf.carry(0b1111)
        self.assertEqual(fork.weight, 4)
        self.assertEqual(len(fork.candidates), 6)
        self.assertEqual(fork.status, "open")
        self.assertIsNone(fork.value)
        tets = [fork.tetrad(c) for c in fork.candidates]
        union = 0
        for t in tets:
            self.assertEqual(bin(t).count("1"), 4)
            self.assertFalse(union & t)
            union |= t
        self.assertEqual(union, cf.FULL)

    def test_a_correctable_read_is_resolved_at_once(self):
        c = GOLAY_MASKS[77]
        fork = cf.carry(c ^ 0b101)
        self.assertEqual(fork.status, "resolved")
        self.assertEqual(fork.value, c)

    def test_the_ledger_partitions_and_names_every_removal(self):
        c = GOLAY_MASKS[300]
        fork = cf.carry(c ^ 0b1111).restrict_to_cases([c, GOLAY_MASKS[5]])
        self.assertTrue(fork.partition_holds())
        for e in fork.ledger:
            self.assertEqual(e.stage, "context")
            self.assertTrue(e.reason and e.assumption)
        self.assertEqual(fork.assumptions, (cf.CLOSED_WORLD,))

    def test_nothing_is_chosen_by_order(self):
        octad, e1, _ = _octad_split()
        fork = cf.carry(e1).restrict_to_cases([0, octad])
        self.assertEqual(fork.status, "open")
        self.assertEqual(set(fork.live), {0, octad})

    def test_an_empty_fork_is_contradicted(self):
        fork = cf.carry(0b1111).restrict_to_cases([GOLAY_MASKS[4095]])
        self.assertEqual(fork.status, "contradicted")

    def test_later_decisions_commute(self):
        octad, e1, e2 = _octad_split()
        a = cf.carry(e1).intersect(cf.carry(e2)).rule_out_sure(e1 | 0b1)
        b = cf.carry(e1).rule_out_sure(e1 | 0b1).intersect(cf.carry(e2))
        self.assertEqual(set(a.live), set(b.live))

    def test_an_unknown_stage_is_refused(self):
        with self.assertRaises(ValueError):
            cf.carry(0b1111).prune("guess", lambda c: True, "r", "a")


class TestTheMarks(unittest.TestCase):

    def test_k2_reproduces_x1(self):
        k2 = cf.k2_second_reading()
        self.assertEqual((k2["double_reads"], k2["answered"], k2["wrong"]),
                         (4224, 4224, 0))
        self.assertTrue(k2["witness_is_truth_and_octad"])
        self.assertTrue(k2["passed"])

    def test_k3_unsure_set_never_wrong(self):
        k3 = cf.k3_unsure()
        self.assertTrue(k3["passed"])
        for row in k3["rows"]:
            self.assertEqual(row["wrong"], 0)
            if row["unsure_size"] <= 7:
                self.assertEqual(row["answered"], row["reads"])

    def test_k1_small_case_sets(self):
        k1 = cf.k1_context(sizes=(2, 4))
        for row in k1["rows"]:
            self.assertEqual(row["wrong"], 0)
            self.assertEqual(row["control_answered_on_sample"], 0)
            self.assertEqual(row["hostile_control_answered"], 0)
        self.assertEqual(k1["rows"][0]["answered"], 21112)

    def test_k4a_sample(self):
        k4a = cf.k4a_hard_lift(limit=8)
        self.assertEqual(k4a["certified_a1_24_with_48"], 8)

    def test_escalation_is_an_estimate_beside_the_fork(self):
        words, errs = cf.x1_probe()
        c, e = words[3], errs[5]
        fork = cf.carry(c ^ e)
        esc = cf.escalate(fork, cf.soft_reading(0, c, e))
        self.assertEqual(fork.status, "open")          # untouched
        self.assertEqual(set(esc.nearest), set(esc.euclidean_nearest))
        self.assertTrue(all(isinstance(d, Fraction) for _, d in esc.distances))

    @pytest.mark.exhaustive
    def test_the_whole_report(self):
        report = cf.carried_fork_report(full=True)
        self.assertEqual(report["met"], ["K2", "K3", "K4a", "K4c"])
        self.assertEqual(report["not_met"], ["K1", "K4b"])
        self.assertEqual(report["K1"]["wrong"], 0)
        self.assertEqual(report["K4b"]["certified_cut_wrong"], 0)
        self.assertEqual(report["K4a"]["certified_a1_24_with_48"], 1771)


class TestTheDialect(unittest.TestCase):

    def _run(self, source):
        return sp.speak(source)

    def _cpython(self, source):
        ns = {}
        exec(ps.PRELUDE, ns)
        return ns["run_source"](source)

    def test_resolve_answers_where_classify_refuses(self):
        src = ("s = golay_encode(1) ^ 0b1111\n"
               "resolve(s, golay_encode(1), golay_encode(2))")
        p = self._run(src)
        self.assertIsNone(p.refusal)
        self.assertEqual(p.value, 0)
        self.assertEqual(self._cpython(src), 0)
        self.assertTrue(any("closed-world" in s.language for s in p.steps))
        q = self._run(src.replace("resolve", "classify"))
        self.assertEqual(q.refusal, "AMBIGUOUS")

    def test_resolve_refuses_an_open_fork_by_name(self):
        octad, e1, _ = _octad_split()
        p = self._run(f"resolve({e1}, 0, {octad})")
        self.assertEqual(p.refusal, "AMBIGUOUS")

    def test_agree_and_resolve_unsure(self):
        c = ps.golay_encode(5)
        p = self._run(f"agree({c ^ 0b1111}, {c ^ 0b111000000000000000000001})")
        self.assertEqual(p.value, c)
        q = self._run(f"resolve_unsure({c ^ 0b1111}, 0b11111)")
        self.assertEqual(q.value, c)
        octad, e1, e2 = _octad_split()
        self.assertEqual(self._run(f"agree({e1}, {e2})").refusal, "AMBIGUOUS")

    def test_nearest_carries_the_six(self):
        p = self._run("nearest(0b1111)")
        self.assertEqual(len(p.value), 6)
        self.assertEqual(p.value, self._cpython("nearest(0b1111)"))

    def test_the_payload_verifies(self):
        p = self._run("s = golay_encode(1) ^ 0b1111\n"
                      "resolve(s, golay_encode(1), golay_encode(2))")
        self.assertTrue(sp.verify_payload(p)["verified"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
