"""``glm_universal.reasoning.multires`` -- addressing at two resolutions.

The directive
-------------
Address the same object at two scales and compare the addresses:

**bit level (micro)**
    an individual cell or bit goes to its MOG coordinates -- the ``4 x 6``
    frame cell, the ``F_2^4`` value of its column, that column's
    ``GF(4) x Z_4`` fibre coordinates, and the local sub-lattice of
    ``Lambda_24`` supported on the column's four coordinates.

**grid level (macro)**
    a whole 2D grid goes to a carrier in ``Q^24`` and thence to a ten-plane
    stack of ``Lambda / 2 Lambda`` Monster addresses
    (:mod:`glm_universal.reasoning.monster_stack`).

**cross level**
    the two addresses are multiplied: inner products under the Griess form and
    the rank-one tensor of their coefficient vectors, and then the whole
    construction is re-run on rescaled, reflected and rotated grids to see
    what survives.

The ``F_2^4 <-> GF(4) x Z_4`` fibration
---------------------------------------
A MOG column is four bits, and the map ``b -> sum b_i w^i`` sending a column to
its hexacode digit is 4-to-1 onto ``GF(4)``: its kernel is the four columns
``{0000, 1000, 0111, 1111}``.  Choosing a representative per digit and
coordinates on the kernel gives an explicit bijection

    ``F_2^4  <->  GF(4) x Z_4``

implemented by :func:`column_to_fibre` and :func:`fibre_to_column` and checked
exhaustively over all 16 columns by :func:`fibre_bijection_report`.  The
kernel is elementary abelian, so the ``Z_4`` coordinate labels the four kernel
elements as residues; it is a bijection of sets, not a group isomorphism, and
the report says which.

What is invariant, and what is not
----------------------------------
:func:`scale_invariance_report` blocks a grid up by a factor ``k`` (each cell
becomes a ``k x k`` block) and measures what changes.  The findings are
computed, not assumed:

* the **signature** -- normalised colour histogram, density, aspect ratio,
  symmetry flags and component count -- is invariant under blocking, under
  reflection in either axis and under rotation by 180 degrees;
* the **census carrier** is not: its counts scale by ``k^2``;
* the **Monster address** is not, and neither are the cross-level inner
  products: they are addresses of the carrier, and the carrier moved.

That pair of findings is the point of the exercise.  Scale invariance is a
property of a chosen statistic, not of an addressing scheme, and this module
separates the two rather than hoping they coincide.

Everything is exact: ``int`` and :class:`~fractions.Fraction` only.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import leech_construct, leech2, mog
from ..substrate.linalg import det_int
from . import monster_stack, product

__all__ = [
    "Grid",
    "column_to_fibre", "fibre_to_column", "fibre_bijection_report",
    "MicroAddress", "micro_address", "column_sublattice",
    "grid_shape", "grid_carrier", "grid_census", "grid_signature",
    "grid_address", "upscale", "reflect_horizontal", "reflect_vertical",
    "rotate180", "SAMPLE_GRIDS",
    "cross_inner", "cross_position", "cross_tensor",
    "cross_level_report",
    "scale_invariance_report", "census_collision_witness",
    "multires_report",
]

Grid = Sequence[Sequence[int]]

DIM = 24
ROWS, COLS = 4, 6


# ===========================================================================
# 1.  BIT LEVEL: F_2^4  <->  GF(4) x Z_4
# ===========================================================================

#: Row ``r`` of the MOG carries the GF(4) label ``r`` (0, 1, w, w^2).
ROW_LABELS: Tuple[int, ...] = (0, 1, 2, 3)

#: The kernel of ``column -> GF(4) digit``: four columns, an F_2^2.
KERNEL: Tuple[int, ...] = tuple(
    v for v in range(16) if mog.COLUMN_LABEL[v] == 0)

#: Generators of the kernel, used as the two bits of the Z_4 coordinate.
_KERNEL_GENERATORS: Tuple[int, int] = (0b0001, 0b1110)

#: Least column value carrying each GF(4) digit.
_DIGIT_REPRESENTATIVE: Tuple[int, ...] = tuple(
    min(v for v in range(16) if mog.COLUMN_LABEL[v] == d) for d in range(4))


def column_to_fibre(value: int) -> Tuple[int, int]:
    """``F_2^4 -> GF(4) x Z_4``: the digit and the position in its fibre."""
    if not 0 <= int(value) < 16:
        raise ValueError("column_to_fibre: a column is four bits")
    value = int(value)
    digit = mog.COLUMN_LABEL[value]
    offset = value ^ _DIGIT_REPRESENTATIVE[digit]
    g1, g2 = _KERNEL_GENERATORS
    b = 1 if offset in (g1, g1 ^ g2) else 0
    a = 1 if offset in (g2, g1 ^ g2) else 0
    if (b * g1) ^ (a * g2) != offset:
        raise AssertionError("column_to_fibre: the offset is not in the "
                             "kernel, which contradicts the digit map")
    return digit, 2 * a + b


def fibre_to_column(digit: int, residue: int) -> int:
    """``GF(4) x Z_4 -> F_2^4``, the inverse of :func:`column_to_fibre`."""
    if not 0 <= int(digit) < 4:
        raise ValueError("fibre_to_column: digit must be a GF(4) element")
    if not 0 <= int(residue) < 4:
        raise ValueError("fibre_to_column: residue must be in Z_4")
    g1, g2 = _KERNEL_GENERATORS
    a, b = divmod(int(residue), 2)
    return _DIGIT_REPRESENTATIVE[int(digit)] ^ (b * g1) ^ (a * g2)


def fibre_bijection_report() -> Dict[str, object]:
    """Check the fibration exhaustively over all 16 columns."""
    forward = {v: column_to_fibre(v) for v in range(16)}
    round_trip = all(fibre_to_column(*forward[v]) == v for v in range(16))
    images = set(forward.values())
    fibres: Dict[int, List[int]] = {}
    for v, (d, _z) in forward.items():
        fibres.setdefault(d, []).append(v)
    kernel_is_cyclic = False
    for g in KERNEL:
        powers = {0}
        x = 0
        for _ in range(4):
            x ^= g
            powers.add(x)
        if g and len(powers) == 4:
            kernel_is_cyclic = True
    return {
        "columns": 16,
        "distinct_images": len(images),
        "bijective": len(images) == 16 and round_trip,
        "round_trip": round_trip,
        "kernel": list(KERNEL),
        "kernel_size": len(KERNEL),
        "fibre_sizes": {d: len(v) for d, v in sorted(fibres.items())},
        "kernel_is_cyclic_of_order_4": kernel_is_cyclic,
        "note": ("the kernel is elementary abelian, so the Z_4 coordinate "
                 "indexes the fibre as a set of residues rather than as a "
                 "cyclic group"),
    }


def column_sublattice(col: int) -> Dict[str, object]:
    """The local ``Lambda_24`` structure on one MOG column.

    The column's four coordinates carry two lattices -- what the column *sees*
    of ``Lambda`` (the projection) and what lives *inside* it (the
    intersection) -- and the index between them is the column's coupling to
    the rest of the lattice.
    """
    indices = tuple(mog.cell_of(r, col) for r in range(ROWS))
    proj = leech_construct.projection_lattice_basis(indices)
    inter = leech_construct.supported_sublattice_basis(indices)
    dproj = abs(det_int([list(r) for r in proj])) if len(proj) == 4 else None
    dinter = (abs(det_int([list(r) for r in inter]))
              if len(inter) == 4 else None)
    index = (dinter // dproj) if (dproj and dinter) else None
    return {
        "column": col,
        "coordinates": list(indices),
        "tetrad_mask": mog.column_mask(col),
        "projection_basis": [list(r) for r in proj],
        "projection_determinant": dproj,
        "intersection_basis": [list(r) for r in inter],
        "intersection_determinant": dinter,
        "index": index,
    }


@dataclass(frozen=True)
class MicroAddress:
    """The address of a single cell of the MOG frame."""

    coordinate: int
    row: int
    col: int
    bit: int
    column_value: int
    gf4_digit: int
    z4_residue: int
    column_mask: int
    axis_class: Optional[int]
    axis_note: str

    def axis(self) -> product.AlgebraVector:
        """The ``2A`` axis this cell's column points at."""
        if self.axis_class is None:
            raise product.PositionError(
                f"cell {self.coordinate}: no 2A axis ({self.axis_note})")
        return product.axis(self.axis_class)

    def as_dict(self) -> Dict[str, object]:
        """A JSON-friendly view."""
        return {
            "coordinate": self.coordinate,
            "row": self.row,
            "col": self.col,
            "bit": self.bit,
            "column_value": self.column_value,
            "gf4_digit": self.gf4_digit,
            "z4_residue": self.z4_residue,
            "column_mask": self.column_mask,
            "axis_class": self.axis_class,
            "axis_note": self.axis_note,
        }


