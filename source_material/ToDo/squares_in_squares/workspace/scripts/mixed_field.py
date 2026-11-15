#!/usr/bin/env python3
r"""mixed_field.py — mixed-level two-block structures: a 45°-rotated block
and a 30°-rotated block stacked in the container's diagonal band, with the
four corner staircases split between them (depths a and b).

Geometry (all measured exactly, verified by packlib):
  container s (tight): the binding face of the 45° block sits at
  distance a·√2/2 from the LL corner along the diagonal; the binding face
  of the 30° block at b·√3/2 (blocks stack along the diagonal: 45° block
  toward LL, 30° block toward UR, both centered on the diagonal).
  tightness: binding faces touch => exact closed form per family:
      s = √2·(a+1) + √3·(b+1) − p45·√2/2 − p30·√3/2   (face-to-face stack)
  with feasibility: the two rotated bboxes must stay inside the container
  and the blocks must not overlap each other (guaranteed by construction:
  separated along the diagonal by the staircase band; verified numerically).
Sweep a, b, p45, p30; keep verified packings; compare with the table.
A win here would be a genuine world record (mixed Q(√2,√3) level).
"""
import json
import math
import sys
from math import sqrt

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

HERE = ROOT + "/scripts"
sys.path.insert(0, HERE)
import packlib as P

TAB = ROOT + "/workspace/submission/table.json"
SQ2, SQ3 = sqrt(2), sqrt(3)


def build(a, b, p45, p30):
    """Two rotated blocks on the container diagonal + 4 corner staircases
    (depths a toward LL/UR-x stairs, b toward the other two).
    Returns (n, state) or None if infeasible."""
    # staircase square counts: 4 staircases — two of depth a, two of depth b
    # (T(k)=k(k+1)/2 each); blocks p² each.
    n = p45 * p45 + p30 * p30 + a * (a + 1) + b * (b + 1)
    # positions
    c45, s45 = SQ2 / 2, SQ2 / 2
    c30, s30 = SQ3 / 2, 0.5
    # binding faces along the diagonal: 45-block lower-left part, 30-block
    # upper-right part; tight container:
    #   s = (a+1)*√2/2 + (b+1)*√3/2 + (p45*√2/2 + p30*√3/2)
    #   (binding faces + blocks' half-extents along the diagonal)
    s = (a + 1) * SQ2 / 2 + (b + 1) * SQ3 / 2 + p45 * SQ2 / 2 + p30 * SQ3 / 2
    # block centers on the diagonal at parameter t (x=y=t)
    t45 = (a + 1) * SQ2 / 4 + p45 * SQ2 / 4
    t30 = s - ((b + 1) * SQ3 / 4 + p30 * SQ3 / 4)
    # feasibility: blocks must not overlap along the diagonal: the 45-block's
    # UR-most extent < 30-block's LL-most extent
    up45 = t45 + (p45 * SQ2 / 4)   # half-extent along diagonal for 45° block
    lo30 = t30 - (p30 * SQ3 / 4)
    if up45 > lo30 + 1e-12:
        return None, None
    st = []
    # 45 block: squares rotated 45°, centered (t45, t45)
    off = (p45 - 1) / 2
    for i in range(p45):
        for j in range(p45):
            u, v = i - off, j - off
            st.append((t45 + u * c45 - v * s45, t45 + u * s45 + v * c45, math.pi / 4))
    # 30 block: squares rotated 30°, centered (t30, t30)
    off = (p30 - 1) / 2
    for i in range(p30):
        for j in range(p30):
            u, v = i - off, j - off
            st.append((t30 + u * c30 - v * s30, t30 + u * s30 + v * c30, math.pi / 6))
    # staircases: LL and UR corners depth a; LR and UL depth b
    for (ox, oy) in ((0, 0), (1, 1)):
        for i in range(a):
            for j in range(a - i):
                X = (i + 0.5) if ox == 0 else s - (i + 0.5)
                Y = (j + 0.5) if oy == 0 else s - (j + 0.5)
                st.append((X, Y, 0.0))
    for (ox, oy) in ((1, 0), (0, 1)):
        for i in range(b):
            for j in range(b - i):
                X = (i + 0.5) if ox == 0 else s - (i + 0.5)
                Y = (j + 0.5) if oy == 0 else s - (j + 0.5)
                st.append((X, Y, 0.0))
    # containment check: all inside [0, s]
    for (X, Y, T) in st:
        ex = 0.5 * (abs(math.cos(T)) + abs(math.sin(T)))
        if X - ex < -1e-9 or X + ex > s + 1e-9 or Y - ex < -1e-9 or Y + ex > s + 1e-9:
            return None, None
    return n, (st, s)


def main():
    tab = json.load(open(TAB))
    wins = []
    best_list = []
    for a in range(0, 7):
        for b in range(0, 7):
            for p45 in range(1, 8):
                for p30 in range(1, 8):
                    n, st = build(a, b, p45, p30)
                    if st is None:
                        continue
                    state, s = st
                    if len(state) != n:
                        continue
                    r = P.verify(state)
                    if r["worst_pen"] > 1e-9:
                        continue
                    stf, r2 = P.finalize(state, gap=2e-9)
                    if not r2["ok"]:
                        continue
                    Lv = float(r2["L"])
                    grid = math.ceil(math.sqrt(n))
                    cur = tab.get(str(n), {}).get("L")
                    rec = {"a": a, "b": b, "p45": p45, "p30": p30, "n": n,
                           "s": round(Lv, 9), "grid": grid, "cur": cur}
                    best_list.append(rec)
                    if cur is not None and Lv < cur - 1e-9:
                        wins.append(rec)
                    elif cur is None:
                        # new n beyond 1000? cap
                        if n <= 1000:
                            pass
    print(f"verified mixed-level packings: {len(best_list)}")
    # best per n
    byn = {}
    for r in best_list:
        if r["n"] not in byn or r["s"] < byn[r["n"]]["s"]:
            byn[r["n"]] = r
    useful = [r for r in byn.values() if r["cur"] is not None and r["s"] < r["cur"] - 1e-9]
    beats_grid = [r for r in byn.values() if r["s"] < r["grid"] - 1e-9]
    print(f"distinct n: {len(byn)} | beats record: {len(useful)} | beats grid only: {len(beats_grid)}")
    for r in sorted(beats_grid, key=lambda z: z["n"])[:10]:
        tag = " RECORD!" if r["cur"] is not None and r["s"] < r["cur"] - 1e-9 else ""
        print(f"  n={r['n']} (a={r['a']},b={r['b']},p45={r['p45']},p30={r['p30']}): s={r['s']:.6f} grid={r['grid']} cur={r['cur']}{tag}")
    print(f"WINS (record beats): {len(wins)}")
    for w in wins[:10]:
        print(f"  n={w['n']}: {w['cur']} -> {w['s']}")
    json.dump({"verified": len(best_list), "by_n": {str(k): v for k, v in byn.items()},
                "wins": wins}, open("/tmp/mixed_field.json", "w"))


if __name__ == "__main__":
    main()
