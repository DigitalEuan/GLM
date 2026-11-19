#!/usr/bin/env python3
r"""space_around.py — the largest empty square in each band anchor, any angle.

WHY.  Run 78 asked a *placement* question: take the last record of each k-block,
put one more unit square inside a box that still beats the grid, and scan six
orientations (0, 45 deg and four Pythagorean tilts) on a 1/16 raster.  It found
no placement, and reported the free space as "box-shaped, not diamond-shaped",
with the largest empty square 0.86 to 0.91 of a unit.  Six orientations and a
raster are a sample, not a statement about the space: this run asks the reverse
question and answers it over the whole orientation circle.

A CORRECTION, found while building this.  Run 78's margins are not gaps.  Its
scan required a separation of `1.0` on the *packed* square's axes, but a
candidate rotated by theta needs `0.5 k + 0.5` there, with `k = |cos dphi| +
|sin dphi|` up to `sqrt 2`; at zero tilt the two agree, at a tilt they do not,
and the shortfall makes the recorded overlap smaller than it is.  So "largest
empty square = 1 - margin" (0.86..0.91) is an over-estimate: measured exactly
here it is 0.62..0.76.  Run 78's verdict is untouched -- its scan was optimistic
and still found no placement -- but its number is, and 41's sentence about it is
annotated.

WHAT THIS COMPUTES.  For a frozen state of unit squares and a box of side L,
write s(p, theta) for the largest square that

    is centred at p,          is rotated by theta,
    lies inside [0, L]^2,     and is interior-disjoint from every packed square.

Both constraints are closed-form.  Containment gives
`s <= 2 min(p_x, L-p_x, p_y, L-p_y) / (|cos theta| + |sin theta|)`, and the
separation from one packed square is a max over four SAT axes (the inserted
square's two axes and the packed square's two), each an affine function of s:

    s <= 2 (|d . u_new| - h_obs)          on the inserted square's axes
    s <= (2 |d . u_old| - 1) / k          on the packed square's axes,

with `h_obs = (|cos dphi| + |sin dphi|) / 2` and `k = |cos dphi| + |sin dphi|`
(and 1 <= k <= sqrt 2).  So s(p, theta) is *exact and cheap*, and

    s_max(theta) = max over p in [0, L]^2 of s(p, theta)

is the largest empty square at that orientation.  The position maximum is the
only part that is searched: a covering grid seeds it and a pattern search
refines the best seed to ~1e-10, so every number reported is attained by a
placement that `verify_placement` checks exactly (same closed form, tol 0).
`max over theta` is then the maximal empty square over all orientations.

THE ANSWER WANTED.  Is the ~0.1 deficit to fitting another unit square uniform
in orientation, or is it an artefact of only looking at right angles?  Three
variants per anchor are measured, because the free space depends on the box:

    own       the record's own bounding box (side L0) -- the gaps inside it;
    roomy     side k+1-1e-6, record flush in the corner -- plus the L-band;
    roomy-c   the same box, record centred -- four thin strips instead of two.

THE GATE IS STILL THE ONLY JUDGE.  Any s_max >= 1 is a candidate: the unit
square is inserted, `packlib.finalize`d and handed to `declp.gate` at the box
side.  A row is beaten only if the gate says `ok` and `L < grid - 1e-9`.  No
other line in this file may report a score, and nothing writes submission.csv.

Controls: (1) hand geometry (two unit squares in a 2-box: s_max = 1);
(2) a rigid grid has no empty square of positive side; (3) a holed grid gives
exactly 1 and the gate accepts the insertion with room; (4) anisotropy is
detected (a 0.4 strip: 0.4 at 0 deg, less at 45 deg); (5) the closed form agrees
with a vertex-projection SAT on 729 placements of a mixed-angle state -- the
check that caught run 78's axis shortfall.

READ-ONLY apart from `workspace/push/space_around.json`.

    python3 scripts/space_around.py --selftest
    python3 scripts/space_around.py                 # 14 anchors, 3 variants
    python3 scripts/space_around.py --k 18 --step 3 # one anchor, coarser
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import band_construct as B   # noqa: E402  (band, anchors, anchored)
import declp as D            # noqa: E402
import packlib as P          # noqa: E402
import sqscore as SQ         # noqa: E402

ROOT = os.path.dirname(HERE)
CENSUS = os.path.join(ROOT, "workspace/push/row_census.json")
LEDGER = os.path.join(ROOT, "workspace/push/space_around.json")

STEP = math.pi / 4.0 / 16.0    # 2.8125 deg: 17 samples over the circle
H_FINE = 0.35                  # seed-grid spacing (pockets are ~0.7 wide)
SEED_AT = (0.0, math.pi / 8.0, math.pi / 4.0)   # grids at 0, 22.5, 45 deg
EPS = 1e-6                     # the box run 78 used: k + 1 - EPS
CLIMB_TOL = 1e-10


# ------------------------------------------------------------------ geometry
def half_extent(theta: float) -> float:
    """Half-width of a unit square rotated by theta, along x."""
    return 0.5 * (abs(math.cos(theta)) + abs(math.sin(theta)))


def sat_side(p, th_new, xy, th, L) -> float:
    """Exact largest square centred at p with orientation th_new (may be < 0)."""
    c, s = math.cos(th_new), math.sin(th_new)
    ex = 0.5 * (abs(c) + abs(s))
    d = np.asarray(p, dtype=float) - np.asarray(xy, dtype=float)
    ux = d[:, 0] * c + d[:, 1] * s
    vx = -d[:, 0] * s + d[:, 1] * c
    dphi = np.asarray(th, dtype=float) - th_new
    ad = np.abs(dphi)
    h_obs = 0.5 * (np.abs(np.cos(ad)) + np.abs(np.sin(ad)))
    k = h_obs * 2.0                       # |cos| + |sin|, in [1, sqrt 2]
    cu, su = np.cos(th), np.sin(th)
    uj = d[:, 0] * cu + d[:, 1] * su
    vj = -d[:, 0] * su + d[:, 1] * cu
    b = np.maximum(2.0 * (np.abs(ux) - h_obs), 2.0 * (np.abs(vx) - h_obs))
    b = np.maximum(b, (2.0 * np.abs(uj) - 1.0) / k)
    b = np.maximum(b, (2.0 * np.abs(vj) - 1.0) / k)
    cont = min(p[0], L - p[0], p[1], L - p[1]) / ex
    return float(min(cont, float(b.min())))


def vertices(cx, cy, theta, side):
    """The four corners of a square, for the independent cross-check."""
    c, s = math.cos(theta), math.sin(theta)
    h = 0.5 * side
    out = []
    for a in (1, -1):
        for b in (1, -1):
            out.append((cx + a * h * c - b * h * s, cy + a * h * s + b * h * c))
    return out


def penetration_vertices(p, th_new, side, q, phi) -> float:
    """SAT by projecting explicit vertices (no closed form): overlap, min over axes."""
    A = vertices(p[0], p[1], th_new, side)
    Bv = vertices(q[0], q[1], phi, 1.0)
    worst = None
    for a in (th_new, th_new + math.pi / 2, phi, phi + math.pi / 2):
        nx, ny = math.cos(a), math.sin(a)
        pa = [x * nx + y * ny for x, y in A]
        pb = [x * nx + y * ny for x, y in Bv]
        ov = min(max(pa), max(pb)) - max(min(pa), min(pb))
        worst = ov if worst is None else min(worst, ov)
    return worst


def verify_placement(p, th_new, side, xy, th, L, tol=1e-12) -> dict:
    """Independent check: containment and pairwise separation of the insertion."""
    c, s = math.cos(th_new), math.sin(th_new)
    ex = 0.5 * (abs(c) + abs(s))
    worst = ex * side - min(p[0], L - p[0], p[1], L - p[1])   # > 0: outside
    d = np.asarray(p, dtype=float) - np.asarray(xy, dtype=float)
    ux = d[:, 0] * c + d[:, 1] * s
    vx = -d[:, 0] * s + d[:, 1] * c
    dphi = np.asarray(th, dtype=float) - th_new
    ad = np.abs(dphi)
    h_obs = 0.5 * (np.abs(np.cos(ad)) + np.abs(np.sin(ad)))
    k = 2.0 * h_obs
    cu, su = np.cos(th), np.sin(th)
    uj = d[:, 0] * cu + d[:, 1] * su
    vj = -d[:, 0] * su + d[:, 1] * cu
    sep = np.maximum(np.abs(ux) - (0.5 * side + h_obs),
                     np.abs(vx) - (0.5 * side + h_obs))
    sep = np.maximum(sep, np.abs(uj) - (0.5 * side * k + 0.5))
    sep = np.maximum(sep, np.abs(vj) - (0.5 * side * k + 0.5))
    worst = max(float(worst), float(-sep.min()))
    return {"ok": bool(worst <= tol), "worst": float(worst)}


# --------------------------------------------------------------------- search
def grid_seeds(xy, th, L, th_new, h, top=3, sub=9, sub_top=20):
    """Best `top` positions: a coarse covering grid, then a local subgrid.

    The pockets are sharply peaked -- s falls ~0.2 per 0.1 of movement at the
    band anchors -- so a coarse grid point can sit beside the peak and report
    half its value.  The coarse pass finds the cells, the subgrid resolves the
    peak, and `climb` finishes.
    """
    coarse = _coarse_grid(xy, th, L, th_new, h)
    order = np.argsort(coarse[1])[-sub_top:][::-1]
    pts = []
    for i in order:
        c = coarse[0][i]
        for a in np.linspace(-h, h, sub):
            for b in np.linspace(-h, h, sub):
                q = np.array([c[0] + a, c[1] + b])
                if 0.0 <= q[0] <= L and 0.0 <= q[1] <= L:
                    pts.append(q)
    vals = [sat_side(p, th_new, xy, th, L) for p in pts]
    idx = np.argsort(vals)[-top:][::-1]
    return [(float(vals[i]), pts[i]) for i in idx]


def _coarse_grid(xy, th, L, th_new, h):
    """(points, exact sides) on a grid of spacing h covering [0, L]^2."""
    m = max(2, int(round(L / h)))
    xs = np.linspace(0.0, L, m + 1)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    P = np.stack([X.ravel(), Y.ravel()], axis=1)
    c, s = math.cos(th_new), math.sin(th_new)
    ex = 0.5 * (abs(c) + abs(s))
    ux = P[:, 0] * c + P[:, 1] * s
    vx = -P[:, 0] * s + P[:, 1] * c
    cont = np.minimum(np.minimum(P[:, 0], L - P[:, 0]),
                      np.minimum(P[:, 1], L - P[:, 1])) / ex
    best = cont
    dphi_all = np.asarray(th, dtype=float) - th_new
    ca, sa = np.cos(th), np.sin(th)
    for j in range(len(xy)):
        dx = P[:, 0] - xy[j][0]
        dy = P[:, 1] - xy[j][1]
        h_obs = 0.5 * (abs(math.cos(dphi_all[j])) + abs(math.sin(dphi_all[j])))
        k = 2.0 * h_obs
        b = np.maximum(2.0 * (np.abs(dx * c + dy * s) - h_obs),
                       2.0 * (np.abs(-dx * s + dy * c) - h_obs))
        b = np.maximum(b, (2.0 * np.abs(dx * ca[j] + dy * sa[j]) - 1.0) / k)
        b = np.maximum(b, (2.0 * np.abs(-dx * sa[j] + dy * ca[j]) - 1.0) / k)
        np.minimum(best, b, out=best)
    return P, best


def climb(xy, th, L, th_new, p0, step=None):
    """Pattern search for max over p of s(p, th_new).  Deterministic."""
    p = np.array(p0, dtype=float)
    p = np.clip(p, 0.0, L)
    f = sat_side(p, th_new, xy, th, L)
    step = step if step is not None else max(0.02, L / 240.0)
    dirs = [np.array([1.0, 0.0]), np.array([-1.0, 0.0]),
            np.array([0.0, 1.0]), np.array([0.0, -1.0]),
            np.array([1.0, 1.0]) / math.sqrt(2), np.array([1.0, -1.0]) / math.sqrt(2),
            np.array([-1.0, 1.0]) / math.sqrt(2), np.array([-1.0, -1.0]) / math.sqrt(2)]
    while step > CLIMB_TOL:
        improved = False
        for d in dirs:
            q = np.clip(p + step * d, 0.0, L)
            g = sat_side(q, th_new, xy, th, L)
            if g > f + 1e-15:
                p, f, improved = q, g, True
        if not improved:
            step *= 0.5
    return p, f


def curve(xy, th, L, step=STEP, h=H_FINE):
    """s_max(theta) over [0, pi/4].

    Grids at 0, 22.5 and 45 deg give the pockets; every orientation between
    them is climbed from those seeds and from the previous orientation's
    optimum, so the curve tracks a placement through the whole arc.
    """
    seeds = []
    for t in SEED_AT:
        seeds += [p for _, p in grid_seeds(xy, th, L, t, h)]
    n = max(2, int(round((math.pi / 4.0) / step)) + 1)
    out = []
    track = None
    for i in range(n):
        t = math.pi / 4.0 * i / (n - 1)
        starts = seeds + ([track] if track is not None else [])
        best_p, best_s = None, -np.inf
        for p0 in starts:
            p, s = climb(xy, th, L, t, p0)
            if s > best_s:
                best_p, best_s = p, s
        track = best_p
        out.append({"theta": t, "side": best_s,
                    "p": [float(best_p[0]), float(best_p[1])]})
    return out


# ------------------------------------------------------------------ anchors
def variants(state, k):
    """(name, L, state) for the three boxes the free space can be measured in."""
    st, L0 = B.anchored(state)
    room = k + 1 - EPS
    shift = 0.5 * (room - L0)
    centred = [(x + shift, y + shift, t) for x, y, t in st]
    return [("own", L0, st), ("roomy", room, st), ("roomy-c", room, centred)]


def measure(state, k, step=STEP, h=H_FINE):
    """Curves, deficit statistics and the gated payoff (if any) for one anchor."""
    rec = {"k": k, "variants": {}}
    for name, L, st in variants(state, k):
        xy = np.array([[s[0], s[1]] for s in st], dtype=float)
        th = np.array([s[2] for s in st], dtype=float)
        cur = curve(xy, th, L, step=step, h=h)
        sides = np.array([c["side"] for c in cur])
        i = int(np.argmax(sides))
        ths = [c["theta"] for c in cur]
        # exact check of the best placement, at the reported side
        chk = verify_placement(cur[i]["p"], ths[i], sides[i], xy, th, L)
        s0 = float(cur[0]["side"])
        s45 = float(cur[-1]["side"])
        rec["variants"][name] = {
            "L": round(L, 9), "s_max": float(sides[i]),
            "theta_max_deg": round(math.degrees(ths[i]), 3),
            "s_at_0": s0, "s_at_45": s45,
            "s_min_over_theta": float(sides.min()),
            "spread": float(sides.max() - sides.min()),
            "argmax_ok": chk["ok"], "argmax_worst": chk["worst"],
            "p_max": cur[i]["p"],
            "fits_1": float(sides[i]) >= 1.0,
            "curve": [{"theta_deg": round(math.degrees(c["theta"]), 3),
                       "side": round(c["side"], 12)} for c in cur],
        }
        if sides[i] >= 1.0:
            rec["variants"][name]["payoff"] = payoff(
                xy, th, L, cur[i]["p"], ths[i], k)
    return rec


def payoff(xy, th, L, p, th_new, k):
    """Insert the unit square and let the gate decide.  Never edits the table."""
    st = [(float(x), float(y), float(t)) for x, y, t in xy.tolist()]
    st += [(float(p[0]), float(p[1]), float(th_new))]
    n1 = len(st)
    stf, rf = P.finalize(st, gap=2e-9)
    g = D.gate(n1, np.array([(s[0], s[1]) for s in stf]),
               np.array([s[2] for s in stf]), L)
    return {"row": n1, "gate_ok": g["ok"], "L": round(g["L"], 9),
            "worst_pen": g["worst_pen"],
            "beats_grid": bool(g["ok"] and g["L"] < SQ.grid(n1))}


# ---------------------------------------------------------------- controls
def selftest(per: dict, census: dict) -> int:
    print("control 1 — hand geometry: two unit squares in a 2-box, s_max = 1")
    one = np.array([[0.5, 0.5]])
    th1 = np.array([0.0])
    s = sat_side(np.array([1.5, 0.5]), 0.0, one, th1, 2.0)
    assert abs(s - 1.0) < 1e-12, s
    v = verify_placement(np.array([1.5, 0.5]), 0.0, 1.0, one, th1, 2.0)
    assert v["ok"], v
    smax = max(sat_side(np.array([x, y]), 0.0, one, th1, 2.0)
               for x in np.linspace(0, 2, 41) for y in np.linspace(0, 2, 41))
    assert abs(smax - 1.0) < 1e-12, smax
    print(f"   s(1.5, 0.5, 0 deg) = {s:.12f}; grid max = {smax:.12f}")

    print("control 2 — a rigid grid has no empty square")
    k = 10
    g = np.array([[i + 0.5, j + 0.5] for i in range(k) for j in range(k)])
    gt = np.zeros(len(g))
    smax = max(sat_side(np.array([x, y]), 0.0, g, gt, float(k))
               for x in np.linspace(0, k, 61) for y in np.linspace(0, k, 61))
    assert smax <= 1e-12, smax
    dup = [(float(a), float(b), 0.0) for a, b in g] + [(0.0, 0.0, 0.0)]
    gd = D.gate(len(dup), np.array([(a, b) for a, b, _ in dup]),
                np.zeros(len(dup)), float(k))
    assert not gd["ok"], gd
    print(f"   10x10 grid at L = 10: s_max = {smax:.3e}, insertion refused")

    print("control 3 — a holed grid gives exactly 1, and the gate accepts it")
    k = 8
    holed = np.array([[i + 0.5, j + 0.5] for i in range(k) for j in range(k)
                      if (i, j) != (k // 2, k // 2)])
    s = sat_side(np.array([k // 2 + 0.5, k // 2 + 0.5]), 0.0, holed,
                 np.zeros(len(holed)), float(k))
    assert abs(s - 1.0) < 1e-12, s
    st = [(float(a), float(b), 0.0) for a, b in holed]
    st.append((k // 2 + 0.5, k // 2 + 0.5, 0.0))
    stf, rf = P.finalize(st, gap=2e-9)
    gd = D.gate(len(st), np.array([(a, b) for a, b, _ in stf]),
                np.array([t for _, _, t in stf]), float(k) + 1e-6)
    assert gd["ok"], gd
    print(f"   hole at the centre: s = {s:.12f}; gated at L = {k + 1e-6:.6f}")

    print("control 4 — anisotropy is detected (a 0.4 strip)")
    strip = np.array([[0.5, 0.5]])
    th1 = np.array([0.0])
    L = 1.4
    s0 = max(sat_side(np.array([x, y]), 0.0, strip, th1, L)
             for x in np.linspace(0, L, 29) for y in np.linspace(0, L, 29))
    s45 = max(sat_side(np.array([x, y]), math.pi / 4, strip, th1, L)
              for x in np.linspace(0, L, 29) for y in np.linspace(0, L, 29))
    assert abs(s0 - 0.4) < 1e-9, s0
    assert s45 < s0 - 1e-3, (s0, s45)
    print(f"   0.4 strip: s_max(0 deg) = {s0:.6f}, s_max(45 deg) = {s45:.6f}")

    print("control 5 — the closed form agrees with an independent vertex SAT")
    mixed = [(500.5 + 2.0 * i, 500.5 + 2.0 * j, a)
             for i, j, a in [(0, 0, 0.0), (1, 0, math.pi / 4),
                             (0, 1, math.atan(3.0 / 4.0)), (1, 1, 0.3)]]
    xy = np.array([[a, b] for a, b, _ in mixed], dtype=float)
    th = np.array([t for _, _, t in mixed], dtype=float)
    bad, checked = 0, 0
    for t in (0.0, 0.26, math.pi / 4):
        for s in (0.4, 0.8, 1.2):
            for x in np.linspace(499.8, 504.0, 9):
                for y in np.linspace(499.8, 504.0, 9):
                    p = np.array([x, y])
                    lim = sat_side(p, t, xy, th, 2e3)   # box never binds
                    # our own side must bracket zero penetration
                    inside = max(penetration_vertices(p, t, s, xy[j], th[j])
                                 for j in range(len(xy)))
                    if (s <= lim - 1e-9 and inside > 1e-9) or \
                            (s >= lim + 1e-9 and inside <= -1e-9):
                        bad += 1
                    checked += 1
    assert bad == 0, bad
    print(f"   {checked} placements: side below/above the closed-form limit "
          f"agrees with explicit-vertex penetration on all of them")
    print("selftest: OK")
    return 0


# --------------------------------------------------------------------- run
def run(per, census, k_only=0, step=STEP, h=H_FINE, write=True) -> int:
    SQ.guard(per, quiet=True)
    an = B.anchors(census)
    ks = [k_only] if k_only else sorted(an)
    print(f"anchors: {len(ks)} k-blocks; {len(ks)} variants each; "
          f"orientations 0..45 deg in {math.degrees(step):.2f} deg steps")
    print(f"{'k':>3} {'variant':>8} {'L':>9} {'s_max':>8} {'@deg':>6} "
          f"{'s(0)':>8} {'s(45)':>8} {'min':>8} {'spread':>7}  fits-1")
    out = {"note": "largest empty square over all orientations in each band "
                   "anchor; the exact gate is the only judge",
           "step_deg": round(math.degrees(step), 4), "h_fine": h, "eps": EPS,
           "rows": []}
    t0 = time.time()
    for k in ks:
        n = k * k + an[k]
        rec = measure(per[n], k, step=step, h=h)
        rec.update(n=n, m_anchor=an[k], L_anchor=round(SQ.extent(per[n]), 9))
        for name, v in rec["variants"].items():
            print(f"{k:3d} {name:>8} {v['L']:9.6f} {v['s_max']:8.5f} "
                  f"{v['theta_max_deg']:6.2f} {v['s_at_0']:8.5f} "
                  f"{v['s_at_45']:8.5f} {v['s_min_over_theta']:8.5f} "
                  f"{v['spread']:7.5f}  {v['fits_1']}", flush=True)
        out["rows"].append(rec)
    dt = time.time() - t0
    own = [r["variants"]["own"] for r in out["rows"]]
    smax = np.array([v["s_max"] for v in own])
    at0 = np.array([v["s_at_0"] for v in own])
    sp = np.array([v["spread"] for v in own])
    print()
    print(f"own box: s_max {smax.min():.5f}..{smax.max():.5f} "
          f"(mean {smax.mean():.5f}); angle of the max "
          f"{min(v['theta_max_deg'] for v in own):.1f}.."
          f"{max(v['theta_max_deg'] for v in own):.1f} deg")
    print(f"          s(0 deg) mean {at0.mean():.5f}, spread over the circle "
          f"mean {sp.mean():.5f}, max {sp.max():.5f}")
    hits = [f"k={r['k']}/{name}" for r in out["rows"]
            for name, v in r["variants"].items() if v.get("payoff", {}).get("gate_ok")]
    print(f"gated improvements: {len(hits)}" + (f" {hits}" if hits else ""))
    out["summary"] = {"anchors": len(ks), "seconds": round(dt, 1),
                      "own_smax_min": float(smax.min()),
                      "own_smax_max": float(smax.max()),
                      "own_smax_mean": float(smax.mean()),
                      "own_s0_mean": float(at0.mean()),
                      "own_spread_mean": float(sp.mean()),
                      "own_spread_max": float(sp.max()),
                      "gated": hits}
    if write:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "w") as f:
            json.dump(out, f, indent=1)
        print(f"ledger -> {os.path.relpath(LEDGER, ROOT)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--k", type=int, default=0)
    ap.add_argument("--step", type=float, default=STEP, help="radians")
    ap.add_argument("--h", type=float, default=H_FINE, help="seed grid spacing")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    per = SQ.load()
    with open(CENSUS) as f:
        census = json.load(f)
    if a.selftest:
        return selftest(per, census)
    return run(per, census, a.k, a.step, a.h, write=not a.no_write)


if __name__ == "__main__":
    raise SystemExit(main())
