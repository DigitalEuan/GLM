"""Exact pressure-settling probe for 2-D square packing.

This is a **declared computational analogy**, not a proof of optimal packing.
It uses the two wheel laws that already exist in the repository:

* W36: ``pair_energy = pair_penetration^2`` and
  ``wall_energy = container_violation^2``;
* W37: ``relaxation_time = viscosity / modulus`` and
  ``strain_rate = stress / viscosity``.

The engine is restricted to axis-aligned unit squares in a fixed square
container.  A pair's SAT penetration is treated as stress (the declared W36
to W37 junction).  An explicit relaxation step then moves overlapping squares
apart along the minimum-penetration axis.  The step fraction is
``min(1, dt / relaxation_time)``.

The resulting objective is the W36 energy.  The engine can find a feasible
packing for a declared initial state, but it does not search all configurations
and therefore does not claim global optimality.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Sequence

SCHEMA = "cent-packing/1"
ENGINE = "pressure-settling"
SOURCE_WHEELS = ("W36", "W37")
PRIMITIVE_CHAIN = ("mult", "sum", "div", "scale", "accum", "sat", "dissipate")
OBJECTIVE = "sum(pair_penetration^2) + sum(container_violation^2)"
INSTANCE_SCOPE = "axis-aligned unit squares in a fixed square container"

Q = Fraction


@dataclass(frozen=True)
class Square:
    """One axis-aligned unit square, with its lower-left corner."""

    id: str
    x: Q
    y: Q

    def as_dict(self) -> dict[str, str]:
        return {"id": self.id, "x": str(self.x), "y": str(self.y)}


@dataclass(frozen=True)
class PackingState:
    """The measured state of one packing configuration."""

    squares: tuple[Square, ...]
    energy: Q
    max_penetration: Q
    total_penetration: Q
    max_wall_violation: Q
    pair_count: int
    wall_count: int

    @property
    def feasible(self) -> bool:
        return (
            self.max_penetration == 0
            and self.max_wall_violation == 0
        )

    def as_dict(self) -> dict:
        return {
            "energy": str(self.energy),
            "max_penetration": str(self.max_penetration),
            "total_penetration": str(self.total_penetration),
            "max_wall_violation": str(self.max_wall_violation),
            "pair_count": self.pair_count,
            "wall_count": self.wall_count,
            "feasible": self.feasible,
            "placements": [square.as_dict() for square in self.squares],
        }


def _fraction(value: object, name: str) -> Q:
    try:
        return value if isinstance(value, Fraction) else Fraction(str(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{name} must be an exact rational") from exc


def default_squares(n: int, side: Q) -> tuple[Square, ...]:
    """A deliberate fully-overlapped start state for the probe."""
    if n < 1:
        raise ValueError("n must be at least 1")
    if side <= 0:
        raise ValueError("container side must be positive")
    centre = side / 2
    return tuple(Square(f"s{index}", centre, centre) for index in range(n))


def _pair_penetration(a: Square, b: Square) -> tuple[Q, str, Q]:
    """Return (penetration, axis, direction-for-a), or (0, '', 0)."""
    overlap_x = min(a.x + 1, b.x + 1) - max(a.x, b.x)
    overlap_y = min(a.y + 1, b.y + 1) - max(a.y, b.y)
    if overlap_x <= 0 or overlap_y <= 0:
        return Q(0), "", Q(0)
    if overlap_x < overlap_y:
        penetration, axis = overlap_x, "x"
    elif overlap_y < overlap_x:
        penetration, axis = overlap_y, "y"
    else:
        penetration = overlap_x
        axis = "x" if a.id <= b.id else "y"
    if axis == "x":
        direction = Q(1) if a.x == b.x and a.id <= b.id else (
            Q(-1) if a.x <= b.x else Q(1)
        )
    else:
        direction = Q(1) if a.y == b.y and a.id <= b.id else (
            Q(-1) if a.y <= b.y else Q(1)
        )
    return penetration, axis, direction


def _wall_violations(square: Square, side: Q) -> tuple[Q, ...]:
    return (
        max(Q(0), -square.x),
        max(Q(0), square.x + 1 - side),
        max(Q(0), -square.y),
        max(Q(0), square.y + 1 - side),
    )


def measure(squares: Sequence[Square], side: Q) -> PackingState:
    """Measure the exact W36 energy and maximum constraints."""
    total = Q(0)
    total_penetration = Q(0)
    max_penetration = Q(0)
    max_wall = Q(0)
    pair_count = 0
    wall_count = 0
    ordered = tuple(squares)
    for index, left in enumerate(ordered):
        for right in ordered[index + 1:]:
            penetration, _, _ = _pair_penetration(left, right)
            if penetration:
                pair_count += 1
                total_penetration += penetration
                max_penetration = max(max_penetration, penetration)
                total += penetration * penetration
    for square in ordered:
        for violation in _wall_violations(square, side):
            if violation:
                wall_count += 1
                max_wall = max(max_wall, violation)
                total += violation * violation
    return PackingState(
        squares=ordered,
        energy=total,
        max_penetration=max_penetration,
        total_penetration=total_penetration,
        max_wall_violation=max_wall,
        pair_count=pair_count,
        wall_count=wall_count,
    )


def _relax_once(
    squares: Sequence[Square],
    *,
    side: Q,
    alpha: Q,
) -> tuple[Square, ...]:
    """One deterministic overlap/wall projection step."""
    moved = {square.id: [square.x, square.y] for square in squares}
    ordered = tuple(squares)
    for index, left in enumerate(ordered):
        for right in ordered[index + 1:]:
            penetration, axis, direction = _pair_penetration(left, right)
            if not penetration:
                continue
            step = alpha * penetration / 2
            if axis == "x":
                moved[left.id][0] += direction * step
                moved[right.id][0] -= direction * step
            else:
                moved[left.id][1] += direction * step
                moved[right.id][1] -= direction * step
    for square in ordered:
        x, y = moved[square.id]
        if x < 0:
            x += alpha * (-x)
        elif x + 1 > side:
            x -= alpha * (x + 1 - side)
        if y < 0:
            y += alpha * (-y)
        elif y + 1 > side:
            y -= alpha * (y + 1 - side)
        moved[square.id] = [x, y]
    return tuple(
        Square(square.id, moved[square.id][0], moved[square.id][1])
        for square in ordered
    )


def settle(
    n: int = 2,
    *,
    side: object = 2,
    initial: Iterable[Square] | None = None,
    iterations: int = 12,
    dt: object = Fraction(1, 4),
    viscosity: object = 1,
    modulus: object = 4,
    tolerance: object = 0,
) -> dict:
    """Run the exact pressure-settling probe.

    The return value is a JSON-serialisable ``cent-packing/1`` payload.  The
    fixed-container result is a feasibility result, never a global optimum.
    """
    container_side = _fraction(side, "side")
    dt_q = _fraction(dt, "dt")
    eta = _fraction(viscosity, "viscosity")
    elastic_modulus = _fraction(modulus, "modulus")
    tolerance_q = _fraction(tolerance, "tolerance")
    if n < 1:
        raise ValueError("n must be at least 1")
    if container_side <= 0:
        raise ValueError("container side must be positive")
    if dt_q <= 0 or eta <= 0 or elastic_modulus <= 0:
        raise ValueError("dt, viscosity and modulus must be positive")
    if iterations < 0:
        raise ValueError("iterations must be non-negative")
    if tolerance_q < 0:
        raise ValueError("tolerance must be non-negative")

    squares = tuple(initial) if initial is not None else default_squares(n, container_side)
    if len(squares) != n:
        raise ValueError("initial placements must contain exactly n squares")
    if len({square.id for square in squares}) != n:
        raise ValueError("square ids must be unique")
    for square in squares:
        if not isinstance(square, Square):
            raise ValueError("initial entries must be Square records")

    relaxation_time = eta / elastic_modulus
    alpha = min(Q(1), dt_q / relaxation_time)
    state = measure(squares, container_side)
    initial_state = state
    trace = [{
        "iteration": 0,
        "energy": str(state.energy),
        "max_penetration": str(state.max_penetration),
        "max_wall_violation": str(state.max_wall_violation),
    }]
    used = 0
    for iteration in range(1, iterations + 1):
        used = iteration
        squares = _relax_once(squares, side=container_side, alpha=alpha)
        state = measure(squares, container_side)
        trace.append({
            "iteration": iteration,
            "energy": str(state.energy),
            "max_penetration": str(state.max_penetration),
            "max_wall_violation": str(state.max_wall_violation),
        })
        if state.energy <= tolerance_q:
            break

    feasible = state.feasible
    gaps = []
    if not feasible:
        gaps.append("the declared iteration budget did not reach zero overlap/wall violation")
    gaps.extend([
        "global optimality is not proved; the engine has no exhaustive search or lower bound",
        "only axis-aligned unit squares in a fixed square container are declared",
        "no rotation, arbitrary square sizes, physical device or fabrication netlist is declared",
        "the relaxation projection is a declared numerical scheme, not a hardware simulation",
    ])
    return {
        "ok": True,
        "schema": SCHEMA,
        "engine": ENGINE,
        "source_wheels": list(SOURCE_WHEELS),
        "primitive_chain": list(PRIMITIVE_CHAIN),
        "objective": OBJECTIVE,
        "instance": {
            "n": n,
            "container_side": str(container_side),
            "scope": INSTANCE_SCOPE,
        },
        "relaxation": {
            "viscosity": str(eta),
            "modulus": str(elastic_modulus),
            "relaxation_time": str(relaxation_time),
            "dt": str(dt_q),
            "alpha": str(alpha),
            "law": "alpha = min(1, dt / (viscosity / modulus))",
        },
        "iterations": {"requested": iterations, "used": used},
        "initial": initial_state.as_dict(),
        "final": state.as_dict(),
        "passed": feasible,
        "settled": state.energy <= tolerance_q,
        "optimal": False,
        "optimality_gap": (
            "fixed-container pressure relaxation only; no global optimality "
            "certificate or exhaustive configuration search"
        ),
        "gaps": gaps,
        "trace": trace,
        "provenance": {
            "w36": "pair_energy = pair_penetration^2; wall_energy = container_violation^2",
            "w37": "relaxation_time = viscosity / modulus; strain_rate = stress / viscosity",
            "junction": "W36 pair_penetration is read as W37 stress",
            "claim": "declared computational analogy; not a measured device or optimal solver",
        },
    }


def render_text(payload: dict) -> str:
    """Render the probe without upgrading it to an optimality claim."""
    lines = [
        "=" * 78,
        "PRESSURE SETTLING PACKING PROBE",
        "=" * 78,
        f"engine       {payload['engine']}",
        f"objective    {payload['objective']}",
        f"scope        {payload['instance']['scope']}",
        f"n / side     {payload['instance']['n']} / {payload['instance']['container_side']}",
        f"relaxation   {payload['relaxation']['law']}",
        f"alpha        {payload['relaxation']['alpha']}",
        f"initial      energy {payload['initial']['energy']} · "
        f"max penetration {payload['initial']['max_penetration']}",
        f"final        energy {payload['final']['energy']} · "
        f"max penetration {payload['final']['max_penetration']} · "
        f"max wall {payload['final']['max_wall_violation']}",
        f"feasible     {payload['passed']}",
        f"optimal      {payload['optimal']}",
        f"gap          {payload['optimality_gap']}",
    ]
    lines.append("")
    lines.append("Placements")
    for square in payload["final"]["placements"]:
        lines.append(f"  {square['id']:<8} x={square['x']:<12} y={square['y']}")
    lines.append("")
    lines.append("Gaps")
    for gap in payload["gaps"]:
        lines.append(f"  - {gap}")
    return "\n".join(lines)


__all__ = [
    "SCHEMA",
    "ENGINE",
    "SOURCE_WHEELS",
    "PRIMITIVE_CHAIN",
    "OBJECTIVE",
    "INSTANCE_SCOPE",
    "Square",
    "PackingState",
    "default_squares",
    "measure",
    "settle",
    "render_text",
]
