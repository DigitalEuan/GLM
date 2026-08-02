"""
v046_expanded_fisher.py — Expanded Pattern Catalogue for ARC-AGI
================================================================

Extends v045 disruption fisher with new pattern categories:
- Connected component operations
- Interior fill (flood fill enclosed regions)
- Symmetry-based operations
- Position-dependent fills
- Counting operations
- Neighbourhood-conditional (richer)
- Object extraction
- Two-step compositions
- Size-changing operations (tile, crop, scale)

Full transparency: every solve and non-solve is reported.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set
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
    for pair in task.train:
        pred = rule_fn(pair.input)
        if pred is None or not grids_equal(pred, pair.output):
            return None
    pred = rule_fn(task.test[0].input)
    if pred is None:
        return None
    return pred


# ═══════════════════════════════════════════════════════════════════
# CONNECTED COMPONENTS
# ═══════════════════════════════════════════════════════════════════

def get_components(grid: Grid, colour: int = None) -> List[Set[Tuple[int, int]]]:
    """Get connected components of a specific colour (or all non-zero)."""
    h, w = grid.height, grid.width
    visited = set()
    components = []
    
    for r in range(h):
        for c in range(w):
            if (r, c) in visited:
                continue
            if colour is not None and grid.cells[r][c] != colour:
                continue
            if colour is None and grid.cells[r][c] == 0:
                continue
            
            # BFS
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
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in comp:
                        if colour is not None and grid.cells[nr][nc] == colour:
                            queue.append((nr, nc))
                        elif colour is None and grid.cells[nr][nc] != 0:
                            queue.append((nr, nc))
            components.append(comp)
    return components


def get_bbox(comp: Set[Tuple[int, int]]) -> Tuple[int, int, int, int]:
    """Get bounding box (min_r, min_c, max_r, max_c) of component."""
    rows = [r for r, c in comp]
    cols = [c for r, c in comp]
    return min(rows), min(cols), max(rows), max(cols)


# ═══════════════════════════════════════════════════════════════════
# PATTERN: Interior Fill (flood fill enclosed regions)
# ═══════════════════════════════════════════════════════════════════

def interior_fill(grid: Grid, bg: int = 0) -> Optional[Grid]:
    """Fill enclosed zero-regions (not connected to border) with the colour
    of their enclosing object."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    
    # Find all zero cells connected to border
    border_connected = set()
    queue = []
    for r in range(h):
        for c in range(w):
            if cells[r][c] == bg:
                if r == 0 or r == h-1 or c == 0 or c == w-1:
                    queue.append((r, c))
                    border_connected.add((r, c))
    
    while queue:
        cr, cc = queue.pop()
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = cr+dr, cc+dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in border_connected:
                if cells[nr][nc] == bg:
                    border_connected.add((nr, nc))
                    queue.append((nr, nc))
    
    # Fill enclosed zeros
    changed = False
    for r in range(h):
        for c in range(w):
            if cells[r][c] == bg and (r, c) not in border_connected:
                # Find enclosing colour
                neighbours = set()
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] != bg:
                        neighbours.add(cells[nr][nc])
                if len(neighbours) == 1:
                    cells[r][c] = neighbours.pop()
                    changed = True
                elif len(neighbours) > 1:
                    # Multiple enclosing colours — use most common
                    cells[r][c] = Counter(neighbours).most_common(1)[0][0]
                    changed = True
    
    return Grid(cells) if changed else None


# ═══════════════════════════════════════════════════════════════════
# PATTERN: Component Size → Fill Colour
# ═══════════════════════════════════════════════════════════════════

def component_size_fill(grid: Grid) -> Optional[Grid]:
    """Fill colour = size of the connected component the cell belongs to."""
    h, w = grid.height, grid.width
    components = get_components(grid)
    
    cells = [row[:] for row in grid.cells]
    for comp in components:
        size = len(comp)
        for r, c in comp:
            cells[r][c] = size % 10  # Keep in 0-9 range
    
    return Grid(cells)


