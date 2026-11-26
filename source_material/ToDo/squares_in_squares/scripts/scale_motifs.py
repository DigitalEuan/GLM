#!/usr/bin/env python3
r"""scale_motifs.py — the exact, float-free audit of the scalable motif families on n = 101..1000.

WHAT IS AUDITED, AND WHY THESE THREE.

The delivered table has 554 beats and 446 grid ties over n = 1..1000.  The high rows
were built by composing small verified packings, by Friedman's unit-border inflation, and
from the parametric motifs of the literature.  Run 151 asked whether the table had
actually exploited them, so this script re-derives each family from its own law and
compares it, *exactly*, with the delivered side of every row in 101..1000:

  (A) k x k products.  From a verified packing of m squares in side L, k^2 translated
      copies give k^2 m squares in side k L, and dropping any r cells of the copies gives
      k^2 m - r in the same side (0 <= r <= m - 1).  Written once, that is the whole
      family: every n in [k^2 m - m + 1, k^2 m] at side k L.
  (B) Friedman's L-border inflation.  Put the base in the corner of an (L+1)-square and
      fill the two unit strips with axis-aligned unit cells: floor(L+1) up one side,
      floor(L+1) along the other, the corner shared, so

          n' = n + 2 floor(L+1) - 1 = n + 2 floor(L) + 1,   L' = L + 1,

      iterated while n' stays in the window.
  (C) the parametric motifs.  A b x b block of unit squares at a rational word
      (8-15-17: cos = 8/17, sin = 15/17) or the 45-degree word, corner-anchored, with
      every axis-aligned unit square that fits exactly in the remainder added by an exact
      greedy fill judged cell by cell with the SAT gate.  This covers the "centred /
      off-centre b x b 45-degree block" and the "rational spinor" as *constructions*: the
      count and the side are read off the pose, never off a remembered formula.
  (D) composites (run 153).  A base and an exact motif in its leftover: the base sits in
      `[0, L]^2`, the motif's square bbox in `[L, L+S]^2` (the far corner), and both
      L-shaped strips — which are the whole free area, `2 L S` — are filled to the integer
      lattice.  `n = n_base + m + 2 nx ny` with `nx = floor(L+S) - ceil(L)`, `ny = floor(L)`.
      Because `n_base <= L^2` and `m <= S^2`, every composite satisfies `n <= (L+S)^2`: a
      composite is a **grid-or-worse** construction by construction, which is what run 153
      measures (one grid tie, everything else at least 3e-3 above).

NOTHING IS APPROXIMATE.  The delivered sides are 45-digit Decimals computed from the
CSV's own decimal text; the trigonometric functions are `true_geom`'s Decimal series, so
no float touches them.  Every candidate side is an element of the base's own quadratic
field — `Q(sqrt k)` for the k of its words, `Q(sqrt 2)` when they are rational — read off
an exact pose, and the comparison is `L + 1e-8 <= delivered(n)` with `1e-8` an exact
Fraction, i.e. a candidate must beat the delivered row by the project's whole margin.  A
strict beat is then *verified*: the exact SAT gate (`qsqrt2.gate`, which is one procedure
over any `exact_field.Quad(d)`) plus a certificate in `verify_certificates`' schema, at
clearance >= 0.

WHICH ROWS ARE BASES (run 152).  A row is rebuilt when every angle is a declared word of
the unit circle of degree <= 2: the rational words (Pythagorean / half-angle, in Q), the
45-degree word, and every word with `cos^2`, `sin^2` rational (`exact_words.classify`).
Quarter turns are the axis word, so a row turned by pi/2 is the same sentence.  That lifts
the census from 519 rows (Run 151, 0/45 degrees only) to 552, and the ledger records the
refusal of the other 448 by name: an angle that is not a word, or two different radicals.

WHAT IT FOUND (runs 151-153).  Zero strict beats in any family on any row of 101..1000.
(A) and (B) are the table's own constructions, so every row they reach is already at or
below their side; (C)'s area ceiling is the area bound itself and the staircase waste in
the corner fill leaves every realised pose above sqrt(n) by more than the delivered rows
are; (D) is bounded by `(L+S)^2` and so cannot exceed grid density at all.  The pattern is
structural, not bad luck: **a composition of rigid tiles cannot beat a row that is
denser than the grid**, and 554 of the delivered rows are.

USAGE
    python3 scripts/scale_motifs.py --selftest   # 15 controls
    python3 scripts/scale_motifs.py              # the audit, ledger written
    python3 scripts/scale_motifs.py --promote    # C1 on every strict beat (none)
"""
from __future__ import annotations

import json
import math
import os
import sys
from decimal import Decimal, getcontext, localcontext
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import exact_field as EF          # noqa: E402  (the bytecode audit)
import exact_words as EW          # noqa: E402  (the word catalogue: Q and Q(sqrt k))
import qsqrt2 as QS              # noqa: E402  (the gate, side, words; Q2 is its default)
import verify_certificates as VC  # noqa: E402  (C1: the certificate schema)

from qsqrt2 import AXIS, Q2, gate, side, word_45  # noqa: E402

