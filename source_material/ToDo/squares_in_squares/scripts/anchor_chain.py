#!/usr/bin/env python3
r"""anchor_chain.py — run 117/118: square placements as backward-linked anchor
commands, under the GLM's own three-column step contract; and a forward,
goal-directed anchor-admission search.

WHY THIS EXISTS.  ``glm_universal.reasoning.stepwise_script`` is the stepwise
planner's chain format: every step is *admitted* by a gate (``step_check``) that
reads column 1 (a sentence) and column 2 (an exact equation) back with its own
readers, requires every input to be an earlier step, and recomputes a computed
value exactly.  This module asks whether a packing can be written in that form,
and then whether the same grammar can *build* one forwards.

THE BRIDGE, STATED HONESTLY.  A GLM ``Step`` value is a ``Fraction`` (or a
verdict string); the exact coordinates of a rotated square lie in a real
quadratic field.  So the split is:

* the **Step** carries the command as column 1, the same command as the equation
  in column 2, the number of cells placed as its exact value, and the anchor's
  full description in ``detail``.  ``step_check`` verifies the columns, the
  backward links and the count;
* the **anchor gate** below verifies the geometry, exactly, in ``Q(sqrt d)``
  (``exact_field.Quad``): no overlap against every earlier cell, every declared
  contact tangent with slack *exactly* zero, every declared wall edge *exactly*
  on the container, and every required cell an earlier one.

Neither check substitutes for the other, and nothing here is a float.

TWO FIELDS.  n = 10 lives in Q(sqrt 2) (the proved optimum ``3 + 1/2 sqrt2``,
doc 24); n = 18 is the Ring row in **Q(sqrt 7)** (``7/2 + 1/2 sqrt7``, docs
56-57), whose eight rotated cells use ``cos = (1 + sqrt7)/4``,
``sin = (sqrt7 - 1)/4``.  The command grammar is the same in both — which is the
point of running the second one.

FORWARD SETTLING.  ``settle`` runs the grammar at a given target side L:
it admits ANCHOR_CORNER / STACK_BLOCK / PROPAGATE_SLIDE steps only when both
gates pass at clearance >= 0, and backtracks on the exact overlap refusals.  A
cell is an admissible *determined* anchor when it is tangent to a placed cell and
closed by a wall or by a second contact — the three commands, and nothing else.
"""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal, getcontext
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "..", "..", "..", "src"))

import exact_field as EF                                          # noqa: E402

try:
    from glm_universal.reasoning import stepwise_script as SS
except Exception:                                                 # pragma: no cover
    SS = None

TAB = os.path.join(ROOT, "workspace/submission/table.json")
OUT = os.path.join(ROOT, "workspace/push/anchor_chain117.json")
OUT18 = os.path.join(ROOT, "workspace/push/anchor_chain118.json")
OUTFWD = os.path.join(ROOT, "workspace/push/anchor_forward118.json")

#: The tolerance a decimal string is snapped with — a *reading*, not a result.
SNAP = F(1, 10 ** 6)


class Field:
    """A real quadratic field Q(sqrt d) with a declared direction menu."""

    def __init__(self, d, name, dirs, angles, denoms=(4, 8, 16, 32)):
        self.d, self.name = d, name
        self.denoms = denoms
        self.cls = type(f"Q{d}", (EF.Quad,), {"d": d})
        self.dirs = {}
        for k, ((ca, cb), (sa, sb)) in dirs.items():
            self.dirs[k] = (self.q(ca, cb), self.q(sa, sb))
        self.angles = {k: [F(v) for v in vs] for k, vs in angles.items()}
        self.zero, self.one = self.q(0), self.q(1)

    def q(self, a, b=0):
        return self.cls(F(a), F(b))


#: The two fields this project's exact rows live in, with the decimals their
#: directions are *read* from (radians, as the table stores them).
FIELDS = {
    2: Field(2, "Q(sqrt 2)",
             {"axis": ((1, 0), (0, 0)), "diag": ((0, F(1, 2)), (0, F(1, 2)))},
             {"axis": ["0.0", "1.5707963267948966"],
              "diag": ["0.7853981633974483"]}),
    7: Field(7, "Q(sqrt 7)",
             {"axis": ((1, 0), (0, 0)),
              "ring": ((F(1, 4), F(1, 4)), (F(-1, 4), F(1, 4)))},
             {"axis": ["0.0", "1.570796326795"],
              "ring": ["0.424031039491"]}),
}


class Refusal(Exception):
    """An anchor the gate does not admit."""


