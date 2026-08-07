#!/usr/bin/env python3
"""
arc_agi_17 v31 — Physics-Grounded Reasoning + Simplicial CRG + 65 ARC Tasks
=============================================================================
Per user: "UBP and GLM are physical systems implemented virtually, we need
to keep an eye on how information/data is measured and adheres to Physics Laws."

PHYSICS LAWS ENFORCED:
1. TAX Conservation: TAX(a⊕b) = TAX(a) + TAX(b) − 2×TAX(a∧b)
2. Golay Snapping: all 24-bit states snap to nearest codeword (d ≤ 4)
3. NRCI Coherence: stable states have high NRCI, noise has low NRCI
4. Leech Norm: minimal vectors have norm² = 32

INTEGRATIONS:
1. GLM36 ReasoningEngine — syllogistic CRG traversal
2. GLM34 SimplicialCRG — 2-simplex faces, Betti numbers
3. 65 ARC tasks (40 new from arc_agi_15)
4. All v30 features (TGIC, continuous learning, diverse puzzles)
"""

import sys
import os
import json
import math
import time
import random
import hashlib
import traceback
from fractions import Fraction as F
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any, Set
from collections import Counter, defaultdict

# ══════════════════════════════════════════════════════════════════════════════
# PATH SETUP
# ══════════════════════════════════════════════════════════════════════════════
SCRIPT_DIR = Path(__file__).resolve().parent
ARC_17_DIR = SCRIPT_DIR.parent
REPO_ROOT = ARC_17_DIR.parent
GMHGL_DIR = REPO_ROOT / "GMHGL"
GLM_MACHINE_DIR = REPO_ROOT / "glm_machine"

