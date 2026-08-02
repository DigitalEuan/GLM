"""
v065_ubp_glm.py — Extended UBP/GLM ARC system
================================================

Extends v064 with new solver families targeting the most tractable unsolved tasks.

New solvers added:
1. consistent_recolour — pure global colour mapping (50846271, 7acdf6d3)
2. marker_dilate — fill zeros adjacent to marker colour (9caf5b84, 712bf12e)
3. uniform_fill — fill all zeros with a single learned colour (fcc82909, d4f3cd78)
4. column_fill — fill specific columns with learned colour (d43fd935 partial)

Expected improvement: 9 → ~15 (18% → ~30%)
"""

from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from arc_loader import ARCTask, Grid, load_task
from v032_distance_rule import try_distance_diagonal_rule
from v062_unified_learning import (
    compute_signature,
    extract_objects,
    verify_and_predict,
    gravity_down,
    local_swap,
    colour_center_fill,
    column_rank_fill,
    marker_fill_85,
    cond_recolour,
)

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BATCH = os.path.join(_THIS_DIR, "data", "training")
DEFAULT_STATE = os.path.join(_THIS_DIR, "glm_state", "ubp_glm_operational_state.json")
DEFAULT_REPORT_MD = os.path.join(_THIS_DIR, "REPORTS", "v065_operational_report.md")
DEFAULT_REPORT_JSON = os.path.join(_THIS_DIR, "REPORTS", "v065_operational_report.json")


# ════════════════════════════════════════════════════════════════════════════
# Utilities
# ════════════════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    return g1.height == g2.height and g1.width == g2.width and g1.cells == g2.cells


def same_size_task(task: ARCTask) -> bool:
    return all(p.input.shape == p.output.shape for p in task.train)


def nonzero_count(grid: Grid) -> int:
    return sum(1 for row in grid.cells for v in row if v != 0)


def palette_without_zero(grid: Grid) -> List[int]:
    return sorted(set(v for row in grid.cells for v in row if v != 0))


def pretty_grid(grid: Grid) -> str:
    return "\n".join(" ".join(str(v) for v in row) for row in grid.cells)


# ════════════════════════════════════════════════════════════════════════════
# New solver: Consistent global recolour
# ════════════════════════════════════════════════════════════════════════════

def learn_consistent_recolour(task: ARCTask) -> Optional[Callable[[Grid], Optional[Grid]]]:
    """
    Learn a consistent global colour mapping from train pairs.
    Works when every input colour maps to exactly one output colour.
    
    Solves: 50846271 ({5:8}), 7acdf6d3 ({7:9, 9:7})
    """
    if not same_size_task(task):
        return None
    
    mapping: Dict[int, int] = {}
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                src = pair.input.cells[r][c]
                dst = pair.output.cells[r][c]
                if src != dst:  # Only track actual changes
                    if src in mapping:
                        if mapping[src] != dst:
                            return None  # Inconsistent
                    else:
                        mapping[src] = dst
    
    # Must have at least one non-identity mapping
    if not mapping or all(k == v for k, v in mapping.items()):
        return None
    
    def apply(grid: Grid) -> Optional[Grid]:
        cells = []
        changed = False
        for row in grid.cells:
            new_row = []
            for v in row:
                nv = mapping.get(v, v)
                if nv != v:
                    changed = True
                new_row.append(nv)
            cells.append(new_row)
        return Grid(cells) if changed else None
    
    return apply


# ════════════════════════════════════════════════════════════════════════════
# New solver: Marker dilate (fill zeros adjacent to a marker colour)
# ════════════════════════════════════════════════════════════════════════════

