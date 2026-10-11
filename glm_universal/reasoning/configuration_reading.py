"""``glm_universal.reasoning.configuration_reading`` -- the configuration
reading ``L5`` of the deep-hole ladder, for the 28-vertex pair of lattice
item 6 (Phase 122).

The question
------------
``studies/SHARE_SEPARATION_STUDY.md`` §7 left lattice item 6 narrowed to one
pair of reference holes, ``E_6^4`` and ``D_6^4``: both have 28 vertices, so
once every arrival share is near ``1/28`` a *sorted* list of shares cannot
tell them apart.  ``studies/CONFIGURATION_READING_STUDY.md`` pre-registered a
reading that keeps what sorting discards -- how the reached vertices sit
relative to one another -- and six marks.

The reading
-----------
For an emission record the arrival vertices ``V`` are the emitted points at
the minimum squared distance ``r^2``.  Two of them are joined with
multiplicity 1 when their squared distance is ``3 r^2`` and 2 when it is
``4 r^2`` (the affine Dynkin diagram of the hole, read from the points
alone).  Each arrival vertex gets the key ``(size of its component, degree
with multiplicity)``, and the profile is the pushforward of the arrival
shares along the key: ``key -> total share``.  Profiles are compared in L1
over the union of their keys (``GLM.ConfigurationReading.push`` and ``l1``).

What this module does
---------------------
It applies the reading to the stored ensembles of
:mod:`glm_universal.reasoning.share_ensemble` at every stored size, reports
the ladder's cell statistics (``Q0``, ``W``, ``B``, ``rho`` and the per-hole
ratio) exactly as :func:`share_separation.cell` computes them, checks the
control (the diagram the arrival vertices form is the affine diagram of the
label) and the bound of ``config_shift_le_matched``, and scores the marks.

Exactness
---------
Integers and :class:`~fractions.Fraction` only.  Nothing here decodes a
lattice point.
"""

from __future__ import annotations

import re
from collections import Counter
from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from . import deep_hole_escalation as de
from . import share_ensemble as se
from . import share_separation as ss

__all__ = [
    "LEAN_MODULE", "LAYER", "STATISTICS_TRIED", "UNIFORM_CLOSEST",
    "arrivals", "multiplicity_graph", "vertex_keys", "configuration_profile",
    "configuration_distance", "affine_keys", "expected_keys", "control_rows",
    "NIEMEIER_TYPES", "niemeier_uniform_floor", "uniform_distance",
    "cell", "bound_rows", "configuration_report",
]

#: The Lean file that proves the bound, the uniform-limit distances and the
#: separation floor.
LEAN_MODULE: str = "RequestProject/GLM/ConfigurationReading.lean"

#: The rung's name, beside the ladder's four.
LAYER: str = "configuration"

#: Phase 121's 36 statistics plus the eight ``L5`` cells of this round.
STATISTICS_TRIED: int = ss.STATISTICS_TRIED + len(se.SIZES)

#: The pre-registered uniform-limit closest pair and its distance
#: (``GLM.ConfigurationReading.e8_d8_uniform_distance``), and the 28-vertex
#: pair's (``e6_d6_uniform_distance``).
UNIFORM_CLOSEST: Tuple[str, str, Fraction] = ("E_8^3", "D_8^3", Fraction(4, 9))
UNIFORM_PAIR: Tuple[str, str, Fraction] = ("E_6^4", "D_6^4", Fraction(4, 7))

Point = Tuple[int, ...]
Key = Tuple[int, int]


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE READING
# ═════════════════════════════════════════════════════════════════════════

def arrivals(record: Sequence[Tuple]
             ) -> Tuple[Dict[Point, Fraction], Optional[Fraction]]:
    """The arrival shares and the arrival squared distance ``r^2``.

    ``record`` is an emission record of ``(point, distance)`` pairs or a
    stored multiset of ``(point, distance, count)`` triples
    (:func:`share_ensemble.multiset`); the reading is the same either way.
    """
    if not record:
        return {}, None
    triples = [(item[0], item[1], item[2] if len(item) > 2 else 1)
               for item in record]
    best = min(distance for _point, distance, _count in triples)
    counts: Dict[Point, int] = {}
    for point, distance, count in triples:
        if distance == best:
            counts[point] = counts.get(point, 0) + int(count)
    total = sum(counts.values())
    return ({point: Fraction(count, total) for point, count in counts.items()},
            best)


