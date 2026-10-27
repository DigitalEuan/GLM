"""``glm_universal.reasoning.grid_planner`` -- the stepwise planner for grid puzzles.

Round 29 of the Rule 30 study.  Round 28 gave the GLM a *one-step* puzzle solver (the
local-rule ladder, ``local_rule_induction.py``).  A single step rarely solves a puzzle: a typical
ARC task is *crop the object, then mirror it, then recolour it*.  This module is the GLM's own
planning discipline, lifted from text questions to grids:

* the **stepwise planner** (``runtime/stepwise.py``): a chain is licensed when every step is, and
  the answer is given only when every licensed reading agrees;
* the **search loop** of the archive (``reasoning/search_loop.py``; ``SearchLoop.lean``):
  the hard gate (D1: keep a candidate only if it reproduces every demonstration exactly) and
  Occam (C5: among the survivors, the cheapest description);
* **breadth-first state-space search with merging** (a standard planning method): partial plans
  that leave every probe grid in the same state are merged, so the search runs over *states*,
  not over the ``|A|^n`` plans.

What is proved (Lean, ``RequestProject/GLM/Rule30/PlanSearch.lean``, namespace
``GLM.PlanSearch``) and what this code does to respect it:

==========================================  ===============================================
Lean statement                              implementation
==========================================  ===============================================
``run_append``                              a plan is applied step by step (``run``)
``sig_append_congr``, ``consistent_congr``  plans are merged on their states on the
                                            demonstration inputs **and the queries**
``train_only_signature_unsound``            ... merging on demonstrations alone is unsound,
                                            so the queries are always probes
``layer_complete``, ``agree_iff_layer``     breadth-first layers with merging lose no plan
``planner_minimal``                         the first cost tier with a consistent
                                            hypothesis is used
``planner_agree_all``, ``agree_correct``    answer only if every consistent hypothesis of
                                            that tier gives the same grid; else refuse
``separating_example_refutes``              ... and name the query cell to ask about
``minAgree_correct``                        cost tiers = (plan length, finisher rank,
                                            Occam weight of the steps), lexicographic
``reproduces_iff_keyOK`` (Round 28)         finishers are fitted tables over a reader
``answer_determined_iff_covered``           a fitted table answers only on seen keys
==========================================  ===============================================

A hypothesis is a plan of fixed grid steps (geometry, cropping, scaling, tiling, splitting,
gravity, symmetry completion, ...) followed by a *finisher* fitted from the data: the identity,
a colour map, or a local rule over one of the Round 28 readers or the new object-level readers
(To Do 21).  Exact, deterministic, no randomness; test outputs are never read.
"""
from __future__ import annotations

import time
from collections import Counter
from typing import Callable, Dict, Hashable, List, Optional, Sequence, Tuple

try:  # inside the GLM
    from . import local_rule_induction as lri
except ImportError:  # stand-alone (study folder)
    import local_rule_induction as lri  # type: ignore

Grid = Tuple[Tuple[int, ...], ...]
Step = Callable[[Grid], Optional[Grid]]
MAXDIM = 30
SENTINEL = 10  # a colour no ARC grid uses: marks cells a step singled out (a finisher renames it)

# ---------------------------------------------------------------------------------------------
# grid utilities
# ---------------------------------------------------------------------------------------------


def G(g) -> Grid:
    return tuple(tuple(r) for r in g)


def ok(g) -> Optional[Grid]:
    if not g or not g[0] or len(g) > MAXDIM or len(g[0]) > MAXDIM:
        return None
    return G(g)


def shape(g: Grid) -> Tuple[int, int]:
    return len(g), len(g[0])


def bg_of(g: Grid) -> int:
    c = Counter(v for r in g for v in r)
    return max(sorted(c), key=lambda k: c[k])


def transpose(g: Grid) -> Grid:
    return tuple(zip(*g))


def flip_h(g: Grid) -> Grid:
    return tuple(tuple(reversed(r)) for r in g)


def flip_v(g: Grid) -> Grid:
    return tuple(reversed(g))


def rot90(g: Grid) -> Grid:  # clockwise
    return flip_h(transpose(g))


def components(g: Grid, bg: int, diag: bool = True, by_colour: bool = False):
    """Connected components of non-background cells: lists of (r, c)."""
    h, w = shape(g)
    seen = [[False] * w for _ in range(h)]
    out = []
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diag:
        nb += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for r in range(h):
        for c in range(w):
            if seen[r][c] or g[r][c] == bg:
                continue
            col = g[r][c]
            stack, comp = [(r, c)], []
            seen[r][c] = True
            while stack:
                y, x = stack.pop()
                comp.append((y, x))
                for dy, dx in nb:
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w and not seen[yy][xx] and g[yy][xx] != bg \
                            and (not by_colour or g[yy][xx] == col):
                        seen[yy][xx] = True
                        stack.append((yy, xx))
            out.append(sorted(comp))
    return out