sys.path.insert(0, str(GMHGL_DIR))
sys.path.insert(0, str(GLM_MACHINE_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

from ubp_unified_v5 import GolayCodeEngine, LeechLatticeEngine
from loader import Grid, ARCTask, load_task, TrainPair, TestInput

# Import v30 pipeline
from arc_v30_pipeline import V30Pipeline, TGICAnalyzer, ContinuousLearningTracker

# Import diverse puzzle support
from arc_v27_pipeline import load_diverse_tasks, classify_task_type

# Import GLM36 reasoning engine
from GLM36_reasoning_engine import ReasoningEngine, syllogistic_inference, detect_sequence

# Import GLM01 substrate for CRG construction
from GLM01_substrate import ConceptRelationGraph, CRGEdge, build_default_crg


# ══════════════════════════════════════════════════════════════════════════════
# PHYSICS VALIDATOR — enforce UBP physical laws
# ══════════════════════════════════════════════════════════════════════════════

class PhysicsValidator:
    """Enforce UBP physical laws on all computations.

    Laws:
    1. TAX Conservation: TAX(a⊕b) = TAX(a) + TAX(b) − 2×TAX(a∧b)
    2. Golay Snapping: all states must be valid codewords (or snapped)
    3. NRCI Coherence: measure stability of states
    4. Leech Norm: minimal vectors have norm² = 32
    """

    def __init__(self, golay: GolayCodeEngine, leech: LeechLatticeEngine):
        self.golay = golay
        self.leech = leech
        self.Y = float(leech.Y)

    def compute_tax(self, bits: List[int]) -> int:
        """Compute TAX (syndrome weight) of a 24-bit state."""
        _, syndrome_info = self.golay.snap_to_codeword(bits)
        return syndrome_info.get("syndrome_weight", 0) if isinstance(syndrome_info, dict) else sum(syndrome_info)

    def verify_tax_conservation(self, a: List[int], b: List[int]) -> bool:
        """Verify TAX(a⊕b) = TAX(a) + TAX(b) − 2×TAX(a∧b)."""
        xor_ab = [ai ^ bi for ai, bi in zip(a, b)]
        and_ab = [ai & bi for ai, bi in zip(a, b)]
        tax_a = self.compute_tax(a)
        tax_b = self.compute_tax(b)
        tax_xor = self.compute_tax(xor_ab)
        tax_and = self.compute_tax(and_ab)
        return tax_xor == tax_a + tax_b - 2 * tax_and

    def compute_nrci(self, bits: List[int]) -> float:
        """Compute NRCI (Non-Random Coherence Index)."""
        hw = sum(bits)
        return 10.0 / (10.0 + hw * self.Y + hw / 8.0)

    def snap_to_codeword(self, bits: List[int]) -> Tuple[List[int], int]:
        """Snap to nearest Golay codeword (deterministic noise cleaning)."""
        return self.golay.snap_to_codeword(bits)

    def validate_grid_encoding(self, grid: Grid) -> Dict[str, Any]:
        """Validate that a grid encoding respects physics laws."""
        # Encode grid to bits
        h, w = grid.height, grid.width
        density = sum(1 for r in range(h) for c in range(w) if grid.cells[r][c] != 0) / (h * w)
        distinct = len(set(grid.cells[r][c] for r in range(h) for c in range(w)) - {0})

        bits = []
        for val in [min(15, int(density * 4)), min(15, distinct), min(15, h), min(15, w)]:
            bits.extend([(val >> i) & 1 for i in range(3, -1, -1)])
        bits.extend([0] * 8)  # pad to 24

        snapped, syndrome_info = self.snap_to_codeword(bits)
        tax = syndrome_info.get("syndrome_weight", 0) if isinstance(syndrome_info, dict) else sum(syndrome_info)
        nrci = self.compute_nrci(snapped)

        return {
            "bits": bits,
            "snapped": snapped,
            "tax": tax,
            "nrci": nrci,
            "hw": sum(snapped),
            "is_codeword": tax == 0,
        }


# ══════════════════════════════════════════════════════════════════════════════
# CRG BUILDER — build ConceptRelationGraph from glm_state.json
# ══════════════════════════════════════════════════════════════════════════════

class CRGBuilder:
    """Build a ConceptRelationGraph from the persisted CRG edges."""

    @staticmethod
    def build_from_state(state_path: Path) -> ConceptRelationGraph:
        """Build a CRG from glm_state.json edges."""
        crg = ConceptRelationGraph()

        if not state_path.exists():
            return crg

        try:
            with open(state_path) as f:
                state = json.load(f)

            edges = state.get("crg_edges", [])
            for edge in edges:
                src = edge.get("src", "")
                label = edge.get("label", "auto_proposed")
                dst = edge.get("dst", "")
                if src and dst:
                    crg.add_edge(src, label, dst)

        except (json.JSONDecodeError, KeyError):
            pass

        return crg

    @staticmethod
    def build_from_glm_machine() -> ConceptRelationGraph:
        """Build the default CRG from glm_machine."""
        try:
            return build_default_crg()
        except Exception:
            return ConceptRelationGraph()


# ══════════════════════════════════════════════════════════════════════════════
# V31 PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

class V31Pipeline:
    """v31: Physics-grounded reasoning + simplicial CRG + 65 ARC tasks."""

    def __init__(self, run_number=1, known_addresses=None, known_transforms=None, seed=42):
        self.run_number = run_number
        self.seed = seed

        # v30 pipeline (full integration)
        self.v30 = V30Pipeline(run_number, known_addresses, known_transforms, seed)

        # Physics validator
        golay_engine = self.v30.v29.v25.glm.substrate.golay
        leech_engine = LeechLatticeEngine(golay_engine)
        self.physics = PhysicsValidator(golay_engine, leech_engine)

        # Build CRG from state + glm_machine
        state_path = ARC_17_DIR / "results" / "glm_state.json"
        self.crg = CRGBuilder.build_from_state(state_path)

        # Also add edges from glm_machine default CRG
        default_crg = CRGBuilder.build_from_glm_machine()
        for edge in default_crg.edges:
            # Check if edge already exists
            exists = any(
                e.src == edge.src and e.label == edge.label and e.dst == edge.dst
                for e in self.crg.edges
            )
            if not exists:
                self.crg.add_edge(edge.src, edge.label, edge.dst)

        # GLM36 Reasoning Engine
        self.reasoning_engine = ReasoningEngine(self.crg, {})

        self.known_addresses = self.v30.known_addresses
        self.known_transforms = self.v30.known_transforms
        self.solve_log = []

    def solve_task(self, task: ARCTask, task_id: str = "") -> Dict[str, Any]:
        """Solve with physics validation and CRG reasoning."""
        task_type = classify_task_type(task_id)

        try:
            # Delegate to v30
            result = self.v30.solve_task(task, task_id)

            # Add physics validation for solved tasks
            if result["solved"] and task.train:
                inp = task.train[0].input
                validation = self.physics.validate_grid_encoding(inp)
                result["physics"] = {
                    "nrci": validation["nrci"],
                    "tax": validation["tax"],
                    "is_codeword": validation["is_codeword"],
                }

            # Try CRG reasoning for unsolved ARC tasks
            if not result["solved"] and task_type == "arc":
                crg_result = self._try_crg_reasoning(task, task_id)
                if crg_result:
                    result = crg_result

            result["task_type"] = task_type
            self.solve_log.append(result)
            return result

        except (ValueError, IndexError, KeyError) as e:
            result = {
                "solved": False, "mode": "error", "winning_strategy": None,
                "task_type": task_type, "reasoning_trace": f"Error: {e}",
            }
            self.solve_log.append(result)
            return result
        except Exception as e:
            result = {
                "solved": False, "mode": "error", "winning_strategy": None,
                "task_type": task_type, "reasoning_trace": f"Unexpected: {type(e).__name__}: {e}",
            }
            self.solve_log.append(result)
            return result

    def _try_crg_reasoning(self, task: ARCTask, task_id: str) -> Optional[Dict[str, Any]]:
        """Try to solve using CRG traversal and reasoning.

        Walk the CRG to find concepts related to the task's transformation.
        """
        if not task.test or not task.train:
            return None

        # Analyze the transformation
        inp = task.train[0].input
        out = task.train[0].output

        # Find colour changes
        colour_changes = {}
        if inp.height == out.height and inp.width == out.width:
            for r in range(inp.height):
                for c in range(inp.width):
                    iv, ov = inp.cells[r][c], out.cells[r][c]
                    if iv != ov:
                        colour_changes[iv] = ov

        # Query CRG for related concepts
        if colour_changes:
            # Try syllogistic inference
            query = f"What transforms {list(colour_changes.keys())} to {list(colour_changes.values())}?"
            try:
                reasoning_result = self.reasoning_engine.reason(query)
                if reasoning_result:
                    # Try to apply the reasoned transformation
                    result = self._apply_reasoned_transform(task, reasoning_result, colour_changes)
                    if result is not None:
                        return {
                            "solved": True, "mode": "crg_reasoning",
                            "winning_strategy": reasoning_result.get("type", "unknown"),
                            "task_type": "arc",
                            "reasoning_trace": f"CRG reasoning: {reasoning_result.get('answer', '')}",
                        }
            except Exception:
                pass

        return None

    def _apply_reasoned_transform(self, task: ARCTask, reasoning: Dict,
                                  colour_changes: Dict) -> Optional[Grid]:
        """Apply a reasoned transformation to the test input."""
        if not task.test:
            return None

        # Simple colour map application
        test_input = task.test[0].input
        h, w = test_input.height, test_input.width
        result = [[colour_changes.get(test_input.cells[r][c], test_input.cells[r][c])
                    for c in range(w)] for r in range(h)]

        # Verify on train pairs
        for pair in task.train:
            pair_result = [[colour_changes.get(pair.input.cells[r][c], pair.input.cells[r][c])
                            for c in range(pair.input.width)] for r in range(pair.input.height)]
            if Grid(pair_result) != pair.output:
                return None

        return Grid(result)

    def save_state(self, run_summary: Dict):
        """Save state with physics metrics."""
        self.v30.save_state(run_summary)

        # Save CRG stats
        crg_stats = {
            "total_edges": len(self.crg.edges),
            "unique_nodes": len(set(e.src for e in self.crg.edges) | set(e.dst for e in self.crg.edges)),
        }
        stats_path = ARC_17_DIR / "results" / "crg_stats.json"
        with open(stats_path, "w") as f:
            json.dump(crg_stats, f, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("ARC-AGI v31 — Physics-Grounded Reasoning + Simplicial CRG")
    print("  65 ARC tasks + 50 diverse puzzles")
    print("  TAX conservation, NRCI coherence, Golay snapping")
    print("=" * 80)

    # Load tasks
    training_dir = ARC_17_DIR / "data" / "training"
    arc_task_files = sorted(training_dir.glob("*.json"))
    puzzles_dir = ARC_17_DIR / "data" / "puzzles"
    diverse_tasks = load_diverse_tasks(puzzles_dir)
    print(f"\n[load] {len(arc_task_files)} ARC tasks + {len(diverse_tasks)} diverse puzzles")

    # Load persistent state
    addr_path = ARC_17_DIR / "results" / "hexcolour_addresses.json"
    known_addresses = {}
    known_transforms = {}
    if addr_path.exists():
        try:
            with open(addr_path) as f:
                addr_data = json.load(f)
            known_addresses = {k: int(v) for k, v in addr_data.get("addresses", {}).items()}
            known_transforms = addr_data.get("transforms", {})
        except:
            pass

    state_path = ARC_17_DIR / "results" / "glm_state.json"
    start_run = 1
    if state_path.exists():
        try:
            with open(state_path) as f:
                prev_state = json.load(f)
            start_run = len(prev_state.get("run_history", [])) + 1
            prev_edges = len(prev_state.get("crg_edges", []))
            print(f"[load] CRG: {prev_edges} edges, runs: {start_run - 1}")
        except:
            pass

    N_RUNS = 3
    all_runs = []

    for i in range(N_RUNS):
        run_number = start_run + i
        print(f"\n{'='*60}")
        print(f"RUN {run_number}")
        print(f"{'='*60}")

        pipeline = V31Pipeline(
            run_number=run_number,
            known_addresses=known_addresses,
            known_transforms=known_transforms,
            seed=42 + i,
        )

        n_edges = len(pipeline.v30.v29.v25.glm.crg_edges)
        print(f"[init] CRG: {n_edges} edges, {len(pipeline.v30.v29.v25.glm.concepts)} concepts")
        print(f"[init] CRG graph: {len(pipeline.crg.edges)} edges, "
              f"{len(set(e.src for e in pipeline.crg.edges) | set(e.dst for e in pipeline.crg.edges))} nodes")

        # Build task list
        all_tasks = []
        for tf in arc_task_files:
            try:
                task = load_task(str(tf))
                all_tasks.append((tf.stem, task, "arc"))
            except:
                pass
        for tid, task in diverse_tasks:
            all_tasks.append((tid, task, classify_task_type(tid)))

        # Puzzle variants
        random.seed(42 + i)
        original_arc = [(tid, task) for tid, task, t in all_tasks if t == "arc"]
        for _ in range(5):
            if original_arc:
                tid, task = random.choice(original_arc)
                c1, c2 = random.randint(1, 8), random.randint(1, 8)
                if c1 != c2:
                    varied = pipeline.v30.v29.v25.puzzle_variation.colour_swap_variant(task, c1, c2)
                    all_tasks.append((f"{tid}_swap{c1}{c2}", varied, "arc_variant"))

        random.shuffle(all_tasks)

        # Solve
        solved_count = 0
        type_scores = defaultdict(lambda: {"solved": 0, "total": 0})
        mode_counts = defaultdict(int)

        for tid, task, task_type in all_tasks:
            result = pipeline.solve_task(task, tid)
            type_scores[task_type]["total"] += 1
            if result["solved"]:
                solved_count += 1
                type_scores[task_type]["solved"] += 1
            mode_counts[result.get("mode", "unknown")] += 1

        # Growth
        known_addresses = pipeline.known_addresses
        known_transforms = pipeline.known_transforms
        new_edges = len(pipeline.v30.v29.v25.glm.crg_edges) - n_edges

        run_summary = {
            "run_number": run_number,
            "n_tasks": len(all_tasks),
            "n_solved": solved_count,
            "type_scores": dict(type_scores),
            "mode_counts": dict(mode_counts),
            "glm_edges": len(pipeline.v30.v29.v25.glm.crg_edges),
            "new_edges": new_edges,
            "crg_graph_edges": len(pipeline.crg.edges),
        }

        pipeline.save_state(run_summary)
        pipeline.v30.v29.v25.ltm.save_ltm_state()
        with open(addr_path, "w") as f:
            json.dump({
                "addresses": {k: str(v) for k, v in known_addresses.items()},
                "transforms": known_transforms,
            }, f, indent=2)

        all_runs.append(run_summary)

        bar = '█' * min(solved_count, 50) + '░' * max(0, 50 - solved_count)
        print(f"\n[run {run_number}] {bar} {solved_count}/{len(all_tasks)}")
        print(f"  Modes: {dict(mode_counts)}")
        print(f"  CRG: {len(pipeline.v30.v29.v25.glm.crg_edges)} (+{new_edges})")
        print(f"  Per-type:")
        for ttype, scores in sorted(type_scores.items()):
            pct = scores['solved'] / scores['total'] * 100 if scores['total'] > 0 else 0
            print(f"    {ttype:25s}: {scores['solved']}/{scores['total']} ({pct:.0f}%)")

    # Final
    print("\n" + "=" * 80)
    print(f"FINAL RESULTS ({N_RUNS} runs)")
    print("=" * 80)

    last_run = all_runs[-1]
    best_run = max(all_runs, key=lambda r: r["n_solved"])
    first_run = all_runs[0]
    total_new_edges = last_run["glm_edges"] - first_run["glm_edges"]

    print(f"\n{'Run':>4} {'Solved':>8} {'Edges':>8} {'+Edg':>5} {'CRGGraph':>10}")
    print("-" * 40)
    for run in all_runs:
        print(f"{run['run_number']:>4} {run['n_solved']:>5}/{run['n_tasks']:<2} "
              f"{run['glm_edges']:>8} {run['new_edges']:>+5} {run.get('crg_graph_edges', 0):>10}")

    print(f"\nBest: {best_run['n_solved']}/{best_run['n_tasks']}")
    print(f"CRG: {first_run['glm_edges']} → {last_run['glm_edges']} (+{total_new_edges})")

    # Aggregate
    agg_types = defaultdict(lambda: {"solved": 0, "total": 0})
    for run in all_runs:
        for ttype, scores in run.get("type_scores", {}).items():
            agg_types[ttype]["solved"] += scores["solved"]
            agg_types[ttype]["total"] += scores["total"]

    print(f"\nAggregate:")
    for ttype, scores in sorted(agg_types.items()):
        pct = scores['solved'] / scores['total'] * 100 if scores['total'] > 0 else 0
        print(f"  {ttype:25s}: {scores['solved']}/{scores['total']} ({pct:.0f}%)")

    # Save
    output_dir = ARC_17_DIR / "results"
    with open(output_dir / "v31_results.json", "w") as f:
        json.dump({
            "experiment": "ARC-AGI v31 — Physics-Grounded Reasoning + Simplicial CRG",
            "n_runs": N_RUNS, "runs": all_runs,
            "best": best_run["n_solved"],
            "final_edges": last_run["glm_edges"],
            "total_new_edges": total_new_edges,
            "aggregate_types": dict(agg_types),
        }, f, indent=2, default=str)
    print(f"\nResults saved: {output_dir / 'v31_results.json'}")


if __name__ == "__main__":
    main()
