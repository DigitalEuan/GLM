"""
v025_pipeline.py — v0.29: cortex (Y observer + viewpoints + rule derivation)
==============================================================================

The cortex is now wired in.  It tries, in order:
  1. Trigger-mapping rules ("A next to T → C")
  2. Dynamic contextual rules ("A next to B → mapping[B]")
  3. Pattern rules ("IF property P THEN transform")
  4. Orthographic rule (global colour mapping, from Y's outside view)
  5. Perspective rule (focal vs peripheral, from Y's inside view)
  6. Combined rule

If the cortex produces a verified prediction, it wins (priority 1).
Otherwise, fall back to the senses (arm, hex, taste, DSL, paths).
"""
from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from fractions import Fraction
import sys, os, time, math, signal

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


class _OpTimeout(Exception):
    pass

def _alarm_handler(s, f):
    raise _OpTimeout()

signal.signal(signal.SIGALRM, _alarm_handler)

def _apply_timed(prog, grid, seconds=1.5):
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return prog.apply(grid)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


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
    ns = sum(x * x for x in snapped)
    tax = Fraction(hw) * Y + Fraction(ns, 8)
    return Fraction(10) / (Fraction(10) + tax)


COHERENCE_THRESHOLD = 0.7


def solve(task: ARCTask) -> Tuple[Optional[Grid], str, Dict]:
    """Solve with the v0.29 pipeline — cortex + all 6 senses."""
    test_input = task.test[0].input
    candidates: List[Tuple[Grid, str, int, float]] = []

    # ── CORTEX (priority 1) ──
    # The cortex tries to derive rules from train.
    # If it succeeds, it wins over the senses.
    try:
        from vendor.cortex_v2 import predict as cortex_predict
        cortex_pred, cortex_src, cortex_diag = cortex_predict(task)
        if cortex_pred is not None:
            cortex_priority = {
                "cortex_trigger": 1,        # most specific rule
                "cortex_dynamic": 1,
                "cortex_pattern": 2,
                "cortex_orthographic": 3,
                "cortex_perspective": 3,
                "cortex_combined": 3,
                "cortex_pattern_single": 2,
            }.get(cortex_src, 5)
            candidates.append((cortex_pred, cortex_src, cortex_priority,
                                float(_nrci(cortex_pred))))
    except Exception:
        pass

    # ── SENSES (priority 2-7) ──
    # Touch (k-arm + soft neighbourhood)
    from generative.geometric_language import (
        read_sentence, predict_with_free_arm, KArmConfig,
    )
    from generative.hex_learner import predict_best

    sentence = read_sentence(task)
    try:
        arm_pred, arm_src, _ = predict_with_free_arm(task)
        if arm_pred is not None:
            arm_priority = {
                "rotation_only": 0,
                "identity": 0,
                "free_k_arm_neighbourhood": 3,
                "free_k_arm": 3,
                "free_k_arm_no_rot": 4,
                "free_k_arm_pos_only": 5,
            }.get(arm_src, 8)
            candidates.append((arm_pred, arm_src, arm_priority, float(_nrci(arm_pred))))
    except Exception:
        pass

    # Audition (generative)
    try:
        from vendor.auditory_sense import predict_generative
        aud_pred, aud_src, _ = predict_generative(task)
        if aud_pred is not None:
            candidates.append((aud_pred, aud_src, 2, float(_nrci(aud_pred))))
    except Exception:
        pass

    # Hex-learner
    try:
        hex_pred, hex_src, _ = predict_best(task)
        if hex_pred is not None:
            hex_priority = {
                "hex_uniform_delta": 2,
                "hex_colour_mapping": 3,
                "hex_nearest_address": 7,
            }.get(hex_src, 8)
            if not any(s == hex_src for _, s, _, _ in candidates):
                candidates.append((hex_pred, hex_src, hex_priority, float(_nrci(hex_pred))))
    except Exception:
        pass

    # Taste (generative)
    try:
        from vendor.taste_generative import predict_best_taste
        taste_pred, taste_src, _ = predict_best_taste(task)
        if taste_pred is not None:
            candidates.append((taste_pred, taste_src, 2, float(_nrci(taste_pred))))
    except Exception:
        pass

    # DSL ops (fallback)
    for op in Ops:
        try:
            prog = Program([Operation(op)])
            if _train_pass(task, prog):
                pred = _apply_timed(prog, test_input)
                op_name = f"dsl_{op.name}"
                if op.name in ("GRAVITY_DOWN", "GRAVITY_UP", "GRAVITY_LEFT", "GRAVITY_RIGHT",
                                "ROTATE_90", "ROTATE_180", "ROTATE_270",
                                "FLIP_H", "FLIP_V", "TRANSPOSE"):
                    priority = 1
                elif op.name in ("CROP_TO_NONZERO", "TILE_2X",
                                  "SHIFT_UP", "SHIFT_DOWN", "SHIFT_LEFT", "SHIFT_RIGHT"):
                    priority = 2
                elif op.name == "RECOLOUR":
                    priority = 3
                else:
                    priority = 5
                candidates.append((pred, op_name, priority, float(_nrci(pred))))
        except Exception:
            continue

    # Train-derived colour mappings
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
            pred = _apply_timed(prog, test_input)
            candidates.append((pred, "train_map", 4, float(_nrci(pred))))

    # Prediction paths
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
                    candidates.append((pred, name, 7, float(_nrci(pred))))
            except Exception:
                pass
    except Exception:
        pass

    n_after_gen = len(candidates)

    # Coherence gate
    coherent = [c for c in candidates if c[3] >= COHERENCE_THRESHOLD]
    if not coherent and candidates:
        coherent = candidates
    n_after_coherence = len(coherent)

    # Tiebreak
    if coherent:
        try:
            from vendor.smell_taste_sense import smell_grid, smell_similarity
            train_output_smell = smell_grid(task.train[0].output)
            augmented = []
            for pred, src, prio, nrci in coherent:
                pred_smell = smell_grid(pred)
                smell_sim = smell_similarity(pred_smell, train_output_smell)
                augmented.append((pred, src, prio, nrci, smell_sim))
            augmented.sort(key=lambda x: (x[2], -x[4], -x[3]))
            best = augmented[0]
            return best[0], best[1], {
                "n_candidates": n_after_gen,
                "n_coherent": n_after_coherence,
                "sources": [s for _, s, _, _, _ in augmented],
                "sentence": {
                    "rotation": sentence.rotation,
                    "direction_confidence": sentence.direction_confidence,
                    "colour_mapping": sentence.colour_mapping,
                },
                "smell_score": best[4],
                "priority": best[2],
                "nrci": best[3],
                "coherence_threshold": COHERENCE_THRESHOLD,
            }
        except Exception:
            coherent.sort(key=lambda x: (x[2], -x[3]))
            best = coherent[0]
            return best[0], best[1], {
                "n_candidates": n_after_gen,
                "n_coherent": n_after_coherence,
                "sources": [s for _, s, _, _ in coherent],
                "priority": best[2],
                "nrci": best[3],
            }
    return test_input.copy(), "none", {
        "n_candidates": n_after_gen,
        "n_coherent": n_after_coherence,
        "coherence_threshold": COHERENCE_THRESHOLD,
    }


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
    t_total = 0
    sources = {}
    cortex_wins = 0

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
        if src.startswith("cortex_"):
            cortex_wins += 1
        if args.verbose or ok:
            print(f"  {fname}: {'OK' if ok else 'X'} src={src} "
                  f"gen={diag.get('n_candidates', 0)} "
                  f"coh={diag.get('n_coherent', 0)} "
                  f"({time.time() - t0:.2f}s)")

    print(f"\n═══ v0.29 ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Time: {t_total:.1f}s (avg {t_total / max(total, 1):.2f}s/task)")
    print(f"  Cortex wins: {cortex_wins}")
    print(f"  Sources: {sources}")
