"""
v065b — Neighbour-conditional recolour solver
==============================================
Learns per-(colour, neighbour_signature) → output_colour rules from train pairs.
Handles the "conditional recolour" category that blocks 41 tasks.
"""

from __future__ import annotations
import os, sys, json, time
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arc_loader import ARCTask, Grid, load_task
from v062_unified_learning import (
    compute_signature, extract_objects, verify_and_predict,
    gravity_down, local_swap, colour_center_fill,
    column_rank_fill, marker_fill_85, cond_recolour,
)
from v065_ubp_glm import (
    learn_consistent_recolour, learn_marker_dilate, learn_uniform_fill,
    learn_marker_flood, learn_row_col_fill, learn_multi_interior_fill,
    try_conditional_recolour, cross_shift_by_markers, try_distance_diagonal_rule,
    grids_equal, same_size_task, diagnose_task,
)


def learn_neighbour_recolour(task: ARCTask) -> Optional[object]:
    """
    Learn a per-cell transformation rule: (input_val, neighbour_signature) → output_val.
    
    The neighbour signature is the sorted tuple of 4-connected neighbour colours.
    This handles tasks where the output colour depends on both the cell's own
    colour and its immediate context.
    
    Returns a function that applies the learned rule to a grid.
    """
    if not same_size_task(task):
        return None
    
    # Collect rules from all train pairs
    # Key: (input_val, neighbour_signature) -> output_val
    rules: Dict[Tuple[int, Tuple[int, ...]], int] = {}
    
    for pair in task.train:
        inp = pair.input
        out = pair.output
        h, w = inp.height, inp.width
        
        for r in range(h):
            for c in range(w):
                iv = inp.cells[r][c]
                ov = out.cells[r][c]
                if iv == ov:
                    continue  # No change, skip
                
                # Get neighbour signature
                neighbours = []
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w:
                        neighbours.append(inp.cells[nr][nc])
                n_sig = tuple(sorted(neighbours))
                
                key = (iv, n_sig)
                if key in rules:
                    if rules[key] != ov:
                        return None  # Inconsistent rule
                else:
                    rules[key] = ov
    
    if not rules:
        return None
    
    class NeighbourRecolourFn:
        def __init__(self, rules):
            self.rules = rules
            # Also build a simpler lookup: just input_val -> output_val
            # for cases where the rule is actually a simple recolour
            self.simple = {}
            for (iv, n_sig), ov in rules.items():
                if iv not in self.simple:
                    self.simple[iv] = ov
                elif self.simple[iv] != ov:
                    self.simple = None  # Not a simple recolour
                    break
        
        def __call__(self, grid: Grid) -> Optional[Grid]:
            h, w = grid.height, grid.width
            src = grid.cells  # Read from original
            cells = [row[:] for row in src]  # Write to copy
            changed = False
            
            for r in range(h):
                for c in range(w):
                    iv = src[r][c]  # Read from ORIGINAL
                    
                    # Get neighbour signature from ORIGINAL
                    neighbours = []
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            neighbours.append(src[nr][nc])
                    n_sig = tuple(sorted(neighbours))
                    
                    key = (iv, n_sig)
                    if key in self.rules:
                        cells[r][c] = self.rules[key]
                        changed = True
            
            return Grid(cells) if changed else None
    
    return NeighbourRecolourFn(rules)


def learn_position_recolour(task: ARCTask) -> Optional[object]:
    """
    Learn a per-cell transformation: (input_val, row, col) → output_val.
    For tasks where the transformation depends on absolute position.
    """
    if not same_size_task(task):
        return None
    
    rules: Dict[Tuple[int, int, int], int] = {}
    
    for pair in task.train:
        inp = pair.input
        out = pair.output
        h, w = inp.height, inp.width
        
        for r in range(h):
            for c in range(w):
                iv = inp.cells[r][c]
                ov = out.cells[r][c]
                if iv == ov:
                    continue
                
                key = (iv, r, c)
                if key in rules:
                    if rules[key] != ov:
                        return None
                else:
                    rules[key] = ov
    
    if not rules:
        return None
    
    class PositionRecolourFn:
        def __init__(self, rules):
            self.rules = rules
        
        def __call__(self, grid: Grid) -> Optional[Grid]:
            h, w = grid.height, grid.width
            cells = [row[:] for row in grid.cells]
            changed = False
            
            for r in range(h):
                for c in range(w):
                    key = (cells[r][c], r, c)
                    if key in self.rules:
                        cells[r][c] = self.rules[key]
                        changed = True
            
            return Grid(cells) if changed else None
    
    return PositionRecolourFn(rules)


