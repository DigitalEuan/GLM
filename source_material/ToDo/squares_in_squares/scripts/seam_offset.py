#!/usr/bin/env python3
r"""seam_offset.py — W1, started: the multi-lattice seam with the offset FREE.

WHAT THIS IS FOR.  `22` §3 refused n = 290 because its 50 tilted squares do not
lie on one 45 deg lattice, and `23` §3 split them into two frames and *recorded*
the split.  Both treated the offset between the frames as a fact about a
delivered row.  W1 (`WHITEBOARD.md`, "Squares in Squares") asks the other
question: a seam between two lattices is a *configuration*, so its offset is a
degree of freedom — can shifting one lattice along the seam buy side?

THE ATOM.  A delivered row is read as:
  * upright squares -> wall anchors (mode, index) with coordinate a + b*L, a in
    half-integers, b in {0, 1/2, 1} -- `seam_wheels.posfunc`, unchanged;
  * tilted squares -> their delivered centres, grouped into frames by the
    45 deg lattice residue.  Two tilted centres are on one 45 deg lattice iff
    (x + y)/sqrt2 and (x - y)/sqrt2 have the same fractional part modulo 1/2, so
    the residue of 2*(x +- y)/sqrt2 modulo 1 identifies the frame.  The `% 1`
    fold is load-bearing: without it a residue of -1e-9 reads as 0.999999999 and
    splits one frame into two -- the bug `23` §3 already paid for once.
  * a frame is a *label*, not a reconstruction: group B is translated by the
    seam shift s and nothing else moves with it.  The exact gate below is asked
    about the resulting state, so a group that has been labelled wrongly shows
    up as an infeasible or absurd side, not as a silent claim.

THE FREE PARAMETER AND THE DECLARED SET.  The seam is shifted along (1, -1)/sqrt2
by s, i.e. group B's centres move by (s/2, -s/2).  The declared set is
{0} U {j*sqrt2/8 : j = -8..8} -- 17 surd shifts plus the delivered position, so
a *positive* answer cannot be blamed on a lucky float.  Every shift is exact in
Q(sqrt2), which is the field the whole atom lives in.

WHAT IS SOLVED, AND WHAT IS CERTIFIED.  For each declared s the side is found by
a two-sided bisection whose predicate is the float gate on the 12-dp state; that
only *nominates*.  The nominated side and every coordinate are then snapped to
Q(sqrt2) and replayed through `seam_wheels.exact_gate`, which recomputes
containment and all SAT axes with no floats.  If the snapped state is refused it
is nudged upward in 1e-9 steps and the first passing side is reported: a pass is
a certificate of FEASIBILITY at that exact side, never of optimality, and the
nudge is stated rather than hidden.

CONTROLS (all must pass; `--selftest`):
  1  n = 226 (one frame) reproduces its delivered side -- the degradation check,
     and the check that the split is not simply always returning two frames;
  2  n = 290 at s = 0 rebuilds the delivered row and lands on its delivered side;
  3  the measured frames are reported with their exact Q(sqrt2) offset, and a
     0.25-moved copy of the atom is refused at the delivered side.

READ-ONLY apart from `workspace/push/seam_offset.json`.

    python3 scripts/seam_offset.py                # census + write ledger
    python3 scripts/seam_offset.py --selftest      # controls only
    python3 scripts/seam_offset.py --no-write
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import declp as D            # noqa: E402
import packlib as P          # noqa: E402
import seam_wheels as SW     # noqa: E402
import sqscore as SQ         # noqa: E402

ROOT = os.path.dirname(HERE)
LEDGER = os.path.join(ROOT, "workspace/push/seam_offset.json")

#: row the two-frame path is measured on, and its one-frame control
TWO_FRAME = 290
ONE_FRAME = 226
#: the declared seam shifts: 0 and every j*sqrt2/8 for |j| <= 8, as (numerator,
#: denominator) over sqrt2, so nothing is rounded before the gate sees it
SHIFTS = [(0, 1)] + [(j, 8) for j in range(-8, 9) if j]
#: a certified gain must survive the finalizer's ~2e-9 pad and the 1e-9 nudge
GAIN_MIN = 4e-8
#: bisection width on the side
WIDE = 1.0
#: NOMINATION ONLY.  The bisection predicate is a float gate asked with this
#: tolerance, which is the size of the contact pad the CSV itself carries; no
#: result is reported from it.  `packlib.finalize` cannot be the predicate: it
#: *scales* the state (by up to 3e-5 on its later tries), so "finalize succeeds"
#: means "feasible at a side above the one asked about" -- measured as a false
#: 2.4e-6 gain on the n = 226 control before this was fixed.
NOM_TOL = 1e-9
#: cluster tolerance on the folded 45 deg residue (the rows are stored with a
#: 2e-9 pad, so residues carry ~1e-9 of noise; 1e-3 is generous and still
#: separates frames that are 1/8 of a lattice step apart)
RES_TOL = 1e-3


class Refusal(Exception):
    """The row is not an atom this instrument can describe."""


# ------------------------------------------------------------------ describe
def _fold(v: float) -> float:
    """Fractional part in [0, 1), with a residue of 1 - eps folded to 0.

    The comparison has to be a *distance*, not a one-sided test: a residue that
    comes back as exactly 1 - 1e-9 fails `f > 1 - 1e-9` and survives as
    0.999999999, which then sits 1e-9 from a residue of 0 and 1 away from it
    depending on which side of the comparison it lands.  That is `23` §3's bug
    in a new place, so the fold is by tolerance and the clustering below uses
    the circular distance.
    """
    f = v % 1.0
    return 0.0 if f > 1.0 - RES_TOL or f < RES_TOL else f


def _dist(a: float, b: float) -> float:
    """Circular distance between two residues in [0, 1)."""
    d = abs(a - b) % 1.0
    return min(d, 1.0 - d)


def describe2(n: int, per: dict) -> dict:
    """Read a delivered row as anchors + tilted groups.  No fitting, no p."""
    raw = [tuple(map(float, s)) for s in per[n]]
    L = SQ.extent(raw)
    ex = [0.5 * (abs(math.cos(t)) + abs(math.sin(t))) for _, _, t in raw]
    ox = min(x - e for (x, _, _), e in zip(raw, ex))
    oy = min(y - e for (_, y, _), e in zip(raw, ex))
    st = [(x - ox, y - oy, t) for x, y, t in raw]

    axis, tilt = [], []
    for x, y, t in st:
        if abs(t % (math.pi / 2)) > 1e-9:
            tilt.append((x, y))
            continue
        kx, ky = SW._code(x, L), SW._code(y, L)
        if kx is None or ky is None:
            raise Refusal(f"n={n}: an upright square is not on a wall/centre "
                          f"anchor, so the atom is not in this grammar")
        axis.append((kx[0], kx[1], ky[0], ky[1]))

    # frames, by the folded 45 deg residue of 2*(x +- y)/sqrt2
    res = []
    for x, y in tilt:
        rx, ry = 2.0 * (x + y) / math.sqrt(2), 2.0 * (x - y) / math.sqrt(2)
        res.append((_fold(rx), _fold(ry)))
    groups: list[list[int]] = []
    for k, r in enumerate(res):
        for g in groups:
            if (_dist(r[0], res[g[0]][0]) < RES_TOL
                    and _dist(r[1], res[g[0]][1]) < RES_TOL):
                g.append(k)
                break
        else:
            groups.append([k])
    sizes = sorted(len(g) for g in groups)
    for g in groups:
        p = int(round(math.sqrt(len(g))))
        if p * p != len(g):
            raise Refusal(f"n={n}: a tilted frame has {len(g)} sites, not a "
                          f"square p^2")
    if len(groups) > 2:
        raise Refusal(f"n={n}: {len(groups)} tilted frames; this instrument "
                      f"declares at most two")

    # the measured frame offset: the two residues differ by an element of
    # Q(sqrt2) in the (x - y) and (x + y) directions
    off = None
    if len(groups) == 2:
        da = _fold(res[groups[1][0]][0] - res[groups[0][0]][0])
        db = _fold(res[groups[1][0]][1] - res[groups[0][0]][1])
        off = {"d_res_2x": da, "d_res_2y": db,
               "d_x_plus_y": da * math.sqrt(2) / 2,
               "d_x_minus_y": db * math.sqrt(2) / 2}
    return {"n": n, "L0": L, "L": L, "axis": axis, "tilt": tilt,
            "group": [0] * len(tilt), "groups": groups, "sizes": sizes,
            "offset": off, "state": st}


def _label(atom: dict) -> dict:
    """Group labels 0/1 per tilted square; group 0 is the larger (ties: first)."""
    lab = [0] * len(atom["tilt"])
    gs = atom["groups"]
    if len(gs) == 2:
        order = sorted(range(len(gs)), key=lambda i: (-len(gs[i]), i))
        for rank, gi in enumerate(order):
            for k in gs[gi]:
                lab[k] = rank
    atom = dict(atom)
    atom["group"] = lab
    return atom


# --------------------------------------------------------------------- build
def build(atom: dict, L: float, s: float = 0.0) -> list:
    """The state at side L with group-1 tilted centres shifted by s along (1,-1)."""
    st = []
    for (xm, xi, ym, yi) in atom["axis"]:
        a0, aL = SW.posfunc(xm, xi)
        b0, bL = SW.posfunc(ym, yi)
        st.append((a0 + aL * L, b0 + bL * L, 0.0))
    for (x, y), g in zip(atom["tilt"], atom["group"]):
        d = 0.5 * s if g == 1 else 0.0
        st.append((x + d, y - d, math.pi / 4))
    return st


def _ok(st: list) -> bool:
    """Nomination predicate: the float gate at the CSV's own pad.  Not a judge."""
    return bool(P.verify(P.round_state(list(st)), tol=NOM_TOL)["ok"])


