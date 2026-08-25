"""``glm_universal.reasoning.voronoi_walk`` -- holes reached by walking.

The Leech lattice's Voronoi cell has 196,560 facets.  A *hole* is a vertex
of the Voronoi diagram: a point equidistant from enough lattice points that
no direction moves away from all of them.  The deep holes -- the ones at
the covering radius -- are the global maxima of the distance-to-lattice
function, and they are what the Niemeier classification is a
classification of.

Nothing here enumerates facets or stores hole centres.  A hole is *reached*:

``vertex_walk``
    Start at a lattice point.  Repeatedly pick a direction orthogonal to
    every constraint that is already active, and slide along it until one
    more lattice point becomes equidistant with the active set.  Each slide
    raises the number of active constraints by at least one, so after at
    most 24 slides the active set spans and the point can move no further:
    it is a vertex of the Voronoi diagram.  The stopping distance of each
    slide is *solved for* exactly -- a linear equation in one unknown --
    rather than searched, so the walk lands on the vertex exactly, in
    rationals, with no rounding anywhere.

``climb``
    A vertex has one Voronoi edge for each active constraint it can drop.
    Dropping one and sliding along the resulting edge lands on a
    neighbouring vertex, whose radius is larger or smaller.  Taking any
    edge that increases the radius, until none does, is a hill climb on the
    1-skeleton of the Voronoi diagram, and its maxima are the deep holes.

Both are processes, and their behaviour -- not a table -- is the answer.
The one thing the walk depends on is a nearest-lattice-point oracle, and
the package already has an exact one
(:func:`glm_universal.reasoning.fwht_decode.nearest_lattice_point_fwht`).

Every number here is an exact ``Fraction``.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import metric
from .fwht_decode import _Sweep, nearest_lattice_point_fwht

__all__ = [
    "DIM",
    "dot",
    "squared_distance",
    "orthogonal_direction",
    "crossing_time",
    "advance",
    "vertex_walk",
    "climb",
    "walk_to_deep_hole",
]

DIM = 24

#: How far inside a computed crossing the walk probes when it checks that no
#: earlier constraint was skipped.  Any value strictly between 0 and 1 does;
#: this one leaves a thousandth of the step.
_INSIDE = Fraction(999, 1000)


def dot(a: Sequence, b: Sequence) -> Fraction:
    return sum(Fraction(a[i]) * Fraction(b[i]) for i in range(DIM))


def squared_distance(a: Sequence, b: Sequence) -> Fraction:
    return sum((Fraction(a[i]) - Fraction(b[i])) ** 2 for i in range(DIM))


def _orthogonalise(vectors: Sequence[Sequence]) -> List[Tuple[List[Fraction],
                                                              Fraction]]:
    """Gram-Schmidt, exactly, dropping dependent vectors."""
    basis: List[Tuple[List[Fraction], Fraction]] = []
    for vector in vectors:
        current = [Fraction(x) for x in vector]
        for b, norm in basis:
            factor = dot(current, b) / norm
            current = [current[i] - factor * b[i] for i in range(DIM)]
        norm = dot(current, current)
        if norm != 0:
            basis.append((current, norm))
    return basis


def orthogonal_direction(vectors: Sequence[Sequence], sweep: _Sweep
                         ) -> Optional[List[Fraction]]:
    """A nonzero vector orthogonal to every vector given, or ``None``.

    ``None`` means the vectors already span, so there is nowhere left to
    move -- which is exactly the walk's stopping condition.
    """
    basis = _orthogonalise(vectors)
    if len(basis) >= DIM:
        return None
    for _attempt in range(64):
        candidate = [Fraction(sweep.below(21) - 10) for _ in range(DIM)]
        for b, norm in basis:
            factor = dot(candidate, b) / norm
            candidate = [candidate[i] - factor * b[i] for i in range(DIM)]
        if dot(candidate, candidate) != 0:
            return candidate
    return None


def crossing_time(center: Sequence, direction: Sequence, active: Sequence,
                  challenger: Sequence) -> Optional[Fraction]:
    """When does ``challenger`` become as close as ``active``?

    Solves ``|c + t d - w|^2 == |c + t d - v|^2`` for ``t``.  The quadratic
    terms cancel, so this is one linear equation and the answer is exact.
    """
    w = [Fraction(x) for x in challenger]
    v = [Fraction(x) for x in active]
    numerator = (dot(w, w) - 2 * dot(center, w)
                 - dot(v, v) + 2 * dot(center, v))
    denominator = 2 * (dot(direction, w) - dot(direction, v))
    if denominator == 0:
        return None
    return numerator / denominator


def advance(center: Sequence, active: Sequence[Tuple[int, ...]],
            direction: Sequence) -> Optional[Dict[str, object]]:
    """Slide from ``center`` along ``direction`` to the next constraint.

    ``active`` is the set of lattice points currently equidistant and
    nearest.  The slide stops at the first point along the ray at which a
    lattice point outside ``active`` becomes equidistant with it.  Finding
    that point is a cutting loop: probe far out, take whatever the decoder
    says is nearest there, solve for the time at which *it* would join,
    step back to just inside that time and probe again.  The loop stops
    when the decoder no longer names anything new, and the time it stops at
    is the true first crossing.
    """
    center = [Fraction(x) for x in center]
    direction = [Fraction(x) for x in direction]
    known = set(active)

    step = Fraction(1)
    challenger = None
    for _ in range(26):
        probe = [center[i] + step * direction[i] for i in range(DIM)]
        candidate = nearest_lattice_point_fwht(probe).point
        if candidate not in known:
            challenger = candidate
            break
        step *= 2
    if challenger is None:
        return None

    time: Optional[Fraction] = None
    for _ in range(64):
        candidate_time = crossing_time(center, direction, active[0],
                                       challenger)
        if candidate_time is None or candidate_time <= 0:
            return None
        probe = [center[i] + candidate_time * _INSIDE * direction[i]
                 for i in range(DIM)]
        nearest = nearest_lattice_point_fwht(probe).point
        if nearest in known or nearest == challenger:
            time = candidate_time
            break
        challenger = nearest
    if time is None:
        return None

    moved = [center[i] + time * direction[i] for i in range(DIM)]
    radius = squared_distance(moved, active[0])
    kept = [v for v in active if squared_distance(moved, v) == radius]
    if squared_distance(moved, challenger) == radius:
        kept.append(challenger)
    return {"center": moved, "active": kept, "radius2_raw": radius,
            "time": time, "joined": challenger}


def vertex_walk(seed: int = 20260825, spread: int = 250,
                max_slides: int = 40) -> Optional[Dict[str, object]]:
    """Walk from a lattice point to a vertex of the Voronoi diagram.

    Returns ``None`` only if the walk could not find a constraint to move
    against, which is reported rather than retried.
    """
    sweep = _Sweep(seed)
    start = [Fraction(sweep.below(2 * spread * 4 + 1) - spread * 4, spread)
             for _ in range(DIM)]
    base = nearest_lattice_point_fwht(start).point
    center: List[Fraction] = [Fraction(x) for x in base]
    active: List[Tuple[int, ...]] = [base]
    radius = Fraction(0)
    slides = 0
    for _ in range(max_slides):
        offsets = [[Fraction(v[i]) - Fraction(active[0][i]) for i in range(DIM)]
                   for v in active[1:]]
        direction = orthogonal_direction(offsets, sweep)
        if direction is None:
            break
        step = advance(center, active, direction)
        if step is None:
            step = advance(center, active, [-x for x in direction])
        retries = 0
        while step is None and retries < 6:
            # A direction can fail: the cutting loop may not settle, or the
            # ray may leave along a degenerate face.  Try another direction
            # in the same free space rather than abandoning the walk.
            retries += 1
            direction = orthogonal_direction(offsets, sweep)
            if direction is None:
                break
            step = advance(center, active, direction)
            if step is None:
                step = advance(center, active, [-x for x in direction])
        if step is None:
            return None
        center = step["center"]
        active = step["active"]
        radius = step["radius2_raw"]
        slides += 1
    return {
        "center": tuple(center),
        "active": tuple(active),
        "active_count": len(active),
        "radius2_raw": radius,
        "radius2": radius / metric.GRIESS_SCALE,
        "slides": slides,
        "seed": seed,
    }


def climb(center: Sequence, active: Sequence[Tuple[int, ...]],
          radius2_raw: Fraction, seed: int = 20260825,
          max_moves: int = 24) -> Dict[str, object]:
    """Hill-climb the Voronoi 1-skeleton until no edge raises the radius.

    One move drops a single active constraint, which frees a line, and
    slides along that line in the direction that takes the dropped point
    *away* -- so the remaining constraints stay the nearest ones -- to the
    next vertex.  The first move found that increases the radius is taken.
    """
    sweep = _Sweep(seed)
    center = [Fraction(x) for x in center]
    active = list(active)
    radius = Fraction(radius2_raw)
    curve = [radius / metric.GRIESS_SCALE]
    moves = 0
    for _ in range(max_moves):
        improved = False
        for dropped in list(active):
            kept = [v for v in active if v != dropped]
            if len(kept) < 2:
                continue
            offsets = [[Fraction(v[i]) - Fraction(kept[0][i])
                        for i in range(DIM)] for v in kept[1:]]
            direction = orthogonal_direction(offsets, sweep)
            if direction is None:
                continue
            recede = sum(direction[i] * (Fraction(dropped[i])
                                         - Fraction(kept[0][i]))
                         for i in range(DIM))
            if recede == 0:
                continue
            if recede > 0:
                direction = [-x for x in direction]
            step = advance(center, kept, direction)
            if step is None:
                continue
            if step["radius2_raw"] > radius:
                center = step["center"]
                active = step["active"]
                radius = step["radius2_raw"]
                curve.append(radius / metric.GRIESS_SCALE)
                moves += 1
                improved = True
                break
        if not improved:
            break
    return {
        "center": tuple(center),
        "active": tuple(active),
        "active_count": len(active),
        "radius2_raw": radius,
        "radius2": radius / metric.GRIESS_SCALE,
        "moves": moves,
        "radius_curve": tuple(curve),
        "stalled": moves == 0,
    }


def walk_to_deep_hole(seed: int = 20260825, spread: int = 250
                      ) -> Optional[Dict[str, object]]:
    """Walk to a Voronoi vertex, then climb.  The whole process, once.

    The result records the radius the walk landed on and the radius the
    climb reached, so a run that stalls short of the covering radius is
    visible as a stall rather than being dressed up.
    """
    landed = vertex_walk(seed=seed, spread=spread)
    if landed is None:
        return None
    climbed = climb(landed["center"], landed["active"],
                    landed["radius2_raw"], seed=seed + 1)
    climbed["landed_radius2"] = landed["radius2"]
    climbed["landed_active_count"] = landed["active_count"]
    climbed["slides"] = landed["slides"]
    climbed["seed"] = seed
    climbed["is_deep"] = climbed["radius2"] == Fraction(2)
    return climbed
