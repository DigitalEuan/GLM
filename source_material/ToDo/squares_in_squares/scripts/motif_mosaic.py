#!/usr/bin/env python3
r"""motif_mosaic.py — the multi-motif composer (GLM round, 15 November 2026).

The owner's question: can a *motif* or *multi-motif* arrangement gain even a
slight advantage on the current score, without importing anyone else's data?

What is already in this tree, and why this family is not one of them:

* `theta_family.py` — one p x p block at angle θ centred in the container with
  FOUR corner staircases (n = p² + 2a(a+1));
* `gobel2.py` — the 45° diamond core with four corner staircases, the
  G(a1, a2, b, c) family;
* `gobel5/6.py` — tilted bands (one, then two) with greedy wall fills;
* `mixed_field.py` — a 45° block and a 30° block stacked on the diagonal with
  split staircases.

The family here is a **two-corner mosaic**: one p x p block at angle θ, held
between TWO opposite corner staircases of depth a along the main diagonal, and
the remaining space filled by an axis-aligned lattice motif wherever a unit
square still fits.  The block touches the two staircases' frontiers, so the
container side is not a free parameter:

    frontier of a depth-a staircase:  x + y = a + 1  (and the mirrored one)
    support of the θ-rotated p-block along the diagonal:  p·cos θ / √2
    =>  s = a + 1 + p·cos θ

which at θ = 45° is exactly Göbel's a + 1 + p/√2, and for θ < 45° is larger.
The interesting question is what the *other* constraint allows once the lattice
fill is counted: the block's sideways extent is (p/2)(cos θ + sin θ), so for
θ > 45° the side staircases bite before the diagonal does.  Every candidate is
therefore built, filled, and handed to `packlib.verify`; the design value of s
is never trusted.

A candidate is reported only when its verified L beats the current submission
by more than 1e-9, and it is written out only after `packlib.finalize` passes.

Result (measured 15 November 2026): the family is DOMINATED.  The support of a
theta-rotated p-block along either diagonal normal is p*max(cos, sin)/sqrt2, the
same for both normals, so both diagonal contact laws read `s >= a + 1 + p*M` and
`s >= b + 1 + p*M` with M = max(cos t, sin t): the deeper staircase pair binds
both, and s is minimised at theta = 45 degrees with equal depths -- which is
Göbel exactly.  Swept over p <= 30, a, b <= 14 and eleven angles, no design beats
the current submission and no verified packing does either (0 survivors,
0 wins).  Any gain in this space has to come from the BAND mosaic, where the
band angle is continuous rather than a symmetry of the block.

Usage:
    python3 scripts/motif_mosaic.py --domination
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


# --------------------------------------------------------------- geometry
def _pen_array(cand, X, Y, T) -> np.ndarray:
    """min over the four edge-normal axes of (ext_i + ext_j - |d.axis|), per pair."""
    xc, yc, tc = cand
    e = 0.5 * (np.abs(np.cos(T)) + np.abs(np.sin(T)))
    ec = 0.5 * (abs(math.cos(tc)) + abs(math.sin(tc)))
    axes = []
    c0, s0 = math.cos(tc), math.sin(tc)
    axes.append((c0, s0, e))
    axes.append((-s0, c0, e))
    cT, sT = np.cos(T), np.sin(T)
    axes.append((cT, sT, None))            # per-placed axes, two of them
    axes.append((-sT, cT, None))
    out = None
    for k, (ax, ay, _e) in enumerate(axes):
        if k < 2:
            d = np.abs((X - xc) * ax + (Y - yc) * ay)
            pen = ec + e - d
        else:
            d = np.abs((X - xc) * ax + (Y - yc) * ay)
            pen = ec + e - d
        out = pen if out is None else np.minimum(out, pen)
    return out


def clear(placed, cand) -> bool:
    """True if the candidate overlaps none of the placed squares."""
    if not len(placed):
        return True
    X, Y, T = placed[:, 0], placed[:, 1], placed[:, 2]
    return float(np.max(_pen_array(cand, X, Y, T))) <= 0.0


# ------------------------------------------------------------- the motifs
def staircase(depth: int, corner: str, s: float):
    """A corner staircase of depth a: a(a+1)/2 unit squares against the corner."""
    out = []
    for i in range(depth):
        for j in range(depth - i):
            if corner == "ll":
                out.append((i + 0.5, j + 0.5, 0.0))
            elif corner == "ur":
                out.append((s - i - 0.5, s - j - 0.5, 0.0))
            elif corner == "lr":
                out.append((s - i - 0.5, j + 0.5, 0.0))
            else:                                     # upper left
                out.append((i + 0.5, s - j - 0.5, 0.0))
    return out


def block(p: int, theta: float, cx: float, cy: float):
    """A p x p block of unit squares at angle theta, centred at (cx, cy)."""
    c, s = math.cos(theta), math.sin(theta)
    out = []
    for i in range(p):
        for j in range(p):
            dx = (i - (p - 1) / 2.0)
            dy = (j - (p - 1) / 2.0)
            out.append((cx + dx * c - dy * s, cy + dx * s + dy * c, theta))
    return out


def side(p: int, theta: float, a: int, b: int) -> float:
    """The minimal container side for the mosaic, from its four contact laws.

    a = depth of the staircase pair on the (0,0)/(s,s) diagonal,
    b = depth of the pair on the (s,0)/(0,s) diagonal, block p x p at theta.
    """
    c, s = math.cos(theta), math.sin(theta)
    # The support of a theta-rotated p-block along EITHER diagonal normal is
    #   (p/2)(|cos t + sin t| + |cos t - sin t|) = p * max(cos t, sin t) / sqrt2,
    # the same for both normals (the square is 4-fold symmetric), so the two
    # diagonal contact laws are  s >= a + 1 + p*M  and  s >= b + 1 + p*M  with
    # M = max(cos t, sin t): the DEEPER staircase pair binds both, and the
    # minimum over theta sits at 45 degrees where M = 1/sqrt2.  That is the
    # domination result this file was written to test.
    M = max(c, s)
    return max(max(a, b) + 1 + p * M,  # block touches the deeper staircase pair
               p * (c + s),            # block stays inside the walls
               a + b + 2.0)            # the two staircase pairs do not collide


def build(p: int, a: int, b: int, theta: float, s: float | None = None,
          fill: bool = True, phases=(0.5, 0.25, 0.75)):
    """Assemble the mosaic and (optionally) fill every clear lattice cell."""
    if s is None:
        s = side(p, theta, a, b)
    state = staircase(a, "ll", s) + staircase(a, "ur", s)
    state += staircase(b, "lr", s) + staircase(b, "ul", s)
    state += block(p, theta, s / 2.0, s / 2.0)
    if fill:
        placed = np.array(state, dtype=float)
        k = int(math.ceil(s - 1e-9))
        for gx in range(k):
            for gy in range(k):
                for ph in phases:
                    cand = (gx + ph, gy + ph, 0.0)
                    if cand[0] + 0.5 > s + 1e-12 or cand[1] + 0.5 > s + 1e-12:
                        continue
                    if clear(placed, cand):
                        placed = np.vstack([placed, np.array(cand)])
                        break
        state = [(float(u), float(v), float(w)) for u, v, w in placed]
    return state, s


def verified(state):
    r = P.verify(state)
    return bool(r["ok"]), float(r["L"]), float(r["worst_pen"])


# ------------------------------------------------------------------- sweep
def table_L():
    by_n = P.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    return {n: P.verify(by_n[n])["L"] for n in range(1, 1001) if n in by_n
            and len(by_n[n]) == n}


def domination(p_max=30, a_max=14, angles=(20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70)):
    """The full generality test: every (p, a, b, theta) of this family vs the table.

    Prints the design survivors (a side below the current submission that also
    clears the area bound) and then the verified wins (finalize + verify).
    """
    tab = table_L()
    cands = {}
    for p in range(1, p_max + 1):
        for a in range(0, a_max + 1):
            for b in range(0, a_max + 1):
                for th_deg in angles:
                    th = math.radians(th_deg)
                    s = side(p, th, a, b)
                    n = p * p + a * (a + 1) + b * (b + 1)
                    if not (1 <= n <= 1000):
                        continue
                    if s < math.sqrt(n) - 1e-12:
                        continue
                    if n in tab and s < tab[n] - 1e-9:
                        if n not in cands or s < cands[n][0]:
                            cands[n] = (s, th_deg, p, a, b)
    print(f"design survivors: {len(cands)}")
    wins = []
    for n, (s, thd, p, a, b) in sorted(cands.items()):
        state, _ = build(p, a, b, math.radians(thd), s=s, fill=False)
        fin, r = P.finalize(state)
        if r["ok"] and r["L"] < tab[n] - 1e-9:
            wins.append({"n": n, "L_before": tab[n], "L_after": r["L"],
                         "theta_deg": thd, "p": p, "a": a, "b": b,
                         "state": [[float(u), float(v), float(w)] for u, v, w in fin]})
            print(f"  WIN n={n}: {tab[n]:.9f} -> {r['L']:.9f}")
    path = os.path.join(ROOT, "workspace/push/motif_mosaic_results.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"found": wins, "survivors": len(cands),
               "score_gain": sum((w["L_before"] - w["L_after"]) / math.sqrt(w["n"])
                                 for w in wins)}, open(path, "w"), indent=1)
    print(f"verified wins: {len(wins)}; wrote {path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domination", action="store_true")
    args = ap.parse_args()
    if args.domination:
        return domination()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
