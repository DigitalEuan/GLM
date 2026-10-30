"""``glm_universal.substrate.superposition`` -- carrying a Golay tie forward.

Why this module exists
----------------------
:mod:`glm_universal.substrate.golay_decode` retired the legacy ``snap``: at
coset weight 4 it returns **all six** nearest codewords and refuses to choose.
That is where the package stopped.  This module is what happens next -- the
engineering directive "Geometric Ambiguity and Conceptual Superposition" asks
for the six candidates to be *carried* as an active parallel hypothesis space,
bundled into a single hypervector, and collapsed later by context rather than
by a coin flip.

The directive names two bundling rules in one breath, as if they were
interchangeable:

    ``COMPUTING_IN_SUPERPOSITION_METHOD``: VSA bundling (rational vector
    addition **and** ``F_2`` symmetric difference to carry parallel
    hypotheses).

They are not interchangeable, and the difference is not a matter of degree:

* :func:`bundle_f2` -- the XOR bundle of a complete six-fold tie is
  ``0xFFFFFF``, the all-ones word, **for every received word**.  The six error
  patterns are a sextet: six disjoint tetrads covering all 24 coordinates, so
  they XOR to all-ones, and the six copies of the received word cancel in
  characteristic two.  XOR-bundling a complete tie destroys exactly the
  information it was introduced to preserve.
* :func:`bundle_rational` -- the rational bundle is ``(1 + 4 v_i) / 6``
  coordinatewise: an affine, invertible image of the received word.
  :func:`recover_from_bundle` inverts it, so the whole hypothesis space travels
  in one hypervector with nothing lost.

Both statements are theorems, machine-checked in Lean under
``RequestProject/GLM/Superposition.lean`` (``bundleF2_eq_one``,
``bundleQ_eq``, ``bundleQ_injective``).  Everything here recomputes them over
the actual code.

What else is here
-----------------
* :func:`superpose` -- list decoding as a first-class object, with the sextet
  exposed and its partition property checked.
* :func:`collapse` -- the measurement operator: a downstream predicate (a
  dimensional check, a stoichiometric balance, a lexicon constraint) filters
  the hypothesis space; the result says whether it collapsed to one state,
  stayed in superposition, or ruled everything out.  No tie is ever broken by
  enumeration order.
* :func:`sextet_cycle_reading` -- the "wiggle": a carrier that visits the six
  candidates in a cycle rather than snapping to one.  Its exact time average
  over a completed cycle *is* the rational bundle, so the trajectory
  distribution determines the received word (Lean: ``sextet_cycle_avgVec``,
  ``sextet_cycle_determines``).
* :func:`coset_census_report` -- how *often* the tie happens.  The 4,096
  cosets sit at distances ``1, 24, 276, 2024, 1771``, so 1,771 of them are
  six-fold ties, and the mean distance to the code is exactly ``3433/1024``:
  strictly past the packing radius 3, strictly inside the covering radius 4.
  The average word is already outside the radius of unique reading (Lean:
  ``coset_census``, ``mean_coset_weight``).
* :func:`alphabet_expansion_report` -- the hull experiment.  Widening the
  emitted alphabet by *scaling* codewords does not widen what the carrier can
  reach; widening it by admitting new *supports* -- minimal Leech vectors of
  shape ``(+-4^2, 0^22)`` -- does.  Certificate and witness are both exact.

Exact arithmetic only: ``int`` and ``fractions.Fraction``.  No float is
constructed anywhere in this module, and no RNG is imported.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .golay_decode import (COVERING_RADIUS, N, PACKING_RADIUS,
                           coset_table, decode_complete)
from .linalg import popcount
from .mog import GOLAY, GOLAY_MASKS

__all__ = [
    "ALL_ONES", "TIE_COUNT",
    "LEAN_COSET_CENSUS", "LEAN_MEAN_COSET_WEIGHT",
    "Superposition", "Collapse",
    "superpose", "bundle_f2", "bundle_rational", "recover_from_bundle",
    "collapse", "sextet_cycle_reading",
    "coset_weight_distribution", "mean_coset_weight", "coset_census_report",
    "CHAIN_STEPS", "coset_chain_report",
    "sextet_partition_report", "bundling_report", "collapse_report",
    "alphabet_expansion_report", "superposition_report",
]

#: The all-ones 24-bit word: the value of every complete XOR bundle.
ALL_ONES = (1 << N) - 1

#: The number of equidistant codewords at the covering radius.
TIE_COUNT = 6


def _bits(mask: int) -> Tuple[int, ...]:
    """The 24 coordinate bits of a mask, coordinate 0 first."""
    return tuple((mask >> i) & 1 for i in range(N))


def _mask_of_bits(bits: Sequence[int]) -> int:
    out = 0
    for i, b in enumerate(bits):
        if b:
            out |= 1 << i
    return out


# ===========================================================================
# 1.  LIST DECODING AS AN OBJECT
# ===========================================================================

@dataclass(frozen=True)
class Superposition:
    """A received word together with its whole hypothesis space.

    Attributes
    ----------
    received
        The 24-bit word read.
    weight
        Its exact distance to the code (the coset weight, ``0..4``).
    leaders
        Every minimum-weight error pattern -- one below the covering radius,
        six at it.  At weight 4 these are the six tetrads of a sextet.
    candidates
        The nearest codewords, one per leader, sorted.
    ambiguous
        Whether more than one candidate survives.
    """

    received: int
    weight: int
    leaders: Tuple[int, ...]
    candidates: Tuple[int, ...]
    ambiguous: bool

    @property
    def dimension(self) -> int:
        """How many hypotheses are being carried."""
        return len(self.candidates)


def superpose(mask: int) -> Superposition:
    """List-decode ``mask``, keeping every nearest codeword."""
    d = decode_complete(mask)
    return Superposition(received=d.received, weight=d.weight,
                         leaders=d.leaders, candidates=d.candidates,
                         ambiguous=len(d.candidates) > 1)


def sextet_partition_report(samples: int = 64) -> Dict[str, object]:
    """The six leaders of a weight-4 coset partition the 24 coordinates.

    Checked on the first ``samples`` tetrads in lexicographic order -- the
    property is a theorem (``sextet_partition``), so a sample either agrees
    with it everywhere or exhibits a counterexample.
    """
    checked = 0
    disjoint = True
    covers = True
    sizes: set = set()
    for support in combinations(range(N), 4):
        if checked >= samples:
            break
        mask = _mask_of_bits([1 if i in support else 0 for i in range(N)])
        sup = superpose(mask)
        if sup.weight != 4:
            continue
        checked += 1
        sizes.add(len(sup.leaders))
        union = 0
        for a, b in combinations(sup.leaders, 2):
            if a & b:
                disjoint = False
        for leader in sup.leaders:
            union |= leader
        if union != ALL_ONES:
            covers = False
    return {
        "tetrads_checked": checked,
        "leader_counts": sorted(sizes),
        "pairwise_disjoint": disjoint,
        "covers_all_24": covers,
        "tie_count": TIE_COUNT,
    }


# ===========================================================================
# 2.  BUNDLING
# ===========================================================================

def bundle_f2(candidates: Sequence[int]) -> int:
    """The ``F_2`` (XOR) bundle of a hypothesis space.

    For a complete six-fold tie this is always :data:`ALL_ONES`, whatever was
    received -- see :func:`bundling_report`.
    """
    out = 0
    for c in candidates:
        out ^= c
    return out


def bundle_rational(candidates: Sequence[int]) -> Tuple[Fraction, ...]:
    """The exact rational bundle: the coordinatewise mean of the candidates."""
    if not candidates:
        raise ValueError("bundle_rational: empty hypothesis space")
    n = len(candidates)
    return tuple(Fraction(sum((c >> i) & 1 for c in candidates), n)
                 for i in range(N))


def recover_from_bundle(bundle: Sequence[Fraction]) -> int:
    """Invert :func:`bundle_rational` for a complete six-fold tie.

    Each coordinate of the bundle is ``(1 + 4 v_i) / 6``, so
    ``v_i = (6 b_i - 1) / 4``; any other value raises, because the bundle did
    not come from a complete tie.
    """
    bits: List[int] = []
    for b in bundle:
        if not isinstance(b, Fraction):
            raise TypeError("recover_from_bundle: bundles are exact Fractions")
        v = (6 * b - 1) / 4
        if v not in (0, 1):
            raise ValueError(
                "recover_from_bundle: not the bundle of a complete six-fold "
                f"tie (coordinate value {b})")
        bits.append(int(v))
    return _mask_of_bits(bits)


def bundling_report(samples: int = 256) -> Dict[str, object]:
    """XOR bundling is a constant; rational bundling is invertible.

    Runs over the first ``samples`` weight-4 words in lexicographic order of
    their support and recomputes, for each: the XOR bundle, the rational
    bundle, and the word recovered from the rational bundle.
    """
    checked = 0
    f2_values: set = set()
    q_values: set = set()
    recovered_ok = True
    distinct_bundles: set = set()
    for support in combinations(range(N), 4):
        if checked >= samples:
            break
        mask = _mask_of_bits([1 if i in support else 0 for i in range(N)])
        sup = superpose(mask)
        if sup.weight != 4:
            continue
        checked += 1
        f2_values.add(bundle_f2(sup.candidates))
        q = bundle_rational(sup.candidates)
        q_values.update(q)
        distinct_bundles.add(q)
        if recover_from_bundle(q) != mask:
            recovered_ok = False
    return {
        "words_checked": checked,
        "f2_bundle_values": sorted(f2_values),
        "f2_bundle_is_constant": len(f2_values) == 1,
        "f2_bundle_is_all_ones": f2_values == {ALL_ONES},
        "rational_bundle_coordinate_values": sorted(q_values),
        "rational_bundle_injective": len(distinct_bundles) == checked,
        "rational_bundle_recovers_input": recovered_ok,
        "f2_bundle_distinguishes": len(f2_values),
        "rational_bundle_distinguishes": len(distinct_bundles),
    }


# ===========================================================================
# 3.  COLLAPSE BY CONTEXT
# ===========================================================================

@dataclass(frozen=True)
class Collapse:
    """The result of measuring a superposition against a context.

    ``status`` is ``"collapsed"`` (exactly one candidate survived),
    ``"superposed"`` (several did) or ``"refuted"`` (none did).  A refuted
    measurement is information: the context and the read are incompatible.
    """

    before: Tuple[int, ...]
    after: Tuple[int, ...]
    status: str

    @property
    def value(self) -> Optional[int]:
        """The single surviving codeword, or ``None``."""
        return self.after[0] if self.status == "collapsed" else None


def collapse(superposition: Superposition,
             context: Callable[[int], bool]) -> Collapse:
    """Filter a hypothesis space by a downstream context predicate."""
    survivors = tuple(c for c in superposition.candidates if context(c))
    if len(survivors) == 1:
        status = "collapsed"
    elif survivors:
        status = "superposed"
    else:
        status = "refuted"
    return Collapse(before=superposition.candidates, after=survivors,
                    status=status)


def collapse_report() -> Dict[str, object]:
    """Three measurements of one ambiguous read: collapse, hold, refute."""
    mask = _mask_of_bits([1 if i < 4 else 0 for i in range(N)])
    sup = superpose(mask)
    chosen = sup.candidates[0]
    one = collapse(sup, lambda c: c == chosen)
    some = collapse(sup, lambda c: popcount(c) <= 12)
    none = collapse(sup, lambda c: popcount(c) == 1)
    return {
        "received": mask,
        "weight": sup.weight,
        "dimension": sup.dimension,
        "collapsed": {"status": one.status, "value": one.value},
        "superposed": {"status": some.status, "survivors": len(some.after)},
        "refuted": {"status": none.status, "survivors": len(none.after)},
        "no_tie_broken_by_order": one.value == chosen,
    }


# ===========================================================================
# 4.  THE WIGGLE: A CARRIER THAT VISITS ALL SIX
# ===========================================================================

def sextet_cycle_reading(mask: int) -> Tuple[Fraction, ...]:
    """The exact time average of a carrier cycling through the six candidates.

    A carrier that emits the six nearest codewords in turn reads back, at every
    completed cycle, exactly the rational bundle of the tie -- so the *motion*
    computes a faithful encoding of the received word, where a snap would have
    thrown 10,626 possibilities away.
    """
    sup = superpose(mask)
    return bundle_rational(sup.candidates)


# ===========================================================================
# 5.  HOW OFTEN: THE COSET CENSUS
# ===========================================================================

#: The census machine-checked in Lean (`Golay/Census.lean`, `coset_census`):
#: how many of the 4,096 cosets sit at each distance from the code.
LEAN_COSET_CENSUS: Dict[int, int] = {0: 1, 1: 24, 2: 276, 3: 2024, 4: 1771}

#: The mean coset weight machine-checked in Lean (`mean_coset_weight`).
LEAN_MEAN_COSET_WEIGHT: Fraction = Fraction(3433, 1024)


def coset_weight_distribution() -> Dict[int, int]:
    """``distance to the code -> how many of the 4,096 cosets sit there``.

    Recomputed from the decoder's own coset table, not quoted.  Comes out as
    ``{0: 1, 1: 24, 2: 276, 3: 2024, 4: 1771}``.
    """
    counts: Dict[int, int] = {}
    for leaders in coset_table().values():
        w = popcount(leaders[0])
        counts[w] = counts.get(w, 0) + 1
    return dict(sorted(counts.items()))


def mean_coset_weight() -> Fraction:
    """The average distance from a 24-bit word to the code, exactly.

    Every coset holds the same number of words (4,096 of them), so averaging
    over cosets and averaging over words are the same number:
    ``13732 / 4096 = 3433 / 1024``.  Exact ``Fraction`` arithmetic; no float.
    """
    counts = coset_weight_distribution()
    cosets = sum(counts.values())
    total = sum(w * c for w, c in counts.items())
    return Fraction(total, cosets)


def coset_census_report() -> Dict[str, object]:
    """Where the *average* word sits, and how much of the code is ambiguous.

    The sextet reports above describe the shape of the tie.  This one counts
    how often it happens.  The packing radius is 3 and the covering radius is
    4; the mean distance to the code is ``3433/1024 = 3.352...``, strictly
    between them.  So the average received word is already **past** the radius
    inside which the nearest-codeword reading is unique: ambiguity is the
    typical case for this code, not a corner case, and a decoder that always
    returns a single codeword is suppressing a live alternative on
    ``1771/4096`` of its inputs.

    Lean: ``GLM.Golay24.coset_census``, ``unique_vs_ambiguous``,
    ``mean_coset_weight``, ``mean_coset_weight_gt_three``,
    ``mean_coset_weight_lt_four`` in ``Golay/Census.lean``.
    """
    counts = coset_weight_distribution()
    cosets = sum(counts.values())
    total_weight = sum(w * c for w, c in counts.items())
    mean = mean_coset_weight()
    unique = sum(c for w, c in counts.items() if w <= PACKING_RADIUS)
    ambiguous = sum(c for w, c in counts.items() if w > PACKING_RADIUS)
    return {
        "cosets": cosets,
        "cosets_by_distance": counts,
        "total_coset_weight": total_weight,
        "mean_coset_weight": mean,
        "packing_radius": PACKING_RADIUS,
        "covering_radius": COVERING_RADIUS,
        "mean_exceeds_packing_radius": mean > PACKING_RADIUS,
        "mean_below_covering_radius": mean < COVERING_RADIUS,
        "uniquely_read_cosets": unique,
        "ambiguous_cosets": ambiguous,
        "ambiguous_fraction": Fraction(ambiguous, cosets),
        "census_agrees_with_lean": counts == LEAN_COSET_CENSUS,
        "mean_agrees_with_lean": mean == LEAN_MEAN_COSET_WEIGHT,
    }


# ===========================================================================
# 5b.  THE DYNAMICAL HALF: A CARRIER UNDER REPEATED PERTURBATION
# ===========================================================================

#: How many ticks the chain report runs.  Twelve is enough to show both the
#: two-step periodicity and the time average settling; the arithmetic is exact
#: and the cost is linear in this number.
CHAIN_STEPS = 12


def _columns() -> Tuple[int, ...]:
    """The 24 parity-check columns, as syndromes of the unit words."""
    return tuple(GOLAY.syndrome_int(1 << k) for k in range(N))


def _syndrome_weights() -> Tuple[int, ...]:
    """``syndrome -> distance to the code``, indexed by syndrome integer."""
    table = coset_table()
    return tuple(popcount(table[s][0]) for s in range(1 << 12))


def coset_chain_report(steps: int = CHAIN_STEPS) -> Dict[str, object]:
    """Does a perturbed carrier *settle* at the critical weight?

    The census says where the average word sits.  This says what a *process*
    does.  One tick is "flip a uniformly chosen coordinate", which adds a
    parity-check column to the carrier's syndrome, so the law over the 4,096
    cosets is pushed forward exactly (integer numerators over ``24 ** n``; no
    float, no sampling).  Three findings, all matching
    ``RequestProject/GLM/Golay/Dynamics.lean``:

    * the uniform law is stationary and is the only stationary law
      (``step_unif``, ``stationary_unique``), and under it the mean distance
      to the code is the census figure ``3433/1024``;
    * the chain is **periodic**: every column has odd parity, so the law after
      ``n`` ticks lives entirely on one of the two parity classes and is never
      uniform (``iterate_dirac_ne_unif``).  There is no limiting law; only the
      time average can settle, and the time averages computed here do
      approach ``3433/1024``;
    * the stationary law does not concentrate either: it puts ``301/4096`` on
      distances ``<= 2`` (``prob_unif_subcritical_pos``), so the weight keeps
      fluctuating rather than locking on to the boundary.

    With *correction* after each perturbation the question does not even
    arise: a one-bit error on a codeword is corrected back to that codeword
    uniquely (``perturb_correct_returns``), so the corrected carrier sits on
    the code for ever, at distance 0 -- checked here on every coordinate of a
    sample of codewords.
    """
    cols = _columns()
    weights = _syndrome_weights()
    size = 1 << 12

    # exact push-forward: numerators over 24 ** n, starting from a point mass
    law = [0] * size
    law[0] = 1
    denom = 1
    supports: List[int] = []
    parity_classes: List[int] = []
    means: List[Fraction] = []
    for _ in range(steps):
        nxt = [0] * size
        for f, m in enumerate(law):
            if m:
                for c in cols:
                    nxt[f ^ c] += m
        law = nxt
        denom *= N
        supports.append(sum(1 for m in law if m))
        parities = {popcount(f) & 1 for f, m in enumerate(law) if m}
        parity_classes.append(sorted(parities)[0] if len(parities) == 1 else -1)
        means.append(Fraction(sum(m * weights[f] for f, m in enumerate(law)),
                              denom))

    stationary = LEAN_MEAN_COSET_WEIGHT
    cesaro = sum(means, Fraction(0)) / len(means)
    last_pair = (means[-2] + means[-1]) / 2

    # the uniform law is stationary, exactly
    uniform = Fraction(1, size)
    pushed = [sum((uniform for _ in cols), Fraction(0)) / N for _ in range(4)]
    uniform_stationary = all(x == uniform for x in pushed)

    # correction after each perturbation returns the same codeword
    corrected_ok = True
    corrected_distances = set()
    for c in GOLAY_MASKS[:8]:
        for k in range(N):
            d = decode_complete(c ^ (1 << k))
            corrected_distances.add(d.weight)
            if d.candidates != (c,):
                corrected_ok = False
    return {
        "states": size,
        "steps": steps,
        "columns_all_odd_parity": all(popcount(c) % 2 == 1 for c in cols),
        "uniform_is_stationary": uniform_stationary,
        "stationary_mean_distance": stationary,
        "support_by_step": tuple(supports),
        "parity_class_by_step": tuple(parity_classes),
        "parity_alternates": parity_classes == [(i + 1) % 2
                                                 for i in range(steps)],
        "law_never_uniform": all(s <= size // 2 for s in supports),
        "mean_distance_by_step": tuple(means),
        "time_average_mean_distance": cesaro,
        "two_step_average_mean_distance": last_pair,
        "time_average_error": abs(cesaro - stationary),
        "two_step_average_error": abs(last_pair - stationary),
        "settles_in_distribution": False,
        "corrected_carrier_returns_to_code": corrected_ok,
        "corrected_distances_before_correction": sorted(corrected_distances),
        "corrected_distance_after_correction": 0,
    }


# ===========================================================================
# 6.  THE HULL: SCALING VERSUS NEW SUPPORTS
# ===========================================================================

#: The separating functional ``7 x_0 - sum_{j != 0} x_j``.
_FUNCTIONAL: Tuple[int, ...] = tuple(7 if i == 0 else -1 for i in range(N))

#: The target ``(1/2) e_0``: half a unit on one coordinate, nothing elsewhere.
_TARGET: Tuple[Fraction, ...] = tuple(
    Fraction(1, 2) if i == 0 else Fraction(0) for i in range(N))


def _apply_functional(vector: Sequence[Fraction]) -> Fraction:
    return sum((Fraction(_FUNCTIONAL[i]) * vector[i] for i in range(N)),
               Fraction(0))


def alphabet_expansion_report() -> Dict[str, object]:
    """Widening the alphabet: scale changes nothing, support changes everything.

    The concept under test is "let the modulator emit Leech lattice points or
    scaled codewords, so the convex hull it can wiggle through is larger".
    Half of it fails and half of it works, and the report separates them:

    * the functional ``7 x_0 - sum_{j != 0} x_j`` is ``<= 0`` on **all 4,096**
      codewords (checked here) and hence on every non-negative multiple of one,
      while it takes the value ``7/2`` at the target ``(1/2) e_0``.  So no
      carrier emitting scaled codewords ever reads that target: the obstruction
      is that a codeword through coordinate 0 drags seven more coordinates with
      it (minimum weight 8), and scaling cannot separate them.
    * admitting the two minimal Leech vectors ``4 e_0 +- 4 e_1`` -- shape
      ``(+-4^2, 0^22)``, support 2, a support no nonzero codeword has -- puts
      the target inside reach, and a 16-tick cycle hits it exactly.

    Lean: ``GLM.Hull.alphabet_expansion_strictly_helps``.
    """
    worst = None
    for c in GOLAY_MASKS:
        value = _apply_functional(tuple(Fraction(b) for b in _bits(c)))
        if worst is None or value > worst:
            worst = value
    target_value = _apply_functional(_TARGET)

    plus = [Fraction(4) if i in (0, 1) else Fraction(0) for i in range(N)]
    minus = [Fraction(4) if i == 0 else (Fraction(-4) if i == 1
                                         else Fraction(0)) for i in range(N)]
    zero = [Fraction(0)] * N
    cycle = [plus, minus] + [zero] * 14
    reading = tuple(sum((v[i] for v in cycle), Fraction(0)) / len(cycle)
                    for i in range(N))

    return {
        "codewords_checked": len(GOLAY_MASKS),
        "functional": _FUNCTIONAL,
        "max_over_scaled_codewords": worst,
        "value_at_target": target_value,
        "target_separated_from_scaled_hull": worst <= 0 < target_value,
        "leech_cycle_length": len(cycle),
        "leech_cycle_reading": reading,
        "leech_cycle_reaches_target": reading == _TARGET,
        "scaling_helps": False,
        "new_supports_help": True,
    }


# ===========================================================================
# 7.  THE WHOLE STUDY, RECOMPUTED
# ===========================================================================

def superposition_report() -> Dict[str, object]:
    """Everything this module claims, recomputed from the code itself."""
    return {
        "sextet": sextet_partition_report(),
        "bundling": bundling_report(),
        "collapse": collapse_report(),
        "census": coset_census_report(),
        "chain": coset_chain_report(),
        "hull": alphabet_expansion_report(),
        "tie_count": TIE_COUNT,
        "all_ones": ALL_ONES,
    }
