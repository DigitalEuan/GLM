"""``glm_universal.reasoning.colour_induction_study`` -- the marks of part A
of ``studies/COLOUR_INDUCTION_STUDY.md`` (Phase 178): ``tool induce`` on
colour grids whose shape may change, and ``tool arc`` on the stored ARC
tasks.

*Created 22 October 2026.*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from ``MASTER_PLAN.md`` (Phase 178:
marks C1-C6, R1-R3, B, L, T; 1,080 in-vocabulary queries; 360 at three
demonstrations; the declared 90 %; ARC 2 of 50 right, 0 wrong; binary tasks
unchanged, 200 of 200), ``studies/GLM_ACADEMIC_PAPER.md`` §20.52 and
``STATUS.md`` §2.1 item 9, which record the marks' outcomes but not their
wording.  The wording below, the task families and their generator are this
reconstruction's, written into this module before its first run; they are
not the lost originals, and the figures they give are this generator's, not
the original's.*

What is measured
----------------
Twelve in-vocabulary task families on colour grids, thirty queries each at
two, three and four demonstrations (1,080 queries), and four families
outside the vocabulary (360 queries), drawn by a fixed integer recurrence
(:class:`pipeline_kit.Stream`): ``flip_h``, ``gravity_down``, ``crop``,
``scale2``, ``tile2x2``, ``mirror_h``, ``complete_h`` (symmetry
completion), ``flip_v_then_scale2`` (two steps), ``colour_map``,
``recolour_by_size``, ``enclosed_fill``, ``half_logic``; outside:
``translate_right``, ``extend_right``, ``hollow``, ``count_bar``.  Solvers:
**shipped** (the gate with the invariant reading, the span rule and the
unread rule); **no span rule** (a fitted family counts as tested by its fit);
**first take** (a survivor with an unread parameter is set aside, not a
refusal); **eager** (the first survivor with an output answers).  The
invariant reading is checked by reading every query again without it.  The
fifty stored ARC tasks are solved by ``tool arc``'s solver and every test
answer graded.

The marks (this reconstruction's wording, fixed before its first run)
---------------------------------------------------------------------
* **C1** shipped: 0 wrong on the twelve in-vocabulary families, every
  demonstration count;
* **C2** at three demonstrations at least 90 % of the in-vocabulary queries
  answered right;
* **C3** outside the vocabulary: 0 wrong, every demonstration count;
* **C4** the span rule earns its keep: without it at least one wrong answer
  (in or outside the vocabulary) that the shipped solver does not give;
* **C5** the invariant reading is lossless and does work: it skips at least
  one hypothesis, and reading every query without it changes no verdict and
  no answer;
* **C6** the gate earns its keep: the eager control gives at least one wrong
  in-vocabulary answer;
* **R1** ARC: 0 wrong of the stored tasks;
* **R2** ARC: more tasks right than the vision stack solves
  (:mod:`vision_stack`);
* **R3** ARC: at least 5 of the 50 right;
* **B** binary tasks unchanged: on 200 binary queries of the pipeline kit's
  families, the colour module's router and ``tool induce`` give exactly
  ``pipeline_kit.induce_text``'s verdict and answer;
* **L** ``ColourInduction.lean`` states its recorded theorems with no
  ``sorry`` (read through :func:`glm_universal.constants.lean_file`; not met
  when the file is missing);
* **T** ``tool induce`` answers a fixed colour task through the colour solver
  and ``tool arc 1e0a9b12`` is graded right.

Exactness
---------
Integers, tuples and strings only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .. import integrity
from . import colour_induction as ci
from . import pipeline_kit as pk

__all__ = ["DATA_PATH", "QUERIES", "DEMOS", "IN_VOCAB", "OUT_VOCAB",
           "task", "synthetic", "arc", "binary", "compute", "measure",
           "write_measurements", "measurements", "state", "current",
           "colour_induction_report"]

_HERE = Path(__file__).resolve().parent
DATA_PATH: Path = _HERE / "_data" / "colour_induction_study.json"

QUERIES = 30
DEMOS: Tuple[int, ...] = (2, 3, 4)
BINARY_QUERIES = 200

_SOURCES: Tuple[str, ...] = (
    "reasoning/colour_induction_study.py",
    "reasoning/colour_induction.py",
    "reasoning/pipeline_kit.py",
    "reasoning/vision_stack.py",
    "runtime/toolbox.py",
)

Grid = ci.Grid

IN_VOCAB: Tuple[str, ...] = (
    "flip_h", "gravity_down", "crop", "scale2", "tile2x2", "mirror_h",
    "complete_h", "flip_v_then_scale2", "colour_map", "recolour_by_size",
    "enclosed_fill", "half_logic")
OUT_VOCAB: Tuple[str, ...] = ("translate_right", "extend_right", "hollow",
                              "count_bar")

TOOL_COLOUR = ("tool induce 120/300 -> 340/500 ; 210/003 -> 430/005 ? "
               "210/030")
TOOL_COLOUR_TRUE = "430/050"
TOOL_ARC = "tool arc 1e0a9b12"


# ── the generator ──────────────────────────────────────────────────────────

def _blank(h: int, w: int) -> List[List[int]]:
    return [[0] * w for _ in range(h)]


def _freeze(g: List[List[int]]) -> Grid:
    return tuple(tuple(r) for r in g)


def _colour(s: pk.Stream) -> int:
    return 1 + s.below(9)


def _sparse(s: pk.Stream, h: int, w: int, k_lo: int = 2, k_hi: int = 5
            ) -> Grid:
    """A background-0 grid with a few coloured cells (at most a third of
    the grid, so 0 stays the background)."""
    g = _blank(h, w)
    k = min(s.between(k_lo, k_hi), (h * w) // 3)
    placed = 0
    while placed < k:
        r, c = s.below(h), s.below(w)
        if g[r][c] == 0:
            g[r][c] = _colour(s)
            placed += 1
    return _freeze(g)


def _small(s: pk.Stream) -> Grid:
    """A small grid, about half coloured, for scaling, tiling, mirrors."""
    h, w = s.between(2, 3), s.between(2, 3)
    return _freeze([[(_colour(s) if s.below(2) else 0) for _ in range(w)]
                    for _ in range(h)])


def _object_on_field(s: pk.Stream) -> Grid:
    h, w = s.between(5, 7), s.between(5, 7)
    oh, ow = s.between(2, 3), s.between(2, 3)
    top, left = s.below(h - oh + 1), s.below(w - ow + 1)
    g = _blank(h, w)
    for r in range(oh):
        for c in range(ow):
            g[top + r][left + c] = _colour(s)
    return _freeze(g)


def _symmetric_with_holes(s: pk.Stream) -> Grid:
    """A left-right symmetric sparse pattern with some coloured cells of one
    side removed (each removed cell's mirror image kept)."""
    h, w = s.between(3, 5), s.between(4, 6)
    g = _blank(h, w)
    for r in range(h):
        for c in range((w + 1) // 2):
            if s.below(3) == 0:
                g[r][c] = g[r][w - 1 - c] = _colour(s)
    cells = [(r, c) for r in range(h) for c in range(w // 2)
             if g[r][c] and c != w - 1 - c]
    for r, c in cells:
        if s.below(2):
            if s.below(2):
                g[r][c] = 0
            else:
                g[r][w - 1 - c] = 0
    return _freeze(g)


def _dense(s: pk.Stream, palette: List[int]) -> Grid:
    h, w = s.between(2, 4), s.between(2, 4)
    return _freeze([[palette[s.below(len(palette))] for _ in range(w)]
                    for _ in range(h)])


_SHAPES: Tuple[Tuple[Tuple[int, int], ...], ...] = (
    ((0, 0),), ((0, 0), (0, 1)), ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (0, 2)), ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)), ((0, 0), (0, 1), (0, 2), (0, 3)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
)


def _objects(s: pk.Stream, colour: int) -> Grid:
    """Two to four objects of one colour, none touching another."""
    h, w = s.between(6, 7), s.between(6, 7)
    g = _blank(h, w)
    want, tries = s.between(2, 4), 0
    placed = 0
    while placed < want and tries < 60:
        tries += 1
        shape = _SHAPES[s.below(len(_SHAPES))]
        top, left = s.below(h), s.below(w)
        cells = [(top + a, left + b) for a, b in shape]
        if any(r >= h or c >= w for r, c in cells):
            continue
        near = {(r + dr, c + dc) for r, c in cells
                for dr, dc in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))}
        if any(0 <= r < h and 0 <= c < w and g[r][c] for r, c in near):
            continue
        for r, c in cells:
            g[r][c] = colour
        placed += 1
    return _freeze(g)


