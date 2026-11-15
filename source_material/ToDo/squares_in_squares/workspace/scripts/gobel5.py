#!/usr/bin/env python3
r"""gobel5.py — Run 14: the free-placement block family (the exact
instrument; completes the 0-deg + 45-deg architecture programme).

Prior sweeps (gobel2/gobel3/gobel4/theta_family) placed the 45 deg block
CENTRED and charged each staircase pair its deepest corner
(S >= max(a1,a4)+1+b/sqrt2).  The block position is a free variable, so
the true family is bigger: for a box of side S with 0-deg corner
staircases a1..a4 at (0,0),(S,0),(0,S),(S,S) and a b x c block at 45 deg
with centre (cx,cy), ext = (b+c)/(2*sqrt2), feasibility is exactly the
half-plane system

    cx >= ext,  cy >= ext,  cx <= S-ext,  cy <= S-ext      (block in box)
    cx+cy >= a1+1+b/sqrt2        (clears staircase (0,0))
    cx+cy <= 2S-a4-1-b/sqrt2     (clears staircase (S,S))
    cx-cy <= S-a2-c/sqrt2        (clears staircase (S,0))
    cx-cy >= a3-S+c/sqrt2        (clears staircase (0,S))

plus S >= max(a_i) and the staircase adjacency sums.  The minimum S is
found by bisection on this convex feasibility problem (Sutherland-Hodgman
clipping of the box by the strips), so placement is solved exactly rather
than assumed.  Every candidate with S < grid(n) is built and
packlib-verified (the honest gate).

n = T(a1)+T(a2)+T(a3)+T(a4) + b*c.  Asymmetric pairs now genuinely help
(the centred law could not see that), which is the point of this sweep.
"""
import json
import sys
from math import ceil, sqrt

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(
    __import__("os").path.abspath(__file__)))
sys.path.insert(0, ROOT + "/scripts")
import packlib as P

TAB = ROOT + "/workspace/submission/table.json"
OUT = ROOT + "/workspace/push/gobel5_results.json"
C45 = sqrt(2) / 2
PI4 = 0.7853981633974483
AMAX = 34


def T(a):
    return a * (a + 1) // 2


PM = {}
for _p in range(AMAX + 1):
    for _q in range(AMAX + 1):
        PM.setdefault(T(_p) + T(_q), []).append((_p, _q))
for _x in PM:
    PM[_x].sort(key=lambda pq: (pq[0] + pq[1], max(pq)))
KEYS = sorted(PM)


# ---------------------------------------------------------- geometry core

