#!/usr/bin/env python3
r"""glm_plan.py — run 136: let the GLM decide what is worth attempting.

Parts of this repository are *proved closed* (doc 16's address, doc 49's
induction, doc 75's block substitution, run 135's 45° uniqueness and band-5
legalisation, run 134's square ties, and run 136's two notches).  What has never
been written down is the thing that follows: **which remaining claims are
decidable at all**, and therefore which runs could have succeeded before they
were started.

This instrument makes that a first-class object.  For every band that still has
an unbeaten row it writes down

    the claim      "one more cell fits inside this frontier pose's void"
    the obligation cells to add `j`, void to save `d` (doc 75's price),
                   the frontier pose's angle-class count,
    the prize      (k - L) / sqrt(n+1)   [exact, `sqscore` scale]

and then applies a decidability rule, so that a band is *scheduled* only when
its obligation is a bounded exact enumeration:

  R1  the frontier pose is structured: at most `MAX_CLASSES` angle classes.
      A pose with hundreds of classes is a continuum object; its "next pose" is
      an open optimisation, not an enumeration.
  R2  the obligation lives in the small-pose regime: n + j <= `MAX_POSE`.
      Above that the void's boundary is a long list of cells and the placement
      space stops being a bounded enumeration (this is exactly the step that
      made runs 116/117 undecidable: a 20-26 cell obligation on a 500-1000
      cell pose).
  R3  the void to save is under a cell: at most `MAX_PRICE` unit^2.
  R4  the pose is not at the band's void limit: V/j <= `MAX_FILL`.

Refusals are the point of the file.  A refused band has an obligation the
engine cannot decide, so any run spent on it is a run spent without a proof
obligation — which is the pattern that produced the dead ends.

The claims are `glm_wheels.Claim` objects (the audited six-slot record), so the
plan itself is in the GLM's own vocabulary and `glm_wheels --audit` covers it.

    python3 scripts/glm_plan.py            # write the worklist
    python3 scripts/glm_plan.py --selftest
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from decimal import Decimal, getcontext

getcontext().prec = 40

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import glm_wheels as GW                 # noqa: E402
import sqscore as SQ                    # noqa: E402

CSV = os.path.join(ROOT, "workspace/submission/submission.csv")
CHECKED = os.path.join(ROOT, "workspace/push/pub_bounds_check.json")
OUT = os.path.join(ROOT, "workspace/push/glm_plan.json")
TOL = 1e-6

# Published frontier for n = 1..100: (best-known upper bound, best proved lower
# bound), from The Squares Project "100 Best Known Square Packings", J. Levy,
# 2026-10-20 (jlevy.github.io/squares/square-packings-100-20261008.pdf), read
# 2026-11-25.  Where a value is proved optimal the two entries are equal.  This
# is the only external data in the file; `--frontier` compares the delivered
# table against it, which is how the repository learns whether it is at the
# world frontier or behind it.
PUB = {
    1: (1, 1), 2: (2, 2), 3: (2, 2), 4: (2, 2), 5: (2.707107, 2.707107),
    6: (3, 3), 7: (3, 3), 8: (3, 3), 9: (3, 3), 10: (3.707107, 3.707107),
    11: (3.877084, 3.877084), 12: (4, 3.9715), 13: (4, 4), 14: (4, 4),
    15: (4, 4), 16: (4, 4), 17: (4.675531, 4.660442), 18: (4.822876, 4.705),
    19: (4.885619, 4.825), 20: (5, 4.905), 21: (5, 5), 22: (5, 5), 23: (5, 5),
    24: (5, 5), 25: (5, 5), 26: (5.621321, 5.545), 27: (5.707107, 5.6435),
    28: (5.824445, 5.735), 29: (5.933834, 5.81), 30: (6, 5.8835),
    31: (6, 5.9525), 32: (6, 6), 33: (6, 6), 34: (6, 6), 35: (6, 6), 36: (6, 6),
    37: (6.59862, 6.44), 38: (6.707107, 6.545), 39: (6.810723, 6.65),
    40: (6.828428, 6.718), 41: (6.926694, 6.775), 42: (7, 6.8475),
    43: (7, 6.9075), 44: (7, 6.9725), 45: (7, 7), 46: (7, 7), 47: (7, 7),
    48: (7, 7), 49: (7, 7), 50: (7.571429, 7.4), 51: (7.690356, 7.47),
    52: (7.707107, 7.55), 53: (7.822876, 7.6275), 54: (7.846668, 7.685),
    55: (7.945772, 7.728), 56: (8, 7.8025), 57: (8, 7.8725), 58: (8, 7.935),
    59: (8, 8), 60: (8, 8), 61: (8, 8), 62: (8, 8), 63: (8, 8), 64: (8, 8),
    65: (8.535534, 8.35), 66: (8.656855, 8.43), 67: (8.707107, 8.48),
    68: (8.798796, 8.53), 69: (8.827195, 8.62), 70: (8.880961, 8.6575),
    71: (8.944072, 8.721), 72: (9, 8.76), 73: (9, 8.813), 74: (9, 8.8675),
    75: (9, 8.94), 76: (9, 8.965), 77: (9, 9), 78: (9, 9), 79: (9, 9),
    80: (9, 9), 81: (9, 9), 82: (9.535534, 9.32), 83: (9.634758, 9.37),
    84: (9.697935, 9.4225), 85: (9.742641, 9.475), 86: (9.820536, 9.503),
    87: (9.838816, 9.58), 88: (9.882452, 9.62), 89: (9.949748, 9.65),
    90: (10, 9.73), 91: (10, 9.7625), 92: (10, 9.77), 93: (10, 9.88),
    94: (10, 9.95), 95: (10, 9.965), 96: (10, 9.97), 97: (10, 10),
    98: (10, 10), 99: (10, 10), 100: (10, 10),
}

#: proved-optimal rows among 1..100, from the source's `data-status="proved"`.
#: `pub_bounds_check.py` re-derives this set from the saved frontier table; the
#: literal is the fallback when the ledger is absent.
PROVED_OPTIMAL_FALLBACK = frozenset(
    {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 21, 22, 23, 24, 25,
     32, 33, 34, 35, 36, 44, 45, 46, 47, 48, 49, 59, 60, 61, 62, 63, 64, 76,
     77, 78, 79, 80, 81, 95, 96, 97, 98, 99, 100})

MAX_CLASSES = 4       # R1: a structured pose, not a continuum
MAX_POSE = 64         # R2: the obligation lives in the small-pose regime
MAX_PRICE = 0.25      # R3: at most a quarter of a cell of void to save
MAX_FILL = 0.999      # R4: not already at the band's void limit


def load_rows():
    rows = {}
    with open(CSV) as f:
        for r in csv.DictReader(f):
            rows.setdefault(int(r["n"]), []).append(
                (float(r["x"]), float(r["y"]), float(r["angle"])))
    return rows


def classes(state, tol=TOL):
    """Distinct angle classes mod pi/2 (discovery: decimal angles, 1e-6)."""
    seen = set()
    for _x, _y, t in state:
        c = (t % (math.pi / 2) + math.pi / 2) % (math.pi / 2)
        if math.pi / 2 - c < tol:
            c = 0.0
        seen.add(round(c / tol) * tol)
    return len(seen)


def bands(rows):
    """The frontier of every band k: the largest n < k^2 whose row beats k."""
    out = {}
    for n, st in rows.items():
        k = SQ.grid(n)
        L = SQ.extent(st)
        if L >= k - 1e-12 or n >= k * k:
            continue
        cur = out.get(k)
        if cur is None or n > cur["n"]:
            out[k] = {"k": k, "n": n, "L": L, "j": k * k - n,
                      "V": L * L - n}
    for k, b in out.items():
        b["classes"] = classes(rows[b["n"]])
        b["price"] = b["V"] - (b["j"] - 1)
        b["fill"] = b["V"] / b["j"]
        root = Decimal(b["n"] + 1).sqrt()
        b["prize"] = float((Decimal(b["k"]) - Decimal(b["L"])) / root)
    return dict(sorted(out.items()))


def pub_table():
    """The published frontier: `(ub, lb, proved)`.  Machine-checked if available.

    `pub_bounds_check.py` diffs the hand transcription against the source's own
    table; when its ledger exists the *verified* numbers are used, and the
    proved-optimal set is the source's 45 `data-status="proved"` rows.
    """
    if os.path.exists(CHECKED):
        with open(CHECKED) as f:
            c = json.load(f)
        proved = frozenset(int(n) for n in c.get("proved_rows", []))
        src = c.get("verified_table") or {}
        tab = {}
        for n, (ub, lb) in PUB.items():
            v = src.get(str(n))
            tab[n] = (float(v["ub"]), float(v["lb"])) if v else (ub, lb)
        return tab, (proved or PROVED_OPTIMAL_FALLBACK)
    return dict(PUB), PROVED_OPTIMAL_FALLBACK


def decide(b, pub=None, proved=None):
    """The rules.  Returns (ok, [reasons]).

    R1 structured pose, R2 small-pose regime, R3 void under a cell, R4 not at
    the band's void limit, and **R5 proved-optimal target**: if the claim's row
    `n + 1` has a *proved optimal* side, then no search is needed — either the
    proved optimum is at or above the frontier side (the claim is impossible) or
    a packing attaining it already exists (the claim is already solved).  Row 6
    (`s(6) = 3`, Kearney-Shiu) is the case that matters for band `k = 3`.
    """
    pub, proved = pub or PUB, proved or PROVED_OPTIMAL_FALLBACK
    why = []
    if b["classes"] > MAX_CLASSES:
        why.append(f"R1 continuum pose ({b['classes']} angle classes)")
    if b["n"] + b["j"] > MAX_POSE:
        why.append(f"R2 large-pose obligation (n+j = {b['n'] + b['j']} > {MAX_POSE})")
    if b["price"] > MAX_PRICE:
        why.append(f"R3 must save {b['price']:.3f} unit^2 of void")
    if b["fill"] > MAX_FILL:
        why.append(f"R4 pose at the band void limit (V/j = {b['fill']:.3f})")
    target = b["n"] + 1
    if target in proved:
        opt = pub.get(target, (None, None))[0]
        why.append(f"R5 target row {target} is proved optimal (s = {opt})")
    return (not why), why


def needs_world_record(b, pub=None, proved=None) -> bool:
    """True when the claim needs a side better than the published best known."""
    pub, proved = pub or PUB, proved or PROVED_OPTIMAL_FALLBACK
    target = b["n"] + 1
    if target in proved:
        return True
    ub = pub.get(target, (None, None))[0]
    return ub is not None and b["L"] < ub - 1e-9


def claim(b, pub=None, proved=None) -> "GW.Claim":
    """The band's claim in the audited six-slot form."""
    ok, why = decide(b, pub, proved)
    return GW.Claim(
        domain="packing", family="next_row", params={"k": b["k"], "n": b["n"]},
        size=b["n"] + 1,
        laws={
            "prize": ("(k - L) / sqrt(n + 1)", repr(b["prize"])),
            "price": ("V(m*) - (j* - 1)", repr(b["price"])),
            "cells_to_add": ("k^2 - n", str(b["j"])),
        },
        payload=None,
        meta={"frontier": b["n"], "L": repr(b["L"]), "classes": b["classes"],
              "decidable": ok, "refusals": why},
        measure=("side_needed", repr(b["L"])),
        invariant=("void_budget", repr(b["j"] - 1)),
    )


