#!/usr/bin/env python3
"""Planner v3 — partial-fill cascade chains (fast version).

Walk 2D band-extension chains from every base packing.  At each state
(m, L, st) with container Lnext = L+1, the free band cells are computed from
the ACTUAL bbox (w, h) of st: nx = floor(Lnext - w) columns right, ny rows
above; right band nx×floor(h), top band floor(w)×ny, corner nx×ny.  A partial
fill of the first r cells (fixed order) packs m+r squares at container Lnext.

Candidates are stored raw; per-n winners are finalized + verified once.
Merge with table.json (records + removals), keep the better.
"""
import json
import os
import sys
import time
from math import ceil, floor, sqrt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import packlib as P
from cascade2 import bbox_wh, normalize

SUB = "/home/z/my-project/workspace/submission"

def band_cells(state, Lnext):
    lox, loy, hix, hiy = bbox_wh(state)
    w, h = hix - lox, hiy - loy
    nx = max(0, floor(Lnext - w + 1e-9))
    ny = max(0, floor(Lnext - h + 1e-9))
    rows_h = floor(h + 1e-9)
    cols_w = floor(w + 1e-9)
    cells = []
    for c in range(nx):
        for r in range(rows_h):
            cells.append((w + c + 0.5, r + 0.5, 0.0))
    for r in range(ny):
        for c in range(cols_w):
            cells.append((c + 0.5, h + r + 0.5, 0.0))
    for c in range(nx):
        for r in range(ny):
            cells.append((w + c + 0.5, h + r + 0.5, 0.0))
    return cells

def main():
    t0 = time.time()
    stores = P.load_stores(SUB, names=("found.json", "found2.json",
                                       "cascade.json", "records.json"))
    # also use table.json states as bases (records + removals realized)
    tab = json.load(open(os.path.join(SUB, "table.json")))
    for k, v in tab.items():
        stores[int(k)] = v
    print(f"bases: {len(stores)}", flush=True)

    best = {}    # n -> (Lnext, raw state)
    for key in sorted(stores, key=int):
        m0 = int(key)
        if m0 > 2000:
            continue
        rec = stores[key]
        st = normalize(rec["state"])
        L0 = rec["L"]
        if m0 <= 1000:
            prev = best.get(m0)
            if prev is None or L0 < prev[0]:
                best[m0] = (L0, st)
        cur = (m0, L0, st)
        steps = 0
        while cur[0] <= 1000 and steps < 80:
            m, L, stt = cur
            Lnext = L + 1.0
            cells = band_cells(stt, Lnext)
            cap = len(cells)
            if cap == 0:
                break
            for r in range(1, cap + 1):
                n = m + r
                if n > 1000:
                    break
                prev = best.get(n)
                if prev is not None and Lnext >= prev[0] - 1e-12:
                    continue
                best[n] = (Lnext, stt + cells[:r])
            cur = (m + cap, Lnext, normalize(stt + cells))
            steps += 1
        if time.time() - t0 > 600:
            print(f"  [warn] over 600s at base {m0}", flush=True)
    print(f"[{time.time()-t0:.0f}s] raw candidates: {len(best)}", flush=True)

    # finalize winners that beat table.json
    improved = 0
    fails = []
    for n in range(1, 1001):
        cand = best.get(n)
        curL = tab[str(n)]["L"]
        if cand is None or cand[0] >= curL - 1e-12:
            continue
        stf, rf = P.finalize(cand[1], gap=2e-9)
        if not rf["ok"] or rf["worst_pen"] > 0:
            fails.append((n, cand[0], rf["worst_pen"]))
            continue
        if rf["L"] < curL - 1e-12:
            tab[str(n)] = {"L": round(rf["L"], 12), "state": stf,
                           "src": f"chain3"}
            improved += 1
    print(f"chain improvements applied: {improved}, fails: {len(fails)}", flush=True)
    for f in fails[:8]:
        print("  FAIL", f, flush=True)

    json.dump(tab, open(os.path.join(SUB, "table.json"), "w"))
    tot = 0.0
    for n in range(1, 1001):
        L = tab[str(n)]["L"]
        tot += L / sqrt(n) - 1
    gt = sum(ceil(sqrt(n)) / sqrt(n) - 1 for n in range(1, 1001))
    beats = sum(1 for n in range(1, 1001) if tab[str(n)]["L"] < ceil(sqrt(n)) - 1e-9)
    print(f"SCORE={tot:.6f} (grid {gt:.6f}, improvement {gt - tot:.6f}) BEATS_GRID={beats}", flush=True)

if __name__ == "__main__":
    main()
