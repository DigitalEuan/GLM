#!/usr/bin/env python3
"""figures.py -- the 5 figures for the Leech-grid report (English labels).

  F1 map:       every solved grid as (n, L/sqrt(n)) colored by Leech level
                (the 'waste' trajectory with level bands).
  F2 fields:    bar chart of number fields across the 1000 grids.
  F3 tower:     laminated tower kissing numbers (log scale), verified
                points marked, plus per-level grid counts.
  F4 octads:    octad calculus -- intersection histogram (30/448/280 per
                octad) + Steiner lambda ladder 253/77/21/5/1.
  F5 projection: the defect-1 law -- index of pi_S(Leech) in
                2Z^d + Z(1..1) as a function of d: flat 1 everywhere,
                759 exceptions exactly at the octads (d = 8).
All data read from the verified JSON outputs; nothing recomputed.
"""
import json

import matplotlib.font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf')
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['Noto Sans SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10

D = "/home/z/my-project/download/"
F = D + "fig/"
import os
os.makedirs(F, exist_ok=True)

LM = json.load(open(D + "leech_map.json"))
CORE = json.load(open(D + "leech_core.json"))
OCT = json.load(open(D + "octad_moves.json"))
rows = LM["rows"]

LEV_COLOR = {0: "#b0b0b0", 1: "#1f77b4", 2: "#2ca02c", 3: "#d62728", 4: "#9467bd"}
LEV_NAME = {0: "0 unresolved (numeric only)", 1: "1 rational Q -> L1-L4",
            2: "2 quadratic Q(sqrt m) -> L8", 3: "3 biquadratic/quartic -> L16",
            4: "4 octic+ -> L24"}

# ---------------- F1: the map -------------------------------------------
fig, ax = plt.subplots(figsize=(7.2, 4.4), constrained_layout=True)
for lvl in (0, 1, 2, 3):
    ns = np.array([r["n"] for r in rows if r["level"] == lvl])
    eff = np.array([r["L"] / np.sqrt(r["n"]) for r in rows if r["level"] == lvl])
    ax.scatter(ns, eff, s=9 if lvl else 5, c=LEV_COLOR[lvl],
               label=LEV_NAME[lvl], alpha=.75, linewidths=0)
ax.axhline(1.0, color="k", lw=.6, ls=":")
ax.set_xlim(0, 1000)
ax.set_ylim(0.98, 1.35)
ax.set_xlabel("n (number of unit squares)")
ax.set_ylabel("compactness L/sqrt(n)  (lower = better)")
ax.set_title("Fig 1  The 1000 solved grids colored by Leech level: higher algebraic tiers track the lower bound 1")
ax.legend(loc="upper right", fontsize=8.5, framealpha=.95)
ax.grid(alpha=.25)
fig.savefig(F + "f1_map.png", dpi=170)
plt.close(fig)

# ---------------- F2: field distribution --------------------------------
from collections import Counter
fields = Counter(r["field"] or "未定" for r in rows)
order = sorted(fields.items(), key=lambda kv: -kv[1])
labels = [k if len(k) < 16 else k[:14] + "…" for k, _ in order]
vals = [v for _, v in order]
fig, ax = plt.subplots(figsize=(7.2, 4.0), constrained_layout=True)
bars = ax.bar(range(len(vals)), vals, color="#4c72b0", edgecolor="k", lw=.4)
top = order[0][1]
for i, (k, v) in enumerate(order):
    ax.text(i, v + top * .012, str(v), ha="center", fontsize=8)
ax.set_xticks(range(len(vals)))
ax.set_xticklabels(labels, rotation=38, ha="right", fontsize=8)
ax.set_ylabel("grids")
ax.set_title("Fig 2  Number-field distribution of the 1000 container values (87% exact; Q(sqrt2) dominates tier 2)")
ax.grid(axis="y", alpha=.25)
fig.savefig(F + "f2_fields.png", dpi=170)
plt.close(fig)

# ---------------- F3: laminated tower -----------------------------------
tw = CORE["tower"]
dims = [t["dim"] for t in tw]
kiss = [t["kissing"] for t in tw]
src_ok = [t["source"].startswith("verified") for t in tw]
lev_counts = Counter(r["level"] for r in rows)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.6), constrained_layout=True)
ax1.plot(dims, kiss, "o-", color="#d62728", lw=1.6, ms=6)
for d, k, ok in zip(dims, kiss, src_ok):
    ax1.annotate(f"{k}", (d, k), textcoords="offset points",
                 xytext=(0, 7), ha="center", fontsize=8)
    if not ok:
        ax1.plot(d, k, "s", color="#b0b0b0", ms=9, zorder=0)
