"""
arc_dsl.py — domain-specific language of ARC grid operators
============================================================

A small but expressive DSL of grid operators that compose into programs.
Each operator takes a Grid (and possibly parameters) and returns a Grid.
Programs are pipelines of operators, expressed as a list of Operation
dataclasses.

The DSL is intentionally minimal — it covers the operator primitives needed
for the 5 archetypes in the v2 study (rotate-then-recolor, gravity-drop,
contiguity-fill, count-and-replicate, set-difference) plus a few common
utilities. Operators compose, so e.g. "rotate then recolour then flip-v"
is a 3-step program.

Usage:
    from arc_dsl import Operation, Program, Ops
    from arc_loader import Grid

    g = Grid([[0,1,0],[1,1,1],[0,1,0]])

    # A 2-step program: rotate 90° clockwise, then recolour 1→2
    prog = Program([
        Operation(Ops.ROTATE_90),
        Operation(Ops.RECOLOUR, params={"mapping": {1: 2}}),
    ])
    out = prog.apply(g)
    print(out.pretty())

    # Check if a program is consistent with training pairs
    from arc_loader import ARCTask, TrainPair
    task = ARCTask(
        train=[TrainPair(g, prog.apply(g))],
        test=[Grid([[0,1],[1,1]])],
    )
    print(prog.matches_train(task))   # True
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
import sys, os

# Make arc_loader importable
_PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import Grid, ARCTask


# ══════════════════════════════════════════════════════════════════════════════
# OPERATOR ENUM
# ══════════════════════════════════════════════════════════════════════════════

class Ops(str, Enum):
    """All DSL operators. str-Enum for stable JSON serialisation."""
    # Identity
    IDENTITY      = "identity"

    # Geometric transforms
    ROTATE_90     = "rotate_90"      # 90° clockwise
    ROTATE_180    = "rotate_180"
    ROTATE_270    = "rotate_270"     # 90° counter-clockwise
    FLIP_H        = "flip_h"          # left-right
    FLIP_V        = "flip_v"          # top-bottom
    TRANSPOSE     = "transpose"

    # Scaling (v2 — uses Spatial Arithmetic R(n) for the scale factor)
    SCALE_2X      = "scale_2x"        # double each dimension
    SCALE_HALF    = "scale_half"      # halve each dimension

    # Translation (v2)
    TRANSLATE     = "translate"       # params: dr, dc

    # Recolouring
    RECOLOUR      = "recolour"        # params: mapping {old: new}

    # Set operations (operate on colour classes)
    SET_INTERSECT = "set_intersect"   # params: with_colour
    SET_DIFFERENCE= "set_difference"  # params: from_colour, by_colour
    SET_UNION     = "set_union"       # params: c1, c2, into_colour

    # Count and replicate
    REPLICATE     = "replicate"       # params: count, axis, step
    COUNT_FILL    = "count_fill"      # fill a row with N copies of dominant shape

    # Contiguity
    FILL_INTERIOR = "fill_interior"   # params: outline_colour, fill_colour
    OUTLINE       = "outline"         # extract 1-cell border
    DILATE        = "dilate"          # grow each object by 1 cell (params: colour)
    ERODE         = "erode"           # shrink each object by 1 cell (params: colour)

    # Gravity (v2 — full 4-direction set)
    GRAVITY_DOWN  = "gravity_down"    # objects fall to rest
    GRAVITY_UP    = "gravity_up"
    GRAVITY_LEFT  = "gravity_left"
    GRAVITY_RIGHT = "gravity_right"

    # Pattern operations (v2)
    REPLACE_PATTERN = "replace_pattern"  # params: from_pattern (2d), to_pattern (2d)

    # v0.4 — Conditional recolouring (the dominant ARC pattern)
    FILL_INTERIOR_AUTO = "fill_interior_auto"  # auto-detect outline colour, fill interior with given colour
    RECOLOUR_INTERIOR  = "recolour_interior"   # recolour all interior (non-outline) cells
    RECOLOUR_BG        = "recolour_bg"          # recolour all background (0) cells to a colour
    RECOLOUR_NONZERO   = "recolour_nonzero"     # recolour all non-zero cells to a colour
    RECOLOUR_IF_NEIGHBOUR = "recolour_if_neighbour"  # recolour cells that have a neighbour of given colour
    RECOLOUR_IF_BORDER = "recolour_if_border"   # recolour cells on the grid border
    RECOLOUR_IF_CORNER = "recolour_if_corner"   # recolour cells at grid corners

    # v0.4 — Row/Column operations
    SHIFT_ROW          = "shift_row"             # params: row_idx, shift (positive=right)
    SHIFT_COL          = "shift_col"             # params: col_idx, shift (positive=down)
    FILL_ROW           = "fill_row"              # params: row_idx, colour
    FILL_COL           = "fill_col"              # params: col_idx, colour
    COPY_ROW           = "copy_row"              # params: from_idx, to_idx
    COPY_COL           = "copy_col"              # params: from_idx, to_idx

    # v0.4 — Object extraction
    EXTRACT_LARGEST    = "extract_largest"       # extract the largest connected component
    EXTRACT_COLOUR     = "extract_colour"        # params: colour — extract all cells of that colour

    # v0.4 — Connectivity / drawing
    DRAW_LINE          = "draw_line"             # params: r1, c1, r2, c2, colour
    DRAW_RECT_OUTLINE  = "draw_rect_outline"     # params: r1, c1, r2, c2, colour
    DRAW_RECT_FILL     = "draw_rect_fill"        # params: r1, c1, r2, c2, colour

    # v0.4 — Tiling / replication
    TILE_2X            = "tile_2x"               # tile the grid 2x in both dimensions
    TILE_3X            = "tile_3x"               # tile the grid 3x in both dimensions

    # Truncation
    CROP_TO_NONZERO = "crop_to_nonzero"


# ── operator implementations ──────────────────────────────────────────────────
# Each function takes (grid: Grid, params: dict) → Grid. The function MUST be
# pure: same input + same params → same output.

def _op_identity(g: Grid, p: dict) -> Grid:
    return g.copy()

def _op_rotate_90(g: Grid, p: dict) -> Grid:
    return g.rotate_90()

def _op_rotate_180(g: Grid, p: dict) -> Grid:
    return g.rotate_180()

def _op_rotate_270(g: Grid, p: dict) -> Grid:
    return g.rotate_270()

def _op_flip_h(g: Grid, p: dict) -> Grid:
    return g.flip_h()

def _op_flip_v(g: Grid, p: dict) -> Grid:
    return g.flip_v()

def _op_transpose(g: Grid, p: dict) -> Grid:
    return g.transpose()

def _op_scale_2x(g: Grid, p: dict) -> Grid:
    """Double each dimension — every cell becomes a 2x2 block of itself."""
    h, w = g.shape
    out = [[0]*(w*2) for _ in range(h*2)]
    for r in range(h):
        for c in range(w):
            v = g.cells[r][c]
            out[r*2][c*2] = v
            out[r*2][c*2+1] = v
            out[r*2+1][c*2] = v
            out[r*2+1][c*2+1] = v
    return Grid(out)

def _op_scale_half(g: Grid, p: dict) -> Grid:
    """Halve each dimension — take every other cell starting from (0,0).
    Grid must have even dimensions; otherwise crop to largest even."""
    h, w = g.shape
    nh, nw = h // 2, w // 2
    if nh == 0 or nw == 0:
        return g.copy()
    out = [[g.cells[r*2][c*2] for c in range(nw)] for r in range(nh)]
    return Grid(out)

def _op_translate(g: Grid, p: dict) -> Grid:
    """Shift all non-zero cells by (dr, dc). Cells that fall off the grid are lost.
    Empty cells (0) are not shifted — only non-zero content moves."""
    dr = int(p.get("dr", 0))
    dc = int(p.get("dc", 0))
    h, w = g.shape
    out = [[0]*w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            v = g.cells[r][c]
            if v == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                out[nr][nc] = v
    return Grid(out)

def _op_recolour(g: Grid, p: dict) -> Grid:
    return g.recolour(p.get("mapping", {}))

def _op_set_intersect(g: Grid, p: dict) -> Grid:
    """Keep only cells where (cell == with_colour) AND (any neighbour == c2).
    This is a 1-cell dilation intersect."""
    with_c = p.get("with_colour", 1)
    by_c = p.get("by_colour", 2)
    h, w = g.shape
    out = [[0]*w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if g.cells[r][c] != with_c:
                continue
            # Check 8-neighbours for by_c
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w and g.cells[nr][nc] == by_c:
                        out[r][c] = with_c
                        break
                else:
                    continue
                break
    return Grid(out)

def _op_set_difference(g: Grid, p: dict) -> Grid:
    """Set (from_colour) cells to 0 if they have any neighbour of (by_colour)."""
    from_c = p.get("from_colour", 1)
    by_c = p.get("by_colour", 2)
    h, w = g.shape
    out = [row[:] for row in g.cells]
    for r in range(h):
        for c in range(w):
            if g.cells[r][c] != from_c:
                continue
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w and g.cells[nr][nc] == by_c:
                        out[r][c] = 0
                        break
                else:
                    continue
                break
    return Grid(out)

def _op_set_union(g: Grid, p: dict) -> Grid:
    """Paint all cells of c1 OR c2 as into_colour."""
    c1 = p.get("c1", 1)
    c2 = p.get("c2", 2)
    into = p.get("into_colour", c1)
    return Grid([[into if v in (c1, c2) else v for v in row] for row in g.cells])

def _op_replicate(g: Grid, p: dict) -> Grid:
    """Replicate the dominant shape `count` times along `axis` (h or v)
    with `step` cells gap between copies. Output is sized to fit."""
    count = int(p.get("count", 2))
    axis = p.get("axis", "h")  # "h" = horizontal placement (along columns)
    step = int(p.get("step", 1))
    dominant = g.dominant_colour()
    if dominant == 0:
        return g.copy()
    # Find bbox of dominant
    from encoder.arc_to_24bit import _dominant_object_bbox
    bbox = _dominant_object_bbox(g, dominant)
    if bbox is None:
        return g.copy()
    rmin, rmax, cmin, cmax = bbox
    sub_h = rmax - rmin + 1
    sub_w = cmax - cmin + 1
    sub = [[g.cells[r][c] for c in range(cmin, cmax+1)] for r in range(rmin, rmax+1)]
    if axis == "h":
        new_w = sub_w * count + step * (count - 1)
        new_h = sub_h
        out = [[0]*new_w for _ in range(new_h)]
        for i in range(count):
            off = i * (sub_w + step)
            for r in range(sub_h):
                for c in range(sub_w):
                    out[r][off + c] = sub[r][c]
    else:
        new_h = sub_h * count + step * (count - 1)
        new_w = sub_w
        out = [[0]*new_w for _ in range(new_h)]
        for i in range(count):
            off = i * (sub_h + step)
            for r in range(sub_h):
                for c in range(sub_w):
                    out[off + r][c] = sub[r][c]
    return Grid(out)

def _op_count_fill(g: Grid, p: dict) -> Grid:
    """Fill the bottom row with N copies of the dominant shape's colour,
    where N = total count of distinct objects across ALL colours in the input."""
    dominant = g.dominant_colour()
    if dominant == 0:
        return g.copy()
    # Count objects across all non-zero colours
    from encoder.arc_to_24bit import _count_objects
    palette = g.palette()
    n = sum(_count_objects(g, c) for c in palette)
    h, w = g.shape
    out = [row[:] for row in g.cells]
    # Bottom row gets N cells of dominant (left-to-right)
    for c in range(min(n, w)):
        out[h-1][c] = dominant
    return Grid(out)

def _op_fill_interior(g: Grid, p: dict) -> Grid:
    """Flood-fill the interior of the outline (outline_colour) with fill_colour.
    Interior = cells reachable from the grid edge without crossing outline."""
    outline_c = p.get("outline_colour", g.dominant_colour())
    fill_c = p.get("fill_colour", outline_c)
    h, w = g.shape
    seen = [[False]*w for _ in range(h)]
    # BFS from all border cells
    stack = []
    for r in range(h):
        for c in range(w):
            if r == 0 or r == h-1 or c == 0 or c == w-1:
                if g.cells[r][c] != outline_c:
                    stack.append((r, c))
                    seen[r][c] = True
    while stack:
        r, c = stack.pop()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r+dr, c+dc
                if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and g.cells[nr][nc] != outline_c:
                    seen[nr][nc] = True
                    stack.append((nr, nc))
    # Any unseen, non-outline cell is interior
    out = [row[:] for row in g.cells]
    for r in range(h):
        for c in range(w):
            if not seen[r][c] and g.cells[r][c] != outline_c:
                out[r][c] = fill_c
    return Grid(out)

def _op_outline(g: Grid, p: dict) -> Grid:
    """Keep only the 1-cell border of the dominant object; interior → 0."""
    dominant = g.dominant_colour()
    if dominant == 0:
        return g.copy()
    h, w = g.shape
    out = [[0]*w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if g.cells[r][c] != dominant:
                continue
            # Border if any 4-neighbour is not dominant or is off-grid
            is_border = False
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if not (0 <= nr < h and 0 <= nc < w) or g.cells[nr][nc] != dominant:
                    is_border = True
                    break
            if is_border:
                out[r][c] = dominant
    return Grid(out)

def _op_gravity_down(g: Grid, p: dict) -> Grid:
    """Each colour falls straight down until it hits the floor or another cell."""
    h, w = g.shape
    out = [[0]*w for _ in range(h)]
    for c in range(w):
        # Stack non-zero cells from bottom
        column = [g.cells[r][c] for r in range(h) if g.cells[r][c] != 0]
        # Place at bottom
        for i, v in enumerate(column):
            out[h - len(column) + i][c] = v
    return Grid(out)

def _op_gravity_up(g: Grid, p: dict) -> Grid:
    """Each colour falls straight up until it hits the ceiling or another cell."""
    h, w = g.shape
    out = [[0]*w for _ in range(h)]
    for c in range(w):
        column = [g.cells[r][c] for r in range(h) if g.cells[r][c] != 0]
        for i, v in enumerate(column):
            out[i][c] = v
    return Grid(out)

def _op_gravity_left(g: Grid, p: dict) -> Grid:
    """Each colour falls left until it hits the wall or another cell."""
    h, w = g.shape
    out = [[0]*w for _ in range(h)]
    for r in range(h):
        row = [v for v in g.cells[r] if v != 0]
        for i, v in enumerate(row):
            out[r][i] = v
    return Grid(out)

def _op_gravity_right(g: Grid, p: dict) -> Grid:
    """Each colour falls right until it hits the wall or another cell."""
    h, w = g.shape
    out = [[0]*w for _ in range(h)]
    for r in range(h):
        row = [v for v in g.cells[r] if v != 0]
        for i, v in enumerate(row):
            out[r][w - len(row) + i] = v
    return Grid(out)

def _op_dilate(g: Grid, p: dict) -> Grid:
    """Grow each cell of the specified colour by 1 in all 4 directions.
    params: colour (default: dominant)."""
    colour = p.get("colour", g.dominant_colour())
    if colour == 0:
        return g.copy()
    h, w = g.shape
    out = [row[:] for row in g.cells]
    for r in range(h):
        for c in range(w):
            if g.cells[r][c] != colour:
                # Check 4-neighbours
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w and g.cells[nr][nc] == colour:
                        out[r][c] = colour
                        break
    return Grid(out)

def _op_erode(g: Grid, p: dict) -> Grid:
    """Shrink each cell of the specified colour by removing border cells.
    params: colour (default: dominant)."""
    colour = p.get("colour", g.dominant_colour())
    if colour == 0:
        return g.copy()
    h, w = g.shape
    out = [row[:] for row in g.cells]
    for r in range(h):
        for c in range(w):
            if g.cells[r][c] != colour:
                continue
            # Border if any 4-neighbour is not this colour or off-grid
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if not (0 <= nr < h and 0 <= nc < w) or g.cells[nr][nc] != colour:
                    out[r][c] = 0
                    break
    return Grid(out)

def _op_replace_pattern(g: Grid, p: dict) -> Grid:
    """Find all occurrences of from_pattern and replace with to_pattern.
    params: from_pattern (2d list), to_pattern (2d list)."""
    fp = p.get("from_pattern", [])
    tp = p.get("to_pattern", [])
    if not fp or not tp:
        return g.copy()
    fph, fpw = len(fp), len(fp[0])
    tph, tpw = len(tp), len(tp[0])
    h, w = g.shape
    if fph > h or fpw > w:
        return g.copy()
    # Find all top-left positions where from_pattern matches
    matches = []
    for r in range(h - fph + 1):
        for c in range(w - fpw + 1):
            ok = True
            for dr in range(fph):
                for dc in range(fpw):
                    if g.cells[r+dr][c+dc] != fp[dr][dc]:
                        ok = False; break
                if not ok: break
            if ok:
                matches.append((r, c))
    if not matches:
        return g.copy()
    # Build output grid sized to fit the largest replacement
    # For simplicity: if to_pattern is same size as from_pattern, do in-place
    if fph == tph and fpw == tpw:
        out = [row[:] for row in g.cells]
        for r, c in matches:
            for dr in range(tph):
                for dc in range(tpw):
                    out[r+dr][c+dc] = tp[dr][dc]
        return Grid(out)
    # Different size — return original (v0 limitation)
    return g.copy()

# ══════════════════════════════════════════════════════════════════════════════
# v0.4 OPERATORS — conditional recolouring, row/col, extraction, drawing, tiling
# ══════════════════════════════════════════════════════════════════════════════

def _op_fill_interior_auto(g: Grid, p: dict) -> Grid:
    """Auto-detect the outline colour (most common non-zero colour forming a border)
    and fill the interior with the given fill_colour.

    params: fill_colour (default: dominant colour)
    """
    fill_c = p.get("fill_colour", g.dominant_colour())
    # Auto-detect outline: find the colour that forms the most enclosed regions
    # Heuristic: the outline colour is the one whose cells most often border 0-cells
    h, w = g.shape
    border_counts: dict = {}
    for r in range(h):
        for c in range(w):
            v = g.cells[r][c]
            if v == 0:
                continue
            # Count how many 0-neighbours this cell has
            zero_neighbours = 0
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if not (0 <= nr < h and 0 <= nc < w) or g.cells[nr][nc] == 0:
                    zero_neighbours += 1
            if zero_neighbours > 0:
                border_counts[v] = border_counts.get(v, 0) + 1
    if not border_counts:
        return g.copy()
    outline_c = max(border_counts, key=border_counts.get)
    # Now flood-fill interior
    return _op_fill_interior(g, {"outline_colour": outline_c, "fill_colour": fill_c})


def _op_recolour_interior(g: Grid, p: dict) -> Grid:
    """Recolour all interior cells (cells enclosed by an outline) to a given colour.
    Auto-detects the outline colour.
    params: new_colour
    """
    new_c = p.get("new_colour", g.dominant_colour())
    return _op_fill_interior_auto(g, {"fill_colour": new_c})


def _op_recolour_bg(g: Grid, p: dict) -> Grid:
    """Recolour all background (0) cells to a given colour.
    params: new_colour
    """
    new_c = p.get("new_colour", 1)
    return Grid([[new_c if v == 0 else v for v in row] for row in g.cells])


def _op_recolour_nonzero(g: Grid, p: dict) -> Grid:
    """Recolour all non-zero cells to a single colour.
    params: new_colour
    """
    new_c = p.get("new_colour", 1)
    return Grid([[new_c if v != 0 else 0 for v in row] for row in g.cells])


def _op_recolour_if_neighbour(g: Grid, p: dict) -> Grid:
    """Recolour cells that have at least one neighbour of a given colour.
    params: target_colour (cells to recolour), neighbour_colour (trigger), new_colour
    """
    target_c = p.get("target_colour", 0)
    neigh_c = p.get("neighbour_colour", 1)
    new_c = p.get("new_colour", 1)
    h, w = g.shape
    out = [row[:] for row in g.cells]
    for r in range(h):
        for c in range(w):
            if g.cells[r][c] != target_c:
                continue
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w and g.cells[nr][nc] == neigh_c:
                        out[r][c] = new_c
                        break
                else:
                    continue
                break
    return Grid(out)


def _op_recolour_if_border(g: Grid, p: dict) -> Grid:
    """Recolour cells on the grid border (row 0, row h-1, col 0, col w-1).
    params: new_colour, target_colour (default 0 = only background border cells)
    """
    new_c = p.get("new_colour", 1)
    target_c = p.get("target_colour", 0)
    h, w = g.shape
    out = [row[:] for row in g.cells]
    for c in range(w):
        if out[0][c] == target_c:
            out[0][c] = new_c
        if out[h-1][c] == target_c:
            out[h-1][c] = new_c
    for r in range(h):
        if out[r][0] == target_c:
            out[r][0] = new_c
        if out[r][w-1] == target_c:
            out[r][w-1] = new_c
    return Grid(out)


def _op_recolour_if_corner(g: Grid, p: dict) -> Grid:
    """Recolour cells at the four grid corners.
    params: new_colour
    """
    new_c = p.get("new_colour", 1)
    h, w = g.shape
    out = [row[:] for row in g.cells]
    out[0][0] = new_c
    out[0][w-1] = new_c
    out[h-1][0] = new_c
    out[h-1][w-1] = new_c
    return Grid(out)


def _op_shift_row(g: Grid, p: dict) -> Grid:
    """Shift a specific row left/right. Cells that fall off are lost.
    params: row_idx, shift (positive=right, negative=left)
    """
    row_idx = int(p.get("row_idx", 0))
    shift = int(p.get("shift", 1))
    h, w = g.shape
    if row_idx < 0 or row_idx >= h:
        return g.copy()
    out = [row[:] for row in g.cells]
    new_row = [0] * w
    for c in range(w):
        nc = c + shift
        if 0 <= nc < w:
            new_row[nc] = g.cells[row_idx][c]
    out[row_idx] = new_row
    return Grid(out)


def _op_shift_col(g: Grid, p: dict) -> Grid:
    """Shift a specific column up/down. Cells that fall off are lost.
    params: col_idx, shift (positive=down, negative=up)
    """
    col_idx = int(p.get("col_idx", 0))
    shift = int(p.get("shift", 1))
    h, w = g.shape
    if col_idx < 0 or col_idx >= w:
        return g.copy()
    out = [row[:] for row in g.cells]
    new_col = [0] * h
    for r in range(h):
        nr = r + shift
        if 0 <= nr < h:
            new_col[nr] = g.cells[r][col_idx]
    for r in range(h):
        out[r][col_idx] = new_col[r]
    return Grid(out)


def _op_fill_row(g: Grid, p: dict) -> Grid:
    """Fill an entire row with a colour.
    params: row_idx, colour
    """
    row_idx = int(p.get("row_idx", 0))
    colour = int(p.get("colour", 1))
    h, w = g.shape
    if row_idx < 0 or row_idx >= h:
        return g.copy()
    out = [row[:] for row in g.cells]
    out[row_idx] = [colour] * w
    return Grid(out)


def _op_fill_col(g: Grid, p: dict) -> Grid:
    """Fill an entire column with a colour.
    params: col_idx, colour
    """
    col_idx = int(p.get("col_idx", 0))
    colour = int(p.get("colour", 1))
    h, w = g.shape
    if col_idx < 0 or col_idx >= w:
        return g.copy()
    out = [row[:] for row in g.cells]
    for r in range(h):
        out[r][col_idx] = colour
    return Grid(out)


def _op_copy_row(g: Grid, p: dict) -> Grid:
    """Copy one row to another.
    params: from_idx, to_idx
    """
    from_idx = int(p.get("from_idx", 0))
    to_idx = int(p.get("to_idx", 1))
    h, w = g.shape
    if from_idx < 0 or from_idx >= h or to_idx < 0 or to_idx >= h:
        return g.copy()
    out = [row[:] for row in g.cells]
    out[to_idx] = out[from_idx][:]
    return Grid(out)


def _op_copy_col(g: Grid, p: dict) -> Grid:
    """Copy one column to another.
    params: from_idx, to_idx
    """
    from_idx = int(p.get("from_idx", 0))
    to_idx = int(p.get("to_idx", 1))
    h, w = g.shape
    if from_idx < 0 or from_idx >= w or to_idx < 0 or to_idx >= w:
        return g.copy()
    out = [row[:] for row in g.cells]
    for r in range(h):
        out[r][to_idx] = out[r][from_idx]
    return Grid(out)


def _op_extract_largest(g: Grid, p: dict) -> Grid:
    """Extract the largest connected component (by cell count).
    Returns a new grid cropped to the bbox of that component."""
    h, w = g.shape
    seen = [[False]*w for _ in range(h)]
    best_comp = []
    for r in range(h):
        for c in range(w):
            if g.cells[r][c] != 0 and not seen[r][c]:
                # BFS
                comp = []
                stack = [(r, c)]
                seen[r][c] = True
                colour = g.cells[r][c]
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr+dr, cc+dc
                            if (0 <= nr < h and 0 <= nc < w
                                    and not seen[nr][nc]
                                    and g.cells[nr][nc] == colour):
                                seen[nr][nc] = True
                                stack.append((nr, nc))
                if len(comp) > len(best_comp):
                    best_comp = comp
    if not best_comp:
        return g.copy()
    # Crop to bbox
    rs = [r for r, _ in best_comp]
    cs = [c for _, c in best_comp]
    rmin, rmax, cmin, cmax = min(rs), max(rs), min(cs), max(cs)
    out = [[g.cells[r][c] if (r, c) in set(best_comp) else 0
            for c in range(cmin, cmax+1)]
           for r in range(rmin, rmax+1)]
    return Grid(out)


def _op_extract_colour(g: Grid, p: dict) -> Grid:
    """Extract all cells of a given colour; set everything else to 0.
    params: colour
    """
    colour = int(p.get("colour", g.dominant_colour()))
    return Grid([[v if v == colour else 0 for v in row] for row in g.cells])


def _op_draw_line(g: Grid, p: dict) -> Grid:
    """Draw a line from (r1,c1) to (r2,c2) using Bresenham.
    params: r1, c1, r2, c2, colour
    """
    r1 = int(p.get("r1", 0)); c1 = int(p.get("c1", 0))
    r2 = int(p.get("r2", 0)); c2 = int(p.get("c2", 0))
    colour = int(p.get("colour", 1))
    h, w = g.shape
    out = [row[:] for row in g.cells]
    # Bresenham
    dr = abs(r2 - r1); dc = abs(c2 - c1)
    sr = 1 if r1 < r2 else -1; sc = 1 if c1 < c2 else -1
    err = dr - dc
    r, c = r1, c1
    while True:
        if 0 <= r < h and 0 <= c < w:
            out[r][c] = colour
        if r == r2 and c == c2:
            break
        e2 = 2 * err
        if e2 > -dc:
            err -= dc; r += sr
        if e2 < dr:
            err += dr; c += sc
    return Grid(out)


def _op_draw_rect_outline(g: Grid, p: dict) -> Grid:
    """Draw a rectangle outline from (r1,c1) to (r2,c2).
    params: r1, c1, r2, c2, colour
    """
    r1 = int(p.get("r1", 0)); c1 = int(p.get("c1", 0))
    r2 = int(p.get("r2", 1)); c2 = int(p.get("c2", 1))
    colour = int(p.get("colour", 1))
    h, w = g.shape
    out = [row[:] for row in g.cells]
    rmin, rmax = min(r1, r2), max(r1, r2)
    cmin, cmax = min(c1, c2), max(c1, c2)
    for c in range(cmin, cmax+1):
        if 0 <= rmin < h and 0 <= c < w:
            out[rmin][c] = colour
        if 0 <= rmax < h and 0 <= c < w:
            out[rmax][c] = colour
    for r in range(rmin, rmax+1):
        if 0 <= r < h and 0 <= cmin < w:
            out[r][cmin] = colour
        if 0 <= r < h and 0 <= cmax < w:
            out[r][cmax] = colour
    return Grid(out)


def _op_draw_rect_fill(g: Grid, p: dict) -> Grid:
    """Draw a filled rectangle from (r1,c1) to (r2,c2).
    params: r1, c1, r2, c2, colour
    """
    r1 = int(p.get("r1", 0)); c1 = int(p.get("c1", 0))
    r2 = int(p.get("r2", 1)); c2 = int(p.get("c2", 1))
    colour = int(p.get("colour", 1))
    h, w = g.shape
    out = [row[:] for row in g.cells]
    rmin, rmax = min(r1, r2), max(r1, r2)
    cmin, cmax = min(c1, c2), max(c1, c2)
    for r in range(rmin, rmax+1):
        for c in range(cmin, cmax+1):
            if 0 <= r < h and 0 <= c < w:
                out[r][c] = colour
    return Grid(out)


def _op_tile_2x(g: Grid, p: dict) -> Grid:
    """Tile the grid 2x in both dimensions (output is 2h x 2w)."""
    h, w = g.shape
    out = [[0]*(w*2) for _ in range(h*2)]
    for r in range(h):
        for c in range(w):
            v = g.cells[r][c]
            out[r][c] = v
            out[r][c+w] = v
            out[r+h][c] = v
            out[r+h][c+w] = v
    return Grid(out)


def _op_tile_3x(g: Grid, p: dict) -> Grid:
    """Tile the grid 3x in both dimensions (output is 3h x 3w)."""
    h, w = g.shape
    out = [[0]*(w*3) for _ in range(h*3)]
    for r in range(h):
        for c in range(w):
            v = g.cells[r][c]
            for dr in range(3):
                for dc in range(3):
                    out[r+dr*h][c+dc*w] = v
    return Grid(out)


def _op_crop_to_nonzero(g: Grid, p: dict) -> Grid:
    """Crop the grid to the bounding box of all non-zero cells."""
    h, w = g.shape
    rmin, rmax, cmin, cmax = h, -1, w, -1
    for r in range(h):
        for c in range(w):
            if g.cells[r][c] != 0:
                rmin = min(rmin, r); rmax = max(rmax, r)
                cmin = min(cmin, c); cmax = max(cmax, c)
    if rmax < 0:
        return g.copy()
    return Grid([[g.cells[r][c] for c in range(cmin, cmax+1)] for r in range(rmin, rmax+1)])


# Operator dispatch table
OP_IMPL: Dict[Ops, Callable[[Grid, dict], Grid]] = {
    Ops.IDENTITY:       _op_identity,
    Ops.ROTATE_90:      _op_rotate_90,
    Ops.ROTATE_180:     _op_rotate_180,
    Ops.ROTATE_270:     _op_rotate_270,
    Ops.FLIP_H:         _op_flip_h,
    Ops.FLIP_V:         _op_flip_v,
    Ops.TRANSPOSE:      _op_transpose,
    Ops.SCALE_2X:       _op_scale_2x,
    Ops.SCALE_HALF:     _op_scale_half,
    Ops.TRANSLATE:      _op_translate,
    Ops.RECOLOUR:       _op_recolour,
    Ops.SET_INTERSECT:  _op_set_intersect,
    Ops.SET_DIFFERENCE: _op_set_difference,
    Ops.SET_UNION:      _op_set_union,
    Ops.REPLICATE:      _op_replicate,
    Ops.COUNT_FILL:     _op_count_fill,
    Ops.FILL_INTERIOR:  _op_fill_interior,
    Ops.OUTLINE:        _op_outline,
    Ops.DILATE:         _op_dilate,
    Ops.ERODE:          _op_erode,
    Ops.GRAVITY_DOWN:   _op_gravity_down,
    Ops.GRAVITY_UP:     _op_gravity_up,
    Ops.GRAVITY_LEFT:   _op_gravity_left,
    Ops.GRAVITY_RIGHT:  _op_gravity_right,
    Ops.REPLACE_PATTERN:_op_replace_pattern,
    # v0.4 operators
    Ops.FILL_INTERIOR_AUTO:    _op_fill_interior_auto,
    Ops.RECOLOUR_INTERIOR:     _op_recolour_interior,
    Ops.RECOLOUR_BG:           _op_recolour_bg,
    Ops.RECOLOUR_NONZERO:      _op_recolour_nonzero,
    Ops.RECOLOUR_IF_NEIGHBOUR: _op_recolour_if_neighbour,
    Ops.RECOLOUR_IF_BORDER:    _op_recolour_if_border,
    Ops.RECOLOUR_IF_CORNER:    _op_recolour_if_corner,
    Ops.SHIFT_ROW:             _op_shift_row,
    Ops.SHIFT_COL:             _op_shift_col,
    Ops.FILL_ROW:              _op_fill_row,
    Ops.FILL_COL:              _op_fill_col,
    Ops.COPY_ROW:              _op_copy_row,
    Ops.COPY_COL:              _op_copy_col,
    Ops.EXTRACT_LARGEST:       _op_extract_largest,
    Ops.EXTRACT_COLOUR:        _op_extract_colour,
    Ops.DRAW_LINE:             _op_draw_line,
    Ops.DRAW_RECT_OUTLINE:     _op_draw_rect_outline,
    Ops.DRAW_RECT_FILL:        _op_draw_rect_fill,
    Ops.TILE_2X:               _op_tile_2x,
    Ops.TILE_3X:               _op_tile_3x,
    Ops.CROP_TO_NONZERO:       _op_crop_to_nonzero,
}


# ══════════════════════════════════════════════════════════════════════════════
# PROGRAM
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Operation:
    """A single DSL operation: an Op enum + its parameters."""
    op: Ops
    params: Dict[str, Any] = field(default_factory=dict)

    def apply(self, grid: Grid) -> Grid:
        impl = OP_IMPL.get(self.op)
        if impl is None:
            raise ValueError(f"Unknown op: {self.op}")
        return impl(grid, self.params)

    def __repr__(self):
        if self.params:
            return f"Op({self.op.value}, {self.params})"
        return f"Op({self.op.value})"


@dataclass
class Program:
    """A pipeline of Operations applied left-to-right."""
    operations: List[Operation] = field(default_factory=list)
    name: str = "<anonymous>"

    def apply(self, grid: Grid) -> Grid:
        g = grid
        for op in self.operations:
            g = op.apply(g)
        return g

    def matches_train(self, task: ARCTask) -> bool:
        """Returns True iff this program reproduces every train output exactly."""
        for pair in task.train:
            if self.apply(pair.input) != pair.output:
                return False
        return True

    def __repr__(self):
        ops_str = " → ".join(str(op) for op in self.operations)
        return f"Program({self.name}: {ops_str})"

    def __len__(self):
        return len(self.operations)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "operations": [
                {"op": op.op.value, "params": op.params} for op in self.operations
            ],
        }
