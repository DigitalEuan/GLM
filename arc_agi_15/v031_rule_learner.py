"""
v031_rule_learner.py — General rule discovery for ARC tasks
============================================================

Discovers conditional transformation rules from train pairs.

Approach:
1. For each cell (r, c) in train pairs where input != output:
   - Extract features: input colour, position, neighbours, object membership, etc.
   - Record the transformation (input → output)
2. Find the simplest rule that explains ALL transformations
3. Apply the rule to test input

Rule types (in order of simplicity):
1. GLOBAL_FILL: all zeros → colour X
2. CONDITIONAL_FILL: zeros adjacent to colour X → colour Y
3. COLUMN_FILL: column C fills with colour X
4. ROW_FILL: row R fills with colour X
5. NEIGHBOUR_RULE: cell with neighbour colour X in direction D → colour Y
6. POSITION_RULE: cell at (r%R, c%C) with colour X → colour Y
7. OBJECT_BOUNDARY: cells on boundary of objects → colour X
8. CONNECT: fill path between two objects
9. SPREAD_FROM_SEED: non-zero cells spread to adjacent zeros
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any, Set, Callable
from collections import Counter, defaultdict, deque
import sys, os, signal, itertools

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from arc_loader import Grid, ARCTask, load_task


class _OpTimeout(Exception):
    pass

def _alarm_handler(s, f):
    raise _OpTimeout()

signal.signal(signal.SIGALRM, _alarm_handler)


def grids_equal(g1: Grid, g2: Grid) -> bool:
    if g1.height != g2.height or g1.width != g2.width:
        return False
    return all(g1.cells[r][c] == g2.cells[r][c]
               for r in range(g1.height) for c in range(g1.width))


# ═══════════════════════════════════════════════════════════════════
# FEATURE EXTRACTION
# ═══════════════════════════════════════════════════════════════════

def extract_cell_features(grid: Grid, r: int, c: int) -> Dict[str, Any]:
    """Extract all features of a cell for rule learning."""
    h, w = grid.height, grid.width
    ic = grid.cells[r][c]
    
    # Neighbours (4-connected)
    n4 = {}
    for dr, dc, name in [(-1,0,'N'), (1,0,'S'), (0,-1,'W'), (0,1,'E')]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < h and 0 <= nc < w:
            n4[name] = grid.cells[nr][nc]
        else:
            n4[name] = -1  # boundary
    
    # Neighbours (8-connected)
    n8 = {}
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            name = f'd{dr+1}{dc+1}'
            nr, nc = r+dr, c+dc
            if 0 <= nr < h and 0 <= nc < w:
                n8[name] = grid.cells[nr][nc]
            else:
                n8[name] = -1
    
    # Neighbour counts
    n_nonzero_4 = sum(1 for v in n4.values() if v > 0)
    n_nonzero_8 = sum(1 for v in n8.values() if v > 0)
    
    # Distinct neighbour colours (4-connected)
    neighbour_cols_4 = set(v for v in n4.values() if v > 0)
    neighbour_cols_8 = set(v for v in n8.values() if v > 0)
    
    # Position features
    is_border = (r == 0 or r == h-1 or c == 0 or c == w-1)
    is_corner = (r in (0, h-1) and c in (0, w-1))
    
    # Distance to nearest non-zero cell
    min_dist_to_nonzero = float('inf')
    for dr in range(-3, 4):
        for dc in range(-3, 4):
            nr, nc = r+dr, c+dc
            if 0 <= nr < h and 0 <= nc < w and grid.cells[nr][nc] != 0:
                min_dist_to_nonzero = min(min_dist_to_nonzero, abs(dr)+abs(dc))
    if min_dist_to_nonzero == float('inf'):
        min_dist_to_nonzero = -1
    
    return {
        'colour': ic,
        'r': r, 'c': c,
        'r_mod2': r % 2, 'c_mod2': c % 2,
        'r_mod3': r % 3, 'c_mod3': c % 3,
        'is_border': is_border,
        'is_corner': is_corner,
        'n_nonzero_4': n_nonzero_4,
        'n_nonzero_8': n_nonzero_8,
        'neighbour_cols_4': frozenset(neighbour_cols_4),
        'neighbour_cols_8': frozenset(neighbour_cols_8),
        'n4': n4,
        'n8': n8,
        'min_dist_to_nonzero': min_dist_to_nonzero,
    }


# ═══════════════════════════════════════════════════════════════════
# RULE TYPES
# ═══════════════════════════════════════════════════════════════════

class Rule:
    """Base class for transformation rules."""
    def applies(self, features: Dict) -> bool:
        raise NotImplementedError
    def apply(self, features: Dict) -> Optional[int]:
        raise NotImplementedError
    def __repr__(self):
        return self.__class__.__name__


class GlobalFillRule(Rule):
    """All zeros become colour X."""
    def __init__(self, colour: int):
        self.colour = colour
    def applies(self, features: Dict) -> bool:
        return features['colour'] == 0
    def apply(self, features: Dict) -> Optional[int]:
        if features['colour'] == 0:
            return self.colour
        return None
    def __repr__(self):
        return f'GlobalFill({self.colour})'


class ConditionalFillRule(Rule):
    """Zeros with neighbour colour X in direction D become colour Y."""
    def __init__(self, neighbour_colour: int, direction: str, fill_colour: int):
        self.neighbour_colour = neighbour_colour
        self.direction = direction
        self.fill_colour = fill_colour
    def applies(self, features: Dict) -> bool:
        if features['colour'] != 0:
            return False
        return features['n4'].get(self.direction, -1) == self.neighbour_colour
    def apply(self, features: Dict) -> Optional[int]:
        if self.applies(features):
            return self.fill_colour
        return None
    def __repr__(self):
        return f'CondFill(neighbour={self.neighbour_colour} in {self.direction} → {self.fill_colour})'


class ColourTransformRule(Rule):
    """All cells of colour X become colour Y."""
    def __init__(self, from_colour: int, to_colour: int):
        self.from_colour = from_colour
        self.to_colour = to_colour
    def applies(self, features: Dict) -> bool:
        return features['colour'] == self.from_colour
    def apply(self, features: Dict) -> Optional[int]:
        if features['colour'] == self.from_colour:
            return self.to_colour
        return None
    def __repr__(self):
        return f'ColourTransform({self.from_colour}→{self.to_colour})'


class NeighbourCountRule(Rule):
    """Cells of colour X with exactly N non-zero neighbours become colour Y."""
    def __init__(self, from_colour: int, n_neighbours: int, to_colour: int):
        self.from_colour = from_colour
        self.n_neighbours = n_neighbours
        self.to_colour = to_colour
    def applies(self, features: Dict) -> bool:
        return (features['colour'] == self.from_colour and 
                features['n_nonzero_4'] == self.n_neighbours)
    def apply(self, features: Dict) -> Optional[int]:
        if self.applies(features):
            return self.to_colour
        return None
    def __repr__(self):
        return f'NeighbourCount({self.from_colour}, n={self.n_neighbours}→{self.to_colour})'


class HasNeighbourRule(Rule):
    """Zeros adjacent (4-connected) to colour X become colour Y."""
    def __init__(self, neighbour_colour: int, fill_colour: int):
        self.neighbour_colour = neighbour_colour
        self.fill_colour = fill_colour
    def applies(self, features: Dict) -> bool:
        return (features['colour'] == 0 and 
                self.neighbour_colour in features['neighbour_cols_4'])
    def apply(self, features: Dict) -> Optional[int]:
        if self.applies(features):
            return self.fill_colour
        return None
    def __repr__(self):
        return f'HasNeighbour({self.neighbour_colour}→{self.fill_colour})'


class SpreadRule(Rule):
    """Non-zero cells stay; zeros adjacent to non-zero become that colour."""
    def applies(self, features: Dict) -> bool:
        if features['colour'] != 0:
            return True  # Keep non-zero
        # Check if adjacent to a single non-zero colour
        cols = features['neighbour_cols_4']
        return len(cols) == 1
    def apply(self, features: Dict) -> Optional[int]:
        if features['colour'] != 0:
            return features['colour']  # Keep
        cols = features['neighbour_cols_4']
        if len(cols) == 1:
            return list(cols)[0]
        return None
    def __repr__(self):
        return 'SpreadRule'


# ═══════════════════════════════════════════════════════════════════
# RULE LEARNER
# ═══════════════════════════════════════════════════════════════════

def learn_rules(task: ARCTask) -> List[Rule]:
    """Learn transformation rules from train pairs."""
    
    # Collect all (features, output_colour) pairs
    observations = []
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return []  # Can't handle size changes yet
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                ic = pair.input.cells[r][c]
                oc = pair.output.cells[r][c]
                if ic != oc:
                    features = extract_cell_features(pair.input, r, c)
                    observations.append((features, oc))
    
    if not observations:
        return []
    
    # Try rules in order of simplicity
    
    # 1. Global fill: all zeros → same colour
    fill_colours = Counter()
    for features, oc in observations:
        if features['colour'] == 0:
            fill_colours[oc] += 1
    if fill_colours:
        most_common_fill = fill_colours.most_common(1)[0]
        # Check if ALL zero→nonzero transitions use this colour
        all_same = all(oc == most_common_fill[0] for f, oc in observations if f['colour'] == 0)
        nonzero_changes = [(f, oc) for f, oc in observations if f['colour'] != 0]
        if all_same and not nonzero_changes:
            return [GlobalFillRule(most_common_fill[0])]
    
    # 2. Colour transform: all X → Y
    colour_transitions = Counter()
    for features, oc in observations:
        colour_transitions[(features['colour'], oc)] += 1
    
    # Check for consistent single-colour transform
    for (from_c, to_c), count in colour_transitions.most_common():
        # Check if ALL cells of from_c become to_c
        all_from_c_transform = True
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] == from_c and pair.output.cells[r][c] != to_c:
                        if pair.output.cells[r][c] != from_c:  # Not identity
                            all_from_c_transform = False
                            break
                if not all_from_c_transform:
                    break
            if not all_from_c_transform:
                break
        if all_from_c_transform and from_c != to_c:
            # Check if this explains ALL observations
            remaining = [(f, oc) for f, oc in observations if f['colour'] != from_c]
            if not remaining:
                return [ColourTransformRule(from_c, to_c)]
    
    # 3. HasNeighbour: zeros adjacent to X → Y
    for neighbour_col in set(f['colour'] for f, _ in observations if f['colour'] != 0):
        neighbour_fills = Counter()
        for features, oc in observations:
            if features['colour'] == 0 and neighbour_col in features['neighbour_cols_4']:
                neighbour_fills[oc] += 1
        if neighbour_fills:
            most_common = neighbour_fills.most_common(1)[0]
            # Check consistency
            consistent = all(oc == most_common[0] 
                           for f, oc in observations 
                           if f['colour'] == 0 and neighbour_col in f['neighbour_cols_4'])
            if consistent:
                remaining = [(f, oc) for f, oc in observations 
                           if not (f['colour'] == 0 and neighbour_col in f['neighbour_cols_4'])]
                if not remaining:
                    return [HasNeighbourRule(neighbour_col, most_common[0])]
    
    # 4. Conditional fill: zeros in direction D from colour X → Y
    for direction in ['N', 'S', 'W', 'E']:
        for neighbour_col in set(f['n4'].get(direction, -1) for f, _ in observations):
            if neighbour_col <= 0:
                continue
            dir_fills = Counter()
            for features, oc in observations:
                if features['colour'] == 0 and features['n4'].get(direction) == neighbour_col:
                    dir_fills[oc] += 1
            if dir_fills:
                most_common = dir_fills.most_common(1)[0]
                consistent = all(oc == most_common[0]
                               for f, oc in observations
                               if f['colour'] == 0 and f['n4'].get(direction) == neighbour_col)
                if consistent:
                    remaining = [(f, oc) for f, oc in observations
                               if not (f['colour'] == 0 and f['n4'].get(direction) == neighbour_col)]
                    if not remaining:
                        return [ConditionalFillRule(neighbour_col, direction, most_common[0])]
    
    # 5. Multi-colour: different input colours → different output colours
    # Check if it's a simple mapping (each input colour maps to one output colour)
    colour_map = {}
    for features, oc in observations:
        ic = features['colour']
        if ic in colour_map:
            if colour_map[ic] != oc:
                colour_map = None
                break
        else:
            colour_map[ic] = oc
    if colour_map and all(k != v for k, v in colour_map.items()):
        rules = [ColourTransformRule(k, v) for k, v in colour_map.items()]
        # Verify on all train pairs
        all_pass = True
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            for r in range(h):
                for c in range(w):
                    ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                    if ic in colour_map and colour_map[ic] != oc:
                        all_pass = False
                        break
                if not all_pass:
                    break
            if not all_pass:
                break
        if all_pass:
            return rules
    
    # 6. Spread: non-zero cells spread to adjacent zeros
    # Check if output = input after 1-step spread
    spread_works = True
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        cells = [row[:] for row in pair.input.cells]
        # 1-step spread
        new_cells = [row[:] for row in cells]
        for r in range(h):
            for c in range(w):
                if cells[r][c] == 0:
                    neighbour_cols = []
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] != 0:
                            neighbour_cols.append(cells[nr][nc])
                    if len(neighbour_cols) == 1:
                        new_cells[r][c] = neighbour_cols[0]
                    elif len(neighbour_cols) > 1:
                        new_cells[r][c] = Counter(neighbour_cols).most_common(1)[0][0]
        if Grid(new_cells) != pair.output:
            spread_works = False
            break
    if spread_works:
        return [SpreadRule()]
    
    return []


# ═══════════════════════════════════════════════════════════════════
# RULE APPLICATION
# ═══════════════════════════════════════════════════════════════════

def apply_rules(rules: List[Rule], grid: Grid) -> Grid:
    """Apply learned rules to a grid."""
    h, w = grid.height, grid.width
    new_cells = []
    for r in range(h):
        row = []
        for c in range(w):
            features = extract_cell_features(grid, r, c)
            new_val = None
            for rule in rules:
                result = rule.apply(features)
                if result is not None:
                    new_val = result
                    break
            row.append(new_val if new_val is not None else grid.cells[r][c])
        new_cells.append(row)
    return Grid(new_cells)


def predict_with_rules(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Learn rules from train pairs and apply to test."""
    rules = learn_rules(task)
    if not rules:
        return None
    
    test_input = task.test[0].input
    pred = apply_rules(rules, test_input)
    
    # Verify on train
    for pair in task.train:
        train_pred = apply_rules(rules, pair.input)
        if train_pred != pair.output:
            return None
    
    rule_desc = ', '.join(str(r) for r in rules)
    return pred, f'rules[{rule_desc}]', {'rules': [str(r) for r in rules]}


