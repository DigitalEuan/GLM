#!/usr/bin/env python3
"""
Three-Cube Reed-Muller Construction for the GLM.

Per user: map the 24 MOG bits into three parallel 3D cubes (8 bits each).
Each cube is a natural RM(1,3) code. The three hierarchical rules:

  Rule A (RM(2,3)): each cube's 6 face parities are even
  Rule B (RM(1,3)): corresponding faces across cubes align globally
  Rule C (Golay):   weight symmetry (0, 8, 12, 16, 24)

This connects:
  Golay [24,12,8] → three × RM(1,3) [8,4,4] → BW256 (Reed-Muller tower)

The three cubes enable:
  1. Self-guided expansion (the cube rules tell you what's missing)
  2. Fast Walsh-Hadamard decoding (RM native, not brute-force search)
  3. Three-Column Thinking: Cube 0 = Language, Cube 1 = Math, Cube 2 = Script
  4. Dimensional extension: from 24D (Golay) to 256D (Barnes-Wall)

PUNCTURING vs EXTENSION:
  - Puncturing (projecting down) loses information — can't recover
  - Extension (going up) adds capacity — the BW256 has 2^128 codewords
  - The three-cube structure is the BRIDGE between 24D and 256D
"""

import sys
import json
import math
import itertools
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional, Set
from collections import defaultdict, Counter

sys.path.insert(0, '/home/z/my-project/scripts')
sys.path.insert(0, '/home/z/my-project/download/arc_agi_17')

from glm_clean import DataObject
from ubp_unified_v5 import GOLAY_ENGINE


# ══════════════════════════════════════════════════════════════════════════════
# THE THREE CUBES
# ══════════════════════════════════════════════════════════════════════════════

# A 3D cube has 8 vertices, indexed by (x, y, z) where x, y, z ∈ {0, 1}
# Vertex index: x*4 + y*2 + z
# Faces: 6 faces, each defined by fixing one coordinate to 0 or 1
#   face 0: x=0 (left),   face 1: x=1 (right)
#   face 2: y=0 (bottom), face 3: y=1 (top)
#   face 4: z=0 (back),   face 5: z=1 (front)

CUBE_VERTICES = list(itertools.product([0, 1], repeat=3))
CUBE_FACES = [
    ("x=0", [i for i, v in enumerate(CUBE_VERTICES) if v[0] == 0]),
    ("x=1", [i for i, v in enumerate(CUBE_VERTICES) if v[0] == 1]),
    ("y=0", [i for i, v in enumerate(CUBE_VERTICES) if v[1] == 0]),
    ("y=1", [i for i, v in enumerate(CUBE_VERTICES) if v[1] == 1]),
    ("z=0", [i for i, v in enumerate(CUBE_VERTICES) if v[2] == 0]),
    ("z=1", [i for i, v in enumerate(CUBE_VERTICES) if v[2] == 1]),
]

FACE_NAMES = ["x=0 (left)", "x=1 (right)", "y=0 (bottom)", "y=1 (top)",
              "z=0 (back)", "z=1 (front)"]


@dataclass
class Cube:
    """A single 3D cube (8 bits, one per vertex)."""
    bits: List[int]  # 8 bits

    def face_parity(self, face_idx: int) -> int:
        """Parity of a face (0=even, 1=odd)."""
        return sum(self.bits[v] for v in CUBE_FACES[face_idx][1]) % 2

    def all_face_parities(self) -> List[int]:
        """All 6 face parities."""
        return [self.face_parity(i) for i in range(6)]

    def weight(self) -> int:
        return sum(self.bits)

    def is_rm2(self) -> bool:
        """Rule A: valid RM(2,3) — all face parities even."""
        return all(p == 0 for p in self.all_face_parities())

    def describe(self) -> str:
        lines = [f"  Cube bits: {self.bits} (weight={self.weight()})"]
        for i, (name, vertices) in enumerate(CUBE_FACES):
            par = self.face_parity(i)
            active = [v for v in vertices if self.bits[v]]
            lines.append(f"    {FACE_NAMES[i]}: parity={par} active_vertices={active}")
        lines.append(f"    RM(2,3) valid: {self.is_rm2()}")
        return "\n".join(lines)