def learn_marker_dilate(task: ARCTask) -> Optional[Callable[[Grid], Optional[Grid]]]:
    """
    Fill zeros that are adjacent (4-connected) to a specific marker colour
    with a learned fill colour.
    
    Pattern: zeros touching marker_colour → fill_colour
    
    Solves: 9caf5b84 (marker=non-zero, fill=7), 712bf12e (marker=5, fill=2)
    """
    if not same_size_task(task):
        return None
    
    # Collect all (marker_colour, fill_colour) pairs from train data
    # For each zero cell in input that becomes non-zero in output,
    # check what non-zero neighbours it had in the input
    marker_to_fill: Dict[int, int] = {}
    
    for pair in task.train:
        inp = pair.input
        out = pair.output
        h, w = inp.height, inp.width
        
        for r in range(h):
            for c in range(w):
                if inp.cells[r][c] == 0 and out.cells[r][c] != 0:
                    fill = out.cells[r][c]
                    # Check 4-connected neighbours in input
                    neighbours = set()
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            nv = inp.cells[nr][nc]
                            if nv != 0:
                                neighbours.add(nv)
                    
                    if len(neighbours) == 1:
                        marker = next(iter(neighbours))
                        if marker in marker_to_fill:
                            if marker_to_fill[marker] != fill:
                                return None  # Inconsistent
                        else:
                            marker_to_fill[marker] = fill
    
    if not marker_to_fill:
        return None
    
    def apply(grid: Grid) -> Optional[Grid]:
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        changed = False
        
        # Find all zeros adjacent to marker colours
        to_fill = []
        for r in range(h):
            for c in range(w):
                if cells[r][c] != 0:
                    continue
                neighbours = set()
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w:
                        nv = cells[nr][nc]
                        if nv != 0:
                            neighbours.add(nv)
                
                for marker, fill in marker_to_fill.items():
                    if marker in neighbours:
                        to_fill.append((r, c, fill))
                        break
        
        for r, c, fill in to_fill:
            cells[r][c] = fill
            changed = True
        
        return Grid(cells) if changed else None
    
    return apply


# ════════════════════════════════════════════════════════════════════════════
# New solver: Uniform fill (fill all zeros with one colour)
# ════════════════════════════════════════════════════════════════════════════

def learn_uniform_fill(task: ARCTask) -> Optional[Callable[[Grid], Optional[Grid]]]:
    """
    Fill ALL zeros with a single learned colour.
    
    Works when every zero in every train pair maps to the same colour.
    Solves: fcc82909 (fill=3), d4f3cd78 (fill=8)
    """
    if not same_size_task(task):
        return None
    
    fill_colours = set()
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    fill_colours.add(pair.output.cells[r][c])
                    if len(fill_colours) > 1:
                        return None  # Multiple fill colours
    
    if len(fill_colours) != 1:
        return None
    
    fill = next(iter(fill_colours))
    
    # Verify: ALL zeros must become this colour (no zeros remain)
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                if pair.input.cells[r][c] == 0:
                    if pair.output.cells[r][c] != fill:
                        return None  # Some zeros don't get filled
    
    def apply(grid: Grid) -> Optional[Grid]:
        cells = []
        changed = False
        for row in grid.cells:
            new_row = []
            for v in row:
                if v == 0:
                    new_row.append(fill)
                    changed = True
                else:
                    new_row.append(v)
            cells.append(new_row)
        return Grid(cells) if changed else None
    
    return apply


# ════════════════════════════════════════════════════════════════════════════
# New solver: Marker dilate iteratively (flood fill from markers)
# ════════════════════════════════════════════════════════════════════════════

