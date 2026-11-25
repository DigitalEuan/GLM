#!/usr/bin/env python3
r"""face_slide.py — the face slide, the high-void attack, and the exact Kaggle score.

Doc 68 §4 left one concrete move untested: a **face slide**, all the cells that realise one
side of a certified row's bounding box translated by a common exact `t` inward.  A certified
face is multiply defined (7–8 cells at n = 66, 18 at n = 325), so no single-cell or two-cell
move can lower the side, while a face slide lowers it by exactly `t` — if every pair between a
moving face cell and a fixed cell stays legal.  That is an exact interval question, and this
script settles it: the feasible set is `[0, T]` with `T` the smallest pair cap, so `T > 0` means
the side strictly shrinks by `T` and the gate lands on a contact.

PART 1 — the slide on the two rows doc 68 named, then on every exact-worded certified row:
the per-face `T`, the binding pair, the gated and certificate-checked moved state, and the new
side.  A face is *locked* only when `T = 0`, which is what "multiply defined" looks like when
it bites: every face cell has room, but not all of them along the same direction at once.

PART 2 — the highest-slack uncertified rows.  The rows run 106 could not certify are ranked by
their own Kaggle contribution `L/sqrt(n) - 1` (exact, in rigorous intervals) with the void
`L^2 - n` recorded beside it, and the top fifteen are attacked constructively: snap the stored
angles to the exact words, survey, repair the overlaps one exact step at a time, slide to the
tightest contact, then take a face slide, and certify whatever is clean at clearance 0.

PART 3 — the exact metric.  `score = sum_n L_n/sqrt(n) - 1` over all 1000 rows, before and
after any verified improvement, each term bounded rigorously with integer square roots — no
float, no Decimal comparison, no tolerance anywhere in the decision path.

READ-ONLY on `submission.csv` and the root `WHITEBOARD.md`: candidates go to
`workspace/push/submission_candidate.csv` and the ledger to `workspace/push/face_slide.json`.

USAGE
    python3 scripts/face_slide.py --selftest
    python3 scripts/face_slide.py --slide      # part 1
    python3 scripts/face_slide.py --rank       # part 2
    python3 scripts/face_slide.py --score      # part 3
    python3 scripts/face_slide.py              # all three
"""
from __future__ import annotations

import json
import os
import sys
import time
from fractions import Fraction as F
from math import isqrt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import cand105 as C                 # noqa: E402
import cand106 as K                 # noqa: E402
import rat47 as R                   # noqa: E402
import qsqrt2 as Q                  # noqa: E402
import verify_certificates as VC    # noqa: E402

Q2 = C.Q2
HALF = F(1, 2)
ZERO, ONE, TWO = Q2(F(0)), Q2(F(1)), Q2(F(2))
SIDES = K.SIDES
OUT = os.path.join(ROOT, "workspace/push/face_slide.json")
LED106 = os.path.join(ROOT, "workspace/push/cand106.json")
TAB = os.path.join(ROOT, "workspace/submission/table.json")
CAND = os.path.join(ROOT, "workspace/push/submission_candidate.csv")
SQRT_SCALE = 10 ** 40               # integer scale for the rigorous sqrt bounds
TOPK = 15


# ------------------------------------------------------------------ exact score terms
def sqrt_bounds(n, scale=SQRT_SCALE):
    """`(lo, hi)` integers with `lo/scale <= sqrt(n) < hi/scale`, exactly."""
    s = isqrt(n * scale * scale)
    if s * s == n * scale * scale:
        return s, s
    return s, s + 1


def sqrt2_bounds(scale=SQRT_SCALE):
    """`(lo, hi)` fractions bracketing `sqrt(2)`, from an integer square root."""
    s = isqrt(2 * scale * scale)
    return F(s, scale), F(s + 1, scale)


def term_bounds_q2(a, b, n, scale=SQRT_SCALE):
    """Rigorous `(lo, hi)` for `(a + b sqrt 2)/sqrt(n)`: bracket both roots, then divide.

    Every quantity is a rational here; the only approximation is the integer square root, and
    it is taken on the safe side in both directions, so the returned interval always contains
    the true value.  No float, no Decimal, no tolerance.
    """
    s2lo, s2hi = sqrt2_bounds(scale)
    lo_n, hi_n = (F(x, scale) for x in sqrt_bounds(n, scale))
    cand = [F(a) + F(b) * s2lo, F(a) + F(b) * s2hi]
    num_lo, num_hi = min(cand), max(cand)
    return num_lo / hi_n, num_hi / lo_n


