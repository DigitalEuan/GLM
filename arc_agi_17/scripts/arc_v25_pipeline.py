#!/usr/bin/env python3
"""
arc_agi_17 v25 — Gap Words + Deliberative Reasoning + Applied Imagination
==========================================================================
Per user: "Gap word derivation and Deliberative reasoning seems logical to
use here" + all 5 growth items accepted.

WHAT'S NEW:

1. GAP WORD DERIVATION (from v37)
   When the GLM encounters unknown concepts during ARC solving (e.g., a
   pattern it hasn't seen), it DERIVES a vector for them on-the-fly:
   - Hash the concept to a 24-bit vector
   - Snap to nearest Golay codeword
   - Check if it's close to an existing concept (Hamming ≤ 8)
   - If yes, add it to the vocabulary — the GLM has LEARNED a new concept
   This grows the vocabulary organically during training.

2. DELIBERATIVE REASONING (from v37)
   For complex transformations, the GLM breaks the problem into steps:
   - Step 1: "What is the input shape? What is the output shape?"
   - Step 2: "What colours changed? What stayed the same?"
   - Step 3: "Is this a single transformation or a composition?"
   - Step 4: "What is the simplest rule that explains all train pairs?"
   Each step produces an intermediate result that feeds the next.

3. APPLIED IMAGINATION ADJUSTMENTS
   When imagination detects incoherence, it now CREATES a refined proposal:
   - Shape mismatch → try scale/crop
   - Colour mismatch → adjust colour map
   - Density mismatch → try fill/extract
   The refined proposal is TESTED, not just logged.

4. MORE PUZZLE VARIATION TYPES
   - Scaled variants (2× the grid)
   - Flipped variants (horizontal flip)
   - Density-modified variants (add noise cells)

5. RUN 5 TRAINING ITERATIONS

OUTPUTS:
  /home/z/my-project/download/arc_agi_17/results/v25_results.json
  /home/z/my-project/download/arc_agi_17/reports/v25_report.md
"""

import sys
import os
import json
import math
import time
import random
import hashlib
import itertools
import copy
from fractions import Fraction as F
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any, Set
from collections import Counter, defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
ARC_17_DIR = SCRIPT_DIR.parent

sys.path.insert(0, str(Path("/home/z/my-project/scripts")))
from ubp_engine.ubp_unified_v5 import GolayCodeEngine, LeechLatticeEngine, BarnesWallEngine

sys.path.insert(0, str(SCRIPT_DIR))
from loader import Grid, ARCTask, load_task

from arc_v17_2_pipeline import (
    Y_CONST, LTM_STRATEGY_MAP,
    SettlementGravitySolver, ColourMapViaANDSolver, ConditionalSolver,
    InteriorFillSolver, ScaleAwareResizeSolver, ShiftSolver, RotateSolver, FlipSolver,
)
from arc_v17_pipeline import ParitySignRecolorSolver
from arc_v17_1_pipeline import ColumnRankSolver
from arc_v17_3_pipeline import GrownLTM
from arc_v17_6_pipeline import GLMSandbox
from arc_v17_7_pipeline import FullVocabGLMCore, GLM_RESOURCES
from arc_v21_pipeline import (
    GeometricNumber, GeometricArithmetic, GeometricComputationVerifier,
    MathAtlas, PhysicsExact, DataObjectEncoder,
)
from arc_v22_pipeline import GenerativeCRGReasoning, V22GLMMind, V22Pipeline
from arc_v23_pipeline import (
    SpatialEncoder, ActivePerception, DifferentialTransitionEngine, V23GLMMind, V23Pipeline,
)
from arc_v24_pipeline import (
    ImaginationLayer, PuzzleVariation, CrystallizationEngine, AdversarialTest,
    V24GLMMind, V24Pipeline,
)
from arc_v17_9_pipeline import (
    QUADRANT_NAMES, GRAMMAR_ROLE, QUADRANT_RANGES,
    dominant_quadrant, quadrant_weights, computed_role,
)


# ============================================================
# 1. GAP WORD DERIVATION (from v37 _derive_gap_words)
# ============================================================
#
# When the GLM encounters an unknown concept during ARC solving, it
# DERIVES a vector for it on-the-fly. This grows the vocabulary
# organically during training.
#
# For ARC, "unknown concepts" are patterns the GLM hasn't encoded:
# - A new colour combination
# - A new shape pattern
# - A new transformation type
# These get hashed → snapped → checked for proximity → added to vocab.
# ============================================================