def learn_marker_flood(task: ARCTask) -> Optional[Callable[[Grid], Optional[Grid]]]:
    """
    Iteratively fill zeros adjacent to marker-coloured cells until no more can be filled.
    This handles cases where the fill propagates outward from markers.
    
    Pattern: flood fill from marker cells, filling zeros with fill_colour.
    """
    if not same_size_task(task):
        return None
    
    # Determine marker colour and fill colour
    marker_colours = set()
    fill_colours = set()
    
    for pair in task.train:
        inp = pair.input
        out = pair.output
        for r in range(inp.height):
            for c in range(inp.width):
                if inp.cells[r][c] == 0 and out.cells[r][c] != 0:
                    fill_colours.add(out.cells[r][c])
                # Check if non-zero cells are preserved
                if inp.cells[r][c] != 0 and out.cells[r][c] != inp.cells[r][c]:
                    # Some non-zero cells change — not a simple flood
                    return None
    
    if len(fill_colours) != 1:
        return None
    
    fill = next(iter(fill_colours))
    
    # Now determine: which non-zero colours act as "seeds" for the flood?
    # A seed is a colour in the input that has adjacent zeros that get filled
    seeds = set()
    for pair in task.train:
        inp = pair.input
        out = pair.output
        h, w = inp.height, inp.width
        for r in range(h):
            for c in range(w):
                if inp.cells[r][c] == 0 and out.cells[r][c] == fill:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and inp.cells[nr][nc] != 0:
                            seeds.add(inp.cells[nr][nc])
    
    if not seeds:
        return None
    
    # Verify: flood fill from seed cells fills exactly the right zeros
    for pair in task.train:
        inp = pair.input
        out = pair.output
        h, w = inp.height, inp.width
        
        # Simulate flood fill
        filled = set()
        queue = []
        for r in range(h):
            for c in range(w):
                if inp.cells[r][c] in seeds:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and inp.cells[nr][nc] == 0:
                            if (nr, nc) not in filled:
                                filled.add((nr, nc))
                                queue.append((nr, nc))
        
        # Propagate
        while queue:
            r, c = queue.pop(0)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and inp.cells[nr][nc] == 0 and (nr, nc) not in filled:
                    filled.add((nr, nc))
                    queue.append((nr, nc))
        
        # Check: filled cells should match output
        for r in range(h):
            for c in range(w):
                if (r, c) in filled:
                    if out.cells[r][c] != fill:
                        return None  # Flood fills wrong cell
                elif inp.cells[r][c] == 0:
                    if out.cells[r][c] != 0:
                        return None  # Zero should stay zero
    
    def apply(grid: Grid) -> Optional[Grid]:
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        filled = set()
        queue = []
        
        # Start flood from seed-adjacent zeros
        for r in range(h):
            for c in range(w):
                if cells[r][c] in seeds:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] == 0 and (nr, nc) not in filled:
                            filled.add((nr, nc))
                            queue.append((nr, nc))
        
        while queue:
            r, c = queue.pop(0)
            cells[r][c] = fill
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] == 0 and (nr, nc) not in filled:
                    filled.add((nr, nc))
                    queue.append((nr, nc))
        
        return Grid(cells) if filled else None
    
    return apply


# ════════════════════════════════════════════════════════════════════════════
# New solver: Row/column fill (fill entire rows or columns)
# ════════════════════════════════════════════════════════════════════════════

