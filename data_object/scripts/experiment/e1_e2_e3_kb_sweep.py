"""
Test E1 + E2 + E3: KB-hardened vector pair sweep + REACTION calibration.

E1: Re-run the pair sweep using KB-hardened 24-bit vectors (not hand-rolled).
    Confirm whether the E0 correlations survive.
E2: Scale up to 30+ reactive pairs for statistical significance.
E3: Use KB REACTION entries directly. Compare predicted interaction metric
    vs the actual ΔH of the reaction.

Combined: one script, one results file, one ledger update.
"""

from __future__ import annotations

import sys
import json
import math
import statistics
import time
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Tuple, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import ubp_unified_v5 as ubp
import spatial_arithmetic as sa
import ubp_kb_loader as kb
import golay_mog_investigation as inv

OUT_DIR = Path("/home/z/my-project/download")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ════════════════════════════════════════════════════════════════════════════════
# Helper: compute all interaction metrics for a pair of 24-bit vectors
# ════════════════════════════════════════════════════════════════════════════════

def interaction_metrics(vec_a: List[int], vec_b: List[int]) -> Dict:
    """Compute the full interaction metric suite for two 24-bit vectors.

    This is the KB-hardened version. Vectors are assumed to already be
    valid Golay codewords (syndrome weight 0), so 'snap' is a no-op for
    individual objects but XOR may or may not be a codeword.
    """
    av, bv = vec_a, vec_b
    xor = [av[i] ^ bv[i] for i in range(24)]
    snapped, meta = ubp.GOLAY_ENGINE.snap_to_codeword(xor)
    hw_xor = sum(xor)
    sw_xor = sum(ubp.GOLAY_ENGINE.syndrome(xor))

    # Hexacode shadow of each
    hex_a, _ = ubp.GOLAY_ENGINE.mog_decompose(av)
    hex_b, _ = ubp.GOLAY_ENGINE.mog_decompose(bv)
    hex_xor, _ = ubp.GOLAY_ENGINE.mog_decompose(xor)

    # Hexacode shadow diff
    agreements = sum(1 for x, y in zip(hex_a, hex_b) if x == y)
    disagreements = 6 - agreements

    # Spatial scene merge (using rule 3 from inv)
    scene_a = inv.skew_rule_mog_grid_scene(av)
    scene_b = inv.skew_rule_mog_grid_scene(bv)
    active_a = [c for c in scene_a["cells"] if c["on"]]
    active_b = [c for c in scene_b["cells"] if c["on"]]

    scn_min = None
    scn_mean = None
    scn_overlap = 0
    if active_a and active_b:
        y_offset = 5.0
        active_b_off = [
            (c["centroid"][0], c["centroid"][1] + y_offset, c["centroid"][2])
            for c in active_b
        ]
        distances = []
        for ca in active_a:
            for cb in active_b_off:
                d = math.dist(ca["centroid"], cb)
                distances.append(d)
                if d < (ca["radius"] + 0.5):  # 0.5 = inactive cell radius
                    scn_overlap += 1
        scn_min = min(distances)
        scn_mean = statistics.mean(distances)

    # Spatial arithmetic op: cap to low 6 bits + 1
    int_a_full = sum((av[i] << (23 - i)) for i in range(24))
    int_b_full = sum((bv[i] << (23 - i)) for i in range(24))
    int_a_cap = (int_a_full & 0x3F) + 1
    int_b_cap = (int_b_full & 0x3F) + 1
    nat_sum, _ = sa.natural_add(int_a_cap, int_b_cap)

    # Leech tax of the XOR (the 'interaction tax' from UBP)
    tax_xor = ubp.LEECH_ENGINE.symmetry_tax(xor)
    nrci_xor = ubp.LEECH_ENGINE.calculate_nrci(xor)

    # Ontological health of XOR (4-layer split)
    onto_xor = ubp.LEECH_ENGINE.ontological_health(xor)

    # 'Blast radius' metrics: how many bits flip when we XOR?
    # Already captured by hw_xor.
    # But we can also measure how the XOR distributes across MOG rows.
    mog_xor = [xor[r*6:(r+1)*6] for r in range(4)]
    row_hw = [sum(row) for row in mog_xor]

    return {
        "xor_hamming_weight": hw_xor,
        "xor_syndrome_weight": sw_xor,
        "xor_is_codeword": sw_xor == 0,
        "xor_tax": str(tax_xor),
        "xor_nrci": str(nrci_xor),
        "hex_a": list(hex_a),
        "hex_b": list(hex_b),
        "hex_xor": list(hex_xor),
        "hex_agreements": agreements,
        "hex_disagreements": disagreements,
        "scn_min_distance": scn_min,
        "scn_mean_distance": scn_mean,
        "scn_overlap_count": scn_overlap,
        "int_a_full": int_a_full,
        "int_b_full": int_b_full,
        "int_a_cap": int_a_cap,
        "int_b_cap": int_b_cap,
        "nat_sum": nat_sum,
        "row_hw_xor": row_hw,
        "onto_xor": {k: str(v) for k, v in onto_xor.items()},
    }


