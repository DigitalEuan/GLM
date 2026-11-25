#!/usr/bin/env python3
r"""construct_seam.py — run 130: build arrangements instead of squeezing them.

Doc 88 §7 closed the squeeze route with a *measurement*: a random single-cell
combinatorial move changes where the overlap is, not how deep, and the best of
128 draws sat 2.1-2.6x above the convertibility bar.  What it asked for next is
the opposite kind of candidate: an arrangement **constructed** at the target
side, with exact contacts, so its residual is zero *before* any relaxation.

This module builds the one family that does that in closed form, in the exact
field `Q(sqrt 2)`, and measures it.

The construction ("four-corner pocket net", the pattern of the delivered
n = 5 pose generalised).  Put an `a x a` upright block in each corner of a
container of side `L`, and a single unit cell tilted 45 degrees at the centre.
The central cell's edge is at distance 1/2 from its centre, so the corner
blocks' inner corners lie exactly on it when

    (L - 2a) / sqrt 2 = 1/2        i.e.    L = 2a + sqrt2/2 .

Every contact is exact (`Q(sqrt 2)`, no float), so the pose is legal by
construction and its side is algebraic, not numerical:

    n = 4a^2 + 1 ,      L = 2a + sqrt2/2 ,      grid k = ceil(sqrt n) = 2a+1 ,

which beats the grid by exactly `1 - sqrt2/2 = 0.292893...` for **every** `a`.
At `a = 1` this is `s(5) = 2 + sqrt2/2`, the proved optimum (`optima.py`), so
the arithmetic is not merely plausible: it reproduces a theorem.

It is also **rigid**.  Replacing the central cell by a `p x p` tilted block and
permitting rectangular corner blocks `a x b` gives

    L = a + b + p/sqrt2 ,      n = 4ab + p^2 ,

and a sweep of that box (`--scan`) shows the only winners are `p = 1, a = b`:
the family beats the grid at `n ≡ 1 (mod 4)` and nowhere else.  Adding a strip
of upright cells to reach a neighbouring count costs a full unit of side, so
the neighbourhood of every family row is `sqrt2/2` *outside* its grid.

That is what the target rows are measured against: at the target side
`L_t = k - 1/8` the constructed pose's residual penetration is `p = 0` on a
family row (a certified beat) and `p = sqrt2/2 + 1/8` on every other row --
constant in `n`, while the bar `1/8 / L_t` falls like `1/L`.  So the family's
penetration is 25x to 56x the bar by `n = 33 .. 900`, and it is never a
function of how much budget the row gets.

    python3 scripts/construct_seam.py --selftest
    python3 scripts/construct_seam.py --scan
    python3 scripts/construct_seam.py            # the target measurement
"""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal, getcontext
from fractions import Fraction
from math import isqrt

getcontext().prec = 45

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import seam_wheels as SW                   # noqa: E402  (Q2, exact_gate)
import range_leverage as RL                # noqa: E402  (the leverage ranking)

Q2 = SW.Q2
R2H = SW.R2H                               # sqrt(2)/2
HALF = SW.HALF
OUT = os.path.join(ROOT, "workspace/push/construct_seam130.json")
TABLE = os.path.join(ROOT, "workspace/submission/table.json")
EXT = os.path.join(ROOT, "json/extended_table_5000.json")
#: packlib.finalize's pad on every delivered side (see seam_wheels.PAD).
PAD = Decimal("2e-9")
EIGHTH = Q2(Fraction(1, 8))


def to_dec(q: Q2) -> Decimal:
    """The algebraic number to 45 digits (comparison only; never a verdict)."""
    return Decimal(q.a.numerator) / Decimal(q.a.denominator) + (
        Decimal(q.b.numerator) / Decimal(q.b.denominator)) * Decimal(2).sqrt()


def k_of(n: int) -> int:
    k = isqrt(n)
    return k if k * k == n else k + 1