def term_bounds(Lnum, Lden, n, scale=SQRT_SCALE):
    """Rigorous `(lo, hi)` for `L/sqrt(n)` with a rational `L`."""
    return term_bounds_q2(F(Lnum, Lden), F(0), n, scale)


def score_bounds(Ls, scale=SQRT_SCALE):
    """`sum_n L_n/sqrt(n) - 1` over a `{n: (a, b)}` map of `Q(sqrt 2)` sides, as bounds."""
    lo = F(0)
    hi = F(0)
    for n, (a, b) in Ls.items():
        tlo, thi = term_bounds_q2(a, b, int(n), scale)
        lo += tlo
        hi += thi
    return lo - F(len(Ls)), hi - F(len(Ls))


def score_of(table, improved, scale=SQRT_SCALE):
    """The delivered table's score, and the same table with `improved` rows replaced."""
    base = {}
    for k, v in table.items():
        f = F(str(v["L"]))
        base[int(k)] = (f, F(0))
    after = dict(base)
    for n, L in improved.items():
        after[int(n)] = L if isinstance(L, tuple) else (F(L), F(0))
    return {"before": score_bounds(base, scale), "after": score_bounds(after, scale),
            "rows": len(base), "changed": sorted(improved)}


# ------------------------------------------------------------------ the face slide
def _fr(x):
    """A `Q(sqrt 2)` element whose `sqrt 2` part is zero, as a `Fraction`."""
    return F(x.a) if hasattr(x, "a") else F(x)


def face_room_fast(pf, wf, cells, d):
    """`face_room` in `Q`, for a row whose words are all rational: the same rule, fractions.

    A face slide is ~24 rows a second in the field and ~200 in `Q`; the census is mostly
    axis-aligned, so the fast path is what makes a full sweep affordable.  The two
    implementations are checked against each other in `selftest` control 4.
    """
    wfF = [(w[0].a, w[1].a) for w in wf]
    pfF = [(_fr(x), _fr(y)) for x, y in pf]
    dF = (_fr(d[0]), _fr(d[1]))
    n = len(pfF)
    inside = set(cells)
    best = None
    for m in cells:
        xm, ym = pfF[m]
        for k in range(n):
            if k in inside:
                continue
            dx, dy = pfF[k][0] - xm, pfF[k][1] - ym
            if abs(dx) >= 2 or abs(dy) >= 2:
                continue
            cap, legal = None, False
            for owner, other in ((m, k), (k, m)):
                oc, os_ = wfF[other]
                c, s_ = wfF[owner]
                for qx, qy in ((c, s_), (-s_, c)):
                    proj = dx * qx + dy * qy
                    need = HALF + (abs(oc * qx + os_ * qy) + abs(oc * qy - os_ * qx)) * HALF
                    dq = dF[0] * qx + dF[1] * qy
                    if dq == 0:
                        continue
                    slack = abs(proj) - need
                    if slack < 0:
                        continue
                    legal = True
                    kq = -dq
                    if proj == 0 or (proj > 0) == (kq > 0):
                        continue
                    t = slack / abs(kq)
                    if cap is None or t > cap:
                        cap = t
            if not legal:
                return ZERO, [m, k], "overlap"
            if cap is None:
                continue
            if best is None or cap < best[0]:
                best = (Q2(cap), [m, k])
    return (None, None, "unbounded") if best is None else (best[0], best[1], None)


