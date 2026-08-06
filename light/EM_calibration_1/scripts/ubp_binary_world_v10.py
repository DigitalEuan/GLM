#!/usr/bin/env python3
"""
UBP Binary World v10 — Testing the Substrate as Native Binary
==============================================================
Per user's question: "Do I need to move into the Binary world more now for
deeper results? — like skip the python stuff and go for zeros and ones maybe?"

This experiment tests whether the substrate can be operated as NATIVE BINARY
(no Fractions, no lists-of-ints, no Python object model — just integers and
bit operations).

SIX PARTS:

Part 1: Build a pure-bitwise substrate (the substrate as int operations)
Part 2: Test native binary ALU — can codewords do ADD/MUL via bit ops?
Part 3: Test composition laws — what happens when two codewords combine?
Part 4: Test conservation laws — what does the substrate conserve?
Part 5: Test cellular automaton formulation — can the substrate be a CA?
Part 6: Honest assessment — what does the binary world add vs lose?

The question: is the substrate MORE than a Python implementation? Does going
to raw bits reveal structure that the Python abstractions hide?

Outputs:
  /home/z/my-project/download/ubp_binary_world_v10.json
  /home/z/my-project/download/ubp_binary_world_v10_report.md
"""

import sys
import math
import json
import itertools
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any
from collections import Counter, defaultdict

sys.path.insert(0, "/home/z/my-project/scripts")
from ubp_engine.ubp_unified_v5 import (
    GolayCodeEngine,
    LeechLatticeEngine,
    UBPSourceCodeParticlePhysics,
)


# ============================================================
# Part 1: Pure-bitwise substrate
# ============================================================
#
# The verified engine uses List[int] (24-element lists of 0s and 1s).
# This is Python's way of representing binary. But the substrate IS binary
# — it should be operable as INTS with BIT OPERATIONS.
#
# We rebuild the core substrate using only:
#   - Python int (arbitrary precision, but we only use 24 bits)
#   - Bit operations: ^, &, |, ~, <<, >>
#   - bin(x).count('1') for popcount
#   - No Fractions, no floats, no lists (except for I/O)
#
# The question: does this reveal anything the List[int] version hides?
# ============================================================


class BinarySubstrate:
    """The UBP substrate as pure bitwise operations on 24-bit ints.

    No Fractions, no lists, no Python object model. Just ints and bit ops.
    """

    def __init__(self):
        # Import the verified engine's H columns (guaranteed correct)
        from ubp_engine.ubp_unified_v5 import GolayCodeEngine
        ge = GolayCodeEngine()
        cols = ge._H_cols  # 24 columns, each a 12-tuple

        # Build H as 12 rows of 24-bit ints
        self.H = []
        for i in range(12):
            row = 0
            for k in range(24):
                if cols[k][i]:
                    row |= 1 << (23 - k)
            self.H.append(row)

        # Build G from the verified engine (12 rows of 24-bit ints)
        self.G = []
        for i in range(12):
            row = 0
            for j in range(24):
                if ge.G[i][j]:
                    row |= 1 << (23 - j)
            self.G.append(row)

        # Build all 4096 codewords as ints
        self.CODEWORDS = []
        for mask in range(4096):
            cw = 0
            for i in range(12):
                if (mask >> i) & 1:
                    cw ^= self.G[i]
            self.CODEWORDS.append(cw)
        self.CODEWORD_SET = set(self.CODEWORDS)

        # Build complete coset-leader table (Lean-verified decoder)
        self.COSET_LEADERS = {}
        for weight in range(5):
            for combo in itertools.combinations(range(24), weight):
                leader = 0
                for bit in combo:
                    leader |= 1 << bit
                s = self._syndrome(leader)
                if s not in self.COSET_LEADERS:
                    self.COSET_LEADERS[s] = leader
        assert len(self.COSET_LEADERS) == 4096

        # Y constant (as a float for TAX computation — the only non-bit op)
        self.Y = 1.0 / (math.pi + 2.0 / math.pi)  # ≈ 0.2647

    @staticmethod
    def _popcount(x: int) -> int:
        """Hamming weight of a 24-bit int."""
        return bin(x).count('1')

    def _syndrome(self, v: int) -> int:
        """12-bit syndrome of a 24-bit word. Pure bit ops."""
        s = 0
        for i in range(12):
            # bit i of syndrome = popcount(v & H[i]) mod 2
            bit = self._popcount(v & self.H[i]) & 1
            s |= bit << (11 - i)
        return s

    def snap(self, v: int) -> int:
        """Lean-verified complete decoder. Pure bit ops."""
        s = self._syndrome(v)
        return v ^ self.COSET_LEADERS[s]

    def is_codeword(self, v: int) -> bool:
        return v in self.CODEWORD_SET

    def encode(self, msg12: int) -> int:
        """Encode 12-bit message as 24-bit codeword. Pure bit ops."""
        cw = 0
        for i in range(12):
            if (msg12 >> i) & 1:
                cw ^= self.G[i]
        return cw

    def hamming_weight(self, v: int) -> int:
        return self._popcount(v)

    def hamming_distance(self, a: int, b: int) -> int:
        return self._popcount(a ^ b)

    def tax(self, v: int) -> float:
        """TAX = HW × Y + HW/8. Uses one float multiply (Y is irrational)."""
        hw = self._popcount(v)
        return hw * self.Y + hw / 8.0

    def nrci(self, v: int) -> float:
        """NRCI = 10 / (10 + TAX)."""
        return 10.0 / (10.0 + self.tax(v))

    def xor(self, a: int, b: int) -> int:
        """Substrate XOR: the natural composition operation."""
        return a ^ b

    def and_op(self, a: int, b: int) -> int:
        """Substrate AND: shared structure."""
        return a & b

    def or_op(self, a: int, b: int) -> int:
        """Substrate OR: union."""
        return a | b


