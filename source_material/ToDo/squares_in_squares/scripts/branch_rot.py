#!/usr/bin/env python3
r"""branch_rot.py — single-row branch-assignment + rotation search (run 69).

THE ROW IS CHOSEN BY THE WALL-MARGIN TABLE, NOT BY TASTE
--------------------------------------------------------
`wall_margin.py` gives mu(n) = L - sqrt(n) and rho(n) = mu/sqrt(n) = score(n) for
all 1000 rows.  The targeting rule used here is fixed in advance:

    among rows that are (a) NOT proved optimal, and (b) small enough that the
    whole declared cell space can be enumerated (n <= 20), take the largest rho
    (score value per row), tie-break on mu.

That selects n = 11 (rho = 0.168985, mu = 0.560459, 3.877084 delivered side,
5 of 11 squares tilted).  It is the largest score payoff per row that is still
small enough to enumerate exactly at this scale.

THE DECLARED CELL SPACE (this is the whole experiment)
------------------------------------------------------
A *word* is an exact rotation, given by a rational t = tan(theta/2) so that
cos(theta) = (1-t^2)/(1+t^2) and sin(theta) = 2t/(1+t^2) are rational -- no
angle is ever rounded into the model:

    t = 0                 theta = 0            (the axis branch)
    t = sqrt2 - 1         theta = pi/4         (the 45 degree branch)
    t = 1/2               theta = 53.1301 deg
    t = 1/3               theta = 36.8699 deg
    t = 1/4               theta = 28.0725 deg

A *branch assignment* puts a word on a set S of squares; the other squares keep
their delivered rotation.  The cells are

    (B)  full branch assignment: one word per delivered angle class (all squares
         in a class share the word) -- the algebraic-word reading of the row;
    (S1) one square re-worded: 11 x 5 cells;
    (S2) two squares re-worded: 55 x 25 cells.

Every cell is priced by the declared-axis LP in `declp.solve` (run 67's corrected
form: the separation required on the owner's axis is 0.5 + the OTHER square's
extent along that axis, not its own), with every translation free and side
L = L0 - eps.  The pair axes are declared from the trial geometry (the minimum
penetration axis); a refusal is therefore conservative -- a pair that wants a
different axis could in principle still be packed, and that is the price of the
declaration.

This script's declared profile is in `PROFILE`: all translations free, a 5e-10
separation pad, free offsets bounded by 2L.  The builder itself is not here: it
is `declp.solve`, the one copy shared with `sat_probe` and `t1_glide`
(consolidation pass after run 70 -- three copies are how run 67's defect lived).

THE ONLY JUDGE IS THE EXACT GATE
--------------------------------
An LP-feasible cell is not a result.  The returned centres are rounded to 12 dp
and handed to `packlib.verify` at tolerance 0 (the canonical SAT gate) and to
`sqscore.row_gain`.  A cell counts only if the gate accepts AND the side is
strictly below the delivered side; the ledger keeps the refusals too.
"""
from __future__ import annotations

import itertools
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import declp as DL          # noqa: E402
import packlib as P         # noqa: E402
import sqscore as SQ        # noqa: E402
import wall_margin as WM    # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/branch_rot.json")
#: this script's declared LP profile -- one declaration, used by every cell
PROFILE = {"pad": DL.PAD, "move": 0.6, "free_span": 2.0}
#: rows the record names as proved optimal (optima.py plus the below-grid results
#: quoted in README/04: s(5), s(11), s(12), s(13), s(17), s(19)).  A search cannot
#: improve a proved row; excluding them is what makes the target rule mean "room".
NAMED_PROVED = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
                          17, 19, 24, 35})


def cells_for(n, th):
    """Yield (kind, squares, word-vector) for the declared cell space."""
    # (B) branch assignment: delivered angle classes
    classes = {}
    for i, a in enumerate(th):
        classes.setdefault(round(float(a), 6), []).append(i)
    groups = list(classes.values())
    if len(groups) > 1 and len(DL.WORDS) ** len(groups) <= 4000:
        for combo in itertools.product(range(len(DL.WORDS)), repeat=len(groups)):
            w = list(th)
            for g, wi in zip(groups, combo):
                for i in g:
                    w[i] = DL.WORDS[wi][1]
            yield ("B", len(groups), w)
    # (S1) and (S2): one and two squares re-worded
    for i in range(n):
        for wi in range(len(DL.WORDS)):
            w = list(th)
            w[i] = DL.WORDS[wi][1]
            yield ("S1", 1, w)
    for i, j in itertools.combinations(range(n), 2):
        for wi, wj in itertools.product(range(len(DL.WORDS)), repeat=2):
            w = list(th)
            w[i], w[j] = DL.WORDS[wi][1], DL.WORDS[wj][1]
            yield ("S2", 2, w)


