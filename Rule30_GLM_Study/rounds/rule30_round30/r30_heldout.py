"""Round 30 fresh held-out families, scored once by ``pipeline_bench.py --only D``.

Written after stages 1 and 3 of the pipeline were frozen (sha256 a809d08c...).  Afterwards, and
before any held-out result was seen, the ask policy of stage 2 was revised because of a unit test
(``test_round30.py``: ask before skipping an undetermined tier); the scored version is sha256
031c6eb5ee2464dfa57462a26d7edd233ecfe23f036c008af5aad4635edd521f.

Eleven families, 12 instances each (3 demonstrations, 1 query), seeds 300000+.  Nine are
expressible by the Round 30 pipeline at plan depth <= 2, and several need a stage 1 addition
(a fitted reader followed by a symmetry, a scale factor read from the grid, line drawing,
per-object moves, positional / unique-colour crops).  Two are CONTROLS that no plan in the
alphabet expresses (the right result for a control is REFUSED).

NOTE: the families were chosen knowing the pipeline's new step kinds, so this set measures whether
the new kinds work on unseen instances and compositions; it is not an unbiased sample of
puzzles.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.join(HERE, "glm_overlay", "glm_universal", "reasoning"),
          os.path.join(HERE, "..", "rule30_round29", "glm_overlay", "glm_universal", "reasoning"),
          os.path.join(HERE, "..", "rule30_round28", "glm_overlay", "glm_universal", "reasoning"),
          os.path.join(HERE, "..", "rule30_round29")):
    if p not in sys.path:
        sys.path.insert(0, p)
import glm_pipeline as P  # noqa: E402
import grid_planner as gp  # noqa: E402
from r29_benchmark import L, sparse  # noqa: E402


def blobs(g, cols=(1, 2, 3, 4), n_lo=2, n_hi=3, size_lo=1, size_hi=3, H0=9, W0=9):
    """A few separated rectangular single-colour blobs (8-separated) on background 0."""
    H, W = H0 + g.next(3), W0 + g.next(3)
    a = [[0] * W for _ in range(H)]
    n = n_lo + g.next(n_hi - n_lo + 1)
    placed = 0
    for _ in range(40):
        if placed == n:
            break
        h, w = size_lo + g.next(size_hi - size_lo + 1), size_lo + g.next(size_hi - size_lo + 1)
        r0, c0 = g.next(H - h), g.next(W - w)
        if any(a[r][c] for r in range(max(0, r0 - 1), min(H, r0 + h + 1))
               for c in range(max(0, c0 - 1), min(W, c0 + w + 1))):
            continue
        col = cols[g.next(len(cols))]
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                a[r][c] = col
        placed += 1
    return a


def lines_input(g):
    """Pairs of same-coloured cells in rows, background between them, plus noise cells."""
    H, W = 7 + g.next(3), 8 + g.next(3)
    a = [[0] * W for _ in range(H)]
    for r in range(H):
        if g.next(100) < 45:
            c1 = g.next(W - 3)
            c2 = c1 + 2 + g.next(W - c1 - 2)
            col = 1 + g.next(3)
            a[r][c1] = a[r][c2] = col
    return a


def small_cols(g, cols=(0, 1, 2, 3)):
    h, w = 3 + g.next(3), 3 + g.next(3)
    return [[cols[g.next(len(cols))] for _ in range(w)] for _ in range(h)]


def recol(m):
    return lambda a: [[m.get(v, v) for v in r] for r in a]


def comp(*fs):
    def f(a):
        for h in fs:
            a = h(gp.G(a))
            if a is None:
                return None
            a = L(a)
        return a
    return f


def obj_size_recolour(a):
    """Objects (4-connected, one colour) of size >= 4 become colour 5."""
    out = [list(r) for r in a]
    for cp in gp.components(gp.G(a), 0, diag=False, by_colour=True):
        if len(cp) >= 4:
            for r, c in cp:
                out[r][c] = 5
    return out


def scale_by_objects(a):
    k = len(gp.components(gp.G(a), 0, diag=True))
    if k < 2 or k * len(a) > 30 or k * len(a[0]) > 30:
        return None
    return L(gp.s_upscale(k)(gp.G(a)))


def small_blobs(g):
    return blobs(g, n_lo=2, n_hi=3, size_lo=1, size_hi=2, H0=3, W0=3)


def unique_colour_scene(g):
    """Two or three objects of colour 1 and one object of another colour."""
    a = blobs(g, cols=(1,), n_lo=2, n_hi=3, size_lo=1, size_hi=3)
    H, W = len(a), len(a[0])
    for _ in range(40):
        h, w = 2 + g.next(2), 2 + g.next(2)
        r0, c0 = g.next(H - h), g.next(W - w)
        if any(a[r][c] for r in range(max(0, r0 - 1), min(H, r0 + h + 1))
               for c in range(max(0, c0 - 1), min(W, c0 + w + 1))):
            continue
        col = 2 + g.next(3)
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if g.next(100) < 80 or (r, c) == (r0, c0):
                    a[r][c] = col
        break
    return a


def reverse_nonzero_rows(a):  # CONTROL
    out = []
    for r in a:
        nz = [v for v in r if v]
        it = iter(reversed(nz))
        out.append([next(it) if v else 0 for v in r])
    return out


def diagonal_rays(a):  # CONTROL
    H, W = len(a), len(a[0])
    out = [list(r) for r in a]
    for r in range(H):
        for c in range(W):
            if a[r][c]:
                k = 1
                while r + k < H and c + k < W and out[r + k][c + k] == 0:
                    out[r + k][c + k] = a[r][c]
                    k += 1
    return out


S = P.STEP_FN
HELDOUT30 = [
    ("objsize-recolour-rot90", lambda g: blobs(g, cols=(1, 3), size_hi=3),
     comp(obj_size_recolour, gp.rot90), True),
    ("recolour-transpose", lambda g: small_cols(g, (0, 1, 2, 3)),
     comp(recol({1: 4, 2: 6, 3: 1}), gp.transpose), True),
    ("scale-by-objects", small_blobs, scale_by_objects, True),
    ("flip-scale-by-objects", small_blobs, comp(gp.flip_h, scale_by_objects), True),
    ("connect-rot180", lines_input, comp(S["connect_h"], S["rot180"]), True),
    ("objects-fall", lambda g: blobs(g, cols=(2, 6, 7), n_lo=2, n_hi=4),
     comp(S["obj_fall_down"]), True),
    ("fall-left-crop", lambda g: blobs(g, cols=(4, 8), n_lo=2, n_hi=3),
     comp(S["obj_fall_left"], S["crop_bbox"]), True),
    ("unique-colour-mirror", unique_colour_scene,
     comp(S["crop_unique_colour"], S["mirror_h"]), True),
    ("topmost-upscale", lambda g: blobs(g, cols=(3, 5, 9), n_lo=2, n_hi=3, size_hi=3),
     comp(S["crop_topmost"], S["up2"]), True),
    ("CONTROL-reverse-row-colours", lambda g: sparse(g, (1, 2, 3, 4), 40),
     reverse_nonzero_rows, False),
    ("CONTROL-diagonal-rays", lambda g: blobs(g, cols=(2, 3), n_lo=2, n_hi=3, size_lo=1,
                                              size_hi=1), diagonal_rays, False),
]
