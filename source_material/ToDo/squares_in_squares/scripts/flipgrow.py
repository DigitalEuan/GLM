#!/usr/bin/env python3
r"""flipgrow.py — the queued card action, run: one branch flip plus free-set
expansion, on the slack-positive seed the wall-margin ranking leads to (run 71).

WHY THIS RUN EXISTS
-------------------
Run 70 ran the T1 branch flip with **every translation free** and the free set
fixed at the delivered tight pairs.  `33` §7 queued the one cell of the card it
never entered: a flip *combined with free-set expansion*, on a seed whose LP is
not already rigid at `L0`.  This is that run.

THE SEED CONDITION, MEASURED
----------------------------
"Slack at L0" is not the wall margin `mu = L - sqrt(n)`: mu is distance to the
area wall, and a row can have a large mu and still be pinned.  The thing the
action needs is a constraint system with room, and that is measured three ways:

  * **base depth** — the largest `eps` with `declp.solve(L0 - eps)` feasible on
    the delivered branches.  Run 69 measured 3.1e-8 at n = 18; this run measures
    it for every open row at n <= 60.
  * **flip seed** — the largest `eps` with `solve(L0 - eps, branch={(i,j): a})`
    feasible after one declared flip.  A flip that cannot absorb 1e-6 is not a
    seed: feasibility at `L0 - eps` decreases in `eps`, so the smallest `eps` is
    the cheapest *and* strongest test, and it is tested first.
  * **pad slack** — the largest `pad` with `solve(L0, pad=p)` feasible.  This is
    the row's interior room in the contact system, independent of shrinking
    (a pad demands *more* separation in the same box; a shrink demands the same
    separations in a smaller box -- related, not equivalent).

FREE-SET EXPANSION IS MONOTONE, AND THAT IS THE POINT
-----------------------------------------------------
Feasibility is monotone in the free set: any solution on a subset of the
variables is a solution on all of them.  So testing at "all free" is the
*strongest* form of the test, and the ladder (pair -> 1-ring -> 2-ring -> all)
can only ever find the smallest sufficient repair, never more room.  Therefore:

  * if no flip is feasible at `L0 - 1e-6` with every square free, then no flip is
    feasible on any smaller free set either, and the whole flip+expansion family
    is closed **by monotonicity**, not by a sample;
  * the ladder is only entered when a flip does pass, and then it answers a
    different question -- how small a repair suffices.

THE GATE IS THE ONLY JUDGE
--------------------------
`declp.price` is not used here because the seed is tested first; every state the
LP admits goes to `declp.gate` (12-dp state, `packlib.verify(tol=0)`, canonical
score).  LP feasibility alone is reported as `lp` and never as a result.

MODES
-----
    python3 scripts/flipgrow.py              # the run: all open rows n <= 60
    python3 scripts/flipgrow.py --census     # binding constraints vs 2n, n <= 120
    python3 scripts/flipgrow.py 18 39        # named rows only

Ledger: `workspace/push/flipgrow.json` (schema `flipgrow/1`).  It never writes the
submission.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import declp as DL          # noqa: E402
import sqscore as SQ        # noqa: E402
import t1_glide as T1       # noqa: E402
import wall_margin as WM    # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/flipgrow.json")
#: the row-search profile: every translation free, 5e-10 pad, offsets within 2L
PROFILE = {"pad": DL.PAD, "move": 0.6, "free_span": 2.0}
#: the cheapest and strongest seed test: this much shrink, then the ladder upward
SEED_EPS = 1e-6
#: a row's `mu` rank is the search order; the seed test decides


# ---------------------------------------------------------------- free sets
def adjacency(edges):
    adj = {}
    for i, j, _a in edges:
        adj.setdefault(i, set()).add(j)
        adj.setdefault(j, set()).add(i)
    return adj


def free_ladder(n, edges, i, j):
    """Nested free sets, smallest first: the pair, its rings, everything."""
    adj = adjacency(edges)
    s0 = {i, j}
    s1 = set(s0) | {k for v in s0 for k in adj.get(v, ())}
    s2 = set(s1) | {k for v in s1 for k in adj.get(v, ())}
    return [("pair", s0), ("1-ring", s1), ("2-ring", s2),
            ("all", set(range(n)))]


# ---------------------------------------------------------------- measurement
def _solve(xy, th, L, **kw):
    """`declp.solve` at this run's profile, with the caller's knobs on top."""
    return DL.solve(xy, th, L, **{**PROFILE, **kw})


def depth(xy, th, L0, branch=None, free=None):
    """Largest `eps` on the declared ladder with `L0 - eps` LP-feasible, or 0.0.

    Feasibility decreases in `eps`, so the ladder is walked from the smallest
    value upward and stops at the first refusal.
    """
    got = 0.0
    for eps in reversed(DL.EPS):
        if _solve(xy, th, L0 - eps, branch=branch, free=free) is None:
            continue
        got = eps
    return got


def pad_slack(xy, th, L0, branch=None, lo=0.0, hi=0.5, it=24):
    """Largest `pad` the declared system admits at `L0` (bisection)."""
    if _solve(xy, th, L0, branch=branch, pad=lo) is None:
        return 0.0
    for _ in range(it):
        mid = 0.5 * (lo + hi)
        if _solve(xy, th, L0, branch=branch, pad=mid) is None:
            hi = mid
        else:
            lo = mid
    return lo


def census(hi_n=120):
    """Binding constraints against degrees of freedom, per row.

    A row with more binding constraints than variables is over-determined: one
    flip cannot open room in it.  Counting is a pointer only -- redundancy and
    the geometry decide -- but it says which rows are worth the LP.
    """
    per = SQ.load()
    rows = WM.build(per)
    out = []
    for n in range(4, hi_n + 1):
        st = per[n]
        xy, th, cs, sn = DL.frames(st)
        L0 = rows[n]["L"]
        S = DL.tables(xy, th)[3]
        a = np.argmin(S, axis=0)
        pen = np.take_along_axis(S, a[None, :, :], axis=0)[0]
        if abs(rows[n]["mu"] - (L0 - float(np.sqrt(n)))) > 1e-9:
            raise AssertionError(f"n={n}: wall margin disagrees with the table")
        contacts = int(((pen >= -DL.CONTACT)
                        & np.triu(np.ones((n, n), bool), 1)).sum())
        ex = 0.5 * (np.abs(cs) + np.abs(sn))
        lox, hix = (xy[:, 0] - ex).min(), (xy[:, 0] + ex).max()
        loy, hiy = (xy[:, 1] - ex).min(), (xy[:, 1] + ex).max()
        walls = int(np.isclose(xy[:, 0] + ex, hix, atol=1e-9).sum()
                    + np.isclose(xy[:, 0] - ex, lox, atol=1e-9).sum()
                    + np.isclose(xy[:, 1] + ex, hiy, atol=1e-9).sum()
                    + np.isclose(xy[:, 1] - ex, loy, atol=1e-9).sum())
        out.append({"n": n, "vars": 2 * n, "contacts": contacts,
                    "walls": walls, "binding": contacts + walls,
                    "slack_by_count": contacts + walls - 2 * n,
                    "mu": rows[n]["mu"]})
    return out


def run_row(n, per, rows, deadline):
    """Test every single declared flip on one row, seed first, gate last."""
    st = per[n]
    xy, th, _cs, _sn = DL.frames(st)
    L0 = rows[n]["L"]
    E = T1.contacts(xy, th)
    ext, _box = T1.extreme_squares(xy, th)
    keep = [e for e in E if e[0] in ext or e[1] in ext]
    rec = {"n": n, "L0": L0, "mu": rows[n]["mu"], "rank_mu": None,
           "contacts": len(E), "edges_at_extreme": len(keep),
           "base_depth": depth(xy, th, L0),
           "base_pad": pad_slack(xy, th, L0),
           "flips": 0, "seeds": [], "cells": 0, "lp": 0, "gated": 0,
           "gains": [], "best_flip_pad": 0.0, "timed_out": False}
    for i, j, a in keep:
        for a2 in range(4):
            if a2 == a:
                continue
            if time.time() > deadline:
                rec["timed_out"] = True
                return rec
            br = {(i, j): a2}
            rec["flips"] += 1
            if _solve(xy, th, L0 - SEED_EPS, branch=br) is None:
                continue
            # a seed: no smaller free set can do better, so expand only here
            rec["seeds"].append([i, j, a, a2])
            for label, free in free_ladder(n, E, i, j):
                for eps in DL.EPS:
                    rec["cells"] += 1
                    new = _solve(xy, th, L0 - eps, branch=br, free=free)
                    if new is None:
                        continue
                    g = DL.gate(n, new, th, L0)
                    rec["lp"] += 1
                    if g["ok"] and g["gain"] > 1e-9:
                        rec["gated"] += 1
                        rec["gains"].append(
                            {"edge": [i, j], "from": a, "to": a2,
                             "free": label, "free_size": len(free),
                             "eps": eps, "L": g["L"], "gain": g["gain"]})
                    break           # largest admitted shrink on the ladder
    return rec


def control():
    """Show the seed test and the gate can fire, and that they also refuse.

    A test that only ever refuses is not evidence.  Three cases:

    * a loose 2x2 grid at side 2.2 -- `depth` must report 1e-2, so the shrink
      measurement is not stuck at zero by construction;
    * the same grid with one contact edge flipped onto each alternative branch
      at `L0 - 1e-6` -- the *seed test itself* must return a state and the gate
      must accept it, so the path seed -> ladder -> gate is live;
    * two unit squares at their exact optimum (side 2.0) -- base and every flip
      must refuse `L0 - 1e-6`, so the test is not permissive: at a tight
      configuration nothing passes, which is the shape of the run's result.
    """
    xy = np.array([[0.0, 0.0], [1.2, 0.0], [0.0, 1.2], [1.2, 1.2]])
    th = [0.0, 0.0, 0.0, 0.0]
    loose = depth(xy, th, 2.2)
    print(f"control loose 2x2 at 2.2      : base depth {loose:.0e} (must be 1e-02)")

    live = []
    S = DL.tables(xy, th)[3]
    a = int(np.argmin(S[:, 0, 1]))
    for a2 in range(4):
        if a2 == a:
            continue
        new = _solve(xy, th, 2.2 - SEED_EPS, branch={(0, 1): a2})
        if new is None:
            continue
        g = DL.gate(4, new, th, 2.2)
        if g["ok"] and g["gain"] > 0:
            live.append({"edge": [0, 1], "from": a, "to": a2, "L": g["L"],
                         "gain": g["gain"]})
    print(f"control flipped loose grid    : {len(live)} of 3 branches seed and "
          f"GATE (must be at least 1)")

    xy2 = np.array([[-0.5, 0.0], [0.5, 0.0]])
    th2 = [0.0, 0.0]
    base2 = _solve(xy2, th2, 2.0 - SEED_EPS) is not None
    anyflip = any(_solve(xy2, th2, 2.0 - SEED_EPS, branch={(0, 1): b}) is not None
                  for b in range(4))
    print(f"control touching pair at 2.0  : base "
          f"{'feasible' if base2 else 'REFUSED'} (must be refused), any flip "
          f"{'feasible' if anyflip else 'REFUSED'} (must be refused)")
    return {"loose_grid_depth": loose, "flipped_loose_grid": live,
            "touching_base_feasible": base2, "touching_any_flip": anyflip}


def main() -> int:
    args = sys.argv[1:]
    if "--control" in args:
        ctrl = control()
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        old = {}
        if os.path.exists(OUT):
            try:
                old = json.load(open(OUT))
            except Exception:               # noqa: BLE001
                old = {}
        old["control"] = ctrl
        old.setdefault("run", 71)
        old.setdefault("schema", "flipgrow/1")
        with open(OUT, "w") as f:
            json.dump(old, f, indent=1)
        print(f"ledger: {OUT}")
        return 0
    if "--census" in args:
        out = census()
        cands = [r for r in out if r["slack_by_count"] <= 1]
        print(f"{'n':>4} {'vars':>4} {'contacts':>8} {'walls':>5} {'binding':>7} "
              f"{'over':>6}")
        for r in out:
            if r["n"] in (11, 12, 18, 20, 30, 39, 60, 100, 120) or r in cands:
                print(f"{r['n']:4d} {r['vars']:4d} {r['contacts']:8d} "
                      f"{r['walls']:5d} {r['binding']:7d} "
                      f"{r['slack_by_count']:6d}{'  candidate' if r in cands else ''}")
        print(f"\nrows 4..120: {len(out)}; not over-determined by count: "
              f"{[r['n'] for r in cands]}")
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        path = OUT.replace(".json", "_census.json")
        with open(path, "w") as f:
            json.dump({"run": 71, "schema": "flipgrow-census/1", "rows": out}, f,
                      indent=0)
        print(f"ledger: {path}")
        return 0

    global SEED_EPS
    if "--seed-eps" in args:
        i = args.index("--seed-eps")
        SEED_EPS = float(args[i + 1])
        args = args[:i] + args[i + 2:]
    t0 = time.time()
    deadline = t0 + 240.0                 # stay inside the tool's own cap
    per = SQ.load()
    rows = WM.build(per)
    proved = WM.proved_set()
    named = [int(a) for a in args if a.isdigit()]
    if named:
        todo = named
    else:
        todo = [n for n in range(4, 61) if n not in proved]
        todo.sort(key=lambda n: rows[n]["mu"], reverse=True)
    rank_mu = WM.rank_by(rows, "mu")
    print(f"open rows tested: {len(todo)}; order = wall margin mu (largest "
          f"first); seed test = LP at L0 - {SEED_EPS:.0e}, all free")
    print(f"{'n':>4} {'mu':>8} {'rank':>5} {'edges':>5} {'base_dep':>9} "
          f"{'flips':>6} {'seeds':>5} {'gated':>5}")
    out = []
    for n in todo:
        rec = run_row(n, per, rows, deadline)
        rec["rank_mu"] = rank_mu[n]
        out.append(rec)
        print(f"{n:4d} {rec['mu']:8.5f} {rec['rank_mu']:5d} "
              f"{rec['edges_at_extreme']:5d} {rec['base_depth']:9.0e} "
              f"{rec['flips']:6d} {len(rec['seeds']):5d} {rec['gated']:5d}"
              f"{'  (deadline)' if rec['timed_out'] else ''}")
        if rec["timed_out"]:
            print("deadline reached: rows after this one were not tested")
            break
    flips = sum(r["flips"] for r in out)
    seeds = sum(len(r["seeds"]) for r in out)
    gains = sum(len(r["gains"]) for r in out)
    print(f"\nrows {len(out)}  flips {flips}  seeds {seeds}  "
          f"cells {sum(r['cells'] for r in out)}  gated {sum(r['gated'] for r in out)}"
          f"  GAINS {gains}")
    print(f"elapsed {time.time() - t0:.1f}s")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    old = {}
    if os.path.exists(OUT):
        try:
            old = {r["n"]: r for r in json.load(open(OUT)).get("rows", [])}
        except Exception:                   # noqa: BLE001
            old = {}
    for r in out:
        old[r["n"]] = r
    with open(OUT, "w") as f:
        json.dump({"run": 71, "schema": "flipgrow/1",
                   "profile": PROFILE, "seed_eps": SEED_EPS,
                   "order": "wall margin mu, largest first",
                   "rows": [old[k] for k in sorted(old)]}, f, indent=1)
    print(f"ledger: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
