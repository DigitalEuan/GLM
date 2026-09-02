"""Unit tests for ``glm_universal.substrate``.

Covers the four Step-1 success criteria:

* ``2A`` (type-2) axis detection against the exhaustive 98,280-class table;
* MOG trio partitioning, sextet geometry and bijective 4x6 / 3x8 reshaping;
* lossless 10-plane reconstruction ``class_stack_rebuild(class_stack(v)) == v``
  across diverse integer and rational carriers;
* exactness and determinism: no float anywhere, no RNG anywhere, identical
  results on repeated evaluation.

Run with::

    uv run pytest glm_universal/tests/test_substrate.py -q
"""

from __future__ import annotations

import ast
import itertools
from fractions import Fraction
from pathlib import Path
from typing import List, Tuple

import pytest

from glm_universal.substrate import digit_stack as DS
from glm_universal.substrate import leech2 as L
from glm_universal.substrate import linalg as LA
from glm_universal.substrate import mog as M

SUBSTRATE_DIR = Path(__file__).resolve().parent.parent / "substrate"


# ===========================================================================
# deterministic carrier fixtures  (no RNG: an explicit LCG with a fixed seed)
# ===========================================================================

def _lcg(seed: int, count: int, lo: int, hi: int) -> List[int]:
    """A fixed, reproducible integer sequence in ``[lo, hi]``.

    Deliberately not ``random``: the package forbids importing it, and a
    hand-rolled LCG makes the test inputs a literal function of the seed.
    """
    out: List[int] = []
    state = seed
    span = hi - lo + 1
    for _ in range(count):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        out.append(lo + state % span)
    return out


def integer_carriers() -> List[Tuple[int, ...]]:
    """Diverse integral 24-vectors, including boundary cases."""
    carriers: List[Tuple[int, ...]] = [
        tuple([0] * 24),
        tuple([1] * 24),
        tuple([-1] * 24),
        tuple(range(24)),
        tuple(-i for i in range(24)),
        tuple([511] * 24),                     # upper edge of the default range
        tuple([-512] * 24),                    # lower edge of the default range
        tuple(511 if i % 2 else -512 for i in range(24)),
    ]
    for seed in (1, 7, 99, 20260820):
        carriers.append(tuple(_lcg(seed, 24, -500, 500)))
    return carriers


def rational_carriers() -> List[Tuple[Fraction, ...]]:
    """Rational 24-vectors with mixed denominators, inside the 10-plane range.

    "Inside the range" means the coordinates cleared by their least common
    denominator stay within ``[-512, 511]``, so the default ``(offset 512,
    depth 10)`` pair is admissible.  Carriers that do not are exercised
    separately by :func:`wide_rational_carriers`.
    """
    carriers: List[Tuple[Fraction, ...]] = [
        tuple(Fraction(1, 2) for _ in range(24)),
        tuple(Fraction(-3, 4) for _ in range(24)),
        tuple(Fraction(i, 3) for i in range(-12, 12)),
        tuple(Fraction((-1) ** i * (i + 1), (i % 5) + 1) for i in range(24)),
        tuple(Fraction(7, 8) if i % 3 == 0 else Fraction(-5, 6)
              for i in range(24)),
    ]
    nums = _lcg(2026, 24, -40, 40)
    carriers.append(tuple(Fraction(n, 8) for n in nums))
    carriers.append(tuple(Fraction(n, 12) for n in _lcg(818, 24, -42, 42)))
    return carriers


def wide_rational_carriers() -> List[Tuple[Fraction, ...]]:
    """Rational carriers whose cleared coordinates overflow the 10-plane range.

    These are the cases that make Proposition D1 a measurement rather than a
    convention: the identity still holds, but only at a derived depth.
    """
    nums = _lcg(2026, 24, -40, 40)
    dens = _lcg(818, 24, 1, 12)
    return [
        tuple(Fraction(n, d) for n, d in zip(nums, dens)),
        tuple(Fraction(i + 1, i + 2) for i in range(24)),
        tuple(Fraction(10 ** 6 + i, 7) for i in range(24)),
    ]


