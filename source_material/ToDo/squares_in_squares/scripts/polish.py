#!/usr/bin/env python3
r"""polish.py — Run 16/17 / NEXT_STEPS P2: motif-seeded numerical polish.

Doctrine (Run 13, failure -> requirement): search may only POLISH
constructions, never find them.  This is the bounded campaign around
the gobel5 near-miss map: take the top near-misses (family states with
s within +0.06 of grid on tied rows), and re-settle them on the fine
axes the coarse sweep quantizes:

  - band angle: th +/- 1.5 deg in 0.05 deg steps;
  - anchor (xlo, ylo): +/- 0.75 in 0.05 steps (0.5-grid in the sweep);
  - fill-lattice phase: {0, 0.25, 0.5} off the walls.

Any candidate with s < grid(n) on a tied row beats the table (the
table is at the community frontier = grid there); the ONLY gate that
applies anything is packlib.finalize.  Everything measured.  Best
candidate per n wins; ties broken by design s.
"""
import json
import math
import sys
from math import sqrt

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(
    __import__("os").path.abspath(__file__)))
sys.path.insert(0, ROOT + "/scripts")
import packlib as P
from gobel5 import build

TAB = ROOT + "/workspace/submission/table.json"
IN = ROOT + "/workspace/push/gobel5_results.json"
OUT = ROOT + "/workspace/push/polish_results.json"


def main():
    tab = json.load(open(TAB))
    L0 = {n: tab[str(n)]["L"] for n in range(1, 1001)}
    grid = {n: P.grid_L(n) for n in range(1, 1001)}
    led = json.load(open(IN))
    nm = sorted(led.get("nearmiss", []), key=lambda r: r["gap"])[:50]
    print(f"polish campaign: {len(nm)} near-miss seeds"
          + (f" (gap {nm[0]['gap']:.4f}..{nm[-1]['gap']:.4f})" if nm else ""))

    tested = fails = 0
    best = {}                      # n -> record dict (best L)
    for seed in nm:
        th0 = seed["th_deg"]
        H, W = seed["H"], seed["W"]
        xlo0, ylo0 = seed["xlo"], seed["ylo"]
        base_th = math.radians(th0)
        for dth in [0.05 * k for k in range(-30, 31)]:
            th = base_th + math.radians(dth)
            for phase in (0.0, 0.25, 0.5):
                for dx in [0.05 * k for k in range(-15, 16)]:
                    for dy in [0.05 * k for k in range(-15, 16)]:
                        r = build(th, H, W, xlo0 + dx, ylo0 + dy, phase)
                        if r is None:
                            continue
                        s, state = r
                        n = len(state)
                        if n < 5 or n > 1000:
                            continue
                        K = grid[n]
                        if s >= K - 1e-9:
                            continue
                        tested += 1
                        stf, rf = P.finalize(state, gap=2e-9)
                        if (not rf["ok"]) or rf["worst_pen"] > 0:
                            fails += 1
                            continue
                        Lv = rf["L"]
                        cur = best.get(n)
                        if Lv < L0[n] - 1e-9 and (cur is None or Lv < cur["L"]):
                            best[n] = {
                                "n": n, "th_deg": round(th0 + dth, 3),
                                "H": H, "W": W,
                                "xlo": round(xlo0 + dx, 3),
                                "ylo": round(ylo0 + dy, 3),
                                "phase": phase, "design_s": round(s, 9),
                                "L": round(Lv, 12), "old": L0[n], "state": stf}
                            print(f"  RECORD n={n}: th={th0+dth:.2f} {W}x{H} "
                                  f"@({xlo0+dx:.2f},{ylo0+dy:.2f}) ph={phase} "
                                  f"s={s:.6f} L={Lv:.9f} (was {L0[n]:.9f})")

    records = sorted(best.values(), key=lambda r: r["n"])
    print(f"tested {tested} | verify-fails {fails} | records {len(records)}")
    for rec in records:
        tab[str(rec["n"])] = {
            "L": rec["L"], "state": rec["state"],
            "src": (f"polish:th={rec['th_deg']},{rec['W']}x{rec['H']},"
                    f"({rec['xlo']},{rec['ylo']}),ph={rec['phase']}")}
    if records:
        json.dump(tab, open(TAB, "w"))
        tot = sum(tab[str(n)]["L"] / sqrt(n) - 1 for n in range(1, 1001))
        bts = sum(1 for n in range(1, 1001)
                  if tab[str(n)]["L"] < P.grid_L(n) - 1e-12)
        print(f"new score: {tot:.6f} | beats-grid: {bts}")
    json.dump({"records": records, "tested": tested, "verify_fails": fails,
               "seeds": len(nm)}, open(OUT, "w"), indent=1)
    print("ledger ->", OUT)


if __name__ == "__main__":
    main()
