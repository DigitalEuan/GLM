# ==============================================================================
# §17  SEMANTIC FRAMES — NATURAL LANGUAGE GENERATION (v3.9.0 NEW MODULE)
# ==============================================================================
# Adapted from core/glm_semantic_frames.py.  Gives GLM the ability to
# compose natural-language explanations from CRG edges and zone state,
# rather than only emitting "[KB] X: ..." or "[Backbone] a | b" tags.
#
# A frame is a small template with named slots:
#   * DEFINITION:        "<topic> is a <kind> that <verb>s <object>."
#   * RELATION:          "<lhs> scales as <rhs>."
#   * COMPOSITION:       "<whole> is the <relation> of <part1> and <part2>."
#   * CONSTRAINT:        "<lhs> commutes with <rhs>."
#   * DUALITY:           "<lhs> is dual to <rhs>."
#   * GENERATES:         "<lhs> generates <rhs>."
#   * MEASURES:          "<lhs> measures <rhs>."
#   * DEPENDS_ON:        "<lhs> depends on <rhs>."
#
# Frame selection is deterministic — pure function of the query + zone state.
# Slot fillers come from the zone's topic nouns + CRG backbone, so every
# generated sentence is grounded in the live vocabulary.
#
# Design rules:
#   * Pure stdlib, no I/O.
#   * Deterministic — same inputs → same output.
#   * Non-fatal — if a slot can't be filled, the frame is skipped.
# ==============================================================================
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set

from GLM01_substrate import BLA, CRGEdge


# ── 1. FRAME DEFINITIONS ─────────────────────────────────────────────────────

@dataclass
class FrameSlot:
    name: str
    role: str = "ANY"  # NOUN / VERB / ADJECTIVE / OPERATOR / PROPERTY / ANY
    seed_word: Optional[str] = None  # if set, prefer this word verbatim


@dataclass
class SemanticFrame:
    name: str
    template: str  # Python format string with slot names
    slots: List[FrameSlot]
    priority: int = 5  # lower = higher priority (0 = best)


FRAMES: List[SemanticFrame] = [
    # ── definitions ───────────────────────────────────────────────────────────
    SemanticFrame(
        name="definition_isa",
        template="the {topic} is a {kind} that {verb}s the {object}",
        slots=[FrameSlot("topic", "NOUN"),
               FrameSlot("kind", "NOUN"),
               FrameSlot("verb", "VERB"),
               FrameSlot("object", "NOUN")],
        priority=3,
    ),
    SemanticFrame(
        name="definition_property",
        template="the {topic} has the property of being {property}",
        slots=[FrameSlot("topic", "NOUN"),
               FrameSlot("property", "ADJECTIVE")],
        priority=4,
    ),
    # ── relations ─────────────────────────────────────────────────────────────
    SemanticFrame(
        name="scales_as",
        template="{lhs} scales as {rhs}",
        slots=[FrameSlot("lhs", "NOUN"),
               FrameSlot("rhs", "NOUN")],
        priority=2,
    ),
    SemanticFrame(
        name="depends_on",
        template="{lhs} depends on {rhs}",
        slots=[FrameSlot("lhs", "NOUN"),
               FrameSlot("rhs", "NOUN")],
        priority=2,
    ),
    SemanticFrame(
        name="commutes_with",
        template="{lhs} commutes with {rhs}",
        slots=[FrameSlot("lhs", "NOUN"),
               FrameSlot("rhs", "NOUN")],
        priority=1,
    ),
    SemanticFrame(
        name="dual_to",
        template="{lhs} is dual to {rhs}",
        slots=[FrameSlot("lhs", "NOUN"),
               FrameSlot("rhs", "NOUN")],
        priority=1,
    ),
    SemanticFrame(
        name="generates",
        template="{lhs} generates {rhs}",
        slots=[FrameSlot("lhs", "NOUN"),
               FrameSlot("rhs", "NOUN")],
        priority=1,
    ),
    SemanticFrame(
        name="measures",
        template="{lhs} measures {rhs}",
        slots=[FrameSlot("lhs", "NOUN"),
               FrameSlot("rhs", "NOUN")],
        priority=2,
    ),
    SemanticFrame(
        name="has_property",
        template="{lhs} has the property of being {rhs}",
        slots=[FrameSlot("lhs", "NOUN"),
               FrameSlot("rhs", "ADJECTIVE")],
        priority=3,
    ),
    SemanticFrame(
        name="is_a",
        template="{lhs} is a {rhs}",
        slots=[FrameSlot("lhs", "NOUN"),
               FrameSlot("rhs", "NOUN")],
        priority=3,
    ),
]


