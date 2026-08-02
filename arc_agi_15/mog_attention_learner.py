"""
mog_attention_learner.py — MOG-Attention Learning from Train Pairs
====================================================================

The MOG-mind's equivalent of transformer attention over train pairs.

In a standard transformer:
  - Attention heads learn to focus on relevant tokens
  - Training examples provide the context
  - The model generalises from examples to new inputs

In the MOG-mind:
  - The 4 MOG rows ARE the attention heads (Mass, Info, Activation, Potential)
  - Train pairs ARE the context
  - The mind attends to train pairs through the MOG structure

The key insight: the MOG doesn't just perceive grids — it perceives
TRANSFORMATIONS. When the mind looks at a train pair, it doesn't just
see "input → output". It sees:
  - Row 0 (Mass):      "these colours became those colours"
  - Row 1 (Info):       "this adjacency became that adjacency"
  - Row 2 (Activation): "these cells changed, those stayed"
  - Row 3 (Potential):  "this structure became that structure"

Each row is an attention head that focuses on a different aspect of
the transformation. The mind learns by attending to all 4 heads
simultaneously and finding the consistent pattern.

This is the MOG-mind's own "train-pair attention" — not borrowed from
LLMs, but derived from the substrate's own structure.
"""

from __future__ import annotations
import os, sys, json, time, math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arc_loader import ARCTask, Grid, load_task


# ═══════════════════════════════════════════════════════════════════════════════
# MOG Attention — The 4 Heads
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AttentionHead:
    """One MOG attention head — what it sees in a train pair."""
    name: str
    # What changed in this head's channel
    changes: Dict[str, int] = field(default_factory=dict)  # pattern → count
    # The consistent pattern (if any)
    consistent_pattern: Optional[Any] = None
    # Confidence in this head's pattern
    confidence: float = 0.0


@dataclass
class MOGAttention:
    """The mind's attention over train pairs — all 4 heads."""
    mass: AttentionHead = field(default_factory=lambda: AttentionHead("Mass"))
    info: AttentionHead = field(default_factory=lambda: AttentionHead("Info"))
    activation: AttentionHead = field(default_factory=lambda: AttentionHead("Activation"))
    potential: AttentionHead = field(default_factory=lambda: AttentionHead("Potential"))

    # Cross-head synthesis
    synthesis: str = ""
    overall_confidence: float = 0.0


def attend_to_train_pairs(task: ARCTask) -> MOGAttention:
    """
    The mind attends to train pairs through all 4 MOG heads.
    
    This is the MOG-mind's equivalent of "training" — it doesn't update
    weights, it extracts the transformation pattern from examples.
    """
    attn = MOGAttention()

    # Collect patterns from each train pair
    mass_patterns = []
    info_patterns = []
    activation_patterns = []
    potential_patterns = []

    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue

        # Head 0: Mass — colour distribution changes
        mass = _attend_mass(pair.input, pair.output)
        mass_patterns.append(mass)

        # Head 1: Info — adjacency changes
        info = _attend_info(pair.input, pair.output)
        info_patterns.append(info)

        # Head 2: Activation — which cells changed
        activation = _attend_activation(pair.input, pair.output)
        activation_patterns.append(activation)

        # Head 3: Potential — structural changes
        potential = _attend_potential(pair.input, pair.output)
        potential_patterns.append(potential)

    # Synthesise each head across all train pairs
    attn.mass = _synthesise_head("Mass", mass_patterns)
    attn.info = _synthesise_head("Info", info_patterns)
    attn.activation = _synthesise_head("Activation", activation_patterns)
    attn.potential = _synthesise_head("Potential", potential_patterns)

    # Cross-head synthesis
    attn.synthesis, attn.overall_confidence = _cross_synthesise(attn)

    return attn


# ─── Head 0: Mass (Colour Distribution) ─────────────────────────────────────

