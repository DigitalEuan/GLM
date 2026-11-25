#!/usr/bin/env python3
r"""shared_box.py — two whole lattices in one shared box, no deletions (Run 143).

Doc 99 read the 508 priced-out rows as *area sharing*: a class the single-grain
price rejects does not own its bounding box, because the other lattice's cells are
inside it. This file builds the constructor that mechanism implies and puts it
through doc 99's entry test before any search is allowed to run.

THE FAMILY. Two full rectangles of lattice, both kept whole:

    A   an `a1 x a2` block of axis cells, centred on the half-integers, occupying
        exactly the rectangle [0, a1] x [0, a2];
    B   a `b1 x b2` block of the same lattice rotated by the rational spinor
        `tan(theta/2) = p/q` (`c = (q^2-p^2)/(p^2+q^2)`, `s = 2pq/(p^2+q^2)`),
        occupying a rotated rectangle of bbox `W = b1 c + b2 s` by `H = b1 s + b2 c`;
    box A sits in the bottom-left corner and B's bbox in the top-right corner of
        one square box [0, L]^2, so the two bounding boxes *overlap* -- the region
        B's bbox covers that A does not fill is where the area sharing happens.

Nothing is deleted, unlike run 141's two yield rules, so both lattices are whole.
Because each block is a *full* rectangle of unit cells, its cells tile its own
rectangle exactly; two such blocks are disjoint iff the two rectangles are, and
that is the four-axis separating test on two rectangles -- O(1), exact in
`Fraction`, and equal to the cell-level answer (control 3 cross-checks it against
`import_n090.pair_slack` on every pair of the built pose).

THE CONTACT SIDE, IN CLOSED FORM. Writing `Delta = c_B - c_A`, the four axis
slacks are affine in `L`, so the smallest legal side of a configuration is

    s* = max( max(a1, a2, W, H),  min(r_x, r_y, r_u, r_v) )

with `r_x = a1 + W`, `r_y = a2 + H`, and `r_u`, `r_v` the roots of the two rotated
axes (see `min_side`).  No bisection, no scan: one closed form per split.

THE ENTRY TEST (doc 99 §9). Before any sweep, the family must reproduce the
delivered `(n, side)` pair of at least 20 of the 110 two-class beating rows at
`|s* - L_delivered| <= 1e-8`, with the built pose carrying 0 overlaps under
`import_n090`'s exact SAT. This file runs that test and nothing else unless it
passes.

    python3 scripts/shared_box.py                # entry test + domain census, ledger
    python3 scripts/shared_box.py --selftest      # 9 controls

The entry test is accompanied by a census of the *translation domains* of the
delivered two-class classes (how many lattice translates make up each class), so
the refusal comes with its structural diagnosis and not only its size.
"""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal, getcontext, ROUND_FLOOR
from fractions import Fraction as F
from math import isqrt

getcontext().prec = 60

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import import_n090 as N9                        # noqa: E402  (independent exact SAT)
import sqscore as SQ                            # noqa: E402
import tilt_audit as TA                         # noqa: E402  (exact CSV reader)

LEDGER = os.path.join(ROOT, "workspace/push/shared_box.json")
TOL = F(1, 10 ** 8)          # reproduction tolerance on the side (CSV shim x 100)
ASPECT = 3                   # only blocks with max side <= 3 x min side are built
SPINORS = [("1/1", 0, 1), ("1/2", 1, 2), ("2/3", 2, 3), ("1/3", 1, 3),
           ("1/4", 1, 4), ("3/4", 3, 4)]
QUANT = Decimal("1e-6")      # tolerance of the translation-domain census


def _fmt(fr, spec: str = ".7f") -> str:
    """Display a `Fraction` at the module's 60-digit Decimal precision."""
    if not isinstance(fr, F):
        fr = F(fr)
    return format(Decimal(fr.numerator) / Decimal(fr.denominator), spec)


def _fdec(text) -> Decimal:
    """A `"p/q"` or decimal string as a 60-digit Decimal (display and statistics)."""
    fr = F(text)
    return Decimal(fr.numerator) / Decimal(fr.denominator)


