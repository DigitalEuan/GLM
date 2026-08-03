#!/usr/bin/env python3
"""
GLM TOOLS v2 — Coherence & Geometry Expansion Pack
=====================================================
New tools derived from the Holographic Arithmetic Engine research
and the GLM Mathematical Methods Checklist.

These tools extend the base GLM_tools.py with methods targeting
coherence, topological integrity, and self-assembling value geometry.

NEW TOOLS:
11. VALUE_GEOMETRY    — Self-assembling value geometry (omega, lattice type, 144° modulus)
12. RICCI_CURVATURE   — Forman-Ricci curvature on CRG edges (bottleneck detection)
13. GHOST_FILTER      — Filter high-NRCI but low-connectivity transient concepts
14. TOPOLOGICAL_HEALTH — Betti numbers (β₀, β₁) and connected component analysis
15. RESONANCE_TUNNEL  — Bond concepts sharing dominant sextet beyond Hamming-3
16. REFINED_NRCI      — Multi-shell NRCI with Y₀ = 1/(π + 2/π) constant
17. COSINE_SIMILARITY — Angular similarity between 24-bit concept vectors
18. SEXTET_PARITY     — Check/force geometric domain alignment via sextet parity
"""

import math
import re
from typing import List, Dict, Tuple, Any, Optional, Set
from collections import defaultdict, deque


# ═══════════════════════════════════════════════════════════════════════════
# §11  VALUE GEOMETRY — Self-Assembling Value Geometry
# ═══════════════════════════════════════════════════════════════════════════
# From the audio research: every integer autonomously determines its own
# geometric profile based strictly on its prime factorization.
#   - ω (omega) = number of DISTINCT prime factors → dimensionality
#   - Largest prime factor p:
#       p ≡ 1 (mod 4) → Gaussian lattice (square grid)
#       p ≡ 1 (mod 3) → Eisenstein lattice (hexagonal grid)
#       otherwise      → Rectangular lattice
#   - 144° modulus: sum of all Platonic solid face angles = 14,400° = 100 × 144° = 80π

# The five Platonic solid total face angles (the 144° identity)
_PLATONIC_FACE_ANGLES = {
    "tetrahedron":  720,     # 4 triangles × 180°
    "cube":         2160,    # 6 squares × 360°
    "octahedron":   1440,    # 8 triangles × 180°
    "dodecahedron": 6480,    # 12 pentagons × 540°
    "icosahedron":  3600,    # 20 triangles × 180°
}
_PLATONIC_TOTAL = sum(_PLATONIC_FACE_ANGLES.values())  # 14,400
_MODULUS_144 = 144  # 14,400 / 100
_RADIAN_EQUIVALENT = 80 * math.pi  # in radians


def _distinct_prime_factors(n: int) -> List[int]:
    """Return the sorted list of distinct prime factors of n."""
    if n < 2:
        return []
    factors = set()
    d = 2
    temp = n
    while d * d <= temp:
        while temp % d == 0:
            factors.add(d)
            temp //= d
        d += 1
    if temp > 1:
        factors.add(temp)
    return sorted(factors)


def _largest_prime_factor(n: int) -> int:
    """Return the largest prime factor of n."""
    factors = _distinct_prime_factors(n)
    return max(factors) if factors else n


def value_geometry(n: int) -> Dict[str, Any]:
    """Compute the self-assembling geometric profile of an integer.

    Implements the Holographic Arithmetic Engine's value geometry:
    every integer has an intrinsic geometric blueprint determined by
    its prime factorization.

    Parameters
    ----------
    n : int
        The integer to analyze.

    Returns
    -------
    dict with keys: omega, dimensionality, prime_factors, largest_prime,
                    lattice_type, lattice_mod, platonic_resonance,
                    modulus_144_class, angular_signature
    """
    if n < 1:
        return {"error": "Only positive integers have value geometry"}

    primes = _distinct_prime_factors(n)
    omega = len(primes)  # number of distinct prime factors

    # Dimensionality from omega
    dim_names = {0: "point", 1: "line", 2: "plane", 3: "volume",
                 4: "4-manifold", 5: "5-manifold"}
    dimensionality = min(omega, 5)
    dim_name = dim_names.get(dimensionality, f"{dimensionality}-manifold")

    # Lattice type from largest prime factor
    lp = _largest_prime_factor(n) if primes else n
    if lp % 4 == 1:
        lattice_type = "gaussian"
        lattice_mod = f"{lp} ≡ 1 (mod 4)"
        lattice_desc = "square Gaussian lattice (Z[i])"
    elif lp % 3 == 1:
        lattice_type = "eisenstein"
        lattice_mod = f"{lp} ≡ 1 (mod 3)"
        lattice_desc = "hexagonal Eisenstein lattice (Z[ω])"
    elif lp == 2:
        lattice_type = "dyadic"
        lattice_mod = "p = 2 (dyadic)"
        lattice_desc = "dyadic 2-adic lattice"
    else:
        lattice_type = "rectangular"
        lattice_mod = f"{lp} mod classes: {lp % 4} (mod 4), {lp % 3} (mod 3)"
        lattice_desc = "rectangular lattice"

    # 144° modulus class
    mod_class = n % _MODULUS_144

    # Platonic resonance: which Platonic solid's face angle sum
    # is closest to n mod 14400?
    platonic_res = min(_PLATONIC_FACE_ANGLES.items(),
                       key=lambda kv: abs(n % _PLATONIC_TOTAL - kv[1]))

    # Angular signature: map n into the 144° circle
    angular_signature = (n % _MODULUS_144) / _MODULUS_144 * 360.0

    return {
        "n": n,
        "omega": omega,
        "dimensionality": dimensionality,
        "dim_name": dim_name,
        "prime_factors": primes,
        "largest_prime": lp,
        "lattice_type": lattice_type,
        "lattice_mod": lattice_mod,
        "lattice_desc": lattice_desc,
        "modulus_144_class": mod_class,
        "angular_signature_deg": round(angular_signature, 2),
        "platonic_resonance": platonic_res[0],
        "platonic_angle": platonic_res[1],
        "platonic_total_identity": _PLATONIC_TOTAL,
    }


