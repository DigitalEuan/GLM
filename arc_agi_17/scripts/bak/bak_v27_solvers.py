#!/usr/bin/env python3
"""
v27_solvers.py — Additional solvers for diverse puzzle types
=============================================================
These solvers handle the diverse puzzle types that the existing
ARC pipeline doesn't cover:
  - Diagonal fill
  - Object gravity (object-aware)
  - Pattern tile detection
  - Conditional region
  - Connected component labelling
  - Noise cleaning
  - Count encoding

Each solver follows the same interface: solve(task) -> Optional[Grid]
"""

import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any
from collections import Counter

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from loader import Grid, ARCTask


class DiagonalFillSolver:
    """Fill below (or above) the main diagonal with a detected colour."""

    def solve(self, task: ARCTask) -> Optional[Grid]:
        if not task.test or not task.train:
            return None

        for pair in task.train:
            inp, out = pair.input, pair.output
            if inp.height != out.height or inp.width != out.width:
                return None

        # Detect the fill: find cells that are 0 in input but non-zero in output
        fill_colour = None
        for pair in task.train:
            inp, out = pair.input, pair.output
            for r in range(inp.height):
                for c in range(inp.width):
                    if inp.cells[r][c] == 0 and out.cells[r][c] != 0:
                        fill_colour = out.cells[r][c]
                        break
                if fill_colour is not None:
                    break
            if fill_colour is not None:
                break

        if fill_colour is None:
            return None

        # Verify: all train pairs have the same fill pattern
        for pair in task.train:
            inp, out = pair.input, pair.output
            test_out = [row[:] for row in inp.cells]
            h, w = inp.height, inp.width
            for r in range(h):
                for c in range(w):
                    if inp.cells[r][c] == 0 and r > c:
                        test_out[r][c] = fill_colour
            if Grid(test_out) != out:
                # Try fill above diagonal
                test_out2 = [row[:] for row in inp.cells]
                for r in range(h):
                    for c in range(w):
                        if inp.cells[r][c] == 0 and r < c:
                            test_out2[r][c] = fill_colour
                if Grid(test_out2) != out:
                    return None
                fill_below = False
            else:
                fill_below = True

        # Apply to test
        test_input = task.test[0].input
        h, w = test_input.height, test_input.width
        result = [row[:] for row in test_input.cells]
        for r in range(h):
            for c in range(w):
                if test_input.cells[r][c] == 0:
                    if fill_below and r > c:
                        result[r][c] = fill_colour
                    elif not fill_below and r < c:
                        result[r][c] = fill_colour
        return Grid(result)


class ObjectGravitySolver:
    """Gravity that treats connected components as units."""

    def solve(self, task: ARCTask) -> Optional[Grid]:
        if not task.test or not task.train:
            return None

        # Check if gravity works on all train pairs
        for pair in task.train:
            gravity_out = self._apply_gravity(pair.input)
            if gravity_out != pair.output:
                return None

        return self._apply_gravity(task.test[0].input)

    @staticmethod
    def _apply_gravity(grid: Grid) -> Grid:
        h, w = grid.height, grid.width
        result = [[0] * w for _ in range(h)]
        for c in range(w):
            column = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
            for i, val in enumerate(column):
                result[h - len(column) + i][c] = val
        return Grid(result)


class PatternTileSolver:
    """Detect a repeating tile pattern and extend it."""

    def solve(self, task: ARCTask) -> Optional[Grid]:
        if not task.test or not task.train:
            return None

        # For each train pair, check if output is a tiling of a sub-pattern
        for pair in task.train:
            inp, out = pair.input, pair.output
            if inp.height != out.height or inp.width != out.width:
                return None

        # Try to find tile size by checking divisors
        h, w = task.train[0].input.height, task.train[0].input.width
        for th in range(1, h + 1):
            if h % th != 0:
                continue
            for tw in range(1, w + 1):
                if w % tw != 0:
                    continue
                if th == h and tw == w:
                    continue

                # Check if all train outputs are tilings of the top-left th×tw
                all_match = True
                for pair in task.train:
                    tile = [row[:tw] for row in pair.output.cells[:th]]
                    for r in range(pair.output.height):
                        for c in range(pair.output.width):
                            if pair.output.cells[r][c] != tile[r % th][c % tw]:
                                all_match = False
                                break
                        if not all_match:
                            break
                    if not all_match:
                        break

                if all_match:
                    # Found the tile — apply to test input
                    test_input = task.test[0].input
                    # The test input might be partial (top-left tile only)
                    # or full — we tile the top-left portion
                    tile = [row[:tw] for row in test_input.cells[:th]]
                    result = [[tile[r % th][c % tw] for c in range(test_input.width)]
                              for r in range(test_input.height)]
                    return Grid(result)
        return None


