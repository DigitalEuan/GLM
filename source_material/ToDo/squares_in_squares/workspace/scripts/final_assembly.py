#!/usr/bin/env python3
"""Final assembly: table.json -> submission.csv + full round-trip verification.

Steps:
 1. Build detail dict: table.json states for covered n, trivial grid otherwise.
 2. write_csv to workspace/submission/submission.csv (12-dp decimals).
 3. Round-trip: read the CSV back, verify every packing (SAT non-overlap with
    tol, bbox containment), recompute the score independently.
 4. Report row count (must be 500500 + header), id continuity, per-n square
    counts, and the final score.
"""
import json
import os
import sys
from math import ceil, sqrt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import packlib as P

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

SUB = ROOT + "/workspace/submission"

def main():
    tab = json.load(open(os.path.join(SUB, "table.json")))
    detail = {}
    for n in range(1, 1001):
        rec = tab[str(n)]
        assert len(rec["state"]) == n, f"n={n}: {len(rec['state'])} squares"
        detail[n] = {"state": rec["state"], "L": rec["L"], "src": rec.get("src", "?")}

    # 1+2. write
    path = os.path.join(SUB, "submission.csv")
    nrows = P.write_csv(path, detail)
    print(f"rows written: {nrows} (expect 500500)")
    assert nrows == 500500

    # 3. round-trip
    by_n = P.read_csv(path)
    assert len(by_n) == 1000, f"puzzles in csv: {len(by_n)}"
    ids_ok = True
    with open(path) as f:
        import csv as _csv
        rd = list(_csv.reader(f))[1:]
        for i, row in enumerate(rd):
            if int(row[0]) != i:
                ids_ok = False
                break
    print(f"id continuity: {ids_ok}")

    bad = []
    tot = 0.0
    gt = 0.0
    beats = 0
    for n in range(1, 1001):
        st = by_n[n]
        if len(st) != n:
            bad.append((n, "count", len(st)))
            continue
        r = P.verify(st, tol=1e-9)
        if not r["ok"]:
            bad.append((n, "overlap", r["worst_pen"]))
            continue
        # compare with table L (rounded) — allow 1e-9 for the 12-dp round trip
        if abs(r["L"] - tab[str(n)]["L"]) > 1e-9:
            bad.append((n, "L drift", r["L"], tab[str(n)]["L"]))
        tot += r["L"] / sqrt(n) - 1
        g = ceil(sqrt(n))
        gt += g / sqrt(n) - 1
        if r["L"] < g - 1e-9:
            beats += 1
    print(f"round-trip issues: {len(bad)}")
    for b in bad[:10]:
        print("  BAD", b)
    print(f"FINAL SCORE = {tot:.6f}")
    print(f"grid ceiling = {gt:.6f}  improvement = {gt - tot:.6f}")
    print(f"puzzles beating grid: {beats}/1000")

if __name__ == "__main__":
    main()