def micro_address(mask: int, coordinate: int,
                  repair: bool = True) -> MicroAddress:
    """Address one bit of a 24-bit plane at MOG resolution.

    The bit's frame cell, its column's ``F_2^4`` value, that value's
    ``GF(4) x Z_4`` fibre coordinates, and the ``2A`` axis carried by the
    column's own 24-bit mask (the plane restricted to the column), repaired if
    necessary by the same rule the ten-plane stack uses.
    """
    if not 0 <= int(mask) < (1 << DIM):
        raise ValueError("micro_address: mask must be a 24-bit integer")
    if not 0 <= int(coordinate) < DIM:
        raise ValueError("micro_address: coordinate must be in 0..23")
    mask, coordinate = int(mask), int(coordinate)
    row, col = mog.mog_index_of(coordinate)
    grid = mog.frame(mask)
    value = sum(grid[r][col] << r for r in range(ROWS))
    digit, residue = column_to_fibre(value)
    restricted = mask & mog.column_mask(col)
    plane = monster_stack.plane_address(col, restricted, repair=repair)
    return MicroAddress(
        coordinate=coordinate, row=row, col=col,
        bit=(mask >> coordinate) & 1,
        column_value=value, gf4_digit=digit, z4_residue=residue,
        column_mask=restricted, axis_class=plane.axis_class,
        axis_note=plane.note or ("the column mask is itself of type 2"
                                 if plane.is_type2 else ""))


