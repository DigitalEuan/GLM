#!/usr/bin/env python3
r"""extended_table.py — §3 artifact: upper-bound table for n in 1001..5000.

Memory-safe design:
  - grid: L = ceil(sqrt(n)); states are NOT stored (regenerable by the
    documented formula: cols=g, rows=n//g, partial row of rem).
  - records: the 4 kingbird catalogue SVGs (parsed Decimal-exact,
    packlib-verified, states kept).
  - göbel: family members in range, generated + verified, states kept.
  - closure: L_entry(n) = min L(real construction at m ≥ n). Validity is
    the removal theorem (dropping squares from a packing leaves a packing;
    the bbox cannot grow). Verified by construction at the base; sample
    spot-checks (every 50th entry) performed numerically as a guard.
  - +1 bound: s(n+1) <= s(n)+1 forward pass over the final best values
    (sound: one added square grows the bbox by at most 1).
Output: workspace/submission/extended_table_5000.json
  {n: {"L": best known L (state kept or theorem),
       "bound": min(L, +1-chain),
       "grid": grid L, "src": provenance, "state": [...] or null}}
"""
import json
import math
import os
import sys
from math import ceil, sqrt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "workspace", "tools"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "workspace"))

import packlib as P
from parse_all_svgs import parse_one
from gobel_squares import gobel_state

SQ2 = sqrt(2)
OUT = "/home/z/my-project/workspace/submission/extended_table_5000.json"
NMIN, NMAX = 1001, 5000


def finalize(state):
    boxes = []
    for (x, y, t) in state:
        ex = 0.5 * (abs(math.cos(t)) + abs(math.sin(t)))
        boxes.append((x - ex, x + ex, y - ex, y + ex))
    lox = min(b[0] for b in boxes); hix = max(b[1] for b in boxes)
    loy = min(b[2] for b in boxes); hiy = max(b[3] for b in boxes)
    cx, cy = (lox + hix) / 2, (loy + hiy) / 2
    out = [(q[0] - cx, q[1] - cy, q[2]) for q in state]
    return out, max(hix - lox, hiy - loy)


def spot_check(base_state, k, n):
    """Drop k squares arbitrarily (from the end), verify the result."""
    st = base_state[: len(base_state) - k]
    assert len(st) == n
    r = P.verify(st, tol=1e-9)
    assert r["ok"], (n, r)
    return r["L"]


def main():
    # working structures: constructions with real states
    real = {}  # n -> {"L", "state", "src"}
    # 1. grid L values (no states)
    gridL = {n: ceil(sqrt(n)) for n in range(NMIN, NMAX + 1)}
    # 2. records
    imported = []
    for n in (1453, 1765, 1850, 2043):
        state, s_decl, prec = parse_one(f"/tmp/sq_{n}.svg")
        assert len(state) == n, (n, len(state))
        st, r2 = P.finalize(state, gap=2e-9)
        assert r2["ok"] and r2["worst_pen"] <= 0, (n, r2)
        real[n] = {"L": round(r2["L"], 12), "state": st, "src": "catalogue:kingbird"}
        imported.append((n, round(r2["L"], 9)))
    # 3. göbel members
    gcount = 0
    for a in range(1, 80):
        for b in range(1, 200):
            n = 2 * a * (a + 1) + b * b
            if n < NMIN or n > NMAX:
                continue
            if not (a - 1 < b * SQ2 / 2 < a + 1):
                continue
            s = a + 1 + b * SQ2 / 2
            if s >= min(gridL[n], real.get(n, {}).get("L", 1e18)) - 1e-9:
                continue
            s_gen, st_gen = gobel_state(a, b)
            assert len(st_gen) == n
            stf, rf = P.finalize(st_gen, gap=2e-9)
            if not rf["ok"] or rf["worst_pen"] > 0:
                continue
            if rf["L"] < real.get(n, {}).get("L", 1e18) - 1e-12:
                real[n] = {"L": round(rf["L"], 12), "state": stf, "src": f"göbel:a{a}b{b}"}
                gcount += 1
    # 4. closure: prefix-min over real constructions; theorem + spot checks
    best = {}  # n -> (L, base_n, src)
    cur = None  # (L, base_n, src) of the best real packing at or above
    spots = 0
    for n in range(NMAX, NMIN - 1, -1):
        if n in real:
            if cur is None or real[n]["L"] < cur[0] - 1e-12:
                cur = (real[n]["L"], n, real[n]["src"])
        if cur is not None:
            best[n] = cur
    # spot checks: every 50th closure entry where base != n
    bases = {}
    for n, (L, m, src) in best.items():
        if m != n and (n % 50 == 0):
            bases.setdefault(m, real[m]["state"])
    for n, (L, m, src) in sorted(best.items()):
        if m != n and (n % 50 == 0):
            st = bases[m]
            got = spot_check(st, m - n, n)
            assert got <= L + 1e-9, (n, got, L)
            spots += 1
    # 5. +1 forward bound on final best
    final = {}
    for n in range(NMIN, NMAX + 1):
        cand = [gridL[n]]
        if n in real:
            cand.append(real[n]["L"])
        if n in best:
            cand.append(best[n][0])
        final[n] = min(cand)
    for n in range(NMIN + 1, NMAX + 1):
        if final[n - 1] + 1 < final[n] - 1e-12:
            final[n] = final[n - 1] + 1
    # assemble output (states only for real constructions)
    out = {}
    for n in range(NMIN, NMAX + 1):
        if n in real and final[n] >= real[n]["L"] - 1e-12:
            src, L, st = real[n]["src"], real[n]["L"], real[n]["state"]
        elif n in best and best[n][0] < gridL[n] - 1e-12 and (n not in real or best[n][0] < real[n]["L"] - 1e-12):
            src, L, st = f"closure:from-{best[n][1]}", best[n][0], None
        else:
            src, L, st = "grid", float(gridL[n]), None
        if n in real and real[n]["L"] <= final[n] + 1e-12 and real[n]["L"] < L - 1e-12:
            src, L, st = real[n]["src"], real[n]["L"], real[n]["state"]
        out[str(n)] = {"L": round(float(L), 12), "bound": round(float(final[n]), 12),
                       "grid": gridL[n], "src": src, "state": st}
    json.dump(out, open(OUT, "w"))
    beats = sum(1 for n in range(NMIN, NMAX + 1) if final[n] < gridL[n] - 1e-12)
    with_state = sum(1 for v in out.values() if v["state"])
    print(f"catalogue imported: {imported}")
    print(f"göbel members applied: {gcount} | closure spot-checks passed: {spots}")
    print(f"beats-grid (bound) in {NMIN}..{NMAX}: {beats} | entries with states: {with_state}")


if __name__ == "__main__":
    main()
