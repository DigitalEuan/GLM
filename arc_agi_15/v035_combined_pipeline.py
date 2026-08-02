"""
v035_combined_pipeline.py — Unified pipeline combining all approaches
=====================================================================

Combines:
1. DSL ops (gravity, rotate, flip, etc.)
2. Consistent recolour detection
3. DSL pair compositions (geo + recolour)
4. Minkowski sweep (p=1, 1.5, 2, inf)
5. Totient kinetics features

Goal: maximize candidate coverage across all 50 tasks.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter
import sys, os, time, signal
import numpy as np

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task
from dsl.arc_dsl_full import Ops, Operation, Program


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


def _apply_timed(prog, grid, seconds=1.0):
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return prog.apply(grid)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def _train_pass(task, prog):
    for pair in task.train:
        try:
            if _apply_timed(prog, pair.input) != pair.output:
                return False
        except:
            return False
    return True


# ═══════════════════════════════════════════════════════════════════
# SOURCE 1: DSL OPS
# ═══════════════════════════════════════════════════════════════════

def try_dsl_ops(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Try all single DSL operations."""
    for op in Ops:
        try:
            prog = Program([Operation(op)])
            if _train_pass(task, prog):
                pred = _apply_timed(prog, task.test[0].input)
                return pred, f"dsl_{op.name}"
        except:
            continue
    return None


# ═══════════════════════════════════════════════════════════════════
# SOURCE 2: CONSISTENT RECOLOUR
# ═══════════════════════════════════════════════════════════════════

