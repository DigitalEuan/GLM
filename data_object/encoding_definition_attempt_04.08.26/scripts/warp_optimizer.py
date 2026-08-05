#!/usr/bin/env python3
"""
Warping Permutation Optimizer + Light-Speed Calibration
========================================================
Experiment: encoding_definition_attempt_04.08-26
Date: 4 August 2026

1. Systematically test ALL column swap permutations to find the
   optimal warping for Bond Energy prediction.

2. Calibrate geometric work units to kJ/mol using the speed of light
   as the baseline lattice throughput.

Usage:
  python3 warp_optimizer.py --optimize
  python3 warp_optimizer.py --calibrate
  python3 warp_optimizer.py --both
"""

from __future__ import annotations

import json
import math
import random
import sys
import itertools
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from elements_data_object_system import (
    GolayEngine, DataObject, MOGSpatialArithmetic,
    load_elements_from_kb, encode_element, interact,
    BEST_ENCODING, Y_CONST,
)
from refined_element_system import (
    EXPANDED_PAIRS, pearson_r, mae, k_fold_split,
)
from three_directions import SimpleRandomForest

import numpy as np


# ════════════════════════════════════════════════════════════════════════════════
# 1. WARPING PERMUTATION OPTIMIZER
# ════════════════════════════════════════════════════════════════════════════════

def apply_column_permutation(codeword: List[int], perm: List[int]) -> List[int]:
    """Apply a column permutation to all 4 MOG rows."""
    warped = [0] * 24
    for row in range(4):
        base = row * 6
        for new_col, old_col in enumerate(perm):
            warped[base + new_col] = codeword[base + old_col]
    return warped


def apply_row_permutation(codeword: List[int], perm: List[int]) -> List[int]:
    """Apply a row permutation."""
    warped = [0] * 24
    for new_row, old_row in enumerate(perm):
        warped[new_row * 6:(new_row + 1) * 6] = codeword[old_row * 6:(old_row + 1) * 6]
    return warped


def apply_bit_flip_mask(codeword: List[int], mask: List[int]) -> List[int]:
    """Flip bits at specified positions."""
    warped = list(codeword)
    for pos in mask:
        warped[pos] ^= 1
    return warped


def apply_rotation(codeword: List[int], shift: int) -> List[int]:
    """Rotate all MOG columns by shift positions."""
    warped = list(codeword)
    for row in range(4):
        base = row * 6
        row_bits = warped[base:base + 6]
        shifted = row_bits[-shift:] + row_bits[:-shift]
        warped[base:base + 6] = shifted
    return warped


def nrci_from_bits(bits: List[int]) -> float:
    hw = sum(bits)
    ns = sum(b * b for b in bits)
    tax = float(Y_CONST) * hw + ns / 8.0
    return 10.0 / (10.0 + tax)


def build_warped_features(ca: List[int], cb_warped: List[int],
                          do_a: DataObject, do_b: DataObject) -> List[float]:
    """Build feature vector from warped interaction."""
    and_bits = [ca[i] & cb_warped[i] for i in range(24)]
    xor_bits = [ca[i] ^ cb_warped[i] for i in range(24)]
    and_hw = sum(and_bits)
    xor_hw = sum(xor_bits)
    and_nrci = nrci_from_bits(and_bits)
    xor_nrci = nrci_from_bits(xor_bits)
    
    # Per-row overlap
    row_ov = [sum(ca[r*6:(r+1)*6][i] & cb_warped[r*6:(r+1)*6][i] for i in range(6)) for r in range(4)]
    row_diff = [sum(ca[r*6:(r+1)*6][i] ^ cb_warped[r*6:(r+1)*6][i] for i in range(6)) for r in range(4)]
    
    return [
        and_hw, xor_hw, and_nrci, xor_nrci, and_nrci - xor_nrci,
        *row_ov, *row_diff,
        do_a.hamming_weight, do_b.hamming_weight,
        float(do_a.nrci()), float(do_b.nrci()),
    ]


