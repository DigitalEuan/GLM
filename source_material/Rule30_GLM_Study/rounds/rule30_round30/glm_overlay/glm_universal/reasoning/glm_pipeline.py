"""``glm_universal.reasoning.glm_pipeline`` -- Round 30: one pipeline for planning, asking and
measuring.

Round 29 gave the GLM a stepwise planner for grid puzzles (``grid_planner.py``; Lean
``GLM.PlanSearch``).  Round 30 turns the four follow-up items of that round into **one pipeline**
that shares one search, one hypothesis table and one refusal rule:

=====  ==========================================  ==============================================
stage  what it adds (To Do item)                   Lean statement it respects (``GLM.Pipeline``)
=====  ==========================================  ==============================================
1      fitted *middle* steps and goal regression   ``run_append_eq_some_iff_runBack`` (an
       (To Do 23): a fitted reader followed by an  invertible suffix is read backwards from the
       invertible suffix, a scale step whose       goal), ``shapePrune_sound`` (a step whose exact
       factor is read from the grid, line drawing  output shape cannot meet the goal is skipped
       and per-object moves; the last layer is     without losing a consistent plan)
       pruned by the goal's shape
2      the ask loop (To Do 24, 21): on a refusal,  ``askLoop_correct``, ``askLoop_length_le``
       ask the oracle for one query cell and       (each answer to a separating question removes
       re-decide on the *same* search              a hypothesis, the truth is never removed, at
                                                   most ``|H| - 1`` questions)
3      the Occam measurement (To Do 26): the       ``gate_keeps_truth``, ``gate_can_drop_truth``
       leave-one-out gate from depth ``k``         (a gate is sound iff it keeps the truth; a
                                                   leave-one-out gate can drop it)
4      the planner over statements (To Do 25, 18)  see ``statement_planner.py``
=====  ==========================================  ==============================================

The search is built **once** per puzzle (``Search``); deciding, asking and gating only re-read it
(the signature of a plan does not depend on what is asked, ``sig_append_congr``).

Exact and deterministic; test outputs are only read by the simulated oracle of stage 2 and by
the scorers, never by the planner.
"""
from __future__ import annotations

import time
from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

try:  # inside the GLM
    from . import grid_planner as gp
    from . import local_rule_induction as lri
except ImportError:  # stand-alone (study folder)
    import grid_planner as gp  # type: ignore
    import local_rule_induction as lri  # type: ignore

Grid = Tuple[Tuple[int, ...], ...]
G, shape, bg_of = gp.G, gp.shape, gp.bg_of

# The leave-one-out gate (Round 28's "listening test") applies to fitted finishers from plan
# depth 1 when there are at most two demonstrations, from depth 2 otherwise (the Round 29
# setting).  Chosen from the Round 30 Occam measurement (To Do 26, ``pipeline_bench.py`` C).
AUTO = "auto"

# =============================================================================================
# Stage 1a: new fixed steps (To Do 23: lines between objects, per-object moves, positional crops)
# =============================================================================================


def _connect_rows(g: Grid) -> Grid:
    bg = bg_of(g)
    out = [list(r) for r in g]
    for r, row in enumerate(g):
        last = None
        for c, v in enumerate(row):
            if v == bg:
                continue
            if last is not None and row[last] == v and c - last > 1:
                for x in range(last + 1, c):
                    out[r][x] = v
            last = c
    return G(out)


def s_connect(axis: str):
    """Draw a line between two cells of the same colour in one row (``h``), one column (``v``)
    or both (``hv``), when only background lies between them."""
    def f(g):
        if axis == "h":
            out = _connect_rows(g)
        elif axis == "v":
            out = gp.transpose(_connect_rows(gp.transpose(g)))
        else:
            a, b = _connect_rows(g), gp.transpose(_connect_rows(gp.transpose(g)))
            out = G([[x if x != v else y for x, y, v in zip(ra, rb, rg)]
                     for ra, rb, rg in zip(a, b, g)])
        return out if out != g else None
    return f


