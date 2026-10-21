#!/usr/bin/env python3
"""
Generate plots for the GLM experiments report.

Outputs:
  /home/z/my-project/download/plots/exp_AC_bars.png       (Note 5)
  /home/z/my-project/download/plots/exp_B_bars.png        (Notes 1-2)
  /home/z/my-project/download/plots/exp_B_imr_bars.png   (Notes 1-2 IMR)
  /home/z/my-project/download/plots/exp_B_curves.png     (Notes 1-2 learning curves)
  /home/z/my-project/download/plots/audit_chain.png       (Note 4 chain summary)
"""

import os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
# Register a Chinese-safe font (in case any CJK glyphs sneak in), DejaVu for symbols
try:
    fm.fontManager.addfont('/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf')
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
OUT  = "/home/z/my-project/download/plots"
os.makedirs(OUT, exist_ok=True)


# ============================================================================
# Plot 1: Experiment A+C -- solver comparison bars
# ============================================================================
def plot_exp_AC():
    with open(f"{DATA}/exp_AC_results.json") as f:
        d = json.load(f)
    agg = d["aggregate"]
    tasks = ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]
    solvers = ["oracle", "raw_xor", "golay_coset", "random_linear"]
    labels  = ["Oracle", "Raw XOR", "Golay coset", "Random linear"]
    colors  = ["#2c3e50", "#27ae60", "#c0392b", "#7f8c8d"]

    fig, ax = plt.subplots(figsize=(11, 5.5), constrained_layout=True)
    x = np.arange(len(tasks))
    width = 0.2
    for i, (sol, lab, col) in enumerate(zip(solvers, labels, colors)):
        vals = [agg[t]["em"][sol] for t in tasks]
        ax.bar(x + (i - 1.5) * width, vals, width, label=lab, color=col, edgecolor="black", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("Exact-match accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_title("Experiment A+C (Note 5): Leech/Golay quotient adds no transfer power\n"
                 "4x6 grids, 50 trials per task family")
    ax.legend(loc="upper right", framealpha=0.95)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    # annotate the transfer_safe flag
    for xi, t in enumerate(tasks):
        flag = "Δ transfers" if agg[t]["transfer_safe"] else "Δ does not transfer"
        ax.text(xi, -0.10, flag, ha="center", va="top", fontsize=8,
                color="#34495e", transform=ax.get_xaxis_transform())
    fig.savefig(f"{OUT}/exp_AC_bars.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/exp_AC_bars.png")


# ============================================================================
# Plot 2: Experiment B -- final EM bars (FINAL_ONLY vs TRACE)
# ============================================================================
def plot_exp_B_em():
    with open(f"{DATA}/exp_B_results.json") as f:
        d = json.load(f)
    agg = d["aggregate"]
    tasks = ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]
    final_means, final_stds = [], []
    trace_means, trace_stds = [], []
    for t in tasks:
        kf = f"{t}|trace=False"; kt = f"{t}|trace=True"
        final_means.append(agg[kf]["best_em_mean"])
        final_stds.append(agg[kf]["best_em_std"])
        trace_means.append(agg[kt]["best_em_mean"])
        trace_stds.append(agg[kt]["best_em_std"])
    fig, ax = plt.subplots(figsize=(10, 5.5), constrained_layout=True)
    x = np.arange(len(tasks))
    w = 0.35
    ax.bar(x - w/2, final_means, w, yerr=final_stds, label="FINAL_ONLY",
           color="#3498db", edgecolor="black", linewidth=0.5, capsize=4)
    ax.bar(x + w/2, trace_means, w, yerr=trace_stds, label="TRACE",
           color="#e67e22", edgecolor="black", linewidth=0.5, capsize=4)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("Best validation exact-match accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_title("Experiment B (Notes 1-2): trace supervision vs. final-answer-only\n"
                 "3 seeds, 500 train / 100 val, 60 epochs, 4x6 grids")
    ax.legend(loc="lower right", framealpha=0.95)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    # annotate delta
    for xi, (f, t) in enumerate(zip(final_means, trace_means)):
        d = t - f
        sign = "+" if d >= 0 else ""
        ax.text(xi, max(f, t) + 0.05, f"Δ {sign}{d:.3f}",
                ha="center", va="bottom", fontsize=9,
                color="#c0392b" if d < 0 else "#27ae60",
                fontweight="bold")
    fig.savefig(f"{OUT}/exp_B_bars.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/exp_B_bars.png")


