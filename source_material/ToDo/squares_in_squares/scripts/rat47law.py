#!/usr/bin/env python3
"""rat47law.py — run 104, part 2: the 28 + 28 band's law, and the rung above 1000.

Run 103 found the rung's invariant by counting: every one of the four `m + 4/7` rows
carries exactly 28 squares at the 3-4-5 word and 28 at the `t = 1/3` word, and the
rest axis-aligned.  This script asks the next two questions.

1. **Is there a contact law?**  Three independent readings, none of them float:

   * the **module**: where the 56 tilted squares sit relative to the row's own bbox
     corner, and how much that placement moves across `m = 26, 27, 28, 29`;
   * the **contact graph**: for each of the 56, which pairs are in contact (within a
     declared classification tolerance whose *safety* is measured: the gap to the
     next scale is printed next to it) and on which of the eight SAT axes — compared
     across the four rows as a labelled multiset;
   * the **lattice law**: each cell's bbox corner is classified as sitting on `Z^2`
     or on `(Z + 4/7)^2`, and the gaps between neighbouring columns are counted.
     This is where the rung's `4/7` lives: not in a seam (the strip lemma forbids
     that) but in the *shift between the two lattices*, with `4/7` and `3/7` gaps
     alternating where they interpenetrate.

2. **Does `N = m^2 + 4` extend past `N > 1000` without float drift?**  Two answers,
   kept apart on purpose:

   * **arithmetic**: the decomposition `N = (m^2 - 52) + 56` is measured in all four
     rows, the module's footprint is `m`-independent (its extent is under 26), so the
     count and the side extend to every `m >= 26`; the table for `m = 32, 40, 45`
     is computed in Fractions;
   * **computational**: the sentence is grown by `k` by copying its outer `k`-wide
     band outward — every added cell is an *exact translate* of a cell already in the
     row, so no coordinate is re-derived and no drift can accumulate.  The exact gate
     then decides whether the grown sentence is a packing at the new side, and the
     count is compared with `m'^2 + 4`.

Nothing here rounds a position: the growth is translation only.  The one tolerance is
the band-pairing key (`MATCH_TOL`), which chooses *which cell is the copy of which*
and never a coordinate.

Usage:
    python3 scripts/rat47law.py              # law + above-1000 growth, ledger
    python3 scripts/rat47law.py --selftest
"""
from __future__ import annotations

import collections
import json
import math
import os
import sys
import time
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import glm_wheels as W            # noqa: E402
import landscape65 as L           # noqa: E402
import qsqrt2 as Q                # noqa: E402
import rat47 as R                 # noqa: E402
import rat47pos as P              # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/rat47law.json")

TARGETS = (680, 733, 788, 845)
RUNG = {680: F(186, 7), 733: F(193, 7), 788: F(200, 7), 845: F(207, 7)}
BANDS = ("t=1/2", "t=1/3")
CONTACT_TOL = F(1, 10 ** 4)   # a pair is "in contact" if |slack| <= this; safety measured
MATCH_TOL = F(1, 10 ** 3)     # the band-pairing key; topology only, never a coordinate
MEAS_TOL = F(1, 10 ** 6)      # how close a delivered gap must be to 3/7 or 4/7
PITCH = F(4, 7)


# ------------------------------------------------------------------- small exact bits
def _floor(v):
    """The floor of a Fraction (exact, no float)."""
    return v.numerator // v.denominator


def _nearest_int(v):
    """The nearest integer to a Fraction, ties down (exact)."""
    n = _floor(v)
    return n if v - n <= F(1, 2) else n + 1


def _dist_to_int(v):
    """The distance from a Fraction to the nearest integer, exact."""
    return abs(v - _nearest_int(v))


def _qkey(v, tol):
    """A Fraction on a `tol` grid, as an integer key (a topology key, not a value)."""
    return _nearest_int(v / tol)


# ---------------------------------------------------------------- the 28 + 28 module
def band_cells(row):
    """The 56 tilted cells of a rung row: `(index lists by snapped word name)`."""
    names = [R.snap(t)[0] for _x, _y, t in row]
    out = {name: [] for name in BANDS}
    for i, name in enumerate(names):
        if name in out:
            out[name].append(i)
    return out, names


