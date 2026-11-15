#!/usr/bin/env python3
"""Verify current workspace state: packing validity (SAT penetration, bbox)
and exact score of submission.csv. Independent re-implementation (no engine import).
"""
import csv, json, math, sys
from math import ceil, sqrt

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

WS = ROOT + "/workspace"

def half_extent(theta):
    return 0.5 * (abs(math.cos(theta)) + abs(math.sin(theta)))

def corners(x, y, t):
    c, s = math.cos(t), math.sin(t)
    return [(x + c * .5, y + s * .5), (x - s * .5, y + c * .5),
            (x - c * .5, y - s * .5), (x + s * .5, y - s * .5)]

def sat_pen(i, j):
    """max over 4 axes of (hi+hj-|d|); <=0 separated. Min over axes."""
    ci, cj = corners(*i), corners(*j)
    # for unit squares, SAT axis = each square's edge normals
    axes = []
    for sq in (i, j):
        t = sq[2]
        axes += [(math.cos(t), math.sin(t)), (-math.sin(t), math.cos(t))]
    best = None
    dx, dy = j[0] - i[0], j[1] - i[1]
    for ax, ay in axes:
        d = dx * ax + dy * ay
        hi = max(abs(c[0] * ax + c[1] * ay) - i[0] * ax - i[1] * ay for c in [corners(*i)[0]])  # unused
        # extent of square i along axis: project center + unit dirs
        ext_i = 0.5 * (abs(math.cos(i[2]) * ax + math.sin(i[2]) * ay)
                       + abs(-math.sin(i[2]) * ax + math.cos(i[2]) * ay))
        ext_j = 0.5 * (abs(math.cos(j[2]) * ax + math.sin(j[2]) * ay)
                       + abs(-math.sin(j[2]) * ax + math.cos(j[2]) * ay))
        pen = ext_i + ext_j - abs(d)
        if best is None or pen < best:
            best = pen
    return best  # min over axes; <0 => separated by that axis

def max_pen(state):
    """worst (deepest) penetration over all pairs; > 0 means overlap."""
    n = len(state)
    worst = -float('inf')
    for a in range(n):
        for b in range(a + 1, n):
            p = sat_pen(state[a], state[b])
            if p > worst:
                worst = p
    return worst

def bbox(state):
    hs = [half_extent(t) for _, _, t in state]
    w = max(x + h for (x, y, t), h in zip(state, hs)) - min(x - h for (x, y, t), h in zip(state, hs))
    hgt = max(y + h for (x, y, t), h in zip(state, hs)) - min(y - h for (x, y, t), h in zip(state, hs))
    return max(w, hgt), w, hgt

def main():
    # 1. JSON stores
    for fname in ("found.json", "found2.json", "cascade.json"):
        data = json.load(open(f"{WS}/submission/{fname}"))
        bad = []
        for k, rec in sorted(data.items(), key=lambda kv: int(kv[0])):
            st = [tuple(q) for q in rec["state"]]
            mp = max_pen(st)
            L, w, hgt = bbox(st)
            flag = "OK" if (mp <= 1e-9 and L <= rec["L"] + 1e-7) else "BAD"
            if flag == "BAD":
                bad.append(k)
            if int(k) <= 12 or flag == "BAD":
                print(f"{fname} n={k}: declared L={rec['L']:.6f} bbox L={L:.9f} (w={w:.6f} h={hgt:.6f}) max_pen={mp:.2e} {flag}")
        print(f"{fname}: {len(data)} packings, bad: {bad or 'none'}")

    # 2. submission.csv score
    best = {}
    with open(f"{WS}/submission/submission.csv") as f:
        rd = csv.DictReader(f)
        for row in rd:
            n = int(row["n"]); x = float(row["x"]); y = float(row["y"]); t = float(row["angle"])
            best.setdefault(n, []).append((x, y, t))
    total = 0.0
    grid_total = 0.0
    covered = 0
    rows = 0
    for n in range(1, 1001):
        if n in best and len(best[n]) == n:
            st = best[n]
            L, w, hgt = bbox(st)
            mp = max_pen(st)
            if mp > 1e-9:
                print(f"OVERLAP in submission n={n}: pen={mp:.2e}")
            covered += 1
            rows += len(st)
            total += L / sqrt(n) - 1
        else:
            # missing => grid
            total += ceil(sqrt(n)) / sqrt(n) - 1
        grid_total += ceil(sqrt(n)) / sqrt(n) - 1
    print(f"submission.csv: covered {covered}/1000 puzzles, rows={rows}, declared-n set matches: {len(best)}")
    print(f"score = {total:.6f}   (grid ceiling {grid_total:.6f}, improvement {grid_total - total:.6f})")
    # where do we beat grid?
    beats = []
    for n in range(1, 1001):
        if n in best and len(best[n]) == n:
            st = best[n]
            L = bbox(st)[0]
            if L < ceil(sqrt(n)) - 1e-12:
                beats.append((n, round(L, 6), ceil(sqrt(n))))
    print(f"puzzles beating grid: {len(beats)}")
    print(beats[:40])

if __name__ == "__main__":
    main()
