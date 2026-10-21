#!/usr/bin/env python3
"""
Iteration 9 Phase 2 — Richer Λ_48 snap (syndrome-coset decoder).

Per rec #2: extend the substrate's nearest_lattice_point to Λ_48 by searching
all C(23) cosets over F_3 (not just the zero codeword). The trivial snap
from iteration 8 only considered the zero codeword — too coarse for non-zero
binary targets.

This phase implements a syndrome-coset decoder:
  1. Compute target mod 3 = r (a 48-tuple over F_3)
  2. Compute syndrome s = H · r (H = dual_ternary_generator, 24×48 over F_3)
  3. If s = 0, the target is already in C(23) — snap = target
  4. If s corresponds to a weight-1 error (48 cases), snap = target - e_i
  5. If s corresponds to a weight-2 error (C(48,2) = 1128 cases), search
  6. Otherwise (heavier errors), fall back to the trivial snap (zero codeword)

This gives a much better snap for most targets without exponential search.
"""

from __future__ import annotations
import sys, os, json, time
from fractions import Fraction
from typing import Dict, List, Any, Tuple, Optional
from itertools import combinations
import numpy as np

GLM_REPO = "/home/z/my-project/glm_repo"
sys.path.insert(0, GLM_REPO)
sys.path.insert(0, "/home/z/my-project/scripts")

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from glm_universal.substrate import leech2, mog, golay_decode, linalg
from glm_universal.substrate import lattice48
from bin_tasks import TASKS

OUT_JSON = "/home/z/my-project/data/iter9_richer_snap.json"
OUT_TXT  = "/home/z/my-project/data/iter9_richer_snap.txt"


# ============================================================================
# 1. Syndrome-coset decoder for Λ_48
# ============================================================================
_H48 = None
def _get_H48():
    global _H48
    if _H48 is None:
        _H48 = lattice48.dual_ternary_generator()
    return _H48

def compute_syndrome(r: Tuple[int, ...]) -> Tuple[int, ...]:
    """Compute syndrome s = H · r mod 3, where r is a 48-tuple over F_3."""
    H = _get_H48()
    s = []
    for i in range(24):
        si = sum(H[i][j] * r[j] for j in range(48)) % 3
        s.append(si)
    return tuple(s)

def in_lambda48(x: Tuple[int, ...]) -> bool:
    """Λ_48 membership: x ∈ Z^48 with x mod 3 ∈ C(23)."""
    H = _get_H48()
    x_mod3 = tuple(v % 3 for v in x)
    for i in range(24):
        s = sum(H[i][j] * x_mod3[j] for j in range(48)) % 3
        if s != 0:
            return False
    return True


# Precompute weight-1 and weight-2 coset leaders
_WEIGHT1_LEADERS = None
_WEIGHT2_LEADERS = None

def _build_weight1_leaders():
    """Weight-1 coset leaders: e_i for i=0..47, with all 3 values (1, 2) for each.
    Actually for F_3, a weight-1 vector has one nonzero coord (1 or 2). So 48*2 = 96 leaders.
    """
    global _WEIGHT1_LEADERS
    if _WEIGHT1_LEADERS is None:
        leaders = {}
        for i in range(48):
            for v in (1, 2):
                vec = [0] * 48
                vec[i] = v
                syndrome = compute_syndrome(tuple(vec))
                leaders[syndrome] = tuple(vec)
        _WEIGHT1_LEADERS = leaders
    return _WEIGHT1_LEADERS

def _build_weight2_leaders():
    """Weight-2 coset leaders: e_i + e_j for i<j, with values (1,1), (1,2), (2,1), (2,2).
    Total: C(48,2) * 4 = 1128 * 4 = 4512 leaders. But many will have the same syndrome.
    We keep the first (lowest-weight) leader per syndrome.
    """
    global _WEIGHT2_LEADERS
    if _WEIGHT2_LEADERS is None:
        print("    Building weight-2 coset leader table (4512 candidates)...", end=" ", flush=True)
        t0 = time.time()
        leaders = {}
        for i, j in combinations(range(48), 2):
            for vi in (1, 2):
                for vj in (1, 2):
                    vec = [0] * 48
                    vec[i] = vi
                    vec[j] = vj
                    syndrome = compute_syndrome(tuple(vec))
                    if syndrome not in leaders:
                        leaders[syndrome] = tuple(vec)
        _WEIGHT2_LEADERS = leaders
        print(f"done ({len(leaders)} unique syndromes, {time.time()-t0:.1f}s)")
    return _WEIGHT2_LEADERS