def module(row):
    """Where the two bands sit, relative to the row's own bbox corner (exact)."""
    cells, names = band_cells(row)
    pf = [(x, y) for x, y, _t in row]
    wf = [P.word_frac(R.snap(t)[2]) for _x, _y, t in row]
    lo, hi = P.box_q(pf, wf)
    rec = {"counts": {name: len(cells[name]) for name in BANDS},
           "corner": [str(lo[0]), str(lo[1])],
           "corner_decimal": [str(L._dec(lo[0])), str(L._dec(lo[1]))],
           "side": str(hi[0] - lo[0] if hi[0] - lo[0] > hi[1] - lo[1] else hi[1] - lo[1]),
           "bands": {}}
    for name in BANDS:
        idx = cells[name]
        xs = [pf[i][0] - lo[0] for i in idx]
        ys = [pf[i][1] - lo[1] for i in idx]
        rec["bands"][name] = {
            "x0": str(min(xs)), "y0": str(min(ys)),
            "x0_decimal": str(L._dec(min(xs))), "y0_decimal": str(L._dec(min(ys))),
            "w": str(max(xs) - min(xs)), "h": str(max(ys) - min(ys)),
            "w_decimal": str(L._dec(max(xs) - min(xs))),
            "h_decimal": str(L._dec(max(ys) - min(ys))),
            "touches_corner": None}
    # a band "touches its own corner" if its bbox starts within one cell of both walls
    for name in BANDS:
        b = rec["bands"][name]
        b["touches_corner"] = [F(b["x0"]) < F(3, 2), F(b["y0"]) < F(3, 2)]
    return rec, cells, names, pf, wf


