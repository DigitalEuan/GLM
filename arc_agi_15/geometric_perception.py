"""
geometric_perception.py — Geometric Understanding for the MOG-Mind
===================================================================

Uses spatial_arithmetic.py to give the mind geometric understanding.

The key insight: ARC objects have geometric meaning.
- An object's SIZE maps to a spatial arithmetic polygon (node_count = 2|N| + 4)
- An object's SHAPE maps to its circumradius (how "spread" it is)
- An object's POSITION maps to its centroid (where it "lives")
- An object's COLOUR maps to its semantic role (what it "means")

The UBP calibrated scale grounds this understanding:
- Charge: vertex step = e/12 (from lightspeed study Phase 19A)
- Velocity: v/c = 0.339 (from MONAD/13 decomposition)
- Mass ratio: m_μ/m_e = 169/WOBBLE (from Phase 10B)

These aren't just physics constants — they're the SUBSTRATE'S understanding
of what "size", "speed", and "mass" mean in the 24D manifold.

For ARC, this translates to:
- Object size → node_count → polygon complexity
- Object motion → centroid shift → velocity in the manifold
- Object interaction → pairwise distance → force/tension
- Object colour → semantic mass → how "heavy" the transformation is
"""

from __future__ import annotations
import os, sys, math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arc_loader import Grid

# Import spatial arithmetic
try:
    from spatial_arithmetic import (
        node_count, decode_node_count, circumradius,
        encode, decode, centroid, radius_of,
        pairwise_centroid_distance, calibrate_edge_length,
        cluster_detect, make_unit_cycle,
        eml, UNIT, BASE_NODES, OPERATOR_CODES,
    )
    HAS_SPATIAL = True
except ImportError:
    HAS_SPATIAL = False


# ═══════════════════════════════════════════════════════════════════════════════
# UBP Calibrated Scale (from lightspeed study)
# ═══════════════════════════════════════════════════════════════════════════════

# Substrate constants
_PI = 3.141592653589793
_PHI = 1.618033988749895
_E = 2.718281828459045
_MONAD = _PI * _PHI * _E  # ≈ 13.818
_WOBBLE = _MONAD - 13     # ≈ 0.818
_Y = 1.0 / (_PI + 2.0/_PI)  # ≈ 0.265

# Calibrated scales (from Phase 20)
CHARGE_PER_VERTEX = 1.602176634e-19 / 12  # e/12 per vertex step
VELOCITY_RATIO = math.sqrt(1 - 13**2 / _MONAD**2)  # v/c ≈ 0.339
MASS_RATIO_WOBBLE = 169 / _WOBBLE  # m_μ/m_e ≈ 206.7


# ═══════════════════════════════════════════════════════════════════════════════
# Geometric Object — what the mind "sees" when it looks at a connected component
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GeometricObject:
    """A connected component understood geometrically."""
    # Identity
    colour: int
    size: int  # number of cells
    cells: List[Tuple[int, int]]  # (row, col) positions

    # Geometric properties (from spatial_arithmetic)
    node_count: int = 0        # polygon vertex count (2*size + 4)
    circumradius: float = 0.0  # polygon radius (how "spread")
    centroid: Tuple[float, float] = (0.0, 0.0)  # geometric centre
    bounding_box: Tuple[int, int, int, int] = (0, 0, 0, 0)  # (r_min, c_min, r_max, c_max)

    # UBP properties
    charge: float = 0.0      # vertex count × CHARGE_PER_VERTEX
    mass_proxy: float = 0.0   # size × Y (topological cost)
    nrci: float = 0.0         # coherence index

    # Shape properties
    aspect_ratio: float = 1.0  # width/height of bounding box
    compactness: float = 0.0   # size / bounding_box_area
    is_linear: bool = False    # all cells in one row or column
    is_rectangular: bool = False  # fills its bounding box


