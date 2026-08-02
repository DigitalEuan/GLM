"""
v030_pattern_learner.py — Advanced pattern detection for ARC tasks
==================================================================

Detects transformation patterns that the current DSL + senses miss:
1. FLOOD_FILL: fill enclosed regions (zeros bounded by non-zeros)
2. SPREAD: non-zero cells spread to adjacent zeros
3. OUTLINE: non-zero cells become their boundary colour
4. OBJECT_GROW: objects expand by 1 cell in all directions
5. COPY_REGION: copy one region to another location
6. MIRROR_FILL: fill one half based on the other
7. PATTERN_REPEAT: detect repeating tile patterns
8. CONNECT: connect two objects with a line
9. EXTRACT_OBJECT: extract the largest/smallest/different object
10. COUNT_FILL: fill based on count of neighbours
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import Counter, defaultdict, deque
import sys, os, time, signal, copy

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task


class _OpTimeout(Exception):
    pass

def _alarm_handler(s, f):
    raise _OpTimeout()

signal.signal(signal.SIGALRM, _alarm_handler)


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def grid_copy(grid: Grid) -> Grid:
    return Grid(grid.height, grid.width, [row[:] for row in grid.cells])


def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c]
               for r in range(g1.height) for c in range(g1.width))


def find_objects(grid: Grid) -> List[List[Tuple[int, int]]]:
    """Find connected components of non-zero cells (4-connected)."""
    visited = set()
    objects = []
    for r in range(grid.height):
        for c in range(grid.width):
            if (r, c) in visited or grid.cells[r][c] == 0:
                continue
            obj = []
            queue = deque([(r, c)])
            visited.add((r, c))
            while queue:
                cr, cc = queue.popleft()
                obj.append((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if (0 <= nr < grid.height and 0 <= nc < grid.width
                        and (nr, nc) not in visited
                        and grid.cells[nr][nc] != 0):
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            objects.append(obj)
    return objects


def object_colour(grid: Grid, obj: List[Tuple[int, int]]) -> int:
    """Get the dominant colour of an object."""
    cols = Counter(grid.cells[r][c] for r, c in obj)
    return cols.most_common(1)[0][0]


def object_bbox(obj: List[Tuple[int, int]]) -> Tuple[int, int, int, int]:
    """Get bounding box (min_r, min_c, max_r, max_c)."""
    min_r = min(r for r, c in obj)
    min_c = min(c for r, c in obj)
    max_r = max(r for r, c in obj)
    max_c = max(c for r, c in obj)
    return min_r, min_c, max_r, max_c


# ═══════════════════════════════════════════════════════════════════
# PATTERN 1: FLOOD FILL ENCLOSED REGIONS
# ═══════════════════════════════════════════════════════════════════

def try_flood_fill(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Fill enclosed zero-regions with a colour derived from the boundary."""
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Learn fill colour from train pairs
    fill_colours = []
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        # Find zero cells that became non-zero
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    fill_colours.append(pair.output.cells[r][c])
                    break
            else:
                continue
            break
    
    if not fill_colours:
        return None
    
    # Try each fill colour
    for fill_col in set(fill_colours):
        test_input = task.test[0].input
        h, w = test_input.height, test_input.width
        
        # Find enclosed regions: BFS from border zeros
        reachable = set()
        queue = deque()
        
        # Start from all border zeros
        for r in range(h):
            for c in range(w):
                if (r == 0 or r == h-1 or c == 0 or c == w-1) and test_input.cells[r][c] == 0:
                    queue.append((r, c))
                    reachable.add((r, c))
        
        while queue:
            cr, cc = queue.popleft()
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = cr+dr, cc+dc
                if (0 <= nr < h and 0 <= nc < w
                    and (nr, nc) not in reachable
                    and test_input.cells[nr][nc] == 0):
                    reachable.add((nr, nc))
                    queue.append((nr, nc))
        
        # Fill enclosed zeros (zeros NOT reachable from border)
        new_cells = [row[:] for row in test_input.cells]
        filled = False
        for r in range(h):
            for c in range(w):
                if test_input.cells[r][c] == 0 and (r, c) not in reachable:
                    new_cells[r][c] = fill_col
                    filled = True
        
        if not filled:
            continue
        
        pred = Grid(h, w, new_cells)
        
        # Verify on train
        all_pass = True
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            reachable = set()
            queue = deque()
            for r in range(h):
                for c in range(w):
                    if (r == 0 or r == h-1 or c == 0 or c == w-1) and pair.input.cells[r][c] == 0:
                        queue.append((r, c))
                        reachable.add((r, c))
            while queue:
                cr, cc = queue.popleft()
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if (0 <= nr < h and 0 <= nc < w
                        and (nr, nc) not in reachable
                        and pair.input.cells[nr][nc] == 0):
                        reachable.add((nr, nc))
                        queue.append((nr, nc))
            
            cells = [row[:] for row in pair.input.cells]
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] == 0 and (r, c) not in reachable:
                        cells[r][c] = fill_col
            if Grid(h, w, cells) != pair.output:
                all_pass = False
                break
        
        if all_pass:
            return pred, "flood_fill"
    
    return None