def _sq(left: Point, right: Point) -> int:
    return sum((a - b) ** 2 for a, b in zip(left, right))


def multiplicity_graph(points: Sequence[Point], r2: Fraction
                       ) -> Dict[Tuple[int, int], int]:
    """The edges ``(i, j) -> multiplicity`` among ``points``: 1 at squared
    distance ``3 r^2``, 2 at ``4 r^2``."""
    edges: Dict[Tuple[int, int], int] = {}
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = _sq(points[i], points[j])
            if d == 3 * r2:
                edges[(i, j)] = 1
            elif d == 4 * r2:
                edges[(i, j)] = 2
    return edges


def vertex_keys(points: Sequence[Point], r2: Fraction) -> Tuple[Key, ...]:
    """``(component size, degree with multiplicity)`` for each point."""
    n = len(points)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    degree = [0] * n
    for (i, j), m in multiplicity_graph(points, r2).items():
        degree[i] += m
        degree[j] += m
        a, b = find(i), find(j)
        if a != b:
            parent[a] = b
    sizes = Counter(find(i) for i in range(n))
    return tuple((sizes[find(i)], degree[i]) for i in range(n))


def configuration_profile(record: Sequence[Tuple]
                          ) -> Tuple[Tuple[Key, Fraction], ...]:
    """``L5``: the arrival shares pushed forward along the diagram key,
    as sorted ``(key, share)`` pairs."""
    shares, r2 = arrivals(record)
    if not shares or r2 is None:
        return ()
    points = sorted(shares)
    keys = vertex_keys(points, r2)
    out: Dict[Key, Fraction] = {}
    for point, key in zip(points, keys):
        out[key] = out.get(key, Fraction(0)) + shares[point]
    return tuple(sorted(out.items()))


def configuration_distance(left: Sequence[Tuple[Key, Fraction]],
                           right: Sequence[Tuple[Key, Fraction]]) -> Fraction:
    """L1 over the union of the keys (``GLM.ConfigurationReading.l1``)."""
    a, b = dict(left), dict(right)
    return sum((abs(a.get(k, Fraction(0)) - b.get(k, Fraction(0)))
                for k in set(a) | set(b)), Fraction(0))


def _records(data: Dict[str, object], starts: int
             ) -> Tuple[Tuple[str, Tuple, Tuple], ...]:
    """Per hole, the stored multisets of both seeds at ``starts``."""
    return tuple((str(hole["label"]), se.multiset(hole["reference"], starts),
                  se.multiset(hole["sanity"], starts))
                 for hole in data["holes"])


def matched_share_shift(left: Sequence[Tuple], right: Sequence[Tuple]
                        ) -> Fraction:
    """The vertex-matched share shift of :mod:`share_separation`, from two
    stored multisets."""
    a, _ = arrivals(left)
    b, _ = arrivals(right)
    return sum((abs(a.get(k, Fraction(0)) - b.get(k, Fraction(0)))
                for k in set(a) | set(b)), Fraction(0))


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE CONTROL: THE AFFINE DIAGRAM OF THE LABEL
# ═════════════════════════════════════════════════════════════════════════

def affine_keys(family: str, rank: int) -> Counter:
    """The keys of the affine diagram of one irreducible root system."""
    nodes = rank + 1
    if family == "A":
        return Counter({(nodes, 2): nodes})          # a cycle; A_1 a double edge
    if family == "D":
        if rank == 4:
            return Counter({(5, 1): 4, (5, 4): 1})
        return Counter({(nodes, 1): 4, (nodes, 2): rank - 5, (nodes, 3): 2})
    if family == "E":
        return Counter({(nodes, 1): 3, (nodes, 2): rank - 3, (nodes, 3): 1})
    raise ValueError(f"affine_keys: unknown family {family!r}")


def expected_keys(label: str) -> Counter:
    """The keys of every vertex of a deep hole of type ``label``."""
    total: Counter = Counter()
    for family, rank, power in re.findall(r"([ADE])_(\d+)(?:\^(\d+))?", label):
        for key, count in affine_keys(family, int(rank)).items():
            total[key] += count * int(power or 1)
    return total


