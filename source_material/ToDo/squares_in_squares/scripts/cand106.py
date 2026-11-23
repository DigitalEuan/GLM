#!/usr/bin/env python3
r"""cand106.py — batch certification, the 45-degree repair, and the coupled two-cell move.

Run 105 closed the *extent* lever (no word relabelling can lower a side whose bbox is set
by axis cells) and left three things to do.  This script is all three, and each is exact.

PART 1 -- batch slide-to-contact.  A row whose stored angles *are* exact words and whose
pose gates clean is a packing but not a *sentence*: the table's `1e-9` polish shim leaves
the clearance positive, and the certificate schema wants a contact.  One exact slide to
the nearest contact (by that pair's own unit axis, by exactly its slack) closes it.  This
part screens the whole census, surveys every exact row in one exact pass (violations *and*
the tightest positive slack in the same loop, in `Q` when the row's words are rational),
slides the clean ones and verifies a certificate for each.  The ledger keeps a compact
per-row line plus the full certificate of three representatives, so the count can be
re-checked with `verify_certificates.py` without re-running the batch.

PART 2 -- the positional repair, extended to the 45 degree word.  Run 104 moved a cell
along an axis by a rational `t`; a 45 degree square's own axes are `(1,1)/sqrt2` and
`(-1,1)/sqrt2`, so the same construction runs in `Q(sqrt 2)` with the step projected on
those axes.  The step is exact: for each of the pair's eight axes the separation is linear
in `t`, the smallest `t` that clears the axis is a quotient of field elements, and the
gate -- not the algebra -- accepts or refuses.  Applied to n = 330 (6 overlaps) and
n = 332 (159).

PART 3 -- the coupled two-cell move.  Doc 66 section 7's next idea, prototyped: move an
interior cell out to a *new* contact, then pull the wall cell that sets the bbox inward by
the room that creates.  If the second move is positive the side strictly shrinks -- the
only way left to beat a row whose extent bound is tight.  Tested on n = 66 and n = 325,
both certified in part 1.

READ-ONLY: `workspace/push/cand106.json`.  `submission.csv` and the root `WHITEBOARD.md`
are never opened for writing, and no score is claimed.

USAGE
    python3 scripts/cand106.py --selftest
    python3 scripts/cand106.py --batch
    python3 scripts/cand106.py --repair
    python3 scripts/cand106.py --couple
    python3 scripts/cand106.py            # all three
"""
from __future__ import annotations

import json
import os
import sys
import time
from decimal import Decimal, getcontext
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import cand105 as C                # noqa: E402
import rat47 as R                  # noqa: E402
import field_triage as FT          # noqa: E402
import qsqrt2 as Q                 # noqa: E402
import verify_certificates as VC   # noqa: E402

getcontext().prec = 70

OUT = os.path.join(ROOT, "workspace/push/cand106.json")
Q2 = C.Q2
HALF = F(1, 2)
SNAP_TOL = Decimal("1e-9")         # a stored angle is an exact word within this distance
SAMPLE_CERTS = 3                   # full certificates kept in the ledger for re-checking
ROUNDING = F(1, 10 ** 6)
ZERO, ONE = Q2(F(0)), Q2(F(1))


# ------------------------------------------------------------------ the exact survey
def survey(pf, wf):
    """One exact pass: every overlapping pair, and the tightest *separated* pair.

    The tightest one is what the slide needs -- its own axis, its own slack -- and the
    violations are what part 2 repairs, so a row costs one pass and not two.
    """
    n = len(pf)
    viol, tight = [], None
    for i in range(n):
        xi, yi = pf[i]
        for j in range(i + 1, n):
            if abs(pf[j][0] - xi) >= 2 or abs(pf[j][1] - yi) >= 2:
                continue
            dx = C._q(pf[j][0]) - C._q(xi)
            dy = C._q(pf[j][1]) - C._q(yi)
            best, bq, bproj = None, None, None
            for owner, other in ((i, j), (j, i)):
                for q in C.axes_q(wf[owner]):
                    proj = dx * q[0] + dy * q[1]
                    sl = abs(proj) - (Q2(HALF) + C.support(wf[other], q, Q2))
                    if best is None or sl > best:
                        best, bq, bproj = sl, (owner, other, q), proj
            if best is None:
                continue
            if best.sign() < 0:
                viol.append([i, j, str(best)])
            elif tight is None or best < tight[0]:
                tight = (best, i, j, bq, bproj)
    return {"violations": viol, "tight": tight}