# ═══════════════════════════════════════════════════════════════════════════
# §12  RICCI CURVATURE — Forman-Ricci on CRG Edges
# ═══════════════════════════════════════════════════════════════════════════
# Forman-Ricci curvature is a combinatorial alternative to Ollivier-Ricci.
# For an edge (u,v), F(u,v) = 4 - deg(u) - deg(v).
# Negative values indicate bottleneck edges whose removal would
# disconnect the graph. This directly measures CRG structural health.

def forman_ricci_edge(crg, src: str, dst: str) -> Dict[str, Any]:
    """Compute Forman-Ricci curvature for a single CRG edge.

    F(u,v) = 4 - deg(u) - deg(v)

    Returns dict with curvature value and interpretation.
    """
    def _degree(node):
        # Count non-trivial outgoing edges (exclude self-loops and lattice_adjacent)
        count = 0
        for e in crg.out.get(node, []):
            if e.src != e.dst and not e.label.startswith('lattice_adjacent'):
                count += 1
        for e in crg.inn.get(node, []):
            if e.src != e.dst and not e.label.startswith('lattice_adjacent'):
                count += 1
        return max(count, 1)

    deg_u = _degree(src)
    deg_v = _degree(dst)
    curvature = 4.0 - deg_u - deg_v

    if curvature > 0:
        interpretation = "redundant (multiple paths exist)"
        health = "robust"
    elif curvature == 0:
        interpretation = "balanced (exactly 2 paths through each endpoint)"
        health = "stable"
    elif curvature > -2:
        interpretation = "mild bottleneck (few alternative paths)"
        health = "fragile"
    else:
        interpretation = "critical bottleneck (bridge edge — removal disconnects)"
        health = "critical"

    return {
        "src": src, "dst": dst,
        "deg_src": deg_u, "deg_dst": deg_v,
        "forman_ricci": curvature,
        "interpretation": interpretation,
        "health": health
    }


def ricci_curvature_report(crg, top_n: int = 10) -> Dict[str, Any]:
    """Compute Forman-Ricci curvature for all CRG edges.

    Returns a ranked report of bottleneck edges and graph health summary.
    """
    SKIP = {"auto_proposed", "co_occurs"}
    edge_curvatures = []

    for src, edges in crg.out.items():
        for e in edges:
            if e.label in SKIP or e.src == e.dst:
                continue
            if e.label.startswith('lattice_adjacent'):
                continue
            fc = forman_ricci_edge(crg, e.src, e.dst)
            fc["label"] = e.label
            edge_curvatures.append(fc)

    # Sort by curvature (most negative first = worst bottlenecks)
    edge_curvatures.sort(key=lambda x: x["forman_ricci"])

    bottlenecks = [e for e in edge_curvatures if e["forman_ricci"] < 0]
    critical = [e for e in edge_curvatures if e["health"] == "critical"]

    avg_curvature = (sum(e["forman_ricci"] for e in edge_curvatures) / len(edge_curvatures)
                     if edge_curvatures else 0)

    # Compute degree distribution for context
    nodes = set()
    for src, edges in crg.out.items():
        for e in edges:
            if e.label not in SKIP and e.src != e.dst and not e.label.startswith('lattice_adjacent'):
                nodes.add(e.src)
                nodes.add(e.dst)

    return {
        "total_edges": len(edge_curvatures),
        "avg_curvature": round(avg_curvature, 4),
        "bottleneck_count": len(bottlenecks),
        "critical_count": len(critical),
        "graph_health": "healthy" if avg_curvature >= -1 else
                        "stressed" if avg_curvature >= -3 else "degraded",
        "worst_bottlenecks": edge_curvatures[:top_n],
        "critical_bridges": critical[:5],
    }