# ===========================================================================
# 2.  GRID LEVEL
# ===========================================================================

#: Deterministic sample grids used by the reports and by the task runner.
SAMPLE_GRIDS: Dict[str, Tuple[Tuple[int, ...], ...]] = {
    "cross": ((0, 1, 0), (1, 1, 1), (0, 1, 0)),
    "corner": ((2, 0, 0), (0, 0, 0), (0, 0, 3)),
    "stripes": ((1, 2, 1, 2), (1, 2, 1, 2), (1, 2, 1, 2)),
    "diagonal": ((4, 0, 0), (0, 4, 0), (0, 0, 4)),
    "block": ((5, 5), (5, 5)),
}


def grid_shape(grid: Grid) -> Tuple[int, int]:
    """``(rows, cols)``, with a check that the grid is rectangular."""
    rows = len(grid)
    if rows == 0:
        raise ValueError("grid_shape: the grid is empty")
    cols = len(grid[0])
    if cols == 0 or any(len(r) != cols for r in grid):
        raise ValueError("grid_shape: the grid is not rectangular")
    for r in grid:
        for v in r:
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise ValueError("grid_shape: cells must be non-negative ints")
    return rows, cols


def grid_carrier(grid: Grid, mode: str = "auto") -> Tuple[Fraction, ...]:
    """A 24-coordinate carrier for a whole grid.

    ``"frame"``
        For grids that fit the MOG frame (at most ``4 x 6``): the cell values
        are placed in their frame cells and the rest is zero.  **Lossless**
        given the shape.
    ``"census"``
        For any grid: 24 exact statistics (:func:`grid_census`).  Lossy by
        construction, and :func:`census_collision_witness` exhibits the loss.
    ``"auto"``
        ``"frame"`` when the grid fits, ``"census"`` otherwise.
    """
    rows, cols = grid_shape(grid)
    if mode == "auto":
        mode = "frame" if rows <= ROWS and cols <= COLS else "census"
    if mode == "frame":
        if rows > ROWS or cols > COLS:
            raise ValueError("grid_carrier: the grid does not fit the 4x6 "
                             "MOG frame; use mode='census'")
        out = [Fraction(0)] * DIM
        for r in range(rows):
            for c in range(cols):
                out[mog.cell_of(r, c)] = Fraction(grid[r][c])
        return tuple(out)
    if mode == "census":
        return tuple(Fraction(x) for x in grid_census(grid))
    raise ValueError("grid_carrier: mode must be 'frame', 'census' or 'auto'")


def _components(grid: Grid) -> int:
    """Number of 4-connected components of non-zero cells."""
    rows, cols = grid_shape(grid)
    seen = [[False] * cols for _ in range(rows)]
    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            count += 1
            stack = [(r, c)]
            seen[r][c] = True
            while stack:
                y, x = stack.pop()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if (0 <= ny < rows and 0 <= nx < cols
                            and not seen[ny][nx] and grid[ny][nx]):
                        seen[ny][nx] = True
                        stack.append((ny, nx))
    return count


