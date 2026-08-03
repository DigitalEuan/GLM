import csv
import unittest

import spatial_chemistry_discovery as discovery


class SpatialChemistryDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = discovery.run()

    def test_blast_masks_are_exact_golay_linear_responses(self):
        records = self.result["blast"]["per_message_bit"]
        self.assertEqual(len(records), 12)
        self.assertEqual(sorted(r["total_changed_code_bits"] for r in records), [8] * 11 + [12])
        self.assertTrue(all(sum(r["changed_bits_by_destination_row"]) == r["total_changed_code_bits"]
                            for r in records))

    def test_discrete_gray_clock_has_one_message_flip_per_tick(self):
        for audit in self.result["temporal_orderings"].values():
            self.assertEqual(audit["message_hamming_distribution"], {1: 117})
            self.assertEqual(audit["golay_burst_distribution"], {8: 59, 12: 58})
            self.assertEqual(sum(audit["message_bit_flip_counts"]), 117)

    def test_declared_orderings_expose_expected_controls(self):
        audits = self.result["temporal_orderings"]
        self.assertGreater(audits["group_then_period_positive_control"]["adjacent_same_group_fraction"], 0.8)
        self.assertLess(audits["seeded_random_negative_control"]["adjacent_same_group_fraction"], 0.15)

    def test_pair_scores_are_valid_heldout_aucs(self):
        for relation in self.result["pairwise_heldout_auc"].values():
            self.assertEqual(set(relation), {
                "atomic_number", "gray_message", "golay_hamming", "spatial_arithmetic",
                "fixed_mog_geometry", "training_selected_mog_geometry"})
            self.assertTrue(all(0.0 <= value <= 1.0 for value in relation.values()))

    def test_layout_selection_is_recorded_per_fold(self):
        with discovery.PAIR_CSV.open(newline="", encoding="utf-8") as handle:
            records = list(csv.DictReader(handle))
        selected = [row for row in records if row["configuration"] == "training_selected_mog_geometry"]
        self.assertEqual(len(selected), 10)
        self.assertTrue(all(row["selected_layout_index"] and row["selected_train_auc"] for row in selected))
        self.assertEqual(len(records), 2 * 5 * 6)


if __name__ == "__main__":
    unittest.main()
