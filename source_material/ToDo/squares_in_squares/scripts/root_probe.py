#!/usr/bin/env python3
r"""root_probe.py — the missing diagnostic of the run-19 campaign.

The campaign ledger recorded only gate outcomes (find / None), so
"0 applicable finds" cannot distinguish near-misses from far-misses.
This probe re-runs attempts on the smallest roots at the campaign's
levels, recording the RAW settle objective and the binding margins
BEFORE the finalize gate:

  per attempt: terminal objective f, worst positive pair margin
  (penetration depth), worst wall-out, and the settle's last-step L.

Readout: f ~ 1e-9..1e-7 => kissing the boundary (packings likely exist
just below; ramp stalling); f ~ 1e-3..1e-1 => local-minimum trapped
(structural prior needed, not more pressure).
"""
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pressure_settle import obj_grad, sat_stack, hw, out_amounts
from oracle_basin import ramp_settle
from cent_discovery import rsa_seed

ROOT = os.path.dirname(HERE)
tab = json.load(open(os.path.join(ROOT, "workspace/submission/table.json")))


def probe(n, L_t, seed, ramp=12):
    rng = np.random.RandomState(seed)
    q0 = rsa_seed(n, L_t + 0.45, rng)
    q, f = ramp_settle(q0, L_t, steps=ramp)
    m = q.size // 3
    S, _, _, _ = sat_stack(q[:m], q[m:2 * m], q[2 * m:])
    M = S.min(axis=0)
    iu = np.triu_indices(m, k=1)
    pair_pen = float(np.max(M[iu]))            # worst pair margin (>0 overlap)
    wall = float(np.max(out_amounts(q[:m], q[m:2 * m], hw(q[2 * m:]), L_t)))
    # binding-axis histogram: which of the 4 SAT axis cases holds
    # the worst pair (0=u_i,1=v_i,2=u_j,3=v_j) — structural signature
    return {"f": f, "pair_pen": pair_pen, "wall_out": wall}


def main():
    ROOTS = ((12, 4.0), (20, 5.0), (30, 6.0))
    LEVELS = (0.1, 0.05, 0.002)
    out = {}
    for n, g in ROOTS:
        for lv in LEVELS:
            L_t = round(g - lv, 6)
            recs = []
            t0 = time.time()
            for s in range(1, 7):
                r = probe(n, L_t, 7919 * n + s + int(lv * 1000))
                recs.append(r)
            fs = [r["f"] for r in recs]
            pens = [r["pair_pen"] for r in recs]
            walls = [r["wall_out"] for r in recs]
            out[f"n{n}_g{lv}"] = {
                "target": L_t, "n_seeds": 6,
                "best_f": min(fs), "median_f": sorted(fs)[len(fs)//2],
                "best_pair_pen": min(pens),
                "best_wall_out": min(walls),
                "f_all": [round(x, 9) for x in fs]}
            print(f"n={n} @ {L_t}: best f {min(fs):.2e} | median "
                  f"{sorted(fs)[len(fs)//2]:.2e} | min pair_pen "
                  f"{min(pens):.2e} | min wall {min(walls):.2e} "
                  f"| {time.time()-t0:.0f}s", flush=True)
    json.dump(out, open(os.path.join(
        ROOT, "workspace/push/root_probe.json"), "w"), indent=1)
    print("saved workspace/push/root_probe.json")


if __name__ == "__main__":
    main()
