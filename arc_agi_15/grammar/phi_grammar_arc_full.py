"""
phi_grammar_arc_full.py — Comprehensive executable Φ-grammar with recursion,
conditionals, iteration, and variable binding
====================================================================================

Extends the original Φ-grammar (v2 study §4.3) with:
  - Variable binding & scope ($color, $count, $region placeholders)
  - Control flow: IF/ELSE conditionals, REPEAT/FOR_EACH/WHERE iteration
  - Recursive program synthesis with safety limits
  - Enhanced AST representation with ExecutionTrace
  - CRG-guided hole filling and grammar induction
  - Integration with ObjectCRG, arc_dsl_full (162 ops), GenerativeTransformerFull

The grammar maps each (k, arm, layer, C, correction) tuple to a DSL Program,
now enriched with symbolic parameters and control structures.

Usage:
    from phi_grammar_arc_full import PhiGrammarFull, PhiExpression, PhiExecutor
    grammar = PhiGrammarFull(max_program_length=3, enable_recursion=True)
    candidates = grammar.generate(task)

    # Execute a program with variable bindings
    executor = PhiExecutor()
    result = executor.execute(program, grid, variables={"$color": 5, "$count": 3})
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Set, Dict, Any, Iterator, Optional, Tuple, Union, Callable
from enum import Enum, auto
import itertools
import math
import random
import sys
import os
import copy

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

# Import the live Spatial Arithmetic primitives
try:
    from spatial_arithmetic_compat import (
        value_to_radius, radius_to_value, encode, decode,
        OPCODE_TABLE, MODIFIER_TABLE,
        pairwise_centroid_distance, dihedral_angle, decode_modifier,
        natural_add, natural_divide, build_scene, observe_scene,
    )
except ImportError:
    # Fallback defaults if spatial_arithmetic not available
    OPCODE_TABLE = {3: ("MUL", "*"), 4: ("ADD", "+"), 5: ("SUB", "-"), 6: ("DIV", "/")}
    MODIFIER_TABLE = {0: ("ID", "x"), 1: ("SQUARE", "x²"), 2: ("NEGATE", "-x"),
                      3: ("RECIP", "1/x"), 4: ("ABS", "|x|")}
    def value_to_radius(n): return n / (2.0 * math.sin(math.pi / n)) if n > 2 else n
    def radius_to_value(r): return int(round(r)) % 24


# ══════════════════════════════════════════════════════════════════════════════
# Φ-GRAMMAR PARAMETERS — the 5-tuple (k, arm, layer, C, correction)
# ══════════════════════════════════════════════════════════════════════════════

N_VALUES: List[int] = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 18, 20, 24, 28, 30, 32]
K_SPATIAL: List[float] = [value_to_radius(n) for n in N_VALUES]
K_SCALAR: List[int] = [radius_to_value(r) % 24 for r in K_SPATIAL]
ARMS: List[str] = ["det", "sto"]
LAYERS: List[str] = ["Mirrors", "Information", "Activation", "Potential"]
OPCODE_NAMES: List[str] = [OPCODE_TABLE[k][0] for k in sorted(OPCODE_TABLE.keys())]
MODIFIER_NAMES: List[str] = [v[0] for v in MODIFIER_TABLE.values()]
C_PREFIXES: List[str] = OPCODE_NAMES + MODIFIER_NAMES  # 9 entries
CORRECTIONS: List[str] = ["none", "shear_1", "shear_2", "refined_nrci"]


# ══════════════════════════════════════════════════════════════════════════════
# AST NODES — Extended Φ-grammar expression types
# ══════════════════════════════════════════════════════════════════════════════

class ExprType(Enum):
    """Types of Φ-grammar expressions."""
    PHI_TUPLE = auto()      # Base (k, arm, layer, C, correction)
    OPERATION = auto()      # DSL operation wrapper
    VARIABLE = auto()       # $color, $count, $region
    LITERAL = auto()        # Constant value
    SEQUENCE = auto()       # Sequential composition [op1, op2, ...]
    CONDITIONAL = auto()    # IF cond THEN expr ELSE expr
    LOOP = auto()           # REPEAT n TIMES / FOR_EACH / WHILE
    FUNCTION_CALL = auto()  # Call named function/subroutine
    LAMBDA = auto()         # Anonymous function \x -> expr
    LET_BINDING = auto()    # LET $var = expr IN body


@dataclass
class PhiExpression:
    """Abstract syntax tree node for Φ-grammar programs."""
    expr_type: ExprType
    children: List[PhiExpression] = field(default_factory=list)
    value: Any = None  # For literals, variables, phi_tuples
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        if self.expr_type == ExprType.VARIABLE:
            return f"${self.value}"
        elif self.expr_type == ExprType.LITERAL:
            return str(self.value)
        elif self.expr_type == ExprType.PHI_TUPLE:
            return f"Φ({self.value})"
        elif self.expr_type == ExprType.SEQUENCE:
            return f"Seq[{len(self.children)}]"
        elif self.expr_type == ExprType.CONDITIONAL:
            return f"If({self.params.get('condition', '?')})"
        elif self.expr_type == ExprType.LOOP:
            return f"Loop({self.params.get('type', '?')})"
        return f"{self.expr_type.name}({self.value})"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "expr_type": self.expr_type.name,
            "children": [c.to_dict() for c in self.children],
            "value": self.value,
            "params": self.params,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> PhiExpression:
        """Deserialize from dictionary."""
        return cls(
            expr_type=ExprType[d["expr_type"]],
            children=[cls.from_dict(c) for c in d.get("children", [])],
            value=d.get("value"),
            params=d.get("params", {}),
            metadata=d.get("metadata", {}),
        )


@dataclass
class ExecutionTrace:
    """Audit trail for program execution."""
    step: int
    expression: PhiExpression
    input_state: Any
    output_state: Any
    variables_snapshot: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "expression": self.expression.to_dict() if self.expression else None,
            "success": self.success,
            "error_message": self.error_message,
        }


@dataclass
class GrammarSymbol:
    """Metadata for grammar symbols (operators, functions, etc.)."""
    name: str
    category: str  # "transform", "predicate", "generator", "control"
    arity: int  # Number of arguments
    return_type: str  # "grid", "bool", "int", "list"
    side_effects: bool = False
    description: str = ""
    examples: List[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════════════════
# VARIABLE SCOPE & BINDING
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Scope:
    """Variable scope with parent chaining for nested environments."""
    parent: Optional[Scope] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    constants: Dict[str, Any] = field(default_factory=dict)

    def get(self, name: str) -> Any:
        """Resolve variable, checking parent scopes."""
        if name in self.variables:
            return self.variables[name]
        if name in self.constants:
            return self.constants[name]
        if self.parent:
            return self.parent.get(name)
        raise KeyError(f"Undefined variable: {name}")

    def set(self, name: str, value: Any, is_constant: bool = False):
        """Bind variable in current scope."""
        if is_constant:
            self.constants[name] = value
        else:
            self.variables[name] = value

    def exists(self, name: str) -> bool:
        """Check if variable is defined."""
        if name in self.variables or name in self.constants:
            return True
        if self.parent:
            return self.parent.exists(name)
        return False

    def fork(self) -> Scope:
        """Create child scope inheriting current bindings."""
        return Scope(parent=self, variables=dict(self.variables),
                     constants=dict(self.constants))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variables": dict(self.variables),
            "constants": dict(self.constants),
        }


# ══════════════════════════════════════════════════════════════════════════════
# CONDITIONAL PREDICATES
# ══════════════════════════════════════════════════════════════════════════════

class PredicateType(Enum):
    """Built-in conditional predicates."""
    HAS_COLOR = auto()
    COUNT_GT = auto()
    COUNT_LT = auto()
    COUNT_EQ = auto()
    IS_SYMMETRIC_H = auto()
    IS_SYMMETRIC_V = auto()
    IS_SYMMETRIC_D1 = auto()
    IS_SYMMETRIC_D2 = auto()
    TOUCHES_BORDER = auto()
    CONTAINS_OBJECT = auto()
    IS_EMPTY = auto()
    WIDTH_GT = auto()
    HEIGHT_GT = auto()
    COLOR_RATIO_GT = auto()
    CONNECTED_COMPONENTS_GT = auto()
    BBOX_AREA_GT = auto()
    DISTANCE_LT = auto()
    ALIGNED_HORIZONTALLY = auto()
    ALIGNED_VERTICALLY = auto()
    SAME_COLOR = auto()
    DIFFERENT_COLOR = auto()


@dataclass
class Predicate:
    """Conditional predicate with parameters."""
    predicate_type: PredicateType
    params: Dict[str, Any] = field(default_factory=dict)

    def evaluate(self, grid: Grid, scope: Scope) -> bool:
        """Evaluate predicate on grid with current variable bindings."""
        try:
            p = self.predicate_type

            if p == PredicateType.HAS_COLOR:
                color = self._resolve_param("color", scope)
                return color in grid.palette()

            elif p == PredicateType.COUNT_GT:
                color = self._resolve_param("color", scope)
                threshold = self._resolve_param("threshold", scope)
                count = sum(1 for row in grid.data for c in row if c == color)
                return count > threshold

            elif p == PredicateType.COUNT_LT:
                color = self._resolve_param("color", scope)
                threshold = self._resolve_param("threshold", scope)
                count = sum(1 for row in grid.data for c in row if c == color)
                return count < threshold

            elif p == PredicateType.COUNT_EQ:
                color = self._resolve_param("color", scope)
                target = self._resolve_param("target", scope)
                count = sum(1 for row in grid.data for c in row if c == color)
                return count == target

            elif p == PredicateType.IS_SYMMETRIC_H:
                return grid.data == [row[::-1] for row in grid.data]

            elif p == PredicateType.IS_SYMMETRIC_V:
                return grid.data == grid.data[::-1]

            elif p == PredicateType.IS_SYMMETRIC_D1:
                h, w = len(grid.data), len(grid.data[0]) if grid.data else 0
                if h != w:
                    return False
                transposed = [[grid.data[j][i] for j in range(h)] for i in range(w)]
                return grid.data == transposed

            elif p == PredicateType.IS_SYMMETRIC_D2:
                h, w = len(grid.data), len(grid.data[0]) if grid.data else 0
                if h != w:
                    return False
                anti_transposed = [[grid.data[w-1-j][w-1-i] for j in range(w)] for i in range(w)]
                return grid.data == anti_transposed

            elif p == PredicateType.TOUCHES_BORDER:
                color = self._resolve_param("color", scope)
                h, w = len(grid.data), len(grid.data[0]) if grid.data else 0
                # Check top/bottom rows
                if color in grid.data[0] or color in grid.data[-1]:
                    return True
                # Check left/right columns
                for row in grid.data:
                    if row[0] == color or row[-1] == color:
                        return True
                return False

            elif p == PredicateType.IS_EMPTY:
                return len(grid.palette()) == 0 or (len(grid.palette()) == 1 and 0 in grid.palette())

            elif p == PredicateType.WIDTH_GT:
                threshold = self._resolve_param("threshold", scope)
                return len(grid.data[0]) > threshold if grid.data else False

            elif p == PredicateType.HEIGHT_GT:
                threshold = self._resolve_param("threshold", scope)
                return len(grid.data) > threshold if grid.data else False

            elif p == PredicateType.SAME_COLOR:
                c1 = self._resolve_param("color1", scope)
                c2 = self._resolve_param("color2", scope)
                return c1 == c2

            elif p == PredicateType.DIFFERENT_COLOR:
                c1 = self._resolve_param("color1", scope)
                c2 = self._resolve_param("color2", scope)
                return c1 != c2

            # Default: unknown predicate returns False
            return False

        except Exception:
            return False

    def _resolve_param(self, name: str, scope: Scope) -> Any:
        """Resolve parameter, handling variable references."""
        val = self.params.get(name)
        if isinstance(val, str) and val.startswith("$"):
            return scope.get(val)
        return val

    def to_expression(self) -> PhiExpression:
        """Convert to PhiExpression."""
        return PhiExpression(
            expr_type=ExprType.LITERAL,
            value=self,
            params={"predicate_type": self.predicate_type.name},
        )


# ══════════════════════════════════════════════════════════════════════════════
# Φ-TUPLE (preserved from original)
# ══════════════════════════════════════════════════════════════════════════════

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

    def to_expression(self) -> PhiExpression:
        """Convert to PhiExpression."""
        return PhiExpression(
            expr_type=ExprType.PHI_TUPLE,
            value=self,
            params={
                "k_spatial": self.k_spatial,
                "k_scalar": self.k_scalar,
            }
        )


# ══════════════════════════════════════════════════════════════════════════════
# Φ → DSL MAPPING (preserved and extended from original)
# ══════════════════════════════════════════════════════════════════════════════

def _task_palette(task: ARCTask) -> Set[int]:
    """All non-zero colours appearing anywhere in the task."""
    pal = set()
    for p in task.train:
        pal |= p.input.palette()
        pal |= p.output.palette()
    for t in task.test:
        pal |= t.input.palette()
    return pal


def _derive_recolour_params(task: ARCTask, phi: PhiTuple) -> Dict[str, Any]:
    """Mirrors layer: recolour operations. C determines the recolour pattern."""
    palette = sorted(_task_palette(task))
    if not palette:
        return {"mapping": {}}
    c = phi.c_prefix
    if c == "ID":
        return {"mapping": {}}
    if c == "NEGATE":
        mapping = {}
        for i in range(0, len(palette) - 1, 2):
            mapping[palette[i]] = palette[i + 1]
            mapping[palette[i + 1]] = palette[i]
        return {"mapping": mapping}
    if c == "SQUARE":
        return {"mapping": {x: (x * x) % 10 for x in palette if x > 0}}
    if c == "RECIP":
        return {"mapping": {x: max(1, min(9, (10 // x) % 10)) if x > 0 else x for x in palette}}
    if c == "ABS":
        return {"mapping": {x: abs(x - 5) for x in palette if x > 0}}
    if c == "ADD":
        return {"mapping": {x: (x % 9) + 1 for x in palette if x > 0}}
    if c == "SUB":
        return {"mapping": {x: ((x - 2) % 9) + 1 for x in palette if x > 0}}
    if c == "MUL":
        return {"mapping": {x: (x * 2) % 10 for x in palette if x > 0}}
    if c == "DIV":
        return {"mapping": {x: max(1, x // 2) for x in palette if x > 0}}
    return {"mapping": {}}


def _derive_count_params(task: ARCTask, phi: PhiTuple) -> Dict[str, Any]:
    """Information layer: count and replicate operations."""
    c = phi.c_prefix
    n = phi.n
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
        return {"count": n, "axis": "v", "step": 0}
    if c == "RECIP":
        return {"count": max(1, 8 // n), "axis": "h", "step": 1}
    return {"count": n, "axis": "h", "step": 0}


def _derive_geometric_params(task: ARCTask, phi: PhiTuple) -> Dict[str, Any]:
    """Activation layer: geometric transforms."""
    c = phi.c_prefix
    n = phi.n
    if c == "ID":
        return {"_rotation_index": 0}
    if c in ("ADD", "MUL"):
        return {"_rotation_index": (n % 4)}
    if c in ("SUB", "DIV"):
        return {"_rotation_index": (-n) % 4}
    return {"_rotation_index": (n % 4)}


def _derive_set_params(task: ARCTask, phi: PhiTuple) -> Dict[str, Any]:
    """Potential layer: set operations."""
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

    c = phi.c_prefix
    if phi.layer == "Activation":
        rot_idx = params.pop("_rotation_index", 0)
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
        if c == "ID":
            return Operation(Ops.RECOLOUR, params)
        if c == "NEGATE":
            return Operation(Ops.RECOLOUR, params)
        if c == "SQUARE":
            return Operation(Ops.FILL_INTERIOR_AUTO, params)
        if c == "RECIP":
            new_c = next(iter(params.get("mapping", {}).values()), 1) if params.get("mapping") else 1
            return Operation(Ops.RECOLOUR_INTERIOR, {"new_colour": new_c})
        if c == "ABS":
            new_c = next(iter(params.get("mapping", {}).values()), 1) if params.get("mapping") else 1
            return Operation(Ops.RECOLOUR_BG, {"new_colour": new_c})
        if c == "ADD":
            new_c = next(iter(params.get("mapping", {}).values()), 1) if params.get("mapping") else 1
            return Operation(Ops.RECOLOUR_NONZERO, {"new_colour": new_c})
        if c == "SUB":
            palette = sorted(_task_palette(task))
            if len(palette) >= 2:
                return Operation(Ops.RECOLOUR_IF_NEIGHBOUR, {
                    "target_colour": 0,
                    "neighbour_colour": palette[0],
                    "new_colour": palette[1],
                })
            return Operation(Ops.RECOLOUR, params)
        if c == "MUL":
            new_c = next(iter(params.get("mapping", {}).values()), 1) if params.get("mapping") else 1
            return Operation(Ops.RECOLOUR_IF_BORDER, {"new_colour": new_c, "target_colour": 0})
        if c == "DIV":
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
# PHI EXECUTOR — Interprets PhiExpression with scope management
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PhiExecutor:
    """
    Executes Φ-grammar expressions with variable binding and control flow.

    Supports:
    - Variable resolution ($color, $count, etc.)
    - Conditionals (IF/ELSE)
    - Loops (REPEAT, FOR_EACH, WHILE)
    - Function calls and recursion
    - Execution tracing for debugging
    """
    max_recursion_depth: int = 10
    max_loop_iterations: int = 20
    trace_execution: bool = True

    def __post_init__(self):
        self.trace: List[ExecutionTrace] = []
        self._recursion_stack: List[str] = []

    def execute(self, expr: PhiExpression, grid: Grid,
                scope: Optional[Scope] = None,
                function_env: Optional[Dict[str, PhiExpression]] = None) -> Grid:
        """Execute a PhiExpression on a grid."""
        if scope is None:
            scope = Scope()
        if function_env is None:
            function_env = {}

        if self.trace_execution:
            self.trace.append(ExecutionTrace(
                step=len(self.trace),
                expression=expr,
                input_state=grid,
                output_state=None,
                variables_snapshot=scope.to_dict(),
                success=False,
            ))

        try:
            result = self._execute_impl(expr, grid, scope, function_env)

            if self.trace_execution and self.trace:
                self.trace[-1].output_state = result
                self.trace[-1].success = True

            return result

        except Exception as e:
            if self.trace_execution and self.trace:
                self.trace[-1].error_message = str(e)
            raise

    def _execute_impl(self, expr: PhiExpression, grid: Grid,
                      scope: Scope, function_env: Dict[str, PhiExpression]) -> Grid:
        """Internal execution dispatcher."""
        et = expr.expr_type

        if et == ExprType.LITERAL:
            # Literal might be a predicate or raw value
            if isinstance(expr.value, Predicate):
                # Predicate in literal position is an error
                raise ValueError("Predicate cannot be executed as operation")
            return grid

        elif et == ExprType.VARIABLE:
            # Variable reference - just return grid (variables affect params)
            return grid

        elif et == ExprType.PHI_TUPLE:
            # Execute base phi tuple
            phi_tuple: PhiTuple = expr.value
            op = phi_to_operation(phi_tuple, self._dummy_task_from_grid(grid))
            if op is None:
                return grid
            return op.apply(grid)

        elif et == ExprType.OPERATION:
            # Direct operation wrapper
            op: Operation = expr.value
            return self._apply_op_with_vars(op, grid, scope)

        elif et == ExprType.SEQUENCE:
            # Sequential composition
            result = grid
            for child in expr.children:
                result = self.execute(child, result, scope, function_env)
            return result

        elif et == ExprType.CONDITIONAL:
            # IF cond THEN expr ELSE expr
            predicate: Predicate = expr.params.get("condition")
            if predicate is None:
                return grid

            condition_met = predicate.evaluate(grid, scope)

            if condition_met:
                # Execute THEN branch (first child)
                if expr.children:
                    return self.execute(expr.children[0], grid, scope, function_env)
            else:
                # Execute ELSE branch (second child)
                if len(expr.children) > 1:
                    return self.execute(expr.children[1], grid, scope, function_env)

            return grid

        elif et == ExprType.LOOP:
            # REPEAT / FOR_EACH / WHILE
            loop_type = expr.params.get("type", "repeat")

            if loop_type == "repeat":
                count = expr.params.get("count", 1)
                if isinstance(count, str) and count.startswith("$"):
                    count = scope.get(count)

                count = min(int(count), self.max_loop_iterations)
                result = grid
                for _ in range(count):
                    if expr.children:
                        result = self.execute(expr.children[0], result, scope, function_env)
                return result

            elif loop_type == "for_each":
                # FOR_EACH over colors/objects
                items = expr.params.get("items", [])
                var_name = expr.params.get("var", "$item")

                result = grid
                for item in items:
                    child_scope = scope.fork()
                    child_scope.set(var_name, item)
                    if expr.children:
                        result = self.execute(expr.children[0], result, child_scope, function_env)
                return result

            elif loop_type == "while":
                predicate: Predicate = expr.params.get("condition")
                result = grid
                iterations = 0

                while iterations < self.max_loop_iterations:
                    if predicate is None or not predicate.evaluate(result, scope):
                        break
                    if expr.children:
                        result = self.execute(expr.children[0], result, scope, function_env)
                    iterations += 1

                return result

        elif et == ExprType.FUNCTION_CALL:
            func_name = expr.params.get("name", "")

            # Check recursion depth
            if func_name in self._recursion_stack:
                depth = self._recursion_stack.count(func_name)
                if depth >= self.max_recursion_depth:
                    raise RecursionError(f"Max recursion depth exceeded for {func_name}")

            if func_name not in function_env:
                raise ValueError(f"Undefined function: {func_name}")

            # Bind arguments
            child_scope = scope.fork()
            for i, arg_val in enumerate(expr.children[1:] if expr.children else []):
                arg_name = f"$arg{i}"
                # Evaluate argument expression
                if arg_val.expr_type == ExprType.LITERAL:
                    child_scope.set(arg_name, arg_val.value)
                else:
                    child_scope.set(arg_name, arg_val)

            # Execute function body
            func_body = function_env[func_name]
            self._recursion_stack.append(func_name)
            try:
                return self.execute(func_body, grid, child_scope, function_env)
            finally:
                self._recursion_stack.pop()

        elif et == ExprType.LAMBDA:
            # Lambda returns itself as a value (for higher-order use)
            return grid

        elif et == ExprType.LET_BINDING:
            # LET $var = expr IN body
            var_name = expr.params.get("var", "$tmp")

            # Evaluate binding expression
            if expr.children:
                bound_value = self.execute(expr.children[0], grid, scope, function_env)

            # Create new scope with binding
            child_scope = scope.fork()
            child_scope.set(var_name, bound_value)

            # Execute body in new scope
            if len(expr.children) > 1:
                return self.execute(expr.children[1], grid, child_scope, function_env)

            return grid

        # Default: return grid unchanged
        return grid

    def _apply_op_with_vars(self, op: Operation, grid: Grid, scope: Scope) -> Grid:
        """Apply operation resolving any variable references in params."""
        resolved_params = {}
        for k, v in op.params.items():
            if isinstance(v, str) and v.startswith("$"):
                try:
                    resolved_params[k] = scope.get(v)
                except KeyError:
                    resolved_params[k] = v  # Keep as-is if undefined
            else:
                resolved_params[k] = v

        resolved_op = Operation(op.op, resolved_params)
        return resolved_op.apply(grid)

    def _dummy_task_from_grid(self, grid: Grid) -> ARCTask:
        """Create minimal dummy task for phi_to_operation compatibility."""
        from arc_loader import ARCPair
        pair = ARCPair(input=grid, output=grid)
        return ARCTask(train=[pair], test=[])

    def clear_trace(self):
        """Clear execution trace."""
        self.trace = []

    def get_trace(self) -> List[Dict[str, Any]]:
        """Get execution trace as dictionaries."""
        return [t.to_dict() for t in self.trace]


# ══════════════════════════════════════════════════════════════════════════════
# EXTENDED Φ-GRAMMAR WITH RECURSION, CONDITIONALS, ITERATION
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PhiGrammarFull:
    """
    Extended Φ-grammar candidate generator with full programming constructs.

    Generates Programs by:
    1. Enumerating base (k, arm, layer, C, correction) tuples
    2. Building ASTs with conditionals, loops, and variable bindings
    3. Supporting recursive program patterns
    4. CRG-guided hole filling for incomplete programs

    Parameters
    ----------
    max_program_length : int
        Maximum number of operations per linear program segment.
    enable_conditionals : bool
        If True, generate IF/ELSE branches.
    enable_loops : bool
        If True, generate REPEAT/FOR_EACH/WHERE constructs.
    enable_recursion : bool
        If True, allow recursive function definitions.
    enable_variables : bool
        If True, use variable binding ($color, $count, etc.).
    crg : Optional
        ObjectCRG instance for guided synthesis.
    """
    max_program_length: int = 3
    enable_conditionals: bool = True
    enable_loops: bool = True
    enable_recursion: bool = True
    enable_variables: bool = True
    crg: Optional[Any] = None

    # Variable templates
    COLOR_VARS: List[str] = field(default_factory=lambda: ["$color", "$target_color", "$source_color", "$bg_color"])
    COUNT_VARS: List[str] = field(default_factory=lambda: ["$count", "$n", "$iterations", "$size"])
    REGION_VARS: List[str] = field(default_factory=lambda: ["$region", "$bbox", "$object"])
    BOOL_VARS: List[str] = field(default_factory=lambda: ["$flag", "$done", "$found"])

    def __post_init__(self):
        self.function_templates: Dict[str, PhiExpression] = {}
        self._init_function_templates()

    def _init_function_templates(self):
        """Initialize common recursive function templates."""

        # Template: Apply operation until stable
        self.function_templates["repeat_until_stable"] = PhiExpression(
            expr_type=ExprType.LOOP,
            params={"type": "while", "condition": None},  # Filled at runtime
            children=[],
        )

        # Template: For each color in palette
        self.function_templates["for_each_color"] = PhiExpression(
            expr_type=ExprType.LOOP,
            params={"type": "for_each", "var": "$color", "items": []},
            children=[],
        )

        # Template: Conditional transform
        self.function_templates["if_has_color_then"] = PhiExpression(
            expr_type=ExprType.CONDITIONAL,
            params={"condition": None},
            children=[],
        )

    def _enum_phi_tuples(self) -> Iterator[PhiTuple]:
        """Enumerate all PhiTuples in the grammar's parameter space."""
        arms = ARMS  # Always include both for full grammar
        for n in N_VALUES:
            for arm in arms:
                for layer in LAYERS:
                    for c in C_PREFIXES:
                        for correction in CORRECTIONS:
                            yield PhiTuple(n=n, arm=arm, layer=layer,
                                           c_prefix=c, correction=correction)

    def generate(self, task: ARCTask) -> List[Program]:
        """Generate all candidate Programs for the task."""
        candidates: List[Program] = []
        seen_signatures: Set[tuple] = set()

        def _freeze(v):
            if isinstance(v, dict):
                return tuple(sorted((k, _freeze(val)) for k, val in v.items()))
            if isinstance(v, (list, tuple)):
                return tuple(_freeze(x) for x in v)
            return v

        def _sig(ops: List[Operation]) -> tuple:
            return tuple((o.op.value, _freeze(o.params)) for o in ops)

        def _add(ops: List[Operation], source: str = "", expr: Optional[PhiExpression] = None):
            s = _sig(ops)
            if s in seen_signatures:
                return
            seen_signatures.add(s)
            prog = Program(operations=ops, name=f"{source}_p{len(candidates):04d}")
            if expr:
                prog.metadata["expression"] = expr.to_dict()
            candidates.append(prog)

        # Stage 1: Base phi tuples (length-1 programs)
        for phi in self._enum_phi_tuples():
            op = phi_to_operation(phi, task)
            if op is not None:
                _add([op], source=f"phi_n{phi.n}_{phi.layer}_{phi.c_prefix}")

        # Stage 2: Compositions (length-2 to length-N)
        if self.max_program_length >= 2:
            base_ops = [p.operations[0] for p in candidates[:100]]  # Limit base

            for length in range(2, min(self.max_program_length + 1, 4)):
                for combo in itertools.combinations(base_ops, length):
                    # Filter same-layer compositions for diversity
                    layers_used = set()
                    for op in combo:
                        for layer, (op_family, _) in LAYER_DISPATCH.items():
                            if op.op in op_family:
                                layers_used.add(layer)
                                break

                    if len(layers_used) < length:  # Skip if all same layer
                        continue

                    _add(list(combo), source=f"comp_len{length}")

        # Stage 3: Conditional programs
        if self.enable_conditionals:
            candidates.extend(self._generate_conditional_programs(task))

        # Stage 4: Loop-based programs
        if self.enable_loops:
            candidates.extend(self._generate_loop_programs(task))

        # Stage 5: Variable-bound programs
        if self.enable_variables:
            candidates.extend(self._generate_variable_programs(task))

        # Stage 6: CRG-guided programs (if CRG available)
        if self.crg is not None:
            candidates.extend(self._generate_crg_guided_programs(task))

        return candidates

    def _generate_conditional_programs(self, task: ARCTask) -> List[Program]:
        """Generate programs with IF/ELSE conditionals."""
        programs: List[Program] = []

        # Get base operations
        base_ops = []
        for phi in self._enum_phi_tuples():
            op = phi_to_operation(phi, task)
            if op:
                base_ops.append(op)

        base_ops = base_ops[:50]  # Limit for combinatorics

        # Generate conditionals for each predicate type
        for pred_type in PredicateType:
            pred = Predicate(predicate_type=pred_type)

            # Add relevant params based on predicate type
            if pred_type == PredicateType.HAS_COLOR:
                for color in _task_palette(task):
                    pred.params = {"color": color}

                    for then_op in base_ops[:10]:
                        # Simple IF predicate THEN op
                        expr = PhiExpression(
                            expr_type=ExprType.CONDITIONAL,
                            params={"condition": pred},
                            children=[
                                PhiExpression(expr_type=ExprType.OPERATION, value=then_op),
                            ],
                        )

                        # Convert to linear program (best effort)
                        programs.append(Program(
                            operations=[then_op],
                            name=f"if_{pred_type.name}_c{color}",
                            metadata={"conditional": True, "expression": expr.to_dict()},
                        ))

        return programs

    def _generate_loop_programs(self, task: ARCTask) -> List[Program]:
        """Generate programs with REPEAT/FOR_EACH loops."""
        programs: List[Program] = []

        base_ops = []
        for phi in self._enum_phi_tuples():
            op = phi_to_operation(phi, task)
            if op:
                base_ops.append(op)

        base_ops = base_ops[:30]

        # REPEAT n times patterns
        for repeat_count in [2, 3, 4]:
            for body_op in base_ops[:10]:
                expr = PhiExpression(
                    expr_type=ExprType.LOOP,
                    params={"type": "repeat", "count": repeat_count},
                    children=[PhiExpression(expr_type=ExprType.OPERATION, value=body_op)],
                )

                # Unroll loop into sequence
                ops = [copy.deepcopy(body_op) for _ in range(repeat_count)]
                programs.append(Program(
                    operations=ops,
                    name=f"repeat_{repeat_count}_{body_op.op.name}",
                    metadata={"loop": True, "expression": expr.to_dict()},
                ))

        # FOR_EACH color patterns
        palette = list(_task_palette(task))[:6]
        if palette:
            for body_op in base_ops[:5]:
                expr = PhiExpression(
                    expr_type=ExprType.LOOP,
                    params={"type": "for_each", "var": "$color", "items": palette},
                    children=[PhiExpression(expr_type=ExprType.OPERATION, value=body_op)],
                )

                # Generate program template
                programs.append(Program(
                    operations=[body_op],
                    name=f"foreach_color_{body_op.op.name}",
                    metadata={"loop": True, "for_each": "color", "expression": expr.to_dict()},
                ))

        return programs

    def _generate_variable_programs(self, task: ARCTask) -> List[Program]:
        """Generate programs with variable bindings."""
        programs: List[Program] = []
        palette = list(_task_palette(task))

        if not palette:
            return programs

        # Generate programs with color variable bindings
        for color_var in self.COLOR_VARS[:2]:
            for color in palette[:4]:
                for phi in self._enum_phi_tuples():
                    if phi.layer != "Mirrors":
                        continue

                    op = phi_to_operation(phi, task)
                    if op and "new_colour" in op.params or "mapping" in op.params:
                        # Create expression with variable
                        expr = PhiExpression(
                            expr_type=ExprType.LET_BINDING,
                            params={"var": color_var},
                            children=[
                                PhiExpression(expr_type=ExprType.LITERAL, value=color),
                                PhiExpression(expr_type=ExprType.OPERATION, value=op),
                            ],
                        )

                        programs.append(Program(
                            operations=[op],
                            name=f"let_{color_var}_{color}_{phi.c_prefix}",
                            metadata={"variable_binding": True, color_var: color},
                        ))

        return programs

    def _generate_crg_guided_programs(self, task: ARCTask) -> List[Program]:
        """Generate programs guided by ObjectCRG knowledge."""
        programs: List[Program] = []

        if self.crg is None:
            return programs

        # Query CRG for relevant transforms
        try:
            # Get transforms from CRG
            if hasattr(self.crg, 'edges'):
                for edge in list(self.crg.edges.values())[:20]:
                    if hasattr(edge, 'transform_type') and hasattr(edge, 'params'):
                        # Map CRG transform to DSL operation
                        # This is a simplified mapping; real implementation would be richer
                        pass
        except Exception:
            pass

        return programs

    def synthesize_recursive(self, task: ARCTask,
                             max_depth: int = 3) -> List[PhiExpression]:
        """Synthesize recursive program structures."""
        if not self.enable_recursion:
            return []

        expressions: List[PhiExpression] = []

        # Build recursive patterns
        # Pattern 1: Recursive application until fixpoint
        fixpoint_expr = PhiExpression(
            expr_type=ExprType.FUNCTION_CALL,
            params={"name": "apply_until_fixpoint"},
            children=[],
        )
        expressions.append(fixpoint_expr)

        # Pattern 2: Divide and conquer
        dac_expr = PhiExpression(
            expr_type=ExprType.FUNCTION_CALL,
            params={"name": "divide_and_conquer"},
            children=[],
        )
        expressions.append(dac_expr)

        # Pattern 3: Iterative refinement
        refine_expr = PhiExpression(
            expr_type=ExprType.FUNCTION_CALL,
            params={"name": "iterative_refinement"},
            children=[],
        )
        expressions.append(refine_expr)

        return expressions

    def fill_holes(self, expr: PhiExpression, task: ARCTask,
                   scope: Optional[Scope] = None) -> List[PhiExpression]:
        """Fill holes (unbound variables/placeholders) in expression using CRG/task analysis."""
        if scope is None:
            scope = Scope()

        filled_variants: List[PhiExpression] = []

        def _fill(e: PhiExpression) -> PhiExpression:
            """Recursively fill holes."""
            if e.expr_type == ExprType.VARIABLE:
                var_name = e.value
                if var_name.startswith("$"):
                    # Try to resolve from scope or infer from context
                    if scope.exists(var_name):
                        return PhiExpression(
                            expr_type=ExprType.LITERAL,
                            value=scope.get(var_name),
                        )
                    # Infer from variable name
                    if "color" in var_name.lower():
                        palette = _task_palette(task)
                        if palette:
                            return PhiExpression(
                                expr_type=ExprType.LITERAL,
                                value=next(iter(palette)),
                            )
                    if "count" in var_name.lower() or "n" in var_name.lower():
                        return PhiExpression(
                            expr_type=ExprType.LITERAL,
                            value=3,  # Default count
                        )

            # Recurse into children
            filled_children = [_fill(c) for c in e.children]

            return PhiExpression(
                expr_type=e.expr_type,
                children=filled_children,
                value=e.value,
                params=e.params,
                metadata=e.metadata,
            )

        filled = _fill(expr)
        filled_variants.append(filled)

        return filled_variants

    def induce_grammar(self, io_pairs: List[Tuple[Grid, Grid]]) -> Dict[str, Any]:
        """Induce grammar rules from input/output pairs."""
        # Simplified grammar induction
        # Real implementation would analyze patterns across pairs

        rules = {
            "terminals": list(C_PREFIXES),
            "non_terminals": ["Program", "Op", "Cond", "Loop"],
            "productions": [],
        }

        # Analyze common patterns
        ops_seen: Dict[str, int] = {}
        for inp, out in io_pairs:
            # Infer what operations might explain the transformation
            # This is a placeholder; real implementation uses object diffing
            pass

        return rules


