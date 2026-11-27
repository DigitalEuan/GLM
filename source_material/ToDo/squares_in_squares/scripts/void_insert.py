#!/usr/bin/env python3
r"""void_insert.py — run 114: does the frontier pose of each band contain room
for one more cell?

The question the 447 grid rows actually pose.  Band k runs n = (k-1)^2+1 .. k^2.
The delivered table beats an initial segment of the band and stops at the
frontier row m*; the next row m*+1 is unbeaten.  Beating it means packing one
more unit square into the *frontier pose itself* (side L(m*) < k) - not into a
grid.  So measure, exactly, the largest square that fits in that pose's free
space:

    s_max(m*) = max over (centre, angle) of the largest non-overlapping
                square that stays inside the container.

s_max >= 1  ->  a beat exists and is constructed here (verified by true_geom).
s_max <  1  ->  the shortfall 1 - s_max is the cell that has to come out of the
                void first; that number is the row's true price.

Method: separating-axis in closed form.  For a candidate square of side s
(half-size h = s/2) at centre c with angle t, and an existing unit cell at p
with angle u, the pair is non-overlapping iff some candidate axis q (the two
edge normals of each square) satisfies

    |(c-p).q| >= h*g(t,q) + h_u(q),      g(t,q) = |cos t qx + sin t qy| + |-sin t qx + cos t qy|
    h_u(q) = (|cos u qx + sin u qy| + |-sin u qx + cos u qy|)/2

so for fixed (c, t) the largest feasible h is

    h_max = min_cells max_axes ((|(c-p).q| - h_u(q)) / g(t,q)),

capped by the container: h*|cos t| + h*|sin t| <= distance from c to each wall.
A scan over a centre grid and the angle range [0, pi/4] (a square is 90-periodic
and mirror-symmetric) finds the global max, then the cell is refined locally.

Float use: discovery/census, like relax_angles.py.  The final verdict is taken
by true_geom (40 digits), not by this scan.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sqscore as SQ          # noqa: E402
import true_geom as TG        # noqa: E402

TAB = os.path.join(ROOT, "workspace/submission/table.json")
OUT = os.path.join(ROOT, "workspace/push/void_insert114.json")


def load_pose(n):
    tab = json.load(open(TAB))
    st = tab[str(n)]["state"]
    x = np.array([float(r[0]) for r in st])
    y = np.array([float(r[1]) for r in st])
    t = np.array([float(r[2]) for r in st])
    return x, y, t


def half_ext(x, y, t):
    h = 0.5 * (np.abs(np.cos(t)) + np.abs(np.sin(t)))
    return x - h, x + h, y - h, y + h


def hfield(x, y, t, CX, CY, th, box):
    """Largest square half-size h allowed at every (CX, CY) for angle th.

    Separating-axis, exactly: two convex squares are disjoint iff some axis
    among their four edge normals separates them, so for each existing cell the
    feasible h is the MAXimum over those four axes, and the pose-wide value is
    the MINimum over cells.  Container: the rotated square's bbox half-extent is
    h*(|cos th| + |sin th|), so h is also capped by the distance to each wall.
    """
    xmin, xmax, ymin, ymax, _L = box
    ct, st_ = math.cos(th), math.sin(th)
    gu = abs(ct) + abs(st_)
    cap = np.minimum(np.minimum(CX - xmin, xmax - CX),
                     np.minimum(CY - ymin, ymax - CY)) / max(gu, 1e-12)
    hbest = np.full(CX.shape, np.inf)
    for j in range(len(x)):
        cj, sj = math.cos(t[j]), math.sin(t[j])
        bound = np.full(CX.shape, -np.inf)
        for (qx, qy) in ((ct, st_), (-st_, ct), (cj, sj), (-sj, cj)):
            gA = abs(ct * qx + st_ * qy) + abs(-st_ * qx + ct * qy)
            hB = 0.5 * (abs(cj * qx + sj * qy) + abs(-sj * qx + cj * qy))
            proj = np.abs((CX - x[j]) * qx + (CY - y[j]) * qy)
            bound = np.maximum(bound, (proj - hB) / max(gA, 1e-12))
        hbest = np.minimum(hbest, bound)
    return np.minimum(hbest, cap)


def hmax_scan(x, y, t, grid=84, angles=13):
    """Largest square (half-size h) fitting in the pose's free space."""
    x0, x1, y0, y1 = half_ext(x, y, t)
    xmin, xmax = float(x0.min()), float(x1.max())
    ymin, ymax = float(y0.min()), float(y1.max())
    L = max(xmax - xmin, ymax - ymin)
    xmax, ymax = xmin + L, ymin + L
    box = (xmin, xmax, ymin, ymax, L)
    CX, CY = np.meshgrid(np.linspace(xmin, xmax, grid),
                         np.linspace(ymin, ymax, grid))
    CX, CY = CX.ravel(), CY.ravel()
    best = (-1.0, 0.0, 0.0, 0.0)
    for ai in range(angles):
        th = (math.pi / 4) * ai / max(1, angles - 1)
        h = hfield(x, y, t, CX, CY, th, box)
        i = int(np.argmax(h))
        if h[i] > best[0]:
            best = (float(h[i]), float(CX[i]), float(CY[i]), th)
    return best, box