getcontext().prec = 50
sys.set_int_max_str_digits(1_000_000)

SUBMISSION = os.path.join(ROOT, "workspace/submission/submission.csv")
LEDGER = os.path.join(ROOT, "workspace/push/scale_motifs.json")

#: the project's noise floor: a row is beaten only by at least this much
MARGIN_D = Decimal("1e-8")
MARGIN = F(1, 10 ** 8)

N_LO, N_HI = 101, 1000

#: a CSV angle is "the 45-degree word" when it is within this of pi/4, in decimal text
#: (kept for the docstring's vocabulary; the classifier decides the words now)

#: the base must reproduce the delivered side to this, or it is not that row's sentence
REPRO = Decimal("5e-9")

#: the rational words of the parametric family, all exact
WORDS = {"45": word_45(),
         "8-15-17": (Q2(F(8, 17)), Q2(F(15, 17))),
         "3-4-5": (Q2(F(3, 5)), Q2(F(4, 5)))}

#: bases, so a beat can be rebuilt when it is verified
BASES: dict = {}


# ---------------------------------------------------------------- decimal shadow
def z2dec(z, places: int = 45) -> Decimal:
    """`z` (an element of any `Q(sqrt k)`) as a Decimal at `places`.

    `Quad.decimal` takes sqrt(k) by Decimal's own sqrt at the working precision, so this
    shadow differs from the true value by less than 10^-places; every comparison is made
    with an 1e-8 margin, so no decision can depend on the shadow's last digits.
    """
    with localcontext() as ctx:          # callers set their own ambient precision
        ctx.prec = max(places + 20, 60)
        return Decimal(z.decimal(places))


def grid(n: int) -> int:
    k = math.isqrt(n)
    return k if k * k == n else k + 1


#: run 151's base rule, kept so the extension's *new* sentences can be named and gated
_OLD_TOL = Decimal("1e-9")
_OLD_PI4 = Decimal("0.7853981633974483096")
_OLD_PI = Decimal("3.1415926535897932384")


def old_rule_row(cells) -> bool:
    """Run 151's rule: every angle is 0, pi or pi/4 within the CSV's own 1e-9."""
    for _x, _y, a in cells:
        if abs(a) <= _OLD_TOL or abs(a - _OLD_PI) <= _OLD_TOL or abs(a - _OLD_PI4) <= _OLD_TOL:
            continue
        return False
    return True


# ---------------------------------------------------------------- the delivered table
def load_delivered():
    """`{n: (Decimal side, [(Decimal x, y, angle)])}` from the CSV, without a float.

    The side is measured the way `sqscore.extent` measures it, at 45 digits, with
    `true_geom`'s Decimal `cos`/`sin`.
    """
    import true_geom as TG
    per = {}
    with open(SUBMISSION) as f:
        names = [h.strip() for h in f.readline().split(",")]
        ix = {h: i for i, h in enumerate(names)}
        for line in f:
            parts = line.rstrip("\n").split(",")
            if len(parts) < len(names):
                continue
            n = int(parts[ix["n"]])
            per.setdefault(n, []).append((Decimal(parts[ix["x"]].strip()),
                                          Decimal(parts[ix["y"]].strip()),
                                          Decimal(parts[ix["angle"]].strip())))
    return {n: (TG.side(cells), cells) for n, cells in per.items()}


# ------------------------------------------------------------------- exact bases
class Base:
    """A delivered row rebuilt exactly in its own field: the pose a family grows from."""

    __slots__ = ("n", "cells", "words", "L", "kind", "field", "cls", "gated")

    def __init__(self, n, cells, words, L, kind, cls, field):
        self.n, self.cells, self.words, self.L = n, cells, words, L
        self.kind, self.cls, self.field = kind, cls, field
        self.gated = None

    def gate(self):
        if self.gated is None:
            self.gated = gate(self.cells, self.words, self.cls)
        return self.gated


def row_words(cells):
    """`(words, k)` when every angle is a declared word in one field, else `(None, reason)`.

    A word is a point of the unit circle algebraic of degree <= 2: the rational words
    (`k = 1`), the 45-degree word, and every word with `cos^2`, `sin^2` rational in
    `Q(sqrt k)` (`exact_words.classify`).  A row mixing two different radicals needs a
    degree-4 tower and is refused rather than approximated.
    """
    ws, k = [], 1
    for _x, _y, a in cells:
        w = EW.classify(a)
        if w is None:
            return (None, "an angle that is not a declared word")
        if w.k > 1:
            if k != 1 and k != w.k:
                return (None, "two different quadratic fields")
            k = w.k
        ws.append(w)
    return (ws, k)


