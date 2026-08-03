"""
Run the full multi-pair element sweep and save all results to JSON.

For each pair in SWEEP_PAIRS:
  - Encode both elements as 24-bit Data Objects
  - Apply all 3 skew rules to each object
  - Apply all 4 interaction metrics to the pair
  - Tag with known chemistry data (bond energy, ΔH formation)

Output: /home/z/my-project/download/golay_mog_results.json
"""

from __future__ import annotations

import sys
import json
import time
from pathlib import Path
from fractions import Fraction

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import golay_mog_investigation as inv
import element_data as ed


def fraction_to_str(obj):
    """Recursively convert Fraction objects to strings for JSON serialization."""
    if isinstance(obj, Fraction):
        return str(obj)
    if isinstance(obj, dict):
        return {k: fraction_to_str(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [fraction_to_str(x) for x in obj]
    if isinstance(obj, tuple):
        return [fraction_to_str(x) for x in obj]
    return obj


def main():
    print("=" * 72)
    print("GOLAY MOG DATA OBJECT INVESTIGATION — MULTI-PAIR SWEEP")
    print("=" * 72)
    print()

    # The 10 pairs we'll sweep
    pairs = [
        ("He", "Ne"),  # inert control 1
        ("He", "Ar"),  # inert control 2
        ("Na", "Cl"),  # canonical ionic
        ("Li", "F"),   # extreme ionic
        ("C",  "O"),   # covalent combustion
        ("H",  "O"),   # polar covalent water
        ("H",  "F"),   # strongest simple H-X bond
        ("Fe", "O"),   # redox / oxidation
        ("C",  "H"),   # organic backbone
        ("H",  "Cl"),  # acid
    ]

    print(f"Sweeping {len(pairs)} element pairs...")
    print()

    all_results = []
    for i, (a, b) in enumerate(pairs, 1):
        t0 = time.time()
        print(f"[{i:2d}/{len(pairs)}] {a} + {b}  ", end="", flush=True)
        rep = inv.full_pair_report(a, b)
        rep["computed_at"] = time.time()
        rep["compute_time_s"] = time.time() - t0
        all_results.append(rep)
        known = rep["known_chemistry"]
        be = known.get("bond_energy_kJ", "?")
        dh = known.get("deltaH_form_kJ", "?")
        print(f"  bondE={be} kJ/mol  ΔH={dh}  ({rep['compute_time_s']:.2f}s)")

    print()
    print("=" * 72)
    print("SWEEP COMPLETE — building summary tables")
    print("=" * 72)

    # Build a compact summary table for visual inspection
    print()
    print("── Per-object summary (Hamming weight, syndrome weight, NRCI, Hexacode) ──")
    print(f"{'Sym':<5} {'HW':>3} {'SW':>3} {'NRCI':>7} {'Hex shadow':<26} {'Lattice class':<14}")
    seen = set()
    for r in all_results:
        for obj_key in ("object_a", "object_b"):
            obj = r[obj_key]
            if obj["symbol"] in seen:
                continue
            seen.add(obj["symbol"])
            hex_str = "(" + ",".join(str(h) for h in obj["hex_symbols_raw"]) + ")"
            # Determine lattice class
            hw = obj["hamming_weight"]
            if hw == 0: lattice = "Identity"
            elif hw == 8: lattice = "Octad"
            elif hw == 12: lattice = "Dodecad"
            elif hw == 16: lattice = "Hexadecad"
            elif hw == 24: lattice = "Universe"
            else: lattice = f"Off-Lattice(w={hw})"
            print(f"{obj['symbol']:<5} {hw:>3} {obj['syndrome_weight']:>3} "
                  f"{float(obj['nrci_raw']):>7.4f} {hex_str:<26} {lattice:<14}")

    print()
    print("── Per-pair interaction summary ──")
    print(f"{'Pair':<10} {'BondE':>6} {'ΔH':>6} │ "
          f"{'XOR_HW':>6} {'XOR_SW':>6} {'HexΔ':>5} {'HexAgr':>6} │ "
          f"{'ScnMin':>7} {'ScnMean':>7} {'Overlap':>7} │ "
          f"{'R_ratio':>7} {'Add_ok':>6}")
    for r in all_results:
        a, b = r["pair"]
        known = r["known_chemistry"]
        be = known.get("bond_energy_kJ") or 0
        dh = known.get("deltaH_form_kJ") or 0

        gx = r["interactions"]["golay_xor_snap"]
        hx = r["interactions"]["hexacode_shadow_diff"]
        sx = r["interactions"]["spatial_scene_merge"]
        ax = r["interactions"]["spatial_arithmetic_op"]

        xor_hw = gx["xor_hamming_weight"]
        xor_sw = gx["xor_syndrome_weight"]
        hex_agr = hx["agreements"]
        hex_dis = hx["disagreements"]

        scn_min = sx.get("min_distance") or 0
        scn_mean = sx.get("mean_distance") or 0
        overlap = sx.get("overlap_count", 0)

        r_ratio = ax.get("radius_ratio", 0)
        add_ok = "yes" if ax.get("add_ok") else "no"

        print(f"{a+'+'+b:<10} {be:>6} {dh:>6} │ "
              f"{xor_hw:>6} {xor_sw:>6} {hex_dis:>5} {hex_agr:>6} │ "
              f"{scn_min:>7.2f} {scn_mean:>7.2f} {overlap:>7} │ "
              f"{r_ratio:>7.3f} {add_ok:>6}")

    # Save full JSON
    out_dir = Path("/home/z/my-project/download")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "golay_mog_results.json"
    with open(out_path, "w") as f:
        json.dump(fraction_to_str(all_results), f, indent=2, default=str)
    print()
    print(f"Full results saved to: {out_path}")
    print(f"File size: {out_path.stat().st_size:,} bytes")
    return all_results


if __name__ == "__main__":
    main()
