#!/usr/bin/env python3
"""audit23b.py — run 23 fact base, pass 2.

Pass 1 established: n=5 already 2.7071 in table (run-22 find = control,
above submitted value, correctly NOT applied); score = sum(L/sqrt(n)-1);
table has 1000 rows; run 22 wrote nothing to table/submission (mtimes).

This pass: (a) near-grid rows at tol 1e-5 (the roots), (b) n=12/n=20
entries, (c) improvement/waste definitions in leech_map.py, (d) where
the '23 roots' list lives (run-21 clue ledger?), (e) recompute the
score on the current table vs leech metrics, (f) top-waste rows.
"""
import json
import math
import os

W = "/home/z/my-project"
tab = json.load(open(f"{W}/workspace/submission/table.json"))
leech = json.load(open(f"{W}/json/leech_map.json"))
rows = {r["n"]: r for r in leech["rows"]}

def grid(n):
    return math.ceil(math.sqrt(n))

print("== (a) near-grid rows, tol 1e-5 ==")
near = []
for k, rec in tab.items():
    n = int(k)
    if abs(rec["L"] - grid(n)) < 1e-5:
        near.append((n, rec["L"]))
near.sort()
print("count:", len(near))
for n, L in near:
    r = rows.get(n, {})
    print(f"  n={n:4d} L={L:.9f} grid={grid(n)} "
          f"level={r.get('level')} tier={r.get('tier')} src={rec.get('src','')[:30]}")

print("\n== (b) n=12 / n=20 entries ==")
for n in (12, 20, 13, 6, 2):
    rec = tab.get(str(n))
    if rec:
        print(f"  n={n:3d} L={rec['L']:.9f} grid={grid(n)} src={rec.get('src','')[:40]}")

print("\n== (c) improvement / waste definitions in leech_map.py ==")
src = open(f"{W}/scripts/leech_map.py").read()
for key in ("improvement", "waste"):
    i = 0
    while True:
        i = src.find(key, i)
        if i < 0:
            break
        seg = src[max(0, i - 120):i + 160].replace("\n", " ")[:260]
        print(f"  [{key}] ...{seg}...")
        i += len(key)
        break  # first occurrence only, per key

print("\n== (d) 'roots' in run-21 artifacts ==")
for p in ("workspace/push/clue_ledger.json",
          "workspace/push/boundary_demo.json",
          "workspace/push/wheel_census.json"):
    fp = f"{W}/{p}"
    if os.path.exists(fp):
        d = json.load(open(fp))
        s = json.dumps(d)
        if "root" in s:
            print(f"  {p}: contains 'root'")
            for k, v in d.items():
                if isinstance(v, (list, dict)) and "root" in json.dumps(v).lower():
                    print(f"    key={k}: {json.dumps(v)[:400]}")
        else:
            print(f"  {p}: no 'root' mention")

print("\n== (e) score on current table vs leech metrics ==")
score = sum(rec["L"] / math.sqrt(int(k)) - 1 for k, rec in tab.items())
gscore = sum(grid(int(k)) / math.sqrt(int(k)) - 1 for k in tab)
print(f"  current score  = {score:.9f}   (leech total_score  = "
      f"{leech['metrics']['total_score']:.9f})")
print(f"  grid score     = {gscore:.9f}   (leech grid_ceiling = "
      f"{leech['metrics']['grid_ceiling']:.9f})")
print(f"  saving vs grid = {gscore - score:.9f}   (leech improvement = "
      f"{leech['metrics']['improvement']:.9f})")
print(f"  identical to leech build? {abs(score - leech['metrics']['total_score']) < 1e-9}")

print("\n== (f) top-15 waste rows (waste = L/sqrt(n)-1) ==")
w = sorted(((rec["L"] / math.sqrt(int(k)) - 1, int(k), rec["L"])
            for k, rec in tab.items()), reverse=True)
for waste, n, L in w[:15]:
    r = rows.get(n, {})
    print(f"  n={n:4d} waste={waste:.6f} L={L:.6f} grid={grid(n)} "
          f"level={r.get('level')} tier={r.get('tier','')[:12]} src={tab[str(n)].get('src','')[:24]}")
print("  ... bottom-3 (tightest rows):",
      [(n, round(ws, 6)) for ws, n, L in w[-3:]])

print("\n== (g) level distribution of near-grid rows ==")
from collections import Counter
c = Counter(rows.get(n, {}).get("level") for n, _ in near)
print("  ", dict(c))
