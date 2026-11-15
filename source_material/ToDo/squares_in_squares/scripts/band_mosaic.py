#!/usr/bin/env python3
r"""band_mosaic.py — the continuous-angle band mosaic (GLM round, 15 November 2026).

Why a band and not a block: the block mosaic is *dominated*.  Its two diagonal
contact laws share one support value (`p·max(cos, sin)/√2`), so the deeper
staircase pair binds both and the side is minimised at 45° — Göbel.  A band's
two diagonal supports are different numbers, so the band angle φ is a genuine
continuous parameter, and the side is a smooth max of four contact laws:

    band bounding box            s ≥ W·cos φ + H·sin φ        (along x)
                                 s ≥ W·sin φ + H·cos φ        (along y)
    a-staircase pair (0,0)/(s,s) s ≥ a + 1 + [W(c+s) + H(c−s)]/2
    b-staircase pair (s,0)/(0,s) s ≥ b + 1 + [W(c−s) + H(c+s)]/2

with c = cos φ, s_ = sin φ and 0 < φ ≤ 45° (the other half is the mirror
image).  n = W·H + a(a+1) + b(b+1), and a lattice fill can add squares at the
same side, which is where a band can pick up rows the table does not cover.

Cent lineage (the owner's reading of the compiler): the band is the epitaxial
motif (an L-frame grown along a seam rather than around the border); the
staircases are the corner wedges it leaves; the side is the W6 pressure
variable and the frozen angle is the phase-change reading (Δθ = 0 outside the
dedicated angle interval).  Everything here is a *construction* — the only
authority is `packlib.finalize` + `packlib.verify`.

Usage:
    python3 scripts/band_mosaic.py --sweep
    python3 scripts/band_mosaic.py --sweep --refine 0.01
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import packlib as P                                      # noqa: E402


# ---------------------------------------------------------------- geometry
def side(W: int, H: int, a: int, b: int, phi: float) -> float:
    """The minimal container side from the six contact laws (closed form)."""
    c, s = math.cos(phi), math.sin(phi)
    return max(W * c + H * s,
               W * s + H * c,
               a + 1 + (W * (c + s) + H * (c - s)) / 2.0,
               b + 1 + (W * (c - s) + H * (c + s)) / 2.0,
               a + b,        # the two staircase pairs meet along an edge
               a + 1)        # the two a-pairs meet along the diagonal


def staircase(depth: int, corner: str, side_: float):
    out = []
    for i in range(depth):
        for j in range(depth - i):
            if corner == "ll":
                out.append((i + 0.5, j + 0.5, 0.0))
            elif corner == "ur":
                out.append((side_ - i - 0.5, side_ - j - 0.5, 0.0))
            elif corner == "lr":
                out.append((side_ - i - 0.5, j + 0.5, 0.0))
            else:
                out.append((i + 0.5, side_ - j - 0.5, 0.0))
    return out


def band(W: int, H: int, phi: float, side_: float):
    c, s = math.cos(phi), math.sin(phi)
    cx = cy = side_ / 2.0
    out = []
    for i in range(W):
        for j in range(H):
            u = i - (W - 1) / 2.0
            v = j - (H - 1) / 2.0
            out.append((cx + u * c - v * s, cy + u * s + v * c, phi))
    return out


def _pen_vec(cand, X, Y, T):
    xc, yc, tc = cand
    e = 0.5 * (np.abs(np.cos(T)) + np.abs(np.sin(T)))
    ec = 0.5 * (abs(math.cos(tc)) + abs(math.sin(tc)))
    c0, s0 = math.cos(tc), math.sin(tc)
    cT, sT = np.cos(T), np.sin(T)
    axes = ((c0, s0), (-s0, c0), (cT, sT), (-sT, cT))
    out = None
    for ax, ay in axes:
        pen = ec + e - np.abs((X - xc) * ax + (Y - yc) * ay)
        out = pen if out is None else np.minimum(out, pen)
    return out


def build(W: int, H: int, a: int, b: int, phi: float, side_: float | None = None,
          fills: bool = True, tol: float = 1e-9):
    if side_ is None:
        side_ = side(W, H, a, b, phi)
    state = staircase(a, "ll", side_) + staircase(a, "ur", side_)
    state += staircase(b, "lr", side_) + staircase(b, "ul", side_)
    state += band(W, H, phi, side_)
    if fills:
        placed = np.array(state, dtype=float)
        k = int(math.ceil(side_ - 1e-9))
        for gx in range(k):
            for gy in range(k):
                cand = (gx + 0.5, gy + 0.5, 0.0)
                if cand[0] + 0.5 > side_ + 1e-12 or cand[1] + 0.5 > side_ + 1e-12:
                    continue
                X, Y, T = placed[:, 0], placed[:, 1], placed[:, 2]
                if float(np.max(_pen_vec(cand, X, Y, T))) <= -tol:
                    placed = np.vstack([placed, np.array(cand)])
        state = [(float(u), float(v), float(w)) for u, v, w in placed]
    return state, side_


def feasible(W, H, a, b, phi, side_):
    state, _ = build(W, H, a, b, phi, side_, fills=False)
    placed = np.array(state, dtype=float)
    n = len(state)
    for i in range(n):
        X = np.delete(placed[:, 0], i)
        Y = np.delete(placed[:, 1], i)
        T = np.delete(placed[:, 2], i)
        if n > 1 and float(np.max(_pen_vec(placed[i], X, Y, T))) > 1e-9:
            return False, state
    return True, state


# ------------------------------------------------------------------ sweep
def table_L():
    by_n = P.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    return {n: P.verify(by_n[n])["L"] for n in range(1, 1001) if n in by_n
            and len(by_n[n]) == n}


def side_vec(W: int, H: int, a: int, b: int, phis: np.ndarray) -> np.ndarray:
    """side() over an array of angles (radians), vectorised."""
    c, s = np.cos(phis), np.sin(phis)
    return np.maximum.reduce([
        W * c + H * s,
        W * s + H * c,
        a + 1 + (W * (c + s) + H * (c - s)) / 2.0,
        b + 1 + (W * (c - s) + H * (c + s)) / 2.0,
        np.full_like(c, a + b),
        np.full_like(c, a + 1),
    ])


def sweep(w_max=40, h_max=12, a_max=10, coarse=0.5, refine=0.02, top=3):
    tab = table_L()
    t0 = __import__("time").time()
    grid = np.radians(np.arange(0.5, 45.0 + 1e-9, coarse))
    best = {}
    triples = 0
    for W in range(1, w_max + 1):
        for H in range(1, h_max + 1):
            if W * H > 1000:
                continue
            for a in range(0, a_max + 1):
                for b in range(0, a_max + 1):
                    n = W * H + a * (a + 1) + b * (b + 1)
                    if not (1 <= n <= 1000):
                        continue
                    triples += 1
                    vals = side_vec(W, H, a, b, grid)
                    order = np.argsort(vals)[:top]
                    for k in order:
                        lo = grid[max(0, k - 1)]
                        hi = grid[min(len(grid) - 1, k + 1)]
                        fine = np.arange(lo, hi + 1e-12, math.radians(refine))
                        fv = side_vec(W, H, a, b, fine)
                        j = int(np.argmin(fv))
                        s = float(fv[j])
                        if s < math.sqrt(n) - 1e-12:
                            continue
                        if n in tab and s < tab[n] - 1e-9:
                            if n not in best or s < best[n][0]:
                                best[n] = (s, math.degrees(float(fine[j])), W, H, a, b)
    print(f"{triples} triples scanned; design survivors: {len(best)} "
          f"({__import__('time').time()-t0:.0f} s)", flush=True)
    wins = []
    for n, (s, g, W, H, a, b) in sorted(best.items()):
        ok, state = feasible(W, H, a, b, math.radians(g), s)
        if not ok:
            continue
        fin, r = P.finalize(state)
        if r["ok"] and r["L"] < tab[n] - 1e-9:
            wins.append({"n": n, "L_before": tab[n], "L_after": r["L"],
                         "phi_deg": g, "W": W, "H": H, "a": a, "b": b,
                         "gain": (tab[n] - r["L"]) / math.sqrt(n),
                         "state": [[float(u), float(v), float(w)] for u, v, w in fin]})
            print(f"  WIN n={n}: {tab[n]:.9f} -> {r['L']:.9f} "
                  f"(phi {g:.2f}, {W}x{H}, a {a}, b {b})", flush=True)
    path = os.path.join(ROOT, "workspace/push/band_mosaic_results.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"found": wins, "survivors": len(best),
               "score_gain": sum(w["gain"] for w in wins)}, open(path, "w"), indent=1)
    print(f"verified wins: {len(wins)}; gain "
          f"{sum(w['gain'] for w in wins):.6f}; wrote {path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--w-max", type=int, default=40)
    ap.add_argument("--h-max", type=int, default=12)
    ap.add_argument("--a-max", type=int, default=10)
    ap.add_argument("--coarse", type=float, default=1.0)
    ap.add_argument("--refine", type=float, default=0.05)
    args = ap.parse_args()
    if args.sweep:
        return sweep(args.w_max, args.h_max, args.a_max, args.coarse, args.refine)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
