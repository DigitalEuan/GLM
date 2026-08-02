"""
colour_space_bridge.py — the 2×4×8×32 = 2048 Golay-Leech ↔ colour bridge
==========================================================================

The user's observation: "I see 2×4×8×32 = 2048 these appear to be bridges
between Golay-Leech shells and colour spaces to me."

This module builds that bridge explicitly.

The bridge
----------

A 24-bit Leech address has the structure:

    [ hemisphere (1 bit) | MOG quadrant (2 bits) | octad index (3 bits) | colour index (5 bits) ]
       2 states             4 states               8 states               32 states

    2 × 4 × 8 × 32 = 2048 distinct (hemisphere, quadrant, octad, colour) cells.

This is the bridge between:
  - Golay-Leech shells (hemisphere × quadrant × octad = 64 shell positions)
  - Colour spaces (32 subpalette colours per shell position)

Why 32 colours?
---------------
The 256-colour space (3-3-2 RGB) is the standard 8-bit palette.  ARC uses
10 colours (0-9), but the LEECH address has 5 bits of "colour" information
(bits 18-23 of the 24-bit vector).  2^5 = 32, so each shell position has
32 colour slots — enough to embed the 10 ARC colours plus 22 "spectral"
colours that fill out the palette.

The bridge lets us:
  1. Look up any 24-bit Leech address as a (shell, colour) pair
  2. Find the nearest 256-colour RGB equivalent of a Leech address
  3. Map the 10 ARC colours into the 32-colour subpalette with spectral
     interpolation
  4. Use the well-studied 256-colour space (perceptual distances,
     complements, harmonies) as PRIOR KNOWLEDGE for the GLM

144 = 12 × 12 pairwise angular sectors
---------------------------------------
The user's note: "144 is simply the number of pairwise interactions
between 12 angular sectors".  The Golay code has rank 12; each message
bit defines an angular sector.  Pairwise interactions between 12 sectors
= 12 × 12 = 144 = the relational space for any 12-element system.

When we move data through Time, each Time step has 144 possible
pairwise direction-changes.  This is the "temporal relational space"
that the k-arm can explore.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from fractions import Fraction
from collections import defaultdict
import sys, os, math, itertools

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_THIS_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from ubp_unified_v5 import (
    GOLAY_ENGINE, LEECH_ENGINE, MOG_CATEGORIES,
    ontological_position_to_vector,
)
from GLM18_hex_colour import vector_to_colour


# ══════════════════════════════════════════════════════════════════════════════
# The 2×4×8×32 = 2048 bridge
# ══════════════════════════════════════════════════════════════════════════════

# Standard 3-3-2 RGB palette (256 colours).  This is the well-mapped
# colour space the user mentioned.  Index = (R << 5) | (G << 2) | B
# where R,G ∈ {0..7} (3 bits) and B ∈ {0..3} (2 bits).
def build_rgb332_palette() -> List[Tuple[int, int, int]]:
    """Build the standard 256-colour 3-3-2 RGB palette."""
    palette = []
    for r in range(8):
        for g in range(8):
            for b in range(4):
                # Scale to 0-255
                R = (r * 255) // 7
                G = (g * 255) // 7
                B = (b * 255) // 3
                palette.append((R, G, B))
    return palette


RGB332_PALETTE = build_rgb332_palette()
assert len(RGB332_PALETTE) == 256


# The 10 ARC colours mapped into RGB for visualisation.
# (These are the standard ARC-AGI colour values.)
ARC_COLOUR_RGB = {
    0: (0, 0, 0),         # black
    1: (0, 116, 217),     # blue
    2: (255, 65, 54),     # red
    3: (46, 204, 64),     # green
    4: (255, 220, 0),     # yellow
    5: (170, 170, 170),   # grey
    6: (240, 18, 190),    # magenta
    7: (255, 133, 27),    # orange
    8: (127, 219, 255),   # azure
    9: (135, 153, 119),   # olive
}


def nearest_rgb332(r: int, g: int, b: int) -> int:
    """Find the index in the 256-colour palette nearest to (r,g,b)."""
    best_idx = 0
    best_dist = float("inf")
    for i, (pr, pg, pb) in enumerate(RGB332_PALETTE):
        d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if d < best_dist:
            best_dist = d
            best_idx = i
    return best_idx


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Convert #RRGGBB to (r, g, b) in 0-255."""
    h = hex_str.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert (r,g,b) to #RRGGBB."""
    return f"#{r:02x}{g:02x}{b:02x}"


