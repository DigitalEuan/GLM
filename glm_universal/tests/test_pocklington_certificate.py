"""Tests for the Pocklington round (Phase 140): primes whose ``p - 1`` does
not split within the work budget, certified from a partial factorisation and
proved sound in ``RequestProject/GLM/PocklingtonCertificate.lean``
(``studies/POCKLINGTON_CERTIFICATE_STUDY.md``,
:mod:`glm_universal.evaluation.pocklington_certificate_cases`)."""

from __future__ import annotations

import unittest
from pathlib import Path

from glm_universal.evaluation import pocklington_certificate_cases as pkc
from glm_universal.evaluation import primality_certificate_cases as pcc
from glm_universal.reasoning import primality_certificate as pc
from glm_universal.reasoning import stepwise_script as ss
from glm_universal.runtime import stepwise
from glm_universal.runtime.session import GeometricSession

ROOT = Path(__file__).resolve().parents[3]
LEAN = ROOT / "overlay" / "glm_lean" / pkc.LEAN_FILE
M521 = 2 ** 521 - 1


class TestTheLeanFile(unittest.TestCase):
    """Q1 and Q5: the theorems the checker mirrors, and the kernel instance."""

    def test_file(self):
        text = LEAN.read_text(encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in pkc.LEAN_THEOREMS:
            with self.subTest(theorem=name):
                self.assertIn(f"theorem {name} ", text)

    def test_the_kernel_instance_is_the_tool_s_certificate(self):
        text = LEAN.read_text(encoding="utf-8")
        cert = pc.certify(M521)
        self.assertEqual(cert["kind"], "pocklington")
        for p, fs in cert["chain"]:
            fl = ", ".join(f"({q}, {e}, {a})" for q, e, a in fs)
            self.assertIn(f"({p}, [{fl}])", text)


def _script_reader():
    """``certified_verdict`` (and its ``gcd``) as the column-3 script defines
    them, taken from the generated script's own text."""
    src = ss._SCRIPT
    ns: dict = {}
    for name in ("certified_verdict", "gcd"):
        start = src.index(f"\ndef {name}(")
        end = src.index("\ndef ", start + 1)
        exec(src[start:end], ns)
    return ns["certified_verdict"]


class TestTheChecker(unittest.TestCase):
    """The Pocklington checker accepts what it should and nothing else."""

    @classmethod
    def setUpClass(cls):
        cls.cert = pc.certify(M521)

    def test_m521_is_certified(self):
        self.assertEqual(pc.check(M521, self.cert), "prime")

    def test_the_last_entry_is_a_partial_factorisation(self):
        p, fs = self.cert["chain"][-1]
        part = 1
        for q, e, _a in fs:
            part *= q ** e
        self.assertEqual(p, M521)
        self.assertLess(part, p - 1)
        self.assertLess(p, (part + 1) ** 2)

    def test_tampered_certificates_prove_nothing(self):
        for kind, bad in pkc.tampered(self.cert):
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    pc.check(M521, bad)

    def test_the_script_reader_agrees(self):
        reader = _script_reader()
        self.assertEqual(reader(M521, self.cert), "prime")
        for kind, bad in pkc.tampered(self.cert):
            with self.subTest(kind=kind):
                with self.assertRaises(AssertionError):
                    reader(M521, bad)

    def test_a_pratt_certificate_converts(self):
        """Every Pratt entry is a Pocklington entry with F = p - 1."""
        pratt = pc.certify(10 ** 12 + 39)
        chain = [[p, [[q, e, a] for q, e in fs]] for p, a, fs in pratt["chain"]]
        self.assertEqual(pc.check(10 ** 12 + 39,
                                  {"kind": "pocklington", "chain": chain}),
                         "prime")

    def test_a_composite_is_never_certified_prime(self):
        for n in (561, 1105, 1729, 2 ** 523 - 1,
                  (2 ** 89 - 1) * (2 ** 107 - 1)):
            with self.subTest(n=n):
                self.assertEqual(pc.verdict(n)[0], "not prime")

    def test_numbers_phase_139_certified_keep_their_certificate(self):
        for n in (10 ** 12 + 39, 2 ** 61 - 1, 2 ** 127 - 1):
            with self.subTest(n=n):
                pc.POCKLINGTON = False
                try:
                    before = pc.certify(n)
                finally:
                    pc.POCKLINGTON = True
                self.assertEqual(pc.certify(n), before)

    def test_small_numbers_still_agree_with_trial_division(self):
        for n in range(2, 1500):
            with self.subTest(n=n):
                self.assertEqual(pc.check(n, pc.certify(n)), pcc._trial(n))


class TestTheNPlusOneCertificate(unittest.TestCase):
    """Part B: the N+1 (Lucas) entry and the mixed chain."""

    @classmethod
    def setUpClass(cls):
        from math import factorial
        cls.n = factorial(33) - 1
        cls.cert = pc.certify(cls.n)

    def test_33_factorial_minus_1_is_certified(self):
        self.assertEqual(self.cert["kind"], "lucas")
        self.assertEqual(pc.check(self.n, self.cert), "prime")
        self.assertEqual(len(self.cert["chain"][-1]), 3)

    def test_the_kernel_instance_is_the_tool_s_certificate(self):
        text = (LEAN.parent / Path(pkc.LEAN_FILE_B).name).read_text(
            encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in pkc.LEAN_THEOREMS_B:
            with self.subTest(theorem=name):
                self.assertIn(f"theorem {name} ", text)
        for e in self.cert["chain"]:
            if len(e) == 2:
                s = f".pock {e[0]} [" + ", ".join(
                    f"({q}, {x}, {a})" for q, x, a in e[1]) + "]"
            else:
                s = f".lucas {e[0]} {e[1]} [" + ", ".join(
                    f"({q}, {x})" for q, x in e[2]) + "]"
            self.assertIn(s, text)

    def test_tampered_certificates_prove_nothing(self):
        reader = _script_reader()
        for kind, bad in pkc.tampered(self.cert):
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    pc.check(self.n, bad)
                with self.assertRaises(AssertionError):
                    reader(self.n, bad)

    def test_the_script_reader_agrees(self):
        self.assertEqual(_script_reader()(self.n, self.cert), "prime")

    def test_the_control_restores_the_refusal(self):
        with pkc.flags(True, False):
            with self.assertRaises(pc.NoCertificate):
                pc.certify(self.n)

    def test_a_mersenne_prime_by_n_plus_1(self):
        """``2^p - 1`` has ``n + 1 = 2^p``: one factor, one entry."""
        n = 2 ** 89 - 1
        chain = [[2, []], [n, 0, [[2, 89]]]]
        for big_p in range(3, 200):
            chain[1][1] = big_p
            if pc._check_mchain(chain):
                break
        self.assertEqual(pc.check(n, {"kind": "lucas", "chain": chain}),
                         "prime")

    def test_a_composite_never_passes_an_n_plus_1_entry(self):
        for n in (91, 341, 561, 1105, 8911):
            for big_p in range(3, 60):
                fs: dict = {}
                m, d = n + 1, 2
                while m > 1:
                    while m % d == 0:
                        fs[d] = fs.get(d, 0) + 1
                        m //= d
                    d += 1
                with self.subTest(n=n, P=big_p):
                    self.assertFalse(pc._check_lentry(
                        set(fs), n, big_p, [[q, e] for q, e in fs.items()]))


class TestTheStep(unittest.TestCase):
    """The ``prime`` step on a number Phase 139 refused."""

    @classmethod
    def setUpClass(cls):
        cls.session = GeometricSession()

    def test_m521_is_answered(self):
        a = stepwise.answer(self.session, "is 2 to the power 521 minus 1 prime")
        self.assertTrue(a.answered)
        self.assertEqual(a.value, "prime")
        step = a.chain.steps[-1]
        self.assertEqual(step.detail["certificate"]["kind"], "pocklington")
        self.assertTrue(ss.step_check(step, a.chain.steps)[0])

    def test_a_tampered_certificate_fails_the_gate(self):
        a = stepwise.answer(self.session, "is 2 to the power 521 minus 1 prime")
        s = a.chain.steps[-1]
        for kind, bad in pkc.tampered(dict(s.detail["certificate"])):
            with self.subTest(kind=kind):
                t = ss.Step(s.index, s.op, s.inputs, s.value, s.label,
                            dict(s.detail, certificate=bad), s.origin)
                steps = list(a.chain.steps[:-1]) + [t]
                self.assertFalse(ss.step_check(t, steps)[0])


if __name__ == "__main__":
    unittest.main()
