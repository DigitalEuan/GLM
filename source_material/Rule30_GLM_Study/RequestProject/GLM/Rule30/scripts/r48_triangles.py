#!/usr/bin/env python3
"""Round 48 (EMP, exact integer arithmetic, not machine-checked).

Statistics of the white runs (tops of white triangles) of Rule 30 from a single black cell.

  python3 r48_triangles.py [T]      (default T = 10000)

Prints
  1. the longest white run in each eighth of the row (left -> right), and the number of runs of
     length >= 8, 12, 16, 20 per eighth, over rows 100 <= t < T;
  2. the record white runs one cell inside the right edge (they occur at rows t = 2^k);
  3. black line segments heading left-down versus right-down: count and mean length.
"""
import re
import sys

T = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
MASK = (1 << (2 * T + 3)) - 1


def rows():
    r = 1 << T  # bit i  <->  cell x = i - T
    for t in range(T):
        yield t, r
        r = ((r << 1) ^ (r | (r >> 1))) & MASK


def segment(t, r):
    s = bin(r)[2:].zfill(2 * T + 1)[::-1]
    return s[T - t:T + t + 1]  # index j <-> x = j - t


K = 8
mx = [0] * K
ths = (8, 12, 16, 20)
cnt = [[0] * K for _ in ths]
edge_best = 0
edge_records = []
prev = None
ld_len = {}  # running lengths of black left-down / right-down lines ending at each cell
rd_len = {}
ld_done = []
rd_done = []
for t, r in rows():
    seg = segment(t, r)
    if t >= 100:
        for m in re.finditer('0+', seg):
            a, b = m.start(), m.end() - 1
            L = b - a + 1
            k = min(K - 1, (a + b) * K // (4 * t))
            mx[k] = max(mx[k], L)
            for j, th in enumerate(ths):
                if L >= th:
                    cnt[j][k] += 1
    for m in re.finditer('0+', seg):
        a, b = m.start(), m.end() - 1
        if 2 * t - b == 1 and b - a + 1 > edge_best:
            edge_best = b - a + 1
            edge_records.append((t, edge_best))
    # line segments (only rows t < 2000 to keep it quick)
    if t < 2000:
        new_ld, new_rd = {}, {}
        for j, ch in enumerate(seg):
            if ch == '1':
                x = j - t
                new_ld[x] = ld_len.get(x + 1, 0) + 1
                new_rd[x] = rd_len.get(x - 1, 0) + 1
        for x, L in ld_len.items():
            if x - 1 not in new_ld and x + t - 1 > 1:  # line ended (skip the two edge lines)
                ld_done.append(L)
        for x, L in rd_len.items():
            if x + 1 not in new_rd and x != t - 1:  # skip the right edge
                rd_done.append(L)
        ld_len, rd_len = new_ld, new_rd

print("rows 100 <= t <", T)
print("longest white run by eighth of row (left -> right):", mx)
for j, th in enumerate(ths):
    print("runs of length >=", th, "by eighth:", cnt[j])
print("record white runs one cell inside the right edge (t, length):", edge_records)
print("finished black line segments, rows < 2000:")
print("  left-down : count", len(ld_done), "mean length", round(sum(ld_done) / len(ld_done), 3),
      "max", max(ld_done))
print("  right-down: count", len(rd_done), "mean length", round(sum(rd_done) / len(rd_done), 3),
      "max", max(rd_done))