def leech_points() -> List[Tuple[int, ...]]:
    """A spread of genuine points of ``Lambda`` in the integer model."""
    pts: List[Tuple[int, ...]] = [tuple([0] * 24)]
    pts.extend(list(itertools.islice(L.minimal_vectors(), 0, 40)))
    # a few deeper points: sums and doublings stay inside Lambda
    a, b = pts[1], pts[7]
    pts.append(tuple(x + y for x, y in zip(a, b)))
    pts.append(tuple(2 * x for x in a))
    pts.append(tuple(x - 3 * y for x, y in zip(a, b)))
    pts.extend(tuple(r) for r in L.LEECH_BASIS[:6])
    return pts


def in_range_leech_points() -> List[Tuple[int, ...]]:
    """Lattice points whose Euclidean coordinates fit the default 10 planes."""
    return [p for p in leech_points() if max(abs(c) for c in p) <= 511]


# ===========================================================================
# 1.  EXACTNESS AND DETERMINISM
# ===========================================================================

class TestPurity:
    """The package is standard library, exact and deterministic."""

    def test_no_random_import_anywhere(self) -> None:
        for path in sorted(SUBSTRATE_DIR.glob("*.py")):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name.split(".")[0] != "random", path.name
                elif isinstance(node, ast.ImportFrom):
                    root = (node.module or "").split(".")[0]
                    assert root != "random", path.name

    def test_only_standard_library_imports(self) -> None:
        # ``pathlib``, ``base64`` and ``array`` are here for one reason: the
        # 98,280-class type-2 table is stored beside the digest of the sources
        # it was derived from, and reading it back needs a path and an exact
        # byte packing.  All three are deterministic and exact -- no
        # randomness, no hashing, no floating point -- so the discipline this
        # test enforces is untouched.
        allowed = {"", "__future__", "fractions", "typing", "dataclasses",
                   "math", "itertools", "collections", "enum", "functools",
                   "pathlib", "base64", "array"}
        for path in sorted(SUBSTRATE_DIR.glob("*.py")):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name.split(".")[0] in allowed, \
                            f"{path.name}: {alias.name}"
                elif isinstance(node, ast.ImportFrom):
                    if node.level:          # relative, in-package
                        continue
                    root = (node.module or "").split(".")[0]
                    assert root in allowed, f"{path.name}: {node.module}"

    def test_floats_are_rejected_by_the_stack(self) -> None:
        v = [0.5] + [0] * 23
        with pytest.raises(TypeError):
            DS.class_stack(v)

    def test_rational_inner_product_is_exact(self) -> None:
        v = next(iter(L.minimal_vectors()))
        assert isinstance(L.rational_norm2(v), Fraction)
        assert L.rational_norm2(v) == Fraction(32, 8) == 4
        assert L.rational_inner(v, v) == Fraction(L.norm2(v), 8)

    def test_reports_are_deterministic(self) -> None:
        assert M.mog_report(full=False) == M.mog_report(full=False)
        assert L.witt_decomposition() == L.witt_decomposition()
        assert L.type_census() == L.type_census()


# ===========================================================================
# 2.  EXACT LINEAR ALGEBRA
# ===========================================================================

class TestLinalg:

    def test_popcount_and_masks(self) -> None:
        assert LA.popcount(0) == 0
        assert LA.popcount(0xFFFFFF) == 24
        assert LA.bits_of(0b1011) == [0, 1, 3]
        assert LA.mask_of([0, 1, 3]) == 0b1011

    def test_hnf_spans_the_same_lattice(self) -> None:
        rows = [[2, 0, 0], [0, 2, 0], [1, 1, 1]]
        basis = LA.hermite_normal_form(rows, 3)
        assert len(basis) == 3
        for r in rows:
            assert LA.solve_upper_triangular(basis, r) is not None

    def test_determinant_and_triangular_solve(self) -> None:
        basis = [[2, 1, 0], [0, 3, 0], [0, 0, 5]]
        assert LA.det_int(basis) == 30
        assert LA.solve_upper_triangular(basis, [4, 5, 10]) == [2, 1, 2]
        assert LA.solve_upper_triangular(basis, [1, 0, 0]) is None

    def test_f2_rank(self) -> None:
        assert LA.f2_rank([0b001, 0b010, 0b011]) == 2
        assert LA.f2_rank([1 << i for i in range(24)]) == 24


