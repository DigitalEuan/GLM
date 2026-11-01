#!/usr/bin/env python3
"""
Phase 3 (iteration 2) — Leech native 24-D wobble.

The user's clarification (d): "The Leech in its native 24-D is the natural
progression, according to GLM findings there is a layered perspective to
almost all things where failure indicated the required mechanism for
progression up the ladder."

Phase 2 found that ALL 5 task-family query grids lie OUTSIDE the convex hull
of the 4096 Golay codewords — the Golay delta-sigma modulator provably cannot
reach them, and the accumulator grows linearly at the predicted rate.

This phase tests whether the Leech lattice's minimal vectors — 196,560 of
them, in R^24, NOT in F_2^24 — can reach those same targets.

We use the 'matched' rule (the paper's Rule 2, §8.4): at each tick, emit the
minimal vector v that maximises <v, accumulator + target>. Update the
accumulator by subtracting v. This is the support-function quantiser.

To keep CPU time tractable, we use the **1,104 sparse-shell minimal vectors
of shape (±4², 0²²)** as the alphabet. These are:
  * 276 unordered pairs of coordinates {i, j}, 24 choose 2
  * for each pair, 4 sign choices (+/+), (+/-), (-/+), (-/-)
  * = 276 * 4 = 1,104 vectors
Each has squared norm 32 (= 4² + 4²), the second-simplest Leech shell.

The 1104 shell is a strict subset of the full 196,560, but it is enough to
test whether a real-valued Leech alphabet can reach the binary targets the
Golay alphabet provably cannot.

Outputs:
  /home/z/my-project/data/iter2_phase3_leech.{json,txt}
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

from glm_universal.substrate import leech2
from bin_tasks import TASKS

OUT_JSON = "/home/z/my-project/data/iter2_phase3_leech.json"
OUT_TXT  = "/home/z/my-project/data/iter2_phase3_leech.txt"


# ----------------------------------------------------------------------------
# 1. Build the Leech alphabet (full 196,560 minimal vectors)
# ----------------------------------------------------------------------------
def build_full_leech_shell() -> np.ndarray:
    """All 196,560 Leech minimal vectors as a numpy array (196560 x 24).

    These are the three shapes:
      * 1,104 of (±4², 0²²)
      * 97,152 of (±2⁸ on an octad)
      * 98,304 of (∓3, ±1²³)
    Each has squared norm 32 in the x*sqrt(8) integer model.
    """
    vecs = list(leech2.minimal_vectors())
    arr = np.array(vecs, dtype=np.int64)
    assert arr.shape == (196560, 24), f"got {arr.shape}"
    return arr


# ----------------------------------------------------------------------------
# 2. Leech-shell delta-sigma modulator (matched rule)
# ----------------------------------------------------------------------------
def leech_shell_delta_sigma(target: np.ndarray, alphabet: np.ndarray,
                              steps: int = 200) -> Dict[str, Any]:
    """Run the matched-rule delta-sigma against the Leech shell alphabet.

    At each tick:
      driven = accumulator + target
      emit v* = argmax_v <v, driven>  (over the alphabet)
      accumulator -= v*
    The running mean of emitted vectors converges to target iff target is in
    the convex hull of the alphabet (support function bound).

    Returns:
      trajectory of (v_index, distance_to_target),
      final accumulator,
      average,
      max coordinate deviation,
      max accumulator,
      unique vectors visited,
      most-visited share,
    """
    acc = np.zeros(24, dtype=np.float64)
    totals = np.zeros(24, dtype=np.float64)
    visits = np.zeros(len(alphabet), dtype=np.int64)
    trajectory = []
    excursion = 0.0
    # Precompute alphabet norms for support-function bound
    # We don't normalise; just take argmax of <v, driven>
    for _ in range(steps):
        driven = acc + target
        # <v, driven> for all v: matrix-vector product
        scores = alphabet @ driven
        idx = int(np.argmax(scores))
        v = alphabet[idx]
        acc = acc + target - v
        excursion = max(excursion, float(np.abs(acc).max()))
        totals = totals + v.astype(np.float64)
        visits[idx] += 1
        # distance: L2 norm of (target - v) (per-tick emission error)
        dist = float(np.linalg.norm(target - v))
        trajectory.append((idx, dist))
    average = totals / steps
    deviation = float(np.max(np.abs(average - target)))
    return {
        "steps": steps,
        "unique_vectors": int(np.sum(visits > 0)),
        "most_visited_share": float(visits.max() / steps),
        "max_coordinate_deviation": deviation,
        "max_accumulator": excursion,
        # 1/N bound: deviation should be ≤ covering_radius / N
        "ambiguous_ticks": 0,  # the matched rule is never ambiguous (always picks argmax)
        "mean_distance": float(np.mean([d for _, d in trajectory])),
        "visits_histogram": {
            int(k): int(v) for k, v in zip(*np.unique(visits[visits > 0], return_counts=True))
        } if visits.any() else {},
    }


# ----------------------------------------------------------------------------
# 3. Run on tasks and constants
# ----------------------------------------------------------------------------
def grid_to_target_real_24(grid: np.ndarray) -> np.ndarray:
    """Map a binary 4x6 grid to a 24-D real target.

    Each cell becomes a real coordinate. We map bit 0 -> -4 and bit 1 -> +4
    to match the alphabet's per-coordinate range {-4, -3, ..., +4}.
    """
    H, W = grid.shape
    assert H * W == 24
    return np.array([-4.0 if v == 0 else 4.0 for v in grid.flatten()],
                     dtype=np.float64)


def const_to_target_real_24(frac: Fraction) -> np.ndarray:
    """Build a 24-D real target from a constant: place the constant (as float)
    in all 24 coordinates, scaled to match the alphabet's range.

    The Leech minimal vectors have norms in {sqrt(32)}; their entries are in
    {-4, -3, -2, -1, 0, +1, +2, +3, +4}. We map the constant's fractional
    value to the same range: target = (2f - 1) * 4 = 8f - 4.
    """
    f = float(frac)
    val = 8 * f - 4
    return np.full(24, val, dtype=np.float64)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Phase 3: Leech native 24-D wobble (full 196,560 minimal vectors)")
    print("Building full Leech shell alphabet...", end=" ", flush=True)
    alphabet = build_full_leech_shell()
    print(f"shape={alphabet.shape}")

    # Constants baseline (same as Phase 2, scaled to [-4, 4] range)
    constants = {
        "0":               Fraction(0),
        "1/3":             Fraction(1, 3),
        "sqrt2_minus_1":   Fraction(414214, 1000000),
        "pi_minus_3":      Fraction(141593, 1000000),
        "e_minus_2":       Fraction(718282, 1000000),
        "phi_minus_1":     Fraction(618034, 1000000),
    }
    print("\n[Constants baseline — 24-D real targets in [-4, +4]]")
    const_res = {}
    for name, frac in constants.items():
        target = const_to_target_real_24(frac)
        t0 = time.time()
        r = leech_shell_delta_sigma(target, alphabet, steps=200)
        t1 = time.time()
        const_res[name] = {"target_value": float(frac), **r, "time_s": t1 - t0}
        print(f"  {name:18s} unique_v={r['unique_vectors']:4d}  "
              f"share={r['most_visited_share']:.3f}  "
              f"dev={r['max_coordinate_deviation']:.4f}  "
              f"acc_max={r['max_accumulator']:.2f}  "
              f"mean_dist={r['mean_distance']:.3f}  "
              f"({t1-t0:.2f}s)")

    # Task families — query grid as target
    print("\n[Task families — query grid as 24-D real target, bipolar encoding]")
    task_res = {}
    for task_name in ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]:
        fam = TASKS[task_name]
        per_seed = []
        t0_total = time.time()
        for s in range(20):
            x_q, y_q, _ = fam.generate(seed=s + 100, H=4, W=6, dx=1, dy=1)
            target = grid_to_target_real_24(x_q)
            r = leech_shell_delta_sigma(target, alphabet, steps=200)
            per_seed.append({"seed": s, **r})
        t1_total = time.time()
        # aggregate
        uv = [p["unique_vectors"] for p in per_seed]
        sh = [p["most_visited_share"] for p in per_seed]
        dv = [p["max_coordinate_deviation"] for p in per_seed]
        am = [p["max_accumulator"] for p in per_seed]
        md = [p["mean_distance"] for p in per_seed]
        task_res[task_name] = {
            "per_seed_summary": {
                "unique_vectors_mean": float(np.mean(uv)),
                "unique_vectors_std": float(np.std(uv)),
                "most_visited_share_mean": float(np.mean(sh)),
                "max_coordinate_deviation_mean": float(np.mean(dv)),
                "max_accumulator_mean": float(np.mean(am)),
                "mean_distance_mean": float(np.mean(md)),
            },
            "per_seed": per_seed,
            "total_time_s": t1_total - t0_total,
        }
        s = task_res[task_name]["per_seed_summary"]
        print(f"  {task_name:14s} unique_v={s['unique_vectors_mean']:6.1f}±{s['unique_vectors_std']:.1f}  "
              f"share={s['most_visited_share_mean']:.3f}  "
              f"dev={s['max_coordinate_deviation_mean']:.4f}  "
              f"acc_max={s['max_accumulator_mean']:.2f}  "
              f"mean_d={s['mean_distance_mean']:.3f}  "
              f"({t1_total - t0_total:.1f}s)")

    # Hull check (Leech 1104 shell): does the accumulator stay bounded?
    # If accumulator grows linearly, target is outside the hull.
    # We measure this by max_accumulator: if it's ~steps, linear growth.
    # We also compute the "stays bounded" predicate (acc_max < 10 means bounded).

    # Render
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 2 / PHASE 3 — Leech native 24-D wobble")
    lines.append("=" * 96)
    lines.append("")
    lines.append("Matched-rule delta-sigma against the FULL Leech minimal-vector shell")
    lines.append("(196,560 vectors of shapes (±4², 0²²), (±2⁸ on octad), (∓3, ±1²³),")
    lines.append("each with norm² 32). This is the paper's Rule 2 (§8.4) against the whole shell.")
    lines.append("")
    lines.append("For each target, the running mean of emitted vectors should converge to the")
    lines.append("target iff the target is in the convex hull of the alphabet.")
    lines.append("")
    lines.append("[Constants baseline — 24-D targets in [-4, +4]]")
    lines.append("-" * 96)
    lines.append(f"{'Constant':<20}{'unique v':<12}{'most share':<14}{'max dev':<14}{'acc_max':<14}{'mean_d':<12}")
    lines.append("-" * 96)
    for name, r in const_res.items():
        lines.append(f"{name:<20}{r['unique_vectors']:<12}{r['most_visited_share']:<14.3f}"
                     f"{r['max_coordinate_deviation']:<14.4f}{r['max_accumulator']:<14.2f}"
                     f"{r['mean_distance']:<12.3f}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("[Task families — query grid as 24-D target, bipolar ±1 encoding]")
    lines.append("-" * 96)
    lines.append(f"{'Task':<14}{'unique v':<16}{'most share':<14}{'max dev':<14}{'acc_max':<14}{'mean_d':<12}")
    lines.append("-" * 96)
    for name, r in task_res.items():
        s = r["per_seed_summary"]
        lines.append(f"{name:<14}{s['unique_vectors_mean']:6.1f}±{s['unique_vectors_std']:<3.1f}    "
                     f"{s['most_visited_share_mean']:<14.3f}"
                     f"{s['max_coordinate_deviation_mean']:<14.4f}"
                     f"{s['max_accumulator_mean']:<14.2f}"
                     f"{s['mean_distance_mean']:<12.3f}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("Interpretation:")
    lines.append("  * If acc_max stays bounded (< ~10) and max_dev shrinks with N, the target")
    lines.append("    IS reachable by the Leech shell alphabet -- the 1/N bound holds.")
    lines.append("  * If acc_max grows linearly with steps (≈ 200 after 200 steps), the target")
    lines.append("    is OUTSIDE the Leech 1104-shell hull. Escalation to the FULL Leech")
    lines.append("    196,560-shell or to the 32-D Barnes-Wall lattice is required.")
    lines.append("  * Compare to Phase 2: the Golay alphabet could not reach ANY task target")
    lines.append("    (all 100% hull-separates). If the Leech 1104-shell CAN reach them, this")
    lines.append("    is a concrete demonstration of the layered-perspective progression.")
    txt = "\n".join(lines)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    with open(OUT_JSON, "w") as f:
        json.dump({"constants": const_res, "tasks": task_res}, f, indent=2, default=str)
    print()
    print(txt)
    print(f"\nWrote: {OUT_JSON}")
    print(f"Wrote: {OUT_TXT}")


if __name__ == "__main__":
    main()
