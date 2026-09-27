"""``glm_universal.reasoning.information_loss`` -- loss at the layer boundaries.

What this module is
-------------------
:mod:`~glm_universal.reasoning.dimension_layers` says *that* the GLM is a stack
of perspectives, each true within its range and each handing off to the next.
This module measures *where* one range ends: it computes, for real carriers,
exactly what each layer cannot see, and exactly which laws stop holding when
the next layer takes over.

Everything here is derived from one relation.  Two carriers are
**indistinguishable at a layer** when that layer's own ``measure`` reports
distance ``0`` between their views -- the layer's own verdict that they are the
same thing.  From that relation:

``classes``
    the partition of a set of carriers into what a layer can tell apart;
``resolution`` / ``loss_count``
    how many distinct things a layer sees, and how many it loses;
``boundary``
    the pairs one layer conflates and a higher one splits -- the information
    lost at that boundary, listed rather than asserted;
``refinement_violations``
    the pairs a *lower* layer splits and a *higher* one conflates.  Layers
    ought to refine one another; where they do not, the escalation ladder has
    a hole, and this function finds it;
``congruence_witness``
    a law's reach: four carriers showing that a layer's resolution is not
    enough to compute an operation.  A layer can carry out an operation in its
    own view space exactly when no such witness exists;
``information_loss_report``
    all of the above, recomputed on demand -- never quoted.

The counterpart formal development, with the same definitions proved as
theorems, is in ``RequestProject/GLM/Layers.lean`` and
``RequestProject/GLM/Stack.lean`` of this repository.

Everything is exact.  No float is constructed anywhere in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from . import dimension_layers as DL

__all__ = [
    "Carrier", "Witness",
    "view", "clear_view_cache",
    "indistinguishable", "classes", "resolution", "loss_count",
    "boundary", "refinement_violations", "refines", "congruence_witness",
    "is_congruent", "capacity", "sample_carriers", "carrier_sum",
    "axis_sharing_carriers", "non_cumulative_report",
    "information_loss_report",
]

#: A carrier is 24 exact rational coordinates.
Carrier = Sequence[Fraction]


@dataclass(frozen=True)
class Witness:
    """Four carriers showing that an operation escapes a layer's resolution.

    ``a`` and ``a2`` are indistinguishable at the layer, and so are ``b`` and
    ``b2``, yet ``op(a, b)`` and ``op(a2, b2)`` are not.  The layer therefore
    cannot compute ``op`` from what it sees: the operation does not descend.
    """

    layer: str
    a: Tuple[Fraction, ...]
    a2: Tuple[Fraction, ...]
    b: Tuple[Fraction, ...]
    b2: Tuple[Fraction, ...]

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "layer": self.layer,
            "a": [str(x) for x in self.a],
            "a2": [str(x) for x in self.a2],
            "b": [str(x) for x in self.b],
            "b2": [str(x) for x in self.b2],
        }


# ===========================================================================
# 1.  THE ONE RELATION
# ===========================================================================

#: Perceived views, keyed by layer name and exact carrier.  A layer's
#: ``perceive`` can be costly -- the rational layer runs a Leech nearest-point
#: decode -- and the searches below revisit the same few carriers thousands of
#: times.  The cache is sound because ``perceive`` is a pure function of the
#: carrier and no carrier here is ever mutated.
_VIEWS: Dict[Tuple[str, Tuple[Fraction, ...]], object] = {}


def _exact(carrier: Carrier) -> Tuple[Fraction, ...]:
    """The carrier as a hashable tuple of exact rationals."""
    return tuple(Fraction(x) for x in carrier)


def view(layer: DL.DimensionLayer, carrier: Carrier) -> object:
    """What the layer sees of the carrier, computed once and remembered."""
    key = (layer.name, _exact(carrier))
    if key not in _VIEWS:
        _VIEWS[key] = layer.perceive(carrier)
    return _VIEWS[key]


def clear_view_cache() -> None:
    """Forget every remembered view.  Only ever a memory concern."""
    _VIEWS.clear()


def indistinguishable(layer: DL.DimensionLayer, a: Carrier, b: Carrier) -> bool:
    """Whether a layer's own measure reports the two carriers as the same."""
    if _exact(a) == _exact(b):
        return True
    return layer.measure(view(layer, a), view(layer, b)) == 0


# ===========================================================================
# 2.  RESOLUTION AND LOSS
# ===========================================================================

def classes(layer: DL.DimensionLayer,
            carriers: Sequence[Carrier]) -> Tuple[Tuple[int, ...], ...]:
    """Partition the carriers into the classes the layer can tell apart.

    Returned as tuples of indices into ``carriers``, in first-appearance
    order, so the result is deterministic.
    """
    buckets: List[List[int]] = []
    for i, carrier in enumerate(carriers):
        placed = False
        for bucket in buckets:
            if indistinguishable(layer, carriers[bucket[0]], carrier):
                bucket.append(i)
                placed = True
                break
        if not placed:
            buckets.append([i])
    return tuple(tuple(b) for b in buckets)


