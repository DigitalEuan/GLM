#!/usr/bin/env python3
"""
Three Directions — Nonlinear Predictors, Geometric Bonds, Understanding Tests
==============================================================================
Experiment: encoding_definition_attempt_04.08-26
Date: 4 August 2026

Direction 1: Nonlinear predictors (Jaccard, decision trees, ensemble)
Direction 2: Bond as geometric object, snap as interaction mechanism
Direction 3: Understanding tests beyond interactions (clustering, property prediction)

Usage:
  python3 three_directions.py --all
  python3 three_directions.py --direction 1
  python3 three_directions.py --direction 2
  python3 three_directions.py --direction 3
"""

from __future__ import annotations

import json
import math
import random
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from elements_data_object_system import (
    GolayEngine, DataObject, MOGSpatialArithmetic,
    load_elements_from_kb, encode_element, interact, InteractionResult,
    BEST_ENCODING, Y_CONST,
)
from refined_element_system import (
    EXPANDED_PAIRS, compute_snap_dynamics, compute_interaction_snap_dynamics,
    pearson_r, mae, k_fold_split,
)

import numpy as np

# ════════════════════════════════════════════════════════════════════════════════
# DIRECTION 1: NONLINEAR PREDICTORS
# ════════════════════════════════════════════════════════════════════════════════

def jaccard_similarity(a: List[int], b: List[int]) -> float:
    """Jaccard index: |intersection| / |union| of set bits."""
    intersection = sum(1 for i in range(len(a)) if a[i] == 1 and b[i] == 1)
    union = sum(1 for i in range(len(a)) if a[i] == 1 or b[i] == 1)
    return intersection / union if union > 0 else 0.0


def jaccard_distance(a: List[int], b: List[int]) -> float:
    """1 - Jaccard similarity."""
    return 1.0 - jaccard_similarity(a, b)


def dice_coefficient(a: List[int], b: List[int]) -> float:
    """Dice coefficient: 2|intersection| / (|a| + |b|)."""
    intersection = sum(1 for i in range(len(a)) if a[i] == 1 and b[i] == 1)
    total = sum(a) + sum(b)
    return 2 * intersection / total if total > 0 else 0.0


def cosine_similarity_bits(a: List[int], b: List[int]) -> float:
    """Cosine similarity for binary vectors."""
    dot = sum(a[i] * b[i] for i in range(len(a)))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0


def overlap_coefficient(a: List[int], b: List[int]) -> float:
    """Overlap coefficient: |intersection| / min(|a|, |b|)."""
    intersection = sum(1 for i in range(len(a)) if a[i] == 1 and b[i] == 1)
    min_size = min(sum(a), sum(b))
    return intersection / min_size if min_size > 0 else 0.0


class DecisionStump:
    """A single decision stump (one split)."""
    
    def __init__(self, feature_idx: int = 0, threshold: float = 0.0,
                 left_val: float = 0.0, right_val: float = 0.0):
        self.feature_idx = feature_idx
        self.threshold = threshold
        self.left_val = left_val
        self.right_val = right_val
    
    def predict(self, x: List[float]) -> float:
        if x[self.feature_idx] <= self.threshold:
            return self.left_val
        return self.right_val


