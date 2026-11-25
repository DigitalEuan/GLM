#!/usr/bin/env python3
r"""row_census.py — the row-keyed ledger: what can still move, and what cannot.

WHY THIS EXISTS.  Every instrument in this project answers a *family* question
("can this wheel beat this row") and writes its own ledger; nothing answers the
*table* question: of the 1000 rows, which ones can still hold score, by how much,
and which are already at a proved floor.  Without that table the 0.163635 gap to
the leader is an undifferentiated number, and the project keeps aiming at
whichever family was written down last (`19` §4.3, `21` §6, W4, W5).

WHAT IT COMPUTES, PER ROW.  Nothing is searched; this is arithmetic over the
delivered table plus bounds the project already holds:

    L        the delivered side                     SQ.extent
    grid     ceil(sqrt n)                           exact, isqrt
    gain     (grid - L) / sqrt n                    positive iff the row beats
    floor    max(area, Karakus)                     the strongest proved side
    head     (grid - floor)/sqrt n - gain           gain still reachable, at most
    closed   n = k^2  (area) or  n = k^2 - 1 (Karakus, exact at that endpoint)

`head` is an *upper* bound on what one row can still contribute, and it is the
only reason this file exists: a row whose `head` is 1e-5 cannot be part of a
0.163635 gap, no matter how the construction is arranged.  At a row that a
published bound closes, `head` is defined to be exactly **0** -- the floor is the
grid, so no gain is available there, and the raw formula would instead report
how far the row sits *above* the grid, which is not opportunity and must not be
summed.

THE ONE LEDGER (run 77).  The census is also where the other instruments are
stamped: if `workspace/push/frozen_opt.json` exists, every row it attempted
carries `certified_frozen` and the row gets one `status` word --

    closed         a published bound forbids any gain here
    opt@declared   the delivered side is the optimum of its own declaration at
                   frozen angles (run 77: every beat with n <= 324)
    beat-open      beats the grid, no certificate
    grid-open      does not beat the grid, no published bound closes it

and the census prints the gap accounting: the sum of the *best conceivable*
gains (zero-waste ceiling) against the recorded 0.163635 gap.  That sum is the
honest statement that no bound this project holds attributes the gap row by row
-- it is forty to a hundred times too large (run 77).

SCOPE OF THE BOUND, STATED.  The area floor is orientation-free.  The Karakus
bound (`seam_wheels.bound_karakus`, arXiv:2609.37410 Cor. 1.2) is used here as
`21` §7 uses it -- as a bound on s(n) for this project, where rotations are
allowed -- and it is exact at n = k^2 - 1.  If it were an axis-parallel-only
statement, the `closed` verdicts would be class-scoped; no delivered row
violates it (control 2), which is consistent with the orientation-free reading
but does not prove it.  That scope question is worth confirming against the
paper before any `closed` row is quoted as settled.

CONTROLS.
  1  the delivered table reproduces: 22.217428576, 554 beats, 446 grid rows;
  2  no delivered row violates the floor (a violation would mean the bound, not
     the row, is wrong) -- including every one of the 554 beats;
  3  the two endpoints are exercised: n = 15 (= 16-1) is closed by Karakus at
     exactly 4, n = 11 is open with head > 0;
  4  a closed row carries head exactly 0 and is never stamped certified (the
     floor is the grid, so a positive head would be an artefact);
  5  the gap accounting does *not* localise the gap: the conceivable total
     exceeds 0.163635, so no bound-derived attribution exists (a negative, and
     asserting it is how it stays visible).

READ-ONLY apart from `workspace/push/row_census.json`.

    python3 scripts/row_census.py             # census + write ledger
    python3 scripts/row_census.py --selftest   # controls only
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import seam_wheels as SW     # noqa: E402
import sqscore as SQ         # noqa: E402

ROOT = os.path.dirname(HERE)
LEDGER = os.path.join(ROOT, "workspace/push/row_census.json")
#: the frozen-angle certificate, if this worktree has run `frozen_opt`
CERT = os.path.join(ROOT, "workspace/push/frozen_opt.json")
#: the exact algebraic sides, if this worktree has run `exact_sides`
SIDES = os.path.join(ROOT, "workspace/push/exact_sides.json")
#: the recorded gap to the leader (doc 19); used here only as a scale
GAP = 0.163635
#: the catalogue the table was assembled against stops here (doc 08, W3)
FRONTIER = 324


def floor_side(n: int):
    """(strongest proved side, name).  Orientation-free; see the module note."""
    area = math.sqrt(n)
    kar = SW.bound_karakus(n)
    if kar is None or kar <= area:
        return area, "area"
    return kar, "karakus"


def closed_by_theorem(n: int) -> str | None:
    """Why this row cannot beat the grid, by a published bound alone."""
    k = math.isqrt(n)
    if k * k == n:
        return "square"           # area floor = k = grid
    if n >= 8 and SW.bound_karakus(n) is not None:
        if abs(SW.bound_karakus(n) - (k + 1)) < 1e-12:
            return "k^2-1"        # Karakus is exact here
    return None


def aligned(state) -> bool:
    """Axis-parallel in the table's own sense: every angle a multiple of pi/2."""
    return all(abs(math.sin(2.0 * float(t))) < 1e-9 for _, _, t in state)


