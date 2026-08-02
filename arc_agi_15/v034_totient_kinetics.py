"""
v034_totient_kinetics.py — Totient Reaction Kinetics for ARC tasks
====================================================================

Uses the Spatial Totient Kinetics engine to analyse ARC transformations
as thermodynamic reactions between geometric objects (N-gons).

Key mappings:
- ARC colour N → regular N-gon
- R(N) = 1/(2*sin(π/N)) → spatial radius
- C(N) = floor(N/2) - φ(N)/2 → sub-cycles (internal complexity)
- Colour transformation → thermodynamic reaction with ΔC (binding energy)

Approach:
1. For each cell change (input_colour → output_colour), compute reaction energetics
2. Find patterns: does the reaction regime (exo/endo/iso) determine which cells change?
3. Use geometric tension and radius as additional features in the Minkowski sweep
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter
import sys, os, signal, math
import numpy as np

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task
from spatial_totient_kinetics import (
    R_n, count_sub_cycles_closed, phi, get_geometric_tension, analyze_reaction
)


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
# COLOUR GEOMETRY: ARC colours as N-gons
# ═══════════════════════════════════════════════════════════════════

def colour_geometry(colour: int) -> Dict[str, float]:
    """Get geometric properties of an ARC colour treated as an N-gon."""
    n = colour if colour >= 3 else 3  # Map 0,1,2 to triangle
    return {
        'radius': R_n(n),
        'sub_cycles': count_sub_cycles_closed(colour),
        'tension': get_geometric_tension(n),
        'phi': phi(colour) if colour > 0 else 0,
        'is_prime': count_sub_cycles_closed(colour) == 0 and colour >= 2,
    }


def reaction_features(input_col: int, output_col: int) -> Dict[str, float]:
    """Compute reaction features for a colour transformation."""
    if input_col == output_col:
        return {'delta_C': 0, 'delta_T': 0, 'regime': 0}  # Identity
    
    try:
        r = analyze_reaction(input_col, output_col - input_col)
        return {
            'delta_C': r['delta_C'],
            'delta_T': r['delta_T'],
            'regime': 1 if r['regime'] == 'EXOTHERMIC' else (-1 if r['regime'] == 'ENDOTHERMIC' else 0),
        }
    except:
        return {'delta_C': 0, 'delta_T': 0, 'regime': 0}


# ═══════════════════════════════════════════════════════════════════
# GEOMETRIC FEATURE FIELD
# ═══════════════════════════════════════════════════════════════════

def compute_geometric_field(grid: Grid) -> Dict[str, np.ndarray]:
    """
    Compute geometric feature fields for a grid.
    Each cell gets: radius, sub_cycles, tension, phi values
    as continuous fields.
    """
    h, w = grid.height, grid.width
    matrix = np.array(grid.cells)
    
    # Pre-compute geometry for all possible colours (0-9)
    geo_cache = {}
    for c in range(10):
        geo_cache[c] = colour_geometry(c)
    
    radius_field = np.zeros((h, w))
    cycle_field = np.zeros((h, w))
    tension_field = np.zeros((h, w))
    prime_field = np.zeros((h, w))
    
    for r in range(h):
        for c in range(w):
            col = matrix[r, c]
            geo = geo_cache[col]
            radius_field[r, c] = geo['radius']
            cycle_field[r, c] = geo['sub_cycles']
            tension_field[r, c] = geo['tension']
            prime_field[r, c] = 1.0 if geo['is_prime'] else 0.0
    
    return {
        'radius': radius_field,
        'sub_cycles': cycle_field,
        'tension': tension_field,
        'is_prime': prime_field,
    }


# ═══════════════════════════════════════════════════════════════════
# PREDICTION: GEOMETRIC TRANSFORMATION RULES
# ═══════════════════════════════════════════════════════════════════

def try_geometric_transformation(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Try to find a geometric transformation rule.
    
    Approach: for each cell that changes, record the input colour's
    geometric properties and the transformation. Look for patterns
    like "prime colours change to X" or "high-tension colours change to Y".
    """
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Collect transformation data
    transformations = []  # (input_col, output_col, geo_features)
    
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                if ic != oc:
                    geo = colour_geometry(ic)
                    transformations.append((ic, oc, geo))
    
    if not transformations:
        return None
    
    # Check: is there a consistent mapping based on primality?
    prime_map = {}  # is_prime → output colour
    consistent = True
    
    for ic, oc, geo in transformations:
        key = geo['is_prime']
        if key in prime_map:
            if prime_map[key] != oc:
                consistent = False
                break
        else:
            prime_map[key] = oc
    
    if consistent and len(prime_map) > 0:
        # Apply prime/composite mapping
        test_input = task.test[0].input
        h, w = test_input.height, test_input.width
        cells = [row[:] for row in test_input.cells]
        
        for r in range(h):
            for c in range(w):
                ic = test_input.cells[r][c]
                geo = colour_geometry(ic)
                key = geo['is_prime']
                if key in prime_map:
                    cells[r][c] = prime_map[key]
        
        pred = Grid(cells)
        
        # Verify on train
        all_pass = True
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            cells = [row[:] for row in pair.input.cells]
            for r in range(h):
                for c in range(w):
                    ic = pair.input.cells[r][c]
                    geo = colour_geometry(ic)
                    key = geo['is_prime']
                    if key in prime_map:
                        cells[r][c] = prime_map[key]
            if not grids_equal(Grid(cells), pair.output):
                all_pass = False
                break
        
        if all_pass:
            return pred, f"geo_prime_map_{prime_map}"
    
    # Check: is there a consistent mapping based on sub-cycle count?
    cycle_map = {}
    consistent = True
    
    for ic, oc, geo in transformations:
        key = geo['sub_cycles']
        if key in cycle_map:
            if cycle_map[key] != oc:
                consistent = False
                break
        else:
            cycle_map[key] = oc
    
    if consistent and len(cycle_map) > 1:
        test_input = task.test[0].input
        h, w = test_input.height, test_input.width
        cells = [row[:] for row in test_input.cells]
        
        for r in range(h):
            for c in range(w):
                ic = test_input.cells[r][c]
                geo = colour_geometry(ic)
                key = geo['sub_cycles']
                if key in cycle_map:
                    cells[r][c] = cycle_map[key]
        
        pred = Grid(cells)
        
        all_pass = True
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            cells = [row[:] for row in pair.input.cells]
            for r in range(h):
                for c in range(w):
                    ic = pair.input.cells[r][c]
                    geo = colour_geometry(ic)
                    key = geo['sub_cycles']
                    if key in cycle_map:
                        cells[r][c] = cycle_map[key]
            if not grids_equal(Grid(cells), pair.output):
                all_pass = False
                break
        
        if all_pass:
            return pred, f"geo_cycle_map_{len(cycle_map)}_classes"
    
    # Check: is there a consistent mapping based on radius ordering?
    # Sort colours by radius, map based on rank
    all_cols = set()
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                all_cols.add(pair.input.cells[r][c])
    
    sorted_cols = sorted(all_cols, key=lambda x: R_n(max(x, 3)))
    rank_map = {col: i for i, col in enumerate(sorted_cols)}
    
    rank_transform = {}
    consistent = True
    for ic, oc, geo in transformations:
        ir = rank_map.get(ic, -1)
        if ir in rank_transform:
            if rank_transform[ir] != oc:
                consistent = False
                break
        else:
            rank_transform[ir] = oc
    
    if consistent and len(rank_transform) > 1:
        test_input = task.test[0].input
        h, w = test_input.height, test_input.width
        cells = [row[:] for row in test_input.cells]
        
        for r in range(h):
            for c in range(w):
                ic = test_input.cells[r][c]
                ir = rank_map.get(ic, -1)
                if ir in rank_transform:
                    cells[r][c] = rank_transform[ir]
        
        pred = Grid(cells)
        
        all_pass = True
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            cells = [row[:] for row in pair.input.cells]
            for r in range(h):
                for c in range(w):
                    ic = pair.input.cells[r][c]
                    ir = rank_map.get(ic, -1)
                    if ir in rank_transform:
                        cells[r][c] = rank_transform[ir]
            if not grids_equal(Grid(cells), pair.output):
                all_pass = False
                break
        
        if all_pass:
            return pred, f"geo_radius_rank_map"
    
    return None


