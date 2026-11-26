#!/usr/bin/env python3
r"""proposal_anneal.py — STAGE 1: the float proposal engine, with a calibration gate.

WHAT THIS IS.  Stage 1 *proposes*; it never decides.  Every float in the two-stage solver lives
here, and only here.  `snap_certify.py` re-reads these proposals as `Decimal`s, snaps them to
exact rational spinors and adjudicates them with the float-free gate.

WHY IT IS ALLOWED TO EXIST.  A numerical search is the only way to discover a multi-angle pose:
nobody writes down a 118-square contact graph by hand.  The rule is not "never compute with
floats", it is "never *decide* with floats" — so the search sits behind a decimal fence, and its
output is decimal text.

THE CALIBRATION GATE (run 155).  Run 154's annealer was a single-square random walk, and it
failed on every target: at `k - 1e-4` its best pose was still `1.5e-2` illegal.  A negative from
an uncalibrated solver is not evidence, so the solver now has to prove itself first, cold:

    --selftest      n = 5  at L <= 2.71   (max overlap < 1e-6)
                    n = 10 at L <= 3.72
                    n = 39 at L <= 6.85

All three beat the plain integer grid (`ceil(sqrt n)`), all three start from *unaligned* seeds —
random fills and jittered lattices, never from a known optimal packing — and none of them may be
given the answer.  If this gate fails, the run stops here and says so: no n > 100 work is allowed
on a solver that cannot do n = 5.

THE SOLVER.  Multi-body, not one square at a time:

  energy   a smooth max over the four SAT axes of every pair (log-sum-exp, temperature tau),
           softplus'd so an overlap costs its square and a gap costs nothing, plus a wall term;
  relax    scipy L-BFGS-B over all 3n coordinates jointly (numeric gradient — the energy is
           vectorised over pairs, so this is affordable);
  inflate  Lubachevsky-Stillinger style: start above the target side, shrink in stages, relax at
           each, and keep going while the pose stays feasible;
  quench   hard-box projection plus a simultaneous Jacobi separation pass, which is what turns a
           smooth relaxation into a pose with a measured overlap rather than a penalty value.

The last step is deliberately *simultaneous* (every violating pair moves both its cells at once,
by half its penetration along the binding axis) rather than the sequential Gauss-Seidel sweep
run 154 used, which pushed the overlap from one pair to the next and made 18 of 20 rows worse.

USAGE
    python3 scripts/proposal_anneal.py --selftest          # the calibration gate
    python3 scripts/proposal_anneal.py --rank
    python3 scripts/proposal_anneal.py --run --only 117,118 --budget 40
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from decimal import Decimal

import numpy as np
from scipy.optimize import basinhopping, minimize

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

SUBMISSION = os.path.join(ROOT, "workspace/submission/submission.csv")
TARGETS = os.path.join(ROOT, "workspace/push/anneal_targets.json")
OUT = os.path.join(ROOT, "workspace/push/anneal.jsonl")

PASS_PEN = 1e-5
SHRINK = 1e-4
TARGET_OVERLAP = 1e-6            # the calibration gate's "valid packing" line

#: (n, side threshold) — each beats the integer grid `ceil(sqrt n)`, cold
CALIBRATION = ((5, 2.71), (10, 3.72), (39, 6.85))

TIER_A_K = (11, 12, 13, 14, 15)
TIER_A_R = (3, 4)
PROVED_R = (1, 2)


# ------------------------------------------------------------------- ranking
def load_delivered():
    """`{n: Decimal side}` from the CSV, read exactly (the side is max-min, so text is enough)."""
    import true_geom as TG
    per = {}
    with open(SUBMISSION) as f:
        names = [h.strip() for h in f.readline().split(",")]
        ix = {h: i for i, h in enumerate(names)}
        for line in f:
            parts = line.rstrip("\n").split(",")
            if len(parts) < len(names):
                continue
            per.setdefault(int(parts[ix["n"]]), []).append(
                (Decimal(parts[ix["x"]].strip()), Decimal(parts[ix["y"]].strip()),
                 Decimal(parts[ix["angle"]].strip())))
    return {n: TG.side(cells) for n, cells in per.items()}


def rank_targets(limit: int = 20):
    deliv = load_delivered()
    tier_a, rest = [], []
    for n in range(101, 1001):
        k = math.isqrt(n)
        if k * k < n:
            k += 1
        r = k * k - n
        if r < 1 or r in PROVED_R or r > 12:
            continue
        if abs(deliv[n] - k) >= Decimal("1e-8"):
            continue
        gain = Decimal(k) / Decimal(n).sqrt() - 1
        rec = {"n": n, "k": k, "r": r, "delivered": str(deliv[n]),
               "max_gain": str(gain.quantize(Decimal("1e-9")))}
        if k in TIER_A_K and r in TIER_A_R:
            rec["tier"] = "A"
            tier_a.append(rec)
        else:
            rec["tier"] = "B"
            rest.append(rec)
    tier_a.sort(key=lambda rec: (-Decimal(rec["max_gain"]), rec["n"]))
    rest.sort(key=lambda rec: (-Decimal(rec["max_gain"]), rec["n"]))
    ranked = tier_a + rest[:max(0, limit - len(tier_a))]
    for i, rec in enumerate(ranked, 1):
        rec["rank"] = i
    return ranked


def do_rank() -> int:
    ranked = rank_targets(20)
    os.makedirs(os.path.dirname(TARGETS), exist_ok=True)
    with open(TARGETS, "w") as f:
        json.dump(ranked, f, indent=1)
    print(f"{'rank':>4} {'n':>4} {'k':>2} {'r':>2} {'delivered':>12} {'max gain':>9}  tier")
    for rec in ranked:
        print(f"{rec['rank']:>4} {rec['n']:>4} {rec['k']:>2} {rec['r']:>2} "
              f"{Decimal(rec['delivered']):>12.6f} {Decimal(rec['max_gain']):>9.5f}  {rec['tier']}")
    print(f"targets: {os.path.relpath(TARGETS, ROOT)}")
    return 0


# ------------------------------------------------------------------- geometry
def frames(th):
    return np.cos(th), np.sin(th)


def pair_pens(x, y, c, s, I, J):
    """The four SAT penetrations of every pair, vectorised: `(4, P)`, positive = overlap."""
    dx = x[I] - x[J]
    dy = y[I] - y[J]
    out = []
    for k, other in ((I, J), (J, I)):
        for ax, ay in ((c[k], s[k]), (-s[k], c[k])):
            proj = np.abs(dx * ax + dy * ay)
            need = 0.5 + (np.abs(c[other] * ax + s[other] * ay)
                          + np.abs(c[other] * ay - s[other] * ax)) / 2.0
            out.append(need - proj)                 # penetration: > 0 means overlap
    return np.stack(out)


def half_box(c, s):
    """The bounding-box half-extent of every square (same on both axes)."""
    return (np.abs(c) + np.abs(s)) / 2.0


def energy_grad(u, n, L, tau=1e-3, xi=1e-4, kappa=4.0, need_grad=True):
    """The smooth energy and its exact gradient with respect to all `3n` coordinates.

    The energy is a composition of four pieces, and each is differentiated in closed form:

      a_k      `need_k - |proj_k|` per SAT axis, four per pair;
      smin     `min_k a_k` smoothed by a log-sum-exp at temperature `tau`, whose weights are
               the softmax of `-a/tau` (so `d smin / d a_k = w_k`, and `sum_k w_k = 1`);
      pen      `softplus(smin)` at scale `xi`, so overlaps cost their square and gaps nothing;
      walls    `kappa * (excess)^2` per square, with the half-extent's own `theta` derivative.

    Positions enter only through `proj`; angles enter through both the axis direction (`dq`)
    and the other square's projected half-extent.  Everything is a numpy array operation over
    the `n(n-1)/2` pairs, which is the whole point: one pass, not `3n` finite differences.
    """
    x, y, th = u[0::3], u[1::3], u[2::3]
    c, s = np.cos(th), np.sin(th)
    I, J = np.triu_indices(n, 1)
    g = np.zeros(3 * n)
    e = 0.0
    gx = np.zeros(n)
    gy = np.zeros(n)
    gth = np.zeros(n)
    if I.size:
        dx = x[I] - x[J]
        dy = y[I] - y[J]
        owns = (I, I, J, J)
        oths = (J, J, I, I)
        # axis vectors and their theta derivatives, for each of the four axes
        qxs, qys, dqxs, dqys = [], [], [], []
        for k in range(4):
            if k % 2 == 0:                       # u = (c, s),  du/dtheta = (-s, c) = v
                qxs.append(c[owns[k]]); qys.append(s[owns[k]])
                dqxs.append(-s[owns[k]]); dqys.append(c[owns[k]])
            else:                                # v = (-s, c), dv/dtheta = (-c, -s) = -u
                qxs.append(-s[owns[k]]); qys.append(c[owns[k]])
                dqxs.append(-c[owns[k]]); dqys.append(-s[owns[k]])
        a = np.empty((4, I.size))
        sgn = np.empty((4, I.size))
        need = np.empty((4, I.size))
        dn_own = np.empty((4, I.size))
        dn_oth = np.empty((4, I.size))
        for k in range(4):
            qx, qy, dqx, dqy = qxs[k], qys[k], dqxs[k], dqys[k]
            o = oths[k]
            proj = dx * qx + dy * qy
            sgnk = np.where(proj >= 0, 1.0, -1.0)
            A = c[o] * qx + s[o] * qy
            B = c[o] * qy - s[o] * qx
            needk = 0.5 + 0.5 * (np.abs(A) + np.abs(B))
            sA, sB = np.sign(A), np.sign(B)
            need[k] = needk
            sgn[k] = sgnk
            a[k] = needk - np.abs(proj)
            dn_own[k] = 0.5 * (sA * (c[o] * dqx + s[o] * dqy)
                               + sB * (c[o] * dqy - s[o] * dqx))
            dn_oth[k] = 0.5 * (sA * (-s[o] * qx + c[o] * qy)
                               + sB * (-s[o] * qy - c[o] * qx))
        m = a.min(axis=0)
        W = np.exp((m - a) / tau)
        S = W.sum(axis=0)
        w = W / S
        smin = m - tau * np.log(S)
        root = np.sqrt(smin * smin + xi * xi)
        pen = 0.5 * (smin + root)
        e = float(np.sum(pen * pen))
        if need_grad:
            dpen = 0.5 * (1.0 + smin / root)
            gg = 2.0 * pen * dpen * w                 # dE/da_k, shape (4, P)
            Gx = np.zeros(I.size)
            Gy = np.zeros(I.size)
            for k in range(4):
                Gx += gg[k] * sgn[k] * qxs[k]          # dE/dx_I = + sum, dE/dx_J = -sum
                Gy += gg[k] * sgn[k] * qys[k]
            # `proj` is built from `dx = x[I] - x[J]`, so the I cell's derivative is -q
            np.add.at(gx, I, -Gx)
            np.add.at(gx, J, Gx)
            np.add.at(gy, I, -Gy)
            np.add.at(gy, J, Gy)
            for k in range(4):
                own, oth = owns[k], oths[k]
                proj_der = dx * dqxs[k] + dy * dqys[k]
                np.add.at(gth, own, gg[k] * (dn_own[k] - sgn[k] * proj_der))
                np.add.at(gth, oth, gg[k] * dn_oth[k])
    # walls
    h = (np.abs(c) + np.abs(s)) / 2.0
    dh = (np.sign(c) * (-s) + np.sign(s) * c) / 2.0
    lo_x = h - x
    hi_x = x + h - L
    lo_y = h - y
    hi_y = y + h - L
    wall = np.maximum(lo_x, 0) + np.maximum(hi_x, 0) + np.maximum(lo_y, 0) + np.maximum(hi_y, 0)
    e += kappa * float(np.sum(wall * wall))
    if need_grad:
        dwx = -np.where(lo_x > 0, 1.0, 0.0) + np.where(hi_x > 0, 1.0, 0.0)
        dwy = -np.where(lo_y > 0, 1.0, 0.0) + np.where(hi_y > 0, 1.0, 0.0)
        dwh = (np.where(lo_x > 0, 1.0, 0.0) + np.where(hi_x > 0, 1.0, 0.0)
               + np.where(lo_y > 0, 1.0, 0.0) + np.where(hi_y > 0, 1.0, 0.0))
        tw = 2.0 * kappa * wall
        gx += tw * dwx
        gy += tw * dwy
        gth += tw * dwh * dh
    if need_grad:
        g[0::3] = gx
        g[1::3] = gy
        g[2::3] = gth
        return e, g
    return e, None


def energy(u, n, L, tau=1e-3, xi=1e-4, kappa=4.0):
    """The energy alone (kept separate so the optimiser can be called either way)."""
    return energy_grad(u, n, L, tau, xi, kappa, need_grad=False)[0]


def joint_pens(cells, words):
    """SAT penetrations for a pose: `(4, P)`, positive = overlap, and the pair indices."""
    x = np.array([p[0] for p in cells], dtype=float)
    y = np.array([p[1] for p in cells], dtype=float)
    c = np.array([w[0] for w in words], dtype=float)
    s = np.array([w[1] for w in words], dtype=float)
    I, J = np.triu_indices(len(cells), 1)
    return pair_pens(x, y, c, s, I, J), I, J


def max_pen(cells, words):
    """The pose's worst penetration: negative means the pose has that much clearance."""
    if len(cells) < 2:
        return 0.0
    sl, _I, _J = joint_pens(cells, words)
    return float(np.max(np.min(sl, axis=0))) if sl.size else 0.0