def base_of(n: int, deliv) -> Base | None:
    """Rebuild row `n` exactly in the row's own field, if every angle is a declared word.

    The centres are the CSV's own decimal text, hence exact rationals; the words are exact
    elements of `Q(sqrt k)`; so the pose is an exact sentence.  Two guards keep the base
    honest: every word's `cos^2 + sin^2 = 1` is checked in the field, and the rebuilt side
    must reproduce the delivered side to `REPRO` -- a row whose angles merely *look* like
    a word cannot enter the census as that row.
    """
    side_d, cells = deliv[n]
    ws, k = row_words(cells)
    if ws is None:                            # `k` carries the refusal reason
        return None
    kk = k if k > 1 else 2
    cls = EW.quad(kk)
    st, words = [], []
    for (x, y, _a), w in zip(cells, ws):
        c, s = w.element(kk)
        st.append((cls(F(x)), cls(F(y))))
        words.append((c, s))
    if len(st) != n:
        return None
    ex = [QS.frame_extent(c, s, cls) for c, s in words]
    lo_x = min(st[i][0] - ex[i] for i in range(n))
    lo_y = min(st[i][1] - ex[i] for i in range(n))
    st = [(x - lo_x, y - lo_y) for x, y in st]
    L = side(st, words, cls)
    if abs(z2dec(L, 45) - side_d) > REPRO:
        return None                       # the row is not this sentence
    tags = {w.name for w in ws}
    kind = "45" if tags == {"45"} else ("axis" if tags == {"axis"} else "mixed")
    field = "Q" if k == 1 else f"Q(sqrt {kk})"
    return Base(n, st, words, L, kind, cls, field)


# ------------------------------------------------------------------- family (A)
def product_cells(base: Base, k: int, drop: int = 0):
    """`k^2 m - drop` cells: translated copies, truncated in the last one.

    Dropping cells cannot create an overlap and cannot grow the box, so validity is
    structural; any candidate that is a strict beat is still passed through the gate.
    """
    want = k * k * base.n - drop
    cells, words = [], []
    for j in range(k):
        for i in range(k):
            if len(cells) >= want:
                return cells, words
            dx, dy = base.cls(i) * base.L, base.cls(j) * base.L
            for idx in range(base.n):
                if len(cells) >= want:
                    return cells, words
                x, y = base.cells[idx]
                cells.append((x + dx, y + dy))
                words.append(base.words[idx])
    return cells, words


def family_product(bases):
    """Every `(n, L, k, m, drop)` the k x k family reaches inside the window."""
    out = []
    for m, base in bases.items():
        for k in (2, 3):
            hi_n = k * k * m
            lo_n = hi_n - (m - 1)
            if hi_n < N_LO or lo_n > N_HI:
                continue
            L = base.L * base.cls(k)
            for r in range(0, m):
                n = hi_n - r
                if N_LO <= n <= N_HI:
                    out.append({"family": "A-product", "n": n, "L": L, "k": k,
                                "m": m, "drop": r, "field": base.field})
    return out


# ------------------------------------------------------------------- family (B)
def border_count(L) -> int:
    """`2 floor(L+1) - 1`, the cells a unit border adds.  Exact in any `Quad`."""
    return 2 * (L.floor() + 1) - 1


def inflate_cells(base: Base, steps: int):
    """The pose after `steps` border inflations and the side after each one."""
    one, half = base.cls(1), base.cls(F(1, 2))
    cells, words, L = list(base.cells), list(base.words), base.L
    sides = []
    for _ in range(steps):
        row = (L + one).floor()
        moved = [(x + one, y + one) for x, y in cells]
        mw = list(words)
        for j in range(row):                      # vertical strip: x in [0,1]
            moved.append((half, base.cls(j) + half))
            mw.append((one, base.cls(0)))
        for i in range(1, row):                   # horizontal strip: y in [0,1]
            moved.append((base.cls(i) + half, half))
            mw.append((one, base.cls(0)))
        cells, words, L = moved, mw, L + one
        sides.append(L)
    return cells, words, sides


def family_inflate(bases, steps_max: int = 12):
    """The cascade from every exact base, iterated while `n` stays in the window."""
    out = []
    for m, base in bases.items():
        n, L = m, base.L
        for j in range(1, steps_max + 1):
            add = border_count(L)
            n2, L2 = n + add, L + base.cls(1)
            if n2 > N_HI:
                break
            if n2 >= N_LO:
                out.append({"family": "B-inflate", "n": n2, "L": L2, "steps": j,
                            "m": m, "added": add, "field": base.field})
            n, L = n2, L2
    return out


# ------------------------------------------------------------------- family (C)
def _bucket_add(buckets, idx, x, y):
    buckets.setdefault((QS.floor_q2(x), QS.floor_q2(y)), []).append(idx)


def _bucket_near(buckets, x, y, rad: int = 2):
    i, j = QS.floor_q2(x), QS.floor_q2(y)
    out = []
    for di in range(-rad, rad + 1):
        for dj in range(-rad, rad + 1):
            lst = buckets.get((i + di, j + dj))
            if lst:
                out.extend(lst)
    return out