def snap_to_lambda48_rich(target_q: Tuple[Fraction, ...]) -> Tuple[int, ...]:
    """Snap a 48-D rational target to the nearest Λ_48 point.
    
    Algorithm:
      1. Round each coord to nearest integer -> target_int
      2. Compute r = target_int mod 3
      3. Compute syndrome s = H · r
      4. If s = 0, snap = target_int (already in lattice)
      5. If s in weight-1 leaders, snap = target_int - leader
      6. If s in weight-2 leaders, snap = target_int - leader
      7. Otherwise, fall back to trivial snap (round to zero codeword)
    """
    # Round to nearest integer
    target_int = tuple(int(round(float(v))) for v in target_q)
    # Compute r = target_int mod 3 (in {0, 1, 2})
    r = tuple(v % 3 for v in target_int)
    s = compute_syndrome(r)
    if all(si == 0 for si in s):
        # Already in lattice
        return target_int
    # Try weight-1 leaders
    w1 = _build_weight1_leaders()
    if s in w1:
        leader = w1[s]
        # snap = target_int - leader (in F_3, but in Z we just subtract)
        # Actually we need: snap mod 3 = r - leader mod 3, and snap ≈ target_int
        # So snap = target_int - leader (in Z, not mod 3) where leader is the F_3 vector
        snap = tuple(target_int[i] - leader[i] for i in range(48))
        return snap
    # Try weight-2 leaders
    w2 = _build_weight2_leaders()
    if s in w2:
        leader = w2[s]
        snap = tuple(target_int[i] - leader[i] for i in range(48))
        return snap
    # Fall back: trivial snap (round to nearest multiple of 3)
    return tuple(int(round(float(v) / 3)) * 3 for v in target_q)


# ============================================================================
# 2. Binary <-> Λ_48 encoding/decoding (from iteration 8)
# ============================================================================
def binary_to_lambda48(bits: int) -> Tuple[int, ...]:
    bits_list = [(bits >> (23 - i)) & 1 for i in range(24)]
    out = []
    for b in bits_list:
        out.append(3 * b)
        out.append(0)
    return tuple(out)

def lambda48_to_binary(point: Tuple[int, ...]) -> int:
    bits = 0
    for i in range(24):
        c = point[2 * i]
        b = 1 if c >= 2 else 0
        bits = (bits << 1) | b
    return bits

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
# 3. Lattice analogy at the Λ_48 level with RICHER snap
# ============================================================================
def lattice_analogy_lambda48_rich(a_bits: int, b_bits: int, c_bits: int) -> Dict[str, Any]:
    """Solve A : B :: C : ? at the Λ_48 level with the richer snap."""
    a = binary_to_lambda48(a_bits)
    b = binary_to_lambda48(b_bits)
    c = binary_to_lambda48(c_bits)
    # D* = C + (B - A) in Q^48
    d_star = tuple(Fraction(c[i]) + Fraction(b[i]) - Fraction(a[i])
                    for i in range(48))
    # Snap with the richer snap
    snap = snap_to_lambda48_rich(d_star)
    in_latt = in_lambda48(snap)
    pred_bits = lambda48_to_binary(snap)
    # Distance² between snap and D* (for diagnostics)
    dist2 = sum((Fraction(snap[i]) - d_star[i]) ** 2 for i in range(48))
    return {
        "a_bits": a_bits, "b_bits": b_bits, "c_bits": c_bits,
        "snap_first_10": list(snap[:10]),
        "snap_in_lambda48": in_latt,
        "pred_bits": pred_bits,
        "dist2_snap_to_dstar": str(dist2),
    }


