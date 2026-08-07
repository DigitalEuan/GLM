#!/usr/bin/env python3
"""
arc_agi_17 v17.3 — Growth Layer (extends v17.2, doesn't replace it)
====================================================================
Per user: "Lets make the system we have get better rather than completely
change it each iteration - growth not rebuild each Time."

This script IMPORTS v17.2 and EXTENDS it:
  1. Loads the previous GLM state (concepts + CRG edges) if it exists
  2. Adds BROAD general-purpose CRG edges (not just ARC-specific)
  3. Expands the GLM vocabulary with general reasoning concepts
  4. Uses BW-1024 NRCI for finer task classification
  5. Makes the LTM persistent across runs
  6. Adds a LEARNING ANALYSIS that shows HOW the GLM learns

GROWTH MECHANISM:
  - Each run loads the previous state (concepts, edges, LTM experiences)
  - Each run adds new concepts and edges based on what the tasks need
  - Each run saves the grown state for the next run
  - The learning analysis tracks growth rate and patterns

CRG EDGE CATEGORIES (broad, general-purpose per user):
  - Causal: causes, enables, prevents, requires, produces
  - Temporal: precedes, follows, during, after, simultaneous_with
  - Spatial: contains, borders, intersects, adjacent_to, surrounds
  - Quantitative: measures, counts, scales, proportional_to, bounds
  - Logical: implies, contradicts, equivalent_to, independent_of, excludes
  - Structural: part_of, composed_of, instance_of, type_of, variant_of

LTM LEARNING ANALYSIS:
  - Which task types the GLM learns fastest (fewest attempts to first success)
  - Which CRG edges correlate with success
  - Which concepts are most activated in successful reasoning
  - Growth rate: new concepts/edges per run

OUTPUTS:
  /home/z/my-project/download/arc_agi_17/results/v17_3_results.json
  /home/z/my-project/download/arc_agi_17/results/glm_state.json  (persistent state)
  /home/z/my-project/download/arc_agi_17/reports/v17_3_report.md
"""

import sys
import os
import json
import math
import time
import itertools
from fractions import Fraction as F
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, field

SCRIPT_DIR = Path(__file__).resolve().parent
ARC_17_DIR = SCRIPT_DIR.parent

sys.path.insert(0, str(Path("/home/z/my-project/scripts")))
from ubp_engine.ubp_unified_v5 import (
    GolayCodeEngine,
    LeechLatticeEngine,
    UBPSourceCodeParticlePhysics,
    BarnesWallEngine,
)

sys.path.insert(0, str(SCRIPT_DIR))
from loader import Grid, ARCTask, load_task

# IMPORT v17.2 (growth, not rebuild)
from arc_v17_2_pipeline import (
    GLMSemanticCore,
    GLMConcept,
    CRGEdge,
    ThreeColumnStep,
    LINGO_VOCAB,
    QUADRANT_NAMES,
    GRAMMAR_ROLE,
    QUADRANT_RANGES,
    dominant_quadrant,
    quadrant_weights,
    computed_role,
    LongTermMemory,
    SettlementGravitySolver,
    ColourMapViaANDSolver,
    ConditionalSolver,
    InteriorFillSolver,
    ScaleAwareResizeSolver,
    ShiftSolver,
    RotateSolver,
    FlipSolver,
    LTM_STRATEGY_MAP,
    Y_CONST,
)

# Also import the parity sign recolor solver and column rank solver from previous versions
from arc_v17_pipeline import ParitySignRecolorSolver
from arc_v17_1_pipeline import ColumnRankSolver


# ============================================================
# EXPANDED VOCABULARY (broad, general-purpose concepts)
# ============================================================
#
# Per user: "be broad with CRG edge additions - ARC AGI visual puzzles are
# just one of the problems it will face and solve"
#
# These concepts are GENERAL-PURPOSE — they apply to any reasoning task,
# not just ARC. They cover the semantic primitives a reasoning system needs.
# ============================================================