def survey_rat(pf, wf, wfF):
    """The same survey in `Q`, for a row whose words are all rational: about twice as fast."""
    n = len(pf)
    viol, tight = [], None
    for i in range(n):
        xi, yi = pf[i]
        for j in range(i + 1, n):
            if abs(pf[j][0] - xi) >= 2 or abs(pf[j][1] - yi) >= 2:
                continue
            dx, dy = pf[j][0] - xi, pf[j][1] - yi
            best, bq, bproj = None, None, None
            for owner, other in ((i, j), (j, i)):
                oc, os_ = wfF[other]
                for qx, qy in ((wfF[owner][0], wfF[owner][1]),
                               (-wfF[owner][1], wfF[owner][0])):
                    proj = dx * qx + dy * qy
                    need = HALF + (abs(oc * qx + os_ * qy) + abs(oc * qy - os_ * qx)) * HALF
                    sl = abs(proj) - need
                    if best is None or sl > best:
                        best, bq, bproj = sl, (owner, other, (qx, qy)), proj
            if best is None:
                continue
            if best < 0:
                viol.append([i, j, str(best)])
            elif tight is None or best < tight[0]:
                tight = (C._q(best), i, j, bq, C._q(bproj))
    return {"violations": viol, "tight": tight}


def survey_row(pf, wf):
    """`survey`, by the fast path when the words allow it."""
    if all(w[0].b == 0 and w[1].b == 0 for w in wf):
        return survey_rat(pf, wf, [(w[0].a, w[1].a) for w in wf])
    return survey(pf, wf)


def slide(pf, wf, sv):
    """The exact state after sliding to the tightest contact, or `None` if already tight."""
    if sv["tight"] is None:
        return None
    slack, _i, j, (owner, _other, q), proj = sv["tight"]
    if slack.sign() <= 0:
        return None
    step = -slack if proj.sign() > 0 else slack
    out = list(pf)
    out[j] = (C._q(pf[j][0]) + step * q[0], C._q(pf[j][1]) + step * q[1])
    return {"state": out, "cell": j, "slack": str(slack),
            "axis": [str(q[0]), str(q[1])], "owner": owner,
            "shift": [str(step * q[0]), str(step * q[1])]}


def slide_best(pf, wf, sv):
    """Slide to a genuine contact: the smallest step along a direction that closes *every*
    positive axis of the tightest pair.

    One axis is not enough when the pair is a diagonal one: its x and y separations can
    both be positive, and a single-axis move leaves the other positive, so the pair stays
    separated and the sentence has no contact.  Trying all eight signed directions and
    taking the one whose largest required step is smallest closes them together.
    """
    if sv["tight"] is None:
        return None
    slack, i, j, _q0, _p0 = sv["tight"]
    best = None
    for kind in DIRS8:
        d = direction(kind)
        t, okdir = None, True
        for proj, need, q in pair_axes(pf, wf, i, j):
            gap = abs(proj) - need
            if gap.sign() <= 0:
                continue                      # this axis is already closed
            dq = d[0] * q[0] + d[1] * q[1]
            if dq.sign() == 0 or (proj.sign() * dq.sign()) >= 0:
                okdir = False                 # the move widens (or misses) this axis
                break
            need_t = gap / abs(dq)
            if t is None or need_t > t:
                t = need_t
        if not okdir or t is None or t.sign() <= 0:
            continue
        out = list(pf)
        out[j] = (C._q(pf[j][0]) + t * d[0], C._q(pf[j][1]) + t * d[1])
        if best is None or t < best[0]:
            best = (t, {"state": out, "cell": j, "slack": str(slack),
                        "direction": kind, "t": str(t),
                        "shift": [str(t * d[0]), str(t * d[1])]})
    return None if best is None else best[1]


