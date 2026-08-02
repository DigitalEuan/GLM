"""
v054_mog_construction.py — MOG + Construction System ARC Solver (v2)
====================================================================

D = fill/propagate (background fill)
X = erase (remove colour)  
N = nest (conditional recolour based on object properties)
J = join (compose operations in sequence)

Key fix: N primitives are CONDITIONAL on object properties (size, colour).
This is what the Construction System's "nesting" means — placing a new
colour INSIDE an object's context, subject to the object's properties.

Full transparency: every result is reported honestly.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import permutations
import sys, os, signal

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task


# ══════════════════════════════════════════════════════════════════════════════
# OBJECT EXTRACTION
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
            centroid_r = sum(r for r, _ in cells) / len(cells)
            centroid_c = sum(c for _, c in cells) / len(cells)
            objects.append({
                'cells': cells, 'colour': colour, 'size': len(cells),
                'centroid': (centroid_r, centroid_c),
            })
    return objects


def eval_prop(obj: Dict, prop: str, op: str, val: Any) -> bool:
    if prop == 'size': actual = obj['size']
    elif prop == 'colour': actual = obj['colour']
    else: return False
    if op == '==': return actual == val
    if op == '!=': return actual != val
    if op == '>=': return actual >= val
    if op == '<=': return actual <= val
    return False


def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c] for r in range(g1.height) for c in range(g1.width))


# ══════════════════════════════════════════════════════════════════════════════
# CONSTRUCTION PRIMITIVES
# ══════════════════════════════════════════════════════════════════════════════

def op_D_fill(grid: Grid, colour: int) -> Grid:
    """D: fill all zeros with colour."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if cells[r][c] == 0:
                cells[r][c] = colour
    return Grid(cells)


def op_X_erase(grid: Grid, colour: int) -> Grid:
    """X: erase all instances of colour."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if cells[r][c] == colour:
                cells[r][c] = 0
    return Grid(cells)


def op_N_recolour(grid: Grid, from_col: int, to_col: int) -> Grid:
    """N: unconditional recolour."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if cells[r][c] == from_col:
                cells[r][c] = to_col
    return Grid(cells)


def op_N_conditional(grid: Grid, prop: str, op: str, val: Any, outcome: int) -> Grid:
    """N: conditional recolour based on object property."""
    objs = extract_objects(grid)
    cells = [row[:] for row in grid.cells]
    for obj in objs:
        if eval_prop(obj, prop, op, val):
            for r, c in obj['cells']:
                cells[r][c] = outcome
    return Grid(cells)


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER
# ══════════════════════════════════════════════════════════════════════════════

