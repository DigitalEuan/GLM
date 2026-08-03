# ══════════════════════════════════════════════════════════════════════════════
# §32  MODE ALGEBRA (v3.20.0 — Kracht sign grammar for compositional NL)
# ══════════════════════════════════════════════════════════════════════════════
#
# PURPOSE
#   Implement Marcus Kracht's sign grammar formally: a sign is a triple
#   σ = ⟨E, C, M⟩ where:
#     E = Exponent (the surface string form)
#     C = Category (the syntactic type — a VECTOR, not a scalar)
#     M = Meaning (the semantic content — CRG edge + substrate fingerprint)
#
#   The critical constraint (Kracht's "strongness"): a combination is only
#   "definite" when all three homomorphisms (ε, γ, µ) are defined
#   simultaneously. This is the formal content behind "compositional."
#
#   GLM currently CONFLATES these three into one 24-bit vector:
#     - computed_role() uses argmax over sextet weights → collapses C to a scalar
#     - CRGEdge.label plays all three roles at once (E, C, M)
#     - fill_frame_from_edge never checks slot roles against actual roles
#     - construct_paragraph discards the edge label and re-derives the verb
#
#   This module separates them. Every combination is gated on the simultaneous
#   definedness of all three. This eliminates word salad at the source —
#   instead of emitting "Time ent beweeping" and hoping, the mode-algebra
#   returns None when the combination isn't definite.
#
# ARCHITECTURE
#
#   Sign(dataclass):
#     E: str                    — surface form ("hamiltonian generates time")
#     C: Tuple[int,int,int,int] — category vector (full 4-tuple, NOT argmax)
#     M: Dict[str, Any]         — meaning (edge label + fingerprint + nrci)
#     definite: bool            — are all three homomorphisms defined?
#
#   Mode(dataclass):
#     name: str                 — e.g. "SVO", "RELATION", "DEFINITION"
#     arity: int                — 1 (unary) or 2 (binary)
#     exponent: Callable        — ε: how strings combine
#     category: Callable        — γ: what categories are compatible (returns bool)
#     meaning: Callable         — µ: what the combination means (returns dict or None)
#
#   combine(sign_a, sign_b, mode) -> Optional[Sign]:
#     Returns a new Sign only if mode.category(a.C, b.C) is True AND
#     mode.meaning(a.M, b.M) is not None AND mode.exponent(a.E, b.E) succeeds.
#     Otherwise returns None — the combination is NOT definite.
#
# KEY INSIGHT (Kracht §3.1)
#   The "strongness" requirement is the rigorous version of what
#   generate_grammatical() lacks. GLM's geometric traversal combines words
#   based on vector proximity alone — there is no defined mode with a
#   genuine, simultaneously-specified exponent function, category function,
#   and meaning function. This module provides exactly that.
#
# AUTHOR
#   Z.ai v3.20 development push — 2026-07-08
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# ── GLM imports ─────────────────────────────────────────────────────────────
try:
    from GLM01_substrate import (
        WordEntry, CRGEdge, EDGE_LABELS,
        vector_to_hex_int, fast_hamming, BLA,
    )
    from GLM22_ontological_grammar import (
        QUADRANT_RANGES, GRAMMAR_ROLE, QUADRANT_NAMES,
        dominant_quadrant, quadrant_weights, gap_vector,
    )
    _HAS_GLM = True
except Exception as _e:
    _HAS_GLM = False
    _GLM_ERR = str(_e)


