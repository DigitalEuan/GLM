"""The second reading of the archive, pinned.

``glm_universal.reasoning.salvage_second`` recomputes everything
``studies/SOURCE_SALVAGE_SECOND_PASS.md`` says came back from the second
reading of ``source_material/GLM-main.zip``, and every one of those results is
also a Lean theorem in ``RequestProject/GLM/``.  This file is the third leg: it
fixes the numbers, so that a change which moved any of them would fail here
rather than quietly rewriting the study.

The Lean file is the specification (D8), so each assertion below names the
theorem it mirrors.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from glm_universal.reasoning import salvage_second as s2


class TestRetrievalTable(unittest.TestCase):
    """Every retrieval names a Lean file and an archive source."""

    def test_eight_retrievals(self):
        self.assertEqual(len(s2.RETRIEVED_SECOND), 8)

    def test_rows_are_complete(self):
        for lean, source, settles in s2.RETRIEVED_SECOND:
            self.assertTrue(lean.endswith(".lean"), lean)
            self.assertTrue(source.strip())
            self.assertTrue(settles.strip())

    def test_report_carries_every_section(self):
        report = s2.second_pass_report()
        for key in ("cube", "read_quantum", "gray", "tension", "lobe",
                    "modes", "stabiliser", "mirror"):
            self.assertIn(key, report)
        self.assertEqual(report["retrieved_files"], 8)


class TestCubeSurface(unittest.TestCase):
    """`CubeSurface.lean`: the code read on the six faces of a cube."""

    def setUp(self):
        self.cube = s2.cube_surface_report()

    def test_hexacode_is_sixty_four_words_of_distance_four(self):
        # CubeSurface.hexacode_card, CubeSurface.hexacode_min_dist
        self.assertEqual(self.cube["hexacode_words"], 64)
        self.assertEqual(self.cube["hexacode_min_distance"], 4)

    def test_three_layers(self):
        # CubeSurface.fibre_card, hexpass_card, mog_card, parity_layer_factor
        self.assertEqual(self.cube["fibre_sizes"], {0: 4, 1: 4, 2: 4, 3: 4})
        self.assertEqual(self.cube["hexacode_layer_grids"], 2 ** 18)
        self.assertEqual(self.cube["codewords"], 2 ** 12)
        self.assertEqual(self.cube["parity_layer_factor"], 64)

    def test_weight_enumerator(self):
        # CubeSurface.mog_weight_enumerator, mog_min_weight
        self.assertEqual(self.cube["weight_enumerator"],
                         {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1})
        self.assertEqual(self.cube["min_nonzero_weight"], 8)
        self.assertTrue(self.cube["all_parametrised_grids_are_codewords"])

    def test_one_face_heals_and_two_do_not(self):
        # CubeSurface.face_erasure_correctable, two_face_ambiguous
        self.assertEqual(self.cube["single_face_codewords"], 0)
        self.assertEqual(self.cube["two_face_pairs"], 15)
        self.assertEqual(self.cube["two_face_weights"], [8])

    def test_the_two_hexacode_presentations_differ_but_agree(self):
        report = s2.second_pass_report()
        self.assertEqual(report["hexacode_words_in_common"], 4)
        self.assertTrue(report["hexacode_presentations_agree_on_invariants"])
        self.assertEqual(report["cube_substrate_generator"]["weight_enumerator"],
                         self.cube["weight_enumerator"])


class TestReadQuantum(unittest.TestCase):
    """`ReadQuantum.lean`: the read-cost operator and the tax it induces."""

    def setUp(self):
        self.rq = s2.read_quantum_report()

    def test_Y_is_not_the_maximum_of_its_own_operator(self):
        # ReadQuantum.Y_lt_amgm
        self.assertTrue(self.rq["Y_squared_below_amgm_squared"])
        self.assertEqual(self.rq["amgm_squared"], Fraction(1, 8))

    def test_read_cost_has_no_positive_lower_bound(self):
        # ReadQuantum.readCost_le_inv, readCost_no_pos_lower_bound
        witnesses = self.rq["read_cost_decay"]
        self.assertEqual(witnesses[1000], Fraction(1, 1000))
        self.assertTrue(all(a > b for a, b in
                            zip(witnesses.values(), list(witnesses.values())[1:])))

    def test_only_two_regimes_on_twentyfour_signed_coordinates(self):
        # ReadQuantum.signed24_tax_le, signed24_regime
        self.assertTrue(self.rq["signed24_below_budget"])
        low, high = self.rq["max_signed24_tax_interval"]
        self.assertLess(high, 10)
        self.assertGreater(low, Fraction(9))

    def test_onbit_is_exactly_six_activations(self):
        # ReadQuantum.signed_onBit_iff
        self.assertTrue(self.rq["onbit_boundary"]["six_Q_below"])
        self.assertTrue(self.rq["onbit_boundary"]["seven_Q_above"])

    def test_protection_costs_eight_quanta(self):
        # ReadQuantum.regime_coherent_of_hammingWeight_ge_eight
        self.assertTrue(self.rq["octad_is_coherent_not_onbit"])
        low, high = self.rq["octad_tax_interval"]
        self.assertGreater(low, Fraction(5, 2))
        self.assertLess(high, 4)


class TestGrayJump(unittest.TestCase):
    """`GrayJump.lean`: the shortcut formula and the parity law."""

    def setUp(self):
        self.gray = s2.gray_jump_report()

    def test_shortcut_formula(self):
        # GrayJump.d2_eq_pop_gray_xor
        self.assertTrue(self.gray["shortcut_formula_holds"])

    def test_adjacent_integers_are_at_distance_one(self):
        # GrayJump.d2_succ, d2_interfacial_all_one
        self.assertTrue(self.gray["walk_all_one"])
        self.assertEqual(self.gray["published_walk_values"], [1])

    def test_parity_law_and_odd_jumps(self):
        # GrayJump.d2_mod_two, exists_odd_d2
        self.assertTrue(self.gray["parity_law_holds"])
        self.assertTrue(self.gray["even_is_not_a_property_of_this_layer"])
        self.assertEqual(self.gray["odd_jump_norms_in_sample"],
                         self.gray["sample"] ** 2 // 2)


class TestGridTension(unittest.TestCase):
    """`GridTension.lean`: the bounds the archive's float geometry becomes."""

    def setUp(self):
        self.t = s2.grid_tension_report()

    def test_the_hypotheses_the_bounds_need(self):
        # GridTension.tension_lt_inv_sq needs 2 pi / N <= 1, i.e. N >= 7.
        self.assertEqual(self.t["smallest_N_with_two_pi_over_N_at_most_one"], 7)
        self.assertTrue(self.t["pi_squared_below_ten"])

    def test_tension_bound_is_rational_and_decays(self):
        # GridTension.tension_lt_ten_div_sq
        bounds = self.t["tension_upper_bounds"]
        self.assertEqual(bounds[7], Fraction(10, 49))
        self.assertEqual(bounds[24], Fraction(10, 576))
        self.assertTrue(all(bounds[n] > bounds[n + 1]
                            for n in range(7, max(bounds))))

    def test_radius_bracket_is_narrow(self):
        # GridTension.circumradius_gt, circumradius_lt
        self.assertTrue(self.t["bracket_width_below_one_over_N"])
        low, high = self.t["radius_brackets"][24]
        self.assertLess(low, high)


