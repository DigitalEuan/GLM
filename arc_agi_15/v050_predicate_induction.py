"""
v050_predicate_induction.py — Automated Predicate Induction for ARC-AGI
========================================================================

Addresses the three disconnections identified in ARC_AGI_Rewiring_Brief.md:

1. Candidate generation now conditions on OBJECTS (not flat grids)
2. The object/relation vocabulary now INDUCES rules (not just matches)
3. Surviving predicates persist as TEMPLATES (not literal instances)

Algorithm:
  1. Decompose train input/output grids into objects (GridObject)
  2. Align input objects to output objects (centroid matching)
  3. Compute property vectors per object (size, colour, position, rank, etc.)
  4. Generate candidate predicates per property (==, >=, <=, rank, etc.)
  5. Keep predicates whose truth value maps to the SAME outcome across ALL train pairs
  6. Hard-gate the reconstructed grid against every train pair
  7. Tiebreak survivors with MDL/Occam priority

Full transparency: every result is reported honestly.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set, Callable
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import sys, os, json, signal

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task


# ══════════════════════════════════════════════════════════════════════════════
# OBJECT EXTRACTION (self-contained, no external deps)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Obj:
    """Lightweight object representation."""
    cells: List[Tuple[int, int]]
    colour: int
    bbox: Tuple[int, int, int, int]  # rmin, rmax, cmin, cmax
    centroid: Tuple[float, float]
    grid_shape: Tuple[int, int]

    @property
    def cell_count(self) -> int:
        return len(self.cells)

    @property
    def width(self) -> int:
        return self.bbox[3] - self.bbox[2] + 1

    @property
    def height(self) -> int:
        return self.bbox[1] - self.bbox[0] + 1

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def fill_ratio(self) -> float:
        return self.cell_count / max(self.area, 1)

    @property
    def touches_top(self) -> bool:
        return self.bbox[0] == 0

    @property
    def touches_bottom(self) -> bool:
        return self.bbox[1] == self.grid_shape[0] - 1

    @property
    def touches_left(self) -> bool:
        return self.bbox[2] == 0

    @property
    def touches_right(self) -> bool:
        return self.bbox[3] == self.grid_shape[1] - 1

    @property
    def touches_border(self) -> bool:
        return self.touches_top or self.touches_bottom or self.touches_left or self.touches_right


def extract_objects(grid: Grid) -> List[Obj]:
    """Extract connected components (4-neighbour) as objects."""
    h, w = grid.height, grid.width
    visited = set()
    objects = []

    for r in range(h):
        for c in range(w):
            if (r, c) in visited or grid.cells[r][c] == 0:
                continue
            colour = grid.cells[r][c]
            cells = []
            queue = [(r, c)]
            while queue:
                cr, cc = queue.pop()
                if (cr, cc) in visited:
                    continue
                visited.add((cr, cc))
                cells.append((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in visited:
                        if grid.cells[nr][nc] == colour:
                            queue.append((nr, nc))

            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            bbox = (min(rs), max(rs), min(cs), max(cs))
            centroid = (sum(rs) / len(cells), sum(cs) / len(cells))

            objects.append(Obj(
                cells=cells, colour=colour, bbox=bbox,
                centroid=centroid, grid_shape=(h, w),
            ))

    # Sort by (colour, size descending)
    objects.sort(key=lambda o: (o.colour, -o.cell_count))
    return objects


# ══════════════════════════════════════════════════════════════════════════════
# OBJECT PAIRING
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Pair:
    """A matched input→output object pair."""
    inp: Obj
    out: Optional[Obj]  # None if disappeared
    transform: str       # "unchanged", "recolour", "move", "resize", "appear", "disappear"


def pair_objects(inp_objs: List[Obj], out_objs: List[Obj]) -> List[Pair]:
    """Match objects by nearest centroid."""
    pairs = []
    used = set()

    for in_obj in inp_objs:
        best_idx = -1
        best_dist = float('inf')
        for i, out_obj in enumerate(out_objs):
            if i in used:
                continue
            dr = in_obj.centroid[0] - out_obj.centroid[0]
            dc = in_obj.centroid[1] - out_obj.centroid[1]
            dist = (dr*dr + dc*dc) ** 0.5
            if dist < best_dist:
                best_dist = dist
                best_idx = i

        if best_idx >= 0 and best_dist < 5.0:
            out_obj = out_objs[best_idx]
            used.add(best_idx)
            colour_changed = in_obj.colour != out_obj.colour
            pos_changed = best_dist > 0.5
            size_changed = in_obj.cell_count != out_obj.cell_count

            if not colour_changed and not pos_changed and not size_changed:
                t = "unchanged"
            elif colour_changed and not pos_changed and not size_changed:
                t = "recolour"
            elif not colour_changed and pos_changed and not size_changed:
                t = "move"
            elif not colour_changed and not pos_changed and size_changed:
                t = "resize"
            else:
                t = "composite"

            pairs.append(Pair(inp=in_obj, out=out_obj, transform=t))
        else:
            pairs.append(Pair(inp=in_obj, out=None, transform="disappear"))

    for i, out_obj in enumerate(out_objs):
        if i not in used:
            pairs.append(Pair(
                inp=Obj(cells=[], colour=0, bbox=(0,0,0,0), centroid=(0,0), grid_shape=out_obj.grid_shape),
                out=out_obj, transform="appear",
            ))

    return pairs


# ══════════════════════════════════════════════════════════════════════════════
# PROPERTY EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ObjProperties:
    """All computable properties of an object."""
    obj: Obj
    # Numeric properties
    cell_count: int
    colour: int
    width: int
    height: int
    area: int
    fill_ratio: float
    centroid_r: float
    centroid_c: float
    # Rank properties (among siblings in same grid)
    size_rank: int        # 0 = largest
    colour_rank: int      # 0 = lowest colour value
    # Boolean properties
    touches_border: bool
    touches_top: bool
    touches_bottom: bool
    touches_left: bool
    touches_right: bool
    is_largest: bool
    is_smallest: bool
    # Context properties
    num_same_colour: int  # how many objects share this colour
    num_neighbours: int   # how many other objects are adjacent


def compute_properties(obj: Obj, all_objs: List[Obj]) -> ObjProperties:
    """Compute all properties of an object relative to its siblings."""
    # Ranks
    sizes = sorted(set(o.cell_count for o in all_objs), reverse=True)
    colours = sorted(set(o.colour for o in all_objs))

    size_rank = sizes.index(obj.cell_count) if obj.cell_count in sizes else -1
    colour_rank = colours.index(obj.colour) if obj.colour in colours else -1

    # Same colour count
    num_same_colour = sum(1 for o in all_objs if o.colour == obj.colour)

    # Neighbour count (objects whose bbox is within 1 cell)
    num_neighbours = 0
    for other in all_objs:
        if other is obj:
            continue
        # Check if bboxes are adjacent (within 1 cell)
        if (obj.bbox[0] <= other.bbox[1] + 1 and obj.bbox[1] >= other.bbox[0] - 1 and
            obj.bbox[2] <= other.bbox[3] + 1 and obj.bbox[3] >= other.bbox[2] - 1):
            num_neighbours += 1

    return ObjProperties(
        obj=obj,
        cell_count=obj.cell_count,
        colour=obj.colour,
        width=obj.width,
        height=obj.height,
        area=obj.area,
        fill_ratio=obj.fill_ratio,
        centroid_r=obj.centroid[0],
        centroid_c=obj.centroid[1],
        size_rank=size_rank,
        colour_rank=colour_rank,
        touches_border=obj.touches_border,
        touches_top=obj.touches_top,
        touches_bottom=obj.touches_bottom,
        touches_left=obj.touches_left,
        touches_right=obj.touches_right,
        is_largest=(size_rank == 0),
        is_smallest=(size_rank == len(sizes) - 1),
        num_same_colour=num_same_colour,
        num_neighbours=num_neighbours,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PREDICATE SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Predicate:
    """A predicate over object properties."""
    prop_name: str     # which property to test
    op: str            # "==", "!=", ">=", "<=", "rank==", "is_max", "is_min"
    value: Any         # the threshold/value

    def evaluate(self, props: ObjProperties) -> bool:
        """Evaluate this predicate against an object's properties."""
        actual = getattr(props, self.prop_name, None)
        if actual is None:
            return False

        if self.op == "==":
            return actual == self.value
        elif self.op == "!=":
            return actual != self.value
        elif self.op == ">=":
            return actual >= self.value
        elif self.op == "<=":
            return actual <= self.value
        elif self.op == "rank==":
            return props.size_rank == self.value
        elif self.op == "is_max":
            return props.is_largest
        elif self.op == "is_min":
            return props.is_smallest
        elif self.op == "touches":
            return actual == True
        elif self.op == "not_touches":
            return actual == False
        return False

    def __repr__(self):
        return f"{self.prop_name} {self.op} {self.value}"

    def complexity(self) -> int:
        """MDL complexity score (lower = simpler)."""
        base = 1
        if self.op in ("rank==", "is_max", "is_min"):
            base = 2
        return base


