"""
reasoning_loop.py - The Mind's Complete Reasoning Cycle
========================================================

The mind doesn't just solve tasks. It REASONS about them:

1. PERCEIVE: What do I see? (describe the input in Lingo)
2. GOAL: What needs to happen? (describe the expected output in Lingo)
3. GAP: What's different? (compare input vs output semantically)
4. PROPOSE: How do I get there? (suggest a transformation)
5. INSPECT: Does my proposal work? (verify and explain)

This is the complete cognitive cycle - the mind's ability to think
about a problem, not just brute-force a solution.
"""

from __future__ import annotations
import os, sys, json, time, math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arc_loader import ARCTask, Grid, load_task
from conditional_lobe import (
    extract_objects, GridObject, induce_conditional_pattern,
    apply_conditional_pattern, verify_conditional_pattern,
)
from semantic_layer import describe_transformation, LINGO_VOCAB, LINGO_TO_HUMAN


# ═══════════════════════════════════════════════════════════════════════════════
# Perception - What Do I See?
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Percept:
    """What the mind perceives about a grid."""
    # Objects
    objects: List[GridObject] = field(default_factory=list)
    n_objects: int = 0

    # Structure
    rows: int = 0
    cols: int = 0
    density: float = 0.0
    palette: Set[int] = field(default_factory=set)

    # Energy
    tax: float = 0.0
    nrci: float = 0.0

    # Semantic description
    lingo_description: str = ""
    human_description: str = ""


def perceive_grid(grid: Grid) -> Percept:
    """Perceive a grid and describe it in Lingo."""
    p = Percept()
    p.rows, p.cols = grid.height, grid.width
    p.objects = extract_objects(grid)
    p.n_objects = len(p.objects)
    p.palette = set(v for row in grid.cells for v in row if v != 0)
    p.density = sum(1 for row in grid.cells for v in row if v != 0) / (p.rows * p.cols)

    # TAX/NRCI
    hw = sum(1 for row in grid.cells for v in row if v != 0)
    norm_sq = sum(v * v for row in grid.cells for v in row)
    Y = 0.2646754304045269672
    p.tax = hw * Y + norm_sq / 8.0
    p.nrci = 10.0 / (10.0 + p.tax)

    # Lingo description
    parts = []
    parts.append(f"SPATIAL_SUBSTRATE({p.rows}×{p.cols})")
    parts.append(f"density={p.density:.2f}")
    parts.append(f"NRCI={p.nrci:.3f}")

    if p.objects:
        obj_summary = Counter(o.colour for o in p.objects)
        obj_parts = [f"CLUSTER(colour={c}, count={n})" for c, n in obj_summary.most_common(3)]
        parts.append("objects: " + ", ".join(obj_parts))

    p.lingo_description = " | ".join(parts)

    # Human description
    human_parts = []
    human_parts.append(f"{p.rows}×{p.cols} grid")
    human_parts.append(f"{p.n_objects} objects")
    human_parts.append(f"colours: {sorted(p.palette)}")
    if p.objects:
        sizes = sorted([o.size for o in p.objects], reverse=True)[:3]
        human_parts.append(f"sizes: {sizes}")
    p.human_description = ", ".join(human_parts)

    return p


# ═══════════════════════════════════════════════════════════════════════════════
# Goal - What Needs to Happen?
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Goal:
    """What the mind understands the goal to be."""
    # What should change
    objects_should_change: List[str] = field(default_factory=list)
    objects_should_stay: List[str] = field(default_factory=list)

    # The transformation
    transformation_type: str = ""
    transformation_description: str = ""

    # Confidence
    confidence: float = 0.0


def infer_goal(task: ARCTask) -> Goal:
    """Infer the goal from train pairs - what needs to happen?"""
    goal = Goal()

    # Analyse all train pairs
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            goal.transformation_type = "size_change"
            goal.transformation_description = f"Size {pair.input.shape} → {pair.output.shape}"
            continue

        inp_objs = extract_objects(pair.input)
        out_objs = extract_objects(pair.output)

        # What objects changed?
        for inp_obj in inp_objs:
            # Check if this object changed
            out_colours = set()
            for r, c in inp_obj.cells:
                out_colours.add(pair.output.cells[r][c])

            if len(out_colours) == 1:
                out_colour = next(iter(out_colours))
                if out_colour != inp_obj.colour:
                    desc = f"CLUSTER(colour={inp_obj.colour}, size={inp_obj.size}) → colour {out_colour}"
                    if desc not in goal.objects_should_change:
                        goal.objects_should_change.append(desc)
                else:
                    desc = f"CLUSTER(colour={inp_obj.colour}, size={inp_obj.size}) preserved"
                    if desc not in goal.objects_should_stay:
                        goal.objects_should_stay.append(desc)

    # Infer transformation type
    if not goal.transformation_type:
        if goal.objects_should_change and not goal.objects_should_stay:
            goal.transformation_type = "global_recolour"
        elif goal.objects_should_change and goal.objects_should_stay:
            goal.transformation_type = "conditional_recolour"
        elif not goal.objects_should_change:
            goal.transformation_type = "structural"

    goal.confidence = 0.7
    return goal


