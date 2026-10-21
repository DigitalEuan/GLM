#!/usr/bin/env python3
"""Generate plots for iteration 5."""

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
OUT  = "/home/z/my-project/download/iter5_plots"
os.makedirs(OUT, exist_ok=True)


def plot_field_punctures():
    """Plot the puncture/spin structure across F_2, F_3, F_4, F_5, F_7, F_8, F_9."""
    with open(f"{DATA}/iter5_field_punctures.json") as f:
        fields = json.load(f)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    names = [f["name"] for f in fields]
    qs = [f["q"] for f in fields]
    units = [f["n_units"] for f in fields]
    spins = [f["spin_order"] for f in fields]
    chars = [f["char"] for f in fields]

    # Left: units and spin_order vs q
    ax = axes[0]
    x = np.arange(len(fields))
    w = 0.35
    ax.bar(x - w/2, units, w, label="# units (mult group size)",
           color="#3498db", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, spins, w, label="spin order (order of mult by 2 or α)",
           color="#e67e22", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{n}\n(q={q}, char={c})" for n, q, c in zip(names, qs, chars)],
                         fontsize=8)
    ax.set_ylabel("count")
    ax.set_title("Multiplicative richness across finite fields")
    ax.legend(loc="upper left")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for xi, (u, s) in enumerate(zip(units, spins)):
        ax.text(xi - w/2, u + 0.2, str(u), ha="center", fontsize=8, color="#3498db")
        ax.text(xi + w/2, s + 0.2, str(s), ha="center", fontsize=8, color="#e67e22")

    # Right: spin_order vs q (log scale, showing the doubling pattern)
    ax = axes[1]
    ax.plot(qs, spins, "o-", color="#e67e22", lw=2, markersize=10,
             markerfacecolor="white", markeredgewidth=2)
    # Annotate each point
    for q, s, name in zip(qs, spins, names):
        ax.annotate(f"{name}\nspin_order={s}",
                     xy=(q, s), xytext=(5, 5), textcoords="offset points",
                     fontsize=8, color="#34495e")
    ax.set_xlabel("field size q")
    ax.set_ylabel("spin order (order of multiplication by 2 / α)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title("Spin richness growth: the user's 'doubling' prediction\n"
                  "F_2 → F_3: 0 → 2 (puncture broken, spin appears)\n"
                  "F_3 → F_9: 2 → 4 (spin DOUBLES — the predicted finer resolution)")
    ax.grid(True, which="both", linestyle=":", alpha=0.4)
    # Highlight the two doubling transitions
    ax.annotate("F_2 → F_3:\n0 → 2 (puncture broken)",
                 xy=(3, 2), xytext=(2.5, 4),
                 fontsize=9, color="#27ae60", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#27ae60"))
    ax.annotate("F_3 → F_9:\n2 → 4 (spin DOUBLES)",
                 xy=(9, 4), xytext=(6, 7),
                 fontsize=9, color="#27ae60", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#27ae60"))

    fig.savefig(f"{OUT}/field_punctures.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/field_punctures.png")


def plot_rule_learner():
    """Plot the multi-head rule-learner results."""
    with open(f"{DATA}/iter5_rule_learner.json") as f:
        d = json.load(f)
    results = d["results"]
    tasks = list(results.keys())

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)

    # Left: in-distribution vs held-out accuracy per task
    ax = axes[0]
    x = np.arange(len(tasks))
    w = 0.35
    in_dist = [results[t]["in_dist_acc"]["lattice"] for t in tasks]
    held_out = [results[t]["held_out_acc"]["lattice"] for t in tasks]
    ax.bar(x - w/2, in_dist, w, label="in-distribution val",
           color="#27ae60", edgecolor="black", linewidth=0.5)
    ax.bar(x + w/2, held_out, w, label="held-out task (cross-task)",
           color="#c0392b", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("lattice-head accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_title("Multi-head rule-learner: lattice-head accuracy")
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for xi, (i, h) in enumerate(zip(in_dist, held_out)):
        ax.text(xi - w/2, i + 0.02, f"{i:.2f}", ha="center", fontsize=8, color="#27ae60")
        ax.text(xi + w/2, h + 0.02, f"{h:.2f}", ha="center", fontsize=8, color="#c0392b")

    # Right: failure distribution by task
    ax = axes[1]
    fl = d["failure_log"]
    by_task = {}
    for entry in fl:
        t = entry.get("task", "?")
        by_task[t] = by_task.get(t, 0) + 1
    tasks_f = list(by_task.keys())
    counts = list(by_task.values())
    colors = ["#c0392b", "#e67e22", "#3498db", "#9b59b6", "#27ae60"][:len(tasks_f)]
    ax.bar(tasks_f, counts, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_ylabel("failure count")
    ax.set_title(f"Failure distribution by task ({len(fl)} total failures logged)")
    for xi, c in enumerate(counts):
        ax.text(xi, c + 2, str(c), ha="center", fontsize=10, fontweight="bold")
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    fig.suptitle("Iteration 5: multi-head rule-learner results + failure analysis",
                 fontsize=13)
    fig.savefig(f"{OUT}/rule_learner.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/rule_learner.png")


def plot_failure_pattern():
    """Visualise the failure pattern: model defaults to majority class."""
    fig, ax = plt.subplots(figsize=(11, 5), constrained_layout=True)
    ax.axis("off")
    ax.text(0.5, 0.95, "Failure pattern: model defaults to majority class",
             ha="center", va="top", fontsize=13, fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.80,
             "The model achieves 67-87% in-distribution accuracy and 60-97% cross-task.\n"
             "But it fails consistently on odd-parity targets, predicting Leech_24 (the\n"
             "easiest layer) when the truth is Barnes_Wall_32 (a higher layer needed\n"
             "for odd parity).",
             ha="center", va="top", fontsize=10, color="#34495e", transform=ax.transAxes)
    # Diagram: input -> model -> wrong prediction
    boxes = [
        (0.10, 0.50, "INPUT\nodd-parity\nbinary grid", "#34495e"),
        (0.35, 0.50, "MODEL\n(multi-head)", "#16a085"),
        (0.60, 0.50, "PREDICTION\nLeech_24 (idx 0)\n[majority class]", "#c0392b"),
        (0.85, 0.50, "TRUTH\nBarnes_Wall_32 (idx 1)\n[higher layer needed]", "#27ae60"),
    ]
    for x, y, label, color in boxes:
        ax.text(x, y, label, ha="center", va="center", fontsize=10,
                bbox=dict(boxstyle="round,pad=0.4", facecolor=color, edgecolor="black", alpha=0.85),
                color="white", fontweight="bold", transform=ax.transAxes)
    # Arrows
    for x1, x2 in [(0.16, 0.29), (0.41, 0.54), (0.66, 0.79)]:
        ax.annotate("", xy=(x2, 0.50), xytext=(x1, 0.50),
                    arrowprops=dict(arrowstyle="->", lw=2, color="#7f8c8d"),
                    xycoords="axes fraction", textcoords="axes fraction")
    # Failure analysis
    ax.text(0.5, 0.25,
             "Development escalation requirements (from the failure log):",
             ha="center", va="top", fontsize=11, fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.15,
             "1. Parity discrimination: the binary input doesn't make parity easy to learn.\n"
             "   The model needs an explicit parity feature (sum of bits mod 2).\n"
             "2. Class-balanced loss: 50/50 parity distribution causes majority-class default.\n"
             "3. Better feature representation: the 24-bit input needs a learned embedding\n"
             "   that captures parity, n_ones, and codeword-structure simultaneously.",
             ha="center", va="top", fontsize=9.5, color="#34495e", transform=ax.transAxes,
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff5e5", edgecolor="#a68544"))
    fig.savefig(f"{OUT}/failure_pattern.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/failure_pattern.png")


if __name__ == "__main__":
    plot_field_punctures()
    plot_rule_learner()
    plot_failure_pattern()
    print("\nAll plots written to", OUT)
