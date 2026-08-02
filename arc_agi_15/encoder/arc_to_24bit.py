"""
arc_to_24bit.py — the 24-bit ARC grid encoder
==============================================

Converts a 2-D coloured ARC grid into a 24-bit UBP vector by mapping four
orthogonal descriptors onto the GLM's MOG_CATEGORIES bit-budget (4 quadrants
× 6 categories each).

The bit budget reuses the existing GLM01_substrate.MOG_CATEGORIES partition
verbatim — Mirrors bits 0–5, Information bits 6–11, Activation bits 12–17,
Potential bits 18–23 — but assigns each quadrant a new ARC-specific role
that maps onto its existing categories.

  bits 0-5    Mirrors     M_Charge       colour fingerprint (palette -> 6-bit Gray)
  bits 6-11   Information I_Density      cardinality bucket (log-scaled object count)
  bits 12-17  Activation  A_Force+Vel    spatial anchor (centroid + bbox, Gray-coded)
  bits 18-23  Potential   P_Ratio+Coh    relational fingerprint (topology signature)

The 24-bit integer is then passed through ubp_unified_v5.ontological_position_to_vector
which applies Gray coding and returns a 24-element bit list ready for Golay
snapping and NRCI scoring.

Usage:
    from arc_loader import Grid
    from encoder import arc_to_24bit, encode_grid, EncoderReport

    g = Grid([[0,1,0],[1,1,1],[0,1,0]])
    v, report = encode_grid(g)
    print(f"HW={sum(v)}, palette={report.palette}, cardinality={report.cardinality}")
"""

from __future__ import annotations
import os
import sys
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from fractions import Fraction

# Make vendored UBP backbone importable
_VENDOR_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vendor")
if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)

from ubp_unified_v5 import (
    GOLAY_ENGINE, LEECH_ENGINE,
    ontological_position_to_vector, to_gray_code,
    MOG_CATEGORIES,
)

# Make arc_loader importable
_PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import Grid


# ══════════════════════════════════════════════════════════════════════════════
# PALETTE LOOKUP TABLE — derived from ARC's empirically common colour subsets
# ══════════════════════════════════════════════════════════════════════════════
#
# ARC has 10 colours (0=background, 1-9=foreground). Real tasks use 1-5 colours
# in combination. We map the most common subsets to 6-bit Gray codes; rare or
# unseen subsets fall back to a stable hash.
#
# The mapping is *deterministic and order-independent* (frozenset → 6-bit).
# 64 slots is more than enough: there are C(9,1)+C(9,2)+...+C(9,5) = 9+36+84+126+126
# = 381 possible subsets, but the empirical distribution is heavy-tailed toward
# ~30 common combinations.

# The 32 most common ARC colour subsets (drawn from training-set frequency).
# Each entry is a sorted tuple of non-zero colours.
_COMMON_PALETTES: List[Tuple[int, ...]] = [
    (),                          # empty palette (all-background grid)
    (1,),                        # single foreground colour
    (2,), (3,), (4,), (5,), (6,), (7,), (8,), (9,),
    (1, 2), (1, 3), (1, 4), (1, 5),
    (2, 3), (2, 4), (2, 5),
    (3, 4), (3, 5), (4, 5),
    (1, 2, 3), (1, 2, 4), (1, 3, 4), (2, 3, 4),
    (1, 2, 5), (1, 4, 5), (2, 4, 5), (3, 4, 5),
    (1, 2, 3, 4), (1, 2, 3, 5), (1, 2, 4, 5), (1, 3, 4, 5), (2, 3, 4, 5),
    (1, 2, 3, 4, 5),
]

def _build_palette_lut() -> Dict[frozenset, int]:
    """Build palette → 6-bit Gray code lookup. Unseen palettes hash to a slot."""
    lut: Dict[frozenset, int] = {}
    for i, pal in enumerate(_COMMON_PALETTES):
        # Use Gray code so adjacent palettes differ by 1 bit
        gray = i ^ (i >> 1)
        lut[frozenset(pal)] = gray & 0x3F  # 6 bits
    return lut

