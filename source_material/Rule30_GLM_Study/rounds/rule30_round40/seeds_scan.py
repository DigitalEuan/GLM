"""Round 40 hypothesis-engine run on To Do 46 (the open bit at even white diagonals).

For many random left-edge seeds, simulate the left band of Rule 30 (./transient), and record
the eventually white left diagonals, the parity of the outer neighbour, and the transients.
Hypotheses tested (stated before the run):
  H1  (theorem check) every seed has the same white diagonals up to and including the first
      white whose outer neighbour has EVEN parity (odd whites never branch).
  H2  at each even white the two branches occur with frequency ~1/2 across seeds (no law in
      the eventual data picks the branch).
  H3  transients are near-linear with slope ~1: tau(D) <= D + c for a small c, far below the
      proven bound 1 + D*Q.
"""
import json, random, subprocess, sys
from collections import Counter, defaultdict

W, T = int(sys.argv[1]) if len(sys.argv) > 1 else 600, int(sys.argv[2]) if len(sys.argv) > 2 else 8000
S = int(sys.argv[3]) if len(sys.argv) > 3 else 400
random.seed(40)

def run(seedhex):
    out = subprocess.run(["./transient", str(W), str(T), seedhex], capture_output=True, text=True).stdout
    rows = [tuple(map(int, l.split())) for l in out.split("\n") if l]
    return rows

def whites(rows):
    res = []
    for (D, Q, white, par, bit, tau) in rows:
        if white and D >= 1:
            outer = rows[D - 1]
            res.append((D, outer[1], outer[3]))  # (white D, outer period, outer parity)
    return res

seeds = ["1"] + [format(random.getrandbits(15) << 1 | 1, "x") for _ in range(S)]
data = {}
slope = []
unresolved = 0
for sh in seeds:
    rows = run(sh)
    if any(r[1] == 0 for r in rows[: W - 50]):
        unresolved += 1
        continue
    data[sh] = whites(rows)
    slope.append(max(r[5] - r[0] for r in rows[: W - 50]))

# H1: prefix up to first even white identical
prefixes = Counter()
for sh, ws in data.items():
    pre = []
    for (D, Q, p) in ws:
        pre.append((D, Q, p))
        if p == 0:
            break
    prefixes[tuple(pre)] += 1
# H2: branch statistics along the tree
tree = defaultdict(Counter)
for sh, ws in data.items():
    hist = ()
    for (D, Q, p) in ws:
        if hist and hist[-1][2] == 0:   # previous white even -> branch point
            tree[hist][(D, Q, p)] += 1
        hist = hist + ((D, Q, p),)
branch_report = []
for hist, cnt in sorted(tree.items(), key=lambda kv: -sum(kv[1].values()))[:12]:
    n = sum(cnt.values())
    branch_report.append({"after": [h[0] for h in hist], "n": n,
                          "outcomes": {f"white {k[0]} (Q={k[1]}, parity {k[2]})": v for k, v in cnt.items()}})
report = {
    "W": W, "T": T, "seeds": len(seeds), "resolved": len(data), "unresolved": unresolved,
    "seed_1_whites": data.get("1"),
    "H1_prefix_classes": [{"prefix": list(k), "count": v} for k, v in prefixes.most_common(6)],
    "H2_branch_points": branch_report,
    "H3_max_tau_minus_D": {"max": max(slope), "median": sorted(slope)[len(slope) // 2]},
}
print(json.dumps(report, indent=1))
json.dump(report, open("r40_seed_scan.json", "w"), indent=1)
