"""
E7 — Encoding specification study with dual-encoding support.

Findings from initial harness test:
  - D_geometric re-encoded vectors are BEST for scn_overlap signal (r=+0.46 vs BE)
  - KB-hardened vectors are BEST for aa_normal_dot signal (r=-0.37 vs BE)
  - The two encodings expose DIFFERENT, COMPLEMENTARY signals

The optimal Data Object encoding is LAYERED:
  Layer 1: KB-hardened 24-bit vector (UBP v5.4.1's native encoding)
           → best for normal-vector alignment (E6 signal)
  Layer 2: D_geometric re-encoding (Z, Rad, EN, Valence)
           → best for scene overlap (E4 signal)

This script:
  1. Tests the dual-encoding composite metric
  2. Runs per-bit ablation on BOTH layers
  3. Runs property-to-row permutation on Layer 2
  4. Cross-validates the composite
  5. Produces the final encoding specification
"""

from __future__ import annotations

import sys
import json
import math
import statistics
import random
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from itertools import permutations

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import ubp_unified_v5 as ubp
import spatial_arithmetic as sa
import ubp_kb_loader as kb
import stacked_mog_grids as smg
import per_bit_leech as pbl
import encoding_spec as es
from e1_e2_e3_kb_sweep import KNOWN_PAIRS, interaction_metrics

OUT_DIR = Path("/home/z/my-project/download")
OUT_DIR.mkdir(parents=True, exist_ok=True)

import numpy as np

ROW_NAMES = ["Reality", "Info", "Activation", "Potential"]


# ════════════════════════════════════════════════════════════════════════════════
# Dual-encoding scoring
# ════════════════════════════════════════════════════════════════════════════════

def compute_dual_encoding_metrics(spec: es.EncodingSpec,
                                   sym_a: str, sym_b: str) -> Dict:
    """Compute metrics using BOTH KB-hardened and D_geometric encodings.

    Layer 1 (KB-hardened): aa_normal_dot (E6 signal)
    Layer 2 (D_geometric): scn_overlap (E4 signal)
    Layer 1 (KB-hardened): sa_b_max_3d (E5 signal)

    Returns all three signals.
    """
    ea = kb.get_element(sym_a)
    eb = kb.get_element(sym_b)
    if ea is None or eb is None:
        return {}

    # KB-hardened vectors (Layer 1)
    vec_a_kb = ea.vector24
    vec_b_kb = eb.vector24

    # D_geometric re-encoded vectors (Layer 2)
    vec_a_d = es.encode_element(sym_a, spec)
    vec_b_d = es.encode_element(sym_b, spec)

    # Signal 1: scn_overlap from D_geometric (Layer 2)
    m_d = interaction_metrics(vec_a_d, vec_b_d)
    scn_overlap_d = m_d["scn_overlap_count"]

    # Signal 2: sa_b_max_3d from KB-hardened (Layer 1)
    sa_b_kb = pbl.spatial_arithmetic_on_per_bit_leech(vec_b_kb, spec.leech_scheme)
    sa_b_max_3d_kb = sa_b_kb["scene_stats"]["max_3d_dist"]

    # Signal 3: aa_normal_dot from KB-hardened (Layer 1)
    scene = smg.StackedMOGScene(
        cell_w=spec.mog_cell_w, cell_h=spec.mog_cell_h,
        z_offset=spec.mog_z_offset,
        seed_offset_a=0, seed_offset_b=spec.mog_seed_b,
    )
    m_scene_kb = scene.compute_pair_metrics(vec_a_kb, vec_b_kb)
    aa_normal_dot_kb = m_scene_kb["aa_mean_normal_dot"]

    # Bonus: also compute scn_overlap from KB-hardened for comparison
    m_kb = interaction_metrics(vec_a_kb, vec_b_kb)
    scn_overlap_kb = m_kb["scn_overlap_count"]

    # And aa_normal_dot from D_geometric
    m_scene_d = scene.compute_pair_metrics(vec_a_d, vec_b_d)
    aa_normal_dot_d = m_scene_d["aa_mean_normal_dot"]

    return {
        "scn_overlap_d": scn_overlap_d,        # Layer 2 signal
        "sa_b_max_3d_kb": sa_b_max_3d_kb,      # Layer 1 signal
        "aa_normal_dot_kb": aa_normal_dot_kb,  # Layer 1 signal
        "scn_overlap_kb": scn_overlap_kb,      # diagnostic
        "aa_normal_dot_d": aa_normal_dot_d,    # diagnostic
    }


