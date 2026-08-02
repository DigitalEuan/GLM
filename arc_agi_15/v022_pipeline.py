"""
v022_pipeline.py — v0.22: GLM as language machine
====================================================

The user's reframe: "this is a language machine not a script pipeline".
v0.22 stops being a script pipeline and starts being a language machine.

The pipeline structure:

  1. READ the task in geometric language
     - read_sentence() produces a GeometricSentence: rotation, Time,
       direction_mode, per_colour_directions, per_position_directions
     - identify_cells() gives every cell its full colour-space identity
       (ARC colour, hex, bridge address, RGB332, complement, harmony)

  2. SPEAK the prediction in geometric language
     - predict_with_free_arm() runs the free k-arm driven by the sentence
     - The arm has shoulder (test cell), elbow (rotation), wrist (Time),
       fingertips (K nearest train cells)
     - The arm is NOT anchored at Y — Y is diagnostic only

  3. VERIFY with the hard gate (non-negotiable)
     - Every candidate must reproduce every train pair exactly

  4. TIEBREAK by source priority (MDL / Occam's razor)
     - rotation_only < identity < free_k_arm < dsl_gravity/rotate/flip
       < dsl_recolour < train_map < hex_nearest < analogy/chain/group

  5. DIAGNOSE with the full UBP stack
     - HDRB signature (Hodge decomposition)
     - Colour-space bridge (RGB332 distance, complement, harmony)
     - NRCI, LDP, eml (still computed, never used for selection)

The change vs v0.21: the geometric language DRIVES generation.  The
GLM reads the sentence, speaks the prediction, verifies, tiebreaks,
diagnoses.  The 162 DSL ops become a fallback, not the primary path.
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


# ── per-op timeout ───────────────────────────────────────────────────────────
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


# ══════════════════════════════════════════════════════════════════════════════
# SOLVE
# ══════════════════════════════════════════════════════════════════════════════

def solve(task: ARCTask) -> Tuple[Optional[Grid], str, Dict]:
    """Solve with the v0.22 language-machine pipeline."""
    test_input = task.test[0].input
    survivors: List[Tuple[Grid, str, int]] = []  # (grid, source, priority)

    # ── 1. READ: geometric sentence + colour-space identity ──
    from generative.geometric_language import (
        read_sentence, predict_with_free_arm, KArmConfig,
    )
    from generative.hex_learner import (
        learn_from_task, predict_best,
    )

    sentence = read_sentence(task)

    # ── 2. SPEAK: free k-arm driven by the sentence ──
    try:
        arm_pred, arm_src, arm_diag = predict_with_free_arm(task)
        if arm_pred is not None:
            # Source priority for arm predictions
            arm_priority = {
                "rotation_only": 0,        # rotation alone explains train
                "identity": 0,             # identity
                "free_k_arm": 3,           # full k-arm with neighbourhood+rotation+per-colour+per-position
                "free_k_arm_neighbourhood": 3,  # neighbourhood-only (deepest learning)
                "free_k_arm_no_rot": 4,    # k-arm without rotation
                "free_k_arm_pos_only": 5,  # k-arm with position lookup only
            }.get(arm_src, 8)
            survivors.append((arm_pred, arm_src, arm_priority))
    except Exception:
        pass

    # ── 3. Hex-learner (uniform delta, colour mapping, k-NN) ──
    try:
        hex_pred, hex_src, hex_diag = predict_best(task)
        if hex_pred is not None:
            hex_priority = {
                "hex_uniform_delta": 2,
                "hex_colour_mapping": 3,
                "hex_nearest_address": 7,
            }.get(hex_src, 8)
            # Only add if not already present from free_arm
            if not any(s == hex_src for _, s, _ in survivors):
                survivors.append((hex_pred, hex_src, hex_priority))
    except Exception:
        pass

    # ── 4. ALL 162 DSL ops (fallback) ──
    for op in Ops:
        try:
            prog = Program([Operation(op)])
            if _train_pass(task, prog):
                pred = _apply_timed(prog, test_input)
                # DSL priority
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
                survivors.append((pred, op_name, priority))
        except Exception:
            continue

    # ── 5. Train-derived colour mappings ──
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
            survivors.append((pred, "train_map", 4))

    # ── 6. Prediction paths (analogy, chain, group) ──
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
                    survivors.append((pred, name, 7))
            except Exception:
                pass
    except Exception:
        pass

    # ── 7. TIEBREAK: source priority (Occam's razor) ──
    if survivors:
        # Sort by priority ascending (lower = simpler = preferred)
        survivors.sort(key=lambda x: x[2])
        best = survivors[0]
        return best[0], best[1], {
            "survivors": len(survivors),
            "sources": [s for _, s, _ in survivors],
            "sentence": {
                "rotation": sentence.rotation,
                "direction_mode_hamming": sentence.direction_mode_hamming,
                "direction_confidence": sentence.direction_confidence,
                "per_colour_count": len(sentence.per_colour_directions),
                "per_position_count": len(sentence.per_position_directions),
                "colour_mapping": sentence.colour_mapping,
            },
            "priority": best[2],
            "nrci": float(_nrci(best[0])),
        }
    return test_input.copy(), "none", {
        "survivors": 0,
        "sentence": {
            "rotation": sentence.rotation,
            "direction_confidence": sentence.direction_confidence,
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

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
    rotations_found = 0
    identities_found = 0
    arm_wins = 0

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
        sent = diag.get("sentence", {})
        if sent.get("rotation", "identity") != "identity":
            rotations_found += 1
        if src.startswith("free_k_arm") or src in ("rotation_only", "identity"):
            arm_wins += 1
            if src == "identity":
                identities_found += 1
        if args.verbose or ok:
            print(f"  {fname}: {'OK' if ok else 'X'} src={src} "
                  f"survivors={diag.get('survivors', 0)} "
                  f"rot={sent.get('rotation', 'identity')} "
                  f"conf={sent.get('direction_confidence', 0):.2f} "
                  f"({time.time() - t0:.2f}s)")

    print(f"\n═══ v0.22 ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Time: {t_total:.1f}s (avg {t_total / max(total, 1):.2f}s/task)")
    print(f"  Rotations detected: {rotations_found}")
    print(f"  Identities detected: {identities_found}")
    print(f"  Arm wins: {arm_wins}")
    print(f"  Sources: {sources}")