def refine(x, y, t, state, box, rounds=5, grid=61):
    h, cx, cy, th = state
    xmin, xmax, ymin, ymax, L = box
    span = L / 6.0
    best = (h, cx, cy, th)
    for _ in range(rounds):
        los = np.linspace(max(xmin, cx - span), min(xmax, cx + span), grid)
        losy = np.linspace(max(ymin, cy - span), min(ymax, cy + span), grid)
        tspan = span / max(L, 1e-9)
        tlo, thi = max(0.0, th - tspan), min(math.pi / 4, th + tspan)
        CX, CY = np.meshgrid(los, losy)
        CX, CY = CX.ravel(), CY.ravel()
        for th2 in np.linspace(tlo, thi, 11):
            h2 = hfield(x, y, t, CX, CY, float(th2), box)
            i = int(np.argmax(h2))
            if h2[i] > best[0]:
                best = (float(h2[i]), float(CX[i]), float(CY[i]), float(th2))
        h, cx, cy, th = best
        span /= 4.0
    return best


def frontier_rows(per):
    rows = []
    for k in range(2, 33):
        lo, hi = (k - 1) ** 2 + 1, min(k * k, 1000)
        beaten = [n for n in range(lo, hi + 1) if SQ.extent(per[n]) < k - 1e-12]
        if beaten:
            rows.append((k, max(beaten)))
    return rows


def pen_vec(ax, ay, at, bx, by, bt, eps=0.0):
    """Exact pairwise penetration of unit squares (0 when disjoint), vectorised.

    Separating-axis over the four edge normals; a pair is disjoint iff one of
    them separates, so the penetration is minus the best (largest) separation.
    `eps` asks for that much *clearance* rather than mere non-overlap, so the
    result survives the 40-digit check instead of landing on a 1e-16 touch.
    """
    best = np.full(np.shape(ax), -1e9)
    for (qx, qy) in ((np.cos(at), np.sin(at)), (-np.sin(at), np.cos(at)),
                     (np.cos(bt), np.sin(bt)), (-np.sin(bt), np.cos(bt))):
        hA = 0.5 * (np.abs(np.cos(at) * qx + np.sin(at) * qy)
                    + np.abs(-np.sin(at) * qx + np.cos(at) * qy))
        hB = 0.5 * (np.abs(np.cos(bt) * qx + np.sin(bt) * qy)
                    + np.abs(-np.sin(bt) * qx + np.cos(bt) * qy))
        proj = np.abs((ax - bx) * qx + (ay - by) * qy)
        best = np.maximum(best, proj - (hA + hB))
    return np.clip(eps - best, 0.0, None)


