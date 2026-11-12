#!/usr/bin/env python3
"""Exact-arithmetic wobble statistics for the Rule 30 centre column.

Integers and fractions.Fraction only: no floating point, no numpy.

The centre column a(0), a(1), ... of Rule 30 from a single black cell is generated with the
bit-parallel step  r -> (r << 2) ^ ((r << 1) | r)  (bit t of the row after t steps is the
centre cell; this is the same encoding that the Lean file Compute.lean proves correct).

For every N in [1, LIMIT] it tracks the delta-sigma accumulator D(N) = 2*#ones - N and the
exact squared ratio D(N)^2 / N, reporting the running maxima at each power of ten.
Comparing D^2/N with C^2 is the exact form of |D(N)| <= C*sqrt(N).

Usage:  python3 wobble_certificate.py [LIMIT]      (default 10**6; takes a few minutes)
The results for LIMIT = 10**6 are recorded in wobble_certificate_output.txt.
"""
import sys
from fractions import Fraction

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10**6
    r = 1
    D = 0
    best = Fraction(0)          # max of D(N)^2 / N
    best_at = 0
    maxabs = 0
    maxabs_at = 0
    checkpoints = {10**k for k in range(1, 8)}
    keep = (1 << (limit + 1)) - 1
    print("N, D(N), max_{k<=N} |D(k)|, argmax, max_{k<=N} D(k)^2/k (exact), argmax")
    for t in range(limit):
        bit = (r >> t) & 1
        D += 1 if bit else -1
        N = t + 1
        if abs(D) > maxabs:
            maxabs, maxabs_at = abs(D), N
        q = Fraction(D * D, N)
        if q > best:
            best, best_at = q, N
        if N in checkpoints:
            print(f"{N}, {D}, {maxabs}, {maxabs_at}, {best.numerator}/{best.denominator}, {best_at}")
            sys.stdout.flush()
        # next row.  A new bit k only depends on old bits k-2, k-1, k, and the centre cell at
        # time t is bit t, so bits above index `limit` are never needed: trim them.
        r = ((r << 2) ^ ((r << 1) | r)) & keep
    # exact comparison with C = 2 : D^2 <= 4 N for all N <= limit ?
    print(f"max D(N)^2/N over N <= {limit} = {best} (at N = {best_at});"
          f" bound |D(N)| <= 2 sqrt(N) holds up to {limit}: {best <= 4}")

if __name__ == "__main__":
    main()
