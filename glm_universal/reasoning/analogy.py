"""``glm_universal.reasoning.analogy`` -- proportional analogy in ``Q^24``.

The problem
-----------
``A : B :: C : D``.  Read as a statement about the substrate it says: the
displacement that carries ``A`` to ``B`` also carries ``C`` to ``D``.  So the
*ideal* answer is the exact rational vector

.. math::   D^{*} = C + (B - A),

and the *reported* answer is whatever admissible object is nearest to ``D*``
under the Griess metric of :mod:`glm_universal.reasoning.metric`.  Two kinds
of admissible target are supported:

``project="candidates"``
    the nearest member of a supplied set of :class:`~glm_universal.
    data_objects.base.DataObject` carriers -- the domain-level solver;
``project="lattice"``
    the nearest point of the Leech lattice ``Lambda`` itself.

Exact nearest-lattice-point decoding
------------------------------------
:func:`nearest_lattice_point` is exact and **provably optimal**, not a
heuristic.  ``Lambda`` in the ``x sqrt(8)`` integer model is the disjoint
union, over a parity ``m`` in ``{0, 1}`` and a Golay codeword ``c``, of the
sets

    ``{x : x_i = m + 2 (mod 4) for i in supp(c), x_i = m (mod 4) otherwise,
       and sum(x) = 4m (mod 8)}``

-- these are exactly the congruences :func:`glm_universal.substrate.leech2.
in_leech` tests.  Inside one such coset each coordinate ranges over an
arithmetic progression of step 4, so the unconstrained nearest point is
coordinatewise rounding; the sum condition is a single ``mod 8`` constraint
that any admissible point either satisfies or misses, and moving one
coordinate by ``+-4`` flips it at minimum cost.  Enumerating the ``2 x 4096``
cosets therefore searches all of ``Lambda``, and the minimum over them is the
true nearest point.  The routine is separable, so the per-coset work is a sum
over the codeword's support rather than over all 24 coordinates.

Every step is :class:`~fractions.Fraction` or ``int``; nothing is rounded in
floating point, and the answer is checked with ``in_leech`` before it is
returned.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..data_objects import base as do_base
from ..data_objects import elements as do_elements
from ..data_objects import physics as do_physics
from ..data_objects import semantic_lexicon as do_semantic_lexicon
from ..data_objects.base import DataObject
from ..substrate import leech2, mog
from . import metric

__all__ = [
    "SUBSPACES", "AnalogyResult", "LatticeAnalogyResult",
    "analogy_target", "solve_analogy", "solve_analogy_objects",
    "nearest_golay_codeword", "nearest_lattice_point", "lattice_analogy",
    "physics_analogy", "element_analogy", "domain_analogy",
    "subspace_indices", "project_subspace",
]


# ===========================================================================
# 0.  SUBSPACES
# ===========================================================================

#: Named coordinate subsets that make an analogy answer a specific question.
#:
#: A raw 24-coordinate difference mixes semantic content with bookkeeping --
#: for physics it would let the nominal ``kind`` and ``domain`` labels outvote
#: the dimensional exponents.  A subspace restricts both the displacement and
#: the metric to the coordinates the question is actually about.  ``None``
#: means "all 24 coordinates".
SUBSPACES: Dict[str, Tuple[str, ...]] = {
    # physics: the ten EXT10 exponents and their redundant SI7 projection
    "physics.dimension": (
        tuple(f"ext10.{a}" for a in do_physics.AXES_EXT10)
        + tuple(f"si7.{a}" for a in do_physics.AXES_SI7)),
    # physics: dimension plus decimal scale, i.e. the full magnitude content
    "physics.magnitude": (
        tuple(f"ext10.{a}" for a in do_physics.AXES_EXT10)
        + tuple(f"si7.{a}" for a in do_physics.AXES_SI7) + ("scale",)),
    # chemistry: where an element sits in the table, and nothing else
    "chemistry.position": ("z", "period", "group_block_code"),
    # chemistry: the measured physical attributes
    "chemistry.measured": (
        "atomic_weight_u", "electronegativity_pauling", "atomic_radius_pm",
        "covalent_radius_pm", "valence_electrons", "ionization_energy_eV"),
    # lexicon (v0.5.1): the ten semantic primitives alone.  This subspace
    # lets analogies over words resolve on meaning rather than spelling.
    # `energy : force :: heat : ?` should resolve to `temperature` from
    # this subspace, because heat->temperature differs from energy->force
    # in the same primitive axes.
    "lexicon.primitives": tuple(do_semantic_lexicon.SEMANTIC_PRIMITIVE_NAMES),
    # lexicon (v0.5.1): the four predicate + four object slots.  This
    # subspace asks "what relations does this concept participate in?"
    # without regard to its meaning.
    "lexicon.relations": tuple(
        f"predicate{i}" for i in range(do_semantic_lexicon.MAX_SEMANTIC_RELATIONS)
    ) + tuple(
        f"object{i}" for i in range(do_semantic_lexicon.MAX_SEMANTIC_RELATIONS)
    ),
}


def subspace_indices(layout: Sequence[str], names: Sequence[str]) -> Tuple[int, ...]:
    """Positions of ``names`` within a carrier ``layout``."""
    idx = []
    for name in names:
        try:
            idx.append(tuple(layout).index(name))
        except ValueError:
            raise KeyError(
                f"subspace_indices: {name!r} is not a coordinate of this "
                f"layout") from None
    return tuple(idx)


def project_subspace(carrier: Sequence, indices: Optional[Sequence[int]]
                     ) -> Tuple[Fraction, ...]:
    """Zero out every coordinate outside ``indices``, keeping 24 slots.

    Zeroing rather than slicing keeps the result a point of ``Q^24``, so the
    same Griess form applies and the result can still be stacked, projected
    onto facets and compared against lattice points.
    """
    exact = metric.as_exact_vector(carrier)
    if indices is None:
        return exact
    keep = set(int(i) for i in indices)
    return tuple(v if i in keep else Fraction(0) for i, v in enumerate(exact))


def _resolve_subspace(subspace, layout: Sequence[str]) -> Optional[Tuple[int, ...]]:
    if subspace is None:
        return None
    if isinstance(subspace, str):
        try:
            names = SUBSPACES[subspace]
        except KeyError:
            raise KeyError(f"analogy: unknown subspace {subspace!r}; known "
                           f"names are {sorted(SUBSPACES)}") from None
        return subspace_indices(layout, names)
    return tuple(int(i) for i in subspace)


# ===========================================================================
# 1.  THE PROPORTIONAL TARGET
# ===========================================================================

def analogy_target(a: Sequence, b: Sequence, c: Sequence) -> Tuple[Fraction, ...]:
    """``D* = C + (B - A)``, exactly, in ``Q^24``."""
    va, vb, vc = (metric.as_exact_vector(x) for x in (a, b, c))
    return tuple(z + (y - x) for x, y, z in zip(va, vb, vc))


@dataclass(frozen=True)
class AnalogyResult:
    """The outcome of a proportional analogy against a candidate set."""

    target: Tuple[Fraction, ...]
    answer: str
    distance2: Fraction
    exact_hit: bool
    runner_up: Optional[str]
    runner_up_distance2: Optional[Fraction]
    margin2: Optional[Fraction]
    ranked: Tuple[Tuple[str, Fraction], ...]
    subspace: Optional[str]
    tied: Tuple[str, ...] = ()

    @property
    def unique(self) -> bool:
        """Whether exactly one candidate attains the minimum distance.

        A tie is a real property of the register, not a defect of the solver:
        several physical quantities can share a dimension vector exactly.
        Reporting ``answer`` without ``unique`` would overclaim.
        """
        return len(self.tied) == 1

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view; rationals as ``"n/d"`` strings."""
        def q(x):
            return None if x is None else f"{x.numerator}/{x.denominator}"
        return {
            "answer": self.answer,
            "distance2": q(self.distance2),
            "exact_hit": self.exact_hit,
            "unique": self.unique,
            "tied": list(self.tied),
            "runner_up": self.runner_up,
            "runner_up_distance2": q(self.runner_up_distance2),
            "margin2": q(self.margin2),
            "subspace": self.subspace,
            "top5": [[n, q(d)] for n, d in self.ranked[:5]],
        }


