#!/usr/bin/env python3
"""
Generate plots for iteration 2.

Outputs (in /home/z/my-project/download/iter2_plots/):
  cost_atlas_bars.png        — Phase 1: per-task mean cost (delta wt, coset wt, TAX)
  coset_weight_heatmap.png  — Phase 1: coset weight histogram per task
  wobble_signatures.png     — Phase 2: constants vs tasks wobble signatures
  hull_separation.png       — Phase 2: hull separation rate (constants vs tasks)
  leech_vs_golay_wobble.png — Phase 3: Leech vs Golay wobble (constants baseline)
  per_step_costs.png        — Phase 4: per-step coset weight + TAX
  escalation_ladder.png     — Summary: layered perspective (Golay -> Leech -> Barnes-Wall)
"""

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
OUT  = "/home/z/my-project/download/iter2_plots"
os.makedirs(OUT, exist_ok=True)


# ============================================================================
# Plot 1: Cost atlas bars (Phase 1)
# ============================================================================
def plot_cost_atlas():
    with open(f"{DATA}/iter2_phase1_atlas.json") as f:
        d = json.load(f)
    tasks = ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]
    delta_means = [d[t]["delta_weight_mean"] for t in tasks]
    coset_means = [d[t]["coset_weight_mean"] for t in tasks]
    tax_means   = [d[t]["tax_mean"] for t in tasks]
    ambig_rates = [100 * d[t]["ambiguous_rate"] for t in tasks]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), constrained_layout=True)
    x = np.arange(len(tasks))
    w = 0.35
    # Left: delta weight + coset weight
    ax = axes[0]
    ax.bar(x - w/2, delta_means, w, label="Δ weight (bits changed)",
           color="#3498db", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, coset_means, w, label="coset weight (F_2 cost)",
           color="#e67e22", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("Mean weight")
    ax.set_ylim(0, 26)
    ax.set_title("Phase 1: Displacement weight vs coset weight")
    ax.legend(loc="upper right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    # Right: TAX + ambiguous rate
    ax = axes[1]
    ax.bar(x - w/2, tax_means, w, label="TAX (codeword energy)",
           color="#9b59b6", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, ambig_rates, w, label="ambiguous % (coset wt=4)",
           color="#c0392b", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("TAX (left) / Ambiguous % (right)")
    ax.set_ylim(0, 105)
    ax.set_title("Phase 1: TAX cost + escalation trigger rate")
    ax.legend(loc="upper right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.savefig(f"{OUT}/cost_atlas_bars.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/cost_atlas_bars.png")


# ============================================================================
# Plot 2: Coset weight heatmap (Phase 1)
# ============================================================================
def plot_coset_heatmap():
    with open(f"{DATA}/iter2_phase1_atlas.json") as f:
        d = json.load(f)
    tasks = ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]
    # Build a (5 x 5) matrix: task x coset weight (0..4)
    M = np.zeros((len(tasks), 5))
    for i, t in enumerate(tasks):
        hist = d[t]["coset_weight_histogram"]
        for k, v in hist.items():
            M[i, int(k)] = v
    # Normalise each row
    M_norm = M / M.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    im = ax.imshow(M_norm, cmap="YlOrRd", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(5)); ax.set_xticklabels([f"coset wt {i}" for i in range(5)])
    ax.set_yticks(range(len(tasks))); ax.set_yticklabels(tasks)
    ax.set_title("Phase 1: coset weight distribution per task (row-normalised)")
    # Annotate
    for i in range(len(tasks)):
        for j in range(5):
            val = M_norm[i, j]
            if val > 0:
                ax.text(j, i, f"{val*100:.0f}%", ha="center", va="center",
                         color="white" if val > 0.5 else "black",
                         fontsize=10, fontweight="bold")
    fig.colorbar(im, ax=ax, label="fraction of transitions")
    fig.savefig(f"{OUT}/coset_weight_heatmap.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/coset_weight_heatmap.png")


# ============================================================================
# Plot 3: Wobble signatures (Phase 2) — constants vs tasks
# ============================================================================
def plot_wobble_signatures():
    with open(f"{DATA}/iter2_phase2_wobble.json") as f:
        d = json.load(f)
    constants = list(d["constants"].keys())
    tasks = list(d["tasks"].keys())
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    # Left: constants baseline
    ax = axes[0]
    x = np.arange(len(constants))
    uniq = [d["constants"][c]["wobble"]["unique_codewords"] for c in constants]
    acc  = [d["constants"][c]["wobble"]["max_accumulator"] for c in constants]
    share = [d["constants"][c]["wobble"]["most_visited_share"] for c in constants]
    ax.bar(x - 0.2, uniq, 0.4, label="unique codewords", color="#3498db",
            edgecolor="black", linewidth=0.5)
    ax2 = ax.twinx()
    ax2.bar(x + 0.2, acc, 0.4, label="max accumulator", color="#c0392b",
              edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(constants, rotation=20)
    ax.set_ylabel("unique codewords", color="#3498db")
    ax2.set_ylabel("max accumulator (linear growth = unreachable)", color="#c0392b")
    ax.set_title("Phase 2: Wobble on constants (Golay alphabet)")
    ax.set_ylim(0, 5)
    ax2.set_ylim(0, 5)
    ax.legend(loc="upper left"); ax2.legend(loc="upper right")
    # Right: tasks
    ax = axes[1]
    x = np.arange(len(tasks))
    uniq_t = [d["tasks"][t]["per_seed_summary"]["unique_codewords_mean"] for t in tasks]
    acc_t  = [d["tasks"][t]["per_seed_summary"]["max_accumulator_mean"] for t in tasks]
    sep_t  = [100 * d["tasks"][t]["per_seed_summary"]["hull_separates_rate"] for t in tasks]
    ax.bar(x - 0.2, uniq_t, 0.4, label="unique codewords", color="#3498db",
            edgecolor="black", linewidth=0.5)
    ax2 = ax.twinx()
    ax2.bar(x + 0.2, acc_t, 0.4, label="max accumulator", color="#c0392b",
              edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("unique codewords", color="#3498db")
    ax2.set_ylabel("max accumulator (linear growth = unreachable)", color="#c0392b")
    ax.set_title("Phase 2: Wobble on task targets (Golay alphabet)")
    ax.set_ylim(0, 5)
    ax2.set_ylim(0, 450)
    ax.legend(loc="upper left"); ax2.legend(loc="upper right")
    fig.savefig(f"{OUT}/wobble_signatures.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/wobble_signatures.png")


# ============================================================================
# Plot 4: Hull separation rate (Phase 2)
# ============================================================================
def plot_hull_separation():
    with open(f"{DATA}/iter2_phase2_wobble.json") as f:
        d = json.load(f)
    constants = list(d["constants"].keys())
    tasks = list(d["tasks"].keys())
    const_sep = [100 if d["constants"][c]["hull"]["separates"] else 0 for c in constants]
    task_sep  = [100 * d["tasks"][t]["per_seed_summary"]["hull_separates_rate"] for t in tasks]
    fig, ax = plt.subplots(figsize=(11, 4.5), constrained_layout=True)
    x = np.arange(len(constants) + len(tasks))
    vals = const_sep + task_sep
    colors = ["#27ae60"] * len(constants) + ["#c0392b"] * len(tasks)
    ax.bar(x, vals, color=colors, edgecolor="black", linewidth=0.5)
    labels = [f"const:\n{c}" for c in constants] + [f"task:\n{t}" for t in tasks]
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=0, fontsize=8)
    ax.set_ylabel("Hull-separation rate (%)")
    ax.set_ylim(0, 110)
    ax.set_title("Phase 2: hull certificate — is the target OUTSIDE the convex hull of the 4096 Golay codewords?\n"
                  "Green = inside (reachable by wobble); Red = outside (substrate MUST escalate)")
    # Threshold line
    ax.axhline(50, color="gray", linestyle="--", alpha=0.5)
    # Annotate
    for xi, v in zip(x, vals):
        ax.text(xi, v + 3, f"{v:.0f}%", ha="center", fontsize=9)
    fig.savefig(f"{OUT}/hull_separation.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/hull_separation.png")


# ============================================================================
# Plot 5: Leech vs Golay wobble (Phase 3)
# ============================================================================
def plot_leech_vs_golay():
    with open(f"{DATA}/iter2_phase2_wobble.json") as f:
        d2 = json.load(f)
    with open(f"{DATA}/iter2_phase3_leech.json") as f:
        d3 = json.load(f)
    constants = list(d2["constants"].keys())
    fig, ax = plt.subplots(figsize=(11, 5), constrained_layout=True)
    x = np.arange(len(constants))
    w = 0.35
    # Golay acc_max (constants)
    golay_acc = [d2["constants"][c]["wobble"]["max_accumulator"] for c in constants]
    # Leech acc_max (constants)
    leech_acc = [d3["constants"][c]["max_accumulator"] for c in constants]
    ax.bar(x - w/2, golay_acc, w, label="Golay alphabet (4,096 codewords)",
           color="#3498db", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, leech_acc, w, label="Leech shell alphabet (196,560 minimal vectors)",
           color="#e67e22", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(constants, rotation=20)
    ax.set_ylabel("Max accumulator (lower = better convergence)")
    ax.set_ylim(0, 800)
    ax.set_title("Phase 3: Golay vs Leech wobble — constants baseline\n"
                  "sqrt2_minus_1 and phi_minus_1 CONVERGE on the Leech shell; others still fail")
    ax.legend(loc="upper left")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    # Annotate convergence (acc < 10)
    for xi, v in zip(x, leech_acc):
        if v < 10:
            ax.text(xi + w/2, v + 15, "✓ converges", ha="center",
                     color="#27ae60", fontsize=9, fontweight="bold")
        elif v < 100:
            ax.text(xi + w/2, v + 15, "partial", ha="center",
                     color="#a68544", fontsize=9)
        else:
            ax.text(xi + w/2, v + 15, "✗ diverges", ha="center",
                     color="#c0392b", fontsize=9)
    fig.savefig(f"{OUT}/leech_vs_golay_wobble.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/leech_vs_golay_wobble.png")


# ============================================================================
# Plot 6: Per-step costs (Phase 4)
# ============================================================================
def plot_per_step_costs():
    with open(f"{DATA}/iter2_phase4_per_step.json") as f:
        d = json.load(f)
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), constrained_layout=True)
    axes = axes.flatten()
    task_colors = {"toggle": "#3498db", "translate": "#e67e22",
                     "reflect_v": "#9b59b6", "flood_fill": "#27ae60",
                     "bfs_shortest": "#c0392b"}
    for i, (name, r) in enumerate(d.items()):
        ax = axes[i]
        steps = list(r["per_step"].keys())
        cosets = [r["per_step"][s]["coset_weight_mean"] for s in steps]
        taxes  = [r["per_step"][s]["tax_mean"] for s in steps]
        ambig  = [100 * r["per_step"][s]["ambiguous_rate"] for s in steps]
        x = np.arange(len(steps))
        w = 0.3
        ax.bar(x - w, cosets, w, label="coset wt", color=task_colors[name],
                edgecolor="black", linewidth=0.5, alpha=0.7)
        ax.bar(x, taxes, w, label="TAX", color="#7f8c8d",
                edgecolor="black", linewidth=0.5, alpha=0.7)
        ax.bar(x + w, [a / 25 for a in ambig], w, label="ambig % (÷25)",
                color="#c0392b", edgecolor="black", linewidth=0.5, alpha=0.7)
        ax.set_xticks(x); ax.set_xticklabels(steps, rotation=20, fontsize=8)
        ax.set_ylim(0, 11)
        ax.set_title(f"{name}", fontsize=11)
        ax.set_ylabel("cost")
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        if i == 0:
            ax.legend(loc="upper right", fontsize=8)
        # Mark escalation zones (coset wt = 4)
        for xi, c in zip(x, cosets):
            if c >= 3.5:
                ax.axvspan(xi - 0.5, xi + 0.5, color="red", alpha=0.08)
                ax.text(xi, 10, "ESCALATE", ha="center", color="red",
                         fontsize=8, fontweight="bold")
    axes[5].axis("off")
    axes[5].text(0.5, 0.5, "Red shaded zones = steps where coset wt ≈ 4\n"
                            "(deep hole — substrate cannot decide octad;\n"
                            "must escalate to Leech lattice)",
                  ha="center", va="center", fontsize=10, transform=axes[5].transAxes)
    fig.suptitle("Phase 4: per-step cost in multi-step transformation traces",
                   fontsize=13)
    fig.savefig(f"{OUT}/per_step_costs.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/per_step_costs.png")


# ============================================================================
# Plot 7: Escalation ladder (summary)
# ============================================================================
def plot_escalation_ladder():
    fig, ax = plt.subplots(figsize=(12, 6), constrained_layout=True)
    ax.axis("off")
    layers = [
        ("F_2^24 / G_24\n(binary quotient)\n4,096 cosets\nTAX range: 0 to ~9.35",
         "#34495e", 0.05),
        ("Golay code\n[24,12,8]\n759 octads\nS(5,8,24), min TAX = 3.117",
         "#16a085", 0.22),
        ("Leech lattice Λ_24\n196,560 minimal vectors\nnorm² 32, no roots\nconvex hull = bounded ball",
         "#8e44ad", 0.42),
        ("Barnes-Wall Λ_32\n146,880 minimal vectors\nthree nested resolutions\n(4Z^32 ⊂ 2·RM(3,5) ⊂ RM(1,5))",
         "#c0392b", 0.65),
        ("Ternary Λ_48\n96 words of norm² 18\n16,834× denser than Leech\n(no Golay; uses F_3 code)",
         "#7f8c8d", 0.88),
    ]
    for label, color, x in layers:
        ax.text(x, 0.55, label, ha="center", va="center", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.6", facecolor=color, edgecolor="black", alpha=0.85),
                color="white", fontweight="bold")
    # Arrows
    for i in range(len(layers) - 1):
        x1 = layers[i][2] + 0.06
        x2 = layers[i+1][2] - 0.06
        ax.annotate("", xy=(x2, 0.55), xytext=(x1, 0.55),
                    arrowprops=dict(arrowstyle="->", lw=2, color="#7f8c8d"))
    # Failure annotations between layers
    failures = [
        (0.13, "Phase 1: toggle Δ is a codeword\n(cw wt 24); F_2 quotient loses it."),
        (0.32, "Phase 2: ALL task targets lie OUTSIDE\nthe Golay hull (hull_sep = 100%)."),
        (0.53, "Phase 3: binary targets in ±4 encoding\nlie outside the Leech shell hull too."),
        (0.76, "Open: does Λ_32's three nested resolutions\nresolve the deep-hole ambiguity?"),
    ]
    for x, text in failures:
        ax.text(x, 0.20, text, ha="center", va="top", fontsize=8.5,
                color="#c0392b", style="italic",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff5f5",
                           edgecolor="#c0392b", alpha=0.9))
    ax.text(0.5, 0.92, "Layered perspective: failure indicates the required mechanism for progression up the ladder",
            ha="center", va="top", fontsize=12, fontweight="bold")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    fig.savefig(f"{OUT}/escalation_ladder.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/escalation_ladder.png")


if __name__ == "__main__":
    plot_cost_atlas()
    plot_coset_heatmap()
    plot_wobble_signatures()
    plot_hull_separation()
    plot_leech_vs_golay()
    plot_per_step_costs()
    plot_escalation_ladder()
    print("\nAll plots written to", OUT)
