#!/usr/bin/env python3
"""
GLM v8 — Honest Rewrite Addressing GA Feedback.

Changes from v7:
1. Dimensional analysis presented FIRST (classical, no overclaiming)
2. Golay encoding presented as OPTIONAL representation layer (the novel part)
3. Mod-2 ceiling acknowledged as self-inflicted (honest)
4. Two headline theorems stated formally
5. Threat model for error correction defined
6. Syndrome connected to dynamics (σ as residual)
7. No "100% precision" overclaiming — that's what dimensional analysis gives

Per reviewer: "The best path is to let GA's rigor discipline GLM's real ideas."
"""

import sys
import json
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from fractions import Fraction

sys.path.insert(0, str(Path("/home/z/my-project/scripts")))
sys.path.insert(0, str(Path("/home/z/my-project/download/arc_agi_17")))

from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE


# ══════════════════════════════════════════════════════════════════════════════
# PART I: CLASSICAL DIMENSIONAL ANALYSIS (no Golay needed)
# ══════════════════════════════════════════════════════════════════════════════

DIM_NAMES = ["L", "M", "T", "I", "Θ", "N", "J"]


@dataclass
class Quantity:
    """A physical quantity with SI dimensions.

    This is CLASSICAL dimensional analysis (Buckingham-Pi / Kracht formalism).
    No Golay code, no error correction, no binary encoding — just integers.

    The group (Z⁷, +) with d(A·B) = d(A) + d(B) is standard.
    """
    name: str
    dimensions: List[int]  # [L, M, T, I, Θ, N, J]

    def dims_str(self) -> str:
        parts = []
        for n, e in zip(DIM_NAMES, self.dimensions):
            if e == 1: parts.append(n)
            elif e != 0: parts.append(f"{n}^{e}")
        return "·".join(parts) if parts else "dimensionless"


def compose(a: Quantity, b: Quantity, op: str = "multiply") -> Quantity:
    """Compose quantities via addition (deterministic, information-preserving).

    This is the group homomorphism d(A·B) = d(A) + d(B).
    NOT XOR — addition is invertible (subtraction recovers the original).
    """
    if op == "multiply":
        dims = [x + y for x, y in zip(a.dimensions, b.dimensions)]
        name = f"({a.name}·{b.name})"
    elif op == "divide":
        dims = [x - y for x, y in zip(a.dimensions, b.dimensions)]
        name = f"({a.name}/{b.name})"
    else:
        raise ValueError(f"Unknown operation: {op}")
    return Quantity(name=name, dimensions=dims)


def check_equation(lhs: Quantity, rhs: Quantity) -> bool:
    """Check dimensional homogeneity. This is classical — any correct
    implementation gives the same result. No overclaiming here."""
    return lhs.dimensions == rhs.dimensions


# ══════════════════════════════════════════════════════════════════════════════
# THEOREM 1: Reversible Composition (headline structural property)
# ══════════════════════════════════════════════════════════════════════════════

def verify_reversibility() -> bool:
    """Theorem 1: For all a, b ∈ Z⁷: subtract(add(a,b),b) = a.

    This is the group property that makes composition reversible.
    It parallels GA's invertible geometric product.

    Proof: integer addition forms a group (Z⁷, +). The inverse of +b is -b.
    Therefore (a + b) - b = a + (b - b) = a + 0 = a. QED.
    """
    import random
    rng = random.Random(42)
    for _ in range(1000):
        a_dims = [rng.randint(-5, 5) for _ in range(7)]
        b_dims = [rng.randint(-5, 5) for _ in range(7)]
        a = Quantity("a", a_dims)
        b = Quantity("b", b_dims)
        composed = compose(a, b, "multiply")
        recovered = compose(composed, b, "divide")
        if recovered.dimensions != a.dimensions:
            return False
    return True


# ══════════════════════════════════════════════════════════════════════════════
# PART II: THE GOLAY REPRESENTATION LAYER (the novel part)
# ══════════════════════════════════════════════════════════════════════════════

# GF(4) arithmetic
GF4_ADD = [[0,1,2,3],[1,0,3,2],[2,3,0,1],[3,2,1,0]]
GF4_SYM = {0:"0", 1:"1", 2:"ω", 3:"ω̄"}
ROW_W = [0, 1, 2, 3]