def _outlines(s: pk.Stream, colour: int) -> Grid:
    h, w = s.between(5, 7), s.between(5, 7)
    g = _blank(h, w)
    rh, rw = s.between(3, h), s.between(3, w)
    top, left = s.below(h - rh + 1), s.below(w - rw + 1)
    for c in range(left, left + rw):
        g[top][c] = g[top + rh - 1][c] = colour
    for r in range(top, top + rh):
        g[r][left] = g[r][left + rw - 1] = colour
    return _freeze(g)


def _halves_input(s: pk.Stream, a: int, b: int, divider: int) -> Grid:
    h, k = 3, 3
    rows = []
    for _ in range(h):
        left = [a if s.below(2) else 0 for _ in range(k)]
        right = [b if s.below(2) else 0 for _ in range(k)]
        rows.append(tuple(left + [divider] + right))
    return tuple(rows)


def _filled_rects(s: pk.Stream, colour: int) -> Grid:
    h, w = s.between(5, 7), s.between(5, 7)
    g = _blank(h, w)
    rh, rw = s.between(3, h), s.between(3, w)
    top, left = s.below(h - rh + 1), s.below(w - rw + 1)
    for r in range(top, top + rh):
        for c in range(left, left + rw):
            g[r][c] = colour
    return _freeze(g)