class TestConditionalLobe(unittest.TestCase):
    """`ConditionalInduction.lean`: the census of the archive's induction."""

    def setUp(self):
        self.lobe = s2.conditional_lobe_report()

    def test_the_universe_is_six_thousand_five_hundred_and_sixty_one(self):
        self.assertEqual(self.lobe["observations"], 3 ** 8)

    def test_survivor_distribution(self):
        # ConditionalInduction.census_survivors
        self.assertEqual(self.lobe["survivor_distribution"],
                         {0: 5193, 1: 1232, 2: 111, 3: 20, 4: 4, 5: 0, 6: 1})
        self.assertEqual(sum(self.lobe["survivor_distribution"].values()), 3 ** 8)

    def test_sound(self):
        # ConditionalInduction.induce_sound
        self.assertEqual(self.lobe["unsound_answers"], 0)

    def test_incomplete(self):
        # ConditionalInduction.census_missed
        self.assertEqual(self.lobe["gave_up_though_separable"], 56)

    def test_the_order_is_a_tie_break(self):
        # ConditionalInduction.census_ambiguous, census_committed
        self.assertEqual(self.lobe["ambiguous_observations"], 136)
        self.assertEqual(self.lobe["answered_while_ambiguous"], 119)


class TestModeAlgebra(unittest.TestCase):
    """`ModeAlgebra.lean`: Kracht signs, and the cost of the argmax."""

    def setUp(self):
        self.m = s2.mode_algebra_report()

    def test_the_category_space(self):
        # ModeAlgebra.card_all
        self.assertEqual(self.m["categories"], 7 ** 4)
        # ModeAlgebra.card_dominance
        self.assertEqual(list(self.m["dominance_census"].values()),
                         [784, 644, 532, 441])
        self.assertEqual(sum(self.m["dominance_census"].values()), 7 ** 4)

    def test_every_category_is_realised_by_a_word(self):
        # ModeAlgebra.catOf_surjective, and the fibre count behind it
        self.assertEqual(self.m["fibre_total"], 2 ** 24)
        self.assertTrue(self.m["fibre_total_is_two_to_the_24"])

    def test_licensed_counts(self):
        # ModeAlgebra.card_subjectOk, card_verbOk, svo_licensed_triples
        self.assertEqual(self.m["subject_licensed"], 1724)
        self.assertEqual(self.m["verb_licensed"], 1717)
        self.assertEqual(self.m["svo_licensed_triples"],
                         1724 * 1717 * 1724)
        # ModeAlgebra.definition_licensed_pairs
        self.assertEqual(self.m["definition_licensed_pairs"], 784 * 784)

    def test_the_argmax_collapse_is_lossy_for_the_svo_mode(self):
        # ModeAlgebra.svo_not_a_function_of_dominant_role
        self.assertEqual(self.m["argmax_collapse_witnesses"], 1185)
        lo, hi = self.m["smallest_collapse_witness"]
        self.assertEqual(s2._dominant_role(lo), s2._dominant_role(hi))
        self.assertTrue(s2._verb_ok(lo))
        self.assertFalse(s2._verb_ok(hi))

    def test_the_property_role_is_unreachable(self):
        # ModeAlgebra.dominantRole_ne_property
        self.assertTrue(self.m["property_role_unreachable"])

    def test_the_contradiction_mode_can_never_fire(self):
        # ModeAlgebra.contradiction_never_definite,
        # ModeAlgebra.strongness_is_strictly_stronger
        self.assertEqual(self.m["contradiction_category_pairs"], 784 * 784)
        self.assertEqual(self.m["contradiction_definite_pairs"], 0)
        # ModeAlgebra.card_labels, card_indefinite_labels
        self.assertEqual(self.m["labels"], 18)
        self.assertEqual(self.m["indefinite_labels"], 2)


