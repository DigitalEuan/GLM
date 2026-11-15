#!/usr/bin/env python3
r"""gobel5.py — Run 16 / NEXT_STEPS P1: the CORNER-BAND family.

Architecture (decoded from the imported 2026 records via
inspect_map.py / inspect_lattice.py): ONE tilted parallelogram band
(W x H at free angle th) anchored near the bottom-left corner running
to the top-right, plus axis-aligned wall-hugging fills in the four
corner wedges — the class the exhausted diamond+staircase family
cannot express (Run 13: 0/546).

Params: th in 30 rational atan2(p/q) angles; band W x H; translation
(xlo, ylo) on a 0.5 grid; fill-lattice phase off the walls (re-settling
axis, used by polish.py).  s = band bbox side.  Fills: greedy on the
two-wall union lattice (vectorized SAT vs the band).  n = W*H + fills.
Apply gate: design s below grid(n) AND finalize-L beats table[n] by
> 1e-9 (the table is mid-recovery in run 17, NOT at the frontier, so
"below grid" alone claims nothing).  packlib.finalize is the only gate
that applies anything.  Near-misses (s < grid + 0.06 on tied rows) are
recorded for P2 seeding.
"""
import json
import math
import sys
from math import atan2, sqrt

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(
    __import__("os").path.abspath(__file__)))
sys.path.insert(0, ROOT + "/scripts")
import packlib as P

import numpy as np

TAB = ROOT + "/workspace/submission/table.json"
OUT = ROOT + "/workspace/push/gobel5_results.json"
ANGLES = sorted({round(atan2(p, q), 6)
                 for q in range(2, 9) for p in range(1, q + 1)})


def build(th, H, W, xlo, ylo, phase=0.0):
    c, s_ = math.cos(th), math.sin(th)
    e = 0.5 * (abs(c) + abs(s_))
    cs = [(xlo + i * c - j * s_, ylo + i * s_ + j * c)
          for i, j in ((0, 0), (H - 1, 0), (0, W - 1), (H - 1, W - 1))]
    xlo_c = min(x for x, _ in cs) - e
    xhi_c = max(x for x, _ in cs) + e
    ylo_c = min(y for _, y in cs) - e
    yhi_c = max(y for _, y in cs) + e
    if xlo_c < -1e-9 or ylo_c < -1e-9 or xhi_c < 1.0 or yhi_c < 1.0:
        return None
    s = max(xhi_c, yhi_c)
    half = s - 0.5
    # band centres (B,2)
    band = np.array([[xlo + i * c - j * s_, ylo + i * s_ + j * c]
                     for i in range(H) for j in range(W)])
    # fill lattice: union of the two wall sub-lattices on each axis,
    # optionally phase-shifted away from the walls (re-settling axis)
    pos = sorted({round(0.5 + phase + k, 6) for k in range(int(s) + 2)}
                 | {round(half - phase - k, 6) for k in range(int(s) + 2)
                    if half - phase - k >= 0.5 - 1e-9})
    pos = np.array([p for p in pos if 0.5 - 1e-9 <= p <= half + 1e-9])
    if len(pos) < 2:
        return None
    X, Y = np.meshgrid(pos, pos)          # (P,P) centres, row=y, col=x
    dx = X[None, :, :] - band[:, 0][:, None, None]
    dy = Y[None, :, :] - band[:, 1][:, None, None]
    ext = 0.5 + 0.5 * (abs(c) + abs(s_))
    # overlap mask (P,P): True where a lattice cell overlaps SOME band sq
    ov = (np.abs(dx) < ext) & (np.abs(dy) < ext)
    for ux, uy in ((c, s_), (-s_, c)):
        pr = dx * ux + dy * uy
        ov &= (np.abs(pr) < ext)
    free = ~ov.any(axis=0)                # (P,P) True = no band overlap
    # greedy by wall-distance level: rows/cols hugging each wall
    lvl = np.minimum(pos - 0.5, half - pos)        # per-axis wall distance
    # per-axis adjacency: pos values within unit distance (overlap book-
    # keeping between the two wall sub-lattices; spacing exactly 1 is
    # legal touching, < 1 is overlap)
    Pn = len(pos)
    adj = [[j for j in range(Pn) if abs(pos[i] - pos[j]) < 1 - 1e-7]
           for i in range(Pn)]
    blocked = np.zeros((Pn, Pn), bool)
    fills = []
    order = list(np.argsort(lvl))
    for p in order:
        rowkills = adj[p]
        for q in order:
            if not free[p, q] or blocked[p, q]:
                continue
            fills.append((float(pos[q]), float(pos[p])))
            for pp in rowkills:
                bp = blocked[pp]
                for qq in adj[q]:
                    bp[qq] = True
    state = ([(float(bx), float(by), th) for (bx, by) in band]
             + [(x, y, 0.0) for (x, y) in fills])
    return s, state