# ═══════════════════════════════════════════════════════════════════════════════
# Gap - What's Different?
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Gap:
    """The difference between what is and what should be."""
    # Semantic differences
    colour_changes: List[str] = field(default_factory=list)
    size_changes: List[str] = field(default_factory=list)
    position_changes: List[str] = field(default_factory=list)
    structural_changes: List[str] = field(default_factory=list)

    # Energy difference
    inp_tax: float = 0.0
    out_tax: float = 0.0
    delta_tax: float = 0.0

    # Summary
    summary: str = ""


def analyse_gap(inp_percept: Percept, out_percept: Percept,
                 inp_grid: Grid, out_grid: Grid) -> Gap:
    """Analyse the gap between input and output."""
    gap = Gap()
    gap.inp_tax = inp_percept.tax
    gap.out_tax = out_percept.tax
    gap.delta_tax = gap.out_tax - gap.inp_tax

    # Colour changes
    inp_colours = Counter(o.colour for o in inp_percept.objects)
    out_colours = Counter(o.colour for o in out_percept.objects)
    for colour in set(inp_colours.keys()) | set(out_colours.keys()):
        inp_count = inp_colours.get(colour, 0)
        out_count = out_colours.get(colour, 0)
        if inp_count != out_count:
            gap.colour_changes.append(f"colour {colour}: {inp_count} → {out_count} objects")

    # Size changes
    inp_sizes = sorted([o.size for o in inp_percept.objects], reverse=True)
    out_sizes = sorted([o.size for o in out_percept.objects], reverse=True)
    if inp_sizes != out_sizes:
        gap.size_changes.append(f"sizes: {inp_sizes[:5]} → {out_sizes[:5]}")

    # Structural changes
    if inp_percept.n_objects != out_percept.n_objects:
        gap.structural_changes.append(f"objects: {inp_percept.n_objects} → {out_percept.n_objects}")
    if inp_percept.density != out_percept.density:
        gap.structural_changes.append(f"density: {inp_percept.density:.2f} → {out_percept.density:.2f}")

    # Summary
    parts = []
    if gap.colour_changes:
        parts.append(f"{len(gap.colour_changes)} colour changes")
    if gap.size_changes:
        parts.append("size changes")
    if gap.structural_changes:
        parts.append(f"{len(gap.structural_changes)} structural changes")
    gap.summary = ", ".join(parts) if parts else "no changes"

    return gap


# ═══════════════════════════════════════════════════════════════════════════════
# Proposal - How Do I Get There?
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Proposal:
    """The mind's proposal for how to transform input → output."""
    # The proposed transformation
    strategy: str = ""
    strategy_name: str = ""

    # Lingo expression
    lingo: str = ""
    human: str = ""

    # Confidence
    confidence: float = 0.0

    # Inspection results
    verified: bool = False
    inspection_notes: List[str] = field(default_factory=list)


