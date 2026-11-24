#!/usr/bin/env python3
r"""relax_angles.py — coupled position *and* angle relaxation, judged by the true geometry.

Runs 106–109 froze the angles: they snapped every cell to one of the eight exact words and
searched positions. That is what makes the exact gate possible, and also what makes it blind —
a cell that would fit only at 47 degrees can never be found. This module removes the blindfold
for *discovery* only:

  * the state is relaxed in continuous variables `(dx, dy, dtheta)` per cell, coupled, so a
    cluster can rotate and shift at the same time (a contact-normal step: overlapping pairs push
    apart along the axis that separates least, and the whole configuration is re-shrunk);
  * the objective is the true container side plus a heavy penalty on overlap, minimised by
    L-BFGS-B with bounded steps;
  * every candidate is then judged by `true_geom` at 40 decimal digits - the side and the exact
    no-overlap test - and compared with the row's *true* delivered side from `table.json`.

**Discovery and certification are deliberately separated.** This search uses float arithmetic and
is *not* in the float audit, because it proposes nothing that is certified. Anything it finds is
a candidate; promotion would still require the exact `Q(sqrt 2)` gate plus a certificate, which
for a row whose angles are not words cannot exist at all (doc 70 §4) - `certifiable()` reports
that honestly rather than pretending.

    python3 scripts/relax_angles.py            # n = 11, 17, 18, 29
    python3 scripts/relax_angles.py --selftest
"""
from __future__ import annotations

import json
import os
import sys
import time

from decimal import Decimal as D

import numpy as np
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import cand105 as C                 # noqa: E402
import cand106 as K                 # noqa: E402
import rat47 as R                   # noqa: E402
import semantic_pack as SP          # noqa: E402
import true_geom as TG              # noqa: E402

TARGETS = (11, 17, 18, 29)
RESTARTS = 3
LAMBDA = 1e6
MAXITER = 400
OUT = os.path.join(ROOT, "workspace/push/relax_angles.json")
TAB = os.path.join(ROOT, "workspace/submission/table.json")


# ------------------------------------------------------------------ geometry in float
def extents(theta):
    """Half-extents `(hx, hy)` of each cell: both `(|cos| + |sin|) / 2`."""
    h = 0.5 * (np.abs(np.cos(theta)) + np.abs(np.sin(theta)))
    return h, h


def side_of(x, y, theta):
    h, _ = extents(theta)
    return max(float((x + h).max() - (x - h).min()), float((y + h).max() - (y - h).min()))


def overlap_penalty(x, y, theta, near):
    """Sum of squared penetrations over the pairs that are close enough to matter."""
    if len(near) == 0:
        return 0.0
    i, j = near[:, 0], near[:, 1]
    dx, dy = x[j] - x[i], y[j] - y[i]
    ci, si = np.cos(theta[i]), np.sin(theta[i])
    cj, sj = np.cos(theta[j]), np.sin(theta[j])
    best = None
    for (c1, s1, c2, s2) in ((ci, si, cj, sj), (cj, sj, ci, si)):
        for q in ((c1, s1), (-s1, c1), (c2, s2), (-s2, c2)):
            proj = np.abs(dx * q[0] + dy * q[1])
            h1 = 0.5 * (np.abs(c1 * q[0] + s1 * q[1]) + np.abs(-s1 * q[0] + c1 * q[1]))
            h2 = 0.5 * (np.abs(c2 * q[0] + s2 * q[1]) + np.abs(-s2 * q[0] + c2 * q[1]))
            sl = proj - (h1 + h2)
            best = sl if best is None else np.maximum(best, sl)
    pen = np.clip(-best, 0.0, None)
    return float((pen ** 2).sum())


def near_pairs(x, y, theta, reach=2.2):
    """Pairs whose centres are within `reach` -- the only ones a local step can make overlap."""
    dx = np.abs(x[:, None] - x[None, :])
    dy = np.abs(y[:, None] - y[None, :])
    close = (dx <= reach) & (dy <= reach)
    iu = np.triu_indices(len(x), k=1)
    keep = close[iu]
    return np.stack(iu, axis=1)[keep]