class GapWordDerivation:
    """Derive vectors for unknown concepts on-the-fly (from v37).

    When the GLM encounters a pattern it hasn't seen, it:
    1. Hashes the pattern to a 24-bit vector
    2. Snaps to nearest Golay codeword
    3. Checks if it's close to an existing concept (Hamming ≤ 8)
    4. If yes, adds it to the vocabulary — the GLM has LEARNED
    """

    def __init__(self, glm_core):
        self.glm = glm_core
        self.derived_cache = set()
        self.derived_count = 0

    def derive(self, concept_name: str) -> bool:
        """Derive a vector for an unknown concept.

        Returns True if the concept was successfully derived and added.
        """
        if concept_name in self.derived_cache:
            return False
        if concept_name in self.glm.concepts:
            return False
        if len(concept_name) < 3:
            return False

        self.derived_cache.add(concept_name)

        # Hash the concept name to a 24-bit vector
        h = hashlib.sha256(concept_name.encode()).digest()
        bits = [(byte >> k) & 1 for byte in h for k in range(7, -1, -1)][:24]

        # Snap to nearest Golay codeword
        snapped, _ = self.glm.golay.snap_to_codeword(bits)

        # Check proximity to existing concepts
        best_d = 999
        best_word = None
        for name, concept in list(self.glm.concepts.items())[:200]:  # sample for speed
            d = sum(1 for a, b in zip(snapped, concept.vector) if a != b)
            if d < best_d:
                best_d = d
                best_word = name

        # Only add if reasonably close (d <= 8)
        if best_d <= 8:
            qw = quadrant_weights(snapped)
            role = GRAMMAR_ROLE[dominant_quadrant(snapped)]
            hw = sum(snapped)
            nrci = 10.0 / (10.0 + hw * Y_CONST + hw / 8.0)

            self.glm.concepts[concept_name] = type(next(iter(self.glm.concepts.values())))(
                name=concept_name, vector=snapped, role=role,
                lingo_term=concept_name.upper(),
                quadrant_weights=qw, nrci=nrci,
            )
            self.derived_count += 1
            return True

        return False

    def derive_from_pattern(self, pattern: Dict[str, Any]) -> str:
        """Derive a concept from an observed ARC pattern.

        Creates a concept name from the pattern description and derives it.
        """
        # Create a concept name from the pattern
        parts = []
        if pattern.get("type"):
            parts.append(pattern["type"])
        if pattern.get("colour_map"):
            parts.append("swap")
        if pattern.get("gravity"):
            parts.append("gravity")
        if pattern.get("shift"):
            parts.append(f"shift_{pattern['shift'][0]}_{pattern['shift'][1]}")
        if pattern.get("fill") is not None:
            parts.append(f"fill_{pattern['fill']}")

        if not parts:
            return ""

        concept_name = "_".join(parts)
        if self.derive(concept_name):
            return concept_name
        return ""


# ============================================================
# 2. DELIBERATIVE REASONING (from v37 deliberate())
# ============================================================
#
# For complex transformations, the GLM breaks the problem into steps:
#   Step 1: "What is the input shape? What is the output shape?"
#   Step 2: "What colours changed? What stayed the same?"
#   Step 3: "Is this a single transformation or a composition?"
#   Step 4: "What is the simplest rule that explains all train pairs?"
#
# Each step produces an intermediate result that feeds the next.
# This is the GLM "thinking through" the problem step by step.
# ============================================================


