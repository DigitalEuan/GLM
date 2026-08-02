"""
run_pipeline.py — end-to-end GLM-ARC pipeline runner
=====================================================

Runs the full 5-stage pipeline on a single ARC task:
  1. Load task (arc_loader)
  2. Encode grids (encoder)
  3. Generate candidates (grammar)
  4. Rank candidates (ranker)
  5. Verify and submit (ranker.top_k)

Usage:
    python3 run_pipeline.py path/to/task.json
    python3 run_pipeline.py --synthetic   # run on built-in synthetic tasks

For programmatic use:
    from run_pipeline import run_pipeline, PipelineReport
    report = run_pipeline(task)
    print(report.summary())
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import time
import sys, os

# Make all sub-packages importable
_PKG_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import ARCTask, load_task, Grid, TrainPair, TestInput
from encoder import encode_task, encode_grid
from grammar import PhiGrammar, generate_candidates
from ranker import Ranker, RankResult, RandomRanker


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE REPORT
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PipelineReport:
    task_name: str
    task_summary: str
    # Stage 2: encoding
    train_manifested_frac: float        # fraction of train grids with refined NRCI ≥ 0.70
    train_mean_refined_nrci: float
    test_manifested_frac: float
    test_mean_refined_nrci: float
    # Stage 3: candidate generation
    n_candidates: int
    gen_time_sec: float
    # Stage 4: ranking
    n_train_pass: int                   # candidates that pass empirical-adequacy filter
    n_submit: int                       # candidates with verdict == SUBMIT
    n_marginal: int                     # candidates with verdict == MARGINAL
    n_curiosity: int                    # candidates with verdict == CURIOSITY
    n_discard: int                      # candidates with verdict == DISCARD
    n_error: int                        # candidates that crashed
    rank_time_sec: float
    # Stage 5: top-k
    top_results: List[RankResult] = field(default_factory=list)
    # Optional: ground-truth check
    correct: Optional[bool] = None      # True iff top-1 matches expected output

    def summary(self) -> str:
        lines = [
            f"═══ Pipeline Report: {self.task_name} ═══",
            f"",
            f"── Stage 2: Encoding ──",
            f"  train manifested fraction:  {self.train_manifested_frac:.1%}",
            f"  train mean refined NRCI:    {self.train_mean_refined_nrci:.4f}",
            f"  test manifested fraction:   {self.test_manifested_frac:.1%}",
            f"  test mean refined NRCI:     {self.test_mean_refined_nrci:.4f}",
            f"",
            f"── Stage 3: Candidate Generation ──",
            f"  candidates generated:       {self.n_candidates}",
            f"  generation time:            {self.gen_time_sec:.2f}s",
            f"",
            f"── Stage 4: Ranking ──",
            f"  train-pass:                 {self.n_train_pass}",
            f"  SUBMIT (train-pass + NRCI≥0.70): {self.n_submit}",
            f"  MARGINAL (train-pass + NRCI<0.70): {self.n_marginal}",
            f"  CURIOSITY (train-fail + NRCI≥0.70): {self.n_curiosity}",
            f"  DISCARD (train-fail + NRCI<0.70):  {self.n_discard}",
            f"  ERROR:                      {self.n_error}",
            f"  ranking time:               {self.rank_time_sec:.2f}s",
            f"",
            f"── Stage 5: Top-k ──",
        ]
        for i, r in enumerate(self.top_results[:3]):
            lines.append(f"  [{i}] {r.verdict}  nrci={r.nrci_refined:.4f}  {r.program}")
        if self.correct is not None:
            lines.append(f"")
            lines.append(f"── Ground-truth check ──")
            lines.append(f"  top-1 matches expected:     {self.correct}")
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline(task: ARCTask,
                 max_program_length: int = 2,
                 top_k: int = 3,
                 check_ground_truth: bool = True) -> PipelineReport:
    """Run the full 5-stage pipeline on a single ARC task.

    Parameters
    ----------
    task : ARCTask
        The task to solve.
    max_program_length : int
        Maximum number of operations per candidate program. Default 2.
    top_k : int
        Number of top candidates to return. Default 3.
    check_ground_truth : bool
        If True (and task.test[0].expected_output is set), check if top-1
        matches the expected output.
    """
    # Stage 2: encode all grids in the task
    task_enc = encode_task(task)

    # Stage 3: generate candidates (v0.14: smart + conditional candidates)
    t0 = time.time()
    from grammar.smart_candidates import generate_smart_candidates
    from grammar.conditional_candidates import generate_conditional_candidates
    candidates = generate_smart_candidates(task, max_length=max_program_length)
    conditional_cands = generate_conditional_candidates(task)
    # Conditional candidates are CustomPrograms, not standard Programs.
    # They need special handling in the ranker — add them as a separate list.
    gen_time = time.time() - t0

    # Stage 4: rank candidates (v0.14: include conditional candidates)
    t0 = time.time()
    ranker = Ranker()
    results = ranker.rank(task, candidates)
    rank_time = time.time() - t0

    # Tally verdicts
    n_submit = sum(1 for r in results if r.verdict == "SUBMIT")
    n_marginal = sum(1 for r in results if r.verdict == "MARGINAL")
    n_curiosity = sum(1 for r in results if r.verdict == "CURIOSITY")
    n_discard = sum(1 for r in results if r.verdict == "DISCARD")
    n_error = sum(1 for r in results if r.verdict == "ERROR")
    n_train_pass = sum(1 for r in results if r.train_pass and r.error is None)

    # v0.14: Check conditional candidates FIRST — they already pass train
    conditional_outputs: List[Tuple[Any, Grid]] = []
    for cand in conditional_cands:
        try:
            test_output = cand.apply(task.test[0].input)
            conditional_outputs.append((cand, test_output))
        except Exception:
            pass

    # Stage 5: top-k
    # v0.14: If conditional candidates exist, prefer them (they're train-verified)
    if conditional_outputs:
        # Use the first conditional candidate (they're all train-verified)
        best_cond = conditional_outputs[0]
        from ranker import RankResult
        top = [RankResult(
            program=best_cond[0],
            train_pass=True,
            nrci_basic=0.0,
            nrci_refined=0.0,
            manifested=False,
            test_output=best_cond[1],
        )]
    else:
        top = ranker.top_k(task, candidates, k=top_k)

    # Ground-truth check
    correct = None
    if check_ground_truth and task.test[0].expected_output is not None and top:
        correct = (top[0].test_output == task.test[0].expected_output)

    return PipelineReport(
        task_name=task.name,
        task_summary=task.summary(),
        train_manifested_frac=task_enc.manifested_fraction(),
        train_mean_refined_nrci=task_enc.mean_refined_nrci(),
        test_manifested_frac=sum(1 for r in task_enc.test_inputs if r.manifested) / max(len(task_enc.test_inputs), 1),
        test_mean_refined_nrci=sum(r.nrci_refined for r in task_enc.test_inputs) / max(len(task_enc.test_inputs), 1),
        n_candidates=len(candidates),
        gen_time_sec=gen_time,
        n_train_pass=n_train_pass,
        n_submit=n_submit,
        n_marginal=n_marginal,
        n_curiosity=n_curiosity,
        n_discard=n_discard,
        n_error=n_error,
        rank_time_sec=rank_time,
        top_results=top,
        correct=correct,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SYNTHETIC TASKS — for self-test
# ══════════════════════════════════════════════════════════════════════════════

def _make_synthetic_rotate_task() -> ARCTask:
    """A 2-train-pair task where the rule is 'rotate 90° clockwise'."""
    in1 = Grid([[1, 0, 0],
                [1, 0, 0],
                [1, 1, 1]])
    out1 = in1.rotate_90()
    in2 = Grid([[0, 0, 2],
                [0, 0, 2],
                [2, 2, 2]])
    out2 = in2.rotate_90()
    test_in = Grid([[3, 0, 0],
                    [3, 0, 0],
                    [3, 3, 3]])
    test_out = test_in.rotate_90()
    return ARCTask(
        train=[TrainPair(in1, out1), TrainPair(in2, out2)],
        test=[TestInput(test_in, expected_output=test_out)],
        name="synthetic_rotate_90",
    )


def _make_synthetic_recolour_task() -> ARCTask:
    """A 2-train-pair task where the rule is 'swap colours 1 and 2'."""
    in1 = Grid([[1, 1, 0],
                [0, 2, 2]])
    out1 = in1.recolour({1: 2, 2: 1})
    in2 = Grid([[2, 0, 1],
                [2, 1, 0]])
    out2 = in2.recolour({1: 2, 2: 1})
    test_in = Grid([[1, 2, 1],
                    [2, 1, 2]])
    test_out = test_in.recolour({1: 2, 2: 1})
    return ARCTask(
        train=[TrainPair(in1, out1), TrainPair(in2, out2)],
        test=[TestInput(test_in, expected_output=test_out)],
        name="synthetic_recolour_swap",
    )


def _make_synthetic_gravity_task() -> ARCTask:
    """A 2-train-pair task where the rule is 'gravity down' (column-wise compaction).

    Gravity semantics: each column's non-zero cells compact to the bottom,
    preserving their relative order. This matches the standard ARC gravity family.
    """
    in1 = Grid([[1, 0, 0],
                [0, 0, 2],
                [0, 0, 0]])
    # Column 0: [1, 0, 0] → compact to [0, 0, 1]
    # Column 1: [0, 0, 0] → [0, 0, 0]
    # Column 2: [0, 2, 0] → compact to [0, 0, 2]
    out1 = Grid([[0, 0, 0],
                 [0, 0, 0],
                 [1, 0, 2]])
    in2 = Grid([[0, 3, 0, 4],
                [0, 0, 0, 0]])
    # Both 3 and 4 fall to the bottom row
    out2 = Grid([[0, 0, 0, 0],
                 [0, 3, 0, 4]])
    test_in = Grid([[5, 0, 6],
                    [0, 0, 0]])
    test_out = Grid([[0, 0, 0],
                     [5, 0, 6]])
    return ARCTask(
        train=[TrainPair(in1, out1), TrainPair(in2, out2)],
        test=[TestInput(test_in, expected_output=test_out)],
        name="synthetic_gravity_down",
    )


def _make_synthetic_count_fill_task() -> ARCTask:
    """A 2-train-pair task where the rule is 'fill bottom row with N copies of dominant
    colour, where N = number of distinct objects'."""
    # 3 objects → 3 cells filled
    in1 = Grid([[1, 0, 2],
                [0, 3, 0],
                [0, 0, 0]])
    out1 = Grid([[1, 0, 2],
                 [0, 3, 0],
                 [1, 1, 1]])  # 3 cells of dominant (1)
    # 2 objects → 2 cells filled
    in2 = Grid([[4, 0, 0],
                [0, 0, 5],
                [0, 0, 0]])
    out2 = Grid([[4, 0, 0],
                 [0, 0, 5],
                 [4, 4, 0]])
    test_in = Grid([[6, 0, 7],
                    [0, 0, 0],
                    [0, 0, 0]])
    test_out = Grid([[6, 0, 7],
                     [0, 0, 0],
                     [6, 6, 0]])
    return ARCTask(
        train=[TrainPair(in1, out1), TrainPair(in2, out2)],
        test=[TestInput(test_in, expected_output=test_out)],
        name="synthetic_count_fill",
    )


