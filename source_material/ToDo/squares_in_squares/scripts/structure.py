#!/usr/bin/env python3
r"""structure.py — runs 124/126: the structure-changing route on the unbeaten rows.

Doc 82 closed the local routes (closure settler, polish clamps, free-position
perturbation) and pointed at the family that changes *which cells sit where*:
`resqueeze`'s patch-coordinate relaxation and the block-swap idea of run 115.
The difference that matters is that this relaxation is a **penalty** method: it
may pass *through* overlapping states, so unlike `perturb.py` it is not stopped
by a contact.  A new packing is allowed to be transiently illegal on the way.

Per row, inside a wall-clock budget:

  attempt 0  hinge   container hinged at L0 - TARGET and every patch relaxed;
  attempt 1  hinge   the same after a random 3-cell block is teleported into
                     free space (a block swap that changes the tiling);
  attempt 2  hinge   after a 2x2 block is rotated 90 degrees about its centroid.

Every attempt is judged at 40 digits by `true_geom`: a result counts only if it
has **zero violations** and a side **strictly below the delivered side**.

Controls (run with --control), because a null is worthless without them:

  A  recovery — inflate a delivered pose by a known 5e-3, hinge it back at the
     delivered side, and require the machinery to return a legal pose.  Proves
     the relaxer closes a known gap at the scale the score needs.
  B  structural absorb — teleport one cell from the interior to a free-space
     void and relax at the delivered side; the pose must legalise again.  Proves
     a *changed arrangement* is absorbed, not just a scaled copy of the old one.

Run 126 (doc 85) made the patch solve affordable, so a sweep now finishes on
every tested row: the pose is compacted to the patch plus its neighbourhood and
the gradient is analytic (`patch_problem`), 374-410 ms -> ~2 ms per patch, and a
sweep at n=942 costs 3.2 s instead of 163.3 s.  Each attempt records
`sweeps_completed` / `sweeps_aborted` / `patches_solved`, so a zero can no longer
be produced by a sweep that was cut off, and the per-attempt budget is split
60/40 between the squeeze and the projection (`relax` used to consume all of it,
leaving the projection untested).

Discovery arithmetic is float (like resqueeze/relax_angles); every number that
decides anything is `true_geom` at 40 digits.

    python3 scripts/structure.py --control
    python3 scripts/structure.py --check-solver      # gradient vs scipy FD
    python3 scripts/structure.py --rows 20 --seconds 20 --iters 10 --proj-iters 40
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import sqscore as SQ                     # noqa: E402
import true_geom as TG                   # noqa: E402
import perturb as PB                     # noqa: E402
from resqueeze import total_pen   # noqa: E402

TAB = os.path.join(ROOT, "workspace/submission/table.json")
OUT = os.path.join(ROOT, "workspace/push/structure124.json")

TARGET = 4e-3          # the dL the score actually needs (doc 72 band 4e-3..1e-2)


def load_pose(n):
    """(X, Y, T) floats for discovery, and the 40-digit side."""
    with open(TAB) as f:
        tab = json.load(f, **{"parse_float": str})
    rec = tab[str(n)]
    state = [(float(r[0]), float(r[1]), float(r[2])) for r in rec["state"]]
    X = np.array([s[0] for s in state])
    Y = np.array([s[1] for s in state])
    T = np.array([s[2] for s in state])
    # The delivered side is the O(n) exact side (`true_geom.side`), not the
    # O(n^2) pair pass: on a 999-cell row the pair pass costs 85 s and returns
    # the same number.
    return X, Y, T, exact_side(X, Y, T)


def side40(X, Y, T):
    chk = TG.check([(repr(float(a)), repr(float(b)), repr(float(c)))
                    for a, b, c in zip(X, Y, T)])
    return chk["side"], len(chk["violations"]), chk


SCREEN = 1e-6          # penetration far above rounding: illegal at 40 digits


def exact_side(X, Y, T):
    """The 40-digit container side in O(n).

    `side40` runs the full separating-axis pass, which is O(n^2): 85 s on a
    999-cell pose.  The *side* only needs the extreme walls (`true_geom.side`),
    so a side can be compared exactly at any size for the cost of n cosines.
    Legality still needs the pair pass, and is only paid where it can change a
    verdict (see `legalise`).
    """
    return +TG.side([(float(a), float(b), float(c)) for a, b, c in zip(X, Y, T)])


def clearly_illegal(X, Y, T):
    """True when a pair overlaps far beyond what float rounding can explain.

    Sound as a *rejection* only: at coordinates of order 32 the float error in a
    penetration is ~1e-14, so a measured 1e-6 overlap cannot be legal at 40
    digits.  It never certifies legality -- that is `side40`'s job.
    """
    return total_pen(X, Y, T)[1] > SCREEN


def box_for(L, X, Y, T):
    h = 0.5 * (np.abs(np.cos(T)) + np.abs(np.sin(T)))
    xm = 0.5 * (float((X - h).min()) + float((X + h).max()))
    ym = 0.5 * (float((Y - h).min()) + float((Y + h).max()))
    half = L / 2.0
    return xm - half, xm + half, ym - half, ym + half


def patches(X, Y, size=3.0, step=1.5):
    """Overlapping square patches of cells, by centre position.

    This replaces `resqueeze.patches`, which uses `while x < hi_x` / `while y <
    hi_y` and therefore returns an **empty list** when the pose's extent in a
    direction is zero, and can skip the last row and column of patches.  A run
    whose patch list is empty relaxes nothing and reports a null for a
    mechanical reason — the positive control caught exactly that here.
    """
    out = []
    lo_x, hi_x = float(X.min()), float(X.max())
    lo_y, hi_y = float(Y.min()), float(Y.max())
    x = lo_x
    while x <= hi_x + 1e-12:
        y = lo_y
        while y <= hi_y + 1e-12:
            idx = np.nonzero((X >= x) & (X <= x + size)
                             & (Y >= y) & (Y <= y + size))[0]
            if len(idx) >= 2:
                out.append(idx)
            y += step
        x += step
    if not out:
        out = [np.arange(len(X))]
    return out


def near_cells(X, Y, idx, reach=2.6):
    """Outside cells within `reach` (L1 centre distance) of any patch cell.

    Vectorised replacement for the python loop that used to do one numpy call
    per cell of the pose; the *set* returned is identical (same reach, same
    L1 measure), which is what the penalty's pair list depends on.
    """
    n = len(X)
    inside = np.zeros(n, dtype=bool)
    inside[idx] = True
    dx = np.abs(X[:, None] - X[idx][None, :])
    dy = np.abs(Y[:, None] - Y[idx][None, :])
    return np.nonzero((~inside) & ((dx + dy).min(axis=1) <= reach))[0]


def patch_problem(X, Y, T, idx, lo, hi, wall_w, eps=1e-9, calls=None):
    """The patch objective and its batched forward-difference gradient.

    Compacted to the patch plus its neighbours (`near_cells`), so one objective
    call touches only the cells the patch can actually press on.  The pair list
    is the same one the original solver used -- intra-patch pairs *and*
    patch-vs-neighbour pairs -- with the same `eps`, and the wall term carries
    the same `wall_w`, so the function being minimised is unchanged.

    The gradient is the 2-point forward difference scipy would compute anyway
    (`h = sqrt(eps) * max(1, |z|)`), but for all 3c variables at once: the
    perturbations are stacked into one (3c, m) batch.  This is the same
    arithmetic per variable, evaluated in a single pass.
    """
    from void_insert import pen_vec
    idx = np.asarray(idx)
    c = len(idx)
    near = near_cells(X, Y, idx)
    comp = np.concatenate([idx, near])
    m = len(comp)
    cx, cy, ct = X[comp], Y[comp], T[comp]
    pi, pj = [], []
    for a_i in range(c):
        for b_i in range(a_i + 1, c):
            pi.append(a_i)
            pj.append(b_i)
        for o in range(c, m):
            pi.append(a_i)
            pj.append(o)
    pi = np.array(pi, dtype=int)
    pj = np.array(pj, dtype=int)

    def wall(ax, ay, at):
        hx = 0.5 * (np.abs(np.cos(at)) + np.abs(np.sin(at)))
        return (np.clip(ax + hx - hi, 0, None) ** 2
                + np.clip(lo - ax + hx, 0, None) ** 2
                + np.clip(ay + hx - hi, 0, None) ** 2
                + np.clip(lo - ay + hx, 0, None) ** 2)

    def unpack(z):
        ax, ay, at = cx.copy(), cy.copy(), ct.copy()
        ax[:c], ay[:c], at[:c] = z[:c], z[c:2 * c], z[2 * c:]
        return ax, ay, at

    def obj(z):
        if calls is not None:
            calls["objective"] = calls.get("objective", 0) + 1
        ax, ay, at = unpack(z)
        if len(pi):
            pen = pen_vec(ax[pi], ay[pi], at[pi], ax[pj], ay[pj], at[pj], eps=eps)
            pv = float((pen ** 2).sum())
        else:
            pv = 0.0
        return pv + wall_w * float(wall(ax[:c], ay[:c], at[:c]).sum())

    def jac(z):
        """Analytic gradient of `obj`, one pass over the four separating axes.

        `pen_vec` takes the penetration p = clip(eps - best, 0), where `best` is
        the maximum separation over the four edge normals of the pair.  Where
        the maximum is attained by axis q, best = |d.q| - hA(q) - hB(q), so

            d(p^2)/dv = -2 p * d(best)/dv        (0 where p = 0)

        and d(best)/dv is the derivative of that axis's separation alone.  The
        angle derivatives include the *rotating axis* itself (for an axis owned
        by cell A, dq/dat is the other unit vector of A), which is what makes
        the shape derivative come out right rather than only the translation
        part.  hA and hB are each exactly 1/2 on their owner's own axes and
        carry d/dat = (sign(u) v - sign(v) u)/2 on the other cell's axes.

        This is the same gradient the finite-difference batch approximates,
        without the 4-per-pair trig: run 126 measured the FD batch at 2.2 ms
        and this at a fraction of it.  `--check-solver` compares it with
        scipy's own finite differences at the start pose and at perturbed ones.
        """
        out = np.zeros(3 * c)
        if len(pi):
            bx, by, bt = unpack(z)
            XA, YA, TA = bx[pi], by[pi], bt[pi]
            XB, YB, TB = bx[pj], by[pj], bt[pj]
            cA, sA = np.cos(TA), np.sin(TA)
            cB, sB = np.cos(TB), np.sin(TB)
            d1, d2 = XA - XB, YA - YB
            nP = len(pi)
            axes = ((cA, sA), (-sA, cA), (cB, sB), (-sB, cB))
            sep = np.empty((4, nP))
            dax = np.empty((4, nP))
            day = np.empty((4, nP))
            dat = np.empty((4, nP))
            dbx = np.empty((4, nP))
            dby = np.empty((4, nP))
            dbt = np.empty((4, nP))
            for k, (qx, qy) in enumerate(axes):
                signed = d1 * qx + d2 * qy
                proj = np.abs(signed)
                uA, vA = cA * qx + sA * qy, -sA * qx + cA * qy
                uB, vB = cB * qx + sB * qy, -sB * qx + cB * qy
                sep[k] = proj - 0.5 * (np.abs(uA) + np.abs(vA)) \
                    - 0.5 * (np.abs(uB) + np.abs(vB))
                sgn = np.sign(signed)
                dax[k], day[k] = sgn * qx, sgn * qy
                dbx[k], dby[k] = -dax[k], -day[k]
                if k == 0:                       # A's own first axis rotates
                    dproj_at = sgn * (-d1 * sA + d2 * cA)
                elif k == 1:                     # A's second axis rotates
                    dproj_at = sgn * (-(d1 * cA + d2 * sA))
                else:
                    dproj_at = 0.0
                if k == 2:                       # B's own first axis rotates
                    dproj_bt = sgn * (-d1 * sB + d2 * cB)
                elif k == 3:                     # B's second axis rotates
                    dproj_bt = sgn * (-(d1 * cB + d2 * sB))
                else:
                    dproj_bt = 0.0
                dhA = 0.5 * (np.sign(uA) * vA - np.sign(vA) * uA)
                dhB = 0.5 * (np.sign(uB) * vB - np.sign(vB) * uB)
                dat[k] = dproj_at - dhA
                dbt[k] = dproj_bt - dhB
            pick = np.argmax(sep, axis=0)
            col = np.arange(nP)
            best = sep[pick, col]
            p = np.clip(eps - best, 0.0, None)
            coef = np.where(p > 0, -2.0 * p, 0.0)
            gx = np.bincount(pi, weights=coef * dax[pick, col], minlength=c)
            gy = np.bincount(pi, weights=coef * day[pick, col], minlength=c)
            gt = np.bincount(pi, weights=coef * dat[pick, col], minlength=c)
            far = pj < c                       # b-side moves only for neighbours
            if far.any():
                jb = pj[far]
                gx += np.bincount(jb, weights=(coef * dbx[pick, col])[far],
                                  minlength=c)
                gy += np.bincount(jb, weights=(coef * dby[pick, col])[far],
                                  minlength=c)
                gt += np.bincount(jb, weights=(coef * dbt[pick, col])[far],
                                  minlength=c)
            out[:c], out[c:2 * c], out[2 * c:] = gx, gy, gt

        # container term: over(X, Y, T) per patch cell, same expression as `obj`
        bx, by, bt = unpack(z)
        px, py, pt = bx[:c], by[:c], bt[:c]
        hx = 0.5 * (np.abs(np.cos(pt)) + np.abs(np.sin(pt)))
        # hx has a cusp at theta = 0 (it is a minimum), so take the right-hand
        # slope there: sign(0) is 0 and would silently report no torque.
        sgn0 = lambda v: np.where(v >= 0, 1.0, -1.0)      # noqa: E731
        dhx = 0.5 * (-np.sin(pt) * sgn0(np.cos(pt))
                     + np.cos(pt) * sgn0(np.sin(pt)))
        ox1 = np.clip(px + hx - hi, 0, None)
        ox0 = np.clip(lo - px + hx, 0, None)
        oy1 = np.clip(py + hx - hi, 0, None)
        oy0 = np.clip(lo - py + hx, 0, None)
        out[:c] += wall_w * (2.0 * ox1 - 2.0 * ox0)
        out[c:2 * c] += wall_w * (2.0 * oy1 - 2.0 * oy0)
        out[2 * c:] += wall_w * (2.0 * (ox1 + ox0 + oy1 + oy0) * dhx)
        if calls is not None:
            calls["objective"] = calls.get("objective", 0) + 1
            calls["batches"] = calls.get("batches", 0) + 1
        return out

    z0 = np.concatenate([X[idx], Y[idx], T[idx]])
    return obj, jac, z0, comp, c


def solve_patch_w(X, Y, T, idx, lo, hi, wall_w, iters=120, eps=1e-9,
                  calls=None, jac_mode="batched"):
    """Relax one patch against every cell it touches, with wall weight `wall_w`.

    `wall_w = 0` is the **projection** stage: remove overlaps only, ignore the
    container.  `wall_w > 0` is the **squeeze** stage: pay for the box, and
    accept overlap as the price.  Alternating the two is the squeeze-and-project
    scheme of run 111, and it is what lets the pose move through illegal states
    instead of being blocked by a contact.

    Run 126: the objective is unchanged; only its *evaluation* is.  `jac_mode=
    "scipy"` restores the pre-126 behaviour (scipy's own finite differences) and
    exists so `--check-solver` can compare the two on the same patch.
    """
    from scipy.optimize import minimize
    idx = np.asarray(idx)
    c = len(idx)
    if c == 0:
        return X, Y, T
    obj, jac, z0, comp, c = patch_problem(X, Y, T, idx, lo, hi, wall_w, eps, calls)
    kw = {"jac": jac} if jac_mode == "batched" else {}
    res = minimize(obj, z0, method="L-BFGS-B",
                   options={"maxiter": iters, "ftol": 1e-17, "gtol": 1e-13}, **kw)
    if calls is not None:
        calls["nfev"] = calls.get("nfev", 0) + int(res.nfev)
        calls["nit"] = calls.get("nit", 0) + int(res.nit)
    ax, ay, at = X[comp].copy(), Y[comp].copy(), T[comp].copy()
    ax[:c], ay[:c], at[:c] = res.x[:c], res.x[c:2 * c], res.x[2 * c:]
    Xa, Ya, Ta = X.copy(), Y.copy(), T.copy()
    Xa[comp], Ya[comp], Ta[comp] = ax, ay, at
    return Xa, Ya, Ta


def relax(X, Y, T, L, sweeps=6, deadline=None, rng=None, size=3.0, step=1.5,
          verbose=False, wall_w=1e5, iters=120, stats=None):
    """Patch-coordinate relaxation inside a box of side L.  Returns the best pose.

    `stats`, when a dict is passed, is updated with **sweep-completion** counts
    (`sweeps_completed`, `sweeps_aborted`, `patches_solved`) so a run records
    whether its null came from a finished sweep or from a budget that cut one
    off -- the distinction run 125 could only infer from wall clock.
    """
    lo_x, hi_x, lo_y, hi_y = box_for(L, X, Y, T)
    best = None
    for s in range(sweeps):
        order = patches(X, Y, size=size, step=step)
        if rng is not None:
            rng.shuffle(order)
        cut = False
        for idx in order:
            if deadline is not None and time.monotonic() > deadline:
                cut = True
                break
            X, Y, T = solve_patch_w(X, Y, T, idx, lo_x, hi_x, wall_w, iters=iters)
            if stats is not None:
                stats["patches_solved"] = stats.get("patches_solved", 0) + 1
        if stats is not None:
            if cut:
                stats["sweeps_aborted"] = stats.get("sweeps_aborted", 0) + 1
            else:
                stats["sweeps_completed"] = stats.get("sweeps_completed", 0) + 1
        pen, pmax = total_pen(X, Y, T)
        # wall term is included in the patch objective; measure it here too
        h = 0.5 * (np.abs(np.cos(T)) + np.abs(np.sin(T)))
        over = float((np.clip(X + h - hi_x, 0, None) ** 2
                      + np.clip(lo_x - X + h, 0, None) ** 2
                      + np.clip(Y + h - hi_y, 0, None) ** 2
                      + np.clip(lo_y - Y + h, 0, None) ** 2).sum())
        score = pen + wall_w * over
        if best is None or score < best[0]:
            best = (score, X.copy(), Y.copy(), T.copy())
        if verbose:
            print(f"    sweep {s}: pen {pen:.3e} wall {over:.3e} score {score:.3e}",
                  flush=True)
        if deadline is not None and time.monotonic() > deadline:
            break
        if pen < 1e-20 and over < 1e-20:
            break
    return best[1], best[2], best[3]


def project(X, Y, T, L, deadline, rng, rounds=3, screen=False, stats=None,
            iters=400):
    """Remove overlaps at 40 digits: repeat the projection until it is legal.

    `screen=True` (the driver's mode) pays one projection round and then an
    exact O(n) side, with the O(n^2) pair pass only if the pose is not clearly
    illegal.  The verdict that matters is taken in `legalise`; this stage only
    produces the pose it starts from.
    """
    if screen:
        X, Y, T = relax(X, Y, T, L, sweeps=3, deadline=deadline, rng=rng,
                        wall_w=1e2, iters=iters, stats=stats)
        # No pair pass here: `legalise` takes the verdict on this same pose, and
        # doing it twice was the whole cost (85 s each on a 999-cell pose).
        return float(exact_side(X, Y, T)), None, X, Y, T
    best = None
    for _ in range(rounds):
        if time.monotonic() > deadline:
            break
        X, Y, T = relax(X, Y, T, L, sweeps=3, deadline=deadline, rng=rng,
                        wall_w=1e2, iters=iters, stats=stats)
        s40, viol, _ = side40(X, Y, T)
        if best is None or viol < best[0]:
            best = (viol, float(s40), X.copy(), Y.copy(), T.copy())
        if viol == 0:
            return float(s40), 0, X, Y, T
    if best is None:                      # deadline expired before any round
        s40, viol, _ = side40(X, Y, T)
        return float(s40), viol, X, Y, T
    return best[1], best[0], best[2], best[3], best[4]


def legalise(X, Y, T, tries=14, ceiling=None):
    """Expand about the centroid by the smallest factor that is legal at 40 digits.

    The relaxer works at 1e-9 penetration tolerance, so its output can be illegal
    by a hair.  Scaling the whole shape up by `1 + f` increases every separation
    monotonically, so a geometric ladder finds the smallest legal f.  This is a
    legalisation step, not a gain: the dL reported is always measured after it.

    Two bounds keep it affordable on ~1000-cell poses without weakening it:

      * `ceiling`: stop as soon as the exact side reaches it.  Monotone, so no
        later rung can be below it -- an exact early exit, not a truncation;
      * a rung whose penetration exceeds `SCREEN` is illegal by five orders more
        than rounding and is skipped without the O(n^2) pair pass.

    Returns (side, viol, X, Y, T, f, why) where `viol is None` means the pose was
    not certified legal (no pair count was computed), `f > 0` the factor that
    certified legality, `f < 0` the negative of the rung at which the exact side
    reached `ceiling` (the side at that rung is returned in the first slot), and
    `why` names the path so a null is never ambiguous.
    """
    h = 0.5 * (np.abs(np.cos(T)) + np.abs(np.sin(T)))
    cx = 0.5 * (float((X - h).min()) + float((X + h).max()))
    cy = 0.5 * (float((Y - h).min()) + float((Y + h).max()))
    s40 = exact_side(X, Y, T)
    if ceiling is not None and float(s40) >= ceiling:
        # Expansion only grows the side, so a pose already at or above the bar
        # cannot be a gain; no 40-digit pair pass is needed to say so.
        return s40, None, X, Y, T, None, "pose at or above the bar"
    if clearly_illegal(X, Y, T):
        viol = None
        why = "screened illegal (> 1e-6 penetration)"
    else:
        s40, viol, _chk = side40(X, Y, T)
        why = f"exact: {viol} violations"
        if viol == 0:
            return s40, 0, X, Y, T, 0.0, "legal where projected"
    for e in range(1, tries + 1):
        f = 10.0 ** (-13 + e) if e <= 9 else 10.0 ** (e - 12)
        Xa, Ya = cx + (X - cx) * (1 + f), cy + (Y - cy) * (1 + f)
        if clearly_illegal(Xa, Ya, T):
            continue
        s2 = exact_side(Xa, Ya, T)
        if ceiling is not None and float(s2) >= ceiling:
            return s2, viol, X, Y, T, -f, f"expansion reached the bar at f={f:g}"
        s2, v2, _ = side40(Xa, Ya, T)
        if v2 == 0:
            return s2, 0, Xa, Ya, T, f, f"legal at f={f:g}"
        why = f"exact: {v2} violations at f={f:g}"
    return s40, viol, X, Y, T, None, f"ladder exhausted ({why})"


def free_point(X, Y, T, rng, tries=400):
    """A random position whose centre keeps >= 1.02 clearance from every cell."""
    lo = 0.5 * (float((X - 0.5).min())) - 0.1
    hi = 0.5 * (float((X + 0.5).max())) + 0.1
    lo2 = 0.5 * (float((Y - 0.5).min())) - 0.1
    hi2 = 0.5 * (float((Y + 0.5).max())) + 0.1
    h = 0.5 * (np.abs(np.cos(T)) + np.abs(np.sin(T)))
    for _ in range(tries):
        cx = rng.uniform(lo, hi)
        cy = rng.uniform(lo2, hi2)
        # bounding-box (Chebyshev) clearance: two axis cells need 1.0, a 45
        # degree cell needs sqrt2, so the requirement is 1.0005 + 2h - 1
        d = np.maximum(np.abs(X - cx), np.abs(Y - cy))
        if np.all(d > 1.0005 + 2 * h - 1.0):
            return cx, cy
    return None


def attempt(n, kind, seconds, seed, iters=10, proj_iters=40, split=0.6,
            pose_out=None):
    """One structure-changing attempt at row n; returns a record.

    The budget is **split** between the squeeze and the projection
    (`split` x seconds for the squeeze, the rest for the projection).  Run 125
    handed the whole budget to `relax`, which keeps sweeping until its deadline,
    so the projection always ran with zero time left and every attempt was
    judged on a pose nobody had tried to legalise.  `iters`/`proj_iters` cap
    the L-BFGS iterations per patch visit: run 126 measured that at a fixed
    wall clock, fewer iterations per visit and more completed sweeps leave a
    *lower* residual penalty (n=662: 6.6e-3 at 2 sweeps vs 1.1e-2 at 1), so
    the cap is a throughput choice, not a relaxation of the objective.

    `pose_out`, when a list is passed, receives the relaxed pose the record
    judges -- the squeeze-and-project output before `legalise`, as decimal
    strings via `repr(float)`, which is the exact shortest form of the float64
    the relaxer produced.  Run 128 uses it to hand the projection stage's own
    output to the exact legal move set; the record itself is unchanged.
    """
    t0 = time.monotonic()
    deadline = t0 + seconds
    squeeze_deadline = t0 + split * seconds
    X, Y, T, L0 = load_pose(n)
    rng = random.Random(seed * 7919 + n + kind)
    nprng = np.random.RandomState(seed * 31 + n * 7 + kind)
    Xa, Ya, Ta = X.copy(), Y.copy(), T.copy()
    moved = "none"
    if kind == 1:
        i = rng.randrange(len(X))
        pts = free_point(Xa, Ya, Ta, rng)
        if pts:
            Xa[i], Ya[i] = pts
            moved = f"teleport cell {i} to a void"
        else:
            ang = rng.choice([(0.4, 0.0), (-0.4, 0.0), (0.0, 0.4), (0.0, -0.4)])
            Xa[i], Ya[i] = Xa[i] + ang[0], Ya[i] + ang[1]
            moved = f"displace cell {i} by {ang}"
    elif kind == 2:
        # rotate a 2x2 block about its centroid
        cx, cy = float(Xa.mean()), float(Ya.mean())
        near = np.argsort((np.abs(Xa - cx) + np.abs(Ya - cy)))[:4]
        mx, my = float(Xa[near].mean()), float(Ya[near].mean())
        dx, dy = Xa[near] - mx, Ya[near] - my
        Xa[near], Ya[near] = mx - dy, my + dx
        Ta[near] = Ta[near] + math.pi / 2
        moved = "rotate 2x2 block"
    want = float(L0) - TARGET
    squeeze_side = float(L0)
    post_side = float(L0)
    stats = {}
    outer_cut = False
    for _outer in range(4):
        if time.monotonic() > squeeze_deadline:
            outer_cut = True
            break
        Xa, Ya, Ta = relax(Xa, Ya, Ta, want, sweeps=2, deadline=squeeze_deadline,
                           rng=nprng, wall_w=1e5, iters=iters,
                           stats=stats)                        # squeeze
        squeeze_side = float(exact_side(Xa, Ya, Ta))
        # `project` in screen mode returns no verdict: `legalise` takes the one
        # that matters on this same pose, so it is not paid for twice.
        _, _, Xa, Ya, Ta = project(Xa, Ya, Ta, want, deadline, nprng,
                                   screen=True, stats=stats, iters=proj_iters)
        post_side = float(exact_side(Xa, Ya, Ta))
        if time.monotonic() > deadline:
            outer_cut = True
            break

    if pose_out is not None:
        pose_out.append([(repr(float(a)), repr(float(b)), repr(float(c)))
                         for a, b, c in zip(Xa, Ya, Ta)])

    # The ceiling is the delivered side: once an expansion reaches it, no rung
    # can be a gain (the ladder is monotone), so this is an exact early exit.
    post_pen = float(total_pen(Xa, Ya, Ta)[0])
    s40, viol, Xb, Yb, Tb, spill, why = legalise(Xa, Ya, Ta, ceiling=float(L0))
    dL = float(L0) - float(s40) if viol == 0 else 0.0
    crossed = spill is not None and spill < 0
    return {"n": n, "k": SQ.grid(n), "kind": kind, "moved": moved,
            "L0": str(L0), "side40": str(s40),
            "violations": viol, "certified_legal": viol == 0,
            "why": why,
            "dL": dL, "legal": viol == 0, "legalise": spill,
            "expansion_crossed": crossed,
            "squeeze_side": str(squeeze_side),
            "post_project_side": str(post_side),
            "squeeze_below_L0": squeeze_side < float(L0) - 1e-12,
            "sweeps_completed": stats.get("sweeps_completed", 0),
            "sweeps_aborted": stats.get("sweeps_aborted", 0),
            "patches_solved": stats.get("patches_solved", 0),
            "patches_total": sum(len(p) for p in patches(X, Y)),
            "post_project_pen": post_pen,
            "iters": iters, "proj_iters": proj_iters, "split": split,
            "budget_limited": bool(stats.get("sweeps_aborted", 0) > 0 or outer_cut),
            "seconds": round(time.monotonic() - t0, 2),
            "beat": bool(viol == 0 and dL > 1e-12)}


def control(seconds=12.0):
    """A: recovery from a known inflation.  B: absorb a changed arrangement."""
    print("control A -- recovery: inflate n=16 by 5e-3, hinge back at its side")
    X, Y, T, L0 = load_pose(16)
    h = 0.5 * (np.abs(np.cos(T)) + np.abs(np.sin(T)))
    xm = 0.5 * (float((X - h).min()) + float((X + h).max()))
    ym = 0.5 * (float((Y - h).min()) + float((Y + h).max()))
    k = 1.0 + 5e-3 / float(L0)
    Xi, Yi = xm + (X - xm) * k, ym + (Y - ym) * k
    si, vi, _ = side40(Xi, Yi, T)
    Xb, Yb, Tb = relax(Xi, Yi, T, float(L0), sweeps=4, iters=400,
                       deadline=time.monotonic() + seconds)
    s40, viol, Xb, Yb, Tb = project(Xb, Yb, Tb, float(L0),
                                    time.monotonic() + seconds, random.Random(4))
    s40, viol, Xb, Yb, Tb, _f, _why = legalise(Xb, Yb, Tb)
    print(f"  delivered {L0}  inflated {si}  relaxed to {s40}  violations {viol}")
    assert viol == 0, "control A: relaxer did not produce a legal pose"
    assert float(s40) < float(si), "control A: relaxer did not shrink the inflated pose"
    recovered = float(si) - float(s40)
    assert recovered > 1e-6, "control A: recovered less than 1e-6 of the injection"
    print(f"  recovered {recovered:.3e} of the {float(si) - float(L0):.3e} injected "
          f"({100 * recovered / (float(si) - float(L0)):.1f} %) -> mechanism fires")

    print("control B -- structural absorb: displace a cell by 0.3, then legalise")
    X, Y, T, L0 = load_pose(12)
    Xa, Ya = X.copy(), Y.copy()
    Xa[5] += 0.3
    s_pre, v_pre, _ = side40(Xa, Ya, T)
    s40, viol, Xb, Yb, Tb = project(Xa, Ya, T, float(L0) + 0.35,
                                    time.monotonic() + seconds, random.Random(5))
    s40, viol, Xb, Yb, Tb, _f, _why = legalise(Xb, Yb, Tb)
    print(f"  after displacement {s_pre} (viol {v_pre})  absorbed at {s40} "
          f"(viol {viol})")
    assert viol == 0, "control B: relaxer did not legalise a displaced arrangement"
    assert float(s40) < float(L0) + 0.35, "control B: no absorption at all"
    print("  -> a displaced cell is absorbed; the mechanism can change the arrangement")
    print("control: OK")


def check_solver(n=33, reps=3):
    """Positive control for run 126's acceleration.

    The change is *only* in how the objective's gradient is evaluated (one
    stacked forward-difference batch instead of 3c+1 separate calls), so the
    control is that the accelerated solve lands where the plain scipy
    finite-difference solve lands -- the pre-126 behaviour -- on the same real
    patches, with the same pair list and `eps`.  It also requires the run to be
    measurably faster, otherwise there is no reason to adopt it.
    """
    X, Y, T, L0 = load_pose(n)
    lo_x, hi_x, lo_y, hi_y = box_for(float(L0), X, Y, T)
    order = sorted(patches(X, Y), key=len, reverse=True)[:reps]

    def f(ax, ay, at):
        pen, _ = total_pen(ax, ay, at)
        hx = 0.5 * (np.abs(np.cos(at)) + np.abs(np.sin(at)))
        over = (np.clip(ax + hx - hi_x, 0, None) ** 2
                + np.clip(lo_x - ax + hx, 0, None) ** 2
                + np.clip(ay + hx - hi_y, 0, None) ** 2
                + np.clip(lo_y - ay + hx, 0, None) ** 2)
        return pen + 1e5 * float(over.sum())

    print(f"check-solver -- n={n}, {len(order)} largest patches")
    # Gradient first, and NOT only at the start pose: run 126's first batched
    # jacobian agreed with scipy at z0 to 1e-17 and was 1e7 wrong one step
    # away, because it perturbed the pose captured at build time instead of
    # the z it was handed.  A control that only samples z0 cannot see that.
    #
    # The delivered pose itself is excluded from the assertion on purpose: the
    # objective there is ~1e-17, i.e. roundoff, so a finite difference of it is
    # noise and cannot referee anything.  The generic points below are where a
    # gradient error would actually change the search.
    from scipy.optimize._numdiff import approx_derivative
    idx0 = order[0]
    _o, _j, z0g, _comp, _c = patch_problem(X, Y, T, idx0, lo_x, hi_x, 1e5)
    g_at0 = _j(z0g)
    print(f"  at the delivered pose f={_o(z0g):.2e} (degenerate): |g| "
          f"{np.max(np.abs(g_at0)):.2e} -- not asserted", flush=True)
    rng = np.random.RandomState(11)
    for trial, d in enumerate((1e-3, 1e-2, 5e-2)):
        z = z0g + rng.uniform(-d, d, len(z0g))
        gm, gr = _j(z), approx_derivative(_o, z, method="2-point")
        sc = max(1e-12, float(np.max(np.abs(gr))))
        err = float(np.max(np.abs(gm - gr))) / sc
        print(f"  gradient at f={_o(z):.3e} (|g|inf {sc:.3e}): max rel err "
              f"{err:.2e}", flush=True)
        assert err < 5e-5, "check-solver: analytic gradient disagrees with scipy"
    for idx in order:
        ca, cb = {}, {}
        t0 = time.monotonic()
        Xa, Ya, Ta = solve_patch_w(X, Y, T, idx, lo_x, hi_x, 1e5, calls=ca)
        t_new = time.monotonic() - t0
        t0 = time.monotonic()
        Xb, Yb, Tb = solve_patch_w(X, Y, T, idx, lo_x, hi_x, 1e5, calls=cb,
                                   jac_mode="scipy")
        t_ref = time.monotonic() - t0
        fa, fb = f(Xa, Ya, Ta), f(Xb, Yb, Tb)
        dpose = max(float(np.abs(Xa - Xb).max()), float(np.abs(Ya - Yb).max()),
                    float(np.abs(Ta - Tb).max()))
        print(f"  patch {len(idx):3d} cells  f_batched {fa:.6e}  f_scipy-FD "
              f"{fb:.6e}  |df| {abs(fa - fb):.2e}  dpose {dpose:.2e}  "
              f"batched {t_new * 1e3:.1f} ms vs {t_ref * 1e3:.1f} ms "
              f"({t_ref / t_new:.1f}x), objective calls {ca.get('objective', 0)} "
              f"in {ca.get('batches', 0)} batches vs nfev {cb.get('nfev', 0)}",
              flush=True)
        assert fa <= fb + 1e-12 * max(1.0, abs(fb)), \
            "check-solver: batched solve ended worse than the scipy-FD solve"
        assert abs(fa - fb) <= 1e-6 * max(1.0, abs(fb)), \
            "check-solver: the two solves did not reach the same objective"
        assert t_new < t_ref, "check-solver: the batched gradient was not faster"
    print("check-solver: OK -- same objective, faster evaluation")


def main(argv):
    opts = dict(zip(argv[0::2], argv[1::2]))
    rows = int(opts.get("--rows", 20))
    seconds = float(opts.get("--seconds", 10))
    seed = int(opts.get("--seed", 3))
    iters = int(opts.get("--iters", 10))
    proj_iters = int(opts.get("--proj-iters", 40))
    split = float(opts.get("--split", 0.6))
    out = opts.get("--out", OUT)
    per = SQ.load()
    unbeaten = [n for n in range(1, 1001)
                if SQ.extent(per[n]) >= SQ.grid(n) - 1e-12]
    step = len(unbeaten) / rows
    pick = sorted({unbeaten[min(len(unbeaten) - 1, int(round(i * step)))]
                   for i in range(rows)})
    print(f"unbeaten {len(unbeaten)}; testing {len(pick)} evenly spaced")
    recs = []
    for n in pick:
        best = None
        for kind in (0, 1, 2):
            r = attempt(n, kind, seconds, seed, iters=iters,
                        proj_iters=proj_iters, split=split)
            better = (best is None
                      or (r["legal"] and not best["legal"])
                      or (r["legal"] == best["legal"] and r["dL"] > best["dL"]))
            best = r if better else best
        best["budget_seconds"] = seconds * 3
        recs.append(best)
        print(f"  n={n:4d} k={best['k']:2d} L0={best['L0'][:20]:20s} "
              f"side40={best['side40'][:20]:20s} dL={best['dL']:+.3e} "
              f"viol {best['violations']} sweeps {best['sweeps_completed']}"
              f"/{best['sweeps_aborted']} patches {best['patches_solved']}"
              f"/{best['patches_total']} pen@proj {best['post_project_pen']:.1e}"
              f" [{best['why']}] ({best['moved']}) {best['seconds']}s",
              flush=True)
    ds = sorted(r["dL"] for r in recs)
    pos = [d for d in ds if d > 1e-12]
    print(f"\ndL over {len(ds)} rows: min {ds[0]:.3e} median "
          f"{ds[len(ds) // 2]:.3e} max {ds[-1]:.3e}")
    print(f"  rows with any gain: {len(pos)}/{len(ds)}")
    print(f"  rows legal and improving: {len([r for r in recs if r['beat']])}")
    print(f"  rows reaching the 4e-3 target: {len([r for r in ds if r >= TARGET])}")
    done = [r for r in recs if r["sweeps_completed"] > 0]
    print(f"  rows with at least one COMPLETED sweep: {len(done)}/{len(recs)}"
          f"   (budget-limited: {len([r for r in recs if r['budget_limited']])})")
    below = [r for r in recs if r["squeeze_below_L0"]]
    print(f"  rows whose squeeze got BELOW L0: {len(below)}/{len(recs)}"
          + (f"   min gain in the illegal pose "
             f"{max(float(r['L0']) - float(r['squeeze_side']) for r in below):+.3e}"
             if below else ""))
    if below:
        paid = sorted(float(r["L0"]) - float(r["side40"]) for r in below)
        print(f"  after legalising the below-L0 poses: dL min {paid[0]:+.3e} "
              f"max {paid[-1]:+.3e}  (negative = legalisation paid back more)")
    json.dump(recs, open(out, "w"), indent=1)
    print(f"wrote {out}")


if __name__ == "__main__":
    if "--control" in sys.argv:
        control()
    elif "--check-solver" in sys.argv:
        check_solver()
    else:
        main(sys.argv[1:])