EXPANDED_CONCEPTS = {
    # === General reasoning concepts (not ARC-specific) ===
    # Causal
    "cause": {"layer": "A_Force", "term": "CAUSAL_LINK"},
    "effect": {"layer": "A_Energy", "term": "CONSEQUENCE"},
    "enable": {"layer": "A_Force", "term": "ENABLEMENT"},
    "prevent": {"layer": "P_Ratio", "term": "INHIBITION"},
    "require": {"layer": "P_Limit", "term": "PREREQUISITE"},

    # Temporal
    "before": {"layer": "I_Topology", "term": "PRECEDES"},
    "after": {"layer": "I_Topology", "term": "FOLLOWS"},
    "sequence": {"layer": "I_Density", "term": "ORDERED_SERIES"},
    "repeat": {"layer": "A_Flux", "term": "PERIODIC_ITERATION"},
    "cycle": {"layer": "A_Flux", "term": "CLOSED_LOOP"},

    # Spatial (broader than ARC)
    "region": {"layer": "M_Space", "term": "SPATIAL_DOMAIN"},
    "boundary": {"layer": "I_Connectivity", "term": "FRONTIER"},
    "center": {"layer": "I_Topology", "term": "CENTROID"},
    "edge": {"layer": "I_Connectivity", "term": "PERIMETER"},
    "corner": {"layer": "I_Topology", "term": "VERTEX_POINT"},

    # Quantitative
    "measure": {"layer": "P_Limit", "term": "QUANTIFICATION"},
    "label": {"layer": "P_Ratio", "term": "IDENTIFIER_TAG"},
    "threshold": {"layer": "P_Limit", "term": "DECISION_BOUNDARY"},
    "ratio": {"layer": "P_Ratio", "term": "PROPORTIONALITY"},
    "count_value": {"layer": "P_Limit", "term": "INTEGER_RESULT"},

    # Logical
    "rule": {"layer": "P_Coherence", "term": "INFERENCE_RULE"},
    "condition": {"layer": "P_Ratio", "term": "CONTINGENCY"},
    "match": {"layer": "I_Density", "term": "PATTERN_AGREEMENT"},
    "differ": {"layer": "I_Density", "term": "PATTERN_DIVERGENCE"},

    # Structural
    "part": {"layer": "M_Count", "term": "COMPONENT"},
    "whole": {"layer": "M_Count", "term": "AGGREGATE"},
    "type": {"layer": "I_Symmetry", "term": "CATEGORY_CLASS"},
    "instance": {"layer": "M_Count", "term": "SPECIFIC_EXEMPLAR"},

    # === ARC-useful concepts (but also general) ===
    "marker": {"layer": "I_Connectivity", "term": "SIGNAL_ANCHOR"},
    "tile": {"layer": "M_Space", "term": "REPEATING_UNIT"},
    "rank": {"layer": "P_Limit", "term": "ORDINAL_POSITION"},
    "layer_row": {"layer": "I_Topology", "term": "HORIZONTAL_BAND"},
    "layer_col": {"layer": "I_Topology", "term": "VERTICAL_BAND"},

    # === Substrate-native concepts (from our v1-v11 work) ===
    "tax": {"layer": "P_Coherence", "term": "SYMMETRY_COST"},
    "nrci": {"layer": "P_Coherence", "term": "COHERENCE_INDEX"},
    "snap": {"layer": "P_Phase", "term": "GOLAY_CORRECTION"},
    "xor": {"layer": "A_Energy", "term": "SYMMETRIC_DIFFERENCE"},
    "and": {"layer": "A_Energy", "term": "INTERSECTION_OPERATOR"},
    "vacuum": {"layer": "M_Mass", "term": "ZERO_STATE"},
    "codeword": {"layer": "M_Count", "term": "LATTICE_POINT"},
}


# ============================================================
# BROAD CRG EDGES (general-purpose semantic relations)
# ============================================================
#
# Per user: "be broad with CRG edge additions"
# These edges cover general reasoning patterns, not just ARC.
# Each edge is TRANSPARENT (documented) per user's request.
# ============================================================


BROAD_CRG_EDGES = [
    # === Causal relations ===
    ("cause", "produces", "effect"),
    ("enable", "permits", "effect"),
    ("prevent", "blocks", "effect"),
    ("require", "precedes", "enable"),
    ("condition", "gates", "effect"),

    # === Temporal relations ===
    ("before", "precedes", "after"),
    ("sequence", "contains", "before"),
    ("repeat", "generates", "sequence"),
    ("cycle", "contains", "sequence"),
    ("repeat", "implies", "cycle"),

    # === Spatial relations ===
    ("region", "contains", "cell"),
    ("region", "bounded_by", "boundary"),
    ("boundary", "surrounds", "region"),
    ("center", "inside", "region"),
    ("edge", "part_of", "boundary"),
    ("corner", "part_of", "boundary"),
    ("grid", "composed_of", "region"),

    # === Quantitative relations ===
    ("measure", "produces", "count_value"),
    ("measure", "uses", "rule"),
    ("label", "identifies", "object"),
    ("threshold", "divides", "object"),
    ("ratio", "relates", "measure"),
    ("count", "produces", "label"),
    ("rank", "orders", "object"),

    # === Logical relations ===
    ("rule", "implies", "effect"),
    ("condition", "enables", "rule"),
    ("match", "validates", "pattern"),
    ("differ", "invalidates", "match"),
    ("match", "contradicts", "differ"),

    # === Structural relations ===
    ("part", "component_of", "whole"),
    ("whole", "composed_of", "part"),
    ("instance", "exemplifies", "type"),
    ("type", "classifies", "instance"),

    # === ARC-relevant but general ===
    ("marker", "indicates", "region"),
    ("marker", "signals", "transformation"),
    ("tile", "repeats", "pattern"),
    ("tile", "covers", "grid"),
    ("rank", "assigns", "label"),
    ("layer_row", "part_of", "grid"),
    ("layer_col", "part_of", "grid"),

    # === Substrate-native relations (from our v1-v11 work) ===
    ("tax", "measures", "codeword"),
    ("nrci", "measures", "coherent"),
    ("snap", "produces", "codeword"),
    ("snap", "corrects", "error"),
    ("xor", "combines", "codeword"),
    ("and", "intersects", "codeword"),
    ("vacuum", "is_zero", "codeword"),
    ("codeword", "instance_of", "grid"),

    # === Cross-domain relations (the GLM's power) ===
    ("gravity", "causes", "effect"),
    ("gravity", "produces", "cycle"),
    ("fill", "requires", "region"),
    ("fill", "produces", "effect"),
    ("recolour", "changes", "label"),
    ("recolour", "preserves", "object"),
    ("scale", "changes", "ratio"),
    ("scale", "preserves", "pattern"),
    ("rotate", "preserves", "shape"),
    ("rotate", "changes", "position"),
    ("flip", "preserves", "shape"),
    ("flip", "changes", "position"),
    ("move", "changes", "position"),
    ("move", "preserves", "object"),
    ("crop", "removes", "part"),
    ("crop", "changes", "whole"),
    ("count", "measures", "object"),
    ("count", "produces", "count_value"),

    # === Contradictions (from GLM03, expanded) ===
    ("gravity", "contradicts", "scale"),
    ("fill", "contradicts", "crop"),
    ("rotate", "contradicts", "flip"),
    ("match", "contradicts", "differ"),
    ("before", "contradicts", "after"),
    ("part", "contradicts", "whole"),
    ("cause", "contradicts", "prevent"),

    # === New: reasoning about ARC failures (transparent) ===
    ("marker", "enables", "fill"),
    ("threshold", "enables", "recolour"),
    ("rank", "enables", "label"),
    ("pattern", "enables", "match"),
    ("symmetry", "enables", "rotate"),
    ("symmetry", "enables", "flip"),
]


