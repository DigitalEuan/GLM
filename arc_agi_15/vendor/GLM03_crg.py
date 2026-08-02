# ══════════════════════════════════════════════════════════════════════════════
# §03  CRG EXTENDED  — contradiction edges + auto-expansion (v3.7.6 Hardened)
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import re
from collections import defaultdict
from typing import List, Tuple, Dict, Set, Any, Optional

# Import from previous hardened modules
from GLM01_substrate import (
    ConceptRelationGraph, CRGEdge, EDGE_LABELS, build_default_crg,
    BLA, vector_to_hex_int, fast_hamming, get_domain, _get_mog_category,
    _query_type
)
from GLM02_constants import (
    AUTO_EXPAND_RADIUS, AUTO_EXPAND_CONF, LATTICE_LINK_RADIUS
)

# ── 1. CONTRADICTION DEFINITIONS ───────────────────────────────────────
EDGE_LABELS.add("contradicts")
EDGE_LABELS.add("incompatible_with")
EDGE_LABELS.add("auto_proposed")

_SYMMETRIC = {"commutes_with", "is_dual_to", "contradicts", "incompatible_with"}

_CONTRADICTIONS: List[Tuple[str, str, str]] = [
    ("boson",            "contradicts",       "fermion"),
    ("commutator",       "contradicts",       "anticommutator"),
    ("continuum",        "incompatible_with", "lattice"),
    ("classical",        "incompatible_with", "quantum"),
    ("majorana",         "incompatible_with", "dirac"),
    ("unitary",          "contradicts",       "antiunitary"),
    ("real",             "incompatible_with", "imaginary"),
    ("local",            "incompatible_with", "nonlocal"),
]

# ── 2. CRG BUILDING LOGIC ──────────────────────────────────────────────
def build_extended_crg() -> ConceptRelationGraph:
    """Build the default CRG and add curated contradiction edges."""
    crg = build_default_crg()
    for src, label, dst in _CONTRADICTIONS:
        crg.add_edge(src, label, dst)
        if label in _SYMMETRIC and src != dst:
            crg.add_edge(dst, label, src)
    return crg

def detect_contradictions(backbone: List[CRGEdge],
                          crg: ConceptRelationGraph) -> List[Tuple[CRGEdge, CRGEdge]]:
    """Find (edge, contradicting_edge) pairs in a backbone."""
    contradictions = []
    seen = set()
    for e in backbone:
        # Check outgoing contradictions
        for ce in crg.out.get(e.src, []):
            if ce.label in ("contradicts", "incompatible_with") and ce.dst == e.dst:
                key = tuple(sorted([e.src, e.dst])) + (ce.label,)
                if key not in seen:
                    contradictions.append((e, ce)); seen.add(key)
    return contradictions

def contradiction_penalty(backbone: List[CRGEdge],
                          crg: ConceptRelationGraph) -> float:
    """Penalty [0, 0.5] applied to coherence when contradictions exist."""
    cons = detect_contradictions(backbone, crg)
    return min(0.5, len(cons) * 0.15)

