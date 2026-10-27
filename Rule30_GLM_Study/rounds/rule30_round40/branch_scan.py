"""Round 40, hypothesis engine on To Do 46: which branch do left-edge rows take at an even
white diagonal?  Uses ./bandfast (bit-packed band, exact settling certificate row(t)=row(t-64)).

H1 (prediction of the Round 40 theorem `next_white_independent_of_odd_bit`): every left-edge
   row has the white diagonals 2, 7, 28, 399, 53207 (all whites up to the first even one).
H2 at the even white 53207 the two branches are taken by roughly half of the rows each.
H4 the branch at 53207 is not predicted by simple features of the seed (popcount parity,
   width parity, the seed's bit 1).
"""
import json, random, subprocess, sys
from collections import Counter

W = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
S = int(sys.argv[2]) if len(sys.argv) > 2 else 300
random.seed(4040)

def run(seedhex):
    out = subprocess.run(["./bandfast", str(W), seedhex], capture_output=True, text=True).stdout
    settled, whites = None, []
    for l in out.split("\n"):
        p = l.split()
        if not p: continue
        if p[0] == "SETTLED": settled = int(p[1])
        if p[0] == "WHITE": whites.append((int(p[1]), int(p[2]), int(p[3])))
    return settled, whites

seeds = ["1"]
while len(seeds) < S + 1:
    width = random.randint(2, 40)
    s = format(random.getrandbits(width - 1) << 1 | 1, "x")
    if s not in seeds: seeds.append(s)
rows = {}
for s in seeds:
    rows[s] = run(s)
pref = Counter(); after = Counter(); feats = {"popcount_parity": Counter(), "bit1": Counter()}
settle_ratio = []
for s, (ts, ws) in rows.items():
    settle_ratio.append(ts / W)
    first_even = next((i for i, w in enumerate(ws) if w[2] == 0), None)
    pre = tuple(w[0] for w in ws[: (first_even + 1 if first_even is not None else len(ws))])
    pref[pre] += 1
    if first_even is not None and first_even + 1 < len(ws):
        nxt = ws[first_even + 1]
        key = (ws[first_even][0], nxt[0], nxt[2])
    else:
        key = (ws[first_even][0] if first_even is not None else None, None, None)
    after[key] += 1
    v = int(s, 16)
    feats["popcount_parity"][(bin(v).count("1") % 2, key)] += 1
    feats["bit1"][((v >> 1) & 1, key)] += 1
report = {
    "W": W, "rows": len(rows),
    "seed_1": rows["1"],
    "H1_prefixes_up_to_first_even_white": {str(list(k)): v for k, v in pref.most_common(5)},
    "H2_branch_after_first_even_white": {str(k): v for k, v in after.most_common(10)},
    "H4_features": {f: {str(k): v for k, v in c.most_common()} for f, c in feats.items()},
    "settle_time_over_W": {"min": min(settle_ratio), "max": max(settle_ratio)},
}
print(json.dumps(report, indent=1))
json.dump(report, open("r40_branch_scan.json", "w"), indent=1)
