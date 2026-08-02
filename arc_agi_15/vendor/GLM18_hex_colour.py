# ==============================================================================
# §18  HEX COLOUR SIGNATURES (v3.9.0 NEW MODULE)
# ==============================================================================
# The 24-bit vector of every concept IS a hex colour (#RRGGBB).  This module
# exposes that fact for visualization, idea-blending, and colour-signature
# comparison.
#
# Capabilities:
#   * word_to_colour(word)   -> "#RRGGBB"
#   * vector_to_colour(vec)  -> "#RRGGBB"
#   * blend_colours(vectors) -> "#RRGGBB"  (mix of multiple concept colours)
#   * colour_distance(c1, c2) -> int  (Euclidean RGB distance)
#   * idea_signature(zone)   -> {colour, secondary, gradient} for the UI
#   * render_palette(words)  -> [{word, colour, nrci}, ...] for a concept map
#
# The Pyodide UI can use this to render:
#   - A concept constellation where each concept is a coloured dot
#   - An idea "aura" that shifts colour as the zone evolves
#   - A similarity heatmap between the query and the vocab
#
# Design rules:
#   * Pure stdlib.
#   * No external dependencies.
#   * Deterministic.
# ==============================================================================
from __future__ import annotations
import hashlib
from typing import List, Dict, Tuple, Optional, Any

from GLM01_substrate import (
    BLA, LEECH_ENGINE, vector_to_hex_int, _get_mog_category
)


# ── 1. CORE COLOUR FUNCTIONS ──────────────────────────────────────────────────

def vector_to_colour(vec: List[int]) -> str:
    """Convert a 24-bit vector to a #RRGGBB hex colour string.

    The 24 bits map directly to the R, G, B channels (8 bits each).
    This is the foundational UBP insight: every concept IS a colour.
    """
    if not vec or len(vec) != 24:
        return "#000000"
    # R = bits 0-7, G = bits 8-15, B = bits 16-23
    r = 0
    for i in range(8):
        if vec[i]:
            r |= (1 << (7 - i))
    g = 0
    for i in range(8):
        if vec[8 + i]:
            g |= (1 << (7 - i))
    b = 0
    for i in range(8):
        if vec[16 + i]:
            b |= (1 << (7 - i))
    return f"#{r:02x}{g:02x}{b:02x}"


def word_to_colour(word: str, vocab: Any) -> Optional[str]:
    """Look up a word in the vocab and return its hex colour.

    Returns None if the word is not in the vocabulary.
    """
    target = vocab.words if hasattr(vocab, 'words') else vocab
    entry = target.get(word)
    if not entry or not getattr(entry, 'vector', None):
        return None
    return vector_to_colour(entry.vector)


