# ══════════════════════════════════════════════════════════════════════════════
# §34  SIMPLICIAL CRG (v3.21.0 — 2-complex topology for the Concept Relation Graph)
# ══════════════════════════════════════════════════════════════════════════════
#
# PURPOSE
#   Move the CRG from a 1-complex (graph: nodes + edges) to a 2-complex
#   (nodes + edges + triangular faces). This is a simplicial complex.
#
#   Why: a "relation" is currently binary (A —label→ B), but much of the
#   structure GLM cares about is genuinely ternary — {boson, fermion, spin},
#   {hamiltonian, time, energy}, {lattice, continuum, continuum limit}.
#   A 2-simplex (filled triangle) captures "these three concepts cohere as
#   a unit" without privileging any one pair.
#
#   Once we have faces, we get a topological notion of coherence for free:
#   an argument backbone is a 1-chain (path of edges). We can ask whether
#   that path is the boundary of a union of faces. If it is, the argument
#   "fills" — there are no holes. If it isn't, the residual cycle is a
#   hole — a geometry-driven signal of a reasoning gap.
#
#   This generalises the existing contradiction_penalty from "bad edge
#   present" to "good cycle absent."
#
# WHAT THIS MODULE IMPLEMENTS (ideas 1–6 from the design notes)
#
#   1. Nodes as positions — each concept's BLA vector is coordinates in
#      {0,1}^24; Hamming distance is the L1 metric on that cube.
#   2. Node intrinsic geometry — degree (1-skeleton), stellar count
#      (2-skeleton degree = incident faces), bridge_score (node B mediates
#      A–C if d(A,C) = d(A,B) + d(B,C) — B lies on a Hamming geodesic).
#   3. Faces as 2-simplices — find 3-cliques in the non-contradiction edge
#      graph, keep only "tight" ones using a Hamming-area filter. Each face
#      stores side lengths (a,b,c), Heron area, circumradius.
#   4. Triangle-shape semantics — equilateral = symmetric triad (peers),
#      isosceles = two close + one outlier, degenerate = bridge triple.
#   5. Boundary operators over GF(2) — C₂ →∂₂ C₁ →∂₁ C₀. A backbone is
#      a 1-chain; if it's a cycle (∂₁=0) and lies in im ∂₂, it bounds a
#      set of faces — coherent. Otherwise the residual is a hole.
#   6. Betti numbers and Euler characteristic as global CRG health metrics:
#      χ = V − E + F = β₀ − β₁ + β₂
#      β₀ = connected components, β₁ = independent holes, β₂ = enclosed voids.
#      A "healthy" knowledge base should have small β₁ — few unfilled loops.
#
# AUTHOR
#   Z.ai v3.21 development push — 2026-07-08
#   Based on the simplicial CRG design notes (Pasted Content_1783529288399.txt)
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import math
import itertools
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

# ── GLM imports ─────────────────────────────────────────────────────────────
try:
    from GLM01_substrate import (
        ConceptRelationGraph, CRGEdge,
        vector_to_hex_int, fast_hamming, BLA,
        _get_mog_category,
    )
    _HAS_GLM = True
except Exception as _e:
    _HAS_GLM = False
    _GLM_ERR = str(_e)


# ══════════════════════════════════════════════════════════════════════════════
#  1. DATA CLASSES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CRGFace:
    """A 2-simplex: an oriented triple of concept nodes.

    Attributes
    ----------
    nodes : Tuple[str, str, str]
        Sorted triple (a ≤ b ≤ c) of concept names.
    label : str
        Semantic label for the face (e.g. "coherent_triad").
    sides : Tuple[int, int, int]
        Hamming distances (ab, bc, ac).
    area : float
        Heron's formula area. 0 = degenerate (collinear/bridge triple).
    circumradius : float
        R = abc / (4*area). inf for degenerate faces.
    degenerate : bool
        True if area ≈ 0 (the three nodes are collinear on a Hamming geodesic).
    """
    nodes: Tuple[str, str, str]
    label: str
    sides: Tuple[int, int, int]
    area: float
    circumradius: float
    degenerate: bool

    @property
    def shape(self) -> str:
        """Classify the triangle shape: 'equilateral', 'isosceles', 'scalene', 'degenerate'."""
        if self.degenerate:
            return "degenerate"
        a, b, c = self.sides
        if a == b == c:
            return "equilateral"
        if a == b or b == c or a == c:
            return "isosceles"
        return "scalene"


