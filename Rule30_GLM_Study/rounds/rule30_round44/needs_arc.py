#!/usr/bin/env python3
"""ARC-style grid puzzles for the needs wheel (Round 44).

A self-contained stand-in for ARC: puzzle FAMILIES generate demonstrations and a test pair
(input grid -> output grid, colours 0..9, 0 = background).  The solver is the Round 29/30 contract
in small: breadth-first programs of at most two steps over its primitive set, each step fitted to
the demonstrations; it answers only when every cheapest consistent program gives the same test
output, and refuses otherwise.

What is new is the NEEDS step.  When the solver refuses, it diagnoses — from the demonstrations
only, never from the family name — what kind of step is missing, after each transformation it
already has (so "flip, then something that moves cells down" is diagnosed as a missing mover).
The diagnosis is a list of `Need` objects with signatures such as `primitive:gravity` or
`primitive:fill-enclosed`.  The wheel holds provisions (new fitted primitives); a provision is
installed only if it serves a stated need.

Protocol (all measured, nothing proved):
  1. development set: run the base solver, collect its needs;
  2. freeze the requested provisions;
  3. score a fresh held-out set (different seed, more families, controls) under
       base / requested (from development) / all provisions / random same-size subsets /
       on-demand (per puzzle: refuse -> state needs -> load matching provisions -> retry).
The ground truth is the generator's test output.  New primitives are NOT sound provisions in the
sense of `NeedsWheel.lean`: they can create wrong answers through cheaper wrong programs, and the
measurement counts those.

Standard library only.
"""

from __future__ import annotations

import random
from collections import Counter
from typing import Callable, Optional

from glm_needs import Need

Grid = tuple  # tuple of row tuples


def G(rows) -> Grid:
    return tuple(tuple(r) for r in rows)


def shape(g: Grid):
    return (len(g), len(g[0]) if g else 0)


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Grid operations
# ─────────────────────────────────────────────────────────────────────────────────────────────

def flip_h(g): return G(r[::-1] for r in g)
def flip_v(g): return G(g[::-1])
def transpose(g): return G(zip(*g))
def rot90(g): return flip_h(transpose(g))
def rot180(g): return flip_v(flip_h(g))
def rot270(g): return transpose(flip_h(g))


def objects(g: Grid, diag: bool = False):
    """4-connected components of equal non-zero colour: list of (colour, cells)."""
    h, w = shape(g)
    seen = set()
    out = []
    for i in range(h):
        for j in range(w):
            if g[i][j] and (i, j) not in seen:
                c = g[i][j]
                stack, cells = [(i, j)], []
                seen.add((i, j))
                while stack:
                    a, b = stack.pop()
                    cells.append((a, b))
                    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        x, y = a + da, b + db
                        if 0 <= x < h and 0 <= y < w and (x, y) not in seen and g[x][y] == c:
                            seen.add((x, y))
                            stack.append((x, y))
                out.append((c, cells))
    return out


def gravity(g, d):
    """Non-zero cells fall in direction d (0 down, 1 up, 2 right, 3 left), keeping order."""
    if d == 0:
        return transpose(G([0] * (len(c) - len([x for x in c if x])) + [x for x in c if x]
                           for c in transpose(g)))
    if d == 1:
        return flip_v(gravity(flip_v(g), 0))
    if d == 2:
        return transpose(gravity(transpose(g), 0))
    return flip_h(gravity(flip_h(g), 2))


def border_bg(g):
    h, w = shape(g)
    seen = set()
    stack = [(i, j) for i in range(h) for j in range(w)
             if (i in (0, h - 1) or j in (0, w - 1)) and g[i][j] == 0]
    seen.update(stack)
    while stack:
        a, b = stack.pop()
        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            x, y = a + da, b + db
            if 0 <= x < h and 0 <= y < w and (x, y) not in seen and g[x][y] == 0:
                seen.add((x, y))
                stack.append((x, y))
    return seen