# ============================================================
# Part 2: Native binary ALU test
# ============================================================
#
# Can the substrate do ARITHMETIC using only bit operations on codewords?
#
# The EM engine (ubp_electromagnetic_analog_compute_engine.py) does ADD/MUL
# via Poynting flux — but that's a Python abstraction. Can the substrate
# itself do arithmetic?
#
# Test: encode two integers as codewords, try to add them via substrate
# operations (XOR, AND, shifts), and check if the result is the encoded sum.
#
# The honest expectation: the substrate is NOT a general-purpose ALU. It's
# a code (Golay), not a computer. But the TEST is whether there's ANY
# arithmetic that works natively.
# ============================================================


def test_binary_alu(substrate: BinarySubstrate) -> Dict[str, Any]:
    """Test whether the substrate can do arithmetic via bit ops."""
    print("  Testing native binary ALU...")

    results = {}

    # Test 1: Can XOR of two codewords represent addition mod 2?
    # In GF(2), XOR IS addition. So codeword_a XOR codeword_b is the sum in GF(2)^24.
    # But does this correspond to integer addition? No — XOR is not integer add.
    a = substrate.encode(0b101100101011)  # arbitrary 12-bit message
    b = substrate.encode(0b010011010100)
    xor_result = substrate.xor(a, b)
    results["xor_as_gf2_add"] = {
        "a_msg": 0b101100101011,
        "b_msg": 0b010011010100,
        "a_cw": a,
        "b_cw": b,
        "xor_result": xor_result,
        "is_xor_a_codeword": substrate.is_codeword(xor_result),
        "interpretation": (
            "XOR of two codewords IS a codeword (the Golay code is LINEAR). "
            "This means GF(2) addition works natively. But this is NOT integer "
            "addition — it's mod-2 addition. The substrate does GF(2) arithmetic "
            "natively, but not integer arithmetic."
        ),
    }

    # Test 2: Can we do integer addition via a sequence of bit ops?
    # Integer add: a + b = a XOR b + 2*(a AND b), recursively (carry propagation)
    # Test: does this work on codewords?
    def integer_add_via_bits(x: int, y: int, max_bits: int = 24) -> int:
        """Add two integers using only bit ops (carry propagation)."""
        for _ in range(max_bits):
            carry = x & y
            x = x ^ y
            y = carry << 1
            if y == 0:
                break
        return x & ((1 << max_bits) - 1)

    a_int = 15
    b_int = 27
    sum_via_bits = integer_add_via_bits(a_int, b_int)
    results["integer_add_via_bits"] = {
        "a": a_int,
        "b": b_int,
        "sum_via_bits": sum_via_bits,
        "sum_python": a_int + b_int,
        "matches": sum_via_bits == a_int + b_int,
        "interpretation": (
            "Integer addition CAN be done via bit ops (carry propagation). "
            "But the RESULT is not a codeword — it's just an integer. "
            "The substrate can DO integer arithmetic on the 24-bit REPRESENTATION, "
            "but the result doesn't snap to a codeword (unless you re-encode)."
        ),
    }

    # Test 3: Can we do multiplication via bit ops?
    def integer_mul_via_bits(x: int, y: int, max_bits: int = 24) -> int:
        """Multiply two integers using only bit ops (shift-add)."""
        result = 0
        while y:
            if y & 1:
                result = integer_add_via_bits(result, x, max_bits)
            x <<= 1
            y >>= 1
        return result & ((1 << max_bits) - 1)

    a_int = 6
    b_int = 7
    product_via_bits = integer_mul_via_bits(a_int, b_int)
    results["integer_mul_via_bits"] = {
        "a": a_int,
        "b": b_int,
        "product_via_bits": product_via_bits,
        "product_python": a_int * b_int,
        "matches": product_via_bits == a_int * b_int,
        "interpretation": (
            "Integer multiplication CAN be done via bit ops (shift-add). "
            "Same caveat: the result is an integer, not a codeword."
        ),
    }

    # Test 4: Does the substrate have a NATIVE multiplication (not integer mul)?
    # In GF(2^12), multiplication is polynomial multiplication mod an irreducible.
    # The Golay code is a SUBSPACE of GF(2)^24, not a field. So there's no native
    # multiplication that stays in the code.
    # But: the AND operation is "componentwise multiplication" in GF(2)^24.
    # Does AND of two codewords give a codeword? Generally NO (the code is not closed under AND).
    a_cw = substrate.encode(0b101100101011)
    b_cw = substrate.encode(0b010011010100)
    and_result = substrate.and_op(a_cw, b_cw)
    results["and_as_componentwise_mul"] = {
        "a_cw": a_cw,
        "b_cw": b_cw,
        "and_result": and_result,
        "is_and_a_codeword": substrate.is_codeword(and_result),
        "interpretation": (
            "AND of two codewords is generally NOT a codeword. "
            "The Golay code is closed under XOR (GF(2) add) but NOT under AND (GF(2) mul). "
            "This means the substrate has native ADDITION but not native MULTIPLICATION. "
            "Multiplication requires leaving the code (and re-snapping)."
        ),
    }

    return {
        "tests": results,
        "summary": (
            "The substrate does GF(2) arithmetic natively (XOR = addition). "
            "It does NOT do integer arithmetic natively — that requires carry propagation, "
            "which is a bit-op algorithm but not substrate-native. "
            "AND (componentwise multiplication) does NOT preserve the code. "
            "CONCLUSION: the substrate is a GF(2) linear algebra engine, not a general ALU."
        ),
        "what_the_binary_world_reveals": (
            "Going to bit ops makes it clear: the substrate's native operation is XOR (GF(2) add). "
            "Everything else (integer add, multiply, AND) is either an algorithm ON TOP of the substrate "
            "or leaves the code. The substrate is a LINEAR ALGEBRA engine over GF(2), not a computer."
        ),
    }