def propose_transformation(task: ARCTask, goal: Goal, gap: Gap) -> List[Proposal]:
    """
    Propose transformations to close the gap.

    The mind thinks about what needs to happen and proposes actions.
    """
    proposals = []

    # Proposal 1: Conditional pattern (from conditional lobe)
    pattern = induce_conditional_pattern(task)
    if pattern:
        p = Proposal(
            strategy="conditional",
            strategy_name=f"conditional_{pattern.condition_type}",
            lingo=pattern.describe_in_lingo(),
            human=pattern.describe_in_human(),
            confidence=pattern.confidence,
        )
        proposals.append(p)

    # Proposal 2: Settlement dynamics (from substrate mind)
    from substrate_mind import learn_settlement_dynamics
    dynamics = learn_settlement_dynamics(task)
    if dynamics.gravity_detected:
        proposals.append(Proposal(
            strategy="settlement",
            strategy_name="settlement_gravity",
            lingo="COMPACTION_FLOW",
            human="compact non-zero cells to bottom (gravity)",
            confidence=0.9,
        ))
    if dynamics.component_size_threshold:
        proposals.append(Proposal(
            strategy="settlement",
            strategy_name="settlement_component_cond",
            lingo=f"CHARGE_SWAP IF NODE_CARDINALITY ≥ {dynamics.component_size_threshold}",
            human=f"change colour if component size ≥ {dynamics.component_size_threshold}",
            confidence=0.8,
        ))
    if dynamics.colour_map:
        cm = dynamics.colour_map
        proposals.append(Proposal(
            strategy="settlement",
            strategy_name="settlement_colour_map",
            lingo=f"CHARGE_SWAP({cm})",
            human=f"apply colour map {cm}",
            confidence=0.7,
        ))

    # Proposal 3: Toolkit solvers
    from v062_unified_learning import (
        gravity_down, local_swap, colour_center_fill,
        column_rank_fill, marker_fill_85, cond_recolour,
    )
    from v032_distance_rule import try_distance_diagonal_rule
    from v065_ubp_glm import learn_multi_interior_fill

    toolkit = [
        ("toolkit_gravity", gravity_down, "COMPACTION_FLOW", "gravity down"),
        ("toolkit_swap", local_swap, "CHARGE_SWAP", "swap colours in component"),
        ("toolkit_center", colour_center_fill, "CENTROID_SHIFT", "project centres to bottom"),
        ("toolkit_col_rank", column_rank_fill, "COLUMN_RANK", "fill by column rank"),
        ("toolkit_marker", marker_fill_85, "MARKER_FILL", "fill rows with markers"),
    ]

    for name, fn, lingo, human in toolkit:
        result = fn(task.test[0].input)
        if result:
            proposals.append(Proposal(
                strategy="toolkit",
                strategy_name=name,
                lingo=lingo,
                human=human,
                confidence=0.6,
            ))

    # Interior fill
    fn = learn_multi_interior_fill(task)
    if fn:
        result = fn(task.test[0].input)
        if result:
            proposals.append(Proposal(
                strategy="toolkit",
                strategy_name="toolkit_interior",
                lingo="REGION_FILL(interior)",
                human="fill enclosed regions",
                confidence=0.6,
            ))

    # Distance rule
    dist = try_distance_diagonal_rule(task)
    if dist:
        proposals.append(Proposal(
            strategy="toolkit",
            strategy_name="toolkit_distance",
            lingo="DISTANCE_FILL",
            human="fill by distance rule",
            confidence=0.5,
        ))
    
    # Conditional recolour sweep
    from conditional_lobe import extract_objects as eo
    test = task.test[0].input
    objs = eo(test)
    max_size = max((o.size for o in objs), default=0)
    for threshold in range(2, max(max_size + 1, 10)):
        for outcome in range(1, 10):
            result = cond_recolour(test, threshold, outcome)
            if result:
                proposals.append(Proposal(
                    strategy="toolkit",
                    strategy_name=f"toolkit_cond_{threshold}_{outcome}",
                    lingo=f"CHARGE_SWAP IF NODE_CARDINALITY ≥ {threshold}",
                    human=f"conditional recolour (threshold={threshold}, outcome={outcome})",
                    confidence=0.5,
                ))
                break
        break
    
    # Cross shift
    from substrate_mind import _cross_shift
    cross = _cross_shift(test)
    if cross:
        proposals.append(Proposal(
            strategy="toolkit",
            strategy_name="toolkit_cross",
            lingo="CENTROID_SHIFT(marker)",
            human="cross shift by marker count",
            confidence=0.5,
        ))
    
    return proposals


# ═══════════════════════════════════════════════════════════════════════════════
# Inspection - Does My Proposal Work?
# ═══════════════════════════════════════════════════════════════════════════════

def inspect_proposal(task: ARCTask, proposal: Proposal) -> Proposal:
    """
    Inspect a proposal: verify it on train pairs and explain why it works or fails.
    """
    # Special case: distance_rule uses v032's own verification
    if proposal.strategy_name == "toolkit_distance":
        from v032_distance_rule import try_distance_diagonal_rule
        result = try_distance_diagonal_rule(task)
        proposal.verified = result is not None
        if proposal.verified:
            proposal.inspection_notes.append("  VERIFIED by v032 distance rule")
        else:
            proposal.inspection_notes.append("  FAILED: distance rule doesn't match")
        return proposal
    
    # Apply the proposal to each train pair
    checked = 0
    passed = 0
    total_diffs = 0

    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue

        result = _apply_proposal(task, proposal, pair.input)
        if result is None:
            proposal.inspection_notes.append(f"  Pair: strategy returned None")
            continue

        if result.cells == pair.output.cells:
            passed += 1
            proposal.inspection_notes.append(f"  Pair: ✓ MATCH")
        else:
            diff = sum(1 for r in range(pair.input.height) for c in range(pair.input.width)
                      if result.cells[r][c] != pair.output.cells[r][c])
            total_diffs += diff
            proposal.inspection_notes.append(f"  Pair: ✗ {diff} diffs")
        checked += 1

    proposal.verified = (passed == checked and checked > 0)

    if proposal.verified:
        proposal.inspection_notes.append(f"  VERIFIED: {passed}/{checked} pairs match")
    else:
        proposal.inspection_notes.append(f"  FAILED: {passed}/{checked} pairs match, {total_diffs} total diffs")

    return proposal


