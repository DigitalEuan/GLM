#!/usr/bin/env python3
r"""p1p_insert31.py — run 31, P1': insertion campaign at the top aims,
designed by the symmetry census (user input: "many optimal grids are
symmetrical and efficient").

Census findings that design this run (symmetry_audit31.json):
  - every parametric construction class is majority-symmetric
    (gobel2/gobelS 100%, chain3 76%, closure/exact ~71%);
  - the stored tied states are tail-drop asymmetric, but a canonical
    symmetric arrangement exists for every tied row — arm A builds
    those canonical forms explicitly as seeds;
  - the aims are open upstream too (Mishapolk's best = integer grid
    at 356/395/355 — the parametric arm is dominated before running).

Arm A — grid-seeded symmetric squeeze.  Seed = the K x K lattice with
a symmetric hole pattern (D4/D2/Cs/C2 orbits; the patterns are listed
below), pressure-settled from its own extent K down to L_t = K - d
(ramp_settle, the prescribed P1' move), then 3 cycles of hot shuffle
(anneal, soft pass-through — the only class-crossing mechanism) and
re-hardening (settle_to).  Find gate = finalize on the best-extent
settle state (doctrine: polish.py / run 30), bar = the row's L.

Arm B — record-seeded greedy insertion.  Seed = the deepest sub-K
record below the aim; insert the missing squares greedily at the
max-clearance axis-aligned positions (0.25-pitch candidate lattice).
If all insert at L(seed) < K that is a direct find, no settling.

Per-cell NRCI/phi logging (run-29 falsifiable prediction: any
improvement should come with phi down / NRCI up).

Ledger: workspace/push/p1p_insert31.json (resumable).  Bounded.
"""
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, "/home/z/my-project/scripts")
import packlib as P
from oracle_basin import settle_to, ramp_settle
from sa_push import anneal
from soft_relax import unpack, PHI
from sat_measure import review_row
from symmetry_audit import census, group_name

W = "/home/z/my-project"
TAB = f"{W}/workspace/submission/table.json"
OUT = f"{W}/workspace/push/p1p_insert31.json"
AIMS = (356, 395, 355)
DELTAS = (0.01, 0.08)
MOVES = 6000
PHIh = math.pi / 2
TGUARD = 1500.0


# ------------------------------------------------ seed hole patterns
def patterns(n, K):
    """Symmetric removal sets (lattice indices) for K*K -> n."""
    c = K // 2 if K % 2 else None          # center index (odd K)
    out = {}
    if n == 356 and K == 19:
        ring_ax = [(8, 9), (10, 9), (9, 8), (9, 10)]
        ring_dg = [(8, 8), (10, 8), (8, 10), (10, 10)]
        corners = [(0, 0), (18, 0), (0, 18), (18, 18)]
        out["center+axialring"] = [(9, 9)] + ring_ax
        out["center+diagring"] = [(9, 9)] + ring_dg
        out["center+corners"] = [(9, 9)] + corners
    elif n == 355 and K == 19:
        vpair = [(9, 4), (9, 14)]                   # r180 pair, V-axis col
        c2pair = [(5, 5), (13, 13)]                 # r180 pair off-axis
        ring_ax = [(8, 9), (10, 9), (9, 8), (9, 10)]
        ring_dg = [(8, 8), (10, 8), (8, 10), (10, 10)]
        out["vpair+axialring"] = vpair + ring_ax     # D2
        out["c2pair+diagring"] = c2pair + ring_dg    # C2
    elif n == 395 and K == 20:
        # even K: center point (10,10); D4 orbit around it + a single
        # on the main diagonal (fixed by the D reflection)
        ring1 = [(9, 9), (10, 9), (9, 10), (10, 10)]
        ring2 = [(8, 10), (11, 10), (10, 8), (10, 11)]
        out["diag1+ring1"] = [(5, 5)] + ring1        # Cs(D)
        out["diag2+ring2"] = [(15, 15)] + ring2      # Cs(D)
    return out


def build_seed(n, K, idx):
    """K*K lattice, drop idx, at L=K (theta 0)."""
    holes = {(i, j) for i, j in idx}
    state = [(i + 0.5, j + 0.5, 0.0)
             for i in range(K) for j in range(K)
             if (i, j) not in holes]
    assert len(state) == n, (len(state), n)
    return state


def pack(state):
    return np.array([s[0] for s in state] + [s[1] for s in state]
                    + [s[2] for s in state], dtype=float)


