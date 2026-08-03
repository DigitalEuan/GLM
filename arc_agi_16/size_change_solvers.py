"""
arc_agi_16/size_change_solvers.py
==================================

Solvers for ARC-AGI size-change tasks.

Target tasks:
- 3979b1a8: 5x5 -> 10x10 (2x upscale, column/row distinct-value cycling)
- 7953d61e: 4x4 -> 8x8 (2x upscale, same pattern)
- 6f473927: HxW -> Hx2W (horizontal double, colour mapping)
- 662c240a: 9x3 -> 3x3 (block selection)
- 5587a8d0: NxN -> MxM (concentric nesting)
- 5289ad53: HxW -> 2x3 (object extraction)
- 2697da3f: HxW -> SxS (square output, binary)
- 2753e76c: 16x16 -> variable (crop/extraction)
- 6ecd11f4: large -> 3x3/4x4 (extraction)
- 846bdb03: 13x13 -> variable (extraction)
- 8abad3cf: 7x7 -> variable (extraction)
"""

from __future__ import annotations
import os, sys, json
from collections import Counter
from typing import List, Tuple, Optional, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arc_agi_15'))

from arc_loader import Grid


# ═══════════════════════════════════════════════════════════════════════════════
# Grid utilities
# ═══════════════════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    return g1.height == g2.height and g1.width == g2.width and g1.cells == g2.cells

def make_grid(cells: List[List[int]]) -> Grid:
    return Grid(cells)

def grid_from_lists(cells: List[List[int]]) -> Grid:
    return Grid(cells)

def extract_objects(grid: Grid, bg: int = 0):
    """Find connected components of non-bg values."""
    h, w = grid.height, grid.width
    visited = set()
    objects = []
    for r in range(h):
        for c in range(w):
            if (r, c) in visited or grid.cells[r][c] == bg:
                continue
            colour = grid.cells[r][c]
            queue = [(r, c)]
            cells = set()
            while queue:
                cr, cc = queue.pop()
                if (cr, cc) in visited:
                    continue
                if cr < 0 or cr >= h or cc < 0 or cc >= w:
                    continue
                if grid.cells[cr][cc] != colour:
                    continue
                visited.add((cr, cc))
                cells.add((cr, cc))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    queue.append((cr + dr, cc + dc))
            min_r = min(r for r, c in cells)
            max_r = max(r for r, c in cells)
            min_c = min(c for r, c in cells)
            max_c = max(c for r, c in cells)
            objects.append({
                'colour': colour,
                'cells': cells,
                'area': len(cells),
                'bbox': (min_r, min_c, max_r, max_c),
                'bh': max_r - min_r + 1,
                'bw': max_c - min_c + 1,
                'center': ((min_r + max_r) / 2, (min_c + max_c) / 2),
            })
    objects.sort(key=lambda o: -o['area'])
    return objects


# ═══════════════════════════════════════════════════════════════════════════════
# Solver 1: 2x upscale with column/row distinct-value cycling
# Pattern: TL=input, TR=column distinct values cycled, BL=row distinct values cycled
# ═══════════════════════════════════════════════════════════════════════════════

def get_column_distinct_values(cells: List[List[int]], col: int) -> List[int]:
    """Get distinct values in a column, ordered by first appearance."""
    seen = []
    seen_set = set()
    for row in cells:
        v = row[col]
        if v not in seen_set:
            seen.append(v)
            seen_set.add(v)
    return seen

def get_row_distinct_values(cells: List[List[int]], row: int) -> List[int]:
    """Get distinct values in a row, ordered by first appearance."""
    seen = []
    seen_set = set()
    for v in cells[row]:
        if v not in seen_set:
            seen.append(v)
            seen_set.add(v)
    return seen

