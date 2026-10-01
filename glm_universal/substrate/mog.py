"""The Miracle Octad Generator: Golay code, hexacode shadow, trio and sextet.

This module owns the *combinatorial* half of the GLM-3+ substrate.  It fixes
one labelling of the 24 coordinates and derives, by execution rather than by
quotation, every structure the rest of the system indexes against:

    * the extended binary Golay code ``C = [24, 12, 8]`` in systematic form
      ``G = [I_12 | B]`` -- 4096 codewords, 759 octads, self-dual, doubly even;
    * the MOG alignment, a bijection ``mog_index -> coordinate`` under which
      every Golay codeword's six GF(4) column labels form a hexacode word
      (checked exhaustively over all 4096 codewords);
    * the **trio**: the three 4x2 bricks of the 4x6 MOG frame are three
      pairwise-disjoint octads ``O_1, O_2, O_3`` covering all 24 coordinates;
    * the **sextet**: the six 4-cell columns of the frame are six tetrads, any
      two of which union to an octad;
    * the **MOG-cube trio**: each brick's eight cells are the vertices of a
      2x2x2 cube, giving each coordinate an address ``(brick, x, y, z)``.

Bijective reshaping between a linear 24-vector and its ``4 x 6`` or ``3 x 8``
presentations is provided for arbitrary element types (ints, Fractions, bits),
so the same geometry serves the F_2 layer and the rational carrier layer.

Ported and unified from ``glm_lean/glm/glm_substrate.py`` (GolayCode, GF4,
Hexacode, MOG) and ``glm_lean/glm3/glm3_mog.py`` (trio / sextet / cube).

Notes
-----
Pure Python standard library, exact arithmetic, deterministic.  No RNG is
imported anywhere in this package.
"""

from __future__ import annotations

from itertools import combinations
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple, TypeVar

from .linalg import bits_of, mask_of, popcount

__all__ = [
    "N",
    "GolayCode",
    "GOLAY",
    "GOLAY_MASKS",
    "GOLAY_SET",
    "OCTAD_MASKS",
    "GF4",
    "Hexacode",
    "HEXACODE",
    "ALIGNED_BITS",
    "cell_of",
    "mog_index_of",
    "frame",
    "column_mask",
    "row_mask",
    "brick_mask",
    "COLUMNS",
    "BRICKS",
    "TRIO",
    "SEXTET",
    "hexacode_shadow",
    "cube_coordinates",
    "cube_index",
    "coordinate_of_cube",
    "cube_profile",
    "face_parities",
    "to_grid_4x6",
    "from_grid_4x6",
    "to_trio_3x8",
    "from_trio_3x8",
    "sextet_of_tetrad",
    "trio_of_octad",
    "trio_census",
    "mog_report",
]

N = 24

T = TypeVar("T")


# ===========================================================================
# 1.  THE EXTENDED BINARY GOLAY CODE
# ===========================================================================