def min_side(atom: dict, s: float = 0.0) -> dict:
    """A LOCAL two-sided bracket on L: lo infeasible, hi feasible.

    Feasibility is not monotone in L here: a far-anchored upright square moves
    with the side while a near-anchored one does not, so raising L slides one
    row of the fill into another.  The bracket is therefore found by walking, and
    it certifies a *local* minimum only -- the same limitation `22` §2 carries,
    and it is why a shifted seam is reported as `bracket`, never as optimal.
    """
    L0 = atom["L0"]
    hi = None
    for k in range(81):                     # a feasible side, the delivered one first
        L = L0 if k == 0 else L0 + 0.05 * k
        if _ok(build(atom, L, s)):
            hi = L
            break
    if hi is None:
        return {"lo": None, "hi": None}
    step = 0.05                             # an infeasible side below it
    L = hi - step
    while L > 0.5 and _ok(build(atom, L, s)):
        hi = L
        step *= 2.0
        L = hi - step
    lo = max(L, 0.16)
    if _ok(build(atom, lo, s)):
        return {"lo": None, "hi": hi}
    for _ in range(70):
        mid = 0.5 * (lo + hi)
        if mid <= lo or mid >= hi:
            break
        if _ok(build(atom, mid, s)):
            hi = mid
        else:
            lo = mid
    return {"lo": lo, "hi": hi}