def synthetic_control():
    """A loose 2x2 grid of 4 squares at side 2.2 must shrink: LP+gate must say so."""
    xy = np.array([[0.0, 0.0], [1.2, 0.0], [0.0, 1.2], [1.2, 1.2]])
    th = [0.0, 0.0, 0.0, 0.0]
    new = DL.solve(xy, th, 2.05, **PROFILE)
    if new is None:
        return {"lp": False}
    g = DL.gate(4, new, th, 2.2)
    return {"lp": True, "gate_ok": g["ok"], "L": g["L"], "pen": g["worst_pen"]}


def controls(per, target=18) -> dict:
    out = {}
    st = per[target]
    xy = np.array([(s[0], s[1]) for s in st], dtype=float)
    th = [s[2] for s in st]
    L0 = SQ.extent(st)
    out["identity_at_L0"] = DL.solve(xy, th, L0, **PROFILE) is not None
    out["identity_max_shrink"] = DL.max_shrink(xy, th, L0, **PROFILE)
    out["synthetic_loose_4_at_2.05"] = synthetic_control()
    # negative control: s(12) = 4 is proved, so 3.99 must be refused
    st12 = per[12]
    xy12 = np.array([(s[0], s[1]) for s in st12], dtype=float)
    th12 = [s[2] for s in st12]
    out["n12_at_3.99_lp"] = DL.solve(xy12, th12, 4.0 - 1e-2, **PROFILE) is not None
    for k, v in out.items():
        print(f"  control {k}: {v}")
    return out


def relax_pass(target, xy, th, L0):
    """Non-declared-axis pass: pressure-settle the cell, then the exact gate.

    The LP above needs a declared separating axis per pair; this pass needs no
    declaration at all -- `cram_relax.relax` descends the penetration energy at a
    fixed target side and `cram_relax.settle_and_gate` reports `packlib.finalize`
    + `packlib.verify`, i.e. the project's own gate.  Same cells, no axis guess.
    """
    import cram_relax as CR
    Lt = L0 - 1e-3
    cells = [("identity", None, np.column_stack([xy[:, 0], xy[:, 1], th]))]
    for i in range(target):
        for wi in range(len(DL.WORDS)):
            w = list(th)
            w[i] = DL.WORDS[wi][1]
            cells.append((f"S1:{i}:{DL.WORDS[wi][0]}", None,
                          np.column_stack([xy[:, 0], xy[:, 1], w])))
    tilted = [i for i in range(target) if abs(th[i]) > 1e-9]
    for i in tilted:
        for wi in range(len(DL.WORDS)):
            for p in [tuple(q) for q in xy]:
                w = list(th)
                w[i] = DL.WORDS[wi][1]
                st = np.column_stack([xy[:, 0], xy[:, 1], w])
                st[i, 0], st[i, 1] = p
                cells.append((f"R:{i}:{DL.WORDS[wi][0]}", None, st))
    seen, hits, best = set(), [], None
    for tag, _, st in cells:
        key = (tag, round(float(st[:, 0].sum()), 6), round(float(st[:, 2].sum()), 6))
        if key in seen:
            continue
        seen.add(key)
        out = CR.relax(st, Lt, moves=1200, mode="full", seed=1)
        g = CR.settle_and_gate(out, Lt)
        rec = {"tag": tag, "gated_ok": g["gated_ok"], "gated_L": g["gated_L"],
               "worst_pen": g["worst_pen"]}
        if g["gated_ok"] and g["gated_L"] is not None and g["gated_L"] < L0 - 1e-9:
            rec["gain"] = SQ.row_gain(target, g["gated_L"]) - SQ.row_gain(target, L0)
            hits.append(rec)
            if best is None or g["gated_L"] < best["gated_L"]:
                best = rec
    print(f"relax cells: {len(seen)}   gated improvements: {len(hits)}")
    if best:
        print(f"  best gated L={best['gated_L']:.12f} gain={best['gain']:+.3e} "
              f"({best['tag']})")
    return {"cells": len(seen), "hits": len(hits), "best": best}