# ============================================================================
# Plot 3: Experiment B -- IMR bars
# ============================================================================
def plot_exp_B_imr():
    with open(f"{DATA}/exp_B_results.json") as f:
        d = json.load(f)
    agg = d["aggregate"]
    tasks = ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]
    final_means, trace_means = [], []
    for t in tasks:
        kf = f"{t}|trace=False"; kt = f"{t}|trace=True"
        final_means.append(agg[kf]["best_imr_mean"])
        trace_means.append(agg[kt]["best_imr_mean"])
    fig, ax = plt.subplots(figsize=(10, 5.5), constrained_layout=True)
    x = np.arange(len(tasks))
    w = 0.35
    ax.bar(x - w/2, final_means, w, label="FINAL_ONLY",
           color="#3498db", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, trace_means, w, label="TRACE",
           color="#e67e22", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("Best intermediate match rate (IMR)")
    ax.set_ylim(0, 1.05)
    ax.set_title("Experiment B: intermediate-grid match rate (IMR)\n"
                 "TRACE always improves alignment with intermediate milestones")
    ax.legend(loc="lower right", framealpha=0.95)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for xi, (f, t) in enumerate(zip(final_means, trace_means)):
        d = t - f
        sign = "+" if d >= 0 else ""
        ax.text(xi, max(f, t) + 0.03, f"Δ {sign}{d:.3f}",
                ha="center", va="bottom", fontsize=9,
                color="#27ae60" if d >= 0 else "#c0392b",
                fontweight="bold")
    fig.savefig(f"{OUT}/exp_B_imr_bars.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/exp_B_imr_bars.png")


# ============================================================================
# Plot 4: Experiment B -- learning curves (mean ± std across seeds)
# ============================================================================
def plot_exp_B_curves():
    with open(f"{DATA}/exp_B_results.json") as f:
        d = json.load(f)
    results = d["results"]["results"]
    tasks = ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]
    fig, axes = plt.subplots(1, 5, figsize=(16, 4), constrained_layout=True)
    for ax, t in zip(axes, tasks):
        for trace, color, lab in [(False, "#3498db", "FINAL_ONLY"),
                                   (True, "#e67e22", "TRACE")]:
            curves = [r["val_em_curve"] for r in results
                      if r["task"] == t and r["trace"] == trace]
            if not curves: continue
            arr = np.array(curves)  # shape (n_seeds, n_epochs)
            mean = arr.mean(axis=0)
            std  = arr.std(axis=0)
            epochs = np.arange(len(mean))
            ax.plot(epochs, mean, color=color, lw=2, label=lab)
            ax.fill_between(epochs, mean - std, mean + std,
                             color=color, alpha=0.2)
        ax.set_title(t, fontsize=11)
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Val EM")
        ax.set_ylim(-0.05, 1.05)
        ax.grid(linestyle=":", alpha=0.4)
        if t == "toggle":
            ax.legend(loc="upper left", fontsize=8)
    fig.suptitle("Experiment B: validation EM learning curves (mean ± std across 3 seeds)",
                 fontsize=13)
    fig.savefig(f"{OUT}/exp_B_curves.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/exp_B_curves.png")


# ============================================================================
# Plot 5: Note 4 audit chain summary
# ============================================================================
def plot_audit_chain():
    fig, ax = plt.subplots(figsize=(12, 4.5), constrained_layout=True)
    ax.axis("off")
    chain = [
        ("F_2\n{0,1}", "#34495e"),
        ("Hamming\nmetric", "#16a085"),
        ("G_23\n[23,12,7]_2\nperfect code", "#27ae60"),
        ("G_24\n[24,12,8]_2\ndoubly even,\nself-dual", "#2980b9"),
        ("Lambda_24\nmin norm 4\nno roots\n196,560 min vecs", "#8e44ad"),
        ("Co_0 / Co_1\n98,280 type-2\naxes", "#c0392b"),
    ]
    x = np.linspace(0.05, 0.95, len(chain))
    for i, (label, color) in enumerate(chain):
        ax.text(x[i], 0.55, label, ha="center", va="center", fontsize=10,
                bbox=dict(boxstyle="round,pad=0.6", facecolor=color, edgecolor="black", alpha=0.85),
                color="white", fontweight="bold")
        if i < len(chain) - 1:
            ax.annotate("", xy=(x[i+1] - 0.04, 0.55), xytext=(x[i] + 0.05, 0.55),
                        arrowprops=dict(arrowstyle="->", lw=2, color="#7f8c8d"))
    # Substrate-verified facts below each box
    facts = [
        "popcount = 3",
        "d_H = XOR popcount",
        "C(23,k) sum = 2^11",
        "759 octads\nS(5,8,24)",
        "theta series\nE_4^3 - 720Δ",
        "pair census\n{4:2, 2:9200,\n1:94208, 0:93150}",
    ]
    for i, f in enumerate(facts):
        ax.text(x[i], 0.18, f, ha="center", va="top", fontsize=8,
                color="#34495e", family="monospace")
    ax.text(0.5, 0.92, "Note 4 Math Audit: F_2 -> Hamming -> Golay -> Leech -> Conway",
            ha="center", va="top", fontsize=13, fontweight="bold")
    ax.text(0.5, 0.05, "22/22 substrate self-checks PASS — chain is real, exact, and matches every cited theorem.",
            ha="center", va="bottom", fontsize=10, color="#27ae60")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    fig.savefig(f"{OUT}/audit_chain.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/audit_chain.png")


if __name__ == "__main__":
    plot_exp_AC()
    plot_exp_B_em()
    plot_exp_B_imr()
    plot_exp_B_curves()
    plot_audit_chain()
    print("\nAll plots written to", OUT)
