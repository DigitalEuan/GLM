#!/usr/bin/env python3
"""motif_zoo.py — classify every table packing by motif signature.

Signature = sorted list of (angle, count) for tilted squares (angle != 0)
plus count of axis-aligned squares. Cluster packings by signature to expose
the parametric families (the 'wheels') present in our verified data.
Output: per-family inventory (angle, members, n-range) to stdout, small.
"""
import json
import sys
from collections import defaultdict

TAB = "/home/z/my-project/workspace/submission/table.json"

def ang_key(t):
    # bucket angles to 0.01 rad
    return round(t % (3.141592653589793 / 2), 2)

def main():
    tab = json.load(open(TAB))
    fam = defaultdict(list)
    for n in range(1, 1001):
        rec = tab[str(n)]
        st = rec["state"]
        ax = sum(1 for q in st if abs(q[2]) < 1e-9)
        tl = defaultdict(int)
        for q in st:
            if abs(q[2]) >= 1e-9:
                tl[ang_key(q[2])] += 1
        if not tl:
            sig = "GRID" if rec.get("src", "").startswith("grid") else "AXIS-ONLY"
        else:
            sig = "|".join(f"{a:.2f}rad:{c}" for a, c in sorted(tl.items()))
        fam[sig].append(n)
    # print families with tilted squares (the wheels), plus grid/axis summary
    print(f"signatures: {len(fam)}")
    grid = fam.pop("GRID", [])
    axonly = fam.pop("AXIS-ONLY", [])
    print(f"grid-tied: {len(grid)}, axis-only-constructed: {len(axonly)}")
    for sig, members in sorted(fam.items(), key=lambda kv: -len(kv[1]))[:25]:
        ns = members
        print(f"{sig}  members={len(ns)} n=[{min(ns)}..{max(ns)}] e.g. {ns[:6]}")
    json.dump({k: v for k, v in fam.items()}, open("/tmp/motif_families.json", "w"))

if __name__ == "__main__":
    main()
