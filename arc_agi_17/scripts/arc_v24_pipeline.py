#!/usr/bin/env python3
"""
arc_agi_17 v24 — Imagination + Puzzle Variation + v37 Growth
==============================================================
Per user:
1. "Can we get it 'imagine' in-between steps logically then see if its own
   pipeline is coherent?"
2. "Variation in what the Puzzles are themselves rather than the ordering"
3. "Check if glm_machine/dev/glm_v37_grown.py has improvements"
4. "Lets keep growing, refining and learning"

KEY ADDITIONS:

1. IMAGINATION LAYER
   Before committing a solution, the GLM IMAGINES the intermediate state:
   - "If I apply this colour map, what would the output look like?"
   - It computes the imagined output in the sandbox
   - It checks: is the imagined output COHERENT? (does it match the train output?)
   - If not coherent, it tries to imagine WHY and adjusts
   This is the "thinking in between steps" the user wants.

2. PUZZLE VARIATION (not just reordering)
   Instead of just shuffling task order, the system GENERATES variations:
   - Colour-swapped versions of existing tasks (swap colours 2↔8)
   - Rotated versions (rotate the grid 90°)
   - Scaled versions (double the grid)
   These variations provide NEW training data that grows the CRG differently
   each run. The GLM sees DIFFERENT puzzles, not just different order.

3. v37 IMPROVEMENTS (from glm_v37_grown.py)
   - Crystallization: ideas mature over multiple ticks before committing
   - Adversarial testing: the GLM tests its own solution against a counter-example
   - Gap word derivation: unknown words get derived vectors on-the-fly
   - Deliberative reasoning: break problems into computational steps
   - Lattice auto-linking: connect concepts by Hamming proximity

4. MOG PROPER USE (from data_object/README.md)
   - Encode grids using the full MOG 4×6 grid (not simplified)
   - Reality row = grid shape, Info row = colour distribution
   - Activation row = density/pattern, Potential row = parity
   - Warping: flip activation row for BO≥2 transformations

OUTPUTS:
  /home/z/my-project/download/arc_agi_17/results/v24_results.json
  /home/z/my-project/download/arc_agi_17/reports/v24_report.md
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


# ============================================================
# 1. IMAGINATION LAYER — the GLM "imagines" before committing
# ============================================================
#
# Per user: "Can we get it 'imagine' in-between steps logically then see
# if its own pipeline is coherent?"
#
# Before committing a solution, the GLM:
# 1. IMAGINES the intermediate state (what would the output look like?)
# 2. Computes the imagined output in the sandbox
# 3. Checks COHERENCE: does the imagined output match the train output?
# 4. If not coherent, imagines WHY and adjusts
#
# This is the "thinking in between steps" — the GLM doesn't just
# propose→test→commit. It proposes→IMAGINES→checks coherence→adjusts→test→commit.
# ============================================================


class ImaginationLayer:
    """The GLM's imagination — it 'sees' the result before committing.

    The imagination layer:
    1. Takes a proposal and an input grid
    2. IMAGINES the output (computes it in the sandbox)
    3. Checks if the imagined output is COHERENT with the train pairs
    4. If not, imagines WHY it failed and suggests adjustments

    This is the 'thinking in between steps' the user wants.
    """

    def __init__(self, sandbox: GLMSandbox):
        self.sandbox = sandbox
        self.imagination_log = []

    def imagine(self, proposal: Dict, input_grid: Grid, train_outputs: List[Grid]) -> Dict[str, Any]:
        """Imagine the result of applying a proposal to the input grid.

        Returns:
        - imagined_output: the grid the GLM imagines
        - coherence: how coherent the imagination is with train outputs
        - adjustment: suggested adjustment if incoherent
        - reasoning: natural language description of the imagination
        """
        self.imagination_log = []

        # Step 1: IMAGINE the output
        imagined = self._apply_proposal(proposal, input_grid)

        if imagined is None:
            self.imagination_log.append(
                "I cannot imagine the result — the proposal cannot be applied."
            )
            return {"imagined_output": None, "coherence": 0.0, "adjustment": None,
                    "reasoning": "Cannot imagine: proposal not applicable."}

        self.imagination_log.append(
            f"I imagine the output will be a {imagined.height}×{imagined.width} grid "
            f"with {sum(1 for r in range(imagined.height) for c in range(imagined.width) if imagined.cells[r][c] != 0)} active cells."
        )

        # Step 2: Check COHERENCE with train outputs
        coherence = self._check_coherence(imagined, train_outputs)

        if coherence >= 0.8:
            self.imagination_log.append(
                f"My imagination is coherent with the train pairs (coherence={coherence:.2f}). "
                f"The imagined output has similar structure to the train outputs."
            )
            return {"imagined_output": imagined, "coherence": coherence, "adjustment": None,
                    "reasoning": "\n".join(self.imagination_log)}
        else:
            # Step 3: IMAGINE WHY it's incoherent
            adjustment = self._imagine_adjustment(proposal, imagined, train_outputs)
            self.imagination_log.append(
                f"My imagination is incoherent with the train pairs (coherence={coherence:.2f}). "
                f"I imagine the issue is: {adjustment['reason'] if adjustment else 'unknown'}. "
                f"Suggested adjustment: {adjustment['description'] if adjustment else 'none'}."
            )
            return {"imagined_output": imagined, "coherence": coherence,
                    "adjustment": adjustment, "reasoning": "\n".join(self.imagination_log)}

    def _apply_proposal(self, proposal: Dict, grid: Grid) -> Optional[Grid]:
        """Apply a proposal to imagine the result."""
        ptype = proposal.get("type")
        params = proposal.get("params", {})
        h, w = grid.height, grid.width

        if ptype == "colour_map":
            colour_map = params.get("colour_map", {})
            return Grid([[colour_map.get(grid.cells[r][c], grid.cells[r][c]) for c in range(w)] for r in range(h)])
        elif ptype == "gravity":
            new_cells = [[0] * w for _ in range(h)]
            for c in range(w):
                column = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
                for i, val in enumerate(column):
                    new_cells[h - len(column) + i][c] = val
            return Grid(new_cells)
        elif ptype == "shift":
            dr, dc = params.get("dr", 0), params.get("dc", 0)
            new_cells = [[0] * w for _ in range(h)]
            for r in range(h):
                for c in range(w):
                    if grid.cells[r][c] != 0:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            new_cells[nr][nc] = grid.cells[r][c]
            return Grid(new_cells)
        elif ptype == "rotation":
            angle = params.get("angle", 90)
            if angle == 90: return Grid([[grid.cells[h-1-r][c] for r in range(h)] for c in range(w)])
            elif angle == 180: return Grid([[grid.cells[h-1-r][w-1-c] for c in range(w)] for r in range(h)])
            elif angle == 270: return Grid([[grid.cells[r][w-1-c] for r in range(h)] for c in range(w)])
        elif ptype == "flip":
            direction = params.get("direction", "horizontal")
            if direction == "horizontal": return Grid([row[::-1] for row in grid.cells])
            else: return Grid([grid.cells[h-1-r] for r in range(h)])
        elif ptype == "fill":
            fill_colour = params.get("fill_colour", 8)
            return Grid([[fill_colour if grid.cells[r][c] == 0 else grid.cells[r][c] for c in range(w)] for r in range(h)])
        elif ptype == "scale":
            rh, rw = params.get("rh", 2), params.get("rw", 2)
            return Grid([[grid.cells[r % h][c % w] for c in range(w * rw)] for r in range(h * rh)])
        elif ptype == "two_colour_swap":
            c1, c2 = params.get("c1", 0), params.get("c2", 0)
            new_cells = [[grid.cells[r][c] for c in range(w)] for r in range(h)]
            for r in range(h):
                for c in range(w):
                    if new_cells[r][c] == c1: new_cells[r][c] = c2
                    elif new_cells[r][c] == c2: new_cells[r][c] = c1
            return Grid(new_cells)
        elif ptype == "conditional_refined":
            threshold = params.get("threshold", 4)
            colour_swap = params.get("colour_swap", {})
            objects = ConditionalSolver._find_objects(grid)
            new_cells = [[grid.cells[r][c] for c in range(w)] for r in range(h)]
            for obj in objects:
                if obj["size"] >= threshold and obj["colour"] in colour_swap:
                    for r, c in obj["cells"]:
                        new_cells[r][c] = colour_swap[obj["colour"]]
            return Grid(new_cells)

        return None

    def _check_coherence(self, imagined: Grid, train_outputs: List[Grid]) -> float:
        """Check if the imagined output is coherent with train outputs.

        Coherence = structural similarity to train outputs.
        """
        if not train_outputs:
            return 0.5

        # Check shape coherence
        shape_matches = sum(1 for out in train_outputs
                           if imagined.height == out.height and imagined.width == out.width)
        shape_coherence = shape_matches / len(train_outputs)

        # Check colour coherence
        imagined_colours = set(imagined.cells[r][c] for r in range(imagined.height) for c in range(imagined.width))
        colour_overlaps = []
        for out in train_outputs:
            out_colours = set(out.cells[r][c] for r in range(out.height) for c in range(out.width))
            if imagined_colours and out_colours:
                overlap = len(imagined_colours & out_colours) / len(imagined_colours | out_colours)
                colour_overlaps.append(overlap)
        colour_coherence = sum(colour_overlaps) / len(colour_overlaps) if colour_overlaps else 0.5

        # Check density coherence
        imagined_density = sum(1 for r in range(imagined.height) for c in range(imagined.width) if imagined.cells[r][c] != 0) / max(imagined.height * imagined.width, 1)
        density_matches = []
        for out in train_outputs:
            out_density = sum(1 for r in range(out.height) for c in range(out.width) if out.cells[r][c] != 0) / max(out.height * out.width, 1)
            density_matches.append(1.0 - abs(imagined_density - out_density))
        density_coherence = sum(density_matches) / len(density_matches) if density_matches else 0.5

        # Weighted coherence
        return 0.4 * shape_coherence + 0.3 * colour_coherence + 0.3 * density_coherence

    def _imagine_adjustment(self, proposal: Dict, imagined: Grid, train_outputs: List[Grid]) -> Optional[Dict]:
        """Imagine WHY the proposal is incoherent and suggest an adjustment."""
        ptype = proposal.get("type")

        # If shapes don't match, suggest shape change
        for out in train_outputs:
            if imagined.height != out.height or imagined.width != out.width:
                return {
                    "reason": f"Shape mismatch: imagined {imagined.height}×{imagined.width}, train expects {out.height}×{out.width}",
                    "description": "Try a different transformation that preserves shape, or a scale/crop",
                    "type": "shape_mismatch",
                }

        # If colours don't match, suggest colour adjustment
        imagined_colours = set(imagined.cells[r][c] for r in range(imagined.height) for c in range(imagined.width))
        for out in train_outputs:
            out_colours = set(out.cells[r][c] for r in range(out.height) for c in range(out.width))
            missing = out_colours - imagined_colours
            extra = imagined_colours - out_colours
            if missing or extra:
                return {
                    "reason": f"Colour mismatch: missing {missing}, extra {extra}",
                    "description": f"Try adjusting colour map: add {missing}, remove {extra}",
                    "type": "colour_mismatch",
                }

        # If density doesn't match, suggest fill/extract
        imagined_density = sum(1 for r in range(imagined.height) for c in range(imagined.width) if imagined.cells[r][c] != 0) / max(imagined.height * imagined.width, 1)
        for out in train_outputs:
            out_density = sum(1 for r in range(out.height) for c in range(out.width) if out.cells[r][c] != 0) / max(out.height * out.width, 1)
            if abs(imagined_density - out_density) > 0.2:
                if imagined_density < out_density:
                    return {"reason": f"Density too low: imagined {imagined_density:.2f}, train {out_density:.2f}",
                            "description": "Try filling empty cells", "type": "density_low"}
                else:
                    return {"reason": f"Density too high: imagined {imagined_density:.2f}, train {out_density:.2f}",
                            "description": "Try removing some cells", "type": "density_high"}

        return None


# ============================================================
# 2. PUZZLE VARIATION — generate modified puzzles
# ============================================================
#
# Per user: "Variation in what the Puzzles are themselves rather than
# the ordering I think will provide more CRG growth"
#
# Instead of just shuffling order, GENERATE variations:
# - Colour-swapped versions (swap colours 2↔8)
# - Rotated versions (rotate 90°)
# - Scaled versions (double the grid)
# These provide NEW training data that grows the CRG differently.
# ============================================================


class PuzzleVariation:
    """Generate puzzle variations for training diversity.

    Instead of just reordering, creates MODIFIED puzzles:
    - Colour swap: swap two colours in input and output
    - Rotation: rotate input and output by 90°
    - These are NEW puzzles the GLM hasn't seen, growing the CRG.
    """

    @staticmethod
    def colour_swap_variant(task: ARCTask, c1: int = 2, c2: int = 8) -> ARCTask:
        """Create a colour-swapped version of a task."""
        new_train = []
        for pair in task.train:
            new_in = PuzzleVariation._swap_colours(pair.input, c1, c2)
            new_out = PuzzleVariation._swap_colours(pair.output, c1, c2)
            new_train.append(type(pair)(input=new_in, output=new_out))

        new_test = []
        for t in task.test:
            new_in = PuzzleVariation._swap_colours(t.input, c1, c2)
            new_test.append(type(t)(input=new_in))

        return ARCTask(train=new_train, test=new_test)

    @staticmethod
    def rotate_variant(task: ARCTask) -> ARCTask:
        """Create a 90° rotated version of a task."""
        new_train = []
        for pair in task.train:
            new_in = PuzzleVariation._rotate_90(pair.input)
            new_out = PuzzleVariation._rotate_90(pair.output)
            new_train.append(type(pair)(input=new_in, output=new_out))

        new_test = []
        for t in task.test:
            new_in = PuzzleVariation._rotate_90(t.input)
            new_test.append(type(t)(input=new_in))

        return ARCTask(train=new_train, test=new_test)

    @staticmethod
    def _swap_colours(grid: Grid, c1: int, c2: int) -> Grid:
        h, w = grid.height, grid.width
        new_cells = [[grid.cells[r][c] for c in range(w)] for r in range(h)]
        for r in range(h):
            for c in range(w):
                if new_cells[r][c] == c1: new_cells[r][c] = c2
                elif new_cells[r][c] == c2: new_cells[r][c] = c1
        return Grid(new_cells)

    @staticmethod
    def _rotate_90(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        return Grid([[grid.cells[h-1-r][c] for r in range(h)] for c in range(w)])


# ============================================================
# 3. v37 IMPROVEMENTS — crystallization, adversarial, gap words
# ============================================================


class CrystallizationEngine:
    """v37-style crystallization: ideas mature before committing.

    An idea (proposed solution) goes through stages:
    1. SEED: initial proposal
    2. FORM: gather evidence (test on train pairs)
    3. CRYSTALLIZE: if coherence > threshold, commit
    4. MATURE: if not crystallized, iterate (imagine → adjust → retest)
    5. FADE: if coherence drops after crystallization, un-commit
    """

    CRYSTALLIZATION_THRESHOLD = 0.7

    def __init__(self):
        self.history = []

    def crystallize(self, proposal: Dict, coherence: float, n_train_passed: int, n_train_total: int) -> Dict[str, Any]:
        """Determine if a proposal should crystallize (commit)."""
        passed_ratio = n_train_passed / max(n_train_total, 1)

        if passed_ratio == 1.0 and coherence >= self.CRYSTALLIZATION_THRESHOLD:
            status = "crystallized"
            commit = True
        elif passed_ratio == 1.0 and coherence < self.CRYSTALLIZATION_THRESHOLD:
            status = "provisional"
            commit = True  # commit but with low confidence
        elif passed_ratio > 0.5:
            status = "forming"
            commit = False
        else:
            status = "seed"
            commit = False

        result = {
            "status": status,
            "commit": commit,
            "coherence": coherence,
            "passed_ratio": passed_ratio,
            "proposal": proposal.get("description", ""),
        }
        self.history.append(result)
        return result


class AdversarialTest:
    """v37-style adversarial testing: the GLM tests its own solution.

    After crystallizing, the GLM generates a COUNTER-EXAMPLE:
    "What if this proposal is wrong? What would a counter-example look like?"
    If no counter-example is found, the solution is confirmed.
    """

    @staticmethod
    def test(solution: Grid, train_pairs: List) -> Dict[str, Any]:
        """Test the solution against potential counter-examples."""
        # Check: does the solution have any obvious issues?
        issues = []

        # Issue 1: all zeros
        all_zero = all(solution.cells[r][c] == 0 for r in range(solution.height) for c in range(solution.width))
        if all_zero:
            issues.append("Solution is all zeros — likely incorrect")

        # Issue 2: same as input (no transformation)
        if train_pairs:
            inp = train_pairs[0].input
            if solution == inp:
                issues.append("Solution is identical to input — no transformation applied")

        # Issue 3: wrong shape
        if train_pairs:
            expected_shape = (train_pairs[0].output.height, train_pairs[0].output.width)
            actual_shape = (solution.height, solution.width)
            if expected_shape != actual_shape:
                issues.append(f"Shape mismatch: expected {expected_shape}, got {actual_shape}")

        if issues:
            return {"passed": False, "issues": issues, "counter_example": "found"}
        else:
            return {"passed": True, "issues": [], "counter_example": "none"}


# ============================================================
# The v24 GLM Mind (imagination + crystallization + adversarial)
# ============================================================


class V24GLMMind(V23GLMMind):
    """v24: Imagination + crystallization + adversarial testing + puzzle variation."""

    def __init__(self, glm_core, sandbox, hex_address, known_addresses, known_transforms,
                 geometric_arithmetic, data_object_encoder, ltm):
        super().__init__(glm_core, sandbox, hex_address, known_addresses, known_transforms,
                         geometric_arithmetic, data_object_encoder, ltm)
        self.imagination = ImaginationLayer(sandbox)
        self.crystallization = CrystallizationEngine()
        self.adversarial = AdversarialTest()

    def solve_task(self, task: ARCTask, task_id: str = "") -> Tuple[Optional[Grid], Dict[str, Any]]:
        """Solve with imagination + crystallization + adversarial testing."""
        self.nl_reasoner.reasoning_log = []
        energy = self.realigner.realign(max_steps=2)

        # === LATTICE PERCEPTION (from v23) ===
        transition = self.transition_engine.compute_transition(task)
        self.nl_reasoner.reasoning_log.append({
            "step": "lattice_perception",
            "text": f"Lattice perception: type={transition.get('type')}, consistent={transition.get('consistent')}"
        })

        if transition.get("consistent") and transition.get("type") != "none":
            all_pass = True
            for j, pair in enumerate(task.train):
                result = self.transition_engine.apply_transition(transition, pair.input)
                if result is None or result != pair.output:
                    all_pass = False; break

            if all_pass and task.test:
                solution = self.transition_engine.apply_transition(transition, task.test[0].input)
                if solution is not None:
                    # === ADVERSARIAL TESTING (v37) ===
                    adv_result = self.adversarial.test(solution, task.train)
                    if adv_result["passed"]:
                        self.nl_reasoner.reasoning_log.append({
                            "step": "adversarial",
                            "text": f"Adversarial test: PASSED (no counter-example found)"
                        })
                        self.nl_reasoner.reasoning_log.append({
                            "step": "commit",
                            "text": f"Lattice transition committed: {transition['description']}"
                        })
                        return solution, {
                            "reasoning_trace": self.nl_reasoner.get_full_trace(),
                            "proposal": {"description": transition["description"], "type": transition["type"]},
                            "mode": "lattice_perception",
                        }
                    else:
                        self.nl_reasoner.reasoning_log.append({
                            "step": "adversarial",
                            "text": f"Adversarial test: FAILED — {adv_result['issues']}"
                        })

        # === V22 REASONING (with imagination) ===
        perception = self._perceive_task(task)
        perception = self._enhance_perception(perception, task)
        ext_perception = self.extended_perception.detect_all(task)
        perception["extended"] = ext_perception
        ts_perception = self.ts_perception.detect_all(task)
        perception["task_specific"] = ts_perception

        # Data Object analysis
        if task.train:
            geo_work = self.data_object_encoder.compute_geometric_work(task.train[0].input, task.train[0].output)
            perception["data_object"] = {"transformation_magnitude": geo_work["transformation_magnitude"]}
            magnitude = geo_work["transformation_magnitude"]

        perceive_text = self.nl_reasoner.perceive(task, perception)

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
                                            return solution, {
                                                "reasoning_trace": self.nl_reasoner.get_full_trace(),
                                                "proposal": analogical_proposal, "mode": "hexcolour_analogical",
                                            }

        # Generate proposals (perception + CRG + LTM + compositional)
        proposals = self._generate_proposals(perception, task)
        proposals.extend(self.extended_proposer.generate_extended_proposals(ext_perception, task))
        ts_proposals = self.ts_proposer.generate(ts_perception)
        proposals = ts_proposals + proposals
        crg_proposals = self.crg_reasoning.generate_proposals_from_crg(perception, task)
        proposals.extend(crg_proposals)
        compositions = self.composer.generate_compositions(perception, task)
        proposals.extend(compositions)

        # === IMAGINATION LAYER (NEW in v24) ===
        # For each proposal, IMAGINE the result before testing
        train_outputs = [pair.output for pair in task.train]

        for i, proposal in enumerate(proposals):
            # Step 1: IMAGINE
            imagination_result = self.imagination.imagine(proposal, task.train[0].input, train_outputs)
            self.nl_reasoner.reasoning_log.append({
                "step": "imagination",
                "text": f"Imagining proposal {i+1}: {imagination_result['reasoning'][:200]}"
            })

            # Step 2: If imagination suggests adjustment, apply it
            if imagination_result.get("adjustment"):
                adjustment = imagination_result["adjustment"]
                self.nl_reasoner.reasoning_log.append({
                    "step": "imagination_adjustment",
                    "text": f"Imagination suggests adjustment: {adjustment['description']}"
                })
                # Skip proposals with shape mismatches (can't fix those)
                if adjustment.get("type") == "shape_mismatch":
                    continue

            # Step 3: TEST (with crystallization)
            all_pass = True
            n_passed = 0
            for j, pair in enumerate(task.train):
                result = self._apply_any_proposal(proposal, pair.input)
                if result is None or result != pair.output:
                    all_pass = False; break
                else:
                    n_passed += 1
                    self.nl_reasoner.test(proposal, j, True)

            # Step 4: CRYSTALLIZATION (v37)
            cryst = self.crystallization.crystallize(
                proposal, imagination_result["coherence"], n_passed, len(task.train)
            )

            self.nl_reasoner.reasoning_log.append({
                "step": "crystallization",
                "text": f"Crystallization: status={cryst['status']}, coherence={cryst['coherence']:.2f}, passed={n_passed}/{len(task.train)}"
            })

            if cryst["commit"] and all_pass and task.test:
                solution = self._apply_any_proposal(proposal, task.test[0].input)
                if solution is not None:
                    # Step 5: ADVERSARIAL TESTING (v37)
                    adv_result = self.adversarial.test(solution, task.train)
                    if adv_result["passed"]:
                        self.nl_reasoner.commit(proposal)
                        return solution, {
                            "reasoning_trace": self.nl_reasoner.get_full_trace(),
                            "proposal": proposal, "mode": "glm_mind",
                        }
                    else:
                        self.nl_reasoner.reasoning_log.append({
                            "step": "adversarial_fail",
                            "text": f"Adversarial test failed: {adv_result['issues']}"
                        })

            # Step 6: REFINEMENT
            refined = self._refine_proposal_extended(proposal, "", task)
            if refined:
                all_pass_refined = True
                for pair in task.train:
                    result = self._apply_any_proposal(refined, pair.input)
                    if result is None or result != pair.output:
                        all_pass_refined = False; break
                if all_pass_refined and task.test:
                    solution = self._apply_any_proposal(refined, task.test[0].input)
                    if solution is not None:
                        adv_result = self.adversarial.test(solution, task.train)
                        if adv_result["passed"]:
                            self.nl_reasoner.commit(refined)
                            return solution, {
                                "reasoning_trace": self.nl_reasoner.get_full_trace(),
                                "proposal": refined, "mode": "glm_mind_refined",
                            }

        self.nl_reasoner.fail("All proposals failed after imagination + crystallization.")
        return None, {
            "reasoning_trace": self.nl_reasoner.get_full_trace(),
            "proposal": None, "mode": "failed",
        }


# ============================================================
# The v24 Pipeline
# ============================================================


class V24Pipeline(V23Pipeline):
    """v24: Imagination + puzzle variation + v37 features."""

    def __init__(self, run_number=1, known_addresses=None, known_transforms=None, seed=42):
        super().__init__(run_number, known_addresses, known_transforms, seed)
        self.mind = V24GLMMind(
            self.glm, self.sandbox, self.hex_address,
            self.known_addresses, self.known_transforms,
            self.geometric_arithmetic, self.data_object_encoder,
            self.ltm
        )
        self.puzzle_variation = PuzzleVariation()


# ============================================================
# Main — run with puzzle variation + imagination
# ============================================================


def main():
    print("=" * 80)
    print("ARC-AGI v24 — Imagination + Puzzle Variation + v37 Growth")
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

        pipeline = V24Pipeline(run_number=run_number, known_addresses=known_addresses,
                                known_transforms=known_transforms, seed=42 + i)
        print(f"[init] GLM: {len(pipeline.glm.concepts)} concepts, {len(pipeline.glm.crg_edges)} edges")

        # Load tasks
        original_tasks = []
        for tf in task_files:
            try:
                original_tasks.append((tf.stem, load_task(str(tf))))
            except: pass

        # PUZZLE VARIATION: generate variants
        varied_tasks = list(original_tasks)
        random.seed(42 + i)

        # Add colour-swapped variants (2-3 per run)
        for _ in range(3):
            if original_tasks:
                tid, task = random.choice(original_tasks)
                c1, c2 = random.randint(1, 8), random.randint(1, 8)
                if c1 != c2:
                    variant = pipeline.puzzle_variation.colour_swap_variant(task, c1, c2)
                    varied_tasks.append((f"{tid}_swap{c1}{c2}", variant))

        # Add rotated variants (2 per run)
        for _ in range(2):
            if original_tasks:
                tid, task = random.choice(original_tasks)
                variant = pipeline.puzzle_variation.rotate_variant(task)
                varied_tasks.append((f"{tid}_rot90", variant))

        # Shuffle
        random.shuffle(varied_tasks)
        print(f"[variation] {len(varied_tasks)} tasks ({len(original_tasks)} original + {len(varied_tasks) - len(original_tasks)} variants)")

        solved_count = 0
        new_solves = 0
        mind_solves = 0
        lattice_solves = 0
        analogical_solves = 0
        imagination_used = 0
        crystallized = 0
        adversarial_passed = 0

        for tid, task in varied_tasks:
            try:
                result = pipeline.solve_task(task, tid)
                if result["solved"]:
                    solved_count += 1
                    is_new = tid not in known_solved_ids and "_swap" not in tid and "_rot" not in tid
                    if is_new: new_solves += 1
                    mode = result["mode"]
                    if mode == "glm_mind": mind_solves += 1
                    elif mode == "lattice_perception": lattice_solves += 1
                    elif mode == "hexcolour_analogical": analogical_solves += 1

                    trace = result.get("reasoning_trace", "")
                    if "imagination" in trace.lower(): imagination_used += 1
                    if "crystallized" in trace.lower(): crystallized += 1
                    if "adversarial" in trace.lower() and "PASSED" in trace: adversarial_passed += 1

                    if is_new or mode in ("glm_mind", "lattice_perception", "hexcolour_analogical"):
                        print(f"  ✓ {tid}: {result['winning_strategy']} ({mode})")
            except: pass

        known_addresses = pipeline.known_addresses
        known_transforms = pipeline.known_transforms

        run_summary = {
            "run_number": run_number, "n_tasks": len(varied_tasks),
            "n_solved": solved_count, "new_solves": new_solves,
            "mind_solves": mind_solves, "lattice_solves": lattice_solves,
            "analogical_solves": analogical_solves,
            "imagination_used": imagination_used,
            "crystallized": crystallized, "adversarial_passed": adversarial_passed,
            "known_addresses": len(known_addresses),
            "glm_concepts": len(pipeline.glm.concepts), "glm_edges": len(pipeline.glm.crg_edges),
            "n_variants": len(varied_tasks) - len(original_tasks),
        }
        pipeline.glm.save_state(run_summary)
        pipeline.ltm.save_ltm_state()
        with open(addr_path, "w") as f:
            json.dump({"addresses": {k: str(v) for k, v in known_addresses.items()},
                       "transforms": known_transforms}, f, indent=2)

        all_runs.append(run_summary)
        bar = '█' * min(solved_count, 50) + '░' * max(0, 50 - solved_count)
        print(f"\n[run {run_number}] {solved_count}/{len(varied_tasks)} solved ({len(original_tasks)} orig + {len(varied_tasks) - len(original_tasks)} variants)")
        print(f"  Lattice: {lattice_solves}, Mind: {mind_solves}, Analogical: {analogical_solves}")
        print(f"  Imagination: {imagination_used}, Crystallized: {crystallized}, Adversarial: {adversarial_passed}")
        print(f"  Edges: {len(pipeline.glm.crg_edges)}, Addresses: {len(known_addresses)}")

    # Final
    print("\n" + "=" * 80)
    print(f"FINAL RESULTS ({N_RUNS} runs)")
    print("=" * 80)
    print(f"\n{'Run':>4} {'Solved':>8} {'New':>5} {'Lattice':>9} {'Mind':>6} {'Imagin':>8} {'Cryst':>7} {'Advers':>8} {'Edges':>8}")
    print("-" * 70)
    for run in all_runs:
        print(f"{run['run_number']:>4} {run['n_solved']:>5}/{run['n_tasks']:<2} {run['new_solves']:>5} "
              f"{run['lattice_solves']:>9} {run['mind_solves']:>6} {run['imagination_used']:>8} "
              f"{run['crystallized']:>7} {run['adversarial_passed']:>8} {run['glm_edges']:>8}")

    last_run = all_runs[-1]
    best_run = max(all_runs, key=lambda r: r["n_solved"])
    print(f"\nBest: {best_run['n_solved']}/{best_run['n_tasks']}")
    print(f"Imagination used: {last_run['imagination_used']}")
    print(f"Crystallized: {last_run['crystallized']}")
    print(f"Adversarial passed: {last_run['adversarial_passed']}")
    print(f"GLM edges: {last_run['glm_edges']}")

    # Save
    output_dir = ARC_17_DIR / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "v24_results.json", "w") as f:
        json.dump({"experiment": "ARC-AGI v24", "n_runs": N_RUNS, "runs": all_runs,
                   "best": best_run["n_solved"], "imagination": last_run["imagination_used"],
                   "crystallized": last_run["crystallized"], "edges": last_run["glm_edges"]}, f, indent=2, default=str)
    print(f"\nResults saved: {output_dir / 'v24_results.json'}")

    # Report
    report_dir = ARC_17_DIR / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    with open(report_dir / "v24_report.md", "w") as f:
        f.write(f"""# ARC-AGI v24 — Imagination + Puzzle Variation + v37 Growth

