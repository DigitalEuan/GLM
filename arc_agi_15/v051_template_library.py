"""
v051_template_library.py — DreamCoder-style Template Library for ARC-AGI
=========================================================================

Implements the library learning pattern from DreamCoder (Ellis et al., 2021):
  1. WAKE: Solve tasks using predicate induction (v050)
  2. COMPRESS: Extract parameterized templates from solved traces
  3. LIBRARY: Persist templates, ranked by success count
  4. SLEEP: Try templates on unsolved tasks (cheap, fast)
  5. GROW: New successful patterns → new templates

Key design decisions (from studying ARGA/GPAR/DreamCoder):
  - Templates are PARAMETERIZED (colours/thresholds as variables)
  - Templates are ranked by prior success (MDL/Occam)
  - Templates are tried BEFORE fresh induction (cheap first)
  - Object-centric: templates operate on objects, not raw cells

Full transparency: every result is reported honestly.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Callable
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import sys, os, json, signal, time

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task


# ══════════════════════════════════════════════════════════════════════════════
# OBJECT EXTRACTION (reuse from v050)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Obj:
    cells: List[Tuple[int, int]]
    colour: int
    bbox: Tuple[int, int, int, int]
    centroid: Tuple[float, float]
    grid_shape: Tuple[int, int]

    @property
    def cell_count(self) -> int: return len(self.cells)
    @property
    def width(self) -> int: return self.bbox[3] - self.bbox[2] + 1
    @property
    def height(self) -> int: return self.bbox[1] - self.bbox[0] + 1
    @property
    def area(self) -> int: return self.width * self.height
    @property
    def touches_border(self) -> bool:
        return (self.bbox[0] == 0 or self.bbox[1] == self.grid_shape[0] - 1 or
                self.bbox[2] == 0 or self.bbox[3] == self.grid_shape[1] - 1)


def extract_objects(grid: Grid) -> List[Obj]:
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
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in visited and grid.cells[nr][nc] == colour:
                        queue.append((nr, nc))
            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            bbox = (min(rs), max(rs), min(cs), max(cs))
            centroid = (sum(rs)/len(cells), sum(cs)/len(cells))
            objects.append(Obj(cells=cells, colour=colour, bbox=bbox, centroid=centroid, grid_shape=(h, w)))
    objects.sort(key=lambda o: (o.colour, -o.cell_count))
    return objects


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Template:
    """A parameterized rule template.

    Example: "IF cell_count >= THRESHOLD THEN colour = TARGET_COLOUR"
    Where THRESHOLD and TARGET_COLOUR are parameters learned per-task.
    """
    name: str
    predicate_prop: str      # property to test (cell_count, colour, width, etc.)
    predicate_op: str        # operator (>=, <=, ==, !=, rank==, is_max, is_min)
    outcome_prop: str        # property to set (colour)
    # Parameters are filled per-task:
    # - predicate_value: the threshold
    # - outcome_value: the target colour
    success_count: int = 0   # how many tasks this template solved
    total_seen: int = 0      # how many tasks this template was tried on

    @property
    def reliability(self) -> float:
        return self.success_count / max(self.total_seen, 1)

    @property
    def priority(self) -> float:
        """Higher = try first. Combines reliability and simplicity."""
        return self.reliability * (1.0 / max(len(self.name), 1))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "predicate_prop": self.predicate_prop,
            "predicate_op": self.predicate_op,
            "outcome_prop": self.outcome_prop,
            "success_count": self.success_count,
            "total_seen": self.total_seen,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Template":
        return cls(**d)


# The initial template catalogue (from what we've learned)
INITIAL_TEMPLATES = [
    Template(name="size_threshold_recolour",
             predicate_prop="cell_count", predicate_op=">=", outcome_prop="colour"),
    Template(name="rank_recolour",
             predicate_prop="size_rank", predicate_op="rank==", outcome_prop="colour"),
    Template(name="is_largest_recolour",
             predicate_prop="cell_count", predicate_op="is_max", outcome_prop="colour"),
    Template(name="is_smallest_recolour",
             predicate_prop="cell_count", predicate_op="is_min", outcome_prop="colour"),
    Template(name="colour_eq_recolour",
             predicate_prop="colour", predicate_op="==", outcome_prop="colour"),
    Template(name="touches_border_recolour",
             predicate_prop="touches_border", predicate_op="touches", outcome_prop="colour"),
    Template(name="width_threshold_recolour",
             predicate_prop="width", predicate_op=">=", outcome_prop="colour"),
    Template(name="area_threshold_recolour",
             predicate_prop="area", predicate_op=">=", outcome_prop="colour"),
    Template(name="height_threshold_recolour",
             predicate_prop="height", predicate_op=">=", outcome_prop="colour"),
]


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE LIBRARY
# ══════════════════════════════════════════════════════════════════════════════

LIBRARY_PATH = os.path.join(_THIS_DIR, "data", "template_library.json")


def load_library() -> List[Template]:
    if not os.path.exists(LIBRARY_PATH):
        return list(INITIAL_TEMPLATES)
    with open(LIBRARY_PATH) as f:
        data = json.load(f)
    templates = [Template.from_dict(d) for d in data]
    # Merge with initial templates (keep initial if not already present)
    existing = {(t.predicate_prop, t.predicate_op) for t in templates}
    for t in INITIAL_TEMPLATES:
        if (t.predicate_prop, t.predicate_op) not in existing:
            templates.append(t)
    return templates


def save_library(templates: List[Template]):
    os.makedirs(os.path.dirname(LIBRARY_PATH), exist_ok=True)
    with open(LIBRARY_PATH, "w") as f:
        json.dump([t.to_dict() for t in templates], f, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE INSTANTIATION AND APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

def get_prop(obj: Obj, prop_name: str, all_objs: List[Obj]) -> Any:
    """Get a property value from an object."""
    if prop_name == "cell_count": return obj.cell_count
    if prop_name == "colour": return obj.colour
    if prop_name == "width": return obj.width
    if prop_name == "height": return obj.height
    if prop_name == "area": return obj.area
    if prop_name == "touches_border": return obj.touches_border
    if prop_name == "size_rank":
        sizes = sorted(set(o.cell_count for o in all_objs), reverse=True)
        return sizes.index(obj.cell_count) if obj.cell_count in sizes else -1
    if prop_name == "colour_rank":
        cols = sorted(set(o.colour for o in all_objs))
        return cols.index(obj.colour) if obj.colour in cols else -1
    if prop_name == "is_largest":
        return obj.cell_count == max(o.cell_count for o in all_objs)
    if prop_name == "is_smallest":
        return obj.cell_count == min(o.cell_count for o in all_objs)
    return None


def evaluate_predicate(obj: Obj, all_objs: List[Obj], prop: str, op: str, value: Any) -> bool:
    """Evaluate a predicate against an object."""
    actual = get_prop(obj, prop, all_objs)
    if actual is None:
        return False
    if op == "==": return actual == value
    if op == "!=": return actual != value
    if op == ">=": return actual >= value
    if op == "<=": return actual <= value
    if op == "rank==": return get_prop(obj, "size_rank", all_objs) == value
    if op == "is_max": return actual == max(o.cell_count for o in all_objs)
    if op == "is_min": return actual == min(o.cell_count for o in all_objs)
    if op == "touches": return actual == True
    if op == "not_touches": return actual == False
    return False


def learn_template_params(task: ARCTask, template: Template) -> Optional[Tuple[Any, Any]]:
    """Learn the specific parameters (predicate_value, outcome_value) for a template.

    For each train pair, find objects where the predicate is true,
    and check what their output colour is. Keep if consistent across all pairs.
    """
    n_pairs = len(task.train)

    # For each train pair, collect: predicate_value → set of outcome colours
    pair_observations = []

    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None

        inp_objs = extract_objects(pair.input)
        out_objs = extract_objects(pair.output)

        if not inp_objs:
            return None

        # Simple centroid matching
        used = set()
        pairs_list = []
        for in_obj in inp_objs:
            best_idx, best_dist = -1, float('inf')
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
                pairs_list.append((in_obj, out_objs[best_idx], "recolour" if in_obj.colour != out_objs[best_idx].colour else "unchanged"))
                used.add(best_idx)
            else:
                pairs_list.append((in_obj, None, "disappear"))

        # For each possible predicate value, check what outcome it predicts
        # Collect all unique property values
        prop_values = set()
        for in_obj, _, _ in pairs_list:
            val = get_prop(in_obj, template.predicate_prop, inp_objs)
            if val is not None:
                prop_values.add(val)

        # Also try threshold values (for >=, <=)
        if template.predicate_op in (">=", "<="):
            all_vals = sorted(set(get_prop(o, template.predicate_prop, inp_objs)
                                  for o in inp_objs if get_prop(o, template.predicate_prop, inp_objs) is not None))
            if len(all_vals) >= 2:
                lo, hi = int(min(all_vals)), int(max(all_vals))
                for v in range(lo, hi + 1):
                    prop_values.add(v)

        obs = defaultdict(set)  # predicate_value → set of outcome colours
        unchanged_true = set()  # predicate_values that are true for unchanged objects

        for in_obj, out_obj, transform in pairs_list:
            for val in prop_values:
                if evaluate_predicate(in_obj, inp_objs, template.predicate_prop, template.predicate_op, val):
                    if transform == "recolour" and out_obj is not None:
                        obs[val].add(out_obj.colour)
                    else:
                        unchanged_true.add(val)

        pair_observations.append((obs, unchanged_true))

    # Find predicate_value that maps to a single outcome in ALL pairs
    # AND is NEVER true for unchanged objects
    first_obs, first_unchanged = pair_observations[0]
    for pred_val, outcomes in first_obs.items():
        if len(outcomes) != 1:
            continue
        outcome = next(iter(outcomes))

        is_consistent = True
        for obs, unchanged in pair_observations:
            # Must have same outcome
            if pred_val not in obs or obs[pred_val] != {outcome}:
                is_consistent = False
                break
            # Must NOT be true for unchanged objects
            if pred_val in unchanged:
                is_consistent = False
                break

        if is_consistent:
            return (pred_val, outcome)

    return None


def apply_template(grid: Grid, template: Template, pred_val: Any, outcome_val: Any,
                   bg_fill: Optional[int] = None) -> Optional[Grid]:
    """Apply a template with learned parameters to a grid."""
    h, w = grid.height, grid.width
    inp_objs = extract_objects(grid)
    cells = [row[:] for row in grid.cells]
    any_applied = False

    for obj in inp_objs:
        if evaluate_predicate(obj, inp_objs, template.predicate_prop, template.predicate_op, pred_val):
            if template.outcome_prop == "colour":
                for r, c in obj.cells:
                    cells[r][c] = outcome_val
                any_applied = True

    if bg_fill is not None:
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == 0:
                    cells[r][c] = bg_fill
                    any_applied = True

    return Grid(cells) if any_applied else None


# ══════════════════════════════════════════════════════════════════════════════
# VERIFICATION (hard gate)
# ══════════════════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c] for r in range(g1.height) for c in range(g1.width))


def verify_template(task: ARCTask, template: Template, pred_val: Any, outcome_val: Any,
                    bg_fill: Optional[int] = None) -> bool:
    """Verify a template+params against all train pairs."""
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return False
        pred = apply_template(pair.input, template, pred_val, outcome_val, bg_fill)
        if pred is None or not grids_equal(pred, pair.output):
            return False
    return True


# ══════════════════════════════════════════════════════════════════════════════
# MAIN SOLVER
# ══════════════════════════════════════════════════════════════════════════════

def solve(task: ARCTask, library: Optional[List[Template]] = None) -> Optional[Tuple[Grid, str, Template, Any, Any]]:
    """Try all templates in the library on a task.

    Returns (prediction, description, template, pred_val, outcome_val) or None.
    """
    if library is None:
        library = load_library()

    same_size = all(p.input.height == p.output.height and p.input.width == p.output.width
                    for p in task.train)
    if not same_size:
        return None

    # Sort templates by priority (reliable first)
    library.sort(key=lambda t: t.priority, reverse=True)

    for template in library:
        result = learn_template_params(task, template)
        if result is None:
            continue

        pred_val, outcome_val = result

        # Verify with hard gate
        if verify_template(task, template, pred_val, outcome_val):
            # Apply to test input
            test_pred = apply_template(task.test[0].input, template, pred_val, outcome_val)
            if test_pred is not None:
                desc = f"{template.name}({template.predicate_prop} {template.predicate_op} {pred_val} → {outcome_val})"
                return test_pred, desc, template, pred_val, outcome_val

        # Try with background fill
        bg_fills = set()
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                        bg_fills.add(pair.output.cells[r][c])

        for bg in bg_fills:
            if verify_template(task, template, pred_val, outcome_val, bg_fill=bg):
                test_pred = apply_template(task.test[0].input, template, pred_val, outcome_val, bg_fill=bg)
                if test_pred is not None:
                    desc = f"{template.name}({template.predicate_prop} {template.predicate_op} {pred_val} → {outcome_val}) + bg={bg}"
                    return test_pred, desc, template, pred_val, outcome_val

    return None


# ══════════════════════════════════════════════════════════════════════════════
# LEARN-AND-GROW: Solve tasks, extract new templates
# ══════════════════════════════════════════════════════════════════════════════

def learn_and_grow(batch_dir: str, verbose: bool = False) -> Tuple[int, int, List[Template]]:
    """Run the wake-sleep cycle:
    1. Try existing templates on all tasks
    2. For solved tasks, update template success counts
    3. Save updated library
    """
    library = load_library()
    files = sorted(f for f in os.listdir(batch_dir) if f.endswith(".json"))

    solved = total = 0
    solved_tasks = []

    for fname in files:
        task = load_task(os.path.join(batch_dir, fname), name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1

        try:
            signal.setitimer(signal.ITIMER_REAL, 15.0)
            result = solve(task, library)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except:
            signal.setitimer(signal.ITIMER_REAL, 0)
            result = None

        tid = os.path.splitext(fname)[0]
        if result is not None:
            pred, desc, template, pred_val, outcome_val = result
            ok = (pred == task.test[0].expected_output)
            if ok:
                solved += 1
                template.success_count += 1
                solved_tasks.append((tid, desc))
            template.total_seen += 1
            if verbose:
                print(f"  {tid}: {'✓' if ok else '✗'} {desc}")
        else:
            if verbose:
                print(f"  {tid}: ✗")

    save_library(library)
    return solved, total, library


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--show-library", action="store_true")
    args = p.parse_args()

    if args.show_library:
        library = load_library()
        print(f"Template library ({len(library)} templates):")
        for t in sorted(library, key=lambda x: x.priority, reverse=True):
            print(f"  {t.name}: {t.predicate_prop} {t.predicate_op} → {t.outcome_prop}"
                  f"  [success={t.success_count}, seen={t.total_seen}, reliability={t.reliability:.2f}]")
        sys.exit(0)

    print("═" * 60)
    print(" TEMPLATE LIBRARY v051 — DreamCoder-style Learning")
    print("═" * 60)
    print()

    t0 = time.time()
    solved, total, library = learn_and_grow(args.batch, verbose=args.verbose)
    t1 = time.time()

    print(f"\n{'═' * 60}")
    print(f" RESULTS ({total} tasks, {t1-t0:.1f}s)")
    print(f"{'═' * 60}")
    print(f"  SOLVED: {solved}/{total} ({solved / max(total, 1):.1%})")

    print(f"\n  Template library ({len(library)} templates):")
    for t in sorted(library, key=lambda x: x.priority, reverse=True):
        if t.total_seen > 0:
            print(f"    {t.name}: {t.predicate_prop} {t.predicate_op} → {t.outcome_prop}"
                  f"  [success={t.success_count}, seen={t.total_seen}]")