def face_room(pf, wf, cells, d):
    """The largest exact `t` with every pair legal after moving each of `cells` by `t d`.

    Pairs with both cells on the face are untouched by a common translation and are skipped.
    For a moving cell and a fixed one, each of the pair's eight axes is separated at `t = 0`
    with slack `s` and fails at `s/|d.q|` if the motion narrows it, or never if it widens it;
    the pair survives while *some* axis survives, so its cap is the largest such failure time,
    and the face's interval is the smallest pair cap.  Returns `(T, binder, None)`; `T` is
    `None` when no fixed cell can ever be reached (the face would slide forever).
    """
    if all(w[0].b == 0 and w[1].b == 0 for w in wf) and d[0].b == 0 and d[1].b == 0:
        return face_room_fast(pf, wf, cells, d)
    n = len(pf)
    inside = set(cells)
    best = None
    for m in cells:
        xm, ym = C._q(pf[m][0]), C._q(pf[m][1])
        for k in range(n):
            if k in inside:
                continue
            xk, yk = C._q(pf[k][0]), C._q(pf[k][1])
            if abs(xk - xm) >= TWO or abs(yk - ym) >= TWO:
                continue                     # the gate's own exact prune
            cap = None
            legal = False
            for proj, need, q in K.pair_axes(pf, wf, m, k):
                dq = d[0] * q[0] + d[1] * q[1]
                if dq.sign() == 0:
                    continue
                kq = -dq
                slack = abs(proj) - need
                if slack.sign() < 0:
                    continue                 # not separated on this axis at t = 0: it cannot
                    #                          be the axis that holds the pair, and it cannot
                    #                          extend the component of t = 0 either
                legal = True
                if (proj.sign() * kq.sign()) >= 0:
                    continue                 # this axis only widens
                t = slack / abs(kq)
                if cap is None or t > cap:
                    cap = t
            if not legal:
                return ZERO, [m, k], "overlap"   # this pair is violated at t = 0
            if cap is None:
                continue                          # the motion never narrows a holding axis
            if best is None or cap < best[0]:
                best = (cap, [m, k])
    return (None, None, "unbounded") if best is None else (best[0], best[1], None)


def slide_face(pf, wf, cells, d, T):
    """The exact state with every cell of `cells` translated by `T d`."""
    out = []
    for i, (x, y) in enumerate(pf):
        x, y = C._q(x), C._q(y)
        out.append((x + T * d[0], y + T * d[1]) if i in set(cells) else (x, y))
    return out


def gate_state(n, st, wf, keep_cert=True):
    """Gate a `Q(sqrt 2)` pose in its own box and build and verify its certificate.

    `cand106.certify_state` is the same thing with string-valued `L`; here the side has to stay
    in the field so the exact differences can be compared and summed.
    """
    ex = [C.extent_of(wf[i], Q2) for i in range(n)]
    lo_x = min(st[i][0] - ex[i] for i in range(n))
    lo_y = min(st[i][1] - ex[i] for i in range(n))
    sh = [(st[i][0] - lo_x, st[i][1] - lo_y) for i in range(n)]
    g = Q.gate(sh, wf, Q2)
    out = {"ok": bool(g["ok"]), "L": g["L"], "contacts": g["contacts"],
           "violations": g["violations"], "clearance": g["clearance"],
           "certificate": None, "cert_obj": None}
    if g["ok"] and g["clearance"] is not None and g["clearance"].sign() == 0 and keep_cert:
        cert = C.cert_quad(2, n, sh, wf, g["L"], g["contacts"])
        try:
            v = VC.verify_certificate(cert)
            out["certificate"] = {"status": v["status"], "N": v["N"],
                                  "contacts": v["contacts"], "L": v["L"],
                                  "clearance": v["clearance"], "void": v["void"]}
            out["cert_obj"] = cert
        except VC.Failure as f:
            out["certificate"] = {"status": "refused", "kind": f.kind,
                                  "check": f.check, "detail": f.detail}
    return out


def squeeze(st, wf, rounds=3):
    """Slide both faces of each axis inward, alternating while the side still falls.

    The container is a *square*: `L` is the larger of the two extents, so a slide on one face
    changes nothing until that axis is the wider one.  Sliding both faces of an axis shortens
    it by their two rooms at once, and alternating axes then lets the other one bind.
    """
    pf = st
    hist = []
    for _ in range(rounds):
        moved = False
        for side in SIDES:
            cells = K.wall_cells(pf, wf, side)
            T, binder, note = face_room(pf, wf, cells, K.inward(side))
            if note is None and T is not None and T.sign() > 0:
                pf = slide_face(pf, wf, cells, K.inward(side), T)
                hist.append({"side": side, "T": str(T), "binder": binder, "cells": len(cells)})
                moved = True
        if not moved:
            break
    return pf, hist


