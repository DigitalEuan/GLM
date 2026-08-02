"""
Generate visualizations for the Golay MOG Data Object investigation.

Outputs (saved to /home/z/my-project/download/):
  1. mog_grids.png          — 4x6 MOG grid for each element (10 elements)
  2. bit_skew_bars.png      — per-bit skew (rule 1) for each element
  3. interaction_correlations.png  — scatter of metrics vs bond energy
  4. hexacode_shadows.png   — 6-symbol Hexacode shadow per element
  5. pair_interaction_heatmap.png  — pairwise metric heatmap
"""

from __future__ import annotations

import sys
import json
import math
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np

# Register fonts for clean rendering
try:
    fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
except Exception:
    pass
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import golay_mog_investigation as inv
import element_data as ed


OUT_DIR = Path("/home/z/my-project/download")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ALL_ELEMENTS = ["H", "He", "Li", "C", "O", "F", "Ne", "Na", "Cl", "Ar", "Fe"]
ROW_NAMES = inv.ROW_NAMES


# ──────────────────────────────────────────────────────────────────────────────
# 1. MOG grids for all elements
# ──────────────────────────────────────────────────────────────────────────────
def plot_mog_grids():
    fig, axes = plt.subplots(3, 4, figsize=(16, 10), constrained_layout=True)
    axes = axes.flatten()

    for idx, sym in enumerate(ALL_ELEMENTS):
        ax = axes[idx]
        obj = inv.encode_data_object(sym)
        grid = np.array(obj["mog_grid"])  # 4x6
        # Display with row labels
        ax.imshow(grid, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(6))
        ax.set_xticklabels([f"c{i}" for i in range(6)], fontsize=8)
        ax.set_yticks(range(4))
        ax.set_yticklabels([f"{ROW_NAMES[r][:3]}" for r in range(4)], fontsize=9)
        # Annotate cells
        for r in range(4):
            for c in range(6):
                if grid[r, c] == 1:
                    ax.text(c, r, "1", ha="center", va="center",
                            color="white", fontsize=11, fontweight="bold")
                else:
                    ax.text(c, r, "0", ha="center", va="center",
                            color="gray", fontsize=9)
        # Title with key stats
        hw = obj["hamming_weight"]
        sw = obj["syndrome_weight"]
        hex_str = "".join(str(h) for h in obj["hex_symbols_raw"])
        ax.set_title(f"{sym}  (Z={obj['element']['Z']}, HW={hw}, SW={sw})\n"
                     f"Hex: ({hex_str})", fontsize=10)
        # Hex symbols below grid
        for c in range(6):
            ax.text(c, 4.2, str(obj["hex_symbols_raw"][c]),
                    ha="center", va="center", fontsize=9, color="darkred",
                    fontweight="bold")
        ax.set_ylim(-0.5, 4.7)

    # Hide unused subplot
    for idx in range(len(ALL_ELEMENTS), len(axes)):
        axes[idx].axis("off")

    fig.suptitle("Golay MOG Data Objects — 4×6 Grid per Element\n"
                 "(row 0=Reality/Z, 1=Info/mass, 2=Activation/EN, 3=Potential/valence)",
                 fontsize=12, fontweight="bold")
    out = OUT_DIR / "mog_grids.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


