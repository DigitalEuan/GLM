#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM CODEC  —  Z^7  <->  F_2^24  <->  GF(4)^6 x Z_4^6
================================================================================

  Part of:  The Geometric Language Machine (GLM)
  Layer  :  Tier 1 — the lossless codec between meaning and substrate.
  Deps   :  glm_substrate.py, standard library only.

  Contents
  --------
    §1  ColumnCodec   the 16-state column bijection  F_2^4 <-> GF(4) x Z_4
    §2  MOGCodec      the 24-bit codec  F_2^24 <-> GF(4)^6 x Z_4^6
    §3  DimCarrier    the bijective carrier  Z^7 (range-limited) <-> F_2^24
    §4  views         the four "ontological tiers" as an interpretive profile
    §5  lawfulness    which dimension vectors land exactly on Golay codewords

  Design note (why this differs from GLM v7 - v17)
  ------------------------------------------------
  Earlier versions encoded a dimension vector d in Z^7 into 24 bits with a
  four-tier feature map (Reality / Information / Activation / Potential,
  6 bits each).  That map is MANY-TO-ONE: e.g. d = (2,1,-2,0,0,0,0) (energy)
  and (3,1,-2,0,0,0,0) share several tiers, and the published implementation
  also skipped the "amount of substance" dimension through an index slip
  (`range(5)` + index 6).  Because of that, "0-bit reconstruction error"
  described the feature bits, not the concept: you could recover the bits but
  not the physics.

  This module fixes that.  The carrier is now a *bijection* on the exponent
  box  E = [-4, 4]^7:

        |E| = 9^7 = 4,782,969  <  2^24 = 16,777,216

  so a dimension vector fits losslessly in 24 bits with room to spare, and the
  full chain

        d  ->  24-bit carrier  ->  (hexacode shadow, fibre keys)  ->  d

  is exactly invertible.  The four tiers survive as an interpretive *view*
  (§4), which is what they were always used for in practice.

      python3 glm_codec.py         # runs the codec self-audit
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from glm_substrate import GF4, GOLAY, MOG, BitOps

__all__ = [
    "ColumnCodec", "MOGShadow", "MOGCodec",
    "DIM_MIN", "DIM_MAX", "DIM_RADIX", "CARRIER_CAPACITY",
    "DimCarrier", "TIER_NAMES", "ontological_profile",
    "lawful_dimension_census", "codec_audit",
]

Vec = List[int]


# ══════════════════════════════════════════════════════════════════════════════
# §1.  THE COLUMN BIJECTION   F_2^4  <->  GF(4) x Z_4
# ══════════════════════════════════════════════════════════════════════════════

class ColumnCodec:
    """
    A 4-bit MOG column b = (b0, b1, b2, b3) carries two pieces of information:

        label(b) in GF(4)   the hexacode symbol  (XOR of the row labels
                            0, 1, w, w^2 over the set rows)
        fibre(b) in Z_4     which of the four columns sharing that label b is,
                            ranked by the column's integer value

    label is GF(2)-linear and surjective with kernel of size 4, so every label
    has exactly four preimages (`MOG.label_fibre_sizes()`), and

        b  <->  (label(b), fibre(b))

    is a bijection between the 16 columns and GF(4) x Z_4.  That is the whole
    content of the "MOG fibre codec": it is lossless by counting, and the
    16-state table below is checked exhaustively.
    """

    #: value -> (label, fibre index)
    TO_SHADOW: Dict[int, Tuple[int, int]] = {}
    #: (label, fibre index) -> value
    FROM_SHADOW: Dict[Tuple[int, int], int] = {}

    @classmethod
    def _build(cls) -> None:
        if cls.TO_SHADOW:
            return
        buckets: Dict[int, List[int]] = {0: [], 1: [], 2: [], 3: []}
        for value in range(16):                 # ranked by integer value: canonical
            buckets[MOG.COLUMN_LABEL[value]].append(value)
        for label, members in buckets.items():
            for fibre, value in enumerate(sorted(members)):
                cls.TO_SHADOW[value] = (label, fibre)
                cls.FROM_SHADOW[(label, fibre)] = value

    @classmethod
    def encode(cls, value: int) -> Tuple[int, int]:
        cls._build()
        return cls.TO_SHADOW[value]

    @classmethod
    def decode(cls, label: int, fibre: int) -> int:
        cls._build()
        return cls.FROM_SHADOW[(label, fibre)]

    @classmethod
    def table(cls) -> Dict[int, Tuple[int, int]]:
        cls._build()
        return dict(cls.TO_SHADOW)

    @classmethod
    def verify_bijection(cls) -> Dict[str, object]:
        cls._build()
        round_trip_ok = all(
            cls.decode(*cls.encode(v)) == v for v in range(16)
        )
        return {
            "states": len(cls.TO_SHADOW),
            "inverse_states": len(cls.FROM_SHADOW),
            "round_trip_ok": round_trip_ok,
            "bijective": round_trip_ok and len(cls.TO_SHADOW) == 16
            and len(cls.FROM_SHADOW) == 16,
        }


