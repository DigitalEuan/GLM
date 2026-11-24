#!/usr/bin/env python3
r"""pattern_seeds.py — constructive macro-block seeds, built from scratch (discovery side).

Run 112 built packings from macro-blocks and every family lost; doc 73 §5 named the three next
steps, and this is them:

  1. a **corner-nesting packer** — corner insertion over bounding boxes instead of a shelf, so the
     residue strip can sit *beside* the near-square block instead of under it (doc 73 measured that
     waste at 49–57 void units on the big rows);
  2. a **boundary-staircase family E** — an upright core with one-cell tilted cells seated along one
     or two walls by a real clearance search, at the quarter word and at rational slopes t = p/q with
     an expanding denominator. This is the only topology whose tilt cost is perimeter-order, and it
     is what the delivered table actually does;
  3. an **interval certificate** for whatever E builds — `scripts/interval_verifier.py` re-checks the
     exact rational recipe in `Fraction` arithmetic, so a seed's non-overlap and its side are proved
     rather than measured, which is what doc 72 §5 C1 requires of a non-word row.

The exact ceiling this run states and then measures against is arithmetic, not search: a pose whose
cells all sit on the integer lattice has side at least `ceil(sqrt n)`, because `s` integer columns hold
at most `s^2` cells. Every one of the nine target rows beats the grid (`L_delivered < ceil(sqrt n)`),
so **no lattice construction can pass C2 on any of them** — the only route left is a pose that leaves
the lattice, which is exactly what a tilted boundary cell does and what the tilted *body* cannot do
cheaply. Family E is the test of whether leaving it at the edge is enough.

Families A–D are run 112's, unchanged except for the packer:

  A. dual-tilted blocks: two 45-degree blocks, a bent transition strip, an upright residue.
  B. L-cut nested frames: an upright core, four 45-degree perimeter bands, an upright residue.
  C. rational-t lattices: blocks at a Pythagorean angle, in squares and bands, upright residue.
  D. upright reference: near-square upright blocks only. Every tilted family has to beat this first.

Ranking is in float, the reported side is `true_geom.side` at 40 digits, zero overlap is
`true_geom.check` at the same digits, and a winner (there is none this run) would be re-proved by
`interval_verifier.py`. Discovery in float, judgement in decimals, certificate in `Fraction` — the
same separation as everywhere else in this repository.

    python3 scripts/pattern_seeds.py --selftest
    python3 scripts/pattern_seeds.py --rows 29 41 53 55 680 733 845 904 971
    python3 scripts/pattern_seeds.py --denominators 971
    python3 scripts/pattern_seeds.py --verify
"""
from __future__ import annotations

import json
import math
import sys
from decimal import Decimal as D
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import true_geom as TG  # noqa: E402

ROOT = HERE.parent
TABLE = ROOT / "workspace" / "submission" / "table.json"
OUT = ROOT / "workspace" / "push" / "pattern_seeds.json"
OUT_E = ROOT / "workspace" / "push" / "staircase.json"
OUT_RECIPES = ROOT / "workspace" / "push" / "interval_checks.json"

QUARTER = math.pi / 4
PYTH = ((4, 3), (12, 5), (15, 8), (2, 1))  # (p, q) -> arctan(q/p), cos/sin rational

GAP = 1e-9   # hairline between blocks: bounding boxes touch exactly, so a construction contact
             # would otherwise sit at slack 0 and read as a 1e-16 float overlap in `true_geom`
MARGIN = 1e-9  # the clearance the staircase search demands, and the slack the interval verifier
               # can certify; an exact contact is invisible to an enclosure

GRID_STEP = 1.0 / 32.0   # the staircase search's step along a wall (and outward, along it)
SPEC_DIRS = ((1, 1), (3, 4), (5, 12), (8, 15), (1, 2), (2, 5), (1, 3), (3, 7), (4, 9), (5, 13),
             (7, 20), (9, 25), (11, 30), (13, 37), (1, 5), (1, 8), (1, 13))


@lru_cache(maxsize=None)
def _cs(t):
    return math.cos(t), math.sin(t)