class SimpleRandomForest:
    """Simple random forest from scratch (numpy only)."""
    
    def __init__(self, n_trees: int = 50, max_depth: int = 3, 
                 min_samples_leaf: int = 3, seed: int = 42):
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.rng = random.Random(seed)
        self.trees = []
    
    def _build_tree(self, X: np.ndarray, y: np.ndarray, depth: int = 0) -> Any:
        """Build a decision tree recursively."""
        n, m = X.shape
        
        # Stopping conditions
        if depth >= self.max_depth or n < self.min_samples_leaf * 2:
            return float(np.mean(y))
        
        # Find best split
        best_gain = -float('inf')
        best_idx = 0
        best_thresh = 0.0
        
        # Try random subset of features
        n_features = max(1, int(math.sqrt(m)))
        feature_indices = self.rng.sample(range(m), min(n_features, m))
        
        for fi in feature_indices:
            values = X[:, fi]
            # Try a few thresholds
            unique_vals = np.unique(values)
            if len(unique_vals) < 2:
                continue
            thresholds = np.percentile(unique_vals, [25, 50, 75])
            
            for thresh in thresholds:
                left_mask = values <= thresh
                right_mask = ~left_mask
                if np.sum(left_mask) < self.min_samples_leaf or np.sum(right_mask) < self.min_samples_leaf:
                    continue
                
                # Variance reduction
                var_total = np.var(y)
                var_left = np.var(y[left_mask]) if np.sum(left_mask) > 0 else 0
                var_right = np.var(y[right_mask]) if np.sum(right_mask) > 0 else 0
                n_left = np.sum(left_mask)
                n_right = np.sum(right_mask)
                
                gain = var_total - (n_left * var_left + n_right * var_right) / n
                
                if gain > best_gain:
                    best_gain = gain
                    best_idx = fi
                    best_thresh = thresh
        
        if best_gain <= 0:
            return float(np.mean(y))
        
        # Split
        left_mask = X[:, best_idx] <= best_thresh
        right_mask = ~left_mask
        
        left_child = self._build_tree(X[left_mask], y[left_mask], depth + 1)
        right_child = self._build_tree(X[right_mask], y[right_mask], depth + 1)
        
        return {
            'feature': best_idx,
            'threshold': best_thresh,
            'left': left_child,
            'right': right_child,
        }
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """Build the forest."""
        n = len(y)
        self.trees = []
        for _ in range(self.n_trees):
            # Bootstrap sample
            indices = [self.rng.randint(0, n - 1) for _ in range(n)]
            X_boot = X[indices]
            y_boot = y[indices]
            tree = self._build_tree(X_boot, y_boot)
            self.trees.append(tree)
    
    def _predict_tree(self, tree, x: List[float]) -> float:
        if isinstance(tree, (int, float)):
            return tree
        if x[tree['feature']] <= tree['threshold']:
            return self._predict_tree(tree['left'], x)
        return self._predict_tree(tree['right'], x)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        predictions = []
        for x in X:
            tree_preds = [self._predict_tree(t, x.tolist()) for t in self.trees]
            predictions.append(np.mean(tree_preds))
        return np.array(predictions)


class SimpleGradientBoost:
    """Simple gradient boosting from scratch."""
    
    def __init__(self, n_estimators: int = 50, learning_rate: float = 0.1,
                 max_depth: int = 2, seed: int = 42):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.rf = SimpleRandomForest(n_trees=1, max_depth=max_depth, seed=seed)
        self.trees = []
        self.base_prediction = 0.0
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        self.base_prediction = float(np.mean(y))
        residuals = y - self.base_prediction
        self.trees = []
        
        for _ in range(self.n_estimators):
            # Fit a tree to residuals
            tree_builder = SimpleRandomForest(n_trees=1, max_depth=self.rf.max_depth)
            tree_builder.fit(X, residuals)
            tree = tree_builder.trees[0]
            self.trees.append(tree)
            
            # Update residuals
            preds = tree_builder.predict(X)
            residuals = residuals - self.learning_rate * preds
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        preds = np.full(len(X), self.base_prediction)
        for tree in self.trees:
            tree_builder = SimpleRandomForest(n_trees=1)
            tree_builder.trees = [tree]
            preds += self.learning_rate * tree_builder.predict(X)
        return preds


