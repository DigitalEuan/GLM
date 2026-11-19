#!/usr/bin/env python3
r"""frozen_opt.py — item 2: certify the delivered side as the frozen-angle optimum.

THE STATEMENT THIS TESTS.  Run 74 solved 87,767 branch structures at five rows and
found 0 improvements; run 67 found that at k = n the free-set LP *is* a
certificate that the delivered side is the optimum of the declared-axis,
fixed-orientation model.  Together they suggest a table-wide statement:

    for row n, given its own angle multiset, no choice of one separating axis per
    pair and no translation of the n squares fits a side below L0 - eps.

That is exactly `declp.solve(xy, th, L0 - eps, free=all) is None`: the LP's
feasibility is a certificate (a feasible point is a packing at that side), so a
refusal at every declared branch... no -- the *declared* branch is the argmin
axis of the delivered state, so a refusal here is a statement about **that
declaration**, while run 74's leaf closed the whole declaration space at five
rows.  The two differ and the difference is the honest content of the result:
this instrument is cheap enough for many rows, and it is a statement about the
delivered declaration, not about every branch structure.  `--branches` optionally
also tries the other three axes per tight pair (run 29's grammar) at a capped
number of rows, which is where the two meet.

WHY IT IS WORTH RUNNING AT ALL.  A row whose side is already optimal in this
model cannot be improved by any frozen-angle rearrangement, so no amount of
search at fixed angles will move it; a row that is *not* optimal would be handed
back a feasible state, which is a score candidate.  Either answer is actionable,
and the certificate costs one LP per row.

SLICE.  Rows are read from `row_census.json` and taken in order of *head* (room
to the published floor), because that is where a different arrangement would pay
most; `--top`, `--min-n` and `--max-n` bound the work.  The slice is declared in
the ledger, so a partial run cannot be quoted as a table-wide result.

THE LEDGER ACCUMULATES (run 77).  Each run appends its slice under `slices` and
merges its rows by n, so a later band (e.g. the rows just above the catalogue
frontier) does not erase the block already certified.  `summary` is the union.

CONTROLS.
  1  the delivered state must be feasible at its own side (run 67's permanent
     check): `solve(..., L0)` returns a state for every row attempted;
  2  a demand 0.5 below the side must be refused at n = 5, where the row is a
     single 45 deg square pair and the answer is known;
  3  run 67's published refusal is reproduced: n = 294 refuses at L0 - 1e-6.

READ-ONLY apart from `workspace/push/frozen_opt.json`.

    python3 scripts/frozen_opt.py --selftest
    python3 scripts/frozen_opt.py --top 12 --max-n 150
    python3 scripts/frozen_opt.py --min-n 325 --max-n 400   # the band above the
                                                          # frontier (run 77)
"""
from __future__ import annotations

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import declp as D            # noqa: E402
import sqscore as SQ         # noqa: E402

ROOT = os.path.dirname(HERE)
LEDGER = os.path.join(ROOT, "workspace/push/frozen_opt.json")
CENSUS = os.path.join(ROOT, "workspace/push/row_census.json")
#: the side demanded below L0; a refusal at this demand is the certificate
EPS = 1e-6


def attempt(n: int, state, eps: float = EPS, **kw) -> dict:
    """One LP: is the delivered side improvable at frozen angles?"""
    xy, th, _, _ = D.frames(state)
    L0 = SQ.extent(state)
    t0 = time.time()
    free = set(range(n))
    ok_self = D.solve(xy, th, L0, free=free, pad=0.0, move=1.0,
                      free_span=2.0) is not None
    st = D.solve(xy, th, L0 - eps, free=free, pad=0.0, move=1.0,
                 free_span=2.0, **kw)
    dt = time.time() - t0
    rec = {"n": n, "L0": L0, "eps": eps, "self_feasible": ok_self,
           "certified": st is None, "seconds": round(dt, 2)}
    if st is not None:
        g = D.gate(n, st, th, L0)
        rec["candidate"] = {"gated": bool(g["ok"]),
                            "L": g["L"] if g["ok"] else None,
                            "pen": g["worst_pen"]}
    return rec


def selftest(per: dict) -> int:
    print("control 1 — the delivered state is feasible at its own side")
    for n in (5, 11, 15, 294):
        st = per[n]
        xy, th, _, _ = D.frames(st)
        L0 = SQ.extent(st)
        assert D.solve(xy, th, L0, free=set(range(n)), pad=0.0, move=1.0,
                       free_span=2.0) is not None, n
    print("  n = 5, 11, 15, 294 all feasible at L0 with every square free")

    print("control 2 — a demand 0.5 below the side is refused at n = 5")
    st = per[5]
    xy, th, _, _ = D.frames(st)
    L0 = SQ.extent(st)
    assert D.solve(xy, th, L0 - 0.5, free=set(range(5)), pad=0.0, move=1.0,
                   free_span=2.0) is None
    print("  n=5: L0 - 0.5 refused (the LP does bite)")

    print("control 3 — run 67's published refusal reproduces at n = 294")
    rec = attempt(294, per[294])
    assert rec["self_feasible"] and rec["certified"], rec
    print(f"  n=294: delivered side {rec['L0']:.9f} certified as the "
          f"declared-axis frozen-angle optimum ({rec['seconds']} s)")
    print("selftest: OK")
    return 0