def certify_state(n, st, wf):
    """Gate a Q(sqrt 2) sentence in its own box, and build and verify its certificate."""
    lo_x = min(st[i][0] - C.extent_of(wf[i], Q2) for i in range(n))
    lo_y = min(st[i][1] - C.extent_of(wf[i], Q2) for i in range(n))
    sh = [(st[i][0] - lo_x, st[i][1] - lo_y) for i in range(n)]
    g = Q.gate(sh, wf, Q2)
    rec = {"ok": bool(g["ok"]), "L": str(g["L"]), "contacts": g["contacts"],
           "violations": g["violations"],
           "clearance": None if g["clearance"] is None else str(g["clearance"]),
           "certificate": None, "cert_obj": None}
    if g["ok"] and g["clearance"] is not None and g["clearance"].sign() == 0:
        cert = C.cert_quad(2, n, sh, wf, g["L"], g["contacts"])
        try:
            v = VC.verify_certificate(cert)
            rec["certificate"] = {"status": v["status"], "N": v["N"],
                                  "contacts": v["contacts"], "L": v["L"],
                                  "clearance": v["clearance"], "void": v["void"]}
            rec["cert_obj"] = cert
        except VC.Failure as f:
            rec["certificate"] = {"status": "refused", "kind": f.kind,
                                  "check": f.check, "detail": f.detail}
    return rec


# ------------------------------------------------------------- PART 1: the batch
def exact_screen(row, dec_alphabet):
    """The row's worst word distance, from its few distinct angles."""
    worst = Decimal(0)
    cache = {}
    for _x, _y, t in row:
        if t not in cache:
            dc, ds = FT.cos_sin(t)
            cache[t] = min(max(abs(dc - ec), abs(ds - es)) for _n, (ec, es) in dec_alphabet)
        if cache[t] > worst:
            worst = cache[t]
    return worst


def certify_row(n, row):
    """Screen, survey, slide and certify one row; the record the ledger keeps."""
    pf = [(x, y) for x, y, _t in row]
    wf = [R.snap(t)[2] for _x, _y, t in row]
    sv = survey_row(pf, wf)
    rec = {"n": n, "N": len(pf), "violations": len(sv["violations"]),
           "tightest": None, "slide": None, "L": None, "contacts": None,
           "certificate": None, "cert_obj": None, "verdict": None}
    if sv["tight"] is not None:
        rec["tightest"] = str(sv["tight"][0])
    if sv["violations"]:
        rec["verdict"] = "not-clean"
        return rec
    sl = slide_best(pf, wf, sv)
    if sl is None:
        rec["verdict"] = "already-tight"
        return rec
    rep = certify_state(n, sl["state"], wf)
    rec["slide"] = {k: sl[k] for k in ("cell", "slack", "direction", "t", "shift")}
    rec["L"] = rep["L"]
    rec["contacts"] = rep["contacts"]
    rec["clearance"] = rep["clearance"]
    rec["certificate"] = rep["certificate"]
    rec["cert_obj"] = rep["cert_obj"]
    if rep["certificate"] and rep["certificate"].get("status") == "verified":
        rec["verdict"] = "certified"
    else:
        rec["verdict"] = "gated-not-certified"
    return rec


def batch(rows, dec_alphabet, budget=None):
    """Every exact-worded row: survey, slide, certify.  `budget` is a wall-clock cap."""
    start = time.time()
    out = {"rows": [], "tally": {"census": 0, "not_clean": 0, "certified": 0,
                                 "already_tight": 0, "other": 0},
           "samples": [], "seconds": None}
    for n in sorted(rows):
        if exact_screen(rows[n], dec_alphabet) > SNAP_TOL:
            continue
        out["tally"]["census"] += 1
        rec = certify_row(n, rows[n])
        if rec["cert_obj"] is not None and len(out["samples"]) < SAMPLE_CERTS:
            out["samples"].append({"n": n, "certificate": rec["cert_obj"]})
        rec.pop("cert_obj", None)
        out["rows"].append(rec)
        key = {"certified": "certified", "not-clean": "not_clean",
               "already-tight": "already_tight"}.get(rec["verdict"], "other")
        out["tally"][key] += 1
        if budget is not None and time.time() - start > budget:
            out["truncated_at"] = n
            break
    out["seconds"] = str(Decimal(time.time() - start).quantize(Decimal("0.01")))
    return out


# ------------------------------------------------- PART 2: the 45 degree repair
DIRS = ("x", "y", "diag", "anti")
DIRS8 = DIRS + tuple("-" + k for k in DIRS)


def direction(kind):
    """The eight signed translation directions, exactly.

    `x`, `y` and the two diagonals, each with its negative: `(+-1,0)`, `(0,+-1)`,
    `+-(1,1)/sqrt2` and `+-(1,-1)/sqrt2`, where `(1,1)/sqrt2` is the field element
    `(0, 1/2)` in `Q(sqrt 2)` and never a decimal.
    """
    if kind.startswith("-"):
        d = direction(kind[1:])
        return (-d[0], -d[1])
    if kind == "x":
        return (ONE, ZERO)
    if kind == "y":
        return (ZERO, ONE)
    h = Q2(ZERO.a, HALF)                     # 0 + (1/2) sqrt 2, the exact (sqrt2)/2
    return (h, h) if kind == "diag" else (-h, h)


