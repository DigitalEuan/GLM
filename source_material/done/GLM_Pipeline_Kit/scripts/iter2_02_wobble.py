#!/usr/bin/env python3
"""
Phase 2 (iteration 2) — Delta-sigma wobble signatures.

The user's clarification (b): "looking simply at the difference between any
two data changes is not enough, we also need to look at the path it takes,
not just the start/end points or nodes - what is the exact shape of this
'decision'."

The substrate exposes `golay_delta_sigma(target, steps, rule)` which runs a
deterministic error-feedback loop against the 4,096 Golay codewords. For each
task family, we use the QUERY GRID (the input we want to transform) as the
24-coordinate target, run the wobble for N=200 steps, and record:

  * trajectory length
  * unique codewords visited
  * most_visited_share  (how concentrated the orbit is)
  * mean_distance       (mean L1 distance from the emitted codeword to target)
  * max_coordinate_deviation (does the running average converge?)
  * within_one_over_n   (is the 1/N bound respected?)
  * ambiguous_ticks     (how often the decoder hit a sextet tie)
  * max_accumulator     (the worst excursion)

Each task family should have a CHARACTERISTIC wobble signature. We also run
the wobble on known constants (√2, π, e, 1/3) as a reference baseline — the
GLM paper reports these have distinct "vibrational signatures".

Outputs:
  /home/z/my-project/data/iter2_phase2_wobble.{json,txt}
"""

from __future__ import annotations
import sys, os, json
from fractions import Fraction
from typing import Dict, List, Any, Tuple
import numpy as np

GLM_REPO = "/home/z/my-project/glm_repo"
sys.path.insert(0, GLM_REPO)
sys.path.insert(0, "/home/z/my-project/scripts")

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from glm_universal.reasoning import exact_real
from glm_universal.substrate import leech2, mog, golay_decode, linalg
from bin_tasks import TASKS

OUT_JSON = "/home/z/my-project/data/iter2_phase2_wobble.json"
OUT_TXT  = "/home/z/my-project/data/iter2_phase2_wobble.txt"


def grid_to_target_24(grid: np.ndarray) -> Tuple[Fraction, ...]:
    """Map a binary grid to a 24-coordinate target in [0,1]^24 (one coord per cell)."""
    H, W = grid.shape
    assert H * W == 24
    # Each cell becomes its own coordinate; the binary value 0/1 maps to 0/1 directly.
    # (We could also use ±1/2 to center the alphabet; the substrate's delta_sigma
    # accepts any rational in [0,1].)
    return tuple(Fraction(int(v)) for v in grid.flatten())


def run_wobble(name: str, target: Tuple[Fraction, ...], steps: int = 200,
                rule: str = "nearest") -> Dict[str, Any]:
    res = exact_real.golay_delta_sigma(target, steps, rule=rule)
    # Drop the heavy trajectory for storage; keep summary stats
    return {
        "task": name,
        "rule": rule,
        "steps": res["steps"],
        "unique_codewords": res["unique_codewords"],
        "most_visited_share": float(res["most_visited_share"]),
        "mean_distance": float(res["mean_distance"]),
        "max_coordinate_deviation": float(res["max_coordinate_deviation"]),
        "within_one_over_n": bool(res["within_one_over_n"]),
        "ambiguous_ticks": res["ambiguous_ticks"],
        "max_accumulator": float(res["max_accumulator"]),
        # also: entropy of the visit distribution
        # (we'll re-derive this from the trajectory, which we kept)
    }


def run_hull(target: Tuple[Fraction, ...], steps: int = 400) -> Dict[str, Any]:
    """Run hull_certificate to test whether the target lies inside the convex hull
    of the 4096 codewords. If 'separates' is True, the target is provably
    UNREACHABLE by ANY quantiser rule."""
    cert = exact_real.hull_certificate(target, steps)
    return {
        "value_at_target": float(cert["value_at_target"]),
        "max_over_codewords": float(cert["max_over_codewords"]),
        "separates": bool(cert["separates"]),
        "gap": float(cert["gap"]),
        "steps": cert["steps"],
    }


