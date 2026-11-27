#!/usr/bin/env python3
r"""target_audit.py — where the score actually is, row by row, against the catalogue and the bounds.

WHY THIS EXISTS.  Runs 154-158 spent their budget on `n = 117..222` because `rank_targets` called every
`r = k^2 - n` row with `r >= 3` a target.  Two of those families are now settled at exactly `k`
(`s(k^2 - 3) = k` and `s(k^2 - 4) = k`, Daniel 2026, Lean-checked; the catalogue records `n = 118` as
*proved*), so the ten-row list could never have produced a promotion at any budget.  The same is true of
the other family rows: `r = 0` is the area floor, `r = 1, 2` is Nagamochi 2005.

This file answers the only question a run should start with: *which rows can still move, and what is each
one worth?*  Three classes, each decided from data rather than from habit:

  import      the catalogue's verified upper bound is **below** our delivered side.  A certified pose
              exists for it, so the row is a score gain with no search at all (C1-C2 by construction,
              provided our own verifier replays it).
  open tie    we deliver the grid side `k`, the row is not proved optimal, and the catalogue's best
              known is also `k`.  Beating it is a *new* result, so these are the record targets.
  locked      `r <= 4` (proved/reported at `k`), or a catalogue case marked `proved`.  Never target.

The score is `sum over n of (L/sqrt n - 1)` (`sqscore.py`), so every gain is `delta_L / sqrt n`: a row's
worth is its *side reduction over its own sqrt n*, not the size of the grid it sits on.  That is why the
biggest single items are the small-`k` ties (n = 20 is worth `0.118` of score if it could reach `sqrt 20`)
and why a 0.01 polish on a beaten row is worth ~`1e-3` at `n = 100` but only ~`3e-4` at `n = 1000`.

USAGE
    python3 scripts/target_audit.py                 # the report
    python3 scripts/target_audit.py --json PATH     # also write the machine-readable version
"""
from __future__ import annotations

import json
import math
import os
import sys
from decimal import Decimal, getcontext

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import true_geom as TG

getcontext().prec = 40

SUBMISSION = os.path.join(ROOT, "workspace/submission/submission.csv")
CATALOGUE = os.path.join(ROOT, "workspace/catalogue/frontier.json")
REPORT = os.path.join(ROOT, "workspace/push/target_audit.json")

#: families whose side is exactly `k`, so a row with that `r` can never be promoted.
#: r = 0 is the area floor; r = 1, 2 Nagamochi 2005; r = 3 Daniel 2026 (catalogue `n = 118` proved);
#: r = 4 Daniel 2026 (reported, `ValidTilt9` reported independently by Hosono; catalogue `n = 117` open).
LOCKED_R = {0: "area floor", 1: "Nagamochi 2005", 2: "Nagamochi 2005",
            3: "Daniel 2026 (proved)", 4: "Daniel 2026 (reported)"}


def grid(n: int) -> int:
    k = math.isqrt(n)
    return k if k * k == n else k + 1


def delivered() -> dict:
    """`{n: Decimal side}`, read exactly from the submission."""
    per = {}
    with open(SUBMISSION) as f:
        names = [h.strip() for h in f.readline().split(",")]
        ix = {h: i for i, h in enumerate(names)}
        for line in f:
            p = line.rstrip("\n").split(",")
            if len(p) < len(names):
                continue
            per.setdefault(int(p[ix["n"]]), []).append(
                (Decimal(p[ix["x"]].strip()), Decimal(p[ix["y"]].strip()),
                 Decimal(p[ix["angle"]].strip())))
    return {n: TG.side(c) for n, c in per.items()}


def catalogue() -> dict:
    if not os.path.exists(CATALOGUE):
        return {}
    with open(CATALOGUE) as f:
        return json.load(f)["cases"]


def karakus(n: int) -> Decimal:
    """The general lower bound `s(n) >= 1/2 + sqrt(n - floor(sqrt n) + 1/4)` (nonsquare, n >= 8)."""
    k = math.isqrt(n)
    if k * k == n or n < 8:
        return Decimal(k)
    return Decimal(1) / 2 + (Decimal(n - k) + Decimal(1) / 4).sqrt()


