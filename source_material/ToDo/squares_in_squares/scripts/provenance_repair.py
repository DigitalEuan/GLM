#!/usr/bin/env python3
r"""provenance_repair.py — make submission.csv the single source of truth (run 160, D0).

What was wrong
--------------
`reconcile_table.py --write` rewrote every row's `L` to the true 40-digit side from
`submission.csv` but deliberately left `state` alone.  The result is a mixed table:
642 rows hold the delivered pose, 358 hold an older pose (for the ten bands
k = 21, 22, 24..31 it is the *unclosed k x k margin grid*, with one unit hole per
missing cell), and there is no field saying which.  Every instrument built on
`void_insert.load_pose()` — `void_insert.py`, `block_swap.py`, `resqueeze.py`,
`notch32.py`, `p1p_insert31.py` — therefore measured a pose that is not in the
submission for those rows.  The 0.9994–0.9999 "sliver" of run 75 is that unit
hole, not a property of the delivered pose (doc 115).

What this does
--------------
`--write` writes the CSV state into every `table.json` row, adds `state_src` and
`state_digest`, keeps `L`, `L_model` and `src`, and records the change in
`table.meta.json` plus a JSON ledger.  `--guard` re-reads both files and enforces:

  G1  every row has exactly n cells and `state_src == "submission.csv"`;
  G2  the state is the CSV state exactly (float equality on every coordinate);
  G3  `|true_geom.side(state) - L| <= 1e-9`, with L a Decimal;
  G4  `packlib.verify(state)` is ok: zero overlap at the project gate;
  G5  `sqscore.guard()` is unchanged (22.217428576..., 554 beats, 446 ties).

Nothing here decides a packing.  It is I/O and a gate: the state is copied, never
recomputed, and a row that fails G3/G4 refuses the whole write.

    python3 scripts/provenance_repair.py --selftest
    python3 scripts/provenance_repair.py --guard
    python3 scripts/provenance_repair.py --write
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from decimal import Decimal, localcontext

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import packlib as P                  # noqa: E402  (the project's SAT gate)
import sqscore as SQ                 # noqa: E402  (the one scorer)
import true_geom as TG               # noqa: E402  (40-digit Decimal side)

TABLE = os.path.join(ROOT, "workspace/submission/table.json")
META = os.path.join(ROOT, "workspace/submission/table.meta.json")
CSV = os.path.join(ROOT, "workspace/submission/submission.csv")
LEDGER = os.path.join(ROOT, "workspace/push/provenance_repair.json")
BACKUP = os.path.join(ROOT, "workspace/push/table_before_provenance.json")
TOL = Decimal("1e-9")


def read_csv(path=CSV):
    """n -> [(x, y, angle) as the CSV strings], in file order."""
    per = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            per.setdefault(int(row["n"]), []).append(
                (row["x"], row["y"], row["angle"]))
    return per


def csv_sha256(path=CSV):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def state_from_rows(rows):
    """The CSV strings as JSON numbers, preserving the delivered double exactly."""
    return [[float(x), float(y), float(a)] for x, y, a in rows]


def state_digest(state):
    raw = json.dumps(state, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(raw).hexdigest()


def truth(per):
    """n -> the 40-digit true side of the CSV row."""
    return {n: TG.side(rows) for n, rows in per.items()}


def compare(table, per):
    """All rows where the table state is not the CSV state (float equality)."""
    bad = []
    for n in sorted(per):
        st = table.get(str(n), {}).get("state", [])
        csvst = state_from_rows(per[n])
        if len(st) != len(csvst):
            bad.append((n, "count", len(st), len(csvst)))
            continue
        for j, (a, b) in enumerate(zip(st, csvst)):
            if any(float(a[k]) != b[k] for k in range(3)):
                bad.append((n, "coords", j))
                break
    return bad


def compare_L(table, per):
    """All rows where the table L is not the CSV true side (40-digit Decimal)."""
    bad = []
    for n, Lt in truth(per).items():
        old = Decimal(str(table[str(n)]["L"]))
        if abs(old - Lt) > TOL:
            bad.append((n, old, Lt))
    return bad


def guard(table=None, per=None, quiet=False):
    """G1-G5.  Returns a report; raises AssertionError on failure."""
    table = json.load(open(TABLE)) if table is None else table
    per = read_csv() if per is None else per
    true_L = truth(per)
    problems = []
    if len(table) != 1000 or set(table) != {str(n) for n in range(1, 1001)}:
        problems.append(f"table keys: {len(table)}, expected 1000 rows 1..1000")
    worst_side = Decimal(0)
    worst_overlap = -1e99
    for n in sorted(per):
        rec = table.get(str(n))
        if rec is None:
            problems.append(f"n={n}: no table row")
            continue
        st = rec.get("state", [])
        if len(st) != n:
            problems.append(f"n={n}: {len(st)} cells, expected {n}")
            continue
        if rec.get("state_src") != "submission.csv":
            problems.append(f"n={n}: state_src={rec.get('state_src')!r}")
        csvst = state_from_rows(per[n])
        if any(float(st[j][k]) != csvst[j][k] for j in range(n) for k in range(3)):
            problems.append(f"n={n}: state is not the CSV state")
        with localcontext() as ctx:
            ctx.prec = 40
            d = abs(TG.side([(str(float(x)), str(float(y)), str(float(a)))
                             for x, y, a in st]) - true_L[n])
        worst_side = max(worst_side, d)
        if d > TOL:
            problems.append(f"n={n}: |extent-L|={d}")
        v = P.verify(st)
        worst_overlap = max(worst_overlap, v["worst_pen"])
        if not v["ok"]:
            problems.append(f"n={n}: packlib overlap {v['worst_pen']:.3e}")
    s = SQ.guard(quiet=True)
    if abs(s["score"] - SQ.DELIVERED_SCORE) > SQ.TOL or s["beats"] != SQ.DELIVERED_BEATS:
        problems.append(f"sqscore changed: {s['score']} / {s['beats']}")
    rep = {"rows": len(table), "problems": problems,
           "worst_side_error": str(worst_side), "worst_overlap": worst_overlap,
           "score": str(s["score"]), "beats": s["beats"], "grid": s["grid"],
           "csv_sha256": csv_sha256()}
    if problems:
        raise AssertionError("provenance guard failed:\n  " + "\n  ".join(problems[:20]))
    if not quiet:
        print(f"[provenance] guard OK: {rep['rows']} rows, "
              f"worst |extent-L| {worst_side:.3e}, worst overlap {worst_overlap:.3e}, "
              f"score {s['score']:.9f}, {s['beats']} beats")
    return rep


def write():
    """Copy the CSV state into every table row; keep L, L_model and src."""
    per = read_csv()
    table = json.load(open(TABLE))
    before = compare(table, per)
    # refuse to write until the *target* passes the geometry gate
    true_L = truth(per)
    l_before = compare_L(table, per)
    trial = {}
    for n in sorted(per):
        rec = dict(table[str(n)])
        old_L = Decimal(str(rec["L"]))
        if abs(old_L - true_L[n]) > TOL:
            rec["L_before_provenance"] = str(old_L)
        rec["L"] = str(+true_L[n])
        rec["state"] = state_from_rows(per[n])
        rec["state_src"] = "submission.csv"
        rec["state_digest"] = state_digest(rec["state"])
        trial[str(n)] = rec
    guard(trial, per, quiet=True)
    if os.path.exists(TABLE):
        open(BACKUP, "wb").write(open(TABLE, "rb").read())
    for key in trial:
        table[key] = trial[key]
    with open(TABLE, "w") as f:
        json.dump(table, f, indent=1)

    meta = {}
    if os.path.exists(META):
        meta = json.load(open(META))
    meta.update({
        "state_src": "submission.csv",
        "state_rows_replaced": len(before),
        "L_rows_replaced": len(l_before),
        "state_guard": "extent<=1e-9, packlib 0 overlap, sqscore unchanged",
        "csv_sha256": csv_sha256(),
        "generated_by": "scripts/provenance_repair.py --write",
    })
    with open(META, "w") as f:
        json.dump(meta, f, indent=1)

    rep = guard(table, per, quiet=True)
    rep["changed_rows"] = len(before)
    rep["changed_L_rows"] = [{"n": n, "L_old": str(o), "L_csv": str(t)}
                            for n, o, t in l_before]
    rep["changed_by_kind"] = {}
    for n, kind, *_ in before:
        rep["changed_by_kind"][kind] = rep["changed_by_kind"].get(kind, 0) + 1
    rep["backup"] = os.path.relpath(BACKUP, ROOT)
    with open(LEDGER, "w") as f:
        json.dump(rep, f, indent=1)
    print(f"[provenance] wrote {len(before)} states and {len(l_before)} L values "
          f"from submission.csv; backup {rep['backup']}; ledger {os.path.relpath(LEDGER, ROOT)}")
    print(f"[provenance] guard OK: {rep['rows']} rows, worst |extent-L| "
          f"{Decimal(rep['worst_side_error']):.3e}, worst overlap {rep['worst_overlap']:.3e}")
    return rep


def selftest():
    """Four controls: stale detection, extent identity, overlap refusal, score guard."""
    per = {1: [("0.500000001", "0.500000001", "0")]}
    fresh = {"1": {"L": "1.000000002", "state": [[0.500000001, 0.500000001, 0.0]],
                   "state_src": "submission.csv"}}
    assert compare(fresh, per) == []
    stale = {"1": {"L": "1.000000002", "state": [[0.5, 0.5, 0.0]],
                   "state_src": "submission.csv"}}
    assert len(compare(stale, per)) == 1
    # extent of the CSV row is the true side: the unit square at 0.500000001 has side 1
    d = abs(TG.side([("0.500000001", "0.500000001", "0")]) - Decimal("1"))
    assert d == 0, d
    # a planted overlap is caught by the project gate
    v = P.verify([(0.5, 0.5, 0.0), (0.5, 0.5, 0.0)])
    assert not v["ok"] and v["worst_pen"] > 0, v
    # the delivered scorer still holds (this is the real 1000-row CSV, not the toy)
    s = SQ.guard(quiet=True)
    assert s["beats"] == 554 and abs(s["score"] - SQ.DELIVERED_SCORE) <= SQ.TOL, s
    print("provenance_repair selftest: 4 controls OK (stale detection, extent identity, "
          "planted overlap refused, sqscore guard)")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        selftest()
        return 0
    if "--write" in argv:
        write()
        return 0
    if "--guard" in argv:
        guard()
        return 0
    rep = compare(json.load(open(TABLE)), read_csv())
    print(f"[provenance] {len(rep)} rows differ from submission.csv "
          f"(run with --write to repair, --guard to enforce)")
    return 0 if not rep else 1


if __name__ == "__main__":
    sys.exit(main())