# ---------------------------------------------------------------------------
# 1.  EXACT GEOMETRY IN Q(sqrt d)
# ---------------------------------------------------------------------------
def half_along(cell, axis):
    """The half-width of a cell along an axis: (|c.qx + s.qy| + |-s.qx + c.qy|)/2."""
    c, s = cell["c"], cell["s"]
    qx, qy = axis
    return (abs(c * qx + s * qy) + abs(-s * qx + c * qy)) * F(1, 2)


def axes(cell):
    """The two edge normals of a cell — enough for the separating-axis test."""
    c, s = cell["c"], cell["s"]
    return ((c, s), (-s, c))


def slack(a, b):
    """Exact SAT slack between two cells: > 0 apart, 0 tangent, < 0 overlapping."""
    dx, dy = b["x"] - a["x"], b["y"] - a["y"]
    best = None
    for q in axes(a) + axes(b):
        proj = dx * q[0] + dy * q[1]
        sl = abs(proj) - half_along(a, q) - half_along(b, q)
        if best is None or sl > best:
            best = sl
    return best


def cell_h(cell):
    """The bounding-box half-width of a cell."""
    return half_along(cell, (cell["one"], cell["zero"]))


def wall_slacks(cell, lo, side):
    """The four exact gaps from a cell's bounding box to the container walls."""
    h = cell_h(cell)
    hi = lo + side
    return (cell["x"] - h - lo, hi - (cell["x"] + h),
            cell["y"] - h - lo, hi - (cell["y"] + h))


def bbox(cells):
    """(lo, side) of a set of cells, exactly: the container they define."""
    los, his = [], []
    for c in cells:
        h = cell_h(c)
        los.append(min(c["x"] - h, c["y"] - h))
        his.append(max(c["x"] + h, c["y"] + h))
    lo, hi = min(los), max(his)
    return lo, hi - lo


def overlaps(cells):
    """Every pair with negative exact slack, deepest first."""
    out = []
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            sl = slack(cells[i], cells[j])
            if sl < 0:
                out.append((i, j, sl))
    out.sort(key=lambda t: t[2])
    return out


# ---------------------------------------------------------------------------
# 2.  READING A DELIVERED ROW EXACTLY
# ---------------------------------------------------------------------------
def load_raw(n):
    """The pose's decimal strings, exactly — ``parse_float=str`` keeps the text,
    so no binary float is ever constructed."""
    with open(TAB) as f:
        tab = json.load(f, **{"parse_float": str})
    rec = tab[str(n)]
    return str(rec["L"]), [(str(r[0]), str(r[1]), str(r[2])) for r in rec["state"]]


def direction_of(field, angle_text):
    """Classify a cell's direction by exact rational comparison with the field's
    declared decimals."""
    a = F(angle_text)
    best = None
    for name, vals in field.angles.items():
        for v in vals:
            err = abs(a - v)
            if best is None or err < best[0]:
                best = (err, name)
    if best[0] > SNAP:
        raise Refusal(f"angle {angle_text} is not in {field.name}'s direction set")
    return best[1]


def snap(field, text, places=50):
    """The exact ``(a + b sqrt d)/q`` nearest a decimal string, or a refusal.

    The decimal is read at 50 places (``Decimal``, not a binary float) and the
    nearest field element with a denominator in the field's declared set is
    recovered; the error is then measured *exactly* in the field.  The reported
    pose is always an exact field element — nothing downstream sees the decimal.
    """
    getcontext().prec = places
    want = F(text)
    v = Decimal(text)
    root = Decimal(field.d).sqrt()
    best = None
    for q in field.denoms:
        for b in range(-8 * q, 8 * q + 1):
            approx = v * q - b * root
            a0 = int(approx.to_integral_value())
            for a in (a0, a0 + 1, a0 - 1):
                cand = field.q(F(a, q), F(b, q))
                err = abs(cand - want)
                if best is None or err < best[0]:
                    best = (err, cand)
    if best[0] > SNAP:
        raise Refusal(f"{text} is not within {SNAP} of a {field.name} lattice value")
    return best[1], best[0]


def exact_cells(n, field=None):
    """Snap a delivered pose to exact cells; report the worst read."""
    L_text, rows = load_raw(n)
    if field is None:
        for cand in FIELDS.values():
            try:
                cells, worst = _snap_all(cand, rows)
            except Refusal:
                continue
            return cells, F(L_text), worst, cand
        raise Refusal(f"n = {n}: no declared field covers this pose")
    cells, worst = _snap_all(field, rows)
    return cells, F(L_text), worst, field