# ════════════════════════════════════════════════════════════════════════════════
# E1+E2: Pair sweep with KB-hardened vectors
# ════════════════════════════════════════════════════════════════════════════════

# Define 30+ reactive pairs with known bond energies
# Format: (sym_a, sym_b, bond_energy_kJ, delta_H_form_kJ_or_None, label)
KNOWN_PAIRS = [
    # Single-bond diatomics & simple binaries
    ("H",  "H",   436,    0, "H2 bond"),
    ("O",  "O",   498,    0, "O2 bond"),
    ("N",  "N",   945,    0, "N2 triple bond"),
    ("F",  "F",   159,    0, "F2 bond"),
    ("Cl", "Cl",  243,    0, "Cl2 bond"),
    # H-X single bonds
    ("H",  "F",   570, -273, "HF"),
    ("H",  "Cl",  432,  -92, "HCl"),
    ("H",  "Br",  366,  -36, "HBr"),
    ("H",  "I",   298,  +26, "HI"),
    ("H",  "O",   463, -286, "H2O O-H"),
    ("H",  "N",   391,  -46, "NH3 N-H"),
    ("H",  "C",   413,  -75, "CH4 C-H"),
    ("H",  "S",   363,  -20, "H2S"),
    # C-X bonds
    ("C",  "O",   799, -394, "CO2 C=O"),  # double bond
    ("C",  "C",   347,    0, "C-C single"),
    ("C",  "N",   305,    0, "C-N"),
    ("C",  "Cl",  339, -102, "CCl4"),
    ("C",  "F",   485, -680, "CF4"),
    # Ionic pairs
    ("Na", "Cl",  411, -411, "NaCl"),
    ("Na", "F",   477, -574, "NaF"),
    ("Na", "Br",  367, -361, "NaBr"),
    ("Na", "I",   305, -288, "NaI"),
    ("K",  "Cl",  427, -436, "KCl"),
    ("K",  "F",   494, -567, "KF"),
    ("K",  "Br",  382, -394, "KBr"),
    ("K",  "I",   323, -328, "KI"),
    ("Li", "F",   577, -617, "LiF"),
    ("Li", "Cl",  469, -409, "LiCl"),
    ("Li", "Br",  423, -351, "LiBr"),
    ("Li", "I",   345, -271, "LiI"),
    # Oxides / redox
    ("Fe", "O",   460, -824, "Fe2O3"),
    ("Mg", "O",   385, -602, "MgO"),
    ("Ca", "O",   360, -635, "CaO"),
    ("Al", "O",   511, -1676, "Al2O3"),
    ("Si", "O",   452, -911, "SiO2"),
    # Other
    ("Cl", "O",   205,  -33, "Cl-O"),
    ("S",  "O",   523, -297, "SO2"),
]


