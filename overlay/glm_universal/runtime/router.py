"""``glm_universal.runtime.router`` -- one question path to every surface.

The rule
--------
The surfaces of :data:`glm_universal.runtime.toolbox.SURFACES` are tried in
order.  Each either **reads** the text -- and then its answer or its refusal
is the verdict -- or does not read it, and the next is tried.  The last, the
typed planner followed by the grammar, reads everything, so every text gets
exactly one verdict from exactly one surface, and the verdict names it.

``RequestProject/GLM/ConnectedMachine.lean`` proves what makes this safe:
a surface placed in front of the planner changes the verdict only for text
it reads (``route_cons_none``), and adding a surface at the end never changes
a verdict an earlier surface gave (``route_append_of_some``).  So the claim
"the router leaves the planner's answers alone" is a count of which declared
questions each early surface reads, and :func:`connected_report` takes it.

The readers
-----------
``toolbox``      text that starts with ``tool`` or is ``tools``;
``reverse``      text that starts with a reverse Three Column Thinking
                 operation (``say:``, ``entails:``, ``solve for x:``, ...);
                 every prefix carries a colon, so no dialect program and no
                 planner question begins with one; ``relay:`` hands the
                 answer's column 2 to the planner and reads its answer back
                 (:mod:`glm_universal.runtime.reverse_relay`);
``python``       text that parses as Python **and** loads only bound names --
                 names it assigns, dialect builtins, or names the dialect
                 refuses by name.  *what is 2 + 2* parses (a comparison of
                 ``what`` with ``2 + 2``) and is not read: ``what`` is unbound;
``engineering``  a question one of its frames reads;
``planner``      everything else.

Exact, deterministic, float-free; no surface is given text another surface
read.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence, Set, Tuple

from . import toolbox as tb

__all__ = ["Routed", "python_reads", "reader_of", "route", "ask_routed",
           "connected_report", "ORDER"]

#: The surfaces in the order they are tried.
ORDER: Tuple[str, ...] = tuple(s.name for s in tb.SURFACES)


# ===========================================================================
# 1.  THE PYTHON READER
# ===========================================================================

def _bound_names(tree: ast.AST) -> Set[str]:
    out: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx,
                                                     (ast.Store, ast.Del)):
            out.add(node.id)
        elif isinstance(node, ast.arg):
            out.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.alias):
            out.add((node.asname or node.name).split(".")[0])
        elif isinstance(node, ast.ExceptHandler) and node.name:
            out.add(node.name)
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
            out.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            out.add(node.rest)
    return out


def python_reads(text: str) -> bool:
    """Whether the Python dialect reads ``text``: it parses, it is not a
    bare name, and every name it loads is bound."""
    from ..reasoning import python_speech as sp
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return False
    if not tree.body:
        return False
    only = tree.body[0] if len(tree.body) == 1 else None
    if (isinstance(only, ast.Expr)
            and isinstance(only.value, (ast.Name, ast.Attribute))):
        return False
    known = (set(sp.BUILTINS) | set(sp.FLOAT_NAMES)
             | set(sp.NONDETERMINISTIC_NAMES)
             | set(sp.NONDETERMINISTIC_MODULES) | {"True", "False", "None"})
    bound = _bound_names(tree) | known
    loaded = {n.id for n in ast.walk(tree)
              if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    return loaded <= bound


def reader_of(text: str) -> str:
    """The surface that reads ``text``: the first in :data:`ORDER`."""
    from ..engineering import speak as es
    from ..reasoning import reverse_tct as rv
    if tb.reads_tool(text):
        return "toolbox"
    if rv.reads(text):
        return "reverse"
    if python_reads(text):
        return "python"
    if es.answer(text)[0] != "unread":
        return "engineering"
    return "planner"


# ===========================================================================
# 2.  THE ROUTE
# ===========================================================================

@dataclass
class Routed:
    """One verdict, and the surface that gave it."""

    surface: str
    answered: bool
    text: str
    solution: object = None
    payload: object = None
    faculty: str = ""

    def as_dict(self) -> Dict[str, object]:
        return {"surface": self.surface, "answered": self.answered,
                "text": self.text, "faculty": self.faculty}


def route(session, text: str) -> Routed:
    """Give ``text`` to the first surface that reads it."""
    surface = reader_of(text)
    if surface == "toolbox":
        got = tb.run_tool(text)
        return Routed("toolbox", got.ok, got.text, payload=got,
                      faculty="address" if got.ok else "refusal")
    if surface == "reverse":
        from .reverse_relay import answer_any
        a = answer_any(text, session)
        body = (f"{a.verdict}: {a.sentence}" if a.answered
                else f"refused: {a.refusal}: {a.reason}")
        return Routed("reverse", a.answered, body, payload=a,
                      faculty="derive" if a.answered else "refusal")
    if surface == "python":
        from ..reasoning import python_speech as sp
        p = sp.speak(text)
        body = (f"{p.value_literal}" if p.answered
                else f"refused: {p.refusal}: {p.reason}")
        return Routed("python", p.answered, body, payload=p,
                      faculty="derive" if p.answered else "refusal")
    if surface == "engineering":
        sol = session.ask_engineering(text)
        return Routed("engineering", bool(sol.ok), sol.answer, solution=sol,
                      faculty=str((sol.payload or {}).get("faculty", ""))
                      if sol.ok else "refusal")
    from .parser import QueryError
    try:
        sol = session.ask_planned(text)
    except QueryError as exc:
        return Routed("planner", False, f"refused: {exc}",
                      faculty="refusal")
    return Routed("planner", bool(sol.ok), sol.answer, solution=sol)


def ask_routed(session, text: str):
    """:func:`route`, returned as a :class:`~glm_universal.runtime.solution.
    Solution` so the command line renders every surface one way."""
    from .parser import Query
    from .solution import Solution, Step
    r = route(session, text)
    if r.solution is not None:
        return r.solution
    query = Query(raw=text, normalised=text.strip(), kind="unknown",
                  rule=f"router:{r.surface}",
                  trace=(f"router: read by {r.surface}",))
    if r.surface == "python":
        p = r.payload
        steps = tuple(Step("python", a, b) for a, b in
                      zip(p.column1, p.column2)) or (
            Step("python", r.text, r.text),)
    elif r.surface == "reverse":
        a = r.payload
        col2 = list(a.column2) + [""] * len(a.column1)
        steps = tuple(Step("reverse", s, m) for s, m in
                      zip(a.column1, col2)) or (
            Step("reverse", r.text, r.text),)
    else:
        steps = tuple(Step("tool", line, line)
                      for line in r.text.splitlines()[:40])
    return Solution(query=query, kind=f"routed-{r.surface}", answer=r.text,
                    steps=steps, ok=r.answered,
                    error=None if r.answered else r.text,
                    payload={"surface": r.surface, "faculty": r.faculty})


# ===========================================================================
# 3.  THE MEASUREMENT OF THE STUDY'S §2.2 (C1-C4)
# ===========================================================================

def _declared_sets() -> Dict[str, List[str]]:
    from ..evaluation import cognition_heldout as ch
    from ..evaluation import engineering_heldout as eh
    from ..evaluation import python_speech_cases as pc
    from ..evaluation.cases import CASES
    return {
        "contract": [c.question for c in CASES],
        "engineering": [q.question for s in eh.ALL_SETS.values() for q in s],
        "cognition": [q.question for s in (ch.INTERVAL_QUESTIONS,
                                           ch.FRACTION_QUESTIONS,
                                           ch.DIMENSION_QUESTIONS)
                      for q in s],
        "python": ([s for _, s in pc.VALUE_CASES]
                   + [s for _, s, _ in pc.REFUSAL_CASES]),
    }


def reads_census() -> Dict[str, Dict[str, int]]:
    """Which surface reads each declared question -- the whole of C1 and the
    routing half of C2, by the non-interference rule."""
    out: Dict[str, Dict[str, int]] = {}
    for name, texts in _declared_sets().items():
        counts = {s: 0 for s in ORDER}
        for t in texts:
            counts[reader_of(t)] += 1
        out[name] = counts
    return out


def python_through_router() -> Dict[str, int]:
    """C2, Python half: the routed verdicts against the declared corpus."""
    from ..evaluation import python_speech_cases as pc
    from ..reasoning import python_speech as sp
    value_ok = refusal_ok = 0
    for _, src in pc.VALUE_CASES:
        r = route(None, src)
        if r.surface != "python" or not r.answered:
            continue
        ns, ref = sp._cpython_reference(src)
        value_ok += bool(ns["same"](eval(r.payload.value_literal, ns), ref))
    for _, src, name in pc.REFUSAL_CASES:
        r = route(None, src)
        refusal_ok += (r.surface == "python" and not r.answered
                       and r.payload.refusal == name)
    return {"values": len(pc.VALUE_CASES), "values_ok": value_ok,
            "refusals": len(pc.REFUSAL_CASES), "refusals_ok": refusal_ok}


def engineering_through_router(session) -> Dict[str, int]:
    """C2, engineering half: the routed verdicts scored as the engineering
    study scores them."""
    from ..evaluation import engineering_heldout as eh
    counts = {"correct": 0, "wrong": 0, "refused": 0, "correct-refusal": 0}
    for q in (q for s in eh.ALL_SETS.values() for q in s):
        r = route(session, q.question)
        counts[eh.score_engineering(q, r.answered, r.text)] += 1
    return counts


def tools_census(clock=None) -> Dict[str, object]:
    """C4: every declared tool question, answered, with the fragment.

    The runtime never reads a clock (a trace must be byte-identical between
    runs), so the 60-second budget is checked only when the caller passes
    ``clock``, a function returning nanoseconds; ``tools connected`` passes
    ``time.monotonic_ns``."""
    from ..evaluation.connected_cases import TOOL_QUESTIONS
    rows = []
    for question, fragment in TOOL_QUESTIONS:
        start = clock() if clock is not None else 0
        r = route(None, question)
        elapsed_ns = (clock() - start) if clock is not None else 0
        rows.append({"question": question, "answered": r.answered,
                     "contains": fragment in r.text,
                     "within_budget": elapsed_ns < 60 * 10 ** 9})
    return {"rows": rows, "passed": sum(1 for x in rows if x["answered"]
                                        and x["contains"]
                                        and x["within_budget"]),
            "total": len(rows), "timed": clock is not None}


def connected_report(run_engineering: bool = False) -> Dict[str, object]:
    """The router's measurement, at the size a report can afford: the reads
    census and the Python half of C2; ``run_engineering`` adds the
    engineering half, which needs a session."""
    report: Dict[str, object] = {
        "order": list(ORDER),
        "reads": reads_census(),
        "python": python_through_router(),
        "surfaces": len(tb.SURFACES), "tools": len(tb.TOOLS),
        "study": "studies/CONNECTED_MACHINE_STUDY.md",
        "lean_file": "RequestProject/GLM/ConnectedMachine.lean",
    }
    if run_engineering:
        from .session import GeometricSession
        report["engineering"] = engineering_through_router(GeometricSession())
    return report
