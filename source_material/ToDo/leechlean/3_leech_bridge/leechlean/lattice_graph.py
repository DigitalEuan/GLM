"""leechlean.lattice_graph -- a Lean file as a graph of lattice addresses.

The owner's concept, second push: the parts that construct file contents are
words, symbols and machine instructions; a constructed Lean file is a group
of addresses linked together into a **lattice-graph**, and files reuse parts
that other files also use -- those joinings are the object of interest.

Constituent taxonomy (``constituent_of``):
  word        -- identifiers and keywords (what the text says);
  symbol      -- operators and punctuation (how it is written);
  instruction -- tactic invocations and declaration frames (what the proof
                 machine is told to do);
  number, string, layout (whitespace), prose (comments), composite (bigrams).

The graph:
  * **nodes** are parts, at their Leech addresses (the codebook);
  * **edges** are *joinings*: an adjacency edge (u, v) is counted once for
    every pair of consecutive structural tokens u, v in a file -- the
    construction sequence of the corpus;
  * every edge is itself a lattice vector d = A(v) - A(u) (both endpoints are
    lattice points), so each joining carries a squared norm (its length in
    the lattice) and a Lambda/2Lambda class and type (its coset) --
    measured here, not assumed;
  * **reuse**: a part's document frequency (how many files use it) and an
    edge's file frequency (how many files join those two parts) -- the
    joinings shared across files and modules are extracted and ranked.

File subgraphs: :func:`file_subgraph` returns one file's induced graph with
per-node reuse counts and per-edge sharing, ready for export or drawing.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from . import cosets as CS
from .lean_parts import DECL_KW, FileRecord, structural
from .leech_core import norm2

# ---------------------------------------------------------------------------
# constituent taxonomy
# ---------------------------------------------------------------------------

_KIND_CONSTITUENT = {
    "kw": "word", "ident": "word", "sym": "symbol", "num": "number",
    "str": "string", "ws": "layout", "comment": "prose",
}


def constituent_of(part_key: str) -> str:
    """word | symbol | instruction | number | string | layout | prose | composite."""
    tag = part_key.split(":", 1)[0]
    if tag == "t" or tag == "f":
        return "instruction"
    if tag == "b":
        return "composite"
    return _KIND_CONSTITUENT.get(tag, "other")


# ---------------------------------------------------------------------------
# graph construction
# ---------------------------------------------------------------------------

@dataclass
class LatticeGraph:
    addresses: Dict[str, Tuple[int, ...]]
    adj: Dict[Tuple[str, str], int]              # directed adjacency edge -> count
    edge_files: Dict[Tuple[str, str], set]       # edge -> files using it
    part_files: Dict[str, set]                   # part -> files using it
    file_parts: Dict[str, List[str]]             # rel -> ordered distinct parts
    file_module: Dict[str, str]

    # ------------------------------------------------------------------
    def parts(self) -> List[str]:
        return sorted(self.part_files)

    def edge_vector(self, u: str, v: str) -> Tuple[int, ...]:
        A, B = self.addresses[u], self.addresses[v]
        return tuple(b - a for a, b in zip(A, B))

    def edge_norm2(self, u: str, v: str) -> int:
        d = self.edge_vector(u, v)
        return sum(x * x for x in d)

    def edge_class_type(self, u: str, v: str) -> int:
        return CS.class_type(CS.class_key(self.edge_vector(u, v)))

    def doc_frequency(self, part: str) -> int:
        return len(self.part_files.get(part, ()))

    def edge_file_frequency(self, u: str, v: str) -> int:
        return len(self.edge_files.get((u, v), ()))


def build_graph(corpus: Sequence[FileRecord],
                addresses: Dict[str, Tuple[int, ...]]) -> LatticeGraph:
    """One pass over the corpus: adjacency joinings + reuse bookkeeping."""
    adj: Counter = Counter()
    edge_files: Dict[Tuple[str, str], set] = defaultdict(set)
    part_files: Dict[str, set] = defaultdict(set)
    file_parts: Dict[str, List[str]] = {}
    file_module: Dict[str, str] = {}
    for rec in corpus:
        st = structural(rec.toks)
        keys = [t.key for _, t in st]
        seen = set()
        ordered = []
        for k in keys:
            part_files[k].add(rec.rel)
            if k not in seen:
                seen.add(k)
                ordered.append(k)
        file_parts[rec.rel] = ordered
        file_module[rec.rel] = rec.module
        for a, b in zip(keys, keys[1:]):
            adj[(a, b)] += 1
            edge_files[(a, b)].add(rec.rel)
    return LatticeGraph(addresses=addresses, adj=dict(adj),
                        edge_files=edge_files, part_files=part_files,
                        file_parts=file_parts, file_module=file_module)


# ---------------------------------------------------------------------------
# edge analysis (vectorised)
# ---------------------------------------------------------------------------

@dataclass
class EdgeAnalysis:
    n_edges: int
    norms2: np.ndarray                       # squared norms of edge vectors
    types: np.ndarray                        # class types 0/2/3/4 per edge
    counts: np.ndarray                       # occurrence counts per edge
    file_freq: np.ndarray                    # files per edge
    const_pairs: List[Tuple[str, str]]       # constituent class of (u, v)
    edges: List[Tuple[str, str]]


def analyse_edges(g: LatticeGraph, max_edges: Optional[int] = None,
                  min_count: int = 1) -> EdgeAnalysis:
    """Lattice statistics of the joining vectors, vectorised."""
    edges = [(u, v) for (u, v), c in g.adj.items() if c >= min_count]
    edges.sort(key=lambda e: -g.adj[e])
    if max_edges:
        edges = edges[:max_edges]
    D = np.array([list(g.edge_vector(u, v)) for u, v in edges], dtype=np.int64)
    norms2 = (D * D).sum(axis=1)
    types = []
    CH = 512
    for s in range(0, len(D), CH):
        keys = CS.class_keys(D[s:s + CH])
        for k in keys:
            types.append(CS.class_type(tuple(k)))
    counts = np.array([g.adj[e] for e in edges], dtype=np.int64)
    file_freq = np.array([g.edge_file_frequency(*e) for e in edges],
                         dtype=np.int64)
    const_pairs = [(constituent_of(u), constituent_of(v)) for u, v in edges]
    return EdgeAnalysis(n_edges=len(edges), norms2=norms2,
                        types=np.array(types, dtype=np.int64),
                        counts=counts, file_freq=file_freq,
                        const_pairs=const_pairs, edges=edges)


# ---------------------------------------------------------------------------
# reuse
# ---------------------------------------------------------------------------

def module_overlap(g: LatticeGraph) -> Tuple[List[str], np.ndarray, Dict[str, set]]:
    """Jaccard overlap of the part sets of the modules, with the sets."""
    mods = sorted(set(g.file_module.values()))
    sets = {m: set() for m in mods}
    for part, files in g.part_files.items():
        for f in files:
            sets[g.file_module[f]].add(part)
    n = len(mods)
    J = np.zeros((n, n))
    for i, a in enumerate(mods):
        for j, b in enumerate(mods):
            if i == j:
                J[i, j] = 1.0
                continue
            union = len(sets[a] | sets[b])
            J[i, j] = len(sets[a] & sets[b]) / union if union else 0.0
    return mods, J, sets


def shared_joins(g: LatticeGraph, top: int = 30) -> List[dict]:
    """The corpus's construction joints: adjacency edges ranked by the number
    of files that join them, with their lattice geometry."""
    ranked = sorted(g.edge_files, key=lambda e: -len(g.edge_files[e]))
    out = []
    for e in ranked[:top]:
        u, v = e
        modules = sorted({g.file_module[f] for f in g.edge_files[e]})
        out.append({
            "u": u, "v": v,
            "files": len(g.edge_files[e]),
            "count": g.adj[e],
            "modules": len(modules),
            "edge_norm2": g.edge_norm2(u, v),
            "edge_energy": g.edge_norm2(u, v) // 8,
            "edge_class_type": g.edge_class_type(u, v),
        })
    return out


def universal_parts(g: LatticeGraph, min_modules: int) -> List[str]:
    """Parts used by at least ``min_modules`` different modules."""
    out = []
    for part, files in g.part_files.items():
        mods = {g.file_module[f] for f in files}
        if len(mods) >= min_modules:
            out.append(part)
    return sorted(out, key=lambda p: -len(g.part_files[p]))


# ---------------------------------------------------------------------------
# file subgraphs
# ---------------------------------------------------------------------------

@dataclass
class FileSubgraph:
    rel: str
    module: str
    nodes: List[dict]                         # per part: address, reuse, ...
    edges: List[dict]                         # per adjacency edge: count, sharing
    decl_joins: Dict[str, List[str]]          # declaration name -> its parts


def file_subgraph(g: LatticeGraph, rec: FileRecord) -> FileSubgraph:
    """One file's induced lattice-graph, annotated with cross-file reuse."""
    st = structural(rec.toks)
    keys = [t.key for _, t in st]
    nodes = []
    seen = set()
    for k in keys:
        if k in seen:
            continue
        seen.add(k)
        a = g.addresses[k]
        nodes.append({
            "part": k,
            "constituent": constituent_of(k),
            "address": list(a),
            "energy": sum(c * c for c in a) // 8,
            "files_using": g.doc_frequency(k),
            "modules_using": len({g.file_module[f] for f in g.part_files[k]}),
        })
    edges = []
    seen_e = set()
    for a, b in zip(keys, keys[1:]):
        e = (a, b)
        if e in seen_e:
            continue
        seen_e.add(e)
        edges.append({
            "u": a, "v": b,
            "count": g.adj[e],
            "files_joining": g.edge_file_frequency(a, b),
            "edge_norm2": g.edge_norm2(a, b),
            "edge_class_type": g.edge_class_type(a, b),
        })
    # declaration joins: parts co-occurring in the same top-level declaration
    starts = [i for i, (_, t) in enumerate(st)
              if t.kind == "kw" and t.text in DECL_KW and t.col == 0]
    decl_joins: Dict[str, List[str]] = {}
    for si, i0 in enumerate(starts):
        end = starts[si + 1] if si + 1 < len(starts) else len(st)
        name = st[i0 + 1][1].text if i0 + 1 < len(st) else f"decl{si}"
        parts = []
        pseen = set()
        for j in range(i0, end):
            k = keys[j]
            if k not in pseen:
                pseen.add(k)
                parts.append(k)
        decl_joins[name] = parts
    return FileSubgraph(rel=rec.rel, module=rec.module, nodes=nodes,
                        edges=edges, decl_joins=decl_joins)