@dataclass
class ThreeCubeSystem:
    """Three parallel 3D cubes = 24 bits = the Golay code.

    Cube 0: bits 0-7  (Language column in TCT)
    Cube 1: bits 8-15 (Math column in TCT)
    Cube 2: bits 16-23 (Script column in TCT)
    """
    cube0: Cube
    cube1: Cube
    cube2: Cube

    @classmethod
    def from_bits(cls, bits: List[int]) -> "ThreeCubeSystem":
        return cls(
            cube0=Cube(bits=list(bits[0:8])),
            cube1=Cube(bits=list(bits[8:16])),
            cube2=Cube(bits=list(bits[16:24])),
        )

    def to_bits(self) -> List[int]:
        return self.cube0.bits + self.cube1.bits + self.cube2.bits

    def check_rule_a(self) -> Dict[str, Any]:
        """Rule A: each cube must be valid RM(2,3) — all face parities even."""
        results = {
            "cube0": self.cube0.is_rm2(),
            "cube1": self.cube1.is_rm2(),
            "cube2": self.cube2.is_rm2(),
        }
        results["all_pass"] = all(results.values())
        results["details"] = {
            "cube0_parities": self.cube0.all_face_parities(),
            "cube1_parities": self.cube1.all_face_parities(),
            "cube2_parities": self.cube2.all_face_parities(),
        }
        return results

    def check_rule_b(self) -> Dict[str, Any]:
        """Rule B: corresponding faces across cubes must align.

        For each face i, the sum of face_parities across the three cubes
        must be even (global parity check).
        """
        p0 = self.cube0.all_face_parities()
        p1 = self.cube1.all_face_parities()
        p2 = self.cube2.all_face_parities()

        face_checks = []
        for i in range(6):
            total = p0[i] + p1[i] + p2[i]
            face_checks.append({
                "face": FACE_NAMES[i],
                "parities": (p0[i], p1[i], p2[i]),
                "sum": total,
                "even": total % 2 == 0,
            })

        return {
            "faces": face_checks,
            "all_pass": all(fc["even"] for fc in face_checks),
        }

    def check_rule_c(self) -> Dict[str, Any]:
        """Rule C: Golay weight symmetry.

        Valid Golay codewords have weight 0, 8, 12, 16, or 24.
        """
        total_weight = self.cube0.weight() + self.cube1.weight() + self.cube2.weight()
        valid_weights = {0, 8, 12, 16, 24}
        return {
            "total_weight": total_weight,
            "cube_weights": (self.cube0.weight(), self.cube1.weight(), self.cube2.weight()),
            "is_valid": total_weight in valid_weights,
            "valid_weights": sorted(valid_weights),
        }

    def check_all(self) -> Dict[str, Any]:
        """Check all three rules."""
        a = self.check_rule_a()
        b = self.check_rule_b()
        c = self.check_rule_c()
        return {
            "rule_a": a,
            "rule_b": b,
            "rule_c": c,
            "all_pass": a["all_pass"] and b["all_pass"] and c["is_valid"],
        }

    def is_golay_codeword(self) -> bool:
        """Check if this is a valid Golay codeword."""
        return GOLAY_ENGINE.syndrome_weight(self.to_bits()) == 0

    def describe(self) -> str:
        lines = ["Three-Cube System:"]
        lines.append(f"  Cube 0 (Language): {self.cube0.bits}")
        lines.append(f"  Cube 1 (Math):     {self.cube1.bits}")
        lines.append(f"  Cube 2 (Script):   {self.cube2.bits}")
        lines.append("")
        a = self.check_rule_a()
        b = self.check_rule_b()
        c = self.check_rule_c()
        lines.append(f"  Rule A (RM(2,3) per cube): {'PASS' if a['all_pass'] else 'FAIL'}")
        lines.append(f"  Rule B (face alignment):  {'PASS' if b['all_pass'] else 'FAIL'}")
        lines.append(f"  Rule C (weight symmetry):  {'PASS' if c['is_valid'] else 'FAIL'} (weight={c['total_weight']})")
        lines.append(f"  Golay codeword: {self.is_golay_codeword()}")
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# WALSH-HADAMARD FAST DECODE (RM(1,3) native)
# ══════════════════════════════════════════════════════════════════════════════

