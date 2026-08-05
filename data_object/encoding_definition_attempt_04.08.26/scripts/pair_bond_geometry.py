#!/usr/bin/env python3
"""
Pair-Bond Geometry + Evolutionary Seeds
========================================
Experiment: encoding_definition_attempt_04.08-26

Implements the feedback:
1. Bond as geometric object (midpoint/direction/snap)
2. Bond order warping of Leech space
3. Nonlinear geometric primitives (cross-terms, triple products)
4. Evolutionary seed selection for settlement dynamics

Usage:
  python3 pair_bond_geometry.py --full-test
  python3 python3 pair_bond_geometry.py --evolve --seeds 50
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
    EXPANDED_PAIRS, compute_snap_dynamics,
    pearson_r, mae, k_fold_split,
)

import numpy as np


# ════════════════════════════════════════════════════════════════════════════════
# 1. PAIR-BOND GEOMETRY
# ════════════════════════════════════════════════════════════════════════════════

class PairBondGeometry:
    """
    A bond as a geometric object in 24D Leech space.
    
    The bond exists BETWEEN two Data Objects. It has:
    - Midpoint: the shared structure (AND of codewords)
    - Direction: the difference (XOR of codewords)
    - Length: Hamming distance
    - Snap dynamics: how the bond snaps to valid Golay state
    - MOG decomposition: per-row analysis
    
    The bond is NOT just a scalar — it's a geometric entity with
    position, direction, and dynamics.
    """
    
    def __init__(self, do_a: DataObject, do_b: DataObject, golay: GolayEngine):
        ca, cb = do_a.codeword, do_b.codeword
        
        # Core geometry
        self.midpoint = [ca[i] & cb[i] for i in range(24)]
        self.direction = [ca[i] ^ cb[i] for i in range(24)]
        self.length = sum(self.direction)
        
        # Snap the bond (midpoint)
        self.bond_cw, self.bond_meta = golay.snap_to_codeword(self.midpoint)
        self.bond_syndrome = golay.syndrome(self.midpoint)
        self.bond_syn_weight = sum(self.bond_syndrome)
        self.bond_snap_bits = self.bond_meta.get('snap_bits', -1)
        
        # MOG decomposition (4 rows × 6 cols)
        self.mog_mid = [self.midpoint[r*6:(r+1)*6] for r in range(4)]
        self.mog_dir = [self.direction[r*6:(r+1)*6] for r in range(4)]
        
        # Per-row metrics
        self.row_overlap = [sum(ca[r*6:(r+1)*6][i] & cb[r*6:(r+1)*6][i] for i in range(6)) for r in range(4)]
        self.row_diff = [sum(ca[r*6:(r+1)*6][i] ^ cb[r*6:(r+1)*6][i] for i in range(6)) for r in range(4)]
        
        # Snap energy
        pre_hw = sum(self.midpoint)
        pre_ns = sum(b*b for b in self.midpoint)
        self.pre_snap_tax = float(Y_CONST) * pre_hw + pre_ns / 8.0
        
        post_hw = sum(self.bond_cw)
        post_ns = sum(b*b for b in self.bond_cw)
        self.post_snap_tax = float(Y_CONST) * post_hw + post_ns / 8.0
        
        self.snap_energy = self.post_snap_tax - self.pre_snap_tax
        
        # Element-level properties
        self.hw_a = do_a.hamming_weight
        self.hw_b = do_b.hamming_weight
        self.nrci_a = float(do_a.nrci())
        self.nrci_b = float(do_b.nrci())
        self.tax_a = float(do_a.tax())
        self.tax_b = float(do_b.tax())
    
    def features(self) -> List[float]:
        """Extract feature vector from bond geometry."""
        return [
            # Snap dynamics (the key signal)
            self.snap_energy,
            self.bond_syn_weight,
            self.bond_snap_bits,
            self.pre_snap_tax,
            self.post_snap_tax,
            # Bond geometry
            self.length,
            sum(self.midpoint),  # shared bits
            # Per-row decomposition
            *self.row_overlap,   # 4 values
            *self.row_diff,      # 4 values
            # Element properties
            self.hw_a,
            self.hw_b,
            self.nrci_a,
            self.nrci_b,
            self.tax_a,
            self.tax_b,
        ]
    
    @staticmethod
    def feature_names() -> List[str]:
        return [
            'snap_energy', 'bond_syn_w', 'bond_snap_bits', 'pre_tax', 'post_tax',
            'length', 'shared_bits',
            'overlap_R', 'overlap_I', 'overlap_A', 'overlap_P',
            'diff_R', 'diff_I', 'diff_A', 'diff_P',
            'hw_a', 'hw_b', 'nrci_a', 'nrci_b', 'tax_a', 'tax_b',
        ]


# ════════════════════════════════════════════════════════════════════════════════
# 2. BOND ORDER WARPING
# ════════════════════════════════════════════════════════════════════════════════

def warp_codeword_by_bond_order(codeword: List[int], bond_order: int, 
                                  golay: GolayEngine) -> List[int]:
    """
    Warp a codeword based on bond order.
    
    The idea: bond order geometrically warps the Leech space coordinates.
    - BO=1: no warp (identity)
    - BO=2: apply Golay generator permutation to columns 2-3
    - BO=3: apply Golay generator permutation to columns 4-5
    
    This ensures O=O and O-O land on DIFFERENT sectors of the 24D lattice.
    """
    if bond_order <= 1:
        return list(codeword)
    
    # Apply column permutation based on bond order
    warped = list(codeword)
    
    # For BO=2: swap columns 2 and 3 in the MOG grid
    if bond_order >= 2:
        for row in range(4):
            base = row * 6
            # Swap bits at positions (base+2) and (base+3)
            warped[base + 2], warped[base + 3] = warped[base + 3], warped[base + 2]
    
    # For BO=3: additionally swap columns 4 and 5
    if bond_order >= 3:
        for row in range(4):
            base = row * 6
            # Swap bits at positions (base+4) and (base+5)
            warped[base + 4], warped[base + 5] = warped[base + 5], warped[base + 4]
    
    # Snap to nearest codeword
    warped_cw, _ = golay.snap_to_codeword(warped)
    return warped_cw


# ════════════════════════════════════════════════════════════════════════════════
# 3. NONLINEAR GEOMETRIC PRIMITIVES
# ════════════════════════════════════════════════════════════════════════════════

def nonlinear_primitives(do_a: DataObject, do_b: DataObject, 
                          bond: PairBondGeometry) -> List[float]:
    """
    Nonlinear geometric primitives including cross-terms.
    
    Inspired by the feedback: incorporate scalar triple products
    and wedge products between element vectors and bond vector.
    """
    ca = np.array(do_a.codeword, dtype=float)
    cb = np.array(do_b.codeword, dtype=float)
    mid = np.array(bond.midpoint, dtype=float)
    direc = np.array(bond.direction, dtype=float)
    
    # Dot products (projections)
    dot_ab = float(np.dot(ca, cb))
    dot_a_mid = float(np.dot(ca, mid))
    dot_b_mid = float(np.dot(cb, mid))
    dot_a_dir = float(np.dot(ca, direc))
    dot_b_dir = float(np.dot(cb, direc))
    
    # Norms
    norm_a = float(np.linalg.norm(ca))
    norm_b = float(np.linalg.norm(cb))
    norm_mid = float(np.linalg.norm(mid))
    norm_dir = float(np.linalg.norm(direc))
    
    # Cross-term: element interaction strength
    cross_strength = dot_ab / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0
    
    # Projection ratios: how much of each element is in the bond
    proj_a = dot_a_mid / norm_a if norm_a > 0 else 0
    proj_b = dot_b_mid / norm_b if norm_b > 0 else 0
    
    # Asymmetry: which element contributes more to the bond
    asymmetry = (proj_a - proj_b) / (proj_a + proj_b) if (proj_a + proj_b) > 0 else 0
    
    # Direction alignment: do the elements align or oppose along the bond direction?
    dir_alignment = dot_a_dir * dot_b_dir  # positive = same direction, negative = opposite
    
    # "Triple product" proxy: volume of the parallelepiped formed by a, b, and bond direction
    # For 24D vectors, we use the determinant of the Gram matrix
    # Simplified: ||a|| * ||b|| * ||dir|| * sin(angles)
    triple_proxy = norm_a * norm_b * norm_dir * abs(cross_strength)
    
    # Bond "stiffness": how much the bond resists perturbation
    # Related to how far the bond midpoint is from a valid codeword
    stiffness = bond.bond_syn_weight / max(bond.length, 1)
    
    # Snap "depth": how much the bond changes when it snaps
    snap_depth = abs(bond.snap_energy) * bond.bond_snap_bits if bond.bond_snap_bits > 0 else 0
    
    return [
        cross_strength,
        proj_a,
        proj_b,
        asymmetry,
        dir_alignment,
        triple_proxy,
        stiffness,
        snap_depth,
        dot_ab,
        norm_a * norm_b,  # "mass" product
    ]


def nonlinear_feature_names() -> List[str]:
    return [
        'cross_strength', 'proj_a', 'proj_b', 'asymmetry',
        'dir_alignment', 'triple_proxy', 'stiffness', 'snap_depth',
        'dot_ab', 'mass_product',
    ]


# ════════════════════════════════════════════════════════════════════════════════
# 4. EVOLUTIONARY SEED SELECTION
# ════════════════════════════════════════════════════════════════════════════════

class EvolutionarySeedSelector:
    """
    Genetic algorithm wrapper for settlement dynamics.
    
    1. Spin up N random seeds (perception-weight vectors)
    2. Evaluate each over a short training window
    3. Select top K%
    4. Breed (crossover + mutation)
    5. Repeat
    """
    
    def __init__(self, n_features: int, population_size: int = 50,
                 top_k: float = 0.1, mutation_rate: float = 0.1,
                 seed: int = 42):
        self.n_feat = n_features
        self.pop_size = population_size
        self.top_k = max(1, int(population_size * top_k))
        self.mutation_rate = mutation_rate
        self.rng = random.Random(seed)
        
        # Initialize population: each individual is a weight vector
        self.population = []
        for _ in range(population_size):
            weights = [self.rng.uniform(0.1, 2.0) for _ in range(n_features)]
            self.population.append(weights)
    
    def evaluate_individual(self, weights: List[float], 
                            train_data: List[Dict]) -> float:
        """Evaluate one weight vector using k-NN on training data."""
        n = len(train_data)
        n_feat = len(weights)
        
        # Apply weights to features
        weighted = []
        for d in train_data:
            wf = [d['norm'][i] * weights[i] for i in range(n_feat)]
            weighted.append(wf)
        
        # LOO accuracy on training data
        correct = 0
        for i in range(min(n, 30)):  # subsample for speed
            test = weighted[i]
            dists = []
            for j in range(n):
                if j == i:
                    continue
                d = math.sqrt(sum((test[k] - weighted[j][k])**2 for k in range(n_feat)))
                dists.append((d, train_data[j]['bo']))
            dists.sort()
            
            # k=3 vote
            votes = {}
            for dist, bo in dists[:3]:
                w = 1.0 / max(dist, 0.001)
                votes[bo] = votes.get(bo, 0) + w
            pred = max(votes, key=votes.get)
            if pred == train_data[i]['bo']:
                correct += 1
        
        return correct / min(n, 30)
    
    def evolve(self, train_data: List[Dict], generations: int = 20) -> Tuple[List[float], float]:
        """Run the evolutionary algorithm."""
        best_weights = None
        best_fitness = 0
        
        for gen in range(generations):
            # Evaluate all individuals
            fitness = []
            for weights in self.population:
                f = self.evaluate_individual(weights, train_data)
                fitness.append(f)
            
            # Find best
            gen_best_idx = max(range(len(fitness)), key=lambda i: fitness[i])
            if fitness[gen_best_idx] > best_fitness:
                best_fitness = fitness[gen_best_idx]
                best_weights = self.population[gen_best_idx][:]
            
            # Select top K
            sorted_indices = sorted(range(len(fitness)), key=lambda i: fitness[i], reverse=True)
            survivors = [self.population[i] for i in sorted_indices[:self.top_k]]
            
            # Breed next generation
            new_pop = list(survivors)  # keep survivors
            while len(new_pop) < self.pop_size:
                # Crossover: pick two parents
                p1 = self.rng.choice(survivors)
                p2 = self.rng.choice(survivors)
                child = []
                for i in range(self.n_feat):
                    # Crossover
                    if self.rng.random() < 0.5:
                        child.append(p1[i])
                    else:
                        child.append(p2[i])
                    # Mutation
                    if self.rng.random() < self.mutation_rate:
                        child[i] += self.rng.gauss(0, 0.3)
                        child[i] = max(0.01, child[i])
                new_pop.append(child)
            
            self.population = new_pop
            
            if gen % 5 == 0:
                print(f"    Gen {gen:3d}: best_acc={best_fitness:.1%}  "
                      f"mean_acc={sum(fitness)/len(fitness):.1%}")
        
        return best_weights, best_fitness


# ════════════════════════════════════════════════════════════════════════════════
# 5. FULL TEST
# ════════════════════════════════════════════════════════════════════════════════

def run_full_test():
    """Run the complete pair-bond geometry test."""
    print("=" * 72)
    print("PAIR-BOND GEOMETRY + EVOLUTIONARY SEEDS")
    print("=" * 72)
    
    # Load
    kb_path = Path(__file__).resolve().parent.parent.parent / "long_term_memory" / "ubp_system_kb.json"
    if not kb_path.exists():
        kb_path = Path("/home/work/.openclaw/workspace/GLM/long_term_memory/ubp_system_kb.json")
    
    print(f"\n[1] Loading elements")
    elements = load_elements_from_kb(str(kb_path))
    golay = GolayEngine()
    spatial = MOGSpatialArithmetic(golay)
    
    data_objects = {}
    for sym in elements:
        do = encode_element(sym, elements, BEST_ENCODING, golay)
        if do:
            data_objects[sym] = do
    print(f"    Encoded {len(data_objects)} elements")
    
    # ── Build bond geometries ─────────────────────────────────────────────────
    print(f"\n[2] Building pair-bond geometries")
    
    bonds = []
    y_be = []
    y_bo = []
    labels = []
    
    for sym_a, sym_b, be, dh, label, bo in EXPANDED_PAIRS:
        if sym_a not in data_objects or sym_b not in data_objects:
            continue
        do_a, do_b = data_objects[sym_a], data_objects[sym_b]
        
        bond = PairBondGeometry(do_a, do_b, golay)
        nl_prims = nonlinear_primitives(do_a, do_b, bond)
        
        # Combined features: bond geometry + nonlinear primitives
        combined = bond.features() + nl_prims
        
        bonds.append({
            'sym_a': sym_a, 'sym_b': sym_b,
            'be': be, 'bo': bo, 'label': label,
            'bond': bond,
            'features': combined,
        })
        y_be.append(be)
        y_bo.append(bo)
        labels.append(label)
    
    n = len(bonds)
    n_feat = len(bonds[0]['features'])
    all_names = PairBondGeometry.feature_names() + nonlinear_feature_names()
    
    print(f"    Pairs: {n}, Features: {n_feat}")
    
    # Normalize
    all_f = [b['features'] for b in bonds]
    means = [sum(f[i] for f in all_f)/n for i in range(n_feat)]
    stds = [math.sqrt(sum((f[i]-means[i])**2 for f in all_f)/n) for i in range(n_feat)]
    stds = [max(s, 1e-10) for s in stds]
    for b in bonds:
        b['norm'] = [(b['features'][i]-means[i])/stds[i] for i in range(n_feat)]
    
    # ── Feature correlations ──────────────────────────────────────────────────
    print(f"\n[3] Feature correlations")
    
    print(f"\n    With bond energy:")
    for i, name in enumerate(all_names):
        vals = [b['features'][i] for b in bonds]
        r = pearson_r(vals, y_be)
        if abs(r) > 0.1:
            bar = "█" * min(int(abs(r) * 30), 30)
            print(f"      {name:<20} r={r:>7.4f}  {bar}")
    
    print(f"\n    With bond order:")
    for i, name in enumerate(all_names):
        vals = [b['features'][i] for b in bonds]
        r = pearson_r(vals, y_bo)
        if abs(r) > 0.1:
            bar = "█" * min(int(abs(r) * 30), 30)
            print(f"      {name:<20} r={r:>7.4f}  {bar}")
    
    # ── Bond order classification ─────────────────────────────────────────────
    print(f"\n[4] Bond order classification (LOO k-NN)")
    
    correct = 0
    for i in range(n):
        test = bonds[i]
        train = bonds[:i] + bonds[i+1:]
        
        dists = []
        for t in train:
            d = math.sqrt(sum((test['norm'][j] - t['norm'][j])**2 for j in range(n_feat)))
            dists.append((d, t['bo']))
        dists.sort()
        
        votes = {}
        for dist, bo in dists[:5]:
            w = 1.0 / max(dist, 0.001)
            votes[bo] = votes.get(bo, 0) + w
        pred = max(votes, key=votes.get)
        if pred == test['bo']:
            correct += 1
    
    print(f"    k-NN (k=5) LOO: {correct}/{n} = {correct/n:.1%}")
    
    # ── Bond energy prediction ────────────────────────────────────────────────
    print(f"\n[5] Bond energy prediction (Random Forest, 5-fold CV)")
    
    X = np.array([b['norm'] for b in bonds])
    y = np.array(y_be)
    
    folds = k_fold_split(n, k=5, seed=42)
    rf_preds = np.zeros(n)
    
    for fi, (tr, te) in enumerate(folds):
        # Simple random forest
        from three_directions import SimpleRandomForest
        rf = SimpleRandomForest(n_trees=100, max_depth=3, seed=fi)
        rf.fit(X[tr], y[tr])
        rf_preds[te] = rf.predict(X[te])
        fold_r = pearson_r(rf_preds[te].tolist(), y[te].tolist())
        print(f"    Fold {fi+1}: r={fold_r:.4f}")
    
    rf_r = pearson_r(rf_preds.tolist(), y.tolist())
    rf_mae_val = mae(rf_preds.tolist(), y.tolist())
    print(f"    Overall CV r = {rf_r:.4f}")
    print(f"    Overall CV MAE = {rf_mae_val:.1f}")
    
    # ── Bond energy with warped codewords ─────────────────────────────────────
    print(f"\n[6] Bond energy with warped codewords (bond order warping)")
    
    # Build warped features
    warped_bonds = []
    for sym_a, sym_b, be, dh, label, bo in EXPANDED_PAIRS:
        if sym_a not in data_objects or sym_b not in data_objects:
            continue
        do_a, do_b = data_objects[sym_a], data_objects[sym_b]
        
        # Warp element B's codeword by bond order
        warped_cb = warp_codeword_by_bond_order(do_b.codeword, int(bo), golay)
        
        # Create warped Data Object
        warped_do_b = DataObject(
            symbol=do_b.symbol,
            raw_bits=do_b.raw_bits,
            codeword=warped_cb,
            snap_meta=do_b.snap_meta,
            properties=do_b.properties,
            encoding_spec=do_b.encoding_spec,
        )
        
        # Compute bond geometry with warped codeword
        warped_bond = PairBondGeometry(do_a, warped_do_b, golay)
        warped_nl = nonlinear_primitives(do_a, warped_do_b, warped_bond)
        warped_features = warped_bond.features() + warped_nl
        
        warped_bonds.append({
            'features': warped_features,
            'be': be, 'bo': bo,
        })
    
    # Normalize warped features
    wf = [b['features'] for b in warped_bonds]
    wmeans = [sum(f[i] for f in wf)/n for i in range(n_feat)]
    wstds = [math.sqrt(sum((f[i]-wmeans[i])**2 for f in wf)/n) for i in range(n_feat)]
    wstds = [max(s, 1e-10) for s in wstds]
    for b in warped_bonds:
        b['norm'] = [(b['features'][i]-wmeans[i])/wstds[i] for i in range(n_feat)]
    
    X_w = np.array([b['norm'] for b in warped_bonds])
    warped_preds = np.zeros(n)
    
    for fi, (tr, te) in enumerate(folds):
        from three_directions import SimpleRandomForest
        rf = SimpleRandomForest(n_trees=100, max_depth=3, seed=fi)
        rf.fit(X_w[tr], y[tr])
        warped_preds[te] = rf.predict(X_w[te])
        fold_r = pearson_r(warped_preds[te].tolist(), y[te].tolist())
        print(f"    Fold {fi+1}: r={fold_r:.4f}")
    
    warped_r = pearson_r(warped_preds.tolist(), y.tolist())
    warped_mae_val = mae(warped_preds.tolist(), y.tolist())
    print(f"    Overall CV r = {warped_r:.4f}")
    print(f"    Overall CV MAE = {warped_mae_val:.1f}")
    
    # ── Evolutionary seed selection ───────────────────────────────────────────
    print(f"\n[7] Evolutionary seed selection (50 seeds, 20 generations)")
    
    evo = EvolutionarySeedSelector(
        n_features=n_feat,
        population_size=50,
        top_k=0.1,
        mutation_rate=0.15,
        seed=42,
    )
    
    best_weights, best_acc = evo.evolve(bonds, generations=20)
    print(f"\n    Best fitness (BO classification): {best_acc:.1%}")
    print(f"    Best weights (top 5):")
    weight_importance = list(zip(all_names, best_weights))
    weight_importance.sort(key=lambda x: x[1], reverse=True)
    for name, w in weight_importance[:10]:
        bar = "█" * min(int(w * 5), 30)
        print(f"      {name:<20} {w:.3f}  {bar}")
    
    # Use evolved weights for k-NN bond energy prediction
    print(f"\n    Evolved weights for BE prediction (LOO k-NN):")
    be_preds_evo = []
    be_actuals_evo = []
    for i in range(n):
        test = bonds[i]
        train = bonds[:i] + bonds[i+1:]
        
        dists = []
        for t in train:
            d = sum(best_weights[j] * (test['norm'][j] - t['norm'][j])**2 
                   for j in range(n_feat))
            d = math.sqrt(max(d, 0))
            dists.append((d, t['be']))
        dists.sort()
        
        pred = sum(be for _, be in dists[:5]) / 5
        be_preds_evo.append(pred)
        be_actuals_evo.append(test['be'])
    
    evo_r = pearson_r(be_preds_evo, be_actuals_evo)
    evo_mae_val = mae(be_preds_evo, be_actuals_evo)
    print(f"    r = {evo_r:.4f}")
    print(f"    MAE = {evo_mae_val:.1f}")
    
    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*72}")
    print("PAIR-BOND GEOMETRY SUMMARY")
    print(f"{'='*72}")
    print(f"  Bond order classification (k-NN): {correct/n:.1%}")
    print(f"  Bond energy (RF, original):       r = {rf_r:.4f}")
    print(f"  Bond energy (RF, warped):         r = {warped_r:.4f}")
    print(f"  Bond energy (evolved k-NN):       r = {evo_r:.4f}")
    print(f"  Evolutionary best BO accuracy:    {best_acc:.1%}")
    print()
    
    if warped_r > rf_r:
        print(f"  ✓ Bond order warping IMPROVES prediction (+{warped_r-rf_r:.4f})")
    else:
        print(f"  ✗ Bond order warping does not improve (Δ={warped_r-rf_r:+.4f})")
    
    if evo_r > 0.3:
        print(f"  ✓ Evolved weights show meaningful correlation")
    else:
        print(f"  ✗ Evolved weights weak — features may need rethinking")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-test", action="store_true")
    parser.add_argument("--evolve", action="store_true")
    parser.add_argument("--seeds", type=int, default=50)
    args = parser.parse_args()
    
    if args.full_test or args.evolve:
        run_full_test()
    else:
        parser.print_help()
