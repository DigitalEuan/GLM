"""``glm_universal.reasoning.containers`` -- generators, wobble, hull.

What this module is
-------------------
The companion study *The Generators and Containers of Real Processes* profiles
eight constants through three "containers":

1. **the algorithmic container** -- the exact-rational generator that produces
   the constant, and how many steps it needs to reach a stated precision;
2. **the temporal container** -- the delta-sigma stream whose running average
   converges to the constant, and the statistics of that stream;
3. **the geometric container** -- the constant projected into 24 coordinates
   and tested against the convex hull of the Leech minimal vectors.

This module is the instrument for all three.  It is written so that a claim
about any of them can be *settled* rather than repeated: every generator is
exact over ``Q``, every precision figure is an integer comparison, and the
hull verdict is a certificate rather than a sample.

Three things are worth saying about method, because they are what make the
verdicts in :mod:`~glm_universal.reasoning.companion` mean anything.

**Steps are counted from zero.**  ``x_0`` is the generator's first value, so
"three steps to ten bits" means ``x_3`` is the first iterate accurate to ten
bits.  The study does not state its indexing; this one reproduces its table
for Heron, Machin and the exponential series, which is the reason to prefer
it.

**Precision is relative and exact.**  ``precision_bits`` returns the largest
``b`` with ``|x - x*| / |x*| <= 2**-b``, decided by integer comparison against
a reference held to far more bits than the answer needs.  No logarithm is
taken and no float is constructed anywhere in this file.

**A hull verdict is a certificate or it is nothing.**  Sampling witnesses can
prove that a point is *inside* a hull -- the sample is a subset, so a convex
combination over it is a convex combination over the whole -- but it can never
prove that a point is outside.  Two exact tests are used instead:

``outside``
    some direction ``u`` separates: ``<u, x>`` exceeds ``max_p <u, p>`` over
    all 196,560 minimal vectors, so no convex combination of them reaches
    ``x``.  Two directions are tried: the study's own proposal ``u = x``, and
    one tuned by descent, which is what settles Champernowne's constant;
``inside``
    the target lies in ``{x : |x|_1 <= 8, |x|_inf <= 4}``, whose extreme
    points are exactly the 1,104 minimal vectors of shape ``(+-4, +-4, 0^22)``
    and which is therefore contained in the hull.

Anything the two tests do not settle is reported as ``undetermined``, which is
the honest answer and not a failure.

Reachable from the runtime as ``report containers``.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..derived import memo
from ..substrate import leech2
from . import exact_real as xr
from . import wobble as wb

__all__ = [
    "PRECISION_THRESHOLDS", "REFERENCE_BITS",
    "heron_sequence", "golden_sequence", "machin_sequence",
    "exponential_sequence", "liouville_sequence", "champernowne_bits",
    "champernowne_sequence", "lcg_bits", "omega_surrogate_sequence",
    "one_third_sequence",
    "Constant", "CONSTANTS", "constant_by_name",
    "precision_bits", "precision_profile", "convergence_table",
    "stream_of", "wobble_row", "wobble_table", "AUTOCORRELATION_LAGS",
    "autocorrelation_row", "autocorrelation_table", "apparent_period",
    "stream_period", "near_period_coincidence",
    "PROJECTION_SCALE", "INSIDE_L1_BOUND", "INSIDE_LINF_BOUND",
    "SEPARATING_DIRECTIONS", "projection", "projection_norm2",
    "projection_l1", "projection_linf", "support", "separating_scale",
    "unit_support", "inside_certificate", "outside_certificate",
    "hull_status", "hull_table", "implied_value", "critical_scales",
    "containers_report",
]


#: The precision thresholds the study tabulates, in bits.
PRECISION_THRESHOLDS: Tuple[int, ...] = (10, 30, 50)

#: How many bits the reference values carry.  Far more than any threshold, so
#: the comparison is settled by the reference rather than limited by it.
REFERENCE_BITS = 200


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE GENERATORS
# ═════════════════════════════════════════════════════════════════════════
#
# Each returns the whole trajectory, ``x_0`` first.  Every value is an exact
# ``Fraction``; no float is constructed.

def heron_sequence(n: int, steps: int, start: Fraction = Fraction(1)
                   ) -> Tuple[Fraction, ...]:
    """Heron's method for ``sqrt(n)``: ``x_(k+1) = (x_k + n/x_k) / 2``.

    The study states ``x_0 = 1``, which is the default here.  The number of
    correct bits doubles at every step, so the denominators double too: eight
    steps already carry more than two hundred bits.
    """
    if n < 1:
        raise ValueError("heron_sequence: n must be positive")
    if steps < 0:
        raise ValueError("heron_sequence: steps must not be negative")
    out = [Fraction(start)]
    for _ in range(steps):
        x = out[-1]
        out.append((x + Fraction(n) / x) / 2)
    return tuple(out)


def golden_sequence(steps: int) -> Tuple[Fraction, ...]:
    """``phi_k = (1 + s_k) / 2`` with ``s_k`` the Heron iterates for
    ``sqrt(5)`` -- the study's construction of the golden ratio."""
    return tuple((1 + s) / 2 for s in heron_sequence(5, steps))


