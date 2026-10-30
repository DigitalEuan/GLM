"""Phase 106 -- derivations and proofs.

``studies/DERIVATION_STUDY.md`` declares marks R1-R9 before any code
(:mod:`glm_universal.evaluation.derivation_cases`).  These tests hold the
facts the round rests on at a sampled scale; the full measurement is
``python3 -m glm_universal.tools derivation``.
"""

from __future__ import annotations

import unittest

from glm_universal.evaluation import derivation_cases as C
from glm_universal.evaluation import question_set_b_cases as qc
from glm_universal.reasoning import derivation as D
from glm_universal.reasoning import proof_search as PS
from glm_universal.reasoning import symbolic as S
from glm_universal.runtime import derivation_frames as DF
from glm_universal.runtime import derivation_report as R
from glm_universal.runtime import question_frames as qf


class TestProver(unittest.TestCase):

    def test_curry_is_constructive(self):
        v = PS.decide(*PS.parse_sequent("C <-> (C -> F) |- F"))
        self.assertEqual(v.kind, "intuitionistic")
        self.assertTrue(PS.check_proof(v.proof))

    def test_excluded_middle_is_classical_with_a_kripke_model(self):
        v = PS.decide(*PS.parse_sequent("|- p | ~p"))
        self.assertEqual(v.kind, "classical")
        self.assertEqual(v.excluded_middle, ("p",))
        self.assertIsNotNone(v.kripke)

    def test_non_theorem_has_a_countermodel(self):
        v = PS.decide(*PS.parse_sequent("p -> q, q |- p"))
        self.assertEqual(v.kind, "NOT_VALID")
        self.assertEqual(v.valuation, {"p": False, "q": True})

    def test_a_tampered_proof_is_rejected(self):
        v = PS.decide(*PS.parse_sequent("p -> q, q -> r |- p -> r"))
        bad = PS.Proof("R|1", v.proof.context, v.proof.goal,
                       v.proof.principal, v.proof.premises)
        self.assertFalse(PS.check_proof(bad))

    def test_declared_proofs(self):
        self.assertTrue(R.proof_marks(run_scripts=False)["met"])

    def test_battery_sample(self):
        out = R.prover_battery(150)
        self.assertEqual(out["unsound"], 0)
        self.assertEqual(out["gaps"], 0)
        self.assertEqual(out["script_failures"], 0)


class TestDerivations(unittest.TestCase):

    def test_declared_motion(self):
        self.assertTrue(R.motion_marks(run_scripts=False)["met"])

    def test_declared_transfer(self):
        self.assertTrue(R.transfer_marks(run_scripts=False)["met"])

    def test_declared_profiles(self):
        self.assertTrue(R.profile_marks(run_scripts=False)["met"])

    def test_declared_refusals(self):
        self.assertTrue(R.refusal_marks()["met"])

    def test_a_given_moves_the_answer(self):
        # a stiffer middle spring moves the second frequency
        mo = D.equations_of_motion(
            "(1/2)*m*(x1_dot^2 + x2_dot^2) - (1/2)*k*(x1^2 + x2^2) "
            "- (1/2)*c*(x2 - x1)^2", ["x1", "x2"], True)
        self.assertEqual(len(mo.frequencies), 2)
        self.assertTrue(any((f - S.parse("(k + 2*c)/m")).is_zero()
                            for f in mo.frequencies))

    def test_a_level_tank_is_a_first_order_lag(self):
        tr = D.transfer_functions(["A*d(h)/dt = qi - h/R"], ["qi"], ["h"])
        self.assertTrue((tr.functions[("h", "qi")] -
                         S.parse("R/(A*R*s + 1)")).is_zero())


class TestReadings(unittest.TestCase):

    def test_scripts_verify_and_mutants_fail(self):
        for q in (C.PROOFS[0][1], C.MOTION[2][1], C.TRANSFER[0][1],
                  C.PROFILES[2][1], C.PROOFS[-1][1]):
            rd = DF.read_operation(q)
            self.assertTrue(qf.run_gate(rd.script, 20)[0], q)
            mut = DF.mutated_operation(q)
            self.assertFalse(qf.run_gate(mut.script, 20)[0], q)

    def test_outside_class_p(self):
        items = qc.outside()
        for idx, frag in C.OUTSIDE_P:
            rd = qf.read(items[idx].text)
            self.assertTrue(rd.answered, idx)
            self.assertIn(frag, rd.value, idx)
            self.assertTrue(rd.gate[0], idx)

    def test_a_triple_pendulum_is_read_too(self):
        text = ("A triple pendulum of three identical bobs of mass m on "
                "strings of identical length l: formulate the Lagrangian "
                "and the equations of motion using the small-angle "
                "approximation.")
        rd = qf.read(text)
        self.assertEqual(rd.frame, "chain_pendulum")
        self.assertTrue(rd.answered)
        self.assertTrue(rd.gate[0])

    def test_the_switch_restores_the_frame_layer(self):
        text = C.OUTSIDE_P[0]
        saved = qf.DERIVATIONS
        try:
            qf.DERIVATIONS = False
            self.assertIsNone(qf.frame_of(qc.outside()[text[0]].text))
            self.assertIsNone(qf.frame_of(C.PROOFS[0][1]))
        finally:
            qf.DERIVATIONS = saved


class TestLean(unittest.TestCase):

    def test_lean_file(self):
        self.assertTrue(R.lean_mark()["met"])


if __name__ == "__main__":
    unittest.main()
