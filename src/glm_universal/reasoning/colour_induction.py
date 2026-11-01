"""``glm_universal.reasoning.colour_induction`` -- the gate of ``tool induce``
on colour grids whose shape may change, and ``tool arc`` on the stored ARC
tasks (Phase 178, part A).

*Created 22 October 2026.*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from ``MASTER_PLAN.md`` (Phase
178), ``SYSTEM.md`` (the paragraph "Colour grids, objects and the frame
plane"), ``studies/GLM_ACADEMIC_PAPER.md`` §20.52, ``STATUS.md`` §2.1 item 9,
the row of ``tests/README.md`` for ``test_colour_induction.py``, the
interface of the Round 11 stand-in
(``source_material/.../rule30_round11/standins/colour_induction_standin.py``:
``parse_task``, ``is_colour_task``, ``induce_colour_text``, ``arc_text``),
``reasoning/pipeline_kit.py`` (the gate this module carries to colours) and
``reasoning/vision_stack.py`` (the size classes of the conditional
recolour).  The vocabulary below is the documented one; what the documents
do not fix (the exact operator list inside each documented group, the
object keys' encoding, the background rule's tie-break) is chosen here and
stated in the docstrings.  ``ColourInduction.lean`` is not in the tree at
this reconstruction; :data:`LEAN_THEOREMS` lists the five theorem names the
documents record (of twelve).*

Where it comes from
-------------------
``tool induce`` (:mod:`glm_universal.reasoning.pipeline_kit`, Phase 175)
induces a rule from demonstration pairs of 0/1 grids of one shape and
answers only when every fitting hypothesis agrees.  Its study left colours
and objects open; the frame-operator study (Phase 177) left two rules to
carry over: **read the invariant first** and **count evidence by span**.
This module is that widening, for grids of the colours ``0``-``9`` whose
shape may change from input to output.

The vocabulary
--------------
*Parameter-free operators* (:func:`operators`): the eight symmetries of the
square (``identity``, three turns, two mirrors, the two diagonals); gravity
towards each side; the crop to the box of the non-background cells; scaling
by 2 and 3; tiling ``1x2``, ``2x1``, ``2x2``; mirrors (the grid beside its
mirror image, above it, and the four-fold kaleidoscope); the four halves;
symmetry completion (a background cell takes the colour of its mirror image
left-right, up-down, or under both).  *Two-step compositions*: any two
non-identity operators in turn, read in the same tier as single operators
(the union tier of ``pipeline_kit``).  *Fitted families*
(:data:`FITTED`), each with a parameter read off the demonstrations: a
colour map (the output a function of the input cell by cell,
``GLM.ColourInduction.fit_iff_functional``); object recolouring, a
connected object's new colour a function of its colour and its size class,
its size rank, or whether it touches the border; enclosed fill (background
cells not connected to the border through background take one colour); and
half logic (the two halves either side of a divider, or the two equal
halves, combined cell by cell by a fitted truth table).

The three layers
----------------
1. **The invariant reading** (:func:`read_invariants`).  Each pair is read
   first for what it keeps: the colour counts, the colour set, the shape.  A
   cell permutation keeps the colour counts
   (``GLM.ColourInduction.count_perm``), so when a demonstration changes them
   no symmetry, gravity or composition of them is tried; no parameter-free
   operator brings in a colour, so when an output shows a colour its input
   lacks none is tried; when a demonstration changes shape no shape-keeping
   hypothesis is tried.  The hypotheses skipped are counted
   (figure ``skipped_by_invariant``); skipping changes no answer, since every
   skipped hypothesis fails a demonstration.
2. **The fit.**  Every hypothesis not skipped is run on every demonstration;
   the survivors are those that reproduce every output.  A fitted family's
   parameter is read off all the demonstrations.
3. **The gate** (:func:`verdict`).  The query is answered only when every
   survivor gives it the same output and at least one survivor is
   **tested**.  A parameter-free operator is tested by any demonstration it
   fits (it has nothing to fit); a fitted family is tested only when, fitted
   to all the demonstrations but one, it reproduces the one left out -- the
   **span rule** (``GLM.ColourInduction.untested_never_answers``), so one
   demonstration of a recolour is never answered.  A fitted survivor whose
   parameter the query needs but no demonstration showed (a colour the map
   never read, an object key never seen) forces a refusal -- the **unread
   rule** (``GLM.ColourInduction.unread_fitted_refuses``); the first take of
   Phase 178 set such survivors aside and answered from the rest, and was
   wrong ten times.  The gate is sound (``GLM.ColourInduction.gate_sound``):
   an answer is the true rule's whenever the true rule is in the vocabulary.

The background
--------------
One background per task (the second take's fix for a generator artefact):
the colour most frequent over every demonstration input and the query, the
smaller colour on a tie (:func:`background`).

Exactness
---------
Integers and tuples only (D7).
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .vision_stack import size_bucket

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "Grid", "parse_grid", "grid_text",
    "parse_task", "is_colour_task", "background", "components",
    "operators", "FITTED", "read_invariants", "read_task", "verdict",
    "solve", "induce_colour_text", "induce_tool_text", "arc_names",
    "arc_task_path", "arc_task", "arc_solve", "arc_text", "USAGE",
]

LEAN_FILE = "RequestProject/GLM/ColourInduction.lean"
#: The theorem names the surviving documents record (``MASTER_PLAN.md``
#: Phase 178: twelve theorems, of which these five are named).
LEAN_THEOREMS: Tuple[str, ...] = (
    "count_perm", "fit_iff_functional", "gate_sound",
    "untested_never_answers", "unread_fitted_refuses")

Grid = Tuple[Tuple[int, ...], ...]
Pairs = Sequence[Tuple[Grid, Grid]]

USAGE = ("give demonstrations and a query: 'IN -> OUT ; IN -> OUT ? QUERY', "
         "each grid as rows of colours 0-9 split by '/', e.g. tool induce "
         "120/300 -> 021/003 ; 450/060 -> 054/060 ? 708/090")


# ── grids ──────────────────────────────────────────────────────────────────

def parse_grid(text: str) -> Optional[Grid]:
    """Rows split by ``/``; a row is a run of digits (``0120``) or colours
    split by spaces or commas (``0 1 2 0``).  Colours ``0``-``9``; ``None``
    if the text is not a rectangular grid of them."""
    rows = [r.strip() for r in text.strip().split("/")]
    if not rows or any(not r for r in rows):
        return None
    out: List[Tuple[int, ...]] = []
    for r in rows:
        cells = r.replace(",", " ").split()
        if len(cells) == 1:
            cells = list(cells[0])
        if not cells or any(not c.isdigit() or len(c) != 1 for c in cells):
            return None
        out.append(tuple(int(c) for c in cells))
    if len({len(r) for r in out}) != 1:
        return None
    return tuple(out)


def grid_text(g: Optional[Grid]) -> str:
    if g is None:
        return "(none)"
    return "/".join("".join(str(v) for v in row) for row in g)


def _shape(g: Grid) -> Tuple[int, int]:
    return (len(g), len(g[0]) if g else 0)


def _colours(g: Grid) -> Counter:
    return Counter(v for row in g for v in row)


def parse_task(arg: str) -> Tuple[Optional[List[Tuple[Grid, Grid]]],
                                  Optional[Grid], str]:
    """``IN -> OUT ; IN -> OUT ? QUERY`` as ``(pairs, query, "")``, or
    ``(None, None, reason)``."""
    if "?" not in arg:
        return None, None, "no query"
    left, qtext = arg.rsplit("?", 1)
    pairs: List[Tuple[Grid, Grid]] = []
    for part in [p for p in left.split(";") if p.strip()]:
        if "->" not in part:
            return None, None, f"{part.strip()!r} is not 'IN -> OUT'"
        a, b = part.split("->", 1)
        x, y = parse_grid(a), parse_grid(b)
        if x is None or y is None:
            bad = a if x is None else b
            return None, None, f"{bad.strip()!r} is not a grid of colours 0-9"
        pairs.append((x, y))
    query = parse_grid(qtext)
    if query is None:
        return None, None, f"{qtext.strip()!r} is not a grid of colours 0-9"
    if not pairs:
        return None, None, "no demonstrations"
    return pairs, query, ""


def is_colour_task(pairs: Pairs, query: Grid) -> bool:
    """A colour task: some cell holds a colour other than 0 and 1, or some
    demonstration changes shape.  Every other task is a binary one-shape
    task and goes to :mod:`pipeline_kit` exactly as before."""
    grids = [g for p in pairs for g in p] + [query]
    if any(v not in (0, 1) for g in grids for row in g for v in row):
        return True
    return any(_shape(a) != _shape(b) for a, b in pairs)


def background(pairs: Pairs, query: Optional[Grid] = None) -> int:
    """One background per task: the colour most frequent over every
    demonstration input and the query (the smaller colour on a tie)."""
    total: Counter = Counter()
    for x, _ in pairs:
        total.update(_colours(x))
    if query is not None:
        total.update(_colours(query))
    if not total:
        return 0
    return min(total, key=lambda c: (-total[c], c))


# ── parameter-free operators ───────────────────────────────────────────────

def _rot90(g: Grid) -> Grid:
    h, w = _shape(g)
    return tuple(tuple(g[h - 1 - r][c] for r in range(h)) for c in range(w))


def _rot180(g: Grid) -> Grid:
    return tuple(tuple(reversed(row)) for row in reversed(g))


def _rot270(g: Grid) -> Grid:
    h, w = _shape(g)
    return tuple(tuple(g[r][w - 1 - c] for r in range(h)) for c in range(w))


def _flip_h(g: Grid) -> Grid:
    return tuple(tuple(reversed(row)) for row in g)


def _flip_v(g: Grid) -> Grid:
    return tuple(reversed(g))


def _transpose(g: Grid) -> Grid:
    return tuple(zip(*g))


def _antitranspose(g: Grid) -> Grid:
    return _rot180(_transpose(g))


def gravity(g: Grid, bg: int, side: str) -> Grid:
    """Every non-background cell slides towards ``side`` (``down``, ``up``,
    ``left``, ``right``), keeping its order."""
    if side in ("left", "right"):
        rows = []
        for row in g:
            cells = [v for v in row if v != bg]
            pad = [bg] * (len(row) - len(cells))
            rows.append(tuple(cells + pad if side == "left" else pad + cells))
        return tuple(rows)
    t = _transpose(g)
    return _transpose(gravity(t, bg, "left" if side == "up" else "right"))


def crop(g: Grid, bg: int) -> Optional[Grid]:
    """The box of the non-background cells; ``None`` if there are none."""
    cells = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row)
             if v != bg]
    if not cells:
        return None
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return tuple(tuple(g[r][c0:c1 + 1]) for r in range(r0, r1 + 1))


def scale(g: Grid, k: int) -> Grid:
    return tuple(tuple(v for v in row for _ in range(k))
                 for row in g for _ in range(k))


def tile(g: Grid, down: int, across: int) -> Grid:
    return tuple(tuple(row) * across for _ in range(down) for row in g)


def _mirror_h(g: Grid) -> Grid:
    return tuple(tuple(row) + tuple(reversed(row)) for row in g)


def _mirror_v(g: Grid) -> Grid:
    return tuple(g) + tuple(reversed(g))


def half(g: Grid, which: str) -> Optional[Grid]:
    """A half: ``left``/``right`` takes the first/last ``w // 2`` columns
    (an odd middle column, a divider, is left out), ``top``/``bottom`` the
    same for rows; ``None`` on a grid of one column (row)."""
    h, w = _shape(g)
    if which in ("left", "right"):
        if w < 2:
            return None
        k = w // 2
        return tuple(tuple(row[:k] if which == "left" else row[w - k:])
                     for row in g)
    if h < 2:
        return None
    k = h // 2
    return tuple(g[:k]) if which == "top" else tuple(g[h - k:])


def complete(g: Grid, bg: int, axes: str) -> Grid:
    """Symmetry completion: a background cell takes the colour of its mirror
    image left-right (``h``), up-down (``v``), or the first non-background
    of its three images (``hv``)."""
    h, w = _shape(g)
    out = []
    for r in range(h):
        row = []
        for c in range(w):
            v = g[r][c]
            if v == bg:
                images = {"h": [(r, w - 1 - c)], "v": [(h - 1 - r, c)],
                          "hv": [(r, w - 1 - c), (h - 1 - r, c),
                                 (h - 1 - r, w - 1 - c)]}[axes]
                for rr, cc in images:
                    if g[rr][cc] != bg:
                        v = g[rr][cc]
                        break
            row.append(v)
        out.append(tuple(row))
    return tuple(out)


Op = Callable[[Grid, int], Optional[Grid]]


class Operator:
    """A parameter-free operator, with what it always keeps: the colour
    counts (``count_keep``: a cell permutation) and the shape
    (``shape_keep``)."""

    __slots__ = ("name", "run", "count_keep", "shape_keep")

    def __init__(self, name: str, run: Op, count_keep: bool,
                 shape_keep: bool):
        self.name = name
        self.run = run
        self.count_keep = count_keep
        self.shape_keep = shape_keep


def _o(name: str, run: Op, count_keep: bool = False,
       shape_keep: bool = False) -> Operator:
    return Operator(name, run, count_keep, shape_keep)


_OPERATORS: Tuple[Operator, ...] = (
    # the eight symmetries (cell permutations: they keep the colour counts)
    _o("identity", lambda g, bg: g, True, True),
    _o("rotate90", lambda g, bg: _rot90(g), True),
    _o("rotate180", lambda g, bg: _rot180(g), True, True),
    _o("rotate270", lambda g, bg: _rot270(g), True),
    _o("flip_h", lambda g, bg: _flip_h(g), True, True),
    _o("flip_v", lambda g, bg: _flip_v(g), True, True),
    _o("transpose", lambda g, bg: _transpose(g), True),
    _o("antitranspose", lambda g, bg: _antitranspose(g), True),
    # gravity (cell permutations too)
    _o("gravity_down", lambda g, bg: gravity(g, bg, "down"), True, True),
    _o("gravity_up", lambda g, bg: gravity(g, bg, "up"), True, True),
    _o("gravity_left", lambda g, bg: gravity(g, bg, "left"), True, True),
    _o("gravity_right", lambda g, bg: gravity(g, bg, "right"), True, True),
    # crop
    _o("crop", crop),
    # scaling
    _o("scale2", lambda g, bg: scale(g, 2)),
    _o("scale3", lambda g, bg: scale(g, 3)),
    # tiling
    _o("tile1x2", lambda g, bg: tile(g, 1, 2)),
    _o("tile2x1", lambda g, bg: tile(g, 2, 1)),
    _o("tile2x2", lambda g, bg: tile(g, 2, 2)),
    # mirrors
    _o("mirror_h", lambda g, bg: _mirror_h(g)),
    _o("mirror_v", lambda g, bg: _mirror_v(g)),
    _o("mirror_4", lambda g, bg: _mirror_v(_mirror_h(g))),
    # halves
    _o("half_left", lambda g, bg: half(g, "left")),
    _o("half_right", lambda g, bg: half(g, "right")),
    _o("half_top", lambda g, bg: half(g, "top")),
    _o("half_bottom", lambda g, bg: half(g, "bottom")),
    # symmetry completion
    _o("complete_h", lambda g, bg: complete(g, bg, "h"), False, True),
    _o("complete_v", lambda g, bg: complete(g, bg, "v"), False, True),
    _o("complete_hv", lambda g, bg: complete(g, bg, "hv"), False, True),
)


def operators() -> Tuple[Operator, ...]:
    """The parameter-free operators of the vocabulary, in reading order."""
    return _OPERATORS


# ── objects ────────────────────────────────────────────────────────────────

def components(g: Grid, bg: int) -> List[Tuple[int, Tuple[Tuple[int, int], ...]]]:
    """The objects: maximal 4-connected sets of cells of one non-background
    colour, as ``(colour, cells)`` in reading order of their first cell."""
    h, w = _shape(g)
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or g[r][c] == bg:
                continue
            colour = g[r][c]
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                a, b = stack.pop()
                cells.append((a, b))
                for aa, bb in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    if 0 <= aa < h and 0 <= bb < w and not seen[aa][bb] \
                            and g[aa][bb] == colour:
                        seen[aa][bb] = True
                        stack.append((aa, bb))
            out.append((colour, tuple(sorted(cells))))
    return out


def _object_keys(kind: str, g: Grid, comps) -> List[Tuple[int, object]]:
    """Each object's key for one recolouring family: its colour with its size
    class (the vision stack's classes, :func:`vision_stack.size_bucket`), its
    dense size rank in the grid (0 the largest), or whether it touches the
    border."""
    h, w = _shape(g)
    if kind == "size":
        return [(col, size_bucket(len(cells))) for col, cells in comps]
    if kind == "rank":
        sizes = sorted({len(cells) for _, cells in comps}, reverse=True)
        return [(col, sizes.index(len(cells))) for col, cells in comps]
    if kind == "border":
        return [(col, any(r in (0, h - 1) or c in (0, w - 1)
                          for r, c in cells)) for col, cells in comps]
    raise KeyError(kind)


def _enclosed(g: Grid, bg: int) -> List[Tuple[int, int]]:
    """Background cells not 4-connected to the border through background."""
    h, w = _shape(g)
    seen = [[False] * w for _ in range(h)]
    stack = [(r, c) for r in range(h) for c in range(w)
             if (r in (0, h - 1) or c in (0, w - 1)) and g[r][c] == bg]
    for r, c in stack:
        seen[r][c] = True
    while stack:
        r, c = stack.pop()
        for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= rr < h and 0 <= cc < w and not seen[rr][cc] \
                    and g[rr][cc] == bg:
                seen[rr][cc] = True
                stack.append((rr, cc))
    return [(r, c) for r in range(h) for c in range(w)
            if g[r][c] == bg and not seen[r][c]]


def _split(g: Grid, bg: int, orient: str) -> Optional[Tuple[Grid, Grid]]:
    """The two halves for half logic: either side of a divider (a middle
    column, or row for ``orient="tb"``, of one non-background colour) or the
    two equal halves of an even grid."""
    if orient == "tb":
        s = _split(_transpose(g), bg, "lr")
        return None if s is None else (_transpose(s[0]), _transpose(s[1]))
    h, w = _shape(g)
    if w % 2 == 1:
        d = w // 2
        col = {g[r][d] for r in range(h)}
        if w < 3 or len(col) != 1 or bg in col:
            return None
        return (tuple(tuple(row[:d]) for row in g),
                tuple(tuple(row[d + 1:]) for row in g))
    if w < 2:
        return None
    k = w // 2
    return (tuple(tuple(row[:k]) for row in g),
            tuple(tuple(row[k:]) for row in g))


# ── fitted families ────────────────────────────────────────────────────────
#
# A family is (fit, apply): ``fit(pairs, bg)`` reads the parameter off every
# demonstration, or ``None`` when no parameter reproduces them all;
# ``apply(param, grid, bg)`` is ``(output, unread)`` -- ``unread`` lists what
# the grid needs that the parameter never read (then the output is ``None``).

def _fit_colour_map(pairs: Pairs, bg: int):
    m: Dict[int, int] = {}
    for x, y in pairs:
        if _shape(x) != _shape(y):
            return None
        for rx, ry in zip(x, y):
            for a, b in zip(rx, ry):
                if m.setdefault(a, b) != b:
                    return None
    return m


def _apply_colour_map(m, g: Grid, bg: int):
    missing = sorted({v for row in g for v in row} - set(m))
    if missing:
        return None, [f"colour {c}" for c in missing]
    return tuple(tuple(m[v] for v in row) for row in g), []


def _fit_recolour(kind: str):
    def fit(pairs: Pairs, bg: int):
        m: Dict[Tuple[int, object], int] = {}
        for x, y in pairs:
            if _shape(x) != _shape(y):
                return None
            for rx, ry in zip(x, y):
                for a, b in zip(rx, ry):
                    if a == bg and b != bg:
                        return None
            comps = components(x, bg)
            for (col, cells), key in zip(comps, _object_keys(kind, x, comps)):
                outs = {y[r][c] for r, c in cells}
                if len(outs) != 1:
                    return None
                o = outs.pop()
                if m.setdefault(key, o) != o:
                    return None
        return m
    return fit


def _apply_recolour(kind: str):
    def apply(m, g: Grid, bg: int):
        comps = components(g, bg)
        keys = _object_keys(kind, g, comps)
        missing = sorted({k for k in keys if k not in m}, key=repr)
        if missing:
            return None, [f"object key {k}" for k in missing]
        out = [list(row) for row in g]
        for (_col, cells), key in zip(comps, keys):
            for r, c in cells:
                out[r][c] = m[key]
        return tuple(tuple(row) for row in out), []
    return apply


def _fit_fill(pairs: Pairs, bg: int):
    colour: Optional[int] = None
    for x, y in pairs:
        if _shape(x) != _shape(y):
            return None
        inside = set(_enclosed(x, bg))
        for r, (rx, ry) in enumerate(zip(x, y)):
            for c, (a, b) in enumerate(zip(rx, ry)):
                if (r, c) in inside:
                    if colour is None:
                        colour = b
                    if b != colour:
                        return None
                elif a != b:
                    return None
    return ("fill", colour)


def _apply_fill(param, g: Grid, bg: int):
    colour = param[1]
    inside = _enclosed(g, bg)
    if inside and colour is None:
        return None, ["the fill colour"]
    out = [list(row) for row in g]
    for r, c in inside:
        out[r][c] = colour
    return tuple(tuple(row) for row in out), []


def _fit_halves(orient: str):
    def fit(pairs: Pairs, bg: int):
        table: Dict[Tuple[bool, bool], int] = {}
        for x, y in pairs:
            s = _split(x, bg, orient)
            if s is None:
                return None
            a, b = s
            if _shape(a) != _shape(y) or _shape(b) != _shape(y):
                return None
            for ra, rb, ry in zip(a, b, y):
                for va, vb, vy in zip(ra, rb, ry):
                    key = (va != bg, vb != bg)
                    if table.setdefault(key, vy) != vy:
                        return None
        return table
    return fit


def _apply_halves(orient: str):
    def apply(table, g: Grid, bg: int):
        s = _split(g, bg, orient)
        if s is None:
            return None, ["a divider or two equal halves"]
        a, b = s
        keys = {(va != bg, vb != bg) for ra, rb in zip(a, b)
                for va, vb in zip(ra, rb)}
        missing = sorted(k for k in keys if k not in table)
        if missing:
            return None, [f"half cells {k}" for k in missing]
        return tuple(tuple(table[(va != bg, vb != bg)]
                           for va, vb in zip(ra, rb))
                     for ra, rb in zip(a, b)), []
    return apply


class Family:
    """A fitted family: its fit, its application, and whether it always
    keeps the shape (for the invariant reading)."""

    __slots__ = ("name", "fit", "apply", "shape_keep")

    def __init__(self, name, fit, apply, shape_keep):
        self.name = name
        self.fit = fit
        self.apply = apply
        self.shape_keep = shape_keep


FITTED: Tuple[Family, ...] = (
    Family("colour_map", _fit_colour_map, _apply_colour_map, True),
    Family("recolour_by_size", _fit_recolour("size"), _apply_recolour("size"),
           True),
    Family("recolour_by_rank", _fit_recolour("rank"), _apply_recolour("rank"),
           True),
    Family("recolour_by_border", _fit_recolour("border"),
           _apply_recolour("border"), True),
    Family("enclosed_fill", _fit_fill, _apply_fill, True),
    Family("half_logic_lr", _fit_halves("lr"), _apply_halves("lr"), False),
    Family("half_logic_tb", _fit_halves("tb"), _apply_halves("tb"), False),
)


# ── the invariant reading ──────────────────────────────────────────────────

def read_invariants(pairs: Pairs) -> Dict[str, bool]:
    """What every demonstration keeps: the colour counts, the colour set
    (no output colour its input lacks), the shape."""
    return {
        "counts_kept": all(_colours(x) == _colours(y) for x, y in pairs),
        "no_new_colour": all(set(_colours(y)) <= set(_colours(x))
                             for x, y in pairs),
        "shape_kept": all(_shape(x) == _shape(y) for x, y in pairs),
    }


def _skip_op(inv: Dict[str, bool], count_keep: bool, shape_keep: bool) -> bool:
    if not inv["no_new_colour"]:
        return True                       # no operator brings in a colour
    if count_keep and not inv["counts_kept"]:
        return True                       # GLM.ColourInduction.count_perm
    if shape_keep and not inv["shape_kept"]:
        return True
    return False


# ── reading a task ─────────────────────────────────────────────────────────

class Survivor:
    """A hypothesis that fits every demonstration, with its output on the
    query, what it left unread there, and whether it is tested."""

    __slots__ = ("name", "kind", "output", "unread", "tested")

    def __init__(self, name, kind, output, unread, tested):
        self.name = name
        self.kind = kind          # "operator", "steps" or "fitted"
        self.output = output
        self.unread = unread
        self.tested = tested


def _same(fn: Callable[[Grid], Optional[Grid]], pairs: Pairs) -> bool:
    for x, y in pairs:
        if fn(x) != y:
            return False
    return True


def _loo_tested(fam: Family, pairs: Pairs, bg: int) -> bool:
    """The span rule: fitted to every demonstration but one, the family
    reproduces the one left out."""
    for i in range(len(pairs)):
        rest = list(pairs[:i]) + list(pairs[i + 1:])
        if not rest:
            continue
        p = fam.fit(rest, bg)
        if p is None:
            continue
        out, unread = fam.apply(p, pairs[i][0], bg)
        if not unread and out == pairs[i][1]:
            return True
    return False


def read_task(pairs: Pairs, query: Grid, invariant: bool = True
              ) -> Dict[str, object]:
    """Every survivor of the vocabulary on these demonstrations, with its
    output on the query; the invariants read and the hypotheses they let the
    solver skip.  The verdict is :func:`verdict`'s."""
    bg = background(pairs, query)
    inv = read_invariants(pairs)
    ops = operators()
    skipped = 0
    tried = 0
    survivors: List[Survivor] = []

    # outputs of every operator on every demonstration input, computed once
    inputs = [x for x, _ in pairs]
    cache: Dict[Tuple[str, int], Optional[Grid]] = {}

    def run(op: Operator, i: int) -> Optional[Grid]:
        key = (op.name, i)
        if key not in cache:
            g = inputs[i]
            cache[key] = op.run(g, bg) if g is not None else None
        return cache[key]

    def fits_single(op: Operator) -> bool:
        return all(run(op, i) == y for i, (_, y) in enumerate(pairs))

    for op in ops:
        if invariant and _skip_op(inv, op.count_keep, op.shape_keep):
            skipped += 1
            continue
        tried += 1
        if fits_single(op):
            survivors.append(Survivor(op.name, "operator", op.run(query, bg),
                                      [], True))

    firsts = [o for o in ops if o.name != "identity"]
    for a in firsts:
        mids = None
        for b in firsts:
            if invariant and _skip_op(inv, a.count_keep and b.count_keep,
                                      a.shape_keep and b.shape_keep):
                skipped += 1
                continue
            tried += 1
            if mids is None:
                mids = [run(a, i) for i in range(len(pairs))]
            ok = True
            for m, (_, y) in zip(mids, pairs):
                if m is None or b.run(m, bg) != y:
                    ok = False
                    break
            if ok:
                q = a.run(query, bg)
                survivors.append(Survivor(f"{a.name} then {b.name}", "steps",
                                          None if q is None else b.run(q, bg),
                                          [], True))

    for fam in FITTED:
        if invariant and fam.shape_keep and not inv["shape_kept"]:
            skipped += 1
            continue
        tried += 1
        p = fam.fit(pairs, bg)
        if p is None:
            continue
        out, unread = fam.apply(p, query, bg)
        survivors.append(Survivor(fam.name, "fitted", out, list(unread),
                                  _loo_tested(fam, pairs, bg)))
    return {"background": bg, "invariants": inv, "survivors": survivors,
            "skipped_by_invariant": skipped, "tried": tried,
            "demonstrations": len(pairs)}


def verdict(reading: Dict[str, object], *, span_rule: bool = True,
            unread_rule: bool = True, gate: bool = True) -> Dict[str, object]:
    """The gate over a reading.  ``span_rule=False`` counts a fitted family as
    tested by its fit; ``unread_rule=False`` sets aside a survivor with an
    unread parameter (the first take); ``gate=False`` is the eager control,
    the first survivor with an output answers."""
    surv: List[Survivor] = reading["survivors"]   # type: ignore[assignment]
    base = {"survivors": [s.name for s in surv],
            "background": reading["background"],
            "skipped_by_invariant": reading["skipped_by_invariant"],
            "tried": reading["tried"]}
    if not surv:
        return dict(base, status="unsolved", answer=None)
    if not gate:
        for s in surv:
            if s.output is not None:
                return dict(base, status="answered", answer=s.output,
                            by=s.name)
        return dict(base, status="undefined", answer=None)
    unread = [s for s in surv if s.unread]
    if unread and unread_rule:
        return dict(base, status="unread", answer=None,
                    unread={s.name: list(s.unread) for s in unread})
    live = [s for s in surv if not s.unread]
    if not live:
        return dict(base, status="unread", answer=None,
                    unread={s.name: list(s.unread) for s in unread})
    outs = [s.output for s in live]
    if all(o is None for o in outs):
        return dict(base, status="undefined", answer=None)
    distinct = {o for o in outs}
    if len(distinct) > 1:
        return dict(base, status="ambiguous", answer=None,
                    answers=sorted(grid_text(o) for o in distinct))
    tested = [s.name for s in live
              if s.tested or (not span_rule and s.kind == "fitted")]
    if not tested:
        return dict(base, status="untested", answer=None,
                    candidate=outs[0])
    return dict(base, status="answered", answer=outs[0], tested=tested)


def solve(pairs: Pairs, query: Grid, **kw) -> Dict[str, object]:
    """Read the task and give the gate's verdict (keywords as
    :func:`verdict`)."""
    if not pairs:
        return {"status": "unsolved", "answer": None, "survivors": [],
                "background": 0, "skipped_by_invariant": 0, "tried": 0}
    return verdict(read_task(pairs, query), **kw)


# ── the tool's text ────────────────────────────────────────────────────────

def _names(xs: Sequence[str], k: int = 4) -> str:
    return ", ".join(xs[:k]) + (f" and {len(xs) - k} more" if len(xs) > k
                                else "")


def induce_colour_text(pairs: Pairs, query: Grid
                       ) -> Tuple[bool, str, Dict[str, object]]:
    """``tool induce`` on a colour task: solve and say it in words."""
    reading = read_task(pairs, query)
    r = verdict(reading)
    inv = reading["invariants"]
    kept = [n for n, k in (("the colour counts", inv["counts_kept"]),
                           ("the colour set", inv["no_new_colour"]),
                           ("the shape", inv["shape_kept"])) if k]
    said = (f"background {r['background']}; every demonstration keeps "
            f"{', '.join(kept) if kept else 'none of colour counts, colour set and shape'}"
            f", so {r['skipped_by_invariant']} hypotheses were skipped by the "
            f"invariant reading (GLM.ColourInduction.count_perm) and "
            f"{r['tried']} tried")
    fig: Dict[str, object] = {
        "solver": "colour", "status": r["status"],
        "survivors": len(r["survivors"]), "background": r["background"],
        "skipped_by_invariant": r["skipped_by_invariant"],
        "tried": r["tried"], "demonstrations": len(pairs)}
    surv = r["survivors"]
    if r["status"] == "answered":
        fig["answer"] = grid_text(r["answer"])
        fig["tested"] = len(r["tested"])
        return True, (f"induce (colour): {grid_text(r['answer'])}, given by "
                      f"every one of the {len(surv)} hypotheses that fit all "
                      f"{len(pairs)} demonstrations ({_names(surv)}), "
                      f"{_names(r['tested'], 3)} tested; "
                      "GLM.ColourInduction.gate_sound makes it the true "
                      "rule's answer whenever the true rule is in the "
                      f"vocabulary [{said}]"), fig
    if r["status"] == "unread":
        need = "; ".join(f"{n} never read {', '.join(u)}"
                         for n, u in r["unread"].items())
        fig["unread"] = sorted(r["unread"])
        return False, (f"induce (colour): refused -- a fitted hypothesis that "
                       f"fits every demonstration needs, for this query, a "
                       f"parameter no demonstration showed ({need}) "
                       "(GLM.ColourInduction.unread_fitted_refuses); a "
                       "demonstration showing it would decide "
                       f"[{said}]"), fig
    if r["status"] == "ambiguous":
        fig["answers"] = r["answers"]
        return False, (f"induce (colour): refused -- the {len(surv)} "
                       f"hypotheses that fit every demonstration "
                       f"({_names(surv)}) disagree on the query, giving "
                       f"{len(r['answers'])} different answers; any answer "
                       "would be wrong for one of them; another "
                       f"demonstration would decide [{said}]"), fig
    if r["status"] == "untested":
        fig["candidate"] = grid_text(r["candidate"])
        return False, (f"induce (colour): refused -- the hypotheses that fit "
                       f"({_names(surv)}) agree on "
                       f"{grid_text(r['candidate'])}, but each is a fitted "
                       "family none of whose fits was tested on a "
                       "demonstration it was not fitted to (the span rule, "
                       "GLM.ColourInduction.untested_never_answers); one "
                       f"more demonstration would test it [{said}]"), fig
    if r["status"] == "undefined":
        return False, (f"induce (colour): refused -- the hypotheses that fit "
                       f"({_names(surv)}) give this query no output "
                       f"[{said}]"), fig
    return False, ("induce (colour): refused -- nothing in the vocabulary "
                   "(symmetries, gravity, crops, scaling, tiling, mirrors, "
                   "halves, symmetry completion, any two in turn, colour "
                   "maps, object recolouring, enclosed fill, half logic) fits "
                   f"every demonstration [{said}]"), fig


def induce_tool_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    """The whole of ``tool induce``: a colour or shape-changing task goes to
    the colour solver; every other task to
    :func:`pipeline_kit.induce_text`, exactly as before Phase 178."""
    pairs, query, _err = parse_task(arg)
    if pairs is not None and query is not None and \
            is_colour_task(pairs, query):
        return induce_colour_text(pairs, query)
    from . import pipeline_kit as pk
    return pk.induce_text(arg)


# ── tool arc: the stored ARC tasks ─────────────────────────────────────────

def _arc_dir():
    from ..constants import source_material_item
    return source_material_item("arc_agi_17") / "data" / "training"


def arc_names() -> List[str]:
    """The stored ARC tasks, in name order."""
    d = _arc_dir()
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


def arc_task_path(name: str):
    return _arc_dir() / f"{name.strip()}.json"


def arc_task(name: str) -> Optional[Dict[str, object]]:
    path = arc_task_path(name)
    if not name.strip() or not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _g(rows) -> Grid:
    return tuple(tuple(int(v) for v in row) for row in rows)


def arc_solve(task: Dict[str, object]) -> Dict[str, object]:
    """Solve every test input of a stored task from its training pairs, and
    grade each answer against the stored output (used for grading only).
    ``status``: ``right`` (every test answered right), ``wrong`` (some test
    answered wrong), ``refused`` (otherwise)."""
    pairs = [(_g(p["input"]), _g(p["output"])) for p in task["train"]]
    tests = []
    for t in task["test"]:
        q = _g(t["input"])
        r = solve(pairs, q)
        want = _g(t["output"]) if "output" in t else None
        grade = ("refused" if r["status"] != "answered" else
                 "right" if r["answer"] == want else "wrong")
        tests.append({"status": r["status"], "grade": grade,
                      "survivors": len(r["survivors"]),
                      "answer": r.get("answer")})
    grades = [t["grade"] for t in tests]
    status = ("wrong" if "wrong" in grades else
              "right" if grades and all(g == "right" for g in grades) else
              "refused")
    return {"status": status, "tests": tests,
            "demonstrations": len(pairs)}


def arc_text(name: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool arc NAME``: the stored task solved from its training pairs,
    every test answer graded against the stored output."""
    name = name.strip()
    task = arc_task(name)
    if task is None:
        known = arc_names()
        return False, (f"arc: refused -- no stored ARC task named {name!r}"
                       + (f"; the {len(known)} stored tasks include "
                          f"{', '.join(known[:5])}" if known else
                          "; no ARC tasks are stored")), \
            {"status": "unknown", "task": name}
    r = arc_solve(task)
    fig: Dict[str, object] = {
        "status": r["status"], "task": name,
        "tests": len(r["tests"]),
        "answered": sum(t["grade"] != "refused" for t in r["tests"]),
        "right": sum(t["grade"] == "right" for t in r["tests"]),
        "wrong": sum(t["grade"] == "wrong" for t in r["tests"])}
    parts = []
    for i, t in enumerate(r["tests"], 1):
        if t["grade"] == "refused":
            parts.append(f"test {i}: refused ({t['status']}, "
                         f"{t['survivors']} survivors)")
        else:
            parts.append(f"test {i}: {grid_text(t['answer'])} -- "
                         f"{t['grade'].upper()}")
    head = {"right": "RIGHT", "wrong": "WRONG",
            "refused": "refused"}[r["status"]]
    return r["status"] == "right", (
        f"arc {name}: {head} from {r['demonstrations']} training pairs by "
        f"the colour solver of tool induce; {'; '.join(parts)} (each answer "
        "graded against the stored output)"), fig
