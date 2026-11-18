#!/usr/bin/env python3
r"""seam_wheels.py — G-2: the seam, declared, solved, and certified.

WHY THIS FILE EXISTS.  Run 52 (`20-R1-ATOMS.md`) answered G-1 negatively: the
two r = 1 bands use the same orientation alphabet `{axis, pi/4}`, so the 0.520815
step is an ARRANGEMENT, not a new word.  The feedback on that result was direct:
*keep the good block and improve its boundary*, and stop paying for angle search.
This file is the instrument for that: it takes the block as given, declares the
seam as a finite layout, and asks the only question left — how small a side does
that seam admit.

WHAT IS DECLARED, AND WHAT IS SOLVED.  A delivery is described by integers only:

    p            diamond extent (a p x p block of unit squares at 45 deg)
    (dx, dy)     the diamond's offset from the container centre, in half-integers
    [(m, i, m', j)] each upright square's two wall anchors:
                 m = 0 -> wall + 1/2 + i      (near wall)
                 m = 1 -> L - 1/2 - i          (far wall)
                 m = 2 -> L/2 + i              (centre; only one square needs it)

The 45 deg block is not a free lattice: its centres are exactly
`c + ((u - v)/2, (u + v - p + 1)/2) * sqrt(2)`, u, v = 0..p-1, which is the
zero-waste tiling of the rotated frame.  So the whole atom lies in Q(sqrt 2), and
the ONLY free scalar is the side L.  L is then not fitted: it is solved.

THREE STAGES, THREE DIFFERENT LIABILITIES (kept separate in the ledger):

  1. declare   the integer description, read off a delivered row.  A description
               that does not rebuild the row to 1e-8 is `describe_mismatch`.
  2. solve     an LP over (L, tx, ty) — the side and the diamond's translation —
               with one separating axis DECLARED per seam pair (the axis the
               delivered state actually uses, signed by its direction).  Every
               inequality is linear in (L, tx, ty) because each square's
               coordinate is `a + b*L` plus the diamond's translation.
               The LP nominates.  It does not certify: HiGHS works in floats.
  3. certify   the nominated (L, tx, ty) is snapped to Q(sqrt 2) and replayed
               against the exact gate, which recomputes every pair on all four
               SAT axes in exact arithmetic.  A pass is a certificate of
               FEASIBILITY at that exact side — not of optimality; a failure is
               not an infeasibility proof.

LEDGER OUTCOMES (the four the review asked to keep apart):

    layout_not_enumerated   the declaration itself is malformed / does not
                            rebuild the delivered row
    lp_infeasible           the declared seam cannot exist at any side
    numerically_inconclusive the LP nominated a side but no Q(sqrt 2) snap of it
                            passes the exact gate (float artefact or a side that
                            is genuinely not in the field)
    candidate_rejected_exact  a snapped point exists but the exact gate rejects
                            it (and its half-step neighbours); this is NOT a
                            proof that the layout is impossible
    feasible_no_gain        certified at a side >= the delivered one
    feasible_gain           certified STRICTLY below the delivered side

THE BOUND AND THE CONTROL.  `bound_karakus` is s(N) >= 1/2 + sqrt(N - floor
sqrt(N) + 1/4) for nonsquare N >= 8 (Karakus 2026, arXiv:2609.37410, Cor. 1.2),
which is stronger than the area bound everywhere and exact at N = k^2 - 1.  That
endpoint is the negative control: any row n = k^2 - 1 that claims to beat k is a
builder/verifier/scorer bug, because s(k^2-1) = k is a theorem.

READ-ONLY apart from `workspace/push/seam_wheels.json`.

    python3 scripts/seam_wheels.py               # reconstruct + variants + rank
    python3 scripts/seam_wheels.py --selftest     # the checks that must pass
    python3 scripts/seam_wheels.py --no-write
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import packlib as P        # noqa: E402
import sqscore as SQ       # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/seam_wheels.json")

SQ2 = math.sqrt(2.0)
MAX_N = 1000
EPS_GATE = 1e-12
#: packlib.finalize scales every delivered row by ~2e-9, so the STORED side of a
#: row is 2e-9 above the algebraic side it came from.  An exact (unpadded) side
#: therefore looks 2e-9 "better" than the delivered one.  A gain must beat that
#: pad by an order of magnitude to be a gain at all -- this threshold was added
#: after the first sweep reported 0.000000002 as a gain on every r = 1 row.
PAD = 2e-9
GAIN_MIN = 20 * PAD

# ---------------------------------------------------------------- exact field
class Q2:
    """a + b*sqrt(2) with Fraction a, b.  Exact, totally ordered, no floats."""

    __slots__ = ("a", "b")

    def __init__(self, a=0, b=0):
        self.a = a if isinstance(a, Fraction) else Fraction(a)
        self.b = b if isinstance(b, Fraction) else Fraction(b)

    # -- arithmetic -------------------------------------------------------
    def __add__(self, o):
        o = _q(o)
        return Q2(self.a + o.a, self.b + o.b)

    def __radd__(self, o):
        return _q(o).__add__(self)

    def __neg__(self):
        return Q2(-self.a, -self.b)

    def __sub__(self, o):
        o = _q(o)
        return Q2(self.a - o.a, self.b - o.b)

    def __rsub__(self, o):
        return _q(o).__sub__(self)

    def __mul__(self, o):
        if isinstance(o, (int, Fraction)):
            return Q2(self.a * o, self.b * o)
        o = _q(o)
        # (a1 + b1 r)(a2 + b2 r) = a1a2 + 2 b1b2 + (a1b2 + a2b1) r
        return Q2(self.a * o.a + 2 * self.b * o.b,
                  self.a * o.b + o.a * self.b)

    def __rmul__(self, o):
        return self.__mul__(o)

    def __truediv__(self, o):
        if isinstance(o, (int, Fraction)):
            return Q2(self.a / o, self.b / o)
        raise TypeError("only scalar division is exact here")

    # -- order ------------------------------------------------------------
    def _sign(self) -> int:
        a, b = self.a, self.b
        if b == 0:
            return (a > 0) - (a < 0)
        if a == 0:
            return (b > 0) - (b < 0)
        if a > 0 and b > 0:
            return 1
        if a < 0 and b < 0:
            return -1
        # opposite signs: compare a^2 with 2 b^2
        lhs, rhs = a * a, 2 * b * b
        if a > 0:                     # a > 0 > b : sign(a^2 - 2b^2)
            return (lhs > rhs) - (lhs < rhs)
        return (rhs > lhs) - (rhs < lhs)   # a < 0 < b : sign(2b^2 - a^2)

    def __eq__(self, o):
        try:
            o = _q(o)
        except TypeError:
            return NotImplemented
        return self.a == o.a and self.b == o.b

    def __lt__(self, o):
        return (self - _q(o))._sign() < 0

    def __le__(self, o):
        return (self - _q(o))._sign() <= 0

    def __gt__(self, o):
        return (self - _q(o))._sign() > 0

    def __ge__(self, o):
        return (self - _q(o))._sign() >= 0

    def __hash__(self):
        return hash((self.a, self.b))

    def __abs__(self):
        return -self if self._sign() < 0 else Q2(self.a, self.b)

    def __float__(self):
        return float(self.a) + float(self.b) * SQ2

    def __repr__(self):
        return f"Q2({self.a},{self.b})"

    def pretty(self) -> str:
        a, b = self.a, self.b
        if b == 0:
            return str(a)
        if a == 0:
            return f"{b}*sqrt2"
        return f"{a}{'+' if b > 0 else '-'}{abs(b)}*sqrt2"


def _q(x) -> Q2:
    if isinstance(x, Q2):
        return x
    if isinstance(x, Fraction):
        return Q2(x, 0)
    if isinstance(x, int):
        return Q2(x, 0)
    if isinstance(x, float):
        # only exact for dyadic rationals; the declaration only ever uses halves
        f = Fraction(x).limit_denominator(10 ** 6)
        if abs(float(f) - x) > 1e-12:
            raise TypeError(f"float {x!r} is not a small rational")
        return Q2(f, 0)
    raise TypeError(f"cannot make a Q2 from {type(x).__name__}")


ZERO, HALF, ONE = Q2(0), Q2(Fraction(1, 2)), Q2(1)
R2H = Q2(0, Fraction(1, 2))          # sqrt(2)/2


# ------------------------------------------------------------ orientations
#: 0 = axis-aligned, 1 = exactly 45 degrees.  Both have edge normals among
#: ('x', 'y') and ('d+', 'd-') respectively, so the SAT axis set is finite.
DIRS = {"x": (ONE, ZERO), "y": (ZERO, ONE), "d+": (R2H, R2H), "d-": (R2H, -R2H)}
#: extent of a square of orientation o along each SAT direction
EXT = {0: {"x": HALF, "y": HALF, "d+": R2H, "d-": R2H},
       1: {"x": R2H, "y": R2H, "d+": HALF, "d-": HALF}}
AXES_OF = {(0, 0): ("x", "y"), (1, 1): ("d+", "d-"),
           (0, 1): ("x", "y", "d+", "d-"), (1, 0): ("x", "y", "d+", "d-")}


def dot(ax: str, dx: Q2, dy: Q2) -> Q2:
    ux, uy = DIRS[ax]
    return dx * ux + dy * uy


def pen_exact(oa: int, ob: int, dx: Q2, dy: Q2) -> Q2:
    """min over the pair's SAT axes of (ext_a + ext_b - |projection|)."""
    best = None
    for ax in AXES_OF[(oa, ob)]:
        v = EXT[oa][ax] + EXT[ob][ax] - abs(dot(ax, dx, dy))
        if best is None or v < best:
            best = v
    return best