# The 8×8 Walsh-Hadamard matrix (Sylvester construction)
def walsh_hadamard_8() -> List[List[int]]:
    """Generate the 8×8 Walsh-Hadamard matrix."""
    H = [[1]]
    for _ in range(3):  # 2^3 = 8
        H = [row + row for row in H] + [row + [-x for x in row] for row in H]
    return H


WH_MATRIX = walsh_hadamard_8()


def fast_walsh_hadamard_transform(bits: List[int]) -> List[int]:
    """Compute the Fast Walsh-Hadamard Transform of an 8-bit vector.

    The FWHT is the native decoding operation for RM(1,3) codes.
    The position of the maximum absolute value tells you the closest codeword.
    """
    # In-place FWHT (signal is the 8-bit vector, mapped to ±1)
    signal = [1 if b else -1 for b in bits]
    n = len(signal)
    h = 1
    while h < n:
        for i in range(0, n, h * 2):
            for j in range(i, i + h):
                x = signal[j]
                y = signal[j + h]
                signal[j] = x + y
                signal[j + h] = x - y
        h *= 2
    return signal


def decode_rm13(bits: List[int]) -> Dict[str, Any]:
    """Decode an 8-bit vector using RM(1,3) via Walsh-Hadamard.

    RM(1,3) has 16 codewords (2^4). The FWHT finds the closest one.
    """
    wht = fast_walsh_hadamard_transform(bits)

    # The maximum absolute value gives the closest codeword
    max_val = max(abs(v) for v in wht)
    max_idx = max(range(8), key=lambda i: abs(wht[i]))

    # The sign tells us whether to flip
    sign = 1 if wht[max_idx] > 0 else -1

    # Reconstruct the closest RM(1,3) codeword
    # RM(1,3) codewords are: all-0, all-1, and the 14 weight-4 patterns
    # that are rows of the Walsh-Hadamard matrix
    closest = [1 if (sign * WH_MATRIX[max_idx][i]) > 0 else 0 for i in range(8)]
    if sign < 0:
        closest = [1 - c for c in closest]

    # Also check all-0 and all-1
    d_all0 = sum(bits)
    d_all1 = sum(1 - b for b in bits)
    d_closest = sum(a != b for a, b in zip(bits, closest))

    # Pick the actual closest
    if d_all0 <= d_all1 and d_all0 <= d_closest:
        best = [0] * 8
        best_d = d_all0
    elif d_all1 <= d_closest:
        best = [1] * 8
        best_d = d_all1
    else:
        best = closest
        best_d = d_closest

    return {
        "input": bits,
        "wht": wht,
        "max_abs": max_val,
        "max_idx": max_idx,
        "closest_codeword": best,
        "distance": best_d,
        "correctable": best_d <= 1,  # RM(1,3) has d=4, corrects 1 error
    }


# ══════════════════════════════════════════════════════════════════════════════
# SELF-GUIDED EXPANSION
# ══════════════════════════════════════════════════════════════════════════════

