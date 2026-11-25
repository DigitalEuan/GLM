#!/usr/bin/env python3
r"""construct92.py — run 135: constructive poses at band 5, and the angle question.

Runs 132-134 closed every *tightening* route on the delivered table: `g* = 1` on
551/551 rows, squeeze-and-legalise negative on 20/20, and pure band slides worth
at most `5.5e-13` anywhere.  What they did not test is the other half of the
brief: build a pose **from scratch** at a row's own count, with the two axes not
tied into the deadlocked `span_x = span_y = L` shape that 507 of 551 rows have.

Family I — the four-corner seam at any exact angle.

    Four axis-aligned k x k blocks in the corners of the box, and a strip of m
    unit squares at angle theta whose centres are one unit apart along the
    strip's own edge direction.  The strip's cells are mutually tangent; the
    corner blocks are tangent to the strip's ends and long faces.

Run 84 (doc 47) proved for `theta = 45 deg` that this family's side is
`2k + m*sqrt2/2` and its gain over the grid is `1 - m*sqrt2/2`, so only `m = 1`
pays.  The open question this run was asked is whether a *different* exact angle
does better: the `Q(sqrt 7)` ring direction (`0.424031` rad — the angle rows 18
and 55 of the delivered table are actually built at), the `3-4-5` spinor
(`36.87 deg`) or the `5-12-13` (`22.62 deg`).

The family's side is the same in every field, and each term is monotone:

    L(k, m) = 2k + 1/(cos + sin) + (m - 1) * max(cos, sin)          (*)

    with   1/(cos + sin) >= sqrt2/2   and   max(cos, sin) >= sqrt2/2,

both equalities holding **iff** `cos = sin`, i.e. iff `theta = 45 deg`.  So the
45-degree seam is the unique minimiser of the side at every `(k, m)`: a
multi-angle or rational-spinor seam cannot undercut it, and the asymmetric words
are strictly worse.  (*) is checked, not asserted, for every word: the instrument
builds the pose at that side and gates it exactly (0 violations, 0 penetration),
then rebuilds it `1/1000` narrower and requires the exact gate to refuse it.

Family II — fresh patterns at band 5.  For `n = 20..23` the delivered row is the
plain 5x5 grid, so a beat means 20..23 cells below `L = 5`, i.e. a density above
`0.8` — better than the plain grid's own density at that count.  The run builds
each count from scratch (the grid with `j = 25 - n` cells removed in four notch
shapes), runs the repo's own squeeze and project at `L = 5 - 0.02` and measures
the projected pose with `p_screen.measure` at 40 digits.  No delivered pose is
an input.

Family III — the one-binding-axis rows.  Run 134's 44 rows (`span_x != span_y`)
are the rows where a single-axis reduction is geometrically permitted.  A
from-scratch construction at `n >= 303` is outside this run's budget; recorded
instead is a *bounded* exact anchor-closure probe at those rows' own counts with
the node cap stated, so the reader sees how far the exact contact grammar gets
rather than being told the question is closed.

Every verdict is an exact gate: containment and non-overlap on SAT axes in
`Q(sqrt 2)` or `Q(sqrt 7)` (`Fraction` arithmetic, exact comparisons).  Floats
appear in two labelled places only — the repo's squeeze stage and the record's
own display — and both are re-judged exactly before anything is reported.

    python3 scripts/construct92.py --selftest
    python3 scripts/construct92.py --families       # Family I, every word
    python3 scripts/construct92.py --band5          # Family II
    python3 scripts/construct92.py --axis           # Family III
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from decimal import Decimal, getcontext
from fractions import Fraction

getcontext().prec = 45

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import exact_field as EF                 # noqa: E402  (exact Q(sqrt d))
import mixed_field as MF                 # noqa: E402  (run 84's 45-degree seam)
import p_screen as PS                    # noqa: E402  (40-digit measurement)
import structure as ST                   # noqa: E402  (squeeze, discovery only)

OUT = os.path.join(ROOT, "workspace/push/construct92.json")
THOU = Fraction(1, 1000)


class Q2(EF.Quad):
    d = 2


class Q7(EF.Quad):
    d = 7


# ---------------------------------------------------------------- exact words
class Word:
    """A unit-square orientation: edge vectors (c, s) and (-s, c), exact."""

    __slots__ = ("name", "c", "s", "field")

    def __init__(self, name, c, s):
        self.name, self.c, self.s = name, c, s
        self.field = type(c)

    def axes(self):
        return ((self.c, self.s), (-self.s, self.c))

    def mx(self):
        return self.c if self.c >= self.s else self.s

    def __repr__(self):
        return f"Word({self.name})"


def words():
    h = Fraction(1, 2)
    return [
        Word("45 deg", Q2(0, h), Q2(0, h)),
        Word("ring 24.30 deg (sqrt7)", Q7(Fraction(1, 4), Fraction(1, 4)),
             Q7(Fraction(-1, 4), Fraction(1, 4))),
        Word("3-4-5 36.87 deg", Q2(Fraction(4, 5)), Q2(Fraction(3, 5))),
        Word("5-12-13 22.62 deg", Q2(Fraction(12, 13)), Q2(Fraction(5, 13))),
    ]


def half_ext(w, qx, qy):
    """Exact half-extent of a word square along the axis (qx, qy)."""
    c, s = w.c, w.s
    return (abs(c * qx + s * qy) + abs(-s * qx + c * qy)) / 2


def pretty(q) -> str:
    """`a + b*sqrt(d)` in readable exact form."""
    a, b = q.a, q.b
    if b == 0:
        return str(a)
    if a == 0:
        return f"{b}*sqrt{q.d}"
    return f"{a}{'+' if b > 0 else '-'}{abs(b)}*sqrt{q.d}"


def dec(q) -> str:
    """Exact field element as a 40-digit Decimal (display/comparison only)."""
    d = Decimal(q.a.numerator) / Decimal(q.a.denominator)
    if q.b:
        d += Decimal(q.b.numerator) / Decimal(q.b.denominator) * Decimal(q.d).sqrt()
    return str(+d)


def fnum(q) -> float:
    """Discovery-only float of an exact element (used in labels only)."""
    return float(q.a) + float(q.b) * math.sqrt(q.d)


# ------------------------------------------------------------------- the gate
def gate(cells, L):
    """Exact containment + non-overlap.  `cells` = [(x, y, Word)] in one field.

    A pair is separated when some SAT axis has |projection| >= the sum of the
    half-extents; the deepest violation is the largest overlap over the pair's
    axes.  Returns (violations, worst_penetration, witness).
    """
    viol, worst, why = 0, None, None
    for i, (x, y, w) in enumerate(cells):
        F = w.field
        hx, hy = half_ext(w, F(1), F(0)), half_ext(w, F(0), F(1))
        for over, tag in ((0 - (x - hx), "x-lo"), (x + hx - L, "x-hi"),
                          (0 - (y - hy), "y-lo"), (y + hy - L, "y-hi")):
            if over > 0:
                viol += 1
                if worst is None or over > worst:
                    worst, why = over, f"wall {tag} cell {i}"
    for i in range(len(cells)):
        xi, yi, wi = cells[i]
        for j in range(i + 1, len(cells)):
            xj, yj, wj = cells[j]
            dx, dy = xj - xi, yj - yi
            best = None
            for q in wi.axes() + wj.axes():
                v = (abs(dx * q[0] + dy * q[1])
                     - half_ext(wi, q[0], q[1]) - half_ext(wj, q[0], q[1]))
                if best is None or v > best:
                    best = v
            if best < 0:
                viol += 1
                if worst is None or -best > worst:
                    worst, why = -best, f"pair {i}-{j}"
    return viol, worst, why


# ---------------------------------------------------------- the seam family
def seam_cost(word, m: int):
    """`1/(c+s) + (m-1)*max(c,s)`, exactly, in the word's field."""
    F = word.field
    return F(1) / (word.c + word.s) + F(m - 1) * word.mx()