# ══════════════════════════════════════════════════════════════════════════════
# §2.  THE 24-BIT CODEC   F_2^24  <->  GF(4)^6 x Z_4^6
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class MOGShadow:
    """A 24-bit word seen as six hexacode symbols plus six fibre keys."""

    labels: Tuple[int, ...]        # 6 GF(4) symbols
    fibres: Tuple[int, ...]        # 6 elements of Z_4
    aligned: bool                  # which gridding produced it

    def symbol_string(self) -> str:
        return GF4.word_str(self.labels)

    def is_hexacode_word(self) -> bool:
        from glm_substrate import HEXACODE
        return self.labels in HEXACODE

    def __repr__(self) -> str:
        return (f"MOGShadow(symbols=[{self.symbol_string()}], "
                f"fibres={list(self.fibres)}, aligned={self.aligned})")


class MOGCodec:
    """
    Lossless projection of a 24-bit word onto (hexacode shadow, fibre keys).

    `aligned=True`  uses the verified MOG bit alignment, under which the six
                    labels of a Golay codeword form a hexacode word.
    `aligned=False` uses the plain "tier" gridding (row r = bits 6r..6r+5).
                    Still bijective, but the labels are not hexacode words.

    Bijectivity of the 24-bit codec follows from bijectivity of the 16-state
    column codec, because the map acts independently on the six columns; the
    column table is verified exhaustively and the 24-bit round trip is checked
    on structured and pseudo-random samples in the test-suite.
    """

    @staticmethod
    def project(v24: Sequence[int], aligned: bool = True) -> MOGShadow:
        cols = MOG.columns(v24, aligned=aligned)
        pairs = [ColumnCodec.encode(c) for c in cols]
        return MOGShadow(tuple(p[0] for p in pairs),
                         tuple(p[1] for p in pairs),
                         aligned)

    @staticmethod
    def reconstruct(shadow: MOGShadow) -> Vec:
        cols = [ColumnCodec.decode(lbl, fib)
                for lbl, fib in zip(shadow.labels, shadow.fibres)]
        flat = [0] * 24
        for c, value in enumerate(cols):
            for r in range(4):
                flat[6 * r + c] = (value >> r) & 1
        if not shadow.aligned:
            return flat
        out = [0] * 24
        for mog_idx, coord in enumerate(MOG.ALIGNED_BITS):
            out[coord] = flat[mog_idx]
        return out

    @staticmethod
    def round_trip_error(v24: Sequence[int], aligned: bool = True) -> int:
        """Hamming distance between a word and its codec round trip (expect 0)."""
        return BitOps.distance(
            v24, MOGCodec.reconstruct(MOGCodec.project(v24, aligned=aligned))
        )


# ══════════════════════════════════════════════════════════════════════════════
# §3.  THE DIMENSION CARRIER   Z^7  <->  F_2^24
# ══════════════════════════════════════════════════════════════════════════════

DIM_MIN = -4
DIM_MAX = 4
DIM_RADIX = DIM_MAX - DIM_MIN + 1          # 9 exponent values per dimension
CARRIER_CAPACITY = DIM_RADIX ** 7          # 4,782,969 representable vectors


def _zigzag(e: int) -> int:
    """Signed exponent -> digit in [0, 8]:  0,1,-1,2,-2,3,-3,4,-4 -> 0..8."""
    return 2 * e if e >= 0 else -2 * e - 1


def _unzigzag(z: int) -> int:
    return z // 2 if z % 2 == 0 else -(z + 1) // 2


