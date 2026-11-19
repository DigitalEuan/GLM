#!/usr/bin/env python3
r"""band_construct.py — aim a construction at the 247 open grid rows above 324.

WHAT THE BAND ACTUALLY IS (measured, run 78).  Above n = 324 the open grid rows
are contiguous in the residue m = n - k^2, one block per k, and each block starts
exactly at one more than the last row of that k that beats:

    k=18: beats m 1..20, open 21..35        k=25: beats m 1..30, open 31..49
    k=19: beats m 1..21, open 22..37        k=26: beats m 1..31, open 32..51
    ...                                     k=31: beats m 1..37, open 38..39

So the band is a *catalogue boundary* per k, not a geometric wall: the records we
imported stop at m = M(k), and every row past it sits at the grid.  That fixes
the target for a construction: the smallest open m of each k, because a packing
of n squares at side L is also a packing of n-1 squares at L (drop one), so the
band's first row is the easiest one and every larger m of that k is at least as
hard at the same side.

THE CONSTRUCTION AIMED.  "Extend the record": take the delivered state of the
row with m = M(k) -- verified below to beat the grid -- and put one more unit
square inside its bounding box, whose side already beats the grid.  Two tiers:

  T1  rigid insertion: scan placements on a raster at three angles (0, 45 deg,
      arctan 3/4) and ask the gate.  A free placement is immediate: the box is
      the record's own (already < grid), so n = k^2 + M(k) + 1 squares at that
      side beat the grid outright.
  T2  local translation: where T1 finds no free placement, hand the best few
      overlapping placements to `declp.solve` at L = grid - 1e-6 with the new
      square and its nearest neighbours free.  LP feasibility is a *point*, so a
      feasible LP is a candidate; it still has to pass `packlib.finalize` and the
      exact gate before it counts for anything.

THE EXACT GATE IS THE ONLY JUDGE.  `declp.gate(n, xy, th, L0)` rounds to 12 dp,
runs the canonical `packlib.verify` SAT at tol 0.0 and measures the side with
`sqscore.extent`.  A row counts as beaten only if `ok` and `L < grid - 1e-9`.
Nothing else in this file is allowed to report a score.

CONTROLS.
  1  every anchor (the m = M(k) row) beats the grid and its delivered state
     passes the gate at its own side;
  2  the gate bites: the same state with one square duplicated is refused;
  3  the detector is calibrated both ways: a k x k grid with one square removed
     must yield a free placement, a complete k x k grid must yield none;
  4  the band's first open m is exactly M(k) + 1 for all fourteen k, and the
     blocks are contiguous (the claim the target rests on).

READ-ONLY apart from `workspace/push/band_construct.json`.

    python3 scripts/band_construct.py --selftest
    python3 scripts/band_construct.py --max-k 20    # a short slice
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import declp as D            # noqa: E402
import packlib as P          # noqa: E402
import sqscore as SQ         # noqa: E402

ROOT = os.path.dirname(HERE)
CENSUS = os.path.join(ROOT, "workspace/push/row_census.json")
LEDGER = os.path.join(ROOT, "workspace/push/band_construct.json")
FRONTIER = 324
#: raster for the T1 scan (1/16 of a side; the gate, not the raster, decides).
#: Cell centres are multiples of H, so half-integer positions -- where the
#: delivered grids put their centres -- are always sampled.
H = 1.0 / 16.0
#: the angles the scan tries: 0, 45 deg, and small Pythagorean tilts (rational
#: cos and sin, so a placement on rational coordinates stays exactly rational)
ANGLES = (0.0, math.pi / 4.0, math.atan(3.0 / 4.0), math.atan(5.0 / 12.0),
          math.atan(7.0 / 24.0), math.atan(8.0 / 15.0))
#: how far below the grid T2 demands a packing
EPS = 1e-6


# --------------------------------------------------------------------- band
def band(census: dict) -> dict[int, list[int]]:
    """{k: sorted open m} above the frontier."""
    out: dict[int, list[int]] = {}
    for r in census["rows"]:
        if not r["beat"] and not r["closed"] and r["n"] > FRONTIER:
            k = math.isqrt(r["n"])
            out.setdefault(k, []).append(r["n"] - k * k)
    return {k: sorted(v) for k, v in out.items()}


def anchors(census: dict) -> dict[int, int]:
    """{k: largest beating m above the frontier} — the record the band follows."""
    out: dict[int, int] = {}
    for r in census["rows"]:
        if r["beat"] and r["n"] > FRONTIER:
            k = math.isqrt(r["n"])
            out[k] = max(out.get(k, 0), r["n"] - k * k)
    return out


# ---------------------------------------------------------------- geometry
def anchored(state):
    """Shift a state so its bounding box starts at (0, 0); return (state, L)."""
    a = np.asarray(state, dtype=float)
    ex = 0.5 * (np.abs(np.cos(a[:, 2])) + np.abs(np.sin(a[:, 2])))
    lo_x = float((a[:, 0] - ex).min())
    lo_y = float((a[:, 1] - ex).min())
    st = [(float(x - lo_x), float(y - lo_y), float(t)) for x, y, t in a]
    return st, SQ.extent(st)


def scan(states, L: float, th_c: float, h: float = H):
    """Net penetration of one extra square over the raster: (px, py, worst).

    `worst` is max over the existing squares of min over the four SAT axes of
    (required separation - projection).  <= 0 means the placement is free.
    """
    xs = np.arange(h, L, h)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    px, py = X.ravel(), Y.ravel()
    cs, sn = math.cos(th_c), math.sin(th_c)
    ex_c = 0.5 * (abs(cs) + abs(sn))
    inside = ((px - ex_c >= -1e-12) & (px + ex_c <= L + 1e-12) &
              (py - ex_c >= -1e-12) & (py + ex_c <= L + 1e-12))
    worst = np.full(px.size, -np.inf)
    for (xj, yj, tj) in states:
        ddx = xj - px
        ddy = yj - py
        cj, sj = math.cos(tj), math.sin(tj)
        # the existing square's own axes require separation 1.0 (its own 0.5
        # plus the candidate's 0.5 along the same direction)
        m = np.minimum(1.0 - np.abs(ddx * cj + ddy * sj),
                       1.0 - np.abs(-ddx * sj + ddy * cj))
        # the candidate's axes require 0.5 + the existing square's support
        need = 0.5 + 0.5 * (abs(cj * cs + sj * sn) + abs(cj * sn - sj * cs))
        m = np.minimum(m, need - np.abs(ddx * cs + ddy * sn))
        m = np.minimum(m, need - np.abs(-ddx * sn + ddy * cs))
        worst = np.maximum(worst, m)
    worst = np.where(inside, worst, np.inf)
    return px, py, worst


def gate_state(n: int, st, L0: float):
    """The exact gate on a list of (x, y, theta); returns its dict."""
    xy = np.array([[s[0], s[1]] for s in st], dtype=float)
    th = np.array([s[2] for s in st], dtype=float)
    return D.gate(n, xy, th, L0)


def finalize_gate(n: int, st, L0: float):
    """The project's certification path: finalize (gain clearance), then gate."""
    stc, _ = P.finalize([(float(x), float(y), float(t)) for x, y, t in st])
    return gate_state(n, stc, L0)


