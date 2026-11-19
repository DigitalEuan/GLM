#!/usr/bin/env python3
r"""refine_cascade.py — can any solve we hold be refined slightly further?

WHY.  Runs 77-79 certified 191 beating rows as the frozen-angle optimum of their
own declaration and closed both cheap routes into the band, but **362 beating
rows were never shrink-tested**: the global LP needs an n x n constraint matrix
(500k rows at n = 1000), so `frozen_opt` stopped at n = 400.  Those rows are the
only part of the delivered table where "slightly further" has never been asked.

WHAT THIS DOES.

  * REFINE.  For each uncertified beating row, centre the state, then run a
    *local* LP around the walls: the squares that define the four extreme edges
    plus their immediate neighbours are free, everything further than 2.6 is
    held.  The demand `L0 - eps` is tested on a descending ladder; the first
    feasible cell is finalized (2e-9) and put through the exact gate.  A round
    that gates at a strictly smaller side is accepted and the next round starts
    from the new state, so a row can be compressed repeatedly.

    The LP is `declp.solve`'s formulation verbatim -- same delivered branch per
    pair (`argmin` of the four SAT axes), same separation constant
    `0.5 + e_other`, same `sgn` from the delivered projection, same containment
    `|x + t + D| + h <= L/2` -- restricted to the pairs that can bind under the
    move bound.  With `span = 0.05` per square and `move = 0.5` global, a pair
    centre-distance >= 2.6 cannot come into contact (max relative motion 0.2,
    binding needs < 0.5 + 0.7071 = 1.2071), so the restriction loses nothing.

    A refusal is LOCAL: it says this wall configuration cannot shrink with these
    squares free.  It is not a certificate.  Only the gate accepts, and it is
    the only thing that does.

  * CASCADE.  Every accepted refinement is read through the residue class it
    belongs to.  Writing n = k^2 + r, the cascade of `09-CASCADE.md` carries a
    base's slack delta to every larger row of the same class:

        base k0^2 + r at slack delta  =>  row k^2 + r at k + delta.

    So a base refined by Delta refines each class member by Delta, worth
    `Delta * sum_{n' in class, n' >= n} 1/sqrt(n')`.  That sum is reported as
    the cascade weight W(r) and the product as `propagated` -- a BOUND, and it
    is labelled one: the chain step is a lattice construction, so it carries a
    base whose ring squares are lattice cells, not an arbitrary polished state.

READ-ONLY apart from `workspace/push/refine_cascade.json`.  Never writes
`submission.csv`: a refinement found here is a candidate state, not a delivery.

    python3 scripts/refine_cascade.py --selftest
    python3 scripts/refine_cascade.py --n-min 401            # the 362 open rows
    python3 scripts/refine_cascade.py --n-min 401 --limit 40
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np
from scipy.optimize import linprog
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import declp as D            # noqa: E402
import packlib as P          # noqa: E402
import sqscore as SQ         # noqa: E402

ROOT = os.path.dirname(HERE)
LEDGER = os.path.join(ROOT, "workspace/push/refine_cascade.json")

#: the demand ladder, descending.  A refinement below ~3e-9 cannot survive
#: finalize's 2e-9 global scale, so the ladder stops at 1e-7 and says so.
LADDER = (1e-2, 3e-3, 1e-3, 1e-4, 3e-5, 1e-5, 3e-6, 1e-6, 3e-7, 1e-7)
CUTOFF = 2.6          # pair truncation radius (see module docstring)
SPAN = 0.05           # per-square move bound
MOVE = 0.5            # global translation bound
FMAX = 50             # free-set cap
WALL_TOL = 1e-9
#: a row counts as cascade-open only above the scale `finalize` itself moves the
#: side by (2e-9); at 1e-9 the 25 "open" rows are all that margin, not slack.
OPEN_TOL = 1e-8


# ------------------------------------------------------------------ geometry
def bbox(xy, h):
    xlo = float((xy[:, 0] - h).min()); xhi = float((xy[:, 0] + h).max())
    ylo = float((xy[:, 1] - h).min()); yhi = float((xy[:, 1] + h).max())
    return xlo, xhi, ylo, yhi


def centred(state):
    """State shifted so its bbox is centred at the origin (L is unchanged)."""
    st = [(float(x), float(y), float(t)) for x, y, t in state]
    xy, th, _, _ = D.frames(st)
    h = 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))
    xlo, xhi, ylo, yhi = bbox(xy, h)
    cx, cy = 0.5 * (xlo + xhi), 0.5 * (ylo + yhi)
    return [(x - cx, y - cy, t) for x, y, t in st]


def wall_set(xy, th, fmax=FMAX):
    """Squares that define one of the four extreme edges, and their neighbours."""
    h = 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))
    xlo, xhi, ylo, yhi = bbox(xy, h)
    w = set(np.where(xy[:, 0] - h <= xlo + WALL_TOL)[0]) \
        | set(np.where(xy[:, 0] + h >= xhi - WALL_TOL)[0]) \
        | set(np.where(xy[:, 1] - h <= ylo + WALL_TOL)[0]) \
        | set(np.where(xy[:, 1] + h >= yhi - WALL_TOL)[0])
    tree = cKDTree(xy)
    near = set()
    for i in w:
        near.update(tree.query_ball_point(xy[i], 1.3))
    F = sorted(w | near)
    capped = len(F) > fmax
    if capped:                             # keep the walls when the ring is wide
        F = sorted(w)
        capped = len(F) >= fmax            # still capped if even the walls are
    return F, capped


# ------------------------------------------------------------------------ LP
def local_solve(xy, th, L, free, span=SPAN, move=MOVE, cutoff=CUTOFF):
    """declp.solve restricted to the pairs that can bind.  New centres or None."""
    xy = np.asarray(xy, dtype=float)
    th = np.asarray(th, dtype=float)
    n = len(xy)
    cs, sn = np.cos(th), np.sin(th)
    u = np.stack([cs, sn], axis=1)
    v = np.stack([-sn, cs], axis=1)
    h = 0.5 * (np.abs(cs) + np.abs(sn))
    F = sorted(set(int(i) for i in free))
    idx = {i: k for k, i in enumerate(F)}
    fs = set(F)
    nv = 2 + 2 * len(F)
    tree = cKDTree(xy)
    pairs = tree.query_pairs(cutoff, output_type="ndarray")

    A, b = [], []
    for i, j in pairs:
        i, j = int(i), int(j)
        if i not in fs and j not in fs:
            continue                        # both held: separated at L0 already
        d = xy[j] - xy[i]
        e = 0.5 * (abs(math.cos(th[j] - th[i])) + abs(math.sin(th[j] - th[i])))
        pen = (0.5 + e - abs(float(d @ u[i])), 0.5 + e - abs(float(d @ v[i])),
               0.5 + e - abs(float(d @ u[j])), 0.5 + e - abs(float(d @ v[j])))
        a = int(np.argmin(pen))
        owner = i if a < 2 else j
        q = u[owner] if a % 2 == 0 else v[owner]
        hs = 0.5 + e
        t0 = float(d @ q)
        sgn = 1.0 if t0 >= 0 else -1.0
        need = hs - sgn * t0
        row = np.zeros(nv)
        if j in fs:
            row[2 + 2 * idx[j]] += sgn * q[0]
            row[3 + 2 * idx[j]] += sgn * q[1]
        if i in fs:
            row[2 + 2 * idx[i]] -= sgn * q[0]
            row[3 + 2 * idx[i]] -= sgn * q[1]
        A.append(-row)
        b.append(-need)
    for i in range(n):
        vcol = 2 + 2 * idx[i] if i in fs else None
        for ax in (0, 1):
            for sg in (1.0, -1.0):
                row = np.zeros(nv)
                row[ax] = sg
                if vcol is not None:
                    row[vcol + ax] = sg
                A.append(row)
                b.append(L / 2 - h[i] - sg * float(xy[i][ax]))
    res = linprog(np.zeros(nv), A_ub=np.array(A), b_ub=np.array(b),
                  bounds=[(-move, move), (-move, move)]
                  + [(-span, span)] * (2 * len(F)), method="highs")
    if res.status != 0:
        return None
    x = res.x
    new = np.array(xy, dtype=float)
    new[:, 0] += x[0]; new[:, 1] += x[1]
    for i in F:
        new[i, 0] += x[2 + 2 * idx[i]]
        new[i, 1] += x[3 + 2 * idx[i]]
    return new


def refine_row(n, state, rounds=6, ladder=LADDER, fmax=FMAX):
    """Greedy local compression of one row.  Gate-certified, or a refusal."""
    st = centred(state)
    L0 = SQ.extent(st)
    cur = st
    L = L0
    accepted = []
    cap_hit = False
    for rd in range(rounds):
        xy, th, _, _ = D.frames(cur)
        F, capped = wall_set(xy, th, fmax=fmax)
        cap_hit = cap_hit or capped
        got = None
        for eps in ladder:
            new = local_solve(xy, th, L - eps, F)
            if new is None:
                continue
            cand = [(float(new[i][0]), float(new[i][1]), float(th[i]))
                    for i in range(n)]
            stf, rf = P.finalize(cand, gap=2e-9)
            if not rf["ok"]:
                continue
            g = D.gate(n, np.array([(s[0], s[1]) for s in stf]),
                       np.array([s[2] for s in stf]), L)
            if g["ok"] and g["L"] < L - 1e-8:
                got = (stf, g, eps, len(F))
                break
        if got is None:
            break
        stf, g, eps, nf = got
        accepted.append({"round": rd, "eps": eps, "free": nf,
                         "L": round(g["L"], 12),
                         "drop": round(L - g["L"], 12)})
        cur = stf
        L = g["L"]
    return {"n": n, "L0": L0, "L1": L, "rounds": accepted,
            "drop": L0 - L, "accepted": bool(accepted), "cap_hit": cap_hit,
            "state": cur if accepted else None}


# ------------------------------------------------------------------- cascade
def class_rows(n: int, nmax: int = 1000):
    k = math.isqrt(n)
    r = n - k * k
    out = []
    for kk in range(k, math.isqrt(nmax) + 1):
        m = kk * kk + r
        if m > nmax:
            break
        if m >= n:
            out.append((m, kk))
    return r, out


def cascade(n, nmax=1000):
    """The residue class of n and the weight W(r) a refinement would carry."""
    r, rows = class_rows(n, nmax)
    return {"r": r, "members": len(rows),
            "W": sum(1.0 / math.sqrt(m) for m, _ in rows)}


def causal_leaders(per: dict) -> dict:
    """n -> (k0, n0, slack0): the best base in n's residue class with k0 < k.

    The cascade only runs upwards, so a row of larger k cannot serve a smaller
    one; the leader must be taken over strictly earlier bands.  (The global
    class minimum is *not* a base -- it is usually a later, better row.)
    """
    cls: dict = {}
    for n in sorted(per):
        k = math.isqrt(n)
        r = n - k * k
        if r == 0:
            continue
        cls.setdefault(r, []).append((n, k))
    out: dict = {}
    for r, rows in cls.items():
        best = None
        for n, k in rows:
            if best is not None:
                out[n] = best
            d = SQ.extent(per[n]) - k
            if best is None or d < best[2] - 1e-12:
                best = (k, n, d)
    return out


def chain_build(leader, k0: int, k: int, th_tol: float = 1e-12):
    """Translate a base's ring into a bigger corner.  New state, or None.

    The base is a k0 x k0 axis grid plus r squares in its ring.  Placing a k x k
    grid and translating every ring square by (k - k0, k - k0) leaves the grid
    clear (ring x or y was >= k0, now >= k) and the ring inside [0, k+delta]^2,
    so the pair separations are untouched and the side is k + delta.  Only the
    cases the translation can carry are built: an all-axis, on-lattice grid of
    exactly k0^2 squares, and ring squares outside it.
    """
    st = [(float(x), float(y), float(t)) for x, y, t in leader]
    if any(abs(t) > th_tol for _, _, t in st):
        return None
    xy = np.array([(x, y) for x, y, _ in st])
    tol = 1e-6
    ongrid = (xy[:, 0] >= 0.5 - tol) & (xy[:, 0] <= k0 - 0.5 + tol) \
        & (xy[:, 1] >= 0.5 - tol) & (xy[:, 1] <= k0 - 0.5 + tol)
    if int(ongrid.sum()) != k0 * k0:
        return None
    ring = xy[~ongrid]
    if not len(ring):
        return None
    shift = k - k0
    new = [(i + 0.5, j + 0.5, 0.0) for i in range(k) for j in range(k)]
    new += [(float(x) + shift, float(y) + shift, 0.0) for x, y in ring]
    return new


def open_rows(per: dict) -> list:
    """Rows whose slack exceeds the causal class leader's: the chain would
    already improve them from a base we hold."""
    lead = causal_leaders(per)
    out = []
    for n, (k0, n0, d0) in lead.items():
        k = math.isqrt(n)
        d = SQ.extent(per[n]) - k
        if d > d0 + OPEN_TOL:
            out.append((n, k, d - d0, k0, n0, d0))
    return sorted(out, key=lambda z: -z[2] / math.sqrt(z[0]))


def profile(per: dict) -> dict:
    """Per residue class: leader slack, rows above it, and the weight W.

    W(r) = sum over the class of 1/sqrt(n) is the score bought per unit of
    slack: a leader refined by Delta propagates Delta * W(r) if the chain
    carries.  A row with slack > leader slack is *cascade-open*: the chain from
    a base we already hold predicts a smaller side for it.
    """
    cls: dict = {}
    for n in sorted(per):
        k = math.isqrt(n)
        r = n - k * k
        if r == 0:
            continue
        cls.setdefault(r, []).append((n, k, SQ.extent(per[n]) - k))
    out = {}
    for r, rows in sorted(cls.items()):
        rows = sorted(rows, key=lambda z: z[1])       # by k, i.e. causally
        W = sum(1.0 / math.sqrt(n) for n, _, _ in rows)
        best = rows[0][2]                 # the first (smallest k) is the base
        open_rows, avail, n_at = [], 0.0, 1
        for n, _, d in rows[1:]:
            if d > best + OPEN_TOL:
                open_rows.append((n, round(d - best, 12)))
                avail += (d - best) / math.sqrt(n)
            else:
                n_at += 1
            best = min(best, d)
        out[r] = {"rows": len(rows), "W": W, "leader_slack": best,
                  "at_chain": n_at, "open": open_rows,
                  "open_gain": avail}
    return out


# ------------------------------------------------------------------ selftest
def selftest(per: dict) -> int:
    print("control 1 — the local LP reproduces declp.solve on a small row")
    for n in (10, 50, 100):
        st = centred(per[n])
        xy, th, _, _ = D.frames(st)
        L0 = SQ.extent(st)
        allfree = list(range(n))
        for eps in (0.0, 1e-6, 1e-3):
            mine = local_solve(xy, th, L0 - eps, allfree, span=2.0, move=1.0)
            ref = D.solve(xy, th, L0 - eps, free=set(allfree), pad=0.0,
                          move=1.0, free_span=2.0)
            assert (mine is None) == (ref is None), (n, eps, mine is None,
                                                     ref is None)
    print("   n = 10, 50, 100: feasibility agrees with declp.solve at "
          "L0, L0-1e-6, L0-1e-3 (all squares free)")

    print("control 2 — a rigid grid has nothing to give")
    grid = [(0.5 + i, 0.5 + j, 0.0) for i in range(5) for j in range(5)]
    r = refine_row(25, grid)
    assert not r["accepted"] and abs(r["drop"]) < 1e-12, r["drop"]
    print("   5x5 grid at L = 5: refused at every rung of the ladder")

    print("control 3 — a loosened wall is found and gated back")
    loose = centred(per[10])
    L = SQ.extent(loose)
    loose = [(x + (0.02 if x + 0.5 >= L / 2 - 1e-9 else 0.0),
              y, t) for x, y, t in loose]
    L1 = SQ.extent(loose)
    r = refine_row(10, loose)
    assert r["accepted"] and r["L1"] < L1 - 1e-3, (L1, r["L1"])
    print(f"   n=10 loosened by +{L1 - L:.3f}: refined back to {r['L1']:.6f} "
          f"(delivered {L:.6f}), {len(r['rounds'])} round(s)")

    print("control 4 — the gate is the judge, not the LP")
    lo = centred(per[10])
    L = SQ.extent(lo)
    loose = [(x + (0.02 if x + 0.5 >= L / 2 - 1e-9 else 0.0), y, t) for x, y, t in lo]
    L1 = SQ.extent(loose)
    xy, th, _, _ = D.frames(loose)
    new = local_solve(xy, th, L1 - 1e-3, list(range(10)), span=2.0, move=1.0)
    assert new is not None, "the loosened row must admit its own side"
    raw = D.gate(10, new, th, L1)
    stf, rf = P.finalize([(new[i][0], new[i][1], th[i]) for i in range(10)],
                         gap=2e-9)
    fin = D.gate(10, np.array([(s[0], s[1]) for s in stf]),
                 np.array([s[2] for s in stf]), L1)
    assert raw["ok"] is False, "the raw LP state must not pass the gate"
    assert fin["ok"] and fin["L"] < L1, fin
    print(f"   raw LP state refused by the gate (pen {raw['worst_pen']:.2e}); "
          f"finalized at {fin['L']:.6f} -> ok={fin['ok']}")

    print("control 5 — the cascade arithmetic on a known row")
    c = cascade(50)
    k = math.isqrt(50)
    assert c["r"] == 50 - k * k and c["members"] >= 1
    hand = sum(1.0 / math.sqrt(kk * kk + c["r"])
               for kk in range(k, 32) if kk * kk + c["r"] <= 1000)
    assert abs(hand - c["W"]) < 1e-12, (hand, c["W"])
    print(f"   n=50 -> r={c['r']}, {c['members']} members, W={c['W']:.6f} "
          f"agrees with the hand sum")
    print("selftest: OK")
    return 0


# ---------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--n-min", type=int, default=401)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--budget", type=float, default=210.0, help="seconds")
    ap.add_argument("--rounds", type=int, default=12)
    ap.add_argument("--fmax", type=int, default=FMAX)
    ap.add_argument("--profile", action="store_true")
    ap.add_argument("--chain", action="store_true")
    a = ap.parse_args()
    per = SQ.load()
    SQ.guard(per, quiet=True)
    if a.selftest:
        return selftest(per)
    if a.chain:
        op = open_rows(per)
        print(f"cascade-open rows {len(op)}")
        wins, built, skipped = [], 0, 0
        for n, k, g, k0, n0, d0 in op:
            st = chain_build(per[n0], k0, k)
            if st is None:
                skipped += 1
                continue
            built += 1
            stf, rf = P.finalize(st, gap=2e-9)
            if not rf["ok"]:
                continue
            gg = D.gate(n, np.array([(s[0], s[1]) for s in stf]),
                        np.array([s[2] for s in stf]), SQ.extent(per[n]))
            if gg["ok"] and gg["L"] < SQ.extent(per[n]) - 1e-9:
                wins.append({"n": n, "L0": SQ.extent(per[n]), "L": gg["L"],
                             "base": n0, "gain": (SQ.extent(per[n]) - gg["L"])
                             / math.sqrt(n), "state": gg["state"]})
                print(f"  CHAIN n={n}: {SQ.extent(per[n]):.9f} -> "
                      f"{gg['L']:.9f} from base n={n0} "
                      f"(gain {wins[-1]['gain']:.2e})")
        tot = sum(w["gain"] for w in wins)
        print(f"built {built}, skipped {skipped}, gated improvements "
              f"{len(wins)}, score {tot:.3e}")
        with open(LEDGER.replace(".json", "_chain.json"), "w") as f:
            json.dump({"open": [list(map(float, z)) for z in op],
                       "built": built, "skipped": skipped,
                       "wins": [{k: v for k, v in w.items() if k != "state"}
                                for w in wins],
                       "score": tot}, f, indent=1)
        print("ledger ->", LEDGER.replace(".json", "_chain.json"))
        return 0
    if a.profile:
        prof = profile(per)
        tot_open = sum(v["open_gain"] for v in prof.values())
        nopen = sum(len(v["open"]) for v in prof.values())
        op = open_rows(per)
        tot = sum(g / math.sqrt(n) for n, _, g, _, _, _ in op)
        print(f"causal cascade-open rows {len(op)} worth {tot:.3e}")
        for n, k, g, k0, n0, d0 in op[:10]:
            print(f"  n={n:<4} k={k:<2} base n={n0} (k0={k0}, slack "
                  f"{d0:.6f}) -> predicted {k + d0:.6f}, slack is "
                  f"+{g:.2e} above it")
        print()
        print(f"residue classes {len(prof)}; rows at their causal chain value "
              f"{sum(v['at_chain'] for v in prof.values())}; "
              f"cascade-open rows {nopen} worth {tot_open:.3e} "
              f"(tolerance {OPEN_TOL:g}, above finalize's 2e-9)")
        print(f"{'r':>3} {'rows':>5} {'W(r)':>8} {'leader':>9} {'at_chain':>8} "
              f"{'open':>5}")
        for r in sorted(prof, key=lambda z: -prof[z]["W"])[:12]:
            v = prof[r]
            print(f"{r:>3} {v['rows']:>5} {v['W']:>8.4f} {v['leader_slack']:>9.6f} "
                  f"{v['at_chain']:>8} {len(v['open']):>5}")
        for v in prof.values():
            for n, over in v["open"]:
                print(f"  open n={n} slack +{over:.2e} above its class leader")
        with open(LEDGER.replace(".json", "_profile.json"), "w") as f:
            json.dump(prof, f, indent=1)
        print("ledger ->", LEDGER.replace(".json", "_profile.json"))
        return 0

    beats = [n for n in sorted(per)
             if SQ.is_beat(n, SQ.extent(per[n]))]
    cand = [n for n in beats if n >= a.n_min]
    if a.limit:
        cand = cand[:a.limit]
    certified = len([n for n in beats if n <= 400])    # run 77's coverage
    print(f"beating rows {len(beats)}; uncertified (n >= {a.n_min}) "
          f"{len(cand)}; certified by run 77: {certified}")

    t0 = time.time()
    recs, scanned, caps = [], 0, 0
    for n in cand:
        if time.time() - t0 > a.budget:
            print(f"budget reached after {scanned} rows")
            break
        r = refine_row(n, per[n], rounds=a.rounds, fmax=a.fmax)
        scanned += 1
        caps += int(r["cap_hit"])
        if r["accepted"]:
            c = cascade(n)
            drop = r["drop"]
            r["cascade"] = {"r": c["r"], "W": round(c["W"], 9),
                            "propagated_bound": round(drop * c["W"], 12),
                            "class_members": c["members"]}
            r["gain"] = drop / math.sqrt(n)
            recs.append(r)
            print(f"  REFINED n={n}: {r['L0']:.9f} -> {r['L1']:.9f} "
                  f"(-{drop:.2e}, {len(r['rounds'])} rounds) gain {r['gain']:.2e} "
                  f"| r={c['r']} cascade bound {drop * c['W']:.2e}")
    dt = time.time() - t0
    print()
    print(f"scanned {scanned} of {len(cand)} beating rows in {dt:.0f}s; "
          f"free-set cap hit on {caps} row-rounds")
    print(f"refined {len(recs)}")
    tot = sum(r["gain"] for r in recs)
    prop = sum(r["cascade"]["propagated_bound"] for r in recs)
    print(f"measured row gain {tot:.3e}; cascade bound {prop:.3e}")
    if not recs:
        print("every scanned row refused the ladder: no wall square could move "
              "inward at frozen angles (local statement only)")
    res = {"n_min": a.n_min, "candidates": len(cand), "scanned": scanned,
           "cap_hits": caps, "fmax": a.fmax,
           "seconds": round(dt, 1), "ladder": list(LADDER),
           "cutoff": CUTOFF, "span": SPAN, "move": MOVE,
           "refined": [{k: v for k, v in r.items() if k != "state"} for r in recs],
           "states": {str(r["n"]): r["state"] for r in recs},
           "row_gain": tot, "cascade_bound": prop}
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w") as f:
        json.dump(res, f, indent=1)
    print("ledger ->", LEDGER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