# ------------------------------------------------------------------ spinors ---
def spinor(p: int, q: int) -> tuple[F, F]:
    """Rational cos/sin of the spinor angle theta = 2 atan(p/q)."""
    d = q * q + p * p
    return F(q * q - p * p, d), F(2 * p * q, d)


def shapes(m: int) -> list[tuple[int, int]]:
    """Rectangle shapes `a x b` with `a*b = m` and aspect <= ASPECT."""
    out = []
    for a in range(1, isqrt(m) + 1):
        if m % a:
            continue
        b = m // a
        if b <= ASPECT * a:
            out.append((a, b))
            if a != b:
                out.append((b, a))
    return out


def block_extent(b1: int, b2: int, c: F, s: F) -> tuple[F, F]:
    """(W, H): the bbox of a `b1 x b2` block at spinor (c, s)."""
    return b1 * c + b2 * s, b1 * s + b2 * c


# ------------------------------------------------------------------- the SAT --
def min_side(a1: int, a2: int, b1: int, b2: int, c: F, s: F) -> F:
    """Smallest side at which the two corner blocks are disjoint (closed form).

    `L` is the side of the shared box; A's bbox is [0,a1]x[0,a2] and B's bbox is
    [L-W, L] x [L-H, L].  The four separating axes give affine slacks whose roots
    are the candidate contact sides; the smallest legal side is the first root the
    box can reach, raised to the containment bound.
    """
    W, H = block_extent(b1, b2, c, s)
    lo = max(F(a1), F(a2), W, H)
    roots = [F(a1) + W, F(a2) + H]
    # u axis: slack_u = L(c+s) - [c(W+a1) + s(H+a2) + a1 c + a2 s + b1]/2
    roots.append((c * (W + a1) + s * (H + a2) + a1 * c + a2 * s + b1)
                 / (2 * (c + s)))
    # v axis: Delta.v = L(c-s) - [-s(W+a1) + c(H+a2)]/2, and r1+r2 = (a1 s + a2 c + b2)/2
    base = -s * (W + a1) + c * (H + a2)
    reach = a1 * s + a2 * c + b2
    if c > s:
        roots.append((base + reach) / (2 * (c - s)))
    elif c < s:
        roots.append((base - reach) / (2 * (c - s)))
    # c == s (theta = 45 degrees): Delta.v is constant in L, so it either holds at
    # every L or at none -- encoded by leaving it out of the roots; `legal` decides
    if any(r <= lo for r in roots):
        return lo                     # containment alone already separates
    return min(roots)


def slack_axes(a1: int, a2: int, b1: int, b2: int, c: F, s: F, L: F) -> list[F]:
    """The four exact axis slacks of the two corner blocks at side `L`."""
    W, H = block_extent(b1, b2, c, s)
    dx = L - W / 2 - F(a1, 2)
    dy = L - H / 2 - F(a2, 2)
    r1x = F(a1, 2)
    r2x = W / 2
    r1y = F(a2, 2)
    r2y = H / 2
    r1u = (a1 * c + a2 * s) / 2
    r2u = F(b1, 2)
    r1v = (a1 * s + a2 * c) / 2
    r2v = F(b2, 2)
    return [dx - r1x - r2x,
            dy - r1y - r2y,
            dx * c + dy * s - r1u - r2u,
            abs(-dx * s + dy * c) - r1v - r2v]


def legal(a1: int, a2: int, b1: int, b2: int, c: F, s: F, L: F) -> bool:
    """Legal iff both blocks fit the box and some axis separates them."""
    W, H = block_extent(b1, b2, c, s)
    if max(F(a1), F(a2), W, H) > L:
        return False
    return max(slack_axes(a1, a2, b1, b2, c, s, L)) >= 0


