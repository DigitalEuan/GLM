#!/usr/bin/env python3
r"""sat_measure.py — run 29: a TAX/NRCI-style measure on the SAT data.

User input: is there a measure on the SAT data — like the TAX
measurement the GLM uses, with NRCI as a metric?

The GLM (github.com/DigitalEuan/GLM; definitions in
upload/GLM_Complete_Number_Theory_Evidence.md §1.1-1.3) measures
binary words:

  Y  = 1/(pi + 2/pi)  in (0.264675, 0.264676)   observer/read quantum
  Q  = Y + 1/8                                     activation quantum
  B  = 10                                         coherence budget
  TAX(v)  = HW(v)*Y + |v|^2/8  =  HW(v)*Q on binary carriers
  NRCI(v) = B/(B + TAX(v))  in (0,1];  NRCI = 1 iff v = 0 (vacuum)
  regimes (proved): onBit TAX <= 5/2; coherent <= 10;
                     transitional <= 70/3; subcoherent above
  conservation (binary layer only): TAX(a^b) + 2*TAX(a&b)
                                     = TAX(a) + TAX(b)

The SAT data's native binary layer is the SYMMETRY-TIED contact: a
pair whose two axis families see the same two directions, so the four
axis penetrations pair up and the tight axes come in tied pairs
(even weight; the parity law run 28 measured as "3-tight empty").
The tied test is phase-independent:

  tied  <=>  multiset{pen_u0, pen_v0} == multiset{pen_u1, pen_v1}
             (owner family i's pens == cross family j's pens)
             within TIE_TOL; for tied pairs the tight word is forced
             by the symmetry (weight 2 edge / weight 4 corner).

Everything else is the GENERIC language (weight-1 edge/vertex,
weight-2 owner-family corner, weight-2 mixed) — the excursion layer
where run 28 found the table's slack concentrated (run18-frontier).

The measure, per packing P (the carrier is P's contact word; the
1-bits are the generic contacts):

  g(P)      = number of generic (non-tied) pair contacts
  SAT-TAX   = g * Q            (the GLM binary-layer formula, GLM's Q)
  SAT-NRCI  = 10/(10 + SAT-TAX);  = 1 iff g = 0 (the vacuum = the
              fully tied/parallel contact language)
  regime    = GLM's, with integer cutoffs exact under the proved Y
              bounds: onBit g<=6, coherent g<=25, transitional g<=59,
              subcoherent g>=60 (6Q=2.338<=5/2<7Q=2.728;
              25Q=9.742<=10<26Q=10.132; 59Q=22.991<=70/3<60Q=23.381)

Walls (container contacts) are lab-frame, not pair contacts; they are
excluded from the word and reported as a separate census (tied wall =
axis-aligned square, generic wall = tilted square).

Outputs: workspace/push/sat_measure29.json + printed report.
"""
import collections
import csv
import json
import math

import numpy as np

W = "/home/z/my-project"
CSV = f"{W}/workspace/submission/submission.csv"
TAB = f"{W}/workspace/submission/table.json"
RA = f"{W}/workspace/push/root_audit27.json"
OUT = f"{W}/workspace/push/sat_measure29.json"

# ---- GLM constants (upload/GLM_Complete_Number_Theory_Evidence.md) ----
Y = 1.0 / (math.pi + 2.0 / math.pi)
assert 0.264675 < Y < 0.264676, Y          # Calibration.lean Y_bounds
Q = Y + 0.125                              # Q = Y + 1/8
B = 10.0


def regime_of(g):
    if g <= 6:
        return "onBit"
    if g <= 25:
        return "coherent"
    if g <= 59:
        return "transitional"
    return "subcoherent"


def tax_of(g):
    return g * Q


def nrci_of(g):
    return B / (B + g * Q)


CONTACT_TOL = 1e-7
# TIE_TOL sits in the measured EMPTY GAP of the tie-residual
# distribution: the tied population (exact parallelism — float noise
# of exact constructions) lives at <= ~1e-12; the generic continuum
# starts at ~1e-8 (44-contact bridge) and runs to ~1e-1.  Nothing
# lives in (1e-11, 1e-8); any cut there classifies identically.
TIE_TOL = 1e-9
BRIDGE_TOL = 1e-6     # generic contacts with residual <= this are the
                      # near-parallel bridge (construction-noise level)