def face_slide_row(n, row, keep_cert=False):
    """All four faces: room, slide, gate, certificate, and the exact change in the side."""
    pf = [(x, y) for x, y, _t in row]
    wf = [R.snap(t)[2] for _x, _y, t in row]
    box, _edges = K.box_and_edges(pf, wf)
    L0 = max(box[2] - box[0], box[3] - box[1])       # the container is a square: the wider axis
    rec = {"n": n, "N": len(pf), "L0": str(L0), "faces": [], "best": None}
    for side in SIDES:
        cells = K.wall_cells(pf, wf, side)
        d = K.inward(side)
        T, binder, note = face_room(pf, wf, cells, d)
        f = {"side": side, "cells": len(cells), "binder": binder, "T": None if T is None else str(T),
             "note": note, "verdict": None, "L": None, "certificate": None}
        if note is not None:
            f["verdict"] = "unbounded"
        elif T.sign() <= 0:
            f["verdict"] = "locked"
        else:
            st = slide_face(pf, wf, cells, d, T)
            rep = gate_state(n, st, wf)
            f["L"] = str(rep["L"])
            f["clearance"] = rep["clearance"]
            f["dL"] = str(rep["L"] - L0)
            ok = (rep["ok"] and rep["certificate"]
                  and rep["certificate"].get("status") == "verified")
            f["verdict"] = "moves" if ok else "not-verified"
        rec["faces"].append(f)
    st, hist = squeeze([(C._q(x), C._q(y)) for x, y in pf], wf)
    rec["squeeze"] = hist
    if hist:
        rep = gate_state(n, st, wf)
        rec["L_squeezed"] = str(rep["L"])
        rec["dL"] = str(rep["L"] - L0)
        rec["clearance"] = rep["clearance"]
        rec["contacts"] = rep["contacts"]
        rec["certificate"] = rep["certificate"]
        ok = (rep["ok"] and rep["certificate"]
              and rep["certificate"].get("status") == "verified")
        rec["verdict"] = "shrink" if ok and rep["L"] < L0 else "not-verified"
        if rec["verdict"] == "shrink":
            rec["best"] = {"side": "+".join(h["side"] for h in hist), "L": str(rep["L"]),
                           "dL": rec["dL"], "T": [h["T"] for h in hist],
                           "_L": rep["L"], "_dL": rep["L"] - L0,
                           "cells": [h["cells"] for h in hist],
                           "binder": [h["binder"] for h in hist],
                           "certificate": rep["certificate"]}
            if keep_cert:
                rec["best"]["cert_obj"] = rep["cert_obj"]
    else:
        rec["verdict"] = "locked"
        rec["L_squeezed"] = rec["L0"]
    return rec


def word_rows(rows=None):
    """The rows whose stored angles are exact words (the census run 106 certified)."""
    rows = rows or C.load_rows()
    alpha = K.dec_alphabet()
    out = {}
    for n in sorted(rows):
        if K.exact_screen(rows[n], alpha) <= K.SNAP_TOL:
            out[n] = rows[n]
    return out


def improved_vs_table(slide):
    """Rows whose verified face slide gives a strictly smaller side than the delivered table."""
    table = json.load(open(TAB), parse_float=str)
    imp = {}
    for rec in slide.get("shrinks", []):
        n = rec["n"]
        L = Q2(F(rec["dL"])) + Q2(F(rec["L0"]))
        if L < Q2(F(str(table[str(n)]["L"]))):
            imp[str(n)] = [str(L.a), str(L.b)]
    for n, rec in slide.get("named", {}).items():
        b = rec.get("best")
        if b is not None and b["_L"] < Q2(F(str(table[n]["L"]))):
            imp[str(n)] = [str(b["_L"].a), str(b["_L"].b)]
    return imp


