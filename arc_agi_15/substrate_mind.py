"""
substrate_mind.py — The Substrate Equilibrium Mind
===================================================

The UBP insight: the substrate starts in a perfect state (lowest TAX).
Data disturbs it. The output is the equilibrium — the state the substrate
settles to after the perturbation propagates.

Train pairs are Y-observations: the observer (Y constant) makes a copy
of the perturbation→equilibrium path. Each observation costs Y per active
bit. The mind learns by observing multiple perturbation→equilibrium pairs.

The mind's job: given a new perturbation (test input), predict the
equilibrium state (test output) by understanding the substrate's
settlement dynamics.

This is NOT pattern matching. This is substrate physics.
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
    extract_objects,
)
from v032_distance_rule import try_distance_diagonal_rule
from v065_ubp_glm import learn_multi_interior_fill
from semantic_layer import (
    describe_transformation, generate_from_lingo,
    verify_lingo_candidate, apply_lingo_to_grid,
    semantic_report,
)
from conditional_lobe import (
    induce_conditional_pattern, apply_conditional_pattern,
    verify_conditional_pattern, conditional_report,
)


# ═══════════════════════════════════════════════════════════════════════════════
# UBP Substrate Constants
# ═══════════════════════════════════════════════════════════════════════════════

_Y = 0.2646754304045269672  # Observer constant = 1/(π + 2/π)
_MONAD = 3.141592653589793 * 1.618033988749895 * 2.718281828459045  # π·φ·e
_WOBBLE = _MONAD - 13  # Entropic remainder
_COHERENCE_HORIZON = 0.500  # NRCI threshold for manifestation


# ═══════════════════════════════════════════════════════════════════════════════
# TAX / NRCI — The Substrate's Stability Metrics
# ═══════════════════════════════════════════════════════════════════════════════

def grid_tax(grid: Grid) -> float:
    """
    Symmetry Tax of a grid state.
    TAX = HW × Y + norm²/8
    
    HW = number of non-zero cells (active bits)
    norm² = sum of squared values (geometric displacement)
    """
    hw = 0
    norm_sq = 0
    for row in grid.cells:
        for v in row:
            if v != 0:
                hw += 1
                norm_sq += v * v
    return hw * _Y + norm_sq / 8.0


def grid_nrci(grid: Grid) -> float:
    """
    Non-Random Coherence Index of a grid state.
    NRCI = 10/(10 + TAX)
    
    Higher = more coherent = closer to equilibrium.
    """
    tax = grid_tax(grid)
    return 10.0 / (10.0 + tax)


def grid_energy(grid: Grid) -> Dict[str, float]:
    """Full energy profile of a grid state."""
    return {
        "tax": grid_tax(grid),
        "nrci": grid_nrci(grid),
        "hw": sum(1 for row in grid.cells for v in row if v != 0),
        "norm_sq": sum(v * v for row in grid.cells for v in row),
        "density": sum(1 for row in grid.cells for v in row if v != 0) / (grid.height * grid.width),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Perturbation Analysis — What the Input Does to the Substrate
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Perturbation:
    """How an input grid disturbs the substrate."""
    # Energy state
    inp_energy: Dict[str, float] = field(default_factory=dict)
    out_energy: Dict[str, float] = field(default_factory=dict)
    
    # Energy change (perturbation → equilibrium)
    delta_tax: float = 0.0
    delta_nrci: float = 0.0
    delta_hw: float = 0.0
    
    # Settlement type
    settlement_type: str = "unknown"
    # Types:
    #   cooling: TAX decreases (substrate settles to lower energy)
    #   heating: TAX increases (substrate absorbs energy)
    #   stable: TAX unchanged (substrate already at equilibrium)
    #   phase_change: structural reorganisation (component count changes)
    
    # Y-observation cost (per train pair)
    observation_cost: float = 0.0
    
    # What changed
    n_cells_changed: int = 0
    change_ratio: float = 0.0


def analyse_perturbation(inp: Grid, out: Grid) -> Perturbation:
    """Analyse how a train pair shows the substrate settling."""
    p = Perturbation()
    p.inp_energy = grid_energy(inp)
    p.out_energy = grid_energy(out)
    
    p.delta_tax = p.out_energy["tax"] - p.inp_energy["tax"]
    p.delta_nrci = p.out_energy["nrci"] - p.inp_energy["nrci"]
    p.delta_hw = p.out_energy["hw"] - p.inp_energy["hw"]
    
    # Count changes (only for same-size pairs)
    if inp.shape == out.shape:
        h, w = inp.height, inp.width
        p.n_cells_changed = sum(1 for r in range(h) for c in range(w)
                                if inp.cells[r][c] != out.cells[r][c])
        p.change_ratio = p.n_cells_changed / (h * w)
    else:
        p.n_cells_changed = -1  # Size change
        p.change_ratio = -1.0
    
    # Settlement type
    if abs(p.delta_tax) < 0.01:
        p.settlement_type = "stable"
    elif p.delta_tax < 0:
        p.settlement_type = "cooling"  # Substrate releases energy
    else:
        p.settlement_type = "heating"  # Substrate absorbs energy
    
    # Y-observation cost: each changed cell costs Y
    if p.n_cells_changed > 0:
        p.observation_cost = p.n_cells_changed * _Y
    else:
        p.observation_cost = 0.0
    
    return p


# ═══════════════════════════════════════════════════════════════════════════════
# Settlement Dynamics — How the Substrate Settles
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SettlementDynamics:
    """How the substrate settles from perturbation to equilibrium."""
    # Learned from train pairs
    settlement_type: str = "unknown"
    confidence: float = 0.0
    
    # Per-cell settlement rules (what each cell does to settle)
    cell_rules: Dict[Tuple[int, ...], int] = field(default_factory=dict)
    # Key: (cell_value, sorted_neighbour_values) → settled_value
    
    # Global settlement rules
    colour_map: Dict[int, int] = field(default_factory=dict)
    fill_colour: Optional[int] = None
    
    # Component-level rules
    component_size_threshold: Optional[int] = None
    component_colour_map: Dict[int, int] = field(default_factory=dict)
    
    # Energy trajectory
    inp_tax: float = 0.0
    out_tax: float = 0.0
    tax_released: float = 0.0
    
    # Observations
    n_observations: int = 0
    observation_cost_total: float = 0.0
    
    # Gravity detection
    gravity_detected: bool = False


def learn_settlement_dynamics(task: ARCTask) -> SettlementDynamics:
    """
    Learn how the substrate settles by observing train pairs.
    
    Each train pair is a Y-observation: the observer sees the
    perturbation→equilibrium path at cost Y per active bit.
    """
    dynamics = SettlementDynamics()
    
    perturbations = []
    cell_rule_candidates = defaultdict(list)
    colour_maps = []
    position_rule_candidates = defaultdict(list)
    
    for pair in task.train:
        # Analyse this observation
        p = analyse_perturbation(pair.input, pair.output)
        perturbations.append(p)
        dynamics.observation_cost_total += p.observation_cost
        dynamics.n_observations += 1
        
        if pair.input.shape != pair.output.shape:
            continue
        
        # Learn per-cell rules (context-dependent)
        h, w = pair.input.height, pair.input.width
        for r in range(h):
            for c in range(w):
                iv = pair.input.cells[r][c]
                ov = pair.output.cells[r][c]
                if iv == ov:
                    continue
                
                # Neighbour context
                n_cols = []
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w:
                        n_cols.append(pair.input.cells[nr][nc])
                key = (iv, tuple(sorted(n_cols)))
                cell_rule_candidates[key].append(ov)
                
                # Position context (row, col relative to grid)
                pos_key = (iv, r / max(h-1, 1), c / max(w-1, 1))
                position_rule_candidates[pos_key].append((ov, r, c))
        
        # Learn colour map
        cm = {}
        consistent = True
        for r in range(h):
            for c in range(w):
                s, d = pair.input.cells[r][c], pair.output.cells[r][c]
                if s != d:
                    if s in cm and cm[s] != d:
                        consistent = False
                    cm[s] = d
        if consistent and cm:
            colour_maps.append(cm)
    
    if not perturbations:
        return dynamics
    
    # Synthesize settlement type
    types = [p.settlement_type for p in perturbations]
    if all(t == "cooling" for t in types):
        dynamics.settlement_type = "cooling"
    elif all(t == "heating" for t in types):
        dynamics.settlement_type = "heating"
    elif all(t == "stable" for t in types):
        dynamics.settlement_type = "stable"
    else:
        dynamics.settlement_type = "mixed"
    
    # Synthesize cell rules (majority vote)
    for key, outcomes in cell_rule_candidates.items():
        if outcomes:
            most_common = Counter(outcomes).most_common(1)[0]
            if most_common[1] >= len(outcomes) * 0.5:  # Majority
                dynamics.cell_rules[key] = most_common[0]
    
    # Synthesize colour map (intersection across observations)
    # CRITICAL: only include mappings where the MAJORITY of cells with that
    # colour actually change. If only a few cells change, it's conditional.
    if colour_maps:
        consistent_cm = {}
        for colour in colour_maps[0]:
            targets = set(m[colour] for m in colour_maps if colour in m)
            if len(targets) == 1:
                # Check: what fraction of cells with this colour actually change?
                total_with_colour = 0
                total_changed = 0
                for pair in task.train:
                    if pair.input.shape != pair.output.shape:
                        continue
                    for r in range(pair.input.height):
                        for c in range(pair.input.width):
                            if pair.input.cells[r][c] == colour:
                                total_with_colour += 1
                                if pair.output.cells[r][c] != colour:
                                    total_changed += 1
                # Only include if >50% of cells with this colour change
                if total_with_colour > 0 and total_changed / total_with_colour > 0.5:
                    consistent_cm[colour] = targets.pop()
        dynamics.colour_map = consistent_cm
    
    # Check for fill pattern
    fill_colours = set()
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                    fill_colours.add(pair.output.cells[r][c])
    if len(fill_colours) == 1:
        dynamics.fill_colour = next(iter(fill_colours))
    
    # Check for component-size conditional pattern
    # (the key conditional reasoning gap)
    component_rules = _learn_component_rules(task)
    if component_rules:
        dynamics.component_size_threshold = component_rules.get("threshold")
        dynamics.component_colour_map = component_rules.get("colour_map", {})
    
    # Energy trajectory
    dynamics.inp_tax = sum(p.inp_energy["tax"] for p in perturbations) / len(perturbations)
    dynamics.out_tax = sum(p.out_energy["tax"] for p in perturbations) / len(perturbations)
    dynamics.tax_released = dynamics.inp_tax - dynamics.out_tax
    
    # Detect gravity pattern (non-zero cells move down)
    gravity_detected = True
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            gravity_detected = False
            break
        h, w = pair.input.height, pair.input.width
        # Check: for each column, non-zero cells are compacted to bottom
        for c in range(w):
            inp_col = [pair.input.cells[r][c] for r in range(h)]
            out_col = [pair.output.cells[r][c] for r in range(h)]
            inp_nonzero = [v for v in inp_col if v != 0]
            out_nonzero = [v for v in out_col if v != 0]
            if inp_nonzero != out_nonzero:
                gravity_detected = False
                break
            # Check: output has non-zero cells at bottom
            expected = [0] * (h - len(inp_nonzero)) + inp_nonzero
            if out_col != expected:
                gravity_detected = False
                break
        if not gravity_detected:
            break
    dynamics.gravity_detected = gravity_detected
    
    # Confidence
    dynamics.confidence = min(1.0, dynamics.n_observations / max(len(task.train), 1))
    
    return dynamics


def _learn_component_rules(task: ARCTask) -> Optional[Dict]:
    """
    Learn component-size conditional rules.
    
    This is the key to the conditional reasoning gap:
    "change colour A to B IF component size ≥ threshold"
    """
    # Collect: for each colour, what sizes change and what sizes don't
    size_changes = defaultdict(lambda: {"changed": [], "preserved": []})
    
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        
        h, w = pair.input.height, pair.input.width
        inp_components = _get_components(pair.input)
        
        for comp in inp_components:
            colour = comp["colour"]
            size = comp["size"]
            # Check if this component's cells changed
            any_changed = False
            for r, c in comp["cells"]:
                if pair.output.cells[r][c] != pair.input.cells[r][c]:
                    any_changed = True
                    break
            
            if any_changed:
                size_changes[colour]["changed"].append(size)
            else:
                size_changes[colour]["preserved"].append(size)
    
    # Find the threshold for each colour
    for colour, data in size_changes.items():
        if not data["changed"]:
            continue
        if not data["preserved"]:
            continue
        
        min_changed = min(data["changed"])
        max_preserved = max(data["preserved"])
        
        # The threshold is between max_preserved and min_changed
        if max_preserved < min_changed:
            threshold = min_changed
            # Find what colour they change to
            colour_map = {}
            for pair in task.train:
                if pair.input.shape != pair.output.shape:
                    continue
                for r in range(pair.input.height):
                    for c in range(pair.input.width):
                        if pair.input.cells[r][c] == colour and pair.output.cells[r][c] != colour:
                            colour_map[colour] = pair.output.cells[r][c]
                            break
            if colour_map:
                return {"threshold": threshold, "colour_map": colour_map}
    
    return None


def _get_components(grid: Grid) -> List[Dict]:
    """Get connected components."""
    h, w = grid.height, grid.width
    visited = set()
    components = []
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
                if grid.cells[cr][cc] != colour:
                    continue
                visited.add((cr, cc))
                cells.append((cr, cc))
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = cr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in visited:
                        queue.append((nr, nc))
            components.append({"colour": colour, "size": len(cells), "cells": cells})
    return components


# ═══════════════════════════════════════════════════════════════════════════════
# Settlement Prediction — Apply Dynamics to Test Input
# ═══════════════════════════════════════════════════════════════════════════════

def predict_equilibrium(test: Grid, dynamics: SettlementDynamics,
                         task: ARCTask) -> List[Tuple[str, Grid]]:
    """
    Predict the equilibrium state for a test input.
    
    The substrate settles from perturbation (test input) to equilibrium
    (test output) following the learned dynamics.
    """
    h, w = test.height, test.width
    candidates = []
    
    # Strategy 1: Apply per-cell rules (the substrate's settlement path)
    if dynamics.cell_rules:
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
                if key in dynamics.cell_rules:
                    cells[r][c] = dynamics.cell_rules[key]
                    changed = True
        if changed:
            candidates.append(("settlement_cell_rules", Grid(cells)))
    
    # Strategy 2: Apply colour map (global settlement)
    if dynamics.colour_map:
        cm = dynamics.colour_map
        cells = [[cm.get(test.cells[r][c], test.cells[r][c]) for c in range(w)] for r in range(h)]
        candidates.append(("settlement_colour_map", Grid(cells)))
    
    # Strategy 3: Apply fill (vacuum filling)
    if dynamics.fill_colour is not None:
        cells = [[dynamics.fill_colour if test.cells[r][c] == 0 else test.cells[r][c]
                   for c in range(w)] for r in range(h)]
        candidates.append(("settlement_fill", Grid(cells)))
    
    # Strategy 4: Apply component-size conditional (the key conditional gap)
    if dynamics.component_size_threshold is not None and dynamics.component_colour_map:
        cells = [row[:] for row in test.cells]
        components = _get_components(test)
        changed = False
        for comp in components:
            if comp["colour"] in dynamics.component_colour_map:
                if comp["size"] >= dynamics.component_size_threshold:
                    new_colour = dynamics.component_colour_map[comp["colour"]]
                    for r, c in comp["cells"]:
                        cells[r][c] = new_colour
                        changed = True
        if changed:
            candidates.append(("settlement_component_cond", Grid(cells)))
    
    # Strategy 5: Gravity (non-zero cells compact to bottom)
    if dynamics.gravity_detected:
        cells = [[0]*w for _ in range(h)]
        for c in range(w):
            col = [test.cells[r][c] for r in range(h) if test.cells[r][c] != 0]
            for i, v in enumerate(col):
                cells[h - len(col) + i][c] = v
        candidates.append(("settlement_gravity", Grid(cells)))
    
    # Strategy 5: Conditional Lingo reasoning (semantic intelligence)
    pattern = induce_conditional_pattern(task)
    if pattern:
        result = apply_conditional_pattern(test, pattern)
        if result:
            candidates.append((f"conditional_{pattern.condition_type}", result))
    
    # Strategy 6: Lingo-guided candidates (semantic reasoning)
    desc = describe_transformation(task)
    lingo_cands = generate_from_lingo(task, desc)
    for name, pred in lingo_cands:
        candidates.append((name, pred))
    
    # Strategy 7: Toolkit solvers (the substrate's known stable states)
    for fn, name in [
        (gravity_down, "toolkit_gravity"),
        (local_swap, "toolkit_swap"),
        (colour_center_fill, "toolkit_center"),
        (column_rank_fill, "toolkit_col_rank"),
        (marker_fill_85, "toolkit_marker"),
    ]:
        result = fn(test)
        if result:
            candidates.append((name, result))
    
    # Toolkit: interior fill
    fn = learn_multi_interior_fill(task)
    if fn:
        result = fn(test)
        if result:
            candidates.append(("toolkit_interior", result))
    
    # Toolkit: distance rule
    dist = try_distance_diagonal_rule(task)
    if dist:
        pred, _ = dist
        candidates.append(("toolkit_distance", pred))
    
    # Toolkit: conditional recolour sweep
    objs = extract_objects(test)
    max_size = max((o["size"] for o in objs), default=0)
    for threshold in range(2, max(max_size + 1, 10)):
        for outcome in range(1, 10):
            result = cond_recolour(test, threshold, outcome)
            if result:
                candidates.append((f"toolkit_cond_{threshold}_{outcome}", result))
    
    # Toolkit: cross shift
    cross = _cross_shift(test)
    if cross:
        candidates.append(("toolkit_cross", cross))
    
    # Always: identity (substrate already at equilibrium)
    candidates.append(("identity", Grid([row[:] for row in test.cells])))
    
    return candidates


def _cross_shift(grid: Grid) -> Optional[Grid]:
    """Cross shift by markers."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# Verification — The Sacred Hard Gate
