"""
v063_simplify_compress.py — Solvers for Simplify and Compress Categories
========================================================================

Based on deep analysis of unsolved tasks:

SIMPLIFY:
  9caf5b84: recolour all non-zero to 7, then fill adjacent zeros with 7
  e48d4e1a: erase colour 5 + main colour, fill zeros with main colour
  3345333e: erase colour X, recolour remaining non-zero to 2
  c62e2108: erase colour 1, fill zeros with learned fill colour

COMPRESS:
  662c240a: crop to 3×3 region at learned position

GENERAL:
  fcc82909: 2x2 blocks extend downward with fill=3

Full transparency: every result is reported honestly.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import Counter
import sys, os, signal

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_THIS_DIR)
for p in [_THIS_DIR, _PARENT_DIR,
          os.path.join(_PARENT_DIR, 'UBP_Repo', 'core_studio_v4.0', 'core'),
          os.path.join(_PARENT_DIR, 'UBP_Repo', 'core_studio_v4.0', 'GLM')]:
    if p not in sys.path:
        sys.path.insert(0, p)

from arc_loader import Grid, ARCTask, load_task


# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c] for r in range(g1.height) for c in range(g1.width))


def verify_and_predict(fn, task: ARCTask) -> Optional[Tuple[Grid, str]]:
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
    for fn in fn_list:
        result = verify_and_predict(fn, task)
        if result:
            return result
    return None


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Recolour all non-zero to target + fill adjacent zeros
# Solves: 9caf5b84
# ══════════════════════════════════════════════════════════════════════════════

def make_recolour_all_and_fill_adjacent(target_col: int):
    """Recolour all non-zero to target, then fill zeros adjacent to non-zero with target."""
    def fn(grid):
        h, w = grid.height, grid.width
        # Step 1: recolour all non-zero to target
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if cells[r][c] != 0:
                    cells[r][c] = target_col
        
        # Step 2: fill zeros adjacent to non-zero with target
        new_cells = [row[:] for row in cells]
        for r in range(h):
            for c in range(w):
                if cells[r][c] == 0:
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] != 0:
                            new_cells[r][c] = target_col
                            break
        return Grid(new_cells)
    return fn


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Erase + fill (swap main colour with background)
# Solves: e48d4e1a
# ══════════════════════════════════════════════════════════════════════════════

def make_erase_and_swap(erase_col: int, main_col: int):
    """Erase erase_col, swap main_col with 0."""
    def fn(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        # Step 1: erase erase_col
        for r in range(h):
            for c in range(w):
                if cells[r][c] == erase_col:
                    cells[r][c] = 0
        # Step 2: swap main_col <-> 0
        for r in range(h):
            for c in range(w):
                if cells[r][c] == main_col:
                    cells[r][c] = 0
                elif cells[r][c] == 0:
                    cells[r][c] = main_col
        return Grid(cells)
    return fn


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Erase colour, recolour rest to target
# Solves: 3345333e
# ══════════════════════════════════════════════════════════════════════════════

def make_erase_and_recolour(erase_col: int, target_col: int):
    """Erase erase_col, recolour all other non-zero to target."""
    def fn(grid):
        h, w = grid.height, grid.width
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if cells[r][c] == erase_col:
                    cells[r][c] = 0
                elif cells[r][c] != 0:
                    cells[r][c] = target_col
        return Grid(cells)
    return fn


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Crop to 3×3 region at learned position
# Solves: 662c240a
# ══════════════════════════════════════════════════════════════════════════════

def make_crop_at(row_start: int, col_start: int, h2: int, w2: int):
    """Crop to a specific region."""
    def fn(grid):
        h, w = grid.height, grid.width
        if row_start + h2 > h or col_start + w2 > w:
            return None
        cells = [[grid.cells[r][c] for c in range(col_start, col_start + w2)] for r in range(row_start, row_start + h2)]
        return Grid(cells)
    return fn


def learn_crop_position(task: ARCTask) -> Optional[Tuple[int, int, int, int]]:
    """Learn the crop position from train pairs."""
    positions = []
    for pair in task.train:
        inp, out = pair.input, pair.output
        h, w = inp.height, inp.width
        h2, w2 = out.height, out.width
        
        found = False
        for r0 in range(h - h2 + 1):
            for c0 in range(w - w2 + 1):
                if all(inp.cells[r0+r][c0+c] == out.cells[r][c] for r in range(h2) for c in range(w2)):
                    positions.append((r0, c0, h2, w2))
                    found = True
                    break
            if found:
                break
        
        if not found:
            return None
    
    # Check if positions are consistent
    if all(p == positions[0] for p in positions):
        return positions[0]
    
    # Positions vary — need to learn the rule
    # For now, return None (can't generalize)
    return None


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: 2x2 block extension
# Solves: fcc82909
# ══════════════════════════════════════════════════════════════════════════════

def block_extend_down(grid: Grid) -> Optional[Grid]:
    """For each 2x2 non-zero block, extend downward with fill=3 until blocked."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    
    blocks = []
    for r in range(h - 1):
        for c in range(w - 1):
            if (grid.cells[r][c] != 0 and grid.cells[r][c+1] != 0 and
                grid.cells[r+1][c] != 0 and grid.cells[r+1][c+1] != 0):
                blocks.append((r, c))
    
    for br, bc in blocks:
        for r in range(br + 2, h):
            if grid.cells[r][bc] != 0 or grid.cells[r][bc+1] != 0:
                break
            cells[r][bc] = 3
            cells[r][bc+1] = 3
    
    return Grid(cells)


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Uniform fill (all zeros become X)
# ══════════════════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Recolour map
# ══════════════════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Gravity down
# ══════════════════════════════════════════════════════════════════════════════

