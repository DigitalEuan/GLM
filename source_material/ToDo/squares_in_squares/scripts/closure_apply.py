#!/usr/bin/env python3
"""closure_apply.py — global removal-closure of table.json.

F(n) = min over m >= n of L(m)  (prefix-min from above).
Removing squares from a packing never grows its bounding box, so every
n < m inherits L(m) for free.  For each n with F(n) < L(n):
  - candidate bases: all m >= n with L(m) == F(n)
  - remove (m - n) squares greedily: at each step drop the square whose
    removal most reduces max(w, h); recenter to origin.
  - keep the candidate with the smallest resulting bbox side.
Verified per entry with packlib (SAT non-overlap, tol 1e-9, containment).
Iterated to fixpoint (a smaller L at n can serve n' < n as a base).
"""
import json
import os
import sys
from math import ceil, sqrt, cos, sin

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import packlib as P

SUB = "/home/z/my-project/workspace/submission"
TAB = os.path.join(SUB, "table.json")


def extents(state):
    # per-square (left, right, bottom, top) in bbox terms
    out = []
    for (x, y, t) in state:
        c, s = abs(cos(t)), abs(sin(t))
        ex = 0.5 * (c + s)
        out.append((x - ex, x + ex, y - ex, y + ex))
    return out


def bbox_wh(state):
    ext = extents(state)
    lox = min(e[0] for e in ext); hix = max(e[1] for e in ext)
    loy = min(e[2] for e in ext); hiy = max(e[3] for e in ext)
    return hix - lox, hiy - loy, lox, hix, loy, hiy


def remove_greedy(state, k):
    """Drop k squares, each time the one that most reduces max(w,h)."""
    st = [tuple(q) for q in state]
    for _ in range(k):
        ext = extents(st)
        lox = min(e[0] for e in ext); hix = max(e[1] for e in ext)
        loy = min(e[2] for e in ext); hiy = max(e[3] for e in ext)
        base = max(hix - lox, hiy - loy)
        best_i, best_val = None, base
        for i in range(len(st)):
            # recompute extremes without i (only matters if i is at an extreme)
            others = [ext[j] for j in range(len(st)) if j != i]
            nlox = min(o[0] for o in others); nhix = max(o[1] for o in others)
            nloy = min(o[2] for o in others); nhiy = max(o[3] for o in others)
            val = max(nhix - nlox, nhiy - nloy)
            if val < best_val - 1e-12:
                best_val, best_i = val, i
        if best_i is None:
            # no single removal reduces the bbox: drop an interior square
            # (closest to the center, least likely to matter later)
            cx = (lox + hix) / 2; cy = (loy + hiy) / 2
            best_i = min(range(len(st)), key=lambda i: (st[i][0] - cx) ** 2 + (st[i][1] - cy) ** 2)
        st.pop(best_i)
    return st


def finalize(state):
    """Recenter to origin; return (state, L)."""
    w, h, lox, hix, loy, hiy = bbox_wh(state)
    cx, cy = (lox + hix) / 2, (loy + hiy) / 2
    out = [(q[0] - cx, q[1] - cy, q[2]) for q in state]
    return out, max(w, h)


def main():
    tab = json.load(open(TAB))
    rounds = 0
    while True:
        rounds += 1
        L = {n: tab[str(n)]["L"] for n in range(1, 1001)}
        F, cur = {}, float("inf")
        for n in range(1000, 0, -1):
            cur = min(cur, L[n])
            F[n] = cur
        impr = [n for n in range(1, 1001) if F[n] < L[n] - 1e-12]
        if not impr:
            break
        print(f"round {rounds}: {len(impr)} improvements")
        for n in impr:
            cands = [m for m in range(n, 1001) if abs(L[m] - F[n]) < 1e-12]
            best = None
            for m in cands:
                st = remove_greedy(tab[str(m)]["state"], m - n)
                st, Ln = finalize(st)
                if best is None or Ln < best[1] - 1e-12:
                    best = (st, Ln, m)
            st, Ln, m = best
            r = P.verify(st, tol=1e-9)
            assert r["ok"] and r["L"] <= Ln + 1e-9, f"n={n} verify failed: {r}"
            tab[str(n)] = {"L": round(Ln, 12), "state": [[round(q[0], 12), round(q[1], 12), round(q[2], 12)] for q in st],
                           "src": f"closure:removal-from-{m}:{tab[str(m)].get('src','?')[:30]}"}
        json.dump(tab, open(TAB, "w"))
    # summary
    grid = sum(1 for n in range(1, 1001) if tab[str(n)]["src"].startswith("grid"))
    sc = sum(tab[str(n)]["L"] / sqrt(n) - 1 for n in range(1, 1001))
    print(f"fixpoint after {rounds-1} apply-rounds | score={sc:.6f} | grid-tied={grid} | beats={1000-grid}")
    json.dump(tab, open(TAB, "w"))


if __name__ == "__main__":
    main()
