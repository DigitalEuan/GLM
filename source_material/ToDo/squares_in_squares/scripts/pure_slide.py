"""Run 133: the pure legal band-slide path on the delivered beat poses.

Run 132 measured the *uniform contraction* bound: `g* = 1` for every one of the
551 beaten poses, so no scaling of all coordinates can reduce a side.  That is
one equivalence class of rearrangements.  A **band slide** is a different one --
a wall's cells (or one cell) translate alone, the rest of the pose does not
move -- so a positive `dL` here would not contradict `g* = 1`; the two measure
different move sets and this module exists to close that gap.

No squeeze stage: the pose handed to the slide is the delivered one, at
`slack >= 0` everywhere.  Every comparison is `Decimal` at 40 digits; the only
non-exact quantity is the wall-clock budget.

The path is checked *live* before it judges anything:

  A  `legal_slide.tighten` (ladder) on the library's 4x4 pose with one row
     shifted by 0.25 -- must accept a move and land on side exactly 4.
  B  `legal_slide.tighten_exact` (side-minimising step) on the same pose with a
     1e-3 gap -- the ladder's smallest rung is 1/512, so only the exact step
     can see this gap; it must close it.
  C  a **real** delivered pose (`n = 17`) with a 0.05 gap inserted under its top
     wall -- the path must recover the gap on real combinatorics, not just on a
     grid.  This is the control that makes the null on delivered poses mean
     something.
  D  a tight 4x4 grid -- nothing to do, no move accepted, `dL = 0` exactly.
"""

from __future__ import annotations

import json
import os
import sys
import time
from decimal import Decimal, getcontext

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import beaten_leverage as BL         # noqa: E402
import legal_relaxed as LR           # noqa: E402
import legal_slide as LSL            # noqa: E402
import true_geom as TG               # noqa: E402

getcontext().prec = 50
ZERO = Decimal(0)
ONE = Decimal(1)
OUT = os.path.join(BL.ROOT, "workspace", "push", "pure_slide133.json")


def measure(st, dr):
    worst, viol, _w = LSL.check_pose(st, dr, LSL.positions(st))
    return worst, viol


def slide(st, seconds, rounds=8):
    """Both legal-move variants, in sequence, with no squeeze anywhere."""
    dr = LSL.directions(st)
    idx = LSL.positions(st)
    L0 = LSL.side_of(st, dr)
    deadline = time.monotonic() + seconds
    moved, n_lad = LSL.tighten(st, dr, idx, rounds=rounds, deadline=deadline)
    s_lad = LSL.side_of(moved, dr)
    moved2, n_ex = LSL.tighten_exact(moved, LSL.directions(moved),
                                     LSL.positions(moved), rounds=rounds,
                                     deadline=deadline)
    dr2 = LSL.directions(moved2)
    s_fin = LSL.side_of(moved2, dr2)
    worst, viol = measure(moved2, dr2)
    return {"L0": L0, "side_ladder": s_lad, "side_final": s_fin,
            "moves_ladder": n_lad, "moves_exact": n_ex,
            "dL_ladder": L0 - s_lad, "dL": L0 - s_fin,
            "violations": viol, "worst": worst,
            "pose": moved2, "dirs": dr2}


def wall_budget(st, seconds):
    """The largest legal inward slide of each wall's cells -- exact.

    `max_step` is the best *single* cell (sampled, two per wall);
    `set_step` is the whole wall set moved together, which is the only move
    that can actually shrink the side when several bands define the wall.  The
    two differ exactly where the null is interesting: a cell with room whose
    band is not what bounds the box.
    """
    dr = LSL.directions(st)
    idx = LSL.positions(st)
    out = {}
    for which, axis, sign in (("xlo", 0, 1), ("xhi", 0, -1),
                              ("ylo", 1, 1), ("yhi", 1, -1)):
        cells = LSL.wall_cells(st, dr, which)
        best = ZERO
        for i in cells[:2]:
            m = LSL.max_legal_step(st, dr, idx, i, axis, sign)
            if m > best:
                best = m
        whole = (LSL.max_legal_step(st, dr, idx, cells, axis, sign)
                 if len(cells) > 1 else best)
        out[which] = {"cells": len(cells), "max_step": str(best),
                      "set_step": str(whole)}
    return out


