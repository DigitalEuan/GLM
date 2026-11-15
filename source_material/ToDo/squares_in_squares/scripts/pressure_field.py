#!/usr/bin/env python3
r"""pressure_field.py — a container-pressure engine for Squares in Squares.

Added 15 November 2026 by the GLM round (the owner's question: can a cent
engine concept, rather than an import, move the score?).

Concept, as the cent compiler declares it
(`cent_compiler_v12/docs/PACKING_PRESSURE_SETTLING.md`, wheels W36/W37):

* W6 pressure / force — the container is a *pressure vessel*: its side L is the
  pressure variable, and closing the walls is the applied force;
* W5 force / energy — the field of pairwise penetrations is the elastic energy
  that resists the pressure (`E = sum max(0, penetration)^2`, the W36 objective)
  and the relaxation is its dissipation.

The two wheels are read here as one field law: each shrink of the container
raises the pressure, the field answers with a gradient on the *positions and
angles together* (a rotated square pushes back along a different direction than
an axis-aligned one, which is what makes the field more than a scalar), and the
arrangement settles into the nearest feasible configuration before the next
shrink.  Unlike the pressure-settling probe, this engine is allowed to rotate
and to move the container, and unlike the motif sweeps it does not assume a
family: it only needs a seed.

Every candidate is gated by the project's own authority: `packlib.finalize`
(2e-9 contact opening, 12-dp round trip) and `packlib.verify` (worst pairwise
penetration <= 0).  A candidate is reported only if its verified L is strictly
below the seed's L.

Usage:
    python3 scripts/pressure_field.py --control
    python3 scripts/pressure_field.py --campaign --top 40 --max-n 260
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
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import packlib as P                                      # noqa: E402


# ----------------------------------------------------------------- the field
def extents(th: np.ndarray) -> np.ndarray:
    """Half-width of a unit square at angle th, the same on both axes."""
    return 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))


def energy(state: np.ndarray, L: float, wall_weight: float = 1.0) -> float:
    """W36 objective at container side L: pair penetration + wall violation."""
    x, y, th = state[:, 0], state[:, 1], state[:, 2]
    n = len(state)
    e = extents(th)
    c, s = np.cos(th), np.sin(th)
    # wall violation: the container is [0, L]^2 (a translation of it is free)
    lo = np.minimum(x - e, 0.0)
    hi = np.maximum(x + e - L, 0.0)
    loy = np.minimum(y - e, 0.0)
    hiy = np.maximum(y + e - L, 0.0)
    wall = float(np.sum(lo ** 2 + hi ** 2 + loy ** 2 + hiy ** 2))
    if n < 2:
        return wall_weight * wall
    PU = np.stack([c, s], axis=1) @ np.stack([x, y], axis=0)      # axes of i
    PV = np.stack([-s, c], axis=1) @ np.stack([x, y], axis=0)
    Eu = 0.5 * (np.abs(np.outer(c, c) + np.outer(s, s))
                + np.abs(np.outer(-s, c) + np.outer(c, s)))
    dU = np.diag(PU)[:, None] - PU
    dV = np.diag(PV)[:, None] - PV
    fam0 = np.minimum(0.5 + Eu - np.abs(dU), 0.5 + Eu - np.abs(dV))
    fam1 = np.minimum(0.5 + Eu.T - np.abs(dU.T), 0.5 + Eu.T - np.abs(dV.T))
    pen = np.minimum(fam0, fam1)
    iu = np.triu_indices(n, k=1)
    over = np.maximum(0.0, pen[iu])
    return float(np.dot(over, over)) + wall_weight * wall


def gradient(state: np.ndarray, L: float, h: float = 1e-6,
             wall_weight: float = 1.0) -> np.ndarray:
    """Central differences on (x, y, theta) — the field's answer to the pressure."""
    g = np.zeros_like(state)
    for k in range(3):
        sp = state.copy()
        sm = state.copy()
        sp[:, k] += h
        sm[:, k] -= h
        g[:, k] = (energy(sp, L, wall_weight) - energy(sm, L, wall_weight)) / (2 * h)
    return g


def relax(state: np.ndarray, L: float, steps: int = 60, lr: float = 0.05,
          momentum: float = 0.6, wall_weight: float = 1.0) -> np.ndarray:
    """Settle the arrangement at side L (dissipation of the W5 energy)."""
    st = state.copy()
    vel = np.zeros_like(st)
    lr_k = lr * max(0.2, min(1.0, L / 20.0))
    for _ in range(steps):
        g = gradient(st, L, wall_weight=wall_weight)
        vel = momentum * vel - lr_k * g
        vel[:, :2] = np.clip(vel[:, :2], -0.25 * max(L, 1.0), 0.25 * max(L, 1.0))
        vel[:, 2] = np.clip(vel[:, 2], -0.05, 0.05)
        st = st + vel
        # keep the arrangement near the container without clipping its shape
        st[:, :2] -= np.median(st[:, :2], axis=0) - L / 2.0
    return st


def feasible(state: np.ndarray) -> tuple[bool, float, float]:
    """(ok, worst pair penetration, extent L) under the project's own verifier."""
    r = P.verify([(float(a), float(b), float(c)) for a, b, c in state])
    return bool(r["ok"]), float(r["worst_pen"]), float(r["L"])


