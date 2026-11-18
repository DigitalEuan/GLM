#!/usr/bin/env python3
r"""leech_map.py — the metric codec from a 2D packing to a point of Lambda24.

1. THE WINDOW.  A packing of n unit squares in a side-L square is n centres (2n
   numbers), n angles (discrete) and the side L.  Translation is a symmetry of the
   packing, so it is modded out by putting the bounding box at the origin, and

        continuous dimension = 2n + 1,

   so a lossless, reversible map into 24 real coordinates exists exactly for
   2n + 1 <= 24, i.e. n <= 11, with one coordinate to spare at n = 11.  For
   n >= 12 no injective continuous map exists at all, and every "address" there
   is a lossy feature map.

   A first attempt used the GAP vector (n+1 gaps per axis, 2n+2 numbers).  That
   is wrong in 2D and the round trip caught it: along an axis a packing stacks
   squares, so the projections overlap, the "gaps" go negative and stop summing
   to L - sum(e).  Gaps are a coordinate system only for a single row.

2. THE MAP.
   skeleton(state) -> angles                     discrete, n bits
   encode(state,S) -> 24 ints = round(S*[x_1..x_n, y_1..y_n, L])  zero-padded
   decode(ints,angles) -> state                  reversible up to 1/(2S)

   S is a declared integer scale.  The only loss is the rounding and the only
   gauge is translation, which is a symmetry.  That free scale is the finding:
   "is this packing a Lambda24 point" depends on S, so it is a property of the
   quantisation, not of the packing.

3. THE MEMBERSHIP TEST.  `in_leech24` implements the exact integer form the
repository's `LeechResidue.lean` states: all coordinates share a parity m;
sum(x) = 4m (mod 8); each nonempty residue class mod 4 is a Golay codeword.
`validate` checks it against all 196 560 minimal vectors of sqrt(8)*Lambda24,
which come in three shapes, and against the short impostors it must reject.

4. WHAT WAS MEASURED (run 45, see 16-LEECH-MAP.md).  Delivered rows: grid rows
   are legal at S in {8..1024}; the three rows containing a 45-degree square
   (n = 5, 10, 11) are legal at no scale in {1..1024}.  Over 87 tilted and 168
   untilted rows the crosstab is perfect: tilt => never legal, no tilt => legal
   somewhere.  The lattice condition is an integrality condition and a tilted
   square injects sqrt(2)/2 into the coordinates, so the address cannot represent
   the configurations that produce the score.  This file is therefore a CODEC,
   not an address; the address that works is combinatorial (`leech_comb.py`).

Usage:
    python3 scripts/leech_map.py --validate     # minimal-vector validation
    python3 scripts/leech_map.py --probe        # codec + legality measurements
    python3 scripts/leech_map.py                # both
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "workspace/push/leech_map.json")
sys.path.insert(0, HERE)
import packlib  # noqa: E402
import sqscore  # noqa: E402
import leech24_design as LD  # noqa: E402  (the Golay code)

WINDOW_MAX_N = 11          # 2n + 1 <= 24
SCALES = (1, 2, 4, 8, 16, 64, 256, 1024)


# ------------------------------------------------------------------ the code
_GOLAY: set[int] | None = None


def golay_set() -> set[int]:
    global _GOLAY
    if _GOLAY is None:
        _GOLAY = set(LD.golay_words())
    return _GOLAY


def in_leech24(x) -> bool:
    """Exact membership test for sqrt(8)*Lambda24 (the Lean integer form)."""
    if len(x) != 24:
        return False
    x = [int(v) for v in x]
    m = x[0] & 1
    if any((v & 1) != m for v in x):
        return False
    if (sum(x) - 4 * m) % 8 != 0:
        return False
    classes: dict[int, int] = {}
    for i, v in enumerate(x):
        classes[v % 4] = classes.get(v % 4, 0) | (1 << i)
    words = golay_set()
    return all(mask in words for mask in classes.values())


# ------------------------------------------------------------------ the map
def bbox_origin(state):
    """Bounding-box origin: translation is a symmetry, so this is a gauge."""
    ex = [0.5 * (abs(math.cos(float(s[2]))) + abs(math.sin(float(s[2]))))
          for s in state]
    return (min(s[0] - e for s, e in zip(state, ex)),
            min(s[1] - e for s, e in zip(state, ex)))


def skeleton(state):
    """The discrete content of a packing: its n angles."""
    return [float(s[2]) for s in state]


def encode(state, S: int = 64):
    """24 integers: round(S*[x, y, L]) with the box at the origin, zero-padded."""
    n = len(state)
    if 2 * n + 1 > 24:
        raise ValueError(f"n={n} is outside the window (2n+1 > 24)")
    lox, loy = bbox_origin(state)
    L = packlib.verify(state)["L"]
    vals = ([s[0] - lox for s in state] + [s[1] - loy for s in state] + [L])
    return [int(round(S * v)) for v in vals] + [0] * (24 - len(vals))


def decode(vec, angles, S: int = 64):
    """Rebuild the state from 24 integers and the angles."""
    n = len(angles)
    xs = [v / S for v in vec[:n]]
    ys = [v / S for v in vec[n:2 * n]]
    return [(xs[i], ys[i], angles[i]) for i in range(n)]


def tilted(state) -> bool:
    return any(abs(math.sin(2 * float(s[2]))) > 0.5 for s in state)


# --------------------------------------------------------------- validation
def minimal_vectors():
    """Yield (family, vector) for the 196 560 minimal vectors of sqrt(8)*Lambda24.

    Streamed rather than materialised: the caller only counts and tests.
    """
    for w in sorted(golay_set()):
        if LD.weight(w) != 8:                     # (2^8, 0^16) on the 759 octads
            continue
        pts = [i for i in range(24) if (w >> i) & 1]
        for signs in itertools.product((2, -2), repeat=8):
            if sum(1 for s in signs if s < 0) % 2:
                continue
            v = [0] * 24
            for i, s in zip(pts, signs):
                v[i] = s
            yield "A_2^8", v
    for i in range(24):                           # (3, 1^23) up to signs
        for c in sorted(golay_set()):
            # classes mod 4 must stay codewords: +1 stays in C, -1 in its
            # complement, and the magnitude-3 entry takes the class of its sign
            v = [1 if (c >> j) & 1 else -1 for j in range(24)]
            v[i] = -3 if (c >> i) & 1 else 3
            yield "B_3_1", v
    for i, j in itertools.combinations(range(24), 2):   # (4, 4, 0^22)
        for si in (4, -4):
            for sj in (4, -4):
                v = [0] * 24
                v[i], v[j] = si, sj
                yield "C_4_4", v


def validate() -> dict:
    counts = {"A_2^8": 0, "B_3_1": 0, "C_4_4": 0}
    accepted = dict(counts)
    roots = set()
    for fam, v in minimal_vectors():
        counts[fam] += 1
        roots.add(sum(x * x for x in v))
        if in_leech24(v):
            accepted[fam] += 1
    impostors = {}
    for label, v in (("2 e_i", [2] + [0] * 23), ("4 e_i", [4] + [0] * 23),
                     ("2^4", [2, 2, 2, 2] + [0] * 20), ("1^8", [1] * 8 + [0] * 16),
                     ("2^2", [2, 2] + [0] * 22)):
        impostors[label] = in_leech24(v)
    return {"counts": counts, "accepted": accepted,
            "squared_norms": sorted(roots),
            "total": sum(counts.values()),
            "all_accepted": accepted == counts,
            "impostors_accepted": [k for k, b in impostors.items() if b]}


# ------------------------------------------------------------------ probe
def jitter_ensemble(state, amp, trials, rng):
    """Push each square outward from the bbox centre; every trial stays feasible.

    Outward is the direction that keeps a packing legal (all gaps grow), so each
    trial is a slightly worse packing with a different L.
    """
    L0 = packlib.verify(state)["L"]
    lox, loy = bbox_origin(state)
    cx, cy = lox + L0 / 2, loy + L0 / 2
    out = []
    for _ in range(trials):
        cand = [(cx + (x - cx) * (1.0 + rng.uniform(0.0, amp)),
                 cy + (y - cy) * (1.0 + rng.uniform(0.0, amp)), t)
                for x, y, t in state]
        r = packlib.verify(cand)
        if not r["ok"] or r["worst_pen"] > -1e-12:
            continue
        st, r2 = packlib.finalize(cand)
        if r2["ok"] and r2["worst_pen"] <= -1e-12:
            out.append((st, r2["L"]))
    return out


def probe(trials=40, seed=20261118):
    rng = random.Random(seed)
    store = packlib.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    rows = {n: store[n] for n in range(1, WINDOW_MAX_N + 1) if n in store}
    res = {"window_max_n": WINDOW_MAX_N, "scales": list(SCALES),
           "delivered": [], "ensemble": []}

    for n, st in sorted(rows.items()):
        S = 256
        vec = encode(st, S)
        rec = decode(vec, skeleton(st), S)
        lox, loy = bbox_origin(st)      # translation gauge, added back to compare
        err = max(max(abs((a[0] - lox) - b[0]), abs((a[1] - loy) - b[1]))
                  for a, b in zip(st, rec))
        L = packlib.verify(st)["L"]
        res["delivered"].append({
            "n": n, "L": L, "slack": sqscore.row_score(n, L),
            "roundtrip_err": err, "tilted": tilted(st),
            "legal_scales": [S_ for S_ in SCALES if in_leech24(encode(st, S_))],
        })

    for n, st0 in sorted(rows.items()):
        if n < 5:
            continue
        ens = jitter_ensemble(st0, 0.02, trials, rng)
        if not ens:
            continue
        per_scale = {S_: 0 for S_ in SCALES}
        hits = 0
        for st, L in ens:
            if any(in_leech24(encode(st, S_)) for S_ in SCALES):
                hits += 1
            for S_ in SCALES:
                if in_leech24(encode(st, S_)):
                    per_scale[S_] += 1
        slacks = [sqscore.row_score(n, L) for _, L in ens]
        res["ensemble"].append({
            "n": n, "trials": len(ens), "any_legal": hits, "per_scale": per_scale,
            "tilted": sum(1 for st, _ in ens if tilted(st)),
            "slack_min": min(slacks), "slack_max": max(slacks),
        })

    cells = {(True, True): 0, (True, False): 0, (False, True): 0, (False, False): 0}
    for r in res["delivered"]:
        cells[(r["tilted"], bool(r["legal_scales"]))] += 1
    for e in res["ensemble"]:
        if e["tilted"] == e["trials"]:
            cells[(True, True)] += e["any_legal"]
            cells[(True, False)] += e["trials"] - e["any_legal"]
        elif e["tilted"] == 0:
            cells[(False, True)] += e["any_legal"]
            cells[(False, False)] += e["trials"] - e["any_legal"]
    res["tilt_vs_legal"] = {f"tilted={k[0]},legal={k[1]}": v for k, v in cells.items()}
    return res


# --------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--probe", action="store_true")
    args = ap.parse_args()
    do_all = not args.validate and not args.probe
    t0 = time.time()
    # merge into any existing ledger: a --validate run must not wipe the probe
    ledger = {}
    if os.path.exists(OUT):
        try:
            with open(OUT) as f:
                ledger = json.load(f)
        except (OSError, ValueError):
            ledger = {}
    ledger.update({"instrument": "leech_map.py", "run": 46,
                   "schema": "leech-map/2", "written": time.strftime("%Y-%m-%d %H:%M:%S")})
    ok = True
    if args.validate or do_all:
        v = validate()
        ledger["validation"] = v
        print("minimal vectors of sqrt(8)*Lambda24 (squared norm 32):")
        for k in ("A_2^8", "B_3_1", "C_4_4"):
            print(f"  {k:8s} {v['counts'][k]:7d}  norms {v['squared_norms']}"
                  f"  accepted {v['accepted'][k]:7d}")
        print(f"  total {v['total']}   impostors accepted: "
              f"{v['impostors_accepted'] or 'none'}")
        ok &= v["all_accepted"] and not v["impostors_accepted"]
    if args.probe or do_all:
        p = probe()
        ledger["probe"] = p
        print(f"\nrows in the window n <= {p['window_max_n']}: "
              f"{[r['n'] for r in p['delivered']]}")
        print(f"  {'n':>3} {'L':>12} {'slack':>9} {'rt_err':>9} {'legal@':>22}")
        for r in p["delivered"]:
            print(f"  {r['n']:3d} {r['L']:12.9f} {r['slack']:9.6f} "
                  f"{r['roundtrip_err']:.2e}   {r['legal_scales'] or 'none'}")
        rt = max(r["roundtrip_err"] for r in p["delivered"])
        print(f"  worst round-trip error {rt:.2e}  (bound 1/(2S) = 0.00195)")
        for e in p["ensemble"]:
            print(f"  ensemble n={e['n']:2d}: {e['trials']:3d} jitters, "
                  f"legal {e['any_legal']}, tilted {e['tilted']}, "
                  f"slack [{e['slack_min']:.6f}, {e['slack_max']:.6f}]")
        print("tilt vs lattice legality:")
        for k, v in sorted(p["tilt_vs_legal"].items()):
            print(f"  {k:24s} {v:5d}")
        ledger["roundtrip_max_err"] = rt
    ledger["seconds"] = round(time.time() - t0, 2)
    ledger["ok"] = ok
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(ledger, f, indent=1)
    print(f"\n{'PASS' if ok else 'FAIL'}  [{ledger['seconds']}s]  ledger: {OUT}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
