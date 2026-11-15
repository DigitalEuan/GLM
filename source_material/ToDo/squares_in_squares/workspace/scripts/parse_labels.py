#!/usr/bin/env python3
"""Parse label groups from the 5 survey pages.

Each picture box on the pages is:
    <div class="box"><font size="+3">LABEL<br><a href="square-N.svg">...</a>
    </font><div align="center"><font size="+1">$s = EXACT = \\Nn{DECIMAL}$ ...
LABEL is the comma-separated n-group (the SVG pictures the largest).
Commented-out boxes (<!-- -->) are superseded duplicates — strip first.

Output: groups.json = [{ns: [...], svg: "square-N.svg", s: decimal}, ...]
Cross-checks: label max == svg N; every n <= 1000; s > 0.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PAGES = {
    "main": "/tmp/ellsworth.html",
    "strips": "/tmp/aux_G_bel_strips_html.html",
    "squares": "/tmp/aux_G_bel_squares_html.html",
    "rigid": "/tmp/aux_rigid_html.html",
    "n2nm1": "/tmp/aux_n_2_n_1_html.html",
}

def strip_comments(h):
    return re.sub(r"<!--[\s\S]*?-->", " ", h)

def parse_boxes(h):
    boxes = []
    for chunk in h.split('<div class="box">')[1:]:
        # label: text after <font size="+3"> up to <br>
        m = re.search(r'<font size="\+3">([\s\S]*?)<br>', chunk)
        if not m:
            continue
        label = m.group(1)
        ns = [int(x) for x in re.findall(r"\d+", label)]
        if not ns:
            continue
        # svg href (first square-*.svg link)
        mh = re.search(r'href="(square-[\w]+\.svg)"', chunk)
        if not mh:
            continue
        svg = mh.group(1)
        # s decimal: \Nn{...} appears in the description; also plain $s = 3$
        ms = re.search(r"\\Nn\{([0-9.]+)\}", chunk)
        if ms:
            s = float(ms.group(1))
        else:
            ms2 = re.search(r"\$s = (\d+(?:\.\d+)?)\$", chunk)
            if ms2:
                s = float(ms2.group(1))
            else:
                continue
        boxes.append({"ns": ns, "svg": svg, "s": s, "label": label.strip()})
    return boxes

def main():
    all_boxes = []
    for pname, path in PAGES.items():
        if not os.path.exists(path):
            print(f"SKIP {pname}: {path} missing")
            continue
        h = strip_comments(open(path, errors="ignore").read())
        boxes = parse_boxes(h)
        print(f"{pname}: {len(boxes)} boxes")
        for b in boxes:
            n_pic = int(re.search(r"square-(\d+)", b["svg"]).group(1))
            if max(b["ns"]) != n_pic:
                print(f"  WARN {pname}: label max {max(b['ns'])} != svg N {n_pic} ({b['label']!r})")
        all_boxes += [{"page": pname, **b} for b in boxes]
    # dedup: same (ns-set, svg) from multiple pages — keep once (s identical)
    seen = {}
    for b in all_boxes:
        key = (tuple(b["ns"]), b["svg"])
        if key in seen:
            if abs(seen[key]["s"] - b["s"]) > 1e-9:
                print(f"  S-MISMATCH {key}: {seen[key]['s']} vs {b['s']}")
            continue
        seen[key] = b
    boxes = list(seen.values())
    print(f"total unique boxes: {len(boxes)}")
    # coverage sanity
    cover = {}
    for b in boxes:
        for n in b["ns"]:
            if n > 1000:
                continue
            cover[n] = min(cover.get(n, 1e9), b["s"])
    print(f"label coverage: {len(cover)} values of n <= 1000")
    missing_files = [b["svg"] for b in boxes
ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

                     if not os.path.exists(fROOT + "/workspace/svgs/{b['svg']}")]
    print(f"missing svg files: {missing_files or 'none'}")
    json.dump(boxes, open(ROOT + "/workspace/groups.json", "w"), indent=0)
    # quick distribution view
    for b in sorted(boxes, key=lambda x: max(x["ns"]))[:12]:
        print(" ", b["ns"], b["svg"], b["s"])
    print("  ...")
    for b in sorted(boxes, key=lambda x: max(x["ns"]))[-8:]:
        print(" ", b["ns"], b["svg"], b["s"])

if __name__ == "__main__":
    main()
