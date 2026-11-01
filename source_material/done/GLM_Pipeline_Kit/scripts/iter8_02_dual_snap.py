#!/usr/bin/env python3
"""
Iteration 8 Phase 2 — Binary-Leech dual snap (rec #1): lift lattice_analogy
to Λ_48 so it can actually TRANSFORM binary targets.

The substrate's lattice_analogy uses nearest_lattice_point which is hardcoded
to Leech (Λ_24). Binary targets lie outside the Leech hull (parity wall),
so the analogy snap lands in Leech but doesn't decode to the binary answer.

This phase implements a BINARY-LEECH DUAL SNAP:
  1. Encode binary targets as Λ_48 points (via trivial 3× scaling)
  2. Compute D* = C + (B - A) in Q^48 (analog of analogy_target)
  3. Snap D* to nearest Λ_48 point (using the F_3 Pless code membership)
  4. Decode the Λ_48 point back to a 24-bit binary grid

If this works, the substrate's analogy machinery can TRANSFORM binary targets.
If not, we document the development issue.
"""

from __future__ import annotations
import sys, os, json, time
from fractions import Fraction
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

GLM_REPO = "/home/z/my-project/glm_repo"
sys.path.insert(0, GLM_REPO)
sys.path.insert(0, "/home/z/my-project/scripts")

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from glm_universal.substrate import leech2, mog, golay_decode, linalg
from glm_universal.substrate import lattice32, lattice48
from glm_universal.reasoning import combiner, analogy
from bin_tasks import TASKS

OUT_JSON = "/home/z/my-project/data/iter8_dual_snap.json"
OUT_TXT  = "/home/z/my-project/data/iter8_dual_snap.txt"


# ============================================================================
# 1. Binary <-> Λ_48 encoding/decoding
# ============================================================================
def binary_to_lambda48(bits: int) -> Tuple[int, ...]:
    """Encode a 24-bit binary word as a Λ_48 point via trivial 3× scaling.
    
    Each bit b -> (3b, 0) in 48-D. So coord 2i = 3*bit_i, coord 2i+1 = 0.
    """
    bits_list = [(bits >> (23 - i)) & 1 for i in range(24)]
    out = []
    for b in bits_list:
        out.append(3 * b)
        out.append(0)
    return tuple(out)

def lambda48_to_binary(point: Tuple[int, ...]) -> int:
    """Decode a Λ_48 point back to a 24-bit binary word.
    
    The trivial encoding has coord 2i = 3*bit_i, coord 2i+1 = 0.
    To decode: bit_i = round(point[2i] / 3). But if the point isn't a trivial
    encoding, we snap each coord to the nearest multiple of 3.
    """
    bits = 0
    for i in range(24):
        # coord 2i should be 0 or 3
        c = point[2 * i]
        # Snap to {0, 3}: if c >= 1.5, bit = 1; else bit = 0
        b = 1 if c >= 2 else 0
        bits = (bits << 1) | b
    return bits


# ============================================================================
# 2. Λ_48 membership test (from iteration 6)
# ============================================================================
_H48 = None
def _get_H48():
    global _H48
    if _H48 is None:
        _H48 = lattice48.dual_ternary_generator()
    return _H48

def in_lambda48(x: Tuple[int, ...]) -> bool:
    """Λ_48 membership: x ∈ Z^48 with x mod 3 ∈ C(23)."""
    H = _get_H48()
    x_mod3 = tuple(v % 3 for v in x)
    for i in range(24):
        s = sum(H[i][j] * x_mod3[j] for j in range(48)) % 3
        if s != 0:
            return False
    return True


# ============================================================================
# 3. Snap to nearest Λ_48 point (Construction A snap)
# ============================================================================
def snap_to_lambda48(target_q: Tuple[Fraction, ...]) -> Tuple[int, ...]:
    """Snap a 48-D rational target to the nearest Λ_48 point.
    
    Construction A snap: for each coord, find the nearest integer congruent to
    0 mod 3 (giving x mod 3 = 0 = zero codeword). This is the simplest snap;
    richer snaps would try other C(23) cosets.
    """
    # For now, use the trivial snap: round each coord to nearest multiple of 3
    # This corresponds to the zero codeword (which is always in C(23))
    out = []
    for v in target_q:
        # Round to nearest multiple of 3
        v_float = float(v)
        nearest_3k = round(v_float / 3) * 3
        out.append(int(nearest_3k))
    return tuple(out)


