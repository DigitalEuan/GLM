"""The measurand register -- register values read through their measurand,
conversions through a stated efficiency, and the elementary charge, pinned.

``glm_universal.runtime.measurand_register`` declares the register
(``studies/MEASURAND_REGISTER_STUDY.md``, Phase 87);
``glm_universal.runtime.measurand_register_report`` measures the declared
corpus of ``glm_universal.evaluation.measurand_register_cases``.  The facts the
round rests on are theorems of ``RequestProject/GLM/MeasurandRegister.lean``
(R8).  Everything is exact.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.evaluation import measurand_register_cases as C
from glm_universal.runtime import measurand_register as mreg
from glm_universal.runtime import measurand_register_report as rr
from glm_universal.runtime import quantity_units as qu
from glm_universal.runtime import stepwise as sw
from glm_universal.runtime.session import GeometricSession

_SESSION = []


def session():
    if not _SESSION:
        _SESSION.append(GeometricSession())
    return _SESSION[0]


class TestTheDeclarations(unittest.TestCase):

    def test_the_elementary_charge_is_the_si_value(self):
        self.assertEqual(mreg.ELEMENTARY_CHARGE, Fraction(1602176634, 10 ** 28))
        read = qu.read_unit("elementary charges")
        self.assertEqual(read.factor, mreg.ELEMENTARY_CHARGE)
        self.assertEqual(read.dimension, qu.quantity_dimension("charge"))
        self.assertEqual(qu.read_unit("percent").factor, Fraction(1, 100))

    def test_every_register_row_names_a_declared_scale(self):
        from glm_universal.reasoning.scale_conversion import declared
        for row in mreg.REGISTER_MEASURANDS:
            self.assertIsNotNone(declared(row.scale), row.scale)
            self.assertTrue(row.argument)

    def test_a_photon_threshold_is_read_per_atom(self):
        row = mreg.measurand_of("element:ionization_energy_eV")
        self.assertEqual((row.by_name, row.wheels, row.factor),
                         ("energy", ("W10",), mreg.ELEMENTARY_CHARGE))

    def test_a_radius_feeds_no_wheel_by_name(self):
        for scale in ("element:atomic_radius_pm", "element:covalent_radius_pm"):
            self.assertIsNone(mreg.measurand_of(scale).by_name)

    def test_each_law_crosses_a_declared_non_identity(self):
        for law in mreg.CONVERSION_LAWS:
            self.assertNotEqual(law.in_label, law.out_label)
            self.assertEqual(law.in_label.split("@")[0], "power")
            self.assertEqual(law.out_label.split("@")[0], "power")
            self.assertIs(mreg.law_named(law.efficiency), law)
            self.assertIs(mreg.law_of_id(law.id), law)

    def test_an_efficiency_name(self):
        self.assertTrue(mreg.efficiency_name("efficiency"))
        self.assertTrue(mreg.efficiency_name("heater_efficiency"))
        self.assertFalse(mreg.efficiency_name("power"))
        self.assertIsNone(mreg.law_named("heater_efficiency"))

    def test_no_law_is_in_scope_between_questions(self):
        sw.answer(session(), C.CONVERSION_CASES[0][1])
        self.assertEqual(sw._LAWS_IN_SCOPE, [])


class TestTheCorpus(unittest.TestCase):
    """R1-R3: every declared case as declared, 0 wrong."""

    def _all_met(self, rep):
        self.assertEqual(rep["met"], rep["cases"],
                         [r for r in rep["rows"] if not r["ok"]])
        self.assertEqual(rep["wrong"], 0)

    def test_r1_register(self):
        self._all_met(rr.register_report(session()))

    def test_r2_conversions(self):
        self._all_met(rr.conversions_report(session()))

    def test_r3_charges(self):
        self._all_met(rr.charges_report(session()))


class TestTheControls(unittest.TestCase):

    def test_r4_controls(self):
        got = rr.control_report(session())
        self.assertTrue(got["met"], got)
        self.assertGreaterEqual(len(got["naive_wrong"]),
                                C.NAIVE_WRONG_AT_LEAST)

    def test_switches_are_restored(self):
        with rr.switched(ACTIVE=False, NAIVE=True, RESTRICT=False):
            self.assertFalse(mreg.ACTIVE)
        self.assertTrue(mreg.ACTIVE)
        self.assertFalse(mreg.NAIVE)
        self.assertTrue(mreg.RESTRICT)


class TestNothingEarlierMoves(unittest.TestCase):

    def test_r5_earlier(self):
        got = rr.earlier_report(session())
        self.assertTrue(got["met"], got)


class TestTheScripts(unittest.TestCase):

    def test_r6_scripts_sample(self):
        got = rr.scripts_report(session(), limit=3)
        self.assertEqual(got["verified"], got["chains"], got["failed"])
        self.assertEqual(got["escaped"], [])


class TestTheCensus(unittest.TestCase):

    def test_r7_census(self):
        got = rr.census_report()
        self.assertTrue(got["met"], got)


class TestTheLeanFile(unittest.TestCase):

    def test_r8_lean_file_has_no_sorry(self):
        root = Path(__file__).resolve().parents[2]
        path = root / "glm_lean" / "RequestProject" / "GLM" / \
            "MeasurandRegister.lean"
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in ("efficiency_out_le_in", "naive_identity_wrong",
                     "derived_efficiency_gt_one", "conversion_compose",
                     "photon_threshold_frequency_monotone",
                     "capacitor_energy_half_QV"):
            self.assertIn(name, text)


if __name__ == "__main__":
    unittest.main()