def component_size_threshold(grid: Grid, threshold: int, fill: int) -> Optional[Grid]:
    """Components with size >= threshold get recoloured to fill."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    
    for colour in set(c for row in grid.cells for c in row):
        if colour == 0:
            continue
        components = get_components(grid, colour)
        for comp in components:
            if len(comp) >= threshold:
                for r, c in comp:
                    cells[r][c] = fill
    
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# PATTERN: Position-Dependent Fill
# ═══════════════════════════════════════════════════════════════════

def make_position_fill_color(fn):
    """Fill zeros with colour determined by position function fn(r, c, h, w)."""
    def rule(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        changed = False
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == 0:
                    val = fn(r, c, h, w)
                    if val is not None and val != 0:
                        cells[r][c] = val
                        changed = True
        return Grid(cells) if changed else None
    return rule


# ═══════════════════════════════════════════════════════════════════
# PATTERN: Counting Operations
# ═══════════════════════════════════════════════════════════════════

def count_fill_row(grid: Grid) -> Optional[Grid]:
    """Fill zeros with count of non-zero cells in their row."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    changed = False
    for r in range(h):
        count = sum(1 for c in range(w) if grid.cells[r][c] != 0)
        for c in range(w):
            if grid.cells[r][c] == 0:
                cells[r][c] = count % 10
                changed = True
    return Grid(cells) if changed else None


def count_fill_col(grid: Grid) -> Optional[Grid]:
    """Fill zeros with count of non-zero cells in their column."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    changed = False
    for c in range(w):
        count = sum(1 for r in range(h) if grid.cells[r][c] != 0)
        for r in range(h):
            if grid.cells[r][c] == 0:
                cells[r][c] = count % 10
                changed = True
    return Grid(cells) if changed else None


def count_neighbours_fill(grid: Grid) -> Optional[Grid]:
    """Fill zeros with count of non-zero 4-neighbours."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    changed = False
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == 0:
                count = 0
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] != 0:
                        count += 1
                if count > 0:
                    cells[r][c] = count
                    changed = True
    return Grid(cells) if changed else None


# ═══════════════════════════════════════════════════════════════════
# PATTERN: Majority Colour Fill
# ═══════════════════════════════════════════════════════════════════

def majority_neighbour_fill(grid: Grid) -> Optional[Grid]:
    """Fill zeros with the majority non-zero colour among 4-neighbours."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    changed = False
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == 0:
                n_cols = []
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] != 0:
                        n_cols.append(grid.cells[nr][nc])
                if n_cols:
                    cells[r][c] = Counter(n_cols).most_common(1)[0][0]
                    changed = True
    return Grid(cells) if changed else None


# ═══════════════════════════════════════════════════════════════════
# PATTERN: Background Replacement
# ═══════════════════════════════════════════════════════════════════

def background_replace(grid: Grid, old_bg: int, new_bg: int) -> Optional[Grid]:
    """Replace all cells of old_bg with new_bg."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    changed = False
    for r in range(h):
        for c in range(w):
            if cells[r][c] == old_bg:
                cells[r][c] = new_bg
                changed = True
    return Grid(cells) if changed else None


# ═══════════════════════════════════════════════════════════════════
# PATTERN: Erase Specific Colour
# ═══════════════════════════════════════════════════════════════════

def make_erase_colour(colour: int):
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
# PATTERN: Symmetry-Based
# ═══════════════════════════════════════════════════════════════════

def reflect_horizontal(grid: Grid) -> Optional[Grid]:
    """Reflect grid horizontally."""
    h, w = grid.height, grid.width
    cells = [row[::-1] for row in grid.cells]
    return Grid(cells)


def reflect_vertical(grid: Grid) -> Optional[Grid]:
    """Reflect grid vertically."""
    h, w = grid.height, grid.width
    cells = grid.cells[::-1]
    return Grid(cells)


def rotate_90(grid: Grid) -> Optional[Grid]:
    """Rotate grid 90 degrees clockwise."""
    h, w = grid.height, grid.width
    cells = [[grid.cells[h-1-r][c] for r in range(h)] for c in range(w)]
    return Grid(cells)


def rotate_180(grid: Grid) -> Optional[Grid]:
    """Rotate grid 180 degrees."""
    h, w = grid.height, grid.width
    cells = [[grid.cells[h-1-r][w-1-c] for c in range(w)] for r in range(h)]
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# PATTERN: Distance to Nearest Non-Zero
# ═══════════════════════════════════════════════════════════════════

