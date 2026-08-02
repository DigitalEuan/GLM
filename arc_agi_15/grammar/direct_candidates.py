"""
direct_candidates.py — direct candidate generation for v0.4 operators
=======================================================================

The Φ-grammar maps (k, arm, layer, C, correction) tuples to DSL ops, but
some v0.4 operators need parameters that the grammar doesn't directly
invent (e.g., FILL_INTERIOR_AUTO needs the right fill_colour, which should
come from the task's output palette).

This module generates additional candidates by:
  1. Trying each v0.4 operator with parameters derived from the task
  2. Trying compositions of 2 operators (e.g., RECOLOUR then FILL_INTERIOR_AUTO)

These candidates are merged with the Φ-grammar candidates in the pipeline.
"""

from __future__ import annotations
from typing import List, Set, Dict, Any, Optional
import itertools
import sys, os

_PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import Grid, ARCTask
from dsl import Ops, Operation, Program


def _task_palette(task: ARCTask) -> Set[int]:
    """All non-zero colours appearing anywhere in the task."""
    pal = set()
    for p in task.train:
        pal |= p.input.palette()
        pal |= p.output.palette()
    for t in task.test:
        pal |= t.input.palette()
    return pal


def _output_palette(task: ARCTask) -> Set[int]:
    """Colours that appear in train outputs but not in train inputs (new colours)."""
    in_pal = set()
    out_pal = set()
    for p in task.train:
        in_pal |= p.input.palette()
        out_pal |= p.output.palette()
    return out_pal - in_pal


def _all_palette(task: ARCTask) -> Set[int]:
    """All colours (including 0) appearing anywhere."""
    return _task_palette(task) | {0}


def generate_direct_candidates(task: ARCTask, max_length: int = 2) -> List[Program]:
    """Generate candidates by trying v0.4 operators with task-derived parameters.

    This complements the Φ-grammar generator by ensuring that operators
    like FILL_INTERIOR_AUTO get tried with every relevant fill colour
    from the task's palette.
    """
    palette = sorted(_task_palette(task))
    output_palette = sorted(_output_palette(task))
    all_colours = palette + output_palette + [1, 2, 3]  # fallback defaults
    all_colours = list(set(all_colours))  # dedupe

    candidates: List[Program] = []
    counter = 0

    def _add(ops: List[Operation]):
        nonlocal counter
        candidates.append(Program(operations=ops, name=f"direct_{counter:04d}"))
        counter += 1

    # ── Length-1 candidates: each v0.4 operator with relevant params ──

    # FILL_INTERIOR_AUTO with each possible fill colour
    for fill_c in all_colours:
        _add([Operation(Ops.FILL_INTERIOR_AUTO, {"fill_colour": fill_c})])

    # RECOLOUR_INTERIOR with each possible new colour
    for new_c in all_colours:
        _add([Operation(Ops.RECOLOUR_INTERIOR, {"new_colour": new_c})])

    # RECOLOUR_BG with each possible colour
    for new_c in all_colours:
        _add([Operation(Ops.RECOLOUR_BG, {"new_colour": new_c})])

    # RECOLOUR_NONZERO with each possible colour
    for new_c in all_colours:
        _add([Operation(Ops.RECOLOUR_NONZERO, {"new_colour": new_c})])

    # RECOLOUR with all single-colour mappings
    for c1 in palette:
        for c2 in all_colours:
            if c1 != c2:
                _add([Operation(Ops.RECOLOUR, {"mapping": {c1: c2}})])

    # RECOLOUR with all two-colour swaps
    for c1, c2 in itertools.combinations(palette, 2):
        _add([Operation(Ops.RECOLOUR, {"mapping": {c1: c2, c2: c1}})])

    # RECOLOUR_IF_NEIGHBOUR with palette-derived params
    for target_c in [0] + palette:
        for neigh_c in palette:
            for new_c in all_colours:
                if target_c != neigh_c and target_c != new_c:
                    _add([Operation(Ops.RECOLOUR_IF_NEIGHBOUR, {
                        "target_colour": target_c,
                        "neighbour_colour": neigh_c,
                        "new_colour": new_c,
                    })])

    # RECOLOUR_IF_BORDER with each possible colour
    for new_c in all_colours:
        _add([Operation(Ops.RECOLOUR_IF_BORDER, {"new_colour": new_c, "target_colour": 0})])

    # RECOLOUR_IF_CORNER with each possible colour
    for new_c in all_colours:
        _add([Operation(Ops.RECOLOUR_IF_CORNER, {"new_colour": new_c})])

    # Param-free geometric operators
    for op in [Ops.IDENTITY, Ops.ROTATE_90, Ops.ROTATE_180, Ops.ROTATE_270,
               Ops.FLIP_H, Ops.FLIP_V, Ops.TRANSPOSE,
               Ops.GRAVITY_DOWN, Ops.GRAVITY_UP, Ops.GRAVITY_LEFT, Ops.GRAVITY_RIGHT,
               Ops.CROP_TO_NONZERO, Ops.SCALE_2X, Ops.SCALE_HALF,
               Ops.DILATE, Ops.ERODE,
               Ops.TILE_2X, Ops.TILE_3X,
               Ops.EXTRACT_LARGEST, Ops.OUTLINE, Ops.COUNT_FILL]:
        _add([Operation(op)])

    # EXTRACT_COLOUR with each palette colour
    for c in palette:
        _add([Operation(Ops.EXTRACT_COLOUR, {"colour": c})])

    if max_length >= 2:
        # ── Length-2 candidates: promising compositions ──
        # Recolour-then-geometric and geometric-then-recolour
        geometric_ops = [Ops.ROTATE_90, Ops.ROTATE_180, Ops.ROTATE_270,
                         Ops.FLIP_H, Ops.FLIP_V, Ops.TRANSPOSE,
                         Ops.GRAVITY_DOWN, Ops.GRAVITY_UP, Ops.GRAVITY_LEFT, Ops.GRAVITY_RIGHT,
                         Ops.CROP_TO_NONZERO, Ops.TILE_2X, Ops.TILE_3X]
        recolour_ops = []
        for c in all_colours:
            recolour_ops.append(Operation(Ops.RECOLOUR_BG, {"new_colour": c}))
            recolour_ops.append(Operation(Ops.RECOLOUR_NONZERO, {"new_colour": c}))
            recolour_ops.append(Operation(Ops.FILL_INTERIOR_AUTO, {"fill_colour": c}))

        # geometric → recolour
        for geo_op in geometric_ops:
            for rec_op in recolour_ops:
                _add([Operation(geo_op), rec_op])

        # recolour → geometric (fewer combos to avoid blowup)
        for rec_op in recolour_ops[:6]:  # cap
            for geo_op in geometric_ops[:6]:  # cap
                _add([rec_op, Operation(geo_op)])

    return candidates
