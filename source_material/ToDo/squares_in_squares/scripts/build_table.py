#!/usr/bin/env python3
"""build_table.py — reconstruct the state-of-the-art s(n) table for n ≤ 1000.

For each n: table[n] = min over
  (a) trivial grid: container ceil(sqrt(n)),
  (b) exact records: parsed survey SVGs (bbox = record side s),
  (c) removals: for every record box B (side s, N_pic squares), every n in the
      window W(B) = {n : floor(s)^2 < n <= N_pic, n <= 1000} is realizable by
      dropping N_pic - n squares (any subset of a valid packing is valid);
      greedy drop order minimizes the resulting bbox.

Window prune proof: for n <= floor(s)^2 we have grid(n) = ceil(sqrt(n))
<= floor(s) <= s, so B can never beat the grid there — only the window can.
Any survey label member with s < grid(n) lies in the window, so (a)+(b)+(c)
reproduces the complete survey table s(n) for n <= 1000.

Greedy removal: at each drop, remove the square whose removal most reduces
max(w, h) of the bbox (ties: smaller w+h); beam width BEAM over candidate
extreme squares (only squares on a bbox edge can change the bbox).

Each chosen state is finalized (clearance scale ~2e-9) and verified by packlib
before storage.  Output: table.json + report.
"""
import json
import os
import re
import sys
from math import ceil, floor, sqrt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "workspace", "tools"))
import packlib as P
from parse_all_svgs import parse_one

SVG_DIR = "/home/z/my-project/workspace/svgs"
OUT_JSON = "/home/z/my-project/workspace/submission/table.json"
BEAM = 4

# ---------------------------------------------------------------- helpers

