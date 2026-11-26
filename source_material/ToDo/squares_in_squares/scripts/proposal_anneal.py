#!/usr/bin/env python3
r"""proposal_anneal.py — STAGE 1: the float proposal engine. The only float in the pipeline.

WHAT THIS IS, AND WHAT IT IS NOT.  This module *proposes*; it never decides.  It runs
simulated annealing / overlap projection with container shrinkage at a target side
`L <= k - 1e-4` and writes its best poses, with their residuals, as decimal text.  Every
float in the two-stage solver lives here, and only here: `snap_certify.py` re-reads these
proposals as `Decimal`s, snaps them to exact rational spinors and adjudicates them with the
float-free gate.  A proposal this module *likes* has no authority at all — the pass rule is
`max penetration < 1e-5` at the target side, and even a passing proposal is only an input to
Stage 2, which can refuse it (and usually will).

WHY IT IS ALLOWED TO EXIST.  A numerical search is the only way to discover a multi-angle
pose: nobody writes down a 118-square contact graph by hand.  The project's rule is not
"never compute with floats", it is "never *decide* with floats": so the search is isolated
behind a decimal fence, its output is a decimal string, and nothing downstream can see a
float even if it wanted to.

THE TARGETS.  `--rank` reads the delivered table with `Decimal` (no float) and ranks the
grid-tying rows of 101..1000: rows where the delivered side is exactly `k = ceil(sqrt n)`
and Nagamochi's proof does not cover them (`n = k^2 - 1` and `k^2 - 2` are proved optimal at
side `k` and are excluded).  The ranking is the *maximum* gain a beat could earn, `k/sqrt(n)
- 1`, and the brief's priority — `n = k^2 - 3` and `k^2 - 4` for k = 11..15, where beating the
integer side is still open — is applied as a tier above it.

THE SEARCH.  Four seeds (perturbed grid, strip stack, tilted wedge, random), a shrinkage
continuation (`k -> k - 5e-5 -> k - 1e-4`), Metropolis moves on translation and rotation, and
an energy of squared pairwise penetration plus a boundary-excess term.  Moves are incremental:
only the moved square's row of the pairwise matrix is recomputed.

USAGE
    python3 scripts/proposal_anneal.py --rank
    python3 scripts/proposal_anneal.py --budget 6 --seeds 4 --out workspace/push/anneal.jsonl
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from decimal import Decimal

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

SUBMISSION = os.path.join(ROOT, "workspace/submission/submission.csv")
TARGETS = os.path.join(ROOT, "workspace/push/anneal_targets.json")
OUT = os.path.join(ROOT, "workspace/push/anneal.jsonl")

#: a proposal is offered to Stage 2 only below this penetration and at this side
PASS_PEN = 1e-5
SHRINK = 1e-4
#: the brief's priority rows (k = 11..15, deficits 3 and 4)
TIER_A_K = (11, 12, 13, 14, 15)
TIER_A_R = (3, 4)
#: Nagamochi's proved rows: no side below k exists, so they are not targets
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
    """The tiered target list: the brief's priority rows first, then the largest headroom."""
    deliv = load_delivered()
    seen, tier_a, rest = set(), [], []
    for n in range(101, 1001):
        k = math.isqrt(n)
        if k * k < n:
            k += 1
        r = k * k - n
        if r < 1 or r in PROVED_R or r > 12:
            continue
        if abs(deliv[n] - k) >= Decimal("1e-8"):
            continue                      # not a grid tie: a beat already exists
        gain = Decimal(k) / Decimal(n).sqrt() - 1
        rec = {"n": n, "k": k, "r": r, "delivered": str(deliv[n]),
               "max_gain": str(gain.quantize(Decimal("1e-9")))}
        seen.add(n)
        if k in TIER_A_K and r in TIER_A_R:
            rec["tier"] = "A"
            tier_a.append(rec)
        else:
            rec["tier"] = "B"
            rest.append(rec)
    tier_a.sort(key=lambda r: (-Decimal(r["max_gain"]), r["n"]))
    rest.sort(key=lambda r: (-Decimal(r["max_gain"]), r["n"]))
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


# --------------------------------------------------------------------- seeds
def seed_grid(n, k, rng):
    """A k x k grid with `k^2 - n` cells removed, jittered."""
    cells = [(i + 0.5, j + 0.5) for j in range(k) for i in range(k)]
    rng.shuffle(cells)
    keep = cells[:n]
    x = np.array([c[0] for c in keep]) + rng.normal(0, 0.002, n)
    y = np.array([c[1] for c in keep]) + rng.normal(0, 0.002, n)
    return x, y, np.zeros(n)


def seed_strip(n, k, rng):
    """Rows of `k` and `k-1` with the short rows centred, plus a tilt on the last row."""
    rows = []
    left = n
    counts = []
    while left > 0:
        c = min(k, left)
        counts.append(c)
        left -= c
    x, y, a = [], [], []
    for j, c in enumerate(counts):
        if j == len(counts) - 1 and c > 1:
            ang = rng.uniform(0.02, 0.12) * (1 if rng.random() < 0.5 else -1)
        else:
            ang = 0.0
        for i in range(c):
            x.append((k - c) / 2 + i + 0.5)
            y.append(j + 0.5)
            a.append(ang)
    return np.array(x), np.array(y), np.array(a)