class TestCubeStabiliser(unittest.TestCase):
    """`CubeStabiliser.lean`: which surface symmetries cost no syndrome."""

    def setUp(self):
        self.st = s2.cube_stabiliser_report()

    def test_the_group(self):
        # CubeStabiliser.cubeSym_card, rotation_count
        self.assertEqual(self.st["symmetries"], 48)
        self.assertEqual(self.st["rotations"], 24)

    def test_twelve_are_free_and_they_are_tetrahedral(self):
        # CubeStabiliser.stabiliser_card, preserves_iff_tetrahedral
        self.assertEqual(self.st["free_under_canonical_placement"], 12)
        self.assertTrue(self.st["free_are_the_tetrahedral_group"])

    def test_a_rotation_that_is_not_free(self):
        # CubeStabiliser.quarterTurn_isRot, quarterTurn_not_preserving
        self.assertTrue(self.st["quarter_turn_is_a_rotation"])
        self.assertFalse(self.st["quarter_turn_is_free"])

    def test_the_second_placement_is_a_golay_code(self):
        # CubeStabiliser.oCode_card, oCode_min_weight, oCode_weight_enumerator
        self.assertEqual(self.st["second_placement_codewords"], 2 ** 12)
        self.assertEqual(self.st["second_placement_min_weight"], 8)
        self.assertEqual(self.st["second_placement_weight_enumerator"],
                         {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1})

    def test_the_second_placement_frees_every_rotation(self):
        # CubeStabiliser.oCode_rotations_free, oCode_improper_priced
        self.assertEqual(self.st["second_placement_free"], 24)
        self.assertTrue(self.st["second_placement_frees_every_rotation"])
        self.assertTrue(self.st["second_placement_prices_every_reflection"])


class TestCubeMirror(unittest.TestCase):
    """`Golay/CubeMirror.lean`: 24 is the ceiling, by a parity count."""

    def setUp(self):
        self.mr = s2.cube_mirror_report()

    def test_the_mirror_is_an_involution_with_four_fixed_cells(self):
        # CubeMirror.sigmaD_involutive, sigmaD_fixed_card
        self.assertTrue(self.mr["is_an_involution"])
        self.assertEqual(self.mr["fixed_cells"], 4)
        self.assertEqual(self.mr["transposed_pairs"], 10)
        self.assertEqual(4 + 2 * 10, self.mr["cells"])

    def test_the_mirror_is_a_reflection_inside_Td(self):
        # CubeMirror.sigmaD_not_rotation, sigmaD_mem_Td
        self.assertTrue(self.mr["mirror_is_a_reflection"])
        self.assertTrue(self.mr["mirror_lies_in_Td"])

    def test_two_hundred_and_twenty_invariant_five_sets(self):
        # CubeMirror.inv5_card
        self.assertEqual(self.mr["invariant_five_sets"], 220)

    def test_the_fibres_are_multiples_of_six_and_220_is_not(self):
        # CubeMirror.six_dvd_fiber, no_diagonal_mirror_invariant_golay
        self.assertEqual(self.mr["invariant_octad_fibres"],
                         {0: 0, 2: 6, 4: 12})
        self.assertTrue(self.mr["every_fibre_is_a_multiple_of_six"])
        self.assertFalse(self.mr["six_divides_the_count"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
