"""
phi_grammar_arc.py — extended Φ-grammar candidate generator with R(n) integration
====================================================================================

Implements the v2 study's §4.3 extended Φ-grammar:

  k          Spatial Arithmetic R(n) = 1/(2·sin(π/n)) — the spatial-log primitive
             (replaces the v1 scalar k ∈ {0, 3, 6, ..., 24})
  arm        det | sto
             (deterministic parameter derivation vs stochastic seed)
  layer      Mirrors | Information | Activation | Potential
             (the 4 MOG_CATEGORIES quadrants — determines which DSL op family)
  C          OPCODE_TABLE (MUL=3, ADD=4, SUB=5, DIV=6)
             + MODIFIER_TABLE (ID, SQUARE, NEGATE, RECIP, ABS)
             (9 entries — replaces the v1 integer prefix set)
  correction none | shear_1 | shear_2 | refined_nrci(α, v_grid)
             (applied at rank-time by nrci_rank.py)

The grammar maps each (k, arm, layer, C, correction) tuple to a DSL Program
by:
  1. R(n) determines the geometric magnitude (rotation angle, count, scale)
  2. layer determines the DSL operator family (Mirrors→recolour, Activation→
     geometric, Information→count, Potential→set ops)
  3. C picks the specific operation within that family
  4. arm determines whether parameters are deterministic or seeded-random
  5. correction is passed through to the ranker (no effect on the program itself)

The scalar k used in Y^k computation (for downstream UBP formula
compatibility) is recovered as:
  k_scalar = radius_to_value(R(n)) mod 24

This preserves the existing clock-cycle semantics while gaining the
spatial-logarithmic expressiveness of R(n).

Usage:
    from phi_grammar_arc import PhiGrammar
    grammar = PhiGrammar(max_program_length=2)
    candidates = grammar.generate(task)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Set, Dict, Any, Iterator, Optional, Tuple
import itertools
import math
import random
import sys, os

# Make vendored dependencies importable
_VENDOR_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vendor")
if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)

# Make arc_loader, encoder, dsl importable
_PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from arc_loader import Grid, ARCTask
from dsl import Ops, Operation, Program

# Import the live Spatial Arithmetic primitives — NO simplification
from spatial_arithmetic_compat import (
    value_to_radius, radius_to_value, encode, decode,
    OPCODE_TABLE, MODIFIER_TABLE,
    pairwise_centroid_distance, dihedral_angle, decode_modifier,
    natural_add, natural_divide, build_scene, observe_scene,
)


# ══════════════════════════════════════════════════════════════════════════════
# Φ-GRAMMAR PARAMETERS — the 5-tuple (k, arm, layer, C, correction)
# ══════════════════════════════════════════════════════════════════════════════

# The n-values whose R(n) we'll use as k-parameters.
# These are the polygon vertex counts that map to useful spatial magnitudes.
# Per the v2 study §4.3: n ∈ [4, 32] gives 28 spatial-k values.
N_VALUES: List[int] = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 18, 20, 24, 28, 30, 32]

# Compute R(n) for each n — these become our k-parameters
K_SPATIAL: List[float] = [value_to_radius(n) for n in N_VALUES]

# Map R(n) → scalar k (mod 24) for downstream UBP Y^k compatibility
K_SCALAR: List[int] = [radius_to_value(r) % 24 for r in K_SPATIAL]

# Arms
ARMS: List[str] = ["det", "sto"]

# Layers — the 4 MOG_CATEGORIES quadrants
LAYERS: List[str] = ["Mirrors", "Information", "Activation", "Potential"]

# C-prefixes — the 9 Spatial Arithmetic operations
# (4 OPCODE_TABLE entries + 5 MODIFIER_TABLE entries)
OPCODE_NAMES: List[str] = [OPCODE_TABLE[k][0] for k in sorted(OPCODE_TABLE.keys())]
MODIFIER_NAMES: List[str] = [v[0] for v in MODIFIER_TABLE.values()]
C_PREFIXES: List[str] = OPCODE_NAMES + MODIFIER_NAMES  # 9 entries

# Corrections
CORRECTIONS: List[str] = ["none", "shear_1", "shear_2", "refined_nrci"]


@dataclass(frozen=True)
class PhiTuple:
    """A single point in the Φ-grammar's 5-dimensional parameter space."""
    n: int                    # the polygon vertex count (k = R(n))
    arm: str                  # "det" or "sto"
    layer: str                # one of LAYERS
    c_prefix: str             # one of C_PREFIXES
    correction: str           # one of CORRECTIONS

    @property
    def k_spatial(self) -> float:
        return value_to_radius(self.n)

    @property
    def k_scalar(self) -> int:
        return radius_to_value(self.k_spatial) % 24

    def __repr__(self):
        return f"Φ(n={self.n}, k=R(n)={self.k_spatial:.3f}, arm={self.arm}, layer={self.layer}, C={self.c_prefix}, corr={self.correction})"


