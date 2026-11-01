#!/usr/bin/env python3
"""
Iteration 8 Phase 1 — Junction method for shared Leech coordinates.

Per user input: "the 'Junction' GLM method (in the GLM repository) could help
here, many things are practically the same operation and the GLM can understand
that way also."

The substrate's coordinate_junction.py implements junctions:
  * A junction is the set of carriers at one exact coordinate vector.
  * junctions(rows) returns groups of carriers sharing coordinates.
  * For our binary targets, the trivial 3x Λ_48 embedding collapses ALL binary
    targets to the same point (the zero Leech point). So they're all in ONE
    junction.

This phase:
  1. Build "carrier rows" for our binary task targets (using Leech class as
     the coordinate)
  2. Use junctions() to find shared-coordinate groups
  3. Test: do binary targets that share a Leech class also share task structure?
     (e.g., do all "even-parity" targets cluster in one junction?)
  4. Modify the rule-learner to use JUNCTION LABELS instead of per-target
     classification
"""

from __future__ import annotations
import sys, os, json, time, random
from fractions import Fraction
from typing import Dict, List, Any, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

GLM_REPO = "/home/z/my-project/glm_repo"
sys.path.insert(0, GLM_REPO)
sys.path.insert(0, "/home/z/my-project/scripts")

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from glm_universal.substrate import leech2, mog, golay_decode, linalg
from glm_universal.substrate import superposition as sup_mod
from bin_tasks import TASKS

OUT_JSON = "/home/z/my-project/data/iter8_junction.json"
OUT_TXT  = "/home/z/my-project/data/iter8_junction.txt"


# ============================================================================
# 1. Build "carrier rows" for our binary targets
# ============================================================================
# The substrate's coordinate_junction.junctions(rows) expects rows of the form:
#   rows[i] = (label, [...other fields...], coordinate_tuple)
# where _coords(rows, i) returns tuple(Fraction(x) for x in rows[i][2]).
#
# For our binary targets, the "coordinate" is the Leech CLASS (mod 2Λ), which
# is a 24-bit integer. We treat this as a 24-tuple of {0, 1} Fractions.

def grid_to_bits_24(grid: np.ndarray) -> int:
    bits = 0
    for v in grid.flatten():
        bits = (bits << 1) | int(v & 1)
    return bits

def bits_to_coord_24(bits: int) -> Tuple[Fraction, ...]:
    """Convert 24-bit int to 24-tuple of Fractions (the 'coordinate' for junction)."""
    return tuple(Fraction((bits >> (23 - i)) & 1) for i in range(24))

def leech_class_as_coord(bits: int) -> Tuple[Fraction, ...]:
    """Use the Leech CLASS (mod 2Λ) as the carrier coordinate.
    
    For a binary target, we compute:
      - The 4x scaled vector's Leech class (via class_of if in Leech)
      - OR the binary target's representation in the F_2 quotient
    
    For targets outside Leech (odd parity), we use the F_2 binary itself.
    For targets inside Leech (even parity), we use the Leech class index.
    """
    bits_list = [(bits >> (23 - i)) & 1 for i in range(24)]
    # Try principal coset: 4*bits
    t_principal = tuple(4 * b for b in bits_list)
    try:
        if leech2.in_leech(t_principal):
            cls = leech2.class_of(t_principal)
            # Use the 24-bit class index as the coordinate
            return tuple(Fraction((cls >> (23 - i)) & 1) for i in range(24))
    except Exception:
        pass
    # Fallback: use the binary target itself
    return tuple(Fraction(b) for b in bits_list)


def build_carrier_rows(n_samples: int = 50) -> List[Tuple]:
    """Build carrier rows for all 5 task families, n_samples each.
    
    Each row: (label, task_name, coordinate_tuple, parity, n_ones, snap_layer)
    """
    rows = []
    for task_name in ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]:
        fam = TASKS[task_name]
        for s in range(n_samples):
            x, _, _ = fam.generate(seed=s + 1, H=4, W=6, dx=1, dy=1)
            bits = grid_to_bits_24(x)
            n_ones = sum((bits >> (23 - i)) & 1 for i in range(24))
            parity = "even" if n_ones % 2 == 0 else "odd"
            coord = leech_class_as_coord(bits)
            # Determine snap layer (which lattice succeeds)
            t_principal = tuple(4 * ((bits >> (23 - i)) & 1) for i in range(24))
            in_leech = leech2.in_leech(t_principal)
            snap_layer = "Leech_24" if in_leech else "higher_lattice"
            label = f"{task_name}_s{s+1}"
            rows.append((label, task_name, list(coord), parity, n_ones, snap_layer))
    return rows


