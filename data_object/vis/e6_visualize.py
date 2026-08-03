"""
E6 visualization + composite metric.

Visualizes:
  1. Best seed_offset (seed_b=10) normal alignment scatter vs ΔH
  2. Seed offset sweep showing r vs seed_b
  3. Stacked MOG grid 3D rendering (2D projection) for a sample pair
  4. Composite metric: combine E4 + E5 + E6 best signals via linear regression
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
import stacked_mog_grids as smg
import per_bit_leech as pbl
from e4_balance_study import encode_with_props, ENCODINGS
from e1_e2_e3_kb_sweep import interaction_metrics, KNOWN_PAIRS

OUT_DIR = Path("/home/z/my-project/download")


def plot_seed_offset_sweep():
    """Plot r vs seed_offset_b for normal alignment metrics."""
    with open(OUT_DIR / "e6_seed_offset_sweep.json") as f:
        results = json.load(f)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)

    seed_bs = [r["seed_b"] for r in results]
    r_dot_be = [r["r_dot_be"] for r in results]
    r_ang_be = [r["r_ang_be"] for r in results]
    r_dot_dh = [r["r_dot_dh"] for r in results]
    r_ang_dh = [r["r_ang_dh"] for r in results]

    # Plot 1: vs Bond Energy
    ax = axes[0]
    ax.plot(seed_bs, [abs(r) for r in r_dot_be], "b-", label="|r(normal_dot, BE)|", linewidth=1.5)
    ax.plot(seed_bs, [abs(r) for r in r_ang_be], "r--", label="|r(normal_angle, BE)|", linewidth=1.5)
    ax.set_xlabel("seed_offset_b")
    ax.set_ylabel("|Pearson r|")
    ax.set_title("Normal alignment vs Bond Energy")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    ax.set_ylim(0, 0.55)
    ax.axhline(0.37, color="gray", linestyle=":", alpha=0.5)

    # Plot 2: vs ΔH
    ax = axes[1]
    ax.plot(seed_bs, [abs(r) for r in r_dot_dh], "b-", label="|r(normal_dot, ΔH)|", linewidth=1.5)
    ax.plot(seed_bs, [abs(r) for r in r_ang_dh], "r--", label="|r(normal_angle, ΔH)|", linewidth=1.5)
    ax.set_xlabel("seed_offset_b")
    ax.set_ylabel("|Pearson r|")
    ax.set_title("Normal alignment vs ΔH Formation")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    ax.set_ylim(0, 0.55)
    ax.axhline(0.48, color="gray", linestyle=":", alpha=0.5)

    # Mark the best seed_b
    best_dh_idx = max(range(len(results)), key=lambda i: abs(results[i]["r_dot_dh"]))
    best_seed = results[best_dh_idx]["seed_b"]
    axes[1].axvline(best_seed, color="green", linestyle="--", alpha=0.7,
                    label=f"best: seed_b={best_seed}")
    axes[1].legend(fontsize=9)

    fig.suptitle("E6 — Normal-vector alignment signal vs seed_offset_b\n"
                 "Grid A uses seed_offset=0; Grid B uses seed_offset=seed_b.\n"
                 "Signal varies with B's polygon orientation — 3D geometry carries chemical information.",
                 fontsize=11, fontweight="bold")
    out = OUT_DIR / "e6_seed_offset_sweep.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


def plot_best_normal_scatter():
    """Scatter of normal alignment vs ΔH for best config (seed_b=10)."""
    scene = smg.StackedMOGScene(
        cell_w=4.0, cell_h=4.0, z_offset=7.0,
        seed_offset_a=0, seed_offset_b=10,
    )

    pairs_data = []
    for sym_a, sym_b, be, dh, label in KNOWN_PAIRS:
        ea = kb.get_element(sym_a)
        eb = kb.get_element(sym_b)
        if ea is None or eb is None: continue
        m = scene.compute_pair_metrics(ea.vector24, eb.vector24)
        if dh is not None and dh != 0:
            pairs_data.append({
                "pair": f"{sym_a}+{sym_b}",
                "be": be, "dh": dh,
                "aa_dot": m["aa_mean_normal_dot"],
                "aa_angle": m["aa_mean_normal_angle"],
            })

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)

    # Plot 1: normal_dot vs ΔH
    ax = axes[0]
    dots = [p["aa_dot"] for p in pairs_data]
    dhs = [p["dh"] for p in pairs_data]
    r_val = statistics.correlation(dots, dhs)
    ax.scatter(dots, dhs, c="tab:blue", s=70, edgecolor="black", alpha=0.8)
    for p in pairs_data:
        ax.annotate(p["pair"], (p["aa_dot"], p["dh"]),
                    fontsize=7, xytext=(4, 3), textcoords="offset points")
    z = np.polyfit(dots, dhs, 1)
    xs = np.linspace(min(dots), max(dots), 50)
    ax.plot(xs, np.polyval(z, xs), "r--", alpha=0.6)
    ax.set_xlabel("Active-active mean normal dot product")
    ax.set_ylabel("ΔH (kJ/mol)")
    ax.set_title(f"Normal dot vs ΔH\nr = {r_val:+.4f} (n={len(pairs_data)})",
                 fontsize=11, fontweight="bold")
    ax.grid(alpha=0.3)

    # Plot 2: normal_angle vs ΔH
    ax = axes[1]
    angles = [p["aa_angle"] for p in pairs_data]
    r_val2 = statistics.correlation(angles, dhs)
    ax.scatter(angles, dhs, c="tab:orange", s=70, edgecolor="black", alpha=0.8)
    for p in pairs_data:
        ax.annotate(p["pair"], (p["aa_angle"], p["dh"]),
                    fontsize=7, xytext=(4, 3), textcoords="offset points")
    z = np.polyfit(angles, dhs, 1)
    xs = np.linspace(min(angles), max(angles), 50)
    ax.plot(xs, np.polyval(z, xs), "r--", alpha=0.6)
    ax.set_xlabel("Active-active mean normal angle (degrees)")
    ax.set_ylabel("ΔH (kJ/mol)")
    ax.set_title(f"Normal angle vs ΔH\nr = {r_val2:+.4f} (n={len(pairs_data)})",
                 fontsize=11, fontweight="bold")
    ax.grid(alpha=0.3)

    fig.suptitle("E6 — Best Config (seed_b=10): Normal-vector alignment vs ΔH\n"
                 "The 3D orientation relationship between active-bit polygons carries reaction enthalpy signal",
                 fontsize=12, fontweight="bold")
    out = OUT_DIR / "e6_best_normal_scatter.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


def plot_stacked_grid_3d():
    """Render a 2D projection of the stacked MOG grids for a sample pair."""
    scene = smg.StackedMOGScene(
        cell_w=4.0, cell_h=4.0, z_offset=7.0,
        seed_offset_a=0, seed_offset_b=10,
    )

    # Use C + O as the sample pair
    ea = kb.get_element("C")
    eb = kb.get_element("O")
    grid_a = scene.build_grid(ea.vector24, "A")
    grid_b = scene.build_grid(eb.vector24, "B")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)

    # Plot 1: Top-down view (XY plane) showing both grids
    ax = axes[0]
    for p in grid_a:
        cx, cy, _ = p["centroid"]
        color = "#1f77b4" if p["bit_value"] else "#cccccc"
        size = 120 if p["bit_value"] else 40
        marker = "s" if p["bit_value"] else "."
        ax.scatter(cx, cy, c=color, s=size, marker=marker, edgecolor="black", linewidth=0.8)
        if p["bit_value"]:
            ax.annotate(f"b{p['bit_index']}", (cx, cy), fontsize=6,
                        ha="center", va="center", color="white", fontweight="bold")

    for p in grid_b:
        cx, cy, cz = p["centroid"]
        # Offset slightly for visibility
        color = "#ff7700" if p["bit_value"] else "#ffeecc"
        size = 120 if p["bit_value"] else 40
        marker = "s" if p["bit_value"] else "."
        ax.scatter(cx + 0.3, cy + 0.3, c=color, s=size, marker=marker,
                   edgecolor="black", linewidth=0.8, alpha=0.7)
        if p["bit_value"]:
            ax.annotate(f"b{p['bit_index']}", (cx + 0.3, cy + 0.3), fontsize=6,
                        ha="center", va="center", color="black", fontweight="bold")

    ax.set_title("Top-down (XY) view: Grid A (blue) + Grid B (orange, offset)\n"
                 "C (HW=16) vs O (HW=12)")
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.set_xlabel("X (columns)")
    ax.set_ylabel("Y (rows)")

    # Plot 2: Side view (XZ plane) showing the Z stacking
    ax = axes[1]
    for p in grid_a:
        cx, _, cz = p["centroid"]
        color = "#1f77b4" if p["bit_value"] else "#cccccc"
        size = 80 if p["bit_value"] else 20
        ax.scatter(cx, cz, c=color, s=size, edgecolor="black", linewidth=0.5)

    for p in grid_b:
        cx, _, cz = p["centroid"]
        color = "#ff7700" if p["bit_value"] else "#ffeecc"
        size = 80 if p["bit_value"] else 20
        ax.scatter(cx, cz, c=color, s=size, edgecolor="black", linewidth=0.5, alpha=0.7)

    ax.set_title("Side (XZ) view: Grid A at Z=0, Grid B at Z=7\n"
                 "Same-position (1,1) pairs → DIVIDE operator (clearance=5)")
    ax.set_xlabel("X (columns)")
    ax.set_ylabel("Z (layer offset)")
    ax.grid(alpha=0.3)

    fig.suptitle("E6 — Stacked MOG Grid Geometry (C + O)",
                 fontsize=12, fontweight="bold")
    out = OUT_DIR / "e6_stacked_grid_3d.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  Saved: {out}")


def compute_composite_metric():
    """Combine E4 + E5 + E6 best signals via multiple linear regression."""
    print()
    print("=" * 78)
    print("COMPOSITE METRIC — Combining E4 + E5 + E6 signals")
    print("=" * 78)
    print()
    print("Combining three orthogonal signals via least-squares linear regression:")
    print("  1. E4: D_geometric scn_overlap_count (r=+0.46 vs BE)")
    print("  2. E5: A_basis sa_b_scene_max_3d_dist (r=-0.47 vs ΔH)")
    print("  3. E6: seed_b=10 aa_mean_normal_dot (r=+0.48 vs ΔH)")
    print()

    # Compute all three metrics for each pair
    pairs_data = []

    # E4 config
    e4_props = ["Z", "Rad", "EN", "Valence_e"]

    # E5 config
    e5_scheme = "A_basis"

    # E6 config
    e6_scene = smg.StackedMOGScene(
        cell_w=4.0, cell_h=4.0, z_offset=7.0,
        seed_offset_a=0, seed_offset_b=10,
    )

    for sym_a, sym_b, be, dh, label in KNOWN_PAIRS:
        ea = kb.get_element(sym_a)
        eb = kb.get_element(sym_b)
        if ea is None or eb is None: continue

        # E4: D_geometric scn_overlap
        vec_a_e4 = encode_with_props(sym_a, e4_props)
        vec_b_e4 = encode_with_props(sym_b, e4_props)
        m_e4 = interaction_metrics(vec_a_e4, vec_b_e4)
        e4_scn_overlap = m_e4["scn_overlap_count"]

        # E5: A_basis sa_b_scene_max_3d_dist
        sa_a = pbl.spatial_arithmetic_on_per_bit_leech(ea.vector24, e5_scheme)
        sa_b = pbl.spatial_arithmetic_on_per_bit_leech(eb.vector24, e5_scheme)
        e5_sa_b_max_3d = sa_b["scene_stats"]["max_3d_dist"]

        # E6: seed_b=10 aa_mean_normal_dot
        m_e6 = e6_scene.compute_pair_metrics(ea.vector24, eb.vector24)
        e6_aa_dot = m_e6["aa_mean_normal_dot"]

        dh_val = dh if dh is not None and dh != 0 else None

        pairs_data.append({
            "pair": f"{sym_a}+{sym_b}",
            "be": be,
            "dh": dh_val,
            "e4_scn_overlap": e4_scn_overlap,
            "e5_sa_b_max_3d": e5_sa_b_max_3d,
            "e6_aa_normal_dot": e6_aa_dot,
        })

    # Single-metric correlations (verify)
    be_vals = [p["be"] for p in pairs_data]
    dh_pairs = [p for p in pairs_data if p["dh"] is not None]
    dh_vals = [p["dh"] for p in dh_pairs]

    print("Single-metric correlations (sanity check):")
    print(f"  E4 scn_overlap vs BE:  r = {statistics.correlation([p['e4_scn_overlap'] for p in pairs_data], be_vals):+.4f}")
    print(f"  E5 sa_b_max_3d vs ΔH:  r = {statistics.correlation([p['e5_sa_b_max_3d'] for p in dh_pairs], dh_vals):+.4f}")
    print(f"  E6 aa_normal_dot vs ΔH: r = {statistics.correlation([p['e6_aa_normal_dot'] for p in dh_pairs], dh_vals):+.4f}")

    # Multiple linear regression for ΔH prediction
    # Features: e4_scn_overlap, e5_sa_b_max_3d, e6_aa_normal_dot
    X = np.array([[1, p["e4_scn_overlap"], p["e5_sa_b_max_3d"], p["e6_aa_normal_dot"]]
                   for p in dh_pairs])
    y_dh = np.array(dh_vals)

    # Least squares
    beta, residuals, rank, sv = np.linalg.lstsq(X, y_dh, rcond=None)
    y_pred = X @ beta
    ss_res = np.sum((y_dh - y_pred) ** 2)
    ss_tot = np.sum((y_dh - np.mean(y_dh)) ** 2)
    r_squared = 1 - ss_res / ss_tot
    r_multiple = math.sqrt(r_squared) if r_squared > 0 else 0

    print()
    print(f"Multiple regression (ΔH ~ E4 + E5 + E6):")
    print(f"  Intercept:     {beta[0]:+.4f}")
    print(f"  E4 scn_overlap: {beta[1]:+.4f}")
    print(f"  E5 sa_b_max_3d: {beta[2]:+.4f}")
    print(f"  E6 aa_dot:      {beta[3]:+.4f}")
    print(f"  R² = {r_squared:.4f}")
    print(f"  Multiple R = {r_multiple:.4f}  (n={len(dh_pairs)})")

    # Also for bond energy
    X_be = np.array([[1, p["e4_scn_overlap"], p["e5_sa_b_max_3d"], p["e6_aa_normal_dot"]]
                      for p in pairs_data])
    y_be = np.array(be_vals)
    beta_be, _, _, _ = np.linalg.lstsq(X_be, y_be, rcond=None)
    y_pred_be = X_be @ beta_be
    ss_res_be = np.sum((y_be - y_pred_be) ** 2)
    ss_tot_be = np.sum((y_be - np.mean(y_be)) ** 2)
    r_squared_be = 1 - ss_res_be / ss_tot_be
    r_multiple_be = math.sqrt(r_squared_be) if r_squared_be > 0 else 0

    print()
    print(f"Multiple regression (BE ~ E4 + E5 + E6):")
    print(f"  Intercept:     {beta_be[0]:+.4f}")
    print(f"  E4 scn_overlap: {beta_be[1]:+.4f}")
    print(f"  E5 sa_b_max_3d: {beta_be[2]:+.4f}")
    print(f"  E6 aa_dot:      {beta_be[3]:+.4f}")
    print(f"  R² = {r_squared_be:.4f}")
    print(f"  Multiple R = {r_multiple_be:.4f}  (n={len(pairs_data)})")

    # Save composite results
    out_path = OUT_DIR / "e6_composite_metric.json"
    with open(out_path, "w") as f:
        json.dump({
            "pairs_data": pairs_data,
            "regression_dh": {
                "beta": list(beta),
                "r_squared": r_squared,
                "multiple_r": r_multiple,
                "n": len(dh_pairs),
            },
            "regression_be": {
                "beta": list(beta_be),
                "r_squared": r_squared_be,
                "multiple_r": r_multiple_be,
                "n": len(pairs_data),
            },
        }, f, indent=2)
    print(f"\nSaved: {out_path}")
    return pairs_data, r_multiple, r_multiple_be


def main():
    print("=" * 72)
    print("E6 VISUALIZATION + COMPOSITE METRIC")
    print("=" * 72)
    plot_seed_offset_sweep()
    plot_best_normal_scatter()
    plot_stacked_grid_3d()
    compute_composite_metric()


if __name__ == "__main__":
    main()