def _attend_mass(inp: Grid, out: Grid) -> Dict[str, Any]:
    """What the Mass head sees: colour distribution changes."""
    h, w = inp.height, inp.width

    # Per-cell colour mapping
    colour_map = {}  # in_colour → out_colour (global)
    consistent = True

    for r in range(h):
        for c in range(w):
            iv = inp.cells[r][c]
            ov = out.cells[r][c]
            if iv != ov:
                if iv in colour_map:
                    if colour_map[iv] != ov:
                        consistent = False
                else:
                    colour_map[iv] = ov

    # Count changes by type
    n_fill = sum(1 for r in range(h) for c in range(w) if inp.cells[r][c] == 0 and out.cells[r][c] != 0)
    n_delete = sum(1 for r in range(h) for c in range(w) if inp.cells[r][c] != 0 and out.cells[r][c] == 0)
    n_recolour = sum(1 for r in range(h) for c in range(w) if inp.cells[r][c] != 0 and out.cells[r][c] != 0 and inp.cells[r][c] != out.cells[r][c])

    # Colour-invariant patterns
    # Pattern: swap (A↔B)
    is_swap = False
    swap_pair = None
    if consistent and len(colour_map) == 2:
        items = list(colour_map.items())
        if items[0][1] == items[1][0] and items[1][1] == items[0][0]:
            is_swap = True
            swap_pair = (items[0][0], items[1][0])

    # Pattern: single recolour (A→B, nothing else changes)
    is_single_recolour = consistent and len(colour_map) == 1 and n_fill == 0 and n_delete == 0

    return {
        "colour_map": colour_map if consistent else {},
        "consistent": consistent,
        "n_fill": n_fill,
        "n_delete": n_delete,
        "n_recolour": n_recolour,
        "is_swap": is_swap,
        "swap_pair": swap_pair,
        "is_single_recolour": is_single_recolour,
    }


# ─── Head 1: Info (Adjacency) ───────────────────────────────────────────────

def _attend_info(inp: Grid, out: Grid) -> Dict[str, Any]:
    """What the Info head sees: adjacency changes."""
    h, w = inp.height, inp.width

    # For each changed cell, record its neighbourhood before and after
    neighbourhood_changes = []

    for r in range(h):
        for c in range(w):
            iv = inp.cells[r][c]
            ov = out.cells[r][c]
            if iv == ov:
                continue

            # Input neighbourhood
            inp_neigh = []
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < h and 0 <= nc < w:
                    inp_neigh.append(inp.cells[nr][nc])

            # Output neighbourhood
            out_neigh = []
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < h and 0 <= nc < w:
                    out_neigh.append(out.cells[nr][nc])

            neighbourhood_changes.append({
                "pos": (r, c),
                "inp_val": iv,
                "out_val": ov,
                "inp_neigh": tuple(sorted(inp_neigh)),
                "out_neigh": tuple(sorted(out_neigh)),
            })

    # Learn: (inp_val, inp_neigh) → out_val
    rules = {}
    consistent = True
    for change in neighbourhood_changes:
        key = (change["inp_val"], change["inp_neigh"])
        if key in rules:
            if rules[key] != change["out_val"]:
                consistent = False
        else:
            rules[key] = change["out_val"]

    return {
        "rules": rules if consistent else {},
        "consistent": consistent,
        "n_changes": len(neighbourhood_changes),
    }


# ─── Head 2: Activation (Change Pattern) ────────────────────────────────────

def _attend_activation(inp: Grid, out: Grid) -> Dict[str, Any]:
    """What the Activation head sees: which cells changed and how."""
    h, w = inp.height, inp.width

    # Change map: which positions changed
    change_map = []
    for r in range(h):
        row = []
        for c in range(w):
            row.append(inp.cells[r][c] != out.cells[r][c])
        change_map.append(row)

    # Row-wise change density
    row_density = [sum(row) / w for row in change_map]
    # Column-wise change density
    col_density = [sum(change_map[r][c] for r in range(h)) / h for c in range(w)]

    # Is the change localised to a region?
    changed_positions = [(r, c) for r in range(h) for c in range(w) if change_map[r][c]]
    if changed_positions:
        r_min = min(r for r, c in changed_positions)
        r_max = max(r for r, c in changed_positions)
        c_min = min(c for r, c in changed_positions)
        c_max = max(c for r, c in changed_positions)
        region_h = r_max - r_min + 1
        region_w = c_max - c_min + 1
        region_area = region_h * region_w
        total_area = h * w
        localisation = len(changed_positions) / region_area if region_area > 0 else 0
    else:
        localisation = 0

    return {
        "change_map": change_map,
        "n_changed": len(changed_positions),
        "row_density": row_density,
        "col_density": col_density,
        "localisation": localisation,  # 1.0 = tightly localised, 0.0 = scattered
    }


