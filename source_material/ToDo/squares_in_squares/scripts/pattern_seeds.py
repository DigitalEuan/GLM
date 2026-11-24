#!/usr/bin/env python3
r"""pattern_seeds.py — constructive macro-block seeds, built from scratch (discovery side).

Runs 109–111 attacked the delivered table by perturbing its own coordinates: free angles, face
slides, lifts, chains. Every one of them was refused, and doc 72 §5 now asks a different question:
can a packing be *built* rather than repaired? This module does that. It never reads the delivered
pose of a row. It reads only `n` and `L_delivered`, then synthesises candidate packings out of
macro-blocks — arrays of unit squares at a fixed angle — and measures each one with
`true_geom.py` at 40 digits.

Three macro-topologies, as doc 72 §5 R3 requires (a *named* mechanism):

  A. dual-tilted blocks: two 45-degree blocks in opposite corners, a bent transition strip (one
     strip of each parity, so the seam turns a corner), and an upright block carrying the residue.
  B. L-cut nested frames: an upright core, four 45-degree perimeter bands around it (the "L-cut"
     is the first two bands closing the corner), and an upright residue staircase.
  C. rational-t lattices: blocks tilted at a Pythagorean angle — arctan(3/4), arctan(5/12),
     arctan(8/15), arctan(2/1) — so every block's bounding box is rational, in squares and in
     bands, with an upright residue.

Placement is a shelf packer over *bounding boxes*: blocks never overlap because their boxes never
overlap, so every seed is overlap-free by construction. That is verified, not assumed — the best
seed of every row and family is then handed to `true_geom.check` at 40 digits.

The honest comparison is against `L_delivered`, the true 40-digit side of the row in `table.json`,
at the same `n`. A seed that is worse is reported as worse, with its deficit in absolute side, in
percent, and in the void area it fails to recover.

    python3 scripts/pattern_seeds.py --selftest
    python3 scripts/pattern_seeds.py --rows 29 41 53 55 680 733 845 904 971
"""
from __future__ import annotations

import json
import math
import sys
from decimal import Decimal as D
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import true_geom as TG  # noqa: E402

ROOT = HERE.parent
TABLE = ROOT / "workspace" / "submission" / "table.json"
OUT = ROOT / "workspace" / "push" / "pattern_seeds.json"

QUARTER = math.pi / 4
PYTH = ((4, 3), (12, 5), (15, 8), (2, 1))  # (p, q) -> arctan(q/p), cos/sin rational

GAP = 1e-9  # hairline between blocks: bounding boxes touch exactly, so a construction contact
            # would otherwise sit at slack 0 and read as a 1e-16 float overlap in `true_geom`


@lru_cache(maxsize=None)
def _cs(t):
    return math.cos(t), math.sin(t)


def block(w, h, t):
    """A `w`-by-`h` array of unit squares at angle `t`, as centres plus its bounding box."""
    c, s = _cs(t)
    step = 1.0 + GAP  # the same hairline inside a block: float cos/sin would otherwise leave
    pts = [(i * step * c - j * step * s, i * step * s + j * step * c)
           for i in range(w) for j in range(h)]  # neighbouring cells at slack -1e-16
    half = (abs(c) + abs(s)) / 2
    x0 = min(p[0] for p in pts) - half
    y0 = min(p[1] for p in pts) - half
    bw = max(p[0] for p in pts) + half - x0
    bh = max(p[1] for p in pts) + half - y0
    return {"w": w, "h": h, "t": t, "pts": pts, "bw": bw, "bh": bh, "ox": x0, "oy": y0}


def place(blk, X, Y):
    """The block's cell centres with its bounding-box corner at `(X, Y)`."""
    return [(X + p[0] - blk["ox"], Y + p[1] - blk["oy"], blk["t"]) for p in blk["pts"]]


def rect_parts(r, t=0.0):
    """Split `r` squares into one near-square block and a single-square remainder strip."""
    if r <= 0:
        return []
    best = None
    for w in range(1, int(math.isqrt(r)) + 1):
        h, left = divmod(r, w)
        side = max(w, h + (1 if left else 0))  # the strip costs one more row when it does not fit
        if best is None or side < best[0]:
            best = (side, w, h, left)
    _, w, h, left = best
    parts = [block(w, h, t)]
    if left:
        parts.append(block(left, 1, t))
    return parts


