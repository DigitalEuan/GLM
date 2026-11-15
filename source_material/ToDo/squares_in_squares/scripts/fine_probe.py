#!/usr/bin/env python3
r"""fine_probe.py — locate the feasibility boundary for n=12.

Stall signature (f ~ 2e-6 => one residual penetration ~1.5e-3) at
g-0.002 across BOTH priors suggests the boundary is between g-0.002
and g.  Probe the terminal objective at the fine deltas with both
priors; if best_f drops to ~1e-13 at some delta, packings exist there
(and the gate should be finding them — a gate bug to fix); if it
stays ~1e-7..1e-6, the settle stalls just short of feasibility at
every delta (honest near-optimality evidence).
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from oracle_basin import ramp_settle
from engine_variants import lattice_seed
from cent_discovery import rsa_seed
from lm_exactify import exactify
from pressure_settle import sat_stack, hw, out_amounts

import packlib as P

OUT = os.path.join(ROOT, "workspace/push/fine_probe.json")


def probe_one(n, L_t, seed, prior):
    rng = np.random.RandomState(seed)
    if prior == "L":
        q0 = lattice_seed(n, L_t + 0.45, rng)
    else:
        q0 = rsa_seed(n, L_t + 0.45, rng)
    q, f = ramp_settle(q0, L_t, steps=14)
    # LM best-effort (same as the engine pipeline)
    if f < 1e-5:
        q, _ = exactify(q, L_t)
        f = float(np.sum(np.maximum(
            np.concatenate([
                np.maximum(sat_stack(q[:n], q[n:2*n], q[2*n:])[0]
                           .min(axis=0)[np.triu_indices(n, 1)] + 1e-9, 0),
                np.maximum(out_amounts(q[:n], q[n:2*n], hw(q[2*n:]), L_t)
                           .flatten() + 1e-9, 0)]), 0) ** 2))
    m = q.size // 3
    TH = q[2 * m:] % (math.pi / 2)
    st = [(float(q[i]), float(q[m + i]), float(TH[i])) for i in range(m)]
    stf, rf = P.finalize(st, gap=2e-9)
    gate = bool(rf["ok"] and rf["worst_pen"] <= -1e-12)
    return f, gate, (round(rf["L"], 12) if rf["ok"] else None)


def main():
    res = {}
    for prior in ("L", "R"):
        for d in (0.001, 0.0005, 0.0002, 0.0001, 0.00005):
            L_t = round(4.0 - d, 8)
            fs, gates = [], []
            for s in range(1, 9):
                f, gate, Lf = probe_one(12, L_t, 7919 * 12 + s + int(d * 1e6),
                                        prior)
                fs.append(f)
                gates.append(gate)
            res[f"{prior}_d{d}"] = {"target": L_t, "best_f": min(fs),
                                    "median_f": sorted(fs)[4],
                                    "gates": sum(gates),
                                    "f_all": [round(x, 12) for x in fs]}
            print(f"n=12 {prior} @ {L_t}: best_f {min(fs):.2e} median "
                  f"{sorted(fs)[4]:.2e} | gate hits {sum(gates)}/8", flush=True)
    json.dump(res, open(OUT, "w"), indent=1)
    print("saved")


if __name__ == "__main__":
    main()