def crop_cells(g: Grid, cells) -> Optional[Grid]:
    if not cells:
        return None
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return ok([row[c0:c1 + 1] for row in g[r0:r1 + 1]])


# ---------------------------------------------------------------------------------------------
# the step alphabet (fixed in advance; each step is a total or partial map Grid -> Grid)
# ---------------------------------------------------------------------------------------------


def s_crop_bbox(g):
    bg = bg_of(g)
    return crop_cells(g, [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v != bg])


def _pick_component(key, by_colour=False, diag=True):
    def f(g):
        bg = bg_of(g)
        comps = components(g, bg, diag=diag, by_colour=by_colour)
        if not comps:
            return None
        vals = [key(g, cp) for cp in comps]
        best = max(vals)
        if vals.count(best) != 1:  # the choice must be unambiguous
            return None
        return crop_cells(g, comps[vals.index(best)])
    return f


def _size(g, cp):
    return len(cp)


def _neg_size(g, cp):
    return -len(cp)


def _ncolours(g, cp):
    return len({g[r][c] for r, c in cp})


def _rarest_colour(g, cp):
    cnt = Counter(v for row in g for v in row)
    return -min(cnt[g[r][c]] for r, c in cp)


def _bbox_area(g, cp):
    rs = [r for r, _ in cp]
    cs = [c for _, c in cp]
    return (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)


def s_upscale(k):
    def f(g):
        return ok([tuple(v for v in row for _ in range(k)) for row in g for _ in range(k)])
    return f


def s_upscale_ncol(g):
    k = len({v for r in g for v in r} - {0})
    return s_upscale(k)(g) if k >= 1 else None


def s_downscale(k):
    def f(g):
        h, w = shape(g)
        if h % k or w % k:
            return None
        out = []
        for R in range(0, h, k):
            row = []
            for C in range(0, w, k):
                vals = {g[R + i][C + j] for i in range(k) for j in range(k)}
                if len(vals) != 1:
                    return None
                row.append(vals.pop())
            out.append(row)
        return ok(out)
    return f


def s_dedup_lines(g):
    rows = [r for i, r in enumerate(g) if i == 0 or r != g[i - 1]]
    t = transpose(G(rows))
    cols = [c for i, c in enumerate(t) if i == 0 or c != t[i - 1]]
    return ok(transpose(G(cols)))


def hcat(a, b):
    if len(a) != len(b):
        return None
    return ok([ra + rb for ra, rb in zip(a, b)])


def vcat(a, b):
    if len(a[0]) != len(b[0]):
        return None
    return ok(list(a) + list(b))


def s_tile(nr, nc):
    def f(g):
        return ok([row * nc for row in g] * nr)
    return f


def s_mirror_h(g):
    return hcat(g, flip_h(g))


def s_mirror_h_rev(g):
    return hcat(flip_h(g), g)


def s_mirror_v(g):
    return vcat(g, flip_v(g))


def s_mirror_v_rev(g):
    return vcat(flip_v(g), g)


def s_mirror_4(g):
    top = hcat(g, flip_h(g))
    return vcat(top, flip_v(top)) if top else None


def s_rot_4(g):
    if len(g) != len(g[0]):
        return None
    top = hcat(g, rot90(g))
    bot = hcat(rot90(rot90(rot90(g))), rot90(rot90(g)))
    return vcat(top, bot) if top and bot else None


def s_kron_self(g):
    """The fractal tiling: block (i, j) is the grid where g[i][j] is coloured, blank otherwise."""
    h, w = shape(g)
    if h * h > MAXDIM or w * w > MAXDIM:
        return None
    bg = 0
    blank = tuple(tuple(bg for _ in range(w)) for _ in range(h))
    out = []
    for i in range(h):
        for r in range(h):
            row = []
            for j in range(w):
                row.extend((g if g[i][j] != bg else blank)[r])
            out.append(row)
    return ok(out)


def _separators(g):
    """Rows and columns made of one colour."""
    h, w = shape(g)
    rows = [i for i in range(h) if len(set(g[i])) == 1]
    cols = [j for j in range(w) if len({g[i][j] for i in range(h)}) == 1]
    return rows, cols


def _cut_blocks(g, rows, cols):
    h, w = shape(g)

    def cuts(n, seps):
        out, start = [], 0
        for s in seps + [n]:
            if s > start:
                out.append((start, s))
            start = s + 1
        return out
    rr, cc = cuts(h, rows), cuts(w, cols)
    bl = [G([row[c0:c1] for row in g[r0:r1]]) for r0, r1 in rr for c0, c1 in cc]
    if len(bl) >= 2 and len({shape(b) for b in bl}) == 1:
        return bl
    return None


