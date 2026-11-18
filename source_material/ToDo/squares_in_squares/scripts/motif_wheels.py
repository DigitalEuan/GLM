#!/usr/bin/env python3
r"""motif_wheels.py — declared motif families, exact builders, one gate, one scorer.

WHY THIS EXISTS (and what it replaces).  `cent_engines.py` compiled four
physics isomorphisms into packing search engines — P-04 flywheel (collective
cluster rotation), P-05 optical PLL (angle phase-locking), P-11 piezo (Hookean
strain relaxation), P-12 Griffith (crack-plane split) — and ran them over the
whole campaign: **236 cells, 0 finds** (`cent_campaign.json["finds"] == []`,
`cent_findings.json == []`).  That route is written off in `14-WRITE-OFFS.md`
and `workspace/push/writeoffs.json`; do not pay for it again.  What is left is
base GEOMETRY: the score is set by which arrangements exist, not by how well a
settle polishes one.  Measured last turn: the r = 1 rows return L
**bit-identical** (8.535533908) when pushed 0.02 below, i.e. locally rigid, and
the n = 5 optimum is reachable only as the 4-upright-corners + 45-degree
diamond cross — 0/300 pure rotation kicks, 25/150 re-slot kicks.

WHAT A MOTIF WHEEL IS.  A declared family in the cent sense, not a generator:
a finite parameter grid, an exact integer count law checked by two independent
paths, an exact builder returning (n, L, state), a declared tilt family, and a
declared rigidity status.  The wheel decides nothing at spin time; `spin()`
only enumerates its declared cells, prunes them by the declared rules, gates
the survivors with `packlib` and scores them with `sqscore`.

GATE (single authority).  Every candidate state goes through
`packlib.finalize` — the project's own scale-then-round step — and must come
back `ok` with `worst_pen <= -1e-12`, which is exactly `finalize`'s guarantee,
so a candidate can survive the 12-dp CSV rounding.  The declared side L is
checked against packlib's L to `LAW_TOL = 1e-6`: the 2e-9 contact pad and the
1e-12 rounding live inside that tolerance, while a wrong count law (a
millimetre, not a nanometre) does not.  A mismatch is a refusal, never a silent
pass.

SCORER (single authority).  No score is computed in this file.  The delivered
side is `sqscore.extent`, the gain is `sqscore.row_gain`, the beat test is
`sqscore.is_beat`, the grid is `sqscore.grid`, and `sqscore.guard()` runs before
any spin and raises unless submission.csv is exactly 22.218056945 / 553 beats.

REFUSAL TAXONOMY.  Every refusal carries its numbers; none is dropped:
    n_cap                 n > 1000 (the submission is 1000 rows)
    area_floor            L < sqrt(n) - 1e-9  (area bound)
    area_exact            |L - sqrt(n)| <= sqrt-tolerance: zero slack, so the
                          cell cannot beat its own row by construction
    packlib_rejected      finalize not ok, or worst_pen > -1e-12
    declared_l_mismatch   |declared L - packlib L| > 1e-6
    worse_than_grid       L > grid(n) - 1e-12
    no_gain               beats grid but L >= delivered L - 1e-12
    dominated             another wheel reaches the same n at a lower L
    no_base / base_mismatch / count_law_mismatch / builder_error
                          a transform wheel whose delivered base is missing,
                          has the wrong side, fails its two-path count, or whose
                          builder raised

USAGE
    python3 scripts/motif_wheels.py              # spin, print, write the ledger
    python3 scripts/motif_wheels.py --selftest   # exercise every prune path
    python3 scripts/motif_wheels.py --writeoffs  # refresh the write-off register

Writes only `workspace/push/motif_spin.json` (and the write-off register with
`--writeoffs`); `submission.csv` and `table.json` are never touched.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import packlib as P       # noqa: E402
import sqscore as SQ      # noqa: E402
import seam_wheels as SW  # noqa: E402  (the G-2 exact seam instrument)

OUT = os.path.join(ROOT, "workspace/push/motif_spin.json")
WRITEOFFS = os.path.join(ROOT, "workspace/push/writeoffs.json")
CAMPAIGN = os.path.join(ROOT, "workspace/push/cent_campaign.json")
FINDINGS = os.path.join(ROOT, "workspace/push/cent_findings.json")

#: The submission is 1000 rows; nothing above it can be scored.
MAX_N = 1000
#: packlib.finalize guarantees this margin on the 12-dp rounded state.
EPS_GATE = 1e-12
#: declared-law tolerance (holds the 2e-9 contact pad + 1e-12 rounding).
LAW_TOL = 1e-6
#: the area bound, to float tolerance.
FLOOR_TOL = 1e-9

SQ2 = math.sqrt(2.0)


# --------------------------------------------------------------- cell model
@dataclass(frozen=True)
class Cell:
    """One declared candidate: what the wheel says it built."""
    wheel: str
    params: tuple
    n: int
    L: float                      # the declared container side
    state: tuple                  # tuple of (x, y, theta)
    law: str                      # the count/side law, as text
    note: str = ""
    #: a RECONSTRUCTION cell declares the side it must reproduce instead of a
    #: side to beat.  Its pass condition is |gated L - expect_L| <= LAW_TOL, so
    #: a reconstruction wheel is tested, not scored — which is what the review
    #: asked for before M-diamond is allowed to be asked to beat anything.
    expect_L: float | None = None


class Refusal(Exception):
    """A wheel-level refusal (no state was built), carrying its reason."""

    def __init__(self, reason: str, detail: str, n: int | None = None,
                 params: tuple | None = None):
        super().__init__(f"{reason}: {detail}")
        self.reason, self.detail, self.n, self.params = reason, detail, n, params


@dataclass(frozen=True)
class Wheel:
    wheel_id: str
    name: str
    params: tuple
    angle_family: str
    rigidity: str
    note: str
    build: Callable[[dict], Iterable[Cell]]


# ------------------------------------------------------------- 1. the grid
def _grid_cells(per: dict) -> Iterable[Cell]:
    """k x k upright grid. n = k^2, L = k: the area-exact baseline."""
    for k in range(1, 33):                     # k = 32 gives n = 1024 > 1000
        n = k * k
        st = tuple((i % k + 0.5, i // k + 0.5, 0.0) for i in range(n))
        assert len(st) == n
        yield Cell("M-grid", (k,), n, float(k), st,
                   f"n = k^2 = {n}; L = k = {k}", "baseline; area-exact")


# ------------------------------------------- 2. the Goebel cross family
def _cross_cells(per: dict) -> Iterable[Cell]:
    """Gap a k x k upright grid by g, fill every interior cross with a 45 deg
    square: n = k^2 + (k-1)^2, L = 1 + (k-1)(1+g).

    k = 2 is Goebel's n = 5 optimum: four upright squares with the fifth turned
    45 degrees between them, feasible exactly when the cross width g is at
    least the diamond's half-diagonal sqrt(2)/2, at L = 2 + sqrt(2)/2.
    """
    for k in (2, 3):
        for g in (SQ2 / 2 - 0.01, SQ2 / 2 + 0.001, 0.75, 0.8):
            s = 1.0 + g
            n = k * k + (k - 1) * (k - 1)
            L = 1.0 + (k - 1) * s
            st = [(0.5 + i * s, 0.5 + j * s, 0.0)
                  for j in range(k) for i in range(k)]
            # square i spans [i*s, i*s+1] and square i+1 starts at (i+1)*s,
            # so the cross between them is centred at i*s + 1 + g/2.  Using
            # (1+i)*s instead puts every diamond on the far vertex and packlib
            # rejects the cell (this bug was caught by --selftest).
            st += [(i * s + 1.0 + g / 2, j * s + 1.0 + g / 2, math.pi / 4)
                   for j in range(k - 1) for i in range(k - 1)]
            assert len(st) == n
            yield Cell("M-cross-grid", (k, round(g, 6)), n, L, tuple(st),
                       f"n = k^2 + (k-1)^2 = {n}; L = 1 + (k-1)(1+g) = {L:.9f}",
                       "k=2 is s(5) = 2 + sqrt(2)/2 (Goebel 1979)" if k == 2
                       else "k>=3 needs a wider cross, so it loses to the grid")


# --------------------------------------------------- 3. the cascade band
def _cascade_cells(per: dict) -> Iterable[Cell]:
    """The exact band step up the r = 1 column, from a delivered base.

    From n0 = k0^2 + r squares in side k0 + delta, the band adds the k0+1
    squares (i+1/2, k0+delta+1/2) and the k0 squares (k0+delta+1/2, j+1/2),
    giving (k0+1)^2 + r squares in side (k0+1) + delta.  delta is READ from the
    delivered base (the column's own slack), then re-asserted at every step.

    The band step itself is not re-implemented here: `pl32_base.band` is the
    single implementation (anchored, with its 1e-9 contact gap).
    """
    from pl32_base import band

    for k0, r in ((8, 1), (25, 1)):
        n0 = k0 * k0 + r
        if n0 not in per:
            raise Refusal("no_base", f"delivered row n={n0} (k0={k0}, r={r}) "
                                     "is not in submission.csv", n=n0, params=(k0, r))
        base = np.asarray(per[n0], float)
        rb = P.verify([tuple(map(float, q)) for q in base])
        if not rb["ok"] or rb["worst_pen"] > -EPS_GATE:
            raise Refusal("base_mismatch", f"delivered base n={n0} does not gate: "
                                           f"worst_pen {rb['worst_pen']:+.2e}",
                          n=n0, params=(k0, r))
        delta = float(rb["L"]) - k0
        if delta <= 0:
            raise Refusal("base_mismatch", f"base n={n0} has non-positive slack "
                                           f"{delta:.6f}", n=n0, params=(k0, r))
        st = base
        k, n = k0, n0
        j = 0
        yield Cell("M-cascade", (k0, r, round(delta, 9)), n, k + delta,
                   tuple(map(tuple, st)),
                   f"base n0 = k0^2 + r = {n0}; L = k0 + delta = {k0 + delta:.9f}",
                   "the delivered base itself (R = 1 column)")
        while True:
            st = band(st, k, delta)
            k += 1
            j += 1
            n_rec = len(st)
            n_closed = n0 + j * (2 * k0 + 1) + j * (j - 1)
            if n_rec != n_closed:
                raise Refusal("count_law_mismatch",
                              f"recursive {n_rec} != closed form {n_closed} at j={j}",
                              n=n_rec, params=(k0, r))
            n = n_rec
            yield Cell("M-cascade", (k0, r, round(delta, 9)), n, k + delta,
                       tuple(map(tuple, st)),
                       f"n_{j} = n0 + j(2k0+1) + j(j-1) = {n}; L = k + delta = {k + delta:.9f}",
                       "band step (2k+1 squares in the two strips)")
            if n > MAX_N:
                break


# --------------------------------------------- 4. Friedman's L-extension
def _anchor(state) -> np.ndarray:
    a = np.asarray(state, float).copy()
    ex = 0.5 * (np.abs(np.cos(a[:, 2])) + np.abs(np.sin(a[:, 2])))
    a[:, 0] -= float((a[:, 0] - ex).min())
    a[:, 1] -= float((a[:, 1] - ex).min())
    return a


def _lext_cells(per: dict) -> Iterable[Cell]:
    """Friedman's L-extension, as in `column3/05_cent_patterns.py`.

    From m squares in side L (inner square at [1, 1+L]^2), place floor(L+1)
    squares along the bottom band and floor(L) up the left band:
    m' = m + floor(L+1) + floor(L) in side L+1.
    """
    for m0 in (5, 10):
        if m0 not in per:
            raise Refusal("no_base", f"delivered row n={m0} is not in submission.csv",
                          n=m0, params=(m0,))
        base = np.asarray(per[m0], float)
        rb = P.verify([tuple(map(float, q)) for q in base])
        if not rb["ok"]:
            raise Refusal("base_mismatch", f"delivered base n={m0} does not gate",
                          n=m0, params=(m0,))
        st = _anchor(base)
        m, L = m0, float(rb["L"])
        yield Cell("M-l-extension", (m0, round(L, 9)), m, L,
                   tuple(map(tuple, st)),
                   f"base m0 = {m0}; L0 = {L:.9f}", "the delivered base itself")
        for j in range(1, 4):
            row, col = int(math.floor(L + 1)), int(math.floor(L))
            inner = [(x + 1.0, y + 1.0, t) for x, y, t in st]
            band_b = [(i + 0.5, 0.5, 0.0) for i in range(row)]
            band_l = [(0.5, 1.0 + jj + 0.5, 0.0) for jj in range(col)]
            st2 = np.asarray(inner + band_b + band_l, float)
            m_closed = m
            m = len(st2)
            expected = m_closed + row + col
            if m != expected:
                raise Refusal("count_law_mismatch",
                              f"built {m} squares, law {m_closed}+{row}+{col}={expected}",
                              n=m, params=(m0,))
            L = L + 1.0
            st = _anchor(st2)
            yield Cell("M-l-extension", (m0, round(L, 9)), m, L,
                       tuple(map(tuple, st)),
                       f"m' = m + floor(L+1) + floor(L); L' = L + 1 = {L:.9f}",
                       f"L-extension step {j}")
            if m > MAX_N:
                break


def _diamond_cells(per: dict) -> Iterable[Cell]:
    """M-diamond: reconstruct a delivered r = 1 atom from its integers.

    `seam_wheels.describe` reads a row as (p, diamond offset, wall anchors) and
    rebuilds it in Q(sqrt 2).  This wheel emits that rebuild with the delivered
    side as its EXPECTED side, so the wheel is judged on reproducing it.  Rows
    whose tilted block is not a full p x p diamond (occupancy < 1) refuse, which
    is the honest limit of this declaration: 20-R1-ATOMS.md section 4 catalogues
    them as partial (0.617, 0.660, 0.578, 0.502).
    """
    for k in range(2, 32):
        n = k * k + 1
        if n not in per or n > MAX_N:
            continue
        try:
            atom = SW.describe(n, per)
        except SW.Refusal as e:
            yield Cell("M-diamond", (k,), n, SW.SQ.extent(per[n]), (),
                       f"p = ? ({e.reason})", e.detail)
            continue
        st = SW.build(atom, atom.L_del)
        yield Cell("M-diamond", (atom.p, atom.kcols()[0], atom.kcols()[1]), n,
                   atom.L_del, tuple(st),
                   f"p = {atom.p}; columns {atom.kcols()}; walls {atom.meta.get('walls')}",
                   f"delta = {atom.delta_del:.9f}", expect_L=atom.L_del)


REGISTRY: tuple[Wheel, ...] = (
    Wheel("M-diamond", "rebuild a delivered 45 deg seam atom from integers",
          (5, 17), "{0, pi/4}", "reconstruction (tested, not scored)",
          "p x p diamond + wall-anchored upright columns, exact in Q(sqrt 2)",
          _diamond_cells),
    Wheel("M-grid", "k x k upright grid", (1, 32),
          "{0, pi/2}", "rigid (jammed, no slack)",
          "the area-exact baseline every row is measured against", _grid_cells),
    Wheel("M-cross-grid", "gap a grid, fill the crosses at 45 deg", (2, 3),
          "{0, pi/4}", "rigid (exact contact at g = sqrt(2)/2)",
          "k=2 is Goebel's s(5); k>=3 is the declared negative", _cross_cells),
    Wheel("M-cascade", "exact band step up the r = 1 column", (8, 25),
          "{0, pi/2}", "inherits the base's rigidity",
          "carries one gated base to every row of its column", _cascade_cells),
    Wheel("M-l-extension", "Friedman L-extension closure", (5, 10),
          "{0, pi/2}", "rigid (band contacts)",
          "m' = m + floor(L+1) + floor(L), L' = L + 1", _lext_cells),
)


# ------------------------------------------------------------------ judging
def _refuse(out: dict, reason: str, detail: str) -> dict:
    out.update(status="refused", reason=reason, detail=detail)
    return out


def judge(cell: Cell, per: dict) -> dict:
    """Prune, gate and score one declared cell. Pruning order is declared order:
    the cheap exact rules first, then packlib, then the scorer."""
    out = {"wheel": cell.wheel, "params": list(cell.params), "n": int(cell.n),
           "declared_L": round(float(cell.L), 12), "law": cell.law,
           "note": cell.note}
    n = int(cell.n)
    if n < 1:
        return _refuse(out, "bad_n", f"n={n}")
    if n > MAX_N:                                            # declared cap
        return _refuse(out, "n_cap", f"n={n} > {MAX_N}")
    L_decl = float(cell.L)
    floor = math.sqrt(n)
    if L_decl < floor - FLOOR_TOL:                           # area bound
        return _refuse(out, "area_floor",
                       f"L={L_decl:.9f} < sqrt(n)={floor:.9f}")
    if not cell.state:                                       # nothing was built
        # a declaration that could not read the row as integers (a partial
        # diamond) carries its reason in `note`; it is not a candidate
        return _refuse(out, "layout_not_enumerated", cell.note or "no state")
    # Karakus (arXiv:2609.37410, Cor. 1.2): s(N) >= 1/2 + sqrt(N - floor sqrt N
    # + 1/4) for every nonsquare N >= 8.  It is strictly stronger than the area
    # bound, and it is a theorem, so a DECLARED side below it is a builder error
    # rather than a loss: refuse it before paying for the gate.
    bnd = SW.bound_karakus(n)
    out["karakus_bound"] = round(bnd, 12) if bnd is not None else None
    if bnd is not None and L_decl < bnd - 1e-9:
        return _refuse(out, "below_karakus_bound",
                       f"declared L={L_decl:.9f} < s({n}) >= {bnd:.9f}: no "
                       "packing of this count has that side")
    st, r = P.finalize([tuple(map(float, q)) for q in cell.state])
    out["gate_L"] = round(float(r["L"]), 12)
    if cell.expect_L is not None:
        # a reconstruction claim: the declaration is right or it is wrong
        if not r["ok"]:
            return _refuse(out, "packlib_rejected",
                           f"reconstruction does not gate (worst_pen "
                           f"{r['worst_pen']:+.3e})")
        if abs(float(r["L"]) - cell.expect_L) > LAW_TOL:
            return _refuse(out, "reconstruction_mismatch",
                           f"declared {cell.expect_L:.9f} vs rebuilt "
                           f"{float(r['L']):.9f}")
        out.update(status="reconstructs", expect_L=round(float(cell.expect_L), 12),
                   rebuilt_L=round(float(r["L"]), 12),
                   err=float(r["L"]) - cell.expect_L)
        return out
    # n <= 1 has no pair, so packlib reports worst_pen = -inf; keep the ledger
    # strict JSON (json module writes -Infinity, which is not valid JSON)
    out["worst_pen"] = (float(r["worst_pen"])
                        if math.isfinite(float(r["worst_pen"])) else None)
    if not r["ok"] or r["worst_pen"] > -EPS_GATE:            # the gate
        return _refuse(out, "packlib_rejected",
                       f"ok={r['ok']} worst_pen={r['worst_pen']:+.3e}")
    L = float(r["L"])
    if abs(L - L_decl) > LAW_TOL:                            # builder bug
        return _refuse(out, "declared_l_mismatch",
                       f"declared {L_decl:.9f} vs packlib {L:.9f}")
    # area_exact is a fact about the DECLARED law, not about the padded side:
    # finalize opens every contact by 2e-9, so the gated L of an exact-fill
    # construction is sqrt(n) + 2e-9, while L_decl is sqrt(n) exactly.
    if abs(L_decl - floor) <= 1e-12:                         # zero slack
        return _refuse(out, "area_exact",
                       f"declared L={L_decl:.9f} = sqrt(n): no slack to win")
    if bnd is not None and L < bnd - 1e-9:
        # the gated side is below a proved lower bound: the gate itself is wrong
        return _refuse(out, "below_karakus_bound",
                       f"gated L={L:.9f} < s({n}) >= {bnd:.9f}: the verifier "
                       "passed a state no packing can have")
    g = SQ.grid(n)
    if L > g - 1e-12:                                        # loses to grid
        return _refuse(out, "worse_than_grid", f"L={L:.9f} > grid {g}")
    old = per.get(n)
    old_L = SQ.extent(old) if old is not None else float(g)
    if L >= old_L - 1e-12:                                   # no improvement
        return _refuse(out, "no_gain",
                       f"L={L:.9f} >= delivered {old_L:.9f}")
    gain_new, gain_old = SQ.row_gain(n, L), SQ.row_gain(n, old_L)
    out.update(status="survivor", delivered_L=round(old_L, 12),
               row_gain_new=gain_new, row_gain_old=gain_old,
               dscore=-(gain_new - gain_old), is_beat=SQ.is_beat(n, L),
               state=[[round(float(a), 12) for a in q] for q in st])
    return out


def _dominate(survivors: list[dict]) -> tuple[list[dict], list[dict]]:
    """One survivor per n: the lowest gated L; the rest are refused as dominated."""
    best: dict[int, dict] = {}
    for s in survivors:
        cur = best.get(s["n"])
        if cur is None or s["gate_L"] < cur["gate_L"] - 1e-12:
            best[s["n"]] = s
    kept, dropped = [], []
    for s in survivors:
        w = best[s["n"]]
        if s is w:
            kept.append(s)
        else:
            s = dict(s)
            s.update(status="refused", reason="dominated",
                     detail=f"{w['wheel']}{tuple(w['params'])} reaches n={s['n']} "
                            f"at L={w['gate_L']:.9f}")
            dropped.append(s)
    return kept, dropped


def spin(per: dict | None = None, wheels: tuple[Wheel, ...] = REGISTRY,
         write: bool = True, verbose: bool = True) -> dict:
    """Enumerate every declared cell, prune, gate, score; keep the survivors."""
    per = SQ.load() if per is None else per
    survivors: list[dict] = []
    recon: list[dict] = []
    refused: list[dict] = []
    per_wheel: dict[str, Counter] = defaultdict(Counter)
    t0 = time.time()
    for w in wheels:
        try:
            for cell in w.build(per):
                j = judge(cell, per)
                per_wheel[w.wheel_id]["cells"] += 1
                # a reconstruction cell is neither a survivor nor a refusal: it
                # is a TEST of the declaration, so it gets its own tally
                per_wheel[w.wheel_id][j.get("reason") or j["status"]] += 1
                if j["status"] == "survivor":
                    survivors.append(j)
                elif j["status"] == "reconstructs":
                    recon.append(j)
                else:
                    refused.append(j)
        except Refusal as e:
            per_wheel[w.wheel_id]["cells"] += 1
            per_wheel[w.wheel_id][e.reason] += 1
            refused.append({"wheel": w.wheel_id, "params": list(e.params or w.params),
                            "status": "refused", "reason": e.reason, "detail": e.detail})
        except Exception as e:                              # noqa: BLE001
            per_wheel[w.wheel_id]["cells"] += 1
            per_wheel[w.wheel_id]["builder_error"] += 1
            refused.append({"wheel": w.wheel_id, "params": list(w.params),
                            "status": "refused", "reason": "builder_error",
                            "detail": f"{type(e).__name__}: {e}"[:200]})
    kept, dropped = _dominate(survivors)
    refused += dropped
    kept.sort(key=lambda s: (-s["dscore"], s["n"]))
    ledger = {
        "instrument": "motif_wheels.py", "schema": "motif-spin/1",
        "written": time.strftime("%Y-%m-%d %H:%M:%S"),
        "seconds": round(time.time() - t0, 2),
        "wheels": [{"wheel_id": w.wheel_id, "name": w.name,
                    "params": w.params, "angle_family": w.angle_family,
                    "rigidity": w.rigidity, "note": w.note} for w in wheels],
        "counts": {"cells": sum(c.get("cells", 0) for c in per_wheel.values()),
                   "survivors": len(kept), "reconstructs": len(recon),
                   "refused": len(refused)},
        "survivors": kept, "reconstructions": recon, "refused": refused,
        "per_wheel": {k: dict(v) for k, v in per_wheel.items()},
        "total_dscore": sum(s["dscore"] for s in kept),
    }
    if write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(ledger, f, indent=1)
    if verbose:
        _report(ledger)
    return ledger


def _report(led: dict):
    print(f"\nspin: {led['counts']['cells']} declared cells, "
          f"{led['counts']['survivors']} survivors, "
          f"{led['counts'].get('reconstructs', 0)} reconstructions, "
          f"{led['counts']['refused']} refused  [{led['seconds']}s]")
    if led.get("reconstructions"):
        print(f"declaration reproduced on {len(led['reconstructions'])} rows: "
              + ", ".join(f"n={r['n']}" for r in led["reconstructions"]))
    print(f"{'wheel':16s} {'cells':>6s}  refusals")
    for wid, c in led["per_wheel"].items():
        why = ", ".join(f"{k}={v}" for k, v in sorted(c.items()) if k != "cells")
        print(f"{wid:16s} {c['cells']:>6d}  {why}")
    if led["survivors"]:
        print("\nsurvivors (gated by packlib, scored by sqscore):")
        for s in led["survivors"]:
            print(f"  n={s['n']:<4} L={s['gate_L']:.9f} (delivered "
                  f"{s['delivered_L']:.9f})  dscore {s['dscore']:+.9f}  "
                  f"[{s['wheel']}{tuple(s['params'])}]")
        print(f"  measured total score change: {led['total_dscore']:+.9f}")
    else:
        print("\nNO SURVIVOR: every declared cell is refused with a reason above. "
              "No score is claimed and no row is changed.")
    if os.path.exists(WRITEOFFS):
        try:
            reg = json.load(open(WRITEOFFS))
            for e in reg.get("entries", []):
                print(f"write-off {e['id']}: {e['route']} — {e['evidence']} "
                      f"({e['verdict']})")
        except Exception:                                   # noqa: BLE001
            pass


# ------------------------------------------------------------- write-offs
def refresh_writeoffs() -> dict:
    """Rebuild the write-off register from the campaign ledgers (derived, not
    asserted): the compiled-analogy route is closed only if it really found
    nothing, and the numbers are re-read every time."""
    camp = json.load(open(CAMPAIGN)) if os.path.exists(CAMPAIGN) else {}
    finds = json.load(open(FINDINGS)) if os.path.exists(FINDINGS) else []
    done = camp.get("done", [])
    per_engine = Counter(x.split("|")[1] for x in done if x.count("|") >= 1)
    campaign_finds = camp.get("finds", []) or []
    total_finds = len(campaign_finds) + len(finds or [])
    reg = {"schema": "cent-writeoff-register/1",
           "written": time.strftime("%Y-%m-%d %H:%M:%S"),
           "entries": []}
    if os.path.exists(WRITEOFFS):
        try:
            reg["entries"] = json.load(open(WRITEOFFS)).get("entries", [])
        except Exception:                                   # noqa: BLE001
            reg["entries"] = []
    entry = {
        "id": "W-01",
        "route": "compiled physics-analogy search moves (P-04 flywheel, P-05 PLL, "
                 "P-11 piezo, P-12 Griffith) as packing attacks",
        "source": "scripts/cent_engines.py (Run 6)",
        "evidence": f"{len(done)} campaign cells, {total_finds} finds",
        "cells": len(done),
        "per_engine": dict(per_engine),
        "finds": total_finds,
        "verdict": "written off" if total_finds == 0 else "REOPENED: finds exist",
        "reason": "a move cannot add an arrangement the geometry does not have; "
                  "score here is set by base geometry, and the two measured "
                  "escapes (re-slot into the widest gap; the n=5 4-around-1 "
                  "cross) are geometric, not analogous to a physical law",
        "do_not_retry_unless": "a new engine is shown, on a gated control, to "
                               "reach a side no local settle reaches",
        "pointers": ["workspace/push/cent_campaign.json",
                     "workspace/push/cent_findings.json",
                     "14-WRITE-OFFS.md", "scripts/motif_wheels.py"],
    }
    reg["entries"] = [e for e in reg["entries"] if e.get("id") != entry["id"]] + [entry]
    with open(WRITEOFFS, "w") as f:
        json.dump(reg, f, indent=1)
    print(f"write-off register: {WRITEOFFS} "
          f"({entry['evidence']}, verdict: {entry['verdict']})")
    return reg


# --------------------------------------------------------------- selftest
def selftest() -> int:
    """Exercise every prune path and the survivor path, so none is dead code."""
    per = SQ.load()
    checks = []

    def expect(name, j, reason):
        got = j.get("reason", "survivor")
        ok = got == reason
        checks.append(ok)
        print(f"  {'ok ' if ok else 'FAIL'} {name:26s} -> {got}"
              f"{'' if ok else f' (expected {reason})'}")

    five_grid = tuple((i % 3 + 0.5, i // 3 + 0.5, 0.0) for i in range(5))
    expect("n_cap", judge(Cell("t", (), 1024, 32.0,
                               tuple((i % 32 + 0.5, i // 32 + 0.5, 0.0)
                                     for i in range(1024)), ""), per), "n_cap")
    expect("area_floor", judge(Cell("t", (), 5, 2.2, five_grid, ""), per),
           "area_floor")
    expect("area_exact", judge(Cell("t", (), 4, 2.0,
                                    tuple((i % 2 + 0.5, i // 2 + 0.5, 0.0)
                                          for i in range(4)), ""), per), "area_exact")
    expect("packlib_rejected", judge(Cell("t", (), 2, 2.1,
                                          ((0.5, 0.5, 0.0), (0.9, 0.5, 0.0)), ""),
                                     per), "packlib_rejected")
    expect("declared_l_mismatch", judge(Cell("t", (), 2, 3.0,
                                             ((0.5, 0.5, 0.0), (1.5, 0.5, 0.0)), ""),
                                        per), "declared_l_mismatch")
    expect("worse_than_grid", judge(Cell("t", (), 4, 3.0,
                                         ((0.5, 0.5, 0.0), (2.5, 0.5, 0.0),
                                          (0.5, 2.5, 0.0), (2.5, 2.5, 0.0)), ""),
                                    per), "worse_than_grid")
    # the Goebel cross at s(5)+0.001: legal, but the delivered row already sits
    # at the optimum -> no_gain (this is the honest result, not a failure)
    g = SQ2 / 2 + 0.001
    s = 1.0 + g
    cross = ((0.5, 0.5, 0.0), (0.5 + s, 0.5, 0.0), (0.5, 0.5 + s, 0.0),
             (0.5 + s, 0.5 + s, 0.0), (1.0 + g / 2, 1.0 + g / 2, math.pi / 4))
    L_cross = 1.0 + s                      # k = 2: L = 1 + (k-1)(1+g)
    expect("no_gain (Goebel cross)", judge(Cell("t", (), 5, L_cross, cross, ""), per),
           "no_gain")
    # the same cell against a doctored delivered row at L=3.0 must survive
    j = judge(Cell("t", (), 5, L_cross, cross, ""), {5: [(i % 3 + 0.5, i // 3 + 0.5, 0.0)
                                                          for i in range(5)]})
    expect("survivor path", j, "survivor")
    if j.get("status") == "survivor":
        print(f"       survivor dscore {j['dscore']:+.9f} "
              f"(delivered 3.0 -> {j['gate_L']:.9f})")
    # dominance keeps the lower side
    a = {"wheel": "a", "params": [], "n": 7, "gate_L": 1.0, "dscore": 0.1,
         "status": "survivor"}
    b = {"wheel": "b", "params": [], "n": 7, "gate_L": 2.0, "dscore": 0.0,
         "status": "survivor"}
    kept, dropped = _dominate([a, b])
    ok = len(kept) == 1 and kept[0] is a and dropped[0]["reason"] == "dominated"
    checks.append(ok)
    print(f"  {'ok ' if ok else 'FAIL'} {'dominated':26s} -> "
          f"{len(kept)} kept, {dropped[0]['reason'] if dropped else 'none'}")
    # ---- the G-2 additions: a reconstruction wheel and the stronger bound
    rec = [judge(c, per) for c in _diamond_cells(per)]
    good = [r for r in rec if r.get("status") == "reconstructs"]
    ck_ok = len(good) >= 2 and any(r["n"] == 65 for r in good) \
        and any(r["n"] == 626 for r in good)
    checks.append(ck_ok)
    print(f"  {'ok ' if ck_ok else 'FAIL'} {'M-diamond reconstructs':26s} -> "
          f"{len(good)}/{len(rec)} cells reproduce the delivered side")
    print(f"       " + ", ".join(f"n={r['n']}" for r in good[:14]))
    # the Karakus bound must refuse a side no packing can have.  n=10 sits
    # between its area floor 3.162278 and its proved bound 3.192582, so 3.18 is
    # the only window where the bound is the binding rule.
    ten = tuple((i % 4 + 0.5, i // 4 + 0.5, 0.0) for i in range(10))
    j = judge(Cell("t", (), 10, 3.18, ten, ""), per)
    expect("below_karakus_bound", j, "below_karakus_bound")
    print(f"       s(10) >= {SW.bound_karakus(10):.6f}, area floor "
          f"{math.sqrt(10):.6f}, declared 3.180000")
    # and the k^2 - 1 control: s(k^2-1) = k, so no row there may beat k
    ctl = [K for K in range(3, 32)
           if K * K - 1 in per
           and SQ.is_beat(K * K - 1, SQ.extent(per[K * K - 1]))]
    checks.append(not ctl)
    print(f"  {'ok ' if not ctl else 'FAIL'} {'control s(k^2-1)=k':26s} -> "
          f"{len(ctl)} violations in 29 rows")
    # the cascade's two-path count law, against the closed form
    n0, k0, bad = 65, 8, 0
    for jj in range(1, 18):
        if n0 + jj * (2 * k0 + 1) + jj * (jj - 1) != (k0 + jj) ** 2 + 1:
            bad += 1
    checks.append(bad == 0)
    print(f"  {'ok ' if bad == 0 else 'FAIL'} {'cascade count law':26s} -> "
          f"{'closed form == (k+j)^2+1 for j=1..17' if bad == 0 else f'{bad} mismatches'}")
    print(f"\nselftest: {sum(checks)}/{len(checks)} checks pass")
    return 0 if all(checks) else 1


# ------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--writeoffs", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()
    s = SQ.guard()
    print(f"[sqscore] delivered table: score {s['score']:.9f}, "
          f"{s['beats']} beats, {s['rows']} rows")
    if args.writeoffs:
        refresh_writeoffs()
        return 0
    if args.selftest:
        return selftest()
    spin(write=not args.no_write)
    print(f"\nledger: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
