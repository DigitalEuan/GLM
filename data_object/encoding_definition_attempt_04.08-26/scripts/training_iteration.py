"""
training_iteration.py — GLM Training Loop: Data Object Encoding Experiments

The GLM learns to encode chemical elements as 24-bit MOG Data Objects,
then tests whether the encoding predicts real chemistry (bond energy, ΔH).

Each iteration:
  1. Define an encoding spec (4 properties → 4 MOG rows, with scaling)
  2. Encode all elements as 24-bit vectors (Gray-coded, Golay-snapped)
  3. For each known chemistry pair, compute interaction metrics
  4. Score: how well do metrics predict BE and ΔH?
  5. Try variations: different properties, row orderings, scaling
  6. Record what works and what doesn't
  7. Learn: the GLM's understanding of what makes a good encoding

This is substrate-native learning — not gradient descent, but
systematic exploration of the encoding space with hard verification.
"""

from __future__ import annotations
import sys, json, math, statistics, itertools
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import kb_adapter as kb


# ═══════════════════════════════════════════════════════════════════════════════
# Encoding Specification
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EncodingSpec:
    """How to encode an element as a 24-bit MOG Data Object."""
    name: str
    prop_set: List[str]         # 4 property names (e.g., ['Z', 'Rad', 'EN', 'Valence_e'])
    row_assignment: List[int]   # which property goes to which MOG row (0-3)
    scaling: Dict[str, str]     # property -> scaling preset name
    leech_scheme: str = "A_basis"

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "prop_set": self.prop_set,
            "row_assignment": self.row_assignment,
            "scaling": self.scaling,
            "leech_scheme": self.leech_scheme,
        }


