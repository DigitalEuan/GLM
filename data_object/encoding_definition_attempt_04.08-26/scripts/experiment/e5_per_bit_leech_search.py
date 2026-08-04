"""
Test E5 — Per-bit 24D Leech address wide search.

For each of the 4 Leech-assignment schemes (A_basis, B_classA, C_classC, D_classB):
  1. Encode each element's 24-bit KB vector into 24 Leech points (one per bit)
  2. Compute intra-object geometry (~12 metrics per element)
  3. Compute inter-object geometry for each pair (~12 metrics per pair)
  4. Compute Spatial Arithmetic integration (~6 metrics per element)
  5. Correlate ALL metrics with bond energy and ΔH across the 37-pair sweep

Total metrics searched: ~30 per scheme × 4 schemes = ~120 correlations.
Wide search for any signal above r = 0.3.
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
import per_bit_leech as pbl
from e1_e2_e3_kb_sweep import KNOWN_PAIRS

OUT_DIR = Path("/home/z/my-project/download")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run_e5_wide_search():
    print("=" * 80)
    print("E5 — PER-BIT 24D LEECH ADDRESS WIDE SEARCH")
    print("=" * 80)
    print(f"Testing 4 schemes × ~30 metrics × 37 pairs = ~120 correlations")
    print()

    schemes = ["A_basis", "B_classA", "C_classC", "D_classB"]

    # Pre-compute intra-object geometry for every element we'll need
    needed_elements = set()
    for sym_a, sym_b, _, _, _ in KNOWN_PAIRS:
        needed_elements.add(sym_a)
        needed_elements.add(sym_b)

    print(f"Pre-computing intra-object geometry for {len(needed_elements)} elements...")
    intra_cache: Dict[Tuple[str, str], Dict] = {}
    for sym in needed_elements:
        e = kb.get_element(sym)
        if e is None:
            continue
        for scheme in schemes:
            intra_cache[(sym, scheme)] = pbl.intra_object_geometry(e.vector24, scheme)
    print(f"  Cached {len(intra_cache)} intra-object geometries.")

    # Pre-compute spatial_arithmetic integration
    print(f"Pre-computing spatial_arithmetic integration for {len(needed_elements)} elements...")
    sa_cache: Dict[Tuple[str, str], Dict] = {}
    for sym in needed_elements:
        e = kb.get_element(sym)
        if e is None:
            continue
        for scheme in schemes:
            sa_cache[(sym, scheme)] = pbl.spatial_arithmetic_on_per_bit_leech(e.vector24, scheme)
    print(f"  Cached {len(sa_cache)} spatial_arithmetic integrations.")

    # For each scheme, sweep all pairs
    all_results = {}
    summary_rows = []

    for scheme in schemes:
        print(f"\n── Scheme {scheme} ──")
        pair_records = []
        for sym_a, sym_b, be, dh, label in KNOWN_PAIRS:
            ea = kb.get_element(sym_a)
            eb = kb.get_element(sym_b)
            if ea is None or eb is None:
                continue
            intra_a = intra_cache.get((sym_a, scheme))
            intra_b = intra_cache.get((sym_b, scheme))
            inter = pbl.inter_object_geometry(ea.vector24, eb.vector24, scheme)
            sa_a = sa_cache.get((sym_a, scheme))
            sa_b = sa_cache.get((sym_b, scheme))

            # Build a flat record with all metrics
            rec = {
                "pair": (sym_a, sym_b),
                "label": label,
                "bond_energy_kJ": be,
                "delta_H_kJ": dh,
                # Inter-object metrics
                "inter_sum_distance": inter["sum_distance"],
                "inter_mean_distance": inter["mean_distance"],
                "inter_min_distance": inter["min_distance"],
                "inter_max_distance": inter["max_distance"],
                "inter_std_distance": inter["std_distance"],
                "inter_alignment_count": inter["alignment_count"],
                "inter_alignment_score": inter["alignment_score"],
                "inter_sign_flip_count": inter["sign_flip_count"],
                "inter_centroid_distance": inter["centroid_distance"],
                "inter_active_overlap_count": inter["active_overlap_count"],
                "inter_active_overlap_mean_dist": inter["active_overlap_mean_dist"],
                "inter_total_diff_tax": inter["total_diff_tax"],
                "inter_mean_diff_tax": inter["mean_diff_tax"],
                # Intra-A metrics
                "intra_a_rms_spread": intra_a["rms_spread"],
                "intra_a_max_pairwise": intra_a["max_pairwise_dist"],
                "intra_a_mean_pairwise": intra_a["mean_pairwise_dist"],
                "intra_a_active_count": intra_a["active_count"],
                "intra_a_active_rms": intra_a["active_only_rms"],
                "intra_a_active_max_dist": intra_a["active_only_max_dist"],
                "intra_a_total_tax": intra_a["total_tax"],
                "intra_a_mean_tax": intra_a["mean_tax"],
                "intra_a_centroid_norm_sq": intra_a["centroid_norm_sq"],
                # Intra-B metrics
                "intra_b_rms_spread": intra_b["rms_spread"],
                "intra_b_max_pairwise": intra_b["max_pairwise_dist"],
                "intra_b_mean_pairwise": intra_b["mean_pairwise_dist"],
                "intra_b_active_count": intra_b["active_count"],
                "intra_b_active_rms": intra_b["active_only_rms"],
                "intra_b_active_max_dist": intra_b["active_only_max_dist"],
                "intra_b_total_tax": intra_b["total_tax"],
                "intra_b_mean_tax": intra_b["mean_tax"],
                "intra_b_centroid_norm_sq": intra_b["centroid_norm_sq"],
                # Combined intra metrics (differences and products)
                "tax_diff": abs(intra_a["total_tax"] - intra_b["total_tax"]),
                "tax_product": intra_a["total_tax"] * intra_b["total_tax"],
                "tax_sum": intra_a["total_tax"] + intra_b["total_tax"],
                "rms_diff": abs(intra_a["rms_spread"] - intra_b["rms_spread"]),
                "rms_product": intra_a["rms_spread"] * intra_b["rms_spread"],
                "active_count_diff": abs(intra_a["active_count"] - intra_b["active_count"]),
                "active_count_sum": intra_a["active_count"] + intra_b["active_count"],
                # Spatial arithmetic metrics
                "sa_a_scene_n_polys": sa_a["scene_stats"]["n_polygons"],
                "sa_a_scene_mean_3d_dist": sa_a["scene_stats"]["mean_3d_dist"],
                "sa_a_scene_max_3d_dist": sa_a["scene_stats"]["max_3d_dist"],
                "sa_b_scene_n_polys": sa_b["scene_stats"]["n_polygons"],
                "sa_b_scene_mean_3d_dist": sa_b["scene_stats"]["mean_3d_dist"],
                "sa_b_scene_max_3d_dist": sa_b["scene_stats"]["max_3d_dist"],
                "sa_diff_mean_3d_dist": abs(sa_a["scene_stats"]["mean_3d_dist"] -
                                             sa_b["scene_stats"]["mean_3d_dist"]),
                "sa_sum_mean_3d_dist": sa_a["scene_stats"]["mean_3d_dist"] +
                                        sa_b["scene_stats"]["mean_3d_dist"],
                "sa_bbox_vol_a": sa_a["bbox_3d"][0] * sa_a["bbox_3d"][1] * sa_a["bbox_3d"][2],
                "sa_bbox_vol_b": sa_b["bbox_3d"][0] * sa_b["bbox_3d"][1] * sa_b["bbox_3d"][2],
                "sa_bbox_vol_diff": abs(sa_a["bbox_3d"][0] * sa_a["bbox_3d"][1] * sa_a["bbox_3d"][2] -
                                         sa_b["bbox_3d"][0] * sa_b["bbox_3d"][1] * sa_b["bbox_3d"][2]),
            }
            pair_records.append(rec)

        all_results[scheme] = pair_records

        # Compute correlations for all metrics
        be_vals = [r["bond_energy_kJ"] for r in pair_records]
        dh_pairs = [r for r in pair_records if r["delta_H_kJ"] is not None and r["delta_H_kJ"] != 0]
        dh_vals = [r["delta_H_kJ"] for r in dh_pairs]

        # Determine which metrics to correlate
        metric_keys = [k for k in pair_records[0].keys()
                       if k not in ("pair", "label", "bond_energy_kJ", "delta_H_kJ")]

        print(f"\n  Bond energy correlations (n={len(pair_records)}):")
        for k in metric_keys:
            vals = [r[k] for r in pair_records]
            if isinstance(vals[0], (int, float)) and statistics.pstdev(vals) > 0:
                r_corr = statistics.correlation(vals, be_vals)
                if abs(r_corr) >= 0.30:
                    print(f"    {k:<40}: r = {r_corr:+.4f}  ***")
                    summary_rows.append({
                        "scheme": scheme, "metric": k, "target": "BE",
                        "r": r_corr, "n": len(pair_records)
                    })
                elif abs(r_corr) >= 0.20:
                    print(f"    {k:<40}: r = {r_corr:+.4f}")
                    summary_rows.append({
                        "scheme": scheme, "metric": k, "target": "BE",
                        "r": r_corr, "n": len(pair_records)
                    })

        print(f"\n  ΔH correlations (n={len(dh_pairs)}):")
        for k in metric_keys:
            vals = [r[k] for r in dh_pairs]
            if isinstance(vals[0], (int, float)) and statistics.pstdev(vals) > 0:
                r_corr = statistics.correlation(vals, dh_vals)
                if abs(r_corr) >= 0.30:
                    print(f"    {k:<40}: r = {r_corr:+.4f}  ***")
                    summary_rows.append({
                        "scheme": scheme, "metric": k, "target": "dH",
                        "r": r_corr, "n": len(dh_pairs)
                    })
                elif abs(r_corr) >= 0.20:
                    print(f"    {k:<40}: r = {r_corr:+.4f}")
                    summary_rows.append({
                        "scheme": scheme, "metric": k, "target": "dH",
                        "r": r_corr, "n": len(dh_pairs)
                    })

    # Final ranking
    print()
    print("=" * 80)
    print("TOP CORRELATIONS ACROSS ALL SCHEMES (|r| >= 0.30)")
    print("=" * 80)
    summary_rows.sort(key=lambda x: -abs(x["r"]))
    print(f"{'Scheme':<12} {'Metric':<42} {'Target':<8} {'r':>8} {'n':>4}")
    print("-" * 80)
    for row in summary_rows:
        if abs(row["r"]) >= 0.30:
            print(f"{row['scheme']:<12} {row['metric']:<42} {row['target']:<8} "
                  f"{row['r']:>+8.4f} {row['n']:>4}")

    # Save JSON
    out_path = OUT_DIR / "e5_per_bit_leech_wide_search.json"
    def ser(o):
        if isinstance(o, Fraction): return str(o)
        if isinstance(o, tuple): return list(o)
        if isinstance(o, set): return list(o)
        return str(o)
    with open(out_path, "w") as f:
        json.dump({
            "all_results": all_results,
            "summary_rows": summary_rows,
        }, f, indent=2, default=ser)
    print()
    print(f"Saved: {out_path}  ({out_path.stat().st_size:,} bytes)")
    return all_results, summary_rows


if __name__ == "__main__":
    t0 = time.time()
    run_e5_wide_search()
    print()
    print(f"Total time: {time.time() - t0:.2f}s")
