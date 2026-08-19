#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM MOONSHINE  —  the Leech / Griess bookkeeping layer  (paper section 10)
================================================================================

  Part of:  The Geometric Language Machine (GLM)
  Layer  :  optional.  Nothing in the decision path depends on this module.
  Deps   :  glm_substrate.py

  Versions 13 to 19 of the archive climbed a "sporadic complexity map" towards
  the Monster: a Griess algebra, a 299-dimensional traceless symmetric piece,
  a 98,280-dimensional line tracker, a 98,304-dimensional tensor product,
  vertex operators and McKay-Thompson coefficients.  Most of that was reached
  for; some of it is exactly checkable arithmetic and belongs in the system.
  This module keeps the checkable part and says plainly what the rest was.

  What is exact here
  ------------------
    §1  line census        the 196,560 minimal vectors of Lambda_24, verified
                           to be closed under negation and pairwise distinct,
                           giving exactly 98,280 lines, split 552 / 48,576 /
                           49,152 by shape class
    §2  class C indexing   the map (coordinate, codeword) -> minimal vector of
                           shape (-+3, +-1^23) is a bijection onto its image,
                           so 98,304 = 24 x 4096 is a count, not an analogy
    §3  dimension ledger   1 + 299 + 98,280 + 98,304 = 196,884, with each
                           summand computed from its own definition
    §4  the head of J      the weight-2 dimension of the Leech lattice vertex
                           algebra, 196,884 = 324 + 196,560, computed from an
                           exact integer q-expansion of prod (1-q^n)^-24 and
                           from the census of §1
    §5  Jordan layer       the 300-dimensional Jordan algebra R + S^2_0(R^24),
                           commutative, unital, non-associative - the honest
                           replacement for the "snap-based Griess product"

  What is NOT here, and why
  -------------------------
    * The Monster itself.  Nothing in the archive constructed it, and nothing
      here does either.  The identity 1 + 299 + 98,280 + 98,304 = 196,884 is
      dimension bookkeeping for the Griess algebra; it is not a construction
      of the algebra and still less of its automorphism group.
    * McKay-Thompson coefficient tables.  The archive carried tables for
      classes 1A, 2A, 2B, 3A, ... which no code in it generated and which
      disagree with each other between versions.  Only the 1A head
      coefficient is shipped, and it is computed (§4), not quoted.
    * The "concept -> Monster conjugacy class" assignment of versions 13-19
      (sigma = 0 -> 1A, sigma <= 3 -> 2A, ...).  It is a relabelling of the
      syndrome weight with no group-theoretic content, so it is dropped; the
      syndrome weight itself is reported directly by the reasoner.
    * Vertex operators.  The archive's Y(v, z) had hand-chosen modes and an
      "inner product" that is 24 - 2 * Hamming distance in disguise (verified
      as such in `hamming_inner_product_report`), so it carried no VOA content.

  Run standalone for a self-audit:   python3 glm_moonshine.py
