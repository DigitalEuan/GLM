"""Tests for the wheels package: the registry, the 15 wheels, the junctions.

Covers:
  * The 15 wheels are registered (W01-W10 engineering + W11-W15 domain).
  * Each wheel has the expected id, title, and axioms.
  * The junction tables are complete (5 Phase-66 + 10 Phase-157 = 15).
  * The four non-identities and two aliases are present.
  * The oscillator junction's four variants and the shipped choice (B).
  * The engineering/domains.py and engineering/oscillator_junction.py
    modules expose the report functions the CLI expects.
"""
from __future__ import annotations

import unittest

from glm_universal.wheels import (
    WHEELS, ALL_WHEELS, DOMAIN_WHEELS, wheel_by_id,
    JUNCTIONS, NON_IDENTITIES, ALIASES,
    Wheel, derive_from, wheel_named,
)
from glm_universal.wheels.junctions import phase66, domain, oscillator
from glm_universal.engineering import domains as dmn
from glm_universal.engineering import domains_study as dms
from glm_universal.engineering import oscillator_junction as osj


class TestWheelRegistry(unittest.TestCase):
    """The 15-wheel registry."""

    def test_fifteen_wheels_registered(self):
        """W01-W10 (engineering) + W11-W15 (domain) = 15 wheels."""
        self.assertEqual(len(ALL_WHEELS), 15)
        self.assertEqual(len(WHEELS), 15)

    def test_engineering_wheels_preserved(self):
        """W01-W10 keep their existing ids 'W1'-'W10'."""
        ids = [w.id for w in ALL_WHEELS[:10]]
        self.assertEqual(ids, [f"W{i}" for i in range(1, 11)])

    def test_domain_wheels_present(self):
        """W11-W15 are the five domain wheels."""
        self.assertEqual(len(DOMAIN_WHEELS), 5)
        ids = [w.id for w in DOMAIN_WHEELS]
        self.assertEqual(ids, ["W11", "W12", "W13", "W14", "W15"])

    def test_wheel_by_id_finds_all(self):
        """wheel_by_id finds every wheel."""
        for i in range(1, 16):
            w = wheel_by_id(f"W{i}")
            self.assertEqual(w.id, f"W{i}")

    def test_wheel_by_id_raises_on_unknown(self):
        with self.assertRaises(KeyError):
            wheel_by_id("W99")

    def test_backward_compat_wheel_named(self):
        """The existing wheel_named() function still works."""
        w = wheel_named("W1")
        self.assertEqual(w.id, "W1")


class TestDomainWheelDefinitions(unittest.TestCase):
    """The five domain wheels' definitions match the study doc."""

    def test_w11_uniform_motion(self):
        w = wheel_by_id("W11")
        self.assertEqual(w.title, "Uniform motion")
        self.assertIn("velocity = length / time", w.axioms)

    def test_w12_density(self):
        w = wheel_by_id("W12")
        self.assertEqual(w.title, "Density, volume and amount of substance")
        self.assertIn("density = mass / volume", w.axioms)
        self.assertIn("volume = area * length", w.axioms)
        self.assertIn("amount = mass / molar_mass", w.axioms)

    def test_w13_oscillator(self):
        w = wheel_by_id("W13")
        self.assertEqual(w.title, "Period and the mass-spring oscillator")
        self.assertIn("frequency = 1 / period", w.axioms)

    def test_w14_inductors(self):
        w = wheel_by_id("W14")
        self.assertEqual(w.title, "Inductors and the LC circuit")
        self.assertIn("reactance = inductance * angular_frequency", w.axioms)

    def test_w15_charge_energy(self):
        w = wheel_by_id("W15")
        self.assertEqual(w.title, "Charge and energy over time")
        self.assertIn("charge = current * time", w.axioms)
        self.assertIn("energy = power * time", w.axioms)