def blocks(g) -> Optional[List[Grid]]:
    """Split by full separator lines of one colour, or else into equal halves (thirds) along the
    longer side; blocks must share a shape.  Separator colours are tried non-background first,
    most lines first."""
    h, w = shape(g)
    rows, cols = _separators(g)
    lines = [g[i][0] for i in rows] + [g[0][j] for j in cols]
    if lines:
        bg = bg_of(g)
        cnt = Counter(lines)
        for c in sorted(cnt, key=lambda c: (c == bg, -cnt[c], c)):
            bl = _cut_blocks(g, [i for i in rows if g[i][0] == c],
                             [j for j in cols if g[0][j] == c])
            if bl:
                return bl
    for n in (2, 3):
        if h >= w and h % n == 0:
            k = h // n
            return [G(g[i * k:(i + 1) * k]) for i in range(n)]
        if w > h and w % n == 0:
            k = w // n
            return [G([row[i * k:(i + 1) * k] for row in g]) for i in range(n)]
    return None


def s_split_overlay(op):
    """Split into two blocks and combine them cell by cell; marked cells get SENTINEL, the rest 0
    (a finisher then names the colours)."""
    def f(g):
        bl = blocks(g)
        if not bl or len(bl) != 2:
            return None
        a, b = bl
        out = []
        for ra, rb in zip(a, b):
            out.append([SENTINEL if op(x != 0, y != 0) else 0 for x, y in zip(ra, rb)])
        return ok(out)
    return f


def s_split_stack(g):
    """Split into blocks and overlay them, later blocks drawn over earlier ones (non-zero wins)."""
    bl = blocks(g)
    if not bl:
        return None
    out = [list(r) for r in bl[0]]
    for b in bl[1:]:
        for i, row in enumerate(b):
            for j, v in enumerate(row):
                if v:
                    out[i][j] = v
    return ok(out)


def s_odd_block(g):
    """The block that differs from all the others (unique up to equality)."""
    bl = blocks(g)
    if not bl or len(bl) < 3:
        return None
    cnt = Counter(bl)
    uniq = [b for b in bl if cnt[b] == 1]
    return uniq[0] if len(uniq) == 1 else None


def s_asym_block(g):
    """The only block that is not mirror-symmetric (about a diagonal or an axis)."""
    bl = blocks(g)
    if not bl:
        return None
    sym = lambda b: b == transpose(b) or b == flip_h(b) or b == flip_v(b)
    a = [b for b in bl if not sym(b)]
    return a[0] if len(a) == 1 else None


def s_block_most(g):
    bl = blocks(g)
    if not bl:
        return None
    n = [sum(v != 0 for r in b for v in r) for b in bl]
    return bl[n.index(max(n))] if n.count(max(n)) == 1 else None


def s_block_least(g):
    bl = blocks(g)
    if not bl:
        return None
    n = [sum(v != 0 for r in b for v in r) for b in bl]
    return bl[n.index(min(n))] if n.count(min(n)) == 1 else None


def s_gravity(dr, dc):
    def down(g):
        h, w = shape(g)
        bg = bg_of(g)
        out = [[bg] * w for _ in range(h)]
        for c in range(w):
            col = [g[r][c] for r in range(h) if g[r][c] != bg]
            for i, v in enumerate(reversed(col)):
                out[h - 1 - i][c] = v
        return G(out)

    def f(g):
        if (dr, dc) == (1, 0):
            return down(g)
        if (dr, dc) == (-1, 0):
            return flip_v(down(flip_v(g)))
        if (dr, dc) == (0, 1):
            return transpose(down(transpose(g)))
        return flip_h(transpose(down(transpose(flip_h(g)))))
    return f


def s_fill_enclosed(g):
    """Background cells not 4-connected to the border are marked SENTINEL."""
    h, w = shape(g)
    bg = bg_of(g)
    seen = [[False] * w for _ in range(h)]
    stack = [(r, c) for r in range(h) for c in range(w)
             if (r in (0, h - 1) or c in (0, w - 1)) and g[r][c] == bg]
    for r, c in stack:
        seen[r][c] = True
    while stack:
        y, x = stack.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and not seen[yy][xx] and g[yy][xx] == bg:
                seen[yy][xx] = True
                stack.append((yy, xx))
    changed = False
    out = []
    for r in range(h):
        row = []
        for c in range(w):
            if g[r][c] == bg and not seen[r][c]:
                row.append(SENTINEL)
                changed = True
            else:
                row.append(g[r][c])
        out.append(row)
    return G(out) if changed else None


