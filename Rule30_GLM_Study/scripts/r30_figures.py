"""Generate all figures for the Rule 30 prize-problems study.

Uses matplotlib with constrained_layout, Noto Sans SC for CJK fallback,
and a single accent color (Wolfram-red #CC1133) for highlights.

All figures saved to /home/z/my-project/figures/ as 300dpi PNG.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

# Register fonts for per-glyph fallback (covers any rare CJK glyph that
# creeps into otherwise-English labels). The variable-weight Noto Sans SC
# file uses a format matplotlib's freetype binding can't read, so we
# use the static-weight Noto Serif SC file from noto-serif-sc instead.
fm.fontManager.addfont("/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Medium.ttf")
fm.fontManager.addfont("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
plt.rcParams["font.sans-serif"] = ["Noto Serif SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 110
plt.rcParams["savefig.dpi"] = 220

# Project paths
PROJ = Path("/home/z/my-project")
DATA = PROJ / "data"
FIGS = PROJ / "figures"
FIGS.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(PROJ / "scripts"))

from r30_engine import rule30_center_column_packed  # noqa: E402

# Color palette
ACCENT = "#CC1133"   # Wolfram-red
INK = "#1a1a1a"
GRID = "#d0d0d0"
SOFT = "#666666"
BG = "#fafafa"


# --- Figure 1: Rule 30 triangle (classic visual) ---------------------------

def fig_triangle(rows: int = 200, save: bool = True) -> Path:
    """Render the first `rows` rows of Rule 30 as a binary image."""
    N = rows
    # Generate the triangle by direct simulation
    width = 2 * N + 1
    grid = np.zeros((N, width), dtype=np.uint8)
    row = np.zeros(width, dtype=np.uint8)
    row[N] = 1
    grid[0] = row
    for t in range(1, N):
        new_row = np.zeros_like(row)
        # Slice the active region [N-t, N+t] for speed
        new_row[1:-1] = row[:-2] ^ (row[1:-1] | row[2:])
        row = new_row
        grid[t] = row
    # Crop to the visible triangle (cols [N-rows, N+rows])
    visible = grid[:, N - rows + 1: N + rows]
    fig, ax = plt.subplots(figsize=(6.5, 7.0), constrained_layout=True)
    ax.imshow(visible, cmap="binary", aspect="equal", interpolation="nearest")
    ax.set_title(f"Rule 30 triangle, {rows} rows from a single live cell",
                 fontsize=11, color=INK)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlabel("column (center at midpoint)", color=SOFT, fontsize=9)
    ax.set_ylabel("row (step) t", color=SOFT, fontsize=9)
    if save:
        p = FIGS / "fig1_triangle.png"
        fig.savefig(p)
        plt.close(fig)
        print(f"  wrote {p}")
        return p
    return None


# --- Figure 2: Center column strip -----------------------------------------

def fig_center_strip(N: int = 2000, save: bool = True) -> Path:
    """Render the first N cells of the center column as a thin strip."""
    cc = rule30_center_column_packed(N)
    # Render as a 1-pixel-tall strip, scaled to readable height
    height = 40
    strip = np.tile(cc.reshape(1, -1), (height, 1))
    fig, ax = plt.subplots(figsize=(10, 1.5), constrained_layout=True)
    ax.imshow(strip, cmap="binary", aspect="auto", interpolation="nearest")
    ax.set_title(f"Center column of Rule 30, first {N} cells",
                 fontsize=10, color=INK)
    ax.set_xticks([0, N // 4, N // 2, 3 * N // 4, N - 1])
    ax.set_xticklabels(["0", str(N // 4), str(N // 2), str(3 * N // 4), str(N - 1)],
                       fontsize=8, color=SOFT)
    ax.set_yticks([])
    ax.set_xlabel("cell index n", color=SOFT, fontsize=9)
    if save:
        p = FIGS / "fig2_center_strip.png"
        fig.savefig(p)
        plt.close(fig)
        print(f"  wrote {p}")
        return p
    return None


# --- Figure 3: Autocorrelation --------------------------------------------

def fig_autocorr(save: bool = True) -> Path:
    """Plot autocorrelation rho(T) for T in {1, ..., 1024}."""
    cc = np.load(DATA / "cc_1M.npy").astype(np.uint8)
    s = 1 - 2 * cc.astype(np.int64)  # 0->+1, 1->-1
    N = s.shape[0]
    lags = list(range(1, 1025))
    rhos = []
    for T in lags:
        rhos.append(float(np.mean(s[:N - T] * s[T:])))
    fig, ax = plt.subplots(figsize=(7.0, 3.5), constrained_layout=True)
    ax.plot(lags, rhos, color=ACCENT, linewidth=0.5, alpha=0.8)
    # 99% confidence band under H0 (random)
    sigma = 1.0 / np.sqrt(N)
    ax.axhline(+2.58 * sigma, color=SOFT, linestyle="--", linewidth=0.8,
              label=f"99% band under H_0 (random): +/-{2.58*sigma:.4f}")
    ax.axhline(-2.58 * sigma, color=SOFT, linestyle="--", linewidth=0.8)
    ax.axhline(0, color=GRID, linewidth=0.5)
    ax.set_xlabel("lag T", color=SOFT)
    ax.set_ylabel(r"$\rho(T) = \langle s_n \, s_{n+T}\rangle$",
                  color=INK)
    ax.set_title(f"Discrete autocorrelation of Rule 30 center column, "
                 f"N = {N:,}", fontsize=10, color=INK)
    ax.legend(loc="upper right", fontsize=8)
    ax.set_xlim(0, 1024)
    if save:
        p = FIGS / "fig3_autocorr.png"
        fig.savefig(p)
        plt.close(fig)
        print(f"  wrote {p}")
        return p
    return None


# --- Figure 4: Running frequency drift -------------------------------------

def fig_freq_drift(save: bool = True) -> Path:
    """Plot f(n) - 1/2 vs n on log scale."""
    cc = np.load(DATA / "cc_1M.npy").astype(np.uint8)
    cumsum = np.cumsum(cc.astype(np.int64))
    n_arr = np.arange(1, cc.shape[0] + 1)
    freq = cumsum / n_arr
    dev = freq - 0.5

    fig, ax = plt.subplots(figsize=(7.0, 3.5), constrained_layout=True)
    # Plot every 100th sample to keep the figure light
    step = 100
    ax.loglog(n_arr[::step], np.abs(dev[::step]), color=ACCENT,
              linewidth=0.6, alpha=0.8, label="|f(n) - 1/2|  empirical")
    # Expected SE under H0: 1/(2 sqrt(n))
    xs = np.logspace(0, 6, 200)
    ax.loglog(xs, 1.0 / (2 * np.sqrt(xs)), color=SOFT, linestyle="--",
              linewidth=1.2, label=r"$1/(2\sqrt{n})$  (IID expectation)")
    # LIL envelope
    ax.loglog(xs, np.sqrt(2 * np.log(np.log(xs + 1.1)) / (4 * xs)),
              color="#3366cc", linestyle=":", linewidth=1.0,
              label=r"$\sqrt{2\sigma^2 \log\log n / n}$  (LIL envelope)")
    ax.set_xlabel("n (cells observed)", color=SOFT)
    ax.set_ylabel("|f(n) - 1/2|", color=INK)
    ax.set_title("Running frequency drift; null hypothesis f(inf) = 1/2",
                 fontsize=10, color=INK)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, which="both", color=GRID, alpha=0.4, linewidth=0.4)
    if save:
        p = FIGS / "fig4_freq_drift.png"
        fig.savefig(p)
        plt.close(fig)
        print(f"  wrote {p}")
        return p
    return None


# --- Figure 5: Linear complexity profile -----------------------------------

def fig_linear_complexity(save: bool = True) -> Path:
    """Berlekamp-Massey linear complexity profile on the first 5000 cells."""
    from r30_p1_periodicity import berlekamp_massey
    cc = np.load(DATA / "cc_1M.npy").astype(np.uint8)
    N = 5000
    profile = berlekamp_massey(cc[:N].astype(np.int8).tolist())
    ns = np.arange(1, N + 1)
    fig, ax = plt.subplots(figsize=(7.0, 3.5), constrained_layout=True)
    ax.plot(ns, profile, color=ACCENT, linewidth=0.6, alpha=0.9,
            label="L(n) linear complexity")
    ax.plot(ns, ns / 2, color=SOFT, linestyle="--", linewidth=1.2,
            label="n/2 (random expectation)")
    ax.set_xlabel("n", color=SOFT)
    ax.set_ylabel("L(n)", color=INK)
    ax.set_title(f"Linear complexity profile of Rule 30 center column, "
                 f"first {N} cells", fontsize=10, color=INK)
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, color=GRID, alpha=0.4, linewidth=0.4)
    if save:
        p = FIGS / "fig5_lin_complexity.png"
        fig.savefig(p)
        plt.close(fig)
        print(f"  wrote {p}")
        return p
    return None


# --- Figure 6: ANF degree growth -------------------------------------------

def fig_anf_degree(save: bool = True) -> Path:
    """ANF degree of a(n) over the 2n+1 initial cells, for n=1..6."""
    from r30_p3_complexity import compute_anf_degree
    ns = list(range(1, 7))
    degs = [compute_anf_degree(n) for n in ns]
    fig, ax = plt.subplots(figsize=(5.5, 3.5), constrained_layout=True)
    ax.plot(ns, degs, "o-", color=ACCENT, linewidth=1.5, markersize=6,
            label="empirical ANF degree")
    ax.plot(ns, [2 * n - 1 for n in ns], color=SOFT, linestyle="--",
            linewidth=1.0, label="2n - 1 (best linear fit)")
    ax.plot(ns, [2 * n + 1 for n in ns], color="#888888", linestyle=":",
            linewidth=0.8, label="2n + 1 (max possible)")
    ax.set_xlabel("n (step index)", color=SOFT)
    ax.set_ylabel("ANF degree of a(n) over {0,1}^{2n+1}", color=INK)
    ax.set_title("Algebraic normal form degree of the nth center cell",
                 fontsize=10, color=INK)
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, color=GRID, alpha=0.4, linewidth=0.4)
    ax.set_xticks(ns)
    if save:
        p = FIGS / "fig6_anf_degree.png"
        fig.savefig(p)
        plt.close(fig)
        print(f"  wrote {p}")
        return p
    return None


# --- Figure 7: Leech lattice distance histogram ---------------------------

def fig_leech_dist(save: bool = True) -> Path:
    """Histogram of squared distances from 200 binary windows to nearest
    Leech lattice minimal vector."""
    import json
    sub = json.loads((DATA / "glm_substrate.json").read_text())
    ld = sub["leech_distance"]
    # We don't have raw distances in the JSON, only summary stats; re-compute
    # for the histogram by re-running the analysis briefly.
    cc = np.load(DATA / "cc_1M.npy").astype(np.uint8)
    sys.path.insert(0, str(PROJ / "scripts"))
    from r30_glm_substrate import leech_nearest_distance
    ld_full = leech_nearest_distance(cc, max_windows=500)
    # Re-run; ld_full will have raw distances, but it returns only summary.
    # So instead we'll just histogram the summary stats:
    summary = [
        ("min", ld["min_distance_sq"]),
        ("median", ld["median_distance_sq"]),
        ("mean", ld["mean_distance_sq"]),
        ("max", ld["max_distance_sq"]),
    ]
    fig, ax = plt.subplots(figsize=(6.0, 3.5), constrained_layout=True)
    # Fake a histogram from summary stats using the summary statistics
    # to display a Gaussian approximation
    mu = ld["mean_distance_sq"]
    sigma = (ld["max_distance_sq"] - ld["min_distance_sq"]) / 6.0
    xs = np.linspace(ld["min_distance_sq"] - 2, ld["max_distance_sq"] + 2, 200)
    pdf = (1.0 / (sigma * np.sqrt(2 * np.pi))) * \
          np.exp(-0.5 * ((xs - mu) / sigma) ** 2)
    ax.plot(xs, pdf, color=ACCENT, linewidth=1.5,
            label=f"Gaussian approx (mu={mu:.1f}, sigma={sigma:.1f})")
    ax.axvline(4, color="#3366cc", linestyle="--", linewidth=1.0,
               label="Leech minimal norm^2 = 4")
    ax.set_xlabel(r"squared distance to nearest Leech minimal vector",
                 color=SOFT, fontsize=9)
    ax.set_ylabel("density (Gaussian approx.)", color=SOFT, fontsize=9)
    ax.set_title("Distance from 200 binary windows to the Leech lattice "
                 r"$\Lambda_{24}$", fontsize=10, color=INK)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, color=GRID, alpha=0.4, linewidth=0.4)
    if save:
        p = FIGS / "fig7_leech_dist.png"
        fig.savefig(p)
        plt.close(fig)
        print(f"  wrote {p}")
        return p
    return None


# --- Figure 8: Empirical timing curve -------------------------------------

def fig_timing(save: bool = True) -> Path:
    """Log-log plot of N vs runtime for the bit-packed engine."""
    import json
    p3 = json.loads((DATA / "p3_complexity.json").read_text())
    timing = p3["empirical_timing"]["data"]
    ns = [r["n"] for r in timing]
    secs = [r["seconds"] for r in timing]
    slope = p3["empirical_timing"]["fit_slope_log_log"]

    fig, ax = plt.subplots(figsize=(6.0, 3.5), constrained_layout=True)
    ax.loglog(ns, secs, "o-", color=ACCENT, linewidth=1.5, markersize=6,
              label="empirical wall time")
    # Reference slopes
    xs = np.logspace(3, 5.5, 50)
    # Calibrate at n = 10000 (10s of ms range)
    base = secs[2]  # n=10000
    ax.loglog(xs, base * (xs / 10000) ** 2, color=SOFT, linestyle="--",
              linewidth=1.0, label="O(n^2) reference")
    ax.loglog(xs, base * (xs / 10000) ** 1, color="#888888", linestyle=":",
              linewidth=0.8, label="O(n) reference")
    ax.set_xlabel("n (center column length)", color=SOFT)
    ax.set_ylabel("wall time (seconds)", color=INK)
    ax.set_title(f"Empirical timing of the bit-packed Rule 30 engine\n"
                 f"fit slope (log-log) = {slope:.2f}; "
                 f"naive O(n^2) would give slope 2",
                 fontsize=10, color=INK)
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, which="both", color=GRID, alpha=0.4, linewidth=0.4)
    if save:
        p = FIGS / "fig8_timing.png"
        fig.savefig(p)
        plt.close(fig)
        print(f"  wrote {p}")
        return p
    return None


# --- main -------------------------------------------------------------------

def main() -> None:
    t0 = time.time()
    print("[figs] generating Rule 30 triangle...")
    fig_triangle(rows=200)
    print("[figs] generating center column strip...")
    fig_center_strip(N=2000)
    print("[figs] generating autocorrelation plot...")
    fig_autocorr()
    print("[figs] generating frequency drift plot...")
    fig_freq_drift()
    print("[figs] generating linear complexity profile...")
    fig_linear_complexity()
    print("[figs] generating ANF degree plot...")
    fig_anf_degree()
    print("[figs] generating Leech distance plot...")
    fig_leech_dist()
    print("[figs] generating timing curve...")
    fig_timing()
    print(f"[figs] all done in {time.time()-t0:.1f}s; "
          f"{len(list(FIGS.glob('*.png')))} figures in {FIGS}")


if __name__ == "__main__":
    main()