def fill_enclosed(g, c):
    h, w = shape(g)
    outside = border_bg(g)
    return G([c if g[i][j] == 0 and (i, j) not in outside else g[i][j] for j in range(w)]
             for i in range(h))


def scale(g, k):
    return G([x for x in r for _ in range(k)] for r in g for _ in range(k))


def tile(g, a, b):
    return G([x for _ in range(b) for x in r] for _ in range(a) for r in g)


def crop_largest(g):
    obs = objects(g)
    if not obs:
        return None
    best = max(obs, key=lambda o: len(o[1]))
    if sum(1 for o in obs if len(o[1]) == len(best[1])) > 1:
        return None
    rs = [a for a, _ in best[1]]
    cs = [b for _, b in best[1]]
    return G(r[min(cs):max(cs) + 1] for r in g[min(rs):max(rs) + 1])


def draw_lines(g):
    h, w = shape(g)
    out = [list(r) for r in g]
    for i in range(h):
        for j in range(w):
            c = g[i][j]
            if not c:
                continue
            for j2 in range(j + 1, w):
                if g[i][j2] == c:
                    for k in range(j + 1, j2):
                        if out[i][k] == 0:
                            out[i][k] = c
                    break
            for i2 in range(i + 1, h):
                if g[i2][j] == c:
                    for k in range(i + 1, i2):
                        if out[k][j] == 0:
                            out[k][j] = c
                    break
    return G(out)


