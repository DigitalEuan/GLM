#!/usr/bin/env python3
"""Round 33, To Do 29: the sideways reconstruction for the period-2 drive 10, column by column,
as exact Boolean polynomials (algebraic normal form over GF(2)) in the free bits
a_s = u(2s+1) of the admissible first column (u(2s) = 1 is forced).

Prints, for columns k = 1..KMAX, the number of monomials and the degree at times 0..7; and the
ANF of recon(k, t) for columns 1..6 and times 0..3.  Columns 1-5 match the closed forms proved in
SidewaysPeriodTwo.lean (col2_even ... col5_even); from column 4 on the degree grows.

Exact arithmetic only: a polynomial is a set of monomials, a monomial a frozenset of indices.
Run: python3 sideways_period_two.py [KMAX]
"""
import sys
from functools import lru_cache

ONE = frozenset([frozenset()])
ZERO = frozenset()


def X(a, b):
    return frozenset(a ^ b)


def A(a, b):
    r = set()
    for m in a:
        for n in b:
            r ^= {m | n}
    return frozenset(r)


def O(a, b):
    return X(X(a, b), A(a, b))


def var(i):
    return frozenset([frozenset([i])])


def bd(t):
    return ONE if t % 2 == 0 else ZERO


def u(t):
    return ONE if t % 2 == 0 else var(t // 2)


@lru_cache(None)
def rec(k, t):
    if k == 0:
        return bd(t)
    if k == 1:
        return u(t)
    return X(rec(k - 1, t + 1), O(rec(k - 1, t), rec(k - 2, t)))


def show(f):
    if not f:
        return "0"
    mons = sorted(("*".join("a%d" % i for i in sorted(m)) or "1") for m in f)
    return " + ".join(sorted(mons, key=lambda s: (len(s), s)))


def main():
    kmax = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    print("# column k: [monomials at t = 0..7]  degree [at t = 0..7]")
    for k in range(1, kmax + 1):
        print(k, [len(rec(k, t)) for t in range(8)], "deg",
              [max((len(m) for m in rec(k, t)), default=0) for t in range(8)])
    print("# closed forms, columns 1..6, times 0..3")
    for k in range(1, 7):
        for t in range(4):
            print("recon(%d, %d) = %s" % (k, t, show(rec(k, t))))


if __name__ == "__main__":
    main()