def grid_census(grid: Grid) -> Tuple[int, ...]:
    """24 integer statistics of a grid, in a fixed order.

    ``0`` rows, ``1`` cols, ``2`` cells, ``3`` distinct colours,
    ``4..13`` counts of colours 0..8 and of everything from 9 up,
    ``14`` horizontal-mirror symmetric, ``15`` vertical-mirror symmetric,
    ``16`` rotation-by-180 symmetric, ``17`` transpose symmetric,
    ``18`` non-zero cells, ``19`` connected components,
    ``20`` bounding-box height, ``21`` bounding-box width,
    ``22`` largest colour, ``23`` a positional checksum.

    Every entry is clamped into ``0..511`` (the checksum is taken modulo 512)
    so that a census carrier always fits the substrate's depth-10 stack at
    offset 512.  The clamp is part of the lossiness of this mode and is
    stated here rather than discovered later: a grid with more than 511 cells
    of one colour reports 511.
    """
    rows, cols = grid_shape(grid)
    counts = [0] * 10
    for r in range(rows):
        for c in range(cols):
            counts[min(grid[r][c], 9)] += 1
    nonzero = [(r, c) for r in range(rows) for c in range(cols)
               if grid[r][c]]
    if nonzero:
        top = min(r for r, _ in nonzero)
        bottom = max(r for r, _ in nonzero)
        left = min(c for _, c in nonzero)
        right = max(c for _, c in nonzero)
        box_h, box_w = bottom - top + 1, right - left + 1
    else:
        box_h = box_w = 0
    checksum = 0
    for r in range(rows):
        for c in range(cols):
            checksum = (checksum + (r * cols + c + 1) * grid[r][c]) % 512
    return _clamp_census((
        rows, cols, rows * cols,
        len({v for r in grid for v in r}),
        *counts,
        int(reflect_horizontal(grid) == _tuple_grid(grid)),
        int(reflect_vertical(grid) == _tuple_grid(grid)),
        int(rotate180(grid) == _tuple_grid(grid)),
        int(rows == cols
            and tuple(zip(*grid)) == _tuple_grid(grid)),
        len(nonzero), _components(grid), box_h, box_w,
        max(v for r in grid for v in r), checksum,
    ))


def _clamp_census(values: Tuple[int, ...]) -> Tuple[int, ...]:
    """Clamp census entries into the depth-10 window ``0..511``."""
    return tuple(min(int(v), 511) for v in values)


def grid_signature(grid: Grid) -> Dict[str, object]:
    """The scale-invariant statistics of a grid.

    Normalised colour histogram, density, aspect ratio, the three symmetry
    flags and the component count.  Every entry is a pure ratio or a Boolean,
    so blocking the grid up by any factor leaves all of them fixed -- which
    :func:`scale_invariance_report` checks rather than assumes.
    """
    rows, cols = grid_shape(grid)
    cells = rows * cols
    counts: Dict[int, int] = {}
    for r in range(rows):
        for c in range(cols):
            counts[grid[r][c]] = counts.get(grid[r][c], 0) + 1
    histogram = {k: Fraction(v, cells) for k, v in sorted(counts.items())}
    nonzero = sum(v for k, v in counts.items() if k)
    return {
        "histogram": histogram,
        "density": Fraction(nonzero, cells),
        "aspect_ratio": Fraction(rows, cols),
        "horizontal_symmetric": reflect_horizontal(grid) == _tuple_grid(grid),
        "vertical_symmetric": reflect_vertical(grid) == _tuple_grid(grid),
        "rot180_symmetric": rotate180(grid) == _tuple_grid(grid),
        "components": _components(grid),
        "colours": tuple(sorted(counts)),
    }


def _tuple_grid(grid: Grid) -> Tuple[Tuple[int, ...], ...]:
    return tuple(tuple(int(v) for v in row) for row in grid)


def upscale(grid: Grid, factor: int) -> Tuple[Tuple[int, ...], ...]:
    """Replace every cell by a ``factor x factor`` block of itself."""
    if factor < 1:
        raise ValueError("upscale: factor must be at least 1")
    grid_shape(grid)
    out: List[Tuple[int, ...]] = []
    for row in grid:
        expanded = tuple(v for v in row for _ in range(factor))
        for _ in range(factor):
            out.append(expanded)
    return tuple(out)


def reflect_horizontal(grid: Grid) -> Tuple[Tuple[int, ...], ...]:
    """Mirror left-right."""
    return tuple(tuple(int(v) for v in reversed(row)) for row in grid)