def run_direction_1(data_objects, pairs_data):
    """Direction 1: Nonlinear predictors."""
    print("=" * 72)
    print("DIRECTION 1: NONLINEAR PREDICTORS")
    print("=" * 72)
    
    n = len(pairs_data)
    n_feat = len(pairs_data[0]['features'])
    
    # ── Set-based metrics ─────────────────────────────────────────────────────
    print("\n[1A] Set-based metrics (Jaccard, Dice, Cosine, Overlap)")
    
    # For each pair, compute set-based similarities between codewords
    set_features = []
    for p in pairs_data:
        do_a = data_objects[p['sym_a']]
        do_b = data_objects[p['sym_b']]
        ca, cb = do_a.codeword, do_b.codeword
        
        set_features.append([
            jaccard_similarity(ca, cb),
            dice_coefficient(ca, cb),
            cosine_similarity_bits(ca, cb),
            overlap_coefficient(ca, cb),
            # Also: per-row Jaccard
            jaccard_similarity(ca[0:6], cb[0:6]),   # Reality
            jaccard_similarity(ca[6:12], cb[6:12]),  # Info
            jaccard_similarity(ca[12:18], cb[12:18]), # Activation
            jaccard_similarity(ca[18:24], cb[18:24]), # Potential
        ])
    
    set_names = ['jaccard', 'dice', 'cosine', 'overlap',
                 'jaccard_R', 'jaccard_I', 'jaccard_A', 'jaccard_P']
    
    y_be = [p['be'] for p in pairs_data]
    
    print(f"    Metric correlations with bond energy:")
    for i, name in enumerate(set_names):
        vals = [sf[i] for sf in set_features]
        r = pearson_r(vals, y_be)
        bar = "█" * min(int(abs(r) * 30), 30)
        print(f"      {name:<15} r={r:>7.4f}  {bar}")
    
    # ── Random Forest ─────────────────────────────────────────────────────────
    print("\n[1B] Random Forest (50 trees, max_depth=3)")
    
    X = np.array([p['features'] for p in pairs_data])
    y = np.array(y_be)
    
    # Normalize
    X_mean = X.mean(axis=0)
    X_std = X.std(axis=0)
    X_std[X_std == 0] = 1
    X_norm = (X - X_mean) / X_std
    
    # 5-fold CV
    folds = k_fold_split(n, k=5, seed=42)
    rf_preds = np.zeros(n)
    
    for fi, (tr, te) in enumerate(folds):
        rf = SimpleRandomForest(n_trees=100, max_depth=3, seed=fi)
        rf.fit(X_norm[tr], y[tr])
        rf_preds[te] = rf.predict(X_norm[te])
        fold_r = pearson_r(rf_preds[te].tolist(), y[te].tolist())
        print(f"    Fold {fi+1}: r={fold_r:.4f}")
    
    rf_r = pearson_r(rf_preds.tolist(), y.tolist())
    rf_mae_val = mae(rf_preds.tolist(), y.tolist())
    print(f"    Overall CV r = {rf_r:.4f}")
    print(f"    Overall CV MAE = {rf_mae_val:.1f}")
    
    # ── Gradient Boosting ─────────────────────────────────────────────────────
    print("\n[1C] Gradient Boosting (50 estimators, lr=0.1)")
    
    gb_preds = np.zeros(n)
    for fi, (tr, te) in enumerate(folds):
        gb = SimpleGradientBoost(n_estimators=50, learning_rate=0.1, max_depth=2, seed=fi)
        gb.fit(X_norm[tr], y[tr])
        gb_preds[te] = gb.predict(X_norm[te])
        fold_r = pearson_r(gb_preds[te].tolist(), y[te].tolist())
        print(f"    Fold {fi+1}: r={fold_r:.4f}")
    
    gb_r = pearson_r(gb_preds.tolist(), y.tolist())
    gb_mae_val = mae(gb_preds.tolist(), y.tolist())
    print(f"    Overall CV r = {gb_r:.4f}")
    print(f"    Overall CV MAE = {gb_mae_val:.1f}")
    
    # ── Random Forest with set-based features ─────────────────────────────────
    print("\n[1D] Random Forest with set-based features (Jaccard etc.)")
    
    X_set = np.array(set_features)
    set_preds = np.zeros(n)
    for fi, (tr, te) in enumerate(folds):
        rf = SimpleRandomForest(n_trees=100, max_depth=3, seed=fi)
        rf.fit(X_set[tr], y[tr])
        set_preds[te] = rf.predict(X_set[te])
        fold_r = pearson_r(set_preds[te].tolist(), y[te].tolist())
        print(f"    Fold {fi+1}: r={fold_r:.4f}")
    
    set_r = pearson_r(set_preds.tolist(), y.tolist())
    set_mae_val = mae(set_preds.tolist(), y.tolist())
    print(f"    Overall CV r = {set_r:.4f}")
    print(f"    Overall CV MAE = {set_mae_val:.1f}")
    
    # ── Combined features ─────────────────────────────────────────────────────
    print("\n[1E] Random Forest with ALL features (original + set-based)")
    
    X_all = np.hstack([X_norm, X_set])
    all_preds = np.zeros(n)
    for fi, (tr, te) in enumerate(folds):
        rf = SimpleRandomForest(n_trees=100, max_depth=3, seed=fi)
        rf.fit(X_all[tr], y[tr])
        all_preds[te] = rf.predict(X_all[te])
        fold_r = pearson_r(all_preds[te].tolist(), y[te].tolist())
        print(f"    Fold {fi+1}: r={fold_r:.4f}")
    
    all_r = pearson_r(all_preds.tolist(), y.tolist())
    all_mae_val = mae(all_preds.tolist(), y.tolist())
    print(f"    Overall CV r = {all_r:.4f}")
    print(f"    Overall CV MAE = {all_mae_val:.1f}")
    
    return {
        'set_metrics': dict(zip(set_names, [pearson_r([sf[i] for sf in set_features], y_be) for i in range(len(set_names))])),
        'rf_cv_r': rf_r, 'rf_cv_mae': rf_mae_val,
        'gb_cv_r': gb_r, 'gb_cv_mae': gb_mae_val,
        'set_rf_cv_r': set_r, 'set_rf_cv_mae': set_mae_val,
        'all_rf_cv_r': all_r, 'all_rf_cv_mae': all_mae_val,
    }


