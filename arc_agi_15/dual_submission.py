"""
dual_submission.py — dual-output submission harness
=====================================================

Produces TWO outputs per task:
  1. ARC-AGI-3 compatible JSON (the accepted submission format)
  2. Full system output (the GLM's complete reasoning — Lingo expressions,
     CRG stats, NRCI coherence, geo_class analysis, Three Column check)

The full output is retained alongside the ARC JSON because it provides
the depth and insights needed to understand WHY the system made each
prediction. The ARC JSON is the "what"; the full output is the "why".

Usage:
    from dual_submission import DualSubmissionHarness

    harness = DualSubmissionHarness()
    result = harness.solve_task(task)
    print(result.arc_json)        # the accepted submission format
    print(result.full_output)     # the complete system reasoning
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import json
import time
import sys, os

_PKG_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import ARCTask, Grid, load_task
from generative import GenerativeTransformer, three_column_verify, extract_objects
from lingo import LingoTranslator, SpatialCalculator
from run_pipeline_v05 import run_pipeline_v05, V05PipelineReport
from encoder import encode_grid


# ══════════════════════════════════════════════════════════════════════════════
# FULL SYSTEM OUTPUT — the complete reasoning behind a prediction
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class FullSystemOutput:
    """The complete system output for a single task.

    This is the "why" behind the ARC JSON "what". It contains:
      - Task summary (palette, dimensions, object count)
      - Lingo chat session (the GLM's reasoning before solving)
      - CRG learning summary (learned transformations)
      - Lingo expression (the GLM's native description of the transform)
      - NRCI coherence analysis (per-object and per-grid)
      - Geo-class analysis (LDP structural fingerprints)
      - SRCC cycle state (self-referential computational cycle)
      - Bell number partition analysis (learning methods)
      - Three Column check (language + math + code alignment)
      - Spatial Arithmetic calculations (exact, no floats)
      - The predicted output grid
    """
    task_id: str
    task_summary: Dict[str, Any] = field(default_factory=dict)
    lingo_chat: List[Dict[str, Any]] = field(default_factory=list)
    crg_summary: Dict[str, Any] = field(default_factory=dict)
    lingo_expression: str = ""
    lingo_human: str = ""
    nrci_analysis: Dict[str, Any] = field(default_factory=dict)
    geo_class_analysis: List[Dict[str, Any]] = field(default_factory=list)
    srcc_state: Dict[str, Any] = field(default_factory=dict)
    bell_analysis: Dict[str, Any] = field(default_factory=dict)
    three_column: Dict[str, Any] = field(default_factory=dict)
    spatial_calculations: List[Dict[str, Any]] = field(default_factory=list)
    predicted_grid: Optional[List[List[int]]] = None
    prediction_source: str = ""
    transform_type: str = ""
    correct: Optional[bool] = None
    time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "task_id": self.task_id,
            "task_summary": self.task_summary,
            "lingo_chat": self.lingo_chat,
            "crg_summary": self.crg_summary,
            "lingo": {
                "expression": self.lingo_expression,
                "human": self.lingo_human,
            },
            "nrci_analysis": self.nrci_analysis,
            "geo_class_analysis": self.geo_class_analysis,
            "srcc_state": self.srcc_state,
            "bell_analysis": self.bell_analysis,
            "three_column": self.three_column,
            "spatial_calculations": self.spatial_calculations,
            "prediction": {
                "grid": self.predicted_grid,
                "source": self.prediction_source,
                "transform_type": self.transform_type,
                "correct": self.correct,
            },
            "time_sec": self.time_sec,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


# ══════════════════════════════════════════════════════════════════════════════
# DUAL SUBMISSION RESULT
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class DualSubmissionResult:
    """The result of solving a single task — both ARC JSON and full output."""
    task_id: str
    arc_output: List[List[int]]          # the ARC-AGI-3 compatible grid
    full_output: FullSystemOutput         # the complete system reasoning

    @property
    def arc_json(self) -> str:
        """The ARC-AGI-3 compatible JSON for this task."""
        return json.dumps(self.arc_output)

    def save(self, arc_path: str = None, full_path: str = None) -> None:
        """Save both outputs to files."""
        if arc_path:
            with open(arc_path, "w") as f:
                json.dump(self.arc_output, f)
        if full_path:
            with open(full_path, "w") as f:
                f.write(self.full_output.to_json())


# ══════════════════════════════════════════════════════════════════════════════
# DUAL SUBMISSION HARNESS
# ══════════════════════════════════════════════════════════════════════════════

class DualSubmissionHarness:
    """Solves ARC tasks and produces both ARC JSON and full system output.

    The ARC JSON is the accepted submission format (a grid of integers).
    The full system output retains all the GLM's reasoning — Lingo
    expressions, CRG stats, NRCI coherence, geo-class analysis — because
    that depth provides the insights needed to improve the system.
    """

    def __init__(self):
        self.translator = LingoTranslator()
        self.calculator = SpatialCalculator()

    def solve_task(self, task: ARCTask) -> DualSubmissionResult:
        """Solve a single task and produce dual output."""
        t0 = time.time()

        # Run the v0.5 generative pipeline
        report = run_pipeline_v05(task, check_ground_truth=True)

        # Build the full system output
        full = FullSystemOutput(
            task_id=task.name,
            time_sec=time.time() - t0,
        )

        # Task summary
        full.task_summary = {
            "train_pairs": len(task.train),
            "test_inputs": len(task.test),
            "input_shape": task.test[0].input.shape,
            "palette": sorted(task.test[0].input.palette()),
            "dominant_colour": task.test[0].input.dominant_colour(),
            "object_count": len(extract_objects(task.test[0].input)),
        }

        # Lingo chat (the GLM reasons about the task before solving)
        from lingo import chat_about_task
        transformer = GenerativeTransformer()
        transformer.learn_from_task(task)
        chat_session = chat_about_task(task, crg=transformer.crg)
        full.lingo_chat = chat_session.to_dict()["messages"]

        # CRG summary
        full.crg_summary = report.crg_stats

        # Lingo expression
        colour_mapping = transformer.crg.global_colour_mapping
        lingo_expr = self.translator.describe_transformation(
            report.transform_type,
            colour_mapping=colour_mapping if colour_mapping else None,
        )
        full.lingo_expression = lingo_expr.to_lingo_string()
        full.lingo_human = lingo_expr.to_human_string()

        # NRCI analysis (coherence measure, not discriminator)
        if report.predicted:
            _, enc_report = encode_grid(report.predicted)
            full.nrci_analysis = {
                "predicted_nrci_basic": enc_report.nrci_basic,
                "predicted_nrci_refined": enc_report.nrci_refined,
                "coherence_label": self.translator.describe_nrci(enc_report.nrci_refined),
                "manifested": enc_report.manifested,
            }

        # Geo-class analysis (LDP structural fingerprints)
        test_objects = extract_objects(task.test[0].input)
        for obj in test_objects[:10]:
            gc = self.translator.describe_geo_class(obj.cell_count)
            full.geo_class_analysis.append({
                "colour": obj.colour,
                "cell_count": obj.cell_count,
                "bbox": obj.bbox,
                "geo_class": gc,
            })

        # SRCC cycle state (self-referential computational cycle)
        from generative import SRCCCycle
        if report.predicted:
            _, enc_report = encode_grid(report.predicted)
            srcc = SRCCCycle()
            srcc_result = srcc.run(enc_report.snapped_codeword, max_iterations=3)
            full.srcc_state = {
                "k": srcc_result.k,
                "k_mirror": srcc_result.k_mirror,
                "nrci": srcc_result.nrci,
                "in_band": srcc_result.in_band,
                "iteration": srcc_result.iteration,
                "converged": srcc_result.converged,
                "monad_laws_satisfied": srcc.verify_monad_laws()["all_satisfied"],
            }

        # Bell number partition analysis
        from generative import analyse_object_partitions
        full.bell_analysis = analyse_object_partitions(len(test_objects))

        # Three Column check
        if report.three_column:
            full.three_column = {
                "language": report.three_column.language,
                "math_nrci": report.three_column.math_nrci,
                "code_pass": report.three_column.code_pass,
                "aligned": report.three_column.aligned,
            }

        # Spatial calculations
        if colour_mapping:
            for old, new in list(colour_mapping.items())[:3]:
                calc = {
                    "operation": "recolour",
                    "input": old,
                    "output": new,
                    "method": "Spatial Arithmetic CHARGE_SWAP",
                }
                full.spatial_calculations.append(calc)

        # Predicted grid
        full.predicted_grid = report.predicted.cells if report.predicted else None
        full.prediction_source = report.prediction_source
        full.transform_type = report.transform_type
        full.correct = report.correct

        # ARC output (the accepted format — just the grid)
        arc_output = report.predicted.cells if report.predicted else [[0]]

        return DualSubmissionResult(
            task_id=task.name,
            arc_output=arc_output,
            full_output=full,
        )

    def solve_batch(self, tasks: Dict[str, ARCTask]) -> Tuple[Dict[str, list], Dict[str, Any]]:
        """Solve a batch of tasks. Returns (arc_json, full_json).

        arc_json: {task_id: grid} — the ARC submission format
        full_json: {task_id: full_output} — the complete system reasoning
        """
        arc_results: Dict[str, list] = {}
        full_results: Dict[str, Any] = {}

        for task_id, task in tasks.items():
            result = self.solve_task(task)
            arc_results[task_id] = result.arc_output
            full_results[task_id] = result.full_output.to_dict()

        return arc_results, full_results

    def save_batch(self, tasks: Dict[str, ARCTask],
                   arc_path: str, full_path: str) -> None:
        """Solve a batch and save both outputs to files."""
        arc_results, full_results = self.solve_batch(tasks)
        with open(arc_path, "w") as f:
            json.dump(arc_results, f, indent=2)
        with open(full_path, "w") as f:
            json.dump(full_results, f, indent=2, default=str)


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    p = argparse.ArgumentParser(description="Dual-output ARC submission harness")
    p.add_argument("task_dir", help="Directory of ARC task JSON files")
    p.add_argument("--max-tasks", type=int, default=None)
    p.add_argument("--arc-output", default="submission_arc.json",
                   help="Path for the ARC-format submission JSON")
    p.add_argument("--full-output", default="submission_full.json",
                   help="Path for the full system output JSON")
    args = p.parse_args()

    harness = DualSubmissionHarness()

    task_files = sorted(f for f in os.listdir(args.task_dir) if f.endswith(".json"))
    if args.max_tasks:
        task_files = task_files[:args.max_tasks]

    print(f"═══ Dual Submission: {len(task_files)} tasks ═══\n")

    tasks: Dict[str, ARCTask] = {}
    for fname in task_files:
        task_id = os.path.splitext(fname)[0]
        task = load_task(os.path.join(args.task_dir, fname), name=task_id)
        tasks[task_id] = task

    arc_results, full_results = harness.solve_batch(tasks)

    # Save both outputs
    with open(args.arc_output, "w") as f:
        json.dump(arc_results, f, indent=2)
    with open(args.full_output, "w") as f:
        json.dump(full_results, f, indent=2, default=str)

    # Print summary
    solved = sum(1 for r in full_results.values()
                 if r.get("prediction", {}).get("correct") is True)
    total = len(full_results)
    print(f"\n═══ Results ═══")
    print(f"  Solved: {solved}/{total} ({solved/max(total,1):.1%})")
    print(f"  ARC submission:   {args.arc_output}")
    print(f"  Full system output: {args.full_output}")

    # Print per-task summary
    print(f"\n  Per-task summary:")
    for task_id, result in full_results.items():
        pred = result.get("prediction", {})
        lingo = result.get("lingo", {})
        nrci = result.get("nrci_analysis", {})
        status = "✓" if pred.get("correct") else "✗"
        print(f"    {status} {task_id}: {pred.get('source')}/{pred.get('transform_type')} "
              f"| {lingo.get('human', '?')} "
              f"| NRCI={nrci.get('coherence_label', '?')[:30]}")


if __name__ == "__main__":
    main()
