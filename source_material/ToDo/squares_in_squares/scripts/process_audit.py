#!/usr/bin/env python3
r"""process_audit.py — Run 12: the process algebra, measured.

User question: "do lemmas provide any clues to the best grid anywhere?
or can we define new ones to then direct our grid constructions? I feel
we are looking at processes rather than start/end points."

Four measurements on the run-11 frontier (table 22.887471):

  A. MONOTONE ENVELOPE (the deletion lemma as a table law).
     s(n) <= s(n+1) is provable (remove a square). On our table:
     L(n) <= L(n+1) must hold; any violation is a FREE improvement
     (apply the removal process to state(n+1)). Count violations.

  B. OPTIMALITY FLAGS (end points we can actually prove).
     Lower bound per n: LB(n) = max(sqrt(n) [area], running max of
     proven values s*(m) for m <= n). Proven sources (workspace
     records, SORRY_LEDGER.md + spec.json axioms):
       - literature optimality: n in {1..8, 10, 14, 15, 24, 35}
         (values = table L at those n, since proven optimal);
       - Nagamochi 2005: s(k^2-2) = s(k^2-1) = k (value k exactly);
       - perfect squares: s(k^2) = k (area bound, tight).
     A row with L(n) <= LB(n) + 2e-9 (table clearance) is PROVABLY
     OPTIMAL today. This is the complete set of end points reachable
     without new mathematics.

  C. SHELL/CASCADE LAW (process prediction, empirical).
     The shell count lemma (Basic.lean cascade_count_symbolic): a
     container step adds (L+1) + L = 2L+1 squares. Prediction:
     L(n + 2*floor(L(n)) + 1) <= L(n) + 1. Measured over all rows.
     Failures = where the +1 process does not transfer (the law is
     family-specific, not a theorem — this measures its domain).

  D. GOBEL FAMILY FRONTIER. For n = k^2+1 the certified family value
     is k + sqrt(2)/2 (Q(sqrt2), theta=45, a=1... constructed by
     gobelS). Compare table L(k^2+1) against it: where the survey
     records beat the algebraic family = the process frontier.

Output: download/process_audit.json
"""
import json
import math
from collections import Counter, defaultdict
from math import floor, sqrt

TAB = json.load(open("/home/z/my-project/download/table.json"))
MAP = json.load(open("/home/z/my-project/download/leech_map.json"))
CERTS = json.load(open("/home/z/my-project/download/galois_certificates.json"))
OUT = "/home/z/my-project/download/process_audit.json"

TOL = 2e-9          # table clearance convention (run-11 calibration)
L = {n: float(TAB[str(n)]["L"]) for n in range(1, 1001)}
SRC = {n: TAB[str(n)]["src"] for n in range(1, 1001)}


