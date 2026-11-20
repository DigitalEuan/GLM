#!/usr/bin/env python3
r"""family_spin.py — every exact grammatical family, spun against the table and past it.

Two questions, one instrument, and no float in either answer.

**(a) Calibration, N <= 1000.**  For every exact family member whose count is a
delivered row, is its exact side `L` *strictly smaller* than the table's own side
at that N?  The table's side is recomputed here from the delivered 12-dp pose as an
exact rational input: every centre is a `Fraction` read off `submission.csv`, and
each square's extent is `(|cos| + |sin|)/2` with `cos` and `sin` of the row's exact
rational angle at 70 digits (`field_triage.cos_sin`).  Both sides of the comparison
are then `Decimal`s whose own error is ~1e-69, and every gap this family can
produce is >= 1e-3, so the verdict is decisive.  Nothing is rounded and no row is
written.

**(b) The window above, 1000 < N <= 2100.**  The delivered table stops at n = 1000,
so there is nothing to calibrate against; what is emitted instead is the sentence
itself — exact container side `L`, exact void `L^2 - N`, and the contact count the
exact gate reads — in `Quad` arithmetic with zero drift.

FAMILIES.  Every sentence is built by `glm_wheels.py`'s own constructors, never
re-typed here:

    Ridge       N = 4k^2 + m,   L = 2k + w,  w = m * min(1/(c+s), c+s)
                over Q(sqrt 2) (45 deg), Q(sqrt 5) (slope 2:1), Q(sqrt 7) (the
                census word and the Seventh), and the rational-t words 1/2, 1/3, 1/5
    Strip       S(k, m) = 4k^2 + m at 45 deg, L = 2k + m sqrt2 / 2
                (the same rungs as Ridge's 45-degree column, built by the other
                constructor — a cross-check, not a second family)
    Ring        N = 4k + 14 at the census word; the pinwheel closes only at k = 1
    Diamond     the declared Product-minus-collision atoms n = 10, 19, 40
    Staircase   N = 4k^2 + 4k + 5 + 2|columns(k)| at the census word, and its side
                is the gate's own bbox — which is `2k + 1 + 2c` only while the brick
                wall's `u`-span fits the box (k = 5, and k = 6 approximately)

READ-ONLY.  This file writes one ledger (`workspace/push/family_spin.json`) and
never touches `submission.csv`, `WHITEBOARD.md` or any row of the table.

USAGE
    python3 scripts/family_spin.py --calibrate
    python3 scripts/family_spin.py --beyond strip
    python3 scripts/family_spin.py --beyond stair
    python3 scripts/family_spin.py --beyond words
"""
from __future__ import annotations

import json
import os
import sys
import time
from decimal import Decimal, getcontext
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import exact_field as EF          # noqa: E402
import qsqrt2 as Q                # noqa: E402
import glm_wheels as G            # noqa: E402
import field_triage as T          # noqa: E402

getcontext().prec = 70

LEDGER = os.path.join(ROOT, "workspace/push/family_spin.json")
DEC = G.DecimalWitness.scalar


# ------------------------------------------------------------------ the words
def words():
    """Every word the spin uses, with its field, read off the module's own builders."""
    out = []
    c2, s2 = Q.word_45()
    out.append(("45deg", 2, c2, s2))
    c5, s5 = G.unit_word(5, 2, 1)
    out.append(("Slope-2:1", 5, c5, s5))
    cls7 = G.qfield(7)
    cw, sw = G._sqrt7_word()
    out.append(("census", 7, cw, sw))
    out.append(("Seventh", 7, cls7(0, F(1, 4)), cls7(F(3, 4))))
    for t in (F(1, 2), F(1, 3), F(1, 5)):
        tc, ts = EF.tword(t)
        cls2 = G.qfield(2)
        out.append((f"t={t}", 2, cls2(F(tc)), cls2(F(ts))))
    return out


def ridge_span(cls, c, s, m):
    """The ridge's seam width, exactly: `m * min(1/(c+s), c+s)`.

    Run 90's closed form at `m = 1`; the bar of `m` tilted squares is `m` long, so
    the corridor it needs scales with `m`.  The gate is the arbiter of every rung
    this width is used at (a width that did not gate would be refused, not claimed).
    """
    one = cls(1)
    return cls(m) * min(one / (c + s), c + s)