def solve_analogy(a: Sequence, b: Sequence, c: Sequence,
                  candidates: Sequence[Tuple[str, Sequence]],
                  exclude: Sequence[str] = (),
                  subspace_index: Optional[Sequence[int]] = None,
                  subspace_name: Optional[str] = None) -> AnalogyResult:
    """Solve ``A : B :: C : ?`` against a labelled candidate set.

    The displacement, the target and every distance are computed in the same
    (optionally restricted) coordinate subspace, so the reported ranking is a
    ranking under one consistent metric.
    """
    target_full = analogy_target(a, b, c)
    target = project_subspace(target_full, subspace_index)
    projected = [(name, project_subspace(vec, subspace_index))
                 for name, vec in candidates]
    ranked = metric.rank_by_distance(target, projected, exclude)
    if not ranked:
        raise ValueError("solve_analogy: no candidates left after exclusion")
    best, best_d = ranked[0]
    second = ranked[1] if len(ranked) > 1 else (None, None)
    margin = None if second[1] is None else second[1] - best_d
    tied = tuple(name for name, d in ranked if d == best_d)
    return AnalogyResult(
        target=target, answer=best, distance2=best_d, exact_hit=best_d == 0,
        runner_up=second[0], runner_up_distance2=second[1], margin2=margin,
        ranked=tuple(ranked), subspace=subspace_name, tied=tied)