def plan(rows=None) -> dict:
    rows = rows or load_rows()
    bs = bands(rows)
    pub, proved = pub_table()
    out = {"bands": {}, "scheduled": [], "refused": [],
           "pub_source": ("machine-checked (pub_bounds_check.json)"
                          if os.path.exists(CHECKED) else "hand transcription")}
    for k, b in bs.items():
        ok, why = decide(b, pub, proved)
        c = claim(b, pub, proved)
        rec = dict(b, decidable=ok, refusals=why, claim=c.brief(),
                   requires_world_record=needs_world_record(b, pub, proved))
        out["bands"][k] = rec
        (out["scheduled"] if ok else out["refused"]).append(rec)
    key = lambda r: -r["prize"]                                   # noqa: E731
    out["scheduled"].sort(key=key)
    out["refused"].sort(key=key)
    out["totals"] = {
        "bands": len(bs),
        "scheduled": len(out["scheduled"]),
        "refused": len(out["refused"]),
        "prize_scheduled": sum(r["prize"] for r in out["scheduled"]),
        "prize_refused": sum(r["prize"] for r in out["refused"]),
        "prize_all": sum(r["prize"] for r in out["bands"].values()),
    }
    return out


def frontier(rows=None) -> dict:
    """Delivered table vs the published best-known / proved lower bounds, n<=100.

    Two numbers matter: `behind` (rows where a published packing is better than
    ours — nothing to import if zero) and `room` (sum over rows of
    `(L_table - LB)/sqrt(n)`, the certified distance to the proved bounds, which
    is the only room that cannot be taken away by someone else's construction).
    """
    rows = rows or load_rows()
    tab, proved = pub_table()
    behind, gaps = [], []
    room = Decimal(0)
    for n in sorted(tab):
        L = SQ.extent(rows[n])
        ub, lb = tab[n]
        if L > ub + 1e-6:
            behind.append({"n": n, "L": L, "pub": ub,
                           "gain": (L - ub) / math.sqrt(n)})
        if L > lb + 1e-6:
            gaps.append({"n": n, "L": L, "lb": lb,
                         "gain": (L - lb) / math.sqrt(n)})
            room += (Decimal(repr(L)) - Decimal(repr(lb))) / Decimal(n).sqrt()
    gaps.sort(key=lambda r: -r["gain"])
    return {"behind": behind, "behind_total": sum(r["gain"] for r in behind),
            "room": str(room), "room_rows": len(gaps), "top": gaps[:12],
            "proved_rows_in_100": len([n for n in proved if n <= 100])}


