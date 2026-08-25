"""Unit tests for ``glm_universal.reasoning``.

Covers the five Step-3 success criteria:

* the Norton-Sakuma ``2A`` product, its involutions and the exact closure of
  the three-dimensional subalgebra under ``fractions.Fraction``;
* positivity, definiteness and the triangle inequality of the Griess metric,
  plus exact clustering;
* proportional analogies over physics dimensions, chemical group/period
  structure and the Leech lattice;
* the multi-plane audit of the 222 scalar and 71 tensor relations with
  31-facet discrepancy attribution;
* exactness and determinism: no ``float`` is constructed anywhere in the
  package, ``random`` is imported nowhere, and every result is reproducible
  within the run.

Run with::

    uv run pytest glm_universal/tests/test_reasoning.py -q
"""

from __future__ import annotations

import ast
import itertools
from fractions import Fraction
from pathlib import Path
from typing import List, Tuple

import pytest

from glm_universal.data_objects import elements as DE
from glm_universal.data_objects import physics as DP
from glm_universal.reasoning import analogy as A
from glm_universal.reasoning import metric as ME
from glm_universal.reasoning import product as PR
from glm_universal.reasoning import verifier as VE
from glm_universal.substrate import digit_stack as DS
from glm_universal.substrate import leech2 as L

REASONING_DIR = Path(__file__).resolve().parent.parent / "reasoning"


# ===========================================================================
# deterministic fixtures  (no RNG anywhere: an explicit LCG with a fixed seed)
# ===========================================================================

def _lcg(seed: int, count: int, lo: int, hi: int) -> List[int]:
    """A fixed, reproducible integer sequence in ``[lo, hi]``."""
    out: List[int] = []
    state = seed
    span = hi - lo + 1
    for _ in range(count):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        out.append(lo + state % span)
    return out


def rational_carriers() -> List[Tuple[Fraction, ...]]:
    """Diverse exact 24-vectors, integral and fractional."""
    out: List[Tuple[Fraction, ...]] = [
        tuple(Fraction(0) for _ in range(24)),
        tuple(Fraction(1) for _ in range(24)),
        tuple(Fraction(i) for i in range(24)),
        tuple(Fraction(i, 3) for i in range(-12, 12)),
        tuple(Fraction((-1) ** i * (i + 1), 8) for i in range(24)),
    ]
    for seed in (11, 29, 97):
        ints = _lcg(seed, 24, -40, 40)
        out.append(tuple(Fraction(v) for v in ints))
        out.append(tuple(Fraction(v, 6) for v in ints))
    return out


@pytest.fixture(scope="module")
def two_a_pairs() -> List[Tuple[int, int]]:
    """Six pairs of ``2A`` axes, drawn deterministically from the class table.

    Module-scoped: the first call builds the exhaustive 98,280-class type-2
    table, which is the expensive part of this file.
    """
    return PR.sample_two_a_pairs(6)


@pytest.fixture(scope="module")
def subalgebra(two_a_pairs) -> PR.TwoASubalgebra:
    return PR.two_a_subalgebra(*two_a_pairs[0])


# ===========================================================================
# 1.  NORTON-SAKUMA 2A PRODUCT ALGEBRA
# ===========================================================================