def _snap_all(field, rows):
    cells, worst = [], F(0)
    for i, (xs, ys, ts) in enumerate(rows):
        x, ex = snap(field, xs)
        y, ey = snap(field, ys)
        worst = max(worst, ex, ey)
        name = direction_of(field, ts)
        c, s = field.dirs[name]
        cells.append({"i": i, "x": x, "y": y, "c": c, "s": s, "dir": name,
                      "one": field.one, "zero": field.zero})
    return cells, worst


# ---------------------------------------------------------------------------
# 3.  THE ANCHOR COMMANDS
# ---------------------------------------------------------------------------
def contact_parents(cell, placed):
    return [p["i"] for p in placed if slack(p, cell) == 0]


def wall_contacts(cell, lo, side):
    """The named walls a cell's bounding box sits exactly on."""
    names = ("left", "right", "bottom", "top")
    return [nm for nm, sl in zip(names, wall_slacks(cell, lo, side)) if sl == 0]


def command_for(cell, placed, lo, side):
    """Which anchor command places this cell, from its exact constraints."""
    par = contact_parents(cell, placed)
    walls = wall_contacts(cell, lo, side)
    if len(walls) >= 2 and not par:
        return "ANCHOR_CORNER", ()
    if par and walls:
        return "PROPAGATE_SLIDE", (par[0],)
    if par:
        return "STACK_BLOCK", tuple(par[:2])
    raise Refusal(f"cell {cell['i']} touches no wall and no placed cell")


def order_cells(cells, lo, side):
    """A placement order: corner anchors first, then wall+contact, then contacts."""
    placed, order, todo = [], [], list(cells)
    while todo:
        pick = None
        for c in todo:
            par = contact_parents(c, placed)
            walls = wall_contacts(c, lo, side)
            key = (0 if (len(walls) >= 2 and not par) else
                   1 if (par and walls) else 2 if len(par) >= 2 else 3)
            if key < 3 and (pick is None or key < pick[0]):
                pick = (key, c)
        if pick is None:
            raise Refusal("no admitted anchor for the remaining cells: "
                          + ", ".join(str(c["i"]) for c in todo))
        c = pick[1]
        order.append(c)
        placed.append(c)
        todo.remove(c)
    return order


# ---------------------------------------------------------------------------
# 4.  THE CHAIN — one Step per anchor, admitted only when both gates pass
# ---------------------------------------------------------------------------
def anchor_step(k, cmd, parents, cell, lo, side, placed, field):
    """The Step for one anchor: the command in both columns, the count as its
    exact value, the anchor itself in ``detail``."""
    name = f"{cmd}#{cell['i']}"
    detail = {
        "name": name,
        "anchor": {
            "command": cmd, "cell": cell["i"], "dir": cell["dir"],
            "field": field.name,
            "x": [cell["x"].a, cell["x"].b], "y": [cell["y"].a, cell["y"].b],
            "requires": [p + 1 for p in parents],
            "contacts": [[p["i"], str(slack(p, cell))] for p in placed
                         if slack(p, cell) == 0],
            "walls": wall_contacts(cell, lo, side),
            "inside": all(s >= 0 for s in wall_slacks(cell, lo, side)),
        },
    }
    if SS is None:
        raise Refusal("glm_universal.reasoning.stepwise_script is not importable")
    return SS.Step(index=k, op="given", inputs=(), value=F(k),
                   label=f"{cmd} places cell {cell['i']} ({cell['dir']})",
                   detail=detail)


def anchor_gate(step, steps, cells_by_step, lo, side, eps=F(0)):
    """Admit an anchor: the GLM gate *and* the exact placement.

    ``eps`` is the clearance asked of every earlier cell: 0 for a transcript
    (contact is legal), >= 0 always — the gate never admits an overlap.
    """
    if SS is None:
        return False, "no GLM step contract to check against"
    ok, why = SS.step_check(step, steps)
    if not ok:
        return False, f"step_check refused: {why}"
    a = step.detail["anchor"]
    k = step.index
    for r in a["requires"]:
        if r < 1 or r >= k:
            return False, f"requirement {r} is not an earlier step"
    if not a["inside"]:
        return False, "the cell is not inside the container"
    cell = cells_by_step[(k, "cell")]
    prefix = cells_by_step[(k, "prefix")]
    for j, cellj in prefix:
        sl = slack(cellj, cell)
        if sl < eps or sl < 0:
            return False, f"overlap with cell {j}: exact slack {sl}"
    for j, want in a["contacts"]:
        hit = [p for cid, p in prefix if cid == j]
        if not hit:
            return False, f"contact with cell {j}, which is not an earlier step"
        sl = slack(hit[0], cell)
        if sl != F(want):
            return False, f"contact with cell {j} reads {sl}, not {want}"
    for nm in a["walls"]:
        if nm not in wall_contacts(cell, lo, side):
            return False, f"the {nm} wall edge is not exactly on the container"
    return True, "step_check + exact placement (no overlap, closure exact)"


