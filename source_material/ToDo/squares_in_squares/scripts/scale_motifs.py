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

NOTHING IS APPROXIMATE.  The delivered sides are 45-digit Decimals computed from the
CSV's own decimal text; the trigonometric functions are `true_geom`'s Decimal series, so
no float touches them.  Every candidate side is an element of Q(sqrt 2) (`qsqrt2.Q2`)
read off an exact pose, and the comparison is `L + 1e-8 <= delivered(n)` with `1e-8` an
exact Fraction, i.e. a candidate must beat the delivered row by the project's whole
margin.  A strict beat is then *verified*: the exact SAT gate (`qsqrt2.gate`) plus a
certificate in `verify_certificates`' schema, at clearance >= 0.

WHAT IT FOUND (run 151).  Zero strict beats in all three families on every row of
101..1000.  (A) and (B) are the table's own constructions, so every row they reach is
already at or below their side; (C)'s area ceiling is the area bound itself and the
staircase waste in the corner fill leaves every realised pose above sqrt(n) by more than
the delivered rows are.

USAGE
    python3 scripts/scale_motifs.py --selftest   # 9 controls
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
import qsqrt2 as QS              # noqa: E402  (Q(sqrt 2): Q2, gate, side, words)
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
HALF_DEG = Decimal("1e-9")
PI4 = Decimal("0.78539816339744830961566084581987572104929234984378")
PI = Decimal("3.14159265358979323846264338327950288419716939937511")

#: the rational words of the parametric family, all exact
WORDS = {"45": word_45(),
         "8-15-17": (Q2(F(8, 17)), Q2(F(15, 17))),
         "3-4-5": (Q2(F(3, 5)), Q2(F(4, 5)))}

#: bases, so a beat can be rebuilt when it is verified
BASES: dict = {}


# ---------------------------------------------------------------- decimal shadow
def z2dec(z: Q2, places: int = 45) -> Decimal:
    """`a + b sqrt 2` as a Decimal at `places`, for display and for the CSV comparison.

    This is the only place a side leaves `Q2`.  The true value differs from this shadow
    by less than 10^-places, and every comparison is made with an 1e-8 margin, so no
    decision can depend on the shadow's last digits.
    """
    with localcontext() as ctx:
        ctx.prec = places
        return (Decimal(z.a.numerator) / Decimal(z.a.denominator)
                + Decimal(z.b.numerator) / Decimal(z.b.denominator)
                * Decimal(2).sqrt())


def q2_of_dec(d: Decimal) -> Q2:
    """An exact `Q2` from a decimal string's value (a rational; no float anywhere)."""
    return Q2(F(d))


def grid(n: int) -> int:
    k = math.isqrt(n)
    return k if k * k == n else k + 1


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
    """A delivered row rebuilt exactly in `Q(sqrt 2)`: the pose a family grows from."""

    __slots__ = ("n", "cells", "words", "L", "kind", "gated")

    def __init__(self, n, cells, words, L, kind):
        self.n, self.cells, self.words, self.L, self.kind = n, cells, words, L, kind
        self.gated = None

    def gate(self):
        if self.gated is None:
            self.gated = gate(self.cells, self.words)
        return self.gated


def base_of(n: int, deliv) -> Base | None:
    """Rebuild row `n` exactly, if every angle is the 0- or the 45-degree word.

    The centres are the CSV's own decimal text, hence exact rationals, and the words are
    exact, so the pose is a `Q2` sentence.  A row with any other angle is refused: its
    geometry is not in this field, and replaying its *decimals* would make the audit
    approximate in exactly the place it must not be.
    """
    _side, cells = deliv[n]
    st, ws = [], []
    saw45 = saw0 = False
    for x, y, a in cells:
        if abs(a) <= HALF_DEG or abs(a - PI) <= HALF_DEG:
            w, saw0 = AXIS, True
        elif abs(a - PI4) <= HALF_DEG:
            w, saw45 = word_45(), True
        else:
            return None
        st.append((q2_of_dec(x), q2_of_dec(y)))
        ws.append(w)
    if len(st) != n:
        return None
    ex = [QS.frame_extent(w[0], w[1]) for w in ws]
    lo_x = min(st[i][0] - ex[i] for i in range(n))
    lo_y = min(st[i][1] - ex[i] for i in range(n))
    st = [(x - lo_x, y - lo_y) for x, y in st]
    kind = "45" if saw45 and not saw0 else ("axis" if saw0 and not saw45 else "mixed")
    return Base(n, st, ws, side(st, ws), kind)


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
            dx, dy = Q2(i) * base.L, Q2(j) * base.L
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
            L = Q2(k) * base.L
            for r in range(0, m):
                n = hi_n - r
                if N_LO <= n <= N_HI:
                    out.append({"family": "A-product", "n": n, "L": L, "k": k,
                                "m": m, "drop": r})
    return out


