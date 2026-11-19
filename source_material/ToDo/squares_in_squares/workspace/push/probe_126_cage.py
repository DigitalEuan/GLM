"""Run-86: does n = 126's square 120 admit a Q(sqrt 2) placement in its cage?"""
import sys
sys.path.insert(0, "scripts")
from fractions import Fraction as F

import glm_wheels as G
import qsqrt2 as Q

Q2 = Q.Q2
rows = G._delivered_rows()
st126 = rows[126]
N = len(st126)
ws = [G._word_of(t) for _, _, t in st126]

CAP = {}
orig = Q.recover_leftovers


def spy(pos, shift, tol, dens, bmax):
    m = orig(pos, shift, tol, dens, bmax)
    CAP["pos"] = list(pos)
    return m


Q.recover_leftovers = spy
r = Q.lift_sentence([(Q2(x), Q2(y)) for x, y, _ in st126], ws)
Q.recover_leftovers = orig
pos = CAP["pos"]
L = r["L"]
j = [i for i, p in enumerate(pos) if p is None][0]
state = [(Q2(x), Q2(y)) for x, y, _ in st126]
ex = [Q.frame_extent(*w) for w in ws]
lo = (min(state[i][0] - ex[i] for i in range(N)),
      min(state[i][1] - ex[i] for i in range(N)))
tgt = (state[j][0] - lo[0], state[j][1] - lo[1])
c = Q2(F(11, 2)) + Q2(0, F(5, 2))       # the rank-1 contact law: y - x = c
LO, HI = F(1335, 1000), F(1372, 1000)   # the measured feasible interval on the line

found = []
for D in (8, 16, 32):
    for pn in range(int(LO * D) - 1, int(HI * D) + 2):
        for rn in range(-8 * D, 8 * D + 1):
            x = Q2(F(pn, D), F(rn, D))
            if not (LO <= x.a <= HI):
                continue
            y = x + c
            e = ex[j]
            if y - e < Q2(0) or y + e > L:
                continue
            cand = list(pos)
            cand[j] = (x, y)
            g = Q.gate(cand, ws)
            if g["ok"] and g["clearance"] == 0:
                found.append((abs(x - tgt[0]) + abs(y - tgt[1]), x, y, D, g["contacts"]))
    print(f"D={D}: {len(found)} accepted so far", flush=True)

found.sort(key=lambda t: t[0])
print("Q(sqrt2) realisations inside the cage at clearance 0:", len(found), flush=True)
for d, x, y, D, ct in found[:5]:
    print(f"   ({x}, {y})  D={D} delta={float(d.decimal()):.3e} contacts={ct}", flush=True)
