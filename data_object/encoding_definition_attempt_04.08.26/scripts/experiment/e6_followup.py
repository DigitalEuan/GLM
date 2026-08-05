"""
E6 follow-up: deeper exploration of the real signals.

1. diff_seed normal-vector alignment (r ≈ ±0.37 vs BE) — explore more seed offsets
2. std_clearance (r = -0.31 vs ΔH) — investigate
3. Operator count metrics — check for real signal beyond the artifact
4. Per-bit normal alignment — which bit positions carry the most signal?
"""

from __future__ import annotations

import sys
import json
import math
import statistics
from pathlib import Path
from fractions import Fraction

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import ubp_kb_loader as kb
import stacked_mog_grids as smg
from e1_e2_e3_kb_sweep import KNOWN_PAIRS

OUT_DIR = Path("/home/z/my-project/download")


def explore_seed_offsets():
    """Sweep many seed_offset_b values to find the best normal-alignment signal."""
    print("=" * 78)
    print("E6 FOLLOW-UP — Seed offset sweep for normal-vector alignment")
    print("=" * 78)
    print()
    print("Using sq4_z7 config (cell_w=4, cell_h=4, z=7.0)")
    print("Sweeping seed_offset_b from 0 to 500 in steps of 5")
    print()

    results = []
    for seed_b in range(0, 501, 5):
        scene = smg.StackedMOGScene(
            cell_w=4.0, cell_h=4.0, z_offset=7.0,
            seed_offset_a=0, seed_offset_b=seed_b,
        )
        be_vals = []
        dh_vals = []
        aa_dots_be = []
        aa_angles_be = []
        aa_dots_dh = []
        aa_angles_dh = []

        for sym_a, sym_b, be, dh, _ in KNOWN_PAIRS:
            ea = kb.get_element(sym_a)
            eb = kb.get_element(sym_b)
            if ea is None or eb is None: continue
            m = scene.compute_pair_metrics(ea.vector24, eb.vector24)
            be_vals.append(be)
            aa_dots_be.append(m["aa_mean_normal_dot"])
            aa_angles_be.append(m["aa_mean_normal_angle"])
            if dh is not None and dh != 0:
                dh_vals.append(dh)
                aa_dots_dh.append(m["aa_mean_normal_dot"])
                aa_angles_dh.append(m["aa_mean_normal_angle"])

        r_dot_be = statistics.correlation(aa_dots_be, be_vals) if statistics.pstdev(aa_dots_be) > 0 else 0
        r_ang_be = statistics.correlation(aa_angles_be, be_vals) if statistics.pstdev(aa_angles_be) > 0 else 0
        r_dot_dh = statistics.correlation(aa_dots_dh, dh_vals) if statistics.pstdev(aa_dots_dh) > 0 else 0
        r_ang_dh = statistics.correlation(aa_angles_dh, dh_vals) if statistics.pstdev(aa_angles_dh) > 0 else 0

        results.append({
            "seed_b": seed_b,
            "r_dot_be": r_dot_be,
            "r_ang_be": r_ang_be,
            "r_dot_dh": r_dot_dh,
            "r_ang_dh": r_ang_dh,
            "max_abs_r": max(abs(r_dot_be), abs(r_ang_be), abs(r_dot_dh), abs(r_ang_dh)),
        })

    # Sort by max |r|
    results.sort(key=lambda x: -x["max_abs_r"])
    print(f"Top 20 seed_offset_b values by max |r|:")
    print(f"{'seed_b':>7} {'r_dot_BE':>9} {'r_ang_BE':>9} {'r_dot_dH':>9} {'r_ang_dH':>9}")
    for r in results[:20]:
        print(f"{r['seed_b']:>7} {r['r_dot_be']:>+9.4f} {r['r_ang_be']:>+9.4f} "
              f"{r['r_dot_dh']:>+9.4f} {r['r_ang_dh']:>+9.4f}")

    return results