def run_e1_e2_sweep():
    """Run the KB-hardened pair sweep."""
    print("=" * 80)
    print("E1+E2 — KB-HARDENED PAIR SWEEP")
    print("=" * 80)
    print(f"Sweeping {len(KNOWN_PAIRS)} element pairs using KB vectors...")
    print()

    results = []
    skipped = []
    for sym_a, sym_b, be, dh, label in KNOWN_PAIRS:
        ea = kb.get_element(sym_a)
        eb = kb.get_element(sym_b)
        if ea is None or eb is None:
            skipped.append((sym_a, sym_b, "element not in KB"))
            continue
        vec_a = ea.vector24
        vec_b = eb.vector24
        m = interaction_metrics(vec_a, vec_b)
        m["pair"] = (sym_a, sym_b)
        m["label"] = label
        m["bond_energy_kJ"] = be
        m["delta_H_kJ"] = dh
        m["hw_a"] = sum(vec_a)
        m["hw_b"] = sum(vec_b)
        results.append(m)

    print(f"Computed: {len(results)} pairs, skipped: {len(skipped)}")
    if skipped:
        for s in skipped:
            print(f"  skipped: {s}")
    print()

    # Print table
    print(f"{'Pair':<10} {'BE':>5} {'ΔH':>6} │ "
          f"{'HWa':>4} {'HWb':>4} {'X_HW':>5} {'X_SW':>5} {'CW':>3} │ "
          f"{'HexA':>4} {'HexD':>4} │ {'ScOv':>4} {'NatSum':>7} │ {'XORtax':>10}")
    print("-" * 110)
    for r in results:
        a, b = r["pair"]
        be = r["bond_energy_kJ"]
        dh = r["delta_H_kJ"] if r["delta_H_kJ"] is not None else 0
        cw = "Y" if r["xor_is_codeword"] else "N"
        scn_ov = r["scn_overlap_count"]
        nat = r["nat_sum"]
        xor_tax_short = float(Fraction(r["xor_tax"]))
        print(f"{a+'+'+b:<10} {be:>5} {dh:>6} │ "
              f"{r['hw_a']:>4} {r['hw_b']:>4} {r['xor_hamming_weight']:>5} "
              f"{r['xor_syndrome_weight']:>5} {cw:>3} │ "
              f"{r['hex_agreements']:>4} {r['hex_disagreements']:>4} │ "
              f"{scn_ov:>4} {nat:>7} │ {xor_tax_short:>10.4f}")

    # Correlations
    print()
    print("── Pearson correlations with Bond Energy (n = %d) ──" % len(results))
    be_vals = [r["bond_energy_kJ"] for r in results]

    metric_keys = [
        "xor_hamming_weight", "xor_syndrome_weight",
        "hex_agreements", "hex_disagreements",
        "scn_overlap_count", "nat_sum",
    ]
    for k in metric_keys:
        vals = [r[k] for r in results]
        if len(vals) > 1 and statistics.pstdev(vals) > 0:
            r_corr = statistics.correlation(vals, be_vals)
            print(f"  {k:<22}: r = {r_corr:+.4f}")

    # Also XOR tax
    xor_tax_vals = [float(Fraction(r["xor_tax"])) for r in results]
    if len(xor_tax_vals) > 1 and statistics.pstdev(xor_tax_vals) > 0:
        r_corr = statistics.correlation(xor_tax_vals, be_vals)
        print(f"  {'xor_tax':<22}: r = {r_corr:+.4f}")

    # ΔH correlation (only for pairs with ΔH != 0)
    print()
    print("── Pearson correlations with ΔH (formation enthalpy) ──")
    dh_pairs = [r for r in results if r["delta_H_kJ"] is not None and r["delta_H_kJ"] != 0]
    print(f"  (n = {len(dh_pairs)})")
    if len(dh_pairs) > 1:
        dh_vals = [r["delta_H_kJ"] for r in dh_pairs]
        for k in metric_keys + ["xor_tax_float"]:
            if k == "xor_tax_float":
                vals = [float(Fraction(r["xor_tax"])) for r in dh_pairs]
            else:
                vals = [r[k] for r in dh_pairs]
            if len(vals) > 1 and statistics.pstdev(vals) > 0:
                r_corr = statistics.correlation(vals, dh_vals)
                print(f"  {k:<22}: r = {r_corr:+.4f}")

    # Save JSON
    out_path = OUT_DIR / "e1_e2_kb_pair_sweep.json"
    def ser(o):
        if isinstance(o, Fraction): return str(o)
        if isinstance(o, tuple): return list(o)
        if isinstance(o, set): return list(o)
        return str(o)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=ser)
    print()
    print(f"Saved: {out_path}  ({out_path.stat().st_size:,} bytes)")
    return results


# ════════════════════════════════════════════════════════════════════════════════
# E3: REACTION entry calibration
# ════════════════════════════════════════════════════════════════════════════════