def solve(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    same_size = all(p.input.height == p.output.height and p.input.width == p.output.width
                    for p in task.train)
    if not same_size:
        return None

    # Gather primitives
    bg_fills = set()
    erase_cols = set()
    recolour_map = {}

    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                if ic == 0 and oc != 0:
                    bg_fills.add(oc)
                elif ic != 0 and oc == 0:
                    erase_cols.add(ic)
                elif ic != 0 and oc != 0 and ic != oc:
                    if ic in recolour_map:
                        if recolour_map[ic] != oc:
                            recolour_map[ic] = None
                    else:
                        recolour_map[ic] = oc

    recolour_map = {k: v for k, v in recolour_map.items() if v is not None}
    bg = bg_fills.pop() if len(bg_fills) == 1 else None

    # ═══ Single-step tests ═══

    # D: simple fill
    if bg is not None:
        def fill_fn(grid): return op_D_fill(grid, bg)
        if _verify(fill_fn, task):
            return _predict(fill_fn, task), f"D(fill={bg})"

    # N: unconditional recolour
    for fc, tc in recolour_map.items():
        def rc_fn(g, f=fc, t=tc): return op_N_recolour(g, f, t)
        if _verify(rc_fn, task):
            return _predict(rc_fn, task), f"N({fc}→{tc})"

    # ═══ Conditional N (the key insight from Construction System) ═══
    # N nests a new colour INSIDE an object's context.
    # The condition is the object's property.

    # Gather conditional observations
    prop_obs = defaultdict(lambda: defaultdict(set))

    for pair_idx, pair in enumerate(task.train):
        inp_objs = extract_objects(pair.input)
        out_objs = extract_objects(pair.output)

        for in_obj in inp_objs:
            # Find matching output object
            best_out, best_dist = None, float('inf')
            for out_obj in out_objs:
                dr = in_obj['centroid'][0] - out_obj['centroid'][0]
                dc = in_obj['centroid'][1] - out_obj['centroid'][1]
                dist = (dr*dr + dc*dc) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best_out = out_obj

            if best_out and best_dist < 5.0 and in_obj['colour'] != best_out['colour']:
                outcome = best_out['colour']
                for prop in ['size', 'colour']:
                    val = in_obj[prop]
                    for op in ['==', '>=', '<=']:
                        prop_obs[(prop, op, val)][pair_idx].add(outcome)

                # Also try size thresholds
                if in_obj['size'] >= 2:
                    for t in range(2, max(o['size'] for o in inp_objs) + 1):
                        if in_obj['size'] >= t:
                            prop_obs[('size', '>=', t)][pair_idx].add(outcome)

    # Find consistent conditional N rules
    n_pairs = len(task.train)
    for (prop, op, val), pair_outcomes in prop_obs.items():
        if len(pair_outcomes) != n_pairs:
            continue

        outcomes = set()
        for pi in range(n_pairs):
            po = pair_outcomes.get(pi, set())
            if len(po) != 1:
                outcomes = set()
                break
            outcomes.add(next(iter(po)))
        if len(outcomes) != 1:
            continue

        outcome = next(iter(outcomes))

        # Check it's NOT true for unchanged objects
        only_recolour = True
        for pair in task.train:
            inp_objs = extract_objects(pair.input)
            out_objs = extract_objects(pair.output)
            for in_obj in inp_objs:
                best_out, best_dist = None, float('inf')
                for out_obj in out_objs:
                    dr = in_obj['centroid'][0] - out_obj['centroid'][0]
                    dc = in_obj['centroid'][1] - out_obj['centroid'][1]
                    dist = (dr*dr + dc*dc) ** 0.5
                    if dist < best_dist:
                        best_dist = dist
                        best_out = out_obj
                if best_out and best_dist < 5.0 and in_obj['colour'] == best_out['colour']:
                    if eval_prop(in_obj, prop, op, val):
                        only_recolour = False
                        break
            if not only_recolour:
                break

        if not only_recolour:
            continue

        # Test conditional N
        def cond_fn(g, p=prop, o=op, v=val, oc=outcome):
            return op_N_conditional(g, p, o, v, oc)

        if _verify(cond_fn, task):
            return _predict(cond_fn, task), f"N({prop} {op} {val}→{outcome})"

    # ═══ Compositions (J primitive) ═══

    # D + N(unconditional)
    if bg is not None:
        for fc, tc in recolour_map.items():
            def dn_fn(g, b=bg, f=fc, t=tc):
                return op_N_recolour(op_D_fill(g, b), f, t)
            if _verify(dn_fn, task):
                return _predict(dn_fn, task), f"D({bg}) + N({fc}→{tc})"

    # D + N(conditional)
    if bg is not None:
        for (prop, op_str, val), pair_outcomes in prop_obs.items():
            if len(pair_outcomes) != n_pairs:
                continue
            outcomes = set()
            for pi in range(n_pairs):
                po = pair_outcomes.get(pi, set())
                if len(po) != 1:
                    outcomes = set()
                    break
                outcomes.add(next(iter(po)))
            if len(outcomes) != 1:
                continue
            outcome = next(iter(outcomes))

            def dcond_fn(g, b=bg, p=prop, o=val, v=val, oc=outcome):
                filled = op_D_fill(g, b)
                return op_N_conditional(filled, p, o, v, oc)
            if _verify(dcond_fn, task):
                return _predict(dcond_fn, task), f"D({bg}) + N({prop} {op_str} {val}→{outcome})"

    # X + D (erase + fill)
    for ec in erase_cols:
        if bg is not None:
            def xd_fn(g, e=ec, b=bg):
                return op_D_fill(op_X_erase(g, e), b)
            if _verify(xd_fn, task):
                return _predict(xd_fn, task), f"X({ec}) + D({bg})"

    # N + N (double recolour)
    items = list(recolour_map.items())
    for i in range(len(items)):
        for j in range(len(items)):
            if i == j:
                continue
            f1, t1 = items[i]
            f2, t2 = items[j]
            def nn_fn(g, a=f1, b=t1, c=f2, d=t2):
                return op_N_recolour(op_N_recolour(g, a, b), c, d)
            if _verify(nn_fn, task):
                return _predict(nn_fn, task), f"N({f1}→{t1}) + N({f2}→{t2})"

    # D + X + N (fill + erase + recolour)
    if bg is not None:
        for ec in erase_cols:
            for fc, tc in recolour_map.items():
                def dxn_fn(g, b=bg, e=ec, f=fc, t=tc):
                    return op_N_recolour(op_D_fill(op_X_erase(g, e), b), f, t)
                if _verify(dxn_fn, task):
                    return _predict(dxn_fn, task), f"X({ec}) + D({bg}) + N({fc}→{tc})"

    # N + D (recolour + fill)
    if bg is not None:
        for fc, tc in recolour_map.items():
            def nd_fn(g, f=fc, t=tc, b=bg):
                return op_D_fill(op_N_recolour(g, f, t), b)
            if _verify(nd_fn, task):
                return _predict(nd_fn, task), f"N({fc}→{tc}) + D({bg})"

    return None


def _verify(fn, task: ARCTask) -> bool:
    for pair in task.train:
        pred = fn(pair.input)
        if not grids_equal(pred, pair.output):
            return False
    return True


def _predict(fn, task: ARCTask) -> Grid:
    return fn(task.test[0].input)


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
    print(" MOG + CONSTRUCTION v054")
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
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        if src != "none":
            print(f"    {src}: {count}")

    print(f"\n  Solved:")
    for tid, ok, src in all_results:
        if ok:
            print(f"    {tid} ← {src}")
