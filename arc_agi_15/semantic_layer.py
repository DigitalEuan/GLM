"""
semantic_layer.py — The Mind's Inner Language
===============================================

The GLM's Lingo vocabulary gives the mind a native language for describing
transformations. Instead of just applying rules, the mind can now:

1. DESCRIBE what it sees in Lingo ("the substrate is cooling, COMPACTION_FLOW
   in the A_Flux layer")
2. REASON about what should happen ("if COMPACTION_FLOW, then gravity")
3. CHECK logical consistency ("does this prediction match the description?")
4. GENERATE candidates from Lingo descriptions

This is the mind's "inner monologue" — semantic reasoning grounded in
the UBP substrate's own language.

The Lingo vocabulary:
  M_* (Reality):   substance, spatial — grid, cell, colour, object, shape
  I_* (Information): sequence, topology — position, adjacency, symmetry
  A_* (Activation): operations, dynamics — rotate, flip, move, scale, gravity
  P_* (Potential): constraints, coherence — recolour, fill, snap, NRCI
"""

from __future__ import annotations
import os, sys, math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arc_loader import ARCTask, Grid


# ═══════════════════════════════════════════════════════════════════════════════
# Lingo Vocabulary — The Mind's Native Terms
# ═══════════════════════════════════════════════════════════════════════════════

# MOG Layers → Lingo terms
LINGO_VOCAB = {
    # M_* (Reality) — substance
    "grid":     {"layer": "M_Space",   "term": "SPATIAL_SUBSTRATE"},
    "cell":     {"layer": "M_Mass",    "term": "UNIT_NODE"},
    "colour":   {"layer": "M_Charge",  "term": "CHARGE_VALUE"},
    "object":   {"layer": "M_Count",   "term": "CLUSTER"},
    "shape":    {"layer": "M_Space",   "term": "N_GON_FOOTPRINT"},
    "size":     {"layer": "M_Count",   "term": "NODE_CARDINALITY"},

    # I_* (Information) — topology
    "position":  {"layer": "I_Topology",      "term": "LATTICE_COORD"},
    "adjacency": {"layer": "I_Connectivity",  "term": "EDGE_BOND"},
    "symmetry":  {"layer": "I_Symmetry",      "term": "DIHEDRAL_GROUP"},
    "pattern":   {"layer": "I_Density",       "term": "TOPO_SIGNATURE"},
    "border":    {"layer": "I_Connectivity",  "term": "BOUNDARY_EDGE"},
    "interior":  {"layer": "I_Connectivity",  "term": "ENCLOSED_REGION"},

    # A_* (Activation) — operations
    "rotate":   {"layer": "A_Force",   "term": "DIHEDRAL_ROTATION"},
    "flip":     {"layer": "A_Force",   "term": "PLANE_REFLECTION"},
    "move":     {"layer": "A_Velocity","term": "CENTROID_SHIFT"},
    "scale":    {"layer": "A_Force",   "term": "RADIUS_SCALING"},
    "gravity":  {"layer": "A_Flux",    "term": "COMPACTION_FLOW"},
    "merge":    {"layer": "A_Energy",  "term": "CLUSTER_UNION"},
    "split":    {"layer": "A_Energy",  "term": "CLUSTER_FISSION"},
    "fill":     {"layer": "A_Flux",    "term": "REGION_FILL"},
    "crop":     {"layer": "A_Velocity","term": "BOUNDARY_TRIM"},

    # P_* (Potential) — constraints
    "recolour":  {"layer": "P_Ratio",     "term": "CHARGE_SWAP"},
    "outline":   {"layer": "P_Coherence", "term": "BOUNDARY_EXTRACT"},
    "count":     {"layer": "P_Limit",     "term": "CARDINALITY_MEASURE"},
    "snap":      {"layer": "P_Phase",     "term": "GOLAY_CORRECTION"},
    "coherent":  {"layer": "P_Coherence", "term": "NRCI_STABLE"},
    "manifested":{"layer": "P_Phase",     "term": "NRCI_MANIFEST"},
    "subliminal":{"layer": "P_Phase",     "term": "NRCI_SUBLIMINAL"},
}