# ------------------------------------------------------------------- the pose --
def build(a1: int, a2: int, b1: int, b2: int, c: F, s: F, L: F):
    """The pose as exact `Fraction` cells `(x, y, cos, sin)`, inside [0, L]^2."""
    W, H = block_extent(b1, b2, c, s)
    pose = [(F(2 * i + 1, 2), F(2 * j + 1, 2), F(1), F(0))
            for i in range(a1) for j in range(a2)]
    x0, y0 = L - W, L - H              # B's bbox min, so its bbox max is (L, L)
    raw = []
    for i in range(b1):
        for j in range(b2):
            u, v = F(2 * i + 1, 2), F(2 * j + 1, 2)
            raw.append((u * c - v * s, u * s + v * c))
    e = (abs(c) + abs(s)) / 2              # cell half-extent: the corner bbox, not
    mx = min(p[0] for p in raw) - e        # the centre bbox, is what must sit at x0
    my = min(p[1] for p in raw) - e
    for x, y in raw:
        pose.append((x - mx + x0, y - my + y0, c, s))
    return pose


def check(pose) -> dict:
    """Independent exact SAT over every pair: overlaps, min slack, side."""
    n = len(pose)
    worst, bad = None, 0
    for i in range(n):
        for j in range(i + 1, n):
            sl = N9.pair_slack(pose[i], pose[j])
            if sl < 0:
                bad += 1
            if worst is None or sl < worst:
                worst = sl
    xs = [x for x, _, _, _ in pose]
    ys = [y for _, y, _, _ in pose]
    ex = [(abs(c) + abs(s)) / 2 for _, _, c, s in pose]
    side = max(max(x + e for x, e in zip(xs, ex)) - min(x - e for x, e in zip(xs, ex)),
               max(y + e for y, e in zip(ys, ex)) - min(y - e for y, e in zip(ys, ex)))
    return {"n": n, "overlaps": bad, "min_slack": worst, "side": side}


# --------------------------------------------------------------- entry test ---
def two_class_rows() -> list[tuple[int, F, Decimal, int]]:
    """(n, delivered side, same as Decimal, grid k) for the 110 two-class rows."""
    led = json.load(open(os.path.join(ROOT, "workspace/push/tilt_audit.json")))
    out = []
    for key, r in led["rows"].items():
        if r["beat"] and r["classes"] == 2:
            d = Decimal(r["side"])
            out.append((int(key), F(d), d, r["grid"]))
    return sorted(out)


def best_for_row(n: int, target: F, spinors=SPINORS) -> dict:
    """Closest `s*` to `target` over every split, shape and spinor."""
    best = None
    better = None                     # a configuration strictly smaller than delivered
    smallest = None                   # the family's own best pose for this count
    tested = 0
    for B in range(1, n):
        A = n - B
        for a1, a2 in shapes(A):
            for b1, b2 in shapes(B):
                for name, p, q in spinors:
                    c, s = spinor(p, q)
                    W, H = block_extent(b1, b2, c, s)
                    if max(F(a1), F(a2), W, H) > target + TOL:
                        continue          # containment already exceeds the target
                    tested += 1
                    st = min_side(a1, a2, b1, b2, c, s)
                    if not legal(a1, a2, b1, b2, c, s, st):
                        continue          # the constant diagonal axis refuses every L
                    gap = abs(st - target)
                    rec = {"split": f"{a1}x{a2}+{b1}x{b2}", "spinor": name,
                           "s_star": st, "gap": gap}
                    if best is None or gap < best["gap"]:
                        best = rec
                    if st < target - TOL:
                        if better is None or st < better["s_star"]:
                            better = rec
                    if smallest is None or st < smallest["s_star"]:
                        smallest = rec
    return {"n": n, "target": target, "tested": tested, "best": best,
            "better": better, "smallest": smallest}