# ═══════════════════════════════════════════════════════════════════════════
# §13  GHOST FILTER — High-NRCI Low-Connectivity Hallucination Filter
# ═══════════════════════════════════════════════════════════════════════════
# LAW_TOPOLOGICAL_TENACITY_001: Filter out concepts with high NRCI but
# zero "Lock Pressure" (connectivity). These are transient ghosts —
# vectors that happen to sit near Golay codewords but have no
# structural support in the knowledge graph.

def ghost_filter(crg, vocab, nrci_threshold: float = 0.5,
                 min_connections: int = 1) -> Dict[str, Any]:
    """Identify ghost concepts: high-NRCI but poorly connected.

    A ghost is a concept whose vector has high coherence (NRCI) but
    lacks structural support in the CRG (few or no meaningful edges).
    These represent hallucinated or transient concepts.

    Parameters
    ----------
    crg : ConceptRelationGraph
    nrci_threshold : float
        Minimum NRCI to be considered "high coherence"
    min_connections : int
        Minimum number of meaningful CRG connections to not be a ghost

    Returns
    -------
    dict with ghosts, locked concepts, and filter statistics
    """
    SKIP = {"auto_proposed", "co_occurs", "contradicts", "incompatible_with"}

    vocab_dict = vocab.words if hasattr(vocab, 'words') else vocab
    ghosts = []
    locked = []

    for word, entry in vocab_dict.items():
        if not hasattr(entry, 'vector') or not hasattr(entry, 'nrci'):
            continue

        nrci = float(entry.nrci)
        if nrci < nrci_threshold:
            continue

        # Count meaningful connections
        connections = 0
        connection_labels = []
        for e in crg.out.get(word, []):
            if e.label not in SKIP and e.src != e.dst and not e.label.startswith('lattice_adjacent'):
                connections += 1
                connection_labels.append(f"{e.label}→{e.dst}")

        if connections < min_connections:
            ghosts.append({
                "word": word,
                "nrci": round(nrci, 4),
                "connections": connections,
                "lock_pressure": 0.0,
                "verdict": "GHOST (high coherence, no structural support)"
            })
        else:
            # Compute lock pressure = connections / max_possible
            lock_pressure = min(connections / 5.0, 1.0)
            locked.append({
                "word": word,
                "nrci": round(nrci, 4),
                "connections": connections,
                "lock_pressure": round(lock_pressure, 3),
                "top_edges": connection_labels[:3]
            })

    return {
        "total_high_nrci": len(ghosts) + len(locked),
        "ghost_count": len(ghosts),
        "locked_count": len(locked),
        "ghost_rate": round(len(ghosts) / max(1, len(ghosts) + len(locked)), 3),
        "ghosts": ghosts,
        "locked": sorted(locked, key=lambda x: -x["lock_pressure"])[:20],
        "verdict": "healthy" if len(ghosts) < len(locked) * 0.3 else "ghost-heavy"
    }


# ═══════════════════════════════════════════════════════════════════════════
# §14  TOPOLOGICAL HEALTH — Betti Numbers & Connected Components
# ═══════════════════════════════════════════════════════════════════════════
# β₀ = number of connected components (should be 1 for a healthy CRG)
# β₁ = number of independent cycles (loops in the knowledge graph)
# These are computed via BFS/DFS on the 1-skeleton (graph structure).

def topological_health(crg) -> Dict[str, Any]:
    """Compute topological invariants of the CRG.

    Returns Betti numbers (β₀, β₁), connected components,
    and structural health metrics.
    """
    SKIP = {"auto_proposed", "co_occurs"}
    adj = defaultdict(set)

    for src, edges in crg.out.items():
        for e in edges:
            if e.label in SKIP or e.src == e.dst:
                continue
            if e.label.startswith('lattice_adjacent'):
                continue
            adj[e.src].add(e.dst)
            adj[e.dst].add(e.src)  # undirected for topology

    if not adj:
        return {"beta_0": 0, "beta_1": 0, "components": 0,
                "nodes": 0, "edges": 0, "health": "empty"}

    # β₀: Connected components via BFS
    visited = set()
    components = []
    all_nodes = set(adj.keys())
    # Also add nodes that only appear as destinations
    for src, edges in crg.out.items():
        for e in edges:
            all_nodes.add(e.dst)

    for node in all_nodes:
        if node in visited:
            continue
        component = []
        queue = deque([node])
        while queue:
            n = queue.popleft()
            if n in visited:
                continue
            visited.add(n)
            component.append(n)
            for neighbor in adj[n]:
                if neighbor not in visited:
                    queue.append(neighbor)
        components.append(component)

    beta_0 = len(components)
    total_nodes = len(all_nodes)
    total_edges = sum(len(neighbors) for neighbors in adj.values()) // 2  # undirected

    # β₁: Number of independent cycles = E - V + β₀ (Euler characteristic for 1-skeleton)
    # For a graph: χ = V - E = β₀ - β₁  →  β₁ = β₀ - V + E
    beta_1 = max(0, total_edges - total_nodes + beta_0)

    # Largest component
    largest = max(components, key=len) if components else []
    largest_pct = len(largest) / max(1, total_nodes) * 100

    # Isolated nodes (no edges)
    isolated = [n for n in all_nodes if n not in adj]

    health = "connected" if beta_0 == 1 else "fragmented"
    if beta_0 == 1 and beta_1 >= 3:
        health = "richly_connected"

    return {
        "beta_0": beta_0,           # connected components
        "beta_1": beta_1,           # independent cycles
        "euler_characteristic": total_nodes - total_edges,
        "nodes": total_nodes,
        "edges": total_edges,
        "components": beta_0,
        "largest_component_size": len(largest),
        "largest_component_pct": round(largest_pct, 1),
        "isolated_nodes": len(isolated),
        "isolated_list": isolated[:10],
        "health": health,
        "component_sizes": sorted([len(c) for c in components], reverse=True)[:5],
    }