def s_symmetrize(kind):
    """Complete a symmetry: a background cell takes the colour of its mirror image(s)."""
    maps = {
        "h": [flip_h],
        "v": [flip_v],
        "hv": [flip_h, flip_v, lambda x: flip_h(flip_v(x))],
        "d": [transpose],
        "rot": [rot90, lambda x: rot90(rot90(x)), lambda x: rot90(rot90(rot90(x)))],
    }[kind]

    def f(g):
        if kind in ("d", "rot") and len(g) != len(g[0]):
            return None
        bg = 0 if any(0 in r for r in g) else bg_of(g)
        imgs = [m(g) for m in maps]
        out = []
        for r, row in enumerate(g):
            o = []
            for c, v in enumerate(row):
                if v == bg:
                    cands = {im[r][c] for im in imgs if im[r][c] != bg}
                    if len(cands) > 1:
                        return None
                    v = cands.pop() if cands else v
                o.append(v)
            out.append(o)
        out = G(out)
        return out if out != g else None
    return f


def s_count_row(g):
    """A 1 x n row of the only non-zero colour, n = how many cells carry it."""
    cells = [v for r in g for v in r if v != 0]
    if not cells or len(set(cells)) != 1:
        return None
    return ok([cells])


def s_colour_hist(g):
    """Colours sorted by frequency (most first), one row each, padded with 0."""
    cnt = Counter(v for r in g for v in r if v != 0)
    if not cnt:
        return None
    order = sorted(cnt, key=lambda k: (-cnt[k], k))
    n = cnt[order[0]]
    return ok([[k] * cnt[k] + [0] * (n - cnt[k]) for k in order])


def s_largest_rect_interior(g):
    """Crop to the interior of the largest single-colour rectangular frame."""
    bg = bg_of(g)
    best = None
    for cp in components(g, bg, diag=False, by_colour=True):
        rs = [r for r, _ in cp]
        cs = [c for _, c in cp]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        if r1 - r0 < 2 or c1 - c0 < 2:
            continue
        frame = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                 if r in (r0, r1) or c in (c0, c1)}
        if not frame <= set(cp):
            continue
        area = (r1 - r0) * (c1 - c0)
        if best is None or area > best[0]:
            best = (area, r0, r1, c0, c1)
    if best is None:
        return None
    _, r0, r1, c0, c1 = best
    return ok([row[c0 + 1:c1] for row in g[r0 + 1:r1]])


def s_remove_colour_noise(g):
    """Remove (to background) the least frequent non-background colour."""
    bg = bg_of(g)
    cnt = Counter(v for r in g for v in r if v != bg)
    if len(cnt) < 2:
        return None
    m = min(cnt.values())
    rare = [k for k in cnt if cnt[k] == m]
    if len(rare) != 1:
        return None
    return G([[bg if v == rare[0] else v for v in r] for r in g])


DIHEDRAL: List[Tuple[str, Callable[[Grid], Grid]]] = [
    ("id", lambda g: g),
    ("rot90", rot90),
    ("rot180", lambda g: rot90(rot90(g))),
    ("rot270", lambda g: rot90(rot90(rot90(g)))),
    ("flip_h", flip_h),
    ("flip_v", flip_v),
    ("transpose", transpose),
    ("antitranspose", lambda g: rot90(rot90(transpose(g)))),
]


def s_each_object(tf):
    """Apply a dihedral transform to every object (8-connected, multi-colour) inside its own
    bounding box; objects whose box is not square are left alone only if the transform keeps
    the box shape, otherwise the step fails."""
    def f(g):
        bg = bg_of(g)
        comps = components(g, bg, diag=True)
        if not comps:
            return None
        out = [list(r) for r in g]
        for cp in comps:
            rs = [r for r, _ in cp]
            cs = [c for _, c in cp]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            box = G([row[c0:c1 + 1] for row in g[r0:r1 + 1]])
            nb = tf(box)
            if shape(nb) != shape(box):
                return None
            for i in range(len(nb)):
                for j in range(len(nb[0])):
                    out[r0 + i][c0 + j] = nb[i][j]
        out = G(out)
        return out if out != g else None
    return f