# ============================================================================
# 4. Lattice analogy at the Λ_48 level
# ============================================================================
def lattice_analogy_lambda48(a_bits: int, b_bits: int, c_bits: int) -> Dict[str, Any]:
    """Solve A : B :: C : ? at the Λ_48 level.
    
    1. Encode a, b, c as Λ_48 points (via binary_to_lambda48)
    2. Compute D* = C + (B - A) in Q^48
    3. Snap D* to nearest Λ_48 point
    4. Decode the snap back to binary
    5. Return the predicted binary word
    """
    a = binary_to_lambda48(a_bits)
    b = binary_to_lambda48(b_bits)
    c = binary_to_lambda48(c_bits)
    # D* = C + (B - A) in Q^48
    d_star = tuple(Fraction(c[i]) + Fraction(b[i]) - Fraction(a[i])
                    for i in range(48))
    # Snap to nearest Λ_48 point
    snap = snap_to_lambda48(d_star)
    in_latt = in_lambda48(snap)
    # Decode back to binary
    pred_bits = lambda48_to_binary(snap)
    return {
        "a_bits": a_bits, "b_bits": b_bits, "c_bits": c_bits,
        "d_star_first_10": [str(d_star[i]) for i in range(10)],
        "snap_first_10": list(snap[:10]),
        "snap_in_lambda48": in_latt,
        "pred_bits": pred_bits,
    }


# ============================================================================
# 5. Test on binary tasks
# ============================================================================
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


def test_toggle_dual_snap(n_samples: int = 30) -> Dict[str, Any]:
    """Toggle: A -> NOT A, predict C -> NOT C via Λ_48 lattice_analogy."""
    fam = TASKS["toggle"]
    results = []
    exact_count = 0
    for s in range(n_samples):
        a_grid, _, _ = fam.generate(seed=s + 1, H=4, W=6)
        b_grid = (1 - a_grid).astype(np.uint8)  # NOT A
        c_grid, _, _ = fam.generate(seed=s + 100, H=4, W=6)
        expected = (1 - c_grid).astype(np.uint8)  # NOT C
        a_bits = grid_to_bits_24(a_grid)
        b_bits = grid_to_bits_24(b_grid)
        c_bits = grid_to_bits_24(c_grid)
        expected_bits = grid_to_bits_24(expected)
        result = lattice_analogy_lambda48(a_bits, b_bits, c_bits)
        pred_grid = bits_to_grid(result["pred_bits"])
        exact = bool(np.array_equal(pred_grid, expected))
        cell_match = float((pred_grid == expected).mean())
        results.append({
            "seed": s + 1,
            "exact_match": exact,
            "cell_match_rate": cell_match,
            "snap_in_lambda48": result["snap_in_lambda48"],
        })
        if exact:
            exact_count += 1
    return {
        "task": "toggle", "n_samples": n_samples,
        "exact_count": exact_count, "exact_rate": exact_count / n_samples,
        "mean_cell_match": float(np.mean([r["cell_match_rate"] for r in results])),
        "snap_in_lambda48_rate": sum(1 for r in results if r["snap_in_lambda48"]) / n_samples,
        "samples": results[:3],
    }


def test_translate_dual_snap(n_samples: int = 30) -> Dict[str, Any]:
    """Translate: A -> B (move block), predict C -> ? via Λ_48 lattice_analogy."""
    fam = TASKS["translate"]
    results = []
    exact_count = 0
    for s in range(n_samples):
        a_grid, b_grid, _ = fam.generate(seed=s + 1, H=4, W=6, dx=1, dy=1)
        c_grid, expected, _ = fam.generate(seed=s + 100, H=4, W=6, dx=1, dy=1)
        a_bits = grid_to_bits_24(a_grid)
        b_bits = grid_to_bits_24(b_grid)
        c_bits = grid_to_bits_24(c_grid)
        expected_bits = grid_to_bits_24(expected)
        result = lattice_analogy_lambda48(a_bits, b_bits, c_bits)
        pred_grid = bits_to_grid(result["pred_bits"])
        exact = bool(np.array_equal(pred_grid, expected))
        cell_match = float((pred_grid == expected).mean())
        results.append({
            "seed": s + 1, "exact_match": exact,
            "cell_match_rate": cell_match,
            "snap_in_lambda48": result["snap_in_lambda48"],
        })
        if exact:
            exact_count += 1
    return {
        "task": "translate", "n_samples": n_samples,
        "exact_count": exact_count, "exact_rate": exact_count / n_samples,
        "mean_cell_match": float(np.mean([r["cell_match_rate"] for r in results])),
        "snap_in_lambda48_rate": sum(1 for r in results if r["snap_in_lambda48"]) / n_samples,
        "samples": results[:3],
    }


