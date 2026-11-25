"""Run 132: rank the beaten scored rows by unclaimed room, and measure the
exact **free contraction** each delivered pose admits.

Two quantities per beaten row:

* `room = L/sqrt(n) - 1` -- the whole of the row's score, i.e. what is left on
  the table for that row.  (`score = sum(room)` over all 1000 rows, so this is
  the row's own contribution, not a hypothetical.)
* `g*` -- the **largest uniform contraction** `g <= 1` of the pose about its
  box centre that still leaves every pair and every wall legal, computed
  exactly in `Decimal` at 40 digits.  A pose at exact contact has `g* = 1`;
  a pose with a gap has `g* < 1` and the side drops from `L` to `L(g*)` with
  **no rearrangement at all** -- every coordinate moves, which is the
  "coordinated coordinate shift" run 132 asks for in its cheapest exact form,
  and which is certified by construction (contraction is affine, so a legal
  pose stays legal while the shrink factor stays above `g*`).

Nothing here can promote a row on its own: a promotion needs the new side to
be strictly smaller *and* the 40-digit gate to pass, which `trial` checks.
The float scan only *proposes* the binding pair; every number reported comes
from `Decimal`, `Fraction` and `true_geom`'s exact axes.
"""

from __future__ import annotations

import json
import os
import sys
from decimal import Decimal, getcontext
from math import isqrt

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import construct_seam as CS          # noqa: E402  (to_dec)
import legal_relaxed as LR           # noqa: E402  (as_decimal)
import legal_slide as LSL            # noqa: E402  (exact pose algebra)
import optima as OP                  # noqa: E402
import true_geom as TG               # noqa: E402  (exact axes)

getcontext().prec = 50
ZERO = Decimal(0)
ONE = Decimal(1)
PAD = Decimal("2e-9")                # `packlib.finalize`'s relative pad
ROOT = os.path.dirname(HERE)
TABLE = os.path.join(ROOT, "workspace", "submission", "table.json")
OUT = os.path.join(ROOT, "workspace", "push", "beaten_leverage132.json")
SQ2H = ONE / Decimal(2).sqrt()
AXQ = ((ONE, ZERO), (ZERO, ONE), (SQ2H, SQ2H), (SQ2H, -SQ2H))


def k_of(n: int) -> int:
    r = isqrt(n)
    return r if r * r == n else r + 1


def load_table():
    with open(TABLE) as f:
        tab = json.load(f)
    out = {}
    for key, rec in tab.items():
        n = int(key)
        out[n] = {"L": Decimal(rec["L"]), "L_model": Decimal(rec["L_model"]),
                  "src": rec["src"], "state": rec["state"]}
    return out


def sqrt_dec(n: int) -> Decimal:
    return Decimal(n).sqrt()


def room(n: int, L: Decimal) -> Decimal:
    return L / sqrt_dec(n) - ONE


def rank(tab, exclude_proved=True):
    """Beaten rows, ranked by unclaimed room, proved optima filtered out."""
    rows = []
    excluded = []
    for n, rec in sorted(tab.items()):
        L = rec["L"]
        k = k_of(n)
        if not L < Decimal(k) - PAD * L:
            continue
        p = OP.proved(n)
        if exclude_proved and p is not None:
            pv = CS.to_dec(p)
            if L <= pv + PAD * L:
                excluded.append({"n": n, "L": str(L), "proved": str(pv)})
                continue
        rows.append({"n": n, "k": k, "L": str(+L), "room": str(+room(n, L)),
                     "leverage": str(+ONE / sqrt_dec(n)), "src": rec["src"],
                     "cells": len(rec["state"])})
    rows.sort(key=lambda r: Decimal(r["room"]), reverse=True)
    return rows, excluded


# --------------------------------------------------------------------------
# the exact contraction bound


def float_binding(state):
    """Discovery only: the pair with the largest **per-pair** threshold.

    Two unit squares are separated when *some* axis separates their
    projections, so the contraction a pair admits is the *minimum* over the
    four axes of `(h_a+h_b)/|d.q|`; the pose's threshold is the *maximum* of
    that over pairs.  (Run 132's first version took the maximum over axes and
    got a threshold above 1 for a legal grid -- `g > 1` never means illegal,
    it means the wrong axis was used; control C2 caught it.)

    Returns `(g_float, (i, j))`, an estimate only: `exact_bound` recomputes the
    winner in `Decimal` and gates the contracted pose at 40 digits.
    """
    a = np.asarray(state, dtype=float)
    x, y, t = a[:, 0], a[:, 1], a[:, 2]
    c, s = np.cos(t), np.sin(t)
    n = len(a)
    gpair = np.full((n, n), np.inf)
    for qx, qy in [(1.0, 0.0), (0.0, 1.0),
                   (2 ** -0.5, 2 ** -0.5), (2 ** -0.5, -(2 ** -0.5))]:
        h = 0.5 * (np.abs(c * qx + s * qy) + np.abs(-s * qx + c * qy))
        proj = np.abs(x[:, None] * qx + y[:, None] * qy
                      - (x[None, :] * qx + y[None, :] * qy))
        tt = h[:, None] + h[None, :]
        ratio = np.where(proj > 1e-12, tt / np.maximum(proj, 1e-12), np.inf)
        np.minimum(gpair, ratio, out=gpair)     # an axis that separates is enough
    np.fill_diagonal(gpair, -np.inf)
    j = int(np.argmax(gpair))
    r, cc = divmod(j, n)
    return float(gpair[r, cc]), (r, cc)