# ═══════════════════════════════════════════════════════════════════
# PATTERN 2: SPREAD (non-zero cells grow into adjacent zeros)
# ═══════════════════════════════════════════════════════════════════

def try_spread(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Non-zero cells spread to adjacent zeros. Try 1-step and 2-step spread."""
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Try 1-step spread: each zero becomes the colour of its nearest non-zero neighbour
    for steps in [1, 2, 3]:
        all_pass = True
        last_pred = None
        
        for pair_idx, pair in enumerate(task.train):
            h, w = pair.input.height, pair.input.width
            cells = [row[:] for row in pair.input.cells]
            
            for step in range(steps):
                new_cells = [row[:] for row in cells]
                for r in range(h):
                    for c in range(w):
                        if cells[r][c] == 0:
                            # Check neighbours
                            neighbour_cols = []
                            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                                nr, nc = r+dr, c+dc
                                if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] != 0:
                                    neighbour_cols.append(cells[nr][nc])
                            if len(neighbour_cols) == 1:
                                new_cells[r][c] = neighbour_cols[0]
                            elif len(neighbour_cols) > 1:
                                # Majority vote
                                col_counts = Counter(neighbour_cols)
                                new_cells[r][c] = col_counts.most_common(1)[0][0]
                cells = new_cells
            
            if not grids_equal(Grid(h, w, cells), pair.output):
                all_pass = False
                break
            
            if pair_idx == len(task.train) - 1:
                last_pred_cells = cells
        
        if all_pass:
            # Apply to test
            test_input = task.test[0].input
            h, w = test_input.height, test_input.width
            cells = [row[:] for row in test_input.cells]
            for step in range(steps):
                new_cells = [row[:] for row in cells]
                for r in range(h):
                    for c in range(w):
                        if cells[r][c] == 0:
                            neighbour_cols = []
                            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                                nr, nc = r+dr, c+dc
                                if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] != 0:
                                    neighbour_cols.append(cells[nr][nc])
                            if len(neighbour_cols) == 1:
                                new_cells[r][c] = neighbour_cols[0]
                            elif len(neighbour_cols) > 1:
                                col_counts = Counter(neighbour_cols)
                                new_cells[r][c] = col_counts.most_common(1)[0][0]
                cells = new_cells
            return Grid(h, w, cells), f"spread_{steps}"
    
    return None


# ═══════════════════════════════════════════════════════════════════
# PATTERN 3: OBJECT GROW (expand objects by 1 cell)
# ═══════════════════════════════════════════════════════════════════

def try_object_grow(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Objects expand by 1 cell in all directions with their colour."""
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    for steps in [1, 2]:
        all_pass = True
        
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            cells = [row[:] for row in pair.input.cells]
            
            for step in range(steps):
                new_cells = [row[:] for row in cells]
                for r in range(h):
                    for c in range(w):
                        if cells[r][c] == 0:
                            # Check all 8 neighbours
                            for dr in [-1, 0, 1]:
                                for dc in [-1, 0, 1]:
                                    if dr == 0 and dc == 0:
                                        continue
                                    nr, nc = r+dr, c+dc
                                    if (0 <= nr < h and 0 <= nc < w
                                        and cells[nr][nc] != 0):
                                        new_cells[r][c] = cells[nr][nc]
                                        break
                                else:
                                    continue
                                break
                cells = new_cells
            
            if not grids_equal(Grid(h, w, cells), pair.output):
                all_pass = False
                break
        
        if all_pass:
            test_input = task.test[0].input
            h, w = test_input.height, test_input.width
            cells = [row[:] for row in test_input.cells]
            for step in range(steps):
                new_cells = [row[:] for row in cells]
                for r in range(h):
                    for c in range(w):
                        if cells[r][c] == 0:
                            for dr in [-1, 0, 1]:
                                for dc in [-1, 0, 1]:
                                    if dr == 0 and dc == 0:
                                        continue
                                    nr, nc = r+dr, c+dc
                                    if (0 <= nr < h and 0 <= nc < w
                                        and cells[nr][nc] != 0):
                                        new_cells[r][c] = cells[nr][nc]
                                        break
                                else:
                                    continue
                                break
                cells = new_cells
            return Grid(h, w, cells), f"object_grow_{steps}"
    
    return None


# ═══════════════════════════════════════════════════════════════════
# PATTERN 4: HORIZONTAL/VERTICAL SPREAD
# ═══════════════════════════════════════════════════════════════════

def try_hv_spread(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Non-zero cells spread horizontally or vertically to fill zeros in the same row/col."""
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    for direction in ['h', 'v']:
        all_pass = True
        
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            cells = [row[:] for row in pair.input.cells]
            
            if direction == 'h':
                # Horizontal spread: fill zeros between non-zero cells in each row
                for r in range(h):
                    # Find leftmost and rightmost non-zero
                    left_col = None
                    right_col = None
                    left_val = None
                    right_val = None
                    for c in range(w):
                        if cells[r][c] != 0:
                            if left_col is None:
                                left_col = c
                                left_val = cells[r][c]
                            right_col = c
                            right_val = cells[r][c]
                    if left_col is not None and right_col is not None and left_col != right_col:
                        # Fill between
                        for c in range(left_col, right_col + 1):
                            if cells[r][c] == 0:
                                # Use nearest non-zero
                                cells[r][c] = left_val  # Simple: fill with left value
            else:
                # Vertical spread
                for c in range(w):
                    top_row = None
                    bottom_row = None
                    top_val = None
                    bottom_val = None
                    for r in range(h):
                        if cells[r][c] != 0:
                            if top_row is None:
                                top_row = r
                                top_val = cells[r][c]
                            bottom_row = r
                            bottom_val = cells[r][c]
                    if top_row is not None and bottom_row is not None and top_row != bottom_row:
                        for r in range(top_row, bottom_row + 1):
                            if cells[r][c] == 0:
                                cells[r][c] = top_val
            
            if not grids_equal(Grid(h, w, cells), pair.output):
                all_pass = False
                break
        
        if all_pass:
            test_input = task.test[0].input
            h, w = test_input.height, test_input.width
            cells = [row[:] for row in test_input.cells]
            
            if direction == 'h':
                for r in range(h):
                    left_col = None
                    right_col = None
                    left_val = None
                    for c in range(w):
                        if cells[r][c] != 0:
                            if left_col is None:
                                left_col = c
                                left_val = cells[r][c]
                            right_col = c
                    if left_col is not None and right_col is not None and left_col != right_col:
                        for c in range(left_col, right_col + 1):
                            if cells[r][c] == 0:
                                cells[r][c] = left_val
            else:
                for c in range(w):
                    top_row = None
                    bottom_row = None
                    top_val = None
                    for r in range(h):
                        if cells[r][c] != 0:
                            if top_row is None:
                                top_row = r
                                top_val = cells[r][c]
                            bottom_row = r
                    if top_row is not None and bottom_row is not None and top_row != bottom_row:
                        for r in range(top_row, bottom_row + 1):
                            if cells[r][c] == 0:
                                cells[r][c] = top_val
            
            return Grid(h, w, cells), f"hv_spread_{direction}"
    
    return None


# ═══════════════════════════════════════════════════════════════════
# PATTERN 5: COUNT-BASED RECOLOUR (neighbour count determines colour)
# ═══════════════════════════════════════════════════════════════════

def try_count_recolour(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Cell colour changes based on count of non-zero neighbours."""
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Build rule: (input_colour, non_zero_neighbour_count) → output_colour
    rule_counts: Dict[Tuple[int, int], Counter] = defaultdict(Counter)
    
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                ic = pair.input.cells[r][c]
                oc = pair.output.cells[r][c]
                # Count non-zero neighbours (4-connected)
                count = 0
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w and pair.input.cells[nr][nc] != 0:
                        count += 1
                key = (ic, count)
                rule_counts[key][oc] += 1
    
    # Build rules
    rules = {}
    for key, counts in rule_counts.items():
        rules[key] = counts.most_common(1)[0][0]
    
    # Apply to test
    test_input = task.test[0].input
    h, w = test_input.height, test_input.width
    new_cells = []
    for r in range(h):
        row = []
        for c in range(w):
            ic = test_input.cells[r][c]
            count = 0
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < h and 0 <= nc < w and test_input.cells[nr][nc] != 0:
                    count += 1
            key = (ic, count)
            row.append(rules.get(key, ic))
        new_cells.append(row)
    pred = Grid(h, w, new_cells)
    
    # Verify on train
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        cells = []
        for r in range(h):
            row = []
            for c in range(w):
                ic = pair.input.cells[r][c]
                count = 0
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w and pair.input.cells[nr][nc] != 0:
                        count += 1
                key = (ic, count)
                row.append(rules.get(key, ic))
            cells.append(row)
        if Grid(h, w, cells) != pair.output:
            return None
    
    return pred, "count_recolour"


# ═══════════════════════════════════════════════════════════════════
# PATTERN 6: IDENTITY (no change)
# ═══════════════════════════════════════════════════════════════════

def try_identity(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Check if output equals input for all train pairs."""
    for pair in task.train:
        if not grids_equal(pair.input, pair.output):
            return None
    return grid_copy(task.test[0].input), "identity"


# ═══════════════════════════════════════════════════════════════════
# MAIN PREDICTOR
# ═══════════════════════════════════════════════════════════════════

def predict_pattern(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Try all pattern strategies."""
    strategies = [
        ("identity", try_identity, 0),
        ("flood_fill", try_flood_fill, 2),
        ("spread", try_spread, 3),
        ("object_grow", try_object_grow, 3),
        ("hv_spread", try_hv_spread, 3),
        ("count_recolour", try_count_recolour, 4),
    ]
    
    for name, fn, priority in strategies:
        try:
            result = fn(task)
            if result is not None:
                pred, src = result
                return pred, src, {"strategy": name, "priority": priority}
        except Exception:
            continue
    
    return None


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
    
    for fname in files:
        task = load_task(os.path.join(args.batch, fname),
                         name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1
        
        result = predict_pattern(task)
        if result is not None:
            pred, src, diag = result
            ok = (pred == task.test[0].expected_output)
            if ok:
                solved += 1
            sources[src] = sources.get(src, 0) + 1
            if args.verbose or ok:
                print(f"  {fname}: {'OK' if ok else 'X'} src={src}")
        else:
            sources["none"] = sources.get("none", 0) + 1
            if args.verbose:
                print(f"  {fname}: X src=none")
    
    print(f"\n═══ Pattern Learner ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources: {sources}")