class TestSakumaProduct:

    def test_positions_are_named_by_the_pair_invariant(self, two_a_pairs):
        u, v = two_a_pairs[0]
        assert PR.pair_invariant_classes(u, u) == 4
        assert PR.position_name(u, u) == "1A"
        assert PR.pair_invariant_classes(u, v) == 2
        assert PR.position_name(u, v) == "2A"
        assert PR.is_two_a_pair(u, v)

    def test_axes_are_idempotent(self, two_a_pairs):
        u, _ = two_a_pairs[0]
        assert PR.axis_product(u, u) == PR.axis(u)
        assert PR.griess_form(PR.axis(u), PR.axis(u)) == PR.SELF_INNER == 1

    def test_sakuma_relation_is_the_one_eighth_formula(self, two_a_pairs):
        for u, v in two_a_pairs:
            w = PR.sakuma_third_axis(u, v)
            expected = (PR.axis(u) + PR.axis(v) - PR.axis(w)).scale(
                Fraction(1, 8))
            assert PR.axis_product(u, v) == expected
            # every coefficient is an exact eighth
            for coeff in PR.axis_product(u, v).coeffs.values():
                assert isinstance(coeff, Fraction)
                assert abs(coeff) == Fraction(1, 8)

    def test_third_axis_is_the_f2_sum_and_is_type_two(self, two_a_pairs):
        for u, v in two_a_pairs:
            w = PR.sakuma_third_axis(u, v)
            assert w == u ^ v
            assert L.is_type2_class(w)
            # and the triple is pairwise in 2A position
            assert PR.pair_invariant_classes(u, w) == 2
            assert PR.pair_invariant_classes(v, w) == 2

    def test_third_axis_refused_outside_the_2a_position(self, two_a_pairs):
        u, _ = two_a_pairs[0]
        lam, _neg = L.axis_of_class(u)
        far = None
        for cls in sorted(L.type2_classes()):
            mu, _ = L.axis_of_class(cls)
            if L.pair_invariant(lam, mu) == 0:
                far = cls
                break
        assert far is not None, "no orthogonal partner found"
        assert PR.position_name(u, far) == "2B"
        assert PR.axis_product(u, far).is_zero()
        with pytest.raises(PR.PositionError):
            PR.sakuma_third_axis(u, far)

    def test_griess_form_is_one_eighth_off_diagonal(self, subalgebra):
        gram = subalgebra.gram
        for i in range(3):
            for j in range(3):
                assert gram[i][j] == (Fraction(1) if i == j
                                      else Fraction(1, 8))

    def test_subalgebra_is_three_dimensional_and_closed(self, subalgebra):
        assert len(subalgebra.labels) == 3
        assert len(set(subalgebra.labels)) == 3
        assert subalgebra.closed
        for product_vec in subalgebra.table.values():
            assert product_vec.in_span(subalgebra.labels)

    def test_algebra_is_commutative_but_not_associative(self, subalgebra):
        assert subalgebra.commutative
        assert not subalgebra.associative
        a, b, _c = subalgebra.basis()
        left = PR.algebra_product(PR.algebra_product(a, a), b)
        right = PR.algebra_product(a, PR.algebra_product(a, b))
        assert left != right                 # the explicit witness
        assert left == PR.algebra_product(a, b)

    def test_product_is_bilinear(self, subalgebra):
        a, b, c = subalgebra.basis()
        lhs = PR.algebra_product(a.scale(Fraction(2, 3)) + b, c)
        rhs = (PR.algebra_product(a, c).scale(Fraction(2, 3))
               + PR.algebra_product(b, c))
        assert lhs == rhs

    def test_fusion_spectrum_is_exact_and_spans(self, subalgebra):
        for label in subalgebra.labels:
            spectrum = PR.fusion_spectrum(label, subalgebra)
            dims = {lam: len(basis) for lam, basis in spectrum.items()}
            assert dims[Fraction(1)] == 1
            assert dims[Fraction(0)] == 1
            assert dims[Fraction(1, 4)] == 1
            assert dims[Fraction(1, 32)] == 0
            assert sum(dims.values()) == 3

    def test_miyamoto_tau_is_trivial_on_the_2a_algebra(self, subalgebra):
        identity = tuple(tuple(Fraction(1 if i == j else 0) for j in range(3))
                         for i in range(3))
        for label in subalgebra.labels:
            tau = PR.miyamoto_tau(label, subalgebra)
            assert tau == identity
            assert PR.is_automorphism(tau, subalgebra)
            assert PR.preserves_form(tau, subalgebra)

    def test_miyamoto_sigma_swaps_the_other_two_axes(self, subalgebra):
        u, v, w = subalgebra.labels
        sigma = PR.miyamoto_sigma(u, subalgebra)
        assert PR.apply_map(sigma, PR.axis(u), subalgebra) == PR.axis(u)
        assert PR.apply_map(sigma, PR.axis(v), subalgebra) == PR.axis(w)
        assert PR.apply_map(sigma, PR.axis(w), subalgebra) == PR.axis(v)
        assert PR.is_automorphism(sigma, subalgebra)
        assert PR.preserves_form(sigma, subalgebra)

    def test_involutions_square_to_the_identity(self, subalgebra):
        a, b, c = subalgebra.basis()
        for label in subalgebra.labels:
            for build in (PR.miyamoto_tau, PR.miyamoto_sigma):
                m = build(label, subalgebra)
                for x in (a, b, c):
                    once = PR.apply_map(m, x, subalgebra)
                    assert PR.apply_map(m, once, subalgebra) == x

    def test_class_translation_is_an_involution_on_partners(self, two_a_pairs):
        u = two_a_pairs[0][0]
        tr = PR.class_translation(u)
        partners = [v for _u, v in two_a_pairs]
        assert tr.is_involution_on(partners)
        assert tr.preserves_type2_on_partners(partners)
        for v in partners:
            assert tr(v) == PR.sakuma_third_axis(u, v)

    def test_closure_report_recomputes_the_facts(self, two_a_pairs):
        report = PR.two_a_closure_report(two_a_pairs)
        assert report["pairs_checked"] == len(two_a_pairs)
        assert report["all_closed"]
        assert report["all_commutative"]
        assert report["none_associative"]
        assert report["all_gram_2A"]
        assert report["all_third_axes_type2"]
        assert report["all_pairwise_invariants_2"]

    def test_non_type2_labels_are_refused(self):
        with pytest.raises(ValueError):
            PR.axis(1)                       # class 1 is not of type 2

    def test_floats_are_refused_as_coefficients(self):
        with pytest.raises(TypeError):
            PR.AlgebraVector({0: 0.5})


# ===========================================================================
# 1b.  THE GRIESS TRILINEAR FORM
# ===========================================================================