# ---------------------------------------------------------------- certify
def _qbase(atom: dict) -> list:
    """The delivered tilted centres in Q(sqrt2), snapped once and cached.

    Snapping the *shifted* coordinate instead would have to reach a Q(sqrt2)
    element of height up to 220 + den, and `seam_wheels.snap` refuses beyond its
    height bound (measured: 13.886485388 has no snap of height <= 220 once
    sqrt2/8 is added).  The base is the part with a small height; the shift is
    added exactly afterwards, which is also faster.
    """
    if atom.get("qbase") is None:
        qb = []
        for x, y in atom["tilt"]:
            try:
                qb.append((SW.snap(x), SW.snap(y)))
            except ValueError as exc:
                raise Refusal(f"tilted centre ({x:.9f}, {y:.9f}) is not in "
                              f"Q(sqrt2): {exc}") from exc
        atom["qbase"] = qb
    return atom["qbase"]


def certify(atom: dict, L: float, num: int, den: int) -> dict:
    """Snap L to Q(sqrt2), add the exact shift, and replay the exact gate.

    The upright fill is exact by construction (`a + b*L` with a, b exact and L in
    Q(sqrt2)); the tilted part is the delivered centre snapped once plus the
    shift `(num/den)*sqrt2/2` along (1, -1), exactly.  If the resulting exact
    state is refused it is nudged upward in 1e-9 steps and the first passing side
    is reported -- a pass certifies FEASIBILITY at that exact side.
    """
    from fractions import Fraction

    try:
        Lq = SW.snap(L)
        qb = _qbase(atom)
    except (ValueError, Refusal) as exc:
        return {"ok": False, "why": f"snap_failed: {exc}", "L": L}
    sh = SW.Q2(Fraction(0), Fraction(num, 2 * den))
    qs = []
    for (xm, xi, ym, yi) in atom["axis"]:
        a0, aL = SW.posfunc(xm, xi)
        b0, bL = SW.posfunc(ym, yi)
        qs.append((SW._q(Fraction(a0)) + SW._q(Fraction(aL)) * Lq,
                   SW._q(Fraction(b0)) + SW._q(Fraction(bL)) * Lq, 0))
    for (qx, qy), g in zip(qb, atom["group"]):
        qs.append((qx + sh, qy - sh, 1) if g == 1 else (qx, qy, 1))
    for k in range(0, 200):
        Ln = Lq + SW._q(Fraction(k, 10 ** 9))
        g = SW.exact_gate(qs, Ln)
        if g["ok"]:
            return {"ok": True, "L": float(Ln), "nudge": k,
                    "pen": g["worst_pen"], "L_q": Ln.pretty()}
    return {"ok": False, "why": "exact_gate_refused", "L": L}


