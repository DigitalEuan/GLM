#!/usr/bin/env python3
r"""sat_probe.py — the bounded experiment of 19 §11.5.

Question: at a side just BELOW the delivered `L`, with only k squares free to
move, is the packing still feasible?

With the orientations frozen and every pair's separating axis taken from the
delivered state, the models becomes a LINEAR PROGRAM in the free translation
(one global (tx,ty) for the rigid part plus (dx_i,dy_i) for each free square):

    for each pair (i,j) whose delivered axis is q with sign s:
        s * ((c_j + D_j - c_i - D_i) . q)  >=  h_i(q) + h_j(q)
    containment:  |x_i| + h_i <= L/2,  |y_i| + h_i <= L/2     (two per square)

Because q and both h are constants once theta is frozen, this is exactly the
declared-axis LP that `seam_wheels.lp_seam` uses, widened from one seam
translation to k free squares.  Feasibility is then a certificate for the
DECLARED axes, and only a violation of that declaration (a pair needing a
different axis) can make a refusal conservative -- stated in the record.

A feasible cell is only a result if `packlib.verify` accepts the final state and
the canonical scorer says the row improves.

The constraint builder is no longer defined here.  `declp.solve` holds the one
copy, shared with `branch_rot` and `t1_glide` (consolidation pass after run 70);
`solve_lp` below keeps run 65's signature and return shape as a shim so
`extreme_probe` and this record stay valid.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import declp as DL                      # noqa: E402
import sqscore as SQ                    # noqa: E402
import packlib as P                     # noqa: E402
from declp import frames, pair_tables   # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/sat_probe.json")


def solve_lp(xy, th, cs, sn, S, win, sign, free, L, move=1.0):
    """Run 65's signature and return shape, kept for `extreme_probe` and the record.

    The builder is `declp.solve`; `cs`, `sn`, `S`, `win`, `sign` are accepted and
    ignored so that a caller cannot hand in a penetration table that disagrees
    with the geometry (the run-67 defect was exactly such a disagreement).

    This probe's profile is the run-65 one: free offsets bounded by ±L (the row
    searches use ±2L) and no separation pad.
    """
    new = DL.solve(xy, th, L, free=free, pad=0.0, move=move, free_span=1.0)
    return (False, xy, float("nan")) if new is None else (True, new, 0.0)


def selftest() -> int:
    """The delivered state must be feasible at its own side.  Run 67 failed this."""
    per = SQ.load()
    ok = 0
    for n in (10, 83, 294):
        st = per[n]
        xy, th, cs, sn = frames(st)
        L0 = SQ.extent(st)
        S, pen, win, sign = pair_tables(xy, cs, sn)
        for free in (set(range(min(8, n))), set(range(n))):
            f, _, _ = solve_lp(xy, th, cs, sn, S, win, sign, free, L0)
            assert f, (n, len(free))
            ok += 1
        # free={0} at L0 - 1e-3 may go either way; only L0 is mandatory
        solve_lp(xy, th, cs, sn, S, win, sign, {0}, L0 - 1e-3)
    print(f"selftest: {ok}/6 mandatory feasibility checks pass (delivered at L0)")
    return 0


def rigid_core_span(xy, cs, sn, free):
    """Extent of the frozen squares alone (a proof of infeasibility if too big)."""
    keep = [i for i in range(len(xy)) if i not in set(free)]
    if not keep:
        return 0.0, 0.0
    h = 0.5 * (np.abs(cs) + np.abs(sn))
    xs = np.concatenate([xy[keep, 0] - h[keep], xy[keep, 0] + h[keep]])
    ys = np.concatenate([xy[keep, 1] - h[keep], xy[keep, 1] + h[keep]])
    return float(xs.max() - xs.min()), float(ys.max() - ys.min())


def probe(n, ks, eps_list):
    per = SQ.load()
    st = per[n]
    xy, th, cs, sn = frames(st)
    L0 = SQ.extent(st)
    S, pen, win, sign = pair_tables(xy, cs, sn)
    h = 0.5 * (np.abs(cs) + np.abs(sn))
    # boundary squares: those whose walls are the binding ones
    edge = np.argsort(-(np.abs(xy[:, 0]) + h))[:max(ks)]
    rows = []
    for k in ks:
        free = set(int(i) for i in edge[:k])
        best = None
        for eps in eps_list:
            ok, new, _ = solve_lp(xy, th, cs, sn, S, win, sign, free, L0 - eps)
            if ok:
                stt = [(float(new[i][0]), float(new[i][1]), float(th[i]))
                       for i in range(len(new))]
                v = P.verify(stt, tol=1e-9)
                L = SQ.extent(stt)
                rows.append({"n": n, "k": k, "eps": eps, "ok": True,
                             "L": L, "gain": SQ.row_gain(n, L) - SQ.row_gain(n, L0),
                             "verifies": v["ok"], "worst_pen": v["worst_pen"]})
                best = eps
                break
        if best is None:
            sx, sy = rigid_core_span(xy, cs, sn, free)
            rows.append({"n": n, "k": k, "eps": None, "ok": False,
                         "rigid_span_x": sx, "rigid_span_y": sy,
                         "rigid_core_blocks": max(sx, sy) > L0 - eps_list[0]})
    return {"n": n, "L_delivered": L0, "rows": rows}


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    per = SQ.load()
    # targets are the six slack-heaviest rows in 20..300 (run 65's rule, kept so
    # the withdrawn ledger stays reproducible).  The `optima.PROVED` block that
    # used to sit here was dead code -- that attribute does not exist -- and is
    # dropped rather than repaired: proved rows are `wall_margin.proved_set()`'s
    # business, not this probe's.
    cands = [(SQ.extent(per[n]) ** 2 - n, n) for n in range(20, 301)]
    cands.sort(reverse=True)
    targets = [n for _, n in cands[:6]]
    eps_list = [1e-6, 1e-4, 1e-2]
    out = [probe(n, (8, 12, 20), eps_list) for n in targets]
    print(f"{'n':>4} {'L_del':>10} {'k':>3} {'largest feasible shrink':>24}")
    for o in out:
        for r in o["rows"]:
            if r["ok"]:
                sh = f"{r['eps']:.0e} gain {r['gain']:+.2e}"
            else:
                sh = ("rigid core spans" if r.get("rigid_core_blocks")
                      else "LP infeasible")
            print(f"{o['n']:4d} {o['L_delivered']:10.6f} {r['k']:3d} {sh:>26}")
    gains = [r for o in out for r in o["rows"] if r["ok"] and r["gain"] > 1e-9]
    print(f"\nfeasible cells: {sum(1 for o in out for r in o['rows'] if r['ok'])}"
          f"   GAINS: {len(gains)}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"run": 65, "schema": "satprobe/1", "targets": targets,
                   "eps_list": eps_list, "probes": out, "gains": gains}, f, indent=1)
    print(f"ledger: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