@dataclass
class RuleTemplate:
    """A learned rule: predicate → outcome."""
    predicate: Predicate
    outcome_prop: str    # which property of the output object to set
    outcome_value: Any   # the value to set
    success_count: int = 0
    total_seen: int = 0

    @property
    def reliability(self) -> float:
        return self.success_count / max(self.total_seen, 1)

    def complexity(self) -> int:
        return self.predicate.complexity()

    def to_dict(self) -> dict:
        return {
            "predicate": {
                "prop_name": self.predicate.prop_name,
                "op": self.predicate.op,
                "value": self.predicate.value,
            },
            "outcome_prop": self.outcome_prop,
            "outcome_value": self.outcome_value,
            "success_count": self.success_count,
            "total_seen": self.total_seen,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RuleTemplate":
        pred = Predicate(
            prop_name=d["predicate"]["prop_name"],
            op=d["predicate"]["op"],
            value=d["predicate"]["value"],
        )
        return cls(
            predicate=pred,
            outcome_prop=d["outcome_prop"],
            outcome_value=d["outcome_value"],
            success_count=d.get("success_count", 0),
            total_seen=d.get("total_seen", 0),
        )


# ══════════════════════════════════════════════════════════════════════════════
# PREDICATE INDUCTION ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def generate_candidate_predicates(props_list: List[ObjProperties]) -> List[Predicate]:
    """Generate all candidate predicates from observed properties."""
    candidates = []

    # Collect all unique values for each property
    for prop_name in ["cell_count", "colour", "width", "height", "area",
                      "size_rank", "colour_rank", "num_same_colour", "num_neighbours"]:
        values = sorted(set(getattr(p, prop_name) for p in props_list))
        for v in values:
            candidates.append(Predicate(prop_name=prop_name, op="==", value=v))
            candidates.append(Predicate(prop_name=prop_name, op="!=", value=v))
        # Add >= and <= for ALL unique values
        for v in values:
            candidates.append(Predicate(prop_name=prop_name, op=">=", value=v))
            candidates.append(Predicate(prop_name=prop_name, op="<=", value=v))
        # Add >= and <= for all integers in the range [min, max]
        if len(values) >= 2 and all(isinstance(v, (int, float)) for v in values):
            lo, hi = int(min(values)), int(max(values))
            for v in range(lo, hi + 1):
                if v not in values:
                    candidates.append(Predicate(prop_name=prop_name, op=">=", value=v))
                    candidates.append(Predicate(prop_name=prop_name, op="<=", value=v))

    # Boolean properties
    for prop_name in ["touches_border", "touches_top", "touches_bottom",
                      "touches_left", "touches_right", "is_largest", "is_smallest"]:
        candidates.append(Predicate(prop_name=prop_name, op="touches", value=True))
        candidates.append(Predicate(prop_name=prop_name, op="not_touches", value=False))

    # Rank predicates
    for k in range(5):
        candidates.append(Predicate(prop_name="size_rank", op="rank==", value=k))

    # is_max / is_min
    candidates.append(Predicate(prop_name="cell_count", op="is_max", value=True))
    candidates.append(Predicate(prop_name="cell_count", op="is_min", value=True))

    return candidates


def find_consistent_rules(task: ARCTask) -> List[Tuple[Predicate, str, Any]]:
    """Find predicates that consistently predict outcomes across ALL train pairs.

    Returns list of (predicate, outcome_property, outcome_value) tuples.
    """
    # Collect all (predicate, outcome) observations across train pairs
    observations = defaultdict(lambda: defaultdict(int))
    # Key: (predicate_repr, outcome_prop, outcome_value), Value: count of pairs where consistent

    for pair_idx, pair in enumerate(task.train):
        inp_grid = pair.input
        out_grid = pair.output

        # Skip size-changing tasks for now
        if inp_grid.height != out_grid.height or inp_grid.width != out_grid.width:
            return []

        inp_objs = extract_objects(inp_grid)
        out_objs = extract_objects(out_grid)

        if not inp_objs:
            return []

        pairs = pair_objects(inp_objs, out_objs)

        # Compute properties for input objects
        inp_props = [compute_properties(p.inp, inp_objs) for p in pairs if p.inp.cells]

        # Generate candidates
        candidates = generate_candidate_predicates(inp_props)

        # For each recolour pair, check which predicates predict the outcome
        for pair_item in pairs:
            if pair_item.transform != "recolour" or pair_item.out is None:
                continue

            inp_props_item = compute_properties(pair_item.inp, inp_objs)

            for pred in candidates:
                if pred.evaluate(inp_props_item):
                    # This predicate is TRUE for this input object
                    # The outcome is: output colour = pair_item.out.colour
                    key = (str(pred), "colour", pair_item.out.colour)
                    observations[key][pair_idx] += 1

    # Find predicates that are consistent across ALL train pairs
    consistent = []
    n_pairs = len(task.train)

    for (pred_str, out_prop, out_val), pair_counts in observations.items():
        # Must have observations from ALL train pairs
        if len(pair_counts) == n_pairs:
            # Must be the ONLY outcome for this predicate (no conflicting outcomes)
            # Check: is there any other outcome with the same predicate?
            has_conflict = False
            for (other_pred, other_prop, other_val), other_counts in observations.items():
                if other_pred == pred_str and (other_prop, other_val) != (out_prop, out_val):
                    if len(other_counts) == n_pairs:
                        has_conflict = True
                        break
            if not has_conflict:
                # Reconstruct the predicate object
                # Parse pred_str back to Predicate
                for pred in generate_candidate_predicates(
                    [compute_properties(p.inp, extract_objects(p.input))
                     for p in task.train for p in [p] if p.input.height == p.output.height]
                ):
                    if str(pred) == pred_str:
                        consistent.append((pred, out_prop, out_val))
                        break

    return consistent


def find_consistent_rules_fast(task: ARCTask) -> List[Tuple[Predicate, str, Any]]:
    """Find predicates that are TRUE for recoloured objects and FALSE for unchanged ones."""
    n_pairs = len(task.train)

    # For each train pair, collect:
    # - predicates that are TRUE for recoloured objects (→ outcome colour)
    # - predicates that are TRUE for unchanged objects (→ must NOT conflict)
    pair_true_for_recolour = []  # List of Dict[key, set of outcome colours]
    pair_true_for_unchanged = []  # List of Set[key]

    for pair in task.train:
        inp_grid = pair.input
        out_grid = pair.output

        if inp_grid.height != out_grid.height or inp_grid.width != out_grid.width:
            return []

        inp_objs = extract_objects(inp_grid)
        out_objs = extract_objects(out_grid)

        if not inp_objs:
            return []

        obj_pairs = pair_objects(inp_objs, out_objs)
        inp_props = [compute_properties(p.inp, inp_objs) for p in obj_pairs if p.inp.cells]

        candidates = generate_candidate_predicates(inp_props)

        recolour_map = defaultdict(set)
        unchanged_keys = set()

        for pair_item in obj_pairs:
            if not pair_item.inp.cells:
                continue

            inp_props_item = compute_properties(pair_item.inp, inp_objs)

            for pred in candidates:
                if pred.evaluate(inp_props_item):
                    key = (pred.prop_name, pred.op, pred.value)
                    if pair_item.transform == "recolour" and pair_item.out is not None:
                        recolour_map[key].add(pair_item.out.colour)
                    else:
                        unchanged_keys.add(key)

        pair_true_for_recolour.append(recolour_map)
        pair_true_for_unchanged.append(unchanged_keys)

    if not pair_true_for_recolour:
        return []

    # Find predicates that:
    # 1. Map to a SINGLE outcome colour in ALL train pairs
    # 2. Are NEVER true for unchanged objects
    consistent = []
    first_map = pair_true_for_recolour[0]

    for key, outcomes in first_map.items():
        if len(outcomes) != 1:
            continue

        outcome = next(iter(outcomes))  # Don't pop — that mutates the dict

        # Check consistency across all pairs
        is_consistent = True
        for i in range(n_pairs):
            recolour_map = pair_true_for_recolour[i]
            unchanged_keys = pair_true_for_unchanged[i]

            # Must have same outcome in this pair
            if key not in recolour_map or recolour_map[key] != {outcome}:
                is_consistent = False
                break

            # Must NOT be true for any unchanged object
            if key in unchanged_keys:
                is_consistent = False
                break

        if is_consistent:
            prop_name, op, value = key
            pred = Predicate(prop_name=prop_name, op=op, value=value)
            consistent.append((pred, "colour", outcome))

    # Sort by complexity (simpler first)
    consistent.sort(key=lambda x: x[0].complexity())

    return consistent


# ══════════════════════════════════════════════════════════════════════════════
# GRID RECONSTRUCTION
# ══════════════════════════════════════════════════════════════════════════════

def apply_rules(grid: Grid, rules: List[Tuple[Predicate, str, Any]],
                default_colour: Optional[int] = None) -> Optional[Grid]:
    """Apply learned rules to reconstruct an output grid.

    For each object in the input, check predicates. If a predicate matches,
    set the output colour to the learned outcome. Otherwise, keep original.
    """
    h, w = grid.height, grid.width
    inp_objs = extract_objects(grid)

    if not inp_objs:
        return None

    cells = [row[:] for row in grid.cells]
    any_applied = False

    for obj in inp_objs:
        props = compute_properties(obj, inp_objs)

        for pred, out_prop, out_val in rules:
            if pred.evaluate(props):
                # Apply: set all cells of this object to the outcome colour
                if out_prop == "colour":
                    for r, c in obj.cells:
                        cells[r][c] = out_val
                    any_applied = True
                break  # First matching rule wins

    if not any_applied:
        return None

    return Grid(cells)


def apply_rules_with_background(grid: Grid, rules: List[Tuple[Predicate, str, Any]],
                                 bg_fill: Optional[int] = None) -> Optional[Grid]:
    """Apply rules + optional background fill."""
    h, w = grid.height, grid.width
    inp_objs = extract_objects(grid)

    cells = [row[:] for row in grid.cells]
    any_applied = False

    # Apply object rules
    for obj in inp_objs:
        props = compute_properties(obj, inp_objs)

        for pred, out_prop, out_val in rules:
            if pred.evaluate(props):
                if out_prop == "colour":
                    for r, c in obj.cells:
                        cells[r][c] = out_val
                    any_applied = True
                break

    # Apply background fill if specified
    if bg_fill is not None:
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == 0:
                    cells[r][c] = bg_fill
                    any_applied = True

    if not any_applied:
        return None

    return Grid(cells)


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE LIBRARY
# ══════════════════════════════════════════════════════════════════════════════

TEMPLATE_PATH = os.path.join(_THIS_DIR, "data", "rule_templates.json")


def load_templates() -> List[RuleTemplate]:
    """Load persisted rule templates."""
    if not os.path.exists(TEMPLATE_PATH):
        return []
    with open(TEMPLATE_PATH) as f:
        data = json.load(f)
    return [RuleTemplate.from_dict(d) for d in data]


def save_templates(templates: List[RuleTemplate]):
    """Persist rule templates."""
    os.makedirs(os.path.dirname(TEMPLATE_PATH), exist_ok=True)
    with open(TEMPLATE_PATH, "w") as f:
        json.dump([t.to_dict() for t in templates], f, indent=2)


def templates_to_rules(templates: List[RuleTemplate]) -> List[Tuple[Predicate, str, Any]]:
    """Convert templates to (predicate, outcome_prop, outcome_value) rules."""
    return [(t.predicate, t.outcome_prop, t.outcome_value) for t in templates]


# ══════════════════════════════════════════════════════════════════════════════
# VERIFICATION (hard gate)
# ══════════════════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c]
               for r in range(g1.height) for c in range(g1.width))