def seam_side(word, k: int, m: int):
    return word.field(2 * k) + seam_cost(word, m)


def strip_pose(word, k: int, m: int, L):
    """Four axis-aligned k-blocks + an m-cell strip at `word`, exactly.

    Strip centres are one unit apart along the word's own edge direction
    `(s, -c)`: consecutive cells are edge-to-edge contacts.  This is
    `mixed_field.strip_sentence` written for any exact word (selftest 2 pins the
    45-degree case to it cell for cell).
    """
    F = word.field
    up = Word("axis", F(1), F(0))
    cells = []
    for ox in (0, L - k):
        for oy in (0, L - k):
            for i in range(k):
                for j in range(k):
                    cells.append((ox + F(i) + F(Fraction(1, 2)),
                                  oy + F(j) + F(Fraction(1, 2)), up))
    mid = L / 2
    for i in range(m):
        t = F(Fraction(2 * i - (m - 1), 2))
        cells.append((mid + t * word.s, mid - t * word.c, word))
    return cells


def family_certify(word, k: int, m: int):
    """Gate the closed-form side exactly, and require refusal 1/1000 below it."""
    L = seam_side(word, k, m)
    cells = strip_pose(word, k, m, L)
    v, _p, why = gate(cells, L)
    Lb = L - word.field(THOU)
    vb, pb, whyb = gate(cells, Lb)
    n = 4 * k * k + m
    grid = int(math.ceil(math.sqrt(n)))
    rec = {"word": word.name, "k": k, "m": m, "n": n, "grid": grid,
           "side_exact": pretty(L), "side": dec(L),
           "gate": v, "gate_witness": why,
           "refused_below": bool(vb > 0), "depth_below": (pretty(pb) if vb else "0"),
           "refusal_witness": whyb,
           "gain_vs_grid": str(Decimal(grid) - Decimal(dec(L))),
           "below_5": bool(Decimal(dec(L)) < 5)}
    if v == 0 and not vb:
        rec["status"] = "not-minimal: still legal 1/1000 below the closed form"
    elif v == 0:
        rec["status"] = "certified"
    else:
        rec["status"] = "closed form illegal"
    return rec