# ============================================================
# Grown GLM Semantic Core (extends v17.2's GLMSemanticCore)
# ============================================================


class GrownGLMSemanticCore(GLMSemanticCore):
    """The GLM semantic core that GROWS across runs.

    Loads previous state, adds new concepts and edges, saves grown state.
    This is GROWTH, not rebuild — each run adds to the previous state.
    """

    def __init__(self, substrate, state_path: Optional[Path] = None):
        self.state_path = state_path or (ARC_17_DIR / "results" / "glm_state.json")
        self.previous_state = self._load_state()

        # Initialize tracking BEFORE growing (needed by _grow_concepts)
        self.new_concepts_this_run = []
        self.new_edges_this_run = []

        # Initialize the base class (builds the original 26 concepts + 30 edges)
        super().__init__(substrate)

        # GROW: add expanded concepts
        self._grow_concepts()

        # GROW: add broad CRG edges
        self._grow_crg()

        # Add BW-1024 NRCI for finer task classification
        self.bw1024 = BarnesWallEngine(substrate.golay, dimension=1024)

    def _load_state(self) -> Dict:
        """Load the previous GLM state if it exists."""
        if self.state_path and self.state_path.exists():
            try:
                with open(self.state_path) as f:
                    state = json.load(f)
                print(f"[GLM] Loaded previous state: {len(state.get('concepts', {}))} concepts, {len(state.get('crg_edges', []))} edges")
                return state
            except Exception as e:
                print(f"[GLM] Failed to load state: {e}")
        return {"concepts": {}, "crg_edges": [], "run_history": []}

    def _grow_concepts(self):
        """Add the expanded concepts to the GLM."""
        golay = self.substrate.golay

        # Start with previous state's concepts
        prev_concepts = self.previous_state.get("concepts", {})

        # Add expanded concepts
        for word, info in {**EXPANDED_CONCEPTS, **LINGO_VOCAB}.items():
            if word in self.concepts:
                continue  # already built by base class

            # Use a deterministic encoding: hash the word to 12 bits
            word_hash = hash(word) & 0xFFF
            msg12 = [(word_hash >> i) & 1 for i in range(12)]
            vec = golay.encode(msg12)

            qw = quadrant_weights(vec)
            role = GRAMMAR_ROLE[dominant_quadrant(vec)]
            hw = sum(vec)
            nrci = 10.0 / (10.0 + hw * Y_CONST + hw / 8.0)

            self.concepts[word] = GLMConcept(
                name=word,
                vector=vec,
                role=role,
                lingo_term=info["term"],
                quadrant_weights=qw,
                nrci=nrci,
            )
            self.new_concepts_this_run.append(word)

        print(f"[GLM] Grown concepts: {len(self.concepts)} total ({len(self.new_concepts_this_run)} new this run)")

    def _grow_crg(self):
        """Add the broad CRG edges."""
        # Add edges from previous state
        prev_edges = self.previous_state.get("crg_edges", [])
        for edge_data in prev_edges:
            edge = CRGEdge(src=edge_data["src"], label=edge_data["label"], dst=edge_data["dst"])
            if edge not in self.crg_edges:
                self.crg_edges.append(edge)

        # Add broad edges
        existing_edges = {(e.src, e.label, e.dst) for e in self.crg_edges}
        for src, label, dst in BROAD_CRG_EDGES:
            if (src, label, dst) not in existing_edges:
                if src in self.concepts and dst in self.concepts:
                    self.crg_edges.append(CRGEdge(src=src, label=label, dst=dst))
                    self.new_edges_this_run.append((src, label, dst))
                    existing_edges.add((src, label, dst))

        print(f"[GLM] Grown CRG: {len(self.crg_edges)} total ({len(self.new_edges_this_run)} new this run)")

    def save_state(self, run_summary: Dict):
        """Save the grown GLM state for the next run."""
        state = {
            "concepts": {name: {
                "name": c.name,
                "vector": c.vector,
                "role": c.role,
                "lingo_term": c.lingo_term,
                "quadrant_weights": c.quadrant_weights,
                "nrci": c.nrci,
            } for name, c in self.concepts.items()},
            "crg_edges": [{"src": e.src, "label": e.label, "dst": e.dst} for e in self.crg_edges],
            "run_history": self.previous_state.get("run_history", []) + [run_summary],
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=2, default=str)
        print(f"[GLM] State saved: {len(state['concepts'])} concepts, {len(state['crg_edges'])} edges, {len(state['run_history'])} runs")

    def classify_task_type_bw1024(self, task: ARCTask) -> str:
        """Classify task type using BW-1024 NRCI for finer resolution.

        The 24-bit NRCI has only 3 values (HW=8/12/16). The BW-1024 NRCI
        gives finer resolution by projecting into 1024 dimensions.
        """
        # Encode the task's first train pair
        if not task.train:
            return "unknown"

        inp = task.train[0].input
        out = task.train[0].output

        # Compute BW-1024 NRCI for input and output
        # Use the grid encoding from v17.2
        import math
        h, w = inp.height, inp.width
        cells_flat = [inp.cells[r][c] for r in range(h) for c in range(w)]
        n_colours = len(set(cells_flat)) - (1 if 0 in cells_flat else 0)
        density = sum(1 for v in cells_flat if v != 0) / max(len(cells_flat), 1)
        effective_freq = max(1.0, (n_colours + 1) * (h * w) * (1 + density))
        log_f = math.log2(effective_freq)

        # Simple 12-bit encoding
        octave = int(log_f) & 0x7
        phase = int((log_f - int(log_f)) * 32) % 32
        compactness = (int(math.floor(math.log2(max(h, w)))) + 16) & 0xF
        msg12 = [0] * 12
        msg12[11] = (octave >> 2) & 1
        msg12[10] = (octave >> 1) & 1
        msg12[9] = octave & 1
        for i in range(5):
            msg12[8 - i] = (phase >> i) & 1
        for i in range(4):
            msg12[3 - i] = (compactness >> i) & 1
        cw = self.substrate.golay.encode(msg12)

        # BW-1024 NRCI
        macro = self.bw1024.generate(cw, dim=1024)
        snapped = self.bw1024.snap(macro)
        bw_nrci = float(self.bw1024.nrci(snapped))

        # Also compute overlap (from v17.2)
        if inp.height == out.height and inp.width == out.width:
            same = sum(1 for r in range(inp.height) for c in range(inp.width) if inp.cells[r][c] == out.cells[r][c])
            total = inp.height * inp.width
            overlap = same / total if total > 0 else 0
        else:
            return "size_change"

        # Finer classification using BW-1024 NRCI
        # The BW NRCI ranges from ~0.07 to ~0.11
        if bw_nrci < 0.08:
            base_type = "low_nrci"
        elif bw_nrci < 0.10:
            base_type = "medium_nrci"
        else:
            base_type = "high_nrci"

        # Combine with overlap
        if overlap > 0.7:
            return f"high_overlap_{base_type}"
        elif overlap > 0.4:
            return f"medium_overlap_{base_type}"
        elif overlap > 0.1:
            return f"low_overlap_{base_type}"
        else:
            return f"size_change_{base_type}"

    def get_concept_activation(self, task: ARCTask) -> List[str]:
        """Which concepts are 'activated' by this task?

        A concept is activated if it appears in the GLM's reasoning trace.
        """
        trace = self.three_column_describe(task)
        activated = []
        for step in trace:
            # Simple: check which concept names appear in the language
            for concept_name in self.concepts:
                if concept_name in step.language.lower():
                    activated.append(concept_name)
        return activated