def pack(z, n):
    return z[:n].copy(), z[n:2 * n].copy(), z[2 * n:].copy()


def objective(z, n, near):
    x, y, t = pack(z, n)
    return side_of(x, y, t) + LAMBDA * overlap_penalty(x, y, t, near)


# ------------------------------------------------------------------ the row's start point
def start(n, rows):
    """The delivered pose from `table.json` -- legal by construction -- as floats.

    Starting from the snapped-and-repaired pose (run 109's convention) would handicap the search:
    that pose is already a few 1e-4 worse than the delivered one, so it would have to recover the
    snapping loss before it could even reach the bar. The fair question is whether a coupled
    position-and-angle step can beat the *delivered* row, so this is where the search starts.
    """
    tab = json.load(open(TAB))
    st = tab[str(n)]["state"]
    x = np.array([float(r[0]) for r in st])
    y = np.array([float(r[1]) for r in st])
    th = np.array([float(r[2]) for r in st])
    chk = TG.check(true_state(x, y, th))
    return (x, y, th), f"delivered table pose ({len(chk['violations'])} violations)", len(chk["violations"])


def start_snapped(n, rows):
    """The snapped-and-repaired pose (kept for the record; not the search start)."""
    pf, wf, _gap = SP.state_of(n, rows)
    sv = SP.survey(pf, wf)
    note = "snapped pose"
    if sv["violations"]:
        fixed = SP.repair(pf, wf, sv)
        if fixed[0] is None:
            return None, "repair-stalled", len(sv["violations"])
        pf = fixed[0]
        note = f"repaired ({fixed[2]} steps)"
    xs = [float(SP.q_parse(SP.q_st(p[0]))) for p in pf]
    ys = [float(SP.q_parse(SP.q_st(p[1]))) for p in pf]
    th = [float(t) for (_x, _y, t) in rows[n]]
    return (np.array(xs), np.array(ys), np.array(th)), note, 0


def true_state(x, y, t):
    """The state as `(x, y, angle)` decimals for `true_geom`."""
    return [(str(float(a)), str(float(b)), str(float(c))) for a, b, c in zip(x, y, t)]


# ------------------------------------------------------------------ one row
def relax_row(n, rows=None, restarts=RESTARTS):
    rows = rows or C.load_rows()
    tab = json.load(open(TAB))
    Ldel = TG.side([(str(x), str(y), str(t)) for (x, y, t) in
                    [(float(r[0]), float(r[1]), float(r[2])) for r in rows[n]]])
    rec = {"n": n, "N": len(rows[n]), "L_true_delivered": str(+Ldel), "restarts": [],
           "best": None, "verdict": None}
    st0, note, viol = start(n, rows)
    rec["start"] = note
    rec["start_legal"] = bool(viol == 0)
    rec["start_violations"] = viol
    if st0 is None:
        rec["verdict"] = "repair-stalled"
        return rec
    x0, y0, t0 = st0
    rec["L_start"] = str(+TG.check(true_state(x0, y0, t0))["side"])
    rng = np.random.RandomState(20261123)
    best = None
    for k in range(restarts):
        z0 = np.concatenate([x0, y0, t0])
        if k:
            z0 = z0 + rng.normal(scale=1e-3, size=z0.shape)
        near = near_pairs(*pack(z0, n))
        bounds = ([(-1e6, 1e6)] * (2 * n)) + [(-1e6, 1e6)] * n
        res = minimize(objective, z0, args=(n, near), method="L-BFGS-B", bounds=bounds,
                       options={"maxiter": MAXITER, "ftol": 1e-14, "gtol": 1e-10})
        x, y, t = pack(res.x, n)
        chk = TG.check(true_state(x, y, t))
        entry = {"restart": k, "side40": str(+chk["side"]), "violations": len(chk["violations"]),
                 "worst": None if chk["worst"] is None else str(+chk["worst"]),
                 "nit": int(res.nit), "fun": float(res.fun)}
        # phase 2 -- project the shrunk state back to feasibility: minimise overlap only, with the
        # side free.  This is the honest test of "is there a legal packing this small": a penalty
        # trade-off can always buy 1e-4 of side with a few overlaps, a projection cannot.
        if chk["violations"]:
            near2 = near_pairs(x, y, t, reach=2.6)
            def proj_obj(z, n, nr):
                xa, ya, ta = pack(z, n)
                return overlap_penalty(xa, ya, ta, nr)
            res2 = minimize(proj_obj, res.x, args=(n, near2), method="L-BFGS-B",
                            bounds=bounds, options={"maxiter": MAXITER, "ftol": 1e-16,
                                                    "gtol": 1e-12})
            x2, y2, t2 = pack(res2.x, n)
            chk2 = TG.check(true_state(x2, y2, t2))
            entry["projected"] = {"side40": str(+chk2["side"]),
                                  "violations": len(chk2["violations"]),
                                  "nit": int(res2.nit)}
            if not chk2["violations"] and (best is None or chk2["side"] < best[0]):
                best = (chk2["side"], x2, y2, t2)
            x, y, t, chk = (x2, y2, t2, chk2) if not chk2["violations"] else (x, y, t, chk)
        rec["restarts"].append(entry)
        if not chk["violations"] and (best is None or chk["side"] < best[0]):
            best = (chk["side"], x, y, t)
        print(f"    n={n} restart {k}: side40 {float(chk['side']):.12f}"
              f" violations {len(chk['violations'])} nit {res.nit}"
              f" | projected {entry.get('projected', {}).get('side40', '-')}"
              f" viol {entry.get('projected', {}).get('violations', '-')}", flush=True)
    if best is None:
        rec["verdict"] = "no-overlap-free-restart"
        return rec
    rec["best"] = {"side40": str(+best[0]), "gain": str(+(Ldel - best[0])),
                   "beats_delivered": bool(best[0] < Ldel),
                   "state": [[str(float(a)), str(float(b)), str(float(c))]
                             for a, b, c in zip(best[1], best[2], best[3])]}
    rec["certifiable"] = certifiable(best[3])
    rec["verdict"] = ("improves (discovery only)" if best[0] < Ldel else "no-improvement")
    return rec