# ═══════════════════════════════════════════════════════════════════
# ENHANCED: Multi-step spread with iteration
# ═══════════════════════════════════════════════════════════════════

def try_iterative_spread(task: ARCTask, max_steps: int = 5) -> Optional[Tuple[Grid, str]]:
    """Try spreading non-zero cells iteratively until output matches."""
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Find the number of spread steps needed
    for steps in range(1, max_steps + 1):
        all_pass = True
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            cells = [row[:] for row in pair.input.cells]
            for step in range(steps):
                new_cells = [row[:] for row in cells]
                changed = False
                for r in range(h):
                    for c in range(w):
                        if cells[r][c] == 0:
                            neighbour_cols = []
                            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                                nr, nc = r+dr, c+dc
                                if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] != 0:
                                    neighbour_cols.append(cells[nr][nc])
                            if len(neighbour_cols) == 1:
                                new_cells[r][c] = neighbour_cols[0]
                                changed = True
                            elif len(neighbour_cols) > 1:
                                new_cells[r][c] = Counter(neighbour_cols).most_common(1)[0][0]
                                changed = True
                cells = new_cells
                if not changed:
                    break
            if not grids_equal(Grid(cells), pair.output):
                all_pass = False
                break
        
        if all_pass:
            # Apply to test
            test_input = task.test[0].input
            h, w = test_input.height, test_input.width
            cells = [row[:] for row in test_input.cells]
            for step in range(steps):
                new_cells = [row[:] for row in cells]
                for r in range(h):
                    for c in range(w):
                        if cells[r][c] == 0:
                            neighbour_cols = []
                            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                                nr, nc = r+dr, c+dc
                                if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] != 0:
                                    neighbour_cols.append(cells[nr][nc])
                            if len(neighbour_cols) == 1:
                                new_cells[r][c] = neighbour_cols[0]
                            elif len(neighbour_cols) > 1:
                                new_cells[r][c] = Counter(neighbour_cols).most_common(1)[0][0]
                cells = new_cells
            return Grid(cells), f'iterative_spread_{steps}'
    
    return None