def best_axis(oa: int, ob: int, dx: Q2, dy: Q2):
    """(axis, signed projection) of the binding SAT axis."""
    best = None
    for ax in AXES_OF[(oa, ob)]:
        pr = dot(ax, dx, dy)
        v = EXT[oa][ax] + EXT[ob][ax] - abs(pr)
        if best is None or v < best[0]:
            best = (v, ax, pr)
    return best[1], best[2]


# ------------------------------------------------------------------- layout
@dataclass(frozen=True)
class Atom:
    """A delivery read as integers: the diamond and the upright anchors."""
    n: int
    p: int
    dx: float                    # diamond offset from centre, half-integer
    dy: float
    axis: tuple                  # ((xm, xi, ym, yi), ...) per upright square
    L_del: float
    delta_del: float
    meta: dict = field(default_factory=dict)

    def kcols(self) -> tuple:
        """(columns anchored low, columns anchored high) on each axis."""
        lox = max((a[1] for a in self.axis if a[0] == 0), default=-1) + 1
        hix = max((a[1] for a in self.axis if a[0] == 1), default=-1) + 1
        loy = max((a[3] for a in self.axis if a[2] == 0), default=-1) + 1
        hiy = max((a[3] for a in self.axis if a[2] == 1), default=-1) + 1
        return lox + hix, loy + hiy


def posfunc(mode: int, idx: int):
    """(a0, aL) with coordinate = a0 + aL * L, for one axis of one square."""
    if mode == 0:
        return (0.5 + idx, 0.0)
    if mode == 1:
        return (-0.5 - idx, 1.0)
    if mode == 2:
        return (float(idx), 0.5)
    raise ValueError(mode)


def tilt_centre(atom: Atom, u: int, v: int, L: float):
    """Exact 45 deg lattice: centres c + ((u-v), (u+v-p+1)) * sqrt(2)/2."""
    cx = 0.5 * L + atom.dx
    cy = 0.5 * L + atom.dy
    s = math.sqrt(0.5)
    return (cx + (u - v) * s, cy + (u + v - atom.p + 1) * s)


def tilt_centre_q(atom: Atom, u: int, v: int, L: Q2):
    cx = HALF * L + _q(atom.dx)
    cy = HALF * L + _q(atom.dy)
    return (cx + (u - v) * R2H, cy + (u + v - atom.p + 1) * R2H)


def build(atom: Atom, L: float, t=(0.0, 0.0)):
    """Rebuild the state in floats: [(x, y, angle)] in tilt-then-axis order."""
    st = []
    for u in range(atom.p):
        for v in range(atom.p):
            x, y = tilt_centre(atom, u, v, L)
            st.append((x + t[0], y + t[1], math.pi / 4))
    for (xm, xi, ym, yi) in atom.axis:
        x = posfunc(xm, xi)[0] + posfunc(xm, xi)[1] * L
        y = posfunc(ym, yi)[0] + posfunc(ym, yi)[1] * L
        st.append((x, y, 0.0))
    return st


