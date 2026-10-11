"""``glm_universal.reasoning.proof_dependency`` -- what a result rests on.

Phase 101 (``studies/CITATION_SCOPE_STUDY.md`` §2.1)
----------------------------------------------------
Once the citation graph is the elaborator's
(:mod:`glm_universal.reasoning.citation_reference`), the question "does this
result rest on that one?" is a reachability question with a checkable
answer, and the machine can reason over its own proof corpus:

``rests_on(a, b)``
    *yes* with the shortest path of elaborated uses from ``a`` to ``b`` as
    its witness, or *no* with the whole closure of ``a`` as its certificate
    of absence;
``closure(a)``
    every declaration of the development ``a`` rests on, directly or
    through others;
``dependents(a)``
    every declaration that rests on ``a`` -- the results a change to ``a``
    can reach.

"Rests on" is the transitive closure of *occurs in the elaborated type or
value*: a definition rests on what its body unfolds to as written, a theorem
on what its statement mentions and its proof term uses (a ``simp`` lemma the
proof used included).  Every answer is computed over the reference only
while it is of the current Lean tree; a stale reference is refused by name
(``REFERENCE_STALE``), never used.

Each answer carries a column-3 script (:func:`script_for`) that embeds the
adjacency it rests on and re-derives the verdict under ``python3 -I`` -- the
path edge by edge, or the closure by a fresh search that must be closed and
must miss ``b``.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Mapping, Optional, Tuple

from . import citation_reference as cr
from . import lean_address as la

__all__ = [
    "DependencyError", "Answer", "graph", "reverse_graph", "lookup",
    "closure", "shortest_path", "rests_on", "what_rests_on", "dependents",
    "script_for",
]


class DependencyError(Exception):
    """A named refusal."""

    def __init__(self, code: str, why: str) -> None:
        super().__init__(why)
        self.code = code
        self.why = why


@dataclass
class Answer:
    """One dependency answer and the evidence its script re-derives."""

    kind: str                      # "rests_on" | "closure" | "dependents"
    source: str
    target: Optional[str]
    verdict: Optional[bool]        # rests_on only
    path: Tuple[str, ...] = ()     # the witness of a yes
    members: Tuple[str, ...] = ()  # the closure (or reverse closure)
    direct: Tuple[str, ...] = ()   # the first step
    adjacency: Dict[str, Tuple[str, ...]] = field(default_factory=dict)


_cache: Dict[str, object] = {}


def _require_fresh() -> None:
    st = cr.state()
    if not st["present"]:
        raise DependencyError(
            "REFERENCE_ABSENT", "the elaborator's citation graph was never "
            "taken (tools citation-scope --reference)")
    if not st["fresh"]:
        raise DependencyError(
            "REFERENCE_STALE", "the elaborator's citation graph was taken "
            "over another Lean tree; re-take it with tools citation-scope "
            "--reference")


def graph() -> Mapping[str, FrozenSet[str]]:
    """The elaborator's graph, refused unless it is of the current tree."""
    _require_fresh()
    if "graph" not in _cache:
        _cache["graph"] = cr.reference_graph()
    return _cache["graph"]            # type: ignore[return-value]


def reverse_graph() -> Mapping[str, FrozenSet[str]]:
    """Who uses whom, inverted."""
    if "reverse" not in _cache:
        out: Dict[str, set] = {}
        for source, targets in graph().items():
            for target in targets:
                out.setdefault(target, set()).add(source)
        _cache["reverse"] = {k: frozenset(v) for k, v in out.items()}
    return _cache["reverse"]          # type: ignore[return-value]


def lookup(name: str, scope: Optional[str] = None) -> str:
    """A full name, or a short name that is unique in the development.

    With ``scope`` -- the full name of the other declaration of the question
    -- an ambiguous short name is read in that declaration's scope, by the
    same rule the citation reader follows
    (:func:`glm_universal.reasoning.lean_address.resolve_in_scope`): in
    ``does resolve_first rest on candidates`` the second name is the
    ``candidates`` that ``resolve_first`` itself would see.
    """
    name = name.strip().strip("`").rstrip("?.").strip()
    names = la.declaration_names()
    if name in names:
        return name
    hits = sorted(n for n in names
                  if n.endswith("." + name) or n == name)
    if not hits:
        raise DependencyError("UNKNOWN_DECLARATION",
                              f"no declaration of the development is "
                              f"named {name!r}")
    if len(hits) > 1 and scope is not None:
        own = scope.rsplit(".", 1)[0] if "." in scope else ""
        scoped = la.resolve_in_scope(name, own, (), names)
        if scoped is not None:
            return scoped
    if len(hits) > 1:
        shown = ", ".join(hits[:4]) + (" ..." if len(hits) > 4 else "")
        raise DependencyError("AMBIGUOUS_NAME",
                              f"{name!r} names {len(hits)} declarations: "
                              f"{shown}")
    return hits[0]


def _search(start: str, edges: Mapping[str, FrozenSet[str]]
            ) -> Dict[str, Optional[str]]:
    """Breadth-first search; every reached node with its parent."""
    parent: Dict[str, Optional[str]] = {start: None}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for nxt in sorted(edges.get(node, ())):
            if nxt not in parent:
                parent[nxt] = node
                queue.append(nxt)
    return parent