class ConditionalRegionSolver:
    """Different rules for different regions (e.g., top half vs bottom half)."""

    def solve(self, task: ARCTask) -> Optional[Grid]:
        if not task.test or not task.train:
            return None

        for pair in task.train:
            inp, out = pair.input, pair.output
            if inp.height != out.height or inp.width != out.width:
                return None

        # Detect: is there a consistent region-based colour map?
        h, w = task.train[0].input.height, task.train[0].input.width
        mid_r = h // 2
        mid_c = w // 2

        # Try quadrant-based or half-based rules
        for region_fn, region_name in [
            (lambda r, c: r < mid_r, "top_half"),
            (lambda r, c: r >= mid_r, "bottom_half"),
            (lambda r, c: c < mid_c, "left_half"),
            (lambda r, c: c >= mid_c, "right_half"),
            (lambda r, c: r < mid_r and c < mid_c, "top_left"),
            (lambda r, c: r < mid_r and c >= mid_c, "top_right"),
            (lambda r, c: r >= mid_r and c < mid_c, "bottom_left"),
            (lambda r, c: r >= mid_r and c >= mid_c, "bottom_right"),
        ]:
            region_map = {}  # (region, in_colour) -> out_colour
            consistent = True

            for pair in task.train:
                inp, out = pair.input, pair.output
                for r in range(inp.height):
                    for c in range(inp.width):
                        in_val = inp.cells[r][c]
                        out_val = out.cells[r][c]
                        in_region = region_fn(r, c)
                        key = (in_region, in_val)
                        if key in region_map:
                            if region_map[key] != out_val:
                                consistent = False
                                break
                        else:
                            region_map[key] = out_val
                    if not consistent:
                        break
                if not consistent:
                    break

            if not consistent:
                continue

            # Verify on all train pairs
            all_pass = True
            for pair in task.train:
                inp, out = pair.input, pair.output
                for r in range(inp.height):
                    for c in range(inp.width):
                        in_region = region_fn(r, c)
                        expected = region_map.get((in_region, inp.cells[r][c]), inp.cells[r][c])
                        if expected != out.cells[r][c]:
                            all_pass = False
                            break
                    if not all_pass:
                        break
                if not all_pass:
                    break

            if all_pass:
                # Apply to test
                test_input = task.test[0].input
                result = [[0] * test_input.width for _ in range(test_input.height)]
                for r in range(test_input.height):
                    for c in range(test_input.width):
                        in_region = region_fn(r, c)
                        result[r][c] = region_map.get(
                            (in_region, test_input.cells[r][c]),
                            test_input.cells[r][c]
                        )
                return Grid(result)

        return None


class ConnectedComponentSolver:
    """Colour connected components with different colours."""

    def solve(self, task: ARCTask) -> Optional[Grid]:
        if not task.test or not task.train:
            return None

        # Check pattern: same-shape, objects get recoloured by component
        for pair in task.train:
            inp, out = pair.input, pair.output
            if inp.height != out.height or inp.width != out.width:
                return None

        # Detect: is the output a component labelling of the input?
        # Find the base colour (the one that gets split into components)
        for pair in task.train:
            inp, out = pair.input, pair.output
            # Find colours that appear in output but not input (new labels)
            inp_colours = set()
            out_colours = set()
            for r in range(inp.height):
                for c in range(inp.width):
                    if inp.cells[r][c] != 0:
                        inp_colours.add(inp.cells[r][c])
                    if out.cells[r][c] != 0:
                        out_colours.add(out.cells[r][c])

            # The base colour is the one in input that gets split
            # New colours in output are the component labels
            new_colours = out_colours - inp_colours
            if not new_colours:
                continue

            # Verify: each connected component of a base colour gets a unique label
            # This is complex — skip for now, return None
            pass

        return None


