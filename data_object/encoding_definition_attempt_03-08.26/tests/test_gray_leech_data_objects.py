import json
import unittest

import gray_leech_data_objects as g
import golay_mog_experiments as base


class GrayLeechDataObjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        g.build()

    def test_gray_round_trip_and_consecutive_locality(self):
        for z in range(1, 119):
            self.assertEqual(g.gray_decode(g.gray_encode(z)), z)
        messages = [g.gray_message12(z) for z in range(1, 119)]
        self.assertTrue(all(g.hamming(a, b) == 1 for a, b in zip(messages, messages[1:])))

    def test_golay_words_remain_unique_but_do_not_claim_gray_adjacency(self):
        words = [base.golay_encode(g.gray_message12(z)) for z in range(1, 119)]
        self.assertEqual(len({tuple(w) for w in words}), 118)
        self.assertTrue(all(g.hamming(a, b) in (8, 12) for a, b in zip(words, words[1:])))

    def test_leech_addresses_are_distinct_minimal_and_full_rank(self):
        addresses = g.leech_addresses()
        self.assertEqual(len(addresses), 24)
        self.assertEqual(len({tuple(v) for v in addresses}), 24)
        self.assertTrue(all(sum(x * x for x in v) == 32 for v in addresses))
        self.assertEqual(g.matrix_rank([[float(x) for x in v] for v in addresses]), 24)

    def test_full_table_objects_and_typed_missingness(self):
        objects = [json.loads(line) for line in g.OUT.read_text().splitlines()]
        self.assertEqual([x["subject"]["atomic_number"] for x in objects], list(range(1, 119)))
        self.assertEqual(len({tuple(x["identity"]["golay_codeword"]) for x in objects}), 118)
        for obj in objects:
            self.assertEqual(set(obj["channels"]), set(g.CHANNEL_CELLS))
            for field, channel in obj["channels"].items():
                self.assertEqual(channel["missing"], channel["value"] is None)
                self.assertEqual(channel["mog_cell"], g.CHANNEL_CELLS[field])


if __name__ == "__main__":
    unittest.main()