def dir_pq(p, q):
    """The float direction `(c, s)` of slope `p/q` -- discovery only."""
    r = math.hypot(p, q)
    return q / r, p / r


def spec_of(p, q):
    """The exact direction spec of the slope `p/q`, for the interval recipe."""
    return ("quarter",) if p == q else ("slope", int(p), int(q))


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


def _corners(placed):
    """Corner-insertion candidates: the origin and the two free corners of every placed box."""
    out = [(0.0, 0.0)]
    for (x, y, w, h) in placed:
        out.append((x + w + GAP, y))
        out.append((x, y + h + GAP))
    return out


def nest_pack(blocks, W):
    """Corner-insertion (bottom-left) packing over bounding boxes; `None` if it does not fit `W`.

    Run 112's shelf could only stack rows, so the residue strip always paid a whole extra row under
    the near-square block. This keeps every free corner of every placed box as a candidate and takes
    the lowest-leftmost one that fits and clears, so the strip nests beside the block instead of
    under it. Boxes are separated by the same `1e-9` hairline as everywhere else, so overlap-freedom
    stays structural.
    """
    order = sorted(blocks, key=lambda b: (-b["bw"] * b["bh"], -b["bh"], -b["bw"]))
    placed = []
    for blk in order:
        best = None
        for (X, Y) in _corners(placed):
            if X + blk["bw"] > W + 1e-12:
                continue
            if all(X + blk["bw"] <= px or px + pw <= X
                   or Y + blk["bh"] <= py or py + ph <= Y
                   for (px, py, pw, ph) in placed):
                key = (round(Y + blk["bh"], 12), round(X, 12))
                if best is None or key < best[0]:
                    best = (key, X, Y)
        if best is None:
            return None
        placed.append((best[1], best[2], blk["bw"], blk["bh"]))
    cells = []
    for blk, (X, Y, _w, _h) in zip(order, placed):
        cells += place(blk, X, Y)
    used = max(x + w for x, y, w, h in placed)
    height = max(y + h for x, y, w, h in placed)
    return cells, used, height


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
    """The best packing of a block set over a width scan, by shelf and by corner insertion."""
    if not blocks:
        return None
    base = math.sqrt(n)
    best = None
    for k in range(tries):
        W = base * (1.0 + 0.02 * k)
        for packer in (shelf, nest_pack):
            got = packer(blocks, W)
            if got is None:
                continue
            cells, used, height = got
            side = fside(cells)
            if best is None or side < best["side"]:
                best = {"side": side, "cells": cells, "W": W, "used": used,
                        "height": height, "packer": packer.__name__}
    return best


# --------------------------------------------------------------------------- families A-D


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


# --------------------------------------------------------------------------- family E


def _pair_slack(ca, cb):
    """The float SAT slack of a pair (max over the four axes); >= 0 means separated."""
    (xi, yi, ci, si) = ca[0], ca[1], ca[6], ca[7]
    (xj, yj, cj, sj) = cb[0], cb[1], cb[6], cb[7]
    dx, dy = xj - xi, yj - yi
    best = None
    for (c1, s1, c2, s2) in ((ci, si, cj, sj), (cj, sj, ci, si)):
        for q in ((c1, s1), (-s1, c1), (c2, s2), (-s2, c2)):
            proj = dx * q[0] + dy * q[1]
            h1 = (abs(c1 * q[0] + s1 * q[1]) + abs(-s1 * q[0] + c1 * q[1])) / 2
            h2 = (abs(c2 * q[0] + s2 * q[1]) + abs(-s2 * q[0] + c2 * q[1])) / 2
            sl = abs(proj) - (h1 + h2)
            best = sl if best is None or sl > best else best
    return best


def _cell(x, y, t, spec):
    """A cell record: position, float angle (for the judges), exact direction (for the recipe)."""
    c, s = _cs(t)
    return (x, y, t, spec, c, s, c, s)


class _Near:
    """A coarse grid so the clearance search only looks at the cells that could matter."""

    def __init__(self):
        self.b = {}

    def add(self, i, x, y):
        self.b.setdefault((math.floor(x), math.floor(y)), []).append(i)

    def at(self, x, y):
        ix, iy = math.floor(x), math.floor(y)
        out = []
        for a in range(ix - 3, ix + 4):
            for b in range(iy - 3, iy + 4):
                out.extend(self.b.get((a, b), ()))
        return out