def measure(state, n):
    m = review_row(state, n)
    return {"C": m["C"], "g": m["g"], "phi": round(m["phi"], 6),
            "NRCI": round(m["NRCI"], 6), "regime": m["regime"]}


def squeeze(n, K, pat_name, idx, delta, seed):
    """Arm A cell. Returns a cell dict."""
    L_t = K - delta
    state0 = build_seed(n, K, idx)
    q0 = pack(state0)
    cen = census(state0)
    t0 = time.time()
    q, _f = ramp_settle(q0.copy(), L_t, steps=10)
    best_ext = math.inf
    cand_q = None
    hard = 0
    for h in range(6):
        if h % 2 == 1:
            X, Y, TH = unpack(q)
            anneal(X, Y, TH, L_t, MOVES, seed * 1009 + h,
                   t0=0.30 if (h // 2) % 2 == 0 else 0.45,
                   tend=0.02, rotate_frac=0.5)
            q = np.concatenate([X, Y, TH])
            continue
        q, _f = settle_to(q, L_t, iters=250)
        st = [(float(q[i]), float(q[n + i]), float(q[2 * n + i]) % PHIh)
              for i in range(n)]
        r = P.verify(st, tol=1e-9)
        if r["worst_pen"] <= -1e-10:
            hard += 1
        if r["L"] < best_ext:
            best_ext = r["L"]
            cand_q = q.copy()
    cell = {"arm": "A", "n": n, "K": K, "pattern": pat_name,
            "seed_group": group_name(cen["hold"]),
            "delta": delta, "L_t": L_t,
            "seed_measure": measure(state0, n),
            "hard": hard, "best_extent": round(best_ext, 9),
            "secs": round(time.time() - t0, 1)}
    # finalize gate
    rowL = json.load(open(TAB))[str(n)]["L"]
    if cand_q is not None and best_ext < rowL - 1e-9:
        stc = [(float(cand_q[i]), float(cand_q[n + i]),
                float(cand_q[2 * n + i]) % PHIh) for i in range(n)]
        stf, rf = P.finalize(stc, gap=2e-9)
        if rf["ok"] and rf["worst_pen"] <= -1e-12 and rf["L"] < rowL - 1e-9:
            cell["find"] = {"L": rf["L"], "state": stf,
                            "measure": measure(stf, n)}
    return cell


# ------------------------------------------------ arm B
def sat_pen_vec(px, py, X, Y, TH):
    """Pair pen of axis-aligned unit square at (px,py) vs each square
    (X, Y, TH): min over the 4 SAT axes (x, y, u_B, v_B).  Negative =
    separated by that margin on the tightest axis."""
    cs, sn = np.cos(TH), np.sin(TH)
    e = 0.5 * (np.abs(cs) + np.abs(sn))
    dx = px - X
    dy = py - Y
    pen_x = 0.5 + e - np.abs(dx)
    pen_y = 0.5 + e - np.abs(dy)
    pen_u = e + 0.5 - np.abs(cs * dx + sn * dy)
    pen_v = e + 0.5 - np.abs(-sn * dx + cs * dy)
    return np.minimum(np.minimum(pen_x, pen_y), np.minimum(pen_u, pen_v))


def greedy_insert(n):
    """Arm B cell: the largest sub-K record below the aim (closest in n),
    greedy max-clearance axis-aligned insertion of the missing squares
    at L(seed).  (Run-31 fix: the first pass selected the record with
    the smallest L over ALL m < n — that is a tiny-n record (n=4 at
    L=2.0), not a seed near the aim; the rule is now 'largest m below
    n whose L is sub-K', i.e. the deepest record adjacent to the aim.)"""
    tab = json.load(open(TAB))
    K = math.ceil(math.sqrt(n))
    best = None
    for m in range(n - 1, 1, -1):
        if tab[str(m)]["L"] < K - 1e-9:
            best = (m, tab[str(m)]["L"])
            break
    if best is None:
        return {"arm": "B", "n": n, "why": "no sub-K seed below aim"}
    m, Lm = best
    state = [tuple(s) for s in tab[str(m)]["state"]]
    k = n - m
    L = Lm
    t0 = time.time()
    inserted = 0
    rounds = []
    for it in range(k):
        X = np.array([s[0] for s in state])
        Y = np.array([s[1] for s in state])
        TH = np.array([s[2] for s in state])
        # centers such that the axis-aligned unit square is fully inside
        # [0, L] (run-31 lesson: the first pass allowed centers at 0.25,
        # which put edges outside the container by 0.25 — the container
        # constraint was never in the greedy's objective)
        lo, hi = 0.5, L - 0.5
        if hi <= lo:
            break
        g = np.arange(lo, hi + 1e-9, 0.25)
        PX, PY = np.meshgrid(g, g)
        PXf, PYf = PX.ravel(), PY.ravel()
        # clearance of each candidate: max over candidates of
        # (min over squares of -pen) -> need min-pen per candidate:
        # vectorized chunked
        best_pen = np.full(len(PXf), -np.inf)
        for chunk in range(0, len(PXf), 512):
            pc = PXf[chunk:chunk + 512]
            yc = PYf[chunk:chunk + 512]
            pens = np.stack([sat_pen_vec(px, py, X, Y, TH)
                             for px, py in zip(pc, yc)])
            worst = pens.max(axis=1)     # pen vs the tightest square
            best_pen[chunk:chunk + 512] = worst
        j = int(np.argmin(best_pen))
        if best_pen[j] > 1e-9:
            break      # no insertable position (overlap everywhere);
                       # pen == 0 (exact tangency) IS accepted — a legal
                       # packing allows touching; finalize scales +2e-9
                        # downstream to separate (the import doctrine)
        state.append((float(PXf[j]), float(PYf[j]), 0.0))
        inserted += 1
        rounds.append(round(float(best_pen[j]), 9))
    cell = {"arm": "B", "n": n, "K": K, "seed_n": m, "seed_L": Lm,
            "need": k, "inserted": inserted,
            "clearance_last": rounds[-1] if rounds else None,
            "seed_measure": measure(tab[str(m)]["state"], m),
            "secs": round(time.time() - t0, 1)}
    if inserted == k:
        r = P.verify(state, tol=1e-9)
        rowL = tab[str(n)]["L"]
        if r["ok"] and r["worst_pen"] <= 0:
            stf, rf = P.finalize(state, gap=2e-9)
            cell["final_L"] = rf["L"]
            if rf["ok"] and rf["worst_pen"] <= -1e-12 and rf["L"] < rowL - 1e-9:
                cell["find"] = {"L": rf["L"], "state": stf,
                                "measure": measure(stf, n)}
    return cell


def main():
    led = json.load(open(OUT)) if os.path.exists(OUT) else {"cells": []}
    done = {(c["arm"], c.get("n"), c.get("pattern", c.get("seed_n")),
             c.get("delta", 0)) for c in led["cells"]}
    t0 = time.time()
    for n in AIMS:
        K = math.ceil(math.sqrt(n))
        pats = patterns(n, K)
        for name, idx in pats.items():
            for delta in DELTAS:
                if ("A", n, name, delta) in done:
                    print(f"  A n={n} {name} d={delta}: skip", flush=True)
                    continue
                if time.time() - t0 > TGUARD:
                    json.dump(led, open(OUT, "w"), indent=1)
                    print("guard: stopping, resumable", flush=True)
                    return finish(led)
                cell = squeeze(n, K, name, idx, delta, 7)
                led["cells"].append(cell)
                json.dump(led, open(OUT, "w"), indent=1)
                print(f"  A n={n} {name} d={delta}: group {cell['seed_group']}"
                      f" hard {cell['hard']} best {cell['best_extent']:.6f}"
                      f" [{cell['secs']}s]"
                      + (" FIND" if "find" in cell else ""), flush=True)
        if ("B", n, n, 0) not in done:
            cell = greedy_insert(n)
            led["cells"].append(cell)
            json.dump(led, open(OUT, "w"), indent=1)
            if "why" in cell:
                print(f"  B n={n}: {cell['why']}", flush=True)
            else:
                print(f"  B n={n}: seed {cell['seed_n']}@{cell['seed_L']:.6f}"
                      f" inserted {cell['inserted']}/{cell['need']}"
                      f" (last clearance {cell.get('clearance_last')})"
                      + (" FIND" if "find" in cell else ""), flush=True)
    finish(led)


def finish(led):
    finds = [c for c in led["cells"] if "find" in c]
    led["finds"] = [{"n": c["n"], "arm": c["arm"],
                     "pattern": c.get("pattern", c.get("seed_n")),
                     "L": c["find"]["L"]} for c in finds]
    json.dump(led, open(OUT, "w"), indent=1)
    print(f"\ncells: {len(led['cells'])} | finds: {len(finds)}")
    for f in led["finds"]:
        print(f"  FIND n={f['n']} arm {f['arm']} L={f['L']:.9f}")
    print("ledger ->", OUT)
    return bool(finds)


if __name__ == "__main__":
    main()