def build(n, field=None):
    """Reconstruct an exact row as a chain of admitted anchor commands."""
    cells, L_text, worst, field = exact_cells(n, field)
    lo, side = bbox(cells)
    order = order_cells(cells, lo, side)
    steps, geo, notes = [], {}, []
    placed = []
    for k, cell in enumerate(order, start=1):
        cmd, par_idx = command_for(cell, placed, lo, side)
        parents = [n for n, p in enumerate(placed) if p["i"] in par_idx]
        step = anchor_step(k, cmd, parents, cell, lo, side, placed, field)
        geo[(k, "cell")] = cell
        geo[(k, "prefix")] = [(p["i"], p) for p in placed]
        steps.append(step)
        ok, why = anchor_gate(step, steps, geo, lo, side)
        notes.append({"step": k, "command": cmd, "cell": cell["i"],
                      "admitted": ok, "why": why})
        if not ok:
            raise Refusal(f"step {k} ({cmd}) refused: {why}")
        placed.append(cell)
    chain = None
    if SS is not None:
        chain = SS.Chain(question=f"reconstruct the exact n = {n} pose",
                         steps=tuple(steps), kind="narrative",
                         notes=(f"anchor commands, exact in {field.name}",))
        ok, chain_notes = SS.chain_check(chain)
        if not ok:
            raise Refusal("chain_check refused: " + "; ".join(chain_notes))
    return {"n": n, "field": field.name, "chain": chain, "cells": cells,
            "order": order, "lo": lo, "side": side, "L_text": L_text,
            "worst_read": worst, "notes": notes, "violations": overlaps(cells)}


# ---------------------------------------------------------------------------
# 5.  FORWARD SETTLING — the grammar as a goal-directed constructor
# ---------------------------------------------------------------------------
def half_w(cell):
    return cell_h(cell)


def place(field, x, y, dirname):
    c, s = field.dirs[dirname]
    return {"i": -1, "x": x, "y": y, "c": c, "s": s, "dir": dirname,
            "one": field.one, "zero": field.zero}


def determined_candidates(field, placed, L, lo, lattice=F(1, 2), frontier=1, span=6):
    """The anchors the three commands can *determine* at a target side L.

    ANCHOR_CORNER: a cell closed by two walls.  Otherwise a cell tangent to a
    placed cell and closed by a wall (PROPAGATE_SLIDE) or by a second contact
    (STACK_BLOCK) — the slide offset is searched on the exact lattice, and any
    candidate within one lattice step of a wall is snapped onto it exactly.
    """
    out = []
    dirs = list(field.dirs)
    if not placed:
        for d in dirs:
            probe = place(field, field.zero, field.zero, d)
            h = half_w(probe)
            for cx in (lo + h, lo + L - h):
                for cy in (lo + h, lo + L - h):
                    out.append(place(field, cx, cy, d))
        return out
    steps = int(span * F(2))          # offsets within +-span half-unit cells
    for p in placed[-frontier:]:
        for q in axes(p):
            for sign in (1, -1):
                for t in range(-steps, steps + 1):
                    probe_dir = None
                    for d in dirs:
                        probe_dir = d
                        cand0 = place(field, field.zero, field.zero, d)
                        gap = half_along(p, q) + half_along(cand0, q)
                        off = F(t) * lattice
                        # centre = p.centre + gap*q + off*q_perp
                        qx, qy = q
                        px, py = -qy, qx
                        cx = p["x"] + sign * gap * qx + off * px
                        cy = p["y"] + sign * gap * qy + off * py
                        cand = place(field, cx, cy, d)
                        cand = _snap_to_wall(cand, lo, L, lattice)
                        if not _inside(cand, lo, L):
                            continue
                        if slack(p, cand) != 0:
                            continue
                        if any(slack(o, cand) < 0 for o in placed):
                            continue
                        contacts = sum(1 for o in placed if slack(o, cand) == 0)
                        wells = len(wall_contacts(cand, lo, L))
                        if contacts + wells < 2:
                            continue
                        key = (cand["x"], cand["y"], cand["dir"])
                        if any((o["x"], o["y"], o["dir"]) == key for o in placed):
                            continue
                        out.append(cand)
    return out