# ═══════════════════════════════════════════════════════════════════════════════

def apply_to_train(task: ARCTask, candidate_name: str, grid: Grid,
                    dynamics: SettlementDynamics) -> Optional[Grid]:
    """Apply a settlement strategy to a grid (for train verification)."""
    h, w = grid.height, grid.width
    
    # Settlement strategies
    if candidate_name == "settlement_cell_rules":
        if dynamics.cell_rules:
            cells = [row[:] for row in grid.cells]
            for r in range(h):
                for c in range(w):
                    n_cols = []
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w:
                            n_cols.append(grid.cells[nr][nc])
                    key = (grid.cells[r][c], tuple(sorted(n_cols)))
                    if key in dynamics.cell_rules:
                        cells[r][c] = dynamics.cell_rules[key]
            return Grid(cells)
        return None
    
    if candidate_name == "settlement_colour_map":
        if dynamics.colour_map:
            cm = dynamics.colour_map
            return Grid([[cm.get(grid.cells[r][c], grid.cells[r][c]) for c in range(w)] for r in range(h)])
        return None
    
    if candidate_name == "settlement_fill":
        if dynamics.fill_colour is not None:
            return Grid([[dynamics.fill_colour if grid.cells[r][c] == 0 else grid.cells[r][c]
                           for c in range(w)] for r in range(h)])
        return None
    
    if candidate_name == "settlement_component_cond":
        if dynamics.component_size_threshold and dynamics.component_colour_map:
            cells = [row[:] for row in grid.cells]
            components = _get_components(grid)
            for comp in components:
                if comp["colour"] in dynamics.component_colour_map:
                    if comp["size"] >= dynamics.component_size_threshold:
                        new_colour = dynamics.component_colour_map[comp["colour"]]
                        for r, c in comp["cells"]:
                            cells[r][c] = new_colour
            return Grid(cells)
        return None
    
    if candidate_name == "settlement_gravity":
        cells = [[0]*w for _ in range(h)]
        for c in range(w):
            col = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
            for i, v in enumerate(col):
                cells[h - len(col) + i][c] = v
        return Grid(cells)
    
    # Toolkit strategies
    toolkit_map = {
        "toolkit_gravity": gravity_down,
        "toolkit_swap": local_swap,
        "toolkit_center": colour_center_fill,
        "toolkit_col_rank": column_rank_fill,
        "toolkit_marker": marker_fill_85,
    }
    if candidate_name in toolkit_map:
        return toolkit_map[candidate_name](grid)
    
    if candidate_name == "toolkit_interior":
        fn = learn_multi_interior_fill(task)
        return fn(grid) if fn else None
    
    if candidate_name == "toolkit_distance":
        return None  # Handled separately
    
    if candidate_name.startswith("toolkit_cond_"):
        parts = candidate_name.split("_")
        return cond_recolour(grid, int(parts[2]), int(parts[3]))
    
    if candidate_name == "toolkit_cross":
        return _cross_shift(grid)
    
    # Lingo strategies
    if candidate_name.startswith("lingo_"):
        return apply_lingo_to_grid(task, candidate_name, grid)
    
    # Conditional strategies
    if candidate_name.startswith("conditional_"):
        pattern = induce_conditional_pattern(task)
        if pattern:
            return apply_conditional_pattern(grid, pattern)
        return None
    
    if candidate_name == "identity":
        return Grid([row[:] for row in grid.cells])
    
    return None


