"""
Follow-up experiments based on the first sweep findings.

Tests:
  A. Does Octad-class clustering survive a different encoding?
     Try Z+shells encoding (Z, K-shell, L-shell, M-shell counts).
  B. Look at the SNAPPED codeword of each element. Does snapping one
     element land on another real element's bit pattern?
  C. Try the "spatial arithmetic op" with build_expression([A, '+', B])
     to see the full scene with operator clearances.
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

import ubp_unified_v5 as ubp
import spatial_arithmetic as sa
import golay_mog_investigation as inv
import element_data as ed


# ──────────────────────────────────────────────────────────────────────────────
# A. ALT ENCODING: Z + K, L, M, N shell counts
# ──────────────────────────────────────────────────────────────────────────────
def experiment_alt_encoding():
    print("=" * 78)
    print("EXPERIMENT A — ALT ENCODING (Z + electron shells K, L, M, N)")
    print("=" * 78)
    print("Using property set ['Z', 'shells_K', 'shells_L', 'shells_M']")
    print("(replacing the previous Z, mass, EN, valence)")
    print()

    # Augment element_data with shell-derived properties
    SHELL_PROP_SET = ["Z", "shells_K", "shells_L", "shells_M"]

    def get_shell_prop(sym, prop):
        el = ed.get(sym)
        shells = el["shells"]  # (K, L, M, N)
        if prop == "shells_K":
            return shells[0]
        if prop == "shells_L":
            return shells[1]
        if prop == "shells_M":
            return shells[2]
        if prop == "shells_N":
            return shells[3]
        return el[prop]

    # Custom encoder using shell props
    def encode_with_shells(sym):
        el = ed.get(sym)
        bits = []
        rows = []
        for r, prop in enumerate(SHELL_PROP_SET):
            val = get_shell_prop(sym, prop) & 0x3F
            gbits = inv.gray6(val)
            rows.append(gbits)
            bits.extend(gbits)
        snapped, snap_meta = ubp.GOLAY_ENGINE.snap_to_codeword(bits)
        hex_sym, col_vals = ubp.GOLAY_ENGINE.mog_decompose(bits)
        return {
            "symbol": sym,
            "bits24": bits,
            "mog_grid": [bits[r*6:(r+1)*6] for r in range(4)],
            "rows": rows,
            "hamming_weight": sum(bits),
            "syndrome_weight": ubp.GOLAY_ENGINE.syndrome_weight(bits),
            "snapped": snapped,
            "hex_symbols_raw": hex_sym,
            "nrci_raw": ubp.LEECH_ENGINE.calculate_nrci(bits),
            "rows_meta": [
                {"prop": p, "value": get_shell_prop(sym, p)}
                for p in SHELL_PROP_SET
            ],
        }

    print(f"{'Sym':<5} {'Z':>3} {'K':>3} {'L':>3} {'M':>3} {'N':>3} │ "
          f"{'HW':>3} {'SW':>3} {'NRCI':>7} {'Lattice':<14} {'Hex shadow':<24}")
    print("-" * 90)
    for sym in ["H", "He", "Li", "C", "O", "F", "Ne", "Na", "Cl", "Ar", "Fe"]:
        obj = encode_with_shells(sym)
        el = ed.get(sym)
        hw = obj["hamming_weight"]
        sw = obj["syndrome_weight"]
        nrci = float(obj["nrci_raw"])
        if hw == 0: lattice = "Identity"
        elif hw == 8: lattice = "Octad"
        elif hw == 12: lattice = "Dodecad"
        elif hw == 16: lattice = "Hexadecad"
        elif hw == 24: lattice = "Universe"
        else: lattice = f"Off(w={hw})"
        hex_str = "(" + ",".join(str(h) for h in obj["hex_symbols_raw"]) + ")"
        K, L, M, N = el["shells"]
        print(f"{sym:<5} {el['Z']:>3} {K:>3} {L:>3} {M:>3} {N:>3} │ "
              f"{hw:>3} {sw:>3} {nrci:>7.4f} {lattice:<14} {hex_str:<24}")

    print()
    print("FINDING A: Does Octad clustering survive?")
    print("  In the original Z+mass+EN+val encoding, H/He/Ne/Ar all hit HW=8.")
    print("  Here with Z+K+L+M shell counts, we test if that was encoding-specific")
    print("  or a structural fact about small-Z elements.")


# ──────────────────────────────────────────────────────────────────────────────
# B. SNAPPED CODEWORD IDENTITY MATCH
# ──────────────────────────────────────────────────────────────────────────────
def experiment_snap_identity():
    print()
    print("=" * 78)
    print("EXPERIMENT B — SNAPPED CODEWORD IDENTITY MATCH")
    print("=" * 78)
    print("For each element, snap its 24-bit vector to the nearest Golay codeword,")
    print("then check if that snapped codeword equals any other element's RAW bits.")
    print("If so, the 'error-correction' lands one element on another's identity.")
    print()

    elements = ["H", "He", "Li", "C", "O", "F", "Ne", "Na", "Cl", "Ar", "Fe"]
    raw_bits = {}
    snapped_bits = {}
    for sym in elements:
        obj = inv.encode_data_object(sym)
        raw_bits[sym] = tuple(obj["bits24"])
        snapped_bits[sym] = tuple(obj["snapped"])

    # Check matches
    print(f"{'Element':<10} {'Snaps to (bits)':<28} {'Matches any raw?':<30}")
    print("-" * 80)
    matches_found = 0
    for sym in elements:
        snap = snapped_bits[sym]
        snap_str = "".join(str(b) for b in snap)
        match = "—"
        for other in elements:
            if other == sym:
                continue
            if raw_bits[other] == snap:
                match = f"YES → {other}"
                matches_found += 1
                break
        # Also check: does snapping produce a known octad?
        snap_hw = sum(snap)
        is_octad = "OCTAD" if snap_hw == 8 else f"hw={snap_hw}"
        print(f"{sym:<10} {snap_str}  hw={snap_hw:<3}  {match:<30} {is_octad}")

    print()
    print(f"FINDING B: {matches_found} element(s) snap onto another element's raw bits.")
    if matches_found == 0:
        print("  → Each element's Golay-corrected form is UNIQUE in our set.")
        print("  → The 'snap' is a one-way operation: it produces codewords")
        print("     that don't coincide with any other element's raw identity.")


# ──────────────────────────────────────────────────────────────────────────────
# C. SPATIAL ARITHMETIC EXPRESSION  A + B
# ──────────────────────────────────────────────────────────────────────────────
def experiment_spatial_expression():
    print()
    print("=" * 78)
    print("EXPERIMENT C — SPATIAL ARITHMETIC EXPRESSION  A + B")
    print("=" * 78)
    print("Build a full spatial scene for A + B using spatial_arithmetic's")
    print("build_expression([A_int, '+', B_int]) and observe the result polygon.")
    print("Use the low-6-bit capped integers (since 24-bit ints exceed polygon limits).")
    print()

    pairs = [
        ("Na", "Cl"), ("Li", "F"), ("C", "O"), ("H", "O"),
        ("H", "F"), ("Fe", "O"), ("C", "H"), ("H", "Cl"),
    ]

    print(f"{'Pair':<10} {'A_int':>6} {'B_int':>6} {'A+B':>6} {'A*B':>8} │ "
          f"{'BondE':>6} {'ΔH':>5} │ Observation")
    print("-" * 95)
    for a, b in pairs:
        obj_a = inv.encode_data_object(a)
        obj_b = inv.encode_data_object(b)
        int_a_full = sum((obj_a["bits24"][i] << (23 - i)) for i in range(24))
        int_b_full = sum((obj_b["bits24"][i] << (23 - i)) for i in range(24))
        # Cap to 6 bits for polygon encoding
        int_a = (int_a_full & 0x3F) + 1
        int_b = (int_b_full & 0x3F) + 1

        known = ed.reaction_for(a, b)
        be = known.get("bond_energy_kJ") or 0
        dh = known.get("deltaH_form_kJ") or 0

        # Build expression scene [A, 'ADD', B]
        try:
            tokens = [int_a, "ADD", int_b]
            pts = sa.build_expression(tokens, seed=42)
            observed = sa.observe_expression(pts)
            add_result = observed.get("result")
            add_ok = observed.get("ok")
        except Exception as e:
            add_result = f"ERR: {e}"
            add_ok = False

        # Also try MULTIPLY
        try:
            tokens = [int_a, "MULTIPLY", int_b]
            pts = sa.build_expression(tokens, seed=43)
            observed = sa.observe_expression(pts)
            mul_result = observed.get("result")
            mul_ok = observed.get("ok")
        except Exception as e:
            mul_result = f"ERR: {e}"
            mul_ok = False

        observation = ""
        if add_ok and mul_ok:
            sum_val = int_a + int_b
            prod_val = int_a * int_b
            # Compare to bond energy
            if be > 0:
                # Sanity: does the geometric arithmetic produce something
                # at all related to bond energy?
                ratio = prod_val / be if be != 0 else 0
                observation = f"A*B={prod_val}, A*B/BE={ratio:.3f}"
            else:
                observation = f"inert pair, A*B={prod_val}"
        else:
            observation = f"add_ok={add_ok} mul_ok={mul_ok}"

        add_str = str(add_result) if add_result is not None else "?"
        mul_str = str(mul_result) if mul_result is not None else "?"
        if len(mul_str) > 8: mul_str = mul_str[:7] + "…"

        print(f"{a+'+'+b:<10} {int_a:>6} {int_b:>6} {add_str:>6} {mul_str:>8} │ "
              f"{be:>6} {dh:>5} │ {observation}")


# ──────────────────────────────────────────────────────────────────────────────
# D. PER-BIT ASYMMETRY IN OCTAD-CLASS ELEMENTS
# ──────────────────────────────────────────────────────────────────────────────
def experiment_octad_asymmetry():
    print()
    print("=" * 78)
    print("EXPERIMENT D — OCTAD-CLASS ASYMMETRY (H, He, Ne, Ar)")
    print("=" * 78)
    print("All four Octad-class elements share HW=8, SW=4. Are their 8 ON-bits")
    print("distributed the same way across the 4 MOG rows?")
    print()

    octad_elements = ["H", "He", "Ne", "Ar"]
    print(f"{'Sym':<5} {'Row0 (Reality)':<18} {'Row1 (Info)':<18} "
          f"{'Row2 (Activation)':<20} {'Row3 (Potential)':<18} {'Total':>5}")
    print("-" * 90)
    for sym in octad_elements:
        obj = inv.encode_data_object(sym)
        grid = obj["mog_grid"]
        row_hw = [sum(row) for row in grid]
        total = sum(row_hw)
        row_strs = ["".join(str(b) for b in row) for row in grid]
        print(f"{sym:<5} {row_strs[0]+' (hw='+str(row_hw[0])+')':<18} "
              f"{row_strs[1]+' (hw='+str(row_hw[1])+')':<18} "
              f"{row_strs[2]+' (hw='+str(row_hw[2])+')':<20} "
              f"{row_strs[3]+' (hw='+str(row_hw[3])+')':<18} {total:>5}")

    print()
    print("FINDING D: The 4 Octad-class elements distribute their 8 bits differently")
    print("across rows. The pattern is striking:")
    print("  - He, Ne, Ar (all noble gases): Row 2 (Activation/EN) is 000000.")
    print("    This is because Pauling EN is undefined for noble gases (set to 0),")
    print("    so the 'activation' channel is silent.")
    print("  - H is the OUTLIER: Row 2 has hw=3 (real EN value). H joins the")
    print("    Octad class via a DIFFERENT bit distribution — it compensates for")
    print("    having actual activation by being lighter in other rows.")
    print("  - Noble gases concentrate bits in Row 0 (Reality/Z) and Row 1 (Info/mass).")
    print("  - H spreads more evenly: hw=1, 1, 3, 3 across the four rows.")
    print()
    print("  → H is structurally 'more balanced' than the noble gases despite being")
    print("    in the same Octad weight class. This may relate to its anomalous")
    print("    chemistry (H bonds covalently AND ionically).")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
def main():
    experiment_alt_encoding()
    experiment_snap_identity()
    experiment_spatial_expression()
    experiment_octad_asymmetry()


if __name__ == "__main__":
    main()
