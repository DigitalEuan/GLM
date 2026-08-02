"""
E7 visualizations + final encoding specification document.
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

try:
    fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
except Exception:
    pass
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import ubp_kb_loader as kb
import encoding_spec as es
from e7_encoding_spec_study import score_dual_encoding, compute_dual_encoding_metrics
from e1_e2_e3_kb_sweep import KNOWN_PAIRS

OUT_DIR = Path("/home/z/my-project/download")

ROW_NAMES = ["Reality", "Info", "Activation", "Potential"]


def plot_ablation_results():
    """Bar chart of per-bit ablation impact."""
    with open(OUT_DIR / "e7_encoding_spec_study.json") as f:
        data = json.load(f)
    ablation = data["ablation"]["ablation_results"]

    # Sort by bit index
    ablation.sort(key=lambda x: x["bit"])

    fig, ax = plt.subplots(figsize=(14, 6), constrained_layout=True)
    bits = [r["bit"] for r in ablation]
    changes = [r["score_change"] for r in ablation]
    colors = ["tab:red" if c < -0.05 else "tab:orange" if c < -0.02
              else "tab:gray" if abs(c) < 0.02 else "tab:green"
              for c in changes]

    bars = ax.bar(bits, changes, color=colors, edgecolor="black", linewidth=0.5)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axhline(-0.05, color="red", linestyle=":", alpha=0.5, label="significant drop (|Δ| > 0.05)")
    ax.axhline(-0.02, color="orange", linestyle=":", alpha=0.5, label="moderate drop (|Δ| > 0.02)")

    # Annotate row boundaries
    for r in range(4):
        ax.axvline(r * 6 - 0.5, color="blue", linestyle="--", alpha=0.3)
        ax.text(r * 6 + 2.5, max(changes) * 0.9, ROW_NAMES[r],
                ha="center", fontsize=10, color="blue", fontweight="bold")

    ax.set_xlabel("Bit index (0-23)", fontsize=10)
    ax.set_ylabel("Score change when bit is flipped", fontsize=10)
    ax.set_title("E7 — Per-bit Ablation Study (KB-hardened Layer 1)\n"
                 "Negative bars = bit is IMPORTANT (flipping it hurts the score)\n"
                 "Positive bars = bit is HARMFUL (flipping it helps)",
                 fontsize=11, fontweight="bold")
    ax.set_xticks(range(0, 24))
    ax.set_xticklabels([str(i) for i in range(24)], fontsize=8)
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(axis="y", alpha=0.3)

    out = OUT_DIR / "e7_ablation_results.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


def plot_permutation_results():
    """Bar chart of all 24 permutation scores."""
    with open(OUT_DIR / "e7_encoding_spec_study.json") as f:
        data = json.load(f)
    results = data["permutation_study"]["all_results"]

    # Sort by overall score
    results.sort(key=lambda x: -x["score"]["overall_score"])

    fig, axes = plt.subplots(1, 2, figsize=(16, 7), constrained_layout=True)

    labels = [f"{r['property_order'][0][:3]}/{r['property_order'][1][:3]}/"
              f"{r['property_order'][2][:3]}/{r['property_order'][3][:3]}"
              for r in results]
    overall = [r["score"]["overall_score"] for r in results]
    r_be = [r["score"]["multiple_r_be"] for r in results]
    r_dh = [r["score"]["multiple_r_dh"] for r in results]

    x = np.arange(len(results))
    width = 0.35

    ax = axes[0]
    ax.bar(x - width/2, r_be, width, label="Multiple R (BE)", color="tab:blue")
    ax.bar(x + width/2, r_dh, width, label="Multiple R (ΔH)", color="tab:orange")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=70, fontsize=7)
    ax.set_ylabel("Multiple R")
    ax.set_title("All 24 property-to-row permutations\n(sorted by overall score)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    ax.axhline(0.57, color="blue", linestyle=":", alpha=0.5)
    ax.axhline(0.49, color="orange", linestyle=":", alpha=0.5)

    # Highlight top 3
    for i in range(3):
        ax.annotate(f"#{i+1}", (i, max(r_be[i], r_dh[i]) + 0.02),
                    ha="center", fontsize=9, fontweight="bold", color="red")

    # Plot 2: Top 5 in detail
    ax = axes[1]
    top5 = results[:5]
    labels5 = [f"{r['property_order'][0][:3]}/{r['property_order'][1][:3]}/"
               f"{r['property_order'][2][:3]}/{r['property_order'][3][:3]}"
               for r in top5]
    overall5 = [r["score"]["overall_score"] for r in top5]
    r_be5 = [r["score"]["multiple_r_be"] for r in top5]
    r_dh5 = [r["score"]["multiple_r_dh"] for r in top5]
    cv_be5 = [r["score"]["cv_multiple_r_be"] for r in top5]
    cv_dh5 = [r["score"]["cv_multiple_r_dh"] for r in top5]

    x5 = np.arange(len(top5))
    width = 0.18
    ax.bar(x5 - 2*width, r_be5, width, label="R (BE)", color="tab:blue")
    ax.bar(x5 - width, r_dh5, width, label="R (ΔH)", color="tab:orange")
    ax.bar(x5, cv_be5, width, label="CV R (BE)", color="tab:cyan")
    ax.bar(x5 + width, cv_dh5, width, label="CV R (ΔH)", color="tab:red")
    ax.set_xticks(x5)
    ax.set_xticklabels(labels5, fontsize=8)
    ax.set_ylabel("R / CV R")
    ax.set_title("Top 5 permutations — full vs cross-validated\n"
                 "(large gap = overfitting; small gap = generalizes)")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)

    fig.suptitle("E7 — Property-to-Row Permutation Study",
                 fontsize=13, fontweight="bold")
    out = OUT_DIR / "e7_permutation_results.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


def plot_composite_prediction():
    """Scatter of predicted vs actual bond energy using the best permutation."""
    with open(OUT_DIR / "e7_encoding_spec_study.json") as f:
        data = json.load(f)

    best_spec = es.EncodingSpec(
        name="best",
        prop_set=["Z", "Valence_e", "EN", "Rad"],  # best permutation
        row_assignment=[0, 1, 2, 3],
        scaling={
            "Z": "identity",
            "Rad": "div4",
            "EN": "en_x15",
            "Valence_e": "valence_redundant",
        },
        leech_scheme="A_basis",
        mog_cell_w=4.0,
        mog_cell_h=4.0,
        mog_z_offset=7.0,
        mog_seed_b=10,
    )

    # Compute all metrics
    records = []
    for sym_a, sym_b, be, dh, label in KNOWN_PAIRS:
        ea = kb.get_element(sym_a)
        eb = kb.get_element(sym_b)
        if ea is None or eb is None:
            continue
        m = compute_dual_encoding_metrics(best_spec, sym_a, sym_b)
        records.append({
            "pair": f"{sym_a}+{sym_b}",
            "be": be,
            "dh": dh if dh is not None and dh != 0 else None,
            **m,
        })

    # Fit regression on bond energy
    X = np.array([[1, r["scn_overlap_d"], r["sa_b_max_3d_kb"], r["aa_normal_dot_kb"]]
                   for r in records])
    y_be = np.array([r["be"] for r in records])
    beta, _, _, _ = np.linalg.lstsq(X, y_be, rcond=None)
    y_pred = X @ beta

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)

    # Bond energy
    ax = axes[0]
    ax.scatter(y_pred, y_be, c="tab:blue", s=70, edgecolor="black", alpha=0.8)
    for i, r in enumerate(records):
        ax.annotate(r["pair"], (y_pred[i], y_be[i]),
                    fontsize=7, xytext=(4, 3), textcoords="offset points")
    # 1:1 line
    lims = [min(min(y_pred), min(y_be)) - 50, max(max(y_pred), max(y_be)) + 50]
    ax.plot(lims, lims, "r--", alpha=0.6, label="perfect prediction")
    ax.set_xlabel("Predicted bond energy (kJ/mol)")
    ax.set_ylabel("Actual bond energy (kJ/mol)")
    r_val = statistics.correlation(list(y_pred), list(y_be))
    ax.set_title(f"Bond Energy Prediction\n"
                 f"R = {r_val:.4f}, R² = {r_val**2:.4f} (n={len(records)})",
                 fontsize=11, fontweight="bold")
    ax.legend()
    ax.grid(alpha=0.3)

    # ΔH prediction
    dh_records = [r for r in records if r["dh"] is not None]
    X_dh = np.array([[1, r["scn_overlap_d"], r["sa_b_max_3d_kb"], r["aa_normal_dot_kb"]]
                      for r in dh_records])
    y_dh = np.array([r["dh"] for r in dh_records])
    beta_dh, _, _, _ = np.linalg.lstsq(X_dh, y_dh, rcond=None)
    y_pred_dh = X_dh @ beta_dh

    ax = axes[1]
    ax.scatter(y_pred_dh, y_dh, c="tab:orange", s=70, edgecolor="black", alpha=0.8)
    for i, r in enumerate(dh_records):
        ax.annotate(r["pair"], (y_pred_dh[i], y_dh[i]),
                    fontsize=7, xytext=(4, 3), textcoords="offset points")
    lims = [min(min(y_pred_dh), min(y_dh)) - 100, max(max(y_pred_dh), max(y_dh)) + 100]
    ax.plot(lims, lims, "r--", alpha=0.6, label="perfect prediction")
    ax.set_xlabel("Predicted ΔH (kJ/mol)")
    ax.set_ylabel("Actual ΔH (kJ/mol)")
    r_val_dh = statistics.correlation(list(y_pred_dh), list(y_dh))
    ax.set_title(f"ΔH Formation Prediction\n"
                 f"R = {r_val_dh:.4f}, R² = {r_val_dh**2:.4f} (n={len(dh_records)})",
                 fontsize=11, fontweight="bold")
    ax.legend()
    ax.grid(alpha=0.3)

    fig.suptitle("E7 — Best Permutation Composite Prediction\n"
                 "Encoding: [Z, Valence_e, EN, Rad] + KB-hardened Layer 1",
                 fontsize=12, fontweight="bold")
    out = OUT_DIR / "e7_composite_prediction.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


def main():
    print("=" * 72)
    print("E7 VISUALIZATIONS")
    print("=" * 72)
    plot_ablation_results()
    plot_permutation_results()
    plot_composite_prediction()


if __name__ == "__main__":
    main()