def rot_block_cells(b: int, word, extra: int = 0):
    """A b x b block at `word`, corner-anchored, plus the exact grid fill around it.

    The block's bbox is a square of side `b (|c| + |s|)`; place it with that bbox at the
    origin, then add every axis-aligned unit cell inside `[0,S]^2` that clears the block
    and the earlier fillers, judged pair by pair with the exact SAT predicate.  Cells
    whose centres differ by 2 or more on an axis are skipped by the same exact rule the
    gate uses, which is what the bucket index implements.
    """
    cells, words = [], []
    c, s = word
    for j in range(b):
        for i in range(b):
            u = Q2(i) + Q2(F(1, 2)) - Q2(b) * Q2(F(1, 2))
            v = Q2(j) + Q2(F(1, 2)) - Q2(b) * Q2(F(1, 2))
            cells.append((c * u - s * v, c * v + s * u))
            words.append(word)
    ex = QS.frame_extent(c, s)
    lo_x = min(x - ex for x, y in cells)
    lo_y = min(y - ex for x, y in cells)
    hi_x = max(x + ex for x, y in cells)
    hi_y = max(y + ex for x, y in cells)
    cells = [(x - lo_x, y - lo_y) for x, y in cells]
    S = (hi_x - lo_x) if (hi_x - lo_x) > (hi_y - lo_y) else (hi_y - lo_y)
    S = S + Q2(extra)
    buckets = {}
    for idx, (x, y) in enumerate(cells):
        _bucket_add(buckets, idx, x, y)
    span = QS.floor_q2(S)
    half = Q2(F(1, 2))
    for j in range(span):
        for i in range(span):
            cand = (Q2(i) + half, Q2(j) + half)
            if cand[0] + half > S or cand[1] + half > S:
                continue
            ok = True
            for idx in _bucket_near(buckets, cand[0], cand[1]):
                trial = [cells[idx], cand]
                tw = [words[idx], AXIS]
                if not any(sl.sign() >= 0 for _q, sl, _n, _o in QS.pair_axes(trial, tw, 0, 1)):
                    ok = False
                    break
            if ok:
                cells.append(cand)
                words.append(AXIS)
                _bucket_add(buckets, len(cells) - 1, cand[0], cand[1])
    return cells, words


def family_rot_block(b_max: int = 20, extra_max: int = 2):
    """The parametric candidates: `(n, L, word, b, extra)`, each an exact pose."""
    out = []
    for name, word in WORDS.items():
        for b in range(2, b_max + 1):
            for extra in range(0, extra_max + 1):
                cells, words = rot_block_cells(b, word, extra)
                if not cells:
                    continue
                out.append({"family": "C-rot-block", "n": len(cells),
                            "L": side(cells, words), "word": name, "b": b,
                            "extra": extra, "cells": cells, "words": words})
    return out


# --------------------------------------------------------------- family (D)
class Motif:
    """A rigid exact pose with a square bbox: what a composite puts in the far corner."""

    __slots__ = ("name", "cells", "words", "S", "n")

    def __init__(self, name, cells, words, S):
        self.name, self.cells, self.words, self.S = name, cells, words, S
        self.n = len(cells)


_MOTIF_CACHE = {}


def motif_library(bases, b_max: int = 5, small_l_max: int = 6):
    """The rigid motifs: the C poses (block + exact fill) and the smallest bases.

    A base is itself a rigid pose whose bbox is a square of side L, so it is a legal motif;
    the small ones are included because the second tile has to be cheap to place, and a
    base is the densest tile this project owns.
    """
    key = (id(bases), b_max, small_l_max)
    if key in _MOTIF_CACHE:
        return _MOTIF_CACHE[key]
    out = []
    for wname, word in WORDS.items():
        for b in range(2, b_max + 1):
            cells, words = rot_block_cells(b, word)
            out.append(Motif(f"{wname}/b{b}", cells, words, side(cells, words)))
    for n, base in sorted(bases.items()):
        if base.cls.d == 2 and base.L.floor() <= small_l_max:
            out.append(Motif(f"base{n}", base.cells, base.words, base.L))
    _MOTIF_CACHE[key] = out
    return out


def rect_counts(L, S):
    """The integer unit cells that fit in `[L, L+S] x [0, L]`: `(nx, ny)`, exactly."""
    nx = (L + S).floor() - L.ceil()
    ny = L.floor()
    return (nx if nx > 0 else 0), (ny if ny > 0 else 0)


def composite_count(base, motif) -> int:
    """`n + m + 2 nx ny`: the base, the motif, and both L-shaped strips filled to the lattice."""
    nx, ny = rect_counts(base.L, motif.S)
    return base.n + motif.n + 2 * nx * ny


def composite_pose(base, motif, drop: int = 0):
    """The composite's exact pose: base at the origin, motif's bbox in the far corner.

    The two bboxes are `[0, L]^2` and `[L, L+S]^2`, so every cell of one is separated from
    every cell of the other by an axis line and validity is structural; the two strips are
    the whole free area (`(L+S)^2 - L^2 - S^2 = 2 L S`) and are filled to the integer
    lattice, which is what `rect_counts` counts.
    """
    one, half = base.cls(1), base.cls(F(1, 2))
    cells, words = list(base.cells), list(base.words)
    for (x, y), w in zip(motif.cells, motif.words):
        cells.append((x + base.L, y + base.L))
        words.append(w)
    nx, ny = rect_counts(base.L, motif.S)
    x0 = y0 = base.L.ceil()
    for dy in range(ny):                      # strip 1: x in [L, L+S], y in [0, L]
        for dx in range(nx):
            cells.append((base.cls(x0 + dx) + half, base.cls(dy) + half))
            words.append((one, base.cls(0)))
    for dx in range(ny):                      # strip 2: x in [0, L], y in [L, L+S]
        for dy in range(nx):
            cells.append((base.cls(dx) + half, base.cls(y0 + dy) + half))
            words.append((one, base.cls(0)))
    if drop:
        cells, words = cells[:-drop], words[:-drop]
    return cells, words


