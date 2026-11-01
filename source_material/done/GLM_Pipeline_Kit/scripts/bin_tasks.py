#!/usr/bin/env python3
"""
Synthetic binary task generators for the GLM experiments.

Each task family exposes:
    generate(seed, H, W, ...) -> (input_grid, output_grid, intermediate_states)

where intermediate_states is a list of (label, grid) tuples in execution order,
matching the "verified transformation traces" requirement of TraceViT / Note 2.

All grids are numpy 2D arrays of {0,1} (uint8). Pure substrate, no ARC dependency.

Task families:
    toggle        - y = NOT x.        Δ_x = all-ones (constant) — DISPLACEMENT TRANSFERS.
    translate     - move a 1-block by (dx,dy). Δ depends on position — DISPLACEMENT FAILS.
    reflect_v     - y = mirror across vertical axis. Δ depends on contents — DISPLACEMENT FAILS.
    flood_fill    - fill enclosed region. Δ depends on geometry — DISPLACEMENT FAILS.
    bfs_shortest  - mark shortest path between two marked bits — DISPLACEMENT FAILS.

Usage:
    from scripts.bin_tasks import TASKS, sample_task
    task = TASKS["translate"]
    x, y, trace = task.generate(seed=0, H=8, W=8, dx=2, dy=1)
"""

from __future__ import annotations
import sys, os
from typing import List, Tuple, Dict, Callable, Any
import numpy as np

Grid = np.ndarray   # shape (H, W), dtype uint8, values in {0,1}

def _new_grid(H: int, W: int) -> Grid:
    return np.zeros((H, W), dtype=np.uint8)

def _random_block(seed: int, H: int, W: int, block_h: int = 2, block_w: int = 2):
    rng = np.random.default_rng(seed)
    # leave a 1-cell margin so translations can move within bounds
    top = rng.integers(1, max(2, H - block_h))
    left = rng.integers(1, max(2, W - block_w))
    return int(top), int(left)

# ---------------------------------------------------------------------------
# Task: TOGGLE  -- y = NOT x.  Δ_x is the all-ones grid (constant, transfers).
# ---------------------------------------------------------------------------
def gen_toggle(seed: int, H: int = 8, W: int = 8, **kw) -> Tuple[Grid, Grid, List[Tuple[str, Grid]]]:
    rng = np.random.default_rng(seed)
    x = rng.integers(0, 2, size=(H, W)).astype(np.uint8)
    y = (1 - x).astype(np.uint8)
    trace = [("init", x.copy()), ("bitwise_not", y.copy())]
    return x, y, trace

# ---------------------------------------------------------------------------
# Task: TRANSLATE -- place a single 2x2 block, then move it by (dx, dy).
# ---------------------------------------------------------------------------
def gen_translate(seed: int, H: int = 8, W: int = 8,
                  block_h: int = 2, block_w: int = 2,
                  dx: int = 0, dy: int = 0, **kw) -> Tuple[Grid, Grid, List[Tuple[str, Grid]]]:
    rng = np.random.default_rng(seed)
    x = _new_grid(H, W)
    # choose a position with room to translate by (dy, dx)
    if dy >= 0:
        top = rng.integers(1, max(2, H - block_h - dy))
    else:
        top = rng.integers(1 - dy, max(2 - dy, H - block_h))
    if dx >= 0:
        left = rng.integers(1, max(2, W - block_w - dx))
    else:
        left = rng.integers(1 - dx, max(2 - dx, W - block_w))
    x[top:top+block_h, left:left+block_w] = 1
    # also a "floor" indicator row at the bottom (a 1xW line of 1s)
    if H >= 4:
        x[H-1, :] = 1
    y = x.copy()
    # erase the block at the old position
    y[top:top+block_h, left:left+block_w] = 0
    # paint it at the new position
    new_top, new_left = top + dy, left + dx
    y[new_top:new_top+block_h, new_left:new_left+block_w] = 1
    # restore floor
    if H >= 4:
        y[H-1, :] = 1
    # trace: init -> mask_block -> erase_old -> paint_new
    mask = _new_grid(H, W)
    mask[top:top+block_h, left:left+block_w] = 1
    erased = x.copy()
    erased[top:top+block_h, left:left+block_w] = 0
    if H >= 4:
        erased[H-1, :] = 1
    painted = erased.copy()
    painted[new_top:new_top+block_h, new_left:new_left+block_w] = 1
    if H >= 4:
        painted[H-1, :] = 1
    trace = [("init", x.copy()),
             ("mask_block", mask),
             ("erase_old", erased),
             ("paint_new", painted)]
    return x, y, trace

# ---------------------------------------------------------------------------
# Task: REFLECT_V -- mirror across the vertical centre axis.
# ---------------------------------------------------------------------------
def gen_reflect_v(seed: int, H: int = 8, W: int = 8, **kw) -> Tuple[Grid, Grid, List[Tuple[str, Grid]]]:
    rng = np.random.default_rng(seed)
    # Build a non-symmetric grid so the reflection is non-trivial.
    # Place a few random small blocks at distinct positions.
    x = _new_grid(H, W)
    n_blocks = int(rng.integers(2, 5))
    positions = []
    for _ in range(n_blocks):
        bh = int(rng.integers(1, 3))
        bw = int(rng.integers(1, 3))
        t = int(rng.integers(0, max(1, H - bh + 1)))
        l = int(rng.integers(0, max(1, W - bw + 1)))
        x[t:t+bh, l:l+bw] = 1
        positions.append((t, l, bh, bw))
    y = x[:, ::-1].copy()
    trace = [("init", x.copy()), ("flip_horizontal", y.copy())]
    return x, y, trace

