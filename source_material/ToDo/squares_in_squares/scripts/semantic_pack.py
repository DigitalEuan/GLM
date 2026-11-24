#!/usr/bin/env python3
r"""semantic_pack.py — the relational layer: contacts, pins, pockets, coupled moves.

Runs 106-108 tested a packing one or two cells at a time (slides, chains, face slides) and always
against the same picture: the side is set by a *contact*, and nothing local can move it. This module
asks the next question — what is the *relational* structure of those contacts, and can moving a
connected group, re-orienting it, or trading a void against a pin lower the side? The gate and
`verify_certificates.py` stay the only judges; everything here is exact over `Q(sqrt 2)`.

PART 1 -- the relational graph of a row.
  * `contacts`      every pair in exact contact (slack 0), with the axis that holds it;
  * `pins`          for each bbox side, the wall cells and, per wall cell, the contacts whose
                    holding axis is *narrowed* by the inward direction -- these are the pins that
                    make a single-cell slide useless;
  * `bottlenecks`   the depth-2 chain wall cell -> pin -> that pin's own pin, i.e. the smallest
                    relational obstruction a move has to break;
  * `pockets`       the connected components of the cells that have room along a given direction,
                    i.e. the free space a coupled move could trade against a pin.
  It is the same information doc 68 measured cell by cell, now read as a graph: who holds whom.

PART 2 -- coupled relational moves, all exact, all judged by the gate:
  * `rigid`         translate a connected sub-cluster (2..5 cells) along one of the eight signed
                    directions by the exact time its first outside pair makes contact;
  * `reorient`      rotate a sub-cluster by 45 or 90 degrees about its own bbox centre -- the eight
                    words are closed under 45 degree rotation, so this stays in `Q(sqrt 2)`;
  * `trade`         a wall-pinning cell and its pin move apart by the same exact amount, so the pair
                    stays legal while the void behind the pin is spent.
  Every survivor is squeezed (run 108's face slide), gated at clearance 0, certified, and compared
  with the delivered side.

READ-ONLY on `submission.csv` and the root `WHITEBOARD.md`; the ledger is
`workspace/push/semantic_pack.json`, and no score is claimed.

USAGE
    python3 scripts/semantic_pack.py --selftest
    python3 scripts/semantic_pack.py --analyse
    python3 scripts/semantic_pack.py --search
    python3 scripts/semantic_pack.py            # both
"""
from __future__ import annotations

import json
import os
import sys
import time
from decimal import Decimal, localcontext
from fractions import Fraction as F
from math import isqrt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import cand105 as C                 # noqa: E402
import cand106 as K                 # noqa: E402
import rat47 as R                   # noqa: E402
import qsqrt2 as Q                  # noqa: E402
import face_slide as FSL            # noqa: E402
import verify_certificates as VC    # noqa: E402
import true_geom as TG              # noqa: E402

Q2 = C.Q2
HALF = F(1, 2)
ZERO, ONE, TWO = Q2(F(0)), Q2(F(1)), Q2(F(2))
H = Q2(F(0), HALF)                  # sqrt(2)/2, the exact 45 degree unit
SIDES = K.SIDES
DIRS8 = K.DIRS8
OUT = os.path.join(ROOT, "workspace/push/semantic_pack.json")
TAB = os.path.join(ROOT, "workspace/submission/table.json")
TARGETS = (11, 17, 18, 29, 330)
MAXK = 5
SET_CAP = 24


# ------------------------------------------------------------------ fields, words, states
def rot_point(p, c, k):
    """Rotate `p` by `k` x 45 degrees about `c`, exactly in `Q(sqrt 2)`."""
    dx, dy = p[0] - c[0], p[1] - c[1]
    for _ in range(k % 8):
        dx, dy = (dx - dy) * H, (dx + dy) * H
    return (c[0] + dx, c[1] + dy)


def rot_word(w, k):
    """Rotate a unit word by `k` x 45 degrees; the eight words are closed under this."""
    c, s = w[0], w[1]
    for _ in range(k % 8):
        c, s = (c - s) * H, (c + s) * H
    return (c, s)


def q_st(v):
    """A JSON-safe exact scalar: the rational string when `v` is in `Q`, else its `[a, b]` pair."""
    return str(v.a) if v.b == 0 else [str(v.a), str(v.b)]


_SQ2 = None


def sqrt2_frac(k=60):
    """`sqrt(2)` as a rational within `10^-k`, from `isqrt` only (no float anywhere)."""
    global _SQ2
    if _SQ2 is None or _SQ2[0] != k:
        _SQ2 = (k, F(isqrt(2 * 10 ** (2 * k)), 10 ** k))
    return _SQ2[1]