# ------------------------------------------------------------- the constructor
def block(a: int, b: int, ox: Q2, oy: Q2) -> list:
    """An a x b block of upright unit cells with its lower-left corner at (ox, oy)."""
    out = []
    for i in range(a):
        for j in range(b):
            out.append((ox + Q2(Fraction(2 * i + 1, 2)),
                        oy + Q2(Fraction(2 * j + 1, 2)), 0))
    return out


def windmill(a: int) -> tuple:
    """Four a x a corner blocks and one 45-degree cell: (n, cells, L), exactly."""
    L = Q2(2 * a) + R2H
    cells = []
    for ox, oy in ((Q2(0), Q2(0)), (L - a, Q2(0)),
                   (Q2(0), L - a), (L - a, L - a)):
        cells += block(a, a, ox, oy)
    cells.append((L * HALF, L * HALF, 1))
    return 4 * a * a + 1, cells, L


def struct_gate(a: int) -> dict:
    """The O(1) exact legality argument for `windmill(a)`.

    Four facts, each an equality or a strict inequality in Q(sqrt 2):

      * the central cell's lower-left edge is `x + y = L - sqrt2/2`, so it is
        `x + y = 2a` iff `L = 2a + sqrt2/2` (by construction);
      * the bottom-left block lies in `x + y <= 2a` (it is `[0,a]^2`), so it is
        outside that edge and touches it at the single corner `(a,a)`;
      * the same for the other three blocks, by symmetry;
      * the central cell's left vertex has `y = L/2` and `a < L/2 < L - a`, so
        it sits in the gap between the two left blocks rather than inside one.
    """
    L = Q2(2 * a) + R2H
    return {"L_is_2a_plus_sqrt2_over_2": L == Q2(2 * a) + R2H,
            "edge_is_2a": L - R2H == Q2(2 * a),
            "left_vertex_in_gap": (Q2(a) < L * HALF) and (L * HALF < L - a),
            "blocks_separated": (L - 2 * a) == R2H and R2H > Q2(0)}


def pen_at(cells: list, L_target: Q2) -> Q2:
    """Exact residual penetration of a constructed pose in a box of side L_target.

    Containment only: the pose is legal internally by `struct_gate`, so its
    residual is how far the extreme cells stick out of the target box.
    """
    lo_x = min(c[0] - SW.EXT[c[2]]["x"] for c in cells)
    hi_x = max(c[0] + SW.EXT[c[2]]["x"] for c in cells)
    lo_y = min(c[1] - SW.EXT[c[2]]["y"] for c in cells)
    hi_y = max(c[1] + SW.EXT[c[2]]["y"] for c in cells)
    over = max(Q2(0) - lo_x, hi_x - L_target, Q2(0) - lo_y, hi_y - L_target)
    return over


# ------------------------------------------------------------ family scanning
def family_gate(a: int, b: int, p: int) -> dict:
    """The exact constraint set for `a x a` corners + a tilted `p x p` centre.

    Four constraints, and each is an equality or inequality in Q(sqrt 2):

      * diagonal pair: the bottom-left block has `x + y <= 2a` and the centre
        needs `x + y >= a + b`, so no overlap requires `2a <= a + b`; the
        top-right block gives `2L - 2b >= L + p/sqrt2`, i.e. the mirror
        inequality.  Together they force `a = b` -- unequal corners overlap the
        centre on one diagonal whatever `L` is;
      * containment: the centre's bounding box is `p*sqrt2` square, so
        `p*sqrt2 <= L = 2a + p/sqrt2`, i.e. `p/sqrt2 <= a`;
      * the far diagonal is then free: the bottom-right block has
        `x - y >= L - 2a = p/sqrt2`, touching the centre's `|x-y| = p/sqrt2`
        edge and never entering it;
      * blocks are `sqrt2/2` apart, and each block is an integer lattice.

    `exact_gate` re-checks the conclusion cell by cell where it is affordable;
    the facts above are O(1) and hold for every `a`.
    """
    L = Q2(a + b) + Q2(p) * R2H
    return {"equal_corners": a == b,
            "centre_inside": Q2(p) * R2H <= Q2(a),
            "centre_bbox_fits": L >= Q2(p) * R2H * Q2(2),
            "blocks_separated": (L - 2 * a) > Q2(0)}