def score_dual_encoding(spec: es.EncodingSpec,
                         pairs: Optional[List] = None,
                         verbose: bool = False) -> Dict:
    """Score the dual-encoding composite metric."""
    if pairs is None:
        pairs = KNOWN_PAIRS

    records = []
    for sym_a, sym_b, be, dh, label in pairs:
        ea = kb.get_element(sym_a)
        eb = kb.get_element(sym_b)
        if ea is None or eb is None:
            continue
        m = compute_dual_encoding_metrics(spec, sym_a, sym_b)
        records.append({
            "pair": (sym_a, sym_b),
            "be": be,
            "dh": dh if dh is not None and dh != 0 else None,
            **m,
        })

    be_vals = [r["be"] for r in records]
    dh_records = [r for r in records if r["dh"] is not None]
    dh_vals = [r["dh"] for r in dh_records]

    # Single-metric correlations
    def safe_corr(xs, ys):
        if len(xs) < 2 or statistics.pstdev(xs) == 0:
            return 0
        return statistics.correlation(xs, ys)

    r_scn_d_be = safe_corr([r["scn_overlap_d"] for r in records], be_vals)
    r_scn_kb_be = safe_corr([r["scn_overlap_kb"] for r in records], be_vals)
    r_aa_kb_be = safe_corr([r["aa_normal_dot_kb"] for r in records], be_vals)
    r_aa_d_be = safe_corr([r["aa_normal_dot_d"] for r in records], be_vals)

    r_scn_d_dh = safe_corr([r["scn_overlap_d"] for r in dh_records], dh_vals)
    r_scn_kb_dh = safe_corr([r["scn_overlap_kb"] for r in dh_records], dh_vals)
    r_sa_kb_dh = safe_corr([r["sa_b_max_3d_kb"] for r in dh_records], dh_vals)
    r_aa_kb_dh = safe_corr([r["aa_normal_dot_kb"] for r in dh_records], dh_vals)
    r_aa_d_dh = safe_corr([r["aa_normal_dot_d"] for r in dh_records], dh_vals)

    # Composite: 3 features (scn_overlap_d, sa_b_max_3d_kb, aa_normal_dot_kb)
    X_be = [[1, r["scn_overlap_d"], r["sa_b_max_3d_kb"], r["aa_normal_dot_kb"]]
             for r in records]
    X_dh = [[1, r["scn_overlap_d"], r["sa_b_max_3d_kb"], r["aa_normal_dot_kb"]]
             for r in dh_records]

    multiple_r_be, r_sq_be = _multiple_regression(X_be, be_vals)
    multiple_r_dh, r_sq_dh = _multiple_regression(X_dh, dh_vals)

    # Cross-validation
    cv_be = _cross_validate(records, "be", k=5)
    cv_dh = _cross_validate(dh_records, "dh", k=5)

    if verbose:
        print(f"\n  Dual-encoding scoring: {spec.name}")
        print(f"  Single-metric correlations:")
        print(f"    scn_overlap (D_geometric) vs BE: r = {r_scn_d_be:+.4f}")
        print(f"    scn_overlap (KB-hardened) vs BE: r = {r_scn_kb_be:+.4f}")
        print(f"    aa_normal_dot (KB-hardened) vs BE: r = {r_aa_kb_be:+.4f}")
        print(f"    aa_normal_dot (D_geometric) vs BE: r = {r_aa_d_be:+.4f}")
        print(f"    scn_overlap (D_geometric) vs ΔH: r = {r_scn_d_dh:+.4f}")
        print(f"    sa_b_max_3d (KB-hardened) vs ΔH: r = {r_sa_kb_dh:+.4f}")
        print(f"    aa_normal_dot (KB-hardened) vs ΔH: r = {r_aa_kb_dh:+.4f}")
        print(f"  Composite:")
        print(f"    Multiple R (BE) = {multiple_r_be:.4f}  (R² = {r_sq_be:.4f})")
        print(f"    Multiple R (ΔH) = {multiple_r_dh:.4f}  (R² = {r_sq_dh:.4f})")
        print(f"    5-fold CV Multiple R (BE) = {cv_be:.4f}")
        print(f"    5-fold CV Multiple R (ΔH) = {cv_dh:.4f}")

    return {
        "name": spec.name,
        "r_scn_d_be": r_scn_d_be,
        "r_scn_kb_be": r_scn_kb_be,
        "r_aa_kb_be": r_aa_kb_be,
        "r_aa_d_be": r_aa_d_be,
        "r_scn_d_dh": r_scn_d_dh,
        "r_sa_kb_dh": r_sa_kb_dh,
        "r_aa_kb_dh": r_aa_kb_dh,
        "r_aa_d_dh": r_aa_d_dh,
        "multiple_r_be": multiple_r_be,
        "multiple_r_dh": multiple_r_dh,
        "r_squared_be": r_sq_be,
        "r_squared_dh": r_sq_dh,
        "cv_multiple_r_be": cv_be,
        "cv_multiple_r_dh": cv_dh,
        "n_be": len(records),
        "n_dh": len(dh_records),
        "overall_score": (multiple_r_be + multiple_r_dh + cv_be + cv_dh) / 4,
    }