def _arctangent_partial(inverse: int, terms: int) -> Fraction:
    """``arctan(1/inverse)`` summed to ``terms`` terms, exactly."""
    total = Fraction(0)
    for n in range(terms):
        sign = -1 if n % 2 else 1
        total += Fraction(sign, (2 * n + 1) * inverse ** (2 * n + 1))
    return total


def machin_sequence(steps: int) -> Tuple[Fraction, ...]:
    """Machin's formula ``pi = 16 arctan(1/5) - 4 arctan(1/239)``.

    Step ``k`` is the partial sum with ``k + 1`` terms of each arc-tangent
    series, so that ``x_0`` is the one-term approximation.
    """
    if steps < 0:
        raise ValueError("machin_sequence: steps must not be negative")
    return tuple(16 * _arctangent_partial(5, k + 1)
                 - 4 * _arctangent_partial(239, k + 1)
                 for k in range(steps + 1))


def exponential_sequence(steps: int) -> Tuple[Fraction, ...]:
    """``e = sum 1/n!``: step ``k`` is the partial sum with ``k + 1`` terms."""
    if steps < 0:
        raise ValueError("exponential_sequence: steps must not be negative")
    out: List[Fraction] = []
    total = Fraction(0)
    factorial = 1
    for n in range(steps + 1):
        if n:
            factorial *= n
        total += Fraction(1, factorial)
        out.append(total)
    return tuple(out)


def liouville_sequence(steps: int) -> Tuple[Fraction, ...]:
    """Liouville's constant ``sum 10**-n!``, one term per step.

    ``x_0`` is the first term, ``10**-1``.  The terms are so sparse that the
    fourth already carries eighty bits.
    """
    if steps < 0:
        raise ValueError("liouville_sequence: steps must not be negative")
    out: List[Fraction] = []
    total = Fraction(0)
    factorial = 1
    for n in range(1, steps + 2):
        factorial *= n
        total += Fraction(1, 10 ** factorial)
        out.append(total)
    return tuple(out)


def champernowne_bits(count: int) -> Tuple[int, ...]:
    """The first ``count`` binary digits of Champernowne's constant.

    ``C_2 = 0.1 10 11 100 101 110 111 1000 ...``: the binary representations
    of 1, 2, 3, ... concatenated.
    """
    if count < 0:
        raise ValueError("champernowne_bits: count must not be negative")
    bits: List[int] = []
    n = 1
    while len(bits) < count:
        bits.extend(int(b) for b in bin(n)[2:])
        n += 1
    return tuple(bits[:count])


def champernowne_sequence(steps: int) -> Tuple[Fraction, ...]:
    """Champernowne's constant, one binary digit revealed per step."""
    bits = champernowne_bits(steps + 1)
    out: List[Fraction] = []
    total = Fraction(0)
    for i, bit in enumerate(bits):
        if bit:
            total += Fraction(1, 2 ** (i + 1))
        out.append(total)
    return tuple(out)