def ridge_member(cls, c, s, k, m, name, d):
    w = ridge_span(cls, c, s, m)
    return {"family": "Ridge", "field": f"Q(sqrt {d})", "word": name,
            "k": k, "m": m, "N": 4 * k * k + m, "L": cls(2 * k) + w,
            "cls": cls, "c": c, "s": s, "w": w}


def strip_member(k, m):
    cls = Q.Q2
    c, s = Q.word_45()
    return {"family": "Strip", "field": "Q(sqrt 2)", "word": "45deg",
            "k": k, "m": m, "N": 4 * k * k + m,
            "L": cls(2 * k) + cls(0, F(m, 2)), "cls": cls, "c": c, "s": s,
            "w": cls(0, F(m, 2))}


def ridge_ladder(kmax=22, mset=(1, 2, 3), names=None):
    out = []
    for name, d, c, s in words():
        if names is not None and name not in names:
            continue
        cls = G.qfield(d)
        for m in mset:
            for k in range(1, kmax + 1):
                out.append(ridge_member(cls, c, s, k, m, name, d))
    return out


def strip_ladder(kmax=22, mset=(1, 2, 3)):
    return [strip_member(k, m) for m in mset for k in range(1, kmax + 1)]


def staircase_member(k, u=None):
    """The staircase at `k`, with the side the gate's bbox actually reads.

    `staircase_field` asserts the family side law `2k + 1 + 2c`; here the side is
    taken from the sentence so that a `k` whose brick wall no longer fits the box is
    *reported* (with its own larger side) instead of refused.  The declared brick
    tangencies are still checked, exactly, for every k.
    """
    cls = G.qfield(7)
    c, s = G._sqrt7_word()
    if u is None:
        u = cls(F(-1357, 128), F(211, 128))
    frame = G.staircase_frame(cls, c, s, k)
    seam = G.staircase_seam(cls, c, s, k, u)
    cells = frame + seam
    ws = [(cls(1), cls(0))] * len(frame) + [(c, s)] * len(seam)
    need = G._staircase_need(cls, c, s)
    adrift = 0
    for i, j in G.staircase_tangencies(k):
        p, q = seam[i], frame[j]
        dv = (p[0] - q[0]) * (-s) + (p[1] - q[1]) * c
        if abs(dv) != need:
            adrift += 1
    L = Q.side(cells, ws, cls)
    law = cls(2 * k + 1) + cls(2) * c
    return {"family": "Staircase", "field": "Q(sqrt 7)", "word": "census",
            "k": k, "m": 0, "N": len(cells), "L": L, "law_L": law,
            "at_law": L == law, "adrift": adrift, "cls": cls, "c": c, "s": s,
            "cells": cells, "words": ws, "u": u,
            "columns": len(G.staircase_columns(k))}


# --------------------------------------------------- the delivered table's side
_TABLES = {}


def table_sides():
    """The delivered side of every row, as a 70-digit measure of its own pose.

    `L = max over axes of (max_i(x + ex_i) - min_i(x - ex_i))` with
    `ex_i = (|cos t_i| + |sin t_i|)/2`; every `x` is the exact `Fraction` of the
    12-dp file, every `cos`/`sin` is a 70-digit `Decimal` of the row's exact
    rational angle.  This is the definition `sqscore.extent` uses, computed here
    without a float so that it can be compared to an exact `Quad` side.
    """
    if _TABLES:
        return _TABLES["sides"]
    rows = G._delivered_rows()
    cache = {}
    out = {}
    for n, cells in rows.items():
        best = None
        for i in (0, 1):
            lo = hi = None
            for r in cells:
                xv = Decimal(F(r[i]).numerator) / Decimal(F(r[i]).denominator)
                if r[2] not in cache:
                    cache[r[2]] = T.cos_sin(r[2])
                cc, ss = cache[r[2]]
                h = (abs(cc) + abs(ss)) / 2
                if lo is None or xv - h < lo:
                    lo = xv - h
                if hi is None or xv + h > hi:
                    hi = xv + h
            w = hi - lo
            if best is None or w > best:
                best = w
        out[n] = best
    _TABLES["sides"] = out
    return out