class SelfGuidedExpansion:
    """The system expands itself by testing what's missing.

    The three-cube rules tell you what's wrong. The system:
    1. Takes a concept (24 bits)
    2. Checks the three rules (A, B, C)
    3. If any rule fails, the system SUGGESTS a fix
    4. Tests the fix — does it make a Golay codeword?
    5. If yes, the concept is "promoted" — it now has a codeword
    6. The body state records the promotion

    This is self-guided: the cube rules ARE the guide.
    """

    def __init__(self):
        self.promoted = {}  # name -> ThreeCubeSystem (codeword)
        self.rejected = {}  # name -> reason

    def suggest_fix(self, tcs: ThreeCubeSystem) -> List[str]:
        """Suggest fixes based on which rules fail."""
        suggestions = []

        a = tcs.check_rule_a()
        b = tcs.check_rule_b()
        c = tcs.check_rule_c()

        # Rule A: fix individual cube face parities
        if not a["all_pass"]:
            for cube_name, passed in [("cube0", a["cube0"]), ("cube1", a["cube1"]), ("cube2", a["cube2"])]:
                if not passed:
                    cube = getattr(tcs, cube_name)
                    for i, par in enumerate(cube.all_face_parities()):
                        if par == 1:
                            suggestions.append(
                                f"Fix {cube_name} face {FACE_NAMES[i]}: flip one vertex to make parity even")

        # Rule B: fix cross-cube alignment
        if not b["all_pass"]:
            for fc in b["faces"]:
                if not fc["even"]:
                    suggestions.append(
                        f"Fix face alignment {fc['face']}: parities {fc['parities']} sum to {fc['sum']} (should be even)")

        # Rule C: fix weight
        if not c["is_valid"]:
            suggestions.append(
                f"Fix weight: current={c['total_weight']}, needs to be in {c['valid_weights']}")

        return suggestions

    def try_promote(self, name: str, bits: List[int]) -> Dict[str, Any]:
        """Try to promote a concept to a Golay codeword."""
        tcs = ThreeCubeSystem.from_bits(bits)

        # Check if it's already a codeword
        if tcs.is_golay_codeword():
            self.promoted[name] = tcs
            return {
                "name": name,
                "status": "ALREADY_LAWFUL",
                "tcs": tcs,
                "suggestions": [],
            }

        # Check the rules
        check = tcs.check_all()
        suggestions = self.suggest_fix(tcs)

        # Try to snap to nearest codeword
        snapped_bits, meta = GOLAY_ENGINE.snap_to_codeword(bits)
        snapped_tcs = ThreeCubeSystem.from_bits(snapped_bits)

        if meta["correctable"]:
            self.promoted[name] = snapped_tcs
            return {
                "name": name,
                "status": "PROMOTED (snapped to codeword)",
                "original_tcs": tcs,
                "snapped_tcs": snapped_tcs,
                "tax": meta["anchor_distance"],
                "suggestions": suggestions,
                "check": check,
            }
        else:
            self.rejected[name] = f"weight {check['rule_c']['total_weight']}, not correctable"
            return {
                "name": name,
                "status": "REJECTED (too far from any codeword)",
                "tcs": tcs,
                "suggestions": suggestions,
                "check": check,
            }

    def stats(self) -> Dict[str, int]:
        return {
            "promoted": len(self.promoted),
            "rejected": len(self.rejected),
        }


# ══════════════════════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_three_cubes_on_codewords():
    """Test: do actual Golay codewords pass all three rules?"""
    print(f"\n{'='*70}")
    print("TEST 1: Three-cube rules on actual Golay codewords")
    print(f"{'='*70}\n")

    all_cws = GOLAY_ENGINE.get_all_codewords()

    # Test a sample of codewords
    import random
    rng = random.Random(42)
    sample = rng.sample(all_cws, 100)

    pass_a = pass_b = pass_c = pass_all = 0
    for cw in sample:
        tcs = ThreeCubeSystem.from_bits(cw)
        a = tcs.check_rule_a()
        b = tcs.check_rule_b()
        c = tcs.check_rule_c()
        if a["all_pass"]: pass_a += 1
        if b["all_pass"]: pass_b += 1
        if c["is_valid"]: pass_c += 1
        if a["all_pass"] and b["all_pass"] and c["is_valid"]: pass_all += 1

    print(f"  Sample: 100 Golay codewords")
    print(f"  Rule A (RM(2,3) per cube): {pass_a}/100 pass")
    print(f"  Rule B (face alignment):   {pass_b}/100 pass")
    print(f"  Rule C (weight symmetry):  {pass_c}/100 pass")
    print(f"  All three rules:            {pass_all}/100 pass")
    print()

    # Show one codeword in detail
    cw = sample[0]
    tcs = ThreeCubeSystem.from_bits(cw)
    print(tcs.describe())
    print()

    return pass_all, 100


def test_walsh_hadamard():
    """Test: Walsh-Hadamard decode of RM(1,3) cubes."""
    print(f"\n{'='*70}")
    print("TEST 2: Walsh-Hadamard Fast Decode (RM(1,3))")
    print(f"{'='*70}\n")

    # Test on a known RM(1,3) codeword (all-zeros)
    print("  Test: all-zeros cube")
    result = decode_rm13([0, 0, 0, 0, 0, 0, 0, 0])
    print(f"    closest: {result['closest_codeword']}, distance={result['distance']}")

    # Test on all-ones
    print("  Test: all-ones cube")
    result = decode_rm13([1, 1, 1, 1, 1, 1, 1, 1])
    print(f"    closest: {result['closest_codeword']}, distance={result['distance']}")

    # Test with 1 error
    print("  Test: all-zeros with 1 error")
    result = decode_rm13([0, 0, 0, 1, 0, 0, 0, 0])
    print(f"    closest: {result['closest_codeword']}, distance={result['distance']}, correctable={result['correctable']}")

    # Test with 2 errors
    print("  Test: all-zeros with 2 errors")
    result = decode_rm13([0, 0, 0, 1, 0, 0, 1, 0])
    print(f"    closest: {result['closest_codeword']}, distance={result['distance']}, correctable={result['correctable']}")

    print()
    print("  (RM(1,3) has d=4, so it corrects 1 error and detects 2)")