def pair_axes(pf, wf, i, j):
    """The eight `(projection, need, axis)` rows of pair `(i, j)`, exactly in Q(sqrt 2)."""
    dx = C._q(pf[j][0]) - C._q(pf[i][0])
    dy = C._q(pf[j][1]) - C._q(pf[i][1])
    out = []
    for owner, other in ((i, j), (j, i)):
        for q in C.axes_q(wf[owner]):
            out.append((dx * q[0] + dy * q[1],
                        Q2(HALF) + C.support(wf[other], q, Q2), q))
    return out


def repair_step(pf, wf, i, j):
    """The smallest exact slide of `i` or `j` that separates the offending pair.

    For a direction `d` and a moving cell `c`, the projection of each of the pair's axes
    changes at the constant rate `k = +-(d.q)`, so the step that clears that axis is
    `(sign(proj) need - proj) / k` and its size is `(need - |proj|) / |k|`.  The smallest
    size over the eight axes is the candidate for that direction; the gate decides whether
    the move kept every other pair legal.
    """
    best = None
    for kind in DIRS:
        d = direction(kind)
        for cell in (i, j):
            take = None
            for proj, need, q in pair_axes(pf, wf, i, j):
                dq = d[0] * q[0] + d[1] * q[1]
                if dq.sign() == 0:
                    continue
                k = dq if cell == j else -dq
                sgn = ONE if proj.sign() >= 0 else -ONE
                t = (sgn * need - proj) / k
                if t.sign() == 0:
                    continue
                if take is None or abs(t) < take[2]:
                    take = (t, q, abs(t))
            if take is None:
                continue
            t, q, size = take
            out = list(pf)
            out[cell] = (C._q(pf[cell][0]) + t * d[0], C._q(pf[cell][1]) + t * d[1])
            if best is None or size < best[0]:
                best = (size, {"state": out, "cell": cell, "direction": kind,
                               "t": str(t), "axis": [str(q[0]), str(q[1])],
                               "pair": [i, j]})
    return None if best is None else best[1]


def repair45(n, row, cap=4):
    """Run 104's loop with the 45 degree directions: fix the worst pair, keep what gates."""
    pf = [(x, y) for x, y, _t in row]
    wf = [R.snap(t)[2] for _x, _y, t in row]
    sv = survey_row(pf, wf)
    rec = {"n": n, "N": len(pf), "start_violations": len(sv["violations"]),
           "start": sv["violations"][:6], "steps": [], "verdict": None,
           "certificate": None}
    cur = pf
    for step in range(cap):
        bad = survey_row(cur, wf)["violations"]
        if not bad:
            break
        i, j = bad[0][0], bad[0][1]
        mv = repair_step(cur, wf, i, j)
        if mv is None:
            rec["steps"].append({"pair": [i, j], "verdict": "no-direction"})
            break
        g = C.gate2(mv["state"], wf)
        rec["steps"].append({"pair": [i, j], "cell": mv["cell"],
                             "direction": mv["direction"], "t": mv["t"],
                             "axis": mv["axis"], "violations_after": g["violations"],
                             "ok": bool(g["ok"]), "clearance": str(g["clearance"])})
        if g["violations"] >= len(bad):
            rec["stopped"] = "the move did not lower the overlap count"
            break
        cur = mv["state"]
    fin = survey_row(cur, wf)
    rec["end_violations"] = len(fin["violations"])
    rep = certify_state(n, [(C._q(x), C._q(y)) for x, y in cur], wf)
    rec["L"] = rep["L"]
    rec["contacts"] = rep["contacts"]
    rec["clearance"] = rep["clearance"]
    rec["certificate"] = rep["certificate"]
    if rep["certificate"] and rep["certificate"].get("status") == "verified":
        rec["verdict"] = "certified"
    elif rep["ok"]:
        rec["verdict"] = "gated-not-certified"
    else:
        rec["verdict"] = "refused"
        rec["why"] = {"violations": rep["violations"], "clearance": rep["clearance"]}
    return rec


