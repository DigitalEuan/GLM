#!/usr/bin/env python3
"""Score an existing submission.csv (or the stores) with packlib."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import packlib as P
ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

def main():

    path = sys.argv[1] if len(sys.argv) > 1 else ROOT + "/workspace/submission/submission.csv"
    by_n = P.read_csv(path)
    # convert to store of verified states
    detail = {}
    total = 0.0
    grid_total = 0.0
    overlaps = []
    for n in range(1, 1001):
        g = P.grid_L(n)
        grid_total += g / n ** 0.5 - 1
        if n in by_n and len(by_n[n]) == n:
            r = P.verify(by_n[n])
            if not r["ok"]:
                overlaps.append((n, r["worst_pen"]))
            L = r["L"]
            detail[n] = (L, L / n ** 0.5 - 1, "sub", by_n[n])
            total += L / n ** 0.5 - 1
        else:
            k, st = P.grid_packing(n)
            detail[n] = (k, k / n ** 0.5 - 1, "grid", st)
            total += k / n ** 0.5 - 1
    print(f"file: {path}")
    print(f"covered puzzles: {sum(1 for n in detail if detail[n][2]=='sub')}")
    print(f"overlap failures: {overlaps or 'none'}")
    print(f"SCORE = {total:.6f}")
    print(f"grid ceiling = {grid_total:.6f}")
    print(f"improvement = {grid_total - total:.6f}")
    beats = [(n, round(d[0], 6), P.grid_L(n)) for n, d in detail.items()
             if d[2] == 'sub' and d[0] < P.grid_L(n) - 1e-12]
    print(f"puzzles beating grid: {len(beats)}")
    print(beats[:50] if len(beats) <= 50 else f"{beats[:20]} ... ({len(beats)} total)")

if __name__ == "__main__":
    main()
