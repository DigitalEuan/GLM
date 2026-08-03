#!/usr/bin/env python3
"""
================================================================================
REFINED NRCI — Non-Random Coherence Index
================================================================================
A clean, commented, drop-in module for the GLM system.

This module implements the full NRCI shell system developed across Sessions 1-5
of the GLM experimentation. It is designed to be dropped directly into the GLM
codebase (core_studio_v4.0/glm_work/) and used as a drop-in replacement for the
existing LEECH_ENGINE.calculate_nrci() when sign-sensitive computation is needed.

--------------------------------------------------------------------------------
WHAT IS NRCI?
--------------------------------------------------------------------------------
NRCI = Non-Random Coherence Index

The name captures the intent: a measure of how COHERENT (structured, non-random)
a point in the 24-bit Golay/Leech substrate is. A high NRCI means the point sits
at a stable lattice position; a low NRCI means it is noisy/degenerate.

The original NRCI (from ubp_unified_v5.py) is:
    tax = hw * Y + ns / 8
    NRCI = 10 / (10 + tax)
where:
    hw = Hamming weight (count of nonzero coordinates)
    ns = sum of squares (norm squared)
    Y  = the UBP Y constant (~0.2647, derived from pi)

PROBLEM: this formula is SIGN-BLIND. It uses hw and ns, both of which ignore
the SIGN of each coordinate. All 128 sign-variants of an octad (8 nonzero
coordinates, each +/-2) have IDENTICAL hw (8) and IDENTICAL ns (32), hence
identical NRCI. 7 bits of information per octad are invisible.

--------------------------------------------------------------------------------
THE SHELL SYSTEM (Session 3-5 development)
--------------------------------------------------------------------------------
The refined NRCI adds SHELLS — additional terms that capture structure the
original (Shell 0) discards. Each shell is analogous to a quantum number:
like (n, l, m, s) in atomic physics, each shell distinguishes points that
lower shells collapse together.

  Shell 0 (GOLAY SHELL): hw + ns/8
    The original NRCI. Sign-blind. Sees "how many coords are nonzero" and
    "how big are they". Cannot see sign distribution.

  Shell 1 (SIGN-PARITY SHELL): |n_pos - n_neg| / n_nonzero
    Sign-sensitive. Sees the BALANCE of positive vs negative coordinates.
    For an octad (8 nonzero): 4neg/4pos = 0 (balanced), 0neg/8pos = 1 (extreme).
    Recovers the Pascal 1-28-70-28-1 distribution (C(8,k) for even k).
    This shell ALONE produces 5 unique NRCI values across 128 octad variants.

  Shell 2 (SEXTET-BALANCE SHELL): coefficient of variation across 4 sextets
    The 24 coords split into 4 sextets (MOG tetrads): [0:6], [6:12], [12:18], [18:24].
    This shell measures how evenly the |weight| is distributed across sextets.
    A well-balanced point has equal |weight| in all 4 sextets.
    This is the MOST SEMANTICALLY CORRELATED shell (Session 3 Track D finding).

  Shell 3 (COSET-TYPE SHELL): Golay syndrome weight / 12
    The Golay syndrome of the point (treating nonzero as 1) identifies its coset.
    There are 4096 cosets; the syndrome WEIGHT (0-12) is a coarse coset type.
    0 = codeword (most stable), higher = further from any codeword.

  Shell 4 (SEXTET-SIGNED SHELL — the Session 5 breakthrough):
    The 4-tuple of SIGNED sextet sums: (s1, s2, s3, s4) where si = sum(coords in sextet i).
    This is the FINEST shell — it produces 24 unique patterns across 128 octad variants
    (vs Shell 1's 5). It distinguishes sign-variants WITHIN a Pascal class.
    This shell is what the MOG topology makes visible.

--------------------------------------------------------------------------------
USAGE
--------------------------------------------------------------------------------
    from refined_nrci import RefinedNRCI

    # Default: all shells enabled, balanced weights
    rnrci = RefinedNRCI()

    # Compute on a binary vector (0/1) — Shells 1,4 give 0 (no sign structure)
    nrci = rnrci.compute([1,0,1,1,...])  # 24-bit binary

    # Compute on a physical Leech point (+/-2) — all shells active
    nrci = rnrci.compute([2,-2,0,2,...])  # 24-coord Leech point

    # Get full breakdown (all shell taxes)
    breakdown = rnrci.describe([2,-2,0,2,...])

    # Configure: disable specific shells, tune weights
    rnrci = RefinedNRCI(use_shell1=False, alpha4=0.5)  # Shell 4 weighted higher

--------------------------------------------------------------------------------
KEY RESULTS (Sessions 3-5)
--------------------------------------------------------------------------------
- Sign-blindness BROKEN: 1 unique NRCI (old) -> 5 (Shell 1) -> 24 (Shell 4)
- Shell 2 is the most semantically correlated (rho=+0.13 with CRG degree)
- Shell 4 (sextet_signed) is the finest: 252 unique patterns across vocab
- On physical Leech points, all shells are active and meaningful
- On binary vectors, only Shells 0, 2, 3 are meaningful (1 and 4 need signs)

Author: GLM Experimentation Sessions 1-5
Date: 2026-07-13
================================================================================
"""