#: The linear congruential generator the study names for its Chaitin-Omega
#: surrogate: ``x <- (a x + c) mod m``.  The *seed* and the rule for reading a
#: bit out of a state are not stated there; the two below are this module's
#: choice, and the ledger records that the row therefore cannot be reproduced
#: rather than pretending it can.
LCG_MULTIPLIER = 1103515245
LCG_INCREMENT = 12345
LCG_MODULUS = 2 ** 31
LCG_SEED = 1


def lcg_bits(count: int, seed: int = LCG_SEED) -> Tuple[int, ...]:
    """``count`` bits of the linear congruential stream: the top bit of each
    successive state.  Deterministic, and reproducible bit for bit."""
    if count < 0:
        raise ValueError("lcg_bits: count must not be negative")
    state = seed
    out: List[int] = []
    for _ in range(count):
        state = (LCG_MULTIPLIER * state + LCG_INCREMENT) % LCG_MODULUS
        out.append((state >> 30) & 1)
    return tuple(out)


def omega_surrogate_sequence(steps: int, seed: int = LCG_SEED
                             ) -> Tuple[Fraction, ...]:
    """The Omega surrogate, one bit of the congruential stream per step."""
    bits = lcg_bits(steps + 1, seed)
    out: List[Fraction] = []
    total = Fraction(0)
    for i, bit in enumerate(bits):
        if bit:
            total += Fraction(1, 2 ** (i + 1))
        out.append(total)
    return tuple(out)


def one_third_sequence(steps: int) -> Tuple[Fraction, ...]:
    """The rigid baseline: ``1/3`` is a ``Fraction``, exact at step 0."""
    return tuple(Fraction(1, 3) for _ in range(steps + 1))


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE EIGHT CONSTANTS
# ═════════════════════════════════════════════════════════════════════════

class Constant:
    """One profiled constant: its class, its generator and its reference."""

    __slots__ = ("name", "kind", "notation", "_generator", "steps",
                 "_reference")

    def __init__(self, name: str, kind: str, notation: str,
                 generator: Callable[[int], Tuple[Fraction, ...]],
                 steps: int,
                 reference: Callable[[], Fraction]) -> None:
        self.name = name
        self.kind = kind
        self.notation = notation
        self._generator = generator
        self.steps = steps
        self._reference = reference

    def trajectory(self, steps: Optional[int] = None
                   ) -> Tuple[Fraction, ...]:
        """The generator's values, ``x_0`` first."""
        return self._generator(self.steps if steps is None else steps)

    def reference(self) -> Fraction:
        """The value the trajectory converges to, to ``REFERENCE_BITS``."""
        return self._reference()

    def fractional_part(self) -> Fraction:
        """What the modulator chases: the constant modulo one."""
        value = self.reference()
        return value - int(value)

    def __repr__(self) -> str:                       # pragma: no cover
        return f"Constant({self.name!r}, {self.kind!r})"


def _reference_sqrt2() -> Fraction:
    return xr.surrogate(xr.parse_real("sqrt(2)"), REFERENCE_BITS)


def _reference_phi() -> Fraction:
    return (1 + xr.surrogate(xr.parse_real("sqrt(5)"), REFERENCE_BITS)) / 2


def _reference_pi() -> Fraction:
    return xr.surrogate(xr.pi(), REFERENCE_BITS)


def _reference_e() -> Fraction:
    return xr.surrogate(xr.parse_real("exp(1)"), REFERENCE_BITS)


def _reference_champernowne() -> Fraction:
    return champernowne_sequence(REFERENCE_BITS)[-1]


def _reference_liouville() -> Fraction:
    return liouville_sequence(6)[-1]


def _reference_omega() -> Fraction:
    return omega_surrogate_sequence(REFERENCE_BITS)[-1]


def _reference_one_third() -> Fraction:
    return Fraction(1, 3)


