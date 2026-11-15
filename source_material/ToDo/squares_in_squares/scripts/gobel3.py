#!/usr/bin/env python3
r"""gobel3.py — Run 10 Wave A: the clipped-diamond (octagon-hull) family
G(a1, a2, b, c, t), swept with closed forms and packlib-gated.

Extension over Run 9's G(a1,a2,b,c): at each of the four (u,v) sign
corners of the b×c 45°-rectangle, remove the t×t block (t ≥ 1). This
relaxes the bbox by √2·t on all four sides (the elbow cells are gone)
at a cost of 4t² cells; the contact constraints are unchanged (the
u-extreme/v-extreme columns are untouched by shallow clips; the deep
slice 2t = min(b,c) degenerates to a smaller Run-9 diamond, covered by
the sweep anyway).

Closed forms (all measured, cross-checked by packlib):
  kept diamond cells: bc − 4t²   (t ≤ min(b,c)//2 keeps the four blocks
                                  pairwise disjoint; 2t ≤ min(b,c))
  u_min = −(b−1)/2 + t if (c even, t = c/2, c ≤ b) else −(b−1)/2
  u_max =  (b−1)/2 − t in that slice, else (b−1)/2
  v analogously with (b even, t = b/2, b ≤ c)
  contact1 = a1 + 1 + √2/2 + √2·max(−u_min, u_max)      [if a1 ≥ 1]
  contact2 = a2 + 1 + √2/2 + √2·max(−v_min, v_max)      [if a2 ≥ 1]
  bbox     = √2(b+c)/2 − √2·t                            [t ≥ 0]
  s = max(contact1, contact2, bbox);  pre-filters: a1+a2 ≤ s,
  n = a1(a1+1)+a2(a2+1)+bc−4t² ≤ 1000, s < table_L(n).

Wave B (pocket fill, same script): every verified state — the new finds
AND all 1000 existing table states — is measured for axis/45° cells that
fit in its container holes; every prefix of the deterministic fill is a
valid state at the same L, giving (n+k, L) entries when they beat the
table (n-migration front).
"""
import json
import sys
from math import sqrt

sys.path.insert(0, "/home/z/my-project/scripts")
import packlib as P

TAB = "/home/z/my-project/workspace/submission/table.json"
OUT = "/home/z/my-project/download/gobel3_results.json"
SQ2 = sqrt(2)
PI4 = 0.7853981633974483


def uv_extremes(b, c, t):
    """(u_min, u_max, v_min, v_max) of the clipped kept set (closed form)."""
    u_min = -(b - 1) / 2.0
    u_max = (b - 1) / 2.0
    v_min = -(c - 1) / 2.0
    v_max = (c - 1) / 2.0
    if c % 2 == 0 and 2 * t == c and c <= b:
        u_min += t
        u_max -= t
    if b % 2 == 0 and 2 * t == b and b <= c:
        v_min += t
        v_max -= t
    return u_min, u_max, v_min, v_max


def family_state(a1, a2, b, c, t, s):
    """Build G(a1,a2,b,c,t) at container side s (design geometry)."""
    st = []
    offu = (b - 1) / 2.0
    offv = (c - 1) / 2.0
    for i in range(b):
        u = i - offu
        for j in range(c):
            v = j - offv
            # four (u,v)-corner blocks removed
            if i >= b - t and j >= c - t:
                continue
            if i >= b - t and j < t:
                continue
            if i < t and j >= c - t:
                continue
            if i < t and j < t:
                continue
            st.append((s / 2 + (u - v) / SQ2, s / 2 + (u + v) / SQ2, PI4))
    for (cx, cy, sx, sy, a) in ((0, 0, 1, 1, a1), (s, s, -1, -1, a1),
                                (s, 0, -1, 1, a2), (0, s, 1, -1, a2)):
        for i in range(a):
            for j in range(a - i):
                st.append((cx + sx * (i + 0.5), cy + sy * (j + 0.5), 0.0))
    return st


def sweep():
    """Wave A: closed-form sweep of the clipped family. Returns finds."""
    tab = json.load(open(TAB))
    L_arr = [0.0] + [tab[str(n)]["L"] for n in range(1, 1001)]
    applied = []
    tested = 0
    census = {"prefilter_n": 0, "prefilter_s": 0, "prefilter_adj": 0}
    for a1 in range(0, 31):
        n1 = a1 * (a1 + 1)
        if n1 + 1 > 1000:
            break
        for a2 in range(0, 31):
            n_pair = n1 + a2 * (a2 + 1)
            if n_pair + 1 > 1000:
                break
            for b in range(1, 46):
                for c in range(1, 46):
                    bc = b * c
                    if n_pair + bc - 4 * ((min(b, c) // 2) ** 2) < 1:
                        continue  # even the fullest clip is empty
                    for t in range(0, min(b, c) // 2 + 1):
                        nd = bc - 4 * t * t
                        if nd < 1:
                            continue  # degenerate slice: staircases only
                        n = n_pair + nd
                        if n > 1000:
                            break
                        census["prefilter_n"] += 1
                        u_min, u_max, v_min, v_max = uv_extremes(b, c, t)
                        s = SQ2 * (b + c) / 2 - SQ2 * t
                        if a1:
                            cc = (a1 + 1 + SQ2 / 2
                                  + SQ2 * max(-u_min, u_max))
                            if cc > s:
                                s = cc
                        if a2:
                            cc = (a2 + 1 + SQ2 / 2
                                  + SQ2 * max(-v_min, v_max))
                            if cc > s:
                                s = cc
                        cur = L_arr[n]
                        if s >= cur - 1e-9:
                            census["prefilter_s"] += 1
                            continue
                        if a1 + a2 > s + 1e-7:
                            census["prefilter_adj"] += 1
                            continue
                        tested += 1
                        st = family_state(a1, a2, b, c, t, s)
                        assert len(st) == n, (a1, a2, b, c, t,
                                              len(st), n)
                        stf, rf = P.finalize(st, gap=2e-9)
                        if (not rf["ok"]) or rf["worst_pen"] > 0:
                            continue
                        Lv = rf["L"]
                        if Lv < cur - 1e-9:
                            tab[str(n)] = {
                                "L": round(Lv, 12),
                                "state": stf,
                                "src": ("gobel3:a1=%d,a2=%d,b=%d,c=%d,t=%d"
                                        % (a1, a2, b, c, t))}
                            L_arr[n] = round(Lv, 12)
                            applied.append({"n": n, "a1": a1, "a2": a2,
                                            "b": b, "c": c, "t": t,
                                            "old": cur, "new": Lv})
                            print("  APPLIED n=%d (%d,%d,%d,%d,%d): "
                                  "%.9f -> %.9f"
                                  % (n, a1, a2, b, c, t, cur, Lv))
    return tab, applied, tested, census


if __name__ == "__main__":
    tab, applied, tested, census = sweep()
    print(f"tested: {tested}")
    print(f"applied: {len(applied)}")
    print("census:", census)
    if applied:
        json.dump(tab, open(TAB, "w"))
        tot = sum(tab[str(n)]["L"] / sqrt(n) - 1 for n in range(1, 1001))
        print(f"score after wave A: {tot:.6f}")
    json.dump({"applied": applied, "tested": tested, "census": census},
              open(OUT, "w"), indent=1)
    print(f"ledger -> {OUT}")
