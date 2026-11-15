#!/usr/bin/env python3
r"""run9_ledger.py — the Run 9 outcomes ledger + refreshed gain tables.

Inputs (all measured this run):
  - gobel2_results.json  (the 68 applied family finds, 0 verify-fails)
  - table.json (post-propagation fixpoint)
  - residue_audit.json (regenerated)
Outputs:
  - download/run9_outcomes.json  (the honest ledger)
  - download/run9_gain_tables.json (value ladder on the NEW frontier)
"""
import json
from math import sqrt

TAB = "/home/z/my-project/workspace/submission/table.json"
tab = json.load(open(TAB))

# ---- classify the current table --------------------------------------
rows = []
for n in range(1, 1001):
    L = tab[str(n)]["L"]
    src = tab[str(n)].get("src", "?")
    q = int(sqrt(n))
    while (q + 1) ** 2 <= n:
        q += 1
    r = n - q * q
    grid = q + 1 if r > 0 else q
    rows.append({"n": n, "q": q, "r": r, "grid": grid, "L": L, "src": src,
                 "depth": grid - L})

sq = [t for t in rows if t["r"] == 0]
nag = [t for t in rows if t["r"] in (2 * t["q"] - 1, 2 * t["q"])]
low = [t for t in rows if 1 <= t["r"] <= 18 and t not in sq and t not in nag]
mid = [t for t in rows if 19 <= t["r"] <= 2 * t["q"] - 2]
low_open = [t for t in low if t["depth"] <= 1e-6]
mid_open = [t for t in mid if t["depth"] <= 1e-6]

score = sum(t["L"] / sqrt(t["n"]) - 1 for t in rows)
beats = sum(1 for t in rows if t["depth"] > 1e-6)

# ---- value ladder on the new frontier --------------------------------
def band_sum(band, eps):
    tot = 0.0
    for t in band:
        if t["depth"] <= 1e-6:  # still open
            L = max(t["q"] + 1 - eps, sqrt(t["n"]))
            tot += L / sqrt(t["n"]) - 1
        else:
            tot += t["L"] / sqrt(t["n"]) - 1
    return tot

scen = []
for eps in (0.002, 0.02, 0.1):
    s_low = band_sum(low, eps)
    s_mid = band_sum(mid, eps)
    tot = s_low + s_mid + sum(t["L"] / sqrt(t["n"]) - 1 for t in sq + nag)
    scen.append({"eps": eps, "LOW": round(s_low, 6), "MID": round(s_mid, 6),
                 "score_ceiling": round(tot, 6),
                 "beats_leader": tot < 22.0544214515})

# leader depth fit (uniform, area-respecting) on the open band
opens = [t for t in low + mid if t["depth"] <= 1e-6]
lo, hi = 0.0, 1.0
base = sum((t["L"] if t["depth"] > 1e-6 else t["grid"]) / sqrt(t["n"]) - 1
           for t in rows)
def total_at(d):
    tot = 0.0
    for t in rows:
        if t["depth"] > 1e-6:
            tot += t["L"] / sqrt(t["n"]) - 1
        else:
            tot += max(t["grid"] - d, sqrt(t["n"])) / sqrt(t["n"]) - 1
    return tot
for _ in range(60):
    m = (lo + hi) / 2
    if total_at(m) > 22.0544214515:
        lo = m
    else:
        hi = m
d_star = (lo + hi) / 2

out = {
    "run": 9,
    "score": round(score, 6),
    "prev_score": 23.17364,
    "gain": round(23.17364 - score, 6),
    "beats_grid": beats,
    "prev_beats_grid": 407,
    "class_counts": {
        "SQ": len(sq), "NAG": len(nag),
        "LOW_total": len(low), "LOW_open": len(low_open),
        "MID_total": len(mid), "MID_open": len(mid_open),
        "MID_below_grid": len(mid) - len(mid_open)},
    "platform_gain": round(23.193864 - score, 6),
    "gobel2": {
        "applied": 68,
        "verify_fails": 0,
        "tested_prefiltered": 326,
        "direct_MID": 17,
        "direct_LOW": 51},
    "propagation": {"cascade3_chains": 81, "closure_round1": 44},
    "wave2_negatives": [
        "mixed-wedge 45-degree serration rows: wash — row areal density "
        "~0.707 in the hypotenuse band exactly cancels the lost staircase "
        "depth (per-wedge net ~ -1 at a1=15)",
        "asymmetric pair splits (a1 != a2): split-invariant at n_max — "
        "verified across the full split range at s=31 (every split lands "
        "n ~= 930); the iso-n curve is a consequence of the symmetric "
        "contact+bbox constraint exchange",
        "side-band squares in unbalanced regimes: degenerate at the "
        "balanced optimum (all three constraints ~tight, slack < 1)"],
    "scenarios": scen,
    "leader_uniform_depth": round(d_star, 6),
    "open_band": {"LOW": len(low_open), "MID": len(mid_open)},
}
json.dump(out, open("/home/z/my-project/download/run9_outcomes.json", "w"),
          indent=1)
json.dump({"scenarios": scen, "leader_depth": round(d_star, 6),
           "open_counts": {"LOW": len(low_open), "MID": len(mid_open)}},
          open("/home/z/my-project/download/run9_gain_tables.json", "w"),
          indent=1)
print(json.dumps(out, indent=1)[:2400])
