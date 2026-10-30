"""The XOR answer, pinned.

``glm_universal.reasoning.combiner`` is the computational half of
``studies/COMBINER_STUDY.md``, and every claim it makes about the substrate is
also a theorem in ``RequestProject/GLM/Combiner.lean``.  This file is the third
leg: it fixes the numbers, and it fails if a module starts using XOR without
being classified.

The Lean file is the specification (D8), so where Lean proves an equality the
test asserts the equality and where Lean proves a bound the test asserts the
bound together with the witness the substrate attains.  By D7 nothing here is
a float.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import combiner as cmb
from glm_universal.substrate import mog


class TestAffineClassification(unittest.TestCase):
    """Sixteen coordinatewise combiners, eight of them affine."""

    def test_sixteen_operations_are_named(self):
        self.assertEqual(len(cmb.OP_NAMES), 16)
        self.assertEqual(len(set(cmb.OP_NAMES)), 16)

    def test_exactly_eight_are_affine(self):
        self.assertEqual(len(cmb.affine_tables()), 8)

    def test_the_affine_ones_are_the_expected_ones(self):
        self.assertEqual(
            set(cmb.AFFINE_NAMES),
            {"false", "true", "a", "b", "not-a", "not-b", "xor", "xnor"})

    def test_xor_is_affine_and_and_is_not(self):
        self.assertEqual(cmb.affine_coefficients(6), (0, 1, 1))
        self.assertIsNone(cmb.affine_coefficients(8))
        self.assertIsNone(cmb.affine_coefficients(14))

    def test_affine_coefficients_reproduce_the_truth_table(self):
        for index in cmb.affine_tables():
            c0, c1, c2 = cmb.affine_coefficients(index)
            table = cmb.op_table(index)
            for x in (0, 1):
                for y in (0, 1):
                    self.assertEqual(table[2 * x + y],
                                     c0 ^ (c1 & x) ^ (c2 & y))

    def test_apply_op_agrees_with_python_operators(self):
        a, b = 0b101100, 0b011010
        self.assertEqual(cmb.apply_op(6, a, b), a ^ b)
        self.assertEqual(cmb.apply_op(8, a, b), a & b)
        self.assertEqual(cmb.apply_op(14, a, b), a | b)
        self.assertEqual(cmb.apply_op(0, a, b), 0)
        self.assertEqual(cmb.apply_op(15, a, b), cmb.ALL_ONES)


class TestClosure(unittest.TestCase):
    """The code is closed under exactly the affine combiners."""

    def test_closed_iff_affine(self):
        report = cmb.closure_report()
        self.assertTrue(report["closed_iff_affine"])
        self.assertEqual(report["affine_operations"], 8)
        self.assertEqual(sorted(report["closed_names"]),
                         sorted(report["affine_names"]))

    def test_every_non_affine_operation_has_a_witness(self):
        report = cmb.closure_report()
        self.assertTrue(report["non_affine_witnessed"])

    def test_the_witness_leaves_the_code(self):
        code = mog.GolayCode()
        for row in cmb.closure_table():
            if row["affine"]:
                self.assertIsNone(row["witness"], row["name"])
                continue
            a, b, out = row["witness"]
            self.assertTrue(code.is_codeword(a))
            self.assertTrue(code.is_codeword(b))
            self.assertFalse(code.is_codeword(out))
            self.assertEqual(cmb.apply_op(row["index"], a, b), out)

    def test_the_all_ones_word_is_a_codeword(self):
        # what makes the four complemented affine operations closed as well
        self.assertTrue(mog.GolayCode().is_codeword(cmb.ALL_ONES))


class TestFibres(unittest.TestCase):
    """What XOR loses, and the pigeonhole that says no combiner avoids it."""

    def test_fibre_is_two_to_the_width(self):
        self.assertEqual(cmb.xor_fibre_size(24), 16777216)
        self.assertEqual(cmb.xor_fibre_size(24), 2 ** 24)

    def test_small_width_census_is_uniform(self):
        self.assertEqual(cmb.small_fibre_census(4), {16: 16})
        self.assertEqual(cmb.small_fibre_census(3), {8: 8})

    def test_xor_attains_the_pigeonhole_bound(self):
        report = cmb.fibre_report()
        self.assertEqual(report["ordered_pairs"], 2 ** 48)
        self.assertEqual(report["words"], 2 ** 24)
        self.assertEqual(report["least_possible_largest_fibre"], 2 ** 24)
        self.assertTrue(report["xor_attains_the_bound"])
        self.assertEqual(report["bits_lost"], 24)


class TestIntegerLayer(unittest.TestCase):
    """Widen the output and the overlap comes back."""

    def test_tsum_recovers_both_classical_operations(self):
        a, b = 0b1011_0110, 0b0110_1110
        self.assertEqual(cmb.tsum_symm_diff(a, b), a ^ b)
        self.assertEqual(cmb.tsum_inter(a, b), a & b)

    def test_tsum_values_are_ternary(self):
        a, b = 0xA5A5A5, 0x3C3C3C
        self.assertTrue(all(x in (0, 1, 2) for x in cmb.tsum(a, b)))
        self.assertTrue(all(x in (-1, 0, 1) for x in cmb.tdiff(a, b)))

    def test_the_pair_is_recovered(self):
        for a, b in ((0, 0), (1, 0), (0xFFFFFF, 0), (0x0F0F0F, 0x00FF00)):
            self.assertEqual(cmb.recover_pair(cmb.tsum(a, b),
                                              cmb.tdiff(a, b)), (a, b))

    def test_ternary_image_sits_between_two_powers(self):
        report = cmb.integer_layer_report()
        self.assertEqual(report["ternary_image"], 282429536481)
        self.assertEqual(report["ternary_image"], 3 ** 24)
        self.assertTrue(2 ** 38 < report["ternary_image"] < 2 ** 39)
        self.assertTrue(report["between_two_powers"])

    def test_report_checks_recovery_on_the_code(self):
        report = cmb.integer_layer_report()
        self.assertTrue(report["xor_recovered_from_tsum"])
        self.assertTrue(report["intersection_recovered_from_tsum"])
        self.assertTrue(report["pair_recovered_from_tsum_and_tdiff"])
        self.assertEqual(report["gain_ratio"],
                         Fraction(3 ** 24, 2 ** 24))


class TestInventory(unittest.TestCase):
    """Every XOR site in the runtime is classified, and stays classified."""

    def test_inventory_is_complete(self):
        inventory = cmb.xor_inventory()
        self.assertEqual(inventory["unclassified_modules"], ())
        self.assertEqual(inventory["stale_declarations"], ())
        self.assertTrue(inventory["inventory_is_complete"])

    def test_every_declared_role_is_known(self):
        for module, roles, note in cmb.XOR_SITES:
            self.assertTrue(roles, module)
            for role in roles:
                self.assertIn(role, cmb.ROLES, module)
            self.assertTrue(note.strip(), module)

    def test_only_two_modules_ever_used_xor_as_a_combiner(self):
        inventory = cmb.xor_inventory()
        self.assertEqual(inventory["lossy_combiner_modules"],
                         ("reasoning/monster_stack.py",
                          "substrate/superposition.py"))
        self.assertEqual(len(inventory["replacements"]), 2)

    def test_the_replacements_exist(self):
        from glm_universal.reasoning import product
        from glm_universal.substrate import superposition
        self.assertTrue(callable(superposition.bundle_rational))
        self.assertTrue(callable(superposition.bundle_f2))
        self.assertTrue(callable(product.axis_product))

    def test_the_xor_bundle_really_is_degenerate(self):
        # the reason bundle_f2 was retired, restated here so the inventory's
        # "retired" verdict is not taken on trust
        from glm_universal.substrate import superposition as sup
        report = sup.bundling_report()
        self.assertTrue(report["f2_bundle_is_all_ones"])


class TestReport(unittest.TestCase):
    """The one-call report carries every section."""

    def test_sections(self):
        report = cmb.combiner_report()
        for key in ("closure", "fibres", "integer_layer", "inventory"):
            self.assertIn(key, report)
        self.assertEqual(report["lean_file"],
                         "RequestProject/GLM/Combiner.lean")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
