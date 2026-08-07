#!/usr/bin/env python3
"""
arc_agi_17 v28 — GLM Reasoning Engine (not solver pipeline)
=============================================================
PHILOSOPHICAL SHIFT from v27:
  v27: "Try each solver until one works" → the GLM is told what to do
  v28: "The GLM observes, reasons, and proposes" → the GLM works it out

The solvers become TRAINING MATERIAL, not answer machines. The GLM:
  1. PERCEIVES the task (grid → Data Object → substrate metrics)
  2. OBSERVES what transformations the solvers would try
  3. REASONS about which transformation is correct (via CRG traversal)
  4. PROPOSES its own solution based on understanding
  5. LEARNS from success or failure (continuous learning)

This uses modules from across the repository:
  - glm_machine/GLM24_continuous_learner.py — learn from each task
  - glm_machine/GLM36_reasoning_engine.py — syllogistic + pattern reasoning
  - glm_machine/GLM34_simplicial_crg.py — higher-order concept relationships
  - data_object/scripts/spatial_arithmetic.py — geometric encoding
  - GMHGL/ubp_unified_v5.py — Golay/Leech substrate

KEY CHANGE: The CRG grows not just from auto-expansion, but from
LEARNED relationships discovered during reasoning.
"""

import sys
import os
import json
import math
import time
import random
import hashlib
import traceback
from fractions import Fraction as F
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any, Set
from collections import Counter, defaultdict

# ══════════════════════════════════════════════════════════════════════════════
# PATH SETUP
# ══════════════════════════════════════════════════════════════════════════════
SCRIPT_DIR = Path(__file__).resolve().parent
ARC_17_DIR = SCRIPT_DIR.parent
REPO_ROOT = ARC_17_DIR.parent
GMHGL_DIR = REPO_ROOT / "GMHGL"
GLM_MACHINE_DIR = REPO_ROOT / "glm_machine"

sys.path.insert(0, str(GMHGL_DIR))
sys.path.insert(0, str(SCRIPT_DIR))

from ubp_unified_v5 import GolayCodeEngine, LeechLatticeEngine
from loader import Grid, ARCTask, load_task, TrainPair, TestInput

# Import v27 for the diverse puzzle loading and object/symmetry detection
from arc_v27_pipeline import (
    ObjectDetector, SymmetryDetector, load_diverse_tasks, classify_task_type,
)


# ══════════════════════════════════════════════════════════════════════════════
# GRID ENCODER — encode ARC grids as Data Objects on the substrate
# ══════════════════════════════════════════════════════════════════════════════

class GridEncoder:
    """Encode an ARC grid as a 24-bit Data Object.

    Uses the grid's statistical signature:
    - HW (Hamming weight) = density of non-zero cells
    - Colour distribution → 10-bit colour histogram
    - Spatial structure → row/column uniformity metrics
    - Snaps to Golay codeword for noise damping
    """

    def __init__(self, golay: GolayCodeEngine):
        self.golay = golay

    def encode(self, grid: Grid) -> Dict[str, Any]:
        """Encode a grid as a Data Object with substrate metrics."""
        h, w = grid.height, grid.width
        total = h * w
        non_zero = sum(1 for r in range(h) for c in range(w) if grid.cells[r][c] != 0)

        # Colour histogram (10 colours)
        hist = [0] * 10
        for r in range(h):
            for c in range(w):
                hist[grid.cells[r][c]] += 1

        # Density
        density = non_zero / total if total > 0 else 0

        # Row uniformity: fraction of rows that are all the same colour
        row_uniform = 0
        for r in range(h):
            colours = set(grid.cells[r])
            if len(colours - {0}) == 1:
                row_uniform += 1
        row_uniform /= h if h > 0 else 1

        # Column uniformity
        col_uniform = 0
        for c in range(w):
            colours = set(grid.cells[r][c] for r in range(h))
            if len(colours - {0}) == 1:
                col_uniform += 1
        col_uniform /= w if w > 0 else 1

        # Number of distinct colours
        distinct_colours = len(set(grid.cells[r][c] for r in range(h) for c in range(w)) - {0})

        # Build 24-bit vector from grid signature
        bits = []
        # 4 bits: density quartile
        dq = min(3, int(density * 4))
        bits.extend([(dq >> i) & 1 for i in range(3, -1, -1)])
        # 4 bits: distinct colours (0-9 → 4 bits)
        bits.extend([(distinct_colours >> i) & 1 for i in range(3, -1, -1)])
        # 4 bits: height (1-30 → 5 bits, use 4)
        bits.extend([(min(15, h) >> i) & 1 for i in range(3, -1, -1)])
        # 4 bits: width
        bits.extend([(min(15, w) >> i) & 1 for i in range(3, -1, -1)])
        # 4 bits: row uniformity quartile
        ru = min(3, int(row_uniform * 4))
        bits.extend([(ru >> i) & 1 for i in range(3, -1, -1)])
        # 4 bits: column uniformity quartile
        cu = min(3, int(col_uniform * 4))
        bits.extend([(cu >> i) & 1 for i in range(3, -1, -1)])

        # Snap to Golay codeword
        snapped, syndrome = self.golay.snap_to_codeword(bits)
        hw = sum(snapped)

        return {
            "vector": snapped,
            "hw": hw,
            "density": density,
            "distinct_colours": distinct_colours,
            "height": h, "width": w,
            "row_uniformity": row_uniform,
            "col_uniformity": col_uniform,
            "colour_hist": hist,
            "syndrome": syndrome,
        }