# ══════════════════════════════════════════════════════════════════════════════
#  THE SIGN TRIPLE — Kracht's σ = ⟨E, C, M⟩
# ══════════════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class Sign:
    """A Kracht sign: ⟨Exponent, Category, Meaning⟩.

    E (Exponent): the surface string form — what the user sees.
    C (Category): the syntactic type as a 4-tuple of sextet weights.
                  NOT reduced to argmax — preserves the full category vector
                  so e.g. a noun with strong Activation bits can be flagged
                  as "noun-with-verb-affordance."
    M (Meaning):  the semantic content — CRG edge label + substrate
                  fingerprint + NRCI. Bottom = empty dict.
    definite:     True iff all three homomorphisms are defined (non-bottom).
    """
    E: str
    C: Tuple[int, int, int, int]
    M: Dict[str, Any]
    definite: bool = True

    @property
    def dominant_category(self) -> str:
        """The argmax category (for backward compat). 'NOUN'/'ADJECTIVE'/'VERB'/'OPERATOR'."""
        if not _HAS_GLM:
            return "NOUN"
        return GRAMMAR_ROLE[self.C.index(max(self.C))]

    @property
    def is_bottom(self) -> bool:
        """Bottom sign — undefined in at least one algebra."""
        return not self.definite or not self.E or not self.C or not self.M


# Bottom sign — the "undefined" value for all three algebras
BOTTOM = Sign(E="", C=(0, 0, 0, 0), M={}, definite=False)


# ══════════════════════════════════════════════════════════════════════════════
#  CATEGORY VECTOR — the full 4-tuple, NOT argmax
# ══════════════════════════════════════════════════════════════════════════════
def category_vector(word: str, vocab: Any) -> Tuple[int, int, int, int]:
    """Return the full 4-tuple of sextet weights for a word.

    This is the key function that replaces computed_role's argmax.
    Instead of collapsing to a single tag, we keep the full vector so
    downstream consumers can check category compatibility precisely.

    Returns (0,0,0,0) for words without vectors.
    """
    if not _HAS_GLM:
        return (0, 0, 0, 0)
    target = vocab.words if hasattr(vocab, 'words') else vocab
    entry = target.get(word)
    if not entry or not hasattr(entry, 'vector') or not entry.vector:
        return (0, 0, 0, 0)
    return tuple(quadrant_weights(entry.vector))


def category_vector_from_vec(vec: List[int]) -> Tuple[int, int, int, int]:
    """Category vector directly from a 24-bit vector."""
    if not _HAS_GLM:
        return (0, 0, 0, 0)
    return tuple(quadrant_weights(vec))


def dominant_role(cv: Tuple[int, int, int, int]) -> str:
    """Convenience: argmax over a category vector → role string."""
    if not _HAS_GLM:
        return "NOUN"
    if sum(cv) == 0:
        return "NOUN"
    return GRAMMAR_ROLE[list(cv).index(max(cv))]


def has_category_affordance(cv: Tuple[int, int, int, int],
                            role: str, threshold: int = 3) -> bool:
    """Does this category vector have enough weight in the `role` sextet?

    A "noun-with-verb-affordance" has dominant NOUN but also ≥3 bits in
    the VERB sextet. This lets the mode-algebra license combinations that
    argmax-only systems would reject.
    """
    if not _HAS_GLM:
        return False
    role_idx = {v: k for k, v in GRAMMAR_ROLE.items()}.get(role)
    if role_idx is None:
        return False
    return cv[role_idx] >= threshold


# ══════════════════════════════════════════════════════════════════════════════
#  MEANING — from CRG edges and substrate fingerprints
# ══════════════════════════════════════════════════════════════════════════════
def meaning_from_edge(edge: CRGEdge, fingerprint: Optional[Dict] = None) -> Dict[str, Any]:
    """Build the M-component of a sign from a CRG edge.

    The meaning dict carries:
      - 'label': the CRG edge label (is_a, generates, commutes_with, ...)
      - 'src': source concept
      - 'dst': destination concept
      - 'fingerprint': substrate fingerprint (if available)
      - 'nrci': NRCI from the fingerprint (if available)
    """
    m: Dict[str, Any] = {
        "label": edge.label,
        "src": edge.src,
        "dst": edge.dst,
    }
    if fingerprint:
        m["fingerprint"] = fingerprint
        if "nrci" in fingerprint:
            m["nrci"] = fingerprint["nrci"]
    return m


