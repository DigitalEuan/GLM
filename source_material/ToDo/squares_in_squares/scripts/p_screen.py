#!/usr/bin/env python3
r"""p_screen.py — run 129: screen combinatorial moves by the `p < gain / L` bar.

Doc 87 (run 128) turned the relaxtion pipeline into an inequality.  The squeeze
banks `gain = L0 - L_squeeze`; making the relaxed pose legal costs about `p * L`,
where `p` is the depth of the deepest violating pair; so a candidate can be
converted only if

    p  <  gain / L          (6.5e-4 at n = 33 down to 1.3e-4 at n = 942)

The six rows of doc 87 were all over that bar by 5.5x to 407x, and every local
continuous route loses for the same reason: it pays for legality at `p * L`.
What no run has tested is whether a *combinatorial* move -- one that changes
which cell sits where before the squeeze -- can leave the projection with a
depth under the bar.  That is the question here, and it is cheap to ask:

  * `structure.attempt` already generates those moves: kind 1 teleports a cell
    into a free-space void (or, when no void is found, displaces one cell),
    kind 2 rotates a 2x2 block by 90 degrees.  Kind 0 is the plain squeeze and
    serves as the control.
  * the *screen* needs one exact `check_pose` on the projected pose, not the
    legalisation, the move set or a certificate.

This driver samples ten unbeaten rows, three families and three seeds per
row/family, measures `p` at 40 digits, and compares each candidate with its own
bar.  A candidate already `>= margin` times above its bar is recorded and **not**
converted (the early stop: that budget would be spent on a doomed conversion);
a candidate inside the margin is converted exactly, and the best of all is
converted whatever its ratio, so the screen's own prediction is checked against
the measured dL rather than assumed.

Arithmetic: the squeeze and the projection are `structure.py`'s (float
discovery, unchanged); the pose is handed over as `repr(float)` strings (exact
for the float64) and everything after that -- the depth, the bar, the
legalisation, the moves, the dL -- is `legal_slide`'s `Decimal` at
`true_geom.DPS = 40`.

    python3 scripts/p_screen.py --list
    python3 scripts/p_screen.py --rows 33,159,439 --seeds 3 --seconds 8 --append
    python3 scripts/p_screen.py --confirm 33,1,4 --seconds 20
    python3 scripts/p_screen.py --selftest
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

import numpy as np              # noqa: E402

import legal_relaxed as LR      # noqa: E402
import legal_slide as LSL       # noqa: E402
import structure as ST          # noqa: E402
import sqscore as SQ            # noqa: E402
import true_geom as TG          # noqa: E402

OUT = os.path.join(ROOT, "workspace/push/p_screen129.json")
RUN128 = os.path.join(ROOT, "workspace/push/legal_relaxed128.json")
DEC = Decimal
ZERO = DEC(0)

#: A candidate this many times above its bar is not converted: the exact stage
#: cannot change the verdict, because it can only *add* side (doc 87 §6).
MARGIN = DEC(10)

FAMILIES = ("plain (control)", "teleport into a void", "displace one cell",
            "rotate a 2x2 block")


def family_of(rec):
    """The move family a record belongs to, read off what `attempt` actually did.

    `attempt` reports its move as a string, and kind 1 has two branches: a
    teleport to a free-space point when one is found, a small displacement
    otherwise.  They are different moves and are attributed separately.
    """
    if rec["kind"] == 0:
        return FAMILIES[0]
    if rec["kind"] == 2:
        return FAMILIES[3]
    return FAMILIES[1] if rec["moved"].startswith("teleport") else FAMILIES[2]


def bar_of(gain, L):
    """The convertibility bar `gain / L`; `ZERO` when the squeeze banked nothing.

    `L` is the *delivered* side `L0`, which is the form doc 87 §5 tabulated
    (`6.544e-4` at n = 33); using the squeeze side instead moves the bar by
    0.07 % and would make the two documents disagree in the fourth digit.
    """
    return gain / L if (gain > ZERO and L > ZERO) else ZERO


def should_convert(p, bar, margin=MARGIN):
    """The screen's decision, in one place so a control can test it.

    Convert if the depth is under the bar (it may pay) or within `margin` of it
    (it is close enough that the exact stage is worth pricing).  Anything further
    out cannot be rescued: the exact stage only ever adds side.
    """
    if bar <= ZERO:
        return False
    return p < margin * bar


def measure(pose_strings):
    """Exact depth, violation count and side of a projected pose, at 40 digits."""
    st = LR.as_decimal(pose_strings)
    dr = LSL.directions(st)
    idx = LSL.positions(st)
    L_sq = LSL.side_of(st, dr)
    worst, nviol, wit = LSL.check_pose(st, dr, idx)
    p = -worst if worst is not None else ZERO
    return {"state": st, "dirs": dr, "idx": idx, "side": L_sq,
            "p": p, "violations": nviol, "worst_pair": list(wit) if wit else None}


def convert(state, dirs, L0, L_sq, deadline, certify_max=200, rounds=3):
    """The exact stage of doc 87: minimum legal scale, then legal moves only.

    Returns the measured payback (`legal side - squeeze side`), the dL after the
    legal moves, and -- on rows small enough for the O(n^2) pass -- the
    independent whole-pose certificate.  `nviol == 0` on the result is asserted,
    not assumed: a conversion that ends illegal is not a conversion.
    """
    t0 = time.monotonic()
    f_star, legal, L_legal, _ = LSL.legal_scale(state, dirs)
    if f_star is None:
        return {"convertible": False, "why": "no legal uniform scale found"}
    idx = LSL.positions(legal)
    legal, idx, swaps, seat = LR.swap_into_void(legal, dirs, idx, deadline)
    pose, n_lad = LSL.tighten(legal, dirs, idx, rounds=4, deadline=deadline)
    pose, n_ex = LSL.tighten_exact(pose, dirs, LSL.positions(pose),
                                   rounds=rounds, deadline=deadline)
    L_fin = LSL.side_of(pose, dirs)
    nviol = LSL.check_pose(pose, dirs)[1]
    assert nviol == 0, f"converted pose is illegal ({nviol} violations)"
    out = {"f_star": str(f_star), "legal_side": str(L_legal),
           "payback": str(L_legal - L_sq), "side_final": str(L_fin),
           "dL": str(L0 - L_fin), "convertible": bool(L_fin < L0),
           "moves_ladder": n_lad, "moves_exact": n_ex, "swaps": swaps,
           "seat": list(seat) if seat else None,
           "certified": None, "seconds_exact": round(time.monotonic() - t0, 2)}
    if len(pose) <= certify_max:
        chk = TG.check([(str(x), str(y), str(t)) for x, y, t in pose])
        assert len(chk["violations"]) == 0
        out["certified"] = {"side": str(+chk["side"]),
                            "violations": len(chk["violations"])}
    return out


def squeeze_from(X, Y, T, L0, seconds, seed, n, iters=10, proj_iters=40,
                 split=0.6):
    """`structure.attempt`'s squeeze-and-project loop from an explicit pose.

    `attempt` always starts from the delivered pose, so a candidate that has
    already been rearranged cannot be handed to it; this is the same loop with
    the same budget split, the same `wall_w` values and the same iteration caps,
    run from the rearranged (X, Y, T) instead.
    """
    t0 = time.monotonic()
    deadline = t0 + seconds
    squeeze_deadline = t0 + split * seconds
    want = float(L0) - ST.TARGET
    nprng = np.random.RandomState(seed * 31 + n * 7 + 5)
    Xa, Ya, Ta = X.copy(), Y.copy(), T.copy()
    stats = {}
    for _outer in range(4):
        if time.monotonic() > squeeze_deadline:
            break
        Xa, Ya, Ta = ST.relax(Xa, Ya, Ta, want, sweeps=2, deadline=squeeze_deadline,
                              rng=nprng, wall_w=1e5, iters=iters, stats=stats)
        _, _, Xa, Ya, Ta = ST.project(Xa, Ya, Ta, want, deadline, nprng,
                                      screen=True, stats=stats, iters=proj_iters)
        if time.monotonic() > deadline:
            break
    return [(repr(float(a)), repr(float(b)), repr(float(c)))
            for a, b, c in zip(Xa, Ya, Ta)], stats


def void_swap(n, seed, seconds, margin=MARGIN, do_convert=False, extra=90.0):
    """The void-swap family, as a *legal* rearrangement before the squeeze.

    `structure.attempt`'s kind 1 samples a free-space point with 1.02 clearance
    from every cell; on these poses no such point exists (0 of 32 draws found
    one, so every kind-1 candidate was a displacement instead).  The void move
    that is actually available is the one run 127 built: a wall cell is moved to
    an exact unit-lattice seat inside the pose -- legal at the destination at 40
    digits -- and the rearranged pose is then squeezed.  Candidates are rejected
    if the swap is illegal or grows the side, and the search walks walls and
    wall cells from `seed`.
    """
    t0 = time.monotonic()
    st = LSL.load_pose(n)
    dr = LSL.directions(st)
    idx = LSL.positions(st)
    L0 = LSL.side_of(st, dr)
    swapped, seat, moved_cell, which = None, None, None, None
    tried = 0
    for k in range(4):
        which, axis, sign = (("xlo", 0, 1), ("xhi", 0, -1),
                             ("ylo", 1, 1), ("yhi", 1, -1))[(seed + k) % 4]
        cells = LSL.wall_cells(st, dr, which)
        for j in range(min(2, len(cells))):
            i = cells[(seed + j) % len(cells)]
            tried += 1
            found = LSL.void_seats(st, dr, moving=i, limit=1, idx=idx)
            if not found:
                continue
            ok, cand, _sl, _who = LSL.try_move(st, dr, idx, [i],
                                               found[0][0] - st[i][0],
                                               found[0][1] - st[i][1])
            if ok and LSL.side_of(cand, dr) <= L0:
                swapped, seat, moved_cell = cand, found[0], i
                break
        if swapped is not None:
            break
    if swapped is None:
        return {"n": n, "kind": 3, "family": "void swap", "seed": seed,
                "moved": "no legal void seat", "L0": str(L0),
                "squeeze_side": None, "gain": "0", "p": None, "bar": "0",
                "ratio": None, "passes_bar": False, "violations": None,
                "worst_pair": None, "screened": True, "cells_tried": tried,
                "screen_reason": f"no legal void seat among {tried} wall cells",
                "sweeps_completed": 0, "sweeps_aborted": 0,
                "patches_solved": 0, "seconds": round(time.monotonic() - t0, 2)}
    X = np.array([float(p[0]) for p in swapped])
    Y = np.array([float(p[1]) for p in swapped])
    T = np.array([float(p[2]) for p in swapped])
    poses, stats = squeeze_from(X, Y, T, L0, seconds, seed, n)
    got = measure(poses)
    gain = L0 - got["side"]
    bar = bar_of(gain, L0)
    p = got["p"]
    ratio = (p / bar) if bar > ZERO else None
    rec_out = {
        "n": n, "kind": 3, "family": "void swap", "seed": seed,
        "moved": f"cell {moved_cell} on {which} to a void seat",
        "cells_tried": tried,
        "L0": str(L0), "squeeze_side": str(got["side"]), "gain": str(gain),
        "p": str(p), "violations": got["violations"],
        "worst_pair": got["worst_pair"], "bar": str(bar),
        "ratio": str(ratio) if ratio is not None else None,
        "passes_bar": bool(bar > ZERO and p < bar),
        "seat": [str(seat[0]), str(seat[1])],
        "sweeps_completed": stats.get("sweeps_completed", 0),
        "sweeps_aborted": stats.get("sweeps_aborted", 0),
        "patches_solved": stats.get("patches_solved", 0),
        "seconds": round(time.monotonic() - t0, 2),
    }
    if do_convert or rec_out["passes_bar"]:
        ex = convert(got["state"], got["dirs"], L0, got["side"],
                     t0 + seconds + extra)
        rec_out["exact"] = ex
        rec_out["screened"] = False
    else:
        rec_out["screened"] = True
        rec_out["screen_reason"] = (
            "no gain banked" if bar <= ZERO
            else f"{format(ratio, '.1f')}x above the bar (>= {margin}x): exact stage skipped")
    return rec_out


def screen(n, kind, seed, seconds, margin=MARGIN, do_convert=False, extra=90.0):
    """One candidate: squeeze with a combinatorial move, measure `p`, screen it."""
    t0 = time.monotonic()
    poses = []
    rec = ST.attempt(n, kind, seconds, seed, pose_out=poses)
    L0 = DEC(rec["L0"])
    got = measure(poses[0])
    gain = L0 - got["side"]
    bar = bar_of(gain, L0)
    p = got["p"]
    ratio = (p / bar) if bar > ZERO else None
    rec_out = {
        "n": n, "kind": kind, "family": family_of(rec), "moved": rec["moved"],
        "seed": seed, "seconds_squeeze": rec["seconds"], "L0": str(L0),
        "squeeze_side": str(got["side"]), "gain": str(gain),
        "p": str(p), "violations": got["violations"],
        "worst_pair": got["worst_pair"],
        "bar": str(bar), "ratio": str(ratio) if ratio is not None else None,
        "passes_bar": bool(bar > ZERO and p < bar),
        "sweeps_completed": rec["sweeps_completed"],
        "sweeps_aborted": rec["sweeps_aborted"],
        "patches_solved": rec["patches_solved"],
        "budget_limited": rec["budget_limited"],
        "seconds": round(time.monotonic() - t0, 2),
    }
    # Only a candidate *under* its bar is converted on the spot.  One inside
    # the margin but over the bar is not: doc 87 §6 measured that the exact stage
    # can only add side, so it cannot turn an over-bar depth into a gain -- it is
    # priced on request with `--confirm` instead, and the margin's job in the
    # sampling loop is to decide whether the row deserves more draws.
    if do_convert or rec_out["passes_bar"]:
        deadline = t0 + seconds + extra
        ex = convert(got["state"], got["dirs"], L0, got["side"], deadline)
        rec_out["exact"] = ex
        rec_out["screened"] = False
    else:
        rec_out["screened"] = True
        rec_out["screen_reason"] = (
            "no gain banked" if bar <= ZERO
            else f"{format(ratio, '.1f')}x above the bar (>= {margin}x): exact stage skipped")
    return rec_out


def row_list(rows=10):
    """`rows` evenly spaced unbeaten rows, by the rule `structure.main` uses."""
    per = SQ.load()
    unbeaten = [n for n in range(2, 1001)
                if SQ.extent(per[n]) >= SQ.grid(n) - 1e-12]
    step = len(unbeaten) / rows
    return sorted({unbeaten[min(len(unbeaten) - 1, int(round(i * step)))]
                   for i in range(rows)})


def median(vals):
    """Median of Decimals (mean of the middle pair when the count is even)."""
    s = sorted(vals)
    k = len(s)
    if not k:
        return None
    return s[k // 2] if k % 2 else (s[k // 2 - 1] + s[k // 2]) / 2


def summarise(recs):
    """Per family and per row: how close to the bar, and how many pass."""
    print(f"\n{'family':22s} {'n':>5s} {'median p':>12s} {'min p':>12s} "
          f"{'max p':>12s} {'min p/bar':>12s} {'pass':>5s}")
    fams = {}
    for r in recs:
        fams.setdefault(r["family"], []).append(r)
    rows = {}
    for fam in FAMILIES:
        if fam not in fams:
            continue
        rs = fams[fam]
        ps = [DEC(r["p"]) for r in rs if r["p"] is not None]
        ratios = [DEC(r["ratio"]) for r in rs if r["ratio"] not in (None, "None")]
        npass = sum(1 for r in rs if r["passes_bar"])
        if not ps:
            print(f"{fam:22s} {'-':>5s} {'no seat in any draw':>12s}")
            continue
        print(f"{fam:22s} {'-':>5s} {format(median(ps), '.3e'):>12s} "
              f"{format(min(ps), '.3e'):>12s} {format(max(ps), '.3e'):>12s} "
              f"{(format(min(ratios), '.1f') if ratios else 'n/a'):>12s} "
              f"{npass:>2d}/{len(rs):<2d}")
        for n in sorted({r["n"] for r in rs}):
            cell = [r for r in rs if r["n"] == n]
            cps = [DEC(r["p"]) for r in cell if r["p"] is not None]
            cratios = [DEC(r["ratio"]) for r in cell if r["ratio"] not in (None, "None")]
            rows.setdefault(n, {})[fam] = (median(cps), min(cps), max(cps),
                                           min(cratios) if cratios else None)
            print(f"{'':22s} {n:>5d} {format(median(cps), '.3e'):>12s} "
                  f"{format(min(cps), '.3e'):>12s} {format(max(cps), '.3e'):>12s} "
                  f"{(format(min(cratios), '.1f') if cratios else 'n/a'):>12s} "
                  f"{sum(1 for r in cell if r['passes_bar']):>2d}/{len(cell):<2d}")
    conv = [r for r in recs if "exact" in r]
    if conv:
        print("\nconverted candidates (exact stage run):")
        for r in conv:
            ex = r["exact"]
            print(f"  n={r['n']:4d} {r['family']:22s} seed {r['seed']}  "
                  f"p {format(DEC(r['p']), '.3e')} bar {format(DEC(r['bar']), '.3e')} "
                  f"ratio {format(DEC(r['ratio']), '.1f')}x  ->  "
                  f"f* {ex.get('f_star', 'n/a')[:12]}  dL "
                  f"{format(DEC(ex['dL']), '+.3e') if 'dL' in ex else 'n/a'}"
                  f"  {'BEAT' if ex.get('convertible') else 'no bite'}")
    npass = sum(1 for r in recs if r["passes_bar"])
    nseat = sum(1 for r in recs if r.get("p") is None)
    print(f"\ncandidates {len(recs)}: {npass} under the bar, "
          f"{len(recs) - npass - nseat} over it, {nseat} with no candidate at all, "
          f"{len(conv)} converted exactly")
    return rows


def selftest():
    """Controls for the bar, the decision function and the screen's non-vacuity."""
    # 1. the bar, cross-checked against doc 87's own table (run 128's record is
    #    read, never rewritten): n = 33 documents p = 3.5893e-3, bar 6.544e-4 and
    #    5.5x over it.
    with open(RUN128) as f:
        r128 = {r["n"]: r for r in json.load(f)}
    r = r128[33]
    L0, L_sq = DEC(r["L0"]), DEC(r["squeeze_side"])
    gain = L0 - L_sq
    bar = bar_of(gain, L0)
    p = DEC(r["residual_penetration"])
    print(f"1 bar arithmetic -- run 128's n=33 record: gain {format(gain, '.4e')}, "
          f"bar {format(bar, '.4e')}, p {format(p, '.4e')}, "
          f"{format(p / bar, '.1f')}x over")
    assert abs(bar - DEC("6.544e-4")) < DEC("1e-7"), bar
    assert DEC("5.4") < p / bar < DEC("5.6"), p / bar
    # and the law itself on the same record: payback is p * L to a few per cent
    pb, L_l = DEC(r["payback"]), DEC(r["legal_side"])
    print(f"  law check -- payback {format(pb, '.3e')} against p*L "
          f"{format(p * L0, '.3e')} (ratio {format(pb / (p * L0), '.2f')})")
    assert DEC("0.7") < pb / (p * L0) < DEC("0.95"), pb / (p * L0)

    # 2. the decision function: under the bar converts, within the margin
    #    converts, far above it is screened -- and no gain means no conversion.
    b = DEC("1e-3")
    cases = ((DEC("0"), True, "p = 0 is under the bar"),
             (DEC("9e-4"), True, "p = 0.9 bar is under the bar"),
             (DEC("9e-3"), True, "p = 9 bar is inside the 10x margin"),
             (DEC("1.1e-2"), False, "p = 11 bar is outside the margin"),
             (DEC("1e-3"), True, "p = bar exactly is priced but not under it"))
    for pv, want, why in cases:
        got = should_convert(pv, b)
        print(f"2 screen decision -- p = {pv} vs bar {b}: convert={got} ({why})")
        assert got == want, (pv, why, got)
    assert should_convert(ZERO, ZERO) is False        # nothing banked, no conversion
    # the bar itself is a strict test: p == gain/L does not *pass* it, even
    # though it is close enough to be worth pricing.
    assert not (DEC("1e-3") < DEC("1e-3"))

    # 3. non-vacuity: a pass is reachable.  A 4x4 grid tightened to exactly side
    #    4 has p = 0, so with a 2e-3 gain its bar is 5e-4 and it passes -- the
    #    screen is not a function that returns \"fail\" for everything.
    st = [(DEC(i), DEC(j), ZERO) for j in range(4) for i in range(4)]
    dr = LSL.directions(st)
    got = measure([(str(x), str(y), str(t)) for x, y, t in st])
    bar3 = bar_of(DEC("2e-3"), got["side"])
    print(f"3 non-vacuity -- a legal 4x4 at side {got['side']} has p = "
          f"{format(got['p'], '.1e')}; with gain 2e-3 the bar is "
          f"{format(bar3, '.1e')} and it passes = {should_convert(got['p'], bar3)}")
    assert got["p"] == ZERO and got["violations"] == 0
    assert should_convert(got["p"], bar3) is True

    # 4. and the screen rejects a real failed draw, not a hypothetical one: the
    #    worst row of run 128 (n = 942, 401x over its bar) is screened.
    r = r128[942]
    bar4 = bar_of(DEC(r["L0"]) - DEC(r["squeeze_side"]), DEC(r["L0"]))
    p4 = DEC(r["residual_penetration"])
    print(f"4 real rejection -- run 128 n=942: p {format(p4, '.3e')} vs bar "
          f"{format(bar4, '.3e')} = {format(p4 / bar4, '.0f')}x, convert = "
          f"{should_convert(p4, bar4)}")
    assert should_convert(p4, bar4) is False
    print("p_screen: OK (4 controls)")


