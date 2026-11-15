#!/usr/bin/env python3
r"""p2_seed_polish.py — run 24 / NEXT_STEPS P2: motif-seeded polish.

P2 (NEXT_STEPS §4): "take the top near-misses, seed with the family
state at s = grid + gap, and run contact-graph re-settling."
OPEN because hop_search (runs 22-23) seeds only from rsa_seed random
states — never from family states.  Run 23 got 0/288 on these rows
with random seeds; this run is the A/B: same hop loop, same seed
formula (identical anneal streams), ONLY the initial state differs
(rebuilt gobel5 corner-band design instead of rsa_seed random).

Rows: per-n best-gap designs from the gobel5 near-miss pool
      (workspace/push/gobel5_results.json, 8489 entries), gap <= 0.002,
      minus externally-proven-optimal rows (Atlas bounds 2026-10-17:
      s(13)=4, s(21)=5, s(32)=6, s(45)=7, s(60)=s(61)=8 — attacking
      those below grid is provably futile, so they are excluded and
      the compute goes to the genuinely open rows).
Targets: grid-0.0005 and grid-0.002 (run 23's two tightest).
Seeds: 2 per cell.  Hops: 8 per seed (4 hard checks each), identical
      to soft_relax.hop_search.
Find: finalize_gate-verified L < min(grid, table L) - 1e-9.
Apply: best-L-wins -> cascade3 -> closure_apply -> final_assembly.
"""
import json
import math
import os
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, "/home/z/my-project/scripts")
import packlib as P
from gobel5 import build, ANGLES
from oracle_basin import settle_to
from sa_push import anneal
from engine_variants import finalize_gate
from soft_relax import MOVES, PHI, unpack

W = "/home/z/my-project"
TAB = f"{W}/workspace/submission/table.json"
OUT = f"{W}/workspace/push/p2_seed_polish.json"

PROVEN = {13: 4, 21: 5, 32: 6, 45: 7, 60: 8, 61: 8}  # Atlas-verified s(n)
LADDER = (0.0005, 0.002)


def grid_L(n):
    return math.ceil(math.sqrt(n))


def rebuild_state(e, n):
    """Pick the ANGLES entry whose rounded degrees == th_deg (pool rounds
    to 3 dp; ANGLES rounds atan2 to 6 dp — an ulp difference that flips
    marginal fills).  Prefer the candidate whose count == n; fall back
    to the first build that returns (the count check flags it)."""
    cands = [a for a in ANGLES
             if round(math.degrees(a), 3) == e["th_deg"]]
    if not cands:
        cands = [math.radians(e["th_deg"])]
    fallback = None
    for a in cands:
        r = build(a, e["H"], e["W"], e["xlo"], e["ylo"])
        if r is None:
            continue
        if fallback is None:
            fallback = r
        if len(r[1]) == n:
            return r
    return fallback


