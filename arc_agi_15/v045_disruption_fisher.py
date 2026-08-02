"""
v045_disruption_fisher.py — Systematic Disruption Pattern Search
=================================================================

Applies all discovered disruption patterns across ALL task types.

Pattern catalogue (from disruption analysis):
1. Column-rank fill: fill = rank of column among columns with zeros
2. Row-rank fill: fill = rank of row among rows with zeros
3. Uniform fill: all zeros become colour X
4. Column-fill: each column gets a specific fill colour
5. Row-fill: each row gets a specific fill colour
6. Consistent recolour: all X become Y
7. Swap recolour: X↔Y swap
8. Conditional recolour: X→Y only if has neighbour Z
9. Distance fill: zeros at distance D from objects become colour X
10. Erase: non-zero cells become 0
11. Two-step: erase + fill
12. Composite: recolour + fill
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
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


def verify_and_predict(rule_fn, task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Verify rule on train pairs, apply to test."""
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Verify on train
    for pair in task.train:
        pred = rule_fn(pair.input)
        if pred is None or not grids_equal(pred, pair.output):
            return None
    
    # Apply to test
    pred = rule_fn(task.test[0].input)
    if pred is None:
        return None
    return pred


# ═══════════════════════════════════════════════════════════════════
# PATTERN 1: Column-Rank Fill
# ═══════════════════════════════════════════════════════════════════

def column_rank_fill(grid: Grid) -> Optional[Grid]:
    """Fill = rank of column among columns with zeros."""
    h, w = grid.height, grid.width
    zero_cols = sorted(set(c for r in range(h) for c in range(w) if grid.cells[r][c] == 0))
    if not zero_cols:
        return None
    col_rank = {c: (i % 9) + 1 for i, c in enumerate(zero_cols)}
    
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == 0:
                cells[r][c] = col_rank.get(c, 0)
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# PATTERN 2: Row-Rank Fill
# ═══════════════════════════════════════════════════════════════════

def row_rank_fill(grid: Grid) -> Optional[Grid]:
    """Fill = rank of row among rows with zeros."""
    h, w = grid.height, grid.width
    zero_rows = sorted(set(r for r in range(h) for c in range(w) if grid.cells[r][c] == 0))
    if not zero_rows:
        return None
    row_rank = {r: (i % 9) + 1 for i, r in enumerate(zero_rows)}
    
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == 0:
                cells[r][c] = row_rank.get(r, 0)
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# PATTERN 3: Uniform Fill (all zeros → X)
# ═══════════════════════════════════════════════════════════════════