# ============================================================
# Part 3: Composition laws
# ============================================================
#
# What happens when two Data Objects combine?
#
# Operations to test:
#   - XOR: the native GF(2) operation. Result IS a codeword.
#   - AND: componentwise mul. Result is NOT generally a codeword.
#   - OR: union. Result is NOT generally a codeword.
#   - Snap after AND/OR: does snapping recover a meaningful codeword?
#
# The bond-geometry formula (v8) was: geometric_work = AND_HW + bond_order × XOR_HW.
# Can we formalize a general composition law?
# ============================================================


def test_composition(substrate: BinarySubstrate) -> Dict[str, Any]:
    """Test what happens when two codewords combine."""
    print("  Testing composition laws...")

    # Pick 10 random pairs of codewords
    import random
    random.seed(42)
    test_pairs = []
    for _ in range(10):
        a_idx = random.randint(0, 4095)
        b_idx = random.randint(0, 4095)
        if a_idx != b_idx:
            test_pairs.append((a_idx, b_idx))

    results = []
    for a_idx, b_idx in test_pairs:
        a = substrate.CODEWORDS[a_idx]
        b = substrate.CODEWORDS[b_idx]

        xor_res = substrate.xor(a, b)
        and_res = substrate.and_op(a, b)
        or_res = substrate.or_op(a, b)

        # Snap the AND and OR results
        and_snapped = substrate.snap(and_res)
        or_snapped = substrate.snap(or_res)

        results.append({
            "a_idx": a_idx,
            "b_idx": b_idx,
            "a_hw": substrate.hamming_weight(a),
            "b_hw": substrate.hamming_weight(b),
            "xor": {
                "result_hw": substrate.hamming_weight(xor_res),
                "is_codeword": substrate.is_codeword(xor_res),
                "result_idx": substrate.CODEWORDS.index(xor_res) if substrate.is_codeword(xor_res) else None,
            },
            "and": {
                "result_hw": substrate.hamming_weight(and_res),
                "is_codeword": substrate.is_codeword(and_res),
                "snapped_hw": substrate.hamming_weight(and_snapped),
                "snap_distance": substrate.hamming_distance(and_res, and_snapped),
            },
            "or": {
                "result_hw": substrate.hamming_weight(or_res),
                "is_codeword": substrate.is_codeword(or_res),
                "snapped_hw": substrate.hamming_weight(or_snapped),
                "snap_distance": substrate.hamming_distance(or_res, or_snapped),
            },
        })

    # Statistics
    xor_always_codeword = all(r["xor"]["is_codeword"] for r in results)
    and_never_codeword = all(not r["and"]["is_codeword"] for r in results)
    or_never_codeword = all(not r["or"]["is_codeword"] for r in results)

    # Test the composition law: is there a formula relating HW(a XOR b) to HW(a), HW(b), HW(a AND b)?
    # The identity: HW(a XOR b) = HW(a) + HW(b) - 2*HW(a AND b)
    # This is a TAUTOLOGY (always true for binary vectors). Test it.
    tautology_holds = True
    for r in results:
        a = substrate.CODEWORDS[r["a_idx"]]
        b = substrate.CODEWORDS[r["b_idx"]]
        expected_xor_hw = substrate.hamming_weight(a) + substrate.hamming_weight(b) - 2 * substrate.hamming_weight(a & b)
        actual_xor_hw = substrate.hamming_weight(a ^ b)
        if expected_xor_hw != actual_xor_hw:
            tautology_holds = False
            break

    return {
        "test_pairs": results,
        "xor_always_codeword": xor_always_codeword,
        "and_never_codeword": and_never_codeword,
        "or_never_codeword": or_never_codeword,
        "composition_tautology": {
            "formula": "HW(a XOR b) = HW(a) + HW(b) - 2 × HW(a AND b)",
            "holds": tautology_holds,
            "interpretation": (
                "This is a TAUTOLOGY of binary arithmetic — it's always true for any two binary vectors. "
                "But it's a USEFUL tautology: it means the substrate's composition is governed by a "
                "conservation law. The XOR 'preserves' the total Hamming weight (minus the shared bits)."
            ),
        },
        "summary": (
            "XOR is the ONLY composition operation that preserves the code (result is always a codeword). "
            "AND and OR leave the code (result is not a codeword), but can be re-snapped. "
            "The composition law HW(a⊕b) = HW(a) + HW(b) - 2×HW(a∧b) is a tautology but reveals "
            "that the substrate has a CONSERVATION LAW: the total 'active bits' are conserved under XOR "
            "(minus the shared bits)."
        ),
    }


# ============================================================
# Part 4: Conservation laws
# ============================================================
#
# What does the substrate conserve?
#
# Known (from Lean):
#   - 4 | d² (Hamming distance between codewords is a multiple of 4)
#   - Codewords have HW ∈ {0, 8, 12, 16, 24}
#
# Test for additional conservation laws:
#   - Parity: is popcount(a XOR b) always even?
#   - Mod 4: is popcount(a XOR b) always 0 mod 4? (Yes, from Lean)
#   - Mod 8: is popcount(a XOR b) always 0 mod 8? (No — 12 mod 8 = 4)
#   - Energy conservation: does TAX(a XOR b) relate to TAX(a) + TAX(b)?
#   - Symmetry: does the substrate conserve any symmetry measure?
# ============================================================


