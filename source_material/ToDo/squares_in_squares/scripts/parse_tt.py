#!/usr/bin/env python3
r"""parse_tt.py — extract every shown (n, s) pair from the triangular table.

The page is fetched once with curl into `workspace/raw/triangular_table.html`
(the in-app page reader truncates it near n = 324, curl does not).  Each entry
is a cell

    <div class="box"><font size="+3">146.<br><a href="square-146.svg"> ...
    <div class="desc"><font size="+1">$s = {}^{16}\Nn{12.60090777851301}$ ...

so the entry number leads the cell and the side length is the first `\Nn{...}`
(or a bare `$s = <number>$` for trivial entries) inside it.

Output: workspace/push/tt.json  {n: s}, s as the catalogue's own decimal.
This is a PARSER, not an authority: it is only a nomination source like every
other catalogue read in this project.  Nothing here enters the submission.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "workspace/raw/triangular_table.html")
OUT = os.path.join(ROOT, "workspace/push/tt.json")

CELL = '<div class="box"><font size="+3">'
NUM = re.compile(r"\s*\(?(\d+)\)?\.?\s*$")
VAL = re.compile(r"Nn\{([0-9]+(?:\.[0-9]+)?)\}")
BARE = re.compile(r"\$s\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*\$")


def parse(path: str = SRC) -> dict:
    html = open(path, encoding="utf-8", errors="replace").read()
    out, dup = {}, {}
    for chunk in html.split(CELL)[1:]:
        # the entry number is the text up to the first tag
        head = chunk.split("<", 1)[0]
        m = NUM.match(head.replace(" ", ""))
        if not m:
            continue
        n = int(m.group(1))
        body = chunk[:4000]
        v = VAL.search(body) or BARE.search(body)
        if not v:
            dup.setdefault(n, None)          # shown, value not parseable
            continue
        s = float(v.group(1))
        if n in out and abs(out[n] - s) > 1e-9:
            dup[n] = (out[n], s)
        out[n] = min(s, out.get(n, s))       # best known wins
    return out, dup


def main() -> int:
    if not os.path.exists(SRC):
        print(f"missing {SRC}; fetch it with:\n  curl -sS -o {SRC} "
              "https://kingbird.myphotos.cc/packing/squares_in_squares__"
              "triangular_table.html")
        return 1
    out, dup = parse()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({str(k): v for k, v in sorted(out.items())}, f, indent=0)
    ns = sorted(out)
    print(f"parsed {len(out)} shown rows, n = {ns[0]}..{ns[-1]}")
    print(f"NOTE: this page's own scope ends at n = {ns[-1]}; above that the "
          "catalogue lists only pictured records (gallery page).")
    missing = [n for n, v in dup.items() if v is None]
    print(f"shown but value not parseable: {missing}")
    amb = {n: v for n, v in dup.items() if isinstance(v, tuple)}
    print(f"cells with two different values (kept the smaller): "
          f"{ {n: v for n, v in list(amb.items())[:6]} } ... {len(amb)} total")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