def wall_signature(atom: Atom, L: float | None = None, tol: float = 1e-6):
    """How the atom meets its container: per wall, how many squares of each kind.

    This is the reviewer's third output and it is what makes the two r = 1 atoms
    comparable at all: n=65 touches all four walls with upright squares only,
    n=626 does the same but through a 25-column upright fill.  A block that did
    not reach a wall would not be pinned, and the LP would say so.
    """
    L = atom.L_del if L is None else L
    st = build(atom, L)
    sig = {"left": [0, 0], "right": [0, 0], "bottom": [0, 0], "top": [0, 0]}
    for x, y, th in st:
        o = 1 if abs(th % (math.pi / 2)) > 1e-9 else 0
        e = math.sqrt(0.5) if o else 0.5
        if abs(x - e) <= tol:
            sig["left"][o] += 1
        if abs(x + e - L) <= tol:
            sig["right"][o] += 1
        if abs(y - e) <= tol:
            sig["bottom"][o] += 1
        if abs(y + e - L) <= tol:
            sig["top"][o] += 1
    return sig


def build_q(atom: Atom, L: Q2, t=(Q2(0), Q2(0))):
    """Rebuild the same state in Q(sqrt 2)."""
    st = []
    for u in range(atom.p):
        for v in range(atom.p):
            x, y = tilt_centre_q(atom, u, v, L)
            st.append((x + t[0], y + t[1], 1))
    for (xm, xi, ym, yi) in atom.axis:
        a0, aL = posfunc(xm, xi)
        x = _q(float(a0)) + _q(float(aL)) * L
        b0, bL = posfunc(ym, yi)
        y = _q(float(b0)) + _q(float(bL)) * L
        st.append((x, y, 0))
    return st


# --------------------------------------------------------------- exact gate
def exact_gate(states, L: Q2 | None = None) -> dict:
    """Exact containment + non-overlap on all SAT axes.  No floats anywhere.

    `states` = [(x: Q2, y: Q2, orient: int)].  Returns ok / worst_pen / L.
    """
    n = len(states)
    if L is None:
        lo_x = min(s[0] - EXT[s[2]]["x"] for s in states)
        hi_x = max(s[0] + EXT[s[2]]["x"] for s in states)
        lo_y = min(s[1] - EXT[s[2]]["y"] for s in states)
        hi_y = max(s[1] + EXT[s[2]]["y"] for s in states)
        L = max(hi_x - lo_x, hi_y - lo_y)
    worst = None
    worst_pair = None
    for i in range(n):
        xi, yi, oi = states[i]
        if xi - EXT[oi]["x"] < ZERO or yi - EXT[oi]["y"] < ZERO:
            return {"ok": False, "worst_pen": None, "L": L,
                    "reason": "containment", "pair": (i, None)}
        if xi + EXT[oi]["x"] > L or yi + EXT[oi]["y"] > L:
            return {"ok": False, "worst_pen": None, "L": L,
                    "reason": "containment", "pair": (i, None)}
        for j in range(i + 1, n):
            xj, yj, oj = states[j]
            v = pen_exact(oi, oj, xi - xj, yi - yj)
            if worst is None or v > worst:
                worst, worst_pair = v, (i, j)
    ok = worst is not None and worst <= ZERO
    return {"ok": bool(ok), "worst_pen": float(worst) if worst is not None else None,
            "worst_pen_q": worst.pretty() if worst is not None else None,
            "L": L, "pair": worst_pair}


# ---------------------------------------------------------------- describe
def _code(v: float, L: float):
    """Recover (mode, index) for one coordinate of one upright square."""
    f = v - 0.5
    if abs(f - round(f)) < 1e-6:
        return (0, int(round(f)))
    g = L - 0.5 - v
    if abs(g - round(g)) < 1e-6:
        return (1, int(round(g)))
    h = v - 0.5 * L
    if abs(h - round(h)) < 1e-6:
        return (2, int(round(h)))
    return None


def describe(n: int, per: dict | None = None) -> Atom:
    """Read a delivered row as integers. Raises Refusal if it does not fit."""
    per = SQ.load() if per is None else per
    raw = [tuple(map(float, s)) for s in per[n]]
    L = SQ.extent(raw)
    # the delivered rows are not all corner-anchored (n=626 sits centred on the
    # origin), and the anchor codes are defined in [0, L]^2, so translate first.
    ox = min(x - 0.5 * (abs(math.cos(t)) + abs(math.sin(t))) for x, _, t in raw)
    oy = min(y - 0.5 * (abs(math.cos(t)) + abs(math.sin(t))) for _, y, t in raw)
    st = [(x - ox, y - oy, t) for x, y, t in raw]
    tilt = [s for s in st if abs(s[2] % (math.pi / 2)) > 1e-9]
    axis = []
    undescribed = 0
    for x, y, th in st:
        if abs(th % (math.pi / 2)) > 1e-9:
            continue
        kx, ky = _code(x, L), _code(y, L)
        if kx is None or ky is None:
            undescribed += 1
            continue
        axis.append((kx[0], kx[1], ky[0], ky[1]))
    if undescribed:
        raise Refusal("describe_mismatch",
                      f"n={n}: {undescribed} upright squares are not on a "
                      f"wall/centre anchor")
    p = int(round(math.sqrt(len(tilt))))
    if p * p != len(tilt):
        raise Refusal("describe_mismatch",
                      f"n={n}: {len(tilt)} tilted squares is not a square p^2")
    # lattice check: every tilted centre must be on the exact 45 deg lattice
    s = math.sqrt(0.5)
    cx = sum(q[0] for q in tilt) / len(tilt)
    cy = sum(q[1] for q in tilt) / len(tilt)
    atom0 = Atom(n, p, Fraction(round((cx - 0.5 * L) * 2), 2),
                 Fraction(round((cy - 0.5 * L) * 2), 2), (), L, L - math.isqrt(n))
    lat_err = 0.0
    for x, y, _ in tilt:
        best = None
        for u in range(p):
            for v in range(p):
                qx, qy = tilt_centre(atom0, u, v, L)
                e = max(abs(qx - x), abs(qy - y))
                if best is None or e < best:
                    best = e
        lat_err = max(lat_err, best)
    if lat_err > 1e-6:
        raise Refusal("describe_mismatch",
                      f"n={n}: tilted block is not the 45 deg lattice "
                      f"(max error {lat_err:.2e})")
    atom = Atom(n, p, atom0.dx, atom0.dy, tuple(axis), L, L - math.isqrt(n))
    # rebuild must reproduce the (corner-anchored) row.  The CSV does not store
    # the squares in builder order, so compare as point sets, not by index.
    rb = build(atom, L)
    sa = sorted((round(a[0], 6), round(a[1], 6)) for a in st)
    sb = sorted((round(b[0], 6), round(b[1], 6)) for b in rb)
    if len(sa) != len(sb):
        raise Refusal("describe_mismatch",
                      f"n={n}: rebuild has {len(sb)} squares, row has {len(sa)}")
    err = max(max(abs(p[0] - q[0]), abs(p[1] - q[1])) for p, q in zip(sa, sb))
    if err > 1e-8:
        raise Refusal("describe_mismatch",
                      f"n={n}: rebuild differs by {err:.2e}")

    final = Atom(n, p, atom.dx, atom.dy, tuple(axis), L, atom.delta_del,
                 {"lat_err": lat_err, "rebuild_err": err,
                  "ncols": atom.kcols()})
    final.meta["walls"] = wall_signature(final, L)
    return final


