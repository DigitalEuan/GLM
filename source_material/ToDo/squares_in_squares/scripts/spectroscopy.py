#!/usr/bin/env python3
r"""spectroscopy.py — run 6, piece 1: field membership of the table.

Every member L (non-grid rows; grid rows are integers) is tested for
membership in Q(sqrt(d)), d squarefree 2..99, i.e. L = p + q*sqrt(d) with
p = k/c, q = m/c, c <= 24, integers. Vectorized over m for each (row, d, c).
Classification tolerance 5e-6 (SVG-parsed values carry ~1e-6 noise);
genuine sqrt component required |q| >= 0.01 (else row is rational, d=1).
Output: the field inventory -- which fields actually pack squares below
grid in this problem, ground-truthed by the catalog + our finds.
"""
import json
from math import sqrt

import numpy as np

TAB = "/home/z/my-project/workspace/submission/table.json"
TOL = 5e-6
CMAX = 24          # denominator bound
QMIN = 0.01        # min genuine sqrt coefficient


def is_sf(d):
    if d in (2, 3):
        return True
    x, p = d, 3
    if x % 4 == 0:
        return False
    while p * p <= x:
        if x % (p * p) == 0:
            return False
        p += 2
    return True


FIELDS = [d for d in range(2, 100) if is_sf(d)]


def decompose(L):
    """Return (d, k, m, c, err) best fit, or None."""
    best = None
    for d in FIELDS:
        sd = sqrt(d)
        for c in range(1, CMAX + 1):
            cL = c * L
            if cL <= 0:
                continue
            # q*sd <= cL + 2  =>  m <= (cL+2)/sd
            mmax = int((cL + 2.0) / sd) + 1
            if mmax < 1:
                continue
            m = np.arange(0, mmax + 1, dtype=float)
            tgt = cL - m * sd
            k = np.round(tgt)
            err = np.abs(tgt - k)
            j = int(np.argmin(err))
            e = float(err[j])
            if e >= TOL:
                continue
            q = m[j] / c
            if abs(q) < QMIN:
                continue
            if best is None or e < best[4]:
                best = (d, int(k[j]), int(m[j]), c, e)
    return best


def main():
    tab = json.load(open(TAB))
    fields = {}
    unmatched = []
    for k, v in tab.items():
        n = int(k)
        L = v["L"]
        src = v["src"].split(":")[0]
        # rational test first: L = k/c, c <= 24 (covers 53/7 etc.)
        rat = None
        for c in range(1, CMAX + 1):
            kk = round(L * c)
            if abs(L * c - kk) < TOL:
                rat = (kk, c)
                break
        if rat:
            fields.setdefault(1, []).append(
                (n, L, src, f"{rat[0]}/{rat[1]}", "0"))
            continue
        if src == "grid":
            unmatched.append((n, L, src))  # should not happen
            continue
        hit = decompose(L)
        if hit:
            d, kk, m, c, e = hit
            p = kk / c
            q = m / c
            fields.setdefault(d, []).append((n, round(L, 9), src,
                                             f"{p:.6f}", f"{q:.6f}"))
        else:
            unmatched.append((n, round(L, 9), src))
    print("=== field inventory of table.json (1000 rows) ===")
    for d in sorted(fields):
        rows = fields[d]
        bysrc = {}
        for _, _, s, _, _ in rows:
            bysrc[s] = bysrc.get(s, 0) + 1
        ex = [(r[0], r[1], r[2]) for r in rows if r[2] != "grid"][:5]
        print(f"  Q(sqrt({d})): {len(rows)} rows  by-src={bysrc}")
        if ex:
            print(f"      non-grid e.g. {ex}")
    print(f"  UNMATCHED: {len(unmatched)}")
    for r in unmatched[:15]:
        print(f"      n={r[0]} L={r[1]} src={r[2]}")
    json.dump({"fields": {str(d): fields[d] for d in fields},
               "unmatched": unmatched},
              open("/home/z/my-project/workspace/push/spectroscopy.json", "w"),
              indent=1)


if __name__ == "__main__":
    main()