def make_uniform_fill(fill_col: int):
    def rule(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == 0:
                    cells[r][c] = fill_col
        return Grid(cells)
    return rule


# ═══════════════════════════════════════════════════════════════════
# PATTERN 4: Column-Fill (each column → specific colour)
# ═══════════════════════════════════════════════════════════════════

def make_column_fill(col_map: Dict[int, int]):
    def rule(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == 0 and c in col_map:
                    cells[r][c] = col_map[c]
        return Grid(cells)
    return rule


# ═══════════════════════════════════════════════════════════════════
# PATTERN 5: Row-Fill (each row → specific colour)
# ═══════════════════════════════════════════════════════════════════

def make_row_fill(row_map: Dict[int, int]):
    def rule(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == 0 and r in row_map:
                    cells[r][c] = row_map[r]
        return Grid(cells)
    return rule


# ═══════════════════════════════════════════════════════════════════
# PATTERN 6: Consistent Recolour (all X → Y)
# ═══════════════════════════════════════════════════════════════════

def make_recolour(mapping: Dict[int, int]):
    def rule(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if cells[r][c] in mapping:
                    cells[r][c] = mapping[cells[r][c]]
        return Grid(cells)
    return rule


# ═══════════════════════════════════════════════════════════════════
# PATTERN 7: Conditional Recolour (X→Y if neighbour Z)
# ═══════════════════════════════════════════════════════════════════

def make_neighbour_recolour(in_col: int, n_col: int, out_col: int):
    def rule(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == in_col:
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] == n_col:
                            cells[r][c] = out_col
                            break
        return Grid(cells)
    return rule


# ═══════════════════════════════════════════════════════════════════
# PATTERN 8: Erase (non-zero → 0)
# ═══════════════════════════════════════════════════════════════════

def make_erase(colour: int):
    def rule(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if cells[r][c] == colour:
                    cells[r][c] = 0
        return Grid(cells)
    return rule


# ═══════════════════════════════════════════════════════════════════
# PATTERN 9: Two-step (erase + fill)
# ═══════════════════════════════════════════════════════════════════

def make_erase_fill(erase_map: Dict[int, int], fill_fn):
    """Erase first (recolour), then fill zeros."""
    def rule(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        # Step 1: erase/recolour
        for r in range(h):
            for c in range(w):
                if cells[r][c] in erase_map:
                    cells[r][c] = erase_map[cells[r][c]]
        # Step 2: fill
        intermediate = Grid(cells)
        filled = fill_fn(intermediate)
        return filled
    return rule


# ═══════════════════════════════════════════════════════════════════
# PATTERN 10: Position-dependent fill (fill at specific positions)
# ═══════════════════════════════════════════════════════════════════

def make_position_fill(positions: Dict[Tuple[int, int], int]):
    """Fill specific positions with specific colours."""
    def rule(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for (r, c), col in positions.items():
            if 0 <= r < h and 0 <= c < w and grid.cells[r][c] == 0:
                cells[r][c] = col
        return Grid(cells)
    return rule


# ═══════════════════════════════════════════════════════════════════
# SYSTEMATIC FISHER
# ═══════════════════════════════════════════════════════════════════

def fish(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Try all disruption patterns systematically."""
    
    # Check same-size
    same_size = all(p.input.height == p.output.height and p.input.width == p.output.width 
                    for p in task.train)
    if not same_size:
        return None
    
    # ═══ LEVEL 1: Simple fills ═══
    
    # 1a. Column-rank fill
    result = verify_and_predict(column_rank_fill, task)
    if result:
        return result, "column_rank_fill", {}
    
    # 1b. Row-rank fill
    result = verify_and_predict(row_rank_fill, task)
    if result:
        return result, "row_rank_fill", {}
    
    # ═══ LEVEL 2: Uniform fills ═══
    
    # Find all possible fill colours from train pairs
    fill_colours = set()
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    fill_colours.add(pair.output.cells[r][c])
    
    for fc in fill_colours:
        rule = make_uniform_fill(fc)
        result = verify_and_predict(rule, task)
        if result:
            return result, f"uniform_fill_{fc}", {}
    
    # ═══ LEVEL 3: Column/Row fills ═══
    
    # Build column fill map from train pairs
    col_map = {}
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    if c in col_map:
                        if col_map[c] != pair.output.cells[r][c]:
                            col_map[c] = None  # Inconsistent
                    else:
                        col_map[c] = pair.output.cells[r][c]
    col_map = {k: v for k, v in col_map.items() if v is not None}
    
    if col_map:
        rule = make_column_fill(col_map)
        result = verify_and_predict(rule, task)
        if result:
            return result, "column_fill", {}
    
    # Build row fill map
    row_map = {}
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    if r in row_map:
                        if row_map[r] != pair.output.cells[r][c]:
                            row_map[r] = None
                    else:
                        row_map[r] = pair.output.cells[r][c]
    row_map = {k: v for k, v in row_map.items() if v is not None}
    
    if row_map:
        rule = make_row_fill(row_map)
        result = verify_and_predict(rule, task)
        if result:
            return result, "row_fill", {}
    
    # ═══ LEVEL 4: Consistent recolour ═══
    
    recolour_map = {}
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                if ic != oc:
                    if ic in recolour_map:
                        if recolour_map[ic] != oc:
                            recolour_map[ic] = None
                    else:
                        recolour_map[ic] = oc
    recolour_map = {k: v for k, v in recolour_map.items() if v is not None and k != v}
    
    if recolour_map:
        rule = make_recolour(recolour_map)
        result = verify_and_predict(rule, task)
        if result:
            return result, f"recolour_{len(recolour_map)}", {}
    
    # ═══ LEVEL 5: Conditional recolour ═══
    
    # Find (in_col, n_col, out_col) triples
    triple_counts = Counter()
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                if ic == oc:
                    continue
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w:
                        n_col = pair.input.cells[nr][nc]
                        if n_col != 0 and n_col != ic:
                            triple_counts[(ic, n_col, oc)] += 1
    
    n_pairs = len(task.train)
    for (ic, n_col, oc), count in triple_counts.most_common(10):
        if count < n_pairs:
            continue
        rule = make_neighbour_recolour(ic, n_col, oc)
        result = verify_and_predict(rule, task)
        if result:
            return result, f"neighbour_{ic}_near_{n_col}_to_{oc}", {}
    
    # ═══ LEVEL 6: Two-step (erase + fill) ═══
    
    # Find erase mappings
    erase_candidates = {}
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                if ic != 0 and oc == 0:
                    if ic in erase_candidates:
                        if erase_candidates[ic] != 0:
                            erase_candidates[ic] = None
                    else:
                        erase_candidates[ic] = 0
    erase_map = {k: v for k, v in erase_candidates.items() if v is not None}
    
    if erase_map:
        # Try erase + each fill type
        for fc in fill_colours:
            rule = make_erase_fill(erase_map, make_uniform_fill(fc))
            result = verify_and_predict(rule, task)
            if result:
                return result, f"erase+fill_{fc}", {}
    
    # ═══ LEVEL 7: Consistent recolour + fill ═══
    
    if recolour_map and fill_colours:
        for fc in fill_colours:
            def make_recolour_fill(rm, fill_c):
                def rule(grid: Grid) -> Grid:
                    h, w = grid.height, grid.width
                    cells = [row[:] for row in grid.cells]
                    # Step 1: recolour
                    for r in range(h):
                        for c in range(w):
                            if cells[r][c] in rm:
                                cells[r][c] = rm[cells[r][c]]
                    # Step 2: fill zeros
                    for r in range(h):
                        for c in range(w):
                            if cells[r][c] == 0:
                                cells[r][c] = fill_c
                    return Grid(cells)
                return rule
            
            rule = make_recolour_fill(recolour_map, fc)
            result = verify_and_predict(rule, task)
            if result:
                return result, f"recolour+fill_{fc}", {}
    
    return None


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

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
    
    print("═" * 60)
    print(" DISRUPTION FISHER — Systematic Pattern Search")
    print("═" * 60)
    print()
    
    for fname in files:
        task = load_task(os.path.join(args.batch, fname),
                         name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1
        
        try:
            signal.setitimer(signal.ITIMER_REAL, 10.0)
            result = fish(task)
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
            tid = os.path.splitext(fname)[0]
            if args.verbose or ok:
                print(f"  {tid}: {'OK' if ok else 'X'} src={src}")
        else:
            sources["none"] = sources.get("none", 0) + 1
    
    print(f"\n{'═' * 60}")
    print(f" DISRUPTION FISHER RESULTS ({total} tasks)")
    print(f"{'═' * 60}")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"    {src}: {count}")