# ════════════════════════════════════════════════════════════════════════════════
# DIRECTION 2: BOND AS GEOMETRIC OBJECT + SNAP AS INTERACTION
# ════════════════════════════════════════════════════════════════════════════════

@dataclass
class BondGeometry:
    """A bond as a geometric object in MOG space."""
    # The bond exists BETWEEN two Data Objects
    # It has its own geometry derived from the interaction
    
    # Core geometry
    midpoint: List[int]          # bitwise midpoint (OR of shared bits)
    direction: List[int]         # XOR = direction vector
    length: int                  # Hamming distance
    
    # Snap dynamics of the bond itself
    bond_syndrome: List[int]     # syndrome of the bond vector
    bond_syndrome_weight: int
    bond_snap_bits: int          # how many bits the bond needs to snap
    bond_codeword: List[int]     # the bond after snapping
    
    # The bond as a MOG grid
    mog_midpoint: List[List[int]]  # 4×6 grid of midpoint
    mog_direction: List[List[int]] # 4×6 grid of direction
    
    # Physical properties
    mass_a: float                # Row 0 contribution from A
    mass_b: float                # Row 0 contribution from B
    info_overlap: int            # Row 1 shared bits
    activation_diff: int         # Row 2 differing bits
    potential_complement: int    # Row 3 complementary bits
    
    # The snap as interaction mechanism
    pre_snap_tax: float          # TAX before snapping the bond
    post_snap_tax: float         # TAX after snapping the bond
    snap_energy: float           # Energy released/absorbed by snap


def compute_bond_geometry(do_a: DataObject, do_b: DataObject, 
                          golay: GolayEngine) -> BondGeometry:
    """Compute the bond as a geometric object."""
    ca, cb = do_a.codeword, do_b.codeword
    
    # Midpoint: the shared structure (AND)
    midpoint = [ca[i] & cb[i] for i in range(24)]
    
    # Direction: the difference (XOR)
    direction = [ca[i] ^ cb[i] for i in range(24)]
    length = sum(direction)
    
    # Snap the bond (midpoint) to see what valid state it maps to
    bond_cw, bond_meta = golay.snap_to_codeword(midpoint)
    bond_syn = golay.syndrome(midpoint)
    bond_syn_weight = sum(bond_syn)
    bond_snap_bits = bond_meta.get('snap_bits', -1)
    
    # MOG grids
    mog_mid = [midpoint[r*6:(r+1)*6] for r in range(4)]
    mog_dir = [direction[r*6:(r+1)*6] for r in range(4)]
    
    # Physical properties per MOG row
    mass_a = sum(ca[0:6])
    mass_b = sum(cb[0:6])
    info_overlap = sum(ca[i] & cb[i] for i in range(6, 12))
    activation_diff = sum(ca[i] ^ cb[i] for i in range(12, 18))
    potential_complement = sum((1 - ca[i]) & cb[i] for i in range(18, 24))
    
    # Snap energy: TAX change when the bond snaps
    pre_hw = sum(midpoint)
    pre_ns = sum(b * b for b in midpoint)
    pre_tax = float(Y_CONST) * pre_hw + pre_ns / 8.0
    
    post_hw = sum(bond_cw)
    post_ns = sum(b * b for b in bond_cw)
    post_tax = float(Y_CONST) * post_hw + post_ns / 8.0
    
    snap_energy = post_tax - pre_tax  # positive = energy absorbed, negative = released
    
    return BondGeometry(
        midpoint=midpoint,
        direction=direction,
        length=length,
        bond_syndrome=bond_syn,
        bond_syndrome_weight=bond_syn_weight,
        bond_snap_bits=bond_snap_bits,
        bond_codeword=bond_cw,
        mog_midpoint=mog_mid,
        mog_direction=mog_dir,
        mass_a=mass_a,
        mass_b=mass_b,
        info_overlap=info_overlap,
        activation_diff=activation_diff,
        potential_complement=potential_complement,
        pre_snap_tax=pre_tax,
        post_snap_tax=post_tax,
        snap_energy=snap_energy,
    )