def _apply_proposal(task: ARCTask, proposal: Proposal, grid: Grid) -> Optional[Grid]:
    """Apply a proposal to a grid."""
    from substrate_mind import apply_to_train, learn_settlement_dynamics
    from conditional_lobe import apply_conditional_pattern, induce_conditional_pattern

    if proposal.strategy == "conditional":
        pattern = induce_conditional_pattern(task)
        if pattern:
            return apply_conditional_pattern(grid, pattern)
        return None

    if proposal.strategy == "settlement":
        dynamics = learn_settlement_dynamics(task)
        from substrate_mind import apply_to_train as at
        return at(task, proposal.strategy_name, grid, dynamics)

    if proposal.strategy == "toolkit":
        # Special: distance rule
        if proposal.strategy_name == "toolkit_distance":
            from v032_distance_rule import try_distance_diagonal_rule
            result = try_distance_diagonal_rule(task)
            if result:
                return result[0]
            return None
        
        from substrate_mind import apply_to_train as at
        dynamics = learn_settlement_dynamics(task)
        return at(task, proposal.strategy_name, grid, dynamics)

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# The Complete Reasoning Cycle
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ReasoningCycle:
    """The mind's complete reasoning about a task."""
    # Step 1: Perception
    input_percept: Optional[Percept] = None
    output_percept: Optional[Percept] = None

    # Step 2: Goal
    goal: Optional[Goal] = None

    # Step 3: Gap
    gap: Optional[Gap] = None

    # Step 4: Proposals
    proposals: List[Proposal] = field(default_factory=list)

    # Step 5: Best proposal
    best_proposal: Optional[Proposal] = None

    # Result
    solved: bool = False
    solution: Optional[Grid] = None


def reason_about_task(task: ARCTask) -> ReasoningCycle:
    """
    The mind's complete reasoning cycle about a task.

    1. PERCEIVE: What do I see?
    2. GOAL: What needs to happen?
    3. GAP: What's different?
    4. PROPOSE: How do I get there?
    5. INSPECT: Does my proposal work?
    """
    cycle = ReasoningCycle()

    # Step 1: Perceive
    cycle.input_percept = perceive_grid(task.test[0].input)
    pair0 = task.train[0]
    cycle.output_percept = perceive_grid(pair0.output)

    # Step 2: Goal
    cycle.goal = infer_goal(task)

    # Step 3: Gap
    cycle.gap = analyse_gap(cycle.input_percept, cycle.output_percept,
                            task.test[0].input, pair0.output)

    # Step 4: Propose
    cycle.proposals = propose_transformation(task, cycle.goal, cycle.gap)

    # Step 5: Inspect each proposal
    for proposal in cycle.proposals:
        inspect_proposal(task, proposal)
        if proposal.verified:
            cycle.best_proposal = proposal
            # Apply to test input
            result = _apply_proposal(task, proposal, task.test[0].input)
            if result:
                cycle.solution = result
                cycle.solved = True
            break

    return cycle


# ═══════════════════════════════════════════════════════════════════════════════
# Report - The Mind's Complete Reasoning
# ═══════════════════════════════════════════════════════════════════════════════