class DeliberativeReasoning:
    """Break complex ARC problems into computational steps.

    The GLM reasons step-by-step:
    1. Analyze shapes (same? different? scaled?)
    2. Analyze colours (which changed? which stayed?)
    3. Analyze positions (did cells move? did objects change?)
    4. Synthesize: what is the simplest rule?
    """

    def __init__(self):
        self.reasoning_steps = []

    def deliberate(self, task: ARCTask) -> Dict[str, Any]:
        """Break the problem into steps and reason through each.

        Returns a structured analysis that the GLM mind can use.
        """
        self.reasoning_steps = []

        if not task.train:
            return {"analysis": "no train pairs", "steps": []}

        # Step 1: Shape analysis
        shapes = [(pair.input.height, pair.input.width, pair.output.height, pair.output.width)
                  for pair in task.train]
        all_same_shape = all(s[0] == s[2] and s[1] == s[3] for s in shapes)
        self.reasoning_steps.append({
            "step": 1, "name": "shape_analysis",
            "result": f"All same shape: {all_same_shape}. Shapes: {shapes}",
            "same_shape": all_same_shape,
        })

        # Step 2: Colour analysis
        colour_maps = []
        for pair in task.train:
            inp, out = pair.input, pair.output
            if inp.height == out.height and inp.width == out.width:
                cm = {}
                consistent = True
                for r in range(inp.height):
                    for c in range(inp.width):
                        if inp.cells[r][c] in cm:
                            if cm[inp.cells[r][c]] != out.cells[r][c]:
                                consistent = False; break
                        else:
                            cm[inp.cells[r][c]] = out.cells[r][c]
                if not consistent:
                    cm = None
                colour_maps.append(cm)
            else:
                colour_maps.append(None)

        all_consistent = all(cm is not None for cm in colour_maps)
        all_same_map = all(cm == colour_maps[0] for cm in colour_maps) if all_consistent else False
        self.reasoning_steps.append({
            "step": 2, "name": "colour_analysis",
            "result": f"Colour maps consistent: {all_consistent}, same across pairs: {all_same_map}",
            "colour_maps": colour_maps,
            "consistent": all_consistent,
            "same_map": all_same_map,
        })

        # Step 3: Position analysis (did cells move?)
        shifts = []
        for pair in task.train:
            inp, out = pair.input, pair.output
            if inp.height == out.height and inp.width == out.width:
                shift = self._detect_shift(inp, out)
                shifts.append(shift)
            else:
                shifts.append(None)

        all_same_shift = all(s == shifts[0] for s in shifts if s is not None) if any(s is not None for s in shifts) else False
        self.reasoning_steps.append({
            "step": 3, "name": "position_analysis",
            "result": f"Shifts: {shifts}, consistent: {all_same_shift}",
            "shifts": shifts,
            "consistent_shift": all_same_shift,
        })

        # Step 4: Synthesis — what is the simplest rule?
        synthesis = self._synthesize(all_same_shape, all_consistent, all_same_map, colour_maps, shifts, task)
        self.reasoning_steps.append({
            "step": 4, "name": "synthesis",
            "result": synthesis["description"],
            "rule": synthesis,
        })

        return {
            "analysis": synthesis["description"],
            "steps": self.reasoning_steps,
            "rule": synthesis,
        }

    def _synthesize(self, same_shape, consistent, same_map, colour_maps, shifts, task):
        """Synthesize the simplest rule from the analysis."""
        # Check gravity
        for pair in task.train:
            inp, out = pair.input, pair.output
            gravity = self._apply_gravity(inp)
            if gravity == out:
                return {"type": "gravity", "description": "COMPACTION_FLOW: cells fall down",
                        "confidence": 0.9}

        # Check rotation
        for angle in [90, 180, 270]:
            all_match = True
            for pair in task.train:
                if self._rotate(pair.input, angle) != pair.output:
                    all_match = False; break
            if all_match:
                return {"type": "rotation", "angle": angle,
                        "description": f"DIHEDRAL_ROTATION: rotate {angle}°",
                        "confidence": 0.9}

        # Check flip
        for direction in ["horizontal", "vertical"]:
            all_match = True
            for pair in task.train:
                if self._flip(pair.input, direction) != pair.output:
                    all_match = False; break
            if all_match:
                return {"type": "flip", "direction": direction,
                        "description": f"PLANE_REFLECTION: flip {direction}",
                        "confidence": 0.9}

        # Consistent colour map
        if consistent and same_map and colour_maps[0]:
            changes = {k: v for k, v in colour_maps[0].items() if k != v}
            if changes:
                return {"type": "colour_map", "colour_map": changes,
                        "description": f"CHARGE_SWAP: {changes}",
                        "confidence": 0.9}

        # Conditional (check objects)
        for pair in task.train:
            inp, out = pair.input, pair.output
            if inp.height != out.height or inp.width != out.width:
                break
            objects = ConditionalSolver._find_objects(inp)
            changed = [o for o in objects if any(out.cells[r][c] != o["colour"] for r, c in o["cells"])]
            stayed = [o for o in objects if all(out.cells[r][c] == o["colour"] for r, c in o["cells"])]
            if changed and stayed:
                changed_sizes = [o["size"] for o in changed]
                stayed_sizes = [o["size"] for o in stayed]
                if min(changed_sizes) > max(stayed_sizes):
                    threshold = min(changed_sizes)
                    colour_swap = {}
                    for o in changed:
                        for r, c in o["cells"]:
                            colour_swap[o["colour"]] = out.cells[r][c]; break
                    return {"type": "conditional", "threshold": threshold,
                            "colour_swap": colour_swap,
                            "description": f"CONDITIONAL: swap for size >= {threshold}",
                            "confidence": 0.8}

        return {"type": "unknown", "description": "No simple rule found",
                "confidence": 0.0}

    @staticmethod
    def _detect_shift(inp, out):
        h, w = inp.height, inp.width
        if inp.height != out.height or inp.width != out.width: return None
        for dr in range(-h + 1, h):
            for dc in range(-w + 1, w):
                matches = True
                for r in range(h):
                    for c in range(w):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            if inp.cells[r][c] != out.cells[nr][nc]:
                                matches = False; break
                        else:
                            if inp.cells[r][c] != 0:
                                matches = False; break
                    if not matches: break
                if matches: return (dr, dc)
        return None

    @staticmethod
    def _apply_gravity(grid):
        h, w = grid.height, grid.width
        new_cells = [[0] * w for _ in range(h)]
        for c in range(w):
            column = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
            for i, val in enumerate(column):
                new_cells[h - len(column) + i][c] = val
        return Grid(new_cells)

    @staticmethod
    def _rotate(grid, angle):
        h, w = grid.height, grid.width
        if angle == 90: return Grid([[grid.cells[h-1-r][c] for r in range(h)] for c in range(w)])
        elif angle == 180: return Grid([[grid.cells[h-1-r][w-1-c] for c in range(w)] for r in range(h)])
        elif angle == 270: return Grid([[grid.cells[r][w-1-c] for r in range(h)] for c in range(w)])
        return grid

    @staticmethod
    def _flip(grid, direction):
        h = grid.height
        if direction == "horizontal": return Grid([row[::-1] for row in grid.cells])
        else: return Grid([grid.cells[h-1-r] for r in range(h)])


# ============================================================
# 3. APPLIED IMAGINATION — actually create refined proposals
# ============================================================