def seat(m, grid=120, angles=25, max_offend=8, margin=1e-4):
    """Try to seat one more cell in the frontier pose of row m.

    The frontier pose of row m has side L(m) < k = grid(m+1), so ANY legal
    unit cell placed inside its bounding box beats row m+1.  The free-space
    scan finds where a cell almost fits; this then frees only the new cell and
    the few cells it penetrates (<= 3*max_offend+3 variables) and drives the
    penetration to zero with L-BFGS-B.  Verdict by true_geom (40 digits).
    """
    from scipy.optimize import minimize
    per = SQ.load()
    x, y, t = load_pose(m)
    st, box = hmax_scan(x, y, t, grid=grid, angles=angles)
    h, cx, cy, th = refine(x, y, t, st, box)
    n_all = len(x)
    pen0 = pen_vec(np.full(n_all, cx), np.full(n_all, cy), np.full(n_all, th),
                   x, y, t)
    off = [int(j) for j in np.argsort(pen0)[::-1][:max_offend] if pen0[j] > 1e-7]
    free = off
    nf = len(free)
    # pairs to police: the new cell against every cell, plus every free cell
    # against everything (free cells move, so their old contacts must hold too)
    jA, jB = [], []
    for j in range(n_all):
        jA.append(n_all), jB.append(j)          # new cell (index n_all) vs all
    for a in free:
        for b in range(n_all):
            if a != b:
                jA.append(a), jB.append(b)
    jA, jB = np.array(jA), np.array(jB)
    z0 = np.concatenate([x[free], y[free], t[free], [cx, cy, th]])

    def state(z):
        xs, ys, ts = x.copy(), y.copy(), t.copy()
        xs[free], ys[free], ts[free] = z[:nf], z[nf:2 * nf], z[2 * nf:3 * nf]
        allx = np.append(xs, z[3 * nf])
        ally = np.append(ys, z[3 * nf + 1])
        allt = np.append(ts, z[3 * nf + 2])
        return allx, ally, allt

    # the container: a box of side k - margin centred on the frontier pose.
    # It strictly contains the pose (its own side is below k) and anything that
    # fits in it has side < k, so a legal seating here IS a beat.
    kk = SQ.grid(m + 1)
    half = (kk - margin) / 2.0
    bx0, bx1, by0, by1 = half_ext(x, y, t)
    xmid = 0.5 * (float(bx0.min()) + float(bx1.max()))
    ymid = 0.5 * (float(by0.min()) + float(by1.max()))
    lo_x, hi_x = xmid - half, xmid + half
    lo_y, hi_y = ymid - half, ymid + half

    def obj(z):
        X, Y, T = state(z)
        pen = pen_vec(X[jA], Y[jA], T[jA], X[jB], Y[jB], T[jB], eps=1e-9)
        hx = 0.5 * (np.abs(np.cos(T)) + np.abs(np.sin(T)))
        over = (np.clip(X + hx - hi_x, 0, None) ** 2
                + np.clip(lo_x - X + hx, 0, None) ** 2
                + np.clip(Y + hx - hi_y, 0, None) ** 2
                + np.clip(lo_y - Y + hx, 0, None) ** 2)
        return float((pen ** 2).sum() + 1e6 * over.sum())

    res = minimize(obj, z0, method="L-BFGS-B",
                   options={"maxiter": 4000, "ftol": 1e-18, "gtol": 1e-14})
    X, Y, T = state(res.x)
    xs, ys, ts = X[:n_all], Y[:n_all], T[:n_all]
    qx, qy, qt = X[-1], Y[-1], T[-1]
    rec = {"k": SQ.grid(m), "frontier_n": m, "side_max": 2 * h,
           "offenders": off, "pen_before": [float(pen0[j]) for j in off],
           "pen_after": float(obj(res.x)), "freed": nf + 1}
    # full-pose legality check on all pairs, then the true 40-digit side
    tab = json.load(open(TAB))
    rows = [(str(float(a)), str(float(b)), str(float(c)))
            for a, b, c in tab[str(m)]["state"]]
    for a in free:
        rows[a] = (str(float(xs[a])), str(float(ys[a])), str(float(ts[a])))
    cand = rows + [(str(float(qx)), str(float(qy)), str(float(qt)))]
    chk = TG.check(cand)
    rec["candidate_n"] = m + 1
    rec["candidate_side"] = str(+chk["side"])
    rec["candidate_violations"] = len(chk["violations"])
    rec["grid_k"] = SQ.grid(m + 1)
    rec["beat"] = bool(len(chk["violations"]) == 0
                       and chk["side"] < SQ.grid(m + 1))
    print(f"  m={m:4d} ({n_all} cells) free square {2 * h:.5f}  freed {nf + 1} cells"
          f"  penalty {rec['pen_after']:.3e}  -> n={m + 1} side {float(chk['side']):.12f}"
          f"  k={rec['grid_k']} viol {rec['candidate_violations']}"
          + ("   *** BEAT ***" if rec["beat"] else ""), flush=True)
    return rec, cand


