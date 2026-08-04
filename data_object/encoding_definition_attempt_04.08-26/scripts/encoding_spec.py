"""
Encoding specification + scoring harness for the UBP Lingo Data Object.

This module defines:
  1. What an "encoding" IS (a complete specification)
  2. How to score any candidate encoding against reality (chemistry)
  3. The current best-known encoding (the baseline)

The GLM learning system can use this as a test harness:
  - Start with the baseline encoding
  - Try variations (different properties, row assignments, scalings)
  - Score each variation
  - Learn which encodings best predict chemistry

An Encoding spec has 4 components:
  - prop_set: list of 4 property names (which KB properties to use)
  - row_assignment: list of 4 row indices (which property goes in which MOG row)
  - scaling: dict of property -> scaling function name
  - leech_scheme: which per-bit Leech scheme to use ('A_basis', 'B_classA', 'C_classC', 'D_classB')
  - mog_grid_config: dict with cell_w, cell_h, z_offset, seed_offset_b

The scoring harness computes:
  - r vs Bond Energy (n=37)
  - r vs ΔH Formation (n=30)
  - Multiple R from composite metric
  - 5-fold cross-validated R (to detect overfitting)
"""

from __future__ import annotations

import sys
import json
import math
import statistics
import random
from fractions import Fraction
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Callable

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import ubp_unified_v5 as ubp
import spatial_arithmetic as sa
import ubp_kb_loader as kb
import stacked_mog_grids as smg
import per_bit_leech as pbl
from e1_e2_e3_kb_sweep import KNOWN_PAIRS, interaction_metrics


# ════════════════════════════════════════════════════════════════════════════════
# Encoding specification
# ════════════════════════════════════════════════════════════════════════════════

ROW_NAMES = ["Reality", "Info", "Activation", "Potential"]


@dataclass
class EncodingSpec:
    """Complete specification of a Data Object encoding.

    Attributes:
        name: human-readable name
        prop_set: list of 4 property names from KB (e.g., ['Z', 'Rad', 'EN', 'Valence_e'])
        row_assignment: list of 4 row indices (0-3), prop_set[i] goes to row_assignment[i]
                        e.g., [0, 1, 2, 3] means prop_set[0] -> row 0, prop_set[1] -> row 1, etc.
        scaling: dict of property_name -> scaling preset name
                presets: 'identity', 'mod64', 'div8', 'div40', 'div4',
                        'en_x15', 'valence_redundant', 'oxidation_shift',
                        'bp_div100', 'mp_div64', 'rho_x25'
        leech_scheme: 'A_basis', 'B_classA', 'C_classC', or 'D_classB'
        mog_cell_w: MOG grid cell width
        mog_cell_h: MOG grid cell height
        mog_z_offset: Z distance between stacked grids
        mog_seed_b: seed offset for grid B polygons (0 = same as A)
    """
    name: str
    prop_set: List[str]
    row_assignment: List[int]
    scaling: Dict[str, str]
    leech_scheme: str = "A_basis"
    mog_cell_w: float = 4.0
    mog_cell_h: float = 4.0
    mog_z_offset: float = 7.0
    mog_seed_b: int = 10

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "prop_set": self.prop_set,
            "row_assignment": self.row_assignment,
            "scaling": self.scaling,
            "leech_scheme": self.leech_scheme,
            "mog_cell_w": self.mog_cell_w,
            "mog_cell_h": self.mog_cell_h,
            "mog_z_offset": self.mog_z_offset,
            "mog_seed_b": self.mog_seed_b,
        }


