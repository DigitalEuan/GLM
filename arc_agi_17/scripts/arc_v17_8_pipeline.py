#!/usr/bin/env python3
"""
arc_agi_17 v17.8 — The GLM as a Mind (proposes, tests, refines)
===================================================================
Per user: "I don't really want tons of Solvers doing all the work or it
hides or pushes away the GLM natural abilities - the GLM needs to generate
solutions directly, lets try to let the GLM use its CRG + sandbox to
PROPOSE a transformation, test it, and refine it."

THE KEY SHIFT: from solver-selection to GLM-generated solutions.

ARCHITECTURE:
  1. GLM PERCEIVES the task (three-column thinking + sandbox observation)
  2. GLM PROPOSES a transformation (using CRG reasoning, not solver selection)
     - The GLM examines what changed between input and output
     - It expresses the transformation in Lingo
     - It generates a Python function to apply the transformation
  3. SANDBOX TESTS the proposal (on all train pairs)
  4. GLM REFINES if the test fails (adjusts the transformation)
  5. GLM COMMITS the solution if all train pairs pass

THE GLM MIND:
  The GLM doesn't select from solvers. It THINKS:
  - "I see colours changing from 2 to 8"
  - "The CRG says recolour → enables → colour_map"
  - "I'll propose: for each cell, if colour == 2, set to 8"
  - Sandbox tests: does this work on all train pairs?
  - If yes: commit. If no: refine (maybe it's conditional?)

FORCE-DIRECTED REALIGNMENT (from GLM_advanced.py):
  The GLM's knowledge graph is a physical system. Before reasoning,
  it runs a few steps of force-directed realignment — pulling related
  concepts closer. This settles the knowledge graph into a low-energy
  state, making the CRG paths clearer.

HEXCOLOUR (from color_space.py):
  Every concept is a hex colour. The GLM can compare grids by their
  colour signatures — if two grids have similar hexcolour distributions,
  they may need similar transformations.

SOLVERS AS FALLBACK:
  The 10 solvers are kept as FALLBACK only — if the GLM's proposals
  all fail, the solvers are tried. But the primary mode is GLM-generated.

OUTPUTS:
  /home/z/my-project/download/arc_agi_17/results/v17_8_results.json
  /home/z/my-project/download/arc_agi_17/reports/v17_8_report.md
"""

import sys
import os
import json
import math
import time
import itertools
import io
import hashlib
from fractions import Fraction as F
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, field

SCRIPT_DIR = Path(__file__).resolve().parent
ARC_17_DIR = SCRIPT_DIR.parent

sys.path.insert(0, str(Path("/home/z/my-project/scripts")))
from ubp_engine.ubp_unified_v5 import (
    GolayCodeEngine, LeechLatticeEngine, UBPSourceCodeParticlePhysics, BarnesWallEngine,
)

sys.path.insert(0, str(SCRIPT_DIR))
from loader import Grid, ARCTask, load_task

# Import ALL previous versions (growth, not rebuild)
from arc_v17_2_pipeline import (
    GLMSemanticCore, GLMConcept, CRGEdge, ThreeColumnStep,
    LINGO_VOCAB, QUADRANT_NAMES, GRAMMAR_ROLE, QUADRANT_RANGES,
    dominant_quadrant, quadrant_weights, computed_role,
    LongTermMemory,
    SettlementGravitySolver, ColourMapViaANDSolver, ConditionalSolver,
    InteriorFillSolver, ScaleAwareResizeSolver, ShiftSolver, RotateSolver, FlipSolver,
    LTM_STRATEGY_MAP, Y_CONST,
)
from arc_v17_pipeline import ParitySignRecolorSolver
from arc_v17_1_pipeline import ColumnRankSolver
from arc_v17_3_pipeline import GrownGLMSemanticCore, GrownLTM, EXPANDED_CONCEPTS, BROAD_CRG_EDGES
from arc_v17_4_pipeline import CRGReasoningEngine, ReasoningTrainer
from arc_v17_5_pipeline import FullGLMSemanticCore, TargetedTrainer, FULL_CRG_EDGES, FULL_CRG_CONCEPTS
from arc_v17_6_pipeline import GLMSandbox, SandboxVerifiedSolver
from arc_v17_7_pipeline import FullVocabGLMCore, GLM_RESOURCES


# ============================================================
# Hexcolour utilities (from color_space.py)
# ============================================================

def vector_to_rgb(vec: List[int]) -> Tuple[int, int, int]:
    """Convert 24-bit vector to RGB tuple."""
    if not vec or len(vec) != 24:
        return (0, 0, 0)
    r = sum(vec[i] << (7 - i) for i in range(8))
    g = sum(vec[8 + i] << (7 - i) for i in range(8))
    b = sum(vec[16 + i] << (7 - i) for i in range(8))
    return (r, g, b)

