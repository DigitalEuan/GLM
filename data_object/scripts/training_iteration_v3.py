"""
training_iteration_v3.py — Molecule Training + Bond-Order Encoding

Building on v1-v2 findings:
  - Best element encoding: EN×10, BP÷40, MP÷40, Rho×10 (score 0.58, r(ΔH)=−0.91)
  - Bond energy needs bond-order awareness

This iteration:
  1. Encode molecules as Data Objects using their physical properties
  2. Test element-molecule interaction predictions
  3. Explore bond-order encoding (single/double/triple as MOG modifier)
  4. Build cross-domain understanding (elements ↔ molecules)
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
    pearson_r, SCALING_PRESETS, gray6, HAS_GOLAY,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Molecule encoding
# ═══════════════════════════════════════════════════════════════════════════════

def encode_molecule(name: str, spec: EncodingSpec) -> List[int]:
    """Encode a molecule as a 24-bit vector using the given spec."""
    mol = kb.get_molecule(name)
    if mol is None:
        return [0] * 24

    rows = [None] * 4
    for i, row_idx in enumerate(spec.row_assignment):
        prop = spec.prop_set[i]
        val = mol.properties.get(prop)
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

    bits = []
    for row in rows:
        if row is None:
            bits.extend([0] * 6)
        else:
            bits.extend(row)
    return bits


# ═══════════════════════════════════════════════════════════════════════════════
# Molecule property analysis
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_molecule_properties():
    """What properties do molecules have?"""
    print("\n" + "=" * 70)
    print("MOLECULE PROPERTY ANALYSIS")
    print("=" * 70)

    molecules = kb.get_all_molecules()
    print(f"Total molecules: {len(molecules)}")

    # Count which properties are available
    prop_counts = {}
    for name, mol in molecules.items():
        for prop in mol.properties:
            prop_counts[prop] = prop_counts.get(prop, 0) + 1

    print(f"\nProperty availability:")
    for prop, count in sorted(prop_counts.items(), key=lambda x: -x[1]):
        print(f"  {prop}: {count}/{len(molecules)} ({100*count/len(molecules):.0f}%)")

    # Show sample molecules
    print(f"\nSample molecule data:")
    for name in ["H2O", "NACL", "METHANOL", "BENZENE", "GLUCOSE", "ATP"]:
        mol = molecules.get(name)
        if mol:
            print(f"  {name}: props={dict(mol.properties)}, hw={mol.hamming_weight}")

    return molecules


# ═══════════════════════════════════════════════════════════════════════════════
# Molecule-molecule interaction scoring
# ═══════════════════════════════════════════════════════════════════════════════

def score_molecule_encoding(spec: EncodingSpec, verbose: bool = False) -> Dict:
    """Score an encoding on molecule bond energies and formation enthalpies."""
    molecules = kb.get_all_molecules()

    # Encode all molecules
    mol_vectors = {}
    for name in molecules:
        vec = encode_molecule(name, spec)
        vec = golay_snap(vec)
        mol_vectors[name] = vec

    # Test molecule bond energies
    be_records = []
    for entry in kb.MOLECULE_BOND_ENERGIES:
        mol_name = entry[0]
        bond_type = entry[1]
        be = entry[2]
        label = entry[3] if len(entry) > 3 else ""
        if mol_name not in mol_vectors:
            continue
        if mol_name not in mol_vectors:
            continue
        # Use the molecule's vector as a proxy for the bond
        vec = mol_vectors[mol_name]
        hw = sum(vec)
        be_records.append({
            "molecule": mol_name,
            "bond": bond_type,
            "be": be,
            "hw": hw,
            "nrci": molecules[mol_name].nrci_val,
            "label": label,
        })

    # Test molecule formation enthalpies
    dh_records = []
    for entry in kb.MOLECULE_PAIRS:
        mol_a = entry[0]
        mol_b = entry[1]
        itype = entry[2]
        value = entry[3]
        label = entry[4] if len(entry) > 4 else ""
        if mol_a not in mol_vectors or mol_b not in mol_vectors:
            continue
        va, vb = mol_vectors[mol_a], mol_vectors[mol_b]
        m = compute_interaction_metrics(va, vb)
        dh_records.append({
            "pair": f"{mol_a}-{mol_b}",
            "dh": value,
            **m,
        })

    # Analyse bond energies
    if be_records:
        be_vals = [r["be"] for r in be_records]
        hw_vals = [r["hw"] for r in be_records]
        nrci_vals = [r["nrci"] for r in be_records]

        r_hw_be = pearson_r(hw_vals, be_vals)
        r_nrci_be = pearson_r(nrci_vals, be_vals)

        if verbose:
            print(f"  Bond energy analysis ({len(be_records)} bonds):")
            print(f"    r(HW, BE) = {r_hw_be:+.4f}")
            print(f"    r(NRCI, BE) = {r_nrci_be:+.4f}")
    else:
        r_hw_be = 0
        r_nrci_be = 0

    # Analyse formation enthalpies
    if dh_records:
        dh_vals = [r["dh"] for r in dh_records]
        metric_names = ["hw_xor", "sw_xor", "hex_agreements", "overlap", "hamming_dist"]
        best_dh_r = 0
        best_dh_metric = ""
        for metric in metric_names:
            vals = [r[metric] for r in dh_records]
            r = pearson_r(vals, dh_vals)
            if abs(r) > abs(best_dh_r):
                best_dh_r = r
                best_dh_metric = metric

        if verbose:
            print(f"  Formation enthalpy analysis ({len(dh_records)} pairs):")
            print(f"    Best r(ΔH) = {best_dh_r:+.4f} via {best_dh_metric}")
    else:
        best_dh_r = 0
        best_dh_metric = ""

    overall = (abs(r_hw_be) + abs(r_nrci_be) + abs(best_dh_r)) / 3

    result = {
        "name": spec.name,
        "overall_score": overall,
        "r_hw_be": r_hw_be,
        "r_nrci_be": r_nrci_be,
        "best_r_dh": best_dh_r,
        "best_r_dh_metric": best_dh_metric,
        "n_be": len(be_records),
        "n_dh": len(dh_records),
    }

    if verbose:
        print(f"  Overall score: {overall:.4f}")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-domain: element encoding applied to molecules
# ═══════════════════════════════════════════════════════════════════════════════

def cross_domain_analysis():
    """Can the element encoding predict molecule properties?"""
    print("\n" + "=" * 70)
    print("CROSS-DOMAIN ANALYSIS: Elements → Molecules")
    print("=" * 70)

    # Best element encoding from v1-v2
    elem_spec = EncodingSpec(
        name="element_best",
        prop_set=["EN", "BP", "MP", "Rho"],
        row_assignment=[0, 1, 2, 3],
        scaling={"EN": "en_x10", "BP": "div40", "MP": "div40", "Rho": "rho_x10"},
    )

    # Encode molecules using the element encoding spec
    molecules = kb.get_all_molecules()
    print(f"Encoding {len(molecules)} molecules with element spec...")

    mol_data = []
    for name, mol in molecules.items():
        vec = encode_molecule(name, elem_spec)
        snapped = golay_snap(vec)
        hw = sum(snapped)
        mol_data.append({
            "name": name,
            "hw": hw,
            "nrci": mol.nrci_val,
            "mass": float(mol.properties.get("M", 0)),
            "bp": float(mol.properties.get("BP", 0)),
            "mp": float(mol.properties.get("MP", 0)),
            "rho": float(mol.properties.get("Rho", 0)),
            "vec": snapped,
        })

    # Analyse distributions
    hw_dist = {}
    for d in mol_data:
        hw = d["hw"]
        hw_dist[hw] = hw_dist.get(hw, 0) + 1

    print(f"\nHamming weight distribution (molecules):")
    for hw in sorted(hw_dist.keys()):
        print(f"  HW={hw}: {hw_dist[hw]} molecules")

    unique_vecs = set(tuple(d["vec"]) for d in mol_data)
    print(f"\nUnique vectors: {len(unique_vecs)} / {len(mol_data)} molecules")

    # Molecules with mass data
    with_mass = [d for d in mol_data if d["mass"] > 0]
    if with_mass:
        masses = [d["mass"] for d in with_mass]
        hws = [d["hw"] for d in with_mass]
        r_mass_hw = pearson_r(masses, hws)
        print(f"\nr(Mass, HW) = {r_mass_hw:+.4f} (n={len(with_mass)})")

        # NRCI vs mass
        nrcis = [d["nrci"] for d in with_mass]
        r_mass_nrci = pearson_r(masses, nrcis)
        print(f"r(Mass, NRCI) = {r_mass_nrci:+.4f}")

    # Molecules with BP data
    with_bp = [d for d in mol_data if d["bp"] > 0]
    if with_bp:
        bps = [d["bp"] for d in with_bp]
        hws_bp = [d["hw"] for d in with_bp]
        r_bp_hw = pearson_r(bps, hws_bp)
        print(f"r(BP, HW) = {r_bp_hw:+.4f} (n={len(with_bp)})")

    return mol_data


# ═══════════════════════════════════════════════════════════════════════════════
# Molecule-specific encoding search
# ═══════════════════════════════════════════════════════════════════════════════

def molecule_encoding_search():
    """Search for the best encoding for molecules."""
    print("\n" + "=" * 70)
    print("MOLECULE ENCODING SEARCH")
    print("=" * 70)

    molecules = kb.get_all_molecules()
    mol_props = set()
    for name, mol in molecules.items():
        mol_props.update(mol.properties.keys())
    print(f"Available molecule properties: {sorted(mol_props)}")

    # Properties with good coverage
    good_props = []
    for prop in sorted(mol_props):
        count = sum(1 for mol in molecules.values() if mol.properties.get(prop) is not None)
        if count >= 10:
            good_props.append(prop)
            print(f"  {prop}: {count}/{len(molecules)}")

    if len(good_props) < 2:
        print("  Not enough properties with data for encoding search")
        return None, None

    # Try combinations of available properties (up to 4)
    best_score = 0
    best_spec = None
    all_results = []

    for combo_size in range(2, min(5, len(good_props) + 1)):
        for combo in itertools.combinations(good_props, combo_size):
            # Pad to 4 properties if needed
            props = list(combo)
            while len(props) < 4:
                props.append(props[-1])  # duplicate last property

            scaling = {}
            for p in props:
                if p == "M":
                    scaling[p] = "log2"
                elif p in ("BP", "MP"):
                    scaling[p] = "div40"
                elif p == "Rho":
                    scaling[p] = "rho_x10"
                else:
                    scaling[p] = "identity"

            spec = EncodingSpec(
                name=f"mol_{'_'.join(combo)}",
                prop_set=props[:4],
                row_assignment=[0, 1, 2, 3],
                scaling=scaling,
            )

            result = score_molecule_encoding(spec, verbose=False)
            all_results.append((spec, result))

            if result["overall_score"] > best_score:
                best_score = result["overall_score"]
                best_spec = spec

    if all_results:
        all_results.sort(key=lambda x: -x[1]["overall_score"])
        print(f"\nTop 5 molecule encodings:")
        for spec, result in all_results[:5]:
            print(f"  {spec.name}: score={result['overall_score']:.4f} "
                  f"r_HW_BE={result['r_hw_be']:+.4f} r_ΔH={result['best_r_dh']:+.4f}")

    return best_spec, all_results


# ═══════════════════════════════════════════════════════════════════════════════
# Element-molecule interaction study
# ═══════════════════════════════════════════════════════════════════════════════

def element_molecule_interactions():
    """Study interactions between element and molecule Data Objects."""
    print("\n" + "=" * 70)
    print("ELEMENT-MOLECULE INTERACTION STUDY")
    print("=" * 70)

    # Best element encoding
    elem_spec = EncodingSpec(
        name="elem_best",
        prop_set=["EN", "BP", "MP", "Rho"],
        row_assignment=[0, 1, 2, 3],
        scaling={"EN": "en_x10", "BP": "div40", "MP": "div40", "Rho": "rho_x10"},
    )

    elements = kb.get_all_elements()
    molecules = kb.get_all_molecules()

    # Encode all
    elem_vecs = {}
    for sym in elements:
        vec = encode_element(sym, elem_spec)
        elem_vecs[sym] = golay_snap(vec)

    mol_vecs = {}
    for name in molecules:
        vec = encode_molecule(name, elem_spec)
        mol_vecs[name] = golay_snap(vec)

    # Compute element-molecule interactions for known chemistry
    # H2O: H + O → H2O
    # NaCl: Na + Cl → NaCl
    pairs = [
        ("H", "H2O", "H in water"),
        ("O", "H2O", "O in water"),
        ("Na", "NACL", "Na in salt"),
        ("Cl", "NACL", "Cl in salt"),
        ("C", "METHANE", "C in methane"),
        ("H", "METHANE", "H in methane"),
        ("N", "AMMONIA", "N in ammonia"),
        ("H", "AMMONIA", "H in ammonia"),
        ("Fe", "FEO", "Fe in rust"),
        ("O", "FEO", "O in rust"),
        ("C", "GLUCOSE", "C in glucose"),
        ("H", "GLUCOSE", "H in glucose"),
        ("O", "GLUCOSE", "O in glucose"),
    ]

    print(f"\nElement-molecule interactions ({len(pairs)} pairs):")
    for sym, mol_name, label in pairs:
        if sym not in elem_vecs or mol_name not in mol_vecs:
            continue
        va = elem_vecs[sym]
        vm = mol_vecs[mol_name]
        m = compute_interaction_metrics(va, vm)
        print(f"  {sym} ↔ {mol_name}: overlap={m['overlap']} hex={m['hex_agreements']} "
              f"hw_xor={m['hw_xor']} ({label})")

    return pairs


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def run_training_v3():
    """Run molecule training."""
    print("=" * 70)
    print("GLM TRAINING v3: MOLECULE ENCODING + CROSS-DOMAIN")
    print("=" * 70)

    # 1. Analyse molecule properties
    molecules = analyze_molecule_properties()

    # 2. Cross-domain: can element encoding predict molecule properties?
    mol_data = cross_domain_analysis()

    # 3. Molecule-specific encoding search
    best_mol_spec, mol_results = molecule_encoding_search()

    # 4. Element-molecule interaction study
    element_molecule_interactions()

    # 5. Score the best element encoding on molecules too
    print("\n" + "=" * 70)
    print("ELEMENT ENCODING ON MOLECULES")
    print("=" * 70)
    elem_spec = EncodingSpec(
        name="element_best_on_molecules",
        prop_set=["EN", "BP", "MP", "Rho"],
        row_assignment=[0, 1, 2, 3],
        scaling={"EN": "en_x10", "BP": "div40", "MP": "div40", "Rho": "rho_x10"},
    )
    elem_on_mol = score_molecule_encoding(elem_spec, verbose=True)

    # Summary
    print("\n" + "=" * 70)
    print("TRAINING v3 SUMMARY")
    print("=" * 70)
    print(f"  Molecules loaded: {len(molecules)}")
    print(f"  Element spec on molecules: score={elem_on_mol['overall_score']:.4f}")
    if best_mol_spec:
        best_result = mol_results[0][1] if mol_results else {}
        print(f"  Best molecule spec: {best_mol_spec.name} score={best_result.get('overall_score', 0):.4f}")

    # Save
    output = {
        "element_on_molecule": {"spec": elem_spec.to_dict(), "result": elem_on_mol},
        "best_molecule_spec": {"spec": best_mol_spec.to_dict() if best_mol_spec else None,
                               "result": mol_results[0][1] if mol_results else None},
    }
    out_path = SCRIPT_DIR.parent / "data" / "training_run_003_molecules.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Results saved to {out_path}")

    # Update calibration log
    update_calibration_log(elem_on_mol, best_mol_spec, mol_results)

    return output


def update_calibration_log(elem_on_mol, best_mol_spec, mol_results):
    """Append to the calibration log."""
    log_path = SCRIPT_DIR.parent / "CALIBRATION_LOG.md"
    with open(log_path, "a") as f:
        f.write("\n\n---\n\n")
        f.write("## Iteration 5 — Molecule Training\n\n")
        f.write("**Date:** 2 Aug 2026\n\n")

        f.write("### Molecule Property Coverage\n\n")
        molecules = kb.get_all_molecules()
        f.write(f"- Total molecules: {len(molecules)}\n")
        prop_counts = {}
        for mol in molecules.values():
            for prop in mol.properties:
                prop_counts[prop] = prop_counts.get(prop, 0) + 1
        for prop, count in sorted(prop_counts.items(), key=lambda x: -x[1]):
            f.write(f"- {prop}: {count}/{len(molecules)} ({100*count/len(molecules):.0f}%)\n")

        f.write(f"\n### Element Encoding on Molecules\n\n")
        f.write(f"- Score: {elem_on_mol['overall_score']:.4f}\n")
        f.write(f"- r(HW, BE): {elem_on_mol['r_hw_be']:+.4f}\n")
        f.write(f"- r(NRCI, BE): {elem_on_mol['r_nrci_be']:+.4f}\n")
        f.write(f"- Best r(ΔH): {elem_on_mol['best_r_dh']:+.4f} via {elem_on_mol['best_r_dh_metric']}\n")

        if best_mol_spec and mol_results:
            f.write(f"\n### Best Molecule Encoding\n\n")
            f.write(f"- Spec: {best_mol_spec.name}\n")
            best_result = mol_results[0][1]
            f.write(f"- Score: {best_result['overall_score']:.4f}\n")
            f.write(f"- Properties: {best_mol_spec.prop_set}\n")
            f.write(f"- Scaling: {best_mol_spec.scaling}\n")

        f.write(f"\n### Key Findings\n\n")
        f.write(f"- Molecules have fewer measurable properties than elements\n")
        f.write(f"- Mass (M), BP, MP are available for most molecules\n")
        f.write(f"- Cross-domain encoding (element spec → molecules) tests substrate generality\n")


if __name__ == "__main__":
    run_training_v3()
