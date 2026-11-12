#!/usr/bin/env python3
"""Round 33: summary of ``word_lifetimes33.c`` outputs on the observer's clock.

For each word (p, k) with b black cells and each code length d, the longest life Lmax(d) ends
with a failing test whose number is n(d) = testsBefore(Lmax(d)) + 1 (TestCountLaw.lean).  The
observer-clock excess is n(d) - d.  Printed per word: the largest d, the largest excess and where,
the excesses at the last four lengths, and the wall-clock ratio Lmax(d)/d at the largest d next
to the inverse test density p/b (exact fractions).  Then the largest excess per period.

Exact arithmetic only (integers and fractions.Fraction).

    python3 word_lifetimes33_summary.py OUTPUT...
"""
import sys
from fractions import Fraction


def read(path):
    for line in open(path):
        if not line.startswith("word"):
            continue
        head, data = line.split(":", 1)
        parts = head.split()
        p, k, b = int(parts[1][2:]), int(parts[2][2:]), int(parts[3][7:])
        rows = []
        for x in data.split():
            f = x.split(":")
            if len(f) == 3 and all(y.isdigit() for y in f):
                rows.append(tuple(int(y) for y in f))
        if rows:
            yield p, k, b, rows


def main():
    per_period = {}
    seen = set()
    for path in sys.argv[1:]:
        for p, k, b, rows in read(path):
            key = (p, k)
            if key in seen:
                continue
            seen.add(key)
            ex = []
            for d, L, S in rows:
                n = sum((k >> (t % p)) & 1 for t in range(L + 1))
                ex.append((n - d, d))
            m = max(ex)
            dmax, Lm = rows[-1][0], rows[-1][1]
            word = "".join(str((k >> t) & 1) for t in range(p))
            print("p=%d k=%-3d word=%-8s b=%d d<=%-2d max(tests-d)=%-3d at d=%-2d last4=%s  "
                  "Lmax/d=%s  p/b=%s" % (p, k, word, b, dmax, m[0], m[1],
                                         [e for e, _ in ex[-4:]], Fraction(Lm, dmax),
                                         Fraction(p, b)))
            if p not in per_period or m[0] > per_period[p][0]:
                per_period[p] = (m[0], k, m[1])
    print("largest excess tests - d per period (over the words listed above):")
    for p in sorted(per_period):
        e, k, d = per_period[p]
        print("  p=%d: %d (word k=%d at d=%d)" % (p, e, k, d))


if __name__ == "__main__":
    main()