class Refusal(Exception):
    def __init__(self, reason: str, detail: str):
        super().__init__(f"{reason}: {detail}")
        self.reason, self.detail = reason, detail


# ------------------------------------------------------------- the seam LP
def _sqpos(atom: Atom, idx: int):
    """(x0, xL, tx, y0, yL, ty, orient): coordinate = x0 + xL*L + tx*t_x.

    For a tilted square x0 carries the individual lattice offset
    ((u-v), (u+v-p+1)) * sqrt(2)/2 — every tilted square shares the same L and
    translation coefficients, so only x0 distinguishes them.
    """
    p2 = atom.p * atom.p
    if idx < p2:
        u, v = divmod(idx, atom.p)
        s = math.sqrt(0.5)
        return (float(atom.dx) + (u - v) * s, 0.5, 1.0,
                float(atom.dy) + (u + v - atom.p + 1) * s, 0.5, 1.0, 1)
    xm, xi, ym, yi = atom.axis[idx - p2]
    ax0, axL = posfunc(xm, xi)
    ay0, ayL = posfunc(ym, yi)
    return (ax0, axL, 0.0, ay0, ayL, 0.0, 0)


def best_axis_f(oa: int, ob: int, dx: float, dy: float):
    """Float twin of `best_axis`, for choosing the axis of a declared pair.

    The choice is discrete, so float error cannot move it: the second-best axis
    is a whole extent away, not an epsilon.
    """
    best = None
    for ax in AXES_OF[(oa, ob)]:
        ux, uy = float(DIRS[ax][0]), float(DIRS[ax][1])
        pr = dx * ux + dy * uy
        v = float(EXT[oa][ax] + EXT[ob][ax]) - abs(pr)
        if best is None or v < best[0]:
            best = (v, ax, pr)
    return best[1], best[2]


def seam_pairs(atom: Atom, reach: float = 2.2):
    """Every pair that can bind the seam, with its declared axis and sign.

    A pair is declared by the separating axis the delivered state actually uses,
    signed by which side the tilted square lies on.  Pairs further apart than
    `reach` in either coordinate cannot bind within the side we are solving for.
    """
    p2 = atom.p * atom.p
    n = p2 + len(atom.axis)
    pos = []
    for i in range(n):
        x0, xL, _, y0, yL, _, o = _sqpos(atom, i)
        pos.append((x0 + xL * atom.L_del, y0 + yL * atom.L_del, o))
    out = []
    for i in range(n):
        xi, yi, oi = pos[i]
        for j in range(i + 1, n):
            xj, yj, oj = pos[j]
            if abs(xi - xj) > reach or abs(yi - yj) > reach:
                continue
            ax, pr = best_axis_f(oi, oj, xi - xj, yi - yj)
            out.append((i, j, ax, 1 if pr >= 0 else -1))
    return out


def lp_seam(atom: Atom, free: tuple = ("L", "t"), reach: float = 2.2,
            drop_declared: int = 0):
    """Minimise L over (L, tx, ty) subject to the declared seam.  Float solve.

    `free` selects which of the three are variables: ("L",) pins the diamond,
    ("L", "t") lets it translate, () pins everything (a pure feasibility test).
    `drop_declared` removes that many constraints, to test how much of the
    declared seam is load-bearing (a sensitivity probe, never a result).
    """
    from scipy.optimize import linprog

    pairs = seam_pairs(atom, reach)
    if drop_declared:
        pairs = pairs[drop_declared:]
    rows, rhs = [], []
    # The coefficient of L must stay 1 even when L is pinned: pinning belongs in
    # the bounds.  Zeroing it (the first version did) dropped the L term from
    # every row while the bound held L fixed, so the solve evaluated the
    # constraints at L = 0.
    cL = 1.0
    ct = 1.0 if "t" in free else 0.0

    for (i, j, ax, sgn) in pairs:
        oi = _sqpos(atom, i)[6]
        oj = _sqpos(atom, j)[6]
        ux, uy = (float(DIRS[ax][0]), float(DIRS[ax][1]))
        _, xLi, txi, _, yLi, tyi, _ = _sqpos(atom, i)
        _, xLj, txj, _, yLj, tyj, _ = _sqpos(atom, j)
        x0i, y0i = _sqpos(atom, i)[0], _sqpos(atom, i)[3]
        x0j, y0j = _sqpos(atom, j)[0], _sqpos(atom, j)[3]
        es = float(EXT[oi][ax] + EXT[oj][ax])
        dL = (xLi - xLj) * ux + (yLi - yLj) * uy
        dtx = (txi - txj) * ux
        dty = (tyi - tyj) * uy
        cst = (x0i - x0j) * ux + (y0i - y0j) * uy
        # sgn * (cst + L*dL + tx*dtx + ty*dty) >= es
        rows.append([-sgn * cL * dL, -sgn * ct * dtx, -sgn * ct * dty])
        rhs.append(sgn * cst - es)

    # diamond containment: cx + tx +- p*sqrt2/2 inside [0, L]
    h = atom.p * SQ2 / 2.0
    rows += [[-0.5 * cL, -ct, 0.0], [-0.5 * cL, ct, 0.0],
             [-0.5 * cL, 0.0, -ct], [-0.5 * cL, 0.0, ct]]
    rhs += [atom.dx - h, -atom.dx - h, atom.dy - h, -atom.dy - h]

    # the count law, per row and per column.  A GLOBAL bound is wrong here:
    # n=485 interleaves near-wall and far-wall columns along x (x = 5.035 sits
    # inside the near-wall span 0.5..21.5), so the groups only have to separate
    # inside a shared row.  In one row, x_near = 1/2 + i and x_far = L - 1/2 - i'
    # do not overlap iff L >= i + i' + 2, so the row's two maxima are binding.
    from collections import defaultdict
    for key_fun, mo, ix in ((lambda a: (a[2], a[3]), 0, 1),
                            (lambda a: (a[0], a[1]), 2, 3)):
        grp = defaultdict(lambda: ([], []))
        for a in atom.axis:
            grp[key_fun(a)][a[mo] == 1].append(a[ix])
        for key, (lo, hi) in grp.items():
            if lo and hi:
                rows.append([-cL, 0.0, 0.0])
                rhs.append(float(-(max(lo) + max(hi) + 2)))
    # centre-anchored coordinates must stay inside the container: L >= 2i + 1
    for a in atom.axis:
        for mo, ix in ((0, 1), (2, 3)):
            if a[mo] == 2:
                rows.append([-0.5 * cL, 0.0, 0.0])
                rhs.append(-(a[ix] + 0.5))

    bounds = [(0.0, None), (None, None), (None, None)]
    if "L" not in free:
        bounds[0] = (atom.L_del, atom.L_del)
    if "t" not in free:
        bounds[1] = (0.0, 0.0)
        bounds[2] = (0.0, 0.0)
    res = linprog([cL, 0.0, 0.0], A_ub=rows, b_ub=rhs, bounds=bounds,
                  method="highs")
    return {"status": int(res.status), "message": str(res.message)[:120],
            "pairs": len(pairs),
            "L": float(res.x[0]) if res.status == 0 else None,
            "t": (float(res.x[1]), float(res.x[2])) if res.status == 0 else None}