@dataclass
class NodeGeom:
    """Geometric / topological attributes of a single node."""
    name: str
    hex_int: int
    zone: str
    degree: int = 0           # 1-skeleton degree
    stellar: int = 0          # 2-skeleton degree (incident faces)
    bridge_score: int = 0     # number of (A,C) pairs this node mediates geodesically


@dataclass
class TopologyReport:
    """Global topology report for the simplicial CRG."""
    n_vertices: int
    n_edges: int
    n_faces: int
    beta0: int                # connected components
    beta1: int                # independent holes (1-cycles that don't bound faces)
    beta2: int                # enclosed voids
    euler: int                # χ = V - E + F
    mean_stellar: float
    max_stellar: int
    overheating_violations: int  # nodes with stellar > 9
    fillable_cycles: int         # faces whose boundary is a fillable 1-cycle


# ══════════════════════════════════════════════════════════════════════════════
#  2. GF(2) LINEAR ALGEBRA (for boundary operators)
# ══════════════════════════════════════════════════════════════════════════════

def _gf2_rank_reduce(cols: List[int]) -> Dict[int, int]:
    """Return pivot map {highest_bit: row_index} for the column set over GF(2).

    Each column is an integer bitmask. The rank is the number of pivots.
    """
    if not cols:
        return {}
    aug = list(cols)
    pivots: Dict[int, int] = {}
    for i in range(len(aug)):
        m = aug[i]
        while m:
            hb = m.bit_length() - 1
            if hb in pivots:
                m ^= aug[pivots[hb]]
            else:
                pivots[hb] = i
                aug[i] = m
                break
        aug[i] = m
    return pivots


def _gf2_solve(cols: List[int], target: int) -> Optional[List[int]]:
    """Solve sum_i x_i * cols[i] = target (mod 2). Returns x or None.

    Uses Gaussian elimination over GF(2).
    """
    if not cols:
        return [] if target == 0 else None
    n = len(cols)
    aug = list(cols)
    origin = [1 << i for i in range(n)]  # track which original columns are involved

    pivots: Dict[int, int] = {}
    for i in range(n):
        m = aug[i]
        while m:
            hb = m.bit_length() - 1
            if hb in pivots:
                m ^= aug[pivots[hb]]
                origin[i] ^= origin[pivots[hb]]
            else:
                pivots[hb] = i
                break
        aug[i] = m
        # origin[i] already updated

    # Now back-substitute to solve for target
    cur = target
    orx = 0
    for hb in sorted(pivots.keys(), reverse=True):
        if (cur >> hb) & 1:
            idx = pivots[hb]
            cur ^= aug[idx]
            orx ^= origin[idx]
    if cur != 0:
        return None
    return [(orx >> i) & 1 for i in range(n)]


# ══════════════════════════════════════════════════════════════════════════════
#  3. THE SIMPLICIAL CRG
# ══════════════════════════════════════════════════════════════════════════════

# Edges to skip when building the 1-skeleton for topology
_SKIP_EDGE_LABELS = {"contradicts", "incompatible_with", "auto_proposed"}


