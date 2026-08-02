"""
thoughts_layer.py — the cortex's thought-writing layer
=======================================================

The user's directive: "What if we have a layer for the Cortex where it
puts its 'thoughts' together (writes actual text and numbers) then that
becomes the thought to consider, it could have n thoughts."

This module lets the cortex WRITE its reasoning as structured text +
numbers.  Each thought is a self-contained observation about the task.
The cortex can have N thoughts, and each thought can reference or build
on previous thoughts.

A thought is structured as:
  THOUGHT #n
  Observation: <what the cortex sees>
  Pattern: <what pattern it noticed>
  Hypothesis: <what it thinks the rule is>
  Prediction: <what it predicts for test>
  Confidence: <0-1>
  Evidence: <list of (train_pair_idx, cell, support)>

The cortex generates thoughts by:
  1. Looking at each train pair and writing what it sees
  2. Comparing across train pairs to find patterns
  3. Forming hypotheses about the transformation rule
  4. Using hypotheses to predict the test output
  5. Checking predictions against train (hard gate)

Multiple thoughts compete.  The cortex tries each thought's prediction
against train; the first one that passes wins.

Why this matters
----------------
The previous cortex modules derived rules implicitly — the rules existed
in code but couldn't be inspected or composed.  The thoughts layer makes
reasoning EXPLICIT and COMPOSABLE:

  - Explicit: each thought is a text/number structure that can be printed
  - Composable: thought N+1 can reference thought N's observation
  - Debuggable: we can see exactly what the cortex was thinking
  - Multi-step: the cortex can have a chain of thoughts, each refining
    the previous

This is the "language machine" the user has been asking for — the cortex
literally writes its thoughts in a structured language.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set
from fractions import Fraction
from collections import defaultdict, Counter
import sys, os, math

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_THIS_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask
from vendor.cortex_v2 import (
    CARDINAL_DIRS, DIAGONAL_DIRS, ALL_DIRS, _has_in_directions,
)
from vendor.displacement_extrapolation import (
    build_curve_from_train, DisplacementCurve,
)


# ══════════════════════════════════════════════════════════════════════════════
# Thought data structure
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Thought:
    """A single thought from the cortex.

    Each thought has:
      - id: thought number (1, 2, 3, ...)
      - observation: what the cortex sees (text)
      - pattern: what pattern it noticed (text)
      - hypothesis: the proposed rule (text + structured data)
      - prediction: the predicted test output (Grid)
      - confidence: 0-1
      - evidence: list of (train_pair_idx, n_supporting_cells)
      - references: list of thought ids this thought builds on
    """
    id: int
    observation: str = ""
    pattern: str = ""
    hypothesis: str = ""
    hypothesis_data: Dict[str, Any] = field(default_factory=dict)
    prediction: Optional[Grid] = None
    confidence: float = 0.0
    evidence: List[Tuple[int, int]] = field(default_factory=list)  # (pair_idx, n_cells)
    references: List[int] = field(default_factory=list)
    passes_train: bool = False

    def to_text(self) -> str:
        """Render the thought as readable text."""
        lines = [
            f"THOUGHT #{self.id}",
            f"  Observation: {self.observation}",
            f"  Pattern: {self.pattern}",
            f"  Hypothesis: {self.hypothesis}",
        ]
        if self.hypothesis_data:
            for k, v in self.hypothesis_data.items():
                lines.append(f"    {k}: {v}")
        lines.append(f"  Confidence: {self.confidence:.2f}")
        lines.append(f"  Passes train: {self.passes_train}")
        if self.evidence:
            lines.append(f"  Evidence: {self.evidence}")
        if self.references:
            lines.append(f"  Builds on: thoughts {self.references}")
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# Thought generators — each produces one or more thoughts
# ══════════════════════════════════════════════════════════════════════════════

def thought_global_recolour(task: ARCTask, thought_id: int) -> Optional[Thought]:
    """Thought: 'The transformation is a global colour mapping.'

    Looks at all train pairs, finds the most common (old → new) mapping,
    and predicts the test output by applying that mapping.
    """
    colour_targets: Dict[int, List[int]] = defaultdict(list)
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                old = pair.input.cells[r][c]
                new = pair.output.cells[r][c]
                if old != new:
                    colour_targets[old].append(new)

    if not colour_targets:
        return None

    mapping = {}
    for old, targets in colour_targets.items():
        mapping[old] = Counter(targets).most_common(1)[0][0]

    def apply(grid: Grid) -> Grid:
        return Grid([[mapping.get(v, v) for v in row] for row in grid.cells])

    # Verify against train
    passes = all(apply(p.input) == p.output for p in task.train)
    pred = apply(task.test[0].input) if passes else None

    return Thought(
        id=thought_id,
        observation=f"{len(colour_targets)} colours change across {len(task.train)} train pairs",
        pattern="Global colour mapping (position-independent)",
        hypothesis=f"Apply mapping {mapping} to every cell",
        hypothesis_data={"mapping": mapping},
        prediction=pred,
        confidence=1.0 if passes else 0.3,
        evidence=[(i, sum(1 for r in range(p.input.height) for c in range(p.input.width)
                           if p.input.cells[r][c] in mapping))
                  for i, p in enumerate(task.train)],
        passes_train=passes,
    )


def thought_relational_trigger(task: ARCTask, thought_id: int) -> Optional[Thought]:
    """Thought: 'Colour A changes when it has trigger T in direction D.'

    Finds the (A, T, D, target) quadruple that best explains the changes.
    """
    # Collect changing cells per (A, target) pair
    changing: Dict[Tuple[int, int], List[Tuple[Grid, int, int]]] = defaultdict(list)
    for pi, pair in enumerate(task.train):
        if pair.input.shape != pair.output.shape:
            continue
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                old = pair.input.cells[r][c]
                new = pair.output.cells[r][c]
                if old != new:
                    changing[(old, new)].append((pair.input, r, c))

    if not changing:
        return None

    # For each (A, target), find the best (T, D) that separates changed from unchanged
    best_thoughts = []
    for (a, target), changed_cells in changing.items():
        if len(changed_cells) < 2:
            continue

        # Find trigger colours
        triggers = set()
        for grid, r, c in changed_cells:
            for _, (dr, dc) in ALL_DIRS.items():
                nr, nc = r + dr, c + dc
                if 0 <= nr < grid.height and 0 <= nc < grid.width:
                    n_colour = grid.cells[nr][nc]
                    if n_colour != a and n_colour != 0:
                        triggers.add(n_colour)

        # For each trigger, find the best direction
        for t in triggers:
            # Count changed cells with T in each direction
            changed_in_dir = {d: sum(1 for grid, r, c in changed_cells
                                       if _has_in_directions(grid, r, c, t, {d: ALL_DIRS[d]}))
                              for d in ALL_DIRS}
            # Find direction with most changed cells
            best_dir = max(changed_in_dir, key=changed_in_dir.get)
            best_count = changed_in_dir[best_dir]

            if best_count < len(changed_cells) * 0.5:
                continue

            # Check unchanged cells
            unchanged = []
            for pi, pair in enumerate(task.train):
                if pair.input.shape != pair.output.shape:
                    continue
                for r in range(pair.input.height):
                    for c in range(pair.input.width):
                        if pair.input.cells[r][c] == a and pair.output.cells[r][c] == a:
                            unchanged.append((pair.input, r, c))
            unchanged_in_best_dir = sum(1 for grid, r, c in unchanged
                                          if _has_in_directions(grid, r, c, t, {best_dir: ALL_DIRS[best_dir]}))

            if unchanged_in_best_dir > len(unchanged) * 0.3:
                continue  # too many false positives

            # Build a mapping for this trigger
            mapping = {t: target}

            # Apply: for each cell of colour A with T in best_dir, set to target
            def apply(grid: Grid, a=a, t=t, d=best_dir, target=target) -> Grid:
                h, w = grid.shape
                out = [row[:] for row in grid.cells]
                dr, dc = ALL_DIRS[d]
                for r in range(h):
                    for c in range(w):
                        if grid.cells[r][c] != a:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] == t:
                            out[r][c] = target
                return Grid(out)

            passes = all(apply(p.input) == p.output for p in task.train)
            pred = apply(task.test[0].input) if passes else None

            best_thoughts.append(Thought(
                id=thought_id,
                observation=f"Colour {a} changes to {target} in {len(changed_cells)} cells",
                pattern=f"Trigger: colour {t} in direction {best_dir}",
                hypothesis=f"If cell is {a} and has {t} in {best_dir}, set to {target}",
                hypothesis_data={
                    "input_colour": a, "trigger_colour": t,
                    "direction": best_dir, "target_colour": target,
                    "mapping": mapping,
                },
                prediction=pred,
                confidence=best_count / len(changed_cells),
                evidence=[(i, best_count) for i in range(len(task.train))],
                passes_train=passes,
            ))

    if not best_thoughts:
        return None
    # Return the thought with highest confidence
    return max(best_thoughts, key=lambda t: t.confidence)


def thought_meta_rule(task: ARCTask, thought_id: int) -> Optional[Thought]:
    """Thought: 'Colour A changes based on trigger T, with extrapolation for unseen T.'

    Combines the relational condition with displacement-curve extrapolation.
    """
    from vendor.meta_rule import derive_meta_rules, compute_trigger_distances

    rules = derive_meta_rules(task)
    if not rules:
        return None

    # Use the first rule (highest priority)
    rule = rules[0]

    # Build displacement curve for extrapolation
    curve = build_curve_from_train(task)

    # Apply with extrapolation
    train_triggers = set(rule.mapping.keys())
    test_input = task.test[0].input

    def apply(grid: Grid) -> Grid:
        h, w = grid.shape
        out = [row[:] for row in grid.cells]
        trigger_dists = compute_trigger_distances(grid, train_triggers, h, w)
        for r in range(h):
            for c in range(w):
                applies, trigger = rule.applies_to(grid, r, c)
                if applies:
                    if trigger in rule.mapping:
                        out[r][c] = rule.mapping[trigger]
                    else:
                        # Extrapolate via displacement curve
                        target, conf = curve.extrapolate_target(trigger, h, w)
                        if target is not None and conf > 0.2:
                            out[r][c] = target
        return Grid(out)

    passes = all(apply(p.input) == p.output for p in task.train)
    pred = apply(test_input) if passes else None

    return Thought(
        id=thought_id,
        observation=f"Colour {rule.input_colour} changes based on trigger colours {list(rule.mapping.keys())}",
        pattern=f"Relational: has trigger in {rule.has_dirs}, NOT in {rule.not_dirs}",
        hypothesis=f"If cell is {rule.input_colour} and has trigger T in {rule.has_dirs} (not {rule.not_dirs}), set to mapping[T] or extrapolate",
        hypothesis_data={
            "input_colour": rule.input_colour,
            "has_dirs": rule.has_dirs,
            "not_dirs": rule.not_dirs,
            "mapping": rule.mapping,
            "extrapolation": "displacement_curve",
        },
        prediction=pred,
        confidence=0.8 if passes else 0.4,
        evidence=[(i, 1) for i in range(len(task.train))],
        passes_train=passes,
    )


def thought_arithmetic_pattern(task: ARCTask, thought_id: int) -> Optional[Thought]:
    """Thought: 'The target is an arithmetic function of the trigger.'

    Looks for patterns like target = (trigger + k) mod 10, target = 10 - trigger, etc.
    """
    # Collect (trigger, target) pairs
    pairs = []
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                old = pair.input.cells[r][c]
                new = pair.output.cells[r][c]
                if old != new:
                    # Find trigger
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < pair.input.height and 0 <= nc < pair.input.width:
                                n_colour = pair.input.cells[nr][nc]
                                if n_colour != old and n_colour != 0:
                                    pairs.append((n_colour, new))

    if len(pairs) < 2:
        return None

    # Try arithmetic patterns
    patterns = []
    # Pattern 1: target = (trigger + k) mod 10
    for k in range(10):
        matches = sum(1 for t, c in pairs if (t + k) % 10 == c)
        if matches == len(pairs):
            patterns.append(("add_k", k))
    # Pattern 2: target = (trigger - k) mod 10
    for k in range(10):
        matches = sum(1 for t, c in pairs if (t - k) % 10 == c)
        if matches == len(pairs):
            patterns.append(("sub_k", k))
    # Pattern 3: target = (10 - trigger) mod 10
    matches = sum(1 for t, c in pairs if (10 - t) % 10 == c)
    if matches == len(pairs):
        patterns.append(("complement", 0))
    # Pattern 4: target = (trigger * k) mod 10
    for k in range(1, 10):
        matches = sum(1 for t, c in pairs if (t * k) % 10 == c)
        if matches == len(pairs):
            patterns.append(("mul_k", k))

    if not patterns:
        return None

    # Use the first pattern
    pat_type, k = patterns[0]

    def apply(grid: Grid) -> Grid:
        h, w = grid.shape
        out = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                old = grid.cells[r][c]
                # Find trigger
                trigger = None
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            n_colour = grid.cells[nr][nc]
                            if n_colour != old and n_colour != 0:
                                trigger = n_colour
                                break
                    if trigger is not None:
                        break
                if trigger is not None:
                    if pat_type == "add_k":
                        out[r][c] = (trigger + k) % 10
                    elif pat_type == "sub_k":
                        out[r][c] = (trigger - k) % 10
                    elif pat_type == "complement":
                        out[r][c] = (10 - trigger) % 10
                    elif pat_type == "mul_k":
                        out[r][c] = (trigger * k) % 10
        return Grid(out)

    passes = all(apply(p.input) == p.output for p in task.train)
    pred = apply(task.test[0].input) if passes else None

    pat_str = f"{pat_type}({k})" if pat_type != "complement" else "complement"
    return Thought(
        id=thought_id,
        observation=f"{len(pairs)} (trigger, target) pairs found",
        pattern=f"Arithmetic: target = {pat_str}(trigger)",
        hypothesis=f"Apply {pat_str} to the trigger colour",
        hypothesis_data={"pattern": pat_type, "k": k, "pairs": pairs},
        prediction=pred,
        confidence=1.0 if passes else 0.5,
        evidence=[(i, len(pairs)) for i in range(len(task.train))],
        passes_train=passes,
    )


# ══════════════════════════════════════════════════════════════════════════════
# The thoughts layer — generates and evaluates all thoughts
# ══════════════════════════════════════════════════════════════════════════════

def generate_thoughts(task: ARCTask) -> List[Thought]:
    """Generate all thoughts for a task.

    Each thought generator produces one thought.  The cortex considers
    all of them and picks the best (highest confidence among those that
    pass train).

    The top-down coherence thought is generated LAST, using the best
    bottom-up thought's prediction as its base.  This allows the
    coherence thought to REFINE the bottom-up prediction.
    """
    thoughts = []
    thought_id = 1

    generators = [
        ("global_recolour", thought_global_recolour),
        ("relational_trigger", thought_relational_trigger),
        ("meta_rule", thought_meta_rule),
        ("arithmetic_pattern", thought_arithmetic_pattern),
    ]

    for name, gen in generators:
        try:
            thought = gen(task, thought_id)
            if thought is not None:
                thoughts.append(thought)
                thought_id += 1
        except Exception as e:
            # Thought generation failed — skip
            pass

    # Generate the top-down coherence thought, using the best bottom-up
    # prediction as its base
    try:
        from vendor.coherence_thought import thought_top_down_coherence
        # Find the best bottom-up prediction (highest confidence that passes train)
        best_bottom_up = None
        best_conf = -1
        for t in thoughts:
            if t.passes_train and t.prediction is not None and t.confidence > best_conf:
                best_bottom_up = t.prediction
                best_conf = t.confidence
        # If no bottom-up passes train, use the test input as base
        base = best_bottom_up if best_bottom_up is not None else task.test[0].input
        coherence_thought = thought_top_down_coherence(task, thought_id, base_prediction=base)
        if coherence_thought is not None:
            # Reference the bottom-up thought it built on
            if best_bottom_up is not None:
                for t in thoughts:
                    if t.prediction == best_bottom_up:
                        coherence_thought.references = [t.id]
                        break
            thoughts.append(coherence_thought)
            thought_id += 1
    except Exception:
        pass

    return thoughts


def select_best_thought(thoughts: List[Thought]) -> Optional[Thought]:
    """Select the best thought.

    Preference order:
      1. Thoughts that pass train (hard gate)
      2. Among those, prefer the coherence thought if it improved over its base
      3. Otherwise, highest confidence
      4. If none pass train, return None
    """
    passing = [t for t in thoughts if t.passes_train and t.prediction is not None]
    if not passing:
        return None

    # Check if the coherence thought improved over its base
    coherence_thoughts = [t for t in passing if "coherence" in t.hypothesis.lower()]
    if coherence_thoughts:
        # Find the coherence thought with the best improvement
        best_coherence = max(coherence_thoughts,
                              key=lambda t: t.hypothesis_data.get("improvement", 0))
        if best_coherence.hypothesis_data.get("improvement", 0) > 0.05:
            # The coherence thought improved by more than 5% — prefer it
            return best_coherence

    # Otherwise, highest confidence
    return max(passing, key=lambda t: t.confidence)


def predict(task: ARCTask) -> Tuple[Optional[Grid], str, Dict[str, Any]]:
    """The thoughts-layer prediction pipeline.

    Generates N thoughts, selects the best one that passes train.
    """
    thoughts = generate_thoughts(task)
    best = select_best_thought(thoughts)

    if best is not None:
        return best.prediction, f"thought_{best.id}", {
            "n_thoughts": len(thoughts),
            "thoughts_summary": [
                {"id": t.id, "hypothesis": t.hypothesis,
                 "confidence": t.confidence, "passes_train": t.passes_train}
                for t in thoughts
            ],
            "selected_thought": best.to_text(),
        }

    return None, "none", {
        "n_thoughts": len(thoughts),
        "thoughts_summary": [
            {"id": t.id, "hypothesis": t.hypothesis,
             "confidence": t.confidence, "passes_train": t.passes_train}
            for t in thoughts
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# Self-test
# ══════════════════════════════════════════════════════════════════════════════

def _self_test():
    print("Thoughts Layer self-test")
    print("=" * 60)

    from arc_loader import TrainPair, TestInput

    # Test: recolour task
    print("\n[Test 1] Global recolour")
    inp = Grid([[1, 2, 0], [1, 2, 0]])
    out = Grid([[2, 3, 0], [2, 3, 0]])
    task = ARCTask(name="recolour",
                   train=[TrainPair(input=inp, output=out)],
                   test=[TestInput(input=inp, expected_output=out)])
    pred, src, diag = predict(task)
    print(f"  src={src}")
    print(f"  pred: {pred.cells if pred else None}")
    print(f"  correct: {pred == out if pred else False}")
    if diag.get("selected_thought"):
        print(f"  thought:\n{diag['selected_thought']}")

    # Test: relational trigger
    print("\n[Test 2] Relational trigger")
    inp2 = Grid([
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
        [6, 7, 6, 7, 6],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ])
    out2 = Grid([
        [7, 7, 7, 7, 7],
        [7, 2, 7, 2, 7],
        [6, 7, 6, 7, 6],
        [7, 7, 7, 7, 7],
        [7, 7, 7, 7, 7],
    ])
    task2 = ARCTask(name="trigger",
                    train=[TrainPair(input=inp2, output=out2)],
                    test=[TestInput(input=inp2, expected_output=out2)])
    pred2, src2, diag2 = predict(task2)
    print(f"  src={src2}")
    print(f"  correct: {pred2 == out2 if pred2 else False}")
    if diag2.get("selected_thought"):
        print(f"  thought:\n{diag2['selected_thought']}")

    print("\n" + "=" * 60)
    print("Self-test complete.")


if __name__ == "__main__":
    _self_test()