def known_constant_target(name: str) -> Tuple[Fraction, ...]:
    """Build a 24-coordinate target from a known constant.

    We replicate the paper's setup (§5.4): the fractional target is placed
    in ALL 24 coordinates, so the wobble's task is to track a single scalar
    constant using the 24-bit alphabet.
    """
    if name == "1/3":
        f = Fraction(1, 3)
    elif name == "sqrt2_minus_1":
        # use 414214/1000000 as the rational approximation
        f = Fraction(414214, 1000000)
    elif name == "pi_minus_3":
        f = Fraction(141593, 1000000)
    elif name == "e_minus_2":
        f = Fraction(718282, 1000000)
    elif name == "phi_minus_1":
        f = Fraction(618034, 1000000)
    elif name == "0":
        f = Fraction(0)
    else:
        raise ValueError(name)
    return tuple(f for _ in range(24))


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Phase 2: Delta-sigma wobble signatures")
    # (a) constants baseline
    constants = ["0", "1/3", "sqrt2_minus_1", "pi_minus_3", "e_minus_2", "phi_minus_1"]
    print("\n[Constants baseline]")
    const_results = {}
    for c in constants:
        target = known_constant_target(c)
        w = run_wobble(f"const:{c}", target, steps=400)
        h = run_hull(target, steps=200)
        const_results[c] = {"wobble": w, "hull": h}
        print(f"  {c:18s} unique_cw={w['unique_codewords']:4d}  "
              f"share={w['most_visited_share']:.3f}  "
              f"dev={w['max_coordinate_deviation']:.4f}  "
              f"ambig={w['ambiguous_ticks']:3d}  "
              f"hull_separates={h['separates']}")

    # (b) task families
    print("\n[Task families — query grid as target]")
    task_results = {}
    for name in ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]:
        fam = TASKS[name]
        # Run on 20 different query grids and aggregate
        per_seed = []
        for s in range(20):
            x_q, y_q, _ = fam.generate(seed=s + 100, H=4, W=6, dx=1, dy=1)
            target = grid_to_target_24(x_q)
            w = run_wobble(f"{name}_q{s}", target, steps=400)
            h = run_hull(target, steps=200)
            per_seed.append({"seed": s, "wobble": w, "hull": h})
        # Aggregate
        uniq = [p["wobble"]["unique_codewords"] for p in per_seed]
        share = [p["wobble"]["most_visited_share"] for p in per_seed]
        dev = [p["wobble"]["max_coordinate_deviation"] for p in per_seed]
        ambig = [p["wobble"]["ambiguous_ticks"] for p in per_seed]
        acc = [p["wobble"]["max_accumulator"] for p in per_seed]
        sep_count = sum(1 for p in per_seed if p["hull"]["separates"])
        task_results[name] = {
            "per_seed_summary": {
                "unique_codewords_mean": float(np.mean(uniq)),
                "unique_codewords_std": float(np.std(uniq)),
                "most_visited_share_mean": float(np.mean(share)),
                "max_coordinate_deviation_mean": float(np.mean(dev)),
                "ambiguous_ticks_mean": float(np.mean(ambig)),
                "max_accumulator_mean": float(np.mean(acc)),
                "hull_separates_rate": sep_count / 20,
            },
            "per_seed": per_seed,
        }
        s = task_results[name]["per_seed_summary"]
        print(f"  {name:14s} unique={s['unique_codewords_mean']:6.1f}±{s['unique_codewords_std']:.1f}  "
              f"share={s['most_visited_share_mean']:.3f}  "
              f"dev={s['max_coordinate_deviation_mean']:.4f}  "
              f"ambig={s['ambiguous_ticks_mean']:.1f}  "
              f"acc_max={s['max_accumulator_mean']:.2f}  "
              f"hull_sep={100*s['hull_separates_rate']:.0f}%")

    # Render text
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 2 / PHASE 2 — Delta-sigma wobble signatures")
    lines.append("=" * 96)
    lines.append("")
    lines.append("Golay delta-sigma modulator (the 'wobble'): for each 24-coordinate target,")
    lines.append("run the substrate's exact_real.golay_delta_sigma for 400 ticks. The")
    lines.append("trajectory visits codewords; the accumulator tracks target error.")
    lines.append("")
    lines.append("[Constants baseline] (24 coordinates all = the fractional target)")
    lines.append("-" * 96)
    lines.append(f"{'Constant':<20}{'unique cw':<12}{'most share':<14}{'max dev':<14}{'ambig':<10}{'hull sep':<12}")
    lines.append("-" * 96)
    for c, r in const_results.items():
        w = r["wobble"]; h = r["hull"]
        lines.append(f"{c:<20}{w['unique_codewords']:<12}{w['most_visited_share']:<14.3f}"
                     f"{w['max_coordinate_deviation']:<14.4f}{w['ambiguous_ticks']:<10}"
                     f"{str(h['separates']):<12}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("[Task families — query grid flattened to 24-bit target]")
    lines.append("-" * 96)
    lines.append(f"{'Task':<14}{'unique cw':<14}{'most share':<14}{'max dev':<14}{'ambig':<10}{'hull sep%':<12}")
    lines.append("-" * 96)
    for name, r in task_results.items():
        s = r["per_seed_summary"]
        lines.append(f"{name:<14}"
                     f"{s['unique_codewords_mean']:6.1f}±{s['unique_codewords_std']:<3.1f}    "
                     f"{s['most_visited_share_mean']:<14.3f}"
                     f"{s['max_coordinate_deviation_mean']:<14.4f}"
                     f"{s['ambiguous_ticks_mean']:<10.1f}"
                     f"{100*s['hull_separates_rate']:<12.0f}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("Interpretation:")
    lines.append("  * 'unique cw' = number of distinct codewords the wobble visits.")
    lines.append("    High -> orbit is diverse; the target is far from any codeword.")
    lines.append("    Low  -> orbit concentrates on a few codewords (target IS close to a")
    lines.append("            codeword, or the substrate has a periodic attractor there).")
    lines.append("  * 'most share' = the fraction of ticks spent at the most-visited codeword.")
    lines.append("    1.0 = stuck at a single codeword (target IS a codeword).")
    lines.append("  * 'max dev' = the worst coordinate-wise deviation of the running average")
    lines.append("    from the target. If within 1/400 = 0.0025, the 1/N bound holds.")
    lines.append("  * 'hull sep' = True iff the target lies OUTSIDE the convex hull of the")
    lines.append("    4,096 codewords. Such targets are PROVABLY UNREACHABLE by any")
    lines.append("    quantiser rule — the substrate must escalate to a higher lattice.")
    txt = "\n".join(lines)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    with open(OUT_JSON, "w") as f:
        json.dump({"constants": const_results, "tasks": task_results},
                   f, indent=2, default=str)
    print()
    print(txt)
    print(f"\nWrote: {OUT_JSON}")
    print(f"Wrote: {OUT_TXT}")


if __name__ == "__main__":
    main()
