import json
import unittest

import leech_class_data_objects as subject


class LeechClassDataObjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = subject.inventory()

    def test_exact_class_cardinalities(self):
        self.assertEqual({name: len(items) for name, items in self.vectors.items()},
                         {"A": 1104, "B": 97152, "C": 98304})
        self.assertEqual(sum(map(len, self.vectors.values())), 196560)

    def test_all_vectors_have_minimal_norm(self):
        for items in self.vectors.values():
            self.assertEqual({sum(x*x for x in vector) for vector in items}, {32})

    def test_classes_are_distinct_shape_families(self):
        supports = {name: {sum(x != 0 for x in vector) for vector in items}
                    for name, items in self.vectors.items()}
        absolutes = {name: {tuple(sorted(abs(x) for x in vector if x)) for vector in items}
                     for name, items in self.vectors.items()}
        self.assertEqual(supports, {"A": {2}, "B": {8}, "C": {24}})
        self.assertEqual(len({next(iter(values)) for values in absolutes.values()}), 3)

    def test_golay_inventory_drives_b_and_c_counts(self):
        words = subject.golay_words()
        self.assertEqual(len(words), 4096)
        self.assertEqual(sum(sum(word) == 8 for word in words), 759)
        self.assertEqual(len(self.vectors["B"]), 759 * 128)
        self.assertEqual(len(self.vectors["C"]), 24 * 4096)

    def test_stable_channel_addresses_are_distinct_per_family(self):
        addresses = subject.stable_addresses(self.vectors)
        for family, mapping in addresses.items():
            self.assertEqual(len(mapping), len(subject.ALL_CHANNELS))
            self.assertEqual(len(set(mapping.values())), len(subject.ALL_CHANNELS))
            self.assertTrue(all(0 <= index < len(self.vectors[family]) for index in mapping.values()))

    def test_generated_outputs_have_all_elements(self):
        subject.write_outputs()
        with subject.OBJECTS.open(encoding="utf-8") as handle:
            objects = [json.loads(line) for line in handle]
        self.assertEqual(len(objects), 118)
        self.assertEqual([obj["subject"]["atomic_number"] for obj in objects], list(range(1, 119)))
        self.assertTrue(all(set(channel["leech_addresses"]) == {"A", "B", "C"}
                            for obj in objects for channel in obj["channels"].values()))


if __name__ == "__main__":
    unittest.main()
