"""
v038_per_colour_minkowski.py — Per-Colour Minkowski Distance Layers
====================================================================

Instead of one distance field (distance to any non-bg), computes
N distance fields (distance to each colour separately).

This enables rules like:
- "cells at distance 2 from blue AND distance 1 from red → change to green"
- "cells near colour X change to Y, cells near colour Z change to W"

Architecture:
1. For each train pair, compute distance fields for ALL colours (0-9)
2. For each changed cell, record its per-colour distances
3. Search for rules that perfectly separate changed from unchanged cells
4. Apply discovered rules to test input

Uses vectorized Minkowski p-norm computation (numpy).
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import Counter
import sys, os, signal
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


def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c]
               for r in range(g1.height) for c in range(g1.width))


# ═══════════════════════════════════════════════════════════════════
# 1. PER-COLOUR DISTANCE FIELD COMPUTATION
# ═══════════════════════════════════════════════════════════════════

def compute_minkowski_field_fast(matrix: np.ndarray, target_mask: np.ndarray, 
                                  p: float) -> np.ndarray:
    """Fast Minkowski distance field computation."""
    h, w = matrix.shape
    target_coords = np.argwhere(target_mask)
    
    if len(target_coords) == 0:
        return np.full((h, w), 999.0)
    
    r_mesh, c_mesh = np.indices((h, w))
    coords_mesh = np.stack([r_mesh, c_mesh], axis=-1).astype(float)
    
    deltas = coords_mesh[:, :, np.newaxis, :] - target_coords[np.newaxis, np.newaxis, :, :]
    abs_deltas = np.abs(deltas)
    
    if p == np.inf:
        dists = np.max(abs_deltas, axis=-1)
    elif p == 1:
        dists = np.sum(abs_deltas, axis=-1)
    else:
        dists = np.sum(abs_deltas ** p, axis=-1) ** (1.0 / p)
    
    return np.min(dists, axis=-1)


def compute_all_colour_fields(grid: Grid, p: float = 1.5) -> Dict[int, np.ndarray]:
    """
    Compute Minkowski distance fields for ALL colours (0-9).
    Returns: {colour: (H, W) distance field}
    """
    h, w = grid.height, grid.width
    matrix = np.array(grid.cells)
    
    fields = {}
    for colour in range(10):
        mask = (matrix == colour)
        if np.any(mask):
            fields[colour] = compute_minkowski_field_fast(matrix, mask, p)
        else:
            fields[colour] = np.full((h, w), 999.0)
    
    return fields


# ═══════════════════════════════════════════════════════════════════
# 2. FEATURE EXTRACTION PER CELL
# ═══════════════════════════════════════════════════════════════════

def extract_cell_distances(fields: Dict[int, np.ndarray], r: int, c: int) -> Dict[int, float]:
    """Get per-colour distances for a specific cell."""
    return {col: fields[col][r, c] for col in fields}


# ═══════════════════════════════════════════════════════════════════
# 3. RULE DISCOVERY — Truth Table with Per-Colour Distances
# ═══════════════════════════════════════════════════════════════════

def discover_per_colour_rules(train_pairs: List[Tuple[Grid, Grid]], 
                                bg_candidates: List[int],
                                p_values: List[float] = [1, 1.5, 2]) -> Optional[Dict]:
    """
    Search for rules using per-colour Minkowski distance fields.
    
    For each bg colour and p-value:
    1. Compute per-colour distance fields
    2. For each changed cell, record its per-colour distances
    3. Find distance thresholds that separate changed from unchanged
    """
    for bg_col in bg_candidates:
        for p_val in p_values:
            # Compute fields for all train pairs
            pair_data = []
            for inp, out in train_pairs:
                if inp.height != out.height or inp.width != out.width:
                    break
                
                fields = compute_all_colour_fields(inp, p_val)
                change_mask = np.array(inp.cells) != np.array(out.cells)
                pair_data.append((fields, change_mask, inp, out))
            else:
                # All pairs processed
                # Collect per-colour distances for changed vs unchanged bg cells
                changed_distances = []  # List of {col: dist} dicts
                unchanged_distances = []
                
                for fields, change_mask, inp, out in pair_data:
                    h, w = inp.height, inp.width
                    for r in range(h):
                        for c in range(w):
                            if inp.cells[r][c] != bg_col:
                                continue
                            
                            dists = extract_cell_distances(fields, r, c)
                            if change_mask[r, c]:
                                changed_distances.append(dists)
                            else:
                                unchanged_distances.append(dists)
                
                if not changed_distances:
                    continue
                
                # Find colour-distance pairs that separate changed from unchanged
                # For each colour, find distance values that appear ONLY in changed cells
                for target_col in fields.keys():
                    if target_col == bg_col:
                        continue
                    
                    changed_vals = set()
                    for d in changed_distances:
                        # Round to avoid floating point issues
                        changed_vals.add(round(d[target_col], 1))
                    
                    unchanged_vals = set()
                    for d in unchanged_distances:
                        unchanged_vals.add(round(d[target_col], 1))
                    
                    unique_to_changed = changed_vals - unchanged_vals
                    
                    if unique_to_changed and len(unique_to_changed) <= 5:
                        # Found a separating distance for this colour
                        # Determine fill colour
                        fill_colours = []
                        for inp, out in train_pairs:
                            h, w = inp.height, inp.width
                            fields = compute_all_colour_fields(inp, p_val)
                            for r in range(h):
                                for c in range(w):
                                    if inp.cells[r][c] == bg_col:
                                        d = round(fields[target_col][r, c], 1)
                                        if d in unique_to_changed:
                                            oc = out.cells[r][c]
                                            if oc != bg_col:
                                                fill_colours.append(oc)
                        
                        if not fill_colours:
                            continue
                        
                        # Check fill consistency
                        fill_counter = Counter(fill_colours)
                        fill = fill_counter.most_common(1)[0][0]
                        
                        # Verify on all train pairs
                        all_pass = True
                        for inp, out in train_pairs:
                            h, w = inp.height, inp.width
                            fields = compute_all_colour_fields(inp, p_val)
                            
                            cells = [row[:] for row in inp.cells]
                            for r in range(h):
                                for c in range(w):
                                    if inp.cells[r][c] == bg_col:
                                        d = round(fields[target_col][r, c], 1)
                                        if d in unique_to_changed:
                                            cells[r][c] = fill
                            
                            if not grids_equal(Grid(cells), out):
                                all_pass = False
                                break
                        
                        if all_pass:
                            return {
                                'bg_col': bg_col,
                                'target_col': target_col,
                                'p_val': p_val,
                                'distances': unique_to_changed,
                                'fill': fill,
                            }
                
                # Try composite rules: distance to colour A AND distance to colour B
                all_cols = list(fields.keys())
                for i, col_a in enumerate(all_cols):
                    if col_a == bg_col:
                        continue
                    for col_b in all_cols[i+1:]:
                        if col_b == bg_col:
                            continue
                        
                        changed_pairs = set()
                        unchanged_pairs = set()
                        
                        for d in changed_distances:
                            changed_pairs.add((round(d[col_a], 1), round(d[col_b], 1)))
                        
                        for d in unchanged_distances:
                            unchanged_pairs.add((round(d[col_a], 1), round(d[col_b], 1)))
                        
                        unique_pairs = changed_pairs - unchanged_pairs
                        
                        if unique_pairs and len(unique_pairs) <= 10:
                            # Determine fill
                            fill_colours = []
                            for inp, out in train_pairs:
                                h, w = inp.height, inp.width
                                fields = compute_all_colour_fields(inp, p_val)
                                for r in range(h):
                                    for c in range(w):
                                        if inp.cells[r][c] == bg_col:
                                            da = round(fields[col_a][r, c], 1)
                                            db = round(fields[col_b][r, c], 1)
                                            if (da, db) in unique_pairs:
                                                oc = out.cells[r][c]
                                                if oc != bg_col:
                                                    fill_colours.append(oc)
                            
                            if not fill_colours:
                                continue
                            
                            fill = Counter(fill_colours).most_common(1)[0][0]
                            
                            # Verify
                            all_pass = True
                            for inp, out in train_pairs:
                                h, w = inp.height, inp.width
                                fields = compute_all_colour_fields(inp, p_val)
                                
                                cells = [row[:] for row in inp.cells]
                                for r in range(h):
                                    for c in range(w):
                                        if inp.cells[r][c] == bg_col:
                                            da = round(fields[col_a][r, c], 1)
                                            db = round(fields[col_b][r, c], 1)
                                            if (da, db) in unique_pairs:
                                                cells[r][c] = fill
                                
                                if not grids_equal(Grid(cells), out):
                                    all_pass = False
                                    break
                            
                            if all_pass:
                                return {
                                    'bg_col': bg_col,
                                    'target_col_a': col_a,
                                    'target_col_b': col_b,
                                    'p_val': p_val,
                                    'distance_pairs': unique_pairs,
                                    'fill': fill,
                                    'type': 'composite',
                                }
    
    return None


# ═══════════════════════════════════════════════════════════════════
# 4. PER-COLOUR FILL RULES (Different fill for different target colours)
# ═══════════════════════════════════════════════════════════════════

def discover_per_colour_fill_rules(train_pairs: List[Tuple[Grid, Grid]],
                                     bg_candidates: List[int],
                                     p_values: List[float] = [1, 1.5, 2]) -> Optional[Dict]:
    """
    Discover rules where different target colours produce different fills.
    
    Pattern: "cells near colour X → fill X, cells near colour Y → fill Y"
    (i.e., the fill colour IS the target colour)
    """
    for bg_col in bg_candidates:
        for p_val in p_values:
            for target_dist in [1, 2, 3]:
                # Check if: bg cells at distance target_dist from colour X → become X
                all_pass = True
                
                for inp, out in train_pairs:
                    if inp.height != out.height or inp.width != out.width:
                        all_pass = False
                        break
                    
                    fields = compute_all_colour_fields(inp, p_val)
                    h, w = inp.height, inp.width
                    
                    cells = [row[:] for row in inp.cells]
                    for r in range(h):
                        for c in range(w):
                            if inp.cells[r][c] == bg_col:
                                # Find which colour is closest at target_dist
                                for col in range(10):
                                    if col == bg_col:
                                        continue
                                    d = round(fields[col][r, c], 1)
                                    if abs(d - target_dist) < 0.5:
                                        cells[r][c] = col
                                        break
                    
                    if not grids_equal(Grid(cells), out):
                        all_pass = False
                        break
                
                if all_pass:
                    return {
                        'type': 'per_colour_fill',
                        'bg_col': bg_col,
                        'p_val': p_val,
                        'target_dist': target_dist,
                    }
    
    return None


# ═══════════════════════════════════════════════════════════════════
# 5. NEAREST-COLOUR DISTANCE RULE
# ═══════════════════════════════════════════════════════════════════

def discover_nearest_colour_rule(train_pairs: List[Tuple[Grid, Grid]],
                                   bg_candidates: List[int],
                                   p_values: List[float] = [1, 1.5, 2]) -> Optional[Dict]:
    """
    Discover rules based on nearest non-bg colour.
    
    Pattern: "bg cells whose nearest non-bg cell is colour X → become Y"
    """
    for bg_col in bg_candidates:
        for p_val in p_values:
            # For each bg cell that changes, what's the nearest non-bg colour?
            nearest_colour_map = {}  # nearest_col → output_col
            consistent = True
            
            for inp, out in train_pairs:
                if inp.height != out.height or inp.width != out.width:
                    consistent = False
                    break
                
                fields = compute_all_colour_fields(inp, p_val)
                h, w = inp.height, inp.width
                
                for r in range(h):
                    for c in range(w):
                        if inp.cells[r][c] != bg_col:
                            continue
                        oc = out.cells[r][c]
                        if oc == bg_col:
                            continue
                        
                        # Find nearest non-bg colour
                        min_dist = 999
                        nearest = -1
                        for col in range(10):
                            if col == bg_col:
                                continue
                            if fields[col][r, c] < min_dist:
                                min_dist = fields[col][r, c]
                                nearest = col
                        
                        if nearest in nearest_colour_map:
                            if nearest_colour_map[nearest] != oc:
                                consistent = False
                                break
                        else:
                            nearest_colour_map[nearest] = oc
                    if not consistent:
                        break
                if not consistent:
                    break
            
            if not consistent or not nearest_colour_map:
                continue
            
            # Verify
            all_pass = True
            for inp, out in train_pairs:
                h, w = inp.height, inp.width
                fields = compute_all_colour_fields(inp, p_val)
                
                cells = [row[:] for row in inp.cells]
                for r in range(h):
                    for c in range(w):
                        if inp.cells[r][c] != bg_col:
                            continue
                        
                        min_dist = 999
                        nearest = -1
                        for col in range(10):
                            if col == bg_col:
                                continue
                            if fields[col][r, c] < min_dist:
                                min_dist = fields[col][r, c]
                                nearest = col
                        
                        if nearest in nearest_colour_map:
                            cells[r][c] = nearest_colour_map[nearest]
                
                if not grids_equal(Grid(cells), out):
                    all_pass = False
                    break
            
            if all_pass:
                return {
                    'type': 'nearest_colour',
                    'bg_col': bg_col,
                    'p_val': p_val,
                    'mapping': nearest_colour_map,
                }
    
    return None


# ═══════════════════════════════════════════════════════════════════
# 6. RULE APPLICATION
# ═══════════════════════════════════════════════════════════════════

def apply_rule(rule: Dict, grid: Grid) -> Grid:
    """Apply a discovered rule to a grid."""
    h, w = grid.height, grid.width
    bg_col = rule['bg_col']
    p_val = rule['p_val']
    
    fields = compute_all_colour_fields(grid, p_val)
    cells = [row[:] for row in grid.cells]
    
    if rule.get('type') == 'per_colour_fill':
        target_dist = rule['target_dist']
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == bg_col:
                    for col in range(10):
                        if col == bg_col:
                            continue
                        d = round(fields[col][r, c], 1)
                        if abs(d - target_dist) < 0.5:
                            cells[r][c] = col
                            break
    
    elif rule.get('type') == 'nearest_colour':
        mapping = rule['mapping']
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] != bg_col:
                    continue
                min_dist = 999
                nearest = -1
                for col in range(10):
                    if col == bg_col:
                        continue
                    if fields[col][r, c] < min_dist:
                        min_dist = fields[col][r, c]
                        nearest = col
                if nearest in mapping:
                    cells[r][c] = mapping[nearest]
    
    elif rule.get('type') == 'composite':
        col_a = rule['target_col_a']
        col_b = rule['target_col_b']
        pairs = rule['distance_pairs']
        fill = rule['fill']
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == bg_col:
                    da = round(fields[col_a][r, c], 1)
                    db = round(fields[col_b][r, c], 1)
                    if (da, db) in pairs:
                        cells[r][c] = fill
    
    else:
        # Single colour rule
        target_col = rule['target_col']
        distances = rule['distances']
        fill = rule['fill']
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == bg_col:
                    d = round(fields[target_col][r, c], 1)
                    if d in distances:
                        cells[r][c] = fill
    
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# 7. MAIN PREDICTOR
# ═══════════════════════════════════════════════════════════════════

def predict(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Discover and apply per-colour Minkowski rules."""
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
    
    bg_candidates = [col for col, _ in all_cols.most_common(4)]
    
    train_pairs = [(p.input, p.output) for p in task.train]
    
    # Try each rule type
    for p_val in [1, 1.5, 2]:
        # 1. Single colour distance rule
        rule = discover_per_colour_rules(train_pairs, bg_candidates, [p_val])
        if rule:
            # Verify on train
            all_pass = True
            for inp, out in train_pairs:
                pred = apply_rule(rule, inp)
                if not grids_equal(pred, out):
                    all_pass = False
                    break
            
            if all_pass:
                test_input = task.test[0].input
                pred = apply_rule(rule, test_input)
                src = f"per_col_p{p_val}_col{rule.get('target_col', '?')}"
                return pred, src, {'rule': str(rule)}
        
        # 2. Per-colour fill (fill = target colour)
        rule = discover_per_colour_fill_rules(train_pairs, bg_candidates, [p_val])
        if rule:
            all_pass = True
            for inp, out in train_pairs:
                pred = apply_rule(rule, inp)
                if not grids_equal(pred, out):
                    all_pass = False
                    break
            
            if all_pass:
                test_input = task.test[0].input
                pred = apply_rule(rule, test_input)
                return pred, f"per_col_fill_p{p_val}", {'rule': str(rule)}
        
        # 3. Nearest colour rule
        rule = discover_nearest_colour_rule(train_pairs, bg_candidates, [p_val])
        if rule:
            all_pass = True
            for inp, out in train_pairs:
                pred = apply_rule(rule, inp)
                if not grids_equal(pred, out):
                    all_pass = False
                    break
            
            if all_pass:
                test_input = task.test[0].input
                pred = apply_rule(rule, test_input)
                return pred, f"nearest_col_p{p_val}", {'rule': str(rule)}
    
    return None


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
            signal.setitimer(signal.ITIMER_REAL, 15.0)
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
    
    print(f"\n═══ Per-Colour Minkowski ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources: {sources}")
