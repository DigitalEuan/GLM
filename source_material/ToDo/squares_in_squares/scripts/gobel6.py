#!/usr/bin/env python3
r"""gobel6.py — Run 17: the TWO-BAND (split-angle) family.

The 2026-record decode (run 16) showed the frontier states carry the
tilted band SPLIT into 2-3 sub-bands at slightly different angles.
gobel5 (one band) lands exactly AT grid on 23 tied roots — the
hypothesis under test here: a second band at another angle, SAT-clear
of the first, plus the same wall-hugging fills, dips BELOW grid there
and/or beats the mid-recovery table elsewhere.

Construction: band A = one seed per gap-0 root from gobel5's near-miss
ledger (dedup by n, smallest design_s); band B = swept (30 rational
angles + the 3-4-5 angle exactly, widths {1,2}, lengths 2..8, anchors
on the 0.5 grid 0..6.5), 4-axis SAT-clear of band A; fills = the same
greedy two-wall-union lattice, SAT-clear of A AND B.

Gates (nothing is claimed, everything measured): a build is finalize-
tested when its design s < grid(n) - 1e-9, or (tied row) s < grid+0.06;
it is APPLIED iff packlib.finalize verifies (0 penetration) and its L
beats table[n] by > 1e-9.  The table is mid-recovery (run 17), so the
near-miss class can also apply — that is intended (score recovery).
"""
import json
import math
import sys
from math import atan2, degrees, sqrt

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(
    __import__("os").path.abspath(__file__)))
sys.path.insert(0, ROOT + "/scripts")
import packlib as P
from gobel5 import ANGLES

import numpy as np

TAB = ROOT + "/workspace/submission/table.json"
IN = ROOT + "/workspace/push/gobel5_results.json"
OUT = ROOT + "/workspace/push/gobel6_results.json"
TH345 = round(atan2(3, 4), 9)          # 36.8699 deg exactly


def sup(th, ux, uy):
    """Support of a unit square rotated by th along unit axis (ux,uy)."""
    c, s_ = math.cos(th), math.sin(th)
    return 0.5 * (abs(ux * c + uy * s_) + abs(-ux * s_ + uy * c))


def sat2(x1, y1, t1, x2, y2, t2):
    """True iff two rotated unit squares (centres, angles) do NOT overlap
    (gap >= 0 on some edge-normal axis of either square)."""
    dx, dy = x2 - x1, y2 - y1
    for th in (t1, t2):
        c, s_ = math.cos(th), math.sin(th)
        for ux, uy in ((c, s_), (-s_, c)):
            if abs(dx * ux + dy * uy) >= sup(t1, ux, uy) + sup(t2, ux, uy):
                return True
    return False


def build2(bA, bB):
    """bA, bB: (th, H, W, xlo, ylo).  Returns (s, state) or None."""
    thA, HA, WA, xa, ya = bA
    thB, HB, WB, xb, yb = bB
    A = [(xa + i * math.cos(thA) - j * math.sin(thA),
          ya + i * math.sin(thA) + j * math.cos(thA))
         for i in range(HA) for j in range(WA)]
    B = [(xb + i * math.cos(thB) - j * math.sin(thB),
          yb + i * math.sin(thB) + j * math.cos(thB))
         for i in range(HB) for j in range(WB)]
    # band-vs-band: every B square must be SAT-clear of every A square
    for (bx, by) in B:
        for (ax, ay) in A:
            if not sat2(ax, ay, thA, bx, by, thB):
                return None
    band = np.array(A + B)
    # union container
    exts = [0.5 * (abs(math.cos(th)) + abs(math.sin(th))) for th in (thA, thB)]
    lox = min(A[0][0] - exts[0], B[0][0] - exts[1]) if A and B else 0.0
    # precise over all squares
    exA = exts[0]
    exB = exts[1]
    lox = min(min(x for x, _ in A) - exA, min(x for x, _ in B) - exB)
    hix = max(max(x for x, _ in A) + exA, max(x for x, _ in B) + exB)
    loy = min(min(y for _, y in A) - exA, min(y for _, y in B) - exB)
    hiy = max(max(y for _, y in A) + exA, max(y for _, y in B) + exB)
    if lox < -1e-9 or loy < -1e-9:
        return None
    s = max(hix, hiy)
    if s < 1.0:
        return None
    half = s - 0.5
    pos = sorted({round(0.5 + k, 6) for k in range(int(s) + 2)}
                 | {round(half - k, 6) for k in range(int(s) + 2)
                    if half - k >= 0.5 - 1e-9})
    pos = np.array([p for p in pos if 0.5 - 1e-9 <= p <= half + 1e-9])
    if len(pos) < 2:
        return None
    X, Y = np.meshgrid(pos, pos)
    # overlap mask for fills: an axis cell overlaps some band square iff
    # BOTH axis-distance tests fail AND both tilted-axis tests fail —
    # per-band square, so run the SAT per band angle over all squares.
    ov = np.zeros((len(pos), len(pos)), bool)
    for th in (thA, thB):
        c, s_ = math.cos(th), math.sin(th)
        # separation threshold for FILL (axis-aligned, 0.5) vs band square:
        # along x/y: 0.5 + 0.5(|c|+|s|); along the band edge-normals the
        # fill's extent is 0.5(|c|+|s|) and the band's own is 0.5 -> same.
        # (gobel5 uses this exact ext; the first gobel6 pass used only
        #  0.5(|c|+|s|) -> fills half-inside bands, pen ~0.5, 100% fails.)
        e = 0.5 + 0.5 * (abs(c) + abs(s_))
        bb = np.array([(x, y) for (x, y) in (A if th == thA else B)])
        dx = X[None, :, :] - bb[:, 0][:, None, None]
        dy = Y[None, :, :] - bb[:, 1][:, None, None]
        m = (np.abs(dx) < e) & (np.abs(dy) < e)
        for ux, uy in ((c, s_), (-s_, c)):
            m &= (np.abs(dx * ux + dy * uy) < e)
        ov |= m.any(axis=0)
    free = ~ov
    Pn = len(pos)
    adj = [[j for j in range(Pn) if abs(pos[i] - pos[j]) < 1 - 1e-7]
           for i in range(Pn)]
    blocked = np.zeros((Pn, Pn), bool)
    fills = []
    lvl = np.minimum(pos - 0.5, half - pos)
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
    state = ([(float(x), float(y), thA) for (x, y) in A]
             + [(float(x), float(y), thB) for (x, y) in B]
             + [(x, y, 0.0) for (x, y) in fills])
    return s, state


