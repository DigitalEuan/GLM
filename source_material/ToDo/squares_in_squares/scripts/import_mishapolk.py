#!/usr/bin/env python3
r"""import_mishapolk.py — run 30, P3: import Mishapolk certificates.

fetch_mishapolk30.json found 366 direct-certificate bounds that beat
our table (potential row-gain 0.173971; 218 of the 219 rows with gain
> 1e-5 lie in the band 325..1000 our atlas never covered).  This
script parses each fetched certificate, verifies it, and applies
best-L-wins.

Certificate format (certificates/0000-0999/n<N>.cert):
  # comments
  <n> <S as exact rational>
  <x> <y> <t>            # per square: CENTRE coords, t = tan(theta/2)

theta = 2*atan(t)  (t=1 -> pi/4, t=0 -> 0).  Strict OPEN container in
the source verifier; our packlib.verify uses closed tolerance — a
state verified open passes ours.  Finalize then scales by +2e-9
relative for CSV-rounding safety.

Construction-only entries are NOT imported here (no coordinates) —
they are watch rows for future certificates (only n=261 has gain
> 1e-5 anyway).

Ledger: workspace/push/import_mishapolk30.json (resumable: rows
already applied are skipped; --dry-run supported).
"""
import json
import math
import os
import sys

from fractions import Fraction

sys.path.insert(0, "/home/z/my-project/scripts")
import packlib as P

W = "/home/z/my-project"
SRC = W + "/workspace/sources/mishapolk"
TAB = W + "/workspace/submission/table.json"
FETCH_LED = W + "/workspace/push/fetch_mishapolk30.json"
OUT = W + "/workspace/push/import_mishapolk30.json"
MIN_GAIN = 1e-9          # apply rows with verified gain above this
DRY = "--dry-run" in sys.argv
if DRY:
    # a dry run must never feed the resume ledger (run-30 lesson:
    # applied=True rows from a dry run caused a 196-row skip)
    OUT = OUT.replace(".json", "_dry.json")


def frac(s):
    return Fraction(str(s)) if "/" in str(s) else Fraction(int(float(s)), 1)


def parse_cert(path):
    """-> (n, S_frac, state) or None."""
    n = None
    S = None
    state = []
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if n is None:
            n = int(parts[0])
            S = frac(parts[1])
            continue
        x = frac(parts[0]); y = frac(parts[1]); t = frac(parts[2])
        theta = 2.0 * math.atan(float(t))
        state.append((float(x), float(y), theta))
    if n is None or len(state) != n:
        return None
    return n, S, state


def cert_rel(src):
    return src.replace("certificates/", "").replace("/", "_")


def main():
    led = json.load(open(FETCH_LED))
    tab = json.load(open(TAB))
    out_rows = []
    applied = skipped = failed = 0

    # candidate rows: direct entries whose fetch actually has a file
    cands = []
    for r in led["direct"]:
        path = f"{SRC}/certs/{cert_rel(r['src'])}"
        if not os.path.exists(path):
            continue
        cur = tab[str(r["n"])]["L"]
        gain = (cur - r["new"]) / math.sqrt(r["n"])
        if gain <= MIN_GAIN:
            continue
        cands.append((r["n"], r, path, cur, gain))
    cands.sort(key=lambda c: c[3])          # worst rows first
    print(f"candidates: {len(cands)} rows "
          f"(potential {sum(c[4] for c in cands):.6f})", flush=True)

    done = {}
    if os.path.exists(OUT):
        done = {r["n"]: r for r in json.load(open(OUT))["rows"]}

    for n, r, path, cur, gain in cands:
        if n in done and done[n].get("applied"):
            skipped += 1
            out_rows.append(done[n])
            continue
        pc = parse_cert(path)
        if pc is None or pc[0] != n:
            failed += 1
            out_rows.append({"n": n, "applied": False,
                             "why": f"parse ({path})", "old": cur})
            continue
        _pn, S, state = pc
        v = P.verify(state, tol=1e-9)
        if not v["ok"] or v["worst_pen"] > 1e-9:
            failed += 1
            out_rows.append({"n": n, "applied": False, "why": "verify",
                             "old": cur, "cert_S": float(S)})
            print(f"  n={n}: VERIFY FAIL "
                  f"(worst_pen {v['worst_pen']:.2e})", flush=True)
            continue
        stf, rf = P.finalize(state, gap=2e-9)
        if not (rf["ok"] and rf["worst_pen"] <= -1e-12 and len(stf) == n):
            failed += 1
            out_rows.append({"n": n, "applied": False, "why": "finalize",
                             "old": cur, "verify_L": v["L"]})
            continue
        newL = rf["L"]
        if newL >= cur - 1e-12:
            skipped += 1
            out_rows.append({"n": n, "applied": False, "why": "no beat",
                             "old": cur, "verify_L": newL,
                             "src": r["src"], "credit": r["credit"]})
            continue
        row = {"n": n, "applied": True, "old": cur, "new": newL,
               "row_gain": (cur - newL) / math.sqrt(n),
               "cert_S": str(S), "verify_L": v["L"],
               "src": f"mishapolk:{r['src']}", "credit": r["credit"]}
        out_rows.append(row)
        applied += 1
        if not DRY:
            tab[str(n)] = {"L": newL, "state": stf,
                           "src": f"mishapolk:{r['src'].split('/')[-1]}"}
        print(f"  n={n}: {cur:.9f} -> {newL:.9f} "
              f"(gain {(cur-newL)/math.sqrt(n):.6f})", flush=True)

    if not DRY and applied:
        json.dump(tab, open(TAB, "w"))
        score = sum(rec["L"] / math.sqrt(int(k)) - 1 for k, rec in tab.items())
        beats = sum(1 for k in range(1, 1001)
                    if tab[str(k)]["L"] < math.ceil(math.sqrt(k)) - 1e-12)
    else:
        tab2 = json.load(open(TAB)) if DRY else tab
        score = sum(rec["L"] / math.sqrt(int(k)) - 1 for k, rec in tab2.items())
        beats = sum(1 for k in range(1, 1001)
                    if tab2[str(k)]["L"] < math.ceil(math.sqrt(k)) - 1e-12)

    json.dump({"rows": out_rows, "applied": applied, "skipped": skipped,
               "failed": failed, "dry_run": DRY,
               "score_after": round(score, 9), "beats_grid": beats},
              open(OUT, "w"), indent=1)
    print(f"applied {applied} | skipped {skipped} | failed {failed}")
    print(f"score: {score:.9f} | beats-grid {beats}")
    print("ledger ->", OUT)


if __name__ == "__main__":
    main()