class TestTrilinearForm:

    def test_trilinear_on_idempotent_axis_is_norm(self, two_a_pairs):
        """T(a, a, a) = <a . a, a> = <a, a> = 1"""
        u, _ = two_a_pairs[0]
        assert PR.trilinear_on_axes(u, u, u) == Fraction(1)
        assert PR.axis_trilinear(u, u, u) == Fraction(1)

    def test_trilinear_with_self_product_is_inner(self, two_a_pairs):
        """T(a, a, b) = <a . a, b> = <a, b> = 1/8 for a 2A pair."""
        u, v = two_a_pairs[0]
        assert PR.trilinear_on_axes(u, u, v) == PR.TWO_A_INNER
        assert PR.trilinear_on_axes(v, v, u) == PR.TWO_A_INNER

    def test_trilinear_is_zero_for_2b_pair(self, two_a_pairs):
        """T(a, b, c) = 0 when a, b are orthogonal (2B)."""
        u, _ = two_a_pairs[0]
        lam, _ = L.axis_of_class(u)
        for cls in sorted(L.type2_classes()):
            mu, _ = L.axis_of_class(cls)
            if L.pair_invariant(lam, mu) == 0:
                # found a 2B partner
                assert PR.trilinear_on_axes(u, cls, u) == Fraction(0)
                assert PR.trilinear_on_axes(cls, u, u) == Fraction(0)
                break

    def test_trilinear_agrees_with_product_then_form(self, two_a_pairs):
        """T(x, y, z) == <x . y, z> computed step by step."""
        for u, v in two_a_pairs[:3]:
            w = PR.sakuma_third_axis(u, v)
            for i in (u, v, w):
                for j in (u, v, w):
                    for k in (u, v, w):
                        direct = PR.trilinear_on_axes(i, j, k)
                        via_product = PR.griess_form(
                            PR.axis_product(i, j), PR.axis(k))
                        assert direct == via_product

    def test_trilinear_is_bilinear_in_first_two_args(self, subalgebra):
        """T(ax + by, z, w) = a*T(x,z,w) + b*T(y,z,w)."""
        a, b, c = subalgebra.basis()
        alpha, beta = Fraction(2, 3), Fraction(-1, 5)
        combo = a.scale(alpha) + b.scale(beta)
        lhs = PR.griess_trilinear(combo, b, c)
        rhs = (PR.griess_trilinear(a, b, c) * alpha
               + PR.griess_trilinear(b, b, c) * beta)
        assert lhs == rhs

    def test_trilinear_is_linear_in_third_arg(self, subalgebra):
        """T(x, y, az + bw) = a*T(x,y,z) + b*T(x,y,w)."""
        a, b, c = subalgebra.basis()
        alpha, beta = Fraction(3, 7), Fraction(-2, 7)
        combo = c.scale(alpha) + a.scale(beta)
        lhs = PR.griess_trilinear(a, b, combo)
        rhs = (PR.griess_trilinear(a, b, c) * alpha
               + PR.griess_trilinear(a, b, a) * beta)
        assert lhs == rhs

    def test_griess_trilinear_on_vectors(self, two_a_pairs):
        """The general form works on AlgebraVector inputs."""
        u, v = two_a_pairs[0]
        x, y, z = PR.axis(u), PR.axis(v), PR.axis(u)
        assert PR.griess_trilinear(x, y, z) == PR.trilinear_on_axes(u, v, u)

    def test_trilinear_report_recomputes_facts(self, two_a_pairs):
        report = PR.trilinear_report(two_a_pairs)
        assert report["pairs_checked"] == len(two_a_pairs)
        assert report["all_exact"]
        assert report["all_diagonal_ones"]
        assert report["all_self_product_correct"]

    def test_semantic_distance2_is_zero_iff_equal(self, two_a_pairs):
        """d(x, x) = 0 and d(x, y) > 0 for distinct axes."""
        u, v = two_a_pairs[0]
        x, y = PR.axis(u), PR.axis(v)
        assert PR.semantic_distance2(x, x) == 0
        assert PR.semantic_distance2(x, y) > 0
        assert PR.semantic_distance2(y, x) == PR.semantic_distance2(x, y)

    def test_semantic_distance2_is_symmetric(self, two_a_pairs):
        """d(x, y) == d(y, x) for all pairs."""
        for u, v in two_a_pairs[:4]:
            x, y = PR.axis(u), PR.axis(v)
            assert PR.semantic_distance2(x, y) == PR.semantic_distance2(y, x)

    def test_semantic_similarity_is_one_for_same_axis(self, two_a_pairs):
        """cos^2(a, a) = 1."""
        u, _ = two_a_pairs[0]
        x = PR.axis(u)
        assert PR.semantic_similarity(x, x) == Fraction(1)

    def test_semantic_similarity_is_bounded(self, two_a_pairs):
        """0 <= cos^2(x, y) <= 1."""
        for u, v in two_a_pairs[:4]:
            x, y = PR.axis(u), PR.axis(v)
            s = PR.semantic_similarity(x, y)
            assert Fraction(0) <= s <= Fraction(1)

    def test_semantic_similarity_refuses_zero(self):
        """Zero element has no direction."""
        with pytest.raises(ValueError):
            PR.semantic_similarity(PR.zero(), PR.axis(0))

    def test_coherence_of_product_captures_structure(self, two_a_pairs):
        """Product coherence is a dict with the expected keys."""
        u, v = two_a_pairs[0]
        coh = PR.coherence_of_product(PR.axis(u), PR.axis(v))
        assert isinstance(coh["factor_x_norm2"], Fraction)
        assert isinstance(coh["factor_y_norm2"], Fraction)
        assert isinstance(coh["product_norm2"], Fraction)
        assert isinstance(coh["self_coherence_x"], Fraction)
        assert isinstance(coh["self_coherence_y"], Fraction)
        # the product of two distinct 2A axes is not zero
        assert not coh["product_is_zero"]

    def test_coherence_self_product_matches_form(self, two_a_pairs):
        """<a . a, a> = <a, a> = 1 for any axis."""
        u, _ = two_a_pairs[0]
        coh = PR.coherence_of_product(PR.axis(u), PR.axis(u))
        assert coh["self_coherence_x"] == Fraction(1)
        assert coh["product_norm2"] == Fraction(1)

    def test_all_values_are_fractions(self, two_a_pairs):
        """No float is ever constructed by the trilinear form."""
        for u, v in two_a_pairs[:3]:
            w = PR.sakuma_third_axis(u, v)
            for i in (u, v, w):
                for j in (u, v, w):
                    for k in (u, v, w):
                        val = PR.trilinear_on_axes(i, j, k)
                        assert isinstance(val, Fraction)


