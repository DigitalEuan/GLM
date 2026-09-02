"""``glm_universal.migration.store`` -- using the migrated state.

A migration that nothing consumes proves nothing, so this module is the
consumer.  :class:`ConceptStore` loads the canonical payload written by
:mod:`glm_universal.migration.state` and answers the questions the stored
knowledge is actually shaped to answer:

* **what a name is** -- its carrier, its exact NRCI, its audited decoding,
  its role and its provenance (``imported`` or ``minted``);
* **what it is connected to** -- the labelled CRG neighbourhood, and the
  shortest labelled path between two names (:meth:`ConceptStore.path`), which
  is the concept-relation-graph's own form of inference;
* **what lies near it in the substrate** -- the carriers at least Hamming
  distance away (:meth:`ConceptStore.hamming_neighbours`), which is a
  *different* notion of nearness from the graph one and mostly disagrees with
  it -- a fact :func:`store_report` measures rather than hides;
* **what a hexcolour address names** -- the six-hex-digit rendering of a
  carrier is a key, not a decoration: :meth:`ConceptStore.by_hexcolour`
  recovers the concept from the address alone, which is well defined because
  the migration checks the addresses are distinct across the whole store;
* **where the two knowledge bases meet** -- the names that are both a CRG
  concept and a carrier of a loaded register
  (:meth:`ConceptStore.crosslinks`), which is the only place where a
  relational claim from the CRG and a dimensional claim from the register can
  be checked against each other.

Everything is exact and deterministic: ties break by name, traversal order is
sorted, and no float is constructed.
"""

from __future__ import annotations

from fractions import Fraction
from typing import (Dict, Iterable, List, Mapping, Optional, Sequence, Tuple)

from .state import load_canonical

__all__ = ["ConceptStore", "store_report"]


def _normalise_hexcolour(colour: str) -> str:
    """``"#A1B2C3"`` and ``"a1b2c3"`` name the same address."""
    text = colour.strip().lower()
    return text[1:] if text.startswith("#") else text


class ConceptStore:
    """The migrated concepts and CRG edges, indexed for use."""

    def __init__(self, payload: Mapping[str, object]) -> None:
        concepts = payload.get("concepts", [])
        edges = payload.get("edges", [])
        if not isinstance(concepts, list) or not isinstance(edges, list):
            raise ValueError("ConceptStore: malformed payload")
        self._concepts: Dict[str, Mapping[str, object]] = {
            str(c["name"]): c for c in concepts}
        self._edges: Tuple[Mapping[str, object], ...] = tuple(edges)
        adjacency: Dict[str, List[Tuple[str, str, str]]] = {}
        for edge in edges:
            src, dst = str(edge["src"]), str(edge["dst"])
            label = str(edge["label"])
            adjacency.setdefault(src, []).append((dst, label, "out"))
            adjacency.setdefault(dst, []).append((src, label, "in"))
        self._adjacency = {name: tuple(sorted(items))
                           for name, items in adjacency.items()}
        self._by_mask: Dict[int, str] = {
            int(c["mask"]): str(c["name"]) for c in concepts}
        self._by_hexcolour: Dict[str, str] = {
            _normalise_hexcolour(str(c["hexcolour"])): str(c["name"])
            for c in concepts}

    # -- loading ---------------------------------------------------------

    @classmethod
    def load(cls, payload: Optional[Mapping[str, object]] = None
             ) -> Optional["ConceptStore"]:
        """The store over the written canonical payload, or ``None``."""
        data = payload if payload is not None else load_canonical()
        if data is None:
            return None
        return cls(data)

    # -- basic access ----------------------------------------------------

    def __len__(self) -> int:
        return len(self._concepts)

    @property
    def names(self) -> Tuple[str, ...]:
        """Every concept name, sorted."""
        return tuple(sorted(self._concepts))

    @property
    def edges(self) -> Tuple[Mapping[str, object], ...]:
        """Every CRG edge, in stored order."""
        return self._edges

    def has(self, name: str) -> bool:
        """Whether the store knows this name."""
        return name in self._concepts

    def concept(self, name: str) -> Mapping[str, object]:
        """One concept record."""
        if name not in self._concepts:
            raise KeyError(f"ConceptStore: no concept {name!r}")
        return self._concepts[name]

    def nrci(self, name: str) -> Fraction:
        """The exact NRCI of a concept."""
        pair = self.concept(name)["nrci"]
        return Fraction(int(pair[0]), int(pair[1]))  # type: ignore[index]

    # -- the graph -------------------------------------------------------

    def neighbours(self, name: str) -> Tuple[Tuple[str, str, str], ...]:
        """``(other, label, direction)`` for every edge at ``name``."""
        if name not in self._concepts:
            raise KeyError(f"ConceptStore: no concept {name!r}")
        return self._adjacency.get(name, ())

    def degree(self, name: str) -> int:
        """How many edges touch a concept."""
        return len(self.neighbours(name))

    def path(self, source: str, target: str, limit: int = 8,
             exclude_labels: Sequence[str] = ()
             ) -> Optional[Tuple[Tuple[str, str, str], ...]]:
        """A shortest labelled path from ``source`` to ``target``.

        Breadth-first over the undirected CRG, neighbours visited in sorted
        order, so the path returned is a function of the data alone.  The
        result is a tuple of ``(from, label, to)`` steps, empty when the two
        names coincide, and ``None`` when no path of at most ``limit`` steps
        exists.

        ``exclude_labels`` drops edges by label before the search.  Passing
        ``("auto_proposed",)`` restricts the walk to the relations something
        asserted, rather than the ones the growth loop proposed, and the two
        answers are usually different -- which is itself worth seeing.
        """
        banned = set(exclude_labels)
        if source not in self._concepts:
            raise KeyError(f"ConceptStore: no concept {source!r}")
        if target not in self._concepts:
            raise KeyError(f"ConceptStore: no concept {target!r}")
        if source == target:
            return ()
        frontier: List[str] = [source]
        came: Dict[str, Tuple[str, str]] = {}
        seen = {source}
        for _ in range(limit):
            nxt: List[str] = []
            for name in frontier:
                for other, label, _direction in self.neighbours(name):
                    if other in seen or label in banned:
                        continue
                    seen.add(other)
                    came[other] = (name, label)
                    if other == target:
                        steps: List[Tuple[str, str, str]] = []
                        cursor = target
                        while cursor != source:
                            previous, edge_label = came[cursor]
                            steps.append((previous, edge_label, cursor))
                            cursor = previous
                        return tuple(reversed(steps))
                    nxt.append(other)
            if not nxt:
                return None
            frontier = sorted(nxt)
        return None

    # -- the substrate ---------------------------------------------------

    def hamming_neighbours(self, name: str, count: int = 5
                           ) -> Tuple[Tuple[str, int], ...]:
        """The ``count`` carriers nearest ``name`` in Hamming distance."""
        mask = int(self.concept(name)["mask"])
        scored = [(bin(mask ^ other).count("1"), other_name)
                  for other, other_name in self._by_mask.items()
                  if other_name != name]
        scored.sort()
        return tuple((other_name, distance)
                     for distance, other_name in scored[:count])

    def crosslinks(self, register_names: Iterable[str]) -> Tuple[str, ...]:
        """Names that are both a CRG concept and a register carrier."""
        return tuple(sorted(set(register_names) & set(self._concepts)))

    # -- the address layer -----------------------------------------------

    def hexcolour(self, name: str) -> str:
        """The six-hex-digit address of a concept's carrier."""
        return str(self.concept(name)["hexcolour"])

    def by_hexcolour(self, colour: str) -> str:
        """The concept a hexcolour address names.

        This is what makes the address layer a *layer* rather than a
        decoration: the six digits are enough to recover the concept, with
        no name and no search, because the migration checks that they are
        distinct across the whole store.  Leading ``#`` and letter case are
        not significant.

        :raises KeyError: if no concept carries that address.
        """
        key = _normalise_hexcolour(colour)
        if key not in self._by_hexcolour:
            raise KeyError(f"ConceptStore: no concept at address {colour!r}")
        return self._by_hexcolour[key]

    def addresses_are_distinct(self) -> bool:
        """Whether the address layer separates every concept in this store."""
        return len(self._by_hexcolour) == len(self._concepts)