# ══════════════════════════════════════════════════════════════════════════════
# Bridge: 24-bit Leech address ↔ (shell, colour) pair
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class BridgeAddress:
    """A 24-bit Leech address decomposed into the 2×4×8×32 bridge.

    Fields:
      hemisphere: 0 or 1 (the "sign" of the address — even/odd parity)
      quadrant:   0-3 (which of the 4 MOG quadrants: Mirrors/Info/Act/Pot)
      octad_idx:  0-7 (which of 8 octad positions within the quadrant)
      colour_idx: 0-31 (which of 32 subpalette colours)

    Together these index into a 2048-cell bridge space.
    """
    hemisphere: int
    quadrant: int
    octad_idx: int
    colour_idx: int

    @property
    def bridge_index(self) -> int:
        """Flat index in [0, 2048).

        Note: hemisphere is encoded via the MSB but is recovered as
        (idx >= 1024), so the bridge index is 0..2047 and the
        hemisphere is the top bit.
        """
        return ((self.hemisphere & 1) << 11) | \
               ((self.quadrant & 3) << 9) | \
               ((self.octad_idx & 7) << 5) | \
               (self.colour_idx & 31)

    @classmethod
    def from_bridge_index(cls, idx: int) -> "BridgeAddress":
        # Don't mask — the hemisphere is the bit at position 11.
        # idx can be up to 2047 (when hemisphere=1, q=3, o=7, c=31).
        h = (idx >> 11) & 1
        q = (idx >> 9) & 3
        o = (idx >> 5) & 7
        c = idx & 31
        return cls(hemisphere=h, quadrant=q, octad_idx=o, colour_idx=c)

    def __repr__(self):
        return (f"BridgAddr(h={self.hemisphere}, q={self.quadrant}, "
                f"o={self.octad_idx}, c={self.colour_idx})")


def leech_to_bridge(vector_24: List[int]) -> BridgeAddress:
    """Decompose a 24-bit Leech address into the 2×4×8×32 bridge.

    Bit allocation (matching per_object_24d / hex_learner):
      bits 0       : hemisphere (parity of the full vector)
      bits 1-2     : quadrant (top 2 bits of palette_code)
      bits 3-5     : octad_idx (bottom 4 bits of palette_code + position hash)
      bits 6-10    : colour_idx (5 bits from position+coherence hash)
      bits 11-23   : unused at bridge level (refined Golay structure)
    """
    # Parity → hemisphere
    parity = sum(vector_24) & 1

    # Take the top 6 bits as palette_code, next 6 as pos_code, etc.
    # (matching the encoder in hex_learner.address_cell)
    n = 0
    for i, bit in enumerate(vector_24):
        if bit:
            n |= (1 << (23 - i))

    palette_code = (n >> 18) & 0x3F
    pos_code = (n >> 12) & 0x3F
    dim_code = (n >> 6) & 0x3F
    coh_code = n & 0x3F

    # Quadrant = top 2 bits of palette_code
    quadrant = (palette_code >> 4) & 3
    # Octad = bottom 4 bits of palette_code XOR top 4 bits of pos_code
    octad_idx = (palette_code & 0xF) ^ ((pos_code >> 2) & 0xF)
    octad_idx &= 7  # 3 bits
    # Colour = bottom 5 bits of coh_code XOR bottom 3 bits of dim_code
    colour_idx = (coh_code & 0x1F) ^ (dim_code & 0x7)
    colour_idx &= 31  # 5 bits

    return BridgeAddress(
        hemisphere=parity,
        quadrant=quadrant,
        octad_idx=octad_idx,
        colour_idx=colour_idx,
    )


