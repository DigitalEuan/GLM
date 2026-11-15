#!/usr/bin/env python3
"""Parse aux-page boxes (td structure) and cross-check n in [325, 1000].

Aux pages (strips/squares/rigid/n2nm1/compared) use:
  <td class="box"><font size="+3">LABEL.<br><a href="square-N.svg">
  ... <td class="desc"><font size="+1">$s = ... = \\Nn{DEC}$ ...
LABEL 'N.' or 'N, M.'; s from \\Nn{...} or $s = <num>$.
For every box: window = (floor(s)^2, n_pic] ∩ [325, 1000]; realize n by removal
from the parsed SVG if s < current table L.  Report any box whose s beats the
current table for some n in its window but whose SVG file is missing.
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
from build_table import drop_k, bbox_wh

PAGES = {
    "strips": "/tmp/aux_G_bel_strips_html.html",
    "squares": "/tmp/aux_G_bel_squares_html.html",
    "rigid": "/tmp/aux_rigid_html.html",
    "n2nm1": "/tmp/aux_n_2_n_1_html.html",
    "compared": "/tmp/aux_compared_html.html",
    "main": "/tmp/ellsworth.html",
}
ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

SVG_DIR = ROOT + "/workspace/svgs"

def strip_comments(h):
    return re.sub(r"<!--[\s\S]*?-->", " ", h)

def parse_td_boxes(h):
    boxes = []
    for chunk in h.split('<font size="+3">')[1:]:
        m = re.match(r"([\d,\s]+)\.<br>\s*<a href=\"(square-[\w]+\.svg)\"", chunk)
        if not m:
            continue
        ns = [int(x) for x in re.findall(r"\d+", m.group(1))]
        svg = m.group(2)
        # s value appears later in the chunk (desc cell)
        ms = re.search(r"\\Nn\{([0-9.]+)\}", chunk)
        if not ms:
            ms = re.search(r"\$s = (\d+(?:\.\d+)?)\$", chunk)
        if not ms:
            continue
        boxes.append({"ns": ns, "svg": svg, "s": float(ms.group(1))})
    return boxes

def main():
    cur = json.load(open(ROOT + "/workspace/submission/table.json"))
    allboxes = []
    for name, path in PAGES.items():
        h = strip_comments(open(path, errors="ignore").read())
        boxes = parse_td_boxes(h)
        print(f"{name}: {len(boxes)} td-boxes")
        allboxes += [{"page": name, **b} for b in boxes]
    # dedup
    seen = {}
    for b in allboxes:
        key = (tuple(b["ns"]), b["svg"], round(b["s"], 9))
        seen[key] = b
    boxes = list(seen.values())
    print(f"unique: {len(boxes)}")

    # which boxes could improve some n in [1,1000]?
    relevant = []
    for b in boxes:
        s = b["s"]
        n_pic = int(re.search(r"square-(\d+)", b["svg"]).group(1))
        lo = floor(s) ** 2 + 1
        hi = min(n_pic, 1000)
        if hi < lo:
            continue
        # does s beat current table for some n in window?
        beats = [n for n in range(lo, hi + 1) if s < cur[str(n)]["L"] - 1e-7]
        if beats:
            relevant.append((b, beats))
    print(f"boxes that beat current table somewhere: {len(relevant)}")
    missing = []
    for b, beats in relevant:
        f = os.path.join(SVG_DIR, b["svg"])
        if not os.path.exists(f):
            missing.append((b, beats))
            continue
        # realize: parse, remove down to each n in beats
        n_pic = int(re.search(r"square-(\d+)", b["svg"]).group(1))
        try:
            state, s_decl, prec = parse_one(f)
        except Exception as e:
            print(f"  PARSE FAIL {b['svg']}: {e}")
            continue
        if len(state) != n_pic:
            print(f"  COUNT {b['svg']}: {len(state)} != {n_pic}")
            continue
        for n in beats:
            k = n_pic - n
            res = drop_k(state, k)
            if not res:
                continue
            L, st = res[0]
            if L < cur[str(n)]["L"] - 1e-12:
                stf, rf = P.finalize(st, gap=2e-9)
                if rf["ok"] and rf["worst_pen"] <= 0:
                    cur[str(n)] = {"L": round(rf["L"], 12), "state": stf,
                                   "src": f"aux:{b['svg']}-{k}"}
                    print(f"  IMPROVED n={n} -> {rf['L']:.9f} via {b['svg']}")
                else:
                    print(f"  FINALIZE FAIL n={n} {b['svg']}")
    print(f"missing svgs for improving boxes: {len(missing)}")
    for b, beats in missing:
        print("  MISSING", b["svg"], "s=", b["s"], "beats", beats[:10])

    # save updated table
    json.dump(cur, open(ROOT + "/workspace/submission/table.json", "w"))
    tot = 0.0
    for n in range(1, 1001):
        L = cur[str(n)]["L"]
        tot += L / sqrt(n) - 1
    gt = sum(ceil(sqrt(n)) / sqrt(n) - 1 for n in range(1, 1001))
    print(f"SCORE={tot:.6f} (grid {gt:.6f}, improvement {gt - tot:.6f})")

if __name__ == "__main__":
    main()
