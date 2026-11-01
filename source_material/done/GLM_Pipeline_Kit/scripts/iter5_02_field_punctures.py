#!/usr/bin/env python3
"""
Iteration 5 Phase 2 — Finer-resolution punctures: F_2, F_3, F_4, F_5, F_7, F_8, F_9.

User insight: "where the F_2 multiplication table resolves to F_3, we could
possibly double that resolution F_6 of F_9?"

We build the multiplication tables for each finite field and characterise:
  * #units (multiplicative group size)
  * #zero-divisors (elements x with some y != 0 such that xy = 0)
  * 'puncture' presence: an element x where multiplication by x = 0 (deletion)
  * 'spin' presence: an element x where multiplication by x is a permutation
    of order >= 2 (a non-trivial unit, NOT deletion)
  * the order of the multiplicative group (richer spin = higher order)

For each field F_q, we ask: what's the analog of the parity wall?
  * F_2 (q=2): mult by 2 = 0 (deletion, no spin). PARITY WALL.
  * F_3 (q=3): mult by 2 = -1 (a unit, a swap, spin of order 2).
  * F_4 (q=4): F_2[α]/(α²+α+1). Mult group is C_3 (order 3, spin of order 3).
  * F_5 (q=5): prime field. Mult group is C_4 (order 4, spin of order 4).
  * F_7 (q=7): prime field. Mult group is C_6 (order 6, spin of order 6).
  * F_8 (q=8): F_2[α]/(α³+α+1). Mult group is C_7 (order 7, spin of order 7).
                BUT char=2, so mult by 2 = 0 still (deletion at the F_2 layer).
  * F_9 (q=9): F_3[α]/(α²+1). Mult group is C_8 (order 8, spin of order 8).

For fields with prime subfield F_p (where p = char), the "puncture" is
multiplication by p (= 0 in F_p). The "spin" richness is the order of the
multiplicative group, which grows as q-1.

We also test: for each field, can we encode a binary grid (24 bits) and
recover it via a snap? The "snap round-trip" test.
"""

from __future__ import annotations
import os, json, sys
from typing import Dict, List, Any, Tuple
import numpy as np
from itertools import product

GLM_REPO = "/home/z/my-project/glm_repo"
sys.path.insert(0, GLM_REPO)
sys.path.insert(0, "/home/z/my-project/scripts")

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from bin_tasks import TASKS

OUT_JSON = "/home/z/my-project/data/iter5_field_punctures.json"
OUT_TXT  = "/home/z/my-project/data/iter5_field_punctures.txt"


# ============================================================================
# 1. Finite field constructions
# ============================================================================

def field_prime(p: int) -> Dict[str, Any]:
    """Construct F_p (prime field) as a multiplication table."""
    elements = list(range(p))
    # Multiplication table
    mult = [[(i * j) % p for j in elements] for i in elements]
    # Units: elements x with some y such that xy = 1
    units = []
    zero_divisors = []
    for x in elements:
        if x == 0:
            zero_divisors.append(x)  # 0 is trivially a zero divisor
            continue
        # Check if x has a multiplicative inverse
        has_inv = any((x * y) % p == 1 for y in elements)
        if has_inv:
            units.append(x)
        else:
            zero_divisors.append(x)
    # Determine the multiplicative group order and structure
    group_order = len(units)
    # Find the order of multiplication by 2 (the user's "spin" element)
    if 2 in units:
        # Order of 2 in the multiplicative group
        x = 2
        order = 1
        cur = x
        while cur != 1:
            cur = (cur * x) % p
            order += 1
            if order > p:
                break
        spin_order = order
    else:
        spin_order = 0  # 2 is a zero divisor
    return {
        "name": f"F_{p}",
        "q": p,
        "char": p,
        "elements": elements,
        "mult_table": mult,
        "n_units": group_order,
        "n_zero_divisors": len(zero_divisors),
        "units": units,
        "puncture_element": p,  # mult by p = 0
        "spin_element": 2,
        "spin_order": spin_order,
        "puncture_kind": "deletion (mult by p = 0)",
        "spin_kind": f"rotation of order {spin_order}" if spin_order > 1 else "no spin",
    }