# ============================================================================
# 2. Find junctions (carrier groups sharing coordinates)
# ============================================================================
def find_junctions(rows: List[Tuple]) -> Dict[str, Any]:
    """Find junctions (groups of carriers with the same coordinate)."""
    groups: Dict[Tuple, List[int]] = {}
    for i, row in enumerate(rows):
        coord = tuple(Fraction(x) for x in row[2])
        groups.setdefault(coord, []).append(i)
    junctions = sorted([tuple(g) for g in groups.values() if len(g) > 1])
    singletons = [g for g in groups.values() if len(g) == 1]
    return {
        "n_carriers": len(rows),
        "n_unique_coords": len(groups),
        "n_junctions": len(junctions),
        "n_singletons": len(singletons),
        "junction_sizes": [len(j) for j in junctions],
        "junctions": junctions[:10],  # first 10 for inspection
        "junction_member_tasks": [
            [rows[i][1] for i in j] for j in junctions[:10]
        ],
    }


# ============================================================================
# 3. Test: do binary targets that share a Leech class also share task structure?
# ============================================================================
def junction_task_correlation(rows: List[Tuple], junctions_info: Dict) -> Dict[str, Any]:
    """For each junction, check if all members come from the same task family."""
    junctions = junctions_info["junctions"]
    same_task_count = 0
    mixed_task_count = 0
    same_parity_count = 0
    mixed_parity_count = 0
    for j in junctions:
        tasks_in_junction = set(rows[i][1] for i in j)
        parities_in_junction = set(rows[i][3] for i in j)
        if len(tasks_in_junction) == 1:
            same_task_count += 1
        else:
            mixed_task_count += 1
        if len(parities_in_junction) == 1:
            same_parity_count += 1
        else:
            mixed_parity_count += 1
    return {
        "n_junctions": len(junctions),
        "same_task_junctions": same_task_count,
        "mixed_task_junctions": mixed_task_count,
        "same_parity_junctions": same_parity_count,
        "mixed_parity_junctions": mixed_parity_count,
        "same_task_rate": same_task_count / max(1, len(junctions)),
        "same_parity_rate": same_parity_count / max(1, len(junctions)),
    }


