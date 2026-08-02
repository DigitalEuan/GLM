"""
v043_composition_grammar.py — The Bridge Between Tools and Tasks
=================================================================

The tools work (10/10 synthetic tests pass).
The gap is COMPOSITION — knowing which tool to use when.

This module implements a composition grammar:
  IF (cell has property P) THEN (apply transformation T)

Properties P are computed by the existing sensors:
  - Neighbourhood bitmask (which colours are adjacent)
  - Minkowski distance (how far from objects)
  - Object membership (which object the cell belongs to)
  - MOG fingerprint (local context identity)

Transformations T are the existing DSL operations:
  - Recolour (change colour)
  - Move (shift position)
  - Fill (propagate colour)
  - Erase (set to background)

The grammar discovers rules by:
1. For each changed cell, extract all properties
2. Find the SIMPLEST property that uniquely identifies the change
3. Verify the rule on all train pairs
4. Apply to test

Simplicity order (Occam's razor):
  1. Colour-only (global recolour)
  2. Colour + neighbour (conditional recolour)
  3. Colour + distance (distance-based)
  4. Colour + object property (object-level)
  5. Multi-condition (colour + neighbour + distance)
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import Counter, deque
import sys, os, signal
import numpy as np

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task
from v032_distance_rule import manhattan_distances
from v041_neighbourhood_bitmask import (
    neighbourhood_bitmask_for_colour, neighbourhood_colours,
    local_context_fingerprint, MOORE_OFFSETS
)
from v042_object_level import segment_objects, ARCObject


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
# 1. PROPERTY EXTRACTION
# ═══════════════════════════════════════════════════════════════════

class CellProperties:
    """All extractable properties of a cell."""
    
    def __init__(self, grid: Grid, r: int, c: int, 
                 dist_fields: Optional[Dict[int, np.ndarray]] = None,
                 objects: Optional[List[ARCObject]] = None):
        h, w = grid.height, grid.width
        self.r = r
        self.c = c
        self.colour = grid.cells[r][c]
        self.h = h
        self.w = w
        
        # Neighbourhood
        self.n4 = neighbourhood_colours(grid, r, c)
        self.n4_set = frozenset(x for x in self.n4 if x >= 0)
        self.n4_nonzero = tuple(sorted(set(x for x in self.n4 if x > 0)))
        self.n_nonzero = sum(1 for x in self.n4 if x > 0)
        
        # For each possible neighbour colour, bitmask
        self.bitmasks = {}
        for col in range(10):
            if col != self.colour:
                self.bitmasks[col] = neighbourhood_bitmask_for_colour(grid, r, c, col)
        
        # Distance to nearest non-zero cell
        if dist_fields is not None and 0 in dist_fields:
            self.dist_to_any = dist_fields[0][r, c]
        else:
            self.dist_to_any = 0
        
        # Distance to specific colours
        self.distances = {}
        if dist_fields is not None:
            for col, field in dist_fields.items():
                self.distances[col] = field[r, c]
        
        # Object membership
        self.object_id = -1
        self.object_size = 0
        self.object_is_frame = False
        self.object_colour = self.colour
        if objects is not None:
            for i, obj in enumerate(objects):
                if (r, c) in obj.cells:
                    self.object_id = i
                    self.object_size = obj.size
                    self.object_is_frame = obj.is_frame
                    self.object_colour = obj.colour
                    break
        
        # Position
        self.is_border = (r == 0 or r == h-1 or c == 0 or c == w-1)
        self.row_parity = r % 2
        self.col_parity = c % 2


def extract_all_properties(grid: Grid, p_val: float = 1.5) -> Dict[Tuple[int, int], CellProperties]:
    """Extract properties for all cells in a grid."""
    h, w = grid.height, grid.width
    
    # Compute distance fields for all colours
    dist_fields = {}
    matrix = np.array(grid.cells)
    for col in range(10):
        mask = (matrix == col)
        if np.any(mask):
            target_coords = np.argwhere(mask).astype(float)
            r_mesh, c_mesh = np.indices((h, w))
            coords = np.stack([r_mesh, c_mesh], axis=-1).astype(float)
            deltas = coords[:, :, np.newaxis, :] - target_coords[np.newaxis, np.newaxis, :, :]
            abs_deltas = np.abs(deltas)
            if p_val == np.inf:
                dists = np.max(abs_deltas, axis=-1)
            elif p_val == 1:
                dists = np.sum(abs_deltas, axis=-1)
            else:
                dists = np.sum(abs_deltas ** p_val, axis=-1) ** (1.0 / p_val)
            dist_fields[col] = np.min(dists, axis=-1)
        else:
            dist_fields[col] = np.full((h, w), 999.0)
    
    # Segment objects
    objects = segment_objects(grid)
    
    # Extract properties for each cell
    props = {}
    for r in range(h):
        for c in range(w):
            props[(r, c)] = CellProperties(grid, r, c, dist_fields, objects)
    
    return props


# ═══════════════════════════════════════════════════════════════════
# 2. RULE DISCOVERY (Occam's Razor)
# ═══════════════════════════════════════════════════════════════════

def discover_rules(train_pairs: List[Tuple[Grid, Grid]]) -> Optional[Dict]:
    """
    Discover transformation rules using Occam's razor.
    Try simplest rules first, then more complex ones.
    """
    # Pre-compute properties for all train pairs
    pair_props = []
    for inp, out in train_pairs:
        if inp.height != out.height or inp.width != out.width:
            return None
        props_in = extract_all_properties(inp)
        pair_props.append((inp, out, props_in))
    
    # Collect changed cells with their properties
    changed = []  # (properties, output_colour)
    unchanged = []  # properties
    
    for inp, out, props in pair_props:
        h, w = inp.height, inp.width
        for r in range(h):
            for c in range(w):
                ic, oc = inp.cells[r][c], out.cells[r][c]
                p = props[(r, c)]
                if ic != oc:
                    changed.append((p, oc))
                else:
                    unchanged.append(p)
    
    if not changed:
        return None
    
    # ═══ LEVEL 1: Simple colour mapping ═══
    colour_map = {}
    consistent = True
    for p, oc in changed:
        if p.colour in colour_map:
            if colour_map[p.colour] != oc:
                consistent = False
                break
        else:
            colour_map[p.colour] = oc
    
    if consistent and colour_map:
        # Verify
        rule = {'type': 'colour_map', 'mapping': colour_map}
        if _verify_rule(rule, train_pairs):
            return rule
    
    # ═══ LEVEL 2: Colour + has neighbour X ═══
    for target_col in range(10):
        for n_col in range(10):
            if n_col == target_col or n_col == 0:
                continue
            
            rule_map = {}
            consistent = True
            for p, oc in changed:
                if p.colour == target_col and p.bitmasks.get(n_col, 0) > 0:
                    if target_col in rule_map:
                        if rule_map[target_col] != oc:
                            consistent = False
                            break
                    else:
                        rule_map[target_col] = oc
            
            if consistent and rule_map:
                rule = {'type': 'has_neighbour', 'colour': target_col, 
                        'neighbour': n_col, 'output': rule_map[target_col]}
                if _verify_rule(rule, train_pairs):
                    return rule
    
    # ═══ LEVEL 3: Colour + neighbour bitmask (exact pattern) ═══
    for target_col in range(10):
        for n_col in range(10):
            if n_col == target_col or n_col == 0:
                continue
            
            # Find bitmask values that uniquely identify changes
            changed_masks = set()
            unchanged_masks = set()
            
            for p, oc in changed:
                if p.colour == target_col:
                    changed_masks.add(p.bitmasks.get(n_col, 0))
            for p in unchanged:
                if p.colour == target_col:
                    unchanged_masks.add(p.bitmasks.get(n_col, 0))
            
            unique_masks = changed_masks - unchanged_masks - {0}
            
            if unique_masks:
                # Find consistent output
                outputs = set()
                for p, oc in changed:
                    if p.colour == target_col and p.bitmasks.get(n_col, 0) in unique_masks:
                        outputs.add(oc)
                
                if len(outputs) == 1:
                    rule = {'type': 'bitmask', 'colour': target_col,
                            'neighbour': n_col, 'masks': unique_masks,
                            'output': list(outputs)[0]}
                    if _verify_rule(rule, train_pairs):
                        return rule
    
    # ═══ LEVEL 4: Colour + distance to X ═══
    for target_col in set(p.colour for p, _ in changed):
        for dist_col in range(10):
            if dist_col == target_col:
                continue
            
            # Find distance values that separate changed from unchanged
            changed_dists = set()
            unchanged_dists = set()
            
            for p, oc in changed:
                if p.colour == target_col and dist_col in p.distances:
                    changed_dists.add(round(p.distances[dist_col], 0))
            for p in unchanged:
                if p.colour == target_col and dist_col in p.distances:
                    unchanged_dists.add(round(p.distances[dist_col], 0))
            
            unique_dists = changed_dists - unchanged_dists
            
            if unique_dists and len(unique_dists) <= 3:
                outputs = set()
                for p, oc in changed:
                    if p.colour == target_col and dist_col in p.distances:
                        if round(p.distances[dist_col], 0) in unique_dists:
                            outputs.add(oc)
                
                if len(outputs) == 1:
                    rule = {'type': 'distance', 'colour': target_col,
                            'dist_col': dist_col, 'distances': unique_dists,
                            'output': list(outputs)[0]}
                    if _verify_rule(rule, train_pairs):
                        return rule
    
    # ═══ LEVEL 5: Object-level rules ═══
    for target_col in set(p.colour for p, _ in changed):
        # Rule: objects of colour X that are frames → colour Y
        frame_outputs = set()
        non_frame_outputs = set()
        
        for p, oc in changed:
            if p.colour == target_col:
                if p.object_is_frame:
                    frame_outputs.add(oc)
                else:
                    non_frame_outputs.add(oc)
        
        if frame_outputs and len(frame_outputs) == 1:
            rule = {'type': 'object_frame', 'colour': target_col,
                    'output': list(frame_outputs)[0]}
            if _verify_rule(rule, train_pairs):
                return rule
    
    # ═══ LEVEL 6: Multi-condition (colour + neighbour count) ═══
    for target_col in range(10):
        for n_count in range(5):
            outputs = set()
            for p, oc in changed:
                if p.colour == target_col and p.n_nonzero == n_count:
                    outputs.add(oc)
            
            if len(outputs) == 1:
                rule = {'type': 'neighbour_count', 'colour': target_col,
                        'count': n_count, 'output': list(outputs)[0]}
                if _verify_rule(rule, train_pairs):
                    return rule
    
    return None


def _verify_rule(rule: Dict, train_pairs: List[Tuple[Grid, Grid]]) -> bool:
    """Verify a rule on all train pairs."""
    for inp, out in train_pairs:
        pred = apply_rule(rule, inp)
        if not grids_equal(pred, out):
            return False
    return True


# ═══════════════════════════════════════════════════════════════════
# 3. RULE APPLICATION
# ═══════════════════════════════════════════════════════════════════

def apply_rule(rule: Dict, grid: Grid) -> Grid:
    """Apply a discovered rule to a grid."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    
    if rule['type'] == 'colour_map':
        mapping = rule['mapping']
        for r in range(h):
            for c in range(w):
                if cells[r][c] in mapping:
                    cells[r][c] = mapping[cells[r][c]]
    
    elif rule['type'] == 'has_neighbour':
        target = rule['colour']
        n_col = rule['neighbour']
        output = rule['output']
        for r in range(h):
            for c in range(w):
                if cells[r][c] == target:
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] == n_col:
                            cells[r][c] = output
                            break
    
    elif rule['type'] == 'bitmask':
        target = rule['colour']
        n_col = rule['neighbour']
        masks = rule['masks']
        output = rule['output']
        for r in range(h):
            for c in range(w):
                if cells[r][c] == target:
                    m = neighbourhood_bitmask_for_colour(grid, r, c, n_col)
                    if m in masks:
                        cells[r][c] = output
    
    elif rule['type'] == 'distance':
        target = rule['colour']
        dist_col = rule['dist_col']
        distances = rule['distances']
        output = rule['output']
        
        # Compute distance field
        matrix = np.array(grid.cells)
        mask = (matrix == dist_col)
        if np.any(mask):
            target_coords = np.argwhere(mask).astype(float)
            r_mesh, c_mesh = np.indices((h, w))
            coords = np.stack([r_mesh, c_mesh], axis=-1).astype(float)
            deltas = coords[:, :, np.newaxis, :] - target_coords[np.newaxis, np.newaxis, :, :]
            dists = np.min(np.sum(np.abs(deltas), axis=-1), axis=-1)
            
            for r in range(h):
                for c in range(w):
                    if cells[r][c] == target:
                        if round(dists[r, c], 0) in distances:
                            cells[r][c] = output
    
    elif rule['type'] == 'object_frame':
        target = rule['colour']
        output = rule['output']
        objects = segment_objects(grid)
        for obj in objects:
            if obj.colour == target and obj.is_frame:
                for r, c in obj.cells:
                    cells[r][c] = output
    
    elif rule['type'] == 'neighbour_count':
        target = rule['colour']
        count = rule['count']
        output = rule['output']
        for r in range(h):
            for c in range(w):
                if cells[r][c] == target:
                    n_nz = sum(1 for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                              if 0 <= r+dr < h and 0 <= c+dc < w and grid.cells[r+dr][c+dc] != 0)
                    if n_nz == count:
                        cells[r][c] = output
    
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# 4. MAIN PREDICTOR
# ═══════════════════════════════════════════════════════════════════

def predict(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Discover and apply composition rules."""
    # Check same-size
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    train_pairs = [(p.input, p.output) for p in task.train]
    
    try:
        signal.setitimer(signal.ITIMER_REAL, 20.0)
        rule = discover_rules(train_pairs)
        signal.setitimer(signal.ITIMER_REAL, 0)
    except:
        signal.setitimer(signal.ITIMER_REAL, 0)
        return None
    
    if rule is None:
        return None
    
    test_input = task.test[0].input
    pred = apply_rule(rule, test_input)
    
    src = f"grammar_{rule['type']}"
    return pred, src, {'rule': rule}


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
    
    print(f"\n═══ Composition Grammar ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources: {sources}")
