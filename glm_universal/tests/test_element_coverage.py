"""Tests for widening the chemistry register without inventing a measurement.

The element register is sparse, and the tempting repair -- paste in a bigger
table -- is the one thing this module must not do.  What is pinned here is
that each of the three honest repairs keeps its label:

* **derive** -- an attribute that is an exact function of fields already
  present is computed exactly, is absent exactly where its inputs are, and is
  labelled ``derived``;
* **estimate** -- the covalent-radius line is a genuine rational
  least-squares fit (checked against the normal equations, not against the
  code that produced it), every value it produces is labelled ``estimated``,
  and its residuals are reported beside it and are honestly in-sample;
* **cross-check** -- the element register's single-bond enthalpy and the
  diatomic register's ``D0`` are compared and *not* merged, and the elements
  where they disagree by hundreds of kJ/mol are named.

And the invariant that makes all three safe: nothing is written back into the
element register, so a caller that asks for measurements still gets only
measurements.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.data_objects import elements as el
from glm_universal.reasoning import element_coverage as ec
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import REPORT_SUBJECTS, GeometricSession


# ===========================================================================
# 1.  WHAT IS THERE
# ===========================================================================

class TestCoverageTable(unittest.TestCase):

    def setUp(self):
        self.table = ec.coverage_table()

    def test_the_table_counts_every_element(self):
        self.assertEqual(self.table["elements"], 118)
        self.assertEqual(len(el.load_element_register()), 118)

    def test_each_count_is_recomputed_from_the_register(self):
        register = el.load_element_register()
        for field, count in self.table["counts"].items():
            with self.subTest(field=field):
                self.assertEqual(
                    count,
                    sum(1 for e in register
                        if getattr(e, field, None) is not None))

    def test_the_cell_totals_add_up(self):
        self.assertEqual(self.table["total_cells"],
                         self.table["elements"] * len(self.table["counts"]))
        self.assertEqual(self.table["filled_cells"],
                         sum(self.table["counts"].values()))
        self.assertLess(self.table["filled_cells"], self.table["total_cells"])

    def test_a_complete_field_really_is_complete(self):
        for field in self.table["complete_fields"]:
            with self.subTest(field=field):
                self.assertEqual(self.table["counts"][field],
                                 self.table["elements"])

    def test_a_sparse_field_is_present_for_fewer_than_half(self):
        for field in self.table["sparse_fields"]:
            with self.subTest(field=field):
                self.assertLess(self.table["counts"][field] * 2,
                                self.table["elements"])

    def test_the_sparsest_field_is_the_sparsest(self):
        sparsest = self.table["sparsest"]
        self.assertIsNotNone(sparsest)
        self.assertEqual(self.table["counts"][sparsest],
                         min(self.table["counts"].values()))


# ===========================================================================
# 2.  DERIVE
# ===========================================================================

class TestDerived(unittest.TestCase):

    def test_every_derived_attribute_declares_its_rule(self):
        for name, (rule, unit, basis) in ec.DERIVED_ATTRIBUTES.items():
            with self.subTest(name=name):
                self.assertTrue(callable(rule))
                self.assertTrue(unit)
                self.assertTrue(basis)

    def test_a_derived_value_is_exactly_its_definition(self):
        carbon = el.element_by_symbol("C")
        liquid = ec.derived_attribute(carbon, "liquid_range_K")
        self.assertEqual(liquid.value,
                         Fraction(carbon.boiling_point_K)
                         - Fraction(carbon.melting_point_K))
        self.assertEqual(liquid.provenance, "derived")

    def test_molar_volume_is_weight_over_density(self):
        for symbol in ("Fe", "Cu", "Al", "Au"):
            with self.subTest(symbol=symbol):
                element = el.element_by_symbol(symbol)
                value = ec.derived_attribute(
                    element, "molar_volume_cm3_per_mol").value
                self.assertEqual(value,
                                 Fraction(element.atomic_weight_u)
                                 / Fraction(element.density_g_per_cm3))

    def test_a_derived_value_is_absent_exactly_where_its_inputs_are(self):
        for name, (rule, _u, _b) in ec.DERIVED_ATTRIBUTES.items():
            for element in el.load_element_register():
                with self.subTest(name=name, symbol=element.symbol):
                    attribute = ec.derived_attribute(element, name)
                    self.assertEqual(attribute.value is None,
                                     rule(element) is None)

    def test_every_derived_value_is_an_exact_rational(self):
        for element in el.load_element_register():
            for name in ec.DERIVED_ATTRIBUTES:
                attribute = ec.derived_attribute(element, name)
                if attribute.value is not None:
                    self.assertIsInstance(attribute.value, Fraction)
                    self.assertNotIsInstance(attribute.value, float)

    def test_an_unknown_derived_attribute_is_refused_by_name(self):
        with self.assertRaises(KeyError):
            ec.derived_attribute(el.element_by_symbol("H"), "no_such_thing")

    def test_the_coverage_summary_matches_the_attributes(self):
        summary = ec.derived_coverage()
        self.assertEqual(summary["attribute_count"],
                         len(ec.DERIVED_ATTRIBUTES))
        self.assertEqual(
            summary["new_cells"],
            sum(int(row["available"])
                for row in summary["attributes"].values()))
        for name, row in summary["attributes"].items():
            with self.subTest(name=name):
                rule = ec.DERIVED_ATTRIBUTES[name][0]
                self.assertEqual(
                    row["available"],
                    sum(1 for e in el.load_element_register()
                        if rule(e) is not None))


# ===========================================================================
# 3.  ESTIMATE, WITH THE ERROR MEASURED
# ===========================================================================

class TestEstimates(unittest.TestCase):

    def setUp(self):
        self.model = ec.covalent_radius_model()

    def test_the_line_is_fitted_and_exact(self):
        self.assertTrue(self.model["fitted"])
        self.assertIsInstance(self.model["slope"], Fraction)
        self.assertIsInstance(self.model["intercept_pm"], Fraction)

    def test_the_line_satisfies_the_normal_equations(self):
        """Checked against the least-squares conditions, not against the code.

        For the true least-squares line the residuals sum to zero and are
        orthogonal to the regressor.  Both are exact identities over the
        rationals, so they hold on the nose rather than to a tolerance.
        """
        pairs = [(Fraction(e.atomic_radius_pm), Fraction(e.covalent_radius_pm))
                 for e in el.load_element_register()
                 if e.atomic_radius_pm is not None
                 and e.covalent_radius_pm is not None]
        slope, intercept = self.model["slope"], self.model["intercept_pm"]
        residuals = [y - (slope * x + intercept) for x, y in pairs]
        self.assertEqual(sum(residuals), 0)
        self.assertEqual(sum(r * x for r, (x, _y) in zip(residuals, pairs)), 0)

    def test_the_fit_uses_exactly_the_elements_that_carry_both(self):
        both = sum(1 for e in el.load_element_register()
                   if e.atomic_radius_pm is not None
                   and e.covalent_radius_pm is not None)
        self.assertEqual(self.model["fitted_on"], both)

    def test_the_reported_residual_statistics_are_the_real_ones(self):
        pairs = [(e.symbol, Fraction(e.atomic_radius_pm),
                  Fraction(e.covalent_radius_pm))
                 for e in el.load_element_register()
                 if e.atomic_radius_pm is not None
                 and e.covalent_radius_pm is not None]
        slope, intercept = self.model["slope"], self.model["intercept_pm"]
        residuals = {s: y - (slope * x + intercept) for s, x, y in pairs}
        self.assertEqual(
            self.model["mean_absolute_residual_pm"],
            sum(abs(r) for r in residuals.values()) / len(residuals))
        worst = max(residuals, key=lambda s: abs(residuals[s]))
        self.assertEqual(self.model["worst_element"], worst)
        self.assertEqual(self.model["max_absolute_residual_pm"],
                         abs(residuals[worst]))

    def test_the_caveat_says_the_residuals_are_in_sample(self):
        self.assertIn("in-sample", self.model["caveat"])

    def test_an_estimate_is_produced_only_where_there_is_no_measurement(self):
        report = ec.estimated_covalent_radii()
        estimated = {symbol for symbol, _value in report["estimates"]}
        for symbol in estimated:
            with self.subTest(symbol=symbol):
                element = el.element_by_symbol(symbol)
                self.assertIsNone(element.covalent_radius_pm)
                self.assertIsNotNone(element.atomic_radius_pm)

    def test_the_coverage_fractions_are_exact_and_improve(self):
        report = ec.estimated_covalent_radii()
        self.assertEqual(report["coverage_before"],
                         Fraction(report["measured_count"], 118))
        self.assertEqual(
            report["coverage_after"],
            Fraction(report["measured_count"] + report["estimate_count"], 118))
        self.assertGreater(report["coverage_after"], report["coverage_before"])

    def test_what_cannot_be_estimated_is_listed_rather_than_filled(self):
        report = ec.estimated_covalent_radii()
        estimated = {symbol for symbol, _value in report["estimates"]}
        for symbol in report["still_absent"]:
            with self.subTest(symbol=symbol):
                element = el.element_by_symbol(symbol)
                self.assertIsNone(element.covalent_radius_pm)
                self.assertIsNone(element.atomic_radius_pm)
                self.assertNotIn(symbol, estimated)
        self.assertEqual(
            report["measured_count"] + report["estimate_count"]
            + len(report["still_absent"]), 118)


# ===========================================================================
# 4.  CROSS-CHECK, NOT MERGE
# ===========================================================================

class TestCrossCheck(unittest.TestCase):

    def setUp(self):
        self.cross = ec.diatomic_cross_check()

    def test_every_row_is_a_real_pair_of_stored_values(self):
        elements = {e.symbol: e for e in el.load_element_register()}
        for row in self.cross["rows"]:
            with self.subTest(element=row["element"]):
                element = elements[row["element"]]
                self.assertEqual(row["single_bond_kJ_per_mol"],
                                 Fraction(element.homonuclear_bde_kJ_per_mol))
                self.assertEqual(row["difference"],
                                 row["diatomic_d0_kJ_per_mol"]
                                 - row["single_bond_kJ_per_mol"])

    def test_the_rows_are_ordered_by_how_badly_they_disagree(self):
        differences = [abs(row["difference"]) for row in self.cross["rows"]]
        self.assertEqual(differences, sorted(differences, reverse=True))

    def test_the_two_quantities_differ_where_the_bond_is_not_single(self):
        by_element = {row["element"]: row for row in self.cross["rows"]}
        for symbol in ("C", "P", "S"):
            with self.subTest(symbol=symbol):
                self.assertGreater(abs(by_element[symbol]["difference"]), 100)
                self.assertIn(symbol, self.cross["disagree_beyond_20"])

    def test_nitrogen_agrees_because_the_register_holds_the_triple_bond(self):
        """The finding the naive reading of the field would miss.

        If the element register's homonuclear field were uniformly a
        *single*-bond enthalpy, nitrogen would disagree with D0 by some
        600 kJ/mol.  It agrees to within 4, because the stored figure for
        nitrogen is already the triple-bond value.  The module says so
        rather than presenting the agreement as a validation.
        """
        by_element = {row["element"]: row for row in self.cross["rows"]}
        self.assertLess(abs(by_element["N"]["difference"]), 20)
        self.assertIn("N", self.cross["agree_within_20"])
        self.assertNotIn("N", self.cross["disagree_beyond_20"])
        self.assertIn("triple-bond", self.cross["statement"])

    def test_the_statement_names_exactly_the_elements_that_disagree(self):
        for symbol in self.cross["disagree_beyond_20"]:
            with self.subTest(symbol=symbol):
                self.assertIn(f"{symbol}2", self.cross["statement"])
        self.assertEqual(
            self.cross["disagree_beyond_20_count"]
            + self.cross["agree_within_20_count"],
            self.cross["compared"])

    def test_the_close_agreements_are_within_twenty(self):
        for row in self.cross["rows"]:
            with self.subTest(element=row["element"]):
                self.assertEqual(row["element"] in self.cross["agree_within_20"],
                                 abs(row["difference"]) <= 20)

    def test_nothing_is_merged_into_the_element_register(self):
        before = {e.symbol: e.homonuclear_bde_kJ_per_mol
                  for e in el.load_element_register()}
        ec.diatomic_cross_check()
        ec.element_coverage_report()
        after = {e.symbol: e.homonuclear_bde_kJ_per_mol
                 for e in el.load_element_register()}
        self.assertEqual(before, after)

    def test_the_statement_says_they_are_not_the_same_quantity(self):
        self.assertIn("not the same quantity", self.cross["statement"])


# ===========================================================================
# 5.  PROVENANCE PER ELEMENT
# ===========================================================================

class TestProvenance(unittest.TestCase):

    def test_every_attribute_carries_one_of_the_declared_provenances(self):
        for symbol in ("H", "C", "Fe", "Sc", "U"):
            for attribute in ec.attributes_of(symbol):
                with self.subTest(symbol=symbol, name=attribute.name):
                    self.assertIn(attribute.provenance, ec.PROVENANCES)

    def test_a_measured_value_is_the_register_s_own(self):
        element = el.element_by_symbol("C")
        by_name = {a.name: a for a in ec.attributes_of("C")
                   if a.provenance == "measured"}
        self.assertEqual(by_name["atomic_weight_u"].value,
                         Fraction(element.atomic_weight_u))

    def test_asking_for_measurements_only_gives_measurements_only(self):
        """Scandium has an atomic radius but no measured covalent radius."""
        with_estimates = ec.attributes_of("Sc", include_estimates=True)
        without = ec.attributes_of("Sc", include_estimates=False)
        self.assertTrue(any(a.provenance == "estimated"
                            for a in with_estimates))
        self.assertFalse(any(a.provenance == "estimated" for a in without))
        self.assertFalse(any(a.name == "covalent_radius_pm"
                             for a in without))

    def test_an_estimated_value_names_the_fit_it_came_from(self):
        estimated = [a for a in ec.attributes_of("Sc")
                     if a.provenance == "estimated"]
        self.assertEqual(len(estimated), 1)
        self.assertIn("least-squares", estimated[0].basis)
        self.assertIn("residual", estimated[0].basis)

    def test_an_element_with_a_measured_radius_gets_no_estimate(self):
        for attribute in ec.attributes_of("C"):
            self.assertNotEqual(attribute.provenance, "estimated")


# ===========================================================================
# 6.  THE REPORT SUBJECT, AND COLUMN 3
# ===========================================================================

class TestReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sess = GeometricSession()
        cls.sol = cls.sess.ask("report chemistry coverage")

    def test_chemistry_coverage_is_a_declared_report_subject(self):
        self.assertIn("chemistry coverage", REPORT_SUBJECTS)

    def test_the_report_answers_and_states_all_three_repairs(self):
        self.assertTrue(self.sol.ok)
        for word in ("derived", "residual", "cross-check"):
            with self.subTest(word=word):
                self.assertIn(word, self.sol.answer)

    def test_the_report_says_nothing_is_written_back(self):
        self.assertIn("nothing is written back", self.sol.answer)

    def test_every_alias_reaches_the_same_subject(self):
        for alias in ("report coverage", "report element coverage",
                      "report covalent radius"):
            with self.subTest(alias=alias):
                sol = self.sess.ask(alias)
                self.assertTrue(sol.ok)
                self.assertEqual(sol.expected["filled_cells"],
                                 self.sol.expected["filled_cells"])

    def test_column_three_is_generated_and_exact(self):
        source = tct.render_script(self.sol)
        ok, offenders = tct.script_is_exact(source)
        self.assertTrue(ok, f"column 3 is not exact: {offenders}")

    def test_column_three_reproduces_column_two(self):
        trace = tct.verify_trace(tct.build_trace(self.sol))
        self.assertIsNotNone(trace.verdict)
        self.assertEqual(trace.verdict.returncode, 0,
                         trace.verdict.stderr_tail)
        self.assertTrue(trace.verdict.matches_column2,
                        trace.verdict.mismatches)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