# ═══════════════════════════════════════════════════════════════════
# ENHANCED: Spread with seed preservation
# ═══════════════════════════════════════════════════════════════════

def try_seed_spread(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Non-zero cells spread to adjacent zeros, but original non-zero cells 
    may change colour based on a separate rule.
    """
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # First, learn what happens to non-zero cells
    nonzero_rule = {}
    for pair in task.train:
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                ic, oc = pair.input.cells[r][c], pair.output.cells[r][c]
                if ic != 0 and ic != oc:
                    if ic in nonzero_rule and nonzero_rule[ic] != oc:
                        return None  # Inconsistent
                    nonzero_rule[ic] = oc
    
    # Check if spreading + recolouring works
    for steps in [1, 2, 3]:
        all_pass = True
        for pair in task.train:
            h, w = pair.input.height, pair.input.width
            cells = [row[:] for row in pair.input.cells]
            
            # Apply non-zero recolour first
            for r in range(h):
                for c in range(w):
                    if cells[r][c] in nonzero_rule:
                        cells[r][c] = nonzero_rule[cells[r][c]]
            
            # Then spread
            for step in range(steps):
                new_cells = [row[:] for row in cells]
                for r in range(h):
                    for c in range(w):
                        if cells[r][c] == 0:
                            neighbour_cols = []
                            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                                nr, nc = r+dr, c+dc
                                if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] != 0:
                                    neighbour_cols.append(cells[nr][nc])
                            if len(neighbour_cols) == 1:
                                new_cells[r][c] = neighbour_cols[0]
                            elif len(neighbour_cols) > 1:
                                new_cells[r][c] = Counter(neighbour_cols).most_common(1)[0][0]
                cells = new_cells
            
            if not grids_equal(Grid(cells), pair.output):
                all_pass = False
                break
        
        if all_pass:
            test_input = task.test[0].input
            h, w = test_input.height, test_input.width
            cells = [row[:] for row in test_input.cells]
            for r in range(h):
                for c in range(w):
                    if cells[r][c] in nonzero_rule:
                        cells[r][c] = nonzero_rule[cells[r][c]]
            for step in range(steps):
                new_cells = [row[:] for row in cells]
                for r in range(h):
                    for c in range(w):
                        if cells[r][c] == 0:
                            neighbour_cols = []
                            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                                nr, nc = r+dr, c+dc
                                if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] != 0:
                                    neighbour_cols.append(cells[nr][nc])
                            if len(neighbour_cols) == 1:
                                new_cells[r][c] = neighbour_cols[0]
                            elif len(neighbour_cols) > 1:
                                new_cells[r][c] = Counter(neighbour_cols).most_common(1)[0][0]
                cells = new_cells
            return Grid(cells), f'seed_spread_{steps}'
    
    return None


# ═══════════════════════════════════════════════════════════════════
# MAIN PREDICTOR
# ═══════════════════════════════════════════════════════════════════

def predict(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """Try all rule-based strategies."""
    strategies = [
        ("rules", predict_with_rules),
        ("iterative_spread", lambda t: try_iterative_spread(t)),
        ("seed_spread", lambda t: try_seed_spread(t)),
    ]
    
    for name, fn in strategies:
        try:
            result = fn(task)
            if result is not None:
                if len(result) == 3:
                    return result
                pred, src = result
                return pred, src, {"strategy": name}
        except Exception:
            continue
    
    return None


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--batch", default="data/training")
    p.add_argument("--max-tasks", type=int, default=None)
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()
    
    files = sorted(f for f in os.listdir(args.batch) if f.endswith(".json"))
    if args.max_tasks:
        files = files[:args.max_tasks]
    
    solved = total = 0
    sources = {}
    
    for fname in files:
        task = load_task(os.path.join(args.batch, fname),
                         name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1
        
        result = predict(task)
        if result is not None:
            pred, src, diag = result
            ok = (pred == task.test[0].expected_output)
            if ok:
                solved += 1
            sources[src] = sources.get(src, 0) + 1
            if args.verbose or ok:
                print(f"  {fname}: {'OK' if ok else 'X'} src={src}")
        else:
            sources["none"] = sources.get("none", 0) + 1
            if args.verbose:
                print(f"  {fname}: X src=none")
    
    print(f"\n═══ Rule Learner ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources: {sources}")
