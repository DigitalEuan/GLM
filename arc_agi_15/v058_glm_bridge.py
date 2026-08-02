"""
v058_glm_bridge.py — GLM ↔ Grid Solver Bridge with Continuous Learning
========================================================================

Bridges the GLM's concept reasoning with grid-level solvers.

The continuous loop:
  1. GRID → CONCEPTS: Analyse ARC task, extract concept-level description
  2. CONCEPTS → CRG: Feed into continuous learner, grow the knowledge base
  3. CRG → SOLVER: Use CRG relationships to suggest which solver to try
  4. SOLVER → VERIFY: Hard-gate against train pairs
  5. VERIFY → CRG: Feed success/failure back, reinforce successful patterns

The GLM learns continuously:
  - Each task teaches it new concept co-occurrences
  - Successful solvers reinforce CRG edges
  - Failed attempts are recorded (negative evidence)
  - The CRG grows with every task processed

Full transparency: every result is reported honestly.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import sys, os, json, signal, hashlib, time

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

_GLM_DIR = os.path.join(os.path.dirname(_THIS_DIR), 'UBP_Repo', 'core_studio_v4.0', 'GLM')
_CORE_DIR = os.path.join(os.path.dirname(_THIS_DIR), 'UBP_Repo', 'core_studio_v4.0', 'core')
if _GLM_DIR not in sys.path:
    sys.path.insert(0, _GLM_DIR)
if _CORE_DIR not in sys.path:
    sys.path.insert(0, _CORE_DIR)

from arc_loader import Grid, ARCTask, load_task


# ══════════════════════════════════════════════════════════════════════════════
# CONCEPT EXTRACTION — Grid → Concepts
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TaskConcepts:
    """Concept-level description of an ARC task."""
    task_id: str
    grid_size: str              # e.g. "6x6"
    fill_count: int             # number of cells filled
    erase_count: int            # number of cells erased
    recolour_count: int         # number of cells recoloured
    object_count: int           # number of input objects
    object_sizes: List[int]     # sizes of input objects
    object_colours: List[int]   # colours of input objects
    fill_colours: List[int]     # colours used for fill
    recolour_map: Dict[int, int]  # colour mappings
    has_size_change: bool       # whether grid size changes
    delta_hw: int               # MOG hamming weight change
    category: str               # preserve/enrich/simplify/compress/expand
    description: str            # natural language description


def extract_concepts(task: ARCTask) -> TaskConcepts:
    """Extract concept-level description from an ARC task."""
    pair = task.train[0]
    h, w = pair.input.height, pair.input.width
    same_size = pair.input.height == pair.output.height and pair.input.width == pair.output.width

    # Count changes
    fill_count = 0
    erase_count = 0
    recolour_count = 0
    fill_colours = []
    recolour_map = {}

    if same_size:
        for r in range(h):
            for c in range(w):
                ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                if ic == 0 and oc != 0:
                    fill_count += 1
                    fill_colours.append(oc)
                elif ic != 0 and oc == 0:
                    erase_count += 1
                elif ic != 0 and oc != 0 and ic != oc:
                    recolour_count += 1
                    recolour_map[ic] = oc

    # Extract objects
    objects = []
    visited = set()
    for r in range(h):
        for c in range(w):
            if (r, c) in visited or pair.input.cells[r][c] == 0:
                continue
            colour = pair.input.cells[r][c]
            cells = set()
            queue = [(r, c)]
            while queue:
                cr, cc = queue.pop()
                if (cr, cc) in cells:
                    continue
                cells.add((cr, cc))
                visited.add((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in cells and pair.input.cells[nr][nc] == colour:
                        queue.append((nr, nc))
            objects.append({'colour': colour, 'size': len(cells)})

    # Compute delta_hw (simplified)
    def mog_encode(grid):
        bits = [0] * 24
        for r in range(grid.height):
            for c in range(grid.width):
                if grid.cells[r][c] != 0:
                    mog_r = grid.cells[r][c] % 4
                    mog_c = (r + c) % 6
                    bits[mog_r * 6 + mog_c] = 1
        return bits

    in_hw = sum(mog_encode(pair.input))
    out_hw = sum(mog_encode(pair.output))
    delta_hw = out_hw - in_hw

    # Category
    if delta_hw == 0:
        category = "preserve"
    elif delta_hw < -6:
        category = "compress"
    elif delta_hw < 0:
        category = "simplify"
    elif delta_hw > 6:
        category = "expand"
    elif delta_hw > 0:
        category = "enrich"
    else:
        category = "unknown"

    # Build description
    parts = []
    if fill_count > 0:
        fc = Counter(fill_colours).most_common(3)
        fc_str = ', '.join(f'colour {c} ({n}x)' for c, n in fc)
        parts.append(f'fill {fill_count} cells with {fc_str}')
    if erase_count > 0:
        parts.append(f'erase {erase_count} cells')
    if recolour_count > 0:
        rc_str = ', '.join(f'{k}→{v}' for k, v in list(recolour_map.items())[:3])
        parts.append(f'recolour {recolour_count} cells: {rc_str}')

    obj_desc = ', '.join('obj(colour={}, size={})'.format(o['colour'], o['size']) for o in objects[:4])
    description = f'grid {h}x{w} {category} ' + '; '.join(parts) + f'. objects: {obj_desc}'

    return TaskConcepts(
        task_id=task.name,
        grid_size=f'{h}x{w}',
        fill_count=fill_count,
        erase_count=erase_count,
        recolour_count=recolour_count,
        object_count=len(objects),
        object_sizes=[o['size'] for o in objects],
        object_colours=[o['colour'] for o in objects],
        fill_colours=list(set(fill_colours)),
        recolour_map=recolour_map,
        has_size_change=not same_size,
        delta_hw=delta_hw,
        category=category,
        description=description,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER CATALOGUE — Grid-level solvers
# ══════════════════════════════════════════════════════════════════════════════

def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c] for r in range(g1.height) for c in range(g1.width))


def extract_objects(grid: Grid) -> List[Dict]:
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
            centroid_r = sum(r for r, _ in cells) / len(cells)
            centroid_c = sum(c for _, c in cells) / len(cells)
            objects.append({'cells': cells, 'colour': colour, 'size': len(cells),
                          'centroid': (centroid_r, centroid_c)})
    return objects


# Solver functions
def solver_gravity_down(grid: Grid) -> Grid:
    h, w = grid.height, grid.width
    cells = [[0]*w for _ in range(h)]
    for c in range(w):
        col_cells = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
        for i, val in enumerate(col_cells):
            cells[h - len(col_cells) + i][c] = val
    return Grid(cells)


def solver_fill(grid: Grid, colour: int) -> Grid:
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if cells[r][c] == 0:
                cells[r][c] = colour
    return Grid(cells)


def solver_erase(grid: Grid, colour: int) -> Grid:
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if cells[r][c] == colour:
                cells[r][c] = 0
    return Grid(cells)


def solver_recolour(grid: Grid, from_col: int, to_col: int) -> Grid:
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if cells[r][c] == from_col:
                cells[r][c] = to_col
    return Grid(cells)


def solver_interior_fill(grid: Grid, colour: int) -> Optional[Grid]:
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    border_connected = set()
    queue = []
    for r in range(h):
        for c in range(w):
            if cells[r][c] == 0:
                if r == 0 or r == h-1 or c == 0 or c == w-1:
                    queue.append((r, c))
                    border_connected.add((r, c))
    while queue:
        cr, cc = queue.pop()
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = cr+dr, cc+dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in border_connected:
                if cells[nr][nc] == 0:
                    border_connected.add((nr, nc))
                    queue.append((nr, nc))
    changed = False
    for r in range(h):
        for c in range(w):
            if cells[r][c] == 0 and (r, c) not in border_connected:
                cells[r][c] = colour
                changed = True
    return Grid(cells) if changed else None


def solver_conditional_recolour(grid: Grid, prop: str, op: str, val: Any, outcome: int) -> Grid:
    objs = extract_objects(grid)
    cells = [row[:] for row in grid.cells]
    for obj in objs:
        actual = obj.get(prop)
        if actual is None:
            continue
        match = False
        if op == '>=' and actual >= val: match = True
        elif op == '<=' and actual <= val: match = True
        elif op == '==' and actual == val: match = True
        elif op == '!=' and actual != val: match = True
        if match:
            for r, c in obj['cells']:
                cells[r][c] = outcome
    return Grid(cells)


def solver_colour_swap(grid: Grid, a: int, b: int) -> Grid:
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if cells[r][c] == a:
                cells[r][c] = b
            elif cells[r][c] == b:
                cells[r][c] = a
    return Grid(cells)


def solver_local_colour_swap(grid: Grid) -> Grid:
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    visited = set()
    for r in range(h):
        for c in range(w):
            if (r, c) in visited or grid.cells[r][c] == 0:
                continue
            comp = set()
            queue = [(r, c)]
            while queue:
                cr, cc = queue.pop()
                if (cr, cc) in comp:
                    continue
                comp.add((cr, cc))
                visited.add((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in comp and grid.cells[nr][nc] != 0:
                        queue.append((nr, nc))
            comp_cols = set(grid.cells[rr][cc] for rr, cc in comp)
            if len(comp_cols) == 2:
                cols = sorted(comp_cols)
                for rr, cc in comp:
                    if grid.cells[rr][cc] == cols[0]:
                        cells[rr][cc] = cols[1]
                    elif grid.cells[rr][cc] == cols[1]:
                        cells[rr][cc] = cols[0]
    return Grid(cells)


def solver_column_rank_fill(grid: Grid) -> Optional[Grid]:
    h, w = grid.height, grid.width
    zero_cols = sorted(set(c for r in range(h) for c in range(w) if grid.cells[r][c] == 0))
    if not zero_cols:
        return None
    col_rank = {c: (i % 9) + 1 for i, c in enumerate(zero_cols)}
    cells = [row[:] for row in grid.cells]
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] == 0:
                cells[r][c] = col_rank.get(c, 0)
    return Grid(cells)


def solver_colour_center_fill(grid: Grid) -> Optional[Grid]:
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    last_row = h - 1
    visited = set()
    components = []
    for r in range(last_row):
        for c in range(w):
            if (r, c) in visited or grid.cells[r][c] == 0:
                continue
            colour = grid.cells[r][c]
            comp = set()
            queue = [(r, c)]
            while queue:
                cr, cc = queue.pop()
                if (cr, cc) in comp:
                    continue
                comp.add((cr, cc))
                visited.add((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < last_row and 0 <= nc < w and (nr, nc) not in comp:
                        if grid.cells[nr][nc] == colour:
                            queue.append((nr, nc))
            components.append(comp)
    for comp in components:
        cols = [c for r, c in comp]
        mid = (min(cols) + max(cols)) // 2
        if cells[last_row][mid] == 0:
            cells[last_row][mid] = 4
    return Grid(cells)


# ══════════════════════════════════════════════════════════════════════════════
# SOLVER ROUTER — Uses CRG + concepts to pick solver
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SolverResult:
    solver_name: str
    prediction: Optional[Grid]
    correct: bool
    concepts_used: List[str]


def try_all_solvers(task: ARCTask, concepts: TaskConcepts) -> List[SolverResult]:
    """Try all solvers and return results."""
    results = []
    same_size = not concepts.has_size_change

    if not same_size:
        return results

    # 1. Gravity down
    try:
        pred = solver_gravity_down(task.test[0].input)
        ok = all(solver_gravity_down(p.input) == p.output for p in task.train)
        results.append(SolverResult("gravity_down", pred if ok else None, ok, ["gravity", "spatial"]))
    except:
        pass

    # 2. Fill with learned colour
    if concepts.fill_colours:
        for fc in set(concepts.fill_colours):
            try:
                fn = lambda g, c=fc: solver_fill(g, c)
                ok = all(fn(p.input) == p.output for p in task.train)
                results.append(SolverResult(f"fill_{fc}", fn(task.test[0].input) if ok else None, ok, ["fill", f"colour_{fc}"]))
            except:
                pass

    # 3. Interior fill
    if concepts.fill_colours:
        for fc in set(concepts.fill_colours):
            try:
                fn = lambda g, c=fc: solver_interior_fill(g, c)
                ok = all(fn(p.input) is not None and fn(p.input) == p.output for p in task.train)
                results.append(SolverResult(f"interior_fill_{fc}", fn(task.test[0].input) if ok else None, ok, ["interior", "fill", f"colour_{fc}"]))
            except:
                pass

    # 4. Recolour
    if concepts.recolour_map:
        for fc, tc in concepts.recolour_map.items():
            try:
                fn = lambda g, f=fc, t=tc: solver_recolour(g, f, t)
                ok = all(fn(p.input) == p.output for p in task.train)
                results.append(SolverResult(f"recolour_{fc}_{tc}", fn(task.test[0].input) if ok else None, ok, ["recolour", f"colour_{fc}", f"colour_{tc}"]))
            except:
                pass

    # 5. Conditional recolour (size >= threshold)
    if concepts.object_sizes:
        max_size = max(concepts.object_sizes)
        for threshold in range(2, max_size + 1):
            for outcome in range(1, 10):
                try:
                    fn = lambda g, t=threshold, o=outcome: solver_conditional_recolour(g, 'size', '>=', t, o)
                    ok = all(fn(p.input) == p.output for p in task.train)
                    if ok:
                        results.append(SolverResult(f"cond_recolour_size>={threshold}_{outcome}",
                                                   fn(task.test[0].input), True,
                                                   ["conditional", "recolour", f"size>={threshold}", f"colour_{outcome}"]))
                except:
                    pass

    # 6. Column rank fill
    try:
        fn = solver_column_rank_fill
        ok = all(fn(p.input) is not None and fn(p.input) == p.output for p in task.train)
        results.append(SolverResult("column_rank_fill", fn(task.test[0].input) if ok else None, ok, ["column", "rank", "fill"]))
    except:
        pass

    # 7. Colour center fill
    try:
        fn = solver_colour_center_fill
        ok = all(fn(p.input) is not None and fn(p.input) == p.output for p in task.train)
        results.append(SolverResult("colour_center_fill", fn(task.test[0].input) if ok else None, ok, ["colour", "center", "fill"]))
    except:
        pass

    # 8. Local colour swap
    try:
        fn = solver_local_colour_swap
        ok = all(fn(p.input) == p.output for p in task.train)
        results.append(SolverResult("local_colour_swap", fn(task.test[0].input) if ok else None, ok, ["local", "swap", "colour"]))
    except:
        pass

    # 9. Colour swap (specific pair)
    if concepts.recolour_map and len(concepts.recolour_map) == 2:
        cols = list(concepts.recolour_map.keys())
        if concepts.recolour_map[cols[0]] == cols[1] and concepts.recolour_map[cols[1]] == cols[0]:
            try:
                fn = lambda g, a=cols[0], b=cols[1]: solver_colour_swap(g, a, b)
                ok = all(fn(p.input) == p.output for p in task.train)
                results.append(SolverResult(f"swap_{cols[0]}_{cols[1]}", fn(task.test[0].input) if ok else None, ok, ["swap", f"colour_{cols[0]}", f"colour_{cols[1]}"]))
            except:
                pass

    # 10. Erase
    if concepts.erase_count > 0:
        for ec in set(r for r in concepts.recolour_map.keys()):
            try:
                fn = lambda g, c=ec: solver_erase(g, c)
                ok = all(fn(p.input) == p.output for p in task.train)
                results.append(SolverResult(f"erase_{ec}", fn(task.test[0].input) if ok else None, ok, ["erase", f"colour_{ec}"]))
            except:
                pass

    return results


# ══════════════════════════════════════════════════════════════════════════════
# CONTINUOUS LEARNING LOOP
# ══════════════════════════════════════════════════════════════════════════════

class GLMBridge:
    """Bridge between GLM concept reasoning and grid-level solvers."""

    def __init__(self):
        self.glm = None
        self.learner = None
        self.task_history = []  # List of (task_id, concepts, results)
        self.crg_growth = []    # Track CRG growth over time

    def init(self):
        """Initialize GLM with ARC knowledge."""
        from GLM import GLM
        from GLM24_continuous_learner import ContinuousLearner

        self.glm = GLM()
        self.learner = ContinuousLearner(self.glm.vocab, self.glm.crg)

        # Inject ARC concepts
        self._inject_arc_concepts()

        print(f"[Bridge] GLM initialized. Vocab: {len(self.glm.vocab.words if hasattr(self.glm.vocab, 'words') else self.glm.vocab)}, CRG: {len(self.glm.crg.edges)} edges")

    def _inject_arc_concepts(self):
        """Inject ARC-specific concepts into the GLM vocabulary."""
        from GLM01_substrate import WordEntry, BLA, GOLAY_ENGINE, LEECH_ENGINE, _get_mog_category

        concepts = {
            "grid": {"def": "2D array of integer cells", "role": "NOUN"},
            "cell": {"def": "Single position in grid with colour 0-9", "role": "NOUN"},
            "fill": {"def": "Replace background zeros with colour", "role": "VERB"},
            "erase": {"def": "Replace non-zero with background zero", "role": "VERB"},
            "recolour": {"def": "Change one colour to another", "role": "VERB"},
            "object": {"def": "Connected component of same-colour cells", "role": "NOUN"},
            "interior": {"def": "Enclosed zeros not connected to border", "role": "NOUN"},
            "gravity": {"def": "Move non-zero cells downward", "role": "NOUN"},
            "swap": {"def": "Exchange two colours", "role": "VERB"},
            "propagate": {"def": "Spread colour to adjacent zeros", "role": "VERB"},
            "adjacent": {"def": "Sharing edge (4-neighbour)", "role": "ADJ"},
            "threshold": {"def": "Numeric boundary triggering action", "role": "NOUN"},
            "predicate": {"def": "Test on object property", "role": "NOUN"},
            "conditional": {"def": "Dependent on a condition", "role": "ADJ"},
            "spatial": {"def": "Related to position in grid", "role": "ADJ"},
            "pattern": {"def": "Recurring structure in grid", "role": "NOUN"},
        }

        target = self.glm.vocab.words if hasattr(self.glm.vocab, 'words') else self.glm.vocab
        for concept, data in concepts.items():
            if concept not in target:
                h = hashlib.sha256(concept.encode()).digest()
                seed_bits = [(byte >> k) & 1 for byte in h for k in range(7, -1, -1)][:24]
                snapped, _ = GOLAY_ENGINE.snap_to_codeword(seed_bits)
                nrci = float(LEECH_ENGINE.calculate_nrci(snapped))
                target[concept] = WordEntry(
                    word=concept, vector=snapped, role=data["role"],
                    ubp_id=f"ARC_{concept.upper()}", nrci=nrci,
                    golay_codeword=snapped, fold3=BLA.fold24_to3(snapped),
                    mog_category=_get_mog_category(snapped),
                )

    def process_task(self, task: ARCTask) -> Optional[Tuple[Grid, str]]:
        """Process a task through the full bridge loop.

        1. Extract concepts from the task
        2. Feed concepts into the continuous learner
        3. Try all solvers
        4. Record results
        5. Feed results back into the CRG
        """
        # Step 1: Extract concepts
        concepts = extract_concepts(task)

        # Step 2: Feed into continuous learner
        words = concepts.description.lower().split()
        self.learner.process_query(concepts.description, words)

        # Step 3: Try all solvers
        results = try_all_solvers(task, concepts)

        # Step 4: Record results
        self.task_history.append((task.name, concepts, results))

        # Step 5: Feed results back into CRG
        self._update_crg(concepts, results)

        # Return best result
        for r in results:
            if r.correct and r.prediction is not None:
                return r.prediction, f"bridge:{r.solver_name}"

        return None

    def _update_crg(self, concepts: TaskConcepts, results: List[SolverResult]):
        """Update CRG based on solver results."""
        # Reinforce edges for successful solvers
        for r in results:
            if r.correct:
                # Create edges between concepts used by successful solver
                for i, c1 in enumerate(r.concepts_used):
                    for c2 in r.concepts_used[i+1:]:
                        self.learner.state.cooccurrence[c1][c2] += 5  # Strong reinforcement
                        self.learner.state.cooccurrence[c2][c1] += 5

                # Create edge: task_category → solver_name
                self.learner.state.cooccurrence[concepts.category][r.solver_name] += 10

                # Create edge: fill_count → solver_name
                if concepts.fill_count > 0:
                    self.learner.state.cooccurrence[f"fill_{concepts.fill_count}"][r.solver_name] += 5

        # Record negative evidence (weak reinforcement for failed concepts)
        for r in results:
            if not r.correct:
                for c in r.concepts_used:
                    self.learner.state.cooccurrence[f"failed_{c}"][r.solver_name] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get bridge statistics."""
        total_tasks = len(self.task_history)
        solved = sum(1 for _, _, results in self.task_history if any(r.correct for r in results))

        solver_success = Counter()
        for _, _, results in self.task_history:
            for r in results:
                if r.correct:
                    solver_success[r.solver_name] += 1

        return {
            "total_tasks": total_tasks,
            "solved": solved,
            "solver_success": dict(solver_success),
            "crg_edges": len(self.glm.crg.edges) if self.glm else 0,
            "learned_edges": len(self.learner.state.learned_edges) if self.learner else 0,
            "learned_words": len(self.learner.state.learned_words) if self.learner else 0,
            "query_count": self.learner.state.query_count if self.learner else 0,
        }

    def save(self):
        """Save learned state."""
        if self.learner:
            self.learner.state.save()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--save-state", action="store_true")
    args = p.parse_args()

    print("═" * 60)
    print(" GLM ↔ GRID BRIDGE v058 — Continuous Learning")
    print("═" * 60)
    print()

    bridge = GLMBridge()
    bridge.init()

    files = sorted(f for f in os.listdir(args.batch) if f.endswith('.json'))

    solved = total = 0
    sources = {}
    all_results = []

    for fname in files:
        task = load_task(os.path.join(args.batch, fname), name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1

        try:
            signal.setitimer(signal.ITIMER_REAL, 30.0)
            result = bridge.process_task(task)
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

    # Save state
    if args.save_state:
        bridge.save()
        print(f"\n[Bridge] State saved.")

    # Print stats
    stats = bridge.get_stats()
    print(f"\n{'═' * 60}")
    print(f" RESULTS ({total} tasks)")
    print(f"{'═' * 60}")
    print(f"  SOLVED: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"\n  Solvers:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        if src != "none":
            print(f"    {src}: {count}")
    print(f"\n  CRG Growth:")
    print(f"    Edges: {stats['crg_edges']}")
    print(f"    Learned edges: {stats['learned_edges']}")
    print(f"    Learned words: {stats['learned_words']}")
    print(f"    Queries processed: {stats['query_count']}")

    print(f"\n  Solved tasks:")
    for tid, ok, src in all_results:
        if ok:
            print(f"    {tid} ← {src}")