def family_hop(n, L_t, seed, q0):
    """Identical loop to soft_relax.hop_search, but seeded q0 (family)."""
    q = q0.copy()
    best = None
    hard = 0
    checked = 0
    for h in range(8):
        if h == 0:
            q, f = settle_to(q, L_t, iters=250)
        elif h % 2 == 1:
            X, Y, TH = unpack(q)
            anneal(X, Y, TH, L_t, MOVES, seed * 1009 + h,
                   t0=0.30 if (h // 2) % 2 == 0 else 0.45,
                   tend=0.02, rotate_frac=0.5)
            q = np.concatenate([X, Y, TH])
            continue
        else:
            q, f = settle_to(q, L_t, iters=250)
        checked += 1
        THn = q[2 * n:] % PHI
        st = [(float(q[i]), float(q[n + i]), float(THn[i])) for i in range(n)]
        r = P.verify(st, tol=1e-9)
        if r["worst_pen"] <= -1e-10:
            hard += 1
            if best is None or r["L"] < best[0]:
                best = (float(r["L"]), q.copy())
    return best, hard, checked


def pack(state):
    X = np.array([s[0] for s in state])
    Y = np.array([s[1] for s in state])
    TH = np.array([s[2] for s in state])
    return np.concatenate([X, Y, TH])


def main():
    tab = json.load(open(TAB))
    pool = json.load(open(f"{W}/workspace/push/gobel5_results.json"))["nearmiss"]
    best_design = {}
    for e in pool:
        if e["n"] not in best_design or e["gap"] < best_design[e["n"]]["gap"]:
            best_design[e["n"]] = e
    rows = sorted(n for n, e in best_design.items()
                  if e["gap"] <= 0.002 and n not in PROVEN)
    print(f"rows: {rows}")
    print(f"({len(best_design)} distinct n in pool; "
          f"{len([n for n in best_design if best_design[n]['gap'] <= 0.002])} "
          f"at gap<=0.002; {len(PROVEN)} proven-optimal excluded)", flush=True)

    # rebuild + verify every family seed state first (honest gate)
    seeds_q0, rebuild_log = {}, []
    for n in rows:
        e = best_design[n]
        r = rebuild_state(e, n)
        if r is None:
            rebuild_log.append({"n": n, "ok": False, "why": "build None"})
            continue
        s, state = r
        v = P.verify(state, tol=1e-9)
        want = grid_L(n) + e["gap"]
        ok = (len(state) == n and v["worst_pen"] <= 1e-9
              and abs(v["L"] - want) <= 0.005)
        # note: worst_pen can be +1e-16 float artifacts on exact geometry;
        # the gate is tol=1e-9 (same as P.verify), not <= 0.
        rebuild_log.append({"n": n, "ok": ok, "count": len(state),
                            "verify_L": round(v["L"], 9), "want": round(want, 9),
                            "worst_pen": float(v["worst_pen"])})
        if ok:
            seeds_q0[n] = pack(state)
    bad = [r for r in rebuild_log if not r["ok"]]
    print(f"rebuilds: {len(seeds_q0)}/{len(rows)} ok"
          + (f" | BAD: {bad}" if bad else ""), flush=True)
    json.dump({"rebuilds": rebuild_log}, open(OUT, "w"), indent=1)

    cells, finds = [], []
    t0 = time.time()
    for n in rows:
        if n not in seeds_q0:
            continue
        g = grid_L(n)
        tabL = tab[str(n)]["L"]
        for dL in LADDER:
            L_t = g - dL
            cell = {"n": n, "grid": g, "target": L_t, "hard_checks": 0,
                    "best_hard_L": None, "verified": None}
            best_state = None
            for s in (1, 2):
                seed = 7919 * n + 104729 * s + int(round(dL * 1e6))
                best, hh, ck = family_hop(n, L_t, seed, seeds_q0[n])
                cell["hard_checks"] += hh
                if best and (cell["best_hard_L"] is None
                             or best[0] < cell["best_hard_L"]):
                    cell["best_hard_L"] = round(best[0], 12)
                    best_state = best[1]
            if best_state is not None:
                hit = finalize_gate(best_state, cell["best_hard_L"] + 1e-6)
                if hit:
                    cell["verified"] = hit["verified_L"]
                    if hit["verified_L"] < min(g, tabL) - 1e-9:
                        finds.append({"n": n, "grid": g, "old": tabL,
                                      "L": hit["verified_L"], "target": L_t,
                                      "state": hit["state"], "src": "p2fam"})
            cells.append(cell)
            v = (f"VERIFIED {cell['verified']:.9f}"
                 if cell["verified"] else
                 (f"hard {cell['best_hard_L']:.9f} (not applicable)"
                  if cell["best_hard_L"] else "no hard state"))
            print(f"  n={n:3d} grid={g:2d} target {L_t:.4f}: "
                  f"hard {cell['hard_checks']}/8 | {v} | {time.time()-t0:.0f}s",
                  flush=True)
            json.dump({"rebuilds": rebuild_log, "cells": cells, "finds": [
                {k: f[k] for k in ("n", "grid", "old", "L", "target")}
                for f in finds]}, open(OUT, "w"), indent=1)

    print(f"\nfinds: {len(finds)}")
    if finds:
        for f in sorted(finds, key=lambda f: f["n"]):
            if f["L"] < tab[str(f["n"])]["L"] - 1e-9:
                tab[str(f["n"])] = {"L": f["L"], "state": f["state"],
                                    "src": f"p2fam:grid{f['grid']}"}
                print(f"  applied n={f['n']}: {f['old']:.9f} -> {f['L']:.9f}")
        json.dump(tab, open(TAB, "w"))
        for cmd in ("scripts/cascade3.py", "scripts/closure_apply.py",
                    "scripts/final_assembly.py"):
            r = subprocess.run([sys.executable, f"{W}/{cmd}"],
                               capture_output=True, text=True)
            print(" ", cmd, "->", (r.stdout or r.stderr).strip().split("\n")[-1])
    else:
        print("no applicable finds — table unchanged (honest).")

    tab2 = json.load(open(TAB))
    s_new = sum(r["L"] / math.sqrt(int(k)) - 1 for k, r in tab2.items())
    print(f"score now: {s_new:.9f}")
    json.dump({"rebuilds": rebuild_log, "cells": cells, "finds": [
        {k: f[k] for k in ("n", "grid", "old", "L", "target")} for f in finds],
        "applied": bool(finds), "score_after": s_new}, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