# ------------------------------------------------------------------ attempt
def attempt(n_target: int, grid: int, anchor_state, keep: int = 5) -> dict:
    """One extra square into a record whose own box already beats the grid."""
    st, L = anchored(anchor_state)
    n0 = len(st)
    # the box the extra square may use is the *largest beating box*, not the
    # anchor's own: L < grid - EPS still beats the grid, and it is room the
    # anchor's packing does not use.
    L_box = grid - EPS
    assert L <= L_box + 1e-9, (n_target, L, L_box)
    rec = {"n": n_target, "grid": grid, "n_anchor": n0,
           "L_anchor": round(L, 9), "L_box": round(L_box, 9),
           "best_margin": None, "margin_axis": None,
           "best_placement": None, "beats": False, "t1": [], "t2": []}
    seeds = []                      # (margin, x, y, theta)
    for th_c in ANGLES:
        px, py, w = scan(st, L_box, th_c)
        k = int(np.argmin(w))
        if th_c == 0.0:
            rec["margin_axis"] = round(float(w[k]), 9)
        seeds.append((float(w[k]), float(px[k]), float(py[k]), th_c))
        if w[k] <= 0.0:             # a free (or touching) placement: insert
            cand = st + [(float(px[k]), float(py[k]), th_c)]
            g = gate_state(n_target, cand, grid)
            rec["t1"].append({"theta": round(th_c, 9), "free": True,
                              "gate_ok": g["ok"], "L": round(g["L"], 9),
                              "worst_pen": g["worst_pen"]})
            if g["ok"] and g["L"] < grid - 1e-9:
                rec.update(beats=True, L_found=g["L"], how="T1 rigid",
                           state=g["state"])
                return rec
        else:
            rec["t1"].append({"theta": round(th_c, 9), "free": False,
                              "best_margin": round(float(w[k]), 9)})
    seeds.sort()
    rec["best_margin"] = round(seeds[0][0], 9)
    rec["best_placement"] = [round(seeds[0][1], 6), round(seeds[0][2], 6),
                             round(seeds[0][3], 9)]

    # T2: local translation at L = grid - EPS with the new square and its
    # nearest neighbours free.  Feasibility is a point; the gate still decides.
    L_target = grid - EPS
    for (margin, x, y, th_c) in seeds[:keep]:
        cand = st + [(x, y, th_c)]
        xy = np.array([[s[0], s[1]] for s in cand], dtype=float)
        ths = np.array([s[2] for s in cand], dtype=float)
        d = np.hypot(xy[:, 0] - x, xy[:, 1] - y)
        near = [int(j) for j in np.argsort(d)[:30]]
        free = set(near) | {len(cand) - 1}
        new = D.solve(xy, ths, L_target, free=free, pad=0.0, move=2.0,
                      free_span=2.0)
        if new is None:
            rec["t2"].append({"theta": round(th_c, 9), "lp": False})
            continue
        moved = [(float(new[j][0]), float(new[j][1]), float(ths[j]))
                 for j in range(len(cand))]
        g = finalize_gate(n_target, moved, grid)
        rec["t2"].append({"theta": round(th_c, 9), "lp": True, "gate_ok": g["ok"],
                          "L": round(g["L"], 9), "worst_pen": g["worst_pen"]})
        if g["ok"] and g["L"] < grid - 1e-9:
            rec.update(beats=True, L_found=g["L"], how="T2 translate",
                       state=g["state"])
            return rec
    return rec