def lemma_rows():
    """The two exact inequalities behind the closed form, per word."""
    out = []
    for w in words():
        F = w.field
        inv = F(1) / (w.c + w.s)
        mx = w.mx()
        out.append({"word": w.name, "c": pretty(w.c), "s": pretty(w.s),
                    "c_plus_s": pretty(w.c + w.s),
                    "inv_c_plus_s": dec(inv), "max_cs": dec(mx),
                    "inv_ge_r2h": bool(inv * inv >= F(Fraction(1, 2))),
                    "max_ge_r2h": bool(mx * mx >= F(Fraction(1, 2))),
                    "equality_both": bool(inv * inv == F(Fraction(1, 2))
                                          and mx * mx == F(Fraction(1, 2))),
                    "is_45": bool(w.c == w.s),
                    "first_cell": dec(inv), "per_extra_cell": dec(mx)})
    return out


def family_table(kmax=3, mmax=4):
    rows = [family_certify(w, k, m)
            for w in words() for k in range(1, kmax + 1) for m in range(1, mmax + 1)]
    return rows


def band5_best(rows):
    best = {}
    for r in rows:
        if r.get("below_5") and r["status"] == "certified":
            cur = best.get(r["word"])
            if cur is None or r["n"] > cur["n"] or (
                    r["n"] == cur["n"] and Decimal(r["side"]) < Decimal(cur["side"])):
                best[r["word"]] = r
    return best


