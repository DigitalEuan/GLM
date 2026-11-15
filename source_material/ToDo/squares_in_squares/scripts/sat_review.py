#!/usr/bin/env python3
r"""sat_review.py — run 28: review the SAT data for insight.

"The SAT data" = what the verifier (packlib.verify's separating-axis
test) computes per packing: for every square pair, the tightest
separating axis and its margin (margin = -pair penetration value;
0 = touching, > 0 = gap); plus the bbox wall touches.

For each of the 1000 delivered packings (submission.csv) this
computes:
  contacts        pairs with margin <= 1e-7 (touching edge-to-edge)
  contact normals the argmin axis per contact pair: 0=u_i, 1=v_i
                  (owner square i's axes), 2=u_j, 3=v_j — the local
                  geometric language of the packing
  wall touches    squares touching the L-defining (binding) sides;
                  binding = the two sides achieving max(w,h), all 4
                  if w == h
  free squares    no pair contact AND no wall touch on any side
                  (floating in a cavity)
  nearest gap     min margin over non-contact pairs (how close the
                  next contact is to forming — insertion room)
  Maxwell ratio   (contacts + binding wall touches) / (3n - 3),
                  first-order jamming count (n >= 4; squares have 3
                  DOF each, minus 3 rigid motions).  Caveat: contacts
                  are one-sided (block compression only), so this is
                  a counting measure, not a jamming proof.

Groups: by src class (grid / run18-frontier / chain3 / exact /
closure / gobel* / removal / aux / register) and by status
(open / sub-grid / proven floor).

Outputs: workspace/push/sat_review28.json + a printed insight summary.
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
OUT = f"{W}/workspace/push/sat_review28.json"

CONTACT_TOL = 1e-7     # margin <= tol  -> pair in contact
WALL_TOL = 1e-7


def pair_data(state):
    """Per-pair SAT data.  Mirrors packlib.verify's formulas, returns
    (margins, axis_ids) for the upper-triangle pairs, plus (w, h)."""
    xy = np.array([(s[0], s[1]) for s in state], dtype=float)
    th = np.array([s[2] for s in state], dtype=float)
    n = len(state)
    cs, sn = np.cos(th), np.sin(th)
    ex = 0.5 * (np.abs(cs) + np.abs(sn))
    lox = float(np.min(xy[:, 0] - ex)); hix = float(np.max(xy[:, 0] + ex))
    loy = float(np.min(xy[:, 1] - ex)); hiy = float(np.max(xy[:, 1] + ex))
    w, h = hix - lox, hiy - loy
    if n < 2:
        e = np.zeros(0)
        return (np.zeros(0), np.zeros(0, dtype=int), np.zeros(0, dtype=int),
                w, h, (ex, xy, lox, hix, loy, hiy))
    PU = np.stack([cs, sn], axis=1) @ xy.T          # PU[i,j] = c_j . u_i
    PV = np.stack([-sn, cs], axis=1) @ xy.T
    Eu = 0.5 * (np.abs(np.outer(cs, cs) + np.outer(sn, sn))
                + np.abs(np.outer(-sn, cs) + np.outer(cs, sn)))
    dU = np.diag(PU)[:, None] - PU                  # (c_i - c_j) . u_i
    dV = np.diag(PV)[:, None] - PV
    pen_u0 = 0.5 + Eu - np.abs(dU)                  # value along u_i
    pen_v0 = 0.5 + Eu - np.abs(dV)                  # along v_i
    pen_u1 = 0.5 + Eu.T - np.abs(dU.T)              # along u_j
    pen_v1 = 0.5 + Eu.T - np.abs(dV.T)              # along v_j
    iu = np.triu_indices(n, k=1)
    pens = np.stack([pen_u0[iu], pen_v0[iu], pen_u1[iu], pen_v1[iu]])
    pair = pens.min(axis=0)
    axis = pens.argmin(axis=0)                      # 0=u_i 1=v_i 2=u_j 3=v_j
    n_tight = (pens <= CONTACT_TOL).sum(axis=0)     # #SAT axes at zero
    return -pair, axis, n_tight, w, h, (ex, xy, lox, hix, loy, hiy)   # margins


def review_row(state, n):
    margins, axes, n_tight, w, h, bb = pair_data(state)
    ex, xy, lox, hix, loy, hiy = bb
    L = max(w, h)
    # binding sides: the sides achieving max(w, h); all 4 if square bbox
    if w > h + 1e-12:
        binding = ("L", "R")
    elif h > w + 1e-12:
        binding = ("T", "B")
    else:
        binding = ("L", "R", "T", "B")
    touch = {
        "L": (xy[:, 0] - ex) - lox <= WALL_TOL,
        "R": hix - (xy[:, 0] + ex) <= WALL_TOL,
        "T": hiy - (xy[:, 1] + ex) <= WALL_TOL,
        "B": (xy[:, 1] - ex) - loy <= WALL_TOL,
    }
    any_touch = touch["L"] | touch["R"] | touch["T"] | touch["B"]
    wall_binding = sum(int(touch[s].sum()) for s in binding)
    wall_all = int(any_touch.sum())
    in_contact = np.zeros(n, dtype=bool)
    if len(margins):
        contact_mask = margins <= CONTACT_TOL
        contacts = int(contact_mask.sum())
        # contact-normal census (argmin axis of contact pairs)
        axis_census = np.bincount(axes[contact_mask], minlength=4)
        # contact-TYPE census: how many SAT axes are simultaneously tight
        #   1 tight axis  -> generic edge/vertex contact (one direction)
        #   2 tight axes  -> parallel edge contact (u_i || u_j, one
        #                    direction) OR non-parallel corner (two)
        #   4 tight axes  -> parallel corner (x and y directions both)
        type_census = np.bincount(n_tight[contact_mask], minlength=5)[:5]
        # squares involved in contacts
        ii, jj = np.triu_indices(n, k=1)
        in_contact[ii[contact_mask]] = True
        in_contact[jj[contact_mask]] = True
        near = margins[~contact_mask]
        nearest_gap = float(near.min()) if len(near) else None
        worst_overlap = float(-margins.min())      # >0 would be overlap
    else:
        contacts, axis_census, nearest_gap = 0, np.zeros(4, int), None
        type_census, worst_overlap = np.zeros(5, int), 0.0
    free = int((~in_contact & ~any_touch).sum())
    dof = 3 * n - 3 if n >= 2 else 0
    ratio = ((contacts + wall_binding) / dof) if dof >= 6 else None
    return {
        "n": n, "L": L, "w": w, "h": h, "binding": "".join(binding),
        "contacts": contacts, "wall_binding": wall_binding,
        "wall_all": wall_all, "free": free,
        "axis_census": axis_census.tolist(),   # [u_i, v_i, u_j, v_j]
        "type_census": type_census.tolist(),   # [#tight axes = 0..4]
        "nearest_gap": nearest_gap,
        "max_overlap": worst_overlap,          # must be <= 0 (verified)
        "ratio": ratio,
        "contact_squares": int(in_contact.sum()),
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
        states[n].sort()          # stable order

    rows = []
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
        assert r["max_overlap"] <= 1e-9, (n, r["max_overlap"])  # SAT clean
        assert abs(r["L"] - tab[str(n)]["L"]) <= 5e-9, (n, r["L"])
        rows.append(r)

    # ---------------- aggregates by class
    def agg(sel):
        rs = [r for r in rows if sel(r)]
        if not rs:
            return None
        n_tot = sum(r["n"] for r in rs)
        c_tot = sum(r["contacts"] for r in rs)
        w_tot = sum(r["wall_binding"] for r in rs)
        ax = [sum(r["axis_census"]) for r in rs]
        ax4 = [sum(r["axis_census"][k] for r in rs) for k in range(4)]
        ty = [sum(r["type_census"][k] for r in rs) for k in range(5)]
        ratios = [r["ratio"] for r in rs if r["ratio"] is not None]
        return {
            "rows": len(rs), "n_total": n_tot,
            "contacts": c_tot, "wall_binding": w_tot,
            "avg_contacts_per_row": round(c_tot / len(rs), 1),
            "contacts_per_square": round(c_tot / n_tot, 3),
            "axis_census": ax4, "axis_census_total": sum(ax),
            "type_census_1_2_3_4": ty[1:],
            "free_squares": sum(r["free"] for r in rs),
            "nearest_gap_median": (
                float(np.median([r["nearest_gap"] for r in rs
                                 if r["nearest_gap"] is not None]))
                if any(r["nearest_gap"] is not None for r in rs) else None),
            "ratio_median": (round(float(np.median(ratios)), 3)
                             if ratios else None),
            "ratio_min": round(min(ratios), 3) if ratios else None,
            "ratio_max": round(max(ratios), 3) if ratios else None,
        }

    by_class = {}
    classes = sorted({r["class"] for r in rows})
    for c in classes:
        a = agg(lambda r, c=c: r["class"] == c)
        a["rows_detail"] = [
            {"n": r["n"], "contacts": r["contacts"],
             "wall": r["wall_binding"], "free": r["free"],
             "ratio": r["ratio"], "nearest_gap": r["nearest_gap"],
             "axis": r["axis_census"], "status": r["status"],
             "depth": round(r["depth"], 6)}
            for r in rows if r["class"] == c]
        by_class[c] = a
    by_status = {s: agg(lambda r, s=s: r["status"] == s)
                 for s in ("open", "sub", "proven")}

    # ---------------- headline lists
    sub_rows = [r for r in rows if r["status"] == "sub" and r["ratio"]]
    most_slack = sorted(sub_rows, key=lambda r: r["ratio"])[:12]
    most_constr = sorted(sub_rows, key=lambda r: -r["ratio"])[:12]
    free_rows = [r for r in rows if r["free"] > 0]
    grid_like = [r for r in rows
                 if r["status"] == "open" and r["contacts"] > 0]
    near_forming = sorted([r for r in rows if r["nearest_gap"] is not None],
                          key=lambda r: r["nearest_gap"])[:15]

    print("=== SAT DATA REVIEW (run 28) — all 1000 packings ===")
    print(f"  verified: max_overlap <= 1e-9 on every row (SAT clean)")
    print(f"  total pair contacts: {sum(r['contacts'] for r in rows)}")
    print(f"  total binding-wall touches: "
          f"{sum(r['wall_binding'] for r in rows)}")
    print(f"  free squares (no contact, no wall): "
          f"{sum(r['free'] for r in rows)} in {len(free_rows)} rows")
    ax4 = [sum(r["axis_census"][k] for r in rows) for k in range(4)]
    ty = [sum(r["type_census"][k] for r in rows) for k in range(5)]
    tot = sum(ax4) or 1
    print(f"  contact-normal census (owner axes vs cross axes):")
    print(f"    u_i {ax4[0]} ({ax4[0]/tot:.1%}) | v_i {ax4[1]} "
          f"({ax4[1]/tot:.1%}) | u_j {ax4[2]} ({ax4[2]/tot:.1%}) | "
          f"v_j {ax4[3]} ({ax4[3]/tot:.1%})")
    print(f"    (owner-family share u_i+v_i = {(ax4[0]+ax4[1])/tot:.1%}; "
          f"by i/j symmetry the split within a family is not meaningful)")
    ctot = sum(ty) or 1
    print(f"  contact-TYPE census (simultaneously tight SAT axes):")
    print(f"    1 tight (generic edge/vertex) {ty[1]} ({ty[1]/ctot:.1%}) | "
          f"2 tight (parallel edge / non-parallel corner) {ty[2]} "
          f"({ty[2]/ctot:.1%}) | 3 tight {ty[3]} ({ty[3]/ctot:.1%}) | "
          f"4 tight (parallel corner) {ty[4]} ({ty[4]/ctot:.1%})")

    print("\n--- by class ---")
    for c in classes:
        a = by_class[c]
        print(f"  {c:16s} rows={a['rows']:3d} c/row={a['avg_contacts_per_row']:7.1f} "
              f"c/sq={a['contacts_per_square']:6.3f} "
              f"ratio med={a['ratio_median']} "
              f"min={a['ratio_min']} max={a['ratio_max']} "
              f"free={a['free_squares']} "
              f"ngap med={a['nearest_gap_median']}")
    print("\n--- by status ---")
    for s, a in by_status.items():
        if a:
            print(f"  {s:7s} rows={a['rows']:3d} c/sq={a['contacts_per_square']:6.3f} "
                  f"ratio med={a['ratio_median']} free={a['free_squares']}")

    print("\n--- most SLACK sub-grid rows (lowest Maxwell ratio) ---")
    for r in most_slack:
        print(f"  n={r['n']:4d} {r['class']:14s} L={r['L']:.6f} "
              f"contacts={r['contacts']:4d} wall={r['wall_binding']:3d} "
              f"ratio={r['ratio']:.3f} free={r['free']} "
              f"ngap={r['nearest_gap']:.4f}" if r["nearest_gap"] is not None
              else f"  n={r['n']:4d} {r['class']:14s} L={r['L']:.6f} "
              f"contacts={r['contacts']:4d} wall={r['wall_binding']:3d} "
              f"ratio={r['ratio']:.3f} free={r['free']} ngap=None")
    print("\n--- most CONSTRAINED sub-grid rows ---")
    for r in most_constr:
        print(f"  n={r['n']:4d} {r['class']:14s} contacts={r['contacts']:4d} "
              f"wall={r['wall_binding']:3d} ratio={r['ratio']:.3f}")
    print("\n--- rows with free squares ---")
    for r in free_rows[:20]:
        print(f"  n={r['n']:4d} {r['class']:14s} status={r['status']:7s} "
              f"free={r['free']:3d} contacts={r['contacts']:4d} "
              f"wall={r['wall_binding']:3d} L={r['L']:.6f}")
    print(f"  ({len(free_rows)} rows total)")
    print("\n--- smallest nearest-gaps (next contact almost forming) ---")
    for r in near_forming:
        print(f"  n={r['n']:4d} {r['class']:14s} ngap={r['nearest_gap']:.6f} "
              f"contacts={r['contacts']} L={r['L']:.6f}")
    print("\n--- open rows that are NOT the trivial grid (contacts>0) ---")
    for r in grid_like[:10]:
        print(f"  n={r['n']:4d} {r['class']:14s} contacts={r['contacts']:4d} "
              f"wall={r['wall_binding']:3d}")

    json.dump({
        "run": 28, "part": "SAT data review (user input)",
        "tolerances": {"contact": CONTACT_TOL, "wall": WALL_TOL},
        "definitions": {
            "contact": "pair SAT margin <= 1e-7 (touching)",
            "margin": "-(min over 4 SAT axes of (ext_i+ext_j-|d.axis|))",
            "binding_walls": "the two sides achieving max(w,h); all 4 if w==h",
            "maxwell_ratio": "(contacts + binding wall touches)/(3n-3), n>=4;"
                             " one-sided contacts — a counting measure only",
            "free_square": "no pair contact and no wall touch on any side"},
        "headline": {
            "total_contacts": sum(r["contacts"] for r in rows),
            "total_wall_binding": sum(r["wall_binding"] for r in rows),
            "free_squares": sum(r["free"] for r in rows),
            "free_rows": len(free_rows),
            "axis_census": ax4,
            "type_census_1_2_3_4": ty[1:]},
        "by_class": by_class,
        "by_status": by_status,
        "most_slack": [{"n": r["n"], "src": r["src"], "L": r["L"],
                        "contacts": r["contacts"],
                        "wall": r["wall_binding"], "ratio": r["ratio"],
                        "free": r["free"],
                        "nearest_gap": r["nearest_gap"]}
                       for r in most_slack],
        "most_constrained": [{"n": r["n"], "src": r["src"],
                              "contacts": r["contacts"],
                              "wall": r["wall_binding"],
                              "ratio": r["ratio"]} for r in most_constr],
        "free_rows": [{"n": r["n"], "src": r["src"], "status": r["status"],
                       "free": r["free"], "contacts": r["contacts"],
                       "wall": r["wall_binding"], "L": r["L"]}
                      for r in free_rows],
        "near_forming": [{"n": r["n"], "src": r["src"],
                          "nearest_gap": r["nearest_gap"],
                          "contacts": r["contacts"]} for r in near_forming],
        "rows": rows,
    }, open(OUT, "w"), indent=1)
    print("\nledger ->", OUT)


if __name__ == "__main__":
    main()
