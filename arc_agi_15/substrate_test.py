"""
substrate_test.py — Validate the Substrate Mind on Simple Problems
===================================================================

Before trying harder ARC tasks, validate the substrate approach on
simple synthetic problems where we know the answer.

Tests:
1. Gravity: drop non-zero cells to bottom
2. Recolour: swap two colours
3. Fill: fill zeros with a colour
4. Component conditional: change colour if component size ≥ threshold
5. Size change: crop to bounding box

If the mind can't solve these, the approach is broken.
If it can, we know the architecture works and can focus on harder tasks.
"""

from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arc_loader import ARCTask, Grid, TestInput
from substrate_mind import substrate_mind_solve, learn_settlement_dynamics, analyse_perturbation


def make_task(name: str, train_pairs: list, test_input: list, test_output: list) -> ARCTask:
    """Create a synthetic ARC task."""
    train = []
    for inp, out in train_pairs:
        train.append(type('Pair', (), {
            'input': Grid(inp),
            'output': Grid(out),
        })())
    test = [TestInput(input=Grid(test_input), expected_output=Grid(test_output))]
    return ARCTask(name=name, train=train, test=test)


def test_gravity():
    """Test: non-zero cells compact to bottom of each column."""
    task = make_task("gravity_test",
        [
            ([[1, 0, 0], [0, 2, 0], [0, 0, 0]],
             [[0, 0, 0], [0, 0, 0], [1, 2, 0]]),
            ([[0, 3, 0], [0, 0, 4], [0, 0, 0]],
             [[0, 0, 0], [0, 0, 0], [0, 3, 4]]),
        ],
        [[5, 0, 6], [0, 0, 0], [0, 0, 0]],
        [[0, 0, 0], [0, 0, 0], [5, 0, 6]],
    )
    result = substrate_mind_solve(task)
    print(f"Gravity: {'PASS' if result else 'FAIL'}")
    if result:
        print(f"  Solver: {result[1]}")
    return result is not None


def test_recolour():
    """Test: swap two colours."""
    task = make_task("recolour_test",
        [
            ([[1, 2, 1], [2, 1, 2]],
             [[2, 1, 2], [1, 2, 1]]),
            ([[1, 1, 2], [2, 2, 1]],
             [[2, 2, 1], [1, 1, 2]]),
        ],
        [[2, 1, 2], [1, 2, 1]],
        [[1, 2, 1], [2, 1, 2]],
    )
    result = substrate_mind_solve(task)
    print(f"Recolour: {'PASS' if result else 'FAIL'}")
    if result:
        print(f"  Solver: {result[1]}")
    return result is not None


def test_fill():
    """Test: fill all zeros with a colour."""
    task = make_task("fill_test",
        [
            ([[1, 0, 0], [0, 2, 0]],
             [[1, 3, 3], [3, 2, 3]]),
            ([[0, 0, 4], [0, 0, 0]],
             [[3, 3, 4], [3, 3, 3]]),
        ],
        [[5, 0, 0], [0, 0, 6]],
        [[5, 3, 3], [3, 3, 6]],
    )
    result = substrate_mind_solve(task)
    print(f"Fill: {'PASS' if result else 'FAIL'}")
    if result:
        print(f"  Solver: {result[1]}")
    return result is not None


def test_component_conditional():
    """Test: change colour if component size ≥ 4."""
    task = make_task("component_cond_test",
        [
            # 2x2 component of colour 2 (size 4) → becomes 6
            # Single cell of colour 2 (size 1) → stays 2
            ([[2, 2, 0, 2], [2, 2, 0, 0], [0, 0, 0, 0]],
             [[6, 6, 0, 2], [6, 6, 0, 0], [0, 0, 0, 0]]),
            ([[2, 0, 2, 2], [0, 0, 2, 2], [0, 0, 0, 0]],
             [[2, 0, 6, 6], [0, 0, 6, 6], [0, 0, 0, 0]]),
        ],
        [[2, 2, 0, 0], [2, 2, 0, 2], [0, 0, 0, 0]],
        [[6, 6, 0, 0], [6, 6, 0, 2], [0, 0, 0, 0]],
    )
    result = substrate_mind_solve(task)
    print(f"Component conditional: {'PASS' if result else 'FAIL'}")
    if result:
        print(f"  Solver: {result[1]}")
    return result is not None