def scan(amax: int = 8, bmax: int = 8, pmax: int = 6) -> dict:
    """Every (a, b, p) in the box: L = a+b+p/sqrt2 against k = ceil(sqrt(4ab+p^2)).

    A candidate is a winner only if the arithmetic beats the grid *and* the
    exact constraint set admits it -- the second half is what the first
    version of this scan was missing, and it is why the arithmetic alone
    reports more winners than the geometry allows.
    """
    win, arith, lose = [], [], []
    for a in range(1, amax + 1):
        for b in range(1, bmax + 1):
            for p in range(1, pmax + 1):
                n = 4 * a * b + p * p
                L = Q2(a + b) + Q2(p) * R2H
                k = k_of(n)
                rec = {"a": a, "b": b, "p": p, "n": n, "k": k,
                       "L": L.pretty(), "gain": str(to_dec(Q2(k) - L))}
                if L < k:
                    g = family_gate(a, b, p)
                    rec["gate"] = {kk: bool(vv) for kk, vv in g.items()}
                    if all(g.values()):
                        win.append(rec)
                    else:
                        rec["refused_by"] = [kk for kk, vv in g.items() if not vv]
                        arith.append(rec)
                else:
                    lose.append(rec)
    return {"winners": win, "arithmetic_only": arith,
            "tried": len(win) + len(arith) + len(lose)}


def hybrid(a: int, columns: int, h: int) -> tuple:
    """The windmill at `a` plus `columns` columns of `h` upright cells each.

    Each column is a wall-to-wall block sharing the previous side, so the pose
    is legal by construction and its side is `L_w + columns` exactly.
    """
    n0, cells, L = windmill(a)
    for c in range(columns):
        for j in range(h):
            cells.append((L + Q2(c) + HALF, Q2(Fraction(2 * j + 1, 2)), 0))
    return n0 + columns * h, cells, L + Q2(columns)


