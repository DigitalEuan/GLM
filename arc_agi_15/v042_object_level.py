"""
v042_object_level.py — Object-Level Reasoning for ARC
======================================================

Implements object-level reasoning using UBP principles:

LAW_PATTERN_001: "Visual puzzles are coherence maps; the OnBit state
(NRCI 1.0) identifies the solution that completes the grid."

LAW_OPTICAL_TOGGLE_001: "Light propagates via a neighbor-dependent
toggle rule; 3, 6, and 9 are the resonant modes."

LAW_TGIC_369_GENESIS: "3-Axis Orthogonality (Hamming 4), 6-Face
Coherence, and the 9-Neighbor Connectivity Limit."

LAW_TOPOLOGICAL_ERASURE_001: "The substrate prioritizes geometric
stability over conservation of magnitude."

Approach:
1. Segment grid into objects (connected components)
2. For each object, compute properties (size, shape, colour, position)
3. Match objects between input and output
4. Derive per-object transformation rules
5. Apply rules to test input objects

Key insight: ARC tasks transform OBJECTS, not CELLS.
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
# 1. OBJECT SEGMENTATION
# ═══════════════════════════════════════════════════════════════════

class ARCObject:
    """Represents a connected component (object) in an ARC grid."""
    
    def __init__(self, cells: List[Tuple[int, int]], colour: int, 
                 grid_height: int, grid_width: int):
        self.cells = sorted(cells)
        self.colour = colour
        self.size = len(cells)
        self.grid_h = grid_height
        self.grid_w = grid_width
        
        # Bounding box
        self.min_r = min(r for r, c in cells)
        self.max_r = max(r for r, c in cells)
        self.min_c = min(c for r, c in cells)
        self.max_c = max(c for r, c in cells)
        self.bbox_h = self.max_r - self.min_r + 1
        self.bbox_w = self.max_c - self.min_c + 1
        
        # Centroid
        self.centroid_r = sum(r for r, c in cells) / len(cells)
        self.centroid_c = sum(c for r, c in cells) / len(cells)
        
        # Shape signature (normalized to bbox)
        self.normalized_cells = frozenset((r - self.min_r, c - self.min_c) for r, c in cells)
        
        # Density (cells / bbox area)
        self.density = self.size / (self.bbox_h * self.bbox_w) if self.bbox_h * self.bbox_w > 0 else 0
        
        # Is it a frame? (has interior zeros)
        self.is_frame = self._check_frame()
        
        # Neighbour colours (4-connected, outside the object)
        self.border_neighbours = set()
    
    def _check_frame(self) -> bool:
        """Check if object forms a hollow frame."""
        if self.size < 4:
            return False
        if self.bbox_h < 3 or self.bbox_w < 3:
            return False
        # Check if interior of bbox has cells NOT in the object
        cell_set = set(self.cells)
        interior_empty = False
        for r in range(self.min_r + 1, self.max_r):
            for c in range(self.min_c + 1, self.max_c):
                if (r, c) not in cell_set:
                    interior_empty = True
                    break
            if interior_empty:
                break
        return interior_empty and self.density < 0.8
    
    def shape_hash(self) -> str:
        """Hash of the normalized shape (translation-invariant)."""
        return hash(self.normalized_cells)
    
    def __repr__(self):
        return (f"Object(col={self.colour}, size={self.size}, "
                f"bbox={self.bbox_h}x{self.bbox_w}, "
                f"pos=({self.min_r},{self.min_c}), "
                f"frame={self.is_frame})")


def segment_objects(grid: Grid) -> List[ARCObject]:
    """Segment a grid into connected components (objects)."""
    h, w = grid.height, grid.width
    visited = set()
    objects = []
    
    for r in range(h):
        for c in range(w):
            if (r, c) in visited or grid.cells[r][c] == 0:
                continue
            
            colour = grid.cells[r][c]
            comp = []
            queue = deque([(r, c)])
            visited.add((r, c))
            
            while queue:
                cr, cc = queue.popleft()
                comp.append((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w 
                        and (nr, nc) not in visited 
                        and grid.cells[nr][nc] == colour):
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            
            obj = ARCObject(comp, colour, h, w)
            
            # Compute border neighbours
            for or_, oc in comp:
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = or_ + dr, oc + dc
                    if 0 <= nr < h and 0 <= nc < w:
                        n_col = grid.cells[nr][nc]
                        if n_col != colour:
                            obj.border_neighbours.add(n_col)
            
            objects.append(obj)
    
    return objects


# ═══════════════════════════════════════════════════════════════════
# 2. OBJECT MATCHING (between input and output)
# ═══════════════════════════════════════════════════════════════════

def match_objects(in_objects: List[ARCObject], 
                  out_objects: List[ARCObject]) -> Dict[int, int]:
    """
    Match input objects to output objects.
    Returns: {input_obj_index: output_obj_index}
    
    Matching strategy: find objects with the same shape and position.
    """
    matches = {}
    used_out = set()
    
    for i, in_obj in enumerate(in_objects):
        best_match = -1
        best_score = -1
        
        for j, out_obj in enumerate(out_objects):
            if j in used_out:
                continue
            
            # Score: overlap of cells
            in_set = set(in_obj.cells)
            out_set = set(out_obj.cells)
            overlap = len(in_set & out_set)
            
            # Also check shape similarity
            shape_match = (in_obj.normalized_cells == out_obj.normalized_cells)
            
            score = overlap + (1000 if shape_match else 0)
            
            if score > best_score:
                best_score = score
                best_match = j
        
        if best_match >= 0 and best_score > 0:
            matches[i] = best_match
            used_out.add(best_match)
    
    return matches


# ═══════════════════════════════════════════════════════════════════
# 3. OBJECT TRANSFORMATION RULES
# ═══════════════════════════════════════════════════════════════════

def derive_object_rules(train_pairs: List[Tuple[Grid, Grid]]) -> Optional[Dict]:
    """
    Derive per-object transformation rules from train pairs.
    
    For each matched pair of (input_object, output_object):
    - What colour does it become?
    - Does it move? (centroid shift)
    - Does it change shape? (normalized cells change)
    - Does it change size?
    """
    all_rules = []
    
    for inp, out in train_pairs:
        if inp.height != out.height or inp.width != out.width:
            return None
        
        in_objects = segment_objects(inp)
        out_objects = segment_objects(out)
        
        matches = match_objects(in_objects, out_objects)
        
        for in_idx, out_idx in matches.items():
            in_obj = in_objects[in_idx]
            out_obj = out_objects[out_idx]
            
            rule = {
                'in_colour': in_obj.colour,
                'out_colour': out_obj.colour,
                'in_size': in_obj.size,
                'out_size': out_obj.size,
                'in_shape': in_obj.normalized_cells,
                'out_shape': out_obj.normalized_cells,
                'centroid_dr': out_obj.centroid_r - in_obj.centroid_r,
                'centroid_dc': out_obj.centroid_c - in_obj.centroid_c,
                'is_frame': in_obj.is_frame,
                'border_neighbours': frozenset(in_obj.border_neighbours),
            }
            all_rules.append(rule)
    
    if not all_rules:
        return None
    
    # Find consistent rules
    # Group by (in_colour, is_frame, border_neighbours)
    rule_groups = {}
    for rule in all_rules:
        key = (rule['in_colour'], rule['is_frame'], rule['border_neighbours'])
        if key not in rule_groups:
            rule_groups[key] = []
        rule_groups[key].append(rule)
    
    # For each group, find the most common transformation
    final_rules = {}
    for key, rules in rule_groups.items():
        # Most common output colour
        out_cols = Counter(r['out_colour'] for r in rules)
        most_common_col = out_cols.most_common(1)[0][0]
        
        # Check if shape changes
        shape_changes = any(r['in_shape'] != r['out_shape'] for r in rules)
        
        # Check if position changes
        pos_changes = any(r['centroid_dr'] != 0 or r['centroid_dc'] != 0 for r in rules)
        
        final_rules[key] = {
            'out_colour': most_common_col,
            'shape_changes': shape_changes,
            'pos_changes': pos_changes,
        }
    
    return {'type': 'object_rules', 'rules': final_rules}


# ═══════════════════════════════════════════════════════════════════
# 4. COHERENCE-BASED PREDICTION (LAW_PATTERN_001)
# ═══════════════════════════════════════════════════════════════════

def compute_grid_coherence(grid: Grid) -> float:
    """
    Compute NRCI-based coherence for a grid.
    LAW_PATTERN_001: "Visual puzzles are coherence maps;
    the OnBit state (NRCI 1.0) identifies the solution."
    """
    h, w = grid.height, grid.width
    
    # Simple coherence: count cells that match their expected pattern
    # (neighbour consistency)
    consistent = 0
    total = 0
    
    for r in range(h):
        for c in range(w):
            col = grid.cells[r][c]
            if col == 0:
                continue
            
            # Check if neighbours are consistent
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    total += 1
                    if grid.cells[nr][nc] == col or grid.cells[nr][nc] == 0:
                        consistent += 1
    
    return consistent / max(total, 1)


def predict_coherence(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    LAW_PATTERN_001: Find the output that maximizes coherence.
    
    For each train pair, compute input and output coherence.
    The output should have higher coherence.
    """
    # Check if outputs consistently have higher coherence than inputs
    higher_coherence = 0
    total_pairs = 0
    
    for pair in task.train:
        in_coh = compute_grid_coherence(pair.input)
        out_coh = compute_grid_coherence(pair.output)
        total_pairs += 1
        if out_coh >= in_coh:
            higher_coherence += 1
    
    if higher_coherence < total_pairs:
        return None  # Outputs don't consistently have higher coherence
    
    return None  # Placeholder — needs more sophisticated coherence maximization


