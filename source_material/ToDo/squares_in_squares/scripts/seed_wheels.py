#!/usr/bin/env python3
r"""seed_wheels.py — construction GRAMMARS, not optimizers.

The evidence so far says ranking and polishing existing arrangements does not
produce a new packing word (`19` §6, `21` §5, `22` §5: every boundary move costs
0.76–0.92 of side).  This instrument adds two new families as wheels, each with
the six parts a wheel needs: a declared grammar, a count law, an exact builder, a
gate, a canonical scorer, and a ledger that keeps survivors AND refusals.

PART A — the two-tilt small-seed wheel at n = 10.
    The corrected ranking (`22` §6) puts n = 10 at the top of the optimistic r = 1
    starts, and that row has only TWO tilted squares: no strip for the mask edits
    of `22` to act on.  The grammar here is bounded and declared:
      tilt pair  3 shapes: two 45° squares sharing an edge (x or y) or a corner
      frame      10 x 10 wall-anchored positions on the sqrt2/2 + 1/2 grid
      fill       3 declared 8-square upright fills: the delivered one, a 3x3 block
                 minus a corner, and a 2x4 bar, all wall-anchored
    Count law: 2 tilted + 8 upright = 10, in every cell.  The side is solved by
    exact bisection in Q(sqrt 2) (two-sided bracket), never fitted.

PART B — the two-frame motif, acceptance test on n = 290.
    `22` §3 refused n = 290 because 25 of its 50 tilted squares lie on a second
    45° lattice.  Representing the tilted part as a UNION of two (frame, mask)
    pairs must reconstruct that row exactly BEFORE anything is perturbed.

SCOPE (the expressiveness ladder, per the run-54 review).  Every refusal in the
ledger says what was excluded, not merely that nothing was found:
    field       Q(sqrt2)  (so: no angle with irrational cos/sin)
    frames      1 or 2    (3+ excluded)
    masks       full block, 5-deep strip, two-tilt seed, union of two frames
    placement   wall-anchored on the sqrt2/2 grid, or centred with a Q(sqrt2)
                offset; continuous translation is NOT searched
    angles      0 and pi/4 only.  Rational t = tan(theta/2) gives rational
                cos/sin and would be exactly certifiable, but is not in this scope

READ-ONLY apart from workspace/push/seed_wheels.json.

    python3 scripts/seed_wheels.py [--selftest]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import packlib as P            # noqa: E402
import seam_wheels as SW       # noqa: E402
import sqscore as SQ           # noqa: E402
import diamond_mask as DM      # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/seed_wheels.json")
S = DM.S                       # sqrt2/2
PAD = SW.PAD
GAIN_MIN = SW.GAIN_MIN

SCOPE = {
    "field": "Q(sqrt2)",
    "frames": [1, 2],
    "masks": ["full", "strip", "two-tilt seed", "union of two frames"],
    "placement": ["wall-anchored on the sqrt2/2 grid", "centred with Q(sqrt2) offset"],
    "angles": ["0", "pi/4"],
    "translations": "declared finite set only; continuous translation NOT searched",
    "excluded": [
        "angles outside {0, pi/4} (rational-t fields are certifiable but not here)",
        "three or more lattices",
        "non-wall-anchored fills",
    ],
}


# ============================================================ PART A: seeds
@dataclass(frozen=True)
class Seed:
    """Two tilted squares + a declared upright fill.

    `centred` selects the placement convention: False anchors the block at
    `kappa` (it stays put as L grows, the fill's far wall moves away); True puts
    the block at `L/2 + kappa`.  Both are exact in Q(sqrt2).
    """
    n: int
    sites: tuple          # two (u, v) lattice sites, normalised
    kx: object            # Q2 frame offset of site (0, 0)
    ky: object
    fill: tuple           # upright anchors (xm, xi, ym, yi)
    L_del: float
    rule: str
    centred: bool = False


# Two tilted 45° squares have TWO distinct relations up to the square's own
# symmetry (D4 acts on the index grid, so (1,1) and (1,-1) are copies):
#   edge    centres 1 apart along a 45° normal  -> they share an edge
#   corner  centres sqrt2 apart along an axis   -> they touch at a corner
# The first draft listed (0,0)-(1,1) and (0,1)-(1,0) as different shapes; they
# are the same shape rotated, which the selftest now checks.
PAIR_SHAPES = {
    "edge": ((0, 0), (1, 0)),
    "corner": ((0, 0), (1, 1)),
}


def seed_states_q(seed: Seed, L):
    base = SW.HALF * L if seed.centred else SW.Q2(0)
    st = [(base + seed.kx + (u - v) * SW.R2H,
           base + seed.ky + (u + v) * SW.R2H, 1) for (u, v) in seed.sites]
    for a in seed.fill:
        x = SW._q(SW.posfunc(a[0], a[1])[0]) + SW._q(SW.posfunc(a[0], a[1])[1]) * L
        y = SW._q(SW.posfunc(a[2], a[3])[0]) + SW._q(SW.posfunc(a[2], a[3])[1]) * L
        st.append((x, y, 0))
    return st


def seed_states_f(seed: Seed, L: float):
    base = 0.5 * L if seed.centred else 0.0
    kx, ky = base + float(seed.kx), base + float(seed.ky)
    st = [(kx + (u - v) * S, ky + (u + v) * S, math.pi / 4)
          for (u, v) in seed.sites]
    for a in seed.fill:
        st.append((SW.posfunc(a[0], a[1])[0] + SW.posfunc(a[0], a[1])[1] * L,
                   SW.posfunc(a[2], a[3])[0] + SW.posfunc(a[2], a[3])[1] * L,
                   0.0))
    return st


def seed_gate_f(seed: Seed, L: float, pairs) -> bool:
    st = seed_states_f(seed, L)
    o = [0 if abs(t % (math.pi / 2)) < 1e-9 else 1 for _, _, t in st]
    for (i, j) in pairs:
        xi, yi, _ = st[i]
        xj, yj, _ = st[j]
        best = None
        for ax in SW.AXES_OF[(o[i], o[j])]:
            ux, uy = SW.DIRS[ax]
            pr = (xi - xj) * float(ux) + (yi - yj) * float(uy)
            v = float(SW.EXT[o[i]][ax] + SW.EXT[o[j]][ax]) - abs(pr)
            if best is None or v < best:
                best = v
        if best > 1e-12:
            return False
    # containment, in floats (nomination only); a 45 degree square has an AABB
    # half-extent of (|cos|+|sin|)/2 = sqrt2/2, not 1/2
    for x, y, th in st:
        h = 0.5 * (abs(math.cos(th)) + abs(math.sin(th)))
        if x - h < -1e-12 or y - h < -1e-12:
            return False
    return True


def seed_min_side(seed: Seed, lo0: float, hi0: float, iters: int = 34):
    """Exact-in-the-limit minimum side for the seed, by bisection."""
    n = len(seed.sites) + len(seed.fill)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    lo, hi = lo0, hi0
    if not seed_gate_f(seed, hi, pairs):
        for _ in range(8):
            hi += 0.5
            if seed_gate_f(seed, hi, pairs):
                break
        else:
            return None, None
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if seed_gate_f(seed, mid, pairs):
            hi = mid
        else:
            lo = mid
    return lo, hi


def seed_certify(seed: Seed, hi: float):
    for _ in range(5):
        Lq = SW.Q2(Fraction(round(hi * 10 ** 9), 10 ** 9))
        g = SW.exact_gate(seed_states_q(seed, Lq), None)
        if g["ok"]:
            return True, g["L"], g["worst_pen_q"]
        hi += 1e-8
    return False, g["L"], g["worst_pen_q"]


def fills_for(n: int, per: dict):
    """Declared 8-square WALL-ANCHORED fills.  Count law: 8 + 2 = 10.

    The delivered n=10 fill is centred, not wall-anchored, so it belongs to the
    control (see selftest) and not to this grammar.
    """
    corner = [(0, i, 0, j) for i in range(3) for j in range(3)
              if not (i == 2 and j == 2)]
    return {"3x3-corner": tuple(corner),
            "bar2x4": tuple((0, i, 0, j) for i in range(2) for j in range(4))}


def _cell(sd: Seed, n: int, L_del: float, floor) -> dict:
    lo, hi = seed_min_side(sd, math.sqrt(n) * 0.95, L_del + 0.5)
    if hi is None:
        return {"rule": sd.rule, "outcome": "no_side_packs",
                "excluded_by": "declared frame grid"}
    ok, Lq, pen = seed_certify(sd, hi)
    if not ok:
        return {"rule": sd.rule, "outcome": "candidate_rejected_exact",
                "detail": f"nominated {hi:.9f} fails the exact gate"}
    gain = L_del - float(Lq)
    return {"rule": sd.rule, "L_exact": Lq.pretty(), "L_exact_float": float(Lq),
            "pen": pen, "n": n, "count": len(sd.sites) + len(sd.fill),
            "centred": sd.centred,
            "outcome": ("feasible_gain" if gain > GAIN_MIN else "feasible_no_gain"),
            "gain": gain, "beats_bound": bool(floor and float(Lq) >= floor - 1e-9)}


def centred_wheel(n: int, per: dict) -> list[dict]:
    """The delivered 8-square fill with the two-tilt block CENTRED in it.

    This is the half of the grammar that can express the delivered row itself
    (which is centred, not wall-anchored), so a positive here would be a new
    word at n = 10 rather than a re-parameterisation.
    """
    L_del = SQ.extent(per[n])
    floor = SW.bound_karakus(n)
    try:
        fill = DM.describe_mask(n, per).axis
    except SW.Refusal as e:
        return [{"rule": "centred control", "outcome": e.reason, "detail": e.detail}]
    rows = []
    offs = (-1, 0, 1)
    for pname, sites in PAIR_SHAPES.items():
        for jx in offs:
            for jy in offs:
                for b in (0, 1):
                    kx = SW.Q2(Fraction(jx, 1)) * SW.R2H + SW.Q2(Fraction(b, 2))
                    ky = SW.Q2(Fraction(jy, 1)) * SW.R2H + SW.Q2(Fraction(b, 2))
                    sd = Seed(n, sites, kx, ky, fill, L_del,
                              f"centred/{pname}/offset({jx}+{b}/2,{jy}+{b}/2)",
                              centred=True)
                    rows.append(_cell(sd, n, L_del, floor))
    return rows


def seed_wheel(n: int, per: dict) -> list[dict]:
    """Enumerate the declared two-tilt grammar and gate every cell exactly."""
    L_del = SQ.extent(per[n])
    floor = SW.bound_karakus(n)
    rows = []
    frames = [(j, b) for j in range(5) for b in (0, 1)]      # sqrt2/2 grid + 1/2
    for fname, fill in fills_for(n, per).items():
        for pname, sites in PAIR_SHAPES.items():
            for (jx, bx) in frames:
                for (jy, by) in frames:
                    kx = SW.Q2(Fraction(jx, 1)) * SW.R2H + SW.Q2(Fraction(bx, 2))
                    ky = SW.Q2(Fraction(jy, 1)) * SW.R2H + SW.Q2(Fraction(by, 2))
                    sd = Seed(n, sites, kx, ky, fill, L_del,
                              f"{fname}/{pname}/frame({jx}+{bx}/2,{jy}+{by}/2)")
                    rows.append(_cell(sd, n, L_del, floor))
    return rows


# ====================================================== PART B: two frames
def split_lattices(tilt, tol: float = 1e-4):
    """Cluster tilted centres into 45° lattices by their (x-y) residue."""
    if not tilt:
        return []
    m0 = max(x - y for x, y, _ in tilt)
    res = [((x - y) - m0) / (2 * S) for x, y, _ in tilt]
    # A site exactly on the lattice can sit at residual -1e-9, giving frac
    # 0.999999999 instead of 0: rounding and taking mod 1 again folds that back
    # onto 0.0.  Without it one lattice reads as two (it did on n=226, 24 + 1).
    frac = [round(r - math.floor(r), 6) % 1.0 for r in res]
    reps = []
    for f in frac:
        if not any(abs(f - g) < tol for g in reps):
            reps.append(f)
    groups = [[] for _ in reps]
    for s, f in zip(tilt, frac):
        i = min(range(len(reps)), key=lambda j: abs(f - reps[j]))
        groups[i].append(s)
    return groups


def describe_two(n: int, per: dict) -> dict:
    """Frame + mask PER LATTICE, plus the shared fill.  Reconstructs n = 290."""
    raw = [tuple(map(float, s)) for s in per[n]]
    L = SQ.extent(raw)
    ox = min(x - 0.5 * (abs(math.cos(t)) + abs(math.sin(t))) for x, y, t in raw)
    oy = min(y - 0.5 * (abs(math.cos(t)) + abs(math.sin(t))) for x, y, t in raw)
    st = [(x - ox, y - oy, t) for x, y, t in raw]
    tilt = [s for s in st if abs(s[2] % (math.pi / 2)) > 1e-9]
    axis = []
    for x, y, th in st:
        if abs(th % (math.pi / 2)) > 1e-9:
            continue
        kx, ky = SW._code(x, L), SW._code(y, L)
        if kx is None or ky is None:
            raise SW.Refusal("layout_not_enumerated",
                             f"n={n}: upright square with no wall/centre anchor")
        axis.append((kx[0], kx[1], ky[0], ky[1]))
    groups = split_lattices(tilt)
    frames = []
    for g in groups:
        us, vs = DM.lattice_coords(g)
        sites = tuple(sorted(set(zip(us, vs))))
        kxs = [x - (u - v) * S for (x, y, _), (u, v) in zip(g, zip(us, vs))]
        kys = [y - (u + v) * S for (x, y, _), (u, v) in zip(g, zip(us, vs))]
        if max(kxs) - min(kxs) > 1e-6 or max(kys) - min(kys) > 1e-6:
            raise SW.Refusal("layout_not_enumerated",
                             f"n={n}: a tilted cluster has no single frame")
        frames.append({"sites": sites, "n_sites": len(sites),
                       "kx": sum(kxs) / len(kxs), "ky": sum(kys) / len(kys),
                       "u_ext": max(u for u, _ in sites) - min(u for u, _ in sites) + 1,
                       "v_ext": max(v for _, v in sites) - min(v for _, v in sites) + 1})
    total_sites = sum(f["n_sites"] for f in frames)
    if total_sites + len(axis) != n:
        raise SW.Refusal("layout_not_enumerated",
                         f"n={n}: {total_sites} sites + {len(axis)} upright != {n}")
    # rebuild the union and verify one-to-one with orientations
    rb = []
    for f, g in zip(frames, groups):
        rb += [(f["kx"] + (u - v) * S, f["ky"] + (u + v) * S, 1) for (u, v) in f["sites"]]
    for a in axis:
        rb.append((SW.posfunc(a[0], a[1])[0] + SW.posfunc(a[0], a[1])[1] * L,
                   SW.posfunc(a[2], a[3])[0] + SW.posfunc(a[2], a[3])[1] * L, 0))
    ok, err, why = DM.match_states(st, rb)
    if not ok:
        raise SW.Refusal("describe_mismatch", f"n={n}: {why} (max error {err:.2e})")
    # exact gate on the reassembled declaration: snap each frame once, then
    # rebuild every position as kappa + (u-v)s, so the states are exact rather
    # than independently rounded per square
    Lq = SW.Q2(Fraction(round(L * 10 ** 9), 10 ** 9))
    stq = []
    for f in frames:
        kx, ky = SW.snap(f["kx"]), SW.snap(f["ky"])
        stq += [(kx + (u - v) * SW.R2H, ky + (u + v) * SW.R2H, 1)
                for (u, v) in f["sites"]]
    for a in axis:
        stq.append((SW._q(SW.posfunc(a[0], a[1])[0])
                    + SW._q(SW.posfunc(a[0], a[1])[1]) * Lq,
                    SW._q(SW.posfunc(a[2], a[3])[0])
                    + SW._q(SW.posfunc(a[2], a[3])[1]) * Lq, 0))
    g = SW.exact_gate(stq, None)
    off = [round(((f["kx"] - frames[0]["kx"]) ** 2 +
                  (f["ky"] - frames[0]["ky"]) ** 2) ** 0.5, 6) for f in frames]
    return {"n": n, "L_del": L, "frames": len(frames), "upright": len(axis),
            "sites": sum(f["n_sites"] for f in frames),
            "mask_shapes": [(f["u_ext"], f["v_ext"]) for f in frames],
            "frame_offsets": off, "gate_ok": bool(g["ok"]),
            "worst_pen": g["worst_pen_q"], "max_rebuild_err": err}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    s = SQ.guard()
    print(f"[sqscore] delivered: {s['score']:.9f}, {s['beats']} beats, {s['rows']} rows")
    per = SQ.load()
    t0 = time.time()
    out = {"run": 55, "schema": "seed-wheels/1",
           "written": time.strftime("%Y-%m-%d %H:%M:%S"), "scope": SCOPE}

    print("\n== PART A: two-tilt seed wheel, n = 10 ==")
    wall = seed_wheel(10, per)
    cen = centred_wheel(10, per)
    rows = wall + cen
    ok = [r for r in rows if r.get("L_exact_float")]
    gains = [r for r in rows if r.get("outcome") == "feasible_gain"]
    print(f"wall-anchored cells {len(wall)}, centred cells {len(cen)}")
    print(f"cells {len(rows)}, certified {len(ok)}, gains {len(gains)}")
    if ok:
        best = min(ok, key=lambda r: r["L_exact_float"])
        print(f"best seed: {best['L_exact_float']:.9f} ({best['rule']}) "
              f"vs delivered {SQ.extent(per[10]):.9f}  pen={best['pen']}")
        print(f"  Karakus floor s(10) = {SW.bound_karakus(10):.6f}; "
              f"best seed above it: {best['beats_bound']}")
        for tag, grp in (("wall", wall), ("centred", cen)):
            o = [r for r in grp if r.get("L_exact_float")]
            if o:
                b = min(o, key=lambda r: r["L_exact_float"])
                print(f"  {tag:8s} best {b['L_exact_float']:.9f}  {b['rule']}")
            else:
                print(f"  {tag:8s} none certified")
    out["seeds"] = {"n": 10, "cells": rows, "wall_cells": len(wall),
                    "centred_cells": len(cen),
                    "certified": len(ok), "gains": len(gains)}

    print("\n== PART B: two-frame motif, acceptance test on n = 290 ==")
    tw = []
    for n in (290, 226):
        try:
            d = describe_two(n, per)
            print(f"n={n}: frames={d['frames']} shapes={d['mask_shapes']} "
                  f"upright={d['upright']} offsets={d['frame_offsets']} "
                  f"gate={d['gate_ok']} pen={d['worst_pen']} err={d['max_rebuild_err']:.1e}")
            tw.append(d)
        except SW.Refusal as e:
            print(f"n={n}: REFUSED {e.reason}: {e.detail}")
            tw.append({"n": n, "outcome": e.reason, "detail": e.detail})
    out["two_frame"] = tw
    out["seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(f"\nledger: {OUT}")
    return 0


def selftest() -> int:
    checks = []

    def ck(name, cond, extra=""):
        checks.append(bool(cond))
        print(f"  {'ok ' if cond else 'FAIL'} {name:40s} {extra}")

    per = SQ.load()
    # centre delta of two lattice sites (u,v) is ((du-dv)s, (du+dv)s); the two
    # declared classes must be the two distinct adjacency classes
    dists = {k: round(math.hypot((a[0] - b[0] - (a[1] - b[1])) * S,
                                 (a[0] - b[0] + (a[1] - b[1])) * S), 6)
             for k, (a, b) in PAIR_SHAPES.items()}
    ck("pair shapes are 2 distinct classes", len(set(dists.values())) == 2
       and abs(dists["edge"] - 1.0) < 1e-9
       and abs(dists["corner"] - math.sqrt(2)) < 1e-5, str(dists))
    # count law: 2 tilted + 8 upright in every declared fill
    fills = fills_for(10, per)
    ck("every fill has 8 upright", all(len(f) == 8 for f in fills.values()),
       f"{ {k: len(v) for k, v in fills.items()} }")
    # the wheel's control: the delivered 8-square fill, its own frame, must
    # certify at the delivered side (a seed that cannot reproduce the row is a
    # broken builder, not a negative result)
    a = DM.describe_mask(10, per)
    # the delivered block is centred, so its frame is 1/2 L + kx0; rebuild it that
    # way and check the gate at L_del
    stq = [(SW.HALF * SW.Q2(Fraction(round(a.L_del * 10 ** 9), 10 ** 9)) + a.kx0
            + (u - v) * SW.R2H,
            SW.HALF * SW.Q2(Fraction(round(a.L_del * 10 ** 9), 10 ** 9)) + a.ky0
            + (u + v) * SW.R2H, 1) for (u, v) in a.sites]
    stq += [(SW._q(SW.posfunc(q[0], q[1])[0])
             + SW._q(SW.posfunc(q[0], q[1])[1])
             * SW.Q2(Fraction(round(a.L_del * 10 ** 9), 10 ** 9)),
             SW._q(SW.posfunc(q[2], q[3])[0])
             + SW._q(SW.posfunc(q[2], q[3])[1])
             * SW.Q2(Fraction(round(a.L_del * 10 ** 9), 10 ** 9)), 0) for q in a.axis]
    g = SW.exact_gate(stq, None)
    ck("delivered n=10 gates exactly", g["ok"] and len(stq) == 10,
       f"pen={g['worst_pen_q']}")
    ck("n=10 has exactly 2 tilted", len(a.sites) == 2, f"{len(a.sites)} sites")
    # the split must find two lattices at n=290 and one at n=226
    g290 = describe_two(290, per)
    ck("n=290 needs two frames", g290["frames"] == 2 and g290["gate_ok"],
       f"offsets={g290['frame_offsets']}")
    g226 = describe_two(226, per)
    ck("n=226 is one frame", g226["frames"] == 1 and g226["gate_ok"],
       f"sites={g226['sites']}")
    # scope declares the ladder explicitly
    ck("scope declares excluded classes", len(SCOPE["excluded"]) >= 3,
       f"{len(SCOPE['excluded'])} exclusions")
    print(f"\nselftest: {sum(checks)}/{len(checks)} checks pass")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