class SimplicialCRG:
    """A CRG augmented with 2-simplices (faces) and topological operators.

    Construction
    ------------
    scrg = SimplicialCRG(crg)
    discover_faces(scrg, vocab_words, max_side=8)
    scrg.build_node_geometry(vocab_words)
    """

    def __init__(self, crg: ConceptRelationGraph):
        self.crg = crg
        self.faces: Dict[Tuple[str, str, str], CRGFace] = {}
        self._node_geom: Dict[str, NodeGeom] = {}

    # ── Face management ─────────────────────────────────────────────────

    def add_face(self, a: str, b: str, c: str, label: str,
                 hex_cache: Dict[str, int]) -> CRGFace:
        """Add a triangular face (2-simplex) to the complex.

        Computes Hamming side lengths, Heron area, circumradius, and
        degeneracy flag.
        """
        nodes = tuple(sorted([a, b, c]))
        if nodes in self.faces:
            return self.faces[nodes]
        ab = fast_hamming(hex_cache[a], hex_cache[b])
        bc = fast_hamming(hex_cache[b], hex_cache[c])
        ac = fast_hamming(hex_cache[a], hex_cache[c])
        s = (ab + bc + ac) / 2.0
        area = math.sqrt(max(0.0, s * (s - ab) * (s - bc) * (s - ac)))
        degen = area < 1e-9
        R = (ab * bc * ac) / (4.0 * area) if area > 1e-9 else float("inf")
        f = CRGFace(nodes, label, (ab, bc, ac), area, R, degen)
        self.faces[nodes] = f
        return f

    def faces_of(self, node: str) -> List[CRGFace]:
        """Return all faces incident to a given node."""
        return [f for f in self.faces.values() if node in f.nodes]

    # ── Node geometry ───────────────────────────────────────────────────

    def build_node_geometry(self, vocab_words: Dict[str, Any],
                            bridge_cap: int = 300) -> Dict[str, NodeGeom]:
        """Compute geometric/topological attributes for every node.

        Parameters
        ----------
        vocab_words : Dict[str, Any]
            The vocabulary dict (word → WordEntry with .vector and .role).
        bridge_cap : int
            Maximum number of nodes to check for bridge_score (O(n²) cost).
            Default 300 — increase for larger vocabs.
        """
        hex_cache: Dict[str, int] = {}
        zones: Dict[str, str] = {}
        for name, entry in vocab_words.items():
            if getattr(entry, "role", None) in ("NOUN", "PROPERTY") and \
               getattr(entry, "vector", None):
                try:
                    hex_cache[name] = vector_to_hex_int(entry.vector)
                    zones[name] = _get_mog_category(entry.vector)
                except Exception:
                    continue

        # 1-skeleton degree (undirected, ignoring contradiction edges)
        deg: Dict[str, int] = defaultdict(int)
        for e in self.crg.edges:
            if e.label in _SKIP_EDGE_LABELS:
                continue
            deg[e.src] += 1
            deg[e.dst] += 1

        geom: Dict[str, NodeGeom] = {}
        names = list(hex_cache.keys())
        for n in names:
            geom[n] = NodeGeom(
                n, hex_cache[n], zones.get(n, "?"),
                degree=deg.get(n, 0),
                stellar=len(self.faces_of(n))
            )

        # bridge_score: B mediates A–C if d(A,C) == d(A,B) + d(B,C)
        # (B lies on a Hamming geodesic between A and C)
        if len(names) <= bridge_cap:
            for i, b in enumerate(names):
                hb = hex_cache[b]
                for j, a in enumerate(names):
                    if j == i:
                        continue
                    ha = hex_cache[a]
                    d_ab = fast_hamming(ha, hb)
                    for c in names[j+1:]:
                        if c == b:
                            continue
                        hc = hex_cache[c]
                        d_bc = fast_hamming(hb, hc)
                        d_ac = fast_hamming(ha, hc)
                        if d_ac == d_ab + d_bc:
                            geom[b].bridge_score += 1

        self._node_geom = geom
        return geom

    # ── Index the complex for topology ──────────────────────────────────

    def _index_complex(self) -> Tuple[
        List[str],                          # node_index
        List[Tuple[str, str]],              # edge_index (sorted pairs)
        Dict[Tuple[str, str], int],         # edge_lookup
        List[Tuple[str, str, str]],         # face_index (sorted triples)
        Dict[Tuple[str, str, str], int],    # face_lookup
        List[int],                          # d1 columns (C₁ → C₀)
        List[int],                          # d2 columns (C₂ → C₁)
    ]:
        """Build the indexed chain complex for GF(2) homology computation."""
        # Collect nodes that appear in edges or faces
        node_set: Set[str] = set()
        edge_set: Set[Tuple[str, str]] = set()
        for e in self.crg.edges:
            if e.label in _SKIP_EDGE_LABELS:
                continue
            key = tuple(sorted([e.src, e.dst]))
            edge_set.add(key)
            node_set.update(key)
        for f in self.faces.values():
            a, b, c = f.nodes
            node_set.update(f.nodes)
            edge_set.add(tuple(sorted([a, b])))
            edge_set.add(tuple(sorted([b, c])))
            edge_set.add(tuple(sorted([a, c])))

        node_index = sorted(node_set)
        node_lookup = {n: i for i, n in enumerate(node_index)}
        edge_index = sorted(edge_set)
        edge_lookup = {e: i for i, e in enumerate(edge_index)}
        face_index = sorted(self.faces.keys())
        face_lookup = {f: i for i, f in enumerate(face_index)}

        # ∂₁: C₁ → C₀  (column per edge: bits at its two endpoints)
        d1_cols: List[int] = []
        for (u, v) in edge_index:
            m = (1 << node_lookup[u]) | (1 << node_lookup[v])
            d1_cols.append(m)

        # ∂₂: C₁ → C₁  (column per face: bits at its three edges)
        d2_cols: List[int] = []
        for (a, b, c) in face_index:
            m = 0
            for (u, v) in [(a, b), (b, c), (a, c)]:
                key = tuple(sorted([u, v]))
                if key in edge_lookup:
                    m |= 1 << edge_lookup[key]
            d2_cols.append(m)

        return (node_index, edge_index, edge_lookup,
                face_index, face_lookup, d1_cols, d2_cols)

    # ── Betti numbers and Euler characteristic ──────────────────────────

    def betti(self) -> Tuple[int, int, int]:
        """Return (β₀, β₁, β₂).

        β₀ = V − rank(∂₁)               — connected components
        β₁ = (E − rank(∂₁)) − rank(∂₂)  — independent holes
        β₂ = F − rank(∂₂)               — enclosed voids
        """
        (nidx, elist, _, flist, _, d1, d2) = self._index_complex()
        V, E, F = len(nidx), len(elist), len(flist)
        r1 = len(_gf2_rank_reduce(d1))
        r2 = len(_gf2_rank_reduce(d2))
        beta0 = V - r1
        beta1 = (E - r1) - r2
        beta2 = F - r2
        return beta0, max(0, beta1), max(0, beta2)

    def euler(self) -> int:
        """Euler characteristic χ = V − E + F."""
        (nidx, elist, _, flist, _, _, _) = self._index_complex()
        return len(nidx) - len(elist) + len(flist)

    def topology_report(self) -> TopologyReport:
        """Full topology dashboard."""
        (nidx, elist, _, flist, _, _, _) = self._index_complex()
        b0, b1, b2 = self.betti()
        stellar = [len(self.faces_of(n)) for n in nidx]
        over = sum(1 for s in stellar if s > 9)
        return TopologyReport(
            n_vertices=len(nidx),
            n_edges=len(elist),
            n_faces=len(flist),
            beta0=b0, beta1=b1, beta2=b2,
            euler=len(nidx) - len(elist) + len(flist),
            mean_stellar=(sum(stellar) / len(stellar)) if stellar else 0.0,
            max_stellar=max(stellar) if stellar else 0,
            overheating_violations=over,
            fillable_cycles=len(flist),
        )

    # ── Backbone coherence (topological upgrade of contradiction_penalty) ──

    def backbone_1chain(self, backbone: List[CRGEdge]) -> int:
        """Represent a backbone as a 1-chain (bitmask over C₁)."""
        (_, _, elookup, _, _, _, _) = self._index_complex()
        chain = 0
        for e in backbone:
            key = tuple(sorted([e.src, e.dst]))
            if key in elookup:
                chain ^= 1 << elookup[key]
        return chain

    def backbone_is_filled(self, backbone: List[CRGEdge]) -> bool:
        """True iff the backbone 1-chain is a boundary of some faces.

        This means the path "fills" — there are no holes.
        """
        (_, _, _, _, _, _, d2) = self._index_complex()
        chain = self.backbone_1chain(backbone)
        sol = _gf2_solve(d2, chain)
        return sol is not None

    def backbone_face_support(self, backbone: List[CRGEdge]) -> int:
        """How many faces touch at least one backbone edge (higher = better supported)."""
        supp = 0
        for f in self.faces.values():
            a, b, c = f.nodes
            fedges = {tuple(sorted([a, b])), tuple(sorted([b, c])),
                      tuple(sorted([a, c]))}
            if any(tuple(sorted([e.src, e.dst])) in fedges for e in backbone):
                supp += 1
        return supp

    def topological_coherence(self, backbone: List[CRGEdge]) -> float:
        """[0,1] coherence: filled cycles score high; unsupported paths score low.

        This is the topological upgrade of contradiction_penalty:
        - contradiction_penalty catches "bad edge present"
        - topological_coherence catches "good cycle absent"
        """
        if not backbone:
            return 1.0
        support = self.backbone_face_support(backbone)
        norm = support / max(1, len(backbone))
        filled_bonus = 0.25 if self.backbone_is_filled(backbone) else 0.0
        return min(1.0, 0.5 * min(1.0, norm) + filled_bonus + 0.25)