# ═══════════════════════════════════════════════════════════════════
# 5. NEIGHBOUR-DEPENDENT TOGGLE (LAW_OPTICAL_TOGGLE_001)
# ═══════════════════════════════════════════════════════════════════

def try_neighbour_toggle(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    LAW_OPTICAL_TOGGLE_001: "Light propagates via a neighbor-dependent
    toggle rule; 3, 6, and 9 are the resonant modes."
    
    Try: cells toggle based on neighbour count.
    If a cell has N non-zero neighbours, it changes to colour C.
    """
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Build rule: (input_colour, n_nonzero_neighbours) → output_colour
    rule_counts = Counter()
    
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                if ic == oc:
                    continue
                
                n_nonzero = 0
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and pair.input.cells[nr][nc] != 0:
                        n_nonzero += 1
                
                rule_counts[(ic, n_nonzero, oc)] += 1
    
    n_pairs = len(task.train)
    consistent = [(k, v) for k, v in rule_counts.items() if v >= n_pairs]
    consistent.sort(key=lambda x: -x[1])
    
    for (ic, n_nz, oc), _ in consistent[:10]:
        all_pass = True
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            cells = [row[:] for row in pair.input.cells]
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] == ic:
                        n_nz_actual = 0
                        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < h and 0 <= nc < w and pair.input.cells[nr][nc] != 0:
                                n_nz_actual += 1
                        if n_nz_actual == n_nz:
                            cells[r][c] = oc
            if not grids_equal(Grid(cells), pair.output):
                all_pass = False
                break
        
        if all_pass:
            test = task.test[0].input
            h, w = test.height, test.width
            cells = [row[:] for row in test.cells]
            for r in range(h):
                for c in range(w):
                    if test.cells[r][c] == ic:
                        n_nz_actual = 0
                        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < h and 0 <= nc < w and test.cells[nr][nc] != 0:
                                n_nz_actual += 1
                        if n_nz_actual == n_nz:
                            cells[r][c] = oc
            pred = Grid(cells)
            return pred, f"toggle_{ic}_n{n_nz}_to_{oc}"
    
    return None


# ═══════════════════════════════════════════════════════════════════
# 6. OBJECT-LEVEL RECOLOUR
# ═══════════════════════════════════════════════════════════════════

def try_object_recolour(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Object-level recolour: objects of colour X with property P → colour Y.
    
    Properties:
    - is_frame: object forms a hollow frame
    - size: number of cells
    - border_neighbours: colours adjacent to the object
    - density: cells / bbox area
    """
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # For each train pair, compute object transformations
    all_transforms = []
    
    for pair in task.train:
        in_objects = segment_objects(pair.input)
        out_objects = segment_objects(pair.output)
        matches = match_objects(in_objects, out_objects)
        
        for in_idx, out_idx in matches.items():
            in_obj = in_objects[in_idx]
            out_obj = out_objects[out_idx]
            
            if in_obj.colour != out_obj.colour:
                all_transforms.append({
                    'in_colour': in_obj.colour,
                    'out_colour': out_obj.colour,
                    'is_frame': in_obj.is_frame,
                    'size': in_obj.size,
                    'density': in_obj.density,
                    'border_neighbours': frozenset(in_obj.border_neighbours),
                    'bbox_h': in_obj.bbox_h,
                    'bbox_w': in_obj.bbox_w,
                })
    
    if not all_transforms:
        return None
    
    # Find consistent rules
    # Try: colour X + is_frame → Y
    for key_field in ['is_frame', 'border_neighbours']:
        rule_groups = {}
        for t in all_transforms:
            key = (t['in_colour'], t[key_field])
            if key not in rule_groups:
                rule_groups[key] = []
            rule_groups[key].append(t['out_colour'])
        
        for key, out_cols in rule_groups.items():
            if len(set(out_cols)) == 1:
                # Consistent rule
                in_col, prop = key
                out_col = out_cols[0]
                
                # Verify on all train pairs
                all_pass = True
                for pair in task.train:
                    in_objects = segment_objects(pair.input)
                    cells = [row[:] for row in pair.input.cells]
                    
                    for obj in in_objects:
                        if obj.colour == in_col:
                            apply = False
                            if key_field == 'is_frame' and obj.is_frame == prop:
                                apply = True
                            elif key_field == 'border_neighbours' and frozenset(obj.border_neighbours) == prop:
                                apply = True
                            
                            if apply:
                                for r, c in obj.cells:
                                    cells[r][c] = out_col
                    
                    if not grids_equal(Grid(cells), pair.output):
                        all_pass = False
                        break
                
                if all_pass:
                    test = task.test[0].input
                    in_objects = segment_objects(test)
                    cells = [row[:] for row in test.cells]
                    
                    for obj in in_objects:
                        if obj.colour == in_col:
                            apply = False
                            if key_field == 'is_frame' and obj.is_frame == prop:
                                apply = True
                            elif key_field == 'border_neighbours' and frozenset(obj.border_neighbours) == prop:
                                apply = True
                            
                            if apply:
                                for r, c in obj.cells:
                                    cells[r][c] = out_col
                    
                    pred = Grid(cells)
                    return pred, f"obj_{key_field}_{in_col}_{prop}_to_{out_col}"
    
    return None


# ═══════════════════════════════════════════════════════════════════
# 7. MAIN PREDICTOR
# ═══════════════════════════════════════════════════════════════════

def predict(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Try object-level approaches."""
    strategies = [
        ("toggle", try_neighbour_toggle),
        ("object_recolour", try_object_recolour),
    ]
    
    for name, fn in strategies:
        try:
            signal.setitimer(signal.ITIMER_REAL, 15.0)
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
    
    print(f"\n═══ Object Level ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources: {sources}")