WALL_TOL = 1e-7
ALIGN_TOL = 1e-6      # rad; wall tie = square axis-aligned to container


def pair_data(state):
    """Full-matrix SAT data: the four family-pen matrices + bbox."""
    xy = np.array([(s[0], s[1]) for s in state], dtype=float)
    th = np.array([s[2] for s in state], dtype=float)
    n = len(state)
    cs, sn = np.cos(th), np.sin(th)
    ex = 0.5 * (np.abs(cs) + np.abs(sn))
    lox = float(np.min(xy[:, 0] - ex)); hix = float(np.max(xy[:, 0] + ex))
    loy = float(np.min(xy[:, 1] - ex)); hiy = float(np.max(xy[:, 1] + ex))
    w, h = hix - lox, hiy - loy
    PU = np.stack([cs, sn], axis=1) @ xy.T          # c_j . u_i
    PV = np.stack([-sn, cs], axis=1) @ xy.T
    Eu = 0.5 * (np.abs(np.outer(cs, cs) + np.outer(sn, sn))
                + np.abs(np.outer(-sn, cs) + np.outer(cs, sn)))
    dU = np.diag(PU)[:, None] - PU                  # (c_i - c_j).u_i
    dV = np.diag(PV)[:, None] - PV
    pen_u0 = 0.5 + Eu - np.abs(dU)                  # axes of i
    pen_v0 = 0.5 + Eu - np.abs(dV)
    pen_u1 = 0.5 + Eu.T - np.abs(dU.T)              # axes of j
    pen_v1 = 0.5 + Eu.T - np.abs(dV.T)
    pens = np.stack([pen_u0, pen_v0, pen_u1, pen_v1])
    pair = pens.min(axis=0)                          # min over 4 axes
    return pens, pair, w, h, (ex, xy, lox, hix, loy, hiy, th)


def review_row(state, n):
    pens, pair, w, h, bb = pair_data(state)
    ex, xy, lox, hix, loy, hiy, th = bb
    L = max(w, h)
    iu = np.triu_indices(n, k=1)
    gap = -pair[iu]                                  # per pair (upper tri)
    contact = gap <= CONTACT_TOL                     # touching
    C = int(contact.sum())
    # weight = # tight axes per contact pair
    weight = (pens[:, iu[0], iu[1]] <= CONTACT_TOL).sum(axis=0)
    # tie residual: multiset equality of the two families' pens
    p0a = np.sort(np.stack([pens[0][iu], pens[1][iu]]), axis=0)   # family i
    p1a = np.sort(np.stack([pens[2][iu], pens[3][iu]]), axis=0)   # family j
    resid = np.abs(p0a - p1a).max(axis=0)
    tied = resid <= TIE_TOL
    gw = weight[contact]
    tg = tied[contact]
    # census by (tied?, weight)
    cens = {
        "tied_w2": int((tg & (gw == 2)).sum()),
        "tied_w4": int((tg & (gw == 4)).sum()),
        "gen_w1": int((~tg & (gw == 1)).sum()),
        "gen_w2": int((~tg & (gw == 2)).sum()),
        "gen_w3": int((~tg & (gw == 3)).sum()),
        "gen_w4": int((~tg & (gw == 4)).sum()),
    }
    # near-parallel bridge among the generic (residual in (TIE_TOL, BRIDGE_TOL])
    g_bridge = int((contact & ~tied & (resid <= BRIDGE_TOL)).sum())
    # tie residual bands for the global histogram
    g = cens["gen_w1"] + cens["gen_w2"] + cens["gen_w3"] + cens["gen_w4"]
    # walls (binding sides only), lab frame
    if w > h + 1e-12:
        binding = ("L", "R")
    elif h > w + 1e-12:
        binding = ("T", "B")
    else:
        binding = ("L", "R", "T", "B")
    gap_wall = {"L": (xy[:, 0] - ex) - lox, "R": hix - (xy[:, 0] + ex),
                "T": hiy - (xy[:, 1] + ex), "B": (xy[:, 1] - ex) - loy}
    wall_binding = sum(int((gap_wall[s] <= WALL_TOL).sum()) for s in binding)
    binding_tilted = np.zeros(n, bool)
    for s in binding:
        binding_tilted |= gap_wall[s] <= WALL_TOL
    tmod = np.mod(th, math.pi / 2)
    aligned = np.minimum(tmod, math.pi / 2 - tmod) <= ALIGN_TOL
    wall_tied = int((binding_tilted & aligned).sum())
    wall_generic = int((binding_tilted & ~aligned).sum())
    # squares touched by a generic contact at all
    ii, jj = iu
    gen_full = contact & ~tied           # full-length: contact and generic
    in_gen = np.zeros(n, bool)
    in_gen[ii[gen_full]] = True
    in_gen[jj[gen_full]] = True
    return {
        "n": n, "L": L, "w": w, "h": h, "C": C,
        "census": cens, "g": g, "g_bridge": g_bridge,
        "phi": (g / C) if C else 0.0,
        "TAX": tax_of(g), "NRCI": nrci_of(g),
        "regime": regime_of(g),
        "wall_binding": wall_binding, "wall_tied": wall_tied,
        "wall_generic": wall_generic,
        "generic_squares": int(in_gen.sum()),
        "max_overlap": float(max(0.0, pair[iu].max() if n > 1 else 0.0)),
    }