# ------------------------------------------------ PART 3: the coupled two-cell move
SIDES = ("lo_x", "hi_x", "lo_y", "hi_y")


def box_and_edges(pf, wf):
    """The exact container box of the pose and each cell's four bbox edges."""
    n = len(pf)
    edges = []
    for i in range(n):
        e = C.extent_of(wf[i], Q2)
        x, y = C._q(pf[i][0]), C._q(pf[i][1])
        edges.append({"lo_x": x - e, "hi_x": x + e, "lo_y": y - e, "hi_y": y + e})
    lo_x = min(e["lo_x"] for e in edges)
    lo_y = min(e["lo_y"] for e in edges)
    hi_x = max(e["hi_x"] for e in edges)
    hi_y = max(e["hi_y"] for e in edges)
    return (lo_x, lo_y, hi_x, hi_y), edges


def wall_cells(pf, wf, side):
    """The cells that realise one side of the bbox."""
    _box, edges = box_and_edges(pf, wf)
    vals = [e[side] for e in edges]
    m = min(vals) if side.startswith("lo") else max(vals)
    return [i for i in range(len(pf)) if vals[i] == m]


def inward(side):
    """The unit vector that pulls a cell off the given wall."""
    return {"lo_x": (ONE, ZERO), "hi_x": (-ONE, ZERO),
            "lo_y": (ZERO, ONE), "hi_y": (ZERO, -ONE)}[side]


def wall_room(pf, wf, cell, d):
    """The largest exact `t` for which moving `cell` by `t d` keeps the pose legal.

    Walls give a cap per axis.  For a pair, each of the eight axes is separated at `t = 0`
    with some slack and fails at `slack / |d.q|` if the motion narrows the projection, or
    never if it widens it; the pair survives while **some** axis survives, so the pair's
    cap is the largest of those failure times.
    """
    box, _edges = box_and_edges(pf, wf)
    lo_x, lo_y, hi_x, hi_y = box
    n = len(pf)
    x, y = C._q(pf[cell][0]), C._q(pf[cell][1])
    e = C.extent_of(wf[cell], Q2)
    caps = []
    for comp, got, lo, hi in ((d[0], x, lo_x, hi_x), (d[1], y, lo_y, hi_y)):
        if comp.sign() > 0:
            caps.append((hi - got - e) / comp)
        elif comp.sign() < 0:
            caps.append((got - e - lo) / (-comp))
    for k in range(n):
        if k == cell:
            continue
        pair_cap = None
        for proj, need, q in pair_axes(pf, wf, cell, k):
            dq = d[0] * q[0] + d[1] * q[1]
            if dq.sign() == 0:
                continue
            kq = -dq                       # the projection moves at `-t d.q`
            slack = abs(proj) - need
            if slack.sign() < 0:
                pair_cap = ZERO
                break
            narrowing = (proj.sign() * kq.sign()) < 0
            if not narrowing:
                continue                   # this axis only widens: it never fails
            cap = slack / abs(kq)
            if pair_cap is None or cap > pair_cap:
                pair_cap = cap
        if pair_cap is not None:
            caps.append(pair_cap)
    if not caps:
        return None
    return min(caps)