def family_composite(bases, motifs, trims: int = 3):
    """Every `(n, L)` the corner composite reaches: base + motif + both strips."""
    out = []
    for m, base in sorted(bases.items()):
        if base.cls.d != 2:
            continue                  # two radicals would need a degree-4 tower
        for mo in motifs:
            nx, ny = rect_counts(base.L, mo.S)
            n0 = base.n + mo.n + 2 * nx * ny
            S = base.L + mo.S
            for r in range(trims):
                n = n0 - r
                if N_LO <= n <= N_HI:
                    out.append({"family": "D-composite", "n": n, "L": S, "m": m,
                                "motif": mo.name, "drop": r,
                                "added": mo.n + 2 * nx * ny, "field": base.field})
    return out


# ------------------------------------------------------------------- the audit
def compare(L: Q2, deliv_side: Decimal) -> dict:
    """`L` against a delivered side: `beat` iff `L + 1e-8 <= delivered`."""
    Ld = z2dec(L, 45)
    return {"L_dec": Ld, "margin": deliv_side - Ld,
            "beat": Ld + MARGIN_D <= deliv_side}


def _rec(c, cmp):
    rec = {"family": c["family"], "n": c["n"], "L": z2dec(c["L"], 18),
           "margin": cmp["margin"], "beat": cmp["beat"]}
    for key in ("k", "m", "drop", "steps", "added", "word", "b", "extra", "field",
                "motif"):
        if key in c:
            rec[key] = c[key]
    return rec


def audit(bases, deliv, verbose: bool = True):
    """Run the three families, compare exactly, report every strict beat."""
    cands = (family_product(bases) + family_inflate(bases) + family_rot_block()
             + family_composite(bases, motif_library(bases)))
    cands = [c for c in cands if N_LO <= c["n"] <= N_HI]
    best, beats = {}, []
    per = {}
    for c in cands:
        n = c["n"]
        cmp = compare(c["L"], deliv[n][0])
        rec = _rec(c, cmp)
        slot = per.setdefault(c["family"], {"candidates": 0, "rows": set(),
                                            "best_margin": None, "beats": 0})
        slot["candidates"] += 1
        slot["rows"].add(n)
        if slot["best_margin"] is None or cmp["margin"] > slot["best_margin"]:
            slot["best_margin"] = cmp["margin"]
        if cmp["beat"]:
            slot["beats"] += 1
            beats.append({**rec, "_cand": c})
        cur = best.get(n)
        if cur is None or cmp["margin"] > cur["margin"]:
            best[n] = rec
    summary = {k: {"candidates": v["candidates"], "rows": len(v["rows"]),
                   "best_margin": v["best_margin"], "beats": v["beats"]}
               for k, v in sorted(per.items())}
    if verbose:
        print(f"scale_motifs: {len(cands)} candidates over n = {N_LO}..{N_HI}, "
              f"{len(best)} rows reached, {len(beats)} strict beat(s)")
        for k, v in summary.items():
            print(f"  {k:12s} {v['candidates']:7d} candidates, {v['rows']:4d} rows, "
                  f"{v['beats']:3d} beats, best margin {v['best_margin']:+.6f}")
        for n in (101, 120, 272, 500, 1000):
            r = best.get(n)
            if r is None:
                print(f"  n={n:<5d} no candidate")
            else:
                print(f"  n={n:<5d} best {r['family']:12s} L = {z2dec_z(r['L']):.6f} "
                      f"vs delivered {deliv[n][0]:.6f}  margin {r['margin']:+.6f}")
    return {"candidates": len(cands), "rows": len(best), "beats": beats,
            "summary": summary, "best": [best[n] for n in sorted(best)]}


def z2dec_z(d: Decimal) -> Decimal:
    """Identity, so the f-string above reads a Decimal where the record stores one."""
    return d


# --------------------------------------------------- C1 on a strict beat
def certificate(cells, words, n: int, L, cid: str) -> dict:
    """A `verify_certificates` document for the pose, in its own field `Quad(d)`."""
    out = {"id": cid, "field": f"Quad({type(L).d})", "N": n,
           "L": [str(L.a), str(L.b)], "origin": ["0", "0"],
           "family": "scale-motifs", "expected": {"ok": True, "violations": 0},
           "cells": []}
    for (x, y), (c, si) in zip(cells, words):
        out["cells"].append({
            "x": [str(x.a), str(x.b)], "y": [str(y.a), str(y.b)],
            # the frame is [R0, R1, R2, R3] with u = (R0, R2), v = (R1, R3)
            "r": [[str(c.a), str(c.b)],
                  [str((-si).a), str((-si).b)],
                  [str(si.a), str(si.b)],
                  [str(c.a), str(c.b)]]})
    return out