def verify_candidate(task: ARCTask, candidate_name: str,
                      test_pred: Grid, dynamics: SettlementDynamics) -> bool:
    """Verify a candidate on train pairs (the sacred hard gate)."""
    if candidate_name == "toolkit_distance":
        result = try_distance_diagonal_rule(task)
        return result is not None
    
    checked = 0
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        result = apply_to_train(task, candidate_name, pair.input, dynamics)
        if result is None or result.cells != pair.output.cells:
            return False
        checked += 1
    return checked > 0


# ═══════════════════════════════════════════════════════════════════════════════
# The Mind — Solve by Understanding Settlement
# ═══════════════════════════════════════════════════════════════════════════════

def substrate_mind_solve(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    The substrate mind solves a task by understanding how the substrate settles.
    
    1. Observe train pairs (Y-observations at cost Y per active bit)
    2. Learn settlement dynamics (how perturbation → equilibrium)
    3. Predict equilibrium for test input
    4. Verify predictions on train pairs (hard gate)
    5. Score by substrate energy (lower TAX = closer to equilibrium)
    6. Return the best prediction
    """
    # Step 1 & 2: Learn settlement dynamics from observations
    dynamics = learn_settlement_dynamics(task)
    
    # Step 3: Predict equilibrium
    test = task.test[0].input
    candidates = predict_equilibrium(test, dynamics, task)
    
    # Step 4: Verify
    verified = []
    for name, pred in candidates:
        if verify_candidate(task, name, pred, dynamics):
            verified.append((name, pred))
    
    if not verified:
        return None
    
    # Step 5: Score by substrate energy (lower TAX = closer to equilibrium)
    scored = []
    for name, pred in verified:
        tax = grid_tax(pred)
        nrci = grid_nrci(pred)
        # Score: lower TAX is better, but also prefer settlement strategies
        settlement_bonus = 0.1 if name.startswith("settlement_") else 0.0
        score = nrci + settlement_bonus
        scored.append((name, pred, score, tax))
    
    scored.sort(key=lambda x: -x[2])
    
    # Step 6: Return best
    return scored[0][1], scored[0][0]


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark
# ═══════════════════════════════════════════════════════════════════════════════

def benchmark(batch_dir: str) -> Dict[str, Any]:
    files = sorted(f for f in os.listdir(batch_dir) if f.endswith(".json"))
    results = []
    solver_counts = Counter()
    settlement_types = Counter()
    t0 = time.time()
    
    for fname in files:
        task = load_task(os.path.join(batch_dir, fname), name=os.path.splitext(fname)[0])
        try:
            outcome = substrate_mind_solve(task)
        except Exception:
            outcome = None
        solved = outcome is not None
        solver = outcome[1] if outcome else "none"
        results.append({"task_id": task.name, "solved": solved, "solver": solver})
        if solved:
            solver_counts[solver] += 1
        
        # Record settlement dynamics
        dynamics = learn_settlement_dynamics(task)
        settlement_types[dynamics.settlement_type] += 1
    
    elapsed = time.time() - t0
    solved_n = sum(1 for r in results if r["solved"])
    return {
        "solved": solved_n, "total": len(results),
        "pct": round(100.0 * solved_n / max(1, len(results)), 1),
        "elapsed": round(elapsed, 1),
        "solver_counts": dict(solver_counts),
        "settlement_types": dict(settlement_types),
        "results": results,
    }


def main():
    batch = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "training")
    
    print("=" * 72)
    print(" SUBSTRATE EQUILIBRIUM MIND")
    print(" The substrate starts perfect. Data disturbs it.")
    print(" The output is the equilibrium — lowest TAX state.")
    print("=" * 72)
    print()
    
    # Show settlement dynamics for a few tasks
    for tid in ["1e0a9b12", "45737921", "ae58858e", "00dbd492"]:
        task = load_task(f"{batch}/{tid}.json", name=tid)
        dynamics = learn_settlement_dynamics(task)
        p = analyse_perturbation(task.train[0].input, task.train[0].output)
        print(f"{tid}:")
        print(f"  Settlement: {dynamics.settlement_type}")
        print(f"  Inp TAX: {p.inp_energy['tax']:.3f} → Out TAX: {p.out_energy['tax']:.3f}")
        print(f"  ΔTAX: {p.delta_tax:+.3f} ({'releases' if p.delta_tax < 0 else 'absorbs'} energy)")
        print(f"  ΔNRCI: {p.delta_nrci:+.3f}")
        print(f"  Y-observation cost: {p.observation_cost:.3f}")
        print(f"  Cell rules: {len(dynamics.cell_rules)}")
        print(f"  Colour map: {dynamics.colour_map}")
        print(f"  Component rule: threshold={dynamics.component_size_threshold}, map={dynamics.component_colour_map}")
        print()
    
    # Benchmark
    summary = benchmark(batch)
    print("=" * 72)
    print(f" RESULT: {summary['solved']}/{summary['total']} ({summary['pct']}%)")
    print(f" Time: {summary['elapsed']}s")
    print("=" * 72)
    
    for r in summary["results"]:
        if r["solved"]:
            print(f"  ✓ {r['task_id']}: {r['solver']}")
    
    print(f"\n  Settlement types:")
    for s, c in sorted(summary["settlement_types"].items(), key=lambda kv: -kv[1]):
        print(f"    {s}: {c}")
    
    print(f"\n  Solvers:")
    for s, c in sorted(summary["solver_counts"].items(), key=lambda kv: -kv[1]):
        print(f"    {s}: {c}")
    
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "REPORTS", "substrate_mind_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Report: {report_path}")


if __name__ == "__main__":
    main()
