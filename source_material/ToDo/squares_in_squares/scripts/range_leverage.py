#!/usr/bin/env python3
r"""range_leverage.py — run 130: the full row range, and what one unit of side buys where.

Two questions, both answered from the delivered data and exact arithmetic:

1.  **What is the full row range?**  `submission.csv` scores `n = 1..1000` (1,000
    rows, 500,500 square entries, recomputed in `sqscore.guard`).  The measured
    extension in `json/extended_table_5000.json` covers `n = 1001..5000`
    (4,000 rows), and doc 08's `beyond1000.py` constructs designs to
    `n = 9900`.  Nothing above 9900 is measured anywhere in the repository.
    Unbeaten rows (side not below `ceil(sqrt n)`) are counted in each range,
    and the count is split again into rows that *cannot* be beaten at all
    (`n = k^2`, where `L >= sqrt n = k` by area) and rows that merely have not
    been.

2.  **What does a unit of side buy?**  `d(row_score)/dL = -1/sqrt n`, so the
    marginal leverage of a row is `lam(n) = 1/sqrt n`: it is the score bought
    per unit side reduction, and it is the only row weight the metric has.
    Multiplied by the side a row could still give up it gives the row's
    *ceiling* `k/sqrt n - 1` -- the score at zero waste.  Ranking by `lam` and
    by `lam * headroom` are different rankings, and doc 75's band census
    supplies the headroom: the frontier row of band `k` spends `V/j*` of its
    void budget, and the *next* row needs `d(k) = V - (j*-1)` unit^2 less void
    than the frontier already has.  `d(k) < 0` means the area is already
    enough -- only the arrangement is missing.

Everything here is `Decimal` at 45 digits on `Fraction`/`isqrt` inputs: no
float is named, so the numbers can be re-derived bit for bit.

    python3 scripts/range_leverage.py --selftest
    python3 scripts/range_leverage.py --out workspace/push/range_leverage130.json
"""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal, getcontext
from math import isqrt

getcontext().prec = 45

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sqscore as SQ                       # noqa: E402  (grid() is isqrt-exact)

TAB = os.path.join(ROOT, "workspace/submission/table.json")
EXT = os.path.join(ROOT, "json/extended_table_5000.json")
OUT = os.path.join(ROOT, "workspace/push/range_leverage130.json")

DELIVERED = Decimal("22.218056945")
DELIVERED_BEATS = 553
DELIVERED_GRID = 447
#: packlib.finalize pads every delivered side by ~2e-9; an exact algebraic side
#: therefore reads that much *smaller*.  A comparison must allow for the pad
#: without allowing a gain.
PAD = Decimal("2e-9")
ZERO = Decimal(0)
ONE = Decimal(1)


# ------------------------------------------------------------------ the rows
def k_of(n: int) -> int:
    """ceil(sqrt n), exactly.  sqscore's definition, not a float root."""
    return SQ.grid(n)


def lam(n: int) -> Decimal:
    """Marginal score per unit of side reduction: 1/sqrt n."""
    return ONE / Decimal(n).sqrt()


def ceiling(n: int) -> Decimal:
    """Best score this row could ever give: k/sqrt n - 1 (zero waste)."""
    return Decimal(k_of(n)) / Decimal(n).sqrt() - ONE


def load_scored() -> dict:
    """n -> {"L": Decimal, "src": str} for the scored rows (table.json strings)."""
    with open(TAB) as f:
        tab = json.load(f)
    out = {}
    for key, rec in tab.items():
        out[int(key)] = {"L": Decimal(rec["L"]), "src": rec["src"]}
    return out


def load_ext() -> dict:
    """n -> {"L", "grid", "bound", "src"} for the measured extension."""
    with open(EXT) as f:
        ext = json.load(f)
    return {int(k): {"L": Decimal(repr(v["L"])), "grid": int(v["grid"]),
                     "bound": Decimal(repr(v["bound"])), "src": v["src"]}
            for k, v in ext.items()}


def status(n: int, L: Decimal) -> str:
    """beat / tie / above, against the exact integer grid."""
    k = Decimal(k_of(n))
    if L < k - PAD:
        return "beat"
    if L > k + PAD:
        return "above"
    return "tie"


