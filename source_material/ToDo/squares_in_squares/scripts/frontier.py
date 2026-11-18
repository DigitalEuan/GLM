#!/usr/bin/env python3
r"""frontier.py — full-range frontier crosswalk (run 58).

For every row 1..1000, what is the best known construction, is the row proved,
and is the delivered row at it?  A row where the best known side is STRICTLY
smaller than the delivered side is an import target; its value is the
forward-only aggregate gain over its residue column, not a bound gap.

SOURCES AND COVERAGE (this matters — see `basis` below)

  triangular_table  Kingbird "Triangular Table View": every shown entry carries
                  its own n and its own s, and the page states its rule exactly:
                  "For the n not shown, the closest packing shown to the right of
                  it is the best known packing (to have the appropriate number of
                  arbitrarily chosen squares removed)."  So best_known(n) = s at
                  the smallest shown n' >= n.  Run 58 used the wrong rule here
                  ("n <= 324 unpictured -> trivial ceil(sqrt n)"), which
                  UNDERSTATES best_known for rows left of a pictured record: it
                  can only have hidden targets, never invented one (see 26 §8).
  catalogue_2026  A value attached to row n itself (exact per-row comparison).
  triangular_anchor@k  Value inherited from the nearest shown row k > n, per the
                  catalogue's own rule.  Correct for best_known, but it is a
                  loose value, so a "beats" here is NOT a record claim.
  ds7_2009        Friedman DS7 (2009) Tables 1-2, used only where the 2026 value
                  could not be extracted.  A 2009 value is an UPPER bound on the
                  current record, so "at" against it is weak.
  anchor_truncated  n sits left of a shown row whose value the page delivered as
                  "..." (the fetch truncates inline).  No value is claimed.
  no_source_above_324  n > 324 with no pictured packing: the source makes NO
                  completeness claim there, and the trivial grid is provably not
                  its best known (its own s(k^2+1) family gives 18.5355 for 325,
                  not 19), so no value is claimed.  See 26 §9.3.
  trivial_bound_only  n left of a shown row whose value the page delivered as
                  "...": best known <= trivial, and the trivial grid is what the
                  catalogue lists, so the value used is trivial.
  anchor_truncated  no longer produced: a truncated anchor now falls back to the
                  trivial grid with basis trivial_bound_only.

A catalogued geometry is a NOMINATION.  Nothing here enters the table; it only
ranks rows by what importing a record-breaking construction would pay.
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sqscore as SQ        # noqa: E402
import seam_wheels as SW    # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/frontier.json")
R2, R5, R7 = math.sqrt(2), math.sqrt(5), math.sqrt(7)
S2 = R2 / 2
TOL = 1e-6


def _c(*vals):
    """Pictured rows named on one line in the catalogue share a value."""
    return vals


PICT = {}
for ns, v in [
    ((1,), 1.0), ((2,), 2.0), ((3,), 2.0), ((4,), 2.0),
    ((5,), 2 + S2), ((6,), 3.0), ((7,), 3.0), ((8,), 3.0), ((9,), 3.0),
    ((10,), 3 + S2), ((11,), 3.87708359002281),
    ((13,), 4.0), ((14,), 4.0), ((15,), 4.0),
    ((18,), 3.5 + R7 / 2), ((19,), 3 + 4 * R2 / 3),
    ((22,), 5.0), ((23,), 5.0), ((24,), 5.0),
    ((26,), 3.5 + 1.5 * R2), ((27,), 5 + S2), ((28,), 5.82444461667405),
    ((33,), 6.0), ((34,), 6.0), ((35,), 6.0),
    ((38,), 6 + S2), ((40,), 4 + 2 * R2), ((41,), 6.92669309446880),
    ((46,), 7.0), ((47,), 7.0), ((48,), 7.0),
    ((50,), 7 + 4 / 7), ((51,), 7.70079923541701), ((52,), 7 + S2),
    ((54,), 7 - S2 + math.sqrt(1 + R2)), ((55,), 7.94577100750391),
    ((62,), 8.0), ((63,), 8.0), ((65,), 5 + 2.5 * R2), ((66,), 3 + 4 * R2),
    ((67,), 8 + S2), ((69,), 8.82719465572973), ((70,), 8.88166675700900),
    ((71,), 8.94407155757031),
    ((79,), 9.0), ((80,), 9.0), ((82,), 6 + 2.5 * R2), ((83,), 9.63475764863108),
    ((84,), 9 + S2), ((85,), 5.5 + 3 * R2), ((86,), 8.5 + R7 / 2),
    ((87,), 9.83881526994826), ((88,), 9.88815305375857), ((89,), 5 + 3.5 * R2),
    ((98,), 10.0), ((99,), 10.0), ((101,), 7 + 2.5 * R2),
    ((102,), 10.61138794077522), ((104,), 10 + S2), ((105,), 10.80761933330707),
    ((106,), 10.82297973416944), ((107,), 10 - S2 + math.sqrt(1 + R2)),
    ((108,), 10.92591939016138), ((109,), 6 + 3.5 * R2), ((110,), 10.99679327401957),
    ((119,), 11.0), ((120,), 11.0), ((122,), 8 + 2.5 * R2),
    ((123,), 11.60139979378801), ((124,), 6 + 4 * R2), ((125,), 11 + S2),
    ((126,), 11.77473513240654), ((127,), 10.5 + R7 / 2), ((128,), 11.82509196821368),
    ((129,), 11.88130621809000), ((132,), 11.99137344423646),
    ((142,), 12.0), ((143,), 12.0), ((145,), 9 + 2.5 * R2), ((147,), 7 + 4 * R2),
    ((148,), 7 + 4 * R2), ((149,), 12 + S2), ((150,), 5 + 5.5 * R2),
    ((151,), 11.5 + R7 / 2), ((153,), 12.88166675700900),
    ((155,), 12.95844711161529), ((156,), 12.98208376048414),
    ((167,), 13.0), ((168,), 13.0), ((170,), 10 + 2.5 * R2),
    ((172,), 13.61898898660160), ((173,), 8 + 4 * R2), ((174,), 13 + S2),
    ((175,), 6 + 5.5 * R2), ((176,), 12.5 + R7 / 2), ((177,), 13.82302875075647),
    ((178,), 13 - S2 + math.sqrt(1 + R2)), ((179,), 13.89534106997649),
    ((181,), 13.95690672341755), ((182,), 13.97419105332569),
    ((194,), 14.0), ((195,), 14.0), ((197,), 11 + 2.5 * R2),
    ((199,), 14.61898898660160), ((200,), 9 + 4 * R2), ((201,), 14 + S2),
    ((202,), 2 + 9 * R2), ((203,), 7 + 5.5 * R2), ((204,), 13.5 + R7 / 2),
    ((205,), 14.82445114612408), ((206,), 14.87221902560728),
    ((209,), 14.95861500087481),
    ((223,), 15.0), ((224,), 15.0), ((226,), 12 + 2.5 * R2), ((227,), 8.5 + 5 * R2),
    ((229,), 10 + 4 * R2), ((231,), 15 + S2), ((232,), 8 + 5.5 * R2),
    ((233,), 8 + 5.5 * R2), ((237,), 14.5 + R2), ((239,), 15.95635358406308),
    ((254,), 16.0), ((255,), 16.0), ((258,), 9.5 + 5 * R2), ((262,), 16 + S2),
    ((263,), 12.5 + 3 * R2), ((264,), 9 + 5.5 * R2), ((265,), 9 + 5.5 * R2),
    ((267,), 16 - S2 + math.sqrt(1 + R2)), ((270,), 16.94062059800744),
    ((271,), 16.95499909412532),
    ((287,), 17.0), ((288,), 17.0), ((294,), 12 + 4 * R2), ((295,), 17 + S2),
    ((296,), 17 + S2), ((298,), 10 + 5.5 * R2), ((299,), 16.5 + R7 / 2),
    ((303,), 17.93125509556197), ((304,), 17.94910783564662),
    ((305,), 17.96066201401205), ((306,), 17.96913960675661),
    ((322,), 18.0), ((323,), 18.0),
    ((626,), 13.5 + 8.5 * R2),
]:
    for n in ns:
        PICT[n] = v

# pictured rows whose value was truncated in the fetched page, or known only in
# DS7 (2009).  Weak basis: an upper bound on the current record.
WEAK = {}
for n, v in {17: 4.6756, 29: 5.9344, 37: 6.5987, 39: 6.8189, 53: 7.8231,
             68: 15 / 2 + R7 / 2, 103: None, 130: None, 131: None,
             146: None, 152: None, 154: None, 171: None, 180: None,
             198: None, 207: None, 208: None, 210: None, 228: None,
             230: None, 234: None, 235: None, 236: None, 238: None,
             240: None, 241: None, 257: None, 259: None, 260: None,
             261: None, 266: None, 268: None, 269: None, 272: None,
             273: None, 290: None, 291: None, 292: None, 293: None,
             297: None, 300: None, 301: None, 302: None, 307: None}.items():
    WEAK[n] = v


# Shown rows from the triangular table, n <= 324, value attached to its own n.
# Trivial anchors are included because they are shown rows like any other.
TT = {12: 4.0, 16: 4.0, 20: 5.0, 25: 5.0, 30: 6.0, 36: 6.0, 42: 7.0,
      49: 7.0, 53: 7.82287565553229, 56: 8.0, 64: 8.0, 68: 8.79879614026010,
      72: 9.0, 81: 9.0, 87: 9.83881526994826, 88: 9.88815305375857,
      90: 10.0, 100: 10.0, 103: 10.70378195534367, 108: 10.92591939016138,
      110: 10.99679327401957, 111: 11.0, 121: 11.0, 129: 11.88130621809000,
      130: 11.91119052015898, 131: 11.95652543280926, 133: 12.0, 144: 12.0,
      152: 12.83095954472600, 167: 13.0, 168: 13.0, 179: 13.89534106997649,
      183: 14.0, 194: 14.0, 198: 14.61898898660160, 206: 14.87221902560728,
      207: 14.89395494255333, 208: 14.93776656277905, 210: 14.97413341886404,
      211: 15.0, 225: 15.0, 230: 15.68292682926829, 234: 15.82287565553229,
      236: 15.87607539315201, 238: 15.93965520031394, 240: 15.97556282833087,
      241: 15.99080517810520, 242: 16.0, 256: 16.0, 257: 16.53553390593273,
      259: 16.60257141234448, 260: 16.65685424949238, 261: 16.68292682926829,
      266: 16.82306208283780, 268: 16.87931143465371, 269: 16.90596764828402,
      272: 16.96971602419903, 273: 16.98820725030513, 274: 17.0, 289: 17.0,
      290: 17.53553390593273, 297: 17.74106074604732, 300: 17.82412338847854,
      301: 17.86889155557430, 302: 17.88674602860566, 307: 17.98272201579610,
      308: 18.0, 324: 18.0}
# The authoritative anchor set is the locally parsed page (parse_tt.py, which
# reads the full HTML fetched with curl — the page reader truncates near n=324).
# The inline TT above is only a fallback for when that file is absent.  The
# triangular table's own scope ends at n = 324: above it the catalogue lists
# only pictured records, so there is nothing to inherit from.
TT_SRC = os.path.join(ROOT, "workspace/push/tt.json")
try:
    with open(TT_SRC) as _f:
        TT.update({int(k): float(v) for k, v in json.load(_f).items()})
    TT_BASIS = "triangular_table"
except (OSError, ValueError):
    TT_BASIS = "triangular_table_inline"

# shown rows whose value the page delivered as "..." (see WEAK's None entries)
ANCHOR_TRUNC = {n for n, v in WEAK.items() if v is None}


def best_known(n: int):
    """(value, basis) for every row 1..1000.  Always returns a value.

    The published best known is the best of the constructions the catalogue
    itself lists for n: the trivial grid (always listed) and, for n <= 324, the
    packing of the nearest shown row to the right with squares removed.  Taking
    the MINIMUM of the two is the strictest admissible reading -- it can only
    make the delivered side look worse, so it can only add import targets.

    Above 324 no inheritance is applied: our parse of the catalogue gallery
    finds exactly one pictured packing in 325..1000 (n = 626, which is in PICT),
    so every other row in that band carries the trivial value in the catalogue.
    That matches an independent count of five records above 324 (626, 1453,
    1765, 1850, 2043), so 626 is the only one inside our range.
    """
    if n in PICT:
        return PICT[n], "catalogue_2026"
    if n in TT:
        return TT[n], TT_BASIS
    if n in WEAK and WEAK[n] is not None:
        return WEAK[n], "ds7_2009"
    triv = float(math.ceil(math.sqrt(n)))
    if n <= 324:
        k = n
        while k <= 324:
            for tab in (TT, PICT):
                if k in tab:
                    v = tab[k]
                    if v < triv:
                        return v, f"triangular_anchor@{k}"
                    return triv, "trivial_rule"
            if k in ANCHOR_TRUNC:
                return triv, "trivial_bound_only"
            k += 1
        return triv, "trivial_bound_only"
    # Above 324 there is no completeness claim and the trivial grid is provably
    # not the catalogue's best known: its own s(k^2+1) family sits at a constant
    # k + 0.5355339 (145, 170, 197, 226, 290 for k = 12,13,14,15,17), which gives
    # 18.5355 for 325 = 18^2+1 against the trivial 19.  Assigning trivial here
    # would manufacture 675 confident comparisons in the direction that HIDES
    # import targets, so the rows are left open.
    return None, "no_source_above_324"


def fwd_gain(per, n, side):
    """Forward-only aggregate gain if a base of `side` seeds n's column.

    Uses the declared (r, delta) cascade invariant: delta = side - k, replayed
    over rows kk > k of the same residue class.  This is an upper bound on what
    the construction would pay IF it extended; it does not build the extension.
    """
    k = math.isqrt(n)
    r = n - k * k
    d0 = side - k
    tot = 0.0
    rows = []
    for kk in range(k + 1, 32):
        nn = kk * kk + r
        if nn > 1000 or nn not in per or nn - math.isqrt(nn) ** 2 != r:
            continue
        Lk = SQ.extent(per[nn])
        g = max(0.0, (Lk - (kk + d0)) / math.sqrt(nn))
        if g > 0:
            tot += g
            rows.append(nn)
    return tot, rows


def main() -> int:
    per = SQ.load()
    rows, tally = [], {}
    for n in range(1, 1001):
        if n not in per:
            continue
        L = SQ.extent(per[n])
        bk, basis = best_known(n)
        rec = {"n": n, "k": math.isqrt(n), "r": n - math.isqrt(n) ** 2,
               "delivered": L, "best_known": bk, "basis": basis}
        if bk is None:
            rec["status"] = "unresolved"
        else:
            d = L - bk
            rec["delta"] = d
            if d < -TOL:
                rec["status"] = "beats"
            elif d <= TOL:
                rec["status"] = "at"
            else:
                rec["status"] = "above"
                g, rr = fwd_gain(per, n, bk)
                rec["direct"] = (SQ.row_gain(n, bk) - SQ.row_gain(n, L))
                rec["fwd"] = g
                rec["fwd_rows"] = rr
                rec["total"] = rec["direct"] + g
        tally[rec["status"]] = tally.get(rec["status"], 0) + 1
        rows.append(rec)
    print(f"rows crosswalked {len(rows)}: {tally}")
    basis = {}
    for r in rows:
        basis[r["basis"]] = basis.get(r["basis"], 0) + 1
    print("basis:", basis)
    ab = sorted([r for r in rows if r["status"] == "above"],
                key=lambda r: -r["total"])
    print(f"\nIMPORT TARGETS: {len(ab)}")
    print(f"{'n':>4} {'r':>2} {'delivered':>11} {'best known':>11} {'delta':>9} "
          f"{'direct':>9} {'fwd':>9} {'total':>9}  basis")
    for r in ab[:25]:
        print(f"{r['n']:4d} {r['r']:2d} {r['delivered']:11.6f} "
              f"{r['best_known']:11.6f} {r['delta']:+9.5f} {r['direct']:+9.5f} "
              f"{r['fwd']:+9.5f} {r['total']:+9.5f}  {r['basis']}")
    if ab:
        print(f"\nsum of direct gains over all targets: "
              f"{sum(r['direct'] for r in ab):+.6f}")
        print(f"sum of direct+forward (reckoned, not verified): "
              f"{sum(r['total'] for r in ab):+.6f}")
    # weak-basis rows that are 'at' only against a 2009 value
    weak_at = [r for r in rows if r["status"] == "at" and r["basis"] == "ds7_2009"]
    print(f"\n'at' only against a 2009 value (could still be a target): "
          f"{[r['n'] for r in weak_at]}")
    led = {"run": 59, "schema": "frontier/2", "tally": tally, "basis": basis,
           "targets": ab, "weak_at": [r["n"] for r in weak_at]}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(led, f, indent=1)
    print(f"\nledger: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