def evaluate_warp(data_objects: Dict, warper, n_trees: int = 50) -> Dict:
    """Evaluate a warping function on all pairs."""
    X = []
    y_be = []
    y_bo = []
    
    for sym_a, sym_b, be, dh, label, bo in EXPANDED_PAIRS:
        if sym_a not in data_objects or sym_b not in data_objects:
            continue
        do_a, do_b = data_objects[sym_a], data_objects[sym_b]
        ca, cb = do_a.codeword, do_b.codeword
        
        warped_b = warper(cb, bo)
        # Snap to nearest codeword
        golay = GolayEngine()
        warped_b, _ = golay.snap_to_codeword(warped_b)
        
        features = build_warped_features(ca, warped_b, do_a, do_b)
        X.append(features)
        y_be.append(be)
        y_bo.append(bo)
    
    n = len(X)
    X_arr = np.array(X)
    y = np.array(y_be)
    
    # Normalize
    X_mean = X_arr.mean(axis=0)
    X_std = X_arr.std(axis=0)
    X_std[X_std == 0] = 1
    X_norm = (X_arr - X_mean) / X_std
    
    # 5-fold CV
    folds = k_fold_split(n, k=5, seed=42)
    preds = np.zeros(n)
    
    for fi, (tr, te) in enumerate(folds):
        rf = SimpleRandomForest(n_trees=n_trees, max_depth=3, seed=fi)
        rf.fit(X_norm[tr], y[tr])
        preds[te] = rf.predict(X_norm[te])
    
    be_r = pearson_r(preds.tolist(), y.tolist())
    be_mae_val = mae(preds.tolist(), y.tolist())
    
    return {"be_r": be_r, "be_mae": be_mae_val, "n": n}