Rule = Callable[[Grid], Grid]


def _make(name: str, s: pk.Stream) -> Tuple[Callable[[pk.Stream], Grid], Rule]:
    """The input sampler and the true rule of one task of a family (the rule's
    parameters drawn once per task)."""
    bg = 0
    if name == "flip_h":
        return (lambda t: _sparse(t, t.between(3, 5), t.between(3, 5)),
                lambda g: tuple(tuple(reversed(r)) for r in g))
    if name == "gravity_down":
        return (lambda t: _sparse(t, t.between(3, 5), t.between(3, 5)),
                lambda g: ci.gravity(g, bg, "down"))
    if name == "crop":
        return _object_on_field, lambda g: ci.crop(g, bg)
    if name == "scale2":
        return _small, lambda g: ci.scale(g, 2)
    if name == "tile2x2":
        return _small, lambda g: ci.tile(g, 2, 2)
    if name == "mirror_h":
        return _small, lambda g: tuple(tuple(r) + tuple(reversed(r)) for r in g)
    if name == "complete_h":
        return _symmetric_with_holes, lambda g: ci.complete(g, bg, "h")
    if name == "flip_v_then_scale2":
        return _small, lambda g: ci.scale(tuple(reversed(g)), 2)
    if name == "colour_map":
        palette = sorted({_colour(s) for _ in range(4)} | {0})
        image = {c: s.below(10) for c in palette}
        return (lambda t: _dense(t, palette),
                lambda g: tuple(tuple(image[v] for v in r) for r in g))
    if name == "recolour_by_size":
        colour = _colour(s)
        classes = ("1", "2-3", "4-7")
        image = {k: _colour(s) for k in classes}

        def recolour(g: Grid) -> Grid:
            out = [list(r) for r in g]
            for col, cells in ci.components(g, bg):
                k = ci.size_bucket(len(cells))
                for r, c in cells:
                    out[r][c] = image.get(k, col)
            return _freeze(out)
        return (lambda t: _objects(t, colour)), recolour
    if name == "enclosed_fill":
        colour, fill = _colour(s), _colour(s)

        def filled(g: Grid) -> Grid:
            out = [list(r) for r in g]
            for r, c in ci._enclosed(g, bg):
                out[r][c] = fill
            return _freeze(out)
        return (lambda t: _outlines(t, colour)), filled
    if name == "half_logic":
        a, b, divider, mark = _colour(s), _colour(s), 5, _colour(s)
        op = ("and", "or", "xor", "left_only")[s.below(4)]

        def logic(g: Grid) -> Grid:
            out = []
            for row in g:
                left, right = row[:3], row[4:]
                cells = []
                for u, v in zip(left, right):
                    p, q = u != 0, v != 0
                    on = {"and": p and q, "or": p or q, "xor": p != q,
                          "left_only": p and not q}[op]
                    cells.append(mark if on else 0)
                out.append(tuple(cells))
            return tuple(out)
        return (lambda t: _halves_input(t, a, b, divider)), logic
    if name == "translate_right":
        def shifted(g: Grid) -> Grid:
            return tuple((0,) + tuple(r[:-1]) for r in g)

        def sample(t: pk.Stream) -> Grid:
            g = _sparse(t, t.between(3, 5), t.between(4, 5))
            return tuple(tuple(r[:-1]) + (0,) for r in g)
        return sample, shifted
    if name == "extend_right":
        def extended(g: Grid) -> Grid:
            out = []
            for r in g:
                row, cur = [], 0
                for v in r:
                    cur = v if v else cur
                    row.append(cur)
                out.append(tuple(row))
            return tuple(out)

        def sample(t: pk.Stream) -> Grid:
            h, w = t.between(3, 5), t.between(4, 6)
            g = _blank(h, w)
            for r in range(h):
                if t.below(2):
                    g[r][t.below(w - 1)] = _colour(t)
            return _freeze(g)
        return sample, extended
    if name == "hollow":
        colour = _colour(s)

        def hollowed(g: Grid) -> Grid:
            h, w = len(g), len(g[0])
            out = [list(r) for r in g]
            for r in range(1, h - 1):
                for c in range(1, w - 1):
                    if all(g[rr][cc] for rr, cc in ((r + 1, c), (r - 1, c),
                                                    (r, c + 1), (r, c - 1))):
                        out[r][c] = 0
            return _freeze(out)
        return (lambda t: _filled_rects(t, colour)), hollowed
    if name == "count_bar":
        colour = _colour(s)

        def bar(g: Grid) -> Grid:
            k = len(ci.components(g, bg))
            return ((colour,) * k,)

        def sample(t: pk.Stream) -> Grid:
            h, w = t.between(4, 6), t.between(4, 6)
            g = _blank(h, w)
            for _ in range(t.between(1, 4)):
                g[t.below(h)][t.below(w)] = colour
            return _freeze(g)
        return sample, bar
    raise KeyError(name)


