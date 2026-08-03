"""
Test E4 — Encoding balance study.

The user noted: 'an element needs a fair amount of math to explain what the
Data Object is, but too much math is probably not the best either — a balance
is likely required.'

For each candidate encoding (subset of the 12 KB element properties), we:
  1. Encode each element's selected properties as 6-bit Gray rows -> 24-bit vector
     (one row per property, max 4 rows = 24 bits)
  2. For each pair of elements, compute interaction_metrics (XOR tax, scn_overlap,
     nat_sum, hex disagreements, etc.)
  3. Compute Pearson correlation vs known bond energy / ΔH
  4. Report which encoding gives the strongest signal

Property subsets to try (each picks 4 of 12 properties for the 4 MOG rows):
  A. Z, M, EN, Valence_e           (identity + bulk + chemistry)
  B. Z, M, EN, Oxidation           (chemistry focus)
  C. Z, EN, Ion, Valence_e         (electronic focus)
  D. Z, Rad, EN, Valence_e         (geometric focus)
  E. Z, M, BP, MP                  (thermal focus)
  F. Z, Rad, Rho, Crystal          (solid-state focus)
  G. Z, EN, Ion, Rad               (size + pull)
  H. Z, M, EN, Valence_e           (same as A — control)
  I. Z only (×4 = redundant rows)  (minimal)
  J. All 12 properties mixed across rows via hashing  (maximal)
"""

from __future__ import annotations

import sys
import json
import math
import statistics
import hashlib
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import ubp_unified_v5 as ubp
import spatial_arithmetic as sa
import ubp_kb_loader as kb
import golay_mog_investigation as inv
from e1_e2_e3_kb_sweep import interaction_metrics, KNOWN_PAIRS

OUT_DIR = Path("/home/z/my-project/download")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def gray6(n: int) -> List[int]:
    n &= 0x3F
    g = n ^ (n >> 1)
    return [(g >> (5 - i)) & 1 for i in range(6)]


def prop_to_6bit(prop_name: str, element) -> List[int]:
    """Encode a single property as a 6-bit Gray-coded row.

    Different properties have different scales, so we apply property-specific
    scaling to fit into [0, 63].
    """
    val = element.properties.get(prop_name)
    if val is None:
        return [0] * 6
    if isinstance(val, str):
        # Non-numeric (rare): hash to 6 bits
        h = int(hashlib.md5(val.encode()).hexdigest(), 16) & 0x3F
        return gray6(h)

    # val is a Fraction. Apply property-specific scaling.
    f = float(val)
    if prop_name == "Z":
        return gray6(int(f) & 0x3F)
    if prop_name == "M":
        # mass 1..250 -> scale mod 64
        return gray6(int(f) & 0x3F)
    if prop_name == "EN":
        # Pauling EN 0..4 -> ×15 -> [0, 60]
        return gray6(int(f * 15) & 0x3F)
    if prop_name == "Ion":
        # IE ~ 500..2400 -> /40 -> [12, 60]
        return gray6(int(f / 40) & 0x3F)
    if prop_name == "Valence_e":
        v = int(f) & 0x07
        return gray6((v << 3) | v)  # redundant encoding, fills 6 bits
    if prop_name == "Oxidation":
        # oxidation -4..+7 -> shift +4 -> [0, 11]
        return gray6(int(f + 8) & 0x3F)
    if prop_name == "BP":
        # boiling point 14..6203 K -> /100 -> [0, 62]
        return gray6(int(f / 100) & 0x3F)
    if prop_name == "MP":
        # melting point 0..3800 K -> /64 -> [0, 59]
        return gray6(int(f / 64) & 0x3F)
    if prop_name == "Rad":
        # radius 25..250 pm -> /4 -> [6, 62]
        return gray6(int(f / 4) & 0x3F)
    if prop_name == "Rho":
        # density 0..23 g/cm3 -> ×2.5 -> [0, 57]
        return gray6(int(f * 2.5) & 0x3F)
    if prop_name == "Crystal":
        # crystal system 1..7 -> direct
        return gray6(int(f) & 0x3F)
    if prop_name == "Phase_STP":
        # phase 1..3 -> direct
        return gray6(int(f) & 0x3F)
    # default: hash
    return gray6(int(abs(f)) & 0x3F)


def encode_with_props(symbol: str, prop_set: List[str]) -> List[int]:
    """Encode an element using a specific 4-property set -> 24-bit vector."""
    e = kb.get_element(symbol)
    if e is None:
        return [0] * 24
    bits = []
    for prop in prop_set:
        bits.extend(prop_to_6bit(prop, e))
    return bits


