#!/usr/bin/env python3
r"""ext_census.py — run 131: certify the pocket-net rows, and diagnose the stored poses.

Two jobs, both exact where they can be.

**1. Certify the 11.**  Run 130 built the four-corner pocket net and compared its
algebraic side `2a + sqrt2/2` against the extension table, finding it smaller on
11 rows above 1000.  A comparison is not a certificate, so this module *gates*
each pose: containment against the exact side, and every pair that could
possibly overlap, exactly, in `Q(sqrt 2)`.  The pair pruning is sound, not a
sample: two unit squares overlap only if `|dx| < sqrt2` and `|dy| < sqrt2`
(the largest half-extent of either orientation is `sqrt2/2`), and both tests are
exact, so the pair list is complete.

The result is written to `json/extended_table_5000_certified.json` -- the run-41
measurement with the certified sides applied and labelled, **never** to
`json/extended_table_5000.json` itself, which stays the historical record.
`submission.csv` is not touched: every row here has `n > 1000`.

**2. Diagnose the 33 stored poses.**  The extension's void price is `-22` to
`-28` at `k = 33..36`, which says its frontier poses spend about a third of the
band's void budget.  Those poses are stored, so the deficit can be inspected
rather than guessed: this module reports, per pose, the orientation census, the
`Q(sqrt 2)` snap residual (are the cells on an exact contact lattice?), the void
`V = L^2 - n` against the box capacity `floor(L)^2`, and -- for the poses above
2000 cells -- whether a free axis-aligned unit cell exists anywhere in them
(a float probe used for *discovery* only; a hit would need an exact rebuild
before it could be a certificate).

    python3 scripts/ext_census.py --selftest
    python3 scripts/ext_census.py
"""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal, getcontext
from fractions import Fraction
from math import isqrt

getcontext().prec = 45

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import seam_wheels as SW                 # noqa: E402
import construct_seam as CS              # noqa: E402

Q2 = SW.Q2
R2H = SW.R2H
HALF = SW.HALF
EXT_SRC = os.path.join(ROOT, "json/extended_table_5000.json")
EXT_OUT = os.path.join(ROOT, "json/extended_table_5000_certified.json")
REC = os.path.join(ROOT, "workspace/push/ext_census131.json")
PAD = Decimal("2e-9")
SQ2 = Decimal(2).sqrt()


def k_of(n: int) -> int:
    k = isqrt(n)
    return k if k * k == n else k + 1


def load_ext(path=EXT_SRC) -> dict:
    """Sides as strings, so every comparison is Decimal and exact."""
    with open(path) as f:
        return json.load(f, parse_float=str)


def load_ext_float(path=EXT_SRC) -> dict:
    """The same rows with real floats, for the pose diagnosis only."""
    with open(path) as f:
        return json.load(f)


# ------------------------------------------------------------------ exact gate
def gate_pose(cells: list, L: Q2) -> dict:
    """Complete exact gate: containment, then every pair that can overlap.

    `cells` = [(x: Q2, y: Q2, orient)].  The prune `|dx|^2 < 2 and |dy|^2 < 2`
    is sound because both orientations have half-extents <= sqrt2/2 in every
    axis, so a pair outside it cannot overlap at any angle.  The surviving
    pairs are tested with the exact separating-axis penetration.
    """
    two = Q2(2)
    worst = Q2(0)
    worst_pair = None
    violations = 0
    for i, (x, y, o) in enumerate(cells):
        ex, ey = SW.EXT[o]["x"], SW.EXT[o]["y"]
        if x - ex < Q2(0) or y - ey < Q2(0) or x + ex > L or y + ey > L:
            violations += 1
    order = sorted(range(len(cells)), key=lambda i: float(cells[i][0]))
    for ii in range(len(order)):
        i = order[ii]
        xi, yi, oi = cells[i]
        for jj in range(ii + 1, len(order)):
            j = order[jj]
            xj, yj, oj = cells[j]
            dx = xi - xj
            if float(dx) < -2.0001:
                break                                 # sorted by x: j is too far
            dy = yi - yj
            if float(dy) > 2.0001 or float(dy) < -2.0001:
                continue
            if dx * dx >= two or dy * dy >= two:          # exact prune
                continue
            pen = SW.pen_exact(oi, oj, dx, dy)
            if pen > Q2(0):
                violations += 1
                if pen > worst:
                    worst, worst_pair = pen, (i, j)
    return {"ok": violations == 0, "violations": violations,
            "worst_pen": str(CS.to_dec(worst)), "pair": worst_pair,
            "side": str(CS.to_dec(L))}


