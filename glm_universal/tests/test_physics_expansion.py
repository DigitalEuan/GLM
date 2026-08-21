"""Tests for the augmented physics register.

After the original 660 concepts, 41 new ones were added across nine domains:
acoustics (+6), photometry (+6), radiometry (+6), base (+4), geophysics (+6),
information (+5), statistical mechanics (+3), astronomy (+3), signals and
control (+2).  The new total is 701.

These tests verify that:
* the register reports the new count,
* every new concept round-trips through PhysicsCodec.check(),
* every new concept is uniquely identifiable by name,
* the new concepts span their intended domains.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.data_objects import physics as ph
from glm_universal.data_objects.physics import (PhysicsCodec,
                                                  load_physics_register,
                                                  quantity_by_name)

#: The names of the 41 concepts added in the augmentation.
NEW_CONCEPT_NAMES = (
    # Acoustics (+6)
    "acoustic_power_level", "acoustic_intensity_level",
    "acoustic_attenuation", "loudness_level", "acoustic_admittance",
    "audio_frequency",
    # Photometry (+6)
    "color_temperature", "chromaticity_x", "chromaticity_y",
    "tristimulus_X", "tristimulus_Y", "tristimulus_Z",
    # Radiometry (+6)
    "spectral_responsivity", "spectral_power_density",
    "spectral_absorptance", "reflectivity", "transmissivity",
    "radiant_exitance",
    # Base (+4)
    "proton_mass", "reduced_planck_constant",
    "stefan_boltzmann_constant", "avogadro_number",
    # Geophysics (+6)
    "s_wave_velocity", "magnetic_inclination", "magnetic_total_field",
    "richter_magnitude", "moment_magnitude", "magnetic_anomaly",
    # Information (+5)
    "shannon_entropy", "hartley_entropy", "kl_divergence",
    "fisher_information", "self_information",
    # Statistical mechanics (+3)
    "gibbs_free_energy", "equipartition_energy", "degeneracy",
    # Astronomy (+3)
    "hubble_constant", "hubble_distance", "light_year",
    # Signals and control (+2)
    "transfer_function", "nyquist_frequency",
)

EXPECTED_COUNT = 720  # 660 original + 41 + 19 new
ADDED_COUNT = 41


class TestPhysicsAugmentation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.register = load_physics_register()
        cls.codec = PhysicsCodec()

    def test_register_size_is_720(self):
        self.assertEqual(len(self.register), EXPECTED_COUNT)

    def test_no_duplicate_names(self):
        names = [q.name for q in self.register]
        self.assertEqual(len(names), len(set(names)))

    def test_every_new_concept_is_present(self):
        for name in NEW_CONCEPT_NAMES:
            with self.subTest(name=name):
                q = quantity_by_name(name)
                self.assertIsNotNone(q, f"{name} missing from register")

    def test_every_new_concept_round_trips(self):
        for name in NEW_CONCEPT_NAMES:
            with self.subTest(name=name):
                q = quantity_by_name(name)
                # Codec.check() runs both legs of the losslessness contract.
                self.codec.check(q)

    def test_every_new_concept_has_24_coord_carrier(self):
        for name in NEW_CONCEPT_NAMES:
            with self.subTest(name=name):
                q = quantity_by_name(name)
                obj = self.codec.encode(q)
                self.assertEqual(len(obj.carrier), 24)

    def test_new_concepts_are_distributed_across_their_domains(self):
        domain_counts = {}
        for name in NEW_CONCEPT_NAMES:
            q = quantity_by_name(name)
            domain_counts[q.domain_name] = domain_counts.get(q.domain_name, 0) + 1
        # Each domain got at least one new concept.
        expected_domains = {
            "acoustics": 6, "photometry": 6, "radiometry": 6,
            "base": 4, "geophysics": 6, "information": 5,
            "statistical mechanics": 3, "astronomy": 3,
            "signals and control": 2,
        }
        for domain, count in expected_domains.items():
            with self.subTest(domain=domain):
                self.assertEqual(domain_counts.get(domain, 0), count,
                                 f"{domain} expected {count} new concepts, "
                                 f"got {domain_counts.get(domain, 0)}")

    def test_information_concepts_carry_the_B_axis(self):
        """All five new information concepts should have B != 0 (the
        information axis), except fisher_information which is
        parameter-scaled and dimensionless."""
        for name in ("shannon_entropy", "hartley_entropy", "kl_divergence",
                     "self_information"):
            with self.subTest(name=name):
                q = quantity_by_name(name)
                # B is axis index 9 in EXT10.
                b_exp = q.exps_ext10[9]
                self.assertEqual(b_exp, Fraction(1),
                                 f"{name} should have B=1, got {b_exp}")

    def test_photometry_tristimulus_values_are_dimensionless(self):
        """X, Y, Z tristimulus values are dimensionless ratios."""
        for name in ("tristimulus_X", "tristimulus_Y", "tristimulus_Z"):
            with self.subTest(name=name):
                q = quantity_by_name(name)
                for exp in q.exps_ext10:
                    self.assertEqual(exp, Fraction(0),
                                     f"{name} should be dimensionless")

    def test_astronomy_distance_concepts_are_lengths(self):
        """hubble_distance and light_year should have L=1 and all else 0."""
        for name in ("hubble_distance", "light_year"):
            with self.subTest(name=name):
                q = quantity_by_name(name)
                # L is axis index 0 in EXT10.
                self.assertEqual(q.exps_ext10[0], Fraction(1))
                for i, exp in enumerate(q.exps_ext10[1:], start=1):
                    self.assertEqual(exp, Fraction(0),
                                     f"{name} axis {i} should be 0")


if __name__ == "__main__":
    unittest.main()
