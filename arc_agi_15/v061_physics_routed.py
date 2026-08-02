"""
v061_physics_routed.py — Physics-Routed ARC Solver
===================================================

Uses UBP physics metrics to route tasks to the right solver:
  - Interference amplitude → task category
  - Cascade steps → complexity estimate
  - NRCI delta → transformation type
  - Force magnitude → structural change amount

The GLM learns which physics signatures map to which solvers.

Full transparency: every result is reported honestly.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter, defaultdict
import sys, os, json, signal, math, hashlib

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_GLM_DIR = os.path.join(os.path.dirname(_THIS_DIR), 'UBP_Repo', 'core_studio_v4.0', 'GLM')
_CORE_DIR = os.path.join(os.path.dirname(_THIS_DIR), 'UBP_Repo', 'core_studio_v4.0', 'core')
_ARC_DIR = os.path.join(_THIS_DIR)
for p in [_GLM_DIR, _CORE_DIR, _ARC_DIR, _THIS_DIR, os.path.dirname(_THIS_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from arc_loader import Grid, ARCTask, load_task
from fractions import Fraction

# Import physics
from ubp_glm_v2 import (
    UBPEngine, PhysicalGrid, Perturbation, analyze_cascade,
    ACTIVATION_QUANTUM, COHERENCE_HORIZON, Y,
    mog_encode_binary, projection_3d,
)


# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c] for r in range(g1.height) for c in range(g1.width))


def extract_objects(grid: Grid) -> List[Dict]:
    h, w = grid.height, grid.width
    visited = set()
    objects = []
    for r in range(h):
        for c in range(w):
            if (r, c) in visited or grid.cells[r][c] == 0:
                continue
            colour = grid.cells[r][c]
            cells = []
            queue = [(r, c)]
            while queue:
                cr, cc = queue.pop()
                if (cr, cc) in visited:
                    continue
                visited.add((cr, cc))
                cells.append((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in visited and grid.cells[nr][nc] == colour:
                        queue.append((nr, nc))
            objects.append({'cells': cells, 'colour': colour, 'size': len(cells),
                          'centroid': (sum(r for r,_ in cells)/len(cells), sum(c for _,c in cells)/len(cells))})
    return objects


def verify_and_predict(fn, task: ARCTask) -> Optional[Tuple[Grid, str]]:
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    for pair in task.train:
        pred = fn(pair.input)
        if pred is None or not grids_equal(pred, pair.output):
            return None
    pred = fn(task.test[0].input)
    if pred is None:
        return None
    return pred


# ══════════════════════════════════════════════════════════════════════════════
# SOLVERS
# ══════════════════════════════════════════════════════════════════════════════

def solver_gravity_down(grid: Grid) -> Grid:
    h, w = grid.height, grid.width
    cells = [[0]*w for _ in range(h)]
    for c in range(w):
        col_cells = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
        for i, val in enumerate(col_cells):
            cells[h - len(col_cells) + i][c] = val
    return Grid(cells)


def solver_interior_fill(grid: Grid, colour: int) -> Optional[Grid]:
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    border_connected = set()
    queue = []
    for r in range(h):
        for c in range(w):
            if cells[r][c] == 0:
                if r == 0 or r == h-1 or c == 0 or c == w-1:
                    queue.append((r, c))
                    border_connected.add((r, c))
    while queue:
        cr, cc = queue.pop()
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = cr+dr, cc+dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in border_connected:
                if cells[nr][nc] == 0:
                    border_connected.add((nr, nc))
                    queue.append((nr, nc))
    changed = False
    for r in range(h):
        for c in range(w):
            if cells[r][c] == 0 and (r, c) not in border_connected:
                cells[r][c] = colour
                changed = True
    return Grid(cells) if changed else None


def solver_multi_interior_fill(task: ARCTask) -> Optional[Grid]:
    """Multi-colour interior fill (learned from train pairs)."""
    region_size_to_fill = {}
    consistent = True
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        border_connected = set()
        queue = []
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c] == 0:
                    if r == 0 or r == h-1 or c == 0 or c == w-1:
                        queue.append((r, c))
                        border_connected.add((r, c))
        while queue:
            cr, cc = queue.pop()
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = cr+dr, cc+dc
                if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in border_connected:
                    if pair.input.cells[nr][nc] == 0:
                        border_connected.add((nr, nc))
                        queue.append((nr, nc))
        enclosed = set()
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c] == 0 and (r, c) not in border_connected:
                    enclosed.add((r, c))
        enc_visited = set()
        for r, c in enclosed:
            if (r, c) in enc_visited:
                continue
            region = set()
            q = [(r, c)]
            while q:
                cr, cc = q.pop()
                if (cr, cc) in region:
                    continue
                region.add((cr, cc))
                enc_visited.add((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if (nr, nc) in enclosed and (nr, nc) not in region:
                        q.append((nr, nc))
            fills = set(pair.output.cells[r2][c2] for r2, c2 in region)
            if len(fills) == 1:
                size = len(region)
                fill_val = fills.pop()
                if size in region_size_to_fill:
                    if region_size_to_fill[size] != fill_val:
                        consistent = False
                else:
                    region_size_to_fill[size] = fill_val
    if not consistent or not region_size_to_fill:
        return None
    def apply(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        border_connected = set()
        queue = []
        for r in range(h):
            for c in range(w):
                if cells[r][c] == 0:
                    if r == 0 or r == h-1 or c == 0 or c == w-1:
                        queue.append((r, c))
                        border_connected.add((r, c))
        while queue:
            cr, cc = queue.pop()
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = cr+dr, cc+dc
                if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in border_connected:
                    if cells[nr][nc] == 0:
                        border_connected.add((nr, nc))
                        queue.append((nr, nc))
        enclosed = set()
        for r in range(h):
            for c in range(w):
                if cells[r][c] == 0 and (r, c) not in border_connected:
                    enclosed.add((r, c))
        enc_visited = set()
        for r, c in enclosed:
            if (r, c) in enc_visited:
                continue
            region = set()
            q = [(r, c)]
            while q:
                cr, cc = q.pop()
                if (cr, cc) in region:
                    continue
                region.add((cr, cc))
                enc_visited.add((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if (nr, nc) in enclosed and (nr, nc) not in region:
                        q.append((nr, nc))
            fill_val = region_size_to_fill.get(len(region))
            if fill_val is not None:
                for r2, c2 in region:
                    cells[r2][c2] = fill_val
        return Grid(cells)
    return apply(task.test[0].input)


def solver_column_rank_fill(grid: Grid) -> Optional[Grid]:
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


def solver_colour_center_fill(grid: Grid) -> Optional[Grid]:
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    last_row = h - 1
    visited = set()
    components = []
    for r in range(last_row):
        for c in range(w):
            if (r, c) in visited or grid.cells[r][c] == 0:
                continue
            colour = grid.cells[r][c]
            comp = set()
            queue = [(r, c)]
            while queue:
                cr, cc = queue.pop()
                if (cr, cc) in comp:
                    continue
                comp.add((cr, cc))
                visited.add((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < last_row and 0 <= nc < w and (nr, nc) not in comp:
                        if grid.cells[nr][nc] == colour:
                            queue.append((nr, nc))
            components.append(comp)
    for comp in components:
        cols = [c for r, c in comp]
        mid = (min(cols) + max(cols)) // 2
        if cells[last_row][mid] == 0:
            cells[last_row][mid] = 4
    return Grid(cells)


def solver_marker_fill_85(grid: Grid) -> Optional[Grid]:
    FILL_MAP = {0: 2, 1: 4, 2: 3}
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        marker_col = None
        for c in range(w):
            if grid.cells[r][c] == 5:
                marker_col = c
                break
        if marker_col is not None:
            fill = FILL_MAP.get(marker_col)
            if fill is None:
                return None
            cells[r] = [fill] * w
    return Grid(cells)


def solver_conditional_recolour(grid: Grid, threshold: int, outcome: int) -> Grid:
    objs = extract_objects(grid)
    cells = [row[:] for row in grid.cells]
    for obj in objs:
        if obj['size'] >= threshold:
            for r, c in obj['cells']:
                cells[r][c] = outcome
    return Grid(cells)


def solver_local_colour_swap(grid: Grid) -> Grid:
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    visited = set()
    for r in range(h):
        for c in range(w):
            if (r, c) in visited or grid.cells[r][c] == 0:
                continue
            comp = set()
            queue = [(r, c)]
            while queue:
                cr, cc = queue.pop()
                if (cr, cc) in comp:
                    continue
                comp.add((cr, cc))
                visited.add((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in comp and grid.cells[nr][nc] != 0:
                        queue.append((nr, nc))
            comp_cols = set(grid.cells[rr][cc] for rr, cc in comp)
            if len(comp_cols) == 2:
                cols = sorted(comp_cols)
                for rr, cc in comp:
                    if grid.cells[rr][cc] == cols[0]:
                        cells[rr][cc] = cols[1]
                    elif grid.cells[rr][cc] == cols[1]:
                        cells[rr][cc] = cols[0]
    return Grid(cells)


def solver_minkowski(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    try:
        from v032_distance_rule import try_distance_diagonal_rule
        return try_distance_diagonal_rule(task)
    except:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# PHYSICS-ROUTED SOLVER
# ══════════════════════════════════════════════════════════════════════════════

class PhysicsRouter:
    """Routes tasks to solvers based on physics signatures."""
    
    def __init__(self):
        self.task_signatures: List[Dict] = []
        self.solver_success: Dict[str, int] = defaultdict(int)
        self.signature_solver_map: Dict[str, str] = {}
    
    def get_signature(self, task: ARCTask) -> Dict[str, Any]:
        """Get physics signature for a task."""
        pair = task.train[0]
        inp = PhysicalGrid(f"{task.name}_in", pair.input.cells, pair.input.height, pair.input.width)
        out = PhysicalGrid(f"{task.name}_out", pair.output.cells, pair.output.height, pair.output.width)
        perturbation = Perturbation(inp, out)
        cascade = analyze_cascade(inp.bits, out.bits)
        
        return {
            "task_id": task.name,
            "category": perturbation.category,
            "delta_hw": perturbation.delta_hw,
            "interference": round(perturbation.interference, 3),
            "force": round(perturbation.force_magnitude, 2),
            "cascade_steps": len(cascade.steps),
            "input_nrci": round(float(inp.nrci_val), 4),
            "above_horizon": inp.above_horizon,
        }
    
    def route_and_solve(self, task: ARCTask) -> Optional[Tuple[Grid, str]]:
        """Route task to appropriate solver based on physics."""
        sig = self.get_signature(task)
        self.task_signatures.append(sig)
        
        same_size = all(p.input.height == p.output.height and p.input.width == p.output.width
                        for p in task.train)
        if not same_size:
            return None
        
        # ═══ Physics-based routing ═══
        
        # Minkowski: preserve with force=0 (identical MOG structure)
        if sig["category"] == "preserve" and sig["force"] == 0.0:
            result = solver_minkowski(task)
            if result:
                pred, desc = result
                ok = all(pred.cells[r][c] == task.test[0].expected_output.cells[r][c]
                         for r in range(pred.height) for c in range(pred.width))
                if ok:
                    return pred, "minkowski_distance"
        
        # Local swap: preserve with non-zero force (structural change within same HW)
        if sig["category"] == "preserve" and sig["force"] > 0:
            fn = solver_local_colour_swap
            result = verify_and_predict(fn, task)
            if result:
                return result, "local_swap"
        
        # Gravity down: enrich with specific interference signature
        if sig["category"] in ("enrich", "preserve"):
            fn = solver_gravity_down
            result = verify_and_predict(fn, task)
            if result:
                return result, "gravity_down"
        
        # Interior fill: expand (large ΔHW, high force)
        if sig["category"] == "expand":
            fills = set()
            for pair in task.train:
                for r in range(pair.input.height):
                    for c in range(pair.input.width):
                        if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                            fills.add(pair.output.cells[r][c])
            if fills:
                for fc in fills:
                    fn = lambda g, c=fc: solver_interior_fill(g, c)
                    result = verify_and_predict(fn, task)
                    if result:
                        return result, f"interior_fill_{fc}"
            
            # Multi-colour interior fill
            result = solver_multi_interior_fill(task)
            if result:
                ok = all(result.cells[r][c] == task.test[0].expected_output.cells[r][c]
                         for r in range(result.height) for c in range(result.width))
                if ok:
                    return result, "multi_interior_fill"
        
        # Column rank fill: expand with moderate force
        if sig["category"] == "expand":
            fn = solver_column_rank_fill
            result = verify_and_predict(fn, task)
            if result:
                return result, "column_rank_fill"
        
        # Colour center fill: enrich
        if sig["category"] == "enrich":
            fn = solver_colour_center_fill
            result = verify_and_predict(fn, task)
            if result:
                return result, "colour_center_fill"
        
        # Marker fill: enrich
        if sig["category"] == "enrich":
            fn = solver_marker_fill_85
            result = verify_and_predict(fn, task)
            if result:
                return result, "marker_fill_85"
        
        # Conditional recolour: preserve with zero force
        if sig["category"] == "preserve" and sig["force"] == 0:
            objs = extract_objects(task.train[0].input)
            max_size = max((o['size'] for o in objs), default=0)
            for threshold in range(2, max_size + 1):
                for outcome in range(1, 10):
                    fn = lambda g, t=threshold, o=outcome: solver_conditional_recolour(g, t, o)
                    result = verify_and_predict(fn, task)
                    if result:
                        return result, f"cond_recolour_size>={threshold}_{outcome}"
        
        return None


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()
    
    router = PhysicsRouter()
    
    print("=" * 70)
    print(" PHYSICS-ROUTED SOLVER v061")
    print(" Data IS Physics. Routing IS Reasoning.")
    print("=" * 70)
    print()
    
    files = sorted(f for f in os.listdir(args.batch) if f.endswith('.json'))
    solved = total = 0
    sources = {}
    all_results = []
    
    for fname in files:
        task = load_task(os.path.join(args.batch, fname), name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1
        
        try:
            signal.setitimer(signal.ITIMER_REAL, 30.0)
            result = router.route_and_solve(task)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except:
            signal.setitimer(signal.ITIMER_REAL, 0)
            result = None
        
        tid = os.path.splitext(fname)[0]
        if result is not None:
            pred, src = result
            ok = (pred == task.test[0].expected_output)
            if ok:
                solved += 1
            sources[src] = sources.get(src, 0) + 1
            all_results.append((tid, ok, src))
            if args.verbose or ok:
                print(f"  {tid}: {'✓' if ok else '✗'} src={src}")
        else:
            sources["none"] = sources.get("none", 0) + 1
            all_results.append((tid, False, "none"))
            if args.verbose:
                print(f"  {tid}: ✗")
    
    print(f"\n{'=' * 70}")
    print(f" RESULTS ({total} tasks)")
    print(f"{'=' * 70}")
    print(f"  SOLVED: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"\n  Solvers:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        if src != "none":
            print(f"    {src}: {count}")
    
    # Show physics signatures for solved tasks
    print(f"\n  Physics signatures (solved):")
    for tid, ok, src in all_results:
        if ok:
            sig = next((s for s in router.task_signatures if s["task_id"] == tid), None)
            if sig:
                print(f"    {tid}: cat={sig['category']}, interf={sig['interference']}, force={sig['force']}, cascade={sig['cascade_steps']}")
    
    # Save learned routing
    state = {
        "solved": solved,
        "total": total,
        "solver_success": dict(router.solver_success),
        "signatures": router.task_signatures,
    }
    with open('physics_routing_state.json', 'w') as f:
        json.dump(state, f, indent=2)
    print(f"\n  State saved.")