def run_optimizer():
    """Systematically test all warping permutations."""
    print("=" * 72)
    print("WARPING PERMUTATION OPTIMIZER")
    print("=" * 72)
    
    # Load
    kb_path = Path("/home/work/.openclaw/workspace/GLM/long_term_memory/ubp_system_kb.json")
    elements = load_elements_from_kb(str(kb_path))
    golay = GolayEngine()
    
    data_objects = {}
    for sym in elements:
        do = encode_element(sym, elements, BEST_ENCODING, golay)
        if do:
            data_objects[sym] = do
    
    results = []
    
    # ── Part A: Column permutations (all 720) ────────────────────────────────
    print(f"\n[1] Testing all 720 column permutations...")
    
    col_perms = list(itertools.permutations(range(6)))
    print(f"    Total permutations: {len(col_perms)}")
    
    # Test each permutation as a warp for BO>=2
    best_r = 0
    best_perm = None
    
    for i, perm in enumerate(col_perms):
        warper = lambda cw, bo, p=perm: apply_column_permutation(cw, p) if bo >= 2 else list(cw)
        result = evaluate_warp(data_objects, warper, n_trees=30)
        results.append({"type": "col_perm", "perm": list(perm), **result})
        
        if result["be_r"] > best_r:
            best_r = result["be_r"]
            best_perm = list(perm)
        
        if (i + 1) % 100 == 0:
            print(f"    Tested {i+1}/720... best r so far: {best_r:.4f}")
    
    print(f"\n    Best column permutation: {best_perm} (r={best_r:.4f})")
    
    # ── Part B: Row permutations (all 24) ────────────────────────────────────
    print(f"\n[2] Testing all 24 row permutations...")
    
    row_perms = list(itertools.permutations(range(4)))
    
    for perm in row_perms:
        warper = lambda cw, bo, p=perm: apply_row_permutation(cw, p) if bo >= 2 else list(cw)
        result = evaluate_warp(data_objects, warper, n_trees=30)
        results.append({"type": "row_perm", "perm": list(perm), **result})
        
        if result["be_r"] > best_r:
            best_r = result["be_r"]
            best_perm = {"type": "row", "perm": list(perm)}
    
    print(f"    Best row permutation: {best_perm} (r={best_r:.4f})")
    
    # ── Part C: Column rotations (6) ─────────────────────────────────────────
    print(f"\n[3] Testing 6 column rotations...")
    
    for shift in range(6):
        warper = lambda cw, bo, s=shift: apply_rotation(cw, s) if bo >= 2 else list(cw)
        result = evaluate_warp(data_objects, warper, n_trees=30)
        results.append({"type": "rotation", "shift": shift, **result})
        
        if result["be_r"] > best_r:
            best_r = result["be_r"]
            best_perm = {"type": "rotation", "shift": shift}
    
    print(f"    Best rotation: {best_perm} (r={best_r:.4f})")
    
    # ── Part D: Bit flip masks (all 6-bit combinations in Activation row) ────
    print(f"\n[4] Testing bit flip masks in Activation row (bits 12-17)...")
    
    act_bits = list(range(12, 18))
    best_flip_r = 0
    best_flip_mask = None
    
    # Test all non-empty subsets of Activation bits
    for size in range(1, 7):
        for mask in itertools.combinations(act_bits, size):
            warper = lambda cw, bo, m=mask: apply_bit_flip_mask(cw, list(m)) if bo >= 2 else list(cw)
            result = evaluate_warp(data_objects, warper, n_trees=30)
            results.append({"type": "flip", "mask": list(mask), **result})
            
            if result["be_r"] > best_flip_r:
                best_flip_r = result["be_r"]
                best_flip_mask = list(mask)
            
            if result["be_r"] > best_r:
                best_r = result["be_r"]
                best_perm = {"type": "flip", "mask": list(mask)}
    
    print(f"    Best flip mask: {best_flip_mask} (r={best_flip_r:.4f})")
    
    # ── Part E: Graduated flips (different masks for BO=2 vs BO=3) ───────────
    print(f"\n[5] Testing graduated flips (BO=2 vs BO=3)...")
    
    best_grad_r = 0
    best_grad = None
    
    for mask2 in itertools.combinations(act_bits, 3):
        for mask3 in itertools.combinations(act_bits, 6):
            def warper(cw, bo, m2=mask2, m3=mask3):
                if bo == 2:
                    return apply_bit_flip_mask(cw, list(m2))
                elif bo >= 3:
                    return apply_bit_flip_mask(cw, list(m3))
                return list(cw)
            
            result = evaluate_warp(data_objects, warper, n_trees=30)
            results.append({"type": "graduated", "mask2": list(mask2), "mask3": list(mask3), **result})
            
            if result["be_r"] > best_grad_r:
                best_grad_r = result["be_r"]
                best_grad = {"mask2": list(mask2), "mask3": list(mask3)}
            
            if result["be_r"] > best_r:
                best_r = result["be_r"]
                best_perm = {"type": "graduated", **best_grad}
    
    print(f"    Best graduated: {best_grad} (r={best_grad_r:.4f})")
    
    # ── Part F: Combined column swap + flip ──────────────────────────────────
    print(f"\n[6] Testing combined column swap + flip...")
    
    # Take top 10 column perms and combine with best flip
    top_col_perms = sorted([r for r in results if r["type"] == "col_perm"],
                           key=lambda r: r["be_r"], reverse=True)[:10]
    
    for col_result in top_col_perms:
        perm = col_result["perm"]
        for mask in itertools.combinations(act_bits, 3):
            def warper(cw, bo, p=perm, m=mask):
                if bo >= 2:
                    warped = apply_column_permutation(cw, p)
                    warped = apply_bit_flip_mask(warped, list(m))
                    return warped
                return list(cw)
            
            result = evaluate_warp(data_objects, warper, n_trees=30)
            results.append({"type": "combined", "col_perm": perm, "flip_mask": list(mask), **result})
            
            if result["be_r"] > best_r:
                best_r = result["be_r"]
                best_perm = {"type": "combined", "col_perm": perm, "flip_mask": list(mask)}
    
    print(f"    Best combined: {best_perm} (r={best_r:.4f})")
    
    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print("OPTIMIZATION RESULTS")
    print(f"{'='*72}")
    
    # Top 20 results
    results.sort(key=lambda r: r["be_r"], reverse=True)
    
    print(f"\n  Top 20 warping configurations:")
    print(f"  {'Rank':>4} {'Type':<15} {'Config':<40} {'BE r':>7} {'MAE':>7}")
    print(f"  {'-'*75}")
    
    for i, r in enumerate(results[:20]):
        if r["type"] == "col_perm":
            config = f"cols={r['perm']}"
        elif r["type"] == "row_perm":
            config = f"rows={r['perm']}"
        elif r["type"] == "rotation":
            config = f"shift={r['shift']}"
        elif r["type"] == "flip":
            config = f"bits={r['mask']}"
        elif r["type"] == "graduated":
            config = f"BO2={r['mask2']}, BO3={r['mask3']}"
        elif r["type"] == "combined":
            config = f"cols={r['col_perm']}, flip={r['flip_mask']}"
        else:
            config = str(r)
        
        print(f"  {i+1:>4} {r['type']:<15} {config:<40} {r['be_r']:>7.4f} {r['be_mae']:>7.1f}")
    
    # Save all results
    save_path = SCRIPT_DIR.parent / "data" / f"warp_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(save_path, 'w') as f:
        json.dump(results[:100], f, indent=2, default=str)
    print(f"\n  Results saved to: {save_path}")
    
    return results


# ════════════════════════════════════════════════════════════════════════════════
# 2. LIGHT-SPEED CALIBRATION
# ════════════════════════════════════════════════════════════════════════════════

