#!/usr/bin/env python3
r"""reconcile_table.py — audit table.json against submission.csv, and rewrite it cleanly.

Two things are wrong with `workspace/submission/table.json` as it stands:

  1. **its `L` is a model value.** For a row whose angles are the eight exact words, the
     snapped model and the true geometry agree; for the other 447 rows they do not, and the
     table *overstates* the row (n = 330: `18.692672` in the table, `18.692388` in the CSV).
     357 of the 1000 rows are stale by more than `1e-9`, the largest by `9.0e-2`.
  2. **that is where 22.645990612927686 comes from.** The repo's own formula
     `score = sum L/sqrt(n) - 1` over the *table's* L gives `22.645990612927686`; over the
     CSV's true sides it gives `22.217428576`, the delivered number. The gap is not a
     discrepancy in the scoring — it is the accumulated snapping error,
     `sum (L_table - L_true)/sqrt(n) = 0.427933668...`.

This module audits that, prints it, and (with `--write`) rewrites `table.json` so that `L` is
the *true* side measured at 40 decimal digits by `true_geom`, with the old value kept as
`L_model` and a `_meta` block recording both scores. Nothing here uses a float.

    python3 scripts/reconcile_table.py            # audit only, exits 1 if out of sync
    python3 scripts/reconcile_table.py --write    # rewrite table.json (L becomes the true side)
"""
from __future__ import annotations

import csv
import json
import os
import sys
from decimal import Decimal, localcontext

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import true_geom as TG              # noqa: E402

TABLE = os.path.join(ROOT, "workspace/submission/table.json")
META = os.path.join(ROOT, "workspace/submission/table.meta.json")
SUBMISSION = os.path.join(ROOT, "workspace/submission/submission.csv")
STALE = Decimal("1e-9")


def read_csv(path=SUBMISSION):
    """`n -> [(x, y, angle) as Decimal strings]`, in file order."""
    per = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            per.setdefault(int(r["n"]), []).append((r["x"], r["y"], r["angle"]))
    return per


def truth(per):
    """`n -> {'L': Decimal, 'rows': N}` from the CSV, at 40 digits."""
    return {n: {"L": TG.side(rows), "rows": len(rows)} for n, rows in per.items()}


def score(per_L):
    """`sum L/sqrt(n) - 1` in Decimal, over a map `n -> L`."""
    with localcontext() as ctx:
        ctx.prec = 40
        tot = Decimal(0)
        for n in sorted(per_L):
            tot += Decimal(per_L[n]) / Decimal(n).sqrt() - 1
        return tot


def audit(table=None, per=None):
    """The comparison: per-row staleness, both totals, and the gap between them."""
    table = json.load(open(TABLE)) if table is None else table
    per = read_csv() if per is None else per
    tr = truth(per)
    stale, big = [], []
    for n in sorted(tr):
        Lm = Decimal(str(table[str(n)]["L"]))
        Lt = tr[n]["L"]
        d = Lm - Lt
        if abs(d) > STALE:
            stale.append((n, Lm, Lt, d))
            if abs(d) > Decimal("1e-3"):
                big.append((n, Lm, Lt, d))
    s_model = score({n: Decimal(str(table[str(n)]["L"])) for n in tr})
    s_true = score({n: tr[n]["L"] for n in tr})
    return {"rows": len(tr), "stale": stale, "big": big,
            "score_model": s_model, "score_true": s_true, "gap": s_model - s_true,
            "truth": tr}


def write(table=None, per=None):
    """Rewrite `table.json`: `L` becomes the true side, `L_model` keeps the old one."""
    table = json.load(open(TABLE)) if table is None else table
    per = read_csv() if per is None else per
    rep = audit(table, per)
    out = {}
    for n in sorted(rep["truth"], key=int):
        key = str(n)
        rec = dict(table[key])
        old = rec.get("L")
        rec["L_model"] = old
        rec["L"] = str(+rep["truth"][n]["L"])
        out[key] = rec
    meta = {
        "note": "L is the true side of the row at 40 decimal digits (true_geom); L_model is the "
                "snapped-word value the earlier runs compared against. The repo score is "
                "sum L/sqrt(n) - 1 over these true sides.",
        "rows": rep["rows"], "score_true": str(+rep["score_true"]),
        "score_model": str(+rep["score_model"]), "gap": str(+rep["gap"]),
        "stale_rows_over_1e-9": len(rep["stale"]),
        "stale_rows_over_1e-3": len(rep["big"]),
        "generated_by": "scripts/reconcile_table.py --write",
    }
    with open(TABLE, "w") as f:
        json.dump(out, f, indent=1)          # integers only: every reader iterates these keys
    with open(META, "w") as f:
        json.dump(meta, f, indent=1)         # the provenance lives beside the table, not in it
    return rep


def selftest():
    """Two controls: the score identity, and that a stale row is caught."""
    with localcontext() as ctx:
        ctx.prec = 40
        # control 1 -- rational roots collapse: n = 1, 4, 9 with sides 1, 3, 5 give 7/6
        s = score({1: Decimal(1), 4: Decimal(3), 9: Decimal(5)})
        assert s == Decimal(7) / 6, s
        assert score({1: Decimal(1)}) == 0, "a unit square scores zero"
        # control 2 -- a row whose table L is 1e-4 above its true side is stale, and the gap
        # is charged at exactly dL/sqrt(n)
        per = {2: [("0", "0", "0"), ("1", "0", "0")]}
        tab = {"2": {"L": "2.0001", "state": [], "src": "test"}}
        rep = audit(tab, per)
        assert len(rep["stale"]) == 1 and rep["stale"][0][0] == 2, rep["stale"]
        assert abs(rep["gap"] - Decimal("0.0001") / Decimal(2).sqrt()) < Decimal("1e-38"), rep["gap"]
        assert rep["score_true"] == 2 / Decimal(2).sqrt() - 1, rep["score_true"]
    print("control 1 -- the score identity: sides 1, 3, 5 at n = 1, 4, 9 give exactly 7/6, and a "
          "lone unit square scores 0.")
    print("control 2 -- staleness: a table side 1e-4 above the true one is flagged, and the gap "
          "is exactly dL/sqrt(n), so the two totals differ only by accumulated model error.")
    print("reconcile_table: OK (2 controls)")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        selftest()
        return 0
    rep = audit()
    print(f"rows {rep['rows']}; stale (|L_table - L_true| > 1e-9): {len(rep['stale'])};"
          f" stale > 1e-3: {len(rep['big'])}")
    print(f"score over table L : {+rep['score_model']:.15f}")
    print(f"score over true  L : {+rep['score_true']:.15f}")
    print(f"gap                : {+rep['gap']:.15f}")
    for n, Lm, Lt, d in sorted(rep["big"], key=lambda r: -abs(r[3]))[:6]:
        print(f"  n={n:4d}  L_table={+Lm:.12f}  L_true={+Lt:.12f}  diff={+d:+.3e}")
    if "--write" in argv:
        rep = write()
        print(f"table.json rewritten: L = true side, L_model kept; {len(rep['stale'])} rows changed")
        return 0
    return 0 if not rep["stale"] else 1


if __name__ == "__main__":
    sys.exit(main())
