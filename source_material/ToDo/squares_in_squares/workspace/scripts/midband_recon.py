#!/usr/bin/env python3
"""midband_recon.py — Run 9 orientation: the exact frontier shape + motifs.

From table.json (the verified submission table):
  - classify every n by (q, r) with q = floor(sqrt(n)), n = q^2 + r
  - depth(n) = grid(n) - L(n)  where grid = q+1 for r >= 1
  - frontier: depth by (q, r); the r<=18 band is solved (r<=q), the
    r in [19..2q-2] band (MID) is the prize
  - motif dump for representative solved puzzles (large q, r<=18):
    angle histogram + structural signature
  - MID band check: all at grid
  - the solved-band constructions' SOURCE labels (which family produced them)
"""
import json
import sys
from collections import Counter
from math import sqrt

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

sys.path.insert(0, ROOT + "/scripts")
import packlib as P

TAB = ROOT + "/workspace/submission/table.json"
tab = json.load(open(TAB))

rows = []
for n in range(1, 1001):
    rec = tab[str(n)]
    L = rec["L"]
    q = int(sqrt(n))
    while (q + 1) ** 2 <= n:
        q += 1
    r = n - q * q
    grid = q + 1 if r > 0 else q
    rows.append({"n": n, "q": q, "r": r, "grid": grid, "L": L,
                 "depth": grid - L, "src": rec.get("src", "?")[:40],
                 "state": rec["state"]})

# ---- 1. solved band: depth by (q, r), r <= 18 -------------------------
print("=== solved band (r<=18): depth = grid - L, by r; columns q =====")
by_r = {}
for row in rows:
    if 1 <= row["r"] <= 18 and row["depth"] > 1e-6:
        by_r.setdefault(row["r"], []).append((row["q"], row["depth"], row["n"]))
for r in sorted(by_r):
    qs = sorted(by_r[r])
    qs_str = " ".join(f"q{q}:{d:.3f}" for q, d, _ in qs[-34:])
    print(f"r={r:2d} ({len(qs):3d} solved) {qs_str}")

# ---- 2. solved band: anything with r >= 19 that beats grid? -----------
weird = [row for row in rows if row["r"] >= 19 and row["depth"] > 1e-6]
print(f"\n=== r>=19 beating grid: {len(weird)}")
for row in weird[:10]:
    print("  ", row["n"], row["q"], row["r"], row["L"], row["src"])

# ---- 3. MID band at grid? --------------------------------------------
mid = [row for row in rows if 19 <= row["r"] <= 2 * row["q"] - 2]
at_grid = [row for row in mid if row["depth"] <= 1e-6]
print(f"\n=== MID band: {len(mid)} puzzles, {len(at_grid)} at grid, "
      f"{len(mid) - len(at_grid)} below")
for row in mid:
    if row["depth"] > 1e-6:
        print("  below-grid MID:", row["n"], row["q"], row["r"], row["L"], row["src"])

# ---- 4. depth-vs-q shape for fixed r (how does depth scale?) ---------
print("\n=== depth scaling for fixed r (is depth ~ f(r) independent of q?)")
for r in (1, 2, 3, 5, 8, 12, 18):
    series = [(row["q"], row["depth"]) for row in rows
              if row["r"] == r and row["depth"] > 1e-6]
    if series:
        ds = [d for _, d in series]
        print(f"r={r:2d}: count={len(series):3d} depth min={min(ds):.4f} "
              f"max={max(ds):.4f} mean={sum(ds)/len(ds):.4f}")

# ---- 5. sources of the solved band ----------------------------------
print("\n=== source labels in the solved band (r<=18, beats grid)")
cnt = Counter(row["src"].split(":")[0] for row in rows
              if 1 <= row["r"] <= 18 and row["depth"] > 1e-6)
for k, v in cnt.most_common(15):
    print(f"  {v:4d}  {k}")

# ---- 6. motif dump: representative large-q solved puzzles ------------
print("\n=== motif dumps (large q, r <= 18, beats grid)")
def dump(n):
    rec = tab[str(n)]
    st = rec["state"]
    ang = Counter(round(s[2] / 0.7853981633974483, 3) for s in st)
    ang2 = Counter(round(s[2], 4) for s in st)
    print(f"n={n} L={rec['L']:.6f} src={rec.get('src','?')[:50]}")
    print(f"  angle/45deg units: {dict(ang.most_common(6))}")
    print(f"  raw angles top: {ang2.most_common(6)}")
    # x-coordinate histogram (strip structure)
    xs = Counter(round(s[0], 3) for s in st)
    ys = Counter(round(s[1], 3) for s in st)
    print(f"  distinct x: {len(xs)}  distinct y: {len(ys)}  n={len(st)}")
    print(f"  top y-values: {ys.most_common(5)}")
    print(f"  top x-values: {xs.most_common(5)}")

for n in (905, 906, 910, 918, 925, 941, 960, 984):
    if n <= 1000:
        dump(n)

# ---- 7. small-q solved examples (the classical bases) ----------------
print("\n=== classical small bases")
for n in (5, 10, 13, 17, 26):
    rec = tab[str(n)]
    print(f"n={n} L={rec['L']:.6f} src={rec.get('src','?')[:50]}")

# ---- 8. per-q MID inventory -----------------------------------------
print("\n=== MID inventory per q (how many targets per block)")
inv = Counter(row["q"] for row in mid)
for q in sorted(inv):
    nmin = q * q + 19
    nmax = min(1000, q * q + 2 * q - 2)
    print(f"  q={q:2d}: {inv[q]:3d} MID puzzles, n in [{nmin}, {nmax}]")