def run_slide(named=(66, 325), everything=True, budget=None):
    """Part 1: the two named rows in full, then every worded row's best face."""
    rows = C.load_rows()
    start = time.time()
    out = {"named": {}, "tally": {"rows": 0, "shrink": 0, "locked": 0, "other": 0},
           "shrinks": [], "seconds": None}
    for n in named:
        rec = face_slide_row(n, rows[n], keep_cert=True)
        out["named"][str(n)] = rec
        b = rec["best"]
        print(f"  n={n}: L0={rec['L0']} best={None if b is None else (b['side'], b['dL'], b['T'])}")
        for f in rec["faces"]:
            print(f"    {f['side']:5s} cells={f['cells']:2d} T={f['T']} {f['verdict']}"
                  f" binder={f['binder']}")
    if everything:
        total = F(0)
        for n, row in word_rows(rows).items():
            if budget is not None and time.time() - start > budget:
                out["truncated_at"] = n
                break
            rec = face_slide_row(n, row)
            out["tally"]["rows"] += 1
            if out["tally"]["rows"] % 50 == 0:
                print(f"    ... {out['tally']['rows']} rows, {len(out['shrinks'])} shrink,"
                      f" {out['seconds'] if 'seconds' in out else ''}", flush=True)
            b = rec["best"]
            if b is None:
                out["tally"]["locked"] += 1
                continue
            out["tally"]["shrink"] += 1
            total += b["_dL"]
            out["shrinks"].append({"n": n, "side": b["side"], "T": b["T"], "dL": b["dL"],
                                   "L0": rec["L0"], "L": str(b["L"]),
                                   "certificate": b["certificate"],
                                   "binder": b["binder"], "_L": b["_L"]})
        out["total_dL"] = str(total)
        out["tally"]["sum_dL"] = str(total)
        table = json.load(open(TAB), parse_float=str)
        imp = {}
        for rec in out["shrinks"]:
            L = rec.pop("_L")
            if L < Q2(F(str(table[str(rec["n"])]["L"]))):
                imp[str(rec["n"])] = [str(L.a), str(L.b)]
        for n, rec in out["named"].items():
            b = rec.get("best")
            if b is not None and b["_L"] < Q2(F(str(table[n]["L"]))):
                imp[str(n)] = [str(b["_L"].a), str(b["_L"].b)]
        out["_improved"] = imp
    out["seconds"] = str(F(time.time() - start).limit_denominator(100))
    print("  slide tally", out["tally"], "total dL", out.get("total_dL"))
    return out


# ------------------------------------------------------------------ ranking + attack
def certified_ns():
    """Every row run 106 certified: the batch's own verdicts plus the three the retry closed."""
    led = json.load(open(LED106))
    ns = {r["n"] for r in led["batch"]["rows"] if r["verdict"] == "certified"}
    for n, rec in led["batch"].get("retry", {}).items():
        if rec.get("repair") == "certified":
            ns.add(int(n))
    return ns


def rank_rows(topk=TOPK):
    """Part 2: rank every uncertified row by its Kaggle contribution, with the void beside it."""
    table = json.load(open(TAB), parse_float=str)
    cert = certified_ns()
    rows = C.load_rows()
    out = []
    for n in sorted(rows):
        if n in cert:
            continue
        L = F(str(table[str(n)]["L"]))
        lo, hi = term_bounds(L.numerator, L.denominator, n)
        out.append({"n": n, "L": str(L), "score_term_lo": str(lo), "score_term_hi": str(hi),
                    "term": str(lo), "void": str(L * L - n),
                    "relative_void": str((L * L - n) / F(n)),
                    "src": table[str(n)].get("src"), "N": len(rows[n])})
    out.sort(key=lambda r: F(r["score_term_lo"]), reverse=True)
    top = out[:topk]
    for i, r in enumerate(top):
        r["rank"] = i + 1
    print(f"  uncertified rows: {len(out)}; top {len(top)} by score term:")
    for r in top:
        print(f"   {r['rank']:2d} n={r['n']:4d} term={F(r['score_term_lo']):.6f} L={F(r['L']):.9f}"
              f" void={F(r['void']):.4f} src={r['src']}")
    return {"rows": out, "top": top, "tally": {"uncertified": len(out)}}


def worst_pair(pfq, wf):
    """The most overlapping pair, as a `Q(sqrt 2)` slack (no string round-trip)."""
    n = len(pfq)
    best = None
    for i in range(n):
        for j in range(i + 1, n):
            if abs(pfq[j][0] - pfq[i][0]) >= TWO or abs(pfq[j][1] - pfq[i][1]) >= TWO:
                continue
            sl = C.pair_slack2(pfq, wf, i, j)
            if sl.sign() < 0 and (best is None or sl < best[0]):
                best = (sl, i, j)
    return best


