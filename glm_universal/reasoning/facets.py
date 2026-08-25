"""``glm_universal.reasoning.facets`` -- the six-facet decomposition.

What this module is
-------------------
A carrier is a point of ``Q^24``, and the 24 coordinates are not a formless
list: the physics layout spends them on six *facets* of what a concept is.

============  ============  ===============================================
facet         coordinates   what it carries
============  ============  ===============================================
dimension     0..16         the ten EXT10 exponents and their SI7 projection
scale         17            the decimal exponent
tensor_rank   18            the tensor rank
context       19, 20, 21    the P, T and C gradings
nominal_kind  22            the nominal-kind index
domain        23            the domain index
============  ============  ===============================================

Those six index sets **partition** ``{0, ..., 23}``: every coordinate belongs
to exactly one facet and none is left over.  :func:`partition_report` checks
that rather than trusting the table.

Strict linearity
----------------
Each facet gives an honest linear projector ``P_F`` on ``Q^24`` -- the diagonal
0/1 matrix of its coordinates -- and :func:`linearity_report` verifies the five
properties that make the decomposition a decomposition, on exact rational
carriers:

* additivity ``P(u+v) = P(u) + P(v)`` and homogeneity ``P(cu) = c P(u)``;
* idempotence ``P.P = P``;
* orthogonality ``P_F . P_G = 0`` for ``F != G``;
* completeness ``sum_F P_F = I``;
* Pythagoras: the squared Griess distance is the *sum* of the six facet
  distances, exactly -- the Griess form is the scaled standard form, so
  distinct facets contribute independently.

Two lattices per facet, and the gap between them
------------------------------------------------
Restricting the *lattice* to a facet can mean two different things, and they
are not the same lattice:

``projection``  ``pi_F(Lambda)`` -- what a facet-local reader sees of every
                Leech point;
``intersection``  ``Lambda ∩ span(F)`` -- the Leech points that live entirely
                inside the facet.

Always ``Lambda ∩ span(F) ⊆ pi_F(Lambda)``, and the index between them is
finite and computed exactly by :func:`facet_lattice_report`.  That index is
the precise amount of cross-facet entanglement of the Leech lattice at that
facet: it counts the facet-local configurations that are *only* reachable with
help from coordinates outside the facet.  Where the index is 1 the facet is
lattice-autonomous; where it is large, facet-local reasoning is reading a
shadow.

Everything is exact: ``int`` and ``Fraction`` only.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import leech_construct
from ..substrate.linalg import det_int
from . import metric

__all__ = [
    "FACET_ORDER", "FACET_INDICES", "FACET_DESCRIPTION",
    "facet_of_coordinate", "partition_report",
    "projector_matrix", "project", "facet_coordinates", "decompose",
    "reassemble", "linearity_report",
    "facet_distance_breakdown", "pythagoras_report",
    "projection_lattice_basis", "intersection_lattice_basis",
    "facet_lattice_report", "facets_report",
]

DIM = 24

#: The six facets, in coordinate order.
FACET_ORDER: Tuple[str, ...] = (
    "dimension", "scale", "tensor_rank", "context", "nominal_kind", "domain")

#: Which coordinates each facet owns.  A partition of ``range(24)``.
FACET_INDICES: Dict[str, Tuple[int, ...]] = {
    "dimension": tuple(range(0, 17)),
    "scale": (17,),
    "tensor_rank": (18,),
    "context": (19, 20, 21),
    "nominal_kind": (22,),
    "domain": (23,),
}

FACET_DESCRIPTION: Dict[str, str] = {
    "dimension": ("the ten EXT10 exponents L M T I H N J A S B and the "
                  "seven-coordinate SI7 projection of them"),
    "scale": "the decimal exponent: the quantity is 10^scale coherent units",
    "tensor_rank": "the tensor rank (0 scalar, 1 vector, 2 tensor, ...)",
    "context": ("the P, T and C gradings -- the discrete symmetry context a "
                "quantity sits in"),
    "nominal_kind": "the nominal-kind index: what sort of thing it is",
    "domain": "the domain index: which register the concept came from",
}


# ===========================================================================
# 1.  THE PARTITION
# ===========================================================================

def facet_of_coordinate(index: int) -> str:
    """Which facet owns a coordinate."""
    if not 0 <= index < DIM:
        raise ValueError("facet_of_coordinate: index must be in 0..23")
    for name in FACET_ORDER:
        if index in FACET_INDICES[name]:
            return name
    raise AssertionError("the facet table does not cover the coordinates")


def partition_report() -> Dict[str, object]:
    """Verify that the six index sets partition the 24 coordinates."""
    seen: Dict[int, List[str]] = {i: [] for i in range(DIM)}
    for name in FACET_ORDER:
        for i in FACET_INDICES[name]:
            if not 0 <= i < DIM:
                raise AssertionError(f"facet {name} names coordinate {i}")
            seen[i].append(name)
    overlaps = {i: names for i, names in seen.items() if len(names) > 1}
    uncovered = [i for i, names in seen.items() if not names]
    sizes = {name: len(FACET_INDICES[name]) for name in FACET_ORDER}
    return {
        "facets": len(FACET_ORDER),
        "sizes": sizes,
        "total": sum(sizes.values()),
        "covers_24": sum(sizes.values()) == DIM and not uncovered,
        "disjoint": not overlaps,
        "is_partition": not overlaps and not uncovered
                        and sum(sizes.values()) == DIM,
        "overlaps": overlaps,
        "uncovered": uncovered,
    }


# ===========================================================================
# 2.  THE PROJECTORS
# ===========================================================================

def projector_matrix(name: str) -> Tuple[Tuple[int, ...], ...]:
    """The 24x24 diagonal 0/1 matrix of the facet."""
    indices = _indices(name)
    return tuple(tuple(1 if (i == j and i in indices) else 0
                       for j in range(DIM)) for i in range(DIM))


def _indices(name: str) -> Tuple[int, ...]:
    try:
        return FACET_INDICES[name]
    except KeyError:
        raise ValueError(f"unknown facet {name!r}; "
                         f"expected one of {FACET_ORDER}") from None


def project(carrier: Sequence, name: str) -> Tuple[Fraction, ...]:
    """``P_F carrier``: the carrier with every other coordinate zeroed."""
    exact = metric.as_exact_vector(carrier)
    indices = set(_indices(name))
    return tuple(exact[i] if i in indices else Fraction(0)
                 for i in range(DIM))


def facet_coordinates(carrier: Sequence, name: str) -> Tuple[Fraction, ...]:
    """Just the facet's own coordinates, in order."""
    exact = metric.as_exact_vector(carrier)
    return tuple(exact[i] for i in _indices(name))


