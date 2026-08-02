"""
v052_object_class_sentences.py — Object-Class-Partitioned Geometric Sentences
==============================================================================

Addresses Disconnection 1 from the Rewiring Brief:
"Candidate generation never conditions on objects"

Instead of building ONE flat GeometricSentence per task (which can only express
global rules), we:
  1. Decompose grids into objects
  2. Classify objects by properties (size, colour, position)
  3. Build SEPARATE sentences per object class
  4. Apply class-specific transformations

This lets us express: "objects with cell_count >= 4 get colour 6,
objects with cell_count < 4 stay unchanged."

Full transparency: every result is reported honestly.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set, Callable
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import sys, os, signal

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task


# ══════════════════════════════════════════════════════════════════════════════
# OBJECT EXTRACTION
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
# OBJECT PAIRING
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ObjPair:
    inp: Obj
    out: Optional[Obj]
    transform: str  # "recolour", "unchanged", "disappear", "appear"


def pair_objects(inp_objs: List[Obj], out_objs: List[Obj]) -> List[ObjPair]:
    pairs = []
    used = set()
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
            out_obj = out_objs[best_idx]
            used.add(best_idx)
            t = "recolour" if in_obj.colour != out_obj.colour else "unchanged"
            pairs.append(ObjPair(inp=in_obj, out=out_obj, transform=t))
        else:
            pairs.append(ObjPair(inp=in_obj, out=None, transform="disappear"))
    for i, out_obj in enumerate(out_objs):
        if i not in used:
            pairs.append(ObjPair(inp=Obj(cells=[], colour=0, bbox=(0,0,0,0), centroid=(0,0), grid_shape=out_obj.grid_shape),
                                 out=out_obj, transform="appear"))
    return pairs


# ══════════════════════════════════════════════════════════════════════════════
# CLASS PARTITIONING
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ObjectClass:
    """A class of objects defined by a predicate."""
    name: str
    predicate: Callable[[Obj, List[Obj]], bool]
    description: str


# The class catalogue
CLASS_CATALOGUE = [
    # Size-based classes
    ObjectClass("largest", lambda o, all: o.cell_count == max(x.cell_count for x in all), "Largest object"),
    ObjectClass("smallest", lambda o, all: o.cell_count == min(x.cell_count for x in all), "Smallest object"),
    ObjectClass("size_above_median", lambda o, all: o.cell_count > sorted(x.cell_count for x in all)[len(all)//2], "Above median size"),
    ObjectClass("size_below_median", lambda o, all: o.cell_count <= sorted(x.cell_count for x in all)[len(all)//2], "Below median size"),
    ObjectClass("size_ge_4", lambda o, all: o.cell_count >= 4, "Size >= 4"),
    ObjectClass("size_ge_3", lambda o, all: o.cell_count >= 3, "Size >= 3"),
    ObjectClass("size_ge_2", lambda o, all: o.cell_count >= 2, "Size >= 2"),
    ObjectClass("size_eq_1", lambda o, all: o.cell_count == 1, "Single cell"),
    # Colour-based classes
    ObjectClass("colour_2", lambda o, all: o.colour == 2, "Colour 2"),
    ObjectClass("colour_5", lambda o, all: o.colour == 5, "Colour 5"),
    ObjectClass("colour_8", lambda o, all: o.colour == 8, "Colour 8"),
    # Position-based classes
    ObjectClass("touches_border", lambda o, all: o.touches_border, "Touches border"),
    ObjectClass("not_touches_border", lambda o, all: not o.touches_border, "Interior"),
    # Rank-based classes
    ObjectClass("rank_0", lambda o, all: sorted(set(x.cell_count for x in all), reverse=True).index(o.cell_count) == 0 if o.cell_count in set(x.cell_count for x in all) else False, "Size rank 0"),
]


# ══════════════════════════════════════════════════════════════════════════════
# CLASS-SPECIFIC SENTENCE
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ClassSentence:
    """A transformation rule for a specific class of objects."""
    obj_class: ObjectClass
    outcome_colour: Optional[int] = None  # If set, recolour objects to this
    outcome_delta: Optional[Tuple[int, int]] = None  # If set, move objects by this
    success_count: int = 0
    total_seen: int = 0


def learn_class_sentences(task: ARCTask) -> List[ClassSentence]:
    """Learn class-specific sentences from train pairs.

    For each object class, check if ALL objects in that class undergo
    the same transformation across ALL train pairs.
    """
    n_pairs = len(task.train)
    class_observations = defaultdict(lambda: defaultdict(set))
    # class_name → pair_idx → set of (transform_type, outcome_value)

    for pair_idx, pair in enumerate(task.train):
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return []

        inp_objs = extract_objects(pair.input)
        out_objs = extract_objects(pair.output)
        obj_pairs = pair_objects(inp_objs, out_objs)

        for obj_class in CLASS_CATALOGUE:
            for obj_pair in obj_pairs:
                if not obj_pair.inp.cells:
                    continue
                if obj_class.predicate(obj_pair.inp, inp_objs):
                    if obj_pair.transform == "recolour" and obj_pair.out:
                        class_observations[obj_class.name][pair_idx].add(("recolour", obj_pair.out.colour))
                    elif obj_pair.transform == "unchanged":
                        class_observations[obj_class.name][pair_idx].add(("unchanged", obj_pair.inp.colour))

    # Find classes with consistent outcomes across ALL pairs
    sentences = []
    for obj_class in CLASS_CATALOGUE:
        obs = class_observations[obj_class.name]
        if len(obs) != n_pairs:
            continue

        # Check if all pairs have the same single outcome
        outcomes = set()
        for pair_idx in range(n_pairs):
            pair_outcomes = obs[pair_idx]
            if len(pair_outcomes) != 1:
                outcomes = set()
                break
            outcomes.add(next(iter(pair_outcomes)))

        if len(outcomes) == 1:
            outcome = next(iter(outcomes))
            transform_type, outcome_val = outcome

            if transform_type == "recolour":
                sentences.append(ClassSentence(
                    obj_class=obj_class,
                    outcome_colour=outcome_val,
                ))
            # "unchanged" is the default, no sentence needed

    return sentences


def apply_class_sentences(grid: Grid, sentences: List[ClassSentence]) -> Optional[Grid]:
    """Apply class-specific sentences to a grid."""
    h, w = grid.height, grid.width
    inp_objs = extract_objects(grid)
    cells = [row[:] for row in grid.cells]
    any_applied = False

    for obj in inp_objs:
        for sentence in sentences:
            if sentence.obj_class.predicate(obj, inp_objs):
                if sentence.outcome_colour is not None:
                    for r, c in obj.cells:
                        cells[r][c] = sentence.outcome_colour
                    any_applied = True
                break  # First matching class wins

    return Grid(cells) if any_applied else None


# ══════════════════════════════════════════════════════════════════════════════
# BACKGROUND FILL + CLASS SENTENCES
# ══════════════════════════════════════════════════════════════════════════════

def apply_class_sentences_with_bg(grid: Grid, sentences: List[ClassSentence],
                                   bg_fill: Optional[int] = None) -> Optional[Grid]:
    """Apply class sentences + optional background fill."""
    h, w = grid.height, grid.width
    inp_objs = extract_objects(grid)
    cells = [row[:] for row in grid.cells]
    any_applied = False

    for obj in inp_objs:
        for sentence in sentences:
            if sentence.obj_class.predicate(obj, inp_objs):
                if sentence.outcome_colour is not None:
                    for r, c in obj.cells:
                        cells[r][c] = sentence.outcome_colour
                    any_applied = True
                break

    if bg_fill is not None:
        for r in range(h):
            for c in range(w):
                if grid.cells[r][c] == 0:
                    cells[r][c] = bg_fill
                    any_applied = True

    return Grid(cells) if any_applied else None


# ══════════════════════════════════════════════════════════════════════════════
# VERIFICATION
# ══════════════════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c] for r in range(g1.height) for c in range(g1.width))


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER
# ══════════════════════════════════════════════════════════════════════════════

def solve(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """Try object-class-partitioned sentences on a task."""
    same_size = all(p.input.height == p.output.height and p.input.width == p.output.width
                    for p in task.train)
    if not same_size:
        return None

    sentences = learn_class_sentences(task)
    if not sentences:
        return None

    # Try without background fill
    def rule_no_bg(grid):
        return apply_class_sentences(grid, sentences)

    all_pass = True
    for pair in task.train:
        pred = rule_no_bg(pair.input)
        if pred is None or not grids_equal(pred, pair.output):
            all_pass = False
            break

    if all_pass:
        test_pred = rule_no_bg(task.test[0].input)
        if test_pred is not None:
            desc = " + ".join(f"{s.obj_class.name}→{s.outcome_colour}" for s in sentences)
            return test_pred, f"class_sentences({desc})"

    # Try with background fill
    bg_fills = set()
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    bg_fills.add(pair.output.cells[r][c])

    for bg in bg_fills:
        def rule_with_bg(grid, b=bg):
            return apply_class_sentences_with_bg(grid, sentences, bg_fill=b)

        all_pass = True
        for pair in task.train:
            pred = rule_with_bg(pair.input)
            if pred is None or not grids_equal(pred, pair.output):
                all_pass = False
                break

        if all_pass:
            test_pred = rule_with_bg(task.test[0].input)
            if test_pred is not None:
                desc = " + ".join(f"{s.obj_class.name}→{s.outcome_colour}" for s in sentences)
                return test_pred, f"class_sentences({desc}) + bg={bg}"

    return None


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    files = sorted(f for f in os.listdir(args.batch) if f.endswith(".json"))

    solved = total = 0
    sources = {}
    all_results = []

    print("═" * 60)
    print(" OBJECT-CLASS SENTENCES v052")
    print("═" * 60)
    print()

    for fname in files:
        task = load_task(os.path.join(args.batch, fname), name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1

        try:
            signal.setitimer(signal.ITIMER_REAL, 15.0)
            result = solve(task)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except:
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
    print(f" RESULTS ({total} tasks)")
    print(f"{'═' * 60}")
    print(f"  SOLVED: {solved}/{total} ({solved / max(total, 1):.1%})")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        if src != "none":
            print(f"    {src}: {count}")