# ===========================================================================
# 2.  THE GRIESS METRIC
# ===========================================================================

class TestGriessMetric:

    def test_form_is_positive_definite_two_ways(self):
        report = ME.positive_definite_report()
        assert report["positive_definite"]
        assert report["standard_basis_diagonal_all_positive"]
        assert report["leech_gram_all_leading_minors_positive"]
        assert report["leech_gram_symmetric"]
        assert report["leech_lattice_is_unimodular"]
        assert report["leech_gram_determinant"] == "1"

    def test_norm_vanishes_only_at_zero(self):
        assert ME.griess_norm2([Fraction(0)] * 24) == 0
        for v in rational_carriers():
            if any(x != 0 for x in v):
                assert ME.griess_norm2(v) > 0

    def test_distance_is_symmetric_and_identifies_indiscernibles(self):
        carriers = rational_carriers()
        for u, v in itertools.combinations(carriers, 2):
            assert ME.distance2(u, v) == ME.distance2(v, u)
            assert ME.distance2(u, v) > 0
        for u in carriers:
            assert ME.distance2(u, u) == 0

    def test_triangle_inequality_holds_on_every_triple(self):
        carriers = rational_carriers()
        for u, v, w in itertools.combinations(carriers, 3):
            assert ME.triangle_inequality_holds(u, v, w)
            assert ME.triangle_inequality_holds(v, u, w)
            assert ME.triangle_inequality_holds(u, w, v)

    def test_triangle_inequality_is_tight_on_a_collinear_triple(self):
        a = [Fraction(0)] * 24
        b = [Fraction(4)] + [Fraction(0)] * 23
        mid = [Fraction(2)] + [Fraction(0)] * 23
        assert ME.triangle_inequality_holds(a, b, mid)
        # equality case: d(a,b)^2 = 2, d(a,m)^2 = d(m,b)^2 = 1/2
        assert ME.distance2(a, b) == Fraction(2)
        assert ME.distance2(a, mid) == Fraction(1, 2)
        s = ME.distance2(a, b) - ME.distance2(a, mid) - ME.distance2(mid, b)
        assert s * s == 4 * ME.distance2(a, mid) * ME.distance2(mid, b)

    def test_everything_is_a_fraction(self):
        u, v = rational_carriers()[3], rational_carriers()[4]
        for value in (ME.griess_inner(u, v), ME.griess_norm2(u),
                      ME.distance2(u, v), ME.signed_cosine_squared(u, v)):
            assert isinstance(value, Fraction)

    def test_floats_are_refused(self):
        with pytest.raises(TypeError):
            ME.griess_inner([0.5] * 24, [1] * 24)

    def test_exact_distance_is_none_when_irrational(self):
        a = [Fraction(0)] * 24
        b = [Fraction(2)] + [Fraction(0)] * 23        # d^2 = 1/2
        assert ME.exact_distance(a, b) is None
        c = [Fraction(4)] + [Fraction(0)] * 23        # d^2 = 2
        assert ME.exact_distance(a, c) is None
        d = [Fraction(0)] * 24
        d[0] = Fraction(2)
        d[1] = Fraction(2)                            # d^2 = 1
        assert ME.exact_distance(a, d) == Fraction(1)

    def test_cosine_comparison_matches_the_geometry(self):
        e0 = [Fraction(1)] + [Fraction(0)] * 23
        e1 = [Fraction(0), Fraction(1)] + [Fraction(0)] * 22
        diag = [Fraction(1), Fraction(1)] + [Fraction(0)] * 22
        assert ME.signed_cosine_squared(e0, e0) == 1
        assert ME.signed_cosine_squared(e0, e1) == 0
        assert ME.signed_cosine_squared(e0, [-x for x in e0]) == -1
        assert ME.signed_cosine_squared(e0, diag) == Fraction(1, 2)
        # e0 is closer in angle to diag than to e1
        assert ME.compare_cosines(e0, diag, e0, e1) == 1

    def test_single_linkage_is_exact_and_deterministic(self):
        labels = ["p0", "p1", "p2", "p3"]
        vectors = [
            [Fraction(0)] * 24,
            [Fraction(1)] + [Fraction(0)] * 23,
            [Fraction(10)] + [Fraction(0)] * 23,
            [Fraction(11)] + [Fraction(0)] * 23,
        ]
        tree = ME.single_linkage(vectors, labels)
        assert [m.height for m in tree.merges] == [
            Fraction(1, 8), Fraction(1, 8), Fraction(81, 8)]
        for merge in tree.merges:
            assert isinstance(merge.height, Fraction)
        assert tree.clusters_of_size(2) == [["p0", "p1"], ["p2", "p3"]]
        assert ME.single_linkage(vectors, labels) == tree      # deterministic

    def test_complete_linkage_differs_where_it_should(self):
        labels = ["a", "b", "c"]
        vectors = [
            [Fraction(0)] * 24,
            [Fraction(2)] + [Fraction(0)] * 23,
            [Fraction(6)] + [Fraction(0)] * 23,
        ]
        single = ME.single_linkage(vectors, labels)
        complete = ME.complete_linkage(vectors, labels)
        # first merge is the same pair; the second height is not
        assert single.merges[0].height == complete.merges[0].height
        assert single.merges[1].height == Fraction(2)          # d^2(b, c)
        assert complete.merges[1].height == Fraction(9, 2)     # d^2(a, c)

    def test_clustering_recovers_planted_groups(self):
        labels, vectors = [], []
        for group, base in enumerate((0, 100)):
            for k in range(3):
                v = [Fraction(0)] * 24
                v[0] = Fraction(base + k)
                labels.append(f"g{group}_{k}")
                vectors.append(v)
        tree = ME.single_linkage(vectors, labels)
        clusters = tree.clusters_of_size(2)
        assert sorted(clusters) == [["g0_0", "g0_1", "g0_2"],
                                    ["g1_0", "g1_1", "g1_2"]]


