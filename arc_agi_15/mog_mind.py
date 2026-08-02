"""
mog_mind.py — The MOG-Mind: A Substrate-Native Cognitive Architecture
======================================================================

Not a solver pipeline. A mind.

The MOG-mind perceives ARC tasks through 4 semantic channels (the MOG rows),
interprets what it sees, selects a driving style, generates candidates,
and learns from feedback.

Architecture (mirrors the MOG 4×6 structure):

  PERCEPTION (4 channels, like the 4 MOG rows):
    Channel 0 — M_Mass:      What colours exist, where, how many
    Channel 1 — I_Info:      What's adjacent to what (topology)
    Channel 2 — A_Activation: What's changing (deltas)
    Channel 3 — P_Potential:  What could change (latent structure)

  INTERPRETATION (6 spatial blocks, like the 6 MOG columns):
    Block 0 — Object inventory:    What objects exist
    Block 1 — Colour semantics:    What colours mean
    Block 2 — Spatial relations:   How objects relate
    Block 3 — Transformation type: What kind of change
    Block 4 — Complexity gauge:    How hard is this
    Block 5 — Style hint:          Which driving style fits

  REASONING:
    The mind selects a driving style based on interpretation,
    then generates candidates using that style's toolkit.

  LEARNING:
    After verification, the mind records what worked and what didn't,
    building experience over tasks.

The driving styles (from driving_ubp_glm.txt):
  - Machining:    Reduce to simplest form (minimise TAX)
  - Resonant:     Match a pattern (maximise NRCI)
  - Differential: Transform the delta (minimise transformation energy)
  - Geodesic:     Shortest path in grid space
  - Entropic:     Reach equilibrium (remove noise)
  - Flow:         Continuous deformation (fill, expand)
  - Ballistic:    Track object trajectories
  - Compression:  Reduce dimensionality (crop, extract)
"""

from __future__ import annotations
import os, sys, json, time, math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arc_loader import ARCTask, Grid, load_task
from v062_unified_learning import (
    gravity_down, local_swap, colour_center_fill,
    column_rank_fill, marker_fill_85, cond_recolour,
    verify_and_predict, extract_objects,
)
from v032_distance_rule import try_distance_diagonal_rule
from v065_ubp_glm import learn_multi_interior_fill
from geometric_perception import (
    extract_geometric_objects, analyse_transformation,
    learn_geometric_pattern, generate_geometric_candidates,
    verify_geometric_candidate, geometric_report,
    GeometricObject, GeometricTransformation, GeometricPattern,
)


# ═══════════════════════════════════════════════════════════════════════════════
# PERCEPTION — The 4 MOG Channels
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Perception:
    """What the mind sees when it looks at a grid."""
    # Channel 0: Mass (colour distribution)
    palette: Set[int] = field(default_factory=set)
    colour_histogram: Dict[int, int] = field(default_factory=dict)
    n_nonzero: int = 0
    density: float = 0.0  # fraction of non-zero cells

    # Channel 1: Info (adjacency topology)
    adjacency_graph: Dict[Tuple[int,int], Set[int]] = field(default_factory=dict)
    n_components: Dict[int, int] = field(default_factory=dict)  # colour → count
    boundary_cells: List[Tuple[int,int]] = field(default_factory=list)

    # Channel 2: Activation (change potential)
    n_empty: int = 0
    n_stable: int = 0  # cells with all same-colour neighbours
    n_boundary: int = 0  # cells with mixed neighbours

    # Channel 3: Potential (structural skeleton)
    rows: int = 0
    cols: int = 0
    is_square: bool = False
    has_border_pattern: bool = False
    dominant_colour: int = 0

    # Geometric objects (from spatial_arithmetic)
    geometric_objects: List[Any] = field(default_factory=list)