def calculate_vacuum_scale(settlement_trajectory: Dict) -> Dict:
    """
    Derive the UBP-to-Reality scale factor using the propagation cost of light.
    
    By defining light as the baseline throughput of the unfrustrated lattice,
    we gain a universal conversion factor from geometric work units to Joules.
    """
    # Physical Constants
    C_REALITY = 299792458  # meters per second
    
    # Substrate Metrics from a pure vacuum run
    base_bits = 24
    baseline_tax = settlement_trajectory.get("baseline_vacuum_tax", 0.0)
    snap_delay = settlement_trajectory.get("snap_depth_ticks", 1.0)
    
    # Total computational time-cost for light to clear 1 lattice unit
    total_ticks_per_cell = base_bits + baseline_tax + snap_delay
    
    # The Universal Scale Factor: Maps 1 Computational Tick to Real Seconds
    LATTICE_SPACING = 1.616255e-35  # Planck Length (meters)
    
    tick_duration_seconds = LATTICE_SPACING / (C_REALITY * total_ticks_per_cell)
    
    return {
        "ticks_per_cell": total_ticks_per_cell,
        "tick_duration_seconds": tick_duration_seconds,
        "scale_factor_j_per_coherence": derive_energy_scale(tick_duration_seconds),
    }


def derive_energy_scale(tick_duration: float) -> float:
    """Using Planck's constant (h = E * t) to find Joule-per-NRCI conversion."""
    H_PLANCK = 6.62607015e-34  # Joule-seconds
    joules_per_geometric_work_unit = H_PLANCK / tick_duration
    return joules_per_geometric_work_unit