# ===========================================================================
# 3.  PROPORTIONAL ANALOGY
# ===========================================================================

class TestAnalogy:

    def test_target_is_the_exact_displacement(self):
        a = [Fraction(1)] * 24
        b = [Fraction(3)] * 24
        c = [Fraction(i, 2) for i in range(24)]
        target = A.analogy_target(a, b, c)
        assert all(t == x + 2 for t, x in zip(target, c))
        assert all(isinstance(t, Fraction) for t in target)

    def test_physics_dimension_analogy(self):
        # velocity : acceleration :: momentum : force   (one more T^-1)
        result = A.physics_analogy("velocity", "acceleration", "momentum")
        assert result.exact_hit
        assert "force" in result.tied
        # the dimension L M T^-2 is shared by several register names, so the
        # answer is a tie class rather than a single concept
        assert not result.unique
        forces = {DP.quantity_by_name(n).dimension_string("EXT10")
                  for n in result.tied}
        assert forces == {"L M T^-2"}

    def test_physics_analogy_with_a_unique_answer(self):
        # length : area :: area : volume  -- one more factor of length
        result = A.physics_analogy("length", "area", "area")
        assert result.exact_hit
        assert "volume" in result.tied

    def test_physics_analogy_target_is_reached_exactly(self):
        result = A.physics_analogy("energy", "power", "momentum")
        assert result.distance2 == 0
        assert all(DP.quantity_by_name(n).dimension_string("EXT10")
                   == "L M T^-2" for n in result.tied)

    def test_element_group_period_analogy(self):
        # Li : Na :: Be : Mg  -- same group, next period
        result = A.element_analogy("Li", "Na", "Be")
        assert result.answer == "Mg"
        assert result.exact_hit and result.unique
        assert result.margin2 > 0

    def test_element_analogy_second_case(self):
        # He : Ne :: Ne : Ar  -- the noble-gas ladder
        result = A.element_analogy("He", "Ne", "Ne")
        assert result.answer == "Ar"
        assert result.unique

    def test_subspace_restriction_changes_the_metric(self):
        objects = DE.element_objects()
        idx = {o.name: o for o in objects}
        full = A.solve_analogy_objects(idx["Li"], idx["Na"], idx["Be"],
                                       objects, subspace=None)
        positional = A.solve_analogy_objects(idx["Li"], idx["Na"], idx["Be"],
                                             objects,
                                             subspace="chemistry.position")
        assert positional.answer == "Mg"
        # the full-carrier metric is dominated by measured attributes, so it
        # need not agree; what must hold is that both are exact and
        # deterministic
        assert isinstance(full.distance2, Fraction)
        assert full == A.solve_analogy_objects(idx["Li"], idx["Na"],
                                               idx["Be"], objects,
                                               subspace=None)

    def test_nearest_lattice_point_fixes_lattice_points(self):
        for point in itertools.islice(L.minimal_vectors(), 5):
            result = A.nearest_lattice_point([Fraction(x) for x in point])
            assert result.exact_hit
            assert result.point == tuple(point)
            assert result.distance2 == 0
            assert result.norm2 == L.MIN_NORM2
            assert result.is_2a_axis

    def test_nearest_lattice_point_decodes_a_perturbed_point(self):
        base = next(iter(L.minimal_vectors()))
        perturbed = [Fraction(x) for x in base]
        perturbed[0] += Fraction(1, 2)
        result = A.nearest_lattice_point(perturbed)
        assert result.in_leech
        assert L.in_leech(list(result.point))
        assert result.distance2 == Fraction(1, 32)     # (1/2)^2 / 8
        assert result.point == tuple(base)

    def test_nearest_lattice_point_is_at_least_as_good_as_any_witness(self):
        """The decoder is claimed optimal; check it against explicit rivals."""
        query = [Fraction(1, 3)] * 24
        result = A.nearest_lattice_point(query)
        witnesses = [list(v) for v in itertools.islice(L.minimal_vectors(), 40)]
        witnesses.append([0] * 24)
        for w in witnesses:
            assert result.distance2 <= ME.distance2(
                query, [Fraction(x) for x in w])

    def test_lattice_analogy(self):
        vectors = list(itertools.islice(L.minimal_vectors(), 3))
        a, b, c = ([Fraction(x) for x in v] for v in vectors)
        result = A.lattice_analogy(a, b, c)
        assert result.in_leech
        assert L.in_leech(list(result.point))
        # the exact target is c + b - a, which is itself a lattice point
        target = A.analogy_target(a, b, c)
        assert L.in_leech([int(x) for x in target])
        assert result.exact_hit
        assert result.point == tuple(int(x) for x in target)

    def test_nearest_golay_codeword(self):
        from glm_universal.substrate import mog as M
        word = M.GOLAY_MASKS[7]
        assert A.nearest_golay_codeword(word) == (word, 0, 1)
        flipped = word ^ 0b111                        # three errors
        cw, dist, count = A.nearest_golay_codeword(flipped)
        assert dist == 3 and count == 1 and cw == word

    def test_analogy_is_deterministic(self):
        first = A.physics_analogy("velocity", "acceleration", "momentum")
        second = A.physics_analogy("velocity", "acceleration", "momentum")
        assert first.ranked == second.ranked


