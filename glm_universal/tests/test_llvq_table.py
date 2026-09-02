"""Tests for :mod:`glm_universal.reasoning.llvq_table`.

Four things are pinned here:

* the **table** -- ``(label, parity, top bit)`` really is a key on the sixteen
  column patterns, and the 128 classes it builds really are the Golay code,
  32 codewords each with nothing left over;
* the **class minimum** -- the six-term min-sum with one parity repair agrees
  with the brute-force minimum over the class's 32 words, on every class;
* the **agreement** -- the table route returns exactly what the 4,096-word
  scan returns, on the sweep, on register carriers, on boundary vectors and
  on the Lean address corpus, so nothing is resolved differently by the
  faster route;
* the **cost** -- the route really does leave most of the code unopened, and
  the figure the documents quote is the one the trace records.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from itertools import product

from glm_universal.reasoning import analogy as an
from glm_universal.reasoning import lean_address as la
from glm_universal.reasoning import llvq_table as lt
from glm_universal.substrate import leech2, mog
from glm_universal.substrate.linalg import popcount


def _delta(seed: int, spread: int = 8) -> list:
    """A deterministic reliability profile, exact rationals."""
    rng = lt._Sweep(seed)
    return [Fraction(rng.between(-spread, spread + 1), rng.between(1, 4))
            for _ in range(24)]


# ===========================================================================
# 1.  THE TABLE
# ===========================================================================

class TestTheTable(unittest.TestCase):

    def test_the_key_is_a_bijection_on_the_sixteen_patterns(self):
        self.assertEqual(len(lt.PATTERN_TABLE), 16)
        self.assertEqual(sorted(lt.PATTERN_TABLE.values()), list(range(16)))
        for (label, parity, top), value in lt.PATTERN_TABLE.items():
            with self.subTest(label=label, parity=parity, top=top):
                self.assertEqual(mog.COLUMN_LABEL[value], label)
                self.assertEqual(popcount(value) & 1, parity)
                self.assertEqual(value & 1, top)

    def test_pattern_table_returns_a_copy(self):
        copy = lt.pattern_table()
        copy.clear()
        self.assertEqual(len(lt.PATTERN_TABLE), 16)

    def test_the_three_conditions_characterise_the_code(self):
        report = lt.characterisation_report()
        self.assertEqual(report["shadow_failures"], 0)
        self.assertEqual(report["column_parity_failures"], 0)
        self.assertEqual(report["top_row_parity_failures"], 0)
        self.assertEqual(report["rebuild_failures"], 0)
        self.assertEqual(report["classes"], 128)
        self.assertEqual(report["classes_seen"], 128)
        self.assertEqual(report["class_size"], [32])
        self.assertEqual(report["classes_times_size"], 4096)
        self.assertTrue(report["accounts_for_the_code"])

    def test_the_classes_partition_the_code(self):
        seen = set()
        for word, parity in lt.CLASSES:
            members = lt.codewords_of_class(word, parity)
            self.assertEqual(len(members), 32)
            self.assertEqual(len(set(members)), 32)
            seen.update(members)
        self.assertEqual(seen, set(mog.GOLAY_MASKS))

    def test_class_of_codeword_inverts_the_build(self):
        for word, parity in lt.CLASSES[::17]:
            for member in lt.codewords_of_class(word, parity):
                with self.subTest(member=member):
                    self.assertEqual(lt.class_of_codeword(member),
                                     (word, parity))

    def test_a_hexacode_word_is_required(self):
        with self.assertRaises(ValueError):
            lt.codewords_of_class((0, 0, 0, 0, 0), 0)
        with self.assertRaises(ValueError):
            lt.codewords_of_class((0, 0, 0, 0, 0, 0), 2)


# ===========================================================================
# 2.  THE COLUMN COSTS AND THE CLASS MINIMA
# ===========================================================================

class TestClassMinima(unittest.TestCase):

    def test_column_costs_against_direct_summation(self):
        delta = _delta(11)
        costs = lt.column_costs(delta)
        for col in range(6):
            for value in range(16):
                with self.subTest(col=col, value=value):
                    direct = sum((delta[lt.CELL[col][row]]
                                  for row in range(4) if (value >> row) & 1),
                                 Fraction(0))
                    self.assertEqual(costs[col][value], direct)

    def test_column_costs_refuse_the_wrong_length(self):
        with self.assertRaises(ValueError):
            lt.column_costs([Fraction(0)] * 23)

    def test_every_class_minimum_is_the_minimum_over_its_32_words(self):
        for seed in (3, 5):
            delta = _delta(seed)
            minima = {(word, parity): value
                      for value, word, parity in lt.class_minima(delta)}
            self.assertEqual(len(minima), 128)
            for word, parity in lt.CLASSES:
                with self.subTest(seed=seed, word=word, parity=parity):
                    brute = min(
                        sum((delta[i] for i in range(24) if (mask >> i) & 1),
                            Fraction(0))
                        for mask in lt.codewords_of_class(word, parity))
                    self.assertEqual(minima[(word, parity)], brute)

    def test_the_least_class_minimum_is_the_soft_decoding_of_the_code(self):
        for seed in (7, 9):
            delta = _delta(seed)
            best = lt.class_minima(delta)[0][0]
            brute = min(
                sum((delta[i] for i in range(24) if (mask >> i) & 1),
                    Fraction(0))
                for mask in mog.GOLAY_MASKS)
            with self.subTest(seed=seed):
                self.assertEqual(best, brute)


# ===========================================================================
# 3.  THE DECODER AGREES WITH THE SCAN
# ===========================================================================

class TestAgreement(unittest.TestCase):

    def test_the_report_finds_no_mismatch(self):
        report = lt.agreement_report(samples=12)
        self.assertTrue(report["agrees"])
        self.assertEqual(report["mismatches"], 0)
        self.assertIsNone(report["first_mismatch"])
        self.assertGreaterEqual(report["checked"], 60)

    def test_point_for_point_on_the_sweep(self):
        for index, vector in enumerate(lt.sweep_vectors(8, 4242)):
            want = an.nearest_lattice_point(vector)
            got = lt.nearest_lattice_point_table(vector)
            with self.subTest(index=index):
                self.assertEqual(got.point, want.point)
                self.assertEqual(got.distance2, want.distance2)
                self.assertEqual(got.leech_class, want.leech_class)
                self.assertEqual(got.norm2, want.norm2)
                self.assertEqual(got.exact_hit, want.exact_hit)
                self.assertEqual(got.is_2a_axis, want.is_2a_axis)

    def test_a_lattice_point_decodes_to_itself(self):
        point = [Fraction(4), Fraction(4)] + [Fraction(0)] * 22
        got = lt.nearest_lattice_point_table(point)
        self.assertTrue(got.exact_hit)
        self.assertEqual(got.distance2, 0)
        self.assertTrue(leech2.in_leech(list(got.point)))

    def test_the_answer_is_always_in_the_lattice(self):
        for index, vector in enumerate(lt.sweep_vectors(6, 99)):
            with self.subTest(index=index):
                got = lt.nearest_lattice_point_table(vector)
                self.assertTrue(leech2.in_leech(list(got.point)))
                self.assertTrue(got.in_leech)

    def test_no_float_is_constructed(self):
        got = lt.nearest_lattice_point_table(lt.sweep_vectors(1, 5)[0])
        self.assertIsInstance(got.distance2, Fraction)
        for coordinate in got.point:
            self.assertIsInstance(coordinate, int)


# ===========================================================================
# 4.  WHAT IT COSTS
# ===========================================================================

class TestCost(unittest.TestCase):

    def test_the_reference_count_is_the_code_s_own_constant(self):
        counts = lt.reference_operation_counts()
        self.assertEqual(counts["codewords"], 4096)
        self.assertTrue(counts["matches_closed_form"])
        self.assertEqual(counts["additions_per_call"],
                         2 * counts["codeword_cost_additions"])

    def test_the_route_leaves_most_of_the_code_unopened(self):
        report = lt.search_cost_report(samples=8)
        self.assertEqual(report["reference_words_per_call"], 8192)
        self.assertLess(report["table_words_per_call"], 1000)
        self.assertGreater(report["words_ratio"], 8)
        self.assertLessEqual(report["worst_classes_in_a_call"], 256)

    def test_the_trace_counts_what_the_run_did(self):
        _, trace = lt.decode_with_trace(lt.sweep_vectors(1, 17)[0])
        self.assertEqual(trace.codeword_additions, 6 * trace.words_evaluated)
        self.assertEqual(trace.column_cost_additions, 2 * 6 * 16 * 4)
        self.assertGreaterEqual(trace.classes_expanded, 2)
        self.assertLessEqual(trace.words_evaluated, 8192)
        self.assertEqual(set(trace.as_dict()), set(lt.DecodeTrace.__slots__))


# ===========================================================================
# 5.  THE HOT PATH IT WAS BUILT FOR
# ===========================================================================

class TestTheAddressCorpus(unittest.TestCase):

    def test_the_addresses_are_unchanged(self):
        report = lt.corpus_report(limit=120)
        self.assertEqual(report["declarations"], 120)
        self.assertEqual(report["addresses_changed"], 0)
        self.assertTrue(report["all_unchanged"])

    def test_quantise_goes_through_the_table_and_agrees_with_the_scan(self):
        table = la.feature_table()
        for name in sorted(table)[:40]:
            vector = table[name]
            scaled = [Fraction(int(v) * la.SCALE) for v in vector]
            with self.subTest(name=name):
                self.assertEqual(
                    la.quantise(vector),
                    tuple(int(c)
                          for c in an.nearest_lattice_point(scaled).point))


# ===========================================================================
# 6.  THE SUBJECT BEHIND `report llvq`
# ===========================================================================

class TestTheReport(unittest.TestCase):

    def test_the_report_holds_together(self):
        report = lt.llvq_table_report(samples=6)
        self.assertTrue(report["characterisation"]["accounts_for_the_code"])
        self.assertTrue(report["agreement"]["agrees"])
        self.assertEqual(report["table_entries"], 16)
        self.assertEqual(report["hexacode_words"], 64)
        self.assertEqual(report["classes"], 128)
        self.assertEqual(report["class_size"], 32)


if __name__ == "__main__":                                # pragma: no cover
    unittest.main()