def reflect_vertical(grid: Grid) -> Tuple[Tuple[int, ...], ...]:
    """Mirror top-bottom."""
    return tuple(tuple(int(v) for v in row) for row in reversed(list(grid)))


def rotate180(grid: Grid) -> Tuple[Tuple[int, ...], ...]:
    """Rotate by half a turn."""
    return reflect_horizontal(reflect_vertical(grid))


def grid_address(grid: Grid, mode: str = "auto",
                 repair: bool = True) -> monster_stack.MonsterAddress:
    """The ten-plane Monster address of a whole grid."""
    return monster_stack.monster_address(grid_carrier(grid, mode=mode),
                                         repair=repair)


# ===========================================================================
# 3.  CROSS LEVEL
# ===========================================================================

def cross_inner(micro: MicroAddress,
                macro: monster_stack.PlaneAddress) -> Optional[Fraction]:
    """The Griess inner product of a bit-level and a grid-level axis.

    ``None`` when either side has no axis; a :class:`~fractions.Fraction`
    otherwise -- 1 when the two addresses coincide, ``1/8`` when they are in
    the ``2A`` position, 0 at ``2B``.  The unmodelled position raises, as it
    does everywhere else in the package.
    """
    if micro.axis_class is None or macro.axis_class is None:
        return None
    return product.griess_form(micro.axis(), macro.axis())


def cross_position(micro: MicroAddress,
                   macro: monster_stack.PlaneAddress) -> Optional[str]:
    """``"1A"``, ``"2A"``, ``"2B"``, ``"unmodelled"`` -- or ``None``.

    ``None`` when either level failed to produce an axis at all, so there is
    no pair to place.  This is the predicate the reports consult before they
    ask for a number, exactly as :func:`monster_stack.compose_sakuma` does at
    the grid level: the unmodelled position is reported, not invented and not
    allowed to escape as an exception.
    """
    if micro.axis_class is None or macro.axis_class is None:
        return None
    return product.position_name(micro.axis_class, macro.axis_class)


def cross_tensor(micro: MicroAddress, macro: monster_stack.PlaneAddress
                 ) -> Dict[str, object]:
    """The rank-one tensor of the two coefficient vectors.

    ``(micro (x) macro)[i, j] = micro_i * macro_j``.  Both sides are single
    axes here, so the tensor has one entry; its rank is 1 by construction and
    the report says so with the entry that witnesses it.  The contraction of
    the tensor against the Griess form is :func:`cross_inner`.
    """
    if micro.axis_class is None or macro.axis_class is None:
        return {"defined": False,
                "position": None,
                "reason": "one of the two levels has no 2A axis"}
    position = product.position_name(micro.axis_class, macro.axis_class)
    if position == "unmodelled":
        return {"defined": False,
                "position": position,
                "reason": "the two axes sit at pair invariant 1, the "
                          "position this kernel does not model: the XOR of "
                          "the two classes is not of type 2, so there is no "
                          "third axis and no inner product to contract"}
    a, b = micro.axis(), macro.axis()
    entries = {f"{i},{j}": str(ci * cj)
               for i, ci in sorted(a.coeffs.items())
               for j, cj in sorted(b.coeffs.items())}
    return {
        "defined": True,
        "entries": entries,
        "rank": 1,
        "contraction": str(product.griess_form(a, b)),
        "position": product.position_name(micro.axis_class,
                                          macro.axis_class),
    }


def cross_level_report(grid: Grid, plane: int = 0) -> Dict[str, object]:
    """Bit-level against grid-level, column by column.

    The grid is addressed as a whole; then, for each of the six MOG columns,
    the first coordinate of that column is addressed at bit level against the
    chosen plane of the grid address, and the two are paired.
    """
    address = grid_address(grid)
    macro = address.planes[plane]
    plane_mask = macro.mask
    rows: List[Dict[str, object]] = []
    for col in range(COLS):
        micro = micro_address(plane_mask, mog.cell_of(0, col))
        position = cross_position(micro, macro)
        inner = None if position in (None, "unmodelled") \
            else cross_inner(micro, macro)
        rows.append({
            "column": col,
            "gf4_digit": micro.gf4_digit,
            "z4_residue": micro.z4_residue,
            "column_value": micro.column_value,
            "micro_axis": micro.axis_class,
            "macro_axis": macro.axis_class,
            "position": position,
            "inner": None if inner is None else str(inner),
            "tensor": cross_tensor(micro, macro),
        })
    defined = [r for r in rows if r["inner"] is not None]
    unmodelled = [r for r in rows if r["position"] == "unmodelled"]
    axisless = [r for r in rows if r["position"] is None]
    return {
        "plane": plane,
        "plane_mask": plane_mask,
        "macro_axis": macro.axis_class,
        "columns": rows,
        "columns_with_inner_product": len(defined),
        "columns_unmodelled": len(unmodelled),
        "columns_without_axis": len(axisless),
        "positions": [r["position"] for r in rows],
        "inner_products": [r["inner"] for r in rows],
    }


