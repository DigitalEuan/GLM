"""The archive retrievals, pinned.

``glm_universal.reasoning.salvage`` recomputes everything
``studies/SOURCE_SALVAGE_AUDIT.md`` says was retrieved from
``source_material/GLM-main.zip``, and every one of those results is also a Lean
theorem in ``RequestProject/GLM/``.  This file is the third leg: it fixes the
numbers, so that a change to the substrate that moved any of them would fail
here rather than quietly rewriting the audit.

The Lean file is the specification (D8), so the assertions below are written to
match the theorem, not the other way round: where Lean proves an equality the
test asserts the equality, and where Lean proves a bound the test asserts the
bound *and* the witness the substrate attains.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import salvage as slv


class TestRetrievalTable(unittest.TestCase):
    """Every retrieval names a Lean file and an archive source."""

    def test_eleven_retrievals(self):
        self.assertEqual(len(slv.RETRIEVED), 11)

    def test_rows_are_complete(self):
        for lean, source, settles in slv.RETRIEVED:
            self.assertTrue(lean.endswith(".lean"), lean)
            self.assertTrue(source.strip())
            self.assertTrue(settles.strip())

    def test_report_carries_every_section(self):
        report = slv.salvage_report(polygon_limit=60, packing_limit=100)
        for key in ("lightspeed", "golay", "packing", "polygon", "steiner",
                    "carrier", "extraspecial", "platonic", "ldp", "triad"):
            self.assertIn(key, report)
        self.assertEqual(report["retrieved_files"], 11)


class TestFirstPassRetrievals(unittest.TestCase):
    """The nine results of the first reading still hold."""

    def test_light_chain_is_circular(self):
        light = slv.lightspeed_report()
        self.assertTrue(light["c_recovered_every_time"])
        self.assertEqual(light["refractive_index_cap_at_tax_24"],
                         Fraction(16, 9))
        self.assertTrue(light["diamond_exceeds_cap"])

    def test_weight_enumerator_agrees_with_lean(self):
        golay = slv.golay_weight_report()
        self.assertTrue(golay["agrees_with_lean"])
        self.assertEqual(golay["octads"], 759)
        self.assertEqual(golay["minimum_nonzero_weight"], 8)

    def test_perfect_lengths_are_seven_and_twentythree(self):
        self.assertEqual(slv.perfect_lengths(200), (7, 23))

    def test_polygon_identity_holds_by_traversal(self):
        poly = slv.polygon_report(limit=200)
        self.assertEqual(poly["disagreements"], 0)
        self.assertTrue(poly["no_subcycle_means_prime"])

    def test_steiner_covers_every_five_set(self):
        design = slv.steiner_report()
        self.assertTrue(design["covers_every_five_set"])
        self.assertEqual(design["max_intersection_of_distinct_octads"], 4)


class TestLiteralDataPhysics(unittest.TestCase):
    """``LDP.lean`` -- the archive's internal-experience table."""

    @classmethod
    def setUpClass(cls):
        cls.report = slv.ldp_report()

    def test_every_excited_coset_descends(self):
        self.assertEqual(self.report["excited_cosets"], 4095)
        self.assertEqual(self.report["can_descend"], 4095)
        self.assertTrue(self.report["every_excited_state_descends"])

    def test_descent_comes_from_the_systematic_half(self):
        self.assertTrue(self.report["unit_columns_are_the_last_twelve"])

    def test_mean_energy_is_six_not_the_sampled_value(self):
        self.assertEqual(self.report["mean_energy"], Fraction(6))
        self.assertNotEqual(self.report["mean_energy"],
                            self.report["archive_sampled_mean_energy"])

    def test_energy_is_bounded_by_twelve(self):
        self.assertEqual(self.report["max_energy"], 12)
        self.assertTrue(self.report["relaxation_flips_match_energy"])

    def test_relaxation_flips_clear_the_syndrome(self):
        for syndrome in (0, 1, 7, 4095, 2730):
            flips = slv.relaxation_flips(syndrome)
            self.assertEqual(len(flips), bin(syndrome).count("1"))
            self.assertTrue(all(12 <= k < 24 for k in flips))

    def test_mass_defect_is_twelve_and_tight(self):
        self.assertEqual(self.report["mass_defect_min"], 12)
        self.assertEqual(self.report["mass_defect_bound_from_min_weight"], 12)

    def test_forbidden_zone_is_empty(self):
        self.assertEqual(self.report["allowed_weights"], (0, 8, 12, 16, 24))
        self.assertEqual(self.report["forbidden_weights_present"], ())

    def test_rigidity_and_parity(self):
        self.assertTrue(self.report["rigidity_holds"])
        self.assertTrue(self.report["parity_conserved_on_octad_pairs"])

    def test_energy_vanishes_exactly_on_the_code(self):
        from glm_universal.substrate import mog
        code = mog.GolayCode()
        for mask in list(code.codeword_masks)[:32]:
            self.assertEqual(slv.energy(mask), 0)
            self.assertGreater(slv.energy(mask ^ 1), 0)


class TestTriad(unittest.TestCase):
    """``Triad.lean`` and ``TriadCensus.lean`` -- the TGIC 3-6-9."""

    @classmethod
    def setUpClass(cls):
        cls.report = slv.triad_report()

    def test_forty_four_balanced_octads(self):
        self.assertEqual(self.report["octads"], 759)
        self.assertEqual(self.report["balanced_octads"], 44)
        self.assertEqual(self.report["unbalanced_octads"], 715)

    def test_deviation_census(self):
        self.assertEqual(self.report["deviation_census"],
                         {0: 44, 2: 336, 4: 312, 6: 58, 8: 9})
        self.assertTrue(self.report["all_deviations_even"])

    def test_triad_sum_is_even_and_bounded(self):
        self.assertTrue(self.report["all_triad_sums_even"])
        self.assertLessEqual(self.report["max_triad_sum"],
                             self.report["triad_sum_bound"])

    def test_balanced_means_all_three_distances_are_four(self):
        balanced = [m for m in slv.octad_masks()
                    if slv.axis_deviation(m) == 0]
        self.assertEqual(len(balanced), 44)
        for mask in balanced:
            self.assertEqual(slv.axis_distances(mask), (4, 4, 4))

    def test_archive_scores_reproduce(self):
        self.assertEqual(self.report["class_a_deviation"], 8)
        self.assertEqual(self.report["class_c_deviation"], 12)
        self.assertTrue(self.report["class_a_matches_archive_to_five_places"])
        self.assertTrue(self.report["class_c_matches_archive_to_five_places"])

    def test_score_bounds_are_an_interval_around_the_score(self):
        lower, upper = slv.axis_score_bounds(8)
        self.assertLess(lower, upper)
        self.assertLess(upper, Fraction(1))
        self.assertEqual(slv.axis_score_bounds(0), (Fraction(1), Fraction(1)))

    def test_the_six_faces_are_three(self):
        self.assertEqual(self.report["faces_are_three"], 3)
        self.assertEqual(self.report["faces_claimed"], 6)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
