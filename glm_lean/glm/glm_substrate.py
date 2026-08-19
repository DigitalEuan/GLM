#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM SUBSTRATE  —  Golay [24,12,8] / Hexacode / MOG / Leech metrics
================================================================================

  Part of:  The Geometric Language Machine (GLM)
  Layer  :  Tier 0 — the discrete substrate everything else is built on.
  Deps   :  Python standard library only.  No floats in any decision path.

  This module is deliberately small, self-contained and exhaustively testable.
  It provides:

    §1  Exact constants          pi, Y (as Fractions from a continued fraction)
    §2  GF(2) linear algebra     weights, distances, matrix/vector products
    §3  GolayCode                encode / syndrome / complete coset-leader
                                 decoder ("snap") / enumeration / census
    §4  Hexacode + MOG           GF(4) arithmetic, the [6,3,4] hexacode, the
                                 verified 4x6 MOG alignment of the 24 bits
    §5  LeechMetrics             minimal-vector census and the (stipulative)
                                 UBP cost layer TAX / NRCI

  Every structural claim made here is checked by an executable audit:

      python3 glm_substrate.py            # runs the substrate self-audit

  Provenance: a cleaned, de-duplicated distillation of the Golay / Leech
  engines of `ubp_unified_v5.py`, keeping the parts the GLM actually uses.
  The B-matrix and the MOG bit alignment are carried over verbatim, because
  the alignment is specific to this particular systematic generator matrix.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

__all__ = [
    "PI", "Y", "Y_INV", "NRCI_BASE",
    "BitOps", "GolayCode", "SnapMeta", "GOLAY",
    "GF4", "Hexacode", "HEXACODE", "MOG",
    "LeechMetrics", "LEECH",
    "substrate_audit",
]

Vec = List[int]


# ══════════════════════════════════════════════════════════════════════════════
# §1.  EXACT CONSTANTS  (rational; no floats in any decision path)
# ══════════════════════════════════════════════════════════════════════════════

# Continued-fraction coefficients of pi.  Truncating at 50 terms gives a
# rational agreeing with pi far beyond anything here needs; the point is that
# the value is exact and reproducible, not that it is pi.
_PI_CF: Tuple[int, ...] = (
    3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, 2, 1, 1, 2, 2, 2, 2,
    1, 84, 2, 1, 1, 15, 3, 13, 1, 4, 2, 6, 6, 99, 1, 2, 2, 6, 3, 5,
    1, 1, 6, 8, 1, 7, 1, 6, 1, 99, 7, 4, 1, 3, 3, 1, 4, 1,
)


def pi_fraction(terms: int = 50) -> F:
    """pi as an exact Fraction from its continued fraction (`terms` coefficients)."""
    coeffs = _PI_CF[: max(1, min(terms, len(_PI_CF)))]
    x = F(coeffs[-1], 1)
    for c in reversed(coeffs[:-1]):
        x = F(c, 1) + F(1, 1) / x
    return x


PI: F = pi_fraction(50)
#: UBP "wobble" constant  Y = 1 / (pi + 2/pi) ~ 0.264734.  Stipulative: it
#: enters only the cost layer (TAX / NRCI), never a structural decision.
Y_INV: F = PI + F(2, 1) / PI
Y: F = F(1, 1) / Y_INV
#: NRCI normalisation base B (stipulative).
NRCI_BASE: F = F(10, 1)


# ══════════════════════════════════════════════════════════════════════════════
# §2.  GF(2) LINEAR ALGEBRA
# ══════════════════════════════════════════════════════════════════════════════

