#!/usr/bin/env python3
"""Round 23 (EMP): the counting law RunCount p d T, by brute force.

RunCount p d T = number of left-white rows with black edge at 0 and free cells x_1..x_{d+T}
(white beyond) such that the column at distance d satisfies col(t) = col(t-p) for p <= t <= T.
This is the same quantity as `RunCount` in `RunCountLaw.lean`.

Lean proves RunCount p d T = 2^(d+p-1) for p-1 <= T < d (`runCount_law`).  This script shows
the table, including T >= d where the law stops (e.g. RunCount 2 3 3 = 20, RunCount 2 4 4 = 20).

Usage: python3 run_count.py      (about a minute; output in run_count_output.txt)
"""


def column(x, T, d):
    pad = T + 2
    row = [0] * pad + x + [0] * pad
    c = pad + d
    col = []
    for _ in range(T + 1):
        col.append(row[c])
        row = [0] + [row[i - 1] ^ (row[i] | row[i + 1]) for i in range(1, len(row) - 1)] + [0]
    return col


def run_count(p, d, T):
    L = d + T
    cnt = 0
    for bits in range(2 ** L):
        x = [1] + [(bits >> i) & 1 for i in range(L)]
        col = column(x, T, d)
        if all(col[t] == col[t - p] for t in range(p, T + 1)):
            cnt += 1
    return cnt


if __name__ == "__main__":
    print("p = 2: row d lists RunCount 2 d T for T = 0 .. d+3; law value 2^(d+1) for 1 <= T < d")
    for d in range(1, 9):
        print(d, [run_count(2, d, T) for T in range(0, d + 4)], "law:", 2 ** (d + 1))
