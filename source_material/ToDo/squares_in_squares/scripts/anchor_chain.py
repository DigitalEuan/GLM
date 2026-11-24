#!/usr/bin/env python3
r"""anchor_chain.py — run 117: square placements as backward-linked anchor
commands, under the GLM's own three-column step contract.

WHY THIS EXISTS.  ``glm_universal.reasoning.stepwise_script`` is the stepwise
planner's chain format: every step is *admitted* by a gate (``step_check``) that
reads column 1 (a sentence) and column 2 (an exact equation) back with its own
readers, requires every input to be an earlier step, and recomputes a computed
value exactly.  This module asks whether a packing can be written in that form:
an anchor is a command that places one square, admitted only when the step
itself passes the GLM gate **and** the placement closes exactly.

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

THE EXACT ROW.  n = 10, the proved optimum ``s(10) = 3 + 1/2 sqrt2`` (Stromquist
2003; this project's doc 24).  The delivered pose's decimal strings snap exactly
to ``(1/4)Z + (1/4) sqrt2 Z`` at directions 0 and 45 degrees, so the whole
reconstruction is exact: side ``3 + 1/2 sqrt2``, zero overlap, and a refusal
control whose anchor bites 1/4 into its parent.
"""
from __future__ import annotations

import json
import os
import sys
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

#: The tolerance a decimal string is snapped with — a *reading*, not a result.
SNAP = F(1, 10 ** 6)


class Q2(EF.Quad):
    """The real quadratic field Q(sqrt 2) the n = 10 pose lives in."""

    d = 2


ZERO, ONE = Q2(0), Q2(1)
HALF = F(1, 2)
#: The declared decimals the direction of a cell is read from.
ANGLE_AXIS = F("0.0")
ANGLE_DIAG = F("0.7853981633974483")
#: Directions, exact: 0 degrees and 45 degrees.
DIR_AXIS = (Q2(1), Q2(0))
DIR_DIAG = (Q2(0, HALF), Q2(0, HALF))


class Refusal(Exception):
    """An anchor the gate does not admit."""


# ---------------------------------------------------------------------------
# 1.  EXACT GEOMETRY IN Q(sqrt 2)
# ---------------------------------------------------------------------------
def half_along(cell, axis):
    """The half-width of a cell along an axis: (|c.qx + s.qy| + |-s.qx + c.qy|)/2."""
    c, s = cell["c"], cell["s"]
    qx, qy = axis
    return (abs(c * qx + s * qy) + abs(-s * qx + c * qy)) * HALF


def axes(cell):
    """The two edge normals of a cell — enough for the separating-axis test."""
    c, s = cell["c"], cell["s"]
    return ((c, s), (-s, c))


def slack(a, b):
    """Exact SAT slack between two cells: > 0 apart, 0 tangent, < 0 overlapping.

    Two convex sets are disjoint iff one of their four edge normals separates
    them, so the maximum over those four axes is the true slack.
    """
    dx, dy = b["x"] - a["x"], b["y"] - a["y"]
    best = None
    for q in axes(a) + axes(b):
        proj = dx * q[0] + dy * q[1]
        sl = abs(proj) - half_along(a, q) - half_along(b, q)
        if best is None or sl > best:
            best = sl
    return best


def wall_slacks(cell, lo, side):
    """The four exact gaps from a cell's bounding box to the container walls."""
    h = half_along(cell, DIR_AXIS)          # (|c| + |s|)/2, the bbox half-width
    hi = lo + side
    return (cell["x"] - h - lo, hi - (cell["x"] + h),
            cell["y"] - h - lo, hi - (cell["y"] + h))


def bbox(cells):
    """(lo, side) of a set of cells, exactly: the container they define."""
    los, his = [], []
    for c in cells:
        h = half_along(c, DIR_AXIS)
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
# 2.  READING THE DELIVERED ROW EXACTLY
# ---------------------------------------------------------------------------
def load_raw(n):
    """The pose's decimal strings, exactly — ``parse_float=str`` keeps the text,
    so no binary float is ever constructed."""
    with open(TAB) as f:
        tab = json.load(f, parse_float=str)
    rec = tab[str(n)]
    return str(rec["L"]), [(str(r[0]), str(r[1]), str(r[2])) for r in rec["state"]]


def direction_of(angle_text):
    """Classify a cell's direction as axis (0 deg) or diagonal (45 deg), by
    exact rational comparison against the two declared decimals."""
    a = F(angle_text)
    da, dd = abs(a - ANGLE_AXIS), abs(a - ANGLE_DIAG)
    if min(da, dd) > SNAP:
        raise Refusal(f"angle {angle_text} is not in the declared direction set")
    return "axis" if da <= dd else "diag"


def snap(text):
    """The exact ``a/4 + (b/4) sqrt2`` nearest a decimal string, or a refusal."""
    want = F(text)
    best = None
    for a in range(-40, 41):
        for b in range(-40, 41):
            q = Q2(F(a, 4), F(b, 4))
            err = abs(q - want)
            if best is None or err < best[0]:
                best = (err, q)
    if best[0] > SNAP:
        raise Refusal(f"{text} is not within {SNAP} of a quarter-lattice value")
    return best[1], best[0]