def _multiple_regression(X, y):
    try:
        X_arr = np.array(X)
        y_arr = np.array(y)
        beta, _, _, _ = np.linalg.lstsq(X_arr, y_arr, rcond=None)
        y_pred = X_arr @ beta
        ss_res = np.sum((y_arr - y_pred) ** 2)
        ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
        r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        r_sq = max(0, r_sq)
        return math.sqrt(r_sq), r_sq
    except Exception:
        return 0.0, 0.0


def _cross_validate(records, target, k=5):
    if len(records) < k * 2:
        return 0.0
    random.seed(42)
    shuffled = records.copy()
    random.shuffle(shuffled)
    fold_size = len(shuffled) // k
    folds = [shuffled[i*fold_size:(i+1)*fold_size] for i in range(k)]
    if len(shuffled) > k * fold_size:
        folds[-1].extend(shuffled[k*fold_size:])

    rs = []
    for i in range(k):
        test = folds[i]
        train = [r for j, f in enumerate(folds) if j != i for r in f]
        if len(train) < 4 or len(test) < 2:
            continue
        X_train = [[1, r["scn_overlap_d"], r["sa_b_max_3d_kb"], r["aa_normal_dot_kb"]]
                    for r in train]
        y_train = [r[target] for r in train]
        try:
            X_arr = np.array(X_train)
            y_arr = np.array(y_train)
            beta, _, _, _ = np.linalg.lstsq(X_arr, y_arr, rcond=None)
            X_test = np.array([[1, r["scn_overlap_d"], r["sa_b_max_3d_kb"], r["aa_normal_dot_kb"]]
                                for r in test])
            y_test = np.array([r[target] for r in test])
            y_pred = X_test @ beta
            ss_res = np.sum((y_test - y_pred) ** 2)
            ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
            r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            r_sq = max(0, r_sq)
            rs.append(math.sqrt(r_sq))
        except Exception:
            continue
    return statistics.mean(rs) if rs else 0.0


# ════════════════════════════════════════════════════════════════════════════════
# Per-bit ablation (on KB-hardened Layer 1)
# ════════════════════════════════════════════════════════════════════════════════