def run_direction_2(data_objects, pairs_data):
    """Direction 2: Bond as geometric object, snap as interaction mechanism."""
    print("\n" + "=" * 72)
    print("DIRECTION 2: BOND AS GEOMETRIC OBJECT + SNAP AS INTERACTION")
    print("=" * 72)
    
    golay = GolayEngine()
    
    # ── Compute bond geometries ───────────────────────────────────────────────
    print("\n[2A] Computing bond geometries")
    
    bond_features = []
    y_be = [p['be'] for p in pairs_data]
    y_bo = [p['bo'] for p in pairs_data]
    
    for p in pairs_data:
        do_a = data_objects[p['sym_a']]
        do_b = data_objects[p['sym_b']]
        bg = compute_bond_geometry(do_a, do_b, golay)
        
        bond_features.append([
            bg.length,                    # bond length (Hamming distance)
            bg.bond_syndrome_weight,      # how far from valid codeword
            bg.bond_snap_bits,            # bits corrected by snap
            bg.snap_energy,               # TAX change from snap
            bg.info_overlap,              # shared Info bits
            bg.activation_diff,           # differing Activation bits
            bg.potential_complement,      # complementary Potential bits
            bg.mass_a + bg.mass_b,        # combined mass
            abs(bg.mass_a - bg.mass_b),   # mass asymmetry
            bg.pre_snap_tax,              # bond pre-snap TAX
            bg.post_snap_tax,             # bond post-snap TAX
        ])
    
    bond_names = ['length', 'syn_weight', 'snap_bits', 'snap_energy',
                  'info_overlap', 'act_diff', 'pot_complement',
                  'combined_mass', 'mass_asymmetry', 'pre_tax', 'post_tax']
    
    print(f"    Bond features computed for {len(bond_features)} pairs")
    
    # ── Feature correlations ──────────────────────────────────────────────────
    print(f"\n[2B] Bond geometry correlations with bond energy:")
    for i, name in enumerate(bond_names):
        vals = [bf[i] for bf in bond_features]
        r = pearson_r(vals, y_be)
        bar = "█" * min(int(abs(r) * 30), 30)
        print(f"      {name:<18} r={r:>7.4f}  {bar}")
    
    print(f"\n    Bond geometry correlations with bond order:")
    for i, name in enumerate(bond_names):
        vals = [bf[i] for bf in bond_features]
        r = pearson_r(vals, y_bo)
        bar = "█" * min(int(abs(r) * 30), 30)
        print(f"      {name:<18} r={r:>7.4f}  {bar}")
    
    # ── Bond as predictor ─────────────────────────────────────────────────────
    print(f"\n[2C] Bond geometry as predictor (Random Forest, 5-fold CV)")
    
    X_bond = np.array(bond_features)
    y = np.array(y_be)
    
    # Normalize
    X_mean = X_bond.mean(axis=0)
    X_std = X_bond.std(axis=0)
    X_std[X_std == 0] = 1
    X_norm = (X_bond - X_mean) / X_std
    
    folds = k_fold_split(len(y_be), k=5, seed=42)
    bond_preds = np.zeros(len(y_be))
    
    for fi, (tr, te) in enumerate(folds):
        rf = SimpleRandomForest(n_trees=100, max_depth=3, seed=fi)
        rf.fit(X_norm[tr], y[tr])
        bond_preds[te] = rf.predict(X_norm[te])
        fold_r = pearson_r(bond_preds[te].tolist(), y[te].tolist())
        print(f"      Fold {fi+1}: r={fold_r:.4f}")
    
    bond_r = pearson_r(bond_preds.tolist(), y.tolist())
    bond_mae_val = mae(bond_preds.tolist(), y.tolist())
    print(f"      Overall CV r = {bond_r:.4f}")
    print(f"      Overall CV MAE = {bond_mae_val:.1f}")
    
    # ── Snap energy analysis ──────────────────────────────────────────────────
    print(f"\n[2D] Snap energy analysis")
    print(f"    Does the snap process release/absorb energy differently for different bond types?")
    
    # Group by bond order
    bo_groups = defaultdict(list)
    for i, p in enumerate(pairs_data):
        bo_groups[p['bo']].append(i)
    
    for bo in sorted(bo_groups.keys()):
        indices = bo_groups[bo]
        snap_energies = [bond_features[i][3] for i in indices]  # snap_energy
        mean_se = sum(snap_energies) / len(snap_energies)
        print(f"      BO={bo}: mean snap_energy = {mean_se:+.4f} (n={len(indices)})")
    
    # ── Show sample bond geometries ───────────────────────────────────────────
    print(f"\n[2E] Sample bond geometries")
    print(f"    {'Pair':<20} {'BO':>3} {'Length':>6} {'SynW':>5} {'Snap':>5} "
          f"{'SnapE':>7} {'InfoO':>5} {'ActD':>5} {'PotC':>5}")
    print(f"    {'-'*70}")
    
    for i in range(min(20, len(pairs_data))):
        p = pairs_data[i]
        bf = bond_features[i]
        print(f"    {p['label']:<20} {p['bo']:>3} {bf[0]:>6.0f} {bf[1]:>5.0f} "
              f"{bf[2]:>5.0f} {bf[3]:>7.4f} {bf[4]:>5.0f} {bf[5]:>5.0f} {bf[6]:>5.0f}")
    
    return {
        'bond_feature_names': bond_names,
        'bond_feature_correlations_be': dict(zip(bond_names, 
            [pearson_r([bf[i] for bf in bond_features], y_be) for i in range(len(bond_names))])),
        'bond_feature_correlations_bo': dict(zip(bond_names,
            [pearson_r([bf[i] for bf in bond_features], y_bo) for i in range(len(bond_names))])),
        'bond_rf_cv_r': bond_r,
        'bond_rf_cv_mae': bond_mae_val,
    }