# ══════════════════════════════════════════════════════════════════════════════
# Φ → DSL MAPPING — how a PhiTuple becomes a Program
# ══════════════════════════════════════════════════════════════════════════════

# The layer determines which DSL op family we draw from.
# Each (layer, C) pair maps to a DSL Ops enum + a parameter-derivation function.

def _derive_recolour_params(task: ARCTask, phi: PhiTuple) -> Dict[str, Any]:
    """Mirrors layer: recolour operations. C determines the recolour pattern."""
    palette = sorted(_task_palette(task))
    if not palette:
        return {"mapping": {}}
    c = phi.c_prefix
    if c == "ID":
        return {"mapping": {}}  # no-op
    if c == "NEGATE":
        # Swap pairs of colours (1↔2, 3↔4, ...)
        mapping = {}
        for i in range(0, len(palette) - 1, 2):
            mapping[palette[i]] = palette[i + 1]
            mapping[palette[i + 1]] = palette[i]
        return {"mapping": mapping}
    if c == "SQUARE":
        # Each colour → itself squared mod 10 (a "compounding" recolour)
        return {"mapping": {x: (x * x) % 10 for x in palette if x > 0}}
    if c == "RECIP":
        # Each colour → (10 // x) mod 10, clamped to [1, 9] (inverse, palette-safe)
        return {"mapping": {x: max(1, min(9, (10 // x) % 10)) if x > 0 else x for x in palette}}
    if c == "ABS":
        # Each colour → abs(x - 5) (mirror around 5)
        return {"mapping": {x: abs(x - 5) for x in palette if x > 0}}
    if c == "ADD":
        # Shift each colour up by 1 (mod 10, skip 0)
        return {"mapping": {x: (x % 9) + 1 for x in palette if x > 0}}
    if c == "SUB":
        # Shift each colour down by 1
        return {"mapping": {x: ((x - 2) % 9) + 1 for x in palette if x > 0}}
    if c == "MUL":
        # Double each colour (mod 10)
        return {"mapping": {x: (x * 2) % 10 for x in palette if x > 0}}
    if c == "DIV":
        # Halve each colour (integer division)
        return {"mapping": {x: max(1, x // 2) for x in palette if x > 0}}
    return {"mapping": {}}


def _derive_count_params(task: ARCTask, phi: PhiTuple) -> Dict[str, Any]:
    """Information layer: count and replicate operations. C determines the count pattern."""
    c = phi.c_prefix
    n = phi.n  # use the polygon vertex count directly as the count
    if c in ("ID", "ABS"):
        return {"count": n, "axis": "h", "step": 0}
    if c == "ADD":
        return {"count": n + 1, "axis": "h", "step": 0}
    if c == "SUB":
        return {"count": max(1, n - 1), "axis": "h", "step": 0}
    if c == "MUL":
        return {"count": n * 2, "axis": "h", "step": 0}
    if c == "DIV":
        return {"count": max(1, n // 2), "axis": "h", "step": 0}
    if c == "SQUARE":
        return {"count": n * n, "axis": "h", "step": 0}
    if c == "NEGATE":
        return {"count": n, "axis": "v", "step": 0}  # flip axis
    if c == "RECIP":
        return {"count": max(1, 8 // n), "axis": "h", "step": 1}
    return {"count": n, "axis": "h", "step": 0}


def _derive_geometric_params(task: ARCTask, phi: PhiTuple) -> Dict[str, Any]:
    """Activation layer: geometric transforms. C determines the transform."""
    c = phi.c_prefix
    n = phi.n
    # The polygon vertex count n maps to a rotation: n=4 → 90°, n=6 → 60°, etc.
    # But ARC grids only really support 90° increments, so we quantise.
    if c == "ID":
        return {"_rotation_index": 0}
    # For rotations, use n mod 4 to pick angle
    if c in ("ADD", "MUL"):
        return {"_rotation_index": (n % 4)}  # 0=90°, 1=180°, 2=270°, 3=360°=identity
    if c in ("SUB", "DIV"):
        return {"_rotation_index": (-n) % 4}
    return {"_rotation_index": (n % 4)}


def _derive_set_params(task: ARCTask, phi: PhiTuple) -> Dict[str, Any]:
    """Potential layer: set operations. C determines the set op."""
    palette = sorted(_task_palette(task))
    if len(palette) < 2:
        return {"with_colour": 1, "by_colour": 2, "from_colour": 1, "c1": 1, "c2": 2, "into_colour": 1}
    c1, c2 = palette[0], palette[1]
    c = phi.c_prefix
    if c == "ID":
        return {"with_colour": c1, "by_colour": c2, "from_colour": c1, "by_colour": c2,
                "c1": c1, "c2": c2, "into_colour": c1}
    if c in ("ADD", "MUL"):
        return {"with_colour": c1, "by_colour": c2, "from_colour": c1, "by_colour": c2,
                "c1": c1, "c2": c2, "into_colour": c1}
    if c in ("SUB", "DIV"):
        return {"with_colour": c2, "by_colour": c1, "from_colour": c2, "by_colour": c1,
                "c1": c2, "c2": c1, "into_colour": c2}
    return {"with_colour": c1, "by_colour": c2, "from_colour": c1, "by_colour": c2,
            "c1": c1, "c2": c2, "into_colour": c1}


def _task_palette(task: ARCTask) -> Set[int]:
    """All non-zero colours appearing anywhere in the task."""
    pal = set()
    for p in task.train:
        pal |= p.input.palette()
        pal |= p.output.palette()
    for t in task.test:
        pal |= t.input.palette()
    return pal


# Layer → (op family, param derivator)
LAYER_DISPATCH: Dict[str, Tuple[List[Ops], Any]] = {
    "Mirrors":    ([Ops.RECOLOUR, Ops.RECOLOUR_BG, Ops.RECOLOUR_NONZERO,
                    Ops.RECOLOUR_INTERIOR, Ops.RECOLOUR_IF_NEIGHBOUR,
                    Ops.RECOLOUR_IF_BORDER, Ops.RECOLOUR_IF_CORNER,
                    Ops.FILL_INTERIOR_AUTO], _derive_recolour_params),
    "Information":([Ops.REPLICATE, Ops.COUNT_FILL, Ops.TILE_2X, Ops.TILE_3X,
                    Ops.EXTRACT_LARGEST, Ops.EXTRACT_COLOUR], _derive_count_params),
    "Activation": ([Ops.ROTATE_90, Ops.ROTATE_180, Ops.ROTATE_270,
                    Ops.FLIP_H, Ops.FLIP_V, Ops.TRANSPOSE,
                    Ops.GRAVITY_DOWN, Ops.GRAVITY_UP, Ops.GRAVITY_LEFT, Ops.GRAVITY_RIGHT,
                    Ops.CROP_TO_NONZERO, Ops.SCALE_2X, Ops.SCALE_HALF,
                    Ops.DILATE, Ops.ERODE,
                    Ops.SHIFT_ROW, Ops.SHIFT_COL,
                    Ops.FILL_ROW, Ops.FILL_COL, Ops.COPY_ROW, Ops.COPY_COL,
                    Ops.DRAW_LINE, Ops.DRAW_RECT_OUTLINE, Ops.DRAW_RECT_FILL], _derive_geometric_params),
    "Potential":  ([Ops.SET_INTERSECT, Ops.SET_DIFFERENCE, Ops.SET_UNION,
                    Ops.FILL_INTERIOR, Ops.OUTLINE], _derive_set_params),
}


def phi_to_operation(phi: PhiTuple, task: ARCTask) -> Optional[Operation]:
    """Map a PhiTuple to a DSL Operation. Returns None if no valid mapping."""
    if phi.layer not in LAYER_DISPATCH:
        return None
    op_family, param_fn = LAYER_DISPATCH[phi.layer]
    params = param_fn(task, phi)

    # Pick the specific op from the family based on C
    c = phi.c_prefix
    if phi.layer == "Activation":
        # Activation layer: use n to pick from rotations, flips, gravity, scale, crop
        # The polygon vertex count n determines the geometric "magnitude"
        # n mod 9 picks from the 9 activation ops (rotations, flips, gravity, etc.)
        rot_idx = params.pop("_rotation_index", 0)
        # Map (c_prefix, n) to specific ops
        # The 9 c_prefixes map to 9 op families within Activation:
        #   ID → identity, ADD → rotate, MUL → scale, SUB → flip, DIV → transpose
        #   NEGATE → gravity, SQUARE → dilate, RECIP → erode, ABS → crop
        if c == "ID":
            return Operation(Ops.IDENTITY)
        if c == "ADD":
            rotations = [Ops.ROTATE_90, Ops.ROTATE_180, Ops.ROTATE_270, Ops.IDENTITY]
            return Operation(rotations[rot_idx])
        if c == "MUL":
            return Operation(Ops.SCALE_2X)
        if c == "SUB":
            flips = [Ops.FLIP_H, Ops.FLIP_V, Ops.TRANSPOSE, Ops.IDENTITY]
            return Operation(flips[rot_idx])
        if c == "DIV":
            return Operation(Ops.SCALE_HALF)
        if c == "NEGATE":
            # Gravity ops — n mod 4 picks direction
            gravities = [Ops.GRAVITY_DOWN, Ops.GRAVITY_UP, Ops.GRAVITY_LEFT, Ops.GRAVITY_RIGHT]
            return Operation(gravities[phi.n % 4])
        if c == "SQUARE":
            return Operation(Ops.DILATE)
        if c == "RECIP":
            return Operation(Ops.ERODE)
        if c == "ABS":
            return Operation(Ops.CROP_TO_NONZERO)
        return Operation(op_family[0])
    elif phi.layer == "Information":
        if c in ("ID", "ADD", "MUL"):
            return Operation(Ops.REPLICATE, params)
        if c in ("SUB", "DIV", "SQUARE", "RECIP", "NEGATE", "ABS"):
            return Operation(Ops.COUNT_FILL)
        return Operation(Ops.REPLICATE, params)
    elif phi.layer == "Mirrors":
        # Mirrors layer: v0.4 expanded — 9 c_prefixes map to 9 recolour variants
        # The recolour params (mapping) are already derived by _derive_recolour_params
        if c == "ID":
            return Operation(Ops.RECOLOUR, params)
        if c == "NEGATE":
            # swap-colours recolour (the v0.2 default)
            return Operation(Ops.RECOLOUR, params)
        if c == "SQUARE":
            # fill interior auto (compound recolour)
            return Operation(Ops.FILL_INTERIOR_AUTO, params)
        if c == "RECIP":
            # recolour interior
            new_c = next(iter(params.get("mapping", {}).values()), 1) if params.get("mapping") else 1
            return Operation(Ops.RECOLOUR_INTERIOR, {"new_colour": new_c})
        if c == "ABS":
            # recolour background
            new_c = next(iter(params.get("mapping", {}).values()), 1) if params.get("mapping") else 1
            return Operation(Ops.RECOLOUR_BG, {"new_colour": new_c})
        if c == "ADD":
            # recolour all nonzero to one colour
            new_c = next(iter(params.get("mapping", {}).values()), 1) if params.get("mapping") else 1
            return Operation(Ops.RECOLOUR_NONZERO, {"new_colour": new_c})
        if c == "SUB":
            # recolour if neighbour — use palette colours
            palette = sorted(_task_palette(task))
            if len(palette) >= 2:
                return Operation(Ops.RECOLOUR_IF_NEIGHBOUR, {
                    "target_colour": 0,
                    "neighbour_colour": palette[0],
                    "new_colour": palette[1],
                })
            return Operation(Ops.RECOLOUR, params)
        if c == "MUL":
            # recolour border cells
            new_c = next(iter(params.get("mapping", {}).values()), 1) if params.get("mapping") else 1
            return Operation(Ops.RECOLOUR_IF_BORDER, {"new_colour": new_c, "target_colour": 0})
        if c == "DIV":
            # recolour corners
            new_c = next(iter(params.get("mapping", {}).values()), 1) if params.get("mapping") else 1
            return Operation(Ops.RECOLOUR_IF_CORNER, {"new_colour": new_c})
        return Operation(Ops.RECOLOUR, params)
    elif phi.layer == "Potential":
        if c in ("ID", "ADD", "MUL"):
            return Operation(Ops.SET_INTERSECT, params)
        if c in ("SUB", "DIV"):
            return Operation(Ops.SET_DIFFERENCE, params)
        if c == "SQUARE":
            return Operation(Ops.SET_UNION, params)
        if c == "NEGATE":
            return Operation(Ops.OUTLINE)
        if c == "RECIP":
            return Operation(Ops.FILL_INTERIOR, params)
        if c == "ABS":
            return Operation(Ops.SET_INTERSECT, params)
        return Operation(Ops.SET_INTERSECT, params)
    return None


def phi_to_program(phi_tuple: PhiTuple, task: ARCTask) -> Optional[Program]:
    """Convert a single PhiTuple to a 1-op Program."""
    op = phi_to_operation(phi_tuple, task)
    if op is None:
        return None
    return Program(operations=[op], name=f"phi_{hash(phi_tuple) & 0xFFFFFF:06x}")


# ══════════════════════════════════════════════════════════════════════════════
# PHI GRAMMAR — the main generator
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PhiGrammar:
    """The extended Φ-grammar candidate generator.

    Generates Programs by enumerating (k, arm, layer, C, correction) tuples
    and mapping each to a DSL program via phi_to_operation.

    Parameters
    ----------
    max_program_length : int
        Maximum number of operations per program. Default 2.
        Length-1: each PhiTuple → 1 Program
        Length-2: each pair of PhiTuples → 1 Program (composition)
    include_stochastic : bool
        If True (default), include arm=sto candidates. If False, det only.
    deduplicate : bool
        If True (default), skip programs with identical op-signatures.
    """
    max_program_length: int = 2
    include_stochastic: bool = True
    deduplicate: bool = True

    def _enum_phi_tuples(self) -> Iterator[PhiTuple]:
        """Enumerate all PhiTuples in the grammar's parameter space."""
        arms = ARMS if self.include_stochastic else ["det"]
        for n in N_VALUES:
            for arm in arms:
                for layer in LAYERS:
                    for c in C_PREFIXES:
                        for correction in CORRECTIONS:
                            yield PhiTuple(n=n, arm=arm, layer=layer,
                                           c_prefix=c, correction=correction)

    def generate(self, task: ARCTask) -> List[Program]:
        """Generate all candidate Programs for the task."""
        # Stage 1: enumerate all length-1 programs
        length1: List[Program] = []
        seen_signatures: Set[tuple] = set()

        def _freeze(v):
            if isinstance(v, dict):
                return tuple(sorted((k, _freeze(val)) for k, val in v.items()))
            if isinstance(v, (list, tuple)):
                return tuple(_freeze(x) for x in v)
            return v

        def _sig(ops: List[Operation]) -> tuple:
            return tuple((o.op.value, _freeze(o.params)) for o in ops)

        def _add(ops: List[Operation], source: str = ""):
            if self.deduplicate:
                s = _sig(ops)
                if s in seen_signatures:
                    return
                seen_signatures.add(s)
            length1.append(Program(operations=ops, name=f"{source}_p{len(length1):04d}"))

        for phi in self._enum_phi_tuples():
            op = phi_to_operation(phi, task)
            if op is not None:
                _add([op], source=f"phi_n{phi.n}_{phi.layer}_{phi.c_prefix}")

        if self.max_program_length == 1:
            return length1

        # Stage 2: enumerate length-2 programs (compositions)
        # Restrict to avoid combinatorial explosion: only compose operations
        # from DIFFERENT layers (this captures the "rotate then recolour" pattern
        # without generating every trivial composition)
        length2: List[Program] = []
        # Group length-1 ops by layer for cross-layer composition
        by_layer: Dict[str, List[Operation]] = {"Mirrors": [], "Information": [],
                                                  "Activation": [], "Potential": []}
        for prog in length1:
            op = prog.operations[0]
            # Determine which layer this op belongs to
            for layer, (op_family, _) in LAYER_DISPATCH.items():
                if op.op in op_family:
                    by_layer[layer].append(op)
                    break

        for layer_a, ops_a in by_layer.items():
            for layer_b, ops_b in by_layer.items():
                if layer_a == layer_b:
                    continue  # skip same-layer compositions
                # Cap the number of cross-layer compositions to avoid blowup
                for op_a in ops_a[:30]:  # cap at 30 per layer
                    for op_b in ops_b[:30]:
                        s = _sig([op_a, op_b])
                        if s in seen_signatures:
                            continue
                        seen_signatures.add(s)
                        length2.append(Program(
                            operations=[op_a, op_b],
                            name=f"comp_{layer_a[:2]}_{layer_b[:2]}_p{len(length2):04d}",
                        ))

        return length1 + length2


def generate_candidates(task: ARCTask, max_program_length: int = 2,
                        include_stochastic: bool = True) -> List[Program]:
    """Convenience function — see PhiGrammar."""
    gen = PhiGrammar(max_program_length=max_program_length,
                     include_stochastic=include_stochastic)
    return gen.generate(task)


# ══════════════════════════════════════════════════════════════════════════════
# GRAMMAR STATS — for debugging and gate reports
# ══════════════════════════════════════════════════════════════════════════════

def grammar_size(include_stochastic: bool = True) -> Dict[str, int]:
    """Report the size of the Φ-grammar's parameter space."""
    arms = 2 if include_stochastic else 1
    return {
        "n_values": len(N_VALUES),
        "arms": arms,
        "layers": len(LAYERS),
        "c_prefixes": len(C_PREFIXES),
        "corrections": len(CORRECTIONS),
        "total_phi_tuples": len(N_VALUES) * arms * len(LAYERS) * len(C_PREFIXES) * len(CORRECTIONS),
    }
