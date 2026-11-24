#!/usr/bin/env python3
r"""perturb.py — run 123: does a *non-closure* perturbation have any dL at all?

Doc 81 named the cheapest honest next test: instead of demanding exact contacts
(the anchor grammar) or re-running the polish clamps (measured ceiling 0.00000 on
12/12 rows), take a delivered pose, let its cells sit at **free positions** with
slack around 1e-6, and ask whether any local rearrangement shrinks the container.

Arithmetic is `Decimal` at 40 digits with `cos`/`sin` from `true_geom`'s Taylor
series — the repository's float-free instrument for poses whose angles are not
words (`true_geom` docstring; used the same way by `relax_angles`).  No binary
float touches a coordinate; `time.monotonic` only spends the budget.

Three move families, all accepted only if every nearby pair keeps slack >= 0:

  jitter   one cell displaced by delta in a random direction;
  pull     a container-extreme cell displaced inward by delta;
  slide    two touching cells displaced together by delta.

deltas are 1e-6, 1e-5, 1e-4, 1e-3.  A move that does not change the container
side is a **plateau** move and is kept (with a drift cap of 0.02), because a
route that cannot cross a plateau cannot reorganise anything; a move that
shrinks the side is a gain and is kept always.

    python3 scripts/perturb.py --selftest
    python3 scripts/perturb.py --rows 20 --seconds 10
"""
from __future__ import annotations

import bisect
import json
import os
import random
import sys
import time
from decimal import Decimal, localcontext

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import true_geom as TG                                          # noqa: E402
import sqscore as SQ                                            # noqa: E402

TAB = os.path.join(ROOT, "workspace/submission/table.json")
OUT = os.path.join(ROOT, "workspace/push/perturb123.json")

DPS = 40
DELTAS = ("0.000001", "0.00001", "0.0001", "0.001")
DRIFT = Decimal("0.02")
GAP_LO, GAP_HI = 6.2e-5, 3.3e-4       # run 111's measured legal-gap band


def dec(v) -> Decimal:
    return Decimal(str(v))


def load_row(n):
    """(cells, half-extents, cos, sin) exactly as the table stores them."""
    with open(TAB) as f:
        tab = json.load(f, **{"parse_float": str})
    rec = tab[str(n)]
    state = [(dec(r[0]), dec(r[1]), dec(r[2])) for r in rec["state"]]
    with localcontext() as ctx:
        ctx.prec = DPS + 10
        cs = [TG.cos_sin(t) for _x, _y, t in state]
    hs = [(abs(c) + abs(s)) / 2 for c, s in cs]
    return state, list(hs), [c for c, _ in cs], [s for _, s in cs]


def clear(xi, yi, ci, si, xj, yj, cj, sj) -> Decimal:
    """SAT slack of two unit squares given exact directions: >= 0 means separated."""
    dx, dy = xj - xi, yj - yi
    best = None
    for (c1, s1, c2, s2) in ((ci, si, cj, sj), (cj, sj, ci, si)):
        for qx, qy in ((c1, s1), (-s1, c1), (c2, s2), (-s2, c2)):
            proj = abs(dx * qx + dy * qy)
            h = ((abs(c1 * qx + s1 * qy) + abs(-s1 * qx + c1 * qy))
                 + (abs(c2 * qx + s2 * qy) + abs(-s2 * qx + c2 * qy))) / 2
            sl = proj - h
            if best is None or sl > best:
                best = sl
    return best


def side_of(xs, ys, hs) -> Decimal:
    hi_x = max(x + h for x, h in zip(xs, hs))
    lo_x = min(x - h for x, h in zip(xs, hs))
    hi_y = max(y + h for y, h in zip(ys, hs))
    lo_y = min(y - h for y, h in zip(ys, hs))
    return max(hi_x - lo_x, hi_y - lo_y)


def extrema(xs, ys, hs):
    """Indices contributing each of the four container extremes."""
    hi_x = max(range(len(xs)), key=lambda i: xs[i] + hs[i])
    lo_x = min(range(len(xs)), key=lambda i: xs[i] - hs[i])
    hi_y = max(range(len(ys)), key=lambda i: ys[i] + hs[i])
    lo_y = min(range(len(ys)), key=lambda i: ys[i] - hs[i])
    return hi_x, lo_x, hi_y, lo_y


def neighbours(xs, order, i, span):
    """Indices whose centre is within `span` in x (a superset of the pair test).

    `order` is the (x, index) list frozen at the start; `span` carries the drift
    cap, so a cell that has moved stays inside the queried window.
    """
    left = bisect.bisect_left(order, (xs[i] - span, -1))
    right = bisect.bisect_right(order, (xs[i] + span, len(xs) + 1))
    return [order[k][1] for k in range(left, right)]


def run_row(n, seconds, seed=0, verbose=False):
    state, hs, cs, sn = load_row(n)
    xs = [x for x, _y, _t in state]
    ys = [y for _x, y, _t in state]
    rec = run_pose(xs, ys, hs, cs, sn, seconds, seed * 1000 + n)
    rec["n"], rec["k"] = n, SQ.grid(n)
    return rec


