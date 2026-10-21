#!/usr/bin/env python3
"""
Iteration 7 Phase 3 — Compose snap with operation via substrate's analogy.py.

The substrate's `lattice_analogy(a, b, c)` solves "A : B :: C : ?" by:
  1. Computing D* = C + (B - A) (the analogy target, in Q^24)
  2. Snapping D* to the nearest Leech lattice point
  3. Returning that as the predicted answer

For our binary tasks:
  * Toggle: a=query_1, b=NOT query_1, c=query_2, expected=NOT query_2
    D* = query_2 + (NOT query_1 - query_1) = query_2 + (1 - 2*query_1) per coord
  * Translate: a=source_1, b=dest_1, c=source_2, expected=dest_2
    D* = source_2 + (dest_1 - source_1)

If lattice_analogy correctly predicts the transformation, this demonstrates
"reasoning exactly via lattice operations" — the pipeline doesn't just ENCODE
binary grids as lattice points; it TRANSFORMS them via the substrate's analogy
solver.
"""

from __future__ import annotations
import sys, os, json, time
from fractions import Fraction
from typing import Dict, List, Any, Tuple
import numpy as np

GLM_REPO = "/home/z/my-project/glm_repo"
sys.path.insert(0, GLM_REPO)
sys.path.insert(0, "/home/z/my-project/scripts")

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from glm_universal.reasoning import analogy
from glm_universal.substrate import leech2, mog, golay_decode, linalg
from bin_tasks import TASKS

OUT_JSON = "/home/z/my-project/data/iter7_lattice_analogy.json"
OUT_TXT  = "/home/z/my-project/data/iter7_lattice_analogy.txt"


def grid_to_q24(grid: np.ndarray) -> Tuple[Fraction, ...]:
    """Convert a binary grid to a 24-tuple of Fractions (0 or 1)."""
    return tuple(Fraction(int(v)) for v in grid.flatten())


def q24_to_grid(q: Tuple[Fraction, ...], shape=(4, 6)) -> np.ndarray:
    """Convert a 24-tuple of Fractions back to a binary grid (threshold at 0.5)."""
    g = np.zeros(shape, dtype=np.uint8)
    for i, v in enumerate(q):
        r, c = divmod(i, shape[1])
        g[r, c] = 1 if float(v) > 0.5 else 0
    return g


def test_toggle_analogy(seed_a: int, seed_c: int) -> Dict[str, Any]:
    """Test 'A is to NOT A as C is to ?' on toggle task."""
    fam = TASKS["toggle"]
    a_grid, _, _ = fam.generate(seed=seed_a, H=4, W=6)
    b_grid, _, _ = fam.generate(seed=seed_a, H=4, W=6)  # same seed
    b_grid = (1 - b_grid).astype(np.uint8)  # NOT A
    c_grid, _, _ = fam.generate(seed=seed_c, H=4, W=6)
    expected = (1 - c_grid).astype(np.uint8)  # NOT C
    a = grid_to_q24(a_grid)
    b = grid_to_q24(b_grid)
    c = grid_to_q24(c_grid)
    try:
        result = analogy.lattice_analogy(a, b, c)
        # Reconstruct the predicted grid
        pred_q = tuple(Fraction(int(v)) for v in result.point)
        pred_grid = q24_to_grid(pred_q)
        # Exact match?
        exact = bool(np.array_equal(pred_grid, expected))
        # Cell match rate
        cell_match = float((pred_grid == expected).mean())
        return {
            "task": "toggle",
            "seed_a": seed_a, "seed_c": seed_c,
            "exact_match": exact,
            "cell_match_rate": cell_match,
            "in_leech": result.in_leech,
            "exact_hit": result.exact_hit,
            "distance2": str(result.distance2),
            "norm2": result.norm2,
            "is_2a_axis": result.is_2a_axis,
        }
    except Exception as e:
        return {"task": "toggle", "seed_a": seed_a, "seed_c": seed_c,
                "error": str(e)}


def test_translate_analogy(seed_a: int, seed_c: int, dx: int = 1, dy: int = 1) -> Dict[str, Any]:
    """Test 'A is to B (translate by dy, dx) as C is to ?' on translate task."""
    fam = TASKS["translate"]
    a_grid, b_grid, _ = fam.generate(seed=seed_a, H=4, W=6, dx=dx, dy=dy)
    c_grid, expected, _ = fam.generate(seed=seed_c, H=4, W=6, dx=dx, dy=dy)
    a = grid_to_q24(a_grid)
    b = grid_to_q24(b_grid)
    c = grid_to_q24(c_grid)
    try:
        result = analogy.lattice_analogy(a, b, c)
        pred_q = tuple(Fraction(int(v)) for v in result.point)
        pred_grid = q24_to_grid(pred_q)
        exact = bool(np.array_equal(pred_grid, expected))
        cell_match = float((pred_grid == expected).mean())
        return {
            "task": "translate",
            "seed_a": seed_a, "seed_c": seed_c,
            "exact_match": exact, "cell_match_rate": cell_match,
            "in_leech": result.in_leech, "exact_hit": result.exact_hit,
            "distance2": str(result.distance2),
        }
    except Exception as e:
        return {"task": "translate", "seed_a": seed_a, "seed_c": seed_c,
                "error": str(e)}