def pair_ratio_min(state, dirs, i, j):
    """Exact per-pair threshold: the minimum over the four axes of `t/|d.q|`."""
    ci, si = dirs[i]
    cj, sj = dirs[j]
    best = None
    for qx, qy in AXQ:
        hi = (abs(ci * qx + si * qy) + abs(-si * qx + ci * qy)) / 2
        hj = (abs(cj * qx + sj * qy) + abs(-sj * qx + cj * qy)) / 2
        dx = state[i][0] - state[j][0]
        dy = state[i][1] - state[j][1]
        proj = abs(dx * qx + dy * qy)
        if proj == 0:
            continue
        r = (hi + hj) / proj
        if best is None or r < best:
            best = r
    return best


def contract(state, dirs, g):
    """Scale every coordinate by `g` about the box centre; angles untouched."""
    xlo, xhi, ylo, yhi = LSL.spans(state, dirs)
    cx, cy = (xlo + xhi) / 2, (ylo + yhi) / 2
    return [(cx + g * (x - cx), cy + g * (y - cy), t) for x, y, t in state]


def exact_bound(state, tries=8):
    """The certified minimal legal contraction of one pose, at 40 digits."""
    st = state if isinstance(state[0][0], Decimal) else LR.as_decimal(state)
    dirs = LSL.directions(st)
    L0 = LSL.side_of(st, dirs)
    g_f, (i, j) = float_binding(state)
    g = pair_ratio_min(st, dirs, i, j)
    if g is None:
        return {"ok": False, "why": "binding pair projects to zero"}
    if g > ONE:
        g = ONE
    # float proposes, exact verifies: shave until the 40-digit gate is clean
    pose, nviol, g_used = None, None, None
    for t in range(tries):
        gg = g * (ONE - Decimal("1e-13") * t) if t else g
        cand = contract(st, dirs, gg)
        worst, nv, _w = LSL.check_pose(cand, dirs)
        if nv == 0:
            pose, nviol, g_used = cand, nv, gg
            break
    if pose is None:
        return {"ok": False, "why": "no clean contraction found", "g": str(+g)}
    L1 = LSL.side_of(pose, dirs)
    return {"ok": True, "g": str(+g_used), "L0": str(+L0), "L1": str(+L1),
            "gain": str(+(L0 - L1)), "violations": nviol,
            "binding": [int(i), int(j)],
            "pose": [(str(x), str(y), str(t)) for x, y, t in pose]}


def certify(pose, cells_max=400):
    """`true_geom`'s independent whole-pose certificate (40 digits)."""
    if len(pose) > cells_max:
        return None
    chk = TG.check([(str(x), str(y), str(t)) for x, y, t in pose])
    return {"side": str(+chk["side"]), "violations": len(chk["violations"])}


# --------------------------------------------------------------------------