def solve_2x_upscale_col_row_cycle(inp: Grid) -> Optional[Grid]:
    """
    2x upscale: TL=input, TR=column distinct values cycled vertically,
    BL=row distinct values cycled horizontally, BR=composite.
    """
    h, w = inp.height, inp.width
    cells = inp.cells
    oh, ow = h * 2, w * 2

    out = [[0] * ow for _ in range(oh)]

    # TL: copy input
    for r in range(h):
        for c in range(w):
            out[r][c] = cells[r][c]

    # TR: each column c gets distinct values of input column c, cycled
    for c in range(w):
        dist_vals = get_column_distinct_values(cells, c)
        n = len(dist_vals)
        for r in range(h):
            out[r][w + c] = dist_vals[r % n]

    # BL: each row r gets distinct values of input row r, cycled
    for r in range(h):
        dist_vals = get_row_distinct_values(cells, r)
        n = len(dist_vals)
        for c in range(w):
            out[h + r][c] = dist_vals[c % n]

    # BR: composite - try column cycling of TR, or row cycling of BL
    # Strategy 1: BR[r][c] = TR column c values cycled at row r
    for c in range(w):
        tr_col_vals = [out[r][w + c] for r in range(h)]
        dist_tr = []
        seen = set()
        for v in tr_col_vals:
            if v not in seen:
                dist_tr.append(v)
                seen.add(v)
        n = len(dist_tr)
        if n == 0:
            n = 1
            dist_tr = [0]
        for r in range(h):
            out[h + r][w + c] = dist_tr[r % n]

    return Grid(out)


def verify_2x_upscale(task_data: dict) -> Tuple[bool, Optional[Grid]]:
    """Check if task follows the 2x upscale pattern and solve."""
    pairs = task_data['train']

    # Check all pairs have 2x size ratio
    for p in pairs:
        ih, iw = len(p['input']), len(p['input'][0])
        oh, ow = len(p['output']), len(p['output'][0])
        if oh != 2 * ih or ow != 2 * iw:
            return False, None

    # Try solving first pair
    inp = Grid(pairs[0]['input'])
    result = solve_2x_upscale_col_row_cycle(inp)
    if result is None:
        return False, None

    # Verify on all train pairs
    for p in pairs:
        inp = Grid(p['input'])
        expected = Grid(p['output'])
        candidate = solve_2x_upscale_col_row_cycle(inp)
        if candidate is None or not grids_equal(candidate, expected):
            return False, None

    return True, result


# ═══════════════════════════════════════════════════════════════════════════════
# Solver 2: Block selection (partition input into blocks, select one)
# ═══════════════════════════════════════════════════════════════════════════════

def solve_block_selection(inp: Grid, oh: int, ow: int) -> List[Tuple[str, Grid]]:
    """Try selecting a block from the input grid."""
    h, w = inp.height, inp.width
    candidates = []

    # Strategy: partition into vertical blocks of height oh
    if h % oh == 0 and ow == w:
        n_blocks = h // oh
        for i in range(n_blocks):
            block = [inp.cells[r][:] for r in range(i * oh, (i + 1) * oh)]
            candidates.append((f"vblock_{i}", Grid(block)))

    # Strategy: partition into horizontal blocks of width ow
    if w % ow == 0 and oh == h:
        n_blocks = w // ow
        for i in range(n_blocks):
            block = [inp.cells[r][i * ow:(i + 1) * ow] for r in range(h)]
            candidates.append((f"hblock_{i}", Grid(block)))

    # Strategy: center crop
    if oh <= h and ow <= w:
        dr = (h - oh) // 2
        dc = (w - ow) // 2
        block = [inp.cells[r + dr][dc:dc + ow] for r in range(oh)]
        candidates.append(("center_crop", Grid(block)))

    # Strategy: top-left crop
    if oh <= h and ow <= w:
        block = [inp.cells[r][:ow] for r in range(oh)]
        candidates.append(("tl_crop", Grid(block)))

    # Strategy: bottom-right crop
    if oh <= h and ow <= w:
        block = [inp.cells[h - oh + r][w - ow:] for r in range(oh)]
        candidates.append(("br_crop", Grid(block)))

    return candidates


def verify_block_selection(task_data: dict) -> Tuple[bool, Optional[Grid]]:
    """Check if task is a block selection and solve."""
    pairs = task_data['train']

    # Get output size from first pair
    oh, ow = len(pairs[0]['output']), len(pairs[0]['output'][0])

    # Try each strategy on all train pairs
    for name, _ in solve_block_selection(Grid(pairs[0]['input']), oh, ow):
        all_match = True
        for p in pairs:
            inp = Grid(p['input'])
            expected = Grid(p['output'])
            candidates = solve_block_selection(inp, oh, ow)
            match_found = False
            for cname, cand in candidates:
                if cname == name and grids_equal(cand, expected):
                    match_found = True
                    break
            if not match_found:
                all_match = False
                break
        if all_match:
            # Apply to test
            test_inp = Grid(pairs[0]['input'])  # placeholder
            return True, solve_block_selection(test_inp, oh, ow)[0][1] if solve_block_selection(test_inp, oh, ow) else None

    return False, None