def perceive(grid: Grid) -> Perception:
    """Extract all 4 MOG channels from a grid."""
    p = Perception()
    h, w = grid.height, grid.width
    p.rows, p.cols = h, w
    p.is_square = (h == w)

    cells = grid.cells

    # Channel 0: Mass
    for r in range(h):
        for c in range(w):
            v = cells[r][c]
            p.colour_histogram[v] = p.colour_histogram.get(v, 0) + 1
            if v != 0:
                p.n_nonzero += 1
                p.palette.add(v)
    p.density = p.n_nonzero / (h * w) if h * w > 0 else 0
    if p.colour_histogram:
        p.dominant_colour = max(
            (k for k in p.colour_histogram if k != 0),
            key=lambda k: p.colour_histogram[k],
            default=0
        )

    # Channel 1: Info (adjacency)
    for r in range(h):
        for c in range(w):
            v = cells[r][c]
            neighbours = set()
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < h and 0 <= nc < w:
                    neighbours.add(cells[nr][nc])
            p.adjacency_graph[(r,c)] = neighbours

            if v != 0:
                # Count same-colour neighbours for component detection
                same = sum(1 for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]
                          if 0<=r+dr<h and 0<=c+dc<w and cells[r+dr][c+dc]==v)
                if same == 0:
                    p.boundary_cells.append((r,c))

    # Components (simplified BFS)
    visited = set()
    for r in range(h):
        for c in range(w):
            if (r,c) in visited or cells[r][c] == 0:
                continue
            colour = cells[r][c]
            queue = [(r,c)]
            while queue:
                cr, cc = queue.pop()
                if (cr,cc) in visited:
                    continue
                if cells[cr][cc] != colour:
                    continue
                visited.add((cr,cc))
                for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0<=nr<h and 0<=nc<w and (nr,nc) not in visited:
                        queue.append((nr,nc))
            p.n_components[colour] = p.n_components.get(colour, 0) + 1

    # Channel 2: Activation
    for r in range(h):
        for c in range(w):
            v = cells[r][c]
            neighbours = p.adjacency_graph[(r,c)]
            if v == 0:
                p.n_empty += 1
            elif len(neighbours - {v, 0}) == 0:
                p.n_stable += 1
            else:
                p.n_boundary += 1

    # Channel 3: Potential
    # Check border pattern
    border_colours = set()
    for r in range(h):
        border_colours.add(cells[r][0])
        border_colours.add(cells[r][w-1])
    for c in range(w):
        border_colours.add(cells[0][c])
        border_colours.add(cells[h-1][c])
    p.has_border_pattern = (len(border_colours) > 1)

    # Geometric objects (from spatial_arithmetic)
    p.geometric_objects = extract_geometric_objects(grid)

    return p


# ═══════════════════════════════════════════════════════════════════════════════
# INTERPRETATION — The 6 Spatial Blocks
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Interpretation:
    """What the mind understands about a task."""
    # Block 0: Object inventory
    n_objects: int = 0
    object_sizes: List[int] = field(default_factory=list)
    has_large_objects: bool = False

    # Block 1: Colour semantics
    colour_map: Dict[int, int] = field(default_factory=dict)  # learned mapping
    is_consistent_recolour: bool = False
    is_conditional_recolour: bool = False

    # Block 2: Spatial relations
    is_same_size: bool = False
    size_change: Optional[Tuple[int,int,int,int]] = None  # (h_in,w_in,h_out,w_out)

    # Block 3: Transformation type
    transformation_type: str = "unknown"
    # Types: identity, recolour, fill, delete, move, rotate, scale, compose

    # Block 4: Complexity
    n_changes: int = 0
    change_ratio: float = 0.0
    complexity: str = "low"  # low, medium, high

    # Block 5: Style hint
    suggested_style: str = "machining"
    style_confidence: float = 0.0

    # Geometric understanding
    geometric_pattern: Optional[Any] = None
    geometric_insight: str = ""


def interpret(task: ARCTask) -> Interpretation:
    """Interpret what a task is asking, using all 4 perception channels."""
    interp = Interpretation()

    # Analyse train pairs
    pair0 = task.train[0]
    inp_perception = perceive(pair0.input)
    out_perception = perceive(pair0.output)

    # Block 2: Size
    interp.is_same_size = all(
        p.input.shape == p.output.shape for p in task.train
    )
    if not interp.is_same_size:
        interp.size_change = (
            pair0.input.height, pair0.input.width,
            pair0.output.height, pair0.output.width
        )

    # Block 0: Objects
    interp.n_objects = sum(inp_perception.n_components.values())
    interp.object_sizes = []
    for colour, count in inp_perception.n_components.items():
        interp.object_sizes.append(count)
    interp.has_large_objects = any(s > 5 for s in interp.object_sizes)

    # Block 1: Colour semantics
    if interp.is_same_size:
        colour_map = {}
        consistent = True
        for pair in task.train:
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    src = pair.input.cells[r][c]
                    dst = pair.output.cells[r][c]
                    if src != dst:
                        if src in colour_map and colour_map[src] != dst:
                            consistent = False
                            break
                        colour_map[src] = dst
            if not consistent:
                break
        if consistent and colour_map:
            interp.is_consistent_recolour = True
            interp.colour_map = colour_map

    # Block 3: Transformation type
    if interp.is_same_size:
        n_filled = 0
        n_deleted = 0
        n_recoloured = 0
        for pair in task.train:
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    iv = pair.input.cells[r][c]
                    ov = pair.output.cells[r][c]
                    if iv != ov:
                        if iv == 0:
                            n_filled += 1
                        elif ov == 0:
                            n_deleted += 1
                        else:
                            n_recoloured += 1

        interp.n_changes = n_filled + n_deleted + n_recoloured
        total_cells = sum(p.input.height * p.input.width for p in task.train)
        interp.change_ratio = interp.n_changes / total_cells if total_cells > 0 else 0

        if interp.n_changes == 0:
            interp.transformation_type = "identity"
        elif n_filled > 0 and n_deleted == 0 and n_recoloured == 0:
            interp.transformation_type = "fill"
        elif n_filled == 0 and n_deleted > 0 and n_recoloured == 0:
            interp.transformation_type = "delete"
        elif n_filled == 0 and n_deleted == 0 and n_recoloured > 0:
            interp.transformation_type = "recolour"
        elif n_filled > 0 and n_deleted > 0:
            interp.transformation_type = "compose"
        else:
            interp.transformation_type = "mixed"
    else:
        interp.transformation_type = "scale"

    # Block 4: Complexity
    if interp.change_ratio < 0.05:
        interp.complexity = "low"
    elif interp.change_ratio < 0.2:
        interp.complexity = "medium"
    else:
        interp.complexity = "high"

    # Block 5: Style suggestion
    interp.suggested_style, interp.style_confidence = _suggest_style(interp, inp_perception, out_perception)

    # Geometric understanding (deferred to avoid timeout)
    interp.geometric_pattern = None
    interp.geometric_insight = "deferred"

    return interp


