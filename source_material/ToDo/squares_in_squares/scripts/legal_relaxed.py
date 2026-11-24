#!/usr/bin/env python3
r"""legal_relaxed.py — run 128: the legal move set on the *relaxed* poses.

Run 127 measured why a legal move never shrinks a **delivered** row: its walls
are jammed to `3.3e-10`, and the move ladder's smallest rung is `1/512`, so no
slide is even available.  The one place in the pipeline where a slide has room
is the output of the projection stage, whose residual penetration is `1.1e-4` at
n = 33 to `1.6e-2` at n = 942 (run 126).  This driver takes that pose and asks
the two questions the run-127 report left open:

  1. **Is the squeeze convertible?**  A pose with residual penetration is not
     legal, so it must first be made legal, and legalising costs side.  The
     cheapest legalisation this pipeline can state is the *minimum uniform
     scale* about the box centre (`legal_slide.legal_scale`, bisected, exact at
     40 digits).  The squeeze is convertible exactly when that scale is below
     `L0 / L_sq`, because the side then scales with it and still beats `L0`.
  2. **Does a legal move fire once the pose is loose?**  The move set is run on
     the legalised pose at two step choices: the run-127 ladder, and the
     side-minimising bisected step (`tighten_exact`).  Every accepted step is
     legal at the destination at 40 digits, as before.

Arithmetic.  The squeeze and the projection are `structure.py`'s (float
discovery, unchanged, same budget split as run 126); the float pose is handed
over as `repr(float)` decimal strings, which is exact for the float64 produced.
Everything after that -- the legality scan, the scale, the moves, the verdict --
is `legal_slide`'s `Decimal` at `true_geom.DPS = 40`.  No verdict is taken in
float, and every reported dL is `L0 - side` with both sides exact.

    python3 scripts/legal_relaxed.py --selftest
    python3 scripts/legal_relaxed.py --rows 33,159,439,662,883,942 --seconds 20
"""
from __future__ import annotations

import json
import os
import sys
import time
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import legal_slide as LSL       # noqa: E402
import structure as ST          # noqa: E402
import sqscore as SQ            # noqa: E402
import true_geom as TG          # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/legal_relaxed128.json")

DEC = Decimal
WALLS = (("xlo", 0, 1), ("xhi", 0, -1), ("ylo", 1, 1), ("yhi", 1, -1))


def as_decimal(pose):
    """A float pose as exact `Decimal`s.

    `structure.attempt` hands over `repr(float)` strings, which are the shortest
    decimal that round-trips to that float64 -- so the Decimal is exactly the
    number the relaxer produced, with no further rounding.
    """
    def d(v):
        return DEC(v) if isinstance(v, str) else DEC(repr(v))
    return [(d(x), d(y), d(t)) for x, y, t in pose]


def clearance(state, dirs, idx, cells_per_wall=2, steps=24):
    """Largest legal inward slide of a cell on each wall -- the run-127 measure.

    This is the number that was `3.3e-10` on delivered poses and about `1e-10` on
    every wall of every row.  On a legalised relaxed pose it should carry the
    scale's own slack, which is the whole question.
    """
    out = {}
    for which, axis, sign in WALLS:
        cells = LSL.wall_cells(state, dirs, which)
        best = LSL.ZERO
        for i in cells[:cells_per_wall]:
            m = LSL.max_legal_step(state, dirs, idx, i, axis, sign, steps=steps)
            if m > best:
                best = m
        out[which] = str(best)
    return out


