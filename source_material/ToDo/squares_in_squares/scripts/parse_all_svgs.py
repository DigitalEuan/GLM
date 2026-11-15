#!/usr/bin/env python3
"""Parse all Ellsworth SVGs into high-precision packings, verify, store.

Pipeline per SVG square-N.svg:
  1. parse with tools/parse_svg_packing (Decimal, auto precision)
  2. convert to float state [(x, y, theta)], x/y normalized to [0, s]
  3. verify with packlib (worst_pen <= tol)  [note: parsed packings touch
     exactly; worst_pen ~ 0 or slightly negative]
  4. finalize with a 1e-9-ish clearance scale, then round to 12 dp
  5. save to workspace/submission/records.json

Also extracts the entity s (container side) per n and compares with bbox L.
"""
import json
import math
import os
import re
import sys
from decimal import Decimal, getcontext

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "workspace", "tools"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "workspace"))

import packlib as P

import parse_svg_packing as PS

SVG_DIR = "/home/z/my-project/workspace/svgs"
OUT = "/home/z/my-project/workspace/submission/records.json"

def parse_one(path):
    squares, entities, prec, centered = PS.parse_svg(path, 0)
    s_val = Decimal(entities["s"])
    half_s = s_val / Decimal(2)
    if centered:
        half_s = Decimal(0)
    getcontext().prec = prec + 20
    from decimal import Decimal as D
    pi_hp = PS.hp_pi(prec)
    out = []
    for sq in squares:
        # replicate the tool's __main__ transforms:
        x = sq["x"]; y = sq["y"]
        x = (x - half_s)
        y = -(y - half_s)
        th = pi_hp / D(2) - sq["theta"]
        # normalize angle to (-pi/2, pi/2] range used by the tool:
        th = (th + pi_hp) % (pi_hp / D(2))
        out.append((float(x), float(y), float(th)))
    return out, float(s_val), prec

def main():
    files = sorted(f for f in os.listdir(SVG_DIR) if f.startswith("square-"))
    store = {}
    report = []
    for f in files:
        n = int(re.search(r"square-(\d+)", f).group(1))
        try:
            state, s_decl, prec = parse_one(os.path.join(SVG_DIR, f))
        except Exception as e:
            report.append((n, "PARSE_FAIL", str(e)[:80]))
            continue
        if len(state) != n:
            # SVG may picture the largest of a group (e.g. "7, 8" pictured as 8):
            # allow n_picture >= n_label? No: file square-N has exactly N in practice.
            report.append((n, "COUNT", f"got {len(state)} squares, expected {n}"))
            continue
        r = P.verify(state)
        gap_needed = max(0.0, r["worst_pen"])
        # finalize: scale to open clearance, round 12dp
        st, r2 = P.finalize(state, gap=2e-9)
        if not r2["ok"] or r2["worst_pen"] > 0:
            report.append((n, "VERIFY_FAIL", f"pen={r2['worst_pen']:.2e} L={r2['L']:.9f} decl={s_decl:.9f}"))
            continue
        L = r2["L"]
        if L > s_decl + 1e-7 * max(1, s_decl):
            report.append((n, "L_MISMATCH", f"L={L:.9f} > decl s={s_decl:.9f}"))
        if n not in store or L < store[n]["L"] - 1e-12:
            store[n] = {"L": round(L, 12), "s_decl": s_decl, "state": st,
                        "prec": prec, "file": f}
        report.append((n, "OK", f"L={L:.9f} decl={s_decl:.9f} pen={r2['worst_pen']:.1e} squares={len(st)}"))
    json.dump({str(k): {"L": v["L"], "state": v["state"]} for k, v in store.items()},
              open(OUT, "w"))
    ok = sum(1 for x in report if x[1] == "OK")
    print(f"parsed {ok}/{len(files)} OK")
    for x in report:
        if x[1] != "OK":
            print("  ISSUE", x)
    return store, report

if __name__ == "__main__":
    main()
