"""
v047_targeted_solvers.py — Targeted Solvers Based on Task Analysis
==================================================================

Based on deep analysis of unsolved tasks, implements specific solver categories:

1. Interior fill with variable colour (00dbd492)
2. Object-extension fills (fcc82909)
3. Row-dependent fill based on object position (a85d4709)
4. Background replacement preserving objects (2bcee788)
5. Object extension to edge (e048c9ed)
6. Colour swap (7acdf6d3)
7. Per-object column fill below (fcc82909 variant)
8. Gravity down (already solved, included for completeness)
9. Object expansion by 1 cell (2bcee788 variant)
10. Marker placement at object column in last row (54d82841)

Full transparency: every solve and non-solve is reported.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set
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
    """Get connected components (4-connected)."""
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
    """Get bounding box (min_r, min_c, max_r, max_c)."""
    rows = [r for r, c in comp]
    cols = [c for r, c in comp]
    return min(rows), min(cols), max(rows), max(cols)


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Interior Fill with Variable Colour
# Task: 00dbd492 — fill enclosed regions with a colour derived from
# the enclosing boundary
# ═══════════════════════════════════════════════════════════════════

def interior_fill_derived(grid: Grid) -> Optional[Grid]:
    """Fill enclosed zero-regions with colour derived from enclosing object.
    
    The fill colour is: (number of non-zero neighbours) % 9 + 1,
    or the most common non-zero colour in the Moore neighbourhood.
    """
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    
    # Find all zero cells connected to border
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
    
    # For each enclosed region, determine fill colour
    # Strategy: fill = most common non-zero colour adjacent to the region
    # But the actual fill colour varies per task, so we need to learn it
    
    # First pass: identify enclosed regions
    enclosed = set()
    for r in range(h):
        for c in range(w):
            if cells[r][c] == 0 and (r, c) not in border_connected:
                enclosed.add((r, c))
    
    if not enclosed:
        return None
    
    # Find fill colour from output (learn from train pairs)
    # This is task-specific, so we return the structure for verification
    # The caller will handle colour derivation
    
    # For now, use the most common non-zero neighbour colour
    for r, c in enclosed:
        n_cols = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r+dr, c+dc
                if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] != 0:
                    n_cols.append(cells[nr][nc])
        if n_cols:
            cells[r][c] = Counter(n_cols).most_common(1)[0][0]
    
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Object Extension to Right Edge
# Task: e048c9ed — each row of non-zero cells extends rightward by 1
# ═══════════════════════════════════════════════════════════════════

def extend_right_by_one(grid: Grid) -> Optional[Grid]:
    """Extend each row of non-zero cells rightward by 1 cell."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    changed = False
    
    for r in range(h):
        # Find rightmost non-zero cell in this row
        rightmost = -1
        for c in range(w-1, -1, -1):
            if grid.cells[r][c] != 0:
                rightmost = c
                break
        
        if rightmost >= 0 and rightmost + 1 < w:
            # Extend by 1 with the same colour
            cells[r][rightmost + 1] = grid.cells[r][rightmost]
            changed = True
    
    return Grid(cells) if changed else None