def run_pose(xs0, ys0, hs, cs, sn, seconds, seed=0, verbose=False):
    t0 = time.monotonic()
    n = len(xs0)
    xs, ys = list(xs0), list(ys0)
    base = side_of(xs, ys, hs)
    best = base
    best_pose = (list(xs), list(ys))
    rng = random.Random(seed)
    span = Decimal("1.6") + Decimal(DELTAS[-1]) + DRIFT
    order = sorted((x, i) for i, x in enumerate(xs))
    drift = [Decimal(0)] * len(xs)
    stats = {"moves": 0, "rejected": 0, "plateau": 0, "gain": 0}
    moves_done = 0
    hi_x = lo_x = hi_y = lo_y = None
    while True:
        if time.monotonic() - t0 > seconds:
            break
        if moves_done == 0:
            ex = extrema(xs, ys, hs)
            hi_x = xs[ex[0]] + hs[ex[0]]
            lo_x = xs[ex[1]] - hs[ex[1]]
            hi_y = ys[ex[2]] + hs[ex[2]]
            lo_y = ys[ex[3]] - hs[ex[3]]
        moves_done += 1
        kind = rng.choice(("jitter", "jitter", "pull", "slide"))
        delta = Decimal(rng.choice(DELTAS))
        ang = rng.randrange(0, 8)
        dirs = ((1, 0), (-1, 0), (0, 1), (0, -1),
                (1, 1), (1, -1), (-1, 1), (-1, -1))
        ux, uy = dirs[ang]
        if kind == "pull":
            i = rng.choice([k for k in ex if rng.random() < 1])
            # pull inward: away from the extreme the cell contributes to
            if i == ex[0]:
                ux, uy = -1, 0
            elif i == ex[1]:
                ux, uy = 1, 0
            elif i == ex[2]:
                ux, uy = 0, -1
            else:
                ux, uy = 0, 1
            movers = [i]
        elif kind == "slide":
            i = rng.randrange(len(xs))
            near = [j for j in neighbours(xs, order, i, span) if j != i]
            movers = [i] + ([rng.choice(near)] if near else [])
        else:
            movers = [rng.randrange(len(xs))]
        dx, dy = delta * ux, delta * uy
        newx = list(xs)
        newy = list(ys)
        ok = True
        for i in movers:
            if abs(drift[i] + dx) + abs(drift[i] + dy) > DRIFT:
                ok = False
                break
            newx[i], newy[i] = xs[i] + dx, ys[i] + dy
        if not ok:
            stats["rejected"] += 1
            continue
        # every moved cell must stay clear of everything nearby
        for i in movers:
            for j in neighbours(newx, order, i, span):
                if j == i:
                    continue
                if j in movers:
                    if movers.index(j) < movers.index(i):
                        continue
                if clear(newx[i], newy[i], cs[i], sn[i],
                         newx[j], newy[j], cs[j], sn[j]) < 0:
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            stats["rejected"] += 1
            continue
        stats["moves"] += 1
        # refresh only the extremes whose contributor moved, then take the max
        vals = [hi_x, lo_x, hi_y, lo_y]
        idxs = [ex[0], ex[1], ex[2], ex[3]]
        for t, i in enumerate(idxs):
            if i in movers:
                vals[t] = (max(newx[k] + hs[k] for k in range(len(newx)))
                           if t == 0 else
                           min(newx[k] - hs[k] for k in range(len(newx)))
                           if t == 1 else
                           max(newy[k] + hs[k] for k in range(len(newy)))
                           if t == 2 else
                           min(newy[k] - hs[k] for k in range(len(newy))))
        new_side = max(vals[0] - vals[1], vals[2] - vals[3])
        if new_side < best:
            best, best_pose, stats["gain"] = new_side, (newx, newy), stats["gain"] + 1
        elif new_side == best:
            stats["plateau"] += 1
        else:
            stats["rejected"] += 1
            continue
        xs, ys = newx, newy
        ex = extrema(xs, ys, hs)
        hi_x = xs[ex[0]] + hs[ex[0]]
        lo_x = xs[ex[1]] - hs[ex[1]]
        hi_y = ys[ex[2]] + hs[ex[2]]
        lo_y = ys[ex[3]] - hs[ex[3]]
        for i in movers:
            drift[i] += dx + dy
        if verbose:
            print(f"    n={n} best {best} moves {stats['moves']}", flush=True)
    dL = base - best
    bx, by = best_pose
    # final certificate on the best pose, once, at 40 digits
    cells = list(zip(bx, by, cs, sn))
    cert = TG.check_cs(cells)
    return {"L0": str(base), "best": str(best),
            "dL": str(dL), "dL_float": float(dL), "moves": stats["moves"],
            "gain": stats["gain"], "plateau": stats["plateau"],
            "rejected": stats["rejected"], "side_check": str(cert["side"]),
            "violations": len(cert["violations"])}


