"""
Deep-dive analysis on the sweep results.

Looks for:
  - Patterns in Hamming weight / syndrome weight by element class
  - Correlation between interaction metrics and known chemistry
  - Outliers and surprising alignments
  - Hexacode shadow 'grammar' patterns
  - Bit-skew distribution patterns
"""

from __future__ import annotations

import sys
import json
import math
import statistics
from pathlib import Path
from fractions import Fraction

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import golay_mog_investigation as inv
import element_data as ed

ROW_NAMES = inv.ROW_NAMES


def main():
    with open("/home/z/my-project/download/golay_mog_results.json") as f:
        results = json.load(f)

    print("=" * 78)
    print("DEEP-DIVE ANALYSIS")
    print("=" * 78)

    # ─── 1. ELEMENT CLASS PATTERNS ────────────────────────────────────────────
    print("\n[1] ELEMENT CLASS PATTERNS")
    print("    Looking at Hamming weight (HW) and syndrome weight (SW) by category:")
    print()
    print(f"    {'Sym':<5} {'Cat':<11} {'Z':>3} {'HW':>3} {'SW':>3} {'NRCI':>7} "
          f"{'Lattice':<14} {'Hex shadow':<22}")
    seen = set()
    for r in results:
        for obj_key in ("object_a", "object_b"):
            obj = r[obj_key]
            if obj["symbol"] in seen:
                continue
            seen.add(obj["symbol"])
            sym = obj["symbol"]
            el = ed.get(sym)
            hw = obj["hamming_weight"]
            sw = obj["syndrome_weight"]
            # nrci_raw may be a Fraction string like "num/den"
            nrci_str = obj["nrci_raw"]
            try:
                nrci_val = float(Fraction(nrci_str))
            except Exception:
                nrci_val = 0.0
            hex_str = "(" + ",".join(str(h) for h in obj["hex_symbols_raw"]) + ")"
            if hw == 0: lattice = "Identity"
            elif hw == 8: lattice = "Octad"
            elif hw == 12: lattice = "Dodecad"
            elif hw == 16: lattice = "Hexadecad"
            elif hw == 24: lattice = "Universe"
            else: lattice = f"Off(w={hw})"
            print(f"    {sym:<5} {el['category']:<11} {el['Z']:>3} {hw:>3} {sw:>3} "
                  f"{nrci_val:>7.4f} {lattice:<14} {hex_str:<22}")

    # ─── 2. INTERACTION METRIC CORRELATIONS ──────────────────────────────────
    print("\n[2] INTERACTION METRIC CORRELATIONS WITH BOND ENERGY")
    print("    (reactive pairs only — bond energy > 0)")

    pairs_data = []
    for r in results:
        a, b = r["pair"]
        known = r["known_chemistry"]
        be = known.get("bond_energy_kJ")
        if be is None or be == 0:
            continue
        gx = r["interactions"]["golay_xor_snap"]
        hx = r["interactions"]["hexacode_shadow_diff"]
        sx = r["interactions"]["spatial_scene_merge"]
        ax = r["interactions"]["spatial_arithmetic_op"]
        pairs_data.append({
            "pair": f"{a}+{b}",
            "be": be,
            "dh": known.get("deltaH_form_kJ") or 0,
            "xor_hw": gx["xor_hamming_weight"],
            "xor_sw": gx["xor_syndrome_weight"],
            "xor_is_cw": gx["is_codeword"],
            "hex_agr": hx["agreements"],
            "hex_dis": hx["disagreements"],
            "scn_min": sx.get("min_distance") or 0,
            "scn_mean": sx.get("mean_distance") or 0,
            "scn_overlap": sx.get("overlap_count", 0),
            "r_ratio": ax.get("radius_ratio", 0),
            "nat_sum": ax.get("natural_sum", 0),
        })

    if not pairs_data:
        print("    No reactive pairs found.")
    else:
        be_vals = [p["be"] for p in pairs_data]
        print(f"\n    {'Pair':<8} {'BE':>5} {'ΔH':>5} │ "
              f"{'X_HW':>4} {'X_SW':>4} {'CW?':>4} │ "
              f"{'HexA':>4} {'HexD':>4} │ {'ScOv':>4} {'R_rat':>6}")
        for p in pairs_data:
            print(f"    {p['pair']:<8} {p['be']:>5} {p['dh']:>5} │ "
                  f"{p['xor_hw']:>4} {p['xor_sw']:>4} {'Y' if p['xor_is_cw'] else 'N':>4} │ "
                  f"{p['hex_agr']:>4} {p['hex_dis']:>4} │ "
                  f"{p['scn_overlap']:>4} {p['r_ratio']:>6.3f}")

        # Compute Pearson correlations
        print("\n    Pearson correlations with bond energy (BE):")
        for key in ["xor_hw", "xor_sw", "hex_agr", "hex_dis",
                    "scn_min", "scn_mean", "scn_overlap", "r_ratio", "nat_sum"]:
            vals = [p[key] for p in pairs_data]
            if len(vals) > 1 and statistics.pstdev(vals) > 0:
                mean_x = statistics.mean(vals)
                mean_y = statistics.mean(be_vals)
                cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(vals, be_vals)) / len(vals)
                std_x = statistics.pstdev(vals)
                std_y = statistics.pstdev(be_vals)
                if std_x > 0 and std_y > 0:
                    r_corr = cov / (std_x * std_y)
                    print(f"      {key:<12}: r = {r_corr:+.4f}")

    # ─── 3. INERT VS REACTIVE COMPARISON ─────────────────────────────────────
    print("\n[3] INERT VS REACTIVE COMPARISON")
    print("    (noble+noble pairs should differ from reactive pairs)")
    inert_pairs = []
    reactive_pairs = []
    for r in results:
        a, b = r["pair"]
        known = r["known_chemistry"]
        be = known.get("bond_energy_kJ") or 0
        if be == 0:
            inert_pairs.append(r)
        else:
            reactive_pairs.append(r)

    if inert_pairs and reactive_pairs:
        print(f"    Inert pairs ({len(inert_pairs)}):   "
              f"avg XOR_HW = {statistics.mean(r['interactions']['golay_xor_snap']['xor_hamming_weight'] for r in inert_pairs):.2f}, "
              f"avg XOR_SW = {statistics.mean(r['interactions']['golay_xor_snap']['xor_syndrome_weight'] for r in inert_pairs):.2f}, "
              f"avg HexDis = {statistics.mean(r['interactions']['hexacode_shadow_diff']['disagreements'] for r in inert_pairs):.2f}")
        print(f"    Reactive pairs ({len(reactive_pairs)}): "
              f"avg XOR_HW = {statistics.mean(r['interactions']['golay_xor_snap']['xor_hamming_weight'] for r in reactive_pairs):.2f}, "
              f"avg XOR_SW = {statistics.mean(r['interactions']['golay_xor_snap']['xor_syndrome_weight'] for r in reactive_pairs):.2f}, "
              f"avg HexDis = {statistics.mean(r['interactions']['hexacode_shadow_diff']['disagreements'] for r in reactive_pairs):.2f}")

    # ─── 4. HEXACODE SHADOW GRAMMAR ──────────────────────────────────────────
    print("\n[4] HEXACODE SHADOW GRAMMAR PATTERNS")
    print("    Distribution of GF(4) symbols across all elements:")
    symbol_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    seen = set()
    for r in results:
        for obj_key in ("object_a", "object_b"):
            obj = r[obj_key]
            if obj["symbol"] in seen:
                continue
            seen.add(obj["symbol"])
            for h in obj["hex_symbols_raw"]:
                symbol_counts[h] += 1
    total = sum(symbol_counts.values())
    for sym, cnt in symbol_counts.items():
        symbol_name = ["0", "1", "ω", "ω²"][sym]
        pct = 100.0 * cnt / total
        bar = "█" * int(pct / 2)
        print(f"      {symbol_name}: {cnt:>3} / {total}  ({pct:5.1f}%)  {bar}")

    # ─── 5. OCTAD-CLASS OBJECTS ──────────────────────────────────────────────
    print("\n[5] OCTAD-CLASS OBJECTS (Hamming weight = 8)")
    print("    These elements 'snap' onto the perfect lattice octad weight:")
    seen = set()
    for r in results:
        for obj_key in ("object_a", "object_b"):
            obj = r[obj_key]
            if obj["symbol"] in seen:
                continue
            seen.add(obj["symbol"])
            if obj["hamming_weight"] == 8:
                sym = obj["symbol"]
                el = ed.get(sym)
                print(f"      {sym}  (Z={el['Z']}, {el['category']}, "
                      f"valence={el['val']})  Hex={obj['hex_symbols_raw']}")

    # ─── 6. PER-BIT SKEW DISTRIBUTION (rule 1) ───────────────────────────────
    print("\n[6] PER-BIT SKEW (Rule 1: weight-as-polygon)")
    print("    Which bit positions are most often ON across all elements?")
    bit_on_counts = [0] * 24
    seen = set()
    for r in results:
        for obj_key in ("object_a", "object_b"):
            obj = r[obj_key]
            if obj["symbol"] in seen:
                continue
            seen.add(obj["symbol"])
            for i, bit in enumerate(obj["bits24"]):
                if bit == 1:
                    bit_on_counts[i] += 1
    n_elements = len(seen)
    print(f"    Across {n_elements} elements:")
    print(f"    {'Bit':>3} {'Row':<12} {'Count':>5} {'Pct':>5}  Bar")
    for i, cnt in enumerate(bit_on_counts):
        row_name = ROW_NAMES[i // 6]
        pct = 100.0 * cnt / n_elements
        bar = "█" * int(pct / 5)
        print(f"    {i:>3} {row_name:<12} {cnt:>5} {pct:>5.1f}  {bar}")

    # ─── 7. SUMMARY OF EMERGENT OBSERVATIONS ────────────────────────────────
    print("\n" + "=" * 78)
    print("EMERGENT OBSERVATIONS")
    print("=" * 78)
    print("""
    1. OCTAD CLASS CLUSTERING: H, He, Ne, Ar all sit at Hamming weight 8
       (the Octad lattice weight in UBP terms). This is the most "coherent"
       class in the Golay code. The only non-noble here is H — also the
       simplest element. Suggests HW=8 is the "minimal stable identity".

    2. SYNDROME WEIGHT IS 4 FOR MOST OCTAD-CLASS ELEMENTS: a near-constant
       4-bit syndrome distance from a true Golay codeword. The "engine" of
       UBP would need to snap these by 4 bits to reach perfect coherence.
       H, He, Ne, Ar all share this. Worth investigating further.

    3. XOR HAMMING WEIGHT: tracks element-class difference more than bond
       energy. Pairs of similar-class elements (H+Cl, both small nonmetal)
       have LOW XOR (~12). Pairs of dissimilar (Na+Cl, Li+F, H+F) have HIGH
       XOR (15-16). C+O is anomalous — both nonmetals but XOR=13.

    4. HEXACODE SHADOWS: NO TWO ELEMENTS SHARE THE SAME 6-SYMBOL SHADOW.
       Even He/Ne/Ar (all noble gases) have completely different shadows.
       Maximum agreement between any two elements is 3/6 (Li+F). This is
       the "grammatical distance" of the system.

    5. NOBLE GASES HAVE ZERO ENCODING IN ROW 2 (Activation/EN): because
       Pauling EN is undefined (set to 0) for noble gases. Their row 2 is
       000000. This makes them 'information sparse' in the activation
       channel — possibly why they're chemically inert in this model.

    6. THE BIT-POSITION HEATMAP: Bit 23 (MSB of valence row) is OFF in
       every element we tested. Valence never exceeds 8 = 0b1000, so the
       high bits of the valence row are always 0. The encoding has slack.

    7. BIT 17 IS ON IN EVERY NOBLE GAS: position 17 is row 3 (Potential)
       col 5, the MSB of the redundant valence encoding. All noble gases
       have valence=8, which gray-codes with bit 17 set. Worth noting.

    Next steps to consider:
       - Try a different encoding (e.g., Z+shells) to see if Octad
         clustering persists or breaks
       - Build a "Golay-codeword version" of each element (after snap)
         and see if it matches another real element
       - Compute MOG-grid skew on the SNAPPED codeword vs the raw bits
       - Try treating Data Object A and B as a spatial scene with
         build_expression([A, '+', B]) and observe result
    """)


if __name__ == "__main__":
    main()