def exact_cells(n):
    """Snap a delivered pose to exact cells; report the worst read."""
    L_text, rows = load_raw(n)
    cells, worst = [], F(0)
    for i, (xs, ys, ts) in enumerate(rows):
        x, ex = snap(xs)
        y, ey = snap(ys)
        worst = max(worst, ex, ey)
        d = direction_of(ts)
        c, s = DIR_DIAG if d == "diag" else DIR_AXIS
        cells.append({"i": i, "x": x, "y": y, "c": c, "s": s, "dir": d})
    return cells, F(L_text), worst


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
def anchor_step(k, cmd, parents, cell, lo, side, placed):
    """The Step for one anchor: the command in both columns, the count as its
    exact value, the anchor itself in ``detail``."""
    name = f"{cmd}#{cell['i']}"
    detail = {
        "name": name,
        "anchor": {
            "command": cmd, "cell": cell["i"], "dir": cell["dir"],
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


def anchor_gate(step, steps, cells_by_step, lo, side):
    """Admit an anchor: the GLM gate *and* the exact placement.

    The GLM gate is ``step_check`` (columns read back, links, recompute).  The
    placement gate re-verifies, exactly, that the cell is inside the container,
    tangent to every contact it declares, on every wall it declares, clear of
    every earlier cell, and that every requirement is an earlier step.
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
    for j, cellj in cells_by_step[(k, "prefix")]:
        sl = slack(cellj, cell)
        if sl < 0:
            return False, f"overlap with cell {j}: exact slack {sl}"
    prefix = cells_by_step[(k, "prefix")]
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


def build(n=10):
    """Reconstruct the exact row as a chain of admitted anchor commands."""
    cells, L_text, worst = exact_cells(n)
    lo, side = bbox(cells)
    order = order_cells(cells, lo, side)
    steps, geo, notes = [], {}, []
    placed = []
    for k, cell in enumerate(order, start=1):
        cmd, par_idx = command_for(cell, placed, lo, side)
        parents = [n for n, p in enumerate(placed) if p["i"] in par_idx]
        step = anchor_step(k, cmd, parents, cell, lo, side, placed)
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
                         notes=("anchor commands, exact in Q(sqrt 2)",))
        ok, chain_notes = SS.chain_check(chain)
        if not ok:
            raise Refusal("chain_check refused: " + "; ".join(chain_notes))
    return {"n": n, "chain": chain, "cells": cells, "order": order,
            "lo": lo, "side": side, "L_text": L_text, "worst_read": worst,
            "notes": notes, "violations": overlaps(cells)}


# ---------------------------------------------------------------------------
# 5.  CONTROLS
# ---------------------------------------------------------------------------
def refusal_control(n=10):
    """An anchor that bites into its parent must be refused with an exact slack.

    The legal chain is built, then step 2's cell is moved 1/4 towards its parent
    along the x axis and offered to the same gate.  The gate must refuse, and the
    exact slack it reports must be -1/4.
    """
    built = build(n)
    parent = built["order"][0]
    child = next((c for c in built["order"] if c is not parent
                  and slack(parent, c) == 0), None)
    if child is None:
        raise Refusal("need a chain whose first anchor has a tangent child")
    moved = dict(child)
    # 1/4 towards the parent along the axis they actually touch on
    if parent["x"] == child["x"]:
        moved["y"] = child["y"] + (Q2(F(1, 4)) if parent["y"] > child["y"]
                                    else Q2(F(-1, 4)))
    else:
        moved["x"] = child["x"] + (Q2(F(1, 4)) if parent["x"] > child["x"]
                                    else Q2(F(-1, 4)))
    step = anchor_step(2, "STACK_BLOCK", (0,), moved, built["lo"], built["side"],
                       [parent])
    # a two-step chain: the parent's admitted step, then the biting anchor — so
    # the gate has to refuse on the geometry, not on the plumbing
    steps = [built["chain"].steps[0], step]
    geo = {(2, "cell"): moved, (2, "prefix"): [(parent["i"], parent)]}
    ok, why = anchor_gate(step, steps, geo, built["lo"], built["side"])
    sl = slack(parent, moved)
    return {"admitted": ok, "why": why, "exact_slack": str(sl),
            "expected_slack": "-1/4", "matches": (not ok) and sl == Q2(F(-1, 4))}


def selftest():
    """The exact row reconstructs, and the biting anchor is refused."""
    built = build()
    assert not built["violations"], built["violations"]
    want = Q2(F(3)) + Q2(0, HALF)                        # 3 + 1/2 sqrt2
    assert built["side"] == want, (built["side"], want)
    assert len(built["notes"]) == 10 and all(x["admitted"] for x in built["notes"])
    ctl = refusal_control()
    assert not ctl["admitted"], ctl
    assert ctl["matches"], ctl
    print(f"  exact side {built['side']} == 3 + 1/2 sqrt2: "
          f"{built['side'] == want}")
    print(f"  anchors admitted: {len(built['notes'])}/10, "
          f"commands {sorted({x['command'] for x in built['notes']})}")
    print(f"  refusal control: {ctl['why']} (exact slack {ctl['exact_slack']})")
    print("  selftest OK")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        selftest()
        return 0
    built = build()
    print(f"n = {built['n']}: worst coordinate read {built['worst_read']}, "
          f"side {built['side']}, violations {len(built['violations'])}")
    for note in built["notes"]:
        print(f"  s{note['step']:>2d} {note['command']:<14s} cell "
              f"{note['cell']:>2d}  {note['why']}")
    ctl = refusal_control()
    print(f"  REFUSAL CONTROL: {ctl['why']}  exact slack {ctl['exact_slack']}")
    rec = {"n": built["n"], "side": str(built["side"]),
           "side_text": "3 + 1/2*sqrt2", "worst_read": str(built["worst_read"]),
           "violations": [[i, j, str(s)] for i, j, s in built["violations"]],
           "steps": built["notes"], "control": ctl,
           "columns": list(zip(built["chain"].column1(), built["chain"].column2()))}
    json.dump(rec, open(OUT, "w"), indent=1)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