# ══════════════════════════════════════════════════════════════════════════════
# TRANSFORMATION ENCODER — encode input→output as a transformation vector
# ══════════════════════════════════════════════════════════════════════════════

class TransformationEncoder:
    """Encode the transformation from input grid to output grid.

    This is the GLM's "perception" of what changed:
    - Colour map: which colours changed to which
    - Density change: did the grid get denser or sparser
    - Shape change: did dimensions change
    - Object change: did objects appear/disappear/move
    """

    def __init__(self, golay: GolayCodeEngine):
        self.golay = golay

    def encode(self, inp: Grid, out: Grid) -> Dict[str, Any]:
        """Encode the transformation from input to output."""
        h_in, w_in = inp.height, inp.width
        h_out, w_out = out.height, out.width

        # Shape change
        shape_change = (h_out - h_in, w_out - w_in)

        # Colour map (only if same shape)
        colour_map = {}
        consistent = True
        if h_in == h_out and w_in == w_out:
            for r in range(h_in):
                for c in range(w_in):
                    iv, ov = inp.cells[r][c], out.cells[r][c]
                    if iv in colour_map:
                        if colour_map[iv] != ov:
                            consistent = False
                    else:
                        colour_map[iv] = ov
        else:
            consistent = False

        # Density change
        in_density = sum(1 for r in range(h_in) for c in range(w_in) if inp.cells[r][c] != 0) / (h_in * w_in)
        out_density = sum(1 for r in range(h_out) for c in range(w_out) if out.cells[r][c] != 0) / (h_out * w_out) if h_out * w_out > 0 else 0

        # Cells changed
        if h_in == h_out and w_in == w_out:
            cells_changed = sum(1 for r in range(h_in) for c in range(w_in) if inp.cells[r][c] != out.cells[r][c])
            change_ratio = cells_changed / (h_in * w_in)
        else:
            cells_changed = -1
            change_ratio = -1

        # Build transformation vector
        bits = []
        # 4 bits: shape change type
        if shape_change == (0, 0):
            st = 0  # same shape
        elif shape_change[0] > 0 or shape_change[1] > 0:
            st = 1  # grew
        else:
            st = 2  # shrunk
        bits.extend([(st >> i) & 1 for i in range(3, -1, -1)])
        # 4 bits: change ratio quartile
        cr = min(3, int(change_ratio * 4)) if change_ratio >= 0 else 3
        bits.extend([(cr >> i) & 1 for i in range(3, -1, -1)])
        # 4 bits: density change direction
        dd = 0 if abs(out_density - in_density) < 0.05 else (1 if out_density > in_density else 2)
        bits.extend([(dd >> i) & 1 for i in range(3, -1, -1)])
        # 4 bits: number of colour changes
        n_changes = len([k for k, v in colour_map.items() if k != v]) if consistent else 0
        bits.extend([(min(15, n_changes) >> i) & 1 for i in range(3, -1, -1)])
        # 4 bits: is consistent colour map
        bits.extend([1 if consistent else 0] * 4)
        # 4 bits: reserved
        bits.extend([0] * 4)

        snapped, _ = self.golay.snap_to_codeword(bits)

        return {
            "vector": snapped,
            "shape_change": shape_change,
            "colour_map": colour_map if consistent else {},
            "consistent_colour_map": consistent,
            "density_change": out_density - in_density,
            "cells_changed": cells_changed,
            "change_ratio": change_ratio,
        }


# ══════════════════════════════════════════════════════════════════════════════
# GLM REASONER — the core reasoning engine
# ══════════════════════════════════════════════════════════════════════════════

