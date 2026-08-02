"""
v053_compositional.py — Compositional Multi-Step Solver using D/X/N/J Primitives
=================================================================================

Uses the UBP Construction System's D/X/N/J primitives as the compositional
vocabulary for multi-step ARC transformations.

D = extend forward (fill/propagate in positive direction)
X = extend backward (fill/propagate in negative direction)
N = nest (place transformed object inside context)
J = join (combine two transformations)

Each ARC transformation is modeled as a ConstructionPath of 2-3 steps.
The solver tries all compositions and hard-gates against train pairs.

Targets: tasks that need multi-step reasoning (background fill + object transform,
erase + fill, propagation, etc.)

Full transparency: every result is reported honestly.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set, Callable
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import sys, os, signal

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task


# ══════════════════════════════════════════════════════════════════════════════
# PRIMITIVE OPERATIONS (D/X/N/J mapped to ARC operations)
# ══════════════════════════════════════════════════════════════════════════════

def op_D_fill(grid: Grid, fill_colour: int) -> Grid:
    """D-primitive: fill all zeros with a colour (extend forward)."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if cells[r][c] == 0:
                cells[r][c] = fill_colour
    return Grid(cells)


def op_X_erase(grid: Grid, erase_colour: int) -> Grid:
    """X-primitive: erase a colour (set to 0, extend backward)."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if cells[r][c] == erase_colour:
                cells[r][c] = 0
    return Grid(cells)


def op_N_recolour(grid: Grid, from_col: int, to_col: int) -> Grid:
    """N-primitive: nest a recolour (replace one colour with another)."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if cells[r][c] == from_col:
                cells[r][c] = to_col
    return Grid(cells)


def op_J_swap(grid: Grid, col_a: int, col_b: int) -> Grid:
    """J-primitive: join/swap two colours."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if cells[r][c] == col_a:
                cells[r][c] = col_b
            elif cells[r][c] == col_b:
                cells[r][c] = col_a
    return Grid(cells)


def op_D_propagate(grid: Grid) -> Grid:
    """D-primitive variant: propagate non-zero into adjacent zeros (1 step)."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
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
                    cells[r][c] = n_cols[0]
                    changed = True
                elif len(n_cols) > 1:
                    cells[r][c] = Counter(n_cols).most_common(1)[0][0]
                    changed = True
    return Grid(cells) if changed else grid


def op_D_propagate_k(grid: Grid, k: int = 2) -> Grid:
    """D-primitive: propagate k steps."""
    result = grid
    for _ in range(k):
        new = op_D_propagate(result)
        if new is result:
            break
        result = new
    return result


def op_N_interior_fill(grid: Grid, fill_colour: int) -> Grid:
    """N-primitive: fill enclosed zeros (interior of boundaries)."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]

    # Find zeros connected to border
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
                cells[r][c] = fill_colour
                changed = True

    return Grid(cells) if changed else grid


def op_N_extend_object_right(grid: Grid, fill_colour: int) -> Grid:
    """N-primitive: extend each row's rightmost non-zero cell rightward by 1."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    changed = False
    for r in range(h):
        rightmost = -1
        for c in range(w-1, -1, -1):
            if grid.cells[r][c] != 0:
                rightmost = c
                break
        if rightmost >= 0 and rightmost + 1 < w and cells[r][rightmost + 1] == 0:
            cells[r][rightmost + 1] = fill_colour
            changed = True
    return Grid(cells) if changed else grid


def op_N_extend_object_down(grid: Grid, fill_colour: int) -> Grid:
    """N-primitive: extend each column's bottommost non-zero cell downward by 1."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    changed = False
    for c in range(w):
        bottommost = -1
        for r in range(h-1, -1, -1):
            if grid.cells[r][c] != 0:
                bottommost = r
                break
        if bottommost >= 0 and bottommost + 1 < h and cells[bottommost + 1][c] == 0:
            cells[bottommost + 1][c] = fill_colour
            changed = True
    return Grid(cells) if changed else grid


def op_N_local_colour_swap(grid: Grid) -> Grid:
    """N-primitive: for each connected component with exactly 2 colours, swap them."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    visited = set()

    for r in range(h):
        for c in range(w):
            if (r, c) in visited or grid.cells[r][c] == 0:
                continue
            # BFS for component
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


# ══════════════════════════════════════════════════════════════════════════════
# COMPOSITIONAL SEARCH
# ══════════════════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c] for r in range(g1.height) for c in range(g1.width))


def verify_and_predict(fn: Callable, task: ARCTask) -> Optional[Tuple[Grid, str]]:
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


def learn_bg_fill(task: ARCTask) -> Optional[int]:
    """Learn background fill colour from train pairs."""
    fills = set()
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    fills.add(pair.output.cells[r][c])
    if len(fills) == 1:
        return fills.pop()
    return None


