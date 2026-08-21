"""Mathematical carriers: rational matrices, reflections, and field elements.

Three kinds of mathematical object fit 24 coordinates without compromise, and
this module refuses to pretend about the ones that do not.

:class:`RationalMatrix`
    Any ``r x c`` matrix over ``Q`` with ``r * c <= 24``.  Entries are laid out
    in row-major order and the unused tail is zero-padded; the shape travels in
    the attributes, so the round trip restores a ``2 x 5`` and a ``5 x 2`` as
    different objects.  The shapes that fill the carrier exactly -- ``1x24``,
    ``2x12``, ``3x8``, ``4x6``, ``6x4``, ``8x3``, ``12x2``, ``24x1`` -- are the
    ones that align with the MOG's own presentations, and ``4x6`` is the MOG
    frame itself.
:class:`Reflection`
    The reflection of ``R^24`` in the hyperplane orthogonal to a root ``r``:
    ``x -> x - 2 <x, r> / <r, r> * r``.  The carrier *is* the root.  When the
    root is a Leech minimal vector the reflection is one of the Monster's
    ``2A`` involutions in the geometric sense the substrate can check, and
    :meth:`Reflection.is_2a_axis` reports which case holds rather than
    assuming.
:class:`FieldElement`
    An element of ``GF(2)^24`` or ``GF(4)^6`` (the hexacode's alphabet).  The
    GF(4) case stores six symbols and expands to 24 coordinates through the
    hexacode's own presentation.

Every transform is applied with exact rational arithmetic.  A reflection
composed with itself returns the identity **exactly**, which is asserted in the
test suite -- with floats it would only return it to within rounding, and the
whole point of the substrate is that "within rounding" is not available here.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import leech2, mog
from .base import Codec, DataObject, Scalar, as_exact, exact_vector

__all__ = [
    "MATRIX_LAYOUT", "EXACT_SHAPES",
    "RationalMatrix", "Reflection", "FieldElement",
    "MatrixCodec", "ReflectionCodec", "FieldElementCodec",
    "mathematics_objects", "reflect", "compose_matrices",
]

#: Shapes whose entry count is exactly 24.
EXACT_SHAPES: Tuple[Tuple[int, int], ...] = (
    (1, 24), (2, 12), (3, 8), (4, 6), (6, 4), (8, 3), (12, 2), (24, 1))

MATRIX_LAYOUT: Tuple[str, ...] = tuple(f"entry{i:02d}" for i in range(24))


# ===========================================================================
# 1.  RATIONAL MATRICES
# ===========================================================================

@dataclass(frozen=True)
class RationalMatrix:
    """An ``r x c`` matrix over ``Q`` with at most 24 entries."""

    name: str
    rows: int
    cols: int
    entries: Tuple[Fraction, ...]

    def __post_init__(self) -> None:
        if self.rows < 1 or self.cols < 1:
            raise ValueError("RationalMatrix: dimensions must be positive")
        if self.rows * self.cols > 24:
            raise ValueError(
                f"RationalMatrix: {self.rows}x{self.cols} needs "
                f"{self.rows * self.cols} coordinates; the carrier holds 24")
        if len(self.entries) != self.rows * self.cols:
            raise ValueError(
                f"RationalMatrix: expected {self.rows * self.cols} entries, "
                f"got {len(self.entries)}")
        object.__setattr__(self, "entries",
                           tuple(as_exact(e) for e in self.entries))

    @classmethod
    def from_rows(cls, name: str,
                  rows: Sequence[Sequence[object]]) -> "RationalMatrix":
        """Build from a nested row sequence."""
        r = len(rows)
        c = len(rows[0]) if r else 0
        if any(len(row) != c for row in rows):
            raise ValueError("RationalMatrix.from_rows: ragged rows")
        flat = [as_exact(v) for row in rows for v in row]
        return cls(name=name, rows=r, cols=c, entries=tuple(flat))

    def row_list(self) -> List[List[Fraction]]:
        """The entries as a nested row list."""
        return [list(self.entries[i * self.cols:(i + 1) * self.cols])
                for i in range(self.rows)]

    @property
    def fills_carrier(self) -> bool:
        """Whether the shape uses all 24 coordinates with no padding."""
        return self.rows * self.cols == 24

    @property
    def is_mog_frame(self) -> bool:
        """Whether the shape is the MOG's own ``4 x 6`` frame."""
        return (self.rows, self.cols) == (4, 6)

    def transpose(self) -> "RationalMatrix":
        """The transpose, as a new matrix."""
        rows = self.row_list()
        flipped = [[rows[i][j] for i in range(self.rows)]
                   for j in range(self.cols)]
        return RationalMatrix.from_rows(f"{self.name}^T", flipped)

    def trace(self) -> Fraction:
        """Sum of the diagonal; requires a square matrix."""
        if self.rows != self.cols:
            raise ValueError("trace: matrix is not square")
        rows = self.row_list()
        return sum((rows[i][i] for i in range(self.rows)), Fraction(0))