# ════════════════════════════════════════════════════════════════════════════════
# DIRECTION 3: UNDERSTANDING TESTS BEYOND INTERACTIONS
# ════════════════════════════════════════════════════════════════════════════════

def run_direction_3(data_objects, elements):
    """Direction 3: Does the GLM 'understand' elements beyond interactions?"""
    print("\n" + "=" * 72)
    print("DIRECTION 3: UNDERSTANDING TESTS BEYOND INTERACTIONS")
    print("=" * 72)
    
    # ── Test 1: Can the encoding cluster elements by group? ───────────────────
    print("\n[3A] Element clustering — do Data Objects group by chemistry?")
    
    # Assign groups
    group_map = {
        'H': 'nonmetal', 'He': 'noble', 'Li': 'alkali', 'Be': 'alkaline',
        'B': 'metalloid', 'C': 'nonmetal', 'N': 'nonmetal', 'O': 'nonmetal',
        'F': 'halogen', 'Ne': 'noble', 'Na': 'alkali', 'Mg': 'alkaline',
        'Al': 'post_transition', 'Si': 'metalloid', 'P': 'nonmetal',
        'S': 'nonmetal', 'Cl': 'halogen', 'Ar': 'noble', 'K': 'alkali',
        'Ca': 'alkaline', 'Sc': 'transition', 'Ti': 'transition',
        'V': 'transition', 'Cr': 'transition', 'Mn': 'transition',
        'Fe': 'transition', 'Co': 'transition', 'Ni': 'transition',
        'Cu': 'transition', 'Zn': 'transition', 'Ga': 'post_transition',
        'Ge': 'metalloid', 'As': 'metalloid', 'Se': 'nonmetal',
        'Br': 'halogen', 'Kr': 'noble', 'Rb': 'alkali', 'Sr': 'alkaline',
        'Ag': 'transition', 'I': 'halogen', 'Ba': 'alkaline',
        'Au': 'transition', 'Pt': 'transition', 'Pb': 'post_transition',
    }
    
    # For each element, find its nearest neighbours
    elem_syms = [s for s in data_objects if s in group_map]
    elem_vectors = [data_objects[s].codeword for s in elem_syms]
    elem_groups = [group_map[s] for s in elem_syms]
    
    # Compute pairwise Hamming distances
    n_elem = len(elem_syms)
    dist_matrix = np.zeros((n_elem, n_elem))
    for i in range(n_elem):
        for j in range(n_elem):
            dist_matrix[i, j] = sum(elem_vectors[i][k] ^ elem_vectors[j][k] for k in range(24))
    
    # For each element, find k nearest neighbours
    k = 3
    correct_cluster = 0
    total_cluster = 0
    
    for i in range(n_elem):
        dists = [(dist_matrix[i, j], j) for j in range(n_elem) if j != i]
        dists.sort()
        neighbors = dists[:k]
        
        same_group = sum(1 for _, j in neighbors if elem_groups[j] == elem_groups[i])
        if same_group >= k // 2:
            correct_cluster += 1
        total_cluster += 1
    
    cluster_accuracy = correct_cluster / total_cluster
    print(f"    k-NN clustering accuracy (k={k}): {correct_cluster}/{total_cluster} = {cluster_accuracy:.1%}")
    
    # Group-level analysis
    print(f"\n    Group centroids (mean HW):")
    groups = defaultdict(list)
    for i, sym in enumerate(elem_syms):
        groups[elem_groups[i]].append(i)
    
    for group, indices in sorted(groups.items()):
        mean_hw = sum(data_objects[elem_syms[i]].hamming_weight for i in indices) / len(indices)
        mean_nrci = sum(float(data_objects[elem_syms[i]].nrci()) for i in indices) / len(indices)
        print(f"      {group:<18} n={len(indices):2d}  mean_HW={mean_hw:.1f}  mean_NRCI={mean_nrci:.4f}")
    
    # ── Test 2: Can we predict element properties from Data Object? ───────────
    print(f"\n[3B] Property prediction from Data Object encoding")
    
    # For each element with known properties, can we predict Z, EN, BP, etc.
    # from the codeword?
    prop_names = ['Z', 'EN', 'BP', 'MP', 'Rho']
    
    for prop in prop_names:
        X_prop = []
        y_prop = []
        for sym in elem_syms:
            elem = elements[sym]
            val = elem['properties'].get(prop)
            if val is not None:
                X_prop.append(data_objects[sym].codeword)
                y_prop.append(float(val))
        
        if len(y_prop) < 10:
            continue
        
        X_arr = np.array(X_prop, dtype=float)
        y_arr = np.array(y_prop)
        
        # Simple linear regression
        ones = np.ones((len(X_arr), 1))
        X_aug = np.hstack([ones, X_arr])
        try:
            w = np.linalg.lstsq(X_aug, y_arr, rcond=None)[0]
            preds = X_aug @ w
            r = pearson_r(preds.tolist(), y_arr.tolist())
            print(f"      {prop:<8} n={len(y_prop):3d}  r={r:.4f}")
        except:
            print(f"      {prop:<8} n={len(y_prop):3d}  FAILED")
    
    # ── Test 3: Can the system predict which elements form compounds? ─────────
    print(f"\n[3C] Compound formation prediction")
    
    # Known compounds: which element pairs form stable compounds?
    compound_formers = [
        ('H', 'O', True), ('H', 'Cl', True), ('Na', 'Cl', True),
        ('Fe', 'O', True), ('Ca', 'O', True), ('Mg', 'O', True),
        ('Si', 'O', True), ('Al', 'O', True), ('C', 'O', True),
        ('N', 'O', True), ('S', 'O', True), ('P', 'O', True),
        ('Li', 'F', True), ('Na', 'F', True), ('K', 'Cl', True),
        # Non-compounds (pairs that don't form stable compounds under normal conditions)
        ('He', 'Ne', False), ('He', 'Ar', False), ('Ne', 'Ar', False),
        ('He', 'O', False), ('Ne', 'O', False), ('Ar', 'O', False),
        ('He', 'H', False), ('Ne', 'H', False), ('Ar', 'H', False),
    ]
    
    # Use AND NRCI as predictor
    correct = 0
    total = 0
    threshold = 0.85  # above this NRCI = compound
    
    for sym_a, sym_b, forms_compound in compound_formers:
        if sym_a not in data_objects or sym_b not in data_objects:
            continue
        do_a = data_objects[sym_a]
        do_b = data_objects[sym_b]
        result = interact(do_a, do_b)
        
        predicted_compound = result.and_nrci > threshold
        if predicted_compound == forms_compound:
            correct += 1
        total += 1
    
    print(f"    Compound formation (AND_NRCI > {threshold}): {correct}/{total} = {correct/total:.1%}")
    
    # Try different thresholds
    print(f"\n    Threshold sweep:")
    for thresh in [0.70, 0.75, 0.80, 0.85, 0.90, 0.95]:
        c = 0
        for sym_a, sym_b, forms in compound_formers:
            if sym_a not in data_objects or sym_b not in data_objects:
                continue
            result = interact(data_objects[sym_a], data_objects[sym_b])
            if (result.and_nrci > thresh) == forms:
                c += 1
        print(f"      threshold={thresh:.2f}  accuracy={c}/{total} = {c/total:.1%}")
    
    # ── Test 4: Noble gas detection ───────────────────────────────────────────
    print(f"\n[3D] Noble gas detection (vacuum state)")
    
    noble_gases = {'He', 'Ne', 'Ar', 'Kr', 'Xe'}
    non_noble = set(elem_syms) - noble_gases
    
    # Noble gases should have HW=0 or very low
    noble_detected = 0
    for sym in noble_gases:
        if sym in data_objects:
            do = data_objects[sym]
            if do.hamming_weight <= 2:  # low HW = noble
                noble_detected += 1
    
    false_positives = 0
    for sym in non_noble:
        do = data_objects[sym]
        if do.hamming_weight <= 2:
            false_positives += 1
    
    print(f"    Noble gases detected: {noble_detected}/{len(noble_gases & set(data_objects.keys()))}")
    print(f"    False positives: {false_positives}/{len(non_noble)}")
    
    return {
        'cluster_accuracy': cluster_accuracy,
        'compound_accuracy': correct / total if total > 0 else 0,
        'noble_detected': noble_detected,
    }


