#!/usr/bin/env python3
r"""sweep23.py — run 23: audit + tight-target soft-relaxation sweep.

USER QUESTIONS THIS RUN:
  Q2: README.md not received (delivery-pattern bug: run 22 nested it
      only under download/run22/; fixed this run with a top-level
      download/README.md refresh).
  Q3: did run 22 move submission.csv or the score?
      Part 0 answers with evidence (write footprint + content hashes +
      CSV-vs-table score recomputation).

FACTS (audit, this run):
  - run 22 wrote only workspace/push/soft_relax*.json; table.json
    content dates to 08:03 today (run18-frontier application write,
    commit a163ab8 09:22); download copies are byte-identical
    (sha256).  Score 22.887470936 (leech snapshot, 08:02) ->
    22.823536149 (08:03 write) happened BEFORE run 22 (22:18).
  - leech_map.py reads download/table.json: the 'atlas' is our own
    table one minute earlier; the run-22 'beat the atlas' claim was
    circular (it was run 19's application delta).
  - 546 rows sit at the trivial grid (all level-1, believed infeasible
    below); 6 former level-1 rows were cracked at 08:03 by
    run18-frontier finds, all by 0.0004..0.0065 -> the level-1
    frontier is JUST below the grid, so the ladder is
    grid-0.0005 / -0.002 / -0.01.

SWEEP (Part 1): 12 top-waste at-grid rows
  {2, 6, 7, 8, 13, 14, 21, 22, 23, 30, 42, 56}
  (waste = grid/sqrt(n)-1 rank order; includes ROOTS members
   21, 30, 42, 56; 12 and 20 were probed in run 22),
  x 3 targets (grid-0.0005, grid-0.002, grid-0.01)
  x 2 seeds x 8 hops (soft_relax.hop_search: SA pass-through shuffle
  + settle_to L-BFGS re-hardening).

FIND CRITERION: finalize_gate-verified L < min(grid, table L) - 1e-9.
APPLICATION (only if finds): table.json best-L-wins, src soft23, then
the repo chain cascade3 -> closure_apply -> final_assembly rebuilds
submission.csv; download copies refreshed; score recomputed.
"""
import json
import math
import os
import re
import sys
import time

import numpy as np

sys.path.insert(0, "/home/z/my-project/scripts")
import packlib as P
from sa_push import anneal  # noqa: F401 (channel reprt)
from soft_relax import hop_search
from engine_variants import finalize_gate

W = "/home/z/my-project"
TAB = f"{W}/workspace/submission/table.json"
CSV = f"{W}/workspace/submission/submission.csv"
OUT = f"{W}/workspace/push/sweep23.json"

ROWS = [2, 6, 7, 8, 13, 14, 21, 22, 23, 30, 42, 56]
LADDER = [0.0005, 0.002, 0.01]
SEEDS = 2


def grid(n):
    return math.ceil(math.sqrt(n))


# ------------------------------------------------------------- Part 0
def audit():
    tab = json.load(open(TAB))
    print("== Part 0: consistency audit ==")
    # score from table
    s_tab = sum(r["L"] / math.sqrt(int(k)) - 1 for k, r in tab.items())
    # score from submission.csv (independent parse + P.verify)
    by_n = {}
    with open(CSV) as f:
        next(f)
        for line in f:
            _, n, _, x, y, a = line.split(",")
            by_n.setdefault(int(n), []).append(
                (float(x), float(y), float(a)))
    s_csv = 0.0
    worst = 0.0
    for n, st in by_n.items():
        r = P.verify(st)
        worst = max(worst, r["worst_pen"])
        s_csv += r["L"] / math.sqrt(n) - 1
    print(f"  rows in csv: {len(by_n)} | table rows: {len(tab)}")
    print(f"  score from table:        {s_tab:.9f}")
    print(f"  score from submission.csv (P.verify): {s_csv:.9f}")
    print(f"  max pair penetration in csv states: {worst:.2e} "
          f"({'non-overlapping' if worst <= 0 else 'OVERLAP!'})")
    print(f"  in sync: {abs(s_tab - s_csv) < 1e-9}")
    # the 6 cracked level-1 rows (context for the ladder)
    leech = json.load(open(f"{W}/json/leech_map.json"))
    lv1 = [r for r in leech["rows"] if r["level"] == 1]
    cracked = [(r["n"], tab[str(r["n"])]["L"]) for r in lv1
               if tab[str(r["n"])]["L"] < grid(r["n"]) - 1e-5]
    print(f"  former level-1 rows now below grid: {len(cracked)}: "
          + ", ".join(f"n={n} (L {L:.7f})" for n, L in cracked))
    return s_tab, s_csv