def task(name: str, seed: int, demos: int):
    """``(pairs, (query, truth))`` for one task: ``demos`` demonstrations
    with distinct inputs, and a query input distinct from them."""
    s = pk.Stream(seed * 7919 + sum(ord(c) for c in name) + 178)
    sample, rule = _make(name, s)
    xs: List[Grid] = []
    tries = 0
    while len(xs) < demos + 1 and tries < 200:
        tries += 1
        x = sample(s)
        if x not in xs and rule(x) is not None:
            xs.append(x)
    pairs = [(x, rule(x)) for x in xs[:demos]]
    q = xs[demos]
    return pairs, (q, rule(q))


# ── the synthetic measurement ──────────────────────────────────────────────

def _blank_tally() -> Dict[str, int]:
    return {"queries": 0, "right": 0, "wrong": 0, "refused": 0}


def _grade(r: Dict[str, object], truth: Grid) -> str:
    if r["status"] != "answered":
        return "refused"
    return "right" if r["answer"] == truth else "wrong"


SOLVERS: Dict[str, Dict[str, bool]] = {
    "shipped": {},
    "no_span_rule": {"span_rule": False},
    "first_take": {"unread_rule": False},
    "eager": {"gate": False},
}


def synthetic() -> Dict[str, object]:
    sides = ("in", "out")
    totals = {s: {side: _blank_tally() for side in sides} for s in SOLVERS}
    by_demos = {str(d): {side: _blank_tally() for side in sides}
                for d in DEMOS}
    families = {f: {s: _blank_tally() for s in SOLVERS}
                for f in IN_VOCAB + OUT_VOCAB}
    statuses: Dict[str, int] = {}
    invariant = {"skipped": 0, "changed": [], "queries": 0}
    span_prevented: List[str] = []
    span_cost = 0
    first_take_wrong: List[str] = []
    for fam in IN_VOCAB + OUT_VOCAB:
        side = "in" if fam in IN_VOCAB else "out"
        for d in DEMOS:
            for q in range(QUERIES):
                pairs, (qx, qy) = task(fam, q + 1000 * d, d)
                reading = ci.read_task(pairs, qx)
                res = {s: ci.verdict(reading, **kw)
                       for s, kw in SOLVERS.items()}
                plain = ci.verdict(ci.read_task(pairs, qx, invariant=False))
                invariant["queries"] += 1
                invariant["skipped"] += reading["skipped_by_invariant"]
                sh = res["shipped"]
                if (plain["status"], plain.get("answer")) != \
                        (sh["status"], sh.get("answer")):
                    invariant["changed"].append(f"{fam}/{d}/{q}")
                for s, r in res.items():
                    g = _grade(r, qy)
                    totals[s][side]["queries"] += 1
                    totals[s][side][g] += 1
                    families[fam][s]["queries"] += 1
                    families[fam][s][g] += 1
                g = _grade(sh, qy)
                by_demos[str(d)][side]["queries"] += 1
                by_demos[str(d)][side][g] += 1
                statuses[sh["status"]] = statuses.get(sh["status"], 0) + 1
                gn = _grade(res["no_span_rule"], qy)
                if gn == "wrong" and g != "wrong":
                    span_prevented.append(f"{fam}/{d}/{q}")
                if gn == "right" and g == "refused":
                    span_cost += 1
                if _grade(res["first_take"], qy) == "wrong":
                    first_take_wrong.append(f"{fam}/{d}/{q}")
    return {"totals": totals, "by_demos": by_demos, "families": families,
            "statuses": statuses, "invariant": invariant,
            "span_rule": {"prevented": span_prevented, "cost": span_cost},
            "first_take_wrong": first_take_wrong}