STEPS: List[Tuple[str, Step]] = [
    ("rot90", rot90),
    ("rot180", lambda g: rot90(rot90(g))),
    ("rot270", lambda g: rot90(rot90(rot90(g)))),
    ("flip_h", flip_h),
    ("flip_v", flip_v),
    ("transpose", transpose),
    ("antitranspose", lambda g: rot90(rot90(transpose(g)))),
    ("crop_bbox", s_crop_bbox),
    ("crop_largest", _pick_component(_size)),
    ("crop_smallest", _pick_component(_neg_size)),
    ("crop_largest_mono", _pick_component(_size, by_colour=True)),
    ("crop_smallest_mono", _pick_component(_neg_size, by_colour=True)),
    ("crop_most_colours", _pick_component(_ncolours)),
    ("crop_rarest_colour", _pick_component(_rarest_colour)),
    ("crop_largest_box", _pick_component(_bbox_area)),
    ("crop_frame_interior", s_largest_rect_interior),
    ("up2", s_upscale(2)),
    ("up3", s_upscale(3)),
    ("up4", s_upscale(4)),
    ("up_ncolours", s_upscale_ncol),
    ("down2", s_downscale(2)),
    ("down3", s_downscale(3)),
    ("dedup_lines", s_dedup_lines),
    ("tile_1x2", s_tile(1, 2)),
    ("tile_2x1", s_tile(2, 1)),
    ("tile_2x2", s_tile(2, 2)),
    ("tile_3x3", s_tile(3, 3)),
    ("mirror_h", s_mirror_h),
    ("mirror_h_rev", s_mirror_h_rev),
    ("mirror_v", s_mirror_v),
    ("mirror_v_rev", s_mirror_v_rev),
    ("mirror_4", s_mirror_4),
    ("rot_4", s_rot_4),
    ("kron_self", s_kron_self),
    ("split_and", s_split_overlay(lambda a, b: a and b)),
    ("split_or", s_split_overlay(lambda a, b: a or b)),
    ("split_xor", s_split_overlay(lambda a, b: a != b)),
    ("split_nor", s_split_overlay(lambda a, b: not a and not b)),
    ("split_stack", s_split_stack),
    ("odd_block", s_odd_block),
    ("asym_block", s_asym_block),
    ("block_most", s_block_most),
    ("block_least", s_block_least),
    ("gravity_down", s_gravity(1, 0)),
    ("gravity_up", s_gravity(-1, 0)),
    ("gravity_right", s_gravity(0, 1)),
    ("gravity_left", s_gravity(0, -1)),
    ("fill_enclosed", s_fill_enclosed),
    ("sym_h", s_symmetrize("h")),
    ("sym_v", s_symmetrize("v")),
    ("sym_hv", s_symmetrize("hv")),
    ("sym_d", s_symmetrize("d")),
    ("sym_rot", s_symmetrize("rot")),
    ("count_row", s_count_row),
    ("colour_hist", s_colour_hist),
    ("drop_rare_colour", s_remove_colour_noise),
] + [("each_obj_" + n, s_each_object(t)) for n, t in DIHEDRAL[1:]]
STEP_FN: Dict[str, Step] = dict(STEPS)


def step_weight(name: str) -> int:
    """Occam weight of a step: the symmetries of the square 1, per-object maps 3, the rest 2."""
    if name in dict(DIHEDRAL):
        return 1
    if name.startswith("each_obj_"):
        return 3
    return 2


def plan_weight(plan: Sequence[str]) -> int:
    return sum(step_weight(s) for s in plan)

# ---------------------------------------------------------------------------------------------
# object-level readers (To Do 21): what the observer sees of the object a cell belongs to
# ---------------------------------------------------------------------------------------------

_OBJ_CACHE: Dict[Hashable, object] = {}
_LAST: List[object] = [None, None]


def _object_index(g):
    """For every non-background cell of its single-colour 4-connected object: size, rank,
    position on the bounding box, shape."""
    if g is _LAST[0]:
        return _LAST[1]
    key = G(g)
    hit = _OBJ_CACHE.get(key)
    if hit is not None:
        _LAST[0], _LAST[1] = g, hit
    if hit is not None:
        return hit
    gg = key
    bg = bg_of(gg)
    comps = components(gg, bg, diag=False, by_colour=True)
    sizes = [len(c) for c in comps]
    info = {}
    for cp, n in zip(comps, sizes):
        rs = [r for r, _ in cp]
        cs = [c for _, c in cp]
        r0, c0 = min(rs), min(cs)
        hh, ww = max(rs) - r0 + 1, max(cs) - c0 + 1
        shp = tuple(sorted((r - r0, c - c0) for r, c in cp))
        for r, c in cp:
            info[(r, c)] = dict(size=n, largest=n == max(sizes), smallest=n == min(sizes),
                                pos=(r - r0 == 0, r - r0 == hh - 1, c - c0 == 0, c - c0 == ww - 1),
                                shape=shp, hw=(hh, ww))
    if len(_OBJ_CACHE) > 4096:
        _OBJ_CACHE.clear()
    _OBJ_CACHE[key] = (bg, info)
    _LAST[0], _LAST[1] = g, (bg, info)
    return bg, info


def r_obj_size(g, r, c):
    bg, info = _object_index(g)
    v = g[r][c]
    i = info.get((r, c))
    return ("objsize", v, i["size"] if i else 0), (v,)


def r_obj_rank(g, r, c):
    bg, info = _object_index(g)
    v = g[r][c]
    i = info.get((r, c))
    return ("objrank", v, (i["largest"], i["smallest"]) if i else None), (v,)


