#!/usr/bin/env python3
"""Generate plots for iteration 8."""

import os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
try:
    fm.fontManager.addfont('/usr/share/fonts/truetype/chinese/NotoSansSC[wght].ttf')
except Exception:
    pass
try:
    fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
except Exception:
    pass
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Noto Sans SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
import numpy as np

DATA = "/home/z/my-project/data"
OUT  = "/home/z/my-project/download/iter8_plots"
os.makedirs(OUT, exist_ok=True)


def plot_f2_combiner_results():
    """Phase 3: F_2 combiner results."""
    with open(f"{DATA}/iter8_f2_combiner.json") as f:
        d = json.load(f)
    results = d["results"]
    tasks = list(results.keys())
    exact_rates = []
    cell_matches = []
    for t in tasks:
        r = results[t]
        if "exact_rate" in r:
            exact_rates.append(r["exact_rate"] * 100)
            cell_matches.append(100)  # toggle gets 100% cell match
        else:
            # reflect_v, translate: use the matches rate
            exact_rates.append(r.get("matches_with_constant_xor_mask_rate", 0) * 100)
            cell_matches.append(0)
    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    x = np.arange(len(tasks))
    w = 0.4
    colors = ["#27ae60", "#c0392b", "#c0392b"]
    ax.bar(x, exact_rates, w, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("exact match rate (%)")
    ax.set_ylim(0, 110)
    ax.set_title("Phase 3: F_2 combiner results\n"
                  "Toggle: 100% via XOR-with-all-ones (coordinatewise op)\n"
                  "Reflect_v, Translate: 0% — they're permutations, not coordinatewise")
    for xi, r in zip(x, exact_rates):
        ax.text(xi, r + 2, f"{r:.0f}%", ha="center", fontsize=10, fontweight="bold")
    ax.axhline(y=100, color="#27ae60", linestyle="--", alpha=0.4)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    # Annotate the development issue
    ax.text(1, 50, "DEVELOPMENT ISSUE:\nsubstrate's combiner.apply_op()\ncannot express permutations",
             ha="center", va="center", fontsize=9, color="#c0392b",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#ffe5e5", edgecolor="#c0392b"))
    ax.text(2, 50, "same issue:\nblock move = permutation",
             ha="center", va="center", fontsize=9, color="#c0392b",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#ffe5e5", edgecolor="#c0392b"))
    fig.savefig(f"{OUT}/f2_combiner_results.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/f2_combiner_results.png")


def plot_dual_snap_results():
    """Phase 2: binary-Leech dual snap results."""
    with open(f"{DATA}/iter8_dual_snap.json") as f:
        d = json.load(f)
    results = d
    tasks = list(results.keys())
    exact_rates = [results[t]["exact_rate"] * 100 for t in tasks]
    cell_matches = [results[t]["mean_cell_match"] * 100 for t in tasks]
    snap_in = [results[t]["snap_in_lambda48_rate"] * 100 for t in tasks]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    x = np.arange(len(tasks))
    w = 0.35
    ax = axes[0]
    ax.bar(x - w/2, exact_rates, w, label="exact match %",
           color="#27ae60", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, cell_matches, w, label="cell match %",
           color="#3498db", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("% accuracy")
    ax.set_ylim(0, 110)
    ax.set_title("Phase 2: binary-Leech dual snap (Λ_48 lift)")
    ax.legend(loc="upper right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for xi, (e, c) in enumerate(zip(exact_rates, cell_matches)):
        ax.text(xi - w/2, e + 2, f"{e:.0f}%", ha="center", fontsize=9, color="#27ae60")
        ax.text(xi + w/2, c + 2, f"{c:.0f}%", ha="center", fontsize=9, color="#3498db")
    # Highlight translate as partial success
    ax.annotate("partial success:\ntranslate 47% exact",
                 xy=(1, exact_rates[1]), xytext=(1.5, 80),
                 fontsize=9, color="#27ae60", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#27ae60"))

    ax = axes[1]
    ax.bar(x, snap_in, 0.5, color="#9b59b6", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("% trials where snap lands in Λ_48")
    ax.set_ylim(0, 110)
    ax.set_title("Snap always lands in Λ_48 (100%)\n"
                  "but the Construction-A snap is too coarse (zero codeword only)")
    ax.axhline(y=100, color="#9b59b6", linestyle="--", alpha=0.5)
    for xi, s in enumerate(snap_in):
        ax.text(xi, s + 2, f"{s:.0f}%", ha="center", fontsize=10, color="#9b59b6", fontweight="bold")
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    fig.suptitle("Iteration 8 Phase 2: binary-Leech dual snap", fontsize=13)
    fig.savefig(f"{OUT}/dual_snap_results.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/dual_snap_results.png")


def plot_junction_results():
    """Phase 1: Junction method results."""
    with open(f"{DATA}/iter8_junction.json") as f:
        d = json.load(f)
    info = d["junctions_info"]
    corr = d["correlation"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)

    # Left: junction distribution
    ax = axes[0]
    labels = ["carriers", "unique coords", "junctions (size≥2)", "singletons"]
    values = [info["n_carriers"], info["n_unique_coords"], info["n_junctions"], info["n_singletons"]]
    colors = ["#3498db", "#9b59b6", "#e67e22", "#7f8c8d"]
    ax.bar(labels, values, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_ylabel("count")
    ax.set_title(f"Phase 1: Junction distribution\n250 binary carriers, 147 unique Leech classes, 17 junctions")
    for xi, v in enumerate(values):
        ax.text(xi, v + 3, str(v), ha="center", fontsize=10, fontweight="bold")
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    # Right: junction-task and junction-parity correlation
    ax = axes[1]
    labels = ["same task", "mixed task", "same parity", "mixed parity"]
    values = [corr["same_task_junctions"], corr["mixed_task_junctions"],
              corr["same_parity_junctions"], corr["mixed_parity_junctions"]]
    colors = ["#27ae60", "#c0392b", "#27ae60", "#c0392b"]
    ax.bar(labels, values, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_ylabel("junction count")
    ax.set_title("Junction correlation: 100% same-parity!\nLeech class IS a parity discriminator")
    for xi, v in enumerate(values):
        ax.text(xi, v + 0.3, str(v), ha="center", fontsize=10, fontweight="bold")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    # Annotate the key finding
    ax.annotate("user's insight confirmed:\n'many things are practically\nthe same operation'",
                 xy=(2, values[2]), xytext=(2.5, 8),
                 fontsize=9, color="#27ae60", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#27ae60"))

    fig.suptitle("Iteration 8 Phase 1: Junction method", fontsize=13)
    fig.savefig(f"{OUT}/junction_results.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/junction_results.png")


if __name__ == "__main__":
    plot_f2_combiner_results()
    plot_dual_snap_results()
    plot_junction_results()
    print("\nAll plots written to", OUT)