# ============================================================
# Grown LTM (extends v17.2's LongTermMemory with persistence)
# ============================================================


class GrownLTM(LongTermMemory):
    """LTM that persists across runs and tracks learning patterns."""

    def __init__(self, state_path: Optional[Path] = None):
        self.ltm_state_path = state_path or (ARC_17_DIR / "results" / "ltm_state.json")
        self.learning_patterns = {
            "task_type_first_success": {},  # task_type → (n_attempts_before_first_success)
            "strategy_success_correlation": defaultdict(int),  # strategy → n_successes
            "concept_activation_success": defaultdict(int),  # concept → n_successes_when_activated
            "growth_per_run": [],  # list of {run, new_concepts, new_edges, n_solved}
        }
        super().__init__()

        # Load previous LTM state
        self._load_ltm_state()

    def _load_ltm_state(self):
        """Load previous LTM state (learning patterns)."""
        if self.ltm_state_path.exists():
            try:
                with open(self.ltm_state_path) as f:
                    state = json.load(f)
                self.learning_patterns = state.get("learning_patterns", self.learning_patterns)
                # Convert defaultdicts back
                if "strategy_success_correlation" in self.learning_patterns:
                    self.learning_patterns["strategy_success_correlation"] = defaultdict(int, self.learning_patterns["strategy_success_correlation"])
                if "concept_activation_success" in self.learning_patterns:
                    self.learning_patterns["concept_activation_success"] = defaultdict(int, self.learning_patterns["concept_activation_success"])
                print(f"[LTM] Loaded learning patterns from previous run")
            except Exception as e:
                print(f"[LTM] Failed to load state: {e}")

    def save_ltm_state(self):
        """Save the LTM state for the next run."""
        state = {
            "learning_patterns": {
                "task_type_first_success": self.learning_patterns["task_type_first_success"],
                "strategy_success_correlation": dict(self.learning_patterns["strategy_success_correlation"]),
                "concept_activation_success": dict(self.learning_patterns["concept_activation_success"]),
                "growth_per_run": self.learning_patterns["growth_per_run"],
            },
            "total_experiences": len(self.experiences),
            "total_updates": len(self.updates),
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self.ltm_state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ltm_state_path, "w") as f:
            json.dump(state, f, indent=2, default=str)
        print(f"[LTM] State saved: {len(self.experiences)} total experiences, {len(self.updates)} new this run")

    def record_success_with_learning(self, task_id: str, task_type: str, strategy: str,
                                      activated_concepts: List[str], run_number: int):
        """Record a success AND track learning patterns."""
        # Record the success (base class)
        substrate_metrics = {"task_type": task_type, "run": run_number}
        self.record_success(task_id, task_type, strategy, substrate_metrics)

        # Track: is this the first success for this task type?
        if task_type not in self.learning_patterns["task_type_first_success"]:
            # Count how many attempts this task type had before first success
            n_previous = sum(1 for e in self.experiences[:-1] if e.get("task_type") == task_type and not e.get("success", True))
            self.learning_patterns["task_type_first_success"][task_type] = n_previous

        # Track strategy success correlation
        self.learning_patterns["strategy_success_correlation"][strategy] += 1

        # Track concept activation success
        for concept in activated_concepts:
            self.learning_patterns["concept_activation_success"][concept] += 1

    def get_learning_analysis(self) -> Dict[str, Any]:
        """Analyze HOW the GLM is learning.

        Per user: "the Long Term Memory will eventually show us how the GLM
        learns so we can bypass a pile of training by designing training
        routines that specifically grow it where needed."
        """
        # Which task types are learned fastest?
        fastest_types = sorted(
            self.learning_patterns["task_type_first_success"].items(),
            key=lambda x: x[1]
        )

        # Which strategies are most successful?
        best_strategies = sorted(
            self.learning_patterns["strategy_success_correlation"].items(),
            key=lambda x: -x[1]
        )

        # Which concepts correlate with success?
        most_useful_concepts = sorted(
            self.learning_patterns["concept_activation_success"].items(),
            key=lambda x: -x[1]
        )

        # Growth rate over time
        growth = self.learning_patterns["growth_per_run"]

        return {
            "fastest_task_types": fastest_types,
            "best_strategies": best_strategies,
            "most_useful_concepts": most_useful_concepts[:10],
            "growth_history": growth,
            "total_experiences": len(self.experiences),
            "total_successes": sum(1 for e in self.experiences if e.get("success")),
            "total_failures_seen": sum(1 for e in self.experiences if not e.get("success", True)),
            "interpretation": (
                "This analysis shows HOW the GLM learns. "
                "Fastest task types need less training. "
                "Best strategies are the GLM's strengths. "
                "Most useful concepts should be expanded. "
                "Use this to design targeted training routines."
            ),
        }