# ═══════════════════════════════════════════════════════════════════════════
# §15  RESONANCE TUNNEL — Sextet-Based Bonding Beyond Hamming-3
# ═══════════════════════════════════════════════════════════════════════════
# The 3-3-3 Golay Limit says concepts with Hamming distance ≤ 3 form
# unbreakable "Lattice Snaps". But concepts with d > 3 that share
# the same Dominant Sextet (Harmonic Key) can still bond tightly
# via "Resonance Tunneling".

def _dominant_sextet(vector) -> int:
    """Return the index of the sextet (0-3) with the most bits set."""
    bits = [0, 0, 0, 0]
    for i in range(24):
        if vector[i]:
            bits[i // 6] += 1
    return bits.index(max(bits))


def _sextet_signature(vector) -> Tuple[int, int]:
    """Return (dominant_sextet_idx, bit_count_of_dominant)."""
    bits = [0, 0, 0, 0]
    for i in range(24):
        if vector[i]:
            bits[i // 6] += 1
    dom = bits.index(max(bits))
    return (dom, bits[dom])


def resonance_tunnel(vocab, crg, concept: str, max_results: int = 5) -> Dict[str, Any]:
    """Find resonance-tunneled connections for a concept.

    Two concepts 'resonate' if they share the same dominant sextet
    but have Hamming distance > 3 (beyond the normal Golay snap range).
    This discovers non-obvious structural connections.
    """
    vocab_dict = vocab.words if hasattr(vocab, 'words') else vocab
    entry = vocab_dict.get(concept)

    if not entry or not hasattr(entry, 'vector'):
        return {"error": f"Concept '{concept}' not found in vocabulary"}

    vec = list(entry.vector)
    my_sextet, my_count = _sextet_signature(vec)
    sextet_names = ["Reality", "Information", "Activation", "Potential"]

    resonances = []
    for word, other in vocab_dict.items():
        if word == concept or not hasattr(other, 'vector'):
            continue
        other_vec = list(other.vector)
        other_sextet, other_count = _sextet_signature(other_vec)

        if other_sextet != my_sextet:
            continue

        # Compute Hamming distance
        hd = sum(a != b for a, b in zip(vec, other_vec))

        # Only report if beyond normal Golay snap range (d > 3)
        if hd > 3:
            # Resonance strength: higher when Hamming distance is moderate
            # (too far = weak resonance, too close = normal snap)
            strength = max(0, 1.0 - (hd - 3) / 21.0)
            resonances.append({
                "word": word,
                "hamming_distance": hd,
                "shared_sextet": sextet_names[my_sextet],
                "resonance_strength": round(strength, 4),
                "nrci": round(float(other.nrci), 4) if hasattr(other, 'nrci') else None,
            })

    resonances.sort(key=lambda x: -x["resonance_strength"])
    return {
        "concept": concept,
        "dominant_sextet": sextet_names[my_sextet],
        "sextet_bit_count": my_count,
        "resonance_candidates": resonances[:max_results],
        "total_resonances": len(resonances),
        "interpretation": (f"{concept} resonates with {len(resonances)} concepts "
                          f"in the {sextet_names[my_sextet]} sextet beyond Hamming-3 range")
    }


# ═══════════════════════════════════════════════════════════════════════════
# §16  REFINED NRCI — Multi-Shell with Y₀ Constant
# ═══════════════════════════════════════════════════════════════════════════
# The UBP defines Y₀ = 1/(π + 2/π) ≈ 0.264675 as the fundamental
# coupling constant. The Refined NRCI uses multi-shell analysis:
#   Shell 1 (sextet level): per-sextet Hamming weights
#   Shell 2 (sextet pairs): cross-sextet interactions
#   Shell 3 (full vector): total Hamming weight and symmetry tax

_Y0 = 1.0 / (math.pi + 2.0 / math.pi)  # ≈ 0.264675
_OBSERVER_CONSTANT = math.pi + 2.0 / math.pi  # ≈ 3.7771


def refined_nrci(vector, leech_engine=None) -> Dict[str, Any]:
    """Compute Refined NRCI with multi-shell analysis and Y₀ constant.

    Shell 1: Per-sextet Hamming weights ( Reality | Information | Activation | Potential )
    Shell 2: Cross-sextet symmetry deviations
    Shell 3: Full-vector NRCI with Y₀ coupling

    Parameters
    ----------
    vector : list[int]
        24-bit concept vector
    leech_engine : optional
        LEECH_ENGINE for computing the exact NRCI (falls back to approximation)

    Returns
    -------
    dict with per-shell metrics and overall refined NRCI
    """
    sextet_labels = ["Reality", "Information", "Activation", "Potential"]
    shells = []
    for i in range(4):
        sw = sum(vector[i*6:(i+1)*6])
        shells.append(sw)

    # Shell 1: Individual sextet weights
    shell1 = dict(zip(sextet_labels, shells))

    # Shell 2: Cross-sextet symmetry
    # Perfect balance would be all sextets equal. Deviation measures imbalance.
    mean_weight = sum(shells) / 4.0
    imbalance = sum(abs(s - mean_weight) for s in shells) / 4.0
    max_sextet = max(shells)
    min_sextet = min(shells)
    range_sextet = max_sextet - min_sextet

    shell2 = {
        "mean_weight": round(mean_weight, 3),
        "imbalance": round(imbalance, 3),
        "range": range_sextet,
        "dominant": sextet_labels[shells.index(max_sextet)],
        "weakest": sextet_labels[shells.index(min_sextet)],
    }

    # Shell 3: Full-vector NRCI
    hw = sum(vector)
    if leech_engine:
        try:
            exact_nrci = float(leech_engine.calculate_nrci(vector))
            exact_tax = float(leech_engine.calculate_symmetry_tax(vector))
        except Exception:
            exact_nrci = None
            exact_tax = None
    else:
        exact_nrci = None
        exact_tax = None

    # Approximate NRCI using Y₀ (the UBP constant)
    # NRCI ≈ 10 / (10 + Y₀ × hw + hw²/64)
    if exact_nrci is None:
        approx_nrci = 10.0 / (10.0 + _Y0 * hw + hw * hw / 64.0)
        approx_tax = _Y0 * hw + hw * hw / 64.0
    else:
        approx_nrci = exact_nrci
        approx_tax = exact_tax

    shell3 = {
        "hamming_weight": hw,
        "nrci": round(approx_nrci, 6),
        "tax": round(approx_tax, 6) if approx_tax else None,
        "y0_constant": round(_Y0, 6),
        "observer_constant": round(_OBSERVER_CONSTANT, 4),
        "nrci_source": "exact (Leech)" if exact_nrci is not None else "approximate (Y₀)",
    }

    # Overall verdict
    if approx_nrci >= 0.7:
        coherence = "consciousness"
    elif approx_nrci >= 0.5:
        coherence = "subliminal"
    elif approx_nrci >= 0.3:
        coherence = "noise"
    else:
        coherence = "chaos"

    return {
        "shell1_sextets": shell1,
        "shell2_symmetry": shell2,
        "shell3_nrci": shell3,
        "overall_coherence": coherence,
        "refined_nrci": round(approx_nrci, 6),
    }


# ═══════════════════════════════════════════════════════════════════════════
# §17  COSINE SIMILARITY — Angular Similarity Between 24-Bit Vectors
# ═══════════════════════════════════════════════════════════════════════════
# While Hamming distance measures bit-wise disagreement, cosine similarity
# measures angular proximity in the vector space. Two vectors can have
# the same Hamming weight but very different cosine similarities if
# their "on" bits are in different positions.

def cosine_similarity_24(vec1, vec2) -> float:
    """Compute cosine similarity between two 24-bit binary vectors.

    cos(θ) = (v₁ · v₂) / (‖v₁‖ × ‖v₂‖)

    For binary vectors, the dot product is the count of positions
    where both bits are 1 (intersection).
    """
    dot = sum(a & b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(vec1))
    norm2 = math.sqrt(sum(vec2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot / (norm1 * norm2)


def angular_distance(vec1, vec2) -> float:
    """Angular distance in degrees between two 24-bit vectors."""
    cos_sim = cosine_similarity_24(vec1, vec2)
    cos_sim = max(-1.0, min(1.0, cos_sim))  # clamp for numerical safety
    return math.degrees(math.acos(cos_sim))


def vector_similarity_report(vocab, concept1: str, concept2: str) -> Dict[str, Any]:
    """Full similarity report between two concepts.

    Includes Hamming distance, cosine similarity, angular distance,
    and Jaccard coefficient.
    """
    vocab_dict = vocab.words if hasattr(vocab, 'words') else vocab
    e1 = vocab_dict.get(concept1)
    e2 = vocab_dict.get(concept2)

    if not e1 or not hasattr(e1, 'vector'):
        return {"error": f"Concept '{concept1}' not found"}
    if not e2 or not hasattr(e2, 'vector'):
        return {"error": f"Concept '{concept2}' not found"}

    v1, v2 = list(e1.vector), list(e2.vector)

    # Hamming
    hamming = sum(a != b for a, b in zip(v1, v2))

    # Cosine
    cos_sim = cosine_similarity_24(v1, v2)
    ang_dist = angular_distance(v1, v2)

    # Jaccard: |intersection| / |union|
    intersection = sum(a & b for a, b in zip(v1, v2))
    union = sum(a | b for a, b in zip(v1, v2))
    jaccard = intersection / union if union > 0 else 0.0

    # Sextet agreement
    s1 = _dominant_sextet(v1)
    s2 = _dominant_sextet(v2)
    sextet_names = ["Reality", "Information", "Activation", "Potential"]
    same_sextet = s1 == s2

    return {
        "concept1": concept1,
        "concept2": concept2,
        "hamming_distance": hamming,
        "hamming_similarity": round(1.0 - hamming / 24.0, 4),
        "cosine_similarity": round(cos_sim, 4),
        "angular_distance_deg": round(ang_dist, 2),
        "jaccard_coefficient": round(jaccard, 4),
        "concept1_sextet": sextet_names[s1],
        "concept2_sextet": sextet_names[s2],
        "same_dominant_sextet": same_sextet,
        "relationship": (
            "identical" if hamming == 0 else
            "lattice_snap" if hamming <= 3 else
            "resonance" if same_sextet else
            "distant"
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
# §18  SEXTET PARITY — Geometric Domain Alignment
# ═══════════════════════════════════════════════════════════════════════════
# Each geometric domain (Substance, Organism, Algorithm, Mechanism)
# has an expected sextet parity pattern. A concept's dominant sextet
# should match its domain assignment for structural consistency.

# Domain → expected dominant sextet mapping
# (These are heuristic defaults derived from the UBP's ontological layers)
_DOMAIN_SEXTET_MAP = {
    "substance": 0,    # Reality — concrete, physical
    "organism": 1,     # Information — relational, living systems
    "algorithm": 2,    # Activation — processes, computations
    "mechanism": 3,    # Potential — abstract, structural
}

_SEXTET_NAMES = ["Reality", "Information", "Activation", "Potential"]


def sextet_parity_check(vector, assigned_domain: str = None) -> Dict[str, Any]:
    """Check whether a vector's dominant sextet matches its domain.

    Parameters
    ----------
    vector : list[int]
        24-bit concept vector
    assigned_domain : str, optional
        The concept's assigned domain (substance/organism/algorithm/mechanism)

    Returns
    -------
    dict with sextet analysis and alignment verdict
    """
    sextet_weights = [sum(vector[i*6:(i+1)*6]) for i in range(4)]
    dominant = sextet_weights.index(max(sextet_weights))
    dominant_name = _SEXTET_NAMES[dominant]

    # Check parity of each sextet (even/odd bit count)
    parities = [sw % 2 for sw in sextet_weights]

    result = {
        "sextet_weights": sextet_weights,
        "dominant_sextet": dominant,
        "dominant_name": dominant_name,
        "sextet_parities": parities,
        "total_parity": sum(vector) % 2,
    }

    if assigned_domain:
        expected = _DOMAIN_SEXTET_MAP.get(assigned_domain.lower())
        if expected is not None:
            aligned = (dominant == expected)
            result["assigned_domain"] = assigned_domain
            result["expected_sextet"] = _SEXTET_NAMES[expected]
            result["aligned"] = aligned
            result["verdict"] = "ALIGNED" if aligned else "MISALIGNED"
        else:
            result["assigned_domain"] = assigned_domain
            result["verdict"] = "UNKNOWN_DOMAIN"

    return result


def sextet_parity_report(vocab, domain_filter: str = None) -> Dict[str, Any]:
    """Check sextet parity alignment across the entire vocabulary.

    Parameters
    ----------
    vocab : vocabulary dict
    domain_filter : str, optional
        If set, only check concepts in this domain
    """
    vocab_dict = vocab.words if hasattr(vocab, 'words') else vocab
    aligned = 0
    misaligned = 0
    unchecked = 0
    misaligned_list = []

    for word, entry in vocab_dict.items():
        if not hasattr(entry, 'vector'):
            continue

        vec = list(entry.vector)
        domain = getattr(entry, 'domain', None) or getattr(entry, 'mog_category', None)

        if domain_filter and domain != domain_filter:
            continue

        if not domain:
            unchecked += 1
            continue

        check = sextet_parity_check(vec, domain)
        if check.get("aligned"):
            aligned += 1
        elif check.get("verdict") == "MISALIGNED":
            misaligned += 1
            misaligned_list.append({
                "word": word,
                "domain": domain,
                "expected": check.get("expected_sextet"),
                "actual": check.get("dominant_name"),
            })

    total = aligned + misaligned
    return {
        "total_checked": total,
        "aligned": aligned,
        "misaligned": misaligned,
        "unchecked": unchecked,
        "alignment_rate": round(aligned / max(1, total), 3),
        "worst_misaligned": misaligned_list[:10],
        "verdict": "well_aligned" if (aligned / max(1, total)) > 0.8 else "needs_realignment"
    }


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION: Extended GLMTools Class
# ═══════════════════════════════════════════════════════════════════════════

class GLMToolsV2:
    """Extended GLM Tools with coherence and geometry methods.

    Drop-in extension for GLMTools. Adds 8 new tools from the
    Holographic Arithmetic Engine research.
    """

    def __init__(self, vocab, crg, runtime=None):
        self.vocab = vocab
        self.crg = crg
        self.rt = runtime
        self.available = False

        try:
            from GLM01_substrate import GOLAY_ENGINE, LEECH_ENGINE, BLA, vector_to_hex_int, fast_hamming
            self.golay = GOLAY_ENGINE
            self.leech = LEECH_ENGINE
            self.bla = BLA
            self.vector_to_hex_int = vector_to_hex_int
            self.fast_hamming = fast_hamming
            self.available = True
        except Exception:
            pass

        self.tools = {
            "VALUE_GEOMETRY": self.tool_value_geometry,
            "RICCI_CURVATURE": self.tool_ricci_curvature,
            "GHOST_FILTER": self.tool_ghost_filter,
            "TOPOLOGICAL_HEALTH": self.tool_topological_health,
            "RESONANCE_TUNNEL": self.tool_resonance_tunnel,
            "REFINED_NRCI": self.tool_refined_nrci,
            "COSINE_SIMILARITY": self.tool_cosine_similarity,
            "SEXTET_PARITY": self.tool_sextet_parity,
        }

    def select_tools(self, query: str, concept: str = None) -> List[str]:
        """Select tools based on query keywords."""
        q = query.lower()
        selected = []

        if any(w in q for w in ['value geometry', 'prime factor', 'lattice type',
                                  'omega', 'dimensionality', 'platonic', '144',
                                  'self-assembling', 'factorization']):
            selected.append("VALUE_GEOMETRY")

        if any(w in q for w in ['ricci', 'curvature', 'bottleneck', 'structural health',
                                  'bridge', 'graph health']):
            selected.append("RICCI_CURVATURE")

        if any(w in q for w in ['ghost', 'hallucination', 'filter', 'transient',
                                  'lock pressure', 'tenacity']):
            selected.append("GHOST_FILTER")

        if any(w in q for w in ['topological', 'betti', 'connected component',
                                  'cycle', 'topology', 'euler', 'homology']):
            selected.append("TOPOLOGICAL_HEALTH")

        if any(w in q for w in ['resonance', 'tunnel', 'sextet', 'harmonic',
                                  'beyond hamming']):
            selected.append("RESONANCE_TUNNEL")

        if any(w in q for w in ['refined nrci', 'multi-shell', 'y0', 'coupling',
                                  'coherence depth', 'shell']):
            selected.append("REFINED_NRCI")

        if any(w in q for w in ['cosine', 'angular', 'similarity', 'jaccard',
                                  'proximity']):
            selected.append("COSINE_SIMILARITY")

        if any(w in q for w in ['sextet parity', 'domain alignment', 'octad filter',
                                  'geometric domain']):
            selected.append("SEXTET_PARITY")

        # Auto-select for coherence queries
        if concept and not selected:
            selected.append("REFINED_NRCI")
            selected.append("GHOST_FILTER")

        return selected

    def execute(self, tool_name: str, **kwargs):
        from GLM_tools import ToolResult
        if tool_name not in self.tools:
            return ToolResult(tool_name, None, f"Unknown tool: {tool_name}", success=False)
        try:
            return self.tools[tool_name](**kwargs)
        except Exception as e:
            return ToolResult(tool_name, None, f"Error: {e}", success=False)

    # ── Tool Implementations ──────────────────────────────────────────────

    def tool_value_geometry(self, number: int = None, **kw):
        from GLM_tools import ToolResult
        if number is None:
            return ToolResult("VALUE_GEOMETRY", None, "No number provided", success=False)
        result = value_geometry(number)
        return ToolResult("VALUE_GEOMETRY", result,
            f"n={number}: ω={result['omega']} ({result['dim_name']}), "
            f"lattice={result['lattice_type']} ({result['lattice_desc']}), "
            f"144° class={result['modulus_144_class']}°, "
            f"resonates with {result['platonic_resonance']}")

    def tool_ricci_curvature(self, concept: str = None, **kw):
        from GLM_tools import ToolResult
        report = ricci_curvature_report(self.crg)
        return ToolResult("RICCI_CURVATURE", report,
            f"CRG: {report['total_edges']} edges, avg FRC={report['avg_curvature']}, "
            f"{report['bottleneck_count']} bottlenecks, {report['critical_count']} critical bridges, "
            f"health={report['graph_health']}")

    def tool_ghost_filter(self, **kw):
        from GLM_tools import ToolResult
        result = ghost_filter(self.crg, self.vocab)
        return ToolResult("GHOST_FILTER", result,
            f"{result['ghost_count']} ghosts / {result['total_high_nrci']} high-NRCI "
            f"(ghost rate={result['ghost_rate']}), verdict={result['verdict']}")

    def tool_topological_health(self, **kw):
        from GLM_tools import ToolResult
        result = topological_health(self.crg)
        return ToolResult("TOPOLOGICAL_HEALTH", result,
            f"β₀={result['beta_0']} components, β₁={result['beta_1']} cycles, "
            f"{result['nodes']} nodes, {result['edges']} edges, health={result['health']}")

    def tool_resonance_tunnel(self, concept: str = None, **kw):
        from GLM_tools import ToolResult
        if not concept:
            return ToolResult("RESONANCE_TUNNEL", None, "No concept", success=False)
        result = resonance_tunnel(self.vocab, self.crg, concept)
        if "error" in result:
            return ToolResult("RESONANCE_TUNNEL", None, result["error"], success=False)
        return ToolResult("RESONANCE_TUNNEL", result,
            f"{concept}: {result['total_resonances']} resonances in "
            f"{result['dominant_sextet']} sextet")

    def tool_refined_nrci(self, concept: str = None, **kw):
        from GLM_tools import ToolResult
        if concept:
            entry = (self.vocab.words if hasattr(self.vocab, 'words') else self.vocab).get(concept)
            if entry and hasattr(entry, 'vector'):
                vec = list(entry.vector)
            else:
                return ToolResult("REFINED_NRCI", None, f"Concept '{concept}' not found", success=False)
        else:
            return ToolResult("REFINED_NRCI", None, "No concept", success=False)

        leech = self.leech if self.available else None
        result = refined_nrci(vec, leech)
        return ToolResult("REFINED_NRCI", result,
            f"{concept}: NRCI={result['refined_nrci']} ({result['overall_coherence']}), "
            f"sextets={result['shell1_sextets']}, imbalance={result['shell2_symmetry']['imbalance']}")

    def tool_cosine_similarity(self, concept1: str = None, concept2: str = None, **kw):
        from GLM_tools import ToolResult
        if not concept1 or not concept2:
            return ToolResult("COSINE_SIMILARITY", None, "Need two concepts", success=False)
        result = vector_similarity_report(self.vocab, concept1, concept2)
        if "error" in result:
            return ToolResult("COSINE_SIMILARITY", None, result["error"], success=False)
        return ToolResult("COSINE_SIMILARITY", result,
            f"{concept1} ↔ {concept2}: cos={result['cosine_similarity']}, "
            f"hamming={result['hamming_distance']}, angular={result['angular_distance_deg']}°, "
            f"Jaccard={result['jaccard_coefficient']}, relationship={result['relationship']}")

    def tool_sextant_parity(self, concept: str = None, **kw):
        from GLM_tools import ToolResult
        if concept:
            entry = (self.vocab.words if hasattr(self.vocab, 'words') else self.vocab).get(concept)
            if entry and hasattr(entry, 'vector'):
                vec = list(entry.vector)
                domain = getattr(entry, 'domain', None) or getattr(entry, 'mog_category', None)
                result = sextet_parity_check(vec, domain)
                return ToolResult("SEXTET_PARITY", result,
                    f"{concept}: dominant={result['dominant_name']}, "
                    f"weights={result['sextet_weights']}, verdict={result.get('verdict', 'N/A')}")
        # Full report
        result = sextet_parity_report(self.vocab)
        return ToolResult("SEXTET_PARITY", result,
            f"{result['aligned']}/{result['total_checked']} aligned "
            f"({result['alignment_rate']}), verdict={result['verdict']}")


if __name__ == "__main__":
    # Quick standalone tests
    print("=== GLM Tools v2 — Coherence & Geometry Expansion ===")
    print()

    # Test VALUE_GEOMETRY
    for n in [7, 13, 42, 144, 60, 210]:
        vg = value_geometry(n)
        print(f"  {n:4d}: ω={vg['omega']}, dim={vg['dim_name']:12s}, "
              f"lattice={vg['lattice_type']:10s} ({vg['lattice_mod']}), "
              f"144°={vg['modulus_144_class']:3d}°, platonic={vg['platonic_resonance']}")

    print()

    # Test REFINED_NRCI with a sample vector
    test_vec = [1,0,1,0,1,0, 0,1,0,1,0,1, 1,0,1,0,1,0, 0,1,0,1,0,1]
    rn = refined_nrci(test_vec)
    print(f"  Refined NRCI test vector: {rn['refined_nrci']} ({rn['overall_coherence']})")
    print(f"    Shell 1 (sextets): {rn['shell1_sextets']}")
    print(f"    Shell 2 (symmetry): imbalance={rn['shell2_symmetry']['imbalance']}")
    print(f"    Shell 3 (NRCI): {rn['shell3_nrci']}")
    print(f"    Y₀ = {rn['shell3_nrci']['y0_constant']}")