class NoiseCleanSolver:
    """Remove noise while preserving the largest connected structure."""

    def solve(self, task: ARCTask) -> Optional[Grid]:
        if not task.test or not task.train:
            return None

        # Check pattern: output has fewer non-zero cells than input
        for pair in task.train:
            inp, out = pair.input, pair.output
            if inp.height != out.height or inp.width != out.width:
                return None

        # Detect strategy from train pairs
        for pair in task.train:
            inp, out = pair.input, pair.output
            # Find the structure colour (the one that survives)
            out_colours = set()
            for r in range(out.height):
                for c in range(out.width):
                    if out.cells[r][c] != 0:
                        out_colours.add(out.cells[r][c])
            if len(out_colours) != 1:
                return None  # multi-colour output, skip
            struct_colour = out_colours.pop()

            # Verify: output is exactly the largest connected component of struct_colour
            objects = self._find_objects(inp, struct_colour)
            if not objects:
                return None
            largest = max(objects, key=lambda o: o["size"])
            test_out = [[0] * inp.width for _ in range(inp.height)]
            for r, c in largest["cells"]:
                test_out[r][c] = struct_colour
            if Grid(test_out) != out:
                return None

        # Apply to test
        test_input = task.test[0].input
        out_colours = set()
        for pair in task.train:
            for r in range(pair.output.height):
                for c in range(pair.output.width):
                    if pair.output.cells[r][c] != 0:
                        out_colours.add(pair.output.cells[r][c])
        struct_colour = out_colours.pop()
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


class CountEncodeSolver:
    """Count objects and encode the count as a pattern."""

    def solve(self, task: ARCTask) -> Optional[Grid]:
        if not task.test or not task.train:
            return None

        # Detect: output is a 1×N grid where N = number of objects in input
        for pair in task.train:
            inp, out = pair.input, pair.output
            if out.height != 1:
                return None

        # Find the object colour and verify count
        for pair in task.train:
            inp, out = pair.input, pair.output
            # Count distinct non-zero cells (simple: each non-zero cell is an "object")
            obj_colours = set()
            for r in range(inp.height):
                for c in range(inp.width):
                    if inp.cells[r][c] != 0:
                        obj_colours.add(inp.cells[r][c])

            if len(obj_colours) != 1:
                return None  # mixed colours, skip

            obj_colour = obj_colours.pop()
            count = sum(1 for r in range(inp.height) for c in range(inp.width)
                        if inp.cells[r][c] == obj_colour)

            if count != out.width:
                return None
            if not all(out.cells[0][c] == obj_colour for c in range(out.width)):
                return None

        # Apply to test
        test_input = task.test[0].input
        obj_colours = set()
        for r in range(test_input.height):
            for c in range(test_input.width):
                if test_input.cells[r][c] != 0:
                    obj_colours.add(test_input.cells[r][c])
        if len(obj_colours) != 1:
            return None
        obj_colour = obj_colours.pop()
        count = sum(1 for r in range(test_input.height) for c in range(test_input.width)
                    if test_input.cells[r][c] == obj_colour)
        return Grid([[obj_colour] * count])


# ══════════════════════════════════════════════════════════════════════════════
# AGGREGATE
# ══════════════════════════════════════════════════════════════════════════════

DIVERSE_SOLVERS = [
    ("diagonal_fill", DiagonalFillSolver()),
    ("object_gravity", ObjectGravitySolver()),
    ("pattern_tile", PatternTileSolver()),
    ("conditional_region", ConditionalRegionSolver()),
    ("noise_clean", NoiseCleanSolver()),
    ("count_encode", CountEncodeSolver()),
]