# THEOREM 2: Bijective MOG Codec
# The map π: F₂²⁴ → GF(4)⁶ × Z₄⁶ is a bijection.
# Proof: Each 4-bit column maps to (score, fiber_idx) via the exhaustive
# 16-entry table. |F₂⁴| = 16 = |GF(4) × Z₄| = 4 × 4. QED.
COLUMN_TO_SHADOW: Dict[Tuple[int,int,int,int], Tuple[int,int]] = {}
SHADOW_TO_COLUMN: Dict[Tuple[int,int], Tuple[int,int,int,int]] = {}

for _val in range(16):
    _b = ((_val>>3)&1, (_val>>2)&1, (_val>>1)&1, _val&1)
    _s = 0
    for _r in range(4):
        if _b[_r]: _s = GF4_ADD[_s][ROW_W[_r]]
    _f = sum(1 for _c, (_sc, _) in COLUMN_TO_SHADOW.items() if _sc == _s)
    COLUMN_TO_SHADOW[_b] = (_s, _f)
    SHADOW_TO_COLUMN[(_s, _f)] = _b


def verify_bijective_codec() -> bool:
    """Theorem 2: The MOG projection is a bijection (lossless).

    Every 4-bit column maps to a unique (score, fiber_idx) pair,
    and the inverse map recovers the original. Tested on all 16 columns.
    """
    for col, (s, f) in COLUMN_TO_SHADOW.items():
        if SHADOW_TO_COLUMN[(s, f)] != col:
            return False
    return len(COLUMN_TO_SHADOW) == 16 and len(SHADOW_TO_COLUMN) == 16


def encode_to_24bit(dims: List[int]) -> List[int]:
    """Encode a 7D dimension vector as a 24-bit pattern.

    This is the REPRESENTATION layer — it maps dimensional information
    onto the Golay substrate. The mapping is deterministic but NOT
    information-preserving (7 integers → 24 bits loses magnitude).
    The integer companion (Part I) carries the exact information.

    HONEST ACKNOWLEDGMENT: The mod-2 ceiling arises here — the binary
    encoding discards magnitude. The integer companion restores it.
    This is a known artifact of the encoding choice, not a fundamental
    property of dimensional analysis.
    """
    reality = [1 if dims[i] != 0 else 0 for i in range(6)]
    info = [dims[i] % 2 for i in range(5)] + [dims[6] % 2]
    activation = [1 if abs(dims[i]) > 1 else 0 for i in range(5)] + [1 if abs(dims[6]) > 1 else 0]
    potential = [1 if dims[i] < 0 else 0 for i in range(5)] + [1 if dims[6] < 0 else 0]
    return reality + info + activation + potential


def project_to_mog(v24: List[int]) -> Tuple[List[int], List[int]]:
    """Project 24-bit vector to MOG shadow (6 GF(4) symbols + 6 fiber indices)."""
    grid = [v24[i*6:(i+1)*6] for i in range(4)]
    scores, fibers = [], []
    for c in range(6):
        col = tuple(grid[r][c] for r in range(4))
        s, f = COLUMN_TO_SHADOW[col]
        scores.append(s)
        fibers.append(f)
    return scores, fibers


def reconstruct_from_mog(scores: List[int], fibers: List[int]) -> List[int]:
    """Reconstruct 24-bit vector from MOG shadow."""
    grid = [[0]*6 for _ in range(4)]
    for c in range(6):
        col = SHADOW_TO_COLUMN[(scores[c], fibers[c])]
        for r in range(4):
            grid[r][c] = col[r]
    return grid[0] + grid[1] + grid[2] + grid[3]


