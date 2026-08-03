"""
lingo_chat.py — the GLM's chat-like reasoning interface
=========================================================

Before attempting to solve a task, the GLM "chats" about it in Lingo.
This is the chat-like discovery mechanism: the GLM describes what it
sees (objects, colours, shapes), what transformations it has learned
(from the CRG), and what it thinks the rule might be — all in UBP-Lingo.

The chat output is retained in the full system output, providing a
human-readable reasoning trace.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import sys, os

_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import ARCTask, Grid
from generative.object_extractor import extract_objects, grid_to_sentence
from generative.object_crg import ObjectCRG
from lingo import LingoTranslator
from encoder import encode_grid


@dataclass
class ChatMessage:
    """A single message in the GLM's Lingo chat."""
    speaker: str          # "GLM" or "OBSERVER"
    lingo: str            # the Lingo expression
    human: str            # human-readable translation
    layer: str = ""       # which MOG layer this concerns


@dataclass
class ChatSession:
    """A complete chat session about one task."""
    task_id: str
    messages: List[ChatMessage] = field(default_factory=list)

    def add(self, speaker: str, lingo: str, human: str, layer: str = ""):
        self.messages.append(ChatMessage(speaker, lingo, human, layer))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "messages": [
                {"speaker": m.speaker, "lingo": m.lingo, "human": m.human, "layer": m.layer}
                for m in self.messages
            ],
        }


def chat_about_task(task: ARCTask, crg: ObjectCRG = None) -> ChatSession:
    """The GLM chats about a task in Lingo before solving it.

    The chat proceeds through the four MOG layers:
      1. REALITY: describe what's in the grid (objects, colours, shapes)
      2. INFORMATION: describe the structure (adjacency, topology, patterns)
      3. ACTIVATION: describe what operations might apply (from the CRG)
      4. POTENTIAL: describe the coherence and constraints (NRCI, Golay snap)
    """
    translator = LingoTranslator()
    session = ChatSession(task_id=task.name)

    # ── Layer 1: REALITY — what's in the grid? ──
    test_input = task.test[0].input
    objects = extract_objects(test_input)
    palette = sorted(test_input.palette())

    session.add("GLM",
        f"REALITY.OBSERVE layer=M_Space → SPATIAL_SUBSTRATE [{test_input.shape[0]}×{test_input.shape[1]}]",
        f"I see a {test_input.shape[0]}×{test_input.shape[1]} grid with {len(objects)} objects.",
        "REALITY")

    session.add("GLM",
        f"REALITY.OBSERVE layer=M_Charge → CHARGE_VALUE [palette={palette}]",
        f"The palette contains colours {palette}.",
        "REALITY")

    for obj in objects[:5]:  # cap at 5 objects for brevity
        session.add("GLM",
            f"REALITY.OBSERVE layer=M_Count → CLUSTER [colour={obj.colour}, cells={obj.cell_count}]",
            f"Object: colour {obj.colour}, {obj.cell_count} cells, bbox {obj.bbox}.",
            "REALITY")

    # ── Layer 2: INFORMATION — what's the structure? ──
    if len(objects) > 1:
        session.add("GLM",
            f"INFORMATION.OBSERVE layer=I_Connectivity → EDGE_BOND [{len(objects)} clusters]",
            f"{len(objects)} objects with adjacency structure.",
            "INFORMATION")

    # Encode the test input and report NRCI
    _, enc_report = encode_grid(test_input)
    nrci_label = translator.describe_nrci(enc_report.nrci_refined)
    session.add("GLM",
        f"INFORMATION.OBSERVE layer=I_Density → TOPO_SIGNATURE [HW={enc_report.hamming_weight}]",
        f"Grid encodes to HW={enc_report.hamming_weight}, NRCI={enc_report.nrci_refined:.4f} ({nrci_label}).",
        "INFORMATION")

    # ── Layer 3: ACTIVATION — what transformations has the GLM learned? ──
    if crg and crg.all_edges:
        dominant = crg.dominant_transform_type()
        lingo_expr = translator.describe_transformation(dominant)
        session.add("GLM",
            lingo_expr.to_lingo_string(),
            f"From {len(crg.all_edges)} learned transformations, the dominant type is '{dominant}'.",
            "ACTIVATION")

        if crg.global_colour_mapping:
            mapping_str = ", ".join(f"{k}→{v}" for k, v in sorted(crg.global_colour_mapping.items()))
            session.add("GLM",
                f"POTENTIAL.NEGATE layer=P_Ratio → CHARGE_SWAP [mapping={{{mapping_str}}}]",
                f"Learned colour mapping: {mapping_str}.",
                "ACTIVATION")
    else:
        # Learn from train pairs
        crg_new = ObjectCRG()
        crg_new.learn_from_task(task)
        if crg_new.all_edges:
            dominant = crg_new.dominant_transform_type()
            lingo_expr = translator.describe_transformation(dominant)
            session.add("GLM",
                lingo_expr.to_lingo_string(),
                f"Learning from train pairs: {len(crg_new.all_edges)} edges, dominant type '{dominant}'.",
                "ACTIVATION")
        else:
            session.add("GLM",
                "ACTIVATION.ID layer=A_Force → UNIT_NODE",
                "No clear transformation pattern detected in train pairs.",
                "ACTIVATION")

    # ── Layer 4: POTENTIAL — what's the coherence and constraint? ──
    manifested = enc_report.nrci_refined >= 0.70
    session.add("GLM",
        f"POTENTIAL.SELF_VALIDATION layer=P_Coherence → {'NRCI_MANIFEST' if manifested else 'NRCI_STABLE'}",
        f"Self-validation: {'PASS (manifested, NRCI ≥ 0.70)' if manifested else 'MARGINAL (NRCI < 0.70, needs refinement)'}.",
        "POTENTIAL")

    # ── Hypothesis ──
    if crg and crg.all_edges:
        dominant = crg.dominant_transform_type()
        session.add("GLM",
            f"POTENTIAL.OUTPUT layer=P_Phase → RECURSION [hypothesis={dominant}]",
            f"My hypothesis: the transformation is '{dominant}'. I will apply the learned transformation and verify via Three Column Thinking.",
            "POTENTIAL")
    else:
        session.add("GLM",
            "POTENTIAL.OUTPUT layer=P_Phase → RECURSION [hypothesis=unknown]",
            "My hypothesis: no clear pattern. I will fall back to the DSL vocabulary.",
            "POTENTIAL")

    return session