def resolution(layer: DL.DimensionLayer,
               carriers: Sequence[Carrier]) -> int:
    """How many distinct things the layer resolves among these carriers."""
    return len(classes(layer, carriers))


def loss_count(layer: DL.DimensionLayer,
               carriers: Sequence[Carrier]) -> int:
    """How many carriers the layer loses: the count minus what it resolves."""
    return len(carriers) - resolution(layer, carriers)


# ===========================================================================
# 3.  BOUNDARIES
# ===========================================================================

def boundary(lower: DL.DimensionLayer, higher: DL.DimensionLayer,
             carriers: Sequence[Carrier]) -> Tuple[Tuple[int, int], ...]:
    """The pairs the lower layer conflates and the higher layer splits.

    This set *is* the information lost at the boundary between the two layers.
    """
    out: List[Tuple[int, int]] = []
    for i in range(len(carriers)):
        for j in range(i + 1, len(carriers)):
            if (indistinguishable(lower, carriers[i], carriers[j])
                    and not indistinguishable(higher, carriers[i],
                                              carriers[j])):
                out.append((i, j))
    return tuple(out)


def refinement_violations(lower: DL.DimensionLayer,
                          higher: DL.DimensionLayer,
                          carriers: Sequence[Carrier]
                          ) -> Tuple[Tuple[int, int], ...]:
    """The pairs the *lower* layer splits and the *higher* layer conflates.

    A stack is a genuine refinement chain only when this is empty: a higher
    perspective is supposed to see at least as much as the one it supersedes.
    Where it is not empty, escalating loses information that the layer below
    already had.
    """
    out: List[Tuple[int, int]] = []
    for i in range(len(carriers)):
        for j in range(i + 1, len(carriers)):
            if (indistinguishable(higher, carriers[i], carriers[j])
                    and not indistinguishable(lower, carriers[i],
                                              carriers[j])):
                out.append((i, j))
    return tuple(out)


def refines(higher: DL.DimensionLayer, lower: DL.DimensionLayer,
            carriers: Sequence[Carrier]) -> bool:
    """Whether the higher layer sees at least as much as the lower one here.

    True exactly when :func:`refinement_violations` is empty.
    """
    return not refinement_violations(lower, higher, carriers)


# ===========================================================================
# 4.  THE REACH OF A LAW
# ===========================================================================

def carrier_sum(a: Carrier, b: Carrier) -> Tuple[Fraction, ...]:
    """Coordinatewise sum: composing two concepts adds their exponents."""
    return tuple(Fraction(x) + Fraction(y) for x, y in zip(a, b))


def congruence_witness(layer: DL.DimensionLayer,
                       carriers: Sequence[Carrier],
                       op: Callable[[Carrier, Carrier],
                                    Sequence[Fraction]] = carrier_sum
                       ) -> Optional[Witness]:
    """A witness that ``op`` escapes the layer's resolution, if one exists here.

    Searches the given carriers for ``a ~ a2`` and ``b ~ b2`` with
    ``op(a, b) !~ op(a2, b2)``.  ``None`` means the operation descends to this
    layer on this set of carriers -- the law holds within that reach.
    """
    n = len(carriers)
    for i in range(n):
        for k in range(n):
            if not indistinguishable(layer, carriers[i], carriers[k]):
                continue
            for j in range(n):
                for m in range(n):
                    if not indistinguishable(layer, carriers[j], carriers[m]):
                        continue
                    left = op(carriers[i], carriers[j])
                    right = op(carriers[k], carriers[m])
                    if not indistinguishable(layer, left, right):
                        return Witness(
                            layer=layer.name,
                            a=tuple(Fraction(x) for x in carriers[i]),
                            a2=tuple(Fraction(x) for x in carriers[k]),
                            b=tuple(Fraction(x) for x in carriers[j]),
                            b2=tuple(Fraction(x) for x in carriers[m]))
    return None


def is_congruent(layer: DL.DimensionLayer, carriers: Sequence[Carrier],
                 op: Callable[[Carrier, Carrier],
                              Sequence[Fraction]] = carrier_sum) -> bool:
    """Whether the operation descends to the layer on these carriers."""
    return congruence_witness(layer, carriers, op) is None


# ===========================================================================
# 5.  CAPACITY
# ===========================================================================

def capacity(layer: DL.DimensionLayer) -> Optional[int]:
    """How many distinct views the layer can hold, or ``None`` if unbounded.

    Only the substrate is finite: its view of a carrier is 24 bits.  Every
    layer above it holds exponents or exact rationals, so its view space is
    infinite and no pigeonhole bound applies.
    """
    if layer.name == "substrate":
        return 2 ** 24
    return None


# ===========================================================================
# 6.  A DETERMINISTIC CARRIER SET
# ===========================================================================

def _unit(index: int, value: Fraction) -> Tuple[Fraction, ...]:
    """The carrier that is ``value`` at one coordinate and zero elsewhere."""
    out = [Fraction(0)] * 24
    out[index] = value
    return tuple(out)