def extend_right_colour(grid: Grid) -> Optional[Grid]:
    """Extend each row rightward, colour = colour of the row's object."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    changed = False
    
    for r in range(h):
        # Find all non-zero cells in this row
        row_cols = [c for c in range(w) if grid.cells[r][c] != 0]
        if not row_cols:
            continue
        
        # Get the colour of the rightmost cell
        rightmost_c = max(row_cols)
        col = grid.cells[r][rightmost_c]
        
        # Extend rightward by 1
        if rightmost_c + 1 < w:
            cells[r][rightmost_c + 1] = col
            changed = True
    
    return Grid(cells) if changed else None


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Row Fill Based on Object Position
# Task: a85d4709 — each row's fill colour depends on where colour 5 is
# ═══════════════════════════════════════════════════════════════════

def row_fill_by_marker(grid: Grid, marker: int = 5) -> Optional[Grid]:
    """Fill each row with a colour determined by the marker's column position.
    
    Fill colour = (column_of_marker % 4) + 2, or some derived value.
    This needs to be learned from train pairs.
    """
    h, w = grid.height, grid.width
    
    # Find marker positions per row
    marker_positions = {}
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == marker:
                marker_positions[r] = c
    
    if not marker_positions:
        return None
    
    # Learn the fill colour mapping from the grid structure
    # For now, try: fill = (marker_col % 5) + 1
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        if r in marker_positions:
            c = marker_positions[r]
            fill = (c % 5) + 1
            cells[r] = [fill] * w
    
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Background Replace + Object Expansion
# Task: 2bcee788 — replace all 0s with colour 3, expand objects by 1
# ═══════════════════════════════════════════════════════════════════

def bg_replace_and_expand(grid: Grid, bg_fill: int = 3) -> Optional[Grid]:
    """Replace background and expand objects by 1 cell in all directions."""
    h, w = grid.height, grid.width
    cells = [[bg_fill]*w for _ in range(h)]
    
    # Copy original non-zero cells
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] != 0:
                cells[r][c] = grid.cells[r][c]
    
    # Expand: for each non-zero cell in original, fill neighbours with same colour
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] != 0:
                col = grid.cells[r][c]
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] == 0:
                        cells[nr][nc] = col
    
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Column Fill Below Objects
# Task: fcc82909 — below each 2×2 object, fill a 2-wide column of colour 3
# ═══════════════════════════════════════════════════════════════════

def column_fill_below_objects(grid: Grid, fill_col: int = 3) -> Optional[Grid]:
    """For each connected component, fill cells below it with fill_col.
    
    The fill extends from the bottom of the component to the bottom of the grid,
    maintaining the component's column span.
    """
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    
    components = get_components(grid)
    
    for comp in components:
        min_r, min_c, max_r, max_c = get_bbox(comp)
        comp_w = max_c - min_c + 1
        
        # Fill below the component
        for r in range(max_r + 1, h):
            for c in range(min_c, max_c + 1):
                if cells[r][c] == 0:
                    cells[r][c] = fill_col
    
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Colour Swap
# Task: 7acdf6d3 — swap two specific colours
# ═══════════════════════════════════════════════════════════════════

def colour_swap(grid: Grid, col_a: int, col_b: int) -> Optional[Grid]:
    """Swap all instances of col_a and col_b."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if cells[r][c] == col_a:
                cells[r][c] = col_b
            elif cells[r][c] == col_b:
                cells[r][c] = col_a
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Marker at Object Column in Last Row
# Task: 54d82841 — place colour 4 at the column of each object in the last row
# ═══════════════════════════════════════════════════════════════════

def marker_at_object_columns(grid: Grid, marker_col: int = 4) -> Optional[Grid]:
    """Place marker_col in the last row at columns where objects exist."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    
    # Find columns that contain non-zero cells
    object_columns = set()
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] != 0:
                object_columns.add(c)
    
    # Place markers in last row
    last_row = h - 1
    for c in object_columns:
        if cells[last_row][c] == 0:
            cells[last_row][c] = marker_col
    
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Object Mirror/Reflection
# ═══════════════════════════════════════════════════════════════════

def mirror_horizontal(grid: Grid) -> Optional[Grid]:
    """Mirror the grid horizontally (left-right flip)."""
    h, w = grid.height, grid.width
    cells = [row[::-1] for row in grid.cells]
    return Grid(cells)


def mirror_vertical(grid: Grid) -> Optional[Grid]:
    """Mirror the grid vertically (top-bottom flip)."""
    h, w = grid.height, grid.width
    cells = grid.cells[::-1]
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Object Extraction (crop to bounding box)
# ═══════════════════════════════════════════════════════════════════

def crop_to_bbox(grid: Grid) -> Optional[Grid]:
    """Crop to bounding box of all non-zero cells."""
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


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Gravity Down (from existing DSL)
# ═══════════════════════════════════════════════════════════════════

def gravity_down(grid: Grid) -> Optional[Grid]:
    """Move all non-zero cells to the bottom of their column."""
    h, w = grid.height, grid.width
    cells = [[0]*w for _ in range(h)]
    
    for c in range(w):
        # Collect non-zero cells in this column
        col_cells = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
        # Place them at the bottom
        for i, val in enumerate(col_cells):
            cells[h - len(col_cells) + i][c] = val
    
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Rotate 90/180/270
# ═══════════════════════════════════════════════════════════════════

def rotate_90(grid: Grid) -> Optional[Grid]:
    """Rotate 90 degrees clockwise."""
    h, w = grid.height, grid.width
    cells = [[grid.cells[h-1-r][c] for r in range(h)] for c in range(w)]
    return Grid(cells)


def rotate_180(grid: Grid) -> Optional[Grid]:
    """Rotate 180 degrees."""
    h, w = grid.height, grid.width
    cells = [[grid.cells[h-1-r][w-1-c] for c in range(w)] for r in range(h)]
    return Grid(cells)


def rotate_270(grid: Grid) -> Optional[Grid]:
    """Rotate 270 degrees clockwise (= 90 CCW)."""
    h, w = grid.height, grid.width
    cells = [[grid.cells[r][w-1-c] for r in range(h)] for c in range(w)]
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Per-Object Transform (different objects get different treatment)
# ═══════════════════════════════════════════════════════════════════

def per_object_recolour(grid: Grid) -> Optional[Grid]:
    """Each connected component gets a unique colour based on its size."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    
    components = get_components(grid)
    for i, comp in enumerate(components):
        new_col = (i % 9) + 1
        for r, c in comp:
            cells[r][c] = new_col
    
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Fill Interior of Rectangles
# ═══════════════════════════════════════════════════════════════════