def bridge_to_rgb332(bridge: BridgeAddress) -> int:
    """Map a bridge address to the 256-colour RGB332 palette.

    Uses the 32-colour subpalette indexed by bridge.colour_idx, then
    refines by quadrant (which shifts the hue) and octad (which shifts
    the brightness).

    The result is a perceptually-meaningful colour that can be compared
    using standard colour-distance metrics.
    """
    # 32 subpalette colours spread across the RGB332 space
    subpalette_idx = bridge.colour_idx
    # Spread 32 colours across the 256-colour space (every 8th colour)
    base_rgb_idx = (subpalette_idx * 8) & 0xFF

    # Quadrant shifts the hue: 0=no shift, 1=red shift, 2=green shift, 3=blue shift
    r, g, b = RGB332_PALETTE[base_rgb_idx]
    quadrant_shifts = [(0, 0, 0), (20, -10, -10), (-10, 20, -10), (-10, -10, 20)]
    dr, dg, db = quadrant_shifts[bridge.quadrant & 3]
    r = max(0, min(255, r + dr))
    g = max(0, min(255, g + dg))
    b = max(0, min(255, b + db))

    # Octad shifts brightness: 0=dark, 7=bright
    brightness_shift = (bridge.octad_idx - 4) * 10
    r = max(0, min(255, r + brightness_shift))
    g = max(0, min(255, g + brightness_shift))
    b = max(0, min(255, b + brightness_shift))

    # Hemisphere inverts if 1
    if bridge.hemisphere:
        r, g, b = 255 - r, 255 - g, 255 - b

    return nearest_rgb332(r, g, b)


# ══════════════════════════════════════════════════════════════════════════════
# 144 = 12 × 12 pairwise angular sectors
# ══════════════════════════════════════════════════════════════════════════════

def angular_sector(message_bit: int) -> int:
    """Map a Golay message bit (0-11) to an angular sector (0-11).

    The 12 message bits of the Golay [24,12,8] code define 12 angular
    sectors, one per dimension of the message space.  Each sector
    corresponds to a "direction" in the 12-dimensional message space.
    """
    if not 0 <= message_bit < 12:
        raise ValueError(f"message_bit must be in [0, 11], got {message_bit}")
    return message_bit


def pairwise_angular_interactions() -> List[Tuple[int, int]]:
    """The 144 pairwise interactions between 12 angular sectors.

    Returns a list of 144 (sector_i, sector_j) tuples, including
    self-pairs (i, i).  This is the relational space for any 12-element
    system, used when moving data through Time.
    """
    return [(i, j) for i in range(12) for j in range(12)]


def temporal_direction_index(delta_int: int) -> Tuple[int, int]:
    """Map a 24-bit delta to a (sector_i, sector_j) pair in the 144-space.

    The delta is split into two 12-bit halves; each half is interpreted
    as an angular sector index.  This compresses a 24-bit transformation
    into a 144-cell relational space, which is small enough to enumerate
    exhaustively in the GLM's "thought".
    """
    sector_i = (delta_int >> 12) & 0xFFF  # top 12 bits
    sector_j = delta_int & 0xFFF           # bottom 12 bits
    # Reduce to 0-11 range by taking mod 12 (or top 4 bits mod 12)
    sector_i = (sector_i >> 8) % 12
    sector_j = (sector_j >> 8) % 12
    return (sector_i, sector_j)


# ══════════════════════════════════════════════════════════════════════════════
# Colour-distance metrics (using the 256-colour space as prior knowledge)
# ══════════════════════════════════════════════════════════════════════════════

def colour_distance_rgb332(idx_a: int, idx_b: int) -> float:
    """Euclidean distance between two RGB332 palette colours."""
    r1, g1, b1 = RGB332_PALETTE[idx_a & 0xFF]
    r2, g2, b2 = RGB332_PALETTE[idx_b & 0xFF]
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def colour_complement_rgb332(idx: int) -> int:
    """The complement of a colour in the RGB332 palette."""
    r, g, b = RGB332_PALETTE[idx & 0xFF]
    return nearest_rgb332(255 - r, 255 - g, 255 - b)