def meaning_from_concept(word: str, entry: Any,
                         fingerprint: Optional[Dict] = None) -> Dict[str, Any]:
    """Build the M-component from a single concept (no edge)."""
    m: Dict[str, Any] = {
        "label": "identity",
        "concept": word,
    }
    if hasattr(entry, 'ubp_id'):
        m["ubp_id"] = entry.ubp_id
    if hasattr(entry, 'nrci'):
        m["nrci"] = entry.nrci
    if hasattr(entry, 'definition') and entry.definition:
        m["definition"] = entry.definition
    if fingerprint:
        m["fingerprint"] = fingerprint
    return m


# ══════════════════════════════════════════════════════════════════════════════
#  SIGN CONSTRUCTORS — build signs from vocab entries
# ══════════════════════════════════════════════════════════════════════════════
def sign_from_word(word: str, vocab: Any,
                   fingerprint: Optional[Dict] = None) -> Sign:
    """Construct a Sign from a vocab word.

    E = the word itself (surface string)
    C = category_vector(word, vocab) — full 4-tuple
    M = meaning_from_concept(word, entry, fingerprint)
    definite = True if the word has a vector, False otherwise
    """
    if not _HAS_GLM:
        return BOTTOM
    target = vocab.words if hasattr(vocab, 'words') else vocab
    entry = target.get(word)
    if not entry or not hasattr(entry, 'vector') or not entry.vector:
        return BOTTOM
    cv = category_vector(word, vocab)
    m = meaning_from_concept(word, entry, fingerprint)
    return Sign(E=word, C=cv, M=m, definite=True)


def sign_from_edge(edge: CRGEdge, vocab: Any,
                   fingerprint: Optional[Dict] = None) -> Sign:
    """Construct a Sign from a CRG edge.

    E = verbalised edge (e.g. "hamiltonian generates time")
    C = category vector of the EDGE (derived from src+dst gap)
    M = meaning_from_edge(edge, fingerprint)
    definite = True if both src and dst have vectors
    """
    if not _HAS_GLM:
        return BOTTOM
    target = vocab.words if hasattr(vocab, 'words') else vocab
    s_entry = target.get(edge.src)
    o_entry = target.get(edge.dst)
    if not s_entry or not o_entry:
        # Try case-insensitive
        for w, e in target.items():
            if w.lower() == edge.src.lower():
                s_entry = e
            if w.lower() == edge.dst.lower():
                o_entry = e
    if not s_entry or not o_entry or not s_entry.vector or not o_entry.vector:
        return BOTTOM
    # The edge's category is the gap vector's category
    gap = gap_vector(s_entry.vector, o_entry.vector, mode="and")
    cv = category_vector_from_vec(gap)
    m = meaning_from_edge(edge, fingerprint)
    # Exponent: verbalise the edge
    e_str = verbalise_edge(edge)
    return Sign(E=e_str, C=cv, M=m, definite=True)


# ══════════════════════════════════════════════════════════════════════════════
#  EDGE VERBALISATION — the E-homomorphism for CRG edges
# ══════════════════════════════════════════════════════════════════════════════
# Complete the _EDGE_TO_FRAME mapping from GLM17 — cover ALL 17 edge labels,
# not just 8. Each label gets a surface form.

