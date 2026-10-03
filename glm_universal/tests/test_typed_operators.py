"""Typed operators -- real, reactive and apparent power, the power factor,
and the dot against the cross product, pinned.

``glm_universal.runtime.typed_operators`` is the reader
(``studies/TYPED_OPERATORS_STUDY.md``, Phase 90);
``glm_universal.runtime.typed_operators_report`` measures the declared corpus
of ``glm_universal.evaluation.typed_operator_cases``.  The facts the round
rests on are theorems of ``RequestProject/GLM/TypedOperators.lean`` (T8).
Everything is exact.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.engineering.smith import GaussQ
from glm_universal.evaluation import typed_operator_cases as C
from glm_universal.runtime import question_frames as qf
from glm_universal.runtime import typed_operators as to
from glm_universal.runtime import typed_operators_report as tr


class TestTheOperators(unittest.TestCase):

    def test_complex_power_conjugates_the_current(self):
        s = to.complex_power(GaussQ.of(120), GaussQ.of(3, -4))
        self.assertEqual(s, GaussQ.of(360, 480))

    def test_power_factor_is_exact_and_signed(self):
        pf, sense = to.power_factor(Fraction(50), Fraction(-100))
        self.assertEqual((pf.b, pf.c, sense), (Fraction(1, 5), 5, "leading"))
        pf, sense = to.power_factor(Fraction(360), Fraction(480))
        self.assertEqual((pf.rational(), sense), (Fraction(3, 5), "lagging"))

    def test_dot_and_cross_differ(self):
        a = (Fraction(1), Fraction(2), Fraction(3))
        b = (Fraction(4), Fraction(5), Fraction(6))
        self.assertEqual(to.dot(a, b), 32)
        self.assertEqual(to.cross(a, b), (-3, 6, -3))
        self.assertEqual(to.cross(b, a), (3, -6, 3))

    def test_the_three_units_are_three_kinds(self):
        self.assertEqual(to.POWER_UNITS["w"][0], frozenset({"real"}))
        self.assertEqual(to.POWER_UNITS["var"][0], frozenset({"reactive"}))
        self.assertEqual(to.POWER_UNITS["va"][0],
                         frozenset({"apparent", "complex"}))


class TestTheCorpus(unittest.TestCase):

    def test_every_case_as_declared(self):
        for cid, q, want in C.ALL_CASES:
            with self.subTest(cid):
                self.assertEqual(to.answer(q).verdict, want)

    def test_a_given_moves_the_answer(self):
        a = to.answer("With phasor voltage V = 120 + 0j V and phasor current "
                      "I = 3 - 5j A, what is the reactive power?")
        self.assertEqual(a.verdict, ("ANSWER", Fraction(600)))

    def test_the_reader_is_switchable(self):
        to.ACTIVE = False
        try:
            self.assertIsNone(to.answer(C.PHASOR_CASES[0][1]))
        finally:
            to.ACTIVE = True

    def test_the_frame_reads_given_phrasing(self):
        got = qf.frame_of(C.PHASOR_CASES[11][1])
        self.assertIsNotNone(got)
        self.assertEqual(got[0].name, "typed_operator")

    def test_the_gate_passes_a_reading(self):
        rd = qf.read(C.PHASOR_CASES[2][1])
        self.assertTrue(rd.answered)
        self.assertTrue(rd.gate[0])
        self.assertIn("480", rd.value)


class TestTheMarks(unittest.TestCase):

    def test_naive_control_is_wrong_often_enough(self):
        c = tr.control_report()
        self.assertTrue(c["met"], c)

    def test_no_earlier_question_is_read(self):
        e = tr.earlier_report()
        self.assertEqual(e["read"], [])
        self.assertGreater(e["strings"], 2000)

    def test_scripts_verify_and_mutations_fail(self):
        s = tr.scripts_report()
        self.assertTrue(s["met"], s)

    def test_census(self):
        self.assertTrue(tr.census_report()["met"])

    def test_the_lean_file_has_no_sorry(self):
        root = Path(__file__).resolve().parents[2]
        lean = root / "glm_lean" / "RequestProject" / "GLM" / \
            "TypedOperators.lean"
        text = lean.read_text()
        self.assertNotIn("sorry", text)
        for name in ("power_triangle", "power_factor_mem",
                     "reactive_sign_undetermined", "naive_real_power_wrong",
                     "lagrange_identity", "naive_torque_wrong"):
            self.assertIn(f"theorem {name}", text)


if __name__ == "__main__":
    unittest.main()
