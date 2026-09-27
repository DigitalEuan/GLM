"""Tests for the v4.2 fundamental-constants expansion of the physics register.

Six named constants are added, taking the register from 720 to 726.  They
were chosen because they close concrete gaps that the reasoning runtime hits
in practice: without ``speed_of_light`` the register cannot even state
``energy = mass * speed_of_light^2``.

Each constant is a *dimensional* record only.  The register stores an EXT10
exponent vector and a decimal scale; it does not store numerical values, so
nothing here asserts a measured magnitude.  A constant whose unit is not an
exact power of ten of its SI coherent unit (the electronvolt, for instance)
is deliberately **not** added, because its ``scale`` coordinate could only be
recorded approximately and the register is exact by construction.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.data_objects.physics import (PhysicsCodec,
                                                load_physics_register,
                                                quantity_by_name)
from glm_universal.runtime.session import GeometricSession

#: name -> expected EXT10 exponents (L, M, T, I, H, N, J, A, S, B)
NEW_CONSTANTS = {
    "speed_of_light": (1, 0, -1, 0, 0, 0, 0, 0, 0, 0),
    "fine_structure_constant": (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    "rydberg_constant": (-1, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    "neutron_mass": (0, 1, 0, 0, 0, 0, 0, 0, 0, 0),
    "atomic_mass_constant": (0, 1, 0, 0, 0, 0, 0, 0, 0, 0),
    "impedance_of_free_space": (2, 1, -3, -2, 0, 0, 0, 0, 0, 0),
}

EXPECTED_COUNT_V3 = 726  # 660 + 41 + 19 + 6


class TestPhysicsConstants(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.register = load_physics_register()
        cls.codec = PhysicsCodec()

    def test_register_size_is_726(self):
        self.assertEqual(len(self.register), EXPECTED_COUNT_V3)

    def test_names_remain_unique(self):
        names = [q.name for q in self.register]
        self.assertEqual(len(names), len(set(names)))

    def test_every_constant_is_present(self):
        for name in NEW_CONSTANTS:
            with self.subTest(name=name):
                self.assertIsNotNone(quantity_by_name(name))

    def test_every_constant_round_trips(self):
        for name in NEW_CONSTANTS:
            with self.subTest(name=name):
                self.codec.check(quantity_by_name(name))

    def test_every_constant_has_the_right_dimensions(self):
        for name, exps in NEW_CONSTANTS.items():
            with self.subTest(name=name):
                q = quantity_by_name(name)
                self.assertEqual(tuple(q.exps_ext10),
                                 tuple(Fraction(e) for e in exps))

    def test_every_constant_has_unit_decimal_scale(self):
        # A constant is expressed in the coherent SI unit, so its scale
        # coordinate is exactly zero.  Nothing here is approximated.
        for name in NEW_CONSTANTS:
            with self.subTest(name=name):
                self.assertEqual(quantity_by_name(name).scale, Fraction(0))

    def test_no_numeric_value_is_claimed(self):
        # The register is dimensional.  Guard against a later edit smuggling
        # a measured magnitude into a field that is meant to be exact.
        for name in NEW_CONSTANTS:
            with self.subTest(name=name):
                q = quantity_by_name(name)
                for value in (q.scale, *q.exps_ext10):
                    self.assertIsInstance(value, Fraction)


class TestConstantsUnlockReasoning(unittest.TestCase):
    """The point of the expansion: queries that used to fail now resolve."""

    @classmethod
    def setUpClass(cls):
        cls.session = GeometricSession()

    def test_mass_energy_equivalence_verifies(self):
        sol = self.session.ask("verify energy = mass * speed_of_light^2")
        self.assertTrue(sol.ok)
        self.assertIn("holds", sol.answer)

    def test_mass_energy_without_the_square_is_rejected(self):
        sol = self.session.ask("verify energy = mass * speed_of_light")
        self.assertTrue(sol.ok)
        self.assertIn("does not hold", sol.answer)

    def test_free_space_impedance_is_a_resistance(self):
        sol = self.session.ask("verify impedance_of_free_space = resistance")
        self.assertTrue(sol.ok)
        self.assertIn("holds", sol.answer)

    def test_rydberg_constant_is_a_wavenumber(self):
        sol = self.session.ask("verify rydberg_constant = wavenumber")
        self.assertTrue(sol.ok)
        self.assertIn("holds", sol.answer)

    def test_constants_are_describable(self):
        for name in NEW_CONSTANTS:
            with self.subTest(name=name):
                sol = self.session.ask(f"describe {name}")
                self.assertTrue(sol.ok, sol.answer)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
