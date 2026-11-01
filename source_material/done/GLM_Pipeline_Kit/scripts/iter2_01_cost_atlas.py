#!/usr/bin/env python3
"""
Phase 1 (iteration 2) — Golay-syndrome cost atlas.

The user's clarification (a): "The Golay code isn't just for error correction,
when we don't want to change data we use it as a measuring device to see the
cost and inner working of any given data transaction."

So for every transition x -> y, we measure:
  * F_2 cost: the syndrome weight of (x XOR y) — the coset weight of the
    displacement, in {0,1,2,3,4} for the Golay code (4 = deep hole).
  * TAX cost: if the displacement's nearest codeword has Hamming weight w,
    TAX = w * (Y + 1/8) where Y = 1/(pi + 2/pi) ≈ 0.2647.
    The minimal codeword TAX is 8Y + 1 = 3.1174 (the 759 octads).
  * Symmetry tax of x and y individually (the codeword weight of x, y
    if they are themselves codewords; else 0).

Outputs:
  /home/z/my-project/data/iter2_phase1_atlas.{json,txt}
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

OUT_JSON = "/home/z/my-project/data/iter2_phase1_atlas.json"
OUT_TXT  = "/home/z/my-project/data/iter2_phase1_atlas.txt"

# The Y constant from the GLM academic paper (§9.1):
#   Y = 1/(pi + 2/pi)
# We use exact rational approximation via Fraction. The paper uses
# pi ≈ 355/113 (a continued-fraction convergent); we keep Y as the
# same approximation the substrate would: a Fraction.
Y_CONST = Fraction(1) / (Fraction(355, 113) + Fraction(2) / Fraction(355, 113))
# TAX per weight unit
TAX_PER_W = Y_CONST + Fraction(1, 8)


def grid_to_bits_24(grid: np.ndarray) -> int:
    H, W = grid.shape
    assert H * W == 24, f"grid must pack to 24 bits, got {H}x{W}={H*W}"
    bits = 0
    for v in grid.flatten():
        bits = (bits << 1) | int(v & 1)
    return bits


def transition_cost(x_bits: int, y_bits: int) -> Dict[str, Any]:
    """Measure the F_2 + TAX cost of the transition x -> y."""
    delta = x_bits ^ y_bits
    # Syndrome of the delta
    dec = golay_decode.decode_complete(delta)
    syn = dec.syndrome
    coset_w = dec.weight          # 0..4 (coset leader weight)
    # The nearest codeword to delta has weight = popcount(corrected) if
    # unambiguous, else None. For TAX we want the WEIGHT of the codeword
    # (which is a measure of the "energy" of the displacement as a codeword).
    # The substrate's decoder gives `corrected` as the codeword; in ambiguous
    # cases (coset_w=4) it returns None and we pick the lowest-weight candidate.
    if dec.corrected is not None:
        cw = dec.corrected
        cw_w = linalg.popcount(cw)
    else:
        # pick the candidate with the smallest weight (deterministic)
        cands = dec.candidates if hasattr(dec, "candidates") else None
        if cands:
            cw = min(cands, key=lambda c: (linalg.popcount(c), c))
            cw_w = linalg.popcount(cw)
        else:
            cw, cw_w = None, None
    # Also: the displacement itself has a Hamming weight (number of changed cells)
    delta_w = linalg.popcount(delta)
    # TAX
    tax = (cw_w * TAX_PER_W) if cw_w is not None else None
    return {
        "delta_weight": delta_w,
        "coset_weight": coset_w,
        "syndrome": syn,
        "codeword_weight": cw_w,
        "tax": float(tax) if tax is not None else None,
        "tax_exact_str": f"{tax.numerator}/{tax.denominator}" if tax is not None else None,
        "ambiguous": (coset_w == 4),
        "is_codeword_delta": (coset_w == 0),
    }


def per_state_cost(bits: int) -> Dict[str, Any]:
    """Cost of the state itself: its distance to the nearest codeword (F_2 cost
    of "holding" this state)."""
    dec = golay_decode.decode_complete(bits)
    return {
        "coset_weight": dec.weight,
        "syndrome": dec.syndrome,
        "ambiguous": (dec.weight == 4),
    }


def measure_task_family(name: str, n_samples: int = 100, H: int = 4, W: int = 6) -> Dict[str, Any]:
    """Measure transition costs across n_samples demonstrations of one task family."""
    fam = TASKS[name]
    rows = []
    for i in range(n_samples):
        x, y, trace = fam.generate(seed=i + 1, H=H, W=W, dx=1, dy=1)
        x_b = grid_to_bits_24(x)
        y_b = grid_to_bits_24(y)
        # Full transition cost
        tc = transition_cost(x_b, y_b)
        # State costs
        x_state = per_state_cost(x_b)
        y_state = per_state_cost(y_b)
        # Intermediate steps: cost of each transition in the trace
        trace_costs = []
        prev = x_b
        for label, grid in trace:
            gb = grid_to_bits_24(grid) if grid.size == 24 else None
            if gb is None:
                continue
            tc_step = transition_cost(prev, gb)
            trace_costs.append({"step": label, "from": prev, "to": gb, **tc_step})
            prev = gb
        rows.append({
            "seed": i + 1, "x_bits": x_b, "y_bits": y_b,
            "transition_cost": tc,
            "x_state_cost": x_state,
            "y_state_cost": y_state,
            "trace_costs": trace_costs,
        })
    # Aggregate
    deltas = [r["transition_cost"]["delta_weight"] for r in rows]
    cosets = [r["transition_cost"]["coset_weight"] for r in rows]
    taxes  = [r["transition_cost"]["tax"] for r in rows if r["transition_cost"]["tax"] is not None]
    ambig  = sum(1 for r in rows if r["transition_cost"]["ambiguous"])
    cw_weights = [r["transition_cost"]["codeword_weight"] for r in rows
                   if r["transition_cost"]["codeword_weight"] is not None]
    # syndrome histogram
    syndromes = [r["transition_cost"]["syndrome"] for r in rows]
    n_unique_syndromes = len(set(syndromes))
    return {
        "task": name,
        "n_samples": n_samples,
        "delta_weight_mean": float(np.mean(deltas)),
        "delta_weight_std":  float(np.std(deltas)),
        "coset_weight_mean": float(np.mean(cosets)),
        "coset_weight_std":  float(np.std(cosets)),
        "coset_weight_histogram": {int(k): int(v) for k, v in np.histogram(cosets, bins=range(6))[0]
                                    .tolist() and
                                    zip(range(5), np.histogram(cosets, bins=range(6))[0])},
        "tax_mean": float(np.mean(taxes)) if taxes else None,
        "tax_std":  float(np.std(taxes))  if taxes else None,
        "ambiguous_count": ambig,
        "ambiguous_rate": ambig / n_samples,
        "codeword_weight_histogram": {int(k): int(v) for k, v in
                                       zip(*np.unique(cw_weights, return_counts=True))
                                       if cw_weights},
        "unique_syndromes": n_unique_syndromes,
        "syndrome_concentration": float(max(np.bincount(syndromes))) / n_samples,
        "rows": rows,
    }


def render(atlas: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 2 / PHASE 1 — Golay-syndrome cost atlas")
    lines.append("=" * 96)
    lines.append("")
    lines.append("Golay as a measuring device: for each transition x -> y on a 4x6 grid (24 bits),")
    lines.append("measure the F_2 cost (coset weight, syndrome) and the TAX cost (codeword weight")
    lines.append(f"times Y + 1/8, where Y = 1/(pi + 2/pi) = {float(Y_CONST):.6f}).")
    lines.append("")
    lines.append("-" * 96)
    lines.append(f"{'Task':<14}{'Δ wt':<14}{'coset wt':<16}{'TAX':<14}{'ambig%':<10}{'unique synd':<14}")
    lines.append("-" * 96)
    for name, agg in atlas.items():
        lines.append(
            f"{name:<14}"
            f"{agg['delta_weight_mean']:.2f}±{agg['delta_weight_std']:.2f}    "
            f"{agg['coset_weight_mean']:.2f}±{agg['coset_weight_std']:.2f}    "
            f"{agg['tax_mean']:.4f}     "
            f"{100*agg['ambiguous_rate']:.1f}%    "
            f"{agg['unique_syndromes']}"
        )
    lines.append("-" * 96)
    lines.append("")
    lines.append("Interpretation:")
    lines.append("  * coset wt 0 = the displacement is itself a Golay codeword (an octad or 0).")
    lines.append("    This means the F_2 quotient 'sees' the transition as a no-op; the rule is")
    lines.append("    invisible at the binary substrate level (Note 5's failure mode).")
    lines.append("  * coset wt 4 = the displacement sits at a deep hole (sextet ambiguity).")
    lines.append("    The substrate cannot decide which octad to credit the change to. This is an")
    lines.append("    escalation trigger — the substrate must lift to a higher layer to disambiguate.")
    lines.append("  * TAX is the per-transition 'energy' on the substrate. The minimum non-zero TAX")
    lines.append("    is at octads (weight 8 codewords), TAX = 8Y + 1 = 3.1174. A transition with")
    lines.append("    TAX > 3.1174 costs more; a transition with coset_wt 0 AND codeword wt 0 is the")
    lines.append("    identity (no movement).")
    lines.append("")
    lines.append("Per-task signatures:")
    for name, agg in atlas.items():
        lines.append(f"  {name}:")
        lines.append(f"    coset weight histogram: {agg['coset_weight_histogram']}")
        lines.append(f"    codeword weight histogram: {agg['codeword_weight_histogram']}")
        lines.append(f"    unique syndromes: {agg['unique_syndromes']} (concentration: {agg['syndrome_concentration']:.3f})")
    return "\n".join(lines)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    atlas = {}
    print("Phase 1: Golay-syndrome cost atlas (100 samples per task family)...")
    for name in ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]:
        print(f"  measuring {name}...", end=" ", flush=True)
        atlas[name] = measure_task_family(name, n_samples=100)
        print(f"mean coset wt = {atlas[name]['coset_weight_mean']:.2f}, "
              f"unique syndromes = {atlas[name]['unique_syndromes']}")
    txt = render(atlas)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    with open(OUT_JSON, "w") as f:
        json.dump(atlas, f, indent=2, default=str)
    print()
    print(txt)
    print(f"\nWrote: {OUT_JSON}")
    print(f"Wrote: {OUT_TXT}")


if __name__ == "__main__":
    main()