# ═══════════════════════════════════════════════════════════════════════════════
# Solver 3: Concentric nesting (objects → nested rings)
# ═══════════════════════════════════════════════════════════════════════════════

def solve_concentric_nesting(inp: Grid) -> Optional[Grid]:
    """
    Nest objects as concentric rings, largest outside, smallest at center.
    Output size = 2k-1 where k = number of objects.
    Each object expands to fill its entire ring.
    """
    h, w = inp.height, inp.width
    bg = Counter(v for row in inp.cells for v in row).most_common(1)[0][0]
    objects = extract_objects(inp, bg=bg)

    if len(objects) < 2:
        return None

    k = len(objects)
    size = 2 * k - 1
    out = [[bg] * size for _ in range(size)]

    # Place rings from outside in (largest first)
    for i, obj in enumerate(objects):
        ring_level = i  # 0 = outermost
        r_min = ring_level
        r_max = size - 1 - ring_level
        c_min = ring_level
        c_max = size - 1 - ring_level

        # Fill the ring with this object's colour
        # Top and bottom rows
        for c in range(c_min, c_max + 1):
            out[r_min][c] = obj['colour']
            out[r_max][c] = obj['colour']
        # Left and right columns (excluding corners)
        for r in range(r_min + 1, r_max):
            out[r][c_min] = obj['colour']
            out[r][c_max] = obj['colour']

    return Grid(out)


def solve_concentric_nesting_v2(inp: Grid) -> Optional[Grid]:
    """
    Alternative: objects placed as filled rectangles, centered, largest first.
    Each object's bounding box is centered in the output grid.
    Larger objects overwrite smaller ones.
    """
    h, w = inp.height, inp.width
    bg = Counter(v for row in inp.cells for v in row).most_common(1)[0][0]
    objects = extract_objects(inp, bg=bg)

    if len(objects) < 2:
        return None

    # Output size: max of all bounding box dimensions, made odd
    max_dim = max(max(o['bh'], o['bw']) for o in objects)
    if max_dim % 2 == 0:
        max_dim += 1

    # But also check: for 2 objects, output should be 3x3
    # For 3 objects, output should be 5x5
    # For 4 objects, output should be 7x7
    expected_size = 2 * len(objects) - 1
    size = expected_size

    out = [[bg] * size for _ in range(size)]
    center = size // 2

    # Place objects from largest to smallest (largest overwrites)
    for obj in objects:
        bh, bw = obj['bh'], obj['bw']
        # Center the bounding box
        r_start = center - bh // 2
        c_start = center - bw // 2

        # Place the object's cells
        for (r, c) in obj['cells']:
            # Relative position within bounding box
            rel_r = r - obj['bbox'][0]
            rel_c = c - obj['bbox'][1]
            out_r = r_start + rel_r
            out_c = c_start + rel_c
            if 0 <= out_r < size and 0 <= out_c < size:
                out[out_r][out_c] = obj['colour']

    return Grid(out)


def solve_concentric_nesting_v3(inp: Grid) -> Optional[Grid]:
    """
    v3: Ring expansion - each object expands to fill its entire ring.
    This matches the 7x7 case where objects fill complete rings.
    """
    h, w = inp.height, inp.width
    bg = Counter(v for row in inp.cells for v in row).most_common(1)[0][0]
    objects = extract_objects(inp, bg=bg)

    if len(objects) < 2:
        return None

    k = len(objects)
    size = 2 * k - 1
    out = [[bg] * size for _ in range(size)]

    center = size // 2

    # Fill rings from outside in (largest object = outermost, fills entire area)
    for i, obj in enumerate(objects):
        ring_level = i  # 0 = outermost (largest object)
        r_min = ring_level
        r_max = size - 1 - ring_level

        # Fill ALL cells in this ring area (not just the boundary)
        for r in range(r_min, r_max + 1):
            for c in range(r_min, r_max + 1):
                out[r][c] = obj['colour']

    return Grid(out)


# ═══════════════════════════════════════════════════════════════════════════════
# Solver 4: Horizontal doubling with colour mapping
# ═══════════════════════════════════════════════════════════════════════════════