def store_report(store: Optional[ConceptStore] = None,
                 samples: Sequence[str] = ("entropy", "energy", "grid",
                                           "colour")) -> Dict[str, object]:
    """Facts about the migrated store, recomputed.

    Includes the measurement that matters for reading it honestly: on the
    sampled concepts, how often the graph's nearest neighbour is also a
    nearest carrier in the substrate.  The two notions of nearness are
    different, and the number says how different.
    """
    active = store if store is not None else ConceptStore.load()
    if active is None:
        return {"available": False}

    degrees = sorted((active.degree(name), name) for name in active.names)
    labels = sorted({str(edge["label"]) for edge in active.edges})
    proposed = sum(1 for edge in active.edges
                   if str(edge["label"]) == "auto_proposed")
    isolated = [name for name in active.names if active.degree(name) == 0]
    minted = [name for name in active.names
              if active.concept(name)["provenance"] == "minted"]

    agreements = 0
    checked = 0
    rows: List[Dict[str, object]] = []
    for name in samples:
        if not active.has(name):
            continue
        checked += 1
        graph = tuple(other for other, _label, _d in active.neighbours(name))
        substrate = tuple(other for other, _d
                          in active.hamming_neighbours(name, 5))
        overlap = sorted(set(graph) & set(substrate))
        if overlap:
            agreements += 1
        rows.append({
            "concept": name,
            "degree": active.degree(name),
            "graph_neighbours": list(graph[:5]),
            "substrate_neighbours": list(substrate),
            "shared": overlap,
        })

    return {
        "available": True,
        "concepts": len(active),
        "edges": len(active.edges),
        "labels": len(labels),
        "auto_proposed_edges": proposed,
        "asserted_edges": len(active.edges) - proposed,
        "isolated_concepts": len(isolated),
        "minted_concepts": len(minted),
        "max_degree": degrees[-1][0] if degrees else 0,
        "max_degree_concept": degrees[-1][1] if degrees else None,
        "samples": rows,
        "samples_checked": checked,
        "samples_where_graph_and_substrate_agree": agreements,
        "reading": ("graph nearness and substrate nearness are different "
                    "relations: an edge records a claim someone made, a "
                    "small Hamming distance records that two carriers were "
                    "assigned nearby codes, and the two need not coincide"),
    }
