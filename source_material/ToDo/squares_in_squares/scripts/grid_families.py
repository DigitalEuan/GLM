#!/usr/bin/env python3
r"""grid_families.py — run 115: do the constructive families give *anything*
below the base grid on the 447 unbeaten rows?

The question: Block45, Block45Half and the ridge are exact families whose sides
sit below `2k + 1` at their own counts, and they beat the delivered table at a
handful of counts.  The 447 unbeaten rows have L = ceil(sqrt n) — the plain grid
— and nothing better.  Does any family member, at ANY of its counts, fit a grid
row below the grid?  Because a packing of N cells at side L also packs every
n <= N at side <= L (delete cells), a member covers a row n whenever N >= n.

Families, from docs 61/62/96 (exact laws, no fitting):

  Block45(s, k)      N = s^2 + 2k(k+1),  L = max(s/sqrt2 + k + 1, s*sqrt2),
                     feasible  k <= floor(s/sqrt2) + 1
  Block45Half(s, k)  N = s^2 + 2k(k-1),  L = max(s/sqrt2 + k + 1/2, s*sqrt2),
                     feasible  L >= 2k - 2
  ridge(m)           N = m^2 + 1,        L = m + 1/sqrt2   (the single-word
                     best case w = min(x, 1/x) = 1/sqrt2 at x = 1),  m >= 2
                     (m = 1 would read N = 2 at L = 1.7071, which s(2) = 2
                     refutes; the seam needs a ring to sit in)

The verdict per row is `L_family - ceil(sqrt n)`: negative means a family
already beats the base grid there (which would be a score gain), zero means
parity, positive is the deficit — the "beginnings of the way" for that row.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sqscore as SQ  # noqa: E402

SQ2 = math.sqrt(2.0)


def members(limit=1000):
    out = []
    for s in range(1, 60):
        for k in range(0, 40):
            # Block45
            if k <= int(math.floor(s / SQ2)) + 1:
                N = s * s + 2 * k * (k + 1)
                if 1 <= N <= limit:
                    L = max(s / SQ2 + k + 1, s * SQ2)
                    out.append({"fam": "Block45", "s": s, "k": k, "N": N, "L": L})
            # Block45Half
            N = s * s + 2 * k * (k - 1)
            if 1 <= N <= limit and k >= 1:
                L = max(s / SQ2 + k + 0.5, s * SQ2)
                if L >= 2 * k - 2:
                    out.append({"fam": "Block45Half", "s": s, "k": k, "N": N, "L": L})
    for m in range(2, 40):
        N = m * m + 1
        if N <= limit:
            out.append({"fam": "ridge", "s": m, "k": 0, "N": N, "L": m + 1 / SQ2})
    return out


def main():
    per = SQ.load()
    mem = members()
    print(f"family members (N <= 1000): {len(mem)}")
    grid_rows = [n for n in range(2, 1001)
                 if SQ.extent(per[n]) >= SQ.grid(n) - 1e-12]
    print(f"unbeaten (grid) rows: {len(grid_rows)}")

    beat, parity, behind = [], [], []
    rows = []
    for n in grid_rows:
        cov = [x for x in mem if x["N"] >= n]
        if not cov:
            continue
        b = min(cov, key=lambda x: x["L"])
        d = b["L"] - SQ.grid(n)
        rows.append({"n": n, "k": SQ.grid(n), "fam": b["fam"], "s": b["s"],
                     "k2": b["k"], "N": b["N"], "L": b["L"], "deficit": d})
        (beat if d < -1e-9 else parity if abs(d) <= 1e-9 else behind).append(rows[-1])

    print(f"\n  families beat the base grid on : {len(beat)} rows")
    print(f"  families at parity with it      : {len(parity)} rows")
    print(f"  families behind it              : {len(behind)} rows")

    if behind:
        print("\n  closest calls (smallest deficit, i.e. nearest a 'slightly better'):")
        for r in sorted(behind, key=lambda r: r["deficit"])[:15]:
            print(f"   n={r['n']:4d} k={r['k']:2d}  {r['fam']}(s={r['s']}, k={r['k2']})"
                  f"  N={r['N']:4d} L={r['L']:.6f}  deficit {r['deficit']:+.4f}")
        bands = {}
        for r in behind:
            bands.setdefault(r["k"], []).append(r["deficit"])
        print("\n  per band (k): best family deficit among that band's unbeaten rows")
        line = []
        for k in sorted(bands):
            line.append(f"k={k}:{min(bands[k]):+.3f}")
        print("   " + "  ".join(line))

    # for contrast: the same families at the counts where they DO beat the grid
    rec = []
    for x in mem:
        n = x["N"]
        if n <= 1000 and SQ.extent(per[n]) < SQ.grid(n) - 1e-12:
            rec.append((n, x["fam"], x["L"], SQ.extent(per[n]), SQ.grid(n)))
    print(f"\n  family members whose own count is a beaten row: {len(rec)}")
    for n, fam, L, Ld, k in sorted(rec, key=lambda r: r[0])[:12]:
        print(f"   n={n:4d} {fam:11s} family L={L:.6f}  delivered {Ld:.6f}  grid {k}")

    out = os.path.join(ROOT, "workspace/push/grid_families115.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"members": len(mem), "grid_rows": len(grid_rows),
               "beat": len(beat), "parity": len(parity), "behind": len(behind),
               "rows": rows}, open(out, "w"), indent=1)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
