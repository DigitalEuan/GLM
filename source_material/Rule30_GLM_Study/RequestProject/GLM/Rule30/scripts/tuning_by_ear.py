#!/usr/bin/env python3
"""Round 25 (EMP): tuning the Rule 30 centre column "by ear" with periodic tunes.

Purpose: for each prefix length n, compute tuneCost(n) = least tau + p (p >= 1) of an eventually
periodic law (transient tau, period p) consistent with the first n centre bits (the Lean
definition `tuneCost` in TuningByEar.lean), the excess n - tuneCost(n), and how often the best tune
changes.  Algorithm: for each period p keep the last position i with s[i] != s[i+p], i + p < n;
the least consistent transient for p is that position + 1.  Outside Lean; unchecked.  The Lean
certificates (TuningByEarData.lean) re-check the bounds used there.

Usage: python3 tuning_by_ear.py [N]   (default N = 2000)
"""
import sys

def centre(N):
    w = 2 * N + 3; row = [0] * w; row[N + 1] = 1; out = []
    for _ in range(N):
        out.append(row[N + 1])
        row = [0] + [row[i - 1] ^ (row[i] | row[i + 1]) for i in range(1, w - 1)] + [0]
    return out

N = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
s = centre(N)
lastmis = {}
best = (-1, 0, None); prev = None; changes = 0; worst_log = -99
for n in range(N + 1):
    if n >= 1:
        j = n - 1
        for p in range(1, j + 1):
            if s[j - p] != s[j]:
                lastmis[p] = j - p
    c, p = min(((lastmis.get(p, -1) + 1) + p, p) for p in range(1, n + 2))
    tune = (c - p, p)
    if prev is not None and tune != prev:
        changes += 1
    prev = tune
    ex = n - c
    if ex > best[0]:
        best = (ex, n, tune)
    lg = n.bit_length() - 1 if n >= 1 else 0  # exact floor(log2 n) (Round 31: no floating point)
    worst_log = max(worst_log, ex - (2 * lg + 2))
    if n in (10, 50, 100, 200, 448, 500, 1000, 1500, 2000, 3000, 5000):
        print(f"n={n:5d} tuneCost={c:5d} best tune (tau,p)={tune} excess={ex:3d} "
              f"max excess so far={best[0]} at n={best[1]} tune={best[2]} mind changes={changes}")
print(f"max over n<={N} of excess - (2 log2 n + 2): {worst_log}  (<= 0 means TuneExcessLog holds)")