def verify_beat(rec) -> dict:
    """C1's exact pass: rebuild, count, re-anchor, gate, certificate."""
    c = rec["_cand"]
    fam = c["family"]
    if fam == "A-product":
        cells, words = product_cells(BASES[c["m"]], c["k"], drop=c["drop"])
    elif fam == "B-inflate":
        cells, words, _s = inflate_cells(BASES[c["m"]], c["steps"])
    elif fam == "D-composite":
        lib = {mo.name: mo for mo in motif_library(BASES)}
        cells, words = composite_pose(BASES[c["m"]], lib[c["motif"]], c["drop"])
    else:
        cells, words = c["cells"], c["words"]
    if len(cells) != rec["n"]:
        return {"ok": False, "why": f"count {len(cells)} != declared {rec['n']}"}
    ex = [QS.frame_extent(w[0], w[1]) for w in words]
    lo_x = min(cells[i][0] - ex[i] for i in range(len(cells)))
    lo_y = min(cells[i][1] - ex[i] for i in range(len(cells)))
    anchored = [(x - lo_x, y - lo_y) for x, y in cells]
    g = gate(anchored, words)
    if not g["ok"]:
        return {"ok": False, "why": f"gate refused: {g['violations']} overlaps",
                "gate": g}
    cert = certificate(anchored, words, len(cells), g["L"],
                       cid=f"scale-{fam}-n{rec['n']}")
    try:
        summ = VC.verify_certificate(cert)
    except VC.Failure as e:                                  # noqa: BLE001
        return {"ok": False, "why": f"certificate refused: {e}", "gate": g}
    return {"ok": bool(summ["ok"]), "gate_clearance": g["clearance"],
            "gate_contacts": g["contacts"], "certificate": summ}


def promote(beats) -> dict:
    """C1 on every strict beat.  Nothing is written unless C1 passes.

    Promotion is C1 (exact certificate at clearance >= 0), C2 (a strictly smaller true
    side), C3 (the guards) and C4 (the rendered row still legal); this function performs
    C1 and refuses to touch the CSV, because a row that fails C1 is not promotable at all
    and a row that passes it needs the scorer-contract update to be made deliberately.
    """
    out = []
    for rec in beats:
        v = verify_beat(rec)
        out.append({**{k: v_ for k, v_ in rec.items() if k != "_cand"},
                    "verdict": "C1 pass" if v["ok"] else "C1 fail",
                    "detail": v.get("why") or f"clearance {v['gate_clearance']}, "
                                              f"contacts {v['gate_contacts']}"})
    return {"beats": out, "promoted": 0,
            "note": "no CSV write: promotion needs C2-C4 and the scorer contract"}


