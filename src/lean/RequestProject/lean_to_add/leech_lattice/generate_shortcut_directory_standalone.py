"""
================================================================================
UBP 24D LEECH LATTICE GEODESIC SHORTCUT DIRECTORY (STANDALONE AUDITOR)
================================================================================
Author: E R A Craig, New Zealand & UBP Research Cortex v5.0
Substrate Engine: ubp_unified_v5.py (v5.4.1)

PURPOSE:
Audits integer state transitions in deep numerical space (N > 1,000,000) using
continuous 24-bit bit-shift mapping. Measures 24D jump vectors (\Delta v), 
jump norms (d^2 = ||\Delta v||^2), Leech lattice quantization (d^2 in 2Z), and
Class B Minimal Vector Octad transitions (d^2 = 8).

NO KB GENERATOR / MINTING CODE IS INCLUDED IN THIS SCRIPT.
================================================================================
"""

import json
import math
from fractions import Fraction

# UBP Core Architecture Imports
from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE, to_gray_code, BLA
from value_geometry import profile, is_prime
from ubp_tgic_engine import TGICInteractionEngine

def map_continuous_vector(n):
    """
    Continuous 24-bit bit-shift mapping without modulo 256 wrapping.
    
    EXPLANATION:
    Mapping large integers with modulo 256 (n % 256) forces coordinate collisions 
    for N > 1,000,000, locking 1D prime monads onto a single X=Y=Z hyper-diagonal.
    By unpacking bits across three 8-bit registers (X = bits 0..7, Y = bits 8..15,
    Z = bits 16..23), states expand naturally across the full 24D canvas.
    """
    # 1. Compute internal factor geometry via ValueGeometry
    prof = profile(n)
    factors = prof.prime_factors
    vec = [0] * 24

    if prof.is_prime:
        # Primes (1D Monads): Distribute integer magnitude across 3 8-bit registers.
        # This preserves 1D monad linear integrity while expanding spatial range.
        x_val = n & 0xFF
        y_val = (n >> 8) & 0xFF
        z_val = (n >> 16) & 0xFF

        vec[0:8] = to_gray_code(x_val, 8)
        vec[8:16] = to_gray_code(y_val, 8)
        vec[16:24] = to_gray_code(z_val, 8)
    else:
        # Composites (3D Polyhedra): Map cumulative factor weights across X, Y, Z.
        # x_val = p1^e1, y_val = p2^e2, z_val = p3^e3 * p4^e4 ...
        x_val = factors[0][0] ** factors[0][1] if len(factors) > 0 else 1
        y_val = factors[1][0] ** factors[1][1] if len(factors) > 1 else 1
        z_val = math.prod(p**e for p, e in factors[2:]) if len(factors) > 2 else 1

        vec[0:8] = to_gray_code(x_val & 0xFF, 8)
        vec[8:16] = to_gray_code(y_val & 0xFF, 8)
        vec[16:24] = to_gray_code(z_val & 0xFF, 8)

    # 2. Golay [24, 12, 8] Error Correction
    # Snaps noisy/raw 24-bit Gray states onto nearest of 4,096 perfect codewords (t <= 3)
    snapped, meta = GOLAY_ENGINE.snap_to_codeword(vec)
    return snapped, meta, prof