# Reverse: Lingo term → human
LINGO_TO_HUMAN = {v["term"]: k for k, v in LINGO_VOCAB.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# Semantic Description — What the Mind "Thinks" About a Task
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SemanticDescription:
    """The mind's semantic description of a transformation in Lingo."""
    # What changed (in Lingo terms)
    operations: List[str] = field(default_factory=list)
    # e.g., ["CHARGE_SWAP", "COMPACTION_FLOW", "REGION_FILL"]

    # Which layers were affected
    layers_affected: Dict[str, List[str]] = field(default_factory=dict)
    # e.g., {"M_Charge": ["colour 2→6"], "A_Flux": ["gravity down"]}

    # Settlement dynamics (from substrate physics)
    settlement: str = ""
    # e.g., "cooling: substrate releases energy, TAX decreases"

    # Logical consistency check
    consistent: bool = True
    inconsistencies: List[str] = field(default_factory=list)

    # Human-readable description
    description: str = ""

    # Confidence
    confidence: float = 0.0


def describe_transformation(task: ARCTask) -> SemanticDescription:
    """
    The mind describes what it sees in Lingo.
    
    This is the mind's "inner monologue" — it observes the train pairs
    and translates what it sees into the GLM's native language.
    """
    desc = SemanticDescription()

    # Observe the first train pair
    pair0 = task.train[0]
    inp = pair0.input
    out = pair0.output

    if inp.shape != out.shape:
        desc.operations.append("BOUNDARY_TRIM")  # or RADIUS_SCALING
        desc.layers_affected["A_Velocity"] = [f"size {inp.shape} → {out.shape}"]
        desc.description = f"Size change: {inp.shape} → {out.shape}"
        desc.settlement = "size_change: substrate boundary reorganisation"
        return desc

    h, w = inp.height, inp.width

    # Count changes per type
    n_fill = sum(1 for r in range(h) for c in range(w) if inp.cells[r][c] == 0 and out.cells[r][c] != 0)
    n_delete = sum(1 for r in range(h) for c in range(w) if inp.cells[r][c] != 0 and out.cells[r][c] == 0)
    n_recolour = sum(1 for r in range(h) for c in range(w)
                     if inp.cells[r][c] != 0 and out.cells[r][c] != 0 and inp.cells[r][c] != out.cells[r][c])
    n_preserved = sum(1 for r in range(h) for c in range(w) if inp.cells[r][c] == out.cells[r][c])

    # Describe in Lingo
    if n_fill > 0:
        desc.operations.append("REGION_FILL")
        desc.layers_affected.setdefault("A_Flux", []).append(f"{n_fill} cells filled")

    if n_delete > 0:
        desc.operations.append("CLUSTER_FISSION")
        desc.layers_affected.setdefault("A_Energy", []).append(f"{n_delete} cells deleted")

    if n_recolour > 0:
        desc.operations.append("CHARGE_SWAP")
        desc.layers_affected.setdefault("P_Ratio", []).append(f"{n_recolour} cells recoloured")

    # Check for gravity pattern (non-zero cells compact to bottom per column)
    gravity = True
    for c in range(w):
        inp_col = [inp.cells[r][c] for r in range(h)]
        out_col = [out.cells[r][c] for r in range(h)]
        inp_nz = [v for v in inp_col if v != 0]
        out_nz = [v for v in out_col if v != 0]
        if inp_nz != out_nz:
            gravity = False
            break
        # Check: output has non-zero cells at bottom, preserving order
        expected = [0] * (h - len(inp_nz)) + inp_nz
        if out_col != expected:
            gravity = False
            break

    if gravity:
        desc.operations = ["COMPACTION_FLOW"]
        desc.layers_affected = {"A_Flux": ["gravity: non-zero cells compact to bottom"]}
        desc.description = "COMPACTION_FLOW: substrate settles via gravitational compaction"
        desc.settlement = "cooling: substrate releases energy via compaction"
        desc.confidence = 0.9
        return desc

    # Check for colour swap
    colour_map = {}
    consistent = True
    for r in range(h):
        for c in range(w):
            s, d = inp.cells[r][c], out.cells[r][c]
            if s != d:
                if s in colour_map and colour_map[s] != d:
                    consistent = False
                colour_map[s] = d

    if consistent and colour_map:
        if len(colour_map) == 2:
            items = list(colour_map.items())
            if items[0][1] == items[1][0] and items[1][1] == items[0][0]:
                desc.operations = ["CHARGE_SWAP"]
                desc.layers_affected = {"P_Ratio": [f"swap {items[0][0]}↔{items[0][1]}"]}
                desc.description = f"CHARGE_SWAP: swap colours {items[0][0]}↔{items[0][1]}"
                desc.settlement = "stable: substrate maintains energy, colours exchange"
                desc.confidence = 0.9
                return desc

    # General description
    ops = []
    if n_fill > 0:
        ops.append(f"fill {n_fill}")
    if n_delete > 0:
        ops.append(f"delete {n_delete}")
    if n_recolour > 0:
        ops.append(f"recolour {n_recolour}")

    desc.description = f"Transformation: {', '.join(ops)} ({n_preserved} preserved)"
    desc.settlement = "mixed: substrate undergoes multi-step reorganisation"
    desc.confidence = 0.5

    # Logical consistency check
    _check_consistency(desc, task)

    return desc


def _check_consistency(desc: SemanticDescription, task: ARCTask):
    """Check if the semantic description is logically consistent."""
    # Check: do all train pairs show the same pattern?
    pair0_type = _classify_pair(task.train[0])
    for i, pair in enumerate(task.train[1:], 1):
        pair_type = _classify_pair(pair)
        if pair_type != pair0_type:
            desc.consistent = False
            desc.inconsistencies.append(
                f"Pair 0 is '{pair0_type}' but pair {i} is '{pair_type}'"
            )


def _classify_pair(pair) -> str:
    """Classify a train pair's transformation type."""
    if pair.input.shape != pair.output.shape:
        return "size_change"
    h, w = pair.input.height, pair.input.width
    n_fill = sum(1 for r in range(h) for c in range(w) if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0)
    n_delete = sum(1 for r in range(h) for c in range(w) if pair.input.cells[r][c] != 0 and pair.output.cells[r][c] == 0)
    n_recolour = sum(1 for r in range(h) for c in range(w)
                     if pair.input.cells[r][c] != 0 and pair.output.cells[r][c] != 0 and pair.input.cells[r][c] != pair.output.cells[r][c])
    if n_fill > 0 and n_delete == 0 and n_recolour == 0:
        return "fill"
    if n_fill == 0 and n_delete > 0 and n_recolour == 0:
        return "delete"
    if n_fill == 0 and n_delete == 0 and n_recolour > 0:
        return "recolour"
    if n_fill > 0 and n_delete > 0:
        return "compose"
    return "mixed"


# ═══════════════════════════════════════════════════════════════════════════════
# Lingo-Guided Candidate Generation
# ═══════════════════════════════════════════════════════════════════════════════

def generate_from_lingo(task: ARCTask, desc: SemanticDescription) -> List[Tuple[str, Grid]]:
    """
    Generate candidates based on the Lingo description.
    
    The mind "thinks" in Lingo about what transformation happened,
    then generates candidates that match the Lingo description.
    """
    test = task.test[0].input
    h, w = test.height, test.width
    candidates = []

    for op in desc.operations:
        if op == "COMPACTION_FLOW":
            # Gravity: compact non-zero cells to bottom
            cells = [[0]*w for _ in range(h)]
            for c in range(w):
                col = [test.cells[r][c] for r in range(h) if test.cells[r][c] != 0]
                for i, v in enumerate(col):
                    cells[h - len(col) + i][c] = v
            candidates.append(("lingo_gravity", Grid(cells)))

        elif op == "CHARGE_SWAP":
            # Recolour: apply colour map from train pairs
            colour_map = _learn_colour_map(task)
            if colour_map:
                cells = [[colour_map.get(test.cells[r][c], test.cells[r][c]) for c in range(w)] for r in range(h)]
                candidates.append(("lingo_recolour", Grid(cells)))

            # Swap: if exactly 2 non-zero colours, swap them
            palette = sorted(set(v for row in test.cells for v in row if v != 0))
            if len(palette) == 2:
                a, b = palette
                cells = [[b if test.cells[r][c] == a else a if test.cells[r][c] == b else test.cells[r][c]
                           for c in range(w)] for r in range(h)]
                candidates.append(("lingo_swap", Grid(cells)))

        elif op == "REGION_FILL":
            # Fill: fill zeros with the fill colour
            fill_colours = set()
            for pair in task.train:
                if pair.input.shape != pair.output.shape:
                    continue
                for r in range(pair.input.height):
                    for c in range(pair.input.width):
                        if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                            fill_colours.add(pair.output.cells[r][c])
            if len(fill_colours) == 1:
                fill = next(iter(fill_colours))
                cells = [[fill if test.cells[r][c] == 0 else test.cells[r][c]
                           for c in range(w)] for r in range(h)]
                candidates.append(("lingo_fill", Grid(cells)))

        elif op == "BOUNDARY_TRIM":
            # Crop: trim to bounding box
            for pair in task.train:
                oh, ow = pair.output.height, pair.output.width
                if oh <= h and ow <= w:
                    # Try centre crop
                    r_off = (h - oh) // 2
                    c_off = (w - ow) // 2
                    cells = [[test.cells[r_off + r][c_off + c] for c in range(ow)] for r in range(oh)]
                    candidates.append(("lingo_crop_centre", Grid(cells)))
                    # Try top-left crop
                    cells = [[test.cells[r][c] for c in range(ow)] for r in range(oh)]
                    candidates.append(("lingo_crop_tl", Grid(cells)))
                    break

    return candidates


def _learn_colour_map(task: ARCTask) -> Dict[int, int]:
    """Learn a consistent colour map from train pairs."""
    mapping = {}
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        for r in range(pair.input.height):
            for c in range(pair.input.width):
                s, d = pair.input.cells[r][c], pair.output.cells[r][c]
                if s != d:
                    if s in mapping and mapping[s] != d:
                        return {}
                    mapping[s] = d
    return mapping


# ═══════════════════════════════════════════════════════════════════════════════
# Verification
# ═══════════════════════════════════════════════════════════════════════════════

def apply_lingo_to_grid(task: ARCTask, candidate_name: str, grid: Grid) -> Optional[Grid]:
    """Apply a Lingo-described strategy to any grid."""
    h, w = grid.height, grid.width

    if candidate_name == "lingo_gravity":
        cells = [[0]*w for _ in range(h)]
        for c in range(w):
            col = [grid.cells[r][c] for r in range(h) if grid.cells[r][c] != 0]
            for i, v in enumerate(col):
                cells[h - len(col) + i][c] = v
        return Grid(cells)

    if candidate_name == "lingo_recolour":
        cm = _learn_colour_map(task)
        if cm:
            return Grid([[cm.get(grid.cells[r][c], grid.cells[r][c]) for c in range(w)] for r in range(h)])
        return None

    if candidate_name == "lingo_swap":
        palette = sorted(set(v for row in grid.cells for v in row if v != 0))
        if len(palette) == 2:
            a, b = palette
            return Grid([[b if grid.cells[r][c] == a else a if grid.cells[r][c] == b else grid.cells[r][c]
                           for c in range(w)] for r in range(h)])
        return None

    if candidate_name == "lingo_fill":
        fill_colours = set()
        for pair in task.train:
            if pair.input.shape != pair.output.shape:
                continue
            for r in range(pair.input.height):
                for c in range(pair.input.width):
                    if pair.input.cells[r][c] == 0 and pair.output.cells[r][c] != 0:
                        fill_colours.add(pair.output.cells[r][c])
        if len(fill_colours) == 1:
            fill = next(iter(fill_colours))
            return Grid([[fill if grid.cells[r][c] == 0 else grid.cells[r][c]
                           for c in range(w)] for r in range(h)])
        return None

    if candidate_name == "lingo_crop_centre":
        for pair in task.train:
            oh, ow = pair.output.height, pair.output.width
            if oh <= h and ow <= w:
                r_off = (h - oh) // 2
                c_off = (w - ow) // 2
                return Grid([[grid.cells[r_off + r][c_off + c] for c in range(ow)] for r in range(oh)])
        return None

    if candidate_name == "lingo_crop_tl":
        for pair in task.train:
            oh, ow = pair.output.height, pair.output.width
            if oh <= h and ow <= w:
                return Grid([[grid.cells[r][c] for c in range(ow)] for r in range(oh)])
        return None

    return None


def verify_lingo_candidate(task: ARCTask, candidate_name: str) -> bool:
    """Verify a Lingo candidate on train pairs."""
    checked = 0
    for pair in task.train:
        if pair.input.shape != pair.output.shape:
            continue
        result = apply_lingo_to_grid(task, candidate_name, pair.input)
        if result is None or result.cells != pair.output.cells:
            return False
        checked += 1
    return checked > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Semantic Report — The Mind's "Inner Monologue"
# ═══════════════════════════════════════════════════════════════════════════════

def semantic_report(task: ARCTask) -> str:
    """Generate the mind's 'inner monologue' about a task."""
    desc = describe_transformation(task)

    lines = [
        f"═══ Semantic Report: {task.name} ═══",
        f"",
        f"What I see:",
        f"  {desc.description}",
        f"",
        f"Lingo operations:",
    ]
    for op in desc.operations:
        lines.append(f"  • {op} ({LINGO_TO_HUMAN.get(op, '?')})")

    if desc.layers_affected:
        lines.append(f"")
        lines.append(f"Layers affected:")
        for layer, details in desc.layers_affected.items():
            for detail in details:
                lines.append(f"  [{layer}] {detail}")

    lines.append(f"")
    lines.append(f"Settlement: {desc.settlement}")
    lines.append(f"Confidence: {desc.confidence:.2f}")

    if not desc.consistent:
        lines.append(f"")
        lines.append(f"⚠ Inconsistencies:")
        for inc in desc.inconsistencies:
            lines.append(f"  • {inc}")

    return "\n".join(lines)