def grid_state(n):
    k = ceil(sqrt(n))
    rows = ceil(n / k)
    st = [((i % k) + 0.5, (i // k) + 0.5, 0.0) for i in range(n)]
    return k, st

def bbox_wh(state):
    """(lox, loy, w, h) over square corner extents."""
    if not state:
        return 0.0, 0.0, 0.0, 0.0
    import math
    lo = [x - 0.5 * (abs(math.cos(t)) + abs(math.sin(t))) for x, y, t in state]
    hi = [x + 0.5 * (abs(math.cos(t)) + abs(math.sin(t))) for x, y, t in state]
    lov = [y - 0.5 * (abs(math.cos(t)) + abs(math.sin(t))) for x, y, t in state]
    hiv = [y + 0.5 * (abs(math.cos(t)) + abs(math.sin(t))) for x, y, t in state]
    return min(lo), min(lov), max(hi) - min(lo), max(hiv) - min(lov)

def drop_k(state, k):
    """greedy/beam removal of k squares minimizing final max(w,h).
    Returns list of remaining states explored, best-first (unique states)."""
    if k <= 0:
        return [(0, list(state))]
    # frontier: (container_upper_bound_so_far, state)  — we explore drop sequences
    # greedily; because each drop only shrinks the bbox, evaluate per step.
    results = []
    frontier = [list(state)]
    for step in range(k):
        nxt = []
        for st in frontier:
            # extremes on each edge
            import math
            ext = [0.5 * (abs(math.cos(t)) + abs(math.sin(t))) for x, y, t in st]
            right = max(x + e for (x, y, t), e in zip(st, ext))
            top = max(y + e for (x, y, t), e in zip(st, ext))
            left = min(x - e for (x, y, t), e in zip(st, ext))
            bot = min(y - e for (x, y, t), e in zip(st, ext))
            w = right - left
            h = top - bot
            # candidates: squares attaining the LARGE edge of max(w,h); if w==h both
            cands = set()
            if w >= h:
                for i, ((x, y, t), e) in enumerate(zip(st, ext)):
                    if x + e == right or x - e == left:
                        cands.add(i)
            if h >= w:
                for i, ((x, y, t), e) in enumerate(zip(st, ext)):
                    if y + e == top or y - e == bot:
                        cands.add(i)
            if not cands:
                continue
            scored = []
            for i in cands:
                st2 = st[:i] + st[i + 1:]
                if not st2:
                    continue
                lox, loy, w2, h2 = bbox_wh(st2)
                scored.append((max(w2, h2), w2 + h2, st2))
            scored.sort(key=lambda z: (z[0], z[1]))
            for sc in scored[:BEAM]:
                nxt.append(sc[2])
        if not nxt:
            break
        # dedup by rounded bbox signature
        seen = {}
        for st in nxt:
            lox, loy, w2, h2 = bbox_wh(st)
            sig = (round(lox, 9), round(loy, 9), round(w2, 9), round(h2, 9), len(st))
            if sig not in seen:
                seen[sig] = st
        frontier = list(seen.values())
    for st in frontier:
        lox, loy, w2, h2 = bbox_wh(st)
        results.append((max(w2, h2), st))
    results.sort(key=lambda z: z[0])
    return results

# ---------------------------------------------------------------- main

def main():
    # 1. parse all svg files (per-file map)
    files = sorted(f for f in os.listdir(SVG_DIR) if f.startswith("square-"))
    boxes = []   # {n_pic, state, s}
    nparse = 0
    for f in files:
        n = int(re.search(r"square-(\d+)", f).group(1))
        try:
            state, s_decl, prec = parse_one(os.path.join(SVG_DIR, f))
        except Exception as e:
            print(f"PARSE FAIL {f}: {e}")
            continue
        if len(state) != n:
            print(f"COUNT FAIL {f}: {len(state)} != {n}")
            continue
        boxes.append({"file": f, "n_pic": n, "state": state, "s": s_decl})
        nparse += 1
    print(f"parsed {nparse}/{len(files)} files", flush=True)

    # sanity: exact record bbox == s_decl
    for b in boxes:
        lox, loy, w, h = bbox_wh(b["state"])
        L = max(w, h)
        if L > b["s"] + 1e-6:
            print(f"  bbox EXCEEDS s: {b['file']} L={L:.9f} s={b['s']:.9f}")
        b["L0"] = L

    # 2. theoretical label table (cross-check)
    groups = json.load(open("/home/z/my-project/workspace/groups.json"))
    th = {}
    for n in range(1, 1001):
        th[n] = (float(ceil(sqrt(n))), "grid")
    for g in groups:
        s = g["s"]
        for n in g["ns"]:
            if n <= 1000 and s < th[n][0] - 1e-12:
                th[n] = (s, g["svg"])

    # 3. build realized candidates
    cand = {}   # n -> (container, state, src)
    for n in range(1, 1001):
        gL, gs = grid_state(n)
        cand[n] = (gL, gs, "grid")
    # exact records
    for b in boxes:
        n = b["n_pic"]
        if n <= 1000 and b["L0"] < cand[n][0] - 1e-12:
            cand[n] = (b["L0"], b["state"], f"exact:{b['file']}")
    # removal windows
    nw = 0
    for b in boxes:
        s = b["s"]
        f2 = floor(s) ** 2
        lo = f2 + 1
        hi = min(b["n_pic"], 1000)
        if hi <= lo:
            continue
        # only if s can beat grid for some n in window
        targets = [n for n in range(lo, hi + 1)
                   if s < cand[n][0] - 1e-12 or (n == b["n_pic"] and b["L0"] < cand[n][0] - 1e-12)]
        # include exact record target too (handled above); keep removal targets:
        targets = [n for n in range(lo, hi + 1) if n < b["n_pic"]]
        if not targets:
            continue
        nw += len(targets)
        # greedy removal from n_pic-1 down to lo: incremental (drop one more each time)
        # chain the drop sets: results for k+1 reuse frontier for k? do per target:
        for n in targets:
            k = b["n_pic"] - n
            res = drop_k(b["state"], k)
            if not res:
                continue
            L, st = res[0]
            if L < cand[n][0] - 1e-12:
                cand[n] = (L, st, f"removal:{b['file']}-{k}")
    print(f"removal targets tried: {nw}", flush=True)

    # 4. finalize + verify
    out = {}
    fails = []
    for n in range(1, 1001):
        L, st, src = cand[n]
        stf, rf = P.finalize(st, gap=2e-9)
        if not rf["ok"] or rf["worst_pen"] > 0:
            fails.append((n, src, rf["worst_pen"]))
            continue
        out[n] = {"L": round(rf["L"], 12), "state": stf, "src": src}
    print(f"finalized {len(out)}/1000, fails: {len(fails)}", flush=True)
    for f in fails[:10]:
        print("  FAIL", f, flush=True)

    # 5. report vs label-th
    worse = []
    better = []
    for n in range(1, 1001):
        if n in out:
            if out[n]["L"] > th[n][0] + 1e-6:
                worse.append((n, out[n]["L"], th[n]))
            elif out[n]["L"] < th[n][0] - 1e-6:
                better.append((n, out[n]["L"], th[n][0], out[n]["src"]))
    print(f"realized WORSE than label-th: {len(worse)}")
    for x in worse[:15]:
        print("  WORSE", x)
    print(f"realized BETTER than label-th: {len(better)}")
    for x in better[:15]:
        print("  BETTER", x)

    # 6. score
    tot = 0.0
    gt = 0.0
    beats = 0
    for n in range(1, 1001):
        g = ceil(sqrt(n))
        L = out[n]["L"] if n in out else g
        tot += L / sqrt(n) - 1
        gt += g / sqrt(n) - 1
        if L < g - 1e-9:
            beats += 1
    print(f"SCORE={tot:.6f} (grid {gt:.6f}, improvement {gt - tot:.6f}) BEATS_GRID={beats}")

    json.dump({str(n): {"L": v["L"], "state": v["state"], "src": v["src"]}
               for n, v in out.items()}, open(OUT_JSON, "w"))
    print(f"wrote {OUT_JSON}")

if __name__ == "__main__":
    main()