ax1.set_yscale("log")
ax1.set_xlabel("dimension")
ax1.set_ylabel("kissing number (log)")
ax1.set_title("(a) Laminated tower L1 -> L24", fontsize=10)
ax1.grid(alpha=.25, which="both")
ax1.set_xticks(dims)
ax1.annotate("grey square = cited value (L16: 7320)", (8, 300), fontsize=7.5, color="#666666")
levels = sorted(lev_counts)
ax2.bar([str(l) for l in levels], [lev_counts[l] for l in levels],
        color=[LEV_COLOR[l] for l in levels], edgecolor="k", lw=.4)
for l in levels:
    ax2.text(str(l), lev_counts[l] + 12, str(lev_counts[l]),
             ha="center", fontsize=9)
ax2.set_xlabel("Leech level (by field degree)")
ax2.set_ylabel("grids")
ax2.set_title("(b) grid placement on the tower", fontsize=10)
ax2.grid(axis="y", alpha=.25)
fig.suptitle("Fig 3  Laminated tower and the placement of the 1000 grids (unresolved = numeric optimum, no exact form)")
fig.savefig(F + "f3_tower.png", dpi=170)
plt.close(fig)

# ---------------- F4: octad calculus ------------------------------------
inter = {int(k): v for k, v in OCT["octad_intersections"].items()}
lam = {int(k): v for k, v in OCT["steiner_ladder"]["lambda"].items()}
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.6), constrained_layout=True)
ks = [0, 2, 4]
vs = [inter[k] for k in ks]
b = ax1.bar([str(k) + " pts" for k in ks], vs,
            color=["#8c564b", "#4c72b0", "#55a868"], edgecolor="k", lw=.4)
for i, v in enumerate(vs):
    ax1.text(i, v + 8, str(v), ha="center", fontsize=9)
ax1.set_ylabel("partners per octad")
ax1.set_title("(a) octad calculus: intersections only 0/2/4", fontsize=10)
ax1.grid(axis="y", alpha=.25)
lks = sorted(lam)
lvs = [lam[k] for k in lks]
ax2.plot(lks, lvs, "o-", color="#d62728", lw=1.6)
for k, v in zip(lks, lvs):
    ax2.annotate(str(v), (k, v), textcoords="offset points",
                 xytext=(0, 8), ha="center", fontsize=9)
ax2.set_yscale("log")
ax2.set_xlabel("k (fixed coordinates)")
ax2.set_ylabel("lambda_k (octads containing k)")
ax2.set_title("(b) Steiner ladder S(5,8,24): 253/77/21/5/1", fontsize=10)
ax2.grid(alpha=.25, which="both")
ax2.set_xticks(lks)
fig.suptitle("Fig 4  The logic layer of the Golay substrate: complete, closed, computable on 759 objects")
fig.savefig(F + "f4_octads.png", dpi=170)
plt.close(fig)

# ---------------- F5: projection law ------------------------------------
law = CORE["projection_law"]
ds = sorted(int(k) for k in law)
idx1 = [law[str(d)]["index_histogram"].get("1", 0) for d in ds]
idx2 = [law[str(d)].get("index_histogram", {}).get("2", 0) for d in ds]
fig, ax = plt.subplots(figsize=(7.2, 3.9), constrained_layout=True)
w = .38
xpos = np.arange(len(ds))
ax.bar(xpos - w / 2, idx1, w, label="index = 1 (no defect: pi_S(L24) = 2Z^d + Z(1..1))",
       color="#4c72b0", edgecolor="k", lw=.4)
ax.bar(xpos + w / 2, idx2, w, label="index = 2 (defect: S is exactly an octad)",
       color="#d62728", edgecolor="k", lw=.4)
for i, d in enumerate(ds):
    if idx1[i] < 200000:
        ax.text(xpos[i] - w / 2, idx1[i] + 6000, f"{idx1[i]}",
                ha="center", fontsize=7.5, rotation=90, va="bottom")
ax.text(xpos[-1] + w / 2, idx2[-1] + 6000, "759", ha="center", fontsize=9,
        color="#d62728")
ax.set_yscale("log")
ax.set_xticks(xpos)
ax.set_xticklabels([f"d={d}" for d in ds])
ax.set_xlabel("projection dimension d (d of the 24 coordinates)")
ax.set_ylabel("coordinate subsets (log)")
ax.set_title("Fig 5  Projection law: zero defect for all projections of dim <= 7; the only defect locus is exactly the 759 octads (d = 8)")
ax.legend(fontsize=8.5, loc="center right")
ax.grid(alpha=.25, which="both")
fig.savefig(F + "f5_projection.png", dpi=170)
plt.close(fig)

# ---------------- verify all -------------------------------------------
from PIL import Image
for name in ("f1_map", "f2_fields", "f3_tower", "f4_octads", "f5_projection"):
    p = F + name + ".png"
    im = Image.open(p).convert("L")
    h = im.histogram()
    nz = 1 - h[255] / sum(h)
    print(f"{p}: {im.size} non-white {nz:.3f}")
    assert im.size[0] > 1000 and nz > 0.02, f"figure {name} looks blank"
print("ALL 5 FIGURES OK")