def couple(n, row):
    """Slide an interior cell onto a new contact, then pull the bbox wall cell inward."""
    pf = [(x, y) for x, y, _t in row]
    wf = [R.snap(t)[2] for _x, _y, t in row]
    sv = survey_row(pf, wf)
    base = {"n": n, "N": len(pf), "violations": len(sv["violations"]),
            "L_base": str(C.bbox_side(pf, wf)), "moves": [], "best": None,
            "verdict": None, "slide": None, "L_certified": None}
    if sv["violations"]:
        base["verdict"] = "not-clean: a coupled move needs a certified sentence first"
        return base
    sl = slide(pf, wf, sv)
    st = sl["state"] if sl is not None else [(C._q(x), C._q(y)) for x, y in pf]
    if sl is not None:
        base["slide"] = {k: sl[k] for k in ("cell", "slack", "shift")}
    L0 = C.bbox_side(st, wf)
    base["L_certified"] = str(L0)
    nb = R.neighbours(pf)
    stats = {"combos": 0, "tau_zero": 0, "gate1_fail": 0, "delta_zero": 0,
             "complete": 0, "walls": 0, "partners": 0}
    max_tau, max_delta = None, None
    for side in SIDES:
        d = inward(side)
        walls = wall_cells(st, wf, side)
        stats["walls"] += len(walls)
        for w in walls:
            stats["partners"] += len(nb[w])
            for p in nb[w]:
                for kind in DIRS8:
                    dp = direction(kind)
                    stats["combos"] += 1
                    tau = wall_room(st, wf, p, dp)
                    if tau is not None and (max_tau is None or tau > max_tau):
                        max_tau = tau
                    if tau is None or tau.sign() <= 0:
                        stats["tau_zero"] += 1
                        continue
                    st1 = list(st)
                    st1[p] = (st[p][0] + tau * dp[0], st[p][1] + tau * dp[1])
                    g1 = C.gate2(st1, wf)
                    if not g1["ok"]:
                        stats["gate1_fail"] += 1
                        continue
                    delta = wall_room(st1, wf, w, d)
                    if delta is not None and (max_delta is None or delta > max_delta):
                        max_delta = delta
                    if delta is None or delta.sign() <= 0:
                        stats["delta_zero"] += 1
                        continue
                    stats["complete"] += 1
                    st2 = list(st1)
                    st2[w] = (st1[w][0] + delta * d[0], st1[w][1] + delta * d[1])
                    g2 = C.gate2(st2, wf)
                    L2 = C.bbox_side(st2, wf)
                    entry = {"side": side, "wall": w, "partner": p, "partner_dir": kind,
                             "tau": str(tau), "delta": str(delta),
                             "ok1": bool(g1["ok"]), "ok2": bool(g2["ok"]),
                             "L": str(L2), "dL": str(L2 - L0),
                             "beats": bool(g2["ok"]) and L2 <= L0 - ROUNDING}
                    if len(base["moves"]) < 40:
                        base["moves"].append(entry)
                    if base["best"] is None or L2 < base["best"][0]:
                        base["best"] = (L2, entry)
    base["stats"] = stats
    base["max_tau"] = None if max_tau is None else str(max_tau)
    base["max_delta"] = None if max_delta is None else str(max_delta)
    if base["best"] is not None:
        base["best"] = base["best"][1]
        if base["best"]["beats"]:
            base["verdict"] = "beat"
        elif base["best"]["ok2"]:
            base["verdict"] = "no-beat: legal, but the box does not shrink"
        else:
            base["verdict"] = "no-beat: the strongest coupled move overlaps"
    elif stats["combos"] == stats["tau_zero"] or \
            stats["tau_zero"] + stats["gate1_fail"] == stats["combos"] or \
            stats["complete"] == 0:
        base["verdict"] = ("no-combination: no partner of a bbox cell has a legal "
                           "first move that frees room for the wall cell")
    else:
        base["verdict"] = "no-combination"
    return base


# ------------------------------------------------------------------- the run
def merge(section, data):
    """Write one section into the shared ledger, keeping the others."""
    led = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            led = json.load(f)
    led.setdefault("run", 106)
    led.setdefault("delivered", "22.218056945")
    led["sections"] = sorted(set(led.get("sections", [])) | {section})
    led[section] = data
    with open(OUT, "w") as f:
        json.dump(led, f, indent=1)
    print(f"cand106: {section} -> {OUT}")


def dec_alphabet():
    return [(name, R._dec_word(w)) for name, _t, w in R.alphabet(16)]


def run_batch(budget=None):
    rows = C.load_rows()
    out = batch(rows, dec_alphabet(), budget)
    merge("batch", out)
    print("  batch tally", out["tally"], "seconds", out["seconds"])
    return out


def run_repair():
    rows = C.load_rows()
    out = {}
    for n in (330, 332):
        rec = repair45(n, rows[n])
        out[str(n)] = rec
        print(f"  n={n}: {rec['verdict']} start={rec['start_violations']} "
              f"end={rec['end_violations']} steps={len(rec['steps'])} L={rec.get('L')}")
    merge("repair45", out)
    return out