def _suggest_style(interp: Interpretation, inp: Perception, out: Perception) -> Tuple[str, float]:
    """Suggest a driving style based on interpretation."""
    if interp.transformation_type == "identity":
        return "machining", 1.0

    if interp.transformation_type == "scale":
        return "compression", 0.9

    if interp.is_consistent_recolour:
        return "resonant", 0.9  # Pattern matching

    if interp.transformation_type == "fill":
        if inp.n_empty > 0:
            return "flow", 0.8  # Fluid fill
        return "entropic", 0.7

    if interp.transformation_type == "recolour":
        if interp.complexity == "low":
            return "differential", 0.8  # Small delta
        return "resonant", 0.7

    if interp.transformation_type == "compose":
        return "recursive", 0.6  # Multi-step

    if interp.complexity == "high":
        return "machining", 0.5  # Default to reduction

    return "geodesic", 0.5  # Default: shortest path


# ═══════════════════════════════════════════════════════════════════════════════
# DRIVING STYLES — The Toolkits
# ═══════════════════════════════════════════════════════════════════════════════

def _learn_colour_map(task: ARCTask) -> Dict[int, int]:
    """Learn consistent colour mapping from train pairs."""
    mapping = {}
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                src = pair.input.cells[r][c]
                dst = pair.output.cells[r][c]
                if src != dst:
                    if src in mapping and mapping[src] != dst:
                        return {}
                    mapping[src] = dst
    return mapping


def generate_candidates_by_style(task: ARCTask, style: str,
                                   interp: Interpretation) -> List[Tuple[str, Grid]]:
    """Generate candidates using the selected driving style's toolkit."""
    test = task.test[0].input
    h, w = test.height, test.width
    candidates = []

    try:
        if style == "machining":
            candidates.extend(_machining_candidates(task, test, interp))
        elif style == "resonant":
            candidates.extend(_resonant_candidates(task, test, interp))
        elif style == "differential":
            candidates.extend(_differential_candidates(task, test, interp))
        elif style == "flow":
            candidates.extend(_flow_candidates(task, test, interp))
        elif style == "entropic":
            candidates.extend(_entropic_candidates(task, test, interp))
        elif style == "geodesic":
            candidates.extend(_geodesic_candidates(task, test, interp))
        elif style == "compression":
            candidates.extend(_compression_candidates(task, test, interp))
        elif style == "recursive":
            candidates.extend(_recursive_candidates(task, test, interp))
        elif style == "toolkit":
            candidates.extend(_toolkit_candidates(task, test, interp))
        elif style == "geometric":
            candidates.extend(_geometric_candidates(task, test, interp))
    except Exception:
        pass  # Style failed, continue

    # Always add identity as fallback
    candidates.append(("identity", Grid([row[:] for row in test.cells])))

    return candidates


# ─── Style: Geometric (Spatial Arithmetic) ──────────────────────────────────

def _geometric_candidates(task, test, interp):
    """Generate candidates using geometric understanding from spatial_arithmetic."""
    cands = []

    if interp.geometric_pattern:
        geo_cands = generate_geometric_candidates(task, interp.geometric_pattern)
        cands.extend(geo_cands)

    return cands


# ─── Style: Machining (Reduce) ──────────────────────────────────────────────

def _machining_candidates(task, test, interp):
    """Reduce to simplest stable form."""
    cands = []
    h, w = test.height, test.width

    # Fill all zeros with dominant colour
    non_zero = [v for row in test.cells for v in row if v != 0]
    if non_zero:
        fill = Counter(non_zero).most_common(1)[0][0]
        cells = [[fill if test.cells[r][c] == 0 else test.cells[r][c]
                   for c in range(w)] for r in range(h)]
        cands.append(("machining_fill", Grid(cells)))

    # Gravity down
    cells = [[0]*w for _ in range(h)]
    for c in range(w):
        col = [test.cells[r][c] for r in range(h) if test.cells[r][c] != 0]
        for i, v in enumerate(col):
            cells[h - len(col) + i][c] = v
    cands.append(("machining_gravity", Grid(cells)))

    return cands


# ─── Style: Resonant (Pattern Match) ────────────────────────────────────────