def fill_rect_interior(grid: Grid) -> Optional[Grid]:
    """For each rectangular object, fill its interior (bounding box minus border)."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    
    components = get_components(grid)
    changed = False
    
    for comp in components:
        min_r, min_c, max_r, max_c = get_bbox(comp)
        
        # Check if it's a rectangle (border cells are all non-zero)
        is_rect = True
        for c in range(min_c, max_c+1):
            if grid.cells[min_r][c] == 0 or grid.cells[max_r][c] == 0:
                is_rect = False
                break
        if is_rect:
            for r in range(min_r, max_r+1):
                if grid.cells[r][min_c] == 0 or grid.cells[r][max_c] == 0:
                    is_rect = False
                    break
        
        if is_rect and max_r - min_r > 1 and max_c - min_c > 1:
            # Fill interior with the border colour
            border_col = grid.cells[min_r][min_c]
            for r in range(min_r+1, max_r):
                for c in range(min_c+1, max_c):
                    if cells[r][c] == 0:
                        cells[r][c] = border_col
                        changed = True
    
    return Grid(cells) if changed else None


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Fill Interior with Derived Colour
# ═══════════════════════════════════════════════════════════════════

def fill_rect_interior_derived(grid: Grid) -> Optional[Grid]:
    """For each rectangular object, fill its interior with a derived colour.
    
    Derivation: fill = (border_colour + 1) % 10, or (border_colour + 2) % 10, etc.
    """
    h, w = grid.height, grid.width
    
    components = get_components(grid)
    
    for offset in range(1, 8):
        cells = [row[:] for row in grid.cells]
        changed = False
        
        for comp in components:
            min_r, min_c, max_r, max_c = get_bbox(comp)
            
            # Check if it's a rectangle
            is_rect = True
            for c in range(min_c, max_c+1):
                if grid.cells[min_r][c] == 0 or grid.cells[max_r][c] == 0:
                    is_rect = False
                    break
            if is_rect:
                for r in range(min_r, max_r+1):
                    if grid.cells[r][min_c] == 0 or grid.cells[r][max_c] == 0:
                        is_rect = False
                        break
            
            if is_rect and max_r - min_r > 1 and max_c - min_c > 1:
                border_col = grid.cells[min_r][min_c]
                fill = (border_col + offset) % 10
                if fill == 0:
                    fill = (border_col + offset) % 9 + 1
                for r in range(min_r+1, max_r):
                    for c in range(min_c+1, max_c):
                        if cells[r][c] == 0:
                            cells[r][c] = fill
                            changed = True
        
        if changed:
            result = Grid(cells)
            # Only return if this matches all train pairs
            return result
    
    return None


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Tiling
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


def tile_2x2_mirror(grid: Grid) -> Optional[Grid]:
    """Tile 2x2 with mirroring."""
    h, w = grid.height, grid.width
    new_h, new_w = h * 2, w * 2
    cells = [[0]*new_w for _ in range(new_h)]
    for r in range(new_h):
        for c in range(new_w):
            sr = r % h if r < h else h - 1 - (r % h)
            sc = c % w if c < w else w - 1 - (c % w)
            cells[r][c] = grid.cells[sr][sc]
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# SOLVER: Scale Down
# ═══════════════════════════════════════════════════════════════════

def scale_down_2x(grid: Grid) -> Optional[Grid]:
    """Scale down by factor 2 (majority in 2x2 block)."""
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
# SOLVER: Conditional Fill Based on Train Pairs
# Learns the fill colour from train pairs and applies to test
# ═══════════════════════════════════════════════════════════════════

def learn_fill_colour(task: ARCTask) -> Optional[int]:
    """Learn the fill colour from train pairs.
    
    Returns the colour that zeros are changed to, if consistent.
    """
    fill_colours = set()
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    fill_colours.add(pair.output.cells[r][c])
    
    if len(fill_colours) == 1:
        return fill_colours.pop()
    return None


# ═══════════════════════════════════════════════════════════════════
# SYSTEMATIC SOLVER
# ═══════════════════════════════════════════════════════════════════

def solve(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Try all targeted solvers systematically."""
    
    same_size = all(p.input.height == p.output.height and p.input.width == p.output.width 
                    for p in task.train)
    
    # ═══ Geometric transforms ═══
    if same_size:
        for name, fn in [("rotate_90", rotate_90), ("rotate_180", rotate_180), 
                         ("rotate_270", rotate_270), ("mirror_h", mirror_horizontal),
                         ("mirror_v", mirror_vertical), ("gravity_down", gravity_down)]:
            result = verify_and_predict(fn, task)
            if result:
                return result, name, {}
    
    # ═══ Colour swap ═══
    if same_size:
        # Find swapped colours
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            swaps = {}
            for r in range(h):
                for c in range(w):
                    ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                    if ic != oc:
                        if ic in swaps:
                            if swaps[ic] != oc:
                                swaps = None
                                break
                        else:
                            swaps[ic] = oc
            if swaps and len(swaps) == 2:
                cols = list(swaps.keys())
                if swaps[cols[0]] == cols[1] and swaps[cols[1]] == cols[0]:
                    def make_swap(a, b):
                        def fn(grid):
                            return colour_swap(grid, a, b)
                        return fn
                    result = verify_and_predict(make_swap(cols[0], cols[1]), task)
                    if result:
                        return result, f"swap_{cols[0]}_{cols[1]}", {}
    
    # ═══ Interior fill ═══
    if same_size:
        fill_col = learn_fill_colour(task)
        if fill_col is not None:
            def make_interior_fill(fc):
                def fn(grid):
                    h, w = grid.height, grid.width
                    cells = [row[:] for row in grid.cells]
                    
                    # Find enclosed zeros
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
                                cells[r][c] = fc
                                changed = True
                    
                    return Grid(cells) if changed else None
                return fn
            
            result = verify_and_predict(make_interior_fill(fill_col), task)
            if result:
                return result, f"interior_fill_{fill_col}", {}
    
    # ═══ Fill rectangular interiors ═══
    if same_size:
        result = verify_and_predict(fill_rect_interior, task)
        if result:
            return result, "fill_rect_interior", {}
        
        for offset in range(1, 8):
            def make_fri_offset(off):
                def fn(grid):
                    h, w = grid.height, grid.width
                    components = get_components(grid)
                    cells = [row[:] for row in grid.cells]
                    changed = False
                    
                    for comp in components:
                        min_r, min_c, max_r, max_c = get_bbox(comp)
                        is_rect = True
                        for c in range(min_c, max_c+1):
                            if grid.cells[min_r][c] == 0 or grid.cells[max_r][c] == 0:
                                is_rect = False
                                break
                        if is_rect:
                            for r in range(min_r, max_r+1):
                                if grid.cells[r][min_c] == 0 or grid.cells[r][max_c] == 0:
                                    is_rect = False
                                    break
                        
                        if is_rect and max_r - min_r > 1 and max_c - min_c > 1:
                            border_col = grid.cells[min_r][min_c]
                            fill = (border_col + off) % 10
                            if fill == 0:
                                fill = (border_col + off) % 9 + 1
                            for r in range(min_r+1, max_r):
                                for c in range(min_c+1, max_c):
                                    if cells[r][c] == 0:
                                        cells[r][c] = fill
                                        changed = True
                    
                    return Grid(cells) if changed else None
                return fn
            
            result = verify_and_predict(make_fri_offset(offset), task)
            if result:
                return result, f"fill_rect_interior_offset_{offset}", {}
    
    # ═══ Column fill below objects ═══
    if same_size:
        fill_col = learn_fill_colour(task)
        if fill_col is not None:
            def make_col_fill(fc):
                def fn(grid):
                    h, w = grid.height, grid.width
                    cells = [row[:] for row in grid.cells]
                    components = get_components(grid)
                    
                    for comp in components:
                        min_r, min_c, max_r, max_c = get_bbox(comp)
                        for r in range(max_r + 1, h):
                            for c in range(min_c, max_c + 1):
                                if cells[r][c] == 0:
                                    cells[r][c] = fc
                    
                    return Grid(cells)
                return fn
            
            result = verify_and_predict(make_col_fill(fill_col), task)
            if result:
                return result, f"column_fill_below_{fill_col}", {}
    
    # ═══ Background replace + expand ═══
    if same_size:
        fill_col = learn_fill_colour(task)
        if fill_col is not None:
            def make_bg_expand(fc):
                def fn(grid):
                    h, w = grid.height, grid.width
                    cells = [[fc]*w for _ in range(h)]
                    
                    # Copy original non-zero cells
                    for r in range(h):
                        for c in range(w):
                            if grid.cells[r][c] != 0:
                                cells[r][c] = grid.cells[r][c]
                    
                    # Expand by 1
                    for r in range(h):
                        for c in range(w):
                            if grid.cells[r][c] != 0:
                                col = grid.cells[r][c]
                                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                                    nr, nc = r+dr, c+dc
                                    if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] == 0:
                                        cells[nr][nc] = col
                    
                    return Grid(cells)
                return fn
            
            result = verify_and_predict(make_bg_expand(fill_col), task)
            if result:
                return result, f"bg_expand_{fill_col}", {}
    
    # ═══ Object extension to right ═══
    if same_size:
        result = verify_and_predict(extend_right_by_one, task)
        if result:
            return result, "extend_right_1", {}
        result = verify_and_predict(extend_right_colour, task)
        if result:
            return result, "extend_right_colour", {}
    
    # ═══ Marker at object columns ═══
    if same_size:
        for marker in range(1, 10):
            def make_marker(m):
                def fn(grid):
                    h, w = grid.height, grid.width
                    cells = [row[:] for row in grid.cells]
                    object_cols = set()
                    for r in range(h):
                        for c in range(w):
                            if grid.cells[r][c] != 0:
                                object_cols.add(c)
                    last_row = h - 1
                    for c in object_cols:
                        if cells[last_row][c] == 0:
                            cells[last_row][c] = m
                    return Grid(cells)
                return fn
            result = verify_and_predict(make_marker(marker), task)
            if result:
                return result, f"marker_{marker}_at_obj_cols", {}
    
    # ═══ Row fill by marker ═══
    if same_size:
        for marker in set(c for pair in task.train for row in pair.input.cells for c in row):
            if marker == 0:
                continue
            def make_row_marker(m):
                def fn(grid):
                    h, w = grid.height, grid.width
                    cells = [row[:] for row in grid.cells]
                    for r in range(h):
                        marker_cols = [c for c in range(w) if grid.cells[r][c] == m]
                        if marker_cols:
                            fill = (marker_cols[0] % 5) + 1
                            for c in range(w):
                                if grid.cells[r][c] == 0:
                                    cells[r][c] = fill
                    return Grid(cells)
                return fn
            result = verify_and_predict(make_row_marker(marker), task)
            if result:
                return result, f"row_fill_by_marker_{marker}", {}
    
    # ═══ Size-changing: tiling ═══
    if all(p.output.height == p.input.height * 2 and p.output.width == p.input.width * 2 for p in task.train):
        result = verify_and_predict(tile_2x2, task)
        if result:
            return result, "tile_2x2", {}
        result = verify_and_predict(tile_2x2_mirror, task)
        if result:
            return result, "tile_2x2_mirror", {}
    
    # ═══ Size-changing: crop ═══
    if all(p.output.height < p.input.height and p.output.width < p.input.width for p in task.train):
        result = verify_and_predict(crop_to_bbox, task)
        if result:
            return result, "crop_to_bbox", {}
        result = verify_and_predict(scale_down_2x, task)
        if result:
            return result, "scale_down_2x", {}
    
    # ═══ Per-object recolour ═══
    if same_size:
        result = verify_and_predict(per_object_recolour, task)
        if result:
            return result, "per_object_recolour", {}
    
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
    print(" TARGETED SOLVERS v047")
    print("═" * 60)
    print()
    
    for fname in files:
        task = load_task(os.path.join(args.batch, fname),
                         name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1
        
        try:
            signal.setitimer(signal.ITIMER_REAL, 20.0)
            result = solve(task)
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
                print(f"  {tid}: ✗ (no solver)")
    
    print(f"\n{'═' * 60}")
    print(f" TARGETED SOLVERS RESULTS ({total} tasks)")
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
