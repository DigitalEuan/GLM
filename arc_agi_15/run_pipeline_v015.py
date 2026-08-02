"""
run_pipeline_v015.py — v0.15 pipeline with full DSL, full CRG, full grammar
=============================================================================

Uses the FULL versions of all core modules:
  - arc_dsl_full.py (162 ops, up from 45)
  - object_crg_full.py (relational edges, analogical reasoning, transform chains)
  - generative_transformer_full.py (multi-object patterns, context-sensitive)
  - phi_grammar_arc_full.py (conditionals, recursion, variable binding)
  - smart_candidates.py (train-derived candidates)
  - conditional_candidates.py (position-dependent patterns)

The pipeline:
  1. Learn from train pairs using the FULL ObjectCRG (relational + analogical)
  2. Generate candidates using smart + conditional + Φ-grammar (162 ops)
  3. Rank by train-pass FIRST, NRCI as tiebreaker (v0.13 inversion)
  4. Fall back to GenerativeTransformerFull (analogical reasoning)
  5. Output dual: ARC JSON + full system reasoning
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
import time
import sys, os

_PKG_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import ARCTask, Grid, load_task
from encoder import encode_task


@dataclass
class V015Report:
    """Report from the v0.15 pipeline."""
    task_name: str
    predicted: Optional[Grid] = None
    prediction_source: str = "none"
    n_candidates: int = 0
    n_train_pass: int = 0
    correct: Optional[bool] = None
    time_sec: float = 0.0
    crg_stats: Dict[str, Any] = field(default_factory=dict)
    conditional_detected: int = 0
    fallback_used: bool = False


def run_pipeline_v015(task: ARCTask,
                      check_ground_truth: bool = True) -> V015Report:
    """Run the v0.15 pipeline on a single task."""
    report = V015Report(task_name=task.name)
    t0 = time.time()

    # ── Step 1: Learn from train pairs using FULL ObjectCRG ──
    from generative.object_crg_full import ObjectCRG as FullCRG
    crg = FullCRG()
    crg.learn_from_task(task)
    report.crg_stats = crg.stats()

    # ── Step 2: Generate candidates ──
    # 2a. Smart candidates (train-derived + CRG-learned + geometric)
    from grammar.smart_candidates import generate_smart_candidates
    # Patch: make smart_candidates use the full DSL
    import dsl.arc_dsl_full as full_dsl
    import dsl as old_dsl
    # Temporarily replace the old DSL's Ops/Operation/Program with the full one
    old_dsl.Ops = full_dsl.Ops
    old_dsl.Operation = full_dsl.Operation
    old_dsl.Program = full_dsl.Program
    old_dsl.OP_IMPL = full_dsl.OP_IMPL

    candidates = generate_smart_candidates(task, max_length=2)
    report.n_candidates = len(candidates)

    # 2b. Conditional candidates (position-dependent patterns)
    from grammar.conditional_candidates import generate_conditional_candidates
    conditional_cands = generate_conditional_candidates(task)
    report.conditional_detected = len(conditional_cands)

    # ── Step 3: Check conditional candidates FIRST (they're train-verified) ──
    if conditional_cands:
        for cand in conditional_cands:
            try:
                test_output = cand.apply(task.test[0].input)
                report.predicted = test_output
                report.prediction_source = "conditional"
                break
            except Exception:
                continue

    # ── Step 4: If no conditional, rank smart candidates ──
    if report.predicted is None:
        from ranker import Ranker, RankResult
        ranker = Ranker()
        results = ranker.rank(task, candidates)
        report.n_train_pass = sum(1 for r in results if r.train_pass and r.error is None)

        if report.n_train_pass > 0:
            top = ranker.top_k(task, candidates, k=1)
            if top:
                report.predicted = top[0].test_output
                report.prediction_source = "ranker"

    # ── Step 5: If no candidate passes, use the FULL GenerativeTransformer ──
    if report.predicted is None:
        try:
            from generative.generative_transformer_full import GenerativeTransformerFull
            transformer = GenerativeTransformerFull()
            transformer.learn_from_task(task)
            result = transformer.predict(task)
            if result is not None:
                report.predicted = result
                report.prediction_source = "generative_full"
                report.fallback_used = True
        except Exception as e:
            pass

    # ── Step 6: Last resort — identity ──
    if report.predicted is None:
        report.predicted = task.test[0].input.copy()
        report.prediction_source = "identity_fallback"

    # ── Ground truth check ──
    if check_ground_truth and task.test[0].expected_output is not None:
        report.correct = (report.predicted == task.test[0].expected_output)

    report.time_sec = time.time() - t0
    return report


def main():
    import argparse
    p = argparse.ArgumentParser(description="v0.15 GLM-ARC Pipeline")
    p.add_argument("--batch", default="data/training", help="Directory of ARC tasks")
    p.add_argument("--max-tasks", type=int, default=None)
    args = p.parse_args()

    task_files = sorted(f for f in os.listdir(args.batch) if f.endswith(".json"))
    if args.max_tasks:
        task_files = task_files[:args.max_tasks]

    print(f"═══ v0.15 Full System ({len(task_files)} tasks) ═══\n")

    solved = 0
    total = 0
    total_time = 0
    sources = {"conditional": 0, "ranker": 0, "generative_full": 0, "identity_fallback": 0}

    for fname in task_files:
        task = load_task(os.path.join(args.batch, fname),
                         name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1
        report = run_pipeline_v015(task)
        total_time += report.time_sec
        sources[report.prediction_source] = sources.get(report.prediction_source, 0) + 1

        if report.correct:
            solved += 1
            print(f"  ✓ {task.name}: {report.prediction_source} ({report.time_sec:.2f}s)")
        else:
            print(f"  ✗ {task.name}: {report.prediction_source} ({report.time_sec:.2f}s)")

    print(f"\n═══ Results ═══")
    print(f"  Solved: {solved}/{total} ({solved/max(total,1):.1%})")
    print(f"  Time: {total_time:.1f}s (avg {total_time/max(total,1):.2f}s/task)")
    print(f"  Sources: {sources}")


if __name__ == "__main__":
    main()