def _resonant_candidates(task, test, interp):
    """Match patterns from train pairs."""
    cands = []
    h, w = test.height, test.width

    # Apply learned colour map
    if interp.colour_map:
        cm = interp.colour_map
        cells = [[cm.get(test.cells[r][c], test.cells[r][c])
                   for c in range(w)] for r in range(h)]
        cands.append(("resonant_recolour", Grid(cells)))

    # Try each train pair's mapping
    for i, pair in enumerate(task.train):
        if pair.input.shape != pair.output.shape:
            continue
        cm = {}
        ok = True
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                s, d = pair.input.cells[r][c], pair.output.cells[r][c]
                if s != d:
                    if s in cm and cm[s] != d:
                        ok = False
                        break
                    cm[s] = d
            if not ok:
                break
        if ok and cm:
            cells = [[cm.get(test.cells[r][c], test.cells[r][c])
                       for c in range(w)] for r in range(h)]
            cands.append((f"resonant_pair{i}", Grid(cells)))

    return cands


# ─── Style: Differential (Minimal Delta) ────────────────────────────────────

def _differential_candidates(task, test, interp):
    """Apply the minimal transformation delta."""
    cands = []
    h, w = test.height, test.width

    # Learn neighbour-conditional rules
    rules = {}
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                iv = pair.input.cells[r][c]
                ov = pair.output.cells[r][c]
                if iv == ov:
                    continue
                n_cols = []
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < pair.input.height and 0 <= nc < pair.input.width:
                        n_cols.append(pair.input.cells[nr][nc])
                key = (iv, tuple(sorted(n_cols)))
                if key in rules and rules[key] != ov:
                    rules = None
                    break
                rules[key] = ov
        if rules is None:
            break

    if rules:
        cells = [row[:] for row in test.cells]
        changed = False
        for r in range(h):
            for c in range(w):
                n_cols = []
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w:
                        n_cols.append(test.cells[nr][nc])
                key = (test.cells[r][c], tuple(sorted(n_cols)))
                if key in rules:
                    cells[r][c] = rules[key]
                    changed = True
        if changed:
            cands.append(("differential_neighbour", Grid(cells)))

    return cands


# ─── Style: Flow (Fill/Expand) ──────────────────────────────────────────────

def _flow_candidates(task, test, interp):
    """Fill/expand like a fluid."""
    cands = []
    h, w = test.height, test.width

    # Uniform fill
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        fills = set()
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    fills.add(pair.output.cells[r][c])
        if len(fills) == 1:
            fill = next(iter(fills))
            cells = [[fill if test.cells[r][c] == 0 else test.cells[r][c]
                       for c in range(w)] for r in range(h)]
            cands.append(("flow_uniform", Grid(cells)))
            break

    # Marker dilate (fill zeros adjacent to specific colour)
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        marker_map = {}  # marker_colour -> fill_colour
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    fill = pair.output.cells[r][c]
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < pair.input.height and 0 <= nc < pair.input.width:
                            mc = pair.input.cells[nr][nc]
                            if mc != 0:
                                if mc in marker_map and marker_map[mc] != fill:
                                    marker_map = None
                                    break
                                marker_map[mc] = fill
                    if marker_map is None:
                        break
            if marker_map is None:
                break

        if marker_map:
            cells = [row[:] for row in test.cells]
            changed = False
            for r in range(h):
                for c in range(w):
                    if cells[r][c] != 0:
                        continue
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w:
                            mc = cells[nr][nc]
                            if mc in marker_map:
                                cells[r][c] = marker_map[mc]
                                changed = True
                                break
            if changed:
                cands.append(("flow_dilate", Grid(cells)))
            break

    return cands


# ─── Style: Entropic (Equilibrium) ──────────────────────────────────────────

def _entropic_candidates(task, test, interp):
    """Remove noise, reach equilibrium."""
    cands = []
    h, w = test.height, test.width

    # Interior fill (enclosed regions)
    regions = _enclosed_zero_regions(test)
    if regions:
        # Learn fill colour from train pairs
        size_to_fill = {}
        for pair in task.train:
            if pair.input.shape != pair.output.shape:
                continue
            train_regions = _enclosed_zero_regions(pair.input)
            for region in train_regions:
                fills = {pair.output.cells[r][c] for r, c in region}
                if len(fills) == 1:
                    size_to_fill[len(region)] = next(iter(fills))

        if size_to_fill:
            cells = [row[:] for row in test.cells]
            changed = False
            for region in regions:
                fill = size_to_fill.get(len(region))
                if fill is not None:
                    for r, c in region:
                        cells[r][c] = fill
                        changed = True
            if changed:
                cands.append(("entropic_interior", Grid(cells)))

    return cands


def _enclosed_zero_regions(grid: Grid) -> List[List[Tuple[int,int]]]:
    """Find enclosed zero regions (not connected to border)."""
    h, w = grid.height, grid.width
    border_connected = set()
    stack = []
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == 0 and (r==0 or r==h-1 or c==0 or c==w-1):
                border_connected.add((r,c))
                stack.append((r,c))
    while stack:
        r, c = stack.pop()
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0<=nr<h and 0<=nc<w and (nr,nc) not in border_connected and grid.cells[nr][nc]==0:
                border_connected.add((nr,nc))
                stack.append((nr,nc))

    enclosed = {(r,c) for r in range(h) for c in range(w)
                if grid.cells[r][c]==0 and (r,c) not in border_connected}
    regions = []
    visited = set()
    for cell in enclosed:
        if cell in visited:
            continue
        region = []
        stack = [cell]
        while stack:
            r, c = stack.pop()
            if (r,c) in visited:
                continue
            visited.add((r,c))
            region.append((r,c))
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nxt = (r+dr, c+dc)
                if nxt in enclosed and nxt not in visited:
                    stack.append(nxt)
        regions.append(region)
    return regions


