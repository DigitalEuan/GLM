"""
Visualize the E5 wide-search top correlations.

Produces:
  - e5_top_correlations_scatter.png : 6 scatter plots of the top correlations
  - e5_scheme_comparison.png        : bar chart of best |r| per scheme × target
  - e5_d_classB_constellation.png   : visualization of the D_classB Leech constellation
                                       for several elements (showing why intra_b correlates)
"""

from __future__ import annotations

import sys
import json
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np

try:
    fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
except Exception:
    pass
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import ubp_kb_loader as kb
import per_bit_leech as pbl
from e1_e2_e3_kb_sweep import KNOWN_PAIRS

OUT_DIR = Path("/home/z/my-project/download")


def load_results():
    with open(OUT_DIR / "e5_per_bit_leech_wide_search.json") as f:
        data = json.load(f)
    return data


def plot_top_correlations(data):
    """Plot scatter of top 6 correlations."""
    summary = data["summary_rows"]
    # Take top 6 by |r|
    top = sorted(summary, key=lambda x: -abs(x["r"]))[:6]

    fig, axes = plt.subplots(2, 3, figsize=(18, 10), constrained_layout=True)
    axes = axes.flatten()

    for idx, row in enumerate(top):
        ax = axes[idx]
        scheme = row["scheme"]
        metric = row["metric"]
        target = row["target"]
        r_val = row["r"]

        # Get the actual data
        records = data["all_results"][scheme]
        if target == "dH":
            records = [r for r in records if r["delta_H_kJ"] is not None and r["delta_H_kJ"] != 0]
            y_vals = [r["delta_H_kJ"] for r in records]
        else:
            y_vals = [r["bond_energy_kJ"] for r in records]
        x_vals = [r[metric] for r in records]
        labels = [f"{r['pair'][0]}+{r['pair'][1]}" for r in records]

        ax.scatter(x_vals, y_vals, c="tab:blue", s=70, edgecolor="black", alpha=0.8)
        for i, lbl in enumerate(labels):
            ax.annotate(lbl, (x_vals[i], y_vals[i]),
                        fontsize=7, xytext=(4, 3), textcoords="offset points")

        # Linear fit
        if len(x_vals) > 1:
            z = np.polyfit(x_vals, y_vals, 1)
            xs = np.linspace(min(x_vals), max(x_vals), 50)
            ax.plot(xs, np.polyval(z, xs), "r--", alpha=0.6)

        ax.set_xlabel(metric, fontsize=9)
        ax.set_ylabel(f"{target} (kJ/mol)", fontsize=9)
        ax.set_title(f"{scheme} | {metric[:35]}\n"
                     f"r = {r_val:+.4f} (n={len(records)})",
                     fontsize=10, fontweight="bold")
        ax.grid(alpha=0.3)

    fig.suptitle("E5 Wide Search — Top 6 Per-Bit Leech Correlations",
                 fontsize=13, fontweight="bold")
    out = OUT_DIR / "e5_top_correlations_scatter.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


def plot_scheme_comparison(data):
    """Bar chart of best |r| per scheme × target."""
    summary = data["summary_rows"]
    schemes = ["A_basis", "B_classA", "C_classC", "D_classB"]
    targets = ["BE", "dH"]

    # Find best |r| per (scheme, target)
    best = {}
    for s in schemes:
        for t in targets:
            matching = [r for r in summary if r["scheme"] == s and r["target"] == t]
            if matching:
                best[(s, t)] = max(matching, key=lambda x: abs(x["r"]))

    fig, ax = plt.subplots(figsize=(12, 6), constrained_layout=True)
    x = np.arange(len(schemes))
    width = 0.35
    be_vals = [abs(best.get((s, "BE"), {"r": 0})["r"]) for s in schemes]
    dh_vals = [abs(best.get((s, "dH"), {"r": 0})["r"]) for s in schemes]

    bars1 = ax.bar(x - width/2, be_vals, width, label="Bond Energy", color="tab:blue")
    bars2 = ax.bar(x + width/2, dh_vals, width, label="ΔH Formation", color="tab:orange")

    # Annotate bars with r value
    for i, (be, dh) in enumerate(zip(be_vals, dh_vals)):
        if be > 0:
            ax.text(i - width/2, be + 0.01, f"r={be:.3f}", ha="center", fontsize=9)
        if dh > 0:
            ax.text(i + width/2, dh + 0.01, f"r={dh:.3f}", ha="center", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(schemes, fontsize=10)
    ax.set_ylabel("Best |Pearson r|", fontsize=11)
    ax.set_title("E5 — Best correlation per scheme × target\n"
                 "(wider = more signal in that scheme/target combination)",
                 fontsize=12, fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, 0.55)

    # Add a horizontal line at r=0.30 (weak signal threshold)
    ax.axhline(0.30, color="red", linestyle=":", alpha=0.5, label="r=0.30 threshold")

    out = OUT_DIR / "e5_scheme_comparison.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


def plot_d_classB_constellation():
    """Visualize the D_classB Leech constellation for several elements.

    For each element, project the 24 per-bit Leech points (each 24D) down to 2D
    using the first two coordinates, and plot them. Show how the constellation
    shape varies across elements.
    """
    elements_to_show = ["H", "He", "C", "O", "Na", "Cl", "Fe", "Ne"]
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), constrained_layout=True)
    axes = axes.flatten()

    for idx, sym in enumerate(elements_to_show):
        ax = axes[idx]
        e = kb.get_element(sym)
        if e is None:
            continue
        bits = e.vector24
        pts = pbl.encode_bits_to_leech(bits, "D_classB")

        # Project to 2D using first two coordinates
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        colors = ["tab:blue" if b else "lightgray" for b in bits]

        ax.scatter(xs, ys, c=colors, s=80, edgecolor="black", linewidth=1)
        for i, (x, y) in enumerate(zip(xs, ys)):
            if bits[i]:
                ax.annotate(f"b{i}", (x, y), fontsize=7,
                            ha="center", va="center", color="white", fontweight="bold")

        # Compute centroid and RMS
        cx = sum(xs) / 24
        cy = sum(ys) / 24
        ax.scatter(cx, cy, c="red", s=120, marker="x", linewidth=2)

        # RMS spread (in 2D projection)
        rms = (sum((x-cx)**2 + (y-cy)**2 for x, y in zip(xs, ys)) / 24) ** 0.5
        ax.set_title(f"{sym} (HW={sum(bits)})\n2D proj RMS={rms:.2f}", fontsize=10)
        ax.set_aspect("equal")
        ax.grid(alpha=0.3)
        ax.set_xlabel("coord[0]", fontsize=8)
        ax.set_ylabel("coord[1]", fontsize=8)

    fig.suptitle("E5 — D_classB Leech Constellation per Element (2D projection)\n"
                 "Red X = centroid. Blue dots = active bits, gray = inactive.",
                 fontsize=12, fontweight="bold")
    out = OUT_DIR / "e5_d_classB_constellation.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


def main():
    print("=" * 72)
    print("E5 VISUALIZATIONS")
    print("=" * 72)
    data = load_results()
    plot_top_correlations(data)
    plot_scheme_comparison(data)
    plot_d_classB_constellation()


if __name__ == "__main__":
    main()