def compress(st, wf, rounds=4):
    """Face-slide every side inward while it has room; the exact squeeze of a pose."""
    pf = st
    rounds_done = 0
    for _ in range(rounds):
        moved = False
        for side in SIDES:
            cells = K.wall_cells(pf, wf, side)
            T, binder, note = face_room(pf, wf, cells, K.inward(side))
            if note is None and T is not None and T.sign() > 0:
                pf = slide_face(pf, wf, cells, K.inward(side), T)
                moved = True
        if not moved:
            break
        rounds_done += 1
    return pf, rounds_done


def attack(n, row, cap=40):
    """Snap to words, repair, slide, face-slide, certify — one honest attempt at one row."""
    table = json.load(open(TAB), parse_float=str)
    Lsub = F(str(table[str(n)]["L"]))
    rec = {"n": n, "L_submitted": str(Lsub), "N": len(row), "verdict": None,
           "steps": [], "start_violations": None, "end_violations": None}
    pf = [(x, y) for x, y, _t in row]
    snap = [R.snap(t) for _x, _y, t in row]
    wf = [s[2] for s in snap]
    rec["worst_word_gap"] = str(max(s[3] for s in snap))
    sv = K.survey_row(pf, wf)
    rec["start_violations"] = len(sv["violations"])
    rec["start_tightest"] = None if sv["tight"] is None else str(sv["tight"][0])
    here = [C._q(x) for x, _y in pf], [C._q(y) for _x, y in pf]
    pfq = [(C._q(x), C._q(y)) for x, y in pf]
    guard = 0
    while len(sv["violations"]) and guard < cap:
        guard += 1
        worst = worst_pair(pfq, wf)
        if worst is None:
            break
        i, j = worst[1], worst[2]
        step = K.repair_step(pfq, wf, i, j)
        if step is None:
            break
        pfq = [(C._q(x), C._q(y)) for x, y in step["state"]]
        rec["steps"].append({"pair": [i, j], "cell": step["cell"], "kind": step["direction"],
                             "t": step["t"], "slack": str(worst[0])})
        sv = K.survey_row(pfq, wf)
    rec["end_violations"] = len(sv["violations"])
    if sv["violations"]:
        rec["verdict"] = "repair-stalled"
        rec["blocked"] = {"pair": [sv["violations"][0][0], sv["violations"][0][1]],
                          "slack": sv["violations"][0][2]}
        return rec
    sl = K.slide_best(pfq, wf, sv)
    st = pfq if sl is None else [(C._q(x), C._q(y)) for x, y in sl["state"]]
    rec["slide"] = None if sl is None else {k: sl[k] for k in ("cell", "slack", "direction", "t")}
    st, rounds_done = compress(st, wf)
    rec["compress_rounds"] = rounds_done
    rep = gate_state(n, st, wf)
    rec["L_exact"] = str(rep["L"])
    rec["clearance"] = rep["clearance"]
    rec["certificate"] = rep["certificate"]
    if rep["certificate"] and rep["certificate"].get("status") == "verified":
        rec["verdict"] = "certified"
        rec["improves"] = rep["L"] < Q2(Lsub)
        rec["dL"] = str(rep["L"] - Q2(Lsub))
        rec["best"] = {"L": str(rep["L"]), "certificate": rep["certificate"]}
        if rec["improves"]:
            rec["cert_obj"] = rep["cert_obj"]
    else:
        rec["verdict"] = "gated-not-certified"
    return rec


def run_rank(topk=TOPK, attack_all=True):
    """Part 2 in full: the ranking, then one constructive attempt per top row."""
    start = time.time()
    rk = rank_rows(topk)
    out = {"top": rk["top"], "uncertified": len(rk["rows"]), "attacks": [],
           "seconds": None}
    rows = C.load_rows()
    if attack_all:
        for r in rk["top"]:
            rec = attack(r["n"], rows[r["n"]])
            rec["rank"] = r["rank"]
            out["attacks"].append(rec)
            print(f"   attack n={r['n']:4d}: {rec['verdict']} "
                  f"viol={rec['start_violations']}->{rec['end_violations']} "
                  f"L={rec.get('L_exact')} sub={rec['L_submitted']} "
                  f"cert={(rec.get('certificate') or {}).get('status')}")
    out["wins"] = [a for a in out["attacks"] if a.get("improves")]
    out["tally"] = {"top": len(rk["top"]), "attacked": len(out["attacks"]),
                    "certified": sum(1 for a in out["attacks"] if a["verdict"] == "certified"),
                    "improves": len(out["wins"]),
                    "stalled": sum(1 for a in out["attacks"] if a["verdict"] == "repair-stalled")}
    out["seconds"] = str(F(time.time() - start).limit_denominator(100))
    print("  rank tally", out["tally"])
    return out