#: The eight constants, in the study's order.  ``steps`` is how far the
#: trajectory is run: far enough to settle the 50-bit threshold where the
#: generator can reach it, and 30 steps for the two that reveal one bit per
#: step, which is where the study stops as well.
CONSTANTS: Tuple[Constant, ...] = (
    Constant("sqrt(2)", "algebraic", "Heron",
             lambda steps: heron_sequence(2, steps), 8, _reference_sqrt2),
    Constant("phi", "algebraic", "Heron on 5",
             golden_sequence, 8, _reference_phi),
    Constant("pi", "transcendental", "Machin",
             machin_sequence, 14, _reference_pi),
    Constant("e", "transcendental", "Taylor",
             exponential_sequence, 22, _reference_e),
    Constant("Champernowne", "exotic", "concatenation",
             champernowne_sequence, 30, _reference_champernowne),
    Constant("Liouville", "exotic", "sum 10**-n!",
             liouville_sequence, 5, _reference_liouville),
    Constant("omega surrogate", "exotic", "congruential",
             omega_surrogate_sequence, 30, _reference_omega),
    Constant("1/3", "rigid", "exact",
             one_third_sequence, 1, _reference_one_third),
)


def constant_by_name(name: str) -> Constant:
    for constant in CONSTANTS:
        if constant.name == name:
            return constant
    raise KeyError(f"containers: no constant named {name!r}")


# ═════════════════════════════════════════════════════════════════════════
# 3.  PHASE 1 -- CONVERGENCE PROFILING
# ═════════════════════════════════════════════════════════════════════════

def precision_bits(approximation: Fraction, reference: Fraction) -> int:
    """The largest ``b`` with ``|x - x*| / |x*| <= 2**-b``.

    Integer arithmetic throughout: the comparison is
    ``|x - x*| * 2**b <= |x*|``, doubled until it fails.  An exact hit
    returns ``REFERENCE_BITS``, since the reference itself carries no more.
    """
    if reference == 0:
        raise ValueError("precision_bits: the reference must be non-zero")
    error = abs(Fraction(approximation) - Fraction(reference))
    if error == 0:
        return REFERENCE_BITS
    target = abs(Fraction(reference))
    bits = 0
    while error * 2 ** (bits + 1) <= target and bits < REFERENCE_BITS:
        bits += 1
    return bits


def precision_profile(constant: Constant,
                      thresholds: Sequence[int] = PRECISION_THRESHOLDS
                      ) -> Dict[str, object]:
    """How many steps each precision threshold costs this constant.

    ``None`` in the ``steps_to`` map means the threshold was not reached
    within the trajectory -- which is the study's "never", and is a statement
    about the trajectory length, not about the constant.
    """
    reference = constant.reference()
    trajectory = constant.trajectory()
    profile = [precision_bits(value, reference) for value in trajectory]
    steps_to: Dict[int, Optional[int]] = {}
    for threshold in thresholds:
        hit = next((k for k, bits in enumerate(profile) if bits >= threshold),
                   None)
        steps_to[threshold] = hit
    return {
        "name": constant.name,
        "kind": constant.kind,
        "notation": constant.notation,
        "steps_run": len(trajectory) - 1,
        "bits_at_step": tuple(profile),
        "steps_to": steps_to,
        "final_bits": profile[-1],
        "exact_at_zero": profile[0] >= REFERENCE_BITS,
    }


def convergence_table(thresholds: Sequence[int] = PRECISION_THRESHOLDS
                      ) -> Tuple[Dict[str, object], ...]:
    """Phase 1 for all eight constants."""
    return tuple(precision_profile(constant, thresholds)
                 for constant in CONSTANTS)


# ═════════════════════════════════════════════════════════════════════════
# 4.  PHASE 2 -- THE WOBBLE SIGNATURE
# ═════════════════════════════════════════════════════════════════════════
#
# The statistics themselves live in ``reasoning/wobble.py``, which prints the
# proved closed form beside every measured column; this section only chooses
# the targets.  The point the ledger makes with them is the one
# ``Sturmian.lean`` proves: each column is a function of the target, so
# running ten thousand ticks tests the implementation, not the constant.

_STREAM_CACHE: Dict[Tuple[Fraction, int], Tuple[int, ...]] = {}


def stream_of(constant: Constant, steps: int = wb.WOBBLE_STEPS
              ) -> Tuple[int, ...]:
    """The modulator's stream for a constant's fractional part, cached.

    Phase 2 reads the same stream twice -- once for the run and entropy
    statistics and once for the autocorrelation column -- and the census
    reads it again, so the ten thousand exact steps are worth keeping.
    """
    key = (constant.fractional_part(), steps)
    cached = _STREAM_CACHE.get(key)
    if cached is None:
        cached = wb.stream_bits(key[0], steps)
        _STREAM_CACHE[key] = cached
    return cached


