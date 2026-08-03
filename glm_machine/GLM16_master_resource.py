# ==============================================================================
# §16  MASTER RESOURCE LOADER (v3.9.0 NEW MODULE)
# ==============================================================================
# Loads the glm_master_resource_v1.json (~14.4 MB) — a curated 4248-word
# dictionary with deterministic 24-bit vectors, NRCI scores, hex_ints, and
# full English definitions.  Also loads 70 element/law `relates_to` edges
# and 55 spatial_nodes with hex colour signatures for visualization.
#
# In v3.8.0 this resource was sitting on disk but unused.  v3.9.0 integrates
# it to:
#   1. Inject 3900+ general-English words (with definitions) into the vocab.
#      Words already present (KB-derived or physics-pack) take precedence —
#      we never overwrite a grounded entry with a dictionary entry.
#   2. Add the 70 element↔law `relates_to` edges to the CRG so queries like
#      "how does hydrogen relate to helium?" find a path.
#   3. Expose spatial_nodes (3D positions + hex colours) for the Pyodide UI
#      to render as a concept constellation.
#   4. Surface full English definitions in the response composer for any
#      word that has one — replacing the 90-char truncated KB descriptions.
#
# Design rules:
#   * Lazy loading — the resource is only parsed once, on first use.
#   * Cached — subsequent calls return the parsed object.
#   * Non-fatal — if the file is missing or corrupt, the system continues
#     with the v3.8.0 baseline vocab.
#   * Pure stdlib (json, hashlib, pathlib).
# ==============================================================================
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set

from GLM00_config import UBP_CORE_PATH
from GLM01_substrate import (
    WordEntry, BLA, GOLAY_ENGINE, LEECH_ENGINE, _get_mog_category
)

# ── 1. RESOURCE PATH ──────────────────────────────────────────────────────────

_MASTER_PATH = UBP_CORE_PATH / "glm_master_resource_v1.json"

_master_cache: Optional[dict] = None


def _load_master() -> dict:
    """Lazy-load and cache the master resource.  Returns empty dict on failure."""
    global _master_cache
    if _master_cache is not None:
        return _master_cache
    try:
        with open(_MASTER_PATH, 'r') as f:
            _master_cache = json.load(f)
    except Exception:
        _master_cache = {}
    return _master_cache


def master_resource_status() -> dict:
    """Report whether the master resource is loaded and its size."""
    mr = _load_master()
    if not mr:
        return {"loaded": False, "path": str(_MASTER_PATH),
                "exists": _MASTER_PATH.exists()}
    return {
        "loaded": True,
        "path": str(_MASTER_PATH),
        "exists": _MASTER_PATH.exists(),
        "version": mr.get("metadata", {}).get("version", "?"),
        "total_words": len(mr.get("vocabulary", {})),
        "total_relations": len(mr.get("relations", [])),
        "total_spatial_nodes": len(mr.get("spatial_nodes", {})),
        "phrase_locks": len(mr.get("phrase_locks", [])),
    }


# ── 2. VOCABULARY INJECTION ───────────────────────────────────────────────────

# Words we never import from the dictionary (already covered by KB or physics
# pack, or too generic to be useful as concept vectors).
_SKIP_WORDS: Set[str] = set()


def inject_master_vocab(words: dict, max_words: int = 4000) -> dict:
    """Inject dictionary entries from the master resource into a live vocab.

    Skips any term already present (KB-derived entries take precedence).
    Skips multi-word phrases (handled by phrase_locks + physics pack).
    Skips very short words (< 3 chars) and pure-number entries.

    Returns a report dict for diagnostics.
    """
    report = {"injected": 0, "skipped_existing": 0, "skipped_multiword": 0,
              "skipped_short": 0, "errors": 0}
    mr = _load_master()
    if not mr:
        return report

    mv = mr.get("vocabulary", {})
    for word, entry in mv.items():
        if report["injected"] >= max_words:
            break
        try:
            # Skip multi-word phrases (handled elsewhere)
            if ' ' in word or '-' in word:
                report["skipped_multiword"] += 1
                continue
            # Skip very short words
            if len(word) < 3:
                report["skipped_short"] += 1
                continue
            # Skip if already in vocab (KB or physics pack takes precedence)
            if word in words:
                report["skipped_existing"] += 1
                continue
            # Skip if in the explicit skip list
            if word in _SKIP_WORDS:
                report["skipped_short"] += 1
                continue

            vec = entry.get("vector")
            if not vec or len(vec) != 24:
                report["errors"] += 1
                continue

            nrci = float(entry.get("nrci", 0.5))
            definition = entry.get("definition", "")
            hex_int = entry.get("hex_int", 0)

            we = WordEntry(
                word=word, vector=list(vec), role="NOUN",
                ubp_id=f"MR_{word}",
                nrci=nrci,
                golay_codeword=list(vec),
                fold3=BLA.fold24_to3(vec),
                mog_category=_get_mog_category(vec),
            )
            # Attach the dictionary definition + hex_int as dynamic attrs
            we.definition = definition  # type: ignore[attr-defined]
            we.hex_int = hex_int  # type: ignore[attr-defined]
            we.source = "master_resource"  # type: ignore[attr-defined]
            words[word] = we
            report["injected"] += 1
        except Exception:
            report["errors"] += 1
            continue

    return report