def load_sides() -> dict[int, dict]:
    """The exact-side rows, keyed by n (empty if `exact_sides` has not run)."""
    if not os.path.exists(SIDES):
        return {}
    with open(SIDES) as f:
        return {r["n"]: r for r in json.load(f).get("rows", [])}


def row_record(n: int, state, cert=None, side=None) -> dict:
    L = SQ.extent(state)
    g = SQ.grid(n)
    gain = SQ.row_gain(n, L)
    fl, fname = floor_side(n)
    cl = closed_by_theorem(n)
    head = (g - fl) / math.sqrt(n) - gain
    if cl:
        # the floor *is* the grid: a published bound forbids any gain here
        head = 0.0
    rec = {"n": n, "L": L, "grid": g, "gain": gain,
           "aligned": aligned(state), "residue": n - math.isqrt(n) ** 2,
           "floor": fl, "floor_from": fname, "head": head,
           "closed": cl, "beat": gain > 0.0,
           "above_frontier": n > FRONTIER, "certified_frozen": cert}
    if side is not None:
        rec.update(side_class=side["mix"], exact=side["expressible"],
                   L_ideal=side.get("ideal"),
                   L_exact=side.get("expr"),
                   exact_residual=side.get("residual"),
                   exact_ok=side.get("residual_ok"))
    rec["status"] = status_of(rec)
    return rec


def status_of(r: dict) -> str:
    """The one word this row's remaining opportunity deserves (see the doc)."""
    if r["closed"]:
        return "closed"
    if r["certified_frozen"]:
        return "opt@declared"
    return "beat-open" if r["beat"] else "grid-open"


def ceiling_gain(n: int) -> float:
    """The best gain any packing at this row could have under the area bound."""
    return SQ.grid(n) / math.sqrt(n) - 1.0


def accounting(rows: list[dict]) -> dict:
    """How much score each group could conceivably still supply."""
    grid_open = [r for r in rows if not r["beat"] and not r["closed"]]
    beats = [r for r in rows if r["beat"]]
    s_grid = sum(ceiling_gain(r["n"]) for r in grid_open)
    s_beat = sum(ceiling_gain(r["n"]) - r["gain"] for r in beats)
    return {"grid_rows": s_grid, "beats": s_beat,
            "conceivable": s_grid + s_beat,
            "published_head": sum(r["head"] for r in rows if not r["closed"])}


def load_certificates() -> dict[int, dict]:
    """The frozen-angle certificate rows, keyed by n (empty if not run)."""
    if not os.path.exists(CERT):
        return {}
    with open(CERT) as f:
        cert = json.load(f)
    return {r["n"]: r for r in cert.get("rows", [])}