# ------------------------------------------------------------------ snap
def snap(x: float, cmax: int = 220, tol: float = 1e-8) -> Q2:
    """The cheapest (a + b*sqrt2)/c that reproduces `x` to `tol`.

    The tolerance is 1e-8, not machine epsilon, for a measured reason: a
    delivered side carries `packlib.finalize`'s ~2e-9 contact pad, so the stored
    L is 1.8e-9 above the algebraic value it came from (n=65: stored
    8.5355339077, algebraic 5 + 5*sqrt2/2 = 8.5355339059).  Snapping at 1e-12
    would reject the atom's own side.

    Searching b first (not a) matters: 5/sqrt2 - 3 is (-6 + 5*sqrt2)/2, whose
    `a` is nowhere near round(x*c), and b is not bounded by x either — only by
    the height budget.  Cheap = small |a| + |b| + c, so the reported form is the
    one a reader would write, not a high-denominator accident.
    """
    best = None
    for c in range(1, cmax + 1):
        for b in range(-cmax, cmax + 1):
            af = x * c - b * SQ2
            a = round(af)
            if abs(a - af) / c > tol:
                continue
            h = abs(a) + abs(b) + c
            if h > cmax:
                continue
            if best is None or h < best[0]:
                best = (h, Q2(Fraction(a, c), Fraction(b, c)))
    if best is None:
        raise ValueError(f"{x!r} has no Q(sqrt2) snap of height <= {cmax}")
    return best[1]


@dataclass
class Outcome:
    variant: str
    n: int
    outcome: str
    detail: str
    L_lp: float | None = None
    t_lp: tuple | None = None
    L_exact: str | None = None
    L_exact_float: float | None = None
    L_del: float | None = None
    worst_pen: str | None = None
    dscore: float | None = None
    packs: bool | None = None

    def as_dict(self):
        return {k: v for k, v in self.__dict__.items()}


def certify(atom: Atom, L_lp: float, t_lp, variant: str) -> Outcome:
    """Snap the LP nomination to Q(sqrt 2) and replay it exactly."""
    L_q = snap(L_lp)
    tx, ty = Q2(Fraction(round(t_lp[0] * 2), 2)), Q2(Fraction(round(t_lp[1] * 2), 2))
    st = build_q(atom, L_q, (tx, ty))
    g = exact_gate(st, None)
    L_meas = g["L"]
    # the measured side is what the exact state actually occupies
    gain = (atom.L_del - float(L_meas)) / math.sqrt(atom.n)
    oc = Outcome(variant, atom.n, "", "", L_lp=L_lp, t_lp=t_lp,
                 L_exact=L_meas.pretty(), L_exact_float=float(L_meas),
                 L_del=atom.L_del, worst_pen=g.get("worst_pen_q"),
                 dscore=gain if float(L_meas) < atom.L_del - 1e-12 else 0.0,
                 packs=bool(g["ok"]))
    if not g["ok"]:
        # A rounded candidate failing is not an infeasibility proof: the LP
        # allows continuous translations, so try the eight half-step
        # neighbours before rejecting.
        best = None
        for ddx in (-0.5, 0.0, 0.5):
            for ddy in (-0.5, 0.0, 0.5):
                if ddx == 0.0 and ddy == 0.0:
                    continue
                tx2 = Q2(Fraction(round((t_lp[0] + ddx) * 2), 2))
                ty2 = Q2(Fraction(round((t_lp[1] + ddy) * 2), 2))
                g2 = exact_gate(build_q(atom, L_q, (tx2, ty2)), None)
                if g2["ok"] and (best is None or float(g2["L"]) < float(best[1]["L"])):
                    best = ((tx2, ty2), g2)
        if best is None:
            oc.outcome, oc.detail = "candidate_rejected_exact", (
                f"snapped point {L_meas.pretty()} fails the exact gate "
                f"({g.get('reason', 'penetration')} {g.get('worst_pen_q')}), and so "
                "do its eight half-step neighbours — the LP nomination is not "
                "certifiable, the layout is not thereby proved impossible")
            return oc
        (tx, ty), g = best
        L_meas = g["L"]
        gain = (atom.L_del - float(L_meas)) / math.sqrt(atom.n)
        oc = Outcome(variant, atom.n, "", "", L_lp=L_lp, t_lp=t_lp,
                     L_exact=L_meas.pretty(), L_exact_float=float(L_meas),
                     L_del=atom.L_del, worst_pen=g.get("worst_pen_q"),
                     packs=True)
    pad = atom.L_del - float(L_meas)
    if pad < GAIN_MIN:
        oc.outcome, oc.detail = "feasible_no_gain", (
            f"certified at {float(L_meas):.9f}; delivered {atom.L_del:.9f} is "
            f"that side + {pad:+.1e} (the finalizer pad)"
            if abs(pad) <= PAD * 5 else
            f"certified at {float(L_meas):.9f} vs delivered {atom.L_del:.9f}")
        oc.dscore = 0.0
        return oc
    # a strict improvement in the solved model still has to be a real packing
    fp_st, fp = P.finalize([(float(x), float(y), math.pi / 4 if o else 0.0)
                            for x, y, o in st])
    if not fp["ok"]:
        oc.outcome, oc.detail = "numerically_inconclusive", (
            "Q(sqrt2) state passes the exact gate but packlib rejects the float "
            f"replay (worst_pen {fp['worst_pen']:+.2e})")
        return oc
    # A scored gain uses the FINALIZED replay's canonical score, not the
    # unpadded exact side: packlib's extent is what the scorer reads.
    oc.dscore = (SQ.row_gain(atom.n, SQ.extent(fp_st))
                 - SQ.row_gain(atom.n, atom.L_del))
    oc.outcome, oc.detail = "feasible_gain", (
        f"certified at {float(L_meas):.9f} < delivered {atom.L_del:.9f}; "
        f"finalized L={SQ.extent(fp_st):.9f}, dscore={oc.dscore:+.6e}")
    return oc