# ── 2. FRAME NAME → TEMPLATE LABEL MAP ───────────────────────────────────────

# Map CRG edge labels to the frame that verbalises them
_EDGE_TO_FRAME: Dict[str, str] = {
    "is_a": "is_a",
    "has_property": "has_property",
    "depends_on": "depends_on",
    "commutes_with": "commutes_with",
    "scales_as": "scales_as",
    "is_dual_to": "dual_to",
    "generates": "generates",
    "measures": "measures",
}


def _get_frame(name: str) -> Optional[SemanticFrame]:
    for f in FRAMES:
        if f.name == name:
            return f
    return None


# ── 3. FRAME FILLER ──────────────────────────────────────────────────────────

@dataclass
class FilledFrame:
    frame: SemanticFrame
    fillers: Dict[str, str]
    surface: str
    edge: Optional[CRGEdge] = None  # the CRG edge that grounded this frame, if any

    def __str__(self):
        return self.surface


def fill_frame_from_edge(edge: CRGEdge) -> Optional[FilledFrame]:
    """Verbalise a single CRG edge using the matching frame.

    Returns None if no frame matches the edge label.
    """
    frame_name = _EDGE_TO_FRAME.get(edge.label)
    if not frame_name:
        return None
    frame = _get_frame(frame_name)
    if not frame:
        return None

    # Fill the two slots from the edge's src and dst
    fillers: Dict[str, str] = {}
    if len(frame.slots) >= 2:
        fillers[frame.slots[0].name] = edge.src
        fillers[frame.slots[1].name] = edge.dst

    try:
        surface = frame.template.format(**fillers)
        return FilledFrame(frame=frame, fillers=fillers, surface=surface, edge=edge)
    except Exception:
        return None


def verbalise_backbone(backbone: List[CRGEdge], max_sentences: int = 3) -> str:
    """Turn a zone's CRG backbone into a natural-language paragraph.

    Picks up to `max_sentences` frames, ordered by frame priority then by
    edge order.  Returns an empty string if no edges can be verbalised.
    """
    if not backbone:
        return ""

    filled: List[FilledFrame] = []
    for edge in backbone:
        ff = fill_frame_from_edge(edge)
        if ff:
            filled.append(ff)

    if not filled:
        return ""

    # Sort by frame priority (lower = higher priority)
    filled.sort(key=lambda f: f.frame.priority)

    # Take the top N, but preserve a sensible sentence order
    chosen = filled[:max_sentences]

    # Capitalise first letter of each sentence, join with ". "
    sentences = []
    for ff in chosen:
        s = ff.surface
        if s:
            s = s[0].upper() + s[1:] if s else s
            sentences.append(s)
    return ". ".join(sentences) + "." if sentences else ""


# ── 4. FRAME SELECTION FOR QUERIES ───────────────────────────────────────────

