"""
submission_harness.py — ARC-AGI-3 submission harness
=====================================================

Wraps the pipeline to produce ARC-AGI-3-compatible JSON submissions and
run the pipeline on a batch of tasks.

Per the ARC-AGI-3 documentation at docs.arcprize.org, a submission is a
single JSON object mapping task_id → predicted_output_grid. The evaluation
harness performs an exact-match comparison; partial credit is not awarded.
Three submissions are allowed per task.

Usage:
    from submission_harness import SubmissionHarness

    harness = SubmissionHarness()
    submission = harness.solve_task(task)  # returns predicted Grid
    json_str = harness.format_submission({"task_id_1": task1, "task_id_2": task2})
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json
import time
import sys, os

# Make packages importable
_PKG_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import ARCTask, Grid, load_task
from encoder import encode_task
from grammar import PhiGrammar, generate_candidates
from ranker import Ranker, RankResult, RandomRanker
from run_pipeline import run_pipeline, PipelineReport


# ══════════════════════════════════════════════════════════════════════════════
# SUBMISSION HARNESS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SubmissionHarness:
    """Wraps the pipeline to produce ARC-AGI-3-compatible submissions.

    Parameters
    ----------
    max_program_length : int
        Max operations per candidate program. Default 2.
    top_k : int
        Number of top candidates to consider. Default 3.
    use_random_fallback : bool
        If True (default), when no train-pass candidate is found, submit
        a copy of the test input as a fallback (better than nothing for
        tasks where the rule is "identity").
    """
    max_program_length: int = 2
    top_k: int = 3
    use_random_fallback: bool = True

    def solve_task(self, task: ARCTask) -> Tuple[Optional[Grid], PipelineReport]:
        """Solve a single task. Returns (predicted_output, report).

        The predicted output is the top-1 candidate's output, or None if
        no candidate passes the empirical-adequacy filter and no fallback
        is available.
        """
        report = run_pipeline(task,
                              max_program_length=self.max_program_length,
                              top_k=self.top_k,
                              check_ground_truth=False)

        if report.top_results:
            return report.top_results[0].test_output, report
        if self.use_random_fallback:
            return task.test[0].input.copy(), report
        return None, report

    def format_submission(self, tasks: Dict[str, ARCTask]) -> str:
        """Solve all tasks and return an ARC-AGI-3-compatible JSON string.

        The output format is:
            {
                "task_id_1": [[...], [...], ...],  # predicted output grid
                "task_id_2": [[...], ...],
                ...
            }
        """
        submission: Dict[str, list] = {}
        for task_id, task in tasks.items():
            predicted, _ = self.solve_task(task)
            if predicted is not None:
                submission[task_id] = predicted.cells
            else:
                # Empty grid as fallback
                submission[task_id] = [[0]]
        return json.dumps(submission, indent=2)

    def save_submission(self, tasks: Dict[str, ARCTask], path: str) -> None:
        """Solve all tasks and save the submission to a JSON file."""
        submission_str = self.format_submission(tasks)
        with open(path, "w") as f:
            f.write(submission_str)


# ══════════════════════════════════════════════════════════════════════════════
# BATCH RUNNER — evaluate on a directory of ARC tasks
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class BatchReport:
    """Aggregate report across a batch of tasks."""
    total_tasks: int = 0
    solved: int = 0                  # tasks where top-1 matches expected output
    train_pass_found: int = 0        # tasks where ≥1 candidate passed train filter
    no_train_pass: int = 0           # tasks where no candidate passed train filter
    errors: int = 0                  # tasks that crashed
    total_candidates: int = 0
    total_time_sec: float = 0.0
    per_task: List[PipelineReport] = field(default_factory=list)

    @property
    def solve_rate(self) -> float:
        return self.solved / max(self.total_tasks, 1)

    @property
    def train_pass_rate(self) -> float:
        return self.train_pass_found / max(self.total_tasks, 1)

    def summary(self) -> str:
        lines = [
            f"═══ Batch Report ═══",
            f"  total tasks:           {self.total_tasks}",
            f"  solved (top-1 correct): {self.solved} ({self.solve_rate:.1%})",
            f"  train-pass found:      {self.train_pass_found} ({self.train_pass_rate:.1%})",
            f"  no train-pass:         {self.no_train_pass}",
            f"  errors:                {self.errors}",
            f"  total candidates:      {self.total_candidates}",
            f"  total time:            {self.total_time_sec:.1f}s",
            f"  avg time/task:         {self.total_time_sec/max(self.total_tasks,1):.2f}s",
            f"  avg candidates/task:   {self.total_candidates/max(self.total_tasks,1):.0f}",
        ]
        return "\n".join(lines)


def run_batch(task_dir: str,
              max_program_length: int = 2,
              max_tasks: Optional[int] = None,
              verbose: bool = True) -> BatchReport:
    """Run the pipeline on every .json task in a directory.

    Parameters
    ----------
    task_dir : str
        Directory containing ARC task JSON files.
    max_program_length : int
        Max operations per candidate program. Default 2.
    max_tasks : int or None
        If set, only run on the first N tasks. Default None (all).
    verbose : bool
        If True, print per-task progress.
    """
    harness = SubmissionHarness(max_program_length=max_program_length)
    report = BatchReport()
    t0 = time.time()

    task_files = sorted(f for f in os.listdir(task_dir) if f.endswith(".json"))
    if max_tasks is not None:
        task_files = task_files[:max_tasks]

    for i, fname in enumerate(task_files):
        task_path = os.path.join(task_dir, fname)
        task_id = os.path.splitext(fname)[0]
        try:
            task = load_task(task_path, name=task_id)
            predicted, pipe_report = harness.solve_task(task)
            report.total_tasks += 1
            report.total_candidates += pipe_report.n_candidates
            report.per_task.append(pipe_report)

            if pipe_report.n_train_pass > 0:
                report.train_pass_found += 1
            else:
                report.no_train_pass += 1

            # Check correctness if expected output is available
            if task.test[0].expected_output is not None:
                if predicted is not None and predicted == task.test[0].expected_output:
                    report.solved += 1
                    if verbose:
                        print(f"  [{i+1:3d}/{len(task_files)}] {task_id} ✓ SOLVED  "
                              f"(nrci={pipe_report.top_results[0].nrci_refined:.4f})")
                else:
                    if verbose:
                        verdict = "train-pass" if pipe_report.n_train_pass > 0 else "no-train-pass"
                        print(f"  [{i+1:3d}/{len(task_files)}] {task_id} ✗ wrong  "
                              f"({verdict}, cand={pipe_report.n_candidates})")
            else:
                if verbose:
                    print(f"  [{i+1:3d}/{len(task_files)}] {task_id} ? no ground truth")

        except Exception as e:
            report.errors += 1
            report.total_tasks += 1
            if verbose:
                print(f"  [{i+1:3d}/{len(task_files)}] {task_id} !! ERROR: {type(e).__name__}: {e}")

    report.total_time_sec = time.time() - t0
    return report


# ══════════════════════════════════════════════════════════════════════════════
# NULL-MODEL BATCH RUNNER — for falsification Test 2
# ══════════════════════════════════════════════════════════════════════════════

def run_null_model_comparison(task_dir: str,
                               max_tasks: int = 50,
                               max_program_length: int = 2) -> Dict:
    """Compare NRCI ranker vs random ranker on a batch of tasks.

    This is Test 2 of the falsification protocol (v2 study §7.2):
        "Replace the NRCI ranker with a uniform random ranker. If the
         random-ranker score equals or exceeds the NRCI-ranker score,
         NRCI is doing no work."

    Returns a dict with both rankers' solve rates and the statistical
    comparison.
    """
    nrci_ranker = Ranker()
    rand_ranker = RandomRanker(seed=42)

    nrci_solved = 0
    rand_solved = 0
    both_solved = 0
    nrci_only = 0
    rand_only = 0
    neither = 0
    total = 0

    task_files = sorted(f for f in os.listdir(task_dir) if f.endswith(".json"))[:max_tasks]

    for fname in task_files:
        task_path = os.path.join(task_dir, fname)
        try:
            task = load_task(task_path, name=os.path.splitext(fname)[0])
            if task.test[0].expected_output is None:
                continue
            total += 1

            candidates = generate_candidates(task, max_program_length=max_program_length)

            # NRCI ranker
            nrci_best = nrci_ranker.best(task, candidates)
            nrci_correct = (nrci_best is not None
                            and nrci_best.test_output == task.test[0].expected_output)

            # Random ranker
            rand_best = rand_ranker.best(task, candidates)
            rand_correct = (rand_best is not None
                            and rand_best.test_output == task.test[0].expected_output)

            if nrci_correct: nrci_solved += 1
            if rand_correct: rand_solved += 1
            if nrci_correct and rand_correct: both_solved += 1
            elif nrci_correct: nrci_only += 1
            elif rand_correct: rand_only += 1
            else: neither += 1
        except Exception:
            continue

    return {
        "total_tasks": total,
        "nrci_solved": nrci_solved,
        "rand_solved": rand_solved,
        "both_solved": both_solved,
        "nrci_only": nrci_only,
        "rand_only": rand_only,
        "neither": neither,
        "nrci_rate": nrci_solved / max(total, 1),
        "rand_rate": rand_solved / max(total, 1),
        "nrci_advantage": (nrci_solved - rand_solved) / max(total, 1),
    }


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    p = argparse.ArgumentParser(description="ARC-AGI-3 submission harness and batch runner")
    p.add_argument("task_dir", help="Directory of ARC task JSON files")
    p.add_argument("--max-tasks", type=int, default=None, help="Max tasks to evaluate")
    p.add_argument("--max-program-length", type=int, default=2)
    p.add_argument("--null-model", action="store_true",
                   help="Run NRCI vs random-ranker comparison (Test 2)")
    p.add_argument("--null-model-tasks", type=int, default=50,
                   help="Number of tasks for null-model comparison")
    p.add_argument("--save-submission", default=None,
                   help="Path to save submission JSON")
    p.add_argument("--quiet", action="store_true", help="Suppress per-task output")
    args = p.parse_args()

    if args.null_model:
        print(f"═══ Null-Model Comparison (Test 2) on {args.null_model_tasks} tasks ═══")
        result = run_null_model_comparison(args.task_dir,
                                            max_tasks=args.null_model_tasks,
                                            max_program_length=args.max_program_length)
        print(f"\n  total tasks:    {result['total_tasks']}")
        print(f"  NRCI solved:    {result['nrci_solved']} ({result['nrci_rate']:.1%})")
        print(f"  Random solved:  {result['rand_solved']} ({result['rand_rate']:.1%})")
        print(f"  both solved:    {result['both_solved']}")
        print(f"  NRCI only:      {result['nrci_only']}")
        print(f"  Random only:    {result['rand_only']}")
        print(f"  neither:        {result['neither']}")
        print(f"  NRCI advantage: {result['nrci_advantage']:+.1%}")
        if result['nrci_advantage'] > 0:
            print(f"\n  ✓ NRCI ranker beats random — NRCI is doing real work")
        elif result['nrci_advantage'] < 0:
            print(f"\n  ✗ Random ranker beats NRCI — NRCI may be HURTING (architecture concern)")
        else:
            print(f"\n  ? No difference — NRCI is not load-bearing (architecture falsified)")
    else:
        print(f"═══ Batch Run on {args.task_dir} ═══")
        report = run_batch(args.task_dir,
                           max_program_length=args.max_program_length,
                           max_tasks=args.max_tasks,
                           verbose=not args.quiet)
        print()
        print(report.summary())

        if args.save_submission:
            print(f"\n  Saving submission to {args.save_submission}...")
            harness = SubmissionHarness(max_program_length=args.max_program_length)
            tasks = {}
            task_files = sorted(f for f in os.listdir(args.task_dir) if f.endswith(".json"))
            if args.max_tasks:
                task_files = task_files[:args.max_tasks]
            for fname in task_files:
                task_id = os.path.splitext(fname)[0]
                tasks[task_id] = load_task(os.path.join(args.task_dir, fname), name=task_id)
            harness.save_submission(tasks, args.save_submission)
            print(f"  ✓ Saved")


if __name__ == "__main__":
    main()