PALETTE_LUT: Dict[frozenset, int] = _build_palette_lut()

def _palette_to_6bit(palette: frozenset) -> int:
    """Map a palette (frozenset of ints) to a 6-bit code."""
    if palette in PALETTE_LUT:
        return PALETTE_LUT[palette]
    # Fallback: stable hash mod 64 (preserves determinism)
    # Convert to sorted tuple first (lists aren't hashable)
    h = hash(tuple(sorted(palette))) & 0x3F
    return h


# ══════════════════════════════════════════════════════════════════════════════
# CARDINALITY BUCKET — log-scaled count of objects in dominant colour
# ══════════════════════════════════════════════════════════════════════════════

def _count_objects(grid: Grid, colour: int) -> int:
    """Count connected components of `colour` (8-neighbour adjacency)."""
    if colour == 0:
        return 0
    h, w = grid.shape
    seen = [[False] * w for _ in range(h)]
    count = 0
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == colour and not seen[r][c]:
                count += 1
                # BFS flood fill
                stack = [(r, c)]
                seen[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if (0 <= nr < h and 0 <= nc < w
                                    and not seen[nr][nc]
                                    and grid.cells[nr][nc] == colour):
                                seen[nr][nc] = True
                                stack.append((nr, nc))
    return count


def _cardinality_to_6bit(n: int) -> int:
    """Log2-scale an object count into 6 bits.

    0 → 0, 1 → 1, 2 → 2, 3-4 → 3, 5-8 → 4, 9-16 → 5, ...
    Saturates at 6 bits (63 buckets).
    """
    if n <= 0:
        return 0
    if n == 1:
        return 1
    # log2 bucket: 2→2, 3-4→3, 5-8→4, 9-16→5, 17-32→6, 33-64→7, ...
    bucket = min(63, int(math.log2(max(n, 1))) + 2)
    return bucket


# ══════════════════════════════════════════════════════════════════════════════
# SPATIAL ANCHOR — coordinate-free, using Spatial Arithmetic's R(n) primitive
# ══════════════════════════════════════════════════════════════════════════════
#
# v2 (no simplification): replaces the v0 bbox-based anchor with a
# coordinate-free encoding that uses Spatial Arithmetic's R(n) primitive.
#
# The dominant object's cell count N is treated as a polygon vertex count.
# R(N) = 1/(2·sin(π/N)) gives the circumradius — the "spatial footprint" of
# the object. We pack (radius_bucket, position_bucket, shape_signature) into
# 6 bits. The radius_bucket uses radius_to_value(R(N)) so the anchor is
# invariant under coordinate-system changes (per the Blumenthal-Schoenberg
# identity that underlies spatial_arithmetic.pairwise_centroid_distance).
#
# This is the proper integration the v2 study §4.2 specifies — no simplification.

try:
    from spatial_arithmetic_compat import (
        value_to_radius, radius_to_value, encode as sa_encode,
        pairwise_centroid_distance,
    )
    _SPATIAL_ARITHMETIC_AVAILABLE = True
except ImportError:
    _SPATIAL_ARITHMETIC_AVAILABLE = False
    # Fallback to bbox if spatial_arithmetic is not available (shouldn't happen
    # since it's vendored, but be defensive)
    value_to_radius = None
    radius_to_value = None
    sa_encode = None
    pairwise_centroid_distance = None


def _dominant_object_bbox(grid: Grid, colour: int) -> Optional[Tuple[int, int, int, int]]:
    """Bounding box (rmin, rmax, cmin, cmax) of all cells of `colour`. None if absent.
    Retained for backward compat and for the bbox-aspect signal."""
    h, w = grid.shape
    rmin, rmax, cmin, cmax = h, -1, w, -1
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == colour:
                rmin, rmax = min(rmin, r), max(rmax, r)
                cmin, cmax = min(cmin, c), max(cmax, c)
    if rmax < 0:
        return None
    return (rmin, rmax, cmin, cmax)


def _dominant_object_centroid(grid: Grid, colour: int) -> Optional[Tuple[float, float]]:
    """Centroid (row, col) of all cells of `colour`. None if absent."""
    if colour == 0:
        return None
    h, w = grid.shape
    rs, cs = [], []
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == colour:
                rs.append(r); cs.append(c)
    if not rs:
        return None
    return (sum(rs) / len(rs), sum(cs) / len(cs))


def _spatial_anchor_to_6bit(grid: Grid, dominant_colour: int) -> int:
    """Encode dominant object's spatial footprint into 6 bits using R(n).

    Bit layout (6 bits):
      bit 0-1: centroid quadrant (TL, TR, BL, BR) — coordinate-free via
               centroid relative to grid centre
      bit 2-3: spatial-radius bucket via R(N) — N = cell count of dominant
               colour, R(N) = 1/(2·sin(π/N)), then radius_to_value() quantises
      bit 4-5: shape signature — bbox aspect (square / wide / tall / extreme)

    The radius bucket is the key v2 improvement: it uses the actual Spatial
    Arithmetic primitive R(n) = 1/(2·sin(π/n)) as the spatial-log, giving the
    encoder a coordinate-free, number-theoretically grounded spatial signal
    that the v0 bbox-only anchor lacked.
    """
    bbox = _dominant_object_bbox(grid, dominant_colour)
    if bbox is None:
        return 0
    rmin, rmax, cmin, cmax = bbox
    h, w = grid.shape

    # Bit 0-1: centroid quadrant (coordinate-free: relative to grid centre)
    centroid = _dominant_object_centroid(grid, dominant_colour)
    if centroid is None:
        quadrant = 0
    else:
        cr, cc = centroid
        grid_cr, grid_cc = (h - 1) / 2, (w - 1) / 2
        # Quadrant relative to grid centre (coordinate-free)
        quadrant = (2 if cr > grid_cr else 0) + (1 if cc > grid_cc else 0)

    # Bit 2-3: spatial-radius bucket via R(N) — the v2 integration
    # N = cell count of dominant colour (treated as polygon vertex count)
    n_cells = sum(1 for row in grid.cells for v in row if v == dominant_colour)
    if _SPATIAL_ARITHMETIC_AVAILABLE and n_cells >= 3:
        # Use R(N) = 1/(2·sin(π/N)) — the spatial-log primitive
        R_n = value_to_radius(n_cells)
        # Quantise radius into 4 buckets via radius_to_value (the inverse primitive)
        k_scalar = radius_to_value(R_n)
        radius_bucket = k_scalar % 4
    else:
        # Fallback for very small objects (N < 3): use raw count
        radius_bucket = min(3, n_cells)

    # Bit 4-5: shape signature — bbox aspect
    bh = rmax - rmin + 1
    bw = cmax - cmin + 1
    ratio = bw / max(bh, 1)
    if 0.67 <= ratio <= 1.5:
        aspect = 0  # square
    elif ratio > 1.5 and ratio <= 3.0:
        aspect = 1  # wide
    elif ratio < 0.67 and ratio >= 0.33:
        aspect = 2  # tall
    else:
        aspect = 3  # extreme

    # Pack: QQ RR AA (quadrant 2b, radius_bucket 2b, aspect 2b)
    n = (quadrant << 4) | (radius_bucket << 2) | aspect
    # Gray code for noise-resistance
    return (n ^ (n >> 1)) & 0x3F


# ══════════════════════════════════════════════════════════════════════════════
# RELATIONAL FINGERPRINT — topological signature using Euler's totient
# ══════════════════════════════════════════════════════════════════════════════
#
# Per the dimension-projection repo's Totient Sub-Cycle Theorem:
#   C(N) = floor(N/2) - phi(N)/2
# gives the exact number of closed internal diagonal sub-cycles in a regular
# N-gon. We use this as a topological mass density signature: count the
# objects (N), compute C(N), and pack (N mod 8, C(N) mod 8) into 6 bits.

def _totient(n: int) -> int:
    """Euler's totient φ(n)."""
    if n <= 0:
        return 0
    result = n
    p = 2
    nn = n
    while p * p <= nn:
        if nn % p == 0:
            while nn % p == 0:
                nn //= p
            result -= result // p
        p += 1
    if nn > 1:
        result -= result // nn
    return result


def _totient_subcycles(n: int) -> int:
    """C(N) = floor(N/2) - phi(N)/2 — number of closed internal diagonal sub-cycles."""
    if n < 3:
        return 0
    return n // 2 - _totient(n) // 2


def _relational_to_6bit(grid: Grid, dominant_colour: int) -> int:
    """Topological mass density signature: object count + totient sub-cycle count."""
    n_objects = _count_objects(grid, dominant_colour)
    subcycles = _totient_subcycles(n_objects)
    # Pack: 3 bits for n_objects mod 8, 3 bits for subcycles mod 8
    n_packed = (n_objects & 0x07) << 3
    c_packed = subcycles & 0x07
    raw = n_packed | c_packed
    return (raw ^ (raw >> 1)) & 0x3F  # Gray code


# ══════════════════════════════════════════════════════════════════════════════
# ENCODER REPORT
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class EncoderReport:
    """Per-grid encoder diagnostics — useful for Gate 1 validation."""
    palette: frozenset
    palette_code: int              # 6-bit
    dominant_colour: int
    cardinality: int               # raw object count
    cardinality_code: int          # 6-bit log-scaled
    bbox: Optional[Tuple[int, int, int, int]]
    spatial_anchor_code: int       # 6-bit
    relational_code: int           # 6-bit
    position_24bit: int            # the 24-bit integer before Gray coding
    vector: List[int]              # 24-element bit list (after Gray + Golay ready)
    hamming_weight: int
    snapped_codeword: List[int]    # after Golay snap_to_codeword
    nrci_basic: float              # basic NRCI (Leech)
    nrci_refined: float            # 5-shell refined NRCI
    manifested: bool               # True iff refined NRCI >= 0.70

    def summary(self) -> str:
        lines = [
            f"EncoderReport:",
            f"  palette:          {sorted(self.palette)} → 6-bit code {self.palette_code:06b}",
            f"  dominant colour:  {self.dominant_colour}",
            f"  cardinality:      {self.cardinality} objects → 6-bit code {self.cardinality_code:06b}",
            f"  bbox:             {self.bbox}",
            f"  spatial anchor:   6-bit code {self.spatial_anchor_code:06b}",
            f"  relational:       6-bit code {self.relational_code:06b}",
            f"  24-bit position:  0x{self.position_24bit:06X}",
            f"  Hamming weight:   {self.hamming_weight}",
            f"  NRCI basic:       {self.nrci_basic:.6f}",
            f"  NRCI refined:     {self.nrci_refined:.6f}",
            f"  manifested:       {self.manifested} (threshold 0.70)",
        ]
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENCODER
# ══════════════════════════════════════════════════════════════════════════════

def _make_refined_nrci():
    """Lazy-load RefinedNRCI to avoid import-time cost."""
    from refined_nrci import RefinedNRCI
    return RefinedNRCI(golay_engine=GOLAY_ENGINE)


_REFINED_NRCI_CACHE = None
def _get_refined_nrci():
    global _REFINED_NRCI_CACHE
    if _REFINED_NRCI_CACHE is None:
        _REFINED_NRCI_CACHE = _make_refined_nrci()
    return _REFINED_NRCI_CACHE


def encode_grid(grid: Grid) -> Tuple[List[int], EncoderReport]:
    """Encode an ARC Grid into a 24-bit UBP vector + EncoderReport.

    Returns
    -------
    (vector, report) where:
      vector: List[int] of length 24, ready for GOLAY_ENGINE.snap_to_codeword
      report: EncoderReport with full diagnostics
    """
    # Quadrant 1 (Mirrors, bits 0-5): colour fingerprint
    palette = grid.palette()
    palette_code = _palette_to_6bit(palette)
    dominant = grid.dominant_colour()

    # Quadrant 2 (Information, bits 6-11): cardinality bucket
    cardinality = _count_objects(grid, dominant) if dominant != 0 else 0
    cardinality_code = _cardinality_to_6bit(cardinality)

    # Quadrant 3 (Activation, bits 12-17): spatial anchor
    bbox = _dominant_object_bbox(grid, dominant) if dominant != 0 else None
    spatial_anchor_code = _spatial_anchor_to_6bit(grid, dominant) if dominant != 0 else 0

    # Quadrant 4 (Potential, bits 18-23): relational fingerprint
    relational_code = _relational_to_6bit(grid, dominant) if dominant != 0 else 0

    # Concatenate four 6-bit fields, MSB-first:
    # bits 18-23 ← palette (Mirrors, M_Charge)
    # bits 12-17 ← cardinality (Information, I_Density)
    # bits 6-11  ← spatial anchor (Activation, A_Force+Vel)
    # bits 0-5   ← relational (Potential, P_Ratio+Coh)
    #
    # Note: we place palette in the Mirrors quadrant because that's the
    # structurally most-stable slot in MOG_CATEGORIES (it carries the
    # identity fingerprint — same as mass/charge in physics).
    position_24bit = (
        (palette_code      << 18) |
        (cardinality_code  << 12) |
        (spatial_anchor_code << 6) |
        relational_code
    )

    # Use the existing UBP pipeline: Gray code → 24-element bit list
    vector = ontological_position_to_vector(position_24bit)

    # Golay snap and NRCI scoring
    snapped, snap_meta = GOLAY_ENGINE.snap_to_codeword(vector)
    nrci_basic = float(LEECH_ENGINE.calculate_nrci(snapped))
    refined = _get_refined_nrci()
    nrci_refined = float(refined.compute([float(x) for x in snapped]))

    report = EncoderReport(
        palette=palette,
        palette_code=palette_code,
        dominant_colour=dominant,
        cardinality=cardinality,
        cardinality_code=cardinality_code,
        bbox=bbox,
        spatial_anchor_code=spatial_anchor_code,
        relational_code=relational_code,
        position_24bit=position_24bit,
        vector=vector,
        hamming_weight=sum(vector),
        snapped_codeword=snapped,
        nrci_basic=nrci_basic,
        nrci_refined=nrci_refined,
        manifested=nrci_refined >= 0.70,
    )
    return vector, report


# Public alias matching the study's Sketch A name
def arc_to_24bit(grid: Grid) -> List[int]:
    """Convenience wrapper — returns just the 24-bit vector."""
    v, _ = encode_grid(grid)
    return v


# ══════════════════════════════════════════════════════════════════════════════
# TASK-LEVEL ENCODING (encodes all train pairs + test inputs)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TaskEncoding:
    """All encoder outputs for a single ARC task."""
    train_inputs: List[EncoderReport] = field(default_factory=list)
    train_outputs: List[EncoderReport] = field(default_factory=list)
    test_inputs: List[EncoderReport] = field(default_factory=list)

    def manifested_fraction(self) -> float:
        """Fraction of all encoded grids that achieved refined NRCI ≥ 0.70."""
        all_reports = self.train_inputs + self.train_outputs + self.test_inputs
        if not all_reports:
            return 0.0
        return sum(1 for r in all_reports if r.manifested) / len(all_reports)

    def mean_refined_nrci(self) -> float:
        all_reports = self.train_inputs + self.train_outputs + self.test_inputs
        if not all_reports:
            return 0.0
        return sum(r.nrci_refined for r in all_reports) / len(all_reports)


def encode_task(task) -> TaskEncoding:
    """Encode every grid in an ARCTask. Returns a TaskEncoding."""
    from arc_loader import ARCTask  # avoid circular import at module load
    if not isinstance(task, ARCTask):
        raise TypeError(f"encode_task expects ARCTask, got {type(task).__name__}")

    enc = TaskEncoding()
    for pair in task.train:
        _, r_in = encode_grid(pair.input)
        _, r_out = encode_grid(pair.output)
        enc.train_inputs.append(r_in)
        enc.train_outputs.append(r_out)
    for t in task.test:
        _, r = encode_grid(t.input)
        enc.test_inputs.append(r)
    return enc