# ══════════════════════════════════════════════════════════════════════════════
# THE SNAP (error correction — the novel addition)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SnapResult:
    """The result of snapping a 24-bit pattern to the nearest Golay codeword.

    THREAT MODEL: The SNAP protects against representation noise — corruption
    of a stored 24-bit codeword by up to 3 bit flips (correctable) or 4 bit
    flips (ambiguous, the "creative zone").

    In a deterministic mathematical representation there is no noise. But in a
    PHYSICAL IMPLEMENTATION (quantum states, optical registers, molecular
    switches), noise is real. The SNAP is the error-correction layer that
    makes the GLM robust to physical implementation noise.

    The syndrome σ(v) = H·v is the ANALOGUE of the field equation residual
    ∇F - J in GA: it measures how much v deviates from lawfulness.
    σ = 0 ⟺ v is a codeword (lawful, like a source-free field).
    σ ≠ 0 ⟺ v carries "history" (like a field with sources).
    """
    before: List[int]
    after: List[int]
    syndrome_weight: int
    correction_bits: List[int]

    @property
    def is_lawful(self) -> bool:
        return self.syndrome_weight == 0

    @property
    def status(self) -> str:
        if self.syndrome_weight == 0: return "lawful"
        if self.syndrome_weight <= 3: return "correctable"
        if self.syndrome_weight == 4: return "ambiguous (creative zone)"
        return "beyond covering radius"