# Property subsets to test
ENCODINGS = {
    "A_chem_core":      ["Z", "M", "EN", "Valence_e"],
    "B_oxidation":      ["Z", "M", "EN", "Oxidation"],
    "C_electronic":     ["Z", "EN", "Ion", "Valence_e"],
    "D_geometric":      ["Z", "Rad", "EN", "Valence_e"],
    "E_thermal":        ["Z", "M", "BP", "MP"],
    "F_solid_state":    ["Z", "Rad", "Rho", "Crystal"],
    "G_size_pull":      ["Z", "EN", "Ion", "Rad"],
    "H_redox":          ["Z", "Oxidation", "Ion", "Rad"],
    "I_minimal_Z_only": ["Z", "Z", "Z", "Z"],
    "J_period_trend":   ["Z", "Rad", "Phase_STP", "Crystal"],
}


def run_e4_balance():
    print("=" * 80)
    print("E4 — ENCODING BALANCE STUDY")
    print("=" * 80)
    print(f"Testing {len(ENCODINGS)} different property encodings.")
    print(f"For each: encode all {len(KNOWN_PAIRS)} pair elements, compute metrics,")
    print(f"correlate with bond energy and ΔH.")
    print()

    # Compute and store vectors per encoding per element
    encoding_vectors: Dict[str, Dict[str, List[int]]] = {}
    for enc_name, prop_set in ENCODINGS.items():
        encoding_vectors[enc_name] = {}
        for sym_a, sym_b, _, _, _ in KNOWN_PAIRS:
            if sym_a not in encoding_vectors[enc_name]:
                encoding_vectors[enc_name][sym_a] = encode_with_props(sym_a, prop_set)
            if sym_b not in encoding_vectors[enc_name]:
                encoding_vectors[enc_name][sym_b] = encode_with_props(sym_b, prop_set)

    # For each encoding, sweep all pairs and compute correlation
    summary = []
    for enc_name, prop_set in ENCODINGS.items():
        print(f"\n── Encoding {enc_name}: props = {prop_set}")
        pair_results = []
        for sym_a, sym_b, be, dh, label in KNOWN_PAIRS:
            vec_a = encoding_vectors[enc_name][sym_a]
            vec_b = encoding_vectors[enc_name][sym_b]
            m = interaction_metrics(vec_a, vec_b)
            m["pair"] = (sym_a, sym_b)
            m["bond_energy_kJ"] = be
            m["delta_H_kJ"] = dh
            pair_results.append(m)

        # Compute correlations
        be_vals = [r["bond_energy_kJ"] for r in pair_results]
        dh_pairs = [r for r in pair_results if r["delta_H_kJ"] is not None and r["delta_H_kJ"] != 0]
        dh_vals = [r["delta_H_kJ"] for r in dh_pairs]

        enc_summary = {
            "encoding": enc_name,
            "prop_set": prop_set,
            "n_pairs": len(pair_results),
            "n_dh_pairs": len(dh_pairs),
        }

        # Bond energy correlations
        print(f"   Bond energy (n={len(pair_results)}):")
        for k in ["xor_hamming_weight", "hex_disagreements",
                  "scn_overlap_count", "nat_sum"]:
            vals = [r[k] for r in pair_results]
            if statistics.pstdev(vals) > 0:
                r_corr = statistics.correlation(vals, be_vals)
                print(f"     {k:<22}: r = {r_corr:+.4f}")
                enc_summary[f"be_r_{k}"] = r_corr

        # ΔH correlations
        if dh_pairs:
            print(f"   ΔH (n={len(dh_pairs)}):")
            for k in ["xor_hamming_weight", "hex_disagreements",
                      "scn_overlap_count", "nat_sum"]:
                vals = [r[k] for r in dh_pairs]
                if statistics.pstdev(vals) > 0:
                    r_corr = statistics.correlation(vals, dh_vals)
                    print(f"     {k:<22}: r = {r_corr:+.4f}")
                    enc_summary[f"dh_r_{k}"] = r_corr

        summary.append(enc_summary)

    # Final ranking
    print()
    print("=" * 80)
    print("ENCODING RANKING by absolute correlation strength")
    print("=" * 80)
    # For each metric, rank encodings
    metrics_to_rank = ["be_r_xor_hamming_weight", "be_r_hex_disagreements",
                       "be_r_scn_overlap_count", "be_r_nat_sum",
                       "dh_r_xor_hamming_weight", "dh_r_hex_disagreements",
                       "dh_r_scn_overlap_count", "dh_r_nat_sum"]

    for metric in metrics_to_rank:
        ranked = sorted(summary, key=lambda s: -abs(s.get(metric, 0)), reverse=False)
        # Filter out encodings without this metric
        ranked = [s for s in ranked if metric in s]
        ranked.sort(key=lambda s: -abs(s[metric]))
        print(f"\n  {metric}:")
        for s in ranked[:5]:
            print(f"    {s['encoding']:<20} props={s['prop_set']}  r = {s[metric]:+.4f}")

    # Save JSON
    out_path = OUT_DIR / "e4_balance_study.json"
    with open(out_path, "w") as f:
        json.dump({"summary": summary}, f, indent=2, default=str)
    print()
    print(f"Saved: {out_path}  ({out_path.stat().st_size:,} bytes)")
    return summary


if __name__ == "__main__":
    run_e4_balance()
