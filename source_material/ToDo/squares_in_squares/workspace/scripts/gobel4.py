#!/usr/bin/env python3
r"""gobel4.py — Run 13 push B: the ASYMMETRIC staircase family G4(a1,a2,a3,a4;
b,c), the strict generalization of Run 9's G(a1,a2,b,c).

Run 9 paired the staircases: depth a1 at corners (0,0),(s,s); a2 at (s,0),
(0,s).  The container law is s = max(bbox, per-corner contact), so splitting
depth *within* a pair is count-invariant at the top end — but with FOUR
independent depths the achievable COUNT at a fixed s becomes much finer
(T(a)=a(a+1)/2 per corner, sums of four of them), which is exactly what the
tied zone needs: n = K^2 - r at s < K.

Design geometry (same substrate as gobel2):
  - diamond b x c at 45 deg, centred (s/2, s/2);
  - axis-aligned staircase of depth a_i in corner i, i=1..4 =
    (0,0), (s,0), (0,s), (s,s);
  - contacts: corner 1 and 4 limited by the b-extent (x+y face),
    corners 2 and 3 by the c-extent; bbox sqrt(2)(b+c)/2;
  - adjacency: a_i + a_j <= s on every shared edge;
  - n = T(a1)+T(a2)+T(a3)+T(a4) + b*c.

Arithmetic stage (this script): for every grid-tied n, scan (b,c) and the
four depths for a representation with design s < grid(n); candidates are
generated, packlib-verified (the honest gate) and applied only if the
measured L beats the table.  Everything is recorded; nothing is claimed
without the verifier.
"""
import json
import sys
from math import ceil, sqrt

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(
    __import__("os").path.abspath(__file__)))
sys.path.insert(0, ROOT + "/scripts")
import packlib as P

TAB = ROOT + "/workspace/submission/table.json"
OUT = ROOT + "/workspace/push/gobel4_results.json"
C45 = sqrt(2) / 2
PI4 = 0.7853981633974483


def T(a):
    return a * (a + 1) // 2


def family_state(a1, a2, a3, a4, b, c, s):
    st = []
    offu = (b - 1) / 2.0
    offv = (c - 1) / 2.0
    for i in range(b):
        u = i - offu
        for j in range(c):
            v = j - offv
            st.append((s / 2 + C45 * (u - v), s / 2 + C45 * (u + v), PI4))
    for (cx, cy, sx, sy, a) in ((0, 0, 1, 1, a1), (s, 0, -1, 1, a2),
                                (0, s, 1, -1, a3), (s, s, -1, -1, a4)):
        for i in range(a):
            for j in range(a - i):
                st.append((cx + sx * (i + 0.5), cy + sy * (j + 0.5), 0.0))
    return st


def pair_map(A):
    """{T(x)+T(y) -> [(x,y), ...] : 0<=x,y<=A}."""
    m = {}
    for x in range(A + 1):
        for y in range(A + 1):
            m.setdefault(T(x) + T(y), []).append((x, y))
    return m


def design_s(a1, a2, a3, a4, b, c):
    s = sqrt(2) * (b + c) / 2
    if a1:
        s = max(s, a1 + 1 + b * C45)
    if a4:
        s = max(s, a4 + 1 + b * C45)
    if a2:
        s = max(s, a2 + 1 + c * C45)
    if a3:
        s = max(s, a3 + 1 + c * C45)
    return s