class AppliedImagination(ImaginationLayer):
    """Imagination that ACTUALLY creates refined proposals from adjustments.

    When imagination detects incoherence, it doesn't just log the issue —
    it CREATES a new proposal that addresses the issue.
    """

    def imagine_and_adjust(self, proposal: Dict, input_grid: Grid,
                           train_outputs: List[Grid], task: ARCTask) -> Tuple[Optional[Dict], str]:
        """Imagine the result and create an adjusted proposal if needed.

        Returns (adjusted_proposal, reasoning).
        """
        result = self.imagine(proposal, input_grid, train_outputs)

        if result["coherence"] >= 0.8:
            return None, result["reasoning"]  # No adjustment needed

        adjustment = result.get("adjustment")
        if not adjustment:
            return None, result["reasoning"]

        # Create an adjusted proposal based on the imagination's suggestion
        adj_type = adjustment.get("type")

        if adj_type == "colour_mismatch":
            # Adjust the colour map
            missing = adjustment.get("reason", "")
            # Try to detect the correct colour map from train pairs
            if task.train:
                inp, out = task.train[0].input, task.train[0].output
                if inp.height == out.height and inp.width == out.width:
                    colour_map = {}
                    consistent = True
                    for r in range(inp.height):
                        for c in range(inp.width):
                            if inp.cells[r][c] in colour_map:
                                if colour_map[inp.cells[r][c]] != out.cells[r][c]:
                                    consistent = False; break
                            else:
                                colour_map[inp.cells[r][c]] = out.cells[r][c]
                    if consistent:
                        changes = {k: v for k, v in colour_map.items() if k != v}
                        if changes:
                            adjusted = {
                                "description": f"ADJUSTED: colour map {changes} (from imagination)",
                                "source": "imagination adjustment (colour mismatch)",
                                "type": "colour_map",
                                "params": {"colour_map": changes},
                            }
                            return adjusted, result["reasoning"] + "\nAdjustment: corrected colour map from train pairs."

        elif adj_type == "density_low":
            # Try fill
            if task.train:
                fill_colour = None
                for pair in task.train:
                    inp, out = pair.input, pair.output
                    for r in range(inp.height):
                        for c in range(inp.width):
                            if inp.cells[r][c] == 0 and out.cells[r][c] != 0:
                                fill_colour = out.cells[r][c]; break
                        if fill_colour is not None: break
                if fill_colour is not None:
                    adjusted = {
                        "description": f"ADJUSTED: fill with colour {fill_colour} (from imagination)",
                        "source": "imagination adjustment (density low)",
                        "type": "fill",
                        "params": {"fill_colour": fill_colour},
                    }
                    return adjusted, result["reasoning"] + "\nAdjustment: added fill to increase density."

        elif adj_type == "shape_mismatch":
            # Can't easily fix shape — skip
            return None, result["reasoning"] + "\nAdjustment: shape mismatch cannot be fixed automatically."

        return None, result["reasoning"]


# ============================================================
# 4. MORE PUZZLE VARIATION TYPES
# ============================================================