def swap_into_void(state, dirs, idx, deadline=None):
    """One legal block swap into a void, if one exists; `(pose, idx, swaps, seat)`."""
    s0 = LSL.side_of(state, dirs)
    for which, _axis, _sign in WALLS:
        if deadline is not None and time.monotonic() > deadline:
            break
        for i in LSL.wall_cells(state, dirs, which)[:2]:
            found = LSL.void_seats(state, dirs, moving=i, limit=1, idx=idx)
            if not found:
                continue
            seat = found[0]
            ok, cand, _sl, _who = LSL.try_move(state, dirs, idx, [i],
                                               seat[0] - state[i][0],
                                               seat[1] - state[i][1])
            if ok and LSL.side_of(cand, dirs) <= s0:
                return cand, LSL.positions(cand), 1, (str(seat[0]), str(seat[1]))
    return state, idx, 0, None


def analyse(n, seconds, seed=3, iters=10, proj_iters=40, split=0.6,
            rounds=3, extra=120.0, certify_max=200):
    """One row: squeeze/project, exact legalisation cost, then the legal moves."""
    t0 = time.monotonic()
    deadline = t0 + seconds + extra
    poses = []
    rec = ST.attempt(n, 0, seconds, seed, iters=iters, proj_iters=proj_iters,
                     split=split, pose_out=poses)
    st = as_decimal(poses[0])
    dr = LSL.directions(st)
    hexes = LSL.extents(dr)
    idx = LSL.positions(st)
    L0 = DEC(rec["L0"])
    L_sq = LSL.side_of(st, dr, hexes)
    worst, nviol, wit = LSL.check_pose(st, dr, idx)
    pen = -worst if worst is not None else LSL.ZERO

    out = {
        "n": n, "k": rec["k"], "L0": str(L0),
        "squeeze_side": str(L_sq), "gain_squeeze": str(L0 - L_sq),
        "residual_penetration": str(pen), "violations_at_projection": nviol,
        "worst_pair": list(wit) if wit else None,
        "sweeps_completed": rec["sweeps_completed"],
        "sweeps_aborted": rec["sweeps_aborted"],
        "patches_solved": rec["patches_solved"],
        "seconds_squeeze": rec["seconds"],
    }
    print(f"  n={n:4d} L0={str(L0)[:18]:18s} squeeze {format(L_sq - L0, '+.3e')} "
          f"pen {format(pen, '.3e')} on {nviol} pair(s)"
          f"  sweeps {rec['sweeps_completed']}/{rec['sweeps_aborted']}"
          f"  {rec['seconds']}s", flush=True)

    f_star, legal, L_legal, _ = LSL.legal_scale(st, dr)
    if f_star is None:
        out["convertible"] = False
        out["why"] = "no legal uniform scale up to the doubling cap"
        print("   no legal scale found", flush=True)
        return out

    payback = L_legal - L_sq
    gain = L0 - L_sq
    out["f_star"] = str(f_star)
    out["legal_side"] = str(L_legal)
    out["payback"] = str(payback)
    out["payback_over_gain"] = str(payback / gain) if gain > 0 else None
    out["dL_at_scale"] = str(L0 - L_legal)
    out["convertible"] = bool(L_legal < L0)
    print(f"   minimal legal scale f* = {f_star}: payback {format(payback, '+.3e')}"
          f" against a banked {format(gain, '+.3e')}"
          f" ({format(payback / gain, '.3f') if gain > 0 else 'n/a'}x)"
          f" -> dL {format(L0 - L_legal, '+.3e')}"
          f"  {'CONVERTIBLE' if out['convertible'] else 'not convertible'}",
          flush=True)

    idx = LSL.positions(legal)
    out["clearance_legal"] = clearance(legal, dr, idx)
    # the run-127 move set, on the one pose in the pipeline that is loose
    legal, idx, swaps, seat = swap_into_void(legal, dr, idx, deadline)
    out["swaps"] = swaps
    out["seat"] = list(seat) if seat else None
    ladder_pose, n_ladder = LSL.tighten(legal, dr, idx, rounds=4, deadline=deadline)
    ex_pose, n_exact = LSL.tighten_exact(ladder_pose, dr, LSL.positions(ladder_pose),
                                         rounds=rounds, deadline=deadline)
    L_fin = LSL.side_of(ex_pose, dr, hexes)
    w2, v2, wit2 = LSL.check_pose(ex_pose, dr)
    assert v2 == 0, f"n={n}: the final pose is not legal ({v2} violations)"

    out["moves_ladder"] = n_ladder
    out["moves_exact"] = n_exact
    out["side_final"] = str(L_fin)
    out["dL"] = str(L0 - L_fin)
    out["beat"] = bool(L_fin < L0)
    out["legal_final"] = True
    if n <= certify_max:
        chk = TG.check([(str(x), str(y), str(t)) for x, y, t in ex_pose])
        out["certified"] = {"side": str(+chk["side"]),
                            "violations": len(chk["violations"])}
        assert len(chk["violations"]) == 0, f"n={n}: TG.check disagrees with the sweep"
        # the two sides are computed in different summation orders at 40 digits,
        # so they agree to the working precision rather than bit for bit
        assert abs(+chk["side"] - L_fin) < DEC("1e-25"), (chk["side"], L_fin)
    out["seconds"] = round(time.monotonic() - t0, 2)
    print(f"   clearance {out['clearance_legal']}  slides {n_ladder}(ladder)"
          f"+{n_exact}(exact)  swaps {swaps}  dL {format(L0 - L_fin, '+.3e')}"
          f"  {out['seconds']}s", flush=True)
    return out