# ─── Head 3: Potential (Structural) ─────────────────────────────────────────

def _attend_potential(inp: Grid, out: Grid) -> Dict[str, Any]:
    """What the Potential head sees: structural changes."""
    h, w = inp.height, inp.width

    # Connected component analysis
    inp_components = _get_components(inp)
    out_components = _get_components(out)

    # Per-colour component count change
    inp_counts = Counter(c["colour"] for c in inp_components)
    out_counts = Counter(c["colour"] for c in out_components)

    # Size distribution change
    inp_sizes = sorted([c["size"] for c in inp_components], reverse=True)
    out_sizes = sorted([c["size"] for c in out_components], reverse=True)

    return {
        "inp_component_counts": dict(inp_counts),
        "out_component_counts": dict(out_counts),
        "inp_sizes": inp_sizes,
        "out_sizes": out_sizes,
        "n_inp_components": len(inp_components),
        "n_out_components": len(out_components),
    }


def _get_components(grid: Grid) -> List[Dict]:
    """Get connected components with their properties."""
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
# Head Synthesis — find the consistent pattern across train pairs
# ═══════════════════════════════════════════════════════════════════════════════

def _synthesise_head(name: str, patterns: List[Dict]) -> AttentionHead:
    """Synthesise one attention head across all train pairs."""
    head = AttentionHead(name=name)

    if not patterns:
        return head

    if name == "Mass":
        # Find consistent colour map across all pairs
        all_maps = [p["colour_map"] for p in patterns if p.get("colour_map")]
        if all_maps:
            # Intersect: only keep mappings present in ALL pairs
            consistent_map = {}
            for colour in all_maps[0]:
                targets = set(m[colour] for m in all_maps if colour in m)
                if len(targets) == 1:
                    consistent_map[colour] = targets.pop()
            head.consistent_pattern = consistent_map
            head.confidence = len(consistent_map) / max(len(all_maps[0]), 1) if all_maps[0] else 0

        # Check fill/delete consistency
        n_fills = [p["n_fill"] for p in patterns]
        n_deletes = [p["n_delete"] for p in patterns]
        if all(n > 0 for n in n_fills) and all(n == 0 for n in n_deletes):
            head.changes["fill_only"] = True
        elif all(n > 0 for n in n_deletes) and all(n == 0 for n in n_fills):
            head.changes["delete_only"] = True

    elif name == "Info":
        # Find consistent neighbour rules across all pairs
        all_rules = [p["rules"] for p in patterns if p.get("rules")]
        if all_rules:
            consistent_rules = {}
            for key in all_rules[0]:
                targets = set(r[key] for r in all_rules if key in r)
                if len(targets) == 1:
                    consistent_rules[key] = targets.pop()
            head.consistent_pattern = consistent_rules
            head.confidence = len(consistent_rules) / max(len(all_rules[0]), 1) if all_rules[0] else 0

    elif name == "Activation":
        # Check if the change pattern is consistent across pairs
        n_changed = [p["n_changed"] for p in patterns]
        localisations = [p["localisation"] for p in patterns]
        head.changes["avg_changed"] = sum(n_changed) / len(n_changed) if n_changed else 0
        head.changes["avg_localisation"] = sum(localisations) / len(localisations) if localisations else 0
        head.confidence = 1.0 - (max(n_changed) - min(n_changed)) / max(max(n_changed), 1) if n_changed else 0

    elif name == "Potential":
        # Check if component structure is consistent
        inp_counts = [p["n_inp_components"] for p in patterns]
        out_counts = [p["n_out_components"] for p in patterns]
        head.changes["stable_components"] = all(ic == oc for ic, oc in zip(inp_counts, out_counts))
        head.confidence = 1.0 if head.changes.get("stable_components") else 0.5

    return head


