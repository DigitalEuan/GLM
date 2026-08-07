#!/usr/bin/env python3
"""
arc_agi_17 v26 — Sustained Growth Training
============================================
Per user: "Lets continue the growth with more training on different puzzles
to gain those CRG edges. My estimate is ~5000 entries per major epoch/threshold gain."

WHAT THIS VERSION DOES:
  1. Runs 10 training iterations on 42 ARC tasks
  2. Each run generates 5 puzzle variants (colour swap, rotation, scale, flip)
  3. The CRG auto-expands ~20 edges/run
  4. HexColour addresses accumulate
  5. All v25 features active (gap words, deliberative, imagination, crystallization, adversarial)
  6. Tracks growth toward the ~5000 edge threshold

The user's prediction: ~5000 CRG edges per major threshold gain.
Current: ~2800 edges. This run should push past 3000.

OUTPUTS:
  /home/z/my-project/download/arc_agi_17/results/v26_results.json
  /home/z/my-project/download/arc_agi_17/reports/v26_report.md
"""

import sys, os, json, math, time, random, hashlib, itertools
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any, Set
from collections import Counter, defaultdict
from fractions import Fraction as F

SCRIPT_DIR = Path(__file__).resolve().parent
ARC_17_DIR = SCRIPT_DIR.parent

sys.path.insert(0, str(Path("/home/z/my-project/scripts")))
from ubp_engine.ubp_unified_v5 import GolayCodeEngine, LeechLatticeEngine, BarnesWallEngine

sys.path.insert(0, str(SCRIPT_DIR))
from loader import Grid, ARCTask, load_task

# Import everything from v25 (growth, not rebuild)
from arc_v25_pipeline import V25Pipeline, V25GLMMind, ExtendedPuzzleVariation, GapWordDerivation, DeliberativeReasoning, AppliedImagination