# ---------------------------------------------------------------- variants
def _flip(mode: int, idx: int):
    """near wall <-> far wall; a centre anchor has no mirror and stays put."""
    return (1 - mode, idx) if mode in (0, 1) else (mode, idx)


def variant_mirror(atom: Atom) -> Atom:
    """Swap every near-wall anchor for the far wall and reflect the diamond."""
    ax = tuple(_flip(a[0], a[1]) + _flip(a[2], a[3]) for a in atom.axis)
    return Atom(atom.n, atom.p, -atom.dx, -atom.dy, ax, atom.L_del,
                atom.delta_del, atom.meta)


def variant_seam_turn(atom: Atom) -> Atom:
    """Turn the seam: reflect the upright anchors on one axis only.

    This is the structural choice the review asked to vary — which wall the
    block anchors to — applied to x alone, so the two 45 deg seams are no longer
    congruent.
    """
    ax = tuple(_flip(a[0], a[1]) + (a[2], a[3]) for a in atom.axis)
    return Atom(atom.n, atom.p, atom.dx, atom.dy, ax, atom.L_del,
                atom.delta_del, atom.meta)


def variant_partial(atom: Atom, where: str = "fullest") -> Atom:
    """Move one upright square to the emptiest row: where a partial row ends.

    Same count, same anchors — only the end of one partial row moves.  This is
    the third structural choice in the review's list.  `where` picks the square
    to move: the fullest column ("fullest") or the column standing against the
    45 deg seam ("seam"), which is the square whose removal widens the staircase.
    """
    from collections import Counter
    cnt = Counter(atom.axis)
    if not cnt:
        return atom
    # the emptiest row (fewest squares at that y-anchor) and the fullest
    rows = Counter((a[2], a[3]) for a in atom.axis)
    empt = min(rows, key=lambda r: (rows[r], r))
    full = max(rows, key=lambda r: (rows[r], r))
    cols = Counter(a[1] for a in atom.axis if a[0] == 0)
    src = None
    if where == "seam":
        # the near-wall column with the smallest index is the one nearest the
        # diamond; its topmost square is the end of the staircase
        best = None
        for a in atom.axis:
            if a[0] != 0:
                continue
            key = (a[1], -a[3])
            if best is None or key < best[0]:
                best = (key, a)
        src = best[1] if best else None
    for a in atom.axis if src is None else ():
        if (a[2], a[3]) == full and a[0] == 0 and cols[a[1]] == max(cols.values()):
            src = a
            break
    if src is None:
        return atom
    dst = None
    for i in range(0, 40):
        cand = (src[0], i, empt[0], empt[1])
        if cand not in cnt:
            dst = cand
            break
    if dst is None:
        return atom
    new = list(atom.axis)
    new.remove(src)
    new.append(dst)
    return Atom(atom.n, atom.p, atom.dx, atom.dy, tuple(new), atom.L_del,
                atom.delta_del, atom.meta)


# ------------------------------------------------------------------- bound
def bound_karakus(N: int):
    """s(N) >= 1/2 + sqrt(N - floor(sqrt N) + 1/4) for nonsquare N >= 8."""
    k = math.isqrt(N)
    if N == k * k or N < 8:
        return None
    return 0.5 + math.sqrt(N - k + 0.25)


def bound_slack_floor(n: int):
    """The smallest slack delta = L - floor(sqrt n) the bound permits."""
    b = bound_karakus(n)
    if b is None:
        return None
    return b - math.isqrt(n)


# ------------------------------------------------------------- the cascade
def cascade_rank(per: dict | None = None) -> dict:
    """What a better base would actually be worth, column by column.

    `(r, delta)` is the cascade invariant: a base with slack delta at k0 sits at
    L = k + delta on every row of its column.  So the payoff of one base is the
    gain of that ONE base replayed to the end of its column — not the sum over
    every (base, row) pair, which would count each row once per base and inflate
    the number by the column length (the first version of this function did
    exactly that, and reported 0.731635 for r = 1).

      now         per legal start k0, with THAT row's own delivered slack d0 and
                  propagating FORWARD only (k >= k0):
                  sum (L_k - (k + d0))/sqrt(n_k).  The maximum over starts.
                  A column-wide best slack replayed at the bottom row would be
                  the same backwards step that prices a base on rows it cannot
                  reach; this version cannot do it.
      optimistic  the same per-start sum with d0 replaced by the Karakus floor
                  at k0 — a lower bound on any base's slack there, so this is
                  an UPPER bound on what a new base at that start would pay
      rows        the rows the base would touch
    """
    per = SQ.load() if per is None else per
    out = {}
    for r in range(1, 9):
        rows = []
        for k in range(2, 32):
            n = k * k + r
            if n > MAX_N or n not in per:
                continue
            # A row belongs to THIS column only if n = k^2 + r is its residue
            # class: k^2 + 6 at k = 2 is n = 10, a residue-1 row, and counting
            # it here gave r = 6 a fictitious base at k = 2.
            if n - math.isqrt(n) ** 2 != r:
                continue
            # Keep grid rows: a base at k0 lifts every row above it whether or
            # not that row currently beats.  Filtering to beating rows here was
            # the same error that once inflated r = 1 by the column length.
            rows.append((k, n, SQ.extent(per[n])))
        if len(rows) < 2:
            continue
        # Price EVERY legal start with THAT row's own slack, propagating forward
        # only.  Using the column-wide minimum slack at the bottom row (the
        # previous version) replays a base backwards to rows its source cannot
        # reach: the base's delta is a function of its own k, not a free
        # constant to move down the column.  Take the best start.
        best_now = best_opt = None
        d_best, k_best = min((L - k, k) for (k, n, L) in rows)
        for (k0, n0, L0) in rows:
            d0 = L0 - k0
            now = sum(max(0.0, (L - (k + d0)) / math.sqrt(n))
                      for (k, n, L) in rows if k >= k0)
            if best_now is None or now > best_now[0]:
                best_now = (now, k0, n0, d0)
            f0 = bound_slack_floor(n0)
            if f0 is not None:
                opt = sum(max(0.0, (L - (k + f0)) / math.sqrt(n))
                          for (k, n, L) in rows if k >= k0)
                if best_opt is None or opt > best_opt[0]:
                    best_opt = (opt, k0, n0, f0)
        out[f"r{r}"] = {"rows": [r0[2] for r0 in rows], "k_lo": rows[0][0],
                        "k_hi": rows[-1][0], "delta_best": d_best,
                        "k_of_best": k_best, "base_k": best_now[1],
                        "base_n": best_now[2], "base_slack": best_now[3],
                        "slack_floor_at_base": best_opt[3] if best_opt else None,
                        "gain_now": best_now[0],
                        "gain_optimistic": best_opt[0] if best_opt else None,
                        "opt_base_k": best_opt[1] if best_opt else None,
                        "starts_priced": len(rows),
                        "n_rows_touched": len([1 for (k, _, _) in rows
                                                if k >= best_now[1]])}
    return out