def learn_recolour_map(task: ARCTask) -> Optional[Dict[int, int]]:
    """Learn consistent colour mapping from train pairs."""
    cmap = {}
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                if ic != oc:
                    if ic in cmap:
                        if cmap[ic] != oc:
                            return None
                    else:
                        cmap[ic] = oc
    return {k: v for k, v in cmap.items() if k != v} or None


def learn_erase_colours(task: ARCTask) -> Optional[Set[int]]:
    """Learn which colours are erased from train pairs."""
    erase = set()
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c] != 0 and pair.output.cells[r][c] == 0:
                    erase.add(pair.input.cells[r][c])
    return erase if erase else None


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Try compositional paths
# ══════════════════════════════════════════════════════════════════════════════

def solve(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Try compositional multi-step transformations."""
    same_size = all(p.input.height == p.output.height and p.input.width == p.output.width
                    for p in task.train)
    if not same_size:
        return None

    bg = learn_bg_fill(task)
    cmap = learn_recolour_map(task)
    erase_cols = learn_erase_colours(task)

    # ═══ 2-step compositions ═══

    # Pattern 1: Recolour + Fill (N then D)
    if cmap and bg is not None:
        for from_col, to_col in cmap.items():
            def make_rc_fill(fc, tc, b):
                def fn(grid):
                    step1 = op_N_recolour(grid, fc, tc)
                    step2 = op_D_fill(step1, b)
                    return step2
                return fn
            result = verify_and_predict(make_rc_fill(from_col, to_col, bg), task)
            if result:
                return result, f"recolour({from_col}→{to_col}) + fill({bg})"

    # Pattern 2: Fill + Recolour (D then N)
    if bg is not None and cmap:
        for from_col, to_col in cmap.items():
            def make_fill_rc(b, fc, tc):
                def fn(grid):
                    step1 = op_D_fill(grid, b)
                    step2 = op_N_recolour(step1, fc, tc)
                    return step2
                return fn
            result = verify_and_predict(make_fill_rc(bg, from_col, to_col), task)
            if result:
                return result, f"fill({bg}) + recolour({from_col}→{to_col})"

    # Pattern 3: Erase + Fill (X then D)
    if erase_cols and bg is not None:
        for ecol in erase_cols:
            def make_erase_fill(ec, b):
                def fn(grid):
                    step1 = op_X_erase(grid, ec)
                    step2 = op_D_fill(step1, b)
                    return step2
                return fn
            result = verify_and_predict(make_erase_fill(ecol, bg), task)
            if result:
                return result, f"erase({ecol}) + fill({bg})"

    # Pattern 4: Erase + Recolour (X then N)
    if erase_cols and cmap:
        for ecol in erase_cols:
            for from_col, to_col in cmap.items():
                def make_erase_rc(ec, fc, tc):
                    def fn(grid):
                        step1 = op_X_erase(grid, ec)
                        step2 = op_N_recolour(step1, fc, tc)
                        return step2
                    return fn
                result = verify_and_predict(make_erase_rc(ecol, from_col, to_col), task)
                if result:
                    return result, f"erase({ecol}) + recolour({from_col}→{to_col})"

    # Pattern 5: Recolour + Recolour (N then N)
    if cmap and len(cmap) >= 2:
        items = list(cmap.items())
        for i in range(len(items)):
            for j in range(len(items)):
                if i == j:
                    continue
                f1, t1 = items[i]
                f2, t2 = items[j]
                def make_rc_rc(a, b, c, d):
                    def fn(grid):
                        step1 = op_N_recolour(grid, a, b)
                        step2 = op_N_recolour(step1, c, d)
                        return step2
                    return fn
                result = verify_and_predict(make_rc_rc(f1, t1, f2, t2), task)
                if result:
                    return result, f"recolour({f1}→{t1}) + recolour({f2}→{t2})"

    # Pattern 6: Fill + Propagate (D then D-propagate)
    if bg is not None:
        def make_fill_propagate(b):
            def fn(grid):
                step1 = op_D_fill(grid, b)
                step2 = op_D_propagate(step1)
                return step2
            return fn
        result = verify_and_predict(make_fill_propagate(bg), task)
        if result:
            return result, f"fill({bg}) + propagate"

    # Pattern 7: Propagate + Fill
    if bg is not None:
        def make_propagate_fill(b):
            def fn(grid):
                step1 = op_D_propagate(grid)
                step2 = op_D_fill(step1, b)
                return step2
            return fn
        result = verify_and_predict(make_propagate_fill(bg), task)
        if result:
            return result, f"propagate + fill({bg})"

    # Pattern 8: Interior fill + Recolour
    if bg is not None and cmap:
        for from_col, to_col in cmap.items():
            def make_int_fill_rc(b, fc, tc):
                def fn(grid):
                    step1 = op_N_interior_fill(grid, b)
                    step2 = op_N_recolour(step1, fc, tc)
                    return step2
                return fn
            result = verify_and_predict(make_int_fill_rc(bg, from_col, to_col), task)
            if result:
                return result, f"interior_fill({bg}) + recolour({from_col}→{to_col})"

    # Pattern 9: Local colour swap (single step, but compositional internally)
    def make_local_swap():
        def fn(grid):
            return op_N_local_colour_swap(grid)
        return fn
    result = verify_and_predict(make_local_swap(), task)
    if result:
        return result, "local_colour_swap"

    # Pattern 10: Recolour + local colour swap
    if cmap:
        for from_col, to_col in cmap.items():
            def make_rc_local_swap(fc, tc):
                def fn(grid):
                    step1 = op_N_recolour(grid, fc, tc)
                    step2 = op_N_local_colour_swap(step1)
                    return step2
                return fn
            result = verify_and_predict(make_rc_local_swap(from_col, to_col), task)
            if result:
                return result, f"recolour({from_col}→{to_col}) + local_swap"

    # ═══ 3-step compositions ═══

    # Pattern 11: Erase + Fill + Recolour
    if erase_cols and bg is not None and cmap:
        for ecol in erase_cols:
            for from_col, to_col in cmap.items():
                def make_erase_fill_rc(ec, b, fc, tc):
                    def fn(grid):
                        step1 = op_X_erase(grid, ec)
                        step2 = op_D_fill(step1, b)
                        step3 = op_N_recolour(step2, fc, tc)
                        return step3
                    return fn
                result = verify_and_predict(make_erase_fill_rc(ecol, bg, from_col, to_col), task)
                if result:
                    return result, f"erase({ecol}) + fill({bg}) + recolour({from_col}→{to_col})"

    # Pattern 12: Recolour + Erase + Fill
    if cmap and erase_cols and bg is not None:
        for from_col, to_col in cmap.items():
            for ecol in erase_cols:
                def make_rc_erase_fill(fc, tc, ec, b):
                    def fn(grid):
                        step1 = op_N_recolour(grid, fc, tc)
                        step2 = op_X_erase(step1, ec)
                        step3 = op_D_fill(step2, b)
                        return step3
                    return fn
                result = verify_and_predict(make_rc_erase_fill(from_col, to_col, ecol, bg), task)
                if result:
                    return result, f"recolour({from_col}→{to_col}) + erase({ecol}) + fill({bg})"

    # Pattern 13: Fill + Recolour + Propagate
    if bg is not None and cmap:
        for from_col, to_col in cmap.items():
            def make_fill_rc_prop(b, fc, tc):
                def fn(grid):
                    step1 = op_D_fill(grid, b)
                    step2 = op_N_recolour(step1, fc, tc)
                    step3 = op_D_propagate(step2)
                    return step3
                return fn
            result = verify_and_predict(make_fill_rc_prop(bg, from_col, to_col), task)
            if result:
                return result, f"fill({bg}) + recolour({from_col}→{to_col}) + propagate"

    # Pattern 14: Extend right + Fill
    if bg is not None:
        def make_extend_fill(b):
            def fn(grid):
                step1 = op_N_extend_object_right(grid, b)
                step2 = op_D_fill(step1, b)
                return step2
            return fn
        result = verify_and_predict(make_extend_fill(bg), task)
        if result:
            return result, f"extend_right + fill({bg})"

    # Pattern 15: Fill + Extend right
    if bg is not None:
        def make_fill_extend(b):
            def fn(grid):
                step1 = op_D_fill(grid, b)
                step2 = op_N_extend_object_right(step1, 0)
                return step2
            return fn
        result = verify_and_predict(make_fill_extend(bg), task)
        if result:
            return result, f"fill({bg}) + extend_right"

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

    files = sorted(f for f in os.listdir(args.batch) if f.endswith(".json"))

    solved = total = 0
    sources = {}
    all_results = []

    print("═" * 60)
    print(" COMPOSITIONAL SOLVER v053 — D/X/N/J Primitives")
    print("═" * 60)
    print()

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
        else:
            sources["none"] = sources.get("none", 0) + 1
            all_results.append((tid, False, "none"))
            if args.verbose:
                print(f"  {tid}: ✗")

    print(f"\n{'═' * 60}")
    print(f" RESULTS ({total} tasks)")
    print(f"{'═' * 60}")
    print(f"  SOLVED: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"\n  Solvers:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        if src != "none":
            print(f"    {src}: {count}")

    print(f"\n  Solved tasks:")
    for tid, ok, src in all_results:
        if ok:
            print(f"    {tid} ← {src}")

    print(f"\n  Unsolved tasks:")
    for tid, ok, src in all_results:
        if not ok:
            print(f"    {tid}")
