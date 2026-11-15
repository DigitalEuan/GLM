#!/usr/bin/env python3
r"""import_candidates.py — run 35/36: gate-import the evand candidate
certificates as register records (T-ids per the jlevy closing replies).

Cert format (workspace/sources/candidates/*.cert, plain text rationals):
  line 1: comment
  line 2: <n> <side S as rational>
  next n lines: <x> <y> <t>   with rotation (c,s) = ((1-t^2)/(1+t^2),
    2t/(1+t^2)) -> theta = 2*atan(t); x, y are centres in [0, S]^2.

Procedure (the run-30 pattern, per-n best-L-wins):
  P.verify(state, tol=1e-9)  ->  P.finalize(state, gap=2e-9)
  -> stored L is the finalized side rf["L"] (cert side + ~2e-9 scale)
  -> applied only if it beats the current row by > MIN_GAIN = 1e-7
     (the 21 noise-level "same packing less finalize inflation" rows,
     ~1.8e-9, never churn the table; `*_regularized` same-side variants
     are skipped by the same rule).

Attribution map (T-id per the jlevy/squares register, run 35):
  172->T-257  175->T-267  182->T-243  204->T-268  260->T-269
  268->T-270  293->T-271  303->T-272  304->T-273   (all Evan Daniel).

Dry-run first (default); --apply writes the table.  Ledger:
  workspace/push/import_candidates35.json.
"""
import json
import math
import os
import sys
from fractions import Fraction
from math import atan, sqrt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import packlib as P

SRC = os.path.join(ROOT, "workspace/sources/candidates")
TAB = os.path.join(ROOT, "workspace/submission/table.json")
LEDGER = os.path.join(ROOT, "workspace/push/import_candidates35.json")
MIN_GAIN = 1e-7

TID = {172: "T-257", 175: "T-267", 182: "T-243", 204: "T-268",
       260: "T-269", 268: "T-270", 293: "T-271", 303: "T-272",
       304: "T-273"}


def parse_cert(path):
    lines = open(path).read().splitlines()
    n, S = lines[1].split()
    n, S = int(n), Fraction(S)
    if S <= 0 or n <= 0:
        raise ValueError("bad header")
    if len(lines) < 2 + n:
        raise ValueError("truncated cert")
    state = []
    for ln in lines[2:2 + n]:
        x, y, t = ln.split()
        x, y, t = Fraction(x), Fraction(y), Fraction(t)
        theta = 2 * atan(float(t)) if t else 0.0
        state.append((float(x), float(y), theta))
    if len(state) != n:
        raise ValueError("count mismatch")
    return n, S, state


def main():
    apply = "--apply" in sys.argv
    tab = json.load(open(TAB))
    before = sum(r["L"] / sqrt(int(k)) - 1 for k, r in tab.items())

    # group all candidates by n, keep the best verifying one per n
    best = {}
    rows = []
    for name in sorted(os.listdir(SRC)):
        if not name.endswith(".cert"):
            continue
        try:
            n, S, state = parse_cert(os.path.join(SRC, name))
        except Exception as e:
            rows.append({"cert": name, "error": str(e)})
            continue
        if n > 1000 or str(n) not in tab:
            continue
        cur = tab[str(n)]["L"]
        v = P.verify(state, tol=1e-9)
        if not v["ok"] or v["worst_pen"] > 1e-9:
            rows.append({"cert": name, "n": n, "why": "verify",
                         "worst_pen": v.get("worst_pen")})
            continue
        stf, rf = P.finalize(state, gap=2e-9)
        if not (rf["ok"] and rf["worst_pen"] <= -1e-12 and len(stf) == n):
            rows.append({"cert": name, "n": n, "why": "finalize"})
            continue
        newL = rf["L"]
        cand = {"cert": name, "n": n, "tid": TID.get(n),
                "cert_S": str(S), "old": cur, "new": newL,
                "row_gain": (cur - newL) / sqrt(n)}
        if newL < cur - MIN_GAIN:
            if n not in best or newL < best[n]["new"]:
                best[n] = cand
            rows.append(cand)
        else:
            rows.append(dict(cand, why=("no-beat" if newL >= cur
                                        else "below MIN_GAIN")))
    applied = sorted(best.values(), key=lambda r: r["n"])
    direct = sum(r["row_gain"] for r in applied)
    after = before - direct
    mode = "applied" if apply else "dry"
    print(f"{mode.upper()}: {len(applied)} rows, direct gain "
          f"{direct:.6f}; score {before:.9f} -> {after:.9f}")
    for r in applied:
        print(f"  n={r['n']:4d} {r['old']!r} -> {r['new']!r} "
              f"({r['tid']}, {r['cert']})")
    if apply:
        for r in applied:
            tab[str(r["n"])] = {
                "L": round(r["new"], 12), "state": None, "src": None}
        # fill state/src from the ledger rows (stf held per candidate)
        # -- re-attach below before writing
        for r in rows:
            if r.get("cert") in {a["cert"] for a in applied} and "state" not in r:
                pass
        # simpler: re-parse the applied certs to attach states
        for r in applied:
            n, S, state = parse_cert(os.path.join(SRC, r["cert"]))
            stf, rf = P.finalize(state, gap=2e-9)
            tab[str(r["n"])] = {
                "L": round(rf["L"], 12), "state": stf,
                "src": f"register:{r['tid']} (Evan Daniel, jlevy/squares)"}
        json.dump(tab, open(TAB, "w"), indent=1, sort_keys=True)
    json.dump({"run": 35, "mode": mode, "rows": rows,
               "applied_total": len(applied), "direct_gain": direct,
               "score_before": before, "score_after": after},
              open(LEDGER, "w"), indent=1)
    print(f"ledger -> {LEDGER}")


if __name__ == "__main__":
    main()