def shelf(blocks, W):
    """Place blocks left to right in shelves of width `W`; returns (cells, width, height)."""
    order = sorted(blocks, key=lambda b: (-b["bh"], -b["bw"]))
    cells, x, y, rowh, used = [], 0.0, 0.0, 0.0, 0.0
    for blk in order:
        if x and x + blk["bw"] > W + 1e-12:
            y += rowh + GAP
            x, rowh = 0.0, 0.0
        cells += place(blk, x, y)
        x += blk["bw"] + GAP
        used = max(used, x)
        rowh = max(rowh, blk["bh"])
    return cells, used, y + rowh


def side_of(cells):
    """The true container side of a cell list, from `true_geom` at 40 digits."""
    return TG.side([(c[0], c[1], c[2]) for c in cells])


def fside(cells):
    """A cheap float side, used only to *rank* candidate seeds; the winner is re-measured by
    `true_geom.side` at 40 digits. Same separation as everywhere else in this repository:
    discovery in float, the reported number in decimals."""
    lx = ly = math.inf
    hx = hy = -math.inf
    for x, y, t in cells:
        c, s_ = _cs(t)
        h = (abs(c) + abs(s_)) / 2
        lx, hx = min(lx, x - h), max(hx, x + h)
        ly, hy = min(ly, y - h), max(hy, y + h)
    return max(hx - lx, hy - ly)


def best_layout(blocks, n, tries=13):
    """The best shelf width for a block set: the smallest true side over a width scan."""
    if not blocks:
        return None
    base = math.sqrt(n)
    best = None
    for k in range(tries):
        W = base * (1.0 + 0.02 * k)
        cells, used, height = shelf(blocks, W)
        side = fside(cells)
        if best is None or side < best["side"]:
            best = {"side": side, "cells": cells, "W": W, "used": used, "height": height}
    return best


# --------------------------------------------------------------------------- families


def family_a(n):
    """A: two 45-degree blocks, a bent strip of each parity, upright residue."""
    for k in range(2, 15):
        for j in (0, 2, 3, 5, 8):
            rem = n - 2 * k * k - 2 * j
            if rem < 1:
                continue
            blocks = [block(k, k, QUARTER), block(k, k, QUARTER)]
            if j:
                blocks += [block(j, 1, QUARTER), block(1, j, QUARTER)]
            blocks += rect_parts(rem)
            yield f"A k={k} strip={j} rem={rem}", blocks


def family_b(n):
    """B: upright core, four 45-degree perimeter bands (L-cut corner), upright residue."""
    for c in range(2, 26):
        for m in (1, 2, 3, 4, 6):
            rem = n - c * c - 4 * m
            if rem < 1:
                continue
            blocks = [block(c, c, 0.0),
                      block(m, 1, QUARTER), block(1, m, QUARTER),
                      block(m, 1, QUARTER), block(1, m, QUARTER)]
            blocks += rect_parts(rem)
            yield f"B core={c} band={m} rem={rem}", blocks


def family_c(n):
    """C: Pythagorean-tilted block lattices, in square and band form, upright residue."""
    for p, q in PYTH:
        t = math.atan2(q, p)
        for b in (2, 3, 4, 5, 7):
            for kind in ("square", "band"):
                unit = b * b if kind == "square" else b
                cnt = (n - 1) // unit
                if cnt < 1:
                    continue
                rem = n - cnt * unit
                blocks = ([block(b, b, t)] * cnt if kind == "square"
                          else [block(b, 1, t)] * cnt)
                blocks += rect_parts(rem)
                yield f"C {p}:{q} b={b} {kind}x{cnt} rem={rem}", blocks


def family_d(n):
    """D: upright near-square blocks only — the reference macro-topology, no tilt anywhere.
    Every other family has to beat this one before its tilt can claim to earn anything."""
    yield f"D upright rem={n}", rect_parts(n)


FAMILIES = {"A": family_a, "B": family_b, "C": family_c, "D": family_d}


# --------------------------------------------------------------------------- driver


def load_table(path=None):
    t = json.load(open(path or TABLE))
    return {int(k): {"L": r["L"], "src": r.get("src")} for k, r in t.items()}


