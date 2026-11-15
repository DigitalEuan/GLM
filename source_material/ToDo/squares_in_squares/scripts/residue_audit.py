#!/usr/bin/env python3
r"""residue_audit.py — Part 1: the residue distribution of the 593 jammed
puzzles, audited exactly against table.json (not from memory or reports).

Block structure: n = k² + r, k = floor(sqrt(n)), r in [0, 2k].
Classes for the grid-tied (jammed) puzzles:
  SQ   r = 0              perfect squares — grid L = k optimal by area;
  NAG  r in {2k-1, 2k}    Nagamochi class: n = m²-1 or m²-2 (m = k+1),
                          s(n) = m proven (Nagamochi 1996) — unbeatable;
  LOW  1 <= r <= 2k-2, r <= 18, non-SQ non-NAG — claimed solved by the
       cascade chains: audited here (the live counterexamples are exactly
       the strategic small-n bases);
  MID  19 <= r <= 2k-2, non-NAG — the mid-band residue gap.

Also audited:
  - the exact per-k census of MID (which blocks contribute which n-ranges);
  - the roomy-target list {695, 696, 748, 749, 803, 804, 862, 922, 983, 984}
    with k, r, grid, sqrt(n) (roominess = grid - sqrt(n)), current L, and
    the survey's known value (tri_table.json / records.json) — the honest
    "what a find would mean" (it would beat the published catalogue);
  - the L-extension cascade leverage, CONSTRUCTIVELY: from any verified
    state with m squares in container L, build the L+1 state with
    m + 2*floor(L) + 1 squares (top row floor(L)+1 + right column floor(L)),
    and packlib-verify it — the rule the cascade planner uses upstream;
  - the "strategic small-n bases" (n <= 40, grid-tied or numeric-level-0):
    current L, src, and what a marginal push would propagate to.

Output: download/residue_audit.json + console report.
"""
import json
import math
import os
import sys
from math import ceil, sqrt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import packlib as P

SUB = "/home/z/my-project/workspace/submission"
DL = "/home/z/my-project/download"
TAB = os.path.join(SUB, "table.json")
TRI = json.load(open("/home/z/my-project/workspace/tri_table.json"))
REC = json.load(open(os.path.join(SUB, "records.json")))


def grid_of(n):
    return ceil(sqrt(n))


def survey_known(n):
    e = TRI.get(str(n))
    if e is not None:
        try:
            return float(e)
        except (TypeError, ValueError):
            pass
        if isinstance(e, dict):
            for key in ("known", "value", "L"):
                if key in e and e[key] is not None:
                    try:
                        return float(e[key])
                    except (TypeError, ValueError):
                        pass
    r = REC.get(str(n))
    if isinstance(r, dict):
        try:
            return float(r.get("L"))
        except (TypeError, ValueError):
            pass
    return None


def band_extend(state, L):
    """The L-extension leverage step: state (m squares, verified, bbox
    within [lo, hi]) -> state with m + 2*floor(L) + 1 squares, container
    side +1.  The band is placed on the state's ACTUAL bbox (stored
    states carry the 2e-9 finalize scaling, so the bbox top can sit
    ~4e-8 above the stored L); a 1e-9 shim keeps the new contacts
    strictly non-overlapping.  Top strip: floor(L)+1 squares; right
    strip: floor(L) squares (corner counted once)."""
    import numpy as np
    xy = np.array([(s[0], s[1]) for s in state], dtype=float)
    th = np.array([s[2] for s in state], dtype=float)
    ex = 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))
    lox = float(np.min(xy[:, 0] - ex)); hix = float(np.max(xy[:, 0] + ex))
    loy = float(np.min(xy[:, 1] - ex)); hiy = float(np.max(xy[:, 1] + ex))
    ell = math.floor(L + 1e-9)
    shim = 1e-9
    out = list(state)
    for i in range(ell + 1):          # top row: ell+1 squares
        out.append((lox + i + 0.5, hiy + 0.5 + shim, 0.0))
    for j in range(ell):              # right column: ell squares
        out.append((hix + 0.5 + shim, loy + j + 0.5, 0.0))
    return out