# ══════════════════════════════════════════════════════════════════════════════
#  4. FACE DISCOVERY
# ══════════════════════════════════════════════════════════════════════════════

def discover_faces(scrg: SimplicialCRG, vocab_words: Dict[str, Any],
                   max_side: int = 8, max_circumradius: float = 50.0,
                   max_faces: int = 200) -> List[CRGFace]:
    """Find 3-cliques in the non-contradiction graph, keep the tight geometric ones.

    Parameters
    ----------
    scrg : SimplicialCRG
        The simplicial CRG to add faces to.
    vocab_words : Dict[str, Any]
        The vocabulary dict (word → WordEntry with .vector).
    max_side : int
        Maximum Hamming distance for any side of the triangle.
    max_circumradius : float
        Maximum circumradius (filters out "flat" triangles).
    max_faces : int
        Maximum number of faces to discover.
    """
    # Build hex cache for all NOUN/PROPERTY words with vectors
    hex_cache: Dict[str, int] = {}
    for name, entry in vocab_words.items():
        if getattr(entry, "role", None) in ("NOUN", "PROPERTY") and \
           getattr(entry, "vector", None):
            try:
                hex_cache[name] = vector_to_hex_int(entry.vector)
            except Exception:
                continue

    # Build undirected adjacency, skip contradiction/auto_proposed edges
    adj: Dict[str, Set[str]] = defaultdict(set)
    for e in scrg.crg.edges:
        if e.label in _SKIP_EDGE_LABELS:
            continue
        adj[e.src].add(e.dst)
        adj[e.dst].add(e.src)

    found: List[CRGFace] = []
    seen: Set[FrozenSet[str]] = set()
    nodes_sorted = sorted(adj.keys())

    for a in nodes_sorted:
        neighbours = sorted(adj[a])
        for b, c in itertools.combinations(neighbours, 2):
            if c not in adj[b]:
                continue
            tri = frozenset([a, b, c])
            if tri in seen:
                continue
            seen.add(tri)
            if not all(x in hex_cache for x in tri):
                continue
            f = scrg.add_face(a, b, c, "coherent_triad", hex_cache)
            if f.degenerate:
                continue  # bridge triple, not a real face
            if max(f.sides) > max_side:
                continue
            if f.circumradius > max_circumradius:
                continue
            found.append(f)
            if len(found) >= max_faces:
                return found
    return found


