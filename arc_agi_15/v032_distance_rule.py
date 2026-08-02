"""
v032_distance_rule.py — Manhattan distance-based rule discovery
================================================================

The 396d80d7 breakthrough: cells at specific Manhattan distances from
objects change to specific colours based on geometric relationships.

This module generalises that pattern:
1. For each background cell, compute distance to nearest object cell
2. Find which distance values consistently predict changes
3. Apply the rule with appropriate colour derivation

This is a NEW category of rule beyond geometric ops and colour mapping.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Set
from collections import Counter
import sys, os, signal

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
# DISTANCE COMPUTATION
# ═══════════════════════════════════════════════════════════════════

def manhattan_distances(grid: Grid, bg_colour: int = 0) -> List[List[int]]:
    """Compute Manhattan distance from each bg cell to nearest non-bg cell."""
    h, w = grid.height, grid.width
    non_bg = set()
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] != bg_colour:
                non_bg.add((r, c))
    
    if not non_bg:
        return [[999] * w for _ in range(h)]
    
    dists = []
    for r in range(h):
        row = []
        for c in range(w):
            if grid.cells[r][c] != bg_colour:
                row.append(0)
            else:
                d = min(abs(r-nr) + abs(c-nc) for nr, nc in non_bg)
                row.append(d)
        dists.append(row)
    return dists


def has_diagonal_non_bg(grid: Grid, r: int, c: int, bg_colour: int = 0) -> bool:
    """Check if cell (r,c) has a diagonal neighbour that is non-bg."""
    h, w = grid.height, grid.width
    for dr in [-1, 1]:
        for dc in [-1, 1]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] != bg_colour:
                return True
    return False


def has_cardinal_non_bg(grid: Grid, r: int, c: int, bg_colour: int = 0) -> bool:
    """Check if cell (r,c) has a cardinal (4-connected) non-bg neighbour."""
    h, w = grid.height, grid.width
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] != bg_colour:
            return True
    return False


# ═══════════════════════════════════════════════════════════════════
# RULE: DISTANCE + DIAGNOAL FILTER (the 396d80d7 pattern)
# ═══════════════════════════════════════════════════════════════════

def try_distance_diagonal_rule(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Rule: bg-cells at specific Manhattan distance from objects,
    filtered by diagonal adjacency, change to a derived colour.
    
    Generalised from 396d80d7 where:
    - bg = 7
    - distance = 2
    - filter = has diagonal non-bg neighbour
    - colour = minority non-bg colour
    """
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Find the background colour (most common colour in input)
    all_cols = Counter()
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                all_cols[pair.input.cells[r][c]] += 1
    
    bg_candidates = [col for col, _ in all_cols.most_common(3)]
    
    for bg_col in bg_candidates:
        # For each candidate bg, find the distance pattern
        distance_counts = Counter()
        
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            dists = manhattan_distances(pair.input, bg_col)
            
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] == bg_col and pair.output.cells[r][c] != bg_col:
                        d = dists[r][c]
                        diag = has_diagonal_non_bg(pair.input, r, c, bg_col)
                        card = has_cardinal_non_bg(pair.input, r, c, bg_col)
                        distance_counts[(d, diag, card)] += 1
        
        if not distance_counts:
            continue
        
        # Find the most common (distance, diag, card) pattern
        for (target_dist, need_diag, need_card), count in distance_counts.most_common():
            if count < 2:  # Need at least 2 observations
                continue
            
            # Derive fill colour PER-PAIR as minority non-bg colour
            # First verify the rule works with per-pair fill
            all_pass = True
            for pair in task.train:
                h, w = pair.input.height, pair.input.width
                dists = manhattan_distances(pair.input, bg_col)
                
                non_bg_cols = Counter()
                for r in range(h):
                    for c in range(w):
                        if pair.input.cells[r][c] != bg_col:
                            non_bg_cols[pair.input.cells[r][c]] += 1
                
                if len(non_bg_cols) < 2:
                    all_pass = False
                    break
                
                pair_fill = non_bg_cols.most_common()[-1][0]
                
                cells = [row[:] for row in pair.input.cells]
                for r in range(h):
                    for c in range(w):
                        if pair.input.cells[r][c] == bg_col:
                            d = dists[r][c]
                            diag = has_diagonal_non_bg(pair.input, r, c, bg_col)
                            card = has_cardinal_non_bg(pair.input, r, c, bg_col)
                            if d == target_dist:
                                if need_diag and not diag:
                                    continue
                                if need_card and not card:
                                    continue
                                cells[r][c] = pair_fill
                
                if not grids_equal(Grid(cells), pair.output):
                    all_pass = False
                    break
            
            if not all_pass:
                continue
            
            colour_source = "minority_per_pair"
            
            # Apply to test with per-test fill colour
            test_input = task.test[0].input
            h, w = test_input.height, test_input.width
            dists = manhattan_distances(test_input, bg_col)
            
            non_bg_cols_test = Counter()
            for r in range(h):
                for c in range(w):
                    if test_input.cells[r][c] != bg_col:
                        non_bg_cols_test[test_input.cells[r][c]] += 1
            
            if len(non_bg_cols_test) >= 2:
                test_fill = non_bg_cols_test.most_common()[-1][0]
            else:
                test_fill = list(non_bg_cols_test.keys())[0] if non_bg_cols_test else 0
            
            cells = [row[:] for row in test_input.cells]
            for r in range(h):
                for c in range(w):
                    if test_input.cells[r][c] == bg_col:
                        d = dists[r][c]
                        diag = has_diagonal_non_bg(test_input, r, c, bg_col)
                        card = has_cardinal_non_bg(test_input, r, c, bg_col)
                        
                        if d == target_dist:
                            if need_diag and not diag:
                                continue
                            if need_card and not card:
                                continue
                            cells[r][c] = test_fill
            
            pred = Grid(cells)
            src = f"dist_d{target_dist}_{'diag' if need_diag else ''}{'card' if need_card else ''}_{colour_source}"
            return pred, src
    
    return None


