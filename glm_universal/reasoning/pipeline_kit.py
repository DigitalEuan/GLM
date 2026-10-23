"""``glm_universal.reasoning.pipeline_kit`` -- rule induction from
demonstrations, with an agreement gate (Phase 175).

*Created 21 October 2026.* *Last altered 21 October 2026 (Phase 176: an
ambiguous refusal names the input to ask about, ``reasoning/pipeline_ask.py``).*

Where it comes from
-------------------
The owner's 9-iteration pipeline study (``source_material/GLM_Pipeline_Kit/``,
its ``README.md`` and ``FINDINGS.md``) ended in a small solver: a task is a
handful of demonstration pairs ``(input grid, output grid)``; every operator
hypothesis consistent with all of them is kept "in superposition"; the query
is answered only when every surviving hypothesis gives it the same output.
The kit solved toggle, translate and reflect and left two families open,
``flood_fill`` and ``bfs_shortest``.  This module is that solver brought into
the GLM, with three additions, and with the kit's measuring step read off the
GLM's own substrate (:mod:`glm_universal.substrate.leech2`) instead of the
kit's private copy of the Golay code:

* **two new single-step operators** -- the region fill (every empty cell not
  connected to the border through empty cells is filled) and the two-point
  path writer (vertical leg then horizontal, or horizontal then vertical,
  from the first set cell in reading order) -- the kit's two open items;
* **task steps**: when no single operator fits, every composition of two is
  searched (a bounded loop, deepened only on failure), together with "a cell
  permutation, then a constant XOR mask";
* **a layer filter** from the kit's ``wt_comp_perm``: a cell permutation keeps
  a grid's weight, so when a demonstration changes the weight no permutation
  is tried, and the count of hypotheses skipped is reported.

The hypotheses are tried in **tiers** -- single operators, then two-step
compositions, then a cell permutation learnt cell by cell from the
demonstrations -- and the first tier with a consistent member is read.  That
is exactly ``GLM.PipelineInduction.solve``
(``RequestProject/GLM/PipelineInduction.lean``): its answer is the true rule's
whenever the true rule lies in the tier it read (``solve_sound``), it refuses
exactly when that tier disagrees (``solve_refuses_disagreement``), and it
never gives an answer no consistent hypothesis gave
(``solve_never_invents``).

Nothing here is specific to puzzles.  A "grid" of one row is a bit string,
so the same solver induces string rules (reverse, rotate, complement and
their compositions) from examples; what it needs is only a finite operator
vocabulary and examples to filter it.

Exactness
---------
Integers and tuples only.  The task samples come from a fixed integer
recurrence (:class:`Stream`), not a random source, so every run reproduces
the last.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "KIT_LEAN_FILES", "Grid", "Stream",
    "parse_grid", "grid_text", "flatten", "unflatten", "grid_to_word",
    "permutation_library", "permute", "fill_enclosed", "path_vh", "path_hv",
    "single_operators", "Hypothesis", "tiers_for", "solve", "measure",
    "induce_text", "check_substrate", "threshold_analogy", "parity_analogy",
    "FAMILIES", "sample",
]

LEAN_FILE = "RequestProject/GLM/PipelineInduction.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "truth_consistent", "consistent_of_subset", "agree_sound",
    "ambiguous_forces_refusal", "mem_consistentIn", "consistentIn_more_demos",
    "collapse_some", "collapse_some_of_agree", "collapse_none_of_disagree",
    "mem_selectTier", "selectTier_append", "solve_sound",
    "solve_refuses_disagreement", "solve_answers_agreement",
    "solve_never_invents", "solve_none_of_unfit", "perm_toggle_layer")

#: The kit's seven Lean files, brought in unchanged but for their imports.
KIT_LEAN_FILES: Tuple[str, ...] = tuple(
    f"RequestProject/GLM/PipelineKit/{n}.lean" for n in (
        "Golay", "Leech", "Lattices", "Pless", "Fields", "Analogy",
        "Permutation"))

Grid = Tuple[Tuple[int, ...], ...]


# ── grids ──────────────────────────────────────────────────────────────────

def parse_grid(text: str) -> Optional[Grid]:
    """``0110/1001`` (rows split by ``/``) or ``0110`` (one row); ``None``
    if the text is not a rectangular grid of 0s and 1s."""
    rows = [r.strip() for r in text.strip().split("/")]
    if not rows or any(not r or set(r) - {"0", "1"} for r in rows):
        return None
    if len({len(r) for r in rows}) != 1:
        return None
    return tuple(tuple(int(c) for c in r) for r in rows)


def grid_text(g: Grid) -> str:
    return "/".join("".join(str(v) for v in row) for row in g)


def flatten(g: Grid) -> Tuple[int, ...]:
    return tuple(v for row in g for v in row)


def unflatten(cells: Sequence[int], w: int) -> Grid:
    return tuple(tuple(cells[r * w:(r + 1) * w]) for r in range(len(cells) // w))


def grid_to_word(g: Grid) -> int:
    """Row-major, first cell the highest bit (the study scripts' convention)."""
    word = 0
    for v in flatten(g):
        word = (word << 1) | (v & 1)
    return word


# ── operators ──────────────────────────────────────────────────────────────

def permute(cells: Sequence[int], perm: Sequence[int]) -> Tuple[int, ...]:
    """``out[i] = cells[perm[i]]`` -- the kit's ``permute_op``."""
    return tuple(cells[p] for p in perm)


def _shift(h: int, w: int, dy: int, dx: int, rows: int) -> List[int]:
    out = []
    for r in range(h):
        for c in range(w):
            out.append(((r - dy) % rows) * w + (c - dx) % w if r < rows
                       else r * w + c)
    return out


def permutation_library(h: int, w: int, kit_only: bool = False
                        ) -> Dict[str, List[int]]:
    """The cell permutations tried: the kit's library (identity, the three
    mirrors, cyclic shifts by up to two cells, the same shifts keeping the
    last row), and -- unless ``kit_only`` -- the transpose and the two
    quarter-turns of a square grid."""
    lib: Dict[str, List[int]] = {
        "identity": list(range(h * w)),
        "reflect_v": [r * w + (w - 1 - c) for r in range(h) for c in range(w)],
        "reflect_h": [(h - 1 - r) * w + c for r in range(h) for c in range(w)],
        "rotate180": [(h - 1 - r) * w + (w - 1 - c)
                      for r in range(h) for c in range(w)],
    }
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if (dy, dx) == (0, 0) or (h == 1 and dy != 0):
                continue
            lib[f"shift({dy},{dx})"] = _shift(h, w, dy, dx, h)
            if h >= 2:
                lib[f"shift({dy},{dx})_keep_last_row"] = _shift(h, w, dy, dx,
                                                                h - 1)
    if not kit_only and h == w:
        lib["transpose"] = [c * w + r for r in range(h) for c in range(w)]
        lib["rotate90"] = [(h - 1 - c) * w + r for r in range(h) for c in range(w)]
        lib["rotate270"] = [c * w + (w - 1 - r) for r in range(h) for c in range(w)]
    return lib


def fill_enclosed(g: Grid) -> Grid:
    """Fill every empty cell not 4-connected to the border through empty
    cells (the closure of a boundary; the kit's open ``flood_fill``)."""
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    stack = [(r, c) for r in range(h) for c in range(w)
             if (r in (0, h - 1) or c in (0, w - 1)) and g[r][c] == 0]
    for r, c in stack:
        seen[r][c] = True
    while stack:
        r, c = stack.pop()
        for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= rr < h and 0 <= cc < w and not seen[rr][cc] \
                    and g[rr][cc] == 0:
                seen[rr][cc] = True
                stack.append((rr, cc))
    return tuple(tuple(1 if g[r][c] or not seen[r][c] else 0
                       for c in range(w)) for r in range(h))


def _two_cells(g: Grid) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
    cells = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v]
    return (cells[0], cells[1]) if len(cells) == 2 else None