# ════════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════════

def run_all():
    """Run all three directions."""
    import numpy as np
    
    # Load data
    kb_path = Path(__file__).resolve().parent.parent.parent / "long_term_memory" / "ubp_system_kb.json"
    if not kb_path.exists():
        kb_path = Path("/home/work/.openclaw/workspace/GLM/long_term_memory/ubp_system_kb.json")
    
    print("Loading elements...")
    elements = load_elements_from_kb(str(kb_path))
    golay = GolayEngine()
    spatial = MOGSpatialArithmetic(golay)
    
    data_objects = {}
    for sym in elements:
        do = encode_element(sym, elements, BEST_ENCODING, golay)
        if do:
            data_objects[sym] = do
    
    # Build pairs
    pairs_data = []
    for sym_a, sym_b, be, dh, label, bo in EXPANDED_PAIRS:
        if sym_a not in data_objects or sym_b not in data_objects:
            continue
        do_a, do_b = data_objects[sym_a], data_objects[sym_b]
        result = interact(do_a, do_b)
        primitives = spatial.full_interaction(do_a, do_b)
        
        features = [
            result.and_nrci, result.xor_nrci, result.delta_nrci,
            result.and_hw, result.xor_hw, result.hamming_distance,
            primitives['gravitic'], primitives['electrostatic'],
            primitives['confinement'], primitives['cymatic']['net_score'],
            do_a.hamming_weight, do_b.hamming_weight,
        ]
        pairs_data.append({
            'sym_a': sym_a, 'sym_b': sym_b,
            'be': be, 'dh': dh, 'label': label, 'bo': bo,
            'features': features,
        })
    
    # Run directions
    r1 = run_direction_1(data_objects, pairs_data)
    r2 = run_direction_2(data_objects, pairs_data)
    r3 = run_direction_3(data_objects, elements)
    
    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("THREE DIRECTIONS — SUMMARY")
    print("=" * 72)
    
    print(f"\n  Direction 1: Nonlinear Predictors")
    print(f"    Set-based metrics best:    {max(r1['set_metrics'].items(), key=lambda x: abs(x[1]))}")
    print(f"    Random Forest CV r:        {r1['rf_cv_r']:.4f}")
    print(f"    Gradient Boosting CV r:    {r1['gb_cv_r']:.4f}")
    print(f"    Set-based RF CV r:         {r1['set_rf_cv_r']:.4f}")
    print(f"    All features RF CV r:      {r1['all_rf_cv_r']:.4f}")
    
    print(f"\n  Direction 2: Bond as Geometric Object")
    print(f"    Bond geometry RF CV r:     {r2['bond_rf_cv_r']:.4f}")
    best_bond = max(r2['bond_feature_correlations_be'].items(), key=lambda x: abs(x[1]))
    print(f"    Best bond feature (BE):    {best_bond[0]} (r={best_bond[1]:.4f})")
    best_bond_bo = max(r2['bond_feature_correlations_bo'].items(), key=lambda x: abs(x[1]))
    print(f"    Best bond feature (BO):    {best_bond_bo[0]} (r={best_bond_bo[1]:.4f})")
    
    print(f"\n  Direction 3: Understanding Beyond Interactions")
    print(f"    Element clustering:        {r3['cluster_accuracy']:.1%}")
    print(f"    Compound formation:        {r3['compound_accuracy']:.1%}")
    print(f"    Noble gas detection:       {r3['noble_detected']}/5")
    
    # Save
    results = {
        'date': datetime.now().isoformat(),
        'direction_1': r1,
        'direction_2': {k: v for k, v in r2.items() if k != 'bond_feature_names'},
        'direction_3': r3,
    }
    save_path = SCRIPT_DIR.parent / "data" / f"three_directions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(save_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results saved to: {save_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--direction", type=int, choices=[1, 2, 3])
    args = parser.parse_args()
    
    if args.all or args.direction:
        run_all()
    else:
        parser.print_help()