# ═══════════════════════════════════════════════════════════════════
# RULE: SIMPLE DISTANCE FILL (distance D → colour C)
# ═══════════════════════════════════════════════════════════════════

def try_simple_distance_fill(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Simpler version: bg cells at distance D become colour C."""
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
        # Collect (distance → colour) mappings
        dist_colour = {}  # distance → colour
        consistent = True
        
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            dists = manhattan_distances(pair.input, bg_col)
            
            pair_dist_col = {}
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] == bg_col and pair.output.cells[r][c] != bg_col:
                        d = dists[r][c]
                        oc = pair.output.cells[r][c]
                        if d in pair_dist_col:
                            if pair_dist_col[d] != oc:
                                consistent = False
                                break
                        else:
                            pair_dist_col[d] = oc
                if not consistent:
                    break
            
            if not consistent:
                break
            
            for d, col in pair_dist_col.items():
                if d in dist_colour:
                    if dist_colour[d] != col:
                        consistent = False
                        break
                else:
                    dist_colour[d] = col
        
        if not consistent or not dist_colour:
            continue
        
        # Verify
        all_pass = True
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            dists = manhattan_distances(pair.input, bg_col)
            cells = [row[:] for row in pair.input.cells]
            
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] == bg_col:
                        d = dists[r][c]
                        if d in dist_colour:
                            cells[r][c] = dist_colour[d]
            
            if not grids_equal(Grid(cells), pair.output):
                all_pass = False
                break
        
        if all_pass:
            test_input = task.test[0].input
            h, w = test_input.height, test_input.width
            dists = manhattan_distances(test_input, bg_col)
            cells = [row[:] for row in test_input.cells]
            
            for r in range(h):
                for c in range(w):
                    if test_input.cells[r][c] == bg_col:
                        d = dists[r][c]
                        if d in dist_colour:
                            cells[r][c] = dist_colour[d]
            
            pred = Grid(cells)
            return pred, f"simple_dist_fill_{dist_colour}"
    
    return None


# ═══════════════════════════════════════════════════════════════════
# MAIN PREDICTOR
# ═══════════════════════════════════════════════════════════════════

def predict(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Try distance-based rules."""
    strategies = [
        ("distance_diagonal", try_distance_diagonal_rule),
        ("simple_distance_fill", try_simple_distance_fill),
    ]
    
    for name, fn in strategies:
        try:
            result = fn(task)
            if result is not None:
                pred, src = result
                return pred, src, {"strategy": name}
        except Exception as e:
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
    
    print(f"\n═══ Distance Rules ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources: {sources}")
