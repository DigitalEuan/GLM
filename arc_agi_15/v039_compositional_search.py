"""
v039_compositional_search.py — Multi-step Program Composition Search
=====================================================================

Implements a beam search through the space of composed DSL programs.

Architecture:
1. Generate candidate programs (single ops, pairs, triples)
2. Test each program on train pairs (hard gate)
3. Keep programs that pass train
4. Apply surviving programs to test input

Key insight: most ARC tasks need 2-3 operation compositions,
not single operations. The search space is manageable because
we only use ~20 useful DSL ops (not all 162).

Search strategy:
- Level 0: try all single ops
- Level 1: try all pairs (op1 → op2)
- Level 2: try promising triples (op1 → op2 → op3)
- Level 3: add recolour as final step (op1 → op2 → recolour)

MOG integration: use the encoder's MOG categories to inform
which ops to try (e.g., Mirrors ops for colour tasks,
Activation ops for spatial tasks).
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


def _apply_timed(prog: Program, grid: Grid, seconds: float = 0.5) -> Optional[Grid]:
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        result = prog.apply(grid)
        signal.setitimer(signal.ITIMER_REAL, 0)
        return result
    except:
        signal.setitimer(signal.ITIMER_REAL, 0)
        return None


def _train_pass(task: ARCTask, prog: Program) -> bool:
    """Check if program reproduces ALL train pairs exactly."""
    for pair in task.train:
        result = _apply_timed(prog, pair.input)
        if result is None or not grids_equal(result, pair.output):
            return False
    return True


# ═══════════════════════════════════════════════════════════════════
# 1. USEFUL OPS — the ~20 that ever win
# ═══════════════════════════════════════════════════════════════════

# Geometric ops (spatial transformations)
GEO_OPS = [
    Ops.ROTATE_90, Ops.ROTATE_180, Ops.ROTATE_270,
    Ops.FLIP_H, Ops.FLIP_V, Ops.TRANSPOSE,
    Ops.GRAVITY_DOWN, Ops.GRAVITY_UP, Ops.GRAVITY_LEFT, Ops.GRAVITY_RIGHT,
]

# Size-change ops
SIZE_OPS = [
    Ops.CROP_TO_NONZERO, Ops.TILE_2X,
    Ops.SCALE_2X, Ops.SCALE_HALF,
]

# Colour ops
COLOUR_OPS = [
    Ops.RECOLOUR,
]

# Shift ops
SHIFT_OPS = [
    Ops.SHIFT_UP, Ops.SHIFT_DOWN, Ops.SHIFT_LEFT, Ops.SHIFT_RIGHT,
]

# All useful ops
USEFUL_OPS = GEO_OPS + SIZE_OPS + SHIFT_OPS


# ═══════════════════════════════════════════════════════════════════
# 2. DERIVE RECOLOUR MAPPING FROM TRAIN PAIRS
# ═══════════════════════════════════════════════════════════════════

def derive_recolour_mapping(task: ARCTask, pre_op: Optional[Ops] = None) -> Optional[Dict[int, int]]:
    """
    Derive a colour mapping from train pairs.
    If pre_op is specified, apply it first, then derive mapping.
    """
    mapping = {}
    
    for pair in task.train:
        if pre_op is not None:
            prog = Program([Operation(pre_op)])
            transformed = _apply_timed(prog, pair.input)
            if transformed is None:
                return None
            if transformed.height != pair.output.height or transformed.width != pair.output.width:
                return None
        else:
            transformed = pair.input
            if transformed.height != pair.output.height or transformed.width != pair.output.width:
                return None
        
        for r in range(transformed.height):
            for c in range(transformed.width):
                ic = transformed.cells[r][c]
                oc = pair.output.cells[r][c]
                if ic in mapping:
                    if mapping[ic] != oc:
                        return None
                else:
                    mapping[ic] = oc
    
    if all(k == v for k, v in mapping.items()):
        return None  # Identity
    
    return mapping


# ═══════════════════════════════════════════════════════════════════
# 3. COMPOSITIONAL SEARCH ENGINE
# ═══════════════════════════════════════════════════════════════════

def search_single_ops(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Level 0: try all single useful ops."""
    for op in USEFUL_OPS:
        try:
            prog = Program([Operation(op)])
            if _train_pass(task, prog):
                pred = _apply_timed(prog, task.test[0].input)
                if pred is not None:
                    return pred, f"single_{op.name}"
        except:
            continue
    return None