# ------------------------------------------------------------------ the constrained ladder
def hinge_objective(z, n, near, target):
    """Overlap plus a hinge on the side: `sum pen^2 + 100 max(0, side - target)^2`.

    A constrained shrink rather than a penalty trade-off: the side is not *rewarded* for being
    small, it is only *punished* for exceeding `target`, so the optimiser spends its freedom on
    removing overlaps first and on the side second. That is the gentle ladder the projection gap
    asks for.
    """
    x, y, t = pack(z, n)
    s = side_of(x, y, t)
    over = max(0.0, s - target)
    return overlap_penalty(x, y, t, near) + 100.0 * over * over


def project(z, n, reach=2.6, maxiter=MAXITER):
    """Minimise overlap alone from `z`; returns the projected state and its 40-digit check."""
    x, y, t = pack(z, n)
    nr = near_pairs(x, y, t, reach=reach)
    def obj(zz, nn, near):
        xa, ya, ta = pack(zz, nn)
        return overlap_penalty(xa, ya, ta, near)
    res = minimize(obj, z, args=(n, nr), method="L-BFGS-B",
                   bounds=([(-1e6, 1e6)] * (3 * n)),
                   options={"maxiter": maxiter, "ftol": 1e-16, "gtol": 1e-12})
    x2, y2, t2 = pack(res.x, n)
    return res.x, TG.check(true_state(x2, y2, t2))


