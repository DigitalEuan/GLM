#!/usr/bin/env python3
r"""import_atlas.py — Run 13 push A: import the community's certified
best-known packings (Square Packing Atlas / jlevy/squares register) into
table.json, packlib-gated exactly like our own constructions.

Source (external data, attributed):
  evand/square-packing  search/regularize/lists/best.json + certs/n-XXX.cert.gz
  "for each n the best known packing, solved exactly at its side and written
   as a rational certificate that two separately written exact checkers
   accept" (state as of 2026-10-17; finders attributed per record).

Cert format (gzip text):
  line 1: comment
  line 2: <n> <side as rational>
  next n lines: <x> <y> <t>   with rotation (c,s) = ((1-t^2)/(1+t^2), 2t/(1+t^2))
  -> theta = 2*atan(t); x, y are centres in [0, s]^2.

Every imported state is converted to float, run through packlib.finalize
(2e-9 contact gap, 12-dp round) and applied only if it VERIFIES and beats
the current table by > 1e-9.  Rejections are recorded.  Attribution is kept
in the src string so the submission table carries provenance.
"""
import gzip
import json
import os
import sys
from fractions import Fraction
from math import atan, sqrt

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(
    __import__("os").path.abspath(__file__)))
sys.path.insert(0, ROOT + "/scripts")
import packlib as P

ATLAS = ROOT + "/workspace/sources/atlas/lists"
TAB = ROOT + "/workspace/submission/table.json"
OUT = ROOT + "/workspace/push/atlas_import.json"


def parse_cert(path):
    with gzip.open(path, "rt") as f:
        lines = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    n, side = lines[0].split()
    n = int(n)
    side = float(Fraction(side))
    st = []
    for ln in lines[1:1 + n]:
        x, y, t = ln.split()
        x = float(Fraction(x)); y = float(Fraction(y)); t = float(Fraction(t))
        th = 2.0 * atan(t)
        st.append((x, y, th))
    assert len(st) == n, (path, len(st), n)
    return n, side, st


def main():
    best = json.load(open(os.path.join(ATLAS, "best.json")))
    tab = json.load(open(TAB))
    applied, rejected, skipped = [], [], 0
    tot_gain = 0.0
    for b in best:
        n = b["n"]
        if n > 1000:
            continue
        cert = os.path.join(ATLAS, b["cert"].split("lists/")[-1])
        if not os.path.exists(cert):
            rejected.append({"n": n, "why": "cert missing", "cert": cert})
            continue
        nn, side, st = parse_cert(cert)
        assert nn == n
        cur = tab[str(n)]["L"]
        if side >= cur - 1e-9:
            skipped += 1
            continue
        # design state must fit in its exact side; finalize adds the 2e-9 gap
        stf, rf = P.finalize(st, gap=2e-9)
        if (not rf["ok"]) or rf["worst_pen"] > 0:
            rejected.append({"n": n, "why": "verify fail",
                             "worst_pen": rf["worst_pen"]})
            continue
        Lv = rf["L"]
        if Lv >= cur - 1e-9:
            rejected.append({"n": n, "why": "no beat after finalize",
                             "L": Lv, "cur": cur})
            continue
        gain = (cur - Lv) / sqrt(n)
        tot_gain += gain
        finder = (b.get("finder") or "-").replace(" ", "")[:24]
        tab[str(n)] = {
            "L": round(Lv, 12),
            "state": stf,
            "src": f"atlas:{b.get('variant','?')}:n-{n:03d}:{finder}"}
        applied.append({"n": n, "old": cur, "new": round(Lv, 12),
                        "gain": round(gain, 8), "finder": b.get("finder"),
                        "side_exact": side})
        print(f"  APPLIED n={n:4d}: {cur:.9f} -> {Lv:.9f} "
              f"(gain {gain:.6f}) finder={b.get('finder')}")

    print(f"\napplied: {len(applied)} | skipped (already <= atlas): {skipped} "
          f"| rejected: {len(rejected)}")
    print(f"direct score gain: {tot_gain:.6f}")
    if applied:
        json.dump(tab, open(TAB, "w"))
        tot = sum(tab[str(n)]["L"] / sqrt(n) - 1 for n in range(1, 1001))
        beats = sum(1 for n in range(1, 1001)
                    if tab[str(n)]["L"] < P.grid_L(n) - 1e-12)
        print(f"new score: {tot:.6f} | beats-grid: {beats}")
    json.dump({"applied": applied, "rejected": rejected, "skipped": skipped,
               "direct_gain": tot_gain}, open(OUT, "w"), indent=1)
    print("ledger ->", OUT)


if __name__ == "__main__":
    main()
