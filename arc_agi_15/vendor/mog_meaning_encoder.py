"""
mog_meaning_encoder.py — MOG bit-addressed meaning
====================================================

The user's insight: "The MOG mapping is a great way to encode meaning
into data and each bit can have a 24D address assigned for increased
dimensions of information."

This module makes that literal.  Each of the 24 bits of a Leech address
gets its OWN 24-bit Leech address — a "bit-of-a-bit" recursion that
gives every bit a dimensional identity in MOG space.

Why this matters
----------------
A flat 24-bit address has 24 bits of information.  But each bit, viewed
as a Leech address itself, has 4 MOG quadrants × 6 categories = 24
dimensions of MEANING.  So the total information capacity of a single
cell becomes 24 × 24 = 576 dimensions of meaning.

This lets the GLM ask "what does bit 7 of this cell's address MEAN?" —
and get a structured answer, not just "0 or 1".

The MOG quadrants (from ubp_unified_v5.MOG_CATEGORIES)
------------------------------------------------------

Each 24-bit address is partitioned into 4 quadrants of 6 bits each:

  Quadrant 0 (bits  0-5):  Mirrors   — the cell's COLOUR fingerprint
  Quadrant 1 (bits  6-11): Information — the cell's POSITION topology
  Quadrant 2 (bits 12-17): Activation — the cell's GRID dimensions
  Quadrant 3 (bits 18-23): Potential  — the cell's COHERENCE pattern

Each quadrant has 6 categories (one per bit), and each category can be
encoded as its own 24-bit Leech address.  This is the "MOG bit address"
that gives every bit a dimensional identity.

The encoder
-----------
  encode_bit_address(quadrant, bit_in_quadrant, value)
    → 24-bit Leech address for that specific bit

  decode_meaning(vector_24)
    → Dict[quadrant_name, Dict[bit_position, bit_address]]

  bit_meaning_signature(vector_24)
    → A 96-element tuple (24 bits × 4 quadrants of meaning) that
      captures the FULL meaning of a cell's address

Sensory metaphor
----------------
This is the "proprioception" sense — the GLM's awareness of what each
part of its own address MEANS.  It complements:
  - touch (k-arm, neighbourhood)
  - sight (colour bridge, RGB332)
  - proprioception (this module — bit-level meaning)
  - audition (next module — periodicity/rhythm)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict
import sys, os, math, itertools

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_THIS_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from ubp_unified_v5 import (
    GOLAY_ENGINE, MOG_CATEGORIES, ontological_position_to_vector,
)


# ══════════════════════════════════════════════════════════════════════════════
# MOG quadrant structure (mirrors ubp_unified_v5.MOG_CATEGORIES)
# ══════════════════════════════════════════════════════════════════════════════

# The 4 MOG quadrants and their meaning (per the UBP spec)
MOG_QUADRANTS = [
    {"name": "Mirrors",     "bits": (0, 5),  "meaning": "colour fingerprint"},
    {"name": "Information", "bits": (6, 11), "meaning": "position topology"},
    {"name": "Activation",  "bits": (12, 17),"meaning": "grid dimensions"},
    {"name": "Potential",   "bits": (18, 23),"meaning": "coherence pattern"},
]


def get_quadrant(bit_index: int) -> int:
    """Which MOG quadrant does bit_index belong to?"""
    for i, q in enumerate(MOG_QUADRANTS):
        if q["bits"][0] <= bit_index <= q["bits"][1]:
            return i
    raise ValueError(f"bit_index {bit_index} out of range [0, 23]")


def get_bit_in_quadrant(bit_index: int) -> int:
    """Position of bit_index within its MOG quadrant (0-5)."""
    q = get_quadrant(bit_index)
    return bit_index - MOG_QUADRANTS[q]["bits"][0]


# ══════════════════════════════════════════════════════════════════════════════
# Bit address — each bit gets its own 24D Leech address
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class BitAddress:
    """The 24-bit Leech address of a single bit of a cell's address.

    A cell's address has 24 bits.  Each bit, viewed as a Leech address
    itself, has 24 bits of meaning.  This gives every bit a dimensional
    identity in MOG space.

    The bit address encodes:
      - which cell bit this is (bit_index 0-23)
      - which MOG quadrant (quadrant 0-3)
      - position within quadrant (bit_in_quadrant 0-5)
      - the bit's value (0 or 1)
      - the cell's row, col, colour (carried through for context)
    """
    bit_index: int           # 0-23, which bit of the cell's address
    quadrant: int            # 0-3, which MOG quadrant
    bit_in_quadrant: int     # 0-5, position within quadrant
    bit_value: int           # 0 or 1, the value of this bit
    vector_24: Tuple[int, ...]  # the 24-bit Leech address of THIS bit

    @property
    def quadrant_name(self) -> str:
        return MOG_QUADRANTS[self.quadrant]["name"]

    @property
    def meaning(self) -> str:
        return MOG_QUADRANTS[self.quadrant]["meaning"]


def encode_bit_address(bit_index: int, bit_value: int,
                        cell_row: int, cell_col: int,
                        cell_colour: int) -> BitAddress:
    """Compute the 24-bit Leech address of a single bit.

    The bit's address encodes:
      - bits 0-5:   bit_index (which cell bit, 0-23) — Gray-coded
      - bits 6-11:  bit_value × cell_row hash
      - bits 12-17: cell_col × cell_colour hash
      - bits 18-23: quadrant × bit_in_quadrant hash

    This gives each bit a unique 24-bit identity that depends on its
    position in the cell's address AND on the cell's context.
    """
    if not 0 <= bit_index < 24:
        raise ValueError(f"bit_index must be in [0, 23], got {bit_index}")
    if bit_value not in (0, 1):
        raise ValueError(f"bit_value must be 0 or 1, got {bit_value}")

    quadrant = get_quadrant(bit_index)
    bit_in_q = get_bit_in_quadrant(bit_index)

    # Pack into 24 bits
    idx_code = bit_index ^ (bit_index >> 1)  # Gray code
    idx_code &= 0x3F

    val_row = ((bit_value * 31 + cell_row * 17) % 64) & 0x3F
    val_row = val_row ^ (val_row >> 1)

    col_col = ((cell_col * 13 + cell_colour * 7) % 64) & 0x3F
    col_col = col_col ^ (col_col >> 1)

    q_biq = ((quadrant * 5 + bit_in_q * 11) % 64) & 0x3F
    q_biq = q_biq ^ (q_biq >> 1)

    position_24bit = (
        (idx_code << 18) |
        (val_row << 12) |
        (col_col << 6) |
        q_biq
    )
    vec = ontological_position_to_vector(position_24bit)
    return BitAddress(
        bit_index=bit_index,
        quadrant=quadrant,
        bit_in_quadrant=bit_in_q,
        bit_value=bit_value,
        vector_24=tuple(vec),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Cell meaning decoder — what does each bit of a cell's address MEAN?
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class CellMeaning:
    """The full dimensional meaning of a cell's 24-bit address.

    For each of the 24 bits, we record:
      - bit_index, quadrant, bit_in_quadrant, bit_value
      - the bit's own 24-bit Leech address (BitAddress)
      - the quadrant name and meaning

    This gives 24 × 24 = 576 dimensions of meaning per cell.
    """
    cell_row: int
    cell_col: int
    cell_colour: int
    cell_vector: List[int]
    bits: List[BitAddress] = field(default_factory=list)

    def quadrant_summary(self) -> Dict[str, Dict[str, Any]]:
        """Summarise meaning by MOG quadrant."""
        summary = {}
        for q_idx, q_info in enumerate(MOG_QUADRANTS):
            q_bits = [b for b in self.bits if b.quadrant == q_idx]
            q_value = sum(b.bit_value << b.bit_in_quadrant for b in q_bits)
            summary[q_info["name"]] = {
                "meaning": q_info["meaning"],
                "value": q_value,
                "weight": sum(b.bit_value for b in q_bits),
                "bits": [(b.bit_index, b.bit_value) for b in q_bits],
            }
        return summary

    def meaning_signature(self) -> Tuple[int, ...]:
        """A 24-element tuple of bit values — the cell's meaning fingerprint.

        This is a compact representation that can be compared with
        Hamming distance.
        """
        return tuple(b.bit_value for b in self.bits)


def decode_meaning(cell_vector: List[int],
                    cell_row: int, cell_col: int, cell_colour: int
                    ) -> CellMeaning:
    """Decode the full dimensional meaning of a cell's 24-bit address.

    For each bit, compute its own 24-bit Leech address (the bit's
    dimensional identity) and record its quadrant, position, value.
    """
    meaning = CellMeaning(
        cell_row=cell_row, cell_col=cell_col, cell_colour=cell_colour,
        cell_vector=cell_vector[:],
    )
    for i, bit_val in enumerate(cell_vector):
        ba = encode_bit_address(i, bit_val, cell_row, cell_col, cell_colour)
        meaning.bits.append(ba)
    return meaning


# ══════════════════════════════════════════════════════════════════════════════
# Meaning-based cell comparison
# ══════════════════════════════════════════════════════════════════════════════

def meaning_distance(meaning_a: CellMeaning, meaning_b: CellMeaning) -> Dict[str, float]:
    """Distance between two cells along each MOG quadrant.

    Returns a dict {quadrant_name: distance} where distance is the
    Hamming distance between the bit values in that quadrant.

    This lets the GLM ask "are these two cells similar in COLOUR
    (Mirrors) but different in POSITION (Information)?" — a question
    that flat 24-bit Hamming distance can't answer.
    """
    distances = {}
    for q_idx, q_info in enumerate(MOG_QUADRANTS):
        bits_a = [b.bit_value for b in meaning_a.bits if b.quadrant == q_idx]
        bits_b = [b.bit_value for b in meaning_b.bits if b.quadrant == q_idx]
        dist = sum(1 for a, b in zip(bits_a, bits_b) if a != b)
        distances[q_info["name"]] = dist
    return distances


def meaning_similarity(meaning_a: CellMeaning, meaning_b: CellMeaning) -> float:
    """Overall similarity between two cells in [0, 1].

    Weighted by quadrant importance:
      - Mirrors (colour) weight 0.4
      - Information (position) weight 0.3
      - Activation (grid) weight 0.2
      - Potential (coherence) weight 0.1
    """
    dists = meaning_distance(meaning_a, meaning_b)
    weights = {"Mirrors": 0.4, "Information": 0.3, "Activation": 0.2, "Potential": 0.1}
    sim = 0.0
    for q, w in weights.items():
        # 6 bits per quadrant, distance 0-6
        sim += w * (1.0 - dists.get(q, 6) / 6.0)
    return sim


# ══════════════════════════════════════════════════════════════════════════════
# Integration with hex_learner
# ══════════════════════════════════════════════════════════════════════════════

def cell_meaning_from_hex_cell(hex_cell) -> CellMeaning:
    """Build a CellMeaning from a hex_learner.HexCell."""
    return decode_meaning(
        hex_cell.vector, hex_cell.row, hex_cell.col, hex_cell.colour
    )


# ══════════════════════════════════════════════════════════════════════════════
# Self-test
# ══════════════════════════════════════════════════════════════════════════════

def _self_test():
    print("MOG Meaning Encoder self-test")
    print("=" * 60)

    # Bit address
    print("\n[Bit address] bit 7 of a cell at (2, 3) colour 4")
    ba = encode_bit_address(7, 1, 2, 3, 4)
    print(f"  {ba}")
    print(f"  Quadrant: {ba.quadrant_name} ({ba.meaning})")
    print(f"  Bit-in-quadrant: {ba.bit_in_quadrant}")
    print(f"  Bit value: {ba.bit_value}")
    print(f"  Vector (24-bit): {ba.vector_24}")

    # Cell meaning
    print("\n[Cell meaning] cell at (1, 1) colour 2, grid 5x5")
    from generative.hex_learner import address_cell
    hex_cell = address_cell(1, 1, 2, 5, 5)
    meaning = cell_meaning_from_hex_cell(hex_cell)
    summary = meaning.quadrant_summary()
    for q_name, q_info in summary.items():
        print(f"  {q_name} ({q_info['meaning']}): value={q_info['value']}, "
              f"weight={q_info['weight']}")

    # Meaning distance
    print("\n[Meaning distance] between (0,0,colour=1) and (0,0,colour=2)")
    cell_a = address_cell(0, 0, 1, 5, 5)
    cell_b = address_cell(0, 0, 2, 5, 5)
    meaning_a = cell_meaning_from_hex_cell(cell_a)
    meaning_b = cell_meaning_from_hex_cell(cell_b)
    dists = meaning_distance(meaning_a, meaning_b)
    for q, d in dists.items():
        print(f"  {q}: Hamming distance = {d}/6")
    print(f"  Overall similarity: {meaning_similarity(meaning_a, meaning_b):.3f}")

    # Same colour, different position
    print("\n[Meaning distance] between (0,0,colour=1) and (4,4,colour=1)")
    cell_c = address_cell(4, 4, 1, 5, 5)
    meaning_c = cell_meaning_from_hex_cell(cell_c)
    dists2 = meaning_distance(meaning_a, meaning_c)
    for q, d in dists2.items():
        print(f"  {q}: Hamming distance = {d}/6")
    print(f"  Overall similarity: {meaning_similarity(meaning_a, meaning_c):.3f}")

    print("\n" + "=" * 60)
    print("Self-test complete.")


if __name__ == "__main__":
    _self_test()