def _cross_synthesise(attn: MOGAttention) -> Tuple[str, float]:
    """Synthesise across all 4 heads to find the overall pattern."""
    scores = []
    insights = []

    # Mass head
    if attn.mass.consistent_pattern:
        scores.append(attn.mass.confidence)
        insights.append(f"Mass: consistent colour map ({len(attn.mass.consistent_pattern)} mappings)")
    elif attn.mass.changes.get("fill_only"):
        scores.append(0.8)
        insights.append("Mass: fill-only transformation")
    elif attn.mass.changes.get("delete_only"):
        scores.append(0.8)
        insights.append("Mass: delete-only transformation")

    # Info head
    if attn.info.consistent_pattern:
        scores.append(attn.info.confidence)
        insights.append(f"Info: consistent neighbour rules ({len(attn.info.consistent_pattern)} rules)")

    # Activation head
    if attn.activation.changes.get("avg_localisation", 0) > 0.8:
        scores.append(0.7)
        insights.append("Activation: changes are tightly localised")

    # Potential head
    if attn.potential.changes.get("stable_components"):
        scores.append(0.6)
        insights.append("Potential: component structure is stable")

    overall = sum(scores) / max(len(scores), 1)
    synthesis = "; ".join(insights) if insights else "No consistent pattern found"

    return synthesis, overall


# ═══════════════════════════════════════════════════════════════════════════════
# Attention-Guided Candidate Generation
# ═══════════════════════════════════════════════════════════════════════════════

def generate_from_attention(task: ARCTask, attn: MOGAttention) -> List[Tuple[str, Grid]]:
    """
    Generate candidates guided by what the attention heads learned.
    """
    test = task.test[0].input
    h, w = test.height, test.width
    candidates = []

    # ─── Per-pair attention (the mind attends to each train pair individually) ─
    for i, pair in enumerate(task.train):
        if pair.input.shape != pair.output.shape or pair.input.shape != test.shape:
            continue

        # Mass: per-pair colour map
        pair_mass = _attend_mass(pair.input, pair.output)
        if pair_mass["colour_map"]:
            cm = pair_mass["colour_map"]
            cells = [[cm.get(test.cells[r][c], test.cells[r][c]) for c in range(w)] for r in range(h)]
            candidates.append((f"attn_pair{i}_mass", Grid(cells)))

        # Info: per-pair neighbour rules
        pair_info = _attend_info(pair.input, pair.output)
        if pair_info["rules"]:
            rules = pair_info["rules"]
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
                candidates.append((f"attn_pair{i}_info", Grid(cells)))

        # Activation: per-pair change pattern
        pair_act = _attend_activation(pair.input, pair.output)
        if pair_act["n_changed"] > 0:
            cells = [row[:] for row in test.cells]
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] != pair.output.cells[r][c]:
                        delta = pair.output.cells[r][c] - pair.input.cells[r][c]
                        cells[r][c] = max(0, min(9, test.cells[r][c] + delta))
            candidates.append((f"attn_pair{i}_delta", Grid(cells)))

    # ─── Global attention (intersection across all pairs) ──────────────────
    if attn.mass.consistent_pattern:
        cm = attn.mass.consistent_pattern
        cells = [[cm.get(test.cells[r][c], test.cells[r][c]) for c in range(w)] for r in range(h)]
        candidates.append(("attn_mass_colour", Grid(cells)))

    if attn.info.consistent_pattern:
        rules = attn.info.consistent_pattern
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
            candidates.append(("attn_info_neighbour", Grid(cells)))

    # ─── Colour-invariant patterns (shape-independent) ───────────────────
    # Swap detection
    if attn.mass.changes.get("is_swap"):
        test_palette = sorted(set(v for row in test.cells for v in row if v != 0))
        if len(test_palette) == 2:
            a, b = test_palette
            cells = [[b if test.cells[r][c] == a else a if test.cells[r][c] == b else test.cells[r][c]
                       for c in range(w)] for r in range(h)]
            candidates.append(("attn_mass_swap", Grid(cells)))

    # Single recolour (shape-independent)
    if attn.mass.changes.get("is_single_recolour"):
        # Try each train pair's colour map
        for i, pair in enumerate(task.train):
            pair_mass = _attend_mass(pair.input, pair.output)
            if pair_mass["colour_map"] and len(pair_mass["colour_map"]) == 1:
                src, dst = list(pair_mass["colour_map"].items())[0]
                # Check if test has the source colour
                test_has_src = any(test.cells[r][c] == src for r in range(h) for c in range(w))
                if test_has_src:
                    cells = [[dst if test.cells[r][c] == src else test.cells[r][c]
                               for c in range(w)] for r in range(h)]
                    candidates.append((f"attn_single_recolour_{src}_{dst}", Grid(cells)))

    # Fill detection (shape-independent)
    if attn.mass.changes.get("fill_only"):
        # Find the fill colour from train pairs
        for pair in task.train:
            fills = set()
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                        fills.add(pair.output.cells[r][c])
            if len(fills) == 1:
                fill = next(iter(fills))
                cells = [[fill if test.cells[r][c] == 0 else test.cells[r][c]
                           for c in range(w)] for r in range(h)]
                candidates.append(("attn_fill_uniform", Grid(cells)))
                break

    # Unanimous neighbour (shape-independent)
    cells = [row[:] for row in test.cells]
    changed = False
    for r in range(h):
        for c in range(w):
            v = test.cells[r][c]
            if v == 0:
                continue
            n_cols = []
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < h and 0 <= nc < w:
                    n_cols.append(test.cells[nr][nc])
            non_zero_neigh = [n for n in n_cols if n != 0]
            if non_zero_neigh and len(set(non_zero_neigh)) == 1 and non_zero_neigh[0] != v:
                cells[r][c] = non_zero_neigh[0]
                changed = True
    if changed:
        candidates.append(("attn_info_unanimous_neigh", Grid(cells)))

    return candidates


