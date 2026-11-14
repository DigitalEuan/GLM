"""Exact finite-direction orientation envelopes.

This is a computational method, not a physical model.  Given exact rational
points and a declared set of rational direction vectors, it projects the points
onto each direction and its exact normal, forms the enclosing rectangle, and
returns the minimum-area rectangle over that declared set.

The method is deliberately finite: it does not search every real orientation.
The returned ``area`` is the exact physical area because the projection basis
has determinant ``dx^2 + dy^2``; the individual projected extents are not
claimed to be unit-normalized lengths.

No liquid-crystal, optical or other physical behavior is simulated here.  A
quadrupolar-orientation story can be attached as optional interpretation, but
the acceptance surface is exact projection arithmetic and a finite search.
"""
from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Iterable, Sequence

from .exact import Q, q, q_to_json

SCHEMA = "cent-envelope/1"
METHOD = "finite-direction-minimax"

Point = tuple[Q, Q]
Direction = tuple[Q, Q]

#: Declared default directions.  They are rational, pairwise distinct after
#: primitive normalization, and include the axis and common diagonal slopes.
DEFAULT_DIRECTIONS: tuple[Direction, ...] = (
    (Fraction(1), Fraction(0)),
    (Fraction(0), Fraction(1)),
    (Fraction(1), Fraction(1)),
    (Fraction(1), Fraction(-1)),
    (Fraction(2), Fraction(1)),
    (Fraction(1), Fraction(2)),
    (Fraction(3), Fraction(1)),
    (Fraction(1), Fraction(3)),
)


def _fraction(value: Any, name: str) -> Q:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an exact rational, not boolean")
    try:
        return value if isinstance(value, Fraction) else q(value)
    except Exception as exc:
        raise ValueError(f"{name} must be an exact rational: {value!r}") from exc


def parse_point(text: str) -> Point:
    """Parse one ``x,y`` exact point."""
    parts = str(text).split(",")
    if len(parts) != 2:
        raise ValueError(f"point must be 'x,y': {text!r}")
    return _fraction(parts[0], "point.x"), _fraction(parts[1], "point.y")


def _point(value: Any, index: int) -> Point:
    if isinstance(value, str):
        return parse_point(value)
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError(f"point {index} must be a pair or 'x,y' string")
    return _fraction(value[0], f"point[{index}].x"), _fraction(
        value[1], f"point[{index}].y"
    )


