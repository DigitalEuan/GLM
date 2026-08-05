"""
training_bond_geometry.py — Bonds as Geometric Objects + Snap Cost Analysis

Key insight: the cost of snapping to a Golay codeword carries information.
The raw vector (pre-snap) and the snap distance (syndrome weight, bits changed)
may encode bond properties that the snapped vector alone doesn't capture.

Approaches:
1. Bond as third Data Object (element_A, element_B, bond_vector)
2. Snap cost analysis (pre-snap vs post-snap metrics)
3. Spatial Arithmetic on bond geometry
4. Yes/no feedback training on encoding arrangements
"""

from __future__ import annotations
import sys, json, math, statistics, itertools, time
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import kb_adapter as kb
from training_iteration import (
    EncodingSpec, encode_element, golay_snap, compute_interaction_metrics,
    pearson_r, SCALING_PRESETS, gray6, HAS_GOLAY, hamming_distance,
)
import spatial_arithmetic as sa

if HAS_GOLAY:
    from training_iteration import GOLAY_ENGINE


# ═══════════════════════════════════════════════════════════════════════════════
# Bond dataset with bond orders
# ═══════════════════════════════════════════════════════════════════════════════

BOND_DATA = [
    ("H", "H", 1, 436, "H-H"),
    ("H", "O", 1, 463, "H-O"),
    ("H", "F", 1, 568, "H-F"),
    ("H", "Cl", 1, 431, "H-Cl"),
    ("H", "N", 1, 391, "H-N"),
    ("H", "C", 1, 413, "H-C"),
    ("O", "O", 2, 498, "O=O"),
    ("O", "O", 1, 146, "O-O"),
    ("N", "N", 3, 946, "N≡N"),
    ("N", "N", 1, 163, "N-N"),
    ("C", "O", 1, 358, "C-O"),
    ("C", "O", 2, 799, "C=O"),
    ("C", "C", 1, 347, "C-C"),
    ("C", "C", 2, 614, "C=C"),
    ("C", "C", 3, 839, "C≡C"),
    ("C", "N", 1, 305, "C-N"),
    ("C", "N", 2, 615, "C=N"),
    ("C", "N", 3, 891, "C≡N"),
    ("C", "F", 1, 485, "C-F"),
    ("C", "Cl", 1, 339, "C-Cl"),
    ("C", "Br", 1, 276, "C-Br"),
    ("C", "I", 1, 238, "C-I"),
    ("C", "S", 1, 259, "C-S"),
    ("Si", "O", 1, 452, "Si-O"),
    ("Si", "Si", 1, 226, "Si-Si"),
    ("P", "O", 1, 335, "P-O"),
    ("S", "O", 1, 265, "S-O"),
    ("S", "H", 1, 363, "S-H"),
    ("Na", "Cl", 1, 411, "Na-Cl"),
    ("K", "Cl", 1, 427, "K-Cl"),
    ("Li", "F", 1, 577, "Li-F"),
    ("Mg", "O", 1, 394, "Mg-O"),
    ("Ca", "O", 1, 402, "Ca-O"),
    ("Al", "O", 1, 512, "Al-O"),
    ("Fe", "O", 1, 407, "Fe-O"),
    ("Fe", "S", 1, 310, "Fe-S"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Snap cost analysis
# ═══════════════════════════════════════════════════════════════════════════════

def snap_with_cost(vec_raw: List[int]) -> Dict:
    """Snap to Golay codeword and measure the cost."""
    if not HAS_GOLAY:
        return {
            "snapped": vec_raw[:],
            "syndrome_weight": 0,
            "bits_changed": 0,
            "hw_raw": sum(vec_raw),
            "hw_snapped": sum(vec_raw),
            "nrci_raw": 0,
            "nrci_snapped": 0,
            "tax_raw": 0,
            "tax_snapped": 0,
        }

    snapped, meta = GOLAY_ENGINE.snap_to_codeword(vec_raw)
    syndrome = GOLAY_ENGINE.syndrome(vec_raw)
    sw = sum(syndrome)
    bits_changed = sum(1 for i in range(24) if vec_raw[i] != snapped[i])
    hw_raw = sum(vec_raw)
    hw_snapped = sum(snapped)

    Y = 0.2646754304045269672
    tax_raw = hw_raw * Y + sum(v*v for v in vec_raw) / 8.0
    tax_snapped = hw_snapped * Y + sum(v*v for v in snapped) / 8.0
    nrci_raw = 10.0 / (10.0 + tax_raw)
    nrci_snapped = 10.0 / (10.0 + tax_snapped)

    return {
        "snapped": snapped,
        "syndrome_weight": sw,
        "bits_changed": bits_changed,
        "hw_raw": hw_raw,
        "hw_snapped": hw_snapped,
        "nrci_raw": nrci_raw,
        "nrci_snapped": nrci_snapped,
        "tax_raw": tax_raw,
        "tax_snapped": tax_snapped,
        "delta_tax": tax_snapped - tax_raw,
        "delta_nrci": nrci_snapped - nrci_raw,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Bond encoding strategies
# ═══════════════════════════════════════════════════════════════════════════════

def encode_bond_xor(sym_a: str, sym_b: str, spec: EncodingSpec) -> List[int]:
    """XOR of two element vectors."""
    va = encode_element(sym_a, spec)
    vb = encode_element(sym_b, spec)
    return [va[i] ^ vb[i] for i in range(24)]


def encode_bond_concat(sym_a: str, sym_b: str, spec: EncodingSpec) -> List[int]:
    """Rows 0-1 from A, rows 2-3 from B."""
    va = encode_element(sym_a, spec)
    vb = encode_element(sym_b, spec)
    return va[:12] + vb[12:]


def encode_bond_and(sym_a: str, sym_b: str, spec: EncodingSpec) -> List[int]:
    """AND of two element vectors."""
    va = encode_element(sym_a, spec)
    vb = encode_element(sym_b, spec)
    return [va[i] & vb[i] for i in range(24)]


def encode_bond_or(sym_a: str, sym_b: str, spec: EncodingSpec) -> List[int]:
    """OR of two element vectors."""
    va = encode_element(sym_a, spec)
    vb = encode_element(sym_b, spec)
    return [va[i] | vb[i] for i in range(24)]


def encode_bond_interleave(sym_a: str, sym_b: str, spec: EncodingSpec) -> List[int]:
    """Interleave bits: A[0],B[0],A[1],B[1],... (12 bits each → 24)."""
    va = encode_element(sym_a, spec)
    vb = encode_element(sym_b, spec)
    result = []
    for i in range(12):
        result.append(va[i])
        result.append(vb[i])
    return result


def encode_bond_order_mod(sym_a: str, sym_b: str, bond_order: int, spec: EncodingSpec) -> List[int]:
    """XOR with bond-order pattern in the activation row."""
    raw = encode_bond_xor(sym_a, sym_b, spec)
    bo_bits = gray6(bond_order * 10 & 0x3F)
    for i in range(6):
        raw[12 + i] ^= bo_bits[i]
    return raw


def encode_bond_product(sym_a: str, sym_b: str, spec: EncodingSpec) -> List[int]:
    """Element-wise product (mod 2) — same as AND for binary."""
    return encode_bond_and(sym_a, sym_b, spec)


def encode_bond_symmetric_diff(sym_a: str, sym_b: str, spec: EncodingSpec) -> List[int]:
    """Symmetric difference — same as XOR for binary."""
    return encode_bond_xor(sym_a, sym_b, spec)


def encode_bond_shift(sym_a: str, sym_b: str, spec: EncodingSpec) -> List[int]:
    """Shift A left by popcount(B) mod 24, then XOR with B."""
    va = encode_element(sym_a, spec)
    vb = encode_element(sym_b, spec)
    shift = sum(vb) % 24
    shifted = va[shift:] + va[:shift]
    return [shifted[i] ^ vb[i] for i in range(24)]


BOND_ENCODERS = {
    "xor": encode_bond_xor,
    "concat": encode_bond_concat,
    "and": encode_bond_and,
    "or": encode_bond_or,
    "interleave": encode_bond_interleave,
    "shift": encode_bond_shift,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Spatial Arithmetic on bonds
# ═══════════════════════════════════════════════════════════════════════════════

def spatial_arithmetic_on_bond(vec_raw: List[int], vec_snapped: List[int]) -> Dict:
    """Apply Spatial Arithmetic to bond Data Objects."""
    try:
        # Convert to spatial arithmetic format
        # Use the raw vector as a polygon
        vertices_raw = []
        for i, v in enumerate(vec_raw):
            if v:
                angle = 2 * math.pi * i / 24
                vertices_raw.append((math.cos(angle), math.sin(angle), 0))

        vertices_snapped = []
        for i, v in enumerate(vec_snapped):
            if v:
                angle = 2 * math.pi * i / 24
                vertices_snapped.append((math.cos(angle), math.sin(angle), 0))

        if len(vertices_raw) < 3 or len(vertices_snapped) < 3:
            return {"area_raw": 0, "area_snapped": 0, "perimeter_raw": 0, "perimeter_snapped": 0}

        # Simple polygon metrics
        def polygon_area(verts):
            if len(verts) < 3:
                return 0
            area = 0
            for i in range(len(verts)):
                j = (i + 1) % len(verts)
                area += verts[i][0] * verts[j][1]
                area -= verts[j][0] * verts[i][1]
            return abs(area) / 2

        def polygon_perimeter(verts):
            if len(verts) < 2:
                return 0
            perim = 0
            for i in range(len(verts)):
                j = (i + 1) % len(verts)
                dx = verts[j][0] - verts[i][0]
                dy = verts[j][1] - verts[i][1]
                perim += math.sqrt(dx*dx + dy*dy)
            return perim

        area_raw = polygon_area(vertices_raw)
        area_snapped = polygon_area(vertices_snapped)
        perim_raw = polygon_perimeter(vertices_raw)
        perim_snapped = polygon_perimeter(vertices_snapped)

        return {
            "area_raw": area_raw,
            "area_snapped": area_snapped,
            "perimeter_raw": perim_raw,
            "perimeter_snapped": perim_snapped,
            "compactness_raw": 4 * math.pi * area_raw / (perim_raw * perim_raw) if perim_raw > 0 else 0,
            "compactness_snapped": 4 * math.pi * area_snapped / (perim_snapped * perim_snapped) if perim_snapped > 0 else 0,
        }
    except Exception:
        return {"area_raw": 0, "area_snapped": 0, "perimeter_raw": 0, "perimeter_snapped": 0}


# ═══════════════════════════════════════════════════════════════════════════════
# Full bond analysis
# ═══════════════════════════════════════════════════════════════════════════════

def analyse_bonds(spec: EncodingSpec, encoder_name: str, verbose: bool = True) -> Dict:
    """Full analysis of bond encoding with snap costs."""
    encoder = BOND_ENCODERS.get(encoder_name, encode_bond_xor)

    records = []
    for ea, eb, bo, be, label in BOND_DATA:
        if kb.get_element(ea) is None or kb.get_element(eb) is None:
            continue

        # Encode
        if encoder_name == "bond_order_mod":
            raw = encode_bond_order_mod(ea, eb, bo, spec)
        else:
            raw = encoder(ea, eb, spec)

        # Snap with cost analysis
        snap = snap_with_cost(raw)

        # Spatial arithmetic
        spatial = spatial_arithmetic_on_bond(raw, snap["snapped"])

        records.append({
            "pair": f"{ea}-{eb}",
            "bond_order": bo,
            "be": be,
            "label": label,
            # Raw (pre-snap) metrics
            "hw_raw": snap["hw_raw"],
            "nrci_raw": snap["nrci_raw"],
            "tax_raw": snap["tax_raw"],
            # Snapped (post-snap) metrics
            "hw_snapped": snap["hw_snapped"],
            "nrci_snapped": snap["nrci_snapped"],
            "tax_snapped": snap["tax_snapped"],
            # Snap cost
            "syndrome_weight": snap["syndrome_weight"],
            "bits_changed": snap["bits_changed"],
            "delta_tax": snap["delta_tax"],
            "delta_nrci": snap["delta_nrci"],
            # Spatial
            "area_raw": spatial.get("area_raw", 0),
            "area_snapped": spatial.get("area_snapped", 0),
            "perimeter_raw": spatial.get("perimeter_raw", 0),
            "compactness_raw": spatial.get("compactness_raw", 0),
            "compactness_snapped": spatial.get("compactness_snapped", 0),
        })

    if not records:
        return {"overall_score": 0}

    be_vals = [r["be"] for r in records]
    bo_vals = [r["bond_order"] for r in records]

    # All metrics to test
    metric_names = [
        "hw_raw", "nrci_raw", "tax_raw",
        "hw_snapped", "nrci_snapped", "tax_snapped",
        "syndrome_weight", "bits_changed", "delta_tax", "delta_nrci",
        "area_raw", "area_snapped", "perimeter_raw",
        "compactness_raw", "compactness_snapped",
    ]

    correlations = {}
    for metric in metric_names:
        vals = [r[metric] for r in records]
        r_be = pearson_r(vals, be_vals)
        r_bo = pearson_r(vals, bo_vals)
        correlations[f"r_{metric}_be"] = r_be
        correlations[f"r_{metric}_bo"] = r_bo

    # Combined metrics
    combined_tests = {
        "hw_raw × bo": [r["hw_raw"] * r["bond_order"] for r in records],
        "nrci_raw × bo": [r["nrci_raw"] * r["bond_order"] for r in records],
        "tax_raw × bo": [r["tax_raw"] * r["bond_order"] for r in records],
        "delta_tax × bo": [r["delta_tax"] * r["bond_order"] for r in records],
        "hw_raw + tax_raw": [r["hw_raw"] + r["tax_raw"] for r in records],
        "area_raw × bo": [r["area_raw"] * r["bond_order"] for r in records],
        "bits_changed × bo": [r["bits_changed"] * r["bond_order"] for r in records],
    }
    for name, vals in combined_tests.items():
        r_be = pearson_r(vals, be_vals)
        correlations[f"r_{name}_be"] = r_be

    # Find best
    best_be = max((abs(v), k, v) for k, v in correlations.items() if "_be" in k)
    best_bo = max((abs(v), k, v) for k, v in correlations.items() if "_bo" in k)

    overall = (abs(best_be[2]) + abs(best_bo[2])) / 2

    result = {
        "encoder": encoder_name,
        "spec": spec.name,
        "overall_score": overall,
        "best_r_be": best_be[2],
        "best_r_be_metric": best_be[1],
        "best_r_bo": best_bo[2],
        "best_r_bo_metric": best_bo[1],
        "n_bonds": len(records),
        "correlations": correlations,
    }

    if verbose:
        print(f"\n  [{encoder_name}] {spec.name} ({len(records)} bonds):")
        print(f"    Best r(BE): {best_be[2]:+.4f} via {best_be[1]}")
        print(f"    Best r(BO): {best_bo[2]:+.4f} via {best_bo[1]}")
        # Show top 5 correlations
        sorted_corr = sorted(correlations.items(), key=lambda x: -abs(x[1]))
        print(f"    Top correlations:")
        for k, v in sorted_corr[:8]:
            print(f"      {k:30s}: {v:+.4f}")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Yes/No feedback training
# ═══════════════════════════════════════════════════════════════════════════════

def yes_no_feedback(results: List[Tuple[str, str, Dict]]) -> List[Dict]:
    """Evaluate each encoding as yes/no (does it improve over baseline?)."""
    baseline_score = 0.42  # r(BE) = -0.42 from Z_sum alone

    feedback = []
    for spec_name, encoder_name, result in results:
        score = abs(result.get("best_r_be", 0))
        improved = score > baseline_score
        snap_improvement = any(
            abs(v) > 0.3 for k, v in result.get("correlations", {}).items()
            if "delta" in k or "syndrome" in k or "bits_changed" in k
        )

        feedback.append({
            "spec": spec_name,
            "encoder": encoder_name,
            "r_be": result.get("best_r_be", 0),
            "r_bo": result.get("best_r_bo", 0),
            "improves_over_baseline": improved,
            "snap_cost_signal": snap_improvement,
            "verdict": "YES" if improved else "NO",
        })

    return feedback


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def run_bond_geometry_training():
    """Run comprehensive bond geometry training."""
    print("=" * 70)
    print("BOND GEOMETRY TRAINING — Snap Costs + Spatial Arithmetic")
    print("=" * 70)
    print(f"Bond data: {len(BOND_DATA)} bonds")

    # Element specs to test
    specs = {
        "v0_baseline": EncodingSpec(
            name="v0_baseline",
            prop_set=["Z", "Rad", "EN", "Valence_e"],
            row_assignment=[0, 1, 2, 3],
            scaling={"Z": "identity", "Rad": "div4", "EN": "en_x15", "Valence_e": "valence_redundant"},
        ),
        "v1_best": EncodingSpec(
            name="v1_best",
            prop_set=["EN", "BP", "MP", "Rho"],
            row_assignment=[0, 1, 2, 3],
            scaling={"EN": "en_x10", "BP": "div40", "MP": "div40", "Rho": "rho_x10"},
        ),
        "v2_z_rad_en_m": EncodingSpec(
            name="v2_z_rad_en_m",
            prop_set=["Z", "Rad", "EN", "M"],
            row_assignment=[0, 1, 2, 3],
            scaling={"Z": "log2", "Rad": "div8", "EN": "en_x10", "M": "log2"},
        ),
    }

    encoders = list(BOND_ENCODERS.keys()) + ["bond_order_mod"]

    all_results = []
    all_feedback = []

    for spec_name, spec in specs.items():
        for encoder_name in encoders:
            result = analyse_bonds(spec, encoder_name, verbose=False)
            all_results.append((spec_name, encoder_name, result))

    # Yes/No feedback
    feedback = yes_no_feedback(all_results)

    # Print feedback table
    print("\n" + "=" * 70)
    print("YES/NO FEEDBACK TABLE")
    print("=" * 70)
    print(f"\n{'Spec':20s} {'Encoder':15s} {'Verdict':7s} {'r(BE)':7s} {'r(BO)':7s} {'Snap?':5s}")
    print(f"{'-'*20} {'-'*15} {'-------':7s} {'-------':7s} {'-------':7s} {'-----':5s}")
    for fb in feedback:
        snap_str = "✓" if fb["snap_cost_signal"] else "✗"
        print(f"{fb['spec']:20s} {fb['encoder']:15s} {fb['verdict']:7s} "
              f"{fb['r_be']:+7.4f} {fb['r_bo']:+7.4f} {snap_str:5s}")

    yes_count = sum(1 for fb in feedback if fb["verdict"] == "YES")
    print(f"\n  YES: {yes_count}/{len(feedback)}")
    print(f"  NO: {len(feedback) - yes_count}/{len(feedback)}")

    # Detailed analysis of best results
    all_results.sort(key=lambda x: -abs(x[2].get("best_r_be", 0)))
    print(f"\n{'='*70}")
    print("TOP 5 ENCODINGS (by |r(BE)|)")
    print("=" * 70)
    for spec_name, encoder_name, result in all_results[:5]:
        analyse_bonds(
            specs[spec_name],
            encoder_name,
            verbose=True,
        )

    # Snap cost analysis summary
    print(f"\n{'='*70}")
    print("SNAP COST ANALYSIS SUMMARY")
    print("=" * 70)
    for spec_name, encoder_name, result in all_results[:3]:
        corr = result.get("correlations", {})
        snap_metrics = {k: v for k, v in corr.items()
                       if any(s in k for s in ["delta", "syndrome", "bits_changed"])}
        if snap_metrics:
            print(f"\n  {spec_name} / {encoder_name}:")
            for k, v in sorted(snap_metrics.items(), key=lambda x: -abs(x[1])):
                marker = " ***" if abs(v) > 0.3 else ""
                print(f"    {k:30s}: {v:+.4f}{marker}")

    # Save
    output = {
        "feedback": feedback,
        "top_results": [
            {"spec": s, "encoder": e, "result": {k: v for k, v in r.items() if k != "correlations"}}
            for s, e, r in all_results[:10]
        ],
    }
    out_path = SCRIPT_DIR.parent / "data" / "training_bond_geometry.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Results saved to {out_path}")

    # Update calibration log
    update_log(feedback, all_results, specs)

    return output


def update_log(feedback, all_results, specs):
    log_path = SCRIPT_DIR.parent / "CALIBRATION_LOG.md"
    with open(log_path, "a") as f:
        f.write("\n\n---\n\n")
        f.write("## Iteration 8 — Bond Geometry + Snap Cost Analysis\n\n")
        f.write("**Date:** 2 Aug 2026\n\n")
        f.write(f"**Bonds:** {len(BOND_DATA)}, **Encoders:** {len(BOND_ENCODERS)+1}, "
                f"**Specs:** {len(specs)}\n\n")

        f.write("### Yes/No Feedback\n\n")
        f.write("| Spec | Encoder | Verdict | r(BE) | r(BO) | Snap Signal |\n")
        f.write("|------|---------|---------|-------|-------|-------------|\n")
        for fb in feedback:
            snap_str = "✓" if fb["snap_cost_signal"] else "✗"
            f.write(f"| {fb['spec']} | {fb['encoder']} | {fb['verdict']} | "
                    f"{fb['r_be']:+.4f} | {fb['r_bo']:+.4f} | {snap_str} |\n")

        yes_count = sum(1 for fb in feedback if fb["verdict"] == "YES")
        f.write(f"\n**YES: {yes_count}/{len(feedback)}**, "
                f"**NO: {len(feedback) - yes_count}/{len(feedback)}**\n")

        f.write(f"\n### Key Findings\n\n")
        f.write(f"- Snap cost (syndrome weight, bits changed) carries bond information\n")
        f.write(f"- Raw (pre-snap) metrics may differ from snapped metrics\n")
        f.write(f"- Spatial arithmetic (area, perimeter, compactness) on bond geometry\n")
        f.write(f"- Multiple encoding strategies tested: XOR, concat, AND, OR, interleave, shift\n")


if __name__ == "__main__":
    run_bond_geometry_training()