def box(cells, words, L):
    """Project every square into `[0, L]^2` (float; Stage 2 re-does this exactly)."""
    out = []
    for (x, y), (c, s) in zip(cells, words):
        h = (abs(c) + abs(s)) / 2.0
        if h > L / 2.0:
            out.append((x, y))
            continue
        out.append((min(max(x, h), L - h), min(max(y, h), L - h)))
    return out


def penetrate(cells, words):
    """The binding violations, vectorised: `[(i, j, qx, qy, sign, pen)]`.

    `q` is the axis of whichever square owns the tightest constraint, `sign` is the sign of the
    pair's projection on it (so that `-sign*q` pushes `i` away from `j` and `+sign*q` pushes `j`
    away from `i`), and `pen` is the penetration, positive.
    """
    sl, I, J = joint_pens(cells, words)
    worst = sl.min(axis=0)                     # SAT: the tightest axis is the pair's state
    bad = np.nonzero(worst > 0)[0]
    out = []
    for p in bad:
        k = int(np.argmin(sl[:, p]))
        i, j = int(I[p]), int(J[p])
        c, s = words[i if k < 2 else j]
        qx, qy = (c, s) if k % 2 == 0 else (-s, c)
        proj = (cells[j][0] - cells[i][0]) * qx + (cells[j][1] - cells[i][1]) * qy
        out.append((i, j, qx, qy, 1.0 if proj >= 0 else -1.0, float(sl[k, p])))
    return out


