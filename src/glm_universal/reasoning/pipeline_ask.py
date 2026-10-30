"""``glm_universal.reasoning.pipeline_ask`` -- when ``tool induce`` refuses,
ask for the example that would settle it (Phase 176).

*Created 21 October 2026.*

``tool induce`` (Phase 175) refuses when two hypotheses that fit every
demonstration disagree on the query; ``ambiguous_forces_refusal`` makes that
refusal forced.  ``STATUS.md`` item 9 asked for the next step: *choose the
input that would separate the disagreeing hypotheses and ask for its output*.
This module does that.

The choice
----------
:func:`separating_input` looks over a declared pool of inputs of the query's
shape (every one-cell change of the query and of each demonstration input,
and seeded random grids with the query's weight, each demonstration input's
weight, and any weight), never the query itself or a demonstration input.  An
input is usable when every surviving hypothesis gives it an output and at
least two outputs differ (it *separates*).  Among usable inputs it takes the
one whose worst reply leaves the fewest distinct answers to the query, then
the fewest survivors, then the first in pool order -- so when it can, it asks
for an example after which the query is decided whatever the reply.

The loop
--------
:func:`ask_loop` solves; while the result is ``ambiguous`` and fewer than
``max_asks`` asks have been made, it asks for the chosen input, takes the
reply from an oracle (in the study, the task family's true rule; in use, the
owner), adds it as a demonstration and solves again.

``PipelineAsk.lean`` proves, for any class: after the reply to a separating
input the two hypotheses it separated cannot both still fit
(``separating_demo_removes``), the survivors drop by at least one
(``separating_strict_shrink``), at most ``|H| - 1`` separating asks can be
made when the true rule is in the class (``asks_bounded``), and whatever the
gate then answers is the true rule's (``ask_then_sound``).  It does not prove
that one ask suffices or that the pool holds a separating input; the study
(``studies/PIPELINE_ASK_STUDY.md``) measures both.

Exactness
---------
Integers, tuples and strings only.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence, Tuple

from . import pipeline_kit as pk

__all__ = ["LEAN_FILE", "LEAN_THEOREMS", "TRUE_RULES", "true_rule",
           "candidate_pool", "survivors", "separating_input", "ask_loop",
           "ask_text"]

Grid = pk.Grid
Pairs = Sequence[Tuple[Grid, Grid]]

LEAN_FILE = "RequestProject/GLM/PipelineAsk.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "separating_demo_removes", "truth_survives_asks", "consistentIn_cons",
    "separating_strict_shrink", "asks_shrink", "asks_bounded",
    "ask_then_sound")

#: Seeded random grids per weight class in the pool.
RANDOM_PER_CLASS = 24


# ── the true rule of each study family (the oracle in the study) ──────────

def _perm(name: str) -> Callable[[int, int], Callable[[Grid], Optional[Grid]]]:
    return lambda h, w: pk._perm_rule(name, h, w)


def _op(f: Callable[[Grid], Optional[Grid]]):
    return lambda h, w: f


def _then(a, b):
    def rule(h: int, w: int):
        fa, fb = a(h, w), b(h, w)
        return lambda g: (lambda m: None if m is None else fb(m))(fa(g))
    return rule


#: name -> rule(h, w).  ``translate`` moves the 2x2 block one cell down and
#: right and keeps the last row: the permutation ``shift(1,1)_keep_last_row``.
TRUE_RULES: Dict[str, Callable[[int, int], Callable[[Grid], Optional[Grid]]]] = {
    "toggle": _op(pk._complement),
    "translate": _perm("shift(1,1)_keep_last_row"),
    "reflect_v": _perm("reflect_v"),
    "flood_fill": _op(pk.fill_enclosed),
    "bfs_shortest": _op(pk.path_vh),
    "reflect_h": _perm("reflect_h"),
    "rotate180": _perm("rotate180"),
    "path_hv": _op(pk.path_hv),
    "reflect_v_then_toggle": _then(_perm("reflect_v"), _op(pk._complement)),
    "fill_then_reflect_h": _then(_op(pk.fill_enclosed), _perm("reflect_h")),
    "path_then_rotate180": _then(_op(pk.path_vh), _perm("rotate180")),
    "string_reverse": _perm("reflect_v"),
    "string_rotate": _perm("shift(0,1)"),
    "string_complement": _op(pk._complement),
    "string_reverse_complement": _then(_perm("reflect_v"), _op(pk._complement)),
}


def true_rule(name: str) -> Callable[[Grid], Optional[Grid]]:
    _group, h, w, _gen = pk.FAMILIES[name]
    return TRUE_RULES[name](h, w)


# ── the pool and the choice ────────────────────────────────────────────────

def _flips(g: Grid) -> List[Grid]:
    h, w = len(g), len(g[0])
    cells = pk.flatten(g)
    out = []
    for i in range(h * w):
        c = list(cells)
        c[i] ^= 1
        out.append(pk.unflatten(c, w))
    return out


def _random_with_weight(s: pk.Stream, h: int, w: int, k: Optional[int]) -> Grid:
    n = h * w
    if k is None:
        return pk.unflatten(s.bit_list(n), w)
    idx = list(range(n))
    for i in range(n - 1, 0, -1):          # Fisher-Yates with the stream
        j = s.below(i + 1)
        idx[i], idx[j] = idx[j], idx[i]
    cells = [0] * n
    for i in idx[:k]:
        cells[i] = 1
    return pk.unflatten(cells, w)


def candidate_pool(pairs: Pairs, query: Grid, seed: int = 176) -> List[Grid]:
    """The declared pool, in a fixed order, without repeats, never the query
    or a demonstration input."""
    h, w = len(query), len(query[0])
    seen = {query} | {x for x, _ in pairs}
    pool: List[Grid] = []

    def add(g: Grid) -> None:
        if g not in seen:
            seen.add(g)
            pool.append(g)

    for g in [query] + [x for x, _ in pairs]:
        for f in _flips(g):
            add(f)
    s = pk.Stream(seed)
    weights: List[Optional[int]] = [sum(pk.flatten(query))]
    weights += [sum(pk.flatten(x)) for x, _ in pairs]
    weights.append(None)
    done = set()
    for k in weights:
        if k in done:
            continue
        done.add(k)
        for _ in range(RANDOM_PER_CLASS):
            add(_random_with_weight(s, h, w, k))
    return pool


def survivors(pairs: Pairs, query: Grid) -> List[pk.Hypothesis]:
    """The hypotheses of the tier the shipped solver reads (the first tier
    with a consistent member), as objects."""
    h, w = len(query), len(query[0])
    tiers, _stats = pk.tiers_for(pairs, h, w)
    for build in tiers:
        live = [hy for hy in build() if pk._consistent(hy, pairs)]
        if live:
            return live
    return []


def separating_input(pairs: Pairs, query: Grid,
                     live: Optional[List[pk.Hypothesis]] = None,
                     exclude: Sequence[Grid] = ()
                     ) -> Optional[Dict[str, object]]:
    """The input to ask about, with its score, or ``None`` when the pool has
    no input that separates the survivors."""
    if live is None:
        live = survivors(pairs, query)
    if len(live) < 2:
        return None
    on_query = [hy(query) for hy in live]
    best = None
    banned = set(exclude)
    for x in candidate_pool(pairs, query):
        if x in banned:
            continue
        outs = [hy(x) for hy in live]
        if any(o is None for o in outs) or len(set(outs)) < 2:
            continue
        blocks: Dict[Grid, List[int]] = {}
        for i, o in enumerate(outs):
            blocks.setdefault(o, []).append(i)
        worst_answers = max(len({on_query[i] for i in b}) for b in blocks.values())
        worst_size = max(len(b) for b in blocks.values())
        key = (worst_answers, worst_size)
        if best is None or key < best[0]:
            best = (key, x, len(blocks))
    if best is None:
        return None
    (worst_answers, worst_size), x, nblocks = best
    return {"input": x, "blocks": nblocks, "worst_answers": worst_answers,
            "worst_survivors": worst_size, "survivors": len(live),
            "decides": worst_answers == 1}


def ask_loop(pairs: Pairs, query: Grid,
             oracle: Callable[[Grid], Optional[Grid]],
             max_asks: int = 3) -> Dict[str, object]:
    """Solve, and while the survivors disagree ask the oracle for the output
    of the separating input, up to ``max_asks`` times."""
    demos = list(pairs)
    asks: List[Dict[str, object]] = []
    undefined: List[Grid] = []
    r = pk.solve(demos, query)
    while r["status"] == "ambiguous" and len(asks) < max_asks:
        live = survivors(demos, query)
        choice = separating_input(demos, query, live, exclude=undefined)
        if choice is None:
            break
        x = choice["input"]
        y = oracle(x)
        if y is None:                      # the reply: no output there
            undefined.append(x)
            continue
        before = [hy.name for hy in live]
        demos.append((x, y))
        r = pk.solve(demos, query)
        asks.append({"input": pk.grid_text(x), "reply": pk.grid_text(y),
                     "before": before, "after": list(r.get("survivors", [])),
                     "decides": choice["decides"]})
    return {"status": r["status"], "answer": r.get("answer"), "asks": asks,
            "survivors": list(r.get("survivors", []))}


def ask_text(pairs: Pairs, query: Grid) -> Tuple[str, Optional[Dict[str, object]]]:
    """The sentence ``tool induce`` adds to an ambiguous refusal."""
    choice = separating_input(pairs, query)
    if choice is None:
        return ("no grid of the declared pool separates the fitting "
                "hypotheses, so no single further example is suggested"), None
    x = pk.grid_text(choice["input"])
    if choice["decides"]:
        tail = "whatever its output, the query is then decided"
    else:
        tail = (f"its output leaves at most {choice['worst_survivors']} of the "
                f"{choice['survivors']} fitting hypotheses")
    return (f"to settle it, give the output for {x} -- the fitting hypotheses "
            f"split {choice['blocks']} ways there, and {tail} "
            "(GLM.PipelineAsk.separating_strict_shrink)"), choice