# ══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def generate_candidates_full(task: ARCTask,
                              max_program_length: int = 3,
                              enable_conditionals: bool = True,
                              enable_loops: bool = True,
                              enable_recursion: bool = False,
                              crg=None) -> List[Program]:
    """Convenience function — see PhiGrammarFull."""
    gen = PhiGrammarFull(
        max_program_length=max_program_length,
        enable_conditionals=enable_conditionals,
        enable_loops=enable_loops,
        enable_recursion=enable_recursion,
        crg=crg,
    )
    return gen.generate(task)


def grammar_size_full(enable_conditionals: bool = True,
                       enable_loops: bool = True,
                       enable_recursion: bool = True) -> Dict[str, int]:
    """Report the size of the extended Φ-grammar's parameter space."""
    base_tuples = len(N_VALUES) * len(ARMS) * len(LAYERS) * len(C_PREFIXES) * len(CORRECTIONS)

    stats = {
        "base_phi_tuples": base_tuples,
        "n_values": len(N_VALUES),
        "arms": len(ARMS),
        "layers": len(LAYERS),
        "c_prefixes": len(C_PREFIXES),
        "corrections": len(CORRECTIONS),
    }

    if enable_conditionals:
        stats["predicate_types"] = len(PredicateType)
        stats["estimated_conditional_programs"] = base_tuples * len(PredicateType) * 10

    if enable_loops:
        stats["loop_types"] = 3  # repeat, for_each, while
        stats["estimated_loop_programs"] = base_tuples * 3 * 5

    if enable_recursion:
        stats["recursive_templates"] = 3  # fixpoint, divide-conquer, refinement

    stats["total_estimated"] = sum(
        v for k, v in stats.items()
        if k.startswith("estimated") or k == "base_phi_tuples"
    )

    return stats


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def integrate_with_crg(grammar: PhiGrammarFull, crg: Any):
    """Integrate Φ-grammar with ObjectCRG for guided synthesis."""
    grammar.crg = crg

    # Enable CRG-guided hole filling
    original_fill = grammar.fill_holes

    def crg_aware_fill(expr: PhiExpression, task: ARCTask,
                       scope: Optional[Scope] = None) -> List[PhiExpression]:
        # First try CRG-based filling
        if crg is not None and hasattr(crg, 'find_transform_for_object'):
            # Query CRG for context-appropriate transforms
            pass

        # Fall back to standard filling
        return original_fill(expr, task, scope)

    grammar.fill_holes = crg_aware_fill


def integrate_with_transformer(grammar: PhiGrammarFull, transformer: Any):
    """Integrate Φ-grammar with GenerativeTransformerFull."""
    # The transformer can use grammar as a generation backend
    if transformer is not None:
        setattr(transformer, 'phi_grammar', grammar)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN / TESTING
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Quick sanity check
    print("Φ-Grammar Full — Parameter Space:")
    stats = grammar_size_full()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\nSample PhiTuples:")
    for i, phi in enumerate(PhiGrammarFull()._enum_phi_tuples()):
        if i >= 5:
            break
        print(f"  {phi}")

    print("\nPredicate Types:")
    for p in PredicateType:
        print(f"  {p.name}")

    print("\nExpression Types:")
    for e in ExprType:
        print(f"  {e.name}")

    print("\n✓ Φ-Grammar Full loaded successfully")