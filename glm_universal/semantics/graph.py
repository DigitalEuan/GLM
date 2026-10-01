"""The grounded semantic graph: nodes are meanings, edges are derivations.

How this differs from the graph it replaces
-------------------------------------------
The inherited concept-relation graph had **names** for nodes and **stored
assertions** for edges.  A name is a string, so two notations for one subject
were two nodes; an assertion is remembered, so an edge could not be checked
against anything.  Three quarters of its edges were ``auto_proposed`` -- an
edge label that states no relation at all, attached to pairs chosen because
their SHA-256-derived carriers were within a Hamming radius.

Here:

* a **node is a meaning**, so ``"water"``, ``"H2O"`` and
  ``"dihydrogen monoxide"`` are one node with three notations, and
  ``"energy"``, ``"work"`` and ``"heat"`` are one node with three;
* an **edge is a derivation**, produced by :mod:`.relations` from the two
  meanings and re-checkable from them: :meth:`SemanticGraph.verify` recomputes
  every edge in the graph and reports how many stand.  A graph that cannot
  re-derive its own edges is not shipped.

Nothing is stored that cannot be recomputed, so the graph has no capacity to
drift away from the registers it was built from.

Scale
-----
Built over the register-backed vocabulary, the graph has a few hundred nodes:
one per distinct meaning, not one per string.  That collapse is itself a
result -- 726 register quantity names denote only 156 distinct dimensions --
and it is reported by :func:`graph_report` rather than hidden, because the
conflation is exactly the information the dimension layer does not carry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import (Dict, Iterable, List, Mapping, Optional, Sequence, Set,
                    Tuple)

from ..derived import memo
from . import relations as rel
from .meaning import Meaning, encode
from .reference import Resolution, reference_terms, resolve

__all__ = [
    "SemanticGraph", "build_graph", "default_graph", "graph_report",
    "meaning_sort_key",
]


def meaning_sort_key(meaning: Meaning) -> Tuple:
    """A total, deterministic order on meanings: their carriers, as rationals.

    Sorting by the carrier rather than by any name keeps the order a function
    of the meanings alone.
    """
    return tuple((c.numerator, c.denominator) if isinstance(c, Fraction)
                 else (c, 1) for c in encode(meaning))


@dataclass(frozen=True)
class SemanticGraph:
    """Meanings, the notations that denote them, and the derived relations."""

    meanings: Tuple[Meaning, ...]
    notations: Mapping[Meaning, Tuple[str, ...]]
    binary: Tuple[rel.Claim, ...]
    ternary: Tuple[rel.Claim, ...]
    refused: Tuple[Resolution, ...]
    _adjacency: Dict[Meaning, Tuple[Tuple[Meaning, str], ...]] = \
        field(default_factory=dict, compare=False)

    # -- access ----------------------------------------------------------

    def __len__(self) -> int:
        return len(self.meanings)

    def terms(self) -> Tuple[str, ...]:
        """Every notation the graph resolved, sorted."""
        return tuple(sorted(term for terms in self.notations.values()
                            for term in terms))

    def meaning_of(self, term: str) -> Optional[Meaning]:
        """The node a notation denotes, if the graph has it."""
        answer = resolve(term)
        if answer.meaning is None or answer.meaning not in self.notations:
            return None
        return answer.meaning

    def names_for(self, meaning: Meaning) -> Tuple[str, ...]:
        """Every notation in the corpus that denotes this meaning."""
        return self.notations.get(meaning, ())

    def neighbours(self, meaning: Meaning
                   ) -> Tuple[Tuple[Meaning, str], ...]:
        """``(other, relation)`` for every binary edge at a node."""
        return self._adjacency.get(meaning, ())

    def degree(self, meaning: Meaning) -> int:
        """How many binary edges touch a node."""
        return len(self.neighbours(meaning))

    def claims_between(self, a: Meaning, b: Meaning) -> Tuple[rel.Claim, ...]:
        """Every relation derivable in either direction between two nodes."""
        return rel.derive(a, b) + rel.derive(b, a)

    def path(self, source: Meaning, target: Meaning, limit: int = 6
             ) -> Optional[Tuple[Tuple[Meaning, str, Meaning], ...]]:
        """A shortest relation path between two nodes, or ``None``.

        Breadth-first with nodes visited in carrier order, so the path is a
        function of the graph alone; ties never depend on insertion order.
        """
        if source == target:
            return ()
        seen: Set[Meaning] = {source}
        frontier: List[Tuple[Meaning, Tuple[Tuple[Meaning, str, Meaning], ...]]]
        frontier = [(source, ())]
        for _ in range(limit):
            nxt: List[Tuple[Meaning,
                            Tuple[Tuple[Meaning, str, Meaning], ...]]] = []
            for node, trail in frontier:
                for other, relation in self.neighbours(node):
                    if other in seen:
                        continue
                    step = trail + ((node, relation, other),)
                    if other == target:
                        return step
                    seen.add(other)
                    nxt.append((other, step))
            if not nxt:
                return None
            frontier = sorted(nxt, key=lambda pair: meaning_sort_key(pair[0]))
        return None

    # -- integrity -------------------------------------------------------

    def verify(self) -> Dict[str, object]:
        """Recompute every edge from its meanings.

        The graph's own claim to be derived rather than remembered, checked.
        """
        binary_ok, binary_bad = rel.verify_all(self.binary)
        ternary_ok, ternary_bad = rel.verify_all(self.ternary)
        return {
            "binary_edges": len(self.binary),
            "binary_verified": binary_ok,
            "binary_failed": len(binary_bad),
            "ternary_edges": len(self.ternary),
            "ternary_verified": ternary_ok,
            "ternary_failed": len(ternary_bad),
            "all_verified": not binary_bad and not ternary_bad,
        }


def _index_notations(terms: Sequence[str]
                     ) -> Tuple[Dict[Meaning, List[str]], List[Resolution]]:
    grounded: Dict[Meaning, List[str]] = {}
    refused: List[Resolution] = []
    for term in sorted(set(terms)):
        answer = resolve(term)
        if answer.meaning is None:
            refused.append(answer)
            continue
        grounded.setdefault(answer.meaning, []).append(term)
    return grounded, refused


def build_graph(terms: Optional[Iterable[str]] = None,
                with_ternary: bool = True) -> SemanticGraph:
    """Build the grounded graph over a corpus of notations.

    ``terms`` defaults to the register-backed vocabulary
    (:func:`.reference.reference_terms`).  Terms with no determinate referent
    are not nodes; they are returned in ``refused`` with their reasons, so a
    caller can always see what the corpus contained that meaning could not.

    The default corpus is a derivation of frozen registers with no argument,
    so it is built once per process and reused; :func:`default_graph` is the
    memoised holder, and ``default_graph.__wrapped__()`` still recomputes it
    from scratch for anything that wants to check the reuse changes nothing.
    """
    if terms is None and with_ternary:
        return default_graph()
    return _construct_graph(terms, with_ternary)


@memo
def default_graph() -> SemanticGraph:
    """The grounded graph over the register-backed vocabulary."""
    return _construct_graph(None, True)


def _construct_graph(terms: Optional[Iterable[str]],
                     with_ternary: bool) -> SemanticGraph:
    """Do the work :func:`build_graph` describes, with nothing reused."""
    corpus = tuple(reference_terms() if terms is None else terms)
    grounded, refused = _index_notations(corpus)
    nodes = tuple(sorted(grounded, key=meaning_sort_key))
    notations = {m: tuple(sorted(names)) for m, names in grounded.items()}

    binary: List[rel.Claim] = []
    adjacency: Dict[Meaning, List[Tuple[Meaning, str]]] = {m: [] for m in nodes}
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            for claim in rel.derive(a, b) + rel.derive(b, a):
                if claim.relation == "same_meaning":
                    continue            # distinct nodes are distinct meanings
                binary.append(claim)
                first, second = claim.meanings[0], claim.meanings[1]
                adjacency[first].append((second, claim.relation))
                adjacency[second].append((first, claim.relation))

    ternary: List[rel.Claim] = []
    if with_ternary:
        dimensional = [m for m in nodes if rel.has_dimension(m)]
        by_exponents: Dict[Tuple[Fraction, ...], Meaning] = {}
        for m in dimensional:
            by_exponents.setdefault(m.exponents, m)
        for b in dimensional:
            for c in dimensional:
                total = tuple(x + y for x, y in zip(b.exponents, c.exponents))
                a = by_exponents.get(total)
                if a is not None:
                    ternary.extend(rel.derive_ternary(a, b, c,
                                                      ("product_of",)))
                difference = tuple(x - y for x, y in
                                   zip(b.exponents, c.exponents))
                a = by_exponents.get(difference)
                if a is not None:
                    ternary.extend(rel.derive_ternary(a, b, c,
                                                      ("quotient_of",)))
        numbers = [m for m in nodes if m.kind == "number"]
        by_value = {m.magnitude: m for m in numbers}
        for b in numbers:
            for c in numbers:
                a = by_value.get(b.magnitude + c.magnitude)
                if a is not None:
                    ternary.extend(rel.derive_ternary(a, b, c, ("sum_is",)))
                a = by_value.get(b.magnitude * c.magnitude)
                if a is not None:
                    ternary.extend(rel.derive_ternary(a, b, c,
                                                      ("product_is",)))

    frozen_adjacency = {m: tuple(sorted(
        items, key=lambda pair: (pair[1], meaning_sort_key(pair[0]))))
        for m, items in adjacency.items()}
    return SemanticGraph(meanings=nodes, notations=notations,
                         binary=tuple(binary), ternary=tuple(ternary),
                         refused=tuple(refused),
                         _adjacency=frozen_adjacency)


def graph_report(graph: Optional[SemanticGraph] = None) -> Dict[str, object]:
    """What the grounded graph contains, counted rather than described."""
    graph = graph if graph is not None else build_graph()
    by_kind: Dict[str, int] = {}
    for meaning in graph.meanings:
        by_kind[meaning.kind] = by_kind.get(meaning.kind, 0) + 1
    by_relation: Dict[str, int] = {}
    for claim in graph.binary + graph.ternary:
        by_relation[claim.relation] = by_relation.get(claim.relation, 0) + 1
    collapsed = sorted(
        ((len(names), meaning.describe(), names)
         for meaning, names in graph.notations.items() if len(names) > 1),
        reverse=True)
    isolated = [m for m in graph.meanings if graph.degree(m) == 0]
    return {
        "notations": len(graph.terms()),
        "meanings": len(graph),
        "refused_terms": len(graph.refused),
        "nodes_by_kind": dict(sorted(by_kind.items())),
        "binary_edges": len(graph.binary),
        "ternary_edges": len(graph.ternary),
        "edges_by_relation": dict(sorted(by_relation.items())),
        "isolated_meanings": len(isolated),
        "collapsed_meanings": len(collapsed),
        "most_notated": [
            {"meaning": describe, "notation_count": count,
             "notations": list(names[:12])}
            for count, describe, names in collapsed[:10]],
        "verification": graph.verify(),
    }