# ------------------------------------------------------------------- selftest
def selftest() -> int:
    import sqscore as SQ
    SQ.guard(quiet=True)
    checks = 0

    deliv = load_delivered()
    assert len(deliv) == 1000
    d5 = deliv[5][0]
    exact5 = Decimal(2) + Decimal(2).sqrt() / 2
    assert abs(d5 - exact5) < Decimal("1e-8"), (d5, exact5)
    print(f"  1. the CSV read exactly: {len(deliv)} rows, side(5) = {d5:.12f} against "
          f"the exact 2 + sqrt2/2 = {exact5:.12f}; the gap {abs(d5 - exact5):.1e} is the "
          f"12-dp angle's rendering noise, below the 1e-8 margin")
    checks += 1

    st = [(Q2(i) + Q2(F(1, 2)), Q2(j) + Q2(F(1, 2))) for j in range(3) for i in range(3)]
    g = gate(st, [AXIS] * 9)
    assert g["ok"] and g["L"] == Q2(3) and g["contacts"] == 20
    print("  2. the exact gate: a 3x3 grid has L = 3 exactly and 20 exact contacts")
    checks += 1

    b = base_of(20, deliv)
    assert b is not None and b.n == 20, b
    v = b.gate()
    assert v["ok"], v
    print(f"  3. row 20 rebuilds in Q(sqrt 2) from the CSV's own decimals "
          f"({b.kind} words): L = {z2dec(b.L, 12):.12f}, gate ok, "
          f"{v['contacts']} contacts")
    checks += 1

    cells, words = product_cells(b, 2)
    g4 = gate(cells, words)
    assert len(cells) == 80 and g4["ok"] and g4["L"] == Q2(2) * b.L, (len(cells), g4["L"])
    cells3, words3 = product_cells(b, 2, drop=3)
    g3 = gate(cells3, words3)
    assert len(cells3) == 77 and g3["ok"] and g3["L"] == g4["L"], (len(cells3), g3["L"])
    print(f"  4. the product law: 4 x 20 = 80 at L = {z2dec(g4['L'], 9):.9f} (exactly 2L), "
          f"and 4 x 20 - 3 = 77 at the same side; both gate")
    checks += 1

    cells, words, sides = inflate_cells(b, 3)
    for j, Ls in enumerate(sides, start=1):
        assert Ls == b.L + Q2(j), (j, Ls)
    gi = gate(cells, words)
    assert gi["ok"], gi["violations"]
    expect = 20 + sum(2 * QS.floor_q2(b.L + Q2(j - 1)) + 1 for j in range(1, 4))
    assert len(cells) == expect, (len(cells), expect)
    print(f"  5. the border law: 3 inflations of row 20 give {len(cells)} cells at "
          f"L = {z2dec(gi['L'], 9):.9f} (exactly L+3), gate ok, {gi['contacts']} contacts")
    checks += 1

    bad = list(b.cells) + [b.cells[0]]
    gb = gate(bad, list(b.words) + [b.words[0]])
    assert not gb["ok"] and gb["clearance"] is not None and gb["clearance"] < 0
    print("  6. a duplicated cell is refused with a negative clearance (the fill "
          "control is not vacuous)")
    checks += 1

    for name in ("45", "8-15-17"):
        cells, words = rot_block_cells(6, WORDS[name], 0)
        gr = gate(cells, words)
        assert gr["ok"], (name, gr["violations"])
        S = gr["L"]
        spare = S * S - Q2(36)
        print(f"  7. {name:8s} b=6: {len(cells)} cells at L = {z2dec(S, 9):.9f}; the "
              f"block alone is 6x6, and S^2 - 36 = {z2dec(spare, 6):.3f} is the area the "
              f"corner fill can ever win")
    checks += 1

    d120 = deliv[120][0]
    assert abs(d120 - Decimal(11)) < Decimal("1e-8"), d120
    c_eq = compare(Q2(11), d120)
    c_lt = compare(Q2(11) - Q2(F(1, 10 ** 6)), d120)
    assert not c_eq["beat"] and abs(c_eq["margin"]) < MARGIN_D
    assert c_lt["beat"], c_lt["margin"]
    print(f"  8. the comparison is against the delivered side (row 120 is a tie at "
          f"{d120:.12f}): 11 is not a beat (margin {c_eq['margin']:+.1e}), 11 - 1e-6 is")
    checks += 1

    b50 = base_of(50, deliv)
    assert b50 is not None and b50.field == "Q", b50
    g50 = b50.gate()
    assert g50["ok"], g50
    c34 = {w.name for w in [EW.classify(a) for _x, _y, a in deliv[50][1]]}
    print(f"  9. a rational-word row joins the census: row 50 ({b50.field}, "
          f"{len(c34)} word classes) rebuilds at L = {z2dec(b50.L, 9):.9f}, gate ok, "
          f"{g50['contacts']} contacts")
    checks += 1

    cls5 = EW.quad(5)
    c5, s5 = EW.root_in(cls5, F(4, 5)), EW.root_in(cls5, F(1, 5))   # 2/sqrt 5, 1/sqrt 5
    assert c5 * c5 == cls5(F(4, 5)) and s5 * s5 == cls5(F(1, 5))
    st5, ws5 = [], []
    for j in (-1, 0, 1):
        for i in (-1, 0, 1):
            u, v = cls5(i), cls5(j)
            st5.append((c5 * u - s5 * v, c5 * v + s5 * u))
            ws5.append((c5, s5))
    g5 = gate(st5, ws5, cls5)
    assert g5["ok"], g5
    assert g5["L"] == cls5(F(9, 5)) * cls5(0, 1), (g5["L"], "3 (|c| + |s|) = 9/sqrt 5")
    print(f"  10. a non-Q(sqrt 2) field end to end: a 3x3 grid at atan(1/2) in Q(sqrt 5) "
          f"gates at L = {z2dec(g5['L'], 9):.9f} = 9/sqrt 5 exactly")
    checks += 1

    fake = [(Decimal(0), Decimal(0), Decimal("0.463647609001")),
            (Decimal(0), Decimal(0), Decimal("0.523598775598"))]
    ws_f, why = row_words(fake)
    assert ws_f is None and why == "two different quadratic fields", (ws_f, why)
    print("  11. a row mixing Q(sqrt 5) and Q(sqrt 3) needs a degree-4 tower and is "
          "refused by name, not approximated")
    checks += 1

    bases = {n: b for n in range(1, N_HI + 1) if (b := base_of(n, deliv)) is not None}
    fields = {}
    for b in bases.values():
        fields[b.field] = fields.get(b.field, 0) + 1
    print(f"  12. the census: {len(bases)} bases recovered of {len(deliv)} (before the "
          f"new-sentence gate), by field {fields}")
    checks += 1

    lib = motif_library(bases)
    b20 = bases[20]
    mo = next(m for m in lib if m.name == "45/b3")
    nD = composite_count(b20, mo)
    cells, words = composite_pose(b20, mo)
    gD = gate(cells, words)
    nx, ny = rect_counts(b20.L, mo.S)
    assert len(cells) == nD and gD["ok"] and gD["L"] == b20.L + mo.S, \
        (len(cells), nD, gD["L"], b20.L + mo.S)
    print(f"  13. the composite law: row 20 + the 45-degree 3x3 motif gives {nD} cells at "
          f"L = {z2dec(gD['L'], 9):.9f}, exactly L + S; the strips add 2 x {nx} x {ny} = "
          f"{2 * nx * ny}, and the built pose gates with {gD['contacts']} contacts")
    checks += 1

    probe = (20, 50, min(bases, key=lambda k: abs(k - 120)))
    best = None
    for n0 in probe:
        bb = bases[n0]
        for m in lib:
            for r in range(3):
                n = composite_count(bb, m) - r
                if N_LO <= n <= N_HI:
                    gap = deliv[n][0] - z2dec(bb.L + m.S, 45)
                    if best is None or gap > best[0]:
                        best = (gap, n, m.name, r)
    print(f"  14. the composite frontier is nowhere near the table: the best of rows "
          f"{probe} against the delivered sides is n = {best[1]} at {best[0]:+.3f} "
          f"(motif {best[2]}, drop {best[3]})")
    checks += 1

    checked, offenders, skipped = EF.audit_module(
        sys.modules[__name__], exempt=EF.AUDIT_EXEMPT + ("selftest",))
    assert offenders == [], offenders
    print(f"  15. bytecode audit: {checked} decision functions, 0 naming float "
          f"(exempt {skipped})")
    checks += 1
    print(f"selftest OK ({checks} controls)")
    return 0


