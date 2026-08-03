"""
training_iteration_v2.py — Deeper encoding exploration.

Building on v1 findings:
  - Best properties: EN, BP, MP, Rho (score 0.53)
  - Best r(ΔH) = 0.85 via sw_xor
  - r(BE) still weak (0.16)

Now exploring:
  1. 5-property encodings (using 5 rows of 6 bits = 30 bits, or packing 5 into 4 rows)
  2. Different metric combinations (multi-variate prediction)
  3. Nonlinear transforms (log, sqrt of properties)
  4. Cross-element interaction patterns
  5. Per-element encoding quality (which elements are well/poorly encoded?)
"""

from __future__ import annotations
import sys, json, math, statistics, itertools
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import kb_adapter as kb
from training_iteration import (
    EncodingSpec, encode_element, golay_snap, compute_interaction_metrics,
    pearson_r, score_encoding, SCALING_PRESETS, AVAILABLE_PROPS,
    SCALING_VARIATIONS, gray6, HAS_GOLAY,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Multi-variate prediction (combining multiple metrics)
# ═══════════════════════════════════════════════════════════════════════════════

def multi_metric_score(spec: EncodingSpec, verbose: bool = False) -> Dict:
    """Score using multi-metric linear combinations."""
    pairs = kb.KNOWN_PAIRS

    # Encode all elements
    elem_vectors = {}
    all_symbols = set()
    for sym_a, sym_b, be, dh, label in pairs:
        all_symbols.add(sym_a)
        all_symbols.add(sym_b)
    for sym in all_symbols:
        vec = encode_element(sym, spec)
        vec = golay_snap(vec)
        elem_vectors[sym] = vec

    # Compute metrics for all pairs
    records = []
    for sym_a, sym_b, be, dh, label in pairs:
        if sym_a not in elem_vectors or sym_b not in elem_vectors:
            continue
        va, vb = elem_vectors[sym_a], elem_vectors[sym_b]
        m = compute_interaction_metrics(va, vb)
        records.append({
            "pair": f"{sym_a}-{sym_b}",
            "be": be,
            "dh": dh if dh is not None and dh != 0 else None,
            **m,
        })

    if len(records) < 5:
        return {"overall_score": 0.0}

    # Try all single metrics
    metric_names = ["hw_xor", "sw_xor", "hex_agreements", "overlap", "hamming_dist"]
    be_vals = [r["be"] for r in records]
    dh_records = [r for r in records if r["dh"] is not None]
    dh_vals = [r["dh"] for r in dh_records]

    best_be_r = 0
    best_be_metric = ""
    best_dh_r = 0
    best_dh_metric = ""

    for metric in metric_names:
        vals = [r[metric] for r in records]
        r_be = pearson_r(vals, be_vals)
        if abs(r_be) > abs(best_be_r):
            best_be_r = r_be
            best_be_metric = metric

        if len(dh_records) >= 3:
            dh_metric_vals = [r[metric] for r in dh_records]
            r_dh = pearson_r(dh_metric_vals, dh_vals)
            if abs(r_dh) > abs(best_dh_r):
                best_dh_r = r_dh
                best_dh_metric = metric

    # Try 2-metric combinations for BE prediction
    best_2m_be_r = abs(best_be_r)
    best_2m_be_pair = (best_be_metric,)
    for m1, m2 in itertools.combinations(metric_names, 2):
        # Simple linear combination: try both m1+m2 and m1-m2
        for sign in [1, -1]:
            combined = [r[m1] + sign * r[m2] for r in records]
            r_be = pearson_r(combined, be_vals)
            if abs(r_be) > abs(best_2m_be_r):
                best_2m_be_r = abs(r_be)
                best_2m_be_pair = (f"{m1}{'+' if sign==1 else '-'}{m2}",)
                best_be_r = r_be
                best_be_metric = f"{m1}{'+' if sign==1 else '-'}{m2}"

    # Try 2-metric combinations for DH prediction
    best_2m_dh_r = abs(best_dh_r)
    for m1, m2 in itertools.combinations(metric_names, 2):
        for sign in [1, -1]:
            combined = [r[m1] + sign * r[m2] for r in dh_records]
            r_dh = pearson_r(combined, dh_vals)
            if abs(r_dh) > abs(best_2m_dh_r):
                best_2m_dh_r = abs(r_dh)
                best_dh_r = r_dh
                best_dh_metric = f"{m1}{'+' if sign==1 else '-'}{m2}"

    overall = (abs(best_be_r) + abs(best_dh_r)) / 2

    result = {
        "name": spec.name,
        "overall_score": overall,
        "best_r_be": best_be_r,
        "best_r_be_metric": best_be_metric,
        "best_r_dh": best_dh_r,
        "best_r_dh_metric": best_dh_metric,
        "n_pairs": len(records),
        "n_dh": len(dh_records),
    }

    if verbose:
        print(f"  {spec.name}")
        print(f"    Best r(BE): {best_be_r:+.4f} via {best_be_metric}")
        print(f"    Best r(ΔH): {best_dh_r:+.4f} via {best_dh_metric}")
        print(f"    Overall: {overall:.4f}")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Nonlinear property transforms
# ═══════════════════════════════════════════════════════════════════════════════

NONLINEAR_SCALINGS = {
    "log_z": lambda f: int(math.log2(max(abs(f), 1)) * 4) & 0x3F,
    "sqrt_z": lambda f: int(math.sqrt(abs(f)) * 3) & 0x3F,
    "z_squared_mod": lambda f: int(f * f) & 0x3F,
    "en_cubed": lambda f: int(abs(f) ** 3 * 100) & 0x3F,
    "bp_log": lambda f: int(math.log2(max(abs(f), 1)) * 4) & 0x3F,
    "mp_log": lambda f: int(math.log2(max(abs(f), 1)) * 4) & 0x3F,
    "rho_cbrt": lambda f: int(abs(f) ** (1/3) * 10) & 0x3F,
    "m_log": lambda f: int(math.log2(max(abs(f), 1)) * 4) & 0x3F,
    "rad_inv": lambda f: int(100 / max(abs(f), 1)) & 0x3F,
    "en_log": lambda f: int(math.log2(max(abs(f) * 10, 1)) * 4) & 0x3F,
}


def run_nonlinear_search():
    """Try nonlinear transforms on the best property set."""
    print("\n" + "=" * 70)
    print("ITERATION 4: NONLINEAR TRANSFORM SEARCH")
    print("=" * 70)

    # Best property set from v1: EN, BP, MP, Rho
    base_props = ["EN", "BP", "MP", "Rho"]

    # Add nonlinear scalings to the options
    extended_scalings = {}
    for p in base_props:
        options = SCALING_VARIATIONS.get(p, ["identity"])
        # Add nonlinear options
        nonlinear_key = p.lower()
        for nl_name, nl_fn in NONLINEAR_SCALINGS.items():
            if nonlinear_key in nl_name:
                options.append(nl_name)
        extended_scalings[p] = options

    best_score = 0
    best_spec = None
    all_results = []

    combo_count = 0
    for scales in itertools.product(*[extended_scalings[p] for p in base_props]):
        combo_count += 1
        scaling = {p: s for p, s in zip(base_props, scales)}

        # Register any nonlinear scalings
        for p, s in scaling.items():
            if s in NONLINEAR_SCALINGS and s not in SCALING_PRESETS:
                SCALING_PRESETS[s] = NONLINEAR_SCALINGS[s]

        spec = EncodingSpec(
            name=f"nl_{'_'.join(scales)}",
            prop_set=base_props,
            row_assignment=[0, 1, 2, 3],
            scaling=scaling,
        )

        result = multi_metric_score(spec, verbose=False)
        all_results.append((spec, result))

        if result["overall_score"] > best_score:
            best_score = result["overall_score"]
            best_spec = spec

    print(f"  Tested {combo_count} nonlinear combinations")
    all_results.sort(key=lambda x: -x[1]["overall_score"])
    print(f"\n  Top 5:")
    for spec, result in all_results[:5]:
        scaling_str = ", ".join(f"{p}={spec.scaling[p]}" for p in spec.prop_set)
        print(f"    {scaling_str}: score={result['overall_score']:.4f} "
              f"r_BE={result['best_r_be']:+.4f} r_ΔH={result['best_r_dh']:+.4f}")

    return all_results[0][0], all_results[0][1], all_results


# ═══════════════════════════════════════════════════════════════════════════════
# Per-element analysis: which elements are well/poorly encoded?
# ═══════════════════════════════════════════════════════════════════════════════

def per_element_analysis(spec: EncodingSpec, verbose: bool = True):
    """Analyze which elements are well-encoded by looking at pair residuals."""
    pairs = kb.KNOWN_PAIRS

    # Encode all elements
    elem_vectors = {}
    all_symbols = set()
    for sym_a, sym_b, be, dh, label in pairs:
        all_symbols.add(sym_a)
        all_symbols.add(sym_b)
    for sym in all_symbols:
        vec = encode_element(sym, spec)
        vec = golay_snap(vec)
        elem_vectors[sym] = vec

    # Compute metrics and fit a simple linear model for BE
    records = []
    for sym_a, sym_b, be, dh, label in pairs:
        if sym_a not in elem_vectors or sym_b not in elem_vectors:
            continue
        va, vb = elem_vectors[sym_a], elem_vectors[sym_b]
        m = compute_interaction_metrics(va, vb)
        records.append({
            "sym_a": sym_a, "sym_b": sym_b,
            "be": be,
            "dh": dh if dh is not None and dh != 0 else None,
            **m,
        })

    # Find which metric best predicts BE
    be_vals = [r["be"] for r in records]
    metric_names = ["hw_xor", "sw_xor", "hex_agreements", "overlap", "hamming_dist"]

    best_metric = None
    best_r = 0
    for metric in metric_names:
        vals = [r[metric] for r in records]
        r = pearson_r(vals, be_vals)
        if abs(r) > abs(best_r):
            best_r = r
            best_metric = metric

    if verbose:
        print(f"\n  Per-element analysis using best metric: {best_metric} (r={best_r:+.4f})")

        # Predict BE using the best metric
        metric_vals = [r[best_metric] for r in records]
        mean_m = sum(metric_vals) / len(metric_vals)
        mean_be = sum(be_vals) / len(be_vals)
        slope = sum((m - mean_m) * (b - mean_be) for m, b in zip(metric_vals, be_vals)) / \
                sum((m - mean_m) ** 2 for m in metric_vals) if sum((m - mean_m) ** 2 for m in metric_vals) > 0 else 0
        intercept = mean_be - slope * mean_m

        # Compute residuals
        residuals = []
        for r in records:
            predicted = intercept + slope * r[best_metric]
            residual = r["be"] - predicted
            residuals.append({**r, "predicted_be": predicted, "residual": residual})

        # Sort by absolute residual (worst predictions first)
        residuals.sort(key=lambda x: -abs(x["residual"]))

        print(f"  Linear model: BE = {intercept:.1f} + {slope:.3f} × {best_metric}")
        print(f"\n  Worst predictions (largest residuals):")
        for r in residuals[:10]:
            print(f"    {r['sym_a']}-{r['sym_b']}: actual={r['be']:.0f} "
                  f"predicted={r['predicted_be']:.0f} residual={r['residual']:+.0f}")

        # Elements that appear most in worst predictions
        from collections import Counter
        bad_elements = Counter()
        for r in residuals[:10]:
            bad_elements[r["sym_a"]] += 1
            bad_elements[r["sym_b"]] += 1
        print(f"\n  Elements with worst predictions:")
        for elem, count in bad_elements.most_common(5):
            e = kb.get_element(elem)
            props = e.properties if e else {}
            print(f"    {elem}: appears in {count} bad predictions, "
                  f"Z={props.get('Z', '?')} EN={props.get('EN', '?')} "
                  f"vector_hw={e.hamming_weight if e else '?'}")

    return records


# ═══════════════════════════════════════════════════════════════════════════════
# Golay structure analysis
# ═══════════════════════════════════════════════════════════════════════════════

def golay_structure_analysis(spec: EncodingSpec):
    """Analyze the Golay code structure of the encoded elements."""
    print("\n" + "=" * 70)
    print("GOLAY STRUCTURE ANALYSIS")
    print("=" * 70)

    elements = kb.get_all_elements()

    # Encode all elements
    encodings = {}
    for sym, elem in elements.items():
        vec = encode_element(sym, spec)
        snapped = golay_snap(vec)
        encodings[sym] = {
            "original": vec,
            "snapped": snapped,
            "hw_original": sum(vec),
            "hw_snapped": sum(snapped),
            "hamming_to_snapped": sum(1 for i in range(24) if vec[i] != snapped[i]),
        }

    # Distribution of Hamming weights
    hw_dist = {}
    for sym, enc in encodings.items():
        hw = enc["hw_snapped"]
        hw_dist[hw] = hw_dist.get(hw, 0) + 1

    print(f"\n  Hamming weight distribution (after Golay snap):")
    for hw in sorted(hw_dist.keys()):
        print(f"    HW={hw}: {hw_dist[hw]} elements")

    # Elements that changed most after Golay snap
    changes = [(sym, enc["hamming_to_snapped"]) for sym, enc in encodings.items()]
    changes.sort(key=lambda x: -x[1])
    print(f"\n  Elements that changed most after Golay snap:")
    for sym, dist in changes[:10]:
        if dist > 0:
            elem = elements[sym]
            print(f"    {sym}: {dist} bits changed, "
                  f"HW: {encodings[sym]['hw_original']}→{encodings[sym]['hw_snapped']}")

    # Unique vectors
    unique_snapped = set(tuple(enc["snapped"]) for enc in encodings.values())
    print(f"\n  Unique Golay codewords used: {len(unique_snapped)} / {len(elements)} elements")
    print(f"  (Out of 4096 possible Golay codewords)")

    return encodings


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def run_training_v2():
    """Run deeper training exploration."""
    print("=" * 70)
    print("GLM TRAINING v2: DEEPER ENCODING EXPLORATION")
    print("=" * 70)

    # Load elements
    elements = kb.get_all_elements()
    print(f"Loaded {len(elements)} elements, {len(kb.KNOWN_PAIRS)} known pairs")

    # Best encoding from v1
    v1_best = EncodingSpec(
        name="v1_best_EN_BP_MP_Rho",
        prop_set=["EN", "BP", "MP", "Rho"],
        row_assignment=[0, 1, 2, 3],
        scaling={
            "EN": "en_x10",
            "BP": "identity",
            "MP": "identity",
            "Rho": "identity",
        },
    )

    print(f"\n--- V1 baseline ---")
    v1_result = multi_metric_score(v1_best, verbose=True)

    # Iteration 4: Nonlinear transforms
    nl_spec, nl_result, nl_results = run_nonlinear_search()

    # Per-element analysis
    per_element_analysis(nl_spec if nl_result["overall_score"] > v1_result["overall_score"] else v1_best)

    # Golay structure analysis
    best_spec = nl_spec if nl_result["overall_score"] > v1_result["overall_score"] else v1_best
    golay_structure_analysis(best_spec)

    # Summary
    print("\n" + "=" * 70)
    print("TRAINING v2 SUMMARY")
    print("=" * 70)
    print(f"  V1 best score:    {v1_result['overall_score']:.4f}")
    print(f"  Nonlinear best:   {nl_result['overall_score']:.4f}")
    print(f"  Improvement:      {nl_result['overall_score'] - v1_result['overall_score']:+.4f}")

    # Save results
    output = {
        "v1_best": {"spec": v1_best.to_dict(), "result": v1_result},
        "nonlinear_best": {"spec": nl_spec.to_dict(), "result": nl_result},
    }
    out_path = SCRIPT_DIR.parent / "data" / "training_run_002.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Results saved to {out_path}")

    return output


if __name__ == "__main__":
    run_training_v2()