def explore_operator_counts():
    """Check operator count metrics for real signal (not the residual artifact)."""
    print()
    print("=" * 78)
    print("E6 FOLLOW-UP — Operator count metrics")
    print("=" * 78)
    print()
    print("Checking if operator COUNT (not residual) carries signal.")
    print("Using sq4_z7_DIV_SUB config (same-pos→DIVIDE, diagonal→SUBTRACT)")
    print()

    scene = smg.StackedMOGScene(cell_w=4.0, cell_h=4.0, z_offset=7.0)

    be_vals = []
    dh_vals = []
    metrics = {k: [] for k in [
        "n_operator_pairs", "same_position_op_count", "active_active_op_count",
        "op_count_MULTIPLY", "op_count_DIVIDE", "op_count_ADD", "op_count_SUBTRACT",
        "aa_op_count_MULTIPLY", "aa_op_count_DIVIDE",
        "aa_op_count_ADD", "aa_op_count_SUBTRACT",
        "sp_op_count_MULTIPLY", "sp_op_count_DIVIDE",
        "sp_op_count_ADD", "sp_op_count_SUBTRACT",
        "cross_row_op_count", "cross_col_op_count",
        "active_active_count",  # AND count
        "mean_normal_dot", "std_normal_dot",
        "same_pos_mean_normal_dot",
        "mean_clearance", "std_clearance", "min_clearance", "max_clearance",
    ]}
    dh_metrics = {k: [] for k in metrics}

    for sym_a, sym_b, be, dh, _ in KNOWN_PAIRS:
        ea = kb.get_element(sym_a)
        eb = kb.get_element(sym_b)
        if ea is None or eb is None: continue
        m = scene.compute_pair_metrics(ea.vector24, eb.vector24)
        be_vals.append(be)
        for k in metrics:
            if k == "active_active_count":
                metrics[k].append(m["active_active_count"])
            else:
                metrics[k].append(m.get(k, 0))
        if dh is not None and dh != 0:
            dh_vals.append(dh)
            for k in dh_metrics:
                if k == "active_active_count":
                    dh_metrics[k].append(m["active_active_count"])
                else:
                    dh_metrics[k].append(m.get(k, 0))

    print(f"{'Metric':<35} {'r vs BE':>9} {'r vs dH':>9}")
    print("-" * 55)
    for k in metrics:
        r_be = 0
        r_dh = 0
        if statistics.pstdev(metrics[k]) > 0:
            r_be = statistics.correlation(metrics[k], be_vals)
        if len(dh_metrics[k]) > 1 and statistics.pstdev(dh_metrics[k]) > 0:
            r_dh = statistics.correlation(dh_metrics[k], dh_vals)
        if abs(r_be) >= 0.15 or abs(r_dh) >= 0.15:
            print(f"{k:<35} {r_be:>+9.4f} {r_dh:>+9.4f}")


def explore_normal_alignment_per_bit():
    """For each bit position, check if its normal alignment correlates with chemistry."""
    print()
    print("=" * 78)
    print("E6 FOLLOW-UP — Per-bit normal-vector alignment")
    print("=" * 78)
    print()
    print("Using sq4_z7 config with seed_offset_b=100 (best from earlier sweep)")
    print("For each of the 24 bit positions, compute the normal dot product")
    print("between grid A and grid B polygons at that position, then correlate")
    print("with bond energy across all 37 pairs.")
    print()

    scene = smg.StackedMOGScene(
        cell_w=4.0, cell_h=4.0, z_offset=7.0,
        seed_offset_a=0, seed_offset_b=100,
    )

    # For each pair, extract per-bit normal dots (for same-position pairs)
    per_bit_dots = [[] for _ in range(24)]  # 24 lists, one per bit position
    be_vals = []
    dh_vals = []
    dh_per_bit_dots = [[] for _ in range(24)]

    for sym_a, sym_b, be, dh, _ in KNOWN_PAIRS:
        ea = kb.get_element(sym_a)
        eb = kb.get_element(sym_b)
        if ea is None or eb is None: continue
        interactions = scene.compute_all_interactions(ea.vector24, eb.vector24)
        same_pos = [i for i in interactions if i["bit_a"] == i["bit_b"]]
        be_vals.append(be)
        for i, sp in enumerate(same_pos):
            per_bit_dots[sp["bit_a"]].append(sp["normal_dot"])
        if dh is not None and dh != 0:
            dh_vals.append(dh)
            for i, sp in enumerate(same_pos):
                dh_per_bit_dots[sp["bit_a"]].append(sp["normal_dot"])

    print(f"Per-bit normal dot vs Bond Energy:")
    print(f"{'Bit':>4} {'Row':<12} {'Col':>4} {'r vs BE':>9} {'r vs dH':>9} {'mean_dot':>10}")
    print("-" * 60)
    for bit in range(24):
        row = bit // 6
        col = bit % 6
        rname = ["Reality", "Info", "Activat", "Potentl"][row]
        r_be = 0
        r_dh = 0
        if len(per_bit_dots[bit]) == len(be_vals) and statistics.pstdev(per_bit_dots[bit]) > 0:
            r_be = statistics.correlation(per_bit_dots[bit], be_vals)
        if len(dh_per_bit_dots[bit]) == len(dh_vals) and statistics.pstdev(dh_per_bit_dots[bit]) > 0:
            r_dh = statistics.correlation(dh_per_bit_dots[bit], dh_vals)
        mean_dot = statistics.mean(per_bit_dots[bit]) if per_bit_dots[bit] else 0
        marker = " ***" if abs(r_be) >= 0.3 or abs(r_dh) >= 0.3 else ""
        print(f"{bit:>4} {rname:<12} {col:>4} {r_be:>+9.4f} {r_dh:>+9.4f} {mean_dot:>10.4f}{marker}")


def main():
    seed_results = explore_seed_offsets()
    explore_operator_counts()
    explore_normal_alignment_per_bit()

    # Save seed offset results
    out_path = OUT_DIR / "e6_seed_offset_sweep.json"
    with open(out_path, "w") as f:
        json.dump(seed_results, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
