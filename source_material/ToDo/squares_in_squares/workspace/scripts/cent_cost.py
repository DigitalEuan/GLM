#!/usr/bin/env python3
"""cent_compiler cost metric + optimization-loop diff.
Vocabulary (22): atomic=sum neg mult scale accum rate wrap spatial exp log sat
hysteresis grad div_spatial curl delay; composite=recip div sqrt eq translinear state_space.
Usage: python3 cent_cost.py decomp.json
       python3 cent_cost.py --before v1.json --after v2.json
JSON: {"primitives": ["sum","mult",...]}
"""
import argparse, json, sys

ATOMIC = {"sum","neg","mult","scale","accum","rate","wrap","spatial","exp","log",
          "sat","hysteresis","grad","div_spatial","curl","delay"}
COMPOSITE = {"recip","div","sqrt","eq","translinear","state_space"}
VOCAB = ATOMIC | COMPOSITE

def count(path):
    spec = json.load(open(path))
    prims = spec.get("primitives", [])
    unknown = [p for p in prims if p not in VOCAB]
    a = sum(1 for p in prims if p in ATOMIC)
    c = sum(1 for p in prims if p in COMPOSITE)
    return prims, a, c, unknown

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("decomp", nargs="?")
    ap.add_argument("--before"); ap.add_argument("--after")
    args = ap.parse_args()
    if args.before and args.after:
        pb, ab, cb, ub = count(args.before)
        pa, aa, ca, ua = count(args.after)
        print(f"BEFORE: total={len(pb)} (atomic={ab}, composite={cb})" + (f" WARNING unknown: {ub}" if ub else ""))
        print(f"AFTER:  total={len(pa)} (atomic={aa}, composite={ca})" + (f" WARNING unknown: {ua}" if ua else ""))
        delta = len(pb) - len(pa)
        if delta > 0: print(f"REDUCED by {delta} — re-verify (Column 3 + Lean) before accepting.")
        elif delta == 0: print("NO REDUCTION — loop may stop.")
        else: print(f"REGRESSED by {-delta} — reject.")
        return 0 if delta >= 0 else 1
    if not args.decomp: ap.error("provide a decomp file or --before/--after")
    prims, a, c, unknown = count(args.decomp)
    print(f"primitives: total={len(prims)} (atomic={a}, composite={c})")
    if unknown: print(f"WARNING unknown: {unknown}"); return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
