#!/usr/bin/env python3
"""
Iteration 8 Phase 3 — Use substrate's combiner.apply_op() at the F_2 level
for binary transformations that don't need lattice-level snap.

The substrate's combiner.py has 16 coordinatewise Boolean combiners (8 affine
over F_2, all closed under the Golay code). For binary ops like toggle (XOR
with all-ones), the F_2 combiner is the right tool — no lattice lift needed.

Test:
  * Toggle: combiner 6 (XOR) with b = all-ones -> NOT a
  * Reflect_v: NOT a coordinatewise (also XOR with all-ones if reflect = NOT)
                Actually reflect_v is mirror, not NOT. Use combiner 6 (XOR)
                with a per-coordinate mask.
  * Identity (control): combiner 12 (a, ignore b)
  * AND/OR (control): combiners 1, 14

For each task, we test:
  (i) Can we express the task's transformation as a fixed combiner index?
  (ii) Does the combiner-closure property (Golay-closed) hold?

This tests whether the substrate's F_2-level combiner is sufficient for
binary transformations, AVOIDING the lattice-level snap entirely.
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

from glm_universal.reasoning import combiner
from glm_universal.substrate import leech2, mog, golay_decode, linalg
from bin_tasks import TASKS

OUT_JSON = "/home/z/my-project/data/iter8_f2_combiner.json"
OUT_TXT  = "/home/z/my-project/data/iter8_f2_combiner.txt"


def grid_to_bits_24(grid: np.ndarray) -> int:
    bits = 0
    for v in grid.flatten():
        bits = (bits << 1) | int(v & 1)
    return bits

def bits_to_grid(bits: int, H: int = 4, W: int = 6) -> np.ndarray:
    g = np.zeros((H, W), dtype=np.uint8)
    for i in range(H - 1, -1, -1):
        for j in range(W - 1, -1, -1):
            g[i, j] = bits & 1
            bits >>= 1
    return g


# ============================================================================
# 1. List the 16 combiners and identify the affine (Golay-closed) ones
# ============================================================================
def combiner_survey() -> Dict[str, Any]:
    """Survey the 16 combiners; identify which are affine (Golay-closed)."""
    survey = []
    affine_tables = set(combiner.affine_tables())
    for idx in range(16):
        tt = combiner.op_table(idx)
        is_aff = combiner.is_affine(idx)
        # Identify the combiner by name
        name = {
            0: "FALSE (always 0)",
            1: "AND (a AND b)",
            2: "a AND NOT b",
            3: "NOT a (b ignored)",
            4: "NOT b AND a",
            5: "NOT b (a ignored)",
            6: "XOR (a XOR b)",
            7: "NOR (NOT (a OR b))",
            8: "a AND NOT b ... wait",
            9: "XNOR (a == b)",
            10: "b (identity on b)",
            11: "NOT a OR b",
            12: "a (identity on a)",
            13: "NOT b OR a",
            14: "OR (a OR b)",
            15: "TRUE (always 1)",
        }.get(idx, "?")
        survey.append({
            "index": idx, "truth_table": list(tt),
            "is_affine": is_aff,
            "golay_closed": idx in affine_tables,
            "name": name,
        })
    return {"combiners": survey, "n_affine": sum(1 for c in survey if c["is_affine"]),
             "n_golay_closed": sum(1 for c in survey if c["golay_closed"])}


# ============================================================================
# 2. Test toggle via combiner 6 (XOR) with b = all-ones
# ============================================================================
def test_toggle_via_combiner(n_samples: int = 50) -> Dict[str, Any]:
    """Toggle = NOT a = a XOR all-ones. Use combiner 6 (XOR) with b = 0xFFFFFF."""
    fam = TASKS["toggle"]
    all_ones = (1 << 24) - 1
    results = []
    exact_count = 0
    golay_closed_count = 0
    for s in range(n_samples):
        x, y_expected, _ = fam.generate(seed=s + 1, H=4, W=6)
        a = grid_to_bits_24(x)
        # toggle: y = NOT a = a XOR all_ones
        # combiner 6 = XOR; apply with b = all_ones
        y_pred_bits = combiner.apply_op(6, a, all_ones, width=24)
        y_pred = bits_to_grid(y_pred_bits)
        exact = bool(np.array_equal(y_pred, y_expected))
        results.append({
            "seed": s + 1, "input_bits": a,
            "expected_bits": grid_to_bits_24(y_expected),
            "predicted_bits": y_pred_bits, "exact_match": exact,
        })
        if exact:
            exact_count += 1
        # Check: is a XOR all-ones a Golay codeword? (For closure)
        # combiner 6 (XOR) is in affine_tables (one of the 8 affine)
        # So XOR of two Golay codewords is a Golay codeword. But the INPUT
        # binary grid is generally NOT a Golay codeword. The "Golay closed"
        # property applies only when both inputs are codewords.
        # For arbitrary binary inputs, XOR is still a valid operation, but
        # the result may not be a Golay codeword.
        dec = golay_decode.decode_complete(y_pred_bits)
        if dec.weight == 0:
            golay_closed_count += 1
    return {
        "task": "toggle", "n_samples": n_samples,
        "combiner_index": 6, "combiner_name": "XOR (a XOR b)",
        "b_value": "all-ones (0xFFFFFF)",
        "exact_count": exact_count, "exact_rate": exact_count / n_samples,
        "golay_closed_count": golay_closed_count,
        "golay_closed_rate": golay_closed_count / n_samples,
        "samples": results[:3],  # store 3 samples for inspection
    }


# ============================================================================
# 3. Test reflect_v via combiner (XOR with position-dependent mask)
# ============================================================================
def test_reflect_v_via_combiner(n_samples: int = 50) -> Dict[str, Any]:
    """reflect_v: y = mirror(x). For a 4x6 grid, this is a permutation of cells.

    The permutation: cell (r, c) -> cell (r, 5-c) for c in 0..5.
    In bit-space: bit at position (r*6 + c) goes to position (r*6 + (5-c)).
    This is NOT a coordinatewise combiner (it's a permutation, not a Boolean op).

    But we can implement it as: y = x XOR mask, where mask is the bit-flip pattern
    that takes x to mirror(x). However, the mask depends on x (since mirroring
    flips bits only where x and mirror(x) differ).

    So reflect_v is NOT a fixed combiner. It requires a position-dependent mask.
    The F_2 combiner is insufficient for reflect_v.
    """
    fam = TASKS["reflect_v"]
    results = []
    # Try combiner 6 (XOR) with b = various masks
    # The mask would need to be x XOR mirror(x), which depends on x.
    # Let's check: is mirror(x) = x XOR something_constant?
    # For a 4x6 grid, mirror(x)[r, c] = x[r, 5-c]. This is a permutation, not
    # a constant mask. So no fixed combiner works.
    # Document this as a development issue.
    matches_with_constant_mask = 0
    for s in range(n_samples):
        x, y_expected, _ = fam.generate(seed=s + 1, H=4, W=6)
        a = grid_to_bits_24(x)
        # Try b = all-ones (NOT) — only works if y_expected = NOT a
        y_pred_not = bits_to_grid(combiner.apply_op(6, a, (1 << 24) - 1, width=24))
        if np.array_equal(y_pred_not, y_expected):
            matches_with_constant_mask += 1
    return {
        "task": "reflect_v", "n_samples": n_samples,
        "matches_with_constant_xor_mask": matches_with_constant_mask,
        "matches_with_constant_xor_mask_rate": matches_with_constant_mask / n_samples,
        "development_issue": ("reflect_v is a PERMUTATION of cells, not a coordinatewise "
                                "Boolean op. No fixed F_2 combiner can express it. The "
                                "substrate's combiner.apply_op() is insufficient for "
                                "permutation-based tasks. Development requirement: extend "
                                "the combiner to handle permutations, or use the lattice-"
                                "level snap for these tasks."),
    }


# ============================================================================
# 4. Test translate (also a permutation — should fail too)
# ============================================================================
def test_translate_via_combiner(n_samples: int = 50) -> Dict[str, Any]:
    """translate: move a 2x2 block by (dy, dx). This is also a permutation."""
    fam = TASKS["translate"]
    matches = 0
    for s in range(n_samples):
        x, y_expected, _ = fam.generate(seed=s + 1, H=4, W=6, dx=1, dy=1)
        a = grid_to_bits_24(x)
        y_pred_not = bits_to_grid(combiner.apply_op(6, a, (1 << 24) - 1, width=24))
        if np.array_equal(y_pred_not, y_expected):
            matches += 1
    return {
        "task": "translate", "n_samples": n_samples,
        "matches_with_constant_xor_mask": matches,
        "matches_with_constant_xor_mask_rate": matches / n_samples,
        "development_issue": ("translate is also a PERMUTATION (move a block). No fixed "
                                "F_2 combiner works. Same development issue as reflect_v."),
    }


# ============================================================================
# 5. Render + main
# ============================================================================
def render(survey: Dict, results: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 8 PHASE 3 — F_2 combiner for binary transformations")
    lines.append("=" * 96)
    lines.append("")
    lines.append("Per rec #2: use the substrate's combiner.apply_op() at the F_2 level for")
    lines.append("binary transformations that don't need lattice-level snap.")
    lines.append("")
    lines.append(f"Combiner survey: {survey['n_affine']}/16 are affine over F_2, "
                 f"{survey['n_golay_closed']}/16 are Golay-closed.")
    lines.append("")
    lines.append("-" * 96)
    lines.append("[Per-task results — F_2 combiner test]")
    lines.append("-" * 96)
    for task_name, r in results.items():
        lines.append(f"\n--- {task_name} ---")
        for k, v in r.items():
            if k != "samples":
                lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append("-" * 96)
    lines.append("Interpretation:")
    lines.append("  * Toggle: should be solved EXACTLY by combiner 6 (XOR) with b=all-ones.")
    lines.append("    Expected: 100% exact match. This tests whether the F_2 combiner is")
    lines.append("    sufficient for NOT-style binary operations.")
    lines.append("  * Reflect_v: a PERMUTATION of cells, not a coordinatewise Boolean op.")
    lines.append("    No fixed F_2 combiner can express it. Expected: ~0% with constant mask.")
    lines.append("    DEVELOPMENT ISSUE: the substrate's combiner.apply_op() is insufficient")
    lines.append("    for permutation-based tasks. Either extend it, or use the lattice")
    lines.append("    snap for these tasks.")
    lines.append("  * Translate: also a permutation. Same issue.")
    return "\n".join(lines)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Iteration 8 Phase 3: F_2 combiner for binary ops")
    survey = combiner_survey()
    print(f"  Survey: {survey['n_affine']}/16 affine, {survey['n_golay_closed']}/16 Golay-closed")
    results = {}
    print("  Testing toggle (XOR with all-ones)...", end=" ", flush=True)
    t0 = time.time()
    results["toggle"] = test_toggle_via_combiner(n_samples=50)
    print(f"exact={results['toggle']['exact_count']}/50  ({time.time()-t0:.1f}s)")
    print("  Testing reflect_v (constant-mask XOR)...", end=" ", flush=True)
    results["reflect_v"] = test_reflect_v_via_combiner(n_samples=50)
    print(f"matches={results['reflect_v']['matches_with_constant_xor_mask']}/50")
    print("  Testing translate (constant-mask XOR)...", end=" ", flush=True)
    results["translate"] = test_translate_via_combiner(n_samples=50)
    print(f"matches={results['translate']['matches_with_constant_xor_mask']}/50")
    txt = render(survey, results)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    with open(OUT_JSON, "w") as f:
        json.dump({"survey": survey, "results": results}, f, indent=2, default=str)
    print()
    print(txt)
    print(f"\nWrote: {OUT_JSON}")
    print(f"Wrote: {OUT_TXT}")


if __name__ == "__main__":
    main()