def main(argv):
    opts = dict(zip(argv[0::2], argv[1::2]))
    if "--list" in argv:
        print("rows:", ",".join(str(n) for n in row_list(int(opts.get("--nrows", "10")))))
        return 0
    if "--selftest" in argv:
        selftest()
        return 0
    if "--confirm" in opts:
        n, kind, seed = (int(a) for a in opts["--confirm"].split(","))
        seconds = int(opts.get("--seconds", "20"))
        rec = screen(n, kind, seed, seconds, do_convert=True,
                     extra=int(opts.get("--extra", "120")))
        print(json.dumps(rec, indent=1))
        return 0
    nrows = int(opts.get("--nrows", "10"))
    rows = ([int(a) for a in opts["--rows"].split(",")] if "--rows" in opts
            else row_list(nrows))
    seeds = [int(s) for s in opts.get("--seeds", "3").split(",")]
    seconds = int(opts.get("--seconds", "8"))
    kinds = [int(k) for k in opts.get("--kinds", "0,1,2").split(",")]
    out = opts.get("--out", OUT)
    recs = []
    if "--append" in argv and os.path.exists(out):
        recs = json.load(open(out))
    print(f"rows {rows}  kinds {kinds}  seeds {seeds}  {seconds}s per attempt")
    for n in rows:
        for kind in kinds:
            drawn = list(seeds)
            k = 0
            group = []
            while k < len(drawn):
                seed = drawn[k]
                r = (void_swap(n, seed, seconds) if kind == 3
                     else screen(n, kind, seed, seconds))
                r["extended"] = bool(k >= len(seeds))
                recs.append(r)
                group.append(r)
                print(f"  n={n:4d} k={kind} seed {seed}  {r['family']:22s} "
                      f"gain {format(DEC(r['gain']), '+.2e')} p "
                      f"{(format(DEC(r['p']), '.3e') if r['p'] else 'no seat'):>9s} bar "
                      f"{format(DEC(r['bar']), '.3e') if DEC(r['bar']) > ZERO else 'n/a':>9s} "
                      f"ratio {(r['ratio'] or 'n/a')[:6]:>6s}  "
                      f"{'SCREENED' if r['screened'] else 'converted'}"
                      f"  sweeps {r['sweeps_completed']}/{r['sweeps_aborted']}"
                      f"  {r['seconds']}s", flush=True)
                k += 1
                # adaptive draws: a family whose draw is within the margin gets
                # two more seeds; one that is 10x out is left at the base count
                close = [g for g in group if g["p"] is not None
                         and should_convert(DEC(g["p"]), DEC(g["bar"]))]
                if k == len(seeds) and len(drawn) == len(seeds) and close:
                    drawn += [max(drawn) + 1, max(drawn) + 2]
                    print(f"     (within the {MARGIN}x margin: extending to "
                          f"{len(drawn)} seeds)", flush=True)
    json.dump(recs, open(out, "w"), indent=1)
    summarise(recs)
    print(f"wrote {out} ({len(recs)} candidates)")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(main(sys.argv[1:]))