def control_rows(data: Dict[str, object], starts: int
                 ) -> Tuple[Dict[str, object], ...]:
    """K2: at ``starts``, per hole and seed, whether the arrival vertices are
    the declared vertex set and their diagram is the label's."""
    declared = {str(e["type"]): set(tuple(int(x) for x in v)
                                     for v in e["vertices"])
                for e in de.reference_entries()[0]}
    rows = []
    for label, ref, san in _records(data, starts):
        for role, record in (("reference", ref), ("sanity", san)):
            shares, r2 = arrivals(record)
            points = sorted(shares)
            keys = Counter(vertex_keys(points, r2)) if r2 is not None else Counter()
            same_set = set(points) == declared[label]
            same_diagram = keys == expected_keys(label)
            rows.append({"label": label, "seed": role,
                         "arrivals": len(points),
                         "declared": len(declared[label]),
                         "vertex_set": same_set, "diagram": same_diagram,
                         "holds": same_set and same_diagram})
    return tuple(rows)


#: The 23 Niemeier root systems, each the type of a class of deep holes of
#: the Leech lattice; ten of them are the reference holes.
NIEMEIER_TYPES: Tuple[str, ...] = (
    "D_24", "D_16 E_8", "E_8^3", "A_24", "D_12^2", "A_17 E_7", "D_10 E_7^2",
    "A_15 D_9", "D_8^3", "A_12^2", "A_11 D_7 E_6", "E_6^4", "A_9^2 D_6",
    "D_6^4", "A_8^3", "A_7^2 D_5^2", "A_6^4", "A_5^4 D_4", "D_4^6", "A_4^6",
    "A_3^8", "A_2^12", "A_1^24")


def niemeier_uniform_floor() -> Dict[str, object]:
    """Post hoc, never a mark: the least ``L5`` uniform-limit distance over
    all pairs of the 23 Niemeier types, and the three closest pairs."""
    pairs = sorted((uniform_distance(a, b), a, b)
                   for i, a in enumerate(NIEMEIER_TYPES)
                   for b in NIEMEIER_TYPES[i + 1:])
    return {"pairs": len(pairs), "floor": pairs[0][0],
            "closest": tuple(pairs[:3])}


def uniform_distance(left: str, right: str) -> Fraction:
    """The ``L5`` distance between two labels' uniform-limit profiles."""
    def profile(label: str) -> Dict[Key, Fraction]:
        keys = expected_keys(label)
        total = sum(keys.values())
        return {k: Fraction(c, total) for k, c in keys.items()}
    return configuration_distance(tuple(profile(left).items()),
                                  tuple(profile(right).items()))


# ═════════════════════════════════════════════════════════════════════════
# 3.  ONE CELL, AND THE BOUND
# ═════════════════════════════════════════════════════════════════════════

def cell(data: Dict[str, object], starts: int) -> Dict[str, object]:
    """The ladder's cell statistics for ``L5`` at ``starts``, computed as
    :func:`share_separation.cell` computes them for the other rungs."""
    table = _records(data, starts)
    references = [(label, configuration_profile(ref)) for label, ref, _ in table]
    sanity = [(label, configuration_profile(san)) for label, _, san in table]
    passes = 0
    worst: Optional[Fraction] = None
    rows: List[Dict[str, object]] = []
    for index, (label, profile) in enumerate(sanity):
        distances = [(name, configuration_distance(profile, reference))
                     for name, reference in references]
        own = distances[index][1]
        best = min(distance for _name, distance in distances)
        winners = [name for name, distance in distances if distance == best]
        correct = len(winners) == 1 and winners[0] == label
        passes += int(correct)
        worst = own if worst is None else max(worst, own)
        nearest_other = min(
            configuration_distance(references[index][1], other)
            for name, other in references if name != label)
        local = (None if nearest_other == 0
                 else Fraction(2) * own / nearest_other)
        rows.append({"label": label, "own_distance": own,
                     "nearest_other_reference": nearest_other,
                     "local_ratio": local,
                     "locally_certified": local is not None and local < 1,
                     "correct": correct})
    separation: Optional[Fraction] = None
    closest: Optional[Tuple[str, str]] = None
    for i in range(len(references)):
        for j in range(i + 1, len(references)):
            distance = configuration_distance(references[i][1],
                                              references[j][1])
            if separation is None or distance < separation:
                separation = distance
                closest = (references[i][0], references[j][0])
    ratio = (None if separation is None or separation == 0 or worst is None
             else Fraction(2) * worst / separation)
    pair = {row["label"]: row for row in rows}
    pair_distance = configuration_distance(dict(references)[UNIFORM_PAIR[0]],
                                           dict(references)[UNIFORM_PAIR[1]])
    return {
        "layer": LAYER, "starts": starts, "q0": passes, "gate": len(table),
        "spread": worst, "separation": separation, "closest_pair": closest,
        "ratio": ratio, "ratio_below_one": ratio is not None and ratio < 1,
        "locally_certified": sum(1 for row in rows if row["locally_certified"]),
        "pair_distance": pair_distance,
        "pair_certified": all(pair[name]["locally_certified"]
                              for name in UNIFORM_PAIR[:2]),
        "rows": tuple(rows),
    }