def clip(poly, keep):
    """Sutherland-Hodgman: keep the part of convex poly where keep(x,y)>=0."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        fa, fb = keep(*a), keep(*b)
        if fa >= -1e-12:
            out.append(a)
        if (fa > 0) != (fb > 0):
            t = fa / (fa - fb)
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    return out


def feasible_cx_cy(S, a1, a2, a3, a4, b, c):
    """A feasible block centre for box side S, or None."""
    ext = (b + c) / (2 * sqrt(2))
    if S < 2 * ext - 1e-12:
        return None
    poly = [(ext, ext), (S - ext, ext), (S - ext, S - ext), (ext, S - ext)]
    strips = [
        lambda x, y: x + y - (a1 + 1 + b * C45),
        lambda x, y: (2 * S - a4 - 1 - b * C45) - (x + y),
        lambda x, y: (S - a2 - c * C45) - (x - y),
        lambda x, y: (x - y) - (a3 - S + c * C45),
    ]
    for keep in strips:
        poly = clip(poly, keep)
        if len(poly) < 3:
            return None
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    return cx, cy


def min_box_S(a1, a2, a3, a4, b, c):
    """Smallest S with a feasible centre (bisection); (S, cx, cy) or None."""
    ext = (b + c) / (2 * sqrt(2))
    lo = max(2 * ext, float(max(a1, a2, a3, a4)), a1 + a2, a1 + a3,
             a4 + a2, a4 + a3)
    # cheap analytic lower bound (centred law with pair sums)
    lo = max(lo, (a1 + a4) / 2.0 + 1 + b * C45 - 1.0,
             (a2 + a3) / 2.0 + c * C45 - 1.0)
    hi = lo + 24.0
    if feasible_cx_cy(hi, a1, a2, a3, a4, b, c) is None:
        return None
    if feasible_cx_cy(lo, a1, a2, a3, a4, b, c) is not None:
        pt = feasible_cx_cy(lo, a1, a2, a3, a4, b, c)
        return lo, pt[0], pt[1]
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if feasible_cx_cy(mid, a1, a2, a3, a4, b, c) is None:
            lo = mid
        else:
            hi = mid
    pt = feasible_cx_cy(hi, a1, a2, a3, a4, b, c)
    return hi, pt[0], pt[1]


def build(a1, a2, a3, a4, b, c, S, cx, cy):
    st = []
    offu = (b - 1) / 2.0
    offv = (c - 1) / 2.0
    for i in range(b):
        u = i - offu
        for j in range(c):
            v = j - offv
            st.append((cx + C45 * (u - v), cy + C45 * (u + v), PI4))
    for (ox, oy, sx, sy, a) in ((0, 0, 1, 1, a1), (S, 0, -1, 1, a2),
                                (0, S, 1, -1, a3), (S, S, -1, -1, a4)):
        for i in range(a):
            for j in range(a - i):
                st.append((ox + sx * (i + 0.5), oy + sy * (j + 0.5), 0.0))
    return st


# --------------------------------------------------------------- sweep

def split_options(x, cap_sum):
    lst = PM.get(x)
    if not lst:
        return []
    out = [pq for pq in lst if pq[0] + pq[1] <= cap_sum]
    if len(out) > 3:
        out = [out[0], out[-1], out[len(out) // 2]]
    return out


def main():
    tab = json.load(open(TAB))
    L_arr = [0.0] + [tab[str(n)]["L"] for n in range(1, 1001)]
    tied = [n for n in range(1, 1001) if P.grid_L(n) - L_arr[n] <= 1e-12]
    print(f"tied n: {len(tied)}", flush=True)

    applied, tested, verify_fail, infeasible = [], 0, 0, 0
    for n in tied:
        K = P.grid_L(n)
        cur = L_arr[n]
        best = None
        stop = False
        for b in range(1, 60):
            for c in range(1, 60):
                bc = b * c
                need = n - bc
                if need < 0:
                    stop = True
                    break
                ext = (b + c) / (2 * sqrt(2))
                if 2 * ext >= K - 1e-9:
                    continue
                A2 = 2 * (K - 1 - b * C45) + 2
                B2 = 2 * (K - 1 - c * C45) + 2
                if A2 < 0 or B2 < 0:
                    continue
                if need > T(int(A2)) + T(int(B2)) + 8:
                    continue
                for x in KEYS:
                    if x > need:
                        break
                    y = need - x
                    if y not in PM:
                        continue
                    for (a1, a4) in split_options(x, A2):
                        for (a2, a3) in split_options(y, B2):
                            if max(a1, a2, a3, a4) >= K - 1e-9:
                                continue
                            r = min_box_S(a1, a2, a3, a4, b, c)
                            if r is None:
                                infeasible += 1
                                continue
                            S, cx, cy = r
                            if best is not None and S >= best[0] - 1e-9:
                                continue
                            if S >= K - 1e-9:
                                continue
                            st = build(a1, a2, a3, a4, b, c, S, cx, cy)
                            if len(st) != n:
                                continue
                            tested += 1
                            stf, rf = P.finalize(st, gap=2e-9)
                            if (not rf["ok"]) or rf["worst_pen"] > 0:
                                verify_fail += 1
                                continue
                            Lv = rf["L"]
                            if Lv < K - 1e-9 and (best is None or
                                                  Lv < best[0] - 1e-12):
                                best = (Lv, (a1, a2, a3, a4, b, c), stf)
                                print(f"  n={n} K={K}: candidate "
                                      f"L={Lv:.9f} params=({a1},{a2},{a3},"
                                      f"{a4};{b},{c})", flush=True)
            if stop:
                break
        if best is not None and best[0] < cur - 1e-9:
            Lv, par, stf = best
            a1, a2, a3, a4, b, c = par
            tab[str(n)] = {
                "L": round(Lv, 12), "state": stf,
                "src": (f"gobel5:a1={a1},a2={a2},a3={a3},a4={a4},"
                        f"b={b},c={c}")}
            L_arr[n] = round(Lv, 12)
            applied.append({"n": n, "old": cur, "new": round(Lv, 12),
                            "params": list(par)})
            print(f"  APPLIED n={n}: {cur:.9f} -> {Lv:.9f}", flush=True)

    print(f"verified: {tested} | verify-fails: {verify_fail} "
          f"| infeasible: {infeasible} | applied: {len(applied)}")
    if applied:
        json.dump(tab, open(TAB, "w"))
        tot = sum(tab[str(n)]["L"] / sqrt(n) - 1 for n in range(1, 1001))
        beats = sum(1 for n in range(1, 1001)
                    if tab[str(n)]["L"] < P.grid_L(n) - 1e-12)
        print(f"new score: {tot:.6f} | beats-grid: {beats}")
    json.dump({"applied": applied, "tested": tested,
               "verify_fails": verify_fail,
               "infeasible": infeasible}, open(OUT, "w"), indent=1)
    print("ledger ->", OUT)


if __name__ == "__main__":
    main()