def main():
    tab = json.load(open(TAB))
    L_arr = [0.0] + [tab[str(n)]["L"] for n in range(1, 1001)]
    tied = [n for n in range(1, 1001)
            if P.grid_L(n) - L_arr[n] <= 1e-12]
    # near-miss first: gap of the SYMMETRIC family at each tied n
    sym = {}
    for a1 in range(0, 25):
        for a2 in range(0, 25):
            for b in range(1, 46):
                for c in range(1, 46):
                    n = a1 * (a1 + 1) + a2 * (a2 + 1) + b * c
                    if n > 1000:
                        break
                    s = design_s(a1, a1, a2, a2, b, c)
                    if n in sym and sym[n][0] <= s:
                        continue
                    sym[n] = (s, (a1, a2, b, c))
    rows = sorted(((sym[n][0] - P.grid_L(n), n) for n in tied if n in sym))
    # COMPLETE coverage: every tied n is a target (near-miss set first)
    targets = [n for g, n in rows] + [n for n in tied if n not in sym]
    print(f"tied n: {len(tied)} | symmetric near-misses (gap<=0.25): "
          f"{len([1 for g, n in rows if g <= 0.25])} | targets (ALL tied): "
          f"{len(targets)}")

    applied, tested, misses = [], 0, 0
    for n in targets:
        K = P.grid_L(n)
        cur = L_arr[n]
        found = None
        for b in range(1, 46):
            for c in range(1, 46):
                bc = b * c
                need = n - bc
                if need < 0:
                    break
                # contact limits at design s < K
                A = int(K - 1 - b * C45)     # corners 1,4 (b-face)
                B = int(K - 1 - c * C45)     # corners 2,3 (c-face)
                # a=0 (no staircase) is always legal: no contact claim.
                A = max(A, 0)
                B = max(B, 0)
                if sqrt(2) * (b + c) / 2 >= K:
                    continue
                P1 = pair_map(A)
                P2 = pair_map(B)
                ok = False
                a1 = a4 = a2 = a3 = None
                for x, lst1 in P1.items():
                    y = need - x
                    if y not in P2:
                        continue
                    for (p1, p4) in lst1:
                        for (p2, p3) in P2[y]:
                            s = design_s(p1, p2, p3, p4, b, c)
                            if s >= K - 1e-9:
                                continue
                            if (p1 + p2 > s + 1e-7 or p1 + p3 > s + 1e-7 or
                                    p4 + p2 > s + 1e-7 or p4 + p3 > s + 1e-7):
                                continue
                            a1, a2, a3, a4 = p1, p2, p3, p4
                            ok = True
                            break
                        if ok:
                            break
                    if ok:
                        break
                if not ok:
                    continue
                s = design_s(a1, a2, a3, a4, b, c)
                st = family_state(a1, a2, a3, a4, b, c, s)
                if len(st) != n:
                    continue
                tested += 1
                stf, rf = P.finalize(st, gap=2e-9)
                if (not rf["ok"]) or rf["worst_pen"] > 0:
                    misses += 1
                    continue
                Lv = rf["L"]
                if Lv < cur - 1e-9:
                    found = {"n": n, "a1": a1, "a2": a2, "a3": a3, "a4": a4,
                             "b": b, "c": c, "old": cur, "new": round(Lv, 12),
                             "state": stf}
                    cur = Lv
                    L_arr[n] = round(Lv, 12)
                    print(f"  APPLIED n={n} G4({a1},{a2},{a3},{a4};{b},{c}): "
                          f"{found['old']:.9f} -> {Lv:.9f}")
                    break
            if found:
                break
        if found:
            tab[str(n)] = {"L": found["new"], "state": found["state"],
                           "src": (f"gobel4:a1={found['a1']},a2={found['a2']},"
                                   f"a3={found['a3']},a4={found['a4']},"
                                   f"b={found['b']},c={found['c']}")}
            applied.append(found)

    print(f"targets {len(targets)} | generated {tested} | verify-fails {misses}"
          f" | applied {len(applied)}")
    if applied:
        json.dump(tab, open(TAB, "w"))
        tot = sum(tab[str(n)]["L"] / sqrt(n) - 1 for n in range(1, 1001))
        beats = sum(1 for n in range(1, 1001)
                    if tab[str(n)]["L"] < P.grid_L(n) - 1e-12)
        print(f"new score: {tot:.6f} | beats-grid: {beats}")
    json.dump({"applied": applied, "tested": tested, "verify_fails": misses,
               "targets": targets}, open(OUT, "w"), indent=1)
    print("ledger ->", OUT)


if __name__ == "__main__":
    main()
