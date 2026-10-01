"""The two open archive questions, pinned.

``glm_universal.reasoning.deep_dive`` is the computational half of
``studies/ARCHIVE_DEEP_DIVE_STUDY.md``, and each of its results is also a
theorem in ``RequestProject/GLM/TriadChance.lean`` or
``RequestProject/GLM/Relaxation.lean``.  This file fixes the numbers, so that a
change to the substrate that moved any of them would fail here rather than
quietly rewriting the study.

The Lean file is the specification (D8) and everything here is exact (D7).
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from itertools import combinations

from glm_universal.reasoning import deep_dive as dd
from glm_universal.reasoning import salvage as slv


class TestChanceCensus(unittest.TestCase):
    """The balance test against the null distribution."""

    def test_all_eight_subsets_are_walked(self):
        census = dd.chance_census()
        self.assertEqual(sum(census.values()), 735471)

    def test_the_chance_census_is_the_lean_one(self):
        # GLM.Triad.chance_census
        self.assertEqual(dd.chance_census(),
                         {0: 37800, 2: 319200, 4: 314580, 6: 55440,
                          8: 7728, 10: 720, 12: 3})

    def test_every_deviation_is_even(self):
        self.assertTrue(all(d % 2 == 0 for d in dd.chance_census()))

    def test_chance_alone_gives_about_thirty_nine(self):
        # GLM.Triad.expected_balanced
        self.assertEqual(dd.chance_expected_balanced(), Fraction(12600, 323))
        self.assertLess(Fraction(38), dd.chance_expected_balanced())
        self.assertLess(dd.chance_expected_balanced(), Fraction(40))

    def test_the_observed_census_is_the_archive_one(self):
        self.assertEqual(dd.observed_census(),
                         {0: 44, 2: 336, 4: 312, 6: 58, 8: 9})

    def test_the_excess_over_chance_is_five_octads(self):
        excess = Fraction(44) - dd.chance_expected_balanced()
        self.assertEqual(excess, Fraction(1612, 323))
        self.assertLess(excess, Fraction(6))


class TestRelabelling(unittest.TestCase):
    """Balance is not an invariant of the code."""

    def test_transposition_range_is_twenty_seven_to_sixty_three(self):
        spread = dd.transposition_range()
        self.assertEqual(spread["transpositions"], 276)
        self.assertEqual(spread["minimum"], 27)
        self.assertEqual(spread["maximum"], 63)

    def test_forty_four_is_not_special(self):
        spread = dd.transposition_range()
        self.assertEqual(spread["transpositions_giving_the_identity_value"],
                         21)
        self.assertEqual(spread["mean"], Fraction(5777, 138))

    def test_the_swap_witness(self):
        # GLM.Triad.balanced_after_swap / deviation_ten_after_swap
        swap = dd.swap_witness(0, 8)
        self.assertEqual(swap["balanced_before"], 44)
        self.assertEqual(swap["balanced_after"], 49)
        self.assertEqual(swap["deviation_ten_before"], 0)
        self.assertEqual(swap["deviation_ten_after"], 1)
        self.assertTrue(swap["balance_is_not_invariant"])

    def test_a_whole_block_sits_at_twelve(self):
        # GLM.Triad.dev_twelve_class
        self.assertEqual(dd.block_deviation(), (12, 12, 12))
        self.assertLess(max(dd.observed_census()), 12)

    def test_the_extreme_class_is_not_a_family(self):
        rows = dd.deviation_eight_octads()
        self.assertEqual(len(rows), 9)
        self.assertEqual(len({row["block_split"] for row in rows}), 6)
        self.assertEqual(len({row["distances"] for row in rows}), 7)
        for row in rows:
            mask = sum(1 << k for k in row["cells"])
            self.assertEqual(len(row["cells"]), 8)
            self.assertEqual(dd.deviation(mask), 8)
            self.assertEqual(row["distances"], slv.axis_distances(mask))


class TestDescentDepth(unittest.TestCase):
    """How far a single flip goes, and how many flips are needed."""

    def test_every_column_weight_is_odd(self):
        # GLM.Golay24.colWt_odd, colWt_le_eleven
        weights = dd.column_weights()
        self.assertEqual(len(weights), 24)
        self.assertTrue(all(w % 2 == 1 for w in weights))
        self.assertEqual(max(weights), 11)
        self.assertEqual(sorted(weights), [1] * 12 + [7] * 11 + [11])

    def test_the_drop_identity(self):
        columns = dd.syndrome_columns()
        for syndrome in (0, 1, 0b101010101010, 0xFFF, 0x59A):
            weight = bin(syndrome).count("1")
            for column in columns:
                drop = weight - bin(syndrome ^ column).count("1")
                overlap = bin(syndrome & column).count("1")
                self.assertEqual(drop,
                                 2 * overlap - bin(column).count("1"))

    def test_the_best_drop_census(self):
        # GLM.Golay24.drop_census
        census = dd.best_drop_census()
        self.assertEqual(census, {1: 1486, 3: 1342, 5: 957, 7: 286,
                                  9: 22, 11: 2})
        self.assertEqual(sum(census.values()), 4095)
        self.assertTrue(all(d % 2 == 1 for d in census))

    def test_the_fastest_descent_census(self):
        # GLM.Golay24.descend_within_four / five / six
        fastest = dd.fastest_descent_census()
        self.assertEqual(fastest["census"],
                         {0: 1, 1: 24, 2: 210, 3: 1298, 4: 1771,
                          5: 726, 6: 66})
        self.assertEqual(fastest["within_four"], 3304)
        self.assertEqual(fastest["within_five"], 4030)
        self.assertEqual(fastest["within_six"], 4096)
        self.assertEqual(fastest["mean_steps"], Fraction(1931, 512))

    def test_six_is_attained(self):
        # GLM.Golay24.not_descend_five_pair
        self.assertEqual(dd.fastest_descent_census()["worst_case"], 6)

    def test_the_greedy_rule_is_a_convention_and_not_optimal(self):
        greedy = dd.greedy_descent_census()
        self.assertEqual(greedy["total_steps"], 16020)
        self.assertEqual(greedy["mean_steps"], Fraction(4005, 1024))
        self.assertEqual(dd.greedy_descent_census(prefer_last=True)
                         ["total_steps"], 16152)
        self.assertGreater(greedy["mean_steps"],
                           dd.fastest_descent_census()["mean_steps"])

    def test_the_energy_bound_is_tight(self):
        # GLM.Golay24.exists_slow_path
        longest = dd.longest_path_census()
        self.assertTrue(longest["equals_popcount"])
        self.assertEqual(longest["total"], 24576)
        self.assertEqual(longest["census"][12], 1)
        self.assertEqual(longest["census"][6], 924)


class TestRelaxationIsNotDecoding(unittest.TestCase):
    """Descent reaches the code, but often not the nearest codeword."""

    def test_the_leader_census(self):
        self.assertEqual(dd.leader_census(),
                         {0: 1, 1: 24, 2: 276, 3: 2024, 4: 1771})
        self.assertEqual(sum(dd.leader_census().values()), 4096)

    def test_seven_hundred_and_ninety_two_are_trapped(self):
        # GLM.Golay24.relaxation_is_not_decoding
        trapped = dd.trapped_census()
        self.assertEqual(trapped["trapped"], 792)
        self.assertEqual(trapped["joint_census"], {"2,6": 66, "3,5": 726})
        self.assertTrue(trapped["descent_is_not_decoding"])

    def test_the_worst_family_is_the_message_half_pairs(self):
        trapped = dd.trapped_census()
        self.assertEqual(trapped["worst_case_steps"], 6)
        self.assertEqual(trapped["worst_case_cosets"], 66)
        self.assertEqual(trapped["message_pairs"], 66)
        self.assertTrue(trapped["worst_case_is_the_message_pairs"])
        self.assertEqual(len(list(combinations(range(12), 2))), 66)


class TestReport(unittest.TestCase):
    """The one-call report carries both halves."""

    def test_sections(self):
        report = dd.deep_dive_report()
        self.assertIn("balance", report)
        self.assertIn("relaxation", report)
        self.assertEqual(report["codewords"], 4096)
        self.assertEqual(len(report["lean_files"]), 2)

    def test_the_verdicts_are_present(self):
        report = dd.deep_dive_report()
        self.assertIn("near-blind", report["balance"]["verdict"])
        self.assertIn("coset leader", report["relaxation"]["verdict"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
