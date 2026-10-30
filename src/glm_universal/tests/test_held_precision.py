"""Held precision, pinned.

``glm_universal.reasoning.held_precision`` is the computational half of
``studies/HELD_PRECISION_STUDY.md`` (Phase 76); the corner bound it rests on
is a theorem of ``RequestProject/GLM/HeldPrecision.lean`` (H5).  Everything
is exact.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import held_precision as hp
from glm_universal.runtime import stepwise as sw
from glm_universal.runtime.session import GeometricSession

# Phase 86 (studies/MEASURANDS_STUDY.md): the three register chains this file
# pinned in Phase 76 fed a melting or boiling point (a temperature level) to
# energy = mass * specific heat capacity * temperature, which reads a
# temperature difference.  They are refused LEVEL_AS_DIFFERENCE now, and the
# chains below are the register chains that remain.
LEVEL_AS_DIFFERENCE = ("given mass = 2, specific heat capacity = 450 and "
                       "temperature = the melting point of iron, what is "
                       "the energy")
ENERGY = ("given temperature = the boiling point of nitrogen and entropy = 2, "
          "what is the energy")
KILOJOULES = ("given temperature = the boiling point of nitrogen and entropy "
              "= 2000, what is the energy in kilojoules")
NO_REGISTER = "given voltage = 12 and resistance = 4, what is the power"


class TestChains(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.session = GeometricSession()

    def chain(self, q):
        a = sw.answer(self.session, q)
        self.assertTrue(a.answered, a.summary())
        return a

    def test_energy_interval(self):
        a = self.chain(ENERGY)
        self.assertEqual(a.value, "3868/25")
        p = hp.chain_precision(a.chain.steps)
        self.assertEqual(p["interval"], (Fraction(15471, 100),
                                         Fraction(15473, 100)))
        self.assertFalse(p["exact"])
        self.assertIn("energy lies in [154.71, 154.73]", a.chain.notes[-1])

    def test_the_phase_76_chain_is_refused_by_kind(self):
        a = sw.answer(self.session, LEVEL_AS_DIFFERENCE)
        self.assertEqual(a.refusal, "LEVEL_AS_DIFFERENCE")

    def test_unit_out_is_carried(self):
        a = self.chain(KILOJOULES)
        p = hp.chain_precision(a.chain.steps)
        self.assertEqual(p["interval"], (Fraction(15471, 100),
                                         Fraction(15473, 100)))

    def test_no_register_no_note(self):
        a = self.chain(NO_REGISTER)
        self.assertIsNone(hp.chain_precision(a.chain.steps))
        self.assertFalse(any(n.startswith("precision: ") for n in a.chain.notes))

    def test_composite_matches_the_chain(self):
        a = self.chain(ENERGY)
        c, ex = hp.composite(a.chain.steps)
        # energy = temperature * entropy: coefficient 1 over the looked-up
        # temperature (leaf 1) and the given entropy (leaf 3).
        self.assertEqual(c, 1)
        self.assertEqual(ex, {1: 1, 3: 1})
        self.assertEqual(hp.evaluate_at(a.chain.steps, {1: Fraction(1)}), 2)


class TestReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.report = hp.held_precision_report()

    def test_marks(self):
        # H3 is no longer met from Phase 86 on (studies/HELD_PRECISION_STUDY.md
        # §4): both of its witnesses -- the exact answer whose held value
        # cancels, and the chain where step-by-step intervals are wider --
        # were the chain that read one temperature as a level and as a
        # difference, which the kinds of quantity now refuse.
        self.assertEqual(self.report["marks"],
                         {"H1": True, "H2": True, "H3": False, "H4": True,
                          "H5": True})

    def test_counts(self):
        self.assertEqual(self.report["chains"], 35)
        self.assertEqual(self.report["with_register"], 4)
        self.assertEqual(self.report["exact"], 0)
        self.assertEqual(self.report["naive_wider"], 0)


if __name__ == "__main__":
    unittest.main()