# ══════════════════════════════════════════════════════════════════════════════
#  5. CONVENIENCE BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def build_simplicial_crg(vocab_words: Dict[str, Any],
                         max_side: int = 8,
                         max_faces: int = 200) -> SimplicialCRG:
    """End-to-end: build extended CRG + discover faces + compute node geometry.

    Parameters
    ----------
    vocab_words : Dict[str, Any]
        The vocabulary dict.
    max_side : int
        Maximum Hamming side length for faces.
    max_faces : int
        Maximum faces to discover.

    Returns
    -------
    SimplicialCRG
        A fully built simplicial CRG with faces and node geometry.
    """
    from GLM03_crg import build_extended_crg
    crg = build_extended_crg()
    scrg = SimplicialCRG(crg)
    discover_faces(scrg, vocab_words, max_side=max_side, max_faces=max_faces)
    scrg.build_node_geometry(vocab_words)
    return scrg


# ══════════════════════════════════════════════════════════════════════════════
#  6. STATUS / SELF-TEST
# ══════════════════════════════════════════════════════════════════════════════

def status() -> Dict[str, Any]:
    return {
        "module": "GLM34_simplicial_crg",
        "version": "3.21.0",
        "operations": ["add_face", "build_node_geometry", "betti", "euler",
                       "topology_report", "backbone_is_filled",
                       "backbone_face_support", "topological_coherence",
                       "discover_faces", "build_simplicial_crg"],
    }


