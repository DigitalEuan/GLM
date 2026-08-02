"""
v044_disruption.py — The Perturbation Lens
=============================================

Instead of asking "what rule transforms input to output?",
ask "how does the input perturb the substrate, and what
does the perturbed state look like?"

The input is a DISRUPTION to the UBP system's equilibrium.
The output is what the system looks like AFTER the disruption
propagates and the system re-settles.

This connects to:
- LAW_PATTERN_001: "Visual puzzles are coherence maps"
- LAW_TOPOLOGICAL_ERASURE_001: "The substrate prioritizes
  geometric stability over conservation of magnitude"
- LAW_OPTICAL_TOGGLE_001: "Light propagates via a
  neighbor-dependent toggle rule"

The disruption perspective:
1. The grid is a FIELD of perturbations (each non-zero cell
   disrupts the background)
2. Disruptions PROPAGATE through the substrate (neighbour-dependent)
3. The output is the EQUILIBRIUM state after propagation
4. The propagation rule is what we need to discover

Implementation:
- For each cell, compute its "disruption signature" (how it
  differs from the background equilibrium)
- Track how disruptions propagate through the grid
- The output is the re-settled state
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter
import sys, os, signal
import numpy as np

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
# 1. DISRUPTION FIELD
# ═══════════════════════════════════════════════════════════════════

def compute_disruption_field(grid: Grid, bg_colour: int = 0) -> np.ndarray:
    """
    Compute the disruption field: how much each cell differs
    from the background equilibrium.
    
    Disruption = 0 for background cells
    Disruption = colour value for non-background cells
    
    This is the PERTURBATION to the substrate.
    """
    h, w = grid.height, grid.width
    field = np.zeros((h, w))
    
    for r in range(h):
        for c in range(w):
            if grid.cells[r][c] != bg_colour:
                field[r, c] = grid.cells[r][c]
    
    return field


def compute_disruption_gradient(field: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the disruption gradient: how the disruption
    changes across the grid.
    
    This shows where disruptions are STRONGEST and where
    they're SPREADING.
    """
    # Gradient in row and column directions
    grad_r = np.diff(field, axis=0, prepend=field[0:1, :])
    grad_c = np.diff(field, axis=1, prepend=field[:, 0:1])
    
    return grad_r, grad_c


# ═══════════════════════════════════════════════════════════════════
# 2. DISRUPTION PROPAGATION
# ═══════════════════════════════════════════════════════════════════

def propagate_disruption(grid: Grid, steps: int = 1) -> Grid:
    """
    Simulate disruption propagation: non-zero cells
    "push" their colour into adjacent zero cells.
    
    This is the LAW_OPTICAL_TOGGLE_001 principle:
    "Light propagates via a neighbor-dependent toggle rule."
    
    After N steps, the grid reaches a new equilibrium.
    """
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    
    for step in range(steps):
        new_cells = [row[:] for row in cells]
        changed = False
        
        for r in range(h):
            for c in range(w):
                if cells[r][c] == 0:
                    # Collect neighbour colours
                    n_cols = []
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] != 0:
                            n_cols.append(cells[nr][nc])
                    
                    if len(n_cols) == 1:
                        new_cells[r][c] = n_cols[0]
                        changed = True
                    elif len(n_cols) > 1:
                        # Majority vote
                        new_cells[r][c] = Counter(n_cols).most_common(1)[0][0]
                        changed = True
        
        cells = new_cells
        if not changed:
            break
    
    return Grid(cells)