def solve_horizontal_double(inp: Grid, pairs: List[dict]) -> Optional[Grid]:
    """
    HxW -> Hx2W. Left half = original, right half = transformed.
    Learn the colour mapping from train pairs.
    """
    h, w = inp.height, inp.width
    ow = w * 2

    # Learn colour mapping from train pairs
    colour_map = {}
    for p in pairs:
        pi, po = p['input'], p['output']
        ph = len(pi)
        pw = len(pi[0])
        for r in range(ph):
            for c in range(pw):
                in_val = pi[r][c]
                out_val = po[r][pw + c]  # right half
                if in_val in colour_map and colour_map[in_val] != out_val:
                    return None  # inconsistent mapping
                colour_map[in_val] = out_val

    # Apply: left = input, right = mapped input
    out = [[0] * ow for _ in range(h)]
    for r in range(h):
        for c in range(w):
            out[r][c] = inp.cells[r][c]
            out[r][w + c] = colour_map.get(inp.cells[r][c], inp.cells[r][c])

    return Grid(out)


# ═══════════════════════════════════════════════════════════════════════════════
# Solver 5: Non-square resizing (crop + reshape)
# ═══════════════════════════════════════════════════════════════════════════════

def solve_extraction_to_fixed_size(inp: Grid, oh: int, ow: int) -> List[Tuple[str, Grid]]:
    """Try various extraction strategies to get a fixed-size output."""
    h, w = inp.height, inp.width
    candidates = []

    # Find bounding box of non-bg content
    bg = Counter(v for row in inp.cells for v in row).most_common(1)[0][0]
    min_r, max_r = h, -1
    min_c, max_c = w, -1
    for r in range(h):
        for c in range(w):
            if inp.cells[r][c] != bg:
                min_r = min(min_r, r)
                max_r = max(max_r, r)
                min_c = min(min_c, c)
                max_c = max(max_c, c)

    if max_r < 0:
        return candidates

    content_h = max_r - min_r + 1
    content_w = max_c - min_c + 1

    # Strategy: extract content bounding box, resize to oh x ow
    if content_h == oh and content_w == ow:
        block = [inp.cells[r][min_c:min_c + ow] for r in range(min_r, min_r + oh)]
        candidates.append(("content_bbox", Grid(block)))

    # Strategy: center crop to oh x ow
    if oh <= h and ow <= w:
        dr = (h - oh) // 2
        dc = (w - ow) // 2
        block = [inp.cells[r + dr][dc:dc + ow] for r in range(oh)]
        candidates.append(("center_crop", Grid(block)))

    # Strategy: subsample (take every nth row/col)
    if h >= oh and w >= ow:
        row_step = h / oh
        col_step = w / ow
        block = []
        for r in range(oh):
            row = []
            for c in range(ow):
                sr = int(r * row_step)
                sc = int(c * col_step)
                row.append(inp.cells[sr][sc])
            block.append(row)
        candidates.append(("subsample", Grid(block)))

    # Strategy: top-left crop
    if oh <= h and ow <= w:
        block = [inp.cells[r][:ow] for r in range(oh)]
        candidates.append(("tl_crop", Grid(block)))

    return candidates


# ═══════════════════════════════════════════════════════════════════════════════
# Solver 6: Column cycling for non-square output
# ═══════════════════════════════════════════════════════════════════════════════

def solve_column_cycling(inp: Grid) -> Optional[Grid]:
    """
    For 6f473927 pattern: left half = input, right half = column cycling.
    Each column in the right half cycles through its input column's distinct values.
    """
    h, w = inp.height, inp.width
    ow = w * 2
    cells = inp.cells

    out = [[0] * ow for _ in range(h)]

    # Left half = input
    for r in range(h):
        for c in range(w):
            out[r][c] = cells[r][c]

    # Right half: each column cycles through distinct values
    for c in range(w):
        dist = get_column_distinct_values(cells, c)
        n = len(dist)
        if n == 0:
            n = 1
            dist = [0]
        for r in range(h):
            out[r][w + c] = dist[r % n]

    return Grid(out)


# ═══════════════════════════════════════════════════════════════════════════════
# Solver 7: Colour-replacing resize (for 662c240a pattern)
# ═══════════════════════════════════════════════════════════════════════════════

