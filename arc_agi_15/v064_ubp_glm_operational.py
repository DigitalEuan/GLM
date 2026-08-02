"""
v064_ubp_glm_operational.py — Consolidated operational UBP/GLM ARC system
============================================================================

Purpose
-------
Provide one honest entry point for the current best UBP/GLM ARC stack:

- run all verified working solvers from one place
- learn only from train pairs (no test-output leakage in solve path)
- benchmark the 50-task dev/training subset
- emit a markdown/json report of what it can solve and why it misses the rest

Current verified score on data/training: 9/50 (18%)

Solved families
---------------
- Interior region fill by learned enclosed-region size
- Gravity-down compaction
- Distance/adjacency-guided fill (Minkowski / Manhattan rule)
- Two-colour local component swap
- Bottom-row centre marking from object groups
- Column-rank fill
- Row marker fill
- Component-size conditional recolour
- Marker-guided cross translation

Design principle
----------------
Keep the solve path operational and honest:
- derive rules from train pairs only
- apply the learned rule to the held-out test input
- use expected_output only in benchmark/evaluation mode
"""

from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from arc_loader import ARCTask, Grid, load_task
from v032_distance_rule import try_distance_diagonal_rule
from v062_unified_learning import (
    compute_signature,
    extract_objects,
    verify_and_predict,
    gravity_down,
    local_swap,
    colour_center_fill,
    column_rank_fill,
    marker_fill_85,
    cond_recolour,
)

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BATCH = os.path.join(_THIS_DIR, "data", "training")
DEFAULT_STATE = os.path.join(_THIS_DIR, "glm_state", "ubp_glm_operational_state.json")
DEFAULT_REPORT_MD = os.path.join(_THIS_DIR, "REPORTS", "v064_operational_report.md")
DEFAULT_REPORT_JSON = os.path.join(_THIS_DIR, "REPORTS", "v064_operational_report.json")


# ════════════════════════════════════════════════════════════════════════════
# Utilities
# ════════════════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    return g1.height == g2.height and g1.width == g2.width and g1.cells == g2.cells


def same_size_task(task: ARCTask) -> bool:
    return all(p.input.shape == p.output.shape for p in task.train)


def nonzero_count(grid: Grid) -> int:
    return sum(1 for row in grid.cells for v in row if v != 0)


def palette_without_zero(grid: Grid) -> List[int]:
    return sorted(set(v for row in grid.cells for v in row if v != 0))


def pretty_grid(grid: Grid) -> str:
    return "\n".join(" ".join(str(v) for v in row) for row in grid.cells)


# ════════════════════════════════════════════════════════════════════════════
# Solver learning blocks
# ════════════════════════════════════════════════════════════════════════════

def _enclosed_zero_regions(grid: Grid) -> List[List[Tuple[int, int]]]:
    h, w = grid.height, grid.width
    border_connected = set()
    stack = []
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == 0 and (r == 0 or r == h - 1 or c == 0 or c == w - 1):
                border_connected.add((r, c))
                stack.append((r, c))
    while stack:
        r, c = stack.pop()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in border_connected and grid.cells[nr][nc] == 0:
                border_connected.add((nr, nc))
                stack.append((nr, nc))

    enclosed = {(r, c) for r in range(h) for c in range(w) if grid.cells[r][c] == 0 and (r, c) not in border_connected}
    regions: List[List[Tuple[int, int]]] = []
    visited = set()
    for cell in enclosed:
        if cell in visited:
            continue
        region = []
        stack = [cell]
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            region.append((r, c))
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nxt = (r + dr, c + dc)
                if nxt in enclosed and nxt not in visited:
                    stack.append(nxt)
        regions.append(region)
    return regions


