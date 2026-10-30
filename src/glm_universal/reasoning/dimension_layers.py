"""``glm_universal.reasoning.dimension_layers`` -- the Dimension Projection.

What this module is
-------------------
The GLM is not a single system; it is a **stack of perspectives**, each one
true within its range and each one handing off to the next when its range is
exhausted.  This module makes those perspectives explicit and callable.

The directive says:

    There are 'Dimensional Projection' perspectives to the GLM -- one is from
    the most recent system showing where previous systems failed and the fix
    for the situation, this is the highest dimension perspective, the other is
    from each iteration which seems to show an alignment up to a point but
    then is superseded by the next higher dimension perspective -- a layered
    projection perspective where each layer is both true from its limited
    perspective and works to that degree of implementation then becomes untrue
    when the next dimension layer is required to take over.

Each layer is a :class:`DimensionLayer` with:

* a **name** and **dimension** (the number of degrees of freedom it models);
* a **perceive** function that maps raw carrier data into that layer's
  coordinate space;
* a **measure** function that computes distances or similarities at that
  layer's resolution;
* a **reach** description stating what it can and cannot do;
* a **failure_mode** describing what happens when its range is exhausted.

The layers are ordered from lowest to highest.  A caller that starts at the
bottom can escalate to the next layer when the current one reports that its
reach is exhausted.

The stack is a refinement chain
-------------------------------
Escalating must never cost anything: whatever a layer can tell apart, every
layer above it can tell apart too.  That is not automatic, and it was not
true of the first version of this module.  The seven SI7 exponents are read
off coordinates 0-6, so an integer layer that saw *only* them was blind to a
unit on coordinate 10 that the substrate's 24-bit parity view separates from
the vacuum -- escalating from the substrate to the integer layer destroyed a
distinction.

The layers here are therefore **cumulative**: each view holds what the layer
below saw, and each measure is zero only when every reading in the view
agrees.  Concretely, the integer view carries ``substrate_bits`` beside
``exponents_SI7`` and its measure adds the Hamming term; the Griess and
universal measures add the carrier term to the semantic one, so that two
distinct carriers repairing to a single 2A axis are no longer called the
same thing by a layer that sits above one which splits them.  The pure
semantic verdict is still available on its own, as
:func:`griess_semantic_component`.

The discarded reading is kept as :data:`LAYER_INTEGER_RAW` -- outside
:data:`LAYERS` -- so that the hole it has can be exhibited and regression
tested rather than merely described.
:func:`glm_universal.reasoning.information_loss.information_loss_report`
checks every consecutive pair of the five layers and reports
``refinement_chain_intact``.

Layers
------
0. **Substrate** (GMHGL): binary carrier, Hamming distance, NRCI.
   Reach: discrete encoding, error correction, weight enumeration.
   Failure: no product, no semantic composition.  Two carriers can be
   compared but not *multiplied*.

1. **Integer** (GLM-1): 7 integer dimension exponents on top of the
   substrate's parity view, Golay/MOG carrier.
   Reach: concept encoding with integer-valued physical dimensions.
   Failure: integer-only -- cannot represent fractional dimensions or
   continuous quantities.

2. **Rational** (GLM-2): 10 rational exponents + scale, Leech carrier, Co₀.
   Reach: continuous dimensions, tensor rank, operator algebra (grad, div,
   curl).  Carrier repair by nearest-point decoding.
   Failure: strictly linear -- the carrier group acts but cannot multiply
   concepts.  No composition, no analogy beyond displacement.

3. **Griess** (GLM-3): 196,884-dimensional V₂, Monster group, Λ/2Λ.
   Reach: the non-associative product, the Griess form, 2A axes, Norton-
   Sakuma subalgebras, Miyamoto involutions.  Concepts can be composed.
   Failure: finite-dimensional -- the Griess algebra is V₂ of the infinite-
   dimensional Moonshine module V^♮.  The graded dimensions produce the
   j-function but the system does not yet *use* that bridge.

4. **Universal** (GLM-3+): all layers accessible, with the trilinear form
   ⟨u·v, w⟩ and semantic similarity.  The dimension projection is explicit:
   the system can invoke any lower layer when the situation calls for it.

Everything is exact.  No float is constructed anywhere in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..substrate import golay_decode, mog, leech2
from . import metric, product

__all__ = [
    "DimensionLayer", "LAYER_SUBSTRATE", "LAYER_INTEGER", "LAYER_RATIONAL",
    "LAYER_GRIESS", "LAYER_UNIVERSAL", "LAYERS", "LAYER_INTEGER_RAW",
    "escalate", "projection_report", "parity_bits",
    "griess_semantic_component",
]


# ===========================================================================
# 1.  THE LAYER DATACLASS
# ===========================================================================

@dataclass(frozen=True)
class DimensionLayer:
    """One perspective in the dimension projection.

    Attributes
    ----------
    name
        Short identifier: ``"substrate"``, ``"integer"``, etc.
    dimension
        The number of degrees of freedom this layer models.
    description
        What this layer sees.
    reach
        What it can do -- a list of capability strings.
    failure_mode
        What happens when its range is exhausted.
    perceive
        ``perceive(carrier) -> view``: maps a 24-coordinate carrier into
        this layer's coordinate space.  The view is a plain dict so that
        each layer can return whatever structure is natural to it.
    measure
        ``measure(view_a, view_b) -> Fraction``: a distance or dissimilarity
        at this layer's resolution.  Returns a :class:`~fractions.Fraction`
        that is 0 iff the two views are identical at this resolution.
    can_multiply
        Whether this layer supports concept composition (product of two
        concepts yielding a third).
    """

    name: str
    dimension: int
    description: str
    reach: Tuple[str, ...]
    failure_mode: str
    perceive: Callable[[Sequence], Dict[str, object]]
    measure: Callable[[Dict[str, object], Dict[str, object]], Fraction]
    can_multiply: bool


# ===========================================================================
# 2.  LAYER 0: SUBSTRATE  (GMHGL)
# ===========================================================================

def parity_bits(carrier: Sequence) -> int:
    """The 24-bit parity reading of a carrier: bit ``i`` is ``carrier[i]`` odd.

    This is the whole of what the substrate sees of a carrier's coordinates,
    and every layer above the substrate carries it too -- see
    :func:`_integer_perceive`.  Factored out so that there is exactly one
    definition of it in the package.
    """
    bits = 0
    for i, v in enumerate(carrier):
        if int(v) & 1:
            bits |= (1 << i)
    return bits


def _substrate_perceive(carrier: Sequence) -> Dict[str, object]:
    """Binary carrier: Hamming weight, NRCI, complete Golay decoding.

    The legacy version of this function *snapped*: it scanned the 4,096
    codewords and kept the first one at least distance.  At coset weight 4
    there are six such codewords and the scan silently returned whichever the
    enumeration reached first, so the view was a function of codeword order.
    It now calls
    :func:`glm_universal.substrate.golay_decode.decode_complete`, which
    returns the exact coset weight, every minimum-weight leader, and a status
    that says out loud when no unique answer exists.  ``nearest_codeword`` is
    ``None`` in that case; ``nearest_codewords`` always holds the full tie.
    """
    bits = parity_bits(carrier)
    hw = bin(bits).count("1")
    decoding = golay_decode.decode_complete(bits)
    # Covering radius 4: NRCI falls linearly from 1 at a codeword to 0 at the
    # deep holes of the code.
    nrci = Fraction(1) - Fraction(decoding.weight, 4)
    return {
        "layer": "substrate",
        "bits": bits,
        "hamming_weight": hw,
        "nearest_codeword": decoding.corrected,
        "nearest_codewords": decoding.candidates,
        "codeword_multiplicity": len(decoding.candidates),
        "snap_distance": decoding.weight,
        "decode_status": decoding.status,
        "decode_guaranteed": decoding.guaranteed,
        "nrci": max(Fraction(0), nrci),
    }


def _substrate_measure(a: Dict[str, object], b: Dict[str, object]) -> Fraction:
    """Hamming distance between the two carriers."""
    return Fraction(bin(a["bits"] ^ b["bits"]).count("1"))


# ===========================================================================
# 3.  LAYER 1: INTEGER  (GLM-1)
# ===========================================================================

def _integer_perceive(carrier: Sequence) -> Dict[str, object]:
    """7 integer dimension exponents, on top of the substrate's parity view.

    The integer layer is **cumulative**: escalating to it adds the seven SI7
    exponents to what the substrate already saw, it does not trade one
    reading for the other.  The view therefore carries ``substrate_bits`` as
    well as ``exponents_SI7``.

    This is not decoration.  The seven exponents are read off coordinates
    0-6, so a reading made of them alone is blind to coordinates 7-23: it
    cannot tell a unit on coordinate 10 from the vacuum, while the substrate
    below it can.  A stack whose first step reads only the exponents is not a
    refinement chain -- escalating from the substrate to it *destroys* a
    distinction -- and :func:`glm_universal.reasoning.information_loss.
    information_loss_report` exhibits exactly that pair for
    :data:`LAYER_INTEGER_RAW`, the non-cumulative reading kept beside this
    one so the hole can be shown rather than described.
    """
    exact = metric.as_exact_vector(carrier)
    # The first 7 coordinates are the integer dimension exponents
    # (L, M, T, A, Th, N, J in SI7)
    exponents = tuple(int(exact[i]) for i in range(7))
    bits = parity_bits(carrier)
    return {
        "layer": "integer",
        "exponents_SI7": exponents,
        "substrate_bits": bits,
        "hamming_weight": bin(bits).count("1"),
        "carrier": exact,
    }


def _integer_measure(a: Dict[str, object], b: Dict[str, object]) -> Fraction:
    """L1 distance on the exponents plus Hamming distance on the parity bits.

    Zero exactly when the two carriers agree on *both* readings the layer
    holds, which is what makes this layer a refinement of the substrate: a
    pair it calls the same is a pair the substrate calls the same.
    """
    ea, eb = a["exponents_SI7"], b["exponents_SI7"]
    exponent_part = Fraction(sum(abs(x - y) for x, y in zip(ea, eb)))
    hamming_part = Fraction(
        bin(a["substrate_bits"] ^ b["substrate_bits"]).count("1"))
    return exponent_part + hamming_part


def _integer_raw_perceive(carrier: Sequence) -> Dict[str, object]:
    """The seven SI7 exponents and nothing else -- the non-cumulative reading.

    Kept, and reported on, because it is the reading a layer stack reaches
    for by default, and it is the one that breaks the chain.  It is not part
    of :data:`LAYERS`.
    """
    exact = metric.as_exact_vector(carrier)
    return {
        "layer": "integer_raw",
        "exponents_SI7": tuple(int(exact[i]) for i in range(7)),
        "carrier": exact,
    }


def _integer_raw_measure(a: Dict[str, object],
                         b: Dict[str, object]) -> Fraction:
    """L1 distance on the 7 integer exponents alone."""
    ea, eb = a["exponents_SI7"], b["exponents_SI7"]
    return Fraction(sum(abs(x - y) for x, y in zip(ea, eb)))


# ===========================================================================
# 4.  LAYER 2: RATIONAL  (GLM-2)
# ===========================================================================

def _rational_perceive(carrier: Sequence) -> Dict[str, object]:
    """10 rational exponents + scale, with Leech lattice projection."""
    exact = metric.as_exact_vector(carrier)
    # project onto the Leech lattice
    lattice_result = _nearest_lattice(exact)
    return {
        "layer": "rational",
        "carrier": exact,
        "lattice_point": lattice_result["point"],
        "lattice_distance2": lattice_result["distance2"],
        "leech_class": lattice_result["leech_class"],
        "is_2a_axis": lattice_result["is_2a_axis"],
    }


def _rational_measure(a: Dict[str, object], b: Dict[str, object]) -> Fraction:
    """Squared Griess distance between the carriers."""
    return metric.distance2(a["carrier"], b["carrier"])


def _nearest_lattice(v: Sequence) -> Dict[str, object]:
    """Minimal nearest-lattice-point for internal use."""
    from . import analogy
    result = analogy.nearest_lattice_point(v)
    return {
        "point": result.point,
        "distance2": result.distance2,
        "leech_class": result.leech_class,
        "is_2a_axis": result.is_2a_axis,
    }


# ===========================================================================
# 5.  LAYER 3: GRIESS  (GLM-3)
# ===========================================================================

def _griess_perceive(carrier: Sequence) -> Dict[str, object]:
    """Full Griess algebra view: 2A axes, product structure, trilinear form."""
    exact = metric.as_exact_vector(carrier)
    lattice_result = _nearest_lattice(exact)
    cls = lattice_result["leech_class"]
    is_axis = lattice_result["is_2a_axis"]

    # If it's a 2A axis, build the algebra element
    algebra_element = None
    if is_axis:
        algebra_element = product.axis(cls)

    return {
        "layer": "griess",
        "carrier": exact,
        "lattice_point": lattice_result["point"],
        "leech_class": cls,
        "is_2a_axis": is_axis,
        "algebra_element": algebra_element,
    }


def griess_semantic_component(a: Dict[str, object],
                              b: Dict[str, object]) -> Fraction:
    """The algebraic part of the Griess-layer measure, on its own.

    Zero means the two carriers repair to the *same* 2A axis: they are the
    same concept as far as the algebra is concerned.  That is a genuine and
    useful verdict, and it is why it is available separately -- but it is not
    a resolution, because two different carriers can share an axis.  The
    layer's own :func:`_griess_measure` adds the carrier term so that the
    layer keeps everything the rational layer below it had.
    """
    ea, eb = a.get("algebra_element"), b.get("algebra_element")
    if ea is not None and eb is not None:
        return product.semantic_distance2(ea, eb)
    return Fraction(0)


def _griess_measure(a: Dict[str, object], b: Dict[str, object]) -> Fraction:
    """Semantic distance between the 2A axes *plus* the carrier distance.

    The Griess view holds the carrier as well as the algebra element, so two
    views are the same only when both agree.  Measuring the algebra alone
    would conflate two distinct carriers that repair to one axis -- a pair
    the rational layer below splits -- and escalating would then lose a
    distinction instead of adding one.  Both terms are non-negative, so the
    sum is zero exactly when each is.
    """
    return (griess_semantic_component(a, b)
            + metric.distance2(a["carrier"], b["carrier"]))


# ===========================================================================
# 6.  LAYER 4: UNIVERSAL  (GLM-3+)
# ===========================================================================

def _universal_perceive(carrier: Sequence) -> Dict[str, object]:
    """All layers at once -- the full projection."""
    exact = metric.as_exact_vector(carrier)
    substrate = _substrate_perceive(carrier)
    integer = _integer_perceive(carrier)
    lattice_result = _nearest_lattice(exact)
    cls = lattice_result["leech_class"]
    is_axis = lattice_result["is_2a_axis"]
    algebra_element = product.axis(cls) if is_axis else None

    return {
        "layer": "universal",
        "carrier": exact,
        "substrate": substrate,
        "integer": integer,
        "lattice_point": lattice_result["point"],
        "leech_class": cls,
        "is_2a_axis": is_axis,
        "algebra_element": algebra_element,
        "all_layers": True,
    }


def _universal_measure(a: Dict[str, object], b: Dict[str, object]) -> Fraction:
    """The highest-resolution measure available: algebra plus carrier.

    The universal view holds every lower view at once, so -- as at the Griess
    layer -- its measure is zero only when all of them agree.
    """
    return (griess_semantic_component(a, b)
            + metric.distance2(a["carrier"], b["carrier"]))


# ===========================================================================
# 7.  THE FIVE LAYERS
# ===========================================================================

LAYER_SUBSTRATE = DimensionLayer(
    name="substrate",
    dimension=24,
    description=(
        "Binary carrier, Hamming distance, NRCI.  The Golay code sees "
        "24 bits and measures how far they are from a codeword."
    ),
    reach=(
        "Discrete encoding and error correction",
        "Hamming weight and distance",
        "NRCI (coherence) measurement",
        "Complete Golay decoding, with ties reported and never broken",
    ),
    failure_mode=(
        "No product: two carriers can be compared but not multiplied.  "
        "No semantic composition is possible at this layer."
    ),
    perceive=_substrate_perceive,
    measure=_substrate_measure,
    can_multiply=False,
)

LAYER_INTEGER = DimensionLayer(
    name="integer",
    dimension=7,
    description=(
        "Seven integer dimension exponents (SI7), carried on top of the "
        "substrate's 24-bit parity view.  Concepts are their physical "
        "dimensions; carriers are quantised projections."
    ),
    reach=(
        "Integer-valued dimensional analysis",
        "Buckingham Pi with integer exponents",
        "Concept identity by dimension vector",
        "Everything the substrate can tell apart: the view is cumulative",
    ),
    failure_mode=(
        "Integer-only: cannot represent fractional dimensions.  "
        "A concept like sqrt(energy/mass) has no integer encoding."
    ),
    perceive=_integer_perceive,
    measure=_integer_measure,
    can_multiply=False,
)

LAYER_RATIONAL = DimensionLayer(
    name="rational",
    dimension=10,
    description=(
        "Ten rational exponents + scale, Leech carrier, Co₀ symmetry.  "
        "Continuous dimensions with nearest-point repair."
    ),
    reach=(
        "Rational dimensional analysis (10 axes + scale)",
        "Tensor rank and parities",
        "Operator algebra (grad, div, curl, d/dt, integrals)",
        "Leech lattice nearest-point decoding",
        "Co₀ group actions on the carrier",
    ),
    failure_mode=(
        "Strictly linear: the carrier group acts but cannot multiply "
        "concepts.  No composition, no analogy beyond displacement."
    ),
    perceive=_rational_perceive,
    measure=_rational_measure,
    can_multiply=False,
)

LAYER_GRIESS = DimensionLayer(
    name="griess",
    dimension=196884,
    description=(
        "The full Griess algebra V₂.  196,884 dimensions.  The Monster "
        "group acts.  Concepts have 2A axes and can be composed via the "
        "non-associative Griess product."
    ),
    reach=(
        "Non-associative Griess product on 2A axes",
        "Norton-Sakuma subalgebras (2A, 2B positions)",
        "Miyamoto involutions (tau, sigma)",
        "Griess bilinear form and trilinear form ⟨u·v, w⟩",
        "Semantic distance and similarity",
        "Class translation on Λ/2Λ",
    ),
    failure_mode=(
        "Finite-dimensional: V₂ is the weight-2 subspace of the infinite-"
        "dimensional Moonshine module V^♮.  The graded dimensions produce "
        "the j-function but the system does not yet use that bridge."
    ),
    perceive=_griess_perceive,
    measure=_griess_measure,
    can_multiply=True,
)

LAYER_UNIVERSAL = DimensionLayer(
    name="universal",
    dimension=-1,  # unbounded
    description=(
        "All layers accessible, with the trilinear form ⟨u·v, w⟩ and "
        "explicit dimension projection.  The system can invoke any lower "
        "layer when the situation calls for it."
    ),
    reach=(
        "Everything the lower layers can do",
        "Explicit dimension projection: invoke any layer on demand",
        "Trilinear form ⟨u·v, w⟩ for coherence measurement",
        "Semantic similarity via the Griess form",
        "Cross-layer comparison: how does a substrate-level NRCI "
        "relate to a Griess-level semantic distance?",
    ),
    failure_mode=(
        "The Moonshine bridge (V^♮) is not yet built.  The infinite-"
        "dimensional modular forms are the next step."
    ),
    perceive=_universal_perceive,
    measure=_universal_measure,
    can_multiply=True,
)

#: The seven SI7 exponents on their own -- the *non-cumulative* integer
#: reading.  It is deliberately **not** in :data:`LAYERS`.  Coordinates 7-23
#: are invisible to it, so it conflates carriers the substrate below it
#: separates, and a stack built on it is not a refinement chain.  It is kept
#: as a first-class object so that the hole can be exhibited and tested --
#: see ``information_loss.information_loss_report()["non_cumulative"]``.
LAYER_INTEGER_RAW = DimensionLayer(
    name="integer_raw",
    dimension=7,
    description=(
        "Seven integer dimension exponents and nothing else: the reading "
        "that discards the substrate's view instead of adding to it."
    ),
    reach=(
        "Integer-valued dimensional analysis on coordinates 0-6",
    ),
    failure_mode=(
        "Blind to coordinates 7-23, so it conflates carriers the substrate "
        "already separates: escalating to it loses information rather than "
        "gaining it.  Superseded by LAYER_INTEGER, which keeps both readings."
    ),
    perceive=_integer_raw_perceive,
    measure=_integer_raw_measure,
    can_multiply=False,
)

#: All five layers in order, lowest to highest.
LAYERS: Tuple[DimensionLayer, ...] = (
    LAYER_SUBSTRATE,
    LAYER_INTEGER,
    LAYER_RATIONAL,
    LAYER_GRIESS,
    LAYER_UNIVERSAL,
)

#: Quick lookup by name.
LAYER_BY_NAME: Dict[str, DimensionLayer] = {l.name: l for l in LAYERS}


# ===========================================================================
# 8.  ESCALATION
# ===========================================================================

def escalate(carrier_a: Sequence, carrier_b: Sequence,
             start: int = 0) -> Dict[str, object]:
    """Walk up the dimension layers until one can handle the pair.

    At each layer, perceives both carriers and measures their distance.
    If the layer's ``can_multiply`` is ``False`` and the caller needs
    composition, escalation continues to the next layer.

    Returns a dict with:
    * ``layer``: the :class:`DimensionLayer` that was reached;
    * ``view_a``, ``view_b``: the perceives at that layer;
    * ``distance``: the measure at that layer;
    * ``all_views``: a list of ``(layer_name, view_a, view_b, distance)``
      for every layer that was tried.

    Parameters
    ----------
    carrier_a, carrier_b
        The two 24-coordinate carriers to compare.
    start
        The layer index to start from (0 = substrate).
    """
    views = []
    for layer in LAYERS[start:]:
        va = layer.perceive(carrier_a)
        vb = layer.perceive(carrier_b)
        d = layer.measure(va, vb)
        views.append((layer.name, va, vb, d))
    # the highest layer that was tried
    final_layer = LAYERS[start + len(views) - 1]
    va = final_layer.perceive(carrier_a)
    vb = final_layer.perceive(carrier_b)
    d = final_layer.measure(va, vb)
    return {
        "layer": final_layer,
        "view_a": va,
        "view_b": vb,
        "distance": d,
        "all_views": views,
    }


# ===========================================================================
# 9.  PROJECTION REPORT
# ===========================================================================

def projection_report(carrier_a: Optional[Sequence] = None,
                      carrier_b: Optional[Sequence] = None) -> Dict[str, object]:
    """Recompute the dimension projection facts on demand.

    If two carriers are given, runs ``escalate`` on them and reports the
    views at every layer.  If not, uses two default carriers (the zero
    vector and a minimal vector) to demonstrate the projection.

    Every number is computed, not quoted.
    """
    if carrier_a is None:
        carrier_a = [Fraction(0)] * 24
    if carrier_b is None:
        # use a minimal vector if available
        try:
            mv = next(iter(leech2.minimal_vectors()))
            carrier_b = [Fraction(x) for x in mv]
        except StopIteration:
            carrier_b = [Fraction(1)] + [Fraction(0)] * 23

    result = escalate(carrier_a, carrier_b)

    layer_reports = []
    for layer_name, va, vb, d in result["all_views"]:
        layer = LAYER_BY_NAME[layer_name]
        layer_reports.append({
            "name": layer_name,
            "dimension": layer.dimension,
            "can_multiply": layer.can_multiply,
            "distance": str(d),
            "view_a_keys": sorted(k for k in va.keys()
                                  if k not in ("carrier", "algebra_element")),
            "view_b_keys": sorted(k for k in vb.keys()
                                  if k not in ("carrier", "algebra_element")),
        })

    return {
        "layers": layer_reports,
        "final_layer": result["layer"].name,
        "final_distance": str(result["distance"]),
        "total_layers": len(LAYERS),
    }