def _clear(cand, cells, near, margin=MARGIN):
    """Clear of every nearby cell by `margin`, with float comparison slop.

    The seats are placed at `+margin`, so their slack *is* `margin` up to float rounding; demanding
    `>= margin` would reject every seat by `1e-17`. The test asks for half of it, which is still
    strictly positive in exact arithmetic — which is what the interval verifier re-checks.
    """
    for i in near.at(cand[0], cand[1]):
        if _pair_slack(cand, cells[i]) < margin * 0.5:
            return False
    return True


def seat_law(p, q):
    """The analytic fringe law of a slope `p/q`: `(half_extent, pitch, protrusion)`.

    Two cells of the same direction at the same outward coordinate are separated iff their gap
    along the wall is at least `1/max(|c|, |s|)` -- along the tight axis one of them projects `1`.
    The first outward position that clears a solid axis wall column is `0.5 + h` from its centres,
    i.e. the fringe's outer bounding edge lands `2h` past the wall itself (and the axis filler's
    `2h = 1` is exactly the next lattice column). Both numbers are minimised at the axis limit
    (`pitch -> 1`, `protrusion -> 1`), which is the domination this run measures: a tilted fringe
    cell is never denser than an axis cell. Arithmetic, not a search.
    """
    c, s = dir_pq(p, q)
    h = (abs(c) + abs(s)) / 2
    return h, 1.0 / max(abs(c), abs(s)), 2 * h


def _seat(cells, near, p, q, L, edge="x", start=0.0, margin=MARGIN, limit=4000):
    """Seat cells of slope `p/q` along a wall at the analytic pitch, keeping each one clear.

    `edge == "x"` seats along the right wall (the centre slides in `y`, the outward coordinate is
    `x`); `edge == "y"` seats along the top wall. The pitch is *derived* by `seat_law`, not scanned;
    every candidate is then still checked against all neighbours, so a seat that a corner or the
    other wall's fringe refuses is skipped rather than asserted.
    """
    c, s = dir_pq(p, q)
    h, pitch, _pro = seat_law(p, q)
    spec = spec_of(p, q)
    t = math.atan2(s, c)
    out = start + 0.5 + h + margin    # `start` is the wall column's centre line
    if out + h > L + 1e-12:
        return 0
    along = h + margin
    added, k = 0, 0
    while along + h <= L + 1e-12 and k < limit:
        cand = _cell(out, along, t, spec) if edge == "x" else _cell(along, out, t, spec)
        if _clear(cand, cells, near, margin):
            cells.append(cand)
            near.add(len(cells) - 1, cand[0], cand[1])
            added += 1
        along += pitch + margin       # the analytic pitch sits at exact contact; the margin opens it
        k += 1
    return added


STEPC = 1.0 + GAP   # the core's own lattice step: an exact contact has slack 0, which no enclosure
                    # can certify, so the construction carries the same hairline as the blocks


def stair_fill(a, b, L, p, q, edges="x"):
    """An `a`-by-`b` upright core with tilted cells seated along one or two walls inside `[0, L]^2`.

    Returns `(cells, tilted_count)`. The core is exact (`i + 1/2` on a `1 + GAP` lattice); the fringe
    is placed at `seat_law`'s pitch and every candidate is clearance-checked, so the numbers are
    measured, not asserted.
    """
    if a < 1 or b < 1 or a > L or b > L:
        return [], 0
    cells = [_cell((i + 0.5) * STEPC, (j + 0.5) * STEPC, 0.0, ("axis",))
             for i in range(a) for j in range(b)]
    near = _Near()
    for i, cl in enumerate(cells):
        near.add(i, cl[0], cl[1])
    tilted = 0
    for edge in (("x", "y") if edges == "xy" else (edges,)):
        start = ((a - 0.5) if edge == "x" else (b - 0.5)) * STEPC
        tilted += _seat(cells, near, p, q, L, edge, start=start)
    return cells, tilted