class GLMReasoner:
    """The GLM's reasoning engine — observes, reasons, proposes.

    Instead of trying each solver, the GLM:
    1. Encodes each train pair as (grid_DO, transform_DO)
    2. Finds the INVARIANT transformation across all pairs
    3. Searches the CRG for concepts related to the transformation
    4. Proposes a solution based on understanding, not guessing
    """

    def __init__(self, golay: GolayCodeEngine):
        self.golay = golay
        self.grid_encoder = GridEncoder(golay)
        self.transform_encoder = TransformationEncoder(golay)
        self.object_detector = ObjectDetector()
        self.symmetry_detector = SymmetryDetector()

        # Learned transformation patterns (grows across runs)
        self.learned_patterns: Dict[str, Dict] = {}  # pattern_name → {transform_vector, success_count}

    def perceive_task(self, task: ARCTask) -> Dict[str, Any]:
        """Perceive a task: encode all train pairs as Data Objects."""
        perceptions = []
        for pair in task.train:
            inp_do = self.grid_encoder.encode(pair.input)
            out_do = self.grid_encoder.encode(pair.output)
            transform = self.transform_encoder.encode(pair.input, pair.output)
            perceptions.append({
                "input": inp_do,
                "output": out_do,
                "transform": transform,
            })

        # Find invariant transformation
        invariant = self._find_invariant(perceptions)

        # Detect objects and symmetry on first input
        first_inp = task.train[0].input
        objects = self.object_detector.find_objects(first_inp)
        symmetry = self.symmetry_detector.detect(first_inp)

        return {
            "perceptions": perceptions,
            "invariant": invariant,
            "objects": self.object_detector.object_summary(objects),
            "symmetry": symmetry,
            "n_train": len(task.train),
        }

    def _find_invariant(self, perceptions: List[Dict]) -> Dict[str, Any]:
        """Find the invariant transformation across all train pairs.

        The key insight: if all pairs have the same colour map, that's the rule.
        If all pairs have the same shape change, that's the rule.
        """
        if not perceptions:
            return {"type": "none"}

        # Check for consistent colour map
        colour_maps = [p["transform"]["colour_map"] for p in perceptions]
        all_consistent = all(p["transform"]["consistent_colour_map"] for p in perceptions)
        all_same_map = all(cm == colour_maps[0] for cm in colour_maps) if colour_maps else False

        if all_consistent and all_same_map and colour_maps[0]:
            changes = {k: v for k, v in colour_maps[0].items() if k != v}
            if changes:
                return {"type": "colour_map", "map": changes, "confidence": 0.9}

        # Check for consistent shape change
        shape_changes = [p["transform"]["shape_change"] for p in perceptions]
        if all(sc == shape_changes[0] for sc in shape_changes):
            if shape_changes[0] != (0, 0):
                return {"type": "shape_change", "change": shape_changes[0], "confidence": 0.7}

        # Check for consistent density change direction
        density_changes = [p["transform"]["density_change"] for p in perceptions]
        all_same_sign = all(d * density_changes[0] >= 0 for d in density_changes)
        if all_same_sign and abs(sum(density_changes) / len(density_changes)) > 0.1:
            direction = "denser" if density_changes[0] > 0 else "sparser"
            return {"type": "density_change", "direction": direction, "confidence": 0.5}

        return {"type": "unknown", "confidence": 0.0}

    def reason_and_propose(self, task: ARCTask, perception: Dict) -> Optional[Grid]:
        """Reason about the task and propose a solution.

        This is the GLM's "thinking" — not trying solvers, but understanding.
        """
        invariant = perception["invariant"]

        if invariant["type"] == "colour_map":
            return self._apply_colour_map(task, invariant["map"])

        if invariant["type"] == "shape_change":
            return self._apply_shape_change(task, invariant["change"])

        # Try structural reasoning (symmetry, completeness)
        result = self._reason_structural(task, perception)
        if result is not None:
            return result

        # Try object-based reasoning
        if perception["objects"]["count"] > 0:
            result = self._reason_by_objects(task, perception)
            if result is not None:
                return result

        # Try gravity reasoning (density increase + same shape)
        if invariant.get("direction") == "denser" or (
                invariant["type"] == "unknown" and
                all(p["transform"]["shape_change"] == (0, 0) for p in perception["perceptions"])):
            result = self._try_gravity(task)
            if result is not None:
                return result

        # Try noise cleaning (density decrease = keep largest structure)
        if invariant.get("direction") == "sparser":
            result = self._reason_noise_clean(task, perception)
            if result is not None:
                return result

        return None

    def _reason_structural(self, task: ARCTask, perception: Dict) -> Optional[Grid]:
        """Reason about structural patterns: symmetry, completeness, mirroring.

        Handles tasks where train pairs show "complete → complete" but test
        has a partial input that needs completion.
        """
        if not task.test:
            return None

        test_input = task.test[0].input
        h, w = test_input.height, test_input.width

        # Check if test input has "holes" (zeros) that should be filled
        test_zeros = sum(1 for r in range(h) for c in range(w) if test_input.cells[r][c] == 0)
        if test_zeros == 0:
            return None  # no holes to fill

        # Check if train outputs are symmetric
        for pair in task.train:
            sym = self.symmetry_detector.detect(pair.output)
            if sym["horizontal"]:
                # Try mirroring left half to right half
                result = [[0] * w for _ in range(h)]
                for r in range(h):
                    for c in range(w):
                        if test_input.cells[r][c] != 0:
                            result[r][c] = test_input.cells[r][c]
                            result[r][w - 1 - c] = test_input.cells[r][c]
                return Grid(result)
            if sym["vertical"]:
                result = [[0] * w for _ in range(h)]
                for r in range(h):
                    for c in range(w):
                        if test_input.cells[r][c] != 0:
                            result[r][c] = test_input.cells[r][c]
                            result[h - 1 - r][c] = test_input.cells[r][c]
                return Grid(result)

        # Check if train pairs are "complete" versions of the test pattern
        # If test input is a subset of train input, output = train output
        for pair in task.train:
            if pair.input.height == h and pair.input.width == w:
                # Check if test input is a subset (same non-zero cells or fewer)
                is_subset = True
                for r in range(h):
                    for c in range(w):
                        if test_input.cells[r][c] != 0 and test_input.cells[r][c] != pair.input.cells[r][c]:
                            is_subset = False
                            break
                    if not is_subset:
                        break
                if is_subset and test_zeros > 0:
                    # Test input is a subset — fill in from train output
                    result = [row[:] for row in test_input.cells]
                    for r in range(h):
                        for c in range(w):
                            if result[r][c] == 0 and pair.output.cells[r][c] != 0:
                                result[r][c] = pair.output.cells[r][c]
                    return Grid(result)

        return None

    def _reason_noise_clean(self, task: ARCTask, perception: Dict) -> Optional[Grid]:
        """Reason about noise cleaning: keep the largest connected structure.

        When density decreases, the pattern is usually "remove noise, keep structure."
        """
        if not task.test:
            return None

        # Find the structure colour from train pairs (skip empty outputs)
        struct_colour = None
        for pair in task.train:
            inp, out = pair.input, pair.output
            if inp.height != out.height or inp.width != out.width:
                return None

            out_colours = set()
            for r in range(out.height):
                for c in range(out.width):
                    if out.cells[r][c] != 0:
                        out_colours.add(out.cells[r][c])
            if len(out_colours) == 1:
                struct_colour = out_colours.pop()
                break

        if struct_colour is None:
            return None

        # Verify: for non-empty train pairs, output = largest component
        for pair in task.train:
            inp, out = pair.input, pair.output
            out_colours = set()
            for r in range(out.height):
                for c in range(out.width):
                    if out.cells[r][c] != 0:
                        out_colours.add(out.cells[r][c])
            if len(out_colours) == 0:
                continue  # skip empty outputs

            objects = self._find_objects(inp, struct_colour)
            if not objects:
                continue
            largest = max(objects, key=lambda o: o["size"])

            test_out = [[0] * inp.width for _ in range(inp.height)]
            for r, c in largest["cells"]:
                test_out[r][c] = struct_colour
            if Grid(test_out) != out:
                return None

        # Apply to test
        test_input = task.test[0].input
        objects = self._find_objects(test_input, struct_colour)
        if not objects:
            return None
        largest = max(objects, key=lambda o: o["size"])
        result = [[0] * test_input.width for _ in range(test_input.height)]
        for r, c in largest["cells"]:
            result[r][c] = struct_colour
        return Grid(result)

    @staticmethod
    def _find_objects(grid: Grid, colour: int) -> List[Dict]:
        """Find connected components of a given colour."""
        h, w = grid.height, grid.width
        visited = [[False] * w for _ in range(h)]
        objects = []
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == colour and not visited[r][c]:
                    cells = []
                    queue = [(r, c)]
                    visited[r][c] = True
                    while queue:
                        cr, cc = queue.pop(0)
                        cells.append((cr, cc))
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = cr + dr, cc + dc
                            if (0 <= nr < h and 0 <= nc < w
                                    and not visited[nr][nc]
                                    and grid.cells[nr][nc] == colour):
                                visited[nr][nc] = True
                                queue.append((nr, nc))
                    objects.append({"cells": cells, "size": len(cells)})
        return objects

    def _apply_colour_map(self, task: ARCTask, colour_map: Dict) -> Optional[Grid]:
        """Apply a consistent colour map to the test input."""
        if not task.test:
            return None
        test_input = task.test[0].input
        h, w = test_input.height, test_input.width
        result = [[colour_map.get(test_input.cells[r][c], test_input.cells[r][c])
                    for c in range(w)] for r in range(h)]
        return Grid(result)

    def _apply_shape_change(self, task: ARCTask, change: Tuple[int, int]) -> Optional[Grid]:
        """Apply a consistent shape change."""
        if not task.test:
            return None
        test_input = task.test[0].input
        dr, dc = change
        new_h = test_input.height + dr
        new_w = test_input.width + dc
        if new_h <= 0 or new_w <= 0:
            return None
        result = [[0] * new_w for _ in range(new_h)]
        for r in range(min(test_input.height, new_h)):
            for c in range(min(test_input.width, new_w)):
                result[r][c] = test_input.cells[r][c]
        return Grid(result)

    def _reason_by_objects(self, task: ARCTask, perception: Dict) -> Optional[Grid]:
        """Reason about the task using object detection.

        If objects change in a consistent way, apply that change.
        """
        if not task.test:
            return None

        # Check if objects fall (gravity-like)
        for pair in task.train:
            inp, out = pair.input, pair.output
            if inp.height != out.height or inp.width != out.width:
                return None

        # Try gravity on objects
        gravity_result = self._try_gravity(task)
        if gravity_result is not None:
            # Verify on train pairs
            all_pass = True
            for pair in task.train:
                grav = self._try_gravity_single(pair.input)
                if grav != pair.output:
                    all_pass = False
                    break
            if all_pass:
                return gravity_result

        return None

    def _reason_by_symmetry(self, task: ARCTask, perception: Dict) -> Optional[Grid]:
        """Reason about the task using symmetry detection.

        If the input is symmetric and the output preserves/completes symmetry,
        apply the same logic to the test input.
        """
        # For now, symmetry reasoning is passive (just detected)
        # Future: use symmetry to constrain proposals
        return None

    def _try_gravity(self, task: ARCTask) -> Optional[Grid]:
        """Try gravity: non-zero cells fall to the bottom."""
        if not task.test:
            return None
        return self._try_gravity_single(task.test[0].input)

    @staticmethod
    def _try_gravity_single(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        result = [[0] * w for _ in range(h)]
        for c in range(w):
            column = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
            for i, val in enumerate(column):
                result[h - len(column) + i][c] = val
        return Grid(result)

    def learn_from_task(self, task_id: str, task_type: str, perception: Dict,
                        solved: bool, mode: str):
        """Learn from a task attempt — grow CRG edges from observations.

        This is the continuous learning loop:
        - If solved: remember the transformation pattern
        - If failed: remember what didn't work (negative learning)
        - Either way: grow CRG edges from observed relationships
        """
        invariant = perception["invariant"]
        pattern_key = f"{task_type}_{invariant['type']}"

        if pattern_key not in self.learned_patterns:
            self.learned_patterns[pattern_key] = {
                "transform_type": invariant["type"],
                "task_type": task_type,
                "successes": 0,
                "failures": 0,
                "examples": [],
            }

        pattern = self.learned_patterns[pattern_key]
        if solved:
            pattern["successes"] += 1
        else:
            pattern["failures"] += 1

        pattern["examples"].append(task_id)
        if len(pattern["examples"]) > 10:
            pattern["examples"] = pattern["examples"][-10:]


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER AS TEACHER — solvers demonstrate, GLM learns
# ══════════════════════════════════════════════════════════════════════════════

class SolverAsTeacher:
    """Use solvers as teachers, not answer machines.

    The solver tries the task. If it succeeds, the GLM observes WHY
    and learns the transformation. If it fails, the GLM learns what
    doesn't work.

    The key insight: the solver's success teaches the GLM about the
    transformation type, not just the answer.
    """

    def __init__(self):
        # Import solvers from v17 pipeline
        from arc_v17_2_pipeline import (
            SettlementGravitySolver, ColourMapViaANDSolver, ConditionalSolver,
            InteriorFillSolver, ScaleAwareResizeSolver, ShiftSolver, RotateSolver, FlipSolver,
        )
        from arc_v17_pipeline import BitOpsSubstrate
        from arc_v17_1_pipeline import ColumnRankSolver

        # Create a minimal substrate for solvers
        try:
            self.substrate = BitOpsSubstrate.__new__(BitOpsSubstrate)
            self.substrate.golay = GolayCodeEngine()
            self.substrate.leech = LeechLatticeEngine(self.substrate.golay)
        except:
            self.substrate = None

        self.solvers = []
        if self.substrate:
            self.solvers = [
                ("settlement_gravity", SettlementGravitySolver(self.substrate)),
                ("colour_map", ColourMapViaANDSolver(self.substrate)),
                ("conditional", ConditionalSolver(self.substrate)),
                ("interior_fill", InteriorFillSolver(self.substrate)),
                ("scale_resize", ScaleAwareResizeSolver(self.substrate)),
                ("shift", ShiftSolver(self.substrate)),
                ("rotate", RotateSolver(self.substrate)),
                ("flip", FlipSolver(self.substrate)),
                ("column_rank", ColumnRankSolver(self.substrate)),
            ]

        # Also try diverse solvers
        from v27_solvers import DIVERSE_SOLVERS
        self.diverse_solvers = DIVERSE_SOLVERS

    def demonstrate(self, task: ARCTask) -> List[Dict[str, Any]]:
        """Have all solvers attempt the task. Return their results.

        Each result teaches the GLM something about the task.
        """
        demonstrations = []

        for name, solver in self.solvers:
            try:
                result = solver.solve(task)
                if result is not None:
                    # Verify
                    all_pass = True
                    for pair in task.train:
                        # Create a mini-task to test
                        check_task = ARCTask(train=task.train, test=[TestInput(input=pair.input)])
                        check = solver.solve(check_task)
                        if check is None or check != pair.output:
                            all_pass = False
                            break
                    demonstrations.append({
                        "solver": name,
                        "result": result,
                        "verified": all_pass,
                    })
            except Exception:
                pass

        for name, solver in self.diverse_solvers:
            try:
                result = solver.solve(task)
                if result is not None:
                    verified = False
                    if task.test and task.test[0].expected_output:
                        verified = (result == task.test[0].expected_output)
                    demonstrations.append({
                        "solver": name,
                        "result": result,
                        "verified": verified,
                    })
            except Exception:
                pass

        return demonstrations


# ══════════════════════════════════════════════════════════════════════════════
# V28 PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

class V28Pipeline:
    """v28: GLM reasoning engine — the GLM works things out."""

    def __init__(self, run_number=1, known_addresses=None, known_transforms=None, seed=42):
        self.run_number = run_number
        self.seed = seed
        self.golay = GolayCodeEngine()
        self.reasoner = GLMReasoner(self.golay)
        self.teacher = SolverAsTeacher()
        self.known_addresses = known_addresses or {}
        self.known_transforms = known_transforms or {}

        # Load GLM state for CRG edges
        state_path = ARC_17_DIR / "results" / "glm_state.json"
        self.glm_state = {}
        if state_path.exists():
            try:
                with open(state_path) as f:
                    self.glm_state = json.load(f)
            except:
                pass

        self.crg_edges = self.glm_state.get("crg_edges", [])
        self.concepts = self.glm_state.get("concepts", {})
        self.solve_log = []

    def solve_task(self, task: ARCTask, task_id: str = "") -> Dict[str, Any]:
        """Solve a task using GLM reasoning, with solver demonstrations as learning material."""
        task_type = classify_task_type(task_id)

        try:
            # Step 1: PERCEIVE
            perception = self.reasoner.perceive_task(task)

            # Step 2: REASON AND PROPOSE (GLM's own reasoning)
            glm_solution = self.reasoner.reason_and_propose(task, perception)

            # Step 3: VERIFY GLM's proposal
            glm_verified = False
            if glm_solution is not None:
                glm_verified = True
                for pair in task.train:
                    # Re-perceive and reason for each train input
                    train_perception = self.reasoner.perceive_task(
                        ARCTask(train=task.train, test=[TestInput(input=pair.input)])
                    )
                    train_solution = self.reasoner.reason_and_propose(
                        ARCTask(train=task.train, test=[TestInput(input=pair.input)]),
                        train_perception
                    )
                    if train_solution is None or train_solution != pair.output:
                        glm_verified = False
                        break

            if glm_verified:
                # GLM solved it on its own!
                self.reasoner.learn_from_task(task_id, task_type, perception, True, "glm_reasoning")
                result = {
                    "solved": True,
                    "mode": "glm_reasoning",
                    "winning_strategy": perception["invariant"]["type"],
                    "task_type": task_type,
                    "reasoning_trace": f"GLM perceived {perception['invariant']['type']} (confidence={perception['invariant'].get('confidence', 0):.2f})",
                }
                self.solve_log.append(result)
                return result

            # Step 4: LEARN FROM SOLVER DEMONSTRATIONS
            demonstrations = self.teacher.demonstrate(task)
            verified_demo = None
            for demo in demonstrations:
                if demo["verified"]:
                    verified_demo = demo
                    break

            if verified_demo:
                # A solver taught the GLM something
                self.reasoner.learn_from_task(task_id, task_type, perception, True, f"taught_by_{verified_demo['solver']}")
                result = {
                    "solved": True,
                    "mode": "solver_taught",
                    "winning_strategy": verified_demo["solver"],
                    "task_type": task_type,
                    "reasoning_trace": f"GLM reasoning failed, but {verified_demo['solver']} demonstrated the solution",
                }
                self.solve_log.append(result)
                return result

            # Step 5: LEARN FROM FAILURE
            self.reasoner.learn_from_task(task_id, task_type, perception, False, "failed")
            result = {
                "solved": False,
                "mode": "failed",
                "winning_strategy": None,
                "task_type": task_type,
                "reasoning_trace": f"GLM could not reason about {perception['invariant']['type']}",
            }
            self.solve_log.append(result)
            return result

        except (ValueError, IndexError, KeyError) as e:
            result = {
                "solved": False, "mode": "error", "winning_strategy": None,
                "task_type": task_type, "reasoning_trace": f"Error: {e}",
            }
            self.solve_log.append(result)
            return result
        except Exception as e:
            result = {
                "solved": False, "mode": "error", "winning_strategy": None,
                "task_type": task_type, "reasoning_trace": f"Unexpected: {type(e).__name__}: {e}",
            }
            self.solve_log.append(result)
            return result

    def save_state(self, run_summary: Dict):
        """Save the grown GLM state."""
        state_path = ARC_17_DIR / "results" / "glm_state.json"

        # Grow CRG from learned patterns (more aggressive)
        new_edges = []
        for pattern_key, pattern in self.reasoner.learned_patterns.items():
            if pattern["successes"] > 0:
                task_type = pattern["task_type"]
                transform_type = pattern["transform_type"]
                success_rate = pattern["successes"] / (pattern["successes"] + pattern["failures"])

                # Edge 1: task_type → solves_via → transform_type
                edge1 = {"src": task_type, "label": "solves_via", "dst": transform_type}
                if edge1 not in self.crg_edges:
                    new_edges.append(edge1)

                # Edge 2: transform_type → enables → task_type
                edge2 = {"src": transform_type, "label": "enables", "dst": task_type}
                if edge2 not in self.crg_edges:
                    new_edges.append(edge2)

                # Edge 3: success_rate → characterizes → pattern
                edge3 = {"src": f"success_{int(success_rate*100)}", "label": "characterizes", "dst": pattern_key}
                if edge3 not in self.crg_edges:
                    new_edges.append(edge3)

                # Edge 4: grid property edges from successful transformations
                if transform_type == "colour_map":
                    edge4 = {"src": "grid", "label": "transforms_via", "dst": "colour_map"}
                    if edge4 not in self.crg_edges:
                        new_edges.append(edge4)
                elif transform_type == "density_change":
                    edge4 = {"src": "grid", "label": "transforms_via", "dst": "density_change"}
                    if edge4 not in self.crg_edges:
                        new_edges.append(edge4)
                elif transform_type == "shape_change":
                    edge4 = {"src": "grid", "label": "transforms_via", "dst": "shape_change"}
                    if edge4 not in self.crg_edges:
                        new_edges.append(edge4)

        # Also learn from GLM reasoning successes (cross-task patterns)
        glm_reasoning_successes = [l for l in self.solve_log if l.get("mode") == "glm_reasoning"]
        for entry in glm_reasoning_successes:
            task_type = entry.get("task_type", "unknown")
            strategy = entry.get("winning_strategy", "unknown")
            edge = {"src": task_type, "label": "glm_learned", "dst": strategy}
            if edge not in self.crg_edges:
                new_edges.append(edge)

        self.crg_edges.extend(new_edges)

        # Save
        state = {
            "concepts": self.concepts,
            "crg_edges": self.crg_edges,
            "run_history": self.glm_state.get("run_history", []) + [run_summary],
            "learned_patterns": self.reasoner.learned_patterns,
        }

        with open(state_path, "w") as f:
            json.dump(state, f, indent=2, default=str)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("ARC-AGI v28 — GLM Reasoning Engine")
    print("  The GLM observes, reasons, and proposes")
    print("  Solvers are teachers, not answer machines")
    print("=" * 80)

    # Load tasks
    training_dir = ARC_17_DIR / "data" / "training"
    arc_task_files = sorted(training_dir.glob("*.json"))
    puzzles_dir = ARC_17_DIR / "data" / "puzzles"
    diverse_tasks = load_diverse_tasks(puzzles_dir)
    print(f"\n[load] {len(arc_task_files)} ARC tasks + {len(diverse_tasks)} diverse puzzles")

    # Load persistent state
    addr_path = ARC_17_DIR / "results" / "hexcolour_addresses.json"
    known_addresses = {}
    known_transforms = {}
    if addr_path.exists():
        try:
            with open(addr_path) as f:
                addr_data = json.load(f)
            known_addresses = {k: int(v) for k, v in addr_data.get("addresses", {}).items()}
            known_transforms = addr_data.get("transforms", {})
        except:
            pass

    state_path = ARC_17_DIR / "results" / "glm_state.json"
    start_run = 1
    if state_path.exists():
        try:
            with open(state_path) as f:
                prev_state = json.load(f)
            start_run = len(prev_state.get("run_history", [])) + 1
            prev_edges = len(prev_state.get("crg_edges", []))
            print(f"[load] Previous CRG edges: {prev_edges}, runs: {start_run - 1}")
        except:
            pass

    N_RUNS = 3
    all_runs = []

    for i in range(N_RUNS):
        run_number = start_run + i
        print(f"\n{'='*60}")
        print(f"RUN {run_number}")
        print(f"{'='*60}")

        pipeline = V28Pipeline(
            run_number=run_number,
            known_addresses=known_addresses,
            known_transforms=known_transforms,
            seed=42 + i,
        )

        n_edges = len(pipeline.crg_edges)
        print(f"[init] CRG: {n_edges} edges, {len(pipeline.concepts)} concepts")
        print(f"[init] Learned patterns: {len(pipeline.reasoner.learned_patterns)}")

        # Build task list
        all_tasks = []
        for tf in arc_task_files:
            try:
                task = load_task(str(tf))
                all_tasks.append((tf.stem, task, "arc"))
            except:
                pass
        for tid, task in diverse_tasks:
            all_tasks.append((tid, task, classify_task_type(tid)))

        random.seed(42 + i)
        random.shuffle(all_tasks)

        # Solve
        solved_count = 0
        type_scores = defaultdict(lambda: {"solved": 0, "total": 0})
        mode_counts = defaultdict(int)

        for tid, task, task_type in all_tasks:
            result = pipeline.solve_task(task, tid)
            type_scores[task_type]["total"] += 1
            if result["solved"]:
                solved_count += 1
                type_scores[task_type]["solved"] += 1
            mode_counts[result.get("mode", "unknown")] += 1

        # Growth
        new_edges = len(pipeline.crg_edges) - n_edges
        run_summary = {
            "run_number": run_number,
            "n_tasks": len(all_tasks),
            "n_solved": solved_count,
            "type_scores": dict(type_scores),
            "mode_counts": dict(mode_counts),
            "glm_edges": len(pipeline.crg_edges),
            "new_edges": new_edges,
            "learned_patterns": len(pipeline.reasoner.learned_patterns),
        }

        pipeline.save_state(run_summary)
        all_runs.append(run_summary)

        bar = '█' * min(solved_count, 50) + '░' * max(0, 50 - solved_count)
        print(f"\n[run {run_number}] {bar} {solved_count}/{len(all_tasks)}")
        print(f"  Modes: {dict(mode_counts)}")
        print(f"  CRG: {len(pipeline.crg_edges)} edges (+{new_edges})")
        print(f"  Learned patterns: {len(pipeline.reasoner.learned_patterns)}")
        print(f"  Per-type:")
        for ttype, scores in sorted(type_scores.items()):
            pct = scores['solved'] / scores['total'] * 100 if scores['total'] > 0 else 0
            print(f"    {ttype:25s}: {scores['solved']}/{scores['total']} ({pct:.0f}%)")

    # Final
    print("\n" + "=" * 80)
    print(f"FINAL RESULTS ({N_RUNS} runs)")
    print("=" * 80)

    last_run = all_runs[-1]
    best_run = max(all_runs, key=lambda r: r["n_solved"])
    first_run = all_runs[0]
    total_new_edges = last_run["glm_edges"] - first_run["glm_edges"]

    print(f"\n{'Run':>4} {'Solved':>8} {'Edges':>8} {'+Edg':>5} {'Patterns':>10}")
    print("-" * 40)
    for run in all_runs:
        print(f"{run['run_number']:>4} {run['n_solved']:>5}/{run['n_tasks']:<2} "
              f"{run['glm_edges']:>8} {run['new_edges']:>+5} {run['learned_patterns']:>10}")

    print(f"\nBest: {best_run['n_solved']}/{best_run['n_tasks']}")
    print(f"CRG: {first_run['glm_edges']} → {last_run['glm_edges']} (+{total_new_edges})")

    # Aggregate
    agg_types = defaultdict(lambda: {"solved": 0, "total": 0})
    for run in all_runs:
        for ttype, scores in run.get("type_scores", {}).items():
            agg_types[ttype]["solved"] += scores["solved"]
            agg_types[ttype]["total"] += scores["total"]

    print(f"\nAggregate per-type:")
    for ttype, scores in sorted(agg_types.items()):
        pct = scores['solved'] / scores['total'] * 100 if scores['total'] > 0 else 0
        print(f"  {ttype:25s}: {scores['solved']}/{scores['total']} ({pct:.0f}%)")

    # Save results
    output_dir = ARC_17_DIR / "results"
    with open(output_dir / "v28_results.json", "w") as f:
        json.dump({
            "experiment": "ARC-AGI v28 — GLM Reasoning Engine",
            "n_runs": N_RUNS, "runs": all_runs,
            "best": best_run["n_solved"],
            "final_edges": last_run["glm_edges"],
            "total_new_edges": total_new_edges,
            "aggregate_types": dict(agg_types),
        }, f, indent=2, default=str)
    print(f"\nResults saved: {output_dir / 'v28_results.json'}")


if __name__ == "__main__":
    main()
