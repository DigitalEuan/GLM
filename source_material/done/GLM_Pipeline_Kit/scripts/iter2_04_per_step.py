#!/usr/bin/env python3
"""
Phase 4 (iteration 2) — Step-by-step cost in multi-step transformation traces.

The user's clarification (c): "intermediate steps are part of (b) here - we
need to take every operation step-by-step and explicitly measure, map and
investigate each step - this is the information the GLM is to learn from."

We already collected per-step trace costs in Phase 1. This phase analyses them:
for each multi-step task (translate: 4 steps; bfs_shortest: many steps), we
extract the per-step syndrome, codeword weight, TAX, and coset weight, and
visualise where the cost spikes — the "decision points" the GLM must learn.

Outputs:
  /home/z/my-project/data/iter2_phase4_per_step.{json,txt}
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

from glm_universal.substrate import leech2, mog, golay_decode, linalg
from bin_tasks import TASKS

OUT_JSON = "/home/z/my-project/data/iter2_phase4_per_step.json"
OUT_TXT  = "/home/z/my-project/data/iter2_phase4_per_step.txt"

# Y from §9.1 of the academic paper
Y_CONST = Fraction(1) / (Fraction(355, 113) + Fraction(2) / Fraction(355, 113))
TAX_PER_W = Y_CONST + Fraction(1, 8)


def grid_to_bits_24(grid: np.ndarray) -> int:
    H, W = grid.shape
    assert H * W == 24
    bits = 0
    for v in grid.flatten():
        bits = (bits << 1) | int(v & 1)
    return bits


def step_cost(x_bits: int, y_bits: int) -> Dict[str, Any]:
    delta = x_bits ^ y_bits
    dec = golay_decode.decode_complete(delta)
    if dec.corrected is not None:
        cw = dec.corrected
        cw_w = linalg.popcount(cw)
    else:
        cands = dec.candidates if hasattr(dec, "candidates") else None
        if cands:
            cw = min(cands, key=lambda c: (linalg.popcount(c), c))
            cw_w = linalg.popcount(cw)
        else:
            cw, cw_w = None, None
    tax = (cw_w * TAX_PER_W) if cw_w is not None else None
    return {
        "delta_weight": linalg.popcount(delta),
        "coset_weight": dec.weight,
        "syndrome": dec.syndrome,
        "codeword_weight": cw_w,
        "tax": float(tax) if tax is not None else None,
        "ambiguous": (dec.weight == 4),
    }


def measure_task_trace(task_name: str, n_samples: int = 50, H: int = 4, W: int = 6) -> Dict[str, Any]:
    """For each trace, record per-step cost. Aggregate by step label."""
    fam = TASKS[task_name]
    per_step_costs: Dict[str, List[Dict[str, Any]]] = {}
    trace_lengths = []
    for i in range(n_samples):
        x, y, trace = fam.generate(seed=i + 1, H=H, W=W, dx=1, dy=1)
        trace_lengths.append(len(trace))
        prev = grid_to_bits_24(x)
        for label, grid in trace:
            if grid.size != 24:
                continue
            gb = grid_to_bits_24(grid)
            sc = step_cost(prev, gb)
            per_step_costs.setdefault(label, []).append(sc)
            prev = gb
    # Aggregate per step
    summary = {}
    for label, costs in per_step_costs.items():
        deltas = [c["delta_weight"] for c in costs]
        cosets = [c["coset_weight"] for c in costs]
        taxes  = [c["tax"] for c in costs if c["tax"] is not None]
        ambig  = [c["ambiguous"] for c in costs]
        cw_ws  = [c["codeword_weight"] for c in costs if c["codeword_weight"] is not None]
        summary[label] = {
            "n_samples": len(costs),
            "delta_weight_mean": float(np.mean(deltas)),
            "coset_weight_mean": float(np.mean(cosets)),
            "coset_weight_histogram": {int(k): int(v) for k, v in
                                         zip(*np.unique(cosets, return_counts=True))},
            "tax_mean": float(np.mean(taxes)) if taxes else None,
            "ambiguous_rate": float(np.mean(ambig)),
            "codeword_weight_mean": float(np.mean(cw_ws)) if cw_ws else None,
            "codeword_weight_histogram": {int(k): int(v) for k, v in
                                          zip(*np.unique(cw_ws, return_counts=True))} if cw_ws else {},
        }
    return {
        "task": task_name,
        "n_samples": n_samples,
        "trace_length_mean": float(np.mean(trace_lengths)),
        "trace_length_min": int(np.min(trace_lengths)),
        "trace_length_max": int(np.max(trace_lengths)),
        "per_step": summary,
    }


def render(results: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 2 / PHASE 4 — Per-step cost in multi-step traces")
    lines.append("=" * 96)
    lines.append("")
    lines.append("For each task with a multi-step trace, measure the per-step F_2 cost")
    lines.append("(syndrome, coset weight), codeword weight, and TAX. Identify decision")
    lines.append("points where the cost spikes — these are the escalation triggers the GLM")
    lines.append("must learn to handle.")
    lines.append("")
    for name, r in results.items():
        lines.append(f"--- {name} (trace length mean = {r['trace_length_mean']:.1f}, "
                     f"min = {r['trace_length_min']}, max = {r['trace_length_max']}) ---")
        lines.append(f"{'Step':<24}{'Δ wt':<10}{'coset wt':<14}{'TAX':<10}{'ambig%':<10}{'cw wt':<10}")
        for step_label, s in r["per_step"].items():
            tax_str = f"{s['tax_mean']:.3f}" if s['tax_mean'] is not None else "N/A"
            cw_str  = f"{s['codeword_weight_mean']:.1f}" if s['codeword_weight_mean'] is not None else "N/A"
            lines.append(f"{step_label:<24}"
                         f"{s['delta_weight_mean']:<10.2f}"
                         f"{s['coset_weight_mean']:<14.2f}"
                         f"{tax_str:<10}"
                         f"{100*s['ambiguous_rate']:<10.1f}"
                         f"{cw_str:<10}")
        lines.append("")
    lines.append("Interpretation:")
    lines.append("  * Steps where coset_weight = 4 are ESCALATION TRIGGERS: the substrate")
    lines.append("    cannot decide which octad to credit, and must lift to a higher lattice.")
    lines.append("  * Steps where codeword_weight > 0 (with coset_weight = 0) are CODEWORD")
    lines.append("    OPERATIONS: the displacement IS a codeword, and the substrate can")
    lines.append("    execute it exactly. The cost is the codeword's TAX.")
    lines.append("  * Steps where coset_weight ∈ {1, 2, 3} are WELL-DEFINED but require")
    lines.append("    syndrome decoding — the substrate handles them, but the operation is")
    lines.append("    not a pure codeword move.")
    return "\n".join(lines)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Phase 4: per-step cost analysis (50 samples per task)")
    results = {}
    for name in ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]:
        print(f"  {name}...", end=" ", flush=True)
        results[name] = measure_task_trace(name, n_samples=50)
        print(f"trace length mean = {results[name]['trace_length_mean']:.1f}")
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
