"""
run_pipeline_v05.py — v0.5 generative pipeline
================================================

The v0.5 pipeline implements the reframe:
  Grid = Sentence, Objects = Words, Transformations = Generated

Pipeline:
  1. Decompose each train pair's input+output into objects (words)
  2. Learn object-to-object transformations in the ObjectCRG
  3. Decompose the test input into objects
  4. For each test object, find the learned CRG transformation (GENERATIVE)
  5. If no CRG hit, generate via Φ-grammar (GENERATIVE)
  6. If no grammar hit, fall back to DSL vocabulary (the GLM's lingo)
  7. Apply Three Column Thinking: language + math + code must align
  8. Reassemble transformed objects into the output grid

Usage:
    python3 run_pipeline_v05.py --synthetic
    python3 run_pipeline_v05.py data/training/1e0a9b12.json
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import time
import sys, os

_PKG_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import ARCTask, Grid, load_task, TrainPair, TestInput
from generative import (
    GenerativeTransformer, ThreeColumnCheck, three_column_verify,
    extract_objects, grid_to_sentence, ObjectCRG,
)
from run_pipeline import SYNTHETIC_TASKS


# ══════════════════════════════════════════════════════════════════════════════
# v0.5 PIPELINE REPORT
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class V05PipelineReport:
    """Report from the v0.5 generative pipeline."""
    task_name: str
    # CRG learning
    crg_stats: Dict[str, Any] = field(default_factory=dict)
    # Prediction
    prediction_source: str = "none"        # "crg", "phi_grammar", "dsl_vocabulary", "fallback"
    transform_type: str = "unknown"
    predicted: Optional[Grid] = None
    # Three Column check
    three_column: Optional[ThreeColumnCheck] = None
    # Ground truth
    correct: Optional[bool] = None
    # Timing
    time_sec: float = 0.0

    def summary(self) -> str:
        lines = [
            f"═══ v0.5 Pipeline Report: {self.task_name} ═══",
            f"",
            f"── CRG Learning ──",
        ]
        for k, v in self.crg_stats.items():
            lines.append(f"  {k}: {v}")
        lines.extend([
            f"",
            f"── Prediction ──",
            f"  source:          {self.prediction_source}",
            f"  transform type:  {self.transform_type}",
            f"  predicted:       {self.predicted is not None}",
        ])
        if self.three_column:
            lines.extend([
                f"",
                f"── Three Column Check ──",
                f"  language:        {self.three_column.language}",
                f"  math (NRCI):     {self.three_column.math_nrci:.4f}",
                f"  code (train):    {self.three_column.code_pass}",
                f"  aligned:         {self.three_column.aligned}",
            ])
        lines.extend([
            f"",
            f"── Result ──",
            f"  correct:         {self.correct}",
            f"  time:            {self.time_sec:.2f}s",
        ])
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# v0.5 PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline_v05(task: ARCTask,
                      check_ground_truth: bool = True) -> V05PipelineReport:
    """Run the v0.5 generative pipeline on a single task."""
    report = V05PipelineReport(task_name=task.name)
    t0 = time.time()

    # Step 1-2: Learn from train pairs
    transformer = GenerativeTransformer()
    transformer.learn_from_task(task)
    report.crg_stats = transformer.crg.stats()

    # Step 3-6: Predict
    predicted = transformer.predict(task)
    report.predicted = predicted

    # Determine the source
    if predicted is not None:
        # Check which path produced the prediction
        dominant = transformer.crg.dominant_transform_type()
        if dominant != "unknown" and transformer.crg.all_edges:
            report.prediction_source = "crg"
            report.transform_type = dominant
        else:
            report.prediction_source = "phi_grammar"
            report.transform_type = "generated"

    if predicted is None:
        report.prediction_source = "fallback"
        report.predicted = task.test[0].input.copy()

    # Step 7: Three Column verification
    colour_mapping = transformer.crg.global_colour_mapping
    report.three_column = three_column_verify(
        task, report.predicted,
        transform_type=report.transform_type,
        colour_mapping=colour_mapping if colour_mapping else None,
    )

    # Ground truth check
    if check_ground_truth and task.test[0].expected_output is not None:
        report.correct = (report.predicted == task.test[0].expected_output)

    report.time_sec = time.time() - t0
    return report


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    p = argparse.ArgumentParser(description="Run the v0.5 generative GLM-ARC pipeline")
    p.add_argument("task_path", nargs="?")
    p.add_argument("--synthetic", action="store_true")
    p.add_argument("--which-synthetic", default="all",
                   choices=["all", "rotate_90", "recolour", "gravity", "count_fill"])
    p.add_argument("--batch", default=None,
                   help="Directory of ARC tasks to run in batch")
    p.add_argument("--max-tasks", type=int, default=None)
    args = p.parse_args()

    if args.batch:
        task_files = sorted(f for f in os.listdir(args.batch) if f.endswith(".json"))
        if args.max_tasks:
            task_files = task_files[:args.max_tasks]
        print(f"═══ v0.5 Batch Run on {len(task_files)} tasks ═══\n")
        solved = 0
        total = 0
        for fname in task_files:
            task = load_task(os.path.join(args.batch, fname),
                             name=os.path.splitext(fname)[0])
            if task.test[0].expected_output is None:
                continue
            total += 1
            report = run_pipeline_v05(task)
            if report.correct:
                solved += 1
                print(f"  ✓ {task.name}: {report.prediction_source}/{report.transform_type}")
            else:
                print(f"  ✗ {task.name}: {report.prediction_source}/{report.transform_type}")
        print(f"\n═══ Solved: {solved}/{total} ({solved/max(total,1):.1%}) ═══")

    elif args.synthetic:
        which = ([args.which_synthetic] if args.which_synthetic != "all"
                 else list(SYNTHETIC_TASKS.keys()))
        print(f"═══ Running v0.5 on {len(which)} synthetic task(s) ═══\n")
        all_correct = True
        for name in which:
            task = SYNTHETIC_TASKS[name]()
            print(f"── Task: {name} ──")
            report = run_pipeline_v05(task)
            print(report.summary())
            print()
            if report.correct is False:
                all_correct = False
        print(f"═══ Synthetic summary: {'all correct' if all_correct else 'some failed'} ═══")

    elif args.task_path:
        task = load_task(args.task_path)
        report = run_pipeline_v05(task)
        print(report.summary())
    else:
        p.error("Either provide task_path, --batch, or --synthetic")


if __name__ == "__main__":
    main()