_EDGE_VERBALISATION: Dict[str, str] = {
    "is_a":              "{src} is a {dst}",
    "has_property":      "{src} has the property of being {dst}",
    "depends_on":        "{src} depends on {dst}",
    "commutes_with":     "{src} commutes with {dst}",
    "scales_as":         "{src} scales as {dst}",
    "is_dual_to":        "{src} is dual to {dst}",
    "generates":         "{src} generates {dst}",
    "measures":          "{src} measures {dst}",
    "lattice_adjacent":  "{src} is lattice-adjacent to {dst}",
    "lattice_adjacent_1": "{src} is lattice-adjacent (tier 1) to {dst}",
    "lattice_adjacent_2": "{src} is lattice-adjacent (tier 2) to {dst}",
    "lattice_adjacent_3": "{src} is lattice-adjacent (tier 3) to {dst}",
    "lattice_adjacent_4": "{src} is lattice-adjacent (tier 4) to {dst}",
    "lattice_adjacent_5": "{src} is lattice-adjacent (tier 5) to {dst}",
    "auto_proposed":     "{src} is auto-linked to {dst}",
    "contradicts":       "{src} contradicts {dst}",
    "incompatible_with": "{src} is incompatible with {dst}",
    "co_occurs":         "{src} co-occurs with {dst}",
}

# Edges that mark INDEFINITE combinations (Kracht: the meaning function
# returns bottom for these — no well-formed sentence asserts both at once)
_INDEFINITE_LABELS = {"contradicts", "incompatible_with"}


def verbalise_edge(edge: CRGEdge) -> str:
    """Verbalise a CRG edge as a surface string (E-homomorphism)."""
    template = _EDGE_VERBALISATION.get(edge.label, "{src} relates to {dst}")
    return template.format(src=edge.src, dst=edge.dst)


# ══════════════════════════════════════════════════════════════════════════════
#  MODES — typed composition rules (Kracht's "modes")
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class Mode:
    """A Kracht mode: a way of combining signs.

    Each mode specifies three functions simultaneously:
      exponent: ε — how the exponents (strings) combine
      category: γ — what categories are compatible (returns bool)
      meaning:  µ — what the combination means (returns dict or None)

    A combination is "definite" (valid) only when all three return non-bottom.
    """
    name: str
    arity: int  # 1 or 2
    exponent: Callable
    category: Callable
    meaning: Callable
    description: str = ""


# ── Mode: SVO (Subject-Verb-Object) ────────────────────────────────────────
def _svo_exponent(s: Sign, v: Sign, o: Sign) -> str:
    return f"{s.E.capitalize()} {v.E} {o.E}."

def _svo_category(s: Sign, v: Sign, o: Sign) -> bool:
    """Subject must be NOUN-dominant, verb must be VERB-dominant (or have
    verb-affordance), object must be NOUN-dominant."""
    s_role = dominant_role(s.C)
    v_role = dominant_role(v.C)
    o_role = dominant_role(o.C)
    # Subject: NOUN (or PROPERTY — a GLM-specific noun-like category)
    s_ok = s_role in ("NOUN",) or has_category_affordance(s.C, "NOUN", threshold=2)
    # Verb: VERB (or OPERATOR with verb-affordance)
    v_ok = v_role == "VERB" or has_category_affordance(v.C, "VERB", threshold=2)
    # Object: NOUN
    o_ok = o_role in ("NOUN",) or has_category_affordance(o.C, "NOUN", threshold=2)
    return s_ok and v_ok and o_ok

def _svo_meaning(s: Sign, v: Sign, o: Sign) -> Optional[Dict]:
    """The meaning of an SVO sentence: who does what to whom."""
    return {
        "label": "svo_action",
        "subject": s.E,
        "verb": v.E,
        "object": o.E,
        "subject_meaning": s.M,
        "verb_meaning": v.M,
        "object_meaning": o.M,
    }

MODE_SVO = Mode(
    name="SVO",
    arity=3,
    exponent=_svo_exponent,
    category=_svo_category,
    meaning=_svo_meaning,
    description="Subject-Verb-Object: the canonical English sentence form."
)


# ── Mode: RELATION (CRG edge verbalisation) ────────────────────────────────
def _relation_exponent(src: Sign, edge_sign: Sign) -> str:
    """The edge_sign already carries the verbalised form in its E."""
    return edge_sign.E.capitalize() + "."