def wobble_row(constant: Constant, steps: int = wb.WOBBLE_STEPS
               ) -> Dict[str, object]:
    """One row of Phase 2: the delta-sigma stream of a constant's fraction."""
    return wb.signature(constant.name, constant.notation,
                        constant.fractional_part(), steps)


def wobble_table(steps: int = wb.WOBBLE_STEPS
                 ) -> Tuple[Dict[str, object], ...]:
    """Phase 2 for all eight constants."""
    return tuple(wobble_row(constant, steps) for constant in CONSTANTS)


#: The lags the study's autocorrelation column reports.
AUTOCORRELATION_LAGS: Tuple[int, ...] = (1, 10, 100, 1000)


def autocorrelation_row(constant: Constant,
                        lags: Sequence[int] = AUTOCORRELATION_LAGS,
                        steps: int = wb.WOBBLE_STEPS) -> Dict[str, object]:
    """The study's autocorrelation column, on the study's own alphabet.

    The study does not define its autocorrelation, and its own rigid baseline
    fixes which one it is: a period-three stream has centred (Pearson) lag-one
    autocorrelation ``-1/2``, but on the ``+/-1`` alphabet the *uncentred* mean
    product is ``-1/3``, which is the figure tabulated.  So the column is
    :func:`~glm_universal.reasoning.wobble.product_autocorrelation`, whose
    lag-one value is the closed form ``1 - 4 min(t, 1 - t)`` in the target.
    """
    target = constant.fractional_part()
    bits = stream_of(constant, steps)
    values = {lag: wb.product_autocorrelation(bits, lag) for lag in lags}
    law = wb.product_autocorrelation_law(target)
    return {
        "name": constant.name,
        "kind": constant.kind,
        "target": target,
        "steps": steps,
        "lags": tuple(lags),
        "autocorrelation": values,
        "rounded": {lag: wb.round_str(value, 3)
                    for lag, value in values.items()},
        "lag1_law": law,
        "lag1_law_rounded": wb.round_str(law, 3),
        "lag1_matches_law": (1 in values
                             and wb.round_str(values[1], 3)
                             == wb.round_str(law, 3)),
    }


def autocorrelation_table(lags: Sequence[int] = AUTOCORRELATION_LAGS,
                          steps: int = wb.WOBBLE_STEPS
                          ) -> Tuple[Dict[str, object], ...]:
    """The autocorrelation half of Phase 2, for all eight constants."""
    return tuple(autocorrelation_row(constant, lags, steps)
                 for constant in CONSTANTS)