# ------------------------------------------------------------------ controls
def selftest(per: dict) -> int:
    print("control 1 — n = 226 is one frame and reproduces its delivered side")
    a1 = _label(describe2(ONE_FRAME, per))
    assert len(a1["groups"]) == 1, a1["sizes"]
    r1 = min_side(a1, 0.0)
    assert r1["hi"] is not None, r1
    d1 = r1["hi"] - a1["L0"]
    assert abs(d1) < 1e-6, (r1, a1["L0"])
    print(f"  n={ONE_FRAME}: {a1['sizes']} tilted, min side {r1['hi']:.9f} "
          f"vs delivered {a1['L0']:.9f} ({d1:+.2e})")

    print("control 2 — n = 290 at s = 0 rebuilds the delivered atom")
    a2 = _label(describe2(TWO_FRAME, per))
    assert len(a2["groups"]) == 2, a2["sizes"]
    st = build(a2, a2["L0"], 0.0)
    sa = sorted((round(x, 6), round(y, 6)) for x, y, _ in a2["state"])
    sb = sorted((round(x, 6), round(y, 6)) for x, y, _ in st)
    err = max(max(abs(p[0] - q[0]), abs(p[1] - q[1])) for p, q in zip(sa, sb))
    assert err < 1e-7, err
    r2 = min_side(a2, 0.0)
    assert r2["hi"] is not None, r2
    d2 = r2["hi"] - a2["L0"]
    assert abs(d2) < 1e-6, (r2, a2["L0"])
    off = a2["offset"]
    print(f"  n={TWO_FRAME}: {a2['sizes']} tilted, rebuild error {err:.1e}, "
          f"min side {r2['hi']:.9f} vs delivered {a2['L0']:.9f} ({d2:+.2e})")
    print(f"  measured frame offset: d(x-y) = {off['d_x_minus_y']:.9f}, "
          f"d(x+y) = {off['d_x_plus_y']:.9f}")
    for key in ("d_x_minus_y", "d_res_2y"):
        q = SW.snap(off[key])
        print(f"    {key} = {off[key]:.9f}  -> Q(sqrt2) {q.pretty() if q else 'no snap <= 220'}")

    print("control 3 — the gate is the judge: a 0.25-moved atom is refused")
    g = D.gate(TWO_FRAME, a2["state"], [t for _, _, t in a2["state"]], a2["L0"])
    assert g["ok"], g
    bad = [list(q) for q in a2["state"]]
    bad[0][0] += 0.25 * (bad[1][0] - bad[0][0])
    bad[0][1] += 0.25 * (bad[1][1] - bad[0][1])
    gb = D.gate(TWO_FRAME, bad, [t for _, _, t in a2["state"]], a2["L0"])
    assert not gb["ok"] and gb["worst_pen"] > 0, gb
    print(f"  delivered gates at {g['L']:.9f}; a 0.25-moved copy is refused "
          f"(pen {gb['worst_pen']:.6f})")
    print("selftest: OK")
    return 0