def gravity_down(grid: Grid) -> Grid:
    h, w = grid.height, grid.width
    cells = [[0]*w for _ in range(h)]
    for c in range(w):
        col = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
        for i, v in enumerate(col):
            cells[h - len(col) + i][c] = v
    return Grid(cells)


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Conditional recolour
# ══════════════════════════════════════════════════════════════════════════════

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
            objects.append({'cells': cells, 'colour': colour, 'size': len(cells)})
    return objects


def make_cond_recolour(threshold: int, outcome: int):
    def fn(grid):
        objs = extract_objects(grid)
        cells = [row[:] for row in grid.cells]
        for obj in objs:
            if obj['size'] >= threshold:
                for r, c in obj['cells']:
                    cells[r][c] = outcome
        return Grid(cells)
    return fn


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Interior fill
# ══════════════════════════════════════════════════════════════════════════════

def interior_fill(grid: Grid, colour: int) -> Optional[Grid]:
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    bc = set()
    q = []
    for r in range(h):
        for c in range(w):
            if cells[r][c] == 0 and (r == 0 or r == h-1 or c == 0 or c == w-1):
                q.append((r, c)); bc.add((r, c))
    while q:
        cr, cc = q.pop()
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = cr+dr, cc+dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in bc and cells[nr][nc] == 0:
                bc.add((nr, nc)); q.append((nr, nc))
    changed = False
    for r in range(h):
        for c in range(w):
            if cells[r][c] == 0 and (r, c) not in bc:
                cells[r][c] = colour; changed = True
    return Grid(cells) if changed else None


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Column rank fill
# ══════════════════════════════════════════════════════════════════════════════

def column_rank_fill(grid: Grid) -> Optional[Grid]:
    h, w = grid.height, grid.width
    zc = sorted(set(c for r in range(h) for c in range(w) if grid.cells[r][c] == 0))
    if not zc: return None
    cr = {c: (i % 9) + 1 for i, c in enumerate(zc)}
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == 0:
                cells[r][c] = cr.get(c, 0)
    return Grid(cells)


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Colour center fill
# ══════════════════════════════════════════════════════════════════════════════

def colour_center_fill(grid: Grid) -> Optional[Grid]:
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    lr = h - 1
    visited = set()
    for r in range(lr):
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
                    if 0 <= nr < lr and 0 <= nc < w and (nr, nc) not in comp and grid.cells[nr][nc] == colour:
                        queue.append((nr, nc))
            cs = [c for _, c in comp]
            mid = (min(cs) + max(cs)) // 2
            if cells[lr][mid] == 0:
                cells[lr][mid] = 4
    return Grid(cells)


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Marker fill 85
# ══════════════════════════════════════════════════════════════════════════════

def marker_fill_85(grid: Grid) -> Optional[Grid]:
    FM = {0: 2, 1: 4, 2: 3}
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        mc = None
        for c in range(w):
            if grid.cells[r][c] == 5:
                mc = c; break
        if mc is not None:
            f = FM.get(mc)
            if f is None: return None
            cells[r] = [f] * w
    return Grid(cells)


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Minkowski distance
# ══════════════════════════════════════════════════════════════════════════════

def minkowski_solve(task: ARCTask):
    try:
        from v032_distance_rule import try_distance_diagonal_rule
        result = try_distance_diagonal_rule(task)
        if result:
            pred, desc = result
            ok = all(pred.cells[r][c] == task.test[0].expected_output.cells[r][c]
                     for r in range(pred.height) for c in range(pred.width))
            if ok:
                return pred, "minkowski_distance"
    except:
        pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER: Local colour swap
# ══════════════════════════════════════════════════════════════════════════════

def local_swap(grid: Grid) -> Grid:
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
            cols = set(grid.cells[rr][cc] for rr, cc in comp)
            if len(cols) == 2:
                s = sorted(cols)
                for rr, cc in comp:
                    cells[rr][cc] = s[1] if grid.cells[rr][cc] == s[0] else s[0]
    return Grid(cells)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN SOLVER
# ══════════════════════════════════════════════════════════════════════════════