def learn_row_col_fill(task: ARCTask) -> Optional[Callable[[Grid], Optional[Grid]]]:
    """
    Fill entire rows or columns that contain zeros with a learned colour.
    
    Pattern: if a row (or column) contains at least one zero, fill ALL zeros
    in that row (or column) with a specific colour.
    """
    if not same_size_task(task):
        return None
    
    # Check row-based fill
    row_fill: Dict[int, int] = {}  # row_index -> fill colour (if all pairs agree)
    # Actually, we need to check: for each row that has zeros, do all zeros
    # in that row get the same fill colour?
    
    # Strategy: check if the fill pattern is row-based or column-based
    # Row-based: for each row r, all zeros in row r get the same colour
    # Column-based: for each column c, all zeros in column c get the same colour
    
    # Try row-based first
    row_consistent = True
    row_mapping: Dict[int, int] = {}  # row_fill_colour (universal)
    
    for pair in task.train:
        inp = pair.input
        out = pair.output
        h, w = inp.height, inp.width
        
        for r in range(h):
            row_fills = set()
            for c in range(w):
                if inp.cells[r][c] == 0 and out.cells[r][c] != 0:
                    row_fills.add(out.cells[r][c])
            if len(row_fills) > 1:
                row_consistent = False
                break
        if not row_consistent:
            break
    
    if row_consistent:
        # Check if ALL rows use the same fill colour
        all_fills = set()
        for pair in task.train:
            inp = pair.input
            out = pair.output
            for r in range(inp.height):
                for c in range(inp.width):
                    if inp.cells[r][c] == 0 and out.cells[r][c] != 0:
                        all_fills.add(out.cells[r][c])
        
        if len(all_fills) == 1:
            fill = next(iter(all_fills))
            # Verify: every row with zeros gets all its zeros filled
            valid = True
            for pair in task.train:
                inp = pair.input
                out = pair.output
                h, w = inp.height, inp.width
                for r in range(h):
                    has_zero = any(inp.cells[r][c] == 0 for c in range(w))
                    if has_zero:
                        for c in range(w):
                            if inp.cells[r][c] == 0 and out.cells[r][c] != fill:
                                valid = False
                                break
                    if not valid:
                        break
                if not valid:
                    break
            
            if valid:
                def apply_row(grid: Grid, _fill=fill) -> Optional[Grid]:
                    cells = [row[:] for row in grid.cells]
                    changed = False
                    for r in range(grid.height):
                        for c in range(grid.width):
                            if cells[r][c] == 0:
                                cells[r][c] = _fill
                                changed = True
                    return Grid(cells) if changed else None
                return apply_row
    
    # Try column-based fill
    col_consistent = True
    for pair in task.train:
        inp = pair.input
        out = pair.output
        h, w = inp.height, inp.width
        for c in range(w):
            col_fills = set()
            for r in range(h):
                if inp.cells[r][c] == 0 and out.cells[r][c] != 0:
                    col_fills.add(out.cells[r][c])
            if len(col_fills) > 1:
                col_consistent = False
                break
        if not col_consistent:
            break
    
    if col_consistent:
        all_fills = set()
        for pair in task.train:
            inp = pair.input
            out = pair.output
            for r in range(inp.height):
                for c in range(inp.width):
                    if inp.cells[r][c] == 0 and out.cells[r][c] != 0:
                        all_fills.add(out.cells[r][c])
        
        if len(all_fills) == 1:
            fill = next(iter(all_fills))
            valid = True
            for pair in task.train:
                inp = pair.input
                out = pair.output
                h, w = inp.height, inp.width
                for c in range(w):
                    has_zero = any(inp.cells[r][c] == 0 for r in range(h))
                    if has_zero:
                        for r in range(h):
                            if inp.cells[r][c] == 0 and out.cells[r][c] != fill:
                                valid = False
                                break
                    if not valid:
                        break
                if not valid:
                    break
            
            if valid:
                def apply_col(grid: Grid, _fill=fill) -> Optional[Grid]:
                    cells = [row[:] for row in grid.cells]
                    changed = False
                    for c in range(grid.width):
                        for r in range(grid.height):
                            if cells[r][c] == 0:
                                cells[r][c] = _fill
                                changed = True
                    return Grid(cells) if changed else None
                return apply_col
    
    return None


# ════════════════════════════════════════════════════════════════════════════
# Existing solvers (from v064)
# ════════════════════════════════════════════════════════════════════════════

def _enclosed_zero_regions(grid: Grid) -> List[List[Tuple[int, int]]]:
    h, w = grid.height, grid.width
    border_connected = set()
    stack = []
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == 0 and (r == 0 or r == h - 1 or c == 0 or c == w - 1):
                border_connected.add((r, c))
                stack.append((r, c))
    while stack:
        r, c = stack.pop()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in border_connected and grid.cells[nr][nc] == 0:
                border_connected.add((nr, nc))
                stack.append((nr, nc))

    enclosed = {(r, c) for r in range(h) for c in range(w) if grid.cells[r][c] == 0 and (r, c) not in border_connected}
    regions: List[List[Tuple[int, int]]] = []
    visited = set()
    for cell in enclosed:
        if cell in visited:
            continue
        region = []
        stack = [cell]
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            region.append((r, c))
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nxt = (r + dr, c + dc)
                if nxt in enclosed and nxt not in visited:
                    stack.append(nxt)
        regions.append(region)
    return regions


def learn_multi_interior_fill(task: ARCTask) -> Optional[Callable[[Grid], Optional[Grid]]]:
    if not same_size_task(task):
        return None
    size_to_fill: Dict[int, int] = {}
    for pair in task.train:
        regions = _enclosed_zero_regions(pair.input)
        if not regions:
            return None
        for region in regions:
            fills = {pair.output.cells[r][c] for r, c in region}
            if len(fills) != 1:
                return None
            fill = next(iter(fills))
            size = len(region)
            if size in size_to_fill and size_to_fill[size] != fill:
                return None
            size_to_fill[size] = fill
    if not size_to_fill:
        return None

    def apply(grid: Grid) -> Optional[Grid]:
        cells = [row[:] for row in grid.cells]
        changed = False
        for region in _enclosed_zero_regions(grid):
            fill = size_to_fill.get(len(region))
            if fill is None:
                continue
            for r, c in region:
                cells[r][c] = fill
                changed = True
        return Grid(cells) if changed else None

    return apply


