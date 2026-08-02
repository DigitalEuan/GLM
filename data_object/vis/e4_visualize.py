"""
Visualize the E4 balance study results.

Produces:
  - e4_encoding_rankings.png : bar chart of |r| for each metric × encoding
  - e4_d_geometric_scatter.png : scatter of scn_overlap vs bond_energy for the winning encoding
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
import golay_mog_investigation as inv
from e4_balance_study import ENCODINGS, encode_with_props, prop_to_6bit
from e1_e2_e3_kb_sweep import interaction_metrics, KNOWN_PAIRS

OUT_DIR = Path("/home/z/my-project/download")


def plot_encoding_rankings(summary_path):
    with open(summary_path) as f:
        data = json.load(f)
    summary = data["summary"]

    # Metrics to plot
    be_metrics = ["be_r_xor_hamming_weight", "be_r_hex_disagreements",
                  "be_r_scn_overlap_count", "be_r_nat_sum"]
    dh_metrics = ["dh_r_xor_hamming_weight", "dh_r_hex_disagreements",
                  "dh_r_scn_overlap_count", "dh_r_nat_sum"]
    metric_labels = ["XOR HW", "Hex Disagr", "Scn Overlap", "Nat Sum"]

    encodings = [s["encoding"] for s in summary]
    n_enc = len(encodings)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), constrained_layout=True)

    for ax, metrics, title in [(axes[0], be_metrics, "Bond Energy (n=37)"),
                                (axes[1], dh_metrics, "ΔH Formation (n=30)")]:
        x = np.arange(n_enc)
        width = 0.2
        for i, (m, lbl) in enumerate(zip(metrics, metric_labels)):
            vals = [abs(s.get(m, 0)) for s in summary]
            ax.bar(x + (i - 1.5) * width, vals, width, label=lbl)
        ax.set_xticks(x)
        ax.set_xticklabels(encodings, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("|Pearson r|")
        ax.set_title(title)
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        ax.set_ylim(0, 0.55)

    fig.suptitle("E4 Encoding Balance Study — |r| by encoding × metric\n"
                 "Higher = stronger correlation. Winner for BE: D_geometric (scn_overlap = 0.46)",
                 fontsize=12, fontweight="bold")
    out = OUT_DIR / "e4_encoding_rankings.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


def plot_winning_scatter():
    """Scatter of scn_overlap_count vs bond_energy for D_geometric encoding."""
    prop_set = ["Z", "Rad", "EN", "Valence_e"]
    pairs_data = []
    for sym_a, sym_b, be, dh, label in KNOWN_PAIRS:
        vec_a = encode_with_props(sym_a, prop_set)
        vec_b = encode_with_props(sym_b, prop_set)
        m = interaction_metrics(vec_a, vec_b)
        m["pair"] = f"{sym_a}+{sym_b}"
        m["label"] = label
        m["be"] = be
        m["dh"] = dh
        pairs_data.append(m)

    be_vals = [p["be"] for p in pairs_data]
    scn_vals = [p["scn_overlap_count"] for p in pairs_data]

    r_corr = statistics.correlation(scn_vals, be_vals)

    fig, ax = plt.subplots(figsize=(10, 7), constrained_layout=True)
    ax.scatter(scn_vals, be_vals, c="tab:blue", s=70, edgecolor="black", alpha=0.8)
    for p in pairs_data:
        ax.annotate(p["pair"], (p["scn_overlap_count"], p["be"]),
                    fontsize=8, xytext=(5, 3), textcoords="offset points")

    # Linear fit
    z = np.polyfit(scn_vals, be_vals, 1)
    xs = np.linspace(min(scn_vals) - 1, max(scn_vals) + 1, 50)
    ax.plot(xs, np.polyval(z, xs), "r--", alpha=0.6, label=f"linear fit")

    ax.set_xlabel("Scene overlap count (active-bit cell bounding-sphere overlap)", fontsize=10)
    ax.set_ylabel("Bond energy (kJ/mol)", fontsize=10)
    ax.set_title(f"Winning encoding: D_geometric (Z, Rad, EN, Valence_e)\n"
                 f"scn_overlap vs Bond Energy: r = {r_corr:+.4f} (n={len(pairs_data)})",
                 fontsize=11, fontweight="bold")
    ax.grid(alpha=0.3)
    ax.legend()

    out = OUT_DIR / "e4_d_geometric_scatter.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


def main():
    print("=" * 72)
    print("E4 VISUALIZATIONS")
    print("=" * 72)
    plot_encoding_rankings(OUT_DIR / "e4_balance_study.json")
    plot_winning_scatter()


if __name__ == "__main__":
    main()
