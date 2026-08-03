#!/usr/bin/env python3
"""
================================================================================
UBP Spatial arithmetic: a small geometric arithmetic codec.
================================================================================
Author  : E R A Craig, New Zealand
Version : 0.2
Date    : 28 June 2026

THE CONCEPT
=========

Signed integers are represented by regular unit-edge polygons embedded in 3-D.
The vertex count stores magnitude and sign.  The empty space between adjacent
polygons stores an operator.  An observer reconstructs the connected cycles,
measures their geometry, decodes the expression, and evaluates it with exact
``fractions.Fraction`` arithmetic.

Documented geometry-based codec.
Signed integers are encoded as rotated regular unit-edge polygons; vertex count carries magnitude and sign.
Operators are encoded using size-independent clearances between polygon bounds.
Added strict cycle validation and explicit rejection of malformed geometry or unsupported expression syntax.
Supports signed integers, +, -, *, /, standard precedence, and exact rational division using Fraction.
Separately validated real-domain eml(x, y) = exp(x) - log(y) function.
CLI handling and deterministic built-in tests.

This is deliberately a codec, not a claim that passive geometry performs
arithmetic by itself.  Python constructs and observes the geometry.  The EML
operator is included as a separate numerical primitive.

Examples:
    python3 spatial_arithmetic.py --eval "3 + 4 * 5"
    python3 spatial_arithmetic.py --scene 7 DIVIDE 3
    python3 spatial_arithmetic.py --eml 1 2
    python3 spatial_arithmetic.py --self-test

================================================================================
"""

from __future__ import annotations

import argparse
import cmath
import json
import math
import random
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from statistics import median
from typing import Callable, Iterable, Iterator, Sequence

Point = tuple[float, float, float]
Number = int | Fraction

UNIT = 1.0
EDGE_TOLERANCE = 1e-7
CODE_TOLERANCE = 1e-5
BASE_NODES = 4
MAX_VERTICES = 100_000

# The code is the clear space, measured in edge lengths, between bounding
# spheres.  Every code is > 1, so vertices belonging to different operands
# cannot accidentally be joined by the unit-edge component detector.
OPERATOR_CODES: dict[str, int] = {
    "MULTIPLY": 4,
    "DIVIDE": 5,
    "ADD": 6,
    "SUBTRACT": 7,
}
CODE_TO_OPERATOR = {code: name for name, code in OPERATOR_CODES.items()}
SYMBOL_TO_OPERATOR = {
    "*": "MULTIPLY",
    "/": "DIVIDE",
    "+": "ADD",
    "-": "SUBTRACT",
}


def _apply_operator(name: str, left: Number, right: Number) -> Number:
    """Apply one decoded operator, retaining exact rational results."""
    if name == "ADD":
        return left + right
    if name == "SUBTRACT":
        return left - right
    if name == "MULTIPLY":
        return left * right
    if name == "DIVIDE":
        if right == 0:
            raise ZeroDivisionError("division by zero")
        return Fraction(left, right)
    raise ValueError(f"unknown operator: {name!r}")


def eml(x: float, y: float) -> float:
    """Return ``exp(x) - log(y)`` on the real domain ``y > 0``."""
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("EML arguments must be finite")
    if y <= 0:
        raise ValueError("real EML requires y > 0")
    return math.exp(x) - math.log(y)


def eml_complex(x: complex, y: complex) -> complex:
    """Complex EML using Python's principal logarithm branch.

    The branch is ``Log(y) = ln|y| + i Arg(y)`` with ``Arg(y)`` in
    ``(-pi, pi]`` and a branch cut on the non-positive real axis.  The value at
    ``y = 0`` is undefined.  Approaching a negative real from above/below gives
    the corresponding ``+pi``/``-pi`` boundary value.
    """
    x, y = complex(x), complex(y)
    if not all(math.isfinite(v) for v in (x.real, x.imag, y.real, y.imag)):
        raise ValueError("complex EML arguments must have finite components")
    if y == 0:
        raise ValueError("complex logarithm is undefined at zero")
    return cmath.exp(x) - cmath.log(y)


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------


