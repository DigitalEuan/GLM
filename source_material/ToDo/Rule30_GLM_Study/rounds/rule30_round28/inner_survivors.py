#!/usr/bin/env python3
"""Round 28 (EMP, outside Lean): To Do 19 -- do long survivors carry an alternating inner column?

Period-2 half-line machine, drive word `10` (black at even times; by `halfLineDies_two_iff` the
only word that matters).  For every code of length d <= DMAX (top bit d-1 set) that survives past
its edge (time d - 1), with death time L, let K = L - (d - 1) be its post-edge life and let
A = the longest stretch [s, e] of consecutive times on which SOME inner column c - k (k >= 1, i.e.
bit k - 1 of the state) follows an alternating drive (either phase).

Candidate uniform statement (To Do 19):
    InnerFollows(a): every code with post-edge life K has an inner column alternating for at
    least K - a consecutive steps.
With `inner_alternation_bound` (Lean) a stretch of length A of column c - k starting at time s is
an inner half-line machine of width (d + s) - k that survives A steps, so InnerFollows would feed
a recursion on the width.  This script reports, for each K, the minimum A over all codes, i.e.
the sharpest `a` the data allow, and the depth k and start s of the stretches of the longest
survivors.

Usage: python3 inner_survivors.py [DMAX]   (default 18)
"""
import sys


def step(b, S):
    return (S >> 1) ^ (S | ((S << 1) | b))


def bd(t):
    return 1 if t % 2 == 0 else 0


def life(S, cap=100000):
    t = 0
    while t < cap:
        if bd(t) and (S & 1) == bd(t + 1):
            return t
        S = step(bd(t), S)
        t += 1
    return None


def longest_inner_alternation(S, L):
    """Longest (A, k, s) with column c-k alternating on times s..s+A-1, all within [0, L]."""
    tr = []
    X = S
    for t in range(L + 1):
        tr.append(X)
        X = step(bd(t), X)
    width = S.bit_length() + L + 1
    best = (0, 0, 0)
    for k in range(1, width + 1):
        col = [(tr[t] >> (k - 1)) & 1 for t in range(L + 1)]
        # maximal runs where col[t] != col[t+1] (alternation), as stretches of times
        start = 0
        for t in range(1, L + 2):
            if t == L + 1 or col[t] == col[t - 1]:
                A = t - start
                if A > best[0]:
                    best = (A, k, start)
                start = t
    return best


def main():
    DMAX = int(sys.argv[1]) if len(sys.argv) > 1 else 18
    minA = {}          # K -> (min A, witness)
    print("d  survivors_past_edge  Lmax  (A,k,s) of a longest survivor")
    for d in range(2, DMAX + 1):
        surv = 0
        top = None
        for S in range(1 << (d - 1), 1 << d):
            L = life(S)
            K = L - (d - 1)
            if K <= 0:
                continue
            surv += 1
            A, k, s = longest_inner_alternation(S, L)
            if K not in minA or A < minA[K][0]:
                minA[K] = (A, (d, S, k, s))
            if top is None or L > top[0]:
                top = (L, S, (A, k, s))
        print("%2d %8d %6s %s" % (d, surv, top[0] if top else "-", top[2] if top else "-"))
    print("\nK (post-edge life) -> minimum longest inner alternation A over all codes, K - A")
    worst = None
    for K in sorted(minA):
        A, w = minA[K]
        print("K=%3d  min A=%3d  K-A=%3d  witness d=%d S=%d (k=%d, s=%d)" % (K, A, K - A, *w))
        worst = K - A if worst is None else max(worst, K - A)
    print("\nsharpest slack a with InnerFollows(a) on this range: %d" % worst)


if __name__ == "__main__":
    main()