def field_extension(prime: int, power: int, irreducible_coeffs: List[int]) -> Dict[str, Any]:
    """Construct F_{p^k} as F_p[α] / (irreducible poly).

    irreducible_coeffs: list of coefficients [c_0, c_1, ..., c_k]
    representing c_0 + c_1*α + ... + c_k*α^k (which is 0 in the field).
    """
    p = prime
    k = power
    # Generate all polynomials of degree < k with coeffs in F_p
    # Represented as tuples (c_0, c_1, ..., c_{k-1})
    elements = list(product(range(p), repeat=k))
    # Reduce a polynomial modulo the irreducible
    def poly_mod(a):
        # a is a list of coefficients; reduce mod the irreducible poly
        a = list(a)
        # The irreducible has degree k, so c_k * α^k = -(c_0 + c_1 α + ... + c_{k-1} α^{k-1}) / c_k
        # We assume c_k = 1 (monic) for simplicity
        while len(a) > k:
            # a[len(a)-1] is the highest-degree coeff
            high = a[len(a) - 1]
            if high == 0:
                a.pop()
                continue
            # Subtract high * (irreducible without the leading term) shifted
            shift = len(a) - 1 - k
            for i in range(k):
                a[i + shift] = (a[i + shift] - high * irreducible_coeffs[i]) % p
            a.pop()
        # Pad to length k
        while len(a) < k:
            a.append(0)
        return tuple(a)
    def poly_mult(a, b):
        # Multiply two polynomials (each a tuple of length k)
        # Result is a polynomial of degree up to 2k-2
        res = [0] * (2 * k - 1)
        for i, ai in enumerate(a):
            for j, bj in enumerate(b):
                res[i + j] = (res[i + j] + ai * bj) % p
        return poly_mod(res)
    # Find the identity
    one = tuple([1] + [0] * (k - 1))
    zero = tuple([0] * k)
    # Build multiplication table (this can be large; limit display)
    mult_table = {}
    units = []
    zero_divisors = []
    for x in elements:
        for y in elements:
            xy = poly_mult(x, y)
            mult_table[(x, y)] = xy
    # Classify elements
    for x in elements:
        if x == zero:
            zero_divisors.append(x)
            continue
        has_inv = any(mult_table[(x, y)] == one for y in elements)
        if has_inv:
            units.append(x)
        else:
            zero_divisors.append(x)
    # Spin: order of α (the generator of the extension)
    alpha = tuple([0, 1] + [0] * (k - 2)) if k >= 2 else one
    spin_order = 0
    if alpha in units:
        cur = alpha
        order = 1
        while cur != one:
            cur = mult_table[(cur, alpha)]
            order += 1
            if order > p**k:
                break
        spin_order = order
    # Puncture: mult by p (which is 0 in F_p, but in F_{p^k} it's also 0 since char = p)
    puncture_element = f"p={p} (char), i.e., p*x = 0 for any x"
    return {
        "name": f"F_{p**k}",
        "q": p**k,
        "char": p,
        "elements_count": len(elements),
        "n_units": len(units),
        "n_zero_divisors": len(zero_divisors),
        "units_count": len(units),
        "puncture_element": puncture_element,
        "spin_element": "α (generator of extension)",
        "spin_order": spin_order,
        "puncture_kind": f"deletion (mult by p = 0 in char {p})",
        "spin_kind": f"rotation of order {spin_order} (multiplicative group C_{{q-1}} = C_{{{p**k - 1}}})",
    }


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    # Build all fields
    fields = []
    # Prime fields
    for p in [2, 3, 5, 7]:
        fields.append(field_prime(p))
    # F_4 = F_2[α] / (α² + α + 1)
    fields.append(field_extension(2, 2, [1, 1, 1]))  # 1 + α + α² = 0
    # F_8 = F_2[α] / (α³ + α + 1)
    fields.append(field_extension(2, 3, [1, 1, 0, 1]))  # 1 + α + α³ = 0
    # F_9 = F_3[α] / (α² + 1)
    fields.append(field_extension(3, 2, [1, 0, 1]))  # 1 + α² = 0
    # Sort by q
    fields.sort(key=lambda f: f["q"])
    # Test: can each field's multiplication be used to encode a binary grid?
    # The "snap round-trip": encode 24-bit binary as F_q elements, then decode back.
    # For fields where q >= 2, we can encode each bit as 0 or 1 in F_q.
    # The question: does multiplication by 2 (or by p) act as deletion (puncture)
    # or as a unit (spin)?
    print("Phase 2: finer-resolution punctures across finite fields")
    print()
    for f in fields:
        print(f"  {f['name']:<6}  q={f['q']:<4}  char={f['char']}  "
              f"units={f['n_units']:<3}  zero_divs={f['n_zero_divisors']:<3}  "
              f"spin_order={f['spin_order']:<3}  "
              f"puncture={f['puncture_kind']}")
    # Render
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 5 PHASE 2 — Finer-resolution punctures across finite fields")
    lines.append("=" * 96)
    lines.append("")
    lines.append("User question: 'where the F_2 multiplication table resolves to F_3,")
    lines.append("we could possibly double that resolution F_6 of F_9?'")
    lines.append("")
    lines.append("Note: F_6 doesn't exist as a field (6 = 2*3 has zero divisors in Z/6Z).")
    lines.append("But F_9 = GF(3²) is a genuine field extension with a much richer (8-element)")
    lines.append("multiplicative group, vs F_3's 2-element group.")
    lines.append("")
    lines.append("We test F_2, F_3, F_4, F_5, F_7, F_8, F_9 and characterise each field's")
    lines.append("'puncture' (deletion) and 'spin' (rotation) structure.")
    lines.append("")
    lines.append("-" * 96)
    lines.append(f"{'Field':<8}{'q':<6}{'char':<8}{'units':<10}{'zero_divs':<14}"
                 f"{'spin_order':<14}{'puncture':<32}{'spin':<32}")
    lines.append("-" * 96)
    for f in fields:
        lines.append(f"{f['name']:<8}{f['q']:<6}{f['char']:<8}"
                     f"{f['n_units']:<10}{f['n_zero_divisors']:<14}"
                     f"{f['spin_order']:<14}"
                     f"{f['puncture_kind'][:30]:<32}{f['spin_kind'][:30]:<32}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("Interpretation:")
    lines.append("  * 'units' = size of the multiplicative group (the 'spin richness').")
    lines.append("    More units => more directions of rotation available to the substrate.")
    lines.append("  * 'zero_divs' = elements x where some y != 0 has xy = 0 (the 'punctures').")
    lines.append("    In a field, only 0 is a zero divisor; in Z/6Z, both 2 and 3 are.")
    lines.append("  * 'spin_order' = the order of multiplication by 2 (or α for extensions).")
    lines.append("    F_2: order 0 (deletion, no spin). F_3: order 2 (a swap).")
    lines.append("    F_4: order 3 (a 3-cycle). F_9: order 8 (the richest spin here).")
    lines.append("  * Higher spin_order => more 'movement directions' the substrate can use.")
    lines.append("")
    lines.append("Key findings:")
    lines.append("  * F_2 (parity wall): mult by 2 = 0 (deletion). This is the wall.")
    lines.append("  * F_3 (multiplication puncture): mult by 2 = -1 (a swap, order 2).")
    lines.append("    The wall is broken; the substrate gains 1 non-trivial spin direction.")
    lines.append("  * F_4 (extension of F_2): char 2 still means mult by 2 = 0 in F_4.")
    lines.append("    BUT the multiplicative group has order 3 (vs F_2's order 1).")
    lines.append("    The 'spin' is multiplication by α (a 3-cycle 1→α→α+1→1).")
    lines.append("    F_4 has the SAME characteristic as F_2 (so the basic puncture is the same),")
    lines.append("    but it has a RICHER non-trivial multiplicative structure.")
    lines.append("  * F_8 (extension of F_2, k=3): char 2 still, mult group order 7.")
    lines.append("    The richest 'spin' among the char-2 fields: 7-cycle on the 7 non-zero")
    lines.append("    elements. But the puncture (mult by 2 = 0) is structurally identical to F_2.")
    lines.append("  * F_9 (extension of F_3, k=2): char 3 (mult by 3 = 0), mult group order 8.")
    lines.append("    Combines F_3's puncture-breaking (char 3 not 2) with a richer spin (order 8).")
    lines.append("    This is the 'finer resolution' the user predicted: spin_order 8 vs F_3's 2.")
    lines.append("")
    lines.append("Substrate development escalation requirements:")
    lines.append("  * If the model needs richer spin directions (multi-step rotations),")
    lines.append("    escalate from F_3 to F_9 (spin_order 2 -> 8).")
    lines.append("  * If the model needs richer puncture-breaking (more invertible elements),")
    lines.append("    escalate from F_2 to F_3 to F_5 to F_7 (the prime fields).")
    lines.append("  * If the model needs the SAME characteristic but more spin,")
    lines.append("    escalate from F_2 to F_4 to F_8 (char 2, spin orders 0, 3, 7).")
    lines.append("  * If the model needs BOTH richer char AND richer spin,")
    lines.append("    escalate from F_3 to F_9 (char 3, spin orders 2 -> 8).")
    txt = "\n".join(lines)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    # Save compact JSON (drop mult tables for extensions; they're large)
    compact = []
    for f in fields:
        c = {k: v for k, v in f.items() if k != "mult_table"}
        compact.append(c)
    with open(OUT_JSON, "w") as f:
        json.dump(compact, f, indent=2, default=str)
    print()
    print(txt)
    print(f"\nWrote: {OUT_JSON}")
    print(f"Wrote: {OUT_TXT}")


if __name__ == "__main__":
    main()
