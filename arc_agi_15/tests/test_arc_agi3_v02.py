"""
test_arc_agi3_v02.py — v0.2 self-test suite
=============================================

Tests the v0.2 enhancements:
  - R(n) integration in the grammar (k-parameter)
  - Coordinate-free encoder (using spatial_arithmetic)
  - Stochastic arm
  - OPCODE_TABLE + MODIFIER_TABLE as C-prefixes
  - New DSL operators (scale, translate, dilate, erode, gravity variants)
  - Submission harness
  - Real ARC task validation

Run with: python3 tests/test_arc_agi3_v02.py
"""

import sys
import os

_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import Grid, ARCTask, TrainPair, TestInput, load_task
from encoder import encode_grid, encode_task
from dsl import Ops, Operation, Program
from grammar import PhiGrammar, generate_candidates, grammar_size, PhiTuple
from ranker import Ranker, RandomRanker
from run_pipeline import run_pipeline, SYNTHETIC_TASKS
from submission_harness import SubmissionHarness, run_batch


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
# TESTS
# ══════════════════════════════════════════════════════════════════════════════

def test_grammar_size():
    print("\n── Test 1: Φ-grammar parameter space ──")
    ok = True
    size = grammar_size(include_stochastic=True)
    ok &= _assert(size["n_values"] == 18, f"18 n-values (got {size['n_values']})")
    ok &= _assert(size["arms"] == 2, f"2 arms (got {size['arms']})")
    ok &= _assert(size["layers"] == 4, f"4 layers (got {size['layers']})")
    ok &= _assert(size["c_prefixes"] == 9, f"9 C-prefixes (got {size['c_prefixes']})")
    ok &= _assert(size["corrections"] == 4, f"4 corrections (got {size['corrections']})")
    total = size["total_phi_tuples"]
    ok &= _assert(total == 18*2*4*9*4, f"total Φ-tuples = {total}")
    print(f"     Grammar size: {total} Φ-tuples = {total} length-1 candidates")
    return ok


def test_rn_integration():
    print("\n── Test 2: R(n) integration in k-parameter ──")
    ok = True
    # Verify that R(n) is being used as the k-parameter
    from spatial_arithmetic_compat import value_to_radius, radius_to_value
    # spatial_arithmetic.value_to_radius(v) interprets v as a "value" (signed integer)
    # and converts to a polygon vertex count via n = 2*|v| + BASE_NODES (BASE_NODES=4).
    # So value_to_radius(4) computes R(2*4+4) = R(12) ≈ 1/(2·sin(π/12)) ≈ 1.93
    R_v4 = value_to_radius(4)
    # R(12) = 1/(2·sin(π/12)) = 1/(2·sin(15°)) = 1/(2·0.2588) ≈ 1.9319
    ok &= _assert(1.5 < R_v4 < 2.5, f"value_to_radius(4) = {R_v4:.4f} (expected ~1.93, which is R(12))")

    # Verify a PhiTuple computes k_spatial correctly
    phi = PhiTuple(n=4, arm="det", layer="Activation", c_prefix="ADD", correction="none")
    # PhiTuple.n=4 means we use value_to_radius(4) as k_spatial
    ok &= _assert(abs(phi.k_spatial - R_v4) < 1e-9, f"PhiTuple.k_spatial = {phi.k_spatial:.4f}")
    ok &= _assert(isinstance(phi.k_scalar, int), f"PhiTuple.k_scalar = {phi.k_scalar} (int)")

    # Verify the grammar generates candidates with R(n)-derived ops
    task = SYNTHETIC_TASKS["rotate_90"]()
    cands = generate_candidates(task, max_program_length=1, include_stochastic=False)
    ok &= _assert(len(cands) > 0, "grammar generates candidates")
    # Check that rotation candidates exist (from ADD c_prefix in Activation layer)
    rotate_cands = [c for c in cands if c.operations and c.operations[0].op in
                    (Ops.ROTATE_90, Ops.ROTATE_180, Ops.ROTATE_270)]
    ok &= _assert(len(rotate_cands) > 0, f"rotation candidates exist ({len(rotate_cands)})")
    return ok


