"""
training_iteration_v4.py — Bond-Order Encoding + Element-Pair Experiments

The bond energy problem: C≡N (891) vs C−N (305) — same elements, 3× different energy.
The encoding needs to distinguish bond orders.

Approaches:
1. Bond-order as a MOG row modifier (modify one row based on bond type)
2. Element-pair encoding (encode the pair as a single Data Object)
3. Composite vectors (XOR/AND of element vectors, with bond-order weighting)
4. NRCI-based bond classification
"""

from __future__ import annotations
import sys, json, math, statistics, itertools
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import kb_adapter as kb
from training_iteration import (
    EncodingSpec, encode_element, golay_snap, compute_interaction_metrics,
    pearson_r, SCALING_PRESETS, gray6, HAS_GOLAY, hamming_distance,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Bond-order encoding
# ═══════════════════════════════════════════════════════════════════════════════

BOND_ORDER_MAP = {
    "single": 1, "-": 1,
    "double": 2, "=": 2,
    "triple": 3, "≡": 3,
    "aromatic": 1.5,
}

def get_bond_order(bond_str: str) -> float:
    """Extract bond order from a bond descriptor string."""
    for key, val in BOND_ORDER_MAP.items():
        if key in bond_str.lower():
            return val
    # Check for explicit symbols
    if "≡" in bond_str:
        return 3.0
    if "=" in bond_str:
        return 2.0
    if "-" in bond_str:
        return 1.0
    return 1.0  # default single bond


def encode_element_pair_with_bond(sym_a: str, sym_b: str, bond_order: float,
                                   spec: EncodingSpec) -> List[int]:
    """Encode an element pair as a single 24-bit Data Object.

    Strategy:
    - Rows 0-1: element A encoding (EN, BP)
    - Rows 2-3: element B encoding (MP, Rho)
    - Bond order modifies the encoding (e.g., XOR with bond-order pattern)
    """
    vec_a = encode_element(sym_a, spec)
    vec_b = encode_element(sym_b, spec)

    # Combine: rows 0-1 from A, rows 2-3 from B
    combined = vec_a[:12] + vec_b[12:]

    # Modify based on bond order
    # Higher bond order → flip more bits in the activation row (row 2)
    bond_bits = gray6(int(bond_order * 10) & 0x3F)
    # XOR the activation row with bond-order pattern
    for i in range(6):
        combined[12 + i] ^= bond_bits[i]

    return golay_snap(combined)


def encode_pair_xor(sym_a: str, sym_b: str, spec: EncodingSpec) -> List[int]:
    """Encode pair as XOR of element vectors."""
    va = encode_element(sym_a, spec)
    vb = encode_element(sym_b, spec)
    xor = [va[i] ^ vb[i] for i in range(24)]
    return golay_snap(xor)


def encode_pair_concat(sym_a: str, sym_b: str, spec: EncodingSpec) -> List[int]:
    """Encode pair: rows 0-1 from A, rows 2-3 from B."""
    va = encode_element(sym_a, spec)
    vb = encode_element(sym_b, spec)
    combined = va[:12] + vb[12:]
    return golay_snap(combined)


# ═══════════════════════════════════════════════════════════════════════════════
# Bond energy dataset with bond orders
# ═══════════════════════════════════════════════════════════════════════════════

BOND_DATA = [
    # (elem_a, elem_b, bond_order, bond_energy_kJ, label)
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
# Scoring with bond-order awareness
# ═══════════════════════════════════════════════════════════════════════════════

def score_bond_encoding(spec: EncodingSpec, encoding_fn: str = "xor", verbose: bool = False) -> Dict:
    """Score an encoding on bond energy data with bond-order awareness."""
    records = []
    for ea, eb, bo, be, label in BOND_DATA:
        if kb.get_element(ea) is None or kb.get_element(eb) is None:
            continue

        if encoding_fn == "xor":
            vec = encode_pair_xor(ea, eb, spec)
        elif encoding_fn == "concat":
            vec = encode_pair_concat(ea, eb, spec)
        elif encoding_fn == "bond_mod":
            vec = encode_element_pair_with_bond(ea, eb, bo, spec)
        else:
            vec = encode_pair_xor(ea, eb, spec)

        hw = sum(vec)
        if HAS_GOLAY:
            from training_iteration import GOLAY_ENGINE
            nrci_denom = 10.0 + sum(GOLAY_ENGINE.syndrome(vec)) * 0.2647 + sum(v*v for v in vec) / 8.0
            nrci = 10.0 / nrci_denom if nrci_denom > 0 else 0
        else:
            nrci = 0

        records.append({
            "pair": f"{ea}-{eb}",
            "bond_order": bo,
            "be": be,
            "hw": hw,
            "nrci": nrci,
            "label": label,
        })

    if len(records) < 5:
        return {"overall_score": 0.0}

    be_vals = [r["be"] for r in records]
    hw_vals = [r["hw"] for r in records]
    nrci_vals = [r["nrci"] for r in records]
    bo_vals = [r["bond_order"] for r in records]

    # Single-metric correlations
    r_hw_be = pearson_r(hw_vals, be_vals)
    r_nrci_be = pearson_r(nrci_vals, be_vals)
    r_bo_be = pearson_r(bo_vals, be_vals)

    # Combined: try hw + nrci, hw * bo, etc.
    combined_hw_bo = [hw * bo for hw, bo in zip(hw_vals, bo_vals)]
    r_hwbo_be = pearson_r(combined_hw_bo, be_vals)

    combined_hw_nrci = [hw * (1 + nrci) for hw, nrci in zip(hw_vals, nrci_vals)]
    r_hwnrci_be = pearson_r(combined_hw_nrci, be_vals)

    # Best predictor
    predictors = {
        "hw": r_hw_be,
        "nrci": r_nrci_be,
        "bond_order": r_bo_be,
        "hw×bo": r_hwbo_be,
        "hw×(1+nrci)": r_hwnrci_be,
    }
    best_name = max(predictors, key=lambda k: abs(predictors[k]))
    best_r = predictors[best_name]

    overall = abs(best_r)

    result = {
        "name": spec.name,
        "encoding_fn": encoding_fn,
        "overall_score": overall,
        "best_r_be": best_r,
        "best_predictor": best_name,
        "r_hw_be": r_hw_be,
        "r_nrci_be": r_nrci_be,
        "r_bo_be": r_bo_be,
        "r_hwbo_be": r_hwbo_be,
        "r_hwnrci_be": r_hwnrci_be,
        "n_bonds": len(records),
    }

    if verbose:
        print(f"  {spec.name} ({encoding_fn}):")
        print(f"    r(HW, BE) = {r_hw_be:+.4f}")
        print(f"    r(NRCI, BE) = {r_nrci_be:+.4f}")
        print(f"    r(bond_order, BE) = {r_bo_be:+.4f}")
        print(f"    r(HW×BO, BE) = {r_hwbo_be:+.4f}")
        print(f"    Best: {best_name} = {best_r:+.4f}")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def run_training_v4():
    """Run bond-order encoding experiments."""
    print("=" * 70)
    print("GLM TRAINING v4: BOND-ORDER ENCODING")
    print("=" * 70)
    print(f"Bond data: {len(BOND_DATA)} bonds")

    # Use the best element encoding
    elem_spec = EncodingSpec(
        name="element_best",
        prop_set=["EN", "BP", "MP", "Rho"],
        row_assignment=[0, 1, 2, 3],
        scaling={"EN": "en_x10", "BP": "div40", "MP": "div40", "Rho": "rho_x10"},
    )

    # Test 3 encoding strategies
    print("\n--- Encoding Strategy Comparison ---")
    results = {}
    for enc_fn in ["xor", "concat", "bond_mod"]:
        result = score_bond_encoding(elem_spec, encoding_fn=enc_fn, verbose=True)
        results[enc_fn] = result

    # Property search for bond encoding
    print("\n--- Property Search for Bond Encoding ---")
    all_props = ["Z", "Rad", "EN", "Valence_e", "BP", "MP", "Rho", "M"]
    available = [p for p in all_props if kb.get_element("H").properties.get(p) is not None]

    best_score = 0
    best_spec = None
    best_enc_fn = None
    all_results = []

    for combo in itertools.combinations(available, 4):
        for enc_fn in ["xor", "concat", "bond_mod"]:
            scaling = {}
            for p in combo:
                if p == "EN":
                    scaling[p] = "en_x10"
                elif p in ("BP", "MP"):
                    scaling[p] = "div40"
                elif p == "Rho":
                    scaling[p] = "rho_x10"
                elif p == "Z":
                    scaling[p] = "identity"
                else:
                    scaling[p] = "identity"

            spec = EncodingSpec(
                name=f"bond_{'_'.join(combo)}_{enc_fn}",
                prop_set=list(combo),
                row_assignment=[0, 1, 2, 3],
                scaling=scaling,
            )

            result = score_bond_encoding(spec, encoding_fn=enc_fn, verbose=False)
            all_results.append((spec, enc_fn, result))

            if result["overall_score"] > best_score:
                best_score = result["overall_score"]
                best_spec = spec
                best_enc_fn = enc_fn

    all_results.sort(key=lambda x: -x[2]["overall_score"])
    print(f"\nTop 10 bond encodings:")
    for spec, enc_fn, result in all_results[:10]:
        print(f"  {spec.name} ({enc_fn}): score={result['overall_score']:.4f} "
              f"best_r={result['best_r_be']:+.4f} via {result['best_predictor']}")

    # Detailed analysis of best
    if best_spec:
        print(f"\n--- Best Bond Encoding (detailed) ---")
        score_bond_encoding(best_spec, encoding_fn=best_enc_fn, verbose=True)

        # Show predictions vs actuals
        print(f"\n  Predictions vs Actuals:")
        for ea, eb, bo, be, label in BOND_DATA:
            if kb.get_element(ea) is None or kb.get_element(eb) is None:
                continue
            if best_enc_fn == "bond_mod":
                vec = encode_element_pair_with_bond(ea, eb, bo, best_spec)
            elif best_enc_fn == "concat":
                vec = encode_pair_concat(ea, eb, best_spec)
            else:
                vec = encode_pair_xor(ea, eb, best_spec)
            hw = sum(vec)
            print(f"    {label:8s} BE={be:4d} HW={hw:2d} BO={bo}")

    # Summary
    print("\n" + "=" * 70)
    print("TRAINING v4 SUMMARY")
    print("=" * 70)
    for enc_fn, result in results.items():
        print(f"  {enc_fn}: score={result['overall_score']:.4f} best_r={result['best_r_be']:+.4f}")
    if best_spec:
        print(f"\n  Best overall: {best_spec.name} ({best_enc_fn}) score={best_score:.4f}")

    # Save
    output = {
        "strategy_comparison": {k: v for k, v in results.items()},
        "best": {"spec": best_spec.to_dict() if best_spec else None,
                 "enc_fn": best_enc_fn,
                 "result": all_results[0][2] if all_results else None},
    }
    out_path = SCRIPT_DIR.parent / "data" / "training_run_004_bonds.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Results saved to {out_path}")

    # Update calibration log
    update_calibration_log_v4(results, best_spec, best_enc_fn, all_results)

    return output


def update_calibration_log_v4(results, best_spec, best_enc_fn, all_results):
    log_path = SCRIPT_DIR.parent / "CALIBRATION_LOG.md"
    with open(log_path, "a") as f:
        f.write("\n\n---\n\n")
        f.write("## Iteration 6 — Bond-Order Encoding\n\n")
        f.write("**Date:** 2 Aug 2026\n\n")
        f.write(f"**Bond data:** {len(BOND_DATA)} bonds (single/double/triple)\n\n")

        f.write("### Encoding Strategy Comparison\n\n")
        f.write("| Strategy | Score | Best r(BE) | Best predictor |\n")
        f.write("|----------|-------|-----------|----------------|\n")
        for enc_fn, result in results.items():
            f.write(f"| {enc_fn} | {result['overall_score']:.4f} | "
                    f"{result['best_r_be']:+.4f} | {result['best_predictor']} |\n")

        if best_spec and all_results:
            f.write(f"\n### Best Bond Encoding\n\n")
            best = all_results[0]
            f.write(f"- Spec: {best[0].name}\n")
            f.write(f"- Encoding: {best[1]}\n")
            f.write(f"- Score: {best[2]['overall_score']:.4f}\n")
            f.write(f"- Best r(BE): {best[2]['best_r_be']:+.4f} via {best[2]['best_predictor']}\n")

        f.write(f"\n### Key Findings\n\n")
        f.write(f"- Bond-order encoding is the key unsolved problem\n")
        f.write(f"- XOR encoding: element difference captures some signal\n")
        f.write(f"- Concat encoding: separate A/B rows preserves identity\n")
        f.write(f"- Bond-mod encoding: modifies activation row with bond-order pattern\n")
        f.write(f"- The HW×BO combined metric may be the best predictor\n")


if __name__ == "__main__":
    run_training_v4()