def main():
    print("=" * 80)
    print("ARC-AGI v26 — Sustained Growth Training")
    print("  10 iterations × 42 tasks + 5 variants/run")
    print("  Target: push CRG past 3000 edges")
    print("=" * 80)

    training_dir = ARC_17_DIR / "data" / "training"
    task_files = sorted(training_dir.glob("*.json"))
    print(f"\n[load] Found {len(task_files)} ARC tasks")

    known_solved_ids = {"00dbd492", "1e0a9b12", "396d80d7", "45737921", "54d82841",
                        "575b1a71", "a85d4709", "ae58858e", "e48d4e1a"}

    addr_path = ARC_17_DIR / "results" / "hexcolour_addresses.json"
    known_addresses = {}
    known_transforms = {}
    if addr_path.exists():
        try:
            with open(addr_path) as f:
                addr_data = json.load(f)
            known_addresses = {k: int(v) for k, v in addr_data.get("addresses", {}).items()}
            known_transforms = addr_data.get("transforms", {})
        except: pass

    state_path = ARC_17_DIR / "results" / "glm_state.json"
    start_run = 1
    if state_path.exists():
        try:
            with open(state_path) as f:
                prev_state = json.load(f)
            start_run = len(prev_state.get("run_history", [])) + 1
        except: pass

    print(f"[load] Starting from run {start_run}")
    print(f"[load] Known addresses: {len(known_addresses)}")

    # Check current edge count
    if state_path.exists():
        with open(state_path) as f:
            prev_state = json.load(f)
        prev_edges = len(prev_state.get("crg_edges", []))
        print(f"[load] Previous CRG edges: {prev_edges}")
        print(f"[load] Edges to 5000 threshold: {5000 - prev_edges}")

    N_RUNS = 10
    all_runs = []

    for i in range(N_RUNS):
        run_number = start_run + i
        print(f"\n{'='*60}")
        print(f"RUN {run_number}")
        print(f"{'='*60}")

        pipeline = V25Pipeline(run_number=run_number, known_addresses=known_addresses,
                                known_transforms=known_transforms, seed=42 + i)
        n_edges = len(pipeline.glm.crg_edges)
        n_concepts = len(pipeline.glm.concepts)
        print(f"[init] GLM: {n_concepts} concepts, {n_edges} edges (target: 5000)")

        # Load tasks
        original_tasks = []
        for tf in task_files:
            try:
                original_tasks.append((tf.stem, load_task(str(tf))))
            except: pass

        # Puzzle variation (5 variants per run)
        varied_tasks = list(original_tasks)
        random.seed(42 + i)

        # 2 colour swaps
        for _ in range(2):
            if original_tasks:
                tid, task = random.choice(original_tasks)
                c1, c2 = random.randint(1, 8), random.randint(1, 8)
                if c1 != c2:
                    varied_tasks.append((f"{tid}_swap{c1}{c2}",
                                        pipeline.puzzle_variation.colour_swap_variant(task, c1, c2)))
        # 1 rotation
        if original_tasks:
            tid, task = random.choice(original_tasks)
            varied_tasks.append((f"{tid}_rot90", pipeline.puzzle_variation.rotate_variant(task)))
        # 1 scale
        if original_tasks:
            tid, task = random.choice(original_tasks)
            varied_tasks.append((f"{tid}_scale2x", pipeline.puzzle_variation.scaled_variant(task, 2)))
        # 1 flip
        if original_tasks:
            tid, task = random.choice(original_tasks)
            varied_tasks.append((f"{tid}_flipH", pipeline.puzzle_variation.flipped_variant(task)))

        random.shuffle(varied_tasks)
        n_variants = len(varied_tasks) - len(original_tasks)

        solved_count = 0; new_solves = 0
        mind_solves = 0; lattice_solves = 0; analogical_solves = 0; deliberative_solves = 0
        imagination_used = 0; gap_words_derived = 0

        for tid, task in varied_tasks:
            try:
                result = pipeline.solve_task(task, tid)
                if result["solved"]:
                    solved_count += 1
                    is_new = not any(x in tid for x in ["_swap", "_rot", "_scale", "_flip"]) and tid not in known_solved_ids
                    if is_new: new_solves += 1
                    mode = result["mode"]
                    if mode == "glm_mind": mind_solves += 1
                    elif mode == "lattice_perception": lattice_solves += 1
                    elif mode == "hexcolour_analogical": analogical_solves += 1
                    elif mode == "deliberative_reasoning": deliberative_solves += 1
                    trace = result.get("reasoning_trace", "")
                    if "imagination" in trace.lower(): imagination_used += 1
                    if "Derived" in trace or "gap_word" in trace.lower(): gap_words_derived += 1
            except: pass

        known_addresses = pipeline.known_addresses
        known_transforms = pipeline.known_transforms
        new_edges = len(pipeline.glm.crg_edges) - n_edges

        run_summary = {
            "run_number": run_number, "n_tasks": len(varied_tasks),
            "n_solved": solved_count, "new_solves": new_solves,
            "mind_solves": mind_solves, "lattice_solves": lattice_solves,
            "analogical_solves": analogical_solves, "deliberative_solves": deliberative_solves,
            "imagination_used": imagination_used, "gap_words_derived": gap_words_derived,
            "known_addresses": len(known_addresses),
            "glm_concepts": len(pipeline.glm.concepts),
            "glm_edges": len(pipeline.glm.crg_edges),
            "new_edges": new_edges,
            "n_variants": n_variants,
        }
        pipeline.glm.save_state(run_summary)
        pipeline.ltm.save_ltm_state()
        with open(addr_path, "w") as f:
            json.dump({"addresses": {k: str(v) for k, v in known_addresses.items()},
                       "transforms": known_transforms}, f, indent=2)

        all_runs.append(run_summary)

        edges_to_5000 = max(0, 5000 - len(pipeline.glm.crg_edges))
        bar = '█' * min(solved_count, 50) + '░' * max(0, 50 - solved_count)
        print(f"\n[run {run_number}] {bar} {solved_count}/{len(varied_tasks)}")
        print(f"  Lattice: {lattice_solves}, Mind: {mind_solves}, Deliberative: {deliberative_solves}, Analogical: {analogical_solves}")
        print(f"  Imagination: {imagination_used}, Gap words: {gap_words_derived}")
        print(f"  Edges: {len(pipeline.glm.crg_edges)} (+{new_edges}), Addresses: {len(known_addresses)}")
        print(f"  Edges to 5000 threshold: {edges_to_5000}")

    # Final
    print("\n" + "=" * 80)
    print(f"FINAL RESULTS ({N_RUNS} runs)")
    print("=" * 80)
    print(f"\n{'Run':>4} {'Solved':>8} {'Lat':>5} {'Mind':>5} {'Delib':>6} {'Imag':>5} {'Gap':>5} {'Edges':>8} {'+Edg':>5} {'Addr':>6} {'→5000':>7}")
    print("-" * 70)
    for run in all_runs:
        to_5k = max(0, 5000 - run["glm_edges"])
        print(f"{run['run_number']:>4} {run['n_solved']:>5}/{run['n_tasks']:<2} {run['lattice_solves']:>5} {run['mind_solves']:>5} "
              f"{run['deliberative_solves']:>6} {run['imagination_used']:>5} {run['gap_words_derived']:>5} "
              f"{run['glm_edges']:>8} {run['new_edges']:>+5} {run['known_addresses']:>6} {to_5k:>7}")

    last_run = all_runs[-1]
    best_run = max(all_runs, key=lambda r: r["n_solved"])
    first_run = all_runs[0]
    total_new_edges = last_run["glm_edges"] - first_run["glm_edges"]

    print(f"\nBest: {best_run['n_solved']}/{best_run['n_tasks']} (Run {best_run['run_number']})")
    print(f"Edges: {first_run['glm_edges']} → {last_run['glm_edges']} (+{total_new_edges})")
    print(f"Edges to 5000: {max(0, 5000 - last_run['glm_edges'])}")
    print(f"Addresses: {first_run['known_addresses']} → {last_run['known_addresses']} (+{last_run['known_addresses'] - first_run['known_addresses']})")

    # Score progression
    print(f"\nScore progression:")
    for run in all_runs:
        bar = '█' * min(run['n_solved'], 50) + '░' * max(0, 50 - run['n_solved'])
        print(f"  Run {run['run_number']:>3}: {bar} {run['n_solved']}/{run['n_tasks']}")

    # Edge growth chart
    print(f"\nCRG edge growth (target: 5000):")
    for run in all_runs:
        pct = run['glm_edges'] / 5000 * 100
        bar = '█' * int(pct / 2) + '░' * (50 - int(pct / 2))
        print(f"  Run {run['run_number']:>3}: {bar} {run['glm_edges']} ({pct:.1f}%)")

    # Save
    output_dir = ARC_17_DIR / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "v26_results.json", "w") as f:
        json.dump({"experiment": "ARC-AGI v26 — Sustained Growth", "n_runs": N_RUNS,
                   "runs": all_runs, "best": best_run["n_solved"],
                   "final_edges": last_run["glm_edges"], "total_new_edges": total_new_edges,
                   "edges_to_5000": max(0, 5000 - last_run["glm_edges"]),
                   "final_addresses": last_run["known_addresses"]}, f, indent=2, default=str)
    print(f"\nResults saved: {output_dir / 'v26_results.json'}")

    # Report
    report_dir = ARC_17_DIR / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    with open(report_dir / "v26_report.md", "w") as f:
        f.write(f"""# ARC-AGI v26 — Sustained Growth Training

**Date:** 2026-08-07
**Iterations:** {N_RUNS}
**Tasks:** {len(task_files)} original + 5 variants/run

## Growth Summary

| Metric | Start | End | Growth |
|---|---|---|---|
| CRG edges | {first_run['glm_edges']} | {last_run['glm_edges']} | +{total_new_edges} |
| HexColour addresses | {first_run['known_addresses']} | {last_run['known_addresses']} | +{last_run['known_addresses'] - first_run['known_addresses']} |
| Best score | {first_run['n_solved']}/{first_run['n_tasks']} | {best_run['n_solved']}/{best_run['n_tasks']} | +{best_run['n_solved'] - first_run['n_solved']} |
| Edges to 5000 | {5000 - first_run['glm_edges']} | {max(0, 5000 - last_run['glm_edges'])} | -{total_new_edges} |

## Results

| Run | Solved | Lattice | Mind | Deliberative | Imagination | Edges | +Edges | →5000 |
|---|---|---|---|---|---|---|---|---|
""")
        for run in all_runs:
            to_5k = max(0, 5000 - run["glm_edges"])
            f.write(f"| {run['run_number']} | {run['n_solved']}/{run['n_tasks']} | {run['lattice_solves']} | {run['mind_solves']} | {run['deliberative_solves']} | {run['imagination_used']} | {run['glm_edges']} | +{run['new_edges']} | {to_5k} |\n")
        f.write(f"""
### User's threshold prediction
The user estimates ~5000 CRG edges per major epoch/threshold gain.
Current: {last_run['glm_edges']} edges. Remaining to 5000: {max(0, 5000 - last_run['glm_edges'])}.
At ~{total_new_edges // N_RUNS} edges/run, that's ~{(max(0, 5000 - last_run['glm_edges'])) // max(total_new_edges // N_RUNS, 1)} more runs to reach 5000.
""")
    print(f"Report saved: {report_dir / 'v26_report.md'}")


if __name__ == "__main__":
    main()
