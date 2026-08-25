"""Tests for :mod:`glm_universal.reasoning.units`.

The claims pinned here:

* the parser reads the grammar the register actually writes -- products,
  quotients, brackets, integer and rational powers, and the one place where
  multiplication is written as a space;
* derived units are *derived*: the lumen's exponents come from parsing
  ``cd*sr``, not from a stored vector;
* every unit string in the physics register parses and agrees with the
  EXT10 exponents declared beside it;
* the steradian is carried as a dimension, and what the SI reading of it
  would cost is measured by running the audit both ways.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.data_objects import physics as do_physics
from glm_universal.reasoning import units as un


def _dim(text: str, steradian: bool = True) -> str:
    return do_physics.dimension_string(
        un.parse_unit(text, steradian=steradian), "EXT10")


# ===========================================================================
# 1.  THE GRAMMAR
# ===========================================================================

class TestGrammar(unittest.TestCase):

    def test_a_base_unit_is_one_axis(self):
        self.assertEqual(_dim("m"), "L")
        self.assertEqual(_dim("kg"), "M")
        self.assertEqual(_dim("sr"), "S")
        self.assertEqual(_dim("rad"), "A")

    def test_products_and_quotients(self):
        self.assertEqual(_dim("kg*m/s^2"), "L M T^-2")
        self.assertEqual(_dim("J*s/rad"), "L^2 M T^-1 A^-1")

    def test_brackets_group_a_denominator(self):
        self.assertEqual(_dim("W/(m^2*sr)"), "M T^-3 S^-1")

    def test_a_space_means_multiplication(self):
        self.assertEqual(_dim("1/(rad s)"), _dim("1/(rad*s)"))

    def test_rational_powers(self):
        self.assertEqual(un.parse_unit("m^(1/2)")[0], Fraction(1, 2))
        self.assertEqual(un.parse_unit("m^(-3/2)")[0], Fraction(-3, 2))

    def test_a_prefix_changes_no_dimension(self):
        for prefixed, plain in (("km", "m"), ("mrad", "rad"), ("MOhm", "Ohm"),
                                ("Gbit", "bit"), ("umol", "mol"),
                                ("nF", "F"), ("kPa", "Pa")):
            with self.subTest(unit=prefixed):
                self.assertEqual(_dim(prefixed), _dim(plain))

    def test_a_known_symbol_is_never_read_as_a_prefixed_one(self):
        # "kat" is the katal, not kilo-anything; "kg" is a base unit.
        self.assertEqual(_dim("kat"), "T^-1 N")
        self.assertEqual(_dim("kg"), "M")

    def test_an_unknown_symbol_is_refused(self):
        with self.assertRaises(un.UnitError):
            un.parse_unit("furlong")

    def test_a_numeric_factor_other_than_one_is_refused(self):
        with self.assertRaises(un.UnitError):
            un.parse_unit("3*m")


# ===========================================================================
# 2.  DERIVED UNITS ARE DERIVED
# ===========================================================================

class TestDerivation(unittest.TestCase):

    def test_no_derived_unit_stores_its_exponents(self):
        for symbol, definition in un.DERIVED_UNITS.items():
            with self.subTest(unit=symbol):
                self.assertEqual(un.dimension_of_symbol(symbol),
                                 un.parse_unit(definition))

    def test_the_lumen_is_the_candela_steradian(self):
        self.assertEqual(_dim("lm"), "J S")

    def test_the_lux_is_the_lumen_per_square_metre(self):
        self.assertEqual(_dim("lx"), _dim("lm/m^2"))

    def test_the_watt_reaches_the_base_units_through_three_definitions(self):
        self.assertEqual(_dim("W"), _dim("kg*m^2/s^3"))

    def test_every_axis_has_exactly_one_base_unit(self):
        self.assertEqual(sorted(un.BASE_UNITS.values()), sorted(un.AXES))


# ===========================================================================
# 3.  THE REGISTER AUDIT
# ===========================================================================

class TestRegisterAudit(unittest.TestCase):

    def test_every_unit_string_parses(self):
        audit = un.register_audit()
        self.assertTrue(audit["every_unit_readable"], audit["unreadable"])

    def test_every_unit_string_agrees_with_its_declared_exponents(self):
        audit = un.register_audit()
        self.assertEqual(audit["mismatched_count"], 0, audit["mismatched"])
        self.assertTrue(audit["every_unit_agrees"])

    def test_the_audit_counts_every_quantity(self):
        audit = un.register_audit()
        self.assertEqual(audit["agreed"] + audit["mismatched_count"]
                         + audit["unreadable_count"], audit["quantities"])


# ===========================================================================
# 4.  THE STERADIAN
# ===========================================================================

class TestSteradian(unittest.TestCase):

    def test_dropping_the_steradian_conflates_the_lumen_with_the_candela(self):
        self.assertEqual(_dim("lm", steradian=False), _dim("cd"))
        self.assertNotEqual(_dim("lm"), _dim("cd"))

    def test_dropping_it_breaks_quantities_that_carrying_it_does_not(self):
        case = un.steradian_case()
        self.assertEqual(case["with_steradian"]["mismatched"], 0)
        self.assertGreater(case["without_steradian"]["mismatched"], 0)

    def test_exactly_the_quantities_with_a_solid_angle_break(self):
        case = un.steradian_case()
        self.assertEqual(set(case["quantities_broken_by_dropping_it"]),
                         set(case["quantities_with_a_solid_angle"]))

    def test_the_photometric_quantities_are_a_subset_of_the_broken_ones(self):
        case = un.steradian_case()
        self.assertTrue(set(case["photometric_quantities"])
                        <= set(case["quantities_broken_by_dropping_it"]))
        self.assertGreater(case["photometric_count"], 0)

    def test_every_conflation_names_the_quantity_it_would_be_confused_with(
            self):
        case = un.steradian_case()
        flux = [entry for entry in case["conflations"]
                if entry["name"] == "luminous_flux"]
        self.assertEqual(len(flux), 1)
        self.assertIn("luminous_intensity", flux[0]["conflated_with"])


# ===========================================================================
# 5.  THE REPORT
# ===========================================================================

class TestReport(unittest.TestCase):

    def test_the_report_recomputes_its_own_figures(self):
        report = un.units_report()
        self.assertEqual(report["base_unit_count"], len(un.BASE_UNITS))
        self.assertEqual(report["derived_unit_count"], len(un.DERIVED_UNITS))
        self.assertEqual(report["audit"]["mismatched_count"], 0)

    def test_the_report_gives_a_dimension_for_every_derived_unit(self):
        report = un.units_report()
        self.assertEqual(set(report["derived_dimensions"]),
                         set(un.DERIVED_UNITS))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
