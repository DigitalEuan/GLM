#!/usr/bin/env python3
"""Round 29 benchmark: does a *pipeline* of steps solve puzzles that one step cannot?

Stand-alone (no GLM checkout needed); runs the planner module directly.  Three measurements:

A. **Stored ARC tasks** (the 50 tasks of ``arc_agi_17/data/training`` in ``glm_repo.zip``) at
   plan depth 0 (one fitted step: the Round 28 ladder plus the Round 29 finishers), 1, 2, 3.
   NOTE: these 50 tasks were looked at while the step alphabet was chosen, so this is a
   *development* score, not a held-out one.
B. **Round 28 local-rule puzzles** (B1 development and B2 held-out families of
   ``rule30_round28/r28_benchmark.py``, regenerated with the same generator and seeds).
C. **Multi-step puzzles**, 11 families each, 12 instances, 3 demonstrations and 1 query:
   9 families are compositions of 2 or 3 steps, 2 are CONTROLS that no plan in the alphabet
   expresses (the right result for a control is REFUSED).
   C1 (development): inspected while the planner was built (with other seeds).
   C2 (held-out): written after the planner was frozen and scored once; the planner's sha256
   is printed with the results.

Usage::

    python3 r29_benchmark.py [ARC_DIR] [--json out.json] [--quick]

Exact and deterministic (a fixed linear congruential generator; no randomness).
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time
from typing import Callable, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "glm_overlay", "glm_universal", "reasoning"))
sys.path.insert(0, os.path.join(HERE, "..", "rule30_round28", "glm_overlay", "glm_universal",
                                "reasoning"))
sys.path.insert(0, os.path.join(HERE, "..", "rule30_round28"))
import grid_planner as gp  # noqa: E402

Grid = List[List[int]]


class LCG:
    def __init__(self, seed: int):
        self.s = seed & 0xFFFFFFFF

    def next(self, n: int) -> int:
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return (self.s >> 8) % n


def L(g) -> Grid:
    return [list(r) for r in g]


# ---------------------------------------------------------------------------------------------
# C. held-out multi-step families (written after the planner was frozen; scored once)
# ---------------------------------------------------------------------------------------------

def one_object(g: LCG, cols=(1, 2, 3, 4)) -> Grid:
    """A background-0 grid with one multi-colour 8-connected blob."""
    H, W = 8 + g.next(4), 8 + g.next(4)
    h, w = 2 + g.next(3), 2 + g.next(3)
    r0, c0 = g.next(H - h), g.next(W - w)
    a = [[0] * W for _ in range(H)]
    for r in range(h):
        for c in range(w):
            if g.next(100) < 75 or (r, c) == (0, 0):
                a[r0 + r][c0 + c] = cols[g.next(len(cols))]
    # make it 8-connected: fill the first column and the first row of the blob
    for r in range(h):
        a[r0 + r][c0] = a[r0 + r][c0] or cols[0]
    for c in range(w):
        a[r0][c0 + c] = a[r0][c0 + c] or cols[0]
    return a


def small(g: LCG, cols=(0, 1, 2, 3), lo=3, hi=5) -> Grid:
    h, w = lo + g.next(hi - lo + 1), lo + g.next(hi - lo + 1)
    return [[cols[g.next(len(cols))] for _ in range(w)] for _ in range(h)]


def sparse(g: LCG, cols=(1, 2, 3), dens=30) -> Grid:
    h, w = 5 + g.next(4), 5 + g.next(4)
    return [[cols[g.next(len(cols))] if g.next(100) < dens else 0 for _ in range(w)]
            for _ in range(h)]


def recol(m):
    return lambda a: [[m.get(v, v) for v in r] for r in a]


def halves(g: LCG) -> Grid:
    h, w = 3 + g.next(3), 3 + g.next(3)
    A = [[1 if g.next(2) else 0 for _ in range(w)] for _ in range(h)]
    B = [[2 if g.next(2) else 0 for _ in range(w)] for _ in range(h)]
    return [ra + [5] + rb for ra, rb in zip(A, B)]


def halves_xor(a):
    w = (len(a[0]) - 1) // 2
    return [[3 if (r[c] != 0) != (r[w + 1 + c] != 0) else 0 for c in range(w)] for r in a]


def half_sym(g: LCG) -> Grid:
    """A left-right symmetric grid with some background holes punched in the right half."""
    h, w = 4 + g.next(3), 2 + g.next(3)
    left = [[1 + g.next(4) for _ in range(w)] for _ in range(h)]
    a = [r + list(reversed(r)) for r in left]
    for r in range(h):
        for c in range(w, 2 * w):
            if g.next(100) < 30:
                a[r][c] = 0
    return a


def complete_sym(a):
    return [[v if v else r[len(r) - 1 - c] for c, v in enumerate(r)] for r in a]


def objects(g: LCG) -> Grid:
    """Several single-colour (colour 1) objects of sizes 1..4 on background 0."""
    H, W = 8 + g.next(3), 8 + g.next(3)
    a = [[0] * W for _ in range(H)]
    for _ in range(4 + g.next(3)):
        n = 1 + g.next(4)
        r, c = g.next(H - 1), g.next(W - 4)
        if all(a[rr][cc] == 0 for rr in range(max(0, r - 1), min(H, r + 2))
               for cc in range(max(0, c - 1), min(W, c + n + 1))):
            for k in range(n):
                a[r][c + k] = 1
    return a


def obj_size_recolour(a):
    """Objects of size >= 3 become 2, smaller ones stay 1 (4-connected objects)."""
    out = [list(r) for r in a]
    for cp in gp.components(gp.G(a), 0, diag=False, by_colour=True):
        if len(cp) >= 3:
            for r, c in cp:
                out[r][c] = 2
    return out


def sort_rows(a):  # CONTROL
    return sorted((r[:] for r in a), key=lambda r: (sum(v != 0 for v in r), r))


def shift_rows_by_count(a):  # CONTROL
    k = sum(v != 0 for r in a for v in r) % len(a)
    return a[k:] + a[:k]


def comp(*fs):
    def f(a):
        for h in fs:
            a = L(h(gp.G(a)))
        return a
    return f

DEV29: List[Tuple[str, Callable, Callable, bool]] = [
    # name, input generator, rule, expressible?  (development: inspected while building)
    ("crop-flip", one_object, comp(gp.STEP_FN["crop_bbox"], gp.flip_h), True),
    ("mirror-recolour", lambda g: small(g), comp(gp.STEP_FN["mirror_v"],
                                                 recol({1: 6, 2: 7, 3: 8})), True),
    ("gravity-recolour", lambda g: sparse(g), comp(gp.STEP_FN["gravity_left"],
                                                   recol({1: 4, 2: 5, 3: 9})), True),
    ("rotate-upscale", lambda g: small(g, lo=2, hi=4), comp(gp.rot90, gp.STEP_FN["up2"]), True),
    ("crop-tile", one_object, comp(gp.STEP_FN["crop_bbox"], gp.STEP_FN["tile_2x2"]), True),
    ("halves-xor", halves, halves_xor, True),
    ("symfill-rotate", half_sym, comp(complete_sym, gp.STEP_FN["rot180"]), True),
    ("objsize-flip", objects, comp(gp.flip_v, obj_size_recolour), True),
    ("crop-rotate-recolour", one_object, comp(gp.STEP_FN["crop_bbox"], gp.rot90,
                                              recol({1: 7, 2: 8, 3: 9, 4: 6})), True),
    ("CONTROL-sort-rows", lambda g: sparse(g), sort_rows, False),
    ("CONTROL-shift-by-count", lambda g: sparse(g), shift_rows_by_count, False),
]


# Held-out families: written after the planner was frozen (planner v1, sha256 recorded in the
# output), never inspected before the single scoring run.
def frames(g: LCG) -> Grid:
    """One or two hollow rectangles (colour 3) on background 0."""
    H, W = 9 + g.next(3), 9 + g.next(3)
    a = [[0] * W for _ in range(H)]
    for _ in range(1 + g.next(2)):
        h, w = 3 + g.next(3), 3 + g.next(3)
        r0, c0 = g.next(H - h), g.next(W - w)
        if any(a[r][c] for r in range(r0, r0 + h) for c in range(c0, c0 + w)):
            continue
        for r in range(r0, r0 + h):
            for c in range(c0, c0 + w):
                if r in (r0, r0 + h - 1) or c in (c0, c0 + w - 1):
                    a[r][c] = 3
    if not any(any(r) for r in a):
        a[1][1:4] = [3, 3, 3]
        a[2][1], a[2][3] = 3, 3
        a[3][1:4] = [3, 3, 3]
    return a


def mono_objects(g: LCG) -> Grid:
    """Single-colour blobs of different sizes (colours 1, 2, 4) on background 0."""
    H, W = 9 + g.next(3), 9 + g.next(3)
    a = [[0] * W for _ in range(H)]
    sizes = [1, 2, 3]
    for k, col in enumerate((1, 2, 4)):
        s = sizes[(k + g.next(3)) % 3] + 1
        r0, c0 = g.next(H - s), g.next(W - s)
        for r in range(r0, r0 + s):
            for c in range(c0, c0 + s):
                if a[r][c] == 0 and (g.next(100) < 85 or (r, c) == (r0, c0)):
                    a[r][c] = col
    return a


def stacked_halves(g: LCG) -> Grid:
    h, w = 3 + g.next(3), 3 + g.next(3)
    A = [[6 if g.next(2) else 0 for _ in range(w)] for _ in range(h)]
    B = [[7 if g.next(2) else 0 for _ in range(w)] for _ in range(h)]
    return A + [[4] * w] + B


def halves_or_flip(a):
    h = (len(a) - 1) // 2
    out = [[2 if (a[r][c] != 0 or a[h + 1 + r][c] != 0) else 0 for c in range(len(a[0]))]
           for r in range(h)]
    return [list(reversed(r)) for r in out]


def fill_rot(a):
    f = gp.STEP_FN["fill_enclosed"](gp.G(a))
    f = f if f is not None else gp.G(a)
    return L(gp.rot90(gp.G([[6 if v == gp.SENTINEL else v for v in r] for r in f])))


def erase_isolated(a):
    H, W = len(a), len(a[0])
    return [[0 if a[r][c] and not any(0 <= r + dr < H and 0 <= c + dc < W and a[r + dr][c + dc]
                                      for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)
             else a[r][c] for c in range(W)] for r in range(H)]


def cyclic_shift(a):  # CONTROL
    return [r[1:] + r[:1] for r in a]


def sort_columns(a):  # CONTROL
    t = list(map(list, zip(*a)))
    t.sort(key=lambda col: (sum(v != 0 for v in col), col))
    return [list(r) for r in zip(*t)]


HELDOUT29: List[Tuple[str, Callable, Callable, bool]] = [
    ("crop-transpose", lambda g: one_object(g, (5, 6, 7, 8)),
     comp(gp.STEP_FN["crop_bbox"], gp.transpose), True),
    ("mirror-flip", lambda g: small(g, (0, 2, 5, 9)),
     comp(gp.STEP_FN["mirror_h"], gp.flip_v), True),
    ("gravity-up-crop", lambda g: sparse(g, (4, 6), 25),
     comp(gp.STEP_FN["gravity_up"], gp.STEP_FN["crop_bbox"]), True),
    ("upscale3-recolour", lambda g: small(g, (0, 1, 2), 2, 3),
     comp(gp.STEP_FN["up3"], recol({1: 8, 2: 3})), True),
    ("halves-or-flip", stacked_halves, halves_or_flip, True),
    ("fill-rotate", frames, fill_rot, True),
    ("largest-upscale", mono_objects,
     comp(gp.STEP_FN["crop_largest_mono"], gp.STEP_FN["up2"]), True),
    ("rot-crop-mirror", one_object,
     comp(gp.STEP_FN["rot180"], gp.STEP_FN["crop_bbox"], gp.STEP_FN["mirror_h"]), True),
    ("transpose-erase", lambda g: sparse(g, (2, 5), 25), comp(gp.transpose, erase_isolated), True),
    ("CONTROL-cyclic-shift", lambda g: sparse(g), cyclic_shift, False),
    ("CONTROL-sort-columns", lambda g: sparse(g), sort_columns, False),
]

INSTANCES = 12


def draw(g: LCG, gen, rule):
    """Draw inputs until the rule is defined on one (e.g. a unique largest object exists)."""
    for _ in range(100):
        a = gen(g)
        try:
            if rule(a) is not None:
                return a
        except TypeError:
            pass
    raise RuntimeError("generator: rule undefined on 100 draws")


def bench_families(families, seed_base: int, depth: int, budget: float):
    res = {}
    for fi, (name, gen, rule, _expr) in enumerate(families):
        tally = {"right": 0, "wrong": 0, "refused": 0}
        for i in range(INSTANCES):
            g = LCG(seed_base + 1000 * fi + i + 1)
            demos = [draw(g, gen, rule) for _ in range(3)]
            query = draw(g, gen, rule)
            train = [(d, L(rule(d))) for d in demos]
            r = gp.solve(train, [query], max_depth=depth, budget_s=budget)
            if r["status"] != "answered":
                tally["refused"] += 1
            elif r["answer"][0] == L(rule(query)):
                tally["right"] += 1
            else:
                tally["wrong"] += 1
        res[name] = tally
    return res


def _load_r28():
    """The Round 28 generator (same families and seeds), loaded without its GLM import."""
    import types
    path = os.path.join(HERE, "..", "rule30_round28", "r28_benchmark.py")
    src = open(path).read().replace(
        "from glm_universal.runtime.toolbox import run_tool  # noqa: E402", "run_tool = None")
    mod = types.ModuleType("r28_generator")
    exec(compile(src, path, "exec"), mod.__dict__)
    return mod


def bench_r28(depth: int, budget: float):
    r28 = _load_r28()
    out = {}
    for key, fams, base in (("B1", r28.FAMILIES, 0), ("B2", r28.HELDOUT, 50000)):
        fam = [(n, (lambda c, d: (lambda g: r28.rand_grid(g, c, d)))(cols, dens), f, loc)
               for n, f, cols, dens, loc in fams]
        res = {}
        for fi, (name, gen, rule, _l) in enumerate(fam):
            tally = {"right": 0, "wrong": 0, "refused": 0}
            for i in range(r28.INSTANCES):
                g = r28.LCG(base + 1000 * fi + i + 1)
                demos = [gen(g) for _ in range(3)]
                query = gen(g)
                r = gp.solve([(d, rule(d)) for d in demos], [query], max_depth=depth,
                             budget_s=budget)
                if r["status"] != "answered":
                    tally["refused"] += 1
                elif r["answer"][0] == rule(query):
                    tally["right"] += 1
                else:
                    tally["wrong"] += 1
            res[name] = tally
        out[key] = res
    return out


def bench_arc(arc_dir: str, depth: int, budget: float):
    files = sorted(glob.glob(os.path.join(arc_dir, "*.json")))
    tally = {"right": [], "wrong": [], "refused": 0}
    for f in files:
        task = json.load(open(f))
        r = gp.solve_task(task, max_depth=depth, budget_s=budget)
        if r["status"] != "answered":
            tally["refused"] += 1
            continue
        ok = all(a == p["output"] for a, p in zip(r["answer"], task["test"]))
        tally["right" if ok else "wrong"].append(os.path.basename(f)[:-5])
    return dict(tally, tasks=len(files))


def total(res):
    t = {"right": 0, "wrong": 0, "refused": 0}
    for v in res.values():
        for k in t:
            t[k] += v[k]
    return t


def show(title, res):
    print(title)
    for name, t in res.items():
        print("   %-24s RIGHT %2d  WRONG %2d  REFUSED %2d" % (name, t["right"], t["wrong"],
                                                            t["refused"]))
    t = total(res)
    print("   %-24s RIGHT %2d  WRONG %2d  REFUSED %2d" % ("TOTAL", t["right"], t["wrong"],
                                                        t["refused"]))


def main():
    pos = [a for i, a in enumerate(sys.argv[1:], 1)
           if not a.startswith("--") and not sys.argv[i - 1].startswith("--")]
    arc_dir = pos[0] if pos else os.environ.get("ARC_DIR", "arc_agi_17/data/training")
    depths = (0, 1, 2) if "--quick" in sys.argv else (0, 1, 2, 3)
    rep = {"arc": {}, "r28": {}, "dev29": {}, "heldout29": {}}
    import hashlib
    src = os.path.join(HERE, "glm_overlay", "glm_universal", "reasoning", "grid_planner.py")
    print("planner sha256:", hashlib.sha256(open(src, "rb").read()).hexdigest())
    t0 = time.time()
    for d in depths:
        rep["arc"][d] = bench_arc(arc_dir, d, 30.0)
        rep["r28"][d] = bench_r28(d, 10.0)
        rep["dev29"][d] = bench_families(DEV29, 290000, d, 10.0)
        rep["heldout29"][d] = bench_families(HELDOUT29, 291000, d, 10.0)
    for d in depths:
        a = rep["arc"][d]
        print("=== plan depth <= %d ===" % d)
        print("A. stored ARC tasks (%d, development): RIGHT %d  WRONG %d  REFUSED %d  right=%s" % (
            a["tasks"], len(a["right"]), len(a["wrong"]), a["refused"], a["right"]))
        if a["wrong"]:
            print("   wrong=%s" % a["wrong"])
        show("B1. Round 28 development local-rule puzzles", rep["r28"][d]["B1"])
        show("B2. Round 28 held-out local-rule puzzles", rep["r28"][d]["B2"])
        show("C1. Round 29 development multi-step puzzles", rep["dev29"][d])
        show("C2. Round 29 held-out multi-step puzzles", rep["heldout29"][d])
        print()
    print("(%.0f s)" % (time.time() - t0))
    if "--json" in sys.argv:
        json.dump(rep, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1,
                  default=str)


if __name__ == "__main__":
    main()
