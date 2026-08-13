"""
Layer 0 — BODY: the 24D Leech Lattice.

The lattice itself. No systems, no measurements. Just the geometry.
This is a thin wrapper over the existing LeechLatticeEngine — the substrate
is already Lean-verified and uses exact Fractions.

Constants (from the user's universe table):
  0     = perfect space (no active coordinate)
  Δ = 2 = primitive difference (numerator of the read operator)
  Z★=1/8= capacity / zone-share (cost of occupying a permitted zone)
  Π = π = loop-check (numeric, argument of the read operator)
  B = 10 = coherence budget
  Y = 1/(π + 2/π) ≈ 0.2646754 = the read quantum
  Q = Y + 1/8 ≈ 0.3896754 = activation quantum

TAX formula:
  TAX(v) = HW(v)·Y + ‖v‖²/8
  NRCI(v) = B / (B + TAX(v))

Coherence regimes (4 bands of NRCI):
  We don't hard-code band names here — the regime is computed from NRCI
  and exposed as a label by the Measure layer (L3). The body only holds
  the constants and the lattice engine.
"""

from __future__ import annotations
from fractions import Fraction
from typing import List, Dict, Any, Tuple
from pathlib import Path

from .substrate import GOLAY_ENGINE, LEECH_ENGINE, SUBSTRATE


# ══════════════════════════════════════════════════════════════════════════════
# THE CONSTANTS (exact Fractions — no float approximation)
# ══════════════════════════════════════════════════════════════════════════════

# Perfect space / zero vector
ZERO = 0

# Primitive difference (numerator of the read operator)
DELTA = Fraction(2, 1)

# Capacity / zone-share (cost of occupying a permitted zone)
Z_STAR = Fraction(1, 8)

# Coherence budget
B = Fraction(10, 1)

# Loop-check (numeric) — π as exact Fraction (50-term continued fraction)
PI = SUBSTRATE.get_constants(50)["PI"]

# The read quantum Y = 1/(π + 2/π)
Y = SUBSTRATE.get_constants(50)["Y"]

# Activation quantum Q = Y + 1/8
Q = Y + Z_STAR

# Float convenience (for display only — all internal math uses Fractions)
Y_FLOAT = float(Y)
Q_FLOAT = float(Q)
PI_FLOAT = float(PI)


class Body:
    """The 24D Leech lattice body.

    Holds the lattice engine and the constants. Does NOT store concepts,
    edges, or measurements — those live in Layer 4 (body_state).

    The body is the geometry. Everything else reads it.
    """

    def __init__(self):
        self.golay = GOLAY_ENGINE
        self.leech = LEECH_ENGINE
        self.substrate = SUBSTRATE
        # Expose constants as instance attributes for convenience
        self.Y = Y
        self.Q = Q
        self.B = B
        self.Z_STAR = Z_STAR
        self.DELTA = DELTA
        self.PI = PI

    # ── coordinate space ──────────────────────────────────────────────────
    @property
    def dimension(self) -> int:
        """The body has 24 coordinates."""
        return 24

    @property
    def grid_shape(self) -> Tuple[int, int]:
        """The MOG grid is 4 rows × 6 columns = 24 coordinates."""
        return (4, 6)

    # ── fundamental operators (delegate to the lattice engine) ────────────
    def hamming_weight(self, v: List[int]) -> int:
        """HW(v) — the number of nonzero coordinates."""
        return sum(1 for x in v if x != 0)

    def norm_squared(self, v: List[int]) -> int:
        """‖v‖² — the sum of squares of coordinates."""
        return sum(x * x for x in v)

    def hamming_distance(self, u: List[int], v: List[int]) -> int:
        """d(u,v) — the number of differing coordinates."""
        return sum(1 for a, b in zip(u, v) if a != b)

    # ── the TAX formula (Layer 3 uses this; defined here because it's a ───
    #    property of the body, not of any particular measurement) ─────────
    def tax(self, v: List[int]) -> Fraction:
        """TAX(v) = HW(v)·Y + ‖v‖²/8

        This is the ONE tax formula. Every measurement reads it.
        """
        hw = self.hamming_weight(v)
        ns = self.norm_squared(v)
        return Fraction(hw) * Y + Fraction(ns) * Z_STAR

    def nrci(self, v: List[int]) -> Fraction:
        """NRCI(v) = B / (B + TAX(v))

        The ONE coherence index. Every measurement reads it.
        """
        return B / (B + self.tax(v))

    # ── syndrome (the structural loop-check) ──────────────────────────────
    def syndrome(self, v: List[int]) -> List[int]:
        """σ(v) — the 12-bit Golay syndrome (the history).

        σ(v) = 0  → lawful pattern (no history)
        σ(v) ≠ 0  → unlawful pattern (history, gap, syndrome)
        """
        return self.golay.syndrome(v)

    def syndrome_weight(self, v: List[int]) -> int:
        """|σ(v)| — the weight of the syndrome (how much history)."""
        return self.golay.syndrome_weight(v)

    def is_lawful(self, v: List[int]) -> bool:
        """A pattern is lawful iff σ(v) = 0."""
        return self.syndrome_weight(v) == 0

    # ── MOG grid access (the grammar lives in L1, but the grid shape ─────
    #    is a property of the body) ───────────────────────────────────────
    def to_mog_grid(self, v: List[int]) -> List[List[int]]:
        """Arrange a 24-bit vector as a 4×6 MOG grid.

            col 0   col 1   col 2   col 3   col 4   col 5
        row 0  b0      b1      b2      b3      b4      b5      ← Reality
        row 1  b6      b7      b8      b9      b10     b11     ← Info
        row 2  b12     b13     b14     b15     b16     b17     ← Activation
        row 3  b18     b19     b20     b21     b22     b23     ← Potential
        """
        if len(v) != 24:
            raise ValueError(f"Body expects 24 coordinates, got {len(v)}")
        return [list(v[i*6:(i+1)*6]) for i in range(4)]

    def from_mog_grid(self, grid: List[List[int]]) -> List[int]:
        """Flatten a 4×6 MOG grid back to a 24-bit vector."""
        if len(grid) != 4 or any(len(row) != 6 for row in grid):
            raise ValueError("MOG grid must be 4×6")
        return [bit for row in grid for bit in row]

    # ── representation ────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (f"Body(dim=24, grid=4×6, Y={float(self.Y):.7f}, "
                f"Q={float(self.Q):.7f}, B={int(self.B)})")

    def constants_table(self) -> Dict[str, Any]:
        """Return all constants as a dict (for display/logging)."""
        return {
            "ZERO": ZERO,
            "DELTA": float(DELTA),
            "Z_STAR": float(Z_STAR),
            "B": int(B),
            "PI": float(PI),
            "Y": float(Y),
            "Q": float(Q),
            "dimension": 24,
            "grid_shape": "4×6",
        }