class TestJunctionTables(unittest.TestCase):
    """The junction tables are complete."""

    def test_phase66_junctions(self):
        """The five Phase-66 junctions between W01-W10."""
        self.assertEqual(len(phase66.JUNCTIONS), 5)
        self.assertIn(("W5", "W6"), phase66.JUNCTIONS)
        self.assertIn(("W1", "W3"), phase66.JUNCTIONS)
        self.assertIn(("W9", "W10"), phase66.JUNCTIONS)

    def test_domain_junctions(self):
        """The ten Phase-157 junctions between W01-W15."""
        self.assertEqual(len(domain.JUNCTIONS), 10)
        self.assertIn(("W5", "W11"), domain.JUNCTIONS)
        self.assertIn(("W9", "W13"), domain.JUNCTIONS)
        self.assertIn(("W1", "W15"), domain.JUNCTIONS)

    def test_oscillator_junction_rule_b(self):
        """W09/W13 joins frequency only (rule B, Phase 158)."""
        self.assertEqual(domain.JUNCTIONS[("W9", "W13")], ("frequency",))

    def test_domain_non_identities(self):
        """The four (now five) non-identities are present."""
        self.assertGreaterEqual(len(domain.NON_IDENTITIES), 4)
        self.assertIn(("W13", "W14"), domain.NON_IDENTITIES)
        self.assertIn(("W3", "W14"), domain.NON_IDENTITIES)

    def test_aliases(self):
        """The two aliases: speed -> velocity, distance -> length."""
        self.assertEqual(domain.ALIASES["speed"], "velocity")
        self.assertEqual(domain.ALIASES["distance"], "length")

    def test_aggregated_junctions(self):
        """The top-level JUNCTIONS dict aggregates Phase-66 + domain."""
        self.assertEqual(len(JUNCTIONS), 15)  # 5 + 10
        self.assertIn(("W5", "W6"), JUNCTIONS)      # phase66
        self.assertIn(("W5", "W11"), JUNCTIONS)     # domain

    def test_aggregated_non_identities(self):
        """The top-level NON_IDENTITIES aggregates both tables."""
        self.assertGreaterEqual(len(NON_IDENTITIES), 4)

    def test_aggregated_aliases(self):
        """The top-level ALIASES dict is the domain aliases."""
        self.assertEqual(ALIASES["speed"], "velocity")


class TestOscillatorJunction(unittest.TestCase):
    """The W09/W13 oscillator junction's four variants."""

    def test_four_variants(self):
        self.assertEqual(oscillator.VARIANTS, ("A", "B", "C", "D"))

    def test_b_is_shipped(self):
        self.assertEqual(oscillator.SHIPPED, "B")

    def test_variant_readings(self):
        self.assertEqual(len(oscillator.VARIANT_READINGS), 4)
        self.assertIn("rate_only", oscillator.VARIANT_READINGS["B"])

    def test_junction_for_variant_b(self):
        """Variant B joins frequency only."""
        self.assertEqual(oscillator.junction_for_variant("B"), ("frequency",))

    def test_junction_for_variant_a(self):
        """Variant A joins frequency and angle."""
        self.assertEqual(oscillator.junction_for_variant("A"),
                         ("frequency", "angle"))

    def test_lean_theorems(self):
        self.assertEqual(len(oscillator.LEAN_THEOREMS), 5)
        self.assertIn("rotor_chain_refused_rate_only", oscillator.LEAN_THEOREMS)


class TestDomainsReport(unittest.TestCase):
    """The engineering/domains.py report function."""

    def test_domains_report_shape(self):
        r = dmn.domains_report(census=False)
        self.assertIn("wheels", r)
        self.assertIn("junctions", r)
        self.assertIn("battery", r)
        self.assertIn("marks", r)
        self.assertIn("met", r)
        self.assertIn("taken", r)

    def test_domains_report_wheels(self):
        r = dmn.domains_report(census=False)
        self.assertEqual(len(r["wheels"]), 5)
        ids = [w["id"] for w in r["wheels"]]
        self.assertEqual(ids, ["W11", "W12", "W13", "W14", "W15"])

    def test_domains_report_junctions(self):
        r = dmn.domains_report(census=False)
        self.assertGreaterEqual(len(r["junctions"]), 10)

    def test_domains_report_with_census(self):
        r = dmn.domains_report(census=True)
        self.assertIn("census", r)
        self.assertIn("gained", r["census"])
        self.assertFalse(r["census_fresh"])

    def test_study_report(self):
        r = dms.study_report()
        self.assertIn("wheels", r)


class TestOscillatorJunctionReport(unittest.TestCase):
    """The engineering/oscillator_junction.py report function."""

    def test_report_not_measured(self):
        """With no stored measurement, report returns measured=False."""
        r = osj.report()
        self.assertFalse(r["measured"])
        self.assertEqual(r["chosen"], "B")

    def test_measure_returns_shape(self):
        m = osj.measure("B")
        self.assertEqual(m["variant"], "B")
        self.assertIn("battery", m)
        self.assertIn("O1", m)

    def test_measure_raises_on_unknown_variant(self):
        with self.assertRaises(KeyError):
            osj.measure("Z")

    def test_variants_reexported(self):
        self.assertEqual(osj.VARIANTS, ("A", "B", "C", "D"))
        self.assertEqual(osj.SHIPPED, "B")


if __name__ == "__main__":
    unittest.main()