# ──────────────────────────────────────────────────────────────────────────────
# 2. Bit-skew bar chart (rule 1: weight-as-polygon)
# ──────────────────────────────────────────────────────────────────────────────
def plot_bit_skew_bars():
    fig, axes = plt.subplots(3, 4, figsize=(16, 10), constrained_layout=True)
    axes = axes.flatten()

    for idx, sym in enumerate(ALL_ELEMENTS):
        ax = axes[idx]
        obj = inv.full_object_report(sym)
        per_bit = obj["skew_rule_1_weight_as_polygon"]["per_bit"]

        bit_indices = list(range(24))
        skew_mags = [b["skew_magnitude"] for b in per_bit]
        colors = ["#1f77b4" if b["on"] else "#dddddd" for b in per_bit]

        ax.bar(bit_indices, skew_mags, color=colors, edgecolor="black", linewidth=0.5)
        ax.set_xlim(-0.5, 23.5)
        ax.set_xticks([0, 6, 12, 18, 23])
        ax.set_title(f"{sym} (HW={obj['hamming_weight']})", fontsize=10)
        ax.set_ylabel("skew magnitude", fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    for idx in range(len(ALL_ELEMENTS), len(axes)):
        axes[idx].axis("off")

    fig.suptitle("Per-bit Spatial Skew (Rule 1: weight-as-polygon)\n"
                 "Blue = bit ON, gray = bit OFF. Higher bit positions → larger polygons → larger skew.",
                 fontsize=12, fontweight="bold")
    out = OUT_DIR / "bit_skew_bars.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


# ──────────────────────────────────────────────────────────────────────────────
# 3. Interaction correlations — does any metric correlate with bond energy?
# ──────────────────────────────────────────────────────────────────────────────
def plot_interaction_correlations(results: list):
    """results = list of pair reports (from JSON-loaded data)."""
    pairs = []
    bond_energies = []
    deltas_h = []
    xor_hws = []
    xor_sws = []
    hex_agrs = []
    hex_dises = []
    scn_means = []
    scn_overlaps = []
    r_ratios = []

    for r in results:
        a, b = r["pair"]
        known = r["known_chemistry"]
        be = known.get("bond_energy_kJ")
        dh = known.get("deltaH_form_kJ")
        if be is None or be == 0:
            continue  # skip inert pairs for the correlation analysis
        gx = r["interactions"]["golay_xor_snap"]
        hx = r["interactions"]["hexacode_shadow_diff"]
        sx = r["interactions"]["spatial_scene_merge"]
        ax = r["interactions"]["spatial_arithmetic_op"]
        pairs.append(f"{a}+{b}")
        bond_energies.append(be)
        deltas_h.append(dh if dh is not None else 0)
        xor_hws.append(gx["xor_hamming_weight"])
        xor_sws.append(gx["xor_syndrome_weight"])
        hex_agrs.append(hx["agreements"])
        hex_dises.append(hx["disagreements"])
        scn_means.append(sx.get("mean_distance") or 0)
        scn_overlaps.append(sx.get("overlap_count", 0))
        r_ratios.append(ax.get("radius_ratio", 0))

    n = len(pairs)
    if n == 0:
        print("  Skipping correlation plot — no reactive pairs.")
        return

    fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    axes = axes.flatten()

    metrics = [
        ("XOR Hamming weight", xor_hws, "tab:blue"),
        ("XOR syndrome weight", xor_sws, "tab:orange"),
        ("Hexacode agreements", hex_agrs, "tab:green"),
        ("Scene mean distance", scn_means, "tab:red"),
        ("Scene overlap count", scn_overlaps, "tab:purple"),
        ("Radius ratio (A/B)", r_ratios, "tab:brown"),
    ]

    for idx, (name, vals, color) in enumerate(metrics):
        ax = axes[idx]
        ax.scatter(vals, bond_energies, c=color, s=80, edgecolor="black", alpha=0.8)
        # Annotate points
        for i, lbl in enumerate(pairs):
            ax.annotate(lbl, (vals[i], bond_energies[i]),
                        fontsize=8, xytext=(5, 5), textcoords="offset points")
        ax.set_xlabel(name, fontsize=9)
        ax.set_ylabel("Bond energy (kJ/mol)", fontsize=9)
        ax.set_title(f"{name} vs Bond Energy", fontsize=10)
        ax.grid(alpha=0.3)
        # Compute Pearson correlation
        if len(vals) > 1:
            try:
                r_corr = np.corrcoef(vals, bond_energies)[0, 1]
                ax.text(0.05, 0.95, f"r = {r_corr:+.3f}",
                        transform=ax.transAxes, fontsize=10,
                        verticalalignment="top",
                        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7))
            except Exception:
                pass

    fig.suptitle("Interaction Metrics vs Known Bond Energy (reactive pairs only)",
                 fontsize=13, fontweight="bold")
    out = OUT_DIR / "interaction_correlations.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


