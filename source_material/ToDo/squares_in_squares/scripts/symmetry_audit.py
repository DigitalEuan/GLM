#!/usr/bin/env python3
r"""symmetry_audit.py — run 31 (user input): "many optimal grids are
symmetrical and efficient."

Treat the input as a hypothesis and measure it on the delivered table
(run 30, score 22.645991): a D4 point-group census over all 1000
packings, joined with the SAT measures (recomputed per row here:
C, g, phi, NRCI — run-29 currency) and depth/class/status.

Method.  The container's own symmetry group is D4 (8 elements about
the bbox center (mx, my)): identity, rotations 90/180/270, and the
four reflections (vertical, horizontal, the two diagonals).  A square
is 4-fold, so on the orientation class theta mod pi/2:
  - rotations leave theta invariant;
  - every reflection maps theta -> -theta (mod pi/2).
An element g holds iff the mapped multiset of (center, theta) equals
the original: every mapped square matches a distinct original within
tol (distinctness is automatic — non-overlap keeps centers >= 1 apart
while tol = 1e-6).  Per element we record the matched distance dmax;
for the ledger also the "distance to one more symmetry" (min dmax
over non-holding elements) — a continuous asymmetry measure.

 theta_fixed: all thetas in {0, pi/4} (mod pi/2) — then reflections
 act on centers alone (the octant-fixed case; grids and 45-degree
 families live here).

Ledger: workspace/push/symmetry_audit31.json.
"""
import json
import math
import sys
import time

import numpy as np

sys.path.insert(0, "/home/z/my-project/scripts")
from sat_measure import review_row

W = "/home/z/my-project"
TAB = f"{W}/workspace/submission/table.json"
OUT = f"{W}/workspace/push/symmetry_audit31.json"
PHI = math.pi / 2
TOL = 1e-6
TOL_TH = 1e-6
ELEMENTS = ("e", "r90", "r180", "r270", "V", "H", "D", "A")


def wrap(t):
    return np.mod(t, PHI)


def angdiff(a, b):
    d = np.abs(wrap(a) - wrap(b))
    return np.minimum(d, PHI - d)


def census(state):
    """-> dict(elements holding, dmax per element, dmin_extra,
    theta_fixed, mx, my)."""
    n = len(state)
    X = np.array([(s[0], s[1]) for s in state], dtype=float)
    TH = wrap(np.array([s[2] for s in state], dtype=float))
    cs, sn = np.cos(TH), np.sin(TH)
    ex = 0.5 * (np.abs(cs) + np.abs(sn))
    lox = float(np.min(X[:, 0] - ex)); hix = float(np.max(X[:, 0] + ex))
    loy = float(np.min(X[:, 1] - ex)); hiy = float(np.max(X[:, 1] + ex))
    mx = (lox + hix) / 2.0
    my = (loy + hiy) / 2.0
    dx = X[:, 0] - mx
    dy = X[:, 1] - my

    maps = {
        "r90":  ((mx - dy, my + dx), False),
        "r180": ((mx - dx, my - dy), False),
        "r270": ((mx + dy, my - dx), False),
        "V":    ((mx - dx, my + dy), True),
        "H":    ((mx + dx, my - dy), True),
        "D":    ((mx + dy, my + dx), True),
        "A":    ((mx - dy, my - dx), True),
    }
    hold = {"e": 0.0}
    dmax_all = {}
    for g, ((MX, MY), flip) in maps.items():
        M = np.stack([MX, MY], axis=1)
        THm = wrap(-TH) if flip else TH
        # pairwise distances O_i -- M_j
        D = np.sqrt(((X[:, None, :] - M[None, :, :]) ** 2).sum(-1))
        imatch = np.argmin(D, axis=0)
        dmin = D[imatch, np.arange(n)]
        thok = angdiff(THm, TH[imatch]) < TOL_TH
        dmax = float(dmin.max())
        dmax_all[g] = dmax
        if dmax < TOL and bool(thok.all()):
            hold[g] = dmax
    non = [dmax_all[g] for g in ELEMENTS if g not in hold]
    dmin_extra = min(non) if non else 0.0
    tf = bool(np.all(np.minimum(wrap(TH), PHI - wrap(TH)) < 1e-9)
              or np.all(np.minimum(np.abs(wrap(TH) - PHI / 4),
                                   PHI / 4 - np.abs(wrap(TH) - PHI / 4)) < 1e-9))
    return {"hold": sorted(hold), "dmax": {g: round(dmax_all[g], 9)
                                           for g in dmax_all},
            "dmin_extra": round(dmin_extra, 9),
            "theta_fixed_0_or_45": tf,
            "center": (round(mx, 6), round(my, 6))}


def group_name(hold):
    k = len(hold)
    if k == 8:
        return "D4"
    if k == 4:
        return "D2"
    if k == 2:
        return "C2" if "r180" in hold else "Cs"
    return "C1"