def _relation_category(src: Sign, edge_sign: Sign) -> bool:
    """Source must have a non-zero category (defined, not bottom).
    The edge sign must have a non-zero category.
    Contradictions are indefinite (return False).

    Note: we do NOT require the source to be NOUN-dominant. After v3.17
    retired quadrant-forcing, the SVD-only vectors don't have clean
    quadrant dominance. Kracht's requirement is that the homomorphisms
    are DEFINED (non-bottom), not that they produce a specific category.
    The CRG edge label already determines the relation type — the category
    check just confirms the signs exist in the category algebra.
    """
    # Both signs must have non-zero category vectors (defined)
    if sum(src.C) == 0 or sum(edge_sign.C) == 0:
        return False
    # Check for indefinite labels (contradictions)
    label = edge_sign.M.get("label", "")
    if label in _INDEFINITE_LABELS:
        return False
    return True

def _relation_meaning(src: Sign, edge_sign: Sign) -> Optional[Dict]:
    """The meaning of a relation: the edge label + both endpoints."""
    label = edge_sign.M.get("label", "relates_to")
    if label in _INDEFINITE_LABELS:
        return None  # bottom — contradictions are not definite
    return {
        "label": label,
        "src": src.E,
        "dst": edge_sign.M.get("dst", ""),
        "src_meaning": src.M,
        "edge_meaning": edge_sign.M,
    }

MODE_RELATION = Mode(
    name="RELATION",
    arity=2,
    exponent=_relation_exponent,
    category=_relation_category,
    meaning=_relation_meaning,
    description="CRG edge verbalisation: X generates Y, X commutes with Y, etc."
)


# ── Mode: DEFINITION (is-a) ────────────────────────────────────────────────
def _definition_exponent(subject: Sign, kind: Sign) -> str:
    return f"{subject.E.capitalize()} is a {kind.E}."

def _definition_category(subject: Sign, kind: Sign) -> bool:
    """Subject must be NOUN, kind must be NOUN."""
    return (dominant_role(subject.C) == "NOUN" and
            dominant_role(kind.C) == "NOUN")

def _definition_meaning(subject: Sign, kind: Sign) -> Optional[Dict]:
    return {
        "label": "definition",
        "subject": subject.E,
        "kind": kind.E,
        "subject_meaning": subject.M,
        "kind_meaning": kind.M,
    }

MODE_DEFINITION = Mode(
    name="DEFINITION",
    arity=2,
    exponent=_definition_exponent,
    category=_definition_category,
    meaning=_definition_meaning,
    description="Is-a definition: X is a Y."
)


# ── Mode: CONTRADICTION (indefinite — for hedging) ─────────────────────────
def _contradiction_exponent(a: Sign, b: Sign) -> str:
    return f"{a.E.capitalize()} contradicts {b.E}."

def _contradiction_category(a: Sign, b: Sign) -> bool:
    """Both must be NOUN-dominant. But the meaning function returns None
    (bottom), so the combination is NOT definite."""
    return (dominant_role(a.C) == "NOUN" and
            dominant_role(b.C) == "NOUN")

def _contradiction_meaning(a: Sign, b: Sign) -> Optional[Dict]:
    """Returns None (bottom) — contradictions are not definite combinations.
    The considered-response layer can hedge these: 'X appears to contradict Y.'"""
    return None

MODE_CONTRADICTION = Mode(
    name="CONTRADICTION",
    arity=2,
    exponent=_contradiction_exponent,
    category=_contradiction_category,
    meaning=_contradiction_meaning,
    description="Contradiction: X contradicts Y. Marked indefinite (meaning=bottom)."
)


# ── Mode: ELABORATION (adding detail) ──────────────────────────────────────
def _elaboration_exponent(main: Sign, detail: Sign) -> str:
    return f"{main.E} — specifically, {detail.E}."

def _elaboration_category(main: Sign, detail: Sign) -> bool:
    """Main must be NOUN or VERB, detail must be NOUN or ADJECTIVE."""
    m_role = dominant_role(main.C)
    d_role = dominant_role(detail.C)
    return (m_role in ("NOUN", "VERB") and
            d_role in ("NOUN", "ADJECTIVE", "PROPERTY"))