# ═══════════════════════════════════════════════════════════════════
# INTEGRATION: GEOMETRIC + MINKOWSKI SWEEP
# ═══════════════════════════════════════════════════════════════════

def try_geometric_minkowski_combo(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Combine geometric features with Minkowski distance fields.
    
    For each non-bg colour, compute:
    - Distance field (Minkowski p=1.5)
    - Geometric features (radius, cycles, tension)
    
    Then search for rules like:
    "bg cells at distance D from colour X, where X has Y sub-cycles → change to Z"
    """
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    all_cols = Counter()
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                all_cols[pair.input.cells[r][c]] += 1
    
    bg_candidates = [col for col, _ in all_cols.most_common(3)]
    
    for bg_col in bg_candidates:
        # For each non-bg colour, try distance-based rules
        non_bg_cols = set()
        for pair in task.train:
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    if pair.input.cells[r][c] != bg_col:
                        non_bg_cols.add(pair.input.cells[r][c])
        
        for target_col in non_bg_cols:
            geo = colour_geometry(target_col)
            
            # Try: bg cells at distance D from target_col → fill
            for p_val in [1, 1.5, 2]:
                for target_dist in [1, 2, 3]:
                    all_pass = True
                    fill_colours = []
                    
                    for pair in task.train:
                        h, w = pair.input.height, pair.input.width
                        matrix = np.array(pair.input.cells)
                        target_mask = (matrix == target_col)
                        
                        # Compute distance field
                        from v033_minkowski_sweep import compute_minkowski_field
                        dist_field = compute_minkowski_field(matrix, target_mask, p_val)
                        
                        cells = [row[:] for row in pair.input.cells]
                        for r in range(h):
                            for c in range(w):
                                if pair.input.cells[r][c] == bg_col:
                                    d = dist_field[r, c]
                                    if abs(d - target_dist) < 0.5:
                                        oc = pair.output.cells[r][c]
                                        if oc != bg_col:
                                            fill_colours.append(oc)
                                            cells[r][c] = oc
                        
                        if not grids_equal(Grid(cells), pair.output):
                            # Not a simple distance rule
                            all_pass = False
                            break
                    
                    if not all_pass or not fill_colours:
                        continue
                    
                    # Check fill colour consistency
                    if len(set(fill_colours)) == 1:
                        fill = fill_colours[0]
                    else:
                        # Try per-pair minority
                        fill = None  # Will be resolved per-pair
                    
                    # Re-verify with correct fill
                    all_pass = True
                    for pair in task.train:
                        h, w = pair.input.height, pair.input.width
                        matrix = np.array(pair.input.cells)
                        target_mask = (matrix == target_col)
                        
                        from v033_minkowski_sweep import compute_minkowski_field
                        dist_field = compute_minkowski_field(matrix, target_mask, p_val)
                        
                        if fill is None:
                            non_bg = [pair.input.cells[r][c] for r in range(h) for c in range(w)
                                     if pair.input.cells[r][c] != bg_col]
                            pair_fill = Counter(non_bg).most_common()[-1][0] if non_bg else 0
                        else:
                            pair_fill = fill
                        
                        cells = [row[:] for row in pair.input.cells]
                        for r in range(h):
                            for c in range(w):
                                if pair.input.cells[r][c] == bg_col:
                                    d = dist_field[r, c]
                                    if abs(d - target_dist) < 0.5:
                                        cells[r][c] = pair_fill
                        
                        if not grids_equal(Grid(cells), pair.output):
                            all_pass = False
                            break
                    
                    if all_pass:
                        # Apply to test
                        test = task.test[0].input
                        h, w = test.height, test.width
                        matrix = np.array(test.cells)
                        target_mask = (matrix == target_col)
                        
                        from v033_minkowski_sweep import compute_minkowski_field
                        dist_field = compute_minkowski_field(matrix, target_mask, p_val)
                        
                        if fill is None:
                            non_bg = [test.cells[r][c] for r in range(h) for c in range(w)
                                     if test.cells[r][c] != bg_col]
                            test_fill = Counter(non_bg).most_common()[-1][0] if non_bg else 0
                        else:
                            test_fill = fill
                        
                        cells = [row[:] for row in test.cells]
                        for r in range(h):
                            for c in range(w):
                                if test.cells[r][c] == bg_col:
                                    d = dist_field[r, c]
                                    if abs(d - target_dist) < 0.5:
                                        cells[r][c] = test_fill
                        
                        pred = Grid(cells)
                        src = f"geo_mink_p{p_val}_d{target_dist}_col{target_col}_C{geo['sub_cycles']}"
                        return pred, src
    
    return None


# ═══════════════════════════════════════════════════════════════════
# MAIN PREDICTOR
# ═══════════════════════════════════════════════════════════════════

def predict(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Try geometric + totient kinetics approaches."""
    strategies = [
        ("geometric_transform", try_geometric_transformation),
        ("geometric_minkowski", try_geometric_minkowski_combo),
    ]
    
    for name, fn in strategies:
        try:
            signal.setitimer(signal.ITIMER_REAL, 5.0)
            result = fn(task)
            signal.setitimer(signal.ITIMER_REAL, 0)
            if result is not None:
                pred, src = result
                return pred, src, {"strategy": name}
        except:
            signal.setitimer(signal.ITIMER_REAL, 0)
            continue
    
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
        
        result = predict(task)
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
    
    print(f"\n═══ Totient Kinetics ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources: {sources}")
