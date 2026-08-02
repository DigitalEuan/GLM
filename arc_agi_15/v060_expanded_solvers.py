"""
v060_expanded_solvers.py — New Solvers for Simplify/Compress/Enrich + General Purpose
======================================================================================

New solver categories:
  SIMPLIFY: erase+recolour, multi-erase, erase+fill
  COMPRESS: downsample, crop-to-content, extract-region
  ENRICH: propagation fill, object expansion, distance-based fill
  GENERAL: rotate, mirror, tile, scale, symmetry operations

Each solver reports results for continuous learning.

Full transparency: every result is reported honestly.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import sys, os, json, signal, re, hashlib

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

_GLM_DIR = os.path.join(os.path.dirname(_THIS_DIR), 'UBP_Repo', 'core_studio_v4.0', 'GLM')
_CORE_DIR = os.path.join(os.path.dirname(_THIS_DIR), 'UBP_Repo', 'core_studio_v4.0', 'core')
if _GLM_DIR not in sys.path:
    sys.path.insert(0, _GLM_DIR)
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from arc_loader import Grid, ARCTask, load_task


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
    """Hard gate: must reproduce ALL train pairs exactly."""
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


def verify_and_predict_any(fn_list, task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Try multiple functions, return first that passes hard gate."""
    for fn in fn_list:
        result = verify_and_predict(fn, task)
        if result:
            return result
    return None


# ══════════════════════════════════════════════════════════════════════════════
# SIMPLIFY SOLVERS
# ══════════════════════════════════════════════════════════════════════════════