def seed_wedge(n, k, rng):
    """A 45-degree block anchored at the origin, axis cells outside its bbox, random fill."""
    b = max(2, int((k - 0.5) / math.sqrt(2)))
    half = math.sqrt(2) / 2.0
    x, y, a = [], [], []
    for j in range(b):
        for i in range(b):
            u, v = i - (b - 1) / 2.0, j - (b - 1) / 2.0
            x.append((u - v) * half + b * half)
            y.append((u + v) * half + b * half)
            a.append(math.pi / 4.0)
    span = b * math.sqrt(2.0)
    filled = len(x)
    for j in range(k):
        for i in range(k):
            if filled >= n:
                break
            if i + 1 <= span and j + 1 <= span:
                continue                            # inside the block's bbox
            x.append(i + 0.5)
            y.append(j + 0.5)
            a.append(0.0)
            filled += 1
        if filled >= n:
            break
    while filled < n:
        x.append(rng.uniform(0, k))
        y.append(rng.uniform(0, k))
        a.append(0.0)
        filled += 1
    return np.array(x[:n]), np.array(y[:n]), np.array(a[:n])


def seed_random(n, k, rng):
    return rng.uniform(0, k, n), rng.uniform(0, k, n), rng.uniform(-0.2, 0.2, n)


SEEDS = {"grid": seed_grid, "strip": seed_strip, "wedge": seed_wedge, "random": seed_random}


# --------------------------------------------------------------------- energy
def half_extent(c, s, qx, qy):
    """Half the projection of the unit square (frame c, s) on the unit axis (qx, qy)."""
    return (np.abs(c * qx + s * qy) + np.abs(c * qy - s * qx)) / 2.0


def pen_row(i, x, y, c, s):
    """Penetration of square `i` against every other square (positive = overlap).

    Four axes: the two edges of `i` and the two of `j`.  On `i`'s own axes its half-extent
    is exactly 1/2; on `j`'s axes it must be projected like any other square.
    """
    dx = x - x[i]
    dy = y - y[i]
    best = np.full(len(x), np.inf)
    for qx, qy in ((c[i], s[i]), (-s[i], c[i])):
        proj = dx * qx + dy * qy
        np.minimum(best, 0.5 + half_extent(c, s, qx, qy) - np.abs(proj), out=best)
    for qx, qy in ((c, s), (-s, c)):
        proj = dx * qx + dy * qy
        hi = half_extent(c[i], s[i], qx, qy)
        np.minimum(best, hi + half_extent(c, s, qx, qy) - np.abs(proj), out=best)
    best[i] = -np.inf
    return best


def row_term(i, x, y, c, s, L):
    """Square `i`'s own contribution: squared penetrations plus the boundary excess."""
    p = np.maximum(pen_row(i, x, y, c, s), 0.0)
    hi = half_extent(c[i], s[i], 1.0, 0.0)
    hj = half_extent(c[i], s[i], 0.0, 1.0)
    out = (max(0.0, hi - x[i]) + max(0.0, x[i] + hi - L)
           + max(0.0, hj - y[i]) + max(0.0, y[i] + hj - L))
    return float(np.dot(p, p)) + 8.0 * out * out


def worst_pen(x, y, c, s):
    """The largest pairwise penetration in the pose, and the box excess."""
    worst = 0.0
    for i in range(len(x)):
        p = float(np.max(pen_row(i, x, y, c, s)))
        if p > worst:
            worst = p
    return worst


def extent(x, y, c, s):
    """The pose's bounding-box side (the container it needs)."""
    hx = half_extent(c, s, 1.0, 0.0)
    hy = half_extent(c, s, 0.0, 1.0)
    return max(float(np.max(x + hx) - np.min(x - hx)),
               float(np.max(y + hy) - np.min(y - hy)))


