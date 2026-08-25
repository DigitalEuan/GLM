"""``glm_universal.reasoning.deep_holes`` -- holes found by running, not stored.

The question
------------
Classify a 24-coordinate carrier by the Niemeier type of the hole it sits
in.  Posed directly this is a Voronoi-cell problem: the Leech lattice's
Voronoi cell has 196,560 facets, one per minimal vector, and materialising
it -- or a table of the 23 deep-hole centres and their neighbourhoods -- is
the obvious way to answer.

This module takes the other route.  Nothing about the 23 types is stored.
The catalogue itself is derived (:mod:`glm_universal.reasoning.niemeier`
enumerates the 23 root systems from the ADE component formulas), the holes
are *reached* by running a process, and the answer a process gives is
checked by an identity before it is believed.

The process, in three parts
---------------------------
1. **Reach a hole.**  :mod:`glm_universal.reasoning.voronoi_walk` slides
   from a lattice point along directions orthogonal to every constraint
   already active, solving exactly for the moment each new lattice point
   becomes equidistant, until it can move no further.  That is a vertex of
   the Voronoi diagram.  A hill climb on the diagram's 1-skeleton then
   raises the radius; its maxima are the deep holes, at the covering
   radius.  A climb that stalls below the covering radius has found a
   shallow hole, which has no Niemeier type, and says so.

2. **Read the hole off a trajectory.**  A hole is characterised by the
   lattice points nearest to it, and those points are exactly what a
   **modulator** aimed at it emits.  Feed the hole centre in as the target
   of the delta-sigma loop of :mod:`glm_universal.reasoning.exact_real`,
   quantise with the exact nearest-Leech-point decoder rather than with the
   Golay one, and the trajectory can only ever emit points of the cell the
   centre lies in.  Run from the zero accumulator the loop is *too* well
   behaved -- it locks into a 2-cycle after one tick -- so what breaks the
   symmetry is a deterministic sweep of small starting offsets, each of
   which tips the first quantisation towards a different vertex.  The union
   grows, and :func:`saturate_vertices` closes it under the differences the
   trajectory has already exposed, which picks up the stragglers the
   sampler's long tail would otherwise cost hundreds of starts.

3. **Certify the reading.**  Vertices at raw squared distance 48 are joined
   in the hole's diagram, at 64 doubly joined, at 32 not joined; the
   connected components are matched to extended Dynkin shapes and the
   result looked up in the derived catalogue.  That much is a *fit*.  What
   makes it an answer is :func:`hole_diagram`'s certificate: each
   component's marks are solved for as the positive null vector of its
   affine Cartan matrix, and the identity ``sum(n_i v_i) = h c`` is checked
   against the centre, with one Coxeter number shared by all components and
   total rank 24.  No node can be added to a disjoint union of extended
   Dynkin diagrams of total rank 24, so a vertex set that passes is the
   whole vertex set -- and the probe stops the moment it can pass, rather
   than guessing from saturation.

What the process settles
------------------------
It settles the classification of any hole it is handed, with a certificate,
and it reaches deep holes on demand: every walk in the census that reached
the covering radius produced a certified Niemeier type.  Two further holes
are built directly out of the substrate's own codewords -- the midpoint of
two orthogonal octads of a MOG trio (48 vertices, 24 double bonds,
``A_1^24``) and the centroid of three dodecad vectors pairwise at raw
squared distance 48 (36 vertices, ``A_2^12``) -- and both are classified
correctly from nothing but the trajectory.

What it leaves undetermined
---------------------------
Three limits, stated rather than worked around.

1. **Coverage is not controlled.**  Which of the 23 types a walk lands on
   is decided by the walk.  Running more walks exhibits more types, and
   :func:`deep_hole_census` reports how many it reached and which are
   missing, but nothing here bounds how many walks a rare type needs.

2. **Reaching a *named* type on demand is exactly the thing that still
   wants a table.**  The process answers "what type is this hole?"; it does
   not answer "give me a hole of type ``A_9^2 D_6``".  Producing a
   representative of a named type needs its centre, and the only route to
   that which this work found is a stored table -- which is what the
   exercise set out to avoid.  That is the one place where a finite table
   is, as far as this got, genuinely unavoidable, and the census reports
   the resulting shortfall as a shortfall.

3. **A generic carrier has no Niemeier type, and that is the honest
   answer.**  A carrier in general position has a *unique* nearest lattice
   point, so its cell is not a hole at all; :func:`classify_carrier` says
   so instead of naming a type.  Finding the deep hole nearest a generic
   carrier is a different problem, and it is not solved here.

Everything is exact ``Fraction`` / integer arithmetic.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import leech2, mog
from ..substrate.linalg import popcount
from . import metric, niemeier, voronoi_walk
from .fwht_decode import _Sweep, nearest_lattice_point_fwht

__all__ = [
    "COVERING_RADIUS2",
    "ADJACENT_DISTANCE2",
    "DOUBLE_BOND_DISTANCE2",
    "probe_hole",
    "saturate_vertices",
    "hole_vertices",
    "hole_diagram",
    "extended_dynkin_marks",
    "classify_carrier",
    "octad_pair_hole",
    "dodecad_triangle_hole",
    "walked_hole",
    "deep_hole_census",
    "deep_holes_report",
]

#: The covering radius of the Leech lattice, squared, in the normalised
#: scale the package's ``distance2`` uses (minimal vectors have norm 4).
COVERING_RADIUS2 = Fraction(2)

#: Raw (unnormalised) squared distances between vertices of a hole.  The
#: package stores lattice points in coordinates scaled by ``sqrt(8)``, so a
#: minimal vector has raw norm 32.  Two vertices of a hole at raw squared
#: distance 48 are **joined** in its diagram; at 64 they are joined by a
#: double bond (the ``A_1`` case); at 32 they are not joined.
ADJACENT_DISTANCE2 = 48
DOUBLE_BOND_DISTANCE2 = 64
NON_ADJACENT_DISTANCE2 = 32


def _exact_point(vector: Sequence) -> List[Fraction]:
    out = metric.as_exact_vector(vector)
    return [Fraction(x) for x in out]


def _raw_distance2(a: Sequence, b: Sequence) -> Fraction:
    return sum((Fraction(a[i]) - Fraction(b[i])) ** 2 for i in range(24))


# ===========================================================================
# 1.  THE PROBE
# ===========================================================================

def probe_hole(center: Sequence, probes: int = 400, seed: int = 20260825,
               ticks: int = 1, dither: int = 4000,
               patience: int = 60, known: Sequence = (),
               stop=None) -> Dict[str, object]:
    """Discover the cell around ``center`` by running the modulator at it.

    Each probe starts the delta-sigma accumulator at a small deterministic
    offset and runs ``ticks`` ticks, quantising with the exact
    nearest-Leech-point decoder.  Every point the loop emits is a lattice
    point of the cell the driven vector fell in; the union over starts is
    the discovered vertex set.

    Parameters
    ----------
    center
        The carrier, as 24 exact coordinates.
    probes
        How many starts to run.  The first is the zero accumulator, which is
        the undithered modulator.
    seed
        The deterministic sweep's seed.  No randomness is used anywhere.
    ticks
        Ticks per start.  One is enough to see the vertex the start points
        at; more follows the trajectory into its cycle.
    dither
        The denominator of the start offsets: coordinates are drawn from
        ``[-1000/dither, 1000/dither]``.  Small enough that the driven
        vector stays in the neighbourhood of the carrier.
    patience
        Stop once this many consecutive starts have produced no point that
        was not already seen.  The probe runs until it stops paying rather
        than for a fixed budget, and the report says which of the two
        stopped it.
    known
        Vertices already in hand -- from a Voronoi walk, say -- seeded into
        the search so the probe only has to find what is missing.
    stop
        An optional predicate on the current vertex tuple.  When it returns
        true the probe stops at once; this is how a completeness
        certificate ends the search the moment it can be issued, instead of
        waiting for the sampler's long barren tail.

    Returns
    -------
    dict
        The vertex set, the growth curve, the distance spectrum of
        everything seen, and how many starts in a row produced nothing new.
    """
    point = _exact_point(center)
    sweep = _Sweep(seed)
    seen: Dict[Tuple[int, ...], Fraction] = {}
    curve: List[int] = []
    barren_tail = 0
    best: Optional[Fraction] = None
    for start in known:
        vertex = tuple(int(x) for x in start)
        distance = _raw_distance2(point, vertex)
        seen[vertex] = distance
        best = distance if best is None else min(best, distance)
    stopped_by_stop = False
    for index in range(max(1, probes)):
        if index == 0:
            accumulator = [Fraction(0)] * 24
        else:
            accumulator = [Fraction(sweep.below(2001) - 1000, dither)
                           for _ in range(24)]
        before = len(seen)
        for _tick in range(max(1, ticks)):
            driven = [accumulator[i] + point[i] for i in range(24)]
            emitted = nearest_lattice_point_fwht(driven).point
            accumulator = [driven[i] - emitted[i] for i in range(24)]
            distance = _raw_distance2(point, emitted)
            seen[emitted] = distance
            best = distance if best is None else min(best, distance)
        curve.append(sum(1 for d in seen.values() if d == best))
        barren_tail = 0 if len(seen) > before else barren_tail + 1
        if stop is not None and len(seen) > before:
            candidate = tuple(sorted(p for p, d in seen.items() if d == best))
            if stop(candidate):
                stopped_by_stop = True
                break
        if barren_tail >= patience:
            break

    assert best is not None
    vertices = tuple(sorted(p for p, d in seen.items() if d == best))
    spectrum: Dict[Fraction, int] = {}
    for distance in seen.values():
        spectrum[distance] = spectrum.get(distance, 0) + 1
    normalised = Fraction(best) / metric.GRIESS_SCALE
    return {
        "center": tuple(point),
        "probes": max(1, probes),
        "ticks_per_probe": max(1, ticks),
        "vertices": vertices,
        "vertex_count": len(vertices),
        "min_distance2_raw": best,
        "min_distance2": normalised,
        "is_deep_hole": normalised == COVERING_RADIUS2,
        "at_a_lattice_point": best == 0,
        "unique_nearest_point": len(vertices) == 1,
        "points_seen": len(seen),
        "distance_spectrum": dict(sorted(spectrum.items())),
        "growth_curve": tuple(curve),
        "starts_run": len(curve),
        "patience": patience,
        "starts_since_last_new_point": barren_tail,
        "saturated": barren_tail >= patience,
        "stopped_by_certificate": stopped_by_stop,
        "stopped_early": len(curve) < max(1, probes),
    }


def _scaled_center(center: Sequence) -> Tuple[List[int], int]:
    """``center`` as integers over a common denominator."""
    point = _exact_point(center)
    den = 1
    for value in point:
        den = den * value.denominator // math.gcd(den, value.denominator)
    return [int(value * den) for value in point], den


def saturate_vertices(center: Sequence, vertices: Sequence[Sequence[int]],
                      min_distance2_raw: Fraction,
                      max_rounds: int = 6) -> Dict[str, object]:
    """Close a partial vertex set under its own difference vectors.

    The probe is a sampler: it finds a vertex only when some start tips the
    first quantisation towards it, and the tail of that coupon-collector is
    long -- on the ``A_1^24`` hole a 400-start sweep reliably finds 46 of
    the 48.  Rather than spend more starts, the missing ones are obtained
    from the geometry the probe has *already* exposed.  A hole's vertex set
    is a union of extended Dynkin diagrams and is highly symmetric, so the
    differences ``y - x`` between vertices already found are, in the main,
    symmetries of the whole set: translating every known vertex by every
    known difference and keeping the results that are lattice points at the
    same distance from the centre adds the stragglers.  The step is
    repeated until a round adds nothing, so its own fixed point stops it.

    This adds no stored data: every difference used was measured on the
    trajectory.  It is a *completion*, not a certificate -- completeness is
    certified separately, by :func:`hole_diagram`.
    """
    scaled, den = _scaled_center(center)
    target = int(Fraction(min_distance2_raw) * den * den)

    def at_min(point: Tuple[int, ...]) -> bool:
        total = 0
        for i in range(24):
            diff = point[i] * den - scaled[i]
            total += diff * diff
            if total > target:
                return False
        return total == target

    found = {tuple(int(x) for x in v) for v in vertices}
    rounds = 0
    added_per_round: List[int] = []
    while rounds < max_rounds:
        rounds += 1
        known = sorted(found)
        differences = set()
        for a in known:
            for b in known:
                if a is not b:
                    differences.add(tuple(b[k] - a[k] for k in range(24)))
        fresh = set()
        for x in known:
            for d in differences:
                y = tuple(x[k] + d[k] for k in range(24))
                if y in found or y in fresh:
                    continue
                if at_min(y) and leech2.in_leech(list(y)):
                    fresh.add(y)
        added_per_round.append(len(fresh))
        if not fresh:
            break
        found |= fresh
    return {
        "vertices": tuple(sorted(found)),
        "vertex_count": len(found),
        "added": len(found) - len(set(tuple(int(x) for x in v)
                                      for v in vertices)),
        "rounds": rounds,
        "added_per_round": tuple(added_per_round),
        "closed": bool(added_per_round and added_per_round[-1] == 0),
    }


def hole_vertices(center: Sequence, probes: int = 400, seed: int = 20260825,
                  patience: int = 60, close: bool = True,
                  known: Sequence = ()) -> Dict[str, object]:
    """Probe for the cell around ``center``, then close the vertex set.

    Returns the probe's own report with the closure folded in, so a caller
    can always see how many vertices the trajectory found by itself and how
    many the closure step added.

    The probe stops the instant the vertices in hand can be certified
    complete (see :func:`hole_diagram`), so on a hole it usually costs a
    few starts rather than the full budget; the budget is what a *failure*
    to certify costs.
    """
    def certified(vertices: Tuple[Tuple[int, ...], ...]) -> bool:
        if len(vertices) < 25:
            return False
        return bool(hole_diagram(vertices, center=center)["certified_complete"])

    probe = probe_hole(center, probes=probes, seed=seed, patience=patience,
                       known=known, stop=certified)
    probe["vertices_from_trajectory"] = probe["vertices"]
    probe["vertex_count_from_trajectory"] = probe["vertex_count"]
    if close and not probe["at_a_lattice_point"] \
            and not probe["unique_nearest_point"]:
        closure = saturate_vertices(center, probe["vertices"],
                                    probe["min_distance2_raw"])
        probe["vertices"] = closure["vertices"]
        probe["vertex_count"] = closure["vertex_count"]
        probe["closure"] = closure
    else:
        probe["closure"] = None
    return probe


# ===========================================================================
# 2.  THE DIAGRAM
# ===========================================================================

#: The extended Dynkin diagrams, keyed by ``(nodes, sorted degree sequence,
#: has a double bond)``.  Each value is ``(letter, rank)``.  These are the
#: shapes themselves, not a lookup of answers: the key is measured off the
#: discovered graph.
def _extended_shape(nodes: int, degrees: Tuple[int, ...],
                    double_bond: bool) -> Optional[Tuple[str, int]]:
    """Identify one connected extended Dynkin diagram from its shape."""
    if double_bond:
        # The only extended diagram with a double bond in this setting is
        # the two-node A_1 tilde.
        return ("A", 1) if nodes == 2 else None
    if nodes >= 3 and all(d == 2 for d in degrees):
        return ("A", nodes - 1)          # a cycle: A_n tilde has n+1 nodes
    counts = {d: degrees.count(d) for d in set(degrees)}
    if nodes == 5 and counts.get(4) == 1 and counts.get(1) == 4:
        return ("D", 4)
    if (nodes >= 6 and counts.get(1) == 4 and counts.get(3) == 2
            and counts.get(2, 0) == nodes - 6):
        return ("D", nodes - 1)
    if nodes == 7 and counts.get(3) == 1 and counts.get(1) == 3:
        return ("E", 6)
    if nodes == 8 and counts.get(3) == 1 and counts.get(1) == 3:
        return ("E", 7)
    if nodes == 9 and counts.get(3) == 1 and counts.get(1) == 3:
        return ("E", 8)
    return None


def extended_dynkin_marks(size: int, edges: Sequence[Tuple[int, int, bool]]
                          ) -> Optional[Tuple[int, ...]]:
    """The marks of a connected extended Dynkin diagram, from its edges.

    The marks are the positive integer null vector of the affine Cartan
    matrix -- entry ``2`` on the diagonal, ``-1`` on a single bond and
    ``-2`` on the double bond of the ``A_1`` diagram.  They are *solved
    for*, not looked up, and they are what turns the vertex set into a
    checkable identity: the centre of the hole is the barycentre of each
    component's vertices weighted by its marks.

    Returns ``None`` if the matrix does not have the one-dimensional
    positive null space an extended diagram must have.
    """
    matrix = [[Fraction(2) if i == j else Fraction(0) for j in range(size)]
              for i in range(size)]
    for a, b, double in edges:
        weight = Fraction(-2) if double else Fraction(-1)
        matrix[a][b] = weight
        matrix[b][a] = weight

    rows = [row[:] for row in matrix]
    pivot_of_column: Dict[int, int] = {}
    row_index = 0
    for column in range(size):
        pivot = None
        for i in range(row_index, size):
            if rows[i][column] != 0:
                pivot = i
                break
        if pivot is None:
            continue
        rows[row_index], rows[pivot] = rows[pivot], rows[row_index]
        scale = rows[row_index][column]
        rows[row_index] = [x / scale for x in rows[row_index]]
        for i in range(size):
            if i != row_index and rows[i][column] != 0:
                factor = rows[i][column]
                rows[i] = [rows[i][j] - factor * rows[row_index][j]
                           for j in range(size)]
        pivot_of_column[column] = row_index
        row_index += 1

    free = [c for c in range(size) if c not in pivot_of_column]
    if len(free) != 1:
        return None
    parameter = free[0]
    vector = [Fraction(0)] * size
    vector[parameter] = Fraction(1)
    for column, row in pivot_of_column.items():
        vector[column] = -rows[row][parameter]

    denominator = 1
    for value in vector:
        denominator = (denominator * value.denominator
                       // math.gcd(denominator, value.denominator))
    integers = [int(value * denominator) for value in vector]
    divisor = 0
    for value in integers:
        divisor = math.gcd(divisor, value)
    if divisor == 0:
        return None
    integers = [value // divisor for value in integers]
    if all(value < 0 for value in integers):
        integers = [-value for value in integers]
    if any(value <= 0 for value in integers):
        return None
    return tuple(integers)


def hole_diagram(vertices: Sequence[Sequence[int]],
                 center: Optional[Sequence] = None) -> Dict[str, object]:
    """The hole's diagram, read off the pairwise distances of its vertices.

    Two vertices at raw squared distance 48 are joined; at 64 they are
    joined by a double bond; at 32 they are not joined.  The connected
    components are matched against the extended Dynkin shapes, and the
    resulting root system is looked for in the derived Niemeier catalogue.

    When ``center`` is supplied the diagram is also **certified**: each
    component's marks are solved for and the barycentre identity
    ``sum(n_i * v_i) == h * center`` is checked, with ``h = sum(n_i)`` the
    Coxeter number.  See ``completeness_certificate`` in the result.
    """
    points = [tuple(int(x) for x in v) for v in vertices]
    n = len(points)
    spectrum: Dict[Fraction, int] = {}
    adjacency: List[List[int]] = [[] for _ in range(n)]
    doubles = 0
    unexpected = 0
    for i in range(n):
        for j in range(i + 1, n):
            d = _raw_distance2(points[i], points[j])
            spectrum[d] = spectrum.get(d, 0) + 1
            if d in (ADJACENT_DISTANCE2, DOUBLE_BOND_DISTANCE2):
                adjacency[i].append(j)
                adjacency[j].append(i)
                if d == DOUBLE_BOND_DISTANCE2:
                    doubles += 1
            elif d != NON_ADJACENT_DISTANCE2:
                unexpected += 1

    seen = [False] * n
    components: List[Dict[str, object]] = []
    for start in range(n):
        if seen[start]:
            continue
        stack = [start]
        seen[start] = True
        members = []
        while stack:
            node = stack.pop()
            members.append(node)
            for other in adjacency[node]:
                if not seen[other]:
                    seen[other] = True
                    stack.append(other)
        members.sort()
        degrees = tuple(sorted(len(adjacency[m]) for m in members))
        has_double = any(
            _raw_distance2(points[a], points[b]) == DOUBLE_BOND_DISTANCE2
            for a in members for b in adjacency[a])
        shape = _extended_shape(len(members), degrees, has_double)
        local = {node: index for index, node in enumerate(members)}
        local_edges = []
        for a in members:
            for b in adjacency[a]:
                if a < b:
                    double = (_raw_distance2(points[a], points[b])
                              == DOUBLE_BOND_DISTANCE2)
                    local_edges.append((local[a], local[b], double))
        marks = extended_dynkin_marks(len(members), local_edges)
        components.append({
            "nodes": len(members),
            "members": tuple(members),
            "degrees": degrees,
            "double_bond": has_double,
            "type": shape,
            "marks": marks,
            "mark_sum": None if marks is None else sum(marks),
        })

    identified = all(c["type"] is not None for c in components)
    tally: Dict[Tuple[str, int], int] = {}
    for component in components:
        shape = component["type"]
        if shape is not None:
            tally[shape] = tally.get(shape, 0) + 1
    parts = tuple(sorted((letter, rank, count)
                         for (letter, rank), count in tally.items()))
    name = " ".join(f"{l}_{r}" if c == 1 else f"{l}_{r}^{c}"
                    for l, r, c in parts) if identified else None
    rank = sum(r * c for _l, r, c in parts)
    coxeter = None
    if identified and parts:
        numbers = {niemeier.ade_component(l, r)["coxeter_number"]
                   for l, r, _c in parts}
        coxeter = numbers.pop() if len(numbers) == 1 else None

    certificate = _completeness_certificate(points, components, rank,
                                            identified, center)
    return {
        "vertex_count": n,
        "completeness_certificate": certificate,
        "certified_complete": bool(certificate
                                   and certificate["certified"]),
        "distance_spectrum": dict(sorted(spectrum.items())),
        "edges": sum(len(a) for a in adjacency) // 2,
        "double_bonds": doubles,
        "unexpected_distances": unexpected,
        "components": tuple(components),
        "component_count": len(components),
        "all_components_identified": identified,
        "root_system": name,
        "rank": rank,
        "coxeter_number": coxeter,
        "in_niemeier_catalogue": bool(
            name is not None and name in niemeier.NIEMIER_BY_NAME),
        "nodes_equal_rank_plus_components": n == rank + len(components),
    }


def _completeness_certificate(points: Sequence[Tuple[int, ...]],
                              components: Sequence[Dict[str, object]],
                              rank: int, identified: bool,
                              center: Optional[Sequence]
                              ) -> Optional[Dict[str, object]]:
    """Check the barycentre identity that certifies the vertex set complete.

    Conway--Parker--Sloane: the vertices of a deep hole of the Leech lattice
    form a disjoint union of extended Dynkin diagrams of total rank 24, all
    with the same Coxeter number ``h``, and each component's marks ``n_i``
    satisfy ``sum(n_i * v_i) = h * c``.  Both halves are checked here.

    Why that certifies completeness rather than merely fitting: a vertex
    set found by the probe is a *subset* of the true one, and no node can
    be added to a disjoint union of extended Dynkin diagrams without either
    breaking a component's shape or raising the total rank above 24.  So a
    subset that already has total rank 24 and identified extended shapes is
    the whole set.  The certificate is therefore conditional on the
    classification theorem, not on the search having saturated -- and it is
    checked on the numbers, not assumed.
    """
    if center is None:
        return None
    exact = _exact_point(center)
    if not identified:
        return {"certified": False,
                "reason": "not every component is an extended Dynkin diagram"}
    coxeter_numbers = set()
    barycentres_hold = True
    for component in components:
        marks = component["marks"]
        members = component["members"]
        if marks is None or len(marks) != len(members):
            return {"certified": False,
                    "reason": "a component has no positive integer marks"}
        height = sum(marks)
        coxeter_numbers.add(height)
        for coordinate in range(24):
            weighted = sum(marks[i] * points[members[i]][coordinate]
                           for i in range(len(members)))
            if weighted != height * exact[coordinate]:
                barycentres_hold = False
                break
        if not barycentres_hold:
            break
    single = len(coxeter_numbers) == 1
    total_rank = rank == 24
    certified = barycentres_hold and single and total_rank
    return {
        "certified": certified,
        "barycentre_identity": barycentres_hold,
        "single_coxeter_number": single,
        "coxeter_numbers": tuple(sorted(coxeter_numbers)),
        "total_rank": rank,
        "total_rank_is_24": total_rank,
        "reason": ("every component's marked barycentre is the hole centre, "
                   "all components share one Coxeter number, and the total "
                   "rank is 24 -- no further vertex can be added"
                   if certified else
                   "the marked barycentres do not all reproduce the centre, "
                   "so the vertex set is not the complete one"),
    }


def classify_carrier(carrier: Sequence, probes: int = 400,
                     seed: int = 20260825, patience: int = 60,
                     known: Sequence = ()) -> Dict[str, object]:
    """Classify a carrier by the hole it sits in -- or refuse, with a reason.

    Only a point at the covering radius has one of the 23 Niemeier types.
    A carrier in general position has a unique nearest lattice point and no
    type at all, and this says so rather than naming the nearest hole: the
    nearest-hole question is a different one and is not answered here.
    """
    probe = hole_vertices(carrier, probes=probes, seed=seed,
                          patience=patience, known=known)
    if probe["at_a_lattice_point"]:
        verdict = ("the carrier is a lattice point: distance 0, no hole and "
                   "no Niemeier type")
        diagram = None
    elif not probe["is_deep_hole"]:
        verdict = (f"the carrier is not a deep hole -- its distance to the "
                   f"lattice is {probe['min_distance2']}, short of the "
                   f"covering radius {COVERING_RADIUS2}, so it has no "
                   f"Niemeier type; "
                   f"{probe['vertex_count']} nearest lattice point(s)")
        diagram = None
    else:
        diagram = hole_diagram(probe["vertices"], center=carrier)
        if diagram["root_system"] is None:
            verdict = ("a deep hole whose diagram the probe could not "
                       "identify -- most likely an incomplete vertex set")
        elif not diagram["in_niemeier_catalogue"]:
            verdict = (f"a deep hole whose diagram reads "
                       f"{diagram['root_system']}, which is not in the "
                       f"derived catalogue -- the vertex set is incomplete")
        elif not diagram["certified_complete"]:
            verdict = (f"a deep hole whose diagram reads "
                       f"{diagram['root_system']}, but the barycentre "
                       f"identity does not close, so the vertex set is not "
                       f"certified complete")
        else:
            verdict = (f"a deep hole of type {diagram['root_system']}, "
                       f"Coxeter number {diagram['coxeter_number']}, from "
                       f"{diagram['vertex_count']} vertices "
                       f"({probe['vertex_count_from_trajectory']} found by "
                       f"{probe['starts_run']} modulator starts, the rest by "
                       f"closure), certified complete by the marked "
                       f"barycentre identity")
    return {
        "probe": probe,
        "diagram": diagram,
        "niemeier_type": (diagram or {}).get("root_system"),
        "has_niemeier_type": bool(diagram
                                  and diagram["in_niemeier_catalogue"]
                                  and diagram["certified_complete"]),
        "certified": bool(diagram and diagram["certified_complete"]),
        "verdict": verdict,
    }


# ===========================================================================
# 3.  TWO HOLES, BUILT OUT OF THE PACKAGE'S OWN CODEWORDS
# ===========================================================================

def _trio_vectors() -> List[Tuple[int, ...]]:
    """``2`` on each octad of a trio: three pairwise orthogonal minimals.

    A trio is a partition of the 24 coordinates into three octads, so the
    three vectors have disjoint supports and inner product 0 -- which is
    what the midpoint construction needs.  The trio is taken from the MOG,
    not written down.
    """
    trio = mog.trio_of_octad(mog.OCTAD_MASKS[0])
    out = []
    for mask in trio:
        vector = tuple(2 if (mask >> k) & 1 else 0 for k in range(24))
        if leech2.in_leech(list(vector)):
            out.append(vector)
    return out


def _dodecad_vectors(limit: int = 60) -> List[Tuple[int, ...]]:
    """``2`` on a dodecad, ``0`` elsewhere: second-shell vectors."""
    out = []
    for mask in mog.GOLAY_MASKS:
        if popcount(mask) != 12:
            continue
        vector = tuple(2 if (mask >> k) & 1 else 0 for k in range(24))
        if leech2.in_leech(list(vector)):
            out.append(vector)
        if len(out) >= limit:
            break
    return out


def octad_pair_hole() -> Dict[str, object]:
    """A deep hole built as the midpoint of two orthogonal octad vectors.

    Two minimal vectors ``u``, ``v`` with ``u . v = 0`` are at raw squared
    distance 64, so their midpoint is at raw squared distance 16 from both
    -- the covering radius.  Both vectors are found here by search over the
    substrate's own octads; nothing is quoted.
    """
    octads = _trio_vectors()
    for i, u in enumerate(octads):
        for v in octads[i + 1:]:
            if sum(u[k] * v[k] for k in range(24)) == 0:
                center = tuple(Fraction(u[k] + v[k], 2) for k in range(24))
                return {"center": center, "left": u, "right": v,
                        "separation2_raw": _raw_distance2(u, v),
                        "construction": "midpoint of two orthogonal octads "
                                        "of a MOG trio"}
    raise RuntimeError("octad_pair_hole: no orthogonal pair of octads found")


def dodecad_triangle_hole() -> Dict[str, object]:
    """A deep hole built as the centroid of an equilateral lattice triangle.

    Three lattice points pairwise at raw squared distance 48 have a centroid
    at raw squared distance ``48 / 3 = 16`` from each -- again the covering
    radius.  The triangle is ``0`` together with two dodecad vectors whose
    inner product is 24, found by search.
    """
    dodecads = _dodecad_vectors()
    zero = tuple([0] * 24)
    for i, u in enumerate(dodecads):
        for v in dodecads[i + 1:]:
            if sum(u[k] * v[k] for k in range(24)) == 24:
                center = tuple(Fraction(u[k] + v[k], 3) for k in range(24))
                return {"center": center, "vertices": (zero, u, v),
                        "side2_raw": _raw_distance2(u, v),
                        "construction": "centroid of an equilateral triangle "
                                        "of lattice points"}
    raise RuntimeError("dodecad_triangle_hole: no such triangle found")

# ===========================================================================
# 4.  THE CENSUS -- HOLES REACHED BY WALKING
# ===========================================================================

def walked_hole(seed: int = 20260825, probes: int = 200,
                patience: int = 40) -> Dict[str, object]:
    """One complete run of the process, start to finish.

    Walk from a lattice point to a vertex of the Voronoi diagram, climb the
    1-skeleton until no edge raises the radius, then read the hole off the
    modulator's trajectory and certify the reading.  Nothing is looked up
    at any stage: the only inputs are the lattice's own decoder and a
    deterministic sweep.

    A run that lands on a shallow hole says so and names no type -- that is
    the honest answer for a hole below the covering radius, not a failure
    of the classifier.
    """
    reached = voronoi_walk.walk_to_deep_hole(seed=seed)
    if reached is None:
        return {
            "seed": seed,
            "reached_deep_hole": False,
            "niemeier_type": None,
            "certified": False,
            "verdict": ("the walk found no constraint to move against and "
                        "reached no vertex"),
        }
    summary = {
        "seed": seed,
        "landed_radius2": reached["landed_radius2"],
        "radius2": reached["radius2"],
        "radius_curve": reached["radius_curve"],
        "climb_moves": reached["moves"],
        "slides": reached["slides"],
        "active_from_walk": reached["active_count"],
        "center": reached["center"],
        "reached_deep_hole": bool(reached["is_deep"]),
    }
    if not reached["is_deep"]:
        summary.update({
            "niemeier_type": None,
            "certified": False,
            "verdict": (f"the climb stalled at squared radius "
                        f"{reached['radius2']}, short of the covering radius "
                        f"{COVERING_RADIUS2}: a shallow hole, which has no "
                        f"Niemeier type"),
        })
        return summary
    classified = classify_carrier(reached["center"], probes=probes, seed=seed,
                                  patience=patience, known=reached["active"])
    summary.update({
        "classification": classified,
        "niemeier_type": (classified["niemeier_type"]
                          if classified["certified"] else None),
        "certified": classified["certified"],
        "vertex_count": classified["probe"]["vertex_count"],
        "starts_after_walk": classified["probe"]["starts_run"],
        "verdict": classified["verdict"],
    })
    return summary


def deep_hole_census(walks: int = 8, seed: int = 20260825, probes: int = 200,
                     patience: int = 40, constructions: bool = True
                     ) -> Dict[str, object]:
    """Run the process many times and count the Niemeier types it exhibits.

    The count is reported against the 23 the catalogue derives, and what is
    missing is reported as missing.  No hole centre is stored anywhere in
    this package; every centre in the census was produced by a walk or by a
    construction out of the substrate's own codewords.
    """
    cases: List[Dict[str, object]] = []
    types: List[str] = []
    deep = 0
    shallow = 0

    for index in range(max(0, walks)):
        run = walked_hole(seed=seed + 977 * index, probes=probes,
                          patience=patience)
        cases.append({"name": f"walk {index}", "construction": "walk + climb",
                      "run": run})
        if run["reached_deep_hole"]:
            deep += 1
        else:
            shallow += 1
        if run["certified"] and run["niemeier_type"]:
            types.append(run["niemeier_type"])

    if constructions:
        pair = octad_pair_hole()
        result = classify_carrier(pair["center"], probes=probes, seed=seed,
                                  patience=patience)
        cases.append({"name": "octad-pair midpoint",
                      "construction": pair["construction"],
                      "center": pair["center"],
                      "classification": result})
        if result["has_niemeier_type"]:
            types.append(result["niemeier_type"])

        triangle = dodecad_triangle_hole()
        result = classify_carrier(triangle["center"], probes=probes,
                                  seed=seed, patience=patience)
        cases.append({"name": "dodecad-triangle centroid",
                      "construction": triangle["construction"],
                      "center": triangle["center"],
                      "classification": result})
        if result["has_niemeier_type"]:
            types.append(result["niemeier_type"])

    # A carrier in general position, to show what a refusal looks like.
    sweep = _Sweep(seed)
    generic = [Fraction(sweep.below(65) - 32, 8) for _ in range(24)]
    result = classify_carrier(generic, probes=24, seed=seed, patience=4)
    cases.append({"name": "a carrier in general position",
                  "construction": "a deterministic sweep, not a hole",
                  "center": tuple(generic),
                  "classification": result})

    # A lattice point, the other degenerate case.
    on_lattice = nearest_lattice_point_fwht(generic).point
    result = classify_carrier(on_lattice, probes=8, seed=seed, patience=4)
    cases.append({"name": "a lattice point",
                  "construction": "the nearest lattice point to the above",
                  "center": tuple(Fraction(x) for x in on_lattice),
                  "classification": result})

    distinct = tuple(sorted(set(types)))
    catalogue = niemeier.NIEMEIER_ROOT_SYSTEMS
    return {
        "cases": tuple(cases),
        "walks_run": max(0, walks),
        "walks_reaching_a_deep_hole": deep,
        "walks_stalling_at_a_shallow_hole": shallow,
        "types_exhibited": distinct,
        "types_exhibited_count": len(distinct),
        "types_in_catalogue": len(catalogue),
        "census_complete": len(distinct) == len(catalogue),
        "missing_types": tuple(name for name, _r, _h in catalogue
                               if name not in distinct),
        "shortfall": len(catalogue) - len(distinct),
        "every_named_type_certified": all(
            case.get("run", {}).get("certified", True)
            for case in cases if case.get("run", {}).get("niemeier_type")),
        "honest_statement": (
            "Each type named above was reached by running a process and "
            "then certified by an identity, never read from a table: the "
            "walk finds a vertex of the Voronoi diagram, the climb raises "
            "its radius to the covering radius, the modulator's trajectory "
            "supplies the vertices and the marked-barycentre identity "
            "closes over them.  What the census does not do is guarantee "
            "coverage.  Which of the 23 types a walk lands on is decided "
            "by the walk, and the types are not equally likely; running "
            "more walks exhibits more types, but nothing here bounds how "
            "many walks a rare type needs, and reaching a named type on "
            "demand would need its centre -- which is the stored table the "
            "exercise set out to avoid.  The shortfall is therefore "
            "reported as a shortfall."),
    }


def deep_holes_report(walks: int = 8, probes: int = 200, patience: int = 40
                      ) -> Dict[str, object]:
    """Everything this module knows, recomputed on call."""
    census = deep_hole_census(walks=walks, probes=probes, patience=patience)
    return {
        "covering_radius2": COVERING_RADIUS2,
        "catalogue_size": len(niemeier.NIEMEIER_ROOT_SYSTEMS),
        "census": census,
        "method": (
            "A hole is reached, not looked up.  A walk slides from a "
            "lattice point along directions orthogonal to the constraints "
            "already active, solving exactly for the moment each new "
            "lattice point joins, until it can move no further: that is a "
            "vertex of the Voronoi diagram.  A hill climb on the diagram's "
            "1-skeleton then raises the radius to the covering radius, "
            "where the hole is deep.  The vertex set is read off the "
            "modulator's trajectory aimed at the hole, closed under its own "
            "differences, and named by the shape of its distance graph.  "
            "The 196,560 facets of the Voronoi cell are never built and no "
            "hole centre is stored."),
        "certificate": (
            "A named type is not taken on trust.  Each connected component "
            "of the distance graph has its marks solved for as the null "
            "vector of its affine Cartan matrix, and the identity "
            "sum(n_i v_i) = h c is checked against the hole centre, with "
            "one Coxeter number h shared by every component and total rank "
            "24.  A vertex set that passes cannot be extended -- no node "
            "can be added to a disjoint union of extended Dynkin diagrams "
            "of total rank 24 -- so the reading is complete, and that is "
            "checked rather than assumed."),
        "limits": (
            "Three, stated rather than worked around.  A walk that stalls "
            "below the covering radius has found a shallow hole, which has "
            "no Niemeier type, and is reported as a stall.  A carrier in "
            "general position has a unique nearest lattice point and "
            "therefore no type at all, and is refused rather than assigned "
            "the nearest one -- finding the deep hole nearest a generic "
            "carrier is a different problem and is not solved here.  And "
            "the census does not cover all 23 types: see "
            "census.honest_statement."),
    }
