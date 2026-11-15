#!/usr/bin/env python3
"""strip_decode.py — run 25 P1: decode the imported Göbel-strip states.

Maps each stored state to the (p,q) frame (p along the diagonal,
p=(x+y)/sqrt(2), q=(x-y)/sqrt(2)); in that frame the strip is the classic
Göbel picture: an axis-aligned chain on the p-axis (theta=pi/4 in xy),
tip diamonds in the acute corners, and rigid diamond staircases filling
the wings.  Prints the decoded lattice so the (a, w) parametrization can
be read off and checked against n = floor(a^2+a+3+(a-1)sqrt(2)).
"""
import json
import math
import sys

W = "/home/z/my-project"
sys.path.insert(0, W + "/scripts")

TAB = W + "/workspace/submission/table.json"
SQ2 = math.sqrt(2.0)


def pq(x, y):
    return (x + y) / SQ2, (x - y) / SQ2


def decode(n, row):
    L, st = row["L"], row["state"]
    a = L - 1 - 1 / SQ2
    C = L * SQ2 / 2.0
    chain, tips, stair = [], [], []
    for (x, y, th) in st:
        p, q = pq(x, y)
        if abs(th - math.pi / 4) < 1e-6:
            chain.append((p, q))
        elif abs(th) < 1e-9:
            # diamond in (p,q); classify: on-axis tips vs wing staircases
            if abs(q) < 1e-6:
                tips.append((p, q))
            else:
                stair.append((p, q))
    chain.sort(); tips.sort(); stair.sort()
    print(f"n={n}  a={a:.6f}  L={L:.9f}  C=L*sqrt2/2={C:.6f}")
    print(f"  chain ({len(chain)}): p={sorted(round(p,6) for p,_ in chain)} "
          f"q-set={sorted(set(round(q,6) for _, q in chain))}")
    print(f"  tips  ({len(tips)}): {[(round(p,6), round(q,6)) for p, q in tips]}")
    lv = {}
    for p, q in stair:
        lv.setdefault(round(abs(q), 6), []).append(round(p, 6))
    for qc in sorted(lv):
        ps = sorted(lv[qc])
        # level parameters: q_c = E + k/sqrt2 ; count; extremes
        print(f"  |q|={qc:9.6f}  n_d={len(ps):2d}  p={ps}")
    # derived: level-k extreme P_k should equal (a-k)/sqrt2 (w=1 theory)
    for qc in sorted(lv):
        k = round((qc - 0.5) * SQ2, 6)
        Pk = (a - k) / SQ2 if k <= a + 0.001 else None
        pmax = max(lv[qc])
        print(f"    level k={k:.3f}: extreme p={pmax:.6f} "
              f"(P_k=(a-k)/sqrt2={Pk:.6f})" if Pk is not None else
              f"    level beyond a: q={qc}")
    print()


def main():
    tab = json.load(open(TAB))
    for n in (5, 10, 27, 38, 52, 67):
        decode(n, tab[str(n)])


if __name__ == "__main__":
    main()