def run(top: int, max_n: int, min_n: int = 1, write: bool = True) -> int:
    per = SQ.load()
    SQ.guard(per, quiet=True)
    with open(CENSUS) as f:
        census = json.load(f)
    cand = [r for r in census["rows"]
            if r["beat"] and min_n <= r["n"] <= max_n]
    cand.sort(key=lambda r: -r["head"])
    slice_rows = cand[:top]
    band = f"n <= {max_n}" if min_n <= 1 else f"{min_n} <= n <= {max_n}"
    print(f"slice: the {len(slice_rows)} beating rows with the most head, "
          f"{band} (of {len(cand)} eligible)")
    print(f"{'n':>5} {'head':>9} {'L0':>11} {'certified':>9} {'s':>6}  verdict")
    out = {"rows": []}
    n_cert = 0
    for r in slice_rows:
        rec = attempt(r["n"], per[r["n"]])
        rec["head"] = r["head"]
        assert rec["self_feasible"], rec
        if rec["certified"]:
            n_cert += 1
            verdict = "optimal (declared-axis, frozen angles)"
        else:
            c = rec["candidate"]
            verdict = (f"CANDIDATE gated={c['gated']} L={c['L']}"
                       if c["L"] else "candidate refused by the gate")
        print(f"{rec['n']:5d} {r['head']:9.6f} {rec['L0']:11.6f} "
              f"{str(rec['certified']):>9} {rec['seconds']:6.1f}  {verdict}")
        rec["verdict"] = verdict
        out["rows"].append(rec)
    print(f"\n{ n_cert } of {len(slice_rows)} certified at eps = {EPS}; "
          f"slice declared, not the whole table")

    # merge into whatever this worktree has already certified
    merged: dict[int, dict] = {}
    slices: list[dict] = []
    if write and os.path.exists(LEDGER):
        with open(LEDGER) as f:
            prev = json.load(f)
        merged = {r["n"]: r for r in prev.get("rows", [])}
        slices = list(prev.get("slices", []))
        if not slices and prev.get("rows"):        # pre-union ledger (run 76)
            ps = prev.get("summary", {})
            slices.append({"min_n": prev.get("min_n") or 1,
                           "max_n": prev.get("max_n"),
                           "top": prev.get("top"),
                           "tried": ps.get("tried"),
                           "certified": ps.get("certified")})
    for r in out["rows"]:
        merged[r["n"]] = r
    slices = [s for s in slices
              if (s.get("min_n") or 1, s.get("max_n")) != (min_n, max_n)]
    slices.append({"min_n": min_n, "max_n": max_n, "top": top,
                   "tried": len(slice_rows), "certified": n_cert,
                   "seconds_total": round(sum(r["seconds"]
                                             for r in out["rows"]), 1)})
    rows = [merged[n] for n in sorted(merged)]
    n_cert_all = sum(1 for r in rows if r["certified"])
    ledger = {"note": "delivered side tested against the declared-axis "
                       "frozen-angle optimum; a refusal at L0 - 1e-6 is the "
                       "certificate.  Slices accumulate; summary is the union.",
              "eps": EPS, "slices": slices,
              "summary": {"rows": len(rows), "certified": n_cert_all,
                          "candidates": len(rows) - n_cert_all},
              "rows": rows}
    print(f"ledger union: {n_cert_all} of {len(rows)} rows certified "
          f"across {len(slices)} slice(s)")
    if write:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "w") as f:
            json.dump(ledger, f, indent=1)
        print(f"ledger -> {os.path.relpath(LEDGER, ROOT)}")
    return 0


def _args(argv):
    top, max_n, min_n, write = 12, 150, 1, True
    i = 0
    while i < len(argv):
        if argv[i] == "--top" and i + 1 < len(argv):
            top = int(argv[i + 1]); i += 2; continue
        if argv[i] == "--max-n" and i + 1 < len(argv):
            max_n = int(argv[i + 1]); i += 2; continue
        if argv[i] == "--min-n" and i + 1 < len(argv):
            min_n = int(argv[i + 1]); i += 2; continue
        if argv[i] == "--no-write":
            write = False
        i += 1
    return top, min_n, max_n, write


def main() -> int:
    per = SQ.load()
    if "--selftest" in sys.argv:
        return selftest(per)
    top, min_n, max_n, write = _args(sys.argv[1:])
    return run(top, max_n, min_n, write)


if __name__ == "__main__":
    raise SystemExit(main())