# ===========================================================================
# 3.  THE GOLAY CODE AND THE MOG ALIGNMENT
# ===========================================================================

class TestGolayAndAlignment:

    def test_code_census(self) -> None:
        c = M.GOLAY.census()
        assert c["codewords"] == 4096
        assert c["octads"] == 759
        assert c["min_distance"] == 8
        assert c["doubly_even"] is True
        assert c["self_dual"] is True
        assert c["matches_expected"] is True

    def test_hexacode(self) -> None:
        assert M.HEXACODE.census() == {"size": 64, "length": 6,
                                       "dimension": 3, "min_distance": 4}

    def test_every_codeword_casts_a_hexacode_shadow(self) -> None:
        failures = [cw for cw in M.GOLAY_MASKS
                    if M.hexacode_shadow(cw) not in M.HEXACODE]
        assert failures == []

    def test_alignment_is_a_permutation(self) -> None:
        assert sorted(M.ALIGNED_BITS) == list(range(24))
        for c in range(24):
            r, col = M.mog_index_of(c)
            assert M.cell_of(r, col) == c


# ===========================================================================
# 4.  THE MOG TRIO, SEXTET AND CUBE GEOMETRY
# ===========================================================================

class TestTrioAndSextet:

    def test_trio_is_three_disjoint_octads_covering_24(self) -> None:
        o1, o2, o3 = M.TRIO
        assert all(LA.popcount(o) == 8 for o in (o1, o2, o3))
        assert all(o in M.GOLAY_SET for o in (o1, o2, o3))
        assert o1 & o2 == 0 and o1 & o3 == 0 and o2 & o3 == 0
        assert o1 | o2 | o3 == (1 << 24) - 1

    def test_sextet_is_six_tetrads_pairing_into_octads(self) -> None:
        assert len(M.SEXTET) == 6
        assert all(LA.popcount(t) == 4 for t in M.SEXTET)
        covered = 0
        for t in M.SEXTET:
            assert covered & t == 0
            covered |= t
        assert covered == (1 << 24) - 1
        for a in range(6):
            for b in range(a + 1, 6):
                assert (M.SEXTET[a] | M.SEXTET[b]) in M.GOLAY_SET

    def test_sextet_of_tetrad_recovers_the_column_sextet(self) -> None:
        assert M.sextet_of_tetrad(M.SEXTET[0]) == tuple(sorted(M.SEXTET))

    def test_trio_of_octad_is_a_partition(self) -> None:
        for octad in M.OCTAD_MASKS[:12]:
            trio = M.trio_of_octad(octad)
            assert len(trio) == 3
            assert all(o in M.GOLAY_SET and LA.popcount(o) == 8 for o in trio)
            assert trio[0] | trio[1] | trio[2] == (1 << 24) - 1

    def test_trio_and_sextet_census(self) -> None:
        census = M.trio_census()
        assert census["octads"] == 759
        assert census["trios"] == 3795
        assert census["sextets"] == 1771

    def test_cube_addressing_is_a_bijection(self) -> None:
        seen = set()
        for i in range(24):
            b, x, y, z = M.cube_coordinates(i)
            assert (b, x, y, z) not in seen
            seen.add((b, x, y, z))
            assert M.coordinate_of_cube(b, x, y, z) == i
            assert (M.BRICKS[b] >> i) & 1 == 1
        assert len(seen) == 24

    def test_cube_profile_and_face_parities(self) -> None:
        full = (1 << 24) - 1
        assert [p["weight"] for p in M.cube_profile(full)] == [8, 8, 8]
        for b in range(3):
            assert M.face_parities(full, b) == (0,) * 6
        single = 1 << M.coordinate_of_cube(0, 0, 0, 0)
        # one bit at the (0,0,0) corner flips exactly the three faces it lies on
        assert M.face_parities(single, 0) == (1, 0, 1, 0, 1, 0)
        assert M.face_parities(single, 1) == (0,) * 6


