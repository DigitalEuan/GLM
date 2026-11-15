#!/usr/bin/env python3
r"""import_s299.py — run 26 P3: import the T-263 s(299) record.

Source (public register, jlevy/squares):
  - record: s(299) <= 17.8012385339790622, T-263 (reported 2026-11-03,
    jlevy/squares #893; frontier file packing/frontier/n-299.md);
    finder Evan Daniel (T-258, Oct 26 2026, #824), improved by
    Doega Oezden (rearrangement, -1.54e-8).
  - retained packet: kenaznia-doga/s299-upper-bound, file
    n-299-candidate.yaml (packing.squares:Witness/v2, center-basis,
    exact rationals), registry verify VERIFIED (44,551 pairs) +
    independent checker VALID.
  - fetched to workspace/sources/s299_T263.yaml this run.

Pipeline (the standing import standard, as import_atlas.py):
  parse exact rationals -> (x, y, theta) state -> packlib.verify
  (count, non-overlap, L) -> P.finalize (scale+round to CSV 12 dp,
  contacts at -2e-9) -> apply iff verified L < table[299].L - 1e-9.
  Provenance recorded in the row's src field.
"""
import json
import math
import sys
from fractions import Fraction

import yaml

W = "/home/z/my-project"
sys.path.insert(0, W + "/scripts")
import packlib as P

SRC = W + "/workspace/sources/s299_T263.yaml"
TAB = W + "/workspace/submission/table.json"
OUT = W + "/workspace/push/import_s299.json"


def frac(s):
    if isinstance(s, int):
        return Fraction(s, 1)
    return Fraction(str(s))


def main():
    doc = yaml.safe_load(open(SRC))
    wit = doc["witness"]
    n = wit["n"]
    side = frac(wit["side"])
    assert n == 299, n
    sqs = wit["squares"]
    assert len(sqs) == 299, len(sqs)

    state = []
    for s in sqs:
        cx = frac(s["center"][0])
        cy = frac(s["center"][1])
        b0 = s["basis"]            # flat [bx_str, by_str]; unit vector
        bx, by = frac(b0[0]), frac(b0[1])
        theta = math.atan2(float(by), float(bx))
        state.append((float(cx), float(cy), theta))

    r = P.verify(state)
    print(f"parsed: n={len(state)} side_exact={float(side):.15f}")
    print(f"verify: ok={r['ok']} L={r['L']:.15f} worst_pen={r['worst_pen']:.3e}")
    print(f"        |L - side| = {abs(r['L'] - float(side)):.3e}")

    stf, rf = P.finalize(state, gap=2e-9)
    print(f"finalize: ok={rf['ok']} L={rf['L']:.15f} "
          f"worst_pen={rf['worst_pen']:.3e} count={len(stf)}")
    assert rf["ok"] and rf["worst_pen"] <= 0 and len(stf) == 299

    tab = json.load(open(TAB))
    old = tab["299"]
    gain_row = (old["L"] - rf["L"]) / math.sqrt(299)
    rec = {
        "n": 299,
        "old_L": old["L"], "old_src": old.get("src", ""),
        "new_L": rf["L"],
        "side_exact": str(side),
        "row_gain": gain_row,
        "provenance": (
            "T-263, jlevy/squares #893 (2026-11-03); finder Evan Daniel "
            "(T-258, #824, 2026-10-26, fault-line DP seeded from Deotte's "
            "s(334)); improved by Doga Oezden (rearrangement, -1.54e-8). "
            "Cert: kenaznia-doga/s299-upper-bound n-299-candidate.yaml "
            "(packing.squares:Witness/v2, exact rationals); registry "
            "VERIFIED 44,551 pairs + independent checker VALID."),
    }
    if rf["L"] < old["L"] - 1e-9:
        tab["299"] = {"L": rf["L"], "state": stf,
                      "src": "register:T-263 (Daniel/Ozden #893)"}
        json.dump(tab, open(TAB, "w"))
        rec["applied"] = True
        print(f"APPLIED: {old['L']:.12f} -> {rf['L']:.12f} "
              f"(row gain {gain_row:.9f})")
    else:
        rec["applied"] = False
        print(f"NOT applied (table {old['L']:.12f} <= {rf['L']:.12f})")

    tab2 = json.load(open(TAB))
    score = sum(rr["L"] / math.sqrt(int(k)) - 1 for k, rr in tab2.items())
    rec["score_after_row"] = score
    json.dump(rec, open(OUT, "w"), indent=1)
    print(f"table score after row: {score:.9f}")
    print("ledger ->", OUT)


if __name__ == "__main__":
    main()
