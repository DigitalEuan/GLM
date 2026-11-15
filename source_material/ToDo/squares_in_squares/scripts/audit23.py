#!/usr/bin/env python3
"""audit23.py — run 23 fact base.

Q (user): did run 22 move submission.csv or the score?
Facts needed:
  1. table n=5 (grid 3 or already 2.707?) — is the run-22 verified
     2.708107407 an UNAPPLIED improvement?
  2. which table rows sit at their trivial grid (score headroom rows)?
  3. leech atlas for those rows (level 1/2): does the study know
     below-grid values we never applied?
  4. where is submission.csv built from, and the scoring method.
  5. run-22 write footprint (answer: table/submission untouched).
  6. recompute the score the way the project scores it.
"""
import json
import math
import os
import subprocess
import time

W = "/home/z/my-project"
tab = json.load(open(f"{W}/workspace/submission/table.json"))
leech = json.load(open(f"{W}/json/leech_map.json"))
rows = {r["n"]: r for r in leech["rows"]}

print("== 1. n=5 in table ==")
print(json.dumps(tab.get("5"), ensure_ascii=False)[:400])

print("\n== 2. rows sitting at the trivial grid (L == ceil(sqrt(n))^2 side) ==")
import math
at_grid = []
for k, rec in tab.items():
    n = int(k)
    g = math.ceil(math.sqrt(n))
    if abs(rec["L"] - g) < 1e-9:
        at_grid.append(n)
at_grid.sort()
print("count:", len(at_grid))
print("n values:", at_grid)

print("\n== 3. leech atlas for at-grid rows (what the study knows) ==")
for n in at_grid:
    r = rows.get(n)
    if r is None:
        print(f"  n={n:4d}: NOT in leech rows")
        continue
    print(f"  n={n:4d} level={r['level']} tier={r['tier']:<12} "
          f"atlas_L={r['L']:.9f} form={r['form'][:28]}")

print("\n== 4. submission files ==")
for p in ("workspace/submission/submission.csv", "download/submission.csv",
          "download/table.json"):
    print(p, "exists" if os.path.exists(f"{W}/{p}") else "MISSING",
          os.path.getsize(f"{W}/{p}") if os.path.exists(f"{W}/{p}") else "")
sub = open(f"{W}/workspace/submission/submission.csv").read().splitlines()
print("submission.csv head:", sub[:3])
print("lines:", len(sub))
for ln in sub:
    if ln.startswith(("5,", "5,")) or ln.split(",")[0] == "5":
        print("n=5 row:", ln)

print("\n== 5. run-22 write footprint (mtime ordering) ==")
for p in ("workspace/submission/table.json",
          "workspace/submission/submission.csv",
          "workspace/push/soft_relax.json",
          "scripts/soft_relax.py"):
    fp = f"{W}/{p}"
    print(f"  {time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(fp)))}"
          f"  {p}" if os.path.exists(fp) else f"  MISSING {p}")

print("\n== 6. score, computed the leech way ==")
src = open(f"{W}/scripts/leech_map.py").read() if os.path.exists(
    f"{W}/scripts/leech_map.py") else ""
i = src.find("total_score")
print("leech_map.py scoring excerpt:")
print(src[max(0, i - 700):i + 200] if i >= 0 else "  (not found)")

print("\n== 7. leech by_level 1 detail (the at-grid class) ==")
lv1 = [r for r in leech["rows"] if r["level"] == 1]
print("level-1 rows:", len(lv1))
tab_at = [n for n in at_grid]
covered = [r["n"] for r in lv1 if str(r["n"]) in tab]
print("level-1 rows that are in our table at grid:", len(covered))
savings = 0.0
for r in lv1:
    n = r["n"]
    g = math.ceil(math.sqrt(n))
    if str(n) in tab and abs(tab[str(n)]["L"] - g) < 1e-9:
        # below-grid headroom = grid - atlas_L if atlas is below grid
        if r["L"] < g - 1e-9:
            savings += g - r["L"]
            print(f"  n={n:4d} ATLAS BELOW GRID: atlas={r['L']:.9f} "
                  f"grid={g} -> headroom {g - r['L']:.6f} tier={r['tier']}")
print("total atlas headroom on at-grid level-1 rows:", round(savings, 6))

print("\n== 8. plain sums ==")
tot = sum(rec["L"] for rec in tab.values())
grid_sum = sum(math.ceil(math.sqrt(int(k))) for k in tab)
print(f"sum(our L) over {len(tab)} rows = {tot:.6f}")
print(f"sum(trivial grid) = {grid_sum:.6f}  (leech grid_ceiling=28.937670)")
print(f"grid - ours = {grid_sum - tot:.6f}  (leech improvement=6.050199)")
