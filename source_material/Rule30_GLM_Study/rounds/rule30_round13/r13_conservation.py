"""Round 13 (EMP, re-checked in Lean by ChemistryLab.lean): is anything conserved in the
Rule 30 "lab"?

A conservation law of range r is a weight f on windows of r consecutive cells, with
f(white...white) = 0, whose total sum_i f(window at i) is the same on every row of the seed run.
Coboundaries f(w) = g(tail w) - g(init w) are conserved for a trivial reason (their total is 0 on
every finite row).  For each r this script computes the dimension of the space of weights whose
total is constant on rows 0..T and compares it with the dimension 2^(r-1) - 1 of the coboundaries;
it reports the first T at which the two agree (no non-trivial law survives).  Exact rationals.

python3 r13_conservation.py      (= r13_conservation_output.txt)
"""
from fractions import Fraction
import itertools


def seed_rows(T):
    cur = {0: 1}
    rows = [dict(cur)]
    for t in range(T):
        new = {}
        for c in range(-t - 1, t + 2):
            v = cur.get(c - 1, 0) ^ (cur.get(c, 0) | cur.get(c + 1, 0))
            if v:
                new[c] = 1
        cur = new
        rows.append(dict(cur))
    return rows


def rank(M):
    M = [[Fraction(x) for x in row] for row in M]
    r = 0
    for c in range(len(M[0]) if M else 0):
        piv = next((i for i in range(r, len(M)) if M[i][c] != 0), None)
        if piv is None:
            continue
        M[r], M[piv] = M[piv], M[r]
        for i in range(len(M)):
            if i != r and M[i][c] != 0:
                f = M[i][c] / M[r][c]
                M[i] = [a - f * b for a, b in zip(M[i], M[r])]
        r += 1
    return r


def counts(row, t, r):
    out = {}
    for i in range(-t - r + 1, t + 1):
        w = tuple(row.get(i + k, 0) for k in range(r))
        if any(w):
            out[w] = out.get(w, 0) + 1
    return out


def main(rmax=6, T=60):
    R = seed_rows(T)
    print("range r | unknown weights | conserved on rows 0..60 | coboundaries | first T with no "
          "non-trivial law")
    for r in range(1, rmax + 1):
        W = [w for w in itertools.product((0, 1), repeat=r) if any(w)]
        c0 = counts(R[0], 0, r)
        M = []
        for t in range(1, T + 1):
            ct = counts(R[t], t, r)
            M.append([ct.get(w, 0) - c0.get(w, 0) for w in W])
        cob = 2 ** (r - 1) - 1
        first = next(TT for TT in range(1, T + 1) if len(W) - rank(M[:TT]) == cob)
        print(f"{r:7d} | {len(W):15d} | {len(W) - rank(M):23d} | {cob:12d} | {first}")
    print("Every weight conserved on those rows is a coboundary: no non-trivial conservation law "
          "of range <= %d in the seed run (Lean: seed_run_no_conservation_law)." % rmax)


if __name__ == "__main__":
    main()