def _path(g: Grid, vertical_first: bool) -> Optional[Grid]:
    ends = _two_cells(g)
    if ends is None:
        return None
    (r, c), (r2, c2) = ends
    out = [list(row) for row in g]
    legs = ("v", "h") if vertical_first else ("h", "v")
    for leg in legs:
        if leg == "v":
            while r != r2:
                r += 1 if r2 > r else -1
                out[r][c] = 1
        else:
            while c != c2:
                c += 1 if c2 > c else -1
                out[r][c] = 1
    return tuple(tuple(row) for row in out)


def path_vh(g: Grid) -> Optional[Grid]:
    """Join the two set cells, vertical leg first, from the first in reading
    order (the kit's open ``bfs_shortest``); ``None`` unless exactly two
    cells are set."""
    return _path(g, True)


def path_hv(g: Grid) -> Optional[Grid]:
    """The same with the horizontal leg first."""
    return _path(g, False)


def _complement(g: Grid) -> Grid:
    return tuple(tuple(1 - v for v in row) for row in g)


Op = Callable[[Grid], Optional[Grid]]


def single_operators(h: int, w: int, kit_only: bool = False
                     ) -> Dict[str, Op]:
    """The parameter-free operators of tier 1, by name."""
    ops: Dict[str, Op] = {}
    for name, p in permutation_library(h, w, kit_only).items():
        ops["perm:" + name] = (lambda g, p=p: unflatten(permute(flatten(g), p), w))
    if not kit_only:
        ops["complement"] = _complement
        ops["fill_enclosed"] = fill_enclosed
        ops["path_vh"] = path_vh
        ops["path_hv"] = path_hv
    return ops