def compose_matrices(a: RationalMatrix, b: RationalMatrix,
                     name: Optional[str] = None) -> RationalMatrix:
    """Exact matrix product ``a @ b``; the result must still fit 24 entries."""
    if a.cols != b.rows:
        raise ValueError(f"compose_matrices: {a.rows}x{a.cols} cannot multiply "
                         f"{b.rows}x{b.cols}")
    ra, rb = a.row_list(), b.row_list()
    out = [[sum((ra[i][k] * rb[k][j] for k in range(a.cols)), Fraction(0))
            for j in range(b.cols)] for i in range(a.rows)]
    return RationalMatrix.from_rows(name or f"({a.name})({b.name})", out)


class MatrixCodec(Codec):
    """Row-major embedding of a rational matrix, zero-padded to 24."""

    domain = "mathematics"
    layout = MATRIX_LAYOUT

    def encode(self, source: RationalMatrix) -> DataObject:
        carrier: List[Scalar] = list(source.entries)
        carrier.extend([0] * (24 - len(carrier)))
        return DataObject(
            name=source.name, domain=self.domain, carrier=carrier,
            attributes={
                "kind": "rational_matrix",
                "rows": source.rows, "cols": source.cols,
                "entry_count": source.rows * source.cols,
                "fills_carrier": source.fills_carrier,
                "is_mog_frame": source.is_mog_frame,
            },
            layout=MATRIX_LAYOUT,
            provenance={"embedding": "row-major, zero-padded tail"},
        )

    def decode(self, obj: DataObject) -> RationalMatrix:
        a = obj.attributes
        n = int(a["rows"]) * int(a["cols"])
        return RationalMatrix(name=obj.name, rows=int(a["rows"]),
                              cols=int(a["cols"]),
                              entries=tuple(as_exact(x)
                                            for x in obj.carrier[:n]))


# ===========================================================================
# 2.  REFLECTIONS
# ===========================================================================

def reflect(vector: Sequence[Scalar],
            root: Sequence[Scalar]) -> Tuple[Fraction, ...]:
    """Reflect ``vector`` in the hyperplane orthogonal to ``root``, exactly.

    ``x -> x - 2 <x, r> / <r, r> * r``.  All arithmetic is over ``Q``, so
    reflecting twice returns the input with no residual whatsoever.
    """
    v = [as_exact(x) for x in vector]
    r = [as_exact(x) for x in root]
    if len(v) != 24 or len(r) != 24:
        raise ValueError("reflect: both arguments need 24 coordinates")
    rr = sum((x * x for x in r), Fraction(0))
    if rr == 0:
        raise ValueError("reflect: the root must be nonzero")
    vr = sum((a * b for a, b in zip(v, r)), Fraction(0))
    factor = 2 * vr / rr
    return tuple(a - factor * b for a, b in zip(v, r))


