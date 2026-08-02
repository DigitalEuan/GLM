"""
v030_recolour_enhanced.py — Enhanced recolour candidate generation
=================================================================

Addresses the gap where consistent recolour tasks and neighbourhood-aware
conditional recolour tasks get no candidates from the current pipeline.

Strategies:
1. CONSISTENT_RECOLOUR: exact per-colour mapping from train pairs
2. CONDITIONAL_RECOLOUR: neighbourhood-aware mapping (8-neighbour signature → output colour)
3. POSITIONAL_RECOLOUR: position-dependent colour mapping (row, col → output colour)
4. OBJECT_RECOLOUR: connected-component-aware recolouring
5. MULTI_STEP: compose position-op + recolour (crop→recolour, rotate→recolour, etc.)
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set
from fractions import Fraction
from collections import Counter, defaultdict
import sys, os, time, signal

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_VENDOR_DIR = os.path.join(_THIS_DIR, "vendor")
if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task
from dsl.arc_dsl_full import Ops, Operation, Program


class _OpTimeout(Exception):
    pass

def _alarm_handler(s, f):
    raise _OpTimeout()

signal.signal(signal.SIGALRM, _alarm_handler)

def _apply_timed(prog, grid, seconds=1.5):
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return prog.apply(grid)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def _train_pass(task: ARCTask, prog: Program) -> bool:
    for pair in task.train:
        try:
            if _apply_timed(prog, pair.input) != pair.output:
                return False
        except Exception:
            return False
    return True


# ═══════════════════════════════════════════════════════════════════
# STRATEGY 1: Consistent Recolour
# ═══════════════════════════════════════════════════════════════════

def try_consistent_recolour(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """If every train pair has the same input→output colour mapping, apply it."""
    # Only works for same-size grids
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Build mapping from first pair
    mapping = {}
    for r in range(task.train[0].input.height):
        for c in range(task.train[0].input.width):
            ic = task.train[0].input.cells[r][c]
            oc = task.train[0].output.cells[r][c]
            if ic in mapping:
                if mapping[ic] != oc:
                    return None  # Inconsistent within first pair
            else:
                mapping[ic] = oc
    
    # Verify on all other pairs
    for pair in task.train[1:]:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                ic = pair.input.cells[r][c]
                oc = pair.output.cells[r][c]
                if mapping.get(ic, ic) != oc:
                    return None
    
    if all(k == v for k, v in mapping.items()):
        return None  # Identity — not interesting
    
    prog = Program([Operation(Ops.RECOLOUR, {"mapping": mapping})])
    test_input = task.test[0].input
    try:
        pred = _apply_timed(prog, test_input)
        return pred, "consistent_recolour"
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════
# STRATEGY 2: Neighbourhood-Aware Conditional Recolour
# ═══════════════════════════════════════════════════════════════════

def _get_neighbours(grid: Grid, r: int, c: int) -> List[int]:
    """Get 8-neighbour colours (out-of-bounds = -1)."""
    neighbours = []
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < grid.height and 0 <= nc < grid.width:
                neighbours.append(grid.cells[nr][nc])
            else:
                neighbours.append(-1)
    return neighbours


def _neighbour_signature(neighbours: List[int]) -> Tuple[int, ...]:
    """Create a hashable signature from neighbour colours."""
    return tuple(sorted(neighbours))


def try_conditional_recolour(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Learn per-(input_colour, neighbour_signature) → output_colour rules.
    If a consistent rule exists for all observed cells, apply it.
    """
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Build rule table: (input_colour, neighbour_sig) → output_colour
    rules: Dict[Tuple[int, Tuple[int, ...]], int] = {}
    rule_counts: Dict[Tuple[int, Tuple[int, ...]], Counter] = defaultdict(Counter)
    
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                ic = pair.input.cells[r][c]
                oc = pair.output.cells[r][c]
                neighbours = _get_neighbours(pair.input, r, c)
                sig = _neighbour_signature(neighbours)
                key = (ic, sig)
                rule_counts[key][oc] += 1
    
    # Build consistent rules (majority vote)
    for key, counts in rule_counts.items():
        most_common = counts.most_common(1)[0]
        rules[key] = most_common[0]
    
    # Apply to test
    test_input = task.test[0].input
    h, w = test_input.height, test_input.width
    new_cells = []
    for r in range(h):
        row = []
        for c in range(w):
            ic = test_input.cells[r][c]
            neighbours = _get_neighbours(test_input, r, c)
            sig = _neighbour_signature(neighbours)
            key = (ic, sig)
            if key in rules:
                row.append(rules[key])
            else:
                row.append(ic)  # Fallback to identity
        new_cells.append(row)
    
    pred = Grid(h, w, new_cells)
    
    # Verify on train
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        cells = []
        for r in range(h):
            row = []
            for c in range(w):
                ic = pair.input.cells[r][c]
                neighbours = _get_neighbours(pair.input, r, c)
                sig = _neighbour_signature(neighbours)
                key = (ic, sig)
                if key in rules:
                    row.append(rules[key])
                else:
                    row.append(ic)
            cells.append(row)
        if Grid(h, w, cells) != pair.output:
            return None
    
    return pred, "conditional_recolour"