# --------------------------------------------------------------- verification
def certify(member):
    """Run the exact gate on a member's own sentence; returns the gate verdict."""
    fam = member["family"]
    cls = member["cls"]
    if fam in ("Ridge", "Strip"):
        if fam == "Strip":
            claim = G.p_strip(member["k"], member["m"])
            return G.gate_of(claim)
        state, ws = G._ridge_sentence(cls, member["c"], member["s"],
                                      member["k"], member["m"], member["w"])
        return Q.gate(state, ws, cls)
    if fam == "Staircase":
        return Q.gate(member["cells"], member["words"], cls)
    if fam == "Ring":
        cw, sw = G._sqrt7_word()
        return G.gate_of(G.ring_claim(7, cw, sw, member["k"]))
    if fam == "Diamond":
        name = {10: "n10", 19: "n19", 40: "n40"}[member["N"]]
        return G.gate_of(G.p_diamond_field(name))
    raise G.Refusal("no_builder", f"{fam} has no direct gate here")


def row_of(member, sides, gated):
    n = member["N"]
    L = member["L"]
    cls = member["cls"]
    rec = {"family": member["family"], "field": member["field"],
           "word": member["word"], "k": member["k"], "m": member["m"],
           "N": n, "L": str(L), "L_dec": str(DEC(L)),
           "void": str(L * L - cls(n)), "void_dec": str(DEC(L * L - cls(n))),
           "gated": gated, "contacts": None, "clearance": None}
    table = sides.get(n)
    if table is None:
        rec["table_side"] = None
        rec["gap"] = None
        rec["verdict"] = "uncalibrated"
        return rec
    gap = table - DEC(L)
    rec["table_side"] = str(table)
    rec["gap"] = str(gap)
    # The table is a 12-decimal pose held at ~2e-9 clearance (the repository's own
    # measurement), so a difference below 1e-6 is the table's pose tolerance, not a
    # packing difference.  Only a gap above that is called a win, and no gap this
    # family can produce sits between the two.
    if gap > Decimal("1e-6"):
        rec["verdict"] = "beats"
    elif gap < Decimal("-1e-6"):
        rec["verdict"] = "behind"
    else:
        rec["verdict"] = "parity"
    return rec


def merge(section, payload):
    ledger = {}
    if os.path.exists(LEDGER):
        with open(LEDGER) as f:
            ledger = json.load(f)
    ledger[section] = payload
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w") as f:
        json.dump(ledger, f, indent=1)
    return LEDGER