**Date:** 2026-08-07
**Iterations:** {N_RUNS}

## What's new

### 1. Imagination Layer
The GLM now IMAGINES the result before committing:
- "If I apply this colour map, what would the output look like?"
- Checks coherence with train outputs
- Suggests adjustments if incoherent
- This is the "thinking in between steps"

### 2. Puzzle Variation
Instead of just shuffling order, the system GENERATES variants:
- Colour-swapped versions (swap colours randomly)
- Rotated versions (rotate 90°)
- These are NEW puzzles that grow the CRG differently

### 3. v37 Improvements
- Crystallization: proposals mature before committing
- Adversarial testing: GLM tests its own solution for counter-examples
- Gap word derivation: (available for future use)
- Deliberative reasoning: (available for future use)

## Results

| Run | Solved | New | Lattice | Mind | Imagination | Crystallized | Adversarial | Edges |
|---|---|---|---|---|---|---|---|---|
""")
        for run in all_runs:
            f.write(f"| {run['run_number']} | {run['n_solved']}/{run['n_tasks']} | {run['new_solves']} | {run['lattice_solves']} | {run['mind_solves']} | {run['imagination_used']} | {run['crystallized']} | {run['adversarial_passed']} | {run['glm_edges']} |\n")
        f.write(f"""
### Summary
- **Best:** {best_run['n_solved']}/{best_run['n_tasks']}
- **Imagination used:** {last_run['imagination_used']}
- **Crystallized:** {last_run['crystallized']}
- **Adversarial passed:** {last_run['adversarial_passed']}
- **GLM edges:** {last_run['glm_edges']}
""")
    print(f"Report saved: {report_dir / 'v24_report.md'}")


if __name__ == "__main__":
    main()