# ── ARC ────────────────────────────────────────────────────────────────────

def _vision_solved(tasks: Dict[str, Dict[str, object]]) -> List[str]:
    """The stored tasks whose first test the vision stack solves, run on the
    same task files (its own data path is not consulted)."""
    from . import vision_stack as vs
    solved = []
    for name, t in sorted(tasks.items()):
        train = tuple((vs._grid(p["input"]), vs._grid(p["output"]))
                      for p in t["train"])
        first = t["test"][0]
        puzzle = vs.Puzzle(name=name, train=train,
                           test_input=vs._grid(first["input"]),
                           test_output=(vs._grid(first["output"])
                                        if "output" in first else None))
        if vs.attempt(puzzle).solved_test:
            solved.append(name)
    return solved


def arc() -> Dict[str, object]:
    names = ci.arc_names()
    tasks = {n: ci.arc_task(n) for n in names}
    rows = {n: ci.arc_solve(tasks[n])["status"] for n in names}
    right = sorted(n for n, s in rows.items() if s == "right")
    wrong = sorted(n for n, s in rows.items() if s == "wrong")
    return {"tasks": len(names), "right": right, "wrong": wrong,
            "refused": len(names) - len(right) - len(wrong),
            "vision_stack_solved": _vision_solved(tasks) if names else []}


# ── binary tasks unchanged ─────────────────────────────────────────────────

def _binary_arg(name: str, q: int) -> str:
    demos = [pk.sample(name, 5000 * q + i) for i in range(3)]
    x, _y = pk.sample(name, 5000 * q + 999)
    return (" ; ".join(f"{pk.grid_text(a)} -> {pk.grid_text(b)}"
                       for a, b in demos) + f" ? {pk.grid_text(x)}")