def main():
    tab = json.load(open(TAB))
    ra = json.load(open(RA))
    proven = {int(k) for k in ra["proven_floors"]}
    states = collections.defaultdict(list)
    for row in csv.DictReader(open(CSV)):
        states[int(row["n"])].append(
            (float(row["x"]), float(row["y"]), float(row["angle"])))
    for n in states:
        states[n].sort()

    rows = []
    resid_dec = collections.Counter()      # decade histogram over contacts
    tied_max, gen_min = 0.0, math.inf
    for n in sorted(states):
        r = review_row(states[n], n)
        K = math.ceil(math.sqrt(n))
        src = tab[str(n)].get("src", "")
        r["K"] = K
        r["src"] = src
        r["class"] = src.split(":")[0] or "none"
        r["depth"] = K - tab[str(n)]["L"]
        r["status"] = ("proven" if n in proven else
                       "open" if tab[str(n)]["L"] >= K - 1e-9 else "sub")
        rows.append(r)
        # residual bands (recompute cheaply from census + resid)
        pens, pair, w, h, bb = pair_data(states[n])
        iu = np.triu_indices(n, k=1)
        gap = -pair[iu]
        contact = gap <= CONTACT_TOL
        if contact.any():
            p0 = np.sort(np.stack([pens[0][iu], pens[1][iu]]), axis=0)
            p1 = np.sort(np.stack([pens[2][iu], pens[3][iu]]), axis=0)
            res = np.abs(p0 - p1).max(axis=0)[contact]
            tiedm = res <= TIE_TOL
            if res[tiedm].size:
                tied_max = max(tied_max, float(res[tiedm].max()))
            if (~tiedm).any():
                gen_min = min(gen_min, float(res[~tiedm].min()))
            for v in res:
                resid_dec[int(math.floor(math.log10(v) if v > 0 else -16))] += 1
        assert r["census"]["gen_w3"] == 0, (n, r["census"])
        assert r["census"]["gen_w4"] == 0, (n, r["census"])

    # ---------------- aggregates
    def agg(sel):
        rs = [r for r in rows if sel(r)]
        if not rs:
            return None
        gs = np.array([r["g"] for r in rs], float)
        return {
            "rows": len(rs),
            "vacuum": int((gs == 0).sum()),
            "median_g": float(np.median(gs)),
            "median_TAX": float(np.median([r["TAX"] for r in rs])),
            "median_NRCI": round(float(np.median([r["NRCI"] for r in rs])), 6),
            "median_phi": round(float(np.median([r["phi"] for r in rs])), 6),
            "regimes": dict(collections.Counter(r["regime"] for r in rs)),
            "wall_generic_median": float(np.median(
                [r["wall_generic"] for r in rs])),
            "g_min": int(gs.min()), "g_max": int(gs.max()),
        }

    by_class = {c: agg(lambda r, c=c: r["class"] == c)
                for c in sorted({r["class"] for r in rows})}
    by_status = {s: agg(lambda r, s=s: r["status"] == s)
                 for s in ("open", "sub", "proven")}

    subs = [r for r in rows if r["status"] == "sub"]
    d = np.array([r["depth"] for r in subs])
    gg = np.array([r["g"] for r in subs], float)
    pear = float(np.corrcoef(gg, d)[0, 1]) if len(subs) > 2 else None
    pear_score = (float(np.corrcoef(gg, d / np.sqrt([r["n"] for r in subs]))[0, 1])
                  if len(subs) > 2 else None)
    frontier = [r for r in rows if r["class"] == "run18-frontier"]
    fr = {
        "rows": len(frontier),
        "median_g": float(np.median([r["g"] for r in frontier])),
        "median_depth": float(np.median([r["depth"] for r in frontier])),
        "regimes": dict(collections.Counter(r["regime"] for r in frontier)),
        "vacuum": sum(1 for r in frontier if r["g"] == 0),
    }
    vac_rows = [{"n": r["n"], "class": r["class"]} for r in rows if r["g"] == 0]
    vac_by_class = collections.Counter(v["class"] for v in vac_rows)
    deep = [r for r in subs if r["depth"] >= 0.1]
    onbit_coherent_sub = [r for r in subs if r["g"] <= 25]
    r50 = next(r for r in rows if r["n"] == 50)

    print("=== SAT MEASURE (run 29) — TAX/NRCI on the SAT data ===")
    print(f"  GLM constants: Y={Y:.9f} (bounds ok), Q={Q:.9f}, B={B:g}")
    print(f"  tie residual gap: tied max {tied_max:.2e} | generic min "
          f"{gen_min:.2e} | TIE_TOL {TIE_TOL:g} "
          f"({math.log10(gen_min / max(tied_max, 1e-300)):.1f} decades)")
    print(f"  weight-3 and generic weight-4 contacts: 0 in all 1000 rows "
          f"(asserted)")
    print(f"  total contacts {sum(r['C'] for r in rows)}, generic "
          f"{sum(r['g'] for r in rows)} "
          f"({sum(r['g'] for r in rows) / sum(r['C'] for r in rows):.2%})")
    print("\n--- by class (g = generic contacts; TAX = g*Q; NRCI = 10/(10+TAX)) ---")
    for c, a in by_class.items():
        print(f"  {c:15s} rows={a['rows']:3d} vac={a['vacuum']:3d} "
              f"g med={a['median_g']:6.1f} [{a['g_min']}..{a['g_max']}] "
              f"TAX med={a['median_TAX']:7.3f} NRCI med={a['median_NRCI']:.4f} "
              f"phi med={a['median_phi']:.4f} "
              f"regimes={dict(sorted(a['regimes'].items()))}")
    print("\n--- by status ---")
    for s, a in by_status.items():
        if a:
            print(f"  {s:7s} rows={a['rows']:3d} vac={a['vacuum']:3d} "
                  f"g med={a['median_g']:6.1f} NRCI med={a['median_NRCI']:.4f} "
                  f"regimes={dict(sorted(a['regimes'].items()))}")
    print(f"\n--- vacuum census (NRCI = 1 exactly) ---")
    print(f"  {len(vac_rows)} rows at the vacuum; by class: "
          f"{dict(vac_by_class.most_common())}")
    print(f"\n--- tax vs depth (sub rows, n={len(subs)}) ---")
    print(f"  Pearson corr(g, depth) = {pear:.4f}")
    print(f"  Pearson corr(g, depth/sqrt(n)) = {pear_score:.4f}")
    print(f"  rows with depth >= 0.1: {len(deep)}, their g: "
          f"min {min(r['g'] for r in deep)}, "
          f"median {float(np.median([r['g'] for r in deep])):.1f}")
    print(f"  sub rows with g <= 25 (coherent or better): "
          f"{len(onbit_coherent_sub)}, their max depth: "
          f"{max(r['depth'] for r in onbit_coherent_sub):.6f}")
    print(f"\n--- frontier calibration (run18-frontier, the record class) ---")
    print(f"  rows={fr['rows']} vacuum={fr['vacuum']} median g={fr['median_g']:.1f} "
          f"median depth={fr['median_depth']:.6f} regimes={fr['regimes']}")
    print(f"\n--- n=50 validation (run-26/28 decode row) ---")
    print(f"  C={r50['C']} (105 expected), g={r50['g']}, census={r50['census']}, "
          f"TAX={r50['TAX']:.4f}, NRCI={r50['NRCI']:.6f}, regime={r50['regime']}, "
          f"phi={r50['phi']:.4f}")
    print(f"  walls: binding={r50['wall_binding']} tied={r50['wall_tied']} "
          f"generic={r50['wall_generic']}")

    json.dump({
        "run": 29, "part": "TAX/NRCI measure on the SAT data (user input)",
        "glm_constants": {"Y": Y, "Q": Q, "B": B,
                          "Y_bounds": [0.264675, 0.264676],
                          "regime_cutoffs_g": {"onBit": 6, "coherent": 25,
                                               "transitional": 59},
                          "regime_thresholds_tax": {"onBit": 2.5, "coherent": 10.0,
                                                    "transitional": 70/3}},
        "tolerances": {"contact": CONTACT_TOL, "tie": TIE_TOL,
                       "wall": WALL_TOL, "align": ALIGN_TOL},
        "definitions": {
            "tied": ("multiset{pen_u0,pen_v0} == multiset{pen_u1,pen_v1} "
                     "within TIE_TOL — the SAT data's binary layer; tight "
                     "axes come in symmetry-tied pairs (even weight)"),
            "generic": "every other contact (weight 1, or weight 2 "
                       "owner-family/mixed) — the excursion language",
            "carrier": "the packing's contact word; 1-bits = generic contacts",
            "SAT_TAX": "g * Q (GLM binary-layer formula, GLM's Q)",
            "SAT_NRCI": "10/(10 + SAT_TAX); = 1 iff g = 0 (the vacuum)",
            "walls": "lab-frame container contacts; excluded from the word, "
                     "reported separately (tied = axis-aligned square)"},
        "tie_gap": {"tied_max": tied_max, "generic_min": gen_min,
                    "TIE_TOL": TIE_TOL,
                    "residual_decades": {str(k): v for k, v in
                                          sorted(resid_dec.items())}},
        "headline": {
            "total_contacts": sum(r["C"] for r in rows),
            "total_generic": sum(r["g"] for r in rows),
            "generic_share": sum(r["g"] for r in rows) / sum(r["C"] for r in rows),
            "vacuum_rows": len(vac_rows),
            "vacuum_by_class": dict(vac_by_class.most_common())},
        "by_class": by_class, "by_status": by_status,
        "frontier": fr,
        "tax_depth": {
            "n_sub": len(subs), "pearson_g_depth": pear,
            "pearson_g_score": pear_score,
            "deep_rows": len(deep),
            "deep_g_min": min((r["g"] for r in deep), default=None),
            "deep_g_median": float(np.median([r["g"] for r in deep])) if deep else None,
            "sub_coherent_rows": len(onbit_coherent_sub),
            "sub_coherent_max_depth": max((r["depth"] for r in onbit_coherent_sub), default=None)},
        "n50": {"C": r50["C"], "g": r50["g"], "census": r50["census"],
                "TAX": r50["TAX"], "NRCI": r50["NRCI"], "regime": r50["regime"],
                "walls": [r50["wall_binding"], r50["wall_tied"], r50["wall_generic"]]},
        "rows": [{k: v for k, v in r.items()} for r in rows],
    }, open(OUT, "w"), indent=1)
    print("\nledger ->", OUT)


if __name__ == "__main__":
    main()