def pocket_rows(amax: int = 35) -> list:
    """Build, exact-gate and compare every `n = 4a^2+1` pocket pose."""
    ext = load_ext()
    out = []
    for a in range(1, amax + 1):
        n, cells, L = CS.windmill(a)
        if str(n) not in ext:
            continue
        gate = gate_pose(cells, L)
        got = Decimal(ext[str(n)]["L"])
        want = CS.to_dec(L)
        verdict = ("table_padded" if abs(got - want) <= PAD
                   else ("pocket_better" if got > want else "table_better"))
        out.append({"a": a, "n": n, "k": k_of(n),
                    "L_exact": str(want.quantize(Decimal("1e-15"))),
                    "L_table": str(got.quantize(Decimal("1e-15"))),
                    "gain": str((got - want).quantize(Decimal("1e-9"))),
                    "gate": gate, "verdict": verdict,
                    "table_status": ("tie" if abs(got - k_of(n)) < 1e-12
                                     else "beaten")})
    return out


def apply_certified(rows: list) -> dict:
    """Write the certified *patch* for the extension table.

    Deliberately a patch and not a rewrite: `json/extended_table_5000.json` is
    the run-41 measurement and stays byte-identical, so every doc that quotes it
    still reproduces.  A reader applies `L_after` where it is smaller, and the
    gate that licenses it travels with the row.
    """
    ext = load_ext()
    changed = []
    for r in rows:
        if r["verdict"] != "pocket_better" or not r["gate"]["ok"]:
            continue
        key = str(r["n"])
        old = Decimal(ext[key]["L"])
        changed.append({
            "n": r["n"], "k": r["k"], "a": r["a"],
            "L_before": str(old), "L_after": r["L_exact"],
            "src_before": ext[key]["src"], "src_after": f"pocket-net:a={r['a']}",
            "gain": r["gain"], "gate": r["gate"],
            "status_before": r["table_status"],
            "status_after": ("beaten" if Decimal(r["L_exact"]) < r["k"] else "tie")})
    patch = {"applies_to": "json/extended_table_5000.json",
             "rule": "where L_after < L_before, L_after is the certified side",
             "certified_by": "scripts/ext_census.py (run 131, exact Q(sqrt2) gate)",
             "rows_changed": len(changed), "changed": changed}
    with open(EXT_OUT, "w") as f:
        json.dump(patch, f, indent=1)
    return {"file": os.path.relpath(EXT_OUT, ROOT), "changed": changed}


# --------------------------------------------------------------- the diagnosis
def snap_q2(v: float, qmax: int = 90) -> tuple:
    """Nearest `(p + q*sqrt2)/2` with p, q integers; returns (Q2, residual)."""
    best = None
    for q in range(-qmax, qmax + 1):
        p = round(2.0 * v - q * float(SQ2))
        r = abs(v - (p + q * float(SQ2)) / 2.0)
        if best is None or r < best[1]:
            best = (Q2(Fraction(p, 2)) + Q2(Fraction(q, 2)) * Q2(2) * R2H, r)
    return best