def band_contacts(pf, wf, idx, tol=CONTACT_TOL):
    """Every contact inside a band, with its SAT axis role, exactly classified.

    A pair is a contact iff its best axis slack is within `tol` of 0.  The *axis
    role* is `(owner side, frame axis, sign)`: side 0 means the first cell of the
    pair owns the projecting axis, 1 the second; frame axis 0 is `u = (c, s)`, 1 is
    `v = (-s, c)`; the sign is that of the projection at contact.
    """
    out = []
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            i, j = idx[a], idx[b]
            if (abs(pf[j][0] - pf[i][0]) >= F(2)
                    or abs(pf[j][1] - pf[i][1]) >= F(2)):
                continue
            axes = P.pair_axes_q(pf, wf, i, j)
            k = max(range(len(axes)), key=lambda r: abs(axes[r][0]) - axes[r][1])
            proj, need = axes[k]
            slack = abs(proj) - need
            if abs(slack) <= tol:
                out.append({"cells": [i, j], "axis": [k // 2, k % 2],
                            "sign": 1 if proj >= 0 else -1, "slack": str(slack)})
    return out


def signature(pf, wf, idx, names_dummy=None):
    """The band's contact graph as a row-independent labelled multiset."""
    kinds = names_dummy if names_dummy is not None else ["?"] * len(pf)
    sig = []
    for c in band_contacts(pf, wf, idx):
        i, j = c["cells"]
        a, b = (i, j) if i < j else (j, i)
        # canonical: the pair is ordered by index, and the axis role's owner side is
        # re-expressed against that order
        owner = i if c["axis"][0] == 0 else j
        side = 0 if owner == a else 1
        sig.append((kinds[a], kinds[b], side, c["axis"][1], c["sign"]))
    return sorted(sig)


def interface_contacts(pf, wf, idx, names, tol=CONTACT_TOL):
    """The band's contacts with everything *outside* it, as a labelled multiset.

    Each entry is `(band word, outside word, owner side, frame axis, sign)`; owner
    side 0 means the band cell owns the projecting axis.  This is the half of the
    module's graph the intra-band signature cannot see: the interface with the axis
    mosaic, which is where the `4/7` / `3/7` lattice gaps live.
    """
    inside = set(idx)
    kinds = collections.Counter()
    for i in idx:
        for j in range(len(pf)):
            if j in inside:
                continue
            if (abs(pf[j][0] - pf[i][0]) >= F(2)
                    or abs(pf[j][1] - pf[i][1]) >= F(2)):
                continue
            axes = P.pair_axes_q(pf, wf, i, j)
            k = max(range(len(axes)), key=lambda r: abs(axes[r][0]) - axes[r][1])
            proj, need = axes[k]
            if abs(abs(proj) - need) <= tol:
                kinds[(names[i], names[j], k // 2, k % 2,
                       1 if proj >= 0 else -1)] += 1
    return kinds


def contact_margin(pf, wf, idx, tol=CONTACT_TOL):
    """The smallest non-contact slack among the band's close pairs: the safety gap."""
    best = None
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            i, j = idx[a], idx[b]
            if (abs(pf[j][0] - pf[i][0]) >= F(2)
                    or abs(pf[j][1] - pf[i][1]) >= F(2)):
                continue
            s = P.pair_slack_q(pf, wf, i, j)
            if s is None or abs(s) <= tol:
                continue
            if best is None or abs(s) < best:
                best = abs(s)
    return best


# ------------------------------------------------------------------- the lattice law
def lattice_split(pf, wf, names):
    """Classify every cell's bbox corner by which lattice it sits nearest to.

    `Z^2` is the unit lattice; `(Z + 4/7)^2` is the shifted one.  The residual is
    kept: the delivered pose is polished, so a cell can sit 1e-3 off its lattice
    (the run-102 carriers do exactly that, and they are the cells that make the
    count not a *rigid* law).
    """
    counts = collections.Counter()
    resid = collections.defaultdict(F)
    off = collections.Counter()
    for i in range(len(pf)):
        x = P.low_edge(pf, wf, i, 0)
        y = P.low_edge(pf, wf, i, 1)
        e0 = max(_dist_to_int(x), _dist_to_int(y))
        e4 = max(_dist_to_int(x - PITCH), _dist_to_int(y - PITCH))
        if e0 <= e4:
            label, err = "Z", e0
        else:
            label, err = "Z+4/7", e4
        counts[label] += 1
        if err > resid[label]:
            resid[label] = err
        if err > MEAS_TOL:
            off[names[i]] += 1
    return {"counts": dict(counts),
            "residual_max": {k: str(v) for k, v in resid.items()},
            "off_lattice_by_word": dict(off)}


def gaps(pf, wf, axis=0):
    """The gaps between neighbouring axis columns (or rows), with 3/7 and 4/7 counts."""
    edges = sorted({P.low_edge(pf, wf, i, axis) for i in range(len(pf))
                    if wf[i][0] in (1, 0) and wf[i][1] in (0, 1)})
    hist = collections.Counter()
    near = collections.Counter()
    for a, b in zip(edges, edges[1:]):
        g = b - a
        hist[g] += 1
        for label, want in (("3/7", F(3, 7)), ("4/7", PITCH)):
            if abs(g - want) <= MEAS_TOL:
                near[label] += 1
    close = sorted([(g, n) for g, n in hist.items() if g < F(1)],
                   key=lambda t: t[0])
    return {"columns": len(edges), "near": dict(near),
            "sub_unit_gaps": [[str(g), n] for g, n in close],
            "closest_3_7": str(min(abs(g - F(3, 7)) for g, _n in hist.items())),
            "closest_4_7": str(min(abs(g - PITCH) for g, _n in hist.items()))}


# --------------------------------------------------------------- growth above 1000
def band_pattern(pf, wf, axis, start, k, tol=MATCH_TOL):
    """The occupancy of a band as integer keys: `(key along axis, key across, word)`."""
    out = []
    for i in range(len(pf)):
        e = P.low_edge(pf, wf, i, axis)
        if start <= e < start + k:
            out.append((_qkey(e - start, tol), _qkey(pf[i][1 - axis], tol), wf[i]))
    return sorted(out)


def grow(pf, wf, k):
    """Grow the sentence by `k` along x, then along y, by copying the outer band.

    The copy is translation by exactly `k`: no coordinate is recomputed, so nothing
    can drift.  A cell of the outer `k`-wide band is left in place and a copy is
    added `k` further out; the band's own periodicity is reported separately.
    """
    added = 0
    for axis in (0, 1):
        lo, hi = P.box_q(pf, wf)
        add_pf, add_wf = [], []
        for i in range(len(pf)):
            if P.low_edge(pf, wf, i, axis) >= hi[axis] - k:
                p = list(pf[i])
                p[axis] += k
                add_pf.append(tuple(p))
                add_wf.append(wf[i])
        pf = list(pf) + add_pf
        wf = list(wf) + add_wf
        added += len(add_pf)
    return pf, wf, added


def growth_check(row, m, k=3):
    """The growth experiment on the largest rung row, gated exactly."""
    pf = [(x, y) for x, y, _t in row]
    wf = [P.word_frac(R.snap(t)[2]) for _x, _y, t in row]
    lo, hi = P.box_q(pf, wf)
    before = {"N": len(pf), "side": str(hi[0] - lo[0] if hi[0] - lo[0] > hi[1] - lo[1]
                                        else hi[1] - lo[1])}
    periodic = {}
    for axis, name in ((0, "x"), (1, "y")):
        lo_a, hi_a = lo[axis], hi[axis]
        a = band_pattern(pf, wf, axis, hi_a - 2 * k, k)
        b = band_pattern(pf, wf, axis, hi_a - k, k)
        periodic[name] = {"band_cells": len(b), "previous_band_cells": len(a),
                          "same_pattern": a == b}
    pf2, wf2, added = grow(pf, wf, k)
    lo2, hi2 = P.box_q(pf2, wf2)
    side = hi2[0] - lo2[0] if hi2[0] - lo2[0] > hi2[1] - lo2[1] else hi2[1] - lo2[1]
    g = P.gate_q(pf2, wf2)
    m_new = m + k
    source_excess = F(before["side"]) - (F(m) + PITCH)
    return {"k": k, "before": before, "added": added, "N": len(pf2),
            "side": str(side), "side_decimal": str(L._dec(side)),
            "rung_next": str(F(m_new) + PITCH),
            "drift": str(side - (F(m_new) + PITCH)),
            "drift_decimal": str(L._dec(side - (F(m_new) + PITCH))),
            "source_excess": str(source_excess),
            "drift_unchanged": (side - (F(m_new) + PITCH)) == source_excess,
            "count_law": {"expected": m_new * m_new + 4, "actual": len(pf2),
                          "deficit": m_new * m_new + 4 - len(pf2)},
            "gate": {"ok": bool(g["ok"]), "violations": g["violations"],
                     "contacts": g["contacts"],
                     "clearance": None if g["clearance"] is None else str(g["clearance"]),
                     "L": str(g["L"])},
            "periodic": periodic}


# -------------------------------------------------------------------------- one row
def target(n, row):
    start = time.time()
    mod, cells, names, pf, wf = module(row)
    m = math.isqrt(len(pf) - 4)
    rec = {"n": n, "N": len(pf), "m": m, "rung": str(RUNG[n]),
           "axis_cells": len(pf) - len(cells[BANDS[0]]) - len(cells[BANDS[1]]),
           "axis_law": m * m - 52, "module": mod,
           "signature": None, "signature_len": 0, "margin": None,
           "contacts": {}, "lattice": None, "gaps": None,
           "seconds": None}
    rec["contacts"] = {name: len(band_contacts(pf, wf, cells[name])) for name in BANDS}
    rec["signature"] = signature(pf, wf, cells[BANDS[0]] + cells[BANDS[1]], names)
    rec["signature_len"] = len(rec["signature"])
    margin = contact_margin(pf, wf, cells[BANDS[0]] + cells[BANDS[1]])
    rec["margin"] = None if margin is None else str(margin)
    iface = interface_contacts(pf, wf, cells[BANDS[0]] + cells[BANDS[1]], names)
    rec["interface"] = {"total": sum(iface.values()),
                        "types": [[list(k), v] for k, v in sorted(iface.items())]}
    rec["lattice"] = lattice_split(pf, wf, names)
    rec["gaps"] = gaps(pf, wf, 0)
    rec["gaps_y"] = gaps(pf, wf, 1)
    rec["seconds"] = round(time.time() - start, 1)
    return rec


# ------------------------------------------------------------------------- the run
def run():
    rows = W._delivered_rows()
    recs = []
    for n in TARGETS:
        print(f"  n = {n}: module, contact graph, lattice …", flush=True)
        recs.append(target(n, rows[n]))
    # cross-row comparison: the module and the contact graph, as multisets.  The
    # *type set* is the law candidate; the multiplicities are reported because a
    # pair sitting on the classification tolerance flips one count between rows.
    sigs = [sorted(tuple(t) for t in r["signature"]) for r in recs]
    same_sig = all(s == sigs[0] for s in sigs)
    types = sorted({t for s in sigs for t in s})
    type_set_same = all({t for t in s} == {t for t in sigs[0]} for s in sigs)
    per_type = [[list(t), [sum(1 for u in s if u == t) for s in sigs]] for t in types]
    # the interface with the axis mosaic, compared the same way
    iface = [{tuple(t): v for t, v in r["interface"]["types"]} for r in recs]
    itypes = sorted({t for d in iface for t in d})
    iface_same_types = all({t for t in d} == {t for t in iface[0]} for d in iface)
    iface_per_type = [[list(t), [d.get(t, 0) for d in iface]] for t in itypes]
    spread = {}
    for name in BANDS:
        for key in ("x0", "y0", "w", "h"):
            vals = [F(r["module"]["bands"][name][key]) for r in recs]
            spread[f"{name}.{key}"] = {"min": str(min(vals)), "max": str(max(vals)),
                                       "spread": str(max(vals) - min(vals))}
    above = growth_check(rows[845], 29, k=3)
    table = [{"m": m, "N": m * m + 4, "axis": m * m - 52, "band": 56,
              "side": str(F(m) + PITCH)} for m in (32, 40, 45)]
    res = {"run": 104, "part": 2, "targets": list(TARGETS), "bands": list(BANDS),
           "contact_tol": str(CONTACT_TOL), "match_tol": str(MATCH_TOL),
           "runs": recs,
           "module_spread": spread,
           "signature_identical": same_sig,
           "signature_type_set_identical": type_set_same,
           "contact_types": per_type,
           "interface_type_set_identical": iface_same_types,
           "interface_types": iface_per_type,
           "signature": [list(t) for t in sigs[0]],
           "above_1000": {"arithmetic": table, "growth": above},
           "identity": ("rat47law: the 28 + 28 band is a corner module whose contact "
                        "graph is compared across m as a labelled multiset; the rung's "
                        "4/7 is the shift between the unit lattice and (Z+4/7)^2, with "
                        "4/7 and 3/7 gaps at the interface; the growth above 1000 is "
                        "translation only, so no coordinate is ever re-derived")}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1)
    return res