# ============================================================================
# 4. Test on binary tasks (same as iteration 8)
# ============================================================================
def test_toggle(n_samples: int = 30) -> Dict[str, Any]:
    fam = TASKS["toggle"]
    results = []
    exact_count = 0
    for s in range(n_samples):
        a_grid, _, _ = fam.generate(seed=s + 1, H=4, W=6)
        b_grid = (1 - a_grid).astype(np.uint8)
        c_grid, _, _ = fam.generate(seed=s + 100, H=4, W=6)
        expected = (1 - c_grid).astype(np.uint8)
        a_bits = grid_to_bits_24(a_grid)
        b_bits = grid_to_bits_24(b_grid)
        c_bits = grid_to_bits_24(c_grid)
        result = lattice_analogy_lambda48_rich(a_bits, b_bits, c_bits)
        pred_grid = bits_to_grid(result["pred_bits"])
        exact = bool(np.array_equal(pred_grid, expected))
        cell_match = float((pred_grid == expected).mean())
        results.append({"seed": s + 1, "exact_match": exact,
                         "cell_match_rate": cell_match,
                         "snap_in_lambda48": result["snap_in_lambda48"]})
        if exact:
            exact_count += 1
    return {"task": "toggle", "n_samples": n_samples,
             "exact_count": exact_count, "exact_rate": exact_count / n_samples,
             "mean_cell_match": float(np.mean([r["cell_match_rate"] for r in results])),
             "snap_in_lambda48_rate": sum(1 for r in results if r["snap_in_lambda48"]) / n_samples}

def test_translate(n_samples: int = 30) -> Dict[str, Any]:
    fam = TASKS["translate"]
    results = []
    exact_count = 0
    for s in range(n_samples):
        a_grid, b_grid, _ = fam.generate(seed=s + 1, H=4, W=6, dx=1, dy=1)
        c_grid, expected, _ = fam.generate(seed=s + 100, H=4, W=6, dx=1, dy=1)
        a_bits = grid_to_bits_24(a_grid)
        b_bits = grid_to_bits_24(b_grid)
        c_bits = grid_to_bits_24(c_grid)
        result = lattice_analogy_lambda48_rich(a_bits, b_bits, c_bits)
        pred_grid = bits_to_grid(result["pred_bits"])
        exact = bool(np.array_equal(pred_grid, expected))
        cell_match = float((pred_grid == expected).mean())
        results.append({"seed": s + 1, "exact_match": exact,
                         "cell_match_rate": cell_match,
                         "snap_in_lambda48": result["snap_in_lambda48"]})
        if exact:
            exact_count += 1
    return {"task": "translate", "n_samples": n_samples,
             "exact_count": exact_count, "exact_rate": exact_count / n_samples,
             "mean_cell_match": float(np.mean([r["cell_match_rate"] for r in results])),
             "snap_in_lambda48_rate": sum(1 for r in results if r["snap_in_lambda48"]) / n_samples}

def test_reflect_v(n_samples: int = 30) -> Dict[str, Any]:
    fam = TASKS["reflect_v"]
    results = []
    exact_count = 0
    for s in range(n_samples):
        a_grid, b_grid, _ = fam.generate(seed=s + 1, H=4, W=6)
        c_grid, expected, _ = fam.generate(seed=s + 100, H=4, W=6)
        a_bits = grid_to_bits_24(a_grid)
        b_bits = grid_to_bits_24(b_grid)
        c_bits = grid_to_bits_24(c_grid)
        result = lattice_analogy_lambda48_rich(a_bits, b_bits, c_bits)
        pred_grid = bits_to_grid(result["pred_bits"])
        exact = bool(np.array_equal(pred_grid, expected))
        cell_match = float((pred_grid == expected).mean())
        results.append({"seed": s + 1, "exact_match": exact,
                         "cell_match_rate": cell_match,
                         "snap_in_lambda48": result["snap_in_lambda48"]})
        if exact:
            exact_count += 1
    return {"task": "reflect_v", "n_samples": n_samples,
             "exact_count": exact_count, "exact_rate": exact_count / n_samples,
             "mean_cell_match": float(np.mean([r["cell_match_rate"] for r in results])),
             "snap_in_lambda48_rate": sum(1 for r in results if r["snap_in_lambda48"]) / n_samples}