def test_reflect_v_analogy(seed_a: int, seed_c: int) -> Dict[str, Any]:
    """Test 'A is to flip(A) as C is to ?' on reflect_v task."""
    fam = TASKS["reflect_v"]
    a_grid, b_grid, _ = fam.generate(seed=seed_a, H=4, W=6)
    c_grid, expected, _ = fam.generate(seed=seed_c, H=4, W=6)
    a = grid_to_q24(a_grid)
    b = grid_to_q24(b_grid)
    c = grid_to_q24(c_grid)
    try:
        result = analogy.lattice_analogy(a, b, c)
        pred_q = tuple(Fraction(int(v)) for v in result.point)
        pred_grid = q24_to_grid(pred_q)
        exact = bool(np.array_equal(pred_grid, expected))
        cell_match = float((pred_grid == expected).mean())
        return {
            "task": "reflect_v",
            "seed_a": seed_a, "seed_c": seed_c,
            "exact_match": exact, "cell_match_rate": cell_match,
            "in_leech": result.in_leech, "exact_hit": result.exact_hit,
            "distance2": str(result.distance2),
        }
    except Exception as e:
        return {"task": "reflect_v", "seed_a": seed_a, "seed_c": seed_c,
                "error": str(e)}


def run_analogy_tests(n_trials: int = 20) -> Dict[str, Any]:
    """Run analogy tests across 3 task families."""
    results = {"toggle": [], "translate": [], "reflect_v": []}
    for trial in range(n_trials):
        seed_a = trial * 10 + 1
        seed_c = trial * 10 + 2
        results["toggle"].append(test_toggle_analogy(seed_a, seed_c))
        results["translate"].append(test_translate_analogy(seed_a, seed_c))
        results["reflect_v"].append(test_reflect_v_analogy(seed_a, seed_c))
    return results


def render(results: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 7 PHASE 3 — Compose snap with operation via substrate's analogy.py")
    lines.append("=" * 96)
    lines.append("")
    lines.append("The substrate's lattice_analogy(a, b, c) solves 'A : B :: C : ?' by:")
    lines.append("  1. Computing D* = C + (B - A) (in Q^24)")
    lines.append("  2. Snapping D* to the nearest Leech lattice point")
    lines.append("  3. Returning that as the predicted answer")
    lines.append("")
    lines.append("We test this on 3 task families:")
    lines.append("  * toggle: A → NOT A, predict C → NOT C")
    lines.append("  * translate: A → B (move block), predict C → ?")
    lines.append("  * reflect_v: A → flip(A), predict C → flip(C)")
    lines.append("")
    lines.append("-" * 96)
    lines.append(f"{'Task':<14}{'trials':<10}{'exact match':<16}{'mean cell match':<20}{'in_leech rate':<16}")
    lines.append("-" * 96)
    for task_name, trials in results.items():
        n = len(trials)
        exact_count = sum(1 for t in trials if t.get("exact_match"))
        cell_matches = [t.get("cell_match_rate", 0) for t in trials if "error" not in t]
        in_leech_count = sum(1 for t in trials if t.get("in_leech"))
        lines.append(f"{task_name:<14}{n:<10}"
                     f"{exact_count}/{n} ({100*exact_count/n:.0f}%)       "
                     f"{np.mean(cell_matches):.3f}          "
                     f"{in_leech_count}/{n} ({100*in_leech_count/n:.0f}%)")
    lines.append("-" * 96)
    lines.append("")
    lines.append("Sample results (first 3 trials per task):")
    for task_name, trials in results.items():
        lines.append(f"\n--- {task_name} ---")
        for t in trials[:3]:
            if "error" in t:
                lines.append(f"  trial a={t['seed_a']} c={t['seed_c']}: ERROR {t['error']}")
            else:
                lines.append(f"  trial a={t['seed_a']} c={t['seed_c']}: "
                             f"exact={t['exact_match']}, cell_match={t['cell_match_rate']:.3f}, "
                             f"in_leech={t['in_leech']}, dist2={t['distance2']}")
    lines.append("")
    lines.append("Interpretation:")
    lines.append("  * If exact_match is high, the substrate's analogy solver correctly")
    lines.append("    solves the binary transformation via lattice operations.")
    lines.append("  * If exact_match is low but cell_match is high, the snap rounds to")
    lines.append("    a nearby (but wrong) Leech point — the operation is partially captured.")
    lines.append("  * If both are low, the substrate's analogy can't solve this task via")
    lines.append("    Leech-level operations alone — escalation needed.")
    return "\n".join(lines)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Iteration 7 Phase 3: lattice_analogy on binary tasks")
    t0 = time.time()
    results = run_analogy_tests(n_trials=20)
    t1 = time.time()
    print(f"  Ran {sum(len(v) for v in results.values())} analogy trials in {t1-t0:.1f}s")
    txt = render(results)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print()
    print(txt)
    print(f"\nWrote: {OUT_JSON}")
    print(f"Wrote: {OUT_TXT}")


if __name__ == "__main__":
    main()
