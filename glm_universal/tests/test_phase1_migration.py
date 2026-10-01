"""Phase 1: complete Golay decoding and the legacy-to-core migration.

Two modules are pinned here.

``substrate/golay_decode``
    The complete syndrome decoder that retired the package's ``snap``.  These
    tests pin the coset census, the fact that no tie is ever broken silently,
    and the computational proof -- via the Steiner system ``S(5, 8, 24)`` --
    that a weight-5 error is decoded confidently and wrongly by *any*
    nearest-codeword rule, so that behaviour is a theorem about the code
    rather than a defect of the decoder.

``substrate/isomorphism``
    The coordinate permutation relating the project's legacy Golay frame to
    this package's canonical one, the checks that make it safe to wrap around
    a decoder (weight and distance preservation), and the bulk migration of
    concepts, CRG edges and hexcolour addresses.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession
from glm_universal.substrate import golay_decode as GD
from glm_universal.substrate import isomorphism as ISO
from glm_universal.substrate.mog import GOLAY_MASKS, GOLAY_SET


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


def popcount(mask: int) -> int:
    return bin(mask).count("1")


# ===========================================================================
# 1.  THE COSET TABLE
# ===========================================================================

class TestCosetTable:

    def test_every_syndrome_has_leaders(self):
        table = GD.coset_table()
        assert len(table) == 4096
        for syndrome, leaders in table.items():
            assert 0 <= syndrome < 4096
            assert leaders
            weights = {popcount(e) for e in leaders}
            assert len(weights) == 1, "leaders must share one weight"

    def test_census_is_the_expected_partition(self):
        census = GD.coset_census()
        assert census["cosets"] == 4096
        assert census["cosets_by_leader_weight"] == {
            0: 1, 1: 24, 2: 276, 3: 2024, 4: 1771}
        assert sum(census["cosets_by_leader_weight"].values()) == 4096

    def test_leader_is_unique_below_the_packing_radius(self):
        census = GD.coset_census()
        assert census["unique_below_radius_4"] is True
        assert census["sextet_at_radius_4"] is True

    def test_weight_four_cosets_carry_six_leaders_each(self):
        census = GD.coset_census()
        assert census["leader_counts_by_weight"][4] == [6]
        assert 1771 * 6 == 10626  # = C(24, 4)


# ===========================================================================
# 2.  DECODING, AND THE TIES THAT ARE NOT BROKEN
# ===========================================================================

class TestDecodeComplete:

    def test_a_codeword_decodes_to_itself(self):
        for word in GOLAY_MASKS[:32]:
            d = GD.decode_complete(word)
            assert d.status == "codeword"
            assert d.corrected == word
            assert d.weight == 0
            assert d.guaranteed is True

    def test_single_errors_are_corrected_with_a_guarantee(self):
        word = GOLAY_MASKS[7]
        for bit in range(24):
            d = GD.decode_complete(word ^ (1 << bit))
            assert d.status == "corrected"
            assert d.corrected == word
            assert d.guaranteed is True

    def test_weight_four_is_ambiguous_and_never_guessed(self):
        word = GOLAY_MASKS[3]
        received = word ^ 0b1111
        d = GD.decode_complete(received)
        assert d.weight == 4
        assert d.status == "ambiguous"
        assert d.corrected is None
        assert len(d.leaders) == 6
        assert len(set(d.candidates)) == 6
        assert d.guaranteed is False

    def test_decode_or_detect_refuses_to_guess(self):
        word = GOLAY_MASKS[3]
        codeword, status = GD.decode_or_detect(word ^ 0b1111)
        assert codeword is None
        assert status == "ambiguous"

    def test_every_candidate_really_is_a_codeword_at_the_stated_distance(self):
        word = GOLAY_MASKS[11]
        received = word ^ 0b1011
        d = GD.decode_complete(received)
        for candidate in d.candidates:
            assert candidate in GOLAY_SET
            assert popcount(candidate ^ received) == d.weight

    def test_out_of_range_input_is_refused(self):
        with pytest.raises(ValueError):
            GD.decode_complete(1 << 24)
        with pytest.raises(TypeError):
            GD.decode_complete("0")  # type: ignore[arg-type]


# ===========================================================================
# 3.  WEIGHT 5 IS A THEOREM, NOT A BUG
# ===========================================================================

class TestWeightFiveMiscorrection:

    def test_the_octads_form_a_steiner_system(self):
        report = GD.steiner_system_report()
        assert report["octads"] == 759
        assert report["five_subsets_total"] == 42504
        assert report["five_subsets_covered"] == 42504
        assert report["multiplicities"] == [1]
        assert report["is_steiner_5_8_24"] is True

    def test_every_weight_five_error_lands_at_coset_weight_three(self):
        report = GD.weight5_miscorrection_report()
        assert report["coset_weights"] == {3: report["sampled"]}
        assert report["always_coset_weight_3"] is True
        assert report["always_miscorrected"] is True
        assert report["always_inside_packing_radius"] is True

    def test_the_confident_answer_is_the_wrong_one(self):
        witness = GD.weight5_miscorrection_report()["witness"]
        assert witness["coset_weight"] == 3
        assert witness["distance_to_truth"] == 5
        assert witness["status"] == "corrected"
        assert witness["guaranteed"] is True


# ===========================================================================
# 4.  THE PERMUTATION
# ===========================================================================

class TestPermutationAlgebra:

    def test_legacy_to_core_is_a_permutation(self):
        assert ISO.is_permutation(ISO.LEGACY_TO_CORE)
        assert sorted(ISO.LEGACY_TO_CORE) == list(range(24))

    def test_inverse_round_trips(self):
        assert ISO.invert_permutation(ISO.LEGACY_TO_CORE) == ISO.CORE_TO_LEGACY
        assert ISO.invert_permutation(ISO.CORE_TO_LEGACY) == ISO.LEGACY_TO_CORE

    def test_composition_with_the_inverse_is_the_identity(self):
        identity = tuple(range(24))
        assert ISO.compose_permutations(
            ISO.LEGACY_TO_CORE, ISO.CORE_TO_LEGACY) == identity

    def test_mask_round_trip(self):
        for word in GOLAY_MASKS[:64]:
            assert ISO.to_legacy_mask(ISO.to_core_mask(word)) == word

    def test_mask_permutation_preserves_weight(self):
        for word in GOLAY_MASKS[:256]:
            assert popcount(ISO.to_core_mask(word)) == popcount(word)

    def test_vector_round_trip_keeps_exact_entries(self):
        vector = tuple(Fraction(i, 8) for i in range(24))
        moved = ISO.to_core_vector(vector)
        assert sorted(moved) == sorted(vector)
        assert ISO.to_legacy_vector(moved) == vector
        for entry in moved:
            assert isinstance(entry, Fraction)

    def test_a_float_coordinate_is_refused(self):
        with pytest.raises(TypeError):
            ISO.permute_vector([0.5] + [0] * 23)

    def test_index_permutation_agrees_with_mask_permutation(self):
        indices = (0, 3, 7, 19)
        mask = sum(1 << i for i in indices)
        moved = ISO.permute_indices(indices)
        assert sum(1 << i for i in moved) == ISO.to_core_mask(mask)

    def test_a_non_permutation_is_refused(self):
        with pytest.raises(ValueError):
            ISO.permute_mask(1, tuple([0] * 24))


class TestHexcolour:

    def test_round_trip_through_the_mask(self):
        for word in GOLAY_MASKS[:32]:
            colour = ISO.mask_to_hexcolour(word)
            assert colour.startswith("#") and len(colour) == 7
            assert ISO.hexcolour_to_mask(colour) == word

    def test_migration_permutes_the_coordinate_set(self):
        colour = ISO.mask_to_hexcolour(GOLAY_MASKS[5])
        migrated = ISO.migrate_hexcolour(colour)
        assert ISO.hexcolour_to_mask(migrated) == ISO.to_core_mask(
            GOLAY_MASKS[5])

    def test_a_malformed_address_is_refused(self):
        with pytest.raises(ValueError):
            ISO.hexcolour_to_mask("#abc")
        with pytest.raises(ValueError):
            ISO.hexcolour_to_mask("#zzzzzz")


# ===========================================================================
# 5.  TWO CODES, ONE BRIDGE
# ===========================================================================

class TestTwoCodes:

    def test_the_legacy_code_is_a_distinct_equivalent_code(self):
        report = ISO.code_report()
        assert report["legacy_codewords"] == 4096
        assert report["legacy_is_distinct"] is True
        assert report["weight_distributions_agree"] is True
        assert report["minimum_distance"] == 8
        assert report["octads_legacy"] == 759

    def test_the_two_codes_share_exactly_eight_codewords(self):
        assert len(ISO.shared_codewords()) == 8

    def test_the_bridge_maps_the_legacy_code_onto_the_canonical_one(self):
        for word in ISO.legacy_code()[:256]:
            assert ISO.to_core_mask(word) in GOLAY_SET

    def test_it_is_not_an_automorphism_and_a_witness_says_why(self):
        report = ISO.is_golay_automorphism()
        assert report["is_automorphism"] is False
        witness = report["witness"]
        assert witness is not None
        assert witness["codeword"] in GOLAY_SET
        assert witness["image"] not in GOLAY_SET
        assert popcount(witness["codeword"]) == popcount(witness["image"])

    def test_it_is_an_isometry_so_it_commutes_with_decoding(self):
        report = ISO.isometry_report()
        assert report["weight_preserving"] is True
        assert report["distance_preserving"] is True
        assert report["commutes_with_decoding"] is True


# ===========================================================================
# 6.  DECODING LEGACY DATA
# ===========================================================================

class TestDecodeLegacy:

    def test_a_legacy_codeword_decodes_to_itself_in_its_own_frame(self):
        for word in ISO.legacy_code()[:16]:
            out = ISO.decode_legacy(word)
            assert out["status"] == "codeword"
            assert out["corrected"] == word

    def test_errors_within_the_packing_radius_are_repaired(self):
        word = ISO.legacy_code()[9]
        for bits in (0b1, 0b101, 0b10101):
            out = ISO.decode_legacy(word ^ bits)
            assert out["status"] == "corrected"
            assert out["corrected"] == word
            assert out["guaranteed"] is True

    def test_weight_four_is_flagged_rather_than_guessed(self):
        word = ISO.legacy_code()[9]
        out = ISO.decode_legacy(word ^ 0b1111)
        assert out["status"] == "ambiguous"
        assert out["corrected"] is None
        assert len(out["candidates"]) == 6

    def test_the_retired_snap_broke_those_ties_silently(self):
        word = ISO.legacy_code()[9]
        _best, distance, tied = ISO.legacy_snap_in_legacy_frame(word ^ 0b1111)
        assert distance == 4
        assert tied == 6

    def test_the_comparison_turns_every_silent_tie_into_a_flag(self):
        report = ISO.legacy_decoder_comparison()
        assert report["snap_silent_ties_total"] > 0
        assert report["every_silent_tie_is_now_flagged"] is True
        assert report["guaranteed_below_packing_radius"] is True

    def test_weight_five_still_miscorrects_in_both_columns(self):
        rows = {row["weight"]: row
                for row in ISO.legacy_decoder_comparison()["rows"]}
        assert rows[5]["snap_recovered"] == 0
        assert rows[5]["routed_recovered"] == 0
        assert rows[5]["routed_miscorrected"] == rows[5]["sampled"]


# ===========================================================================
# 7.  BULK MIGRATION
# ===========================================================================

class TestBulkMigration:

    def test_only_the_named_fields_move(self):
        record = {"id": "c1", "label": "keep me", "mask": 0b1011,
                  "provenance": "legacy"}
        out = ISO.migrate_record(record, ISO.CONCEPT_SPEC)
        assert out["id"] == "c1"
        assert out["label"] == "keep me"
        assert out["provenance"] == "legacy"
        assert out["mask"] == ISO.to_core_mask(0b1011)

    def test_a_missing_field_is_not_invented(self):
        out = ISO.migrate_record({"id": "c1"}, ISO.CONCEPT_SPEC)
        assert out == {"id": "c1"}

    def test_the_whole_dataset_round_trips(self):
        data = ISO.sample_dataset()
        migrated = ISO.migrate_dataset(data["concepts"], data["edges"],
                                       data["hexcolours"])
        checks = migrated["checks"]
        assert checks["round_trip"] is True
        assert checks["weights_preserved"] is True
        assert checks["masks_still_distinct"] is True
        assert checks["referentially_intact"] is True
        assert checks["dangling_edges"] == 0

    def test_edge_endpoints_are_identifiers_and_are_left_alone(self):
        data = ISO.sample_dataset()
        migrated = ISO.migrate_dataset(data["concepts"], data["edges"],
                                       data["hexcolours"])
        for before, after in zip(data["edges"], migrated["edges"]):
            assert after["source"] == before["source"]
            assert after["target"] == before["target"]
            assert after["weight"] == before["weight"]
            assert after["mask"] == ISO.to_core_mask(before["mask"])

    def test_a_dangling_edge_is_reported_rather_than_hidden(self):
        concepts = [{"id": "a", "mask": 1}]
        edges = [{"id": "e", "source": "a", "target": "missing", "mask": 1}]
        migrated = ISO.migrate_dataset(concepts, edges, [])
        assert migrated["checks"]["dangling_edges"] == 1
        assert migrated["checks"]["referentially_intact"] is False


# ===========================================================================
# 8.  RUNTIME WIRING
# ===========================================================================

class TestRuntimeWiring:

    def test_report_golay_decoding_is_reachable_and_verifiable(self, sess):
        solution = sess.ask("report golay decoding")
        assert solution.ok
        assert solution.expected["cosets"] == "4096"
        assert solution.expected["is_steiner_5_8_24"] == "True"
        assert tct.verify_trace(tct.build_trace(solution)).verified

    def test_report_migration_is_reachable_and_verifiable(self, sess):
        solution = sess.ask("report migration")
        assert solution.ok
        assert solution.expected["shared_codewords"] == "8"
        assert solution.expected["is_automorphism"] == "False"
        assert solution.expected["distance_preserving"] == "True"
        assert tct.verify_trace(tct.build_trace(solution)).verified

    def test_the_subject_list_names_both(self, sess):
        solution = sess.ask("report")
        assert solution.ok is False
        assert "golay decoding" in solution.answer
        assert "migration" in solution.answer