def control(seconds=6.0, infl="1.002"):
    """Positive control: a grid pose inflated by 0.2 % must shrink back.

    If the search cannot recover a known 1e-3 of slack, a null result on the
    delivered rows says nothing about the route.
    """
    state, hs, cs, sn = load_row(16)
    xs = [x for x, _y, _t in state]
    ys = [y for _x, y, _t in state]
    base = side_of(xs, ys, hs)
    cx = (max(x + h for x, h in zip(xs, hs)) + min(x - h for x, h in zip(xs, hs))) / 2
    cy = (max(y + h for y, h in zip(ys, hs)) + min(y - h for y, h in zip(ys, hs))) / 2
    k = Decimal(infl)
    state2 = [(cx + (x - cx) * k, cy + (y - cy) * k, t) for x, y, t in state]
    xs2 = [x for x, _y, _t in state2]
    ys2 = [y for _x, y, _t in state2]
    inflated = side_of(xs2, ys2, hs)
    rec = run_pose(xs2, ys2, hs, cs, sn, seconds, 11)
    print(f"control n=16: delivered {base}  inflated {inflated}  "
          f"found {rec['best']}  dL {rec['dL']}  moves {rec['moves']}")
    assert Decimal(rec["dL"]) > 0, "search found no gain on a pose with 1e-3 slack"
    assert Decimal(rec["best"]) < inflated, "search did not shrink the inflated pose"
    assert rec["violations"] == 0, rec["violations"]
    print("control: OK -- the search closes known slack without introducing overlap")


def selftest():
    """Controls: a touching pair cannot be pulled together; a slack pair can."""
    c, s = Decimal(0), Decimal(0)
    one = (Decimal(1), Decimal(0), Decimal(0), Decimal(0))
    a = (Decimal(0), Decimal(0), Decimal(1), Decimal(0))
    b = (Decimal(1), Decimal(0), Decimal(1), Decimal(0))
    tight = clear(*a, *b)
    assert tight == 0, tight
    loose = clear(Decimal(0), Decimal(0), Decimal(1), Decimal(0),
                  Decimal("1.000001"), Decimal(0), Decimal(1), Decimal(0))
    assert loose > 0, loose
    # a 1e-6 inward move of the right-hand cell of a touching pair must violate
    worse = clear(Decimal(0), Decimal(0), Decimal(1), Decimal(0),
                  Decimal("0.999999"), Decimal(0), Decimal(1), Decimal(0))
    assert worse < 0, worse
    side = side_of([Decimal(0), Decimal(1)], [Decimal(0), Decimal(0)],
                   [Decimal("0.5"), Decimal("0.5")])
    assert side == 2, side
    print("perturb: OK (touching pair slack 0; 1e-6 slack positive; 1e-6 "
          "overlap negative; side exact)")


def main(argv):
    opts = dict(zip(argv[0::2], argv[1::2]))
    rows = int(opts.get("--rows", 20))
    seconds = float(opts.get("--seconds", 10))
    per = SQ.load()
    unbeaten = [n for n in range(1, 1001)
                if SQ.extent(per[n]) >= SQ.grid(n) - 1e-12]
    if len(unbeaten) < rows:
        step = 1
    else:
        step = len(unbeaten) / rows
    pick = sorted({unbeaten[min(len(unbeaten) - 1, int(round(i * step)))]
                   for i in range(rows)})
    print(f"unbeaten rows {len(unbeaten)}; testing {len(pick)} evenly spaced: {pick}")
    recs = []
    for n in pick:
        t0 = time.monotonic()
        rec = run_row(n, seconds, seed=7)
        rec["seconds"] = round(time.monotonic() - t0, 2)
        recs.append(rec)
        print(f"  n={n:4d} k={rec['k']:2d} L0={rec['L0'][:22]:22s} dL={rec['dL']:>26s} "
              f"({rec['dL_float']:.3e}) moves {rec['moves']:6d} gains {rec['gain']:3d} "
              f"viol {rec['violations']} {rec['seconds']:.1f}s", flush=True)
    ds = sorted(r["dL_float"] for r in recs)
    pos = [d for d in ds if d > 0]
    print(f"\ndL distribution over {len(ds)} rows: min {ds[0]:.3e}  "
          f"median {ds[len(ds) // 2]:.3e}  max {ds[-1]:.3e}")
    print(f"  rows with any gain: {len(pos)}/{len(ds)}")
    print(f"  rows at or above the legal-gap floor {GAP_LO:.1e}: "
          f"{len([d for d in ds if d >= GAP_LO])}")
    print(f"  rows at or above the legal-gap ceiling {GAP_HI:.1e}: "
          f"{len([d for d in ds if d >= GAP_HI])}")
    tot = sum(r["dL_float"] / (r["n"] ** 0.5) for r in recs)
    print(f"  score value if applied to these rows: {tot:.3e}")
    json.dump(recs, open(OUT, "w"), indent=1)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    elif "--control" in sys.argv:
        i = sys.argv.index("--control")
        rest = [a for a in sys.argv[i + 1:] if not a.startswith("--")]
        control(seconds=6.0, infl=rest[0] if rest else "1.002")
    else:
        main(sys.argv[1:])
