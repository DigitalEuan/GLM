#!/usr/bin/env python3
r"""disj_census.py — where the disjunctive (SAT) model's difficulty lives.

The exact model the review asks about is, for squares i, j with frames
(u_i, v_i), (u_j, v_j) and h_i(q) = (|q.u_i| + |q.v_i|)/2:

    non-overlap(i,j)  <=>  exists q in {u_i, v_i, u_j, v_j}:
                                  |(c_j - c_i).q| >= h_i(q) + h_j(q)

plus containment, minimising L over the 3n poses.  That condition is *exactly*
what `packlib.verify` evaluates (its docstring states the same min-over-4-axes
penetration), so the model is already the project's gate -- what was never run is
the disjunctive OPTIMISATION, and this census measures why.

For each delivered row it reports, over all n(n-1)/2 pairs:
  * tight pairs      pen <= TIGHT: pairs whose disjunction is load-bearing,
  * the axis that resolves each tight pair (of the four),
  * the branch count 4^pairs of the naive enumeration.

Reading: only the tight pairs constrain the model; every other pair is slack, so
the combinatorics of the disjunction is the combinatorics of the contact set --
which 17/18 showed carries no score information (ladder rungs 4-5).
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sqscore as SQ  # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/disj_census.json")
TIGHT = 1e-9


def census(n):
    st = SQ.load()[n]
    xy = np.array([(float(s[0]), float(s[1])) for s in st])
    th = np.array([float(s[2]) for s in st])
    cs, sn = np.cos(th), np.sin(th)
    m = len(st)
    PU = np.stack([cs, sn], axis=1) @ xy.T          # c_j . u_i
    PV = np.stack([-sn, cs], axis=1) @ xy.T         # c_j . v_i
    Eu = 0.5 * (np.abs(np.outer(cs, cs) + np.outer(sn, sn))
                + np.abs(np.outer(-sn, cs) + np.outer(cs, sn)))
    dU = np.diag(PU)[:, None] - PU
    dV = np.diag(PV)[:, None] - PV
    fam0 = np.minimum(0.5 + Eu - np.abs(dU), 0.5 + Eu - np.abs(dV))
    fam1 = np.minimum(0.5 + Eu.T - np.abs(dU.T), 0.5 + Eu.T - np.abs(dV.T))
    pen = np.minimum(fam0, fam1)
    iu = np.triu_indices(m, k=1)
    p = pen[iu]
    tight = np.abs(p) <= TIGHT
    # which of the four axes resolves each pair (0=u_i, 1=v_i, 2=u_j, 3=v_j)
    S = np.stack([0.5 + Eu - np.abs(dU), 0.5 + Eu - np.abs(dV),
                  0.5 + Eu.T - np.abs(dU.T), 0.5 + Eu.T - np.abs(dV.T)])
    win = np.argmin(S, axis=0)[iu]
    counts = [int((win[tight] == k).sum()) for k in range(4)]
    return {"n": n, "pairs": int(len(p)), "tight": int(tight.sum()),
            "tight_frac": float(tight.mean()), "axis_counts": counts,
            "slack_pairs": int((p < -1e-3).sum()),
            "log10_branches": round(len(p) * math.log10(4), 1),
            "worst_pen": float(p.max())}


def main() -> int:
    rows = [census(n) for n in (10, 11, 25, 50, 100, 200, 500, 1000)]
    print(f"{'n':>5} {'pairs':>7} {'tight':>6} {'tight%':>7} {'slack':>6} "
          f"{'4^pairs':>9} {'axes u_i v_i u_j v_j'}")
    for r in rows:
        print(f"{r['n']:5d} {r['pairs']:7d} {r['tight']:6d} "
              f"{100*r['tight_frac']:6.2f}% {r['slack_pairs']:6d} "
              f"1e{r['log10_branches']:8.1f} {r['axis_counts']}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"run": 64, "schema": "disj/1", "tight_tol": TIGHT,
                   "rows": rows}, f, indent=1)
    print(f"\nledger: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
