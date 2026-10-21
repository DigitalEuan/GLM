#!/usr/bin/env python3
"""Generate plots for iteration 6."""

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
OUT  = "/home/z/my-project/download/iter6_plots"
os.makedirs(OUT, exist_ok=True)


def plot_iter5_vs_iter6():
    """Compare iteration 5 baseline vs iteration 6 fixed learner."""
    with open(f"{DATA}/iter6_fixed_learner.json") as f:
        d = json.load(f)
    tasks = list(d["results"].keys())
    # Iteration 5 baseline (hardcoded from the previous report)
    iter5_in = {"toggle": 0.741, "translate": 0.826, "reflect_v": 0.737,
                 "flood_fill": 0.870, "bfs_shortest": 0.670}
    iter5_ho = {"toggle": 0.627, "translate": 0.873, "reflect_v": 0.653,
                 "flood_fill": 0.967, "bfs_shortest": 0.600}

    iter6_in = [d["results"][t]["in_dist_acc"]["lattice"] for t in tasks]
    iter6_ho = [d["results"][t]["held_out_acc"]["lattice"] for t in tasks]
    iter5_in_list = [iter5_in[t] for t in tasks]
    iter5_ho_list = [iter5_ho[t] for t in tasks]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)

    # Left: in-distribution
    ax = axes[0]
    x = np.arange(len(tasks))
    w = 0.35
    ax.bar(x - w/2, iter5_in_list, w, label="iteration 5 baseline",
           color="#7f8c8d", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, iter6_in, w, label="iteration 6 (parity + balanced + 4-layer)",
           color="#27ae60", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("in-distribution lattice accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_title("In-distribution: 3 dev escalation requirements applied")
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for xi, (i5, i6) in enumerate(zip(iter5_in_list, iter6_in)):
        delta = i6 - i5
        sign = "+" if delta >= 0 else ""
        ax.text(xi, max(i5, i6) + 0.04, f"Δ {sign}{delta:.3f}",
                 ha="center", fontsize=8.5, color="#27ae60" if delta >= 0 else "#c0392b",
                 fontweight="bold")

    # Right: held-out cross-task
    ax = axes[1]
    ax.bar(x - w/2, iter5_ho_list, w, label="iteration 5 baseline",
           color="#7f8c8d", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, iter6_ho, w, label="iteration 6 (parity + balanced + 4-layer)",
           color="#3498db", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("held-out cross-task lattice accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_title("Held-out cross-task: 3 dev escalation requirements applied")
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for xi, (i5, i6) in enumerate(zip(iter5_ho_list, iter6_ho)):
        delta = i6 - i5
        sign = "+" if delta >= 0 else ""
        ax.text(xi, max(i5, i6) + 0.04, f"Δ {sign}{delta:.3f}",
                 ha="center", fontsize=8.5, color="#27ae60" if delta >= 0 else "#c0392b",
                 fontweight="bold")

    fig.suptitle("Iteration 6 Phase 1: fixed learner vs iteration 5 baseline", fontsize=13)
    fig.savefig(f"{OUT}/iter5_vs_iter6.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/iter5_vs_iter6.png")


def plot_lambda96_results():
    """Plot Λ_96 snap results and the spin superposition."""
    with open(f"{DATA}/iter6_lambda96.json") as f:
        d = json.load(f)
    results = d["results"]
    tasks = list(results.keys())
    snap_rates = [100 * results[t]["snap_ok_rate"] for t in tasks]
    mean_spins = [results[t]["mean_spin_superpositions"] for t in tasks]
    max_spins = [results[t]["max_spin_superpositions"] for t in tasks]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)

    # Left: snap success rate
    ax = axes[0]
    x = np.arange(len(tasks))
    ax.bar(x, snap_rates, 0.5, color="#27ae60", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("Λ_96 snap success rate (%)")
    ax.set_ylim(0, 110)
    ax.set_title("Λ_96 (over F_3, C_96 = C_23 × C_23) snap rate\n100% across all task families")
    ax.axhline(y=100, color="#27ae60", linestyle="--", alpha=0.5)
    for xi, r in enumerate(snap_rates):
        ax.text(xi, r + 2, f"{r:.0f}%", ha="center", fontsize=10, color="#27ae60", fontweight="bold")
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    # Right: spin superposition count
    ax = axes[1]
    x = np.arange(len(tasks))
    w = 0.35
    ax.bar(x - w/2, mean_spins, w, label="mean spin superpositions",
           color="#3498db", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, max_spins, w, label="max spin superpositions",
           color="#e67e22", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("# spin orientations valid in Λ_96")
    ax.set_ylim(0, 4.5)
    ax.set_title("Spin superposition count per target\n(3-element superposition across all tasks)")
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for xi, (m, mx) in enumerate(zip(mean_spins, max_spins)):
        ax.text(xi - w/2, m + 0.05, f"{m:.2f}", ha="center", fontsize=9, color="#3498db")
        ax.text(xi + w/2, mx + 0.05, f"{mx}", ha="center", fontsize=9, color="#e67e22")

    fig.suptitle("Iteration 6 Phase 2: Λ_96 snap + spin superposition results", fontsize=13)
    fig.savefig(f"{OUT}/lambda96_results.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/lambda96_results.png")


def plot_lattice_comparison():
    """Visualise the layered comparison Λ_24 vs Λ_48 vs Λ_96."""
    with open(f"{DATA}/iter6_lambda96.json") as f:
        d = json.load(f)
    comparisons = d["comparisons"]
    # Aggregate: for each parity, count in_lattice at each layer
    by_parity_layer = {"even": {"Lambda_24": 0, "Lambda_48": 0, "Lambda_96": 0, "n": 0},
                       "odd":  {"Lambda_24": 0, "Lambda_48": 0, "Lambda_96": 0, "n": 0}}
    for c in comparisons:
        p = c["parity"]
        by_parity_layer[p]["n"] += 1
        for L in ["Lambda_24", "Lambda_48", "Lambda_96"]:
            if c[L]["in_lattice"]:
                by_parity_layer[p][L] += 1

    fig, ax = plt.subplots(figsize=(11, 5), constrained_layout=True)
    layers = ["Lambda_24", "Lambda_48", "Lambda_96"]
    x = np.arange(len(layers))
    w = 0.35
    even_counts = [by_parity_layer["even"][L] for L in layers]
    odd_counts  = [by_parity_layer["odd"][L]  for L in layers]
    n_even = by_parity_layer["even"]["n"]
    n_odd  = by_parity_layer["odd"]["n"]
    ax.bar(x - w/2, even_counts, w, label=f"even parity ({n_even} samples)",
           color="#27ae60", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, odd_counts, w, label=f"odd parity ({n_odd} samples)",
           color="#c0392b", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(["Λ_24\n(Leech, F_2 binary)", "Λ_48\n(ternary, F_3)",
                                            "Λ_96\n(F_3 lift, C_23 × C_23)"])
    ax.set_ylabel("# samples that snap to the lattice")
    ax.set_ylim(0, max(n_even, n_odd) + 2)
    ax.set_title("Layered snap comparison: Λ_24 → Λ_48 → Λ_96\n"
                  "Λ_96 matches Λ_48 (100% snap rate) but provides richer spin structure")
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for xi, (e, o) in enumerate(zip(even_counts, odd_counts)):
        ax.text(xi - w/2, e + 0.1, f"{e}/{n_even}", ha="center", fontsize=9, color="#27ae60")
        ax.text(xi + w/2, o + 0.1, f"{o}/{n_odd}", ha="center", fontsize=9, color="#c0392b")
    fig.savefig(f"{OUT}/lattice_comparison_iter6.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/lattice_comparison_iter6.png")


if __name__ == "__main__":
    plot_iter5_vs_iter6()
    plot_lambda96_results()
    plot_lattice_comparison()
    print("\nAll plots written to", OUT)