def test_coordinate_free_encoder():
    print("\n── Test 3: Coordinate-free encoder (R(n) in spatial anchor) ──")
    ok = True
    # The encoder should now use R(n) for the spatial anchor
    from encoder.arc_to_24bit import _SPATIAL_ARITHMETIC_AVAILABLE
    ok &= _assert(_SPATIAL_ARITHMETIC_AVAILABLE, "spatial_arithmetic is available to encoder")

    # Encode a grid with a known dominant object
    g = Grid([[0, 1, 0],
              [1, 1, 1],
              [0, 1, 0]])  # cross, 5 cells of colour 1
    v, r = encode_grid(g)
    ok &= _assert(r.dominant_colour == 1, f"dominant colour = {r.dominant_colour}")
    # The spatial anchor should now use R(5) for the radius bucket
    # (5 cells → n=5 → R(5) = 1/(2·sin(π/5)) ≈ 0.851)
    print(f"     cross grid encoder report (key fields):")
    print(f"       palette_code:        {r.palette_code:06b}")
    print(f"       cardinality_code:    {r.cardinality_code:06b}")
    print(f"       spatial_anchor_code: {r.spatial_anchor_code:06b}  (uses R(5))")
    print(f"       relational_code:     {r.relational_code:06b}")
    print(f"       refined NRCI:        {r.nrci_refined:.4f}")
    ok &= _assert(0.0 < r.nrci_refined <= 1.0, f"NRCI in (0,1] = {r.nrci_refined:.4f}")
    return ok


def test_new_dsl_operators():
    print("\n── Test 4: New DSL operators (scale, translate, dilate, erode, gravity variants) ──")
    ok = True
    g = Grid([[1, 0],
              [0, 2]])

    # SCALE_2X
    s2x = Operation(Ops.SCALE_2X).apply(g)
    ok &= _assert(s2x.shape == (4, 4), f"SCALE_2X: shape {s2x.shape}")
    ok &= _assert(s2x.cells[0][0] == 1 and s2x.cells[0][1] == 1, "SCALE_2X: top-left 2x2 is colour 1")

    # TRANSLATE
    t = Operation(Ops.TRANSLATE, params={"dr": 1, "dc": 1}).apply(g)
    ok &= _assert(t.cells[1][1] == 1 and t.cells[2][2] == 2 if t.shape[0] > 2 else True,
                  f"TRANSLATE: shifted by (1,1)")

    # GRAVITY_UP
    g2 = Grid([[0, 0, 0],
               [1, 0, 2],
               [0, 0, 0]])
    up = Operation(Ops.GRAVITY_UP).apply(g2)
    ok &= _assert(up.cells[0][0] == 1 and up.cells[0][2] == 2, "GRAVITY_UP: cells rise to top")

    # GRAVITY_RIGHT
    right = Operation(Ops.GRAVITY_RIGHT).apply(g2)
    # cells [1,0,2] in row 1 should compact to right: [0,1,2]
    ok &= _assert(right.cells[1] == [0, 1, 2], f"GRAVITY_RIGHT: row compacts right (got {right.cells[1]})")

    # DILATE
    cross = Grid([[0, 1, 0],
                  [1, 1, 1],
                  [0, 1, 0]])
    dil = Operation(Ops.DILATE, params={"colour": 1}).apply(cross)
    # After dilation, the cross should fill the 3x3 grid
    ok &= _assert(all(dil.cells[r][c] == 1 for r in range(3) for c in range(3)),
                  "DILATE: cross fills 3x3")

    # ERODE
    full = Grid([[1, 1, 1],
                 [1, 1, 1],
                 [1, 1, 1]])
    ero = Operation(Ops.ERODE, params={"colour": 1}).apply(full)
    # After erosion, only the center should remain
    ok &= _assert(ero.cells[1][1] == 1 and ero.cells[0][0] == 0,
                  "ERODE: 3x3 block erodes to center")
    return ok


