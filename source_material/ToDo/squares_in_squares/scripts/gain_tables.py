#!/usr/bin/env python3
"""gain_tables.py — Run 7 quantification. All arithmetic in code, printed
and saved to download/run7_gain_tables.json.

1. Class scenario table: score if the 69 LOW / 433 MID (all still at
   grid) moved to grid-eps for eps in {0.002, 0.02, 0.1} — separately,
   and combined; with the resulting leaderboard-style score.
2. Leader-gap decomposition: platform 23.193864 vs leader 22.0544214515
   (user-reported, 2026-11-04); the total gap, the per-puzzle requirement
   over our 593 open and over the user's 502-open figure; the same for
   our local 23.173640.
3. Per-band mean requirement: for each class, the mean eps needed at
   grid so the class alone closes the leader gap.
4. Cascade leverage recap (from Run 6's constructive verification).
"""
import json
import math
from math import ceil, sqrt

TAB = json.load(open("/home/z/my-project/workspace/submission/table.json"))
AUD = json.load(open("/home/z/my-project/download/residue_audit.json"))
OUT = "/home/z/my-project/download/run7_gain_tables.json"

PLATFORM = 23.193864
LEADER = 22.0544214515
LOCAL = 23.173640


def grid_L(n):
    return ceil(sqrt(n))


def classes():
    out = {"LOW": [], "MID": [], "SQ": [], "NAG": []}
    for row in AUD["rows"]:
        out[row["class"]].append(row["n"])
    return out


def scenario(n_list, eps):
    """sum over the listed (still grid) puzzles of (grid-eps)/sqrt(n)-1
    replacing grid/sqrt(n)-1: the delta is -eps/sqrt(n)."""
    return -sum(eps / sqrt(n) for n in n_list)


def main():
    cls = classes()
    low, mid = cls["LOW"], cls["MID"]
    nag = AUD["classes"]["NAG"]
    sq = AUD["classes"]["SQ"]
    res = {"inputs": {"platform": PLATFORM, "leader": LEADER, "local": LOCAL,
                      "classes": {"SQ": sq, "NAG": nag, "LOW": len(low),
                                  "MID": len(mid)}}}

    print("=== 1. class scenario table (delta score, all at grid -> grid-eps) ===")
    rows = []
    for eps in (0.002, 0.02, 0.1):
        d_low = scenario(low, eps)
        d_mid = scenario(mid, eps)
        d_all = d_low + d_mid
        s_low = LOCAL + d_low
        s_mid = LOCAL + d_mid
        s_all = LOCAL + d_all
        r = {"eps": eps,
             "delta_LOW": round(d_low, 6), "delta_MID": round(d_mid, 6),
             "delta_all_open": round(d_all, 6),
             "score_after_LOW": round(s_low, 6), "score_after_MID": round(s_mid, 6),
             "score_after_all": round(s_all, 6),
             "beats_leader_LOW": s_low < LEADER, "beats_leader_MID": s_mid < LEADER,
             "beats_leader_all": s_all < LEADER}
        rows.append(r)
        print(f"  eps={eps}: LOW d={d_low:+.6f} -> {s_low:.6f} | "
              f"MID d={d_mid:+.6f} -> {s_mid:.6f} | all d={d_all:+.6f} -> {s_all:.6f} "
              f"(leader 22.054421: LOW{'WIN' if r['beats_leader_LOW'] else 'no'} "
              f"MID{'WIN' if r['beats_leader_MID'] else 'no'} "
              f"all{'WIN' if r['beats_leader_all'] else 'no'})")
    res["scenarios"] = rows

    print("\n=== 2. leader-gap decomposition ===")
    gap_platform = PLATFORM - LEADER
    gap_local = LOCAL - LEADER
    per_593 = gap_platform / 593
    per_502 = gap_platform / 502
    per_local_593 = gap_local / 593
    res["leader_gap"] = {
        "gap_platform": round(gap_platform, 6), "gap_local": round(gap_local, 6),
        "mean_eps_needed_per_puzzle_over_593": round(per_593 * 1, 6),
        "note_per_502": round(per_502, 6)}
    print(f"  platform - leader = {gap_platform:.6f}; local - leader = {gap_local:.6f}")
    print(f"  mean required (grid-eps) per open puzzle: over 593 open: "
          f"eps = {per_593:.6f}; over the user-cited 502 open: eps = {per_502:.6f}")
    print(f"  (for context: eps=0.002 over 593 gives {0.002*593:.2f} raw; "
          f"the mean of 1/sqrt(n) matters, hence the scenario table)")

    print("\n=== 3. mean eps needed per class to close the gap alone ===")
    mean_low = sum(1 / sqrt(n) for n in low) / len(low)
    mean_mid = sum(1 / sqrt(n) for n in mid) / len(mid)
    eps_low_alone = gap_platform / sum(1 / sqrt(n) for n in low)
    eps_mid_alone = gap_platform / sum(1 / sqrt(n) for n in mid)
    res["class_requirements"] = {
        "mean_inv_sqrt_LOW": round(mean_low, 6), "mean_inv_sqrt_MID": round(mean_mid, 6),
        "eps_if_LOW_alone": round(eps_low_alone, 6),
        "eps_if_MID_alone": round(eps_mid_alone, 6)}
    print(f"  LOW alone would need grid-eps with eps = {eps_low_alone:.4f} "
          f"(mean 1/sqrt(n) = {mean_low:.4f}; n range {min(low)}..{max(low)})")
    print(f"  MID alone would need grid-eps with eps = {eps_mid_alone:.4f} "
          f"(mean 1/sqrt(n) = {mean_mid:.4f}; n range {min(mid)}..{max(mid)})")
    print("  (eps=0.1 is already infeasible for most MID by area: "
          "sqrt(n) headroom is ~0.63; so realistic MID eps <= ~0.6 max, "
          "0.1 is the honest planning bound)")

    print("\n=== 4. cascade leverage (Run 6, constructively verified) ===")
    res["cascade"] = AUD["leverage"]
    for lev in AUD["leverage"]:
        print(f"  from n={lev['from_n']}: m={lev['m']} L={round(lev['L'],6)} -> "
              f"m'={lev['m2']} (expect {lev['expect']}) in L'={round(lev['L2'],6)}, "
              f"pen={lev['pen']:.2e}, verified={lev['ok']}")

    print("\n=== 5. small-n base value (LOW band, smallest first) ===")
    base_rows = []
    for n in sorted(low)[:12]:
        d002 = -0.002 / sqrt(n)
        # downstream reach: how many jammed puzzles share n's block family
        k = int(math.floor(sqrt(n)))
        base_rows.append({"n": n, "k": k, "r": n - k * k,
                          "direct_delta_at_0.002": round(d002, 8)})
        print(f"  n={n} (k={k}, r={n-k*k}): direct delta at grid-0.002 = {d002:+.8f}")
    res["small_bases"] = base_rows

    json.dump(res, open(OUT, "w"), indent=1)
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