@dataclass(frozen=True)
class Reflection:
    """The reflection of ``R^24`` in the hyperplane orthogonal to a root."""

    name: str
    root: Tuple[Fraction, ...]

    def __post_init__(self) -> None:
        root = tuple(as_exact(x) for x in self.root)
        if len(root) != 24:
            raise ValueError("Reflection: the root needs 24 coordinates")
        if all(x == 0 for x in root):
            raise ValueError("Reflection: the root must be nonzero")
        object.__setattr__(self, "root", root)

    def apply(self, vector: Sequence[Scalar]) -> Tuple[Fraction, ...]:
        """Reflect a vector."""
        return reflect(vector, self.root)

    def norm2(self) -> Fraction:
        """``<r, r>`` -- the squared norm of the root."""
        return sum((x * x for x in self.root), Fraction(0))

    def is_involution_on(self, vector: Sequence[Scalar]) -> bool:
        """Whether applying it twice returns the vector exactly."""
        return self.apply(self.apply(vector)) == tuple(
            as_exact(x) for x in vector)

    def is_2a_axis(self) -> bool:
        """Whether the root is a type-2 (``2A``) axis of the Leech lattice.

        A non-integral root, or an integral one outside ``Lambda``, is simply
        not an axis; the substrate raises in that case, so the lattice
        membership is checked first and the answer is ``False`` rather than an
        exception.
        """
        if any(x.denominator != 1 for x in self.root):
            return False
        point = [int(x) for x in self.root]
        if not leech2.in_leech(point):
            return False
        return leech2.is_2a_axis(point)


class ReflectionCodec(Codec):
    """The carrier of a reflection is its root."""

    domain = "mathematics"
    layout = tuple(f"root{i:02d}" for i in range(24))

    def encode(self, source: Reflection) -> DataObject:
        integral = all(x.denominator == 1 for x in source.root)
        return DataObject(
            name=source.name, domain=self.domain,
            carrier=list(source.root),
            attributes={
                "kind": "reflection",
                "root_norm2": str(source.norm2()),
                "root_is_integral": integral,
                "is_2a_axis": source.is_2a_axis(),
            },
            layout=self.layout,
            provenance={"transform": "x -> x - 2<x,r>/<r,r> r, exact over Q"},
        )

    def decode(self, obj: DataObject) -> Reflection:
        return Reflection(name=obj.name,
                          root=tuple(as_exact(x) for x in obj.carrier))


# ===========================================================================
# 3.  FIELD ELEMENTS
# ===========================================================================

@dataclass(frozen=True)
class FieldElement:
    """An element of ``GF(2)^24`` or ``GF(4)^6``."""

    name: str
    field_order: int
    symbols: Tuple[int, ...]

    def __post_init__(self) -> None:
        if self.field_order == 2:
            expected, top = 24, 1
        elif self.field_order == 4:
            expected, top = 6, 3
        else:
            raise ValueError("FieldElement: field order must be 2 or 4")
        if len(self.symbols) != expected:
            raise ValueError(f"FieldElement: GF({self.field_order}) needs "
                             f"{expected} symbols")
        if any(not 0 <= s <= top for s in self.symbols):
            raise ValueError(f"FieldElement: symbols must lie in "
                             f"0..{top}")

    def as_mask(self) -> int:
        """The 24-bit mask, for GF(2) elements only."""
        if self.field_order != 2:
            raise ValueError("as_mask: only defined over GF(2)")
        m = 0
        for i, s in enumerate(self.symbols):
            if s:
                m |= 1 << i
        return m

    def is_golay_codeword(self) -> bool:
        """Whether a GF(2) element lies in the ``[24, 12, 8]`` code."""
        return self.field_order == 2 and self.as_mask() in mog.GOLAY_SET

    def is_hexacode_word(self) -> bool:
        """Whether a GF(4) element lies in the hexacode."""
        if self.field_order != 4:
            return False
        return tuple(self.symbols) in {tuple(w) for w in mog.HEXACODE.words}