# ── hypotheses and the tiered solver ───────────────────────────────────────

class Hypothesis:
    """A named rule ``grid -> grid or None`` (``None``: undefined there)."""

    __slots__ = ("name", "rule", "permutation")

    def __init__(self, name: str, rule: Op, permutation: bool = False):
        self.name = name
        self.rule = rule
        self.permutation = permutation

    def __call__(self, g: Grid) -> Optional[Grid]:
        return self.rule(g)


def _xor_mask(pairs: Sequence[Tuple[Grid, Grid]],
              pre: Optional[Op] = None) -> Optional[Tuple[int, ...]]:
    """The one XOR mask ``d`` with ``pre(x) xor d = y`` on every pair, or
    ``None``.  A mask is fitted *from* the pairs, and one pair fits a mask to
    any rule at all, so with fewer than two distinct pairs there is no
    evidence for it and none is offered (the evidence guard)."""
    if len(set(pairs)) < 2:
        return None
    masks = set()
    for x, y in pairs:
        px = pre(x) if pre else x
        if px is None:
            return None
        masks.add(tuple(a ^ b for a, b in zip(flatten(px), flatten(y))))
        if len(masks) > 1:
            return None
    return next(iter(masks)) if masks else None


def _apply_mask(g: Optional[Grid], d: Sequence[int], w: int) -> Optional[Grid]:
    if g is None:
        return None
    return unflatten(tuple(a ^ b for a, b in zip(flatten(g), d)), w)


def _learn_permutation(pairs: Sequence[Tuple[Grid, Grid]]
                       ) -> Optional[List[int]]:
    """The cell permutation the pairs determine uniquely, or ``None``."""
    flat = [(flatten(x), flatten(y)) for x, y in pairs]
    n = len(flat[0][0])
    perm = []
    for i in range(n):
        cands = [j for j in range(n) if all(y[i] == x[j] for x, y in flat)]
        if len(cands) != 1:
            return None
        perm.append(cands[0])
    return perm if sorted(perm) == list(range(n)) else None