def sample_carriers() -> Tuple[Tuple[Fraction, ...], ...]:
    """A small, fixed carrier set that exercises every boundary.

    * the vacuum;
    * a half-unit and a unit on coordinate 0 -- an integer-layer boundary,
      since truncation cannot see the half;
    * a two-unit on coordinate 0 -- a substrate boundary, since parity cannot
      see an even amplitude;
    * a unit on coordinate 10 -- outside the seven exponents the SI7 reading
      takes, so it is the pair that broke the substrate -> integer step
      before the integer view was made cumulative, and the pair that
      :data:`~glm_universal.reasoning.dimension_layers.LAYER_INTEGER_RAW`
      still gets wrong;
    * two carriers that repair to a *single* 2A axis -- the pair that broke
      the rational -> Griess step before the Griess measure kept the carrier
      term.  See :func:`axis_sharing_carriers`.
    """
    return (
        tuple([Fraction(0)] * 24),
        _unit(0, Fraction(1, 2)),
        _unit(0, Fraction(1)),
        _unit(0, Fraction(2)),
        _unit(10, Fraction(1)),
    ) + axis_sharing_carriers()


def axis_sharing_carriers() -> Tuple[Tuple[Fraction, ...], ...]:
    """Two distinct carriers whose nearest lattice point is the same 2A axis.

    The Griess layer's algebra cannot tell them apart -- they *are* one axis
    to it -- while the rational layer below splits them, since their exact
    coordinates differ.  A Griess measure made of the algebra alone would
    therefore conflate a pair the layer below it separates, so this pair is
    what forces the Griess measure to carry the carrier term as well.
    """
    from ..substrate import leech2
    base = next(iter(leech2.minimal_vectors()))
    a = tuple(Fraction(x) for x in base)
    b = tuple(x + Fraction(1, 7) if i == 0 else x for i, x in enumerate(a))
    return (a, b)


# ===========================================================================
# 7.  THE REPORT
# ===========================================================================

def non_cumulative_report(carriers: Optional[Sequence[Carrier]] = None
                          ) -> Dict[str, object]:
    """What the *non-cumulative* integer reading costs, measured.

    :data:`~glm_universal.reasoning.dimension_layers.LAYER_INTEGER_RAW` reads
    the seven SI7 exponents and discards the substrate's view instead of
    adding to it.  This function shows what that costs: the pairs it
    conflates which the substrate below it splits, and the fact that the
    layer actually in the stack has none.
    """
    if carriers is None:
        carriers = sample_carriers()
    raw = DL.LAYER_INTEGER_RAW
    holes = refinement_violations(DL.LAYER_SUBSTRATE, raw, carriers)
    fixed = refinement_violations(DL.LAYER_SUBSTRATE, DL.LAYER_INTEGER,
                                  carriers)
    return {
        "layer": raw.name,
        "resolution": resolution(raw, carriers),
        "loss_count": loss_count(raw, carriers),
        "refines_substrate": not holes,
        "violating_pairs": [list(p) for p in holes],
        "violation_count": len(holes),
        "cumulative_layer": DL.LAYER_INTEGER.name,
        "cumulative_refines_substrate": not fixed,
        "cumulative_resolution": resolution(DL.LAYER_INTEGER, carriers),
    }


def information_loss_report(carriers: Optional[Sequence[Carrier]] = None
                            ) -> Dict[str, object]:
    """Recompute the whole study on demand.  Every number here is computed.

    The report covers all five layers of the stack and each of the four
    boundaries between consecutive layers, and it checks the property the
    stack has to have to be a stack at all: that every layer sees at least as
    much as the one below it (``refinement_chain_intact``).  Beside it,
    ``non_cumulative`` records what the reading the stack does *not* use
    would have cost.
    """
    if carriers is None:
        carriers = sample_carriers()
    layers = DL.LAYERS

    layer_reports = []
    for layer in layers:
        witness = congruence_witness(layer, carriers)
        layer_reports.append({
            "name": layer.name,
            "dimension": layer.dimension,
            "capacity": capacity(layer),
            "can_multiply": layer.can_multiply,
            "resolution": resolution(layer, carriers),
            "loss_count": loss_count(layer, carriers),
            "classes": [list(c) for c in classes(layer, carriers)],
            "addition_descends": witness is None,
            "congruence_witness": witness.as_dict() if witness else None,
        })

    boundaries = []
    for lower, higher in zip(layers, layers[1:]):
        lost = boundary(lower, higher, carriers)
        holes = refinement_violations(lower, higher, carriers)
        boundaries.append({
            "lower": lower.name,
            "higher": higher.name,
            "lost_pairs": [list(p) for p in lost],
            "lost_count": len(lost),
            "refinement_violations": [list(p) for p in holes],
            "refines": not holes,
        })

    return {
        "carriers": [[str(x) for x in c] for c in carriers],
        "carrier_count": len(carriers),
        "layers": layer_reports,
        "boundaries": boundaries,
        "refinement_chain_intact": all(b["refines"] for b in boundaries),
        "non_cumulative": non_cumulative_report(carriers),
    }