class BitOps:
    """Bit-vector helpers.  Vectors are plain lists of 0/1 ints."""

    @staticmethod
    def weight(v: Sequence[int]) -> int:
        return sum(1 for x in v if x)

    @staticmethod
    def distance(u: Sequence[int], v: Sequence[int]) -> int:
        if len(u) != len(v):
            raise ValueError("hamming distance: length mismatch")
        return sum(1 for a, b in zip(u, v) if a != b)

    @staticmethod
    def xor(u: Sequence[int], v: Sequence[int]) -> Vec:
        if len(u) != len(v):
            raise ValueError("xor: length mismatch")
        return [a ^ b for a, b in zip(u, v)]

    @staticmethod
    def matvec(M: Sequence[Sequence[int]], v: Sequence[int]) -> Vec:
        out = []
        for row in M:
            s = 0
            for a, b in zip(row, v):
                s ^= a & b
            out.append(s)
        return out

    @staticmethod
    def matmul(A: Sequence[Sequence[int]], B: Sequence[Sequence[int]]) -> List[Vec]:
        inner, cols = len(B), len(B[0])
        out: List[Vec] = []
        for row in A:
            new: Vec = []
            for j in range(cols):
                s = 0
                for k in range(inner):
                    s ^= row[k] & B[k][j]
                new.append(s)
            out.append(new)
        return out

    @staticmethod
    def from_int(n: int, length: int) -> Vec:
        """Little-endian: bit i of `n` becomes coordinate i."""
        return [(n >> i) & 1 for i in range(length)]

    @staticmethod
    def to_int(v: Sequence[int]) -> int:
        n = 0
        for i, b in enumerate(v):
            if b:
                n |= 1 << i
        return n


# ══════════════════════════════════════════════════════════════════════════════
# §3.  THE EXTENDED BINARY GOLAY CODE  [24, 12, 8]
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SnapMeta:
    """Everything the decoder knows about one snap, with no rounding."""

    syndrome: int              # 12-bit syndrome as an integer
    syndrome_weight: int       # popcount of the syndrome (0..12)
    distance: int              # Hamming distance moved (= coset leader weight, 0..4)
    tie_count: int             # number of equally near codewords (1, or 6 at d = 4)
    corrected_bits: Tuple[int, ...]

    @property
    def is_lawful(self) -> bool:
        return self.distance == 0

    @property
    def is_correctable(self) -> bool:
        return 1 <= self.distance <= 3

    @property
    def is_ambiguous(self) -> bool:
        return self.distance == 4

    @property
    def status(self) -> str:
        if self.is_lawful:
            return "lawful"
        if self.is_correctable:
            return "correctable"
        if self.is_ambiguous:
            return "ambiguous"
        return "beyond-covering-radius"   # unreachable for 24-bit inputs


