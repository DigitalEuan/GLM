"""
test_arc_agi3_v03.py — v0.3 self-test suite (pattern learner)
================================================================

Tests the v0.3 PatternLearner:
  1. Learner correctly identifies identity tasks
  2. Learner correctly identifies recolour tasks
  3. Learner correctly identifies gravity tasks
  4. Learner correctly identifies geometric tasks
  5. Learner correctly identifies composite tasks
  6. Learner + symbolic pipeline (v0.3) solves all v0.1 synthetic tasks
  7. Learner solves new "pattern induction" tasks
  8. Learner vs symbolic on real ARC tasks
"""

import sys
import os

_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import Grid, ARCTask, TrainPair, TestInput, load_task
from encoder import encode_grid
from learner import PatternLearner
from run_pipeline import SYNTHETIC_TASKS
from run_pipeline_v03 import run_pipeline_v03


PASS = "✓"
FAIL = "✗"

def _assert(cond, msg):
    if cond:
        print(f"  {PASS} {msg}")
        return True
    else:
        print(f"  {FAIL} {msg}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# NEW SYNTHETIC TASKS — require learning, not just hardcoded ops
# ══════════════════════════════════════════════════════════════════════════════

def _make_identity_task() -> ARCTask:
    """A task where the rule is 'identity' (output = input)."""
    in1 = Grid([[1, 0], [0, 2]])
    in2 = Grid([[3, 4], [5, 6]])
    return ARCTask(
        train=[TrainPair(in1, in1), TrainPair(in2, in2)],
        test=[TestInput(Grid([[7, 8], [9, 1]]), expected_output=Grid([[7, 8], [9, 1]]))],
        name="synthetic_identity",
    )


def _make_recolour_consistent_task() -> ARCTask:
    """Recolour task with a consistent mapping across 3 train pairs."""
    in1 = Grid([[1, 1, 0], [0, 2, 2]])
    in2 = Grid([[2, 0, 1], [2, 1, 0]])
    in3 = Grid([[0, 1, 2], [1, 2, 0]])
    mapping = {1: 2, 2: 1}
    return ARCTask(
        train=[TrainPair(in1, in1.recolour(mapping)),
               TrainPair(in2, in2.recolour(mapping)),
               TrainPair(in3, in3.recolour(mapping))],
        test=[TestInput(Grid([[1, 2, 1], [2, 1, 2]]),
                        expected_output=Grid([[1, 2, 1], [2, 1, 2]]).recolour(mapping))],
        name="synthetic_recolour_consistent",
    )


def _make_gravity_up_task() -> ARCTask:
    """Gravity task where cells rise to the top."""
    in1 = Grid([[0, 0, 0],
                [1, 0, 2],
                [0, 0, 0]])
    out1 = Grid([[1, 0, 2],
                 [0, 0, 0],
                 [0, 0, 0]])
    in2 = Grid([[0, 0, 0, 0],
                [0, 3, 0, 4],
                [0, 0, 0, 0]])
    out2 = Grid([[0, 3, 0, 4],
                 [0, 0, 0, 0],
                 [0, 0, 0, 0]])
    return ARCTask(
        train=[TrainPair(in1, out1), TrainPair(in2, out2)],
        test=[TestInput(Grid([[0, 0, 0], [5, 0, 6], [0, 0, 0]]),
                        expected_output=Grid([[5, 0, 6], [0, 0, 0], [0, 0, 0]]))],
        name="synthetic_gravity_up",
    )


def _make_flip_h_task() -> ARCTask:
    """Flip-horizontal task."""
    in1 = Grid([[1, 0, 2],
                [0, 3, 0]])
    out1 = in1.flip_h()
    in2 = Grid([[4, 5, 6],
                [7, 8, 9]])
    out2 = in2.flip_h()
    return ARCTask(
        train=[TrainPair(in1, out1), TrainPair(in2, out2)],
        test=[TestInput(Grid([[1, 2, 3], [4, 5, 6]]),
                        expected_output=Grid([[1, 2, 3], [4, 5, 6]]).flip_h())],
        name="synthetic_flip_h",
    )


def _make_composite_diff_task() -> ARCTask:
    """A task with no simple op pattern — requires cell-level diff replay.

    Rule: cells at (0,0) and (0,2) swap; everything else stays.
    This isn't a standard op, so the learner should fall back to composite.
    """
    in1 = Grid([[1, 0, 2],
                [0, 3, 0]])
    out1 = Grid([[2, 0, 1],
                 [0, 3, 0]])
    in2 = Grid([[4, 0, 5],
                [6, 7, 8]])
    out2 = Grid([[5, 0, 4],
                 [6, 7, 8]])
    return ARCTask(
        train=[TrainPair(in1, out1), TrainPair(in2, out2)],
        test=[TestInput(Grid([[9, 0, 1], [2, 3, 4]]),
                        expected_output=Grid([[1, 0, 9], [2, 3, 4]]))],
        name="synthetic_composite_swap",
    )


NEW_SYNTHETIC_TASKS = {
    "identity":          _make_identity_task,
    "recolour_consistent": _make_recolour_consistent_task,
    "gravity_up":        _make_gravity_up_task,
    "flip_h":            _make_flip_h_task,
    "composite_swap":    _make_composite_diff_task,
}


# ══════════════════════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_learner_identity():
    print("\n── Test 1: Learner identifies identity ──")
    ok = True
    task = NEW_SYNTHETIC_TASKS["identity"]()
    learner = PatternLearner()
    learner.learn_from_task(task)
    ok &= _assert(learner.learned_pattern_type == "identity",
                  f"pattern type = {learner.learned_pattern_type} (expected 'identity')")
    pred = learner.predict(task)
    ok &= _assert(pred == task.test[0].expected_output,
                  "prediction matches expected (identity)")
    return ok


def test_learner_recolour():
    print("\n── Test 2: Learner identifies consistent recolour ──")
    ok = True
    task = NEW_SYNTHETIC_TASKS["recolour_consistent"]()
    learner = PatternLearner()
    learner.learn_from_task(task)
    ok &= _assert(learner.learned_pattern_type == "recolour",
                  f"pattern type = {learner.learned_pattern_type} (expected 'recolour')")
    ok &= _assert(learner.learned_recolour_mapping == {1: 2, 2: 1},
                  f"learned mapping = {learner.learned_recolour_mapping}")
    pred = learner.predict(task)
    ok &= _assert(pred == task.test[0].expected_output,
                  "prediction matches expected (recolour)")
    return ok


def test_learner_gravity_up():
    print("\n── Test 3: Learner identifies gravity_up ──")
    ok = True
    task = NEW_SYNTHETIC_TASKS["gravity_up"]()
    learner = PatternLearner()
    learner.learn_from_task(task)
    ok &= _assert(learner.learned_pattern_type == "gravity",
                  f"pattern type = {learner.learned_pattern_type} (expected 'gravity')")
    ok &= _assert(learner.learned_gravity_direction == "up",
                  f"direction = {learner.learned_gravity_direction}")
    pred = learner.predict(task)
    ok &= _assert(pred == task.test[0].expected_output,
                  "prediction matches expected (gravity_up)")
    return ok


def test_learner_flip_h():
    print("\n── Test 4: Learner identifies flip_h ──")
    ok = True
    task = NEW_SYNTHETIC_TASKS["flip_h"]()
    learner = PatternLearner()
    learner.learn_from_task(task)
    ok &= _assert(learner.learned_pattern_type == "geometric",
                  f"pattern type = {learner.learned_pattern_type} (expected 'geometric')")
    pred = learner.predict(task)
    ok &= _assert(pred == task.test[0].expected_output,
                  "prediction matches expected (flip_h)")
    return ok


def test_learner_composite():
    print("\n── Test 5: Learner falls back to composite ──")
    ok = True
    task = NEW_SYNTHETIC_TASKS["composite_swap"]()
    learner = PatternLearner()
    learner.learn_from_task(task)
    ok &= _assert(learner.learned_pattern_type == "composite",
                  f"pattern type = {learner.learned_pattern_type} (expected 'composite')")
    pred = learner.predict(task)
    # Composite replay should solve this (test input has same layout as train inputs)
    ok &= _assert(pred == task.test[0].expected_output,
                  "prediction matches expected (composite replay)")
    return ok


def test_v03_pipeline_synthetic():
    print("\n── Test 6: v0.3 pipeline (learner + symbolic) on all synthetic tasks ──")
    ok = True
    all_tasks = {**SYNTHETIC_TASKS, **NEW_SYNTHETIC_TASKS}
    for name, task_fn in all_tasks.items():
        task = task_fn()
        report = run_pipeline_v03(task, max_program_length=2, run_symbolic=True)
        status = "✓" if report.final_correct else "✗"
        print(f"     {status} {name}: pattern={report.learner_pattern_type}, "
              f"source={report.final_source}, correct={report.final_correct}")
        if report.final_correct is False:
            ok = False
    return ok


def test_learner_vs_symbolic_real():
    print("\n── Test 7: Learner on real ARC tasks (first 10) ──")
    ok = True
    data_dir = os.path.join(_PKG_ROOT, "data", "training")
    if not os.path.exists(data_dir):
        print("  ⚠ data/training not found — skipping")
        return True

    task_files = sorted(f for f in os.listdir(data_dir) if f.endswith(".json"))[:10]
    learner_solved = 0
    symbolic_solved = 0
    both_solved = 0

    for fname in task_files:
        task = load_task(os.path.join(data_dir, fname), name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue

        # Learner only
        learner = PatternLearner()
        learner.learn_from_task(task)
        pred = learner.predict(task)
        learner_correct = (pred is not None and pred == task.test[0].expected_output)
        if learner_correct:
            learner_solved += 1

        # Full v0.3 (learner + symbolic)
        report = run_pipeline_v03(task, max_program_length=2, run_symbolic=True)
        if report.final_correct:
            symbolic_solved += 1
        if learner_correct and report.final_correct:
            both_solved += 1

        status_l = "✓" if learner_correct else "✗"
        status_s = "✓" if report.final_correct else "✗"
        print(f"     {task.name}: learner={status_l} (pattern={learner.learned_pattern_type}), "
              f"v0.3={status_s} (source={report.final_source})")

    print(f"\n     Learner-only: {learner_solved}/10")
    print(f"     v0.3 (learner+symbolic): {symbolic_solved}/10")
    print(f"     Both: {both_solved}/10")
    ok &= _assert(learner_solved + symbolic_solved > 0,
                  f"at least one approach solves ≥1 task (learner={learner_solved}, v0.3={symbolic_solved})")
    return ok


def test_colour_native_encoding():
    print("\n── Test 8: Colour-native encoding (24-bit vector IS hex colour) ──")
    ok = True
    # Verify that every encoded grid produces a valid #RRGGBB colour
    from learner.pattern_learner import _grid_to_colour_signature
    g1 = Grid([[1, 0], [0, 2]])
    c1 = _grid_to_colour_signature(g1)
    ok &= _assert(c1.startswith("#") and len(c1) == 7,
                  f"colour signature is #RRGGBB (got {c1})")

    g2 = Grid([[3, 4], [5, 6]])
    c2 = _grid_to_colour_signature(g2)
    ok &= _assert(c1 != c2, f"different grids → different colours ({c1} ≠ {c2})")

    # Verify colour distance is computable
    try:
        from learner.pattern_learner import _GLM_COLOUR_AVAILABLE
        ok &= _assert(_GLM_COLOUR_AVAILABLE, "GLM18 colour module is available")
        from GLM18_hex_colour import colour_distance
        d = colour_distance(c1, c2)
        ok &= _assert(d > 0, f"colour_distance({c1}, {c2}) = {d} > 0")
    except ImportError:
        print(f"     ⚠ GLM18 not available — skipping colour_distance test")
    return ok


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

ALL_TESTS = [
    test_learner_identity,
    test_learner_recolour,
    test_learner_gravity_up,
    test_learner_flip_h,
    test_learner_composite,
    test_v03_pipeline_synthetic,
    test_learner_vs_symbolic_real,
    test_colour_native_encoding,
]


def main():
    print("═══════════════════════════════════════════════════════════════")
    print("  GLM-ARC Pipeline v0.3 Self-Test Suite")
    print("  (PatternLearner + colour-native encoding + CRG)")
    print("═══════════════════════════════════════════════════════════════")

    results = []
    for test in ALL_TESTS:
        try:
            ok = test()
            results.append((test.__name__, ok))
        except Exception as e:
            import traceback
            print(f"  {FAIL} {test.__name__}: EXCEPTION {type(e).__name__}: {e}")
            traceback.print_exc()
            results.append((test.__name__, False))

    print("\n═══════════════════════════════════════════════════════════════")
    print("  Summary")
    print("═══════════════════════════════════════════════════════════════")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    for name, ok in results:
        print(f"  {PASS if ok else FAIL} {name}")
    print(f"\n  {passed}/{total} tests passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