def extract_geometric_objects(grid: Grid) -> List[GeometricObject]:
    """Extract connected components and compute their geometric properties."""
    h, w = grid.height, grid.width
    cells = grid.cells
    visited = set()
    objects = []

    for r in range(h):
        for c in range(w):
            if (r, c) in visited or cells[r][c] == 0:
                continue
            colour = cells[r][c]

            # BFS to find connected component
            component = []
            queue = [(r, c)]
            while queue:
                cr, cc = queue.pop()
                if (cr, cc) in visited:
                    continue
                if cells[cr][cc] != colour:
                    continue
                visited.add((cr, cc))
                component.append((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in visited:
                        queue.append((nr, nc))

            obj = _compute_geometry(component, colour)
            objects.append(obj)

    return objects


def _compute_geometry(component: List[Tuple[int, int]], colour: int) -> GeometricObject:
    """Compute geometric properties for a connected component."""
    obj = GeometricObject(colour=colour, size=len(component), cells=component)

    if not component:
        return obj

    # Bounding box
    rows = [r for r, c in component]
    cols = [c for r, c in component]
    obj.bounding_box = (min(rows), min(cols), max(rows), max(cols))

    # Centroid
    obj.centroid = (
        sum(rows) / len(component),
        sum(cols) / len(component),
    )

    # Spatial arithmetic properties
    obj.node_count = node_count(len(component)) if HAS_SPATIAL else 2 * len(component) + 4
    obj.circumradius = circumradius(obj.node_count) if HAS_SPATIAL else len(component)

    # UBP properties
    obj.charge = obj.node_count * CHARGE_PER_VERTEX
    obj.mass_proxy = len(component) * _Y  # Topological cost = size × Y

    # NRCI = 10/(10 + TAX) where TAX = HW×Y + norm²/8
    # For a grid object: HW = size, norm² ≈ size (simplified)
    tax = len(component) * _Y + len(component) / 8.0
    obj.nrci = 10.0 / (10.0 + tax)

    # Shape properties
    r_min, c_min, r_max, c_max = obj.bounding_box
    height = r_max - r_min + 1
    width = c_max - c_min + 1
    obj.aspect_ratio = width / max(height, 1)
    obj.compactness = len(component) / max(height * width, 1)
    obj.is_linear = (height == 1 or width == 1)
    obj.is_rectangular = (len(component) == height * width)

    return obj


# ═══════════════════════════════════════════════════════════════════════════════
# Geometric Transformation — understanding what changed
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GeometricTransformation:
    """Understanding of how objects transform between input and output."""
    # Object-level changes
    objects_preserved: List[Tuple[GeometricObject, GeometricObject]] = field(default_factory=list)
    objects_created: List[GeometricObject] = field(default_factory=list)
    objects_destroyed: List[GeometricObject] = field(default_factory=list)
    objects_moved: List[Tuple[GeometricObject, GeometricObject, Tuple[float, float]]] = field(default_factory=list)
    objects_recoloured: List[Tuple[GeometricObject, GeometricObject]] = field(default_factory=list)
    objects_resized: List[Tuple[GeometricObject, GeometricObject]] = field(default_factory=list)

    # Global properties
    n_objects_in: int = 0
    n_objects_out: int = 0
    total_cells_in: int = 0
    total_cells_out: int = 0
    centroid_shift: Tuple[float, float] = (0.0, 0.0)

    # Geometric meaning
    transformation_type: str = "unknown"
    geometric_insight: str = ""


def analyse_transformation(input_grid: Grid, output_grid: Grid) -> GeometricTransformation:
    """Analyse the geometric transformation between input and output."""
    inp_objects = extract_geometric_objects(input_grid)
    out_objects = extract_geometric_objects(output_grid)

    gt = GeometricTransformation()
    gt.n_objects_in = len(inp_objects)
    gt.n_objects_out = len(out_objects)
    gt.total_cells_in = sum(o.size for o in inp_objects)
    gt.total_cells_out = sum(o.size for o in out_objects)

    # Match objects by colour and overlap
    inp_used = set()
    out_used = set()

    for i, inp_obj in enumerate(inp_objects):
        best_j = -1
        best_overlap = 0
        for j, out_obj in enumerate(out_objects):
            if j in out_used:
                continue
            if inp_obj.colour != out_obj.colour:
                continue
            overlap = len(set(inp_obj.cells) & set(out_obj.cells))
            if overlap > best_overlap:
                best_overlap = overlap
                best_j = j

        if best_j >= 0 and best_overlap > 0:
            out_obj = out_objects[best_j]
            inp_used.add(i)
            out_used.add(best_j)

            # Check what changed
            if set(inp_obj.cells) == set(out_obj.cells):
                gt.objects_preserved.append((inp_obj, out_obj))
            else:
                shift = (
                    out_obj.centroid[0] - inp_obj.centroid[0],
                    out_obj.centroid[1] - inp_obj.centroid[1],
                )
                if abs(shift[0]) > 0.5 or abs(shift[1]) > 0.5:
                    gt.objects_moved.append((inp_obj, out_obj, shift))
                elif inp_obj.size != out_obj.size:
                    gt.objects_resized.append((inp_obj, out_obj))
                else:
                    gt.objects_recoloured.append((inp_obj, out_obj))

    # Unmatched objects
    for i, inp_obj in enumerate(inp_objects):
        if i not in inp_used:
            gt.objects_destroyed.append(inp_obj)
    for j, out_obj in enumerate(out_objects):
        if j not in out_used:
            gt.objects_created.append(out_obj)

    # Classify transformation
    gt.transformation_type, gt.geometric_insight = _classify_geometric(gt)

    return gt


def _classify_geometric(gt: GeometricTransformation) -> Tuple[str, str]:
    """Classify the transformation based on geometric analysis."""
    n_moved = len(gt.objects_moved)
    n_recoloured = len(gt.objects_recoloured)
    n_resized = len(gt.objects_resized)
    n_created = len(gt.objects_created)
    n_destroyed = len(gt.objects_destroyed)
    n_preserved = len(gt.objects_preserved)

    if n_moved > 0 and n_recoloured == 0 and n_created == 0 and n_destroyed == 0:
        # Objects moved but didn't change colour
        shifts = [s for _, _, s in gt.objects_moved]
        if all(abs(s[0]) < 0.1 for s in shifts):
            return "horizontal_shift", f"{n_moved} objects shifted horizontally"
        if all(abs(s[1]) < 0.1 for s in shifts):
            return "vertical_shift", f"{n_moved} objects shifted vertically"
        return "motion", f"{n_moved} objects moved"

    if n_recoloured > 0 and n_moved == 0 and n_created == 0 and n_destroyed == 0:
        return "recolour", f"{n_recoloured} objects recoloured"

    if n_resized > 0 and n_created == 0 and n_destroyed == 0:
        return "resize", f"{n_resized} objects resized"

    if n_created > 0 and n_destroyed == 0:
        return "expand", f"{n_created} objects created"

    if n_destroyed > 0 and n_created == 0:
        return "compress", f"{n_destroyed} objects destroyed"

    if n_created > 0 and n_destroyed > 0:
        return "compose", f"{n_created} created, {n_destroyed} destroyed"

    if n_preserved == len(gt.objects_preserved) and gt.n_objects_in == gt.n_objects_out:
        return "identity", "all objects preserved"

    return "mixed", "multiple changes"


# ═══════════════════════════════════════════════════════════════════════════════
# Geometric Pattern Learning — what the mind learns from train pairs
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GeometricPattern:
    """A learned geometric pattern from train pairs."""
    # Object-level patterns
    size_changes: Dict[int, int] = field(default_factory=dict)  # in_size → out_size
    colour_changes: Dict[int, int] = field(default_factory=dict)  # in_colour → out_colour
    shape_preserved: bool = True  # do objects keep their shape?
    position_rule: str = ""  # how do objects move?

    # Global patterns
    n_objects_stable: bool = True  # same number of objects in/out?
    total_cells_stable: bool = True  # same total cells?
    centroid_rule: str = ""  # how does the centroid shift?

    # Geometric insight
    insight: str = ""


def learn_geometric_pattern(task) -> GeometricPattern:
    """Learn a geometric pattern from all train pairs."""
    pattern = GeometricPattern()

    size_changes = Counter()
    colour_changes = Counter()
    shapes_preserved = 0
    total_pairs = 0
    n_objects_stable_count = 0
    total_cells_stable_count = 0

    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue

        gt = analyse_transformation(pair.input, pair.output)
        total_pairs += 1

        # Object-level patterns
        for inp_obj, out_obj in gt.objects_preserved + gt.objects_recoloured + gt.objects_resized:
            if inp_obj.size != out_obj.size:
                size_changes[(inp_obj.size, out_obj.size)] += 1
            if inp_obj.colour != out_obj.colour:
                colour_changes[(inp_obj.colour, out_obj.colour)] += 1
            if inp_obj.is_rectangular == out_obj.is_rectangular:
                shapes_preserved += 1
        for inp_obj, out_obj, shift in gt.objects_moved:
            if inp_obj.size != out_obj.size:
                size_changes[(inp_obj.size, out_obj.size)] += 1
            if inp_obj.colour != out_obj.colour:
                colour_changes[(inp_obj.colour, out_obj.colour)] += 1

        if gt.n_objects_in == gt.n_objects_out:
            n_objects_stable_count += 1
        if gt.total_cells_in == gt.total_cells_out:
            total_cells_stable_count += 1

    if total_pairs == 0:
        return pattern

    # Synthesize patterns
    if colour_changes:
        most_common = colour_changes.most_common(1)[0]
        pattern.colour_changes = {k: v for k, v in colour_changes.items()}

    if size_changes:
        pattern.size_changes = {k: v for k, v in size_changes.items()}

    pattern.shape_preserved = (shapes_preserved > total_pairs * 0.5)
    pattern.n_objects_stable = (n_objects_stable_count == total_pairs)
    pattern.total_cells_stable = (total_cells_stable_count == total_pairs)

    # Generate insight
    if pattern.colour_changes and not pattern.size_changes:
        pattern.insight = "Objects change colour but preserve shape and size"
    elif pattern.size_changes and not pattern.colour_changes:
        pattern.insight = "Objects change size but preserve colour"
    elif pattern.n_objects_stable and pattern.total_cells_stable:
        pattern.insight = "Stable transformation — same objects, same total cells"
    else:
        pattern.insight = f"Complex transformation — {gt.transformation_type}"

    return pattern


# ═══════════════════════════════════════════════════════════════════════════════
# Geometric Candidate Generation — using geometric understanding
# ═══════════════════════════════════════════════════════════════════════════════

def generate_geometric_candidates(task, pattern: GeometricPattern) -> List[Tuple[str, Grid]]:
    """Generate candidates using geometric understanding."""
    from arc_loader import ARCTask
    test = task.test[0].input
    h, w = test.height, test.width
    candidates = []

    # Strategy 1: Apply learned colour changes
    if pattern.colour_changes:
        cells = [row[:] for row in test.cells]
        changed = False
        for r in range(h):
            for c in range(w):
                v = cells[r][c]
                if v in pattern.colour_changes:
                    cells[r][c] = pattern.colour_changes[v]
                    changed = True
        if changed:
            candidates.append(("geo_colour", Grid(cells)))

    # Strategy 2: Preserve objects (identity for stable objects)
    if pattern.n_objects_stable and pattern.total_cells_stable:
        candidates.append(("geo_identity", Grid([row[:] for row in test.cells])))

    # Strategy 3: Object-level transformations
    inp_objects = extract_geometric_objects(test)
    for inp_obj in inp_objects:
        # Try resizing each object
        if pattern.size_changes:
            for (in_size, out_size), count in pattern.size_changes.items():
                if inp_obj.size == in_size:
                    # Try to resize the object
                    resized = _resize_object(test, inp_obj, out_size)
                    if resized:
                        candidates.append((f"geo_resize_{inp_obj.colour}_{out_size}", resized))

    return candidates


def _resize_object(grid: Grid, obj: GeometricObject, target_size: int) -> Optional[Grid]:
    """Attempt to resize an object to target_size."""
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]

    if target_size > obj.size:
        # Expand: add cells adjacent to the object
        frontier = set()
        for r, c in obj.cells:
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] == 0:
                    frontier.add((nr, nc))

        added = 0
        for r, c in sorted(frontier):
            if added >= target_size - obj.size:
                break
            cells[r][c] = obj.colour
            added += 1

    elif target_size < obj.size:
        # Shrink: remove cells from the boundary
        # Find boundary cells (cells with fewer same-colour neighbours)
        boundary = []
        for r, c in obj.cells:
            same_neigh = sum(1 for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                           if 0<=r+dr<h and 0<=c+dc<w and cells[r+dr][c+dc]==obj.colour)
            if same_neigh < 4:
                boundary.append((r, c, same_neigh))

        boundary.sort(key=lambda x: x[2])  # Remove least-connected first
        removed = 0
        for r, c, _ in boundary:
            if removed >= obj.size - target_size:
                break
            cells[r][c] = 0
            removed += 1

    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════════════════