def r_obj_blind_size(g, r, c):
    bg, info = _object_index(g)
    v = g[r][c]
    i = info.get((r, c))
    return ("objbsize", v == bg, i["size"] if i else 0), (v,)


def r_obj_shape(g, r, c):
    bg, info = _object_index(g)
    v = g[r][c]
    i = info.get((r, c))
    return ("objshape", v, i["shape"] if i else None), (v,)


def r_obj_blind_shape(g, r, c):
    bg, info = _object_index(g)
    v = g[r][c]
    i = info.get((r, c))
    return ("objbshape", v == bg, i["shape"] if i else None), (v,)


def r_obj_box_edge(g, r, c):
    bg, info = _object_index(g)
    v = g[r][c]
    i = info.get((r, c))
    return ("objedge", v, i["pos"] if i else None, i["hw"] if i else None), (v,)


def _colour_ranks(g):
    if g is _LASTRANK[0]:
        return _LASTRANK[1]
    cnt = Counter(v for r in g for v in r)
    order = sorted(cnt, key=lambda k: (-cnt[k], k))
    ranks = {k: i for i, k in enumerate(order)}
    _LASTRANK[0], _LASTRANK[1] = g, ranks
    return ranks


_LASTRANK: List[object] = [None, None]


def r_colour_rank(g, r, c):
    """The frequency rank of the cell's colour in its grid (0 = most common)."""
    v = g[r][c]
    return ("crank", _colour_ranks(g)[v]), (v,)


OBJECT_READERS = [
    ("colour-rank", r_colour_rank),
    ("obj-size", r_obj_size),
    ("obj-rank", r_obj_rank),
    ("obj-blind-size", r_obj_blind_size),
    ("obj-shape", r_obj_shape),
    ("obj-blind-shape", r_obj_blind_shape),
    ("obj-box-edge", r_obj_box_edge),
]

# Finisher ranks: 0 identity, 1 tiling, then the Round 28 ladder in its order (``cell`` = colour map
# first), then the object readers.
FINISHERS: List[Tuple[str, object]] = (
    [("identity", None), ("tile", "tile")] + [(n, f) for n, f in lri.LADDER] + OBJECT_READERS)

# ---------------------------------------------------------------------------------------------
# the planner
# ---------------------------------------------------------------------------------------------


def run(plan: Sequence[str], g) -> Optional[Grid]:
    """``run`` of ``PlanSearch.lean``: steps left to right; a failing step fails the plan."""
    g = G(g)
    for s in plan:
        if g is None:
            return None
        try:
            g = STEP_FN[s](g)
        except (IndexError, ValueError, ZeroDivisionError):
            return None
    return g


def _as_lists(g: Grid):
    return [list(r) for r in g]


def fit_finisher(reader, mids: Sequence[Grid], outs: Sequence[Grid], qmids: Sequence[Grid]):
    """Fit a finisher on the intermediate grids.  ``reader`` is ``None`` (identity), ``"tile"``
    (the tiling finisher) or a cell reader (a table over it).  Returns
    ``None``           if it does not reproduce the demonstrations (refuted: hard gate D1),
    ``"undetermined"`` if it does, but some query cell is not determined (unseen key, or the
                       surviving entries disagree: ``answer_determined_iff_covered``),
    the list of answers otherwise."""
    if reader == "tile":
        return fit_tiling(mids, outs, qmids)
    if any(shape(m) != shape(o) for m, o in zip(mids, outs)):
        return None
    if reader is None:
        return list(qmids) if all(m == o for m, o in zip(mids, outs)) else None
    pairs = [(m, o) for m, o in zip(mids, outs)]
    t = lri.table(reader, pairs)
    if t is None:
        return None
    answers = []
    for q in qmids:
        a = lri.apply(reader, t, q)
        if a is None:
            return "undetermined"
        answers.append(G(a))
    return answers


