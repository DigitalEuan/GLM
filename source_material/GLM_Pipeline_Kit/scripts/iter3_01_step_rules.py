#!/usr/bin/env python3
"""
Iteration 3 — Step-rule library + Construction-C Leech snap as rule composition.

The user's insight: the step rules (popcount, Hamming, sphere-packing, octad
enumeration, theta series, pair census) are the GLM's learning primitives.
Each is a computational primitive at a specific layer of the
F_2 -> Hamming -> G_23 -> G_24 -> Lambda_24 -> Co_0 chain.

This module defines the 6 step rules as clean callables, then implements the
Construction-C Leech snap AS A COMPOSITION OF THESE RULES — showing which
rule is invoked at each stage of the snap.

The 6 step rules (one per layer):

  Layer 1: F_2     popcount(x)            count 1-bits in a 24-bit word
  Layer 2: Hamming hamming(x, y)          XOR-then-popcount (the metric)
  Layer 3: G_23    sphere_packing(n, k)    combinatorial sum check (C(n,k) sum)
  Layer 4: G_24    enumerate_octads()     list the 759 octads (Steiner S(5,8,24))
  Layer 5: Lambda   theta_coefficient(N)   theta series coefficient (E_4^3 - 720*Delta)
  Layer 6: Co_0     pair_census()          invariants over 98,280 type-2 axes
"""

from __future__ import annotations
import sys, os, json
from fractions import Fraction
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from math import comb

GLM_REPO = "/home/z/my-project/glm_repo"
sys.path.insert(0, GLM_REPO)
sys.path.insert(0, "/home/z/my-project/scripts")

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from glm_universal.substrate import leech2, mog, golay_decode, linalg
from bin_tasks import TASKS

OUT_JSON = "/home/z/my-project/data/iter3_step_rules.json"
OUT_TXT  = "/home/z/my-project/data/iter3_step_rules.txt"


# ============================================================================
# The 6 step rules
# ============================================================================

class StepRule:
    """A named step rule with a layer, a cost (in substrate calls), and a callable."""
    def __init__(self, name: str, layer: str, callable_, cost: str):
        self.name = name
        self.layer = layer
        self.callable_ = callable_
        self.cost = cost
    def __call__(self, *args, **kwargs):
        return self.callable_(*args, **kwargs)
    def describe(self) -> str:
        return f"{self.name} [{self.layer}] cost={self.cost}"


def _popcount(bits: int) -> int:
    return linalg.popcount(bits)

def _hamming(x: int, y: int) -> int:
    return linalg.popcount(x ^ y)

def _sphere_packing_check(n: int, k: int) -> bool:
    """Check that sum_{i=0..k} C(n, i) = 2^(n - k_dim) where k_dim = n - log2(sum).
    For G_23 = [23,12,7]: sum_{i=0..3} C(23,i) = 1 + 23 + 253 + 1771 = 2048 = 2^11.
    """
    s = sum(comb(n, i) for i in range(k + 1))
    return s & (s - 1) == 0  # is s a power of 2?

def _enumerate_octads() -> List[int]:
    return list(mog.OCTAD_MASKS)

def _theta_coefficient(N: int) -> int:
    return leech2.theta_series(max(N + 1, 1))[N]

def _pair_census() -> Dict[int, int]:
    return dict(leech2.pair_census())


STEP_RULES = {
    "popcount":      StepRule("popcount",      "F_2",     _popcount,             "1 popcount call"),
    "hamming":       StepRule("hamming",       "Hamming", _hamming,              "1 XOR + 1 popcount"),
    "sphere_packing":StepRule("sphere_packing","G_23",    _sphere_packing_check, "1 combinatorial sum"),
    "octads":        StepRule("octads",        "G_24",    _enumerate_octads,     "759 octads (one-time)"),
    "theta":         StepRule("theta",         "Lambda",  _theta_coefficient,    "1 modular-form coefficient"),
    "pair_census":   StepRule("pair_census",   "Co_0",    _pair_census,          "exhaustive over 98,280 axes"),
}


# ============================================================================
# Construction-C Leech snap AS A COMPOSITION OF STEP RULES
# ============================================================================
#
# The snap takes a 24-D real target and rounds it to the nearest Leech lattice
# point. Construction C requires:
#   (mod 2) all coords even OR all coords odd
#   (mod 4) the set {i : x_i = 2 mod 4} (even) or {i : x_i = 3 mod 4} (odd)
#           is a Golay codeword support
#   (mod 8) sum(x) = 0 mod 8 (even coset) or 4 mod 8 (odd coset)
#
# Each step uses ONE STEP RULE:
#   - parity check: popcount (counts the 1s; for parity mod 2)
#   - Hamming distance to candidate Golay codewords: hamming
#   - sphere-packing check: confirms we're at a valid [n, k, d] code
#   - octad enumeration: lists the weight-8 codewords (one is used as the support)
#   - theta series: verifies the lattice level (optional sanity)
#   - pair census: not invoked here (used at the Co_0 layer, above Λ_24)