def main():
    tab = json.load(open(TAB))
    L0 = {n: tab[str(n)]["L"] for n in range(1, 1001)}
    grid = {n: P.grid_L(n) for n in range(1, 1001)}
    tied = {n for n in range(1, 1001) if grid[n] - L0[n] <= 1e-12}

    tested = fails = 0
    records, nearmiss = [], []
    for th in ANGLES:
        c, s_ = math.cos(th), math.sin(th)
        for W in range(1, 5):
            for H in range(2, 27):
                e = 0.5 * (abs(c) + abs(s_))
                cs = [(i * c - j * s_, i * s_ + j * c)
                      for i, j in ((0, 0), (H - 1, 0), (0, W - 1), (H - 1, W - 1))]
                BW = max(x for x, _ in cs) - min(x for x, _ in cs) + 2 * e
                BH = max(y for _, y in cs) - min(y for _, y in cs) + 2 * e
                if max(BW, BH) > 31.5:
                    break
                for xv in range(0, 17):
                    xlo = 0.5 * xv
                    if xlo + BW > 31.5:
                        break
                    for yv in range(0, 17):
                        ylo = 0.5 * yv
                        if ylo + BH > 31.5:
                            break
                        r = build(th, H, W, xlo, ylo)
                        if r is None:
                            continue
                        s, state = r
                        n = len(state)
                        if n < 5 or n > 1000:
                            continue
                        K = grid[n]
                        interesting = s < K - 1e-9 or (n in tied and s < K + 0.06)
                        if not interesting:
                            continue
                        tested += 1
                        stf, rf = P.finalize(state, gap=2e-9)
                        if (not rf["ok"]) or rf["worst_pen"] > 0:
                            fails += 1
                            continue
                        Lv = rf["L"]
                        if s < K - 1e-9 and Lv < L0[n] - 1e-9:
                            records.append(
                                {"n": n, "th_deg": round(math.degrees(th), 3),
                                 "H": H, "W": W, "xlo": xlo, "ylo": ylo,
                                 "design_s": round(s, 9), "L": round(Lv, 12),
                                 "old": L0[n], "state": stf})
                            print(f"  RECORD n={n}: th={math.degrees(th):.2f} "
                                  f"{W}x{H}@({xlo},{ylo}) s={s:.6f} "
                                  f"L={Lv:.9f} (was {L0[n]:.9f})")
                        elif n in tied:
                            nearmiss.append(
                                {"n": n, "th_deg": round(math.degrees(th), 3),
                                 "H": H, "W": W, "xlo": xlo, "ylo": ylo,
                                 "gap": round(s - K, 6)})
    print(f"tested {tested} | verify-fails {fails} | records {len(records)} "
          f"| near-misses {len(nearmiss)}")
    for rec in records:
        tab[str(rec["n"])] = {
            "L": rec["L"], "state": rec["state"],
            "src": (f"gobel5:th={rec['th_deg']},{rec['W']}x{rec['H']},"
                    f"({rec['xlo']},{rec['ylo']})")}
    if records:
        json.dump(tab, open(TAB, "w"))
        tot = sum(tab[str(n)]["L"] / sqrt(n) - 1 for n in range(1, 1001))
        beats = sum(1 for n in range(1, 1001)
                    if tab[str(n)]["L"] < P.grid_L(n) - 1e-12)
        print(f"new score: {tot:.6f} | beats-grid: {beats}")
    json.dump({"records": records, "nearmiss": nearmiss,
               "tested": tested, "verify_fails": fails},
              open(OUT, "w"), indent=1)
    print("ledger ->", OUT)


if __name__ == "__main__":
    main()