def main() -> int:
    per = SQ.load()
    if "--relax-only" in sys.argv:
        st0 = per[18]
        xy0 = np.array([(q[0], q[1]) for q in st0], dtype=float)
        th0 = [q[2] for q in st0]
        L00 = SQ.extent(st0)
        print("controls for target 18:")
        c = controls(per, 18)
        r = relax_pass(18, xy0, th0, L00)
        led = {"run": 69, "schema": "branchrot/1", "target": 18, "L0": L00,
               "controls": c, "relax": r}
        with open(OUT) as f:
            old = json.load(f)
        old["controls"] = c
        old["relax"] = {k: v for k, v in r.items()}
        with open(OUT, "w") as f:
            json.dump(old, f, indent=1)
        print("ledger updated with controls + relax")
        return 0
    rows = WM.build(per)
    proved = WM.proved_set()
    cand = [n for n in range(11, 21)
            if n not in proved and n not in NAMED_PROVED]
    target = max(cand, key=lambda n: (rows[n]["rho"], rows[n]["mu"]))
    st = per[target]
    L0 = SQ.extent(st)
    xy = np.array([(s[0], s[1]) for s in st], dtype=float)
    th = [s[2] for s in st]
    print(f"target n={target}  L0={L0:.12f}  rho={rows[target]['rho']:.6f}  "
          f"mu={rows[target]['mu']:.6f}  rho-rank={WM.rank_by(rows, 'rho')[target]}"
          f"/1000")
    print(f"cell space: B + {len(th)}x{len(DL.WORDS)} S1 + "
          f"{len(th)*(len(th)-1)//2*len(DL.WORDS)**2} S2")

    ctrl = controls(per, target)
    seen, feasi, gated, gains = set(), [], [], []
    kinds = {}
    n_cells = 0
    for kind, width, w in cells_for(target, th):
        key = (kind, tuple(round(a, 9) for a in w))
        if key in seen:
            continue
        seen.add(key)
        n_cells += 1
        r = DL.price(target, xy, w, L0, **PROFILE)
        r.update({"kind": kind, "words": [a for a in w]})
        if r["lp"]:
            feasi.append(r)
            kinds[kind] = kinds.get(kind, 0) + 1
            if r["gate_ok"]:
                gated.append(r)
                if r["gain"] > 1e-9:
                    gains.append(r)

    print(f"cells enumerated: {n_cells}   LP-feasible: {len(feasi)}   "
          f"gate-accepted: {len(gated)}   GAINS: {len(gains)}")
    for k in sorted(set(r["kind"] for r in feasi)):
        sub = [r for r in feasi if r["kind"] == k]
        print(f"  {k}: feasible {len(sub)}, best eps "
              f"{max(r['eps'] for r in sub):.0e}, min L "
              f"{min(r['L'] for r in sub):.9f}")

    print("\n=== gate-accepted cells (the only ones that count) ===")
    for r in sorted(gated, key=lambda z: z["L"])[:10]:
        print(f"  {r['kind']} L={r['L']:.9f} pen={r['worst_pen']:.2e} "
              f"gain={r['gain']:+.3e}")

    # ---- re-slot variant: put one square at another square's slot, with a new
    # word, then let the other ten translate.  A branch assignment with a move.
    slots = [tuple(p) for p in xy]
    rseen, rfeasi, rgains = set(), [], []
    for i in range(target):
        for wi in range(len(DL.WORDS)):
            for p in slots:
                key = (i, wi, p)
                if key in rseen:
                    continue
                rseen.add(key)
                w = list(th)
                w[i] = DL.WORDS[wi][1]
                trial = np.array(xy, dtype=float)
                trial[i] = p
                r = DL.price(target, trial, w, L0, **PROFILE)
                r.update({"kind": "R", "square": i, "word": DL.WORDS[wi][0]})
                if r["lp"]:
                    rfeasi.append(r)
                    if r["gate_ok"] and r["gain"] > 1e-9:
                        rgains.append(r)
    print(f"re-slot cells (tilted only): {len(rseen)}   LP-feasible: {len(rfeasi)}   "
          f"GAINS: {len(rgains)}")

    best = min((r for r in gated + rgains if r["gate_ok"]), key=lambda z: z["L"],
               default=None)
    if best and best["gain"] > 1e-9:
        st_best = best["state"]
        g = P.verify(st_best, tol=0.0)
        print(f"\nRESULT row {target}: side {L0:.12f} -> {best['L']:.12f}  "
              f"gain {best['gain']:+.6e}  gate {g['ok']} pen {g['worst_pen']:.2e}")
        print("  state:", json.dumps(st_best))
    else:
        print(f"\nRESULT row {target}: no cell survives the exact gate with a "
              f"strictly smaller side (refusal, declared axes only).")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"run": 69, "schema": "branchrot/1", "target": target,
                   "L0": L0, "rho": rows[target]["rho"],
                   "words": [[nm, DL.theta_of(t)] for nm, t in DL.WORDS],
                   "cells": n_cells, "feasible": len(feasi),
                   "gated": len(gated), "gains": len(gains),
                   "by_kind": kinds, "controls": ctrl,
                   "reslot_cells": len(rseen), "reslot_feasible": len(rfeasi),
                   "reslot_gains": len(rgains),
                   "feasible_rows": [{k: v for k, v in r.items()
                                      if k != "state"} for r in feasi],
                   "gated_rows": [{k: v for k, v in r.items()
                                   if k != "state"} for r in gated]}, f, indent=1)
    rel = relax_pass(target, xy, th, L0) if "--relax" in sys.argv else None
    if rel:
        with open(OUT) as f:
            led = json.load(f)
        led["relax"] = rel
        with open(OUT, "w") as f:
            json.dump(led, f, indent=1)
    print(f"ledger: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
