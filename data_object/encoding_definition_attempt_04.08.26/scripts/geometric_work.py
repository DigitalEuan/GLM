#!/usr/bin/env python3
"""
Geometric Work + Graduated Warp + Three-Column Diagnostics
===========================================================
Experiment: encoding_definition_attempt_04.08-26
Date: 4 August 2026

Implements all three feedback items:
1. Geometric Work — path integral of settlement dynamics
2. Graduated Activation Warp — different warps per bond order
3. Three-Column Diagnostic — aligned language/math/script

Usage:
  python3 geometric_work.py --full-test
  python3 geometric_work.py --diagnose N N 3
  python3 geometric_work.py --diagnose H O 1
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from elements_data_object_system import (
    GolayEngine, DataObject, MOGSpatialArithmetic,
    load_elements_from_kb, encode_element, interact, InteractionResult,
    BEST_ENCODING, Y_CONST,
)
from refined_element_system import (
    EXPANDED_PAIRS, pearson_r, mae, k_fold_split,
)
from three_directions import SimpleRandomForest

import numpy as np


# ════════════════════════════════════════════════════════════════════════════════
# 1. GEOMETRIC WORK — Path Integral of Settlement
# ════════════════════════════════════════════════════════════════════════════════

def hamming_distance(a: List[int], b: List[int]) -> int:
    return sum(a[i] ^ b[i] for i in range(len(a)))


def nrci_from_bits(bits: List[int]) -> float:
    hw = sum(bits)
    ns = sum(b * b for b in bits)
    tax = float(Y_CONST) * hw + ns / 8.0
    return 10.0 / (10.0 + tax)


def geometric_work(trajectory: List[List[int]]) -> Dict[str, float]:
    """
    Compute the Geometric Work (Action) done during settlement.
    
    Geometric Work = Σ_t HD(V_t, V_{t+1}) × NRCI_t
    
    This measures the structural "strain" — how much the bond vector
    moves through Leech space during settlement, weighted by coherence.
    
    Physical interpretation:
    - High work = bond undergoes significant structural reorganization
    - Low work = bond is already in a stable configuration
    - Work × sign indicates whether the bond releases or absorbs energy
    """
    if len(trajectory) < 2:
        return {
            "total_work": 0.0,
            "mean_step": 0.0,
            "max_step": 0,
            "nrci_weighted_work": 0.0,
            "path_length": 0,
            "net_displacement": 0,
            "tortuosity": 0.0,
        }
    
    total_work = 0.0
    nrci_weighted_work = 0.0
    max_step = 0
    steps = []
    
    for t in range(len(trajectory) - 1):
        hd = hamming_distance(trajectory[t], trajectory[t + 1])
        nrci_t = nrci_from_bits(trajectory[t])
        
        total_work += hd
        nrci_weighted_work += hd * nrci_t
        max_step = max(max_step, hd)
        steps.append(hd)
    
    # Path length = total Hamming distance traveled
    path_length = total_work
    
    # Net displacement = distance from start to end
    net_displacement = hamming_distance(trajectory[0], trajectory[-1])
    
    # Tortuosity = path_length / net_displacement (>1 = winding path)
    tortuosity = path_length / max(net_displacement, 1)
    
    return {
        "total_work": total_work,
        "mean_step": total_work / len(steps) if steps else 0,
        "max_step": max_step,
        "nrci_weighted_work": nrci_weighted_work,
        "path_length": path_length,
        "net_displacement": net_displacement,
        "tortuosity": tortuosity,
        "n_steps": len(steps),
    }


def settle_with_trajectory(do_a: DataObject, do_b: DataObject,
                           golay: GolayEngine, steps: int = 10) -> Dict:
    """
    Settle an element pair and record the full trajectory.
    
    Uses GLM-style geometric realignment:
    1. Start with bond midpoint (AND)
    2. At each step, blend toward the more stable element
    3. Snap to nearest codeword after each step
    4. Record full trajectory for geometric work calculation
    """
    ca, cb = do_a.codeword, do_b.codeword
    nrci_a = float(do_a.nrci())
    nrci_b = float(do_b.nrci())
    
    # Start with AND midpoint
    current = [ca[i] & cb[i] for i in range(24)]
    trajectory = [list(current)]
    
    for step in range(steps):
        # Blend toward the more stable element
        if nrci_a >= nrci_b:
            target = ca
        else:
            target = cb
        
        # Blend: 85% current + 15% target (more movement than before)
        new = []
        for i in range(24):
            blend = 0.85 * current[i] + 0.15 * target[i]
            new.append(1 if blend >= 0.5 else 0)
        
        # Snap to nearest codeword
        snapped, meta = golay.snap_to_codeword(new)
        current = snapped
        trajectory.append(list(current))
    
    # Compute geometric work
    work = geometric_work(trajectory)
    
    return {
        "trajectory": trajectory,
        "work": work,
        "final_codeword": current,
        "final_hw": sum(current),
        "final_nrci": nrci_from_bits(current),
    }


# ════════════════════════════════════════════════════════════════════════════════
# 2. GRADUATED ACTIVATION WARP
# ════════════════════════════════════════════════════════════════════════════════

def graduated_activation_warp(codeword: List[int], bond_order: int) -> List[int]:
    """
    Graduated warp: different operations for different bond orders.
    
    BO=1 (single):   no warp (identity)
    BO=2 (double):   flip bits 12-14 (first half of Activation row)
    BO=3 (triple):   flip bits 12-17 (full Activation row)
    BO=1.5 (aromatic): rotate Activation row by 1 position
    
    This creates a STEPPED spatial gradient in Leech space
    directly proportional to bond multiplicity.
    """
    if bond_order <= 1:
        return list(codeword)
    
    warped = list(codeword)
    
    if bond_order == 1.5:
        # Aromatic: rotate Activation row by 1
        base = 12
        row_bits = warped[base:base + 6]
        warped[base:base + 6] = row_bits[-1:] + row_bits[:-1]
    elif bond_order == 2:
        # Double: flip first 3 bits of Activation row (12-14)
        for i in range(12, 15):
            warped[i] ^= 1
    elif bond_order >= 3:
        # Triple: flip full Activation row (12-17)
        for i in range(12, 18):
            warped[i] ^= 1
    
    return warped


def barrel_shift_warp(codeword: List[int], bond_order: int) -> List[int]:
    """
    Barrel shift within Activation row.
    Shift distance = BO - 1.
    
    BO=1: no shift
    BO=2: shift by 1
    BO=3: shift by 2
    """
    if bond_order <= 1:
        return list(codeword)
    
    warped = list(codeword)
    shift = int(bond_order) - 1
    base = 12
    row_bits = warped[base:base + 6]
    shifted = row_bits[-shift:] + row_bits[:-shift]
    warped[base:base + 6] = shifted
    return warped


# ════════════════════════════════════════════════════════════════════════════════
# 3. THREE-COLUMN DIAGNOSTIC
# ════════════════════════════════════════════════════════════════════════════════

def three_column_diagnose(sym_a: str, sym_b: str, bond_order: int,
                          data_objects: Dict, golay: GolayEngine):
    """Three-Column Thinking diagnostic for a bond."""
    
    do_a = data_objects[sym_a]
    do_b = data_objects[sym_b]
    
    print("=" * 72)
    print(f"THREE-COLUMN DIAGNOSTIC: {sym_a} + {sym_b} (BO={bond_order})")
    print("=" * 72)
    
    # ── Step 1: PERCEPTION ────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print("Step 1: PERCEPTION")
    print(f"{'─'*72}")
    
    ca, cb = do_a.codeword, do_b.codeword
    
    print(f"  Language: Initialize elements {sym_a} and {sym_b} with bond order {bond_order}.")
    print(f"  Math:     v({sym_a}) = {ca[:6]}|{ca[6:12]}|{ca[12:18]}|{ca[18:24]}")
    print(f"            v({sym_b}) = {cb[:6]}|{cb[6:12]}|{cb[12:18]}|{cb[18:24]}")
    print(f"            HW({sym_a}) = {do_a.hamming_weight}, NRCI = {float(do_a.nrci()):.4f}")
    print(f"            HW({sym_b}) = {do_b.hamming_weight}, NRCI = {float(do_b.nrci()):.4f}")
    print(f"  Script:   do_a = data_objects['{sym_a}']")
    print(f"            do_b = data_objects['{sym_b}']")
    
    # ── Step 2: WARPING ───────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print("Step 2: WARPING")
    print(f"{'─'*72}")
    
    warped = graduated_activation_warp(cb, bond_order)
    warped_snapped, warped_meta = golay.snap_to_codeword(warped)
    
    # Show what changed
    changed_bits = [i for i in range(24) if cb[i] != warped_snapped[i]]
    changed_rows = set(i // 6 for i in changed_bits)
    row_names = ["Reality", "Info", "Activation", "Potential"]
    
    print(f"  Language: Applying graduated Activation warp for BO={bond_order}.")
    if bond_order == 1:
        print(f"            No warp applied (single bond).")
    elif bond_order == 2:
        print(f"            Flipping bits 12-14 (first half of Activation row).")
    elif bond_order >= 3:
        print(f"            Flipping bits 12-17 (full Activation row).")
    
    print(f"  Math:     v({sym_b})_warped = {warped_snapped[:6]}|{warped_snapped[6:12]}|{warped_snapped[12:18]}|{warped_snapped[18:24]}")
    print(f"            Changed bits: {changed_bits}")
    print(f"            Changed rows: {[row_names[r] for r in changed_rows]}")
    print(f"  Script:   warped = graduated_activation_warp(do_b.codeword, {bond_order})")
    
    # ── Step 3: INTERACTION ───────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print("Step 3: INTERACTION")
    print(f"{'─'*72}")
    
    # AND/XOR with warped codeword
    and_bits = [ca[i] & warped_snapped[i] for i in range(24)]
    xor_bits = [ca[i] ^ warped_snapped[i] for i in range(24)]
    and_hw = sum(and_bits)
    xor_hw = sum(xor_bits)
    and_nrci = nrci_from_bits(and_bits)
    xor_nrci = nrci_from_bits(xor_bits)
    
    # Per-row overlap
    row_overlap = []
    for r in range(4):
        overlap = sum(ca[r*6:(r+1)*6][i] & warped_snapped[r*6:(r+1)*6][i] for i in range(6))
        row_overlap.append(overlap)
    
    print(f"  Language: Computing interaction between {sym_a} and warped {sym_b}.")
    print(f"  Math:     AND_HW = {and_hw}, XOR_HW = {xor_hw}")
    print(f"            AND_NRCI = {and_nrci:.4f}, XOR_NRCI = {xor_nrci:.4f}")
    print(f"            Row overlap: R={row_overlap[0]} I={row_overlap[1]} A={row_overlap[2]} P={row_overlap[3]}")
    print(f"  Script:   result = interact(do_a, warped_do_b)")
    
    # ── Step 4: SETTLEMENT ────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print("Step 4: SETTLEMENT (Geometric Work)")
    print(f"{'─'*72}")
    
    # Create warped Data Object
    warped_do = DataObject(
        symbol=f"{sym_b}_warped",
        raw_bits=warped_snapped,
        codeword=warped_snapped,
        snap_meta=warped_meta,
        properties={},
        encoding_spec={},
    )
    
    settlement = settle_with_trajectory(do_a, warped_do, golay, steps=10)
    work = settlement["work"]
    
    print(f"  Language: Running settlement loop. Calculating geometric work.")
    print(f"  Math:     Path integral = {work['total_work']:.1f} bit-steps")
    print(f"            NRCI-weighted work = {work['nrci_weighted_work']:.4f}")
    print(f"            Net displacement = {work['net_displacement']} bits")
    print(f"            Tortuosity = {work['tortuosity']:.2f}")
    print(f"            Final HW = {settlement['final_hw']}, Final NRCI = {settlement['final_nrci']:.4f}")
    print(f"  Script:   settlement = settle_with_trajectory(do_a, warped_do, golay)")
    
    # Show trajectory
    print(f"\n  Trajectory:")
    for t, state in enumerate(settlement["trajectory"][:6]):
        hw = sum(state)
        nrci = nrci_from_bits(state)
        print(f"    t={t}: HW={hw:2d}  NRCI={nrci:.4f}  {state[:6]}|{state[6:12]}|{state[12:18]}|{state[18:24]}")
    if len(settlement["trajectory"]) > 6:
        print(f"    ... ({len(settlement['trajectory'])-6} more steps)")
    
    # ── Step 5: PREDICTION ────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print("Step 5: PREDICTION")
    print(f"{'─'*72}")
    
    # Look up actual BE if available
    actual_be = None
    for sa, sb, be, dh, label, bo in EXPANDED_PAIRS:
        if sa == sym_a and sb == sym_b and bo == bond_order:
            actual_be = be
            break
        if sa == sym_b and sb == sym_a and bo == bond_order:
            actual_be = be
            break
    
    # Prediction: combine geometric work with interaction metrics
    predicted_be = work['nrci_weighted_work'] * 100 + and_nrci * 200
    
    print(f"  Language: Settlement work indicates {'high' if work['total_work'] > 5 else 'low'} structural reorganization.")
    print(f"  Math:     Predicted BE ≈ {predicted_be:.0f} kJ/mol")
    if actual_be:
        error = abs(actual_be - predicted_be)
        print(f"            Actual BE = {actual_be} kJ/mol, Error = {error:.0f} kJ/mol")
    print(f"  Script:   print(f'Prediction: {{predicted_be:.0f}} kJ/mol')")
    
    return {
        "and_hw": and_hw,
        "and_nrci": and_nrci,
        "xor_hw": xor_hw,
        "xor_nrci": xor_nrci,
        "work": work,
        "actual_be": actual_be,
    }


# ════════════════════════════════════════════════════════════════════════════════
# 4. FULL TEST — Geometric Work + Graduated Warp
# ════════════════════════════════════════════════════════════════════════════════

def run_full_test():
    """Run the complete geometric work + graduated warp test."""
    print("=" * 72)
    print("GEOMETRIC WORK + GRADUATED WARP — FULL TEST")
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
    
    # ── Build feature vectors ─────────────────────────────────────────────────
    print(f"\n[1] Building features: interaction + geometric work + graduated warp")
    
    X_features = []
    y_be = []
    y_bo = []
    labels = []
    
    for sym_a, sym_b, be, dh, label, bo in EXPANDED_PAIRS:
        if sym_a not in data_objects or sym_b not in data_objects:
            continue
        do_a, do_b = data_objects[sym_a], data_objects[sym_b]
        ca, cb = do_a.codeword, do_b.codeword
        
        # Graduated warp
        warped_b = graduated_activation_warp(cb, bo)
        warped_b, _ = golay.snap_to_codeword(warped_b)
        
        # Create warped Data Object
        warped_do = DataObject(
            symbol=f"{sym_b}_w", raw_bits=warped_b, codeword=warped_b,
            snap_meta={}, properties={}, encoding_spec={},
        )
        
        # Interaction metrics (with warped codeword)
        and_bits = [ca[i] & warped_b[i] for i in range(24)]
        xor_bits = [ca[i] ^ warped_b[i] for i in range(24)]
        and_hw = sum(and_bits)
        xor_hw = sum(xor_bits)
        and_nrci = nrci_from_bits(and_bits)
        xor_nrci = nrci_from_bits(xor_bits)
        
        # Settlement with trajectory
        settlement = settle_with_trajectory(do_a, warped_do, golay, steps=10)
        work = settlement["work"]
        
        # Per-row overlap with warped codeword
        row_overlap = [sum(ca[r*6:(r+1)*6][i] & warped_b[r*6:(r+1)*6][i] for i in range(6)) for r in range(4)]
        row_diff = [sum(ca[r*6:(r+1)*6][i] ^ warped_b[r*6:(r+1)*6][i] for i in range(6)) for r in range(4)]
        
        features = [
            # Interaction metrics
            and_hw,
            xor_hw,
            and_nrci,
            xor_nrci,
            and_nrci - xor_nrci,  # delta NRCI
            # Per-row decomposition
            *row_overlap,
            *row_diff,
            # Geometric work
            work["total_work"],
            work["nrci_weighted_work"],
            work["net_displacement"],
            work["tortuosity"],
            work["max_step"],
            # Settlement outcome
            settlement["final_hw"],
            settlement["final_nrci"],
            # Element properties
            do_a.hamming_weight,
            do_b.hamming_weight,
            float(do_a.nrci()),
            float(do_b.nrci()),
        ]
        
        X_features.append(features)
        y_be.append(be)
        y_bo.append(bo)
        labels.append(label)
    
    n = len(X_features)
    n_feat = len(X_features[0])
    print(f"    Pairs: {n}, Features: {n_feat}")
    
    # Feature names
    feat_names = [
        'and_hw', 'xor_hw', 'and_nrci', 'xor_nrci', 'delta_nrci',
        'ov_R', 'ov_I', 'ov_A', 'ov_P',
        'diff_R', 'diff_I', 'diff_A', 'diff_P',
        'work_total', 'work_nrci', 'net_disp', 'tortuosity', 'max_step',
        'final_hw', 'final_nrci',
        'hw_a', 'hw_b', 'nrci_a', 'nrci_b',
    ]
    
    # Normalize
    X = np.array(X_features)
    y = np.array(y_be)
    X_mean = X.mean(axis=0)
    X_std = X.std(axis=0)
    X_std[X_std == 0] = 1
    X_norm = (X - X_mean) / X_std
    
    # ── Feature correlations ──────────────────────────────────────────────────
    print(f"\n[2] Feature correlations with bond energy:")
    for i, name in enumerate(feat_names):
        vals = [X_features[j][i] for j in range(n)]
        r = pearson_r(vals, y_be)
        if abs(r) > 0.15:
            bar = "█" * min(int(abs(r) * 30), 30)
            print(f"    {name:<18} r={r:>7.4f}  {bar}")
    
    # ── Random Forest CV ──────────────────────────────────────────────────────
    print(f"\n[3] Random Forest (100 trees, 5-fold CV)")
    
    folds = k_fold_split(n, k=5, seed=42)
    preds = np.zeros(n)
    
    for fi, (tr, te) in enumerate(folds):
        rf = SimpleRandomForest(n_trees=100, max_depth=3, seed=fi)
        rf.fit(X_norm[tr], y[tr])
        preds[te] = rf.predict(X_norm[te])
        fold_r = pearson_r(preds[te].tolist(), y[te].tolist())
        print(f"    Fold {fi+1}: r={fold_r:.4f}")
    
    cv_r = pearson_r(preds.tolist(), y.tolist())
    cv_mae_val = mae(preds.tolist(), y.tolist())
    print(f"    Overall CV r = {cv_r:.4f}")
    print(f"    Overall CV MAE = {cv_mae_val:.1f}")
    
    # ── BO classification ─────────────────────────────────────────────────────
    print(f"\n[4] Bond order classification (LOO k-NN)")
    
    correct = 0
    for i in range(n):
        dists = []
        for j in range(n):
            if i == j:
                continue
            d = math.sqrt(sum((X_norm[i][k] - X_norm[j][k])**2 for k in range(n_feat)))
            dists.append((d, y_bo[j]))
        dists.sort()
        votes = {}
        for dist, bo in dists[:5]:
            w = 1.0 / max(dist, 0.001)
            votes[bo] = votes.get(bo, 0) + w
        pred_bo = max(votes, key=votes.get)
        if pred_bo == y_bo[i]:
            correct += 1
    
    print(f"    k-NN (k=5) LOO: {correct}/{n} = {correct/n:.1%}")
    
    # ── Barrel shift comparison ───────────────────────────────────────────────
    print(f"\n[5] Barrel shift warp comparison")
    
    for warp_name, warper in [("graduated", graduated_activation_warp), 
                               ("barrel_shift", barrel_shift_warp)]:
        X_warp = []
        for sym_a, sym_b, be, dh, label, bo in EXPANDED_PAIRS:
            if sym_a not in data_objects or sym_b not in data_objects:
                continue
            do_a, do_b = data_objects[sym_a], data_objects[sym_b]
            ca, cb = do_a.codeword, do_b.codeword
            
            warped_b = warper(cb, bo)
            warped_b, _ = golay.snap_to_codeword(warped_b)
            
            and_bits = [ca[i] & warped_b[i] for i in range(24)]
            xor_bits = [ca[i] ^ warped_b[i] for i in range(24)]
            
            features = [
                sum(and_bits), sum(xor_bits),
                nrci_from_bits(and_bits), nrci_from_bits(xor_bits),
                do_a.hamming_weight, do_b.hamming_weight,
                float(do_a.nrci()), float(do_b.nrci()),
            ]
            X_warp.append(features)
        
        X_w = np.array(X_warp)
        X_w_mean = X_w.mean(axis=0)
        X_w_std = X_w.std(axis=0)
        X_w_std[X_w_std == 0] = 1
        X_w_norm = (X_w - X_w_mean) / X_w_std
        
        w_preds = np.zeros(n)
        for fi, (tr, te) in enumerate(folds):
            rf = SimpleRandomForest(n_trees=100, max_depth=3, seed=fi)
            rf.fit(X_w_norm[tr], y[tr])
            w_preds[te] = rf.predict(X_w_norm[te])
        
        w_r = pearson_r(w_preds.tolist(), y.tolist())
        w_mae_val = mae(w_preds.tolist(), y.tolist())
        print(f"    {warp_name:<15} r={w_r:.4f}  MAE={w_mae_val:.1f}")
    
    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print("GEOMETRIC WORK + GRADUATED WARP SUMMARY")
    print(f"{'='*72}")
    print(f"  Features:          {n_feat}")
    print(f"  CV r:              {cv_r:.4f}")
    print(f"  CV MAE:            {cv_mae_val:.1f}")
    print(f"  BO accuracy:       {correct/n:.1%}")
    print()
    
    # Best features
    print(f"  Top features:")
    importance = list(zip(feat_names, [pearson_r([X_features[j][i] for j in range(n)], y_be) for i in range(n_feat)]))
    importance.sort(key=lambda x: abs(x[1]), reverse=True)
    for name, r in importance[:8]:
        bar = "█" * min(int(abs(r) * 30), 30)
        print(f"    {name:<18} r={r:>7.4f}  {bar}")


# ════════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-test", action="store_true")
    parser.add_argument("--diagnose", nargs=3, metavar=("SYM_A", "SYM_B", "BO"))
    args = parser.parse_args()
    
    if args.full_test:
        run_full_test()
    elif args.diagnose:
        sym_a, sym_b, bo = args.diagnose[0], args.diagnose[1], int(args.diagnose[2])
        kb_path = Path("/home/work/.openclaw/workspace/GLM/long_term_memory/ubp_system_kb.json")
        elements = load_elements_from_kb(str(kb_path))
        golay = GolayEngine()
        data_objects = {}
        for sym in elements:
            do = encode_element(sym, elements, BEST_ENCODING, golay)
            if do:
                data_objects[sym] = do
        three_column_diagnose(sym_a, sym_b, bo, data_objects, golay)
    else:
        parser.print_help()
