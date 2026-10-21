"""Synthetic binary task families with verified transformation traces (stdlib port of the
study's scripts/bin_tasks.py; same five families and the same trace step names).

NOTE: the study used numpy's default_rng, this port uses random.Random, so individual samples
differ from the study's samples; the families, shapes and trace structure are identical.
"""
from __future__ import annotations
import random
from typing import Dict, List, Tuple

Grid = List[List[int]]


def new_grid(h: int, w: int) -> Grid:
    return [[0] * w for _ in range(h)]


def copy(g: Grid) -> Grid:
    return [row[:] for row in g]


def flatten(g: Grid) -> List[int]:
    return [v for row in g for v in row]


def grid_to_word(g: Grid, msb_first: bool = True) -> int:
    """Row-major word.  msb_first=True matches the study scripts (first cell = highest bit)."""
    cells = flatten(g)
    w = 0
    if msb_first:
        for v in cells:
            w = (w << 1) | (v & 1)
    else:
        for i, v in enumerate(cells):
            w |= (v & 1) << i
    return w


def gen_toggle(seed: int, H: int = 4, W: int = 6, **kw):
    rng = random.Random(seed)
    x = [[rng.randint(0, 1) for _ in range(W)] for _ in range(H)]
    y = [[1 - v for v in row] for row in x]
    return x, y, [("init", copy(x)), ("bitwise_not", copy(y))]


def gen_translate(seed: int, H: int = 4, W: int = 6, dx: int = 1, dy: int = 1,
                  bh: int = 2, bw: int = 2, **kw):
    rng = random.Random(seed)
    floor = H >= 4
    rows_avail = H - 1 if floor else H
    top = rng.randint(0, max(0, rows_avail - bh - dy))
    left = rng.randint(0, max(0, W - bw - dx))
    x = new_grid(H, W)
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            x[r][c] = 1
    if floor:
        x[H - 1] = [1] * W
    mask = new_grid(H, W)
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            mask[r][c] = 1
    erased = copy(x)
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            erased[r][c] = 0
    painted = copy(erased)
    for r in range(top + dy, top + dy + bh):
        for c in range(left + dx, left + dx + bw):
            painted[r][c] = 1
    if floor:
        painted[H - 1] = [1] * W
    y = copy(painted)
    return x, y, [("init", copy(x)), ("mask_block", mask), ("erase_old", erased),
                  ("paint_new", painted)]


def gen_reflect_v(seed: int, H: int = 4, W: int = 6, **kw):
    rng = random.Random(seed)
    x = new_grid(H, W)
    for _ in range(rng.randint(2, 4)):
        bh, bw = rng.randint(1, 2), rng.randint(1, 2)
        t, l = rng.randint(0, H - bh), rng.randint(0, W - bw)
        for r in range(t, t + bh):
            for c in range(l, l + bw):
                x[r][c] = 1
    y = [row[::-1] for row in x]
    return x, y, [("init", copy(x)), ("flip_horizontal", copy(y))]


def gen_flood_fill(seed: int, H: int = 4, W: int = 6, **kw):
    rng = random.Random(seed)
    h = rng.randint(max(3, H // 2), H)
    w = rng.randint(max(3, W // 2), W)
    top, left = rng.randint(0, H - h), rng.randint(0, W - w)
    x = new_grid(H, W)
    for c in range(left, left + w):
        x[top][c] = x[top + h - 1][c] = 1
    for r in range(top, top + h):
        x[r][left] = x[r][left + w - 1] = 1
    y = copy(x)
    for r in range(top + 1, top + h - 1):
        for c in range(left + 1, left + w - 1):
            y[r][c] = 1
    return x, y, [("init", copy(x)), ("fill_interior", copy(y))]


def gen_bfs_shortest(seed: int, H: int = 4, W: int = 6, **kw):
    rng = random.Random(seed)
    cells = set()
    while len(cells) < 2:
        cells.add((rng.randrange(H), rng.randrange(W)))
    (r1, c1), (r2, c2) = sorted(cells)
    x = new_grid(H, W)
    x[r1][c1] = x[r2][c2] = 1
    trace = [("init", copy(x))]
    cur = copy(x)
    r, c = r1, c1
    while r != r2:
        r += 1 if r2 > r else -1
        cur[r][c] = 1
        trace.append(("step_vertical", copy(cur)))
    while c != c2:
        c += 1 if c2 > c else -1
        cur[r][c] = 1
        trace.append(("step_horizontal", copy(cur)))
    trace.append(("final", copy(cur)))
    return x, copy(cur), trace


TASKS = {
    "toggle": gen_toggle,
    "translate": gen_translate,
    "reflect_v": gen_reflect_v,
    "flood_fill": gen_flood_fill,
    "bfs_shortest": gen_bfs_shortest,
}


def verify_trace(x: Grid, y: Grid, trace) -> bool:
    """A trace is well-formed iff it starts at x and ends at y (the TraceViT/Note-2 requirement)."""
    return trace[0][1] == x and trace[-1][1] == y


def sample(name: str, seed: int, H: int = 4, W: int = 6, **kw) -> Tuple[Grid, Grid, list]:
    return TASKS[name](seed, H=H, W=W, **kw)