def tiers_for(pairs: Sequence[Tuple[Grid, Grid]], h: int, w: int,
              kit_only: bool = False, depth: int = 2,
              layer_filter: bool = True, mode: str = "union"
              ) -> Tuple[List[Callable[[], List[Hypothesis]]], Dict[str, int]]:
    """The hypothesis tiers for these demonstrations, each built only when
    the solver reaches it, and the layer filter's count.

    ``mode="union"`` (the default) reads single operators and two-step
    compositions as **one** tier, so a single operator that fits is not
    answered while a composition that also fits disagrees; ``mode="occam"``
    reads them as two tiers, single operators first (fewer refusals, and a
    wrong answer whenever a single operator fits demonstrations made by a
    composition)."""
    ops = single_operators(h, w, kit_only)
    weight_kept = all(sum(flatten(x)) == sum(flatten(y)) for x, y in pairs)
    stats = {"skipped_by_layer": 0}

    def usable(name: str) -> bool:
        if name.startswith("perm:") and layer_filter and not weight_kept:
            stats["skipped_by_layer"] += 1
            return False
        return True

    def tier1() -> List[Hypothesis]:
        hyps = [Hypothesis(n, op, n.startswith("perm:"))
                for n, op in ops.items() if usable(n)]
        d = _xor_mask(pairs)
        if d is not None:
            hyps.append(Hypothesis("xor_mask", lambda g, d=d: _apply_mask(g, d, w)))
        return hyps

    def tier2() -> List[Hypothesis]:
        hyps: List[Hypothesis] = []
        names = [n for n in ops if n != "perm:identity"]
        for a in names:
            for b in names:
                both_perm = a.startswith("perm:") and b.startswith("perm:")
                if both_perm and layer_filter and not weight_kept:
                    stats["skipped_by_layer"] += 1
                    continue
                oa, ob = ops[a], ops[b]
                hyps.append(Hypothesis(
                    f"{a} then {b}",
                    lambda g, oa=oa, ob=ob: (lambda m: None if m is None
                                             else ob(m))(oa(g))))
            if a.startswith("perm:"):
                d = _xor_mask(pairs, ops[a])
                if d is not None:
                    oa = ops[a]
                    hyps.append(Hypothesis(
                        f"{a} then xor_mask",
                        lambda g, oa=oa, d=d: _apply_mask(oa(g), d, w)))
        return hyps

    def tier3() -> List[Hypothesis]:
        p = _learn_permutation(pairs)
        if p is None:
            return []
        return [Hypothesis("learnt_permutation",
                           lambda g, p=p: unflatten(permute(flatten(g), p), w),
                           True)]

    tiers: List[Callable[[], List[Hypothesis]]] = [tier1]
    if depth >= 2 and not kit_only:
        if mode == "union":
            tiers = [lambda: tier1() + tier2()]
        else:
            tiers.append(tier2)
    tiers.append(tier3)
    return tiers, stats


def _consistent(hyp: Hypothesis, pairs: Sequence[Tuple[Grid, Grid]]) -> bool:
    for x, y in pairs:
        if hyp(x) != y:
            return False
    return True


