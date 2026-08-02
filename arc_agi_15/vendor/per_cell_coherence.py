"""
per_cell_coherence.py — per-cell NRCI / coherence map
======================================================

The user's insight: "per-cell AND per-grid gives us the full picture,
we need the per-cell ones wired in so their information is meaningful".

This module computes NRCI for EACH CELL of a grid, not just the whole
grid.  This gives a coherence map: which cells are "real" (high NRCI)
and which are "noise" (low NRCI).

The coherence map is wired into MOG layers at both grid and bit level:

  - GRID LEVEL: the whole grid has one NRCI (already computed)
  - CELL LEVEL: each cell has its own NRCI (new)
  - BIT LEVEL: each bit of each cell has its own NRCI (via MOG meaning)

Together these give the GLM a 3-level coherence picture.

What the coherence map tells us
-------------------------------

A cell with high NRCI is "coherent" — it fits the Golay structure well.
A cell with low NRCI is "incoherent" — it's an outlier, possibly noise
or a transformation boundary.

For ARC tasks:
  - Cells that CHANGE between input and output often have low input NRCI
    (they're "ready to change") and high output NRCI (they've "settled").
  - The coherence delta (output_NRCI - input_NRCI) per cell tells us
    where the transformation "happened".

This is information the per-grid NRCI cannot provide.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from fractions import Fraction
from collections import defaultdict
import sys, os, math

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_THIS_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask
from ubp_unified_v5 import GOLAY_ENGINE, ontological_position_to_vector
from generative.hex_learner import address_cell, address_grid, HexCell


# ══════════════════════════════════════════════════════════════════════════════
# Per-cell NRCI
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class CellCoherence:
    """The coherence of a single cell.

    Fields:
      - nrci: the cell's NRCI (Fraction, 0-1)
      - nrci_float: float version
      - coherence_label: SUBLIMINAL / EMERGING / COHERENT / MANIFESTED
      - hamming_weight: bits set in the snapped codeword
      - is_train_input: was this cell's address seen in train input?
      - is_train_output: was this cell's address seen in train output?
      - coherence_delta: change in NRCI from input to output (if known)
    """
    nrci: Fraction
    nrci_float: float
    coherence_label: str
    hamming_weight: int
    is_train_input: bool = False
    is_train_output: bool = False
    coherence_delta: float = 0.0


def cell_nrci(hex_cell: HexCell) -> CellCoherence:
    """Compute the NRCI of a single cell.

    NRCI = 10 / (10 + symmetry_tax)
    symmetry_tax = hamming_weight * Y + norm_squared / 8

    where Y = π / (π² + 2) is the observer constant.
    """
    from ubp_unified_v5 import UBPSourceCodeParticlePhysics
    pp = UBPSourceCodeParticlePhysics()
    Y = pp.Y

    # Snap to Golay codeword
    snapped, _ = GOLAY_ENGINE.snap_to_codeword(hex_cell.vector)
    hw = sum(snapped)
    ns = sum(x * x for x in snapped)
    tax = Fraction(hw) * Y + Fraction(ns, 8)
    nrci = Fraction(10) / (Fraction(10) + tax)
    nrci_f = float(nrci)

    # Classify coherence
    if nrci_f >= 0.7:
        label = "MANIFESTED"
    elif nrci_f >= 0.5:
        label = "COHERENT"
    elif nrci_f >= 0.3:
        label = "EMERGING"
    else:
        label = "SUBLIMINAL"

    return CellCoherence(
        nrci=nrci, nrci_float=nrci_f,
        coherence_label=label, hamming_weight=hw,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Grid coherence map
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class GridCoherenceMap:
    """Per-cell coherence for an entire grid."""
    grid: Grid
    cells: List[List[CellCoherence]] = field(default_factory=list)

    def mean_nrci(self) -> float:
        """Mean NRCI across all cells (≈ per-grid NRCI)."""
        all_cells = [c for row in self.cells for c in row]
        if not all_cells: return 0.0
        return sum(c.nrci_float for c in all_cells) / len(all_cells)

    def min_nrci(self) -> float:
        all_cells = [c for row in self.cells for c in row]
        if not all_cells: return 0.0
        return min(c.nrci_float for c in all_cells)

    def max_nrci(self) -> float:
        all_cells = [c for row in self.cells for c in row]
        if not all_cells: return 0.0
        return max(c.nrci_float for c in all_cells)

    def coherence_distribution(self) -> Dict[str, int]:
        """Distribution of coherence labels."""
        dist = defaultdict(int)
        for row in self.cells:
            for c in row:
                dist[c.coherence_label] += 1
        return dict(dist)

    def low_coherence_cells(self, threshold: float = 0.5) -> List[Tuple[int, int]]:
        """Positions of cells with NRCI below threshold — the 'noise' cells."""
        return [(r, c) for r, row in enumerate(self.cells)
                for c, cell in enumerate(row) if cell.nrci_float < threshold]

    def high_coherence_cells(self, threshold: float = 0.7) -> List[Tuple[int, int]]:
        """Positions of cells with NRCI >= threshold — the 'manifested' cells."""
        return [(r, c) for r, row in enumerate(self.cells)
                for c, cell in enumerate(row) if cell.nrci_float >= threshold]

    def summary(self) -> str:
        lines = [
            f"GridCoherenceMap ({self.grid.shape[0]}x{self.grid.shape[1]}):",
            f"  mean NRCI: {self.mean_nrci():.4f}",
            f"  min: {self.min_nrci():.4f}, max: {self.max_nrci():.4f}",
            f"  distribution: {self.coherence_distribution()}",
            f"  low-coherence cells: {len(self.low_coherence_cells())}",
            f"  high-coherence cells: {len(self.high_coherence_cells())}",
        ]
        return "\n".join(lines)


def compute_grid_coherence(grid: Grid) -> GridCoherenceMap:
    """Compute per-cell coherence for an entire grid."""
    addrs = address_grid(grid)
    cells = [[cell_nrci(c) for c in row] for row in addrs]
    return GridCoherenceMap(grid=grid, cells=cells)


# ══════════════════════════════════════════════════════════════════════════════
# Coherence delta — where did the transformation happen?
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class CoherenceDeltaMap:
    """Per-cell coherence change from input to output.

    For each cell, computes output_nrci - input_nrci.
    Positive delta = the cell became MORE coherent (settled).
    Negative delta = the cell became LESS coherent (destabilised).
    Near-zero delta = the cell was unchanged.

    This pinpoints WHERE the transformation "happened".
    """
    deltas: List[List[float]] = field(default_factory=list)

    def cells_changed(self, threshold: float = 0.01) -> List[Tuple[int, int]]:
        """Positions where |delta| >= threshold — the cells that changed."""
        return [(r, c) for r, row in enumerate(self.deltas)
                for c, d in enumerate(row) if abs(d) >= threshold]

    def cells_stabilised(self, threshold: float = 0.1) -> List[Tuple[int, int]]:
        """Positions where delta >= threshold — cells that became more coherent."""
        return [(r, c) for r, row in enumerate(self.deltas)
                for c, d in enumerate(row) if d >= threshold]

    def cells_destabilised(self, threshold: float = 0.1) -> List[Tuple[int, int]]:
        """Positions where delta <= -threshold — cells that became less coherent."""
        return [(r, c) for r, row in enumerate(self.deltas)
                for c, d in enumerate(row) if d <= -threshold]


def compute_coherence_delta(grid_in: Grid, grid_out: Grid) -> Optional[CoherenceDeltaMap]:
    """Compute the per-cell coherence delta between input and output."""
    if grid_in.shape != grid_out.shape:
        return None
    in_map = compute_grid_coherence(grid_in)
    out_map = compute_grid_coherence(grid_out)
    deltas = [[out_map.cells[r][c].nrci_float - in_map.cells[r][c].nrci_float
               for c in range(grid_in.width)] for r in range(grid_in.height)]
    return CoherenceDeltaMap(deltas=deltas)


# ══════════════════════════════════════════════════════════════════════════════
# Self-test
# ══════════════════════════════════════════════════════════════════════════════

def _self_test():
    print("Per-Cell Coherence self-test")
    print("=" * 60)

    grid = Grid([
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
    ])
    cmap = compute_grid_coherence(grid)
    print(cmap.summary())

    print("\nPer-cell NRCI:")
    for r in range(grid.height):
        for c in range(grid.width):
            cell = cmap.cells[r][c]
            print(f"  ({r},{c}) colour={grid.cells[r][c]}: NRCI={cell.nrci_float:.4f} [{cell.coherence_label}] hw={cell.hamming_weight}")

    print("\n[Coherence delta] input → output (recolour 0→9)")
    out = Grid([
        [9, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
    ])
    delta = compute_coherence_delta(grid, out)
    if delta:
        print(f"  cells changed: {len(delta.cells_changed())}")
        print(f"  cells stabilised: {len(delta.cells_stabilised())}")
        print(f"  cells destabilised: {len(delta.cells_destabilised())}")
        for r in range(grid.height):
            for c in range(grid.width):
                d = delta.deltas[r][c]
                if abs(d) > 0.01:
                    print(f"  ({r},{c}): delta={d:+.4f}")

    print("\n" + "=" * 60)
    print("Self-test complete.")


if __name__ == "__main__":
    _self_test()