def bound_rows(data: Dict[str, object]) -> Tuple[Dict[str, object], ...]:
    """``config_shift_le_matched`` at every hole and size: the configuration
    seed shift against the vertex-matched share shift."""
    out = []
    for starts in data["sizes"]:
        for label, ref, san in _records(data, int(starts)):
            shift = configuration_distance(configuration_profile(ref),
                                           configuration_profile(san))
            matched = matched_share_shift(ref, san)
            out.append({"starts": int(starts), "label": label,
                        "configuration_shift": shift,
                        "matched_share": matched, "holds": shift <= matched})
    return tuple(out)


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE REPORT AND ITS MARKS
# ═════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def configuration_report() -> Dict[str, object]:
    """Every ``L5`` cell, the control, the bound, and the six marks."""
    data = se.current()
    if data is None:
        return {"available": False, "lean": LEAN_MODULE,
                "reason": "the share ensembles are absent or stale; re-take "
                          "them with python3 -m glm_universal.tools "
                          "share-ensemble --write"}
    sizes = tuple(int(n) for n in data["sizes"])
    top = sizes[-1]
    cells = tuple(cell(data, n) for n in sizes)
    by_size = {c["starts"]: c for c in cells}

    control = control_rows(data, top)
    k2 = bool(control) and all(row["holds"] for row in control)
    bounds = bound_rows(data)
    k3 = bool(bounds) and all(row["holds"] for row in bounds)
    top_cell = by_size[top]
    k4 = bool(top_cell["ratio_below_one"])
    k5 = top_cell["locally_certified"] == top_cell["gate"]
    climb = [by_size[n] for n in sizes if n >= 1920]
    k6 = all(c["q0"] == c["gate"] and c["ratio_below_one"] for c in climb)

    labels = [str(e["type"]) for e in de.reference_entries()[0]]
    limit = min(((uniform_distance(a, b), a, b)
                 for i, a in enumerate(labels) for b in labels[i + 1:]),
                key=lambda t: t[0])
    first_below = next((c["starts"] for c in cells if c["ratio_below_one"]),
                       None)
    marks = {"K1": True,   # the Lean file; checked by the build, pinned by tests
             "K2": k2, "K3": k3, "K4": k4, "K5": k5, "K6": k6}
    return {
        "available": True, "lean": LEAN_MODULE, "sizes": sizes, "top": top,
        "cells": cells, "control": control,
        "control_holds": sum(1 for row in control if row["holds"]),
        "bounds": bounds, "bound_instances": len(bounds),
        "bound_holds": sum(1 for row in bounds if row["holds"]),
        "uniform_closest": {"pair": (limit[1], limit[2]), "distance": limit[0]},
        "uniform_pair": {"pair": UNIFORM_PAIR[:2],
                         "distance": uniform_distance(*UNIFORM_PAIR[:2])},
        "first_below_one": first_below,
        "niemeier": niemeier_uniform_floor(),
        "statistics_tried": STATISTICS_TRIED,
        "marks": marks,
        "marks_met": sum(1 for value in marks.values() if value),
    }
