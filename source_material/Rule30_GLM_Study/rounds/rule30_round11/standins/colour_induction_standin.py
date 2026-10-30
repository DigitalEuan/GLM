"""STAND-IN for ``glm_universal/reasoning/colour_induction.py`` (Round 11, not the owner's module).

``runtime/toolbox.py`` imports this module at the start of ``tool induce`` and ``tool arc``.
The real module (Phase 178) is the colour-and-object solver.  This stand-in implements only
the *gate*: it parses ``IN -> OUT ; ... ? QUERY`` and says whether a task is a colour task
(a value outside {0,1}, or grids that change shape).  Binary one-shape tasks -- every Rule 30
task -- then go to ``reasoning/pipeline_kit.py`` exactly as in the real toolbox.  Colour tasks
and ``tool arc`` are REFUSED with a message naming the missing file; nothing is invented.
"""
from typing import List, Optional, Tuple

_MISSING = ("reasoning/colour_induction.py is not in this checkout (Round 11 stand-in): "
            "colour/shape-changing tasks and `tool arc` cannot be read here")


def _grid(text: str) -> Optional[List[List[int]]]:
    rows = [r.strip() for r in text.strip().split("/") if r.strip()]
    if not rows:
        return None
    out = []
    for r in rows:
        cells = r.replace(",", " ").split()
        if len(cells) == 1 and len(cells[0]) > 1:
            cells = list(cells[0])
        try:
            out.append([int(c) for c in cells])
        except ValueError:
            return None
    return out


def parse_task(arg: str) -> Tuple[Optional[list], Optional[list], str]:
    if "?" not in arg:
        return None, None, "no query"
    demo, query = arg.split("?", 1)
    pairs = []
    for part in demo.split(";"):
        if not part.strip():
            continue
        if "->" not in part:
            return None, None, "a demonstration without ->"
        a, b = part.split("->", 1)
        ga, gb = _grid(a), _grid(b)
        if ga is None or gb is None:
            return None, None, "unreadable grid"
        pairs.append((ga, gb))
    q = _grid(query)
    if q is None:
        return None, None, "unreadable query"
    return pairs, q, ""


def is_colour_task(pairs, query) -> bool:
    grids = [g for p in pairs for g in p] + [query]
    if any(v not in (0, 1) for g in grids for row in g for v in row):
        return True
    shape = lambda g: (len(g), tuple(len(r) for r in g))
    return any(shape(a) != shape(b) for a, b in pairs)


def induce_colour_text(pairs, query):
    return False, _MISSING, {"status": "unavailable", "missing": "reasoning/colour_induction.py"}


def arc_text(name):
    return False, _MISSING, {"status": "unavailable", "missing": "reasoning/colour_induction.py"}