def run_retry():
    """Re-run the batch's exceptions with the all-axis slide (and the 45 degree repair)."""
    rows = C.load_rows()
    led = {}
    with open(OUT) as f:
        led = json.load(f)
    b = led["batch"]
    out = {}
    for rec in b["rows"]:
        if rec["verdict"].startswith("certified"):
            continue
        n = rec["n"]
        pf = [(x, y) for x, y, _t in rows[n]]
        wf = [R.snap(t)[2] for _x, _y, t in rows[n]]
        sv = survey_row(pf, wf)
        cur = pf
        if sv["violations"]:
            rep45 = repair45(n, rows[n], cap=2)
            out[str(n)] = {"kind": "overlap", "violations": len(sv["violations"]),
                           "slack": sv["violations"][0][2],
                           "repair": rep45["verdict"],
                           "repair_end": rep45["end_violations"],
                           "L": rep45["L"], "contacts": rep45["contacts"],
                           "clearance": rep45["clearance"],
                           "steps": rep45["steps"],
                           "certificate": rep45["certificate"]}
            if rep45["certificate"] and rep45["certificate"].get("status") == "verified":
                rec["verdict"] = "certified-repair"
                rec["L"] = rep45["L"]
                rec["contacts"] = rep45["contacts"]
                rec["slide"] = {"repair": rep45["steps"]}
                rec["certificate"] = rep45["certificate"]
            continue
        sl = slide_best(pf, wf, sv)
        if sl is None:
            out[str(n)] = {"kind": "no-pair", "note": "a single square has no pair to contact"}
            continue
        rep = certify_state(n, sl["state"], wf)
        out[str(n)] = {"kind": "slide", "slide": {k: sl[k] for k in
                                                   ("cell", "direction", "t", "shift")},
                       "L": rep["L"], "contacts": rep["contacts"],
                       "clearance": rep["clearance"],
                       "certificate": rep["certificate"]}
        if rep["certificate"] and rep["certificate"].get("status") == "verified":
            prev = rec["verdict"]
            prev_key = {"already-tight": "already_tight",
                        "gated-not-certified": "other"}.get(prev, "other")
            rec["verdict"] = "certified-retry"
            rec["L"] = rep["L"]
            rec["contacts"] = rep["contacts"]
            rec["slide"] = {k: sl[k] for k in ("cell", "direction", "t", "shift")}
            b["tally"]["certified"] += 1
            b["tally"][prev_key] = b["tally"].get(prev_key, 0) - 1
    b["retry"] = out
    # the tally is recomputed from the rows, so a second `--retry` cannot double-count
    tally = {"census": b["tally"]["census"], "certified": 0, "not_clean": 0,
             "already_tight": 0, "other": 0}
    for rec in b["rows"]:
        v = rec["verdict"]
        if v.startswith("certified"):
            tally["certified"] += 1
        elif v == "not-clean":
            tally["not_clean"] += 1
        elif v == "already-tight":
            tally["already_tight"] += 1
        else:
            tally["other"] += 1
    tally["retried"] = len(out)
    b["tally"] = tally
    with open(OUT, "w") as f:
        json.dump(led, f, indent=1)
    print("  retry:", {k: v.get("kind") for k, v in out.items()}, "certified", b["tally"]["certified"])
    return out


def run_couple():
    rows = C.load_rows()
    out = {}
    for n in (66, 325):
        rec = couple(n, rows[n])
        out[str(n)] = rec
        best = rec.get("best") or {}
        print(f"  n={n}: {rec['verdict']} L_cert={rec.get('L_certified')} "
              f"best_dL={best.get('dL')} delta={best.get('delta')}")
    merge("couple", out)
    return out