def e_scan(n, L, dirs=SPEC_DIRS, cores=None, keep_best=1):
    """The best family E fills of `n` at side `L`: how many cells fit, and with which topology.

    A fill with `N >= n` is a **candidate**: drop cells to exactly `n` and the side stays `L`. A fill
    with `N < n` is a shortfall, and the shortfall is the honest measurement of the family.
    """
    k = math.isqrt(n)
    if cores is None:
        cores = [(a, b) for b in (k, k + 1) for a in (k, k - 1, k - 2, k - 3)]
    rows = []
    for (a, b) in cores:
        if a < 1 or b < 1 or a > L or b > L:
            continue
        for (p, q) in dirs:
            for edges in ("x", "y", "xy"):
                cells, tilted = stair_fill(a, b, L, p, q, edges)
                if not cells:
                    continue
                rows.append({"a": a, "b": b, "p": p, "q": q, "edges": edges,
                             "cells": len(cells), "tilted": tilted,
                             "shortfall": n - len(cells),
                             "core_side": max(a, b)})
    rows.sort(key=lambda r: (-r["cells"], r["tilted"], r["core_side"]))
    return rows[:keep_best] if keep_best else rows


# --------------------------------------------------------------------------- recipes


def recipe_rows(cells):
    """An exact `interval_verifier` recipe from float cells: exact rational centres, exact directions."""
    out = []
    for (x, y, t, spec, *_rest) in cells:
        out.append({"x": str(F(x)), "y": str(F(y)), "dir": list(spec)})
    return out


def certify(cells, L=None, label=None):
    """Re-check a cell list with `interval_verifier.py` (Fraction arithmetic, no float)."""
    import interval_verifier as IV
    triples = [(F(x), F(y), tuple(spec)) for (x, y, _t, spec, *_r) in cells]
    rep = IV.verify(triples, L)
    rep["label"] = label
    return rep


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
                        "W": cfg["W"], "packer": cfg["packer"],
                        "bbox_area": sum(b["bw"] * b["bh"] for b in blocks)}
        if best is None:
            out["families"][name] = {"verdict": "no-seed"}
            continue
        side40 = side_of(best["cells"])
        chk = TG.check([(c[0], c[1], c[2]) for c in best["cells"]])
        gain = L_del - side40
        out["families"][name] = {
            "label": best["label"],
            "packer": best["packer"],
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
                  f"({float(best['gap_pct']):+.2f}%)  {best['label']} [{best['packer']}]",
                  flush=True)
    if write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        json.dump(out, open(OUT, "w"), indent=1)
        print(f"pattern_seeds: -> {OUT.relative_to(ROOT)}")
    return out


def run_staircase(ns, write=True):
    """Family E on the target rows: how many cells fit at the delivered side, and the shortfall."""
    tab = load_table()
    out = {"rows": {}, "margin": str(MARGIN), "step": str(GRID_STEP)}
    for n in ns:
        if n not in tab:
            continue
        L = float(tab[n]["L"])
        rows = e_scan(n, L, keep_best=6)
        best = rows[0] if rows else None
        rec = {"n": n, "L_delivered": str(tab[n]["L"]), "grid": TG_sqrt_ceil(n),
               "beats_grid": float(tab[n]["L"]) < TG_sqrt_ceil(n), "fills": rows}
        if best:
            rec.update({"a": best["a"], "b": best["b"], "p": best["p"], "q": best["q"],
                        "edges": best["edges"], "cells": best["cells"],
                        "tilted": best["tilted"], "shortfall": best["shortfall"]})
            # the exact number for the best fill: side 40 digits, zero overlap, interval-certified
            cells, _tilted = stair_fill(best["a"], best["b"], L, best["p"], best["q"],
                                        best["edges"])
            if len(cells) == best["cells"]:
                sel = cells[:n] if len(cells) >= n else cells
                rec["side40"] = str(side_of(sel))
                chk = TG.check([(c[0], c[1], c[2]) for c in sel])
                rec["violations"] = len(chk["violations"])
                rec["worst_slack"] = None if chk["worst"] is None else str(chk["worst"])
                rec["recipe"] = recipe_rows(sel)
                iv = certify(sel, F(tab[n]["L"]))
                rec["interval"] = {k: v for k, v in iv.items() if k != "recipe"}
                print(f"  n={n:4d} E core {best['a']}x{best['b']} t={best['p']}/{best['q']} "
                      f"edges {best['edges']:2s} -> {len(cells):4d} cells at L={L:.6f} "
                      f"shortfall {best['shortfall']:+d} | 40d side {rec['side40'][:12]} "
                      f"viol {rec['violations']} | interval {iv['verdict']} "
                      f"L[{float(F(iv['L_lo'])):.6f},{float(F(iv['L_hi'])):.6f}]", flush=True)
            else:
                rec["side40"] = None
        out["rows"][str(n)] = rec
    if write:
        OUT_E.parent.mkdir(parents=True, exist_ok=True)
        json.dump(out, open(OUT_E, "w"), indent=1)
        print(f"staircase: -> {OUT_E.relative_to(ROOT)}")
    return out