# ─── Style: Geodesic (Shortest Path) ────────────────────────────────────────

def _geodesic_candidates(task, test, interp):
    """Shortest path from input to output."""
    cands = []

    # Try: apply each train pair's transformation directly
    for i, pair in enumerate(task.train):
        if pair.input.shape != pair.output.shape:
            continue
        # Compute the delta grid
        delta = []
        for r in range(pair.input.height):
            row = []
            for c in range(pair.input.width):
                row.append(pair.output.cells[r][c] - pair.input.cells[r][c])
            delta.append(row)

        # Check if this delta is consistent (same delta for same input values)
        # across all train pairs
        delta_consistent = True
        for other_pair in task.train:
            if other_pair.input.shape != pair.input.shape:
                continue
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    expected = other_pair.input.cells[r][c] + delta[r][c]
                    if expected != other_pair.output.cells[r][c]:
                        delta_consistent = False
                        break
                if not delta_consistent:
                    break
            if not delta_consistent:
                break

        if delta_consistent:
            # Only apply if test has same dimensions
            if test.height == pair.input.height and test.width == pair.input.width:
                cells = []
                for r in range(test.height):
                    row = []
                    for c in range(test.width):
                        val = test.cells[r][c] + delta[r][c]
                        row.append(max(0, min(9, val)))  # Clamp to valid palette
                    cells.append(row)
                cands.append((f"geodesic_delta{i}", Grid(cells)))

    return cands


# ─── Style: Compression (Reduce) ────────────────────────────────────────────

def _compression_candidates(task, test, interp):
    """Reduce dimensionality — crop, extract, downsample."""
    cands = []
    # Not implemented in first shot — needs object extraction
    return cands


# ─── Style: Recursive (Multi-step) ──────────────────────────────────────────

def _recursive_candidates(task, test, interp):
    """Multi-step transformations."""
    cands = []
    # Not implemented in first shot — needs composition search
    return cands


# ─── Style: Toolkit (Learned Solvers) ───────────────────────────────────────

def _cross_shift(grid: Grid) -> Optional[Grid]:
    """Cross shift by markers (from v064)."""
    colours = [v for row in grid.cells for v in row if v not in (0, 5)]
    if not colours:
        return None
    main = Counter(colours).most_common(1)[0][0]
    marker_count = sum(1 for row in grid.cells for v in row if v == 5)
    if marker_count <= 0:
        return None
    h, w = grid.height, grid.width
    row_counts = defaultdict(int)
    col_counts = defaultdict(int)
    for r, row in enumerate(grid.cells):
        for c, v in enumerate(row):
            if v == main:
                row_counts[r] += 1
                col_counts[c] += 1
    if not row_counts or not col_counts:
        return None
    horizontal_row = max(row_counts.items(), key=lambda kv: (kv[1], -kv[0]))[0]
    vertical_col = max(col_counts.items(), key=lambda kv: (kv[1], -kv[0]))[0]
    new_row = horizontal_row + marker_count
    new_col = vertical_col - marker_count
    if not (0 <= new_row < h and 0 <= new_col < w):
        return None
    cells = [[0] * w for _ in range(h)]
    for c in range(w):
        cells[new_row][c] = main
    for r in range(h):
        cells[r][new_col] = main
    return Grid(cells)

def _toolkit_candidates(task, test, interp):
    """Use learned solver tools — the mind's existing toolkit."""
    cands = []

    # Gravity down
    result = gravity_down(test)
    if result is not None:
        cands.append(("toolkit_gravity", result))

    # Local swap
    result = local_swap(test)
    if result is not None:
        cands.append(("toolkit_local_swap", result))

    # Colour center fill
    result = colour_center_fill(test)
    if result is not None:
        cands.append(("toolkit_colour_center", result))

    # Column rank fill
    result = column_rank_fill(test)
    if result is not None:
        cands.append(("toolkit_column_rank", result))

    # Marker fill
    result = marker_fill_85(test)
    if result is not None:
        cands.append(("toolkit_marker_fill", result))

    # Interior fill
    fn = learn_multi_interior_fill(task)
    if fn:
        result = fn(test)
        if result is not None:
            cands.append(("toolkit_interior_fill", result))

    # Distance rule
    dist = try_distance_diagonal_rule(task)
    if dist:
        pred, _ = dist
        cands.append(("toolkit_distance", pred))

    # Conditional recolour (sweep)
    objs = extract_objects(test)
    max_size = max((o["size"] for o in objs), default=0)
    for threshold in range(2, max(max_size + 1, 10)):
        for outcome in range(1, 10):
            result = cond_recolour(test, threshold, outcome)
            if result is not None:
                cands.append((f"toolkit_cond_{threshold}_{outcome}", result))

    # Cross shift by markers (inline)
    cross = _cross_shift(test)
    if cross:
        cands.append(("toolkit_cross_shift", cross))

    return cands


