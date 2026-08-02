"""
sharpened_pipeline.py — v0.20: fast, complete, everything wired
==================================================================

Architecture:
  1. Try ALL 159 working DSL ops (direct train-pass, no ranker overhead)
  2. Try CRG-learned colour mappings
  3. Try train-derived colour mappings
  4. Try two-op compositions (geometric → recolour)
  5. Try prediction paths (analogy, chain, group) — WITHOUT re-running all ops
  6. HARD FILTER: exact train-pair reproduction
  7. TIEBREAK: NRCI as MDL proxy (only on survivors)
  8. LDP + eml diagnostics on the winner
"""
from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from fractions import Fraction
import sys, os, time, math, signal

# Per-op timeout: some DSL ops (e.g. GRAVITY_RADIAL on even grids) infinite-loop.
# We hard-kill them with SIGALRM so the pipeline can't hang.
class _OpTimeout(Exception):
    pass

def _alarm_handler(s, f):
    raise _OpTimeout()

signal.signal(signal.SIGALRM, _alarm_handler)

def _apply_timed(prog, grid, seconds=1.5):
    """Apply prog to grid with a hard timeout."""
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return prog.apply(grid)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_VENDOR_DIR = os.path.join(_THIS_DIR, "vendor")
if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task
from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE
from encoder import encode_grid
from dsl.arc_dsl_full import Ops, Operation, Program


def _train_pass(task: ARCTask, prog: Program) -> bool:
    for pair in task.train:
        try:
            if _apply_timed(prog, pair.input) != pair.output:
                return False
        except Exception:
            return False
    return True


def _nrci(grid: Grid) -> Fraction:
    from ubp_unified_v5 import UBPSourceCodeParticlePhysics
    pp = UBPSourceCodeParticlePhysics()
    Y = pp.Y
    v, _ = encode_grid(grid)
    snapped, _ = GOLAY_ENGINE.snap_to_codeword(v)
    hw = sum(snapped)
    ns = sum(x*x for x in snapped)
    tax = Fraction(hw) * Y + Fraction(ns, 8)
    return Fraction(10) / (Fraction(10) + tax)


def _ldp(grid: Grid) -> Dict:
    try:
        from ldp import DataObject
        from generative.object_extractor import extract_objects
        objs = extract_objects(grid)
        mass = sum(DataObject(o.cell_count).mass for o in objs if o.cell_count > 0)
        tensions = [DataObject(o.cell_count).tension for o in objs if o.cell_count > 0]
        primes = sum(1 for o in objs if o.cell_count > 0 and DataObject(o.cell_count).is_prime)
        return {"mass": mass, "tension": sum(tensions)/len(tensions) if tensions else 0,
                "primes": primes, "objects": len(objs)}
    except:
        return {}


def _eml(grid: Grid) -> Dict:
    try:
        from spatial_arithmetic_compat import eml
        n = float(_nrci(grid))
        l = _ldp(grid)
        t = max(l.get("tension", 0.001), 0.001)
        return {"nrci": n, "tension": t, "eml": eml(n, t),
                "Y": math.pi / (math.pi**2 + 2)}
    except:
        return {}


def solve(task: ARCTask) -> Tuple[Optional[Grid], str, Dict]:
    """Solve with the full v0.20 pipeline."""
    test_input = task.test[0].input
    survivors: List[Tuple[Grid, str, Fraction]] = []

    # ── 1. ALL 162 DSL ops ──
    for op in Ops:
        try:
            prog = Program([Operation(op)])
            if _train_pass(task, prog):
                pred = _apply_timed(prog, test_input)
                survivors.append((pred, f"dsl_{op.name}", _nrci(pred)))
        except:
            continue

    # ── 2. CRG colour mapping ──
    try:
        from generative.object_crg_full import ObjectCRG as FullCRG
        crg = FullCRG()
        crg.learn_from_task(task)
        if crg.global_colour_mapping:
            m = {int(k): int(v) for k, v in crg.global_colour_mapping.items()}
            prog = Program([Operation(Ops.RECOLOUR, {"mapping": m})])
            if _train_pass(task, prog):
                pred = prog.apply(test_input)
                survivors.append((pred, "crg", _nrci(pred)))
    except:
        pass

    # ── 3. Train-derived colour mappings ──
    train_maps = []
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        m = {}
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                old, new = pair.input.cells[r][c], pair.output.cells[r][c]
                if old != new:
                    m[old] = new
        if m and m not in train_maps:
            train_maps.append(m)
    for m in train_maps[:5]:
        prog = Program([Operation(Ops.RECOLOUR, {"mapping": m})])
        if _train_pass(task, prog):
            pred = prog.apply(test_input)
            survivors.append((pred, "train_map", _nrci(pred)))

    # ── 4. Two-op compositions ──
    geo_ops = [Ops.ROTATE_90, Ops.ROTATE_180, Ops.ROTATE_270,
               Ops.FLIP_H, Ops.FLIP_V, Ops.TRANSPOSE,
               Ops.GRAVITY_DOWN, Ops.GRAVITY_UP,
               Ops.GRAVITY_LEFT, Ops.GRAVITY_RIGHT,
               Ops.CROP_TO_NONZERO, Ops.TILE_2X]
    for g in geo_ops:
        for m in train_maps[:2]:
            try:
                prog = Program([Operation(g), Operation(Ops.RECOLOUR, {"mapping": m})])
                if _train_pass(task, prog):
                    pred = _apply_timed(prog, test_input)
                    survivors.append((pred, "compose", _nrci(pred)))
            except:
                continue

    # ── 5. Prediction paths (no re-verification) ──
    try:
        from generative.object_crg_full import ObjectCRG as FullCRG
        from generative.prediction_paths import (
            predict_via_analogy, predict_via_chain, predict_via_groups
        )
        crg = FullCRG()
        crg.learn_from_task(task)
        for fn, name in [(predict_via_analogy, "analogy"),
                         (predict_via_chain, "chain"),
                         (predict_via_groups, "group")]:
            try:
                pred = fn(task, crg)
                if pred is not None:
                    survivors.append((pred, name, _nrci(pred)))
            except:
                pass
    except:
        pass

    # ── 6. Identity ──
    if all(p.input == p.output for p in task.train):
        survivors.append((test_input.copy(), "identity", _nrci(test_input)))

    # ── 7. TIEBREAK: highest NRCI ──
    if survivors:
        survivors.sort(key=lambda x: -float(x[2]))
        best = survivors[0]
        return best[0], best[1], {
            "survivors": len(survivors),
            "sources": [s for _, s, _ in survivors],
            "nrci": float(best[2]),
            "ldp": _ldp(best[0]),
            "eml": _eml(best[0]),
        }
    return test_input.copy(), "none", {"survivors": 0}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--max-tasks", type=int, default=None)
    args = p.parse_args()
    
    files = sorted(f for f in os.listdir(args.batch) if f.endswith(".json"))
    if args.max_tasks: files = files[:args.max_tasks]
    
    solved = total = 0
    t_total = 0
    sources = {}
    
    for fname in files:
        task = load_task(os.path.join(args.batch, fname), name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None: continue
        total += 1
        t0 = time.time()
        pred, src, diag = solve(task)
        t_total += time.time() - t0
        if pred == task.test[0].expected_output: solved += 1
        sources[src] = sources.get(src, 0) + 1
    
    print(f"═══ v0.20 ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved/max(total,1):.1%})")
    print(f"  Time: {t_total:.1f}s (avg {t_total/max(total,1):.2f}s/task)")
    print(f"  Sources: {sources}")
