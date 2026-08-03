"""
arc_enhanced_mind.py — Enhanced ARC Solver: Existing Toolkit + Data Object Substrate

Takes the existing consolidated_mind (9/50) and augments it with:
- Data Object encoding of grids (24-bit vectors)
- AND encoding for grid pairs (shared structure)
- NRCI-based candidate ranking
- Snap cost analysis
- Spatial Arithmetic metrics

The substrate doesn't replace the toolkit — it RANKS candidates.
"""

from __future__ import annotations
import os, sys, json, math, time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

SCRIPT_DIR = Path(__file__).resolve().parent
ARC_DIR = SCRIPT_DIR.parent / "glm_machine"
LTM_DIR = SCRIPT_DIR.parent / "long_term_memory"
sys.path.insert(0, str(ARC_DIR / "arc_loader"))
sys.path.insert(0, str(ARC_DIR))

from loader import ARCTask, Grid, load_task
from consolidated_mind import (
    perceive, interpret, generate_all_candidates,
    apply_to_train, grids_equal, Perception, Interpretation,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Data Object Encoding for ARC Grids
# ═══════════════════════════════════════════════════════════════════════════════

Y = 0.2646754304045269672

try:
    sys.path.insert(0, str(SCRIPT_DIR.parent / "data_object" / "scripts"))
    import ubp_unified_v5 as ubp
    GOLAY = ubp.GOLAY_ENGINE
    HAS_GOLAY = True
except Exception:
    HAS_GOLAY = False
    GOLAY = None


def grid_to_do(grid: Grid) -> List[int]:
    """Encode ARC grid as 24-bit Data Object."""
    h, w = grid.height, grid.width
    cells = grid.cells
    flat = [cells[r][c] for r in range(h) for c in range(w)]

    # Row 0 (Reality): top colours present
    colour_counts = Counter(flat)
    top6 = [c for c, _ in colour_counts.most_common(6)]
    row0 = [1 if i < len(top6) and top6[i] != 0 else 0 for i in range(6)]

    # Row 1 (Info): structural flags
    has_border = any(cells[0][c] != 0 for c in range(w)) or any(cells[h-1][c] != 0 for c in range(w))
    has_interior = any(cells[r][c] != 0 for r in range(1, h-1) for c in range(1, w-1)) if h > 2 and w > 2 else False
    h_sym = all(cells[r] == cells[h-1-r] for r in range(h//2))
    v_sym = all(cells[r][c] == cells[r][w-1-c] for r in range(h) for c in range(w//2))
    is_sq = h == w
    density = sum(1 for v in flat if v != 0) / max(len(flat), 1)
    row1 = [int(has_border), int(has_interior), int(density > 0.5), int(h_sym), int(v_sym), int(is_sq)]

    # Row 2 (Activation): density + colour count
    n_colours = len(set(flat)) - (1 if 0 in flat else 0)
    row2_val = min(n_colours * 8, 63)
    row2 = [(row2_val >> (5-i)) & 1 for i in range(6)]

    # Row 3 (Potential): size encoding
    row3_val = min(h * 4 + w, 63)
    row3 = [(row3_val >> (5-i)) & 1 for i in range(6)]

    return row0 + row1 + row2 + row3


def do_metrics(vec: List[int]) -> Dict:
    """Compute Data Object metrics."""
    hw = sum(vec)
    tax = hw * Y + sum(v*v for v in vec) / 8.0
    nrci = 10.0 / (10.0 + tax)

    snapped = golay_snap(vec) if HAS_GOLAY else vec
    bits_changed = sum(1 for i in range(24) if vec[i] != snapped[i])

    return {
        "hw": hw, "nrci": nrci, "tax": tax,
        "bits_changed": bits_changed,
    }


def golay_snap(vec: List[int]) -> List[int]:
    if HAS_GOLAY:
        s, _ = GOLAY.snap_to_codeword(vec)
        return s
    return vec[:]


def do_and(a: List[int], b: List[int]) -> List[int]:
    return [a[i] & b[i] for i in range(24)]


def do_xor(a: List[int], b: List[int]) -> List[int]:
    return [a[i] ^ b[i] for i in range(24)]


# ═══════════════════════════════════════════════════════════════════════════════
# Enhanced Solver: toolkit candidates + substrate ranking
# ═══════════════════════════════════════════════════════════════════════════════

def solve_task_enhanced(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Solve using existing toolkit + substrate ranking."""
    test = task.test[0]
    test_grid = test.input

    # Generate all candidates using existing mind
    interp = interpret(task)
    candidates = generate_all_candidates(task, interp)

    if not candidates:
        return None

    # Encode test input as Data Object
    test_do = grid_to_do(test_grid)
    test_metrics = do_metrics(test_do)

    # Verify each candidate on train pairs
    verified = []
    for cand_name, cand_grid in candidates:
        # Apply to train pairs
        all_match = True
        for pair in task.train:
            # Re-apply the same candidate generation to train input
            # (simplified: just check if candidate matches output)
            pass

        # Encode candidate as Data Object
        cand_do = grid_to_do(cand_grid)
        cand_metrics = do_metrics(cand_do)

        # AND encoding: shared structure between input and output
        and_vec = do_and(test_do, cand_do)
        and_metrics = do_metrics(and_vec)

        # XOR encoding: difference
        xor_vec = do_xor(test_do, cand_do)
        xor_metrics = do_metrics(xor_vec)

        # Verify on train pairs
        train_match = True
        for pair in task.train:
            pair_result = apply_to_train(task, cand_name, pair.input)
            if pair_result is None or not grids_equal(pair_result, pair.output):
                train_match = False
                break

        if train_match:
            verified.append({
                "name": cand_name,
                "grid": cand_grid,
                "cand_nrci": cand_metrics["nrci"],
                "and_nrci": and_metrics["nrci"],
                "and_hw": and_metrics["hw"],
                "xor_hw": xor_metrics["hw"],
                "delta_nrci": cand_metrics["nrci"] - test_metrics["nrci"],
            })

    if not verified:
        return None

    # Rank by substrate metrics
    # Priority: AND NRCI (shared structure) then delta NRCI (coherence change)
    verified.sort(key=lambda v: (-v["and_nrci"], -v["delta_nrci"]))

    best = verified[0]
    return best["grid"], best["name"], {
        "solver": best["name"],
        "input_nrci": test_metrics["nrci"],
        "solution_nrci": best["cand_nrci"],
        "and_nrci": best["and_nrci"],
        "and_hw": best["and_hw"],
        "xor_hw": best["xor_hw"],
        "delta_nrci": best["delta_nrci"],
        "n_candidates": len(candidates),
        "n_verified": len(verified),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("ENHANCED ARC MIND — Toolkit + Data Object Substrate")
    print("=" * 70)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Load long-term memory
    ltm_path = LTM_DIR / "learned_patterns.json"
    if ltm_path.exists():
        with open(ltm_path) as f:
            patterns = json.load(f)
        print(f"Long-term memory: {len(patterns['patterns'])} patterns loaded")
    print()

    data_dir = ARC_DIR / "data" / "training"
    tasks = sorted(f for f in os.listdir(data_dir) if f.endswith('.json'))

    solved = []
    results = []
    t0 = time.time()

    for tf in tasks:
        task_id = tf[:-5]
        task = load_task(os.path.join(data_dir, tf))

        result = solve_task_enhanced(task)

        if result is not None:
            grid, solver_name, metrics = result
            solved.append(task_id)
            status = "✓"
        else:
            metrics = {"solver": "none", "input_nrci": 0}
            status = "✗"

        results.append({"task_id": task_id, "solved": result is not None, **metrics})

        if result is not None:
            print(f"  {task_id}: {status} {metrics['solver']:25s} "
                  f"AND_NRCI={metrics.get('and_nrci', 0):.4f} "
                  f"ΔNRCI={metrics.get('delta_nrci', 0):+.4f}")

    elapsed = time.time() - t0

    # Summary
    print(f"\n{'='*70}")
    print(f"RESULT: {len(solved)}/{len(tasks)} solved ({100*len(solved)/len(tasks):.1f}%)")
    print(f"Time: {elapsed:.1f}s")
    print(f"{'='*70}")

    # Solver breakdown
    solver_counts = Counter(r["solver"] for r in results)
    print(f"\nSolvers:")
    for solver, count in solver_counts.most_common():
        n = sum(1 for r in results if r["solver"] == solver and r["solved"])
        print(f"  {solver:25s}: {count:3d} tried, {n:2d} solved")

    # Substrate analysis of solved tasks
    if solved:
        print(f"\nSolved task substrate analysis:")
        for r in results:
            if r["solved"]:
                print(f"  {r['task_id']}: AND_NRCI={r.get('and_nrci',0):.4f} "
                      f"AND_HW={r.get('and_hw',0):2d} "
                      f"XOR_HW={r.get('xor_hw',0):2d} "
                      f"ΔNRCI={r.get('delta_nrci',0):+.4f}")

    # Save
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_tasks": len(tasks),
        "n_solved": len(solved),
        "score_pct": round(100*len(solved)/len(tasks), 1),
        "time_s": round(elapsed, 1),
        "solved_tasks": solved,
        "results": results,
    }
    out_path = LTM_DIR / "arc_enhanced_run_001.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Saved to {out_path}")

    # Update training log
    log_path = LTM_DIR / "training_log.json"
    if log_path.exists():
        with open(log_path) as f:
            log = json.load(f)
    else:
        log = {"runs": []}
    log["runs"].append({
        "iteration": 14,
        "focus": "ARC-AGI enhanced mind (toolkit + substrate)",
        "n_solved": len(solved),
        "score_pct": round(100*len(solved)/len(tasks), 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)

    return output


if __name__ == "__main__":
    main()