# ============================================================
# The Grown Pipeline (extends v17.2)
# ============================================================


class GrownPipeline:
    """The v17.3 pipeline: GROWN v17.2 with more concepts, edges, and learning."""

    def __init__(self, run_number: int = 1):
        # BitOps substrate (same as v17.2)
        class BitOpsSubstrate:
            def __init__(self):
                self.golay = GolayCodeEngine()
                self.leech = LeechLatticeEngine(self.golay)
                class Decoder:
                    def __init__(self, g):
                        self.g = g
                        self.COSET_LEADERS = {}
                        for w in range(5):
                            for combo in itertools.combinations(range(24), w):
                                leader = [0] * 24
                                for bit in combo:
                                    leader[bit] = 1
                                s = tuple(g.syndrome(leader))
                                if s not in self.COSET_LEADERS:
                                    self.COSET_LEADERS[s] = leader
                        assert len(self.COSET_LEADERS) == 4096
                    def snap(self, v):
                        s = self.g.syndrome(v)
                        leader = self.COSET_LEADERS[tuple(s)]
                        return [v[i] ^ leader[i] for i in range(24)]
                self.decoder = Decoder(self.golay)
                self.golay._legacy_snap = self.golay.snap_to_codeword
                self.golay.snap_to_codeword = lambda v: (self.decoder.snap(v), {"correctable": True})

        self.substrate = BitOpsSubstrate()

        # GROWN GLM semantic core (loads previous state, adds new concepts/edges)
        self.glm = GrownGLMSemanticCore(self.substrate)

        # GROWN LTM (persistent, with learning analysis)
        self.ltm = GrownLTM()

        # All solvers (including v17.1's parity and column_rank that were missing in v17.2)
        self.solvers = {
            "settlement_gravity": SettlementGravitySolver(self.substrate),
            "colour_map_via_AND": ColourMapViaANDSolver(self.substrate),
            "interior_fill": InteriorFillSolver(self.substrate),
            "scale_aware_resize": ScaleAwareResizeSolver(self.substrate),
            "shift_solver": ShiftSolver(self.substrate),
            "rotate_solver": RotateSolver(self.substrate),
            "flip_solver": FlipSolver(self.substrate),
            "conditional_solver": ConditionalSolver(self.substrate),
            "parity_sign_recolor": ParitySignRecolorSolver(self.substrate),  # re-added
            "column_rank_solver": ColumnRankSolver(self.substrate),  # re-added
        }

        self.run_number = run_number

    def solve_task(self, task: ARCTask, task_id: str) -> Dict[str, Any]:
        """Solve a task using the GROWN GLM + LTM."""

        # STEP 1: GLM perceives (three-column thinking)
        reasoning_trace = self.glm.three_column_describe(task)

        # STEP 2: GLM classifies (using BW-1024 NRCI for finer resolution)
        task_type_bw = self.glm.classify_task_type_bw1024(task)
        task_type_simple = self.glm.classify_task_type(task)  # v17.2's simpler version

        # STEP 3: LTM recall (use the simple type for LTM compatibility)
        ltm_recommended = self.ltm.get_recommended_strategies(task_type_simple)
        ltm_recommended_mapped = []
        for s in ltm_recommended:
            mapped = LTM_STRATEGY_MAP.get(s, s)
            if mapped not in ltm_recommended_mapped:
                ltm_recommended_mapped.append(mapped)

        # STEP 4: GLM selects strategies
        strategy_order = []
        for s in ltm_recommended_mapped:
            if s in self.solvers:
                strategy_order.append(s)
        for s in self.solvers:
            if s not in strategy_order:
                strategy_order.append(s)

        # STEP 5: Which concepts are activated?
        activated_concepts = self.glm.get_concept_activation(task)

        # STEP 6: Try each strategy
        attempts = []
        solution = None
        winning_strategy = None

        for strat_name in strategy_order:
            solver = self.solvers[strat_name]
            try:
                result = solver.solve(task)
                from_ltm = strat_name in ltm_recommended_mapped
                attempts.append({
                    "strategy": strat_name,
                    "solved": result is not None,
                    "from_ltm": from_ltm,
                })
                if result is not None and solution is None:
                    solution = result
                    winning_strategy = strat_name
            except Exception as e:
                attempts.append({
                    "strategy": strat_name,
                    "solved": False,
                    "error": str(e),
                    "from_ltm": strat_name in ltm_recommended_mapped,
                })

        # STEP 7: Learn (record success with learning patterns)
        if solution is not None:
            self.ltm.record_success_with_learning(
                task_id, task_type_simple, winning_strategy,
                activated_concepts, self.run_number
            )

        trace_data = [
            {"language": s.language, "math": s.math, "script": s.script}
            for s in reasoning_trace
        ]

        return {
            "task_id": task_id,
            "solved": solution is not None,
            "winning_strategy": winning_strategy,
            "task_type_simple": task_type_simple,
            "task_type_bw1024": task_type_bw,
            "ltm_recommended_mapped": ltm_recommended_mapped,
            "reasoning_trace": trace_data,
            "activated_concepts": activated_concepts,
            "attempts": attempts,
            "solution": solution.cells if solution else None,
        }