# ── 3. AUTO-EXPANSION (Optimized to prevent hangs) ─────────────────────
def auto_expand_crg(crg: ConceptRelationGraph, vocab_words: Dict[str, Any], max_proposals: int = 20) -> List[Tuple[str, str, str]]:
    """Propose new CRG edges from lattice adjacency using Hex-Caching."""
    nouns = {w for w, e in vocab_words.items() if e.role == "NOUN"}
    proposed = []

    # v3.7.4 Fix: Pre-calculate hex ints for ALL nouns ONCE to avoid O(N^2) packing
    hex_cache: Dict[str, int] = {}
    for n in nouns:
        entry = vocab_words.get(n)
        if entry and hasattr(entry, 'vector') and entry.vector:
            try:
                hex_cache[n] = vector_to_hex_int(entry.vector)
            except Exception: pass

    # Build a neighbor index from existing edges
    neighbours: Dict[str, Set[str]] = defaultdict(set)
    for e in crg.edges:
        if e.label not in ("contradicts", "incompatible_with", "auto_proposed"):
            neighbours[e.src].add(e.dst)
            if e.label in _SYMMETRIC:
                neighbours[e.dst].add(e.src)

    # Snapshot to prevent 'dict size changed' errors
    neighbour_snapshot = {k: set(v) for k, v in neighbours.items()}

    import itertools
    candidates = []
    seen_pairs = set()

    for shared_node, connected_nodes in neighbour_snapshot.items():
        valid_nodes = [n for n in connected_nodes if n in hex_cache]
        if len(valid_nodes) < 2: continue

        for a, b in itertools.combinations(valid_nodes, 2):
            pair = tuple(sorted([a, b]))
            if pair in seen_pairs: continue
            seen_pairs.add(pair)

            # Fast Hamming via Cache
            d = fast_hamming(hex_cache[a], hex_cache[b])
            if d <= AUTO_EXPAND_RADIUS:
                candidates.append((d, a, b))

    candidates.sort(key=lambda x: x[0])
    for d, a, b in candidates[:max_proposals]:
        crg.add_edge(a, "auto_proposed", b)
        proposed.append((a, b, f"dist: {d}"))
    
    return proposed

# ── 4. LATTICE AUTO-LINKING ────────────────────────────────────────────
def lattice_auto_link(crg: ConceptRelationGraph, vocab_words: Dict[str, Any],
                      hamming_threshold: int = LATTICE_LINK_RADIUS,
                      max_per_zone: int = 50) -> int:
    """Aggressively link NOUNs that are lattice-adjacent."""
    zones: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
    for name, entry in vocab_words.items():
        if entry.role == "NOUN" and hasattr(entry, 'vector') and entry.vector:
            try:
                z = _get_mog_category(entry.vector)
                zones[z].append((name, vector_to_hex_int(entry.vector)))
            except Exception: continue

    links_added = 0
    for zone_name, words in zones.items():
        if len(words) < 2: continue
        zone_links = 0
        for i in range(len(words)):
            if zone_links >= max_per_zone: break
            name1, hex1 = words[i]
            for j in range(i + 1, len(words)):
                if zone_links >= max_per_zone: break
                name2, hex2 = words[j]
                
                d = fast_hamming(hex1, hex2)
                if 0 < d <= hamming_threshold:
                    # Check if already linked
                    existing = {e.dst for e in crg.out.get(name1, [])}
                    if name2 not in existing:
                        label = f"lattice_adjacent_{hamming_threshold + 1 - d}"
                        crg.add_edge(name1, label, name2)
                        crg.add_edge(name2, label, name1)
                        links_added += 1
                        zone_links += 1
    return links_added

# ── 5. ENHANCED QUERY DETECTION ────────────────────────────────────────
_COMPUTE_RE = re.compile(r'\b(find|compute|calculate|evaluate|determine|solve|simplify|differentiate|integrate)\b')
_PROOF_RE = re.compile(r'\b(prove|proof|show that|verify that|demonstrate)\b')

def _enhanced_query_type(query: str) -> str:
    """Wrap _query_type with computation/proof detection."""
    q = query.lower()
    if _PROOF_RE.search(q): return "proof"
    if _COMPUTE_RE.search(q): return "computation"
    return _query_type(query)

# ── 6. ISOLATION TEST ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Testing Module 03: CRG Extended ===")
    from GLM01_substrate import _build_vocabulary
    try:
        vocab = _build_vocabulary()
        crg = build_extended_crg()
        print(f"✅ Base CRG: {len(crg.edges)} edges.")
        
        expanded = auto_expand_crg(crg, vocab, max_proposals=5)
        print(f"✅ Auto-Expansion: Added {len(expanded)} edges.")
        
        lat_links = lattice_auto_link(crg, vocab)
        print(f"✅ Lattice Linking: Added {lat_links} edges.")
    except Exception as e:
        print(f"❌ Failed: {e}")