def solve_analogy_objects(a: DataObject, b: DataObject, c: DataObject,
                          candidates: Sequence[DataObject],
                          subspace: Optional[object] = None,
                          exclude_inputs: bool = True) -> AnalogyResult:
    """Domain-level analogy over :class:`DataObject` carriers.

    Parameters
    ----------
    a, b, c
        The three given terms.  They must share a layout.
    candidates
        The pool the answer is drawn from.
    subspace
        A key of :data:`SUBSPACES`, an explicit sequence of coordinate
        indices, or ``None`` for the full 24 coordinates.
    exclude_inputs
        Drop ``A``, ``B`` and ``C`` from the pool, which is what makes the
        task nontrivial when the pool is the whole register.
    """
    layouts = {tuple(x.layout) for x in (a, b, c) if x.layout}
    if len(layouts) > 1:
        raise ValueError("solve_analogy_objects: the three terms have "
                         "different layouts")
    layout = tuple(a.layout) if a.layout else ()
    indices = _resolve_subspace(subspace, layout)
    name = subspace if isinstance(subspace, str) else None
    exclude = [x.name for x in (a, b, c)] if exclude_inputs else []
    pool = [(o.name, o.carrier) for o in candidates]
    return solve_analogy(a.carrier, b.carrier, c.carrier, pool,
                         exclude=exclude, subspace_index=indices,
                         subspace_name=name)


# ===========================================================================
# 2.  PROJECTION ONTO THE CODE AND THE LATTICE
# ===========================================================================

def nearest_golay_codeword(mask: int) -> Tuple[int, int, int]:
    """``(codeword, distance, count)`` for the nearest Golay codewords.

    Exhaustive over all 4096 codewords, so the distance is the true minimum;
    ``count`` says how many attain it, which is 1 exactly when the mask is
    within the code's unique-decoding radius of 3.
    """
    if not 0 <= int(mask) < (1 << 24):
        raise ValueError("nearest_golay_codeword: mask must be 24-bit")
    mask = int(mask)
    best, winners = 25, []
    for word in mog.GOLAY_MASKS:
        d = bin(mask ^ word).count("1")
        if d < best:
            best, winners = d, [word]
        elif d == best:
            winners.append(word)
    return min(winners), best, len(winners)


@dataclass(frozen=True)
class LatticeAnalogyResult:
    """The outcome of projecting an analogy target onto ``Lambda``."""

    target: Tuple[Fraction, ...]
    point: Tuple[int, ...]
    distance2: Fraction
    in_leech: bool
    leech_class: int
    norm2: int
    is_2a_axis: bool
    exact_hit: bool

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "point": list(self.point),
            "distance2": f"{self.distance2.numerator}/{self.distance2.denominator}",
            "in_leech": self.in_leech,
            "leech_class": self.leech_class,
            "norm2_integer_model": self.norm2,
            "is_2a_axis": self.is_2a_axis,
            "exact_hit": self.exact_hit,
        }


def _round_to_residue(value: Fraction, residue: int) -> Tuple[int, Fraction, Fraction]:
    """Nearest integer congruent to ``residue`` mod 4, its cost, and the
    extra cost of the second nearest such integer.

    Returns ``(x, cost, penalty)`` where ``cost = (value - x)^2`` and
    ``penalty`` is the increase in cost incurred by moving to ``x +- 4``,
    whichever direction is cheaper.  All exact.
    """
    # x = residue + 4k;  choose k nearest to (value - residue) / 4
    shifted = (value - residue) / 4
    floor_k = shifted.numerator // shifted.denominator
    best_x, best_cost = None, None
    for k in (floor_k, floor_k + 1):
        x = residue + 4 * k
        cost = (value - x) ** 2
        if best_cost is None or cost < best_cost or (cost == best_cost and x < best_x):
            best_x, best_cost = x, cost
    assert best_x is not None and best_cost is not None
    alt = min(((value - (best_x + 4)) ** 2, best_x + 4),
              ((value - (best_x - 4)) ** 2, best_x - 4))
    return best_x, best_cost, alt[0] - best_cost