def _canonical_direction(value: Any, index: int) -> Direction:
    if isinstance(value, str):
        parts = value.split(",")
        if len(parts) != 2:
            raise ValueError(f"direction must be 'dx,dy': {value!r}")
        dx = _fraction(parts[0], "direction.dx")
        dy = _fraction(parts[1], "direction.dy")
    elif isinstance(value, (tuple, list)) and len(value) == 2:
        dx = _fraction(value[0], f"direction[{index}].dx")
        dy = _fraction(value[1], f"direction[{index}].dy")
    else:
        raise ValueError(f"direction {index} must be a pair or 'dx,dy' string")
    if dx == 0 and dy == 0:
        raise ValueError("direction must be nonzero")
    # Convert the rational direction to a primitive integer direction so
    # (1,1), (2,2) and (1/2,1/2) deduplicate to the same projection.
    denominator = math.lcm(dx.denominator, dy.denominator)
    ix = dx.numerator * (denominator // dx.denominator)
    iy = dy.numerator * (denominator // dy.denominator)
    divisor = math.gcd(abs(ix), abs(iy))
    ix //= divisor
    iy //= divisor
    if ix < 0 or (ix == 0 and iy < 0):
        ix, iy = -ix, -iy
    return Fraction(ix), Fraction(iy)


def _candidate(points: Sequence[Point], direction: Direction) -> dict[str, Any]:
    dx, dy = direction
    nx, ny = -dy, dx
    norm2 = dx * dx + dy * dy
    us = [dx * x + dy * y for x, y in points]
    vs = [nx * x + ny * y for x, y in points]
    u_min, u_max = min(us), max(us)
    v_min, v_max = min(vs), max(vs)
    projected_width = u_max - u_min
    projected_height = v_max - v_min
    # u = D p and v = N p, with det([D; N]) = dx^2 + dy^2.  The rectangle
    # area in p-space is therefore width*height / norm2.
    area = projected_width * projected_height / norm2

    def corner(u: Q, v: Q) -> list[dict[str, str]]:
        x = (dx * u - dy * v) / norm2
        y = (dy * u + dx * v) / norm2
        return [q_to_json(x), q_to_json(y)]

    return {
        "direction": [q_to_json(dx), q_to_json(dy)],
        "normal": [q_to_json(nx), q_to_json(ny)],
        "norm2": q_to_json(norm2),
        "u_range": {"min": q_to_json(u_min), "max": q_to_json(u_max)},
        "v_range": {"min": q_to_json(v_min), "max": q_to_json(v_max)},
        "projected_width": q_to_json(projected_width),
        "projected_height": q_to_json(projected_height),
        "area": q_to_json(area),
        "corners": [
            corner(u_min, v_min),
            corner(u_max, v_min),
            corner(u_max, v_max),
            corner(u_min, v_max),
        ],
        "_area": area,
        "_direction": (dx, dy),
    }


def orientation_envelope(
    points: Iterable[Any],
    directions: Iterable[Any] | None = None,
) -> dict[str, Any]:
    """Return the exact minimum-area envelope over declared rational directions."""
    parsed_points = tuple(
        _point(value, index) for index, value in enumerate(points)
    )
    if not parsed_points:
        raise ValueError("at least one point is required")

    raw_directions = tuple(DEFAULT_DIRECTIONS if directions is None else directions)
    if not raw_directions:
        raise ValueError("at least one direction is required")
    unique: list[Direction] = []
    for index, value in enumerate(raw_directions):
        direction = _canonical_direction(value, index)
        if direction not in unique:
            unique.append(direction)

    candidates = [_candidate(parsed_points, direction) for direction in unique]
    candidates.sort(key=lambda item: (item["_area"], item["_direction"]))
    for rank, candidate in enumerate(candidates, start=1):
        candidate["rank"] = rank
    best = candidates[0]
    area = best["_area"]

    checks = [
        {
            "name": "point set",
            "status": "pass" if parsed_points else "gap",
            "detail": f"{len(parsed_points)} exact rational point(s)",
        },
        {
            "name": "direction set",
            "status": "pass" if unique else "gap",
            "detail": f"{len(unique)} unique declared rational direction(s)",
        },
        {
            "name": "point containment",
            "status": "pass",
            "detail": "every point lies inside the selected projection bounds",
        },
    ]
    for candidate in candidates:
        candidate.pop("_area", None)
        candidate.pop("_direction", None)

    return {
        "ok": True,
        "schema": SCHEMA,
        "method": METHOD,
        "points": [[q_to_json(x), q_to_json(y)] for x, y in parsed_points],
        "directions": [[q_to_json(x), q_to_json(y)] for x, y in unique],
        "candidates": candidates,
        "best": best,
        "summary": {
            "points": len(parsed_points),
            "directions": len(unique),
            "best_area": q_to_json(area),
            "best_direction": best["direction"],
            "best_rank": 1,
            "candidate_count": len(candidates),
            "optimal_over_declared_directions": True,
            "global_optimal": False,
        },
        "checks": checks,
        "passed": all(check["status"] == "pass" for check in checks),
        "gaps": [
            "the minimum is over the finite declared direction set, not every real orientation",
            "the projected extents are not unit-normalized; the returned area is exact",
            "no physical, liquid-crystal, optical or fabrication interpretation is simulated",
        ],
        "claim": (
            "Exact finite-direction minimax envelope over rational points; "
            "computational construction only."
        ),
    }


def render_text(payload: dict[str, Any]) -> str:
    """Render one envelope result for the terminal."""
    best = payload["best"]
    direction = best["direction"]
    lines = [
        "=" * 78,
        "ORIENTATION ENVELOPE",
        "=" * 78,
        f"method       {payload['method']}",
        f"points       {payload['summary']['points']}",
        f"directions   {payload['summary']['directions']}",
        f"best area    {payload['summary']['best_area']}",
        f"best dir     ({direction[0]['num']}/{direction[0]['den']}, "
        f"{direction[1]['num']}/{direction[1]['den']})",
        f"global opt   {payload['summary']['global_optimal']}",
        "",
        "Corners",
    ]
    for corner in best["corners"]:
        lines.append(f"  ({corner[0]['num']}/{corner[0]['den']}, "
                     f"{corner[1]['num']}/{corner[1]['den']})")
    lines.append("")
    lines.append("Gaps")
    for gap in payload["gaps"]:
        lines.append(f"  - {gap}")
    return "\n".join(lines)


__all__ = [
    "SCHEMA",
    "METHOD",
    "DEFAULT_DIRECTIONS",
    "parse_point",
    "orientation_envelope",
    "render_text",
]
