#!/usr/bin/env python3
"""Round 21 (EMP, outside Lean): the period-2 half-line machine, searched fast.

The machine of `PeriodTwoHalfLine.lean`: the cells left of an alternating column evolve on their
own, and at every black time of the column the cell next to it must be black.  For a code of `d`
cells (black at the far end) the machine fails at some first time; `halfBound d` is the largest
such time over all codes and both phases.

Two ways to compute it:

* `brute(d)`  — simulate all `2^(d-1)` codes (what the Lean certificate does);
* `usearch(d)` — search the *half-speed sequence* `u` instead (column `c-2` is constant on each
  black/white pair of times, `TileLeads.alt_pair_constant`): choose one bit of column `c-2` per
  pair of time steps, fill the triangle to the left with the left-solve
  `cell(t, j-1) = cell(t+1, j) xor (cell(t, j) or cell(t, j+1))`, and prune as soon as the row at
  time 0 is not white beyond the edge.  This explores about `2^(d/2)` branches instead of
  `2^d`.  Empirically `usearch(d) + 2 == brute(d)` (checked for d <= 20 below).

Usage:  python3 half_line_search.py check 20     # compare both methods for d <= 20
        python3 half_line_search.py fast 40      # usearch for d <= 40
"""
import sys
import time

sys.setrecursionlimit(100000)


def brute_death(S, ph, cap=10000):
    for t in range(cap):
        b = 1 if t % 2 == ph else 0
        if b == 1 and (S & 1) == 0:
            return t
        S = (S >> 1) ^ (S | ((S << 1) | b))
    return None


def brute(d):
    return max(brute_death(S, ph) for ph in (0, 1) for S in range(1 << (d - 1), 1 << d))


def usearch_phase(d, ph, cap=400):
    best = -1
    maxt = cap + 5
    cols = [[None] * (maxt + 2) for _ in range(maxt + 5)]

    def black(t):
        return t % 2 == ph

    for t in range(maxt + 2):
        cols[0][t] = 1 if black(t) else 0

    def ok(m, v):
        return not ((m > d and v != 0) or (m == d and v != 1))

    def dfs(T):
        nonlocal best
        best = max(best, T - 1)
        if T > cap:
            return
        choices = [cols[2][T - 1]] if (T >= 1 and black(T - 1)) else [0, 1]
        for b in choices:
            cols[2][T] = b
            cols[1][T] = 1 if black(T) else 1 - b
            if T == 0 and not (ok(1, cols[1][0]) and ok(2, cols[2][0])):
                continue
            for m in range(3, T + 3):
                t = T + 2 - m
                cols[m][t] = cols[m - 1][t + 1] ^ (cols[m - 1][t] | cols[m - 2][t])
            if not ok(T + 2, cols[T + 2][0]):
                continue
            dfs(T + 1)

    dfs(0)
    return best


def usearch(d):
    return max(usearch_phase(d, 0), usearch_phase(d, 1)) + 2


if __name__ == "__main__":
    mode, D = sys.argv[1], int(sys.argv[2])
    for d in range(1, D + 1):
        t0 = time.time()
        u = usearch(d)
        line = f"d={d:3d}  halfBound(fast)={u:4d}  2d+8={2 * d + 8:4d}"
        if mode == "check":
            line += f"  brute={brute(d):4d}"
        print(line + f"  ({time.time() - t0:.1f}s)", flush=True)