# ============================================================================
# 5. Render + main
# ============================================================================
def render(results: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 9 PHASE 2 — Richer Λ_48 snap (syndrome-coset decoder)")
    lines.append("=" * 96)
    lines.append("")
    lines.append("Per rec #2: extend nearest_lattice_point to Λ_48 by searching C(23) cosets.")
    lines.append("The trivial snap from iteration 8 only considered the zero codeword — too coarse.")
    lines.append("")
    lines.append("Algorithm:")
    lines.append("  1. Round target to nearest integer")
    lines.append("  2. Compute syndrome s = H · (target mod 3)")
    lines.append("  3. If s = 0, target is in C(23) — snap = target")
    lines.append("  4. If s in weight-1 leaders (96 candidates), snap = target - leader")
    lines.append("  5. If s in weight-2 leaders (1128*4=4512 candidates), snap = target - leader")
    lines.append("  6. Otherwise, fall back to trivial snap (zero codeword)")
    lines.append("")
    lines.append("-" * 96)
    lines.append("[Per-task results — comparison vs iteration 8's trivial snap]")
    lines.append("-" * 96)
    iter8_baseline = {
        "toggle":       {"exact_rate": 0.0,   "mean_cell_match": 0.474},
        "translate":    {"exact_rate": 0.467, "mean_cell_match": 0.900},
        "reflect_v":    {"exact_rate": 0.033, "mean_cell_match": 0.613},
    }
    lines.append(f"{'Task':<14}{'i8 exact':<14}{'i9 exact':<14}{'i8 cell match':<18}{'i9 cell match':<18}{'i9 snap in Λ_48':<16}")
    lines.append("-" * 96)
    for task_name, r in results.items():
        i8 = iter8_baseline.get(task_name, {"exact_rate": 0, "mean_cell_match": 0})
        lines.append(f"{task_name:<14}"
                     f"{100*i8['exact_rate']:.0f}%{'':<10}"
                     f"{100*r['exact_rate']:.0f}%{'':<10}"
                     f"{i8['mean_cell_match']:<18.3f}"
                     f"{r['mean_cell_match']:<18.3f}"
                     f"{r['snap_in_lambda48_rate']:<16.3f}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("Interpretation:")
    lines.append("  * If exact match improved, the richer snap correctly recovers the binary answer")
    lines.append("    from the analogy target D* = C + (B - A).")
    lines.append("  * If snap_in_lambda48 is still 100%, the snap always lands in the lattice")
    lines.append("    (as expected — the syndrome-coset decoder finds the nearest C(23) codeword).")
    return "\n".join(lines)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Iteration 9 Phase 2: richer Λ_48 snap (syndrome-coset decoder)")
    results = {}
    print("  Testing toggle...", end=" ", flush=True)
    t0 = time.time()
    results["toggle"] = test_toggle(n_samples=30)
    print(f"exact={results['toggle']['exact_count']}/30, cell_match={results['toggle']['mean_cell_match']:.3f}  ({time.time()-t0:.1f}s)")
    print("  Testing translate...", end=" ", flush=True)
    results["translate"] = test_translate(n_samples=30)
    print(f"exact={results['translate']['exact_count']}/30, cell_match={results['translate']['mean_cell_match']:.3f}")
    print("  Testing reflect_v...", end=" ", flush=True)
    results["reflect_v"] = test_reflect_v(n_samples=30)
    print(f"exact={results['reflect_v']['exact_count']}/30, cell_match={results['reflect_v']['mean_cell_match']:.3f}")
    txt = render(results)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    slim = {k: {k2: v2 for k2, v2 in v.items()} for k, v in results.items()}
    with open(OUT_JSON, "w") as f:
        json.dump(slim, f, indent=2, default=str)
    print()
    print(txt)
    print(f"\nWrote: {OUT_JSON}")
    print(f"Wrote: {OUT_TXT}")


if __name__ == "__main__":
    main()