def distance_fill(grid: Grid, dist_type: str = 'manhattan') -> Optional[Grid]:
    """Fill zeros with distance to nearest non-zero cell."""
    h, w = grid.height, grid.width
    non_zero = [(r, c) for r in range(h) for c in range(w) if grid.cells[r][c] != 0]
    if not non_zero:
        return None
    
    cells = [row[:] for row in grid.cells]
    changed = False
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == 0:
                if dist_type == 'manhattan':
                    d = min(abs(r-nr) + abs(c-nc) for nr, nc in non_zero)
                else:  # chebyshev
                    d = max(abs(r-nr) + abs(c-nc) for nr, nc in non_zero)  # Actually Chebyshev
                    d = min(max(abs(r-nr), abs(c-nc)) for nr, nc in non_zero)
                cells[r][c] = d % 10
                changed = True
    return Grid(cells) if changed else None


# ═══════════════════════════════════════════════════════════════════
# PATTERN: Row/Column Majority Fill
# ═══════════════════════════════════════════════════════════════════

def row_majority_fill(grid: Grid) -> Optional[Grid]:
    """Fill zeros with the most common non-zero colour in their row."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    changed = False
    for r in range(h):
        row_cols = [c for c in grid.cells[r] if c != 0]
        if row_cols:
            maj = Counter(row_cols).most_common(1)[0][0]
            for c in range(w):
                if grid.cells[r][c] == 0:
                    cells[r][c] = maj
                    changed = True
    return Grid(cells) if changed else None


def col_majority_fill(grid: Grid) -> Optional[Grid]:
    """Fill zeros with the most common non-zero colour in their column."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    changed = False
    for c in range(w):
        col_cols = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
        if col_cols:
            maj = Counter(col_cols).most_common(1)[0][0]
            for r in range(h):
                if grid.cells[r][c] == 0:
                    cells[r][c] = maj
                    changed = True
    return Grid(cells) if changed else None


# ═══════════════════════════════════════════════════════════════════
# PATTERN: Neighbourhood-Conditional (Rich)
# ═══════════════════════════════════════════════════════════════════

def make_neighbour_count_fill(target_col: int, min_count: int, fill_col: int):
    """Fill cells of target_col if they have >= min_count neighbours of any non-zero colour."""
    def rule(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == target_col:
                    count = 0
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] != 0 and grid.cells[nr][nc] != target_col:
                            count += 1
                    if count >= min_count:
                        cells[r][c] = fill_col
        return Grid(cells)
    return rule


def make_moore_neighbour_recolour(in_col: int, n_col: int, out_col: int):
    """Recolour in_col to out_col if any of 8 Moore neighbours is n_col."""
    def rule(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == in_col:
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r+dr, c+dc
                            if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] == n_col:
                                cells[r][c] = out_col
                                break
        return Grid(cells)
    return rule


# ═══════════════════════════════════════════════════════════════════
# PATTERN: Tiling (for size-changing tasks)
# ═══════════════════════════════════════════════════════════════════

def tile_2x2(grid: Grid) -> Optional[Grid]:
    """Tile the grid 2x2."""
    h, w = grid.height, grid.width
    new_h, new_w = h * 2, w * 2
    cells = [[0]*new_w for _ in range(new_h)]
    for r in range(new_h):
        for c in range(new_w):
            cells[r][c] = grid.cells[r % h][c % w]
    return Grid(cells)


def tile_2x2_flipped_h(grid: Grid) -> Optional[Grid]:
    """Tile 2x2 with horizontal flip in right half."""
    h, w = grid.height, grid.width
    new_h, new_w = h * 2, w * 2
    cells = [[0]*new_w for _ in range(new_h)]
    for r in range(new_h):
        for c in range(new_w):
            sr = r % h
            sc = c % w
            if c >= w:
                sc = w - 1 - sc
            cells[r][c] = grid.cells[sr][sc]
    return Grid(cells)


