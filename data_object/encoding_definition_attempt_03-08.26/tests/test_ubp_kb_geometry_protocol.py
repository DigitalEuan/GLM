import csv
import json
import math
import unittest

import ubp_kb_geometry_protocol as protocol


class TypedKBGeometryProtocolTests(unittest.TestCase):
    def test_typed_table_is_complete_and_lossless(self):
        protocol.write_outputs()
        with protocol.TYPED_OUT.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 118 * 5)
        self.assertEqual({row["channel"] for row in rows}, set(protocol.CHANNEL_METADATA))
        self.assertTrue(all(row["value_exact"] and row["status"] for row in rows))
        self.assertEqual(sum(row["uncertainty"] == "exact" for row in rows), 118)
        self.assertEqual(sum(row["uncertainty"] == "not_reported" for row in rows), 118 * 4)
        self.assertTrue(all("unresolved" in row["unit"] for row in rows if row["channel"] == "density"))

    def test_three_named_zones_are_disjoint_golay_octads(self):
        audit = protocol.octad_zone_audit()
        self.assertTrue(audit["partition_all_24_coordinates"])
        self.assertEqual(len(audit["zones"]), 3)
        self.assertTrue(all(zone["is_golay_octad"] for zone in audit["zones"]))
        self.assertEqual({c for zone in audit["zones"] for c in zone["coordinates"]}, set(range(24)))

    def test_projection_is_published_and_loss_is_measured(self):
        audit = protocol.projection_audit()
        self.assertEqual(audit["matrix_rank"], 3)
        self.assertEqual(audit["row_gram_before_dividing_by_24"],
                         [[24, 0, 0], [0, 24, 0], [0, 0, 24]])
        self.assertEqual(len(audit["projection_signs"]), 3)
        self.assertTrue(all(len(row) == 24 for row in audit["projection_signs"]))
        metrics = audit["distance_and_neighborhood_audit"]
        self.assertEqual(metrics["pair_count"], math.comb(24, 2))
        self.assertGreater(metrics["mean_relative_distance_error"], 0)
        self.assertLess(metrics["directed_nearest_neighbor_recall"], 1)
        self.assertGreater(metrics["projected_point_collisions"], 0)

    def test_particle_document_is_protocol_not_retroactive_prediction(self):
        result = protocol.prospective_particle_protocol()
        self.assertEqual(result["status"], "protocol_only_not_a_prospective_result")
        self.assertIn("after protocol freeze", result["data_split_rule"])
        self.assertEqual(len(result["baselines"]), 3)


if __name__ == "__main__":
    unittest.main()
