#!/usr/bin/env python3
r"""gap_analysis.py — Run 13 planning instrument (read-only).

Where can score still be won?  All arithmetic in code, printed and saved to
workspace/push/gap_analysis.json.  Nothing is modified.

Sections:
  1. per-block census: for each grid side k, the n in ((k-1)^2, k^2] split
     into improved / grid-tied, with the sum of (grid-L)/sqrt(n) earned so
     far and the area headroom sum (grid-sqrt(n))/sqrt(n) still available;
  2. value ranking: every n by (a) score-per-unit-L weight 1/sqrt(n),
     (b) unclaimed area headroom, (c) concrete potential = L_now - best(LB)
     with LB = max(sqrt(n), running-max of proven-optimal values);
  3. leader-gap calibration: uniform depth needed per class; what fraction
     of the headroom the leader's 22.0544214515 implies;
  4. block-adjacency structure: where the L(n) envelope is tight/loose
     (the run-12 shell law says L(n+2*floor(L)+1) <= L(n)+1: the +1 shell).
"""
import json
import math
import os
from math import ceil, sqrt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TAB = os.path.join(ROOT, "workspace", "submission", "table.json")
OUT = os.path.join(ROOT, "workspace", "push", "gap_analysis.json")

LEADER = 22.0544214515


def grid_L(n):
    return ceil(sqrt(n))


def main():
    tab = json.load(open(TAB))
    L = {n: tab[str(n)]["L"] for n in range(1, 1001)}
    src = {n: tab[str(n)]["src"] for n in range(1, 1001)}
    score = sum(L[n] / sqrt(n) - 1 for n in range(1, 1001))
    gscore = sum(grid_L(n) / sqrt(n) - 1 for n in range(1, 1001))
    print(f"score {score:.6f} | grid {gscore:.6f} | leader {LEADER}")
    print(f"gaps: to leader {score - LEADER:+.6f} | headroom to area floor "
          f"{score - sum(max(sqrt(n), 0)/sqrt(n)-1 for n in range(1,1001)):.6f} "
          f"(= score of closed rows only)")

    # ---- proven-optimal lower bounds (run 12 B list) ----
    prov = set()
    for n in list(range(1, 11)) + [14, 15, 16, 23, 24, 25, 34, 35, 36]:
        prov.add(n)
    for k in range(4, 32):
        prov.add(k * k); prov.add(k * k - 1); prov.add(k * k - 2)

    # ---- 1. per-block census ----
    print("\n=== 1. per-block census (block k: n in ((k-1)^2, k^2]) ===")
    blocks = []
    for k in range(2, 32):
        lo, hi = (k - 1) ** 2 + 1, k * k
        rows = []
        for n in range(lo, hi + 1):
            g = grid_L(n)
            assert g == k
            d = g - L[n]
            rows.append((n, d, d / sqrt(n), (g - sqrt(n)) / sqrt(n)))
        earned = sum(r[2] for r in rows if r[1] > 1e-12)
        head = sum(r[3] for r in rows if r[1] <= 1e-12 and r[0] not in prov)
        tied = sum(1 for r in rows if r[1] <= 1e-12)
        blocks.append({"k": k, "n_lo": lo, "n_hi": hi, "tied": tied,
                       "earned": earned, "open_headroom": head})
        print(f"  k={k:2d} n={lo:4d}..{hi:4d} tied={tied:3d}/{hi-lo+1:3d} "
              f"earned={earned:.4f} open_area_headroom={head:.4f}")

    # ---- 2. value ranking ----
    print("\n=== 2. ranking: grid-tied n by open area headroom (top 40) ===")
    tied = [n for n in range(1, 1001) if grid_L(n) - L[n] <= 1e-12]
    open_tied = [n for n in tied if n not in prov]
    rank = sorted(open_tied,
                  key=lambda n: -(grid_L(n) - sqrt(n)) / sqrt(n))
    tot_head = 0.0
    for n in rank[:40]:
        h = (grid_L(n) - sqrt(n)) / sqrt(n)
        tot_head += h
        print(f"  n={n:4d} k={grid_L(n):2d} 1/sqrt(n)={1/sqrt(n):.5f} "
              f"headroom={h:.5f} r={grid_L(n)**2-n:3d} class={'LOW' if grid_L(n)**2-n<=18 else 'MID'}")
    total_head = sum((grid_L(n) - sqrt(n)) / sqrt(n) for n in open_tied)
    print(f"  open grid-tied: {len(open_tied)} (proven-optimal excluded: "
          f"{len([n for n in tied if n in prov])})")
    print(f"  TOTAL open area headroom = {total_head:.4f} "
          f"(leader needs {score - LEADER:.4f} = "
          f"{100*(score-LEADER)/total_head:.1f}% of it)")

    # ---- 3. leader calibration ----
    print("\n=== 3. leader-gap calibration ===")
    # what uniform depth d on the open set closes the gap?
    cur_open = sum(L[n] / sqrt(n) - 1 for n in open_tied)
    closed = score - cur_open

    def score_at(d):
        return closed + sum(max(grid_L(n) - d, sqrt(n)) / sqrt(n) - 1
                            for n in open_tied)
    lo_d, hi_d = 0.0, 5.0
    for _ in range(80):
        mid = (lo_d + hi_d) / 2
        if score_at(mid) > LEADER:
            lo_d = mid
        else:
            hi_d = mid
    print(f"  uniform depth d* on the {len(open_tied)} open rows to match "
          f"leader: {hi_d:.6f}")
    print(f"  (area-capped absolute floor of the open set = {closed:.6f})")

    # per-block requirement: depth needed if only block k improves
    print("\n  per-block-alone requirement (depth on that block only):")
    for b in blocks:
        lo, hi = b["n_lo"], b["n_hi"]
        ns = [n for n in range(lo, hi + 1) if n in open_tied]
        if not ns:
            continue
        w = sum(1 / sqrt(n) for n in ns)
        need = (score - LEADER) / w
        b["depth_needed_alone"] = need
        b["open_weight"] = w
        if need <= 1.0:
            print(f"    k={b['k']:2d}: {len(ns):3d} open, weight {w:.3f}, "
                  f"depth needed if this block alone: {need:.4f}")

    # ---- 4. envelope structure ----
    print("\n=== 4. L(n) envelope vs grid (selected ranges) ===")
    for lo, hi in ((300, 340), (380, 420), (600, 660), (900, 965)):
        print(f"  n {lo}..{hi}:")
        line = []
        for n in range(lo, hi + 1):
            g = grid_L(n)
            d = g - L[n]
            line.append(f"{n}:{'=' if d<=1e-12 else f'{d:.3f}'}")
        for i in range(0, len(line), 10):
            print("    " + " ".join(line[i:i+10]))

    json.dump({"score": score, "grid": gscore, "leader": LEADER,
               "blocks": blocks,
               "open_tied": open_tied,
               "total_open_headroom": total_head,
               "top40": [{"n": n, "headroom": (grid_L(n)-sqrt(n))/sqrt(n)}
                         for n in rank[:40]]},
              open(OUT, "w"), indent=1)
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