def try_consistent_recolour(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Detect consistent colour mappings across all train pairs."""
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Build mapping from first pair
    mapping = {}
    for r in range(task.train[0].input.height):
        for c in range(task.train[0].input.width):
            ic = task.train[0].input.cells[r][c]
            oc = task.train[0].output.cells[r][c]
            if ic in mapping:
                if mapping[ic] != oc:
                    return None
            else:
                mapping[ic] = oc
    
    # Verify on other pairs
    for pair in task.train[1:]:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                ic = pair.input.cells[r][c]
                oc = pair.output.cells[r][c]
                if mapping.get(ic, ic) != oc:
                    return None
    
    if all(k == v for k, v in mapping.items()):
        return None
    
    # Apply
    test = task.test[0].input
    h, w = test.height, test.width
    cells = [row[:] for row in test.cells]
    for r in range(h):
        for c in range(w):
            if cells[r][c] in mapping:
                cells[r][c] = mapping[cells[r][c]]
    
    pred = Grid(cells)
    return pred, f"recolour_{len(mapping)}map"


# ═══════════════════════════════════════════════════════════════════
# SOURCE 3: DSL PAIR COMPOSITIONS
# ═══════════════════════════════════════════════════════════════════

_GEO_OPS = [
    Ops.ROTATE_90, Ops.ROTATE_180, Ops.ROTATE_270,
    Ops.FLIP_H, Ops.FLIP_V, Ops.TRANSPOSE,
    Ops.GRAVITY_DOWN, Ops.GRAVITY_UP, Ops.GRAVITY_LEFT, Ops.GRAVITY_RIGHT,
]


def try_geo_recolour_composition(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Try: geo_op → recolour (derived from train pairs)."""
    for pair in task.train:
        if pair.input.height == pair.output.height and pair.input.width == pair.output.width:
            break
    else:
        # All pairs change size — try size-change ops
        return None
    
    for geo_op in _GEO_OPS:
        try:
            # Apply geo op to all train inputs
            transformed = []
            skip = False
            for pair in task.train:
                prog = Program([Operation(geo_op)])
                t = _apply_timed(prog, pair.input)
                if t is None:
                    skip = True
                    break
                transformed.append((t, pair.output))
            if skip:
                continue
            
            # Check sizes match
            if any(t.height != o.height or t.width != o.width for t, o in transformed):
                continue
            
            # Derive recolour mapping
            mapping = {}
            consistent = True
            for t, o in transformed:
                for r in range(t.height):
                    for c in range(t.width):
                        ic, oc = t.cells[r][c], o.cells[r][c]
                        if ic in mapping:
                            if mapping[ic] != oc:
                                consistent = False
                                break
                        else:
                            mapping[ic] = oc
                    if not consistent:
                        break
                if not consistent:
                    break
            
            if not consistent or all(k == v for k, v in mapping.items()):
                continue
            
            # Test
            prog = Program([Operation(geo_op), Operation(Ops.RECOLOUR, {"mapping": mapping})])
            if _train_pass(task, prog):
                pred = _apply_timed(prog, task.test[0].input)
                return pred, f"geo_{geo_op.name}_recolour"
        except:
            continue
    
    return None


# ═══════════════════════════════════════════════════════════════════
# SOURCE 4: SIZE-CHANGE OPS
# ═══════════════════════════════════════════════════════════════════

_SIZE_OPS = [Ops.CROP_TO_NONZERO, Ops.TILE_2X, Ops.SCALE_2X, Ops.SCALE_HALF]


def try_size_change_ops(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Try operations that change grid size."""
    for op in _SIZE_OPS:
        try:
            prog = Program([Operation(op)])
            if _train_pass(task, prog):
                pred = _apply_timed(prog, task.test[0].input)
                return pred, f"size_{op.name}"
        except:
            continue
    return None


# ═══════════════════════════════════════════════════════════════════
# SOURCE 5: MINKOWSKI SWEEP
# ═══════════════════════════════════════════════════════════════════

def try_minkowski_sweep(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Use the Minkowski sweep to find distance-based rules."""
    try:
        from v033_minkowski_sweep import predict as minkowski_predict
        result = minkowski_predict(task)
        if result is not None:
            return result[0], result[1]
    except:
        pass
    return None


# ═══════════════════════════════════════════════════════════════════
# SOURCE 6: TRAIN-DERIVED COLOUR MAPPING (positional)
# ═══════════════════════════════════════════════════════════════════

def try_positional_recolour(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Try position-dependent colour mapping."""
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Try different modularities
    for mod_r in range(1, min(6, task.train[0].input.height + 1)):
        for mod_c in range(1, min(6, task.train[0].input.width + 1)):
            rules = {}
            consistent = True
            
            for pair in task.train:
                for r in range(pair.input.height):
                    for c in range(pair.input.width):
                        ic = pair.input.cells[r][c]
                        oc = pair.output.cells[r][c]
                        key = (ic, r % mod_r, c % mod_c)
                        if key in rules:
                            if rules[key] != oc:
                                consistent = False
                                break
                        else:
                            rules[key] = oc
                    if not consistent:
                        break
                if not consistent:
                    break
            
            if not consistent:
                continue
            
            if all(k[0] == v for k, v in rules.items()):
                continue
            
            # Apply
            test = task.test[0].input
            h, w = test.height, test.width
            cells = []
            for r in range(h):
                row = []
                for c in range(w):
                    ic = test.cells[r][c]
                    key = (ic, r % mod_r, c % mod_c)
                    row.append(rules.get(key, ic))
                cells.append(row)
            pred = Grid(cells)
            
            # Verify
            all_pass = True
            for pair in task.train:
                h, w = pair.input.height, pair.input.width
                cells = []
                for r in range(h):
                    row = []
                    for c in range(w):
                        ic = pair.input.cells[r][c]
                        key = (ic, r % mod_r, c % mod_c)
                        row.append(rules.get(key, ic))
                    cells.append(row)
                if not grids_equal(Grid(cells), pair.output):
                    all_pass = False
                    break
            
            if all_pass:
                return pred, f"pos_recolour_{mod_r}x{mod_c}"
    
    return None


# ═══════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════

def solve(task: ARCTask) -> Tuple[Optional[Grid], str, Dict]:
    """Run all candidate sources in priority order."""
    sources = [
        ("dsl", try_dsl_ops, 1),
        ("recolour", try_consistent_recolour, 2),
        ("geo_recolour", try_geo_recolour_composition, 3),
        ("size_change", try_size_change_ops, 4),
        ("positional", try_positional_recolour, 5),
        ("minkowski", try_minkowski_sweep, 6),
    ]
    
    for name, fn, priority in sources:
        try:
            signal.setitimer(signal.ITIMER_REAL, 8.0)
            result = fn(task)
            signal.setitimer(signal.ITIMER_REAL, 0)
            if result is not None:
                pred, src = result
                return pred, src, {"source": name, "priority": priority}
        except:
            signal.setitimer(signal.ITIMER_REAL, 0)
            continue
    
    return task.test[0].input.copy(), "identity", {"source": "fallback"}


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
    t_total = 0
    
    for fname in files:
        task = load_task(os.path.join(args.batch, fname),
                         name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1
        
        t0 = time.time()
        pred, src, diag = solve(task)
        t_total += time.time() - t0
        
        ok = (pred == task.test[0].expected_output)
        if ok:
            solved += 1
        sources[src] = sources.get(src, 0) + 1
        
        if args.verbose or ok:
            print(f"  {fname}: {'OK' if ok else 'X'} src={src} ({time.time()-t0:.2f}s)")
    
    print(f"\n═══ Combined Pipeline ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Time: {t_total:.1f}s (avg {t_total/max(total,1):.2f}s/task)")
    print(f"  Sources: {sources}")