def apparent_period(bits: Sequence[int]) -> Optional[int]:
    """The least ``p`` the *window* repeats at, or ``None`` if there is none.

    This is a measurement of a finite window and nothing more: a stream can
    repeat at ``p`` for every index the window holds and never repeat at ``p``
    again.  :func:`stream_period` is the certified reading; this one is kept
    beside it because the gap between the two is itself a finding (see
    :func:`near_period_coincidence`).
    """
    n = len(bits)
    for period in range(1, n // 2 + 1):
        if all(bits[i] == bits[i + period] for i in range(n - period)):
            return period
    return None


def stream_period(constant: Constant, steps: int = 600) -> Optional[int]:
    """The least period of the constant's stream, or ``None`` if it has none.

    Only a rational target gives a periodic stream, and then the least period
    is exactly the denominator ``q`` of the target in lowest terms -- the
    stream is the mechanical word of ``t``, whose least period is ``q``.  So
    the period is *decided* from the target and then checked against the
    stream, rather than searched for in a window: a window can show a
    repetition that is not a period, and for an irrational target it always
    eventually does.  ``None`` is returned when no period is certified,
    either because the target's denominator does not fit twice inside
    ``steps`` or because the predicted period fails on the window.

    Reported because the study calls the rigid baseline's stream
    ``010101...``, which is period two; the stream the modulator actually
    produces for ``1/3`` has period three.
    """
    if steps <= 0:
        raise ValueError("stream_period: steps must be positive")
    period = constant.fractional_part().denominator
    if 2 * period > steps:
        return None
    bits = stream_of(constant, steps)
    if all(bits[i] == bits[i + period] for i in range(steps - period)):
        return period
    return None


def near_period_coincidence(constant: Constant,
                            steps: int = 400) -> Dict[str, object]:
    """What a windowed period search reports, and why it is not a period.

    An irrational target is carried here by a rational approximation, so its
    stream is periodic in principle -- at a period with hundreds of digits,
    which no window reaches.  What a window *does* reach is the denominator of
    a continued-fraction convergent of the target: the mechanical word of ``t``
    and that of a convergent ``p/q`` agree for far more than ``2q`` places, so
    a search over ``steps`` places reports ``q`` and calls it a period.

    ``sqrt(2)`` at 400 steps is the case in point: the search returns 169, the
    denominator of the convergent ``70/169``, and 169 is not a period of the
    stream -- the two words part company further out.
    """
    target = constant.fractional_part()
    bits = stream_of(constant, steps)
    apparent = apparent_period(bits)
    certified = stream_period(constant, steps)
    agreement: Optional[int] = None
    if apparent is not None:
        longer = stream_of(constant, 4 * steps)
        agreement = next(
            (i for i in range(len(longer) - apparent)
             if longer[i] != longer[i + apparent]),
            None)
    return {
        "name": constant.name,
        "steps": steps,
        "apparent_period": apparent,
        "certified_period": certified,
        "true_period": target.denominator,
        "first_disagreement": agreement,
        "apparent_is_a_period": apparent is not None and agreement is None,
    }


# ═════════════════════════════════════════════════════════════════════════
# 5.  PHASE 3 -- THE 24-DIMENSIONAL HULL CENSUS
# ═════════════════════════════════════════════════════════════════════════
#
# The study projects a scalar ``c`` to ``v_i = 4c/(i+1)`` and asks whether the
# result lies in the convex hull ``K`` of the 196,560 Leech minimal vectors.
# It answers by running a linear program over a *sample* of 150 of them.  A
# sample can only ever prove ``inside``: a convex combination over a subset is
# a convex combination over the whole set, but the infeasibility of the
# sampled program says nothing about the full one.  Every "outside" verdict in
# the study is therefore unestablished by its own method.
#
# Both verdicts are certificates here, and each is checked against all
# 196,560 vectors rather than a sample of them.

#: The scale the study's projection carries: ``v_i = c / (i + 1) * 4``.
PROJECTION_SCALE = 4

#: The largest ``l1`` norm the shape-``(+-4^2, 0^22)`` certificate covers, and
#: the largest ``l-infinity`` norm.  See :func:`inside_certificate`.
INSIDE_L1_BOUND = 8
INSIDE_LINF_BOUND = 4

#: Directions used to look for a separating functional.  Each is an integer
#: vector; only its direction matters, so the scale is chosen to keep the
#: entries small.
#:
#: ``target`` is the study's own proposal -- separate ``x`` from the hull with
#: ``d = x`` -- written for the projection direction, whose ``i``-th entry is
#: proportional to ``1/(i+1)``.  ``tuned`` is a direction found by descent on
#: ``support(u) / <u, projection(1)>``, the scale above which ``u`` separates:
#: it pushes that threshold from 0.9351 down to 0.8012, which is what brings
#: Champernowne's constant inside the reach of a certificate.
_LCM_24 = 5354228880
SEPARATING_DIRECTIONS: Dict[str, Tuple[int, ...]] = {
    "target": tuple(_LCM_24 // k for k in range(1, 25)),
    "tuned": (110, 38, 38, 35, 26, 24, 26, 23, 21, 19, 18, 24,
              17, 15, 18, 16, 14, 17, 18, 13, 15, 15, 16, 15),
}


def projection(value: Fraction) -> Tuple[Fraction, ...]:
    """The study's 24-dimensional projection of a scalar constant."""
    return tuple(Fraction(PROJECTION_SCALE) * Fraction(value) / (i + 1)
                 for i in range(24))


def projection_norm2(value: Fraction) -> Fraction:
    """``|v|**2`` of that projection, exactly."""
    return sum((x * x for x in projection(value)), Fraction(0))


def projection_l1(value: Fraction) -> Fraction:
    """``sum |v_i|`` of that projection, exactly."""
    return sum((abs(x) for x in projection(value)), Fraction(0))


def projection_linf(value: Fraction) -> Fraction:
    """``max |v_i|`` of that projection, exactly."""
    return max(abs(x) for x in projection(value))


_SUPPORT_CACHE: Dict[Tuple[int, ...], int] = {}


def support(direction: Sequence[int]) -> int:
    """``max_p <direction, p>`` over all 196,560 Leech minimal vectors.

    Integer arithmetic on integer data, and cached, because the enumeration
    is the expensive part of the census and the answer never changes.
    """
    key = tuple(int(component) for component in direction)
    if len(key) != 24:
        raise ValueError("support: a direction has 24 components")
    cached = _SUPPORT_CACHE.get(key)
    if cached is not None:
        return cached
    best: Optional[int] = None
    for point in leech2.minimal_vectors():
        total = 0
        for index, component in enumerate(key):
            if component:
                total += component * point[index]
        if best is None or total > best:
            best = total
    assert best is not None
    _SUPPORT_CACHE[key] = best
    return best


def separating_scale(name: str) -> Fraction:
    """The scale above which ``SEPARATING_DIRECTIONS[name]`` separates.

    For a target ``c * projection(1)`` the certificate ``<u, x> > support(u)``
    reads ``c * <u, projection(1)> > support(u)``, so it fires exactly above
    ``support(u) / <u, projection(1)>``.  Both sides are exact rationals.
    """
    direction = SEPARATING_DIRECTIONS[name]
    unit = projection(Fraction(1))
    pairing = sum((Fraction(direction[i]) * unit[i] for i in range(24)),
                  Fraction(0))
    if pairing <= 0:
        raise ValueError(f"separating_scale: direction {name!r} does not "
                         f"pair positively with the projection")
    return Fraction(support(direction)) / pairing


def unit_support() -> Fraction:
    """``max_p <d, p>`` for the unit direction ``d = projection(1)``.

    The study's own separating functional, in the study's own scale.  It is
    exactly 24: the maximum of ``sum_i 4 p_i / (i + 1)`` over the minimal
    vectors is attained at ``p = (4, 4, 0, ..., 0)``.
    """
    return (Fraction(support(SEPARATING_DIRECTIONS["target"]))
            * PROJECTION_SCALE / _LCM_24)


def inside_certificate(value: Fraction) -> bool:
    """Whether the cross-polytope certificate places the projection inside.

    The 1,104 minimal vectors of shape ``(+-4, +-4, 0^22)`` are exactly the
    extreme points of ``B = {x : |x|_1 <= 8, |x|_inf <= 4}``: an extreme point
    of an ``l1`` ball of radius 8 intersected with an ``l-infinity`` ball of
    radius 4 has ``floor(8/4) = 2`` coordinates at ``+-4`` and the rest zero.
    So ``B`` is contained in the hull, and membership of ``B`` is a
    certificate of membership of the hull -- two exact comparisons, no
    enumeration.
    """
    return (projection_l1(value) <= INSIDE_L1_BOUND
            and projection_linf(value) <= INSIDE_LINF_BOUND)


def outside_certificate(value: Fraction) -> Optional[str]:
    """The name of a direction that separates the projection, or ``None``.

    ``u`` separates when ``<u, x> > max_p <u, p>``: every convex combination
    ``sum lambda_p p`` then has ``<u, sum lambda_p p> <= max_p <u, p> <
    <u, x>``, so no convex combination equals ``x``.  The maximum is over all
    196,560 minimal vectors, so the certificate is complete.
    """
    x = projection(value)
    for name, direction in SEPARATING_DIRECTIONS.items():
        pairing = sum((Fraction(direction[i]) * x[i] for i in range(24)),
                      Fraction(0))
        if pairing > support(direction):
            return name
    return None


@memo
def critical_scales() -> Dict[str, Fraction]:
    """The two scales at which the certificates change their answer.

    Every target here is a positive multiple ``c`` of one direction, so both
    tests reduce to a comparison on ``c``:

    * at or below ``inside_at_most`` the shape-``(+-4^2)`` cross-polytope
      contains the target;
    * above ``outside_above`` one of the tuned functionals separates it.

    Between the two, neither certificate decides, and the census says so.
    """
    unit_l1 = projection_l1(Fraction(1))
    unit_linf = projection_linf(Fraction(1))
    scales = {name: separating_scale(name) for name in SEPARATING_DIRECTIONS}
    return {
        "outside_above": min(scales.values()),
        "inside_at_most": min(Fraction(INSIDE_L1_BOUND) / unit_l1,
                              Fraction(INSIDE_LINF_BOUND) / unit_linf),
        "unit_norm2": projection_norm2(Fraction(1)),
        "unit_l1": unit_l1,
        "unit_linf": unit_linf,
        "unit_support": unit_support(),
        "separating_scales": scales,
    }


def hull_status(value: Fraction) -> Dict[str, object]:
    """Decide, with a certificate, where the projection sits.

    ``inside``
        :func:`inside_certificate` fires.
    ``outside``
        :func:`outside_certificate` returns a direction.
    ``undetermined``
        neither fired.  Nothing is claimed, which is the honest answer for a
        target in the band the two certificates leave open.
    """
    value = Fraction(value)
    if value < 0:
        raise ValueError("hull_status: the study projects positive constants")
    inside = inside_certificate(value)
    separator = outside_certificate(value)
    if inside and separator is not None:              # pragma: no cover
        raise AssertionError("hull_status: contradictory certificates")
    if inside:
        status = "inside"
        certificate = "cross-polytope: |x|_1 <= 8, |x|_inf <= 4"
    elif separator is not None:
        status = "outside"
        certificate = f"separating functional: the {separator} direction"
    else:
        status, certificate = "undetermined", "neither certificate fires"
    return {
        "value": value,
        "norm2": projection_norm2(value),
        "l1": projection_l1(value),
        "linf": projection_linf(value),
        "support": value * unit_support(),
        "separator": separator,
        "status": status,
        "certificate": certificate,
    }


@memo
def hull_table() -> Tuple[Dict[str, object], ...]:
    """Phase 3 for all eight constants."""
    rows: List[Dict[str, object]] = []
    for constant in CONSTANTS:
        row = hull_status(constant.reference())
        row["name"] = constant.name
        row["kind"] = constant.kind
        rows.append(row)
    return tuple(rows)


def implied_value(norm: Fraction) -> Fraction:
    """The scalar whose projection has the stated 24-dimensional norm.

    The study tabulates a norm for every constant but a value for only some,
    so this inverts the projection: ``|projection(c)| = c * |projection(1)|``,
    hence ``c = norm / |projection(1)|``.  Used to read the study's own
    Omega-surrogate row, whose generator seed it never states.
    """
    unit_norm2 = projection_norm2(Fraction(1))
    return xr.rational_sqrt_approx(Fraction(norm) ** 2 / unit_norm2, 64)


# ═════════════════════════════════════════════════════════════════════════
# 6.  THE REPORT
# ═════════════════════════════════════════════════════════════════════════

def containers_report(steps: int = wb.WOBBLE_STEPS) -> Dict[str, object]:
    """The whole three-phase study, recomputed on the call."""
    convergence = convergence_table()
    wobble = wobble_table(steps)
    autocorrelation = autocorrelation_table(steps=steps)
    hull = hull_table()
    scales = critical_scales()
    decided = sum(1 for row in hull if row["status"] != "undetermined")
    return {
        "constants": tuple(c.name for c in CONSTANTS),
        "convergence": convergence,
        "wobble": wobble,
        "autocorrelation": autocorrelation,
        "rigid_period": stream_period(constant_by_name("1/3")),
        "hull": hull,
        "critical_scales": scales,
        "hull_decided": decided,
        "hull_inside": tuple(row["name"] for row in hull
                             if row["status"] == "inside"),
        "hull_outside": tuple(row["name"] for row in hull
                              if row["status"] == "outside"),
        "hull_undetermined": tuple(row["name"] for row in hull
                                   if row["status"] == "undetermined"),
        "laws_hold": all(row["laws_hold"] for row in wobble),
        "steps": steps,
    }