def selftest(per: dict) -> int:
    print("control 1 — the delivered table reproduces")
    s = SQ.guard(per)
    assert s["beats"] == 554 and s["grid"] == 446, s
    print(f"  score {s['score']:.9f}, {s['beats']} beats, {s['grid']} grid rows")

    print("control 2 — no delivered row violates its floor")
    worst = None
    for n in sorted(per):
        r = row_record(n, per[n])
        assert r["head"] >= -1e-12, (n, r["L"], r["floor"], r["floor_from"])
        if worst is None or r["head"] < worst["head"]:
            worst = r
    print(f"  tightest row against the bound: n={worst['n']} L={worst['L']:.9f} "
          f"floor={worst['floor']:.9f} ({worst['floor_from']}), head "
          f"{worst['head']:.3e}")

    print("control 3 — both endpoints are exercised")
    r15 = row_record(15, per[15])
    assert r15["closed"] == "k^2-1" and abs(r15["floor"] - 4.0) < 1e-12, r15
    r11 = row_record(11, per[11])
    assert r11["closed"] is None and r11["head"] > 0.0, r11
    print(f"  n=15: closed by Karakus at floor {r15['floor']:.9f} = grid "
          f"{r15['grid']}; n=11: open, head {r11['head']:.6f}")

    print("control 4 — a closed row carries head exactly 0 and no certificate")
    n_closed = 0
    cert = load_certificates()
    for n in sorted(per):
        r = row_record(n, per[n])
        if r["closed"]:
            n_closed += 1
            assert r["head"] == 0.0, (n, r["closed"], r["head"])
            assert cert.get(n, {}).get("certified") is not True, n
    assert n_closed == 60, n_closed
    print(f"  {n_closed} closed rows, all with head 0.0 and none certified "
          f"(the formula's raw value would have been positive)")

    print("control 5 — the bounds cannot attribute the gap")
    acc = accounting([row_record(n, per[n]) for n in sorted(per)])
    assert acc["conceivable"] > GAP, acc
    print(f"  conceivable gain {acc['conceivable']:.6f} against a gap of "
          f"{GAP:.6f}: {acc['conceivable'] / GAP:.0f}x too large to localise it")

    print("control 6 — the exact sides agree with the census")
    sides = load_sides()
    if not sides:
        print("  exact_sides.json absent: control skipped (run exact_sides.py)")
    else:
        axis = 0
        for n in sorted(per):
            s = sides.get(n)
            assert s is not None, n
            r = row_record(n, per[n], None, s)
            if r["side_class"] == "axis":
                axis += 1
                assert r["closed"] or r["L"] is not None, n
                assert str(math.isqrt(n) + (0 if math.isqrt(n) ** 2 == n else 1)) \
                    == str(s["ideal"]), (n, s["ideal"])
                assert r["exact_ok"], (n, s["residual"])
            if not s["expressible"]:
                assert s["angles"]["generic"] > 0, n
        print(f"  {len(sides)} rows stamped; all {axis} axis rows have ideal side "
              f"exactly ceil(sqrt n) and a residual within tolerance")
    print("selftest: OK")
    return 0