def closure(name: str) -> Tuple[str, ...]:
    """Everything ``name`` rests on, sorted (``name`` itself excluded)."""
    reached = _search(name, graph())
    return tuple(sorted(n for n in reached if n != name))


def shortest_path(source: str, target: str) -> Optional[Tuple[str, ...]]:
    reached = _search(source, graph())
    if target not in reached:
        return None
    path = [target]
    while reached[path[-1]] is not None:
        path.append(reached[path[-1]])    # type: ignore[arg-type]
    return tuple(reversed(path))


def _adjacency(nodes, edges) -> Dict[str, Tuple[str, ...]]:
    return {n: tuple(sorted(edges.get(n, ()))) for n in sorted(nodes)}


def _pair(a: str, b: str) -> Tuple[str, str]:
    """Both names of a question; an ambiguous one read in the other's scope."""
    try:
        source = lookup(a)
    except DependencyError as first:
        if first.code != "AMBIGUOUS_NAME":
            raise
        target = lookup(b)
        return lookup(a, scope=target), target
    return source, lookup(b, scope=source)


#: Phase 101's post-hoc repair of mark D1: read an ambiguous name of a
#: two-name question in the other name's scope.  ``False`` is the operation
#: as first declared.
SCOPED_QUESTIONS = True


def rests_on(a: str, b: str) -> Answer:
    if SCOPED_QUESTIONS:
        source, target = _pair(a, b)
    else:
        source, target = lookup(a), lookup(b)
    edges = graph()
    path = shortest_path(source, target) if source != target else None
    members = closure(source)
    if path is not None:
        adj = _adjacency(path[:-1], edges)
        return Answer("rests_on", source, target, True, path=path,
                      members=members,
                      direct=tuple(sorted(edges.get(source, ()))),
                      adjacency=adj)
    adj = _adjacency((source,) + members, edges)
    return Answer("rests_on", source, target, False, members=members,
                  direct=tuple(sorted(edges.get(source, ()))),
                  adjacency=adj)


def what_rests_on(a: str) -> Answer:
    source = lookup(a)
    edges = graph()
    members = closure(source)
    return Answer("closure", source, None, None, members=members,
                  direct=tuple(sorted(edges.get(source, ()))),
                  adjacency=_adjacency((source,) + members, edges))


def dependents(a: str) -> Answer:
    source = lookup(a)
    back = reverse_graph()
    reached = _search(source, back)
    members = tuple(sorted(n for n in reached if n != source))
    return Answer("dependents", source, None, None, members=members,
                  direct=tuple(sorted(back.get(source, ()))),
                  adjacency=_adjacency((source,) + members, back))


# ===========================================================================
#  Column 3
# ===========================================================================

_SEARCH_SRC = '''
def reach(adj, start):
    seen = {start}
    todo = [start]
    while todo:
        node = todo.pop()
        for nxt in adj.get(node, ()):
            if nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    return seen
'''


def script_for(answer: Answer, claim: Optional[bool] = None,
               path: Optional[Tuple[str, ...]] = None,
               count: Optional[int] = None) -> str:
    """A self-contained check of ``answer`` under ``python3 -I``.

    ``claim``, ``path`` and ``count`` override what the script is asked to
    confirm, which is how the mutated readings of mark D2 are built: the
    embedded adjacency is the premise, the claim is what is checked.
    """
    adj = {k: list(v) for k, v in answer.adjacency.items()}
    lines = [f"ADJ = {adj!r}", _SEARCH_SRC]
    if answer.kind == "rests_on":
        verdict = answer.verdict if claim is None else claim
        lines.append(f"A, B = {answer.source!r}, {answer.target!r}")
        if verdict:
            witness = list(answer.path if path is None else path)
            lines.append(f"P = {witness!r}")
            lines.append("ok = (len(P) >= 2 and P[0] == A and P[-1] == B and "
                         "all(P[i + 1] in ADJ.get(P[i], ()) "
                         "for i in range(len(P) - 1)))")
            lines.append("print('RESTS_ON yes path', len(P) - 1, "
                         "'VERIFIED', ok)")
        else:
            lines.append("seen = reach(ADJ, A)")
            lines.append("closed = all(t in ADJ for n in seen "
                         "for t in ADJ.get(n, ()))")
            lines.append("ok = closed and A in ADJ and B not in seen")
            lines.append("print('RESTS_ON no closure', len(seen) - 1, "
                         "'VERIFIED', ok)")
    else:
        expected = len(answer.members) if count is None else count
        lines.append(f"A, N = {answer.source!r}, {expected}")
        lines.append("seen = reach(ADJ, A)")
        lines.append("closed = all(t in ADJ for n in seen "
                     "for t in ADJ.get(n, ()))")
        lines.append("ok = closed and len(seen) - 1 == N")
        lines.append(f"print({answer.kind.upper()!r}, N, 'VERIFIED', ok)")
    return "\n".join(lines) + "\n"