def select_frames_for_query(query: str) -> List[SemanticFrame]:
    """Pick a sensible subset of frames based on the query phrasing.

    Deterministic: pure function of the query text.
    """
    qs = query.lower()
    chosen: List[SemanticFrame] = []
    seen: Set[str] = set()

    def _add(name: str):
        f = _get_frame(name)
        if f and f.name not in seen:
            chosen.append(f)
            seen.add(f.name)

    if any(w in qs for w in ("define", "what is", "what's", "describe")):
        _add("definition_isa")
        _add("definition_property")
    if any(w in qs for w in ("scale", "scaling", "power", "exponent")):
        _add("scales_as")
    if any(w in qs for w in ("depend", "function of", "sensitive to")):
        _add("depends_on")
    if any(w in qs for w in ("commute", "commutator")):
        _add("commutes_with")
    if any(w in qs for w in ("dual", "holographic", "ads", "bcft")):
        _add("dual_to")
    if any(w in qs for w in ("generate", "generator", "creates")):
        _add("generates")
    if any(w in qs for w in ("measure", "observable", "quantif")):
        _add("measures")
    if any(w in qs for w in ("relate", "relationship", "connection", "between")):
        _add("is_a")
        _add("depends_on")
        _add("commutes_with")

    if not chosen:
        # Default mix that works for most queries
        for n in ("is_a", "depends_on", "commutes_with"):
            _add(n)
    return chosen


# ── 5. NL GENERATION FROM ZONE STATE ─────────────────────────────────────────

def generate_explanation(zone: Any, query: str = "", max_sentences: int = 3) -> str:
    """Generate a natural-language explanation of a zone's current state.

    Combines:
      * The zone's thesis (if crystallised)
      * Verbalised CRG backbone edges
      * A definition-style sentence for the primary topic noun

    Returns a multi-sentence string.  Empty if the zone has no content.
    """
    if not zone or not getattr(zone, 'topic_nouns', None):
        return ""

    parts: List[str] = []

    # 1. If crystallised, lead with the thesis
    if getattr(zone, 'crystallized', False) and getattr(zone, 'thesis', ''):
        parts.append(zone.thesis)

    # 2. Verbalise the backbone
    backbone = getattr(zone, 'crg_backbone', [])
    if backbone:
        backbone_text = verbalise_backbone(backbone, max_sentences=max_sentences)
        if backbone_text:
            parts.append(backbone_text)

    # 3. If we have a primary topic noun and no backbone, generate a
    #    definition-style sentence using the frame templates
    if not parts and zone.topic_nouns:
        topic = zone.topic_nouns[0]
        # Try the is_a frame with the topic
        frame = _get_frame("is_a")
        if frame:
            try:
                surface = frame.template.format(lhs=topic, rhs="concept")
                surface = surface[0].upper() + surface[1:]
                parts.append(surface + ".")
            except Exception:
                pass

    return " ".join(parts) if parts else ""


# ── 6. ISOLATION TEST ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Testing Module 17: Semantic Frames (v3.9.0) ===")
    print()
    print("Frames defined:")
    for f in FRAMES:
        print(f"  {f.name:25s} priority={f.priority}  template='{f.template}'")
    print()

    # Test fill_frame_from_edge with mock edges
    from GLM01_substrate import CRGEdge

    test_edges = [
        CRGEdge(src="hamiltonian", label="generates", dst="time"),
        CRGEdge(src="hamiltonian", label="commutes_with", dst="symmetry"),
        CRGEdge(src="weyl anomaly", label="is_a", dst="anomaly"),
        CRGEdge(src="propagator", label="scales_as", dst="momentum"),
        CRGEdge(src="ads", label="is_dual_to", dst="bcft"),
        CRGEdge(src="entropy", label="measures", dst="dimension"),
        CRGEdge(src="beta", label="depends_on", dst="coupling"),
        CRGEdge(src="majorana", label="has_property", dst="topological"),
    ]
    print("Edge verbalisation:")
    for e in test_edges:
        ff = fill_frame_from_edge(e)
        if ff:
            print(f"  {e.src} --{e.label}--> {e.dst}  =>  '{ff.surface}'")
        else:
            print(f"  {e.src} --{e.label}--> {e.dst}  =>  (no frame)")
    print()

    # Test verbalise_backbone
    print("Backbone paragraph:")
    para = verbalise_backbone(test_edges, max_sentences=3)
    print(f"  {para}")
    print()

    # Test frame selection
    print("Frame selection for queries:")
    for q in ["What is the weyl anomaly?",
              "How does the hamiltonian relate to time?",
              "Describe the duality between ads and bcft."]:
        frames = select_frames_for_query(q)
        print(f"  '{q}'")
        print(f"    -> {[f.name for f in frames]}")