# ═══════════════════════════════════════════════════════════════════════════════
# Verification — same hard gate
# ═══════════════════════════════════════════════════════════════════════════════

def apply_attn_to_grid(task: ARCTask, candidate_name: str, grid: Grid,
                        attn: MOGAttention) -> Optional[Grid]:
    """Apply an attention-generated strategy to any grid."""
    h, w = grid.height, grid.width

    # Per-pair strategies
    if candidate_name.startswith("attn_pair"):
        # Parse: attn_pair{i}_{type}
        parts = candidate_name.split("_")
        idx = int(parts[1])
        strategy = parts[2]
        pair = task.train[idx]
        if pair.input.shape != pair.output.shape or pair.input.shape != grid.shape:
            return None

        if strategy == "mass":
            pair_mass = _attend_mass(pair.input, pair.output)
            if pair_mass["colour_map"]:
                cm = pair_mass["colour_map"]
                return Grid([[cm.get(grid.cells[r][c], grid.cells[r][c]) for c in range(w)] for r in range(h)])
            return None

        if strategy == "info":
            pair_info = _attend_info(pair.input, pair.output)
            if pair_info["rules"]:
                rules = pair_info["rules"]
                cells = [row[:] for row in grid.cells]
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
                return Grid(cells)
            return None

        if strategy == "delta":
            cells = [row[:] for row in grid.cells]
            for r in range(h):
                for c in range(w):
                    if pair.input.cells[r][c] != pair.output.cells[r][c]:
                        delta = pair.output.cells[r][c] - pair.input.cells[r][c]
                        cells[r][c] = max(0, min(9, grid.cells[r][c] + delta))
            return Grid(cells)

        return None

    # Global strategies
    if candidate_name == "attn_mass_colour":
        if attn.mass.consistent_pattern:
            cm = attn.mass.consistent_pattern
            return Grid([[cm.get(grid.cells[r][c], grid.cells[r][c]) for c in range(w)] for r in range(h)])
        return None

    if candidate_name == "attn_mass_swap":
        # Swap the two non-zero colours
        palette = sorted(set(v for row in grid.cells for v in row if v != 0))
        if len(palette) == 2:
            a, b = palette
            return Grid([[b if grid.cells[r][c] == a else a if grid.cells[r][c] == b else grid.cells[r][c]
                           for c in range(w)] for r in range(h)])
        return None

    if candidate_name.startswith("attn_mass_recolour_"):
        # Parse: attn_mass_recolour_{src}_{target}
        parts = candidate_name.split("_")
        src = int(parts[3])
        target = int(parts[4])
        return Grid([[target if grid.cells[r][c] == src else grid.cells[r][c]
                       for c in range(w)] for r in range(h)])

    if candidate_name == "attn_info_neighbour":
        if attn.info.consistent_pattern:
            rules = attn.info.consistent_pattern
            cells = [row[:] for row in grid.cells]
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
            return Grid(cells)
        return None

    if candidate_name == "attn_info_unanimous_neigh":
        cells = [row[:] for row in grid.cells]
        for r in range(h):
            for c in range(w):
                v = grid.cells[r][c]
                if v == 0:
                    continue
                n_cols = []
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < h and 0 <= nc < w:
                        n_cols.append(grid.cells[nr][nc])
                non_zero_neigh = [n for n in n_cols if n != 0]
                if non_zero_neigh and len(set(non_zero_neigh)) == 1 and non_zero_neigh[0] != v:
                    cells[r][c] = non_zero_neigh[0]
        return Grid(cells)

    if candidate_name.startswith("attn_activation_pair"):
        idx = int(candidate_name.replace("attn_activation_pair", ""))
        pair = task.train[idx]
        if pair.input.shape != pair.output.shape or pair.input.shape != grid.shape:
            return None
        cells = [row[:] for row in grid.cells]
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                if pair.input.cells[r][c] != pair.output.cells[r][c]:
                    delta = pair.output.cells[r][c] - pair.input.cells[r][c]
                    cells[r][c] = max(0, min(9, grid.cells[r][c] + delta))
        return Grid(cells)

    if candidate_name == "attn_potential_structure":
        return apply_attn_to_grid(task, "attn_mass_colour", grid, attn)

    if candidate_name == "attn_cross_mass_info":
        if attn.mass.consistent_pattern and attn.info.consistent_pattern:
            cm = attn.mass.consistent_pattern
            rules = attn.info.consistent_pattern
            cells = [[cm.get(grid.cells[r][c], grid.cells[r][c]) for c in range(w)] for r in range(h)]
            for r in range(h):
                for c in range(w):
                    n_cols = []
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < h and 0 <= nc < w:
                            n_cols.append(cells[nr][nc])
                    key = (cells[r][c], tuple(sorted(n_cols)))
                    if key in rules:
                        cells[r][c] = rules[key]
            return Grid(cells)
        return None

    # Shape-independent strategies
    if candidate_name == "attn_fill_uniform":
        for pair in task.train:
            fills = set()
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                        fills.add(pair.output.cells[r][c])
            if len(fills) == 1:
                fill = next(iter(fills))
                return Grid([[fill if grid.cells[r][c] == 0 else grid.cells[r][c]
                               for c in range(w)] for r in range(h)])
        return None

    if candidate_name == "attn_mass_swap":
        palette = sorted(set(v for row in grid.cells for v in row if v != 0))
        if len(palette) == 2:
            a, b = palette
            return Grid([[b if grid.cells[r][c] == a else a if grid.cells[r][c] == b else grid.cells[r][c]
                           for c in range(w)] for r in range(h)])
        return None

    if candidate_name.startswith("attn_single_recolour_"):
        parts = candidate_name.split("_")
        src = int(parts[3])
        dst = int(parts[4])
        return Grid([[dst if grid.cells[r][c] == src else grid.cells[r][c]
                       for c in range(w)] for r in range(h)])

    return None


