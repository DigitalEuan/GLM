"""
arc_loader.py — ARC-AGI-3 task loader
======================================

Loads ARC-AGI-3 task JSON files into a uniform in-memory representation.

An ARC task is a JSON object with:
  - "train": list of {"input": grid, "output": grid} pairs (2-5 pairs)
  - "test":  list of {"input": grid} (1 input, output held out by eval harness)

A grid is a 2-D list of integers in [0, 9] (10-colour palette).
Grid dimensions vary between 1×1 and 30×30 and need not be square.

Usage:
    from arc_loader import ARCTask, load_task

    task = load_task("path/to/task.json")
    print(task.summary())
    for pair in task.train:
        print(pair.input.shape, pair.output.shape)

    # Or build a synthetic task in-memory
    from arc_loader import Grid, TrainPair, ARCTask
    g = Grid([[0,1,0],[1,1,1],[0,1,0]])
    task = ARCTask(train=[TrainPair(g, g.rotate_90())],
                   test=[g])  # output is None until solved
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any


# ══════════════════════════════════════════════════════════════════════════════
# GRID — the atomic ARC data structure
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Grid:
    """A 2-D ARC grid of integers in [0, 9]. Immutable in spirit."""
    cells: List[List[int]]

    def __post_init__(self):
        if not self.cells:
            raise ValueError("Grid: cells must be non-empty")
        w = len(self.cells[0])
        for row in self.cells:
            if len(row) != w:
                raise ValueError(f"Grid: ragged row width {len(row)} != {w}")
            for v in row:
                if not isinstance(v, int) or v < 0 or v > 9:
                    raise ValueError(f"Grid: cell {v} out of palette [0,9]")

    @property
    def height(self) -> int:
        return len(self.cells)

    @property
    def width(self) -> int:
        return len(self.cells[0])

    @property
    def shape(self) -> Tuple[int, int]:
        return (self.height, self.width)

    def __eq__(self, other):
        return isinstance(other, Grid) and self.cells == other.cells

    def __hash__(self):
        return hash(tuple(tuple(r) for r in self.cells))

    def __repr__(self):
        return f"Grid({self.height}x{self.width})"

    def pretty(self) -> str:
        """ASCII-art representation, useful for debugging."""
        if self.width > 40 or self.height > 40:
            return f"Grid({self.height}x{self.width}, too large to pretty-print)"
        return "\n".join(" ".join(str(v) for v in row) for row in self.cells)

    # ── basic grid operations (used by DSL) ────────────────────────────────

    def is_empty(self) -> bool:
        """Check if grid is all zeros."""
        return all(v == 0 for row in self.cells for v in row)

    def copy(self) -> "Grid":
        return Grid([row[:] for row in self.cells])

    def palette(self) -> frozenset:
        """Set of distinct colours present in the grid."""
        return frozenset(v for row in self.cells for v in row if v != 0)

    def cell_count(self, colour: int) -> int:
        return sum(1 for row in self.cells for v in row if v == colour)

    def dominant_colour(self) -> int:
        """Most common non-zero colour, or 0 if grid is empty."""
        counts = {c: 0 for c in range(10)}
        for row in self.cells:
            for v in row:
                counts[v] += 1
        counts[0] = 0  # ignore background
        return max(counts, key=counts.get) if max(counts.values()) > 0 else 0

    # ── geometric transforms (return new Grid) ─────────────────────────────

    def rotate_90(self) -> "Grid":
        """Rotate 90° clockwise."""
        return Grid([list(row) for row in zip(*self.cells[::-1])])

    def rotate_180(self) -> "Grid":
        return Grid([row[::-1] for row in self.cells[::-1]])

    def rotate_270(self) -> "Grid":
        """Rotate 90° counter-clockwise."""
        return Grid([list(row) for row in zip(*self.cells)][::-1])

    def flip_h(self) -> "Grid":
        """Flip horizontally (left-right)."""
        return Grid([row[::-1] for row in self.cells])

    def flip_v(self) -> "Grid":
        """Flip vertically (top-bottom)."""
        return Grid([row[:] for row in self.cells[::-1]])

    def transpose(self) -> "Grid":
        return Grid([list(row) for row in zip(*self.cells)])

    def recolour(self, mapping: Dict[int, int]) -> "Grid":
        """Apply a colour map. Missing colours map to themselves."""
        full = {i: mapping.get(i, i) for i in range(10)}
        return Grid([[full[v] for v in row] for row in self.cells])


# ══════════════════════════════════════════════════════════════════════════════
# TRAIN PAIR + TASK
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TrainPair:
    input: Grid
    output: Grid

    def __repr__(self):
        return f"TrainPair(in={self.input}, out={self.output})"


@dataclass
class TestInput:
    input: Grid
    expected_output: Optional[Grid] = None  # held out by eval harness; may be present in dev

    def __repr__(self):
        return f"TestInput(in={self.input}, expected={'set' if self.expected_output else 'None'})"


@dataclass
class ARCTask:
    train: List[TrainPair]
    test: List[TestInput]
    name: str = "<unnamed>"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.train:
            raise ValueError("ARCTask: must have at least one training pair")
        if not self.test:
            raise ValueError("ARCTask: must have at least one test input")

    def __repr__(self):
        return f"ARCTask({self.name}, {len(self.train)} train, {len(self.test)} test)"

    def summary(self) -> str:
        lines = [f"ARCTask: {self.name}",
                 f"  train pairs: {len(self.train)}"]
        for i, p in enumerate(self.train):
            lines.append(f"    [{i}] in={p.input.shape} out={p.output.shape}")
        lines.append(f"  test inputs: {len(self.test)}")
        for i, t in enumerate(self.test):
            lines.append(f"    [{i}] in={t.input.shape}"
                         + (f" expected={t.expected_output.shape}" if t.expected_output else ""))
        # palette
        all_palettes = set()
        for p in self.train:
            all_palettes |= p.input.palette()
            all_palettes |= p.output.palette()
        for t in self.test:
            all_palettes |= t.input.palette()
        lines.append(f"  palette: {sorted(all_palettes)}")
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# LOADERS
# ══════════════════════════════════════════════════════════════════════════════

def _parse_grid(raw) -> Grid:
    return Grid([[int(v) for v in row] for row in raw])


def load_task(path: str, name: Optional[str] = None) -> ARCTask:
    """Load a single ARC task from a JSON file."""
    if name is None:
        name = os.path.splitext(os.path.basename(path))[0]
    with open(path, "r") as f:
        data = json.load(f)

    train = [TrainPair(input=_parse_grid(p["input"]),
                       output=_parse_grid(p["output"]))
             for p in data["train"]]
    test = [TestInput(input=_parse_grid(t["input"]),
                      expected_output=(_parse_grid(t["output"])
                                       if "output" in t else None))
            for t in data["test"]]
    return ARCTask(train=train, test=test, name=name, metadata=data.get("metadata", {}))


def load_task_from_dict(data: Dict, name: str = "<inline>") -> ARCTask:
    """Load an ARC task from an in-memory dict (matches the JSON schema)."""
    train = [TrainPair(input=_parse_grid(p["input"]),
                       output=_parse_grid(p["output"]))
             for p in data["train"]]
    test = [TestInput(input=_parse_grid(t["input"]),
                      expected_output=(_parse_grid(t["output"])
                                       if "output" in t else None))
            for t in data["test"]]
    return ARCTask(train=train, test=test, name=name)


def load_directory(dir_path: str) -> List[ARCTask]:
    """Load all .json tasks from a directory (e.g. ARC training set)."""
    tasks = []
    for fname in sorted(os.listdir(dir_path)):
        if not fname.endswith(".json"):
            continue
        try:
            tasks.append(load_task(os.path.join(dir_path, fname)))
        except Exception as e:
            print(f"  ! skip {fname}: {e}")
    return tasks