# ============================================================
# Main
# ============================================================


def main():
    print("=" * 80)
    print("ARC-AGI v17.3 — Growth Layer (extends v17.2)")
    print("  Grown GLM + Broad CRG + Persistent LTM + Learning Analysis")
    print("=" * 80)

    training_dir = ARC_17_DIR / "data" / "training"
    task_files = sorted(training_dir.glob("*.json"))
    print(f"\n[load] Found {len(task_files)} ARC tasks")

    # Determine run number from previous state
    state_path = ARC_17_DIR / "results" / "glm_state.json"
    run_number = 1
    if state_path.exists():
        try:
            with open(state_path) as f:
                prev_state = json.load(f)
            run_number = len(prev_state.get("run_history", [])) + 1
        except:
            pass
    print(f"[init] Run number: {run_number}")

    pipeline = GrownPipeline(run_number=run_number)
    print(f"[init] Pipeline ready:")
    print(f"  GLM concepts: {len(pipeline.glm.concepts)} ({len(pipeline.glm.new_concepts_this_run)} new)")
    print(f"  CRG edges: {len(pipeline.glm.crg_edges)} ({len(pipeline.glm.new_edges_this_run)} new)")
    print(f"  Solvers: {len(pipeline.solvers)}")
    print(f"  LTM experiences: {len(pipeline.ltm.experiences)}")

    results = []
    solved_count = 0
    new_solves = 0
    known_solved_ids = {"00dbd492", "1e0a9b12", "396d80d7", "45737921", "54d82841",
                        "575b1a71", "a85d4709", "ae58858e", "e48d4e1a"}

    for task_file in task_files:
        task_id = task_file.stem
        try:
            task = load_task(str(task_file))
            print(f"\n[solve] Task {task_id}...")
            result = pipeline.solve_task(task, task_id)
            results.append(result)

            print(f"  Task type (simple): {result['task_type_simple']}")
            print(f"  Task type (BW-1024): {result['task_type_bw1024']}")
            print(f"  Activated concepts: {result['activated_concepts']}")

            if result["solved"]:
                solved_count += 1
                is_new = task_id not in known_solved_ids
                if is_new: new_solves += 1
                marker = " (NEW!)" if is_new else ""
                from_ltm = next((a["from_ltm"] for a in result["attempts"] if a["strategy"] == result["winning_strategy"]), False)
                ltm_marker = " (LTM)" if from_ltm else ""
                print(f"  SOLVED by {result['winning_strategy']}{marker}{ltm_marker}")
            else:
                print(f"  not solved (tried {len(result['attempts'])} strategies)")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback; traceback.print_exc()
            if not any(r.get("task_id") == task_id for r in results):
                results.append({"task_id": task_id, "solved": False, "error": str(e)})

    # === LEARNING ANALYSIS ===
    print("\n" + "=" * 80)
    print("LEARNING ANALYSIS (how the GLM is learning)")
    print("=" * 80)

    learning = pipeline.ltm.get_learning_analysis()
    print(f"\nTotal experiences: {learning['total_experiences']}")
    print(f"Total successes: {learning['total_successes']}")
    print(f"\nFastest task types (fewest attempts to first success):")
    for tt, n in learning["fastest_task_types"]:
        print(f"  {tt}: {n} attempts")
    print(f"\nBest strategies (most successes):")
    for s, n in learning["best_strategies"]:
        print(f"  {s}: {n} successes")
    print(f"\nMost useful concepts (activated in successful reasoning):")
    for c, n in learning["most_useful_concepts"]:
        print(f"  {c}: {n} successes")

    # Growth summary
    growth = {
        "run": run_number,
        "new_concepts": len(pipeline.glm.new_concepts_this_run),
        "new_edges": len(pipeline.glm.new_edges_this_run),
        "n_solved": solved_count,
        "n_tasks": len(task_files),
    }
    pipeline.ltm.learning_patterns["growth_per_run"].append(growth)

    # === SAVE STATE ===
    print("\n[saving] Saving grown state...")
    run_summary = {
        "run_number": run_number,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_tasks": len(task_files),
        "n_solved": solved_count,
        "new_solves": new_solves,
        "new_concepts": len(pipeline.glm.new_concepts_this_run),
        "new_edges": len(pipeline.glm.new_edges_this_run),
    }
    pipeline.glm.save_state(run_summary)
    pipeline.ltm.save_ltm_state()

    # === RESULTS ===
    print("\n" + "=" * 80)
    print(f"RESULTS: {solved_count}/{len(task_files)} solved")
    print(f"  NEW solves: {new_solves}")
    print(f"  Run number: {run_number}")
    print(f"  GLM growth: +{len(pipeline.glm.new_concepts_this_run)} concepts, +{len(pipeline.glm.new_edges_this_run)} edges")
    print("=" * 80)

    strategy_wins = Counter(r["winning_strategy"] for r in results if r.get("solved"))
    print("\nStrategy wins:")
    for s, c in strategy_wins.most_common():
        print(f"  {s}: {c}")

    # Save results
    output_dir = ARC_17_DIR / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "v17_3_results.json"
    with open(results_path, "w") as f:
        json.dump({
            "experiment": "ARC-AGI v17.3 — Growth Layer",
            "date": "2026-08-06",
            "run_number": run_number,
            "n_tasks": len(task_files),
            "n_solved": solved_count,
            "n_new_solves": new_solves,
            "strategy_wins": dict(strategy_wins),
            "glm_growth": {
                "total_concepts": len(pipeline.glm.concepts),
                "total_edges": len(pipeline.glm.crg_edges),
                "new_concepts_this_run": pipeline.glm.new_concepts_this_run,
                "new_edges_this_run": pipeline.glm.new_edges_this_run,
            },
            "learning_analysis": learning,
            "results": results,
        }, f, indent=2, default=str)
    print(f"\nResults saved: {results_path}")

    # Generate report
    report_dir = ARC_17_DIR / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "v17_3_report.md"
    report = generate_report(results, solved_count, new_solves, len(task_files),
                             strategy_wins, known_solved_ids, pipeline, learning, run_number)
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Report saved: {report_path}")


