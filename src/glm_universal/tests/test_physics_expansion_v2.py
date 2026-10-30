"""Tests for the v0.5.1 second physics expansion.

Adds 19 more concepts to take the register from 701 → 720 (726 after the
v4.2 constants expansion), with unique
names that avoid clashes with existing concepts.  The new concepts span
optics (3), quantum (3), materials (4), electrochemistry (3), plasma (2),
meteorology (2), and biophysics (2).
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.data_objects.physics import (PhysicsCodec,
                                                  load_physics_register,
                                                  quantity_by_name)

NEW_CONCEPT_NAMES_V2 = (
    # Optics (3)
    "refractive_index_medium", "abbe_dispersion_number", "diopter_power",
    # Quantum (3)
    "expectation_value_position", "standard_deviation_position",
    "compton_wavelength_electron",
    # Materials (4)
    "yield_stress", "fracture_stress", "elastic_modulus", "toughness_modulus",
    # Electrochemistry (3)
    "standard_electrode_potential", "exchange_current_per_area",
    "nernst_slope",
    # Plasma (2)
    "debye_screening_length", "ionization_fraction",
    # Meteorology (2)
    "dew_point_temperature", "saturation_vapor_pressure",
    # Biophysics (2)
    "resting_potential_cell", "action_potential_amplitude",
)

EXPECTED_COUNT_V2 = 726  # 660 + 41 (v0.5.0) + 19 (v0.5.1) + 6 (v4.2)


class TestPhysicsExpansionV2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.register = load_physics_register()
        cls.codec = PhysicsCodec()

    def test_register_size_is_726(self):
        self.assertEqual(len(self.register), EXPECTED_COUNT_V2)

    def test_every_v2_concept_is_present(self):
        for name in NEW_CONCEPT_NAMES_V2:
            with self.subTest(name=name):
                q = quantity_by_name(name)
                self.assertIsNotNone(q, f"{name} missing from register")

    def test_every_v2_concept_round_trips(self):
        for name in NEW_CONCEPT_NAMES_V2:
            with self.subTest(name=name):
                q = quantity_by_name(name)
                self.codec.check(q)

    def test_v2_concepts_have_correct_dimensions(self):
        # Spot-check a few of the new concepts against their expected EXT10.
        cases = [
            # name, expected (L, M, T, I, H, N, J, A, S, B)
            ("refractive_index_medium", (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
            ("diopter_power", (-1, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
            ("expectation_value_position", (1, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
            ("compton_wavelength_electron", (1, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
            ("yield_stress", (-1, 1, -2, 0, 0, 0, 0, 0, 0, 0)),
            ("elastic_modulus", (-1, 1, -2, 0, 0, 0, 0, 0, 0, 0)),
            ("toughness_modulus", (-1, 1, -2, 0, 0, 0, 0, 0, 0, 0)),
            ("standard_electrode_potential", (2, 1, -3, -1, 0, 0, 0, 0, 0, 0)),
            ("exchange_current_per_area", (-2, 0, 0, 1, 0, 0, 0, 0, 0, 0)),
            ("debye_screening_length", (1, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
            ("ionization_fraction", (0, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
            ("dew_point_temperature", (0, 0, 0, 0, 1, 0, 0, 0, 0, 0)),
            ("saturation_vapor_pressure", (-1, 1, -2, 0, 0, 0, 0, 0, 0, 0)),
            ("resting_potential_cell", (2, 1, -3, -1, 0, 0, 0, 0, 0, 0)),
            ("action_potential_amplitude", (2, 1, -3, -1, 0, 0, 0, 0, 0, 0)),
        ]
        for name, expected in cases:
            with self.subTest(name=name):
                q = quantity_by_name(name)
                actual = tuple(int(Fraction(x)) for x in q.exps_ext10)
                self.assertEqual(actual, expected,
                                 f"{name}: EXT10 mismatch")


if __name__ == "__main__":
    unittest.main()