def _elaboration_meaning(main: Sign, detail: Sign) -> Optional[Dict]:
    return {
        "label": "elaboration",
        "main": main.E,
        "detail": detail.E,
        "main_meaning": main.M,
        "detail_meaning": detail.M,
    }

MODE_ELABORATION = Mode(
    name="ELABORATION",
    arity=2,
    exponent=_elaboration_exponent,
    category=_elaboration_category,
    meaning=_elaboration_meaning,
    description="Elaboration: main concept + specifying detail."
)


# Registry of all modes
MODES: Dict[str, Mode] = {
    "SVO": MODE_SVO,
    "RELATION": MODE_RELATION,
    "DEFINITION": MODE_DEFINITION,
    "CONTRADICTION": MODE_CONTRADICTION,
    "ELABORATION": MODE_ELABORATION,
}


# ══════════════════════════════════════════════════════════════════════════════
#  COMBINE — the core Kracht operation
# ══════════════════════════════════════════════════════════════════════════════
def combine(*signs: Sign, mode: Mode) -> Optional[Sign]:
    """Combine signs using a mode. Returns a new Sign only if DEFINITE.

    A combination is definite when:
      1. mode.category(*signs) returns True (categories are compatible)
      2. mode.meaning(*signs) returns non-None (meaning is defined)
      3. mode.exponent(*signs) succeeds (surface form can be produced)

    If any check fails, returns None — the combination is NOT definite.
    This is Kracht's "strongness" requirement.
    """
    if not signs or len(signs) != mode.arity:
        return None

    # Check all inputs are definite (non-bottom)
    for s in signs:
        if s.is_bottom:
            return None

    # Check category compatibility
    try:
        if not mode.category(*signs):
            return None
    except Exception:
        return None

    # Check meaning definedness
    try:
        m = mode.meaning(*signs)
        if m is None:
            return None
    except Exception:
        return None

    # Compute exponent (surface form)
    try:
        e = mode.exponent(*signs)
        if not e:
            return None
    except Exception:
        return None

    # Compute the combined category (element-wise max of input categories)
    combined_cv = tuple(max(*vals) for vals in zip(*[s.C for s in signs]))

    return Sign(E=e, C=combined_cv, M=m, definite=True)


def combine_svo(subject: Sign, verb: Sign, obj: Sign) -> Optional[Sign]:
    """Convenience: combine three signs in SVO mode."""
    return combine(subject, verb, obj, mode=MODE_SVO)


def combine_relation(src: Sign, edge_sign: Sign) -> Optional[Sign]:
    """Convenience: combine source + edge in RELATION mode."""
    return combine(src, edge_sign, mode=MODE_RELATION)


def combine_definition(subject: Sign, kind: Sign) -> Optional[Sign]:
    """Convenience: combine subject + kind in DEFINITION mode."""
    return combine(subject, kind, mode=MODE_DEFINITION)


# ══════════════════════════════════════════════════════════════════════════════
#  BACKBONE WALK — generate definite sentences from a CRG backbone
# ══════════════════════════════════════════════════════════════════════════════
def backbone_to_signs(backbone: List[CRGEdge], vocab: Any,
                       max_signs: int = 5) -> List[Sign]:
    """Convert a CRG backbone into a list of definite Signs.

    For each edge in the backbone:
      1. Build a Sign from the source word
      2. Build a Sign from the edge
      3. Try combine_relation(src_sign, edge_sign)
      4. If definite, add to the output
      5. If not definite (e.g. contradiction), skip or hedge

    Returns only definite signs — no word salad.
    """
    if not _HAS_GLM:
        return []
    signs: List[Sign] = []
    for edge in backbone:
        src_sign = sign_from_word(edge.src, vocab)
        edge_sign = sign_from_edge(edge, vocab)
        if src_sign.is_bottom or edge_sign.is_bottom:
            continue
        combined = combine_relation(src_sign, edge_sign)
        if combined is not None:
            signs.append(combined)
        if len(signs) >= max_signs:
            break
    return signs