def selftest() -> int:
    rows = load_rows()
    bs = bands(rows)
    assert len(bs) == 30, len(bs)
    # control 1: the table's frontier for k = 32 is row 998 at 31.986238620
    b32 = bs[32]
    assert b32["n"] == 998 and abs(b32["L"] - 31.986238620) < 1e-9, b32
    assert abs(b32["price"] - 0.120) < 5e-3, b32["price"]
    print(f"  1. k=32 frontier n={b32['n']} L={b32['L']:.9f} price "
          f"{b32['price']:+.3f} (doc 75: +0.120)")

    # control 2: the totals are the doc-75 inheritance programme
    tot = sum(r["prize"] for r in bs.values())
    print(f"  2. sum of the 30 next-row prizes: {tot:.5f} "
          f"(doc 75 quotes +0.23251 for the band inheritance)")
    assert 0.15 < tot < 0.35, tot

    # control 3: the rules reproduce on a hand-built band
    fake = {"k": 4, "n": 11, "L": 3.85, "j": 5, "V": 2.5,
            "classes": 3, "price": -0.5, "fill": 0.5, "prize": 1e-3}
    ok, why = decide(fake)
    assert ok, why
    fake.update({"n": 2000, "j": 20})
    ok, why = decide(fake)
    assert not ok and "R2" in why[0], why
    fake.update({"n": 11, "j": 5, "classes": 40})
    ok, why = decide(fake)
    assert not ok and "R1" in why[0], why
    print("  3. rules: a structured small obligation schedules, a 40-class "
          "pose is refused (R1)")

    # control 4: the machine-checked frontier says exactly one row is behind
    # (n = 90: the source has 9.99403876 against our 10.0) and the certified
    # room is 1.09647, not the hand-transcribed 1.14087
    f = frontier(rows)
    assert [r["n"] for r in f["behind"]] == [90], f["behind"]
    assert abs(float(f["room"]) - 1.09647) < 1e-4, f["room"]
    print(f"  4. n<=100 vs the machine-checked frontier: {len(f['behind'])} row "
          f"behind (n = 90), certified room {float(f['room']):.5f} over "
          f"{f['room_rows']} rows")

    # control 5: R5 refuses the proved-optimal target row 6 of band k = 3, and
    # the three surviving bands are all world-record claims
    p = plan(rows)
    b3 = p["bands"][3]
    assert not b3["decidable"] and any(r.startswith("R5") for r in b3["refusals"]), b3
    assert b3["requires_world_record"] and p["bands"][3] not in p["scheduled"], b3
    assert [r["k"] for r in p["scheduled"]] == [4, 5, 7], [r["k"] for r in p["scheduled"]]
    assert all(r["requires_world_record"] for r in p["scheduled"])
    print(f"  5. R5: band k=3 refused — {b3['refusals'][0]}; scheduled "
          f"{[r['k'] for r in p['scheduled']]}, all world-record claims")
    print("  selftest OK (5 controls)")
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()
    p = plan()
    p["frontier"] = frontier()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    p["schema"] = "glm_plan/1"
    p["rules"] = {"MAX_CLASSES": MAX_CLASSES, "MAX_POSE": MAX_POSE,
                  "MAX_PRICE": MAX_PRICE, "MAX_FILL": MAX_FILL}
    with open(OUT, "w") as f:
        json.dump(p, f, indent=1, default=str)
    print(f"{'k':>3} {'front':>5} {'j':>3} {'price':>7} {'classes':>7} "
          f"{'prize':>9}  verdict")
    for r in p["scheduled"] + p["refused"]:
        v = "SCHEDULE" if r["decidable"] else "refuse: " + "; ".join(r["refusals"])
        print(f"{r['k']:>3} {r['n']:>5} {r['j']:>3} {r['price']:>+7.3f} "
              f"{r['classes']:>7} {r['prize']:>9.2e}  {v}")
    t = p["totals"]
    print(f"\n{t['scheduled']} scheduled / {t['refused']} refused of {t['bands']} "
          f"bands; prize scheduled {t['prize_scheduled']:.3e}, "
          f"refused {t['prize_refused']:.3e}, total {t['prize_all']:.5f}")
    f = p["frontier"]
    print(f"\npublished frontier, n<=100 (machine-checked): "
          f"{len(f['behind'])} row behind; certified room "
          f"{float(f['room']):.5f} over {f['room_rows']} rows")
    for r in f["top"][:8]:
        print(f"   n={r['n']:>3}  L={r['L']:.6f}  LB={r['lb']:.6f}  "
              f"room={r['gain']:.5f}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