def solve_diagonal_block_select(inp: Grid, oh: int, ow: int) -> List[Tuple[str, Grid]]:
    """
    For tasks like 662c240a where input is partitioned into blocks
    and one block is selected based on its diagonal pattern.
    """
    h, w = inp.height, inp.width
    candidates = []

    # Partition into vertical blocks
    if h % oh == 0 and ow == w:
        n_blocks = h // oh
        for i in range(n_blocks):
            block = [inp.cells[i * oh + r][:] for r in range(oh)]
            candidates.append((f"vblock_{i}", Grid(block)))

            # Also try: block with diagonal values from other blocks
            # (for the "diagonal pattern" selection)

    return candidates


# ═══════════════════════════════════════════════════════════════════════════════
# Main experiment runner
# ═══════════════════════════════════════════════════════════════════════════════

def load_task(task_id: str, data_dir: str = None) -> dict:
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'arc_agi_15', 'data', 'training')
    path = os.path.join(data_dir, f'{task_id}.json')
    with open(path) as f:
        return json.load(f)


def run_all_experiments():
    """Run all solvers on target tasks."""
    tasks = {
        '3979b1a8': '2x upscale',
        '7953d61e': '2x upscale',
        '6f473927': 'horizontal double',
        '662c240a': 'block selection',
        '5587a8d0': 'concentric nesting',
        '5289ad53': 'extraction',
        '2697da3f': 'square output',
        '2753e76c': 'extraction',
        '6ecd11f4': 'extraction',
        '846bdb03': 'extraction',
        '8abad3cf': 'extraction',
    }

    results = {}

    for task_id, desc in tasks.items():
        task_data = load_task(task_id)
        pairs = task_data['train']
        print(f"\n{'='*60}")
        print(f"Task {task_id} ({desc})")
        print(f"{'='*60}")

        # Show train pairs
        for i, p in enumerate(pairs):
            ih, iw = len(p['input']), len(p['input'][0])
            oh, ow = len(p['output']), len(p['output'][0])
            print(f"  train[{i}]: {ih}x{iw} -> {oh}x{ow}")

        solved = False

        # Try 2x upscale
        is_2x, result = verify_2x_upscale(task_data)
        if is_2x:
            print(f"  ✓ SOLVED by 2x upscale col/row cycling")
            solved = True
            results[task_id] = ('2x_upscale', result)

        # Try block selection
        if not solved:
            is_block, result = verify_block_selection(task_data)
            if is_block:
                print(f"  ✓ SOLVED by block selection")
                solved = True
                results[task_id] = ('block_selection', result)

        # Try horizontal double
        if not solved:
            oh, ow = len(pairs[0]['output']), len(pairs[0]['output'][0])
            ih, iw = len(pairs[0]['input']), len(pairs[0]['input'][0])
            if ow == 2 * iw and oh == ih:
                result = solve_horizontal_double(Grid(pairs[0]['input']), pairs)
                if result:
                    # Verify
                    all_match = True
                    for p in pairs:
                        cand = solve_horizontal_double(Grid(p['input']), pairs)
                        if cand is None or not grids_equal(cand, Grid(p['output'])):
                            all_match = False
                            break
                    if all_match:
                        print(f"  ✓ SOLVED by horizontal double")
                        solved = True
                        results[task_id] = ('horizontal_double', result)

        # Try concentric nesting
        if not solved:
            for solver_name, solver in [('v1', solve_concentric_nesting),
                                         ('v2', solve_concentric_nesting_v2),
                                         ('v3', solve_concentric_nesting_v3)]:
                all_match = True
                for p in pairs:
                    inp = Grid(p['input'])
                    expected = Grid(p['output'])
                    cand = solver(inp)
                    if cand is None or not grids_equal(cand, expected):
                        all_match = False
                        break
                if all_match:
                    print(f"  ✓ SOLVED by concentric nesting {solver_name}")
                    solved = True
                    result = solver(Grid(pairs[0]['input']))
                    results[task_id] = (f'concentric_{solver_name}', result)
                    break

        if not solved:
            print(f"  ✗ NOT SOLVED")
            results[task_id] = (None, None)

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    solved_count = sum(1 for v in results.values() if v[0] is not None)
    print(f"Solved: {solved_count}/{len(tasks)}")
    for tid, (method, _) in results.items():
        status = f"✓ {method}" if method else "✗"
        print(f"  {tid}: {status}")

    return results


if __name__ == '__main__':
    run_all_experiments()