# ------------------------------------------------------------------------ selftest
def selftest():
    """Five controls: the lattice label, the growth, a contact, periodicity, the module."""
    print("rat47law selftest")
    # 1. the lattice label, exactly, on bbox corners (not centres)
    assert lattice_label(F(0), F(0)) == ("Z", 0)
    assert lattice_label(PITCH, PITCH) == ("Z+4/7", 0)
    assert lattice_label(F(3) + PITCH, F(5) + PITCH)[0] == "Z+4/7"
    print("  control 1 — a corner is labelled Z at distance 0 and Z+4/7 at 4/7, exactly")
    # 2. the growth on a 2x2 grid reproduces the 3x3 grid, tightly
    pf = [(F(1, 2), F(1, 2)), (F(3, 2), F(1, 2)), (F(1, 2), F(3, 2)), (F(3, 2), F(3, 2))]
    wf = [P.word_frac(Q.AXIS)] * 4
    pf2, wf2, added = grow(pf, wf, 1)
    assert added == 2 + 3, added
    assert len(pf2) == 9, len(pf2)
    g = P.gate_q(pf2, wf2)
    assert g["ok"] and g["L"] == Q.Q2(3) and g["clearance"] == 0, g
    print(f"  control 2 — growing a 2x2 grid by 1 adds {added} exact translates, gives "
          f"the 3x3 grid (9 cells), L = 3 and clearance exactly 0")
    # 3. one contact, with its axis role
    pf3 = [(F(1, 2), F(1, 2)), (F(3, 2), F(1, 2))]
    wf3 = [P.word_frac(Q.AXIS)] * 2
    cs = band_contacts(pf3, wf3, [0, 1])
    assert len(cs) == 1 and cs[0]["sign"] == 1 and cs[0]["axis"] in ([0, 0], [0, 1]), cs
    assert signature(pf3, wf3, [0, 1], ["z", "z"]) == [("z", "z", 0, 0, 1)] or \
        signature(pf3, wf3, [0, 1], ["z", "z"]) == [("z", "z", 0, 1, 1)]
    print("  control 3 — two axis squares in contact give one contact and a one-entry "
          "signature, with the projecting axis named")
    # 4. the band key is a topology key: 1e-4 of jitter does not change it, 1e-2 does
    a = band_pattern(pf3, wf3, 0, F(0), F(2))
    pf4 = [(F(1, 2) + F(1, 10 ** 4), F(1, 2)), (F(3, 2), F(1, 2))]
    b = band_pattern(pf4, wf3, 0, F(0), F(2))
    assert a == b, (a, b)
    pf5 = [(F(1, 2) + F(1, 10 ** 2), F(1, 2)), (F(3, 2), F(1, 2))]
    assert band_pattern(pf5, wf3, 0, F(0), F(2)) != a
    print("  control 4 — the band key is unmoved by 1e-4 of jitter and moved by 1e-2")
    # 5. the module census on a delivered row: 28 + 28, and axis = m^2 - 52
    rows = W._delivered_rows()
    rec = target(788, rows[788])
    assert rec["module"]["counts"] == {"t=1/2": 28, "t=1/3": 28}, rec["module"]["counts"]
    assert rec["axis_cells"] == 28 * 28 - 52, rec["axis_cells"]
    assert rec["signature_len"] > 0
    print(f"  control 5 — 788's module is 28 + 28 tilted cells over {rec['axis_cells']} "
          f"axis cells (= 28^2 - 52) with {rec['signature_len']} band contacts")
    print("rat47law: OK (5 controls)")
    return 0


