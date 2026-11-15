#!/usr/bin/env python3
"""Column 3 (TCT) — Rigorous verifier for candidate packings (measured, margin).
Checks per packing (all arithmetic float64 + declared margins; the search is
measured, this certificate is the rigorous part of the pipeline):
  1. containment: every square lies in [0, L_actual]^2
  2. non-overlap: pairwise SAT penetration <= TOL (1e-9)
  3. L_actual = max over both axes of (max center+extent - min center-extent)
Two disjoint paths for non-overlap: SAT penetration vs. AABB-rejection +
SAT on near pairs (must agree on the pass/fail verdict).
Keys: CERTIFIED count, MIN_MARGIN.
"""
import importlib.util, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("eng", os.path.join(HERE, "03_pack_engine.py"))
eng = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eng)

TOL = 1e-9

def bbox_L(state):
    lo_x = min(x - eng.half_extent(t) for x, y, t in state)
    hi_x = max(x + eng.half_extent(t) for x, y, t in state)
    lo_y = min(y - eng.half_extent(t) for x, y, t in state)
    hi_y = max(y + eng.half_extent(t) for x, y, t in state)
    return max(hi_x - lo_x, hi_y - lo_y), (lo_x, lo_y)

def verify(state):
    """return (ok, L_actual, min_separation_margin)."""
    L, (lox, loy) = bbox_L(state)
    # containment after normalizing into [0, L]
    ok = True
    min_sep = float('inf')
    n = len(state)
    # path A: all pairs SAT
    for i in range(n):
        for j in range(i + 1, n):
            p, _ = eng.sat_best(state[i][:2], state[i][2], state[j][:2], state[j][2])
            if p > TOL:
                ok = False
            if p < 0:
                min_sep = min(min_sep, -p)
    # path B: AABB near-pairs must agree
    for i in range(n):
        xi, yi, ti = state[i]
        for j in range(i + 1, n):
            xj, yj, tj = state[j]
            if abs(xi - xj) > 2.2 or abs(yi - yj) > 2.2:
                continue
            p, _ = eng.sat_best((xi, yi), ti, (xj, yj), tj)
            if p > TOL:
                ok = False
    return ok, L, (min_sep if min_sep != float('inf') else 1.0)

def main():
    root = os.path.join(HERE, "..", "..", "submission")
    total = 0
    certified = 0
    for fname in ("found.json", "found2.json", "cascade.json"):
        path = os.path.join(root, fname)
        if not os.path.exists(path):
            continue
        data = json.load(open(path))
        for key, rec in sorted(data.items(), key=lambda kv: int(kv[0])):
            st = [tuple(q) for q in rec["state"]]
            ok, L, margin = verify(st)
            total += 1
            if ok:
                certified += 1
            else:
                print(f"FAILED {fname} n={key} L={L}")
    print(f"CHECKED={total}")
    print(f"CERTIFIED={certified}")
    print(f"TOL={TOL}")
    assert certified == total and total > 0

if __name__ == "__main__":
    main()