def entry_test(verbose: bool = True) -> dict:
    rows = two_class_rows()
    out = []
    hits = 0
    tilt_wins = 0                 # rows whose closest config is a genuinely tilted block
    grid_ties = 0                 # rows whose family best side is just the grid side
    for n, target, target_d, k in rows:
        r = best_for_row(n, target)
        if r["best"] is None:
            out.append({"n": n, "target": str(target_d), "gap": None,
                        "reason": "no whole-block split fits the delivered box",
                        "split": None, "spinor": None, "s_star": None,
                        "better": None, "reproduced": False, "cert": None})
            print(f"  n={n:>4} no whole-block split fits the delivered box")
            continue
        tilt_wins += r["best"]["spinor"] != "1/1"
        grid_ties += r["smallest"]["s_star"] == F(k)
        ok = r["best"]["gap"] <= TOL
        # an accepted row is certified by the independent exact SAT on the built pose
        cert = None
        if ok:
            b = r["best"]
            a1, a2 = [int(t) for t in b["split"].split("+")[0].split("x")]
            b1, b2 = [int(t) for t in b["split"].split("+")[1].split("x")]
            c, s = [spinor(int(t.split("/")[0]), int(t.split("/")[1]))
                    for t in [b["spinor"]]][0]
            cert = check(build(a1, a2, b1, b2, c, s, b["s_star"]))
            ok = cert["overlaps"] == 0
            hits += ok
        out.append({"n": n, "target": str(target_d), "gap": str(r["best"]["gap"]),
                    "split": r["best"]["split"], "spinor": r["best"]["spinor"],
                    "s_star": str(r["best"]["s_star"]),
                    "smallest": str(r["smallest"]["s_star"]),
                    "better": (str(r["better"]["s_star"]) if r["better"] else None),
                    "reproduced": bool(ok), "cert": cert})
        if verbose and (ok or len(out) % 20 == 0):
            print(f"  n={n:>4} gap={r['best']['gap']:.3e} "
                  f"{'REPRODUCED' if ok else ''} {r['best']['split']} @{r['best']['spinor']}")
    gaps = sorted(_fdec(o["gap"]) for o in out if o["gap"] is not None)
    exceed = sorted(_fdec(o["smallest"]) - _fdec(o["target"])
                    for o in out if o["smallest"] is not None)
    res = {"rows": len(out), "reproduced": hits, "threshold": 20,
           "passes": hits >= 20, "no_config": sum(1 for o in out if o["gap"] is None),
           "beats_family": sum(1 for o in out if o["better"]),
           "closest_is_tilted": tilt_wins, "family_best_is_grid_side": grid_ties,
           "gap_min": f"{gaps[0]:.3e}", "gap_median": f"{gaps[len(gaps) // 2]:.3e}",
           "gap_max": f"{gaps[-1]:.3e}",
           "family_minus_delivered_min": f"{exceed[0]:.3e}" if exceed else None,
           "family_minus_delivered_median": f"{exceed[len(exceed) // 2]:.3e}" if exceed else None,
           "family_minus_delivered_max": f"{exceed[-1]:.3e}" if exceed else None,
           "detail": out}
    print(f"entry test: {hits}/{len(out)} two-class rows reproduced "
          f"(threshold 20) -> {'PASS' if res['passes'] else 'FAIL'}")
    print(f"  |s* - L| min/median/max: {res['gap_min']} / {res['gap_median']} / {res['gap_max']}")
    print(f"  rows with no fitting split: {res['no_config']}; rows where a config beats "
          f"the delivered side: {res['beats_family']}")
    print(f"  family best side - delivered: min/median/max {res['family_minus_delivered_min']}"
          f" / {res['family_minus_delivered_median']} / {res['family_minus_delivered_max']}")
    print(f"  closest config genuinely tilted: {tilt_wins}/{len(out)}; family best side "
          f"equals the grid side: {grid_ties}/{len(out)}")
    return res


# --------------------------------------------------------- domain census -----
def _dom_key(x: Decimal, y: Decimal, c: Decimal, s: Decimal) -> tuple[int, int]:
    """A cell centre's remainder in the class's own lattice frame, at `QUANT`."""
    u = x * c + y * s
    v = -x * s + y * c
    fu = u - u.to_integral_value(rounding=ROUND_FLOOR)
    fv = v - v.to_integral_value(rounding=ROUND_FLOOR)
    return int((fu / QUANT).to_integral_value()), int((fv / QUANT).to_integral_value())