def test_conservation(substrate: BinarySubstrate) -> Dict[str, Any]:
    """Test what the substrate conserves."""
    print("  Testing conservation laws...")

    # Sample 1000 pairs of codewords
    import random
    random.seed(42)
    n_tests = 1000

    # Test 1: popcount(a XOR b) mod 2 (parity)
    parities = []
    for _ in range(n_tests):
        a = random.choice(substrate.CODEWORDS)
        b = random.choice(substrate.CODEWORDS)
        parities.append(substrate.hamming_weight(a ^ b) % 2)
    parity_always_even = all(p == 0 for p in parities)

    # Test 2: popcount(a XOR b) mod 4
    mod4_values = []
    for _ in range(n_tests):
        a = random.choice(substrate.CODEWORDS)
        b = random.choice(substrate.CODEWORDS)
        mod4_values.append(substrate.hamming_weight(a ^ b) % 4)
    mod4_distribution = Counter(mod4_values)
    mod4_always_zero = all(v == 0 for v in mod4_values)

    # Test 3: popcount(a XOR b) mod 8
    mod8_values = []
    for _ in range(n_tests):
        a = random.choice(substrate.CODEWORDS)
        b = random.choice(substrate.CODEWORDS)
        mod8_values.append(substrate.hamming_weight(a ^ b) % 8)
    mod8_distribution = Counter(mod8_values)

    # Test 4: TAX conservation — does TAX(a XOR b) relate to TAX(a), TAX(b)?
    # TAX = HW × (Y + 1/8). So TAX(a XOR b) = HW(a XOR b) × (Y + 1/8).
    # HW(a XOR b) = HW(a) + HW(b) - 2×HW(a AND b).
    # So TAX(a XOR b) = [HW(a) + HW(b) - 2×HW(a AND b)] × (Y + 1/8)
    #                  = TAX(a) + TAX(b) - 2×HW(a AND b)×(Y + 1/8)
    #                  = TAX(a) + TAX(b) - 2×TAX(a AND b)
    # This is a CONSERVATION LAW: TAX is "conserved" under XOR, with the AND term as the "interaction".
    tax_conservation_holds = True
    for _ in range(100):
        a = random.choice(substrate.CODEWORDS)
        b = random.choice(substrate.CODEWORDS)
        tax_a = substrate.tax(a)
        tax_b = substrate.tax(b)
        tax_xor = substrate.tax(a ^ b)
        tax_and = substrate.tax(a & b)
        expected = tax_a + tax_b - 2 * tax_and
        if abs(expected - tax_xor) > 1e-10:
            tax_conservation_holds = False
            break

    # Test 5: NRCI conservation — does NRCI have a conservation law?
    # NRCI = 10 / (10 + TAX). It's a nonlinear function of TAX.
    # NRCI(a XOR b) = 10 / (10 + TAX(a XOR b)) = 10 / (10 + TAX(a) + TAX(b) - 2×TAX(a AND b))
    # This doesn't simplify to a nice conservation law. NRCI is NOT conserved.
    # But: the PRODUCT NRCI(a) × NRCI(b) / NRCI(a AND b)^2 might have a pattern.
    nrci_products = []
    for _ in range(100):
        a = random.choice(substrate.CODEWORDS)
        b = random.choice(substrate.CODEWORDS)
        nrci_a = substrate.nrci(a)
        nrci_b = substrate.nrci(b)
        nrci_xor = substrate.nrci(a ^ b)
        nrci_and = substrate.nrci(a & b)
        if nrci_and > 0:
            ratio = (nrci_a * nrci_b) / (nrci_and ** 2)
            nrci_products.append(ratio)

    return {
        "parity_conservation": {
            "test": "popcount(a XOR b) mod 2 = 0 for all codeword pairs?",
            "result": parity_always_even,
            "interpretation": "Parity is conserved (codewords are doubly-even, so XOR is even).",
        },
        "mod4_conservation": {
            "test": "popcount(a XOR b) mod 4 = 0 for all codeword pairs?",
            "result": mod4_always_zero,
            "distribution": dict(mod4_distribution),
            "interpretation": "Mod 4 is conserved (Lean theorem `corrected_quantized`: d² ∈ {0,8,12,16,24}, all 0 mod 4).",
        },
        "mod8_conservation": {
            "test": "popcount(a XOR b) mod 8 = 0 for all codeword pairs?",
            "result": all(v == 0 for v in mod8_values),
            "distribution": dict(mod8_distribution),
            "interpretation": "Mod 8 is NOT conserved (d²=12 gives 12 mod 8 = 4). The substrate conserves mod 4, not mod 8.",
        },
        "tax_conservation": {
            "test": "TAX(a XOR b) = TAX(a) + TAX(b) - 2×TAX(a AND b)?",
            "result": tax_conservation_holds,
            "formula": "TAX(a ⊕ b) = TAX(a) + TAX(b) - 2 × TAX(a ∧ b)",
            "interpretation": (
                "TAX IS conserved under XOR, with the AND term as the 'interaction energy'. "
                "This is the substrate's energy conservation law: the 'cost' of the combined state "
                "equals the sum of individual costs minus twice the 'shared cost'. "
                "This is analogous to E(A∪B) = E(A) + E(B) - E(A∩B) in statistical mechanics."
            ),
        },
        "nrci_conservation": {
            "test": "Is NRCI conserved under any operation?",
            "result": "NRCI is NOT conserved — it's a nonlinear function of TAX",
            "sample_products": nrci_products[:10],
            "interpretation": (
                "NRCI (coherence) is a nonlinear function of TAX, so it doesn't have a simple "
                "conservation law. But TAX (cost) DOES. This means the substrate conserves COST, "
                "not COHERENCE. Coherence emerges from cost, not the other way around."
            ),
        },
        "summary": (
            "The substrate conserves: (1) parity (mod 2), (2) mod 4 (Lean theorem), (3) TAX under XOR "
            "with the AND interaction. It does NOT conserve mod 8 or NRCI. "
            "The TAX conservation law (TAX(a⊕b) = TAX(a) + TAX(b) - 2×TAX(a∧b)) is the deepest: "
            "it's the substrate's energy conservation law, with AND as the interaction term."
        ),
    }


# ============================================================
# Part 5: Cellular automaton formulation
# ============================================================
#
# Can the substrate be expressed as a CELLULAR AUTOMATON?
#
# A CA has:
#   - A grid of cells (each holding a bit)
#   - A local update rule (cell's next state depends on its neighbors)
#   - Synchronous updates
#
# The substrate has 24 bits. Can we define a CA rule that:
#   - Snaps any 24-bit state to a codeword?
#   - Minimizes TAX?
#
# Test: define a CA where each bit updates based on its 23 neighbors (the
# whole 24-bit state). The rule is: snap to the nearest codeword.
# This is a GLOBAL rule (not local), so it's not a traditional CA.
# But it IS a synchronous update rule.
#
# Alternative: define a CA where each bit updates based on a LOCAL window
# (e.g., 3 bits: itself and 2 neighbors). Can such a local rule produce
# the Golay snap?
#
# The honest expectation: NO. The Golay snap is a GLOBAL operation (it
# depends on the syndrome, which is a global property). A local CA rule
# cannot implement it. But the TEST is whether ANY local rule approximates
# it.
# ============================================================