# -------------------------------------------------------------------- main
def reconstruct_row(n: int, per: dict) -> list[Outcome]:
    """Describe, rebuild, then solve the seam three ways and certify each."""
    try:
        atom = describe(n, per)
    except Refusal as e:
        return [Outcome("describe", n, "layout_not_enumerated", e.detail)]
    outs = []
    # rebuild is a fact, not a claim: the float state must gate.  `finalize`
    # opens the exact contacts by 2e-9, which is what the CSV needs.
    st = build(atom, atom.L_del)
    st_fin, rb = P.finalize(st)
    if not rb["ok"] or abs(rb["L"] - atom.L_del) > 1e-8:
        return [Outcome("rebuild", n, "layout_not_enumerated",
                        f"rebuilt state does not gate (ok={rb['ok']}, "
                        f"L={rb['L']:.9f} vs {atom.L_del:.9f})")]
    variants = [("declared seam (diamond pinned)", atom, ("L",)),
                ("declared seam (diamond free)", atom, ("L", "t")),
                ("mirrored", variant_mirror(atom), ("L", "t")),
                ("seam turned (x only)", variant_seam_turn(atom), ("L", "t")),
                ("partial row moved (fullest)", variant_partial(atom), ("L", "t")),
                ("partial row moved (seam)", variant_partial(atom, "seam"),
                 ("L", "t"))]
    for name, a, free in variants:
        lp = lp_seam(a, free=free)
        if lp["status"] != 0:
            outs.append(Outcome(name, n, "lp_infeasible",
                                f"LP status {lp['status']}, {lp['pairs']} pairs"))
            continue
        outs.append(certify(a, lp["L"], lp["t"], name))
    return outs


def baseless_rank(per: dict | None = None, residues=range(38, 61)):
    """Rank the base-less columns by what opening one would pay.

    A residue r is base-less when no row of it beats the grid.  The rows sit at
    L = grid = k + 1, so the payoff of a base at k0 with slack delta is
        sum over rows k >= k0 of (grid_k - (k + delta)) / sqrt(n_k).
    `delta` is taken at the Karakus floor of the FIRST row the bound permits to
    beat anything: that is an optimistic lower bound on any base's slack, so the
    number is an upper bound on the column, not a forecast.

    Two things this makes visible: (1) a row with r = 2k is exactly n = (k+1)^2-1,
    where the bound equals the grid, so it can never beat and is skipped as a
    base; (2) residues 38-60 first appear at k = r-... so the base is deep in the
    column and only the rows above it are reachable.
    """
    per = SQ.load() if per is None else per
    out = {}
    for r in residues:
        rows = []
        for k in range(2, 32):
            n = k * k + r
            if n > MAX_N or n not in per or n - math.isqrt(n) ** 2 != r:
                continue
            L = SQ.extent(per[n])
            rows.append((k, n, L, SQ.grid(n), SQ.is_beat(n, L)))
        if not rows:
            continue
        # Price EVERY legal start, propagating forward only, and take the best.
        # The first version priced only the first eligible base; a later base
        # reaches fewer rows but can start at a lower slack floor, so that was
        # an estimate for one start, not a cap on the residue.
        best = None
        for (k, n, L, g, beat) in rows:
            f = bound_slack_floor(n)
            if f is None or not (k + f < g - 1e-9):
                continue
            up = sum(max(0.0, (gj - (kj + f)) / math.sqrt(nj))
                     for (kj, nj, _, gj, _b) in rows if kj >= k)
            if best is None or up > best["upside"]:
                best = {"k0": k, "first_n": n, "slack_floor": f, "upside": up,
                        "rows_reachable": sum(1 for (kj, _, _, _, _) in rows
                                              if kj >= k)}
        if best is None:
            out[f"r{r}"] = {"rows": len(rows), "upside": 0.0,
                            "note": "the bound already equals the grid on every row"}
            continue
        best.update({"rows": len(rows),
                     "already_beating": sum(1 for x in rows if x[4]),
                     "starts_priced": sum(1 for (k, n, _, g, _b) in rows
                                          if (bound_slack_floor(n) or 9) < g - 1e-9)})
        out[f"r{r}"] = best
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()
    s = SQ.guard()
    print(f"[sqscore] delivered: {s['score']:.9f}, {s['beats']} beats, "
          f"{s['rows']} rows")
    if args.selftest:
        return selftest()

    per = SQ.load()
    t0 = time.time()
    rows = [65, 82, 101, 122, 145, 170, 197, 226, 257, 290, 325, 362, 401,
            442, 485, 530, 577, 626]
    results = []
    print(f"\n{'n':>4} {'variant':28s} {'outcome':24s} L")
    for n in rows:
        if n not in per:
            continue
        try:
            atom = describe(n, per)
            w = atom.meta.get("walls")
            print(f"\n-- n={n}: p={atom.p} cols={atom.kcols()} "
                  f"delta={atom.delta_del:.9f} walls={w}")
        except Refusal as e:
            print(f"\n-- n={n}: {e.reason}: {e.detail}")
        for oc in reconstruct_row(n, per):
            results.append(oc.as_dict())
            print(f"{n:4d} {oc.variant:28s} {oc.outcome:24s} "
                  f"{'' if oc.L_exact_float is None else f'{oc.L_exact_float:.9f}'}"
                  f"{'' if not oc.detail else '  ' + oc.detail[:70]}")

    rank = cascade_rank(per)
    print("\ncolumn value if a base existed (cascade to the end of the column):")
    print(f"  {'col':>4} {'rows':>5} {'k':>6} {'delta*':>9} {'gain now':>10} "
          f"{'optimistic':>11} {'floor@first':>12}")
    for key in sorted(rank, key=lambda z: float(z[1:])):
        d = rank[key]
        print(f"  {key:>4} {len(d['rows']):5d} {d['k_lo']:3d}-{d['k_hi']:<3d} "
              f"{d['delta_best']:9.6f} {d['gain_now']:10.6f} "
              f"{(d['gain_optimistic'] if d['gain_optimistic'] is not None else float('nan')):11.6f} "
              f"{(d['slack_floor_at_base'] if d['slack_floor_at_base'] is not None else float('nan')):12.6f}")

    bl = baseless_rank(per)
    print("\nbase-less columns r = 38..60, ranked by the upside of ONE base:")
    print(f"  {'col':>4} {'rows':>5} {'first n':>8} {'reach':>6} {'slack*':>8} {'upside':>8}")
    for key in sorted(bl, key=lambda z: -bl[z]["upside"]):
        d = bl[key]
        if "first_n" not in d:
            print(f"  {key:>4} {d['rows']:5d}   -- {d['note']}")
            continue
        print(f"  {key:>4} {d['rows']:5d} {d['first_n']:8d} {d['rows_reachable']:6d} "
              f"{d['slack_floor']:8.6f} {d['upside']:8.6f}")
    best = max((d for d in bl.values() if "first_n" in d),
               key=lambda d: d["upside"], default=None)
    if best:
        print(f"  highest upside: {best['upside']:.6f} at r="
              f"{next(k for k in bl if bl[k] is best)[1:]}")

    # the negative control, from the theorem
    ctrl = []
    for K in range(3, 32):
        n = K * K - 1
        if n in per:
            L = SQ.extent(per[n])
            ctrl.append({"K": K, "n": n, "L": L, "beats": SQ.is_beat(n, L)})
    bad = [c for c in ctrl if c["beats"]]
    print(f"\nnegative control s(k^2-1)=k: {len(ctrl)} rows, {len(bad)} claim a "
          f"beat" + ("" if not bad else f" -> {bad}"))

    led = {"run": 53, "schema": "seam-wheels/1",
           "written": time.strftime("%Y-%m-%d %H:%M:%S"),
           "seconds": round(time.time() - t0, 1),
           "rows": results, "cascade": rank, "base_less": bl,
           "control_k2m1": {"rows": len(ctrl), "violations": len(bad)},
           "outcomes": {k: sum(1 for r in results if r["outcome"] == k)
                        for k in sorted({r["outcome"] for r in results})}}
    if not args.no_write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w") as f:
            json.dump(led, f, indent=1)
        print(f"\nledger: {OUT}")
    return 0


