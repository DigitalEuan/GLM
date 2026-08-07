"""
diverse_puzzles.py — Non-ARC puzzle generators for broad GLM training
=====================================================================
Creates diverse task types that exercise different cognitive abilities,
growing CRG edges and hexcolour addresses beyond what ARC alone provides.

Puzzle types:
  1. Colour Cascade — consistent colour mapping with offsets
  2. Object Gravity — objects fall/collapse like ARC gravity but with rules
  3. Symmetry Complete — fill in missing half of a symmetric grid
  4. Border Frame — extract or transform border pixels
  5. Pattern Tile — detect and extend a repeating tile pattern
  6. Conditional Region — different rules for different regions
  7. Count Encode — encode object counts as colour patterns
  8. Diagonal Transform — diagonal-based operations
  9. Connected Component — colour connected components differently
  10. Noise Clean — remove noise cells while preserving structure

All puzzles use the same Grid/TrainPair/ARCTask format as ARC tasks.
"""

import random
import json
import hashlib
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any

from loader import Grid, TrainPair, TestInput, ARCTask


class PuzzleGenerator:
    """Base class for puzzle generators."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def generate(self, n_tasks: int = 5) -> List[ARCTask]:
        """Generate n_tasks of this puzzle type."""
        raise NotImplementedError

    @staticmethod
    def task_id(prefix: str, index: int) -> str:
        """Create a deterministic task ID."""
        h = hashlib.md5(f"{prefix}_{index}".encode()).hexdigest()[:8]
        return h


class ColourCascadeGenerator(PuzzleGenerator):
    """Colour mapping: each colour c maps to (c + offset) % 10.

    Exercises: consistent mapping detection, modular arithmetic.
    """

    def generate(self, n_tasks: int = 5) -> List[ARCTask]:
        tasks = []
        for i in range(n_tasks):
            h, w = self.rng.randint(3, 8), self.rng.randint(3, 8)
            offset = self.rng.randint(1, 9)
            palette_size = self.rng.randint(2, 6)
            palette = self.rng.sample(range(1, 10), palette_size)

            train_pairs = []
            for _ in range(self.rng.randint(2, 4)):
                cells = [[self.rng.choice([0] + palette) for _ in range(w)] for _ in range(h)]
                out_cells = [[(v + offset) % 10 if v != 0 else 0 for v in row] for row in cells]
                train_pairs.append(TrainPair(input=Grid(cells), output=Grid(out_cells)))

            test_in = [[self.rng.choice([0] + palette) for _ in range(w)] for _ in range(h)]
            test_out = [[(v + offset) % 10 if v != 0 else 0 for v in row] for row in test_in]
            tasks.append(ARCTask(
                train=train_pairs,
                test=[TestInput(input=Grid(test_in), expected_output=Grid(test_out))],
                name=f"colour_cascade_{self.task_id('cascade', i)}",
            ))
        return tasks


class SymmetryCompleteGenerator(PuzzleGenerator):
    """Fill in the right half of a grid that mirrors the left half.

    Exercises: symmetry detection, spatial reasoning.
    """

    def generate(self, n_tasks: int = 5) -> List[ARCTask]:
        tasks = []
        for i in range(n_tasks):
            h = self.rng.randint(3, 8)
            half_w = self.rng.randint(2, 5)
            palette = self.rng.sample(range(1, 10), self.rng.randint(2, 5))

            train_pairs = []
            for _ in range(self.rng.randint(2, 4)):
                left = [[self.rng.choice([0] + palette) for _ in range(half_w)] for _ in range(h)]
                full = [row + row[::-1] for row in left]
                train_pairs.append(TrainPair(input=Grid(full), output=Grid(full)))

            test_left = [[self.rng.choice([0] + palette) for _ in range(half_w)] for _ in range(h)]
            # Input is left half only, output is full mirrored
            test_in = [row + [0] * half_w for row in test_left]
            test_out = [row + row[::-1] for row in test_left]
            tasks.append(ARCTask(
                train=train_pairs,
                test=[TestInput(input=Grid(test_in), expected_output=Grid(test_out))],
                name=f"symmetry_{self.task_id('sym', i)}",
            ))
        return tasks


class BorderFrameGenerator(PuzzleGenerator):
    """Extract or transform the border pixels of a grid.

    Exercises: boundary detection, object extraction.
    """

    def generate(self, n_tasks: int = 5) -> List[ARCTask]:
        tasks = []
        for i in range(n_tasks):
            h = self.rng.randint(4, 10)
            w = self.rng.randint(4, 10)
            fill_col = self.rng.randint(1, 9)
            border_col = self.rng.randint(1, 9)
            while border_col == fill_col:
                border_col = self.rng.randint(1, 9)

            train_pairs = []
            for _ in range(self.rng.randint(2, 4)):
                cells = [[fill_col] * w for _ in range(h)]
                # Set border
                for c in range(w):
                    cells[0][c] = border_col
                    cells[h - 1][c] = border_col
                for r in range(h):
                    cells[r][0] = border_col
                    cells[r][w - 1] = border_col
                # Output: just the border (interior becomes 0)
                out = [[0] * w for _ in range(h)]
                for c in range(w):
                    out[0][c] = border_col
                    out[h - 1][c] = border_col
                for r in range(h):
                    out[r][0] = border_col
                    out[r][w - 1] = border_col
                train_pairs.append(TrainPair(input=Grid(cells), output=Grid(out)))

            # Test: different fill but same border extraction
            test_fill = self.rng.randint(1, 9)
            while test_fill == border_col:
                test_fill = self.rng.randint(1, 9)
            test_cells = [[test_fill] * w for _ in range(h)]
            for c in range(w):
                test_cells[0][c] = border_col
                test_cells[h - 1][c] = border_col
            for r in range(h):
                test_cells[r][0] = border_col
                test_cells[r][w - 1] = border_col
            test_out = [[0] * w for _ in range(h)]
            for c in range(w):
                test_out[0][c] = border_col
                test_out[h - 1][c] = border_col
            for r in range(h):
                test_out[r][0] = border_col
                test_out[r][w - 1] = border_col
            tasks.append(ARCTask(
                train=train_pairs,
                test=[TestInput(input=Grid(test_cells), expected_output=Grid(test_out))],
                name=f"border_{self.task_id('border', i)}",
            ))
        return tasks


class ObjectGravityGenerator(PuzzleGenerator):
    """Objects fall to the bottom, maintaining relative order.

    Exercises: gravity detection, object tracking.
    """

    def generate(self, n_tasks: int = 5) -> List[ARCTask]:
        tasks = []
        for i in range(n_tasks):
            h = self.rng.randint(4, 8)
            w = self.rng.randint(3, 7)
            n_objects = self.rng.randint(1, 4)
            colours = self.rng.sample(range(1, 10), n_objects)

            train_pairs = []
            for _ in range(self.rng.randint(2, 4)):
                cells = [[0] * w for _ in range(h)]
                # Place objects randomly in top half
                for col in colours:
                    for _ in range(self.rng.randint(1, 3)):
                        r = self.rng.randint(0, h // 2)
                        c = self.rng.randint(0, w - 1)
                        cells[r][c] = col
                # Gravity: each column, non-zero cells fall to bottom
                out = [[0] * w for _ in range(h)]
                for c in range(w):
                    column = [cells[r][c] for r in range(h) if cells[r][c] != 0]
                    for j, val in enumerate(column):
                        out[h - len(column) + j][c] = val
                train_pairs.append(TrainPair(input=Grid(cells), output=Grid(out)))

            # Test
            test_cells = [[0] * w for _ in range(h)]
            for col in colours:
                for _ in range(self.rng.randint(1, 3)):
                    r = self.rng.randint(0, h // 2)
                    c = self.rng.randint(0, w - 1)
                    test_cells[r][c] = col
            test_out = [[0] * w for _ in range(h)]
            for c in range(w):
                column = [test_cells[r][c] for r in range(h) if test_cells[r][c] != 0]
                for j, val in enumerate(column):
                    test_out[h - len(column) + j][c] = val
            tasks.append(ARCTask(
                train=train_pairs,
                test=[TestInput(input=Grid(test_cells), expected_output=Grid(test_out))],
                name=f"obj_gravity_{self.task_id('ograv', i)}",
            ))
        return tasks


class PatternTileGenerator(PuzzleGenerator):
    """Detect and extend a repeating tile pattern.

    Exercises: pattern recognition, periodicity detection.
    """

    def generate(self, n_tasks: int = 5) -> List[ARCTask]:
        tasks = []
        for i in range(n_tasks):
            tile_h = self.rng.randint(2, 4)
            tile_w = self.rng.randint(2, 4)
            reps_h = self.rng.randint(2, 3)
            reps_w = self.rng.randint(2, 3)
            palette = self.rng.sample(range(1, 10), self.rng.randint(2, 4))

            # Create a tile
            tile = [[self.rng.choice([0] + palette) for _ in range(tile_w)] for _ in range(tile_h)]
            # Create tiled grid
            full_h, full_w = tile_h * reps_h, tile_w * reps_w
            tiled = [[tile[r % tile_h][c % tile_w] for c in range(full_w)] for r in range(full_h)]

            train_pairs = []
            train_pairs.append(TrainPair(input=Grid(tiled), output=Grid(tiled)))

            # Test: provide partial tile (top-left) and expect full tiling
            partial_h = tile_h
            partial_w = tile_w
            test_in = [[tile[r % tile_h][c % tile_w] for c in range(full_w)] for r in range(full_h)]
            # Mask bottom-right portion
            for r in range(partial_h, full_h):
                for c in range(partial_w, full_w):
                    test_in[r][c] = 0
            tasks.append(ARCTask(
                train=train_pairs,
                test=[TestInput(input=Grid(test_in), expected_output=Grid(tiled))],
                name=f"tile_{self.task_id('tile', i)}",
            ))
        return tasks


class DiagonalTransformGenerator(PuzzleGenerator):
    """Operations on diagonal cells.

    Exercises: diagonal detection, coordinate transforms.
    """

    def generate(self, n_tasks: int = 5) -> List[ARCTask]:
        tasks = []
        for i in range(n_tasks):
            size = self.rng.randint(4, 8)
            bg_col = 0
            diag_col = self.rng.randint(1, 9)
            fill_col = self.rng.randint(1, 9)
            while fill_col == diag_col:
                fill_col = self.rng.randint(1, 9)

            train_pairs = []
            for _ in range(self.rng.randint(2, 3)):
                cells = [[bg_col] * size for _ in range(size)]
                # Set main diagonal
                for j in range(size):
                    cells[j][j] = diag_col
                # Output: fill below diagonal with fill_col
                out = [row[:] for row in cells]
                for r in range(size):
                    for c in range(size):
                        if r > c:
                            out[r][c] = fill_col
                train_pairs.append(TrainPair(input=Grid(cells), output=Grid(out)))

            # Test
            test_cells = [[bg_col] * size for _ in range(size)]
            for j in range(size):
                test_cells[j][j] = diag_col
            test_out = [row[:] for row in test_cells]
            for r in range(size):
                for c in range(size):
                    if r > c:
                        test_out[r][c] = fill_col
            tasks.append(ARCTask(
                train=train_pairs,
                test=[TestInput(input=Grid(test_cells), expected_output=Grid(test_out))],
                name=f"diagonal_{self.task_id('diag', i)}",
            ))
        return tasks


class ConditionalRegionGenerator(PuzzleGenerator):
    """Different rules for different regions of the grid.

    Exercises: conditional logic, region detection.
    """

    def generate(self, n_tasks: int = 5) -> List[ARCTask]:
        tasks = []
        for i in range(n_tasks):
            h = self.rng.randint(5, 10)
            w = self.rng.randint(5, 10)
            palette = self.rng.sample(range(1, 10), 3)
            c1, c2, c3 = palette

            train_pairs = []
            for _ in range(self.rng.randint(2, 4)):
                cells = [[self.rng.choice([0, c1, c2]) for _ in range(w)] for _ in range(h)]
                out = [row[:] for row in cells]
                # Rule: top half c1→c3, bottom half c2→c3
                mid = h // 2
                for r in range(h):
                    for c in range(w):
                        if r < mid and cells[r][c] == c1:
                            out[r][c] = c3
                        elif r >= mid and cells[r][c] == c2:
                            out[r][c] = c3
                train_pairs.append(TrainPair(input=Grid(cells), output=Grid(out)))

            # Test
            test_cells = [[self.rng.choice([0, c1, c2]) for _ in range(w)] for _ in range(h)]
            test_out = [row[:] for row in test_cells]
            mid = h // 2
            for r in range(h):
                for c in range(w):
                    if r < mid and test_cells[r][c] == c1:
                        test_out[r][c] = c3
                    elif r >= mid and test_cells[r][c] == c2:
                        test_out[r][c] = c3
            tasks.append(ARCTask(
                train=train_pairs,
                test=[TestInput(input=Grid(test_cells), expected_output=Grid(test_out))],
                name=f"cond_region_{self.task_id('creg', i)}",
            ))
        return tasks


class ConnectedComponentGenerator(PuzzleGenerator):
    """Colour connected components differently.

    Exercises: flood fill, connected component detection.
    """

    def generate(self, n_tasks: int = 5) -> List[ARCTask]:
        tasks = []
        for i in range(n_tasks):
            h = self.rng.randint(5, 8)
            w = self.rng.randint(5, 8)
            base_col = self.rng.randint(1, 5)
            out_cols = self.rng.sample(range(1, 10), 4)

            train_pairs = []
            for _ in range(self.rng.randint(2, 3)):
                # Create grid with 2-3 separated regions of base_col
                cells = [[0] * w for _ in range(h)]
                n_regions = self.rng.randint(2, 3)
                for ri in range(n_regions):
                    # Place a rectangular region
                    rh = self.rng.randint(1, h // 2)
                    rw = self.rng.randint(1, w // 2)
                    rr = self.rng.randint(0, h - rh)
                    rc = self.rng.randint(0, w - rw)
                    for r in range(rr, rr + rh):
                        for c in range(rc, rc + rw):
                            cells[r][c] = base_col

                # Output: each connected component gets a different colour
                out = [row[:] for row in cells]
                visited = [[False] * w for _ in range(h)]
                comp_id = 0
                for r in range(h):
                    for c in range(w):
                        if cells[r][c] == base_col and not visited[r][c]:
                            # BFS
                            queue = [(r, c)]
                            visited[r][c] = True
                            comp_cells = [(r, c)]
                            while queue:
                                cr, cc = queue.pop(0)
                                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                    nr, nc = cr + dr, cc + dc
                                    if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and cells[nr][nc] == base_col:
                                        visited[nr][nc] = True
                                        queue.append((nr, nc))
                                        comp_cells.append((nr, nc))
                            colour = out_cols[comp_id % len(out_cols)]
                            for cr, cc in comp_cells:
                                out[cr][cc] = colour
                            comp_id += 1
                train_pairs.append(TrainPair(input=Grid(cells), output=Grid(out)))

            # Test
            test_cells = [[0] * w for _ in range(h)]
            n_regions = self.rng.randint(2, 3)
            for ri in range(n_regions):
                rh = self.rng.randint(1, h // 2)
                rw = self.rng.randint(1, w // 2)
                rr = self.rng.randint(0, h - rh)
                rc = self.rng.randint(0, w - rw)
                for r in range(rr, rr + rh):
                    for c in range(rc, rc + rw):
                        test_cells[r][c] = base_col
            test_out = [row[:] for row in test_cells]
            visited = [[False] * w for _ in range(h)]
            comp_id = 0
            for r in range(h):
                for c in range(w):
                    if test_cells[r][c] == base_col and not visited[r][c]:
                        queue = [(r, c)]
                        visited[r][c] = True
                        comp_cells = [(r, c)]
                        while queue:
                            cr, cc = queue.pop(0)
                            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                nr, nc = cr + dr, cc + dc
                                if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and test_cells[nr][nc] == base_col:
                                    visited[nr][nc] = True
                                    queue.append((nr, nc))
                                    comp_cells.append((nr, nc))
                        colour = out_cols[comp_id % len(out_cols)]
                        for cr, cc in comp_cells:
                            test_out[cr][cc] = colour
                        comp_id += 1
            tasks.append(ARCTask(
                train=train_pairs,
                test=[TestInput(input=Grid(test_cells), expected_output=Grid(test_out))],
                name=f"conncomp_{self.task_id('ccomp', i)}",
            ))
        return tasks


class NoiseCleanGenerator(PuzzleGenerator):
    """Remove noise cells (isolated single cells) while preserving structure.

    Exercises: noise detection, structural preservation.
    """

    def generate(self, n_tasks: int = 5) -> List[ARCTask]:
        tasks = []
        for i in range(n_tasks):
            h = self.rng.randint(5, 8)
            w = self.rng.randint(5, 8)
            struct_col = self.rng.randint(1, 5)
            noise_col = self.rng.randint(6, 9)

            train_pairs = []
            for _ in range(self.rng.randint(2, 3)):
                # Create a structure (horizontal or vertical line)
                cells = [[0] * w for _ in range(h)]
                if self.rng.random() < 0.5:
                    # Horizontal line
                    row = self.rng.randint(1, h - 2)
                    for c in range(1, w - 1):
                        cells[row][c] = struct_col
                else:
                    # Vertical line
                    col = self.rng.randint(1, w - 2)
                    for r in range(1, h - 1):
                        cells[r][col] = struct_col

                # Add noise
                n_noise = self.rng.randint(3, 8)
                for _ in range(n_noise):
                    nr, nc = self.rng.randint(0, h - 1), self.rng.randint(0, w - 1)
                    if cells[nr][nc] == 0:
                        cells[nr][nc] = noise_col

                # Output: just the structure (noise removed)
                out = [[0] * w for _ in range(h)]
                if self.rng.random() < 0.5:
                    row_idx = None
                    for r in range(h):
                        if sum(1 for c in range(w) if cells[r][c] == struct_col) > 1:
                            row_idx = r
                            break
                    if row_idx is not None:
                        for c in range(w):
                            if cells[row_idx][c] == struct_col:
                                out[row_idx][c] = struct_col
                else:
                    col_idx = None
                    for c in range(w):
                        if sum(1 for r in range(h) if cells[r][c] == struct_col) > 1:
                            col_idx = c
                            break
                    if col_idx is not None:
                        for r in range(h):
                            if cells[r][col_idx] == struct_col:
                                out[r][col_idx] = struct_col
                train_pairs.append(TrainPair(input=Grid(cells), output=Grid(out)))

            # Test - similar structure with noise
            test_cells = [[0] * w for _ in range(h)]
            if self.rng.random() < 0.5:
                row = self.rng.randint(1, h - 2)
                for c in range(1, w - 1):
                    test_cells[row][c] = struct_col
            else:
                col = self.rng.randint(1, w - 2)
                for r in range(1, h - 1):
                    test_cells[r][col] = struct_col
            n_noise = self.rng.randint(3, 8)
            for _ in range(n_noise):
                nr, nc = self.rng.randint(0, h - 1), self.rng.randint(0, w - 1)
                if test_cells[nr][nc] == 0:
                    test_cells[nr][nc] = noise_col
            test_out = [[0] * w for _ in range(h)]
            for r in range(h):
                if sum(1 for c in range(w) if test_cells[r][c] == struct_col) > 1:
                    for c in range(w):
                        if test_cells[r][c] == struct_col:
                            test_out[r][c] = struct_col
                    break
            for c in range(w):
                if sum(1 for r in range(h) if test_cells[r][c] == struct_col) > 1:
                    for r in range(h):
                        if test_cells[r][c] == struct_col:
                            test_out[r][c] = struct_col
                    break
            tasks.append(ARCTask(
                train=train_pairs,
                test=[TestInput(input=Grid(test_cells), expected_output=Grid(test_out))],
                name=f"noiseclean_{self.task_id('nclean', i)}",
            ))
        return tasks


class CountEncodeGenerator(PuzzleGenerator):
    """Encode the count of objects as a colour pattern.

    Exercises: counting, encoding, object detection.
    """

    def generate(self, n_tasks: int = 5) -> List[ARCTask]:
        tasks = []
        for i in range(n_tasks):
            h = self.rng.randint(3, 6)
            w = self.rng.randint(3, 6)
            obj_col = self.rng.randint(1, 5)

            train_pairs = []
            for _ in range(self.rng.randint(2, 4)):
                cells = [[0] * w for _ in range(h)]
                n_objects = self.rng.randint(1, 6)
                placed = set()
                for _ in range(n_objects):
                    while True:
                        r, c = self.rng.randint(0, h - 1), self.rng.randint(0, w - 1)
                        if (r, c) not in placed:
                            cells[r][c] = obj_col
                            placed.add((r, c))
                            break
                # Output: 1×n grid where n = count, filled with obj_col
                out = [[obj_col] * n_objects]
                train_pairs.append(TrainPair(input=Grid(cells), output=Grid(out)))

            # Test
            test_cells = [[0] * w for _ in range(h)]
            n_objects = self.rng.randint(1, 6)
            placed = set()
            for _ in range(n_objects):
                while True:
                    r, c = self.rng.randint(0, h - 1), self.rng.randint(0, w - 1)
                    if (r, c) not in placed:
                        test_cells[r][c] = obj_col
                        placed.add((r, c))
                        break
            test_out = [[obj_col] * n_objects]
            tasks.append(ARCTask(
                train=train_pairs,
                test=[TestInput(input=Grid(test_cells), expected_output=Grid(test_out))],
                name=f"count_{self.task_id('count', i)}",
            ))
        return tasks


# ══════════════════════════════════════════════════════════════════════════════
# AGGREGATOR
# ══════════════════════════════════════════════════════════════════════════════

ALL_GENERATORS = [
    ColourCascadeGenerator,
    SymmetryCompleteGenerator,
    BorderFrameGenerator,
    ObjectGravityGenerator,
    PatternTileGenerator,
    DiagonalTransformGenerator,
    ConditionalRegionGenerator,
    ConnectedComponentGenerator,
    NoiseCleanGenerator,
    CountEncodeGenerator,
]

GENERATOR_NAMES = [
    "colour_cascade", "symmetry", "border", "object_gravity",
    "pattern_tile", "diagonal", "conditional_region",
    "connected_component", "noise_clean", "count_encode",
]


def generate_all_diverse(n_per_type: int = 3, seed: int = 42) -> List[ARCTask]:
    """Generate a diverse set of puzzles from all generators."""
    all_tasks = []
    for gen_cls in ALL_GENERATORS:
        gen = gen_cls(seed=seed)
        tasks = gen.generate(n_per_type)
        all_tasks.extend(tasks)
    return all_tasks


def save_puzzles_to_disk(output_dir: Path, n_per_type: int = 3, seed: int = 42):
    """Generate and save puzzles as JSON files (ARC-compatible format)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks = generate_all_diverse(n_per_type, seed)
    saved = []
    for task in tasks:
        data = {
            "train": [{"input": p.input.cells, "output": p.output.cells} for p in task.train],
            "test": [{"input": t.input.cells,
                       "output": t.expected_output.cells if t.expected_output else []}
                      for t in task.test],
        }
        path = output_dir / f"{task.name}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        saved.append(str(path))
    return saved


if __name__ == "__main__":
    from paths import PUZZLES_DIR
    saved = save_puzzles_to_disk(PUZZLES_DIR, n_per_type=5, seed=42)
    print(f"Generated {len(saved)} diverse puzzles in {PUZZLES_DIR}")