def search_geo_recolour_pairs(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Level 1: try geo_op → recolour pairs."""
    for geo_op in GEO_OPS:
        mapping = derive_recolour_mapping(task, geo_op)
        if mapping is None:
            continue
        
        prog = Program([Operation(geo_op), Operation(Ops.RECOLOUR, {"mapping": mapping})])
        if _train_pass(task, prog):
            pred = _apply_timed(prog, task.test[0].input)
            if pred is not None:
                return pred, f"pair_{geo_op.name}_recolour"
    
    return None


def search_shift_recolour_pairs(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Level 1: try shift_op → recolour pairs."""
    for shift_op in SHIFT_OPS:
        mapping = derive_recolour_mapping(task, shift_op)
        if mapping is None:
            continue
        
        prog = Program([Operation(shift_op), Operation(Ops.RECOLOUR, {"mapping": mapping})])
        if _train_pass(task, prog):
            pred = _apply_timed(prog, task.test[0].input)
            if pred is not None:
                return pred, f"pair_{shift_op.name}_recolour"
    
    return None


def search_recolour_geo_pairs(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Level 1: try recolour → geo_op pairs."""
    # First derive recolour mapping from train
    mapping = derive_recolour_mapping(task)
    if mapping is None:
        return None
    
    for geo_op in GEO_OPS:
        prog = Program([Operation(Ops.RECOLOUR, {"mapping": mapping}), Operation(geo_op)])
        if _train_pass(task, prog):
            pred = _apply_timed(prog, task.test[0].input)
            if pred is not None:
                return pred, f"pair_recolour_{geo_op.name}"
    
    return None


def search_geo_geo_pairs(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Level 1: try geo_op1 → geo_op2 pairs."""
    for op1 in GEO_OPS:
        for op2 in GEO_OPS:
            if op1 == op2:
                continue
            try:
                prog = Program([Operation(op1), Operation(op2)])
                if _train_pass(task, prog):
                    pred = _apply_timed(prog, task.test[0].input)
                    if pred is not None:
                        return pred, f"pair_{op1.name}_{op2.name}"
            except:
                continue
    
    return None


def search_geo_shift_pairs(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Level 1: try geo_op → shift_op pairs."""
    for geo_op in GEO_OPS:
        for shift_op in SHIFT_OPS:
            try:
                prog = Program([Operation(geo_op), Operation(shift_op)])
                if _train_pass(task, prog):
                    pred = _apply_timed(prog, task.test[0].input)
                    if pred is not None:
                        return pred, f"pair_{geo_op.name}_{shift_op.name}"
            except:
                continue
    
    return None


def search_triple_compositions(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Level 2: try promising triples (geo → geo → recolour)."""
    for op1 in GEO_OPS[:5]:  # Top 5 geo ops
        for op2 in GEO_OPS[:5]:
            if op1 == op2:
                continue
            mapping = derive_recolour_mapping(task)
            if mapping is None:
                continue
            
            try:
                prog = Program([
                    Operation(op1), Operation(op2),
                    Operation(Ops.RECOLOUR, {"mapping": mapping})
                ])
                if _train_pass(task, prog):
                    pred = _apply_timed(prog, task.test[0].input)
                    if pred is not None:
                        return pred, f"triple_{op1.name}_{op2.name}_recolour"
            except:
                continue
    
    return None


def search_size_recolour_pairs(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Level 1: try size_op → recolour pairs."""
    for size_op in SIZE_OPS:
        mapping = derive_recolour_mapping(task, size_op)
        if mapping is None:
            continue
        
        prog = Program([Operation(size_op), Operation(Ops.RECOLOUR, {"mapping": mapping})])
        if _train_pass(task, prog):
            pred = _apply_timed(prog, task.test[0].input)
            if pred is not None:
                return pred, f"pair_{size_op.name}_recolour"
    
    return None


# ═══════════════════════════════════════════════════════════════════
# 4. MAIN PREDICTOR
# ═══════════════════════════════════════════════════════════════════

def predict(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Run compositional search."""
    # Level 0: single ops
    result = search_single_ops(task)
    if result:
        pred, src = result
        return pred, src, {"level": 0}
    
    # Level 1: pairs
    for search_fn in [
        search_geo_recolour_pairs,
        search_shift_recolour_pairs,
        search_recolour_geo_pairs,
        search_geo_geo_pairs,
        search_geo_shift_pairs,
        search_size_recolour_pairs,
    ]:
        try:
            signal.setitimer(signal.ITIMER_REAL, 10.0)
            result = search_fn(task)
            signal.setitimer(signal.ITIMER_REAL, 0)
            if result:
                pred, src = result
                return pred, src, {"level": 1}
        except:
            signal.setitimer(signal.ITIMER_REAL, 0)
            continue
    
    # Level 2: triples
    result = search_triple_compositions(task)
    if result:
        pred, src = result
        return pred, src, {"level": 2}
    
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
    t_total = 0
    
    for fname in files:
        task = load_task(os.path.join(args.batch, fname),
                         name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1
        
        t0 = time.time()
        try:
            signal.setitimer(signal.ITIMER_REAL, 30.0)
            result = predict(task)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except:
            signal.setitimer(signal.ITIMER_REAL, 0)
            result = None
        
        t_total += time.time() - t0
        
        if result is not None:
            pred, src, diag = result
            ok = (pred == task.test[0].expected_output)
            if ok:
                solved += 1
            sources[src] = sources.get(src, 0) + 1
            if args.verbose or ok:
                print(f"  {fname}: {'OK' if ok else 'X'} src={src} level={diag.get('level', '?')}")
        else:
            sources["none"] = sources.get("none", 0) + 1
            if args.verbose:
                print(f"  {fname}: X src=none")
    
    print(f"\n═══ Compositional Search ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Time: {t_total:.1f}s (avg {t_total/max(total,1):.2f}s/task)")
    print(f"  Sources: {sources}")