def signs_to_sentences(signs: List[Sign]) -> List[str]:
    """Convert definite signs into surface sentences."""
    return [s.E for s in signs if s.definite and s.E]


# ══════════════════════════════════════════════════════════════════════════════
#  STATUS / SELF-TEST
# ══════════════════════════════════════════════════════════════════════════════
def status() -> Dict[str, Any]:
    return {
        "module": "GLM32_mode_algebra",
        "version": "3.20.0",
        "operations": ["combine", "combine_svo", "combine_relation",
                       "combine_definition", "backbone_to_signs",
                       "signs_to_sentences", "category_vector",
                       "has_category_affordance"],
        "modes": list(MODES.keys()),
        "edge_verbalisations": len(_EDGE_VERBALISATION),
        "indefinite_labels": list(_INDEFINITE_LABELS),
    }


if __name__ == "__main__":
    print("=== GLM32 Mode Algebra v3.20.0 — self-test ===")
    print(status())
    print()

    if not _HAS_GLM:
        print("GLM substrate unavailable — cannot run demo.")
        raise SystemExit(1)

    from GLM01_substrate import _build_vocabulary
    from GLM03_crg import build_extended_crg

    vocab_dict = _build_vocabulary()
    class V:
        def __init__(self, d): self.words = d
    v = V(vocab_dict)
    crg = build_extended_crg()

    # Test 1: category_vector (full 4-tuple, not argmax)
    print("--- category_vector (full 4-tuple) ---")
    for word in ["hamiltonian", "time", "energy", "generates", "symmetry"]:
        cv = category_vector(word, v)
        role = dominant_role(cv)
        print(f"  {word!r}: C={cv} dominant={role}")

    # Test 2: sign_from_word
    print("\n--- sign_from_word ---")
    for word in ["hamiltonian", "time", "energy"]:
        s = sign_from_word(word, v)
        print(f"  {word!r}: E={s.E!r} C={s.C} definite={s.definite}")
        print(f"    M keys: {list(s.M.keys())}")

    # Test 3: sign_from_edge + combine_relation
    print("\n--- sign_from_edge + combine_relation ---")
    for edge in crg.edges[:5]:
        if edge.label in _INDEFINITE_LABELS:
            continue
        src_sign = sign_from_word(edge.src, v)
        edge_sign = sign_from_edge(edge, v)
        combined = combine_relation(src_sign, edge_sign)
        if combined:
            print(f"  DEFINITE: {combined.E!r}")
            print(f"    M label: {combined.M.get('label')}")
        else:
            print(f"  NOT DEFINITE: {edge.src} --{edge.label}--> {edge.dst}")

    # Test 4: backbone_to_signs
    print("\n--- backbone_to_signs ---")
    # Build a small backbone from CRG edges
    backbone = [e for e in crg.edges if e.src == "hamiltonian"][:3]
    signs = backbone_to_signs(backbone, v)
    sentences = signs_to_sentences(signs)
    print(f"  backbone: {[(e.src, e.label, e.dst) for e in backbone]}")
    print(f"  definite signs: {len(signs)}")
    for s in sentences:
        print(f"    -> {s!r}")

    # Test 5: contradiction (should be NOT definite)
    print("\n--- contradiction (indefinite) ---")
    # Find a contradicts edge
    for edge in crg.edges:
        if edge.label == "contradicts":
            src_sign = sign_from_word(edge.src, v)
            edge_sign = sign_from_edge(edge, v)
            combined = combine_relation(src_sign, edge_sign)
            print(f"  {edge.src} --{edge.label}--> {edge.dst}")
            print(f"  combined: {combined}")
            break