def decompose(carrier: Sequence) -> Dict[str, Tuple[Fraction, ...]]:
    """The carrier written as six projections, one per facet."""
    return {name: project(carrier, name) for name in FACET_ORDER}


def reassemble(parts: Dict[str, Sequence]) -> Tuple[Fraction, ...]:
    """Add the six projections back up."""
    out = [Fraction(0)] * DIM
    for name, vec in parts.items():
        _indices(name)
        exact = metric.as_exact_vector(vec)
        for i in range(DIM):
            out[i] += exact[i]
    return tuple(out)


def _sample_carriers() -> List[Tuple[Fraction, ...]]:
    """A deterministic sample of rational carriers, for the audits."""
    out: List[Tuple[Fraction, ...]] = []
    for k in range(6):
        out.append(tuple(Fraction((i + 1) * (k + 1), (i % 5) + 1)
                         for i in range(DIM)))
    for i in range(DIM):
        v = [Fraction(0)] * DIM
        v[i] = Fraction(1)
        out.append(tuple(v))
    out.append(tuple(Fraction(0) for _ in range(DIM)))
    out.append(tuple(Fraction(-i, 3) for i in range(DIM)))
    return out


def linearity_report() -> Dict[str, object]:
    """Additivity, homogeneity, idempotence, orthogonality, completeness."""
    sample = _sample_carriers()
    additive = True
    homogeneous = True
    idempotent = True
    complete = True
    scalar = Fraction(-7, 3)
    for u, v in zip(sample, sample[1:]):
        total = [Fraction(0)] * DIM
        for name in FACET_ORDER:
            pu, pv = project(u, name), project(v, name)
            summed = tuple(a + b for a, b in zip(u, v))
            if project(summed, name) != tuple(a + b for a, b in zip(pu, pv)):
                additive = False
            scaled = tuple(scalar * a for a in u)
            if project(scaled, name) != tuple(scalar * a for a in pu):
                homogeneous = False
            if project(pu, name) != pu:
                idempotent = False
            for i in range(DIM):
                total[i] += pu[i]
        if tuple(total) != tuple(u):
            complete = False
    orthogonal = True
    for u in sample:
        for a in FACET_ORDER:
            for b in FACET_ORDER:
                if a == b:
                    continue
                if any(x != 0 for x in project(project(u, a), b)):
                    orthogonal = False
    return {
        "checked_carriers": len(sample),
        "additive": additive,
        "homogeneous": homogeneous,
        "idempotent": idempotent,
        "orthogonal": orthogonal,
        "complete": complete,
        "strictly_linear": all((additive, homogeneous, idempotent,
                                orthogonal, complete)),
    }


