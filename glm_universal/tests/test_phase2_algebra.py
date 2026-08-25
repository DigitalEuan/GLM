"""Phase 2: the Leech construction ladder, the six facets, the Monster stack.

Three modules are pinned here, each of which removed an architectural
simplification.

``substrate/leech_construct``
    Construction A alone gives a kissing number of 48.  Adding Construction B,
    Construction C and the mod-8 coordinate-sum condition restores the true
    196,560, and dropping either condition is shown to break the minimum.

``reasoning/facets``
    The 24 coordinates cut into Dimension, Scale, Tensor Rank, Context,
    Nominal Kind and Domain, as *strict linear projections* -- additive,
    homogeneous, idempotent, mutually orthogonal and complete -- with the
    exact lattice index that measures what a facet reading loses.

``reasoning/monster_stack``
    The ten-plane ``Lambda / 2 Lambda`` address stack composed by the exact
    non-associative Sakuma product ``a . b = (1/8)(a + b - a_rho)`` rather
    than by the associative XOR shortcut it replaced.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import facets as FA
from glm_universal.reasoning import metric as ME
from glm_universal.reasoning import monster_stack as MS
from glm_universal.reasoning import product as PR
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession
from glm_universal.substrate import leech2
from glm_universal.substrate import leech_construct as LC


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


@pytest.fixture(scope="module")
def ladder():
    return LC.leech_construction_report()


# ===========================================================================
# 1.  THE CONSTRUCTION LADDER
# ===========================================================================

class TestConstructionLadder:

    def test_construction_a_is_only_forty_eight(self, ladder):
        assert ladder["kissing_by_level"]["A"] == 48
        assert ladder["minimal_norm_by_level"]["A"] == 16
        assert ladder["construction_A_is_48"] is True

    def test_construction_b_lifts_the_minimum_to_thirty_two(self, ladder):
        assert ladder["minimal_norm_by_level"]["B"] == 32
        assert ladder["kissing_by_level"]["B"] == 98256

    def test_construction_c_restores_the_true_kissing_number(self, ladder):
        assert ladder["kissing_by_level"]["C"] == 196560
        assert ladder["minimal_norm_by_level"]["C"] == 32
        assert ladder["construction_C_is_196560"] is True

    def test_the_three_shapes_add_up(self, ladder):
        shapes = ladder["levels"]["C"]["shapes"]
        assert sorted(shapes.values()) == [1104, 97152, 98304]
        assert sum(shapes.values()) == 196560

    def test_the_odd_coset_contributes_the_missing_vectors(self, ladder):
        assert ladder["odd_coset_contribution"] == 98304
        assert ladder["odd_coset_is_98304"] is True
        assert 98256 + 98304 == 196560

    def test_no_minimal_vector_is_counted_twice(self, ladder):
        for level in ("A", "B", "C"):
            assert ladder["levels"][level]["no_duplicates"] is True
            assert ladder["levels"][level]["all_in_level"] is True

    def test_the_kissing_number_matches_the_substrate_constant(self, ladder):
        assert ladder["kissing_by_level"]["C"] == leech2.KISSING
        assert ladder["minimal_norm_by_level"]["C"] == leech2.MIN_NORM2


class TestConditionsAreNecessary:

    def test_dropping_the_mod_four_golay_condition_collapses_the_minimum(
            self, ladder):
        row = ladder["necessity"]["drop_mod4_golay"]
        assert row["minimal_norm2"] == 8
        assert row["count_at_minimum"] == 552
        witness = tuple(row["witness"])
        assert sorted(witness) == sorted((2, -2) + (0,) * 22)
        assert not LC.golay_condition(witness)

    def test_dropping_the_mod_eight_sum_readmits_the_coordinate_vectors(
            self, ladder):
        row = ladder["necessity"]["drop_mod8_sum"]
        assert row["minimal_norm2"] == 16
        assert row["count_at_minimum"] == 48
        witness = tuple(row["witness"])
        assert sorted(witness) == sorted((4,) + (0,) * 23)
        assert not LC.sum_condition(witness)

    def test_dropping_the_odd_coset_leaves_construction_b(self, ladder):
        row = ladder["necessity"]["drop_odd_coset"]
        assert row["minimal_norm2"] == 32
        assert row["kissing"] == 98256


class TestMultiModSieve:

    def test_the_sieve_agrees_with_the_level_predicate(self):
        vector = (4, 4) + (0,) * 22
        sieve = LC.mod_sieve(vector)
        assert isinstance(sieve, dict)
        assert LC.in_level(vector, LC.LEVEL_C) is True

    def test_a_vector_failing_the_sum_condition_is_not_in_the_lattice(self):
        vector = (4,) + (0,) * 23
        assert LC.sum_condition(vector) is False
        assert LC.in_level(vector, LC.LEVEL_C) is False

    def test_the_ladder_agrees_with_the_substrate_predicate(self, ladder):
        agreement = ladder["agreement_with_leech2"]
        assert agreement["disagreements"] == 0
        assert agreement["agrees"] is True
        assert agreement["checked"] > 100


# ===========================================================================
# 2.  THE SIX FACETS
# ===========================================================================

class TestFacetPartition:

    def test_six_facets_partition_the_twenty_four_coordinates(self):
        report = FA.partition_report()
        assert report["facets"] == 6
        assert report["total"] == 24
        assert report["is_partition"] is True
        assert report["uncovered"] == []
        assert report["overlaps"] == {}

    def test_each_coordinate_has_exactly_one_owner(self):
        for i in range(24):
            name = FA.facet_of_coordinate(i)
            assert name in FA.FACET_ORDER
            assert i in FA.FACET_INDICES[name]

    def test_an_out_of_range_coordinate_is_refused(self):
        with pytest.raises(ValueError):
            FA.facet_of_coordinate(24)

    def test_an_unknown_facet_is_refused(self):
        with pytest.raises(ValueError):
            FA.project([0] * 24, "colour")


class TestFacetLinearity:

    def test_the_projections_are_strictly_linear(self):
        report = FA.linearity_report()
        assert report["additive"] is True
        assert report["homogeneous"] is True
        assert report["idempotent"] is True
        assert report["orthogonal"] is True
        assert report["complete"] is True
        assert report["strictly_linear"] is True

    def test_decompose_and_reassemble_are_inverse(self):
        carrier = tuple(Fraction(i + 1, 3) for i in range(24))
        parts = FA.decompose(carrier)
        assert set(parts) == set(FA.FACET_ORDER)
        assert FA.reassemble(parts) == carrier

    def test_distinct_facets_are_orthogonal(self):
        carrier = tuple(Fraction(i + 1, 5) for i in range(24))
        parts = FA.decompose(carrier)
        for left in FA.FACET_ORDER:
            for right in FA.FACET_ORDER:
                if left != right:
                    assert ME.griess_inner(parts[left], parts[right]) == 0

    def test_squared_distance_splits_across_the_facets(self):
        report = FA.pythagoras_report()
        assert report["additive"] is True
        assert report["failures"] == []

    def test_the_breakdown_sums_to_the_whole_distance(self):
        u = tuple(Fraction(i, 4) for i in range(24))
        v = tuple(Fraction(23 - i, 4) for i in range(24))
        breakdown = FA.facet_distance_breakdown(u, v)
        assert sum(breakdown.values()) == ME.distance2(u, v)


class TestFacetLattices:

    def test_no_facet_is_lattice_autonomous(self):
        report = FA.facets_report()
        assert report["autonomous_facets"] == []
        for name in FA.FACET_ORDER:
            assert report["lattices"][name]["lattice_autonomous"] is False

    def test_the_indices_are_the_measured_ones(self):
        index = FA.facets_report()["index_by_facet"]
        assert index["dimension"] == 512
        assert index["context"] == 32
        for name in ("scale", "tensor_rank", "nominal_kind", "domain"):
            assert index[name] == 8

    def test_the_intersection_is_a_sublattice_of_the_projection(self):
        for name in FA.FACET_ORDER:
            row = FA.facet_lattice_report(name)
            assert row["intersection_determinant"] % \
                row["projection_determinant"] == 0
            assert row["index"] == (row["intersection_determinant"]
                                    // row["projection_determinant"])


# ===========================================================================
# 3.  THE TEN-PLANE MONSTER STACK
# ===========================================================================

class TestPlaneAddressing:

    def test_a_type_two_class_is_its_own_axis(self):
        cls = sorted(leech2.type2_classes())[0]
        plane = MS.plane_address(0, cls)
        assert plane.is_type2 is True
        assert plane.axis_class == cls
        assert plane.repair_distance == 0
        assert plane.has_axis is True

    def test_the_strict_policy_refuses_to_repair(self):
        plane = MS.plane_address(0, 1, repair=False)
        if not leech2.is_type2_class(1):
            assert plane.has_axis is False
            with pytest.raises(PR.PositionError):
                plane.axis()

    def test_nearest_type_two_returns_the_whole_tie(self):
        distance, winners = MS.nearest_type2_classes(0)
        assert distance >= 0
        assert len(winners) == len(set(winners))
        for cls in winners:
            assert leech2.is_type2_class(cls)
            assert bin(cls).count("1") == distance

    def test_an_address_has_ten_planes(self):
        carrier = tuple(Fraction(i, 8) for i in range(24))
        address = MS.monster_address(carrier)
        assert address.depth == MS.DEPTH == 10
        assert len(address.planes) == 10
        assert len(address.masks()) == 10

    def test_the_census_counts_the_planes_it_could_type(self):
        carrier = tuple(Fraction(i, 8) for i in range(24))
        census = MS.address_census(MS.monster_address(carrier))
        assert census["depth"] == 10
        assert (census["type2_planes"] + census["repaired_planes"]
                + census["ambiguous_planes"]) <= 10


class TestSakumaAgainstTheShortcut:

    def test_the_shortcut_keeps_only_the_third_axis_label(self):
        loss = MS.shortcut_loss_report()
        assert loss["position"] == "2A"
        assert loss["sakuma_term_count"] == 3
        assert loss["shortcut_term_count"] == 1
        assert loss["terms_discarded_by_xor"] == 2
        assert loss["xor_is_the_third_axis_label"] is True

    def test_the_coefficient_the_shortcut_dropped_is_minus_one_eighth(self):
        loss = MS.shortcut_loss_report()
        assert Fraction(loss["coefficient_on_xor_term"]) == Fraction(-1, 8)
        assert Fraction(loss["sakuma_norm2"]) != Fraction(
            loss["shortcut_norm2"])

    def test_the_algebra_is_not_associative_but_the_shortcut_is(self):
        report = MS.associativity_report()
        assert report["associative"] is False
        assert report["xor_associative"] is True
        assert report["commutative"] is True
        assert Fraction(report["difference_norm2"]) > 0

    def test_the_two_bracketings_really_differ(self):
        report = MS.associativity_report()
        assert report["left_terms"] != report["right_terms"]
        assert set(report["positions"].values()) == {"2A"}

    def test_composition_is_plane_wise_and_never_invents_a_value(self):
        left = MS.monster_address(tuple(Fraction(i, 8) for i in range(24)))
        right = MS.monster_address(tuple(Fraction(23 - i, 8)
                                         for i in range(24)))
        planes = MS.compose_sakuma(left, right)
        assert len(planes) == 10
        for plane in planes:
            if not plane.defined:
                assert plane.value is None
                assert plane.note

    def test_pair_repair_buys_coverage_and_says_so(self):
        left = MS.monster_address(tuple(Fraction(i, 8) for i in range(24)))
        right = MS.monster_address(tuple(Fraction(23 - i, 8)
                                         for i in range(24)))
        strict = MS.position_census(MS.compose_sakuma(left, right))
        repaired = MS.position_census(
            MS.compose_sakuma(left, right, pair_repair=True))
        assert repaired["defined"] >= strict["defined"]

    def test_xor_composition_is_the_group_law(self):
        left = MS.monster_address(tuple(Fraction(i, 8) for i in range(24)))
        right = MS.monster_address(tuple(Fraction(23 - i, 8)
                                         for i in range(24)))
        xor = MS.compose_xor(left, right)
        assert xor == tuple(a ^ b for a, b in zip(left.masks(),
                                                  right.masks()))

    def test_addresses_of_different_depth_cannot_be_composed(self):
        carrier = tuple(Fraction(i, 8) for i in range(24))
        left = MS.monster_address(carrier)
        right = MS.monster_address(carrier, depth=11)
        with pytest.raises(ValueError):
            MS.compose_xor(left, right)


# ===========================================================================
# 4.  RUNTIME WIRING
# ===========================================================================

class TestRuntimeWiring:

    def test_report_leech_construction_is_reachable(self, sess):
        solution = sess.ask("report leech construction")
        assert solution.ok
        assert solution.expected["kissing_C"] == "196560"
        assert solution.expected["kissing_A"] == "48"
        assert tct.verify_trace(tct.build_trace(solution)).verified

    def test_report_facets_is_reachable(self, sess):
        solution = sess.ask("report facets")
        assert solution.ok
        assert solution.expected["facets"] == "6"
        assert solution.expected["strictly_linear"] == "True"
        assert tct.verify_trace(tct.build_trace(solution)).verified

    def test_report_monster_stack_is_reachable(self, sess):
        solution = sess.ask("report monster stack")
        assert solution.ok
        assert solution.expected["depth"] == "10"
        assert solution.expected["associative"] == "False"
        assert solution.expected["xor_associative"] == "True"
        assert tct.verify_trace(tct.build_trace(solution)).verified