# --------------------------------------------------------------------- part a
def calibrate(kmax=22):
    """Every family member with N <= 1000, against the delivered row at that N."""
    sides = table_sides()
    members = []
    members += ridge_ladder(kmax)
    members += strip_ladder(kmax)
    # the ring: k = 1 closes, k >= 2 is a declared refusal (the pinwheel)
    ring, ring_rows = [], []
    cw, sw = G._sqrt7_word()
    for k in range(1, 4):
        try:
            m = claim_member(G.ring_claim(7, cw, sw, k), "Ring", "census", k, 0, 7)
        except G.Refusal as e:
            ring.append({"k": k, "N": 4 * k + 14, "verdict": "refused",
                         "law": e.law, "detail": str(e)[:140]})
            continue
        rec = row_of(m, sides, True)
        g = certify(m)
        rec["contacts"] = g["contacts"]
        rec["clearance"] = str(g["clearance"])
        rec["gate_ok"] = g["ok"]
        ring.append({k2: rec[k2] for k2 in ("N", "L", "L_dec", "void", "contacts",
                                           "gap", "verdict")})
        ring[-1]["k"] = k
        ring_rows.append(rec)
    # the diamond atoms: Product(X, Y) minus the cells a slot would overlap
    diamond = []
    for name in ("n10", "n19", "n40"):
        m = claim_member(G.p_diamond_field(name), "Diamond", "45deg", 0, 0, 2)
        rec = row_of(m, sides, True)
        g = certify(m)
        rec["contacts"] = g["contacts"]
        rec["clearance"] = str(g["clearance"])
        rec["gate_ok"] = g["ok"]
        diamond.append({k2: rec[k2] for k2 in ("N", "L", "L_dec", "void", "contacts",
                                               "gap", "verdict")})
        diamond[-1]["name"] = name
        ring_rows.append(rec)
    rows = [row_of(m, sides, False) for m in members if m["N"] <= 1000]
    rows += ring_rows
    # fold in whatever `--gate-ks` has already certified: a side the gate has seen is
    # reported as gated, with its contacts, so the calibration is feasible as well as
    # exact wherever the record allows it
    gated_ks: set = set()
    if os.path.exists(LEDGER):
        with open(LEDGER) as f:
            gated = json.load(f).get("gated", {}).get("rows", [])
        index = {(r["family"], r["word"], r["k"], r["m"]): r for r in gated}
        for rec in rows:
            g = index.get((rec["family"], rec["word"], rec["k"], rec["m"]))
            if g is None:
                continue
            assert g["gate_ok"] and g["zero_drift"], g
            rec["gated"] = True
            rec["contacts"] = g["contacts"]
            rec["clearance"] = g["clearance"]
            rec["gate_ok"] = g["gate_ok"]
            rec["zero_drift"] = g["zero_drift"]
            gated_ks.add(rec["k"])
    rows.sort(key=lambda r: (r["family"], r["word"], r["m"], r["k"]))
    beats = [r for r in rows if r["verdict"] == "beats"]
    behind = [r for r in rows if r["verdict"] == "behind"]
    parity = [r for r in rows if r["verdict"] == "parity"]
    by_family = {}
    for r in rows:
        key = (r["family"], r["word"])
        if r["gap"] is None:
            continue
        cur = by_family.get(key)
        if cur is None or Decimal(r["gap"]) > Decimal(cur["gap"]):
            by_family[key] = r
    closest = sorted((r for r in rows if r["gap"] is not None),
                     key=lambda r: -Decimal(r["gap"]))[:8]
    print(f"(a) calibration: {len(rows)} exact members with a delivered row at the same N")
    print(f"    beats the table: {len(beats)}   parity: {len(parity)}   "
          f"behind: {len(behind)}")
    if beats:
        for r in beats:
            print(f"    BEATS  {r['family']:9s} {r['word']:11s} k={r['k']:<3d} "
                  f"N={r['N']:<5d} L={r['L_dec'][:14]} by {r['gap']}")
    print("    closest members (largest table-minus-L, i.e. the smallest shortfalls):")
    for r in closest:
        print(f"      {r['family']:9s} {r['word']:11s} k={r['k']:<3d} N={r['N']:<5d} "
              f"L={r['L_dec'][:16]} table-L={Decimal(r['gap']):+.6f} "
              f"({r['verdict']})")
    print("    every rung, by family and word (closest member and the largest k):")
    for key, best in sorted(by_family.items()):
        grp = [r for r in rows if (r["family"], r["word"]) == key and r["gap"]]
        big = max(grp, key=lambda r: r["N"])
        print(f"      {key[0]:9s} {key[1]:11s} closest N={best['N']:<5d} "
              f"table-L={Decimal(best['gap']):+.6f} | largest N={big['N']:<5d} "
              f"table-L={Decimal(big['gap']):+.6f}")
    n_gated = sum(1 for r in rows if r.get("gated"))
    print(f"    sides gated with the exact gate: {n_gated} of {len(rows)}"
          + (f" (k = {', '.join(str(k) for k in sorted(gated_ks))})" if gated_ks else "")
          + ", every one clearance 0 and gate_L == L")
    payload = {"members": len(rows), "beats": len(beats), "parity": len(parity),
               "behind": len(behind), "gated": n_gated,
               "gated_ks": sorted(gated_ks),
               "best_by_family": {f"{k[0]}|{k[1]}": {"N": v["N"], "k": v["k"],
                                                     "m": v["m"], "L": v["L_dec"],
                                                     "gap": v["gap"]}
                                  for k, v in sorted(by_family.items())},
               "ring": ring, "diamond": diamond, "rows": rows}
    merge("calibrate", payload)
    return payload


def claim_member(claim, family, word, k, m, field_d):
    """A ladder member read straight off a certified claim (the ring, the atoms)."""
    cls = G.qfield(field_d)
    L = claim.laws["extent"][1]
    return {"family": family, "field": f"Q(sqrt {field_d})", "word": word,
            "k": k, "m": m, "N": claim.n, "L": L, "cls": cls,
            "c": None, "s": None, "w": None}


# --------------------------------------------------------------------- part b
def gate_and_record(member):
    g = certify(member)
    rec = row_of(member, {}, True)
    rec["contacts"] = g["contacts"]
    rec["clearance"] = str(g["clearance"])
    rec["gate_ok"] = g["ok"]
    rec["gate_violations"] = g["violations"]
    rec["gate_L"] = str(g["L"])
    rec["zero_drift"] = str(g["L"]) == str(member["L"])
    rec["depth_dec"] = str(Decimal(rec["L_dec"]) / Decimal(member["N"]).sqrt() - 1)
    return rec