def to_dec(x, d=12):
    """`x` in `Q(sqrt 2)`, rounded to `d` decimals as an exact `Q` element.

    The projection is a *rendering*: `sqrt(2)` is bracketed to 60 places by `isqrt`, then the
    value is rounded by integer arithmetic, so the decimal written out is within `10^-d` of the
    true coordinate.  Whatever comes out is gated again exactly, as a rational state.
    """
    v = F(x.a) + F(x.b) * sqrt2_frac()
    q = v * 10 ** d
    scaled = (q.numerator + q.denominator // 2) // q.denominator if q >= 0 else \
        -((-q.numerator + q.denominator // 2) // q.denominator)
    return Q2(F(scaled, 10 ** d))


def q_parse(s):
    """Inverse of `q_st`: an exact field element from its JSON form (string or `[a, b]` pair)."""
    if isinstance(s, (list, tuple)):
        return Q2(F(s[0]), F(s[1]))
    s = s.strip()
    if "\u221a2" not in s and "√2" not in s:
        return Q2(F(s))
    body = s.replace("√2", "").replace("\u221a2", "").strip()
    toks, sign, cur = [], 1, ""
    for ch in body:
        if ch == " ":
            continue
        if ch in "+-":
            if cur:
                toks.append((sign, cur))
                cur = ""
            sign = 1 if ch == "+" else -1
        else:
            cur += ch
    if cur:
        toks.append((sign, cur))
    a, b = F(0), F(0)
    for i, (sg, t) in enumerate(toks):
        if i == len(toks) - 1:
            b = sg * F(t)                      # the √2 coefficient is the last token
        else:
            a += sg * F(t)
    return Q2(a, b)


def state_of(n, rows=None):
    """The row's exact decimal pose with its angles snapped to the eight words."""
    rows = rows or C.load_rows()
    row = rows[n]
    pf = [(C._q(x), C._q(y)) for x, y, _t in row]
    snap = [R.snap(t) for _x, _y, t in row]
    return pf, [s[2] for s in snap], max(s[3] for s in snap)


def survey(pf, wf):
    """Every overlapping pair and every pair in exact contact, exactly."""
    sv = K.survey_row([(x, y) for x, y in pf], wf)
    return sv


def repair(pf, wf, sv, cap=60):
    """Clear the overlaps with the smallest exact slides; returns the clean pose and the steps."""
    guard = 0
    while sv["violations"] and guard < cap:
        guard += 1
        worst = FSL.worst_pair(pf, wf)
        if worst is None:
            break
        step = K.repair_step(pf, wf, worst[1], worst[2])
        if step is None:
            break
        pf = [(C._q(x), C._q(y)) for x, y in step["state"]]
        sv = survey(pf, wf)
    return ((pf, sv, guard) if not sv["violations"] else (None, sv, guard))


def side_of(pf, wf):
    """The container side of a pose (the gate's own rule: the wider axis)."""
    box, _ = K.box_and_edges([(x, y) for x, y in pf], wf)
    return max(box[2] - box[0], box[3] - box[1])


# ------------------------------------------------------------------ part 1: the graph
def contacts(pf, wf):
    """Every pair in exact contact, with the axis that holds it and whether it is wall-facing."""
    out = []
    n = len(pf)
    for i in range(n):
        for j in range(i + 1, n):
            if abs(pf[j][0] - pf[i][0]) >= TWO or abs(pf[j][1] - pf[i][1]) >= TWO:
                continue
            best, bq = None, None
            for proj, need, q in K.pair_axes(pf, wf, i, j):
                sl = abs(proj) - need
                if best is None or sl > best:
                    best, bq = sl, q
            if best is not None and best.sign() == 0:
                out.append((i, j, bq))
    return out


def pins(pf, wf, side, con):
    """The wall cells of one side and, per cell, the contacts that block its inward motion."""
    cells = K.wall_cells([(x, y) for x, y in pf], wf, side)
    d = K.inward(side)
    out = {}
    for wc in cells:
        blocked = []
        for (i, j, q) in con:
            if wc not in (i, j):
                continue
            other = j if i == wc else i
            move_w = (i == wc)
            proj, need = None, None
            for p, nd, qq in K.pair_axes(pf, wf, min(i, j), max(i, j)):
                if qq == q:
                    proj, need = abs(p), nd
                    break
            if proj is None:
                continue
            dq = d[0] * q[0] + d[1] * q[1]
            if dq.sign() == 0:
                continue
            kq = -dq if move_w else dq
            if proj.sign() == 0 or (proj.sign() * kq.sign()) < 0:
                blocked.append({"cell": other, "axis": [str(q[0]), str(q[1])]})
        out[wc] = blocked
    return out


def bottlenecks(pf, wf, con):
    """Depth-2 chains: a wall cell, its pin, and the pin's own pin. The obstruction a move meets."""
    chains = []
    for side in SIDES:
        pin_map = pins(pf, wf, side, con)
        for wc, blocked in pin_map.items():
            for b in blocked:
                second = []
                for (i, j, q) in con:
                    if b["cell"] not in (i, j):
                        continue
                    other = j if i == b["cell"] else i
                    second.append(other)
                if second:
                    chains.append({"side": side, "wall": wc, "pin": b["cell"],
                                   "second": sorted(set(second))})
    return chains


def rooms(pf, wf):
    """Each *wall* cell's exact room along that wall's inward direction, as (cell, side, T).

    Only a wall cell's inward direction is a meaningful move (anything else grows the box), so the
    relational graph's free space is indexed by the wall it would leave.
    """
    out = []
    for side in SIDES:
        for i in K.wall_cells([(x, y) for x, y in pf], wf, side):
            T, binder, note = FSL.face_room(pf, wf, [i], K.inward(side))
            if note is None and T is not None and T.sign() > 0:
                out.append((i, side, T))
    return out


def pockets(pf, wf, con):
    """Connected components of the cells with room, in the contact graph: the free-space groups."""
    free = {(i, side) for (i, side, _T) in rooms(pf, wf)}
    cells = {i for (i, _s) in free}
    parent = {i: i for i in cells}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for (i, j, _q) in con:
        if i in cells and j in cells:
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[ri] = rj
    groups = {}
    for i in cells:
        groups.setdefault(find(i), []).append(i)
    return sorted((sorted(v) for v in groups.values()), key=lambda g: (-len(g), g))


def analyse_row(n, rows=None):
    """The whole relational picture of one row, plus its exact status."""
    pf, wf, gap = state_of(n, rows)
    tab = json.load(open(TAB), parse_float=str)
    rec = {"n": n, "N": len(pf), "word_gap": str(gap),
           "L_delivered": str(F(str(tab[str(n)]["L"]))), "L_pose": None,
           "start_violations": None, "clean": False, "steps": 0}
    sv = survey(pf, wf)
    rec["start_violations"] = len(sv["violations"])
    if sv["violations"]:
        pf, sv, nst = repair(pf, wf, sv)
        rec["steps"] = nst
        if pf is None:
            rec["verdict"] = "repair-stalled"
            rec["left"] = len(sv["violations"])
            rec["blocked"] = [[v[0], v[1], v[2]] for v in sv["violations"][:6]]
            return rec
    rec["clean"] = True
    rec["L_pose"] = q_st(side_of(pf, wf))
    con = contacts(pf, wf)
    rec["contacts"] = len(con)
    rec["contact_degree"] = sorted({i: sum(1 for e in con if i in (e[0], e[1]))
                                    for i in range(len(pf))}.values(), reverse=True)[:8]
    pin_map = {side: pins(pf, wf, side, con) for side in SIDES}
    rec["wall"] = {side: {"cells": len(pin_map[side]),
                          "pinned": sum(1 for v in pin_map[side].values() if v),
                          "free": sum(1 for v in pin_map[side].values() if not v)}
                   for side in SIDES}
    rec["bottlenecks"] = bottlenecks(pf, wf, con)
    rr = rooms(pf, wf)
    rec["rooms"] = {"count": len(rr),
                    "max": q_st(max((t for (_i, _s, t) in rr), default=ZERO))}
    rec["pockets"] = [len(g) for g in pockets(pf, wf, con)]
    rec["verdict"] = "mapped"
    rec["_pf"], rec["_wf"] = pf, wf
    return rec


def run_analyse(targets=TARGETS):
    start = time.time()
    rows = C.load_rows()
    out = {"rows": {}, "seconds": None}
    for n in targets:
        rec = analyse_row(n, rows)
        rec.pop("_pf", None)
        rec.pop("_wf", None)
        out["rows"][str(n)] = rec
        print(f"  n={n}: viol {rec['start_violations']} L={rec.get('L_pose')}"
              f" contacts={rec.get('contacts')} walls={rec.get('wall')}"
              f" chains={len(rec.get('bottlenecks') or [])} pockets={rec.get('pockets')}")
    out["seconds"] = str(F(time.time() - start).limit_denominator(100))
    return out


# ------------------------------------------------------------------ the containment guard
def gaps_of(n, rows=None):
    """The row's snapping error: `(count of non-word angles, largest gap in radians)`."""
    rows = rows or C.load_rows()
    gaps = [R.snap(t)[3] for _x, _y, t in rows[n]]
    return sum(1 for g in gaps if g != 0), max(gaps)


def eps_of(n, rows=None):
    """`epsilon(gap) = 2 max gap`: a rigorous bound on `| true side - model side |`.

    Every square's half-extent is `(|cos t| + |sin t|)/2`, whose derivative in `t` is at most 1
    in absolute value, so moving `t` to its word changes that cell's half-extent by at most the
    gap. The side is `max(x + ex) - min(x - ex)`, so each term moves by at most the largest gap
    and the side by at most twice it. Coarse on purpose: it must never under-estimate.
    """
    _cnt, gap = gaps_of(n, rows)
    return 2 * F(gap)


def q_dec(x, digits=30):
    """A `Q(sqrt 2)` value as a decimal string at `digits` places, by integer arithmetic."""
    v = F(x.a) + F(x.b) * sqrt2_frac()
    q = v * 10 ** digits
    if q >= 0:
        scaled = (q.numerator + q.denominator // 2) // q.denominator
    else:
        scaled = -((-q.numerator + q.denominator // 2) // q.denominator)
    sign = "-" if scaled < 0 else ""
    whole, frac = divmod(abs(scaled), 10 ** digits)
    return f"{sign}{whole}.{frac:0{digits}d}"


def word_angle(w):
    """The exact angle of a word, as `k pi / 4` at the working precision (no float)."""
    from decimal import Decimal as D
    pairs = [(Q2(F(1)), Q2(F(0))), (H, H), (Q2(F(0)), Q2(F(1))), (-H, H),
             (Q2(F(-1)), Q2(F(0))), (-H, -H), (Q2(F(0)), Q2(F(-1))), (H, -H)]
    for k, p in enumerate(pairs):
        if w[0] == p[0] and w[1] == p[1]:
            return D(k) * TG.PI / D(4)
    raise AssertionError(("not a word", str(w[0]), str(w[1])))


def dec_of_fraction(f):
    """A rational as a decimal string at the working precision (no float anywhere)."""
    with localcontext() as ctx:
        ctx.prec = TG.DPS
        return str(+Decimal(f.numerator) / Decimal(f.denominator))


def true_check(state, words, angles=None):
    """The true geometry of a `Q(sqrt 2)` pose at 40 digits (no float).

    `angles` are the row's *stored* angles: a translation keeps every angle, so the true side of
    the moved row is measured there. When `angles` is `None` the pose is a re-orientation and is
    measured at its exact word directions `(c, s)` instead.
    """
    if angles is not None:
        st = [(q_dec(x), q_dec(y), dec_of_fraction(F(t)))
              for (x, y), t in zip(state, angles)]
        return TG.check(st)
    st = [(q_dec(x), q_dec(y), q_dec(w[0], 30), q_dec(w[1], 30))
          for (x, y), w in zip(state, words)]
    return TG.check_cs(st)


def containment(n, model_L, state, words, Ldel, rows=None, angles=None):
    """Bound a snapped-model candidate against the true geometry before any promotion.

    The model side is the gate's exact side for the pose whose angles are the eight words; the
    true side is the same pose measured at its word angles at 40 digits. `epsilon(gap)` bounds
    the difference, so a candidate is promoted only when

      * the two agree within `epsilon` (the snap is not hiding a larger effect),
      * the pose is overlap-free at 40 digits,
      * and the *true* side is strictly below the delivered true side.

    That last condition is what run 109 lacked: it compared the model side with the delivered
    side and promoted a win the real geometry did not have.
    """
    eps = F(eps_of(n, rows))
    epsd = Decimal(eps.numerator) / Decimal(eps.denominator)
    if angles is None and rows is not None:
        angles = [t for (_x, _y, t) in rows[n]]
    chk = true_check(state, words, angles)
    Ltrue = chk["side"]
    model = Decimal(q_dec(model_L, 20))
    Ld = Decimal(q_dec(Ldel, 20)) if hasattr(Ldel, "a") else Decimal(str(F(Ldel)))
    out = {"model": q_dec(model_L, 12), "true": str(+Ltrue), "eps": str(eps),
           "gap_ok": abs(Ltrue - model) <= epsd,
           "overlap_free": not chk["violations"],
           "delivered_true": str(+Ld),
           "true_gain": str(+(Ld - Ltrue))}
    out["beats_true"] = bool(Ltrue < Ld)
    out["promotable"] = bool(out["gap_ok"] and out["overlap_free"] and out["beats_true"])
    return out


# ------------------------------------------------------------------ part 2: coupled moves
def sub_clusters(pf, wf, con, maxk=MAXK, cap=SET_CAP):
    """Connected sub-clusters (contact graph) of 2..maxk cells that include a wall cell."""
    adj = {i: set() for i in range(len(pf))}
    for (i, j, _q) in con:
        adj[i].add(j)
        adj[j].add(i)
    wall = set()
    for side in SIDES:
        wall |= set(K.wall_cells([(x, y) for x, y in pf], wf, side))
    out = []
    seen = set()
    for seed in sorted(wall):
        frontier = [{seed}]
        for _k in range(2, maxk + 1):
            nxt = []
            for s in frontier:
                for c in s:
                    for d in adj[c]:
                        if d not in s:
                            ns = frozenset(s | {d})
                            if ns not in seen:
                                seen.add(ns)
                                nxt.append(set(ns))
            for s in nxt:
                out.append(sorted(s))
            frontier = nxt
            if len(out) >= cap:
                return out[:cap]
    return out[:cap]


def move(pf, wf, cells, d, t):
    """Translate every cell of `cells` by `t d`, exactly."""
    inside = set(cells)
    return [(p[0] + t * d[0], p[1] + t * d[1]) if i in inside else p
            for i, p in enumerate(pf)]


def rotate_set(pf, wf, cells, k):
    """Rotate `cells` by `k` x 45 degrees about their own bbox centre; re-orient the words too."""
    inside = set(cells)
    box, _ = K.box_and_edges([(x, y) for x, y in pf], wf)
    sub_lo = min(pf[i][0] for i in inside)
    sub_hi = max(pf[i][0] for i in inside)
    sub_ly = min(pf[i][1] for i in inside)
    sub_hy = max(pf[i][1] for i in inside)
    c = ((sub_lo + sub_hi) * HALF, (sub_ly + sub_hy) * HALF)
    out = [rot_point(p, c, k) if i in inside else p for i, p in enumerate(pf)]
    words = [rot_word(w, k) if i in inside else w for i, w in enumerate(wf)]
    return out, words


def candidate(pf, wf, st, words, tag, Ldel=None, angles=None):
    """Gate a candidate at its own box, squeeze it, and certify it only if it beats `Ldel`.

    Certificates are the expensive part, so screening runs without one (`keep_cert=False`); a
    candidate that clears the gate *and* then squeezes strictly below the delivered side is
    re-gated with a certificate, and only that verified object is reported as a win.
    """
    g = FSL.gate_state(len(st), st, words, keep_cert=False)
    rec = {"move": tag, "ok": g["ok"], "violations": g["violations"], "clearance": None,
           "L": q_st(g["L"]), "L_obj": g["L"]}
    if not g["ok"]:
        return rec
    rec["clearance"] = None if g["clearance"] is None else q_st(g["clearance"])
    st2, hist = FSL.squeeze(st, words)
    g2 = FSL.gate_state(len(st2), st2, words, keep_cert=False)
    rec["L_squeezed"] = q_st(g2["L"])
    rec["slides"] = [h["side"] for h in hist]
    if not g2["ok"]:
        return rec
    rec["L_final"] = q_st(g2["L"])
    rec["L_final_obj"] = g2["L"]
    rec["beats"] = False if Ldel is None else bool(g2["L"] < Ldel)
    if rec["beats"]:
        rec["containment"] = containment(len(pf), g2["L"], st2, words, Ldel, angles=angles)
        rec["promotable"] = rec["containment"]["promotable"]
        g3 = FSL.gate_state(len(st2), st2, words, keep_cert=True)
        cert = g3["certificate"] or {}
        rec["certificate"] = cert.get("status")
        rec["cert_clearance"] = cert.get("clearance")
        rec["state"] = [[q_st(x), q_st(y)] for x, y in st2]
    return rec


def search_row(n, rows=None, maxk=MAXK, cap=SET_CAP):
    """Every coupled move this module can express on one row, judged by the gate."""
    rows = rows or C.load_rows()
    pf, wf, gap = state_of(n, rows)
    tab = json.load(open(TAB), parse_float=str)
    Ldel = F(str(tab[str(n)]["L"]))
    rec = {"n": n, "N": len(pf), "L_delivered": str(Ldel), "word_gap": str(gap),
           "attacks": [], "wins": [], "kinds": {}}
    sv = survey(pf, wf)
    rec["start_violations"] = len(sv["violations"])
    if sv["violations"]:
        pf, sv, nst = repair(pf, wf, sv)
        rec["steps"] = nst
        if pf is None:
            rec["verdict"] = "repair-stalled"
            rec["left"] = len(sv["violations"])
            return rec
    rec["clean"] = True
    rec["L_clean"] = str(side_of(pf, wf))
    con = contacts(pf, wf)
    angle_row = [t for (_x, _y, t) in rows[n]]
    sets = sub_clusters(pf, wf, con, maxk=maxk, cap=cap)
    rec["clusters"] = len(sets)
    for cells in sets:
        for kind in DIRS8:
            d = K.direction(kind)
            T, binder, note = FSL.face_room(pf, wf, cells, d)
            if note is not None or T is None or T.sign() <= 0:
                continue
            c = candidate(pf, wf, move(pf, wf, cells, d, T), wf,
                          {"kind": "rigid", "cells": cells, "dir": kind, "t": str(T)}, Ldel,
                          angles=angle_row)
            rec["attacks"].append(c)
            rec["kinds"]["rigid"] = rec["kinds"].get("rigid", 0) + 1
            if c.get("promotable"):
                rec["wins"].append(c)
    for cells in sets:
        for k in (1, 2):
            st, words = rotate_set(pf, wf, cells, k)
            c = candidate(pf, wf, st, words,
                          {"kind": "reorient", "cells": cells, "turn": k * 45}, Ldel,
                          angles=None)
            rec["attacks"].append(c)
            rec["kinds"]["reorient"] = rec["kinds"].get("reorient", 0) + 1
            if c.get("promotable"):
                rec["wins"].append(c)
    for side in SIDES:
        pin_map = pins(pf, wf, side, con)
        d = K.inward(side)
        for wc, blocked in pin_map.items():
            for b in blocked:
                # the trade: push the *pin* into the void behind it by its own full room; the
                # wall cell it was holding is then free, and the squeeze that follows pulls the
                # wall in by whatever the pin's retreat opened.  Not a rigid move -- only the
                # pin travels, by a different amount than the wall would.
                Tb, _bb, note_b = FSL.face_room(pf, wf, [b["cell"]], d)
                if note_b is not None or Tb is None or Tb.sign() <= 0:
                    continue
                T = Tb
                st = [(p[0] + T * d[0], p[1] + T * d[1]) if i == b["cell"] else p
                      for i, p in enumerate(pf)]
                c = candidate(pf, wf, st, wf,
                              {"kind": "trade", "wall": wc, "pin": b["cell"],
                               "side": side, "t": str(T)}, Ldel, angles=angle_row)
                rec["attacks"].append(c)
                rec["kinds"]["trade"] = rec["kinds"].get("trade", 0) + 1
                if c.get("L_final") and F(c["L_final"]) < Ldel:
                    rec["wins"].append(c)
    ok = [a for a in rec["attacks"] if a.get("ok")]
    bestv = min((a["L_final_obj"] for a in ok if a.get("L_final_obj")), default=None)
    rec["best"] = None if bestv is None else q_st(bestv)
    cert = [a for a in rec["attacks"] if a.get("certificate") == "verified"]
    rec["model_wins"] = sum(1 for a in rec["attacks"] if a.get("beats"))
    rec["rejected"] = sum(1 for a in rec["attacks"] if a.get("beats") and not a.get("promotable"))
    rec["tally"] = {"attacks": len(rec["attacks"]), "legal": len(ok),
                    "verified": len(cert), "wins": len(rec["wins"])}
    rec["verdict"] = "improves" if rec["wins"] else "no-improvement"
    return rec


def trades_row(n, rows=None):
    """Only the void-trade family, for every pin of the row's clean pose."""
    rows = rows or C.load_rows()
    pf, wf, _gap = state_of(n, rows)
    tab = json.load(open(TAB), parse_float=str)
    Ldel = F(str(tab[str(n)]["L"]))
    rec = {"n": n, "N": len(pf), "L_delivered": str(Ldel), "trades": []}
    sv = survey(pf, wf)
    if sv["violations"]:
        pf, sv, _n = repair(pf, wf, sv)
        if pf is None:
            rec["verdict"] = "repair-stalled"
            return rec
    con = contacts(pf, wf)
    angle_row = [t for (_x, _y, t) in rows[n]]
    for side in SIDES:
        d = K.inward(side)
        for wc, blocked in pins(pf, wf, side, con).items():
            for b in blocked:
                Tb, _bb, note_b = FSL.face_room(pf, wf, [b["cell"]], d)
                if note_b is not None or Tb is None or Tb.sign() <= 0:
                    continue
                st = [(p[0] + Tb * d[0], p[1] + Tb * d[1]) if i == b["cell"] else p
                      for i, p in enumerate(pf)]
                c = candidate(pf, wf, st, wf,
                              {"kind": "trade", "wall": wc, "pin": b["cell"], "side": side,
                               "t": str(Tb)}, Ldel)
                rec["trades"].append(c)
    legal = [c for c in rec["trades"] if c.get("ok")]
    rec["tally"] = {"trades": len(rec["trades"]), "legal": len(legal),
                    "beats": sum(1 for c in legal if c.get("beats"))}
    bv = min((c["L_final_obj"] for c in legal if c.get("L_final_obj")), default=None)
    rec["best"] = None if bv is None else q_st(bv)
    rec["verdict"] = "improves" if rec["tally"]["beats"] else "no-improvement"
    return rec


def run_trades(targets=TARGETS):
    rows = C.load_rows()
    out = {"rows": {}, "seconds": None}
    t0 = time.time()
    for n in targets:
        rec = trades_row(n, rows)
        out["rows"][str(n)] = rec
        print(f"  n={n}: {rec['verdict']} tally={rec.get('tally')} best={rec.get('best')}")
    out["seconds"] = str(F(time.time() - t0).limit_denominator(100))
    return out


def run_guard(targets=TARGETS):
    """Part 2's audit: bound every recorded model win against the true geometry, and the bars."""
    rows = C.load_rows()
    led = json.load(open(OUT)) if os.path.exists(OUT) else {}
    out = {"rows": {}, "recorded": [], "seconds": None}
    t0 = time.time()
    for n in targets:
        cnt, gap = gaps_of(n, rows)
        eps = eps_of(n, rows)
        Ldel = Q2(F(str(json.load(open(TAB), parse_float=str)[str(n)]["L"])))
        bar = Ldel - Q2(eps)             # the model side must be below this to be promotable
        rec = {"n": n, "non_word": cnt, "gap": str(gap), "eps": str(eps),
               "delivered_true": str(Ldel), "model_bar": str(bar)}
        out["rows"][str(n)] = rec
        print(f"  n={n:4d}: {cnt:3d} non-word, gap {gap}, eps {q_dec(Q2(eps), 18)}, "
              f"L_true {q_dec(Ldel, 12)}, model bar {q_dec(bar, 12)}")
    for n, r in (led.get("search", {}).get("rows", {}) or {}).items():
        for w in r.get("wins", []):
            if not w.get("state"):
                continue
            st = [(q_parse(a), q_parse(b)) for a, b in w["state"]]
            _pf, wf, _g = state_of(int(n), rows)
            Ldel = Q2(F(str(json.load(open(TAB), parse_float=str)[n]["L"])))
            con = containment(int(n), q_parse(w["L_final"]), st, wf, Ldel, rows,
                              angles=None if w.get("move", {}).get("kind") == "reorient"
                              else [t for (_x, _y, t) in rows[int(n)]])
            out["recorded"].append({"n": int(n), "move": w.get("move"), **con})
            print(f"  recorded n={n}: model {con['model']} true {con['true']} eps {con['eps']}"
                  f" -> gap_ok {con['gap_ok']} overlap_free {con['overlap_free']}"
                  f" beats_true {con['beats_true']} PROMOTABLE {con['promotable']}")
    out["seconds"] = str(F(time.time() - t0).limit_denominator(100))
    out["verdict"] = ("no recorded model win is promotable"
                      if not any(r["promotable"] for r in out["recorded"]) else "a win survives")
    print("  guard:", out["verdict"])
    return out


def run_search(targets=TARGETS):
    start = time.time()
    rows = C.load_rows()
    out = {"rows": {}, "seconds": None}
    for n in targets:
        rec = search_row(n, rows)
        out["rows"][str(n)] = rec
        print(f"  n={n}: {rec['verdict']} kinds={rec.get('kinds')} tally={rec.get('tally')}")
    out["seconds"] = str(F(time.time() - start).limit_denominator(100))
    return out


# ------------------------------------------------------------------ controls
def selftest():
    """Three controls: the graph's edge cases, a rigid move, and the 45 degree re-orientation."""
    w0 = R.snap(F(0))[2]
    # control 1 -- a 2x2 block: four contacts, every cell pinned on both of its axes, no pockets.
    pf = [(F(1, 2), F(1, 2)), (F(3, 2), F(1, 2)), (F(1, 2), F(3, 2)), (F(3, 2), F(3, 2))]
    wf = [w0] * 4
    con = contacts([(C._q(x), C._q(y)) for x, y in pf], wf)
    assert len(con) == 6, len(con)      # four side contacts and the two corner contacts
    pm = {s: pins([(C._q(x), C._q(y)) for x, y in pf], wf, s, con) for s in SIDES}
    assert all(v for s in SIDES for v in pm[s].values()), "every wall cell must be pinned"
    assert rooms([(C._q(x), C._q(y)) for x, y in pf], wf) == [], "no cell may have room"
    # control 2 -- a rigid two-cell move: a wall pair with a single blocker each, so shifting the
    # pair outward by the exact room keeps every pair legal and the gate certifies the result.
    # (inside the gate's |dx| < 2 prune, so the pair is a real cap and not "unbounded")
    pf2 = [(F(1, 2), F(1, 2)), (F(1, 2), F(3, 2)), (F(19, 10), F(1, 2)), (F(19, 10), F(3, 2))]
    wf2 = [w0] * 4
    p2 = [(C._q(x), C._q(y)) for x, y in pf2]
    T, binder, note = FSL.face_room(p2, wf2, [0, 1], K.direction("x"))
    assert note is None and T is not None and T.sign() > 0, (T, note)
    st = move(p2, wf2, [0, 1], K.direction("x"), T)
    g = FSL.gate_state(4, st, wf2)
    assert g["ok"] and g["clearance"].sign() == 0, g
    # control 3 -- the 45 degree re-orientation stays in the field and is the word's own rotation.
    w45 = (H, H)                                              # (sqrt2/2, sqrt2/2) at 45 degrees
    r1 = rot_word(w45, 1)
    assert r1 == (Q2(F(0)), Q2(F(1))), r1                      # 45 + 45 = 90 degrees = (0, 1)
    assert rot_word(w0, 2) == (Q2(F(0)), Q2(F(1)))             # 0 + 90 = (0, 1)
    assert rot_word(w0, 4) == (Q2(F(-1)), Q2(F(0)))            # 0 + 180 = (-1, 0)
    pt = rot_point((Q2(F(2)), Q2(F(0))), (Q2(F(0)), Q2(F(0))), 2)
    assert pt == (Q2(F(0)), Q2(F(2))), pt                      # a quarter turn about the origin
    print("control 1 -- a 2x2 block: 6 contacts (four sides, two corners), every wall cell pinned on "
          "its inward axis, and no wall cell with room, so the relational graph says 'locked'.")
    print("control 2 -- a rigid two-cell move: the pair's exact room is positive, the move keeps "
          "every pair legal, and the gate certifies it at clearance 0.")
    print("control 3 -- re-orientation: 45 + 45 = 90, 0 + 90 = 90 and 0 + 180 = 180 exactly in "
          "Q(sqrt 2), and a quarter turn about the origin maps (2, 0) to (0, 2).")
    # control 4 -- the containment guard: eps is twice the gap, and a model win inside that
    # budget is refused even when the gate certifies it.
    fake = {7: [(F(0), F(0), F(0)), (F(1), F(0), F(0)),
                (F(2), F(0), F(3141592653589793, 4000000000000000) + F(1, 100))]}
    cnt, gap = gaps_of(7, fake)
    assert cnt == 1 and F(gap) > 0, (cnt, gap)          # one angle is off its word
    eps = eps_of(7, fake)
    assert eps == 2 * F(gap), (eps, gap)                # epsilon is exactly twice the gap
    st = [(Q2(F(1, 2)), Q2(F(1, 2))), (Q2(F(3, 2)), Q2(F(1, 2)))]
    words = [(Q2(F(1)), Q2(F(0))), (H, H)]
    con = containment(7, Q2(F(2) - 2 * eps), st, words, Q2(F(2)), fake)
    assert con["gap_ok"] is False, con          # a gain of 2 eps is outside the budget
    assert con["promotable"] is False, con
    con2 = containment(7, Q2(F(2) - eps / 2), st, words, Q2(F(2)), fake)
    assert con2["gap_ok"] is True, con2         # inside the budget ...
    assert con2["beats_true"] is False and con2["promotable"] is False, con2   # ... but no gain
    print("control 4 -- the containment guard: epsilon is exactly twice the row's largest angle "
          "gap; a gain twice epsilon fails the budget, and a gain of eps/2 passes it yet is still "
          "refused because the true geometry at 40 digits is not below the delivered side.")
    print("semantic_pack: OK (4 controls)")


# ------------------------------------------------------------------ the run
def _clean(o):
    """Drop the live field objects (`*_obj`) a record carries for arithmetic; keep the strings."""
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items() if not k.endswith("_obj")}
    if isinstance(o, list):
        return [_clean(v) for v in o]
    return o


def merge(section, data):
    led = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            led = json.load(f)
    led.setdefault("run", 109)
    led.setdefault("delivered", "22.218056945")
    led["sections"] = sorted(set(led.get("sections", [])) | {section})
    led[section] = _clean(data)
    with open(OUT, "w") as f:
        json.dump(led, f, indent=1)
    print(f"semantic_pack: {section} -> {OUT}")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        selftest()
        return
    if "--guard" in argv:
        merge("guard", run_guard())
        return
    if "--trades" in argv:
        merge("trades", run_trades())
        return
    do_all = not any(a in argv for a in ("--analyse", "--search"))
    if "--analyse" in argv or do_all:
        merge("analyse", run_analyse())
    if "--search" in argv or do_all:
        merge("search", run_search())
    return


if __name__ == "__main__":
    main()