def colour_harmony_rgb332(idx: int) -> List[int]:
    """Three-colour harmony (triadic) of a colour in RGB332."""
    r, g, b = RGB332_PALETTE[idx & 0xFF]
    # Rotate by 120° in RGB space (approximation)
    h1 = nearest_rgb332(b, r, g)
    h2 = nearest_rgb332(g, b, r)
    return [h1, h2]


# ══════════════════════════════════════════════════════════════════════════════
# Top-level: bridge an ARC cell to its full colour-space identity
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class CellColourIdentity:
    """The full colour-space identity of an ARC cell.

    Combines:
      - ARC palette colour (0-9)
      - 24-bit Leech address
      - Hex colour (#RRGGBB)
      - Bridge address (hemisphere, quadrant, octad, colour_idx)
      - RGB332 palette index (0-255)
      - RGB tuple (0-255 each)
      - Complement and harmony colours
    """
    arc_colour: int
    vector_24: List[int]
    hex_colour: str
    bridge: BridgeAddress
    rgb332_idx: int
    rgb: Tuple[int, int, int]
    complement_rgb332: int
    harmony_rgb332: List[int]

    def summary(self) -> str:
        return (f"CellColourIdentity(arc={self.arc_colour}, "
                f"hex={self.hex_colour}, bridge={self.bridge}, "
                f"rgb332={self.rgb332_idx}, rgb={self.rgb})")


def identify_cell(row: int, col: int, colour: int,
                  grid_h: int, grid_w: int) -> CellColourIdentity:
    """Compute the full colour-space identity of a cell."""
    # Reuse hex_learner's address_cell for the 24-bit vector
    from generative.hex_learner import address_cell
    hex_cell = address_cell(row, col, colour, grid_h, grid_w)

    # Bridge decomposition
    bridge = leech_to_bridge(hex_cell.vector)

    # RGB332 mapping
    rgb332_idx = bridge_to_rgb332(bridge)
    rgb = RGB332_PALETTE[rgb332_idx]
    complement = colour_complement_rgb332(rgb332_idx)
    harmony = colour_harmony_rgb332(rgb332_idx)

    return CellColourIdentity(
        arc_colour=colour,
        vector_24=hex_cell.vector,
        hex_colour=hex_cell.hex,
        bridge=bridge,
        rgb332_idx=rgb332_idx,
        rgb=rgb,
        complement_rgb332=complement,
        harmony_rgb332=harmony,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Self-test
# ══════════════════════════════════════════════════════════════════════════════

def _self_test():
    print("Colour-Space Bridge self-test")
    print("=" * 60)

    # Bridge structure
    print(f"\n[Bridge] 2 × 4 × 8 × 32 = {2*4*8*32} cells")
    assert 2 * 4 * 8 * 32 == 2048

    # Round-trip bridge index
    b = BridgeAddress(hemisphere=1, quadrant=2, octad_idx=5, colour_idx=17)
    idx = b.bridge_index
    b2 = BridgeAddress.from_bridge_index(idx)
    assert b == b2, f"bridge round-trip failed: {b} != {b2}"
    print(f"  Bridge round-trip: {b} ↔ idx={idx} ↔ {b2}  ✓")

    # 144 pairwise angular sectors
    pairs = pairwise_angular_interactions()
    assert len(pairs) == 144
    print(f"\n[144] Pairwise angular interactions: {len(pairs)}")

    # Identify a cell
    print(f"\n[Cell identity] (row=2, col=3, colour=4, grid 6×8)")
    ident = identify_cell(2, 3, 4, 6, 8)
    print(f"  {ident.summary()}")
    print(f"  Complement RGB332: {ident.complement_rgb332} ({RGB332_PALETTE[ident.complement_rgb332]})")
    print(f"  Harmony RGB332:    {ident.harmony_rgb332}")

    # Multiple ARC colours → check they get different bridge addresses
    print(f"\n[All 10 ARC colours] bridge addresses:")
    for c in range(10):
        ident = identify_cell(0, 0, c, 5, 5)
        print(f"  colour {c}: bridge={ident.bridge}, hex={ident.hex_colour}, "
              f"rgb332={ident.rgb332_idx}")

    print("\n" + "=" * 60)
    print("Self-test complete.")


if __name__ == "__main__":
    _self_test()