class TestReshaping:
    """4x6 and 3x8 presentations are bijections for arbitrary payloads."""

    @pytest.mark.parametrize("vector", [
        tuple(range(24)),
        tuple(Fraction(i, 7) for i in range(24)),
        tuple("abcdefghijklmnopqrstuvwx"),
    ])
    def test_grid_4x6_round_trip(self, vector) -> None:
        grid = M.to_grid_4x6(vector)
        assert len(grid) == 4 and all(len(r) == 6 for r in grid)
        assert tuple(M.from_grid_4x6(grid)) == tuple(vector)

    @pytest.mark.parametrize("vector", [
        tuple(range(24)),
        tuple(Fraction(i, 7) for i in range(24)),
        tuple("abcdefghijklmnopqrstuvwx"),
    ])
    def test_trio_3x8_round_trip(self, vector) -> None:
        cubes = M.to_trio_3x8(vector)
        assert len(cubes) == 3 and all(len(c) == 8 for c in cubes)
        assert tuple(M.from_trio_3x8(cubes)) == tuple(vector)

    def test_trio_3x8_respects_the_octads(self) -> None:
        marker = tuple(1 if (M.TRIO[1] >> i) & 1 else 0 for i in range(24))
        cubes = M.to_trio_3x8(marker)
        assert cubes[0] == [0] * 8
        assert cubes[1] == [1] * 8
        assert cubes[2] == [0] * 8

    def test_reshaping_rejects_bad_shapes(self) -> None:
        with pytest.raises(ValueError):
            M.to_grid_4x6(list(range(23)))
        with pytest.raises(ValueError):
            M.from_grid_4x6([[0] * 6] * 3)
        with pytest.raises(ValueError):
            M.from_trio_3x8([[0] * 8] * 2)


# ===========================================================================
# 5.  THE LEECH LATTICE AND Lambda / 2 Lambda
# ===========================================================================

class TestLeechBasis:

    def test_basis_rows_lie_in_lambda(self) -> None:
        assert all(L.in_leech(list(r)) for r in L.LEECH_BASIS)
        assert len(L.LEECH_BASIS) == 24

    def test_determinant_is_the_index_in_z24(self) -> None:
        assert abs(L.basis_determinant()) == L.INDEX_IN_Z24 == (1 << 36)

    def test_coordinate_round_trip(self) -> None:
        for x in leech_points():
            u = L.to_coords(list(x))
            assert u is not None, x
            assert L.from_coords(u) == tuple(x)

    def test_non_lattice_points_are_rejected(self) -> None:
        assert L.to_coords([1] + [0] * 23) is None
        assert not L.in_leech([1] + [0] * 23)
        with pytest.raises(ValueError):
            L.class_of([1] + [0] * 23)

    def test_minimal_vectors_are_minimal_and_counted(self) -> None:
        count = 0
        for v in L.minimal_vectors():
            count += 1
            if count % 40000 == 0:
                assert L.norm2(v) == L.MIN_NORM2
        assert count == L.KISSING == 196560