def reasoning_report(task: ARCTask) -> str:
    """Generate the mind's complete reasoning report."""
    cycle = reason_about_task(task)

    lines = []
    lines.append(f"╔══════════════════════════════════════════════════════════════╗")
    lines.append(f"║  REASONING CYCLE: {task.name:<42} ║")
    lines.append(f"╚══════════════════════════════════════════════════════════════╝")

    # Step 1: Perceive
    lines.append(f"")
    lines.append(f"┌─── STEP 1: PERCEIVE ───")
    lines.append(f"  Input:  {cycle.input_percept.human_description}")
    lines.append(f"  Output: {cycle.output_percept.human_description}")
    lines.append(f"  Input Lingo:  {cycle.input_percept.lingo_description}")
    lines.append(f"  Output Lingo: {cycle.output_percept.lingo_description}")

    # Step 2: Goal
    lines.append(f"")
    lines.append(f"┌─── STEP 2: GOAL ───")
    lines.append(f"  Type: {cycle.goal.transformation_type}")
    if cycle.goal.objects_should_change:
        lines.append(f"  Should change:")
        for desc in cycle.goal.objects_should_change[:5]:
            lines.append(f"    • {desc}")
    if cycle.goal.objects_should_stay:
        lines.append(f"  Should stay:")
        for desc in cycle.goal.objects_should_stay[:3]:
            lines.append(f"    • {desc}")

    # Step 3: Gap
    lines.append(f"")
    lines.append(f"┌─── STEP 3: GAP ───")
    lines.append(f"  Summary: {cycle.gap.summary}")
    lines.append(f"  ΔTAX: {cycle.gap.delta_tax:+.3f}")
    if cycle.gap.colour_changes:
        lines.append(f"  Colour changes:")
        for desc in cycle.gap.colour_changes[:5]:
            lines.append(f"    • {desc}")

    # Step 4: Proposals
    lines.append(f"")
    lines.append(f"┌─── STEP 4: PROPOSE ───")
    for i, proposal in enumerate(cycle.proposals[:5]):
        lines.append(f"  Proposal {i+1}: {proposal.strategy_name}")
        lines.append(f"    Lingo: {proposal.lingo}")
        lines.append(f"    Human: {proposal.human}")
        lines.append(f"    Confidence: {proposal.confidence:.2f}")

    # Step 5: Inspection
    lines.append(f"")
    lines.append(f"┌─── STEP 5: INSPECT ───")
    for i, proposal in enumerate(cycle.proposals[:5]):
        status = "✓ VERIFIED" if proposal.verified else "✗ FAILED"
        lines.append(f"  Proposal {i+1} ({proposal.strategy_name}): {status}")
        for note in proposal.inspection_notes[:3]:
            lines.append(f"    {note}")

    # Result
    lines.append(f"")
    lines.append(f"┌─── RESULT ───")
    if cycle.solved:
        lines.append(f"  ✓ SOLVED by {cycle.best_proposal.strategy_name}")
        lines.append(f"  Lingo: {cycle.best_proposal.lingo}")
    else:
        lines.append(f"  ✗ NOT SOLVED")
        lines.append(f"  All proposals failed inspection.")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark
# ═══════════════════════════════════════════════════════════════════════════════

def benchmark(batch_dir: str) -> Dict[str, Any]:
    files = sorted(f for f in os.listdir(batch_dir) if f.endswith(".json"))
    results = []
    solver_counts = Counter()
    t0 = time.time()
    for fname in files:
        task = load_task(os.path.join(batch_dir, fname), name=os.path.splitext(fname)[0])
        try:
            cycle = reason_about_task(task)
            solved = cycle.solved
            solver = cycle.best_proposal.strategy_name if cycle.best_proposal else "none"
        except Exception:
            solved = False
            solver = "error"
        results.append({"task_id": task.name, "solved": solved, "solver": solver})
        if solved:
            solver_counts[solver] += 1
    elapsed = time.time() - t0
    solved_n = sum(1 for r in results if r["solved"])
    return {
        "solved": solved_n, "total": len(results),
        "pct": round(100.0 * solved_n / max(1, len(results)), 1),
        "elapsed": round(elapsed, 1),
        "solver_counts": dict(solver_counts),
        "results": results,
    }


def main():
    batch = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "training")

    print("=" * 72)
    print(" THE MIND'S COMPLETE REASONING CYCLE")
    print("=" * 72)
    print()

    # Show full reasoning for tasks the mind solves itself
    for tid in ['1e0a9b12', '45737921', 'ae58858e']:
        task = load_task(f"{batch}/{tid}.json", name=tid)
        print(reasoning_report(task))
        print()

    # Benchmark
    summary = benchmark(batch)
    print("=" * 72)
    print(f" RESULT: {summary['solved']}/{summary['total']} ({summary['pct']}%)")
    print(f" Time: {summary['elapsed']}s")
    print("=" * 72)
    for r in summary["results"]:
        if r["solved"]:
            print(f"  ✓ {r['task_id']}: {r['solver']}")
    print(f"\n  Solvers:")
    for s, c in sorted(summary["solver_counts"].items(), key=lambda kv: -kv[1]):
        print(f"    {s}: {c}")

    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "REPORTS", "reasoning_cycle_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Report: {report_path}")


if __name__ == "__main__":
    main()