def solve(pairs: Sequence[Tuple[Grid, Grid]], query: Grid,
          kit_only: bool = False, depth: int = 2, gate: bool = True,
          layer_filter: bool = True, mode: str = "union"
          ) -> Dict[str, object]:
    """Read the first tier with a consistent hypothesis; answer only if all
    of them agree on the query (``GLM.PipelineInduction.solve``).

    ``gate=False`` is the control: the first consistent hypothesis answers,
    agreed or not.  The result says which tier was read, every surviving
    hypothesis, and the status: ``answered``, ``ambiguous`` (refused: the
    survivors disagree), ``undefined`` (refused: the survivors give the
    query no output) or ``unsolved`` (refused: nothing fits)."""
    if not pairs:
        return {"status": "unsolved", "answer": None, "tier": None,
                "survivors": [], "steps": ["no demonstrations"]}
    h, w = len(query), len(query[0])
    shapes = {(len(x), len(x[0])) for x, _ in pairs} | \
             {(len(y), len(y[0])) for _, y in pairs}
    if shapes != {(h, w)}:
        return {"status": "unsolved", "answer": None, "tier": None,
                "survivors": [], "steps": ["grids differ in shape"]}
    tiers, stats = tiers_for(pairs, h, w, kit_only, depth, layer_filter,
                             mode)
    steps: List[str] = [f"{len(pairs)} demonstrations of {h}x{w} grids"]
    tried = 0
    for k, build in enumerate(tiers, 1):
        hyps = build()
        tried += len(hyps)
        live = [hy for hy in hyps if _consistent(hy, pairs)]
        steps.append(f"tier {k}: {len(live)} of {len(hyps)} hypotheses fit")
        if not live:
            continue
        outs = [hy(query) for hy in live]
        names = [hy.name for hy in live]
        base = {"tier": k, "survivors": names, "tried": tried,
                "skipped_by_layer": stats["skipped_by_layer"], "steps": steps}
        if not gate:
            return dict(base, status="answered" if outs[0] is not None
                        else "undefined", answer=outs[0])
        if len(set(outs)) == 1:
            if outs[0] is None:
                return dict(base, status="undefined", answer=None)
            return dict(base, status="answered", answer=outs[0])
        return dict(base, status="ambiguous", answer=None,
                    answers=sorted({grid_text(o) for o in outs if o is not None}))
    return {"status": "unsolved", "answer": None, "tier": None,
            "survivors": [], "tried": tried,
            "skipped_by_layer": stats["skipped_by_layer"], "steps": steps}


# ── the measuring step, on the GLM's own substrate ─────────────────────────

def measure(g: Grid) -> Dict[str, object]:
    """The kit's measuring step for a 24-cell grid, read off
    :mod:`glm_universal.substrate.leech2`: weight, parity, whether ``4b`` is
    a Leech point (the parity wall, ``GLMKit.parity_wall``), whether ``8b``
    is (always, ``GLMKit.eight_mul_mem``), and the class of ``4b`` modulo
    ``2Λ`` when ``4b`` is a lattice point (``GLMKit.junction_iff``)."""
    from ..substrate import leech2
    cells = flatten(g)
    out: Dict[str, object] = {"cells": len(cells), "weight": sum(cells),
                              "parity": sum(cells) % 2}
    if len(cells) != 24:
        out["word"] = None
        return out
    four = tuple(4 * v for v in cells)
    out["word"] = grid_to_word(g)
    out["four_in_leech"] = leech2.in_leech(four)
    out["eight_in_leech"] = leech2.in_leech(tuple(8 * v for v in cells))
    out["junction"] = leech2.class_of(four) if out["four_in_leech"] else None
    return out


def check_substrate(trials: int = 2000, seed: int = 0) -> Dict[str, int]:
    """The kit's ``glm_bridge.check_substrate``, run against the GLM's
    substrate: the four theorems proved for any binary code containing 0,
    tested on ``trials`` words in the study scripts' bit order."""
    from ..substrate import leech2
    s = Stream(seed)
    glue = (-3,) + (1,) * 23
    fails = {"parity_wall": 0, "parity_wall_glue": 0, "eight_mul": 0,
             "junction_parity": 0}
    for _ in range(trials):
        b = s.bit_list(24)
        even = sum(b) % 2 == 0
        if bool(leech2.in_leech(tuple(4 * x for x in b))) != even:
            fails["parity_wall"] += 1
        if bool(leech2.in_leech(tuple(4 * x + g for x, g in zip(b, glue)))) != even:
            fails["parity_wall_glue"] += 1
        if not leech2.in_leech(tuple(8 * x for x in b)):
            fails["eight_mul"] += 1
        b2 = s.bit_list(24)
        if even and sum(b2) % 2 == 0:
            same = leech2.class_of(tuple(4 * x for x in b)) == \
                leech2.class_of(tuple(4 * x for x in b2))
            if same and (sum(b) - sum(b2)) % 4 != 0:
                fails["junction_parity"] += 1
    fails["trials"] = trials
    return fails