# Geometric Verification
# ═══════════════════════════════════════════════════════════════════════════════

def verify_geometric_candidate(task, candidate_name: str, 
                                 test_candidate: Grid) -> bool:
    """Verify a geometric candidate on train pairs."""
    checked = 0
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue

        # Apply the same strategy to this train input
        train_result = _apply_geometric_to_grid(task, candidate_name, pair.input)
        if train_result is None:
            return False
        if train_result.cells != pair.output.cells:
            return False
        checked += 1

    return checked > 0


def _apply_geometric_to_grid(task, candidate_name: str, grid: Grid) -> Optional[Grid]:
    """Apply a geometric strategy to any grid."""
    h, w = grid.height, grid.width

    if candidate_name == "geo_identity":
        return Grid([row[:] for row in grid.cells])

    if candidate_name.startswith("geo_colour"):
        # Re-learn colour mapping from train pairs
        colour_map = {}
        for pair in task.train:
            if pair.input.shape != pair.output.shape:
                continue
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    s, d = pair.input.cells[r][c], pair.output.cells[r][c]
                    if s != d:
                        if s in colour_map and colour_map[s] != d:
                            return None
                        colour_map[s] = d
        if colour_map:
            cells = [[colour_map.get(grid.cells[r][c], grid.cells[r][c])
                       for c in range(w)] for r in range(h)]
            return Grid(cells)
        return None

    if candidate_name.startswith("geo_resize_"):
        # Parse: geo_resize_{colour}_{target_size}
        parts = candidate_name.split("_")
        target_colour = int(parts[2])
        target_size = int(parts[3])
        # Find the object of this colour
        objects = extract_geometric_objects(grid)
        for obj in objects:
            if obj.colour == target_colour:
                return _resize_object(grid, obj, target_size)
        return None

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Geometric Perception Report — what the mind "sees"
# ═══════════════════════════════════════════════════════════════════════════════

def geometric_report(grid: Grid) -> str:
    """Generate a human-readable geometric perception report."""
    objects = extract_geometric_objects(grid)

    lines = [f"Grid: {grid.height}×{grid.width}, {len(objects)} objects"]
    for i, obj in enumerate(objects):
        lines.append(
            f"  Object {i}: colour={obj.colour}, size={obj.size}, "
            f"nodes={obj.node_count}, R={obj.circumradius:.2f}, "
            f"centroid=({obj.centroid[0]:.1f},{obj.centroid[1]:.1f}), "
            f"NRCI={obj.nrci:.3f}, "
            f"shape={'linear' if obj.is_linear else 'rect' if obj.is_rectangular else 'complex'}"
        )

    return "\n".join(lines)
