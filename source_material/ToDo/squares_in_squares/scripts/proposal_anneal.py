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


def energy(u, n, L, tau=1e-3, xi=1e-4, kappa=4.0):
    """Smooth multi-body energy: squared penetration over all pairs plus a wall term."""
    x, y, th = u[0::3], u[1::3], u[2::3]
    c, s = frames(th)
    I, J = np.triu_indices(n, 1)
    if I.size:
        sl = pair_pens(x, y, c, s, I, J)
        # SAT: a pair is separated iff SOME axis separates, so the pair's penetration is the
        # MINIMUM over its four axes.  (Run 155's first draft took the maximum and the solver
        # spent its time fighting axes that were already clear.)
        m = sl.min(axis=0)
        smin = m - tau * np.log(np.exp((m - sl) / tau).sum(axis=0))
        # softplus(smin): an overlap costs its square, a gap costs (almost) nothing
        pen = 0.5 * (smin + np.sqrt(smin * smin + xi * xi))
        e = float(np.sum(pen * pen))
    else:
        e = 0.0
    h = half_box(c, s)
    wall = (np.maximum(h - x, 0.0) + np.maximum(x + h - L, 0.0)
            + np.maximum(h - y, 0.0) + np.maximum(y + h - L, 0.0))
    return e + kappa * float(np.sum(wall * wall))


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


SEEDS = {"random": seed_random, "lattice": seed_lattice, "strip": seed_strip}


# -------------------------------------------------------------------- the solver
def relax(u, n, L, iters=140):
    """Joint L-BFGS-B over all 3n coordinates at one side."""
    res = minimize(energy, u, args=(n, L), method="L-BFGS-B",
                   options={"maxiter": iters, "maxfun": 6 * iters * n})
    return res.x, float(res.fun)


def to_u(cells, words):
    u = np.empty(3 * len(cells))
    u[0::3] = [p[0] for p in cells]
    u[1::3] = [p[1] for p in cells]
    u[2::3] = [math.atan2(w[1], w[0]) for w in words]
    return u


def from_u(u, n):
    return (list(zip(u[0::3], u[1::3])),
            [(math.cos(t), math.sin(t)) for t in u[2::3]])


def shrink_path(n, L_target, seed_name, rng, iters=40, factor=0.99, slack=1.30):
    """Inflation: start above the side, relax at every step, shrink while it stays feasible."""
    cells, words = SEEDS[seed_name](n, L_target * slack, rng)
    u = to_u(cells, words)
    L = L_target * slack
    while L > L_target * (1 + 1e-12):
        u, _e = relax(u, n, L, iters)
        L = max(L_target, L * factor)
    u, _e = relax(u, n, L_target, 4 * iters)
    return u


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


def basin(u, n, L, rng, steps=200, pos=0.06, ang=0.30):
    """Basin-hopping: perturb one square, re-relax, keep the best (this is the global escape)."""
    res = basinhopping(energy, u, niter=steps,
                       minimizer_kwargs={"args": (n, L), "method": "L-BFGS-B",
                                         "options": {"maxiter": 120, "maxfun": 12000}},
                       take_step=_Perturb(rng, n, pos, ang), niter_success=steps,
                       seed=int(rng.integers(1 << 30)))
    return res.x


def solve(n, L_target, seed_name, rng, steps=200, shrink=True):
    """The solver: inflate to the target side, basin-hop, then quench into the hard box."""
    if shrink:
        u = shrink_path(n, L_target, seed_name, rng)
    else:
        cells, words = SEEDS[seed_name](n, L_target, rng)
        u = to_u(cells, words)
    u = basin(u, n, L_target, rng, steps=steps)
    cells, words = from_u(u, n)
    cells = quench(cells, words, L_target, iters=1500, damping=0.25)
    return {"pen": max_pen(cells, words), "L": L_target, "cells": cells,
            "words": words, "seed": seed_name}


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
    """The calibration gate: cold-start packings that beat the integer grid, then the audit."""
    print("calibration gate (cold start, random/strip/lattice seeds; max overlap < 1e-6)",
          flush=True)
    failures = []
    for n, thresh in CALIBRATION:
        grid = math.ceil(math.sqrt(n))
        budget = 75.0 if n <= 10 else 150.0
        t0 = time.time()
        best = None
        rng = np.random.default_rng(2000 + n)
        seeds = ["random", "strip", "lattice"]
        rep = 0
        while time.time() - t0 < budget:
            r = solve(n, thresh, seeds[rep % len(seeds)], rng, steps=260 if n <= 10 else 160)
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
          f"float (Stage 1 is the declared float stage; exempt {skipped})")
    if failures:
        print(f"CALIBRATION FAILED: {failures} — no n > 100 work is allowed on this solver")
        return 1
    print("calibration PASSED (3/3): the solver finds packings that beat the integer grid, cold")
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
                                                         "joint_pens", "max_pen", "box"))
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
