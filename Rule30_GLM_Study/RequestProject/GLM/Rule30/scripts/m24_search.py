#!/usr/bin/env python3
"""Round 32 (EMP tool): M24 generators for the GLM Golay code, and a labelling of the
24-cell Rule 30 ring sharing 12 symmetries with M24.

Exact integer arithmetic only; no randomness, no hashing of data (Python sets/dicts are used
only as exact membership tables).  Deterministic: the same output on every run.

1. Builds the GLM code from the 12 generator rows (ShortcutNetworkData.golayRows).
2. Finds code automorphisms by backtracking (images of cells 0,1,2,...; an automorphism is
   pinned down by the Steiner system S(5,8,24): every 5 cells lie in exactly one octad).
3. Picks the first pair of automorphisms whose words act 5-homogeneously (orbit of a 5-set has
   all C(24,5) = 42504 sets); these are the generators gM0, gM1 of MathieuOrbitsData.lean.
4. Breadth-first over words in gM0, gM1 until an element with cycle type 12^2 appears, and lays
   its two 12-cycles on the even and odd ring cells: this is tau0 (MathieuRule30Data.lean).
5. Cross-checks the counts certified in Lean: rotations preserving the code in the GLM labelling,
   the 423 rotation-test survivors among the 735471 eight-cell patterns, the octad orbit size.

Usage: python3 m24_search.py > m24_search_output.txt   (a few seconds)
"""
import itertools

ROWS = [16769025, 4681730, 10727428, 13750280, 6877200, 11825184,
        14299200, 15536256, 7770368, 3887616, 1946624, 9361408]
MASK = (1 << 24) - 1


def popcount(x):
    return bin(x).count("1")


def build_code():
    code = set()
    for m in range(4096):
        x = 0
        for j in range(12):
            if m >> j & 1:
                x ^= ROWS[j]
        code.add(x)
    return code


CODE = build_code()
OCTADS = sorted(c for c in CODE if popcount(c) == 8)
OCT5 = {}
for o in OCTADS:
    pts = [i for i in range(24) if o >> i & 1]
    for s in itertools.combinations(pts, 5):
        OCT5[s] = o


def octad_of(points):
    return OCT5[tuple(sorted(points))]


def apply(g, x):
    """Move cell i of pattern x to cell g[i]."""
    y = 0
    for i in range(24):
        if x >> i & 1:
            y |= 1 << g[i]
    return y


def is_aut(g):
    return all(apply(g, r) in CODE for r in ROWS)


def search(prefix):
    img = list(prefix)

    def ok(k):
        p = k - 1
        for s in itertools.combinations(range(k - 1), 4):
            S = s + (p,)
            O = octad_of(S)
            O2 = octad_of([img[i] for i in S])
            for q in range(k):
                if ((O >> q) & 1) != ((O2 >> img[q]) & 1):
                    return False
        return True

    for k in range(5, len(img) + 1):
        if not ok(k):
            return None

    def rec(k):
        if k == 24:
            return list(img)
        used = set(img)
        for v in range(24):
            if v in used:
                continue
            img.append(v)
            if k < 4 or ok(k + 1):
                r = rec(k + 1)
                if r:
                    return r
            img.pop()
        return None

    return rec(len(img))


def orbit(seed, gens):
    seen = {seed}
    frontier = [seed]
    while frontier:
        nxt = []
        for y in frontier:
            for g in gens:
                z = apply(g, y)
                if z not in seen:
                    seen.add(z)
                    nxt.append(z)
        frontier = nxt
    return seen


def rot(x, k):
    k %= 24
    return x if k == 0 else ((x << k) | (x >> (24 - k))) & MASK


def cycle_type(g):
    seen, t = set(), []
    for i in range(24):
        if i in seen:
            continue
        n, j = 0, i
        while j not in seen:
            seen.add(j)
            j = g[j]
            n += 1
        t.append(n)
    return sorted(t)


def main():
    print("codewords", len(CODE), "octads", len(OCTADS))
    prefixes = [[1, 2, 3, 4, 5], [0, 1, 2, 3, 5, 4], [1, 0, 2, 3, 4], [0, 1, 2, 4, 3],
                [23, 22, 21, 20, 19], [12, 0, 1, 2, 3], [0, 12, 13, 14, 15]]
    cands = [g for g in (search(p) for p in prefixes) if g]
    gens = None
    for a, b in itertools.combinations(range(len(cands)), 2):
        if len(orbit(31, [cands[a], cands[b]])) == 42504:
            gens = [cands[a], cands[b]]
            break
    g0, g1 = gens
    print("gM0", g0, "automorphism:", is_aut(g0))
    print("gM1", g1, "automorphism:", is_aut(g1))
    print("gM0 inverse", [g0.index(i) for i in range(24)])
    print("gM1 inverse", [g1.index(i) for i in range(24)])
    for k, seed in [(1, 1), (2, 3), (3, 7), (4, 15), (5, 31)]:
        print("orbit of", k, "cells:", len(orbit(seed, gens)))
    print("orbit of octad 9335:", len(orbit(9335, gens)))
    print("orbit of dodecad 8190:", len(orbit(8190, gens)))
    print("GLM labelling, turns preserving the code:",
          [k for k in range(24) if all(rot(r, k) in CODE for r in ROWS)])
    allowed = {0, 8, 12, 16, 24}
    surv = 0
    for c in itertools.combinations(range(24), 8):
        w = sum(1 << i for i in c)
        if all(popcount(w ^ rot(w, k)) in allowed for k in range(24)):
            surv += 1
    print("rotation-test survivors among 8-cell patterns:", surv, "(octads: 759)")

    def mul(a, b):
        return tuple(a[b[i]] for i in range(24))
    ident = tuple(range(24))
    seen, frontier, found = {ident}, [ident], None
    while frontier and not found:
        nxt = []
        for h in frontier:
            for g in (g0, g1):
                z = mul(g, h)
                if z in seen:
                    continue
                seen.add(z)
                nxt.append(z)
                if cycle_type(z) == [12, 12]:
                    found = z
                    break
            if found:
                break
        frontier = nxt
    cycles, used = [], set()
    for i in range(24):
        if i in used:
            continue
        c, j = [], i
        while j not in used:
            used.add(j)
            c.append(j)
            j = found[j]
        cycles.append(c)
    tau = [0] * 24
    for j in range(12):
        tau[cycles[0][j]] = 2 * j
        tau[cycles[1][j]] = 2 * j + 1
    placed = set(apply(tau, c) for c in CODE)
    print("element of type 12^2:", list(found))
    print("tau0", tau)
    print("tau0 inverse", [tau.index(i) for i in range(24)])
    print("tau0 labelling, turns preserving the laid-out code:",
          [k for k in range(24) if all(rot(d, k) in placed for d in placed)])


if __name__ == "__main__":
    main()