# ===========================================================================
# 3.  DISTANCE, FACET BY FACET
# ===========================================================================

def facet_distance_breakdown(u: Sequence, v: Sequence
                             ) -> Dict[str, Fraction]:
    """The squared Griess distance split across the six facets."""
    return {name: metric.distance2(project(u, name), project(v, name))
            for name in FACET_ORDER}


def pythagoras_report(pairs: Optional[Sequence[Tuple[Sequence, Sequence]]]
                      = None) -> Dict[str, object]:
    """The six facet distances add up to the whole distance, exactly."""
    if pairs is None:
        sample = _sample_carriers()
        pairs = list(zip(sample, sample[1:]))
    failures: List[Dict[str, object]] = []
    for u, v in pairs:
        parts = facet_distance_breakdown(u, v)
        total = sum(parts.values(), Fraction(0))
        whole = metric.distance2(u, v)
        if total != whole:
            failures.append({"total_of_parts": str(total),
                             "whole": str(whole)})
    return {
        "checked_pairs": len(pairs),
        "additive": not failures,
        "failures": failures,
    }


# ===========================================================================
# 4.  THE TWO LATTICES OF A FACET
# ===========================================================================

def projection_lattice_basis(name: str) -> Tuple[Tuple[int, ...], ...]:
    """A Z-basis of ``pi_F(Lambda)`` inside ``Z^F``, in Hermite normal form."""
    return leech_construct.projection_lattice_basis(_indices(name))


def intersection_lattice_basis(name: str) -> Tuple[Tuple[int, ...], ...]:
    """A Z-basis of ``Lambda ∩ span(F)``, written in ``Z^F`` coordinates."""
    return leech_construct.supported_sublattice_basis(_indices(name))


def _determinant(basis: Sequence[Sequence[int]], rank: int) -> Optional[int]:
    if len(basis) != rank:
        return None
    return abs(det_int([list(r) for r in basis]))


@lru_cache(maxsize=None)
def _facet_lattice(name: str) -> Dict[str, object]:
    indices = _indices(name)
    k = len(indices)
    proj = projection_lattice_basis(name)
    inter = intersection_lattice_basis(name)
    dproj = _determinant(proj, k)
    dinter = _determinant(inter, k)
    index: Optional[int] = None
    if dproj and dinter:
        if dinter % dproj:
            raise AssertionError("the intersection is not a sublattice of "
                                 "the projection")
        index = dinter // dproj
    return {
        "facet": name,
        "coordinates": indices,
        "rank": k,
        "projection_rank": len(proj),
        "projection_determinant": dproj,
        "intersection_rank": len(inter),
        "intersection_determinant": dinter,
        "index": index,
        "lattice_autonomous": index == 1,
    }


def facet_lattice_report(name: str) -> Dict[str, object]:
    """``pi_F(Lambda)`` against ``Lambda ∩ span(F)``, with the exact index."""
    return dict(_facet_lattice(name))


def facets_report() -> Dict[str, object]:
    """The whole decomposition, recomputed."""
    lattices = {name: facet_lattice_report(name) for name in FACET_ORDER}
    return {
        "order": list(FACET_ORDER),
        "partition": partition_report(),
        "linearity": linearity_report(),
        "pythagoras": pythagoras_report(),
        "lattices": lattices,
        "index_by_facet": {name: lattices[name]["index"]
                           for name in FACET_ORDER},
        "autonomous_facets": [name for name in FACET_ORDER
                              if lattices[name]["lattice_autonomous"]],
        "descriptions": dict(FACET_DESCRIPTION),
    }