class GolayCode:
    """
    The extended binary Golay code C in systematic form G = [I12 | B].

    Facts established by execution (see `census()`):
      * |C| = 2^12 = 4096 codewords, C is self-dual (C = C-perp), doubly even
      * minimum distance d = 8; weight enumerator
            W(z) = 1 + 759 z^8 + 2576 z^12 + 759 z^16 + z^24
      * packing radius t = 3, covering radius rho = 4
      * coset-leader profile over the 4096 cosets:
            weight 0:1, 1:24, 2:276, 3:2024, 4:1771   (sum = 4096)
      * every weight-4 coset has exactly 6 minimal leaders, so "snap" at
        distance 4 is a genuine 6-way tie broken by convention, not by the code.

    `snap` maps any v in F_2^24 to a codeword at Hamming distance <= 4.  For
    distance <= 3 that codeword is the unique nearest one; at distance 4 the
    leader chosen is the lexicographically first minimum-weight leader, which
    is a CONVENTION (the tie is real and is reported in `SnapMeta.tie_count`).
    """

    N = 24
    K = 12
    D = 8
    PACKING_RADIUS = 3
    COVERING_RADIUS = 4

    #: symmetric parity block B used in G = [I12 | B] and H = [B | I12]
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
        self.G: List[Vec] = [
            [1 if i == j else 0 for j in range(12)] + list(self.B[i])
            for i in range(12)
        ]
        # B is symmetric, so H = [B^T | I] = [B | I].
        self.H: List[Vec] = [
            [self.B[j][i] for j in range(12)] + [1 if i == j else 0 for j in range(12)]
            for i in range(12)
        ]
        self._syn_cols: Tuple[int, ...] = tuple(
            sum((1 << j) for j in range(12) if self.H[j][k]) for k in range(24)
        )
        self._codewords: Optional[List[Vec]] = None
        self._codeword_ints: Optional[frozenset] = None
        self._octads: Optional[List[Vec]] = None
        self._leaders: Optional[Dict[int, int]] = None    # syndrome -> leader mask
        self._tie_counts: Optional[Dict[int, int]] = None

    # ── basic maps ────────────────────────────────────────────────────────────
    def encode(self, msg12: Sequence[int]) -> Vec:
        if len(msg12) != 12:
            raise ValueError("encode: message must be 12 bits")
        parity = []
        for j in range(12):
            p = 0
            bj = self.B[j]
            for i in range(12):
                p ^= msg12[i] & bj[i]
            parity.append(p)
        return list(msg12) + parity

    def syndrome(self, v24: Sequence[int]) -> Vec:
        """H . v (mod 2), as a 12-bit list."""
        s = self.syndrome_int(v24)
        return [(s >> j) & 1 for j in range(12)]

    def syndrome_int(self, v24: Sequence[int]) -> int:
        if len(v24) != 24:
            raise ValueError("syndrome: 24 bits required")
        n = 0
        for k, bit in enumerate(v24):
            if bit:
                n ^= self._syn_cols[k]
        return n

    def syndrome_weight(self, v24: Sequence[int]) -> int:
        """Weight of the 12-bit syndrome.  NOT the distance to the code."""
        return _popcount(self.syndrome_int(v24))

    def is_codeword(self, v24: Sequence[int]) -> bool:
        return self.syndrome_int(v24) == 0

    # ── complete coset-leader table (all 4096 cosets) ────────────────────────
    def _build_leader_table(self) -> Tuple[Dict[int, int], Dict[int, int]]:
        """
        For every one of the 4096 syndromes, store a minimum-weight coset
        leader (24-bit mask) and the number of leaders of that minimum weight.

        Enumerating all error patterns of weight <= 4 covers every coset
        (covering radius 4).  Patterns are visited in (weight, lexicographic)
        order, so the stored leader is the lex-first minimum-weight leader.
        """
        cols = self._syn_cols
        leaders: Dict[int, int] = {0: 0}
        ties: Dict[int, int] = {0: 1}
        for w in (1, 2, 3, 4):
            for idx in _combinations(range(24), w):
                syn = 0
                mask = 0
                for i in idx:
                    syn ^= cols[i]
                    mask |= 1 << i
                known = leaders.get(syn)
                if known is None:
                    leaders[syn] = mask
                    ties[syn] = 1
                elif _popcount(known) == w:
                    ties[syn] += 1
        return leaders, ties

    def _ensure_leaders(self) -> None:
        if self._leaders is None:
            self._leaders, self._tie_counts = self._build_leader_table()

    def leader_table(self) -> Dict[int, int]:
        self._ensure_leaders()
        assert self._leaders is not None
        return self._leaders

    def snap(self, v24: Sequence[int]) -> Tuple[Vec, SnapMeta]:
        """Correct `v24` to a nearest codeword; return (codeword, metadata)."""
        if len(v24) != 24:
            raise ValueError("snap: 24 bits required")
        self._ensure_leaders()
        assert self._leaders is not None and self._tie_counts is not None
        syn = self.syndrome_int(v24)
        mask = self._leaders[syn]
        out = [b ^ ((mask >> i) & 1) for i, b in enumerate(v24)]
        return out, SnapMeta(
            syndrome=syn,
            syndrome_weight=_popcount(syn),
            distance=_popcount(mask),
            tie_count=self._tie_counts[syn],
            corrected_bits=tuple(i for i in range(24) if (mask >> i) & 1),
        )

    def nearest_codewords(self, v24: Sequence[int]) -> List[Vec]:
        """All codewords at minimum distance from `v24` (1 of them, or 6 at d = 4)."""
        best = 25
        out: List[Vec] = []
        for cw in self.all_codewords():
            d = BitOps.distance(cw, v24)
            if d < best:
                best, out = d, [list(cw)]
            elif d == best:
                out.append(list(cw))
        return out

    # ── enumeration ───────────────────────────────────────────────────────────
    def all_codewords(self) -> List[Vec]:
        if self._codewords is None:
            self._codewords = [self.encode(BitOps.from_int(i, 12)) for i in range(4096)]
            self._codeword_ints = frozenset(BitOps.to_int(c) for c in self._codewords)
        return self._codewords

    def codeword_ints(self) -> frozenset:
        self.all_codewords()
        assert self._codeword_ints is not None
        return self._codeword_ints

    def octads(self) -> List[Vec]:
        """The 759 weight-8 codewords (blocks of the Steiner system S(5,8,24))."""
        if self._octads is None:
            self._octads = [c for c in self.all_codewords() if sum(c) == 8]
        return self._octads

    def weight_enumerator(self) -> Dict[int, int]:
        counts: Dict[int, int] = {}
        for c in self.all_codewords():
            w = sum(c)
            counts[w] = counts.get(w, 0) + 1
        return dict(sorted(counts.items()))

    def min_distance(self) -> int:
        """Minimum distance = minimum nonzero weight (the code is linear)."""
        return min(sum(c) for c in self.all_codewords() if any(c))

    def is_self_dual(self) -> bool:
        """C = C-perp  <=>  G . G^T = 0 (mod 2) and dim C = 12."""
        GT = [[self.G[i][j] for i in range(12)] for j in range(24)]
        prod = BitOps.matmul(self.G, GT)
        return all(x == 0 for row in prod for x in row)

    def is_doubly_even(self) -> bool:
        return all(sum(c) % 4 == 0 for c in self.all_codewords())

    # ── census: the executable audit of every claim above ────────────────────
    def census(self) -> Dict[str, object]:
        self._ensure_leaders()
        assert self._leaders is not None and self._tie_counts is not None
        leader_profile: Dict[int, int] = {}
        tie_profile: Dict[str, int] = {}
        for syn, mask in self._leaders.items():
            w = _popcount(mask)
            leader_profile[w] = leader_profile.get(w, 0) + 1
            key = f"weight{w}:{self._tie_counts[syn]}-way"
            tie_profile[key] = tie_profile.get(key, 0) + 1
        return {
            "codewords": len(self.all_codewords()),
            "octads": len(self.octads()),
            "weight_enumerator": self.weight_enumerator(),
            "min_distance": self.min_distance(),
            "self_dual": self.is_self_dual(),
            "doubly_even": self.is_doubly_even(),
            "cosets": len(self._leaders),
            "leader_weight_profile": dict(sorted(leader_profile.items())),
            "covering_radius": max(leader_profile),
            "tie_profile": dict(sorted(tie_profile.items())),
        }