class GolayCode:
    """The extended binary Golay code ``C = [24, 12, 8]``, systematic form.

    ``G = [I_12 | B]`` with ``B`` symmetric, so the parity-check matrix is
    ``H = [B | I_12]`` and the code is self-dual.  Every derived fact below
    (codeword count, weight enumerator, octad count, minimum distance) is
    computed by :meth:`census`, never asserted from literature.

    Attributes
    ----------
    B
        The symmetric 12x12 parity block.
    G, H
        Generator and parity-check matrices as lists of 24-bit rows.
    """

    N = 24
    K = 12
    D = 8
    PACKING_RADIUS = 3
    COVERING_RADIUS = 4

    B: Tuple[Tuple[int, ...], ...] = (
        (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
        (1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0),
        (1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1),
        (1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1),
        (1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0),
        (1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1),
        (1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1),
        (1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1),
        (1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0),
        (1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0),
        (1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0),
        (1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1),
    )

    def __init__(self) -> None:
        self.G: List[List[int]] = [
            [1 if i == j else 0 for j in range(12)] + list(self.B[i])
            for i in range(12)
        ]
        self.H: List[List[int]] = [
            [self.B[j][i] for j in range(12)]
            + [1 if i == j else 0 for j in range(12)]
            for i in range(12)
        ]
        self._syn_cols: Tuple[int, ...] = tuple(
            sum((1 << j) for j in range(12) if self.H[j][k]) for k in range(24)
        )
        self._basis_masks: Tuple[int, ...] = tuple(
            mask_of([k for k in range(24) if row[k]]) for row in self.G
        )
        self._codeword_masks: Optional[Tuple[int, ...]] = None
        self._codeword_set: Optional[FrozenSet[int]] = None
        self._octads: Optional[Tuple[int, ...]] = None

    # -- basic maps --------------------------------------------------------
    def encode_mask(self, message: int) -> int:
        """The codeword mask of a 12-bit message, as an XOR of basis rows."""
        if not 0 <= message < (1 << 12):
            raise ValueError("encode_mask: message must be 12 bits")
        out = 0
        for i in range(12):
            if (message >> i) & 1:
                out ^= self._basis_masks[i]
        return out

    def syndrome_int(self, mask: int) -> int:
        """``H . v`` (mod 2) of a 24-bit mask, packed into 12 bits."""
        n = 0
        for k in range(24):
            if (mask >> k) & 1:
                n ^= self._syn_cols[k]
        return n

    def is_codeword(self, mask: int) -> bool:
        """Exact membership test: zero syndrome."""
        return self.syndrome_int(mask) == 0

    # -- enumerations ------------------------------------------------------
    @property
    def codeword_masks(self) -> Tuple[int, ...]:
        """All 4096 codewords as 24-bit masks, sorted."""
        if self._codeword_masks is None:
            words = sorted(self.encode_mask(m) for m in range(1 << 12))
            self._codeword_masks = tuple(words)
            self._codeword_set = frozenset(words)
        return self._codeword_masks

    @property
    def codeword_set(self) -> FrozenSet[int]:
        """Frozen set of the 4096 codeword masks (O(1) membership)."""
        if self._codeword_set is None:
            _ = self.codeword_masks
        assert self._codeword_set is not None
        return self._codeword_set

    @property
    def octad_masks(self) -> Tuple[int, ...]:
        """The 759 weight-8 codewords (octads), sorted."""
        if self._octads is None:
            self._octads = tuple(m for m in self.codeword_masks
                                 if popcount(m) == 8)
        return self._octads

    def weight_enumerator(self) -> Dict[int, int]:
        """Weight distribution of the code, computed by enumeration."""
        out: Dict[int, int] = {}
        for m in self.codeword_masks:
            w = popcount(m)
            out[w] = out.get(w, 0) + 1
        return dict(sorted(out.items()))

    def census(self) -> Dict[str, object]:
        """Everything the code claims about itself, computed."""
        we = self.weight_enumerator()
        nonzero = [w for w in we if w]
        dual_ok = all(self.is_codeword(m) for m in self.codeword_masks)
        return {
            "codewords": len(self.codeword_masks),
            "weight_enumerator": we,
            "min_distance": min(nonzero) if nonzero else 0,
            "octads": len(self.octad_masks),
            "doubly_even": all(w % 4 == 0 for w in we),
            "self_dual": dual_ok,
            "expected_weight_enumerator": {0: 1, 8: 759, 12: 2576,
                                           16: 759, 24: 1},
            "matches_expected": we == {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1},
        }


GOLAY = GolayCode()
GOLAY_MASKS: Tuple[int, ...] = GOLAY.codeword_masks
GOLAY_SET: FrozenSet[int] = GOLAY.codeword_set
OCTAD_MASKS: Tuple[int, ...] = GOLAY.octad_masks


# ===========================================================================
# 2.  GF(4) AND THE HEXACODE
# ===========================================================================

class GF4:
    """GF(4) = {0, 1, w, w^2} as {0, 1, 2, 3}; addition is XOR."""

    SYMBOLS = {0: "0", 1: "1", 2: "w", 3: "w2"}
    MUL: Tuple[Tuple[int, ...], ...] = (
        (0, 0, 0, 0),
        (0, 1, 2, 3),
        (0, 2, 3, 1),
        (0, 3, 1, 2),
    )

    @staticmethod
    def add(a: int, b: int) -> int:
        """Field addition (characteristic 2)."""
        return a ^ b

    @staticmethod
    def mul(a: int, b: int) -> int:
        """Field multiplication."""
        return GF4.MUL[a][b]


class Hexacode:
    """The hexacode ``H_6``: a ``[6, 3, 4]`` code over GF(4), 64 words.

    It is the algebraic shadow of the Golay code under the MOG alignment.
    """

    BASIS: Tuple[Tuple[int, ...], ...] = (
        (1, 1, 1, 1, 1, 1),
        (1, 2, 3, 1, 2, 3),
        (1, 1, 2, 2, 3, 3),
    )

    def __init__(self) -> None:
        words = set()
        for a in range(4):
            for b in range(4):
                for c in range(4):
                    words.add(tuple(
                        GF4.add(GF4.add(GF4.mul(a, self.BASIS[0][i]),
                                        GF4.mul(b, self.BASIS[1][i])),
                                GF4.mul(c, self.BASIS[2][i]))
                        for i in range(6)))
        self.words: Tuple[Tuple[int, ...], ...] = tuple(sorted(words))
        self.word_set: FrozenSet[Tuple[int, ...]] = frozenset(self.words)

    def __contains__(self, word: Sequence[int]) -> bool:
        return tuple(word) in self.word_set

    def min_distance(self) -> int:
        """Minimum Hamming weight of a nonzero hexacode word."""
        return min(sum(1 for x in w if x) for w in self.words if any(w))

    def census(self) -> Dict[str, object]:
        """Size, length, dimension and minimum distance, computed."""
        return {"size": len(self.words), "length": 6, "dimension": 3,
                "min_distance": self.min_distance()}


HEXACODE = Hexacode()


def _column_label(value: int) -> int:
    """GF(4) label of a 4-bit column value: XOR of the set rows' labels."""
    lbl = 0
    for r in range(4):
        if (value >> r) & 1:
            lbl ^= r
    return lbl


COLUMN_LABEL: Tuple[int, ...] = tuple(_column_label(v) for v in range(16))


# ===========================================================================
# 3.  THE MOG ALIGNMENT AND THE 4 x 6 FRAME
# ===========================================================================

#: ``ALIGNED_BITS[6 * row + col]`` is the coordinate index in frame cell
#: ``(row, col)``.  This particular permutation is the one under which the
#: systematic generator above casts hexacode shadows; it is verified
#: exhaustively by :func:`mog_report` over all 4096 codewords.
ALIGNED_BITS: Tuple[int, ...] = (
    0, 4, 6, 19, 16, 11,     # row 0  (row label 0)
    1, 17, 15, 5, 9, 13,     # row 1  (row label 1)
    3, 21, 20, 8, 10, 22,    # row 2  (row label w)
    2, 23, 14, 12, 7, 18,    # row 3  (row label w^2)
)

_INVERSE_ALIGNED: Tuple[int, ...] = tuple(
    ALIGNED_BITS.index(c) for c in range(N))


def cell_of(row: int, col: int) -> int:
    """The coordinate index sitting in frame cell ``(row, col)``."""
    if not (0 <= row < 4 and 0 <= col < 6):
        raise ValueError("cell_of: row in 0..3, col in 0..5")
    return ALIGNED_BITS[6 * row + col]


def mog_index_of(coordinate: int) -> Tuple[int, int]:
    """The frame cell ``(row, col)`` holding a coordinate index."""
    if not 0 <= coordinate < N:
        raise ValueError("mog_index_of: coordinate in 0..23")
    return divmod(_INVERSE_ALIGNED[coordinate], 6)


def frame(mask: int) -> List[List[int]]:
    """The 4x6 grid of bits of a 24-bit mask, in the verified alignment."""
    return [[(mask >> cell_of(r, c)) & 1 for c in range(6)] for r in range(4)]


def hexacode_shadow(mask: int) -> Tuple[int, ...]:
    """The six GF(4) column labels of a 24-bit mask.

    A Golay codeword casts a hexacode word; this is the defining property of
    the alignment and is checked over all 4096 codewords in :func:`mog_report`.
    """
    grid = frame(mask)
    cols = [sum(grid[r][c] << r for r in range(4)) for c in range(6)]
    return tuple(COLUMN_LABEL[v] for v in cols)


def column_mask(col: int) -> int:
    """The 4-cell tetrad mask of MOG column ``col``."""
    if not 0 <= col < 6:
        raise ValueError("column_mask: col in 0..5")
    return mask_of([cell_of(r, col) for r in range(4)])


def row_mask(row: int) -> int:
    """The 6-cell mask of MOG row ``row``."""
    if not 0 <= row < 4:
        raise ValueError("row_mask: row in 0..3")
    return mask_of([cell_of(row, c) for c in range(6)])


def brick_mask(brick: int) -> int:
    """The 8 cells of one 4x2 brick, i.e. one 2x2x2 MOG cube."""
    if not 0 <= brick < 3:
        raise ValueError("brick_mask: brick in 0..2")
    return column_mask(2 * brick) | column_mask(2 * brick + 1)


COLUMNS: Tuple[int, ...] = tuple(column_mask(c) for c in range(6))
BRICKS: Tuple[int, int, int] = (brick_mask(0), brick_mask(1), brick_mask(2))

#: The MOG trio ``(O_1, O_2, O_3)``: three disjoint octads covering the 24
#: coordinates.  Octad-hood and disjointness are asserted at import time.
TRIO: Tuple[int, int, int] = BRICKS

#: The MOG sextet: six disjoint tetrads, pairwise unioning to octads.
SEXTET: Tuple[int, ...] = COLUMNS


def _validate_geometry() -> None:
    """Import-time guard: the trio and sextet really are what we claim."""
    if any(popcount(b) != 8 or b not in GOLAY_SET for b in TRIO):
        raise AssertionError("MOG trio bricks are not octads")
    if TRIO[0] | TRIO[1] | TRIO[2] != (1 << N) - 1:
        raise AssertionError("MOG trio does not cover the 24 coordinates")
    if TRIO[0] & TRIO[1] or TRIO[0] & TRIO[2] or TRIO[1] & TRIO[2]:
        raise AssertionError("MOG trio bricks are not disjoint")
    if any(popcount(c) != 4 for c in SEXTET):
        raise AssertionError("MOG sextet columns are not tetrads")
    for a in range(6):
        for b in range(a + 1, 6):
            if SEXTET[a] & SEXTET[b]:
                raise AssertionError("MOG sextet tetrads overlap")
            if (SEXTET[a] | SEXTET[b]) not in GOLAY_SET:
                raise AssertionError("a sextet pair does not union to an octad")


_validate_geometry()


# ===========================================================================
# 4.  THE MOG-CUBE TRIO
# ===========================================================================

def cube_coordinates(coordinate: int) -> Tuple[int, int, int, int]:
    """Where a coordinate sits in the multi-cube picture.

    Returns ``(brick, x, y, z)`` with ``x`` the column parity inside the
    brick and ``(y, z)`` the two bits of the row, so that each brick's eight
    cells are the vertices of a 2x2x2 cube.
    """
    if not 0 <= coordinate < N:
        raise ValueError("cube_coordinates: coordinate in 0..23")
    row, col = mog_index_of(coordinate)
    brick, x = divmod(col, 2)
    y, z = divmod(row, 2)
    return brick, x, y, z


def cube_index(x: int, y: int, z: int) -> int:
    """The 0..7 vertex index of a cube corner ``(x, y, z)``."""
    return 4 * x + 2 * y + z


def coordinate_of_cube(brick: int, x: int, y: int, z: int) -> int:
    """Inverse of :func:`cube_coordinates`."""
    if not 0 <= brick < 3:
        raise ValueError("coordinate_of_cube: brick in 0..2")
    for v in (x, y, z):
        if v not in (0, 1):
            raise ValueError("coordinate_of_cube: x, y, z must be 0 or 1")
    return cell_of(2 * y + z, 2 * brick + x)


def cube_profile(mask: int) -> List[Dict[str, int]]:
    """Per-cube weight and parity of a 24-bit mask."""
    return [{"brick": b, "weight": popcount(mask & BRICKS[b]),
             "parity": popcount(mask & BRICKS[b]) & 1} for b in range(3)]


def face_parities(mask: int, brick: int) -> Tuple[int, ...]:
    """The six face parities of one cube.

    For each of the three axes and each of the two values, the parity of the
    four cells on that face -- the finest bitwise facet of the MOG cube, and
    the unit of blame used by
    :func:`glm_universal.substrate.digit_stack.failing_facets`.
    """
    out: List[int] = []
    for axis in range(3):
        for value in (0, 1):
            p = 0
            for i in bits_of(BRICKS[brick], N):
                if cube_coordinates(i)[1 + axis] == value and (mask >> i) & 1:
                    p ^= 1
            out.append(p)
    return tuple(out)


# ===========================================================================
# 5.  BIJECTIVE RESHAPING OF A LINEAR 24-VECTOR
# ===========================================================================

def to_grid_4x6(vector: Sequence[T]) -> List[List[T]]:
    """Present a linear 24-vector as the 4x6 MOG frame.

    Works for any element type -- bits, ``int``, ``Fraction`` -- because it
    is a pure permutation of positions.  Inverse: :func:`from_grid_4x6`.
    """
    if len(vector) != N:
        raise ValueError("to_grid_4x6: 24 entries required")
    return [[vector[cell_of(r, c)] for c in range(6)] for r in range(4)]


def from_grid_4x6(grid: Sequence[Sequence[T]]) -> List[T]:
    """Inverse of :func:`to_grid_4x6`."""
    if len(grid) != 4 or any(len(row) != 6 for row in grid):
        raise ValueError("from_grid_4x6: a 4x6 grid is required")
    out: List[Optional[T]] = [None] * N
    for r in range(4):
        for c in range(6):
            out[cell_of(r, c)] = grid[r][c]
    if any(v is None for v in out):
        raise AssertionError("from_grid_4x6: alignment is not a bijection")
    return [v for v in out]  # type: ignore[misc]


def to_trio_3x8(vector: Sequence[T]) -> List[List[T]]:
    """Present a linear 24-vector as three 8-cell octads (the trio).

    ``result[b][cube_index(x, y, z)]`` is the entry at the cube corner
    ``(x, y, z)`` of brick ``b``.  Inverse: :func:`from_trio_3x8`.
    """
    if len(vector) != N:
        raise ValueError("to_trio_3x8: 24 entries required")
    out: List[List[Optional[T]]] = [[None] * 8 for _ in range(3)]
    for i in range(N):
        b, x, y, z = cube_coordinates(i)
        out[b][cube_index(x, y, z)] = vector[i]
    if any(v is None for row in out for v in row):
        raise AssertionError("to_trio_3x8: cube addressing is not a bijection")
    return [[v for v in row] for row in out]  # type: ignore[misc]


def from_trio_3x8(cubes: Sequence[Sequence[T]]) -> List[T]:
    """Inverse of :func:`to_trio_3x8`."""
    if len(cubes) != 3 or any(len(c) != 8 for c in cubes):
        raise ValueError("from_trio_3x8: three 8-cell octads are required")
    out: List[Optional[T]] = [None] * N
    for b in range(3):
        for x in (0, 1):
            for y in (0, 1):
                for z in (0, 1):
                    out[coordinate_of_cube(b, x, y, z)] = \
                        cubes[b][cube_index(x, y, z)]
    if any(v is None for v in out):
        raise AssertionError("from_trio_3x8: not a bijection")
    return [v for v in out]  # type: ignore[misc]


# ===========================================================================
# 6.  SEXTETS AND TRIOS AS CLASSIFIERS
# ===========================================================================

def sextet_of_tetrad(tetrad: int) -> Tuple[int, ...]:
    """The sextet through a tetrad.

    The six tetrads ``T'`` with ``T u T'`` an octad, including ``T`` itself.
    Every 4-subset of the 24 lies in exactly one sextet, so there are
    ``C(24, 4) / 6 = 1771`` of them.
    """
    if popcount(tetrad) != 4:
        raise ValueError("sextet_of_tetrad: need a 4-element subset")
    parts = [tetrad]
    for o in OCTAD_MASKS:
        if o & tetrad == tetrad:
            other = o ^ tetrad
            if other and other not in parts:
                parts.append(other)
    covered = 0
    for p in parts:
        covered |= p
    if len(parts) != 6 or covered != (1 << N) - 1:
        raise AssertionError("sextet computation failed")
    return tuple(sorted(parts))


def trio_of_octad(octad: int) -> Tuple[int, ...]:
    """A trio through an octad: two disjoint octads covering the rest.

    For a given octad there are 30 disjoint octads pairing into 15 trios;
    the lexicographically first one found is returned.
    """
    if octad not in GOLAY_SET or popcount(octad) != 8:
        raise ValueError("trio_of_octad: need an octad")
    rest = ((1 << N) - 1) ^ octad
    for o in OCTAD_MASKS:
        if o & octad == 0:
            third = rest ^ o
            if third in GOLAY_SET:
                return tuple(sorted((octad, o, third)))
    raise AssertionError("no trio found")


def trio_census() -> Dict[str, int]:
    """Count trios: partitions of the 24 coordinates into three octads."""
    partitions = set()
    for o in OCTAD_MASKS:
        rest = ((1 << N) - 1) ^ o
        for p in OCTAD_MASKS:
            if p & o:
                continue
            third = rest ^ p
            if third in GOLAY_SET and popcount(third) == 8:
                partitions.add(frozenset((o, p, third)))
    return {"trios": len(partitions),
            "octads": len(OCTAD_MASKS),
            "sextets": len(list(combinations(range(N), 4))) // 6}


# ===========================================================================
# 7.  REPORT
# ===========================================================================

def mog_report(full: bool = True) -> Dict[str, object]:
    """Everything this module asserts, recomputed on demand."""
    shadow_failures = sum(1 for cw in GOLAY_MASKS
                          if hexacode_shadow(cw) not in HEXACODE)
    report: Dict[str, object] = {
        "golay": GOLAY.census(),
        "hexacode": HEXACODE.census(),
        "alignment_codewords_tested": len(GOLAY_MASKS),
        "alignment_shadow_failures": shadow_failures,
        "alignment_verified": shadow_failures == 0,
        "trio": [f"0x{b:06x}" for b in TRIO],
        "trio_weights": [popcount(b) for b in TRIO],
        "trio_are_octads": all(b in GOLAY_SET and popcount(b) == 8
                               for b in TRIO),
        "trio_partitions_24": (TRIO[0] | TRIO[1] | TRIO[2]) == (1 << N) - 1
                              and not (TRIO[0] & TRIO[1])
                              and not (TRIO[0] & TRIO[2])
                              and not (TRIO[1] & TRIO[2]),
        "sextet": [f"0x{c:06x}" for c in SEXTET],
        "sextet_weights": [popcount(c) for c in SEXTET],
        "sextet_pairs_are_octads": all(
            (SEXTET[a] | SEXTET[b]) in GOLAY_SET
            for a in range(6) for b in range(a + 1, 6)),
        "sextet_of_column0_matches": sextet_of_tetrad(SEXTET[0]) ==
                                     tuple(sorted(SEXTET)),
    }
    if full:
        report["trio_census"] = trio_census()
    return report