# ── the iteration-8 analogy decoders (the control of mark A) ───────────────

def threshold_analogy(a: Sequence[int], b: Sequence[int], c: Sequence[int]
                      ) -> Tuple[int, ...]:
    """Iteration 8's dual-snap decode, ``[3(c + b - a) >= 2]`` -- exact on
    toggle only when ``A = C`` (``GLMKit.threshold_analogy_toggle_iff``)."""
    return tuple(1 if 3 * (ci + bi - ai) >= 2 else 0
                 for ai, bi, ci in zip(a, b, c))


def parity_analogy(a: Sequence[int], b: Sequence[int], c: Sequence[int]
                   ) -> Tuple[int, ...]:
    """The fix: decode by parity, which is the F2 analogy
    (``GLMKit.parity_decode_eq_xor``)."""
    return tuple((ci + bi - ai) % 2 for ai, bi, ci in zip(a, b, c))


# ── task families, from a fixed integer recurrence ─────────────────────────

class Stream:
    """A fixed 64-bit linear congruential recurrence (Knuth's MMIX
    constants).  Not a random source: the same seed gives the same
    stream."""

    def __init__(self, seed: int):
        self.state = (seed * 0x9E3779B97F4A7C15 + 1) % (1 << 64)

    def bits(self, k: int) -> int:
        self.state = (self.state * 6364136223846793005
                      + 1442695040888963407) % (1 << 64)
        return self.state >> (64 - k)

    def below(self, n: int) -> int:
        """An integer in ``[0, n)``, by rejection (no modulo bias)."""
        k = max(1, (n - 1).bit_length())
        while True:
            v = self.bits(k)
            if v < n:
                return v

    def between(self, lo: int, hi: int) -> int:
        return lo + self.below(hi - lo + 1)

    def bit_list(self, n: int) -> List[int]:
        return [self.bits(1) for _ in range(n)]


def _blank(h: int, w: int) -> List[List[int]]:
    return [[0] * w for _ in range(h)]


def _freeze(g: List[List[int]]) -> Grid:
    return tuple(tuple(r) for r in g)


def _blocks(s: Stream, h: int, w: int) -> Grid:
    g = _blank(h, w)
    for _ in range(s.between(2, 4)):
        bh, bw = s.between(1, 2), s.between(1, 2)
        t, l = s.between(0, h - bh), s.between(0, w - bw)
        for r in range(t, t + bh):
            for c in range(l, l + bw):
                g[r][c] = 1
    return _freeze(g)


def _gen_toggle(s: Stream, h: int, w: int) -> Tuple[Grid, Grid]:
    x = _freeze([s.bit_list(w) for _ in range(h)])
    return x, _complement(x)


def _gen_translate(s: Stream, h: int, w: int) -> Tuple[Grid, Grid]:
    bh = bw = 2
    top = s.between(0, max(0, h - 1 - bh - 1))
    left = s.between(0, max(0, w - bw - 1))
    x, y = _blank(h, w), _blank(h, w)
    for r in range(bh):
        for c in range(bw):
            x[top + r][left + c] = 1
            y[top + 1 + r][left + 1 + c] = 1
    x[h - 1] = [1] * w
    y[h - 1] = [1] * w
    return _freeze(x), _freeze(y)


