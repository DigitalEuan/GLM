#!/usr/bin/env python3
"""phase2b_runner.py — attempt 0.1-class constructions on representative
MID targets with the full ladder (engine -> LP -> repair), and report the
measured obstruction honestly.

Targets: a spread across the MID band (k from 12 to 31, r various),
at L = grid - 0.1 and L = grid - 0.2 (0.1-class and beyond).
For each: 2 seeds, record pen, mode, obstruction s* (the Phase 1 law
predicts s* = (k - L)/(k - 1) if the engine lands a rigid grid; deviations
from that law = structures that are NOT rigid grids — the interesting
cases, and the only honest path to 0.1-class).

Output: workspace/push/phase2b.json + printed table."""
import json
import os
import sys
from math import ceil, sqrt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import packlib as P
from lp_closure import attempt, seeds_for

PUSH = "/home/z/my-project/workspace/push"


def rep_mid_targets():
    """representative MID: one per k block where possible, spread r."""
    aud = json.load(open("/home/z/my-project/download/residue_audit.json"))
    mid = sorted(r["n"] for r in aud["rows"] if r["class"] == "MID")
    by_k = {}
    for n in mid:
        k = int(ceil(sqrt(n)))
        by_k.setdefault(k, []).append(n)
    picks = []
    for k in sorted(by_k):
        lst = sorted(by_k[k])
        # smallest, middle, largest r in the block
        picks.append((k, lst[0]))
        picks.append((k, lst[len(lst) // 2]))
        picks.append((k, lst[-1]))
    # dedupe
    seen = set()
    out = []
    for k, n in picks:
        if n in seen:
            continue
        seen.add(n)
        out.append((k, n))
    return out


def main():
    targets = rep_mid_targets()
    # cap to keep runtime sane: 8 targets, spread across k-blocks
    if len(targets) > 8:
        step = len(targets) / 8.0
        targets = [targets[int(i * step)] for i in range(8)]
        seen = set(); out = []
        for k, n in targets:
            if n in seen:
                continue
            seen.add(n); out.append((k, n))
        targets = out
    results = []
    for k, n in targets:
        for depth in (0.1, 0.2):
            L = round(P.grid_L(n) - depth, 6)
            rec = attempt(n, L, seeds_for(n, 1), small_angle_search=False)
            law = (k - L) / (k - 1)
            for s in rec["seeds"]:
                info = s.get("info")
                s_star = None
                if isinstance(info, list) and len(info) >= 2 and info[0] in ("stuck", "best_stuck"):
                    s_star = info[1]
                results.append({
                    "k": k, "n": n, "depth": depth, "L": L,
                    "seed": s["seed"], "pen": s["pen"], "mode": s["mode"],
                    "info": info, "s_star": s_star, "law": round(law, 9),
                    "find": rec["find"] and rec["find"]["L"]})
                print(f"k={k} n={n} depth={depth}: pen={s['pen']:.2e} "
                      f"mode={s['mode']} s*={s_star} law={law:.6f} "
                      f"{'FIND ' + str(rec['find']['L']) if rec['find'] else ''}",
                      flush=True)
    json.dump({"targets": results},
              open(os.path.join(PUSH, "phase2b.json"), "w"), indent=1)
    # summary: deviations from the law
    dev = [r for r in results
           if r["s_star"] is not None and abs(r["s_star"] - r["law"]) > 1e-6]
    print(f"\ntotal runs: {len(results)}; "
          f"finds: {sum(1 for r in results if r['find'])}; "
          f"law deviations: {len(dev)}")
    for r in dev:
        print(f"  DEVIATION k={k} n={r['n']} depth={r['depth']}: "
              f"s*={r['s_star']} vs law {r['law']:.6f}")


if __name__ == "__main__":
    main()