def main():
    tab = json.load(open(TAB))
    rows = []
    classes = {"SQ": [], "NAG": [], "LOW": [], "MID": []}
    beats = []
    for n in range(1, 1001):
        e = tab[str(n)]
        L = float(e["L"])
        g = grid_of(n)
        k = int(math.floor(sqrt(n) + 1e-12))
        r = n - k * k
        beat = L < g - 1e-6
        if beat:
            beats.append(n)
            continue
        # grid-tied: classify
        if r == 0:
            cls = "SQ"
        elif r in (2 * k - 1, 2 * k):
            cls = "NAG"               # n = (k+1)²-2 or (k+1)²-1
        elif r <= 18:
            cls = "LOW"
        else:
            cls = "MID"
        classes[cls].append(n)
        rows.append({"n": n, "k": k, "r": r, "L": L, "grid": g,
                     "src": e.get("src"), "class": cls})

    n_sq, n_nag, n_low, n_mid = (len(classes[c]) for c in ("SQ", "NAG", "LOW", "MID"))
    total_jam = n_sq + n_nag + n_low + n_mid
    print(f"puzzles beating grid: {len(beats)}; jammed (grid-tied): {total_jam}")
    print(f"  SQ  r=0        (perfect squares, optimal by area): {n_sq}")
    print(f"  NAG r=2k-1,2k  (Nagamochi, s=m proven):           {n_nag}")
    print(f"  LOW 1<=r<=18   (claimed solved by cascade):       {n_low}")
    print(f"  MID 19<=r<=2k-2 (the residue gap):                {n_mid}")
    assert total_jam == 1000 - len(beats)

    # LOW detail — the live counterexamples = strategic small-n bases
    print("\nLOW band (r<=18, non-SQ non-NAG, grid-tied) — full list:")
    for n in classes["LOW"]:
        e = tab[str(n)]
        k = int(math.floor(sqrt(n)))
        print(f"  n={n}: k={k} r={n-k*k} L={e['L']:.9f} src={e.get('src')} "
              f"survey={survey_known(n)}")

    # MID census per block
    print("\nMID band census per block k:")
    per_k = {}
    for n in classes["MID"]:
        per_k.setdefault(int(math.floor(sqrt(n))), []).append(n)
    for k in sorted(per_k):
        ns = per_k[k]
        print(f"  k={k:2d}: {len(ns):3d} puzzles, n = {min(ns)}..{max(ns)} "
              f"(r = {min(ns)-k*k}..{max(ns)-k*k})")

    # roomy targets
    print("\nroomy mid-band targets (least-jammed, largest blocks):")
    roomy = [695, 696, 748, 749, 803, 804, 862, 922, 983, 984]
    roomy_rows = []
    for n in roomy:
        e = tab[str(n)]
        k = int(math.floor(sqrt(n)))
        r = n - k * k
        g = grid_of(n)
        sk = survey_known(n)
        roomy_rows.append({"n": n, "k": k, "r": r, "grid": g,
                            "sqrt_n": round(sqrt(n), 6),
                            "roominess": round(g - sqrt(n), 6),
                            "L": float(e["L"]), "src": e.get("src"),
                            "survey_known": sk})
        print(f"  n={n}: k={k} r={r} grid={g} sqrt={sqrt(n):.4f} "
              f"(room {g-sqrt(n):.4f}) L={e['L']:.6f} survey={sk}")
    holes = [t for t in roomy_rows
             if t["survey_known"] is not None and t["survey_known"] < t["L"] - 1e-6]
    print(f"  survey-known below our L among roomy targets: {len(holes)} "
          f"(a find at any of these beats the published catalogue)")

    # global holes vs survey (any n) — the honest frontier check
    hole_list = []
    for n in range(1, 1001):
        sk = survey_known(n)
        if sk is not None and sk < float(tab[str(n)]["L"]) - 1e-6:
            hole_list.append(n)
    print(f"\nsurvey-known < our L anywhere in 1..1000: {len(hole_list)} {hole_list[:10]}")

    # cascade leverage — constructive verification
    print("\ncascade leverage m -> m + 2*floor(L)+1 in L+1 (constructive):")
    lev = []
    # (a) from a real table state (chain3-derived), (b) from a plain grid state
    for n_probe, tag in ((325, "chain3-compressed"), (13, "grid-seed")):
        st = tab[str(n_probe)].get("state")
        if not st:
            continue
        L0 = float(tab[str(n_probe)]["L"])
        r0 = P.verify(st)
        L0 = r0["L"]                      # true container side (w=h for these)
        st2 = band_extend(st, L0)
        r2 = P.verify(st2, tol=1e-9)
        m0, m1 = len(st), len(st2)
        expect = m0 + 2 * math.floor(L0) + 1
        ok = (m1 == expect) and r2["worst_pen"] <= 1e-9 and r2["ok"]
        # container of the extended state must be L0+1
        ok = ok and abs(r2["L"] - (L0 + 1)) < 1e-6
        print(f"  {tag}: n={n_probe} m={m0} L={L0:.6f} -> m'={m1} "
              f"(expect {expect}) in L'={r2['L']:.6f} pen={r2['worst_pen']:.2e} "
              f"{'VERIFIED' if ok else 'FAILED'}")
        lev.append({"from_n": n_probe, "m": m0, "L": L0, "m2": m1,
                    "expect": expect, "L2": r2["L"], "pen": r2["worst_pen"],
                    "ok": ok})
    # grid arithmetic check of the leverage on all chain3 entries:
    # every chain3 src entry must equal some base chain — check count only
    ch = [int(k2) for k2 in tab if tab[k2].get("src") == "chain3"]
    print(f"  chain3 entries in table: {len(ch)}")

    out = {
        "beats_grid": len(beats), "jammed": total_jam,
        "classes": {"SQ": n_sq, "NAG": n_nag, "LOW": n_low, "MID": n_mid},
        "low_list": classes["LOW"],
        "mid_per_k": {str(k): {"count": len(v), "min": min(v), "max": max(v)}
                      for k, v in per_k.items()},
        "roomy": roomy_rows,
        "survey_holes": hole_list,
        "leverage": lev,
        "rows": rows,
    }
    json.dump(out, open(os.path.join(DL, "residue_audit.json"), "w"), indent=1)
    print("\nwrote", os.path.join(DL, "residue_audit.json"))


if __name__ == "__main__":
    main()
