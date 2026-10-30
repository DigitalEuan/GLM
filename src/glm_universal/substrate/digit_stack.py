"""The 10-plane 2-adic digit stack: a carrier as a tower of MOG frames.

A single reduction ``Lambda -> Lambda/2Lambda`` keeps one bit per coordinate
and throws the carrier away.  The **digit stack** keeps everything: write each
of the 24 coordinates in binary after a fixed translation, and let *plane k* be
the 24-bit mask of the k-th binary digit.  Each plane is a 24-bit mask, hence a
MOG frame and (in the Leech basis) a class of ``Lambda/2Lambda``; a carrier is
therefore not one Monster address but a stack of them.

The three properties that make this a substrate rather than a picture:

1. **Lossless.**  ``class_stack_rebuild(class_stack(v)) == v`` exactly, for
   every ``v`` in range.  Proposition D1 below turns "10 planes" from a magic
   number into a measurement of the data's coordinate range.
2. **Exact over Q.**  Rational carriers are cleared by their least common
   denominator before expansion; the denominator travels with the stack, so
   reconstruction returns the original :class:`~fractions.Fraction` values with
   no rounding anywhere.
3. **Attributable.**  A vector equation ``lhs == rhs`` is decided plane by
   plane, and a failure is localised to a *facet* -- a named subset of the 24
   coordinates drawn from the MOG geometry (trio bricks, sextet columns, frame
   rows, cube faces).  A false equation does not merely fail; it names where.

Proposition D1 (faithfulness at any admissible depth)
-----------------------------------------------------
Let ``max_abs`` bound the absolute value of the integer coordinates to be
encoded.  Let the offset ``O >= max_abs`` and let the depth ``D`` satisfy
``2^D > O + max_abs``.  Then every shifted coordinate ``u_i + O`` lies in
``[0, 2^D)``, so its binary expansion has ``D`` digits, and reading the k-th
digit of each coordinate and reassembling ``sum_k 2^k d_k - O`` is the identity
on ``[0, 2^D)``.  Faithfulness is a statement about the *range of the data*,
not about the number ten.  Raising ``D`` above the admissible minimum only
appends identically-zero planes, which is why reasoning above the stack is
depth-independent.

The module defaults ``STACK_OFFSET = 2^9`` and ``STACK_DEPTH = 10`` are the
least admissible pair for data with ``max_abs <= 512``, which covers the whole
Leech register (minimal vectors have coordinates bounded by 4) with several
octaves of headroom.  :func:`derive_stack_parameters` computes the least
admissible pair for any other range.

Ported and generalised from ``glm_lean/glm3/glm3_leech2.py`` (``class_stack``)
and ``glm_lean/glm3/glm3_mog.py`` (``plane_stack``).
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import gcd
from typing import Dict, List, Optional, Sequence, Tuple, Union

from . import mog
from .linalg import popcount

__all__ = [
    "N", "STACK_OFFSET", "STACK_DEPTH",
    "Scalar", "Carrier", "DigitStack", "FacetReport", "EquationVerdict",
    "coordinate_range", "derive_stack_parameters",
    "class_stack", "class_stack_rebuild", "class_stack_fitted",
    "stack_is_faithful", "depth_report",
    "FACETS", "facet_masks", "facet_projection", "plane_facets",
    "failing_facets", "verify_equation",
]

N = 24

#: Default translation applied to every coordinate before binary expansion.
STACK_OFFSET = 1 << 9

#: Default number of digit planes.  Least admissible depth for the default
#: offset; see Proposition D1 in the module docstring.
STACK_DEPTH = 10

Scalar = Union[int, Fraction]
Carrier = Sequence[Scalar]


# ===========================================================================
# 1.  RANGE AND PARAMETERS
# ===========================================================================

def _as_fraction(value: Scalar) -> Fraction:
    """Coerce an exact scalar to :class:`~fractions.Fraction`.

    Floats are rejected outright: admitting one would make every downstream
    residue claim unfalsifiable.
    """
    if isinstance(value, bool):
        raise TypeError("digit_stack: booleans are not carrier scalars")
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, Fraction):
        return value
    raise TypeError(
        f"digit_stack: exact scalars only (int / Fraction), got "
        f"{type(value).__name__}; convert with Fraction(numerator, denominator)"
    )


def _clear_denominators(vector: Carrier) -> Tuple[Tuple[int, ...], int]:
    """Scale a rational carrier to integers by its least common denominator.

    Returns ``(integer_coordinates, denominator)`` with ``denominator >= 1``.
    """
    fracs = [_as_fraction(v) for v in vector]
    den = 1
    for f in fracs:
        den = den * f.denominator // gcd(den, f.denominator)
    ints = []
    for f in fracs:
        scaled = f * den
        if scaled.denominator != 1:
            raise AssertionError("denominator clearing failed")
        ints.append(int(scaled))
    return tuple(ints), den


def coordinate_range(vectors: Sequence[Carrier]) -> int:
    """Largest absolute *cleared-integer* coordinate over a set of carriers.

    This is the only property of the data that the stack parameters depend on.
    """
    worst = 0
    for v in vectors:
        ints, _den = _clear_denominators(v)
        for c in ints:
            worst = max(worst, abs(c))
    return worst


def derive_stack_parameters(max_abs: int,
                            offset: Optional[int] = None) -> Tuple[int, int]:
    """``(offset, depth)`` for data bounded in absolute value by ``max_abs``.

    With no offset supplied the least admissible pair is returned: the least
    power of two ``O >= max_abs`` (so the shift is a shift of digit planes and
    not an arbitrary translation), then the least ``D`` with
    ``2^D > O + max_abs``.
    """
    if max_abs < 0:
        raise ValueError("derive_stack_parameters: negative range")
    if offset is None:
        offset = 1
        while offset < max_abs:
            offset <<= 1
    if offset < max_abs:
        raise ValueError(
            f"derive_stack_parameters: offset {offset} below the range "
            f"{max_abs}")
    depth = 1
    while (1 << depth) <= offset + max_abs:
        depth += 1
    return offset, depth


# ===========================================================================
# 2.  THE STACK
# ===========================================================================

@dataclass(frozen=True)
class DigitStack:
    """A carrier presented as ``depth`` binary digit planes.

    Attributes
    ----------
    planes
        ``planes[k]`` is the 24-bit mask of the k-th binary digit of the
        shifted, denominator-cleared coordinates.  Plane 0 of a lattice point
        in the Leech basis is its class in ``Lambda/2Lambda``.
    depth
        Number of planes.
    offset
        Translation applied to every coordinate before expansion.
    denominator
        The least common denominator that was cleared; ``1`` for integer
        carriers.
    basis
        ``"standard"`` for the 24 Euclidean coordinates (where the MOG facet
        geometry applies) or ``"leech"`` for coordinates in the Leech Z-basis
        (where plane 0 is the ``Lambda/2Lambda`` class, but facet names index
        basis vectors rather than MOG cells).
    """

    planes: Tuple[int, ...]
    depth: int
    offset: int
    denominator: int
    basis: str

    def __post_init__(self) -> None:
        if len(self.planes) != self.depth:
            raise ValueError("DigitStack: plane count does not match depth")
        if self.denominator < 1:
            raise ValueError("DigitStack: denominator must be positive")
        if self.basis not in ("standard", "leech"):
            raise ValueError("DigitStack: basis must be 'standard' or 'leech'")
        if any(p < 0 or p >= (1 << N) for p in self.planes):
            raise ValueError("DigitStack: planes must be 24-bit masks")

    @property
    def mog_geometric(self) -> bool:
        """Whether MOG facet names refer to real MOG cells for this stack."""
        return self.basis == "standard"

    def rebuild(self) -> Tuple[Scalar, ...]:
        """The carrier this stack came from.  See :func:`class_stack_rebuild`."""
        return class_stack_rebuild(self)

    def nonzero_planes(self) -> Tuple[int, ...]:
        """Indices of the planes that carry at least one set bit."""
        return tuple(k for k, p in enumerate(self.planes) if p)

    def plane_weights(self) -> Tuple[int, ...]:
        """Hamming weight of each plane."""
        return tuple(popcount(p) for p in self.planes)


def _leech_coords(vector: Carrier) -> Tuple[int, ...]:
    """Leech-basis coordinates of an integral lattice point."""
    from . import leech2  # local import: leech2 does not depend on this module
    ints = []
    for v in vector:
        f = _as_fraction(v)
        if f.denominator != 1:
            raise ValueError(
                "class_stack(basis='leech'): Leech points are integral in the "
                "x sqrt(8) model; a rational carrier has no Leech basis "
                "coordinates")
        ints.append(int(f))
    u = leech2.to_coords(ints)
    if u is None:
        raise ValueError("class_stack(basis='leech'): point is not in Lambda")
    return tuple(u)


def class_stack(vector: Carrier,
                depth: Optional[int] = None,
                offset: Optional[int] = None,
                basis: str = "standard") -> DigitStack:
    """The 2-adic digit stack of a 24-dimensional carrier over Q or Z.

    Parameters
    ----------
    vector
        24 exact scalars (``int`` or :class:`~fractions.Fraction`).
    depth, offset
        Stack parameters; default to :data:`STACK_DEPTH` and
        :data:`STACK_OFFSET`.  Any admissible pair rebuilds the carrier
        exactly (Proposition D1); an inadmissible pair raises with the least
        admissible pair named in the message.
    basis
        ``"standard"`` (default) expands the 24 Euclidean coordinates.
        ``"leech"`` expands the coordinates in the Leech Z-basis, so that
        plane 0 is the class of the point in ``Lambda/2Lambda``.

    Returns
    -------
    DigitStack

    Raises
    ------
    ValueError
        If a coordinate falls outside ``[-offset, 2^depth - offset)``, or if
        ``basis='leech'`` and the carrier is not an integral point of
        ``Lambda``.
    TypeError
        If a coordinate is a float or any other inexact type.
    """
    if len(vector) != N:
        raise ValueError(f"class_stack: {N} coordinates required, "
                         f"got {len(vector)}")
    if basis == "leech":
        ints = _leech_coords(vector)
        den = 1
    elif basis == "standard":
        ints, den = _clear_denominators(vector)
    else:
        raise ValueError("class_stack: basis must be 'standard' or 'leech'")

    depth = STACK_DEPTH if depth is None else int(depth)
    offset = STACK_OFFSET if offset is None else int(offset)
    if depth < 1:
        raise ValueError("class_stack: depth must be positive")

    shifted = [c + offset for c in ints]
    limit = 1 << depth
    if any(s < 0 or s >= limit for s in shifted):
        max_abs = max(abs(c) for c in ints)
        best_off, best_depth = derive_stack_parameters(max_abs)
        raise ValueError(
            f"class_stack: coordinate out of range at offset {offset}, "
            f"depth {depth} (cleared coordinates reach {max_abs}"
            + (f" after clearing denominator {den}" if den != 1 else "")
            + f"); the least admissible pair is offset {best_off}, "
              f"depth {best_depth}")

    planes: List[int] = []
    for k in range(depth):
        m = 0
        for i, s in enumerate(shifted):
            if (s >> k) & 1:
                m |= 1 << i
        planes.append(m)
    return DigitStack(planes=tuple(planes), depth=depth, offset=offset,
                      denominator=den, basis=basis)


def class_stack_fitted(vector: Carrier, basis: str = "standard") -> DigitStack:
    """:func:`class_stack` at the least admissible ``(offset, depth)`` pair."""
    if basis == "leech":
        ints = _leech_coords(vector)
    else:
        ints, _den = _clear_denominators(vector)
    max_abs = max((abs(c) for c in ints), default=0)
    offset, depth = derive_stack_parameters(max_abs)
    return class_stack(vector, depth=depth, offset=offset, basis=basis)


def class_stack_rebuild(stack: DigitStack) -> Tuple[Scalar, ...]:
    """The carrier a stack came from: the stack is a faithful encoding.

    Returns a tuple of ``int`` when the carrier was integral, and of
    :class:`~fractions.Fraction` when a denominator was cleared.  The
    round-trip identity

        ``class_stack_rebuild(class_stack(v)) == tuple(v)``

    holds exactly for every carrier in range, with no rounding at any step.
    """
    ints: List[int] = []
    for i in range(N):
        value = 0
        for k, m in enumerate(stack.planes):
            if (m >> i) & 1:
                value |= 1 << k
        ints.append(value - stack.offset)

    if stack.basis == "leech":
        from . import leech2
        point = leech2.from_coords(ints)
        return tuple(int(c) for c in point)
    if stack.denominator == 1:
        return tuple(ints)
    return tuple(Fraction(c, stack.denominator) for c in ints)


def stack_is_faithful(vector: Carrier,
                      depth: Optional[int] = None,
                      offset: Optional[int] = None,
                      basis: str = "standard") -> bool:
    """Whether ``rebuild(stack(v)) == v`` at the given parameters."""
    stack = class_stack(vector, depth=depth, offset=offset, basis=basis)
    rebuilt = class_stack_rebuild(stack)
    if len(rebuilt) != len(vector):
        return False
    return all(a == _as_fraction(b) for a, b in zip(rebuilt, vector))


def depth_report(vectors: Sequence[Carrier],
                 extra_depths: int = 4,
                 basis: str = "standard") -> Dict[str, object]:
    """Turn the stack depth from a constant into a measurement.

    Computes the coordinate range of the given carriers, the least admissible
    ``(offset, depth)`` pair, the depth the module's conventional offset
    forces, and then checks Proposition D1 empirically: the rebuild identity
    holds at every admissible pair tried, planes at or above the least
    admissible depth are identically zero at a fixed offset, and the planes
    below it do not move.
    """
    carriers = [tuple(v) for v in vectors]
    if basis == "leech":
        ranges = [max(abs(c) for c in _leech_coords(v)) for v in carriers]
        max_abs = max(ranges) if ranges else 0
    else:
        max_abs = coordinate_range(carriers)
    least_offset, least_depth = derive_stack_parameters(max_abs)
    _o, conventional_depth = derive_stack_parameters(max_abs, STACK_OFFSET)

    combos: List[Tuple[int, int]] = []
    for off in (least_offset, STACK_OFFSET, STACK_OFFSET * 2):
        _o2, d0 = derive_stack_parameters(max_abs, off)
        for d in range(d0, d0 + extra_depths + 1):
            combos.append((off, d))

    faithful: Dict[str, bool] = {}
    for off, d in combos:
        faithful[f"offset {off}, depth {d}"] = all(
            stack_is_faithful(v, d, off, basis) for v in carriers)

    base = {class_stack(v, conventional_depth, STACK_OFFSET, basis).planes
            for v in carriers}
    deeper_agrees = True
    deeper_zero = True
    for d in range(conventional_depth, conventional_depth + extra_depths + 1):
        for v in carriers:
            planes = class_stack(v, d, STACK_OFFSET, basis).planes
            if planes[:conventional_depth] not in base:
                deeper_agrees = False
            if any(planes[conventional_depth:]):
                deeper_zero = False

    return {
        "carriers": len(carriers),
        "basis": basis,
        "coordinate_range": max_abs,
        "least_offset": least_offset,
        "least_depth": least_depth,
        "module_offset": STACK_OFFSET,
        "module_depth": STACK_DEPTH,
        "depth_forced_by_the_module_offset": conventional_depth,
        "module_depth_is_admissible": STACK_DEPTH >= conventional_depth,
        "faithful": faithful,
        "faithful_everywhere": all(faithful.values()),
        "deeper_planes_are_zero": deeper_zero,
        "lower_planes_unchanged": deeper_agrees,
    }


# ===========================================================================
# 3.  FACETS
# ===========================================================================

def facet_masks() -> Dict[str, int]:
    """The named facets of the MOG geometry, as 24-bit masks.

    * ``brick0..2``  -- the three octads of the MOG trio;
    * ``col0..5``    -- the six tetrads of the MOG sextet;
    * ``row0..3``    -- the four rows of the 4x6 frame;
    * ``cube{b}.{axis}{value}`` -- the 18 faces of the three 2x2x2 cubes,
      four cells each.

    31 facets in total.  They overlap by design: a discrepancy is attributed
    to *every* facet that contains it, which is what makes the attribution a
    localisation rather than a partition.
    """
    out: Dict[str, int] = {}
    for b in range(3):
        out[f"brick{b}"] = mog.BRICKS[b]
    for c in range(6):
        out[f"col{c}"] = mog.COLUMNS[c]
    for r in range(4):
        out[f"row{r}"] = mog.row_mask(r)
    axis_name = ("x", "y", "z")
    for b in range(3):
        for axis in range(3):
            for value in (0, 1):
                m = 0
                for x in (0, 1):
                    for y in (0, 1):
                        for z in (0, 1):
                            if (x, y, z)[axis] == value:
                                m |= 1 << mog.coordinate_of_cube(b, x, y, z)
                out[f"cube{b}.{axis_name[axis]}{value}"] = m
    return out


#: Immutable facet table, built once at import.
FACETS: Dict[str, int] = facet_masks()


@dataclass(frozen=True)
class FacetReport:
    """Where a 24-bit mask lives, in facet coordinates."""

    mask: int
    weight: int
    parity: int
    facet_weights: Dict[str, int]
    facet_parities: Dict[str, int]
    touched_facets: Tuple[str, ...]

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "mask": f"0x{self.mask:06x}",
            "weight": self.weight,
            "parity": self.parity,
            "touched_facets": list(self.touched_facets),
            "facet_weights": {k: v for k, v in self.facet_weights.items()
                              if v},
        }


def plane_facets(mask: int) -> FacetReport:
    """Bitwise facet projection of a single 24-bit plane."""
    if not 0 <= mask < (1 << N):
        raise ValueError("plane_facets: mask must be a 24-bit integer")
    weights = {name: popcount(mask & fm) for name, fm in FACETS.items()}
    parities = {name: w & 1 for name, w in weights.items()}
    touched = tuple(name for name, w in weights.items() if w)
    return FacetReport(mask=mask, weight=popcount(mask),
                       parity=popcount(mask) & 1,
                       facet_weights=weights, facet_parities=parities,
                       touched_facets=touched)


def facet_projection(stack: DigitStack) -> List[FacetReport]:
    """Facet projection of every plane of a stack, plane 0 first."""
    return [plane_facets(p) for p in stack.planes]


@dataclass(frozen=True)
class EquationVerdict:
    """The outcome of deciding a vector equation across the digit planes."""

    holds: bool
    depth: int
    basis: str
    mog_geometric: bool
    failing_planes: Tuple[int, ...]
    first_failing_plane: Optional[int]
    difference_masks: Dict[int, int]
    facet_reports: Dict[int, FacetReport]
    blamed_facets: Tuple[str, ...]
    note: str

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "holds": self.holds,
            "depth": self.depth,
            "basis": self.basis,
            "mog_geometric": self.mog_geometric,
            "failing_planes": list(self.failing_planes),
            "first_failing_plane": self.first_failing_plane,
            "difference_masks": {str(k): f"0x{v:06x}"
                                 for k, v in self.difference_masks.items()},
            "facet_reports": {str(k): r.as_dict()
                              for k, r in self.facet_reports.items()},
            "blamed_facets": list(self.blamed_facets),
            "note": self.note,
        }


def failing_facets(lhs: DigitStack, rhs: DigitStack) -> EquationVerdict:
    """Compare two stacks plane by plane and attribute every discrepancy.

    For each plane where the two masks differ, the XOR of the masks is the
    *difference mask*, and the facets containing at least one of its bits are
    blamed.  A holding equation returns ``holds=True`` with empty blame.

    Raises
    ------
    ValueError
        If the two stacks were taken at different depths, offsets,
        denominators or bases -- comparing them bitwise would be meaningless.
    """
    if lhs.depth != rhs.depth:
        raise ValueError("failing_facets: stacks have different depths")
    if lhs.offset != rhs.offset:
        raise ValueError("failing_facets: stacks have different offsets")
    if lhs.denominator != rhs.denominator:
        raise ValueError(
            f"failing_facets: stacks cleared different denominators "
            f"({lhs.denominator} vs {rhs.denominator}); re-stack both sides "
            f"over a common denominator before comparing")
    if lhs.basis != rhs.basis:
        raise ValueError("failing_facets: stacks are in different bases")

    diffs: Dict[int, int] = {}
    reports: Dict[int, FacetReport] = {}
    blamed: List[str] = []
    for k in range(lhs.depth):
        d = lhs.planes[k] ^ rhs.planes[k]
        if d:
            diffs[k] = d
            rep = plane_facets(d)
            reports[k] = rep
            for name in rep.touched_facets:
                if name not in blamed:
                    blamed.append(name)

    failing = tuple(sorted(diffs))
    if lhs.basis == "standard":
        note = ("facet names index MOG cells of the 4x6 frame")
    else:
        note = ("basis='leech': facet names index Leech BASIS vectors, not "
                "MOG cells; the partition is combinatorially valid but is not "
                "MOG geometry")
    return EquationVerdict(
        holds=not diffs,
        depth=lhs.depth,
        basis=lhs.basis,
        mog_geometric=lhs.basis == "standard",
        failing_planes=failing,
        first_failing_plane=failing[0] if failing else None,
        difference_masks=diffs,
        facet_reports=reports,
        blamed_facets=tuple(blamed),
        note=note,
    )


def verify_equation(lhs: Carrier, rhs: Carrier,
                    depth: Optional[int] = None,
                    offset: Optional[int] = None,
                    basis: str = "standard") -> EquationVerdict:
    """Decide ``lhs == rhs`` across all digit planes, with attribution.

    Both sides are stacked over a **common denominator** so that the bitwise
    comparison is meaningful, then compared plane by plane.  The verdict is
    exact: ``holds`` is true if and only if the two carriers are equal as
    rational vectors, because the stack is a faithful encoding.
    """
    if len(lhs) != N or len(rhs) != N:
        raise ValueError(f"verify_equation: both sides need {N} coordinates")
    if basis == "standard":
        _l, den_l = _clear_denominators(lhs)
        _r, den_r = _clear_denominators(rhs)
        den = den_l * den_r // gcd(den_l, den_r)
        left: Carrier = tuple(_as_fraction(v) * den for v in lhs)
        right: Carrier = tuple(_as_fraction(v) * den for v in rhs)
        ls = class_stack(left, depth=depth, offset=offset, basis="standard")
        rs = class_stack(right, depth=depth, offset=offset, basis="standard")
        # both sides were pre-scaled, so both carry denominator 1
    else:
        ls = class_stack(lhs, depth=depth, offset=offset, basis=basis)
        rs = class_stack(rhs, depth=depth, offset=offset, basis=basis)
    return failing_facets(ls, rs)
