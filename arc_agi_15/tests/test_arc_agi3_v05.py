"""
test_arc_agi3_v05.py — v0.5 generative pipeline tests
======================================================

Tests the v0.5 generative reframe:
  1. ObjectExtractor decomposes grids into objects (words)
  2. ObjectCRG learns transformations from train pairs
  3. GenerativeTransformer predicts via CRG + Φ-grammar fallback
  4. Three Column Thinking verifies predictions
  5. All synthetic tasks solved
  6. Real ARC tasks: correct transform-type classification
"""

import sys, os
_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import Grid, ARCTask, TrainPair, TestInput, load_task
from generative import (
    extract_objects, grid_to_sentence, pair_objects,
    ObjectCRG, GenerativeTransformer, three_column_verify,
)
from run_pipeline import SYNTHETIC_TASKS
from run_pipeline_v05 import run_pipeline_v05

PASS = "✓"; FAIL = "✗"
def _assert(cond, msg):
    if cond: print(f"  {PASS} {msg}"); return True
    else: print(f"  {FAIL} {msg}"); return False

def test_object_extraction():
    print("\n── Test 1: Object extraction (grid → words) ──")
    ok = True
    g = Grid([[1,0,0],[0,2,0],[0,0,3]])
    objs = extract_objects(g)
    ok &= _assert(len(objs) == 3, f"3 objects extracted (got {len(objs)})")
    ok &= _assert(all(o.cell_count == 1 for o in objs), "each object is 1 cell")
    ok &= _assert(all(o.vector and len(o.vector) == 24 for o in objs), "each object has 24-bit vector")
    ok &= _assert(all(o.nrci_refined > 0 for o in objs), "each object has NRCI > 0")
    # Test with a multi-cell object
    g2 = Grid([[1,1,0],[1,1,0],[0,0,2]])
    objs2 = extract_objects(g2)
    ok &= _assert(len(objs2) == 2, f"2 objects from grid2 (got {len(objs2)})")
    ok &= _assert(objs2[0].cell_count == 4, f"first object has 4 cells (got {objs2[0].cell_count})")
    return ok

def test_crg_learning():
    print("\n── Test 2: ObjectCRG learns from train pairs ──")
    ok = True
    task = SYNTHETIC_TASKS["recolour"]()
    crg = ObjectCRG()
    crg.learn_from_task(task)
    stats = crg.stats()
    ok &= _assert(stats["total_edges"] > 0, f"CRG has edges (got {stats['total_edges']})")
    ok &= _assert(stats["dominant_type"] == "recolour",
                  f"dominant type = {stats['dominant_type']} (expected 'recolour')")
    ok &= _assert(bool(stats["global_colour_mapping"]),
                  f"learned colour mapping = {stats['global_colour_mapping']}")
    return ok

def test_generative_transformer_synthetic():
    print("\n── Test 3: GenerativeTransformer on all synthetic tasks ──")
    ok = True
    for name, task_fn in SYNTHETIC_TASKS.items():
        task = task_fn()
        report = run_pipeline_v05(task)
        status = "✓" if report.correct else "✗"
        print(f"     {status} {name}: source={report.prediction_source}, type={report.transform_type}")
        if report.correct is False:
            ok = False
    return ok

def test_three_column_thinking():
    print("\n── Test 4: Three Column Thinking verification ──")
    ok = True
    task = SYNTHETIC_TASKS["recolour"]()
    transformer = GenerativeTransformer()
    transformer.learn_from_task(task)
    pred = transformer.predict(task)
    ok &= _assert(pred is not None, "prediction produced")
    if pred:
        check = three_column_verify(task, pred, "recolour", {1:2, 2:1})
        ok &= _assert(check.aligned, f"three columns aligned (lang='{check.language}', nrci={check.math_nrci:.3f})")
        ok &= _assert(check.code_pass, "code column passes (train pairs reproduced)")
    return ok

def test_real_arc_classification():
    print("\n── Test 5: CRG classifies real ARC task transform types ──")
    ok = True
    data_dir = os.path.join(_PKG_ROOT, "data", "training")
    if not os.path.exists(data_dir):
        print("  ⚠ data/training not found — skipping"); return True
    task_files = sorted(f for f in os.listdir(data_dir) if f.endswith(".json"))[:5]
    for fname in task_files:
        task = load_task(os.path.join(data_dir, fname), name=os.path.splitext(fname)[0])
        crg = ObjectCRG()
        crg.learn_from_task(task)
        dominant = crg.dominant_transform_type()
        print(f"     {task.name}: {dominant} (edges={len(crg.all_edges)})")
        ok &= _assert(dominant != "unknown", f"{task.name} classified as {dominant}")
    return ok

def test_speed_improvement():
    print("\n── Test 6: v0.5 speed (generative vs enumerative) ──")
    ok = True
    task = SYNTHETIC_TASKS["rotate_90"]()
    import time
    t0 = time.time()
    report = run_pipeline_v05(task)
    v05_time = time.time() - t0
    ok &= _assert(v05_time < 2.0, f"v0.5 completes in <2s (got {v05_time:.2f}s)")
    ok &= _assert(report.correct, f"v0.5 solves rotate_90")
    print(f"     v0.5 time: {v05_time:.2f}s (vs ~7s for v0.4)")
    return ok

ALL_TESTS = [
    test_object_extraction,
    test_crg_learning,
    test_generative_transformer_synthetic,
    test_three_column_thinking,
    test_real_arc_classification,
    test_speed_improvement,
]

def main():
    print("═══════════════════════════════════════════════════════════════")
    print("  GLM-ARC Pipeline v0.5 Self-Test Suite")
    print("  (Generative: Object extraction + CRG + Three Column)")
    print("═══════════════════════════════════════════════════════════════")
    results = []
    for test in ALL_TESTS:
        try:
            ok = test(); results.append((test.__name__, ok))
        except Exception as e:
            import traceback; print(f"  {FAIL} {test.__name__}: {e}")
            traceback.print_exc(); results.append((test.__name__, False))
    print("\n═══════════════════════════════════════════════════════════════")
    print("  Summary"); print("═══════════════════════════════════════════════════════════════")
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results: print(f"  {PASS if ok else FAIL} {name}")
    print(f"\n  {passed}/{len(results)} tests passed")
    return 0 if passed == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
