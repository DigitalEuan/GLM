#!/usr/bin/env python3
r"""lorentz_lift.py — Run 7 prototype: the Lorentzian lift, compiled for
square packing.

Source: glm-repo/src/lean/RequestProject/GLM/LorentzianLift.lean (Phase 182,
verified, 0 sorry) + studies/LORENTZIAN_LIFT_STUDY.md. What GLM proved:

  lift        L(x) = (x, (1-|x|^2)/2, (1+|x|^2)/2)  onto the light cone;
  linearize   <L x, r_lambda> = 1 - |x - lambda|^2 / 2   (root r = L l - w,
              w = (0,-1,1) Weyl): nearest-site decisions become LINEAR scores;
  tie_iff     a tie (x equidistant from lambda, mu) is exactly
              <L x, r_lambda - r_mu> = 0  — a MIRROR; the reflection in it
              fixes the tied point and swaps the candidates;
  reflection_invariant_tie   NO reflection-invariant rule can break a tie
              (every function of the geometry is such a rule);
  context_break   a tie is broken exactly by a second point y that is not
              itself equidistant — information from OUTSIDE the geometry.
  (study verdict: summing scores over further readings resolves ties,
              0 wrong answers.)

Compilation to packing (this file). Our Run-6 engines are all
reflection-invariant local dynamics — the Lean theorem PREDICTS they jam
at every tie (a jammed wall is a multi-way tie). The lift prescribes the
cure we never tried:

  C1  LINEAR SITE SCORING: candidate sites come from a declared MOTIF
      (per project directive: the 45-degree family ONLY — no angle
      search): grid sites (axis-aligned) UNION diamond sites (the 45
      tiling lattice, spacing sqrt(2)). Square i's site score is
      1 - |c_i - site|^2 / 2 (the lift score): nearest site wins.
  C2  CERTIFIED TIES + CONTEXT LOOKAHEAD: when a square's two nearest
      FREE sites are equidistant (within tie_tol), the choice is a tie;
      it is NOT decided by geometry (theorem) — it is decided by the
      CONTEXT: try both, relax the whole configuration briefly, keep
      whichever gives the lower GLOBAL objective (the rest of the
      configuration is the second reading y).
  C3  BISECTOR-REFLECTION LONG JUMPS: at a certified tie the lift's
      reflection maps basin A to basin B (fixes the tied point, swaps
      candidates) — implemented as an annealing move: reflect the square
      through the perpendicular bisector of its two nearest sites (a
      jump no local dynamics can make).
  C4  ESCALATION LADDER (DeepHoleEscalation): rounds of
      assign -> snap -> relax; if still jammed, escalate: widen the
      context (more lookahead), re-assign.

Everything ends in packlib verification (tol 1e-9), as always: a find is
a state with max pairwise overlap < 1e-10 and zero container violation
that then passes packlib.finalize + packlib.verify.

Probes: the open archetypes (6, 12, 13 — the smallest open LOW-band
puzzles, survey says grid-optimal-known) and two roomy MID targets
(695, 803), plus a sanity container (13 @ 4.2 — comfortably feasible;
the engine must FIND it or it is broken).
"""
import json
import math
import os
import sys
from math import ceil, sqrt

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import packlib as P
from cent_engines import (pen_matrix, out_amounts, hw, objective,
                           engine_p11_piezo, seed_local)

PUSH = "/home/z/my-project/workspace/push"
OUT = os.path.join(PUSH, "lorentz_results.json")
TIE_TOL = 0.12          # sites closer than this in score-distance = a tie
S2 = math.sqrt(2.0)
S2H = S2 / 2.0          # sqrt(2)/2


