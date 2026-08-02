"""
Test E6 — Stacked MOG Grid Spatial Arithmetic interactions.

Sweep top configurations (from config search) across all 37 element pairs.
For each config × pair, compute:
  - Total operator-encoding bit pairs (MULTIPLY, DIVIDE, ADD, SUBTRACT counts)
  - Same-position operator count
  - Active-active operator count
  - Normal-vector alignment stats
  - Clearance distribution stats

Correlate ALL metrics with bond energy and ΔH.
"""

from __future__ import annotations

import sys
import json
import math
import statistics
import time
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import ubp_unified_v5 as ubp
import spatial_arithmetic as sa
import ubp_kb_loader as kb
import stacked_mog_grids as smg
from e1_e2_e3_kb_sweep import KNOWN_PAIRS

OUT_DIR = Path("/home/z/my-project/download")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# Top configurations from the config search (plus some hand-picked variants)
# These produce the most operator-encoding pairs for the test element (Carbon)
TOP_CONFIGS = [
    # (cell_w, cell_h, z_offset, label)
    (3.0, 3.0, 6.0, "sq3_z6_MULT_SUB"),    # 54 ops: 16 MULT + 38 SUB
    (3.0, 6.0, 6.0, "rect3x6_z6"),          # 44 ops: 16 MULT + 28 SUB
    (4.0, 4.0, 7.0, "sq4_z7_DIV_SUB"),     # 44 ops: 16 DIV + 28 SUB
    (6.0, 3.0, 6.0, "rect6x3_z6"),          # 44 ops
    (3.0, 3.0, 7.0, "sq3_z7_DIV_only"),    # 16 ops: 16 DIV
    (3.0, 3.0, 8.0, "sq3_z8_ADD_only"),    # 16 ops: 16 ADD
    (3.0, 3.0, 9.0, "sq3_z9_SUB_only"),    # 16 ops: 16 SUB
    (4.0, 4.0, 6.0, "sq4_z6_MULT_only"),   # 16 ops: 16 MULT
    (4.0, 4.0, 8.0, "sq4_z8_ADD_only"),    # 16 ops: 16 ADD
    (4.0, 4.0, 9.0, "sq4_z9_SUB_only"),    # 16 ops: 16 SUB
    (5.0, 5.0, 7.0, "sq5_z7_DIV_only"),    # 16 ops: 16 DIV
    (5.0, 5.0, 8.0, "sq5_z8_ADD_only"),    # 16 ops: 16 ADD
    # Variant: different seed offsets for grid B (gives different normals)
    (4.0, 4.0, 7.0, "sq4_z7_diff_seed"),   # with seed_offset_b = 100
]