def selftest() -> int:
    ok = True

    def say(tag, cond, msg):
        nonlocal ok
        print(("  ok   " if cond else "  FAIL ") + tag + ": " + msg)
        ok = ok and cond

    # A -- ladder path live on the library's gapped 4x4
    st = LSL.gapped_pose(Decimal("0.25"))
    dr = LSL.directions(st)
    moved, n = LSL.tighten(st, dr, LSL.positions(st))
    s0, s1 = LSL.side_of(st, dr), LSL.side_of(moved, dr)
    say("A ladder live", n >= 1 and s0 == Decimal("4.25") and s1 == Decimal(4),
        f"side {s0} -> {s1} in {n} move(s)")

    # B -- exact-step path live at 1e-3 (below the ladder's 1/512 rung)
    st = LSL.gapped_pose(Decimal("0.001"))
    dr = LSL.directions(st)
    moved, n = LSL.tighten_exact(st, dr, LSL.positions(st))
    s0, s1 = LSL.side_of(st, dr), LSL.side_of(moved, dr)
    say("B exact step live", n >= 1 and s1 - Decimal(4) < Decimal("1e-6"),
        f"side {s0} -> {s1} in {n} move(s) (gap 1e-3, ladder rung 1/512)")

    # C -- a real delivered pose with a gap inserted under its top wall
    tab = BL.load_table()
    st0 = LR.as_decimal(tab[17]["state"])
    dr0 = LSL.directions(st0)
    L_ref = LSL.side_of(st0, dr0)
    top = LSL.wall_cells(st0, dr0, "yhi")
    gap = Decimal("0.05")
    st_g = [(x, y + gap if i in top else y, t) for i, (x, y, t) in enumerate(st0)]
    dr_g = LSL.directions(st_g)
    L_g = LSL.side_of(st_g, dr_g)
    r = slide(st_g, 20)
    # the recovery may land *below* the reference: the pose carries `finalize`'s
    # ~2e-9 pad, and the slide eats a sliver of it too.  1e-9 of reference is the
    # bar -- the gap itself is 0.05, five orders larger.
    say("C real pose live", L_g > L_ref and r["dL"] > gap * Decimal("0.99")
        and abs(r["side_final"] - L_ref) < Decimal("1e-9")
        and r["violations"] == 0,
        f"n=17 with a {gap} gap under its top wall: side {L_g} -> {r['side_final']} "
        f"(reference {L_ref}), dL = {r['dL']}, {r['moves_ladder']}+{r['moves_exact']} "
        f"move(s), {r['violations']} violation(s)")

    # D -- a tight grid has nothing to give
    st = LSL.gapped_pose(ZERO)
    r = slide(st, 10)
    say("D tight grid null", r["moves_ladder"] == 0 and r["moves_exact"] == 0
        and r["dL"] == ZERO,
        f"0 moves, dL = {r['dL']} exactly")

    print(("selftest OK" if ok else "selftest FAILED") + " (4 controls)")
    return 0 if ok else 1


def main(argv) -> int:
    if "--selftest" in argv:
        return selftest()
    rows, excluded = BL.rank(BL.load_table())
    count = int(argv[argv.index("--rows") + 1]) if "--rows" in argv else 20
    seconds = int(argv[argv.index("--seconds") + 1]) if "--seconds" in argv else 12
    tab = BL.load_table()
    recs = []
    for r in rows[:count]:
        n = r["n"]
        st = LR.as_decimal(tab[n]["state"])
        out = slide(st, seconds)
        # the contraction bound from run 132: the *same* slack `g*` measures,
        # so `dL` from slides can never exceed it without contradiction
        b = BL.exact_bound(tab[n]["state"])
        pad_gain = Decimal(b["gain"]) if b.get("ok") else None
        cell = {"n": n, "k": r["k"], "src": r["src"], "room": r["room"],
                "cells": len(st), "L0": str(+out["L0"]),
                "dL_ladder": str(+out["dL_ladder"]), "dL": str(+out["dL"]),
                "moves_ladder": out["moves_ladder"],
                "moves_exact": out["moves_exact"],
                "violations": out["violations"],
                "g_star": b.get("g"), "slack_bound": b.get("gain"),
                "exceeds_slack_bound": bool(pad_gain is not None
                                            and out["dL"] > pad_gain + Decimal("1e-15")),
                "clearance": wall_budget(st, seconds),
                "beat": bool(out["dL"] > 0)}
        if (out["moves_ladder"] or out["moves_exact"]) and len(st) <= 200:
            chk = TG.check([(str(x), str(y), str(t)) for x, y, t in out["pose"]])
            cell["certified"] = {"side": str(+chk["side"]),
                                 "violations": len(chk["violations"])}
        recs.append(cell)
        cl = " ".join(f"{w}:{Decimal(v['max_step']):.2e}/{Decimal(v['set_step']):.2e}"
                      for w, v in cell["clearance"].items())
        cell["any_wall_set_moves"] = any(Decimal(v["set_step"]) > Decimal("1e-9")
                                         for v in cell["clearance"].values())
        ratio = (Decimal(cell["dL"]) / pad_gain) if pad_gain else ZERO
        print(f"  n={n:3d} L0={out['L0']:.12f} dL={Decimal(cell['dL']):+.3e} "
              f"(bound {Decimal(b['gain']):.3e}, {ratio:.3f}x) "
              f"moves {out['moves_ladder']}+{out['moves_exact']} "
              f"viol {out['violations']} clearance {cl}", flush=True)
    gains = [Decimal(r["dL"]) for r in recs]
    print(f"[pure-slide] {len(recs)} rows, {len([g for g in gains if g > 0])} with dL > 0, "
          f"total dL {sum(gains):.3e}, moves accepted "
          f"{sum(r['moves_ladder'] + r['moves_exact'] for r in recs)}, "
          f"rows exceeding the contraction bound: "
          f"{len([r for r in recs if r['exceeds_slack_bound']])}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"rows": recs, "seconds": seconds,
                   "proved_excluded": excluded}, f, indent=1)
    print(f"[write] {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