def snap(v24: List[int]) -> SnapResult:
    """Snap to nearest Golay codeword (error correction)."""
    cw, meta = GOLAY_ENGINE.snap_to_codeword(v24)
    bits_changed = [i for i, (a, b) in enumerate(zip(v24, cw)) if a != b]
    return SnapResult(
        before=list(v24), after=list(cw),
        syndrome_weight=meta.get("syndrome_weight", 0),
        correction_bits=bits_changed,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PHYSICS LIBRARY
# ══════════════════════════════════════════════════════════════════════════════

PHYSICS = {
    "length":     [1,0,0,0,0,0,0], "mass":       [0,1,0,0,0,0,0],
    "time":       [0,0,1,0,0,0,0], "current":    [0,0,0,1,0,0,0],
    "temperature":[0,0,0,0,1,0,0], "amount":     [0,0,0,0,0,1,0],
    "luminous_intensity": [0,0,0,0,0,0,1],
    "speed":      [1,0,-1,0,0,0,0], "acceleration":[1,0,-2,0,0,0,0],
    "force":      [1,1,-2,0,0,0,0], "energy":     [2,1,-2,0,0,0,0],
    "power":      [2,1,-3,0,0,0,0], "pressure":   [-1,1,-2,0,0,0,0],
    "charge":     [0,0,1,1,0,0,0], "momentum":   [1,1,-1,0,0,0,0],
    "action":     [2,1,-1,0,0,0,0], "area":       [2,0,0,0,0,0,0],
    "volume":     [3,0,0,0,0,0,0], "voltage":    [2,1,-3,-1,0,0,0],
    "resistance": [2,1,-3,-2,0,0,0],
}


def build_library() -> Dict[str, Quantity]:
    return {name: Quantity(name, dims) for name, dims in PHYSICS.items()}


# ══════════════════════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print()
    print("=" * 70)
    print("GLM v8 — Honest Rewrite (Addressing GA Feedback)")
    print("=" * 70)
    print()
    print("Structure:")
    print("  Part I:  Classical dimensional analysis (no overclaiming)")
    print("  Part II: Golay representation layer (the novel part)")
    print("  Theorems: Bijective codec + Reversible composition")
    print("  Snap:     Error correction with defined threat model")
    print("  Syndrome: Connected to dynamics (σ as residual)")
    print()

    # ── Theorem 1: Reversible Composition ─────────────────────────────
    print("Theorem 1: Reversible Composition")
    print("  Statement: For all a, b ∈ Z⁷: subtract(add(a,b),b) = a")
    print("  (Parallels GA's invertible geometric product)")
    print(f"  Verified: {'✓ PASS (1000 random tests)' if verify_reversibility() else '✗ FAIL'}")
    print()

    # ── Theorem 2: Bijective Codec ────────────────────────────────────
    print("Theorem 2: Bijective MOG Codec")
    print("  Statement: π: F₂²⁴ → GF(4)⁶ × Z₄⁶ is a bijection")
    print(f"  Verified: {'✓ PASS (16/16 columns)' if verify_bijective_codec() else '✗ FAIL'}")
    print()

    # ── Part I: Classical dimensional analysis ────────────────────────
    print("Part I: Classical Dimensional Analysis")
    print("-" * 50)
    lib = build_library()

    mc2 = compose(compose(lib["mass"], lib["speed"]), lib["speed"])
    mc4 = compose(compose(mc2, lib["speed"]), lib["speed"])
    ma = compose(lib["mass"], lib["acceleration"])
    fl = compose(lib["force"], lib["length"])
    e_div_t = compose(lib["energy"], lib["time"], "divide")

    tests = [
        (lib["energy"], mc2, "E = mc²"),
        (lib["energy"], mc4, "E = mc⁴ (dimensional mismatch)"),
        (lib["force"], ma, "F = ma"),
        (lib["energy"], fl, "E = F·L"),
        (lib["power"], e_div_t, "P = E/t"),
        (lib["energy"], lib["momentum"], "E = p (mismatch)"),
    ]

    for lhs, rhs, label in tests:
        result = check_equation(lhs, rhs)
        print(f"  {label:<35} {'✓' if result else '✗'}  [{lhs.dims_str()} {'=' if result else '≠'} {rhs.dims_str()}]")

    print()
    print("  Note: This is classical dimensional analysis. Any correct")
    print("  implementation gives the same results. No overclaiming.")
    print()

    # ── Part II: Golay representation layer ───────────────────────────
    print("Part II: Golay Representation Layer (novel)")
    print("-" * 50)

    for name in ["energy", "mass", "force", "speed", "voltage"]:
        q = lib[name]
        vec = encode_to_24bit(q.dimensions)
        scores, fibers = project_to_mog(vec)
        reconstructed = reconstruct_from_mog(scores, fibers)
        hamming = sum(1 for a, b in zip(vec, reconstructed) if a != b)
        sr = snap(vec)
        print(f"  {name:<12} dims={q.dims_str():<15} σ={sr.syndrome_weight} "
              f"status={sr.status:<25} roundtrip={'✓' if hamming == 0 else '✗'}")

    print()
    print("  The MOG codec is lossless (0-bit discrepancy).")
    print("  The SNAP provides error correction (threat model: physical noise).")
    print("  The syndrome σ is the analogue of ∇F - J (deviation from lawfulness).")
    print()

    # ── Honest acknowledgment ─────────────────────────────────────────
    print("Honest Acknowledgment")
    print("-" * 50)
    print("  1. The dimensional analysis core is classical (Buckingham-Pi).")
    print("  2. The mod-2 ceiling is self-inflicted (binary encoding loses magnitude).")
    print("  3. The integer companion restores what the binary layer discards.")
    print("  4. The Golay encoding is the novel wrapper, not the checking itself.")
    print("  5. The TAX/NRCI cost layer is stipulative — separate from structural claims.")
    print("  6. The system does dimensional homogeneity, not dynamics (yet).")
    print("  7. The coordinate dependence is fragile — coordinate-free restatement needed.")
    print("  8. The genuinely novel elements: error correction + lossless MOG codec.")
    print()

    # ── Threat model ──────────────────────────────────────────────────
    print("Threat Model for Error Correction")
    print("-" * 50)
    print("  The SNAP protects against representation noise:")
    print("    ≤3 bit flips: uniquely correctable (Lean-verified)")
    print("    4 bit flips: ambiguous (6 equally light candidates)")
    print("  In deterministic math: no noise (SNAP is identity on codewords)")
    print("  In physical implementation: noise is real (quantum/optical/molecular)")
    print("  The SNAP makes the GLM robust to physical implementation noise.")
    print()

    # ── Syndrome as dynamics ──────────────────────────────────────────
    print("Syndrome as Dynamics (the path forward)")
    print("-" * 50)
    print("  In GA: ∇F = J measures deviation from source-free field")
    print("  In GLM: σ(v) = H·v measures deviation from lawfulness")
    print()
    print("  σ = 0  ⟺  v is lawful (like a source-free field)")
    print("  σ ≠ 0  ⟺  v carries history (like a field with sources)")
    print()
    print("  The snap RESOLVES the syndrome (like solving ∇F = J for F).")
    print("  This is the candidate analogue of the field equation.")
    print("  Future work: develop this into a full dynamical theory.")
    print()

    # ── Summary ───────────────────────────────────────────────────────
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    print("  What's classical:  dimensional analysis in (Z⁷,+)")
    print("  What's novel:      lossless MOG codec + Golay error correction")
    print("  What's stipulative: TAX/NRCI/Y/Q cost layer")
    print("  What's needed:      coordinate-free restatement, dynamics, Cl(24) rotors")
    print()
    print("  The best path: let GA's rigor discipline GLM's real ideas.")


if __name__ == "__main__":
    main()