def ladder(n, rows, start_state, deltas, lam_hinge=100.0, tries=4, seed=20261124):
    """Shrink by each `delta` in turn; after every attempt project and report the legal side."""
    x0, y0, t0 = start_state
    rng = np.random.RandomState(seed)
    L0 = TG.check(true_state(x0, y0, t0))["side"]
    best = None
    out = []
    for delta in deltas:
        target = L0 - D(str(delta))
        got = None
        for k in range(tries):
            z0 = np.concatenate([x0, y0, t0])
            if k:
                z0 = z0 + rng.normal(scale=2e-3, size=z0.shape)
            near = near_pairs(*pack(z0, n), reach=2.6)
            res = minimize(hinge_objective, z0, args=(n, near, float(target)), method="L-BFGS-B",
                           bounds=([(-1e6, 1e6)] * (3 * n)),
                           options={"maxiter": MAXITER, "ftol": 1e-16, "gtol": 1e-12})
            z2, chk = project(res.x, n)
            rec = {"delta": delta, "try": k, "side40": str(+chk["side"]),
                   "violations": len(chk["violations"]),
                   "legal": not chk["violations"]}
            out.append(rec)
            print(f"      delta {delta:.1e} try {k}: side {float(chk['side']):.12f}"
                  f" viol {len(chk['violations'])}", flush=True)
            if not chk["violations"] and (got is None or chk["side"] < got[0]):
                got = (chk["side"], z2)
            if not chk["violations"] and chk["side"] <= L0 - D(str(delta)):
                break
        if got is not None and (best is None or got[0] < best[0]):
            best = got
    return {"L_start": str(+L0), "attempts": out,
            "best_legal": None if best is None else str(+best[0]),
            "gain_vs_start": None if best is None else str(+(L0 - best[0]))}


def certifiable(theta):
    """Could this state carry an exact `Q(sqrt 2)` certificate? Only if every angle is a word."""
    off = 0
    for t in theta:
        # distance to the nearest multiple of 45 degrees
        k = round(float(t) / (np.pi / 4))
        off = max(off, abs(float(t) - k * np.pi / 4))
    return {"word_exact": bool(off < 1e-12), "max_off": str(float(off)),
            "note": ("angles are word-exact, an exact certificate is possible"
                     if off < 1e-12 else
                     "angles are not word-exact, so no exact Q(sqrt 2) certificate exists")}


def push_row(n, rows=None, deltas=(1e-4, 2e-4, 5e-4, 1e-3, 2e-3, 4e-3), tries=4):
    """The definitive push: a constrained shrink ladder from the delivered pose."""
    rows = rows or C.load_rows()
    st, note, viol = start(n, rows)
    tab = json.load(open(TAB))
    Ldel = TG.side([(str(float(r[0])), str(float(r[1])), str(float(r[2])))
                    for r in tab[str(n)]["state"]])
    rec = {"n": n, "N": len(rows[n]), "L_true_delivered": str(+Ldel), "start": note,
           "start_violations": viol}
    if st is None:
        rec["verdict"] = "no-start"
        return rec
    lad = ladder(n, rows, st, deltas, tries=tries)
    rec["ladder"] = lad
    best = lad["best_legal"]
    rec["best_legal"] = best
    LdelF = TF(str(+Ldel))
    rec["gain_vs_delivered"] = None if best is None else str(+(LdelF - TF(best)))
    rec["beats_delivered"] = bool(best is not None and TF(best) < LdelF)
    rec["verdict"] = ("improves" if rec["beats_delivered"] else
                      ("legal-not-better" if best is not None else "no-legal-state"))
    return rec


def TF(s):
    """A decimal string as an exact Fraction (no float in the decision)."""
    from fractions import Fraction as Fr
    return Fr(str(s))


def screen_row(n, rows=None, deltas=(1e-4, 5e-4), tries=3):
    """One quick shrink-and-project attempt, to measure the row's projection gap."""
    rows = rows or C.load_rows()
    st, note, viol = start(n, rows)
    tab = json.load(open(TAB))
    Ldel = TG.side([(str(float(r[0])), str(float(r[1])), str(float(r[2])))
                    for r in tab[str(n)]["state"]])
    rec = {"n": n, "N": len(rows[n]), "L_true_delivered": str(+Ldel),
           "start_violations": viol, "best_legal": None, "gap": None,
           "deltas": [str(x) for x in deltas], "tries": tries}
    if st is None:
        rec["verdict"] = "no-start"
        return rec
    lad = ladder(n, rows, st, deltas, tries=tries, seed=20261125 + n)
    best = lad["best_legal"]
    rec["best_legal"] = best
    LdelF = TF(str(+Ldel))
    rec["gap"] = None if best is None else str(+(TF(best) - LdelF))
    rec["loose"] = bool(best is None or (TF(best) - LdelF) > TF("1e-4"))
    rec["verdict"] = "legal-not-better" if best is not None else "no-legal-state"
    return rec