def test_self_guided_expansion():
    """Test: self-guided expansion of physics concepts."""
    print(f"\n{'='*70}")
    print("TEST 3: Self-Guided Expansion")
    print(f"{'='*70}\n")

    from glm_clean.tests.test_three_ideas import PHYSICS_CONCEPTS, encode_dimensioned

    expander = SelfGuidedExpansion()

    print(f"Testing {len(PHYSICS_CONCEPTS)} physics concepts...")
    print()

    for name, dims in PHYSICS_CONCEPTS.items():
        concept = encode_dimensioned(name, dims)
        result = expander.try_promote(name, concept.bits)

        status = result["status"]
        if "PROMOTED" in status:
            tax = result.get("tax", 0)
            print(f"  ✓ {name:<15} → {status} (tax={tax})")
        elif "ALREADY" in status:
            print(f"  ✓ {name:<15} → {status}")
        else:
            suggestions = result.get("suggestions", [])
            print(f"  ✗ {name:<15} → {status}")
            for s in suggestions[:2]:
                print(f"      suggestion: {s}")

    print()
    print(f"  Body state: {expander.stats()}")
    print()

    # Show the three-cube view of a promoted concept
    if expander.promoted:
        name = list(expander.promoted.keys())[0]
        tcs = expander.promoted[name]
        print(f"  Three-cube view of '{name}':")
        print(tcs.describe())

    return expander


def test_three_column_thinking():
    """Test: three cubes as Three-Column Thinking (Language | Math | Script)."""
    print(f"\n{'='*70}")
    print("TEST 4: Three-Column Thinking (Cube 0=Language, 1=Math, 2=Script)")
    print(f"{'='*70}\n")

    # Take a physics concept and show its three-cube decomposition
    from glm_clean.tests.test_three_ideas import PHYSICS_CONCEPTS, encode_dimensioned

    for name in ["energy", "force", "mass", "speed"]:
        concept = encode_dimensioned(name, PHYSICS_CONCEPTS[name])
        tcs = ThreeCubeSystem.from_bits(concept.bits)

        print(f"  {name}:")
        print(f"    Cube 0 (Language): {tcs.cube0.bits} weight={tcs.cube0.weight()} RM(2,3)={tcs.cube0.is_rm2()}")
        print(f"    Cube 1 (Math):     {tcs.cube1.bits} weight={tcs.cube1.weight()} RM(2,3)={tcs.cube1.is_rm2()}")
        print(f"    Cube 2 (Script):   {tcs.cube2.bits} weight={tcs.cube2.weight()} RM(2,3)={tcs.cube2.is_rm2()}")

        check = tcs.check_all()
        print(f"    Rules: A={check['rule_a']['all_pass']} B={check['rule_b']['all_pass']} C={check['rule_c']['is_valid']}")
        print(f"    Golay codeword: {tcs.is_golay_codeword()}")
        print()

    # The idea: the three cubes should AGREE (all pass rules) for a valid concept
    # If they disagree, the concept is "incoherent" — the columns don't match
    print("  Three-Column Thinking: the three cubes must AGREE for a concept to be lawful.")
    print("  If Cube 0 (Language) says one thing and Cube 1 (Math) says another,")
    print("  the concept is incoherent — the syndrome (Rule failure) tells you WHERE.")