def run(only=None, grid=84, angles=13):
    per = SQ.load()
    res = []
    for k, m in frontier_rows(per):
        if only and k not in only:
            continue
        x, y, t = load_pose(m)
        st, box = hmax_scan(x, y, t, grid=grid, angles=angles)
        st = refine(x, y, t, st, box)
        h, cx, cy, th = st
        rec = {"k": k, "frontier_n": m, "L_frontier": SQ.extent(per[m]),
               "side_max": 2 * h, "centre": [cx, cy], "theta": th,
               "fits_one_cell": bool(2 * h >= 1.0 - 1e-9)}
        if rec["fits_one_cell"]:
            # build the candidate: frontier pose + one cell at (cx, cy, th)
            tab = json.load(open(TAB))
            st_rows = [(str(float(a)), str(float(b)), str(float(c)))
                       for a, b, c in tab[str(m)]["state"]]
            cand = st_rows + [(str(cx), str(cy), str(th))]
            chk = TG.check(cand)
            rec["candidate_n"] = m + 1
            rec["candidate_side"] = str(+chk["side"])
            rec["candidate_violations"] = len(chk["violations"])
            rec["candidate_beats_grid"] = bool(
                len(chk["violations"]) == 0 and chk["side"] < SQ.grid(m + 1))
        res.append(rec)
        print(f"  k={k:2d} frontier n={m:4d} side {SQ.extent(per[m]):.9f}  "
              f"largest free square {2 * h:.4f}  shortfall {1 - 2 * h:+.4f}"
              + ("   <-- ONE CELL FITS" if rec["fits_one_cell"] else ""), flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT}")
    return res


def selftest():
    """Two controls with a known answer: an emptied corner, and no hole at all."""
    def grid3(skip):
        xs, ys = [], []
        for i in range(3):
            for j in range(3):
                if (i, j) == skip:
                    continue
                xs.append(0.5 + i)
                ys.append(0.5 + j)
        return np.array(xs), np.array(ys), np.zeros(len(xs))

    for skip, want in (((2, 2), 1.0), (None, 0.0)):
        x, y, t = grid3(skip)
        st, box = hmax_scan(x, y, t, grid=90, angles=7)
        got = 2 * refine(x, y, t, st, box)[0]
        print(f"  control skip={skip}: largest free square {got:.4f} (want {want:.4f})")
        assert abs(got - want) < 0.02, (skip, got, want)
    print("  selftest OK")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--selftest":
        selftest()
    elif args and args[0] == "--seat":
        from scipy.optimize import minimize  # noqa: F401
        per = SQ.load()
        fr = {k: m for k, m in frontier_rows(per)}
        out = []
        for a in args[1:]:
            k = int(a)
            rec, _cand = seat(fr[k]) if k in fr else (None, None)
            if rec:
                out.append(rec)
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump(out, open(os.path.join(ROOT, "workspace/push/seat114.json"), "w"),
                  indent=1)
    else:
        run(only={int(a) for a in args} if args else None)