def main():
    res = {}

    # ---- A. monotone envelope --------------------------------------
    viol = [(n, L[n], L[n + 1]) for n in range(1, 1000)
            if L[n] > L[n + 1] + 1e-12]
    res["A_monotone_envelope"] = {
        "lemma": "deletion: s(n) <= s(n+1) (removable square)",
        "table_law_holds": len(viol) == 0,
        "violations": viol,
        "note": ("each violation would be a free improvement by applying "
                 "the removal process to state(n+1); count: %d" % len(viol)),
    }

    # ---- B. optimality flags ---------------------------------------
    # proven value sources
    lit = {1, 2, 3, 4, 5, 6, 7, 8, 10, 14, 15, 24, 35}   # SORRY_LEDGER
    nag = set()
    k = 2
    while k * k - 2 <= 1000:
        nag.add(k * k - 2)
        if k * k - 1 <= 1000:
            nag.add(k * k - 1)
        k += 1
    sq = {i * i for i in range(1, 32) if i * i <= 1000}

    proven = {}   # n -> (value, source)
    for n in sorted(lit):
        proven[n] = (L[n], "literature {1..8,10,14,15,24,35}")
    for n in sorted(nag):
        kk = round(sqrt(n + 2))
        # table check: Nagamochi says s = k; table must carry L = k
        if n not in proven and abs(L[n] - kk) < 1e-6:
            proven[n] = (float(kk), "Nagamochi 2005 (k^2-2/k^2-1 = k)")
        elif n not in proven:
            proven[n] = (float(kk), "Nagamochi (table mismatch! %.6f vs %d)"
                         % (L[n], kk))
    for n in sorted(sq):
        kk = int(sqrt(n))
        if n not in proven and abs(L[n] - kk) < 1e-6:
            proven[n] = (float(kk), "area bound tight at k^2")
        elif n not in proven:
            proven[n] = (float(kk), "area (table mismatch! %.6f vs %d)"
                         % (L[n], kk))

    # envelope: LB(n) = max(sqrt(n), max proven value for m <= n)
    lb = [0.0] * 1001
    run = 0.0
    for n in range(1, 1001):
        if n in proven:
            run = max(run, proven[n][0])
        lb[n] = max(sqrt(n), run)

    opt_rows = []
    for n in range(1, 1001):
        if L[n] <= lb[n] + TOL:
            # which source sealed it
            src = ("area(sqrt(n))" if abs(lb[n] - sqrt(n)) < 1e-12
                   and lb[n] >= run else "envelope")
            # finer: last proven m that set the running max
            opt_rows.append({"n": n, "L": L[n], "LB": round(lb[n], 6),
                             "src": SRC[n].split(":")[0]})
    res["B_optimality_flags"] = {
        "proven_sources": {
            "literature": sorted(lit),
            "nagamochi": sorted(nag),
            "perfect_squares": sorted(sq),
        },
        "proven_values": {str(n): v for n, (v, s) in sorted(proven.items())},
        "provably_optimal_rows": len(opt_rows),
        "rows": opt_rows,
        "note": ("rows with L(n) <= LB(n) + 2e-9: optimal TODAY, by the "
                 "deletion lemma (monotone s) + area + the recorded "
                 "literature theorems. Everything else is open."),
    }

    # ---- C. shell/cascade law --------------------------------------
    holds = fails = 0
    fail_list = []
    for n in range(1, 1001):
        np = n + 2 * floor(L[n]) + 1
        if np > 1000:
            continue
        if L[np] <= L[n] + 1 + 5e-9:
            # 5e-9: the table clearance convention (each row carries its
            # own +1.3-1.9e-9); a 1e-9 window misreads clearance as failure
            holds += 1
        else:
            fails += 1
            fail_list.append({"n": n, "L": L[n], "n'": np,
                              "L(n)+1": L[n] + 1, "L(n')": L[np]})
    res["C_shell_law"] = {
        "lemma": ("shell count (Basic.lean cascade_count_symbolic): "
                  "container step adds (L+1)+L = 2L+1 squares"),
        "prediction": "L(n + 2*floor(L(n)) + 1) <= L(n) + 1",
        "checked": holds + fails, "holds": holds, "fails": fails,
        "failures": fail_list[:20],
        "note": ("empirical law of the construction families; NOT a "
                 "theorem for arbitrary packings — failures map the "
                 "law's domain"),
    }

    # ---- D. Goebel family frontier ----------------------------------
    fam = []
    for kk in range(2, 32):
        n = kk * kk + 1
        if n > 1000:
            break
        fv = kk + sqrt(2) / 2          # certified family value (Q(sqrt2))
        tv = L[n]
        fam.append({"k": kk, "n": n, "family_value": round(fv, 6),
                    "table_value": round(tv, 6),
                    "verdict": ("family wins/ties" if tv >= fv - 1e-9
                                else "survey beats family by %.4f" % (fv - tv))})
    res["D_goebel_frontier"] = {
        "family": "gobelS: n = k^2+1 at s = k + sqrt(2)/2 (certified Q(sqrt2))",
        "rows": fam,
        "beats": sum(1 for r in fam if r["table_value"] < r["family_value"] - 1e-9),
    }

    json.dump(res, open(OUT, "w"), indent=1)
    print("A monotone envelope:", "HOLDS" if not viol else
          f"{len(viol)} VIOLATIONS", viol[:5])
    print("B provably optimal rows:", len(opt_rows), "of 1000")
    print("   sources:", {k: len(v) for k, v in
                          res["B_optimality_flags"]["proven_sources"].items()})
    print("C shell law:", holds, "holds /", fails, "fails")
    for f in fail_list[:5]:
        print("   FAIL n=%(n)d L=%(L).4f n'=%(n')d L+1=%(L(n)+1).4f table=%(L(n')).4f" % f)
    print("D Goebel frontier: survey beats family on",
          res["D_goebel_frontier"]["beats"], "of", len(fam))
    print("->", OUT)


if __name__ == "__main__":
    main()