# ═══════════════════════════════════════════════════════════════════════════════
# VERIFICATION — Hard Gate
# ═══════════════════════════════════════════════════════════════════════════════

def apply_candidate_to_grid(task: ARCTask, style: str, candidate_name: str,
                              grid: Grid) -> Optional[Grid]:
    """Apply a candidate strategy to any grid (for train verification)."""
    h, w = grid.height, grid.width

    # Get interpretation for this task
    interp = interpret(task)

    # Regenerate candidates for this specific grid
    # We need to re-apply the same strategy
    if candidate_name == "identity":
        return Grid([row[:] for row in grid.cells])

    if candidate_name.startswith("resonant_recolour"):
        if interp.colour_map:
            cm = interp.colour_map
            cells = [[cm.get(grid.cells[r][c], grid.cells[r][c])
                       for c in range(w)] for r in range(h)]
            return Grid(cells)
        return None

    if candidate_name.startswith("resonant_pair"):
        idx = int(candidate_name.replace("resonant_pair", ""))
        pair = task.train[idx]
        if pair.input.shape != pair.output.shape:
            return None
        cm = {}
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                s, d = pair.input.cells[r][c], pair.output.cells[r][c]
                if s != d:
                    cm[s] = d
        cells = [[cm.get(grid.cells[r][c], grid.cells[r][c])
                   for c in range(w)] for r in range(h)]
        return Grid(cells)

    if candidate_name == "machining_gravity":
        cells = [[0]*w for _ in range(h)]
        for c in range(w):
            col = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
            for i, v in enumerate(col):
                cells[h - len(col) + i][c] = v
        return Grid(cells)

    if candidate_name == "machining_fill":
        non_zero = [v for row in grid.cells for v in row if v != 0]
        if non_zero:
            fill = Counter(non_zero).most_common(1)[0][0]
            cells = [[fill if grid.cells[r][c] == 0 else grid.cells[r][c]
                       for c in range(w)] for r in range(h)]
            return Grid(cells)
        return None

    if candidate_name == "flow_uniform":
        for pair in task.train:
            if pair.input.shape != pair.output.shape:
                continue
            fills = set()
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                        fills.add(pair.output.cells[r][c])
            if len(fills) == 1:
                fill = next(iter(fills))
                cells = [[fill if grid.cells[r][c] == 0 else grid.cells[r][c]
                           for c in range(w)] for r in range(h)]
                return Grid(cells)
        return None

    if candidate_name == "flow_dilate":
        # Re-learn marker map from train pairs
        marker_map = {}
        for pair in task.train:
            if pair.input.shape != pair.output.shape:
                continue
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                        fill = pair.output.cells[r][c]
                        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                            nr, nc = r+dr, c+dc
                            if 0 <= nr < pair.input.height and 0 <= nc < pair.input.width:
                                mc = pair.input.cells[nr][nc]
                                if mc != 0:
                                    marker_map[mc] = fill
        if marker_map:
            cells = [row[:] for row in grid.cells]
            changed = False
            for r in range(h):
                for c in range(w):
                    if cells[r][c] != 0:
                        continue
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w:
                            mc = cells[nr][nc]
                            if mc in marker_map:
                                cells[r][c] = marker_map[mc]
                                changed = True
                                break
            return Grid(cells) if changed else None
        return None

    if candidate_name == "differential_neighbour":
        rules = {}
        for pair in task.train:
            if pair.input.shape != pair.output.shape:
                continue
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    iv = pair.input.cells[r][c]
                    ov = pair.output.cells[r][c]
                    if iv == ov:
                        continue
                    n_cols = []
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < pair.input.height and 0 <= nc < pair.input.width:
                            n_cols.append(pair.input.cells[nr][nc])
                    key = (iv, tuple(sorted(n_cols)))
                    if key in rules and rules[key] != ov:
                        return None
                    rules[key] = ov
        if rules:
            cells = [row[:] for row in grid.cells]
            changed = False
            for r in range(h):
                for c in range(w):
                    n_cols = []
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w:
                            n_cols.append(grid.cells[nr][nc])
                    key = (grid.cells[r][c], tuple(sorted(n_cols)))
                    if key in rules:
                        cells[r][c] = rules[key]
                        changed = True
            return Grid(cells) if changed else None
        return None

    if candidate_name == "entropic_interior":
        regions = _enclosed_zero_regions(grid)
        size_to_fill = {}
        for pair in task.train:
            if pair.input.shape != pair.output.shape:
                continue
            train_regions = _enclosed_zero_regions(pair.input)
            for region in train_regions:
                fills = {pair.output.cells[r][c] for r, c in region}
                if len(fills) == 1:
                    size_to_fill[len(region)] = next(iter(fills))
        if size_to_fill and regions:
            cells = [row[:] for row in grid.cells]
            changed = False
            for region in regions:
                fill = size_to_fill.get(len(region))
                if fill is not None:
                    for r, c in region:
                        cells[r][c] = fill
                        changed = True
            return Grid(cells) if changed else None
        return None

    if candidate_name.startswith("geodesic_delta"):
        idx = int(candidate_name.replace("geodesic_delta", ""))
        pair = task.train[idx]
        if pair.input.shape != pair.output.shape or pair.input.shape != grid.shape:
            return None
        delta = [[pair.output.cells[r][c] - pair.input.cells[r][c]
                   for c in range(pair.input.width)] for r in range(pair.input.height)]
        cells = [[max(0, min(9, grid.cells[r][c] + delta[r][c]))
                   for c in range(grid.width)] for r in range(grid.height)]
        return Grid(cells)

    # Toolkit strategies
    if candidate_name == "toolkit_gravity":
        return gravity_down(grid)
    if candidate_name == "toolkit_local_swap":
        return local_swap(grid)
    if candidate_name == "toolkit_colour_center":
        return colour_center_fill(grid)
    if candidate_name == "toolkit_column_rank":
        return column_rank_fill(grid)
    if candidate_name == "toolkit_marker_fill":
        return marker_fill_85(grid)
    if candidate_name == "toolkit_interior_fill":
        fn = learn_multi_interior_fill(task)
        return fn(grid) if fn else None
    if candidate_name == "toolkit_distance":
        # Use v032's own verification
        result = try_distance_diagonal_rule(task)
        if result:
            pred, _ = result
            # Check if this prediction matches the grid we're verifying
            if pred.cells == grid.cells:
                return pred
            # Try applying to this specific grid
            # v032 works on the full task, not individual grids
            # So we can't easily re-apply it
        return None
    if candidate_name.startswith("toolkit_cond_"):
        parts = candidate_name.split("_")
        threshold = int(parts[2])
        outcome = int(parts[3])
        return cond_recolour(grid, threshold, outcome)
    if candidate_name == "toolkit_cross_shift":
        return _cross_shift(grid)

    # Geometric strategies
    if candidate_name == "geo_identity":
        return Grid([row[:] for row in grid.cells])
    if candidate_name.startswith("geo_colour"):
        return _apply_geometric_to_grid(task, candidate_name, grid)
    if candidate_name.startswith("geo_resize_"):
        return _apply_geometric_to_grid(task, candidate_name, grid)

    return None