# ------------------------------------------------------------- Part 1
def sweep():
    tab = json.load(open(TAB))
    cells, finds = [], []
    t0 = time.time()
    for n in ROWS:
        g = grid(n)
        tabL = tab[str(n)]["L"]
        for dL in LADDER:
            L_t = g - dL
            cell = {"n": n, "grid": g, "target": L_t,
                    "hard_hops": 0, "best_hard_L": None,
                    "verified": None, "state": None}
            best_state = None
            for s in range(1, SEEDS + 1):
                seed = 7919 * n + 104729 * s + int(round(dL * 1e6))
                best, hh, ck = hop_search(n, L_t, seed)
                cell["hard_hops"] += hh
                if best and (cell["best_hard_L"] is None
                             or best[0] < cell["best_hard_L"]):
                    cell["best_hard_L"] = round(best[0], 12)
                    best_state = best[1]
            if best_state is not None:
                hit = finalize_gate(best_state, cell["best_hard_L"] + 1e-6)
                if hit:
                    cell["verified"] = hit["verified_L"]
                    cell["state"] = hit["state"]
                    if hit["verified_L"] < min(g, tabL) - 1e-9:
                        finds.append({"n": n, "grid": g,
                                      "old": tabL,
                                      "L": hit["verified_L"],
                                      "target": L_t,
                                      "state": hit["state"],
                                      "src": "soft23"})
            cells.append(cell)
            v = (f"VERIFIED {cell['verified']:.9f}"
                 if cell["verified"] else
                 (f"hard {cell['best_hard_L']:.9f} (not applicable)"
                  if cell["best_hard_L"] else "no hard state"))
            print(f"  n={n:3d} grid={g:2d} target {L_t:.4f}: "
                  f"hard_hops {cell['hard_hops']}/{SEEDS*4} | {v} | "
                  f"{time.time()-t0:.0f}s", flush=True)
            json.dump({"cells": cells, "finds": [
                {k: f[k] for k in ('n', 'grid', 'old', 'L', 'target')}
                for f in finds]},
                open(OUT, "w"), indent=1)
    return cells, finds


# ------------------------------------------------------------- Part 2
def apply(finds):
    if not finds:
        print("no applicable finds — table unchanged (honest).")
        return False
    tab = json.load(open(TAB))
    for f in sorted(finds, key=lambda f: f["n"]):
        if f["L"] < tab[str(f["n"])]["L"] - 1e-9:
            tab[str(f["n"])] = {"L": f["L"], "state": f["state"],
                                "src": f"soft23:grid{f['grid']}"}
            print(f"  applied n={f['n']}: {f['old']:.9f} -> {f['L']:.9f}")
    json.dump(tab, open(TAB, "w"))
    import subprocess
    for cmd in ("scripts/cascade3.py", "scripts/closure_apply.py",
                "scripts/final_assembly.py"):
        r = subprocess.run([sys.executable, f"{W}/{cmd}"],
                           capture_output=True, text=True)
        print(" ", cmd, "->", (r.stdout or r.stderr).strip().split("\n")[-1])
    return True


def main():
    s_tab, s_csv = audit()
    print("\n== Part 1: sweep (12 rows x 3 targets x 2 seeds x 8 hops) ==")
    cells, finds = sweep()
    print(f"\n== Part 2: application ==")
    changed = apply(finds)
    tab = json.load(open(TAB))
    s_new = sum(r["L"] / math.sqrt(int(k)) - 1 for k, r in tab.items())
    print(f"\nfinds: {len(finds)} | table changed: {changed}")
    print(f"score: before-run {s_tab:.9f} -> now {s_new:.9f}")
    json.dump({"audit": {"score_table": s_tab, "score_csv": s_csv},
               "cells": [{k: c[k] for k in
                          ('n', 'grid', 'target', 'hard_hops',
                           'best_hard_L', 'verified')} for c in cells],
               "finds": [{k: f[k] for k in
                          ('n', 'grid', 'old', 'L', 'target')} for f in finds],
               "applied": changed,
               "score_after": s_new},
              open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