def _gen_rect(s: Stream, h: int, w: int) -> Grid:
    rh = s.between(max(3, h // 2), h)
    rw = s.between(max(3, w // 2), w)
    top, left = s.between(0, h - rh), s.between(0, w - rw)
    g = _blank(h, w)
    for c in range(left, left + rw):
        g[top][c] = g[top + rh - 1][c] = 1
    for r in range(top, top + rh):
        g[r][left] = g[r][left + rw - 1] = 1
    return _freeze(g)


def _gen_two(s: Stream, h: int, w: int) -> Grid:
    cells = set()
    while len(cells) < 2:
        cells.add((s.below(h), s.below(w)))
    g = _blank(h, w)
    for r, c in cells:
        g[r][c] = 1
    return _freeze(g)


def _perm_rule(name: str, h: int, w: int) -> Callable[[Grid], Grid]:
    p = permutation_library(h, w)[name]
    return lambda g: unflatten(permute(flatten(g), p), w)


def _family(make_input: Callable[[Stream, int, int], Grid],
            rule: Callable[[int, int], Callable[[Grid], Optional[Grid]]]):
    def gen(s: Stream, h: int, w: int) -> Tuple[Grid, Grid]:
        x = make_input(s, h, w)
        y = rule(h, w)(x)
        assert y is not None
        return x, y
    return gen


def _then(f, g):
    return lambda h, w: (lambda x: g(h, w)(f(h, w)(x)))


def _random_row(s: Stream, h: int, w: int) -> Grid:
    return _freeze([s.bit_list(w) for _ in range(h)])


_F = Dict[str, Tuple[str, int, int, Callable[[Stream, int, int], Tuple[Grid, Grid]]]]

#: name -> (group, rows, columns, generator).  Groups: ``kit`` (the study's
#: five), ``single`` (one more operator each), ``steps`` (two operators in
#: turn), ``string`` (one-row grids: bit strings).
FAMILIES: _F = {
    "toggle": ("kit", 4, 6, _gen_toggle),
    "translate": ("kit", 4, 6, _gen_translate),
    "reflect_v": ("kit", 4, 6, _family(_blocks, lambda h, w: _perm_rule("reflect_v", h, w))),
    "flood_fill": ("kit", 4, 6, _family(_gen_rect, lambda h, w: fill_enclosed)),
    "bfs_shortest": ("kit", 4, 6, _family(_gen_two, lambda h, w: path_vh)),
    "reflect_h": ("single", 4, 6, _family(_blocks, lambda h, w: _perm_rule("reflect_h", h, w))),
    "rotate180": ("single", 4, 6, _family(_blocks, lambda h, w: _perm_rule("rotate180", h, w))),
    "path_hv": ("single", 4, 6, _family(_gen_two, lambda h, w: path_hv)),
    "reflect_v_then_toggle": ("steps", 4, 6, _family(
        _blocks, _then(lambda h, w: _perm_rule("reflect_v", h, w),
                       lambda h, w: _complement))),
    "fill_then_reflect_h": ("steps", 4, 6, _family(
        _gen_rect, _then(lambda h, w: fill_enclosed,
                         lambda h, w: _perm_rule("reflect_h", h, w)))),
    "path_then_rotate180": ("steps", 4, 6, _family(
        _gen_two, _then(lambda h, w: path_vh,
                        lambda h, w: _perm_rule("rotate180", h, w)))),
    "string_reverse": ("string", 1, 24, _family(
        _random_row, lambda h, w: _perm_rule("reflect_v", h, w))),
    "string_rotate": ("string", 1, 24, _family(
        _random_row, lambda h, w: _perm_rule("shift(0,1)", h, w))),
    "string_complement": ("string", 1, 24, _family(
        _random_row, lambda h, w: _complement)),
    "string_reverse_complement": ("string", 1, 24, _family(
        _random_row, _then(lambda h, w: _perm_rule("reflect_v", h, w),
                           lambda h, w: _complement))),
}


def sample(name: str, seed: int) -> Tuple[Grid, Grid]:
    _group, h, w, gen = FAMILIES[name]
    return gen(Stream(seed * 7919 + sum(ord(ch) for ch in name)), h, w)


# ── the tool's text ────────────────────────────────────────────────────────

USAGE = ("give demonstrations and a query: 'IN -> OUT ; IN -> OUT ? QUERY', "
         "each grid as rows of 0s and 1s split by '/', e.g. tool induce "
         "100/000/000 -> 001/000/000 ; 010/100/000 -> 010/001/000 ? "
         "110/000/001")


def induce_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool induce``: parse, solve, and say what happened in words."""
    if "?" not in arg:
        return False, f"refused: {USAGE}", {}
    left, query_text = arg.rsplit("?", 1)
    query = parse_grid(query_text)
    pairs: List[Tuple[Grid, Grid]] = []
    for part in [p for p in left.split(";") if p.strip()]:
        if "->" not in part:
            return False, f"refused: {part.strip()!r} is not 'IN -> OUT'; {USAGE}", {}
        a, b = part.split("->", 1)
        x, y = parse_grid(a), parse_grid(b)
        if x is None or y is None:
            bad = a if x is None else b
            return False, f"refused: {bad.strip()!r} is not a grid of 0s and 1s", {}
        pairs.append((x, y))
    if query is None or not pairs:
        return False, f"refused: {USAGE}", {}
    r = solve(pairs, query)
    figures: Dict[str, object] = {
        "status": r["status"], "tier": r.get("tier"),
        "survivors": len(r.get("survivors", [])),
        "tried": r.get("tried", 0),
        "skipped_by_layer": r.get("skipped_by_layer", 0)}
    m = measure(query)
    if m.get("word") is not None:
        figures["query_word"] = m["word"]
        figures["query_four_in_leech"] = m["four_in_leech"]
    trail = "; ".join(r["steps"])
    if r["status"] == "answered":
        ans = r["answer"]
        figures["answer"] = grid_text(ans)
        rules = r["survivors"]
        shown = ", ".join(rules[:4]) + (f" and {len(rules) - 4} more"
                                        if len(rules) > 4 else "")
        return True, (f"induce: {grid_text(ans)}, given by every one of the "
                      f"{len(rules)} hypotheses of tier {r['tier']} that fit "
                      f"all {len(pairs)} demonstrations ({shown}); "
                      "GLM.PipelineInduction.solve_sound makes it the true "
                      f"rule's answer whenever the true rule is in that tier "
                      f"[{trail}]"), figures
    if r["status"] == "ambiguous":
        figures["answers"] = r["answers"]
        from . import pipeline_ask as pa        # Phase 176: ask to settle it
        ask_sentence, choice = pa.ask_text(pairs, query)
        if choice is not None:
            figures["ask"] = grid_text(choice["input"])
            figures["ask_decides"] = choice["decides"]
        o = solve(pairs, query, mode="occam")
        hint = ""
        if o["status"] == "answered":
            figures["occam_answer"] = grid_text(o["answer"])
            hint = (f"; the single operators alone ({', '.join(o['survivors'][:3])})"
                    f" would give {grid_text(o['answer'])}, which is not "
                    "safe to assert while a two-step rule that also fits "
                    "disagrees")
        return False, (f"induce: refused -- the {len(r['survivors'])} "
                       f"hypotheses of tier {r['tier']} that fit every "
                       f"demonstration disagree on the query ("
                       f"{', '.join(r['survivors'][:4])}...), giving "
                       f"{len(r['answers'])} different answers; any answer "
                       "would be wrong for one of them "
                       "(GLM.PipelineInduction.ambiguous_forces_refusal); "
                       f"another demonstration would decide{hint}; "
                       f"{ask_sentence} [{trail}]"), figures
    if r["status"] == "undefined":
        return False, (f"induce: refused -- the hypotheses that fit "
                       f"({', '.join(r['survivors'][:4])}) give this query "
                       f"no output [{trail}]"), figures
    return False, (f"induce: refused -- no hypothesis of any tier fits every "
                   f"demonstration (GLM.PipelineInduction.solve_none_of_unfit)"
                   f" [{trail}]"), figures