# ============================================================================
# 4. Modify rule-learner to use JUNCTION LABELS
# ============================================================================
class JunctionAwareGLM(nn.Module):
    """Rule-learner that predicts the JUNCTION LABEL (not the per-target lattice).
    
    Instead of classifying per-target into lattice layers, classify by junction
    membership. Carriers in the same junction get the same prediction.
    """
    def __init__(self, hidden_dim=64, n_junction_classes=8):
        super().__init__()
        # 27 inputs: 24 bits + parity + sup_dim + sup_amb
        self.encoder = nn.Sequential(
            nn.Linear(27, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
        )
        # Junction class head (predicts which junction the target belongs to)
        self.junction_head = nn.Linear(hidden_dim, n_junction_classes)
        # Snap head (predicts whether snap succeeds)
        self.snap_head = nn.Linear(hidden_dim, 1)
    
    def forward(self, x):
        h = self.encoder(x)
        return {
            "junction": self.junction_head(h),
            "snap": self.snap_head(h).squeeze(-1),
        }


# We won't fully train this model in this run; instead we'll measure the
# junction distribution and document the development requirements.

# ============================================================================
# 5. Render + main
# ============================================================================
def render(junctions_info: Dict, correlation: Dict) -> str:
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 8 PHASE 1 — Junction method for shared Leech coordinates")
    lines.append("=" * 96)
    lines.append("")
    lines.append("Per user input: the 'Junction' GLM method could help — many things are")
    lines.append("practically the same operation and the GLM can understand that way also.")
    lines.append("")
    lines.append("The substrate's coordinate_junction.py implements junctions: a junction is")
    lines.append("the set of carriers at one exact coordinate vector. For our binary targets,")
    lines.append("the 'coordinate' is the Leech CLASS (mod 2Λ). Carriers sharing a Leech class")
    lines.append("are in the same junction.")
    lines.append("")
    lines.append("-" * 96)
    lines.append("[Junction distribution — 50 samples per task, 250 carriers total]")
    lines.append("-" * 96)
    lines.append(f"  n_carriers:        {junctions_info['n_carriers']}")
    lines.append(f"  n_unique_coords:   {junctions_info['n_unique_coords']}")
    lines.append(f"  n_junctions:       {junctions_info['n_junctions']}  (groups of >= 2 carriers sharing a coord)")
    lines.append(f"  n_singletons:      {junctions_info['n_singletons']}")
    if junctions_info['junction_sizes']:
        lines.append(f"  junction_sizes:   {junctions_info['junction_sizes'][:10]}{'...' if len(junctions_info['junction_sizes']) > 10 else ''}")
    lines.append("")
    lines.append("-" * 96)
    lines.append("[Junction-task correlation — do same-coord carriers come from same task?]")
    lines.append("-" * 96)
    lines.append(f"  same_task_junctions:    {correlation['same_task_junctions']}/{correlation['n_junctions']} ({100*correlation['same_task_rate']:.1f}%)")
    lines.append(f"  mixed_task_junctions:   {correlation['mixed_task_junctions']}/{correlation['n_junctions']} ({100*(1-correlation['same_task_rate']):.1f}%)")
    lines.append(f"  same_parity_junctions:  {correlation['same_parity_junctions']}/{correlation['n_junctions']} ({100*correlation['same_parity_rate']:.1f}%)")
    lines.append(f"  mixed_parity_junctions:{correlation['mixed_parity_junctions']}/{correlation['n_junctions']} ({100*(1-correlation['same_parity_rate']):.1f}%)")
    lines.append("")
    lines.append("Interpretation:")
    lines.append("  * If same_task_rate is high, junctions correlate with task family — the")
    lines.append("    GLM can use junction membership as a task discriminator.")
    lines.append("  * If same_parity_rate is high, junctions correlate with parity — the")
    lines.append("    GLM can use junction membership as a parity discriminator (the user's")
    lines.append("    'many things are practically the same operation' insight).")
    lines.append("  * If mixed_parity_rate is high, junctions contain both even AND odd")
    lines.append("    parity targets — meaning the Leech class doesn't distinguish parity.")
    lines.append("    This would be a development issue: the coordinate (Leech class) needs")
    lines.append("    to be enriched to separate parity.")
    return "\n".join(lines)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Iteration 8 Phase 1: Junction method for shared Leech coordinates")
    print("  Building carrier rows (50 samples per task, 250 carriers)...")
    rows = build_carrier_rows(n_samples=50)
    print(f"  Built {len(rows)} carrier rows")
    junctions_info = find_junctions(rows)
    print(f"  Found {junctions_info['n_junctions']} junctions "
          f"(sizes: {junctions_info['junction_sizes'][:5]}...)")
    correlation = junction_task_correlation(rows, junctions_info)
    print(f"  Same-task rate: {100*correlation['same_task_rate']:.1f}%, "
          f"Same-parity rate: {100*correlation['same_parity_rate']:.1f}%")
    txt = render(junctions_info, correlation)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    with open(OUT_JSON, "w") as f:
        json.dump({
            "junctions_info": {k: v for k, v in junctions_info.items() if k != "junctions"},
            "junctions_first_10": [
                {"members": list(j), "tasks": junctions_info["junction_member_tasks"][i]}
                for i, j in enumerate(junctions_info["junctions"][:10])
            ],
            "correlation": correlation,
        }, f, indent=2, default=str)
    print()
    print(txt)
    print(f"\nWrote: {OUT_JSON}")
    print(f"Wrote: {OUT_TXT}")


if __name__ == "__main__":
    main()