# --------------------------------------------------------------- the engine
def compact(seed, L0: float, shrink: float = 0.01, tries: int = 400,
            steps: int = 40, verbose: bool = False) -> tuple[np.ndarray, float]:
    """Close the walls while the field holds the arrangement feasible.

    Returns the best *verified* state and its L (never worse than the seed's).
    """
    st = np.array(seed, dtype=float)
    L = L0
    best_state, best_L = st.copy(), L0
    stale = 0
    for t in range(tries):
        target = L * (1.0 - shrink)
        cand = relax(st, target, steps=steps)
        ok, worst, ext = feasible(cand)
        if ok and ext <= target * (1.0 + 0.02):
            fin, r = P.finalize([(a, b, c) for a, b, c in cand])
            if r["ok"]:
                st = np.array(fin, dtype=float)
                L = float(r["L"])
                if L < best_L - 1e-12:
                    best_state, best_L, stale = st.copy(), L, 0
                else:
                    stale += 1
        else:
            stale += 1
            # a rejected shrink: back off, settle harder, and let the field
            # jitter (a jammed arrangement cannot cross to another class
            # without it -- `soft_relax.py` calls this the pass-through channel)
            cand = relax(st, L, steps=steps * 2)
            rng = np.random.default_rng(t)
            cand[:, 2] += rng.normal(0.0, 0.02, len(cand))
            cand[:, :2] += rng.normal(0.0, 0.0005 * max(L, 1.0), (len(cand), 2))
            ok, worst, ext = feasible(cand)
            if ok:
                st = np.array(P.finalize([(a, b, c) for a, b, c in cand])[0], dtype=float)
        if verbose and t % 25 == 0:
            print(f"    step {t}: L={L:.6f} best={best_L:.6f} stale={stale}")
        if stale > 60:
            break
    return best_state, best_L


# ------------------------------------------------------------------ seeding
def motif_seed(n: int, L: float) -> np.ndarray:
    """A field-neutral seed: the grid, then squeezed into side L."""
    st = []
    k = int(math.ceil(math.sqrt(n)))
    for i in range(n):
        st.append((0.5 + (i % k), 0.5 + (i // k), 0.0))
    a = np.array(st, dtype=float)
    a[:, :2] = (a[:, :2] - 0.5) * (L / k) + L / 2.0
    return a


def state_seed(rows) -> np.ndarray:
    return np.array([(x, y, t) for x, y, t in rows], dtype=float)


# ----------------------------------------------------------------- controls
CONTROLS = [
    # (n, known best L, grid L, tolerance) -- the engine must reach the known value
    (5, 2.70710678, 3.0, 2e-3),
    (11, 3.87708359, 4.0, 2e-3),
    (17, 4.67553009, 5.0, 2e-3),
    (19, 4.88561808, 5.0, 2e-3),
    (26, 5.62132034, 6.0, 2e-3),
]


def run_controls() -> int:
    print("controls — the engine seeds from the grid and must reach the known side")
    bad = 0
    for n, known, grid, tol in CONTROLS:
        t0 = time.time()
        seed = motif_seed(n, grid)
        st, L = compact(seed, grid, shrink=0.005, tries=260, steps=40)
        ok = abs(L - known) <= tol or L <= known + tol
        print(f"  n={n:<4} grid {grid:.4f}  known {known:.5f}  reached {L:.5f}  "
              f"{'PASS' if ok else 'MISS'}  ({time.time()-t0:.1f} s)")
        bad += 0 if ok else 1
    print(f"controls: {len(CONTROLS)-bad} of {len(CONTROLS)} passed")
    return 0 if bad == 0 else 1


# ------------------------------------------------------------------ campaign
def run_campaign(top: int, max_n: int, shuffle_tries: int) -> int:
    sub = P.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    rows = []
    for n in range(2, max_n + 1):
        if n not in sub or len(sub[n]) != n:
            continue
        r = P.verify(sub[n])
        L = r["L"]
        rows.append((L / math.sqrt(n) - 1.0, n, L, r["worst_pen"]))
    rows.sort(reverse=True)
    targets = rows[:top]
    print(f"campaign: {len(targets)} puzzles, the largest relative excess with n <= {max_n}")
    found = []
    t0 = time.time()
    for excess, n, L, _wp in targets:
        st0 = state_seed(sub[n])
        best_state, best_L = st0, L
        # seed 1: the frontier state itself, pressed
        st, L1 = compact(st0, L, shrink=0.004, tries=200, steps=40)
        if L1 < best_L - 1e-12:
            best_state, best_L = st, L1
        # seed 2: the grid, squeezed to L (a different basin)
        if shuffle_tries:
            st, L2 = compact(motif_seed(n, L), L, shrink=0.004, tries=200, steps=40)
            if L2 < best_L - 1e-12:
                best_state, best_L = st, L2
        gain = (L - best_L) / math.sqrt(n)
        if L - best_L > 1e-12:
            found.append({"n": n, "L_before": L, "L_after": best_L, "gain": gain,
                          "state": [[float(a), float(b), float(c)] for a, b, c in best_state]})
        print(f"  n={n:<5} L {L:.9f} -> {best_L:.9f}  {'+' if gain > 0 else ''}{gain:+.2e}"
              f"  [{len(found)} found]  ({time.time()-t0:.0f} s)", flush=True)
    out = os.path.join(ROOT, "workspace/push/pressure_field_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({"found": found}, f, indent=1)
    total = sum(r["gain"] for r in found)
    print(f"\nfound {len(found)} improvement(s), score gain {total:.6f}; wrote {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--campaign", action="store_true")
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--max-n", type=int, default=260)
    ap.add_argument("--seeds", type=int, default=1)
    args = ap.parse_args()
    if args.control:
        return run_controls()
    if args.campaign:
        return run_campaign(args.top, args.max_n, args.seeds)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