def _fall_down(g: Grid) -> Optional[Grid]:
    """Every object (8-connected, multi-colour) falls rigidly until it meets the floor or
    another object; lower objects move first."""
    h, w = shape(g)
    bg = bg_of(g)
    comps = gp.components(g, bg, diag=True)
    if not comps:
        return None
    comps.sort(key=lambda cp: -max(r for r, _ in cp))
    occ = [[False] * w for _ in range(h)]
    out = [[bg] * w for _ in range(h)]
    for cp in comps:
        k = 0
        while all(r + k + 1 < h and not occ[r + k + 1][c] for r, c in cp):
            k += 1
        for r, c in cp:
            occ[r + k][c] = True
            out[r + k][c] = g[r][c]
    out = G(out)
    return out if out != g else None


def s_obj_fall(direction: str):
    pre, post = {
        "down": (lambda g: g, lambda g: g),
        "up": (gp.flip_v, gp.flip_v),
        "right": (lambda g: gp.flip_v(gp.transpose(g)), lambda g: gp.transpose(gp.flip_v(g))),
        "left": (gp.transpose, gp.transpose),
    }[direction]

    def f(g):
        r = _fall_down(pre(g))
        return post(r) if r is not None else None
    return f


def _pick_by(key):
    """Crop to the object (8-connected, multi-colour) with the unique largest ``key``."""
    def f(g):
        bg = bg_of(g)
        comps = gp.components(g, bg, diag=True)
        if len(comps) < 2:
            return None
        vals = [key(g, cp) for cp in comps]
        best = max(vals)
        if vals.count(best) != 1:
            return None
        return gp.crop_cells(g, comps[vals.index(best)])
    return f


def _unique_colour_obj(g, cp):
    """1 if the object's colour set occurs in no other object."""
    bg = bg_of(g)
    mine = frozenset(g[r][c] for r, c in cp)
    others = [frozenset(g[r][c] for r, c in o) for o in gp.components(g, bg, diag=True)]
    return 1 if others.count(mine) == 1 else 0


def _unique_shape_obj(g, cp):
    bg = bg_of(g)

    def norm(p):
        r0 = min(r for r, _ in p)
        c0 = min(c for _, c in p)
        return frozenset((r - r0, c - c0) for r, c in p)
    shapes = [norm(o) for o in gp.components(g, bg, diag=True)]
    return 1 if shapes.count(norm(cp)) == 1 else 0


NEW_STEPS = [
    ("connect_h", s_connect("h")),
    ("connect_v", s_connect("v")),
    ("connect_hv", s_connect("hv")),
    ("obj_fall_down", s_obj_fall("down")),
    ("obj_fall_up", s_obj_fall("up")),
    ("obj_fall_left", s_obj_fall("left")),
    ("obj_fall_right", s_obj_fall("right")),
    ("crop_topmost", _pick_by(lambda g, cp: -min(r for r, _ in cp))),
    ("crop_bottommost", _pick_by(lambda g, cp: max(r for r, _ in cp))),
    ("crop_leftmost", _pick_by(lambda g, cp: -min(c for _, c in cp))),
    ("crop_rightmost", _pick_by(lambda g, cp: max(c for _, c in cp))),
    ("crop_unique_colour", _pick_by(_unique_colour_obj)),
    ("crop_unique_shape", _pick_by(_unique_shape_obj)),
]

STEPS = list(gp.STEPS) + NEW_STEPS
STEP_FN = dict(STEPS)


def step_weight(name: str) -> int:
    return gp.step_weight(name)


def plan_weight(plan: Sequence[str]) -> int:
    return sum(step_weight(s) for s in plan)


def run(plan: Sequence[str], g) -> Optional[Grid]:
    g = G(g)
    for s in plan:
        if g is None:
            return None
        try:
            g = STEP_FN[s](g)
        except (IndexError, ValueError, ZeroDivisionError):
            return None
    return g

# =============================================================================================
# Stage 1b: exact output shapes, for goal regression on shapes (``shapePrune_sound``)
# =============================================================================================