def per_bit_ablation_kb(spec: es.EncodingSpec, verbose: bool = True) -> Dict:
    """For each of the 24 bit positions in the KB-hardened vector, flip that bit
    in ALL elements and re-score. Bits whose flip causes the biggest score
    change are the most important.

    Note: we FLIP (not zero) because KB-hardened bits have meaning we don't
    want to destroy by zeroing.
    """
    if verbose:
        print(f"\n── Per-bit ablation (KB-hardened Layer 1) ──")
        print(f"   Flipping each bit position across all elements, re-scoring.")

    # We need to temporarily modify the KB element vectors
    # Save originals
    original_vectors = {sym: e.vector24[:] for sym, e in kb.ELEMENTS.items()}

    # Baseline score
    baseline = score_dual_encoding(spec, verbose=False)
    baseline_overall = baseline["overall_score"]

    if verbose:
        print(f"   Baseline overall score: {baseline_overall:.4f}")
        print(f"   Baseline Multiple R (BE): {baseline['multiple_r_be']:.4f}")
        print(f"   Baseline Multiple R (ΔH): {baseline['multiple_r_dh']:.4f}")
        print()

    results = []
    for bit_idx in range(24):
        # Flip this bit in all elements
        for sym, e in kb.ELEMENTS.items():
            e.atlas["vector"][bit_idx] = 1 - e.atlas["vector"][bit_idx]

        # Score
        score = score_dual_encoding(spec, verbose=False)

        # Restore
        for sym, e in kb.ELEMENTS.items():
            e.atlas["vector"] = original_vectors[sym][:]

        change = score["overall_score"] - baseline_overall
        results.append({
            "bit": bit_idx,
            "row": bit_idx // 6,
            "col": bit_idx % 6,
            "row_name": ROW_NAMES[bit_idx // 6],
            "score_with_bit_flipped": score["overall_score"],
            "score_change": change,
            "multiple_r_be_with_flip": score["multiple_r_be"],
            "multiple_r_dh_with_flip": score["multiple_r_dh"],
            "abs_change": abs(change),
        })

        if verbose:
            marker = " ***" if abs(change) > 0.05 else ""
            print(f"   bit {bit_idx:>2} (row={ROW_NAMES[bit_idx//6][:8]}, col={bit_idx%6}): "
                  f"score={score['overall_score']:.4f}  change={change:+.4f}{marker}")

    # Sort by absolute change (most impactful first)
    results.sort(key=lambda x: -x["abs_change"])

    if verbose:
        print(f"\n   Top 5 most impactful bits (by |change|):")
        for r in results[:5]:
            print(f"     bit {r['bit']:>2} ({r['row_name']}, col {r['col']}): change = {r['score_change']:+.4f}")
        print(f"\n   Bottom 5 (least impactful):")
        for r in results[-5:]:
            print(f"     bit {r['bit']:>2} ({r['row_name']}, col {r['col']}): change = {r['score_change']:+.4f}")

    return {
        "baseline_score": baseline_overall,
        "baseline_multiple_r_be": baseline["multiple_r_be"],
        "baseline_multiple_r_dh": baseline["multiple_r_dh"],
        "ablation_results": results,
    }


# ════════════════════════════════════════════════════════════════════════════════
# Property-to-row permutation (on D_geometric Layer 2)
# ════════════════════════════════════════════════════════════════════════════════

def row_permutation_study(spec: es.EncodingSpec, verbose: bool = True) -> Dict:
    """Try all 4! = 24 orderings of the 4 properties across the 4 MOG rows."""
    if verbose:
        print(f"\n── Row permutation study (D_geometric Layer 2) ──")
        print(f"   Trying all 24 orderings of {spec.prop_set}")

    results = []
    for perm in permutations(range(4)):
        perm_list = list(perm)
        modified_spec = es.EncodingSpec(
            name=f"{spec.name}_perm{perm_list}",
            prop_set=spec.prop_set,
            row_assignment=perm_list,
            scaling=spec.scaling,
            leech_scheme=spec.leech_scheme,
            mog_cell_w=spec.mog_cell_w,
            mog_cell_h=spec.mog_cell_h,
            mog_z_offset=spec.mog_z_offset,
            mog_seed_b=spec.mog_seed_b,
        )
        score = score_dual_encoding(modified_spec, verbose=False)
        results.append({
            "permutation": perm_list,
            "property_order": [spec.prop_set[i] for i in perm_list],
            "score": score,
        })

    results.sort(key=lambda x: -x["score"]["overall_score"])

    if verbose:
        print(f"\n   Top 5 permutations:")
        for r in results[:5]:
            print(f"     {r['property_order']}: overall={r['score']['overall_score']:.4f}  "
                  f"R_BE={r['score']['multiple_r_be']:.4f}  R_dH={r['score']['multiple_r_dh']:.4f}")
        print(f"\n   Bottom 3 permutations:")
        for r in results[-3:]:
            print(f"     {r['property_order']}: overall={r['score']['overall_score']:.4f}  "
                  f"R_BE={r['score']['multiple_r_be']:.4f}  R_dH={r['score']['multiple_r_dh']:.4f}")

    return {
        "best_permutation": results[0],
        "all_results": results,
    }


# ════════════════════════════════════════════════════════════════════════════════
# Main E7 runner
# ════════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("E7 — ENCODING SPECIFICATION STUDY (DUAL-ENCODING)")
    print("=" * 80)

    spec = es.BASELINE_ENCODING

    # 1. Score baseline dual-encoding
    print("\n[1/4] Scoring baseline dual-encoding composite")
    baseline_score = score_dual_encoding(spec, verbose=True)

    # 2. Per-bit ablation on KB-hardened layer
    print("\n[2/4] Per-bit ablation (KB-hardened Layer 1)")
    ablation = per_bit_ablation_kb(spec, verbose=True)

    # 3. Row permutation study on D_geometric layer
    print("\n[3/4] Row permutation study (D_geometric Layer 2)")
    perm_study = row_permutation_study(spec, verbose=True)

    # 4. Test the best permutation
    print("\n[4/4] Testing best permutation from row study")
    best_perm = perm_study["best_permutation"]["permutation"]
    best_spec = es.EncodingSpec(
        name=f"{spec.name}_best_perm",
        prop_set=spec.prop_set,
        row_assignment=best_perm,
        scaling=spec.scaling,
        leech_scheme=spec.leech_scheme,
        mog_cell_w=spec.mog_cell_w,
        mog_cell_h=spec.mog_cell_h,
        mog_z_offset=spec.mog_z_offset,
        mog_seed_b=spec.mog_seed_b,
    )
    best_score = score_dual_encoding(best_spec, verbose=True)

    # Save everything
    out_path = OUT_DIR / "e7_encoding_spec_study.json"
    with open(out_path, "w") as f:
        json.dump({
            "baseline_spec": spec.to_dict(),
            "baseline_score": baseline_score,
            "ablation": ablation,
            "permutation_study": {
                "best_permutation": perm_study["best_permutation"],
                "all_results": perm_study["all_results"],
            },
            "best_permutation_spec": best_spec.to_dict(),
            "best_permutation_score": best_score,
        }, f, indent=2, default=str)
    print(f"\nSaved: {out_path}  ({out_path.stat().st_size:,} bytes)")

    return baseline_score, ablation, perm_study, best_score


if __name__ == "__main__":
    main()