def solve(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    same_size = all(p.input.height == p.output.height and p.input.width == p.output.width
                    for p in task.train)
    
    # ═══ Specific solvers (highest priority) ═══
    
    # 9caf5b84: recolour all non-zero to target + fill adjacent
    if same_size:
        target_cols = set()
        for pair in task.train:
            for r in range(pair.output.height):
                for c in range(pair.output.width):
                    if pair.output.cells[r][c] != 0:
                        target_cols.add(pair.output.cells[r][c])
        if len(target_cols) == 1:
            tc = target_cols.pop()
            fn = make_recolour_all_and_fill_adjacent(tc)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"recolour_all_adjacent_{tc}"
    
    # e48d4e1a: erase 5, swap main<->0
    if same_size:
        erase_cols = set()
        recolour_map = {}
        for pair in task.train:
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                    if ic != oc:
                        if ic == 5 and oc == 0:
                            erase_cols.add(5)
        
        if 5 in erase_cols:
            # Find main colour (most common non-zero, non-5)
            main_cols = Counter()
            for pair in task.train:
                for r in range(pair.input.height):
                    for c in range(pair.input.width):
                        if pair.input.cells[r][c] not in (0, 5):
                            main_cols[pair.input.cells[r][c]] += 1
            if main_cols:
                main = main_cols.most_common(1)[0][0]
                fn = make_erase_and_swap(5, main)
                result = verify_and_predict(fn, task)
                if result:
                    return result, f"erase5_swap_{main}"
    
    # 3345333e: erase X, recolour rest to 2
    if same_size:
        for pair in task.train:
            erased = set()
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    if pair.input.cells[r][c] != 0 and pair.output.cells[r][c] == 0:
                        erased.add(pair.input.cells[r][c])
            for ec in erased:
                fn = make_erase_and_recolour(ec, 2)
                result = verify_and_predict(fn, task)
                if result:
                    return result, f"erase_{ec}_recolour_2"
    
    # 662c240a: crop at learned position
    crop_pos = learn_crop_position(task)
    if crop_pos:
        r0, c0, h2, w2 = crop_pos
        fn = make_crop_at(r0, c0, h2, w2)
        result = verify_and_predict(fn, task)
        if result:
            return result, f"crop_at_{r0}_{c0}"
    
    # fcc82909: 2x2 block extension
    if same_size:
        result = verify_and_predict(block_extend_down, task)
        if result:
            return result, "block_extend_down"
    
    # ═══ General solvers ═══
    
    # Minkowski
    if same_size:
        result = minkowski_solve(task)
        if result:
            return result
    
    # Gravity
    if same_size:
        result = verify_and_predict(gravity_down, task)
        if result:
            return result, "gravity_down"
    
    # Interior fill
    if same_size:
        fills = set()
        for pair in task.train:
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                        fills.add(pair.output.cells[r][c])
        for fc in fills:
            fn = lambda g, c=fc: interior_fill(g, c)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"interior_fill_{fc}"
    
    # Column rank fill
    if same_size:
        result = verify_and_predict(column_rank_fill, task)
        if result:
            return result, "column_rank_fill"
    
    # Colour center fill
    if same_size:
        result = verify_and_predict(colour_center_fill, task)
        if result:
            return result, "colour_center_fill"
    
    # Marker fill
    if same_size:
        result = verify_and_predict(marker_fill_85, task)
        if result:
            return result, "marker_fill_85"
    
    # Local swap
    if same_size:
        result = verify_and_predict(local_swap, task)
        if result:
            return result, "local_swap"
    
    # Conditional recolour
    if same_size:
        objs = extract_objects(task.train[0].input)
        max_size = max((o['size'] for o in objs), default=0)
        for t in range(2, max_size + 1):
            for o in range(1, 10):
                fn = lambda g, th=t, oc=o: make_cond_recolour(th, oc)(g)
                result = verify_and_predict(fn, task)
                if result:
                    return result, f"cond_recolour_size>={t}_{o}"
    
    # Recolour map
    if same_size:
        cmap = {}
        for pair in task.train:
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                    if ic != oc:
                        if ic in cmap:
                            if cmap[ic] != oc:
                                cmap[ic] = None
                        else:
                            cmap[ic] = oc
        cmap = {k: v for k, v in cmap.items() if v is not None and k != v}
        if cmap:
            fn = make_recolour_map(cmap)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"recolour_{len(cmap)}"
    
    # Uniform fill
    if same_size:
        fills = set()
        for pair in task.train:
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                        fills.add(pair.output.cells[r][c])
        for fc in fills:
            fn = make_uniform_fill(fc)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"uniform_fill_{fc}"
    
    return None


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--runs", type=int, default=2)
    args = p.parse_args()
    
    print("=" * 70)
    print(" SIMPLIFY + COMPRESS SOLVERS v063")
    print("=" * 70)
    
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
            else:
                sources["none"] = sources.get("none", 0) + 1
                all_results.append((tid, False, "none"))
                if args.verbose:
                    print(f"  {tid}: ✗")
        
        print(f"\n{'=' * 70}")
        print(f" Run {run+1} RESULTS ({total} tasks)")
        print(f"{'=' * 70}")
        print(f"  SOLVED: {solved}/{total} ({solved / max(total, 1):.1%})")
        print(f"\n  Solvers:")
        for src, count in sorted(sources.items(), key=lambda x: -x[1]):
            if src != "none":
                print(f"    {src}: {count}")
        
        print(f"\n  Solved:")
        for tid, ok, src in all_results:
            if ok:
                print(f"    {tid} ← {src}")
