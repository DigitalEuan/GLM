#!/usr/bin/env python3
"""Generate plots for iteration 3."""

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
OUT  = "/home/z/my-project/download/iter3_plots"
os.makedirs(OUT, exist_ok=True)


def plot_step_rule_chain():
    """Visualise the 6 step rules across the chain layers."""
    fig, ax = plt.subplots(figsize=(13, 5), constrained_layout=True)
    ax.axis("off")
    layers = [
        ("F_2",        "popcount",     "count 1-bits",                "#34495e"),
        ("Hamming",    "d_H",          "XOR + popcount",              "#16a085"),
        ("G_23",       "C(23,k) sum",  "sphere-packing identity",     "#27ae60"),
        ("G_24",       "octads",       "759 octads (Steiner S(5,8,24))", "#2980b9"),
        ("Lambda_24",  "theta series", "E_4^3 - 720*Delta",           "#8e44ad"),
        ("Co_0",       "pair census",  "98,280 type-2 axes",          "#c0392b"),
    ]
    x = np.linspace(0.06, 0.94, len(layers))
    for i, (layer, rule, what, color) in enumerate(layers):
        ax.text(x[i], 0.65, layer, ha="center", va="center", fontsize=11,
                bbox=dict(boxstyle="round,pad=0.5", facecolor=color, edgecolor="black"),
                color="white", fontweight="bold")
        ax.text(x[i], 0.45, rule, ha="center", va="center", fontsize=10,
                color=color, fontweight="bold")
        ax.text(x[i], 0.32, what, ha="center", va="center", fontsize=8.5,
                color="#34495e", style="italic")
        if i < len(layers) - 1:
            ax.annotate("", xy=(x[i+1] - 0.04, 0.65), xytext=(x[i] + 0.04, 0.65),
                        arrowprops=dict(arrowstyle="->", lw=2, color="#7f8c8d"))
    ax.text(0.5, 0.92, "The 6 step rules: one per layer of the F_2 -> Hamming -> G_23 -> G_24 -> Lambda_24 -> Co_0 chain",
            ha="center", va="top", fontsize=12, fontweight="bold")
    ax.text(0.5, 0.08, "These are the GLM's computational primitives. Construction-C Leech snap is a composition of these rules.",
            ha="center", va="bottom", fontsize=10, color="#27ae60")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    fig.savefig(f"{OUT}/step_rule_chain.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/step_rule_chain.png")