class FieldElementCodec(Codec):
    """GF(2) symbols occupy all 24 coordinates; GF(4) symbols occupy six."""

    domain = "mathematics"
    layout = tuple(f"symbol{i:02d}" for i in range(24))

    def encode(self, source: FieldElement) -> DataObject:
        carrier: List[Scalar] = list(source.symbols)
        carrier.extend([0] * (24 - len(carrier)))
        return DataObject(
            name=source.name, domain=self.domain, carrier=carrier,
            attributes={
                "kind": "field_element",
                "field_order": source.field_order,
                "symbol_count": len(source.symbols),
                "is_golay_codeword": source.is_golay_codeword(),
                "is_hexacode_word": source.is_hexacode_word(),
            },
            layout=self.layout,
            provenance={"embedding": "symbols in order, zero-padded tail"},
        )

    def decode(self, obj: DataObject) -> FieldElement:
        n = int(obj.attributes["symbol_count"])
        return FieldElement(name=obj.name,
                            field_order=int(obj.attributes["field_order"]),
                            symbols=tuple(int(x) for x in obj.carrier[:n]))


# ===========================================================================
# 4.  A SMALL CANONICAL COLLECTION
# ===========================================================================

def mathematics_objects() -> Tuple[DataObject, ...]:
    """A deterministic collection covering all three mathematical kinds.

    Includes the MOG frame shape, every carrier-filling shape, a padded shape,
    a high-denominator rational matrix, reflections in a Leech minimal vector
    and in a non-lattice root, the first Golay codewords and the first
    hexacode words.  Nothing here is random; the collection is the same on
    every run.
    """
    mats = MatrixCodec()
    refs = ReflectionCodec()
    fields = FieldElementCodec()
    out: List[DataObject] = []

    # -- matrices: every exactly-filling shape, plus a padded one ----------
    for r, c in EXACT_SHAPES:
        entries = [Fraction(i + 1, (i % 7) + 1) for i in range(r * c)]
        out.append(mats.encode(RationalMatrix(
            name=f"filled_{r}x{c}", rows=r, cols=c, entries=tuple(entries))))
    out.append(mats.encode(RationalMatrix.from_rows(
        "identity_4x4", [[Fraction(int(i == j)) for j in range(4)]
                         for i in range(4)])))
    out.append(mats.encode(RationalMatrix.from_rows(
        "high_denominator_2x3",
        [[Fraction(1, 3), Fraction(1, 7), Fraction(1, 11)],
         [Fraction(1, 13), Fraction(1, 17), Fraction(1, 19)]])))
    out.append(mats.encode(RationalMatrix.from_rows(
        "wide_range_1x4",
        [[Fraction(10 ** 18), Fraction(-10 ** 18),
          Fraction(1, 10 ** 12), Fraction(0)]])))

    # -- reflections --------------------------------------------------------
    minimal = next(iter(leech2.minimal_vectors()))
    out.append(refs.encode(Reflection(name="leech_minimal_root",
                                      root=tuple(Fraction(x)
                                                 for x in minimal))))
    basis_root = [Fraction(0)] * 24
    basis_root[0] = Fraction(1)
    out.append(refs.encode(Reflection(name="axis_root_e0",
                                      root=tuple(basis_root))))
    rational_root = [Fraction(1, 3)] * 24
    out.append(refs.encode(Reflection(name="rational_root_thirds",
                                      root=tuple(rational_root))))

    # -- field elements -----------------------------------------------------
    for idx in (0, 1, 2, 4095):
        word = mog.GOLAY_MASKS[idx]
        symbols = tuple((word >> i) & 1 for i in range(24))
        out.append(fields.encode(FieldElement(
            name=f"golay_codeword_{idx}", field_order=2, symbols=symbols)))
    for idx, word in enumerate(mog.HEXACODE.words[:4]):
        out.append(fields.encode(FieldElement(
            name=f"hexacode_word_{idx}", field_order=4,
            symbols=tuple(int(s) for s in word))))

    return tuple(out)