def run_standalone_shortcut_audit():
    """
    Main execution loop. Scans test sequences, computes 24D jump vectors (\Delta v),
    measures norm squared d^2, and evaluates TGIC 3-6-9 genesis stability.
    """
    print("=" * 80)
    print("UBP 24D LEECH LATTICE GEODESIC SHORTCUT DIRECTORY (STANDALONE AUDIT)")
    print("=" * 80)

    # Initialize TGIC Constraint & Interaction Engine
    tgic = TGICInteractionEngine()

    # Define Test Sequences in Deep Numerical Space (N > 1,000,000)
    interfacial_sequence = list(range(1000033, 1000051))  # 18 consecutive deep integers
    
    deep_primes = []
    candidate = 1000000
    while len(deep_primes) < 20:
        if is_prime(candidate):
            deep_primes.append(candidate)
        candidate += 1

    audit_sequences = [
        ("Deep Interfacial Sequence (N = 1,000,033 .. 1,000,050)", interfacial_sequence),
        ("Deep Prime-to-Prime Trajectory (P > 1,000,000)", deep_primes)
    ]

    catalog = {}
    all_d2_values = []
    octad_count = 0
    total_steps = 0

    for seq_label, sequence in audit_sequences:
        print(f"\nScanning Sequence: {seq_label} ({len(sequence)} nodes)...")
        steps = []
        node_states = []

        # Step 1: Map all nodes to 24D Leech coordinates and evaluate metrics
        for n in sequence:
            snapped, meta, prof = map_continuous_vector(n)
            tax = LEECH_ENGINE.calculate_symmetry_tax(snapped)
            nrci = LEECH_ENGINE.calculate_nrci(snapped)
            ortho = tgic.constraints.check_3_axis_orthogonality(snapped)
            stab = tgic.calculate_total_stability(snapped)

            node_states.append({
                "n": n,
                "snapped_vector": snapped,
                "meta": meta,
                "profile": prof,
                "nrci": float(nrci),
                "symmetry_tax": float(tax),
                "orthogonality": float(ortho),
                "tgic_stability": float(stab)
            })

        # Step 2: Analyze transitions between consecutive nodes (Geodesic Jump Vectors)
        for i in range(len(node_states) - 1):
            curr = node_states[i]
            nxt = node_states[i+1]

            # 24D Jump Vector: \Delta v = v_{target} - v_{origin}
            jump_vec = [b - a for a, b in zip(curr["snapped_vector"], nxt["snapped_vector"])]
            
            # Norm Squared (Euclidean Distance Squared in 24D Space): d^2 = ||\Delta v||^2
            d2 = sum(x**2 for x in jump_vec)
            
            # Class B Minimal Vector Octad check: d^2 == 8 (Norm^2 = 32 in x8 representation)
            is_octad = (d2 == 8)
            
            # Leech Quantization check: d^2 % 2 == 0 (Distance squared must be an even integer)
            is_even = (d2 % 2 == 0)

            all_d2_values.append(d2)
            total_steps += 1
            if is_octad: 
                octad_count += 1

            steps.append({
                "step": i + 1,
                "origin_node": {
                    "n": curr["n"],
                    "is_prime": curr["profile"].is_prime,
                    "factor_imbalance": curr["profile"].imbalance,
                    "nrci": curr["nrci"],
                    "3axis_orthogonality": curr["orthogonality"]
                },
                "target_node": {
                    "n": nxt["n"],
                    "is_prime": nxt["profile"].is_prime,
                    "factor_imbalance": nxt["profile"].imbalance,
                    "nrci": nxt["nrci"],
                    "3axis_orthogonality": nxt["orthogonality"]
                },
                "jump_vector_24d": jump_vec,
                "jump_norm_d2": d2,
                "is_minimal_octad_step": is_octad,
                "leech_even_quantized": is_even
            })

        catalog[seq_label] = steps

    # Calculate Overall Summary Statistics
    avg_d2 = sum(all_d2_values) / len(all_d2_values) if all_d2_values else 0.0
    even_quant_pct = (sum(1 for d in all_d2_values if d % 2 == 0) / len(all_d2_values)) * 100.0 if all_d2_values else 0.0
    octad_pct = (octad_count / total_steps) * 100.0 if total_steps else 0.0

    summary = {
        "total_transitions_audited": total_steps,
        "avg_jump_norm_d2": round(avg_d2, 4),
        "even_quantization_rate_pct": round(even_quant_pct, 2),
        "class_b_octad_step_rate_pct": round(octad_pct, 2),
        "observed_jump_norms": sorted(list(set(all_d2_values)))
    }

    full_output = {
        "summary": summary,
        "catalogs": catalog
    }

    # Save Catalog to JSON File
    output_filename = "lattice_shortcut_directory_standalone.json"
    with open(output_filename, "w") as f:
        json.dump(full_output, f, indent=2)

    print("\n" + "=" * 80)
    print("AUDIT SUMMARY & RESULTS")
    print("=" * 80)
    print(f"✅ Saved full directory to:     '{output_filename}'")
    print(f"  • Total Transitions Audited:   {total_steps}")
    print(f"  • Average Jump Norm (d²):      {avg_d2:.4f}")
    print(f"  • Even Quantization Rate:      {even_quant_pct:.1f}%  (d² in 2Z)")
    print(f"  • Class B Octad Step Rate:     {octad_pct:.1f}%  (d² = 8 Minimal Vectors)")
    print(f"  • Observed Jump Norms (d²):    {summary['observed_jump_norms']}")
    print("=" * 80)

if __name__ == "__main__":
    run_standalone_shortcut_audit()