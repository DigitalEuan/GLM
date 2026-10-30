"""Round 7 (empirical, not a proof): constant runs in the Rule 30 centre column.

The Lean theorem `centerCol_change_in_window` proves that a run of equal centre-column values
starting at time N has length at most 3N + 6 (every window [N, 4N+6] contains a change).
This script measures the actual runs, to show how far the proved bound is from the data.
Integers only (Python big-int row, bit-parallel Rule 30).
"""
from fractions import Fraction

T = 20000
row = 1 << T            # single black cell at bit T (the centre)
mask = (1 << (2 * T + 1)) - 1
col = []
for t in range(T):
    col.append((row >> T) & 1)
    # new = left xor (centre or right); the first 20 bits printed below match OEIS A051023
    row = ((row << 1) ^ (row | (row >> 1))) & mask
runs, i = [], 0
while i < T:
    j = i
    while j < T and col[j] == col[i]:
        j += 1
    runs.append((i, j - i))
    i = j
longest = max(r for _, r in runs)
print("first 20 centre-column bits:", "".join(map(str, col[:20])))
print("time steps:", T)
print("number of runs:", len(runs))
print("longest run:", longest, "starting at", [s for s, r in runs if r == longest])
print("worst ratio run/(3N+6) over runs with N>=1:",
      max(Fraction(r, 3 * s + 6) for s, r in runs if s >= 1))