# ---------------------------------------------------------------- the annealer
def anneal(n, k, seed_name, budget_s, rng):
    """Shrink from side `k` to `k - SHRINK`, annealing, then quench; return the best pose.

    Three annealed stages (`k`, `k - SHRINK/2`, `k - SHRINK`) plus a quench at the final
    side: the shrink is the point of the exercise, because a pose that is legal at `k` has to
    be *rearranged*, not just nudged, to fit at `k - 1e-4`.
    """
    x, y, a = SEEDS[seed_name](n, k, rng)
    c, s = np.cos(a).copy(), np.sin(a).copy()
    x, y = clamp_pose(x, y, c, s, k)
    Ls = [k, k - 0.5 * SHRINK, k - SHRINK]
    slice_s = budget_s / (len(Ls) + 1)
    best = None
    for si, L in enumerate(Ls + [k - SHRINK]):
        x, y = clamp_pose(x, y, c, s, L)
        t1 = time.time() + slice_s
        steps = 0
        T0 = (0.0002, 0.002, 0.0003, 0.0)[si]
        while time.time() < t1:
            steps += 1
            i = int(rng.integers(0, n))
            ox, oy, oc, os_ = x[i], y[i], c[i], s[i]
            e_old = row_term(i, x, y, c, s, L)
            sc = 0.05 * max(0.0, 1.0 - steps / 2500.0) + 0.001
            if rng.random() < 0.25:
                x[i] += rng.normal(0, sc)
                y[i] += rng.normal(0, sc)
            else:
                ang = math.atan2(s[i], c[i]) + rng.normal(0, 0.3 * sc)
                c[i], s[i] = math.cos(ang), math.sin(ang)
            e_new = row_term(i, x, y, c, s, L)
            if True:                         # the container is a container in every slice
                hxx = (abs(c[i]) + abs(s[i])) / 2.0
                if (x[i] - hxx < -1e-12 or x[i] + hxx > L + 1e-12
                        or y[i] - hxx < -1e-12 or y[i] + hxx > L + 1e-12):
                    e_new = np.inf
            T = T0 * max(0.0, 1.0 - steps / 2500.0)
            if e_new > e_old and (T <= 1e-12 or rng.random() >= math.exp((e_old - e_new) / T)):
                x[i], y[i], c[i], s[i] = ox, oy, oc, os_
            hxx = (abs(c[i]) + abs(s[i])) / 2.0          # containment after every move
            x[i] = min(max(x[i], hxx), L - hxx)
            y[i] = min(max(y[i], hxx), L - hxx)
        w = worst_pen(x, y, c, s)
        if si == len(Ls) and (best is None or w < best["pen"]):
            best = {"L": L, "pen": w, "x": x.copy(), "y": y.copy(),
                    "c": c.copy(), "s": s.copy(), "seed": seed_name}
    return best


def clamp_pose(x, y, c, s, L):
    """Project a pose into `[0, L]^2` in place (the container is not negotiable)."""
    h = (np.abs(c) + np.abs(s)) / 2.0
    ok = h <= L / 2.0
    np.copyto(x, np.where(ok, np.clip(x, h, L - h), x))
    np.copyto(y, np.where(ok, np.clip(y, h, L - h), y))
    return x, y


def normalise(best, n):
    """Re-anchor the pose at the bbox corner and report its side and worst penetration."""
    x, y, c, s = best["x"], best["y"], best["c"], best["s"]
    hx = half_extent(c, s, 1.0, 0.0)
    hy = half_extent(c, s, 0.0, 1.0)
    lo_x = float(np.min(x - hx))
    lo_y = float(np.min(y - hy))
    side = extent(x, y, c, s)
    return x - lo_x, y - lo_y, np.arctan2(s, c), side, worst_pen(x - lo_x, y - lo_y, c, s)


def emit(n, rec, x, y, a, side, pen, target_L, out):
    """Write one proposal as decimal text (17 significant digits), with its residual."""
    cells = [{"x": format(float(x[i]), ".17g"), "y": format(float(y[i]), ".17g"),
              "a": format(float(a[i]), ".17g")} for i in range(n)]
    rec = {"proposal": True, "n": n, "k": rec["k"], "r": rec["r"], "rank": rec["rank"],
           "tier": rec["tier"], "target_L": format(float(target_L), ".17g"),
           "side": format(float(side), ".17g"), "pen": format(float(pen), ".17g"),
           "qualifies": bool(pen < PASS_PEN and side <= target_L + 1e-9),
           "cells": cells}
    out.write(json.dumps(rec) + "\n")
    out.flush()


def main() -> int:
    argv = sys.argv
    if "--rank" in argv:
        return do_rank()
    budget = float(argv[argv.index("--budget") + 1]) if "--budget" in argv else 4.0
    seeds = int(argv[argv.index("--seeds") + 1]) if "--seeds" in argv else 4
    path = argv[argv.index("--out") + 1] if "--out" in argv else OUT
    only = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None
    with open(TARGETS) as f:
        ranked = json.load(f)
    if only:
        ranked = [r for r in ranked if str(r["n"]) in only]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rng = np.random.default_rng(20261126)
    with open(path, "w") as out:
        for rec in ranked:
            n, k = rec["n"], rec["k"]
            target_L = k - SHRINK
            t0 = time.time()
            bestall = None
            names = list(SEEDS)[:seeds]
            for name in names:
                best = anneal(n, k, name, budget, rng)
                x, y, a, side, pen = normalise(best, n)
                if bestall is None or pen < bestall[4]:
                    bestall = (x, y, a, side, pen, name)
                print(f"  n={n} seed={name:6s} pen={pen:.3e} side={side:.9f} "
                      f"({time.time() - t0:.1f}s)", flush=True)
            x, y, a, side, pen, name = bestall
            emit(n, rec, x, y, a, side, pen, target_L, out)
            print(f"n={n} k={k} r={rec['r']} tier={rec['tier']}: best {name} pen={pen:.3e} "
                  f"side={side:.9f} target {target_L:.9f} qualifies={pen < PASS_PEN}",
                  flush=True)
    print(f"proposals: {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