def _apply_geometric_to_grid(task, candidate_name: str, grid: Grid) -> Optional[Grid]:
    """Apply a geometric strategy to any grid."""
    from geometric_perception import _apply_geometric_to_grid as _apply_geo
    return _apply_geo(task, candidate_name, grid)


def verify_and_rank(task: ARCTask, candidates: List[Tuple[str, Grid]]) -> List[Tuple[str, Grid, float]]:
    """Verify candidates on train pairs, then rank by attention score."""
    verified = []

    for name, test_pred in candidates:
        # Special case: distance_rule uses v032's own verification
        if name == "toolkit_distance":
            result = try_distance_diagonal_rule(task)
            if result:
                pred, _ = result
                score = _attention_score(task.test[0].input, pred)
                verified.append((name, pred, score))
            continue

        # Hard gate: must reproduce ALL train pairs
        passes = True
        checked = 0
        for pair in task.train:
            if pair.input.shape != pair.output.shape:
                continue
            train_result = apply_candidate_to_grid(task, "none", name, pair.input)
            if train_result is None or train_result.cells != pair.output.cells:
                passes = False
                break
            checked += 1

        if not passes or checked == 0:
            continue

        # Attention score (MOG coherence)
        score = _attention_score(task.test[0].input, test_pred)
        verified.append((name, test_pred, score))

    # Rank by attention score (higher = more coherent)
    verified.sort(key=lambda x: -x[2])
    return verified


def _attention_score(inp: Grid, out: Grid) -> float:
    """MOG attention coherence score."""
    if inp.shape != out.shape:
        return 0.0
    h, w = inp.height, inp.width
    total = 0
    coherent = 0
    for r in range(h):
        for c in range(w):
            total += 1
            if inp.cells[r][c] == out.cells[r][c]:
                coherent += 1
    return coherent / total if total > 0 else 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# THE MIND — Main Loop
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MindResult:
    """What the mind decided."""
    task_id: str
    solved: bool
    style_used: str
    candidate_name: str
    interpretation: Interpretation
    perception: Perception
    n_candidates_generated: int
    n_candidates_verified: int
    attention_score: float


