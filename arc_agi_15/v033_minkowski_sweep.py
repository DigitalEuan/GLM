"""
v033_minkowski_sweep.py — Vectorized Minkowski distance rule discovery
=====================================================================

Implements the Sense → Abstract → Synthesize pipeline:
1. Compute Minkowski distance fields (p=1, 1.5, 2, inf) for each colour
2. Extract symbolic feature vectors per cell
3. Search for rules that perfectly separate changed cells from unchanged cells
4. Apply discovered rules to test input

Architecture: vectorized tensor fields, not hardcoded loops.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Set, Any
from collections import Counter
import sys, os, signal, math
import numpy as np

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task


class _OpTimeout(Exception):
    pass

def _alarm_handler(s, f):
    raise _OpTimeout()

signal.signal(signal.SIGALRM, _alarm_handler)


# ═══════════════════════════════════════════════════════════════════
# STEP 1: VECTORIZED DISTANCE FIELD COMPUTATION
# ═══════════════════════════════════════════════════════════════════

def compute_minkowski_field(grid_matrix: np.ndarray, target_mask: np.ndarray, 
                            p: float) -> np.ndarray:
    """
    Computes Minkowski p-norm distance field from each cell to nearest target cell.
    p=1: Manhattan, p=2: Euclidean, p=inf: Chebyshev, p=1.5: fractional.
    """
    h, w = grid_matrix.shape
    target_coords = np.argwhere(target_mask)
    
    if len(target_coords) == 0:
        return np.full((h, w), 999.0)
    
    r_mesh, c_mesh = np.indices((h, w))
    coords_mesh = np.stack([r_mesh, c_mesh], axis=-1).astype(float)
    
    # deltas: (H, W, Num_Targets, 2)
    deltas = coords_mesh[:, :, np.newaxis, :] - target_coords[np.newaxis, np.newaxis, :, :]
    abs_deltas = np.abs(deltas)
    
    if p == np.inf:
        # Chebyshev: max of absolute deltas
        dists = np.max(abs_deltas, axis=-1)  # (H, W, Num_Targets)
        field = np.min(dists, axis=-1)        # (H, W)
    elif p == 1:
        # Manhattan: sum of absolute deltas
        dists = np.sum(abs_deltas, axis=-1)
        field = np.min(dists, axis=-1)
    else:
        # Generalized Minkowski
        dists = np.sum(abs_deltas ** p, axis=-1) ** (1.0 / p)
        field = np.min(dists, axis=-1)
    
    return field


def compute_weighted_manhattan_field(grid_matrix: np.ndarray, target_mask: np.ndarray,
                                      row_weight: float, col_weight: float) -> np.ndarray:
    """Weighted Manhattan: w_r*|dr| + w_c*|dc|"""
    h, w = grid_matrix.shape
    target_coords = np.argwhere(target_mask)
    
    if len(target_coords) == 0:
        return np.full((h, w), 999.0)
    
    r_mesh, c_mesh = np.indices((h, w))
    coords_mesh = np.stack([r_mesh, c_mesh], axis=-1).astype(float)
    
    deltas = coords_mesh[:, :, np.newaxis, :] - target_coords[np.newaxis, np.newaxis, :, :]
    abs_deltas = np.abs(deltas)
    
    # Weighted Manhattan
    weighted = abs_deltas[:, :, :, 0] * row_weight + abs_deltas[:, :, :, 1] * col_weight
    field = np.min(weighted, axis=-1)
    
    return field


# ═══════════════════════════════════════════════════════════════════
# STEP 2: FEATURE EXTRACTION
# ═══════════════════════════════════════════════════════════════════

def extract_features(grid: Grid, bg_col: int, target_col: Optional[int] = None) -> Dict[str, np.ndarray]:
    """
    Extract symbolic feature vectors for all cells.
    Returns dict of feature_name → (H, W) array.
    """
    h, w = grid.height, grid.width
    matrix = np.array(grid.cells)
    
    bg_mask = (matrix == bg_col)
    non_bg_mask = ~bg_mask
    
    if target_col is not None:
        target_mask = (matrix == target_col)
    else:
        target_mask = non_bg_mask
    
    features = {
        'color': matrix.astype(float),
        'is_bg': bg_mask.astype(float),
        'row': np.broadcast_to(np.arange(h)[:, np.newaxis], (h, w)).astype(float),
        'col': np.broadcast_to(np.arange(w)[np.newaxis, :], (h, w)).astype(float),
        'row_parity': (np.broadcast_to(np.arange(h)[:, np.newaxis], (h, w)) % 2).astype(float),
        'col_parity': (np.broadcast_to(np.arange(w)[np.newaxis, :], (h, w)) % 2).astype(float),
    }
    
    # Distance fields for multiple p-norms
    for p_val in [1, 1.5, 2, np.inf]:
        key = f'dist_p{p_val}'
        features[key] = compute_minkowski_field(matrix, target_mask, p_val)
        features[f'{key}_int'] = np.round(features[key]).astype(int).astype(float)
        features[f'{key}_parity'] = (np.round(features[key]).astype(int) % 2).astype(float)
    
    # Neighbour counts (4-connected)
    for col in set(np.unique(matrix)):
        col_mask = (matrix == col)
        n_count = np.zeros((h, w))
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            shifted = np.roll(np.roll(col_mask, dr, axis=0), dc, axis=1)
            if dr == -1: shifted[0, :] = False
            if dr == 1: shifted[-1, :] = False
            if dc == -1: shifted[:, 0] = False
            if dc == 1: shifted[:, -1] = False
            n_count += shifted.astype(float)
        features[f'n_{col}_cardinal'] = n_count
    
    # 8-connected neighbour counts
    for col in set(np.unique(matrix)):
        col_mask = (matrix == col)
        n_count = np.zeros((h, w))
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                shifted = np.roll(np.roll(col_mask, dr, axis=0), dc, axis=1)
                if dr == -1: shifted[0, :] = False
                if dr == 1: shifted[-1, :] = False
                if dc == -1: shifted[:, 0] = False
                if dc == 1: shifted[:, -1] = False
                n_count += shifted.astype(float)
        features[f'n_{col}_diag'] = n_count
    
    return features


# ═══════════════════════════════════════════════════════════════════
# STEP 3: RULE DISCOVERY (Truth Table Strategy)
# ═══════════════════════════════════════════════════════════════════

def discover_rule(train_pairs: List[Tuple[Grid, Grid]], 
                  bg_candidates: List[int]) -> Optional[Dict[str, Any]]:
    """
    Search for a rule that perfectly separates changed cells from unchanged cells.
    Uses the truth table strategy: find feature conditions where
    all changed cells satisfy the condition and no unchanged cells do.
    """
    for bg_col in bg_candidates:
        # Collect features and change masks for all train pairs
        all_changed_features = []
        all_unchanged_features = []
        
        valid = True
        for inp, out in train_pairs:
            if inp.height != out.height or inp.width != out.width:
                valid = False
                break
            
            features = extract_features(inp, bg_col)
            change_mask = np.array(inp.cells) != np.array(out.cells)
            
            h, w = inp.height, inp.width
            for feat_name, feat_arr in features.items():
                if len(all_changed_features) <= 0:
                    all_changed_features.append({})
                    all_unchanged_features.append({})
                
            # Gather feature values for changed vs unchanged cells
            for feat_name, feat_arr in features.items():
                if len(all_changed_features) == 0:
                    all_changed_features = [{} for _ in range(len(train_pairs))]
                    all_unchanged_features = [{} for _ in range(len(train_pairs))]
            
            break  # Just check first pair for validity
        
        if not valid:
            continue
        
        # Re-collect properly
        pair_data = []
        for inp, out in train_pairs:
            features = extract_features(inp, bg_col)
            change_mask = np.array(inp.cells) != np.array(out.cells)
            pair_data.append((features, change_mask, inp, out))
        
        # Try single-feature rules
        feature_names = list(pair_data[0][0].keys())
        
        for feat_name in feature_names:
            # For each feature, find values that appear ONLY in changed cells
            changed_vals = set()
            unchanged_vals = set()
            
            all_match = True
            for features, change_mask, _, _ in pair_data:
                feat = features[feat_name]
                # Round to avoid floating point issues
                if feat.dtype == float:
                    feat_rounded = np.round(feat, 2)
                else:
                    feat_rounded = feat
                
                cv = set(feat_rounded[change_mask].flatten())
                uv = set(feat_rounded[~change_mask].flatten())
                changed_vals.update(cv)
                unchanged_vals.update(uv)
            
            # Find values unique to changed cells
            unique_to_changed = changed_vals - unchanged_vals
            
            if unique_to_changed and len(changed_vals) > 0:
                # Check if this rule works for ALL train pairs
                rule_works = True
                for features, change_mask, inp, out in pair_data:
                    feat = features[feat_name]
                    if feat.dtype == float:
                        feat_rounded = np.round(feat, 2)
                    else:
                        feat_rounded = feat
                    
                    # Predict: cells with feature value in unique_to_changed → change
                    predicted_change = np.isin(feat_rounded, list(unique_to_changed))
                    
                    # Check if prediction matches actual changes
                    # We need: predicted_change ⊆ change_mask (no false positives)
                    # AND we want to maximize coverage
                    false_positives = predicted_change & ~change_mask
                    if np.any(false_positives):
                        rule_works = False
                        break
                
                if rule_works:
                    # Determine fill colour
                    fill_method = determine_fill_colour(train_pairs, bg_col, feat_name, unique_to_changed)
                    
                    return {
                        'type': 'single_feature',
                        'bg_col': bg_col,
                        'feature': feat_name,
                        'values': unique_to_changed,
                        'fill_method': fill_method,
                    }
        
        # Try composite rules (feature1 == val1 AND feature2 == val2)
        # Only try distance combinations
        dist_features = [f for f in feature_names if 'dist_p' in f and '_int' in f]
        neighbor_features = [f for f in feature_names if f.startswith('n_') and 'cardinal' in f]
        
        for df in dist_features:
            for nf in neighbor_features:
                for target_dist in [1, 2, 3]:
                    for target_n in [0, 1, 2, 3]:
                        rule_works = True
                        has_true = False
                        
                        for features, change_mask, inp, out in pair_data:
                            dist = np.round(features[df], 0).astype(int)
                            nfeat = features[nf]
                            
                            cond = (dist == target_dist) & (nfeat >= target_n)
                            
                            # Check: cond cells are subset of changed cells
                            false_pos = cond & ~change_mask
                            if np.any(false_pos):
                                rule_works = False
                                break
                            
                            if np.any(cond & change_mask):
                                has_true = True
                        
                        if rule_works and has_true:
                            fill_method = determine_fill_colour(train_pairs, bg_col, df, None)
                            return {
                                'type': 'composite',
                                'bg_col': bg_col,
                                'dist_feature': df,
                                'target_dist': target_dist,
                                'neighbor_feature': nf,
                                'target_n': target_n,
                                'fill_method': fill_method,
                            }
        
        # Try parity rules (dist_p1_parity == 0)
        for df in dist_features:
            parity_feat = df.replace('_int', '_parity')
            if parity_feat in feature_names:
                for parity_val in [0, 1]:
                    rule_works = True
                    has_true = False
                    
                    for features, change_mask, inp, out in pair_data:
                        parity = features[parity_feat]
                        cond = (parity == parity_val)
                        
                        false_pos = cond & ~change_mask
                        # Only check bg cells
                        bg_mask = features['is_bg'].astype(bool)
                        false_pos_bg = false_pos & bg_mask & ~change_mask
                        
                        if np.any(false_pos_bg):
                            rule_works = False
                            break
                        
                        if np.any(cond & bg_mask & change_mask):
                            has_true = True
                    
                    if rule_works and has_true:
                        fill_method = determine_fill_colour(train_pairs, bg_col, parity_feat, None)
                        return {
                            'type': 'parity',
                            'bg_col': bg_col,
                            'feature': parity_feat,
                            'value': parity_val,
                            'fill_method': fill_method,
                        }
    
    return None


def determine_fill_colour(train_pairs, bg_col, feat_name, values):
    """Determine how to derive the fill colour."""
    # Check if fill colour is consistent across pairs
    fill_colours = []
    for inp, out in train_pairs:
        h, w = inp.height, inp.width
        for r in range(h):
            for c in range(w):
                if inp.cells[r][c] == bg_col and out.cells[r][c] != bg_col:
                    fill_colours.append(out.cells[r][c])
    
    if not fill_colours:
        return ('fixed', 0)
    
    # Check if it's always the same
    if len(set(fill_colours)) == 1:
        return ('fixed', fill_colours[0])
    
    # Check if it's minority/majority of non-bg
    all_non_bg = []
    for inp, _ in train_pairs:
        for r in range(inp.height):
            for c in range(inp.width):
                if inp.cells[r][c] != bg_col:
                    all_non_bg.append(inp.cells[r][c])
    
    if all_non_bg:
        counts = Counter(all_non_bg)
        majority = counts.most_common(1)[0][0]
        minority = counts.most_common()[-1][0]
        
        if all(f == minority for f in fill_colours):
            return ('minority',)
        if all(f == majority for f in fill_colours):
            return ('majority',)
    
    return ('per_pair_minority',)


# ═══════════════════════════════════════════════════════════════════
# STEP 4: RULE APPLICATION
# ═══════════════════════════════════════════════════════════════════

def apply_rule(rule: Dict, grid: Grid) -> Grid:
    """Apply a discovered rule to a grid."""
    h, w = grid.height, grid.width
    bg_col = rule['bg_col']
    features = extract_features(grid, bg_col)
    
    cells = [row[:] for row in grid.cells]
    
    if rule['type'] == 'single_feature':
        feat = features[rule['feature']]
        if feat.dtype == float:
            feat_rounded = np.round(feat, 2)
        else:
            feat_rounded = feat
        
        values = rule['values']
        fill = resolve_fill(rule['fill_method'], grid, bg_col)
        
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == bg_col and feat_rounded[r, c] in values:
                    cells[r][c] = fill
    
    elif rule['type'] == 'composite':
        dist = np.round(features[rule['dist_feature']], 0).astype(int)
        nfeat = features[rule['neighbor_feature']]
        
        cond = (dist == rule['target_dist']) & (nfeat >= rule['target_n'])
        fill = resolve_fill(rule['fill_method'], grid, bg_col)
        
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == bg_col and cond[r, c]:
                    cells[r][c] = fill
    
    elif rule['type'] == 'parity':
        parity = features[rule['feature']]
        fill = resolve_fill(rule['fill_method'], grid, bg_col)
        
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == bg_col and parity[r, c] == rule['value']:
                    cells[r][c] = fill
    
    return Grid(cells)


def resolve_fill(fill_method, grid, bg_col):
    """Resolve the fill colour for a grid."""
    if fill_method[0] == 'fixed':
        return fill_method[1]
    elif fill_method[0] == 'minority':
        non_bg = [grid.cells[r][c] for r in range(grid.height) for c in range(grid.width) 
                  if grid.cells[r][c] != bg_col]
        if non_bg:
            return Counter(non_bg).most_common()[-1][0]
        return 0
    elif fill_method[0] == 'majority':
        non_bg = [grid.cells[r][c] for r in range(grid.height) for c in range(grid.width) 
                  if grid.cells[r][c] != bg_col]
        if non_bg:
            return Counter(non_bg).most_common(1)[0][0]
        return 0
    elif fill_method[0] == 'per_pair_minority':
        non_bg = [grid.cells[r][c] for r in range(grid.height) for c in range(grid.width) 
                  if grid.cells[r][c] != bg_col]
        if non_bg:
            return Counter(non_bg).most_common()[-1][0]
        return 0
    return 0


# ═══════════════════════════════════════════════════════════════════
# MAIN PREDICTOR
# ═══════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c]
               for r in range(g1.height) for c in range(g1.width))


def predict(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Discover and apply distance-based rules."""
    # Check same-size
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Find bg candidates
    all_cols = Counter()
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                all_cols[pair.input.cells[r][c]] += 1
    
    bg_candidates = [col for col, _ in all_cols.most_common(3)]
    
    # Discover rule
    train_pairs = [(p.input, p.output) for p in task.train]
    rule = discover_rule(train_pairs, bg_candidates)
    
    if rule is None:
        return None
    
    # Verify on train
    for inp, out in train_pairs:
        pred = apply_rule(rule, inp)
        if not grids_equal(pred, out):
            return None
    
    # Apply to test
    test_input = task.test[0].input
    pred = apply_rule(rule, test_input)
    
    src = f"minkowski_{rule['type']}_{rule.get('feature', rule.get('dist_feature', ''))}"
    return pred, src, {'rule': str(rule)}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--max-tasks", type=int, default=None)
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()
    
    files = sorted(f for f in os.listdir(args.batch) if f.endswith(".json"))
    if args.max_tasks:
        files = files[:args.max_tasks]
    
    solved = total = 0
    sources = {}
    
    for fname in files:
        task = load_task(os.path.join(args.batch, fname),
                         name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1
        
        try:
            signal.setitimer(signal.ITIMER_REAL, 5.0)
            result = predict(task)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except:
            signal.setitimer(signal.ITIMER_REAL, 0)
            result = None
        
        if result is not None:
            pred, src, diag = result
            ok = (pred == task.test[0].expected_output)
            if ok:
                solved += 1
            sources[src] = sources.get(src, 0) + 1
            if args.verbose or ok:
                print(f"  {fname}: {'OK' if ok else 'X'} src={src}")
        else:
            sources["none"] = sources.get("none", 0) + 1
            if args.verbose:
                print(f"  {fname}: X src=none")
    
    print(f"\n═══ Minkowski Sweep ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources: {sources}")