# Scaling presets: convert a float property value to a 6-bit integer [0, 63]
SCALING_PRESETS = {
    "identity": lambda f: int(abs(f)) & 0x3F,
    "mod64": lambda f: int(abs(f)) & 0x3F,
    "div4": lambda f: int(abs(f) // 4) & 0x3F,
    "div8": lambda f: int(abs(f) // 8) & 0x3F,
    "div16": lambda f: int(abs(f) // 16) & 0x3F,
    "div40": lambda f: int(abs(f) // 40) & 0x3F,
    "en_x10": lambda f: int(abs(f) * 10) & 0x3F,
    "en_x15": lambda f: int(abs(f) * 15) & 0x3F,
    "en_x20": lambda f: int(abs(f) * 20) & 0x3F,
    "valence_simple": lambda f: int(f) & 0x3F,
    "valence_redundant": lambda f: (int(f) & 0x07) << 3 | (int(f) & 0x07),
    "log2": lambda f: int(math.log2(max(abs(f), 1))) & 0x3F,
    "sqrt": lambda f: int(math.sqrt(abs(f))) & 0x3F,
    "bp_div100": lambda f: int(abs(f) // 100) & 0x3F,
    "rho_x10": lambda f: int(abs(f) * 10) & 0x3F,
}


def gray6(n: int) -> List[int]:
    """Convert a 6-bit integer to Gray code (6 bits)."""
    n &= 0x3F
    g = n ^ (n >> 1)
    return [(g >> (5 - i)) & 1 for i in range(6)]


def encode_element(symbol: str, spec: EncodingSpec) -> List[int]:
    """Encode an element as a 24-bit vector using the given spec."""
    elem = kb.get_element(symbol)
    if elem is None:
        return [0] * 24

    rows = [None] * 4
    for i, row_idx in enumerate(spec.row_assignment):
        prop = spec.prop_set[i]
        val = elem.properties.get(prop)
        if val is None:
            bits = [0] * 6
        else:
            scaling_name = spec.scaling.get(prop, "identity")
            scaler = SCALING_PRESETS.get(scaling_name, SCALING_PRESETS["identity"])
            try:
                f = float(val)
                n = scaler(f)
            except (ValueError, TypeError, ZeroDivisionError):
                n = 0
            bits = gray6(n)
        rows[row_idx] = bits

    # Flatten: row0 + row1 + row2 + row3 = 24 bits
    bits = []
    for row in rows:
        if row is None:
            bits.extend([0] * 6)
        else:
            bits.extend(row)
    return bits


# ═══════════════════════════════════════════════════════════════════════════════
# Golay Engine (simplified — snap to nearest codeword)
# ═══════════════════════════════════════════════════════════════════════════════

# We use the UBP unified engine for Golay operations if available,
# otherwise use a simplified version
try:
    sys.path.insert(0, str(SCRIPT_DIR.parent.parent / "GMHGL"))
    import ubp_unified_v5 as ubp
    GOLAY_ENGINE = ubp.GOLAY_ENGINE
    HAS_GOLAY = True
except Exception:
    HAS_GOLAY = False
    print("Warning: ubp_unified_v5 not available, using simplified Golay")


def golay_snap(vec: List[int]) -> List[int]:
    """Snap a 24-bit vector to the nearest Golay codeword."""
    if HAS_GOLAY:
        snapped, meta = GOLAY_ENGINE.snap_to_codeword(vec)
        return snapped
    else:
        # Simplified: just return the vector as-is
        return vec


# ═══════════════════════════════════════════════════════════════════════════════
# Interaction Metrics
# ═══════════════════════════════════════════════════════════════════════════════

def xor_vectors(a: List[int], b: List[int]) -> List[int]:
    return [a[i] ^ b[i] for i in range(24)]


def hamming_weight(vec: List[int]) -> int:
    return sum(vec)


def hamming_distance(a: List[int], b: List[int]) -> int:
    return sum(1 for i in range(24) if a[i] != b[i])


def compute_interaction_metrics(vec_a: List[int], vec_b: List[int]) -> Dict[str, float]:
    """Compute interaction metrics between two 24-bit vectors."""
    xor = xor_vectors(vec_a, vec_b)
    hw_xor = hamming_weight(xor)

    # Golay syndrome weight of XOR (error weight)
    if HAS_GOLAY:
        snapped, meta = GOLAY_ENGINE.snap_to_codeword(xor)
        sw_xor = sum(GOLAY_ENGINE.syndrome(xor))
    else:
        sw_xor = 0

    # Hexacode shadow agreement
    if HAS_GOLAY:
        hex_a, _ = GOLAY_ENGINE.mog_decompose(vec_a)
        hex_b, _ = GOLAY_ENGINE.mog_decompose(vec_b)
        hex_agreements = sum(1 for x, y in zip(hex_a, hex_b) if x == y)
    else:
        hex_agreements = 6  # assume full agreement if no engine

    # Simple overlap count (bits that are the same)
    overlap = sum(1 for i in range(24) if vec_a[i] == vec_b[i])

    return {
        "hw_xor": hw_xor,
        "sw_xor": sw_xor,
        "hex_agreements": hex_agreements,
        "overlap": overlap,
        "hamming_dist": hamming_distance(vec_a, vec_b),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Scoring
# ═══════════════════════════════════════════════════════════════════════════════

def pearson_r(x: List[float], y: List[float]) -> float:
    """Compute Pearson correlation coefficient."""
    n = len(x)
    if n < 3:
        return 0.0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
    if std_x == 0 or std_y == 0:
        return 0.0
    return cov / (std_x * std_y)


def score_encoding(spec: EncodingSpec, verbose: bool = False) -> Dict:
    """Score an encoding by how well its metrics predict chemistry."""
    pairs = kb.KNOWN_PAIRS

    # Encode all elements once
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
        return {"overall_score": 0.0, "n_pairs": len(records)}

    # Correlations with bond energy
    be_vals = [r["be"] for r in records]
    dh_records = [r for r in records if r["dh"] is not None]
    dh_vals = [r["dh"] for r in dh_records]

    # Try all metrics as predictors
    metric_names = ["hw_xor", "sw_xor", "hex_agreements", "overlap", "hamming_dist"]
    correlations = {}
    for metric in metric_names:
        vals = [r[metric] for r in records]
        r_be = pearson_r(vals, be_vals)
        correlations[f"r_{metric}_be"] = r_be

        if len(dh_records) >= 3:
            dh_metric_vals = [r[metric] for r in dh_records]
            r_dh = pearson_r(dh_metric_vals, dh_vals)
            correlations[f"r_{metric}_dh"] = r_dh

    # Best single-metric correlation
    best_be = max((abs(v), k, v) for k, v in correlations.items() if "_be" in k)
    best_dh = max((abs(v), k, v) for k, v in correlations.items() if "_dh" in k and "r_" in k)

    # Overall score: average of best |r| for BE and DH
    overall = (best_be[0] + best_dh[0]) / 2

    result = {
        "name": spec.name,
        "overall_score": overall,
        "best_r_be": best_be[2],
        "best_r_be_metric": best_be[1],
        "best_r_dh": best_dh[2],
        "best_r_dh_metric": best_dh[1],
        "n_pairs": len(records),
        "n_dh": len(dh_records),
        "correlations": correlations,
    }

    if verbose:
        print(f"  Encoding: {spec.name}")
        print(f"    Best r(BE): {best_be[2]:+.4f} via {best_be[1]}")
        if len(dh_records) >= 3:
            print(f"    Best r(ΔH): {best_dh[2]:+.4f} via {best_dh[1]}")
        print(f"    Overall score: {overall:.4f}")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Training Iterations
# ═══════════════════════════════════════════════════════════════════════════════

# Available properties from our KB
AVAILABLE_PROPS = ["Z", "Rad", "EN", "Valence_e", "BP", "MP", "Rho", "M"]

# Property-to-row permutations (24 orderings for 4 properties)
def all_row_permutations(props: List[str]) -> List[List[int]]:
    """All 4! = 24 orderings of 4 properties across 4 MOG rows."""
    return [list(p) for p in itertools.permutations(range(4))]


# Scaling variations to try
SCALING_VARIATIONS = {
    "Z": ["identity", "mod64", "log2", "sqrt"],
    "Rad": ["identity", "div4", "div8", "div16"],
    "EN": ["identity", "en_x10", "en_x15", "en_x20"],
    "Valence_e": ["valence_simple", "valence_redundant"],
    "BP": ["identity", "bp_div100", "div40"],
    "MP": ["identity", "bp_div100", "div40"],
    "Rho": ["identity", "rho_x10"],
    "M": ["identity", "mod64", "log2", "sqrt", "div40"],
}


def run_baseline():
    """Run the baseline encoding and score it."""
    print("=" * 70)
    print("ITERATION 0: BASELINE ENCODING")
    print("=" * 70)

    baseline = EncodingSpec(
        name="baseline_Z_Rad_EN_Val",
        prop_set=["Z", "Rad", "EN", "Valence_e"],
        row_assignment=[0, 1, 2, 3],
        scaling={
            "Z": "identity",
            "Rad": "div4",
            "EN": "en_x15",
            "Valence_e": "valence_redundant",
        },
    )

    result = score_encoding(baseline, verbose=True)
    return baseline, result


def run_property_search():
    """Search for the best 4-property combination."""
    print("\n" + "=" * 70)
    print("ITERATION 1: PROPERTY COMBINATION SEARCH")
    print("=" * 70)

    # Try all combinations of 4 properties from available
    best_score = 0.0
    best_spec = None
    best_result = None
    all_results = []

    props_to_try = [p for p in AVAILABLE_PROPS if kb.get_element("H").properties.get(p) is not None]
    print(f"  Available properties with data: {props_to_try}")

    combo_count = 0
    for combo in itertools.combinations(props_to_try, 4):
        combo_count += 1
        # Default scaling for each property
        scaling = {}
        for p in combo:
            presets = SCALING_VARIATIONS.get(p, ["identity"])
            scaling[p] = presets[0]  # use first preset as default

        spec = EncodingSpec(
            name=f"combo_{'_'.join(combo)}",
            prop_set=list(combo),
            row_assignment=[0, 1, 2, 3],
            scaling=scaling,
        )

        result = score_encoding(spec, verbose=False)
        all_results.append((spec, result))

        if result["overall_score"] > best_score:
            best_score = result["overall_score"]
            best_spec = spec
            best_result = result

    print(f"  Tested {combo_count} property combinations")
    print(f"  Best: {best_spec.name} with score {best_score:.4f}")
    if best_result:
        print(f"    Best r(BE): {best_result['best_r_be']:+.4f} via {best_result['best_r_be_metric']}")
        print(f"    Best r(ΔH): {best_result['best_r_dh']:+.4f} via {best_result['best_r_dh_metric']}")

    # Show top 5
    all_results.sort(key=lambda x: -x[1]["overall_score"])
    print(f"\n  Top 5 property combinations:")
    for spec, result in all_results[:5]:
        print(f"    {spec.name}: score={result['overall_score']:.4f} "
              f"r_BE={result['best_r_be']:+.4f} r_ΔH={result['best_r_dh']:+.4f}")

    return best_spec, best_result, all_results


def run_scaling_search(base_spec: EncodingSpec):
    """Given a property set, search for the best scaling for each property."""
    print("\n" + "=" * 70)
    print(f"ITERATION 2: SCALING SEARCH for {base_spec.name}")
    print("=" * 70)

    best_score = 0.0
    best_spec = None
    all_results = []

    # For each property, try all scaling options
    prop_scalings = []
    for p in base_spec.prop_set:
        options = SCALING_VARIATIONS.get(p, ["identity"])
        prop_scalings.append(options)

    # Try all combinations
    combo_count = 0
    for scales in itertools.product(*prop_scalings):
        combo_count += 1
        scaling = {p: s for p, s in zip(base_spec.prop_set, scales)}

        spec = EncodingSpec(
            name=f"scale_{'_'.join(scales)}",
            prop_set=base_spec.prop_set,
            row_assignment=base_spec.row_assignment,
            scaling=scaling,
        )

        result = score_encoding(spec, verbose=False)
        all_results.append((spec, result))

        if result["overall_score"] > best_score:
            best_score = result["overall_score"]
            best_spec = spec

    print(f"  Tested {combo_count} scaling combinations")
    all_results.sort(key=lambda x: -x[1]["overall_score"])
    print(f"  Best: {all_results[0][0].name} with score {all_results[0][1]['overall_score']:.4f}")
    print(f"\n  Top 5 scaling combinations:")
    for spec, result in all_results[:5]:
        scaling_str = ", ".join(f"{p}={spec.scaling[p]}" for p in spec.prop_set)
        print(f"    {scaling_str}: score={result['overall_score']:.4f}")

    return all_results[0][0], all_results[0][1], all_results


def run_row_permutation_search(base_spec: EncodingSpec):
    """Given property set and scaling, search for the best row ordering."""
    print("\n" + "=" * 70)
    print(f"ITERATION 3: ROW PERMUTATION SEARCH")
    print("=" * 70)

    best_score = 0.0
    best_spec = None
    all_results = []

    for perm in itertools.permutations(range(4)):
        perm_list = list(perm)
        spec = EncodingSpec(
            name=f"perm_{perm_list}",
            prop_set=base_spec.prop_set,
            row_assignment=perm_list,
            scaling=base_spec.scaling,
        )

        result = score_encoding(spec, verbose=False)
        all_results.append((spec, result))

        if result["overall_score"] > best_score:
            best_score = result["overall_score"]
            best_spec = spec

    print(f"  Tested 24 row permutations")
    all_results.sort(key=lambda x: -x[1]["overall_score"])
    print(f"  Best: {[base_spec.prop_set[i] for i in all_results[0][0].row_assignment]} "
          f"with score {all_results[0][1]['overall_score']:.4f}")
    print(f"\n  Top 5 row permutations:")
    for spec, result in all_results[:5]:
        order = [base_spec.prop_set[i] for i in spec.row_assignment]
        print(f"    {order}: score={result['overall_score']:.4f}")

    return all_results[0][0], all_results[0][1], all_results


# ═══════════════════════════════════════════════════════════════════════════════
# Main Training Loop
# ═══════════════════════════════════════════════════════════════════════════════

def run_training():
    """Run the full training iteration."""
    print("=" * 70)
    print("GLM TRAINING: DATA OBJECT ENCODING EXPERIMENTS")
    print("=" * 70)
    print()

    # Load elements
    elements = kb.get_all_elements()
    print(f"Loaded {len(elements)} elements")
    print(f"Known chemistry pairs: {len(kb.KNOWN_PAIRS)}")

    # Check which properties have data
    elem_H = kb.get_element("H")
    elem_C = kb.get_element("C")
    elem_Fe = kb.get_element("Fe")
    print(f"\nH properties: {dict(elem_H.properties)}")
    print(f"C properties: {dict(elem_C.properties)}")
    print(f"Fe properties: {dict(elem_Fe.properties)}")
    print()

    # Iteration 0: Baseline
    baseline_spec, baseline_result = run_baseline()

    # Iteration 1: Property combination search
    best_prop_spec, best_prop_result, prop_results = run_property_search()

    # Iteration 2: Scaling search (on best property combination)
    if best_prop_spec:
        best_scale_spec, best_scale_result, scale_results = run_scaling_search(best_prop_spec)
    else:
        best_scale_spec, best_scale_result = baseline_spec, baseline_result

    # Iteration 3: Row permutation search
    if best_scale_spec:
        best_perm_spec, best_perm_result, perm_results = run_row_permutation_search(best_scale_spec)
    else:
        best_perm_spec, best_perm_result = baseline_spec, baseline_result

    # Summary
    print("\n" + "=" * 70)
    print("TRAINING SUMMARY")
    print("=" * 70)
    print(f"  Baseline score:  {baseline_result['overall_score']:.4f}")
    print(f"  Best properties: {best_prop_result['overall_score']:.4f} ({best_prop_spec.name})")
    print(f"  Best scaling:    {best_scale_result['overall_score']:.4f} ({best_scale_spec.name})")
    print(f"  Best permutation:{best_perm_result['overall_score']:.4f} ({best_perm_spec.name})")

    # Save results
    output = {
        "baseline": {"spec": baseline_spec.to_dict(), "result": baseline_result},
        "best_properties": {"spec": best_prop_spec.to_dict() if best_prop_spec else None, "result": best_prop_result},
        "best_scaling": {"spec": best_scale_spec.to_dict() if best_scale_spec else None, "result": best_scale_result},
        "best_permutation": {"spec": best_perm_spec.to_dict() if best_perm_spec else None, "result": best_perm_result},
    }

    out_path = SCRIPT_DIR.parent / "data" / "training_run_001.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Results saved to {out_path}")

    return output


if __name__ == "__main__":
    run_training()
