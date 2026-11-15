#!/usr/bin/env python3
r"""gobel3_fill.py — Run 10 Wave B: the pocket-fill n-migration front.

For every table state (n, L): measure the container holes on the axis
grid (0°) and the half-grid (45°), fill deterministically (raster: axis
pass, then 45° pass, each accepted cell joins the state and blocks later
candidates). Every prefix of the fill is a valid state at the SAME L —
so each source state yields entries (n+k, L) for all useful k. Apply
where L beats the table. packlib.finalize gates every accepted fill;
the applied prefix is a subset of the verified set (subsets of clean
sets are clean).

Clearances: axis-axis |d| <= 1-1e-6; axis-45 L1dist >= r+1e-6 with
r = √2/2; 45-45 L1dist >= √2+1e-6. Final gate: packlib.finalize.
"""
import json
import sys
from math import sqrt, floor, ceil, cos, sin

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

sys.path.insert(0, ROOT + "/scripts")
import packlib as P

TAB = ROOT + "/workspace/submission/table.json"
OUT = ROOT + "/download/gobel3_fill.json"
SQ2 = sqrt(2)
R = SQ2 / 2          # 45-cell half-extent along x/y
PI4 = 0.7853981633974483


def _sq_axes(th):
    return ((1.0, 0.0), (0.0, 1.0),
            (cos(th), sin(th)), (-sin(th), cos(th)))


def _h(a, th):
    """Support extent of a unit square rotated by th along axis a."""
    return 0.5 * (abs(a[0] * cos(th) + a[1] * sin(th))
                  + abs(-a[0] * sin(th) + a[1] * cos(th)))


MARG = 1e-7  # separation slack: touching (d = h1+h2) is LEGAL contact;
             # reject only on true penetration beyond MARG.


def cells_overlap(cx, cy, cth, ex, ey, eth):
    """Exact SAT: do two unit squares (centers, angles) overlap?
    Separated (legal) if any edge-normal axis gives d > h1 + h2 - MARG;
    touching contacts therefore count as separated, penetrations don't."""
    dx, dy = cx - ex, cy - ey
    for a in _sq_axes(cth):
        d = abs(dx * a[0] + dy * a[1])
        if d > _h(a, cth) + _h(a, eth) - MARG:
            return False
    for a in _sq_axes(eth)[2:]:
        d = abs(dx * a[0] + dy * a[1])
        if d > _h(a, cth) + _h(a, eth) - MARG:
            return False
    return True


def try_fill(state, s):
    """Deterministic pocket fill of state in container [0, s]^2.
    Every candidate is tested with exact SAT against ALL existing and
    newly added cells (any angle). Returns list of new cells
    (axis raster, then 45 raster)."""
    cur = [tuple(c) for c in state]
    out = []
    # ---- axis pass: centers (i+0.5, j+0.5), i,j integers in [0, s-1]
    imax = int(floor(s - 1e-9)) - 1
    for i in range(0, imax + 1):
        for j in range(0, imax + 1):
            cx, cy = i + 0.5, j + 0.5
            ok = True
            for (ex, ey, eth) in cur:
                if cells_overlap(cx, cy, 0.0, ex, ey, eth):
                    ok = False
                    break
            if ok:
                cur.append((cx, cy, 0.0))
                out.append((cx, cy, 0.0))
    # ---- 45 pass: centers (i+0.5, j+0.5) with extent +-R in x/y
    ilo = int(ceil(R - 0.5 - 1e-9))          # i+0.5 >= R
    ihi = int(floor(s - R - 0.5 + 1e-9))     # i+0.5 <= s - R
    for i in range(ilo, ihi + 1):
        for j in range(ilo, ihi + 1):
            cx, cy = i + 0.5, j + 0.5
            ok = True
            for (ex, ey, eth) in cur:
                if cells_overlap(cx, cy, PI4, ex, ey, eth):
                    ok = False
                    break
            if ok:
                cur.append((cx, cy, PI4))
                out.append((cx, cy, PI4))
    return out


def main():
    tab = json.load(open(TAB))
    L_arr = [0.0] + [tab[str(n)]["L"] for n in range(1, 1001)]
    grid = [0.0]
    from math import isqrt
    for n in range(1, 1001):
        q = isqrt(n)
        grid.append(q + 1 if n > q * q else q)
    applied = []
    fills = {}
    fails = 0
    for n0 in range(1000, 0, -1):        # descending: fills migrate UP
        s = L_arr[n0]
        # useful? exists n' in (n0, 1000] with table L > s
        if not any(L_arr[np] > s + 1e-9
                   for np in range(n0 + 1, min(n0 + 400, 1000) + 1)):
            continue
        state = tab[str(n0)]["state"]
        src = tab[str(n0)].get("src", "?")
        F = try_fill(state, s)
        if not F:
            continue
        stf, rf = P.finalize(list(state) + F, gap=2e-9)
        if (not rf["ok"]) or rf["worst_pen"] > 0:
            fails += 1
            continue
        Lv = rf["L"]
        if Lv >= s + 1e-6:               # finalize inflated beyond design
            fails += 1
            continue
        fills[n0] = len(F)
        for k in range(0, len(F) + 1):
            np_ = n0 + k
            if np_ > 1000:
                break
            if Lv < L_arr[np_] - 1e-9:
                tab[str(np_)] = {
                    "L": round(Lv, 12),
                    "state": stf[:np_],
                    "src": "fill:%s+%d" % (src.split(":")[0], k)}
                L_arr[np_] = round(Lv, 12)
                applied.append({"from": n0, "to": np_, "k": k,
                                "L": Lv})
    print(f"fills measured: {len(fills)}, verify-fails: {fails}")
    print(f"entries applied: {len(applied)}")
    real = [a for a in applied if a["L"] < grid[a["to"]] - 1e-9
            and a["to"] != a["from"]]
    print(f"real improvements over table: {len(real)}")
    if applied:
        json.dump(tab, open(TAB, "w"))
        tot = sum(tab[str(n)]["L"] / sqrt(n) - 1 for n in range(1, 1001))
        beats = sum(1 for n in range(1, 1001)
                    if tab[str(n)]["L"] < grid[n] - 1e-9)
        print(f"score after wave B: {tot:.6f} | beats-grid: {beats}")
    json.dump({"fills": {str(k): v for k, v in fills.items()},
               "applied": applied[-400:], "fails": fails},
              open(OUT, "w"), indent=1)
    print(f"ledger -> {OUT}")


if __name__ == "__main__":
    main()