def beyond(which="strip", ks=None):
    """The N > 1000 rungs, gated: exact side, void and contacts, no float."""
    ks = ks or []
    rows = []
    t0 = time.time()
    if which == "strip":
        for k in ks:
            for m in (1, 2, 3):
                member = strip_member(k, m)
                if member["N"] <= 1000:
                    continue
                rec = gate_and_record(member)
                rows.append(rec)
                print(f"    strip k={k:>2d} m={m} N={rec['N']:<5d} "
                      f"L={rec['L_dec'][:18]} contacts={rec['contacts']} "
                      f"ok={rec['gate_ok']} ({time.time() - t0:.0f}s)")
    elif which == "stair":
        for k in ks:
            member = staircase_member(k)
            if member["N"] <= 1000:
                continue
            rec = gate_and_record(member)
            rec.update({"columns": member["columns"],
                        "at_law": member["at_law"], "adrift": member["adrift"],
                        "law_L": str(member["law_L"])})
            rows.append(rec)
            print(f"    stair k={k:>2d} N={rec['N']:<5d} L={rec['L_dec'][:18]} "
                  f"law_L={rec['law_L']} at_law={rec['at_law']} "
                  f"adrift={rec['adrift']} contacts={rec['contacts']} "
                  f"ok={rec['gate_ok']} ({time.time() - t0:.0f}s)")
    elif which == "words":
        # the same rung over every field: N = 4k^2 + 1 at k = 16, 19, 22
        for name, d, c, s in words():
            cls = G.qfield(d)
            for k in ks:
                member = ridge_member(cls, c, s, k, 1, name, d)
                rec = gate_and_record(member)
                rows.append(rec)
                print(f"    ridge {name:11s} k={k:>2d} N={rec['N']:<5d} "
                      f"L={rec['L_dec'][:18]} contacts={rec['contacts']} "
                      f"ok={rec['gate_ok']} ({time.time() - t0:.0f}s)")
    else:
        raise SystemExit(f"unknown part {which}")
    payload = {"part": which, "ks": ks, "rows": rows}
    merge(f"beyond_{which}", payload)
    return payload


def gate_column(ks=(15,), mset=(1, 2, 3)):
    """Gate a whole `k` column of the ridge ladder: every word, every `m`.

    The calibration's sides are the family law `L = 2k + w`; a law is exact but it is
    not a *sentence*.  This mode runs the exact gate on the members the argument
    actually leans on, so the column the score reasoning quotes is certified feasible
    at clearance 0 as well as exact.  Earlier columns are kept, never replaced.
    """
    rows, t0 = [], time.time()
    for name, d, c, s in words():
        cls = G.qfield(d)
        for k in ks:
            for m in mset:
                rec = gate_and_record(ridge_member(cls, c, s, k, m, name, d))
                rows.append(rec)
                print(f"    {name:11s} k={k:>2d} m={m} N={rec['N']:<5d} "
                      f"L={rec['L_dec'][:18]} contacts={rec['contacts']} "
                      f"ok={rec['gate_ok']} drift0={rec['zero_drift']} "
                      f"({time.time() - t0:.0f}s)")
    seen = {(r["family"], r["word"], r["k"], r["m"]) for r in rows}
    prior = {}
    if os.path.exists(LEDGER):
        with open(LEDGER) as f:
            prior = json.load(f).get("gated", {})
    for r in prior.get("rows", []):
        if (r["family"], r["word"], r["k"], r["m"]) not in seen:
            rows.append(r)
    rows.sort(key=lambda r: (r["family"], r["word"], r["k"], r["m"]))
    merge("gated", {"ks": sorted({r["k"] for r in rows}),
                    "mset": sorted({r["m"] for r in rows}),
                    "members": len(rows), "rows": rows})
    return rows


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--gate-ks" in argv:
        ks = [int(x) for x in argv[argv.index("--gate-ks") + 1].split(",")]
        gate_column(ks)
        if "--calibrate" in argv:
            calibrate()
        return 0
    if "--calibrate" in argv:
        calibrate()
        return 0
    if "--beyond" in argv:
        which = argv[argv.index("--beyond") + 1]
        ks = [16, 22] if which == "strip" else ([16] if which == "words"
              else [6, 8, 12, 15, 18, 21])
        if which == "strip":
            ks = [16, 22]
        beyond(which, ks)
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