def run_e6_search():
    print("=" * 80)
    print("E6 — STACKED MOG GRID SPATIAL ARITHMETIC INTERACTIONS")
    print("=" * 80)
    print(f"Testing {len(TOP_CONFIGS)} configurations × {len(KNOWN_PAIRS)} pairs")
    print()

    all_results = {}
    summary_rows = []

    for cfg_idx, (cell_w, cell_h, z_offset, label) in enumerate(TOP_CONFIGS):
        print(f"\n[{cfg_idx+1}/{len(TOP_CONFIGS)}] Config: {label} "
              f"(cell_w={cell_w}, cell_h={cell_h}, z={z_offset})")

        # Use different seed offset for the "diff_seed" variant
        seed_b = 100 if "diff_seed" in label else 0

        scene = smg.StackedMOGScene(
            cell_w=cell_w, cell_h=cell_h, z_offset=z_offset,
            seed_offset_a=0, seed_offset_b=seed_b,
        )

        pair_records = []
        for sym_a, sym_b, be, dh, desc in KNOWN_PAIRS:
            ea = kb.get_element(sym_a)
            eb = kb.get_element(sym_b)
            if ea is None or eb is None:
                continue
            m = scene.compute_pair_metrics(ea.vector24, eb.vector24)
            m["pair"] = (sym_a, sym_b)
            m["label"] = desc
            m["bond_energy_kJ"] = be
            m["delta_H_kJ"] = dh
            m["config_label"] = label
            pair_records.append(m)

        all_results[label] = pair_records

        # Compute correlations
        be_vals = [r["bond_energy_kJ"] for r in pair_records]
        dh_pairs = [r for r in pair_records if r["delta_H_kJ"] is not None and r["delta_H_kJ"] != 0]
        dh_vals = [r["delta_H_kJ"] for r in dh_pairs]

        # All numeric metrics to correlate
        metric_keys = [
            "n_operator_pairs",
            "same_position_op_count",
            "active_active_op_count",
            "active_active_op_count",
            "mean_clearance",
            "std_clearance",
            "min_clearance",
            "max_clearance",
            "mean_operator_residual",
            "min_operator_residual",
            "mean_normal_dot",
            "std_normal_dot",
            "mean_normal_angle",
            "std_normal_angle",
            "same_pos_mean_normal_dot",
            "same_pos_mean_normal_angle",
            "aa_mean_normal_dot",
            "aa_mean_normal_angle",
            "bounding_overlap_count",
            "cross_row_op_count",
            "cross_col_op_count",
        ]
        # Add operator-specific counts
        for op in ["MULTIPLY", "DIVIDE", "ADD", "SUBTRACT"]:
            metric_keys.append(f"op_count_{op}")
            metric_keys.append(f"aa_op_count_{op}")
            metric_keys.append(f"sp_op_count_{op}")

        # Extract operator counts as top-level metrics
        for r in pair_records:
            for op in ["MULTIPLY", "DIVIDE", "ADD", "SUBTRACT"]:
                r[f"op_count_{op}"] = r["operator_counts"][op]
                r[f"aa_op_count_{op}"] = r["active_active_op_breakdown"][op]
                r[f"sp_op_count_{op}"] = r["same_position_op_breakdown"][op]

        print(f"  Bond energy correlations (n={len(pair_records)}):")
        for k in metric_keys:
            vals = [r.get(k, 0) for r in pair_records]
            if isinstance(vals[0], (int, float)) and statistics.pstdev(vals) > 0:
                r_corr = statistics.correlation(vals, be_vals)
                if abs(r_corr) >= 0.30:
                    print(f"    {k:<40}: r = {r_corr:+.4f}  ***")
                    summary_rows.append({
                        "config": label, "metric": k, "target": "BE",
                        "r": r_corr, "n": len(pair_records)
                    })
                elif abs(r_corr) >= 0.20:
                    print(f"    {k:<40}: r = {r_corr:+.4f}")
                    summary_rows.append({
                        "config": label, "metric": k, "target": "BE",
                        "r": r_corr, "n": len(pair_records)
                    })

        print(f"  ΔH correlations (n={len(dh_pairs)}):")
        for k in metric_keys:
            vals = [r.get(k, 0) for r in dh_pairs]
            if isinstance(vals[0], (int, float)) and statistics.pstdev(vals) > 0:
                r_corr = statistics.correlation(vals, dh_vals)
                if abs(r_corr) >= 0.30:
                    print(f"    {k:<40}: r = {r_corr:+.4f}  ***")
                    summary_rows.append({
                        "config": label, "metric": k, "target": "dH",
                        "r": r_corr, "n": len(dh_pairs)
                    })
                elif abs(r_corr) >= 0.20:
                    print(f"    {k:<40}: r = {r_corr:+.4f}")
                    summary_rows.append({
                        "config": label, "metric": k, "target": "dH",
                        "r": r_corr, "n": len(dh_pairs)
                    })

    # Final ranking
    print()
    print("=" * 80)
    print("TOP CORRELATIONS ACROSS ALL CONFIGURATIONS (|r| >= 0.30)")
    print("=" * 80)
    summary_rows.sort(key=lambda x: -abs(x["r"]))
    print(f"{'Config':<25} {'Metric':<42} {'Target':<8} {'r':>8} {'n':>4}")
    print("-" * 90)
    for row in summary_rows:
        if abs(row["r"]) >= 0.30:
            print(f"{row['config']:<25} {row['metric']:<42} {row['target']:<8} "
                  f"{row['r']:>+8.4f} {row['n']:>4}")

    # Save JSON
    out_path = OUT_DIR / "e6_stacked_mog_search.json"
    def ser(o):
        if isinstance(o, Fraction): return str(o)
        if isinstance(o, tuple): return list(o)
        if isinstance(o, set): return list(o)
        return str(o)
    # Strip the large interactions_sample before saving
    for label, records in all_results.items():
        for r in records:
            r.pop("interactions_sample", None)
    with open(out_path, "w") as f:
        json.dump({
            "all_results": all_results,
            "summary_rows": summary_rows,
            "configs": [c[:3] for c in TOP_CONFIGS],
        }, f, indent=2, default=ser)
    print()
    print(f"Saved: {out_path}  ({out_path.stat().st_size:,} bytes)")
    return all_results, summary_rows


if __name__ == "__main__":
    t0 = time.time()
    run_e6_search()
    print()
    print(f"Total time: {time.time() - t0:.2f}s")