# ═══════════════════════════════════════════════════════════════════
# STRATEGY 3: Positional Recolour
# ═══════════════════════════════════════════════════════════════════

def try_positional_recolour(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Learn per-(input_colour, row_mod, col_mod) → output_colour.
    Uses modular arithmetic to handle periodic patterns.
    """
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Try different modularities
    for mod_r in range(1, min(8, task.train[0].input.height + 1)):
        for mod_c in range(1, min(8, task.train[0].input.width + 1)):
            rules: Dict[Tuple[int, int, int], int] = {}
            consistent = True
            
            for pair in task.train:
                for r in range(pair.input.height):
                    for c in range(pair.input.width):
                        ic = pair.input.cells[r][c]
                        oc = pair.output.cells[r][c]
                        key = (ic, r % mod_r, c % mod_c)
                        if key in rules:
                            if rules[key] != oc:
                                consistent = False
                                break
                        else:
                            rules[key] = oc
                    if not consistent:
                        break
                if not consistent:
                    break
            
            if not consistent:
                continue
            
            # Check it's not identity
            if all(k[0] == v for k, v in rules.items()):
                continue
            
            # Apply to test
            test_input = task.test[0].input
            h, w = test_input.height, test_input.width
            new_cells = []
            for r in range(h):
                row = []
                for c in range(w):
                    ic = test_input.cells[r][c]
                    key = (ic, r % mod_r, c % mod_c)
                    row.append(rules.get(key, ic))
                new_cells.append(row)
            pred = Grid(h, w, new_cells)
            
            return pred, f"positional_recolour_{mod_r}x{mod_c}"
    
    return None


# ═══════════════════════════════════════════════════════════════════
# STRATEGY 4: Connected-Component Recolour
# ═══════════════════════════════════════════════════════════════════

def _find_objects(grid: Grid) -> List[List[Tuple[int, int]]]:
    """Find connected components (4-connected) of non-zero cells."""
    visited = set()
    objects = []
    
    for r in range(grid.height):
        for c in range(grid.width):
            if (r, c) in visited or grid.cells[r][c] == 0:
                continue
            # BFS
            obj = []
            queue = [(r, c)]
            visited.add((r, c))
            while queue:
                cr, cc = queue.pop(0)
                obj.append((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if (0 <= nr < grid.height and 0 <= nc < grid.width
                        and (nr, nc) not in visited
                        and grid.cells[nr][nc] != 0):
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            objects.append(obj)
    return objects


def try_object_recolour(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    For each connected component, learn a recolour based on object properties
    (size, bounding box, dominant colour).
    """
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Build object-level mapping
    object_rules = []
    for pair in task.train:
        in_objects = _find_objects(pair.input)
        out_objects = _find_objects(pair.output)
        
        if len(in_objects) != len(out_objects):
            return None  # Object count changed — not a pure recolour
        
        for inp_obj, out_obj in zip(in_objects, out_objects):
            if len(inp_obj) != len(out_obj):
                return None  # Object shape changed
            
            # Sort by position
            inp_obj.sort()
            out_obj.sort()
            
            for (ir, ic), (or_, oc) in zip(inp_obj, out_obj):
                inp_col = pair.input.cells[ir][ic]
                out_col = pair.output.cells[or_][oc]
                if inp_col != out_col:
                    object_rules.append((inp_col, out_col))
    
    if not object_rules:
        return None
    
    # Check if it's just a consistent recolour (already handled by strategy 1)
    mapping = {}
    for ic, oc in object_rules:
        if ic in mapping and mapping[ic] != oc:
            return None  # Inconsistent
        mapping[ic] = oc
    
    # Already handled by consistent_recolour
    return None


# ═══════════════════════════════════════════════════════════════════
# STRATEGY 5: Multi-Step (Position Op + Recolour)
# ═══════════════════════════════════════════════════════════════════

_POSITION_OPS = [
    Ops.ROTATE_90, Ops.ROTATE_180, Ops.ROTATE_270,
    Ops.FLIP_H, Ops.FLIP_V, Ops.TRANSPOSE,
    Ops.GRAVITY_DOWN, Ops.GRAVITY_UP, Ops.GRAVITY_LEFT, Ops.GRAVITY_RIGHT,
]


def try_multi_step(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Try: position-op → recolour (derived from train pairs).
    For each position op, apply to train inputs, then derive recolour mapping.
    """
    test_input = task.test[0].input
    
    for pos_op in _POSITION_OPS:
        try:
            # Apply position op to all train inputs
            transformed_pairs = []
            for pair in task.train:
                t_prog = Program([Operation(pos_op)])
                t_input = _apply_timed(t_prog, pair.input)
                transformed_pairs.append((t_input, pair.output))
            
            # Check sizes match
            if any(tp.height != op.height or tp.width != op.width 
                   for tp, op in transformed_pairs):
                continue
            
            # Derive recolour mapping
            mapping = {}
            consistent = True
            for tp, op in transformed_pairs:
                for r in range(tp.height):
                    for c in range(tp.width):
                        ic, oc = tp.cells[r][c], op.cells[r][c]
                        if ic in mapping:
                            if mapping[ic] != oc:
                                consistent = False
                                break
                        else:
                            mapping[ic] = oc
                    if not consistent:
                        break
                if not consistent:
                    break
            
            if not consistent:
                continue
            
            if all(k == v for k, v in mapping.items()):
                continue  # Identity after transform — just the position op
            
            # Build composed program
            prog = Program([Operation(pos_op), Operation(Ops.RECOLOUR, {"mapping": mapping})])
            if _train_pass(task, prog):
                pred = _apply_timed(prog, test_input)
                return pred, f"multi_step_{pos_op.name}_recolour"
        except Exception:
            continue
    
    return None


# ═══════════════════════════════════════════════════════════════════
# STRATEGY 6: Size-Change Operations (crop, tile, scale)
# ═══════════════════════════════════════════════════════════════════

def try_size_change_ops(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Try DSL ops that change grid size."""
    size_change_ops = [
        Ops.CROP_TO_NONZERO, Ops.TILE_2X,
        Ops.SCALE_2X, Ops.SCALE_HALF,
    ]
    
    for op in size_change_ops:
        try:
            prog = Program([Operation(op)])
            if _train_pass(task, prog):
                pred = _apply_timed(prog, task.test[0].input)
                return pred, f"size_change_{op.name}"
        except Exception:
            continue
    
    return None


# ═══════════════════════════════════════════════════════════════════
# STRATEGY 7: Neighbourhood-Aware with Cardinal Direction
# ═══════════════════════════════════════════════════════════════════

def try_directional_recolour(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Learn rules like: "if cell is colour A and has colour B in direction D, 
    change to colour C". More specific than full 8-neighbour signature.
    """
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    directions = [(-1,0,'N'), (1,0,'S'), (0,-1,'W'), (0,1,'E'),
                  (-1,-1,'NW'), (-1,1,'NE'), (1,-1,'SW'), (1,1,'SE')]
    
    # Build rules: (input_colour, direction, neighbour_colour) → output_colour
    rule_counts: Dict[Tuple[int, str, int], Counter] = defaultdict(Counter)
    
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                ic = pair.input.cells[r][c]
                oc = pair.output.cells[r][c]
                if ic == oc:
                    continue
                for dr, dc, dname in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < pair.input.height and 0 <= nc < pair.input.width:
                        nc_col = pair.input.cells[nr][nc]
                        key = (ic, dname, nc_col)
                        rule_counts[key][oc] += 1
    
    # Find consistent rules
    rules = {}
    for key, counts in rule_counts.items():
        most_common = counts.most_common(1)[0]
        if most_common[1] >= len(task.train):  # Must appear in all train pairs
            rules[key] = most_common[0]
    
    if not rules:
        return None
    
    # Apply to test
    test_input = task.test[0].input
    h, w = test_input.height, test_input.width
    new_cells = [row[:] for row in test_input.cells]  # Copy
    
    for r in range(h):
        for c in range(w):
            ic = test_input.cells[r][c]
            for dr, dc, dname in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    nc_col = test_input.cells[nr][nc]
                    key = (ic, dname, nc_col)
                    if key in rules:
                        new_cells[r][c] = rules[key]
                        break
    
    pred = Grid(h, w, new_cells)
    
    # Verify on train
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        cells = [row[:] for row in pair.input.cells]
        for r in range(h):
            for c in range(w):
                ic = pair.input.cells[r][c]
                for dr, dc, dname in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w:
                        nc_col = pair.input.cells[nr][nc]
                        key = (ic, dname, nc_col)
                        if key in rules:
                            cells[r][c] = rules[key]
                            break
        if Grid(h, w, cells) != pair.output:
            return None
    
    return pred, "directional_recolour"


# ═══════════════════════════════════════════════════════════════════
# MAIN PREDICTOR
# ═══════════════════════════════════════════════════════════════════

def predict_enhanced_recolour(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Try all enhanced recolour strategies in priority order."""
    
    strategies = [
        ("consistent_recolour", try_consistent_recolour, 1),
        ("conditional_recolour", try_conditional_recolour, 2),
        ("directional_recolour", try_directional_recolour, 2),
        ("positional_recolour", try_positional_recolour, 3),
        ("multi_step", try_multi_step, 4),
        ("size_change_ops", try_size_change_ops, 5),
    ]
    
    for name, fn, priority in strategies:
        try:
            result = fn(task)
            if result is not None:
                pred, src = result
                return pred, src, {"strategy": name, "priority": priority}
        except Exception:
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
        
        result = predict_enhanced_recolour(task)
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
    
    print(f"\n═══ Enhanced Recolour ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources: {sources}")