# ----------------------------------------------------------------------- main
def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    import sqscore as SQ
    SQ.guard(quiet=True)
    deliv = load_delivered()
    print(f"rows read: {len(deliv)}")
    bases = {}
    for n in range(1, N_HI + 1):
        b = base_of(n, deliv)
        if b is not None:
            bases[n] = b
            BASES[n] = b
    # the extension's sentences are *inferred* from the angle, so they are gated before
    # they are trusted; run 151's own 519 rows are the table's declared words and are not
    # re-gated here (C1 gates every candidate that would be promoted, from any base).
    new_bases = [n for n in sorted(bases) if not old_rule_row(deliv[n][1])]
    dropped = []
    for n in new_bases:
        g = bases[n].gate()
        if not g["ok"]:
            dropped.append({"n": n, "violations": g["violations"],
                            "clearance": str(z2dec(g["clearance"], 12))})
    for rec in dropped:
        bases.pop(rec["n"], None)
        BASES.pop(rec["n"], None)
    print(f"new sentences: {len(new_bases)} recovered beyond run 151's rule, "
          f"{len(new_bases) - len(dropped)} pass the exact gate, {len(dropped)} dropped "
          f"{[(r['n'], r['violations']) for r in dropped]} (clearance "
          f"{[r['clearance'] for r in dropped]})")
    kinds, fields = {}, {}
    for b in bases.values():
        kinds[b.kind] = kinds.get(b.kind, 0) + 1
        fields[b.field] = fields.get(b.field, 0) + 1
    refused = {}
    for n in range(1, N_HI + 1):
        if n in bases:
            continue
        _ws, why = row_words(deliv[n][1])
        if _ws is None:                    # else it was recovered but failed the gate
            refused[why] = refused.get(why, 0) + 1
    for rec in dropped:
        refused["the inferred sentence overlaps at the exact gate"] = \
            refused.get("the inferred sentence overlaps at the exact gate", 0) + 1
    print(f"exact bases: {len(bases)} of {len(deliv)}  words {kinds}  fields {fields}")
    print(f"refused: {sum(refused.values())}  {refused}")
    res = audit(bases, deliv, verbose=True)
    out = {"instrument": "scale_motifs.py", "schema": "scale-motifs/1",
           "window": [N_LO, N_HI], "margin": str(MARGIN_D),
           "bases": {k: v for k, v in kinds.items()},
           "base_fields": {k: v for k, v in fields.items()},
           "refused": {k: v for k, v in refused.items()},
           "base_gate": {"new_sentences": len(new_bases), "dropped": dropped},
           "candidates": res["candidates"], "rows_reached": res["rows"],
           "summary": {k: {kk: (str(vv) if isinstance(vv, Decimal) else vv)
                           for kk, vv in v.items()}
                       for k, v in res["summary"].items()},
           "beats": [{k: str(v) if isinstance(v, Decimal) else v
                      for k, v in r.items() if k != "_cand"} for r in res["beats"]],
           "rows": [{k: str(v) if isinstance(v, Decimal) else v for k, v in r.items()}
                    for r in res["best"]]}
    if "--promote" in sys.argv:
        out["promotion"] = promote(res["beats"])
        for p in out["promotion"]["beats"]:
            print(f"  n={p['n']}: {p['verdict']} ({p['detail']})")
        print(f"  promoted: {out['promotion']['promoted']} "
              f"({out['promotion']['note']})")
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w") as f:
        json.dump(out, f, indent=1)
    print(f"ledger: {os.path.relpath(LEDGER, ROOT)}")
    if not res["beats"]:
        print("NO STRICT BEAT: every candidate in every family is at or above the "
              "delivered side of its row. Nothing to promote, no score claimed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