SYNTHETIC_TASKS = {
    "rotate_90":   _make_synthetic_rotate_task,
    "recolour":    _make_synthetic_recolour_task,
    "gravity":     _make_synthetic_gravity_task,
    "count_fill":  _make_synthetic_count_fill_task,
}


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    p = argparse.ArgumentParser(description="Run the GLM-ARC pipeline end-to-end")
    p.add_argument("task_path", nargs="?", help="Path to ARC task JSON file")
    p.add_argument("--synthetic", action="store_true",
                   help="Run on built-in synthetic tasks instead of a JSON file")
    p.add_argument("--which-synthetic", default="all",
                   choices=["all", "rotate_90", "recolour", "gravity", "count_fill"],
                   help="Which synthetic task to run")
    p.add_argument("--max-program-length", type=int, default=2,
                   help="Max operations per candidate program (default: 2)")
    p.add_argument("--top-k", type=int, default=3,
                   help="Number of top candidates to return (default: 3)")
    args = p.parse_args()

    if args.synthetic:
        which = ([args.which_synthetic] if args.which_synthetic != "all"
                 else list(SYNTHETIC_TASKS.keys()))
        print(f"═══ Running {len(which)} synthetic task(s) ═══\n")
        all_correct = True
        for name in which:
            task = SYNTHETIC_TASKS[name]()
            print(f"── Task: {name} ──")
            report = run_pipeline(task,
                                   max_program_length=args.max_program_length,
                                   top_k=args.top_k)
            print(report.summary())
            print()
            if report.correct is False:
                all_correct = False
        print(f"═══ Synthetic summary: {'all correct' if all_correct else 'some failed'} ═══")
    elif args.task_path:
        task = load_task(args.task_path)
        report = run_pipeline(task,
                               max_program_length=args.max_program_length,
                               top_k=args.top_k)
        print(report.summary())
    else:
        p.error("Either provide task_path or use --synthetic")


if __name__ == "__main__":
    main()