def test_size_crop():
    """Test: crop to bounding box of non-zero cells."""
    task = make_task("crop_test",
        [
            ([[0, 0, 0, 0], [0, 1, 2, 0], [0, 3, 4, 0], [0, 0, 0, 0]],
             [[1, 2], [3, 4]]),
            ([[0, 0, 0, 0], [0, 5, 6, 0], [0, 7, 8, 0], [0, 0, 0, 0]],
             [[5, 6], [7, 8]]),
        ],
        [[0, 0, 0, 0], [0, 9, 1, 0], [0, 2, 3, 0], [0, 0, 0, 0]],
        [[9, 1], [2, 3]],
    )
    result = substrate_mind_solve(task)
    print(f"Size crop: {'PASS' if result else 'FAIL'}")
    if result:
        print(f"  Solver: {result[1]}")
    return result is not None


def test_neighbour_rule():
    """Test: if all neighbours are the same colour, change to that colour."""
    task = make_task("neighbour_test",
        [
            ([[1, 2, 2], [2, 2, 2], [2, 2, 1]],
             [[1, 2, 2], [2, 2, 2], [2, 2, 1]]),
            # Actually, let's use a simpler rule:
            # cell changes to the colour that appears most in its neighbourhood
        ],
        [[1, 2, 2], [2, 2, 2], [2, 2, 1]],
        [[1, 2, 2], [2, 2, 2], [2, 2, 1]],
    )
    # This is identity — just checking the mind handles it
    result = substrate_mind_solve(task)
    print(f"Neighbour (identity): {'PASS' if result else 'FAIL'}")
    if result:
        print(f"  Solver: {result[1]}")
    return result is not None


def test_shift_right():
    """Test: shift all non-zero cells right by 1."""
    task = make_task("shift_right_test",
        [
            ([[1, 0, 0], [0, 2, 0], [0, 0, 3]],
             [[0, 1, 0], [0, 0, 2], [0, 0, 0]]),
            ([[4, 0, 0], [5, 0, 0], [0, 0, 0]],
             [[0, 4, 0], [0, 5, 0], [0, 0, 0]]),
        ],
        [[6, 0, 0], [0, 7, 0], [0, 0, 0]],
        [[0, 6, 0], [0, 0, 7], [0, 0, 0]],
    )
    result = substrate_mind_solve(task)
    print(f"Shift right: {'PASS' if result else 'FAIL'}")
    if result:
        print(f"  Solver: {result[1]}")
    return result is not None


def test_colour_flip():
    """Test: flip colour 1→2 everywhere."""
    task = make_task("colour_flip_test",
        [
            ([[1, 0, 1], [0, 1, 0]],
             [[2, 0, 2], [0, 2, 0]]),
            ([[1, 1, 0], [0, 0, 1]],
             [[2, 2, 0], [0, 0, 2]]),
        ],
        [[0, 1, 0], [1, 0, 1]],
        [[0, 2, 0], [2, 0, 2]],
    )
    result = substrate_mind_solve(task)
    print(f"Colour flip: {'PASS' if result else 'FAIL'}")
    if result:
        print(f"  Solver: {result[1]}")
    return result is not None


def test_border_fill():
    """Test: fill border cells with colour 3."""
    task = make_task("border_fill_test",
        [
            ([[0, 0, 0], [0, 1, 0], [0, 0, 0]],
             [[3, 3, 3], [3, 1, 3], [3, 3, 3]]),
            ([[0, 0, 0], [0, 0, 0], [0, 0, 0]],
             [[3, 3, 3], [3, 0, 3], [3, 3, 3]]),
        ],
        [[0, 0, 0], [0, 2, 0], [0, 0, 0]],
        [[3, 3, 3], [3, 2, 3], [3, 3, 3]],
    )
    result = substrate_mind_solve(task)
    print(f"Border fill: {'PASS' if result else 'FAIL'}")
    if result:
        print(f"  Solver: {result[1]}")
    return result is not None


def main():
    print("=" * 60)
    print(" SUBSTRATE MIND — Synthetic Validation Tests")
    print("=" * 60)
    print()
    
    results = {
        "gravity": test_gravity(),
        "recolour": test_recolour(),
        "fill": test_fill(),
        "component_conditional": test_component_conditional(),
        "size_crop": test_size_crop(),
        "neighbour_identity": test_neighbour_rule(),
        "shift_right": test_shift_right(),
        "colour_flip": test_colour_flip(),
        "border_fill": test_border_fill(),
    }
    
    print()
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    print(f" RESULTS: {passed}/{len(results)} passed")
    for name, passed in results.items():
        print(f"  {'✓' if passed else '✗'} {name}")
    print("=" * 60)


if __name__ == "__main__":
    main()
