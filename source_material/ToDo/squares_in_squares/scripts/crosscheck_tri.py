#!/usr/bin/env python3
"""Parse the triangular-table page (authoritative per-n list) and cross-check
against the realized table.json.

Triangular rows: 'N.' followed by '$s = ...$ desc' lines.  n without a row are
covered by the removal rule (not shown → neighbor minus squares).
Cross-check failure tri_s < realized_L - 1e-6  =>  missing record (fetch it).
"""
import json
import os
import re
import sys
from math import ceil, sqrt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

def parse_tri(path):
    h = open(path, errors="ignore").read()
    h = re.sub(r"<!--[\s\S]*?-->", " ", h)
    h = re.sub(r"<script[\s\S]*?</script>", " ", h)
    t = re.sub(r"<[^>]+>", " ", h)
    for r in ["&nbsp;", "&ensp;", "&thinsp;", "&emsp;"]:
        t = t.replace(r, " ")
    t = re.sub(r"[ \t]+", " ", t)
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    # data zone: from the line '1.' onwards
    start = next(i for i, l in enumerate(lines) if l == "1.")
    out = {}
    n = None
    for l in lines[start:]:
        m = re.match(r"^(\d+)\.$", l)
        if m:
            n = int(m.group(1))
            continue
        if n is None:
            continue
        ms = re.search(r"\\Nn\{([0-9.]+)\}", l)
        if ms is None:
            ms = re.search(r"^\$s = (\d+(?:\.\d+)?)\$", l)
        if ms is not None and n not in out:
            out[n] = float(ms.group(1))
            n = None
        elif re.match(r"^\d+\.", l):
            n = None
    return out

def main():
    tri = parse_tri("/tmp/aux_triangular_table_html.html")
    print(f"triangular rows: {len(tri)} (n up to {max(tri)})")
    tab = json.load(open("/home/z/my-project/workspace/submission/table.json"))
    missing = []
    matches = 0
    wins = []
    for n, s in sorted(tri.items()):
        if n > 1000:
            continue
        myL = tab[str(n)]["L"]
        if s < myL - 1e-6:
            missing.append((n, s, myL, tab[str(n)]["src"]))
        elif myL < s - 1e-6:
            wins.append((n, myL, s))
        else:
            matches += 1
    print(f"checked n<=1000: matches {matches}, tri-better {len(missing)}, mine-better {len(wins)}")
    for x in missing[:40]:
        print("  MISSING RECORD n=%d tri_s=%.9f myL=%.9f (%s)" % x)
    for x in wins[:20]:
        print("  MINE BETTER n=%d myL=%.9f tri_s=%.9f" % x)
    json.dump({str(n): s for n, s in tri.items()}, open("/home/z/my-project/workspace/tri_table.json", "w"))

if __name__ == "__main__":
    main()