def selftest():
    """The five run-127 controls plus E, F and S -- inside the audited module."""
    assert LSL.selftest()
    print("legal_relaxed: OK (legal_slide's controls cover the move set)")
    return True


def main(argv):
    opts = dict(zip(argv[0::2], argv[1::2]))
    if "--rows" in opts:
        rows = [int(a) for a in opts["--rows"].split(",")]
    else:
        per = SQ.load()
        unbeaten = [n for n in range(2, 1001)
                    if SQ.extent(per[n]) >= SQ.grid(n) - 1e-12]
        rows = [unbeaten[0], unbeaten[49], unbeaten[149], unbeaten[299],
                unbeaten[399], unbeaten[449]]
    seconds = int(opts.get("--seconds", "20"))
    extra = int(opts.get("--extra", "120"))
    seed = int(opts.get("--seed", "3"))
    iters = int(opts.get("--iters", "10"))
    proj_iters = int(opts.get("--proj-iters", "40"))
    rounds = int(opts.get("--rounds", "3"))
    certify_max = int(opts.get("--certify-max", "200"))
    out_path = opts.get("--out", OUT)

    recs = [analyse(n, seconds, seed=seed, iters=iters, proj_iters=proj_iters,
                    rounds=rounds, extra=extra, certify_max=certify_max)
            for n in rows]
    done = [r for r in recs if "f_star" in r]
    print(f"\n{len(done)}/{len(recs)} rows legalised")
    if done:
        conv = [r for r in done if r["convertible"]]
        print(f"  squeezes convertible by the minimal legal scale: {len(conv)}/{len(done)}")
        for r in done:
            print(f"  n={r['n']:4d} pen {format(DEC(r['residual_penetration']), '.2e')}"
                  f"  f* {r['f_star'][:12]:12s}"
                  f"  payback {format(DEC(r['payback']), '+.2e')}"
                  f"  slides {r['moves_ladder']}+{r['moves_exact']}"
                  f"  dL {format(DEC(r['dL']), '+.2e')}"
                  f"  {'BEAT' if r['beat'] else 'no bite'}")
        for r in done:
            print(f"  n={r['n']:4d} clearance after legalisation "
                  f"{max(DEC(v) for v in r['clearance_legal'].values()):.3e}"
                  f"  final side {r['side_final'][:18]}")
        beats = [r for r in done if r["beat"]]
        print(f"  rows that beat their delivered side: {len(beats)}/{len(done)}")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump(recs, open(out_path, "w"), indent=1)
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(main(sys.argv[1:]))
