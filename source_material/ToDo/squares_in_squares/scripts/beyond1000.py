#!/usr/bin/env python3
r"""beyond1000.py — Run 41: the wider census, n above the delivered table.

WHY.  The delivered table is rows 1..1000 and the submission is scored over
those rows only.  Every statement this project makes about the shape of the
landscape is therefore a statement about a 1000-row window, and the §11 census
says what that window contains at its *proved* end: 156 proven-optimal rows,
99.99% of whose contacts sit in the two lattice relation cells — the vacuum.

The owner's reading: keep the submission where it is, but widen the
perspective past 1000, because some of the rows up there are *easy*.  This
instrument builds the easy ones exactly and counts them.

WHAT "EASY" MEANS HERE.  Four constructions, all exact and all valid by an
elementary argument, for every k with k^2 > 1000 (k = 32..K_MAX):

  n = k^2          L = k      the k x k unit lattice
  n = k^2 - i      L = k      the lattice with i squares removed (i = 1..4)
                              — proved optimal: T-084 (i=1), T-086 (i=2),
                              T-064 (i=3), T-081 (i=4), and the area bound
                              at i = 0
  n = k^2 + j      L = k+1    the lattice plus j squares in a new row (j=1..k)

The validity argument for integer lattice placements is elementary and exact:
two axis-aligned unit squares with integer centres overlap in their interiors
iff their centres coincide, because distinct integer points differ by at least
1 on some axis.  So "all centres distinct" is the whole check — O(n), no
tolerance.  `--gate` additionally hands a spread of these states to
`packlib.finalize` + `packlib.verify`, the project's authority, so the
elementary argument and the gate are confirmed to agree.

WHAT THIS IS NOT.  It is not a bound on s(n) for n > 1000, and it does not
touch `submission.csv` (scoring is n <= 1000).  Rows at n = k^2 + j with
j > k are *not* easy by this construction — those need a real arrangement, and
they are the genuinely open region.

Usage:
    python3 scripts/beyond1000.py --census
    python3 scripts/beyond1000.py --census --gate --write
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import packlib as P                                      # noqa: E402

OUTDIR = os.path.join(ROOT, "workspace/push")
TABLE_MAX = 1000
K_MAX = 99                       # k = 99 -> n up to 9801, inside 10,000


# ------------------------------------------------------------- constructions
def lattice(k: int, drop: int = 0, extra: int = 0) -> list:
    """k x k unit lattice, `drop` squares removed from the last row, `extra`
    squares added in a row above it.  Centres at (x + 0.5, y + 0.5)."""
    pts = []
    total = k * k
    keep = total - drop
    for idx in range(keep):
        y, x = divmod(idx, k)
        pts.append((x + 0.5, y + 0.5, 0.0))
    for j in range(extra):
        pts.append((j + 0.5, k + 0.5, 0.0))
    return pts


def distinct_centres(state: list) -> bool:
    """The elementary exact check: integer lattice centres must be distinct."""
    seen = set()
    for x, y, _ in state:
        key = (round((x - 0.5) * 2), round((y - 0.5) * 2))
        if key in seen:
            return False
        seen.add(key)
    return True


def bbox_side(state: list) -> float:
    xs = [x for x, _, _ in state]
    ys = [y for _, y, _ in state]
    return max(max(xs) - min(xs), max(ys) - min(ys))


def rows_for_k(k: int) -> list:
    """(n, L_design, construction name, state) for one k."""
    out = []
    out.append((k * k, float(k), "square k^2", lattice(k)))
    for i in range(1, 5):
        out.append((k * k - i, float(k), f"k^2-{i}", lattice(k, drop=i)))
    for j in range(1, k + 1):
        out.append((k * k + j, float(k + 1), "k^2+j (new row)", lattice(k, extra=j)))
    return out


def census(k_min: int = 32, k_max: int = K_MAX) -> dict:
    """Build every easy row above the table and check it elementarily."""
    rows = []
    bad = []
    for k in range(k_min, k_max + 1):
        for n, L_design, name, state in rows_for_k(k):
            if n <= TABLE_MAX:
                continue
            ok = distinct_centres(state) and len(state) == n
            side = bbox_side(state)
            # the constructed state's own bounding box must fit the design side
            fits = side <= L_design + 1e-12
            rows.append({"n": n, "k": k, "kind": name, "L_design": L_design,
                         "bbox": side, "ok": bool(ok and fits),
                         "depth": L_design / math.sqrt(n) - 1.0})
            if not (ok and fits):
                bad.append(n)
    rows.sort(key=lambda r: r["n"])
    by_kind = {}
    for r in rows:
        d = by_kind.setdefault(r["kind"], {"rows": 0, "depth_median": None, "depths": []})
        d["rows"] += 1
        d["depths"].append(r["depth"])
    for d in by_kind.values():
        d["depths"].sort()
        d["depth_median"] = d["depths"][len(d["depths"]) // 2]
        d["depth_max"] = d["depths"][-1]
        del d["depths"]
    covered = sorted({r["n"] for r in rows})
    return {
        "k_range": [k_min, k_max],
        "rows_built": len(rows),
        "distinct_n": len(covered),
        "n_range": [covered[0], covered[-1]] if covered else None,
        "invalid": bad,
        "by_kind": by_kind,
        "window_1000_to_10000": 9000,
        "share_of_window": round(len(covered) / 9000.0, 4),
        "proved_optimal": sum(1 for r in rows if r["kind"].startswith(("square", "k^2-"))),
        "rows": rows,
    }


def gate_sample(census_rows: list, per_kind: int = 4, n_cap: int = 2500) -> dict:
    """Hand a spread of the built states to the project's authority."""
    out = []
    seen = {}
    for r in sorted(census_rows, key=lambda z: z["n"]):
        if r["n"] > n_cap:
            continue
        if seen.get(r["kind"], 0) >= per_kind:
            continue
        seen[r["kind"]] = seen.get(r["kind"], 0) + 1
        k = r["k"]
        name = r["kind"]
        if name.startswith("square"):
            state = lattice(k)
        elif name.startswith("k^2-"):
            state = lattice(k, drop=int(name.split("-")[1]))
        else:
            state = lattice(k, extra=r["n"] - k * k)
        t0 = time.time()
        stc, ver = P.finalize([tuple(map(float, s)) for s in state])
        got = float(ver["L"])
        # finalize scales by +2e-9 before rounding, so the gate's L sits a few
        # parts in 1e-8 above the design side; that is the known clearance.
        out.append({"n": r["n"], "kind": name, "design_L": r["L_design"],
                    "gate_L": round(got, 12), "sat": bool(ver["ok"]),
                    "worst_pen": float(ver["worst_pen"]),
                    "drift": got - r["L_design"],
                    "matches_design": abs(got - r["L_design"]) < 1e-6,
                    "seconds": round(time.time() - t0, 3)})
    return {"rows": out, "all_match": all(r["matches_design"] for r in out)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--kmax", type=int, default=K_MAX)
    args = ap.parse_args()
    if not (args.census or args.gate):
        ap.print_help()
        return 0

    res = {"instrument": "beyond1000.py", "run": 41, "table_max": TABLE_MAX}
    if args.census or args.gate:
        t0 = time.time()
        res["census"] = census(k_max=args.kmax)
        res["census"]["seconds"] = round(time.time() - t0, 1)
        c = res["census"]
        print(f"built {c['rows_built']} rows over {c['distinct_n']} distinct n, "
              f"n in {c['n_range']}, invalid {len(c['invalid'])}", flush=True)
        print(f"  share of the 9,000-row window: {c['share_of_window']:.2%}", flush=True)
        for kind, d in sorted(c["by_kind"].items()):
            print(f"  {kind:<18} rows {d['rows']:<5} depth median {d['depth_median']:.4f} "
                  f"max {d['depth_max']:.4f}", flush=True)
    if args.gate:
        t0 = time.time()
        res["gate"] = gate_sample(res["census"]["rows"])
        res["gate"]["seconds"] = round(time.time() - t0, 1)
        print(f"gate: {len(res['gate']['rows'])} rows, all_match "
              f"{res['gate']['all_match']}", flush=True)
        for r in res["gate"]["rows"][:6]:
            print(f"  n={r['n']:<6} {r['kind']:<18} design {r['design_L']:.1f} "
                  f"gate {r['gate_L']:.6f} match {r['matches_design']}", flush=True)
    if args.write:
        os.makedirs(OUTDIR, exist_ok=True)
        path = os.path.join(OUTDIR, "beyond1000.json")
        merged = {}
        if os.path.exists(path):
            with open(path) as f:
                merged = json.load(f)
        merged.update(res)
        with open(path, "w") as f:
            json.dump(merged, f, indent=1)
        print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