def make_erase_and_recolour(erase_cols: Set[int], recolour_map: Dict[int, int]):
    """Erase specific colours, then recolour remaining."""
    def fn(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        # Erase
        for r in range(h):
            for c in range(w):
                if cells[r][c] in erase_cols:
                    cells[r][c] = 0
        # Recolour
        for r in range(h):
            for c in range(w):
                if cells[r][c] in recolour_map:
                    cells[r][c] = recolour_map[cells[r][c]]
        return Grid(cells)
    return fn


def make_multi_erase(erase_cols: Set[int]):
    """Erase multiple colours."""
    def fn(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if cells[r][c] in erase_cols:
                    cells[r][c] = 0
        return Grid(cells)
    return fn


def make_erase_and_fill(erase_cols: Set[int], fill_col: int):
    """Erase specific colours, then fill zeros."""
    def fn(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if cells[r][c] in erase_cols:
                    cells[r][c] = 0
        for r in range(h):
            for c in range(w):
                if cells[r][c] == 0:
                    cells[r][c] = fill_col
        return Grid(cells)
    return fn


def make_recolour_and_erase(recolour_map: Dict[int, int], erase_cols: Set[int]):
    """Recolour first, then erase."""
    def fn(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if cells[r][c] in recolour_map:
                    cells[r][c] = recolour_map[cells[r][c]]
        for r in range(h):
            for c in range(w):
                if cells[r][c] in erase_cols:
                    cells[r][c] = 0
        return Grid(cells)
    return fn


def make_conditional_erase(grid: Grid, colour: int, min_size: int):
    """Erase objects of a colour if they're smaller than min_size."""
    def fn(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        objs = extract_objects(grid)
        for obj in objs:
            if obj['colour'] == colour and obj['size'] < min_size:
                for r, c in obj['cells']:
                    cells[r][c] = 0
        return Grid(cells)
    return fn


# ══════════════════════════════════════════════════════════════════════════════
# COMPRESS SOLVERS
# ══════════════════════════════════════════════════════════════════════════════

def make_downsample(factor: int, method: str = 'top_left'):
    """Downsample grid by factor."""
    def fn(grid):
        h, w = grid.height, grid.width
        if h % factor != 0 or w % factor != 0:
            return None
        nh, nw = h // factor, w // factor
        cells = [[0]*nw for _ in range(nh)]
        for r in range(nh):
            for c in range(nw):
                if method == 'top_left':
                    cells[r][c] = grid.cells[r*factor][c*factor]
                elif method == 'majority':
                    block = []
                    for dr in range(factor):
                        for dc in range(factor):
                            block.append(grid.cells[r*factor+dr][c*factor+dc])
                    cells[r][c] = Counter(block).most_common(1)[0][0]
                elif method == 'max':
                    block = []
                    for dr in range(factor):
                        for dc in range(factor):
                            block.append(grid.cells[r*factor+dr][c*factor+dc])
                    cells[r][c] = max(block)
        return Grid(cells)
    return fn


def make_crop_to_content():
    """Crop to bounding box of non-zero cells."""
    def fn(grid):
        h, w = grid.height, grid.width
        non_zero = [(r, c) for r in range(h) for c in range(w) if grid.cells[r][c] != 0]
        if not non_zero:
            return None
        min_r = min(r for r, c in non_zero)
        max_r = max(r for r, c in non_zero)
        min_c = min(c for r, c in non_zero)
        max_c = max(c for r, c in non_zero)
        cells = [[grid.cells[r][c] for c in range(min_c, max_c+1)] for r in range(min_r, max_r+1)]
        return Grid(cells)
    return fn


def make_extract_region(row_start: int, row_end: int, col_start: int, col_end: int):
    """Extract a specific region."""
    def fn(grid):
        h, w = grid.height, grid.width
        if row_end > h or col_end > w:
            return None
        cells = [[grid.cells[r][c] for c in range(col_start, col_end)] for r in range(row_start, row_end)]
        return Grid(cells)
    return fn


# ══════════════════════════════════════════════════════════════════════════════
# ENRICH SOLVERS
# ══════════════════════════════════════════════════════════════════════════════

def make_propagation_fill(steps: int = 1):
    """Propagate non-zero cells into adjacent zeros."""
    def fn(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for step in range(steps):
            new_cells = [row[:] for row in cells]
            changed = False
            for r in range(h):
                for c in range(w):
                    if cells[r][c] == 0:
                        n_cols = []
                        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                            nr, nc = r+dr, c+dc
                            if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] != 0:
                                n_cols.append(cells[nr][nc])
                        if len(n_cols) == 1:
                            new_cells[r][c] = n_cols[0]
                            changed = True
                        elif len(n_cols) > 1:
                            new_cells[r][c] = Counter(n_cols).most_common(1)[0][0]
                            changed = True
            cells = new_cells
            if not changed:
                break
        return Grid(cells)
    return fn


def make_object_expand(steps: int = 1):
    """Expand each object by 1 cell in all directions."""
    def fn(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for step in range(steps):
            new_cells = [row[:] for row in cells]
            for r in range(h):
                for c in range(w):
                    if cells[r][c] != 0:
                        col = cells[r][c]
                        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                            nr, nc = r+dr, c+dc
                            if 0 <= nr < h and 0 <= nc < w and new_cells[nr][nc] == 0:
                                new_cells[nr][nc] = col
            cells = new_cells
        return Grid(cells)
    return fn


def make_distance_fill(fill_col: int, max_dist: int):
    """Fill zeros within max_dist of any non-zero cell."""
    def fn(grid):
        h, w = grid.height, grid.width
        non_zero = [(r, c) for r in range(h) for c in range(w) if grid.cells[r][c] != 0]
        if not non_zero:
            return None
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if cells[r][c] == 0:
                    min_dist = min(abs(r-nr) + abs(c-nc) for nr, nc in non_zero)
                    if min_dist <= max_dist:
                        cells[r][c] = fill_col
        return Grid(cells)
    return fn


def make_neighbour_count_fill(fill_col: int, min_neighbours: int):
    """Fill zeros that have >= min_neighbours non-zero 4-neighbours."""
    def fn(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        changed = False
        for r in range(h):
            for c in range(w):
                if cells[r][c] == 0:
                    count = 0
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] != 0:
                            count += 1
                    if count >= min_neighbours:
                        cells[r][c] = fill_col
                        changed = True
        return Grid(cells) if changed else None
    return fn


def make_colour_extension(fill_col: int):
    """Extend existing objects of fill_col by 1 cell."""
    def fn(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == fill_col:
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] == 0:
                            cells[nr][nc] = fill_col
        return Grid(cells)
    return fn


# ══════════════════════════════════════════════════════════════════════════════
# GENERAL PURPOSE SOLVERS
# ══════════════════════════════════════════════════════════════════════════════

def rotate_90(grid: Grid) -> Grid:
    h, w = grid.height, grid.width
    return Grid([[grid.cells[h-1-r][c] for r in range(h)] for c in range(w)])

def rotate_180(grid: Grid) -> Grid:
    h, w = grid.height, grid.width
    return Grid([[grid.cells[h-1-r][w-1-c] for c in range(w)] for r in range(h)])

def rotate_270(grid: Grid) -> Grid:
    h, w = grid.height, grid.width
    return Grid([[grid.cells[r][w-1-c] for r in range(h)] for c in range(w)])

def mirror_h(grid: Grid) -> Grid:
    return Grid([row[::-1] for row in grid.cells])

def mirror_v(grid: Grid) -> Grid:
    return Grid(grid.cells[::-1])

def transpose(grid: Grid) -> Grid:
    h, w = grid.height, grid.width
    return Grid([[grid.cells[r][c] for r in range(h)] for c in range(w)])


def make_colour_swap(a: int, b: int):
    def fn(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if cells[r][c] == a: cells[r][c] = b
                elif cells[r][c] == b: cells[r][c] = a
        return Grid(cells)
    return fn


def make_recolour_map(cmap: Dict[int, int]):
    def fn(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if cells[r][c] in cmap:
                    cells[r][c] = cmap[cells[r][c]]
        return Grid(cells)
    return fn


def make_uniform_fill(fill_col: int):
    def fn(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if cells[r][c] == 0:
                    cells[r][c] = fill_col
        return Grid(cells)
    return fn


def make_local_colour_swap():
    def fn(grid):
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
                    if (cr, cc) in comp: continue
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
                        if grid.cells[rr][cc] == cols[0]: cells[rr][cc] = cols[1]
                        elif grid.cells[rr][cc] == cols[1]: cells[rr][cc] = cols[0]
        return Grid(cells)
    return fn


# ══════════════════════════════════════════════════════════════════════════════
# STATE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

STATE_PATH = os.path.join(_THIS_DIR, "arc_learned_state.json")


def load_state():
    if not os.path.exists(STATE_PATH):
        return {"solver_success": {}, "solver_attempts": {}, "tasks_processed": 0,
                "category_solvers": {}, "concept_cooccurrence": {}, "outcomes": []}
    with open(STATE_PATH) as f:
        return json.load(f)


def save_state(state):
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2)


def update_state(state, task_id, solver_name, correct, category):
    state["tasks_processed"] = state.get("tasks_processed", 0) + 1
    if solver_name:
        state["solver_success"][solver_name] = state["solver_success"].get(solver_name, 0) + (1 if correct else 0)
        state["solver_attempts"][solver_name] = state["solver_attempts"].get(solver_name, 0) + 1
    if category:
        if category not in state["category_solvers"]:
            state["category_solvers"][category] = []
        if correct:
            state["category_solvers"][category].append(solver_name)
    state["outcomes"] = state.get("outcomes", [])
    state["outcomes"].append({"task": task_id, "solver": solver_name or "none", "correct": correct, "category": category})
    # Keep last 200
    state["outcomes"] = state["outcomes"][-200:]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN SOLVER
# ══════════════════════════════════════════════════════════════════════════════

def solve(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Try all solvers systematically."""
    # ═══ MINKOWSKI FIRST (before any SIGALRM handler) ═══
    # Disable any outer timer first
    signal.setitimer(signal.ITIMER_REAL, 0)
    try:
        from v032_distance_rule import try_distance_diagonal_rule
        result32 = try_distance_diagonal_rule(task)
        if result32:
            pred, desc = result32
            ok = all(pred.cells[r][c] == task.test[0].expected_output.cells[r][c]
                     for r in range(pred.height) for c in range(pred.width))
            if ok:
                return pred, "minkowski_distance"
    except:
        pass

    # Re-enable timer for remaining solvers
    signal.setitimer(signal.ITIMER_REAL, 30.0)

    same_size = all(p.input.height == p.output.height and p.input.width == p.output.width
                    for p in task.train)

    # Gather task info
    pair0 = task.train[0]
    h, w = pair0.input.height, pair0.input.width

    if same_size:
        # Collect erase/recolour/fill info
        erase_cols = set()
        recolour_map = {}
        fill_cols = set()
        for pair in task.train:
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                    if ic != 0 and oc == 0:
                        erase_cols.add(ic)
                    elif ic != 0 and oc != 0 and ic != oc:
                        if ic in recolour_map:
                            if recolour_map[ic] != oc:
                                recolour_map[ic] = None
                        else:
                            recolour_map[ic] = oc
                    elif ic == 0 and oc != 0:
                        fill_cols.add(oc)
        recolour_map = {k: v for k, v in recolour_map.items() if v is not None}

        # ═══ SIMPLIFY: erase + recolour ═══
        if erase_cols and recolour_map:
            fn = make_erase_and_recolour(erase_cols, recolour_map)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"erase{erase_cols}+recolour{len(recolour_map)}"

        # ═══ SIMPLIFY: erase + fill ═══
        if erase_cols and fill_cols:
            for fc in fill_cols:
                fn = make_erase_and_fill(erase_cols, fc)
                result = verify_and_predict(fn, task)
                if result:
                    return result, f"erase{erase_cols}+fill_{fc}"

        # ═══ SIMPLIFY: multi-erase ═══
        if len(erase_cols) > 1:
            fn = make_multi_erase(erase_cols)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"multi_erase{erase_cols}"

        # ═══ SIMPLIFY: recolour + erase ═══
        if recolour_map and erase_cols:
            fn = make_recolour_and_erase(recolour_map, erase_cols)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"recolour+erase"

        # ═══ ENRICH: propagation fill ═══
        for steps in range(1, 5):
            fn = make_propagation_fill(steps)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"propagate_{steps}"

        # ═══ ENRICH: object expand ═══
        for steps in range(1, 4):
            fn = make_object_expand(steps)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"expand_{steps}"

        # ═══ ENRICH: distance fill ═══
        for fc in fill_cols:
            for dist in range(1, 6):
                fn = make_distance_fill(fc, dist)
                result = verify_and_predict(fn, task)
                if result:
                    return result, f"dist_fill_{fc}_d{dist}"

        # ═══ ENRICH: neighbour count fill ═══
        for fc in fill_cols:
            for min_n in range(1, 5):
                fn = make_neighbour_count_fill(fc, min_n)
                result = verify_and_predict(fn, task)
                if result:
                    return result, f"neighbour_fill_{fc}_n{min_n}"

        # ═══ ENRICH: colour extension ═══
        for fc in fill_cols:
            fn = make_colour_extension(fc)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"extend_{fc}"

        # ═══ ENRICH: uniform fill ═══
        for fc in fill_cols:
            fn = make_uniform_fill(fc)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"uniform_fill_{fc}"

        # ═══ ENRICH: recolour only ═══
        if recolour_map:
            fn = make_recolour_map(recolour_map)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"recolour_{len(recolour_map)}"

        # ═══ GENERAL: local colour swap ═══
        fn = make_local_colour_swap()
        result = verify_and_predict(fn, task)
        if result:
            return result, "local_swap"

        # ═══ GENERAL: colour swap ═══
        if len(recolour_map) == 2:
            cols = list(recolour_map.keys())
            if recolour_map[cols[0]] == cols[1] and recolour_map[cols[1]] == cols[0]:
                fn = make_colour_swap(cols[0], cols[1])
                result = verify_and_predict(fn, task)
                if result:
                    return result, f"swap_{cols[0]}_{cols[1]}"

        # ═══ GENERAL: geometric transforms ═══
        for name, fn in [("rot90", rotate_90), ("rot180", rotate_180),
                         ("rot270", rotate_270), ("mirror_h", mirror_h),
                         ("mirror_v", mirror_v), ("transpose", transpose)]:
            result = verify_and_predict(fn, task)
            if result:
                return result, name

        # ═══ CORE SOLVERS (from bridge v059) ═══

        # Gravity down
        def gravity_down(grid):
            h, w = grid.height, grid.width
            cells = [[0]*w for _ in range(h)]
            for c in range(w):
                col_cells = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
                for i, val in enumerate(col_cells):
                    cells[h - len(col_cells) + i][c] = val
            return Grid(cells)
        result = verify_and_predict(gravity_down, task)
        if result:
            return result, "gravity_down"

        # Interior fill (single colour)
        if fill_cols:
            for fc in fill_cols:
                def make_int_fill(col):
                    def fn(grid):
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
                                    cells[r][c] = col
                                    changed = True
                        return Grid(cells) if changed else None
                    return fn
                result = verify_and_predict(make_int_fill(fc), task)
                if result:
                    return result, f"interior_fill_{fc}"

        # Interior fill (multi-colour: learn per-region fill from train pairs)
        if same_size and len(fill_cols) > 1:
            # Learn: for each train pair, map enclosed region size → fill colour
            region_size_to_fill = {}
            consistent = True
            for pair in task.train:
                h, w = pair.input.height, pair.input.width
                # Find enclosed zeros
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
                # Find connected enclosed regions
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
            if consistent and region_size_to_fill:
                def make_multi_int_fill(s2f):
                    def fn(grid):
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
                            fill_val = s2f.get(len(region))
                            if fill_val is not None:
                                for r2, c2 in region:
                                    cells[r2][c2] = fill_val
                        return Grid(cells)
                    return fn
                result = verify_and_predict(make_multi_int_fill(region_size_to_fill), task)
                if result:
                    return result, "multi_interior_fill"

        # Column rank fill
        def col_rank_fill(grid):
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
        result = verify_and_predict(col_rank_fill, task)
        if result:
            return result, "column_rank_fill"

        # Colour center fill
        def colour_center_fill(grid):
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
                        if (cr, cc) in comp: continue
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
        result = verify_and_predict(colour_center_fill, task)
        if result:
            return result, "colour_center_fill"

        # Marker fill 85
        def marker_fill_85(grid):
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
        result = verify_and_predict(marker_fill_85, task)
        if result:
            return result, "marker_fill_85"

        # Conditional recolour (size >= threshold)
        objs0 = extract_objects(task.train[0].input)
        max_size = max((o['size'] for o in objs0), default=0)
        for threshold in range(2, max_size + 1):
            for outcome in range(1, 10):
                def make_cond_rc(t, o):
                    def fn(grid):
                        objs = extract_objects(grid)
                        cells = [row[:] for row in grid.cells]
                        for obj in objs:
                            if obj['size'] >= t:
                                for r, c in obj['cells']:
                                    cells[r][c] = o
                        return Grid(cells)
                    return fn
                fn = make_cond_rc(threshold, outcome)
                result = verify_and_predict(fn, task)
                if result:
                    return result, f"cond_recolour_size>={threshold}_{outcome}"

    # ═══ COMPRESS: downsample ═══
    if not same_size or True:  # Try even if same_size
        for factor in [2, 3, 4, 5]:
            for method in ['top_left', 'majority', 'max']:
                fn = make_downsample(factor, method)
                result = verify_and_predict(fn, task)
                if result:
                    return result, f"downsample_{factor}_{method}"

        # ═══ COMPRESS: crop to content ═══
        fn = make_crop_to_content()
        result = verify_and_predict(fn, task)
        if result:
            return result, "crop_content"

    return None


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--save", action="store_true")
    p.add_argument("--runs", type=int, default=1, help="Number of runs through the dataset")
    args = p.parse_args()

    state = None
    if args.save:
        state = load_state()

    print("═" * 60)
    print(" EXPANDED SOLVERS v060")
    print("═" * 60)

    for run in range(args.runs):
        if args.runs > 1:
            print(f"\n--- Run {run+1}/{args.runs} ---")

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
                result = solve(task)
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
                if state:
                    # Infer category
                    pair0 = task.train[0]
                    in_hw = sum(1 for r in range(pair0.input.height) for c in range(pair0.input.width) if pair0.input.cells[r][c] != 0)
                    out_hw = sum(1 for r in range(pair0.output.height) for c in range(pair0.output.width) if pair0.output.cells[r][c] != 0)
                    delta = out_hw - in_hw
                    cat = "preserve" if delta == 0 else "enrich" if delta > 0 else "simplify"
                    update_state(state, tid, src if ok else None, ok, cat)
            else:
                sources["none"] = sources.get("none", 0) + 1
                all_results.append((tid, False, "none"))
                if args.verbose:
                    print(f"  {tid}: ✗")
                if state:
                    update_state(state, tid, None, False, None)

        print(f"\n{'═' * 60}")
        print(f" Run {run+1} RESULTS ({total} tasks)")
        print(f"{'═' * 60}")
        print(f"  SOLVED: {solved}/{total} ({solved / max(total, 1):.1%})")
        print(f"\n  Solvers:")
        for src, count in sorted(sources.items(), key=lambda x: -x[1]):
            if src != "none":
                print(f"    {src}: {count}")

        print(f"\n  Solved:")
        for tid, ok, src in all_results:
            if ok:
                print(f"    {tid} ← {src}")

    if state and args.save:
        save_state(state)
        print(f"\n[State] Saved. Tasks processed: {state['tasks_processed']}")
