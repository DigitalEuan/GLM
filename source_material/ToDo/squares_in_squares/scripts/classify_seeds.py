#!/usr/bin/env python3
r"""classify_seeds.py — Sturmian classification of mid-band targets at seed
level (no annealing cycles committed; the classifier's whole purpose).

For each target n (grid-tied, roomy window): build the grid+jitter seed at
L = ceil(sqrt(n)) - 0.005 (the jam state of stage-B attempts), compute the
contact bit-stream and lag-1 autocorrelation, and record the verdict.
RIGID_WALL  -> motif change needed; annealing cycles are not committed.
ONE_PARAM_JAM -> would warrant rotation-rich retry (none expected here).
Appends to workspace/push/delta_sigma_results.json.
"""
import json
import sys
from math import ceil, sqrt

sys.path.insert(0, "/home/z/my-project/scripts")
from delta_sigma_push import classify
from sa_push import grid_seed

PUSH = "/home/z/my-project/workspace/push"
RES = PUSH + "/delta_sigma_results.json"

TARGETS = [803, 748, 983, 804, 862, 695, 749, 984, 922, 696]


def main():
    res = json.load(open(RES)) if __import__("os").path.exists(RES) else []
    have = {r.get("n") for r in res}
    lines = []
    for n in TARGETS:
        if n in have:
            continue
        g = ceil(sqrt(n))
        L = g - 0.005
        X, Y, TH = grid_seed(n, L, 7919 * n + 13)
        verdict, rho, ones, tot = classify(X, Y, TH)
        r = {"n": n, "verdict": verdict, "rho": rho, "contacts": ones,
             "total": tot, "L_seed": L, "mode": "seed-level"}
        res.append(r)
        lines.append(f"  n={n}: {verdict} rho={rho:.3f} contacts={ones}/{tot} (seed at L={L:.3f})")
        json.dump(res, open(RES, "w"), indent=1)
    with open(PUSH + "/delta_sigma_log.txt", "a") as f:
        f.write("seed-level classification (no cycles committed):\n")
        for ln in lines:
            f.write(ln + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
