import csv
import math
import unittest

import golay_mog_experiments as e


class ExactEncodingTests(unittest.TestCase):
    def test_all_element_addresses_round_trip_and_are_unique(self):
        words = []
        for z in range(1, 119):
            msg = e.message12(z)
            self.assertEqual(sum(msg[i] << i for i in range(7)), z)
            words.append(tuple(e.golay_encode(msg)))
        self.assertEqual(len(set(words)), 118)

    def test_full_golay_weight_distribution(self):
        counts = {}
        for n in range(4096):
            cw = e.golay_encode([(n >> i) & 1 for i in range(12)])
            counts[sum(cw)] = counts.get(sum(cw), 0) + 1
        self.assertEqual(counts, {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1})

    def test_mog_assignment_is_permutation(self):
        self.assertEqual(sorted(e.MOG_GRID_BITS), list(range(24)))

    def test_geometry_feature_dimensions_are_finite(self):
        bits = e.mog_bits(e.golay_encode(e.message12(79)))
        for kind in ("planar", "stacked", "cylinder", "sphere"):
            f = e.geometry_features(bits, kind)
            self.assertEqual(len(f), 10)
            self.assertTrue(all(math.isfinite(v) for v in f))

    def test_processed_data_has_all_elements(self):
        rows = e.read_and_normalize()
        self.assertEqual([int(r["AtomicNumber"]) for r in rows], list(range(1, 119)))


if __name__ == "__main__":
    unittest.main()