def plot_parity_wall():
    """Per-task parity distribution + wall rate."""
    with open(f"{DATA}/iter3_step_rules.json") as f:
        d = json.load(f)
    results = d["results"]
    tasks = list(results.keys())
    even = [results[t]["parity_distribution"]["even"] for t in tasks]
    odd  = [results[t]["parity_distribution"]["odd"]  for t in tasks]
    wall = [results[t]["wall_count"] for t in tasks]
    fig, ax = plt.subplots(figsize=(11, 5), constrained_layout=True)
    x = np.arange(len(tasks))
    w = 0.35
    ax.bar(x - w/2, even, w, label="even parity (snaps to Leech)",
           color="#27ae60", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, wall, w, label="parity wall (odd parity)",
           color="#c0392b", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("# of samples (out of 50)")
    ax.set_ylim(0, 55)
    ax.set_title("Phase 3: parity wall — odd-parity binary grids cannot be encoded\n"
                  "as Leech lattice points via 4*binary + canonical glue")
    ax.legend(loc="upper right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for xi, e, wd in zip(x, even, wall):
        ax.text(xi - w/2, e + 1, str(e), ha="center", fontsize=9, color="#27ae60")
        ax.text(xi + w/2, wd + 1, str(wd), ha="center", fontsize=9, color="#c0392b")
    fig.savefig(f"{OUT}/parity_wall.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/parity_wall.png")


def plot_rule_invocations():
    """Per-task rule invocation counts."""
    with open(f"{DATA}/iter3_step_rules.json") as f:
        d = json.load(f)
    results = d["results"]
    tasks = list(results.keys())
    rule_names = ["popcount", "hamming", "octads", "sum_mod_8", "in_leech"]
    rule_labels = ["popcount\n(F_2)", "hamming\n(Hamming)", "octads\n(G_24)",
                    "sum_mod_8\n(G_24)", "in_leech\n(Lambda_24)"]
    colors = ["#34495e", "#16a085", "#2980b9", "#7f8c8d", "#8e44ad"]
    M = np.zeros((len(tasks), len(rule_names)))
    for i, t in enumerate(tasks):
        c = results[t]["rule_invocation_counts"]
        for j, r in enumerate(rule_names):
            M[i, j] = c.get(r, 0)
    fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
    x = np.arange(len(tasks))
    w = 0.15
    for j, (rule, label, color) in enumerate(zip(rule_names, rule_labels, colors)):
        ax.bar(x + (j - 2) * w, M[:, j], w, label=label, color=color,
                edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("Invocations across 50 samples")
    ax.set_title("Phase 1: step-rule invocations per task family\n"
                  "(Each snap calls popcount, sum_mod_8, in_leech twice; hamming and octads once)")
    ax.legend(loc="upper right", ncols=2, fontsize=8.5)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.savefig(f"{OUT}/rule_invocations.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/rule_invocations.png")


def plot_snap_decision_tree():
    """Visualise the Construction-C snap as a decision tree of step rules."""
    fig, ax = plt.subplots(figsize=(12, 7), constrained_layout=True)
    ax.axis("off")
    # Tree structure
    # Top: input binary target
    # Step 1: popcount(target) -> n_ones
    # Step 2: parity check (n_ones mod 2)
    # Branch A (even): scale by 4 -> principal candidate -> sum_mod_8 check -> in_leech?
    # Branch B (odd): scale by 4 + glue -> odd candidate -> sum_mod_8 check -> in_leech?
    # If both branches fail (odd parity case): WALL -> escalate to Lambda_32 / Lambda_48
    # If one succeeds: VERDICT (in Leech)
    # Diagnostic: hamming to nearest codeword, octad check
    nodes = [
        # (x, y, label, color)
        (0.5, 0.92, "INPUT: binary target (24-bit word)", "#34495e"),
        (0.5, 0.80, "popcount(target) → n_ones  [F_2 rule]", "#34495e"),
        (0.5, 0.68, "parity = n_ones mod 2", "#34495e"),
        (0.25, 0.56, "EVEN: 4*target → principal candidate", "#27ae60"),
        (0.75, 0.56, "ODD: 4*target + glue → odd candidate", "#c0392b"),
        (0.25, 0.44, "sum_mod_8 (need 0)", "#16a085"),
        (0.75, 0.44, "sum_mod_8 (need 4)", "#16a085"),
        (0.25, 0.32, "in_leech test  [Lambda_24 rule]", "#8e44ad"),
        (0.75, 0.32, "in_leech test  [Lambda_24 rule]", "#8e44ad"),
        (0.25, 0.20, "VERDICT: IN LEECH", "#27ae60"),
        (0.75, 0.20, "WALL: parity wall\n(odd parity → no Leech encoding)", "#c0392b"),
        (0.5, 0.08, "Diagnostic: hamming → nearest codeword; octads check\n[Hamming + G_24 rules]", "#7f8c8d"),
    ]
    for x, y, label, color in nodes:
        ax.text(x, y, label, ha="center", va="center", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.4", facecolor=color, edgecolor="black", alpha=0.85),
                color="white", fontweight="bold")
    # arrows
    arrows = [
        ((0.5, 0.88), (0.5, 0.84)),
        ((0.5, 0.76), (0.5, 0.72)),
        ((0.40, 0.64), (0.25, 0.60)),
        ((0.60, 0.64), (0.75, 0.60)),
        ((0.25, 0.52), (0.25, 0.48)),
        ((0.75, 0.52), (0.75, 0.48)),
        ((0.25, 0.40), (0.25, 0.36)),
        ((0.75, 0.40), (0.75, 0.36)),
        ((0.25, 0.28), (0.25, 0.24)),
        ((0.75, 0.28), (0.75, 0.24)),
        ((0.25, 0.16), (0.5, 0.12)),
        ((0.75, 0.16), (0.5, 0.12)),
    ]
    for (x1, y1), (x2, y2) in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=1.5, color="#7f8c8d"))
    ax.text(0.5, 0.97, "Construction-C Leech snap as a composition of step rules",
            ha="center", va="top", fontsize=13, fontweight="bold")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    fig.savefig(f"{OUT}/snap_decision_tree.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/snap_decision_tree.png")


if __name__ == "__main__":
    plot_step_rule_chain()
    plot_parity_wall()
    plot_rule_invocations()
    plot_snap_decision_tree()
    print("\nAll plots written to", OUT)