def binary() -> Dict[str, object]:
    from ..runtime.toolbox import run_tool
    names = sorted(pk.FAMILIES)
    same_router = same_tool = 0
    routed_to_colour = 0
    differ: List[str] = []
    for q in range(BINARY_QUERIES):
        name = names[q % len(names)]
        arg = _binary_arg(name, q // len(names))
        pairs, query, _ = ci.parse_task(arg)
        if pairs is not None and ci.is_colour_task(pairs, query):
            routed_to_colour += 1
        ok0, _t0, f0 = pk.induce_text(arg)
        ok1, _t1, f1 = ci.induce_tool_text(arg)
        t = run_tool(f"tool induce {arg}")
        want = (ok0, f0.get("status"), f0.get("answer"))
        if (ok1, f1.get("status"), f1.get("answer")) == want:
            same_router += 1
        if (t.ok, t.figures.get("status"), t.figures.get("answer")) == want:
            same_tool += 1
        else:
            differ.append(f"{name}/{q}")
    return {"queries": BINARY_QUERIES, "same_router": same_router,
            "same_tool": same_tool, "routed_to_colour": routed_to_colour,
            "differ": differ[:20]}


# ── Lean and the tool ──────────────────────────────────────────────────────

def _lean() -> Dict[str, object]:
    from ..constants import LEAN_HOLDING_DIR, lean_file
    path = lean_file(ci.LEAN_FILE)
    present = path.is_file()
    text = path.read_text(encoding="utf-8") if present else ""
    found = [t for t in ci.LEAN_THEOREMS if f"theorem {t}" in text]
    return {"file": ci.LEAN_FILE, "present": present,
            "declared": len(ci.LEAN_THEOREMS), "theorems": len(found),
            "sorry": text.count("sorry"),
            "held": present and LEAN_HOLDING_DIR in path.parents}


def _tool() -> Dict[str, object]:
    from ..runtime.toolbox import run_tool
    c = run_tool(TOOL_COLOUR)
    a = run_tool(TOOL_ARC)
    return {"colour_ok": c.ok, "colour_solver": c.figures.get("solver"),
            "colour_answer": c.figures.get("answer"),
            "arc_ok": a.ok, "arc_status": a.figures.get("status")}


# ── the report ─────────────────────────────────────────────────────────────

def compute() -> Dict[str, object]:
    report = {"synthetic": synthetic(), "arc": arc(), "binary": binary(),
              "lean": _lean(), "tool": _tool(), "queries": QUERIES,
              "demos": list(DEMOS), "in_vocab": list(IN_VOCAB),
              "out_vocab": list(OUT_VOCAB)}
    marks = _marks(report)
    report["marks"] = marks
    report["met"] = sum(marks.values())
    report["taken"] = len(marks)
    return report


def _marks(r: Dict[str, object]) -> Dict[str, bool]:
    s = r["synthetic"]
    t = s["totals"]
    three = s["by_demos"]["3"]["in"]
    a = r["arc"]
    b = r["binary"]
    lean = r["lean"]
    tool = r["tool"]
    return {
        "C1": t["shipped"]["in"]["queries"] > 0
        and t["shipped"]["in"]["wrong"] == 0,
        "C2": three["queries"] > 0
        and 100 * three["right"] >= 90 * three["queries"],
        "C3": t["shipped"]["out"]["queries"] > 0
        and t["shipped"]["out"]["wrong"] == 0,
        "C4": len(s["span_rule"]["prevented"]) > 0,
        "C5": s["invariant"]["skipped"] > 0 and not s["invariant"]["changed"],
        "C6": t["eager"]["in"]["wrong"] > 0,
        "R1": a["tasks"] > 0 and not a["wrong"],
        "R2": a["tasks"] > 0
        and len(a["right"]) > len(a["vision_stack_solved"]),
        "R3": len(a["right"]) >= 5,
        "B": b["same_router"] == b["queries"] and b["same_tool"] == b["queries"],
        "L": (lean["present"] and lean["theorems"] == lean["declared"]
              and lean["sorry"] == 0),
        "T": (tool["colour_ok"] and tool["colour_solver"] == "colour"
              and tool["colour_answer"] == TOOL_COLOUR_TRUE
              and tool["arc_ok"] and tool["arc_status"] == "right"),
    }


def _plain(x):
    if isinstance(x, dict):
        return {str(k): _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def module_digest() -> str:
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / n for n in sorted(set(_SOURCES))],
                                 root)


def measure() -> Dict[str, object]:
    report = compute()
    report["source_digest"] = module_digest()
    return report


_cache: Optional[Dict[str, object]] = None


def write_measurements(path: Optional[Path] = None) -> Path:
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(_plain(measure()), indent=1, sort_keys=True,
                                 ensure_ascii=False) + "\n", encoding="utf-8")
    global _cache
    _cache = None
    return target


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return _cache


def state() -> Dict[str, object]:
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    fresh = stored.get("source_digest") == live
    return {"present": True, "fresh": fresh,
            "verdict": "current" if fresh else "stale",
            "live_digest": live, "stored_digest": stored.get("source_digest")}


def current() -> Optional[Dict[str, object]]:
    return measurements() if state()["fresh"] else None


def colour_induction_report() -> Dict[str, object]:
    """The stored marks, or why there are none."""
    stored = current()
    if stored is None:
        return {"available": False, "reason": (
            f"the stored measurement is {state()['verdict']}; re-take it "
            f"with python3 -m glm_universal.tools colour-induction --write")}
    return dict(stored, available=True)
