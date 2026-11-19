"""Run-86 probe: what is inside n = 126 square 120's exact feasible cage?

Read-only.  Prints, in order:
  * which squares the lift leaves unplaced, and what each recovers to;
  * square 120's contact equations (linear in its own position), and their rank;
  * the cage at a few tolerances, with the exact distance to the stored pose;
  * whether the found point passes the full gate.
"""
import sys
sys.path.insert(0, "scripts")
from fractions import Fraction as F

import glm_wheels as G
import qsqrt2 as Q

Q2 = Q.Q2
rows = G._delivered_rows()
N = len(rows[126])
ws = [G._word_of(t) for _, _, t in rows[126]]

CAP = {}
orig = Q.recover_leftovers


def spy(pos, shift, tol, dens, bmax):
    CAP["pre"] = [i for i, p in enumerate(pos) if p is None]
    m = orig(pos, shift, tol, dens, bmax)
    CAP["pos"] = list(pos)
    return m


Q.recover_leftovers = spy
r = Q.lift_sentence([(Q2(x), Q2(y)) for x, y, _ in rows[126]], ws)
Q.recover_leftovers = orig
print("status", r["status"], "unplaced before recovery", CAP["pre"], flush=True)
pos, L = CAP["pos"], r["L"]
print("L =", L, flush=True)

state = [(Q2(x), Q2(y)) for x, y, _ in rows[126]]
ex = [Q.frame_extent(*w) for w in ws]
lo = (min(state[i][0] - ex[i] for i in range(N)),
      min(state[i][1] - ex[i] for i in range(N)))
shift = [(state[i][0] - lo[0], state[i][1] - lo[1]) for i in range(N)]

j = [i for i, p in enumerate(pos) if p is None][0]
tgt = shift[j]
print("unrecovered square", j, "stored", rows[126][j], flush=True)

trial = list(pos)
trial[j] = tgt
print("contacts in the stored pose (|slack| <= 1e-8):", flush=True)
rank_rows = []
for i in range(N):
    if i == j or trial[i] is None:
        continue
    ax = Q.pair_axes(trial, ws, i, j)
    best = min(ax, key=lambda t: abs(t[1]))
    if abs(best[1]) <= Q2(F(1, 10 ** 8)):
        print(f"   {i:3d} axis {best[0]} slack {best[1]}", flush=True)
        rank_rows.append(i)

# Fmt: projection p.q is affine in square j's position, so two evaluations pin it.
def proj_affine(i, q):
    """(a, b, c) with p.q (as a vector) = a*x + b*y for square j vs placed i."""
    t0 = list(trial); t0[j] = (Q2(0), Q2(0))
    t1 = list(trial); t1[j] = (Q2(1), Q2(0))
    t2 = list(trial); t2[j] = (Q2(0), Q2(1))
    v0 = (t0[j][0] - t0[i][0]) * q[0] + (t0[j][1] - t0[i][1]) * q[1]
    v1 = (t1[j][0] - t1[i][0]) * q[0] + (t1[j][1] - t1[i][1]) * q[1]
    v2 = (t2[j][0] - t2[i][0]) * q[0] + (t2[j][1] - t2[i][1]) * q[1]
    return (v1 - v0, v2 - v0, v0)


eqs = []
for i in range(N):
    if i == j or trial[i] is None:
        continue
    ax = Q.pair_axes(trial, ws, i, j)
    best = min(ax, key=lambda t: abs(t[1]))
    if abs(best[1]) > Q2(F(1, 10 ** 8)):
        continue
    q, _s, need, owner = best
    a, b, c = proj_affine(i, q)
    # |p.q| = need  ->  a x + b y = -c +/- need  (sign from the stored pose)
    v = a * tgt[0] + b * tgt[1] + c
    sgn = 1 if v.sign() >= 0 else -1
    eqs.append(((a, b), Q2(0) - c + (need if sgn > 0 else Q2(0) - need), i))
print("linear equations for square", j, ":", len(eqs), flush=True)
for (a, b), rhs, i in eqs:
    print("   (%s) x + (%s) y = %s     [partner %d]" % (a, b, rhs, i), flush=True)

sols = []
for p1 in range(len(eqs)):
    for p2 in range(p1 + 1, len(eqs)):
        (a1, b1), c1, i1 = eqs[p1]
        (a2, b2), c2, i2 = eqs[p2]
        det = a1 * b2 - a2 * b1
        if det.sign() == 0:
            continue
        x = (c1 * b2 - c2 * b1) / det
        y = (a1 * c2 - b1 * c1) / det
        e = ex[j]
        if x - e < Q2(0) or x + e > L or y - e < Q2(0) or y + e > L:
            continue
        cand = list(trial)
        cand[j] = (x, y)
        g = Q.gate(cand, ws)
        sols.append((g["ok"], g["violations"], x, y, i1, i2, abs(x - tgt[0]) + abs(y - tgt[1])))
print("in-box 2x2 solutions:", len(sols), " gate-ok:", sum(1 for s in sols if s[0]), flush=True)
for s in sols[:8]:
    print("   ok=%s viol=%d (%s, %s) dist=%s" % (s[0], s[1], s[2], s[3], s[6]), flush=True)

for tol in ("1e-7", "1e-4"):
    best = G.cage_point(trial, ws, j, L, tgt, tol=Q2(F(tol)))
    print("cage tol", tol, "->", best, flush=True)