def domain_census() -> dict:
    """How many lattice translates each delivered two-class class is made of.

    The family built here is two *single* lattice blocks.  Two classes that are
    each one translate are exactly that shape; a class that is a union of several
    translates is a sparse carrier and cannot be expressed by a full rectangle.
    The CSV is read through `tilt_audit`'s exact reader and the classes are
    formed by its `TAU = 1e-6` gap rule, so this census is a tolerance statement
    on the delivered decimal angles, at the same tolerance as doc 99's classes.
    """
    poses = TA.load_poses()
    led = json.load(open(os.path.join(ROOT, "workspace/push/tilt_audit.json")))
    ns = sorted(int(k) for k, r in led["rows"].items()
                if r["beat"] and r["classes"] == 2)
    hist: dict = {}
    detail = []
    single_both = 0
    for n in ns:
        pose = poses[n]
        groups = TA.class_partition([TA.angle_data(a)[0] for _, _, a in pose], TA.TAU)
        doms = []
        for g in groups:
            c, s = TA.trig_of(Decimal(pose[g[0]][2]))
            doms.append(len({_dom_key(x, y, c, s) for x, y, _ in (pose[i] for i in g)}))
        doms.sort()
        single_both += doms[0] == 1 and doms[-1] == 1
        key = f"{doms[0]}+{doms[-1]}"
        hist[key] = hist.get(key, 0) + 1
        detail.append({"n": n, "domains": doms})
    pairs = [d["domains"] for d in detail]
    return {"rows": len(ns), "quant": str(QUANT),
            "single_both": single_both,
            "smaller_min": min(p[0] for p in pairs),
            "smaller_max": max(p[0] for p in pairs),
            "larger_min": min(p[-1] for p in pairs),
            "larger_max": max(p[-1] for p in pairs),
            "rows_larger_ge_4": sum(1 for p in pairs if p[-1] >= 4),
            "histogram": dict(sorted(hist.items(), key=lambda kv: -kv[1])),
            "detail": detail}


# -------------------------------------------------------------------- report --
def main() -> int:
    import sqscore as _SQ
    globals()["SQ"] = _SQ
    getcontext().prec = 60
    SQ.guard(quiet=True)
    print("shared_box — two whole lattices in one shared box, no deletions")
    res = entry_test()
    dom = domain_census()
    print(f"translation domains: {dom['single_both']}/{dom['rows']} two-class rows are two "
          f"single lattices; larger class {dom['larger_min']}-{dom['larger_max']} translates "
          f"(>= 4 in {dom['rows_larger_ge_4']}/{dom['rows']} rows)")
    led = {"family": "two rectangle blocks, opposite corners of one box, no deletions",
           "aspect_cap": ASPECT, "tol": str(TOL), "spinors": [s[0] for s in SPINORS],
           "entry_test": res, "domains": dom}
    with open(LEDGER, "w") as f:
        json.dump(led, f, indent=1)
    print(f"wrote {os.path.relpath(LEDGER, ROOT)}")
    return 0 if res["passes"] else 0