# ------------------------------------------------------------------- the controls
def selftest():
    ok = 0

    # 1. the survey finds the overlap and the tightest separated pair in one pass
    wf = [(ONE, ZERO), (ONE, ZERO)]
    sv = survey([(Q2(HALF), Q2(HALF)), (Q2(F(7, 5)), Q2(HALF))], wf)
    assert len(sv["violations"]) == 1, "a 1/10 overlap must be found"
    assert sv["violations"][0][2] == "-1/10", f"the overlap must read -1/10, got {sv['violations']}"
    sv2 = survey([(Q2(HALF), Q2(HALF)), (Q2(F(17, 10)), Q2(HALF))], wf)
    assert not sv2["violations"] and sv2["tight"][0] == F(1, 5), \
        f"the 1/5 gap must be the tightest slack, got {sv2['tight']}"
    print("control 1 -- the exact survey: a pair overlapping by 1/10 is reported with its "
          "exact negative slack, and a pair separated by 1/5 comes back as the tightest "
          "positive slack in the same pass, so one loop feeds both the refusal and the "
          "slide.")
    ok += 1

    # 2. the slide lands the pair exactly on contact, and that sentence certifies
    pf = [(Q2(HALF), Q2(HALF)), (Q2(F(17, 10)), Q2(HALF))]
    sl = slide(pf, wf, sv2)
    assert sl is not None and sl["slack"] == "1/5"
    rep = certify_state(2, sl["state"], wf)
    assert rep["ok"] and rep["clearance"] == "0", "the slid sentence must be tight"
    assert rep["certificate"]["status"] == "verified", "the slid sentence must certify"
    print("control 2 -- the slide: the 1/5 gap is closed by exactly 1/5 along the pair's "
          "own axis, the sentence gates at clearance 0 with one contact, and the "
          "certificate verifies -- the batch's unit of work, end to end.")
    ok += 1

    # 3. the 45 degree directions are exact unit vectors, orthogonal, and match the word
    dg, an = direction("diag"), direction("anti")
    assert dg[0] * dg[0] + dg[1] * dg[1] == ONE, "the diagonal must be a unit vector"
    assert dg[0] == dg[1] and an[0] == -an[1]
    assert dg[0] * an[0] + dg[1] * an[1] == ZERO, "the diagonals must be orthogonal"
    assert C.support(Q.word_45(), dg, Q2) == Q2(HALF), \
        "the 45 degree word's half-extent along its own axis must be exactly 1/2"
    print("control 3 -- the 45 degree directions: `(1,1)/sqrt2` is the field element "
          "`(0, 1/2)`, a unit vector orthogonal to `(-1,1)/sqrt2`, and the 45 degree "
          "word's half-extent along it is exactly 1/2 -- no decimal sqrt anywhere.")
    ok += 1

    # 4. the repair step separates a known overlap exactly
    pf3 = [(Q2(HALF), Q2(HALF)), (Q2(F(7, 5)), Q2(HALF))]
    bad = survey(pf3, wf)["violations"]
    assert len(bad) == 1, "the 1/10 overlap must be found first"
    mv = repair_step(pf3, wf, bad[0][0], bad[0][1])
    assert mv is not None, "the repair must find a direction"
    g = C.gate2(mv["state"], wf)
    assert g["ok"], "the repaired pose must gate"
    print(f"control 4 -- the 45 degree repair step: the 1/10 overlap is separated by an "
          f"exact step along `{mv['direction']}` (t = {mv['t']}), and the repaired pose "
          f"gates with 0 overlaps.")
    ok += 1

    # 5. the coupled move: the wall cell has no room until its partner makes some
    pf5 = [(Q2(HALF), Q2(HALF)), (Q2(F(3, 2)), Q2(HALF)), (Q2(F(7, 2)), Q2(HALF))]
    wf5 = [(ONE, ZERO), (ONE, ZERO), (ONE, ZERO)]
    before = C.bbox_side(pf5, wf5)
    d = inward("lo_x")
    assert wall_room(pf5, wf5, 0, d).sign() == 0, "a touching neighbour must block it"
    tau = wall_room(pf5, wf5, 1, d)
    assert tau is not None and tau == 1, f"the partner has exactly 1 of room, got {tau}"
    st1 = list(pf5)
    st1[1] = (pf5[1][0] + tau * d[0], pf5[1][1] + tau * d[1])
    assert C.gate2(st1, wf5)["ok"], "the partner's move alone must stay legal"
    delta = wall_room(st1, wf5, 0, d)
    assert delta is not None and delta == tau, f"the wall cell must take the room, got {delta}"
    st2 = list(st1)
    st2[0] = (st1[0][0] + delta * d[0], st1[0][1] + delta * d[1])
    assert C.gate2(st2, wf5)["ok"], "the coupled move must stay legal"
    after = C.bbox_side(st2, wf5)
    assert after == before - delta, f"the box must shrink by exactly delta, {after} vs {before}"
    print(f"control 5 -- the coupled move: the wall cell has 0 room while it touches its "
          f"neighbour, the partner has exactly 1, and after the partner moves the wall "
          f"cell takes the full 1 -- the box shrinks from {before} to {after} with the gate "
          f"clean.  Whether a *row* has that room is what part 3 asks.")
    ok += 1

    print(f"cand106: OK ({ok} controls)")
    return ok


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        selftest()
        return 0
    if "--batch" in argv:
        run_batch()
        return 0
    if "--repair" in argv:
        run_repair()
        return 0
    if "--couple" in argv:
        run_couple()
        return 0
    if "--retry" in argv:
        run_retry()
        return 0
    run_batch()
    run_repair()
    run_couple()
    return 0


if __name__ == "__main__":
    sys.exit(main())