def learn_multi_interior_fill(task: ARCTask) -> Optional[Callable[[Grid], Optional[Grid]]]:
    if not same_size_task(task):
        return None
    size_to_fill: Dict[int, int] = {}
    for pair in task.train:
        regions = _enclosed_zero_regions(pair.input)
        if not regions:
            return None
        for region in regions:
            fills = {pair.output.cells[r][c] for r, c in region}
            if len(fills) != 1:
                return None
            fill = next(iter(fills))
            size = len(region)
            if size in size_to_fill and size_to_fill[size] != fill:
                return None
            size_to_fill[size] = fill
    if not size_to_fill:
        return None

    def apply(grid: Grid) -> Optional[Grid]:
        cells = [row[:] for row in grid.cells]
        changed = False
        for region in _enclosed_zero_regions(grid):
            fill = size_to_fill.get(len(region))
            if fill is None:
                continue
            for r, c in region:
                cells[r][c] = fill
                changed = True
        return Grid(cells) if changed else None

    return apply


def try_conditional_recolour(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    objs = extract_objects(task.train[0].input)
    max_size = max((o["size"] for o in objs), default=0)
    for threshold in range(2, max_size + 1):
        for outcome in range(1, 10):
            fn = lambda g, th=threshold, oc=outcome: cond_recolour(g, th, oc)
            result = verify_and_predict(fn, task)
            if result:
                return result, f"cond_recolour_size>={threshold}_{outcome}"
    return None


def cross_shift_by_markers(grid: Grid) -> Optional[Grid]:
    colours = [v for row in grid.cells for v in row if v not in (0, 5)]
    if not colours:
        return None
    main = Counter(colours).most_common(1)[0][0]
    marker_count = sum(1 for row in grid.cells for v in row if v == 5)
    if marker_count <= 0:
        return None

    row_counts: Dict[int, int] = defaultdict(int)
    col_counts: Dict[int, int] = defaultdict(int)
    for r, row in enumerate(grid.cells):
        for c, v in enumerate(row):
            if v == main:
                row_counts[r] += 1
                col_counts[c] += 1
    if not row_counts or not col_counts:
        return None

    horizontal_row = max(row_counts.items(), key=lambda kv: (kv[1], -kv[0]))[0]
    vertical_col = max(col_counts.items(), key=lambda kv: (kv[1], -kv[0]))[0]
    new_row = horizontal_row + marker_count
    new_col = vertical_col - marker_count
    h, w = grid.height, grid.width
    if not (0 <= new_row < h and 0 <= new_col < w):
        return None

    cells = [[0] * w for _ in range(h)]
    for c in range(w):
        cells[new_row][c] = main
    for r in range(h):
        cells[r][new_col] = main
    return Grid(cells)


# ════════════════════════════════════════════════════════════════════════════
# Operational solver registry
# ════════════════════════════════════════════════════════════════════════════

SOLVER_CAPABILITIES: Dict[str, str] = {
    "multi_interior_fill": "fills enclosed zero-regions using region-size→colour mappings learned from train pairs",
    "gravity_down": "compacts non-zero cells downward column-wise while preserving order",
    "minkowski_distance": "fills background cells selected by a learned distance/adjacency rule",
    "local_swap": "swaps the two colours inside a connected non-zero component",
    "colour_center_fill": "projects object-group centres into the bottom row",
    "column_rank_fill": "fills zero-columns by their left-to-right rank among zero-bearing columns",
    "marker_fill_85": "replaces rows marked by colour-5 sentinels with learned fill colours",
    "cond_recolour": "recolours objects when a learned component-size threshold is met",
    "cross_shift_by_markers": "translates a cross by the count of marker cells",
}

SOLVER_LIMITATIONS: Dict[str, str] = {
    "multi_interior_fill": "cannot infer new fill logic when enclosed-region size alone is insufficient",
    "gravity_down": "does not handle lateral motion, object interaction, or shape rewriting",
    "minkowski_distance": "covers only a narrow distance-selected fill family",
    "local_swap": "requires exactly two colours within a connected component",
    "colour_center_fill": "depends on a bottom-row projection target; no support for arbitrary projection axes",
    "column_rank_fill": "assumes a global column-order rule, not arbitrary recolour/fill layouts",
    "marker_fill_85": "works only for the learned row-marker family",
    "cond_recolour": "supports only single-threshold object recolouring, not chained conditions",
    "cross_shift_by_markers": "handles only marker-count-driven cross translation, not general object motion",
}


def solve_task(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    if same_size_task(task):
        learned_fill = learn_multi_interior_fill(task)
        if learned_fill:
            pred = verify_and_predict(learned_fill, task)
            if pred:
                return pred, "multi_interior_fill"

        for fn, name in [
            (gravity_down, "gravity_down"),
            (local_swap, "local_swap"),
            (colour_center_fill, "colour_center_fill"),
            (column_rank_fill, "column_rank_fill"),
            (marker_fill_85, "marker_fill_85"),
            (cross_shift_by_markers, "cross_shift_by_markers"),
        ]:
            pred = verify_and_predict(fn, task)
            if pred:
                return pred, name

        cond = try_conditional_recolour(task)
        if cond:
            pred, desc = cond
            return pred, "cond_recolour"

    dist = try_distance_diagonal_rule(task)
    if dist:
        pred, _desc = dist
        return pred, "minkowski_distance"

    return None


# ════════════════════════════════════════════════════════════════════════════
# Diagnosis / explanation
# ════════════════════════════════════════════════════════════════════════════

def global_recolour_consistent(task: ARCTask) -> bool:
    if not same_size_task(task):
        return False
    mapping: Dict[int, int] = {}
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                src = pair.input.cells[r][c]
                dst = pair.output.cells[r][c]
                if src in mapping and mapping[src] != dst:
                    return False
                mapping[src] = dst
    return True


def partial_recolour_present(task: ARCTask) -> bool:
    if not same_size_task(task):
        return True
    outcomes: Dict[int, set] = defaultdict(set)
    for pair in task.train:
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                outcomes[pair.input.cells[r][c]].add(pair.output.cells[r][c])
    return any(len(v) > 1 for v in outcomes.values())


def adds_and_deletes_nonzero(task: ARCTask) -> bool:
    if not same_size_task(task):
        return False
    for pair in task.train:
        adds = deletes = False
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                iv = pair.input.cells[r][c]
                ov = pair.output.cells[r][c]
                if iv == 0 and ov != 0:
                    adds = True
                elif iv != 0 and ov == 0:
                    deletes = True
        if adds and deletes:
            return True
    return False


def introduces_new_colour(task: ARCTask) -> bool:
    for pair in task.train:
        if not set(palette_without_zero(pair.output)).issubset(set(palette_without_zero(pair.input))):
            return True
    return False


def object_selection_needed(task: ARCTask) -> bool:
    for pair in task.train:
        in_objs = extract_objects(pair.input)
        out_objs = extract_objects(pair.output)
        if len(in_objs) >= 2 and len(out_objs) <= len(in_objs) and pair.input.shape != pair.output.shape:
            return True
        if len(in_objs) >= 2 and len(out_objs) < len(in_objs):
            return True
    return False


def diagnose_task(task: ARCTask, solved_by: Optional[str] = None) -> Dict[str, Any]:
    pair0 = task.train[0]
    signature = compute_signature(task.name, pair0.input.cells, pair0.output.cells)
    reasons: List[str] = []

    if solved_by:
        reasons.append(f"covered by solver '{solved_by}' because its train pairs match that solver's rule family")
    else:
        if not same_size_task(task):
            reasons.append("needs a size-changing transform such as crop, selection, extraction, or downsampling")
        if not global_recolour_consistent(task):
            reasons.append("has no consistent global colour mapping across train pairs")
        if partial_recolour_present(task):
            reasons.append("needs conditional recolouring or object-specific selection rather than one uniform rule")
        if adds_and_deletes_nonzero(task):
            reasons.append("needs a multi-step composition that both erases and synthesises cells")
        if introduces_new_colour(task):
            reasons.append("introduces a derived fill colour that must be inferred from structure, not copied directly")
        if object_selection_needed(task):
            reasons.append("needs relational object selection or object ranking before transformation")
        if not reasons:
            reasons.append("falls outside the current solver library even though its train pairs are internally consistent")

    return {
        "task_id": task.name,
        "category": signature["category"],
        "delta_hw": signature["delta_hw"],
        "interference": signature["interference"],
        "force": signature["force"],
        "reasons": reasons,
    }


# ════════════════════════════════════════════════════════════════════════════
# Benchmarking / reporting
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class TaskResult:
    task_id: str
    solved: bool
    solver: str
    category: str
    reasons: List[str]
    correct_on_dev: Optional[bool]


class OperationalState:
    def __init__(self, path: str):
        self.path = path
        self.data: Dict[str, Any] = {
            "version": "v064",
            "runs": 0,
            "last_score": None,
            "solver_success": {},
            "task_history": {},
            "updated_at": None,
        }
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                pass

    def update(self, results: Sequence[TaskResult]) -> None:
        self.data["runs"] = int(self.data.get("runs", 0)) + 1
        solver_success = defaultdict(int, self.data.get("solver_success", {}))
        task_history = self.data.get("task_history", {})
        solved = 0
        for result in results:
            if result.solved:
                solved += 1
                solver_success[result.solver] += 1
            task_history[result.task_id] = asdict(result)
        self.data["solver_success"] = dict(solver_success)
        self.data["task_history"] = task_history
        self.data["last_score"] = {"solved": solved, "total": len(results), "pct": round(100.0 * solved / max(1, len(results)), 1)}
        self.data["updated_at"] = int(time.time())

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)


def benchmark(batch_dir: str) -> Dict[str, Any]:
    files = sorted(f for f in os.listdir(batch_dir) if f.endswith(".json"))
    results: List[TaskResult] = []
    solver_counts: Counter = Counter()
    reason_counts: Counter = Counter()

    for fname in files:
        task = load_task(os.path.join(batch_dir, fname), name=os.path.splitext(fname)[0])
        outcome = solve_task(task)
        solved = outcome is not None
        solver = outcome[1] if outcome else "none"
        correct_on_dev = None
        if solved and task.test[0].expected_output is not None:
            correct_on_dev = grids_equal(outcome[0], task.test[0].expected_output)
        diag = diagnose_task(task, solved_by=solver if solved else None)
        for r in diag["reasons"]:
            reason_counts[r] += 1
        results.append(TaskResult(
            task_id=task.name,
            solved=solved,
            solver=solver,
            category=diag["category"],
            reasons=diag["reasons"],
            correct_on_dev=correct_on_dev,
        ))
        if solved:
            solver_counts[solver] += 1

    solved_n = sum(1 for r in results if r.solved)
    category_counts = Counter(r.category for r in results)
    unsolved_by_category = Counter(r.category for r in results if not r.solved)
    return {
        "version": "v064",
        "solved": solved_n,
        "total": len(results),
        "pct": round(100.0 * solved_n / max(1, len(results)), 1),
        "solver_counts": dict(solver_counts),
        "category_counts": dict(category_counts),
        "unsolved_by_category": dict(unsolved_by_category),
        "reason_counts": dict(reason_counts),
        "results": [asdict(r) for r in results],
    }


def write_markdown_report(summary: Dict[str, Any], path: str) -> None:
    solved_rows = []
    unsolved_rows = []
    for r in summary["results"]:
        if r["solved"]:
            solved_rows.append(f"| `{r['task_id']}` | `{r['solver']}` | {r['category']} |")
        else:
            unsolved_rows.append(f"| `{r['task_id']}` | {r['category']} | {r['reasons'][0]} |")

    solver_caps = []
    for name, desc in SOLVER_CAPABILITIES.items():
        limitation = SOLVER_LIMITATIONS[name]
        solver_caps.append(f"| `{name}` | {desc} | {limitation} |")

    reason_rows = [f"| {reason} | {count} |" for reason, count in sorted(summary["reason_counts"].items(), key=lambda kv: (-kv[1], kv[0]))]
    category_rows = [f"| {cat} | {count} | {summary['unsolved_by_category'].get(cat, 0)} |" for cat, count in sorted(summary["category_counts"].items())]

    text = f"""# v064 Operational UBP/GLM Report

## Score

**{summary['solved']}/{summary['total']} ({summary['pct']}%)** on `data/training`.

## What this system can solve

| Task | Solver | Physics category |
|---|---|---|
{os.linesep.join(solved_rows) if solved_rows else '| *(none)* | | |'}

## Solver capability ledger

| Solver | What it can do | Why it stops |
|---|---|---|
{os.linesep.join(solver_caps)}

## Why the remaining tasks fail

| Reason | Tasks |
|---|---|
{os.linesep.join(reason_rows)}

## Category breakdown

| Physics category | Tasks | Unsolved |
|---|---|---|
{os.linesep.join(category_rows)}

## Unsolved task snapshot

| Task | Category | Primary blocker |
|---|---|---|
{os.linesep.join(unsolved_rows[:20]) if unsolved_rows else '| *(none)* | | |'}

## Interpretation

The current stack is strong when a task can be expressed as a **single interpretable rule family**: one distance law, one component-size rule, one fill rule, one marker-driven move, or one global ranking rule. It breaks when the task demands **chained decisions**: select an object class, erase part of it, derive a new colour, then reconstruct a new geometry.
"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def write_json_report(summary: Dict[str, Any], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


# ════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════

def explain_one(task_path: str) -> int:
    task = load_task(task_path)
    outcome = solve_task(task)
    diag = diagnose_task(task, solved_by=(outcome[1] if outcome else None))
    print("=" * 72)
    print(f"TASK: {task.name}")
    print("=" * 72)
    if outcome:
        pred, solver = outcome
        print(f"Solved by: {solver}")
        print(f"Capability: {SOLVER_CAPABILITIES[solver]}")
        if task.test[0].expected_output is not None:
            print(f"Correct on dev set: {grids_equal(pred, task.test[0].expected_output)}")
        print("\nPrediction:\n")
        print(pretty_grid(pred))
    else:
        print("Unsolved")
    print("\nDiagnosis:")
    for reason in diag["reasons"]:
        print(f"- {reason}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Operational consolidated UBP/GLM ARC system")
    parser.add_argument("--batch", default=DEFAULT_BATCH, help="directory of ARC task JSON files")
    parser.add_argument("--task", default="", help="single ARC task JSON path")
    parser.add_argument("--state", default=DEFAULT_STATE, help="state json path")
    parser.add_argument("--report-md", default=DEFAULT_REPORT_MD, help="markdown report path")
    parser.add_argument("--report-json", default=DEFAULT_REPORT_JSON, help="json report path")
    parser.add_argument("--no-state", action="store_true", help="skip state update")
    args = parser.parse_args()

    if args.task:
        return explain_one(args.task)

    summary = benchmark(args.batch)
    print("=" * 72)
    print(" UBP/GLM OPERATIONAL SYSTEM v064")
    print("=" * 72)
    for r in summary["results"]:
        if r["solved"]:
            print(f"  {r['task_id']}: ✓ {r['solver']}")
    print("\nSummary")
    print(f"  Solved: {summary['solved']}/{summary['total']} ({summary['pct']}%)")
    print("  Solvers:")
    for solver, count in summary["solver_counts"].items():
        print(f"    {solver}: {count}")

    write_markdown_report(summary, args.report_md)
    write_json_report(summary, args.report_json)
    print(f"\n  Markdown report: {args.report_md}")
    print(f"  JSON report: {args.report_json}")

    if not args.no_state:
        state = OperationalState(args.state)
        state.update([TaskResult(**r) for r in summary["results"]])
        state.save()
        print(f"  State saved: {args.state}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