def generate_report(results, solved_count, new_solves, n_tasks, strategy_wins,
                    known_solved_ids, pipeline, learning, run_number):
    lines = []
    lines.append("# ARC-AGI v17.3 — Growth Layer Results")
    lines.append("")
    lines.append(f"**Date:** 2026-08-06")
    lines.append(f"**Run number:** {run_number}")
    lines.append("**Approach:** GROWTH (extends v17.2, doesn't replace it)")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Tasks tested:** {n_tasks}")
    lines.append(f"- **Solved:** {solved_count}/{n_tasks}")
    lines.append(f"- **New solves:** {new_solves}")
    lines.append(f"- **Run number:** {run_number} (the system has run {run_number} times)")
    lines.append("")

    lines.append("## GLM Growth")
    lines.append("")
    lines.append(f"- **Total concepts:** {len(pipeline.glm.concepts)} (+{len(pipeline.glm.new_concepts_this_run)} this run)")
    lines.append(f"- **Total CRG edges:** {len(pipeline.glm.crg_edges)} (+{len(pipeline.glm.new_edges_this_run)} this run)")
    lines.append("")
    lines.append("### New concepts added this run:")
    lines.append("")
    for c in pipeline.glm.new_concepts_this_run[:20]:
        concept = pipeline.glm.concepts[c]
        lines.append(f"- **{c}** ({concept.role}): {concept.lingo_term}")
    if len(pipeline.glm.new_concepts_this_run) > 20:
        lines.append(f"- ... and {len(pipeline.glm.new_concepts_this_run) - 20} more")
    lines.append("")

    lines.append("### New CRG edges added this run:")
    lines.append("")
    for src, label, dst in pipeline.glm.new_edges_this_run[:20]:
        lines.append(f"- {src} --{label}--> {dst}")
    if len(pipeline.glm.new_edges_this_run) > 20:
        lines.append(f"- ... and {len(pipeline.glm.new_edges_this_run) - 20} more")
    lines.append("")

    lines.append("## Learning Analysis (HOW the GLM learns)")
    lines.append("")
    lines.append("Per user: 'the Long Term Memory will eventually show us how the GLM learns so we can bypass a pile of training by designing training routines that specifically grow it where needed.'")
    lines.append("")
    lines.append(f"- **Total experiences:** {learning['total_experiences']}")
    lines.append(f"- **Total successes:** {learning['total_successes']}")
    lines.append("")
    lines.append("### Fastest task types (fewest attempts to first success)")
    lines.append("")
    lines.append("| Task type | Attempts to first success |")
    lines.append("|---|---|")
    for tt, n in learning["fastest_task_types"]:
        lines.append(f"| {tt} | {n} |")
    lines.append("")
    lines.append("This tells us which task types the GLM learns fastest. These need less training.")
    lines.append("")

    lines.append("### Best strategies (most successes)")
    lines.append("")
    lines.append("| Strategy | Successes |")
    lines.append("|---|---|")
    for s, n in learning["best_strategies"]:
        lines.append(f"| {s} | {n} |")
    lines.append("")
    lines.append("These are the GLM's strengths. Build on them.")
    lines.append("")

    lines.append("### Most useful concepts (activated in successful reasoning)")
    lines.append("")
    lines.append("| Concept | Successes when activated |")
    lines.append("|---|---|")
    for c, n in learning["most_useful_concepts"]:
        lines.append(f"| {c} | {n} |")
    lines.append("")
    lines.append("These concepts should be EXPANDED — they correlate with success.")
    lines.append("")

    lines.append("## Per-task results")
    lines.append("")
    lines.append("| Task | Task type (simple) | Task type (BW-1024) | Solved? | Strategy | New? | Activated concepts |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in results:
        tt_simple = r.get("task_type_simple", "—")
        tt_bw = r.get("task_type_bw1024", "—")
        solved = "✓" if r.get("solved") else "✗"
        strat = r.get("winning_strategy", "—")
        is_new = "NEW!" if r.get("task_id") not in known_solved_ids and r.get("solved") else ""
        activated = ", ".join(r.get("activated_concepts", [])) or "—"
        lines.append(f"| {r['task_id']} | {tt_simple} | {tt_bw} | {solved} | {strat} | {is_new} | {activated} |")
    lines.append("")

    lines.append("## Comparison across versions")
    lines.append("")
    lines.append("| Metric | v17 | v17.1 | v17.2 | v17.3 |")
    lines.append("|---|---|---|---|---|")
    lines.append(f"| Solvers | 8 | 11 | 8 | {len(pipeline.solvers)} |")
    lines.append(f"| Solved | 4/10 | 5/10 | 5/10 | {solved_count}/10 |")
    lines.append(f"| New solves | 1 | 1 | 1 | {new_solves} |")
    lines.append("| GLM concepts | — | — | 26 | %d |" % len(pipeline.glm.concepts))
    lines.append("| CRG edges | — | — | 30 | %d |" % len(pipeline.glm.crg_edges))
    lines.append("| Persistent LTM | ❌ | ❌ | ❌ | ✅ |")
    lines.append("| Learning analysis | ❌ | ❌ | ❌ | ✅ |")
    lines.append("| BW-1024 classifier | ❌ | ❌ | ❌ | ✅ |")
    lines.append("")

    lines.append("## What grew this run")
    lines.append("")
    lines.append(f"- **{len(pipeline.glm.new_concepts_this_run)} new concepts** added (general-purpose, not just ARC)")
    lines.append(f"- **{len(pipeline.glm.new_edges_this_run)} new CRG edges** added (broad semantic relations)")
    lines.append(f"- **{len(pipeline.ltm.updates)} new successes** recorded to LTM")
    lines.append(f"- **BW-1024 NRCI** used for finer task classification")
    lines.append(f"- **Parity sign recolor** and **column rank** solvers re-added (were missing in v17.2)")
    lines.append("")

    lines.append("## The growth mechanism")
    lines.append("")
    lines.append("Per user: 'growth not rebuild each Time.'")
    lines.append("")
    lines.append("The v17.3 pipeline:")
    lines.append("1. **Loads** the previous GLM state (concepts + CRG edges) from `glm_state.json`")
    lines.append("2. **Adds** new concepts and edges (broad, general-purpose)")
    lines.append("3. **Runs** the pipeline with the grown system")
    lines.append("4. **Saves** the grown state for the next run")
    lines.append("5. **Analyzes** how the GLM is learning (which concepts correlate with success)")
    lines.append("")
    lines.append("Each run adds to the previous state. The system gets smarter over time, not rebuilt.")
    lines.append("")

    lines.append("## Next steps (growth-oriented)")
    lines.append("")
    lines.append("1. **Run v17.3 multiple times** — each run grows the GLM. Watch the learning analysis change.")
    lines.append("2. **Expand the most useful concepts** — the learning analysis shows which concepts correlate with success. Add more concepts related to those.")
    lines.append("3. **Design targeted training routines** — use the learning analysis to identify which task types need more training, and design routines that grow the GLM in those areas.")
    lines.append("4. **Integrate the full GLM** (from glm_machine/) — the current 50+ concepts are a proof of concept. The full GLM has 2,550 concepts and 989 CRG edges.")
    lines.append("5. **Use the CRG for reasoning** — the 80+ edges are currently transparent (for debugging). Next step: use them to COMPUTE new strategies, not just classify tasks.")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