class TestQuadraticForm:

    def test_class_map_is_well_defined_mod_2lambda(self) -> None:
        for i in range(24):
            x = L.LEECH_BASIS[i]
            y = tuple(a + 2 * b for a, b in zip(x, L.LEECH_BASIS[(i + 5) % 24]))
            assert L.class_of(x) == L.class_of(y)

    def test_q_and_b_match_the_lattice_definition(self) -> None:
        state = 0x9E3779B9
        for _ in range(48):
            state = (state * 1103515245 + 12345) & 0xFFFFFFFF
            u = state & 0xFFFFFF
            state = (state * 1103515245 + 12345) & 0xFFFFFFFF
            w = state & 0xFFFFFF
            xu, xw = L.representative(u), L.representative(w)
            assert L.q_form(u) == (L.norm2(xu) // 16) % 2
            assert L.b_form(u, w) == (L.inner(xu, xw) // 8) % 2

    def test_polar_form_is_symmetric_and_bilinear(self) -> None:
        a, b, c = 0x0F0F0F, 0x00FF00, 0x123456
        assert L.b_form(a, b) == L.b_form(b, a)
        assert L.b_form(a ^ b, c) == (L.b_form(a, c) ^ L.b_form(b, c))

    def test_witt_decomposition_is_12_planes_of_plus_type(self) -> None:
        w = L.witt_decomposition()
        assert w["planes"] == 12
        assert w["plus_type"] is True
        assert w["anisotropic_planes"] % 2 == 0
        assert w["singular_count"] == (1 << 23) + (1 << 11) == 8390656
        assert L.singular_class_count() == 8390656
        assert L.form_is_plus_type() is True

    def test_theta_series_and_class_census_close_at_2_pow_24(self) -> None:
        assert L.theta_series(5)[:5] == [1, 0, 196560, 16773120, 398034000]
        c = L.type_census()
        assert c["type2_classes"] == 98280
        assert c["type3_classes"] == 8386560
        assert c["type4_classes"] == 8292375
        assert c["total"] == L.N_CLASSES == 16777216
        assert c["closes"] is True
        assert c["matches_plus_type"] is True


# ===========================================================================
# 6.  2A AXIS DETECTION
# ===========================================================================

class TestAxisDetection:
    """Type-2 detection against the exhaustive class table."""

    def test_table_has_exactly_98280_classes(self) -> None:
        table = L.type2_class_table()
        assert len(table) == 98280 == L.KISSING // 2
        assert len(L.type2_classes()) == 98280

    def test_table_size_matches_the_theta_series(self) -> None:
        assert len(L.type2_class_table()) == L.type_census()["type2_classes"]

    def test_every_minimal_vector_is_a_2a_axis(self) -> None:
        for v in itertools.islice(L.minimal_vectors(), 0, 300):
            assert L.is_2a_axis(v)

    def test_axis_of_class_returns_the_plus_minus_pair(self) -> None:
        for v in itertools.islice(L.minimal_vectors(), 0, 50):
            cls = L.class_of(v)
            plus, minus = L.axis_of_class(cls)
            assert L.norm2(plus) == L.norm2(minus) == L.MIN_NORM2
            assert minus == tuple(-a for a in plus)
            assert L.class_of(plus) == L.class_of(minus) == cls

    def test_non_axes_are_rejected(self) -> None:
        assert not L.is_2a_axis([0] * 24)                       # type 0
        v = next(iter(L.minimal_vectors()))
        assert not L.is_2a_axis([2 * a for a in v])             # 2v lies in 2L
        assert not L.is_type2_class(0)

    def test_type2_classes_are_singular(self) -> None:
        table = L.type2_class_table()
        for cls in itertools.islice(sorted(table), 0, 500):
            assert L.q_form(cls) == 0

    def test_axis_detection_is_class_invariant(self) -> None:
        """Adding 2 * (a lattice point) cannot change the verdict."""
        shift = tuple(2 * a for a in L.LEECH_BASIS[3])
        for v in itertools.islice(L.minimal_vectors(), 0, 40):
            w = tuple(a + b for a, b in zip(v, shift))
            assert L.class_of(w) == L.class_of(v)
            assert L.is_2a_axis(w) is True

    def test_pair_invariant_census(self) -> None:
        census = L.pair_census()
        assert census == {0: 93150, 1: 94208, 2: 9200, 4: 2}
        assert sum(census.values()) == L.KISSING

    def test_rejects_out_of_range_class(self) -> None:
        with pytest.raises(ValueError):
            L.is_type2_class(1 << 24)


# ===========================================================================
# 7.  THE 10-PLANE DIGIT STACK  --  LOSSLESS RECONSTRUCTION
# ===========================================================================

class TestDigitStack:
    """``class_stack_rebuild(class_stack(v)) == v`` is the Step-1 criterion."""

    def test_defaults_are_the_ten_plane_stack(self) -> None:
        assert DS.STACK_DEPTH == 10
        assert DS.STACK_OFFSET == 1 << 9
        stack = DS.class_stack(tuple([0] * 24))
        assert stack.depth == 10 and len(stack.planes) == 10

    @pytest.mark.parametrize("vector", integer_carriers())
    def test_integer_round_trip(self, vector) -> None:
        stack = DS.class_stack(vector)
        assert DS.class_stack_rebuild(stack) == tuple(vector)
        assert DS.stack_is_faithful(vector)

    @pytest.mark.parametrize("vector", rational_carriers())
    def test_rational_round_trip(self, vector) -> None:
        stack = DS.class_stack(vector)
        rebuilt = DS.class_stack_rebuild(stack)
        assert rebuilt == tuple(vector)
        assert all(isinstance(x, (int, Fraction)) for x in rebuilt)
        assert DS.stack_is_faithful(vector)

    @pytest.mark.parametrize("vector", wide_rational_carriers())
    def test_wide_rational_round_trip_at_derived_depth(self, vector) -> None:
        """Out-of-range carriers are refused at depth 10 and exact when fitted."""
        with pytest.raises(ValueError, match="least admissible pair"):
            DS.class_stack(vector)
        stack = DS.class_stack_fitted(vector)
        assert stack.depth > DS.STACK_DEPTH
        assert DS.class_stack_rebuild(stack) == tuple(vector)

    def test_round_trip_over_lattice_points_in_the_standard_basis(self) -> None:
        for x in in_range_leech_points():
            assert DS.class_stack_rebuild(DS.class_stack(x)) == tuple(x)
        # every lattice point round-trips once the depth is fitted to it
        for x in leech_points():
            fitted = DS.class_stack_fitted(x)
            assert DS.class_stack_rebuild(fitted) == tuple(x)

    def test_round_trip_over_lattice_points_in_the_leech_basis(self) -> None:
        """Leech-basis coordinates of the whole fixture fit the 10 planes."""
        for x in leech_points():
            stack = DS.class_stack(x, basis="leech")
            assert stack.depth == DS.STACK_DEPTH
            assert DS.class_stack_rebuild(stack) == tuple(x)

    def test_plane_zero_in_the_leech_basis_is_the_class(self) -> None:
        for x in leech_points():
            stack = DS.class_stack(x, basis="leech")
            assert stack.planes[0] == L.class_of(x)

    def test_denominator_is_recorded_and_cleared(self) -> None:
        v = tuple(Fraction(i, 6) for i in range(24))
        stack = DS.class_stack(v)
        assert stack.denominator == 6
        assert DS.class_stack_rebuild(stack) == v

    def test_integer_carrier_reports_denominator_one(self) -> None:
        stack = DS.class_stack(tuple(range(24)))
        assert stack.denominator == 1
        assert all(isinstance(x, int)
                   for x in DS.class_stack_rebuild(stack))

    def test_fitted_parameters_are_least_admissible(self) -> None:
        v = tuple([7] * 24)
        stack = DS.class_stack_fitted(v)
        assert (stack.offset, stack.depth) == DS.derive_stack_parameters(7)
        assert DS.class_stack_rebuild(stack) == v

    def test_derive_stack_parameters(self) -> None:
        assert DS.derive_stack_parameters(0) == (1, 1)
        assert DS.derive_stack_parameters(4) == (4, 4)
        assert DS.derive_stack_parameters(512) == (512, 11)
        assert DS.derive_stack_parameters(500)[0] == 512
        with pytest.raises(ValueError):
            DS.derive_stack_parameters(1000, offset=8)

    def test_range_bound_is_conservative_and_symmetric(self) -> None:
        """``derive_stack_parameters`` bounds ``|c|``, not the signed range.

        At offset 512 the representable window is ``[-512, 511]``: the value
        ``-512`` encodes fine, but ``max_abs = 512`` makes the derived depth
        11 because the bound ``2^D > O + max_abs`` is two-sided.  This is a
        deliberate conservatism, not a defect, and it is asserted here so that
        a later change to the formula cannot pass silently.
        """
        assert DS.stack_is_faithful(tuple([-512] * 24))
        assert DS.stack_is_faithful(tuple([511] * 24))
        assert DS.derive_stack_parameters(511) == (512, 10)
        assert DS.derive_stack_parameters(512) == (512, 11)
        with pytest.raises(ValueError):
            DS.class_stack(tuple([512] * 24))

    def test_out_of_range_raises_with_an_actionable_message(self) -> None:
        with pytest.raises(ValueError, match="least admissible pair"):
            DS.class_stack(tuple([5000] * 24))

    def test_deeper_stacks_only_append_zero_planes(self) -> None:
        v = tuple(_lcg(3, 24, -100, 100))
        base = DS.class_stack(v, depth=10)
        deep = DS.class_stack(v, depth=16)
        assert deep.planes[:10] == base.planes
        assert all(p == 0 for p in deep.planes[10:])
        assert DS.class_stack_rebuild(deep) == v

    def test_depth_report_confirms_proposition_d1(self) -> None:
        carriers = [v for v in integer_carriers()
                    if max(abs(c) for c in v) <= 511]
        report = DS.depth_report(carriers)
        assert report["coordinate_range"] == 511
        assert report["faithful_everywhere"] is True
        assert report["deeper_planes_are_zero"] is True
        assert report["lower_planes_unchanged"] is True
        assert report["module_depth_is_admissible"] is True

    def test_wrong_length_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            DS.class_stack(tuple(range(23)))

    def test_leech_basis_rejects_non_lattice_and_rational(self) -> None:
        with pytest.raises(ValueError):
            DS.class_stack([1] + [0] * 23, basis="leech")
        with pytest.raises(ValueError):
            DS.class_stack([Fraction(1, 2)] * 24, basis="leech")


# ===========================================================================
# 8.  FACET PROJECTION AND FAILING-FACET ATTRIBUTION
# ===========================================================================

class TestFacets:

    def test_facet_table_shape(self) -> None:
        assert len(DS.FACETS) == 3 + 6 + 4 + 18 == 31
        assert all(0 <= m < (1 << 24) for m in DS.FACETS.values())
        assert [LA.popcount(DS.FACETS[f"brick{b}"]) for b in range(3)] \
            == [8, 8, 8]
        assert [LA.popcount(DS.FACETS[f"col{c}"]) for c in range(6)] \
            == [4] * 6
        assert [LA.popcount(DS.FACETS[f"row{r}"]) for r in range(4)] \
            == [6] * 4
        faces = [m for k, m in DS.FACETS.items() if k.startswith("cube")]
        assert len(faces) == 18 and all(LA.popcount(m) == 4 for m in faces)

    def test_plane_facets_of_the_empty_and_full_planes(self) -> None:
        empty = DS.plane_facets(0)
        assert empty.weight == 0 and empty.touched_facets == ()
        full = DS.plane_facets((1 << 24) - 1)
        assert full.weight == 24
        assert len(full.touched_facets) == 31

    def test_single_bit_is_localised_to_its_facets(self) -> None:
        coord = M.coordinate_of_cube(1, 0, 1, 0)
        rep = DS.plane_facets(1 << coord)
        assert rep.weight == 1
        assert "brick1" in rep.touched_facets
        assert "brick0" not in rep.touched_facets
        assert "cube1.x0" in rep.touched_facets
        assert "cube1.y1" in rep.touched_facets
        assert "cube1.z0" in rep.touched_facets
        assert "cube1.x1" not in rep.touched_facets

    def test_facet_projection_covers_every_plane(self) -> None:
        stack = DS.class_stack(tuple(_lcg(11, 24, -300, 300)))
        reports = DS.facet_projection(stack)
        assert len(reports) == stack.depth
        for rep, plane in zip(reports, stack.planes):
            assert rep.mask == plane

    def test_true_equation_holds_with_no_blame(self) -> None:
        v = tuple(_lcg(5, 24, -200, 200))
        verdict = DS.verify_equation(v, v)
        assert verdict.holds is True
        assert verdict.failing_planes == ()
        assert verdict.blamed_facets == ()
        assert verdict.first_failing_plane is None

    def test_false_equation_names_the_plane_and_the_facet(self) -> None:
        lhs = list(_lcg(5, 24, -200, 200))
        coord = M.coordinate_of_cube(2, 1, 0, 1)
        rhs = list(lhs)
        rhs[coord] += 1                      # flips at least plane 0
        verdict = DS.verify_equation(lhs, rhs)
        assert verdict.holds is False
        assert 0 in verdict.failing_planes
        assert verdict.first_failing_plane == 0
        assert "brick2" in verdict.blamed_facets
        assert "cube2.x1" in verdict.blamed_facets
        assert "cube2.z1" in verdict.blamed_facets
        # the discrepancy is confined to the single coordinate that moved
        for mask in verdict.difference_masks.values():
            assert mask & ~(1 << coord) == 0

    def test_failure_localises_to_a_high_plane_when_only_a_high_bit_moves(
            self) -> None:
        lhs = tuple([0] * 24)
        rhs = tuple([256 if i == 3 else 0 for i in range(24)])
        verdict = DS.verify_equation(lhs, rhs)
        assert verdict.holds is False
        # 512 -> 768: only bit 8 of the shifted coordinate changes
        assert verdict.failing_planes == (8,)

    def test_rational_equation_is_decided_exactly(self) -> None:
        lhs = tuple(Fraction(1, 3) for _ in range(24))
        rhs = tuple(Fraction(2, 6) for _ in range(24))
        assert DS.verify_equation(lhs, rhs).holds is True
        near = list(rhs)
        near[0] = Fraction(1, 3) + Fraction(1, 1000000)
        # a difference of one part in a million is still a difference
        verdict = DS.verify_equation(lhs, near, depth=32, offset=1 << 31)
        assert verdict.holds is False

    def test_verdict_is_json_serialisable(self) -> None:
        import json
        lhs = tuple([0] * 24)
        rhs = tuple([1] + [0] * 23)
        payload = DS.verify_equation(lhs, rhs).as_dict()
        assert json.loads(json.dumps(payload))["holds"] is False

    def test_mismatched_stacks_are_refused(self) -> None:
        a = DS.class_stack(tuple([0] * 24), depth=10)
        b = DS.class_stack(tuple([0] * 24), depth=12)
        with pytest.raises(ValueError):
            DS.failing_facets(a, b)
        c = DS.class_stack(tuple(Fraction(1, 2) for _ in range(24)))
        with pytest.raises(ValueError, match="denominator"):
            DS.failing_facets(a, c)

    def test_leech_basis_verdict_flags_that_facets_are_not_mog(self) -> None:
        pts = leech_points()
        verdict = DS.verify_equation(pts[1], pts[2], basis="leech")
        assert verdict.mog_geometric is False
        assert "not MOG geometry" in verdict.note


# ===========================================================================
# 9.  TOP-LEVEL REPORTS
# ===========================================================================

class TestReports:

    def test_mog_report(self) -> None:
        r = M.mog_report(full=True)
        assert r["alignment_verified"] is True
        assert r["trio_are_octads"] is True
        assert r["trio_partitions_24"] is True
        assert r["sextet_pairs_are_octads"] is True

    def test_leech2_report(self) -> None:
        r = L.leech2_report(full=True)
        assert r["determinant_matches_index"] is True
        assert r["basis_rows_in_lambda"] is True
        assert r["q_matches_lattice"] is True
        assert r["b_matches_lattice"] is True
        assert r["q_well_defined_mod_2lambda"] is True
        assert r["type2_classes_found"] == 98280
        assert r["type2_matches_theta"] is True
        assert r["type2_all_singular"] is True