def seed_row(n, L_del, ledger_path=OUT):
    """Best seed of each family for one row, judged against the delivered side."""
    out = {"n": n, "L_delivered": str(L_del), "families": {}}
    for name, fam in FAMILIES.items():
        best = None
        tried = 0
        for label, blocks in fam(n):
            if sum(b["w"] * b["h"] for b in blocks) != n:
                raise AssertionError(f"{name}: block areas do not sum to {n} ({label})")
            tried += 1
            cfg = best_layout(blocks, n)
            if cfg is None:
                continue
            if best is None or cfg["side"] < best["side"]:
                best = {"side": cfg["side"], "label": label, "cells": cfg["cells"],
                        "W": cfg["W"], "bbox_area": sum(b["bw"] * b["bh"] for b in blocks)}
        if best is None:
            out["families"][name] = {"verdict": "no-seed"}
            continue
        side40 = side_of(best["cells"])
        chk = TG.check([(c[0], c[1], c[2]) for c in best["cells"]])
        gain = L_del - side40
        out["families"][name] = {
            "label": best["label"],
            "configs_tried": tried,
            "side40": str(side40),
            "side_raw": str(best["side"]),
            "gain": str(gain),
            "gap_pct": float(gain) / float(L_del) * 100.0,
            "bbox_area": str(best["bbox_area"]),
            "waste_tilt": str(D(str(best["bbox_area"])) - n),
            "waste_pack": str(side40 ** 2 - D(str(best["bbox_area"]))),
            "void_seed": str(side40 ** 2 - n),
            "void_delivered": str(float(L_del) ** 2 - n),
            "violations": len(chk["violations"]),
            "worst_slack": None if chk["worst"] is None else str(chk["worst"]),
            "verdict": "beats" if gain > 0 else "worse",
        }
    return out


def run_rows(ns, write=True):
    tab = load_table()
    out = {"rows": {}}
    for n in ns:
        if n not in tab:
            print(f"  n={n}: not in table, skipped")
            continue
        rec = seed_row(n, D(tab[n]["L"]))
        out["rows"][str(n)] = rec
        best = min((f for f in rec["families"].values() if "side40" in f),
                   key=lambda f: float(f["side40"]), default=None)
        if best:
            print(f"  n={n:4d} delivered {float(tab[n]['L']):.9f}  "
                  f"best seed {float(best['side40']):.9f}  gap {float(best['gain']):+.4f} "
                  f"({float(best['gap_pct']):+.2f}%)  {best['label']}", flush=True)
    if write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        json.dump(out, open(OUT, "w"), indent=1)
        print(f"pattern_seeds: -> {OUT.relative_to(ROOT)}")
    return out


def selftest():
    """Four controls: an axis block, a 45 degree block, block areas, and disjoint boxes."""
    one = block(2, 2, 0.0)
    assert abs(one["bw"] - 2) < 1e-8 and abs(one["bh"] - 2) < 1e-8, (one["bw"], one["bh"])
    assert abs(float(side_of(place(one, 0.0, 0.0))) - 2) < 1e-8
    diag = block(2, 2, QUARTER)
    assert abs(diag["bw"] - 2 * math.sqrt(2)) < 1e-8, diag["bw"]
    for name, fam in FAMILIES.items():
        for n in (29, 325):
            seen = 0
            for label, blocks in fam(n):
                assert sum(b["w"] * b["h"] for b in blocks) == n, (name, n, label)
                seen += 1
                if seen >= 6:
                    break
            assert seen, (name, n)
    blocks = [block(3, 3, QUARTER), block(3, 3, QUARTER), block(2, 1, 0.0)]
    cells, used, height = shelf(blocks, 10.0)
    assert len({(round(c[0], 12), round(c[1], 12)) for c in cells}) == 9 + 9 + 2
    chk = TG.check(list(cells))
    assert not chk["violations"], chk["violations"][:2]
    print("pattern_seeds: OK (5 controls)")


def main(argv):
    if "--selftest" in argv:
        selftest()
        return 0
    ns = []
    if "--rows" in argv:
        i = argv.index("--rows")
        for a in argv[i + 1:]:
            if not a.isdigit():
                break
            ns.append(int(a))
    if not ns:
        ns = [29, 41, 53, 55, 680, 733, 845, 904, 971]
    run_rows(ns)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