def verify_and_predict(rule_fn: Callable, task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Hard gate: rule must reproduce ALL train pairs exactly."""
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    for pair in task.train:
        pred = rule_fn(pair.input)
        if pred is None or not grids_equal(pred, pair.output):
            return None
    pred = rule_fn(task.test[0].input)
    if pred is None:
        return None
    return pred


# ══════════════════════════════════════════════════════════════════════════════
# MAIN SOLVER
# ══════════════════════════════════════════════════════════════════════════════

def solve(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Try predicate induction on a task."""

    # Skip size-changing tasks
    same_size = all(p.input.height == p.output.height and p.input.width == p.output.width
                    for p in task.train)
    if not same_size:
        return None

    # Step 1: Find consistent predicates
    rules = find_consistent_rules_fast(task)

    if not rules:
        return None

    # Step 2: Try applying rules (object recolour only)
    def make_recolour_rule(r):
        def rule_fn(grid):
            return apply_rules(grid, r)
        return rule_fn

    result = verify_and_predict(make_recolour_rule(rules), task)
    if result:
        return result, f"predicate_recolour_{len(rules)}_rules"

    # Step 3: Try with background fill
    # Learn background fill colour from train pairs
    bg_fills = set()
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    bg_fills.add(pair.output.cells[r][c])

    for bg in bg_fills:
        def make_bg_rule(r, b):
            def rule_fn(grid):
                return apply_rules_with_background(grid, r, bg_fill=b)
            return rule_fn

        result = verify_and_predict(make_bg_rule(rules, bg), task)
        if result:
            return result, f"predicate_recolour+bg_{bg}"

    return None


# ══════════════════════════════════════════════════════════════════════════════
# DIAGNOSTIC
# ══════════════════════════════════════════════════════════════════════════════

def diagnose(task: ARCTask):
    """Print detailed diagnostic for a task."""
    print(f"Task: {task.name}")
    print(f"Train pairs: {len(task.train)}")

    for i, pair in enumerate(task.train):
        inp_objs = extract_objects(pair.input)
        out_objs = extract_objects(pair.output)
        obj_pairs = pair_objects(inp_objs, out_objs)

        print(f"\n  Train {i}: {pair.input.height}x{pair.input.width}")
        print(f"    Input objects: {len(inp_objs)}")
        for j, obj in enumerate(inp_objs):
            props = compute_properties(obj, inp_objs)
            print(f"      [{j}] colour={obj.colour}, cells={obj.cell_count}, "
                  f"size_rank={props.size_rank}, touches_border={props.touches_border}")

        print(f"    Output objects: {len(out_objs)}")
        for j, obj in enumerate(out_objs):
            print(f"      [{j}] colour={obj.colour}, cells={obj.cell_count}")

        print(f"    Pairs:")
        for p in obj_pairs:
            if p.out:
                print(f"      {p.transform}: colour {p.inp.colour}→{p.out.colour}, "
                      f"cells {p.inp.cell_count}→{p.out.cell_count}")
            else:
                print(f"      disappeared: colour {p.inp.colour}, cells {p.inp.cell_count}")

    rules = find_consistent_rules_fast(task)
    print(f"\n  Consistent rules found: {len(rules)}")
    for pred, out_prop, out_val in rules:
        print(f"    IF {pred} THEN {out_prop}={out_val}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--diagnose", type=str, default=None, help="Diagnose a specific task")
    args = p.parse_args()

    if args.diagnose:
        task = load_task(os.path.join(args.batch, args.diagnose),
                         name=os.path.splitext(args.diagnose)[0])
        diagnose(task)
        sys.exit(0)

    files = sorted(f for f in os.listdir(args.batch) if f.endswith(".json"))

    solved = total = 0
    sources = {}
    all_results = []

    print("═" * 60)
    print(" PREDICATE INDUCTION v050")
    print("═" * 60)
    print()

    for fname in files:
        task = load_task(os.path.join(args.batch, fname),
                         name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1

        try:
            signal.setitimer(signal.ITIMER_REAL, 30.0)
            result = solve(task)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except Exception as e:
            signal.setitimer(signal.ITIMER_REAL, 0)
            result = None

        tid = os.path.splitext(fname)[0]
        if result is not None:
            pred, src = result
            ok = (pred == task.test[0].expected_output)
            if ok:
                solved += 1
            sources[src] = sources.get(src, 0) + 1
            all_results.append((tid, ok, src))
            if args.verbose or ok:
                print(f"  {tid}: {'✓' if ok else '✗'} src={src}")
        else:
            sources["none"] = sources.get("none", 0) + 1
            all_results.append((tid, False, "none"))
            if args.verbose:
                print(f"  {tid}: ✗")

    print(f"\n{'═' * 60}")
    print(f" PREDICATE INDUCTION RESULTS ({total} tasks)")
    print(f"{'═' * 60}")
    print(f"  SOLVED: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"\n  Solvers used:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        if src != "none":
            print(f"    {src}: {count}")
    print(f"  Unsolved: {sources.get('none', 0)}")

    print(f"\n  Solved tasks:")
    for tid, ok, src in all_results:
        if ok:
            print(f"    {tid} ← {src}")

    print(f"\n  Unsolved tasks:")
    for tid, ok, src in all_results:
        if not ok:
            print(f"    {tid}")
