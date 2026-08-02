"""
run_pipeline_v03.py — v0.3 pipeline with pattern learner
==========================================================

Runs the v0.3 pipeline that combines:
  1. The v0.2 Φ-grammar + NRCI ranker (symbolic search)
  2. The v0.3 PatternLearner (learn-on-the-fly from train pairs)

The two approaches are run in parallel and the learner's prediction is
preferred when it produces a train-pass result; otherwise the v0.2
ranker's top-1 is used.

This mirrors the GLM's own architecture: the substrate (v0.2) provides
the symbolic search, while the ContinuousLearner (v0.3) provides the
learned-pattern shortcut.

Usage:
    python3 run_pipeline_v03.py --synthetic
    python3 run_pipeline_v03.py path/to/task.json
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import time
import sys, os

# Make packages importable
_PKG_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import ARCTask, Grid, load_task, TrainPair, TestInput
from encoder import encode_task
from grammar import generate_candidates
from ranker import Ranker, RankResult
from learner import PatternLearner
from run_pipeline import run_pipeline, PipelineReport, SYNTHETIC_TASKS


# ══════════════════════════════════════════════════════════════════════════════
# v0.3 PIPELINE REPORT
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class V03PipelineReport:
    """Combined report from v0.3 pipeline (symbolic + learner)."""
    task_name: str
    # v0.2 symbolic results
    v02_report: Optional[PipelineReport] = None
    # v0.3 learner results
    learner_pattern_type: str = "unknown"
    learner_summary: str = ""
    learner_predicted: Optional[Grid] = None
    learner_train_pass: bool = False  # does learner's prediction match all train pairs?
    # Final decision
    final_prediction: Optional[Grid] = None
    final_source: str = "none"  # "learner" or "symbolic" or "fallback"
    final_correct: Optional[bool] = None

    def summary(self) -> str:
        lines = [
            f"═══ v0.3 Pipeline Report: {self.task_name} ═══",
            f"",
            f"── Pattern Learner ──",
            f"  pattern type:      {self.learner_pattern_type}",
            f"  train-pass:        {self.learner_train_pass}",
            f"  predicted:         {self.learner_predicted is not None}",
        ]
        if self.v02_report:
            lines.extend([
                f"",
                f"── v0.2 Symbolic Search ──",
                f"  candidates:        {self.v02_report.n_candidates}",
                f"  train-pass:        {self.v02_report.n_train_pass}",
                f"  SUBMIT:            {self.v02_report.n_submit}",
            ])
            if self.v02_report.top_results:
                top = self.v02_report.top_results[0]
                lines.append(f"  top-1:             {top.verdict} nrci={top.nrci_refined:.4f}")
        lines.extend([
            f"",
            f"── Final Decision ──",
            f"  source:            {self.final_source}",
            f"  correct:           {self.final_correct}",
        ])
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# v0.3 PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline_v03(task: ARCTask,
                      max_program_length: int = 2,
                      run_symbolic: bool = True,
                      check_ground_truth: bool = True) -> V03PipelineReport:
    """Run the v0.3 pipeline: learner + symbolic search in parallel.

    The learner's prediction is preferred if it passes the train filter.
    Otherwise the symbolic ranker's top-1 is used.
    """
    report = V03PipelineReport(task_name=task.name)

    # ── v0.3: Pattern Learner ──
    learner = PatternLearner()
    learner.learn_from_task(task)
    report.learner_pattern_type = learner.learned_pattern_type
    report.learner_summary = learner.summary()
    report.learner_predicted = learner.predict(task)

    # Check if learner's prediction passes the train filter
    if report.learner_predicted is not None:
        learner_program = None  # learner doesn't produce a Program, just a Grid
        # Verify: does the learner's transformation reproduce all train pairs?
        # We do this by checking if applying the learned pattern to each train input
        # produces the corresponding train output.
        # For recolour: apply the mapping to each train input
        # For geometric: apply the op to each train input
        # For composite: replay diffs
        report.learner_train_pass = _verify_learner_prediction(learner, task)

    # ── v0.2: Symbolic Search (optional) ──
    if run_symbolic:
        report.v02_report = run_pipeline(task,
                                          max_program_length=max_program_length,
                                          top_k=3,
                                          check_ground_truth=False)

    # ── Final Decision ──
    # Prefer learner if it passes train; otherwise use symbolic top-1
    if report.learner_train_pass and report.learner_predicted is not None:
        report.final_prediction = report.learner_predicted
        report.final_source = "learner"
    elif report.v02_report and report.v02_report.top_results:
        top = report.v02_report.top_results[0]
        if top.test_output is not None:
            report.final_prediction = top.test_output
            report.final_source = "symbolic"
    if report.final_prediction is None:
        report.final_prediction = task.test[0].input.copy()
        report.final_source = "fallback"

    # Ground-truth check
    if check_ground_truth and task.test[0].expected_output is not None:
        report.final_correct = (report.final_prediction == task.test[0].expected_output)

    return report


def _verify_learner_prediction(learner: PatternLearner, task: ARCTask) -> bool:
    """Verify that the learner's transformation reproduces all train pairs."""
    if learner.learned_pattern_type == "identity":
        # Identity: all train outputs should equal train inputs
        return all(p.input == p.output for p in task.train)
    if learner.learned_pattern_type == "recolour":
        # Apply the learned mapping to each train input, check it matches output
        from dsl import Operation, Ops
        op = Operation(Ops.RECOLOUR, params={"mapping": learner.learned_recolour_mapping})
        return all(op.apply(p.input) == p.output for p in task.train)
    if learner.learned_pattern_type in ("geometric", "gravity", "count"):
        if learner.learned_geometric_op:
            from dsl import Operation
            op = Operation(learner.learned_geometric_op)
            return all(op.apply(p.input) == p.output for p in task.train)
    if learner.learned_pattern_type == "composite":
        # Composite: replay diffs on each train input, check it matches output
        for i, pair in enumerate(task.train):
            diffs = learner.learned_cell_diffs[i] if i < len(learner.learned_cell_diffs) else []
            reconstructed = pair.input.copy()
            for r, c, old, new in diffs:
                if (0 <= r < reconstructed.height and 0 <= c < reconstructed.width
                        and reconstructed.cells[r][c] == old):
                    reconstructed.cells[r][c] = new
            if reconstructed != pair.output:
                return False
        return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    p = argparse.ArgumentParser(description="Run the v0.3 GLM-ARC pipeline (learner + symbolic)")
    p.add_argument("task_path", nargs="?")
    p.add_argument("--synthetic", action="store_true")
    p.add_argument("--which-synthetic", default="all",
                   choices=["all", "rotate_90", "recolour", "gravity", "count_fill"])
    p.add_argument("--max-program-length", type=int, default=2)
    p.add_argument("--no-symbolic", action="store_true",
                   help="Skip v0.2 symbolic search (learner only)")
    args = p.parse_args()

    if args.synthetic:
        which = ([args.which_synthetic] if args.which_synthetic != "all"
                 else list(SYNTHETIC_TASKS.keys()))
        print(f"═══ Running v0.3 on {len(which)} synthetic task(s) ═══\n")
        all_correct = True
        for name in which:
            task = SYNTHETIC_TASKS[name]()
            print(f"── Task: {name} ──")
            report = run_pipeline_v03(task,
                                       max_program_length=args.max_program_length,
                                       run_symbolic=not args.no_symbolic)
            print(report.summary())
            print()
            if report.final_correct is False:
                all_correct = False
        print(f"═══ Synthetic summary: {'all correct' if all_correct else 'some failed'} ═══")
    elif args.task_path:
        task = load_task(args.task_path)
        report = run_pipeline_v03(task,
                                   max_program_length=args.max_program_length,
                                   run_symbolic=not args.no_symbolic)
        print(report.summary())
    else:
        p.error("Either provide task_path or use --synthetic")


if __name__ == "__main__":
    main()