# ── 3. RELATION INJECTION ─────────────────────────────────────────────────────

def inject_master_relations(crg) -> dict:
    """Add the 70 element↔law `relates_to` edges from the master resource
    into the live CRG.  The edges use ubp_id-style node names (e.g.
    'elem_h_001', 'law_aqueous_geometry') which we resolve to vocab words
    where possible; otherwise we add the edge with the ubp_id as the node
    name (it will still be traversable but won't match a vocab lookup).
    """
    report = {"added": 0, "skipped": 0, "errors": 0}
    mr = _load_master()
    if not mr:
        return report

    relations = mr.get("relations", [])
    for rel in relations:
        try:
            if not isinstance(rel, list) or len(rel) != 3:
                report["errors"] += 1
                continue
            src, label, dst = rel
            # Normalise label to a CRG-compatible type
            if label not in ("relates_to", "is_a", "depends_on", "commutes_with",
                              "scales_as", "is_dual_to", "generates", "measures",
                              "has_property", "auto_proposed"):
                label = "auto_proposed"
            # Try to add the edge.  The CRG's add_edge is tolerant of unknown
            # nodes — it just stores them.
            if crg.add_edge(src, label, dst):
                report["added"] += 1
            else:
                report["skipped"] += 1
        except Exception:
            report["errors"] += 1
            continue

    return report


# ── 4. SPATIAL NODES + HEX COLOURS ────────────────────────────────────────────

def get_spatial_nodes() -> dict:
    """Return the 55 spatial_nodes from the master resource.

    Each node has:
      * pos: [x, y, z] 3D position for visualization
      * color: hex colour string (e.g. '#9932cc') derived from the 24-bit vector
      * role: a human-readable role label
    """
    mr = _load_master()
    return mr.get("spatial_nodes", {}) if mr else {}


def get_phrase_locks() -> list:
    """Return the 30 multi-word phrase locks from the master resource.

    These are the canonical multi-word physics terms that should be treated
    as atomic tokens by the lexer.  In v3.8.0 we already added these via
    the physics pack; this exposes them for the lexer to consume directly.
    """
    mr = _load_master()
    return mr.get("phrase_locks", []) if mr else []


# ── 5. DEFINITION LOOKUP ──────────────────────────────────────────────────────

def lookup_definition(word: str) -> Optional[str]:
    """Look up a word's full English definition in the master resource.

    Returns None if the word is not in the master resource or if the
    resource is not loaded.
    """
    mr = _load_master()
    if not mr:
        return None
    entry = mr.get("vocabulary", {}).get(word.lower())
    if not entry:
        return None
    return entry.get("definition")


def lookup_hex_colour(word: str) -> Optional[str]:
    """Look up a word's hex colour signature (e.g. '#b4d9f7').

    Computed from the 24-bit vector: each of the 4 sextets maps to a
    pair of hex digits in the #RRGGBB colour string.
    """
    mr = _load_master()
    if not mr:
        return None
    entry = mr.get("vocabulary", {}).get(word.lower())
    if not entry:
        return None
    hex_int = entry.get("hex_int", 0)
    # Convert to #RRGGBB (take the low 24 bits)
    return f"#{hex_int & 0xFFFFFF:06x}"


# ── 6. ISOLATION TEST ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Testing Module 16: Master Resource Loader (v3.9.0) ===")
    status = master_resource_status()
    print(f"Status: {json.dumps(status, indent=2)}")
    print()

    if status.get("loaded"):
        # Test definition lookup
        for w in ["energy", "time", "oxygen", "lattice"]:
            d = lookup_definition(w)
            c = lookup_hex_colour(w)
            if d:
                print(f"  {w}: colour={c}, def='{d[:80]}...'")
            else:
                print(f"  {w}: (no definition)")
        print()

        # Test phrase_locks
        locks = get_phrase_locks()
        print(f"Phrase locks ({len(locks)}): {locks[:8]}")
        print()

        # Test spatial_nodes
        nodes = get_spatial_nodes()
        print(f"Spatial nodes: {len(nodes)}")
        for k in list(nodes.keys())[:3]:
            print(f"  {k}: {nodes[k]}")
        print()

        # Test injection (into a fresh dict)
        from GLM01_substrate import _build_vocabulary
        vocab = _build_vocabulary()
        before = len(vocab)
        report = inject_master_vocab(vocab)
        after = len(vocab)
        print(f"Vocab injection: {before} -> {after} (+{after - before})")
        print(f"  report: {report}")
