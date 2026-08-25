"""Tests for the molecules register and its runtime wiring.

A molecule is the first thing in the package that one carrier cannot hold
without loss, so what is checked here is mostly about *which* representation
loses what.

* the **formula grammar** reads what chemists write -- counts, nested
  brackets, hydrates, trailing charges -- and refuses, by name, what it
  cannot read;
* every coordinate is **derived** from the element register at encode time,
  so the register cannot carry a measurement that disagrees with the element
  register, and a coordinate the element register cannot support is absent
  with its bit set rather than imputed;
* the **bundle is faithful** and the **composite is a summary**: the formula
  is read straight back off the bundle for every molecule, while the
  composite is checked for collisions rather than assumed injective;
* the **wiring**: the register loads, resolves by name and by formula,
  answers `describe`, `nearest` and `analogy`, and `report molecules`
  reproduces itself in a fresh interpreter through column 3.

Everything is exact: ``int`` and ``Fraction`` only, and no float is
constructed anywhere.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.data_objects import molecules as mol
from glm_universal.data_objects.elements import element_by_symbol
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import DOMAINS, REPORT_SUBJECTS, \
    GeometricSession


# ===========================================================================
# 1.  THE FORMULA GRAMMAR
# ===========================================================================

class TestFormulaGrammar(unittest.TestCase):

    def test_plain_formulae(self):
        for text, counts in (
                ("H2O", {"H": 2, "O": 1}),
                ("CO2", {"C": 1, "O": 2}),
                ("NaCl", {"Na": 1, "Cl": 1}),
                ("C6H12O6", {"C": 6, "H": 12, "O": 6}),
                ("SF6", {"S": 1, "F": 6})):
            with self.subTest(formula=text):
                self.assertEqual(mol.parse_formula(text), (counts, 0))

    def test_nested_brackets_multiply_through(self):
        self.assertEqual(mol.parse_formula("Ca(OH)2"),
                         ({"Ca": 1, "O": 2, "H": 2}, 0))
        self.assertEqual(mol.parse_formula("Fe2(SO4)3"),
                         ({"Fe": 2, "S": 3, "O": 12}, 0))
        self.assertEqual(mol.parse_formula("K[Al(SO4)2]"),
                         ({"K": 1, "Al": 1, "S": 2, "O": 8}, 0))

    def test_a_hydrate_is_the_sum_of_its_parts(self):
        counts, charge = mol.parse_formula("CuSO4.5H2O")
        self.assertEqual(charge, 0)
        self.assertEqual(counts, {"Cu": 1, "S": 1, "O": 9, "H": 10})

    def test_trailing_charges(self):
        self.assertEqual(mol.parse_formula("SO4 2-"), ({"S": 1, "O": 4}, -2))
        self.assertEqual(mol.parse_formula("NH4 +"), ({"N": 1, "H": 4}, 1))
        self.assertEqual(mol.parse_formula("OH -"), ({"O": 1, "H": 1}, -1))

    def test_an_unknown_symbol_is_refused_by_name(self):
        with self.assertRaises(mol.FormulaError) as caught:
            mol.parse_formula("XyZ2")
        self.assertIn("Xy", str(caught.exception))

    def test_malformed_formulae_are_refused(self):
        for text in ("Ca(OH", "Ca)OH(2", "", "   ", "2H2O!"):
            with self.subTest(formula=text):
                with self.assertRaises(mol.FormulaError):
                    mol.parse_formula(text)

    def test_hill_order_round_trips_through_the_parser(self):
        for _name, formula in mol.MOLECULES:
            with self.subTest(formula=formula):
                counts, charge = mol.parse_formula(formula)
                hill = mol.format_formula(counts, charge)
                self.assertEqual(mol.parse_formula(hill), (counts, charge))

    def test_hill_order_puts_carbon_and_hydrogen_first(self):
        counts, _charge = mol.parse_formula("C2H6O")
        self.assertEqual(mol.format_formula(counts), "C2H6O")
        self.assertEqual(mol.format_formula({"O": 1, "H": 2}), "H2O")


# ===========================================================================
# 2.  THE DERIVED COORDINATES
# ===========================================================================

class TestDerivedCoordinates(unittest.TestCase):

    def setUp(self):
        self.register = mol.load_molecule_register()
        self.by_name = {m.name: m for m in self.register}

    def test_the_register_stores_only_a_name_and_a_formula(self):
        for entry in mol.MOLECULES:
            with self.subTest(entry=entry):
                self.assertEqual(len(entry), 2)
                self.assertTrue(all(isinstance(x, str) for x in entry))

    def test_molar_mass_is_the_exact_sum_over_the_element_register(self):
        water = self.by_name["water"]
        expected = (2 * Fraction(element_by_symbol("H").atomic_weight_u)
                    + Fraction(element_by_symbol("O").atomic_weight_u))
        self.assertEqual(water.molar_mass_u, expected)
        self.assertIsInstance(water.molar_mass_u, Fraction)

    def test_electron_count_is_the_nuclear_charge_less_the_ionic_charge(self):
        self.assertEqual(self.by_name["water"].electron_count, 10)
        self.assertEqual(self.by_name["ammonium ion"].electron_count, 10)
        self.assertEqual(self.by_name["hydroxide ion"].electron_count, 10)

    def test_degree_of_unsaturation_where_it_is_defined(self):
        self.assertEqual(self.by_name["benzene"].degree_of_unsaturation, 4)
        self.assertEqual(self.by_name["cyclohexane"].degree_of_unsaturation, 1)
        self.assertEqual(self.by_name["octane"].degree_of_unsaturation, 0)
        self.assertEqual(self.by_name["acetylene"].degree_of_unsaturation, 2)

    def test_degree_of_unsaturation_is_absent_where_it_means_nothing(self):
        for name in ("sulfuric acid", "potassium permanganate",
                     "iron(III) sulfate", "sodium chloride"):
            with self.subTest(name=name):
                self.assertIsNone(
                    self.by_name[name].degree_of_unsaturation)

    def test_electronegativity_mean_is_weighted_by_atom_count(self):
        water = self.by_name["water"]
        h = Fraction(element_by_symbol("H").electronegativity_pauling)
        o = Fraction(element_by_symbol("O").electronegativity_pauling)
        self.assertEqual(water.electronegativity_mean, (2 * h + o) / 3)
        self.assertEqual(water.electronegativity_spread, o - h)

    def test_carbon_mass_fraction_is_zero_without_carbon(self):
        self.assertEqual(self.by_name["water"].carbon_mass_fraction, 0)
        self.assertGreater(self.by_name["benzene"].carbon_mass_fraction,
                           Fraction(9, 10))

    def test_no_float_anywhere_in_a_carrier(self):
        for obj in mol.molecule_objects():
            with self.subTest(name=obj.name):
                for value in obj.carrier:
                    self.assertIsInstance(value, (int, Fraction))
                    self.assertNotIsInstance(value, float)


# ===========================================================================
# 3.  THE CODEC
# ===========================================================================

class TestCodec(unittest.TestCase):

    def setUp(self):
        self.codec = mol.MoleculeCodec()

    def test_every_carrier_has_24_coordinates(self):
        self.assertEqual(len(mol.MOLECULE_LAYOUT), 24)
        for obj in mol.molecule_objects():
            with self.subTest(name=obj.name):
                self.assertEqual(len(obj.carrier), 24)
                self.assertEqual(tuple(obj.layout), mol.MOLECULE_LAYOUT)

    def test_the_semantic_round_trip_holds_for_every_molecule(self):
        for molecule in mol.load_molecule_register():
            with self.subTest(name=molecule.name):
                obj = self.codec.encode(molecule)
                back = self.codec.decode(obj)
                self.assertEqual(back.counts, molecule.counts)
                self.assertEqual(back.charge, molecule.charge)

    def test_the_substrate_round_trip_holds_for_every_molecule(self):
        for obj in mol.molecule_objects():
            with self.subTest(name=obj.name):
                self.assertTrue(obj.round_trip_ok())

    def test_a_corrupted_coordinate_is_caught_rather_than_decoded(self):
        obj = self.codec.encode(mol.molecule_by_name("water"))
        carrier = list(obj.carrier)
        carrier[0] = carrier[0] + 1          # atom_count no longer matches
        broken = obj.__class__(name=obj.name, domain=obj.domain,
                               carrier=carrier, attributes=obj.attributes,
                               layout=obj.layout, provenance=obj.provenance)
        with self.assertRaises(ValueError):
            self.codec.decode(broken)

    def test_missingness_is_flagged_and_the_coordinate_is_zero(self):
        obj = self.codec.encode(mol.molecule_by_name("sulfuric acid"))
        index = mol.MOLECULE_FIELDS.index("degree_of_unsaturation")
        mask = int(obj.carrier[19])
        self.assertTrue(mask >> index & 1)
        self.assertEqual(obj.carrier[index], 0)
        self.assertIn("degree_of_unsaturation",
                      obj.attributes["missing_fields"])

    def test_nothing_is_imputed_where_the_element_register_is_silent(self):
        for obj in mol.molecule_objects():
            with self.subTest(name=obj.name):
                mask = int(obj.carrier[19])
                for i, name in enumerate(mol.MOLECULE_FIELDS):
                    if mask >> i & 1:
                        self.assertEqual(obj.carrier[i], 0)


# ===========================================================================
# 4.  BUNDLE AGAINST COMPOSITE
# ===========================================================================

class TestMultiCarrier(unittest.TestCase):

    def test_the_bundle_gives_the_formula_back_for_every_molecule(self):
        for molecule in mol.load_molecule_register():
            with self.subTest(name=molecule.name):
                bundle = mol.molecule_bundle(molecule)
                self.assertEqual(
                    mol.formula_from_bundle(bundle, molecule.charge),
                    mol.format_formula(molecule.counts, molecule.charge))

    def test_a_bundle_entry_is_the_element_s_own_carrier(self):
        from glm_universal.data_objects.elements import ElementCodec
        bundle = mol.molecule_bundle(mol.molecule_by_name("water"))
        symbols = [s for s, _c, _v in bundle]
        self.assertEqual(symbols, ["H", "O"])
        expected = ElementCodec().encode(element_by_symbol("O")).carrier
        self.assertEqual(list(bundle[1][2]), list(expected))
        self.assertEqual(bundle[0][1], 2)

    def test_the_census_of_collisions_is_computed_not_assumed(self):
        census = mol.composite_collisions()
        self.assertTrue(census["bundle_is_faithful"])
        self.assertEqual(census["bundle_collision_count"], 0)
        self.assertEqual(census["distinct_bundles"], census["molecules"])
        # Whatever the composite does, the report states it as a count.
        self.assertEqual(len(census["composite_collisions"]),
                         census["composite_collision_count"])
        self.assertEqual(census["distinct_composites"] +
                         sum(len(g) - 1
                             for g in census["composite_collisions"]),
                         census["molecules"])

    def test_two_different_molecules_never_share_a_bundle(self):
        seen = {}
        for molecule in mol.load_molecule_register():
            key = (tuple((s, c) for s, c, _v in mol.molecule_bundle(molecule)),
                   molecule.charge)
            self.assertNotIn(key, seen,
                             f"{molecule.name} and {seen.get(key)} share one "
                             f"bundle")
            seen[key] = molecule.name


# ===========================================================================
# 5.  THE RUNTIME WIRING
# ===========================================================================

class TestWiring(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sess = GeometricSession()

    def test_molecules_is_a_session_domain_and_loads(self):
        self.assertIn("molecules", DOMAINS)
        register = self.sess.register("molecules")
        self.assertEqual(len(register), len(mol.MOLECULES))
        self.assertTrue(all(o.domain == "molecules" for o in register))

    def test_describe_resolves_a_molecule_by_name(self):
        sol = self.sess.ask("describe glucose")
        self.assertTrue(sol.ok)
        self.assertEqual(sol.expected["domain"], "molecules")
        self.assertIn("C6H12O6", sol.steps[0].language)

    def test_describe_resolves_a_molecule_by_formula(self):
        sol = self.sess.ask("describe C6H12O6")
        self.assertTrue(sol.ok)
        self.assertEqual(sol.expected["domain"], "molecules")
        self.assertIn("glucose", sol.answer)

    def test_a_formula_outside_the_register_still_falls_back(self):
        """`PbCl2` is not an entry, so the reference resolver answers."""
        sol = self.sess.ask("describe PbCl2")
        self.assertTrue(sol.ok)
        self.assertIn("compound", sol.answer)

    def test_nearest_ranks_within_the_molecules_register(self):
        sol = self.sess.ask("nearest to water")
        self.assertTrue(sol.ok)
        names = {m.name for m in mol.load_molecule_register()}
        listed = sol.answer.split(":", 1)[1]
        self.assertTrue(any(name in listed for name in names))

    def test_an_analogy_over_molecules_stays_in_the_register(self):
        sol = self.sess.ask("methane : ethylene :: benzene : ?")
        self.assertTrue(sol.ok)
        self.assertEqual(sol.query.domain, "molecules")

    def test_the_describe_detail_names_the_two_representations(self):
        sol = self.sess.ask("describe sucrose")
        self.assertIn("bundle", sol.steps[0].language)
        self.assertIn("composite", sol.steps[0].language)


# ===========================================================================
# 6.  THE REPORT SUBJECT, AND COLUMN 3
# ===========================================================================

class TestReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sess = GeometricSession()
        cls.sol = cls.sess.ask("report molecules")

    def test_molecules_is_a_declared_report_subject(self):
        self.assertIn("molecules", REPORT_SUBJECTS)

    def test_the_report_answers_and_states_the_two_representations(self):
        self.assertTrue(self.sol.ok)
        self.assertIn("bundle", self.sol.answer)
        self.assertIn(str(len(mol.MOLECULES)), self.sol.answer)

    def test_every_alias_reaches_the_same_subject(self):
        for alias in ("report molecule", "report compounds",
                      "report multi-carrier"):
            with self.subTest(alias=alias):
                sol = self.sess.ask(alias)
                self.assertTrue(sol.ok)
                self.assertEqual(sol.expected["molecules"],
                                 self.sol.expected["molecules"])

    def test_the_expected_claims_are_exact_strings(self):
        for key, value in self.sol.expected.items():
            with self.subTest(key=key):
                self.assertIsInstance(value, str)

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