def mog_mind_solve(task: ARCTask, verbose: bool = False) -> Optional[MindResult]:
    """
    The MOG-mind solves a task.

    1. PERCEIVE: Look at the task through 4 channels
    2. INTERPRET: Understand what's happening
    3. SELECT STYLE: Choose a driving style
    4. GENERATE: Create candidates using that style
    5. VERIFY: Hard gate on train pairs
    6. RANK: Select best by attention coherence
    7. LEARN: Record what happened
    """
    # Step 1: Perceive
    inp_perception = perceive(task.train[0].input)

    # Step 2: Interpret
    interp = interpret(task)

    # Step 3: Select style
    style = interp.suggested_style

    # Step 4: Generate candidates
    candidates = generate_candidates_by_style(task, style, interp)

    # Also try other styles if primary doesn't work
    all_styles = ["machining", "resonant", "differential", "flow",
                  "entropic", "geodesic", "toolkit", "geometric"]
    for alt_style in all_styles:
        if alt_style != style:
            try:
                alt_candidates = generate_candidates_by_style(task, alt_style, interp)
                candidates.extend(alt_candidates)
            except Exception:
                pass  # Skip broken styles

    # Step 5 & 6: Verify and rank
    verified = verify_and_rank(task, candidates)

    if verbose:
        print(f"  Perception: palette={inp_perception.palette}, density={inp_perception.density:.2f}")
        print(f"  Interpretation: type={interp.transformation_type}, complexity={interp.complexity}")
        print(f"  Style: {style} (confidence={interp.style_confidence:.2f})")
        print(f"  Candidates: {len(candidates)} generated, {len(verified)} verified")
        if verified:
            print(f"  Best: {verified[0][0]} (score={verified[0][2]:.3f})")

    if not verified:
        return MindResult(
            task_id=task.name,
            solved=False,
            style_used=style,
            candidate_name="none",
            interpretation=interp,
            perception=inp_perception,
            n_candidates_generated=len(candidates),
            n_candidates_verified=0,
            attention_score=0.0,
        )

    best_name, best_grid, best_score = verified[0]
    return MindResult(
        task_id=task.name,
        solved=True,
        style_used=style,
        candidate_name=best_name,
        interpretation=interp,
        perception=inp_perception,
        n_candidates_generated=len(candidates),
        n_candidates_verified=len(verified),
        attention_score=best_score,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK — Run the mind on all tasks
# ═══════════════════════════════════════════════════════════════════════════════

def benchmark(batch_dir: str, verbose: bool = False) -> Dict[str, Any]:
    files = sorted(f for f in os.listdir(batch_dir) if f.endswith(".json"))
    results = []
    style_counts = Counter()
    candidate_counts = Counter()

    t0 = time.time()
    for fname in files:
        task = load_task(os.path.join(batch_dir, fname), name=os.path.splitext(fname)[0])
        try:
            result = mog_mind_solve(task, verbose=verbose)
        except Exception as e:
            result = MindResult(
                task_id=task.name, solved=False, style_used="error",
                candidate_name="error", interpretation=Interpretation(),
                perception=Perception(), n_candidates_generated=0,
                n_candidates_verified=0, attention_score=0.0,
            )

        results.append(result)
        if result.solved:
            style_counts[result.style_used] += 1
            candidate_counts[result.candidate_name] += 1

    elapsed = time.time() - t0
    solved = sum(1 for r in results if r.solved)

    return {
        "solved": solved,
        "total": len(results),
        "pct": round(100.0 * solved / max(1, len(results)), 1),
        "elapsed": round(elapsed, 1),
        "style_counts": dict(style_counts),
        "candidate_counts": dict(candidate_counts),
        "results": results,
    }


def main():
    batch = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "training")

    print("=" * 72)
    print(" MOG-MIND — Substrate-Native Cognitive Architecture")
    print("=" * 72)
    print()

    summary = benchmark(batch, verbose=True)

    print()
    print("=" * 72)
    print(f" RESULT: {summary['solved']}/{summary['total']} ({summary['pct']}%)")
    print(f" Time: {summary['elapsed']}s")
    print("=" * 72)

    for r in summary["results"]:
        if r.solved:
            print(f"  ✓ {r.task_id}: {r.candidate_name} (style={r.style_used}, score={r.attention_score:.3f})")

    print(f"\n  Style distribution:")
    for style, count in sorted(summary["style_counts"].items(), key=lambda kv: -kv[1]):
        print(f"    {style}: {count}")

    print(f"\n  Candidate distribution:")
    for cand, count in sorted(summary["candidate_counts"].items(), key=lambda kv: -kv[1]):
        print(f"    {cand}: {count}")

    # Show what the mind "saw" for unsolved tasks
    print(f"\n  Unsolved task interpretations:")
    for r in summary["results"]:
        if not r.solved:
            interp = r.interpretation
            print(f"    {r.task_id}: type={interp.transformation_type}, "
                  f"complexity={interp.complexity}, style={r.style_used}, "
                  f"candidates={r.n_candidates_generated}, verified={r.n_candidates_verified}")

    # Save
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "REPORTS", "mog_mind_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    report = {
        "solved": summary["solved"],
        "total": summary["total"],
        "pct": summary["pct"],
        "elapsed": summary["elapsed"],
        "style_counts": summary["style_counts"],
        "candidate_counts": summary["candidate_counts"],
        "results": [{
            "task_id": r.task_id,
            "solved": r.solved,
            "style": r.style_used,
            "candidate": r.candidate_name,
            "type": r.interpretation.transformation_type,
            "complexity": r.interpretation.complexity,
            "n_candidates": r.n_candidates_generated,
            "n_verified": r.n_candidates_verified,
            "score": r.attention_score,
        } for r in summary["results"]],
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report: {report_path}")


if __name__ == "__main__":
    main()