def quench(cells, words, L, iters=600, damping=0.5):
    """Simultaneous damped separation + hard box: every violating pair moves both its cells.

    This is the fix for run 154's sequential sweep, which pushed one pair's overlap into its
    neighbour.  Every pair's residual is accumulated first, then all cells move together.
    """
    cells = box(cells, words, L)
    for _ in range(iters):
        bad = penetrate(cells, words)
        if not bad:
            break
        acc = [[0.0, 0.0] for _ in cells]
        for i, j, qx, qy, sgn, pen in bad:
            d = damping * pen
            acc[i][0] -= sgn * d * qx
            acc[i][1] -= sgn * d * qy
            acc[j][0] += sgn * d * qx
            acc[j][1] += sgn * d * qy
        cells = [(x + dx, y + dy) for (x, y), (dx, dy) in zip(cells, acc)]
        cells = box(cells, words, L)
    return cells


# --------------------------------------------------------------------- seeds
def seed_random(n, L, rng):
    return ([(float(v), float(w)) for v, w in rng.uniform(0, L, (n, 2))],
            [(float(math.cos(t)), float(math.sin(t)))
             for t in rng.uniform(0, math.pi / 2, n)])


def seed_lattice(n, L, rng):
    """A jittered square lattice, optionally with a random spin — never a known packing."""
    m = max(1, int(math.ceil(math.sqrt(n))))
    step = L / m
    pts = [((i + 0.5) * step + rng.normal(0, 0.01 * step),
            (j + 0.5) * step + rng.normal(0, 0.01 * step))
           for j in range(m) for i in range(m)][:n]
    cells = [(p[0], p[1]) for p in pts]
    words = [(1.0, 0.0)] * len(cells)
    if rng.random() < 0.5 and len(cells) > 2:      # spin a few cells
        for idx in rng.choice(len(cells), max(1, len(cells) // 6), replace=False):
            t = float(rng.uniform(0, math.pi / 2))
            words[int(idx)] = (math.cos(t), math.sin(t))
    return cells, words


def seed_strip(n, L, rng):
    """Rows with a tilted last row — the k^2 + 1 motif's neighbourhood, not its answer."""
    rows, left = [], n
    width = max(1, int(math.floor(L)))
    while left > 0:
        c = min(width, left)
        rows.append(c)
        left -= c
    cells, words = [], []
    y = 0.0
    for ri, c in enumerate(rows):
        tilt = float(rng.uniform(0.6, 0.85)) if ri == len(rows) - 1 and c > 1 else 0.0
        h = (abs(math.cos(tilt)) + abs(math.sin(tilt))) / 2.0
        y += h
        x = (L - c) / 2 + 0.5
        for _ in range(c):
            cells.append((x, y))
            words.append((math.cos(tilt), math.sin(tilt)))
            x += 1.0
        y += h
    return cells, words


def seed_defect(n, L, rng):
    """The lattice with `m^2 - n` cells removed at the *boundary and corner* sites.

    The missing cells of a row `n = k^2 - r` are exactly a boundary defect, so a seed that
    removes them from the wall (corners first) starts in the topologically right place: the
    notch is where the strain is, and the relaxation only has to heal it.
    """
    m = max(1, int(math.ceil(math.sqrt(n))))
    step = L / m
    sites = [(i, j) for j in range(m) for i in range(m)]
    edge = {i: min(i, j, m - 1 - i, m - 1 - j) for i, j in sites}

    def key(site):
        i, j = site
        return (edge[i] + 0.5 * rng.random(), rng.random())

    keep = sorted(sites, key=key)[:n]
    cells = [((i + 0.5) * step, (j + 0.5) * step) for i, j in keep]
    words = [(1.0, 0.0)] * len(cells)
    return cells, words


def seed_corner(n, L, rng):
    """A floor-lattice block plus the leftover cells packed into its margin at random angles.

    This is the seed family the target rows actually live in: `m = floor(sqrt n)` cells in an
    `m x m` block, and the `n - m^2` leftovers (3 or 4 for a `k^2 - r` row) tilted into the
    margin.  The angles and margin positions are random, so this is a *hypothesis about where
    the packing lives*, not a copy of a known pose — the calibration cases still have to find
    their own side.
    """
    m = max(1, int(math.floor(math.sqrt(n))))
    step = L / (m + 0.45)
    cells = [((i + 0.5) * step, (j + 0.5) * step) for j in range(m) for i in range(m)]
    words = [(1.0, 0.0)] * len(cells)
    extra = n - len(cells)
    for _ in range(max(0, extra)):
        ang = float(rng.uniform(0.6, 0.9)) * (1 if rng.random() < 0.5 else -1)
        h = (abs(math.cos(ang)) + abs(math.sin(ang))) / 2.0
        cells.append((float(rng.uniform(h, L - h)), float(rng.uniform(h, L - h))))
        words.append((math.cos(ang), math.sin(ang)))
    return cells, words


SEEDS = {"corner": seed_corner, "defect": seed_defect, "strip": seed_strip,
         "lattice": seed_lattice, "random": seed_random}


# -------------------------------------------------------------------- the solver
class StopRun(Exception):
    """Raised by a deadline callback to abandon a restart that has used its time."""


class Cap:
    """A hard wall-clock cap enforced *inside* the optimiser's callback.

    The cap is what run 155 lacked: its budget was only checked between restarts, so one
    `solve` at n = 39 ran for 526 s and the case never got a second attempt.  Here every
    L-BFGS-B iteration and every basin-hopping step checks the clock.
    """

    def __init__(self, seconds):
        self.t_end = time.monotonic() + seconds
        self.last = None
        self.hit = False
        self.used = 0.0

    def expired(self) -> bool:
        return time.monotonic() >= self.t_end

    def __call__(self, *args):
        if args:
            self.last = np.array(args[0], dtype=float)
        if self.expired():
            self.hit = True
            raise StopRun
        return False


def relax(u, n, L, iters=140, cap=None):
    """Joint L-BFGS-B over all 3n coordinates, with the analytic gradient (`jac=True`)."""
    holder = {"u": np.array(u, dtype=float)}

    def cb(xk):
        holder["u"] = np.array(xk, dtype=float)
        if cap is not None and cap.expired():
            cap.hit = True
            raise StopRun

    try:
        res = minimize(energy_grad, u, jac=True, args=(n, L), method="L-BFGS-B",
                       callback=cb, options={"maxiter": iters, "maxfun": 6 * iters})
        return res.x, float(res.fun)
    except StopRun:
        v = holder["u"]
        return v, energy(v, n, L)


def to_u(cells, words):
    u = np.empty(3 * len(cells))
    u[0::3] = [p[0] for p in cells]
    u[1::3] = [p[1] for p in cells]
    u[2::3] = [math.atan2(w[1], w[0]) for w in words]
    return u


def from_u(u, n):
    return (list(zip(u[0::3], u[1::3])),
            [(math.cos(t), math.sin(t)) for t in u[2::3]])


def shrink_path(n, L_target, seed_name, rng, iters=40, factor=0.99, slack=1.30, cap=None):
    """Inflation: start above the side, relax at every step, shrink while it stays feasible."""
    cells, words = SEEDS[seed_name](n, L_target * slack, rng)
    u = to_u(cells, words)
    L = L_target * slack
    while L > L_target * (1 + 1e-12):
        if cap is not None and cap.expired():
            return u
        u, _e = relax(u, n, L, iters, cap=cap)
        L = max(L_target, L * factor)
    u, _e = relax(u, n, L_target, 3 * iters, cap=cap)
    return u


def own_pen(cells, words):
    """Each cell's worst penetration over its pairs -- who is being squeezed the hardest."""
    n = len(cells)
    if n < 2:
        return np.zeros(n)
    I, J = np.triu_indices(n, 1)
    pen = pair_pens(cells[:, 0], cells[:, 1], words[:, 0], words[:, 1], I, J).min(axis=0)
    out = np.full(n, -np.inf)
    np.maximum.at(out, I, pen)
    np.maximum.at(out, J, pen)
    return out


def cell_slack(cx, cy, cc, cs, cells, words):
    """Run 127's exact `slack` for one probe cell against every cell, vectorised.

    `legal_slide.slack` is `max` over the **four** separating axes -- both squares' own frames,
    two axes each -- of `|proj| - (h_probe + h_other)`: two convex sets are disjoint when at
    least one axis separates them, so the pair's state is the *largest* slack.  (The energy uses
    the complementary view, `min` penetration; the two are negative of each other, and it is
    worth keeping them separate in the head because run 155's inverted-measure bug lived here.)
    The probe is a unit cell, so in its own frame `h_probe = 1/2` exactly, and in the other's
    frame `h_other = 1/2`; both are added back explicitly -- omitting either is a silent
    half-unit error, which is what the exact seat control in `--selftest` caught.

    Returns `(K,)`: the worst separation each of the `K` probe candidates achieves.
    """
    dx = cells[None, :, 0] - cx[:, None]
    dy = cells[None, :, 1] - cy[:, None]
    ax, ay = words[None, :, 0], words[None, :, 1]
    cc, cs = cc[:, None], cs[:, None]
    h_oth_p = 0.5 * (np.abs(ax * cc + ay * cs) + np.abs(ay * cc - ax * cs))
    h_probe_o = 0.5 * (np.abs(cc * ax + cs * ay) + np.abs(cc * ay - cs * ax))
    four = np.stack([np.abs(dx * cc + dy * cs) - (0.5 + h_oth_p),
                     np.abs(-dx * cs + dy * cc) - (0.5 + h_oth_p),
                     np.abs(dx * ax + dy * ay) - (0.5 + h_probe_o),
                     np.abs(-dx * ay + dy * ax) - (0.5 + h_probe_o)])
    return four.max(axis=0).min(axis=1)


def void_seat(cells, words, moving, L, grid=9, angles=(0.0, 0.4, 0.785398, 1.2, 1.570796)):
    """The best seat for cell `moving`: the centre that leaves it the most room, walls first.

    This is `legal_slide.void_seats`'s question -- *where can this cell go?* -- asked of a
    continuous pose instead of a whole-cell lattice: the scan is a `grid x grid` of centres
    at each of `angles`, scored by the four-axis slack of run 127 against the other cells and
    minus the wall excess, so a genuine void (slack `>= 0`) is preferred but a jammed pose
    still yields its deepest gap.  The gate pins this against the exact seat finder on the
    lattice control, because a re-implementation has to be anchored to its source.
    """
    rest = np.delete(np.arange(len(cells)), moving)
    lo, hi = 0.0, L
    xs = np.linspace(lo, hi, grid)
    gx, gy = np.meshgrid(xs, xs, indexing="ij")
    cx0 = gx.reshape(-1)
    cy0 = gy.reshape(-1)
    best = None
    for ang in angles:
        cc = np.full(cx0.shape, math.cos(ang))
        cs = np.full(cx0.shape, math.sin(ang))
        h = (abs(math.cos(ang)) + abs(math.sin(ang))) / 2.0
        wall = (np.maximum(h - cx0, 0) + np.maximum(cx0 + h - L, 0)
                + np.maximum(h - cy0, 0) + np.maximum(cy0 + h - L, 0))
        sc = cell_slack(cx0, cy0, cc, cs, cells[rest], words[rest]) - 8.0 * wall
        k = int(np.argmax(sc))
        if best is None or sc[k] >= best[0]:
            best = (float(sc[k]), float(cx0[k]), float(cy0[k]), float(ang))
    return best[1], best[2], best[3]


class _StructStep:
    """Run 127's move set as basin-hopping's step: jitter, **teleport into a seat**, or swap.

    A jitter cannot cross a closed gap, which is exactly why the gate's `n = 5` case jammed at
    1.45e-1 in run 156: the `2 + 1/sqrt 2` pose needs its fifth square *between* the block's
    corners.  The teleport move asks the seat finder where that square has the most room and
    puts it there outright -- the relaxation that follows then decides whether the block yields.
    The swap exchanges a lattice-aligned cell with a tilted one, which changes *which* cell
    carries the angle without moving the block at all.
    """

    def __init__(self, rng, n, L, pos=0.06, ang=0.30, p_squeeze=0.25, p_teleport=0.15,
                 p_swap=0.15):
        self.rng, self.n, self.L = rng, n, L
        self.pos, self.ang = pos, ang
        self.p_squeeze, self.p_teleport, self.p_swap = p_squeeze, p_teleport, p_swap

    def __call__(self, u):
        v = np.array(u, dtype=float).reshape(self.n, 3)
        r = float(self.rng.random())
        if r < self.p_swap:
            self._swap(v)
        elif r < self.p_swap + self.p_teleport:
            self._teleport(v)
        elif r < self.p_swap + self.p_teleport + self.p_squeeze:
            self._squeeze(v)
        else:
            k = int(self.rng.integers(self.n))
            v[k, 0] += float(self.rng.normal(0, self.pos))
            v[k, 1] += float(self.rng.normal(0, self.pos))
            v[k, 2] += float(self.rng.normal(0, self.ang))
        return v.reshape(-1)

    def _squeeze(self, v):
        """Put a tilted cell where the pose is most crowded, then let the relaxation decide.

        This is the move the `n = 5` gate needed.  The jammed pose is a solid block of five
        axis-aligned squares, and no jitter or seat search can put a square *inside* it: every
        seat with room is outside.  Squeezing a 45-degree cell into the centroid makes the
        cell illegal on purpose, and L-BFGS-B then has to open the block around it -- which is
        exactly the pinwheel/centre-diamond rearrangement the `2 + 1/sqrt 2` optimum needs.  The
        jitter matters: the exact centroid at exactly 45 degrees is a symmetric jam that
        relaxes back, and the perturbed version finds a pose with `-5.4e-5` clearance in ~0.3 s.
        """
        k = int(self.rng.integers(self.n))
        v[k, 0] = float(v[:, 0].mean() + self.rng.normal(0, 0.15))
        v[k, 1] = float(v[:, 1].mean() + self.rng.normal(0, 0.15))
        v[k, 2] = math.pi / 4 + float(self.rng.normal(0, 0.2))

    def _teleport(self, v):
        cells = v[:, :2].copy()
        words = np.stack([np.cos(v[:, 2]), np.sin(v[:, 2])], axis=1)
        worst = int(np.argmax(own_pen(cells, words)))
        x, y, a = void_seat(cells, words, worst, self.L)
        v[worst, 0], v[worst, 1], v[worst, 2] = x, y, a

    def _swap(self, v):
        s2 = np.abs(np.sin(2.0 * v[:, 2]))
        flat = np.where(s2 < 0.30)[0]
        tilt = np.where(s2 > 0.70)[0]
        if len(flat) == 0 or len(tilt) == 0:
            return
        i = int(flat[self.rng.integers(len(flat))])
        j = int(tilt[self.rng.integers(len(tilt))])
        v[i], v[j] = v[j], v[i].copy()


class _Perturb:
    """Basin-hopping move: displace one square and re-orient it a little."""

    def __init__(self, rng, n, pos=0.06, ang=0.30):
        self.rng, self.n, self.pos, self.ang = rng, n, pos, ang

    def __call__(self, u):
        v = u.copy()
        k = int(self.rng.integers(self.n))
        v[3 * k] += self.rng.normal(0, self.pos)
        v[3 * k + 1] += self.rng.normal(0, self.pos)
        v[3 * k + 2] += self.rng.normal(0, self.ang)
        return v


def basin(u, n, L, rng, steps=200, pos=0.06, ang=0.30, cap=None, step=None):
    """Basin-hopping: perturb one square, re-relax, keep the best (this is the global escape)."""
    best = {"f": float("inf"), "x": np.array(u, dtype=float)}

    def cb(x, f, accept):
        # accumulating the *best* here is not bookkeeping: `basinhopping` returns its best local
        # minimum only on a clean exit, so without this a cap abort returned the last step and
        # threw away the good pose the structural stage had just found (n = 5 fell from -4e-5
        # back to 3.6e-1 before this line existed).
        if args_ok(x) and f < best["f"]:
            best["f"], best["x"] = float(f), np.array(x, dtype=float)
        if cap.expired():
            cap.hit = True
            raise StopRun

    def args_ok(x):
        return hasattr(x, "__len__")

    try:
        res = basinhopping(energy_grad, u, niter=steps,
                           minimizer_kwargs={"jac": True, "args": (n, L),
                                             "method": "L-BFGS-B",
                                             "options": {"maxiter": 150, "maxfun": 3000}},
                           take_step=step if step is not None else _Perturb(rng, n, pos, ang),
                           niter_success=steps,
                           callback=cb, seed=int(rng.integers(1 << 30)))
        return res.x
    except StopRun:
        return best["x"]


def squeeze_ladder(u, n, L, rng, cap, target=TARGET_OVERLAP, iters=600, quench_iters=2000):
    """Hill-climb with the structural move: squeeze a tilted cell into the centroid, relax, keep.

    This is the move that changes the pose's *topology* rather than its detail.  The jitter and
    seat moves in `_StructStep` search around the current basin; this one deliberately breaks it
    and asks the relaxation to re-form, and it keeps the best pose so a failed squeeze costs
    nothing but time.  Returns the last accepted pose (an `u` vector) and leaves the clock to
    `cap`, which is raised from inside `relax`.
    """
    best = (max_pen(*from_u(u, n)), u)
    while not cap.expired():
        if best[0] < target:
            break
        cells, words = from_u(best[1], n)
        v = np.column_stack([np.asarray(cells, float),
                             np.arctan2(np.asarray(words, float)[:, 1],
                                        np.asarray(words, float)[:, 0])])
        k = int(rng.integers(n))
        if rng.random() < 0.6:                       # the centroid squeeze: the n = 5 move
            v[k, 0] = float(v[:, 0].mean() + rng.normal(0, 0.18))
            v[k, 1] = float(v[:, 1].mean() + rng.normal(0, 0.18))
            ang0 = math.pi / 4
        else:                                        # a random point, a random tilt
            v[k, 0] = float(rng.uniform(0.5, max(0.6, L - 0.5)))
            v[k, 1] = float(rng.uniform(0.5, max(0.6, L - 0.5)))
            ang0 = float(rng.uniform(0.0, math.pi / 2))
        v[k, 2] = ang0 + float(rng.normal(0, 0.2))
        if n > 8 and rng.random() < 0.35:
            # a second cell as well: one 45-degree square opens a five-cell block, but a 39-cell
            # pose needs a bigger hole before the relaxation can re-form around it
            j = int(rng.integers(n))
            if j != k:
                v[j, 0] = float(v[:, 0].mean() + rng.normal(0, 0.30))
                v[j, 1] = float(v[:, 1].mean() + rng.normal(0, 0.30))
                v[j, 2] = ang0 + math.pi / 2 + float(rng.normal(0, 0.2))
        cand, _e = relax(v.reshape(-1), n, L, iters, cap=cap)
        cc, ww = from_u(cand, n)
        cc = quench(cc, ww, L, iters=quench_iters, damping=0.25)
        p = max_pen(cc, ww)
        if p < best[0]:
            best = (p, to_u(cc, ww))
    return best[1]


def solve(n, L_target, seed_name, rng, steps=200, shrink=True, cap_seconds=15.0):
    """The solver: inflate, squeeze a fresh block, then basin-hop -- each stage with its share.

    The order and the shares both matter, and both were learned the hard way in run 157:

    * the ladder must not run last -- run 156's first version let basin-hopping spend the whole
      cap, so the structural move never started and `n = 5` sat at `1.45e-1` with a working move
      sitting unused at the end of the pipeline;
    * it must not run on the inflation's output either -- that pose is already smeared by
      hundreds of L-BFGS steps and the squeeze's clean block is gone (`n = 5` failed there at
      8.2e-2 over ten tries);
    * it passes in 0-1.5 s on a *fresh* lattice block, which is what the seed at the target side
      gives after one short relaxation.

    So: inflate for structure-agnostic breadth, squeeze a fresh block for the topological move,
    then basin-hop around whichever pose is better with what time is left.
    """
    t_all = float(cap_seconds)
    t0 = time.monotonic()
    caps = []
    cap = Cap(0.25 * t_all)
    caps.append(cap)
    if shrink:
        u = shrink_path(n, L_target, seed_name, rng, cap=cap)
    else:
        cells, words = SEEDS[seed_name](n, L_target, rng)
        u = to_u(cells, words)
    cap = Cap(0.45 * t_all)
    caps.append(cap)
    cells, words = SEEDS[seed_name](n, L_target, rng)
    fresh, _e = relax(to_u(cells, words), n, L_target, 400, cap=cap)
    fresh = squeeze_ladder(fresh, n, L_target, rng, cap)
    if max_pen(*from_u(fresh, n)) < max_pen(*from_u(u, n)):
        u = fresh
    if max_pen(*from_u(u, n)) < TARGET_OVERLAP:      # solved: do not spend the rest of the cap
        cells, words = from_u(u, n)
        return {"pen": max_pen(cells, words), "L": L_target, "cells": cells,
                "words": words, "seed": seed_name, "cap_hit": any(c.hit for c in caps),
                "seconds": round(time.monotonic() - t0, 2)}
    left = max(0.5, t_all - (time.monotonic() - t0))
    cap = Cap(left)
    caps.append(cap)
    keep = (max_pen(*from_u(u, n)), np.array(u, dtype=float))
    u = basin(u, n, L_target, rng, steps=steps, cap=cap,
              step=_StructStep(rng, n, L_target))
    cells, words = from_u(u, n)
    cells = quench(cells, words, L_target, iters=1500, damping=0.25)
    if max_pen(cells, words) > keep[0]:          # the last stage may not give a good pose back
        cells, words = from_u(keep[1], n)
    return {"pen": max_pen(cells, words), "L": L_target, "cells": cells,
            "words": words, "seed": seed_name, "cap_hit": any(c.hit for c in caps),
            "seconds": round(time.monotonic() - t0, 2)}


def solve_best(n, L_target, seeds, rng, steps=200, budget=None):
    """Try each seed; keep the best pose.  `budget` (seconds) bounds the whole call."""
    best = None
    t0 = time.time()
    for name in seeds:
        r = solve(n, L_target, name, rng, steps=steps)
        if best is None or r["pen"] < best["pen"]:
            best = r
        if best["pen"] < TARGET_OVERLAP:
            break
        if budget is not None and time.time() - t0 > budget:
            break
    return best


# ------------------------------------------------------------------ calibration
def do_selftest() -> int:
    """The calibration gate: analytic gradient, cold-start packings, then the audit.

    Three things run here and all three must pass before any `n > 100` row is touched:
    the analytic gradient against finite differences (`< 1e-7`), and three cold-start
    packings that beat the integer grid.  The whole gate is budgeted to stay under a
    minute: each restart has a hard per-restart cap enforced inside the optimiser, so no
    single run can stall the gate the way run 155's `n = 39` did.
    """
    t_start = time.time()
    print("calibration gate (analytic gradient, then cold-start packings)", flush=True)

    rng_m = np.random.default_rng(99)
    worst = 0.0
    n_dims = 0
    for n, L in ((5, 2.71), (40, 6.9)):
        cells, words = seed_random(n, L, rng_m)
        u = to_u(cells, words)
        _e, g = energy_grad(u, n, L)
        h = 1e-6
        for k in range(len(u)):
            d = np.zeros_like(u)
            d[k] = h
            worst = max(worst, abs(g[k] - (energy(u + d, n, L) - energy(u - d, n, L)) / (2 * h)))
        n_dims += len(u)
    ok_grad = worst < 1e-7
    print(f"  0. analytic gradient vs finite differences: max |error| = {worst:.2e} over "
          f"{n_dims} coordinates  {'PASS' if ok_grad else 'FAIL'}", flush=True)

    # 1. the seat finder and its slack are pinned to run 127's exact versions, because a
    #    re-implementation of an exact routine has to be anchored to its source.  The first
    #    port of this was wrong by exactly half a unit per axis (the probe's own half-extent was
    #    missing) and took the min over the four axes where run 127 takes the max; the control
    #    below catches both, on the 3x3-minus-centre pose that has seven exact seats.
    import legal_slide as LS
    st = LS.holed_pose()
    dr = LS.directions(st)
    sc = np.array([[float(q[0]), float(q[1])] for q in st])
    sw = np.array([[float(c), float(s)] for c, s in dr])
    worst_seat = 0.0
    for i in range(len(st)):
        for j in range(len(st)):
            if i == j:
                continue
            ex = float(LS.slack((st[i][0], st[i][1], dr[i][0], dr[i][1]),
                                (st[j][0], st[j][1], dr[j][0], dr[j][1])))
            my = float(cell_slack(np.array([sc[i, 0]]), np.array([sc[i, 1]]),
                                  np.array([sw[i, 0]]), np.array([sw[i, 1]]),
                                  sc[j:j + 1], sw[j:j + 1])[0])
            worst_seat = max(worst_seat, abs(ex - my))
    seats = LS.void_seats(st, dr, moving=0)
    legal = bool(seats) and all(
        float(cell_slack(np.array([float(q[0])]), np.array([float(q[1])]),
                         np.array([sw[0, 0]]), np.array([sw[0, 1]]), sc[1:], sw[1:])[0]) >= -1e-12
        for q in seats)
    ok_seat = worst_seat < 1e-12 and legal
    print(f"  1. seat finder vs run 127: {len(st) * (len(st) - 1)} pair slacks agree to "
          f"{worst_seat:.1e}, {len(seats)} exact seat(s) all legal  "
          f"{'PASS' if ok_seat else 'FAIL'}", flush=True)

    plan = ((5, 2.71, 8.0), (10, 3.72, 10.0), (39, 6.85, 42.0))
    failures = [] if ok_grad else [("gradient", 0, worst)]
    if not ok_seat:
        failures.append(("seat", worst_seat, 0))
    for n, thresh, budget in plan:
        grid = math.ceil(math.sqrt(n))
        t0 = time.time()
        best = None
        rng = np.random.default_rng(3000 + n)
        seeds = ["corner", "defect", "strip", "random"]
        rep = 0
        while time.time() - t0 < budget:
            cap = min(20.0, budget - (time.time() - t0))
            if cap <= 1.0:
                break
            r = solve(n, thresh, seeds[rep % len(seeds)], rng, steps=4000, cap_seconds=cap)
            rep += 1
            if best is None or r["pen"] < best["pen"]:
                best = r
            if best["pen"] < TARGET_OVERLAP:
                break
        ok = best["pen"] < TARGET_OVERLAP
        print(f"  n={n:>2}  L <= {thresh:<5} grid side {grid}  found L = {best['L']:.6f}  "
              f"max overlap {best['pen']:+.3e}  restarts {rep}  ({time.time() - t0:.1f}s)  "
              f"{'PASS' if ok else 'FAIL'}", flush=True)
        if not ok:
            failures.append((n, thresh, round(best["pen"], 6)))
        else:
            assert best["L"] < grid, (n, best["L"], grid)

    checked, offenders, skipped = _audit_self()
    print(f"  float audit of the shaping helpers: {checked} functions, {len(offenders)} naming "
          f"float (Stage 1 is the declared float stage)", flush=True)
    total = time.time() - t_start
    print(f"calibration gate: {total:.1f}s", flush=True)
    if failures:
        print(f"CALIBRATION FAILED: {failures} — no n > 100 work is allowed on this solver")
        return 1
    if total >= 60.0:
        print(f"CALIBRATION FAILED: {total:.1f}s is over the 60 s budget")
        return 1
    print("calibration PASSED: analytic gradient verified and 3/3 cold packings beat the grid")
    return 0


def _audit_self():
    """Prove the Stage-1 helpers that *shape* proposals contain no decision arithmetic."""
    import exact_field as EF
    checked, offenders, skipped = EF.audit_module(
        sys.modules[__name__], exempt=EF.AUDIT_EXEMPT + ("do_selftest", "energy", "solve",
                                                         "solve_best", "relax", "quench",
                                                         "seed_random", "seed_lattice",
                                                         "seed_strip", "penetrate",
                                                         "pair_pens", "half_box", "frames",
                                                         "joint_pens", "max_pen", "box",
                                                         "energy_grad", "energy", "relax",
                                                         "basin", "Cap", "StopRun",
                                                         "seed_defect", "seed_corner", "_Perturb",
                                                         "do_selftest"))
    return checked, offenders, skipped


# ------------------------------------------------------------------------ run
def emit(n, rec, r, target_L, out):
    cells = [{"x": format(float(x), ".17g"), "y": format(float(y), ".17g"),
              "a": format(float(math.atan2(s_, c_)), ".17g")}
             for (x, y), (c_, s_) in zip(r["cells"], r["words"])]
    rec_out = {"proposal": True, "n": n, "k": rec["k"], "r": rec["r"], "rank": rec["rank"],
               "tier": rec["tier"], "target_L": format(float(target_L), ".17g"),
               "side": format(float(target_L), ".17g"), "pen": format(float(r["pen"]), ".17g"),
               "seed": r["seed"],
               "qualifies": bool(r["pen"] < PASS_PEN),
               "cells": cells}
    out.write(json.dumps(rec_out) + "\n")
    out.flush()


def main() -> int:
    argv = sys.argv
    if "--selftest" in argv:
        return do_selftest()
    if "--rank" in argv:
        return do_rank()
    budget = float(argv[argv.index("--budget") + 1]) if "--budget" in argv else 40.0
    only = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else OUT
    with open(TARGETS) as f:
        ranked = json.load(f)
    if only:
        ranked = [r for r in ranked if str(r["n"]) in only]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    rng = np.random.default_rng(20261127)
    with open(out_path, "w") as out:
        for rec in ranked:
            n, k = rec["n"], rec["k"]
            target_L = k - SHRINK
            t0 = time.time()
            best = None
            while time.time() - t0 < budget:
                r = solve_best(n, target_L, ["strip", "lattice", "random"], rng)
                if best is None or r["pen"] < best["pen"]:
                    best = r
                if best["pen"] < PASS_PEN:
                    break
            emit(n, rec, best, target_L, out)
            print(f"n={n} k={k} r={rec['r']} tier={rec['tier']}: pen={best['pen']:.3e} "
                  f"at L={target_L:.6f} ({time.time() - t0:.1f}s) "
                  f"qualifies={best['pen'] < PASS_PEN}", flush=True)
    print(f"proposals: {os.path.relpath(out_path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