def lattice_residual(state: list, qmax: int = 90, sample: int = 60) -> dict:
    """Worst snap residual of a sample of coordinates onto the Q(sqrt2) lattice."""
    idx = [i for i in range(len(state)) if i % max(1, len(state) // sample) == 0][:sample]
    worst = 0.0
    for i in idx:
        for v in (state[i][0], state[i][1]):
            _, r = snap_q2(v, qmax)
            worst = max(worst, r)
    return {"sampled": len(idx), "worst_residual": worst}


def occupancy(state: list, L: float, step: float = 0.5, chunk: int = 256) -> dict:
    """Float probe: the largest free square of each orientation in the pose.

    For a centre `c` and orientation `o` the largest square that fits there is

        s_o(c) = min over cells and axes of (|(c-p).q| - e_cell(q)) / e_o(q)

    (the separating-axis form; `e_o(q)` is the candidate's half-extent along
    axis `q` for unit side).  `s_0` is the largest upright square, `s_45` the
    largest at 45 degrees, and `max over c` of each is the pose's free square --
    the same quantity doc 75 §3 reports for the scored frontiers (0.9995 for a
    compressed lattice, 0.7171 for the `k = 32` notch).  `>= 1` means a cell of
    that orientation fits (in float arithmetic; the exact rebuild is a separate
    step and is not claimed here).  Discovery only.
    """
    import numpy as np
    a = np.asarray(state, dtype=float)[:, :3]
    cos, sin = np.cos(a[:, 2]), np.sin(a[:, 2])
    axes = np.array([[1.0, 0.0], [0.0, 1.0],
                     [1 / 2 ** 0.5, 1 / 2 ** 0.5],
                     [1 / 2 ** 0.5, -1 / 2 ** 0.5]])       # (4, 2)
    e_cell = 0.5 * (np.abs(cos)[None, :] * np.abs(axes[:, 0])[:, None]
                    + np.abs(sin)[None, :] * np.abs(axes[:, 1])[:, None])
    e_o = {0: 0.5 * (np.abs(axes[:, 0]) + np.abs(axes[:, 1])),
           1: 0.5 * (np.abs(axes[:, 0]) + np.abs(axes[:, 1])) / 2 ** 0.5}

    grid = np.arange(0.5, L - 0.5 + 1e-12, step)
    gx, gy = np.meshgrid(grid, grid, indexing="ij")
    pts = np.stack([gx.ravel(), gy.ravel()], axis=1)
    best = {0: (-9.9, None), 1: (-9.9, None)}
    for s0 in range(0, len(pts), chunk):
        blk = pts[s0:s0 + chunk]
        dx = blk[:, 0][:, None] - a[:, 0][None, :]
        dy = blk[:, 1][:, None] - a[:, 1][None, :]
        proj = np.abs(dx[:, None, :] * axes[None, :, 0, None]
                      + dy[:, None, :] * axes[None, :, 1, None])   # (m,4,n)
        sep = proj - e_cell[None, :, :]                            # (m,4,n)
        for o in (0, 1):
            s = (sep / e_o[o][None, :, None]).min(axis=2).min(axis=1)
            k = int(s.argmax())
            if float(s[k]) > best[o][0]:
                best[o] = (float(s[k]), [round(float(blk[k, 0]), 3),
                                         round(float(blk[k, 1]), 3)])
    return {"largest_upright": round(best[0][0], 6), "at_upright": best[0][1],
            "largest_45": round(best[1][0], 6), "at_45": best[1][1],
            "step": step}


def contact_census(state: list) -> dict:
    """Is the pose jammed (exact contacts everywhere) or loose (gaps to squeeze)?

    For every pair of cells whose centres are within `sqrt2 + sqrt2` (the only
    pairs that can touch at either orientation) this reports the separating-axis
    slack: `< 0` overlap, `= 0` exact contact, `> 0` gap.  A pose whose contacts
    are all exactly zero has no seam to repair; a pose with a *floor* of small
    positive gaps is uniformly loose and can be squeezed.  Float arithmetic,
    labelled as discovery: the exact gate is `gate_pose`, and it is used on
    every pose this run certifies.
    """
    import numpy as np
    a = np.asarray(state, dtype=float)[:, :3]
    n = len(a)
    cos, sin = np.cos(a[:, 2]), np.sin(a[:, 2])
    axes = np.array([[1.0, 0.0], [0.0, 1.0],
                     [1 / 2 ** 0.5, 1 / 2 ** 0.5],
                     [1 / 2 ** 0.5, -1 / 2 ** 0.5]])
    e = 0.5 * (np.abs(cos)[None, :] * np.abs(axes[:, 0])[:, None]
               + np.abs(sin)[None, :] * np.abs(axes[:, 1])[:, None])   # (4,n)
    dx = a[:, 0][:, None] - a[:, 0][None, :]
    dy = a[:, 1][:, None] - a[:, 1][None, :]
    near = (np.abs(dx) < 2.001) & (np.abs(dy) < 2.001)
    np.fill_diagonal(near, False)
    slack = np.full(dx.shape, 9.9)
    for k in range(4):
        proj = np.abs(dx * axes[k, 0] + dy * axes[k, 1])
        slack = np.minimum(slack, proj - e[k][:, None] - e[k][None, :])
    vals = slack[near]
    neg = vals[vals < -1e-6]
    contact = vals[np.abs(vals) <= 1e-6]
    gaps = vals[vals > 1e-6]
    return {"pairs": int(near.sum() // 2), "violations": int(neg.size),
            "worst_overlap": round(float(neg.min()), 9) if neg.size else 0.0,
            "contacts": int(contact.size // 2),
            "contact_share": round(float(contact.size) / max(1, vals.size), 4),
            "gap_min": round(float(gaps.min()), 6) if gaps.size else None,
            "gap_median": round(float(np.median(gaps)), 6) if gaps.size else None,
            "gap_max": round(float(gaps.max()), 6) if gaps.size else None}


def diagnose(nmax_extra: bool = True) -> list:
    ext = load_ext_float()
    out = []
    for key, rec in ext.items():
        st = rec.get("state")
        if not st:
            continue
        n = int(key)
        L = float(rec["L"])
        ang = sorted({round(c[2], 6) for c in st})
        tilted = sum(1 for c in st if abs(c[2]) > 1e-9)
        row = {"n": n, "cells": len(st), "L": L, "grid": k_of(n),
               "src": rec["src"], "tilted": tilted,
               "tilted_share": round(tilted / len(st), 4),
               "angle_classes": ang[:6], "angle_classes_count": len(ang),
               "void": round(L * L - n, 4),
               "k_floor": int(L),
               "capacity": int(L) * int(L),
               "beyond_grid": n - int(L) * int(L),
               "side_over_grid": round(L - int(L), 4),
               "lattice": lattice_residual(st)}
        row["contacts"] = contact_census(st)
        if nmax_extra and n > 2000:
            row["occupancy"] = occupancy(st, L)
        out.append(row)
    return out


# --------------------------------------------------------------------- controls
def selftest() -> int:
    """Four controls: the gate, its refusal, the pad, and the diagnosis's scale."""
    # 1. the windmill is legal and its gate is exactly zero
    n, cells, L = CS.windmill(1)
    g = gate_pose(cells, L)
    assert g["ok"] and g["violations"] == 0, g
    print(f"  windmill(1): gate ok, worst penetration {g['worst_pen']}")

    # 2. an overlapped copy must be refused with an exact penetration
    bad = cells + [(Q2(Fraction(1, 2)), Q2(Fraction(1, 2)), 0)]
    gb = gate_pose(bad, L)
    assert not gb["ok"] and gb["violations"] > 0, gb
    assert abs(Decimal(gb["worst_pen"]) - Decimal(1)) < Decimal("1e-12"), gb
    print(f"  refusal: duplicate cell -> violations {gb['violations']}, "
          f"exact worst penetration {gb['worst_pen']}")

    # 3. the pocket pose reproduces the *scored* row 5 to the pad, and the
    #    extension rows the run certifies are all above 1000
    with open(os.path.join(ROOT, "workspace/submission/table.json")) as f:
        scored = json.load(f)
    got = Decimal(scored["5"]["L"])
    want = CS.to_dec(L)
    assert abs(got - want) <= PAD, (got, want)
    rows = pocket_rows(35)
    cert = [r for r in rows if r["verdict"] == "pocket_better"]
    assert cert and all(r["n"] > 1000 for r in cert), cert
    print(f"  n=5 vs scored table: diff {got - want:+.1e} (pad), gate ok; "
          f"{len(cert)} certified extension rows, all n > 1000")

    # 4. the diagnosis recovers the stored pose's own numbers
    d = diagnose(nmax_extra=False)
    assert len(d) == 33, len(d)
    big = [r for r in d if r["n"] > 2000]
    assert big and all(r["tilted"] > 0 for r in big)
    print(f"  diagnosis: {len(d)} stored poses, {len(big)} above 2000, "
          f"tilted share {big[0]['tilted_share']:.2f} at n={big[0]['n']}")
    print("  selftest OK")
    return 0


# ------------------------------------------------------------------------ main
def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()

    rows = pocket_rows(35)
    cert = [r for r in rows if r["verdict"] == "pocket_better"]
    app = apply_certified(rows)
    print(f"[pocket] {len(rows)} rows n=4a^2+1<=5000 gated exactly; "
          f"{len(cert)} certified better than the table")
    for r in cert:
        print(f"  n={r['n']:5d} a={r['a']:2d} L {r['L_table'][:18]} -> "
              f"{r['L_exact'][:18]} (gain {r['gain']}) gate "
              f"{'OK' if r['gate']['ok'] else 'FAIL'} was {r['table_status']}")
    print(f"[table] wrote {app['file']}: {len(app['changed'])} rows changed")
    for c in app["changed"]:
        print(f"  n={c['n']:5d} {c['status_before']} -> {c['status_after']}")

    diag = diagnose()
    print(f"\n[diagnosis] {len(diag)} stored poses")
    print(f"  {'n':>5} {'L':>9} {'k':>3} {'tilted':>9} {'+grid':>6} "
          f"{'void':>7} {'contacts':>9} {'gap med':>8} {'gap max':>8} "
          f"{'free 0':>8} {'free 45':>8}")
    for r in diag:
        occ = r.get("occupancy")
        c = r["contacts"]
        f0 = "-" if not occ else f"{occ['largest_upright']:.4f}"
        f45 = "-" if not occ else f"{occ['largest_45']:.4f}"
        gm = "-" if c["gap_median"] is None else f"{c['gap_median']:.4f}"
        gx = "-" if c["gap_max"] is None else f"{c['gap_max']:.4f}"
        print(f"  {r['n']:5d} {r['L']:9.4f} {r['k_floor']:3d} "
              f"{r['tilted']:4d}/{r['cells']:<4d} {r['beyond_grid']:6d} "
              f"{r['void']:7.3f} {c['contacts']:9d} {gm:>8} {gx:>8} "
              f"{f0:>8} {f45:>8}")

    os.makedirs(os.path.dirname(REC), exist_ok=True)
    with open(REC, "w") as f:
        json.dump({"pocket_rows": rows, "applied": app, "diagnosis": diag},
                  f, indent=1, default=str)
    print(f"\nwrote {REC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