# ===========================================================================
# 4.  MULTI-PLANE EQUATION VERIFICATION AND FACET ATTRIBUTION
# ===========================================================================

class TestVerifier:

    def test_snapshot_matches_the_implemented_operator_set(self):
        raw = VE.load_relations()
        assert set(raw["operators"]) == set(VE.OPERATORS)
        assert raw["scalar_count"] == 222
        assert raw["tensor_count"] == 71

    def test_tables_have_the_expected_size(self):
        assert len(VE.relation_table("scalar")) == 222
        assert len(VE.relation_table("tensor")) == 71

    def test_parser_reproduces_known_dimensions(self):
        energy = VE.parse("mass * speed^2")
        assert DP.dimension_string(energy.exps, "EXT10") == "L^2 M T^-2"
        assert energy.rank == 0
        planck = VE.parse("(planck_constant * gravitational_constant "
                          "/ speed^3)^(1/2)")
        assert DP.dimension_string(planck.exps, "EXT10") == "L"

    def test_parser_refuses_non_powers_of_ten(self):
        with pytest.raises(VE.RelationError):
            VE.parse("3 * length")
        with pytest.raises(VE.RelationError):
            VE.parse("not_a_concept * length")

    def test_operator_algebra_distinguishes_rank(self):
        tensor_product = VE.parse("force * position")
        contraction = VE.parse("dot(force, position)")
        assert tensor_product.rank == 2
        assert contraction.rank == 0
        assert tensor_product.exps == contraction.exps

    def test_moment_consumes_a_radian_and_cross_does_not(self):
        torque = VE.parse("moment(position, force)")
        poynting = VE.parse("cross(electric_field, magnetic_field_h)")
        assert torque.exponent("A") == -1
        assert poynting.exponent("A") == 0

    def test_all_222_scalar_relations_hold_under_scalar_semantics(self):
        result = VE.verify_all("scalar", "scalar")
        assert result["checked"] == 222
        assert result["parse_errors"] == 0
        assert result["failed"] == 0, result["failures"][:3]
        assert result["all_hold"]

    def test_all_71_tensor_relations_hold_under_full_semantics(self):
        result = VE.verify_all("tensor", "full")
        assert result["checked"] == 71
        assert result["parse_errors"] == 0
        assert result["failed"] == 0, result["failures"][:3]

    def test_full_semantics_is_strictly_harder(self):
        loose = VE.verify_all("scalar", "scalar")
        strict = VE.verify_all("scalar", "full")
        assert strict["held"] < loose["held"]
        assert strict["held"] == 186 and strict["failed"] == 36

    def test_a_true_equation_blames_nothing(self):
        verdict = VE.verify_expression_pair("energy", "dot(force, position)",
                                            "full")
        assert verdict.holds
        assert verdict.failing_planes == ()
        assert verdict.blamed_facets == ()
        assert verdict.first_failing_plane is None

    def test_a_rank_error_is_attributed_to_named_facets(self):
        verdict = VE.verify_expression_pair("energy", "force * position",
                                            "full")
        assert not verdict.holds
        assert verdict.lhs_rank == 0 and verdict.rhs_rank == 2
        assert "rank" in verdict.difference_coordinates
        assert verdict.blamed_facets
        for facet in verdict.blamed_facets:
            assert facet in DS.FACETS
        # the rank coordinate is coordinate 18; every facet containing it must
        # be blamed, and no facet disjoint from the difference may be
        rank_index = VE.RELATION_LAYOUT.index("rank")
        must = {name for name, mask in DS.FACETS.items()
                if (mask >> rank_index) & 1}
        assert must <= set(verdict.blamed_facets)

    def test_a_dimension_error_is_attributed_to_named_facets(self):
        verdict = VE.verify_expression_pair("energy", "mass * speed", "scalar")
        assert not verdict.holds
        assert verdict.blamed_facets
        assert verdict.first_failing_plane is not None
        speed_index = VE.RELATION_LAYOUT.index("ext10.T")
        must = {name for name, mask in DS.FACETS.items()
                if (mask >> speed_index) & 1}
        assert must <= set(verdict.blamed_facets)

    def test_facet_census_covers_all_31_facets(self):
        census = VE.facet_attribution_census("scalar", "full")
        assert census["n_facets"] == 31
        assert len(census["facet_counts"]) == 31
        assert census["failed"] == 36
        assert 0 < census["facets_blamed"] <= 31
        assert sum(census["failing_plane_counts"].values()) > 0

    def test_scalar_semantics_ignores_tensor_character(self):
        loose = VE.verify_expression_pair("energy", "force * position",
                                          "scalar")
        strict = VE.verify_expression_pair("energy", "force * position",
                                           "full")
        assert loose.holds
        assert not strict.holds

    def test_carriers_round_trip_through_the_digit_stack(self):
        for lhs, rhs in list(VE.relation_table("tensor"))[:12]:
            sense = VE.parse(rhs)
            carrier = VE.sense_carrier(sense, "full")
            stack = DS.class_stack_fitted(carrier)
            assert tuple(DS.class_stack_rebuild(stack)) == carrier

    def test_verifier_report_is_reproducible_within_the_run(self):
        first = VE.verifier_report()
        second = VE.verifier_report()
        assert first == second