# ------------------------------------------------- Family II: fresh patterns
def pattern(n: int, kind: int):
    """A fresh `n`-cell pose: the 5x5 grid with `25 - n` cells removed by `kind`."""
    import numpy as np
    cells = [(i, j) for j in range(5) for i in range(5)]
    j = 25 - n
    orders = {
        0: [(i, 4) for i in range(5)] + [(i, 3) for i in range(5)],
        1: [(4, 4), (3, 4), (4, 3), (2, 4), (3, 3), (4, 2), (1, 4), (2, 3), (3, 2), (4, 1)],
        2: [(2, 2), (1, 2), (2, 1), (3, 2), (2, 3), (1, 1), (3, 3), (0, 2), (2, 0)],
        3: [(0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (0, 2), (2, 1), (1, 2), (2, 2)],
    }
    rem = set(orders[kind][:j])
    keep = [c for c in cells if c not in rem]
    if len(keep) != n:
        raise ValueError(f"pattern {kind} gives {len(keep)} cells, wanted {n}")
    X = np.array([i + 0.5 for i, _ in keep], dtype=float)
    Y = np.array([j + 0.5 for _, j in keep], dtype=float)
    return X, Y, np.zeros(n)


def squeeze_fresh(X, Y, T, L0, seconds, seed, n):
    """Squeeze a *fresh* pose, then legalise it exactly (`squeeze_from`+`convert`).

    `p_screen.squeeze_from` is the same squeeze-and-project loop `structure.attempt`
    runs, but from an explicit pose instead of the delivered one; `convert` is the
    exact stage (minimum legal scale, void swaps, band ladder, exact step) and it
    asserts its own output has zero violations at 40 digits.
    """
    t0 = time.monotonic()
    poses, stats = PS.squeeze_from(X, Y, T, L0, seconds, seed, n)
    m = PS.measure(poses)                 # exact: 40-digit depth, side, violations
    conv = PS.convert(m["state"], m["dirs"], Decimal(str(L0)), m["side"],
                      time.monotonic() + max(8.0, seconds))
    out = {"seconds": round(time.monotonic() - t0, 1),
           "side_projected": str(m["side"]), "p_projected": str(m["p"]),
           "violations_projected": m["violations"],
           "convert": {k: v for k, v in conv.items() if k != "state"},
           "stats": {k: v for k, v in stats.items()
                     if k in ("sweeps_completed", "sweeps_aborted", "patches_solved")}}
    if conv.get("dL") is not None:
        out["dL"] = conv["dL"]
        out["certified"] = conv.get("certified")
    out["hit"] = bool(out.get("dL") is not None and Decimal(out["dL"]) > 0
                      and conv.get("certified")
                      and conv["certified"].get("violations") == 0)
    return out


def band5_run(seconds=8.0, targets=(20, 21, 22, 23), kinds=(0, 1, 2, 3)):
    rows = []
    for n in targets:
        for kind in kinds:
            X, Y, T = pattern(n, kind)
            r = squeeze_fresh(X, Y, T, 5.0, seconds, seed=kind, n=n)
            r.update({"n": n, "kind": kind})
            rows.append(r)
            dl = r.get("dL")
            cert = r.get("certified") or {}
            print(f"  n={n} kind={kind}: projected L={float(r['side_projected']):.6f} "
                  f"p={Decimal(r['p_projected']):+.3e} viol={r['violations_projected']} | "
                  f"converted L={cert.get('side', 'n/a')} "
                  f"dL={'n/a' if dl is None else format(Decimal(dl), '+.3e')} "
                  f"({r['seconds']}s)", flush=True)
    pos = [r for r in rows if r["hit"]]
    print(f"[band5] {len(rows)} fresh patterns, {len(pos)} legal and below 5.0")
    return rows


def band5_controls():
    """Controls: recovery of a known gap, and no gain at a proved optimum."""
    import numpy as np
    out = {}
    # A. a 4x4 grid inflated to side 4.2 must come back to 4.0 (s(16) = 4)
    X = np.array([(i + 0.5) * 1.05 for j in range(4) for i in range(4)], dtype=float)
    Y = np.array([(j + 0.5) * 1.05 for j in range(4) for i in range(4)], dtype=float)
    out["A_recovery"] = squeeze_fresh(X, Y, np.zeros(16), 4.2, 5.0, seed=11, n=16)
    # B. the same 4x4 grid already at 4.0: no gain is allowed to be reported
    X2 = np.array([i + 0.5 for j in range(4) for i in range(4)], dtype=float)
    Y2 = np.array([j + 0.5 for j in range(4) for i in range(4)], dtype=float)
    out["B_optimum"] = squeeze_fresh(X2, Y2, np.zeros(16), 4.0, 5.0, seed=12, n=16)
    return out


def pocket_control():
    """Run 131's exact pocket enumeration, as Family I's band-5 control."""
    import band5 as B5
    pb = B5.pocket_bound(kmax=4)
    return {"max_cells": pb["max_cells"], "at": pb["at"],
            "admissible": pb["admissible_tuples"],
            "bound_argument": B5.bound_argument()}


# ------------------------------------------------- Family III: one-axis rows
def axis_rows():
    """The 44 rows whose poses have a single binding axis (from run 134)."""
    with open(os.path.join(ROOT, "workspace/push/pure_slide134_all.json")) as f:
        rec = json.load(f)
    rows = []
    for r in rec["rows"]:
        w = r.get("walls") or {}
        ax = bool(w.get("xlo", {}).get("attains_side") and w.get("xhi", {}).get("attains_side"))
        ay = bool(w.get("ylo", {}).get("attains_side") and w.get("yhi", {}).get("attains_side"))
        if ax != ay:
            rows.append({"n": r["n"], "axis": "x" if ax else "y",
                         "L": r["L0"], "dL_slide": r.get("dL"),
                         "wall_set_step": r.get("max_set_attaining")})
    return rows


def axis_census(rows):
    """Exact spans of every one-axis row: how much room the free axis really has."""
    import legal_slide as LSL
    out = []
    for r in rows:
        st = LSL.load_pose(int(r["n"]))
        dr = LSL.directions(st)
        xlo, xhi, ylo, yhi = LSL.spans(st, dr)
        sx, sy = xhi - xlo, yhi - ylo
        other = sy if r["axis"] == "x" else sx
        L = max(sx, sy)
        out.append({"n": r["n"], "axis": r["axis"], "L": str(L),
                    "span_x": str(sx), "span_y": str(sy),
                    "free_axis_slack": str(L - other),
                    "equal_axes": bool(sx == sy)})
    return out


def axis_probe(rows, cap=12, limit=3):
    """Bounded exact anchor-closure construction at a one-axis row's own count."""
    import anchor_chain as AC
    field = AC.FIELDS[2]
    out = []
    for r in rows[:limit]:
        n = int(r["n"])
        target = Fraction(Decimal(r["L"])) - THOU
        t0 = time.monotonic()
        got = AC.settle(n, field.q(target), field, node_cap=cap, top=8,
                        mode="lattice")
        out.append({"n": n, "L_target": str(float(Decimal(r["L"]) - Decimal("0.001"))),
                    "cap": cap, "placed": len(got["placed"]), "why": got["why"],
                    "nodes": got["nodes"], "states": got["states"],
                    "refusals": got["refusals"], "exhausted": got["exhausted"],
                    "seconds": round(time.monotonic() - t0, 1)})
        print(f"  n={n}: {out[-1]['placed']}/{n} placed at L - 1/1000 "
              f"({out[-1]['why']}, nodes {out[-1]['nodes']}, {out[-1]['seconds']}s)",
              flush=True)
    return out


# ---------------------------------------------------------------- selftest
def selftest() -> int:
    """Five controls: the lemma, run 84's form, the pocket cap, two refusals."""
    # 1. the two inequalities, exactly, on every word; equality iff 45 degrees
    for w in words():
        F = w.field
        inv = F(1) / (w.c + w.s)
        assert inv * inv >= F(Fraction(1, 2)), w.name
        assert w.mx() * w.mx() >= F(Fraction(1, 2)), w.name
        both = (inv * inv == F(Fraction(1, 2))) and (w.mx() * w.mx() == F(Fraction(1, 2)))
        assert both == bool(w.c == w.s), w.name
    print("  1. lemma: 1/(c+s) >= sqrt2/2 and max(c,s) >= sqrt2/2 on all 4 "
          "words, both equal iff 45 deg")

    # 2. the 45-degree family reproduces run 84 exactly, and matches mixed_field
    w45 = words()[0]
    for k, m in ((1, 1), (2, 1), (2, 3), (3, 2)):
        L = seam_side(w45, k, m)
        assert L == w45.field(2 * k) + w45.field(0, Fraction(m, 2)), (k, m)
        cells = strip_pose(w45, k, m, L)
        v, p, why = gate(cells, L)
        assert v == 0, (k, m, v, p, why)
        st, _ws, _L = MF.strip_sentence(k, m)
        assert len(st) == len(cells) == 4 * k * k + m
        for c, s in zip(cells, st):
            assert abs(fnum(c[0]) - fnum(s[0])) < 1e-9, (k, m)
            assert abs(fnum(c[1]) - fnum(s[1])) < 1e-9, (k, m)
    print("  2. 45 deg family: L == 2k + m*sqrt2/2 exactly, gate 0, and "
          "cell-for-cell equal to mixed_field.strip_sentence")

    # 3. the pocket family's exact cap below 5 is 17
    pc = pocket_control()
    assert pc["max_cells"] == 17 and pc["bound_argument"]["max_cells"] == 17, pc
    print(f"  3. pocket family below L = 5: max {pc['max_cells']} cells "
          f"({pc['admissible']} admissible tuples)")

    # 4. the gate refuses a duplicate with penetration exactly 1
    F = Q2
    up = Word("axis", F(1), F(0))
    dup = [(F(Fraction(1, 2)), F(Fraction(1, 2)), up)] * 2
    v, p, _ = gate(dup, F(2))
    assert v == 1 and p == F(1), (v, p)
    print(f"  4. duplicate cell refused: {v} violation, penetration exactly "
          f"{pretty(p)}")

    # 5. exact refusal below the closed form, on 45 deg and on the ring word
    w7 = words()[1]
    for w, k, m in ((w45, 2, 1), (w7, 2, 1)):
        L = seam_side(w, k, m)
        cells = strip_pose(w, k, m, L)
        v, _p, why = gate(cells, L)
        assert v == 0, (w.name, k, m, v, why)
        vb, pb, _ = gate(cells, L - w.field(THOU))
        assert vb > 0 and pb > 0, (w.name, vb, pb)
    print(f"  5. both seams legal at the closed form and refused 1/1000 below: "
          f"45 deg L = {dec(seam_side(w45, 2, 1))[:10]}, "
          f"ring L = {dec(seam_side(w7, 2, 1))[:10]} (ring strictly worse)")
    print("  selftest OK (5 controls)")
    return 0


# -------------------------------------------------------------------- main
def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()
    rec = {"words": [w.name for w in words()], "lemma": lemma_rows()}
    if "--families" in argv or not argv:
        rows = family_table()
        best = band5_best(rows)
        rec["family"] = rows
        rec["below5_best"] = best
        rec["pocket"] = pocket_control()
        print("[lemma] the closed form's two terms per word (exact):")
        print(f"  {'word':24s} {'1/(c+s)':>10s} {'max(c,s)':>10s} {'45?':>4s}")
        for r in rec["lemma"]:
            print(f"  {r['word']:24s} {Decimal(r['inv_c_plus_s']):10.6f} "
                  f"{Decimal(r['max_cs']):10.6f} {'yes' if r['is_45'] else ' no':>4s}")
        print("\n[family] certified side of the four-corner seam (gate 0, "
              "refused 1/1000 below):")
        print(f"  {'word':24s} {'k':>2s} {'m':>2s} {'n':>3s} {'L':>11s} "
              f"{'grid':>4s} {'gain':>9s} {'<5':>3s} status")
        for w in words():
            for r in sorted((r for r in rows if r["word"] == w.name),
                            key=lambda r: (r["n"], r["m"])):
                if r["n"] > 24:
                    continue
                print(f"  {w.name:24s} {r['k']:2d} {r['m']:2d} {r['n']:3d} "
                      f"{Decimal(r['side']):11.6f} {r['grid']:4d} "
                      f"{Decimal(r['gain_vs_grid']):+9.6f} "
                      f"{'yes' if r['below_5'] else ' no':>3s} {r['status']}")
        print("\n[family] largest count below L = 5, per word:")
        for name, r in best.items():
            print(f"  {name}: n = {r['n']} at L = {Decimal(r['side']):.9f} "
                  f"(k = {r['k']}, m = {r['m']})")
        print(f"[pocket] run 131's exact cap in its own family: "
              f"{rec['pocket']['max_cells']} cells below 5")
    if "--band5" in argv:
        rec["band5"] = band5_run()
        rec["band5_controls"] = band5_controls()
        print("[band5] controls:", json.dumps(
            {k: {"dL": v.get("dL"), "p": v["p_projected"][:14],
                 "side": (v.get("certified") or {}).get("side", "n/a")[:20],
                 "hit": v["hit"]}
             for k, v in rec["band5_controls"].items()}, indent=1))
    if "--axis" in argv:
        rows = axis_rows()
        rec["axis_rows"] = rows
        rec["axis_census"] = axis_census(rows)
        print(f"[axis] {len(rows)} one-binding-axis rows in run 134's record")
        sl = sorted(Decimal(c["free_axis_slack"]) for c in rec["axis_census"])
        print(f"[axis] free-axis slack: min {sl[0]:.6f} median {sl[len(sl)//2]:.6f} "
              f"max {sl[-1]:.6f}")
        for c in rec["axis_census"][:6]:
            print(f"  n={c['n']:4d} binding {c['axis']}: spans "
                  f"{Decimal(c['span_x']):.6f} x {Decimal(c['span_y']):.6f}, "
                  f"free-axis slack {Decimal(c['free_axis_slack']):.6f}")
        rec["axis_probe"] = axis_probe(rows)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(rec, f, indent=1, default=str)
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