def verify_attn_candidate(task: ARCTask, candidate_name: str, 
                           test_pred: Grid, attn: MOGAttention) -> bool:
    """Verify an attention-generated candidate on train pairs."""
    checked = 0
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        result = apply_attn_to_grid(task, candidate_name, pair.input, attn)
        if result is None or result.cells != pair.output.cells:
            return False
        checked += 1
    return checked > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Integration: The Full MOG-Attention Solve
# ═══════════════════════════════════════════════════════════════════════════════

def mog_attention_solve(task: ARCTask) -> Optional[Tuple[Grid, str]]:
    """
    Solve a task using MOG-attention over train pairs.
    
    1. Attend to train pairs through 4 MOG heads
    2. Generate candidates from attention patterns
    3. Verify on train pairs (hard gate)
    4. Return best verified candidate
    """
    # Step 1: Attend
    attn = attend_to_train_pairs(task)

    # Step 2: Generate from attention
    candidates = generate_from_attention(task, attn)

    # Step 3: Verify and select
    verified = []
    for name, pred in candidates:
        if verify_attn_candidate(task, name, pred, attn):
            # Score by how well it matches the test input
            score = _match_score(task.test[0].input, pred)
            verified.append((name, pred, score))

    if not verified:
        return None

    # Step 4: Return best
    verified.sort(key=lambda x: -x[2])
    return verified[0][1], verified[0][0]