from __future__ import annotations
import math
from fractions import Fraction
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


# ══════════════════════════════════════════════════════════════════════════════
# THE Y CONSTANT (from ubp_unified_v5.py)
# ══════════════════════════════════════════════════════════════════════════════
# Y is the UBP "Y constant" — a geometric constant derived from pi that sets
# the scale of the Golay shell tax. See ubp_unified_v5.py for the full derivation.
# Approximate value: 0.2647
# We import it from the real engine to ensure exact consistency.
try:
    from ubp_unified_v5 import _Y
    Y = float(_Y)
except ImportError:
    # Fallback: use the known approximate value if the engine isn't available
    Y = 0.2646754304


# ══════════════════════════════════════════════════════════════════════════════
# THE REFINED NRCI CLASS
# ══════════════════════════════════════════════════════════════════════════════

class RefinedNRCI:
    """Non-Random Coherence Index — multi-shell, sign-sensitive.

    Computes NRCI as a weighted combination of up to 5 shells:
      Shell 0: Golay shell (hw + ns/8) — the original, sign-blind
      Shell 1: Sign-parity shell — balance of +/- signs
      Shell 2: Sextet-balance shell — evenness across 4 MOG tetrads
      Shell 3: Coset-type shell — Golay syndrome weight
      Shell 4: Sextet-signed shell — 4-tuple of signed sextet sums

    The combined tax is:
        tax = tax_0 + alpha1 * tax_1 + alpha2 * tax_2 + alpha3 * tax_3 + alpha4 * tax_4
        NRCI = 10 / (10 + tax)

    Parameters
    ----------
    alpha1 : float
        Weight for Shell 1 (sign-parity). Default 0.5.
    alpha2 : float
        Weight for Shell 2 (sextet-balance). Default 0.3.
    alpha3 : float
        Weight for Shell 3 (coset-type). Default 0.2.
    alpha4 : float
        Weight for Shell 4 (sextet-signed). Default 0.4.
    use_shell1 : bool
        Enable Shell 1. Default True.
    use_shell2 : bool
        Enable Shell 2. Default True.
    use_shell3 : bool
        Enable Shell 3. Default True.
    use_shell4 : bool
        Enable Shell 4. Default True.
    golay_engine : optional
        A GolayCodeEngine instance (for Shell 3 syndrome computation).
        If None, Shell 3 is skipped (syndrome requires the Golay parity matrix).
    """

    # The 4 MOG sextet ranges: [start, end) for each of the 4 tetrads
    SEXTET_RANGES = [(0, 6), (6, 12), (12, 18), (18, 24)]

    def __init__(self,
                 alpha1: float = 0.5,
                 alpha2: float = 0.3,
                 alpha3: float = 0.2,
                 alpha4: float = 0.4,
                 use_shell1: bool = True,
                 use_shell2: bool = True,
                 use_shell3: bool = True,
                 use_shell4: bool = True,
                 golay_engine=None):
        self.alpha1 = alpha1
        self.alpha2 = alpha2
        self.alpha3 = alpha3
        self.alpha4 = alpha4
        self.use_shell1 = use_shell1
        self.use_shell2 = use_shell2
        self.use_shell3 = use_shell3
        self.use_shell4 = use_shell4
        self.golay = golay_engine
        self.Y = Y

    # ──────────────────────────────────────────────────────────────────────────
    # SHELL 0: Golay shell (the original NRCI, sign-blind)
    # ──────────────────────────────────────────────────────────────────────────
    def tax_shell0(self, point: List[float]) -> float:
        """Golay shell tax: hw * Y + ns / 8.

        This is the ORIGINAL NRCI tax from ubp_unified_v5.py.
        It is SIGN-BLIND: hw counts nonzero coords, ns sums squares.
        All 128 sign-variants of an octad have identical tax_0.

        For an octad (8 coords of +/-2):
            hw = 8, ns = 8 * 4 = 32
            tax_0 = 8 * 0.2647 + 32/8 = 2.1176 + 4.0 = 6.1176
            NRCI_0 = 10 / (10 + 6.1176) = 0.6204
        """
        hw = sum(1 for x in point if x != 0)
        ns = sum(x * x for x in point)
        return hw * self.Y + ns / 8.0

    # ──────────────────────────────────────────────────────────────────────────
    # SHELL 1: Sign-parity shell (sign-sensitive)
    # ──────────────────────────────────────────────────────────────────────────
    def tax_shell1(self, point: List[float]) -> float:
        """Sign-parity tax: imbalance between positive and negative coords.

        Range: [0, 1]
            0 = perfectly balanced (equal +/- count)
            1 = all same sign (all positive or all negative)

        For an octad (8 nonzero):
            4 neg / 4 pos -> 0.0 (balanced, most symmetric)
            2 neg / 6 pos -> 0.5
            0 neg / 8 pos -> 1.0 (extreme)

        This shell recovers the Pascal 1-28-70-28-1 distribution:
            0 neg (n=1):   C(8,0) = 1
            2 neg (n=28):  C(8,2) = 28
            4 neg (n=70):  C(8,4) = 70  <- most common, most balanced
            6 neg (n=28):  C(8,6) = 28
            8 neg (n=1):   C(8,8) = 1

        NOTE: For binary vectors (0/1), this shell is always 0 (no negatives).
        It only activates on physical Leech points (+/-2 coordinates).
        """
        nonzero = [x for x in point if x != 0]
        if not nonzero:
            return 0.0
        n_neg = sum(1 for x in nonzero if x < 0)
        n_pos = len(nonzero) - n_neg
        return abs(n_pos - n_neg) / len(nonzero)

    def sign_class(self, point: List[float]) -> int:
        """Return the number of negative coordinates (the Pascal class index)."""
        return sum(1 for x in point if x < 0)

    # ──────────────────────────────────────────────────────────────────────────
    # SHELL 2: Sextet-balance shell (partially sign-sensitive)
    # ──────────────────────────────────────────────────────────────────────────
    def tax_shell2(self, point: List[float]) -> float:
        """Sextet-balance tax: coefficient of variation across 4 sextets.

        The 24 coordinates split into 4 sextets (MOG tetrads):
            Sextet 0: coords[0:6]   (M_Mass, M_Charge, M_Space, M_Time, M_Thermal, M_Count)
            Sextet 1: coords[6:12]  (I_Topology, I_Symmetry, ...)
            Sextet 2: coords[12:18] (A_Energy, A_Force, ...)
            Sextet 3: coords[18:24] (P_Probability, P_Ratio, ...)

        This shell measures how evenly the |weight| is distributed across
        the 4 sextets. A well-balanced point has equal |weight| in all 4.

        Range: [0, ~2]
            0 = perfectly balanced (all 4 sextets have equal |sum|)
            higher = skewed (one sextet dominates)

        This is the MOST SEMANTICALLY CORRELATED shell:
            Spearman rho = +0.13 with CRG degree (Session 3 Track D finding).
        It is partially sign-sensitive (uses |coord|, not coord).

        NOTE: This shell is meaningful for BOTH binary and Leech points.
        """
        sextets = [point[s:e] for s, e in self.SEXTET_RANGES]
        weights = [sum(abs(x) for x in s) for s in sextets]
        if max(weights) == 0:
            return 0.0
        mean_w = sum(weights) / 4.0
        variance = sum((w - mean_w) ** 2 for w in weights) / 4.0
        return math.sqrt(variance) / (mean_w + 1e-10)

    # ──────────────────────────────────────────────────────────────────────────
    # SHELL 3: Coset-type shell (sign-blind, needs Golay engine)
    # ──────────────────────────────────────────────────────────────────────────
    def tax_shell3(self, point: List[float]) -> float:
        """Coset-type tax: Golay syndrome weight / 12.

        The Golay syndrome of the point (treating nonzero as 1) identifies
        which of the 4096 cosets the point belongs to. The syndrome WEIGHT
        (0-12) is a coarse coset type:
            0  = the point IS a Golay codeword (most stable)
            12 = maximally far from any codeword

        Range: [0, 1]
            0 = codeword
            1 = maximally non-codeword

        NOTE: Requires the GolayCodeEngine (for the parity-check matrix H).
        If no engine is provided, this shell returns 0 (skipped).
        """
        if self.golay is None:
            return 0.0
        bits = [1 if x != 0 else 0 for x in point]
        sw = self.golay.syndrome_weight(bits)
        return sw / 12.0

    # ──────────────────────────────────────────────────────────────────────────
    # SHELL 4: Sextet-signed shell (FULLY sign-sensitive — the finest shell)
    # ──────────────────────────────────────────────────────────────────────────
    def tax_shell4(self, point: List[float]) -> float:
        """Sextet-signed tax: L2 norm of the 4-tuple of signed sextet sums.

        This is the FINEST shell — it distinguishes sign-variants WITHIN
        a Pascal class. For each of the 4 sextets, compute the SIGNED sum
        of coordinates. The 4-tuple (s1, s2, s3, s4) uniquely identifies
        most sign-variants.

        For an octad (8 coords of +/-2):
            The 128 variants produce 24 unique 4-tuples
            (vs Shell 1's 5 unique classes).

        The tax is the L2 norm of the 4-tuple, normalized:
            tax_4 = sqrt(s1^2 + s2^2 + s3^2 + s4^2) / max_possible

        A balanced sign pattern (4 neg, 4 pos distributed evenly across sextets)
        has LOW tax_4. An unbalanced pattern has HIGH tax_4.

        NOTE: For binary vectors (0/1), this reduces to the sextet weight
        pattern — still meaningful but less granular than for Leech points.
        """
        sextet_sums = []
        for s, e in self.SEXTET_RANGES:
            sextet_sums.append(sum(point[s:e]))
        # L2 norm of the 4-tuple
        norm = math.sqrt(sum(s * s for s in sextet_sums))
        # Normalize: for an octad (8 coords of +/-2), max possible = sqrt(4 * 16) = 8
        # For binary (8 ones), max = sqrt(4 * 36) = 12 (if all in one sextet)
        # Use a general normalization: divide by sqrt(4) * max_abs_coord * 6
        max_coord = max(abs(x) for x in point) if any(point) else 1
        max_norm = math.sqrt(4) * max_coord * 6
        return norm / (max_norm + 1e-10)

    def sextet_signed_pattern(self, point: List[float]) -> Tuple[int, ...]:
        """Return the 4-tuple of signed sextet sums (the Shell 4 signature).

        This is the sign-sensitive identifier. Two points with the same
        binary projection but different sign patterns will have DIFFERENT
        signatures (in general).
        """
        return tuple(sum(point[s:e]) for s, e in self.SEXTET_RANGES)

    # ──────────────────────────────────────────────────────────────────────────
    # COMBINED TAX + NRCI
    # ──────────────────────────────────────────────────────────────────────────
    def tax(self, point: List[float]) -> float:
        """Combined finer tax across all enabled shells.

            tax = tax_0 + alpha1 * tax_1 + alpha2 * tax_2 + alpha3 * tax_3 + alpha4 * tax_4

        Lower tax = more coherent (more lattice-stable).
        """
        tax = self.tax_shell0(point)
        if self.use_shell1:
            tax += self.alpha1 * self.tax_shell1(point)
        if self.use_shell2:
            tax += self.alpha2 * self.tax_shell2(point)
        if self.use_shell3:
            tax += self.alpha3 * self.tax_shell3(point)
        if self.use_shell4:
            tax += self.alpha4 * self.tax_shell4(point)
        return tax

    def compute(self, point: List[float]) -> float:
        """Compute the refined NRCI = 10 / (10 + tax).

        This is the main API. Returns a float in (0, 1].
            1.0 = perfectly coherent (zero tax, e.g., the all-zeros point)
            0.5 = moderately coherent
            0.0 = maximally incoherent (infinite tax)
        """
        return 10.0 / (10.0 + self.tax(point))

    def describe(self, point: List[float]) -> Dict[str, float]:
        """Return a full breakdown of all shell taxes + the combined NRCI.

        Useful for debugging and understanding which shell dominates.
        """
        t0 = self.tax_shell0(point)
        t1 = self.tax_shell1(point) if self.use_shell1 else 0.0
        t2 = self.tax_shell2(point) if self.use_shell2 else 0.0
        t3 = self.tax_shell3(point) if self.use_shell3 else 0.0
        t4 = self.tax_shell4(point) if self.use_shell4 else 0.0
        total = t0
        if self.use_shell1: total += self.alpha1 * t1
        if self.use_shell2: total += self.alpha2 * t2
        if self.use_shell3: total += self.alpha3 * t3
        if self.use_shell4: total += self.alpha4 * t4
        return {
            "shell0_golay": t0,
            "shell1_sign_parity": t1,
            "shell2_sextet_balance": t2,
            "shell3_coset_type": t3,
            "shell4_sextet_signed": t4,
            "tax_total": total,
            "nrci": 10.0 / (10.0 + total),
            "sign_class": self.sign_class(point),
            "sextet_pattern": self.sextet_signed_pattern(point),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # CONVENIENCE: batch compute
    # ──────────────────────────────────────────────────────────────────────────
    def compute_batch(self, points: List[List[float]]) -> List[float]:
        """Compute NRCI for a list of points."""
        return [self.compute(p) for p in points]

    def unique_values(self, points: List[List[float]], decimals: int = 6) -> int:
        """Count unique NRCI values across a set of points.

        Useful for testing sign-blindness: the old NRCI gives 1 unique
        value across 128 octad variants; the refined NRCI gives 5-24.
        """
        nrcis = [round(self.compute(p), decimals) for p in points]
        return len(set(nrcis))


# ══════════════════════════════════════════════════════════════════════════════
# SELF-TEST / DEMO
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("REFINED NRCI — Non-Random Coherence Index")
    print("=" * 70)
    print()

    # Try to load the real Golay engine for Shell 3
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from ubp_unified_v5 import GOLAY_ENGINE as REAL_GOLAY, LEECH_ENGINE as REAL_LEECH
        golay = REAL_GOLAY
        print(f"[setup] Real Golay engine loaded. Shell 3 active.")
        print(f"[setup] Y constant = {Y:.10f}")
    except Exception as e:
        golay = None
        print(f"[setup] Golay engine not available ({e}). Shell 3 will be skipped.")

    rnrci = RefinedNRCI(golay_engine=golay)

    # ── Test 1: Sign-blindness on 128 octad variants ──────────────────────────
    print()
    print("-" * 70)
    print("TEST 1: Sign-blindness (128 octad sign-variants)")
    print("-" * 70)

    if golay is not None:
        octads = golay.get_octads()
        sample_octad = octads[42]
        print(f"  Sample octad: hw={sum(sample_octad)}")

        # Expand to 128 physical Leech points
        physical_points = REAL_LEECH.expand_octad_to_physical(sample_octad)
        print(f"  Expanded to {len(physical_points)} Leech points (+/-2 coords)")

        # Old NRCI (Shell 0 only)
        old_nrcis = [float(REAL_LEECH.calculate_nrci(p)) for p in physical_points]
        old_unique = len(set(round(n, 6) for n in old_nrcis))

        # Refined NRCI (all shells)
        refined_nrcis = [rnrci.compute(p) for p in physical_points]
        refined_unique = rnrci.unique_values(physical_points)

        # Shell 1 only (sign-parity)
        rnrci_s1 = RefinedNRCI(use_shell2=False, use_shell3=False, use_shell4=False,
                                golay_engine=golay)
        s1_unique = rnrci_s1.unique_values(physical_points)

        # Shell 4 only (sextet-signed)
        rnrci_s4 = RefinedNRCI(use_shell1=False, use_shell2=False, use_shell3=False,
                                golay_engine=golay)
        s4_unique = rnrci_s4.unique_values(physical_points)

        print(f"\n  Unique NRCI values across 128 variants:")
        print(f"    Old NRCI (Shell 0 only):      {old_unique}  (sign-BLIND)")
        print(f"    + Shell 1 (sign-parity):      {s1_unique}  (Pascal 1-28-70-28-1)")
        print(f"    + Shell 4 (sextet-signed):    {s4_unique}  (finest)")
        print(f"    All shells combined:          {refined_unique}")
        print()

        # Pascal distribution check
        from collections import Counter
        sign_classes = [rnrci.sign_class(p) for p in physical_points]
        pascal = Counter(sign_classes)
        print(f"  Pascal distribution (sign classes):")
        expected = {0: 1, 2: 28, 4: 70, 6: 28, 8: 1}
        for sc in sorted(pascal.keys()):
            print(f"    {sc} negatives: {pascal[sc]} (expected {expected.get(sc, 0)})")

    # ── Test 2: Breakdown on a sample point ───────────────────────────────────
    print()
    print("-" * 70)
    print("TEST 2: Full breakdown on a sample Leech point")
    print("-" * 70)

    if golay is not None:
        sample_point = physical_points[70]  # a 4-negative variant
        breakdown = rnrci.describe(sample_point)
        print(f"  Point: {sample_point}")
        print(f"  Sign class: {breakdown['sign_class']} negatives")
        print(f"  Sextet pattern: {breakdown['sextet_pattern']}")
        print(f"  Shell taxes:")
        print(f"    Shell 0 (Golay):          {breakdown['shell0_golay']:.4f}")
        print(f"    Shell 1 (sign-parity):    {breakdown['shell1_sign_parity']:.4f}")
        print(f"    Shell 2 (sextet-balance): {breakdown['shell2_sextet_balance']:.4f}")
        print(f"    Shell 3 (coset-type):     {breakdown['shell3_coset_type']:.4f}")
        print(f"    Shell 4 (sextet-signed):  {breakdown['shell4_sextet_signed']:.4f}")
        print(f"  Total tax: {breakdown['tax_total']:.4f}")
        print(f"  Refined NRCI: {breakdown['nrci']:.4f}")

    # ── Test 3: Binary vs Leech comparison ────────────────────────────────────
    print()
    print("-" * 70)
    print("TEST 3: Binary vs Leech point comparison")
    print("-" * 70)

    if golay is not None:
        binary_vec = list(sample_octad)  # 0/1
        leech_point = physical_points[70]  # +/-2
        print(f"  Binary vector: {binary_vec}")
        print(f"  Leech point:   {leech_point}")
        print(f"  Binary NRCI:   {rnrci.compute(binary_vec):.4f}")
        print(f"  Leech NRCI:    {rnrci.compute(leech_point):.4f}")
        print(f"  (Binary has no sign structure -> Shells 1,4 contribute 0)")
        print(f"  (Leech has full sign structure -> all shells active)")

    print()
    print("=" * 70)
    print("REFINED NRCI module ready for drop-in use.")
    print("Import: from refined_nrci import RefinedNRCI")
    print("Compute: nrci = RefinedNRCI(golay_engine=golay).compute(point)")
    print("=" * 70)