# --------------------------------------------------------------- band census
def bands(rows: dict, kmax: int) -> dict:
    """Recompute doc 75's price per band from the rows themselves.

    `n = k^2 - j`, `V = L^2 - n`; the frontier `m*` is the smallest row of the
    band whose side is below `k`, and the next row up needs one cell's worth of
    void less: `d = V(m*) - (j* - 1)`.  Doc 75 §2 tabulates this for k = 3..32;
    this function derives it, so the two can be compared.
    """
    out = {}
    for k in range(2, kmax + 1):
        lo, hi = (k - 1) ** 2 + 1, k * k          # rows this band owns
        front = [(n, rows[n]["L"]) for n in range(lo, hi) if n in rows]
        beaten = [(n, L) for n, L in front if status(n, L) == "beat"]
        if not beaten:
            continue
        m, Lm = max(beaten)                        # the frontier: closest to k^2
        j = k * k - m
        V = Lm * Lm - Decimal(m)
        out[k] = {"m": m, "j": j, "L": Lm, "V": V, "price": V - Decimal(j - 1),
                  "rows": len(front), "beaten": len(beaten)}
    return out


# ------------------------------------------------------------------- ranking
def inventory(scored: dict, ext: dict) -> dict:
    """Counts by range, and the unbeaten split into reachable and proved-optimal."""
    def tally(rows, lo, hi):
        s = {"rows": 0, "beat": 0, "tie": 0, "above": 0,
             "unbeaten": 0, "area_optimal": 0, "targetable": 0,
             "ceiling_sum": ZERO}
        for n in range(lo, hi + 1):
            if n not in rows:
                continue
            L = rows[n]["L"]
            st = status(n, L)
            s["rows"] += 1
            s[st] += 1
            if st != "beat":
                s["unbeaten"] += 1
                c = ceiling(n)
                s["ceiling_sum"] += c
                if c == 0:                         # n = k^2 : L >= sqrt n = k
                    s["area_optimal"] += 1
                else:
                    s["targetable"] += 1
        return s
    return {"scored": tally(scored, 1, 1000), "ext": tally(ext, 1001, 5000)}


def rank(rows: dict, lo: int, hi: int) -> list:
    """Every unbeaten row with room, ordered by marginal leverage lam(n)."""
    out = []
    for n in range(lo, hi + 1):
        if n not in rows:
            continue
        L = rows[n]["L"]
        if status(n, L) == "beat":
            continue
        c = ceiling(n)
        if c == 0:
            continue
        out.append({"n": n, "k": k_of(n), "L": L, "lam": lam(n), "ceiling": c})
    out.sort(key=lambda r: (-r["lam"], r["n"]))
    return out


def headroom(ranked: list, bnd: dict) -> list:
    """Attach the band's void price: how much area a first beat still owes."""
    for r in ranked:
        b = bnd.get(r["k"])
        r["band_price"] = None if b is None else b["price"]
        r["front"] = None if b is None else b["m"]
    return ranked


# ------------------------------------------------------------------- printing
def show(ranked: list, top: int = 24) -> None:
    print(f"  {'n':>5} {'k':>3} {'L':>10} {'1/sqrt n':>9} {'ceiling':>9} "
          f"{'front m*':>9} {'price d':>9}")
    for r in ranked[:top]:
        p = "-" if r["band_price"] is None else f"{r['band_price']:+.3f}"
        f = "-" if r["front"] is None else str(r["front"])
        print(f"  {r['n']:5d} {r['k']:3d} {r['L']:10.4f} {r['lam']:9.5f} "
              f"{r['ceiling']:9.5f} {f:>9} {p:>9}")