def try_conditional_recolour(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    objs = extract_objects(task.train[0].input)
    max_size = max((o["size"] for o in objs), default=0)
    for threshold in range(2, max_size + 1):
        for outcome in range(1, 10):
            fn = lambda g, th=threshold, oc=outcome: cond_recolour(g, th, oc)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"cond_recolour_size>={threshold}_{outcome}"
    return None


def cross_shift_by_markers(grid: Grid) -> Optional[Grid]:
    colours = [v for row in grid.cells for v in row if v not in (0, 5)]
    if not colours:
        return None
    main = Counter(colours).most_common(1)[0][0]
    marker_count = sum(1 for row in grid.cells for v in row if v == 5)
    if marker_count <= 0:
        return None

    row_counts: Dict[int, int] = defaultdict(int)
    col_counts: Dict[int, int] = defaultdict(int)
    for r, row in enumerate(grid.cells):
        for c, v in enumerate(row):
            if v == main:
                row_counts[r] += 1
                col_counts[c] += 1
    if not row_counts or not col_counts:
        return None

    horizontal_row = max(row_counts.items(), key=lambda kv: (kv[1], -kv[0]))[0]
    vertical_col = max(col_counts.items(), key=lambda kv: (kv[1], -kv[0]))[0]
    new_row = horizontal_row + marker_count
    new_col = vertical_col - marker_count
    h, w = grid.height, grid.width
    if not (0 <= new_row < h and 0 <= new_col < w):
        return None

    cells = [[0] * w for _ in range(h)]
    for c in range(w):
        cells[new_row][c] = main
    for r in range(h):
        cells[r][new_col] = main
    return Grid(cells)


# ════════════════════════════════════════════════════════════════════════════
# Solver registry
# ════════════════════════════════════════════════════════════════════════════

SOLVER_CAPABILITIES: Dict[str, str] = {
    "consistent_recolour": "applies a global colour mapping learned from train pairs",
    "marker_dilate": "fills zeros adjacent to a marker colour with a learned fill colour",
    "uniform_fill": "fills all zeros with a single learned colour",
    "marker_flood": "flood-fills from marker cells outward through connected zeros",
    "row_col_fill": "fills all zeros in rows/columns that contain zeros",
    "multi_interior_fill": "fills enclosed zero-regions using region-size→colour mappings",
    "gravity_down": "compacts non-zero cells downward column-wise while preserving order",
    "minkowski_distance": "fills background cells selected by a learned distance/adjacency rule",
    "local_swap": "swaps the two colours inside a connected non-zero component",
    "colour_center_fill": "projects object-group centres into the bottom row",
    "column_rank_fill": "fills zero-columns by their left-to-right rank among zero-bearing columns",
    "marker_fill_85": "replaces rows marked by colour-5 sentinels with learned fill colours",
    "cond_recolour": "recolours objects when a learned component-size threshold is met",
    "cross_shift_by_markers": "translates a cross by the count of marker cells",
}


# ════════════════════════════════════════════════════════════════════════════
# Main solver pipeline
# ════════════════════════════════════════════════════════════════════════════

def solve_task(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    # --- Same-size solvers ---
    if same_size_task(task):
        # 1. Consistent recolour (cheapest — just a mapping)
        consistent_fn = learn_consistent_recolour(task)
        if consistent_fn:
            pred = verify_and_predict(consistent_fn, task)
            if pred:
                return pred, "consistent_recolour"
        
        # 2. Uniform fill
        uniform_fn = learn_uniform_fill(task)
        if uniform_fn:
            pred = verify_and_predict(uniform_fn, task)
            if pred:
                return pred, "uniform_fill"
        
        # 3. Marker dilate
        marker_fn = learn_marker_dilate(task)
        if marker_fn:
            pred = verify_and_predict(marker_fn, task)
            if pred:
                return pred, "marker_dilate"
        
        # 4. Marker flood
        flood_fn = learn_marker_flood(task)
        if flood_fn:
            pred = verify_and_predict(flood_fn, task)
            if pred:
                return pred, "marker_flood"
        
        # 5. Row/column fill
        rcf_fn = learn_row_col_fill(task)
        if rcf_fn:
            pred = verify_and_predict(rcf_fn, task)
            if pred:
                return pred, "row_col_fill"
        
        # 6. Interior fill (v064)
        learned_fill = learn_multi_interior_fill(task)
        if learned_fill:
            pred = verify_and_predict(learned_fill, task)
            if pred:
                return pred, "multi_interior_fill"

        # 7. v064 solvers
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

        # 8. Conditional recolour
        cond = try_conditional_recolour(task)
        if cond:
            pred, desc = cond
            return pred, "cond_recolour"

    # --- Size-changing solvers ---
    dist = try_distance_diagonal_rule(task)
    if dist:
        pred, _desc = dist
        return pred, "minkowski_distance"

    return None


# ════════════════════════════════════════════════════════════════════════════
# Diagnosis
# ════════════════════════════════════════════════════════════════════════════

def global_recolour_consistent(task: ARCTask) -> bool:
    if not same_size_task(task):
        return False
    mapping: Dict[int, int] = {}
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                src = pair.input.cells[r][c]
                dst = pair.output.cells[r][c]
                if src in mapping and mapping[src] != dst:
                    return False
                mapping[src] = dst
    return True


def partial_recolour_present(task: ARCTask) -> bool:
    if not same_size_task(task):
        return True
    outcomes: Dict[int, set] = defaultdict(set)
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                outcomes[pair.input.cells[r][c]].add(pair.output.cells[r][c])
    return any(len(v) > 1 for v in outcomes.values())


def adds_and_deletes_nonzero(task: ARCTask) -> bool:
    if not same_size_task(task):
        return False
    for pair in task.train:
        adds = deletes = False
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                iv = pair.input.cells[r][c]
                ov = pair.output.cells[r][c]
                if iv == 0 and ov != 0:
                    adds = True
                elif iv != 0 and ov == 0:
                    deletes = True
        if adds and deletes:
            return True
    return False


def introduces_new_colour(task: ARCTask) -> bool:
    for pair in task.train:
        if not set(palette_without_zero(pair.output)).issubset(set(palette_without_zero(pair.input))):
            return True
    return False


def object_selection_needed(task: ARCTask) -> bool:
    for pair in task.train:
        in_objs = extract_objects(pair.input)
        out_objs = extract_objects(pair.output)
        if len(in_objs) >= 2 and len(out_objs) <= len(in_objs) and pair.input.shape != pair.output.shape:
            return True
        if len(in_objs) >= 2 and len(out_objs) < len(in_objs):
            return True
    return False


def diagnose_task(task: ARCTask, solved_by: Optional[str] = None) -> Dict[str, Any]:
    pair0 = task.train[0]
    signature = compute_signature(task.name, pair0.input.cells, pair0.output.cells)
    reasons: List[str] = []

    if solved_by:
        reasons.append(f"covered by solver '{solved_by}'")
    else:
        if not same_size_task(task):
            reasons.append("needs a size-changing transform")
        if not global_recolour_consistent(task):
            reasons.append("has no consistent global colour mapping")
        if partial_recolour_present(task):
            reasons.append("needs conditional recolouring")
        if adds_and_deletes_nonzero(task):
            reasons.append("needs multi-step composition")
        if introduces_new_colour(task):
            reasons.append("introduces a derived fill colour")
        if object_selection_needed(task):
            reasons.append("needs relational object selection")
        if not reasons:
            reasons.append("falls outside current solver library")

    return {
        "task_id": task.name,
        "category": signature["category"],
        "delta_hw": signature["delta_hw"],
        "interference": signature["interference"],
        "force": signature["force"],
        "reasons": reasons,
    }


# ════════════════════════════════════════════════════════════════════════════
# Benchmarking
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class TaskResult:
    task_id: str
    solved: bool
    solver: str
    category: str
    reasons: List[str]
    correct_on_dev: Optional[bool]


def benchmark(batch_dir: str) -> Dict[str, Any]:
    files = sorted(f for f in os.listdir(batch_dir) if f.endswith(".json"))
    results: List[TaskResult] = []
    solver_counts: Counter = Counter()

    for fname in files:
        task = load_task(os.path.join(batch_dir, fname), name=os.path.splitext(fname)[0])
        outcome = solve_task(task)
        solved = outcome is not None
        solver = outcome[1] if outcome else "none"
        correct_on_dev = None
        if solved and task.test[0].expected_output is not None:
            correct_on_dev = grids_equal(outcome[0], task.test[0].expected_output)
        diag = diagnose_task(task, solved_by=solver if solved else None)
        results.append(TaskResult(
            task_id=task.name,
            solved=solved,
            solver=solver,
            category=diag["category"],
            reasons=diag["reasons"],
            correct_on_dev=correct_on_dev,
        ))
        if solved:
            solver_counts[solver] += 1

    solved_n = sum(1 for r in results if r.solved)
    return {
        "version": "v065",
        "solved": solved_n,
        "total": len(results),
        "pct": round(100.0 * solved_n / max(1, len(results)), 1),
        "solver_counts": dict(solver_counts),
        "results": [asdict(r) for r in results],
    }


def write_markdown_report(summary: Dict[str, Any], path: str) -> None:
    solved_rows = []
    unsolved_rows = []
    for r in summary["results"]:
        if r["solved"]:
            solved_rows.append(f"| `{r['task_id']}` | `{r['solver']}` | {r['category']} |")
        else:
            unsolved_rows.append(f"| `{r['task_id']}` | {r['category']} | {r['reasons'][0]} |")

    text = f"""# v065 UBP/GLM Report

## Score

**{summary['solved']}/{summary['total']} ({summary['pct']}%)**

## Solved tasks

| Task | Solver | Category |
|---|---|---|
{os.linesep.join(solved_rows) if solved_rows else '| *(none)* | | |'}

## Unsolved tasks

| Task | Category | Blocker |
|---|---|---|
{os.linesep.join(unsolved_rows[:25]) if unsolved_rows else '| *(none)* | | |'}

## Solver distribution

| Solver | Count |
|---|---|
{os.linesep.join(f'| {s} | {c} |' for s, c in sorted(summary['solver_counts'].items(), key=lambda kv: -kv[1]))}
"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(description="v065 UBP/GLM ARC system")
    parser.add_argument("--batch", default=DEFAULT_BATCH)
    parser.add_argument("--task", default="")
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD)
    parser.add_argument("--report-json", default=DEFAULT_REPORT_JSON)
    args = parser.parse_args()

    if args.task:
        task = load_task(args.task)
        outcome = solve_task(task)
        diag = diagnose_task(task, solved_by=(outcome[1] if outcome else None))
        print(f"TASK: {task.name}")
        if outcome:
            pred, solver = outcome
            print(f"Solved by: {solver}")
            if task.test[0].expected_output is not None:
                print(f"Correct: {grids_equal(pred, task.test[0].expected_output)}")
            print(f"\nPrediction:\n{pretty_grid(pred)}")
        else:
            print("Unsolved")
        print(f"\nDiagnosis: {diag['reasons']}")
        return 0

    summary = benchmark(args.batch)
    print("=" * 72)
    print(f" UBP/GLM v065 — {summary['solved']}/{summary['total']} ({summary['pct']}%)")
    print("=" * 72)
    
    # Show new solves vs v064
    v064_solved = {'00dbd492', '1e0a9b12', '396d80d7', '45737921', '54d82841',
                   '575b1a71', 'a85d4709', 'ae58858e', 'e48d4e1a'}
    
    for r in summary["results"]:
        if r["solved"]:
            new = " ★ NEW" if r["task_id"] not in v064_solved else ""
            print(f"  {r['task_id']}: ✓ {r['solver']}{new}")
    
    print(f"\n  Solvers:")
    for solver, count in sorted(summary["solver_counts"].items(), key=lambda kv: -kv[1]):
        print(f"    {solver}: {count}")

    write_markdown_report(summary, args.report_md)
    with open(args.report_json, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Reports: {args.report_md}, {args.report_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
