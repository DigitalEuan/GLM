#!/usr/bin/env python3
r"""import_busyaprime38.py — run 38, P3: import the public Kaggle
network merge (busya PRIME's aggregator notebook).

Source (mirrored run 38 via signed GCS URL from the public output
page, scriptVersionId 366947991, read 2026-11-09):
  workspace/sources/busyaprime38/submission.csv — 500,500 rows, the
  competition format itself (id,n,square_id,x,y,angle[rad]): the best
  public packing of every puzzle, merged shortest-first from 1299
  submission-shaped CSVs across 136 public notebooks + 33 public
  datasets (68,269 distinct packings), certified by the hosts' metric
  code as doubles; displayed LB 22.2180568.
  workspace/sources/busyaprime38/provenance.csv — per-puzzle L (45
  digits) + source list (credit).

Import per row (the import_candidates.py gate, unchanged):
  P.verify(states, 1e-9) — ok and worst_pen <= 1e-9
  P.finalize(states, gap=2e-9) — ok, worst_pen <= -1e-12
  apply iff newL < cur - 1e-7 (MIN_GAIN, the anti-churn convention).
Idempotent by construction (re-run => all no-beat).  Ledger:
  workspace/push/import_busyaprime38.json.
"""
import csv
import json
import math
import sys
from collections import defaultdict

sys.path.insert(0, "/home/z/my-project/scripts")
import packlib as P

W = "/home/z/my-project"
SRC = f"{W}/workspace/sources/busyaprime38"
TAB = f"{W}/workspace/submission/table.json"
OUT = f"{W}/workspace/push/import_busyaprime38.json"
MIN_GAIN = 1e-7
APPLY = "--apply" in sys.argv


def load_states():
    """submission.csv -> {n: [(x, y, angle_rad), ...]}"""
    by_n = defaultdict(list)
    with open(f"{SRC}/submission.csv", newline="") as f:
        rd = csv.DictReader(f)
        for row in rd:
            n = int(row["n"])
            by_n[n].append((float(row["x"]), float(row["y"]),
                            float(row["angle"])))
    for n, st in by_n.items():
        st.sort(key=lambda s: (s[0], s[1], s[2]))
    return by_n


def load_provenance():
    prov = {}
    with open(f"{SRC}/provenance.csv", newline="") as f:
        rd = csv.DictReader(f)
        for row in rd:
            prov[int(row["n"])] = {
                "their_L": float(row["L"]),
                "sources": row["sources"]}
    return prov


def main():
    by_n = load_states()
    prov = load_provenance()
    tab = json.load(open(TAB))
    before = sum(r["L"] / math.sqrt(int(k)) - 1 for k, r in tab.items())

    rows_out = []
    applied = []
    failed = skipped = 0
    for n in range(1, 1001):
        cur = tab[str(n)]["L"]
        st = by_n.get(n)
        rec = {"n": n, "old": cur, "their_L": prov.get(n, {}).get("their_L")}
        if not st or len(st) != n:
            rec["why"] = "missing/count"
            failed += 1
            rows_out.append(rec)
            continue
        v = P.verify(st, tol=1e-9)
        if not v["ok"] or v["worst_pen"] > 1e-9:
            rec.update(why="verify", worst_pen=v.get("worst_pen"),
                       their_L=rec["their_L"])
            failed += 1
            rows_out.append(rec)
            continue
        stf, rf = P.finalize(st, gap=2e-9)
        if not (rf["ok"] and rf["worst_pen"] <= -1e-12 and len(stf) == n):
            rec.update(why="finalize")
            failed += 1
            rows_out.append(rec)
            continue
        newL = rf["L"]
        rec["new"] = newL
        rec["row_gain"] = (cur - newL) / math.sqrt(n)
        if newL < cur - MIN_GAIN:
            rec["applied"] = True
            applied.append(rec)
            if APPLY:
                credit = (prov.get(n, {}).get("sources") or "?").split(";")[0].strip()
                tab[str(n)] = {"L": newL, "state": stf,
                               "src": "busyaprime",
                               "credit": credit,
                               "their_exact_L": prov.get(n, {}).get("their_L")}
        else:
            rec["why"] = "no-beat" if newL >= cur else "below MIN_GAIN"
            skipped += 1
        rows_out.append(rec)

    direct = sum(r["row_gain"] for r in applied)
    after = before - direct
    mode = "APPLIED" if APPLY else "DRY"
    print(f"{mode}: {len(applied)} rows, direct gain {direct:.6f}; "
          f"score {before:.9f} -> {after:.9f}")
    for r in sorted(applied, key=lambda r: -r["row_gain"])[:12]:
        print(f"  n={r['n']:4d} {r['old']:.9f} -> {r['new']:.9f} "
              f"(gain {r['row_gain']:.6f})")
    print(f"  (failed {failed}, skipped {skipped})")
    if APPLY:
        json.dump(tab, open(TAB, "w"), indent=1)
    json.dump({"mode": mode, "source": "busyaprime/aggregator "
               "scriptVersionId 366947991 read 2026-11-09",
               "before": before, "after": after,
               "direct_gain": direct, "applied": len(applied),
               "rows": rows_out}, open(OUT, "w"), indent=1)
    print(f"ledger -> {OUT}")


if __name__ == "__main__":
    main()