def _inside(cell, lo, L):
    return all(s >= 0 for s in wall_slacks(cell, lo, L))


def _snap_to_wall(cell, lo, L, lattice):
    """Snap a candidate onto a wall it is within one lattice step of."""
    h = half_w(cell)
    hi = lo + L
    for axis in ("x", "y"):
        for wall, target in ((lo + h, lo + h), (hi - h, hi - h)):
            d = cell[axis] - wall
            if abs(d) <= lattice:
                cell = dict(cell)
                cell[axis] = target
    return cell


#: rational bracket of sqrt(d), shared by the bounds prefilter
_ROOT_LO, _ROOT_HI = {}, {}
#: memo of tested pairs, and counters for the ledger
_OVERLAP = {}
STATS = {"raw_candidates": 0, "kept_candidates": 0, "pairs_tested": 0,
         "prefilter_skips": 0, "memo_hits": 0, "memo_misses": 0}


def _root_bounds(d):
    """Exact rational bracket of sqrt(d): integer sqrt only, no float anywhere."""
    if d not in _ROOT_LO:
        n = _isqrt(d * 10 ** 24)
        _ROOT_LO[d], _ROOT_HI[d] = F(n, 10 ** 12), F(n + 1, 10 ** 12)
    return _ROOT_LO[d], _ROOT_HI[d]


