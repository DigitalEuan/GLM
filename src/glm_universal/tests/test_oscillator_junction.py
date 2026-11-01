"""Tests for the oscillator junction (Phase 158,
``studies/OSCILLATOR_JUNCTION_STUDY.md``):
:mod:`glm_universal.engineering.oscillator_junction`.

Fast: the four junction tables, the probe questions of §§5 and 7.1 under
each (a few seconds of exact linear algebra), the grading of §2.3 and the
choice of §2.4 on stand-in measurements.  The preservation set and the
censuses (minutes and hours) are not taken here; nothing is written.

*Reconstructed 31 October 2026 (repository check): the original
tests/test_oscillator_junction.py was lost in the October 2026
reorganisation; rebuilt from studies/OSCILLATOR_JUNCTION_STUDY.md (§§2, 5,
7.1) and the reconstructed module.*
"""
from __future__ import annotations

import unittest

from glm_universal.engineering import oscillator_junction as osj


def _probes(variant):
    return {p["probe"]: p for p in osj.probes(variant)}


class TestTables(unittest.TestCase):

    def test_variant_tables(self):
        a, a66 = osj.variant_tables("A")
        self.assertEqual(a[("W9", "W13")], ("frequency", "angle"))
        self.assertIn(("W4", "W9"), a66)
        b, _ = osj.variant_tables("B")
        self.assertEqual(b[("W9", "W13")], ("frequency",))
        c, _ = osj.variant_tables("C")
        self.assertNotIn(("W9", "W13"), c)
        d, d66 = osj.variant_tables("D")
        self.assertEqual(d[("W9", "W13")], ("frequency", "angle"))
        self.assertNotIn(("W4", "W9"), d66)
        # every other junction is kept
        self.assertEqual({k for k in a if k != ("W9", "W13")},
                         {k for k in c})
        with self.assertRaises(KeyError):
            osj.variant_tables("Z")

    def test_shipped_table_is_b(self):
        from glm_universal.engineering import domains as dmn
        self.assertEqual(osj.junctions("B"), dmn.union_junctions())

    def test_preservation_questions(self):
        self.assertEqual(len(osj.preservation_questions()), 24150)


class TestProbes(unittest.TestCase):
    """§7.1's readings of the four variants, question by question."""

    @classmethod
    def setUpClass(cls):
        cls.got = {v: _probes(v) for v in osj.VARIANTS}

    def answered(self, v, probe):
        return self.got[v][probe]["answered"]

    def test_rotor_chain_only_under_a(self):
        self.assertEqual(self.got["A"]["rotor chain"]["equation"],
                         "angular_frequency = power / torque")
        for v in "BCD":
            self.assertFalse(self.answered(v, "rotor chain"))

    def test_wave_period_lost_only_apart(self):
        for v in "ABD":
            self.assertEqual(self.got[v]["wave period"]["equation"],
                             "wavelength = period * wave_speed")
        self.assertFalse(self.answered("C", "wave period"))
        self.assertFalse(self.answered("C", "photon period"))

    def test_reference_circle_under_a_and_d(self):
        for v in "AD":
            self.assertEqual(self.got[v]["reference circle"]["equation"],
                             "angular_frequency = angular_velocity")
        for v in "BC":
            self.assertFalse(self.answered(v, "reference circle"))

    def test_shaft_power_lost_only_under_d(self):
        for v in "ABC":
            self.assertEqual(self.got[v]["shaft power through a wave"]["equation"],
                             "power = angle * frequency * torque")
        self.assertFalse(self.answered("D", "shaft power through a wave"))

    def test_frame_agrees_with_the_lean_theorems(self):
        got = osj.proved_agreement({v: list(p.values()) for v, p in self.got.items()})
        self.assertEqual((got["agree"], got["theorems"]), (5, 5))


class TestGradingAndChoice(unittest.TestCase):

    def test_grade_census(self):
        cen = {"rows": [
            {"t": "angular_frequency", "formula": "power / torque",
             "wheels": ["W4", "W9", "W13"], "one_wheel": False},
            {"t": "wavelength", "formula": "period * wave_speed",
             "wheels": ["W9", "W13"], "one_wheel": False},
            {"t": "spring_constant", "formula": "angular_velocity^2 * mass",
             "wheels": ["W9", "W13"], "one_wheel": False},
            {"t": "frequency", "formula": "1 / period", "wheels": ["W13"],
             "one_wheel": True},
            {"t": "time", "formula": "capacitance * resistance",
             "wheels": ["W1", "W3", "W15"], "one_wheel": False}]}
        g = osj.grade_census(cen, labels=["wavelength = period * wave_speed"])
        self.assertEqual(g["gained_reread"], 4)
        self.assertEqual(g["right"], 1)
        self.assertEqual(g["oscillator"], 3)
        self.assertEqual(g["not_entailed"], 1)
        self.assertEqual((g["entailed_labelled"], g["entailed_other"]), (1, 1))
        from glm_universal.engineering import domains as dmn
        if dmn._labels() is None:
            # without the declared labels the entailed answers are not split
            u = osj.grade_census(cen)
            self.assertEqual((u["not_entailed"], u["entailed"]), (1, 2))
            self.assertIsNone(u["entailed_labelled"])
            self.assertIsNone(u["right"])

    def test_choice_rule(self):
        m = {"A": {"O1": True, "O2": True, "not_entailed": 6,
                   "entailed_labelled": 11},
             "B": {"O1": True, "O2": True, "not_entailed": 0,
                   "entailed_labelled": 9},
             "C": {"O1": False, "O2": True, "not_entailed": 0,
                   "entailed_labelled": 0},
             "D": {"O1": True, "O2": False, "not_entailed": 0,
                   "entailed_labelled": 11}}
        self.assertEqual(osj.choose(m)["chosen"], "B")
        none = {v: dict(x, O1=False) for v, x in m.items()}
        self.assertEqual(osj.choose(none)["chosen"], "A")

    def test_marks_of(self):
        self.assertEqual(osj.marks_of({"O1": True, "lost": 0, "not_entailed": 0,
                                       "O4": True}),
                         {"O1": True, "O2": True, "O3": True, "O4": True})
        self.assertEqual(osj.marks_of({"lost": None, "not_entailed": None}),
                         {"O1": False, "O2": False, "O3": False, "O4": False})

    def test_preservation_on_a_stand_in_reference(self):
        ref = [("power", ("angle", "frequency", "torque"),
                "power = angle * frequency * torque")]
        self.assertEqual(osj.preservation("B", ref)["lost"], 0)
        self.assertEqual(osj.preservation("D", ref)["lost"], 1)


class TestMeasureAndReport(unittest.TestCase):

    def test_measure_without_the_long_sets(self):
        m = osj.measure("C")
        self.assertEqual(m["variant"], "C")
        self.assertFalse(m["full"])
        self.assertIsNone(m["lost"])
        self.assertFalse(m["O2"] or m["O3"])           # not measured: missed
        if not m["battery_available"]:
            self.assertFalse(m["O1"])
        with self.assertRaises(KeyError):
            osj.measure("E")

    def test_report(self):
        r = osj.report()
        if not r["measured"]:
            self.assertEqual(r["chosen"], osj.SHIPPED)
            self.assertIn("--write", r["reason"])
        else:
            self.assertEqual(set(r["marks"]), set(osj.VARIANTS))


if __name__ == "__main__":
    unittest.main()