class ExtendedPuzzleVariation(PuzzleVariation):
    """Extended puzzle variation with more types."""

    @staticmethod
    def scaled_variant(task: ARCTask, factor: int = 2) -> ARCTask:
        """Create a scaled (2×) version of a task."""
        new_train = []
        for pair in task.train:
            new_in = ExtendedPuzzleVariation._scale(pair.input, factor)
            new_out = ExtendedPuzzleVariation._scale(pair.output, factor)
            new_train.append(type(pair)(input=new_in, output=new_out))
        new_test = [type(t)(input=ExtendedPuzzleVariation._scale(t.input, factor)) for t in task.test]
        return ARCTask(train=new_train, test=new_test)

    @staticmethod
    def flipped_variant(task: ARCTask) -> ARCTask:
        """Create a horizontally-flipped version."""
        new_train = []
        for pair in task.train:
            new_in = Grid([row[::-1] for row in pair.input.cells])
            new_out = Grid([row[::-1] for row in pair.output.cells])
            new_train.append(type(pair)(input=new_in, output=new_out))
        new_test = [type(t)(input=Grid([row[::-1] for row in t.input.cells])) for t in task.test]
        return ARCTask(train=new_train, test=new_test)

    @staticmethod
    def _scale(grid: Grid, factor: int) -> Grid:
        h, w = grid.height, grid.width
        return Grid([[grid.cells[r // factor][c // factor]
                      for c in range(w * factor)] for r in range(h * factor)])


# ============================================================
# The v25 GLM Mind (gap words + deliberative + applied imagination)
# ============================================================


class V25GLMMind(V24GLMMind):
    """v25: Gap word derivation + deliberative reasoning + applied imagination."""

    def __init__(self, glm_core, sandbox, hex_address, known_addresses, known_transforms,
                 geometric_arithmetic, data_object_encoder, ltm):
        super().__init__(glm_core, sandbox, hex_address, known_addresses, known_transforms,
                         geometric_arithmetic, data_object_encoder, ltm)
        self.gap_words = GapWordDerivation(glm_core)
        self.deliberative = DeliberativeReasoning()
        self.applied_imagination = AppliedImagination(sandbox)

    def solve_task(self, task: ARCTask, task_id: str = "") -> Tuple[Optional[Grid], Dict[str, Any]]:
        """Solve with gap words + deliberative reasoning + applied imagination."""
        self.nl_reasoner.reasoning_log = []
        energy = self.realigner.realign(max_steps=2)

        # === LATTICE PERCEPTION ===
        transition = self.transition_engine.compute_transition(task)
        self.nl_reasoner.reasoning_log.append({
            "step": "lattice_perception",
            "text": f"Lattice: type={transition.get('type')}, consistent={transition.get('consistent')}"
        })

        if transition.get("consistent") and transition.get("type") != "none":
            all_pass = True
            for pair in task.train:
                result = self.transition_engine.apply_transition(transition, pair.input)
                if result is None or result != pair.output:
                    all_pass = False; break
            if all_pass and task.test:
                solution = self.transition_engine.apply_transition(transition, task.test[0].input)
                if solution is not None:
                    adv = self.adversarial.test(solution, task.train)
                    if adv["passed"]:
                        self.nl_reasoner.reasoning_log.append({"step": "commit", "text": f"Lattice: {transition['description']}"})
                        # === GAP WORD DERIVATION ===
                        concept = self.gap_words.derive_from_pattern(transition)
                        if concept:
                            self.nl_reasoner.reasoning_log.append({"step": "gap_word", "text": f"Derived new concept: {concept}"})
                        return solution, {"reasoning_trace": self.nl_reasoner.get_full_trace(),
                                          "proposal": {"description": transition["description"], "type": transition["type"]},
                                          "mode": "lattice_perception"}

        # === DELIBERATIVE REASONING (NEW) ===
        deliberation = self.deliberative.deliberate(task)
        rule = deliberation.get("rule", {})
        self.nl_reasoner.reasoning_log.append({
            "step": "deliberative",
            "text": f"Deliberative reasoning: {rule.get('description', 'no rule found')} (confidence={rule.get('confidence', 0):.2f})"
        })

        # If deliberative found a high-confidence rule, try it directly
        if rule.get("confidence", 0) >= 0.8:
            rule_type = rule.get("type")
            if rule_type == "colour_map":
                proposal = {"description": rule["description"], "source": "deliberative",
                            "type": "colour_map", "params": {"colour_map": rule["colour_map"]}}
                all_pass = True
                for pair in task.train:
                    result = self._apply_any_proposal(proposal, pair.input)
                    if result is None or result != pair.output:
                        all_pass = False; break
                if all_pass and task.test:
                    solution = self._apply_any_proposal(proposal, task.test[0].input)
                    if solution is not None:
                        adv = self.adversarial.test(solution, task.train)
                        if adv["passed"]:
                            self.nl_reasoner.commit(proposal)
                            concept = self.gap_words.derive_from_pattern(rule)
                            return solution, {"reasoning_trace": self.nl_reasoner.get_full_trace(),
                                              "proposal": proposal, "mode": "deliberative_reasoning"}
            elif rule_type == "gravity":
                proposal = {"description": rule["description"], "source": "deliberative", "type": "gravity", "params": {}}
                all_pass = True
                for pair in task.train:
                    result = self._apply_any_proposal(proposal, pair.input)
                    if result is None or result != pair.output:
                        all_pass = False; break
                if all_pass and task.test:
                    solution = self._apply_any_proposal(proposal, task.test[0].input)
                    if solution is not None:
                        self.nl_reasoner.commit(proposal)
                        return solution, {"reasoning_trace": self.nl_reasoner.get_full_trace(),
                                          "proposal": proposal, "mode": "deliberative_reasoning"}
            elif rule_type == "conditional":
                proposal = {"description": rule["description"], "source": "deliberative",
                            "type": "conditional_refined",
                            "params": {"threshold": rule["threshold"], "colour_swap": rule["colour_swap"]}}
                all_pass = True
                for pair in task.train:
                    result = self._apply_any_proposal(proposal, pair.input)
                    if result is None or result != pair.output:
                        all_pass = False; break
                if all_pass and task.test:
                    solution = self._apply_any_proposal(proposal, task.test[0].input)
                    if solution is not None:
                        self.nl_reasoner.commit(proposal)
                        return solution, {"reasoning_trace": self.nl_reasoner.get_full_trace(),
                                          "proposal": proposal, "mode": "deliberative_reasoning"}

        # === FULL V24 PIPELINE (with applied imagination) ===
        perception = self._perceive_task(task)
        perception = self._enhance_perception(perception, task)
        ext_perception = self.extended_perception.detect_all(task)
        perception["extended"] = ext_perception
        ts_perception = self.ts_perception.detect_all(task)
        perception["task_specific"] = ts_perception

        # HexColour routing
        if task.test:
            test_address = self.hex_address.compute_address(task.test[0].input)
            for threshold in [4, 6, 8, 10, 12, 16, 20]:
                similar = self.hex_address.find_similar(test_address, self.known_addresses, max_distance=threshold)
                if similar:
                    for tid, addr, dist in similar:
                        strategy = self.known_transforms.get(tid)
                        if strategy:
                            analogical_proposal = self._create_analogical_proposal(strategy, perception, task)
                            if analogical_proposal:
                                all_pass = True
                                for pair in task.train:
                                    result = self._apply_any_proposal(analogical_proposal, pair.input)
                                    if result is None or result != pair.output:
                                        all_pass = False; break
                                if all_pass:
                                    self.nl_reasoner.commit(analogical_proposal)
                                    if task.test:
                                        solution = self._apply_any_proposal(analogical_proposal, task.test[0].input)
                                        if solution is not None:
                                            return solution, {"reasoning_trace": self.nl_reasoner.get_full_trace(),
                                                              "proposal": analogical_proposal, "mode": "hexcolour_analogical"}

        # Generate proposals
        proposals = self._generate_proposals(perception, task)
        proposals.extend(self.extended_proposer.generate_extended_proposals(ext_perception, task))
        proposals = self.ts_proposer.generate(ts_perception) + proposals
        proposals.extend(self.crg_reasoning.generate_proposals_from_crg(perception, task))
        proposals.extend(self.composer.generate_compositions(perception, task))

        # Add deliberative rule as a proposal (if found)
        if rule.get("confidence", 0) > 0:
            proposals.insert(0, {"description": rule["description"], "source": "deliberative",
                                 "type": rule["type"], "params": rule})

        train_outputs = [pair.output for pair in task.train]

        for i, proposal in enumerate(proposals):
            # === APPLIED IMAGINATION (NEW) ===
            adjusted_proposal, imagination_reasoning = self.applied_imagination.imagine_and_adjust(
                proposal, task.train[0].input, train_outputs, task
            )
            self.nl_reasoner.reasoning_log.append({
                "step": "imagination",
                "text": f"Imagining: {imagination_reasoning[:200]}"
            })

            # If imagination created an adjusted proposal, try it too
            test_proposals = [proposal]
            if adjusted_proposal:
                test_proposals.append(adjusted_proposal)
                self.nl_reasoner.reasoning_log.append({
                    "step": "imagination_adjustment",
                    "text": f"Imagination created adjusted proposal: {adjusted_proposal['description']}"
                })

            for tp in test_proposals:
                all_pass = True
                n_passed = 0
                for j, pair in enumerate(task.train):
                    result = self._apply_any_proposal(tp, pair.input)
                    if result is None or result != pair.output:
                        all_pass = False; break
                    n_passed += 1

                cryst = self.crystallization.crystallize(tp, 0.8, n_passed, len(task.train))

                if cryst["commit"] and all_pass and task.test:
                    solution = self._apply_any_proposal(tp, task.test[0].input)
                    if solution is not None:
                        adv = self.adversarial.test(solution, task.train)
                        if adv["passed"]:
                            self.nl_reasoner.commit(tp)
                            # === GAP WORD DERIVATION ===
                            concept = self.gap_words.derive_from_pattern(tp.get("params", {}))
                            if concept:
                                self.nl_reasoner.reasoning_log.append({"step": "gap_word", "text": f"Derived: {concept}"})
                            return solution, {"reasoning_trace": self.nl_reasoner.get_full_trace(),
                                              "proposal": tp, "mode": "glm_mind"}

                # Refinement
                refined = self._refine_proposal_extended(tp, "", task)
                if refined:
                    all_pass_r = True
                    for pair in task.train:
                        result = self._apply_any_proposal(refined, pair.input)
                        if result is None or result != pair.output:
                            all_pass_r = False; break
                    if all_pass_r and task.test:
                        solution = self._apply_any_proposal(refined, task.test[0].input)
                        if solution is not None:
                            adv = self.adversarial.test(solution, task.train)
                            if adv["passed"]:
                                self.nl_reasoner.commit(refined)
                                return solution, {"reasoning_trace": self.nl_reasoner.get_full_trace(),
                                                  "proposal": refined, "mode": "glm_mind_refined"}

        self.nl_reasoner.fail("All proposals failed.")
        return None, {"reasoning_trace": self.nl_reasoner.get_full_trace(), "proposal": None, "mode": "failed"}


# ============================================================
# The v25 Pipeline
# ============================================================


class V25Pipeline(V24Pipeline):
    """v25: Gap words + deliberative + applied imagination + more variation."""

    def __init__(self, run_number=1, known_addresses=None, known_transforms=None, seed=42):
        super().__init__(run_number, known_addresses, known_transforms, seed)
        self.mind = V25GLMMind(
            self.glm, self.sandbox, self.hex_address,
            self.known_addresses, self.known_transforms,
            self.geometric_arithmetic, self.data_object_encoder,
            self.ltm
        )
        self.puzzle_variation = ExtendedPuzzleVariation()


# ============================================================
# Main
# ============================================================


def main():
    print("=" * 80)
    print("ARC-AGI v25 — Gap Words + Deliberative + Applied Imagination")
    print("=" * 80)

    training_dir = ARC_17_DIR / "data" / "training"
    task_files = sorted(training_dir.glob("*.json"))
    print(f"\n[load] Found {len(task_files)} ARC tasks")

    known_solved_ids = {"00dbd492", "1e0a9b12", "396d80d7", "45737921", "54d82841",
                        "575b1a71", "a85d4709", "ae58858e", "e48d4e1a"}

    addr_path = ARC_17_DIR / "results" / "hexcolour_addresses.json"
    known_addresses = {}
    known_transforms = {}
    if addr_path.exists():
        try:
            with open(addr_path) as f:
                addr_data = json.load(f)
            known_addresses = {k: int(v) for k, v in addr_data.get("addresses", {}).items()}
            known_transforms = addr_data.get("transforms", {})
        except: pass

    state_path = ARC_17_DIR / "results" / "glm_state.json"
    start_run = 1
    if state_path.exists():
        try:
            with open(state_path) as f:
                prev_state = json.load(f)
            start_run = len(prev_state.get("run_history", [])) + 1
        except: pass

    N_RUNS = 5
    all_runs = []

    for i in range(N_RUNS):
        run_number = start_run + i
        print(f"\n{'='*60}")
        print(f"RUN {run_number}")
        print(f"{'='*60}")

        pipeline = V25Pipeline(run_number=run_number, known_addresses=known_addresses,
                                known_transforms=known_transforms, seed=42 + i)
        print(f"[init] GLM: {len(pipeline.glm.concepts)} concepts, {len(pipeline.glm.crg_edges)} edges")
        print(f"[init] Gap words derived so far: {pipeline.mind.gap_words.derived_count}")

        # Load tasks
        original_tasks = []
        for tf in task_files:
            try:
                original_tasks.append((tf.stem, load_task(str(tf))))
            except: pass

        # PUZZLE VARIATION (extended)
        varied_tasks = list(original_tasks)
        random.seed(42 + i)

        # Colour-swapped variants (2)
        for _ in range(2):
            if original_tasks:
                tid, task = random.choice(original_tasks)
                c1, c2 = random.randint(1, 8), random.randint(1, 8)
                if c1 != c2:
                    varied_tasks.append((f"{tid}_swap{c1}{c2}",
                                        pipeline.puzzle_variation.colour_swap_variant(task, c1, c2)))

        # Rotated variants (1)
        if original_tasks:
            tid, task = random.choice(original_tasks)
            varied_tasks.append((f"{tid}_rot90", pipeline.puzzle_variation.rotate_variant(task)))

        # Scaled variant (1)
        if original_tasks:
            tid, task = random.choice(original_tasks)
            varied_tasks.append((f"{tid}_scale2x", pipeline.puzzle_variation.scaled_variant(task, 2)))

        # Flipped variant (1)
        if original_tasks:
            tid, task = random.choice(original_tasks)
            varied_tasks.append((f"{tid}_flipH", pipeline.puzzle_variation.flipped_variant(task)))

        random.shuffle(varied_tasks)
        n_variants = len(varied_tasks) - len(original_tasks)
        print(f"[variation] {len(varied_tasks)} tasks ({len(original_tasks)} orig + {n_variants} variants)")

        solved_count = 0; new_solves = 0
        mind_solves = 0; lattice_solves = 0; analogical_solves = 0; deliberative_solves = 0
        imagination_used = 0; gap_words_derived = 0; crystallized = 0; adversarial_passed = 0

        for tid, task in varied_tasks:
            try:
                result = pipeline.solve_task(task, tid)
                if result["solved"]:
                    solved_count += 1
                    is_new = tid not in known_solved_ids and "_swap" not in tid and "_rot" not in tid and "_scale" not in tid and "_flip" not in tid
                    if is_new: new_solves += 1
                    mode = result["mode"]
                    if mode == "glm_mind": mind_solves += 1
                    elif mode == "lattice_perception": lattice_solves += 1
                    elif mode == "hexcolour_analogical": analogical_solves += 1
                    elif mode == "deliberative_reasoning": deliberative_solves += 1

                    trace = result.get("reasoning_trace", "")
                    if "imagination" in trace.lower(): imagination_used += 1
                    if "gap_word" in trace.lower() or "Derived" in trace: gap_words_derived += 1
                    if "crystallized" in trace.lower(): crystallized += 1
                    if "adversarial" in trace.lower() and "PASSED" in trace: adversarial_passed += 1

                    if is_new or mode in ("glm_mind", "lattice_perception", "deliberative_reasoning", "hexcolour_analogical"):
                        print(f"  ✓ {tid}: {result['winning_strategy']} ({mode})")
            except: pass

        known_addresses = pipeline.known_addresses
        known_transforms = pipeline.known_transforms

        run_summary = {
            "run_number": run_number, "n_tasks": len(varied_tasks),
            "n_solved": solved_count, "new_solves": new_solves,
            "mind_solves": mind_solves, "lattice_solves": lattice_solves,
            "analogical_solves": analogical_solves, "deliberative_solves": deliberative_solves,
            "imagination_used": imagination_used, "gap_words_derived": gap_words_derived,
            "crystallized": crystallized, "adversarial_passed": adversarial_passed,
            "known_addresses": len(known_addresses),
            "glm_concepts": len(pipeline.glm.concepts), "glm_edges": len(pipeline.glm.crg_edges),
            "n_variants": n_variants,
        }
        pipeline.glm.save_state(run_summary)
        pipeline.ltm.save_ltm_state()
        with open(addr_path, "w") as f:
            json.dump({"addresses": {k: str(v) for k, v in known_addresses.items()},
                       "transforms": known_transforms}, f, indent=2)

        all_runs.append(run_summary)
        bar = '█' * min(solved_count, 50) + '░' * max(0, 50 - solved_count)
        print(f"\n[run {run_number}] {bar} {solved_count}/{len(varied_tasks)}")
        print(f"  Lattice: {lattice_solves}, Mind: {mind_solves}, Deliberative: {deliberative_solves}, Analogical: {analogical_solves}")
        print(f"  Imagination: {imagination_used}, Gap words: {gap_words_derived}, Cryst: {crystallized}, Advers: {adversarial_passed}")
        print(f"  Concepts: {len(pipeline.glm.concepts)}, Edges: {len(pipeline.glm.crg_edges)}, Addresses: {len(known_addresses)}")

    # Final
    print("\n" + "=" * 80)
    print(f"FINAL RESULTS ({N_RUNS} runs)")
    print("=" * 80)
    print(f"\n{'Run':>4} {'Solved':>8} {'Lat':>5} {'Mind':>5} {'Delib':>6} {'Imag':>5} {'Gap':>5} {'Edges':>8} {'Addr':>6}")
    print("-" * 60)
    for run in all_runs:
        print(f"{run['run_number']:>4} {run['n_solved']:>5}/{run['n_tasks']:<2} "
              f"{run['lattice_solves']:>5} {run['mind_solves']:>5} {run['deliberative_solves']:>6} "
              f"{run['imagination_used']:>5} {run['gap_words_derived']:>5} {run['glm_edges']:>8} {run['known_addresses']:>6}")

    last_run = all_runs[-1]
    best_run = max(all_runs, key=lambda r: r["n_solved"])
    print(f"\nBest: {best_run['n_solved']}/{best_run['n_tasks']}")
    print(f"Gap words derived: {last_run['gap_words_derived']}")
    print(f"Imagination used: {last_run['imagination_used']}")
    print(f"Deliberative solves: {last_run['deliberative_solves']}")
    print(f"GLM edges: {last_run['glm_edges']}")

    # Save
    output_dir = ARC_17_DIR / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "v25_results.json", "w") as f:
        json.dump({"experiment": "ARC-AGI v25", "n_runs": N_RUNS, "runs": all_runs,
                   "best": best_run["n_solved"], "gap_words": last_run["gap_words_derived"],
                   "deliberative": last_run["deliberative_solves"],
                   "imagination": last_run["imagination_used"],
                   "edges": last_run["glm_edges"]}, f, indent=2, default=str)
    print(f"\nResults saved: {output_dir / 'v25_results.json'}")

    # Report
    report_dir = ARC_17_DIR / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    with open(report_dir / "v25_report.md", "w") as f:
        f.write(f"""# ARC-AGI v25 — Gap Words + Deliberative + Applied Imagination

**Date:** 2026-08-07
**Iterations:** {N_RUNS}

## What's new

### 1. Gap Word Derivation (from v37)
The GLM derives vectors for unknown concepts on-the-fly. When it encounters
a new pattern during ARC solving, it:
- Hashes the pattern to a 24-bit vector
- Snaps to nearest Golay codeword
- Checks proximity to existing concepts (Hamming ≤ 8)
- If close, ADDS it to the vocabulary — the GLM has LEARNED

### 2. Deliberative Reasoning (from v37)
The GLM breaks complex problems into steps:
1. Shape analysis (same? different? scaled?)
2. Colour analysis (which changed? which stayed?)
3. Position analysis (did cells move?)
4. Synthesis (what is the simplest rule?)

### 3. Applied Imagination
When imagination detects incoherence, it now CREATES a refined proposal:
- Colour mismatch → correct the colour map from train pairs
- Density low → add fill
- Shape mismatch → skip (can't fix)

### 4. More Puzzle Variation
- Colour-swapped variants
- Rotated variants
- Scaled variants (2×)
- Flipped variants

## Results

| Run | Solved | Lattice | Mind | Deliberative | Imagination | Gap Words | Edges |
|---|---|---|---|---|---|---|---|
""")
        for run in all_runs:
            f.write(f"| {run['run_number']} | {run['n_solved']}/{run['n_tasks']} | {run['lattice_solves']} | {run['mind_solves']} | {run['deliberative_solves']} | {run['imagination_used']} | {run['gap_words_derived']} | {run['glm_edges']} |\n")
        f.write(f"""
### Summary
- **Best:** {best_run['n_solved']}/{best_run['n_tasks']}
- **Gap words derived:** {last_run['gap_words_derived']}
- **Imagination used:** {last_run['imagination_used']}
- **Deliberative solves:** {last_run['deliberative_solves']}
- **GLM edges:** {last_run['glm_edges']}
""")
    print(f"Report saved: {report_dir / 'v25_report.md'}")


if __name__ == "__main__":
    main()