class DimCarrier:
    """
    Bijective encoding of a dimension vector d in [-4,4]^7 into 24 bits.

    The seven exponents are zigzag-coded (0, 1, -1, 2, -2, 3, -3, 4, -4 ->
    digits 0..8) and packed as a mixed-radix base-9 integer, little-endian in
    dimension order (L, M, T, I, Theta, N, J), then written out as 24 bits.

      * the dimensionless vector d = 0 maps to the all-zero word, which is the
        Golay zero codeword: "dimensionless is the vacuum"
      * small exponents give small integers, so physically common quantities
        occupy the low end of the carrier
      * `decode` is exact and total on the carrier's image; it returns None for
        the 12M words that are not the image of any in-range dimension vector

    This is an ARITHMETIC packing.  It makes the codec chain lossless; it does
    not by itself give the bits a physical meaning.  The interpretive reading
    of the bits is the tier profile of §4, and the code-theoretic reading is
    the lawfulness census of §5.
    """

    @staticmethod
    def in_range(dims: Sequence[int]) -> bool:
        return len(dims) == 7 and all(DIM_MIN <= e <= DIM_MAX for e in dims)

    @staticmethod
    def to_int(dims: Sequence[int]) -> int:
        if not DimCarrier.in_range(dims):
            raise ValueError(
                f"DimCarrier: exponents must be 7 integers in "
                f"[{DIM_MIN}, {DIM_MAX}], got {list(dims)}"
            )
        n = 0
        for e in reversed(dims):
            n = n * DIM_RADIX + _zigzag(e)
        return n

    @staticmethod
    def from_int(n: int) -> Optional[List[int]]:
        if n < 0 or n >= CARRIER_CAPACITY:
            return None
        dims = []
        for _ in range(7):
            n, z = divmod(n, DIM_RADIX)
            dims.append(_unzigzag(z))
        return dims

    @staticmethod
    def encode(dims: Sequence[int]) -> Vec:
        return BitOps.from_int(DimCarrier.to_int(dims), 24)

    @staticmethod
    def decode(v24: Sequence[int]) -> Optional[List[int]]:
        return DimCarrier.from_int(BitOps.to_int(v24))

    @staticmethod
    def is_carrier_word(v24: Sequence[int]) -> bool:
        return BitOps.to_int(v24) < CARRIER_CAPACITY

    @staticmethod
    def census() -> Dict[str, object]:
        return {
            "exponent_range": [DIM_MIN, DIM_MAX],
            "radix": DIM_RADIX,
            "representable_vectors": CARRIER_CAPACITY,
            "carrier_bits": 24,
            "carrier_states": 1 << 24,
            "utilisation": CARRIER_CAPACITY / float(1 << 24),
        }


# ══════════════════════════════════════════════════════════════════════════════
# §4.  THE FOUR ONTOLOGICAL TIERS  (interpretive view, not the encoding)
# ══════════════════════════════════════════════════════════════════════════════

TIER_NAMES = ("Reality", "Information", "Activation", "Potential")


def ontological_profile(dims: Sequence[int]) -> Dict[str, List[int]]:
    """
    The four-tier reading of a dimension vector, kept from earlier GLM
    versions as an interpretation (7 flags per tier, one per SI dimension):

        Reality     d_i != 0      the dimension participates at all
        Information d_i mod 2     its parity (what a mod-2 substrate can see)
        Activation  |d_i| > 1     it is present to a power above the first
        Potential   d_i < 0       it appears in the denominator

    These four flags do NOT determine d (e.g. every d with d_i in {2, 4} has
    the same profile), which is exactly why they are a view and not the
    carrier: see the module docstring.
    """
    if len(dims) != 7:
        raise ValueError("ontological_profile: 7 exponents required")
    return {
        "Reality": [1 if e != 0 else 0 for e in dims],
        "Information": [e % 2 for e in dims],
        "Activation": [1 if abs(e) > 1 else 0 for e in dims],
        "Potential": [1 if e < 0 else 0 for e in dims],
    }


# ══════════════════════════════════════════════════════════════════════════════
# §5.  LAWFULNESS:  WHICH DIMENSION VECTORS ARE GOLAY CODEWORDS?
# ══════════════════════════════════════════════════════════════════════════════

