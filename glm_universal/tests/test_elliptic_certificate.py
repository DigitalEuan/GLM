"""Tests for the elliptic-curve round (Phase 141): primes that neither
``p - 1`` nor ``p + 1`` reaches within the work budget, certified by an
elliptic-curve chain proved sound in
``RequestProject/GLM/EllipticCertificate.lean``
(``studies/ELLIPTIC_CERTIFICATE_STUDY.md``,
:mod:`glm_universal.evaluation.elliptic_certificate_cases`).

The prime used here, ``EXPLORED``, is one of the exploration primes declared
in the cases module (the next probable prime after an integer drawn by a
seeded generator outside the package); it is not a held-out number.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from glm_universal.evaluation import elliptic_certificate_cases as ecc
from glm_universal.reasoning import elliptic_certificate as ec
from glm_universal.reasoning import primality_certificate as pc
from glm_universal.reasoning import stepwise_script as ss
from glm_universal.runtime import stepwise
from glm_universal.runtime.session import GeometricSession

ROOT = Path(__file__).resolve().parents[3]
LEAN = ROOT / "overlay" / "glm_lean" / ecc.LEAN_FILE
#: Refused by the Phase 140 certifier: neither p - 1 nor p + 1 splits.
EXPLORED = 867571890575302897545147419291896285465686746712294895001999


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


class TestTheLeanFile(unittest.TestCase):
    """E1 and E5: the theorems the checker mirrors, and the kernel instance."""

    def test_file(self):
        text = LEAN.read_text(encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in ecc.LEAN_THEOREMS + (ecc.INSTANCE_THEOREM,):
            with self.subTest(theorem=name):
                self.assertIn(f"theorem {name} ", text)

    def test_the_kernel_instance_is_the_tool_s_certificate(self):
        text = LEAN.read_text(encoding="utf-8")
        n = next(n for cid, _nm, n, _w in ecc.HELD_OUT
                 if cid == ecc.INSTANCE_ID)
        cert = ec.elliptic(n)
        for e in cert["chain"]:
            with self.subTest(entry=e[0]):
                self.assertIn(ecc.lean_entry(e), text)


class TestClassPolynomials(unittest.TestCase):
    """The fixed-point computation gives the published class polynomials."""

    def test_known_polynomials(self):
        self.assertEqual(ec.class_polynomial(-7), (3375, 1))
        self.assertEqual(ec.class_polynomial(-163),
                         (640320 ** 3, 1))
        self.assertEqual(ec.class_polynomial(-15), (-121287375, 191025, 1))
        self.assertEqual(ec.class_polynomial(-23),
                         (12771880859375, -5151296875, 3491750, 1))

    def test_every_discriminant_rounds_cleanly(self):
        bad = [d for _h, d in ec.discriminants()
               if ec.class_polynomial(d) is None]
        self.assertEqual(bad, [])

    def test_class_numbers(self):
        self.assertEqual(len(ec.reduced_forms(-4)), 1)
        self.assertEqual(len(ec.reduced_forms(-23)), 3)
        self.assertEqual(len(ec.reduced_forms(-71)), 7)

    def test_cornacchia(self):
        p = 10 ** 12 + 39
        for d in (-3, -4, -7, -8, -11, -15, -20, -23):
            ts = ec.cornacchia(p, d)
            if ts is not None:
                t, s = ts
                with self.subTest(d=d):
                    self.assertEqual(t * t + (-d) * s * s, 4 * p)


class TestTheArithmetic(unittest.TestCase):
    """``_ec_mul`` is repeated ``_ec_add`` on a small curve."""

    def test_double_and_add_is_repeated_addition(self):
        p, a, b = 1009, 2, 3
        pt = next((x, y) for x in range(p) for y in range(1, p)
                  if (y * y - x ** 3 - a * x - b) % p == 0)
        acc = None
        for k in range(0, 60):
            with self.subTest(k=k):
                self.assertEqual(pc._ec_mul(p, a, k, pt), acc)
            acc = pc._ec_add(p, a, acc, pt)


class TestTheChecker(unittest.TestCase):
    """The elliptic checker accepts the search's certificate and nothing
    altered, and column 3's own reader agrees."""

    @classmethod
    def setUpClass(cls):
        cls.cert = ec.elliptic(EXPLORED)

    def test_certified(self):
        self.assertEqual(pc.check(EXPLORED, self.cert), "prime")
        self.assertTrue(any(len(e) == 7 for e in self.cert["chain"]))

    def test_the_script_reader_agrees(self):
        self.assertEqual(_script_reader()(EXPLORED, self.cert), "prime")

    def test_tampered_certificates_prove_nothing(self):
        reader = _script_reader()
        for kind, bad in ecc.tampered(self.cert):
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    pc.check(EXPLORED, bad)
                with self.assertRaises(AssertionError):
                    reader(EXPLORED, bad)

    def test_the_phase_140_certifier_refuses_it(self):
        with ecc.flags(False):
            with self.assertRaises(pc.NoCertificate):
                pc.certify(EXPLORED)
        with ecc.flags(True):
            self.assertEqual(pc.certify(EXPLORED)["kind"], "elliptic")

    def test_no_composite_passes_an_elliptic_entry(self):
        primes = [q for q in range(2, 200)
                  if all(q % d for d in range(2, q))]
        known = set(primes)
        accepted = []
        for p in range(9, 60, 2):
            if p in known:
                continue
            for a in range(3):
                for b in range(1, 3):
                    for x in range(p):
                        for y in range(1, p):
                            if (y * y - x ** 3 - a * x - b) % p:
                                continue
                            for k in (1, 2, 3, 4):
                                for q in primes:
                                    if pc._check_eentry(known, p, a, b, x, y,
                                                        k, q):
                                        accepted.append((p, a, b, x, y, k, q))
        self.assertEqual(accepted, [])


class TestTheStep(unittest.TestCase):
    """The stepwise ``prime`` step carries the elliptic certificate."""

    def test_the_step(self):
        a = stepwise.answer(GeometricSession(), f"is {EXPLORED} prime")
        self.assertTrue(a.answered)
        step = [s for s in a.chain.steps if s.op == "prime"][0]
        self.assertEqual(step.value, "prime")
        self.assertEqual(step.detail["certificate"]["kind"], "elliptic")
        bad = ecc.tampered(dict(step.detail["certificate"]))[0][1]
        t = ss.Step(step.index, step.op, step.inputs, step.value, step.label,
                    dict(step.detail, certificate=bad), step.origin)
        steps = [t if x is step else x for x in a.chain.steps]
        self.assertFalse(ss.step_check(t, steps)[0])


if __name__ == "__main__":
    unittest.main()