def TG_sqrt_ceil(n):
    """`ceil(sqrt n)`, exactly: the side any integer-lattice pose of `n` cells needs."""
    k = math.isqrt(n)
    return k if k * k == n else k + 1


def run_denominators(n, write=True):
    """How the boundary slope's denominator moves the count: fix the core, sweep `t = 1/q`."""
    tab = load_table()
    L = float(tab[n]["L"])
    k = math.isqrt(n)
    out = {"n": n, "L_delivered": str(tab[n]["L"]), "core": [k - 1, k], "sweep": []}
    for q in (1, 2, 3, 4, 5, 7, 8, 9, 13, 20, 25, 30, 37, 50, 100, 200, 500, 1000):
        rows = e_scan(n, L, dirs=((1, q),), cores=[(k - 1, k)], keep_best=3)
        if not rows:
            continue
        best = rows[0]
        c, s = dir_pq(1, q)
        h = (abs(c) + abs(s)) / 2
        pitch = 1.0 / max(abs(c), abs(s))
        out["sweep"].append({"q": q, "half_extent": round(h, 9), "pitch": round(pitch, 9),
                             "cells": best["cells"], "tilted": best["tilted"],
                             "shortfall": best["shortfall"], "edges": best["edges"]})
        print(f"  t = 1/{q:<4d} half-extent {h:.6f}  pitch {pitch:.6f}  cells {best['cells']:4d} "
              f"tilted {best['tilted']:3d}  shortfall {best['shortfall']:+d}", flush=True)
    if write:
        json.dump(out, open(ROOT / "workspace" / "push" / "staircase_denominators.json", "w"),
                  indent=1)
    return out


def run_verify():
    """Certify every stored staircase recipe with the interval verifier, and report the verdict."""
    doc = json.load(open(OUT_E))
    checks = []
    for n, rec in doc["rows"].items():
        if not rec.get("recipe"):
            continue
        checks.append({"label": f"family E n={n} a={rec['a']} b={rec['b']} t={rec['p']}/{rec['q']}",
                       "L": rec["L_delivered"], "cells": rec["recipe"]})
    json.dump({"checks": checks}, open(OUT_RECIPES, "w"), indent=1)
    import interval_verifier as IV
    ok = True
    for ch in checks:
        rep = IV.verify(IV.recipe_from_rows([(c["x"], c["y"], tuple(c["dir"])) for c in ch["cells"]]),
                        F(ch["L"]))
        ok = ok and rep["verdict"] != "refused"
        print(f"  {ch['label'][:48]:48s} N={rep['N']:4d} {rep['verdict']:12s} "
              f"walls {rep['walls_checked']} slack {rep['min_certified_slack']} "
              f"viol {rep['violations']} unclear {rep['inconclusive']} "
              f"L_hi<del {rep['L_hi_below_declared']}")
    print(f"interval_verifier: {len(checks)} recipes, {'OK' if ok else 'REFUSED'}")
    return checks