def lawful_dimension_census(max_examples: int = 8) -> Dict[str, object]:
    """
    Sweep the whole exponent box [-4,4]^7 and count the dimension vectors whose
    24-bit carrier is exactly a Golay codeword (syndrome 0, snap distance 0).

    This is a property of the codec, not of physics: it says how much of the
    concept space sits on the code, i.e. needs no correction.  It replaces the
    earlier "brute force over [-3,3]^7 found 221 sigma = 0 encodings" result,
    which was measured against the old lossy tier encoder.
    """
    codewords = GOLAY.codeword_ints()
    lawful: List[int] = [n for n in range(CARRIER_CAPACITY) if n in codewords]
    by_weight: Dict[int, int] = {}
    for n in lawful:
        w = bin(n).count("1")
        by_weight[w] = by_weight.get(w, 0) + 1
    examples = []
    for n in sorted(lawful, key=lambda m: (bin(m).count("1"), m))[:max_examples]:
        examples.append({"dims": DimCarrier.from_int(n),
                         "carrier_int": n,
                         "weight": bin(n).count("1")})
    return {
        "searched": CARRIER_CAPACITY,
        "lawful": len(lawful),
        "fraction": len(lawful) / float(CARRIER_CAPACITY),
        "by_carrier_weight": dict(sorted(by_weight.items())),
        "examples": examples,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  SELF-AUDIT
# ══════════════════════════════════════════════════════════════════════════════

def codec_audit(sample: int = 20000, lawful_sweep: bool = True) -> Dict[str, object]:
    """Check the column bijection, the 24-bit round trip and the carrier."""
    col = ColumnCodec.verify_bijection()

    # 24-bit round trip, both griddings, on a deterministic pseudo-random sweep
    errors_aligned = 0
    errors_tier = 0
    state = 0x9E3779B9
    for _ in range(sample):
        state = (state * 1103515245 + 12345) & 0xFFFFFF
        v = BitOps.from_int(state, 24)
        errors_aligned += MOGCodec.round_trip_error(v, aligned=True)
        errors_tier += MOGCodec.round_trip_error(v, aligned=False)

    # carrier round trip over a full sub-box plus the extremes
    carrier_errors = 0
    for n in range(0, CARRIER_CAPACITY, 7919):        # ~604 evenly spaced words
        d = DimCarrier.from_int(n)
        assert d is not None
        if DimCarrier.to_int(d) != n:
            carrier_errors += 1
    for e0 in range(DIM_MIN, DIM_MAX + 1):
        for e1 in range(DIM_MIN, DIM_MAX + 1):
            d = [e0, e1, -e0, e1 // 2, -e1, e0 // 2, e0]
            if DimCarrier.decode(DimCarrier.encode(d)) != d:
                carrier_errors += 1

    out: Dict[str, object] = {
        "column_codec": col,
        "round_trip_samples": sample,
        "round_trip_errors_aligned": errors_aligned,
        "round_trip_errors_tier": errors_tier,
        "carrier": DimCarrier.census(),
        "carrier_round_trip_errors": carrier_errors,
    }
    if lawful_sweep:
        out["lawful_dimension_census"] = lawful_dimension_census()
    return out


def _print_audit() -> Dict[str, object]:
    a = codec_audit()
    print("=" * 78)
    print("  GLM CODEC SELF-AUDIT")
    print("=" * 78)
    print("\n[Column bijection F_2^4 <-> GF(4) x Z_4]")
    print(f"  {a['column_codec']}")
    print("\n[24-bit MOG codec round trip]")
    print(f"  samples {a['round_trip_samples']}, "
          f"errors (aligned) {a['round_trip_errors_aligned']}, "
          f"errors (tier gridding) {a['round_trip_errors_tier']}")
    print("\n[Dimension carrier Z^7 <-> F_2^24]")
    c = a["carrier"]
    print(f"  exponent box {c['exponent_range']}^7 -> {c['representable_vectors']} "
          f"vectors in {c['carrier_states']} words "
          f"({100 * c['utilisation']:.1f}% utilisation)")
    print(f"  round-trip errors: {a['carrier_round_trip_errors']}")
    law = a.get("lawful_dimension_census")
    if law:
        print("\n[Lawful dimension vectors (carrier is a Golay codeword)]")
        print(f"  {law['lawful']} of {law['searched']} "
              f"({100 * law['fraction']:.4f}%), by carrier weight "
              f"{law['by_carrier_weight']}")
        for ex in law["examples"][:4]:
            print(f"    dims={ex['dims']}  weight={ex['weight']}")
    print("=" * 78)
    return a


if __name__ == "__main__":
    _print_audit()
