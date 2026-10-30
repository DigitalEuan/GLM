"""Tests for :mod:`glm_universal.engineering` -- electrical and mechanical as
languages the GLM can be asked in."""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.engineering import (analogy, delta_sigma, smith, speak,
                                       study, wheels)
from glm_universal.evaluation import engineering_heldout as held


class TestWheels(unittest.TestCase):

    def test_relation_vector_carries_coefficient(self):
        self.assertEqual(wheels.relation_vector("energy = 1/2 * mass * v^2"),
                         {"energy": 1, "mass": -1, "v": -2, "#2": 1})

    def test_ohm_wheel_has_twelve_spokes(self):
        w = wheels.wheel_named("W1")
        spokes = [s.text() for q in wheels.wheel_quantities(w)
                  for s in wheels.wheel_spokes(w, q)]
        self.assertEqual(len(spokes), 12)
        self.assertIn("power = voltage^2 / resistance", spokes)
        self.assertIn("current = (power / resistance)^(1/2)", spokes)

    def test_certificate_replays(self):
        s = wheels.derive_from("power", ("voltage", "resistance"),
                               wheels.wheel_named("W1").axioms)
        weights = dict(s.certificate.weights)
        self.assertEqual(weights["voltage = current * resistance"], -1)
        self.assertEqual(weights["power = voltage * current"], 1)

    def test_negative_control_not_derivable(self):
        self.assertFalse(wheels.is_derivable(
            "power = voltage * resistance", wheels.wheel_named("W1").axioms))

    def test_report_matches_preregistration(self):
        r = wheels.wheels_report()
        self.assertEqual(r["cases"], 41)
        for key in ("reference_si_agree", "reference_explicit_agree",
                    "register_si7_agree", "register_ext10_agree",
                    "derivable_agree", "register_held"):
            self.assertEqual(r[key], 41, key)
        self.assertEqual(r["union_flips"], ["W6-03"])

    def test_layer_disagreement_is_the_angle(self):
        self.assertTrue(wheels.consistency("angular_velocity = frequency",
                                           "si7")["consistent"])
        ext = wheels.consistency("angular_velocity = frequency", "ext10")
        self.assertEqual(ext["residual"], {"A": 1})

    def test_dependent_inputs_refused(self):
        self.assertIsNone(wheels.derive_from(
            "power", ("resistance", "impedance"),
            wheels.wheel_named("W1").axioms))


class TestSmith(unittest.TestCase):

    def test_sixteen_checks(self):
        checks = smith.smith_checks()
        self.assertEqual(len(checks), 16)
        self.assertTrue(all(ok for _, ok in checks))

    def test_vswr_radical_when_irrational(self):
        g = smith.gamma_of(smith.GaussQ.of(Fraction(1, 2), Fraction(1, 2)))
        value, shown = smith.vswr(g)
        self.assertIsNone(value)
        self.assertIn("^(1/2)", shown)

    def test_match_never_worse_than_bypass(self):
        m = smith.smith_report()["match"]
        self.assertLessEqual(m["worst_gamma2"], m["bypass_gamma2"])


class TestAnalogy(unittest.TestCase):

    def test_force_voltage_preserves_every_law(self):
        r = analogy.structure_check(analogy.FORCE_VOLTAGE)
        self.assertEqual(r["electrical_to_mechanical"], 9)
        self.assertEqual(r["mechanical_to_electrical"], 9)

    def test_force_current_breaks_only_quality_factor(self):
        r = analogy.structure_check(analogy.FORCE_CURRENT)
        self.assertEqual(r["electrical_to_mechanical"], 8)
        self.assertTrue(all("quality_factor" in a for a, _ in r["failures"]))

    def test_scrambled_control_fails(self):
        r = analogy.structure_check(analogy.SCRAMBLED)
        self.assertLess(r["electrical_to_mechanical"], 9)

    def test_no_degeneracy(self):
        self.assertEqual(analogy.degeneracy(),
                         {"electrical": None, "mechanical": None})

    def test_translation_keeps_order(self):
        self.assertEqual(analogy.translate_equation(
            "power = current^2 * resistance", analogy.FORCE_VOLTAGE,
            "to_mechanical"), "power = velocity^2 * damping_coefficient")


class TestDeltaSigma(unittest.TestCase):

    def test_six_checks(self):
        self.assertEqual(delta_sigma.delta_sigma_report()["passed"], 6)

    def test_rational_period_is_denominator(self):
        bits = delta_sigma.first_order_bits(Fraction(3, 8), 256)
        self.assertEqual(delta_sigma.detect_period(bits, 64), 8)
        self.assertEqual(delta_sigma.rational_period(Fraction(6, 12)), 2)

    def test_sqrt2_bits_match_loop(self):
        from math import isqrt
        bits = delta_sigma.sqrt2_minus_1_bits(50)
        self.assertEqual(sum(bits), isqrt(2 * 50 * 50) - 50)

    def test_db_floor_exact(self):
        self.assertEqual(delta_sigma.db_floor(Fraction(100)), 20)
        self.assertEqual(delta_sigma.db_floor(Fraction(99)), 19)


class TestSurface(unittest.TestCase):

    def test_preregistered_sets(self):
        rep = study.language_report()
        self.assertEqual(rep["total"]["wrong"], 0)
        self.assertEqual(rep["questions"], 63)
        self.assertEqual(rep["stress_now"]["counts"], held.STRESS_FIRST_RUN)

    def test_never_reads_an_existing_question(self):
        self.assertEqual(study.interference()["read"], [])

    def test_unnamed_analogy_refused(self):
        verdict, _, reason = speak.answer("what is the electrical analogue "
                                          "of mass?")
        self.assertEqual(verdict, "refused")
        self.assertIn("ambiguous", reason)

    def test_two_routes_agree(self):
        verdict, got, _ = speak.answer("quality factor of a 1 kg mass, "
                                       "16 N/m spring and 2 N s/m damper")
        self.assertEqual(verdict, "answered")
        self.assertIn("q = 2", got.text)

    def test_session_falls_through(self):
        from glm_universal.runtime.session import GeometricSession
        s = GeometricSession()
        a = s.ask_engineering("what is the atomic weight of carbon")
        b = s.ask_planned("what is the atomic weight of carbon")
        self.assertEqual(a.answer, b.answer)

    def test_envelopes(self):
        env = study.evidence_envelopes()
        self.assertEqual([e["claim_id"] for e in env],
                         ["ENG-WHEELS", "ENG-SMITH", "ENG-ANALOGY",
                          "ENG-DELTA-SIGMA"])


if __name__ == "__main__":
    unittest.main()