_SAME = ["rot180", "flip_h", "flip_v", "gravity_down", "gravity_up", "gravity_right",
         "gravity_left", "fill_enclosed", "sym_h", "sym_v", "sym_hv", "sym_d", "sym_rot",
         "drop_rare_colour", "connect_h", "connect_v", "connect_hv", "obj_fall_down",
         "obj_fall_up", "obj_fall_left", "obj_fall_right"] + \
    ["each_obj_" + n for n, _ in gp.DIHEDRAL[1:]]
_SWAP = ["rot90", "rot270", "transpose", "antitranspose"]


def _mul(a, b):
    return lambda h, w: (h * a, w * b)


SHAPE_FN = {n: (lambda h, w: (h, w)) for n in _SAME}
SHAPE_FN.update({n: (lambda h, w: (w, h)) for n in _SWAP})
SHAPE_FN.update({"up2": _mul(2, 2), "up3": _mul(3, 3), "up4": _mul(4, 4),
                 "tile_1x2": _mul(1, 2), "tile_2x1": _mul(2, 1), "tile_2x2": _mul(2, 2),
                 "tile_3x3": _mul(3, 3), "mirror_h": _mul(1, 2), "mirror_h_rev": _mul(1, 2),
                 "mirror_v": _mul(2, 1), "mirror_v_rev": _mul(2, 1), "mirror_4": _mul(2, 2),
                 "rot_4": _mul(2, 2), "kron_self": lambda h, w: (h * h, w * w),
                 "down2": lambda h, w: (h // 2, w // 2), "down3": lambda h, w: (h // 3, w // 3)})


def goal_compatible(mid: Tuple[int, int], out: Tuple[int, int]) -> bool:
    """Can *some* finisher (with or without a suffix or scale step) map a grid of shape ``mid``
    to one of shape ``out``?  Equal or swapped shapes, or an integer ratio either way.  This
    over-approximates the shape relation of every finisher, so pruning by it is sound
    (``shapePrune_sound``)."""
    (h, w), (H, W) = mid, out
    if h <= 0 or w <= 0:
        return False
    for (a, b) in ((h, w), (w, h)):
        if (a, b) == (H, W):
            return True
        if H % a == 0 and W % b == 0:
            return True
        if a % H == 0 and b % W == 0:
            return True
    return False

# =============================================================================================
# Stage 1c: fitted readers with partial answers (asked cells refine the table)
# =============================================================================================

FINISHERS = list(gp.FINISHERS)          # identity, tile, the 21 Round 28 readers, 7 object readers
FIN_RANK: Dict[str, float] = {n: i for i, (n, _) in enumerate(FINISHERS)}
FIN_RANK["scale-fit"] = 1.5
FITTED_READERS = [(n, f) for n, f in FINISHERS if n not in ("identity", "tile")]


def _split_extra(extra):
    cells = [e for e in extra if e[0] != "S"]
    shapes = {e[1]: (e[2], e[3]) for e in extra if e[0] == "S"}
    return cells, shapes


def fit_reader(reader, mids, outs, qmids, cells=()):
    """The fitted table of ``reader`` on the demonstrations plus the asked query cells
    ``cells = [(query index, r, c, value)]``.  Returns ``None`` (refuted) or a list of partial
    answers (cells ``None`` where the query is not determined)."""
    t: Dict[object, frozenset] = {}
    for a, b in zip(mids, outs):
        for r in range(len(a)):
            for c in range(len(a[0])):
                k, slots = reader(a, r, c)
                enc = lri._encodings(b[r][c], slots)
                t[k] = t[k] & enc if k in t else enc
                if not t[k]:
                    return None
    for qi, r, c, v in cells:
        q = qmids[qi]
        if not (0 <= r < len(q) and 0 <= c < len(q[0])):
            return None
        k, slots = reader(q, r, c)
        enc = lri._encodings(v, slots)
        t[k] = t[k] & enc if k in t else enc
        if not t[k]:
            return None
    answers = []
    for q in qmids:
        rows = []
        for r in range(len(q)):
            row = []
            for c in range(len(q[0])):
                k, slots = reader(q, r, c)
                if k not in t:
                    row.append(None)
                    continue
                vals = {lri._decode(e, slots) for e in t[k]}
                row.append(vals.pop() if len(vals) == 1 else None)
            rows.append(tuple(row))
        answers.append(tuple(rows))
    return answers


def leave_one_out(reader, mids, outs) -> bool:
    """Each demonstration is predicted exactly by the reader fitted on the others."""
    if len(mids) < 2:
        return False
    for i in range(len(mids)):
        rm = [m for j, m in enumerate(mids) if j != i]
        ro = [o for j, o in enumerate(outs) if j != i]
        res = fit_reader(reader, rm, ro, [mids[i]])
        if res is None or res[0] != outs[i]:
            return False
    return True

# =============================================================================================
# Stage 1d: invertible suffixes (goal regression, ``run_append_eq_some_iff_runBack``) and the
# fitted scale step
# =============================================================================================


def _inv_dihedral(name):
    inv = {"rot90": "rot270", "rot270": "rot90"}.get(name, name)
    return dict(gp.DIHEDRAL)[inv]


def _up_partial(k):
    return lambda a: tuple(tuple(v for v in row for _ in range(k)) for row in a for _ in range(k))


# (name, forward step, exact preimage, Occam weight)
SUFFIXES = [(n, f, _inv_dihedral(n), 1) for n, f in gp.DIHEDRAL[1:]] + \
    [("up2", gp.s_upscale(2), gp.s_downscale(2), 2),
     ("up3", gp.s_upscale(3), gp.s_downscale(3), 2)]
SUFFIX_PARTIAL = {n: f for n, f in gp.DIHEDRAL[1:]}
SUFFIX_PARTIAL.update({"up2": _up_partial(2), "up3": _up_partial(3)})


def _pull_cell(name, qshape, r, c):
    """Where cell ``(r, c)`` of the final answer comes from in the suffix's input (shape
    ``qshape``), so that an asked cell can refine the reader *before* the suffix."""
    h, w = qshape
    if name.startswith("up"):
        k = int(name[2:])
        return (r // k, c // k) if r // k < h and c // k < w else None
    idx = tuple(tuple((i, j) for j in range(w)) for i in range(h))
    img = dict(gp.DIHEDRAL)[name](idx)
    if not (0 <= r < len(img) and 0 <= c < len(img[0])):
        return None
    return img[r][c]


# features a scale factor can be read from (To Do 23: "scale to a size read from the grid")
def _ncol(g):
    return len({v for r in g for v in r} - {bg_of(g)})


def _nobj(g):
    return len(gp.components(g, bg_of(g), diag=True))


def _maxobj(g):
    cs = gp.components(g, bg_of(g), diag=True)
    return max((len(c) for c in cs), default=0)


def _ncells(g):
    bg = bg_of(g)
    return sum(v != bg for r in g for v in r)


def _minority(g):
    cnt = Counter(v for r in g for v in r if v != bg_of(g))
    return min(cnt.values()) if cnt else 0


SCALE_FEATURES = [("n-colours", _ncol), ("n-objects", _nobj), ("largest-object", _maxobj),
                  ("n-cells", _ncells), ("rarest-colour-count", _minority)]


def fit_scale(mids, outs, qmids):
    """The fitted scale step: each demonstration's output is its input scaled up (or down) by an
    integer factor ``k``, and ``k`` is read from the input by a feature.  Constant factors are
    already fixed steps (``up_k``, ``down_k``), so only grid-read factors are tried.  Returns the
    list of ``(feature, scaled queries or None)`` over the consistent features, or ``None``."""
    ks, direction = [], None
    for m, o in zip(mids, outs):
        (h, w), (H, W) = shape(m), shape(o)
        if H % h == 0 and W % w == 0 and H // h == W // w and H // h >= 2:
            d, k = "up", H // h
        elif h % H == 0 and w % W == 0 and h // H == w // W and h // H >= 2:
            d, k = "down", h // H
        else:
            return None
        if direction not in (None, d):
            return None
        direction = d
        ks.append(k)
    scale = gp.s_upscale if direction == "up" else gp.s_downscale
    for m, o, k in zip(mids, outs, ks):
        if scale(k)(m) != o:
            return None  # the step itself must reproduce the demonstration exactly
    res = []
    for name, feat in SCALE_FEATURES:
        if all(feat(m) == k for m, k in zip(mids, ks)):
            scaled = []
            for q in qmids:
                k = feat(q)
                s = scale(k)(q) if k >= 2 else None
                if s is None:
                    scaled = None
                    break
                scaled.append(s)
            res.append((name, scaled))
    return res or None

# =============================================================================================
# Stage 2: the search (built once) and the decision (re-read on every question)
# =============================================================================================


class Search:
    """Breadth-first layers with merging on the probes (demonstration inputs *and* queries),
    as ``PlanSearch.layer``; the last layer is pruned by the goal's shape (``shapePrune_sound``).
    ``stats['pruned']`` counts the step expansions skipped by the pruning."""

    def __init__(self, train, queries, max_depth=2, budget_s=30.0, max_layer=3000,
                 prune=True, steps=None):
        self.t0 = time.time()
        self.ins = [G(a) for a, _ in train]
        self.outs = [G(b) for _, b in train]
        self.qs = [G(q) for q in queries]
        self.nin = len(self.ins)
        self.max_depth = max_depth
        self.steps = steps if steps is not None else STEPS
        probes = tuple(self.ins + self.qs)
        self.layers: List[Dict[tuple, tuple]] = [{probes: ()}]
        seen = {probes}
        self.stats = dict(explored=1, applied=0, pruned=0, budget_hit=False)
        oshapes = [shape(o) for o in self.outs]
        for depth in range(1, max_depth + 1):
            last = depth == max_depth
            nxt: Dict[tuple, tuple] = {}
            for sigv, plan in self.layers[-1].items():
                for name, fn in self.steps:
                    if prune and last and name in SHAPE_FN:
                        sf = SHAPE_FN[name]
                        if not all(goal_compatible(sf(*shape(m)), o)
                                   for m, o in zip(sigv[:self.nin], oshapes)):
                            self.stats["pruned"] += 1
                            continue
                    self.stats["applied"] += 1
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
                        continue
                    key = tuple(new)
                    if key in seen:
                        continue
                    seen.add(key)
                    nxt[key] = plan + (name,)
                if time.time() - self.t0 > budget_s:
                    self.stats["budget_hit"] = True
                    break
            if len(nxt) > max_layer:
                nxt = dict(sorted(nxt.items(), key=lambda kv: kv[1])[:max_layer])
            self.stats["explored"] += len(nxt)
            self.layers.append(nxt)
            if self.stats["budget_hit"]:
                break
        self.stats["seconds"] = round(time.time() - self.t0, 2)
        self._cache: Dict[tuple, list] = {}

    # ---- hypotheses -------------------------------------------------------------------------

    def hypotheses(self, depth: int, listen_from: Optional[int], extra=(),
                   middle: bool = True) -> list:
        """All hypotheses of plan depth ``depth`` that reproduce the demonstrations and the asked
        cells.  Each is ``(finisher rank, weight, (plan, finisher, suffix), answers)``;
        ``answers`` is a list of partial grids, or ``None`` if the hypothesis cannot give even
        the output shape.  ``middle=False`` switches stage 1 (fitted middle steps) off."""
        if listen_from == "auto":  # To Do 26: gate from depth 1 when demonstrations are few
            listen_from = 1 if self.nin <= 2 else 2
        key = (depth, listen_from, tuple(extra), middle)
        if key in self._cache:
            return self._cache[key]
        cells, shapes = _split_extra(extra)
        hyps = []
        outs, nin = self.outs, self.nin
        if depth < len(self.layers):
            for sigv, plan in self.layers[depth].items():
                mids, qm = sigv[:nin], list(sigv[nin:])
                same = all(shape(m) == shape(o) for m, o in zip(mids, outs))
                wt = plan_weight(plan)
                for fname, reader in FINISHERS:
                    if reader is None:
                        if same and all(m == o for m, o in zip(mids, outs)):
                            hyps.append((FIN_RANK[fname], wt, (plan, fname, None), qm))
                    elif reader == "tile":
                        res = gp.fit_tiling(mids, outs, qm)
                        if res is None:
                            continue
                        if listen_from is not None and depth >= listen_from and \
                                not gp.leave_one_out("tile", mids, outs):
                            continue
                        hyps.append((FIN_RANK[fname], wt, (plan, fname, None),
                                     None if res == "undetermined" else [G(a) for a in res]))
                    elif same:
                        res = fit_reader(reader, mids, outs, qm, cells)
                        if res is None:
                            continue
                        if listen_from is not None and depth >= listen_from and \
                                not leave_one_out(reader, mids, outs):
                            continue
                        hyps.append((FIN_RANK[fname], wt, (plan, fname, None), res))
        # stage 1: fitted middle steps -- a reader (or the scale step) at depth - 1, then an
        # invertible suffix read backwards from the goal
        if middle and depth >= 1 and depth - 1 < len(self.layers):
            for sigv, plan in self.layers[depth - 1].items():
                mids, qm = sigv[:nin], list(sigv[nin:])
                wt0 = plan_weight(plan)
                sres = fit_scale(mids, outs, qm)
                for feat, scaled in sres or []:
                    hyps.append((FIN_RANK["scale-fit"], wt0 + 2,
                                 (plan, "scale-fit[%s]" % feat, None), scaled))
                for sname, sfn, spre, swt in SUFFIXES:
                    routs = []
                    for o in outs:
                        try:
                            z = spre(o)
                        except (IndexError, ValueError, ZeroDivisionError):
                            z = None
                        if z is None:
                            break
                        routs.append(G(z))
                    if len(routs) != len(outs):
                        continue
                    if not all(shape(m) == shape(z) for m, z in zip(mids, routs)):
                        continue
                    if not all(G(sfn(z)) == o for z, o in zip(routs, outs)):
                        continue  # the preimage must be exact
                    pcells = []
                    for qi, r, c, v in cells:
                        src = _pull_cell(sname, shape(qm[qi]), r, c)
                        if src is None:
                            pcells = None
                            break
                        pcells.append((qi, src[0], src[1], v))
                    if pcells is None:
                        continue
                    for fname, reader in FITTED_READERS:
                        res = fit_reader(reader, mids, routs, qm, pcells)
                        if res is None:
                            continue
                        if listen_from is not None and depth >= listen_from and \
                                not leave_one_out(reader, mids, routs):
                            continue
                        ans = [G(SUFFIX_PARTIAL[sname](a)) for a in res]
                        hyps.append((FIN_RANK[fname], wt0 + swt, (plan, fname, sname), ans))
        # asked cells and shapes filter every hypothesis (and fill cells it left open)
        if cells or shapes:
            kept = []
            for h in hyps:
                ans = h[3]
                if ans is None:
                    kept.append(h)
                    continue
                if any(shape(ans[qi]) != s for qi, s in shapes.items()):
                    continue
                ans = [list(map(list, a)) for a in ans]
                good = True
                for qi, r, c, v in cells:
                    a = ans[qi]
                    if not (0 <= r < len(a) and 0 <= c < len(a[0])):
                        good = False
                        break
                    if a[r][c] is None:
                        a[r][c] = v
                    elif a[r][c] != v:
                        good = False
                        break
                if good:
                    kept.append((h[0], h[1], h[2], [G(a) for a in ans]))
            hyps = kept
        self._cache[key] = hyps
        return hyps

    # ---- the decision -----------------------------------------------------------------------

    def decide(self, listen_from=AUTO, extra=(), middle: bool = True,
               max_depth: Optional[int] = None, ask_mode: bool = False) -> Dict[str, object]:
        """The Round 29 decision rule (ladder policy) over the extended hypothesis space:
        at the first cost tier ``(depth, finisher rank, weight)`` with a hypothesis, answer only
        if every hypothesis of the tier is fully determined and all agree; a tier whose
        hypotheses are *all* undetermined is skipped.  A refusal names the question to ask.

        ``ask_mode`` (used by the ask loop, when an oracle is available): an all-undetermined
        tier is *not* skipped; the decision refuses and names one of its open cells, so that no
        costlier tier answers while a cheaper one can still be settled by a question (the
        tiered rule of ``minAgree_correct`` instead of the ladder)."""
        top = self.max_depth if max_depth is None else min(max_depth, self.max_depth)
        for depth in range(0, top + 1):
            hyps = self.hypotheses(depth, listen_from, extra, middle)
            for tier_key in sorted({(h[0], h[1]) for h in hyps}):
                tier = [h for h in hyps if (h[0], h[1]) == tier_key]
                det = [h for h in tier if h[3] is not None and
                       all(v is not None for a in h[3] for row in a for v in row)]
                und = [h for h in tier if h[3] is None or
                       any(v is None for a in h[3] for row in a for v in row)]
                info = dict(depth=depth, tier=tier_key, n_hyp=len(tier),
                            plans=[_describe(h) for h in tier[:3]])
                if und and det:
                    return dict(status="refused", why="undetermined", ask=_ask_open(und),
                                **info)
                if und:
                    if ask_mode:
                        return dict(status="refused", why="undetermined", ask=_ask_open(und),
                                    **info)
                    continue
                answers = {tuple(h[3]) for h in det}
                if len(answers) > 1:
                    two = sorted(answers)[:2]
                    return dict(status="refused", why="disagree",
                                ask=_ask_separating(two), **info)
                return dict(status="answered", answer=[list(map(list, a)) for a in answers.pop()],
                            plan=_describe(det[0]), agreeing=len(det), **info)
        # every tier undetermined: the cheapest tier names the question (Occam order)
        for depth in range(0, top + 1):
            hyps = self.hypotheses(depth, listen_from, extra, middle)
            if hyps:
                tier_key = min((h[0], h[1]) for h in hyps)
                und = [h for h in hyps if (h[0], h[1]) == tier_key]
                return dict(status="refused", why="undetermined", ask=_ask_open(und),
                            depth=depth, tier=tier_key, n_hyp=len(und),
                            plans=[_describe(h) for h in und[:3]])
        return dict(status="refused", why="no plan", ask=None)


def _describe(h) -> str:
    plan, fin, suf = h[2]
    s = " -> ".join(plan) or "(no step)"
    s += " | " + fin
    if suf:
        s += " -> " + suf
    return s


def _ask_separating(two) -> Optional[tuple]:
    """The first query cell where two surviving answers differ (``separating_example_refutes``);
    ``("shape", qi)`` if their shapes differ."""
    a, b = two
    for qi, (ga, gb) in enumerate(zip(a, b)):
        if shape(ga) != shape(gb):
            return ("shape", qi)
        for r, (ra, rb) in enumerate(zip(ga, gb)):
            for c, (x, y) in enumerate(zip(ra, rb)):
                if x != y:
                    return ("cell", qi, r, c)
    return None


def _ask_open(und) -> Optional[tuple]:
    """For undetermined hypotheses: the query cell left open by the most of them (its answer is a
    new demonstration cell, which can determine every cell with the same key); ``("shape", qi)``
    if a hypothesis cannot even give the output shape."""
    cnt: Counter = Counter()
    for h in und:
        if h[3] is None:
            return ("shape", 0)
        for qi, a in enumerate(h[3]):
            for r, row in enumerate(a):
                for c, v in enumerate(row):
                    if v is None:
                        cnt[(qi, r, c)] += 1
    if not cnt:
        return None
    (qi, r, c), _ = min(cnt.items(), key=lambda kv: (-kv[1], kv[0]))
    return ("cell", qi, r, c)

# =============================================================================================
# Stage 2: the ask loop (To Do 24) -- a simulated oracle answers the question the refusal names
# =============================================================================================


def ask_loop(search: Search, truth: Sequence, max_questions: int = 8,
             listen_from=AUTO, middle: bool = True) -> Dict[str, object]:
    """Decide in ``ask_mode``; on a refusal that names a question, ask the oracle (the true
    output) for it, add the answer as a demonstration cell (or an output shape), and decide again
    on the *same* search.  Stops when the planner answers, when no question can be asked, when a
    question repeats, or after ``max_questions``; then, if still refused, the plain (ladder)
    decision with the cells gathered so far is returned.  ``trace`` records, after each number of
    questions, the ask-mode decision and the plain decision."""
    truth = [G(t) for t in truth]
    extra: List[tuple] = []
    asked = 0
    trace = []
    while True:
        res = search.decide(listen_from, tuple(extra), middle, ask_mode=True)
        plain = search.decide(listen_from, tuple(extra), middle)
        trace.append((asked, res["status"], res.get("why"),
                      res["answer"] if res["status"] == "answered" else None,
                      plain["status"], plain["answer"] if plain["status"] == "answered" else None))
        if res["status"] == "answered" or res.get("ask") is None or asked >= max_questions:
            break
        q = res["ask"]
        if q[0] == "shape":
            qi = q[1]
            new = ("S", qi) + shape(truth[qi])
        else:
            _, qi, r, c = q
            t = truth[qi]
            if 0 <= r < len(t) and 0 <= c < len(t[0]):
                new = (qi, r, c, t[r][c])
            else:  # the named cell does not exist: the true shape answers the question
                new = ("S", qi) + shape(t)
        if new in extra:
            break
        asked += 1
        extra.append(new)
    if res["status"] != "answered":
        res = dict(plain, asked_mode_why=res.get("why"))
    res["questions"] = asked
    res["asked"] = list(extra)
    res["trace"] = trace
    return res


def solve(train, queries, max_depth=2, budget_s=30.0, listen_from=AUTO, prune=True,
          middle=True) -> Dict[str, object]:
    """One call: build the search and decide (no questions)."""
    return Search(train, queries, max_depth, budget_s, prune=prune).decide(listen_from,
                                                                            middle=middle)


def grid_text(g) -> str:
    return " / ".join("".join(str(v) for v in row) for row in g)


def induce_text(pairs, query) -> Tuple[bool, str, Dict[str, object]]:
    """GLM tool entry: decide (no oracle is available inside a tool call; a refusal names the
    question a user could answer)."""
    res = solve(pairs, [query])
    if res["status"] != "answered":
        ask = res.get("ask")
        q = "" if not ask else (" -- ask: output size" if ask[0] == "shape" else
                                " -- ask: cell (%d, %d)" % (ask[2], ask[3]))
        return False, "pipeline: refused (%s)%s" % (res["why"], q), dict(res, family="pipeline")
    return True, "pipeline: %s: %s" % (res["plan"], grid_text(res["answer"][0])), \
        dict(res, family="pipeline")


def arc_text(name: str) -> Tuple[bool, str, Dict[str, object]]:
    import json
    task = json.load(open(lri.arc_task_path(name)))
    train = [(p["input"], p["output"]) for p in task["train"]]
    res = solve(train, [p["input"] for p in task["test"]])
    if res["status"] != "answered":
        return False, "arc %s: pipeline refused (%s)" % (name, res["why"]), \
            dict(res, status="refused")
    right = all(a == p.get("output") for a, p in zip(res["answer"], task["test"]))
    return right, "arc %s: pipeline %s -- %s" % (name, res["plan"], "RIGHT" if right else "WRONG"), \
        dict(res, status="right" if right else "wrong")
