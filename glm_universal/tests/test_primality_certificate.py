"""Tests for the primality-certificate round (Phase 139): the stepwise
planner's ``prime`` step past 10^12 by a factor, a Fermat witness or a Pratt
certificate, each proved sound in ``RequestProject/GLM/PrimalityCertificate
.lean`` (``studies/PRIMALITY_CERTIFICATE_STUDY.md``,
:mod:`glm_universal.evaluation.primality_certificate_cases`)."""

from __future__ import annotations

import unittest
from pathlib import Path

from glm_universal.evaluation import primality_certificate_cases as pcc
from glm_universal.reasoning import primality_certificate as pc
from glm_universal.reasoning import stepwise_script as ss
from glm_universal.runtime import stepwise
from glm_universal.runtime.session import GeometricSession

ROOT = Path(__file__).resolve().parents[3]
LEAN = ROOT / "overlay" / "glm_lean" / pcc.LEAN_FILE


class TestTheLeanFile(unittest.TestCase):
    """P1: the soundness theorems the checker mirrors."""

    def test_file(self):
        text = LEAN.read_text(encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in pcc.LEAN_THEOREMS:
            with self.subTest(theorem=name):
                self.assertIn(f"theorem {name} ", text)

    def test_the_kernel_instance_is_the_tool_s_certificate(self):
        """The certificate checked by the kernel for 10^12 + 39 is the one
        the run-time certifier produces."""
        text = LEAN.read_text(encoding="utf-8")
        cert = pc.certify(10 ** 12 + 39)
        for p, a, fs in cert["chain"]:
            fl = ", ".join(f"({q}, {e})" for q, e in fs)
            self.assertIn(f"({p}, {a}, [{fl}])", text)


class TestTheChecker(unittest.TestCase):
    """The checker accepts what it should and nothing else."""

    def test_small_numbers_agree_with_trial_division(self):
        for n in range(-3, 3000):
            with self.subTest(n=n):
                self.assertEqual(pc.check(n, pc.certify(n)), pcc._trial(n))

    def test_two_and_three(self):
        self.assertEqual(pc.certify(2),
                         {"kind": "pratt", "chain": [[2, 1, []]]})
        self.assertEqual(pc.check(3, pc.certify(3)), "prime")

    def test_carmichael_numbers_are_caught(self):
        for n in (561, 1105, 1729, 1042789205881):
            with self.subTest(n=n):
                self.assertEqual(pc.verdict(n)[0], "not prime")

    def test_fermat_witness_names_no_factor(self):
        n = (2 ** 89 - 1) * (2 ** 107 - 1)
        cert = pc.certify(n)
        self.assertEqual(cert["kind"], "fermat")
        self.assertEqual(pc.check(n, cert), "not prime")

    def test_tampered_certificates_prove_nothing(self):
        for n in (10 ** 12 + 39, 2 ** 61 - 1, 10 ** 12 + 1,
                  (2 ** 61 - 1) * (2 ** 89 - 1)):
            for kind, bad in pcc._tampered(pc.certify(n)):
                with self.subTest(n=n, kind=kind):
                    with self.assertRaises(ValueError):
                        pc.check(n, bad)

    def test_a_certificate_for_one_number_is_not_one_for_another(self):
        cert = pc.certify(10 ** 12 + 39)
        with self.assertRaises(ValueError):
            pc.check(10 ** 12 + 37, cert)

    def test_the_budget_refuses_rather_than_guesses(self):
        """Phase 139's behaviour, under the Phase 140 control."""
        pc.POCKLINGTON = False
        try:
            with self.assertRaises(pc.NoCertificate) as ctx:
                pc.certify(2 ** 521 - 1)
        finally:
            pc.POCKLINGTON = True
        self.assertGreater(ctx.exception.cofactor, 1)


class TestTheStep(unittest.TestCase):
    """The ``prime`` step past 10^12."""

    @classmethod
    def setUpClass(cls):
        cls.session = GeometricSession()

    def test_past_the_old_ceiling(self):
        a = stepwise.answer(self.session, "is 2 to the power 127 minus 1 prime")
        self.assertTrue(a.answered)
        self.assertEqual(a.value, "prime")
        step = a.chain.steps[-1]
        self.assertEqual(step.detail["certificate"]["kind"], "pratt")
        self.assertTrue(ss.step_check(step, a.chain.steps)[0])

    def test_below_the_line_is_unchanged(self):
        a = stepwise.answer(self.session, "is 999999999989 prime")
        if a.answered:
            self.assertNotIn("certificate", a.chain.steps[-1].detail)

    def test_the_control_restores_the_refusal(self):
        stepwise.CERTIFIED_PRIMALITY = False
        try:
            a = stepwise.answer(self.session, "is 1000000000039 prime")
        finally:
            stepwise.CERTIFIED_PRIMALITY = True
        self.assertFalse(a.answered)

    def test_a_prime_is_read(self):
        a = stepwise.answer(self.session, "is 1000000000039 a prime")
        self.assertTrue(a.answered)
        self.assertEqual(a.value, "prime")

    def test_the_budget_is_a_refusal(self):
        """Phase 139's behaviour, under the Phase 140 control."""
        pc.POCKLINGTON = False
        try:
            a = stepwise.answer(self.session,
                                "is 2 to the power 521 minus 1 prime")
        finally:
            pc.POCKLINGTON = True
        self.assertFalse(a.answered)
        self.assertIn("NO_CERTIFICATE", a.summary())

    def test_a_lie_about_the_verdict_fails_the_gate(self):
        a = stepwise.answer(self.session, "is 1000000000001 prime")
        s = a.chain.steps[-1]
        lied = ss.Step(s.index, s.op, s.inputs, "prime", s.label, s.detail,
                       s.origin)
        steps = list(a.chain.steps[:-1]) + [lied]
        self.assertFalse(ss.step_check(lied, steps)[0])


if __name__ == "__main__":
    unittest.main()