def selftest() -> int:
    ok = True

    def say(tag, cond, msg):
        nonlocal ok
        print(("  ok   " if cond else "  FAIL ") + tag + ": " + msg)
        ok = ok and cond

    # C1 -- a tight 3x3 grid cannot contract at all
    grid = [[(i * 1.0, j * 1.0, 0.0) for i in range(3)] for j in range(3)]
    grid = [c for row in grid for c in row]
    r = exact_bound([(repr(float(x)), repr(float(y)), repr(float(t)))
                     for x, y, t in grid])
    say("tight grid", r["ok"] and Decimal(r["g"]) == 1 and Decimal(r["gain"]) == 0,
        f"g = {r['g']}, gain = {r['gain']} (a contact pose admits no contraction)")

    # C2 -- a grid loosened by delta contracts back, by the predicted amount:
    # 3x3 at spacing s has side 2s+1 and contracts to 3, so the gain is 2s-2
    for s in ("1.05", "1.25"):
        sd = Decimal(s)
        loose = [(str(sd * i), str(sd * j), "0") for i in range(3) for j in range(3)]
        r = exact_bound(loose, tries=12)
        want = Decimal(2) * sd - Decimal(2)
        say(f"loosened s={s}", r["ok"] and abs(Decimal(r["gain"]) - want) < Decimal("1e-30"),
            f"gain = {Decimal(r['gain']):.6f} vs predicted {want:.6f}, g = {Decimal(r['g']):.6f}")

    # C3 -- a real delivered pose with a non-grid angle (n = 18, 0.424031 rad)
    # is legal at 40 digits and at contact, so contraction buys (at most) the
    # `finalize` pad.  A pose built from exact Q2 has to be rounded to get into
    # `Decimal`, and that rounding alone makes an exactly touching pair overlap
    # by ~1e-16 -- the instrument's precondition is a *stored* pose, so the
    # control uses one.
    try:
        tab = load_table()
        rec = tab[18]
        r = exact_bound(rec["state"])
        pad = PAD * Decimal(r.get("L0", "1"))
        say("real n=18", r["ok"] and Decimal(r["gain"]) <= pad,
            f"gain = {Decimal(r['gain']):.2e} <= pad {pad:.2e} "
            f"(a contact pose; g = {Decimal(r['g']):.9f})")
    except Exception as e:                                   # pragma: no cover
        say("real n=18", False, f"could not measure the stored pose: {e}")

    # C4 -- a duplicated cell is refused, not silently contracted
    dup = [("0", "0", "0"), ("0", "0", "0")]
    st = LR.as_decimal(dup)
    dirs = LSL.directions(st)
    _w, nv, _ww = LSL.check_pose(st, dirs)
    say("duplicate cell", nv > 0, f"{nv} violation(s) reported at 40 digits")

    print(("selftest OK" if ok else "selftest FAILED") + " (4 controls)")
    return 0 if ok else 1


def main(argv) -> int:
    if "--selftest" in argv:
        return selftest()
    tab = load_table()
    rows, excluded = rank(tab)
    print(f"[rank] beaten rows {len(rows)} ranked, {len(excluded)} proved-optimal "
          f"rows filtered out")
    print(f"[rank] total unclaimed room = {sum(Decimal(r['room']) for r in rows):.9f}")
    top = rows[:25]
    print(f"  {'n':>5} {'k':>3} {'L':>22} {'room':>12} {'1/sqrt n':>10} src")
    for r in top:
        print(f"  {r['n']:5d} {r['k']:3d} {Decimal(r['L']):>22.12f} "
              f"{Decimal(r['room']):>12.6f} {Decimal(r['leverage']):>10.6f} {r['src']}")
    out = {"ranking": rows, "proved_excluded": excluded}
    if "--shrink" in argv:
        limit = None
        if "--limit" in argv:
            limit = int(argv[argv.index("--limit") + 1])
        todo = top if limit else rows
        if "--nmax" in argv:
            todo = [r for r in todo if r["n"] <= int(argv[argv.index("--nmax") + 1])]
        if "--nmin" in argv:
            todo = [r for r in todo if r["n"] >= int(argv[argv.index("--nmin") + 1])]
        moved, jammed, cands = [], [], []
        for pos, r in enumerate(todo):
            if pos and pos % 50 == 0:
                print(f"  .. {pos}/{len(todo)} rows, {len(cands)} loose so far",
                      flush=True)
            state = tab[r["n"]]["state"]
            try:
                b = exact_bound(state)
            except Exception as e:                            # pragma: no cover
                print(f"  n={r['n']}: bound failed: {e}")
                continue
            if not b.get("ok"):
                print(f"  n={r['n']}: {b.get('why')}")
                continue
            gain = Decimal(b["gain"])
            room_now = Decimal(r["room"])
            rec = {"n": r["n"], "k": r["k"], "src": r["src"], "g": b["g"],
                   "L0": b["L0"], "L1": b["L1"], "gain": b["gain"],
                   "room": r["room"],
                   "gain_frac": str(+(gain / room_now)) if room_now else "0",
                   "score_gain": str(+(gain / sqrt_dec(r["n"]))),
                   "cert": certify(b["pose"]) if gain > PAD * Decimal(b["L0"])
                   else None}
            if gain > PAD * Decimal(b["L0"]):
                cands.append(rec)
                print(f"  n={r['n']:4d} LOOSE gain {gain:.6e} "
                      f"(score +{gain / sqrt_dec(r['n']):.3e})")
            elif gain > 0:
                moved.append(rec)
            else:
                jammed.append(rec)
        print(f"[shrink] {len(todo)} rows: {len(cands)} loose, "
              f"{len(moved)} pad-only, {len(jammed)} jammed (g = 1)")
        out.update({"shrink": {"rows": len(todo), "candidates": cands,
                               "pad_only": moved, "jammed": jammed}})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(f"[write] {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