# ------------------------------------------------------------------- family (B)
def border_count(L: Q2) -> int:
    """`2 floor(L+1) - 1`, the cells a unit border adds.  Exact."""
    return 2 * (QS.floor_q2(L) + 1) - 1


def inflate_cells(base: Base, steps: int):
    """The pose after `steps` border inflations and the side after each one."""
    cells, words, L = list(base.cells), list(base.words), base.L
    sides = []
    for _ in range(steps):
        row = QS.floor_q2(L + Q2(1))
        moved = [(x + Q2(1), y + Q2(1)) for x, y in cells]
        mw = list(words)
        for j in range(row):                      # vertical strip: x in [0,1]
            moved.append((Q2(F(1, 2)), Q2(j) + Q2(F(1, 2))))
            mw.append(AXIS)
        for i in range(1, row):                   # horizontal strip: y in [0,1]
            moved.append((Q2(i) + Q2(F(1, 2)), Q2(F(1, 2))))
            mw.append(AXIS)
        cells, words, L = moved, mw, L + Q2(1)
        sides.append(L)
    return cells, words, sides


def family_inflate(bases, steps_max: int = 12):
    """The cascade from every exact base, iterated while `n` stays in the window."""
    out = []
    for m, base in bases.items():
        n, L = m, base.L
        for j in range(1, steps_max + 1):
            add = border_count(L)
            n2, L2 = n + add, L + Q2(1)
            if n2 > N_HI:
                break
            if n2 >= N_LO:
                out.append({"family": "B-inflate", "n": n2, "L": L2, "steps": j,
                            "m": m, "added": add})
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


# ------------------------------------------------------------------- the audit
def compare(L: Q2, deliv_side: Decimal) -> dict:
    """`L` against a delivered side: `beat` iff `L + 1e-8 <= delivered`."""
    Ld = z2dec(L, 45)
    return {"L_dec": Ld, "margin": deliv_side - Ld,
            "beat": Ld + MARGIN_D <= deliv_side}


def _rec(c, cmp):
    rec = {"family": c["family"], "n": c["n"], "L": z2dec(c["L"], 18),
           "margin": cmp["margin"], "beat": cmp["beat"]}
    for key in ("k", "m", "drop", "steps", "added", "word", "b", "extra"):
        if key in c:
            rec[key] = c[key]
    return rec


def audit(bases, deliv, verbose: bool = True):
    """Run the three families, compare exactly, report every strict beat."""
    cands = (family_product(bases) + family_inflate(bases) + family_rot_block())
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
def certificate(cells, words, n: int, L: Q2, cid: str) -> dict:
    """A `verify_certificates` document for a `Q2` pose (canonical fraction strings)."""
    out = {"id": cid, "field": "Quad(2)", "N": n,
           "L": [str(L.a), str(L.b)], "origin": ["0", "0"],
           "family": "scale-motifs", "expected": {"ok": True, "violations": 0},
           "cells": []}
    for (x, y), (c, si) in zip(cells, words):
        out["cells"].append({
            "x": [str(x.a), str(x.b)], "y": [str(y.a), str(y.b)],
            # the frame is [R0, R1, R2, R3] with u = (R0, R2), v = (R1, R3)
            "r": [[str(c.a), str(c.b)],
                  [str((Q2(0) - si).a), str((Q2(0) - si).b)],
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

    checked, offenders, skipped = EF.audit_module(
        sys.modules[__name__], exempt=EF.AUDIT_EXEMPT + ("selftest",))
    assert offenders == [], offenders
    print(f"  9. bytecode audit: {checked} decision functions, 0 naming float "
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
    kinds = {}
    for b in bases.values():
        kinds[b.kind] = kinds.get(b.kind, 0) + 1
    print(f"exact bases (0/45-degree rows): {len(bases)} of {len(deliv)}  {kinds}")
    res = audit(bases, deliv, verbose=True)
    out = {"instrument": "scale_motifs.py", "schema": "scale-motifs/1",
           "window": [N_LO, N_HI], "margin": str(MARGIN_D),
           "bases": {k: v for k, v in kinds.items()},
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
