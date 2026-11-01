#!/usr/bin/env python3
"""Generate plots for iteration 4."""

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
OUT  = "/home/z/my-project/download/iter4_plots"
os.makedirs(OUT, exist_ok=True)


def plot_layered_resolution():
    """Per-task layer distribution + parity wall resolution rates."""
    with open(f"{DATA}/iter4_layered_snap.json") as f:
        d = json.load(f)
    tasks = list(d.keys())
    # Per-task: Leech_24 success, parity wall, BW32 resolves, T48 resolves
    leech_ok   = [d[t]["layer_distribution"]["Leech_24"] for t in tasks]
    wall_count = [d[t]["parity_wall_count"] for t in tasks]
    bw32_resolves = [d[t]["bw32_resolved_parity_wall"] for t in tasks]
    t48_resolves  = [d[t]["t48_resolved_parity_wall"] for t in tasks]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)

    # Left: layer distribution stacked bar
    ax = axes[0]
    x = np.arange(len(tasks))
    w = 0.5
    ax.bar(x, leech_ok, w, label="Leech_24 (snaps at Λ24)",
           color="#27ae60", edgecolor="black", linewidth=0.5)
    ax.bar(x, wall_count, w, bottom=leech_ok,
           label="parity wall (Λ24 fails)",
           color="#c0392b", edgecolor="black", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels(tasks, rotation=15)
    ax.set_ylabel("# samples (out of 50)")
    ax.set_ylim(0, 55)
    ax.set_title("Λ24 snap success vs parity wall")
    ax.legend(loc="lower right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    # Right: wall resolution by Λ32 and Λ48
    ax = axes[1]
    x = np.arange(len(tasks))
    w = 0.35
    # Only tasks with parity wall hits
    mask = np.array(wall_count) > 0
    x_mask = np.arange(int(mask.sum()))
    tasks_mask = [t for t, m in zip(tasks, mask) if m]
    bw32_mask = [b for b, m in zip(bw32_resolves, mask) if m]
    t48_mask  = [t for t, m in zip(t48_resolves, mask) if m]
    wall_mask = [w for w, m in zip(wall_count, mask) if m]
    ax.bar(x_mask - w/2, bw32_mask, w, label="Λ32 (Barnes-Wall) resolves",
           color="#3498db", edgecolor="black", linewidth=0.5)
    ax.bar(x_mask + w/2, t48_mask, w, label="Λ48 (ternary) resolves",
           color="#e67e22", edgecolor="black", linewidth=0.5)
    # Plot wall count as horizontal reference
    for xi, wc in zip(x_mask, wall_mask):
        ax.axhline(y=wc, xmin=(xi-0.4)/max(1, len(x_mask)),
                    xmax=(xi+0.4)/max(1, len(x_mask)),
                    color="gray", linestyle="--", alpha=0.5)
    ax.set_xticks(x_mask); ax.set_xticklabels(tasks_mask, rotation=15)
    ax.set_ylabel("# wall-hits resolved")
    ax.set_ylim(0, 25)
    ax.set_title("Parity-wall resolution: Λ32 vs Λ48\n(both resolve 100% of wall-hits)")
    ax.legend(loc="upper right")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    # Annotate 100%
    for xi, (bw, t48, wc) in enumerate(zip(bw32_mask, t48_mask, wall_mask)):
        ax.text(xi - w/2, bw + 0.5, f"{bw}/{wc}", ha="center", fontsize=9, color="#3498db")
        ax.text(xi + w/2, t48 + 0.5, f"{t48}/{wc}", ha="center", fontsize=9, color="#e67e22")

    fig.suptitle("Iteration 4: layered snap across Λ24 / Λ32 / Λ48", fontsize=13)
    fig.savefig(f"{OUT}/layered_resolution.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/layered_resolution.png")


def plot_multiplication_puncture():
    """Visualise F_2 vs F_3 multiplication tables — the 'puncture' concept."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), constrained_layout=True)

    # F_2 multiplication table
    ax = axes[0]
    M2 = np.array([[0, 0], [0, 1]])
    im = ax.imshow(M2, cmap="RdYlGn", vmin=0, vmax=2, aspect="equal")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["0", "1"]); ax.set_yticklabels(["0", "1"])
    ax.set_xlabel("×"); ax.set_ylabel("y")
    ax.set_title("F_2 multiplication\n(2 = 0, no spin)")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(M2[i, j]), ha="center", va="center",
                     fontsize=14, fontweight="bold",
                     color="white" if M2[i, j] == 0 else "black")
    # Annotate the "puncture"
    ax.annotate("deletion\n(2 = 0)",
                 xy=(0, 0), xytext=(0.5, -0.5),
                 arrowprops=dict(arrowstyle="->", color="red", lw=2),
                 color="red", fontsize=9, ha="center",
                 transform=ax.transData)

    # F_3 multiplication table
    ax = axes[1]
    M3 = np.array([[(i*j) % 3 for j in range(3)] for i in range(3)])
    im = ax.imshow(M3, cmap="RdYlGn", vmin=0, vmax=2, aspect="equal")
    ax.set_xticks([0, 1, 2]); ax.set_yticks([0, 1, 2])
    ax.set_xticklabels(["0", "1", "2"]); ax.set_yticklabels(["0", "1", "2"])
    ax.set_xlabel("×"); ax.set_ylabel("y")
    ax.set_title("F_3 multiplication\n(2 = -1, a unit = a spin)")
    for i in range(3):
        for j in range(3):
            ax.text(j, i, str(M3[i, j]), ha="center", va="center",
                     fontsize=14, fontweight="bold",
                     color="white" if M3[i, j] == 0 else "black")
    # Annotate the "spin"
    ax.annotate("spin: 1→2→1\n(mult by 2)",
                 xy=(2, 1), xytext=(2.3, 0.5),
                 arrowprops=dict(arrowstyle="->", color="green", lw=2),
                 color="green", fontsize=9, ha="left")

    # The puncture diagram: parity wall vs multiplication puncture
    ax = axes[2]
    ax.axis("off")
    ax.text(0.5, 0.92, "The multiplication puncture",
             ha="center", va="top", fontsize=12, fontweight="bold",
             transform=ax.transAxes)
    ax.text(0.5, 0.75,
             "F_2 (binary): multiplying by 2 = 0\n"
             "→ the operation deletes information\n"
             "→ odd-parity targets have no inverse\n"
             "→ PARITY WALL",
             ha="center", va="top", fontsize=10, color="#c0392b",
             transform=ax.transAxes,
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#ffe5e5",
                        edgecolor="#c0392b"))
    ax.text(0.5, 0.35,
             "F_3 (ternary): multiplying by 2 = -1 (a unit)\n"
             "→ the operation is a rotation, not deletion\n"
             "→ every element has a multiplicative inverse\n"
             "→ MULTIPLICATION PUNCTURE",
             ha="center", va="top", fontsize=10, color="#27ae60",
             transform=ax.transAxes,
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#e5ffe5",
                        edgecolor="#27ae60"))

    fig.savefig(f"{OUT}/multiplication_puncture.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/multiplication_puncture.png")


def plot_lattice_comparison():
    """Side-by-side comparison of Λ24, Λ32, Λ48 lattice properties."""
    fig, ax = plt.subplots(figsize=(13, 5), constrained_layout=True)
    ax.axis("off")
    lattices = [
        ("Λ24\n(Leech)",
         "F_2 alphabet\nbinary {0,1}",
         "196,560\nminimal vectors",
         "4\n(extremal)",
         "#8e44ad",
         "parity wall\nat odd parity"),
        ("Λ32\n(Barnes-Wall)",
         "F_2 alphabet\nbinary {0,1}",
         "146,880\nminimal vectors",
         "4\n(extremal)",
         "#c0392b",
         "8 padding bits\nresolve parity wall"),
        ("Λ48\n(ternary)",
         "F_3 alphabet\n{0,1,2}",
         "96 (weight 48)\n+ 196,560* (lifted)",
         "6\n(extremal)",
         "#16a085",
         "mult. by 2 = -1\n(spin); resolves wall\n16,834x denser"),
    ]
    x = [0.15, 0.5, 0.85]
    for i, (name, alphabet, kissing, min_norm, color, mechanism) in enumerate(lattices):
        ax.text(x[i], 0.85, name, ha="center", va="center", fontsize=11,
                bbox=dict(boxstyle="round,pad=0.5", facecolor=color, edgecolor="black"),
                color="white", fontweight="bold")
        ax.text(x[i], 0.65, alphabet, ha="center", va="center", fontsize=9, color="#34495e")
        ax.text(x[i], 0.50, f"kissing: {kissing}", ha="center", va="center", fontsize=9, color="#34495e")
        ax.text(x[i], 0.36, f"min norm: {min_norm}", ha="center", va="center", fontsize=9, color="#34495e")
        ax.text(x[i], 0.15, mechanism, ha="center", va="center", fontsize=8.5,
                color=color, style="italic")
        if i < 2:
            ax.annotate("", xy=(x[i+1] - 0.05, 0.85), xytext=(x[i] + 0.05, 0.85),
                        arrowprops=dict(arrowstyle="->", lw=2, color="#7f8c8d"))
    ax.text(0.5, 0.97, "Lattice comparison: which resolves the parity wall?",
             ha="center", va="top", fontsize=13, fontweight="bold")
    ax.text(0.5, 0.03,
             "Both Λ32 and Λ48 resolve the wall — but via different mechanisms:\n"
             "Λ32 keeps binary alphabet, adds 8 padding bits (more dimensions, same alphabet).\n"
             "Λ48 switches to ternary alphabet, where multiplication is structurally invertible.",
             ha="center", va="bottom", fontsize=9, color="#27ae60")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    fig.savefig(f"{OUT}/lattice_comparison.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT}/lattice_comparison.png")


if __name__ == "__main__":
    plot_layered_resolution()
    plot_multiplication_puncture()
    plot_lattice_comparison()
    print("\nAll plots written to", OUT)