def propagate_disruption_selective(grid: Grid, 
                                     propagate_colours: List[int],
                                     steps: int = 1) -> Grid:
    """
    Selective propagation: only specific colours propagate.
    
    This models the idea that not all disruptions propagate
    equally — some colours are "louder" than others.
    """
    h, w = grid.height, grid.width
    cells = [row[:] for row in grid.cells]
    
    for step in range(steps):
        new_cells = [row[:] for row in cells]
        changed = False
        
        for r in range(h):
            for c in range(w):
                if cells[r][c] == 0:
                    n_cols = []
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w and cells[nr][nc] in propagate_colours:
                            n_cols.append(cells[nr][nc])
                    
                    if len(n_cols) == 1:
                        new_cells[r][c] = n_cols[0]
                        changed = True
                    elif len(n_cols) > 1:
                        new_cells[r][c] = Counter(n_cols).most_common(1)[0][0]
                        changed = True
        
        cells = new_cells
        if not changed:
            break
    
    return Grid(cells)


# ═══════════════════════════════════════════════════════════════════
# 3. DISRUPTION EQUILIBRIUM
# ═══════════════════════════════════════════════════════════════════

def find_equilibrium(grid: Grid, max_steps: int = 10) -> Tuple[Grid, int]:
    """
    Find the equilibrium state: propagate disruptions until
    the grid stops changing.
    
    Returns: (equilibrium_grid, steps_to_equilibrium)
    """
    for steps in range(1, max_steps + 1):
        result = propagate_disruption(grid, steps=1)
        if grids_equal(result, grid):
            return grid, steps - 1
        grid = result
    
    return grid, max_steps


# ═══════════════════════════════════════════════════════════════════
# 4. DISRUPTION ANALYSIS
# ═══════════════════════════════════════════════════════════════════

def analyse_disruption(input_grid: Grid, output_grid: Grid) -> Dict[str, Any]:
    """
    Analyse the disruption pattern: what changed between
    input and output, and how does it relate to propagation?
    """
    h, w = input_grid.height, input_grid.width
    
    # Count disruption types
    zero_to_nonzero = 0
    nonzero_to_nonzero = 0
    nonzero_to_zero = 0
    
    for r in range(h):
        for c in range(w):
            ic, oc = input_grid.cells[r][c], output_grid.cells[r][c]
            if ic == 0 and oc != 0:
                zero_to_nonzero += 1
            elif ic != 0 and oc != ic:
                nonzero_to_nonzero += 1
            elif ic != 0 and oc == 0:
                nonzero_to_zero += 1
    
    # Check if output matches propagation
    propagated = propagate_disruption(input_grid, steps=1)
    propagation_match = grids_equal(propagated, output_grid)
    
    # Check multi-step propagation
    for steps in range(2, 6):
        prop_n = propagate_disruption(input_grid, steps=steps)
        if grids_equal(prop_n, output_grid):
            return {
                'type': 'propagation',
                'steps': steps,
                'zero_to_nonzero': zero_to_nonzero,
                'nonzero_to_nonzero': nonzero_to_nonzero,
                'nonzero_to_zero': nonzero_to_zero,
            }
    
    # Check selective propagation
    all_cols = set(input_grid.cells[r][c] for r in range(h) for c in range(w))
    for col in all_cols:
        if col == 0:
            continue
        prop_sel = propagate_disruption_selective(input_grid, [col], steps=1)
        if grids_equal(prop_sel, output_grid):
            return {
                'type': 'selective_propagation',
                'propagate_col': col,
                'steps': 1,
            }
    
    return {
        'type': 'unknown',
        'zero_to_nonzero': zero_to_nonzero,
        'nonzero_to_nonzero': nonzero_to_nonzero,
        'nonzero_to_zero': nonzero_to_zero,
        'propagation_match': propagation_match,
    }


# ═══════════════════════════════════════════════════════════════════
# 5. PREDICTION: DISRUPTION-BASED
# ═══════════════════════════════════════════════════════════════════