# --------------------------------------------------------------------- census
def census(per: dict, write: bool = True) -> int:
    atom = _label(describe2(TWO_FRAME, per))
    L0 = atom["L0"]
    off = atom["offset"]
    print(f"n = {TWO_FRAME}: {len(atom['tilt'])} tilted in frames {atom['sizes']}, "
          f"{len(atom['axis'])} upright, delivered side {L0:.9f}")
    print(f"measured frame offset: d(x-y) = {off['d_x_minus_y']:+.9f}  "
          f"d(x+y) = {off['d_x_plus_y']:+.9f}")
    for key in ("d_x_minus_y", "d_res_2y"):
        q = SW.snap(off[key])
        print(f"  {key} in Q(sqrt2): {q.pretty() if q else 'no snap <= 220'}")

    print(f"\n{'shift s':>16} {'min side':>13} {'vs L0':>11}  certified")
    rows, best = [], None
    for num, den in SHIFTS:
        s = num * math.sqrt(2) / den
        r = min_side(atom, s)
        if r["hi"] is None:
            rows.append({"shift": s, "shift_q": f"{num}/{den}*sqrt2",
                         "L": None, "verdict": "lp_infeasible"})
            print(f"{num:>+6}/{den}*sqrt2    {'-':>13} {'-':>11}  infeasible")
            continue
        c = certify(atom, r["hi"], num, den)
        rec = {"shift": s, "shift_q": f"{num}/{den}*sqrt2", "L": c.get("L"),
               "nudge": c.get("nudge"), "certified": bool(c["ok"]),
               "delta": (c["L"] - L0) if c["ok"] else None,
               "lo": r["lo"], "hi": r["hi"]}
        rows.append(rec)
        tag = "yes" if c["ok"] else f"no ({c.get('why')})"
        dl = f"{c['L'] - L0:+.3e}" if c["ok"] else "-"
        print(f"{num:>+6}/{den}*sqrt2  {r['hi']:13.9f} {dl:>11}  {tag}")
        if c["ok"] and (best is None or c["L"] < best["L"]):
            best = rec
    gains = [r for r in rows if r.get("delta") is not None and r["delta"] < -GAIN_MIN]
    print(f"\nbest certified side {best['L']:.9f} at s = {best['shift_q']} "
          f"({best['delta']:+.3e} vs delivered); certified gains: {len(gains)}")
    out = {"note": "W1 start: the multi-lattice seam offset is a free declared "
                   "parameter, solved and certified in Q(sqrt2)",
           "n": TWO_FRAME, "L0": L0, "sizes": atom["sizes"],
           "offset": off, "rows": rows,
           "best": best, "gains": len(gains)}
    if write:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "w") as f:
            json.dump(out, f, indent=1)
        print(f"ledger -> {os.path.relpath(LEDGER, ROOT)}")
    return 0


def main() -> int:
    per = SQ.load()
    if "--selftest" in sys.argv:
        return selftest(per)
    return census(per, write="--no-write" not in sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