================================================================================
"""

from __future__ import annotations

from fractions import Fraction as F
from typing import Dict, List, Sequence, Tuple

from glm_substrate import GOLAY, LEECH, BitOps

__all__ = [
    "line_census", "class_c_indexing_report", "dimension_ledger",
    "eta_power_series", "leech_voa_head", "hamming_inner_product_report",
    "JordanElement", "jordan_algebra_report", "moonshine_audit",
]

DIM = 24
GRIESS_DIM = 196884
STANDARD_REP_DIM = 196883


# ══════════════════════════════════════════════════════════════════════════════
# §1.  THE LINE CENSUS
# ══════════════════════════════════════════════════════════════════════════════

def _key(vec: Sequence[int]) -> bytes:
    """A compact hashable key for a minimal vector (coordinates in [-4, 4])."""
    return bytes(x + 4 for x in vec)


def line_census() -> Dict[str, object]:
    """
    Enumerate all 196,560 minimal vectors of Lambda_24 and verify:

      * they are pairwise distinct;
      * the set is closed under v -> -v, and no vector is its own negative;
      * hence the number of LINES {v, -v} is exactly half the number of
        vectors, 98,280, split by shape class as 552 / 48,576 / 49,152.

    Version 18's "orbit line tracker" asserted this split; here it is counted.
    """
    seen: Dict[bytes, str] = {}
    per_class: Dict[str, int] = {}
    for cls in ("A", "B", "C"):
        count = 0
        for v in LEECH.minimal_vectors(cls):
            seen[_key(v)] = cls
            count += 1
        per_class[cls] = count
    total = sum(per_class.values())
    distinct = len(seen)

    negation_closed = True
    class_preserved = True
    self_negative = 0
    for k, cls in seen.items():
        neg = bytes(8 - b for b in k)          # (x + 4) -> (-x + 4)
        if neg not in seen:
            negation_closed = False
            break
        if seen[neg] != cls:
            class_preserved = False
        if neg == k:
            self_negative += 1

    lines_per_class = {c: n // 2 for c, n in per_class.items()}
    return {
        "vectors": total,
        "distinct": distinct,
        "all_distinct": distinct == total,
        "by_class": per_class,
        "negation_closed": negation_closed,
        "class_preserved_under_negation": class_preserved,
        "self_negative_vectors": self_negative,
        "lines": total // 2,
        "lines_by_class": lines_per_class,
        "expected_lines": 98280,
        "matches_expected": (total == 196560 and total // 2 == 98280
                             and lines_per_class == {"A": 552, "B": 48576,
                                                     "C": 49152}),
    }


# ══════════════════════════════════════════════════════════════════════════════
# §2.  CLASS C INDEXING:  98,304 = 24 x 4096
# ══════════════════════════════════════════════════════════════════════════════

def class_c_indexing_report() -> Dict[str, object]:
    """
    The shape-C minimal vectors are indexed by (coordinate i, codeword c):
    coordinate i carries -+3, the others +-1 according to c.  Verify that the
    indexing is injective, that all 24 x 4096 = 98,304 images have norm^2 = 32
    and glue residue 4 mod 8, and that the count coincides with the dimension
    of the tensor factor R^24 (x) V_4096 that version 16 introduced.
    """
    images: Dict[bytes, Tuple[int, int]] = {}
    bad_norm = 0
    bad_glue = 0
    codewords = GOLAY.all_codewords()
    for i in range(DIM):
        for ci, c in enumerate(codewords):
            v = [(-1 if c[j] else 1) for j in range(DIM)]
            v[i] = 3 if c[i] else -3
            if sum(x * x for x in v) != 32:
                bad_norm += 1
            if sum(v) % 8 != 4:
                bad_glue += 1
            images[_key(v)] = (i, ci)
    n = DIM * len(codewords)
    return {
        "index_pairs": n,
        "distinct_images": len(images),
        "injective": len(images) == n,
        "norm_failures": bad_norm,
        "glue_failures": bad_glue,
        "equals_24_times_4096": n == DIM * 4096 == 98304,
    }


# ══════════════════════════════════════════════════════════════════════════════
# §3.  THE DIMENSION LEDGER
# ══════════════════════════════════════════════════════════════════════════════

def dimension_ledger() -> Dict[str, object]:
    """
    Every summand of 196,884 computed from its own definition:

      1        the identity of the algebra
      299      dim S^2_0(R^24) = 24*25/2 - 1, the traceless symmetric forms
      98,280   the lines of minimal vectors (from §1)
      98,304   24 x 4096, the class C index set (from §2)

    and 196,883 = 196,884 - 1 is the standard representation's dimension.
    """
    sym = DIM * (DIM + 1) // 2
    traceless = sym - 1
    lines = line_census()["lines"]
    tensor = DIM * len(GOLAY.all_codewords())
    total = 1 + traceless + lines + tensor
    return {
        "identity": 1,
        "sym_dim": sym,
        "traceless_sym_dim": traceless,
        "lines": lines,
        "tensor": tensor,
        "total": total,
        "griess_dim": GRIESS_DIM,
        "ledger_balances": total == GRIESS_DIM,
        "standard_rep": total - 1,
        "standard_rep_matches": total - 1 == STANDARD_REP_DIM,
    }


# ══════════════════════════════════════════════════════════════════════════════
# §4.  THE HEAD OF J:  196,884 = 324 + 196,560
# ══════════════════════════════════════════════════════════════════════════════

def eta_power_series(order: int) -> List[int]:
    """
    Exact integer coefficients of  prod_{n>=1} (1 - q^n)^{-24}  up to q^order.

    These count the oscillator states of 24 free bosons: 1, 24, 324, 3200, ...
    """
    coeffs = [0] * (order + 1)
    coeffs[0] = 1
    for n in range(1, order + 1):
        for _ in range(24):
            # multiply the series by 1/(1 - q^n)
            for m in range(n, order + 1):
                coeffs[m] += coeffs[m - n]
    return coeffs


def leech_voa_head(order: int = 1) -> Dict[str, object]:
    """
    The head of the graded dimension of the Leech lattice vertex algebra,

        J(q) = Theta_Lambda(q) / eta(q)^24 = q^-1 + 24 + 196884 q + ...

    computed inside the system: the oscillator factor from
    `eta_power_series`, and the lattice factor from the minimal-vector census
    (the only non-trivial coefficient needed at this order is 196,560).

    The weight-2 coefficient 196,884 therefore arises here as

        196,884 = 324 (two oscillator quanta) + 196,560 (minimal vectors),

    while the dimension ledger of §3 splits the same number as
    1 + 299 + 98,280 + 98,304.  Both are computed; their agreement is the
    numerical content of the "moonshine" remark, and nothing more is claimed.

    The expansion stops at q^1, which is exactly as far as the census of §1
    supports it: the next coefficient of Theta_Lambda counts the vectors of
    norm 6, which this system does not enumerate, so a higher order raises
    rather than guesses.
    """
    if order > 1:
        raise ValueError(
            "leech_voa_head: only q^-1 .. q^1 are supported; higher "
            "coefficients need the norm-6 shell of Lambda_24, which this "
            "system does not enumerate")
    osc = eta_power_series(order + 1)
    minimal = sum(1 for _cls in ("A", "B", "C")
                  for _ in LEECH.minimal_vectors(_cls))
    # Theta = 1 + 0*q + minimal*q^2 + ...   (Leech has no vectors of norm 2)
    theta = [0] * (order + 2)
    theta[0] = 1
    if order + 1 >= 2:
        theta[2] = minimal
    # J = q^-1 * (Theta * osc);  coefficient of q^n in J is [q^{n+1}](Theta*osc)
    head: Dict[int, int] = {}
    for n in range(-1, order + 1):
        m = n + 1
        head[n] = sum(theta[t] * osc[m - t] for t in range(m + 1)
                      if t < len(theta) and m - t < len(osc))
    return {
        "oscillator_coefficients": osc[:order + 2],
        "minimal_vectors": minimal,
        "J_head": {f"q^{n}": v for n, v in sorted(head.items())},
        "weight_two_dim": head.get(1),
        "weight_two_split": {"oscillator": osc[2], "lattice": minimal},
        "matches_griess_dim": head.get(1) == GRIESS_DIM,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  what the archive's "Leech inner product" really was
# ══════════════════════════════════════════════════════════════════════════════

def hamming_inner_product_report(samples: int = 4096) -> Dict[str, object]:
    """
    Versions 18 and 19 fused concepts with an "inner product" defined as
    (matching bits) - (mismatching bits) between two 24-bit words, and read
    the result as a Leech lattice pairing.  For 24-bit words that quantity is
    identically 24 - 2 * d(u, v): it is the Hamming distance, rescaled.  This
    is verified over a deterministic sample of word pairs.
    """
    state = 0x5DEECE66
    mismatches = 0
    for _ in range(samples):
        state = (state * 1103515245 + 12345) & 0xFFFFFF
        u = BitOps.from_int(state, 24)
        state = (state * 1103515245 + 12345) & 0xFFFFFF
        v = BitOps.from_int(state, 24)
        archive = sum(1 for a, b in zip(u, v) if a == b) - \
            sum(1 for a, b in zip(u, v) if a != b)
        if archive != 24 - 2 * BitOps.distance(u, v):
            mismatches += 1
    return {
        "pairs_tested": samples,
        "counterexamples": mismatches,
        "identity": "matches - mismatches == 24 - 2 * hamming_distance",
        "holds": mismatches == 0,
    }


# ══════════════════════════════════════════════════════════════════════════════
# §5.  THE JORDAN LAYER  —  R + S^2_0(R^24)
# ══════════════════════════════════════════════════════════════════════════════
#
#  The corrected statement of section 8.3 of the paper is that the archive's
#  "snap-based Griess product" is associative, hence not Griess-like at all.
#  What can be exhibited exactly, in 300 dimensions, is the scalar-plus-
#  traceless-symmetric layer:
#
#      element   (alpha, S)   with alpha in Q and S a traceless symmetric
#                             24 x 24 matrix over Q
#      product   (alpha, S) . (beta, T)
#                  = (alpha*beta + tr(ST)/24,
#                     alpha*T + beta*S + S.T - tr(ST)/24 * I)
#      where     S.T = (ST + TS)/2
#
#  Under (alpha, S) <-> alpha*I + S this is exactly the Jordan algebra of
#  symmetric 24 x 24 matrices: commutative, unital, NOT associative, and
#  satisfying the Jordan identity (x^2 y) x = x^2 (y x).  All four properties
#  are checked below in exact rational arithmetic.  It is the layer of the
#  Griess algebra that a small machine can carry honestly; the other two
#  layers are counted (§3), not constructed.


class JordanElement:
    """(alpha, S) with S symmetric traceless over Q, as exact Fractions."""

    __slots__ = ("alpha", "S")

    def __init__(self, alpha: F, S: List[List[F]]) -> None:
        self.alpha = F(alpha)
        self.S = [[F(x) for x in row] for row in S]

    # ── constructors ─────────────────────────────────────────────────────────
    @classmethod
    def identity(cls) -> "JordanElement":
        return cls(F(1), [[F(0)] * DIM for _ in range(DIM)])

    @classmethod
    def zero(cls) -> "JordanElement":
        return cls(F(0), [[F(0)] * DIM for _ in range(DIM)])

    @classmethod
    def from_seed(cls, seed: int) -> "JordanElement":
        """A deterministic pseudo-random element (exact, small integers)."""
        state = seed | 1
        M = [[0] * DIM for _ in range(DIM)]
        for i in range(DIM):
            for j in range(i, DIM):
                state = (state * 1103515245 + 12345) & 0x7FFFFFFF
                value = (state >> 16) % 7 - 3
                M[i][j] = value
                M[j][i] = value
        trace = sum(M[i][i] for i in range(DIM))
        S = [[F(M[i][j]) - (F(trace, DIM) if i == j else F(0))
              for j in range(DIM)] for i in range(DIM)]
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        return cls(F((state >> 16) % 5 - 2), S)

    # ── linear structure ─────────────────────────────────────────────────────
    def __add__(self, o: "JordanElement") -> "JordanElement":
        return JordanElement(self.alpha + o.alpha,
                             [[a + b for a, b in zip(r, s)]
                              for r, s in zip(self.S, o.S)])

    def __sub__(self, o: "JordanElement") -> "JordanElement":
        return JordanElement(self.alpha - o.alpha,
                             [[a - b for a, b in zip(r, s)]
                              for r, s in zip(self.S, o.S)])

    def __eq__(self, o: object) -> bool:
        return (isinstance(o, JordanElement) and self.alpha == o.alpha
                and self.S == o.S)

    def is_zero(self) -> bool:
        return self.alpha == 0 and all(x == 0 for row in self.S for x in row)

    def is_traceless(self) -> bool:
        return sum(self.S[i][i] for i in range(DIM)) == 0

    def is_symmetric(self) -> bool:
        return all(self.S[i][j] == self.S[j][i]
                   for i in range(DIM) for j in range(i + 1, DIM))

    def norm_sq(self) -> F:
        return self.alpha ** 2 + sum(x * x for row in self.S for x in row)

    # ── the product ──────────────────────────────────────────────────────────
    def __mul__(self, o: "JordanElement") -> "JordanElement":
        A, B = self.S, o.S
        # P = (AB + BA)/2, symmetric
        P = [[F(0)] * DIM for _ in range(DIM)]
        for i in range(DIM):
            Ai, Bi = A[i], B[i]
            for j in range(i, DIM):
                s = F(0)
                for k in range(DIM):
                    s += Ai[k] * B[k][j] + Bi[k] * A[k][j]
                s = s / 2
                P[i][j] = s
                P[j][i] = s
        tr = sum(P[i][i] for i in range(DIM))
        shift = tr / DIM
        S = [[self.alpha * B[i][j] + o.alpha * A[i][j] + P[i][j]
              - (shift if i == j else F(0)) for j in range(DIM)]
             for i in range(DIM)]
        return JordanElement(self.alpha * o.alpha + shift, S)


def jordan_algebra_report(seeds: Sequence[int] = (11, 29, 47)) -> Dict[str, object]:
    """
    Verify, in exact rational arithmetic, that the 300-dimensional layer is a
    commutative unital Jordan algebra which is NOT associative.
    """
    x, y, z = (JordanElement.from_seed(s) for s in seeds)
    one = JordanElement.identity()

    commutes = (x * y) == (y * x) and (y * z) == (z * y)
    unital = (one * x) == x and (x * one) == x
    closed = all(e.is_symmetric() and e.is_traceless()
                 for e in (x * y, y * z, (x * y) * z))
    assoc_defect = ((x * y) * z) - (x * (y * z))
    associative = assoc_defect.is_zero()
    # Jordan identity: (x^2 y) x = x^2 (y x)
    x2 = x * x
    jordan = ((x2 * y) * x) == (x2 * (y * x))
    return {
        "dimension": 1 + DIM * (DIM + 1) // 2 - 1,
        "commutative": commutes,
        "unital": unital,
        "closed_in_layer": closed,
        "associative": associative,
        "associator_norm_sq": str(assoc_defect.norm_sq()),
        "jordan_identity": jordan,
        "note": "commutative, unital, non-associative, Jordan - the honest "
                "shape of the scalar + traceless-symmetric layer",
    }


# ══════════════════════════════════════════════════════════════════════════════
#  audit
# ══════════════════════════════════════════════════════════════════════════════

def moonshine_audit(full: bool = True) -> Dict[str, object]:
    out: Dict[str, object] = {
        "dimension_ledger": dimension_ledger(),
        "jordan_layer": jordan_algebra_report(),
        "hamming_inner_product": hamming_inner_product_report(512),
    }
    if full:
        out["lines"] = line_census()
        out["class_c_indexing"] = class_c_indexing_report()
        out["voa_head"] = leech_voa_head()
    return out


def _print_audit(full: bool = True) -> Dict[str, object]:
    audit = moonshine_audit(full=full)
    print("=" * 78)
    print("  GLM MOONSHINE  —  Leech / Griess bookkeeping self-audit")
    print("=" * 78)

    led = audit["dimension_ledger"]
    print(f"\n  1 + {led['traceless_sym_dim']} + {led['lines']} + {led['tensor']}"
          f" = {led['total']}   (Griess dimension: {led['ledger_balances']})")
    print(f"  standard representation    : {led['standard_rep']} "
          f"({led['standard_rep_matches']})")

    if full:
        ln = audit["lines"]
        print(f"\n  minimal vectors            : {ln['vectors']} "
              f"(distinct: {ln['all_distinct']})")
        print(f"  closed under negation      : {ln['negation_closed']}, "
              f"self-negative: {ln['self_negative_vectors']}")
        print(f"  lines                      : {ln['lines']} "
              f"{ln['lines_by_class']}")
        cc = audit["class_c_indexing"]
        print(f"  class C indexing injective : {cc['injective']} "
              f"({cc['index_pairs']} = 24 x 4096)")
        vo = audit["voa_head"]
        print(f"\n  J(q) head                  : {vo['J_head']}")
        print(f"  196,884 = {vo['weight_two_split']['oscillator']} + "
              f"{vo['weight_two_split']['lattice']}   "
              f"(matches ledger: {vo['matches_griess_dim']})")

    jl = audit["jordan_layer"]
    print(f"\n  Jordan layer (dim {jl['dimension']})     : commutative="
          f"{jl['commutative']}, unital={jl['unital']}, "
          f"associative={jl['associative']}, Jordan={jl['jordan_identity']}")

    hi = audit["hamming_inner_product"]
    print(f"\n  archive 'inner product'    : {hi['identity']} -> {hi['holds']}")
    print()
    return audit


if __name__ == "__main__":
    import sys
    _print_audit(full="--quick" not in sys.argv)