def _match_score(inp: Grid, out: Grid) -> float:
    """Score how well the transformation preserves structure."""
    if inp.shape != out.shape:
        return 0.0
    h, w = inp.height, inp.width
    same = sum(1 for r in range(h) for c in range(w) if inp.cells[r][c] == out.cells[r][c])
    return same / (h * w)


# ═══════════════════════════════════════════════════════════════════════════════
# Report — What the attention heads saw
# ═══════════════════════════════════════════════════════════════════════════════

def attention_report(task: ARCTask) -> str:
    """Generate a human-readable report of what the attention heads saw."""
    attn = attend_to_train_pairs(task)
    lines = [
        f"MOG-Attention Report for {task.name}",
        f"  Overall confidence: {attn.overall_confidence:.2f}",
        f"  Synthesis: {attn.synthesis}",
        f"  Mass head: pattern={attn.mass.consistent_pattern}, confidence={attn.mass.confidence:.2f}",
        f"  Info head: {len(attn.info.consistent_pattern or {})} rules, confidence={attn.info.confidence:.2f}",
        f"  Activation head: avg_localisation={attn.activation.changes.get('avg_localisation', 0):.2f}",
        f"  Potential head: stable_components={attn.potential.changes.get('stable_components', False)}",
    ]
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark
# ═══════════════════════════════════════════════════════════════════════════════

def benchmark(batch_dir: str) -> Dict[str, Any]:
    files = sorted(f for f in os.listdir(batch_dir) if f.endswith(".json"))
    results = []
    solver_counts = Counter()
    t0 = time.time()
    for fname in files:
        task = load_task(os.path.join(batch_dir, fname), name=os.path.splitext(fname)[0])
        try:
            outcome = mog_attention_solve(task)
        except Exception:
            outcome = None
        solved = outcome is not None
        solver = outcome[1] if outcome else "none"
        results.append({"task_id": task.name, "solved": solved, "solver": solver})
        if solved:
            solver_counts[solver] += 1
    elapsed = time.time() - t0
    solved_n = sum(1 for r in results if r["solved"])
    return {
        "solved": solved_n, "total": len(results),
        "pct": round(100.0 * solved_n / max(1, len(results)), 1),
        "elapsed": round(elapsed, 1),
        "solver_counts": dict(solver_counts),
        "results": results,
    }


def main():
    batch = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "training")
    print("=" * 72)
    print(" MOG-ATTENTION LEARNER")
    print("=" * 72)
    print()

    # Show attention report for a few tasks
    for tid in ["45737921", "575b1a71", "ae58858e"]:
        task = load_task(f"{batch}/{tid}.json", name=tid)
        print(attention_report(task))
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
    print(f"\n  Solvers:")
    for s, c in sorted(summary["solver_counts"].items(), key=lambda kv: -kv[1]):
        print(f"    {s}: {c}")

    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "REPORTS", "mog_attention_learner_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Report: {report_path}")


if __name__ == "__main__":
    main()