def predict(task: ARCTask) -> Optional[Tuple[Grid, str, Dict]]:
    """
    Predict using the disruption lens.
    
    Try: propagate disruptions until equilibrium.
    """
    # Check same-size
    for pair in task.train:
        if pair.input.height != pair.output.height or pair.input.width != pair.output.width:
            return None
    
    # Analyse disruption pattern in train pairs
    disruption_types = []
    for pair in task.train:
        analysis = analyse_disruption(pair.input, pair.output)
        disruption_types.append(analysis['type'])
    
    # Check if all pairs have the same disruption type
    if len(set(disruption_types)) == 1:
        dtype = disruption_types[0]
        
        if dtype == 'propagation':
            # Find the number of steps
            for pair in task.train:
                for steps in range(1, 10):
                    prop = propagate_disruption(pair.input, steps=steps)
                    if grids_equal(prop, pair.output):
                        # Verify on all pairs
                        all_pass = True
                        for p in task.train:
                            if not grids_equal(propagate_disruption(p.input, steps=steps), p.output):
                                all_pass = False
                                break
                        
                        if all_pass:
                            test_input = task.test[0].input
                            pred = propagate_disruption(test_input, steps=steps)
                            return pred, f"disrupt_prop_{steps}", {'steps': steps}
                        break
        
        elif dtype == 'selective_propagation':
            # Find which colour propagates
            for pair in task.train:
                analysis = analyse_disruption(pair.input, pair.output)
                if 'propagate_col' in analysis:
                    col = analysis['propagate_col']
                    # Verify
                    all_pass = True
                    for p in task.train:
                        if not grids_equal(propagate_disruption_selective(p.input, [col], steps=1), p.output):
                            all_pass = False
                            break
                    
                    if all_pass:
                        test_input = task.test[0].input
                        pred = propagate_disruption_selective(test_input, [col], steps=1)
                        return pred, f"disrupt_sel_{col}", {'col': col}
    
    # Try: equilibrium state
    for pair in task.train:
        eq, steps = find_equilibrium(pair.input)
        if grids_equal(eq, pair.output):
            # Verify
            all_pass = True
            for p in task.train:
                eq_n, _ = find_equilibrium(p.input)
                if not grids_equal(eq_n, p.output):
                    all_pass = False
                    break
            
            if all_pass:
                test_input = task.test[0].input
                pred, _ = find_equilibrium(test_input)
                return pred, f"disrupt_eq_{steps}", {'steps': steps}
    
    return None


if __name__ == "__main__":
    # First, show disruption analysis for all tasks
    print("═" * 60)
    print(" DISRUPTION ANALYSIS — How data perturbs the system")
    print("═" * 60)
    print()
    
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
    type_counts = Counter()
    
    for fname in files:
        task = load_task(os.path.join(args.batch, fname),
                         name=os.path.splitext(fname)[0])
        if task.test[0].expected_output is None:
            continue
        total += 1
        
        # Analyse first train pair
        analysis = analyse_disruption(task.train[0].input, task.train[0].output)
        dtype = analysis['type']
        type_counts[dtype] += 1
        
        if args.verbose:
            tid = os.path.splitext(fname)[0]
            z2n = analysis.get('zero_to_nonzero', 0)
            n2n = analysis.get('nonzero_to_nonzero', 0)
            n2z = analysis.get('nonzero_to_zero', 0)
            print(f"  {tid}: {dtype:25s} z→n={z2n:3d} n→n={n2n:3d} n→z={n2z:3d}")
        
        # Try prediction
        try:
            signal.setitimer(signal.ITIMER_REAL, 10.0)
            result = predict(task)
            signal.setitimer(signal.ITIMER_REAL, 0)
        except:
            signal.setitimer(signal.ITIMER_REAL, 0)
            result = None
        
        if result is not None:
            pred, src, diag = result
            ok = (pred == task.test[0].expected_output)
            if ok:
                solved += 1
            sources[src] = sources.get(src, 0) + 1
            if ok:
                print(f"  ★ {os.path.splitext(fname)[0]}: SOLVED by {src}")
    
    print()
    print(f"Disruption types across {total} tasks:")
    for dtype, count in type_counts.most_common():
        print(f"  {dtype}: {count}")
    
    print()
    print(f"═══ Disruption Prediction ({total} tasks) ═══")
    print(f"  Solved: {solved}/{total} ({solved / max(total, 1):.1%})")
    print(f"  Sources: {sources}")
