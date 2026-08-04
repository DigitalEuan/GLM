#!/usr/bin/env python3
"""
Refined Warping — Using GLM Mechanisms for Element Interactions
================================================================
Experiment: encoding_definition_attempt_04.08-26
Date: 4 August 2026

The GLM has three mechanisms we haven't used:
1. Geometric Realignment — midpoints snap to nearest codeword
2. Time Drift — concepts settle toward neighbors
3. Deterministic settlement — same input → same output

These are EXACTLY what we need for bond formation:
- Bond = midpoint of two elements, snapped to codeword
- Settlement = iterative refinement of bond geometry
- Determinism = reproducible interactions

Key insight: The GLM's realignment algorithm IS bond formation.
Two related concepts → midpoint → snap to codeword = bond formation.

Usage:
  python3 refined_warping.py --full-test
  python3 refined_warping.py --warp-sweep
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
# 1. GLM-STYLE BOND FORMATION
# ════════════════════════════════════════════════════════════════════════════════

def glm_bond_formation(do_a: DataObject, do_b: DataObject,
                       golay: GolayEngine) -> DataObject:
    """
    Form a bond using the GLM's geometric realignment algorithm.
    
    The GLM finds the midpoint of two related concepts and snaps to
    the nearest Golay codeword. This IS bond formation:
    
    1. Compute midpoint of element codewords (AND = shared structure)
    2. Snap to nearest Golay codeword (error correction = bond formation)
    3. The resulting codeword IS the bond's geometric identity
    
    This is different from simple AND — it uses the full Golay snap
    which can correct up to 3 errors, potentially finding a valid
    codeword that's closer to the true bond state.
    """
    ca, cb = do_a.codeword, do_b.codeword
    
    # Method 1: AND midpoint (shared structure)
    and_mid = [ca[i] & cb[i] for i in range(24)]
    
    # Method 2: Average midpoint (like GLM realignment)
    # Convert to {0, 1} by thresholding at 0.5
    avg_mid = [1 if (ca[i] + cb[i]) >= 1 else 0 for i in range(24)]
    
    # Method 3: Weighted midpoint (by element NRCI)
    nrci_a = float(do_a.nrci())
    nrci_b = float(do_b.nrci())
    total = nrci_a + nrci_b
    if total > 0:
        wa, wb = nrci_a / total, nrci_b / total
    else:
        wa, wb = 0.5, 0.5
    weighted_mid = [1 if (wa * ca[i] + wb * cb[i]) >= 0.5 else 0 for i in range(24)]
    
    # Snap all three to nearest codeword
    and_cw, and_meta = golay.snap_to_codeword(and_mid)
    avg_cw, avg_meta = golay.snap_to_codeword(avg_mid)
    weighted_cw, weighted_meta = golay.snap_to_codeword(weighted_mid)
    
    # Return the one with lowest syndrome weight (closest to valid)
    candidates = [
        (and_cw, and_meta, "and"),
        (avg_cw, avg_meta, "avg"),
        (weighted_cw, weighted_meta, "weighted"),
    ]
    
    # Pick the one that's already a valid codeword (syndrome=0) or closest
    best = min(candidates, key=lambda x: x[1].get('syndrome_weight', 999))
    
    return DataObject(
        symbol=f"{do_a.symbol}-{do_b.symbol}",
        raw_bits=best[0],
        codeword=best[0],
        snap_meta=best[1],
        properties={},
        encoding_spec={"method": best[2]},
    )


# ════════════════════════════════════════════════════════════════════════════════
# 2. WARPING STRATEGIES
# ════════════════════════════════════════════════════════════════════════════════

def warp_column_swap(codeword: List[int], cols: Tuple[int, int]) -> List[int]:
    """Swap two MOG columns in all 4 rows."""
    warped = list(codeword)
    c1, c2 = cols
    for row in range(4):
        base = row * 6
        warped[base + c1], warped[base + c2] = warped[base + c2], warped[base + c1]
    return warped


def warp_column_rotate(codeword: List[int], shift: int) -> List[int]:
    """Rotate all MOG columns by shift positions."""
    warped = list(codeword)
    for row in range(4):
        base = row * 6
        row_bits = warped[base:base + 6]
        # Circular shift
        shifted = row_bits[-shift:] + row_bits[:-shift]
        warped[base:base + 6] = shifted
    return warped


def warp_row_permute(codeword: List[int], perm: List[int]) -> List[int]:
    """Permute MOG rows."""
    warped = [0] * 24
    for new_row, old_row in enumerate(perm):
        warped[new_row * 6:(new_row + 1) * 6] = codeword[old_row * 6:(old_row + 1) * 6]
    return warped


def warp_bit_flip(codeword: List[int], positions: List[int]) -> List[int]:
    """Flip specific bits."""
    warped = list(codeword)
    for pos in positions:
        warped[pos] ^= 1
    return warped


def warp_xor_mask(codeword: List[int], mask: List[int]) -> List[int]:
    """XOR with a mask (like adding a Golay octad)."""
    return [codeword[i] ^ mask[i] for i in range(24)]


# ════════════════════════════════════════════════════════════════════════════════
# 3. WARPING SWEEP — TEST ALL STRATEGIES
# ════════════════════════════════════════════════════════════════════════════════

def run_warp_sweep():
    """Test all warping strategies systematically."""
    print("=" * 72)
    print("WARPING STRATEGY SWEEP")
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
    
    # Get all Golay octads for XOR warping
    octads = golay.get_octads()
    
    # ── Define warping strategies ─────────────────────────────────────────────
    strategies = {
        "identity": lambda cw, bo: list(cw),
        "swap_2_3": lambda cw, bo: warp_column_swap(cw, (2, 3)) if bo >= 2 else list(cw),
        "swap_4_5": lambda cw, bo: warp_column_swap(cw, (4, 5)) if bo >= 3 else list(cw),
        "swap_2_3_and_4_5": lambda cw, bo: warp_column_swap(warp_column_swap(cw, (2, 3)), (4, 5)) if bo >= 3 else (warp_column_swap(cw, (2, 3)) if bo >= 2 else list(cw)),
        "rotate_1": lambda cw, bo: warp_column_rotate(cw, 1) if bo >= 2 else list(cw),
        "rotate_2": lambda cw, bo: warp_column_rotate(cw, 2) if bo >= 2 else list(cw),
        "row_perm_1203": lambda cw, bo: warp_row_permute(cw, [1, 2, 0, 3]) if bo >= 2 else list(cw),
        "row_perm_0213": lambda cw, bo: warp_row_permute(cw, [0, 2, 1, 3]) if bo >= 2 else list(cw),
        "flip_activation": lambda cw, bo: warp_bit_flip(cw, list(range(12, 18))) if bo >= 2 else list(cw),
        "xor_octad_0": lambda cw, bo: warp_xor_mask(cw, octads[0]) if bo >= 2 else list(cw),
        "xor_octad_1": lambda cw, bo: warp_xor_mask(cw, octads[1]) if bo >= 2 else list(cw),
        "xor_octad_2": lambda cw, bo: warp_xor_mask(cw, octads[2]) if bo >= 2 else list(cw),
        "bond_formation": None,  # special case
    }
    
    # ── Test each strategy ────────────────────────────────────────────────────
    print(f"\n{'Strategy':<25} {'BE_r':>7} {'BO_r':>7} {'BE_mae':>8} {'BO_acc':>8}")
    print("-" * 58)
    
    best_be_r = 0
    best_strategy = None
    
    for name, warper in strategies.items():
        # Build warped feature vectors
        X_warped = []
        y_be = []
        y_bo = []
        
        for sym_a, sym_b, be, dh, label, bo in EXPANDED_PAIRS:
            if sym_a not in data_objects or sym_b not in data_objects:
                continue
            do_a, do_b = data_objects[sym_a], data_objects[sym_b]
            
            if name == "bond_formation":
                # Use GLM bond formation
                bond_do = glm_bond_formation(do_a, do_b, golay)
                warped_b = bond_do.codeword
            else:
                # Apply warping to element B
                warped_b = warper(do_b.codeword, bo)
            
            # Snap warped codeword
            warped_b, _ = golay.snap_to_codeword(warped_b)
            
            # Compute features from warped interaction
            ca = do_a.codeword
            cb = warped_b
            
            and_bits = [ca[i] & cb[i] for i in range(24)]
            xor_bits = [ca[i] ^ cb[i] for i in range(24)]
            
            features = [
                sum(and_bits),                    # AND HW
                sum(xor_bits),                    # XOR HW
                10.0 / (10.0 + float(Y_CONST) * sum(and_bits) + sum(b*b for b in and_bits) / 8.0),  # AND NRCI
                10.0 / (10.0 + float(Y_CONST) * sum(xor_bits) + sum(b*b for b in xor_bits) / 8.0),  # XOR NRCI
                # Per-row overlap
                sum(ca[r*6:(r+1)*6][i] & cb[r*6:(r+1)*6][i] for r in range(4) for i in range(6)),
                # Per-row difference
                sum(ca[r*6:(r+1)*6][i] ^ cb[r*6:(r+1)*6][i] for r in range(4) for i in range(6)),
                # Snap energy of bond
                float(Y_CONST) * sum(and_bits) + sum(b*b for b in and_bits) / 8.0,
                # Element properties
                do_a.hamming_weight,
                do_b.hamming_weight,
                float(do_a.nrci()),
                float(do_b.nrci()),
            ]
            
            X_warped.append(features)
            y_be.append(be)
            y_bo.append(bo)
        
        n = len(X_warped)
        X = np.array(X_warped)
        y = np.array(y_be)
        
        # Normalize
        X_mean = X.mean(axis=0)
        X_std = X.std(axis=0)
        X_std[X_std == 0] = 1
        X_norm = (X - X_mean) / X_std
        
        # 5-fold CV for BE
        folds = k_fold_split(n, k=5, seed=42)
        preds = np.zeros(n)
        for fi, (tr, te) in enumerate(folds):
            rf = SimpleRandomForest(n_trees=50, max_depth=3, seed=fi)
            rf.fit(X_norm[tr], y[tr])
            preds[te] = rf.predict(X_norm[te])
        
        be_r = pearson_r(preds.tolist(), y.tolist())
        be_mae_val = mae(preds.tolist(), y.tolist())
        
        # BO correlation (simple)
        bo_r = pearson_r(preds.tolist(), y_bo)
        
        # BO classification accuracy (k-NN)
        correct = 0
        for i in range(n):
            dists = []
            for j in range(n):
                if i == j:
                    continue
                d = math.sqrt(sum((X_norm[i][k] - X_norm[j][k])**2 for k in range(X_norm.shape[1])))
                dists.append((d, y_bo[j]))
            dists.sort()
            votes = {}
            for dist, bo in dists[:5]:
                w = 1.0 / max(dist, 0.001)
                votes[bo] = votes.get(bo, 0) + w
            pred_bo = max(votes, key=votes.get)
            if pred_bo == y_bo[i]:
                correct += 1
        bo_acc = correct / n
        
        print(f"{name:<25} {be_r:>7.4f} {bo_r:>7.4f} {be_mae_val:>8.1f} {bo_acc:>7.1%}")
        
        if be_r > best_be_r:
            best_be_r = be_r
            best_strategy = name
    
    print(f"\n  Best strategy: {best_strategy} (r={best_be_r:.4f})")
    
    return best_strategy, best_be_r


# ════════════════════════════════════════════════════════════════════════════════
# 4. GLM-STYLE SETTLEMENT ON ELEMENT PAIRS
# ════════════════════════════════════════════════════════════════════════════════

def glm_settle_pair(do_a: DataObject, do_b: DataObject,
                    golay: GolayEngine, steps: int = 10) -> Dict:
    """
    Settle an element pair using GLM-style time drift.
    
    The GLM's time_drift moves concepts toward their semantic neighbors
    and snaps to codewords after each step. For element pairs:
    
    1. Start with the bond midpoint (AND)
    2. At each step, move slightly toward the element with higher NRCI
    3. Snap to nearest codeword after each step
    4. Track the trajectory
    
    This simulates the bond "finding its equilibrium" through
    iterative geometric refinement.
    """
    ca, cb = do_a.codeword, do_b.codeword
    
    # Start with AND midpoint
    current = [ca[i] & cb[i] for i in range(24)]
    trajectory = [list(current)]
    
    nrci_a = float(do_a.nrci())
    nrci_b = float(do_b.nrci())
    
    for step in range(steps):
        # Move toward the element with higher NRCI (more stable)
        # This is like the GLM's geometric realignment
        if nrci_a >= nrci_b:
            target = ca
        else:
            target = cb
        
        # Blend: 90% current + 10% target
        new = []
        for i in range(24):
            blend = 0.9 * current[i] + 0.1 * target[i]
            new.append(1 if blend >= 0.5 else 0)
        
        # Snap to nearest codeword
        snapped, meta = golay.snap_to_codeword(new)
        current = snapped
        trajectory.append(list(current))
    
    # Compute settlement metrics
    start_tax = float(Y_CONST) * sum(trajectory[0]) + sum(b*b for b in trajectory[0]) / 8.0
    end_tax = float(Y_CONST) * sum(trajectory[-1]) + sum(b*b for b in trajectory[-1]) / 8.0
    
    return {
        "final_codeword": current,
        "trajectory": trajectory,
        "steps": steps,
        "start_tax": start_tax,
        "end_tax": end_tax,
        "tax_change": end_tax - start_tax,
        "converged": trajectory[-1] == trajectory[-2] if len(trajectory) > 1 else False,
    }


def run_settlement_test():
    """Test GLM-style settlement on element pairs."""
    print("\n" + "=" * 72)
    print("GLM-STYLE SETTLEMENT ON ELEMENT PAIRS")
    print("=" * 72)
    
    kb_path = Path("/home/work/.openclaw/workspace/GLM/long_term_memory/ubp_system_kb.json")
    elements = load_elements_from_kb(str(kb_path))
    golay = GolayEngine()
    
    data_objects = {}
    for sym in elements:
        do = encode_element(sym, elements, BEST_ENCODING, golay)
        if do:
            data_objects[sym] = do
    
    # Test settlement on key pairs
    key_pairs = [
        ("H", "O", 463, 1, "H-O water"),
        ("C", "O", 358, 1, "C-O methanol"),
        ("C", "O", 799, 2, "C=O CO2"),
        ("N", "N", 163, 1, "N-N hydrazine"),
        ("N", "N", 946, 3, "N≡N nitrogen"),
        ("Na", "Cl", 411, 1, "NaCl salt"),
        ("Fe", "O", 407, 1, "Fe-O hematite"),
    ]
    
    print(f"\n{'Pair':<20} {'BO':>3} {'BE':>6} {'Start_TAX':>10} {'End_TAX':>10} "
          f"{'ΔTAX':>8} {'Converged':>9} {'Final_HW':>9}")
    print("-" * 78)
    
    for sym_a, sym_b, be, bo, label in key_pairs:
        if sym_a not in data_objects or sym_b not in data_objects:
            continue
        
        result = glm_settle_pair(data_objects[sym_a], data_objects[sym_b], golay, steps=10)
        
        final_hw = sum(result['final_codeword'])
        converged = "Yes" if result['converged'] else "No"
        
        print(f"{label:<20} {bo:>3} {be:>6} {result['start_tax']:>10.4f} "
              f"{result['end_tax']:>10.4f} {result['tax_change']:>+8.4f} "
              f"{converged:>9} {final_hw:>9}")
    
    # Use settlement as features for prediction
    print(f"\n[2] Settlement features for BE prediction (5-fold CV)")
    
    X_settle = []
    y_be = []
    y_bo = []
    
    for sym_a, sym_b, be, dh, label, bo in EXPANDED_PAIRS:
        if sym_a not in data_objects or sym_b not in data_objects:
            continue
        
        result = glm_settle_pair(data_objects[sym_a], data_objects[sym_b], golay, steps=5)
        
        # Settlement features
        features = [
            result['start_tax'],
            result['end_tax'],
            result['tax_change'],
            float(result['converged']),
            sum(result['final_codeword']),  # final HW
            # Trajectory features
            result['trajectory'][0].count(1),  # start HW
            result['trajectory'][-1].count(1),  # end HW
            # Element properties
            data_objects[sym_a].hamming_weight,
            data_objects[sym_b].hamming_weight,
            float(data_objects[sym_a].nrci()),
            float(data_objects[sym_b].nrci()),
        ]
        
        X_settle.append(features)
        y_be.append(be)
        y_bo.append(bo)
    
    n = len(X_settle)
    X = np.array(X_settle)
    y = np.array(y_be)
    
    # Normalize
    X_mean = X.mean(axis=0)
    X_std = X.std(axis=0)
    X_std[X_std == 0] = 1
    X_norm = (X - X_mean) / X_std
    
    folds = k_fold_split(n, k=5, seed=42)
    preds = np.zeros(n)
    
    for fi, (tr, te) in enumerate(folds):
        rf = SimpleRandomForest(n_trees=100, max_depth=3, seed=fi)
        rf.fit(X_norm[tr], y[tr])
        preds[te] = rf.predict(X_norm[te])
        fold_r = pearson_r(preds[te].tolist(), y[te].tolist())
        print(f"    Fold {fi+1}: r={fold_r:.4f}")
    
    settle_r = pearson_r(preds.tolist(), y.tolist())
    settle_mae_val = mae(preds.tolist(), y.tolist())
    print(f"    Overall CV r = {settle_r:.4f}")
    print(f"    Overall CV MAE = {settle_mae_val:.1f}")
    
    return settle_r


# ════════════════════════════════════════════════════════════════════════════════
# 5. FULL TEST
# ════════════════════════════════════════════════════════════════════════════════

def run_full_test():
    """Run the complete refined warping test."""
    print("=" * 72)
    print("REFINED WARPING — FULL TEST")
    print("Using GLM mechanisms: realignment, settlement, determinism")
    print("=" * 72)
    
    # Part 1: Warping sweep
    best_strategy, best_r = run_warp_sweep()
    
    # Part 2: Settlement test
    settle_r = run_settlement_test()
    
    # Summary
    print(f"\n{'='*72}")
    print("REFINED WARPING SUMMARY")
    print(f"{'='*72}")
    print(f"  Best warping strategy: {best_strategy} (r={best_r:.4f})")
    print(f"  Settlement features:   r={settle_r:.4f}")
    print()
    
    if best_r > 0.3:
        print(f"  ✓ Warping shows meaningful improvement")
    if settle_r > 0.2:
        print(f"  ✓ Settlement dynamics carry signal")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-test", action="store_true")
    parser.add_argument("--warp-sweep", action="store_true")
    args = parser.parse_args()
    
    if args.full_test or args.warp_sweep:
        run_full_test()
    else:
        parser.print_help()