def nearest_lattice_point(vector: Sequence) -> LatticeAnalogyResult:
    """The exact nearest point of ``Lambda`` to a rational 24-vector.

    Optimal, not heuristic: see the module docstring for why enumerating the
    ``2 x 4096`` congruence cosets of ``Lambda`` and taking the coordinatewise
    rounding inside each (plus at most one ``+-4`` repair of the ``sum mod 8``
    condition) searches the whole lattice.
    """
    v = metric.as_exact_vector(vector)

    best_point: Optional[List[int]] = None
    best_cost: Optional[Fraction] = None

    for m in (0, 1):
        r0, r1 = m % 4, (m + 2) % 4
        # per coordinate, for each of the two residue classes
        base: List[Tuple[int, Fraction, Fraction]] = []
        alt: List[Tuple[int, Fraction, Fraction]] = []
        for value in v:
            base.append(_round_to_residue(value, r0))
            alt.append(_round_to_residue(value, r1))
        base_cost = sum((b[1] for b in base), Fraction(0))
        delta = [alt[i][1] - base[i][1] for i in range(24)]

        for word in mog.GOLAY_MASKS:
            support = [i for i in range(24) if (word >> i) & 1]
            cost = base_cost
            for i in support:
                cost += delta[i]
            if best_cost is not None and cost > best_cost:
                # even a perfect sum condition cannot beat the incumbent
                continue
            point = [alt[i][0] if (word >> i) & 1 else base[i][0]
                     for i in range(24)]
            if sum(point) % 8 != (4 * m) % 8:
                # repair with the single cheapest +-4 move
                penalties = [(alt[i][2] if (word >> i) & 1 else base[i][2], i)
                             for i in range(24)]
                pen, idx = min(penalties)
                cost += pen
                # apply the move in the cheaper direction
                x = point[idx]
                up, down = (v[idx] - (x + 4)) ** 2, (v[idx] - (x - 4)) ** 2
                point[idx] = x + 4 if up <= down else x - 4
            if best_cost is None or cost < best_cost or (
                    cost == best_cost and best_point is not None
                    and point < best_point):
                best_cost, best_point = cost, point

    assert best_point is not None and best_cost is not None
    if not leech2.in_leech(best_point):
        raise AssertionError(
            "nearest_lattice_point: the decoded point fails in_leech -- the "
            "coset enumeration and the lattice definition have diverged")
    d2 = best_cost / metric.GRIESS_SCALE
    cls = leech2.class_of(best_point)
    n2 = leech2.norm2(best_point)
    return LatticeAnalogyResult(
        target=v, point=tuple(best_point), distance2=d2, in_leech=True,
        leech_class=cls, norm2=n2,
        is_2a_axis=leech2.is_type2_class(cls), exact_hit=d2 == 0)


def lattice_analogy(a: Sequence, b: Sequence, c: Sequence) -> LatticeAnalogyResult:
    """Solve ``A : B :: C : ?`` in ``Lambda`` by exact nearest-point decoding."""
    return nearest_lattice_point(analogy_target(a, b, c))


# ===========================================================================
# 3.  DOMAIN-LEVEL SOLVERS
# ===========================================================================

def _index(objects: Sequence[DataObject]) -> Dict[str, DataObject]:
    return {o.name: o for o in objects}


def physics_analogy(a: str, b: str, c: str,
                    subspace: object = "physics.dimension",
                    pool: Optional[Sequence[DataObject]] = None
                    ) -> AnalogyResult:
    """``A : B :: C : ?`` over the 660-concept physics register, by name."""
    objects = tuple(pool) if pool is not None else do_physics.physics_objects()
    idx = _index(objects)
    missing = [n for n in (a, b, c) if n not in idx]
    if missing:
        raise KeyError(f"physics_analogy: not in the register: {missing}")
    return solve_analogy_objects(idx[a], idx[b], idx[c], objects,
                                 subspace=subspace)


def element_analogy(a: str, b: str, c: str,
                    subspace: object = "chemistry.position",
                    pool: Optional[Sequence[DataObject]] = None
                    ) -> AnalogyResult:
    """``A : B :: C : ?`` over the 118 elements, by symbol."""
    objects = tuple(pool) if pool is not None else do_elements.element_objects()
    idx = _index(objects)
    missing = [n for n in (a, b, c) if n not in idx]
    if missing:
        raise KeyError(f"element_analogy: not among the element carriers: "
                       f"{missing} (names are {sorted(idx)[:5]}...)")
    return solve_analogy_objects(idx[a], idx[b], idx[c], objects,
                                 subspace=subspace)


def domain_analogy(domain: str, a: str, b: str, c: str,
                   subspace: object = None) -> AnalogyResult:
    """``A : B :: C : ?`` in any of the four data-object domains.

    ``domain`` is one of ``"physics"``, ``"chemistry"``, ``"mathematics"``,
    ``"lexicon"``.
    """
    from ..data_objects import all_objects
    pools = all_objects()
    if domain not in ("physics", "chemistry", "mathematics", "lexicon"):
        raise KeyError(f"domain_analogy: unknown domain {domain!r}")
    objects = pools[domain]
    idx = _index(objects)
    missing = [n for n in (a, b, c) if n not in idx]
    if missing:
        raise KeyError(f"domain_analogy: not in {domain}: {missing}")
    return solve_analogy_objects(idx[a], idx[b], idx[c], objects,
                                 subspace=subspace)
