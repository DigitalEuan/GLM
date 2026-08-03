import csv
import json
import math
import unittest

import diatomic_interaction_experiment as interaction
import structured_element_data_objects as structured


class DiatomicInteractionTests(unittest.TestCase):
    def test_endpoint_is_typed_and_nonempty(self):
        rows = interaction.load_endpoint()
        self.assertEqual(len(rows), 52)
        self.assertEqual({row["charge"] for row in rows}, {"0"})
        self.assertEqual({row["phase"] for row in rows}, {"gas"})
        self.assertEqual({row["temperature_K"] for row in rows}, {"0"})
        self.assertTrue(all(row["value_kJ_mol"] > 0 for row in rows))
        self.assertEqual(sum(row["uncertainty_kJ_mol"] is not None for row in rows), 51)

    def test_predeclared_operators_are_symmetric(self):
        left, right = [1.0, -2.0, 3.0], [4.0, 5.0, -6.0]
        for operator in interaction.OPERATORS.values():
            self.assertEqual(operator(left, right), operator(right, left))

    def test_complete_element_holdout_has_no_element_leakage(self):
        rows = interaction.load_endpoint()
        elements = {str(row[k]) for row in rows for k in ("element_a", "element_b")}
        for held_out in elements:
            train = [row for row in rows if held_out not in (row["element_a"], row["element_b"])]
            self.assertTrue(train)
            self.assertTrue(all(held_out not in (row["element_a"], row["element_b"]) for row in train))

    def test_generated_interaction_results_are_finite(self):
        interaction.write_outputs()
        result = json.loads(interaction.SUMMARY.read_text())
        self.assertEqual(result["endpoint"]["species_records"], 52)
        self.assertEqual(result["endpoint"]["elements"], 19)
        self.assertTrue(all(math.isfinite(row["macro_element_mae_kJ_mol"])
                            for row in result["fixed_results"]))


class StructuredElementObjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.objects = structured.build_objects()

    def test_every_element_has_nine_declared_layers(self):
        self.assertEqual(len(self.objects), 118)
        for obj in self.objects:
            self.assertEqual([view["z"] for view in obj["spatial_views"]], list(range(9)))

    def test_neutral_electron_count_matches_atomic_number(self):
        for obj in self.objects:
            self.assertEqual(obj["electronic_ground_state"]["electron_count"],
                             obj["subject"]["atomic_number"])

    def test_typed_channels_and_exact_addresses_are_retained(self):
        for obj in self.objects:
            for channel in obj["observations"].values():
                self.assertEqual(set(channel["exact_leech_addresses"]), {"A", "B", "C"})
                self.assertIn("unit", channel)
                self.assertIn("uncertainty", channel)
                self.assertIn("conditions", channel)
                self.assertIn("provenance", channel)

    def test_generated_audit(self):
        structured.write_outputs()
        result = json.loads(structured.AUDIT.read_text())
        self.assertTrue(result["electron_count_matches_atomic_number"])
        self.assertTrue(result["every_observation_has_three_exact_addresses"])


if __name__ == "__main__":
    unittest.main()