def main():
    tab = json.load(open(TAB))
    L0 = {n: tab[str(n)]["L"] for n in range(1, 1001)}
    grid = {n: P.grid_L(n) for n in range(1, 1001)}
    tied = {n for n in range(1, 1001) if grid[n] - L0[n] <= 1e-12}
    led = json.load(open(IN))
    # band-A configs: one per gap-0 root (gap < 1e-6), smallest gap
    # (nearmiss entries carry gap = design_s - grid(n); no design_s field)
    zero = [r for r in led["nearmiss"] if r["gap"] < 1e-6]
    byn = {}
    for r in zero:
        k = r["n"]
        if k not in byn or r["gap"] < byn[k]["gap"]:
            byn[k] = r
    seeds = sorted(byn.values(), key=lambda r: r["n"])
    print(f"band-A seeds: {len(seeds)} gap-0 roots: "
          + ", ".join(str(r["n"]) for r in seeds))

    tested = fails = 0
    records, nearmiss = [], []
    seen = set()
    for a in seeds:
        bA = (math.radians(a["th_deg"]), a["H"], a["W"],
              a["xlo"], a["ylo"])
        for th in ANGLES + [TH345]:
            for WB in (1, 2):
                for HB in range(2, 9):
                    for xb in [0.5 * v for v in range(0, 14)]:
                        for yb in [0.5 * v for v in range(0, 14)]:
                            r = build2(bA, (th, HB, WB, xb, yb))
                            if r is None:
                                continue
                            s, state = r
                            n = len(state)
                            if n < 5 or n > 1000:
                                continue
                            K = grid[n]
                            if not (s < K - 1e-9
                                    or (n in tied and s < K + 0.06)):
                                continue
                            key = (a["n"], round(th, 5), HB, WB,
                                   round(xb, 2), round(yb, 2))
                            if key in seen:
                                continue
                            seen.add(key)
                            tested += 1
                            stf, rf = P.finalize(state, gap=2e-9)
                            if (not rf["ok"]) or rf["worst_pen"] > 0:
                                fails += 1
                                continue
                            Lv = rf["L"]
                            if Lv < L0[n] - 1e-9:
                                records.append(
                                    {"n": n, "thA": a["th_deg"],
                                     "thB": round(math.degrees(th), 3),
                                     "A": f"{a['W']}x{a['H']}@({a['xlo']},{a['ylo']})",
                                     "B": f"{WB}x{HB}@({xb},{yb})",
                                     "design_s": round(s, 9),
                                     "L": round(Lv, 12), "old": L0[n],
                                     "state": stf})
                                print(f"  RECORD n={n}: A={a['W']}x{a['H']}"
                                      f"@({a['xlo']},{a['ylo']}) "
                                      f"B={WB}x{HB}@({xb},{yb}) "
                                      f"thB={math.degrees(th):.2f} s={s:.6f} "
                                      f"L={Lv:.9f} (was {L0[n]:.9f})")
                            elif n in tied:
                                nearmiss.append(
                                    {"n": n, "thB": round(math.degrees(th), 3),
                                     "B": f"{WB}x{HB}@({xb},{yb})",
                                     "gap": round(s - K, 6)})
    print(f"tested {tested} | verify-fails {fails} | records {len(records)} "
          f"| near-misses {len(nearmiss)}")
    for rec in records:
        tab[str(rec["n"])] = {
            "L": rec["L"], "state": rec["state"],
            "src": (f"gobel6:A{rec['A']},B{rec['B']},"
                    f"thB={rec['thB']}")}
    if records:
        json.dump(tab, open(TAB, "w"))
        tot = sum(tab[str(n)]["L"] / sqrt(n) - 1 for n in range(1, 1001))
        beats = sum(1 for n in range(1, 1001)
                    if tab[str(n)]["L"] < P.grid_L(n) - 1e-12)
        print(f"new score: {tot:.6f} | beats-grid: {beats}")
    json.dump({"records": records, "nearmiss": nearmiss,
               "tested": tested, "verify_fails": fails,
               "seeds": [r["n"] for r in seeds]},
              open(OUT, "w"), indent=1)
    print("ledger ->", OUT)


if __name__ == "__main__":
    main()