def _isqrt(n):
    """Integer square root by Newton on ints (exact, no floating point)."""
    if n < 2:
        return n
    x = 1 << ((n.bit_length() + 1) // 2)
    while True:
        y = (x + n // x) // 2
        if y >= x:
            return x
        x = y


def bounds(cell, d):
    """A conservative rational bounding box, cheap to compare (no field maths)."""
    lo, hi = _root_bounds(d)

    def span(q):
        a, b = q.a, q.b
        return (a + b * lo, a + b * hi) if b >= 0 else (a + b * hi, a + b * lo)

    hlo, hhi = span(cell_h(cell))
    xlo, xhi = span(cell["x"])
    ylo, yhi = span(cell["y"])
    return (xlo - hhi, xhi - hlo, ylo - hhi, yhi - hlo)


def _boxes_touch(cb, ob):
    """Could two bounding boxes overlap at all?  Cheap, exact-conservative."""
    return not (cb[1] <= ob[0] or ob[1] <= cb[0] or cb[3] <= ob[2] or ob[3] <= cb[2])


def overlaps_memo(a, b, field):
    """Does the pair overlap?  Memoised — the same pairs recur across branches."""
    ka, kb = _key(a), _key(b)
    key = (field.d, ka, kb) if ka <= kb else (field.d, kb, ka)
    got = _OVERLAP.get(key)
    if got is None:
        got = slack(a, b) < 0
        _OVERLAP[key] = got
        STATS["memo_misses"] += 1
    else:
        STATS["memo_hits"] += 1
    return got


def clear_of(cand, placed, field):
    """Legality against every placed cell, with the bounds prefilter and the memo."""
    cb = bounds(cand, field.d)
    for o in placed:
        ob = bounds(o, field.d)
        STATS["pairs_tested"] += 1
        if not _boxes_touch(cb, ob):
            STATS["prefilter_skips"] += 1
            continue
        if overlaps_memo(o, cand, field):
            return False
    return True


def corner_anchors(field, placed, L, lo):
    """ANCHOR_CORNER: two walls fix the cell exactly — no search."""
    out = []
    for dname in field.dirs:
        probe = place(field, field.zero, field.zero, dname)
        h = half_w(probe)
        for cx in (lo + h, lo + L - h):
            for cy in (lo + h, lo + L - h):
                if any(_key(o) == _key(place(field, cx, cy, dname)) for o in placed):
                    continue
                out.append(place(field, cx, cy, dname))
    return out


def wall_contact_candidates(field, placed, L, lo):
    """PROPAGATE_SLIDE solved, not swept: a wall fixes one coordinate, and the
    tangency equation is linear in the other, so the candidate is one division."""
    out = []
    for p in placed:
        for dname in field.dirs:
            probe = place(field, field.zero, field.zero, dname)
            h = half_w(probe)
            px, py = p["x"], p["y"]
            for q in axes(p) + axes(probe):
                R = half_along(p, q) + half_along(probe, q)
                for s in (1, -1):
                    if q[1] != field.zero:          # x pinned by the wall
                        for cx in (lo + h, lo + L - h):
                            cy = py + (s * R - q[0] * (cx - px)) / q[1]
                            out.append(place(field, cx, cy, dname))
                    if q[0] != field.zero:          # y pinned by the wall
                        for cy in (lo + h, lo + L - h):
                            cx = px + (s * R - q[1] * (cy - py)) / q[0]
                            out.append(place(field, cx, cy, dname))
    return out


def two_contact_candidates(field, placed, L, lo):
    """STACK_BLOCK against two independent cells, solved as a 2x2 exact system.

    Two tangency equations are linear in the centre, so the intersection of the
    two loci is a division, not a scan.  The axis may belong to either parent or
    to the candidate itself (the 45 degree cell touches two axis cells along its
    own axis)."""
    out = []
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            p, q2 = placed[i], placed[j]
            for dname in field.dirs:
                probe = place(field, field.zero, field.zero, dname)
                trial = axes(p) + axes(q2) + axes(probe)
                for ap in trial:
                    for aq in trial:
                        det = ap[0] * aq[1] - ap[1] * aq[0]
                        if det == field.zero:
                            continue
                        for s1 in (1, -1):
                            for s2 in (1, -1):
                                r1 = s1 * (half_along(p, ap) + half_along(probe, ap))
                                r2 = s2 * (half_along(q2, aq) + half_along(probe, aq))
                                b1 = p["x"] * ap[0] + p["y"] * ap[1] + r1
                                b2 = q2["x"] * aq[0] + q2["y"] * aq[1] + r2
                                cx = (b1 * aq[1] - ap[1] * b2) / det
                                cy = (ap[0] * b2 - b1 * aq[0]) / det
                                out.append(place(field, cx, cy, dname))
    return out


def sweep_candidates(field, placed, L, lo, need=2):
    """The run-119 closure generator, kept **only** as a measurement control.

    It took the *same* corner and two-contact candidates as the current one, but
    obtained the wall+contact slides by sweeping a rational lattice (span 6) and
    testing each guess, instead of solving the linear equation.  Same width and
    same ordering as `lattice_candidates`, so the speedup is attributable.
    """
    raw = corner_anchors(field, placed, L, lo)
    raw += determined_candidates(field, placed, L, lo)
    raw += two_contact_candidates(field, placed, L, lo)
    STATS["raw_candidates"] += len(raw)
    out, seen = [], set()
    for cand in raw:
        k = _key(cand)
        if k in seen:
            continue
        seen.add(k)
        if not _inside(cand, lo, L):
            continue
        if not clear_of(cand, placed, field):
            continue
        contacts = sum(1 for o in placed if slack(o, cand) == 0)
        wells = len(wall_contacts(cand, lo, L))
        if contacts + wells < need:
            continue
        out.append(cand)
    STATS["kept_candidates"] += len(out)
    return out


def lattice_candidates(field, placed, L, lo, need=2):
    """Every anchor the three commands can *determine*, by constraint intersection.

    Corners (wall+wall), slides (wall+contact) and stacks (contact+contact) are
    each solved directly; nothing is swept.  A candidate survives only if it is
    inside, clear of every placed cell (bounds prefilter + memo) and closed by at
    least `need` constraints.
    """
    raw = corner_anchors(field, placed, L, lo)
    raw += wall_contact_candidates(field, placed, L, lo)
    raw += two_contact_candidates(field, placed, L, lo)
    STATS["raw_candidates"] += len(raw)
    out, seen = [], set()
    for cand in raw:
        k = _key(cand)
        if k in seen:
            continue
        seen.add(k)
        if not _inside(cand, lo, L):
            continue
        if not clear_of(cand, placed, field):
            continue
        contacts = sum(1 for o in placed if slack(o, cand) == 0)
        wells = len(wall_contacts(cand, lo, L))
        if contacts + wells < need:
            continue
        out.append(cand)
    STATS["kept_candidates"] += len(out)
    return out


def _key(cell):
    return (cell["x"].a, cell["x"].b, cell["y"].a, cell["y"].b, cell["dir"])


def write_progress(path, cells, nodes, states):
    """Checkpoint the deepest placement reached — best effort, exact text.

    Coordinates are written as ``[a, b]`` meaning ``a + b sqrt d``, so a killed
    run leaves a placement the caller can reload and re-gate exactly.
    """
    rec = {"cells": [[str(c["x"].a), str(c["x"].b), str(c["y"].a),
                      str(c["y"].b), str(c["c"].a), str(c["c"].b),
                      str(c["s"].a), str(c["s"].b), c.get("dir", "axis"),
                      c.get("i", -1)]
                     for c in cells],
           "nodes": nodes, "states": states}
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(rec, f)
    os.replace(tmp, path)


def read_progress(path, field):
    """Reload a checkpoint as cells (exact from the text, no floats)."""
    with open(path) as f:
        rec = json.load(f)
    out = []
    for xa, xb, ya, yb, ca, cb, sa, sb, dname, idx in rec["cells"]:
        out.append({"x": field.q(F(xa), F(xb)), "y": field.q(F(ya), F(yb)),
                    "c": field.q(F(ca), F(cb)), "s": field.q(F(sa), F(sb)),
                    "dir": dname, "one": field.one, "zero": field.zero,
                    "i": -1 if idx < 0 else idx})
    return out, rec["nodes"], rec["states"]


def settle(n_target, L, field, node_cap=None, top=None, mode="closure", order=True,
           progress=None):
    """Goal-directed settlement at a target side L — exhaustive by default.

    Every admitted anchor passes the exact placement gate at clearance >= 0, and
    an overlapping candidate is refused exactly (counted, not retried).  ``mode``
    chooses the generator: ``"lattice"`` (two-constraint closure, the default) or
    ``"frontier"`` (the one-parent slide generator of run 117/118).

    With ``node_cap``/``top`` unset the search runs until the state space is
    closed, so a failure is a statement about the grammar rather than a budget.
    ``progress`` is a path: the deepest placement reached so far is checkpointed
    there whenever it improves, so a caller that kills the run still gets the
    best effort rather than nothing.
    """
    lo = field.zero
    gen = {"frontier": determined_candidates, "sweep": sweep_candidates}.get(
        mode, lattice_candidates)
    seen, stack = set(), [()]
    nodes = refusals = 0
    deepest = ()
    why = "tree exhausted"
    while stack:
        cells = stack.pop()
        nodes += 1
        if len(cells) > len(deepest):
            deepest = cells
            if progress:
                write_progress(progress, deepest, nodes, len(seen))
        if node_cap is not None and nodes > node_cap:
            why = f"node cap {node_cap} reached after {len(deepest)} cells"
            break
        if len(cells) >= n_target:
            if progress:
                write_progress(progress, cells, nodes, len(seen))
            return {"placed": list(cells), "why": "target reached",
                    "refusals": refusals, "nodes": nodes,
                    "states": len(seen), "exhausted": False}
        placed = list(cells)
        cands = gen(field, placed, L, lo)
        # contact-first order: fill closed positions before opening new ones
        if order:
            cands = sorted(cands, key=lambda c: (
                -(sum(1 for o in placed if slack(o, c) == 0) +
                  len(wall_contacts(c, lo, L))), c["x"] + c["y"], c["x"], c["y"]))
        if top is not None:
            cands = cands[:top]
        for c in cands:
            cell = dict(c)
            cell["i"] = len(placed)
            if any(slack(o, cell) < 0 for o in placed) or not _inside(cell, lo, L):
                refusals += 1
                continue
            key = frozenset(_key(o) for o in placed) | {_key(cell)}
            if key in seen:
                continue
            seen.add(key)
            stack.append(tuple(placed + [cell]))
    return {"placed": list(deepest), "why": why, "refusals": refusals,
            "nodes": nodes, "states": len(seen),
            "exhausted": why == "tree exhausted"}


# ---------------------------------------------------------------------------
# 6.  CONTROLS
# ---------------------------------------------------------------------------
def refusal_control(n=10):
    """An anchor that bites into its parent must be refused with an exact slack."""
    built = build(n)
    parent = built["order"][0]
    child = next((c for c in built["order"] if c is not parent
                  and slack(parent, c) == 0), None)
    if child is None:
        raise Refusal("need a chain whose first anchor has a tangent child")
    moved = dict(child)
    if parent["x"] == child["x"]:
        moved["y"] = child["y"] + (F(1, 4) if parent["y"] > child["y"] else F(-1, 4))
    else:
        moved["x"] = child["x"] + (F(1, 4) if parent["x"] > child["x"] else F(-1, 4))
    step = anchor_step(2, "STACK_BLOCK", (0,), moved, built["lo"], built["side"],
                       [parent], built and exact_cells(n)[3])
    steps = [built["chain"].steps[0], step]
    geo = {(2, "cell"): moved, (2, "prefix"): [(parent["i"], parent)]}
    ok, why = anchor_gate(step, steps, geo, built["lo"], built["side"])
    sl = slack(parent, moved)
    return {"admitted": ok, "why": why, "exact_slack": str(sl),
            "expected_slack": "-1/4", "matches": (not ok) and sl == F(-1, 4)}


def selftest():
    """Two exact rows reconstruct, and the biting anchor is refused."""
    b2 = build(10)
    assert not b2["violations"], b2["violations"]
    want2 = FIELDS[2].q(3) + FIELDS[2].q(0, F(1, 2))
    assert b2["side"] == want2, (b2["side"], want2)
    assert len(b2["notes"]) == 10 and all(x["admitted"] for x in b2["notes"])
    b7 = build(18)
    assert not b7["violations"], b7["violations"]
    want7 = FIELDS[7].q(F(7, 2)) + FIELDS[7].q(0, F(1, 2))
    assert b7["side"] == want7, (b7["side"], want7)
    assert len(b7["notes"]) == 18 and all(x["admitted"] for x in b7["notes"])
    ctl = refusal_control()
    assert not ctl["admitted"] and ctl["matches"], ctl
    print(f"  n=10 side {b2['side']} == 3 + 1/2 sqrt2: {b2['side'] == want2}")
    print(f"  n=18 side {b7['side']} == 7/2 + 1/2 sqrt7: {b7['side'] == want7}"
          f"  ({b7['field']}, anchors {len(b7['notes'])}/18)")
    print(f"  refusal control: {ctl['why']} (exact slack {ctl['exact_slack']})")
    print("  selftest OK")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        selftest()
        return 0
    if "--forward" in argv:
        return forward(argv)
    for n, out in ((10, OUT), (18, OUT18)):
        built = build(n)
        print(f"n = {n} ({built['field']}): worst read {built['worst_read']}, "
              f"side {built['side']}, violations {len(built['violations'])}")
        for note in built["notes"]:
            print(f"  s{note['step']:>2d} {note['command']:<15s} cell "
                  f"{note['cell']:>2d}  {note['why']}")
        rec = {"n": n, "field": built["field"], "side": str(built["side"]),
               "worst_read": str(built["worst_read"]),
               "violations": [[i, j, str(s)] for i, j, s in built["violations"]],
               "steps": built["notes"],
               "columns": list(zip(built["chain"].column1(),
                                   built["chain"].column2()))}
        json.dump(rec, open(out, "w"), indent=1)
        print(f"wrote {out}")
    ctl = refusal_control()
    print(f"  REFUSAL CONTROL: {ctl['why']}  exact slack {ctl['exact_slack']}")
    return 0


def forward(argv):
    """The goal-directed tests: small exact targets, then the Block45 regime."""
    f2 = FIELDS[2]
    L5 = f2.q(2) + f2.q(0, F(1, 2))
    tests = [
        ("n=4 at L=2 (closure, width 8)", 4, f2.q(2), "closure", 8, None),
        ("n=5 at 2+1/2sqrt2 (frontier, no caps)", 5, L5, "frontier", None, None),
        ("n=5 at 2+1/2sqrt2 (closure, width 8)", 5, L5, "closure", 8, None),
        ("n=6 at L=3 (closure, width 8)", 6, f2.q(3), "closure", 8, None),
        ("n=7 at L=3 (closure, width 8)", 7, f2.q(3), "closure", 8, None),
    ]
    if "--closure5" in argv:
        tests = [t for t in tests if t[0].startswith("n=5")]
    if "--small" in argv:
        tests = tests[:3]
    recs = []
    for name, n, L, mode, top, cap in tests:
        print(f"\n  {name}", flush=True)
        STATS.update({k: 0 for k in STATS})
        _OVERLAP.clear()
        t0 = __import__("time").time()
        got = settle(n, L, f2, mode=mode, node_cap=cap, top=top)
        dt = __import__("time").time() - t0
        print(f"    settled {len(got['placed'])}/{n}; {got['why']}; nodes "
              f"{got['nodes']} states {got['states']} refusals {got['refusals']}"
              f" exhausted {got['exhausted']}", flush=True)
        if got["placed"]:
            lo, side = bbox(got["placed"])
            print(f"    exact span {side} (target {L}): {side == L}", flush=True)
        print(f"    stats {STATS}  {dt:.1f}s", flush=True)
        recs.append({"test": name, "target": str(L), "n_target": n,
                     "mode": mode, "top": top, "seconds": round(dt, 2),
                     "stats": dict(STATS),
                     "settled": len(got["placed"]),
                     "why": got["why"], "nodes": got["nodes"],
                     "states": got["states"], "exhausted": got["exhausted"],
                     "refusals": got["refusals"],
                     "span": str(bbox(got["placed"])[1]) if got["placed"] else None})
    json.dump(recs, open(OUTFWD, "w"), indent=1)
    print(f"\nwrote {OUTFWD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