def census(per: dict, write: bool = True) -> int:
    SQ.guard(per, quiet=True)
    cert = load_certificates()
    sides = load_sides()
    rows = [row_record(n, per[n],
                       None if n not in cert else bool(cert[n]["certified"]),
                       sides.get(n)) for n in sorted(per)]
    beat = [r for r in rows if r["beat"]]
    grid = [r for r in rows if not r["beat"]]
    closed = [r for r in grid if r["closed"]]
    openq = [r for r in grid if not r["closed"]]
    open_hi = [r for r in openq if r["above_frontier"]]

    print(f"rows {len(rows)}: {len(beat)} beat the grid, {len(grid)} do not")
    print(f"  of the {len(grid)} grid rows, {len(closed)} cannot beat it by a "
          f"published bound (square or k^2-1); {len(openq)} are open, of which "
          f"{len(open_hi)} are above n = {FRONTIER} where no catalogue exists")

    print("\nresidues of the open grid rows (n - floor(sqrt n)^2):")
    hist: dict[int, list[int]] = {}
    for r in openq:
        hist.setdefault(r["residue"], []).append(r["n"])
    for m in sorted(hist):
        ns = hist[m]
        above = sum(1 for x in ns if x > FRONTIER)
        print(f"  m={m:2d}: {len(ns):3d} rows ({above:3d} above {FRONTIER}), "
              f"n = {ns[0]}..{ns[-1]}")

    tot = sum(r["head"] for r in openq)
    print(f"\nhead reachable over those {len(openq)} open grid rows: {tot:.6f} "
          f"(the whole gap is {GAP})")
    for th in (1e-1, 1e-2, 1e-3, 1e-4):
        k = [r for r in openq if r["head"] >= th]
        print(f"  rows with head >= {th:g}: {len(k):3d}, summing "
              f"{sum(r['head'] for r in k):.6f}")

    print("\nthe 15 open grid rows with the most head:")
    print(f"{'n':>5} {'res':>4} {'grid':>5} {'L':>10} {'head':>10} {'above?':>7}")
    for r in sorted(openq, key=lambda r: -r["head"])[:15]:
        print(f"{r['n']:5d} {r['residue']:4d} {r['grid']:5d} {r['L']:10.6f} "
              f"{r['head']:10.6f} {str(r['above_frontier']):>7}")

    print("\nbeating rows against their own floor (how far from optimal):")
    beat_sorted = sorted(beat, key=lambda r: -r["head"])
    for th in (1e-1, 1e-2, 1e-3):
        k = [r for r in beat_sorted if r["head"] >= th]
        print(f"  {len(k):3d} of {len(beat)} beats still have head >= {th:g} "
              f"(sum {sum(r['head'] for r in k):.6f})")

    acc = accounting(rows)
    states: dict[str, int] = {}
    for r in rows:
        states[r["status"]] = states.get(r["status"], 0) + 1
    if sides:
        mix: dict[str, int] = {}
        for r in rows:
            if r.get("side_class"):
                mix[r["side_class"]] = mix.get(r["side_class"], 0) + 1
        print("\nexact algebraic side (from exact_sides.json):")
        for k in ("axis", "45", "pyth", "45+pyth", "generic"):
            if k in mix:
                where = {"axis": "Q", "45": "Q(sqrt2)", "pyth": "Q",
                         "45+pyth": "Q(sqrt2)", "generic": "not expressible"}[k]
                print(f"  {k:9s} {mix[k]:4d}   L in {where}")
        bad = [r["n"] for r in rows if r.get("exact_ok") is False]
        print(f"  rows whose exact side has no ideal within the declared box: "
              f"{len(bad)}")

    print("\nrow status (the one ledger):")
    for k in ("closed", "opt@declared", "beat-open", "grid-open"):
        print(f"  {k:13s} {states.get(k, 0):4d}")
    if cert:
        print(f"  (stamped from frozen_opt.json: {len(cert)} rows attempted, "
              f"{sum(1 for v in cert.values() if v['certified'])} certified)")
    print(f"\ngap accounting, gap = {GAP}:")
    print(f"  zero-waste ceiling over open grid rows   {acc['grid_rows']:.6f}")
    print(f"  same over the 554 beats                  {acc['beats']:.6f}")
    print(f"  conceivable total                        "
          f"{acc['conceivable']:.6f}  ({acc['conceivable'] / GAP:.0f}x the gap)")
    print(f"  same total restricted to head            "
          f"{acc['published_head']:.6f}  "
          f"({acc['published_head'] / GAP:.0f}x the gap)")
    print("  => no bound held here attributes the gap row by row; see run 77.")

    out = {"note": "row-keyed ledger: gain, published floor, reachable head, "
                   "frozen-angle certificate stamp and status; no search",
           "frontier": FRONTIER,
           "gap": GAP,
           "summary": {"rows": len(rows), "beats": len(beat),
                       "grid": len(grid), "closed_by_bound": len(closed),
                       "open_grid": len(openq),
                       "open_grid_above_frontier": len(open_hi),
                       "head_open_grid": tot,
                       "status": states, "accounting": acc,
                       "side_class": {k: sum(1 for r in rows
                                             if r.get("side_class") == k)
                                      for k in ("axis", "45", "pyth",
                                                "45+pyth", "generic")},
                       "exact_over_box": [r["n"] for r in rows
                                          if r.get("exact_ok") is False]},
           "rows": rows}
    if write:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "w") as f:
            json.dump(out, f, indent=1)
        print(f"\nledger -> {os.path.relpath(LEDGER, ROOT)}")
    return 0


def main() -> int:
    per = SQ.load()
    if "--selftest" in sys.argv:
        return selftest(per)
    return census(per, write="--no-write" not in sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
