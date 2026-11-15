#!/usr/bin/env python3
"""area_recal.py — Run 8 execution: recalibrate the value ladder with the
AREA BOUND. The Run 7 plan's Table 2 assumed L = k - 0.1 for ALL 433 MID;
but the container must satisfy L >= sqrt(n) by area, and for n close to
k^2 (residue near 2k-2), (k-0.1)^2 < n: those puzzles can NEVER reach
k - 0.1, at any level of construction skill. This script computes, all
in code:

1. Per open class: which n are area-capped at depth 0.1 (n > (k-0.1)^2),
   and their best conceivable L = sqrt(n) (the bound itself).
2. Recalibrated scenarios: every open puzzle at L = max(k - eps, sqrt(n))
   for eps in {0.002, 0.02, 0.1} — the honest CEILING of each depth class.
3. The leader implication: given the area cap, what must the leader
   (22.0544214515) have beyond grid-0.1-class? Solve for the uniform
   depth d* such that 'all open at max(k-d, sqrt(n))' hits the leader
   exactly; if even d -> 1 (L = max(k-1, sqrt(n))... capped by area only
   in the limit d = k - sqrt(n) per puzzle, i.e. L = sqrt(n) for all)
   is needed, the leader is beyond any uniform-push model.
4. Absolute floor: score if every OPEN puzzle hit its area bound exactly
   (closed puzzles stay as-is) — the hard ceiling for ANY method.

All arithmetic printed and saved to download/run8_area_recal.json."""
import json
from math import ceil, sqrt

AUD = json.load(open("/home/z/my-project/download/residue_audit.json"))
TAB = json.load(open("/home/z/my-project/workspace/submission/table.json"))
OUT = "/home/z/my-project/download/run8_area_recal.json"

LEADER = 22.0544214515
LOCAL = 23.173640


def main():
    rows = AUD["rows"]
    res = {}

    # class lists
    cls = {"LOW": [], "MID": [], "SQ": [], "NAG": []}
    for r in rows:
        cls.setdefault(r["class"], []).append(r["n"])
    low, mid = cls["LOW"], cls["MID"]
    open_all = low + mid
    closed = 1000 - len(open_all)   # SQ + NAG + covered-below-grid
    print(f"open: LOW {len(low)}, MID {len(mid)}; "
          f"grid-tied total {len(open_all)}")

    # 1. area cap at 0.1
    print("\n=== 1. area cap: can n even reach k-0.1? (need n <= (k-0.1)^2) ===")
    caps = {}
    for name, lst in (("LOW", low), ("MID", mid)):
        capped = []
        for n in lst:
            k = ceil(sqrt(n))
            if n > (k - 0.1) ** 2:
                capped.append(n)
        caps[name] = capped
        print(f"  {name}: {len(capped)}/{len(lst)} area-capped at 0.1 "
              f"(best conceivable L = sqrt(n)); "
              f"headroom k-sqrt(n) of the worst 5: "
              + ", ".join(f"{n}:{ceil(sqrt(n))-sqrt(n):.3f}"
                          for n in sorted(capped,
                                          key=lambda n: ceil(sqrt(n)) - sqrt(n))[:5]))
    res["area_capped_at_0.1"] = {k: v for k, v in caps.items()}

    # 2. recalibrated scenarios: L = max(k - eps, sqrt(n)) per open puzzle
    print("\n=== 2. recalibrated scenario CEILINGS (open at max(k-eps, sqrt n)) ===")
    scen = []
    for eps in (0.002, 0.02, 0.1):
        tot = 0.0
        det = {"LOW": 0.0, "MID": 0.0}
        for name, lst in (("LOW", low), ("MID", mid)):
            for n in lst:
                k = ceil(sqrt(n))
                L = max(k - eps, sqrt(n))
                det[name] += L / sqrt(n) - 1
        # closed puzzles unchanged: their contribution = current - open part
        cur_open = sum(TAB[str(n)]["L"] / sqrt(n) - 1 for n in open_all)
        cur_closed = LOCAL_TOTAL() - cur_open
        tot = cur_closed + det["LOW"] + det["MID"]
        r = {"eps": eps, "LOW": round(det["LOW"], 6), "MID": round(det["MID"], 6),
             "score_ceiling": round(tot, 6),
             "beats_leader": tot < LEADER}
        scen.append(r)
        print(f"  eps={eps}: LOW {det['LOW']:+.6f} MID {det['MID']:+.6f} "
              f"-> score ceiling {tot:.6f} "
              f"({'beats leader' if tot < LEADER else 'ABOVE leader'})")
    res["scenarios"] = scen

    # 3. leader implication: uniform depth d* hitting the leader
    print("\n=== 3. leader implication ===")
    cur_open = sum(TAB[str(n)]["L"] / sqrt(n) - 1 for n in open_all)
    cur_closed = LOCAL_TOTAL() - cur_open

    def score_at(d):
        s = cur_closed
        for n in open_all:
            k = ceil(sqrt(n))
            L = max(k - d, sqrt(n))
            s += L / sqrt(n) - 1
        return s

    lo_d, hi_d = 0.0, 3.0
    if score_at(hi_d) > LEADER:
        print(f"  even uniform depth {hi_d} (capped by area) gives "
              f"{score_at(hi_d):.6f} > leader {LEADER}: the leader is "
              "beyond ANY uniform-push model; requires per-n constructions "
              "beating the area-capped uniform ceiling on a subset.")
        res["leader"] = {"uniform_depth_needed": None,
                         "note": "beyond uniform model"}
    else:
        for _ in range(60):
            mid_d = (lo_d + hi_d) / 2
            if score_at(mid_d) > LEADER:
                lo_d = mid_d
            else:
                hi_d = mid_d
        d_star = (lo_d + hi_d) / 2
        print(f"  uniform depth needed to MATCH the leader: "
              f"d* = {d_star:.6f} (score {score_at(d_star):.6f})")
        res["leader"] = {"uniform_depth_needed": round(d_star, 6)}
    # sanity: absolute floor for open (area bound exact)
    floor = cur_closed + sum(sqrt(n) / sqrt(n) - 1 for n in open_all)
    print(f"  absolute floor (open at sqrt(n) exactly): {floor:.6f}")
    res["floor"] = round(floor, 6)

    # 4. where can the leader's 1.12 advantage live at all?
    #    per-class maximum beyond current, area-capped at generous 0.5:
    print("\n=== 4. max available beyond current (per class, generous cap 0.5) ===")
    for name, lst in (("LOW", low), ("MID", mid)):
        cur = sum(TAB[str(n)]["L"] / sqrt(n) - 1 for n in lst)
        best = sum(max(ceil(sqrt(n)) - 0.5, sqrt(n)) / sqrt(n) - 1 for n in lst)
        print(f"  {name}: current {cur:.4f}; best-at-0.5-cap {best:.4f}; "
              f"available {cur - best:+.4f}")
        res.setdefault("available", {})[name] = {
            "current": round(cur, 4), "best_0.5": round(best, 4),
            "available": round(cur - best, 4)}

    json.dump(res, open(OUT, "w"), indent=1)
    print("\nwrote", OUT)


def LOCAL_TOTAL():
    """current local total score, recomputed from the table."""
    return sum(TAB[str(n)]["L"] / sqrt(n) - 1 for n in range(1, 1001))


if __name__ == "__main__":
    main()