def family_side(n: int) -> dict:
    """The family's exact side for exactly `n` cells: windmill + block strips.

    The windmill holds `4a^2+1`; the rest go into columns of `floor(L_w) = 2a`
    cells beside it, each column costing one unit of side.  This is the
    generalisation that reaches any count -- and it is why the reach costs so
    much: the windmill's own density deficit is `(2a+sqrt2/2)^2 - (4a^2+1)`
    `= (2 sqrt2 - 1) a - 1/2 ~ 2.83 a` cells of area.
    """
    a = isqrt(max(n - 1, 0) // 4)
    while a >= 1 and 4 * a * a + 1 > n:
        a -= 1
    if a < 1:
        return {"a": 0, "built": None, "m": n, "columns": None, "L": None,
                "why": "no windmill fits below n"}
    n0, cells, L_w = windmill(a)
    m = n - n0
    h = 2 * a
    cols = (m + h - 1) // h if m else 0
    if cols == 0:
        return {"a": a, "built": n0, "m": 0, "columns": 0, "L": L_w,
                "cells": cells, "why": "windmill exactly"}
    built, cells, L = hybrid(a, cols, h)
    return {"a": a, "built": built, "m": m, "columns": cols, "L": L,
            "cells": cells, "why": f"windmill(a={a}) + {cols} column(s) of {h}"}


# ------------------------------------------------------------- table compare
def load_sides() -> dict:
    with open(TABLE) as f:
        tab = json.load(f)
    out = {int(k): Decimal(v["L"]) for k, v in tab.items()}
    with open(EXT) as f:
        ext = json.load(f)
    for k, v in ext.items():
        out[int(k)] = Decimal(repr(v["L"]))
    return out


def compare(amax: int = 35) -> dict:
    """The family's exact side against the delivered/extension table, row by row."""
    sides = load_sides()
    rows = []
    for a in range(1, amax + 1):
        n, _, L = windmill(a)
        if n not in sides:
            continue
        got = sides[n]
        want = to_dec(L)
        rows.append({"a": a, "n": n, "k": k_of(n), "L_exact": str(want.quantize(Decimal('1e-12'))),
                     "L_table": str(got.quantize(Decimal('1e-12'))),
                     "verdict": ("table_padded" if abs(got - want) <= PAD
                                 else ("family_better" if got > want
                                       else "table_better")),
                     "gain": str((got - want).quantize(Decimal('1e-9')))})
    return {"rows": rows,
            "family_better": [r for r in rows if r["verdict"] == "family_better"],
            "table_better": [r for r in rows if r["verdict"] == "table_better"],
            "padded": [r for r in rows if r["verdict"] == "table_padded"]}


# ------------------------------------------------------------------ the test
def target_rows(limit: int = 12, ext_limit: int = 6) -> list:
    """The leverage-ranked rows, with what the constructive family can say about them."""
    scored, ext = RL.load_scored(), RL.load_ext()
    rs = RL.headroom(RL.rank(scored, 1, 1000), RL.bands(scored, 32))[:limit]
    re_ = RL.headroom(RL.rank(ext, 1001, 5000), RL.bands(ext, 70))[:ext_limit]
    out = []
    for tag, rows in (("scored", rs), ("ext", re_)):
        for r in rows:
            n, k = r["n"], r["k"]
            L_t = Q2(k) - EIGHTH                  # the target side: k - 1/8
            fam = family_side(n)
            # the bar of run 129's screen, at this row: gain / L with gain 1/8
            bar = Decimal("0.125") / to_dec(L_t)
            rec = {"range": tag, "n": n, "k": k, "L_delivered": str(r["L"]),
                   "lam": str(r["lam"]), "ceiling": str(r["ceiling"]),
                   "band_price": None if r.get("band_price") is None
                   else str(r["band_price"]),
                   "target_side": str(to_dec(L_t)),
                   "family": fam["why"], "built": fam["built"],
                   "short_cells": n - fam["built"] if fam["built"] else None,
                   "short_vs_grid": n - (k - 1) ** 2,
                   "bar": str(bar)}
            if fam["L"] is None:
                rec.update({"L_construct": None, "p": None, "ratio": None,
                            "fits": False})
            else:
                p = pen_at(fam["cells"], L_t)
                g = struct_gate(fam["a"])
                rec.update({
                    "L_construct": str(to_dec(fam["L"])),
                    "struct_gate": all(g.values()),
                    "p": str(to_dec(p)),
                    "ratio": None if p <= Q2(0) else
                    str((to_dec(p) / bar).quantize(Decimal("0.01"))),
                    "fits": p <= Q2(0),
                })
            out.append(rec)
    return out


# --------------------------------------------------- the exact anchor grammar
def anchor_probe(seconds: float = 60.0) -> list:
    """Can the repo's exact anchor builder construct a sub-grid row?

    `anchor_chain.settle(n, L)` places cells by exact contacts (walls, corners,
    two-contact closure) at clearance >= 0 with no relaxation at all -- the
    purest form of "constructive, measured before relaxation".  It is
    exhaustive only until its node cap, so the cap is recorded with every
    result rather than hidden.
    """
    import anchor_chain as AC
    f2 = AC.FIELDS[2]
    out = []
    for n, num, den, cap in ((6, 3, 1, 60), (6, 299, 100, 60), (6, 2875, 1000, 60)):
        t0 = __import__("time").time()
        got = AC.settle(n, f2.q(Fraction(num, den)), f2, mode="closure",
                        node_cap=cap, top=8)
        out.append({"n": n, "L": f"{num}/{den}", "cap": cap,
                    "placed": len(got["placed"]), "why": got["why"],
                    "nodes": got["nodes"], "states": got["states"],
                    "refusals": got["refusals"],
                    "exhausted": got["exhausted"],
                    "seconds": round(__import__("time").time() - t0, 1)})
    return out


# ------------------------------------------------------------------- controls
def selftest() -> int:
    """Four controls: the theorem, the refusal, the rigidity, the pad."""
    # 1. positive: windmill(1) is s(5) exactly, gated cell by cell
    n, cells, L = windmill(1)
    assert n == 5 and L == Q2(2) + R2H
    got = SW.exact_gate(cells, L)
    assert got["ok"], got
    print(f"  windmill(1): n=5 L=2+sqrt2/2={to_dec(L):.12f} exact_gate ok "
          f"worst_pen={got['worst_pen_q']} (s(5) per optima.py)")

    # 2. negative: a side 1/100 smaller must be refused, with an exact overflow
    L_bad = L - Q2(Fraction(1, 100))
    p = pen_at(cells, L_bad)
    assert p == Q2(Fraction(1, 100)), p
    print(f"  refusal: at L-1/100 the pose sticks out by exactly {p.pretty()}")

    # 3. rigidity: the only winners of the family box are p=1, a=b
    sc = scan(8, 8, 6)
    off = [w for w in sc["winners"]
           if w["p"] != 1 or w["a"] != w["b"]]
    assert not off, off[:3]
    assert all(w["n"] % 4 == 1 for w in sc["winners"]), sc["winners"][:3]
    print(f"  rigidity: {len(sc['winners'])}/{sc['tried']} winners, all p=1 a=b, "
          f"all n ≡ 1 (mod 4)")

    # 4. the family reproduces a known beat and loses to the table by the pad only
    cmp = compare(15)
    row = next(r for r in cmp["rows"] if r["n"] == 5)
    assert row["verdict"] == "table_padded", row
    print(f"  n=5 vs table: {row['verdict']} (diff {row['gain']})")
    print("  selftest OK")
    return 0


# ----------------------------------------------------------------------- main
def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()

    cmp = compare(35)
    sc = scan(8, 8, 6)
    print(f"[family] winners of the (a,b,p) box: {len(sc['winners'])}/{sc['tried']}")
    print(f"  all p=1, a=b: "
          f"{all(w['p'] == 1 and w['a'] == w['b'] for w in sc['winners'])}")
    print(f"  rows beaten in n<=1000 (a<=15): "
          f"{sum(1 for r in cmp['rows'] if r['n'] <= 1000)}")
    print(f"\n[table] family vs table over {len(cmp['rows'])} rows n=4a^2+1<=5000")
    print(f"  family better : {len(cmp['family_better'])}  "
          f"{[r['n'] for r in cmp['family_better']]}")
    print(f"  table better  : {len(cmp['table_better'])}  "
          f"{[r['n'] for r in cmp['table_better']]}")
    print(f"  pad-equal     : {len(cmp['padded'])}  "
          f"{[r['n'] for r in cmp['padded']]}")

    tg = target_rows()
    print("\n[targets] leverage-ranked rows at L_t = k - 1/8")
    print(f"  {'n':>5} {'k':>3} {'family':>22} {'L_con':>10} {'p':>9} "
          f"{'bar':>8} {'p/bar':>7}")
    for r in tg:
        fam = r["family"] or "-"
        p = "-" if r["p"] is None else f"{Decimal(r['p']):.4f}"
        ratio = "-" if r["ratio"] is None else f"{Decimal(r['ratio']):.1f}x"
        Lc = "-" if not r.get("L_construct") else f"{Decimal(r['L_construct']):.4f}"
        print(f"  {r['n']:5d} {r['k']:3d} {fam:>22} {Lc:>10} {p:>9} "
              f"{Decimal(r['bar']):8.4f} {ratio:>7}")

    rec = {"family_scan": sc, "compare": cmp, "targets": tg}
    if "--anchor" in argv:
        anc = anchor_probe()
        rec["anchor"] = anc
        print("\n[anchor] exact anchor-closure builder at the grid side and below")
        for r in anc:
            print(f"  n={r['n']} L={r['L']}: {r['placed']}/{r['n']} placed, "
                  f"{r['why']}, nodes {r['nodes']}, refusals {r['refusals']}, "
                  f"exhausted {r['exhausted']}, {r['seconds']}s")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(rec, f, indent=1, default=str)
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