# ------------------------------------------------------------------ the exact metric
def run_score(slide=None, keep=True):
    """Part 3: the exact before/after metric, and the candidate rows kept for review."""
    table = json.load(open(TAB), parse_float=str)
    if slide is None:
        if os.path.exists(OUT):
            slide = json.load(open(OUT)).get("slide")
        if slide is None:
            slide = run_slide(named=(66, 325), everything=True)
    improved = {int(n): (F(a), F(b)) for n, (a, b) in slide.get("_improved", {}).items()}
    sc = score_of(table, improved)
    before, after = sc["before"], sc["after"]
    delta = (after[0] - before[0] + after[1] - before[1]) / 2
    dlo, dhi = (after[0] - before[1]), (after[1] - before[0])
    out = {"rows": sc["rows"], "changed": sc["changed"],
           "before_lo": str(before[0]), "before_hi": str(before[1]),
           "after_lo": str(after[0]), "after_hi": str(after[1]),
           "delta_lo": str(dlo), "delta_hi": str(dhi), "delta_mid": str(delta),
           "delivered": json.load(open(LED106)).get("delivered"),
           "improved": {str(k): [str(a), str(b)] for k, (a, b) in sorted(improved.items())}}
    print(f"  score: {len(improved)} rows changed; before [{F(out['before_lo']):.12f}, "
          f"{F(out['before_hi']):.12f}] delta [{F(out['delta_lo']):.3e}, {F(out['delta_hi']):.3e}]")
    if improved:
        write_candidate(improved)
    return out


def dec_str(x, digits=12):
    """`x` as a decimal string with `digits` places, by integer arithmetic only."""
    v = F(x.a) if hasattr(x, "a") else F(x)
    q = abs(v) * 10 ** digits
    scaled = (q.numerator + (q.denominator // 2)) // q.denominator
    whole, frac = divmod(scaled, 10 ** digits)
    sign = "-" if v < 0 else ""
    return f"{sign}{whole}.{frac:0{digits}d}"


def write_candidate(improved, path=CAND):
    """The delivered submission with the verified rows replaced; never touches submission.csv.

    Only called when at least one row strictly improved, and only for review: the rows written
    are the moved exact states rounded to twelve places, which is a *lossy* rendering the
    reader must gate again (the ledger keeps the exact values).
    """
    import csv
    rows = C.load_rows()
    keep = {}
    for n, (a, b) in improved.items():
        rec = face_slide_row(int(n), rows[int(n)])
        best = rec["best"]
        if best is None:
            continue
        pf = [(x, y) for x, y, _t in rows[int(n)]]
        wf = [R.snap(t)[2] for _x, _y, t in rows[int(n)]]
        st = slide_face(pf, wf, best["cells"], K.inward(best["side"]), F(best["T"]))
        keep[int(n)] = st
    if not keep:
        return None
    src = os.path.join(ROOT, "workspace/submission/submission.csv")
    out_rows = []
    with open(src) as f:
        for r in csv.DictReader(f):
            n = int(r["n"])
            if n in keep:
                k = int(r["square_id"])
                x, y = keep[n][k]
                out_rows.append({"id": r["id"], "n": r["n"], "square_id": r["square_id"],
                                 "x": dec_str(x.a), "y": dec_str(y.a), "angle": r["angle"]})
            else:
                out_rows.append(r)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "n", "square_id", "x", "y", "angle"])
        w.writeheader()
        w.writerows(out_rows)
    return path


