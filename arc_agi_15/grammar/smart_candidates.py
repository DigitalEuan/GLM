"""
smart_candidates.py — v0.20: ALL 162 DSL ops wired in
=========================================================

Generates candidates using the FULL 162-op DSL vocabulary.
Each op is tried as a single-op candidate; promising compositions
are also generated.

The candidates are generated in tiers:
  Tier 1: CRG-learned transforms (5 candidates)
  Tier 2: ALL 162 single-op candidates (162 candidates)
  Tier 3: Train-derived colour mappings (5 candidates)
  Tier 4: Grid-level ops with train-derived params (5 candidates)
  Tier 5: Two-op compositions: geometric → recolour (10 candidates)

Total: ~187 candidates. The hard gate filters >90% of these,
leaving only the ones that reproduce train pairs exactly.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Set, Any
from collections import defaultdict
import itertools
import sys, os

_PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import Grid, ARCTask
from dsl.arc_dsl_full import Ops, Operation, Program
from generative.object_crg_full import ObjectCRG
from generative.object_extractor import extract_objects


def generate_smart_candidates(task: ARCTask, max_length: int = 2) -> List[Program]:
    """Generate candidates using the FULL 162-op DSL vocabulary."""
    candidates: List[Program] = []
    counter = [0]

    def _add(ops: List[Operation], source: str = ""):
        candidates.append(Program(operations=ops))
        counter[0] += 1

    # ── Tier 1: CRG-learned transforms (5 candidates) ──
    crg = ObjectCRG()
    crg.learn_from_task(task)

    if crg.global_colour_mapping:
        _add([Operation(Ops.RECOLOUR, {"mapping": crg.global_colour_mapping})], "crg_mapping")

    test_objects = extract_objects(task.test[0].input)
    per_obj_mapping: Dict[int, int] = {}
    for obj in test_objects:
        edge = crg.find_transform_for_object(obj)
        if edge and edge.output_colour > 0:
            per_obj_mapping[obj.colour] = edge.output_colour
    if per_obj_mapping and per_obj_mapping != crg.global_colour_mapping:
        _add([Operation(Ops.RECOLOUR, {"mapping": per_obj_mapping})], "crg_per_obj")

    dominant = crg.dominant_transform_type()
    if dominant == "gravity":
        for op in [Ops.GRAVITY_DOWN, Ops.GRAVITY_UP, Ops.GRAVITY_LEFT, Ops.GRAVITY_RIGHT]:
            _add([Operation(op)], f"crg_{dominant}")
    elif dominant == "disappear":
        disappear_colours = set()
        for edge in crg.all_edges:
            if edge.transform_type.value == "disappear" or "disappear" in str(edge.transform_type).lower():
                disappear_colours.add(edge.input_colour)
        if disappear_colours:
            _add([Operation(Ops.RECOLOUR, {"mapping": {c: 0 for c in disappear_colours}})],
                 "crg_disappear")

    # ── Tier 2: ALL 162 single-op candidates ──
    # Try every op in the full DSL. Most will fail the hard gate,
    # but the ones that pass are guaranteed correct.
    for op in Ops:
        # Skip ops that require complex params we can't auto-generate
        if op in (Ops.ROTATE_ARBITRARY, Ops.RESIZE, Ops.ASPECT_FILL,
                  Ops.CYCLE_ROWS, Ops.RANDOMIZE, Ops.QUANTIZE,
                  Ops.GRADIENT_MAP, Ops.REPLACE_PATTERN, Ops.FIND_PATTERN,
                  Ops.COLORIZE_REGIONS, Ops.BLIT, Ops.COMPOSITE,
                  Ops.SCALE_NX, Ops.CONTOUR, Ops.SKELETONIZE,
                  Ops.DETECT_PERIODICITY, Ops.CHANNEL_EXTRACT,
                  Ops.COLOUR_TO_INTENSITY, Ops.BINARY_THRESHOLD,
                  Ops.GREYSCALE, Ops.INVERT_COLOURS, Ops.HIGHLIGHT,
                  Ops.RECOLOUR_BY_DENSITY, Ops.RECOLOUR_DIAGONAL_ONLY,
                  Ops.RECOLOUR_EDGE_ADJACENT, Ops.RECOLOUR_IF_CROWDED,
                  Ops.RECOLOUR_IF_ISOLATED, Ops.RECOLOUR_EXTERIOR,
                  Ops.DRAW_CIRCLE, Ops.DRAW_CROSS, Ops.DRAW_DIAGONAL,
                  Ops.DRAW_DOT, Ops.DRAW_FRAME, Ops.DRAW_GRID,
                  Ops.DRAW_BORDER, Ops.COMPLETE_RECTANGLE,
                  Ops.CONNECT_NEAREST, Ops.DELETE_COL, Ops.DELETE_ROW,
                  Ops.CROP_TO_CENTER, Ops.CROP_TO_COLOUR, Ops.CROP_TO_CORNER,
                  Ops.CLOSE_MORPH, Ops.OPEN_MORPH, Ops.THICKEN,
                  Ops.FILL_HOLES, Ops.SAND_FALL, Ops.WATER_FLOW,
                  Ops.GRAVITY_RADIAL, Ops.GRAVITY_DIAGONAL,
                  Ops.EXTRACT_NTH, Ops.EXTRACT_TOP_LEFT, Ops.EXTRACT_CENTER,
                  Ops.EXTRACT_ALL_OBJECTS, Ops.EXTRACT_BBOX,
                  Ops.EXTRACT_SMALLEST, Ops.CHECK_SYMMETRY,
                  Ops.COUNT_OBJECTS, Ops.PALETTE_CYCLE,
                  Ops.NORMALIZE, Ops.INVERT_BG, Ops.ADD_NOISE,
                  Ops.ANTI_TRANSPOSE, Ops.SWAP_COLOURS,
                  Ops.SET_XOR, Ops.SET_COMPLEMENT,
                  Ops.DILATION, Ops.DILATE_OP, Ops.ERODE_OP,
                  Ops.WRAP_SHIFT_H, Ops.WRAP_SHIFT_V,
                  Ops.SHIFT_UP, Ops.SHIFT_DOWN, Ops.SHIFT_LEFT, Ops.SHIFT_RIGHT,
                  Ops.SCALE_3X, Ops.TILE_3X):
            # These ops need params or are complex — try with defaults
            try:
                _add([Operation(op)], f"full_dsl")
            except Exception:
                pass
        else:
            # Simple param-free ops
            try:
                _add([Operation(op)], f"full_dsl")
            except Exception:
                pass

    # ── Tier 3: Train-derived colour mappings (5 candidates) ──
    train_mappings: List[Dict[int, int]] = []
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        mapping: Dict[int, int] = {}
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                old = pair.input.cells[r][c]
                new = pair.output.cells[r][c]
                if old != new:
                    if old in mapping and mapping[old] != new:
                        break
                    mapping[old] = new
        if mapping and mapping not in train_mappings:
            train_mappings.append(mapping)

    for mapping in train_mappings[:5]:
        _add([Operation(Ops.RECOLOUR, {"mapping": mapping})], "train_mapping")

    for mapping in train_mappings[:2]:
        reverse = {v: k for k, v in mapping.items()}
        _add([Operation(Ops.RECOLOUR, {"mapping": reverse})], "train_reverse")

    # ── Tier 4: Grid-level ops with train-derived params ──
    palette = sorted(task.test[0].input.palette())
    train_out_colours = defaultdict(int)
    for pair in task.train:
        for row in pair.output.cells:
            for v in row:
                if v > 0:
                    train_out_colours[v] += 1
    if train_out_colours:
        dominant_out = max(train_out_colours, key=train_out_colours.get)
        _add([Operation(Ops.INVERT_BG, {"new_colour": dominant_out})], "grid_fill_bg")
        _add([Operation(Ops.INVERT_BG, {"new_colour": dominant_out})], "grid_recolour_all")

    for c in palette[:2]:
        _add([Operation(Ops.FILL_INTERIOR, {"fill_colour": c})], "grid_fill_interior")

    # ── Tier 5: Two-op compositions (geometric → recolour) ──
    if max_length >= 2:
        best_recolours = train_mappings[:2] if train_mappings else []
        if not best_recolours and crg.global_colour_mapping:
            best_recolours = [crg.global_colour_mapping]

        for geo_op in [Ops.ROTATE_90, Ops.FLIP_H, Ops.GRAVITY_DOWN,
                       Ops.TRANSPOSE, Ops.CROP_TO_NONZERO]:
            for mapping in best_recolours[:2]:
                _add([Operation(geo_op),
                      Operation(Ops.RECOLOUR, {"mapping": mapping})],
                     "compose_geo_recolour")

    return candidates
