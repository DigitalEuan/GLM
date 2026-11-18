#!/usr/bin/env python3
r"""t1_glide.py — the T1 / SAT-axis-branch flip, implemented (run 70).

The contract in `33-CENT-CONTRACT-T1-GLIDE.md` asks for a discrete change to the
*contact topology*: not a new tilt, not a new position, but a different choice of
which axis (and which owner) separates each tight pair.  That is a degree of
freedom run 69 did not touch -- there the axis per pair was re-derived from the
trial geometry; here the branch is chosen by name and the LP is rebuilt from it.

THE DISJUNCTION
---------------
For a pair (i,j) SAT requires SOME axis of either square to separate them:

    a = 0: u_i    a = 1: v_i    a = 2: u_j    a = 3: v_j

With the branch `a` frozen, the constraint is linear in the translations:

    sgn * ((c_j + D_j) - (c_i + D_i)) . q  >=  0.5 + ext_q(the other square)

where q is the chosen axis and `sgn` is the side of the delivered state.  The
delivered branch is the one that minimises penetration (`argmin` of the four).
A T1 flip reassigns the branch on a contact edge and lets every square translate.

The builder and the gate are `declp.solve` / `declp.gate` -- one copy, shared
with `sat_probe` and `branch_rot` (consolidation pass after run 70; three copies
of this constraint system is how run 67's defect survived review).  This script's
profile is in `PROFILE`: every translation free, 5e-10 pad, offsets bounded by 2L.

CELLS (per row)
---------------
  base        delivered branches (the control: the run-67 fixed point)
  flip1       one contact edge incident to an extreme achiever, each of the 3
              alternative branches
  flip2       two such edges flipped together (capped, deterministic order)
  flip1+word  the flip plus one endpoint re-worded from the exact alphabet

Every cell is priced at L0 - eps for eps in {1e-2, 3e-3, 1e-3, 1e-4, 1e-6} with
a 5e-10 separation pad, and the survivors go to the exact gate: 12-dp state,
`packlib.verify(..., tol=0.0)`, `sqscore.row_gain`.  LP feasibility alone is not
a result.

What this cannot do: a branch belongs to a pair, and a pair is named by index;
an axis flip that would require a *new* contact to exist (a non-contact pair
becoming the separating one) is not in the cell space, and refusals remain
conservative because the branch is declared rather than searched.
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
import sqscore as SQ        # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/t1_glide.json")
#: this script's declared LP profile -- one declaration, used by every cell
PROFILE = {"pad": DL.PAD, "move": 0.6, "free_span": 2.0}


# ------------------------------------------------------------------- geometry
def contacts(xy, th):
    """(i, j, branch) for every pair at contact.

    The predicate is `pen >= -CONTACT`, not `pen <= +CONTACT`: the wrong sign
    reports every pair as tight (run 70's audit caught it at 100 %).
    """
    S = DL.tables(xy, th)[3]
    n = len(xy)
    out = []
    for i in range(n):
        for j in range(i + 1, n):
            a = int(np.argmin(S[:, i, j]))
            if float(S[a, i, j]) >= -DL.CONTACT:
                out.append((i, j, a))
    return out


def extreme_squares(xy, th):
    cs, sn = np.cos(th), np.sin(th)
    ex = 0.5 * (np.abs(cs) + np.abs(sn))
    lox, hix = (xy[:, 0] - ex).min(), (xy[:, 0] + ex).max()
    loy, hiy = (xy[:, 1] - ex).min(), (xy[:, 1] + ex).max()
    out = []
    for i in range(len(xy)):
        if min(abs(xy[i, 0] - ex[i] - lox), abs(xy[i, 0] + ex[i] - hix),
               abs(xy[i, 1] - ex[i] - loy), abs(xy[i, 1] + ex[i] - hiy)) < 1e-9:
            out.append(i)
    return out, (float(lox), float(hix), float(loy), float(hiy))


# ---------------------------------------------------------------- price / gate
def price(n, xy, th, L0, branch):
    """The shared ladder, in this script's ledger vocabulary (`pen`, `branch`)."""
    r = DL.price(n, xy, th, L0, branch=branch, **PROFILE)
    if not r.get("lp"):
        return r
    rec = {"eps": r["eps"], "lp": True, "gate_ok": r["gate_ok"], "L": r["L"],
           "pen": r["worst_pen"], "gain": r["gain"],
           "branch": {f"{i},{j}": a for (i, j), a in branch.items()}}
    if "state" in r:
        rec["state"] = r["state"]
    return rec


def cells(edges, words, cap2=420):
    """base, single flips, double flips (capped), flip+word."""
    for i, j, a in edges:
        for a2 in range(4):
            if a2 != a:
                yield "flip1", {(i, j): a2}
                for nm, t in words:
                    yield "flip1+word", {(i, j): a2}, (i, t), nm
    combos = list(itertools.combinations(range(len(edges)), 2))[:cap2]
    for x, y in combos:
        i, j, a = edges[x]
        k, l, c = edges[y]
        for a2 in range(4):
            if a2 == a:
                continue
            for c2 in range(4):
                if c2 == c:
                    continue
                yield "flip2", {(i, j): a2, (k, l): c2}


def run_row(n, cap2=420):
    per = SQ.load()
    st = per[n]
    xy = np.array([(s[0], s[1]) for s in st], dtype=float)
    th = [s[2] for s in st]
    L0 = SQ.extent(st)
    E = contacts(xy, th)
    ext, box = extreme_squares(xy, th)
    keep = [e for e in E if e[0] in ext or e[1] in ext]
    print(f"n={n:4d} L0={L0:.9f} contacts={len(E)}/{n*(n-1)//2} "
          f"extreme={len(ext)} edges-at-extreme={len(keep)}")
    base = price(n, xy, th, L0, {})
    print(f"  base (delivered branches): lp={base['lp']} gate={base['gate_ok']} "
          f"eps={base['eps']}")
    seen, feas, gated, gains = set(), [], [], []
    for cell in cells(keep, DL.WORDS, cap2):
        kind, br = cell[0], cell[1]
        if kind == "flip1+word":
            sq, t = cell[2]
            w = list(th)
            w[sq] = t
            key = (kind, tuple(sorted(br.items())), sq, round(t, 9))
        else:
            w = th
            key = (kind, tuple(sorted(br.items())))
        if key in seen:
            continue
        seen.add(key)
        r = price(n, xy, w, L0, br)
        r["kind"] = kind
        if r["lp"]:
            feas.append(r)
            if r["gate_ok"] and r["gain"] > 1e-9:
                gated.append(r)
                gains.append(r)
    print(f"  cells={len(seen)} lp-feasible={len(feas)} gate-accepted={len(gated)} "
          f"GAINS={len(gains)}")
    for k in sorted(set(r["kind"] for r in feas)):
        sub = [r for r in feas if r["kind"] == k]
        print(f"    {k}: {len(sub)} feasible, best eps {max(r['eps'] for r in sub):.0e}, "
              f"min L {min(r['L'] for r in sub):.9f}")
    return {"n": n, "L0": L0, "contacts": len(E), "extreme": len(ext),
            "edges_at_extreme": len(keep), "base": {k: v for k, v in base.items()
                                                    if k != "state"},
            "cells": len(seen), "feasible": len(feas), "gated": len(gated),
            "gains": [{k: v for k, v in r.items() if k != "state"} for r in gains],
            "feasible_rows": [{k: v for k, v in r.items() if k != "state"}
                              for r in feas]}


def control():
    """Two controls: the base path shrinks a loose grid, and a *flipped* branch is
    realizable when geometry allows it (two stacked squares re-separated on x)."""
    xy = np.array([[0.0, 0.0], [1.2, 0.0], [0.0, 1.2], [1.2, 1.2]])
    th = [0.0, 0.0, 0.0, 0.0]
    base = price(4, xy, th, 2.2, {})
    print(f"control base loose-4 shrink: lp={base['lp']} gate={base['gate_ok']} "
          f"L={base.get('L')} (target {2.2 - base['eps'] if base['eps'] else None})")
    # flip realizability: A(0,0), B(0,1) separated on y.  Force the x-axis branch.
    # At side 2.001 the pair fits (x = +-0.5); at 1.5 no branch fits.
    xy2 = np.array([[0.0, 0.0], [0.0, 1.0]])
    th2 = [0.0, 0.0]
    got = DL.solve(xy2, th2, 2.001, branch={(0, 1): 0}, **PROFILE)
    if got is None:
        ok2 = {"lp": False, "gate_ok": False, "L": None}
    else:
        g = DL.gate(2, got, th2, 2.0)
        ok2 = {"lp": True, "gate_ok": g["ok"], "L": g["L"], "pen": g["worst_pen"]}
    bad2 = {"lp": DL.solve(xy2, th2, 1.5, branch={(0, 1): 0}, **PROFILE)
            is not None}
    print(f"control flip at L=2.001: lp={ok2['lp']} gate={ok2['gate_ok']} "
          f"L={ok2.get('L')} | at L=1.5: lp={bad2['lp']} (must be False)")
    return {"base": {k: v for k, v in base.items() if k != "state"},
            "flip_at_2.001": ok2, "flip_at_1.5": bad2}


def main() -> int:
    args = sys.argv[1:]
    cap2 = 420
    if "--cap2" in args:
        i = args.index("--cap2")
        cap2 = int(args[i + 1])
        args = args[:i] + args[i + 2:]
    rows = [int(a) for a in args if a.isdigit()] or [18, 20]
    ctrl = control()
    if "--control-only" in args:
        return 0
    out = [run_row(n, cap2) for n in rows]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    merged = {o["n"]: o for o in out}
    if os.path.exists(OUT):                     # keep rows from earlier invocations
        try:
            old = json.load(open(OUT))
            for o in old.get("rows", []):
                merged.setdefault(o["n"], o)
        except Exception:                       # noqa: BLE001
            pass
    with open(OUT, "w") as f:
        json.dump({"run": 70, "schema": "t1glide/1", "control": ctrl,
                   "rows": [merged[k] for k in sorted(merged)]}, f, indent=1)
    tot = sum(o["cells"] for o in out)
    gan = sum(len(o["gains"]) for o in out)
    print(f"total cells {tot}  total gains {gan}")
    print(f"ledger: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