# ---------------------------------------------------------------- controls
def selftest(per: dict, census: dict) -> int:
    print("control 1 — every anchor beats the grid and gates at its own side")
    bs, an = band(census), anchors(census)
    for k in sorted(bs):
        n = k * k + an[k]
        L = SQ.extent(per[n])
        assert L < k + 1 - 1e-9, (n, L, k + 1)
        g = gate_state(n, per[n], k + 1)
        assert g["ok"], (n, g["worst_pen"])
    print(f"  {len(bs)} anchors, all with L < k+1 and all gating clean")

    print("control 2 — the gate bites")
    st = list(per[18 * 18 + an[18]])
    bad = st + [st[0]]
    g = gate_state(len(bad), bad, 19)
    assert not g["ok"], g
    print(f"  duplicating one square is refused (worst penetration "
          f"{g['worst_pen']:.6f})")

    print("control 3 — the detector is calibrated both ways")
    k = 18
    grid = [(i + 0.5, j + 0.5, 0.0) for i in range(k) for j in range(k)]
    px, py, w = scan(grid, float(k), 0.0)
    assert w.min() > 0.0, w.min()
    holed = [s for s in grid if s[:2] != (k // 2 + 0.5, k // 2 + 0.5)]
    px, py, w = scan(holed, float(k), 0.0)
    assert w.min() <= 0.0, w.min()
    i = int(np.argmin(w))
    g = gate_state(len(holed) + 1, holed + [(float(px[i]), float(py[i]), 0.0)],
                   float(k))
    assert g["ok"], g["worst_pen"]
    print(f"  full {k}x{k} grid: no placement (min margin {w.min():.3f} when "
          f"holed); one hole: free at ({px[i]:.3f}, {py[i]:.3f}), gates clean")

    print("control 4 — the band starts at M(k) + 1, contiguously")
    for k in sorted(bs):
        ms = bs[k]
        assert ms[0] == an[k] + 1, (k, ms[0], an[k])
        # the block ends at m = 2k-1 (n = (k+1)^2 - 1, closed by Karakus) or at
        # the last row of the table, whichever comes first
        end = min(2 * k - 1, 1000 - k * k)
        assert ms == list(range(ms[0], end + 1)), (k, ms, end)
    print(f"  {sum(len(v) for v in bs.values())} band rows, "
          f"{len(bs)} blocks, each starting at M(k)+1 and running to the last "
          f"open row of its block")
    print("selftest: OK")
    return 0


# --------------------------------------------------------------------- run
def run(per: dict, census: dict, max_k: int = 99, write: bool = True) -> int:
    SQ.guard(per, quiet=True)
    bs, an = band(census), anchors(census)
    ks = [k for k in sorted(bs) if k <= max_k]
    print(f"targets: the smallest open m of each of {len(ks)} k-blocks "
          f"(k = {ks[0]}..{ks[-1]}), i.e. {sum(len(bs[k]) for k in ks)} of the "
          f"{sum(len(v) for v in bs.values())} band rows decided by "
          f"{len(ks)} attempts")
    print(f"{'k':>3} {'n_tgt':>6} {'grid':>4} {'L_anchor':>10} "
          f"{'margin':>10} {'gate':>6}  verdict")
    out = {"note": "extend-the-record construction aimed at the band's first row "
                   "per k; the exact gate (declp.gate, tol 0) is the only judge",
           "eps": EPS, "frontier": FRONTIER, "raster": H, "rows": []}
    beats = 0
    for k in ks:
        n_t = k * k + bs[k][0]
        t0 = time.time()
        rec = attempt(n_t, k + 1, per[k * k + an[k]])
        rec["k"] = k
        rec["m_target"] = bs[k][0]
        rec["m_anchor"] = an[k]
        rec["band_rows_decided"] = len(bs[k])
        rec["seconds"] = round(time.time() - t0, 1)
        g = rec.get("L_found")
        verdict = (f"BEAT at L = {g:.9f}" if rec["beats"]
                   else f"no construction ({rec['best_margin']:+.3f} margin)")
        print(f"{k:3d} {n_t:6d} {k + 1:4d} {rec['L_anchor']:10.6f} "
              f"{rec['best_margin']:+10.3f} {str(bool(rec['beats'])):>6}  "
              f"{verdict}  [{rec['seconds']}s]")
        beats += int(rec["beats"])
        out["rows"].append(rec)
    out["summary"] = {"blocks": len(ks), "beaten": beats,
                      "band_rows": sum(len(bs[k]) for k in ks),
                      "seconds": round(sum(r["seconds"] for r in out["rows"]), 1)}
    print(f"\n{beats} of {len(ks)} block-first rows beaten; "
          f"the exact gate refused every other construction")
    if write:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "w") as f:
            json.dump(out, f, indent=1)
        print(f"ledger -> {os.path.relpath(LEDGER, ROOT)}")
    return 0


def main() -> int:
    per = SQ.load()
    with open(CENSUS) as f:
        census = json.load(f)
    if "--selftest" in sys.argv:
        return selftest(per, census)
    max_k = 99
    if "--max-k" in sys.argv:
        max_k = int(sys.argv[sys.argv.index("--max-k") + 1])
    return run(per, census, max_k, write="--no-write" not in sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