def run_screen(targets):
    rows = C.load_rows()
    out = {"rows": {}, "loose": [], "seconds": None}
    t0 = time.time()
    for n in targets:
        print(f"  screening n={n} ...", flush=True)
        rec = screen_row(n, rows)
        out["rows"][str(n)] = rec
        if rec.get("loose"):
            out["loose"].append(n)
        print(f"  n={n}: {rec['verdict']} best_legal {rec.get('best_legal')} gap {rec.get('gap')}"
              f" loose {rec.get('loose')}", flush=True)
    out["seconds"] = str(TF(str(time.time())).limit_denominator(100))
    with open(os.path.join(ROOT, "workspace/push/relax_screen.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"relax_angles: screen -> workspace/push/relax_screen.json; loose rows {out['loose']}")
    return out


def run_push(ns, deltas=(1e-4, 2e-4, 5e-4, 1e-3, 2e-3, 4e-3), tries=4):
    rows = C.load_rows()
    out = {"rows": {}, "seconds": None}
    t0 = time.time()
    for n in ns:
        print(f"  pushing n={n} ...", flush=True)
        rec = push_row(n, rows, deltas=deltas, tries=tries)
        out["rows"][str(n)] = rec
        print(f"  n={n}: {rec['verdict']} best_legal {rec.get('best_legal')}"
              f" gain {rec.get('gain_vs_delivered')}", flush=True)
    with open(os.path.join(ROOT, "workspace/push/relax_push.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("relax_angles: push -> workspace/push/relax_push.json")
    return out


def run(targets=TARGETS):
    rows = C.load_rows()
    out = {"rows": {}, "seconds": None}
    t0 = time.time()
    for n in targets:
        print(f"  relaxing n={n} ...", flush=True)
        rec = relax_row(n, rows)
        out["rows"][str(n)] = rec
        b = rec.get("best")
        print(f"  n={n}: {rec['verdict']}"
              f"{'' if b is None else ' side40 ' + str(FloatFmt(b['side40'])) + ' gain ' + str(FloatFmt(b['gain']))}"
              f" certifiable {rec.get('certifiable', {}).get('word_exact')}", flush=True)
    out["seconds"] = str(F(time.time() - t0).limit_denominator(100)) if False else None
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(f"relax_angles: {OUT}")
    return out


def FloatFmt(s):
    return f"{float(s):.12f}"


def selftest():
    """Two controls: the penalty sees an overlap, and the shrink objective prefers a tighter box."""
    x = np.array([0.0, 0.5, 3.0])
    y = np.array([0.0, 0.0, 0.0])
    t = np.zeros(3)
    near = near_pairs(x, y, t)
    assert overlap_penalty(x, y, t, near) > 0, "a 0.5 offset must be an overlap"
    x2 = np.array([0.0, 1.0, 3.0])
    assert overlap_penalty(x2, y, t, near_pairs(x2, y, t)) == 0, "a 1.0 offset must be clear"
    band = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    assert abs(side_of(band[:, 0], band[:, 1], band[:, 2]) - 2.0) < 1e-12, "two touching units span 2"
    tri = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, np.pi / 2]])
    from decimal import Decimal as D
    # the angle has to be pi/2 to the working precision, not the float repr of it
    assert abs(TG.side([("0", "0", "0"), ("1", "1", str(TG.PI / 2))]) - D(2)) < D("1e-38")
    print("control 1 -- the penalty is positive for a 1/2 offset and zero at a 1.0 contact, so an "
          "overlapping pair is charged and a touching one is not.")
    print("control 2 -- the side of two touching unit squares is 2, in float for the search and at "
          "40 digits in true_geom, and a 90 degree pair spans 2 as well.")
    print("relax_angles: OK (2 controls)")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    elif "--push" in sys.argv:
        ns = [int(a) for a in sys.argv[1:] if a.isdigit()] or [29]
        run_push(ns)
    elif "--screen" in sys.argv:
        ns = [int(a) for a in sys.argv[1:] if a.isdigit()] or [11, 18, 17, 29, 28, 39, 37, 41, 53, 55]
        run_screen(ns)
    else:
        run()