def main():
    t0 = time.time()
    tab = json.load(open(TAB))
    rows = []
    for n in range(1, 1001):
        rec = tab[str(n)]
        state = rec["state"]
        L = rec["L"]
        K = math.ceil(math.sqrt(n))
        c = census(state)
        m = review_row(state, n)
        cls = rec.get("src", "?").split(":")[0]
        rows.append({
            "n": n, "L": L, "K": K,
            "status": "tied" if L >= K - 1e-9 else "sub",
            "class": cls,
            "depth": round((K - L) / math.sqrt(n), 9),
            "G_size": len(c["hold"]), "group": group_name(c["hold"]),
            "elements": c["hold"],
            "dmin_extra": c["dmin_extra"],
            "theta_fixed": c["theta_fixed_0_or_45"],
            "C": m["C"], "g": m["g"], "phi": round(m["phi"], 6),
            "NRCI": round(m["NRCI"], 6), "regime": m["regime"],
            "C_per_n": round(m["C"] / n, 6),
        })
    json.dump(rows, open(OUT, "w"))

    # ------------------------------------------------ aggregates
    def agg(sel):
        s = [r for r in rows if sel(r)]
        if not s:
            return {"count": 0}
        return {
            "count": len(s),
            "sym_frac": round(sum(1 for r in s if r["G_size"] >= 2) / len(s), 4),
            "mean_G": round(sum(r["G_size"] for r in s) / len(s), 3),
            "D4_frac": round(sum(1 for r in s if r["G_size"] == 8) / len(s), 4),
            "mean_depth": round(sum(r["depth"] for r in s) / len(s), 6),
            "mean_C_per_n": round(sum(r["C_per_n"] for r in s) / len(s), 4),
            "mean_phi": round(sum(r["phi"] for r in s) / len(s), 6),
            "mean_NRCI": round(sum(r["NRCI"] for r in s) / len(s), 6),
        }

    by = lambda f: {k: agg(lambda r, k=k: f(r) == k)
                    for k in {f(r) for r in rows}}
    sub = [r for r in rows if r["status"] == "sub"]
    tied = [r for r in rows if r["status"] == "tied"]

    def corr(a, b, sel):
        x = np.array([a(r) for r in rows if sel(r)])
        y = np.array([b(r) for r in rows if sel(r)])
        if len(x) < 3:
            return None
        return round(float(np.corrcoef(x, y)[0, 1]), 4)

    out = {
        "rows": rows,
        "headline": {
            "all": agg(lambda r: True),
            "tied": {"count": len(tied),
                     "sym_frac": round(sum(1 for r in tied if r["G_size"] >= 2)
                                       / len(tied), 4),
                     "note": ("stored tied states are tail-drop asymmetric "
                              "by construction; a symmetric rearrangement "
                              "exists for every tied row (canonical form) "
                              "— the census measures stored states")},
            "sub": {"count": len(sub), **{k: v for k, v in
                                          agg(lambda r: r["status"] == "sub").items()
                                          if k != "count"}},
            "by_class": by(lambda r: r["class"]),
            "by_band": {"1..324": agg(lambda r: r["n"] <= 324),
                        "325..1000": agg(lambda r: r["n"] > 324)},
            "correlations_sub": {
                "G_size~depth": corr(lambda r: r["G_size"], lambda r: r["depth"],
                                     lambda r: r["status"] == "sub"),
                "G_size~C_per_n": corr(lambda r: r["G_size"], lambda r: r["C_per_n"],
                                       lambda r: r["status"] == "sub"),
                "depth~C_per_n": corr(lambda r: r["depth"], lambda r: r["C_per_n"],
                                      lambda r: r["status"] == "sub"),
                "depth~phi": corr(lambda r: r["depth"], lambda r: r["phi"],
                                  lambda r: r["status"] == "sub"),
                "G_size~phi": corr(lambda r: r["G_size"], lambda r: r["phi"],
                                   lambda r: r["status"] == "sub"),
            },
            "anchors": {str(r["n"]): {k: r[k] for k in
                                      ("group", "elements", "depth", "phi",
                                       "NRCI", "C", "C_per_n", "class")}
                        for r in rows if r["n"] in (5, 11, 17, 19, 50, 299,
                                                    325, 341, 356)},
        },
    }
    json.dump(out, open(OUT, "w"), indent=1)
    h = out["headline"]
    print(f"({time.time()-t0:.0f}s) rows: {len(rows)}")
    print(f"ALL: sym {h['all']['sym_frac']:.2%} mean|G| {h['all']['mean_G']}"
          f" D4 {h['all']['D4_frac']:.2%}")
    print(f"TIED({h['tied']['count']}): sym {h['tied']['sym_frac']:.2%}")
    print(f"SUB({h['sub']['count']}): sym {h['sub']['sym_frac']:.2%} "
          f"mean|G| {h['sub']['mean_G']} D4 {h['sub']['D4_frac']:.2%} "
          f"depth {h['sub']['mean_depth']:.6f} C/n {h['sub']['mean_C_per_n']:.3f}")
    print("BY CLASS:")
    for k, v in sorted(h["by_class"].items(),
                       key=lambda kv: -kv[1].get("count", 0)):
        if v["count"]:
            print(f"  {k:16s} n={v['count']:4d} sym {v['sym_frac']:.2%} "
                  f"D4 {v['D4_frac']:.2%} depth {v.get('mean_depth', 0):.6f} "
                  f"C/n {v.get('mean_C_per_n', 0):.3f} phi {v.get('mean_phi', 0):.4f}")
    print("BY BAND: 1..324 sym %.2f%% | 325..1000 sym %.2f%%" % (
        h["by_band"]["1..324"]["sym_frac"] * 100,
        h["by_band"]["325..1000"]["sym_frac"] * 100))
    print("CORR (sub rows):", h["correlations_sub"])
    print("ANCHORS:")
    for k, v in h["anchors"].items():
        print(f"  n={k:>4s} {v['group']:3s} depth {v['depth']:.6f} "
              f"phi {v['phi']:.4f} NRCI {v['NRCI']:.4f} C/n {v['C_per_n']:.3f} "
              f"({v['class']})")
    print("ledger ->", OUT)


if __name__ == "__main__":
    main()