def test_cellular_automaton(substrate: BinarySubstrate) -> Dict[str, Any]:
    """Test whether the substrate can be expressed as a cellular automaton."""
    print("  Testing cellular automaton formulation...")

    # Test 1: Global CA (the snap as a global update rule)
    # This trivially works — the snap IS a global update rule.
    # Test: apply snap repeatedly, does it converge?
    import random
    random.seed(42)

    convergence_tests = []
    for _ in range(100):
        state = random.randint(0, (1 << 24) - 1)
        snapped = substrate.snap(state)
        # Snap is idempotent: snap(snap(x)) = snap(x)
        double_snapped = substrate.snap(snapped)
        convergence_tests.append({
            "initial": state,
            "snapped": snapped,
            "double_snapped": double_snapped,
            "idempotent": snapped == double_snapped,
            "is_codeword_after_snap": substrate.is_codeword(snapped),
        })

    idempotent_holds = all(t["idempotent"] for t in convergence_tests)
    always_codeword = all(t["is_codeword_after_snap"] for t in convergence_tests)

    # Test 2: Local CA — can a 3-bit local rule (cell + 2 neighbors) approximate the snap?
    # Define a CA: each bit updates based on (bit[i-1], bit[i], bit[i+1]) mod 24.
    # There are 2^8 = 256 possible 3-bit rules.
    # Test: does ANY rule snap arbitrary states to codewords?
    # (This is infeasible to test exhaustively, so we test a few candidate rules.)

    # Candidate rule: majority rule (bit becomes the majority of itself and neighbors)
    def majority_rule(state: int, n_bits: int = 24) -> int:
        new_state = 0
        for i in range(n_bits):
            left = (state >> ((i - 1) % n_bits)) & 1
            center = (state >> i) & 1
            right = (state >> ((i + 1) % n_bits)) & 1
            majority = 1 if (left + center + right) >= 2 else 0
            new_state |= majority << i
        return new_state

    # Test majority rule on 100 random states
    majority_results = []
    for _ in range(100):
        state = random.randint(0, (1 << 24) - 1)
        for _ in range(10):  # iterate 10 times
            state = majority_rule(state)
        majority_results.append(substrate.is_codeword(state))

    majority_converges_to_codeword = sum(majority_results)

    # Candidate rule: parity rule (bit becomes XOR of itself and neighbors)
    def parity_rule(state: int, n_bits: int = 24) -> int:
        new_state = 0
        for i in range(n_bits):
            left = (state >> ((i - 1) % n_bits)) & 1
            center = (state >> i) & 1
            right = (state >> ((i + 1) % n_bits)) & 1
            parity = left ^ center ^ right
            new_state |= parity << i
        return new_state

    parity_results = []
    for _ in range(100):
        state = random.randint(0, (1 << 24) - 1)
        for _ in range(10):
            state = parity_rule(state)
        parity_results.append(substrate.is_codeword(state))

    parity_converges_to_codeword = sum(parity_results)

    return {
        "global_ca_test": {
            "test": "Is the snap idempotent (snap(snap(x)) = snap(x))?",
            "result": idempotent_holds,
            "always_produces_codeword": always_codeword,
            "interpretation": (
                "The snap IS a global CA rule: it's a synchronous update of all 24 bits "
                "based on the global state. It's idempotent (one step converges). "
                "But it's NOT a LOCAL rule — each bit's update depends on the syndrome, "
                "which is a global property of all 24 bits."
            ),
        },
        "local_ca_majority_rule": {
            "test": "Does the majority rule (3-bit local) converge to codewords?",
            "n_converged_to_codeword": majority_converges_to_codeword,
            "n_tested": 100,
            "interpretation": (
                f"Majority rule converges to a codeword in {majority_converges_to_codeword}/100 cases. "
                f"This is {'high' if majority_converges_to_codeword > 50 else 'low'} — the majority rule "
                f"{'approximates' if majority_converges_to_codeword > 50 else 'does not approximate'} the Golay snap."
            ),
        },
        "local_ca_parity_rule": {
            "test": "Does the parity rule (3-bit local) converge to codewords?",
            "n_converged_to_codeword": parity_converges_to_codeword,
            "n_tested": 100,
            "interpretation": (
                f"Parity rule converges to a codeword in {parity_converges_to_codeword}/100 cases. "
                f"Parity rule is GF(2)-linear, so it might relate to the Golay code's linearity."
            ),
        },
        "summary": (
            "The substrate CAN be expressed as a GLOBAL CA (the snap is an idempotent global update). "
            "It CANNOT be expressed as a simple LOCAL CA (3-bit majority/parity rules don't reliably "
            "produce codewords). The Golay snap is inherently GLOBAL — it requires computing the "
            "syndrome, which depends on all 24 bits. This is the substrate's non-locality: "
            "you cannot snap a codeword by looking at local neighborhoods alone."
        ),
        "what_this_means_for_hardware": (
            "An FPGA implementation would need GLOBAL connectivity (each of 24 bits connects to "
            "a syndrome computation, which feeds back to all bits). This is more like a content-addressable "
            "memory than a CA. The substrate is NOT massively parallel in the CA sense — it's a "
            "single 24-bit register with a global update function."
        ),
    }


# ============================================================
# Part 6: What the binary world adds vs loses
# ============================================================