def lattice_label(x, y):
    """`(label, residual)` for a corner: the nearer of Z^2 and (Z + 4/7)^2."""
    e0 = max(_dist_to_int(x), _dist_to_int(y))
    e4 = max(_dist_to_int(x - PITCH), _dist_to_int(y - PITCH))
    return ("Z" if e0 <= e4 else "Z+4/7"), (e0 if e0 <= e4 else e4)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()
    res = run()
    print("the 28 + 28 module:")
    for r in res["runs"]:
        mod = r["module"]
        b1, b2 = mod["bands"]["t=1/2"], mod["bands"]["t=1/3"]
        print(f"  n = {r['n']:4d} m = {r['m']:2d}  axis {r['axis_cells']:3d} "
              f"(= m^2 - 52: {r['axis_cells'] == r['axis_law']})  "
              f"28 + 28  contacts {r['contacts']}")
        print(f"      t=1/2 at ({b1['x0_decimal'][:9]}, {b1['y0_decimal'][:9]}) "
              f"size {b1['w_decimal'][:9]} x {b1['h_decimal'][:9]}")
        print(f"      t=1/3 at ({b2['x0_decimal'][:9]}, {b2['y0_decimal'][:9]}) "
              f"size {b2['w_decimal'][:9]} x {b2['h_decimal'][:9]}")
        print(f"      lattice {r['lattice']['counts']}  gaps "
              f"{r['gaps']['near']}  margin {r['margin']}")
    print(f"module spread across m (worst per key):")
    for key, v in res["module_spread"].items():
        print(f"   {key:12s} spread {v['spread'][:14]}")
    print(f"contact types identical across the four rows: "
          f"{res['signature_type_set_identical']}; full multiplicity identical: "
          f"{res['signature_identical']} ({len(res['signature'])} contacts in row 680)")
    for t, counts in res["contact_types"]:
        if len(set(counts)) > 1:
            print(f"   type {t} counts {counts} (the one that flips)")
    print(f"band-to-axis interface types identical: "
          f"{res['interface_type_set_identical']}")
    for r in res["runs"]:
        print(f"   n = {r['n']}: interface {r['interface']['total']} contacts in "
              f"{len(r['interface']['types'])} types")
    ab = res["above_1000"]
    print("above 1000, arithmetic (N = m^2 + 4, side = m + 4/7):")
    for row in ab["arithmetic"]:
        print(f"   m = {row['m']:2d}  N = {row['N']:4d}  axis {row['axis']:4d} + "
              f"band {row['band']}  side = {row['side']}")
    g = ab["growth"]
    rung_next = F(29 + g["k"]) + PITCH
    print(f"above 1000, growth (translation only): N {g['before']['N']} -> {g['N']} "
          f"(added {g['added']}), side {g['side_decimal'][:18]} vs rung "
          f"{L._dec(rung_next)} (excess {g['drift_decimal'][:10]})")
    print(f"   count law: expected {g['count_law']['expected']}, actual "
          f"{g['count_law']['actual']}, deficit {g['count_law']['deficit']}")
    print(f"   drift unchanged from the source row: {g['drift_unchanged']} "
          f"({g['source_excess']})")
    for r in res["runs"]:
        print(f"   n = {r['n']}: 3/7 gaps {r['gaps']['near'].get('3/7', 0)} "
              f"(closest {r['gaps']['closest_3_7'][:12]}), 4/7 gaps "
              f"{r['gaps']['near'].get('4/7', 0)} "
              f"(closest {r['gaps']['closest_4_7'][:12]})")
    print(f"   gate: ok={g['gate']['ok']} violations={g['gate']['violations']} "
          f"clearance={str(g['gate']['clearance'])[:12]} "
          f"periodic={ {k: v['same_pattern'] for k, v in g['periodic'].items()} }")
    print(f"ledger: {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