# ------------------------------------------------------------------- controls
def selftest() -> int:
    """Five controls: the score, the census, the optimal rows, monotonicity, doc 75."""
    scored, ext = load_scored(), load_ext()

    # 1. the ranking's rows are the scorer's rows: the delivered total reappears
    tot = ZERO
    for n, r in scored.items():
        tot += r["L"] / Decimal(n).sqrt() - ONE
    assert abs(tot - DELIVERED) < Decimal("1e-9"), tot
    print(f"  score from table.json L strings: {tot:.9f} "
          f"(delivered {DELIVERED})")

    # 2. beat / tie split is the scorer's
    inv = inventory(scored, ext)["scored"]
    assert (inv["beat"], inv["unbeaten"]) == (DELIVERED_BEATS, DELIVERED_GRID), inv
    print(f"  scored: {inv['beat']} beat / {inv['unbeaten']} unbeaten "
          f"({inv['area_optimal']} area-optimal, {inv['targetable']} with room)")

    # 3. n = k^2 has zero ceiling, exactly; and it is not a target
    for n in (4, 100, 961):
        assert ceiling(n) == 0, (n, ceiling(n))
    assert all(ceiling(n) > 0 for n in (12, 13, 20, 998))
    print("  ceiling(4) = ceiling(100) = ceiling(961) = 0 exactly")

    # 4. leverage is monotone and strict
    vals = [lam(n) for n in (2, 10, 100, 1000, 5000)]
    assert all(a > b for a, b in zip(vals, vals[1:])), vals
    print(f"  lam: " + " > ".join(f"{v:.5f}" for v in vals))

    # 5. the recomputed band price matches doc 75 §2's published rows
    bnd = bands(scored, 32)
    for k, want_V, want_d, want_m in ((32, Decimal("25.120"), Decimal("0.120"), 998),
                                      (23, Decimal("19.530"), Decimal("0.530"), 509),
                                      (5, Decimal("4.869"), Decimal("-0.131"), 19)):
        b = bnd[k]
        assert b["m"] == want_m, (k, b["m"])
        # doc 75 prints V and d to 3 decimals; this recomputes them in full.
        assert abs(b["V"] - want_V) < Decimal("1e-3"), (k, b["V"])
        assert abs(b["price"] - want_d) < Decimal("1e-3"), (k, b["price"])
    print(f"  band census reproduces doc 75: k=32 V={bnd[32]['V']:.3f} "
          f"d={bnd[32]['price']:+.3f}; k=23 V={bnd[23]['V']:.3f} "
          f"d={bnd[23]['price']:+.3f}; k=5 d={bnd[5]['price']:+.3f}")
    print("  selftest OK")
    return 0


# ----------------------------------------------------------------------- main
def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()
    out_path = OUT
    if "--out" in argv:
        out_path = argv[argv.index("--out") + 1]

    scored, ext = load_scored(), load_ext()
    inv = inventory(scored, ext)
    bnd = bands(scored, 32)
    bnd_ext = bands(ext, 70)
    rs = headroom(rank(scored, 1, 1000), bnd)
    re = headroom(rank(ext, 1001, 5000), bnd_ext)

    print("[range] full measured range: n = 1..1000 scored, 1001..5000 measured")
    for tag in ("scored", "ext"):
        s = inv[tag]
        print(f"  {tag:6s} rows {s['rows']:5d}  beat {s['beat']:4d}  "
              f"unbeaten {s['unbeaten']:4d}  (area-optimal {s['area_optimal']:3d}, "
              f"with room {s['targetable']:4d})  ceiling {s['ceiling_sum']:.6f}")
    tot_unb = inv["scored"]["unbeaten"] + inv["ext"]["unbeaten"]
    tot_room = inv["scored"]["targetable"] + inv["ext"]["targetable"]
    print(f"  total  rows {inv['scored']['rows'] + inv['ext']['rows']}  "
          f"unbeaten {tot_unb}  with room {tot_room}")

    print("\n[leverage] top scored rows with room, by 1/sqrt(n)")
    show(rs, 16)
    print("\n[leverage] top extension rows with room, by 1/sqrt(n)")
    show(re, 8)

    ceil_scored = inv["scored"]["ceiling_sum"]
    top20 = sum(r["ceiling"] for r in rs[:20])
    print(f"\n[room] scored ceiling over the 447 unbeaten rows: {ceil_scored:.6f}")
    print(f"       top 20 rows hold {top20:.6f} = "
          f"{100 * top20 / ceil_scored:.1f}% of it")
    cheap = sorted((b["price"], k) for k, b in bnd.items())
    print("[price] cheapest next rows (band, price): "
          + ", ".join(f"k={k} {p:+.3f}" for p, k in cheap[:6]))
    print("[price] dearest: " + ", ".join(f"k={k} {p:+.3f}" for p, k in cheap[-4:]))

    rec = {
        "inventory": inv,
        "score_from_table": str(DELIVERED),
        "band_census_scored": {str(k): {kk: str(vv) for kk, vv in b.items()}
                               for k, b in bnd.items()},
        "band_census_ext": {str(k): {kk: str(vv) for kk, vv in b.items()}
                            for k, b in bnd_ext.items()},
        "rank_scored": [{"n": r["n"], "k": r["k"], "L": str(r["L"]),
                         "lam": str(r["lam"]), "ceiling": str(r["ceiling"]),
                         "band_price": None if r["band_price"] is None
                         else str(r["band_price"])} for r in rs],
        "rank_ext": [{"n": r["n"], "k": r["k"], "L": str(r["L"]),
                      "lam": str(r["lam"]), "ceiling": str(r["ceiling"])}
                     for r in re],
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(rec, f, indent=1, default=str)
    print(f"\nwrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