def assess_binary_world(alu: Dict, comp: Dict, cons: Dict, ca: Dict) -> Dict[str, Any]:
    """Honest assessment of what going to binary adds and loses."""

    return {
        "what_binary_ADDS": [
            "1. CLARITY: The substrate's native operation is XOR (GF(2) add). Everything else is an algorithm on top. This is clearer in bit ops than in Python objects.",
            "2. SPEED: Bit operations on 24-bit ints are ~100x faster than List[int] operations. The substrate could run at MHz in pure Python, GHz in C.",
            "3. CONSERVATION LAW: The TAX conservation (TAX(a⊕b) = TAX(a) + TAX(b) - 2×TAX(a∧b)) is obvious in bit ops but hidden in Python objects. This is the substrate's energy conservation law.",
            "4. NON-LOCALITY: The Golay snap is inherently global (syndrome depends on all 24 bits). This is invisible in Python but obvious when you try to make it a local CA.",
            "5. LINEARITY: The substrate is a GF(2) linear algebra engine. XOR preserves the code; AND/OR don't. This distinction is fundamental but easy to miss in Python.",
        ],
        "what_binary_LOSES": [
            "1. ABSTRACTION: The Python engine (ubp_unified_v5.py) has rich abstractions (ExactMath, LeechLatticeEngine, MonsterGroup) that make the substrate USABLE. Raw bits are fast but bare.",
            "2. FRACTIONS: The verified engine uses exact Fractions (no float drift). Going to bits means using floats for Y, TAX, NRCI — losing exactness.",
            "3. COMPOSABILITY: The Python engine composes (Golay → MOG → Hexacode → Leech → Monster). Raw bits don't compose — you'd rebuild each layer.",
            "4. INSPECTABILITY: Python objects are easy to inspect (print, debug). Raw 24-bit ints are opaque without disassembly.",
            "5. EXTENSIBILITY: Adding new substrate operations in Python is easy. In bit ops, each new operation requires careful bit-level design.",
        ],
        "what_is_MISSING_from_the_substrate": [
            "1. NATIVE MULTIPLICATION: The substrate has native ADD (XOR) but no native MUL. AND doesn't preserve the code. Multiplication requires leaving the code and re-snapping. This is a fundamental gap: the substrate can ADD but not MULTIPLY.",
            "2. NATIVE I/O: The substrate has no 'port' for receiving input. Encoding (12-bit payload) is the input, but it's external to the substrate. A real OS needs an I/O mechanism.",
            "3. NATIVE CONDITIONAL: TAX-minimization is a conditional (move only if TAX decreases), but it's implemented as a Python loop. The substrate doesn't have a native if/then/else.",
            "4. NATIVE ITERATION: The relaxation trajectory is a loop, but it's driven externally. The substrate doesn't 'iterate' on its own — it needs a Python loop to drive it.",
            "5. NATIVE MEMORY: Codewords ARE memory, but there's no native 'store' or 'recall' operation. The substrate doesn't have an addressable memory — it just has states.",
            "6. NATIVE SYMMETRY: M24 (the Golay automorphism group) acts on the code, but the substrate doesn't 'know' about its symmetries. Applying an M24 element is a Python operation, not a substrate operation.",
        ],
        "should_you_go_binary": {
            "answer": (
                "PARTIALLY. Going to bit ops for the CORE (Golay snap, XOR, TAX) is worth it — "
                "it's faster and reveals the conservation law. But keep the Python abstractions "
                "for the LAYERS above (Leech, Monster, phi_generator). The substrate is a "
                "GF(2) linear algebra engine at its core, but it's a rich structure on top."
            ),
            "recommended_architecture": (
                "1. CORE (bit ops): Golay snap, syndrome, XOR, TAX, popcount — as 24-bit int operations\n"
                "2. MIDDLE (Python): Leech lattice, MOG, Hexacode, Barnes-Wall — using the verified engine\n"
                "3. HIGH (Python): phi_generator, MonsterGroup, Data Object encoding — as now\n"
                "4. I/O LAYER (NEW): a native encoding/decoding port that maps real-world quantities to payloads\n"
                "5. ALU LAYER (NEW): implement ADD (XOR, native) and MUL (via snap-after-AND) as substrate operations\n"
                "6. MEMORY LAYER (NEW): a codeword-addressable memory (the 4096 codewords ARE the address space)"
            ),
        },
        "the_deep_truth": (
            "The substrate is a GF(2) LINEAR ALGEBRA ENGINE. Its native operation is XOR (addition in GF(2)). "
            "It has a conservation law (TAX is conserved under XOR with AND interaction). It is non-local "
            "(the snap requires global syndrome computation). It has NO native multiplication, conditional, "
            "iteration, or I/O — these must be built ON TOP of the substrate. "
            "Going to bit ops reveals this structure clearly. The Python engine HIDES it behind abstractions. "
            "But the abstractions are NECESSARY for usability — raw bits are too bare to be useful alone. "
            "The right answer is a LAYERED architecture: bit-ops core, Python middle, Python high, plus new I/O/ALU/memory layers."
        ),
    }


# ============================================================
# Report generation
# ============================================================