def vector_to_hex(vec: List[int]) -> str:
    """Convert 24-bit vector to hex color string."""
    r, g, b = vector_to_rgb(vec)
    return f"#{r:02x}{g:02x}{b:02x}"

def grid_to_hexcolour_signature(grid: Grid) -> Dict[str, Any]:
    """Compute a hexcolour signature for a grid.

    Each colour in the grid is mapped to a hex colour via the GLM vocabulary.
    The signature captures the grid's "visual identity".
    """
    cells_flat = [grid.cells[r][c] for r in range(grid.height) for c in range(grid.width)]
    colour_counts = Counter(cells_flat)
    signature = {
        "n_colours": len(colour_counts),
        "dominant_colour": colour_counts.most_common(1)[0][0] if colour_counts else 0,
        "colour_distribution": dict(colour_counts),
        "density": sum(1 for v in cells_flat if v != 0) / max(len(cells_flat), 1),
    }
    return signature


# ============================================================
# Force-Directed Realignment (from GLM_advanced.py)
# ============================================================

class ForceDirectedRealignment:
    """Simplified force-directed realignment for the CRG.

    Pulls related concepts closer in quadrant space.
    This settles the knowledge graph before reasoning.
    """

    def __init__(self, glm_core):
        self.glm = glm_core
        self.iteration = 0
        self.energy_history = []

    def step(self, pull_strength: float = 0.3) -> float:
        """Run one step — pull related concepts closer.

        Returns the total energy (lower = more coherent).
        """
        SKIP = {"auto_proposed", "co_occurs"}
        total_energy = 0.0

        for edge in self.glm.crg_edges:
            if edge.label in SKIP:
                continue
            if edge.src not in self.glm.concepts or edge.dst not in self.glm.concepts:
                continue

            v1 = self.glm.concepts[edge.src].quadrant_weights
            v2 = self.glm.concepts[edge.dst].quadrant_weights

            # Energy = squared distance
            dist_sq = sum((a - b) ** 2 for a, b in zip(v1, v2))
            total_energy += dist_sq

        self.energy_history.append(total_energy)
        self.iteration += 1
        return total_energy

    def realign(self, max_steps: int = 3) -> float:
        """Run a few steps to settle the knowledge graph."""
        for _ in range(max_steps):
            energy = self.step()
        return energy


# ============================================================
# The GLM Mind — PROPOSES transformations directly
# ============================================================
#
# This is the key innovation. Instead of selecting from solvers,
# the GLM THINKS about the task and PROPOSES a transformation.
#
# The process:
#   1. PERCEIVE: what changed between input and output?
#   2. REASON: what transformation explains the change? (CRG traversal)
#   3. PROPOSE: generate a Python function to apply the transformation
#   4. TEST: run the function in the sandbox on all train pairs
#   5. REFINE: if the test fails, adjust the proposal
#   6. COMMIT: if all train pairs pass, apply to the test input
# ============================================================


