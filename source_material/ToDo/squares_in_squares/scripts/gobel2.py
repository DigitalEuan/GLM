#!/usr/bin/env python3
r"""gobel2.py — Run 9: the GENERALIZED Göbel central-square family, swept
exactly and applied under packlib verification (the honest gate).

Family G(a1, a2, b, c)  [a1, a2 >= 0; b, c >= 1]:
  - diamond: b columns x c rows of unit squares at 45°, centered (s/2, s/2);
    columns b drive the x+y diagonal, rows c the x−y diagonal;
  - corner staircases (axis-aligned): depth a1 at corners (0,0),(s,s)
    (the x+y pair), depth a2 at (s,0),(0,s) (the x−y pair);
    T(a) = a(a+1)/2 squares per corner, so 2*T = a(a+1) per pair;
  - container: s = max over the binding constraints
        a1 >= 1:  a1 + 1 + b*√2/2     (x+y contact, both x+y corners)
        a2 >= 1:  a2 + 1 + c*√2/2     (x−y contact, both x−y corners)
        always:   √2*(b+c)/2          (diamond bbox inside [0,s]^2)
    (empty staircase -> no contact claim from that pair);
  - feasibility filter (proved necessary; packlib is the final judge):
        a1 + a2 <= s    (adjacent staircase pairs, row-0 edge squares);
  - n = a1(a1+1) + a2(a2+1) + b*c.

The shipped gobel_squares.py swept only the a1=a2, b=c subfamily (square
diamond, equal depths). This run sweeps the full 4-parameter family.

Every candidate that would beat the current table L is generated, run
through packlib.finalize (2e-9 contact gap, 12-dp rounding), and applied
only if verified (worst_pen <= 0). Rejections are recorded.
"""
import json
import sys
from math import sqrt

sys.path.insert(0, "/home/z/my-project/scripts")
import packlib as P

TAB = "/home/z/my-project/workspace/submission/table.json"
OUT = "/home/z/my-project/download/gobel2_results.json"
SQ2 = sqrt(2)
C45 = SQ2 / 2
PI4 = 0.7853981633974483


def family_state(a1, a2, b, c, s):
    """Build the G(a1,a2,b,c) state at container side s (design geometry)."""
    st = []
    offu = (b - 1) / 2.0
    offv = (c - 1) / 2.0
    # diamond: b columns (u), c rows (v), at 45°, centered (s/2, s/2)
    for i in range(b):
        u = i - offu
        for j in range(c):
            v = j - offv
            st.append((s / 2 + C45 * (u - v), s / 2 + C45 * (u + v), PI4))
    # staircases: (0,0),(s,s) depth a1; (s,0),(0,s) depth a2
    for (cx, cy, sx, sy, a) in ((0, 0, 1, 1, a1), (s, s, -1, -1, a1),
                                (s, 0, -1, 1, a2), (0, s, 1, -1, a2)):
        for i in range(a):
            for j in range(a - i):
                st.append((cx + sx * (i + 0.5), cy + sy * (j + 0.5), 0.0))
    return st


def main():
    tab = json.load(open(TAB))
    L_arr = [0.0] + [tab[str(n)]["L"] for n in range(1, 1001)]  # 1-indexed
    applied = []
    rejected = []
    fam_best = {}   # n -> (s_verified, params) best verified family member
    tested = 0
    for a1 in range(0, 25):
        n1 = a1 * (a1 + 1)
        for a2 in range(0, 25):
            n_pair = n1 + a2 * (a2 + 1)
            if n_pair > 1000:
                break
            for b in range(1, 46):
                sb = b * C45  # b * √2/2
                for c in range(1, 46):
                    n = n_pair + b * c
                    if n > 1000:
                        break
                    # container s
                    s = SQ2 * (b + c) / 2
                    if a1:
                        t = a1 + 1 + sb
                        if t > s:
                            s = t
                    if a2:
                        t = a2 + 1 + c * C45
                        if t > s:
                            s = t
                    # necessary feasibility (adjacent staircase pairs)
                    if a1 + a2 > s + 1e-7:
                        continue
                    cur = L_arr[n]
                    if s >= cur - 1e-9:
                        continue  # cannot beat the current table
                    # generate + verify (the honest gate)
                    st = family_state(a1, a2, b, c, s)
                    assert len(st) == n, (a1, a2, b, c, len(st), n)
                    tested += 1
                    stf, rf = P.finalize(st, gap=2e-9)
                    if (not rf["ok"]) or rf["worst_pen"] > 0:
                        if len(rejected) < 400:
                            rejected.append({"n": n, "a1": a1, "a2": a2,
                                             "b": b, "c": c, "s": s,
                                             "worst_pen": rf["worst_pen"]})
                        continue
                    Lv = rf["L"]
                    if n not in fam_best or Lv < fam_best[n][0] - 1e-12:
                        fam_best[n] = (Lv, (a1, a2, b, c))
                    if Lv < cur - 1e-9:
                        tab[str(n)] = {
                            "L": round(Lv, 12),
                            "state": stf,
                            "src": f"gobel2:a1={a1},a2={a2},b={b},c={c}"}
                        L_arr[n] = round(Lv, 12)
                        applied.append({"n": n, "a1": a1, "a2": a2, "b": b,
                                        "c": c, "old": cur, "new": Lv})
                        print(f"  APPLIED n={n} a1={a1} a2={a2} b={b} c={c}: "
                              f"{cur:.9f} -> {Lv:.9f}")
    # summary
    print(f"tested (passed pre-filters): {tested}")
    print(f"applied: {len(applied)}")
    print(f"rejected (verify fail): {len(rejected)} (cap 400 stored)")
    if applied:
        json.dump(tab, open(TAB, "w"))
        tot = sum(tab[str(n)]["L"] / sqrt(n) - 1 for n in range(1, 1001))
        beats = sum(1 for n in range(1, 1001)
                    if not tab[str(n)]["src"].startswith("grid"))
        print(f"new score: {tot:.6f} | beats-grid: {beats}")
    json.dump({"applied": applied,
               "rejected": rejected,
               "family_best_verified": {str(n): [v[0], list(v[1])]
                                        for n, v in sorted(fam_best.items())},
               "tested": tested},
              open(OUT, "w"), indent=1)
    print(f"ledger -> {OUT}")


if __name__ == "__main__":
    main()