def node_count(value: int) -> int:
    """Number of vertices used to represent a signed integer.

    Non-negative values use ``2*value + 4`` (even); negative values use
    ``2*abs(value) + 5`` (odd).  Four is the smallest polygon used here.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("geometric operands must be integers")
    return 2 * abs(value) + BASE_NODES + (1 if value < 0 else 0)


def decode_node_count(count: int) -> int:
    """Inverse of :func:`node_count` for valid encoded counts."""
    if count < BASE_NODES:
        raise ValueError(f"an operand needs at least {BASE_NODES} vertices")
    magnitude = (count - BASE_NODES) // 2
    return magnitude if count % 2 == 0 else -magnitude


def circumradius(count: int) -> float:
    """Circumradius of a regular ``count``-gon whose edge length is one."""
    if count < 3:
        raise ValueError("a polygon needs at least three vertices")
    return UNIT / (2.0 * math.sin(math.pi / count))


def _rotation_matrix(seed: int) -> tuple[tuple[float, float, float], ...]:
    """Generate a deterministic proper 3-D rotation (Rodrigues' formula)."""
    rng = random.Random(seed)
    axis = [rng.gauss(0.0, 1.0) for _ in range(3)]
    length = math.sqrt(sum(component * component for component in axis))
    x, y, z = (component / length for component in axis)
    angle = rng.uniform(0.0, 2.0 * math.pi)
    c, s, t = math.cos(angle), math.sin(angle), 1.0 - math.cos(angle)
    return (
        (t * x * x + c, t * x * y - s * z, t * x * z + s * y),
        (t * x * y + s * z, t * y * y + c, t * y * z - s * x),
        (t * x * z - s * y, t * y * z + s * x, t * z * z + c),
    )


def _rotate(points: Iterable[Point], matrix: Sequence[Sequence[float]]) -> list[Point]:
    return [
        tuple(sum(matrix[row][column] * point[column] for column in range(3))
              for row in range(3))  # type: ignore[misc]
        for point in points
    ]


def make_unit_cycle(count: int, seed: int = 0) -> list[Point]:
    """Construct a regular unit-edge polygon and rotate its plane in 3-D."""
    if count < BASE_NODES:
        raise ValueError(f"count must be at least {BASE_NODES}")
    if count > MAX_VERTICES:
        raise ValueError(f"count exceeds safety limit ({MAX_VERTICES})")
    radius = circumradius(count)
    planar = [
        (radius * math.cos(2.0 * math.pi * i / count),
         radius * math.sin(2.0 * math.pi * i / count),
         0.0)
        for i in range(count)
    ]
    return _rotate(planar, _rotation_matrix(seed))


# Compatibility name retained from the previous version.
make_3d_cycle = make_unit_cycle


def encode(value: int, seed: int = 0) -> list[Point]:
    """Encode a signed integer as a rotated, unit-edge polygon."""
    return make_unit_cycle(node_count(value), seed)


def decode(points: Sequence[Point]) -> int:
    """Decode an operand after validating its cycle geometry."""
    validate_cycle(points)
    return decode_node_count(len(points))


def centroid(points: Sequence[Point]) -> Point:
    if not points:
        raise ValueError("cannot find the centroid of an empty point set")
    return tuple(sum(point[axis] for point in points) / len(points)
                 for axis in range(3))  # type: ignore[return-value]


def radius_of(points: Sequence[Point]) -> float:
    center = centroid(points)
    return max(math.dist(center, point) for point in points)


def translate(points: Sequence[Point], offset: Point) -> list[Point]:
    return [tuple(point[i] + offset[i] for i in range(3))  # type: ignore[misc]
            for point in points]


def validate_cycle(points: Sequence[Point], tolerance: float = EDGE_TOLERANCE) -> None:
    """Validate vertex count, finite coordinates, and unit consecutive edges.

    Points recovered from an unordered cloud must first be passed through
    :func:`reorder_to_cycle`.
    """
    if len(points) < BASE_NODES:
        raise ValueError("too few vertices for an encoded operand")
    if len(points) > MAX_VERTICES:
        raise ValueError("operand exceeds the vertex safety limit")
    if any(len(point) != 3 or not all(math.isfinite(x) for x in point)
           for point in points):
        raise ValueError("all vertices must have three finite coordinates")
    for i, point in enumerate(points):
        edge = math.dist(point, points[(i + 1) % len(points)])
        if not math.isclose(edge, UNIT, rel_tol=0.0, abs_tol=tolerance):
            raise ValueError(f"edge {i} has length {edge:.12g}, not {UNIT}")


def pairwise_centroid_distance(a: Sequence[Point], b: Sequence[Point]) -> float:
    """Centroid distance computed only from pairwise squared distances.

    The identity is
      |mean(A)-mean(B)|² = E|A-B|² - 1/2 E|A-A'|² - 1/2 E|B-B'|².
    Summing only unordered within-set pairs already supplies each ``1/2``
    term, which is why the denominators below are ``n²`` rather than
    ``2*n²``.
    """
    if not a or not b:
        raise ValueError("both point sets must be non-empty")
    cross = sum(math.dist(x, y) ** 2 for x in a for y in b) / (len(a) * len(b))
    within_a = sum(math.dist(a[i], a[j]) ** 2
                   for i in range(len(a)) for j in range(i + 1, len(a))) / len(a) ** 2
    within_b = sum(math.dist(b[i], b[j]) ** 2
                   for i in range(len(b)) for j in range(i + 1, len(b))) / len(b) ** 2
    return math.sqrt(max(0.0, cross - within_a - within_b))


# ---------------------------------------------------------------------------
# Point-cloud observation
# ---------------------------------------------------------------------------


def _nearby_pairs(points: Sequence[Point], target: float,
                  tolerance: float) -> Iterator[tuple[int, int]]:
    """Yield candidate pairs using a uniform spatial hash, not all-pairs search."""
    cell_size = target + tolerance
    if cell_size <= 0:
        raise ValueError("edge scale and tolerance must be positive")
    cells: dict[tuple[int, int, int], list[int]] = {}
    for i, point in enumerate(points):
        cell = tuple(math.floor(x / cell_size) for x in point)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in cells.get((cell[0] + dx, cell[1] + dy, cell[2] + dz), ()):
                        if abs(math.dist(point, points[j]) - target) <= tolerance:
                            yield j, i
        cells.setdefault(cell, []).append(i)


def calibrate_edge_length(points: Sequence[Point]) -> float:
    """Estimate scan scale robustly as the median nearest-neighbour distance."""
    if len(points) < BASE_NODES:
        raise ValueError("too few scan points to calibrate")
    nearest: list[float] = []
    for i, point in enumerate(points):
        distances = [math.dist(point, other) for j, other in enumerate(points) if i != j]
        nearest.append(min(distances))
    scale = median(nearest)
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("could not calibrate a positive edge length")
    return scale


def cluster_detect(points: Sequence[Point], tolerance: float = EDGE_TOLERANCE,
                   edge_length: float = UNIT) -> list[list[int]]:
    """Find unit-edge components with a spatial hash (near-linear for sparse scans)."""
    if len(points) > MAX_VERTICES:
        raise ValueError("scene exceeds the vertex safety limit")
    parent = list(range(len(points)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        x, y = find(x), find(y)
        if x != y:
            parent[y] = x

    for i, j in _nearby_pairs(points, edge_length, tolerance):
        union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(len(points)):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def reorder_to_cycle(points: Sequence[Point], indices: Sequence[int]) -> list[Point]:
    """Recover cycle order from one unit-edge connected component.

    A valid operand must induce exactly one simple cycle: every vertex has
    degree two and a walk must visit every vertex once.
    """
    local = [points[i] for i in indices]
    adjacency: list[list[int]] = [[] for _ in local]
    for i in range(len(local)):
        for j in range(i + 1, len(local)):
            if math.isclose(math.dist(local[i], local[j]), UNIT,
                            rel_tol=0.0, abs_tol=EDGE_TOLERANCE):
                adjacency[i].append(j)
                adjacency[j].append(i)
    if any(len(neighbours) != 2 for neighbours in adjacency):
        raise ValueError("component is not a simple unit-edge cycle")

    order = [0]
    previous = -1
    current = 0
    while len(order) < len(local):
        choices = [n for n in adjacency[current] if n != previous]
        next_vertex = choices[0]
        if next_vertex == order[0] and len(order) < len(local):
            next_vertex = choices[1]
        if next_vertex in order:
            raise ValueError("cycle closes before visiting every vertex")
        order.append(next_vertex)
        previous, current = current, next_vertex
    if order[0] not in adjacency[order[-1]]:
        raise ValueError("component does not close into a cycle")
    result = [local[i] for i in order]
    validate_cycle(result)
    return result


def _decode_shapes(points: Sequence[Point]) -> list[dict[str, object]]:
    shapes: list[dict[str, object]] = []
    for component in cluster_detect(points):
        cycle = reorder_to_cycle(points, component)
        shapes.append({
            "points": cycle,
            "value": decode_node_count(len(cycle)),
            "center": centroid(cycle),
            "radius": radius_of(cycle),
        })
    shapes.sort(key=lambda shape: shape["center"][0])  # type: ignore[index]
    return shapes


def _operator_distance(left: Sequence[Point], right: Sequence[Point], name: str) -> float:
    """Center distance = two bounding radii + an integer clearance code."""
    return radius_of(left) + radius_of(right) + OPERATOR_CODES[name] * UNIT


def _decode_operator(left: dict[str, object], right: dict[str, object]) -> str:
    distance = pairwise_centroid_distance(
        left["points"], right["points"]  # type: ignore[arg-type]
    )
    clearance = (distance - float(left["radius"]) - float(right["radius"])) / UNIT
    code = round(clearance)
    if code not in CODE_TO_OPERATOR or not math.isclose(
            clearance, code, rel_tol=0.0, abs_tol=CODE_TOLERANCE):
        raise ValueError(f"unrecognised operator clearance {clearance:.8g}")
    return CODE_TO_OPERATOR[code]


# ---------------------------------------------------------------------------
# Scene construction and evaluation
# ---------------------------------------------------------------------------


def build_scene(a: int, b: int, operator: str, seed: int = 0) -> list[Point]:
    """Build a two-operand scene laid out from left to right."""
    operator = operator.upper()
    if operator not in OPERATOR_CODES:
        raise ValueError(f"operator must be one of {', '.join(OPERATOR_CODES)}")
    left, right = encode(a, seed * 2), encode(b, seed * 2 + 1)
    distance = _operator_distance(left, right, operator)
    return left + translate(right, (distance, 0.0, 0.0))


def observe_scene(points: Sequence[Point]) -> dict[str, object]:
    """Decode and evaluate a two-operand scene; errors are reported in-band."""
    try:
        shapes = _decode_shapes(points)
        if len(shapes) != 2:
            raise ValueError(f"expected two operand cycles, found {len(shapes)}")
        operator = _decode_operator(shapes[0], shapes[1])
        a, b = shapes[0]["value"], shapes[1]["value"]
        result = _apply_operator(operator, a, b)  # type: ignore[arg-type]
        return {"ok": True, "a": a, "b": b, "operator": operator, "result": result}
    except (TypeError, ValueError, ZeroDivisionError) as error:
        return {"ok": False, "reason": str(error)}


def build_expression(tokens: Sequence[int | str], seed: int = 0) -> list[Point]:
    """Build a left-to-right geometric scene from alternating values/operators."""
    if not tokens or len(tokens) % 2 == 0:
        raise ValueError("expression must alternate integer, operator, integer")
    values = list(tokens[::2])
    operators = [str(op).upper() for op in tokens[1::2]]
    if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
        raise TypeError("expression operands must be integers")
    if any(operator not in OPERATOR_CODES for operator in operators):
        raise ValueError("expression contains an unknown operator")

    cycles = [encode(value, seed * 100 + i) for i, value in enumerate(values)]
    scene = list(cycles[0])
    x = 0.0
    for i, operator in enumerate(operators):
        x += _operator_distance(cycles[i], cycles[i + 1], operator)
        scene.extend(translate(cycles[i + 1], (x, 0.0, 0.0)))
    return scene


def observe_expression(points: Sequence[Point]) -> dict[str, object]:
    """Decode a flat scene and evaluate with normal */ before +/- precedence."""
    try:
        shapes = _decode_shapes(points)
        if not shapes:
            raise ValueError("the scene contains no operands")
        values: list[Number] = [shape["value"] for shape in shapes]  # type: ignore[misc]
        operators = [_decode_operator(shapes[i], shapes[i + 1])
                     for i in range(len(shapes) - 1)]

        # Collapse multiplication and division from left to right.
        reduced_values = [values[0]]
        reduced_operators: list[str] = []
        for operator, value in zip(operators, values[1:]):
            if operator in ("MULTIPLY", "DIVIDE"):
                reduced_values[-1] = _apply_operator(operator, reduced_values[-1], value)
            else:
                reduced_operators.append(operator)
                reduced_values.append(value)

        result = reduced_values[0]
        for operator, value in zip(reduced_operators, reduced_values[1:]):
            result = _apply_operator(operator, result, value)
        return {"ok": True, "result": result, "values": values,
                "operators": operators}
    except (TypeError, ValueError, ZeroDivisionError) as error:
        return {"ok": False, "reason": str(error)}


_TOKEN = re.compile(r"\s*(?:(\d+)|(.))")


def parse_expression(text: str) -> list[int | str]:
    """Parse integer literals and +, -, *, /; reject every other character."""
    raw: list[int | str] = []
    position = 0
    while position < len(text):
        if text[position:].isspace():
            break
        match = _TOKEN.match(text, position)
        if match is None:
            raise ValueError(f"invalid expression near position {position}")
        position = match.end()
        if match.group(1) is not None:
            raw.append(int(match.group(1)))
        else:
            char = match.group(2)
            if char not in SYMBOL_TO_OPERATOR:
                raise ValueError(f"unsupported character {char!r}")
            raw.append(char)
    if not raw:
        raise ValueError("expression is empty")

    # Fold unary signs into the following integer. Unary plus/minus is accepted
    # only where a value is expected, keeping the geometric grammar unambiguous.
    tokens: list[int | str] = []
    expecting_value = True
    i = 0
    while i < len(raw):
        token = raw[i]
        if expecting_value:
            sign = 1
            if token in ("+", "-"):
                sign = -1 if token == "-" else 1
                i += 1
                if i >= len(raw):
                    raise ValueError("missing integer after unary sign")
                token = raw[i]
            if not isinstance(token, int):
                raise ValueError("expected an integer operand")
            tokens.append(sign * token)
            expecting_value = False
        else:
            if not isinstance(token, str) or token not in SYMBOL_TO_OPERATOR:
                raise ValueError("expected an operator")
            tokens.append(SYMBOL_TO_OPERATOR[token])
            expecting_value = True
        i += 1
    if expecting_value:
        raise ValueError("expression ends with an operator")
    return tokens


# ---------------------------------------------------------------------------
# Rational operands, expression trees, and interchange
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RationalGeometry:
    """Oriented rational operand: numerator above, denominator below.

    ``axis`` points from denominator centroid to numerator centroid.  Keeping
    this orientation in the data removes the reciprocal ambiguity that an
    unordered pair of polygons would have.
    """

    numerator: tuple[Point, ...]
    denominator: tuple[Point, ...]
    axis: Point = (0.0, 0.0, 1.0)


def encode_rational(value: Fraction | int, seed: int = 0) -> RationalGeometry:
    """Encode a reduced fraction as two signed-integer polygons along +z/-z."""
    value = Fraction(value)
    top = encode(value.numerator, seed * 2)
    bottom = encode(value.denominator, seed * 2 + 1)
    separation = radius_of(top) + radius_of(bottom) + 3.0 * UNIT
    return RationalGeometry(
        tuple(translate(top, (0.0, 0.0, separation / 2.0))),
        tuple(translate(bottom, (0.0, 0.0, -separation / 2.0))),
    )


def decode_rational(geometry: RationalGeometry) -> Fraction:
    """Validate and decode an oriented numerator/denominator polygon pair."""
    numerator = decode(geometry.numerator)
    denominator = decode(geometry.denominator)
    if denominator == 0:
        raise ZeroDivisionError("rational geometry has a zero denominator")
    delta = tuple(centroid(geometry.numerator)[i] - centroid(geometry.denominator)[i]
                  for i in range(3))
    if sum(delta[i] * geometry.axis[i] for i in range(3)) <= 0:
        raise ValueError("numerator/denominator orientation is reversed")
    return Fraction(numerator, denominator)


@dataclass(frozen=True)
class ExpressionNode:
    """A binary expression tree; leaves contain exact rational values."""

    value: Fraction | None = None
    operator: str | None = None
    left: "ExpressionNode | None" = None
    right: "ExpressionNode | None" = None

    def __post_init__(self) -> None:
        leaf = self.value is not None
        branch = self.operator is not None and self.left is not None and self.right is not None
        if leaf == branch:
            raise ValueError("an expression node must be exactly one leaf or one binary branch")
        if branch and self.operator not in OPERATOR_CODES:
            raise ValueError(f"unknown tree operator {self.operator!r}")


def parse_expression_tree(text: str) -> ExpressionNode:
    """Parse integers, parentheses, unary signs, and the four binary operators."""
    token_re = re.compile(r"\s*(\d+|[()+*/-])")
    tokens: list[str] = []
    position = 0
    while position < len(text):
        if text[position:].isspace():
            break
        match = token_re.match(text, position)
        if match is None:
            raise ValueError(f"unsupported expression near position {position}")
        tokens.append(match.group(1))
        position = match.end()
    index = 0

    def primary() -> ExpressionNode:
        nonlocal index
        sign = 1
        while index < len(tokens) and tokens[index] in ("+", "-"):
            if tokens[index] == "-":
                sign *= -1
            index += 1
        if index >= len(tokens):
            raise ValueError("missing expression after unary sign")
        if tokens[index] == "(":
            if sign < 0:
                raise ValueError("unary minus before parentheses is not supported; write -1*(...)")
            index += 1
            node = addition()
            if index >= len(tokens) or tokens[index] != ")":
                raise ValueError("missing closing parenthesis")
            index += 1
            return node
        if not tokens[index].isdigit():
            raise ValueError("expected an integer or opening parenthesis")
        value = sign * int(tokens[index])
        index += 1
        return ExpressionNode(value=Fraction(value))

    def multiplication() -> ExpressionNode:
        nonlocal index
        node = primary()
        while index < len(tokens) and tokens[index] in ("*", "/"):
            operator = SYMBOL_TO_OPERATOR[tokens[index]]
            index += 1
            node = ExpressionNode(operator=operator, left=node, right=primary())
        return node

    def addition() -> ExpressionNode:
        nonlocal index
        node = multiplication()
        while index < len(tokens) and tokens[index] in ("+", "-"):
            operator = SYMBOL_TO_OPERATOR[tokens[index]]
            index += 1
            node = ExpressionNode(operator=operator, left=node, right=multiplication())
        return node

    if not tokens:
        raise ValueError("expression is empty")
    root = addition()
    if index != len(tokens):
        raise ValueError(f"unexpected token {tokens[index]!r}")
    return root


def evaluate_expression_tree(node: ExpressionNode) -> Fraction:
    """Evaluate an expression tree exactly."""
    if node.value is not None:
        return node.value
    assert node.left is not None and node.right is not None and node.operator is not None
    return Fraction(_apply_operator(node.operator,
                                    evaluate_expression_tree(node.left),
                                    evaluate_expression_tree(node.right)))


def expression_tree_scene(node: ExpressionNode, seed: int = 0) -> dict[str, object]:
    """Create a serializable geometric tree with explicit parent/child topology.

    Leaves contain oriented rational geometry.  Branch nodes contain an operator
    and child paths.  Explicit topology, rather than planar spacing, preserves
    parentheses under rotation and CAD interchange.
    """
    records: list[dict[str, object]] = []

    def visit(current: ExpressionNode, path: str, depth: int, order: list[int]) -> None:
        if current.value is not None:
            x = order[0] * 12.0
            order[0] += 1
            geometry = encode_rational(current.value, seed + order[0])
            records.append({"path": path, "kind": "value", "value": str(current.value),
                            "position": [x, 0.0, -8.0 * depth],
                            "numerator": geometry.numerator,
                            "denominator": geometry.denominator,
                            "axis": geometry.axis})
            return
        assert current.left is not None and current.right is not None
        records.append({"path": path, "kind": "operator", "operator": current.operator,
                        "children": [path + "L", path + "R"], "depth": depth})
        visit(current.left, path + "L", depth + 1, order)
        visit(current.right, path + "R", depth + 1, order)

    visit(node, "R", 0, [0])
    return {"format": "spatial-arithmetic-tree-v1", "nodes": records}


def save_scene_json(scene: dict[str, object], filename: str | Path) -> None:
    """Write a lossless scene interchange file (coordinates plus tree metadata)."""
    Path(filename).write_text(json.dumps(scene, indent=2), encoding="utf-8")


def load_scene_json(filename: str | Path) -> dict[str, object]:
    """Load and minimally validate a scene interchange file."""
    scene = json.loads(Path(filename).read_text(encoding="utf-8"))
    if not isinstance(scene, dict) or scene.get("format") != "spatial-arithmetic-tree-v1":
        raise ValueError("not a spatial-arithmetic-tree-v1 scene")
    if not isinstance(scene.get("nodes"), list):
        raise ValueError("scene nodes must be a list")
    return scene


def save_scene_obj(scene: dict[str, object], filename: str | Path) -> None:
    """Export leaf polygons as Wavefront OBJ, directly importable by Blender.

    OBJ cannot retain arithmetic tree semantics, so use the JSON file as the
    authoritative sidecar when a round trip is required.
    """
    lines = ["# Spatial Arithmetic geometry; JSON sidecar retains semantics"]
    offset = 1
    for record in scene.get("nodes", []):  # type: ignore[union-attr]
        if not isinstance(record, dict) or record.get("kind") != "value":
            continue
        position = record.get("position", [0.0, 0.0, 0.0])
        for role in ("numerator", "denominator"):
            points = record[role]
            lines.append(f"o {record['path']}_{role}")
            for point in points:
                lines.append("v " + " ".join(str(float(point[i]) + float(position[i])) for i in range(3)))
            count = len(points)
            lines.append("l " + " ".join(str(offset + i) for i in range(count)) + f" {offset}")
            offset += count
    Path(filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def observe_noisy_operand(points: Sequence[Point], relative_tolerance: float = 0.03) -> int:
    """Decode a scaled/noisy isolated operand using calibrated edge tolerance.

    This recovers complete cycles with perturbed coordinates; it deliberately
    rejects missing vertices rather than guessing a value from an open arc.
    """
    if not 0 < relative_tolerance < 0.25:
        raise ValueError("relative_tolerance must lie between 0 and 0.25")
    scale = calibrate_edge_length(points)
    tolerance = scale * relative_tolerance
    components = cluster_detect(points, tolerance=tolerance, edge_length=scale)
    if len(components) != 1:
        raise ValueError(f"expected one calibrated cycle, found {len(components)} components")
    # Normalise the calibrated scan to unit edge length, then use strict topology checks.
    normalised = [tuple(x / scale for x in point) for point in points]
    cycle = reorder_to_cycle_noisy(normalised, components[0], relative_tolerance)
    return decode_node_count(len(cycle))


def reorder_to_cycle_noisy(points: Sequence[Point], indices: Sequence[int],
                           tolerance: float) -> list[Point]:
    """Recover one simple cycle with a caller-supplied calibrated tolerance."""
    local = [points[i] for i in indices]
    adjacency = [[] for _ in local]
    for i, j in _nearby_pairs(local, UNIT, tolerance):
        adjacency[i].append(j)
        adjacency[j].append(i)
    if any(len(row) != 2 for row in adjacency):
        raise ValueError("noisy component is not a recoverable simple cycle")
    order, previous, current = [0], -1, 0
    while len(order) < len(local):
        choices = [n for n in adjacency[current] if n != previous and n not in order]
        if not choices:
            raise ValueError("noisy cycle closes early")
        order.append(choices[0])
        previous, current = current, choices[0]
    if order[0] not in adjacency[order[-1]]:
        raise ValueError("noisy cycle is open")
    return [local[i] for i in order]


def natural_add(a: int, b: int, seed: int = 0) -> tuple[int | None, str]:
    """Demonstrate the node-count identity for non-negative addition.

    The result is read from the combined vertex count after subtracting the two
    four-vertex offsets.  This is a counting identity, not a general signed
    geometric addition rule.
    """
    del seed  # retained for API compatibility
    if a < 0 or b < 0:
        return None, "natural_add is defined only for non-negative operands"
    total_vertices = node_count(a) + node_count(b)
    return (total_vertices - 2 * BASE_NODES) // 2, "node-count identity"


def radius_ratio(a: int, b: int) -> tuple[float, float, float]:
    """Return polygon radii and their ratio (not the arithmetic quotient)."""
    ra, rb = circumradius(node_count(a)), circumradius(node_count(b))
    return ra, rb, ra / rb


# Compatibility name, now documented accurately.
natural_divide = radius_ratio


# ---------------------------------------------------------------------------
# Verification and command-line interface
# ---------------------------------------------------------------------------


def run_tests() -> bool:
    """Run deterministic regression/property checks without third-party tools."""
    checks: list[tuple[str, Callable[[], bool]]] = []

    checks.append(("signed encode/decode round trips", lambda: all(
        decode(encode(value, seed)) == value
        for value in range(-50, 51) for seed in range(5))))
    checks.append(("all consecutive polygon edges are unit length", lambda: all(
        all(math.isclose(math.dist(shape[i], shape[(i + 1) % len(shape)]), UNIT,
                         abs_tol=EDGE_TOLERANCE, rel_tol=0.0)
            for i in range(len(shape)))
        for shape in (encode(value, value + 60) for value in range(-20, 21)))))

    def scene_check() -> bool:
        for a in range(-8, 9):
            for b in range(-8, 9):
                for operator in OPERATOR_CODES:
                    if operator == "DIVIDE" and b == 0:
                        continue
                    observed = observe_scene(build_scene(a, b, operator, seed=19))
                    if not observed.get("ok"):
                        return False
                    if observed["result"] != _apply_operator(operator, a, b):
                        return False
        return True

    checks.append(("two-operand geometric scenes", scene_check))

    examples = {
        "3 + 4 * 5": 23,
        "20 / 4 + 3": 8,
        "10 - 2 * 3": 4,
        "-5 + 3 * -2": -11,
        "7 / 3 + 5": Fraction(22, 3),
        "8 / 3 / 2": Fraction(4, 3),
    }

    def expression_check() -> bool:
        return all(
            observe_expression(build_expression(parse_expression(text), seed=31)).get("result") == expected
            for text, expected in examples.items()
        )

    checks.append(("expression precedence and exact division", expression_check))
    checks.append(("parenthesized expression trees", lambda:
                   evaluate_expression_tree(parse_expression_tree("(3 + 4) * (5 - 2) / 7")) == 3))
    checks.append(("oriented rational operand round trips", lambda: all(
        decode_rational(encode_rational(Fraction(n, d), seed=n + 20 * d)) == Fraction(n, d)
        for n in range(-8, 9) for d in range(1, 8))))

    def noisy_check() -> bool:
        rng = random.Random(2468)
        source = encode(-9, 44)
        noisy = [tuple(2.5 * coordinate + rng.uniform(-0.006, 0.006)
                       for coordinate in point) for point in source]
        rng.shuffle(noisy)
        return observe_noisy_operand(noisy, 0.02) == -9

    checks.append(("calibrated noisy cycle recovery", noisy_check))

    def interchange_check() -> bool:
        import tempfile
        tree = parse_expression_tree("2 * (7 - 3)")
        scene = expression_tree_scene(tree, 9)
        with tempfile.TemporaryDirectory() as directory:
            json_path = Path(directory) / "scene.json"
            obj_path = Path(directory) / "scene.obj"
            save_scene_json(scene, json_path)
            save_scene_obj(scene, obj_path)
            return load_scene_json(json_path) == json.loads(json_path.read_text()) and "\nv " in obj_path.read_text()

    checks.append(("JSON and Blender OBJ interchange", interchange_check))
    checks.append(("complex EML principal branch", lambda:
                   cmath.isclose(eml_complex(0, -1), 1 - 1j * math.pi) and
                   _raises(ValueError, lambda: eml_complex(0, 0))))

    def distance_identity_check() -> bool:
        a, b = encode(4, 1), translate(encode(-7, 2), (12.0, -3.0, 5.0))
        return math.isclose(pairwise_centroid_distance(a, b),
                            math.dist(centroid(a), centroid(b)),
                            abs_tol=1e-10, rel_tol=0.0)

    checks.append(("pairwise centroid-distance identity", distance_identity_check))
    checks.append(("node-count addition identity", lambda: all(
        natural_add(a, b)[0] == a + b for a in range(20) for b in range(20))))
    checks.append(("EML definition and domain check", lambda:
                   math.isclose(eml(1.0, 1.0), math.e) and
                   _raises(ValueError, lambda: eml(1.0, 0.0))))
    checks.append(("invalid syntax is rejected", lambda:
                   _raises(ValueError, lambda: parse_expression("2 + x")) and
                   _raises(ValueError, lambda: parse_expression("2 ** 3"))))

    print("Spatial Arithmetic self-test")
    passed = True
    for description, check in checks:
        try:
            result = check()
        except Exception as error:  # make a failed test informative at the CLI
            result = False
            print(f"  FAIL  {description}: {error}")
        else:
            print(f"  {'PASS' if result else 'FAIL'}  {description}")
        passed &= result
    print("All checks passed." if passed else "One or more checks failed.")
    return passed


def _raises(exception: type[BaseException], action: Callable[[], object]) -> bool:
    try:
        action()
    except exception:
        return True
    return False


def _format_number(value: object) -> str:
    if isinstance(value, Fraction) and value.denominator != 1:
        return f"{value.numerator}/{value.denominator}"
    return str(value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--eval", metavar="EXPRESSION",
                       help="evaluate an integer expression, including parentheses, exactly")
    group.add_argument("--scene", nargs=3, metavar=("A", "OPERATOR", "B"),
                       help="construct, observe, and print one geometric operation")
    group.add_argument("--eml", nargs=2, type=float, metavar=("X", "Y"),
                       help="calculate exp(X) - log(Y) on the real domain")
    group.add_argument("--eml-complex", nargs=2, type=complex, metavar=("X", "Y"),
                       help="complex EML with the principal logarithm branch")
    group.add_argument("--export", nargs=3, metavar=("EXPRESSION", "JSON", "OBJ"),
                       help="export an expression-tree scene to JSON and Blender OBJ")
    group.add_argument("--natural", nargs=2, type=int, metavar=("A", "B"),
                       help="show the node-count addition and radius ratio")
    group.add_argument("--self-test", action="store_true",
                       help="run the complete built-in verification suite")
    args = parser.parse_args(argv)

    try:
        if args.eval is not None:
            result = evaluate_expression_tree(parse_expression_tree(args.eval))
            print(f"{args.eval} = {_format_number(result)}")
        elif args.scene is not None:
            a_text, operator, b_text = args.scene
            result = observe_scene(build_scene(int(a_text), int(b_text), operator, seed=42))
            if not result.get("ok"):
                raise ValueError(str(result.get("reason")))
            print(f"{result['a']} {result['operator']} {result['b']} = "
                  f"{_format_number(result['result'])}")
        elif args.eml is not None:
            print(_format_number(eml(*args.eml)))
        elif args.eml_complex is not None:
            print(eml_complex(*args.eml_complex))
        elif args.export is not None:
            expression, json_name, obj_name = args.export
            scene = expression_tree_scene(parse_expression_tree(expression), seed=42)
            save_scene_json(scene, json_name)
            save_scene_obj(scene, obj_name)
            print(f"wrote {json_name} and {obj_name}")
        elif args.natural is not None:
            a, b = args.natural
            addition, status = natural_add(a, b)
            ra, rb, ratio = radius_ratio(a, b)
            print(f"node-count addition: {addition} ({status})")
            print(f"polygon radius ratio: {ra:.12g} / {rb:.12g} = {ratio:.12g}")
            print("The radius ratio is a geometric measurement, not generally A/B.")
        else:
            return 0 if run_tests() else 1
    except (OverflowError, TypeError, ValueError, ZeroDivisionError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