def denoise(g):
    h, w = shape(g)
    out = [list(r) for r in g]
    for i in range(h):
        for j in range(w):
            if g[i][j] and all(not (0 <= i + a < h and 0 <= j + b < w) or g[i + a][j + b] == 0
                               for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[i][j] = 0
    return G(out)


def hollow(g):
    h, w = shape(g)
    return G([0 if 0 < i < h - 1 and 0 < j < w - 1 and g[i][j] and
              all(g[i + a][j + b] == g[i][j] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
              else g[i][j] for j in range(w)] for i in range(h))


def mirror_complete(g, axis):
    m = flip_h(g) if axis == 0 else flip_v(g)
    h, w = shape(g)
    return G([g[i][j] if g[i][j] else m[i][j] for j in range(w)] for i in range(h))


def count_bar(g):
    n = len(objects(g))
    return G([[1] * n]) if n else None


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Fitted steps: step.fit(pairs) -> params or None ; step.apply(grid, params) -> grid or None
# ─────────────────────────────────────────────────────────────────────────────────────────────

class Step:
    def __init__(self, name, apply, fit=None, cost=1):
        self.name, self._apply, self._fit, self.cost = name, apply, fit, cost

    def fit(self, pairs):
        if self._fit is None:
            return ()
        return self._fit(pairs)

    def apply(self, g, params):
        if g is None:
            return None
        try:
            return self._apply(g, params) if self._fit else self._apply(g)
        except (IndexError, ValueError, ZeroDivisionError):
            return None


def fit_colour_map(pairs):
    m = {}
    for a, b in pairs:
        if a is None or shape(a) != shape(b):
            return None
        for ra, rb in zip(a, b):
            for x, y in zip(ra, rb):
                if m.setdefault(x, y) != y:
                    return None
    if all(k == v for k, v in m.items()):
        return None   # identity map: not a step
    return m


def apply_colour_map(g, m):
    if any(x not in m for r in g for x in r):
        return None
    return G([m[x] for x in r] for r in g)


def fit_fill(pairs):
    cs = set()
    for a, b in pairs:
        if a is None or shape(a) != shape(b):
            return None
        for ra, rb in zip(a, b):
            for x, y in zip(ra, rb):
                if x != y:
                    if x != 0:
                        return None
                    cs.add(y)
    return cs.pop() if len(cs) == 1 else None


def fit_scale(pairs):
    ks = set()
    for a, b in pairs:
        if a is None:
            return None
        (h, w), (H, W) = shape(a), shape(b)
        if h == 0 or H % h or W % w or H // h != W // w or H // h < 2:
            return None
        ks.add(H // h)
    return ks.pop() if len(ks) == 1 else None


def fit_tile(pairs):
    ks = set()
    for a, b in pairs:
        if a is None:
            return None
        (h, w), (H, W) = shape(a), shape(b)
        if h == 0 or H % h or W % w or (H // h, W // w) == (1, 1):
            return None
        ks.add((H // h, W // w))
    return ks.pop() if len(ks) == 1 else None


def fit_size_map(pairs):
    m = {}
    for a, b in pairs:
        if a is None or shape(a) != shape(b):
            return None
        for c, cells in objects(a):
            cols = {b[i][j] for i, j in cells}
            if len(cols) != 1:
                return None
            y = cols.pop()
            if m.setdefault(len(cells), y) != y:
                return None
        for i, r in enumerate(a):
            for j, x in enumerate(r):
                if x == 0 and b[i][j] != 0:
                    return None
    return m or None


def apply_size_map(g, m):
    out = [list(r) for r in g]
    for c, cells in objects(g):
        if len(cells) not in m:
            return None
        for i, j in cells:
            out[i][j] = m[len(cells)]
    return G(out)


def _obj_features(g, cells):
    h, w = shape(g)
    rs = [a for a, _ in cells]
    cs = [b for _, b in cells]
    top, left = min(rs), min(cs)
    norm = tuple(sorted((a - top, b - left) for a, b in cells))
    bh, bw = max(rs) - top + 1, max(cs) - left + 1
    return {
        "size": len(cells),
        "height": bh,
        "width": bw,
        "border": any(a in (0, h - 1) or b in (0, w - 1) for a, b in cells),
        "shape": norm,
        "solid": len(cells) == bh * bw,
        **{f"size>={k}": len(cells) >= k for k in range(2, 9)},
    }


FEATURES = ["size", "height", "width", "border", "shape", "solid"] + [f"size>={k}" for k in range(2, 9)] + \
    ["largest", "smallest"]


def _features_all(g):
    obs = objects(g)
    if not obs:
        return []
    sizes = [len(c) for _, c in obs]
    out = []
    for (col, cells) in obs:
        f = _obj_features(g, cells)
        f["largest"] = len(cells) == max(sizes)
        f["smallest"] = len(cells) == min(sizes)
        out.append((col, cells, f))
    return out


def fit_feature_map(pairs):
    """Recolour each object by one of its features: feature value -> colour, or 'keep'."""
    for feat in FEATURES:
        m = {}
        ok = True
        for a, b in pairs:
            if a is None or shape(a) != shape(b):
                return None
            for i, r in enumerate(a):
                for j, x in enumerate(r):
                    if x == 0 and b[i][j] != 0:
                        return None
            for col, cells, f in _features_all(a):
                outs = {b[i][j] for i, j in cells}
                if len(outs) != 1:
                    return None
                y = outs.pop()
                y = "keep" if y == col else y
                if m.setdefault(f[feat], y) != y:
                    ok = False
                    break
            if not ok:
                break
        if ok and m and any(v != "keep" for v in m.values()):
            return (feat, m)
    return None


def apply_feature_map(g, params):
    feat, m = params
    out = [list(r) for r in g]
    for col, cells, f in _features_all(g):
        if f[feat] not in m:
            return None
        y = m[f[feat]]
        for i, j in cells:
            out[i][j] = col if y == "keep" else y
    return G(out)


BASE_STEPS = [
    Step("flip_h", flip_h), Step("flip_v", flip_v), Step("transpose", transpose),
    Step("rot90", rot90), Step("rot180", rot180), Step("rot270", rot270),
    Step("colour_map", apply_colour_map, fit_colour_map),
]

PROVISION_STEPS = {
    "gravity_down": (Step("gravity_down", lambda g: gravity(g, 0)), ["primitive:gravity-down"]),
    "gravity_up": (Step("gravity_up", lambda g: gravity(g, 1)), ["primitive:gravity-up"]),
    "gravity_right": (Step("gravity_right", lambda g: gravity(g, 2)), ["primitive:gravity-right"]),
    "gravity_left": (Step("gravity_left", lambda g: gravity(g, 3)), ["primitive:gravity-left"]),
    "fill_enclosed": (Step("fill_enclosed", fill_enclosed, fit_fill), ["primitive:fill-enclosed"]),
    "scale": (Step("scale", scale, fit_scale), ["primitive:scale"]),
    "tile": (Step("tile", lambda g, p: tile(g, *p), fit_tile), ["primitive:tile"]),
    "crop_largest": (Step("crop_largest", crop_largest), ["primitive:crop"]),
    "count_bar": (Step("count_bar", count_bar), ["primitive:count"]),
    "draw_lines": (Step("draw_lines", draw_lines), ["primitive:connect"]),
    "denoise": (Step("denoise", denoise), ["primitive:remove-isolated"]),
    "hollow": (Step("hollow", hollow), ["primitive:hollow"]),
    "mirror_h": (Step("mirror_h", lambda g: mirror_complete(g, 0)), ["primitive:mirror-h"]),
    "mirror_v": (Step("mirror_v", lambda g: mirror_complete(g, 1)), ["primitive:mirror-v"]),
    "recolour_by_size": (Step("recolour_by_size", apply_size_map, fit_size_map),
                         ["primitive:recolour-objectwise"]),
}

# Round 44, second loop: provided after the real-ARC run stated `recolour-objectwise` as its most
# frequent specific need and `recolour_by_size` met none of those requests.
PROVISION_STEPS_V2 = dict(PROVISION_STEPS)
PROVISION_STEPS_V2["recolour_by_feature"] = (Step("recolour_by_feature", apply_feature_map, fit_feature_map),
                                             ["primitive:recolour-objectwise"])


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Solver
# ─────────────────────────────────────────────────────────────────────────────────────────────

def solve(demos, test_in, steps):
    """Programs of depth 0..2; answer iff all consistent programs of least depth agree."""
    ins = [a for a, _ in demos]
    outs = [b for _, b in demos]
    if all(a == b for a, b in demos):
        return test_in, ["identity"]
    for depth in (1, 2):
        answers = {}
        progs = [[s] for s in steps] if depth == 1 else [[s, t] for s in steps for t in steps]
        for prog in progs:
            cur, cur_t = list(ins), test_in
            ok = True
            names = []
            for k, st in enumerate(prog):
                if k < len(prog) - 1:
                    params = st.fit(list(zip(cur, outs))) if st._fit is None else None
                    if st._fit is not None:
                        # middle fitted steps are not identifiable from the outputs: skip
                        ok = False
                        break
                    cur = [st.apply(g, ()) for g in cur]
                    cur_t = st.apply(cur_t, ())
                else:
                    params = st.fit(list(zip(cur, outs)))
                    if params is None:
                        ok = False
                        break
                    cur = [st.apply(g, params) for g in cur]
                    cur_t = st.apply(cur_t, params)
                names.append(st.name)
                if any(g is None for g in cur):
                    ok = False
                    break
            if ok and cur == outs and cur_t is not None:
                answers.setdefault(cur_t, []).append("+".join(names))
        if answers:
            if len(answers) == 1:
                (ans, progs_), = answers.items()
                return ans, progs_
            return None, ["ambiguous: " + str(sorted(p for v in answers.values() for p in v))[:200]]
    return None, []


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Needs diagnosis (from demonstrations only)
# ─────────────────────────────────────────────────────────────────────────────────────────────

def packed(b, d):
    """Output feature: in every column (d = 0 down, 1 up) or row (2 right, 3 left) the non-zero
    cells are contiguous against that edge."""
    lines = transpose(b) if d in (0, 1) else b
    for ln in lines:
        seq = list(ln) if d in (0, 2) else list(ln)[::-1]
        k = len(seq) - sum(1 for x in seq if x)
        if any(seq[:k]) or not all(seq[k:]):
            return False
    return True


def residual_candidates(a, b):
    """Which kinds of step could turn a into b?  A set of signatures (possibly empty), using only
    features of the pair: shapes, which cells change, and the structure of the output."""
    if a is None:
        return set()
    (h, w), (H, W) = shape(a), shape(b)
    out = set()
    if (H, W) != (h, w):
        if H >= h and W >= w and H % h == 0 and W % w == 0:
            k, l = H // h, W // w
            if k == l and all(b[i][j] == b[i - i % k][j - j % k] for i in range(H) for j in range(W)):
                out.add("primitive:scale")
            if all(b[i][j] == b[i % h][j % w] for i in range(H) for j in range(W)):
                out.add("primitive:tile")
        elif H <= h and W <= w:
            if H == 1 and len({x for x in b[0]}) == 1:
                out.add("primitive:count")
            subs = {G(r[j:j + W] for r in a[i:i + H]) for i in range(h - H + 1) for j in range(w - W + 1)}
            if b in subs:
                out.add("primitive:crop")
        return out
    changed = [(i, j) for i in range(h) for j in range(w) if a[i][j] != b[i][j]]
    if not changed:
        return {"same"}
    if all(a[i][j] == 0 for i, j in changed):          # only additions
        outside = border_bg(a)
        if all((i, j) not in outside for i, j in changed):
            out.add("primitive:fill-enclosed")
        if b == flip_h(b):
            out.add("primitive:mirror-h")
        if b == flip_v(b):
            out.add("primitive:mirror-v")

        def between(i, j):
            c = b[i][j]
            row = a[i]
            col = [a[k][j] for k in range(h)]
            return (c in row[:j] and c in row[j + 1:]) or (c in col[:i] and c in col[i + 1:])
        if all(between(i, j) for i, j in changed):
            out.add("primitive:connect")
    elif all(b[i][j] == 0 for i, j in changed):         # only removals
        def isolated(i, j):
            return all(not (0 <= i + x < h and 0 <= j + y < w) or a[i + x][j + y] == 0
                       for x, y in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if all(isolated(i, j) for i, j in changed):
            out.add("primitive:remove-isolated")
        if all(0 < i < h - 1 and 0 < j < w - 1 for i, j in changed):
            out.add("primitive:hollow")
    elif all(a[i][j] != 0 and b[i][j] != 0 for i, j in changed):   # recolouring only
        out.add("primitive:recolour-objectwise")
    if Counter(x for r in a for x in r if x) == Counter(x for r in b for x in r if x):
        for d, name in enumerate(("down", "up", "right", "left")):
            if packed(b, d):
                out.add(f"primitive:gravity-{name}")
    return out


def diagnose(demos, base_steps):
    """Needs stated by the solver.  For each transformation it already has (and the identity), the
    kinds of step that could explain EVERY demonstration after it (intersection over the
    demonstrations).  If nothing is common, it says so ("primitive:unknown") instead of guessing."""
    pre = [("identity", lambda g: g)] + [(s.name, (lambda s: lambda g: s.apply(g, ()))(s))
                                         for s in base_steps if s._fit is None]
    found = {}
    for name, f in pre:
        common = None
        for a, b in demos:
            c = residual_candidates(f(a), b)
            common = c if common is None else common & c
        for sig in sorted(common or ()):
            if sig != "same":
                found.setdefault(sig, []).append(name)
    if not found:
        a, b = demos[0]
        return [Need("primitive", "primitive:unknown", "no kind of step is common to all "
                     f"demonstrations (shape {shape(a)} -> {shape(b)})", [], "none: report as a gap")]
    return [Need("primitive", sig, f"after {', '.join(sorted(set(names)))[:60]} every demonstration "
                 f"needs a step of kind '{sig.split(':')[1]}'", [], "the held-out puzzles that "
                 "need it are answered") for sig, names in sorted(found.items())]


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Puzzle families
# ─────────────────────────────────────────────────────────────────────────────────────────────

def rand_grid(rng, h, w, density=0.35, colours=(1, 2, 3, 4, 5)):
    return G([rng.choice(colours) if rng.random() < density else 0 for _ in range(w)]
             for _ in range(h))


def rand_objects_grid(rng, h, w, n_obj, colours=(1, 2, 3, 4, 5, 6)):
    g = [[0] * w for _ in range(h)]
    for _ in range(n_obj):
        c = rng.choice(colours)
        oh, ow = rng.randint(1, 3), rng.randint(1, 3)
        i, j = rng.randint(0, h - oh), rng.randint(0, w - ow)
        for a in range(i, i + oh):
            for b in range(j, j + ow):
                g[a][b] = c
    return G(g)


def boxes_grid(rng, h, w):
    g = [[0] * w for _ in range(h)]
    c = rng.choice((1, 2, 3, 5))
    for _ in range(rng.randint(1, 2)):
        bh, bw = rng.randint(3, 5), rng.randint(3, 5)
        i, j = rng.randint(0, h - bh), rng.randint(0, w - bw)
        for a in range(i, i + bh):
            for b in range(j, j + bw):
                if a in (i, i + bh - 1) or b in (j, j + bw - 1):
                    g[a][b] = c
    return G(g)


def pairs_grid(rng, h, w):
    g = [[0] * w for _ in range(h)]
    for _ in range(rng.randint(1, 3)):
        c = rng.choice((1, 2, 3, 4))
        if rng.random() < 0.5:
            i = rng.randrange(h)
            j1, j2 = sorted(rng.sample(range(w), 2))
            g[i][j1] = g[i][j2] = c
        else:
            j = rng.randrange(w)
            i1, i2 = sorted(rng.sample(range(h), 2))
            g[i1][j] = g[i2][j] = c
    return G(g)


def noisy_blocks(rng, h, w):
    g = [list(r) for r in rand_objects_grid(rng, h, w, 2)]
    for _ in range(rng.randint(2, 4)):
        i, j = rng.randrange(h), rng.randrange(w)
        if all(not (0 <= i + a < h and 0 <= j + b < w) or g[i + a][j + b] == 0
               for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0))):
            g[i][j] = rng.choice((7, 8, 9))
    return G(g)


def solid_blocks(rng, h, w):
    g = [[0] * w for _ in range(h)]
    c = rng.choice((1, 2, 3, 4))
    bh, bw = rng.randint(3, h - 1), rng.randint(3, w - 1)
    i, j = rng.randint(0, h - bh), rng.randint(0, w - bw)
    for a in range(i, i + bh):
        for b in range(j, j + bw):
            g[a][b] = c
    return G(g)


def half_sym(rng, h, w):
    g = [list(r) for r in rand_grid(rng, h, w, 0.5)]
    full = [r[:w // 2] + r[:w // 2][::-1] for r in g]
    for _ in range(rng.randint(2, 5)):
        i, j = rng.randrange(h), rng.randrange(w)
        full[i][j] = 0
    return G(full)


def sized_objects(rng, h, w):
    g = [[0] * w for _ in range(h)]
    for k, size in enumerate(rng.sample([1, 2, 3, 4], 3)):
        for _ in range(10):
            i, j = rng.randrange(h), rng.randrange(w - size + 1)
            if all(g[i][j + t] == 0 for t in range(size)) and \
               all(g[a][b] == 0 for a in range(max(0, i - 1), min(h, i + 2))
                   for b in range(max(0, j - 1), min(w, j + size + 1))):
                for t in range(size):
                    g[i][j + t] = 5
                break
    return G(g)


SIZE_COLOURS = {1: 1, 2: 2, 3: 3, 4: 4}

# family name -> (input generator, transformation)
FAMILIES = {
    "flip_h": (lambda r: rand_grid(r, r.randint(3, 6), r.randint(3, 6)), flip_h),
    "rot90": (lambda r: rand_grid(r, r.randint(3, 6), r.randint(3, 6)), rot90),
    "recolour": (lambda r: rand_grid(r, r.randint(3, 6), r.randint(3, 6), colours=(1, 2, 3)),
                 lambda g: G([{0: 0, 1: 4, 2: 5, 3: 6}[x] for x in row] for row in g)),
    "gravity_down": (lambda r: rand_grid(r, r.randint(4, 7), r.randint(3, 6)), lambda g: gravity(g, 0)),
    "flip_gravity": (lambda r: rand_grid(r, r.randint(4, 7), r.randint(3, 6)), lambda g: gravity(flip_h(g), 0)),
    "gravity_left": (lambda r: rand_grid(r, r.randint(3, 6), r.randint(4, 7)), lambda g: gravity(g, 3)),
    "fill_enclosed": (lambda r: boxes_grid(r, r.randint(6, 9), r.randint(6, 9)), lambda g: fill_enclosed(g, 4)),
    "scale2": (lambda r: rand_grid(r, r.randint(2, 4), r.randint(2, 4)), lambda g: scale(g, 2)),
    "scale3_flip": (lambda r: rand_grid(r, r.randint(2, 3), r.randint(2, 3)), lambda g: scale(flip_v(g), 3)),
    "tile2x2": (lambda r: rand_grid(r, r.randint(2, 4), r.randint(2, 4)), lambda g: tile(g, 2, 2)),
    "crop_largest": (lambda r: rand_objects_grid(r, 8, 8, 3), crop_largest),
    "connect": (lambda r: pairs_grid(r, r.randint(5, 8), r.randint(5, 8)), draw_lines),
    "denoise": (lambda r: noisy_blocks(r, 7, 7), denoise),
    "mirror_complete": (lambda r: half_sym(r, r.randint(3, 6), 2 * r.randint(2, 4)), lambda g: mirror_complete(g, 0)),
    "recolour_by_size": (lambda r: sized_objects(r, 7, 8), lambda g: apply_size_map(g, SIZE_COLOURS)),
    "hollow": (lambda r: solid_blocks(r, 7, 7), hollow),
    "count_bar": (lambda r: rand_objects_grid(r, 7, 7, r.randint(1, 4)), count_bar),
    "rot90_tile": (lambda r: rand_grid(r, 2, 3), lambda g: tile(rot90(g), 1, 2)),
    # controls: no primitive explains these
    "control_shuffle": (lambda r: rand_grid(r, 4, 4), None),
    "control_parity": (lambda r: rand_grid(r, 4, 5), lambda g: G([[(sum(1 for x in row if x) + j) % 2 for j in range(len(row))] for row in g])),
}

DEV_FAMILIES = ["flip_h", "rot90", "recolour", "gravity_down", "fill_enclosed", "scale2",
                "crop_largest", "connect", "denoise", "mirror_complete", "control_shuffle"]
HELDOUT_FAMILIES = list(FAMILIES)  # every family, including ones never seen in development


def make_puzzle(rng, fam, n_demo=3):
    gen, f = FAMILIES[fam]
    for _ in range(200):
        pairs = []
        for _ in range(n_demo + 1):
            a = gen(rng)
            if f is None:
                b = rand_grid(rng, *shape(a))
            else:
                b = f(a)
            if b is None or a == b:
                break
            pairs.append((a, b))
        if len(pairs) == n_demo + 1:
            return {"family": fam, "demos": pairs[:-1], "test_in": pairs[-1][0], "test_out": pairs[-1][1]}
    raise RuntimeError(f"could not generate {fam}")


def make_set(seed, families, per_family):
    rng = random.Random(seed)
    return [make_puzzle(rng, fam) for fam in families for _ in range(per_family)]


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Measurement
# ─────────────────────────────────────────────────────────────────────────────────────────────

def provisions_for(needs):
    sigs = {n.signature for n in needs}
    return [name for name, (_, serves) in PROVISION_STEPS.items() if any(s in sigs for s in serves)]


def steps_with(names):
    return BASE_STEPS + [PROVISION_STEPS[n][0] for n in names]


def score_set(puzzles, steps):
    import time as _t
    t0 = _t.time()
    out = {"right": 0, "wrong": 0, "refused": 0}
    per_family = {}
    for p in puzzles:
        ans, _ = solve(p["demos"], p["test_in"], steps)
        k = "refused" if ans is None else ("right" if ans == p["test_out"] else "wrong")
        out[k] += 1
        per_family.setdefault(p["family"], Counter())[k] += 1
    out["n"] = len(puzzles)
    out["primitives"] = len(steps)
    out["seconds"] = round(_t.time() - t0, 2)
    return out, {f: dict(c) for f, c in per_family.items()}


def on_demand(puzzles):
    """Per puzzle: base solver; if it refuses, state needs, load matching provisions, retry."""
    out = {"right": 0, "wrong": 0, "refused": 0, "loads": 0}
    for p in puzzles:
        ans, _ = solve(p["demos"], p["test_in"], BASE_STEPS)
        if ans is None:
            names = provisions_for(diagnose(p["demos"], BASE_STEPS))
            out["loads"] += len(names)
            if names:
                ans, _ = solve(p["demos"], p["test_in"], steps_with(names))
        k = "refused" if ans is None else ("right" if ans == p["test_out"] else "wrong")
        out[k] += 1
    out["n"] = len(puzzles)
    return out


def run(dev_seed=2044, heldout_seed=4402, dev_per=4, held_per=6, random_draws=5):
    dev = make_set(dev_seed, DEV_FAMILIES, dev_per)
    held = make_set(heldout_seed, HELDOUT_FAMILIES, held_per)
    # 1. development: base solver, needs from refusals
    dev_needs = []
    dev_base, _ = score_set(dev, BASE_STEPS)
    need_log = []
    for p in dev:
        ans, _ = solve(p["demos"], p["test_in"], BASE_STEPS)
        if ans is None:
            ns = diagnose(p["demos"], BASE_STEPS)
            dev_needs += ns
            need_log.append({"family": p["family"], "needs": [n.signature for n in ns],
                             "because": [n.because for n in ns]})
    sig_counts = Counter(n.signature for n in dev_needs)
    requested = provisions_for(dev_needs)
    # 2. held-out scoring under the conditions
    res = {}
    res["base (no wheel)"] = score_set(held, BASE_STEPS)
    res["requested (from development needs)"] = score_set(held, steps_with(requested))
    res["all provisions"] = score_set(held, steps_with(list(PROVISION_STEPS)))
    rng = random.Random(7)
    draws = []
    for _ in range(random_draws):
        names = rng.sample(list(PROVISION_STEPS), len(requested))
        draws.append({"provisions": names, "score": score_set(held, steps_with(names))[0]})
    res["random same-size"] = draws
    res["on-demand (per-puzzle needs)"] = on_demand(held)
    # diagnosis accuracy on held-out refusals: does the stated need match a provision that solves it?
    diag = {"refused_by_base": 0, "need_stated": 0, "unknown": 0, "need_served_and_solved": 0}
    for p in held:
        ans, _ = solve(p["demos"], p["test_in"], BASE_STEPS)
        if ans is None:
            diag["refused_by_base"] += 1
            ns = diagnose(p["demos"], BASE_STEPS)
            if any(n.signature == "primitive:unknown" for n in ns):
                diag["unknown"] += 1
            else:
                diag["need_stated"] += 1
                names = provisions_for(ns)
                a2, _ = solve(p["demos"], p["test_in"], steps_with(names))
                if a2 == p["test_out"]:
                    diag["need_served_and_solved"] += 1
    return {"dev_size": len(dev), "heldout_size": len(held), "dev_base": dev_base,
            "dev_need_counts": dict(sig_counts), "dev_need_log": need_log,
            "requested": requested, "conditions": res, "diagnosis": diag}


if __name__ == "__main__":
    import json
    import time
    t0 = time.time()
    r = run()
    print(json.dumps({k: v for k, v in r.items() if k != "dev_need_log"}, indent=1, default=str)[:6000])
    print("seconds", round(time.time() - t0, 1))