# ===========================================================================
# 5.  PACKAGE-WIDE EXACTNESS AND DETERMINISM
# ===========================================================================

class TestExactness:

    def test_no_module_imports_random(self):
        for path in sorted(REASONING_DIR.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name.split(".")[0] != "random", path.name
                elif isinstance(node, ast.ImportFrom):
                    assert (node.module or "").split(".")[0] != "random", \
                        path.name

    def test_no_float_literals_and_no_float_calls(self):
        """No source line constructs a float, in any reasoning module.

        There is no longer an exception: NRCI shells 2 and 4 take their
        square root rationally, at the declared resolution of
        ``coherence.rational_sqrt``.
        """
        offenders = []
        for path in sorted(REASONING_DIR.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(
                        node.value, float):
                    offenders.append(f"{path.name}:{node.lineno} float literal")
                if (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name)
                        and node.func.id == "float"):
                    offenders.append(f"{path.name}:{node.lineno} float() call")
        assert not offenders, offenders

    def test_only_the_standard_library_is_imported(self):
        allowed_third_party: set = set()
        stdlib_roots = {"ast", "dataclasses", "fractions", "functools",
                        "itertools", "json", "math", "pathlib", "re",
                        "typing", "__future__"}
        for path in sorted(REASONING_DIR.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [(node.module or "").split(".")[0]]
                for name in names:
                    assert name in stdlib_roots | allowed_third_party, \
                        f"{path.name} imports {name}"

    def test_repeated_evaluation_is_identical(self):
        u = [Fraction(i, 7) for i in range(24)]
        v = [Fraction(23 - i, 5) for i in range(24)]
        assert ME.distance2(u, v) == ME.distance2(u, v)
        assert ME.positive_definite_report() == ME.positive_definite_report()
        assert (VE.facet_attribution_census("tensor", "full")
                == VE.facet_attribution_census("tensor", "full"))


# ===========================================================================
# 6.  DIMENSION PROJECTION LAYERS
# ===========================================================================

class TestDimensionLayers:

    def test_five_layers_exist(self):
        from glm_universal.reasoning import dimension_layers as DL
        assert len(DL.LAYERS) == 5
        names = [l.name for l in DL.LAYERS]
        assert names == ["substrate", "integer", "rational", "griess", "universal"]

    def test_layers_are_ordered_by_dimension(self):
        from glm_universal.reasoning import dimension_layers as DL
        # substrate < integer < rational < griess < universal (-1 = unbounded)
        dims = [l.dimension for l in DL.LAYERS]
        assert dims == [24, 7, 10, 196884, -1]

    def test_substrate_layer_perceives_binary(self):
        from glm_universal.reasoning import dimension_layers as DL
        carrier = [Fraction(i % 2) for i in range(24)]
        view = DL.LAYER_SUBSTRATE.perceive(carrier)
        assert view["layer"] == "substrate"
        assert "bits" in view
        assert "hamming_weight" in view
        assert "nrci" in view
        assert isinstance(view["nrci"], Fraction)

    def test_substrate_measure_is_hamming_distance(self):
        from glm_universal.reasoning import dimension_layers as DL
        a = [Fraction(0)] * 24
        b = [Fraction(1)] * 24
        va = DL.LAYER_SUBSTRATE.perceive(a)
        vb = DL.LAYER_SUBSTRATE.perceive(b)
        d = DL.LAYER_SUBSTRATE.measure(va, vb)
        assert d == Fraction(24)

    def test_integer_layer_perceives_dimensions(self):
        from glm_universal.reasoning import dimension_layers as DL
        carrier = [Fraction(i) for i in range(24)]
        view = DL.LAYER_INTEGER.perceive(carrier)
        assert view["layer"] == "integer"
        assert "exponents_SI7" in view
        assert len(view["exponents_SI7"]) == 7

    def test_rational_layer_perceives_lattice(self):
        from glm_universal.reasoning import dimension_layers as DL
        carrier = [Fraction(0)] * 24
        view = DL.LAYER_RATIONAL.perceive(carrier)
        assert view["layer"] == "rational"
        assert "lattice_point" in view
        assert "leech_class" in view

    def test_griess_layer_perceives_algebra(self):
        from glm_universal.reasoning import dimension_layers as DL
        carrier = [Fraction(0)] * 24
        view = DL.LAYER_GRIESS.perceive(carrier)
        assert view["layer"] == "griess"
        assert "is_2a_axis" in view

    def test_universal_layer_perceives_all(self):
        from glm_universal.reasoning import dimension_layers as DL
        carrier = [Fraction(0)] * 24
        view = DL.LAYER_UNIVERSAL.perceive(carrier)
        assert view["layer"] == "universal"
        assert view["all_layers"] is True
        assert "substrate" in view
        assert "integer" in view

    def test_griess_can_multiply_but_lower_cannot(self):
        from glm_universal.reasoning import dimension_layers as DL
        assert not DL.LAYER_SUBSTRATE.can_multiply
        assert not DL.LAYER_INTEGER.can_multiply
        assert not DL.LAYER_RATIONAL.can_multiply
        assert DL.LAYER_GRIESS.can_multiply
        assert DL.LAYER_UNIVERSAL.can_multiply

    def test_escalate_visits_layers(self):
        from glm_universal.reasoning import dimension_layers as DL
        a = [Fraction(0)] * 24
        b = [Fraction(1)] + [Fraction(0)] * 23
        result = DL.escalate(a, b)
        assert result["layer"].name == "universal"
        assert len(result["all_views"]) == 5
        # each view has the layer name
        for name, va, vb, d in result["all_views"]:
            assert isinstance(d, Fraction)

    def test_escalate_from_substrate(self):
        from glm_universal.reasoning import dimension_layers as DL
        a = [Fraction(0)] * 24
        b = [Fraction(1)] * 24
        result = DL.escalate(a, b, start=0)
        assert len(result["all_views"]) == 5

    def test_escalate_from_griess(self):
        from glm_universal.reasoning import dimension_layers as DL
        a = [Fraction(0)] * 24
        b = [Fraction(1)] * 24
        result = DL.escalate(a, b, start=3)
        assert len(result["all_views"]) == 2  # griess + universal

    def test_projection_report_runs(self):
        from glm_universal.reasoning import dimension_layers as DL
        report = DL.projection_report()
        assert report["total_layers"] == 5
        assert report["final_layer"] == "universal"
        assert len(report["layers"]) == 5
        for lr in report["layers"]:
            assert "name" in lr
            assert "distance" in lr
            assert isinstance(lr["distance"], str)  # Fraction as string

    def test_projection_report_with_custom_carriers(self):
        from glm_universal.reasoning import dimension_layers as DL
        a = [Fraction(0)] * 24
        b = [Fraction(i, 3) for i in range(24)]
        report = DL.projection_report(a, b)
        assert report["total_layers"] == 5
        # substrate distance should be 24 (all bits differ)
        substrate = report["layers"][0]
        assert substrate["name"] == "substrate"

    def test_layer_lookup_by_name(self):
        from glm_universal.reasoning import dimension_layers as DL
        assert DL.LAYER_BY_NAME["substrate"] is DL.LAYER_SUBSTRATE
        assert DL.LAYER_BY_NAME["universal"] is DL.LAYER_UNIVERSAL

    def test_no_floats_in_dimension_layers(self):
        """No float is constructed by any layer's perceive or measure."""
        from glm_universal.reasoning import dimension_layers as DL
        import ast as ast_mod
        path = REASONING_DIR / "dimension_layers.py"
        tree = ast_mod.parse(path.read_text(encoding="utf-8"))
        for node in ast_mod.walk(tree):
            if isinstance(node, ast_mod.Constant) and isinstance(
                    node.value, float):
                pytest.fail(
                    f"dimension_layers.py:{node.lineno} float literal")
            if (isinstance(node, ast_mod.Call)
                    and isinstance(node.func, ast_mod.Name)
                    and node.func.id == "float"):
                pytest.fail(
                    f"dimension_layers.py:{node.lineno} float() call")
