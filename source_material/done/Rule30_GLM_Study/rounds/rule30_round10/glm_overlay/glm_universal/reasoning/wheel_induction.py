"""``glm_universal.reasoning.wheel_induction`` -- inducing a wheel from demonstrations.

Round 10 of the Rule 30 study.  The GLM's induction solver (``reasoning/pipeline_kit.py``)
fits permutations, XOR masks, shifts and their compositions.  Those are linear or
cell-permuting maps, so none of its hypotheses fits a non-linear wheel: on three rows of
Rule 30 it reports ``unsolved`` (0 of 76 hypotheses fit).  This module adds the missing
family, **the local rule of radius 1** (the 256 wheels), with the same discipline the GLM
uses everywhere else: fit, keep every survivor, answer only if all survivors agree, and
otherwise refuse and say why.

For wheels that discipline is proved sound and complete in Lean
(``RequestProject/GLM/Rule30/WheelInduction.lean``):

* ``rows_agree_iff`` -- a wheel reproduces the demonstrations iff it agrees with them on every
  neighbourhood the demonstrations show; nothing else about it is fixed;
* ``next_row_determined_iff`` -- every surviving wheel predicts the same next row iff every
  neighbourhood of the query row has been seen.  If one has not, flipping that single entry of
  the table gives a surviving wheel with a different prediction.

So the refusal rule below ("refuse iff the query needs an unseen neighbourhood") is not a
heuristic: it is exactly "refuse iff the survivors disagree".  Both are computed and checked
against each other on every call.

Two readings are offered.

* :func:`induce_rows` -- the ARC-style reading: demonstration pairs ``row -> next row``.
* :func:`induce_column` -- the observer's reading: one column of the run from the impulse
  row, seen by an observer standing at column ``c``.  At ``c = 0`` the answer is never better
  than the class ``{30, 86}`` (Lean ``centre_column_class``): the centre observer cannot tell
  left from right.  At ``1 <= |c| <= 5`` the column determines the wheel
  (Lean ``offCentre_column_identifies``).

Window convention for :func:`induce_rows` (declared, not hidden): a demonstration row is a
finite window of an infinite row that is **white outside the window**, and the next row is
read on the same window.  So the output at the window's edge cell uses a white neighbour.
This is exact for runs that stay white outside the window (for example the impulse run of any
wheel with ``f(0,0,0) = 0``, once the window covers the light cone).

Exact arithmetic only (``int`` and GF(2)).  No float, no randomness.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from ..data_objects import automata as ca

__all__ = [
    "Neighbourhood", "parse_row", "parse_task", "neighbourhoods", "observations",
    "survivors_of_rows", "induce_rows", "induce_rows_text", "induce_column",
    "induce_column_text", "rule30_rows", "rule30_demonstrations",
]

Neighbourhood = Tuple[int, int, int]
Row = Tuple[int, ...]

#: Every neighbourhood, in table order (index ``4L + 2C + R``).
ALL_NEIGHBOURHOODS: Tuple[Neighbourhood, ...] = tuple(
    ((i >> 2) & 1, (i >> 1) & 1, i & 1) for i in range(8))


def _index(n: Neighbourhood) -> int:
    return 4 * n[0] + 2 * n[1] + n[2]


def _name(n: Neighbourhood) -> str:
    return "".join(map(str, n))


# ---------------------------------------------------------------------------
# parsing
# ---------------------------------------------------------------------------

def parse_row(text: str) -> Row:
    """A row written as a string of ``0`` and ``1`` (``.`` and ``#`` are also read)."""
    s = text.strip().replace(".", "0").replace("#", "1").replace(" ", "")
    if not s or any(ch not in "01" for ch in s):
        raise ValueError(f"a row is a string of 0 and 1, got {text!r}")
    return tuple(int(ch) for ch in s)


def parse_task(text: str) -> Tuple[List[Tuple[Row, Row]], Optional[Row]]:
    """``IN -> OUT ; IN -> OUT ? QUERY`` (the GLM's ``tool induce`` grammar), or a diagram
    ``ROW / ROW / ROW ? QUERY`` whose consecutive rows are the demonstrations."""
    body, _, query_text = text.partition("?")
    query = parse_row(query_text) if query_text.strip() else None
    pairs: List[Tuple[Row, Row]] = []
    if "->" in body:
        for chunk in body.split(";"):
            if not chunk.strip():
                continue
            a, sep, b = chunk.partition("->")
            if not sep:
                raise ValueError(f"a demonstration is IN -> OUT, got {chunk.strip()!r}")
            pairs.append((parse_row(a), parse_row(b)))
    else:
        rows = [parse_row(r) for r in body.split("/") if r.strip()]
        pairs = list(zip(rows, rows[1:]))
    if not pairs:
        raise ValueError("no demonstrations")
    return pairs, query


# ---------------------------------------------------------------------------
# the fitted family: radius-1 local rules
# ---------------------------------------------------------------------------

def neighbourhoods(row: Sequence[int]) -> List[Neighbourhood]:
    """The neighbourhood of each cell of a window row, white outside the window."""
    padded = (0,) + tuple(row) + (0,)
    return [(padded[i - 1], padded[i], padded[i + 1]) for i in range(1, len(padded) - 1)]


def step_window(r: int, row: Sequence[int]) -> Row:
    """One step of wheel ``r`` on a window row (white outside it)."""
    return tuple(ca.local_rule(r, *n) for n in neighbourhoods(row))


def observations(pairs: Sequence[Tuple[Row, Row]]
                 ) -> Tuple[Dict[Neighbourhood, int], List[str]]:
    """The table entries the demonstrations show, and any contradiction among them."""
    seen: Dict[Neighbourhood, int] = {}
    conflicts: List[str] = []
    for k, (a, b) in enumerate(pairs):
        if len(a) != len(b):
            conflicts.append(f"pair {k}: rows of different width ({len(a)} and {len(b)})")
            continue
        for i, n in enumerate(neighbourhoods(a)):
            if n in seen and seen[n] != b[i]:
                conflicts.append(f"pair {k}, cell {i}: neighbourhood {_name(n)} gives "
                                 f"{b[i]} here and {seen[n]} earlier")
            seen.setdefault(n, b[i])
    return seen, conflicts


def survivors_of_rows(pairs: Sequence[Tuple[Row, Row]]) -> List[int]:
    """Every wheel ``r < 256`` that reproduces every demonstration (exhaustive)."""
    return [r for r in range(256) if all(step_window(r, a) == tuple(b) for a, b in pairs)]


def induce_rows(pairs: Sequence[Tuple[Row, Row]], query: Optional[Row] = None
                ) -> Dict[str, object]:
    """Fit the wheel to the demonstrations and, if a query row is given, predict its next row
    or refuse.

    Returns a dict with ``status`` (``answered``, ``refused``, ``unsolved`` or ``fitted`` when
    there is no query), the ``survivors``, the ``seen`` and ``unseen`` table entries, the
    ``answer`` row, and the ``steps`` of the reading.  Both refusal criteria are computed (the
    survivors disagree; the query needs an unseen neighbourhood) and asserted equal, which is
    Lean's ``next_row_determined_iff``.
    """
    seen, conflicts = observations(pairs)
    steps: List[str] = [f"{len(pairs)} demonstrations, rows of width "
                        f"{sorted({len(a) for a, _ in pairs})}"]
    if conflicts:
        steps.append("no radius-1 rule fits: " + "; ".join(conflicts[:3]))
        return {"status": "unsolved", "survivors": [], "seen": seen, "unseen": [],
                "answer": None, "steps": steps}
    unseen = [n for n in ALL_NEIGHBOURHOODS if n not in seen]
    surv = survivors_of_rows(pairs)
    # rows_agree_iff: the survivors are exactly the tables that agree on the seen entries.
    by_table = [r for r in range(256)
                if all(ca.local_rule(r, *n) == v for n, v in seen.items())]
    assert surv == by_table, "survivors disagree with the seen-table characterisation"
    assert len(surv) == 2 ** len(unseen)
    steps.append(f"seen table entries: "
                 + ", ".join(f"{_name(n)}->{seen[n]}" for n in ALL_NEIGHBOURHOODS if n in seen))
    steps.append(f"unseen: {[_name(n) for n in unseen] or 'none'}; surviving wheels: "
                 f"{len(surv)} = 2^{len(unseen)}"
                 + (f" {surv}" if len(surv) <= 8 else ""))
    out: Dict[str, object] = {"survivors": surv, "seen": seen, "unseen": unseen,
                              "steps": steps}
    if query is None:
        out.update(status="fitted", answer=surv[0] if len(surv) == 1 else None)
        return out
    needed = sorted(set(neighbourhoods(query)), key=_index)
    missing = [n for n in needed if n not in seen]
    answers = sorted({step_window(r, query) for r in surv})
    # next_row_determined_iff: survivors agree  <=>  nothing the query needs is unseen.
    assert (len(answers) == 1) == (not missing), "refusal criteria disagree"
    steps.append(f"the query needs {[_name(n) for n in needed]}")
    if missing:
        steps.append(f"refused: {[_name(n) for n in missing]} never shown; the survivors give "
                     f"{len(answers)} different next rows")
        out.update(status="refused", answer=None, missing=missing,
                   answers=["".join(map(str, a)) for a in answers[:4]])
    else:
        steps.append("answered: every survivor gives the same next row")
        out.update(status="answered", answer="".join(map(str, answers[0])), missing=[])
    return out


def induce_rows_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    """Text interface in the toolbox's style: ``(ok, text, figures)``."""
    pairs, query = parse_task(arg)
    res = induce_rows(pairs, query)
    lines = list(res["steps"])
    if res["status"] == "answered":
        head = f"next row: {res['answer']} (wheel family, all {len(res['survivors'])} survivors agree)"
    elif res["status"] == "refused":
        head = (f"refused: the demonstrations never show {[_name(n) for n in res['missing']]}; "
                f"candidate next rows {res['answers']}")
    elif res["status"] == "fitted":
        head = (f"fitted: wheel {res['answer']}" if res["answer"] is not None
                else f"fitted: {len(res['survivors'])} wheels survive")
    else:
        head = "unsolved: no radius-1 rule fits"
    figures = {"status": res["status"], "survivors": len(res["survivors"]),
               "unseen": len(res["unseen"])}
    return res["status"] in ("answered", "fitted"), "\n".join([head] + lines), figures


# ---------------------------------------------------------------------------
# the observer's reading: one column of the impulse run
# ---------------------------------------------------------------------------

def induce_column(bits: Sequence[int], column: int = 0) -> Dict[str, object]:
    """Every wheel whose impulse run shows ``bits`` at ``column`` for ``t < len(bits)``."""
    K = len(bits)
    surv = [r for r in range(256)
            if ca.evolve_impulse_column(r, K, column) == tuple(bits)]
    classes = sorted({ca.class_rep(r) for r in surv})
    return {"survivors": surv, "classes": classes, "length": K, "column": column}


def induce_column_text(bits: Sequence[int], column: int = 0) -> str:
    res = induce_column(bits, column)
    s = res["survivors"]
    return (f"observer at column {column}, {res['length']} values: {len(s)} wheels survive"
            + (f" {s}" if len(s) <= 8 else ""))


# ---------------------------------------------------------------------------
# Rule 30 itself, as demonstrations
# ---------------------------------------------------------------------------

def rule30_rows(T: int, half: Optional[int] = None) -> List[Row]:
    """Rows ``0..T`` of wheel 30 from the impulse on the window ``[-half, half]``
    (``half`` defaults to ``T + 1``, which covers the light cone with a white margin)."""
    h = T + 1 if half is None else half
    row: Row = tuple(1 if c == 0 else 0 for c in range(-h, h + 1))
    out = [row]
    for _ in range(T):
        row = step_window(30, row)
        out.append(row)
    return out


def rule30_demonstrations(T: int) -> Tuple[List[Tuple[Row, Row]], Row, Row]:
    """Pairs ``row t -> row t+1`` for ``t < T``, the query row ``T`` and the true row
    ``T + 1``, on a window wide enough for row ``T + 1``."""
    rows = rule30_rows(T + 1, T + 2)
    return list(zip(rows[:T], rows[1:T + 1])), rows[T], rows[T + 1]