def selftest() -> int:
    checks = []

    def ck(name, cond, extra=""):
        checks.append(bool(cond))
        print(f"  {'ok ' if cond else 'FAIL'} {name:34s} {extra}")

    # ---- the field
    ck("Q2 (sqrt2/2)^2 = 1/2", R2H * R2H == HALF)
    ck("Q2 sqrt2 * sqrt2 = 2", Q2(0, 1) * Q2(0, 1) == Q2(2))
    ck("Q2 order 1.4142 < sqrt2",
       Q2(Fraction(14142, 10000)) < Q2(0, 1))
    ck("Q2 order sqrt2 < 1.4143",
       Q2(0, 1) < Q2(Fraction(14143, 10000)))
    ck("Q2 negated order", Q2(0, -1) < Q2(Fraction(-14142, 10000)))
    ck("Q2 mixed sign (1 - 2sqrt2) < 0", (ONE - Q2(0, 2)) < ZERO)
    ck("Q2 exact equality (sqrt2/2)^2 = 1/2",
       R2H * R2H == HALF)
    ck("snap recovers 5/sqrt2 - 3 exactly",
       snap(5 / SQ2 - 3) == Q2(-3, Fraction(5, 2)),
       snap(5 / SQ2 - 3).pretty())
    ck("snap recovers 17/sqrt2 - 23/2 exactly",
       snap(17 / SQ2 - 23 / 2) == Q2(Fraction(-23, 2), Fraction(17, 2)),
       snap(17 / SQ2 - 23 / 2).pretty())
    ck("snap tolerates the 2e-9 contact pad",
       snap(5 + 5 * SQ2 / 2 + 1.8e-9) == Q2(5, Fraction(5, 2)),
       f"padded -> {snap(5 + 5 * SQ2 / 2 + 1.8e-9).pretty()}")

    # ---- the two atoms, declared and rebuilt
    per = SQ.load()
    for n, want in ((65, 5 / SQ2 - 3), (626, 17 / SQ2 - 23 / 2)):
        atom = describe(n, per)
        ok = abs(atom.delta_del - want) < 2e-9
        ck(f"n={n} delta reconstructs {want:.9f}", ok,
           f"delta {atom.delta_del:.9f} p={atom.p} cols={atom.kcols()}")
        st = build(atom, atom.L_del)
        st_fin, r = P.finalize(st)
        ck(f"n={n} rebuilt state gates", r["ok"] and len(st) == n,
           f"L={r['L']:.9f} worst_pen={r['worst_pen']:+.1e}")
        # exact replay of the delivered side, snapped
        g = exact_gate(build_q(atom, snap(atom.L_del)), None)
        ck(f"n={n} exact gate on snapped side", g["ok"],
           f"L={g['L'].pretty()} pen={g['worst_pen_q']}")

    # ---- the LP must not invent a smaller side than the declaration allows
    atom = describe(65, per)
    lp = lp_seam(atom, free=("L", "t"))
    ck("LP n=65 does not beat the delivered row", lp["status"] == 0
       and lp["L"] >= atom.L_del - 1e-6,
       f"LP L={lp['L']:.9f} vs {atom.L_del:.9f}")

    # ---- the bound and the control
    ck("Karakus bound is exact at k^2-1",
       abs(bound_karakus(63) - 8.0) < 1e-12, f"{bound_karakus(63):.9f}")
    ck("Karakus bound beats the area bound",
       all(bound_karakus(N) > math.sqrt(N) + 1e-9
           for N in (15, 63, 65, 200, 999)),
       "checked 5 nonsquares")
    bad = [K for K in range(3, 32)
           if K * K - 1 in per and SQ.is_beat(K * K - 1, SQ.extent(per[K * K - 1]))]
    ck("control: no k^2-1 row beats k", not bad, f"{len(bad)} violations")
    print(f"\nselftest: {sum(checks)}/{len(checks)} checks pass")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