def main() -> int:
    deliv = delivered()
    cat = catalogue()
    out = {"rows": {}, "score": {}, "import": [], "locked": [], "open_ties": []}
    total = Decimal(0)
    for n in range(1, 1001):
        L = deliv[n]
        k = grid(n)
        r = k * k - n
        sn = Decimal(n).sqrt()
        total += L / sn - 1
        c = cat.get(str(n)) or cat.get(n) or {}
        up = Decimal(c["upper"]["value"]) if c.get("upper", {}).get("value") else None
        lo = Decimal(c["lower"]["value"]) if c.get("lower", {}).get("value") else None
        rec = {"n": n, "k": k, "r": r, "L": str(L), "catalogue_status": c.get("status"),
               "catalogue_upper": str(up) if up is not None else None,
               "catalogue_lower": str(lo) if lo is not None else None,
               "score": str(L / sn - 1), "beats": L < k - Decimal("1e-8")}
        if up is not None and up < L - Decimal("1e-8"):
            rec["class"] = "import"
            rec["gain"] = str((L - up) / sn)
            out["import"].append(rec)
        elif rec["beats"]:
            rec["class"] = "beaten"
            rec["headroom"] = str((L - (lo if lo is not None else karakus(n))) / sn)
        elif r in LOCKED_R or c.get("status") == "proved":
            rec["class"] = "locked"
            out["locked"].append(rec)
        else:
            rec["class"] = "open_tie"
            out["open_ties"].append(rec)
        out["rows"][str(n)] = rec

    ties = [r for r in out["rows"].values() if not r["beats"]]
    beats = [r for r in out["rows"].values() if r["beats"]]
    score = {k: sum(Decimal(r["score"]) for r in v) for k, v in
             (("all", list(out["rows"].values())), ("ties", ties), ("beats", beats),
              ("locked", out["locked"]), ("open_ties", out["open_ties"]),
              ("import", out["import"]))}
    out["score"] = {k: str(v) for k, v in score.items()}

    print(f"score                    {score['all']:.9f}   ({len(beats)} beaten + {len(ties)} tied)")
    print(f"  beaten rows            {score['beats']:.9f}   ({len(beats)} rows)")
    print(f"  tied rows              {score['ties']:.9f}   ({len(ties)} rows)")
    print(f"    locked (r<=4 / proved) {score['locked']:.9f}   ({len(out['locked'])} rows, unreachable)")
    print(f"    open ties            {score['open_ties']:.9f}   ({len(out['open_ties'])} rows)")
    gain = sum(Decimal(r["gain"]) for r in out["import"])
    print(f"\nimport list              {score['import']:.9f}   ({len(out['import'])} rows where the "
          f"catalogue's verified bound is below ours)")
    for rec in sorted(out["import"], key=lambda r: -Decimal(r["gain"]))[:12]:
        print(f"   n={rec['n']:>4} ours {Decimal(rec['L']):>13.9f} -> "
              f"{Decimal(rec['catalogue_upper']):>13.9f}  gain {Decimal(rec['gain']):+.6f}  "
              f"[{rec['catalogue_status']}]")
    if len(out["import"]) > 12:
        print(f"   ... {len(out['import']) - 12} more")
    print("\nopen ties by k (score at stake if the row could reach sqrt n):")
    byk = {}
    for rec in out["open_ties"]:
        byk.setdefault(rec["k"], []).append(rec)
    for k in sorted(byk):
        rs = byk[k]
        print(f"   k={k:>2}: {len(rs):>3} rows  score {sum(Decimal(r['score']) for r in rs):.4f}")
    print("\nbiggest open ties:")
    for rec in sorted(out["open_ties"], key=lambda r: -Decimal(r["score"]))[:10]:
        print(f"   n={rec['n']:>3} k={rec['k']:>2} r={rec['r']:>2}  score {Decimal(rec['score']):.5f}"
              f"  catalogue {rec['catalogue_status'] or 'no record'}")
    print("\nfrontier by r (beaten / tied):")
    byr = {}
    for rec in out["rows"].values():
        e = byr.setdefault(rec["r"], [0, 0])
        e[0 if rec["beats"] else 1] += 1
    print("   " + "  ".join(f"r={r}:{v[0]}/{v[0] + v[1]}" for r, v in sorted(byr.items()) if r <= 30))
    print("\nverdict")
    print(f"   * {len(out['locked'])} tied rows are locked by proof (r <= 4 or a proved case): "
          f"{score['locked']:.4f} of score that no run can take.")
    print(f"   * {len(out['import'])} rows can be taken today from the catalogue for "
          f"{gain:.6f} (certified poses, no search).")
    print(f"   * {len(out['open_ties'])} open ties hold {score['open_ties']:.4f}; every one needs a "
          f"*new* packing, and the biggest items are the small-k rows.")
    print(f"   * {len(beats)} beaten rows hold {score['beats']:.4f}; polish there is not a record, it is "
          f"a side reduction worth 1/sqrt n per unit.")

    path = REPORT
    argv = sys.argv
    if "--json" in argv:
        path = argv[argv.index("--json") + 1]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print(f"\nreport: {os.path.relpath(path, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
