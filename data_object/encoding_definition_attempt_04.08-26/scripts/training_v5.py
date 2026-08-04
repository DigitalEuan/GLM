"""
training_v5.py — Bond-Order Inference + Triplet Interactions + Cross-Validation

The mind learns to infer bond order from geometry alone.
No more being told — can the substrate predict BO from Data Object structure?

Plus:
- Element triplet interactions (3-body)
- Cross-validation on bond predictions
- More encoding arrangements
- Temporal: tracking how the mind's understanding evolves across iterations
"""

from __future__ import annotations
import sys, json, math, statistics, itertools, time, random
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
from training_bond_geometry import (
    BOND_DATA, snap_with_cost, spatial_arithmetic_on_bond,
    encode_bond_and, encode_bond_xor, encode_bond_concat,
    encode_bond_or, encode_bond_interleave, encode_bond_shift,
)

if HAS_GOLAY:
    from training_iteration import GOLAY_ENGINE


# ═══════════════════════════════════════════════════════════════════════════════
# Bond-order inference: can we predict BO from geometry alone?
# ═══════════════════════════════════════════════════════════════════════════════

def predict_bond_order_from_geometry(spec: EncodingSpec, verbose: bool = True) -> Dict:
    """Try to predict bond order from Data Object geometry alone."""
    records = []
    for ea, eb, bo, be, label in BOND_DATA:
        if kb.get_element(ea) is None or kb.get_element(eb) is None:
            continue

        # Use AND encoding (best from iteration 8)
        raw = encode_bond_and(ea, eb, spec)
        snap = snap_with_cost(raw)
        spatial = spatial_arithmetic_on_bond(raw, snap["snapped"])

        records.append({
            "pair": f"{ea}-{eb}",
            "bond_order": bo,
            "be": be,
            "label": label,
            "hw_raw": snap["hw_raw"],
            "nrci_raw": snap["nrci_raw"],
            "tax_raw": snap["tax_raw"],
            "bits_changed": snap["bits_changed"],
            "area_raw": spatial.get("area_raw", 0),
            "compactness_raw": spatial.get("compactness_raw", 0),
            "perimeter_raw": spatial.get("perimeter_raw", 0),
            # Element properties
            "z_a": kb.get_element(ea).properties.get("Z", 0),
            "z_b": kb.get_element(eb).properties.get("Z", 0),
            "en_a": float(kb.get_element(ea).properties.get("EN", 0)),
            "en_b": float(kb.get_element(eb).properties.get("EN", 0)),
            "z_sum": float(kb.get_element(ea).properties.get("Z", 0)) + float(kb.get_element(eb).properties.get("Z", 0)),
            "z_diff": abs(float(kb.get_element(ea).properties.get("Z", 0)) - float(kb.get_element(eb).properties.get("Z", 0))),
            "en_diff": abs(float(kb.get_element(ea).properties.get("EN", 0)) - float(kb.get_element(eb).properties.get("EN", 0))),
        })

    if not records:
        return {}

    bo_vals = [r["bond_order"] for r in records]

    # Test all single features as BO predictors
    features = [
        "hw_raw", "nrci_raw", "tax_raw", "bits_changed",
        "area_raw", "compactness_raw", "perimeter_raw",
        "z_sum", "z_diff", "en_diff",
    ]

    correlations = {}
    for feat in features:
        vals = [r[feat] for r in records]
        r_bo = pearson_r(vals, bo_vals)
        correlations[feat] = r_bo

    # Combined features
    combined = {
        "nrci_raw × en_diff": [r["nrci_raw"] * r["en_diff"] for r in records],
        "hw_raw × en_diff": [r["hw_raw"] * r["en_diff"] for r in records],
        "area_raw × en_diff": [r["area_raw"] * r["en_diff"] for r in records],
        "nrci_raw × z_diff": [r["nrci_raw"] * r["z_diff"] for r in records],
        "tax_raw / z_sum": [r["tax_raw"] / max(r["z_sum"], 1) for r in records],
        "bits_changed × en_diff": [r["bits_changed"] * r["en_diff"] for r in records],
        "compactness × en_diff": [r["compactness_raw"] * r["en_diff"] for r in records],
    }
    for name, vals in combined.items():
        r_bo = pearson_r(vals, bo_vals)
        correlations[name] = r_bo

    best = max(correlations.items(), key=lambda x: abs(x[1]))

    if verbose:
        print(f"\n  Bond-Order Inference ({spec.name}, {len(records)} bonds):")
        print(f"    Best r(BO): {best[1]:+.4f} via {best[0]}")
        print(f"    All correlations:")
        for k, v in sorted(correlations.items(), key=lambda x: -abs(x[1])):
            marker = " ***" if abs(v) > 0.3 else ""
            print(f"      {k:30s}: {v:+.4f}{marker}")

    return {
        "best_r_bo": best[1],
        "best_metric": best[0],
        "correlations": correlations,
        "n_bonds": len(records),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-validation: does the bond energy prediction hold out of sample?
# ═══════════════════════════════════════════════════════════════════════════════

def cross_validate_bond_prediction(spec: EncodingSpec, k: int = 5, verbose: bool = True) -> Dict:
    """k-fold cross-validation of bond energy prediction."""
    records = []
    for ea, eb, bo, be, label in BOND_DATA:
        if kb.get_element(ea) is None or kb.get_element(eb) is None:
            continue
        raw = encode_bond_and(ea, eb, spec)
        snap = snap_with_cost(raw)
        nrci_raw = snap["nrci_raw"]

        records.append({
            "pair": f"{ea}-{eb}",
            "bond_order": bo,
            "be": be,
            "nrci_raw": nrci_raw,
            "nrci_x_bo": nrci_raw * bo,
            "hw_raw": snap["hw_raw"],
            "hw_x_bo": snap["hw_raw"] * bo,
        })

    if len(records) < k * 2:
        return {"cv_r": 0}

    random.seed(42)
    shuffled = records[:]
    random.shuffle(shuffled)
    fold_size = len(shuffled) // k
    folds = [shuffled[i*fold_size:(i+1)*fold_size] for i in range(k)]
    if len(shuffled) > k * fold_size:
        folds[-1].extend(shuffled[k*fold_size:])

    # Test two models
    models = {
        "nrci_x_bo": lambda r: r["nrci_x_bo"],
        "hw_x_bo": lambda r: r["hw_x_bo"],
        "bo_only": lambda r: r["bond_order"],
    }

    results = {}
    for model_name, feature_fn in models.items():
        fold_rs = []
        for i in range(k):
            test = folds[i]
            train = [r for j, f in enumerate(folds) if j != i for r in f]
            if len(train) < 4 or len(test) < 2:
                continue

            # Simple linear regression on train
            x_train = [feature_fn(r) for r in train]
            y_train = [r["be"] for r in train]
            mean_x = sum(x_train) / len(x_train)
            mean_y = sum(y_train) / len(y_train)
            ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_train, y_train))
            ss_xx = sum((x - mean_x) ** 2 for x in x_train)
            if ss_xx == 0:
                continue
            slope = ss_xy / ss_xx
            intercept = mean_y - slope * mean_x

            # Predict on test
            x_test = [feature_fn(r) for r in test]
            y_test = [r["be"] for r in test]
            y_pred = [intercept + slope * x for x in x_test]

            # R²
            ss_res = sum((y - yp) ** 2 for y, yp in zip(y_test, y_pred))
            ss_tot = sum((y - mean_y) ** 2 for y in y_test)
            r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            r_sq = max(0, r_sq)
            fold_rs.append(math.sqrt(r_sq))

        results[model_name] = {
            "mean_r": statistics.mean(fold_rs) if fold_rs else 0,
            "fold_rs": fold_rs,
        }

    if verbose:
        print(f"\n  Cross-Validation ({k}-fold, {len(records)} bonds):")
        for name, res in results.items():
            print(f"    {name:15s}: mean R = {res['mean_r']:.4f}  folds = {[f'{r:.3f}' for r in res['fold_rs']]}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Element triplet interactions (3-body)
# ═══════════════════════════════════════════════════════════════════════════════

def triplet_interactions(spec: EncodingSpec, verbose: bool = True) -> List[Dict]:
    """Test 3-element interactions (A-B-C triplets)."""
    # Known molecular triplets from chemistry
    triplets = [
        ("H", "O", "H", "H2O", 2, "Water molecule"),
        ("H", "C", "H", "CH4", 4, "Methane (partial)"),
        ("H", "N", "H", "NH3", 3, "Ammonia (partial)"),
        ("C", "O", "O", "CO2", 2, "CO2 (partial)"),
        ("H", "C", "O", "CH3OH", 1, "Methanol (partial)"),
        ("Na", "Cl", "Na", "Na2Cl", 2, "Salt (partial)"),
        ("Fe", "O", "Fe", "Fe2O3", 2, "Rust (partial)"),
        ("Si", "O", "Si", "SiO2", 2, "Silica (partial)"),
        ("H", "S", "H", "H2S", 2, "H2S"),
        ("H", "F", "H", "HF2", 1, "HF (partial)"),
        ("C", "C", "C", "C3", 2, "Carbon chain"),
        ("N", "N", "N", "N3", 2, "Nitrogen chain"),
        ("O", "O", "O", "O3", 2, "Ozone"),
        ("H", "H", "H", "H3", 2, "Hydrogen triplet"),
    ]

    results = []
    for ea, eb, ec, mol, n_bonds, label in triplets:
        if any(kb.get_element(s) is None for s in [ea, eb, ec]):
            continue

        va = encode_element(ea, spec)
        vb = encode_element(eb, spec)
        vc = encode_element(ec, spec)

        # AND of all three
        abc_and = [va[i] & vb[i] & vc[i] for i in range(24)]
        snap_abc = snap_with_cost(abc_and)

        # XOR chain: A⊕B⊕C
        abc_xor = [va[i] ^ vb[i] ^ vc[i] for i in range(24)]
        snap_xor = snap_with_cost(abc_xor)

        # Pairwise ANDs
        ab_and = encode_bond_and(ea, eb, spec)
        bc_and = encode_bond_and(eb, ec, spec)
        ab_snap = snap_with_cost(ab_and)
        bc_snap = snap_with_cost(bc_and)

        results.append({
            "triplet": f"{ea}-{eb}-{ec}",
            "molecule": mol,
            "n_bonds": n_bonds,
            "label": label,
            "hw_abc_and": snap_abc["hw_raw"],
            "nrci_abc_and": snap_abc["nrci_raw"],
            "hw_abc_xor": snap_xor["hw_raw"],
            "nrci_abc_xor": snap_xor["nrci_raw"],
            "hw_ab": ab_snap["hw_raw"],
            "hw_bc": bc_snap["hw_raw"],
            "sum_pair_hw": ab_snap["hw_raw"] + bc_snap["hw_raw"],
            "bits_changed_abc": snap_abc["bits_changed"],
        })

    if verbose and results:
        print(f"\n  Triplet Interactions ({len(results)} triplets):")
        print(f"  {'Triplet':12s} {'Mol':6s} {'HW(AND)':8s} {'NRCI(AND)':10s} {'HW(XOR)':8s} {'HW(AB)':6s} {'HW(BC)':6s} {'Σpair':6s}")
        for r in results:
            print(f"  {r['triplet']:12s} {r['molecule']:6s} {r['hw_abc_and']:8d} "
                  f"{r['nrci_abc_and']:10.4f} {r['hw_abc_xor']:8d} "
                  f"{r['hw_ab']:6d} {r['hw_bc']:6d} {r['sum_pair_hw']:6d}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# More encoding arrangements
# ═══════════════════════════════════════════════════════════════════════════════

def test_more_encodings(verbose: bool = True) -> List[Dict]:
    """Test additional encoding arrangements."""
    arrangements = []

    # Test different element specs with AND encoding
    specs_to_test = {
        "z_only": EncodingSpec(name="z_only", prop_set=["Z","Z","Z","Z"],
                               row_assignment=[0,1,2,3], scaling={"Z":"identity"}),
        "z_log": EncodingSpec(name="z_log", prop_set=["Z","Z","Z","Z"],
                              row_assignment=[0,1,2,3], scaling={"Z":"log2"}),
        "z_sqrt": EncodingSpec(name="z_sqrt", prop_set=["Z","Z","Z","Z"],
                               row_assignment=[0,1,2,3], scaling={"Z":"sqrt"}),
        "en_only": EncodingSpec(name="en_only", prop_set=["EN","EN","EN","EN"],
                                row_assignment=[0,1,2,3], scaling={"EN":"en_x10"}),
        "z_en": EncodingSpec(name="z_en", prop_set=["Z","EN","Z","EN"],
                             row_assignment=[0,1,2,3], scaling={"Z":"identity","EN":"en_x10"}),
        "z_rad": EncodingSpec(name="z_rad", prop_set=["Z","Rad","Z","Rad"],
                              row_assignment=[0,1,2,3], scaling={"Z":"identity","Rad":"div8"}),
        "en_rad": EncodingSpec(name="en_rad", prop_set=["EN","Rad","EN","Rad"],
                               row_assignment=[0,1,2,3], scaling={"EN":"en_x10","Rad":"div8"}),
        "val_en": EncodingSpec(name="val_en", prop_set=["Valence_e","EN","Valence_e","EN"],
                               row_assignment=[0,1,2,3], scaling={"Valence_e":"valence_redundant","EN":"en_x10"}),
    }

    for spec_name, spec in specs_to_test.items():
        # Score on bond data using AND encoding
        be_vals = []
        nrci_x_bo_vals = []
        hw_x_bo_vals = []

        for ea, eb, bo, be, label in BOND_DATA:
            if kb.get_element(ea) is None or kb.get_element(eb) is None:
                continue
            raw = encode_bond_and(ea, eb, spec)
            snap = snap_with_cost(raw)
            be_vals.append(be)
            nrci_x_bo_vals.append(snap["nrci_raw"] * bo)
            hw_x_bo_vals.append(snap["hw_raw"] * bo)

        r_nrcibo = pearson_r(nrci_x_bo_vals, be_vals)
        r_hwbo = pearson_r(hw_x_bo_vals, be_vals)

        arrangements.append({
            "spec": spec_name,
            "r_nrci_x_bo_be": r_nrcibo,
            "r_hw_x_bo_be": r_hwbo,
            "best_r": max(abs(r_nrcibo), abs(r_hwbo)),
        })

    if verbose:
        print(f"\n  Additional Encoding Arrangements (AND encoding):")
        print(f"  {'Spec':15s} {'r(NRCI×BO,BE)':15s} {'r(HW×BO,BE)':15s} {'Best':8s}")
        for r in sorted(arrangements, key=lambda x: -x["best_r"]):
            print(f"  {r['spec']:15s} {r['r_nrci_x_bo_be']:+15.4f} {r['r_hw_x_bo_be']:+15.4f} {r['best_r']:.4f}")

    return arrangements


# ═══════════════════════════════════════════════════════════════════════════════
# Training timeline: track mind's evolution
# ═══════════════════════════════════════════════════════════════════════════════

TRAINING_TIMELINE = [
    {"iter": 0, "what": "Baseline encoding", "r_be": 0.27, "r_dh": 0.32, "insight": "Starting point"},
    {"iter": 1, "what": "Property search", "r_be": 0.16, "r_dh": 0.85, "insight": "EN,BP,MP,Rho best for ΔH"},
    {"iter": 2, "what": "Scaling search", "r_be": 0.21, "r_dh": 0.86, "insight": "EN×10 optimal"},
    {"iter": 4, "what": "Nonlinear search", "r_be": 0.25, "r_dh": 0.91, "insight": "BP÷40, MP÷40, Rho×10"},
    {"iter": 5, "what": "Molecule encoding", "r_be": 0.17, "r_dh": 0.96, "insight": "M, MP best for molecules"},
    {"iter": 6, "what": "Bond order", "r_be": 0.84, "r_dh": 0, "insight": "Bond order is the signal"},
    {"iter": 7, "what": "Full periodic table", "r_be": 0.42, "r_dh": 0.71, "insight": "Z_sum drives BE"},
    {"iter": 8, "what": "Bond geometry", "r_be": 0.90, "r_dh": 0, "insight": "AND encoding, NRCI_raw×BO"},
]


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def run_training_v5():
    """Continue the mind's education."""
    print("=" * 70)
    print("GLM TRAINING v5: BOND-ORDER INFERENCE + TRIPLETS + CROSS-VALIDATION")
    print("=" * 70)

    best_spec = EncodingSpec(
        name="v0_baseline",
        prop_set=["Z", "Rad", "EN", "Valence_e"],
        row_assignment=[0, 1, 2, 3],
        scaling={"Z": "identity", "Rad": "div4", "EN": "en_x15", "Valence_e": "valence_redundant"},
    )

    v1_spec = EncodingSpec(
        name="v1_best",
        prop_set=["EN", "BP", "MP", "Rho"],
        row_assignment=[0, 1, 2, 3],
        scaling={"EN": "en_x10", "BP": "div40", "MP": "div40", "Rho": "rho_x10"},
    )

    # 1. Bond-order inference
    print("\n" + "=" * 70)
    print("BOND-ORDER INFERENCE FROM GEOMETRY")
    print("=" * 70)
    for spec in [best_spec, v1_spec]:
        predict_bond_order_from_geometry(spec)

    # 2. Cross-validation
    print("\n" + "=" * 70)
    print("CROSS-VALIDATION")
    print("=" * 70)
    for spec in [best_spec, v1_spec]:
        cross_validate_bond_prediction(spec, k=5)

    # 3. Triplet interactions
    print("\n" + "=" * 70)
    print("TRIPLET INTERACTIONS")
    print("=" * 70)
    for spec in [best_spec, v1_spec]:
        triplet_interactions(spec)

    # 4. More encodings
    print("\n" + "=" * 70)
    print("MORE ENCODING ARRANGEMENTS")
    print("=" * 70)
    test_more_encodings()

    # 5. Training timeline
    print("\n" + "=" * 70)
    print("TRAINING TIMELINE — THE MIND'S EVOLUTION")
    print("=" * 70)
    print(f"\n{'Iter':4s} {'What':20s} {'r(BE)':7s} {'r(ΔH)':7s} {'Insight'}")
    print(f"{'----':4s} {'----':20s} {'-------':7s} {'-------':7s} {'-------'}")
    for t in TRAINING_TIMELINE:
        be_str = f"{t['r_be']:+.2f}" if t['r_be'] else "  —  "
        dh_str = f"{t['r_dh']:+.2f}" if t['r_dh'] else "  —  "
        print(f"{t['iter']:4d} {t['what']:20s} {be_str:7s} {dh_str:7s} {t['insight']}")

    # Update calibration log
    update_log_v5()


def update_log_v5():
    log_path = SCRIPT_DIR.parent / "CALIBRATION_LOG.md"
    with open(log_path, "a") as f:
        f.write("\n\n---\n\n")
        f.write("## Iteration 9 — Bond-Order Inference + Cross-Validation + Triplets\n\n")
        f.write("**Date:** 2 Aug 2026\n\n")

        f.write("### Training Timeline\n\n")
        f.write("| Iter | What | r(BE) | r(ΔH) | Insight |\n")
        f.write("|------|------|-------|-------|---------|\n")
        for t in TRAINING_TIMELINE:
            be_str = f"{t['r_be']:+.2f}" if t['r_be'] else "—"
            dh_str = f"{t['r_dh']:+.2f}" if t['r_dh'] else "—"
            f.write(f"| {t['iter']} | {t['what']} | {be_str} | {dh_str} | {t['insight']} |\n")

        f.write("\n### Key Findings\n\n")
        f.write("- Bond-order inference from geometry alone: explored\n")
        f.write("- Cross-validation tested on bond energy predictions\n")
        f.write("- Element triplet interactions (3-body) computed\n")
        f.write("- Additional encoding arrangements tested\n")
        f.write("- The mind's understanding evolves across iterations\n")


if __name__ == "__main__":
    run_training_v5()