if __name__ == "__main__":
    print("=== GLM34 Simplicial CRG v3.21.0 — self-test ===")
    print(status())
    print()

    if not _HAS_GLM:
        print("GLM substrate unavailable — cannot run demo.")
        raise SystemExit(1)

    from GLM01_substrate import _build_vocabulary
    print("Building vocabulary...")
    vocab = _build_vocabulary()

    print("Building simplicial CRG (this may take a moment)...")
    scrg = build_simplicial_crg(vocab, max_side=8, max_faces=100)

    print(f"\n✅ Faces discovered: {len(scrg.faces)}")
    rep = scrg.topology_report()
    print(f"✅ V={rep.n_vertices}  E={rep.n_edges}  F={rep.n_faces}")
    print(f"✅ Betti (β₀, β₁, β₂) = ({rep.beta0}, {rep.beta1}, {rep.beta2})")
    print(f"✅ Euler characteristic χ = {rep.euler}")
    print(f"✅ Stellar: mean={rep.mean_stellar:.2f}  max={rep.max_stellar}  overheats={rep.overheating_violations}")

    # Show the 5 tightest faces
    tight = sorted(scrg.faces.values(), key=lambda f: f.area)[:5]
    print(f"\n--- 5 tightest faces ---")
    for f in tight:
        print(f"  {f.nodes}  sides={f.sides}  area={f.area:.3f}  shape={f.shape}")

    # Show top bridges
    bridges = sorted(scrg._node_geom.values(),
                     key=lambda g: -g.bridge_score)[:5]
    print(f"\n--- top 5 bridge concepts ---")
    for g in bridges:
        print(f"  {g.name}  bridge_score={g.bridge_score}  stellar={g.stellar}  degree={g.degree}")

    # Test backbone coherence on a real backbone
    print(f"\n--- backbone coherence test ---")
    from GLM11_runtime import GLMRuntimeV37
    rt = GLMRuntimeV37(auto_expand=False)
    rt.reset_idea()
    rt.chat("Tell me about the hamiltonian and time.")
    zone = rt.manager.active
    if hasattr(zone, 'crg_backbone') and zone.crg_backbone:
        tc = scrg.topological_coherence(zone.crg_backbone)
        filled = scrg.backbone_is_filled(zone.crg_backbone)
        support = scrg.backbone_face_support(zone.crg_backbone)
        print(f"  backbone: {[(e.src, e.label, e.dst) for e in zone.crg_backbone]}")
        print(f"  topological_coherence: {tc:.3f}")
        print(f"  is_filled: {filled}")
        print(f"  face_support: {support}")
    else:
        print("  no backbone available")
