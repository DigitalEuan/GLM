#!/usr/bin/env python3
"""gobel_squares.py — generate Göbel-square family packings and apply to table.

Family (Göbel 1979; template verified against survey square-233.svg = a=7,b=11
and square-65.svg = a=4,b=5):
  n = 2a(a+1) + b²,  s = a + 1 + b√2/2,  constraint a−1 < b√2/2 < a+1.
Construction:
  - diamond: b×b grid of unit squares at 45°, centered at (s/2, s/2);
  - four corner staircases: axis-aligned unit squares at (corner + i+0.5,
    corner + j+0.5) for i, j ≥ 0, i + j ≤ a−1  (T(a) = a(a+1)/2 each).
Contact identity: diamond edge lines are x+y = s − b√2/2 = a+1; the
staircases' extreme corners reach exactly x+y = a+1 (i+j = a−1 squares have
corner at (i+0.5)+(j+0.5)+1 = a+1). Zero overlap by construction; packlib
verifies every generated state before it is applied.

Sweep all (a, b) with n ≤ 1000; apply where s beats the current table's L.
"""
import json
import sys
from math import sqrt

sys.path.insert(0, "/home/z/my-project/scripts")
import packlib as P

TAB = "/home/z/my-project/workspace/submission/table.json"
SQ2 = sqrt(2)

def gobel_state(a, b):
    s = a + 1 + b * SQ2 / 2
    st = []
    # diamond: b×b grid at 45° centered (s/2, s/2); rotated-frame offsets
    # (u, v) with u, v ∈ [-(b-1)/2, (b-1)/2]; center = (s/2,s/2) + R(45°)(u,v)
    off = (b - 1) / 2.0
    c45 = SQ2 / 2
    for i in range(b):
        for j in range(b):
            u = i - off
            v = j - off
            x = s / 2 + u * c45 - v * c45
            y = s / 2 + u * c45 + v * c45
            st.append((x, y, c45 * 2 * 0.0 + 0.7853981633974483))  # pi/4
    # four staircases
    for (cx, cy, sx, sy) in ((0, 0, 1, 1), (s, 0, -1, 1), (0, s, 1, -1), (s, s, -1, -1)):
        for i in range(a):
            for j in range(a - i):
                x = cx + sx * (i + 0.5)
                y = cy + sy * (j + 0.5)
                st.append((x, y, 0.0))
    return s, st

def main():
    tab = json.load(open(TAB))
    applied = []
    rejected = []
    for a in range(1, 40):
        for b in range(1, 60):
            n = 2 * a * (a + 1) + b * b
            if n > 1000:
                continue
            # constraint
            if not (a - 1 < b * SQ2 / 2 < a + 1):
                continue
            s = a + 1 + b * SQ2 / 2
            cur = tab[str(n)]["L"]
            if s >= cur - 1e-9:
                continue
            # generate + verify
            s_gen, st = gobel_state(a, b)
            assert len(st) == n, (a, b, len(st), n)
            stf, rf = P.finalize(st, gap=2e-9)
            if not rf["ok"] or rf["worst_pen"] > 0:
                rejected.append((a, b, n, s, rf["worst_pen"]))
                continue
            tab[str(n)] = {"L": round(rf["L"], 12), "state": stf,
                           "src": f"gobelS:a{a}b{b}"}
            applied.append((n, a, b, cur, rf["L"]))
    print(f"applied: {len(applied)}")
    for n, a, b, cur, L in applied:
        print(f"  n={n} (a={a},b={b}): {cur:.6f} -> {L:.9f}")
    print(f"rejected (verify fail): {len(rejected)}")
    for r in rejected:
        print("  REJECT", r)
    if applied:
        json.dump(tab, open(TAB, "w"))
        tot = sum(tab[str(n)]["L"] / sqrt(n) - 1 for n in range(1, 1001))
        gt = sum(-(-sqrt(n) // 1) // 1 for n in [])  # placeholder
        print(f"new score: {tot:.6f}")

if __name__ == "__main__":
    main()