def tile_2x2_flipped_v(grid: Grid) -> Optional[Grid]:
    """Tile 2x2 with vertical flip in bottom half."""
    h, w = grid.height, grid.width
    new_h, new_w = h * 2, w * 2
    cells = [[0]*new_w for _ in range(new_h)]
    for r in range(new_h):
        for c in range(new_w):
            sr = r % h
            sc = c % w
            if r >= h:
                sr = h - 1 - sr
            cells[r][c] = grid.cells[sr][sc]
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# PATTERN: Crop to Non-Zero Bounding Box
# ═══════════════════════════════════════════════════════════════════

def crop_to_content(grid: Grid) -> Optional[Grid]:
    """Crop grid to bounding box of non-zero cells."""
    h, w = grid.height, grid.width
    non_zero = [(r, c) for r in range(h) for c in range(w) if grid.cells[r][c] != 0]
    if not non_zero:
        return None
    min_r = min(r for r, c in non_zero)
    max_r = max(r for r, c in non_zero)
    min_c = min(c for r, c in non_zero)
    max_c = max(c for r, c in non_zero)
    
    new_h = max_r - min_r + 1
    new_w = max_c - min_c + 1
    cells = [[grid.cells[r][c] for c in range(min_c, max_c+1)] for r in range(min_r, max_r+1)]
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# PATTERN: Scale Down (for size-reducing tasks)
# ═══════════════════════════════════════════════════════════════════

def scale_down_2x(grid: Grid) -> Optional[Grid]:
    """Scale down by factor 2 (take top-left of each 2x2 block)."""
    h, w = grid.height, grid.width
    if h % 2 != 0 or w % 2 != 0:
        return None
    new_h, new_w = h // 2, w // 2
    cells = [[grid.cells[r*2][c*2] for c in range(new_w)] for r in range(new_h)]
    return Grid(cells)


def scale_down_majority(grid: Grid) -> Optional[Grid]:
    """Scale down by factor 2 (majority colour in each 2x2 block)."""
    h, w = grid.height, grid.width
    if h % 2 != 0 or w % 2 != 0:
        return None
    new_h, new_w = h // 2, w // 2
    cells = [[0]*new_w for _ in range(new_h)]
    for r in range(new_h):
        for c in range(new_w):
            block = [
                grid.cells[r*2][c*2], grid.cells[r*2][c*2+1],
                grid.cells[r*2+1][c*2], grid.cells[r*2+1][c*2+1]
            ]
            cells[r][c] = Counter(block).most_common(1)[0][0]
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# SYSTEMATIC FISHER (expanded)
# ═══════════════════════════════════════════════════════════════════

