"""Phase 107 -- the rest of track P.

``studies/DERIVATION_TWO_STUDY.md`` declares marks Q1-Q11 before any code
(:mod:`glm_universal.evaluation.derivation_two_cases`).  These tests hold the
facts the round rests on at a sampled scale; the full measurement is
``python3 -m glm_universal.tools derivation-two``.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.evaluation import derivation_two_cases as C
from glm_universal.evaluation import question_set_b_cases as qc
from glm_universal.reasoning import coding_theory as CT
from glm_universal.reasoning import fft_derivation as FD
from glm_universal.reasoning import info_inequality as II
from glm_universal.runtime import derivation_two_frames as DF
from glm_universal.runtime import derivation_two_report as R
from glm_universal.runtime import question_frames as qf


class TestInequalities(unittest.TestCase):

    def test_subadditivity_has_a_certificate(self):
        v = II.decide(II.parse_problem("|- H(X) + H(Y) >= H(X,Y)"))
        self.assertEqual(v.kind, "proved")
        self.assertEqual(v.lines(), ["H(X) + H(Y) - H(X,Y) = I(X;Y)"])

    def test_superadditivity_has_a_counterexample(self):
        v = II.decide(II.parse_problem("|- H(X,Y) >= H(X) + H(Y)"))
        self.assertEqual(v.kind, "NOT_VALID")
        self.assertIsNotNone(v.distribution)

    def test_declared_inequalities(self):
        self.assertTrue(R.inequality_marks(run_scripts=False)["met"])

    def test_battery_sample(self):
        out = R.inequality_battery(60)
        self.assertEqual(out["unsound"], 0)
        self.assertEqual(out["undecided"], 0)
        self.assertEqual(out["script_failures"], 0)


class TestCodes(unittest.TestCase):

    def test_an_ambiguous_code_and_its_string(self):
        words = ["0", "01", "10"]
        self.assertFalse(CT.sardinas_patterson(words)[0])
        s, a, b = CT.ambiguous_string(words)
        self.assertEqual("".join(a), s)
        self.assertEqual("".join(b), s)
        self.assertNotEqual(a, b)

    def test_kraft_and_the_canonical_code(self):
        self.assertEqual(CT.kraft_sum([1, 2, 2], 2), Fraction(1))
        code = CT.canonical_prefix_code([1, 2, 3, 3])
        self.assertEqual(code, ["0", "10", "110", "111"])
        self.assertTrue(CT.is_prefix_free(code))

    def test_declared_codes_and_rate_distortion(self):
        self.assertTrue(R.code_marks(run_scripts=False)["met"])
        self.assertTrue(R.rd_marks(run_scripts=False)["met"])

    def test_battery_sample(self):
        out = R.code_battery(80)
        self.assertEqual(out["disagreements"], 0)
        self.assertEqual(out["kraft_violations"], 0)
        self.assertEqual(out["construction_failures"], 0)


class TestOperations(unittest.TestCase):

    def test_declared_maxent_eigen_and_the_rest(self):
        self.assertTrue(R.maxent_marks(run_scripts=False)["met"])
        self.assertTrue(R.eigen_marks(run_scripts=False)["met"])
        self.assertTrue(R.other_marks(run_scripts=False)["met"])

    def test_declared_refusals(self):
        self.assertTrue(R.refusal_marks()["met"])

    def test_an_eight_point_fft(self):
        f = FD.derive_fft(8)
        self.assertEqual(f.n, 8)
        self.assertEqual(f.stages, 3)
        self.assertEqual(f.output_order, [0, 4, 2, 6, 1, 5, 3, 7])


class TestReadings(unittest.TestCase):

    def test_scripts_verify_and_mutants_fail(self):
        for q in (C.INEQUALITIES[0][1], C.CODES[0][1],
                  C.RATE_DISTORTION[0][1], C.MAXENT[0][1], C.EIGEN[0][1],
                  C.SCATTERING[0][1]):
            rd = DF.read_operation(q)
            self.assertTrue(qf.run_gate(rd.script, 20)[0], q)
            mut = DF.mutated_operation(q)
            self.assertFalse(qf.run_gate(mut.script, 20)[0], q)

    def test_outside_rest_of_class_p(self):
        items = qc.outside()
        for idx, frag in C.OUTSIDE_P2:
            rd = qf.read(items[idx].text)
            self.assertTrue(rd.answered, idx)
            self.assertIn(frag, rd.value, idx)
            self.assertTrue(rd.gate[0], idx)

    def test_declared_refusals_stay_unframed(self):
        # Phase 120 answers the three with its explanation frames, tried
        # after every other frame (``explanation_cases.PREVIOUSLY_REFUSED``);
        # no frame before them reads any of the three.
        items = qc.outside()
        saved = qf.EXPLANATIONS
        try:
            qf.EXPLANATIONS = False
            for idx in C.STAYS_REFUSED:
                self.assertIsNone(qf.frame_of(items[idx].text), idx)
        finally:
            qf.EXPLANATIONS = saved

    def test_the_switch_restores_the_frame_layer(self):
        idx = C.OUTSIDE_P2[0][0]
        saved = qf.DERIVATIONS_TWO
        try:
            qf.DERIVATIONS_TWO = False
            self.assertIsNone(qf.frame_of(qc.outside()[idx].text))
            self.assertIsNone(qf.frame_of(C.CODES[0][1]))
        finally:
            qf.DERIVATIONS_TWO = saved


class TestLean(unittest.TestCase):

    def test_lean_file(self):
        self.assertTrue(R.lean_mark()["met"])


if __name__ == "__main__":
    unittest.main()