# ──────────────────────────────────────────────────────────────────────────────
# 4. Hexacode shadows — visual grid
# ──────────────────────────────────────────────────────────────────────────────
def plot_hexacode_shadows():
    fig, ax = plt.subplots(figsize=(14, 5), constrained_layout=True)

    elements = ALL_ELEMENTS
    n = len(elements)
    # 6 GF(4) symbols per element, displayed as colored cells
    # GF(4): 0=white, 1=light blue, 2=medium blue, 3=dark blue
    cmap_colors = ["#ffffff", "#aec7e8", "#1f77b4", "#08306b"]
    grid = np.zeros((n, 6, 3))
    for i, sym in enumerate(elements):
        obj = inv.encode_data_object(sym)
        for j, h in enumerate(obj["hex_symbols_raw"]):
            hexcolor = cmap_colors[h]
            r = int(hexcolor[1:3], 16) / 255
            g = int(hexcolor[3:5], 16) / 255
            b = int(hexcolor[5:7], 16) / 255
            grid[i, j] = [r, g, b]

    # Display
    ax.imshow(grid, aspect="auto")
    ax.set_xticks(range(6))
    ax.set_xticklabels([f"col {i}" for i in range(6)], fontsize=10)
    ax.set_yticks(range(n))
    ax.set_yticklabels([f"{sym} (Z={ed.get(sym)['Z']})" for sym in elements], fontsize=10)

    # Annotate
    for i, sym in enumerate(elements):
        obj = inv.encode_data_object(sym)
        for j, h in enumerate(obj["hex_symbols_raw"]):
            color = "white" if h in (2, 3) else "black"
            symbol_str = ["0", "1", "ω", "ω²"][h]
            ax.text(j, i, symbol_str, ha="center", va="center",
                    color=color, fontsize=12, fontweight="bold")

    ax.set_title("Hexacode Shadow of each element's Data Object\n"
                 "(GF(4) symbols: 0, 1, ω, ω² — derived from MOG column decomposition)",
                 fontsize=12, fontweight="bold")
    out = OUT_DIR / "hexacode_shadows.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


# ──────────────────────────────────────────────────────────────────────────────
# 5. Pairwise interaction heatmap
# ──────────────────────────────────────────────────────────────────────────────
def plot_pair_heatmap(results: list):
    """Heatmap of XOR Hamming weight across all element pairs."""
    elements = ALL_ELEMENTS
    n = len(elements)

    # Build lookup of pair -> metric
    pair_lookup = {}
    for r in results:
        a, b = r["pair"]
        gx = r["interactions"]["golay_xor_snap"]
        hx = r["interactions"]["hexacode_shadow_diff"]
        pair_lookup[(a, b)] = {
            "xor_hw": gx["xor_hamming_weight"],
            "xor_sw": gx["xor_syndrome_weight"],
            "hex_dis": hx["disagreements"],
            "hex_agr": hx["agreements"],
        }

    # Build full symmetric matrix (compute missing pairs on the fly)
    def get_metric(a, b, key):
        if (a, b) in pair_lookup:
            return pair_lookup[(a, b)][key]
        if (b, a) in pair_lookup:
            return pair_lookup[(b, a)][key]
        # Compute on the fly
        rep = inv.full_pair_report(a, b)
        gx = rep["interactions"]["golay_xor_snap"]
        hx = rep["interactions"]["hexacode_shadow_diff"]
        val = {
            "xor_hw": gx["xor_hamming_weight"],
            "xor_sw": gx["xor_syndrome_weight"],
            "hex_dis": hx["disagreements"],
            "hex_agr": hx["agreements"],
        }
        pair_lookup[(a, b)] = val
        return val[key]

    metrics_to_plot = [
        ("xor_hw", "XOR Hamming Weight\n(how many bits differ)"),
        ("xor_sw", "XOR Syndrome Weight\n(Golay 'distance from codeword')"),
        ("hex_dis", "Hexacode Disagreements\n(grammar mismatch)"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), constrained_layout=True)

    for ax, (key, title) in zip(axes, metrics_to_plot):
        matrix = np.zeros((n, n), dtype=int)
        for i, a in enumerate(elements):
            for j, b in enumerate(elements):
                matrix[i, j] = get_metric(a, b, key)
        im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")
        ax.set_xticks(range(n))
        ax.set_xticklabels(elements, fontsize=9)
        ax.set_yticks(range(n))
        ax.set_yticklabels(elements, fontsize=9)
        ax.set_title(title, fontsize=10)
        # Annotate cells
        for i in range(n):
            for j in range(n):
                val = matrix[i, j]
                color = "white" if val > matrix.max() * 0.6 else "black"
                ax.text(j, i, str(val), ha="center", va="center",
                        color=color, fontsize=8)
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    fig.suptitle("Pairwise Interaction Metrics across all Elements",
                 fontsize=13, fontweight="bold")
    out = OUT_DIR / "pair_interaction_heatmap.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