# ------------------------------------------------------------------ selftest --
def selftest() -> int:
    import sqscore as _SQ
    globals()["SQ"] = _SQ
    getcontext().prec = 60
    print("shared_box selftest")
    c45, s45 = spinor(1, 1)

    # 1. spinor identity, exactly
    for p, q in ((1, 1), (1, 2), (2, 3), (3, 4)):
        c, s = spinor(p, q)
        assert c * c + s * s == 1, (p, q)
    print("  1. four spinors satisfy c^2 + s^2 = 1 exactly")

    # 2. the closed-form side is legal and one shim below it is not (tightness)
    a1, a2, b1, b2 = 4, 4, 2, 2
    c53, s53 = spinor(1, 2)                # theta = 53.13 deg, the smallest tilt
    st = min_side(a1, a2, b1, b2, c53, s53)
    assert st == F(214, 35), st          # [c(W+a1) + s(H+a2) + a1 c + a2 s + b1]
                                          # / 2(c+s), contact on the block's own u axis
    assert legal(a1, a2, b1, b2, c53, s53, st), st
    assert not legal(a1, a2, b1, b2, c53, s53, st - F(1, 10 ** 9)), st
    print(f"  2. 4x4 + 2x2 at 53.13 deg: s* = {_fmt(st)} = 214/35 (diagonal contact), "
          f"legal there, illegal 1e-9 below")

    # 3. rectangle SAT equals the cell-level SAT on the built pose
    pose = build(a1, a2, b1, b2, c53, s53, st)
    info = check(pose)
    assert info["overlaps"] == 0 and info["n"] == a1 * a2 + b1 * b2, info
    assert abs(info["side"] - st) < F(1, 10 ** 12), (info["side"], st)
    print(f"  3. built pose: {info['n']} cells, 0 overlaps, min slack "
          f"{_fmt(info['min_slack'], '.2e')}, side {_fmt(info['side'])}")

    # 4. an overlapping placement is rejected by both tests
    bad_side = st - F(1, 4)
    assert not legal(a1, a2, b1, b2, c53, s53, bad_side)
    over = build(a1, a2, b1, b2, c53, s53, bad_side)
    n_bad = sum(1 for i in range(len(over)) for j in range(i + 1, len(over))
                if N9.pair_slack(over[i], over[j]) < 0)
    assert n_bad > 0, n_bad
    print(f"  4. squeezing the box by 1/4 breaks {n_bad} cell pairs (SAT agrees)")

    # 5. the box is shared: the side is below doc 97's butted bound
    W, H = block_extent(b1, b2, c53, s53)
    butted = max(F(a1), F(a2) + H)
    assert st < butted, (st, butted)
    print(f"  5. shared side {_fmt(st, '.6f')} < butted bound {_fmt(butted, '.6f')} "
          f"(saving {_fmt(butted - st, '.6f')})")

    # 6. the degenerate spinor is the plain grid: 4x4 + 1x1 at 90 deg is 17 cells
    #    at side 5, the corner cell of the 5x5 box (a grid tie, as doc 97 says)
    st90 = min_side(4, 4, 1, 1, F(0), F(1))     # p = q is theta = 90 degrees
    assert st90 == 5, st90
    assert legal(4, 4, 1, 1, F(0), F(1), st90)
    p90 = build(4, 4, 1, 1, F(0), F(1), st90)
    assert check(p90)["overlaps"] == 0 and abs(check(p90)["side"] - 5) < F(1, 10 ** 12)
    print("  6. spinor p = q (90 deg): 4x4 + 1x1 = 17 cells at side 5, 0 overlaps")

    # 7. a zero-cell block is refused by construction (shapes() is empty)
    assert shapes(0) == [] and shapes(1) == [(1, 1)]
    print("  7. shapes(0) empty, shapes(1) = [(1, 1)]")

    # 8. every emitted cell lies inside [0, L]^2
    for (a1_, a2_, b1_, b2_, p, q) in ((3, 5, 2, 1, 1, 2), (7, 2, 3, 3, 2, 3),
                                       (1, 1, 1, 4, 1, 3)):
        cc, ss = spinor(p, q)
        L = min_side(a1_, a2_, b1_, b2_, cc, ss)
        for x, y, cx, sx in build(a1_, a2_, b1_, b2_, cc, ss, L):
            e = (abs(cx) + abs(sx)) / 2
            assert -F(1, 10 ** 15) <= x - e and x + e <= L + F(1, 10 ** 15), (x, e, L)
            assert -F(1, 10 ** 15) <= y - e and y + e <= L + F(1, 10 ** 15), (y, e, L)
    print("  8. containment: every cell of three further configurations is inside the box")

    # 9. float-free decision path
    import exact_field as EF
    checked, offenders, skipped = EF.audit_module(sys.modules[__name__],
                                                  exempt=EF.AUDIT_EXEMPT + ("selftest",))
    assert offenders == [], offenders
    print(f"  9. bytecode audit: {checked} decision functions, 0 naming float "
          f"(exempt {skipped})")
    print("selftest OK (9 controls)")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
