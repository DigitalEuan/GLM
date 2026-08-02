"""
taste_generative.py — taste-driven candidate generation
========================================================

The taste sense becomes GENERATIVE: for each test cell, find the train
cell with the most similar taste (local composition) and apply that
cell's transformation.

This is a different kind of k-arm:
  - The TOUCH arm uses 24-bit address Hamming distance to find neighbours
  - The TASTE arm uses local composition similarity (histogram + texture)

The taste arm catches transformations the touch arm misses, because
two cells can have very different addresses but identical local
composition — they're "made of the same stuff" and should transform
the same way.

For each test cell:
  1. Compute its taste (3×3 neighbourhood histogram + texture)
  2. Find the K train cells with the most similar taste
  3. Vote on the output colour, weighted by taste similarity
  4. Apply the voted colour

The taste arm runs IN PARALLEL with the touch arm.  When they agree,
confidence is high.  When they disagree, the taste arm often wins
because it captures composition that addresses miss.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict, Counter
from fractions import Fraction
import sys, os, math

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_THIS_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask
from vendor.smell_taste_sense import (
    TasteProfile, taste_region, taste_distance, taste_similarity,
)
from generative.hex_learner import address_cell, address_grid


# ══════════════════════════════════════════════════════════════════════════════
# Taste-driven prediction
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TasteArmConfig:
    """Configuration for the taste arm."""
    radius: int = 1              # neighbourhood radius (1 = 3×3, 2 = 5×5)
    k: int = 5                   # number of nearest train cells to consider
    min_similarity: float = 0.3  # minimum taste similarity to contribute
    uncertainty_threshold: float = 0.5  # below this, fall back


def collect_train_tastes(task: ARCTask) -> List[Tuple[int, int, int, int, TasteProfile]]:
    """Collect (row, col, input_colour, output_colour, taste) for every train cell.

    Only collects from train pairs where input.shape == output.shape.
    """
    entries = []
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        h, w = pair.input.shape
        for r in range(h):
            for c in range(w):
                taste = taste_region(pair.input, r, c, radius=1)
                in_colour = pair.input.cells[r][c]
                out_colour = pair.output.cells[r][c]
                entries.append((r, c, in_colour, out_colour, taste))
    return entries


def predict_via_taste(task: ARCTask,
                       config: TasteArmConfig = TasteArmConfig()
                       ) -> Optional[Grid]:
    """Predict test output using the taste arm.

    For each test cell:
      1. Compute its taste (3×3 neighbourhood composition)
      2. Find the K train cells with the most similar taste
      3. Vote on output colour, weighted by taste similarity
      4. Apply the voted colour

    Falls back to input colour if no train cell has similar taste.
    """
    test_input = task.test[0].input
    train_entries = collect_train_tastes(task)

    if not train_entries:
        return None

    h, w = test_input.shape
    out_cells = []

    for r in range(h):
        row = []
        for c in range(w):
            test_taste = taste_region(test_input, r, c, config.radius)

            # Compute taste similarity to every train cell
            similarities = []
            for tr, tc, in_col, out_col, train_taste in train_entries:
                sim = taste_similarity(test_taste, train_taste)
                if sim >= config.min_similarity:
                    similarities.append((sim, in_col, out_col))

            if not similarities:
                # No similar taste — fall back to input colour
                row.append(test_input.cells[r][c])
                continue

            # Sort by similarity (descending) and take top K
            similarities.sort(key=lambda x: -x[0])
            top_k = similarities[:config.k]

            # Vote on output colour, weighted by similarity
            colour_weights: Dict[int, float] = defaultdict(float)
            total_weight = 0.0
            for sim, in_col, out_col in top_k:
                # Weight = similarity² (quadratic falloff)
                # Only count if the train cell's input colour matches the test cell's colour
                # OR if we're allowing cross-colour matches
                # For now: weight by similarity only, regardless of input colour
                weight = sim ** 2
                colour_weights[out_col] += weight
                total_weight += weight

            if total_weight > 0:
                best_colour = max(colour_weights, key=colour_weights.get)
                confidence = colour_weights[best_colour] / total_weight
                if confidence >= config.uncertainty_threshold:
                    row.append(best_colour)
                else:
                    # Low confidence — fall back to input colour
                    row.append(test_input.cells[r][c])
            else:
                row.append(test_input.cells[r][c])

        out_cells.append(row)

    return Grid(out_cells)


def predict_via_taste_same_colour(task: ARCTask,
                                    config: TasteArmConfig = TasteArmConfig()
                                    ) -> Optional[Grid]:
    """Like predict_via_taste but only considers train cells with the same
    input colour as the test cell.

    This is more restrictive but more precise — it says "find train cells
    of the same colour with similar local composition, and apply their
    transformation".
    """
    test_input = task.test[0].input
    train_entries = collect_train_tastes(task)

    if not train_entries:
        return None

    # Group train entries by input colour
    by_colour: Dict[int, List[Tuple[int, int, int, TasteProfile]]] = defaultdict(list)
    for tr, tc, in_col, out_col, taste in train_entries:
        by_colour[in_col].append((tr, tc, out_col, taste))

    h, w = test_input.shape
    out_cells = []

    for r in range(h):
        row = []
        for c in range(w):
            test_colour = test_input.cells[r][c]
            test_taste = taste_region(test_input, r, c, config.radius)

            # Only consider train cells with the same input colour
            same_colour_entries = by_colour.get(test_colour, [])
            if not same_colour_entries:
                row.append(test_colour)
                continue

            # Compute taste similarity to same-colour train cells
            similarities = []
            for tr, tc, out_col, train_taste in same_colour_entries:
                sim = taste_similarity(test_taste, train_taste)
                if sim >= config.min_similarity:
                    similarities.append((sim, out_col))

            if not similarities:
                # No similar taste among same-colour cells — fall back
                row.append(test_colour)
                continue

            # Sort and take top K
            similarities.sort(key=lambda x: -x[0])
            top_k = similarities[:config.k]

            # Vote
            colour_weights: Dict[int, float] = defaultdict(float)
            total_weight = 0.0
            for sim, out_col in top_k:
                weight = sim ** 2
                colour_weights[out_col] += weight
                total_weight += weight

            if total_weight > 0:
                best_colour = max(colour_weights, key=colour_weights.get)
                confidence = colour_weights[best_colour] / total_weight
                if confidence >= config.uncertainty_threshold:
                    row.append(best_colour)
                else:
                    row.append(test_colour)
            else:
                row.append(test_colour)

        out_cells.append(row)

    return Grid(out_cells)


# ══════════════════════════════════════════════════════════════════════════════
# Hard-gate verification
# ══════════════════════════════════════════════════════════════════════════════

def _passes_train(task: ARCTask, pred_fn) -> bool:
    for pair in task.train:
        try:
            if pred_fn(pair.input) != pair.output:
                return False
        except Exception:
            return False
    return True


def predict_best_taste(task: ARCTask
                        ) -> Tuple[Optional[Grid], str, Dict[str, Any]]:
    """Try taste-based prediction strategies and return the best.

    Tries:
      1. predict_via_taste_same_colour (more precise)
      2. predict_via_taste (more general)

    Each must pass the hard gate (exact train reproduction).
    """
    strategies = [
        ("taste_same_colour", lambda g: predict_via_taste_same_colour(task)),
        ("taste_general", lambda g: predict_via_taste(task)),
    ]

    # For taste prediction, the function ignores its grid argument and
    # always predicts the test.  So we need to verify differently:
    # apply the same prediction logic to each train pair.

    for name, _ in strategies:
        try:
            # Build a prediction function that works on any grid
            if name == "taste_same_colour":
                def pred_fn(grid: Grid) -> Grid:
                    # Use the grid as test input, predict via taste
                    return _predict_taste_on_grid(grid, task, same_colour=True)
            else:
                def pred_fn(grid: Grid) -> Grid:
                    return _predict_taste_on_grid(grid, task, same_colour=False)

            if _passes_train(task, pred_fn):
                pred = pred_fn(task.test[0].input)
                return pred, name, {"strategy": name}
        except Exception:
            continue

    return None, "none", {}


def _predict_taste_on_grid(grid: Grid, task: ARCTask,
                            same_colour: bool = True) -> Grid:
    """Apply taste-based prediction to an arbitrary grid (for verification)."""
    train_entries = collect_train_tastes(task)
    if not train_entries:
        return grid.copy()

    by_colour: Dict[int, List] = defaultdict(list)
    if same_colour:
        for tr, tc, in_col, out_col, taste in train_entries:
            by_colour[in_col].append((tr, tc, out_col, taste))

    config = TasteArmConfig()
    h, w = grid.shape
    out_cells = []

    for r in range(h):
        row = []
        for c in range(w):
            test_colour = grid.cells[r][c]
            test_taste = taste_region(grid, r, c, config.radius)

            if same_colour:
                candidates = by_colour.get(test_colour, [])
            else:
                candidates = [(tr, tc, out_col, taste)
                               for tr, tc, _, out_col, taste in train_entries]

            if not candidates:
                row.append(test_colour)
                continue

            similarities = []
            for tr, tc, out_col, train_taste in candidates:
                sim = taste_similarity(test_taste, train_taste)
                if sim >= config.min_similarity:
                    similarities.append((sim, out_col))

            if not similarities:
                row.append(test_colour)
                continue

            similarities.sort(key=lambda x: -x[0])
            top_k = similarities[:config.k]

            colour_weights: Dict[int, float] = defaultdict(float)
            total_weight = 0.0
            for sim, out_col in top_k:
                weight = sim ** 2
                colour_weights[out_col] += weight
                total_weight += weight

            if total_weight > 0:
                best_colour = max(colour_weights, key=colour_weights.get)
                confidence = colour_weights[best_colour] / total_weight
                if confidence >= config.uncertainty_threshold:
                    row.append(best_colour)
                else:
                    row.append(test_colour)
            else:
                row.append(test_colour)

        out_cells.append(row)

    return Grid(out_cells)


# ══════════════════════════════════════════════════════════════════════════════
# Self-test
# ══════════════════════════════════════════════════════════════════════════════

def _self_test():
    print("Taste-Driven Generation self-test")
    print("=" * 60)

    from arc_loader import TrainPair, TestInput

    # Test: recolour based on taste
    # Train: a 3×3 block of colour 1 surrounded by 0 → becomes colour 2
    inp = Grid([
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ])
    out = Grid([
        [0, 0, 0, 0, 0],
        [0, 2, 2, 2, 0],
        [0, 2, 2, 2, 0],
        [0, 2, 2, 2, 0],
        [0, 0, 0, 0, 0],
    ])
    test = Grid([
        [0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0, 0],
        [0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 0],
        [0, 0, 0, 1, 1, 0],
    ])
    expected = Grid([
        [0, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 0, 0],
        [0, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 2, 2, 0],
        [0, 0, 0, 2, 2, 0],
    ])
    task = ARCTask(name="taste_recolour",
                   train=[TrainPair(input=inp, output=out)],
                   test=[TestInput(input=test, expected_output=expected)])

    pred, src, _ = predict_best_taste(task)
    print(f"  src={src}")
    if pred:
        print(f"  pred: {pred.cells}")
        print(f"  expected: {expected.cells}")
        print(f"  correct: {pred == expected}")

    print("\n" + "=" * 60)
    print("Self-test complete.")


if __name__ == "__main__":
    _self_test()