def colour_distance(c1: str, c2: str) -> int:
    """Euclidean RGB distance between two #RRGGBB colours.

    Range: 0 (identical) to ~195075 (black vs white = 255²·3).
    Useful for ranking concept-similarity by colour proximity.
    """
    if not c1.startswith("#") or not c2.startswith("#") or len(c1) != 7 or len(c2) != 7:
        return 0
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    return (r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2


# ── 2. COLOUR BLENDING (for idea auras) ───────────────────────────────────────

def blend_colours(vectors: List[List[int]], weights: Optional[List[float]] = None) -> str:
    """Blend multiple concept vectors into a single colour.

    Each of R, G, B is the weighted average of the corresponding channel
    across all input vectors.  Useful for rendering a zone's "idea aura"
    that shifts as evidence accumulates.
    """
    if not vectors:
        return "#000000"
    if weights is None:
        weights = [1.0] * len(vectors)
    if len(weights) != len(vectors):
        weights = [1.0] * len(vectors)
    total_w = sum(weights) or 1.0

    r = g = b = 0.0
    for vec, w in zip(vectors, weights):
        if not vec or len(vec) != 24:
            continue
        # Extract R, G, B as 0-255 values
        vr = sum((1 << (7 - i)) for i in range(8) if vec[i])
        vg = sum((1 << (7 - i)) for i in range(8) if vec[8 + i])
        vb = sum((1 << (7 - i)) for i in range(8) if vec[16 + i])
        r += vr * w
        g += vg * w
        b += vb * w
    r = int(round(r / total_w))
    g = int(round(g / total_w))
    b = int(round(b / total_w))
    return f"#{r:02x}{g:02x}{b:02x}"


# ── 3. IDEA SIGNATURE (zone colour profile) ───────────────────────────────────

def idea_signature(zone: Any) -> Dict[str, Any]:
    """Compute a colour signature for an IdeaZone.

    Returns:
      * primary:    colour of the zone centroid
      * secondary:  colour of the most recent evidence
      * blend:      colour of all evidence blended together
      * nrci:       the zone's NRCI score (coherence)
      * mog:        the dominant MOG category
      * evidence_count: how many evidence vectors contributed
    """
    if not zone or not getattr(zone, 'evidence', None):
        return {"primary": "#000000", "secondary": "#000000",
                "blend": "#000000", "nrci": 0.0, "mog": "I_Topology",
                "evidence_count": 0}

    centroid = getattr(zone, 'centroid', [])
    evidence = zone.evidence
    vecs = [e.vector for e in evidence if hasattr(e, 'vector') and e.vector]

    primary = vector_to_colour(centroid) if centroid else "#000000"
    secondary = vector_to_colour(vecs[-1]) if vecs else "#000000"
    blend = blend_colours(vecs) if vecs else "#000000"

    try:
        nrci = float(LEECH_ENGINE.calculate_nrci(centroid)) if centroid else 0.0
    except Exception:
        nrci = 0.0
    mog = _get_mog_category(centroid) if centroid else "I_Topology"

    return {
        "primary": primary,
        "secondary": secondary,
        "blend": blend,
        "nrci": nrci,
        "mog": mog,
        "evidence_count": len(vecs),
    }


# ── 4. PALETTE RENDERING (for concept maps) ───────────────────────────────────

def render_palette(words: List[str], vocab: Any, max_words: int = 50) -> List[Dict[str, Any]]:
    """Render a list of words as a palette of {word, colour, nrci} dicts.

    Useful for the Pyodide UI to draw a concept map where each word is a
    coloured chip.  Words without vocab entries are skipped.
    """
    target = vocab.words if hasattr(vocab, 'words') else vocab
    out: List[Dict[str, Any]] = []
    for w in words[:max_words]:
        entry = target.get(w)
        if not entry or not getattr(entry, 'vector', None):
            continue
        out.append({
            "word": w,
            "colour": vector_to_colour(entry.vector),
            "nrci": float(getattr(entry, 'nrci', 0.5)),
            "mog": getattr(entry, 'mog_category', 'I_Topology'),
        })
    return out


def rank_by_colour_proximity(query_word: str, vocab: Any,
                              top_n: int = 10) -> List[Dict[str, Any]]:
    """Rank all vocab words by colour proximity to `query_word`.

    Returns a list of {word, colour, distance} dicts, sorted by ascending
    distance (closest colours first).  Useful for "show me concepts with
    similar colour signatures" exploration.
    """
    target = vocab.words if hasattr(vocab, 'words') else vocab
    q_entry = target.get(query_word)
    if not q_entry or not getattr(q_entry, 'vector', None):
        return []
    q_colour = vector_to_colour(q_entry.vector)

    candidates: List[Dict[str, Any]] = []
    for w, entry in target.items():
        if w == query_word:
            continue
        if not getattr(entry, 'vector', None):
            continue
        c = vector_to_colour(entry.vector)
        d = colour_distance(q_colour, c)
        candidates.append({"word": w, "colour": c, "distance": d})

    candidates.sort(key=lambda x: x["distance"])
    return candidates[:top_n]


# ── 5. ISOLATION TEST ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Testing Module 18: Hex Colour Signatures (v3.9.0) ===")
    print()

    # Test vector_to_colour
    test_vecs = [
        ([1] * 24, "all-ones (white)"),
        ([0] * 24, "all-zeros (black)"),
        ([1, 0] * 12, "alternating (magenta-ish)"),
        ([1, 1, 1, 1, 1, 1, 1, 1] + [0] * 16, "red only"),
        ([0] * 8 + [1] * 8 + [0] * 8, "green only"),
        ([0] * 16 + [1] * 8, "blue only"),
    ]
    print("Vector → colour:")
    for vec, name in test_vecs:
        print(f"  {name:30s} -> {vector_to_colour(vec)}")
    print()

    # Test colour_distance
    print("Colour distances:")
    print(f"  black↔white:    {colour_distance('#000000', '#ffffff')}")
    print(f"  red↔blue:       {colour_distance('#ff0000', '#0000ff')}")
    print(f"  red↔darkred:    {colour_distance('#ff0000', '#8b0000')}")
    print()

    # Test blend_colours
    print("Blend red + blue (equal weights):")
    red = [1] * 8 + [0] * 16
    blue = [0] * 16 + [1] * 8
    print(f"  -> {blend_colours([red, blue])}")
    print()

    # Test with the real vocab
    from GLM01_substrate import _build_vocabulary
    vocab = _build_vocabulary()
    class VocabWrap:
        def __init__(self, d): self.words = d
    v = VocabWrap(vocab)

    print("Word colours (sample):")
    for w in ["hamiltonian", "time", "energy", "weyl anomaly", "symmetry", "boson", "fermion"]:
        c = word_to_colour(w, v)
        if c:
            print(f"  {w:25s} -> {c}")
    print()

    # Test rank_by_colour_proximity
    print("Top 5 concepts colour-adjacent to 'hamiltonian':")
    for r in rank_by_colour_proximity("hamiltonian", v, top_n=5):
        print(f"  {r['word']:25s} {r['colour']}  dist={r['distance']}")