def snap_to_leech_with_trace(target_bits: int) -> Dict[str, Any]:
    """Snap a 24-bit binary target to a Leech lattice point, recording each step rule.

    Returns a dict with:
      'principal_candidate': 4*target_bits (if in Leech)
      'odd_candidate':       4*target_bits + glue (if in Leech, with chosen glue)
      'in_principal':       bool
      'in_odd':             bool
      'parity':             'even' or 'odd' (popcount of target_bits mod 2)
      'wall':               str or None (the wall hit, if any)
      'trace':              list of (step_rule_name, layer, input, output, note)
    """
    trace: List[Tuple[str, str, Any, Any, str]] = []
    n_ones = STEP_RULES["popcount"](target_bits)
    trace.append(("popcount", "F_2", target_bits, n_ones,
                   f"Number of 1-bits in the target word"))

    parity = "even" if n_ones % 2 == 0 else "odd"
    # The principal candidate: scale by 4 (each bit becomes 0 or 4)
    t_principal = tuple(4 * ((target_bits >> (23 - i)) & 1) for i in range(24))
    sum_p = sum(t_principal)
    trace.append(("sum_mod_8", "G_24 (mod-8 sum condition)",
                   t_principal, sum_p % 8,
                   f"Sum of coords mod 8 (need 0 for principal coset, 4 for odd)"))

    in_principal = leech2.in_leech(t_principal)
    trace.append(("in_leech", "Lambda_24 (full Construction-C test)",
                   t_principal, in_principal,
                   "Principal-coset candidate membership"))

    # Odd-coset candidate: scale by 4, add canonical glue (-3, +1^23)
    # NOTE: For odd parity (n_ones odd), sum(target) = 4*n_ones + sum(glue).
    # With glue = (-3, +1^23), sum(glue) = 20. For odd parity 4*n_ones ≡ 4 mod 8,
    # so sum(target) ≡ 4 + 20 = 24 ≡ 0 mod 8 -- WRONG coset (needs 4 mod 8).
    # For even parity, sum(target) ≡ 0 + 20 = 20 ≡ 4 mod 8 -- CORRECT (odd coset).
    glue_canonical = (-3,) + (1,) * 23
    t_odd = tuple(4 * ((target_bits >> (23 - i)) & 1) + g for i, g in enumerate(glue_canonical))
    sum_o = sum(t_odd)
    trace.append(("sum_mod_8", "G_24 (mod-8 sum condition for odd coset)",
                   t_odd, sum_o % 8,
                   f"Odd-coset candidate sum mod 8 (need 4)"))
    in_odd = leech2.in_leech(t_odd)
    trace.append(("in_leech", "Lambda_24 (full Construction-C test, odd coset)",
                   t_odd, in_odd,
                   "Odd-coset candidate membership"))

    # Parity wall: if odd, neither candidate works
    wall = None
    if parity == "odd" and not in_principal and not in_odd:
        wall = ("parity_wall: odd-parity binary targets cannot be encoded as "
                "Leech lattice points via 4*binary + canonical glue. The substrate "
                "must escalate to a higher lattice (Barnes-Wall Lambda_32 or "
                "ternary Lambda_48) or use a non-trivial Golay-codeword lift.")

    # Hamming distance to nearest codeword (rule invocation for diagnostic)
    dec = golay_decode.decode_complete(target_bits)
    nearest_cw = dec.corrected if dec.corrected is not None else (
        min(dec.candidates, key=lambda c: (linalg.popcount(c), c))
        if dec.candidates else None)
    if nearest_cw is not None:
        d_h = STEP_RULES["hamming"](target_bits, nearest_cw)
        trace.append(("hamming", "Hamming", (target_bits, nearest_cw), d_h,
                       "Hamming distance from target to nearest Golay codeword"))
        # octad check: if nearest_cw is an octad (weight 8), invoke octads rule
        cw_w = STEP_RULES["popcount"](nearest_cw)
        if cw_w == 8:
            trace.append(("octads", "G_24", nearest_cw, "octad",
                           "The nearest codeword IS an octad (weight-8 codeword)"))
        elif cw_w == 0:
            trace.append(("octads", "G_24", nearest_cw, "zero codeword",
                           "Target is itself a codeword (zero syndrome)"))
        else:
            trace.append(("octads", "G_24", nearest_cw, f"codeword weight {cw_w}",
                           "Nearest codeword is not an octad; weight != 8"))

    return {
        "target_bits": target_bits,
        "n_ones": n_ones,
        "parity": parity,
        "principal_candidate": t_principal,
        "in_principal": in_principal,
        "odd_candidate": t_odd,
        "in_odd": in_odd,
        "wall": wall,
        "trace": trace,
    }


# ============================================================================
# Run on all binary task families
# ============================================================================
def grid_to_bits(grid: np.ndarray) -> int:
    bits = 0
    for v in grid.flatten():
        bits = (bits << 1) | int(v & 1)
    return bits