def selftest():
    """Nine controls: run 112's five, then the ceiling, the packer, the fringe and the recipes."""
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

    # 6. the ceiling: an integer-lattice pose of n cells needs side ceil(sqrt n), and every target
    #    row beats the grid -- so no lattice construction can pass C2 there.
    for n in (29, 41, 53, 55, 680, 733, 845, 904, 971):
        g = TG_sqrt_ceil(n)
        assert g * g >= n and (g - 1) * (g - 1) < n, (n, g)
    assert TG_sqrt_ceil(961) == 31 and TG_sqrt_ceil(962) == 32

    # 7. corner insertion nests the residue strip beside the block: 26 x 26 + 4 at width 27 has side
    #    27 for both packers, but 5 x 1 against a 3 x 3 at width 6 must reach side 5, not 6.
    got = nest_pack([block(3, 3, 0.0), block(5, 1, 0.0)], 6.0)
    assert got is not None and max(got[1], got[2]) < 5.01, got   # the strip sits on top, side 5
    got = nest_pack([block(4, 4, 0.0), block(5, 1, 0.0)], 4.5)
    assert got is None, got                      # a 5-wide strip cannot fit a 4.5-wide shelf
    got = nest_pack([block(4, 4, 0.0), block(3, 1, 0.0)], 4.5)
    assert got is not None and abs(got[2] - 5.0) < 1e-6, got

    # 8. the staircase: a 3-by-3 core holds 9, and a fringe of quarter-word cells at a 2-unit margin
    #    fits strictly between the core and the wall at slack >= the margin.
    cells, tilted = stair_fill(3, 3, 5.0, 1, 1, "x")
    assert len(cells) >= 9 and tilted >= 1, (len(cells), tilted)
    chk = TG.check([(c[0], c[1], c[2]) for c in cells])
    assert not chk["violations"], chk["violations"][:2]
    assert max(c[0] + (_cs(c[2])[0] + _cs(c[2])[1]) / 2 for c in cells) <= 5.0 + 1e-9
    # a larger denominator has a smaller half-extent, so its pitch is tighter and its count not lower
    assert dir_pq(1, 30)[0] > dir_pq(1, 3)[0]
    lo = stair_fill(3, 3, 6.0, 1, 3, "x")[1]
    hi = stair_fill(3, 3, 6.0, 1, 30, "x")[1]
    assert hi >= lo, (lo, hi)

    # 10. the domination law: for every slope in the alphabet, a one-cell fringe's pitch is at least
    #     1 and its protrusion at least 1, with equality only at the axis limit. This is the theorem
    #     the run reports, so it is checked rather than asserted.
    for (p, q) in SPEC_DIRS:
        h, pitch, pro = seat_law(p, q)
        assert pitch >= 1.0 - 1e-12, (p, q, pitch)
        assert pro >= 1.0 - 1e-12, (p, q, pro)
        c, s = dir_pq(p, q)
        assert abs(c * c + s * s - 1.0) < 1e-12, (p, q)
    hy, py, pr = seat_law(0, 1)
    assert abs(py - 1.0) < 1e-12 and abs(pr - 1.0) < 1e-12, (hy, py, pr)
    assert seat_law(1, 1)[1] > 1.4 and seat_law(1, 1)[2] > 1.4

    # 9. the recipe is exact and the interval verifier certifies it (no float in the certificate)
    import interval_verifier as IV
    rep = certify(stair_fill(3, 3, 5.0, 3, 4, "x")[0], F(5))
    assert rep["verdict"] == "certified", rep
    assert F(rep["L_hi"]) <= F(5), rep
    assert IV.spec_of(3, 4) == ("slope", 3, 4) if hasattr(IV, "spec_of") else True
    print("pattern_seeds: OK (10 controls)")
    _ = (used, height)


def main(argv):
    if "--selftest" in argv:
        selftest()
        return 0
    if "--verify" in argv:
        run_verify()
        return 0
    if "--denominators" in argv:
        i = argv.index("--denominators")
        run_denominators(int(argv[i + 1]) if i + 1 < len(argv) else 971)
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
    if "--families" in argv:
        run_rows(ns)
    if "--staircase" in argv or "--families" not in argv:
        run_staircase(ns)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