def fit_tiling(mids, outs, qmids):
    """The tiling finisher: the output is an ``a x b`` array of blocks, block ``(i, j)`` being
    ``T_ij`` (a symmetry of the square) of the grid followed by a colour map ``m_ij``, both
    fitted from the demonstrations.  A block of the query answer is given only if every
    surviving ``(T_ij, m_ij)`` gives the same block (the agreement rule, per block)."""
    ab = set()
    for m, o in zip(mids, outs):
        (h, w), (H, W) = shape(m), shape(o)
        if H % h or W % w:
            return None
        ab.add((H // h, W // w))
    if len(ab) != 1:
        return None
    a, b = ab.pop()
    if (a, b) == (1, 1) or a * b > 36:
        return None
    blocks_out = {}
    for i in range(a):
        for j in range(b):
            surv = []
            for tname, tf in DIHEDRAL:
                cmap: Dict[int, int] = {}
                good = True
                for m, o in zip(mids, outs):
                    tm = tf(m)
                    h, w = shape(m)
                    if shape(tm) != (h, w):
                        good = False
                        break
                    for r in range(h):
                        for c in range(w):
                            x, y = tm[r][c], o[i * h + r][j * w + c]
                            if cmap.setdefault(x, y) != y:
                                good = False
                                break
                        if not good:
                            break
                    if not good:
                        break
                if good:
                    surv.append((tf, cmap))
            if not surv:
                return None
            blocks_out[(i, j)] = surv
    answers = []
    for q in qmids:
        h, w = shape(q)
        out = [[None] * (w * b) for _ in range(h * a)]
        for (i, j), surv in blocks_out.items():
            cands = set()
            for tf, cmap in surv:
                tq = tf(q)
                if shape(tq) != (h, w) or any(v not in cmap for row in tq for v in row):
                    return "undetermined"
                cands.add(G([[cmap[v] for v in row] for row in tq]))
            if len(cands) != 1:
                return "undetermined"
            blk = cands.pop()
            for r in range(h):
                for c in range(w):
                    out[i * h + r][j * w + c] = blk[r][c]
        answers.append(ok(out))
        if answers[-1] is None:
            return None
    return answers


def separating_question(two_answers) -> Dict[str, object]:
    """The example to ask for when plans disagree (``separating_example_refutes``): the first
    query cell where two surviving answers differ (or the output shape, if that differs).  Its
    true value refutes at least one of the two plans."""
    a, b = two_answers
    for qi, (ga, gb) in enumerate(zip(a, b)):
        if shape(ga) != shape(gb):
            return dict(query=qi, cell=None, values=(shape(ga), shape(gb)),
                        text="ask for the output size of query %d (%s or %s)" % (
                            qi, shape(ga), shape(gb)))
        for r, (ra, rb) in enumerate(zip(ga, gb)):
            for c, (x, y) in enumerate(zip(ra, rb)):
                if x != y:
                    return dict(query=qi, cell=(r, c), values=(x, y),
                                text="ask for query %d, cell (%d, %d): %d or %d" % (
                                    qi, r, c, x, y))
    return dict(query=None, cell=None, values=None, text="answers differ")


def leave_one_out(reader, mids, outs) -> bool:
    """Every demonstration is predicted exactly by the finisher fitted on the others."""
    if len(mids) < 2:
        return False
    for i in range(len(mids)):
        rest_m = [m for j, m in enumerate(mids) if j != i]
        rest_o = [o for j, o in enumerate(outs) if j != i]
        res = fit_finisher(reader, rest_m, rest_o, [mids[i]])
        if res is None or res == "undetermined" or res[0] != outs[i]:
            return False
    return True


def _expand(layer: Dict[tuple, tuple], seen: set, t0: float, budget_s: float):
    nxt: Dict[tuple, tuple] = {}
    for sigv, plan in layer.items():
        for name, fn in STEPS:
            new = []
            for s in sigv:
                try:
                    v = fn(s)
                except (IndexError, ValueError, ZeroDivisionError):
                    v = None
                if v is None:
                    break
                new.append(v)
            if len(new) != len(sigv):
                continue  # a failing step fails the plan
            key = tuple(new)
            if key in seen:  # merge: a plan with this signature is already kept (dedup_rep)
                continue
            seen.add(key)
            nxt[key] = plan + (name,)
        if time.time() - t0 > budget_s:
            break
    return nxt


def solve(train: Sequence[Tuple[object, object]], queries: Sequence[object], max_depth: int = 3,
          policy: str = "ladder", budget_s: float = 30.0, max_layer: int = 3000,
          finishers: Optional[List] = None, listen: bool = True) -> Dict[str, object]:
    """Breadth-first planner with merging.

    Layer ``n`` holds one plan per signature: the states of the demonstration inputs *and of
    the queries* after the plan (``sig`` in ``PlanSearch.lean``).  Hypotheses are ordered by cost
    tier ``(n, finisher rank, Occam weight)``.  At the first tier with a hypothesis that reproduces every
    demonstration, all such hypotheses must give the same answer:

    * ``policy="strict"`` -- if some consistent hypothesis of the tier leaves the query
      undetermined, or two disagree, refuse (``planner_agree_all``);
    * ``policy="ladder"`` -- as Round 28's ladder: a tier whose consistent hypotheses are *all*
      undetermined is skipped (two determined hypotheses that disagree still refuse, and a tier
      mixing determined and undetermined hypotheses refuses).

    ``listen`` (default on): a plan of length >= 2 with a *fitted* finisher must also pass the
    leave-one-out test (each demonstration predicted from the others; Round 28's "tuning by
    ear" listening test).  This is an extra gate that only removes hypotheses; it guards against
    long plans that fit three demonstrations by accident.

    Returns a dict with ``status`` in {"answered", "refused"}, the answer, the plan, and search
    statistics.
    """
    t0 = time.time()
    fins = finishers if finishers is not None else FINISHERS
    ins = [G(a) for a, _ in train]
    outs = [G(b) for _, b in train]
    qs = [G(q) for q in queries]
    probes = tuple(ins + qs)
    nin = len(ins)
    layer: Dict[tuple, tuple] = {probes: ()}
    seen = {probes}
    explored = 1
    for depth in range(0, max_depth + 1):
        if depth > 0:
            layer = _expand(layer, seen, t0, budget_s)
            explored += len(layer)
            if len(layer) > max_layer:  # bounded search: keep the first max_layer plans in order
                layer = dict(sorted(layer.items(), key=lambda kv: kv[1])[:max_layer])
        same = [(sigv, plan) for sigv, plan in layer.items()
                if all(shape(m) == shape(o) for m, o in zip(sigv[:nin], outs))]
        for fname, reader in fins:
            cands = list(layer.items()) if reader == "tile" else same
            hyps = []  # (weight, plan, answers or "undetermined")
            for sigv, plan in cands:
                res = fit_finisher(reader, sigv[:nin], outs, sigv[nin:])
                if res is None:
                    continue
                if listen and reader is not None and depth >= 2 and \
                        not leave_one_out(reader, sigv[:nin], outs):
                    continue
                hyps.append((plan_weight(plan), plan, res))
            # cost tiers (depth, finisher rank, Occam weight), lexicographic (minAgree_correct)
            for wt in sorted({h[0] for h in hyps}):
                tier = [h for h in hyps if h[0] == wt]
                consistent = [(p, tuple(r)) for _, p, r in tier if r != "undetermined"]
                undetermined = [p for _, p, r in tier if r == "undetermined"]
                answers = {a for _, a in consistent}
                stats = dict(depth=depth, finisher=fname, weight=wt, explored=explored,
                             seconds=round(time.time() - t0, 2), n_consistent=len(tier))
                name = "(%d, %s, %d)" % (depth, fname, wt)
                if undetermined and (policy == "strict" or consistent):
                    return dict(status="refused", why="tier %s: %d consistent plan(s) leave the "
                                "query undetermined" % (name, len(undetermined)),
                                plans=[list(p) for p in undetermined[:3]], **stats)
                if undetermined:
                    continue  # ladder policy: every hypothesis of this tier is undetermined
                if len(answers) > 1:
                    ask = separating_question(sorted(answers)[:2])
                    return dict(status="refused", why="tier %s: %d consistent plans disagree; "
                                "%s" % (name, len(consistent), ask["text"]), ask=ask,
                                plans=[list(p) for p, _ in consistent[:3]], **stats)
                return dict(status="answered",
                            answer=[list(map(list, a)) for a in answers.pop()],
                            plan=list(consistent[0][0]), agreeing_plans=len(consistent), **stats)
        if time.time() - t0 > budget_s:
            return dict(status="refused", why="search budget exhausted at depth %d" % depth,
                        explored=explored, seconds=round(time.time() - t0, 2))
    return dict(status="refused", why="no plan of length <= %d reproduces the demonstrations"
                % max_depth, explored=explored, seconds=round(time.time() - t0, 2))


def solve_task(task: dict, **kw) -> Dict[str, object]:
    train = [(p["input"], p["output"]) for p in task["train"]]
    queries = [p["input"] for p in task["test"]]
    return solve(train, queries, **kw)


def describe(res: Dict[str, object]) -> str:
    if res["status"] != "answered":
        return "planner: refused -- " + str(res.get("why"))
    plan = " -> ".join(res["plan"]) or "(no step)"
    return "planner: %s, then finisher %s (%d agreeing plan(s), depth %d)" % (
        plan, res["finisher"], res["agreeing_plans"], res["depth"])


def grid_text(g) -> str:
    return " / ".join("".join(str(v) for v in row) for row in g)


def induce_text(pairs, query) -> Tuple[bool, str, Dict[str, object]]:
    res = solve(pairs, [query])
    if res["status"] != "answered":
        return False, describe(res), dict(res, family="planner")
    return True, describe(res) + ": " + grid_text(res["answer"][0]), dict(res, family="planner")


def arc_text(name: str) -> Tuple[bool, str, Dict[str, object]]:
    import json
    task = json.load(open(lri.arc_task_path(name)))
    res = solve_task(task)
    if res["status"] != "answered":
        return False, "arc %s: %s" % (name, describe(res)), dict(res, status="refused")
    right = all(a == p.get("output") for a, p in zip(res["answer"], task["test"]))
    return right, "arc %s: %s -- %s" % (name, describe(res), "RIGHT" if right else "WRONG"), \
        dict(res, status="right" if right else "wrong")