# ------------------------------------------------------------- motifs (45°)
def build_grid_sites(n, L):
    k = int(ceil(sqrt(n)))
    sc = L / k
    sites = []
    for i in range(k * k):
        sites.append((((i % k) + 0.5) * sc, ((i // k) + 0.5) * sc, 0))
    return sites


def build_diamond_sites(L):
    """the 45-degree tiling lattice: centers a*u + b*v,
    u = (s2/2, s2/2), v = (-s2/2, s2/2); keep sites whose bounding box
    (side sqrt(2)) fits in [0, L]^2."""
    sites = []
    amax = int(L / S2H) + 2
    for a in range(-amax, amax + 1):
        for b in range(-amax, amax + 1):
            x = (a - b) * S2H
            y = (a + b) * S2H
            if S2H - 1e-12 <= x <= L - S2H + 1e-12 and S2H - 1e-12 <= y <= L - S2H + 1e-12:
                sites.append((x, y, 1))   # family 1 = diamond (45 deg)
    return sites


# ------------------------------------------------------------- C1: scoring
def site_scores(c, sites):
    """lift scores 1 - |c - s|^2 / 2 for one square against all sites."""
    out = np.empty(len(sites))
    for j, (sx, sy, fam) in enumerate(sites):
        dx, dy = c[0] - sx, c[1] - sy
        out[j] = 1.0 - (dx * dx + dy * dy) / 2.0
    return out


def assign_all(X, Y, TH, sites, n):
    """exclusive greedy assignment, most-tied first (C1 + C2 structure).
    Returns list of site indices per square, and the list of squares that
    ended in a certified tie (top-2 within TIE_TOL)."""
    free = set(range(len(sites)))
    order = []
    info = []
    for i in range(n):
        sc = site_scores((X[i], Y[i]), sites)
        order.append(i)
        info.append(sc)
    # most-tied first: smallest margin between best and second-best among FREE
    def margin(i):
        sc = info[i]
        idx = sorted(free, key=lambda j: -sc[j])
        return sc[idx[0]] - sc[idx[1]]
    sqs = sorted(order, key=margin)
    choice = [None] * n
    ties = []
    for i in sqs:
        sc = info[i]
        idx = sorted(free, key=lambda j: -sc[j])
        j0, j1 = idx[0], idx[1]
        if sc[j0] - sc[j1] < TIE_TOL:
            ties.append((i, j0, j1, sc[j0] - sc[j1]))
        choice[i] = j0
        free.discard(j0)
    return choice, ties


def snap(X, Y, TH, choice, sites, n):
    for i in range(n):
        sx, sy, fam = sites[choice[i]]
        X[i], Y[i] = sx, sy
        TH[i] = (math.pi / 4.0) if fam == 1 else 0.0
    return X, Y, TH


def global_obj(X, Y, TH, L):
    Pp, _ = pen_matrix(X, Y, TH)
    out = out_amounts(X, Y, hw(TH), L)
    return objective(Pp, out)


# ------------------------------------------------------------- C2: context
def context_break(X, Y, TH, L, rng, ties, choice, sites, n, max_look=3):
    """the context rule: for each certified tie (up to max_look), try both
    candidate sites; the REST of the configuration (the second reading y)
    decides — keep whichever choice gives the lower global objective after
    a brief relax."""
    resolved = 0
    for (i, j0, j1, m) in ties[:max_look]:
        if j0 not in [choice[i]] and j1 not in [choice[i]]:
            continue
        # current choice is one of them; evaluate the swap
        cur = choice[i]
        alt = j1 if cur == j0 else j0
        if alt >= len(sites):
            continue
        base_obj = global_obj(X, Y, TH, L)
        X2, Y2, T2 = X.copy(), Y.copy(), TH.copy()
        sx, sy, fam = sites[alt]
        X2[i], Y2[i] = sx, sy
        T2[i] = (math.pi / 4.0) if fam == 1 else 0.0
        o2, X2, Y2, T2 = engine_p11_piezo(X2, Y2, T2, L, rng, iters=12, eta=0.15)
        if o2 < base_obj:
            X[:], Y[:], TH[:] = X2, Y2, T2
            choice[i] = alt
            resolved += 1
    return resolved


# ------------------------------------------------------------- C3: reflection
def bisector_reflection_moves(X, Y, TH, L, rng, sites, n, iters):
    """annealing with the lift's reflection move: pick a square, find its
    two nearest sites; if near-tied, reflect its position through the
    perpendicular bisector of (site_a, site_b) — the lift's mirror swap.
    Accept by Metropolis; mixed with tiny jitter.
    Pure: the caller's arrays are never modified (copy at entry)."""
    X, Y = X.copy(), Y.copy()
    best = (global_obj(X, Y, TH, L), X.copy(), Y.copy(), TH.copy())
    obj = best[0]
    for it in range(iters):
        T = 0.004 * (1 - it / iters) + 1e-6
        i = rng.randint(n)
        sc = site_scores((X[i], Y[i]), sites)
        idx = np.argsort(-sc)[:2]
        ja, jb = int(idx[0]), int(idx[1])
        (ax, ay, _), (bx, by, _) = sites[ja], sites[jb]
        mx, my = (ax + bx) / 2.0, (ay + by) / 2.0   # midpoint of the two sites
        dx, dy = bx - ax, by - ay                   # bisector normal
        dlen = math.hypot(dx, dy) or 1.0
        nx, ny = dx / dlen, dy / dlen
        # reflect c_i through the bisector line (midpoint, normal n):
        # p' = p - 2 ((p-m).n) n
        px, py = X[i], Y[i]
        s = (px - mx) * nx + (py - my) * ny
        Xn, Yn = X.copy(), Y.copy()
        Xn[i] = px - 2 * s * nx
        Yn[i] = py - 2 * s * ny
        objn = global_obj(Xn, Yn, TH, L)
        if objn < obj or rng.uniform() < math.exp(-(objn - obj) / max(T, 1e-9)):
            X[:], Y[:] = Xn, Yn
            obj = objn
        # jitter channel
        if it % 3 == 0:
            j = rng.randint(n)
            X[j] += rng.normal(0, T); Y[j] += rng.normal(0, T)
            obj = global_obj(X, Y, TH, L)
        if obj < best[0]:
            best = (obj, X.copy(), Y.copy(), TH.copy())
    return best


# ------------------------------------------------------------- engine (C4)
def engine_lorentz(X, Y, TH, L, rng, rounds=3):
    """the escalation ladder: assign (C1) -> snap -> context-break ties (C2)
    -> relax -> bisector-reflection anneal (C3); escalate per round."""
    n = len(X)
    sites = build_grid_sites(n, L) + build_diamond_sites(L)
    best = None
    for rnd in range(rounds):
        choice, ties = assign_all(X, Y, TH, sites, n)
        X, Y, TH = snap(X, Y, TH, choice, sites, n)
        if ties:
            context_break(X, Y, TH, L, rng, ties, choice, sites, n,
                          max_look=3 + rnd)     # escalate: wider context
        big = n >= 100
        o, X, Y, TH = engine_p11_piezo(X, Y, TH, L, rng,
                                       iters=30 if big else 60, eta=0.15)
        b = bisector_reflection_moves(X, Y, TH, L, rng, sites, n,
                                      iters=(60 + 30 * rnd) if big
                                      else (120 + 60 * rnd))
        if b[0] < o:
            o, X, Y, TH = b
        o2, X2, Y2, T2 = engine_p11_piezo(X, Y, TH, L, rng,
                                          iters=40 if big else 80, eta=0.1)
        if o2 < o:
            o, X, Y, TH = o2, X2, Y2, T2
        if best is None or o < best[0]:
            best = (o, X.copy(), Y.copy(), TH.copy())
    if best is not None:
        fres = global_obj(best[1], best[2], best[3], L)
        if abs(fres - best[0]) > 1e-9:
            print(f"[engine_lorentz] INCONSISTENT RETURN: claim={best[0]:.6e} "
                  f"fresh={fres:.6e} rounds={rounds}")
    return best


def polish(st, L, rng, n):
    """terminal pure relaxation (no thermal layer): damped piezo descent
    on the engine's best state. Drives residual overlaps to zero when the
    basin contains a feasible configuration."""
    X = np.array([q[0] for q in st]); Y = np.array([q[1] for q in st])
    TH = np.array([q[2] for q in st])
    iters = 500 if n < 100 else 240
    o, X, Y, TH = engine_p11_piezo(X, Y, TH, L, rng, iters=iters,
                                   eta=0.05, T0=0.0)
    return (o, X, Y, TH)


def run_probe(n, L, seed, rounds=3):
    rng = np.random.RandomState(seed)
    X, Y, TH = seed_local(n, L, seed)
    obj, bX, bY, bTH = engine_lorentz(X, Y, TH, L, rng, rounds=rounds)
    o2, pX, pY, pTH = polish([(float(bX[i]), float(bY[i]), float(bTH[i]))
                              for i in range(n)], L, rng, n)
    if o2 < obj:
        obj, bX, bY, bTH = o2, pX, pY, pTH
    stf = [(float(bX[i]), float(bY[i]), float(bTH[i]) % (math.pi / 2))
           for i in range(n)]
    r = P.verify(stf, tol=1e-9)
    worst_out = float(np.max(out_amounts(bX, bY, hw(bTH), L)))
    find = None
    if r["worst_pen"] <= 1e-10 and worst_out <= 1e-10 and r["ok"]:
        stf2, r2 = P.finalize(stf, gap=2e-9)
        if r2["ok"]:
            find = {"n": n, "L": L, "seed": seed, "state": stf2,
                    "verified_L": round(r2["L"], 12)}
    return {"n": n, "L": round(L, 6), "seed": seed, "rounds": rounds,
            "obj": round(float(obj), 12),
            "max_pen": round(float(r["worst_pen"]), 12),
            "max_out": round(worst_out, 12)}, find


def main():
    probes = [
        ("sanity", 13, 4.2),          # comfortably feasible — must FIND
        ("open", 6, 2.998), ("open", 6, 2.98),
        ("open", 12, 3.998), ("open", 12, 3.98),
        ("open", 13, 3.998), ("open", 13, 3.98),
        ("open", 695, 26.998), ("open", 695, 26.98),
        ("open", 803, 28.998), ("open", 803, 28.98),
    ]
    results, finds = [], []
    for tag, n, L in probes:
        r, f = run_probe(n, round(L, 6), 7919 * n + 1,
                         rounds=3 if n < 100 else 2)
        r["tag"] = tag
        results.append(r)
        if f:
            finds.append(f)
        print(f"  [{tag}] n={n} L={L}: obj={r['obj']:.3e} pen={r['max_pen']:.2e} "
              f"out={r['max_out']:.2e}" + ("  FIND" if f else ""))
    json.dump({"probes": results, "finds": finds}, open(OUT, "w"), indent=1)
    print(f"[lorentz] {len(finds)} finds -> {OUT}")


if __name__ == "__main__":
    main()