# Scaling presets
SCALING_PRESETS: Dict[str, Callable] = {
    "identity": lambda f: int(abs(f)) & 0x3F,
    "mod64": lambda f: int(abs(f)) & 0x3F,
    "div8": lambda f: int(abs(f) // 8) & 0x3F,
    "div40": lambda f: int(abs(f) // 40) & 0x3F,
    "div4": lambda f: int(abs(f) // 4) & 0x3F,
    "en_x15": lambda f: int(abs(f) * 15) & 0x3F,
    "en_x10": lambda f: int(abs(f) * 10) & 0x3F,
    "en_x20": lambda f: int(abs(f) * 20) & 0x3F,
    "valence_redundant": lambda f: (int(f) & 0x07) << 3 | (int(f) & 0x07),
    "valence_simple": lambda f: int(f) & 0x3F,
    "oxidation_shift": lambda f: int(f + 8) & 0x3F,
    "bp_div100": lambda f: int(abs(f) // 100) & 0x3F,
    "mp_div64": lambda f: int(abs(f) // 64) & 0x3F,
    "rho_x25": lambda f: int(abs(f) * 25) & 0x3F,
    "rho_x10": lambda f: int(abs(f) * 10) & 0x3F,
}


def gray6(n: int) -> List[int]:
    n &= 0x3F
    g = n ^ (n >> 1)
    return [(g >> (5 - i)) & 1 for i in range(6)]


def encode_element(symbol: str, spec: EncodingSpec) -> List[int]:
    """Encode an element to a 24-bit vector using the given spec."""
    e = kb.get_element(symbol)
    if e is None:
        return [0] * 24

    # Build the 4 rows in the order specified by row_assignment
    # row_assignment[i] = which row prop_set[i] goes to
    # So row r contains the property at index j where row_assignment[j] == r
    rows = [None] * 4
    for i, row_idx in enumerate(spec.row_assignment):
        prop = spec.prop_set[i]
        val = e.properties.get(prop)
        if val is None:
            bits = [0] * 6
        else:
            scaling_name = spec.scaling.get(prop, "identity")
            scaler = SCALING_PRESETS.get(scaling_name, SCALING_PRESETS["identity"])
            try:
                f = float(val)
                n = scaler(f)
            except (ValueError, TypeError):
                n = 0
            bits = gray6(n)
        rows[row_idx] = bits

    # Flatten
    bits = []
    for row in rows:
        if row is None:
            bits.extend([0] * 6)
        else:
            bits.extend(row)
    return bits


# ════════════════════════════════════════════════════════════════════════════════
# Baseline encoding (best known from E4-E6)
# ════════════════════════════════════════════════════════════════════════════════

BASELINE_ENCODING = EncodingSpec(
    name="baseline_D_geometric_v1",
    prop_set=["Z", "Rad", "EN", "Valence_e"],
    row_assignment=[0, 1, 2, 3],  # Z->Reality, Rad->Info, EN->Activation, Valence->Potential
    scaling={
        "Z": "identity",
        "Rad": "div4",
        "EN": "en_x15",
        "Valence_e": "valence_redundant",
    },
    leech_scheme="A_basis",
    mog_cell_w=4.0,
    mog_cell_h=4.0,
    mog_z_offset=7.0,
    mog_seed_b=10,
)


# ════════════════════════════════════════════════════════════════════════════════
# Scoring harness
# ════════════════════════════════════════════════════════════════════════════════

def compute_pair_metrics_for_spec(spec: EncodingSpec,
                                   sym_a: str, sym_b: str) -> Dict:
    """Compute the three composite-metric signals for a pair under a given spec."""
    vec_a = encode_element(sym_a, spec)
    vec_b = encode_element(sym_b, spec)

    # Signal 1: scn_overlap (from E4 — interaction_metrics)
    m_inter = interaction_metrics(vec_a, vec_b)
    scn_overlap = m_inter["scn_overlap_count"]

    # Signal 2: sa_b_scene_max_3d_dist (from E5 — spatial_arithmetic_on_per_bit_leech)
    sa_b = pbl.spatial_arithmetic_on_per_bit_leech(vec_b, spec.leech_scheme)
    sa_b_max_3d = sa_b["scene_stats"]["max_3d_dist"]

    # Signal 3: aa_mean_normal_dot (from E6 — stacked MOG grids)
    scene = smg.StackedMOGScene(
        cell_w=spec.mog_cell_w, cell_h=spec.mog_cell_h,
        z_offset=spec.mog_z_offset,
        seed_offset_a=0, seed_offset_b=spec.mog_seed_b,
    )
    m_scene = scene.compute_pair_metrics(vec_a, vec_b)
    aa_normal_dot = m_scene["aa_mean_normal_dot"]

    return {
        "scn_overlap": scn_overlap,
        "sa_b_max_3d": sa_b_max_3d,
        "aa_normal_dot": aa_normal_dot,
        "vec_a": vec_a,
        "vec_b": vec_b,
    }


def score_encoding(spec: EncodingSpec,
                   pairs: Optional[List[Tuple[str, str, int, Optional[int], str]]] = None,
                   verbose: bool = False) -> Dict:
    """Score an encoding by how well it predicts bond energy and ΔH.

    Returns a dict with:
      - r_scn_overlap_be: r(scn_overlap, bond_energy)
      - r_sa_b_max_3d_dh: r(sa_b_max_3d, delta_H)
      - r_aa_normal_dot_dh: r(aa_normal_dot, delta_H)
      - multiple_r_be: composite multiple R for bond energy
      - multiple_r_dh: composite multiple R for delta H
      - n_be, n_dh: sample sizes
      - cv_multiple_r_be: 5-fold cross-validated multiple R for bond energy
      - cv_multiple_r_dh: 5-fold cross-validated multiple R for delta H
    """
    if pairs is None:
        pairs = KNOWN_PAIRS

    # Compute metrics for all pairs
    records = []
    for sym_a, sym_b, be, dh, label in pairs:
        ea = kb.get_element(sym_a)
        eb = kb.get_element(sym_b)
        if ea is None or eb is None:
            continue
        m = compute_pair_metrics_for_spec(spec, sym_a, sym_b)
        records.append({
            "pair": (sym_a, sym_b),
            "be": be,
            "dh": dh if dh is not None and dh != 0 else None,
            "scn_overlap": m["scn_overlap"],
            "sa_b_max_3d": m["sa_b_max_3d"],
            "aa_normal_dot": m["aa_normal_dot"],
        })

    # Single-metric correlations
    be_vals = [r["be"] for r in records]
    dh_records = [r for r in records if r["dh"] is not None]
    dh_vals = [r["dh"] for r in dh_records]

    r_scn_be = statistics.correlation(
        [r["scn_overlap"] for r in records], be_vals
    ) if statistics.pstdev([r["scn_overlap"] for r in records]) > 0 else 0

    r_sa_dh = statistics.correlation(
        [r["sa_b_max_3d"] for r in dh_records], dh_vals
    ) if statistics.pstdev([r["sa_b_max_3d"] for r in dh_records]) > 0 else 0

    r_aa_dh = statistics.correlation(
        [r["aa_normal_dot"] for r in dh_records], dh_vals
    ) if statistics.pstdev([r["aa_normal_dot"] for r in dh_records]) > 0 else 0

    # Multiple regression for bond energy
    X_be = [[1, r["scn_overlap"], r["sa_b_max_3d"], r["aa_normal_dot"]] for r in records]
    y_be = be_vals
    multiple_r_be, r_sq_be = _multiple_regression(X_be, y_be)

    # Multiple regression for delta H
    X_dh = [[1, r["scn_overlap"], r["sa_b_max_3d"], r["aa_normal_dot"]] for r in dh_records]
    y_dh = dh_vals
    multiple_r_dh, r_sq_dh = _multiple_regression(X_dh, y_dh)

    # 5-fold cross-validation
    cv_be = _cross_validate(records, target="be", k=5)
    cv_dh = _cross_validate(dh_records, target="dh", k=5)

    if verbose:
        print(f"  Scoring encoding: {spec.name}")
        print(f"    r(scn_overlap, BE) = {r_scn_be:+.4f}")
        print(f"    r(sa_b_max_3d, ΔH) = {r_sa_dh:+.4f}")
        print(f"    r(aa_normal_dot, ΔH) = {r_aa_dh:+.4f}")
        print(f"    Multiple R (BE) = {multiple_r_be:.4f}  (R² = {r_sq_be:.4f})")
        print(f"    Multiple R (ΔH) = {multiple_r_dh:.4f}  (R² = {r_sq_dh:.4f})")
        print(f"    5-fold CV Multiple R (BE) = {cv_be:.4f}")
        print(f"    5-fold CV Multiple R (ΔH) = {cv_dh:.4f}")

    return {
        "name": spec.name,
        "r_scn_overlap_be": r_scn_be,
        "r_sa_b_max_3d_dh": r_sa_dh,
        "r_aa_normal_dot_dh": r_aa_dh,
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


def _multiple_regression(X: List[List[float]], y: List[float]) -> Tuple[float, float]:
    """Compute multiple R and R² via least squares."""
    try:
        import numpy as np
        X_arr = np.array(X)
        y_arr = np.array(y)
        beta, _, _, _ = np.linalg.lstsq(X_arr, y_arr, rcond=None)
        y_pred = X_arr @ beta
        ss_res = np.sum((y_arr - y_pred) ** 2)
        ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
        r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        r_sq = max(0, r_sq)  # clamp
        return math.sqrt(r_sq), r_sq
    except Exception:
        return 0.0, 0.0


def _cross_validate(records: List[Dict], target: str, k: int = 5) -> float:
    """k-fold cross-validation. Returns mean multiple R across folds."""
    if len(records) < k * 2:
        return 0.0
    random.seed(42)
    shuffled = records.copy()
    random.shuffle(shuffled)
    fold_size = len(shuffled) // k
    folds = [shuffled[i*fold_size:(i+1)*fold_size] for i in range(k)]
    # Put remainder in last fold
    if len(shuffled) > k * fold_size:
        folds[-1].extend(shuffled[k*fold_size:])

    rs = []
    for i in range(k):
        test = folds[i]
        train = [r for j, f in enumerate(folds) if j != i for r in f]
        if len(train) < 4 or len(test) < 2:
            continue
        # Fit on train
        X_train = [[1, r["scn_overlap"], r["sa_b_max_3d"], r["aa_normal_dot"]] for r in train]
        y_train = [r[target] for r in train]
        try:
            import numpy as np
            X_arr = np.array(X_train)
            y_arr = np.array(y_train)
            beta, _, _, _ = np.linalg.lstsq(X_arr, y_arr, rcond=None)
            # Predict on test
            X_test = np.array([[1, r["scn_overlap"], r["sa_b_max_3d"], r["aa_normal_dot"]] for r in test])
            y_test = np.array([r[target] for r in test])
            y_pred = X_test @ beta
            ss_res = np.sum((y_test - y_pred) ** 2)
            ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
            r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0
            # For held-out, R² can be negative (worse than mean). Clamp at 0.
            r_sq = max(0, r_sq)
            rs.append(math.sqrt(r_sq))
        except Exception:
            continue
    return statistics.mean(rs) if rs else 0.0


# ════════════════════════════════════════════════════════════════════════════════
# Per-bit ablation study
# ════════════════════════════════════════════════════════════════════════════════

def per_bit_ablation(spec: EncodingSpec, verbose: bool = True) -> Dict:
    """For each of the 24 bit positions, zero out that bit in ALL elements
    and re-score the encoding. Bits whose removal causes the biggest score
    drop are the most important.

    Returns a dict mapping bit_index -> score_drop (positive = important).
    """
    if verbose:
        print(f"\n── Per-bit ablation for {spec.name} ──")
        print(f"   Zeroing each bit position across all elements, re-scoring.")

    # Baseline score
    baseline = score_encoding(spec, verbose=False)
    baseline_overall = baseline["overall_score"]

    if verbose:
        print(f"   Baseline overall score: {baseline_overall:.4f}")
        print(f"   Baseline Multiple R (BE): {baseline['multiple_r_be']:.4f}")
        print(f"   Baseline Multiple R (ΔH): {baseline['multiple_r_dh']:.4f}")
        print()

    # For each bit, create a modified spec that zeros out that bit
    # We do this by intercepting the encode_element function
    results = []
    for bit_idx in range(24):
        # Create a wrapper that zeros out the bit
        original_encode = encode_element

        def modified_encode(symbol, spec, _bit_idx=bit_idx):
            bits = original_encode(symbol, spec)
            bits[_bit_idx] = 0
            return bits

        # Monkey-patch
        globals()["encode_element"] = modified_encode

        # Score
        score = score_encoding(spec, verbose=False)

        # Restore
        globals()["encode_element"] = original_encode

        drop = baseline_overall - score["overall_score"]
        results.append({
            "bit": bit_idx,
            "row": bit_idx // 6,
            "col": bit_idx % 6,
            "row_name": ROW_NAMES[bit_idx // 6],
            "score_with_bit_zeroed": score["overall_score"],
            "score_drop": drop,
            "multiple_r_be_with_zero": score["multiple_r_be"],
            "multiple_r_dh_with_zero": score["multiple_r_dh"],
        })

        if verbose:
            marker = " ***" if drop > 0.02 else ""
            print(f"   bit {bit_idx:>2} (row={ROW_NAMES[bit_idx//6][:8]}, col={bit_idx%6}): "
                  f"score={score['overall_score']:.4f}  drop={drop:+.4f}{marker}")

    # Sort by score drop (most important first)
    results.sort(key=lambda x: -x["score_drop"])

    if verbose:
        print(f"\n   Top 5 most important bits:")
        for r in results[:5]:
            print(f"     bit {r['bit']:>2} ({r['row_name']}, col {r['col']}): drop = {r['score_drop']:+.4f}")
        print(f"\n   Bottom 5 (least important):")
        for r in results[-5:]:
            print(f"     bit {r['bit']:>2} ({r['row_name']}, col {r['col']}): drop = {r['score_drop']:+.4f}")

    return {
        "baseline_score": baseline_overall,
        "baseline_multiple_r_be": baseline["multiple_r_be"],
        "baseline_multiple_r_dh": baseline["multiple_r_dh"],
        "ablation_results": results,
    }


# ════════════════════════════════════════════════════════════════════════════════
# Property-to-row permutation study
# ════════════════════════════════════════════════════════════════════════════════

def row_permutation_study(spec: EncodingSpec, verbose: bool = True) -> Dict:
    """Try all 4! = 24 orderings of the 4 properties across the 4 MOG rows.

    Returns the best permutation and all scores.
    """
    from itertools import permutations

    if verbose:
        print(f"\n── Row permutation study for {spec.name} ──")
        print(f"   Trying all 24 orderings of {spec.prop_set}")

    results = []
    for perm in permutations(range(4)):
        perm_list = list(perm)
        modified_spec = EncodingSpec(
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
        score = score_encoding(modified_spec, verbose=False)
        results.append({
            "permutation": perm_list,
            "property_order": [spec.prop_set[i] for i in perm_list],
            "score": score,
        })

    # Sort by overall score
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
# Self-test
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 78)
    print("ENCODING SPECIFICATION HARNESS — SELF TEST")
    print("=" * 78)
    print()
    print(f"Baseline encoding: {BASELINE_ENCODING.name}")
    print(f"  prop_set: {BASELINE_ENCODING.prop_set}")
    print(f"  row_assignment: {BASELINE_ENCODING.row_assignment}")
    print(f"  scaling: {BASELINE_ENCODING.scaling}")
    print(f"  leech_scheme: {BASELINE_ENCODING.leech_scheme}")
    print(f"  mog config: cell={BASELINE_ENCODING.mog_cell_w}x{BASELINE_ENCODING.mog_cell_h}, "
          f"z={BASELINE_ENCODING.mog_z_offset}, seed_b={BASELINE_ENCODING.mog_seed_b}")
    print()

    # Score baseline
    print("── Scoring baseline encoding ──")
    score = score_encoding(BASELINE_ENCODING, verbose=True)
    print()
    print(f"Overall score: {score['overall_score']:.4f}")
    print(f"5-fold CV Multiple R (BE): {score['cv_multiple_r_be']:.4f}")
    print(f"5-fold CV Multiple R (ΔH): {score['cv_multiple_r_dh']:.4f}")
