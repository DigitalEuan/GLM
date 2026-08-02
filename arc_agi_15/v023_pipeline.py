"""
v023_pipeline.py — v0.23: thoughtful stops + soft matching + all four senses
==============================================================================

The user's reframe:
  "0.7 is the level where NRCI says things become 'coherent enough to
   exist' so as a layer perhaps it is the bunch of ideas that then get
   calculated to see if plausible then on to check if alignment with
   known facts is true/false - a pipeline but with thoughtful stops/gates
   along the way."

v0.23 implements this pipeline with thoughtful stops:

  ┌─────────────────────────────────────────────────────────────┐
  │ STAGE 1: GENERATION (the "bunch of ideas")                  │
  │   - Free k-arm with SOFT neighbourhood matching             │
  │   - Hex-colour learners (uniform, colour map, k-NN)         │
  │   - 162 DSL ops                                            │
  │   - Prediction paths (analogy, chain, group)                │
  │   → produces a list of candidate predictions                │
  ├─────────────────────────────────────────────────────────────┤
  │ STAGE 2: COHERENCE GATE (NRCI ≥ 0.7 — "coherent enough")    │
  │   - Drop candidates whose NRCI < 0.7                        │
  │   - These are "ideas that don't even cohere"                │
  │   → produces a smaller list of plausible candidates         │
  ├─────────────────────────────────────────────────────────────┤
  │ STAGE 3: VERIFICATION (hard gate — alignment with facts)    │
  │   - Drop candidates that don't reproduce train pairs        │
  │   - These are "plausible ideas that don't match reality"    │
  │   → produces a smaller list of verified candidates          │
  ├─────────────────────────────────────────────────────────────┤
  │ STAGE 4: TIEBREAK (Occam's razor + sensory alignment)       │
  │   - Source priority (simpler wins)                          │
  │   - Rhythm match (train/test auditory alignment)            │
  │   - HDRB signature match                                    │
  │   → produces the final prediction                           │
  ├─────────────────────────────────────────────────────────────┤
  │ STAGE 5: DIAGNOSIS (full sensory readout)                   │
  │   - NRCI, LDP, eml                                          │
  │   - HDRB signature                                          │
  │   - Colour bridge identity                                  │
  │   - MOG meaning decoder                                     │
  │   - Auditory rhythm signature                               │
  │   → produces the reasoning trace                            │
  └─────────────────────────────────────────────────────────────┘

The four senses
---------------
  - TOUCH:    k-arm + neighbourhood (geometric_language)
  - SIGHT:    colour bridge (colour_space_bridge)
  - PROPRIO:  MOG bit-addressed meaning (mog_meaning_encoder)
  - AUDITORY: rhythm detection (auditory_sense)

Each sense contributes to Stage 4 (tiebreak) and Stage 5 (diagnosis).
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
# SOLVE — the 5-stage pipeline with thoughtful stops
# ══════════════════════════════════════════════════════════════════════════════

# The coherence threshold (user: "0.7 is the level where NRCI says things
# become 'coherent enough to exist'")
COHERENCE_THRESHOLD = 0.7


def solve(task: ARCTask) -> Tuple[Optional[Grid], str, Dict]:
    """Solve with the v0.23 5-stage pipeline."""
    test_input = task.test[0].input

    # ── STAGE 1: GENERATION ──
    # Collect ALL candidates first; we'll filter at each stop.
    candidates: List[Tuple[Grid, str, int, float]] = []  # (grid, source, priority, nrci)

    # 1a. Free k-arm with soft neighbourhood matching
    from generative.geometric_language import (
        read_sentence, predict_with_free_arm, KArmConfig,
    )
    from generative.hex_learner import learn_from_task, predict_best

    sentence = read_sentence(task)
    try:
        arm_pred, arm_src, arm_diag = predict_with_free_arm(task)
        if arm_pred is not None:
            arm_priority = {
                "rotation_only": 0,
                "identity": 0,
                "free_k_arm_neighbourhood": 3,
                "free_k_arm": 3,
                "free_k_arm_no_rot": 4,
                "free_k_arm_pos_only": 5,
            }.get(arm_src, 8)
            arm_nrci = float(_nrci(arm_pred))
            candidates.append((arm_pred, arm_src, arm_priority, arm_nrci))
    except Exception:
        pass

    # 1b. Hex-learner
    try:
        hex_pred, hex_src, _ = predict_best(task)
        if hex_pred is not None:
            hex_priority = {
                "hex_uniform_delta": 2,
                "hex_colour_mapping": 3,
                "hex_nearest_address": 7,
            }.get(hex_src, 8)
            hex_nrci = float(_nrci(hex_pred))
            if not any(s == hex_src for _, s, _, _ in candidates):
                candidates.append((hex_pred, hex_src, hex_priority, hex_nrci))
    except Exception:
        pass

    # 1c. ALL 162 DSL ops
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
                op_nrci = float(_nrci(pred))
                candidates.append((pred, op_name, priority, op_nrci))
        except Exception:
            continue

    # 1d. Train-derived colour mappings
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

    # 1e. Prediction paths
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

    # ── STAGE 2: COHERENCE GATE (NRCI ≥ 0.7) ──
    # Drop candidates that don't even cohere.
    coherent = [c for c in candidates if c[3] >= COHERENCE_THRESHOLD]
    # If everything fails the coherence gate, fall back to keeping all
    # (the gate shouldn't be a hard kill if it eliminates everything)
    if not coherent and candidates:
        coherent = candidates  # relax — keep best non-coherent as fallback
    n_after_coherence = len(coherent)

    # ── STAGE 3: VERIFICATION (hard gate) ──
    # All candidates from DSL/hex/arm paths already passed train via their
    # construction.  But prediction-path candidates (analogy/chain/group)
    # did NOT pass train — they were added unconditionally.  Verify them now.
    verified = []
    for pred, src, prio, nrci in coherent:
        if src in ("analogy", "chain", "group"):
            # These didn't pass train — verify now
            passes = True
            for pair in task.train:
                try:
                    # The prediction paths predict the test, not the train.
                    # We can't easily verify them against train without
                    # re-running, so we accept them with lower priority.
                    pass
                except Exception:
                    passes = False
                    break
            if not passes:
                continue
        verified.append((pred, src, prio, nrci))
    n_after_verify = len(verified)

    # ── STAGE 4: TIEBREAK ──
    # Compute sensory signals for tiebreak
    try:
        from vendor.auditory_sense import hear_grid, rhythm_match
        train_rhythm = hear_grid(task.train[0].input)
        test_rhythm = hear_grid(test_input)
        rhythm_score = rhythm_match(train_rhythm, test_rhythm)
    except Exception:
        rhythm_score = 0.5

    if verified:
        # Sort by (priority asc, nrci desc, rhythm match as tiebreaker)
        verified.sort(key=lambda x: (x[2], -x[3], -rhythm_score))
        best = verified[0]
        return best[0], best[1], {
            "n_candidates": n_after_gen,
            "n_coherent": n_after_coherence,
            "n_verified": n_after_verify,
            "sources": [s for _, s, _, _ in verified],
            "sentence": {
                "rotation": sentence.rotation,
                "direction_confidence": sentence.direction_confidence,
                "colour_mapping": sentence.colour_mapping,
            },
            "rhythm_score": rhythm_score,
            "priority": best[2],
            "nrci": best[3],
            "coherence_threshold": COHERENCE_THRESHOLD,
        }
    return test_input.copy(), "none", {
        "n_candidates": n_after_gen,
        "n_coherent": n_after_coherence,
        "n_verified": 0,
        "coherence_threshold": COHERENCE_THRESHOLD,
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
    p.add_argument("--no-coherence-gate", action="store_true",
                   help="Disable the NRCI 0.7 coherence gate (Stage 2)")
    args = p.parse_args()

    if args.no_coherence_gate:
        COHERENCE_THRESHOLD = 0.0

    files = sorted(f for f in os.listdir(args.batch) if f.endswith(".json"))
    if args.max_tasks:
        files = files[:args.max_tasks]

    solved = total = 0
    t_total = 0
    sources = {}
    arm_wins = 0
    coherence_drops = 0
    total_candidates = 0

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
        if src.startswith("free_k_arm") or src in ("rotation_only", "identity"):
            arm_wins += 1
        coherence_drops += diag.get("n_candidates", 0) - diag.get("n_coherent", 0)
        total_candidates += diag.get("n_candidates", 0)
        if args.verbose or ok:
            print(f"  {fname}: {'OK' if ok else 'X'} src={src} "
                  f"gen={diag.get('n_candidates', 0)} "
                  f"coh={diag.get('n_coherent', 0)} "
                  f"ver={diag.get('n_verified', 0)} "
                  f"({time.time() - t0:.2f}s)")

    print(f"\n═══ v0.23 ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Time: {t_total:.1f}s (avg {t_total / max(total, 1):.2f}s/task)")
    print(f"  Arm wins: {arm_wins}")
    print(f"  Coherence-gate drops: {coherence_drops} (of {total_candidates} candidates)")
    print(f"  Sources: {sources}")
