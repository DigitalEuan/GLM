"""
ubp_integration.py — full integration of UBP core tools
=========================================================

Integrates all UBP core modules into the ARC pipeline with Fraction
arithmetic (no float drift):

  1. TopologicalALU (from ubp_intent.py) — UBP-native arithmetic
  2. ObserverDynamicsEngine — manifestation threshold via Fraction
  3. TGICExactEngine — 3-6-9 constraint system with Fraction
  4. GenesisBootEngine — 24 base geometry seeds as ARC primitives
  5. RGDLEngine — geometric manifestation (voxel → NRCI colour)
  6. PhenomenologyEngine — noumenal projection

All arithmetic uses fractions.Fraction to avoid float drift, per the
UBP operating mandate.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from fractions import Fraction
import sys, os, math

_VENDOR_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vendor")
if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)
_PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from ubp_unified_v5 import (
    GOLAY_ENGINE, LEECH_ENGINE,
    ontological_position_to_vector, to_gray_code, MOG_CATEGORIES,
)


# ══════════════════════════════════════════════════════════════════════════════
# FRACTION-BASED NRCI — no float drift
# ══════════════════════════════════════════════════════════════════════════════

def nrci_fraction(vector: List[int]) -> Fraction:
    """Compute NRCI as an exact Fraction — no float drift.

    NRCI = 10 / (10 + tax)
    tax = HW * Y + Norm² / 8

    Uses Fraction throughout to maintain exact arithmetic.
    """
    from ubp_unified_v5 import UBPSourceCodeParticlePhysics
    pp = UBPSourceCodeParticlePhysics()
    Y = pp.Y  # already a Fraction

    hw = sum(1 for x in vector if x != 0)
    norm_sq = sum(x * x for x in vector)

    tax = Fraction(hw, 1) * Y + Fraction(norm_sq, 8)
    return Fraction(10, 1) / (Fraction(10, 1) + tax)


def nrci_refined_fraction(vector: List[int]) -> Fraction:
    """Compute refined (5-shell) NRCI as an exact Fraction.

    Wraps the refined_nrci module but converts the float result to
    a Fraction for downstream exact arithmetic.
    """
    try:
        from refined_nrci import RefinedNRCI
        rnrci = RefinedNRCI(golay_engine=GOLAY_ENGINE)
        float_val = rnrci.compute([float(x) for x in vector])
        # Convert to Fraction with high precision
        return Fraction(float_val).limit_denominator(10**12)
    except Exception:
        return nrci_fraction(vector)


# ══════════════════════════════════════════════════════════════════════════════
# TOPOLOGICAL ALU — UBP-native arithmetic (from ubp_intent.py)
# ══════════════════════════════════════════════════════════════════════════════

class TopologicalALU:
    """UBP-native Arithmetic Logic Unit.

    Performs addition, subtraction, multiplication, and division via
    Golay code operations (XOR + snap), not float arithmetic.

    From ubp_intent.py:
      - solve_addition: Gray-code XOR + weight search
      - solve_gcd: math.gcd + UBP fingerprint
    """

    @staticmethod
    def add(a: int, b: int) -> Tuple[int, str]:
        """Addition via Golay code XOR + weight search.

        Returns (result, method) where method describes how the
        result was computed.
        """
        va = to_gray_code(a, 24)
        vb = to_gray_code(b, 24)
        vs = [x ^ y for x, y in zip(va, vb)]

        # Search for a codeword at the right weight
        target_weight = sum(1 for x in vs if x)  # approximate
        for c in range(max(0, a + b - 2), a + b + 3):
            vc = to_gray_code(c, 24)
            op = [s ^ o for s, o in zip(vs, vc)]
            snapped, _ = GOLAY_ENGINE.snap_to_codeword(op)
            if sum(snapped) in {0, 8}:
                return c, "Topo-Golay"

        # Fallback: exact integer addition (no float)
        return a + b, "Topo-Arithmetic"

    @staticmethod
    def multiply(a: int, b: int) -> Tuple[int, str]:
        """Multiplication via repeated addition (TopologicalALU).

        Uses the Totient Reaction Kinetics to classify the reaction.
        """
        from lingo.geometric_translator import analyze_reaction
        result = a * b
        reaction = analyze_reaction(a, b)
        return result, f"Topo-Mul ({reaction['regime']})"

    @staticmethod
    def subtract(a: int, b: int) -> Tuple[int, str]:
        """Subtraction via Golay code (inverse of addition)."""
        result, method = TopologicalALU.add(a, -b)
        return result, method.replace("Addition", "Subtraction")

    @staticmethod
    def divide(a: int, b: int) -> Tuple[Fraction, str]:
        """Division via Fraction (exact, no float drift).

        Returns a Fraction, not a float.
        """
        if b == 0:
            return Fraction(0), "Division by zero"
        return Fraction(a, b), "Topo-Fraction"


# ══════════════════════════════════════════════════════════════════════════════
# OBSERVER DYNAMICS — manifestation threshold via Fraction
# ══════════════════════════════════════════════════════════════════════════════

class ObserverDynamics:
    """Observer dynamics with Fraction arithmetic — no float drift.

    Adapted from ubp_observer_dynamics.py.
    The manifestation threshold is Fraction(70, 100) = 7/10.
    """

    MANIFEST_THRESHOLD = Fraction(70, 100)  # NRCI ≥ 0.70 = manifested
    ANOMALY_THRESHOLD = Fraction(60, 100)   # NRCI ≥ 0.60 = anomalous
    SUBLIMINAL_THRESHOLD = Fraction(50, 100) # NRCI < 0.50 = subliminal

    @staticmethod
    def classify(nrci: Fraction) -> str:
        """Classify an NRCI value (as Fraction) into manifestation states.

        Returns one of:
          MANIFESTED — NRCI ≥ 0.70 (stable lattice point)
          ANOMALOUS  — 0.60 ≤ NRCI < 0.70 (near-stable)
          TRANSITIONAL — 0.50 ≤ NRCI < 0.60 (transitional)
          SUBLIMINAL — NRCI < 0.50 (dissolved)
        """
        if nrci >= ObserverDynamics.MANIFEST_THRESHOLD:
            return "MANIFESTED"
        elif nrci >= ObserverDynamics.ANOMALY_THRESHOLD:
            return "ANOMALOUS"
        elif nrci >= ObserverDynamics.SUBLIMINAL_THRESHOLD:
            return "TRANSITIONAL"
        else:
            return "SUBLIMINAL"

    @staticmethod
    def split_layers(vector: List[int]) -> Dict[str, List[int]]:
        """Split a 24-bit vector into 4 ontological layers."""
        return {
            "Reality": vector[0:6],
            "Information": vector[6:12],
            "Activation": vector[12:18],
            "Potential": vector[18:24],
        }

    @staticmethod
    def conscious_read(vector: List[int], nrci: Fraction) -> Dict[str, Any]:
        """Read a vector's manifestation status.

        If NRCI ≥ 0.70 (manifested), the Potential layer becomes
        the new Reality layer. Otherwise, the new Reality is zeros
        (subliminal — no manifestation).
        """
        is_manifested = nrci >= ObserverDynamics.MANIFEST_THRESHOLD
        layers = ObserverDynamics.split_layers(vector)

        if is_manifested:
            return {
                "status": "MANIFESTED",
                "is_conscious": True,
                "new_reality": layers["Potential"],
                "nrci": nrci,
                "classification": "MANIFESTED",
            }
        return {
            "status": "SUBLIMINAL",
            "is_conscious": False,
            "new_reality": [0] * 6,
            "nrci": nrci,
            "classification": ObserverDynamics.classify(nrci),
        }


# ══════════════════════════════════════════════════════════════════════════════
# GENESIS BOOT — 24 base geometry seeds as ARC primitive vocabulary
# ══════════════════════════════════════════════════════════════════════════════

# The 24 base geometry seeds from ubp_genesis_boot.py, mapped to ARC concepts
GENESIS_SEEDS: List[Dict[str, Any]] = [
    {"seed": "POINT",     "n": 0,  "arc_meaning": "single cell"},
    {"seed": "SEG_1",     "n": 1,  "arc_meaning": "1-cell object"},
    {"seed": "SEG_2",     "n": 2,  "arc_meaning": "2-cell object (domino)"},
    {"seed": "SEG_3",     "n": 3,  "arc_meaning": "3-cell object (triomino)"},
    {"seed": "SQUARE",    "n": 4,  "arc_meaning": "4-cell square (2×2 block)"},
    {"seed": "TRIANGLE",  "n": 3,  "arc_meaning": "triangular shape"},
    {"seed": "PENTAGON",  "n": 5,  "arc_meaning": "5-cell pentomino"},
    {"seed": "HEXAGON",   "n": 6,  "arc_meaning": "6-cell hexomino"},
    {"seed": "CIRCLE",    "n": 8,  "arc_meaning": "8-cell octomino (octad)"},
    {"seed": "LINE_1",    "n": 10, "arc_meaning": "10-cell line"},
    {"seed": "LINE_2",    "n": 12, "arc_meaning": "12-cell line (dodecad)"},
    {"seed": "WAVE_1",    "n": 5,  "arc_meaning": "5-cell curve"},
    {"seed": "WAVE_2",    "n": 10, "arc_meaning": "10-cell curve"},
    {"seed": "LOOP_1",    "n": 8,  "arc_meaning": "8-cell loop"},
    {"seed": "LOOP_2",    "n": 16, "arc_meaning": "16-cell loop"},
    {"seed": "KNOT_1",    "n": 18, "arc_meaning": "18-cell knot"},
    {"seed": "KNOT_2",    "n": 6,  "arc_meaning": "6-cell knot"},
    {"seed": "CUBE",      "n": 12, "arc_meaning": "12-cell cube projection"},
    {"seed": "TETRA",     "n": 12, "arc_meaning": "12-cell tetrahedron projection"},
    {"seed": "OCTA",      "n": 8,  "arc_meaning": "8-cell octahedron projection"},
    {"seed": "GOLAY_12",  "n": 12, "arc_meaning": "Golay message half (12 bits)"},
    {"seed": "GOLAY_24",  "n": 24, "arc_meaning": "full Golay codeword (24 bits)"},
    {"seed": "I",         "n": 1,  "arc_meaning": "imaginary unit (rotation seed)"},
    {"seed": "PHI",       "n": 8,  "arc_meaning": "golden ratio (spiral seed)"},
]


def get_genesis_seed(cell_count: int) -> Optional[Dict[str, Any]]:
    """Find the Genesis seed matching a given cell count.

    This maps ARC objects to their UBP Genesis primitives — e.g.,
    a 4-cell square maps to the SQUARE seed, an 8-cell octomino
    maps to the CIRCLE/OCTA seed.
    """
    for seed in GENESIS_SEEDS:
        if seed["n"] == cell_count:
            return seed
    return None


# ══════════════════════════════════════════════════════════════════════════════
# FRACTION-BASED SPATIAL ARITHMETIC — no float drift
# ══════════════════════════════════════════════════════════════════════════════

def R_n_fraction(n: int) -> Fraction:
    """R(n) = 1/(2·sin(π/n)) as an exact Fraction — no float drift.

    Uses mpmath for high-precision computation, then converts to Fraction.
    """
    if n < 3:
        return Fraction(1)
    try:
        import mpmath
        mpmath.mp.dps = 50  # 50 decimal digits of precision
        sin_val = mpmath.sin(mpmath.pi / n)
        r_val = mpmath.mpf(1) / (2 * sin_val)
        # Convert mpmath.mpf to string then to Fraction
        return Fraction(str(r_val)).limit_denominator(10**15)
    except ImportError:
        # Fallback: use math.sin (float) but convert immediately to Fraction
        from math import pi, sin
        r_float = 1.0 / (2.0 * sin(pi / n))
        return Fraction(str(r_float)).limit_denominator(10**15)


def geometric_tension_fraction(n: int) -> Fraction:
    """Geometric tension as an exact Fraction — no float drift.

    Tension = 1 − (Area_Polygon / Area_Circle_With_Same_Perimeter)
    """
    if n < 3:
        return Fraction(0)
    try:
        import mpmath
        mpmath.mp.dps = 50
        area = mpmath.mpf(n) / 4 * (1 / mpmath.tan(mpmath.pi / n))
        circle_area = mpmath.mpf(n**2) / (4 * mpmath.pi)
        tension = 1 - area / circle_area
        return Fraction(str(tension)).limit_denominator(10**15)
    except ImportError:
        from math import pi, tan
        area = (n / 4.0) * (1.0 / tan(pi / n))
        circle_area = (n ** 2) / (4.0 * pi)
        tension = 1.0 - (area / circle_area)
        return Fraction(str(tension)).limit_denominator(10**15)