def measure_task(name: str, n_samples: int = 50) -> Dict[str, Any]:
    fam = TASKS[name]
    snap_results = []
    rule_invocation_counts: Dict[str, int] = {r: 0 for r in STEP_RULES}
    parity_count = {"even": 0, "odd": 0}
    wall_count = 0
    for s in range(n_samples):
        x, _, _ = fam.generate(seed=s + 1, H=4, W=6, dx=1, dy=1)
        bits = grid_to_bits(x)
        snap = snap_to_leech_with_trace(bits)
        snap_results.append({
            "seed": s + 1, "bits": bits, "n_ones": snap["n_ones"],
            "parity": snap["parity"],
            "in_principal": snap["in_principal"],
            "in_odd": snap["in_odd"],
            "wall": snap["wall"] is not None,
        })
        parity_count[snap["parity"]] += 1
        if snap["wall"]:
            wall_count += 1
        # Count rule invocations
        for entry in snap["trace"]:
            rule_name = entry[0]
            if rule_name in rule_invocation_counts:
                rule_invocation_counts[rule_name] += 1
    return {
        "task": name,
        "n_samples": n_samples,
        "parity_distribution": parity_count,
        "wall_count": wall_count,
        "wall_rate": wall_count / n_samples,
        "in_principal_rate": sum(1 for r in snap_results if r["in_principal"]) / n_samples,
        "in_odd_rate": sum(1 for r in snap_results if r["in_odd"]) / n_samples,
        "rule_invocation_counts": rule_invocation_counts,
        "snap_results": snap_results,
    }


def render(results: Dict[str, Any], sample_traces: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 3 — Step-rule library + Construction-C Leech snap")
    lines.append("=" * 96)
    lines.append("")
    lines.append("The 6 step rules (one per substrate layer):")
    for r in STEP_RULES.values():
        lines.append(f"  {r.describe()}")
    lines.append("")
    lines.append("-" * 96)
    lines.append("[Per-task snap results — 50 samples each]")
    lines.append("-" * 96)
    lines.append(f"{'Task':<14}{'even parity':<14}{'odd parity':<14}{'wall rate':<14}"
                 f"{'in principal':<14}{'in odd':<14}")
    lines.append("-" * 96)
    for name, r in results.items():
        p = r["parity_distribution"]
        lines.append(f"{name:<14}"
                     f"{p['even']:<14}{p['odd']:<14}"
                     f"{100*r['wall_rate']:<14.1f}"
                     f"{100*r['in_principal_rate']:<14.1f}"
                     f"{100*r['in_odd_rate']:<14.1f}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("[Rule invocation counts per task (summed across 50 samples)]")
    lines.append("-" * 96)
    lines.append(f"{'Task':<14}{'popcount':<12}{'hamming':<12}{'octads':<10}{'sum_mod_8':<12}{'in_leech':<12}")
    lines.append("-" * 96)
    for name, r in results.items():
        c = r["rule_invocation_counts"]
        lines.append(f"{name:<14}"
                     f"{c.get('popcount',0):<12}"
                     f"{c.get('hamming',0):<12}"
                     f"{c.get('octads',0):<10}"
                     f"{c.get('sum_mod_8',0):<12}"
                     f"{c.get('in_leech',0):<12}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("[Sample trace for one target per task — the step rules in action]")
    lines.append("=" * 96)
    for name, snap in sample_traces.items():
        lines.append(f"\n--- {name} (target_bits = {snap['target_bits']:08x}, n_ones = {snap['n_ones']}, "
                     f"parity = {snap['parity']}) ---")
        for i, (rule, layer, inp, out, note) in enumerate(snap["trace"]):
            inp_str = str(inp)[:50] + ("..." if len(str(inp)) > 50 else "")
            out_str = str(out)[:50] + ("..." if len(str(out)) > 50 else "")
            lines.append(f"  step {i+1}: {rule:<14} [{layer:<28}]  in={inp_str:<25}  out={out_str:<15}  -- {note}")
        if snap["wall"]:
            lines.append(f"  WALL: {snap['wall']}")
        else:
            verdict = "IN LEECH (principal)" if snap["in_principal"] else ("IN LEECH (odd coset)" if snap["in_odd"] else "OUTSIDE LEECH")
            lines.append(f"  VERDICT: {verdict}")
    return "\n".join(lines)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Iteration 3: step-rule library + Construction-C snap")
    results = {}
    sample_traces = {}
    for name in ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]:
        print(f"  {name}...", end=" ", flush=True)
        results[name] = measure_task(name, n_samples=50)
        # Pick a representative sample (first seed) for the trace display
        fam = TASKS[name]
        x, _, _ = fam.generate(seed=1, H=4, W=6, dx=1, dy=1)
        bits = grid_to_bits(x)
        sample_traces[name] = snap_to_leech_with_trace(bits)
        p = results[name]["parity_distribution"]
        print(f"even/odd = {p['even']}/{p['odd']}, wall rate = {100*results[name]['wall_rate']:.0f}%")
    txt = render(results, sample_traces)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    with open(OUT_JSON, "w") as f:
        json.dump({"results": results, "sample_traces": {k: {**v, "trace": [(list(t)[:4] + [t[4]]) for t in v["trace"]]} for k, v in sample_traces.items()}},
                   f, indent=2, default=str)
    print()
    print(txt)
    print(f"\nWrote: {OUT_JSON}")
    print(f"Wrote: {OUT_TXT}")


if __name__ == "__main__":
    main()