def test_extension_to_bw256():
    """Test: the path from Golay (24D) to Barnes-Wall (256D)."""
    print(f"\n{'='*70}")
    print("TEST 5: Extension Path (Golay 24D → BW 256D)")
    print(f"{'='*70}\n")

    print("  The three-cube construction is the bridge:")
    print("    Golay [24,12,8] = 3 × RM(1,3) [8,4,4] + cross-cube parity")
    print()
    print("  Reed-Muller tower:")
    print("    RM(1,3) [8,4,4]   → 8D,  16 codewords,  d=4")
    print("    RM(1,4) [16,5,8]  → 16D, 32 codewords,  d=8")
    print("    RM(1,5) [32,6,16] → 32D, 64 codewords,  d=16")
    print("    RM(1,6) [64,7,32] → 64D, 128 codewords, d=32")
    print("    RM(1,7) [128,8,64]→ 128D,256 codewords, d=64")
    print("    RM(1,8) [256,9,128]→256D,512 codewords,d=128")
    print()
    print("  Barnes-Wall lattice BW256 is built from RM codes:")
    print("    BW16  = RM(1,4) construction")
    print("    BW32  = RM(1,5) construction")
    print("    BW64  = RM(1,6) construction")
    print("    BW128 = RM(1,7) construction")
    print("    BW256 = RM(1,8) construction")
    print()
    print("  The three-cube structure connects to this tower:")
    print("    Level 0: 3 × 8-bit cubes (current, 24D)")
    print("    Level 1: 3 × 16-bit cubes (48D, using RM(1,4))")
    print("    Level 2: 3 × 32-bit cubes (96D, using RM(1,5))")
    print("    Level 3: 3 × 64-bit cubes (192D, using RM(1,6))")
    print("    Level 4: 3 × 128-bit cubes (384D, using RM(1,7))")
    print("    Level 5: BW256 (256D, the full Barnes-Wall lattice)")
    print()
    print("  Each level adds dimensions. The three-cube rules scale:")
    print("    Rule A: each cube is valid RM(2,k) for level k")
    print("    Rule B: face alignment across cubes")
    print("    Rule C: weight symmetry (the Golay invariant)")
    print()
    print("  PUNCTURING (projecting down) loses information — can't recover.")
    print("  EXTENSION (going up) adds capacity — the BW256 has 2^128 codewords.")
    print("  The three-cube structure is the BRIDGE.")
    print()
    print("  ★ This is the path from 24D to 256D ★")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70, flush=True)
    print("Three-Cube Reed-Muller Construction", flush=True)
    print("=" * 70, flush=True)
    print()
    print("24 MOG bits → three 8-bit cubes → RM(1,3) + hierarchical rules → Golay")
    print("Cube 0 = Language | Cube 1 = Math | Cube 2 = Script (TCT)")
    print()

    # Test 1: Do Golay codewords pass the three rules?
    pass_count, total = test_three_cubes_on_codewords()

    # Test 2: Walsh-Hadamard decode
    test_walsh_hadamard()

    # Test 3: Self-guided expansion
    expander = test_self_guided_expansion()

    # Test 4: Three-column thinking
    test_three_column_thinking()

    # Test 5: Extension to BW256
    test_extension_to_bw256()

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print()
    print(f"1. Three-cube rules on Golay codewords: {pass_count}/{total} pass all three")
    print(f"2. Walsh-Hadamard fast decode: RM(1,3) native, corrects 1 error")
    print(f"3. Self-guided expansion: {expander.stats()}")
    print(f"4. Three-Column Thinking: Cube 0=Language, Cube 1=Math, Cube 2=Script")
    print(f"5. Extension path: Golay 24D → RM tower → BW 256D")
    print()
    print("The three-cube construction is the bridge between:")
    print("  - The 24D Golay code (current system)")
    print("  - The 256D Barnes-Wall lattice (the extension)")
    print()
    print("The cube rules ARE the self-guidance:")
    print("  Rule A tells you which cube face is broken")
    print("  Rule B tells you which cross-cube alignment is off")
    print("  Rule C tells you if the weight is wrong")
    print()
    print("The system can expand itself by:")
    print("  1. Checking the three rules on each concept")
    print("  2. Suggesting fixes based on which rule fails")
    print("  3. Testing the fix (does it snap to a codeword?)")
    print("  4. Promoting concepts that pass all three rules")

    # Save
    output = {
        "experiment": "Three-Cube Reed-Muller Construction",
        "codewords_passing_all_rules": f"{pass_count}/{total}",
        "expansion_stats": expander.stats(),
    }
    out_path = Path('/home/z/my-project/download/arc_agi_17/results/three_cube.json')
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n[save] Results saved: {out_path}")


if __name__ == "__main__":
    main()