# ===========================================================================
# 4.  WHAT SURVIVES A CHANGE OF SCALE
# ===========================================================================

def scale_invariance_report(grids: Optional[Dict[str, Grid]] = None,
                            factors: Sequence[int] = (2, 3)
                            ) -> Dict[str, object]:
    """Block each grid up and record what moved and what did not."""
    if grids is None:
        grids = dict(SAMPLE_GRIDS)
    rows: List[Dict[str, object]] = []
    signature_invariant = True
    census_invariant = True
    address_invariant = True
    for name, grid in sorted(grids.items()):
        base_sig = grid_signature(grid)
        base_census = grid_census(grid)
        base_address = grid_address(grid).masks()
        for k in factors:
            big = upscale(grid, k)
            sig = grid_signature(big)
            census = grid_census(big)
            address = grid_address(big).masks()
            same_sig = sig == base_sig
            same_census = census == base_census
            same_address = address == base_address
            signature_invariant &= same_sig
            census_invariant &= same_census
            address_invariant &= same_address
            rows.append({
                "grid": name,
                "factor": k,
                "signature_invariant": same_sig,
                "census_invariant": same_census,
                "address_invariant": same_address,
            })
    reflected = []
    for name, grid in sorted(grids.items()):
        for label, image in (("horizontal", reflect_horizontal(grid)),
                             ("vertical", reflect_vertical(grid)),
                             ("rot180", rotate180(grid))):
            same = grid_signature(image) == grid_signature(grid)
            reflected.append({"grid": name, "symmetry": label,
                              "signature_invariant": same})
    return {
        "rows": rows,
        "reflections": reflected,
        "signature_invariant_under_scaling": signature_invariant,
        "census_invariant_under_scaling": census_invariant,
        "address_invariant_under_scaling": address_invariant,
        "signature_invariant_under_reflection": all(
            r["signature_invariant"] for r in reflected),
        "reading": ("the signature is a ratio statistic and survives; the "
                    "census counts cells and does not; the Monster address "
                    "is an address of the carrier, and the carrier moved"),
    }


def census_collision_witness() -> Dict[str, object]:
    """Two different grids with the same census: the loss, exhibited.

    Searched deterministically over the ``2 x 2`` grids with entries in
    ``{0, 1}``, in lexicographic order, so the witness is a function of the
    definition of :func:`grid_census` and of nothing else.
    """
    seen: Dict[Tuple[int, ...], Tuple[Tuple[int, ...], ...]] = {}
    for bits in range(16):
        grid = ((bits & 1, (bits >> 1) & 1),
                ((bits >> 2) & 1, (bits >> 3) & 1))
        key = grid_census(grid)
        if key in seen and seen[key] != grid:
            return {
                "found": True,
                "first": [list(r) for r in seen[key]],
                "second": [list(r) for r in grid],
                "census": list(key),
                "carriers_equal": (grid_carrier(seen[key], mode="census")
                                   == grid_carrier(grid, mode="census")),
                "frame_carriers_equal": (grid_carrier(seen[key], mode="frame")
                                         == grid_carrier(grid, mode="frame")),
            }
        seen[key] = grid
    return {"found": False}


# ===========================================================================
# 5.  ONE REPORT
# ===========================================================================

def multires_report(grid: Optional[Grid] = None) -> Dict[str, object]:
    """The whole directive, recomputed."""
    if grid is None:
        grid = SAMPLE_GRIDS["cross"]
    return {
        "fibration": fibre_bijection_report(),
        "columns": [column_sublattice(c) for c in range(COLS)],
        "grid": [list(r) for r in grid],
        "grid_signature": {k: str(v)
                           for k, v in grid_signature(grid).items()},
        "grid_census": list(grid_census(grid)),
        "cross_level": cross_level_report(grid),
        "scale_invariance": scale_invariance_report(),
        "census_collision": census_collision_witness(),
    }
