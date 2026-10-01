"""Measurands -- kinds of quantity in the stepwise planner, pinned.

``glm_universal.runtime.measurands`` declares the kinds a dimension check
cannot tell apart (``studies/MEASURANDS_STUDY.md``, Phase 86);
``glm_universal.runtime.measurand_report`` measures the declared corpus of
``glm_universal.evaluation.measurand_cases``.  The facts the kinds rest on
are theorems of ``RequestProject/GLM/MeasurandKinds.lean`` (M7).  Everything
is exact.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from pathlib import Path

from glm_universal.evaluation import measurand_cases as C
from glm_universal.runtime import measurand_report as mr
from glm_universal.runtime import measurands as ms
from glm_universal.runtime import stepwise as sw
from glm_universal.runtime.session import GeometricSession

_SESSION = []


def session():
    if not _SESSION:
        _SESSION.append(GeometricSession())
    return _SESSION[0]


class TestTheDeclarations(unittest.TestCase):

    def test_special_units_are_restricted(self):
        self.assertIn("angular_velocity", ms.unit_forbids("kilohertz")[1])
        self.assertIn("frequency", ms.unit_forbids("radians per second")[1])
        self.assertIn("torque", ms.unit_forbids("kilojoules")[1])
        self.assertIn("energy", ms.unit_forbids("newton metres")[1])
        self.assertIsNone(ms.unit_forbids("joules per second"))
        self.assertIsNone(ms.unit_forbids("metres per second"))

    def test_offset_readings_are_exact(self):
        f, o, _ = ms.offset_reading("degrees celsius", "level")
        self.assertEqual(25 * f + o, Fraction(29815, 100))
        f, o, _ = ms.offset_reading("degrees fahrenheit", "level")
        self.assertEqual(77 * f + o, Fraction(29815, 100))
        f, o, _ = ms.offset_reading("degrees fahrenheit", "difference")
        self.assertEqual((18 * f, o), (10, 0))
        self.assertIsNone(ms.offset_reading("kelvins", "level"))

    def test_slot_kinds(self):
        self.assertEqual(ms.slot_kind("entropy = energy / temperature",
                                      "temperature"), "level")
        self.assertEqual(ms.slot_kind(
            "energy = mass * specific_heat_capacity * temperature",
            "temperature"), "difference")

    def test_defined_constants_are_the_si_values(self):
        self.assertEqual(ms.constant_value("planck_constant"),
                         Fraction(662607015, 10 ** 42))
        self.assertEqual(ms.constant_value("speed_of_light"), 299792458)


class TestTheCorpus(unittest.TestCase):
    """M1-M3: every declared case as declared, 0 wrong."""

    def _all_met(self, rep):
        self.assertEqual(rep["met"], rep["cases"],
                         [r for r in rep["rows"] if not r["ok"]])
        self.assertEqual(rep["wrong"], 0)

    def test_m1_kinds(self):
        self._all_met(mr.kinds_report(session()))

    def test_m2_temperatures(self):
        self._all_met(mr.temperatures_report(session()))

    def test_m3_constants(self):
        self._all_met(mr.constants_report(session()))


class TestTheControl(unittest.TestCase):
    """M4: the dimension check alone answers the kind refusals, and none of
    the new answers."""

    def test_control(self):
        r = mr.control_report(session())
        self.assertTrue(r["met"])
        self.assertGreaterEqual(len(r["kind_refusals_answered"]),
                                C.CONTROL_KIND_ANSWERS_AT_LEAST)
        wrong_by_two_pi = dict(r["kind_refusals_answered"])
        self.assertEqual(wrong_by_two_pi["k01"], "100")
        self.assertEqual(len(r["new_answers"]), 10)

    def test_amendments(self):
        r = mr.amendments_report(session())
        self.assertEqual(r["met"], r["cases"])
        self.assertEqual(r["cases"], len(C.AMENDED))


class TestTheChains(unittest.TestCase):
    """M5 on a sample: the offset and constant steps verify in column 3."""

    def test_offset_and_constant_scripts(self):
        r = mr.scripts_report(session(), limit=None)
        self.assertEqual(r["verified"], r["chains"], r["failed"])
        self.assertEqual(r["escaped"], [])

    def test_offset_step_is_shown(self):
        a = sw.answer(session(), C.TEMPERATURE_CASES[0][1])
        si = [s for s in a.chain.steps if s.op == "si"][-1]
        self.assertEqual(si.detail["offset"], "5463/20")
        self.assertEqual(si.detail["reading"], "level")

    def test_constant_step_is_shown(self):
        a = sw.answer(session(), C.CONSTANT_CASES[0][1])
        self.assertIn("constant", [s.op for s in a.chain.steps])


class TestTheLean(unittest.TestCase):

    def test_lean_file_names_its_theorems(self):
        path = (Path(ms.__file__).resolve().parents[2] / "glm_lean"
                / "RequestProject/GLM/MeasurandKinds.lean")
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("sorry", text)
        for name in ("offset_difference_free",
                     "level_as_difference_depends_on_zero",
                     "difference_law_zero_free", "fahrenheit_kelvin",
                     "absolute_zero_celsius",
                     "hertz_as_angular_velocity_wrong"):
            self.assertIn(f"theorem {name}", text)


if __name__ == "__main__":
    unittest.main()
