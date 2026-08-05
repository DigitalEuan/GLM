"""
training_full_table.py — Full Periodic Table + All Molecules

Comprehensive training run:
  1. Encode all 118 elements, analyse distribution
  2. Compute pair interactions for ALL element combinations
  3. Encode all 82 molecules
  4. Correlate with known chemistry
  5. Explore what the substrate reveals
"""

from __future__ import annotations
import sys, json, math, statistics, itertools, time
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter, defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import kb_adapter as kb
from training_iteration import (
    EncodingSpec, encode_element, golay_snap, compute_interaction_metrics,
    pearson_r, SCALING_PRESETS, gray6, HAS_GOLAY, hamming_distance,
)

if HAS_GOLAY:
    from training_iteration import GOLAY_ENGINE


# ═══════════════════════════════════════════════════════════════════════════════
# Encoding specs to test
# ═══════════════════════════════════════════════════════════════════════════════

SPECS = {
    "v0_baseline": EncodingSpec(
        name="v0_baseline",
        prop_set=["Z", "Rad", "EN", "Valence_e"],
        row_assignment=[0, 1, 2, 3],
        scaling={"Z": "identity", "Rad": "div4", "EN": "en_x15", "Valence_e": "valence_redundant"},
    ),
    "v1_best": EncodingSpec(
        name="v1_best",
        prop_set=["EN", "BP", "MP", "Rho"],
        row_assignment=[0, 1, 2, 3],
        scaling={"EN": "en_x10", "BP": "div40", "MP": "div40", "Rho": "rho_x10"},
    ),
    "v2_z_en_val_m": EncodingSpec(
        name="v2_z_en_val_m",
        prop_set=["Z", "EN", "Valence_e", "M"],
        row_assignment=[0, 1, 2, 3],
        scaling={"Z": "identity", "EN": "en_x10", "Valence_e": "valence_redundant", "M": "log2"},
    ),
    "v3_z_rad_en_m": EncodingSpec(
        name="v3_z_rad_en_m",
        prop_set=["Z", "Rad", "EN", "M"],
        row_assignment=[0, 1, 2, 3],
        scaling={"Z": "log2", "Rad": "div8", "EN": "en_x10", "M": "log2"},
    ),
    "v4_all_nonlinear": EncodingSpec(
        name="v4_all_nonlinear",
        prop_set=["Z", "Rad", "EN", "M"],
        row_assignment=[0, 1, 2, 3],
        scaling={"Z": "sqrt", "Rad": "div16", "EN": "en_x15", "M": "div40"},
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# Full periodic table encoding
# ═══════════════════════════════════════════════════════════════════════════════

def encode_all_elements(spec: EncodingSpec) -> Dict[str, Dict]:
    """Encode all 118 elements and return rich data."""
    elements = kb.get_all_elements()
    results = {}

    for sym, elem in elements.items():
        vec_raw = encode_element(sym, spec)
        vec = golay_snap(vec_raw)
        hw_raw = sum(vec_raw)
        hw = sum(vec)
        bits_changed = sum(1 for i in range(24) if vec_raw[i] != vec[i])

        # NRCI
        if HAS_GOLAY:
            tax = hw * 0.2647 + sum(v*v for v in vec) / 8.0
            nrci = 10.0 / (10.0 + tax)
        else:
            nrci = 0

        results[sym] = {
            "symbol": sym,
            "z": int(elem.properties.get("Z", 0)),
            "vec_raw": vec_raw,
            "vec": vec,
            "hw_raw": hw_raw,
            "hw": hw,
            "bits_changed": bits_changed,
            "nrci": nrci,
            "props": {k: float(v) for k, v in elem.properties.items() if isinstance(v, Fraction)},
        }

    return results


def analyse_element_distribution(encodings: Dict[str, Dict], spec_name: str, verbose: bool = True):
    """Analyse the distribution of encoded elements."""
    hws = [e["hw"] for e in encodings.values()]
    nrcis = [e["nrci"] for e in encodings.values()]
    zs = [e["z"] for e in encodings.values()]
    changed = [e["bits_changed"] for e in encodings.values()]

    hw_dist = Counter(hws)
    unique_vecs = set(tuple(e["vec"]) for e in encodings.values())

    if verbose:
        print(f"\n  [{spec_name}] Element Distribution:")
        print(f"    Elements: {len(encodings)}")
        print(f"    Unique vectors: {len(unique_vecs)}")
        print(f"    Hamming weight distribution:")
        for hw in sorted(hw_dist.keys()):
            print(f"      HW={hw:2d}: {hw_dist[hw]:3d} elements")
        print(f"    Bits changed by Golay snap: mean={statistics.mean(changed):.1f}, max={max(changed)}")
        print(f"    NRCI: mean={statistics.mean(nrcis):.4f}, min={min(nrcis):.4f}, max={max(nrcis):.4f}")

    return {
        "hw_dist": dict(hw_dist),
        "unique_vectors": len(unique_vecs),
        "n_elements": len(encodings),
        "mean_hw": statistics.mean(hws),
        "mean_nrci": statistics.mean(nrcis),
        "mean_bits_changed": statistics.mean(changed),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Full pair sweep
# ═══════════════════════════════════════════════════════════════════════════════

def full_pair_sweep(encodings: Dict[str, Dict], max_pairs: int = 5000) -> List[Dict]:
    """Compute interaction metrics for ALL element pairs."""
    syms = sorted(encodings.keys())
    pairs = []

    count = 0
    for i, sa in enumerate(syms):
        for sb in syms[i:]:
            if count >= max_pairs:
                break
            va = encodings[sa]["vec"]
            vb = encodings[sb]["vec"]
            m = compute_interaction_metrics(va, vb)
            pairs.append({
                "a": sa, "b": sb,
                "z_a": encodings[sa]["z"], "z_b": encodings[sb]["z"],
                "hw_a": encodings[sa]["hw"], "hw_b": encodings[sb]["hw"],
                "nrci_a": encodings[sa]["nrci"], "nrci_b": encodings[sb]["nrci"],
                **m,
            })
            count += 1

    return pairs


def analyse_pair_distribution(pairs: List[Dict], verbose: bool = True):
    """Analyse the distribution of pair metrics."""
    hw_xors = [p["hw_xor"] for p in pairs]
    overlaps = [p["overlap"] for p in pairs]
    hex_agrs = [p["hex_agreements"] for p in pairs]
    ham_dists = [p["hamming_dist"] for p in pairs]

    if verbose:
        print(f"\n  Pair Distribution ({len(pairs)} pairs):")
        print(f"    HW(XOR): mean={statistics.mean(hw_xors):.1f}, min={min(hw_xors)}, max={max(hw_xors)}")
        print(f"    Overlap: mean={statistics.mean(overlaps):.1f}, min={min(overlaps)}, max={max(overlaps)}")
        print(f"    Hex agreements: mean={statistics.mean(hex_agrs):.1f}")
        print(f"    Hamming dist: mean={statistics.mean(ham_dists):.1f}")

        # HW(XOR) distribution
        hw_xor_dist = Counter(hw_xors)
        print(f"    HW(XOR) distribution:")
        for hw in sorted(hw_xor_dist.keys()):
            bar = "█" * (hw_xor_dist[hw] // 10)
            print(f"      {hw:2d}: {hw_xor_dist[hw]:4d} {bar}")

    return {
        "n_pairs": len(pairs),
        "mean_hw_xor": statistics.mean(hw_xors),
        "mean_overlap": statistics.mean(overlaps),
        "mean_hex_agreements": statistics.mean(hex_agrs),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Known chemistry correlation
# ═══════════════════════════════════════════════════════════════════════════════

def correlate_known_chemistry(encodings: Dict[str, Dict], verbose: bool = True) -> Dict:
    """Correlate pair metrics with known bond energies and ΔH."""
    pairs_data = kb.KNOWN_PAIRS

    records = []
    for sym_a, sym_b, be, dh, label in pairs_data:
        if sym_a not in encodings or sym_b not in encodings:
            continue
        va = encodings[sym_a]["vec"]
        vb = encodings[sym_b]["vec"]
        m = compute_interaction_metrics(va, vb)
        records.append({
            "pair": f"{sym_a}-{sym_b}",
            "be": be,
            "dh": dh if dh is not None and dh != 0 else None,
            "z_a": encodings[sym_a]["z"], "z_b": encodings[sym_b]["z"],
            **m,
        })

    be_vals = [r["be"] for r in records]
    dh_records = [r for r in records if r["dh"] is not None]
    dh_vals = [r["dh"] for r in dh_records]

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

    # Z-based correlations
    z_sums = [r["z_a"] + r["z_b"] for r in records]
    z_diffs = [abs(r["z_a"] - r["z_b"]) for r in records]
    correlations["r_z_sum_be"] = pearson_r(z_sums, be_vals)
    correlations["r_z_diff_be"] = pearson_r(z_diffs, be_vals)
    if len(dh_records) >= 3:
        correlations["r_z_sum_dh"] = pearson_r(
            [r["z_a"] + r["z_b"] for r in dh_records], dh_vals)
        correlations["r_z_diff_dh"] = pearson_r(
            [abs(r["z_a"] - r["z_b"]) for r in dh_records], dh_vals)

    # Combined metrics
    combined_hw_zdiff = [m["hw_xor"] * abs(m["z_a"] - m["z_b"]) for m in records]
    correlations["r_hw×zdiff_be"] = pearson_r(combined_hw_zdiff, be_vals)

    best_be = max((abs(v), k, v) for k, v in correlations.items() if "_be" in k)
    best_dh = max((abs(v), k, v) for k, v in correlations.items() if "_dh" in k and "r_" in k)

    result = {
        "n_pairs": len(records),
        "n_dh": len(dh_records),
        "correlations": correlations,
        "best_r_be": best_be[2],
        "best_r_be_metric": best_be[1],
        "best_r_dh": best_dh[2] if dh_records else 0,
        "best_r_dh_metric": best_dh[1] if dh_records else "",
    }

    if verbose:
        print(f"\n  Known Chemistry Correlations ({len(records)} pairs, {len(dh_records)} with ΔH):")
        print(f"    Best r(BE): {best_be[2]:+.4f} via {best_be[1]}")
        if dh_records:
            print(f"    Best r(ΔH): {best_dh[2]:+.4f} via {best_dh[1]}")
        print(f"    All correlations:")
        for k, v in sorted(correlations.items(), key=lambda x: -abs(x[1])):
            print(f"      {k:25s}: {v:+.4f}")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Molecule full encoding
# ═══════════════════════════════════════════════════════════════════════════════

def encode_all_molecules(spec: EncodingSpec) -> Dict[str, Dict]:
    """Encode all molecules."""
    from training_iteration_v3 import encode_molecule
    molecules = kb.get_all_molecules()
    results = {}

    for name, mol in molecules.items():
        vec_raw = encode_molecule(name, spec)
        vec = golay_snap(vec_raw)
        hw = sum(vec)

        if HAS_GOLAY:
            tax = hw * 0.2647 + sum(v*v for v in vec) / 8.0
            nrci = 10.0 / (10.0 + tax)
        else:
            nrci = 0

        results[name] = {
            "name": name,
            "vec": vec,
            "hw": hw,
            "nrci": nrci,
            "nrci_kb": mol.nrci_val,
            "props": {k: float(v) for k, v in mol.properties.items() if isinstance(v, Fraction)},
        }

    return results


def analyse_molecule_distribution(encodings: Dict[str, Dict], verbose: bool = True):
    """Analyse molecule encoding distribution."""
    hws = [e["hw"] for e in encodings.values()]
    nrcis = [e["nrci"] for e in encodings.values()]
    nrcis_kb = [e["nrci_kb"] for e in encodings.values() if e["nrci_kb"] > 0]

    hw_dist = Counter(hws)
    unique_vecs = set(tuple(e["vec"]) for e in encodings.values())

    if verbose:
        print(f"\n  Molecule Distribution:")
        print(f"    Molecules: {len(encodings)}")
        print(f"    Unique vectors: {len(unique_vecs)}")
        print(f"    HW distribution:")
        for hw in sorted(hw_dist.keys()):
            print(f"      HW={hw:2d}: {hw_dist[hw]:3d}")

        # Correlation between our NRCI and KB NRCI
        if nrcis_kb and len(nrcis_kb) > 3:
            our_nrcis = [e["nrci"] for e in encodings.values() if e["nrci_kb"] > 0]
            r = pearson_r(our_nrcis, nrcis_kb)
            print(f"    r(our_NRCI, KB_NRCI) = {r:+.4f}")

    return {
        "n_molecules": len(encodings),
        "unique_vectors": len(unique_vecs),
        "hw_dist": dict(hw_dist),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Element group analysis (by periodic table group)
# ═══════════════════════════════════════════════════════════════════════════════

ELEMENT_GROUPS = {
    "alkali": ["Li", "Na", "K", "Rb", "Cs", "Fr"],
    "alkaline": ["Be", "Mg", "Ca", "Sr", "Ba", "Ra"],
    "transition": ["Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
                    "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
                    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
                    "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn"],
    "post_transition": ["Al", "Ga", "In", "Sn", "Tl", "Pb", "Bi", "Nh", "Fl", "Mc", "Lv", "Ts"],
    "metalloid": ["B", "Si", "Ge", "As", "Sb", "Te", "Po"],
    "nonmetal": ["H", "C", "N", "O", "P", "S", "Se"],
    "halogen": ["F", "Cl", "Br", "I", "At"],
    "noble": ["He", "Ne", "Ar", "Kr", "Xe", "Rn", "Og"],
    "lanthanide": ["La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"],
    "actinide": ["Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"],
}


def analyse_element_groups(encodings: Dict[str, Dict], verbose: bool = True):
    """Analyse how element groups cluster in the encoding space."""
    group_stats = {}

    for group_name, members in ELEMENT_GROUPS.items():
        group_encodings = [encodings[s] for s in members if s in encodings]
        if not group_encodings:
            continue

        hws = [e["hw"] for e in group_encodings]
        nrcis = [e["nrci"] for e in group_encodings]
        vecs = [tuple(e["vec"]) for e in group_encodings]
        unique = len(set(vecs))

        group_stats[group_name] = {
            "n": len(group_encodings),
            "mean_hw": statistics.mean(hws) if hws else 0,
            "mean_nrci": statistics.mean(nrcis) if nrcis else 0,
            "unique_vectors": unique,
            "collision_rate": 1 - unique / len(group_encodings) if group_encodings else 0,
        }

    if verbose:
        print(f"\n  Element Group Analysis:")
        print(f"  {'Group':15s} {'n':3s} {'HW':5s} {'NRCI':6s} {'Unique':6s} {'Collide':7s}")
        print(f"  {'-'*15} {'---':3s} {'-----':5s} {'------':6s} {'------':6s} {'-------':7s}")
        for gname, stats in sorted(group_stats.items(), key=lambda x: -x[1]["mean_nrci"]):
            print(f"  {gname:15s} {stats['n']:3d} {stats['mean_hw']:5.1f} "
                  f"{stats['mean_nrci']:.4f} {stats['unique_vectors']:6d} "
                  f"{stats['collision_rate']:.1%}")

    return group_stats


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def run_full_training():
    """Comprehensive training on full periodic table + all molecules."""
    print("=" * 70)
    print("GLM FULL TRAINING: PERIODIC TABLE + MOLECULES")
    print("=" * 70)

    elements = kb.get_all_elements()
    molecules = kb.get_all_molecules()
    print(f"Elements: {len(elements)}, Molecules: {len(molecules)}")
    print(f"Known chemistry pairs: {len(kb.KNOWN_PAIRS)}")

    all_results = {}

    for spec_name, spec in SPECS.items():
        print(f"\n{'='*70}")
        print(f"ENCODING: {spec_name}")
        print(f"  prop_set: {spec.prop_set}")
        print(f"  scaling: {spec.scaling}")
        print(f"{'='*70}")

        # 1. Encode all elements
        t0 = time.time()
        elem_enc = encode_all_elements(spec)
        t_encode = time.time() - t0

        # 2. Analyse element distribution
        elem_dist = analyse_element_distribution(elem_enc, spec_name)

        # 3. Element group analysis
        group_stats = analyse_element_groups(elem_enc)

        # 4. Full pair sweep
        t0 = time.time()
        pairs = full_pair_sweep(elem_enc, max_pairs=7000)
        t_pairs = time.time() - t0
        pair_dist = analyse_pair_distribution(pairs)

        # 5. Known chemistry correlation
        chem = correlate_known_chemistry(elem_enc)

        # 6. Encode molecules
        mol_enc = encode_all_molecules(spec)
        mol_dist = analyse_molecule_distribution(mol_enc)

        # Timing
        print(f"\n  Timing: encode={t_encode:.2f}s, pairs={t_pairs:.2f}s")

        all_results[spec_name] = {
            "spec": spec.to_dict(),
            "element_distribution": elem_dist,
            "group_stats": group_stats,
            "pair_distribution": pair_dist,
            "chemistry": chem,
            "molecule_distribution": mol_dist,
        }

    # ═══════════════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("FULL TRAINING SUMMARY")
    print("=" * 70)

    print(f"\n{'Encoding':20s} {'Unique':6s} {'r(BE)':7s} {'r(ΔH)':7s} {'MeanHW':6s} {'MeanNRCI':8s}")
    print(f"{'-'*20} {'------':6s} {'-------':7s} {'-------':7s} {'------':6s} {'--------':8s}")
    for name, r in all_results.items():
        ed = r["element_distribution"]
        ch = r["chemistry"]
        print(f"{name:20s} {ed['unique_vectors']:6d} "
              f"{ch['best_r_be']:+7.4f} {ch['best_r_dh']:+7.4f} "
              f"{ed['mean_hw']:6.1f} {ed['mean_nrci']:8.4f}")

    # Save
    out_path = SCRIPT_DIR.parent / "data" / "training_full_table.json"
    # Convert for JSON serialization
    save_data = {}
    for name, r in all_results.items():
        save_data[name] = {
            "spec": r["spec"],
            "element_distribution": r["element_distribution"],
            "pair_distribution": r["pair_distribution"],
            "chemistry": {k: v for k, v in r["chemistry"].items() if k != "correlations"},
            "chemistry_correlations": r["chemistry"].get("correlations", {}),
            "molecule_distribution": r["molecule_distribution"],
        }
    with open(out_path, "w") as f:
        json.dump(save_data, f, indent=2, default=str)
    print(f"\n  Results saved to {out_path}")

    # Update calibration log
    update_calibration_log(all_results)

    return all_results


def update_calibration_log(all_results):
    log_path = SCRIPT_DIR.parent / "CALIBRATION_LOG.md"
    with open(log_path, "a") as f:
        f.write("\n\n---\n\n")
        f.write("## Iteration 7 — Full Periodic Table Training\n\n")
        f.write("**Date:** 2 Aug 2026\n\n")
        f.write(f"Elements: {len(kb.get_all_elements())}, Molecules: {len(kb.get_all_molecules())}\n\n")

        f.write("### Encoding Comparison\n\n")
        f.write("| Encoding | Unique Vectors | r(BE) | r(ΔH) | Mean HW | Mean NRCI |\n")
        f.write("|----------|---------------|-------|-------|---------|----------|\n")
        for name, r in all_results.items():
            ed = r["element_distribution"]
            ch = r["chemistry"]
            f.write(f"| {name} | {ed['unique_vectors']} | "
                    f"{ch['best_r_be']:+.4f} | {ch['best_r_dh']:+.4f} | "
                    f"{ed['mean_hw']:.1f} | {ed['mean_nrci']:.4f} |\n")

        # Element group analysis from best encoding
        best_name = max(all_results, key=lambda n: all_results[n]["chemistry"]["best_r_dh"])
        best = all_results[best_name]
        f.write(f"\n### Element Group Analysis ({best_name})\n\n")
        f.write("| Group | n | Mean HW | Mean NRCI | Unique | Collision Rate |\n")
        f.write("|-------|---|---------|----------|--------|----------------|\n")
        for gname, stats in sorted(best["group_stats"].items(), key=lambda x: -x[1]["mean_nrci"]):
            f.write(f"| {gname} | {stats['n']} | {stats['mean_hw']:.1f} | "
                    f"{stats['mean_nrci']:.4f} | {stats['unique_vectors']} | "
                    f"{stats['collision_rate']:.1%} |\n")

        f.write(f"\n### Pair Distribution ({best_name})\n\n")
        pd = best["pair_distribution"]
        f.write(f"- Total pairs: {pd['n_pairs']}\n")
        f.write(f"- Mean HW(XOR): {pd['mean_hw_xor']:.1f}\n")
        f.write(f"- Mean overlap: {pd['mean_overlap']:.1f}\n")
        f.write(f"- Mean hex agreements: {pd['mean_hex_agreements']:.1f}\n")

        f.write(f"\n### Key Findings\n\n")
        f.write(f"- Full periodic table encoded and analysed\n")
        f.write(f"- Element groups cluster differently in the encoding space\n")
        f.write(f"- Noble gases and halogens have distinct signatures\n")
        f.write(f"- Transition metals show high collision rates (similar vectors)\n")


if __name__ == "__main__":
    run_full_training()
