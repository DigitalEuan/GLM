#!/usr/bin/env python3
r"""crystal_domains.py — what crystal structure do the high-room rows actually have?

For each target row this reads the delivered pose and reports, in `Decimal` at 50
digits (no float in any decision):

  * orientation classes        — the distinct rotations mod pi/2
  * contact graph              — pairs with exact clearance <= 1e-9
  * grain boundaries           — contacts joining two *different* classes
  * domains                    — connected components over contacts, and the
                                 same-class sub-domains inside them
  * rigidity count             — a connected cluster of m squares needs 3m - 3
                                 scalar constraints; contacts vs that number is
                                 the necessary count condition for rigidity
  * area deficit               — L^2 / n, i.e. how far the pose is from the
                                 zero-waste bound L >= sqrt(n)

The room figure is the published one (verified table, `pub_bounds_check.py`), and
the *harvestable* part of it is bounded separately: no rearrangement can put a
row below sqrt(n), so at most `sum(L/sqrt(n) - 1)` of the bookkept room is
collectable by construction.  That sum is printed once for the whole room.

    python3 scripts/crystal_domains.py
    python3 scripts/crystal_domains.py --selftest
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 50

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import sqscore as SQ                          # noqa: E402

LEDGER = ROOT / "workspace/push/crystal_domains.json"
CHECK = ROOT / "workspace/push/pub_bounds_check.json"
TOL = Decimal("1e-9")            # contact threshold: the table's own frame padding
A_TOL = Decimal("1e-6")          # orientation-class threshold (radians)

PI = Decimal("3.14159265358979323846264338327950288419716939937510582097494")


# ------------------------------------------------------------------ trig ---
def _reduce(x: Decimal) -> Decimal:
    """x mod 2pi, into [-pi, pi]."""
    two = 2 * PI
    k = int(x / two)
    r = x - k * two
    if r > PI:
        r -= two
    elif r < -PI:
        r += two
    return r


def dcos(x: Decimal) -> Decimal:
    r, term, acc = _reduce(x), Decimal(1), Decimal(1)
    for k in range(1, 70):
        term = -term * r * r / ((2 * k - 1) * (2 * k))
        acc += term
    return acc


def dsin(x: Decimal) -> Decimal:
    r, term, acc = _reduce(x), Decimal(1), Decimal(1)
    term = r
    acc = r
    for k in range(1, 70):
        term = -term * r * r / ((2 * k) * (2 * k + 1))
        acc += term
    return acc


# -------------------------------------------------------------- geometry ---
def cell(x, y, th):
    """(x, y, cos, sin, ex) for a unit square, ex = (|c|+|s|)/2."""
    c, s = dcos(th), dsin(th)
    return (x, y, c, s, (abs(c) + abs(s)) / 2)


def slack(a, b) -> Decimal:
    """max over the four orientation axes of the separating slack."""
    xa, ya, ca, sa, ea = a
    xb, yb, cb, sb, eb = b
    dx, dy = xb - xa, yb - ya
    best = None
    for ux, uy in ((ca, sa), (-sa, ca), (cb, sb), (-sb, cb)):
        proj = (abs(ux * ca + uy * sa) + abs(ux * -sa + uy * ca)) / 2
        proj_b = (abs(ux * cb + uy * sb) + abs(ux * -sb + uy * cb)) / 2
        v = abs(dx * ux + dy * uy) - proj - proj_b
        best = v if best is None or v > best else best
    return best


def slack_axes(a, b):
    """(max slack, number of axes with slack <= 1e-9).

    One tight axis is an edge contact, two or more is a corner contact; a pair
    whose projections only *touch* on one axis while being apart on another has
    a positive slack on that other axis, so its max slack is positive and it is
    not a contact at all.
    """
    best, tight = None, {}
    for (ux, uy), v in _axis_slacks(a, b):
        if best is None or v > best:
            best = v
        if abs(v) <= TOL:
            key = (ux, uy) if (ux > 0 or (ux == 0 and uy > 0)) else (-ux, -uy)
            tight[key] = v
    return best, len(tight)


def _axis_slacks(a, b):
    xa, ya, ca, sa, _ = a
    xb, yb, cb, sb, _ = b
    dx, dy = xb - xa, yb - ya
    for ux, uy in ((ca, sa), (-sa, ca), (cb, sb), (-sb, cb)):
        proj = (abs(ux * ca + uy * sa) + abs(ux * -sa + uy * ca)) / 2
        proj_b = (abs(ux * cb + uy * sb) + abs(ux * -sb + uy * cb)) / 2
        yield (ux, uy), abs(dx * ux + dy * uy) - proj - proj_b


def classify(pose):
    """Cells, orientation classes (mod pi/2), contact graph, domains."""
    cells = [cell(x, y, th) for x, y, th in pose]
    quarter = PI / 2
    reps: list = []
    cls = []
    for x, y, th in pose:
        r = th % quarter
        if r > quarter / 2:
            r -= quarter                     # a square is symmetric under pi/2
        hit = None
        for i, v in enumerate(reps):
            if abs(r - v) <= A_TOL:
                hit = i
                break
        if hit is None:
            hit = len(reps)
            reps.append(r)
        cls.append(hit)

    n = len(cells)
    contact = [False] * (n * n)
    edges = []            # touching pairs (edges and corners)
    edge_only = 0
    for i in range(n):
        for j in range(i + 1, n):
            sl, zeros = slack_axes(cells[i], cells[j])
            if sl <= TOL:
                contact[i * n + j] = contact[j * n + i] = True
                edges.append((i, j, cls[i] != cls[j]))
                if zeros == 1:
                    edge_only += 1

    def comps(same_only: bool) -> list:
        seen, out = set(), []
        for i in range(n):
            if i in seen:
                continue
            stack, group = [i], []
            seen.add(i)
            while stack:
                u = stack.pop()
                group.append(u)
                for v in range(n):
                    if v in seen or not contact[u * n + v]:
                        continue
                    if same_only and cls[u] != cls[v]:
                        continue
                    seen.add(v)
                    stack.append(v)
            out.append(sorted(group))
        return out

    domains = comps(same_only=False)
    same = comps(same_only=True)
    cross = [e for e in edges if e[2]]
    deg = [sum(1 for v in range(n) if contact[i * n + v]) for i in range(n)]
    biggest = max(domains, key=len)
    need = 3 * len(biggest) - 3
    return {
        "classes": len(reps), "class_sizes": sorted(
            (sum(1 for c in cls if c == k) for k in range(len(reps))), reverse=True),
        "class_reps_rad": [float(v) for v in reps],
        "contacts": len(edges),
        "edge_contacts": edge_only,
        "corner_contacts": len(edges) - edge_only,
        "cross_class_contacts": len(cross),
        "domains": len(domains),
        "same_class_domains": len(same),
        "biggest_domain": len(biggest),
        "biggest_same_class": max(len(g) for g in same),
        "rigidity_need": need,
        "rigidity_ratio": (round(edge_only / need, 3) if need else None),
        "mean_degree": round(sum(deg) / n, 2),
    }


def side(pose) -> Decimal:
    cells = [cell(x, y, th) for x, y, th in pose]
    return max(max(c[0] + c[4] for c in cells) - min(c[0] - c[4] for c in cells),
               max(c[1] + c[4] for c in cells) - min(c[1] - c[4] for c in cells))


def room_table(per, vt):
    rows = []
    tot_room = Decimal(0)
    for n in range(1, 101):
        L = side([(Decimal(str(x)), Decimal(str(y)), Decimal(str(t)))
                  for x, y, t in per[n]])
        lb = Decimal(vt[str(n)]["lb"])
        r = (L - lb) / Decimal(n).sqrt()
        slack_score = L / Decimal(n).sqrt() - 1    # what a zero-waste pose would bank
        tot_room += r
        rows.append({"n": n, "L": L, "lb": lb, "room": r,
                     "geometric_slack_score": slack_score,
                     "room_over_slack": (r / slack_score) if slack_score > 0 else None})
    return rows, tot_room


def main() -> int:
    per = SQ.load()
    vt = json.load(open(CHECK))["verified_table"]
    rows, tot_room = room_table(per, vt)
    top = sorted(rows, key=lambda r: r["room"], reverse=True)[:10]
    named = [r for r in rows if r["n"] in (11, 17, 18, 19)]
    targets = sorted({r["n"] for r in top} | {r["n"] for r in named})

    tol_room = Decimal("5e-5")
    room_rows = [r for r in rows if r["room"] * Decimal(r["n"]).sqrt() > tol_room]
    slack = sum(r["geometric_slack_score"] for r in room_rows)
    out = {"targets": targets, "rows": {}, "room_total": str(tot_room),
           "room_rows": len(room_rows),
           "geometric_slack_on_room_rows": str(slack)}
    print(f"room {tot_room:.5f} over {len(room_rows)} rows; those same rows hold "
          f"{slack:.5f} of geometric slack (L/sqrt(n) - 1), so the room is "
          f"{float(tot_room/slack):.0%} of the distance to a zero-waste pose")
    print(f"{'n':>4} {'L':>12} {'L^2/n':>8} {'room':>9} {'cls':>4} {'cont':>5} "
          f"{'cross':>5} {'dom':>4} {'same':>5} {'big':>4} {'need':>5} {'ratio':>6}")
    for r in rows:
        if r["n"] not in targets:
            continue
        pose = [(Decimal(str(x)), Decimal(str(y)), Decimal(str(t)))
                for x, y, t in per[r["n"]]]
        c = classify(pose)
        L = r["L"]
        out["rows"][r["n"]] = {"L": str(L), "L2_over_n": float(L * L / r["n"]),
                               "room": str(r["room"]),
                               "geometric_slack_score": str(r["geometric_slack_score"]),
                               "room_over_slack": (None if r["room_over_slack"] is None
                                                   else float(r["room_over_slack"])), **c}
        print(f"{r['n']:>4} {float(L):>12.6f} {float(L*L/r['n']):>8.4f} "
              f"{float(r['room']):>9.5f} {c['classes']:>4} {c['contacts']:>5} "
              f"{c['cross_class_contacts']:>5} {c['domains']:>4} "
              f"{c['same_class_domains']:>5} {c['biggest_domain']:>4} "
              f"{c['rigidity_need']:>5} {c['rigidity_ratio']:>6}")
    LEDGER.write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(f"wrote {LEDGER}")
    return 0


def selftest() -> int:
    print("crystal_domains selftest")
    # 1. trig: cos/sin on a few exact points
    assert abs(dcos(Decimal(0)) - 1) < Decimal("1e-25")
    assert abs(dsin(PI / 2) - 1) < Decimal("1e-25")
    assert abs(dcos(PI) + 1) < Decimal("1e-25")
    assert abs(dsin(PI / 6) - Decimal("0.5")) < Decimal("1e-25")
    print("  1. dcos/dsin correct at 0, pi/6, pi/2, pi to 1e-25")

    # 2. a 3x3 grid: 1 class, 12 contacts, one domain, ratio 12/24
    pose = [(Decimal(i) + Decimal("0.5"), Decimal(j) + Decimal("0.5"), Decimal(0))
            for i in range(3) for j in range(3)]
    c = classify(pose)
    assert c["classes"] == 1 and c["contacts"] == 20 and c["domains"] == 1, c
    assert (c["edge_contacts"], c["corner_contacts"]) == (12, 8), c
    assert c["cross_class_contacts"] == 0 and c["rigidity_ratio"] == 0.5, c
    assert side(pose) == 3
    print(f"  2. 3x3 grid: {c['edge_contacts']} edge + {c['corner_contacts']} corner "
          f"contacts, 1 class, 1 domain, ratio {c['rigidity_ratio']}, side exactly 3")

    # 3. two tilted squares touching across a class boundary count as a grain
    t = Decimal(2) ** Decimal("0.5")           # 45 degrees is 2*atan(tan(pi/8))? use pi/4
    pose = [(Decimal("0"), Decimal("0"), Decimal(0)),
            (Decimal(1), Decimal("0"), PI / 4)]
    c = classify(pose)
    assert c["classes"] == 2 and c["cross_class_contacts"] == 1, c
    assert c["domains"] == 1 and c["same_class_domains"] == 2, c
    print(f"  3. axis + 45-degree square in contact: {c['classes']} classes, "
          f"{c['cross_class_contacts']} grain contact, {c['same_class_domains']} same-class domains")

    # 4. a separated pair: no contact, no domain joining them
    pose = [(Decimal(0), Decimal(0), Decimal(0)), (Decimal(3), Decimal(0), Decimal(0))]
    c = classify(pose)
    assert c["contacts"] == 0 and c["domains"] == 2, c
    print("  4. separated pair: 0 contacts, 2 domains")
    print("selftest OK (4 controls)")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