# ──────────────────────────────────────────────────────────────────────────────
# 6. MOG grid scene (rule 3) — visualize the 4x6 spatial scene for one element
# ──────────────────────────────────────────────────────────────────────────────
def plot_mog_grid_spatial_scene():
    """Show the 4x6 spatial grid scene (rule 3) for a few representative elements."""
    elements_to_show = ["H", "C", "O", "Na", "Cl", "Fe"]
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    axes = axes.flatten()

    for idx, sym in enumerate(elements_to_show):
        ax = axes[idx]
        obj = inv.encode_data_object(sym)
        scene = inv.skew_rule_mog_grid_scene(obj["bits24"])
        cells = scene["cells"]

        # Plot each cell as a small polygon at its centroid position
        for cell in cells:
            cx, cy, _ = cell["centroid"]
            color = "#1f77b4" if cell["on"] else "#dddddd"
            size = 80 if cell["on"] else 30
            ax.scatter(cx, cy, c=color, s=size, edgecolor="black",
                       linewidth=1.2, marker="s" if cell["on"] else ".")
            # Label active bits with their position
            if cell["on"]:
                ax.annotate(f"b{cell['bit']}", (cx, cy),
                            fontsize=7, ha="center", va="center",
                            color="white", fontweight="bold")

        # Mark grid centroid
        gx, gy, _ = scene["grid_centroid"]
        ax.scatter(gx, gy, c="red", s=120, marker="x", linewidth=2)

        # Mark active centroid
        ax_centroid = scene["active_centroid"]
        ax.scatter(ax_centroid[0], ax_centroid[1], c="green", s=120, marker="*",
                   linewidth=1.5, label="active centroid")

        # Draw line from grid centroid to active centroid
        ax.plot([gx, ax_centroid[0]], [gy, ax_centroid[1]],
                "g--", linewidth=1.5, alpha=0.6)

        offset = scene["active_offset_from_grid_centroid"]
        ax.set_title(f"{sym}  (HW={scene['n_active']}, offset={offset:.2f})",
                     fontsize=10)
        ax.set_aspect("equal")
        ax.grid(alpha=0.3)
        ax.set_xlabel("X (cols 0-5)", fontsize=8)
        ax.set_ylabel("Y (rows 0-3)", fontsize=8)

    fig.suptitle("Rule 3: MOG Grid Spatial Scene\n"
                 "Red X = grid centroid, Green * = active-bit centroid (offset = 'skew')",
                 fontsize=12, fontweight="bold")
    out = OUT_DIR / "mog_grid_spatial_scene.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 72)
    print("GENERATING VISUALIZATIONS")
    print("=" * 72)

    print("\n[1/6] MOG grids for all elements...")
    plot_mog_grids()

    print("\n[2/6] Bit-skew bar charts (rule 1)...")
    plot_bit_skew_bars()

    print("\n[3/6] Hexacode shadows...")
    plot_hexacode_shadows()

    print("\n[4/6] MOG grid spatial scenes (rule 3)...")
    plot_mog_grid_spatial_scene()

    # Load results JSON for correlation plots
    print("\n[5/6] Interaction correlations (vs bond energy)...")
    results_path = OUT_DIR / "golay_mog_results.json"
    if results_path.exists():
        with open(results_path) as f:
            results = json.load(f)
        plot_interaction_correlations(results)
    else:
        print(f"  Skipping — no results file at {results_path}")

    print("\n[6/6] Pairwise interaction heatmap...")
    plot_pair_heatmap([])  # passes empty list; function computes on the fly

    print("\n" + "=" * 72)
    print("ALL VISUALIZATIONS GENERATED")
    print("=" * 72)


if __name__ == "__main__":
    main()
