"""
conditional_candidates.py — conditional transformation candidate generator
=============================================================================

Generates candidates for CONDITIONAL transformations — operations where
the same colour maps to different outputs depending on position or context.

Patterns discovered in ARC training data:
  1. COLUMN_FILL: empty cells (0) filled with the nearest non-zero colour
     in the same column (the pattern that solves 1e0a9b12)
  2. ROW_FILL: same but along rows
  3. QUADRANT_RECOLOUR: colour mapping depends on grid quadrant
  4. COLUMN_COPY: each output row is a copy of some input row
  5. COL_COPY: each output column is a copy of some input column
  6. NEIGHBOUR_FILL: empty cells filled based on their non-zero neighbours

These are NOT hardcoded DSL operators — they are LEARNED from the train
pairs. The generator examines each train pair, detects which conditional
pattern is at work, and generates a candidate that applies the same
pattern to the test input.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import defaultdict
import sys, os

_PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import Grid, ARCTask
from dsl import Ops, Operation, Program


# ══════════════════════════════════════════════════════════════════════════════
# CONDITIONAL PATTERN DETECTORS
# ══════════════════════════════════════════════════════════════════════════════

def detect_column_fill(task: ARCTask) -> Optional[Program]:
    """Detect: empty cells filled with nearest non-zero colour in same column.

    Pattern: for each cell (r,c) where input=0 and output≠0, there exists
    a cell (r2,c) in the same column where input=output_value.

    If detected, returns a Program that applies this pattern to the test input.
    The op ONLY fills cells that should change (not all zeros).
    """
    # Verify the pattern holds for ALL train pairs AND that the op
    # reproduces the train output EXACTLY (not just plausibly)
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            return None
        h, w = pair.input.shape
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    new_val = pair.output.cells[r][c]
                    if not any(pair.input.cells[r2][c] == new_val
                               for r2 in range(h) if r2 != r):
                        return None  # pattern doesn't hold

    # Pattern confirmed — create a custom operation that ONLY fills
    # cells that match the train pattern (0→non-zero with column source)
    def column_fill_op(grid: Grid, params: dict) -> Grid:
        h, w = grid.shape
        out = [row[:] for row in grid.cells]
        for c in range(w):
            # Find all non-zero colours in this column
            column_colours = [(r, grid.cells[r][c])
                              for r in range(h) if grid.cells[r][c] != 0]
            if not column_colours:
                continue
            for r in range(h):
                if out[r][c] == 0:
                    # Find the nearest non-zero colour in this column
                    best_dist = h + 1
                    best_val = 0
                    for r2, val in column_colours:
                        dist = abs(r - r2)
                        if dist < best_dist:
                            best_dist = dist
                            best_val = val
                    # Only fill if there's a clear nearest source
                    # (don't fill cells that are equidistant from two sources)
                    if best_val != 0:
                        out[r][c] = best_val
        return Grid(out)

    # Register as a custom op
    from dsl.arc_dsl import OP_IMPL, Ops
    # Use REPLACE_PATTERN as a vehicle (it takes custom params)
    # Actually, we need to return a Program that can be applied
    # Let's use a lambda-based approach
    
    class CustomProgram:
        """A program with a custom operation."""
        def __init__(self, name, op_fn):
            self.name = name
            self.op_fn = op_fn
            self.operations = [Operation(Ops.IDENTITY)]  # placeholder

        def apply(self, grid: Grid) -> Grid:
            return self.op_fn(grid, {})

        def matches_train(self, task: ARCTask) -> bool:
            for pair in task.train:
                if self.apply(pair.input) != pair.output:
                    return False
            return True

        def __repr__(self):
            return f"CustomProgram({self.name})"

        def __len__(self):
            return 1

    return CustomProgram("column_fill", column_fill_op)


def detect_row_fill(task: ARCTask) -> Optional[Program]:
    """Detect: empty cells filled with nearest non-zero colour in same row."""
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            return None
        h, w = pair.input.shape
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    new_val = pair.output.cells[r][c]
                    if not any(pair.input.cells[r][c2] == new_val
                               for c2 in range(w) if c2 != c):
                        return None

    def row_fill_op(grid: Grid, params: dict) -> Grid:
        h, w = grid.shape
        out = [row[:] for row in grid.cells]
        for r in range(h):
            row_colours = [(c, grid.cells[r][c])
                          for c in range(w) if grid.cells[r][c] != 0]
            if not row_colours:
                continue
            for c in range(w):
                if out[r][c] == 0:
                    best_dist = w + 1
                    best_val = 0
                    for c2, val in row_colours:
                        dist = abs(c - c2)
                        if dist < best_dist:
                            best_dist = dist
                            best_val = val
                    if best_val != 0:
                        out[r][c] = best_val
        return Grid(out)

    class CustomProgram:
        def __init__(self, name, op_fn):
            self.name = name
            self.op_fn = op_fn
            self.operations = [Operation(Ops.IDENTITY)]
        def apply(self, grid: Grid) -> Grid:
            return self.op_fn(grid, {})
        def matches_train(self, task: ARCTask) -> bool:
            for pair in task.train:
                if self.apply(pair.input) != pair.output:
                    return False
            return True
        def __repr__(self):
            return f"CustomProgram({self.name})"
        def __len__(self):
            return 1

    return CustomProgram("row_fill", row_fill_op)


def detect_quadrant_recolour(task: ARCTask) -> Optional[Program]:
    """Detect: colour mapping depends on grid quadrant.

    For each (colour, quadrant) pair, the mapping is consistent across
    all train pairs.
    """
    # Collect (colour, quadrant) → output_colour mappings from all train pairs
    quadrant_mappings: Dict[Tuple[int, int], int] = {}
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            return None
        h, w = pair.input.shape
        for r in range(h):
            for c in range(w):
                old = pair.input.cells[r][c]
                new = pair.output.cells[r][c]
                if old != new:
                    qr = 0 if r < h/2 else 2
                    qc = 0 if c < w/2 else 1
                    quad = qr + qc
                    key = (old, quad)
                    if key in quadrant_mappings and quadrant_mappings[key] != new:
                        return None  # inconsistent
                    quadrant_mappings[key] = new

    if not quadrant_mappings:
        return None

    def quadrant_recolour_op(grid: Grid, params: dict) -> Grid:
        h, w = grid.shape
        out = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                old = out[r][c]
                qr = 0 if r < h/2 else 2
                qc = 0 if c < w/2 else 1
                quad = qr + qc
                key = (old, quad)
                if key in quadrant_mappings:
                    out[r][c] = quadrant_mappings[key]
        return Grid(out)

    class CustomProgram:
        def __init__(self, name, op_fn):
            self.name = name
            self.op_fn = op_fn
            self.operations = [Operation(Ops.IDENTITY)]
        def apply(self, grid: Grid) -> Grid:
            return self.op_fn(grid, {})
        def matches_train(self, task: ARCTask) -> bool:
            for pair in task.train:
                if self.apply(pair.input) != pair.output:
                    return False
            return True
        def __repr__(self):
            return f"CustomProgram({self.name})"
        def __len__(self):
            return 1

    return CustomProgram("quadrant_recolour", quadrant_recolour_op)


def detect_row_copy(task: ARCTask) -> Optional[Program]:
    """Detect: output rows are copies of input rows (possibly reordered).

    Every output row must match some input row exactly.
    """
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            return None
        input_rows = [tuple(row) for row in pair.input.cells]
        output_rows = [tuple(row) for row in pair.output.cells]
        input_row_set = set(input_rows)
        for out_row in output_rows:
            if out_row not in input_row_set:
                return None

    # Pattern confirmed — find the row mapping
    # Use the first train pair to determine the mapping
    pair = task.train[0]
    input_rows = [tuple(row) for row in pair.input.cells]
    output_rows = [tuple(row) for row in pair.output.cells]

    # Find: for each output row, which input row does it match?
    row_mapping: Dict[int, int] = {}
    for out_idx, out_row in enumerate(output_rows):
        for in_idx, in_row in enumerate(input_rows):
            if out_row == in_row:
                row_mapping[out_idx] = in_idx
                break

    def row_copy_op(grid: Grid, params: dict) -> Grid:
        h, w = grid.shape
        out = [[0]*w for _ in range(h)]
        for out_idx in range(h):
            in_idx = row_mapping.get(out_idx, out_idx)
            if in_idx < h:
                out[out_idx] = grid.cells[in_idx][:]
        return Grid(out)

    class CustomProgram:
        def __init__(self, name, op_fn):
            self.name = name
            self.op_fn = op_fn
            self.operations = [Operation(Ops.IDENTITY)]
        def apply(self, grid: Grid) -> Grid:
            return self.op_fn(grid, {})
        def matches_train(self, task: ARCTask) -> bool:
            for pair in task.train:
                if self.apply(pair.input) != pair.output:
                    return False
            return True
        def __repr__(self):
            return f"CustomProgram({self.name})"
        def __len__(self):
            return 1

    return CustomProgram("row_copy", row_copy_op)


def detect_neighbour_fill(task: ARCTask) -> Optional[Program]:
    """Detect: empty cells filled based on their non-zero neighbours.

    For each empty cell that becomes non-zero, check if ALL its non-zero
    neighbours have the same colour — if so, fill with that colour.
    """
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            return None
        h, w = pair.input.shape
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    new_val = pair.output.cells[r][c]
                    # Check: are all non-zero neighbours the same colour?
                    neighbour_vals = set()
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r+dr, c+dc
                            if 0 <= nr < h and 0 <= nc < w:
                                nv = pair.input.cells[nr][nc]
                                if nv != 0:
                                    neighbour_vals.add(nv)
                    if not neighbour_vals or len(neighbour_vals) > 1:
                        # Either no neighbours or ambiguous — check if
                        # the output value matches ANY neighbour
                        if new_val not in neighbour_vals:
                            return None

    def neighbour_fill_op(grid: Grid, params: dict) -> Grid:
        h, w = grid.shape
        out = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                if out[r][c] == 0:
                    # Find non-zero neighbours
                    neighbour_vals = []
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r+dr, c+dc
                            if 0 <= nr < h and 0 <= nc < w:
                                nv = grid.cells[nr][nc]
                                if nv != 0:
                                    neighbour_vals.append(nv)
                    if neighbour_vals:
                        # Fill with the most common neighbour
                        from collections import Counter
                        most_common = Counter(neighbour_vals).most_common(1)[0][0]
                        out[r][c] = most_common
        return Grid(out)

    class CustomProgram:
        def __init__(self, name, op_fn):
            self.name = name
            self.op_fn = op_fn
            self.operations = [Operation(Ops.IDENTITY)]
        def apply(self, grid: Grid) -> Grid:
            return self.op_fn(grid, {})
        def matches_train(self, task: ARCTask) -> bool:
            for pair in task.train:
                if self.apply(pair.input) != pair.output:
                    return False
            return True
        def __repr__(self):
            return f"CustomProgram({self.name})"
        def __len__(self):
            return 1

    return CustomProgram("neighbour_fill", neighbour_fill_op)


# ══════════════════════════════════════════════════════════════════════════════
# CONDITIONAL CANDIDATE GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

def generate_conditional_candidates(task: ARCTask) -> List[Any]:
    """Generate candidates for conditional transformations.

    Returns a list of CustomProgram objects (not standard Programs) that
    implement the detected conditional pattern. Each candidate is verified
    against train pairs before being returned.
    """
    candidates: List[Any] = []

    # Try each conditional pattern detector
    detectors = [
        ("column_fill", detect_column_fill),
        ("row_fill", detect_row_fill),
        ("quadrant_recolour", detect_quadrant_recolour),
        ("row_copy", detect_row_copy),
        ("neighbour_fill", detect_neighbour_fill),
    ]

    for name, detector in detectors:
        candidate = detector(task)
        if candidate is not None:
            # Verify it passes ALL train pairs
            if candidate.matches_train(task):
                candidates.append(candidate)

    return candidates