# ------------------------------------------------------------------ controls
def selftest():
    """Three controls: a locked face, an opening face, and the score arithmetic."""
    # control 1 -- a 2x2 block of unit squares: every face has two cells, and each is held by
    # the other column, so the face is locked at exactly 0 and no side moves.
    w0 = R.snap(F(0))[2]
    pf = [(F(1, 2), F(1, 2)), (F(3, 2), F(1, 2)), (F(1, 2), F(3, 2)), (F(3, 2), F(3, 2))]
    wf = [w0] * 4
    for side in SIDES:
        cells = K.wall_cells(pf, wf, side)
        T, binder, note = face_room(pf, wf, cells, K.inward(side))
        assert note is None and T is not None and T.sign() == 0, (side, T, note)
    # control 2 -- the same row with the right-hand column pushed out by 1/10: now the lo_x face
    # (which is only the left column) has room, and the slide lowers the side by exactly that.
    pf2 = [(F(1, 2), F(1, 2)), (F(8, 5), F(1, 2)), (F(1, 2), F(3, 2)), (F(8, 5), F(3, 2))]
    cells = K.wall_cells(pf2, wf, "lo_x")
    assert cells == [0, 2], cells
    T, binder, note = face_room(pf2, wf, cells, K.inward("lo_x"))
    assert note is None and T is not None and T.sign() > 0, (T, note)
    L0 = F(8, 5) + F(1, 2) - (F(1, 2) - F(1, 2))
    st = slide_face(pf2, wf, cells, K.inward("lo_x"), T)
    rep = K.certify_state(4, st, wf)
    assert rep["ok"] and rep["certificate"]["status"] == "verified", rep["certificate"]
    assert F(rep["L"]) < L0, (rep["L"], L0)
    assert F(rep["L"]) == L0 - T, (rep["L"], L0 - T)
    # control 3 -- the score arithmetic: n = 1, 4, 9 have rational roots, so the interval must
    # collapse on the exact value; a non-square n must bracket sqrt(n) rigorously.
    tab = {"1": {"L": "1"}, "4": {"L": "3"}, "9": {"L": "5"}}
    lo, hi = score_bounds({"1": (F(1), F(0)), "4": (F(3), F(0)), "9": (F(5), F(0))})
    assert lo == hi == F(7, 6), (lo, hi)       # 1/1 + 3/2 + 5/3 - 3 = 7/6
    lo2, hi2 = term_bounds(1, 1, 2)            # bounds on 1/sqrt(2), unscaled
    assert lo2 * lo2 * 2 <= 1 and hi2 * hi2 * 2 > 1, (lo2, hi2)
    assert lo2 < hi2
    # control 4 -- the fast (rational) and field implementations of the face room must agree
    pf5 = [(F(1, 2), F(1, 2)), (F(8, 5), F(1, 2)), (F(1, 2), F(3, 2)), (F(8, 5), F(3, 2))]
    for side in SIDES:
        c5 = K.wall_cells(pf5, wf, side)
        slow = face_room(pf5, wf, c5, K.inward(side))
        fast = face_room_fast(pf5, wf, c5, K.inward(side))
        assert slow[0] == fast[0] and slow[2] == fast[2], (side, slow, fast)
    print("control 4 -- the rational fast path returns exactly the field path's room on every "
          "side of the shifted block.")
    print("control 1 -- a 2x2 block: all four faces are multiply defined and locked at T = 0, "
          "so the side cannot move; the exact interval is the single point {0}.")
    print("control 2 -- the same block with one column pushed out: the lo_x face is now two "
          "cells with T = 1/10, the slide gates at clearance 0, the certificate verifies and "
          "L drops by exactly T.")
    print("control 3 -- the score: with rational roots the rigorous interval collapses on the "
          "exact value, and for sqrt(2) it brackets it strictly.")
    print("face_slide: OK (4 controls)")


# ------------------------------------------------------------------ the run
def merge(section, data):
    led = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            led = json.load(f)
    led.setdefault("run", 108)
    led.setdefault("delivered", "22.217428576")
    led["sections"] = sorted(set(led.get("sections", [])) | {section})
    led[section] = data
    with open(OUT, "w") as f:
        json.dump(led, f, indent=1)
    print(f"face_slide: {section} -> {OUT}")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        selftest()
        return
    do_all = not any(a in argv for a in ("--slide", "--rank", "--score"))
    if "--slide" in argv or do_all:
        merge("slide", run_slide())
    if "--rank" in argv or do_all:
        merge("rank", run_rank())
    if "--score" in argv or do_all:
        merge("score", run_score())
    return


if __name__ == "__main__":
    main()