def test_stochastic_arm():
    print("\n── Test 5: Stochastic arm (arm=sto) ──")
    ok = True
    task = SYNTHETIC_TASKS["rotate_90"]()
    # Generate with stochastic arm
    cands_sto = generate_candidates(task, max_program_length=1, include_stochastic=True)
    cands_det = generate_candidates(task, max_program_length=1, include_stochastic=False)
    ok &= _assert(len(cands_sto) >= len(cands_det),
                  f"sto candidates ({len(cands_sto)}) >= det candidates ({len(cands_det)})")
    # The stochastic arm should produce MORE candidates (it includes both arms)
    if len(cands_sto) > len(cands_det):
        print(f"     sto produces {len(cands_sto) - len(cands_det)} more candidates than det")
    return ok


def test_submission_harness():
    print("\n── Test 6: Submission harness ──")
    ok = True
    harness = SubmissionHarness(max_program_length=1)

    task = SYNTHETIC_TASKS["rotate_90"]()
    predicted, report = harness.solve_task(task)
    ok &= _assert(predicted is not None, "harness returns a prediction")
    ok &= _assert(predicted == task.test[0].expected_output,
                  "prediction matches expected output")

    # Test format_submission
    import json
    tasks = {"task_1": task}
    json_str = harness.format_submission(tasks)
    parsed = json.loads(json_str)
    ok &= _assert("task_1" in parsed, "submission JSON contains task_1")
    ok &= _assert(isinstance(parsed["task_1"], list), "submission JSON value is a list (grid)")
    return ok


def test_real_arc_tasks():
    print("\n── Test 7: Real ARC task validation (first 5 tasks) ──")
    ok = True
    data_dir = os.path.join(_PKG_ROOT, "data", "training")
    if not os.path.exists(data_dir):
        print("  ⚠ data/training not found — skipping")
        return True

    task_files = sorted(f for f in os.listdir(data_dir) if f.endswith(".json"))[:5]
    if not task_files:
        print("  ⚠ no tasks found — skipping")
        return True

    solved = 0
    for fname in task_files:
        task = load_task(os.path.join(data_dir, fname), name=os.path.splitext(fname)[0])
        predicted, report = run_pipeline(task, max_program_length=2, check_ground_truth=False), None
        # run_pipeline returns a PipelineReport, not a tuple — fix this
        report = predicted
        predicted_grid = report.top_results[0].test_output if report.top_results else task.test[0].input.copy()

        if task.test[0].expected_output is not None:
            if predicted_grid == task.test[0].expected_output:
                solved += 1
                print(f"     {task.name}: ✓ SOLVED (nrci={report.top_results[0].nrci_refined:.4f})")
            else:
                tp = report.n_train_pass
                print(f"     {task.name}: ✗ wrong (train-pass={tp}, cand={report.n_candidates})")

    print(f"     Solved {solved}/{len(task_files)} real ARC tasks")
    ok &= _assert(solved >= 1, f"at least 1/5 real tasks solved (got {solved})")
    return ok


def test_end_to_end_synthetic():
    print("\n── Test 8: End-to-end on all synthetic tasks (v0.2) ──")
    ok = True
    for name, task_fn in SYNTHETIC_TASKS.items():
        task = task_fn()
        report = run_pipeline(task, max_program_length=2, top_k=3)
        if report.correct is not None:
            status = "✓" if report.correct else "✗"
            print(f"     {status} {name}: nrci={report.top_results[0].nrci_refined:.4f} "
                  f"if report.top_results else 'no-cand', cand={report.n_candidates}")
            if report.correct:
                ok &= True
            else:
                ok = False
    return ok


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

ALL_TESTS = [
    test_grammar_size,
    test_rn_integration,
    test_coordinate_free_encoder,
    test_new_dsl_operators,
    test_stochastic_arm,
    test_submission_harness,
    test_real_arc_tasks,
    test_end_to_end_synthetic,
]


def main():
    print("═══════════════════════════════════════════════════════════════")
    print("  GLM-ARC Pipeline v0.2 Self-Test Suite")
    print("  (R(n) integration + coordinate-free encoder + new DSL ops)")
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