# ---------------------------------------------------------------------------
# Task: FLOOD_FILL -- fill the interior of a closed boundary.
# ---------------------------------------------------------------------------
def gen_flood_fill(seed: int, H: int = 8, W: int = 8, **kw) -> Tuple[Grid, Grid, List[Tuple[str, Grid]]]:
    rng = np.random.default_rng(seed)
    x = _new_grid(H, W)
    # Draw a closed rectangular boundary of 1s with empty interior.
    # Vary size and position so the rule is non-trivial.
    h = int(rng.integers(max(3, H // 2), H))
    w = int(rng.integers(max(3, W // 2), W))
    top = int(rng.integers(0, max(1, H - h)))
    left = int(rng.integers(0, max(1, W - w)))
    # boundary
    x[top, left:left+w] = 1
    x[top+h-1, left:left+w] = 1
    x[top:top+h, left] = 1
    x[top:top+h, left+w-1] = 1
    # interior is empty (0) -- this is the "unfilled" state
    # Output: fill the interior
    y = x.copy()
    if h > 2 and w > 2:
        y[top+1:top+h-1, left+1:left+w-1] = 1
    trace = [("init", x.copy()), ("fill_interior", y.copy())]
    return x, y, trace

# ---------------------------------------------------------------------------
# Task: BFS_SHORTEST -- given a start bit and an end bit on a 0-grid, mark the
# shortest Manhattan path between them.
# ---------------------------------------------------------------------------
def gen_bfs_shortest(seed: int, H: int = 8, W: int = 8, **kw) -> Tuple[Grid, Grid, List[Tuple[str, Grid]]]:
    rng = np.random.default_rng(seed)
    x = _new_grid(H, W)
    # Place two distinct marked cells
    cells = set()
    while len(cells) < 2:
        r = int(rng.integers(0, H))
        c = int(rng.integers(0, W))
        cells.add((r, c))
    (r1, c1), (r2, c2) = sorted(cells)
    x[r1, c1] = 1
    x[r2, c2] = 1
    # Build y: mark the L-shaped shortest path
    y = x.copy()
    # Move vertically first, then horizontally
    step_r = 1 if r2 > r1 else -1
    step_c = 1 if c2 > c1 else -1
    trace_grids = [("init", x.copy())]
    # Vertical segment
    cur_r = r1
    intermediate = x.copy()
    while cur_r != r2:
        cur_r += step_r
        intermediate[cur_r, c1] = 1
        trace_grids.append(("step_vertical", intermediate.copy()))
    # Horizontal segment
    cur_c = c1
    while cur_c != c2:
        cur_c += step_c
        intermediate[cur_r, cur_c] = 1
        trace_grids.append(("step_horizontal", intermediate.copy()))
    y = intermediate.copy()
    trace_grids.append(("final", y.copy()))
    return x, y, trace_grids

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
class TaskFamily:
    def __init__(self, name: str, gen: Callable, transfer_safe: bool = False,
                 description: str = ""):
        self.name = name
        self.gen = gen
        self.transfer_safe = transfer_safe  # True if Δ_x transfers (only toggle)
        self.description = description
    def generate(self, seed: int, H: int = 8, W: int = 8, **kw):
        return self.gen(seed=seed, H=H, W=W, **kw)

TASKS: Dict[str, TaskFamily] = {
    "toggle":      TaskFamily("toggle",      gen_toggle,      transfer_safe=True,
                               description="y = NOT x; Δ_x is constant all-ones (displacement transfers)."),
    "translate":   TaskFamily("translate",   gen_translate,   transfer_safe=False,
                               description="Move a 2x2 block by (dx,dy); Δ depends on block position."),
    "reflect_v":   TaskFamily("reflect_v",   gen_reflect_v,   transfer_safe=False,
                               description="Mirror across vertical axis; Δ depends on contents."),
    "flood_fill":  TaskFamily("flood_fill",  gen_flood_fill,  transfer_safe=False,
                               description="Fill interior of closed boundary; Δ depends on geometry."),
    "bfs_shortest":TaskFamily("bfs_shortest",gen_bfs_shortest,transfer_safe=False,
                               description="Mark shortest Manhattan path between two bits."),
}


def sample_task(name: str, seed: int, H: int = 8, W: int = 8, **kw):
    return TASKS[name].generate(seed=seed, H=H, W=W, **kw)


def make_demo_set(name: str, n: int, H: int = 8, W: int = 8,
                  seed_offset: int = 0, **kw) -> List[Dict[str, Any]]:
    """Produce n demonstrations of one task family, each as {x, y, trace}."""
    out: List[Dict[str, Any]] = []
    for i in range(n):
        x, y, trace = sample_task(name, seed=seed_offset + i, H=H, W=W, **kw)
        out.append({"x": x, "y": y, "trace": trace,
                    "H": H, "W": W, "task": name, "seed": seed_offset + i})
    return out


if __name__ == "__main__":
    # quick smoke test
    for name, fam in TASKS.items():
        x, y, trace = fam.generate(seed=0, H=8, W=8)
        print(f"{name:14s} H={x.shape[0]} W={x.shape[1]} trace_len={len(trace)} "
              f"transfer_safe={fam.transfer_safe}")
    print("OK")