def fish(task: ARCTask) -> Optional[Tuple[ Grid, str, Dict]]:
    """Try all expanded patterns systematically."""
    
    same_size = all(p.input.height == p.output.height and p.input.width == p.output.width 
                    for p in task.train)
    
    # ═══ LEVEL 0: Same-size check ═══
    if same_size:
        # ═══ LEVEL 1: Simple fills (from v045) ═══
        
        # Column-rank fill
        def column_rank_fill(grid: Grid) -> Optional[Grid]:
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
        
        result = verify_and_predict(column_rank_fill, task)
        if result:
            return result, "column_rank_fill", {}
        
        # Row-rank fill
        def row_rank_fill(grid: Grid) -> Optional[Grid]:
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
        
        result = verify_and_predict(row_rank_fill, task)
        if result:
            return result, "row_rank_fill", {}
        
        # ═══ LEVEL 2: Interior fill ═══
        result = verify_and_predict(interior_fill, task)
        if result:
            return result, "interior_fill", {}
        
        # ═══ LEVEL 3: Component operations ═══
        for threshold in range(2, 20):
            for fill in range(1, 10):
                def make_comp_thresh(t, f):
                    def rule(grid):
                        return component_size_threshold(grid, t, f)
                    return rule
                result = verify_and_predict(make_comp_thresh(threshold, fill), task)
                if result:
                    return result, f"component_thresh_{threshold}_fill_{fill}", {}
        
        # ═══ LEVEL 4: Uniform fills ═══
        fill_colours = set()
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                        fill_colours.add(pair.output.cells[r][c])
        
        for fc in fill_colours:
            def make_uf(col):
                def rule(grid):
                    h, w = grid.height, grid.width
                    cells = [row[:] for row in grid.cells]
                    for r in range(h):
                        for c in range(w):
                            if grid.cells[r][c] == 0:
                                cells[r][c] = col
                    return Grid(cells)
                return rule
            result = verify_and_predict(make_uf(fc), task)
            if result:
                return result, f"uniform_fill_{fc}", {}
        
        # ═══ LEVEL 5: Background replacement ═══
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] != pair.output.cells[r][c]:
                        old_bg = pair.input.cells[r][c]
                        new_bg = pair.output.cells[r][c]
                        def make_bg_replace(o, n):
                            def rule(grid):
                                return background_replace(grid, o, n)
                            return rule
                        result = verify_and_predict(make_bg_replace(old_bg, new_bg), task)
                        if result:
                            return result, f"bg_replace_{old_bg}_to_{new_bg}", {}
        
        # ═══ LEVEL 6: Recolour mappings ═══
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
            def make_rc(rm):
                def rule(grid):
                    h, w = grid.height, grid.width
                    cells = [row[:] for row in grid.cells]
                    for r in range(h):
                        for c in range(w):
                            if cells[r][c] in rm:
                                cells[r][c] = rm[cells[r][c]]
                    return Grid(cells)
                return rule
            result = verify_and_predict(make_rc(recolour_map), task)
            if result:
                return result, f"recolour_{len(recolour_map)}", {}
        
        # ═══ LEVEL 7: Conditional recolour (cardinal) ═══
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
            def make_nr(ic_, nc_, oc_):
                def rule(grid):
                    h, w = grid.height, grid.width
                    cells = [row[:] for row in grid.cells]
                    for r in range(h):
                        for c in range(w):
                            if grid.cells[r][c] == ic_:
                                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                                    nr, nc = r+dr, c+dc
                                    if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] == nc_:
                                        cells[r][c] = oc_
                                        break
                    return Grid(cells)
                return rule
            result = verify_and_predict(make_nr(ic, n_col, oc), task)
            if result:
                return result, f"neighbour_{ic}_near_{n_col}_to_{oc}", {}
        
        # ═══ LEVEL 8: Moore neighbourhood recolour ═══
        for (ic, n_col, oc), count in triple_counts.most_common(10):
            if count < n_pairs:
                continue
            result = verify_and_predict(make_moore_neighbour_recolour(ic, n_col, oc), task)
            if result:
                return result, f"moore_{ic}_near_{n_col}_to_{oc}", {}
        
        # ═══ LEVEL 9: Majority neighbour fill ═══
        result = verify_and_predict(majority_neighbour_fill, task)
        if result:
            return result, "majority_neighbour_fill", {}
        
        # ═══ LEVEL 10: Row/Col majority fill ═══
        result = verify_and_predict(row_majority_fill, task)
        if result:
            return result, "row_majority_fill", {}
        
        result = verify_and_predict(col_majority_fill, task)
        if result:
            return result, "col_majority_fill", {}
        
        # ═══ LEVEL 11: Count-based fills ═══
        result = verify_and_predict(count_neighbours_fill, task)
        if result:
            return result, "count_neighbours_fill", {}
        
        # ═══ LEVEL 12: Distance fill ═══
        result = verify_and_predict(lambda g: distance_fill(g, 'manhattan'), task)
        if result:
            return result, "distance_fill_manhattan", {}
        
        result = verify_and_predict(lambda g: distance_fill(g, 'chebyshev'), task)
        if result:
            return result, "distance_fill_chebyshev", {}
        
        # ═══ LEVEL 13: Erase specific colours ═══
        for col in set(c for pair in task.train for row in pair.input.cells for c in row):
            if col == 0:
                continue
            result = verify_and_predict(make_erase_colour(col), task)
            if result:
                return result, f"erase_{col}", {}
        
        # ═══ LEVEL 14: Two-step (erase + fill) ═══
        erase_map = {}
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            for r in range(h):
                for c in range(w):
                    ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                    if ic != 0 and oc == 0:
                        if ic in erase_map:
                            if erase_map[ic] != 0:
                                erase_map[ic] = None
                        else:
                            erase_map[ic] = 0
        erase_map = {k: v for k, v in erase_map.items() if v is not None}
        
        if erase_map:
            for fc in fill_colours:
                def make_ef(em, fill_c):
                    def rule(grid):
                        h, w = grid.height, grid.width
                        cells = [row[:] for row in grid.cells]
                        for r in range(h):
                            for c in range(w):
                                if cells[r][c] in em:
                                    cells[r][c] = em[cells[r][c]]
                        intermediate = Grid(cells)
                        # Fill
                        cells2 = [row[:] for row in intermediate.cells]
                        for r in range(h):
                            for c in range(w):
                                if cells2[r][c] == 0:
                                    cells2[r][c] = fill_c
                        return Grid(cells2)
                    return rule
                result = verify_and_predict(make_ef(erase_map, fc), task)
                if result:
                    return result, f"erase+fill_{fc}", {}
        
        # ═══ LEVEL 15: Recolour + fill ═══
        if recolour_map and fill_colours:
            for fc in fill_colours:
                def make_rf(rm, fill_c):
                    def rule(grid):
                        h, w = grid.height, grid.width
                        cells = [row[:] for row in grid.cells]
                        for r in range(h):
                            for c in range(w):
                                if cells[r][c] in rm:
                                    cells[r][c] = rm[cells[r][c]]
                        for r in range(h):
                            for c in range(w):
                                if cells[r][c] == 0:
                                    cells[r][c] = fill_c
                        return Grid(cells)
                    return rule
                result = verify_and_predict(make_rf(recolour_map, fc), task)
                if result:
                    return result, f"recolour+fill_{fc}", {}
    
    # ═══ SIZE-CHANGING OPERATIONS ═══
    
    # Check if output is larger
    if all(p.output.height >= p.input.height and p.output.width >= p.input.width for p in task.train):
        # Tiling
        result = verify_and_predict(tile_2x2, task)
        if result:
            return result, "tile_2x2", {}
        result = verify_and_predict(tile_2x2_flipped_h, task)
        if result:
            return result, "tile_2x2_flipped_h", {}
        result = verify_and_predict(tile_2x2_flipped_v, task)
        if result:
            return result, "tile_2x2_flipped_v", {}
    
    # Check if output is smaller
    if all(p.output.height <= p.input.height and p.output.width <= p.input.width for p in task.train):
        # Crop
        result = verify_and_predict(crop_to_content, task)
        if result:
            return result, "crop_to_content", {}
        
        # Scale down
        result = verify_and_predict(scale_down_2x, task)
        if result:
            return result, "scale_down_2x", {}
        result = verify_and_predict(scale_down_majority, task)
        if result:
            return result, "scale_down_majority", {}
    
    # Geometric transforms (same-size only if they pass)
    if same_size:
        result = verify_and_predict(rotate_90, task)
        if result:
            return result, "rotate_90", {}
        result = verify_and_predict(rotate_180, task)
        if result:
            return result, "rotate_180", {}
        result = verify_and_predict(reflect_horizontal, task)
        if result:
            return result, "reflect_h", {}
        result = verify_and_predict(reflect_vertical, task)
        if result:
            return result, "reflect_v", {}
    
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
    all_results = []
    
    print("═" * 60)
    print(" EXPANDED FISHER v046 — Systematic Pattern Search")
    print("═" * 60)
    print()
    
    for fname in files:
        task = load_task(os.path.join(args.batch, fname),
                         name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1
        
        try:
            signal.setitimer(signal.ITIMER_REAL, 15.0)
            result = fish(task)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except Exception as e:
            signal.setitimer(signal.ITIMER_REAL, 0)
            result = None
        
        tid = os.path.splitext(fname)[0]
        if result is not None:
            pred, src, diag = result
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
                print(f"  {tid}: ✗ (no pattern)")
    
    print(f"\n{'═' * 60}")
    print(f" EXPANDED FISHER RESULTS ({total} tasks)")
    print(f"{'═' * 60}")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"\n  Sources:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        marker = " ←" if src != "none" and count > 0 else ""
        print(f"    {src}: {count}{marker}")
    
    print(f"\n  Unsolved tasks:")
    for tid, ok, src in all_results:
        if not ok:
            print(f"    {tid}")