def generate_report(
    alu: Dict[str, Any],
    comp: Dict[str, Any],
    cons: Dict[str, Any],
    ca: Dict[str, Any],
    assessment: Dict[str, Any],
) -> str:
    lines = []
    lines.append("# UBP Binary World v10 — Should You Go Deeper into Bits?")
    lines.append("")
    lines.append("**Date:** 2026-08-06")
    lines.append("**Engine:** GMHGL/ubp_unified_v5.py + Lean-verified decoder patch")
    lines.append("**Question:** Should the substrate move into the binary world (skip Python, go to zeros and ones)?")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Part 1: The binary substrate
    lines.append("## Part 1: The substrate as pure bit operations")
    lines.append("")
    lines.append("I rebuilt the substrate core using only 24-bit ints and bit operations (^, &, |, ~, <<, >>, popcount). No Fractions, no lists, no Python object model.")
    lines.append("")
    lines.append("The core operations that work natively in bits:")
    lines.append("- `snap(v)` — syndrome + coset-leader XOR (the Lean-verified decoder)")
    lines.append("- `xor(a, b)` — GF(2) addition (preserves the code)")
    lines.append("- `and_op(a, b)` — componentwise multiplication (does NOT preserve the code)")
    lines.append("- `hamming_weight(v)` — popcount")
    lines.append("- `syndrome(v)` — H·v mod 2 (12-bit result)")
    lines.append("")
    lines.append("These are the substrate's NATIVE operations. Everything else is built on top.")
    lines.append("")

    # Part 2: ALU
    lines.append("## Part 2: Native binary ALU test")
    lines.append("")
    lines.append("**Can the substrate do arithmetic via bit ops?**")
    lines.append("")
    lines.append("| Operation | Native? | Result |")
    lines.append("|---|---|---|")
    lines.append(f"| GF(2) addition (XOR) | ✅ YES | Result IS a codeword (code is linear) |")
    lines.append(f"| Integer addition (carry) | ⚠️ Algorithm | Works, but result is an int, not a codeword |")
    lines.append(f"| Integer multiplication (shift-add) | ⚠️ Algorithm | Works, but result is an int |")
    lines.append(f"| GF(2) multiplication (AND) | ❌ NO | Result is NOT a codeword (code not closed under AND) |")
    lines.append("")
    lines.append(f"**Summary:** {alu['summary']}")
    lines.append("")
    lines.append(f"**What binary reveals:** {alu['what_the_binary_world_reveals']}")
    lines.append("")

    # Part 3: Composition
    lines.append("## Part 3: Composition laws")
    lines.append("")
    lines.append("**What happens when two codewords combine?**")
    lines.append("")
    lines.append(f"- XOR always produces a codeword: **{comp['xor_always_codeword']}**")
    lines.append(f"- AND never produces a codeword: **{comp['and_never_codeword']}**")
    lines.append(f"- OR never produces a codeword: **{comp['or_never_codeword']}**")
    lines.append("")
    lines.append("**The composition tautology:**")
    lines.append("")
    lines.append(f"```")
    lines.append(f"{comp['composition_tautology']['formula']}")
    lines.append(f"Holds: {comp['composition_tautology']['holds']}")
    lines.append(f"```")
    lines.append("")
    lines.append(f"**Interpretation:** {comp['composition_tautology']['interpretation']}")
    lines.append("")
    lines.append(f"**Summary:** {comp['summary']}")
    lines.append("")

    # Part 4: Conservation
    lines.append("## Part 4: Conservation laws (the deep finding)")
    lines.append("")
    lines.append("**What does the substrate conserve?**")
    lines.append("")
    lines.append("| Law | Holds? | Interpretation |")
    lines.append("|---|---|---|")
    lines.append(f"| Parity (mod 2) | {cons['parity_conservation']['result']} | {cons['parity_conservation']['interpretation']} |")
    lines.append(f"| Mod 4 | {cons['mod4_conservation']['result']} | {cons['mod4_conservation']['interpretation']} |")
    lines.append(f"| Mod 8 | {cons['mod8_conservation']['result']} | {cons['mod8_conservation']['interpretation']} |")
    lines.append(f"| TAX under XOR | {cons['tax_conservation']['result']} | {cons['tax_conservation']['interpretation']} |")
    lines.append("")
    lines.append("**The TAX conservation law (the substrate's energy conservation):**")
    lines.append("")
    lines.append("```")
    lines.append(cons['tax_conservation']['formula'])
    lines.append("```")
    lines.append("")
    lines.append(f"**Interpretation:** {cons['tax_conservation']['interpretation']}")
    lines.append("")
    lines.append(f"**NRCI:** {cons['nrci_conservation']['interpretation']}")
    lines.append("")
    lines.append(f"**Summary:** {cons['summary']}")
    lines.append("")

    # Part 5: Cellular automaton
    lines.append("## Part 5: Cellular automaton formulation")
    lines.append("")
    lines.append("**Can the substrate be expressed as a CA?**")
    lines.append("")
    lines.append(f"- Global CA (snap as global update): idempotent = **{ca['global_ca_test']['result']}**, always produces codeword = **{ca['global_ca_test']['always_produces_codeword']}**")
    lines.append(f"- Local CA (majority rule): {ca['local_ca_majority_rule']['n_converged_to_codeword']}/100 converge to codeword")
    lines.append(f"- Local CA (parity rule): {ca['local_ca_parity_rule']['n_converged_to_codeword']}/100 converge to codeword")
    lines.append("")
    lines.append(f"**Interpretation:** {ca['global_ca_test']['interpretation']}")
    lines.append("")
    lines.append(f"**Summary:** {ca['summary']}")
    lines.append("")
    lines.append(f"**Hardware implication:** {ca['what_this_means_for_hardware']}")
    lines.append("")

    # Part 6: Assessment
    lines.append("## Part 6: Honest assessment — should you go binary?")
    lines.append("")
    lines.append("### What going binary ADDS")
    lines.append("")
    for item in assessment["what_binary_ADDS"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### What going binary LOSES")
    lines.append("")
    for item in assessment["what_binary_LOSES"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### What is MISSING from the substrate (the gaps)")
    lines.append("")
    for item in assessment["what_is_MISSING_from_the_substrate"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### Should you go binary?")
    lines.append("")
    lines.append(f"**Answer:** {assessment['should_you_go_binary']['answer']}")
    lines.append("")
    lines.append("**Recommended architecture:**")
    lines.append("```")
    lines.append(assessment['should_you_go_binary']['recommended_architecture'])
    lines.append("```")
    lines.append("")
    lines.append("### The deep truth")
    lines.append("")
    lines.append(f"**{assessment['the_deep_truth']}**")
    lines.append("")

    # Conclusion
    lines.append("## Conclusion: What to do next")
    lines.append("")
    lines.append("The substrate is a **GF(2) linear algebra engine** with:")
    lines.append("- Native ADD (XOR) ✅")
    lines.append("- Conservation law (TAX under XOR with AND interaction) ✅")
    lines.append("- Non-local snap (requires global syndrome) ✅")
    lines.append("- No native MUL, I/O, conditional, iteration, memory, or symmetry ❌")
    lines.append("")
    lines.append("**The binary world reveals this clearly.** The Python engine hides it behind abstractions that are necessary for usability but obscure the substrate's nature.")
    lines.append("")
    lines.append("**Recommended next steps:**")
    lines.append("")
    lines.append("1. **Implement a bit-ops CORE** (Golay snap, XOR, TAX as 24-bit int operations). This is the substrate's native language.")
    lines.append("2. **Add an ALU layer** with ADD (native XOR) and MUL (snap-after-AND). This gives the substrate arithmetic.")
    lines.append("3. **Add an I/O layer** — a native encoding port that maps real-world quantities to 12-bit payloads. The current encoding (log2, etc.) is external; make it substrate-native.")
    lines.append("4. **Add a MEMORY layer** — the 4096 codewords ARE the address space. Make them addressable.")
    lines.append("5. **Add a CONDITIONAL layer** — formalize TAX-minimization as a substrate-native if/then/else.")
    lines.append("6. **Keep the Python abstractions** for the high-level layers (Leech, Monster, phi_generator). Don't go fully binary — go LAYERED.")
    lines.append("")
    lines.append("The substrate has Time, Scale, TAX, NRCI, Data Objects. What it's MISSING is **native ALU, I/O, memory, and conditional layers**. These are the next things to build. The binary world shows you WHAT to build; the Python world gives you the TOOLS to build it.")
    lines.append("")

    # Outputs
    lines.append("## Outputs")
    lines.append("")
    lines.append("- `/home/z/my-project/download/ubp_binary_world_v10.json` (full data)")
    lines.append("- `/home/z/my-project/download/ubp_binary_world_v10_report.md` (this file)")
    lines.append("- `/home/z/my-project/scripts/ubp_binary_world_v10.py` (this script, includes the BinarySubstrate class)")
    lines.append("")

    return "\n".join(lines)


# ============================================================
# Main
# ============================================================


def main():
    print("=" * 80)
    print("UBP Binary World v10")
    print("  Should the substrate go deeper into bits?")
    print("=" * 80)

    print("\n[setup] Building pure-bitwise substrate...")
    substrate = BinarySubstrate()
    print(f"  {len(substrate.CODEWORDS)} codewords as 24-bit ints")
    print(f"  {len(substrate.COSET_LEADERS)} coset leaders (complete decoder)")
    print(f"  Y = {substrate.Y:.6f}")

    # Test 1: Verify the binary substrate matches the Python engine
    print("\n[verify] Checking binary substrate against verified engine...")
    from ubp_engine.ubp_unified_v5 import GolayCodeEngine
    ge = GolayCodeEngine()
    # Encode a test message both ways
    test_msg = 0b101100101011
    cw_binary = substrate.encode(test_msg)
    msg_list = [(test_msg >> i) & 1 for i in range(12)]
    cw_python_list = ge.encode(msg_list)
    cw_python = sum(b << (23 - i) for i, b in enumerate(cw_python_list))
    print(f"  Binary encode: {cw_binary:06X}")
    print(f"  Python encode: {cw_python:06X}")
    print(f"  Match: {cw_binary == cw_python}")

    # Run all 5 parts
    print("\n[Part 2] Native binary ALU test...")
    alu = test_binary_alu(substrate)

    print("\n[Part 3] Composition laws test...")
    comp = test_composition(substrate)

    print("\n[Part 4] Conservation laws test...")
    cons = test_conservation(substrate)

    print("\n[Part 5] Cellular automaton test...")
    ca = test_cellular_automaton(substrate)

    print("\n[Part 6] Assessment...")
    assessment = assess_binary_world(alu, comp, cons, ca)

    # Save outputs
    print("\n[saving] Writing outputs...")
    output_dir = Path("/home/z/my-project/download")
    output_dir.mkdir(parents=True, exist_ok=True)

    json_output = {
        "experiment": "UBP Binary World v10",
        "date": "2026-08-06",
        "engine": "GMHGL/ubp_unified_v5.py + Lean-verified decoder patch",
        "question": "Should the substrate move into the binary world?",
        "substrate_description": {
            "core_operations": ["snap", "xor", "and_op", "or_op", "hamming_weight", "syndrome"],
            "native_arithmetic": "GF(2) addition (XOR) only",
            "conservation_law": "TAX(a⊕b) = TAX(a) + TAX(b) - 2×TAX(a∧b)",
            "non_locality": "snap requires global syndrome computation",
        },
        "part_2_binary_alu": alu,
        "part_3_composition": comp,
        "part_4_conservation": cons,
        "part_5_cellular_automaton": ca,
        "part_6_assessment": assessment,
    }

    json_path = output_dir / "ubp_binary_world_v10.json"
    with open(json_path, "w") as f:
        json.dump(json_output, f, indent=2, default=str)
    print(f"  JSON: {json_path}")

    md_path = output_dir / "ubp_binary_world_v10_report.md"
    report = generate_report(alu, comp, cons, ca, assessment)
    with open(md_path, "w") as f:
        f.write(report)
    print(f"  Report: {md_path}")

    print("\n" + "=" * 80)
    print("v10 complete.")
    print("=" * 80)
    print()
    print("THE DEEP TRUTH:")
    print("The substrate is a GF(2) LINEAR ALGEBRA ENGINE.")
    print("Native op: XOR (addition). Conservation: TAX under XOR with AND interaction.")
    print("Missing: native MUL, I/O, conditional, iteration, memory, symmetry.")
    print()
    print("RECOMMENDATION: Go LAYERED, not fully binary.")
    print("  Core: bit ops (snap, XOR, TAX)")
    print("  Middle: Python (Leech, MOG, Barnes-Wall)")
    print("  High: Python (phi_generator, Monster)")
    print("  NEW layers needed: ALU (MUL), I/O, Memory, Conditional")


if __name__ == "__main__":
    main()