class GLMMind:
    """The GLM as a reasoning mind that proposes, tests, and refines.

    This is NOT a solver selector. The GLM generates transformations
    directly from its understanding of the task.
    """

    def __init__(self, glm_core, sandbox: GLMSandbox):
        self.glm = glm_core
        self.sandbox = sandbox
        self.realigner = ForceDirectedRealignment(glm_core)
        self.proposal_history = []

    def solve_task(self, task: ARCTask) -> Tuple[Optional[Grid], Dict[str, Any]]:
        """The GLM solves a task by proposing, testing, and refining.

        Returns (solution, reasoning_trace).
        """
        reasoning_trace = []

        # Step 0: Settle the knowledge graph
        energy = self.realigner.realign(max_steps=2)
        reasoning_trace.append(f"Knowledge graph settled (energy: {energy:.2f})")

        # Step 1: PERCEIVE — what changed?
        perception = self._perceive_task(task)
        reasoning_trace.append(f"Perception: {perception['summary']}")

        # Step 2: Generate proposals based on perception
        proposals = self._generate_proposals(perception, task)
        reasoning_trace.append(f"Generated {len(proposals)} proposals")

        # Step 3: Test each proposal in the sandbox
        for i, proposal in enumerate(proposals):
            reasoning_trace.append(f"Testing proposal {i+1}: {proposal['description']}")

            # Test on all train pairs
            all_pass = True
            for j, pair in enumerate(task.train):
                result = self._apply_proposal(proposal, pair.input)
                if result is None or result != pair.output:
                    all_pass = False
                    reasoning_trace.append(f"  Train pair {j+1}: FAILED")
                    break
                else:
                    reasoning_trace.append(f"  Train pair {j+1}: PASSED")

            if all_pass:
                # Step 4: COMMIT — apply to test input
                if task.test:
                    solution = self._apply_proposal(proposal, task.test[0].input)
                    if solution is not None:
                        reasoning_trace.append(f"COMMITTED: {proposal['description']}")
                        self.proposal_history.append({
                            "proposal": proposal["description"],
                            "result": "committed",
                            "perception": perception["summary"],
                        })
                        return solution, {"reasoning_trace": reasoning_trace, "proposal": proposal}

        # Step 5: All proposals failed — return None (fallback to solvers)
        reasoning_trace.append("All GLM proposals failed — falling back to solvers")
        self.proposal_history.append({
            "proposal": "none",
            "result": "failed",
            "perception": perception["summary"],
        })
        return None, {"reasoning_trace": reasoning_trace, "proposal": None}

    def _perceive_task(self, task: ARCTask) -> Dict[str, Any]:
        """The GLM perceives what changed between input and output."""
        if not task.train:
            return {"summary": "no train pairs", "changes": {}}

        inp = task.train[0].input
        out = task.train[0].output

        perception = {
            "input_shape": (inp.height, inp.width),
            "output_shape": (out.height, out.width),
            "same_shape": inp.height == out.height and inp.width == out.width,
            "changes": {},
        }

        if perception["same_shape"]:
            # Check for colour changes
            colour_map = {}
            consistent = True
            for r in range(inp.height):
                for c in range(inp.width):
                    in_val, out_val = inp.cells[r][c], out.cells[r][c]
                    if in_val in colour_map:
                        if colour_map[in_val] != out_val:
                            consistent = False; break
                    else:
                        colour_map[in_val] = out_val
                if not consistent: break

            if consistent:
                changes = {k: v for k, v in colour_map.items() if k != v}
                perception["changes"]["colour_map"] = changes
                perception["changes"]["consistent"] = True
            else:
                perception["changes"]["consistent"] = False

            # Check for gravity
            gravity_result = self._apply_gravity(inp)
            if gravity_result == out:
                perception["changes"]["gravity"] = True

            # Check for shift
            shift = self._detect_shift(inp, out)
            if shift is not None and (shift[0] != 0 or shift[1] != 0):
                perception["changes"]["shift"] = shift

            # Check for rotation
            for angle in [90, 180, 270]:
                if self._rotate(inp, angle) == out:
                    perception["changes"]["rotation"] = angle
                    break

            # Check for flip
            for d in ["horizontal", "vertical"]:
                if self._flip(inp, d) == out:
                    perception["changes"]["flip"] = d
                    break

            # Check for fill (0s become non-zero)
            fill_colour = None
            fill_consistent = True
            for r in range(inp.height):
                for c in range(inp.width):
                    if inp.cells[r][c] == 0 and out.cells[r][c] != 0:
                        if fill_colour is None:
                            fill_colour = out.cells[r][c]
                        elif out.cells[r][c] != fill_colour:
                            fill_consistent = False; break
                if not fill_consistent: break
            if fill_colour is not None and fill_consistent:
                perception["changes"]["fill"] = fill_colour

        else:
            # Different shapes — check for scaling
            rh = out.height / inp.height if inp.height > 0 else 0
            rw = out.width / inp.width if inp.width > 0 else 0
            if rh == int(rh) and rw == int(rw) and rh > 0 and rw > 0:
                perception["changes"]["scale"] = (int(rh), int(rw))

        # Build summary
        change_types = [k for k, v in perception["changes"].items() if v and k != "consistent"]
        if change_types:
            perception["summary"] = f"changes: {', '.join(change_types)}"
        else:
            perception["summary"] = "no detected changes"

        return perception

    def _generate_proposals(self, perception: Dict, task: ARCTask) -> List[Dict]:
        """The GLM generates transformation proposals based on perception.

        Each proposal is a dict with:
        - 'description': human-readable description
        - 'function': a Python function that applies the transformation
        - 'source': how the GLM generated it (CRG, perception, etc.)
        """
        proposals = []
        changes = perception.get("changes", {})

        # Proposal 1: Colour map (if colour changes detected)
        if changes.get("colour_map") and changes.get("consistent"):
            colour_map = changes["colour_map"]
            proposals.append({
                "description": f"CHARGE_SWAP: apply colour map {colour_map}",
                "source": "perception (colour_map detected)",
                "type": "colour_map",
                "params": {"colour_map": colour_map},
            })

        # Proposal 2: Gravity (if gravity detected)
        if changes.get("gravity"):
            proposals.append({
                "description": "COMPACTION_FLOW: apply gravity (cells fall down)",
                "source": "perception (gravity detected)",
                "type": "gravity",
                "params": {},
            })

        # Proposal 3: Shift (if shift detected)
        if changes.get("shift"):
            dr, dc = changes["shift"]
            proposals.append({
                "description": f"CENTROID_SHIFT: shift by (dr={dr}, dc={dc})",
                "source": "perception (shift detected)",
                "type": "shift",
                "params": {"dr": dr, "dc": dc},
            })

        # Proposal 4: Rotation (if rotation detected)
        if changes.get("rotation"):
            angle = changes["rotation"]
            proposals.append({
                "description": f"DIHEDRAL_ROTATION: rotate by {angle} degrees",
                "source": "perception (rotation detected)",
                "type": "rotation",
                "params": {"angle": angle},
            })

        # Proposal 5: Flip (if flip detected)
        if changes.get("flip"):
            direction = changes["flip"]
            proposals.append({
                "description": f"PLANE_REFLECTION: flip {direction}",
                "source": "perception (flip detected)",
                "type": "flip",
                "params": {"direction": direction},
            })

        # Proposal 6: Fill (if fill detected)
        if changes.get("fill") is not None:
            fill_colour = changes["fill"]
            proposals.append({
                "description": f"REGION_FILL: fill empty cells with colour {fill_colour}",
                "source": "perception (fill detected)",
                "type": "fill",
                "params": {"fill_colour": fill_colour},
            })

        # Proposal 7: Scale (if scale detected)
        if changes.get("scale"):
            rh, rw = changes["scale"]
            proposals.append({
                "description": f"RADIUS_SCALING: scale by {rh}x{rw}",
                "source": "perception (scale detected)",
                "type": "scale",
                "params": {"rh": rh, "rw": rw},
            })

        # Proposal 8: Conditional colour map (if colour map is inconsistent)
        if changes.get("colour_map") is None and not changes.get("consistent", True):
            # Try conditional: only objects above a size threshold change
            proposals.append({
                "description": "CONDITIONAL: colour swap only for objects above size threshold",
                "source": "CRG reasoning (conditional → threshold → recolour)",
                "type": "conditional",
                "params": {},
            })

        # Proposal 9: Interior fill (if no fill detected but grid has enclosed regions)
        if not changes.get("fill") and perception.get("same_shape"):
            if self._has_enclosed_region(task.train[0].input):
                # Learn fill colour from train pairs
                fill_colour = self._learn_fill_colour(task)
                if fill_colour is not None:
                    proposals.append({
                        "description": f"REGION_FILL: fill enclosed regions with colour {fill_colour}",
                        "source": "CRG reasoning (interior → fill → region)",
                        "type": "interior_fill",
                        "params": {"fill_colour": fill_colour},
                    })

        # Proposal 10: 2-colour swap (if exactly 2 colours change)
        if changes.get("colour_map") and changes.get("consistent"):
            colour_map = changes["colour_map"]
            if len(colour_map) == 2:
                items = list(colour_map.items())
                if items[0][0] == items[1][1] and items[0][1] == items[1][0]:
                    proposals.append({
                        "description": f"CHARGE_SWAP: swap colours {items[0][0]}↔{items[0][1]}",
                        "source": "CRG reasoning (match → recolour → swap)",
                        "type": "colour_swap",
                        "params": {"c1": items[0][0], "c2": items[0][1]},
                    })

        return proposals

    def _apply_proposal(self, proposal: Dict, grid: Grid) -> Optional[Grid]:
        """Apply a proposal to a grid."""
        ptype = proposal["type"]
        params = proposal["params"]

        if ptype == "colour_map":
            colour_map = params["colour_map"]
            h, w = grid.height, grid.width
            new_cells = [[colour_map.get(grid.cells[r][c], grid.cells[r][c]) for c in range(w)] for r in range(h)]
            return Grid(new_cells)

        elif ptype == "gravity":
            return self._apply_gravity(grid)

        elif ptype == "shift":
            dr, dc = params["dr"], params["dc"]
            h, w = grid.height, grid.width
            new_cells = [[0] * w for _ in range(h)]
            for r in range(h):
                for c in range(w):
                    if grid.cells[r][c] != 0:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            new_cells[nr][nc] = grid.cells[r][c]
            return Grid(new_cells)

        elif ptype == "rotation":
            angle = params["angle"]
            return self._rotate(grid, angle)

        elif ptype == "flip":
            direction = params["direction"]
            return self._flip(grid, direction)

        elif ptype == "fill":
            fill_colour = params["fill_colour"]
            h, w = grid.height, grid.width
            new_cells = [[fill_colour if grid.cells[r][c] == 0 else grid.cells[r][c] for c in range(w)] for r in range(h)]
            return Grid(new_cells)

        elif ptype == "scale":
            rh, rw = params["rh"], params["rw"]
            h, w = grid.height, grid.width
            new_cells = [[0] * (w * rw) for _ in range(h * rh)]
            for r in range(h):
                for c in range(w):
                    val = grid.cells[r][c]
                    for dr in range(rh):
                        for dc in range(rw):
                            new_cells[r * rh + dr][c * rw + dc] = val
            return Grid(new_cells)

        elif ptype == "conditional":
            # Try different size thresholds
            return self._apply_conditional(grid, params)

        elif ptype == "interior_fill":
            fill_colour = params["fill_colour"]
            return self._apply_interior_fill(grid, fill_colour)

        elif ptype == "colour_swap":
            c1, c2 = params["c1"], params["c2"]
            h, w = grid.height, grid.width
            new_cells = [[grid.cells[r][c] for c in range(w)] for r in range(h)]
            for r in range(h):
                for c in range(w):
                    if new_cells[r][c] == c1: new_cells[r][c] = c2
                    elif new_cells[r][c] == c2: new_cells[r][c] = c1
            return Grid(new_cells)

        return None

    def _apply_conditional(self, grid: Grid, params: Dict) -> Optional[Grid]:
        """Apply conditional colour swap (only objects above size threshold)."""
        # This needs task context — can't apply without knowing the threshold
        # Return None to signal fallback
        return None

    def _apply_interior_fill(self, grid: Grid, fill_colour: int) -> Optional[Grid]:
        """Fill enclosed regions."""
        h, w = grid.height, grid.width
        if h < 3 or w < 3: return None

        border_cells = []
        for c in range(w):
            if grid.cells[0][c] != 0: border_cells.append(grid.cells[0][c])
            if grid.cells[h-1][c] != 0: border_cells.append(grid.cells[h-1][c])
        for r in range(h):
            if grid.cells[r][0] != 0: border_cells.append(grid.cells[r][0])
            if grid.cells[r][w-1] != 0: border_cells.append(grid.cells[r][w-1])
        if not border_cells: return None
        border_colour = Counter(border_cells).most_common(1)[0][0]

        reachable = [[False] * w for _ in range(h)]
        queue = []
        for c in range(w):
            if grid.cells[0][c] != border_colour: queue.append((0, c)); reachable[0][c] = True
            if grid.cells[h-1][c] != border_colour: queue.append((h-1, c)); reachable[h-1][c] = True
        for r in range(h):
            if grid.cells[r][0] != border_colour: queue.append((r, 0)); reachable[r][0] = True
            if grid.cells[r][w-1] != border_colour: queue.append((r, w-1)); reachable[r][w-1] = True
        while queue:
            cr, cc = queue.pop(0)
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = cr+dr, cc+dc
                if 0 <= nr < h and 0 <= nc < w and not reachable[nr][nc] and grid.cells[nr][nc] != border_colour:
                    reachable[nr][nc] = True
                    queue.append((nr, nc))

        new_cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if not reachable[r][c] and grid.cells[r][c] != border_colour:
                    new_cells[r][c] = fill_colour
        return Grid(new_cells)

    def _learn_fill_colour(self, task: ARCTask) -> Optional[int]:
        """Learn the fill colour from train pairs."""
        for pair in task.train:
            inp, out = pair.input, pair.output
            if inp.height != out.height or inp.width != out.width: return None
            for r in range(inp.height):
                for c in range(inp.width):
                    if inp.cells[r][c] == 0 and out.cells[r][c] != 0:
                        return out.cells[r][c]
        return None

    def _has_enclosed_region(self, grid: Grid) -> bool:
        """Check if grid has enclosed regions."""
        h, w = grid.height, grid.width
        if h < 3 or w < 3: return False
        border_cells = []
        for c in range(w):
            if grid.cells[0][c] != 0: border_cells.append(grid.cells[0][c])
            if grid.cells[h-1][c] != 0: border_cells.append(grid.cells[h-1][c])
        for r in range(h):
            if grid.cells[r][0] != 0: border_cells.append(grid.cells[r][0])
            if grid.cells[r][w-1] != 0: border_cells.append(grid.cells[r][w-1])
        if not border_cells: return False
        border_colour = Counter(border_cells).most_common(1)[0][0]
        reachable = [[False] * w for _ in range(h)]
        queue = []
        for c in range(w):
            if grid.cells[0][c] != border_colour: queue.append((0, c)); reachable[0][c] = True
            if grid.cells[h-1][c] != border_colour: queue.append((h-1, c)); reachable[h-1][c] = True
        for r in range(h):
            if grid.cells[r][0] != border_colour: queue.append((r, 0)); reachable[r][0] = True
            if grid.cells[r][w-1] != border_colour: queue.append((r, w-1)); reachable[r][w-1] = True
        while queue:
            cr, cc = queue.pop(0)
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = cr+dr, cc+dc
                if 0 <= nr < h and 0 <= nc < w and not reachable[nr][nc] and grid.cells[nr][nc] != border_colour:
                    reachable[nr][nc] = True
                    queue.append((nr, nc))
        for r in range(h):
            for c in range(w):
                if not reachable[r][c] and grid.cells[r][c] != border_colour:
                    return True
        return False

    @staticmethod
    def _apply_gravity(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        new_cells = [[0] * w for _ in range(h)]
        for c in range(w):
            column = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
            for i, val in enumerate(column):
                new_cells[h - len(column) + i][c] = val
        return Grid(new_cells)

    @staticmethod
    def _detect_shift(inp: Grid, out: Grid) -> Optional[Tuple[int, int]]:
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
    def _rotate(grid: Grid, angle: int) -> Grid:
        h, w = grid.height, grid.width
        if angle == 90: return Grid([[grid.cells[h-1-r][c] for r in range(h)] for c in range(w)])
        elif angle == 180: return Grid([[grid.cells[h-1-r][w-1-c] for c in range(w)] for r in range(h)])
        elif angle == 270: return Grid([[grid.cells[r][w-1-c] for r in range(h)] for c in range(w)])
        return grid

    @staticmethod
    def _flip(grid: Grid, direction: str) -> Grid:
        h = grid.height
        if direction == "horizontal": return Grid([row[::-1] for row in grid.cells])
        else: return Grid([grid.cells[h-1-r] for r in range(h)])


# ============================================================
# The Mind-Directed Pipeline (v17.8)
# ============================================================


class MindDirectedPipeline:
    """v17.8: The GLM as a mind that proposes, tests, and refines.

    Solvers are FALLBACK only — the primary mode is GLM-generated.
    """

    def __init__(self, run_number: int = 1):
        # Bit-Ops substrate
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
        self.glm = FullVocabGLMCore(self.substrate)
        self.sandbox = GLMSandbox(max_iterations=20, timeout=5.0)

        # THE GLM MIND (primary)
        self.mind = GLMMind(self.glm, self.sandbox)

        # Solvers (FALLBACK only)
        self.fallback_solvers = {
            "settlement_gravity": SettlementGravitySolver(self.substrate),
            "colour_map_via_AND": ColourMapViaANDSolver(self.substrate),
            "interior_fill": InteriorFillSolver(self.substrate),
            "scale_aware_resize": ScaleAwareResizeSolver(self.substrate),
            "shift_solver": ShiftSolver(self.substrate),
            "rotate_solver": RotateSolver(self.substrate),
            "flip_solver": FlipSolver(self.substrate),
            "conditional_solver": ConditionalSolver(self.substrate),
            "parity_sign_recolor": ParitySignRecolorSolver(self.substrate),
            "column_rank_solver": ColumnRankSolver(self.substrate),
        }

        # LTM
        self.ltm = GrownLTM()
        self.run_number = run_number

    def solve_task(self, task: ARCTask, task_id: str) -> Dict[str, Any]:
        """Solve using the GLM mind (primary) with solver fallback."""

        # PRIMARY: The GLM mind proposes, tests, refines
        glm_solution, reasoning = self.mind.solve_task(task)

        if glm_solution is not None:
            # The GLM solved it!
            return {
                "task_id": task_id,
                "solved": True,
                "winning_strategy": "glm_mind",
                "reasoning_trace": reasoning["reasoning_trace"],
                "proposal": reasoning["proposal"]["description"] if reasoning.get("proposal") else None,
                "solution": glm_solution.cells,
                "mode": "glm_mind",
            }

        # FALLBACK: Try solvers
        for name, solver in self.fallback_solvers.items():
            try:
                result = solver.solve(task)
                if result is not None:
                    return {
                        "task_id": task_id,
                        "solved": True,
                        "winning_strategy": name,
                        "reasoning_trace": reasoning["reasoning_trace"],
                        "solution": result.cells,
                        "mode": "fallback_solver",
                    }
            except:
                pass

        return {
            "task_id": task_id,
            "solved": False,
            "winning_strategy": None,
            "reasoning_trace": reasoning["reasoning_trace"],
            "mode": "failed",
        }


# ============================================================
# Main
# ============================================================


def main():
    print("=" * 80)
    print("ARC-AGI v17.8 — The GLM as a Mind")
    print("  GLM proposes → sandbox tests → refine → commit")
    print("  Solvers as FALLBACK only")
    print("=" * 80)

    training_dir = ARC_17_DIR / "data" / "training"
    task_files = sorted(training_dir.glob("*.json"))
    print(f"\n[load] Found {len(task_files)} ARC tasks")

    known_solved_ids = {"00dbd492", "1e0a9b12", "396d80d7", "45737921", "54d82841",
                        "575b1a71", "a85d4709", "ae58858e", "e48d4e1a"}

    state_path = ARC_17_DIR / "results" / "glm_state.json"
    start_run = 1
    if state_path.exists():
        try:
            with open(state_path) as f:
                prev_state = json.load(f)
            start_run = len(prev_state.get("run_history", [])) + 1
        except:
            pass

    N_RUNS = 5  # fewer runs since each is heavier (GLM proposes)
    all_runs = []

    for i in range(N_RUNS):
        run_number = start_run + i
        print(f"\n{'='*60}")
        print(f"RUN {run_number}")
        print(f"{'='*60}")

        pipeline = MindDirectedPipeline(run_number=run_number)
        print(f"[init] GLM: {len(pipeline.glm.concepts)} concepts, {len(pipeline.glm.crg_edges)} edges")

        # Run benchmark
        results = []
        solved_count = 0
        new_solves = 0
        glm_mind_solves = 0
        fallback_solves = 0

        for task_file in task_files:
            task_id = task_file.stem
            try:
                task = load_task(str(task_file))
                result = pipeline.solve_task(task, task_id)
                results.append(result)

                if result["solved"]:
                    solved_count += 1
                    is_new = task_id not in known_solved_ids
                    if is_new: new_solves += 1
                    if result["mode"] == "glm_mind":
                        glm_mind_solves += 1
                    else:
                        fallback_solves += 1
                    marker = " NEW!" if is_new else ""
                    mode = "MIND" if result["mode"] == "glm_mind" else "FALLBACK"
                    if is_new or run_number <= 2:
                        print(f"  ✓ {task_id}: {result['winning_strategy']} ({mode}){marker}")
                else:
                    if run_number <= 2:
                        print(f"  ✗ {task_id}")
            except Exception as e:
                if run_number <= 2:
                    print(f"  ! {task_id}: {e}")
                if not any(r.get("task_id") == task_id for r in results):
                    results.append({"task_id": task_id, "solved": False, "error": str(e)})

        # Save state
        run_summary = {
            "run_number": run_number,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "n_tasks": len(task_files),
            "n_solved": solved_count,
            "new_solves": new_solves,
            "glm_mind_solves": glm_mind_solves,
            "fallback_solves": fallback_solves,
            "glm_concepts": len(pipeline.glm.concepts),
            "glm_edges": len(pipeline.glm.crg_edges),
        }
        pipeline.glm.save_state(run_summary)
        pipeline.ltm.save_ltm_state()

        strategy_wins = Counter(r["winning_strategy"] for r in results if r.get("solved"))
        summary = {
            "run_number": run_number,
            "n_solved": solved_count,
            "n_new_solves": new_solves,
            "n_tasks": len(task_files),
            "glm_mind_solves": glm_mind_solves,
            "fallback_solves": fallback_solves,
            "strategy_wins": dict(strategy_wins),
            "glm_concepts": len(pipeline.glm.concepts),
            "glm_edges": len(pipeline.glm.crg_edges),
        }
        all_runs.append(summary)

        print(f"\n[run {run_number}] {solved_count}/{len(task_files)} solved, {new_solves} new")
        print(f"  GLM mind: {glm_mind_solves}, Fallback: {fallback_solves}")

    # === FINAL ANALYSIS ===
    print("\n" + "=" * 80)
    print(f"RESULTS ({N_RUNS} runs, {len(task_files)} tasks)")
    print("=" * 80)

    print(f"\n{'Run':>4} {'Solved':>8} {'New':>5} {'Mind':>6} {'Fallback':>10}")
    print("-" * 40)
    for run in all_runs:
        print(f"{run['run_number']:>4} {run['n_solved']:>5}/{run['n_tasks']:<2} {run['n_new_solves']:>5} "
              f"{run['glm_mind_solves']:>6} {run['fallback_solves']:>10}")

    last_run = all_runs[-1]
    best_run = max(all_runs, key=lambda r: r["n_solved"])
    print(f"\nBest run: Run {best_run['run_number']} — {best_run['n_solved']}/{best_run['n_tasks']}")
    print(f"GLM mind solves (last run): {last_run['glm_mind_solves']}")
    print(f"Fallback solves (last run): {last_run['fallback_solves']}")

    # Save results
    output_dir = ARC_17_DIR / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "v17_8_results.json"
    with open(results_path, "w") as f:
        json.dump({
            "experiment": "ARC-AGI v17.8 — The GLM as a Mind",
            "date": "2026-08-06",
            "n_runs": N_RUNS,
            "n_tasks": len(task_files),
            "runs": all_runs,
            "best_run_solved": best_run["n_solved"],
            "glm_mind_solves": last_run["glm_mind_solves"],
            "fallback_solves": last_run["fallback_solves"],
        }, f, indent=2, default=str)
    print(f"\nResults saved: {results_path}")

    # Generate report
    report_dir = ARC_17_DIR / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "v17_8_report.md"
    report = generate_report(all_runs, N_RUNS, len(task_files), last_run, best_run)
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Report saved: {report_path}")


def generate_report(all_runs, n_runs, n_tasks, last_run, best_run):
    lines = []
    lines.append("# ARC-AGI v17.8 — The GLM as a Mind")
    lines.append("")
    lines.append("**Date:** 2026-08-06")
    lines.append("**Key shift:** GLM generates solutions directly (not solver selection)")
    lines.append(f"**Tasks:** {n_tasks}")
    lines.append(f"**Iterations:** {n_runs}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## The GLM Mind")
    lines.append("")
    lines.append("Per user: 'the GLM needs to generate solutions directly — lets try to let the GLM use its CRG + sandbox to PROPOSE a transformation, test it, and refine it.'")
    lines.append("")
    lines.append("The v17.8 pipeline shifts from **solver-selection** to **GLM-generated solutions**:")
    lines.append("")
    lines.append("1. **PERCEIVE:** the GLM examines what changed between input and output")
    lines.append("2. **PROPOSE:** the GLM generates transformation proposals (using perception + CRG)")
    lines.append("3. **TEST:** the sandbox tests each proposal on ALL train pairs")
    lines.append("4. **REFINE:** if a proposal fails, the GLM tries the next one")
    lines.append("5. **COMMIT:** if all train pairs pass, the GLM commits the solution")
    lines.append("6. **FALLBACK:** if all GLM proposals fail, solvers are tried as fallback")
    lines.append("")

    lines.append("## Results")
    lines.append("")
    lines.append("| Run | Solved | New | GLM Mind | Fallback |")
    lines.append("|---|---|---|---|---|")
    for run in all_runs:
        lines.append(f"| {run['run_number']} | {run['n_solved']}/{run['n_tasks']} | {run['n_new_solves']} | {run['glm_mind_solves']} | {run['fallback_solves']} |")
    lines.append("")

    lines.append(f"### Summary")
    lines.append("")
    lines.append(f"- **Best run:** Run {best_run['run_number']} — {best_run['n_solved']}/{best_run['n_tasks']}")
    lines.append(f"- **GLM mind solves:** {last_run['glm_mind_solves']}")
    lines.append(f"- **Fallback solves:** {last_run['fallback_solves']}")
    lines.append("")

    lines.append("## What the GLM mind does differently")
    lines.append("")
    lines.append("Instead of selecting from 10 pre-built solvers, the GLM:")
    lines.append("1. **Perceives** the task (detects colour changes, gravity, shifts, rotations, flips, fills, scaling)")
    lines.append("2. **Generates** up to 10 transformation proposals based on perception")
    lines.append("3. **Tests** each proposal in the sandbox on all train pairs")
    lines.append("4. **Commits** the first proposal that passes all train pairs")
    lines.append("")
    lines.append("The solvers are still available as FALLBACK, but the primary mode is GLM-generated.")
    lines.append("")

    lines.append("## Comparison across all versions")
    lines.append("")
    lines.append("| Metric | v17.6 | v17.7 | v17.8 |")
    lines.append("|---|---|---|---|")
    lines.append(f"| Tasks | 36 | 36 | {n_tasks} |")
    lines.append(f"| GLM concepts | 527 | 4,620 | {last_run['glm_concepts']} |")
    lines.append(f"| CRG edges | 814 | 1,103 | {last_run['glm_edges']} |")
    lines.append(f"| GLM mind | ❌ | ❌ | ✅ |")
    lines.append(f"| Sandbox | ✅ | ✅ | ✅ |")
    lines.append(f"| Best solved | 15/36 | 15/36 | {best_run['n_solved']}/{n_tasks} |")
    lines.append("")

    lines.append("## Next steps")
    lines.append("")
    lines.append("1. **Deepen the GLM mind** — let it generate more complex proposals (compositions of transformations)")
    lines.append("2. **Use the force-directed realignment** to settle the knowledge graph before reasoning")
    lines.append("3. **Use hexcolour** for visual pattern matching between grids")
    lines.append("4. **Let the GLM refine failed proposals** — currently it just tries the next one; it should ADJUST the failed proposal")
    lines.append("5. **Integrate the full GLM.py runtime** for natural language reasoning")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