GOLAY = GolayCode()


# ══════════════════════════════════════════════════════════════════════════════
# §4.  GF(4), THE HEXACODE [6,3,4] AND THE MOG ALIGNMENT
# ══════════════════════════════════════════════════════════════════════════════

class GF4:
    """GF(4) = {0, 1, w, w^2} represented as {0, 1, 2, 3}; addition is XOR."""

    SYMBOLS = {0: "0", 1: "1", 2: "w", 3: "w2"}
    ADD = tuple(tuple(a ^ b for b in range(4)) for a in range(4))
    MUL = (
        (0, 0, 0, 0),
        (0, 1, 2, 3),
        (0, 2, 3, 1),
        (0, 3, 1, 2),
    )

    @staticmethod
    def add(a: int, b: int) -> int:
        return a ^ b

    @staticmethod
    def mul(a: int, b: int) -> int:
        return GF4.MUL[a][b]

    @staticmethod
    def word_str(word: Sequence[int]) -> str:
        return " ".join(GF4.SYMBOLS[s] for s in word)


class Hexacode:
    """
    The hexacode H6: a [6, 3, 4] linear code over GF(4) with 4^3 = 64 words.
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
                        for i in range(6)
                    ))
        self.words: Tuple[Tuple[int, ...], ...] = tuple(sorted(words))
        self.word_set = frozenset(self.words)

    def __contains__(self, word: Sequence[int]) -> bool:
        return tuple(word) in self.word_set

    def min_distance(self) -> int:
        return min(sum(1 for x in w if x) for w in self.words if any(w))

    def census(self) -> Dict[str, object]:
        return {
            "size": len(self.words),
            "length": 6,
            "dimension": 3,
            "min_distance": self.min_distance(),
        }


HEXACODE = Hexacode()


def _column_label(value: int) -> int:
    """GF(4) label of a 4-bit column: XOR of the row labels (0, 1, w, w^2)."""
    lbl = 0
    for r in range(4):
        if (value >> r) & 1:
            lbl ^= r
    return lbl


class MOG:
    """
    The Miracle Octad Generator view: the 24 coordinates as a 4x6 grid.

    Two distinct griddings are used in the GLM; they must not be confused.

      * `MOG.ALIGNED_BITS` — the VERIFIED alignment for this specific
        systematic Golay generator.  Under it every Golay codeword's six
        column labels form a hexacode word (0 / 4096 failures — see
        `verify_hexacode_shadow`).  Use this whenever a hexacode statement
        is being made.

      * the plain "tier" gridding (row r = coordinates 6r .. 6r+5), used by
        the GLM concept encoder for its four ontological tiers.  It is a
        perfectly good relabelling of the 24 bits, and the column codec is
        bijective under it, but its column labels are NOT hexacode words.

    ALIGNED_BITS[mog_index] = coordinate index, with mog_index = 6*row + col.
    """

    ALIGNED_BITS: Tuple[int, ...] = (
        0, 4, 6, 19, 16, 11,     # row 0  (row label 0)
        1, 17, 15, 5, 9, 13,     # row 1  (row label 1)
        3, 21, 20, 8, 10, 22,    # row 2  (row label w)
        2, 23, 14, 12, 7, 18,    # row 3  (row label w^2)
    )

    #: COLUMN_LABEL[v] = GF(4) label of the 4-bit column value v (bit r = row r)
    COLUMN_LABEL: Tuple[int, ...] = tuple(_column_label(v) for v in range(16))

    @staticmethod
    def to_grid(v24: Sequence[int], aligned: bool = True) -> List[List[int]]:
        """The 4x6 grid of `v24` (row-major) in the chosen gridding."""
        if len(v24) != 24:
            raise ValueError("to_grid: 24 bits required")
        flat = [v24[MOG.ALIGNED_BITS[i]] for i in range(24)] if aligned else list(v24)
        return [flat[6 * r: 6 * r + 6] for r in range(4)]

    @staticmethod
    def columns(v24: Sequence[int], aligned: bool = True) -> List[int]:
        """The six 4-bit column values (bit r = row r)."""
        grid = MOG.to_grid(v24, aligned=aligned)
        return [sum(grid[r][c] << r for r in range(4)) for c in range(6)]

    @staticmethod
    def shadow(v24: Sequence[int], aligned: bool = True) -> Tuple[int, ...]:
        """The six GF(4) column labels — the hexacode shadow."""
        return tuple(MOG.COLUMN_LABEL[v] for v in MOG.columns(v24, aligned=aligned))

    @staticmethod
    def verify_hexacode_shadow() -> Dict[str, object]:
        """
        Exhaustive check: under `ALIGNED_BITS`, every one of the 4096 Golay
        codewords casts a valid hexacode shadow.
        """
        failures = 0
        sample = None
        for cw in GOLAY.all_codewords():
            sh = MOG.shadow(cw, aligned=True)
            if sh not in HEXACODE:
                failures += 1
            elif sample is None and any(cw):
                sample = (BitOps.to_int(cw), sh)
        return {
            "codewords_tested": 4096,
            "failures": failures,
            "aligned": failures == 0,
            "sample": sample,
        }

    @staticmethod
    def label_fibre_sizes() -> Dict[int, int]:
        """How many of the 16 column values carry each GF(4) label (expect 4 each)."""
        out: Dict[int, int] = {}
        for v in range(16):
            lbl = MOG.COLUMN_LABEL[v]
            out[lbl] = out.get(lbl, 0) + 1
        return dict(sorted(out.items()))


# ══════════════════════════════════════════════════════════════════════════════
# §5.  LEECH LATTICE  —  census and the (stipulative) cost layer
# ══════════════════════════════════════════════════════════════════════════════

class LeechMetrics:
    """
    Lambda_24 in the x sqrt(8) integer representation: minimal vectors have
    norm^2 = 32.

    Structural part (verifiable):
      the 196,560 minimal vectors split into three shape classes
        A  (+-4, +-4, 0^22)              1,104  = C(24,2)*4
        B  (+-2^8, 0^16) on octads      97,152  = 759*128
        C  (+-3, +-1^23) Golay-driven   98,304  = 24*4096
      each of norm^2 = 32 and each satisfying the mod-8 glue condition.

    Cost layer (STIPULATIVE — a modelling choice, not a theorem):
        TAX(v)  = HW(v)*Y + ||v||^2/8
        NRCI(v) = B / (B + alpha*TAX(v)),   B = 10, alpha = 1
    Both are exact Fractions.  Nothing structural depends on them; they can be
    removed without touching the codec, the decoder or the reasoner.
    """

    DIM = 24
    SCALE = 8
    KISSING = 196560

    def __init__(self, golay: GolayCode = GOLAY) -> None:
        self.golay = golay
        self.Y = Y

    # ── cost layer ───────────────────────────────────────────────────────────
    def tax(self, point: Sequence[int]) -> F:
        if len(point) != 24:
            raise ValueError("tax: 24 coordinates required")
        hw = sum(1 for x in point if x)
        ns = sum(x * x for x in point)
        return F(hw, 1) * self.Y + F(ns, self.SCALE)

    def nrci(self, point: Sequence[int], alpha: F = F(1)) -> F:
        return NRCI_BASE / (NRCI_BASE + alpha * self.tax(point))

    # ── minimal vectors ──────────────────────────────────────────────────────
    def minimal_vectors(self, cls: str) -> Iterator[Tuple[int, ...]]:
        """Stream the minimal vectors of one shape class ('A', 'B' or 'C')."""
        n = self.DIM
        if cls == "A":
            for i in range(n):
                for j in range(i + 1, n):
                    for si in (4, -4):
                        for sj in (4, -4):
                            v = [0] * n
                            v[i], v[j] = si, sj
                            yield tuple(v)
        elif cls == "B":
            for octad in self.golay.octads():
                pos = [k for k, b in enumerate(octad) if b]
                for signs in range(256):
                    if _popcount(signs) & 1:
                        continue
                    v = [0] * n
                    for k, p in enumerate(pos):
                        v[p] = -2 if (signs >> k) & 1 else 2
                    yield tuple(v)
        elif cls == "C":
            for i in range(n):
                for c in self.golay.all_codewords():
                    v = [(-1 if c[j] else 1) for j in range(n)]
                    v[i] = 3 if c[i] else -3
                    yield tuple(v)
        else:
            raise ValueError("minimal_vectors: class must be 'A', 'B' or 'C'")

    def census(self, verify_every_vector: bool = True) -> Dict[str, object]:
        """
        Count the minimal vectors class by class, optionally verifying norm and
        glue condition for every one of the 196,560 vectors (a few seconds).
        """
        out: Dict[str, object] = {}
        total = 0
        bad_norm = 0
        glue: Dict[str, List[int]] = {}
        for cls in ("A", "B", "C"):
            count = 0
            residues = set()
            for v in self.minimal_vectors(cls):
                count += 1
                if verify_every_vector or count == 1:
                    if sum(x * x for x in v) != 32:
                        bad_norm += 1
                    residues.add(sum(v) % 8)
            out[f"class_{cls}"] = count
            glue[cls] = sorted(residues)
            total += count
        out["total"] = total
        out["expected_total"] = self.KISSING
        out["norm_failures"] = bad_norm
        out["glue_residues_mod8"] = glue
        return out


LEECH = LeechMetrics(GOLAY)


# ══════════════════════════════════════════════════════════════════════════════
#  small helpers
# ══════════════════════════════════════════════════════════════════════════════

def _popcount(n: int) -> int:
    return bin(n).count("1")


def _combinations(pool: Iterable[int], r: int) -> Iterator[Tuple[int, ...]]:
    """Local `itertools.combinations`, kept explicit so the order is visible."""
    items = list(pool)
    n = len(items)
    if r > n:
        return
    idx = list(range(r))
    yield tuple(items[i] for i in idx)
    while True:
        for i in reversed(range(r)):
            if idx[i] != i + n - r:
                break
        else:
            return
        idx[i] += 1
        for j in range(i + 1, r):
            idx[j] = idx[j - 1] + 1
        yield tuple(items[i] for i in idx)


# ══════════════════════════════════════════════════════════════════════════════
#  SELF-AUDIT
# ══════════════════════════════════════════════════════════════════════════════

def substrate_audit(full_leech: bool = True) -> Dict[str, object]:
    """Run every structural check this module makes and return the results."""
    return {
        "golay": GOLAY.census(),
        "hexacode": HEXACODE.census(),
        "mog_alignment": MOG.verify_hexacode_shadow(),
        "mog_label_fibres": MOG.label_fibre_sizes(),
        "leech": LEECH.census(verify_every_vector=full_leech),
        "constants": {
            "pi": str(PI),
            "pi_float": float(PI),
            "Y": str(Y),
            "Y_float": float(Y),
        },
    }


def _print_audit(full_leech: bool = True) -> Dict[str, object]:
    a = substrate_audit(full_leech=full_leech)
    g = a["golay"]
    h = a["hexacode"]
    m = a["mog_alignment"]
    lch = a["leech"]
    c = a["constants"]
    print("=" * 78)
    print("  GLM SUBSTRATE SELF-AUDIT")
    print("=" * 78)
    print("\n[Golay 24,12,8]")
    print(f"  codewords            : {g['codewords']} (expected 4096)")
    print(f"  minimum distance     : {g['min_distance']} (expected 8)")
    print(f"  self-dual            : {g['self_dual']}")
    print(f"  doubly even          : {g['doubly_even']}")
    print(f"  weight enumerator    : {g['weight_enumerator']}")
    print(f"  octads               : {g['octads']} (expected 759)")
    print(f"  cosets               : {g['cosets']} (expected 4096)")
    print(f"  leader weight profile: {g['leader_weight_profile']}")
    print(f"  covering radius      : {g['covering_radius']} (expected 4)")
    print(f"  leader tie profile   : {g['tie_profile']}")
    print("\n[Hexacode 6,3,4 over GF(4)]")
    print(f"  words {h['size']}, min distance {h['min_distance']}")
    print("\n[MOG alignment]")
    print(f"  hexacode-shadow failures over all 4096 codewords: {m['failures']}")
    print(f"  GF(4) label fibre sizes: {a['mog_label_fibres']} (expected 4 each)")
    print("\n[Leech minimal vectors]")
    print(f"  class A {lch['class_A']}, class B {lch['class_B']}, class C {lch['class_C']}")
    print(f"  total {lch['total']} (expected {lch['expected_total']}), "
          f"norm^2 failures {lch['norm_failures']}")
    print(f"  glue residues mod 8  : {lch['glue_residues_mod8']}")
    print("\n[Exact constants]")
    print(f"  pi ~ {c['pi_float']:.15f}   Y = 1/(pi+2/pi) ~ {c['Y_float']:.15f}")
    print("=" * 78)
    return a


if __name__ == "__main__":
    _print_audit()