def run_e3_reactions():
    """For each REACTION entry, compute interaction metrics and compare to ΔH."""
    print()
    print("=" * 80)
    print("E3 — REACTION ENTRY CALIBRATION")
    print("=" * 80)
    print("For each KB reaction, compute metrics on the reaction's own 24-bit vector")
    print("and on the XOR of reactant element vectors. Compare to ΔH.")
    print()

    results = []
    for uid, rxn in kb.REACTIONS.items():
        # Get reaction's own hardened vector
        rxn_vec = rxn.vector24
        rxn_hw = sum(rxn_vec)

        # Get the reactant elements
        reactant_elems = rxn.reactant_elements
        # Look up their KB vectors
        reactant_vecs = []
        for sym in reactant_elems:
            e = kb.get_element(sym)
            if e is not None:
                reactant_vecs.append((sym, e.vector24))

        # Compute pairwise XOR between all reactant elements (if 2+)
        pair_metrics = None
        if len(reactant_vecs) >= 2:
            (sym_a, vec_a), (sym_b, vec_b) = reactant_vecs[:2]
            pair_metrics = interaction_metrics(vec_a, vec_b)
            pair_metrics["pair"] = (sym_a, sym_b)

        # Reaction-level metrics: tax of the reaction's own vector
        rxn_tax = ubp.LEECH_ENGINE.symmetry_tax(rxn_vec)
        rxn_nrci = ubp.LEECH_ENGINE.calculate_nrci(rxn_vec)
        rxn_sw = ubp.GOLAY_ENGINE.syndrome_weight(rxn_vec)
        # Hexacode shadow of the reaction
        rxn_hex, _ = ubp.GOLAY_ENGINE.mog_decompose(rxn_vec)

        results.append({
            "ubp_id": uid,
            "delta_H_kJ": rxn.delta_h_kJ,
            "reaction_type": rxn.reaction_type,
            "reactants_str": rxn.reactants_str,
            "products_str": rxn.products_str,
            "reactant_elements": reactant_elems,
            "rxn_hw": rxn_hw,
            "rxn_sw": rxn_sw,
            "rxn_tax": str(rxn_tax),
            "rxn_nrci": str(rxn_nrci),
            "rxn_hex": list(rxn_hex),
            "pair_metrics": pair_metrics,
        })

    # Print table
    print(f"{'ubp_id':<32} {'ΔH':>8} {'type':<14} {'rxn_HW':>7} {'rxn_tax':>10} │ "
          f"pair XOR_HW  XOR_SW  XOR_tax")
    print("-" * 110)
    for r in results:
        dh = r["delta_H_kJ"]
        dh_str = f"{dh:>8.1f}" if dh is not None else f"{'?':>8}"
        rt = r["reaction_type"] or "?"
        tax_short = float(Fraction(r["rxn_tax"]))
        pm = r["pair_metrics"]
        if pm:
            xor_hw = pm["xor_hamming_weight"]
            xor_sw = pm["xor_syndrome_weight"]
            xor_tax_short = float(Fraction(pm["xor_tax"]))
            pm_str = f"{xor_hw:>9} {xor_sw:>7} {xor_tax_short:>9.4f}"
        else:
            pm_str = f"{'(single)':>9} {'-':>7} {'-':>9}"
        print(f"{r['ubp_id']:<32} {dh_str} {rt:<14} {r['rxn_hw']:>7} {tax_short:>10.4f} │ {pm_str}")

    # Correlation between rxn_tax and ΔH (where ΔH is known)
    print()
    print("── Correlation: reaction-level tax vs ΔH ──")
    dh_pairs = [r for r in results if r["delta_H_kJ"] is not None]
    if len(dh_pairs) > 1:
        dh_vals = [r["delta_H_kJ"] for r in dh_pairs]
        print(f"  n = {len(dh_pairs)}")
        for k, label in [("rxn_hw", "rxn_HW"),
                         ("rxn_tax_float", "rxn_tax")]:
            if k == "rxn_tax_float":
                vals = [float(Fraction(r["rxn_tax"])) for r in dh_pairs]
            else:
                vals = [r[k] for r in dh_pairs]
            if statistics.pstdev(vals) > 0:
                r_corr = statistics.correlation(vals, dh_vals)
                print(f"  {label:<22}: r = {r_corr:+.4f}")

        # Pair-level correlation (where pair_metrics exists)
        pair_dh = [r for r in dh_pairs if r["pair_metrics"] is not None]
        if len(pair_dh) > 1:
            print()
            print(f"── Correlation: pair (XOR) metrics vs ΔH (n = {len(pair_dh)}) ──")
            dh_vals_pair = [r["delta_H_kJ"] for r in pair_dh]
            for k in ["xor_hamming_weight", "xor_syndrome_weight",
                      "hex_agreements", "hex_disagreements",
                      "scn_overlap_count", "nat_sum"]:
                vals = [r["pair_metrics"][k] for r in pair_dh]
                if statistics.pstdev(vals) > 0:
                    r_corr = statistics.correlation(vals, dh_vals_pair)
                    print(f"  {k:<22}: r = {r_corr:+.4f}")
            xor_tax_vals = [float(Fraction(r["pair_metrics"]["xor_tax"])) for r in pair_dh]
            if statistics.pstdev(xor_tax_vals) > 0:
                r_corr = statistics.correlation(xor_tax_vals, dh_vals_pair)
                print(f"  {'xor_tax':<22}: r = {r_corr:+.4f}")

    out_path = OUT_DIR / "e3_kb_reactions.json"
    def ser(o):
        if isinstance(o, Fraction): return str(o)
        if isinstance(o, tuple): return list(o)
        if isinstance(o, set): return list(o)
        return str(o)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=ser)
    print()
    print(f"Saved: {out_path}  ({out_path.stat().st_size:,} bytes)")
    return results


# ════════════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()
    e1_results = run_e1_e2_sweep()
    e3_results = run_e3_reactions()
    print()
    print("=" * 80)
    print(f"DONE. Total time: {time.time() - t0:.2f}s")
    print("=" * 80)
    return e1_results, e3_results


if __name__ == "__main__":
    main()