# ════════════════════════════════════════════════════════════════════════════
# Main solver pipeline
# ════════════════════════════════════════════════════════════════════════════

def solve_task(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    if same_size_task(task):
        # Order matters: simpler/stricter solvers first
        
        # 1. Consistent recolour
        fn = learn_consistent_recolour(task)
        if fn:
            pred = verify_and_predict(fn, task)
            if pred:
                return pred, "consistent_recolour"
        
        # 2. Uniform fill
        fn = learn_uniform_fill(task)
        if fn:
            pred = verify_and_predict(fn, task)
            if pred:
                return pred, "uniform_fill"
        
        # 3. Marker dilate
        fn = learn_marker_dilate(task)
        if fn:
            pred = verify_and_predict(fn, task)
            if pred:
                return pred, "marker_dilate"
        
        # 4. Marker flood
        fn = learn_marker_flood(task)
        if fn:
            pred = verify_and_predict(fn, task)
            if pred:
                return pred, "marker_flood"
        
        # 5. Row/column fill
        fn = learn_row_col_fill(task)
        if fn:
            pred = verify_and_predict(fn, task)
            if pred:
                return pred, "row_col_fill"
        
        # 6. Interior fill
        fn = learn_multi_interior_fill(task)
        if fn:
            pred = verify_and_predict(fn, task)
            if pred:
                return pred, "multi_interior_fill"
        
        # 7. Neighbour-conditional recolour (NEW)
        fn = learn_neighbour_recolour(task)
        if fn:
            pred = verify_and_predict(fn, task)
            if pred:
                return pred, "neighbour_recolour"
        
        # 8. Position-conditional recolour (NEW)
        fn = learn_position_recolour(task)
        if fn:
            pred = verify_and_predict(fn, task)
            if pred:
                return pred, "position_recolour"
        
        # 9. v064 solvers
        for fn, name in [
            (gravity_down, "gravity_down"),
            (local_swap, "local_swap"),
            (colour_center_fill, "colour_center_fill"),
            (column_rank_fill, "column_rank_fill"),
            (marker_fill_85, "marker_fill_85"),
            (cross_shift_by_markers, "cross_shift_by_markers"),
        ]:
            pred = verify_and_predict(fn, task)
            if pred:
                return pred, name
        
        # 10. Conditional recolour (threshold)
        cond = try_conditional_recolour(task)
        if cond:
            pred, desc = cond
            return pred, "cond_recolour"

    # Size-changing
    dist = try_distance_diagonal_rule(task)
    if dist:
        pred, _desc = dist
        return pred, "minkowski_distance"

    return None


def benchmark(batch_dir: str) -> Dict:
    files = sorted(f for f in os.listdir(batch_dir) if f.endswith(".json"))
    results = []
    solver_counts = Counter()
    v064_solved = {'00dbd492', '1e0a9b12', '396d80d7', '45737921', '54d82841',
                   '575b1a71', 'a85d4709', 'ae58858e', 'e48d4e1a'}

    for fname in files:
        task = load_task(os.path.join(batch_dir, fname), name=os.path.splitext(fname)[0])
        outcome = solve_task(task)
        solved = outcome is not None
        solver = outcome[1] if outcome else "none"
        results.append({
            "task_id": task.name,
            "solved": solved,
            "solver": solver,
            "new": solved and task.name not in v064_solved,
        })
        if solved:
            solver_counts[solver] += 1

    solved_n = sum(1 for r in results if r["solved"])
    new_n = sum(1 for r in results if r["new"])
    return {
        "solved": solved_n,
        "total": len(results),
        "pct": round(100.0 * solved_n / max(1, len(results)), 1),
        "new": new_n,
        "solver_counts": dict(solver_counts),
        "results": results,
    }


def main():
    batch = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "training")
    summary = benchmark(batch)
    
    print("=" * 72)
    print(f" UBP/GLM v065b — {summary['solved']}/{summary['total']} ({summary['pct']}%)")
    print(f" New solves: {summary['new']}")
    print("=" * 72)
    
    for r in summary["results"]:
        if r["solved"]:
            new = " ★ NEW" if r["new"] else ""
            print(f"  {r['task_id']}: ✓ {r['solver']}{new}")
    
    print(f"\n  Solvers:")
    for solver, count in sorted(summary["solver_counts"].items(), key=lambda kv: -kv[1]):
        print(f"    {solver}: {count}")
    
    # Save report
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "REPORTS", "v065b_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Report: {report_path}")


if __name__ == "__main__":
    main()