def test_reflect_v_dual_snap(n_samples: int = 30) -> Dict[str, Any]:
    """Reflect_v: A -> flip(A), predict C -> flip(C) via Λ_48 lattice_analogy."""
    fam = TASKS["reflect_v"]
    results = []
    exact_count = 0
    for s in range(n_samples):
        a_grid, b_grid, _ = fam.generate(seed=s + 1, H=4, W=6)
        c_grid, expected, _ = fam.generate(seed=s + 100, H=4, W=6)
        a_bits = grid_to_bits_24(a_grid)
        b_bits = grid_to_bits_24(b_grid)
        c_bits = grid_to_bits_24(c_grid)
        expected_bits = grid_to_bits_24(expected)
        result = lattice_analogy_lambda48(a_bits, b_bits, c_bits)
        pred_grid = bits_to_grid(result["pred_bits"])
        exact = bool(np.array_equal(pred_grid, expected))
        cell_match = float((pred_grid == expected).mean())
        results.append({
            "seed": s + 1, "exact_match": exact,
            "cell_match_rate": cell_match,
            "snap_in_lambda48": result["snap_in_lambda48"],
        })
        if exact:
            exact_count += 1
    return {
        "task": "reflect_v", "n_samples": n_samples,
        "exact_count": exact_count, "exact_rate": exact_count / n_samples,
        "mean_cell_match": float(np.mean([r["cell_match_rate"] for r in results])),
        "snap_in_lambda48_rate": sum(1 for r in results if r["snap_in_lambda48"]) / n_samples,
        "samples": results[:3],
    }


# ============================================================================
# 6. Render + main
# ============================================================================
def render(results: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 8 PHASE 2 — Binary-Leech dual snap via Λ_48")
    lines.append("=" * 96)
    lines.append("")
    lines.append("Per rec #1: lift lattice_analogy to Λ_48 so it can TRANSFORM binary targets.")
    lines.append("The substrate's lattice_analogy uses Leech (Λ_24), where binary targets lie")
    lines.append("OUTSIDE the hull. Lifting to Λ_48 (where the trivial 3x scaling works for")
    lines.append("ALL binary targets) should let the analogy solve binary transformations.")
    lines.append("")
    lines.append("Procedure per trial:")
    lines.append("  1. Encode a, b, c as Λ_48 points (3x scaling + pair encoding)")
    lines.append("  2. Compute D* = C + (B - A) in Q^48")
    lines.append("  3. Snap D* to nearest Λ_48 point (Construction A: nearest multiple of 3)")
    lines.append("  4. Decode the snap back to binary (coord 2i -> bit)")
    lines.append("")
    lines.append("-" * 96)
    lines.append("[Per-task results — Λ_48 dual snap]")
    lines.append("-" * 96)
    lines.append(f"{'Task':<14}{'exact match':<16}{'mean cell match':<20}{'snap in Λ_48':<16}")
    lines.append("-" * 96)
    for task_name, r in results.items():
        lines.append(f"{task_name:<14}"
                     f"{r['exact_count']}/{r['n_samples']} ({100*r['exact_rate']:.0f}%)       "
                     f"{r['mean_cell_match']:<20.3f}"
                     f"{r['snap_in_lambda48_rate']:<16.3f}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("Interpretation:")
    lines.append("  * If exact match is 100%, the binary-Leech dual snap correctly solves the")
    lines.append("    transformation via Λ_48 lattice operations.")
    lines.append("  * If exact match is 0% but cell match is high, the snap is partially correct")
    lines.append("    — the operation is captured but the snap rounds to the wrong cell.")
    lines.append("  * If snap_in_lambda48 is 100%, the snap always lands in the lattice.")
    lines.append("    The trivial Construction-A snap (nearest multiple of 3) trivially lands")
    lines.append("    in Λ_48 because multiples of 3 are in the zero codeword.")
    return "\n".join(lines)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Iteration 8 Phase 2: binary-Leech dual snap via Λ_48")
    results = {}
    print("  Testing toggle...", end=" ", flush=True)
    t0 = time.time()
    results["toggle"] = test_toggle_dual_snap(n_samples=30)
    print(f"exact={results['toggle']['exact_count']}/30, cell_match={results['toggle']['mean_cell_match']:.3f}  ({time.time()-t0:.1f}s)")
    print("  Testing translate...", end=" ", flush=True)
    results["translate"] = test_translate_dual_snap(n_samples=30)
    print(f"exact={results['translate']['exact_count']}/30, cell_match={results['translate']['mean_cell_match']:.3f}")
    print("  Testing reflect_v...", end=" ", flush=True)
    results["reflect_v"] = test_reflect_v_dual_snap(n_samples=30)
    print(f"exact={results['reflect_v']['exact_count']}/30, cell_match={results['reflect_v']['mean_cell_match']:.3f}")
    txt = render(results)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    slim = {k: {k2: v2 for k2, v2 in v.items() if k2 != "samples"} for k, v in results.items()}
    with open(OUT_JSON, "w") as f:
        json.dump(slim, f, indent=2, default=str)
    print()
    print(txt)
    print(f"\nWrote: {OUT_JSON}")
    print(f"Wrote: {OUT_TXT}")


if __name__ == "__main__":
    main()