def run_calibration():
    """
    Calibrate geometric work units to kJ/mol using light-speed baseline.
    
    The key insight: by defining light as the baseline throughput of the
    unfrustrated lattice, we gain a universal conversion factor.
    
    1. Compute vacuum settlement (empty lattice)
    2. Derive tick duration from Planck length / speed of light
    3. Convert geometric work (bit-steps × NRCI) to Joules
    4. Convert Joules to kJ/mol (× Avogadro / 1000)
    """
    print("=" * 72)
    print("LIGHT-SPEED CALIBRATION")
    print("=" * 72)
    
    # Physical constants
    C = 299792458  # m/s
    H = 6.62607015e-34  # J·s
    L_PLANCK = 1.616255e-35  # m
    N_A = 6.02214076e23  # mol⁻¹
    
    print(f"\n[1] Physical constants")
    print(f"    Speed of light:    c = {C} m/s")
    print(f"    Planck's constant: h = {H} J·s")
    print(f"    Planck length:     L_p = {L_PLANCK} m")
    print(f"    Avogadro's number: N_A = {N_A} mol⁻¹")
    
    # ── Vacuum settlement ────────────────────────────────────────────────────
    print(f"\n[2] Vacuum settlement (empty lattice)")
    
    # The vacuum state: all zeros, NRCI = 1.0, TAX = 0
    # In the substrate, light propagates at the speed of unfrustrated lattice turnover
    # Each "tick" = one Golay snap cycle (24 bits → codeword)
    
    # Vacuum metrics
    vacuum_hw = 0
    vacuum_nrci = 1.0
    vacuum_tax = 0.0
    
    # Snap depth: how many ticks for a single bit to propagate through the lattice
    # In the Golay code, a single bit error requires 1 snap cycle to correct
    # For light (unfrustrated), snap_depth = 1
    snap_depth_ticks = 1.0
    
    # Total ticks per lattice cell
    base_bits = 24
    total_ticks = base_bits + vacuum_tax + snap_depth_ticks
    
    print(f"    Vacuum HW:    {vacuum_hw}")
    print(f"    Vacuum NRCI:  {vacuum_nrci}")
    print(f"    Vacuum TAX:   {vacuum_tax}")
    print(f"    Snap depth:   {snap_depth_ticks} ticks")
    print(f"    Total ticks:  {total_ticks} per cell")
    
    # ── Derive tick duration ─────────────────────────────────────────────────
    print(f"\n[3] Deriving tick duration from light speed")
    
    # Light traverses 1 Planck length per tick
    # tick_duration = L_planck / (c × total_ticks_per_cell)
    tick_duration = L_PLANCK / (C * total_ticks)
    
    print(f"    Tick duration = L_p / (c × ticks_per_cell)")
    print(f"                  = {L_PLANCK} / ({C} × {total_ticks})")
    print(f"                  = {tick_duration:.6e} seconds")
    
    # ── Derive energy scale ──────────────────────────────────────────────────
    print(f"\n[4] Deriving energy scale (Joules per geometric work unit)")
    
    # From Planck's relation: E = h / t
    # 1 geometric work unit = 1 bit-step × NRCI
    # At vacuum NRCI = 1.0, 1 work unit = 1 bit-step
    # Energy per work unit = h / tick_duration
    joules_per_work = H / tick_duration
    
    print(f"    Energy per work unit = h / tick_duration")
    print(f"                        = {H} / {tick_duration:.6e}")
    print(f"                        = {joules_per_work:.6e} Joules")
    
    # Convert to kJ/mol
    # 1 work unit in kJ/mol = joules_per_work × N_A / 1000
    kj_mol_per_work = joules_per_work * N_A / 1000
    
    print(f"    kJ/mol per work unit = {joules_per_work:.6e} × {N_A:.6e} / 1000")
    print(f"                        = {kj_mol_per_work:.6e} kJ/mol")
    
    # ── Apply to element pairs ───────────────────────────────────────────────
    print(f"\n[5] Applying calibration to element pairs")
    
    kb_path = Path("/home/work/.openclaw/workspace/GLM/long_term_memory/ubp_system_kb.json")
    elements = load_elements_from_kb(str(kb_path))
    golay = GolayEngine()
    
    data_objects = {}
    for sym in elements:
        do = encode_element(sym, elements, BEST_ENCODING, golay)
        if do:
            data_objects[sym] = do
    
    # Compute geometric work for each pair
    from geometric_work import settle_with_trajectory, graduated_activation_warp
    
    pairs_data = []
    for sym_a, sym_b, be, dh, label, bo in EXPANDED_PAIRS:
        if sym_a not in data_objects or sym_b not in data_objects:
            continue
        do_a, do_b = data_objects[sym_a], data_objects[sym_b]
        
        # Apply graduated warp
        warped_b = graduated_activation_warp(do_b.codeword, bo)
        warped_b, _ = golay.snap_to_codeword(warped_b)
        warped_do = DataObject(
            symbol=f"{sym_b}_w", raw_bits=warped_b, codeword=warped_b,
            snap_meta={}, properties={}, encoding_spec={},
        )
        
        settlement = settle_with_trajectory(do_a, warped_do, golay, steps=10)
        work = settlement["work"]
        
        # Convert to kJ/mol
        predicted_kj_mol = work["nrci_weighted_work"] * kj_mol_per_work
        
        pairs_data.append({
            "label": label,
            "actual_be": be,
            "work_units": work["nrci_weighted_work"],
            "predicted_kj_mol": predicted_kj_mol,
        })
    
    # Show sample predictions
    print(f"\n    {'Label':<30} {'Work':>8} {'Predicted':>12} {'Actual':>8} {'Error':>10}")
    print(f"    {'-'*70}")
    
    for p in pairs_data[:20]:
        error = p["actual_be"] - p["predicted_kj_mol"]
        print(f"    {p['label']:<30} {p['work_units']:>8.2f} {p['predicted_kj_mol']:>12.1f} "
              f"{p['actual_be']:>8} {error:>+10.1f}")
    
    # Correlation
    actuals = [p["actual_be"] for p in pairs_data]
    predicted = [p["predicted_kj_mol"] for p in pairs_data]
    r = pearson_r(predicted, actuals)
    mae_val = mae(predicted, actuals)
    
    print(f"\n    Correlation (predicted vs actual): r = {r:.4f}")
    print(f"    MAE: {mae_val:.1f} kJ/mol")
    
    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print("CALIBRATION SUMMARY")
    print(f"{'='*72}")
    print(f"  Tick duration:          {tick_duration:.6e} seconds")
    print(f"  Joules per work unit:   {joules_per_work:.6e} J")
    print(f"  kJ/mol per work unit:   {kj_mol_per_work:.6e} kJ/mol")
    print(f"  Prediction r:           {r:.4f}")
    print(f"  Prediction MAE:         {mae_val:.1f} kJ/mol")
    print()
    
    # The scale factor
    print(f"  The scale factor converts abstract Leech-space bit-shifts")
    print(f"  into real thermodynamic values (kJ/mol).")
    print()
    print(f"  To use: predicted_BE_kJ = geometric_work × {kj_mol_per_work:.6e}")
    
    return {
        "tick_duration": tick_duration,
        "joules_per_work": joules_per_work,
        "kj_mol_per_work": kj_mol_per_work,
        "prediction_r": r,
        "prediction_mae": mae_val,
    }


# ════════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--optimize", action="store_true", help="Optimize warping permutations")
    parser.add_argument("--calibrate", action="store_true", help="Calibrate with light speed")
    parser.add_argument("--both", action="store_true", help="Run both")
    args = parser.parse_args()
    
    if args.optimize or args.both:
        run_optimizer()
    if args.calibrate or args.both:
        run_calibration()
    if not any([args.optimize, args.calibrate, args.both]):
        parser.print_help()
