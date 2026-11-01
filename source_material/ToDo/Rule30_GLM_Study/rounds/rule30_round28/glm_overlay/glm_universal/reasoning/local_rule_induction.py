"""``glm_universal.reasoning.local_rule_induction`` -- local rules on grids, with sound refusal.

Rule 30 study, Round 28.  The 2-D generalisation of ``wheel_induction.py`` (Round 10): a rule
is a function of what a *reader* (the observer ``Y``) sees around a cell -- the cell, its
neighbours, or the first colour seen looking in a direction -- and the demonstrations are read
with the GLM's discipline: keep every surviving rule, answer only when every survivor agrees,
otherwise refuse and say why.  Proved in Lean (``RequestProject/GLM/Rule30/LocalRuleInduction.lean``):

* ``reproduces_iff_agrees`` -- a rule reproduces the demonstrations iff it agrees with them on
  every key they show;
* ``determined_iff_covered`` -- all surviving rules agree on a query cell iff its key has been
  seen (with at least two colours available);
* ``clash_refutes`` -- two demonstration cells with equal keys and different outputs refute the
  reader for good: no rule over it reproduces the demonstrations, however many more arrive.

Outputs may also be read *relative* to the reader (copy slot ``i``); the same three facts hold
with "rule" meaning "key -> encoding" and are checked by computing all surviving encodings.

The ladder of readers is fixed in advance (cheapest first); test outputs are never consulted.
Exact integers only; no float, no randomness.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from typing import Callable, Dict, Hashable, List, Optional, Sequence, Tuple

Grid = List[List[int]]
Reader = Callable[[Grid, int, int], Hashable]

DEFAULT_DIR = "arc_agi_17/data/training"  # relative to the directory holding GLM.py
BACKGROUND = 0


def _at(g: Grid, r: int, c: int) -> int:
    if 0 <= r < len(g) and 0 <= c < len(g[0]):
        return g[r][c]
    return -1


def _nb(g: Grid, r: int, c: int, dirs) -> Tuple[int, ...]:
    return tuple(_at(g, r + dr, c + dc) for dr, dc in dirs)


def _mask(vals) -> Tuple[int, ...]:
    """Colour-blind shape: 0 background, 1 coloured, 2 off-grid."""
    return tuple(2 if v < 0 else (0 if v == BACKGROUND else 1) for v in vals)


DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIRS8 = DIRS4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))
BLOCK = lambda k: tuple((i, j) for i in range(-k, k + 1) for j in range(-k, k + 1))


def _ray(g: Grid, r: int, c: int, dr: int, dc: int) -> int:
    """First non-background colour seen from (r, c) looking along (dr, dc); -1 if none."""
    r, c = r + dr, c + dc
    while 0 <= r < len(g) and 0 <= c < len(g[0]):
        if g[r][c] != BACKGROUND:
            return g[r][c]
        r, c = r + dr, c + dc
    return -1


def _rays(g, r, c, dirs):
    return tuple(_ray(g, r, c, dr, dc) for dr, dc in dirs)


# A reader returns (key, slots): the key the rule is a function of, and the colours the output
# may copy ("slot i").  An output is recorded as every encoding that produces it: the absolute
# colour, or any slot holding that colour.
def r_cell(g, r, c):
    return g[r][c], (g[r][c],)


def r_mask4(g, r, c):
    nb = _nb(g, r, c, DIRS4)
    return (g[r][c], _mask(nb)), (g[r][c],) + nb


def r_mask8(g, r, c):
    nb = _nb(g, r, c, DIRS8)
    return (g[r][c], _mask(nb)), (g[r][c],) + nb


def r_vn1(g, r, c):
    nb = _nb(g, r, c, DIRS4)
    return (g[r][c],) + nb, (g[r][c],) + nb


def r_moore1(g, r, c):
    nb = _nb(g, r, c, DIRS8)
    return (g[r][c],) + nb, (g[r][c],) + nb


def r_raymask4(g, r, c):
    rs = _rays(g, r, c, DIRS4)
    return (g[r][c], _mask(rs)), (g[r][c],) + rs


def r_raymask8(g, r, c):
    rs = _rays(g, r, c, DIRS8)
    return (g[r][c], _mask(rs)), (g[r][c],) + rs


def r_between(g, r, c):
    """Is the cell between two equal colours, vertically / horizontally?"""
    n, s, w, e = _rays(g, r, c, DIRS4)
    return (g[r][c], n >= 0 and n == s, w >= 0 and w == e), (g[r][c], n, s, w, e)


def r_rays4(g, r, c):
    rs = _rays(g, r, c, DIRS4)
    return (g[r][c],) + rs, (g[r][c],) + rs


def r_rays8(g, r, c):
    rs = _rays(g, r, c, DIRS8)
    return (g[r][c],) + rs, (g[r][c],) + rs


def r_rowcol(g, r, c):
    return (g[r][c], frozenset(g[r]), frozenset(row[c] for row in g)), (g[r][c],)


def r_row3(g, r, c):
    """The Rule 30 wheel neighbourhood read along the row: (west, centre, east)."""
    w, e = _at(g, r, c - 1), _at(g, r, c + 1)
    return (w, g[r][c], e), (g[r][c], w, e)


def r_col3(g, r, c):
    """The same neighbourhood read along the column: (north, centre, south)."""
    n, s = _at(g, r - 1, c), _at(g, r + 1, c)
    return (n, g[r][c], s), (g[r][c], n, s)


def r_tot4(g, r, c):
    """Totalistic: the cell and how many of its 4 neighbours are coloured."""
    nb = _nb(g, r, c, DIRS4)
    return (g[r][c], sum(1 for v in nb if v > 0)), (g[r][c],) + nb


def r_tot8(g, r, c):
    """Totalistic: the cell and how many of its 8 neighbours are coloured."""
    nb = _nb(g, r, c, DIRS8)
    return (g[r][c], sum(1 for v in nb if v > 0)), (g[r][c],) + nb


def r_mask_block2(g, r, c):
    nb = _nb(g, r, c, BLOCK(2))
    return (g[r][c], _mask(nb)), (g[r][c],) + nb


def r_moore2(g, r, c):
    nb = _nb(g, r, c, BLOCK(2))
    return nb, nb


def _blind(reader: Reader) -> Reader:
    """The colour-blind version of a reader: colours in the key are replaced by the mask
    (background / coloured / off-grid); the slots keep the colours, so the output can still
    copy one."""
    def f(g, r, c):
        k, slots = reader(g, r, c)
        return ("blind", _mask(slots)), slots
    return f


LADDER: List[Tuple[str, Reader]] = [
    ("cell", r_cell),
    ("row3", r_row3),
    ("col3", r_col3),
    ("tot4", r_tot4),
    ("tot8", r_tot8),
    ("blind-vn1", _blind(r_vn1)),
    ("blind-rays4", _blind(r_rays4)),
    ("blind-moore1", _blind(r_moore1)),
    ("blind-rays8", _blind(r_rays8)),
    ("mask4", r_mask4),
    ("between", r_between),
    ("raymask4", r_raymask4),
    ("mask8", r_mask8),
    ("raymask8", r_raymask8),
    ("vn1", r_vn1),
    ("rays4", r_rays4),
    ("moore1", r_moore1),
    ("rays8", r_rays8),
    ("rowcol", r_rowcol),
    ("mask5x5", r_mask_block2),
    ("moore2", r_moore2),
]


def same_shape(a: Grid, b: Grid) -> bool:
    return len(a) == len(b) and all(len(x) == len(y) for x, y in zip(a, b))


def _encodings(v: int, slots) -> frozenset:
    return frozenset([("abs", v)] + [("slot", i) for i, s in enumerate(slots) if s == v])


def table(reader: Reader, pairs: Sequence[Tuple[Grid, Grid]]) -> Optional[Dict[Hashable, frozenset]]:
    """For each key, the encodings consistent with every demonstration cell carrying that key;
    ``None`` on a clash (some key has no consistent encoding: the reader is refuted)."""
    t: Dict[Hashable, frozenset] = {}
    for a, b in pairs:
        for r in range(len(a)):
            for c in range(len(a[0])):
                k, slots = reader(a, r, c)
                enc = _encodings(b[r][c], slots)
                t[k] = t[k] & enc if k in t else enc
                if not t[k]:
                    return None
    return t


def _decode(e, slots) -> int:
    return e[1] if e[0] == "abs" else slots[e[1]]


def apply_guess(reader: Reader, t: Dict[Hashable, frozenset], g: Grid) -> Grid:
    """The UNSOUND control: an unseen key keeps the cell's colour, and an ambiguous key takes
    the first encoding in a fixed order.  Used only to measure what the refusal rule prevents."""
    out = []
    for r in range(len(g)):
        row = []
        for c in range(len(g[0])):
            k, slots = reader(g, r, c)
            if k not in t:
                row.append(g[r][c])
            else:
                row.append(_decode(sorted(t[k], key=lambda e: (e[0] != "slot", e[1]))[0], slots))
        out.append(row)
    return out


def apply(reader: Reader, t: Dict[Hashable, frozenset], g: Grid) -> Optional[Grid]:
    """The determined answer, or ``None`` if some query cell is not determined: its key is
    unseen, or the surviving encodings for its key decode to different colours (then two
    surviving rules disagree)."""
    out = []
    for r in range(len(g)):
        row = []
        for c in range(len(g[0])):
            k, slots = reader(g, r, c)
            if k not in t:
                return None
            vals = {_decode(e, slots) for e in t[k]}
            if len(vals) != 1:
                return None
            row.append(vals.pop())
        out.append(row)
    return out


def listened(reader: Reader, pairs: Sequence[Tuple[Grid, Grid]]) -> bool:
    """Leave-one-out: every demonstration is predicted exactly by the table of the others."""
    if len(pairs) < 2:
        return False
    for i in range(len(pairs)):
        rest = [p for j, p in enumerate(pairs) if j != i]
        t = table(reader, rest)
        if t is None or apply(reader, t, pairs[i][0]) != pairs[i][1]:
            return False
    return True


def solve(task: dict, mode: str = "ladder") -> Tuple[Optional[List[Grid]], str]:
    pairs = [(p["input"], p["output"]) for p in task["train"]]
    if not all(same_shape(a, b) for a, b in pairs):
        return None, "shape changes: outside the local-rule family"
    queries = [p["input"] for p in task["test"]]
    clashes = []
    if mode == "guess":
        for name, reader in LADDER:
            t = table(reader, pairs)
            if t is not None:
                return [apply_guess(reader, t, q) for q in queries], name + " (guessed)"
        return None, "every reader refuted"
    for name, reader in LADDER:
        t = table(reader, pairs)
        if t is None:
            clashes.append(name)
            continue
        answers = [apply(reader, t, q) for q in queries]
        if any(a is None for a in answers):
            continue
        if mode == "listened" and not listened(reader, pairs):
            continue
        return answers, name
    return None, "no reader both consistent and covering (refuted: %s)" % (
        ",".join(clashes) or "none")




def _grid_text(g: Grid) -> str:
    return " / ".join("".join(str(v) for v in row) if all(v < 10 for v in row)
                      else " ".join(str(v) for v in row) for row in g)


def induce_grids(pairs: Sequence[Tuple[Grid, Grid]], query: Grid) -> Tuple[Optional[Grid], str]:
    """The determined answer for one query and the reader that gave it, or ``None`` and why."""
    ans, why = solve({"train": [{"input": a, "output": b} for a, b in pairs],
                      "test": [{"input": query}]})
    return (ans[0] if ans else None), why


def induce_grids_text(pairs, query) -> Tuple[bool, str, Dict[str, object]]:
    ans, why = induce_grids(pairs, query)
    if ans is None:
        return False, "local rules: refused -- " + why, {"status": "refused", "family": "local",
                                                         "why": why}
    return True, "local rules (reader %s): %s" % (why, _grid_text(ans)), {
        "status": "answered", "family": "local", "reader": why, "answer": ans}


def arc_task_path(name: str) -> str:
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "..", "arc_agi_17", "data", "training", name + ".json")


def arc_text(name: str) -> Tuple[bool, str, Dict[str, object]]:
    """A stored ARC task read by the local-rule ladder; each answer checked against the stored
    output (used for scoring only)."""
    import json
    import os
    path = arc_task_path(name.strip())
    if not os.path.exists(path):
        return False, "no stored ARC task named %r" % name, {"status": "unknown"}
    task = json.load(open(path))
    ans, why = solve(task)
    if ans is None:
        return False, "local rules: refused -- " + why, {"status": "refused", "why": why}
    ok = all(a == p.get("output") for a, p in zip(ans, task["test"]))
    return ok, "local rules (reader %s): %s" % (why, "RIGHT" if ok else "WRONG"), {
        "status": "right" if ok else "wrong", "reader": why}
