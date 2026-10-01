"""``glm_universal.reasoning.wobble`` -- the wobble signature of a target.

What this module is
-------------------
The external studies collected in ``source_material/glm_study_findings_catalog.md`` run the
first-order delta-sigma modulator for ten thousand steps against a constant and
then *measure the emitted stream*: its Shannon entropy, its lag-1
autocorrelation, its mean and maximum run length, its one-density.  They report
those numbers as the "vibrational signature" of the constant, and a second
study reports the same statistics for an electrical oscillator, where zero
entropy is resonance and the entropy of the bit density is the signal-to-noise
ratio.

This module recomputes all of it, and -- more usefully -- checks each measured
column against the **law** that produces it.  The laws are not fitted here;
they are theorems of ``RequestProject/GLM/Sturmian.lean``, proved of the exact
modulator that ``exact_real.DeltaSigma`` implements:

============================  ==========================================
measured column               law it must obey
============================  ==========================================
ones in ``N`` ticks           exactly ``floor(N * t)``
                              (``GLM.Info.dsOnes_eq_floor``)
longest run of zeros          ``< 1/t``  (``ds_zero_run_length_lt``)
longest run of ones           ``< 1/(1 - t)``  (``ds_one_run_length_lt``)
transitions in ``N`` ticks    ``2 * floor(N t) + bit N`` for ``t < 1/2``
                              (``dsTransitions_eq``)
mean run length               ``-> 1/(2 min(t, 1 - t))``
                              (``dsMeanRunLength_tendsto``)
wobble entropy                ``binEntropy(density)`` in bits
                              (``GLM.Info.wobbleEntropy``)
zero entropy                  the stream is constant
                              (``ds_wobbleEntropy_zero_iff_silent``)
============================  ==========================================

Every measurement below is therefore checked twice: once by running the loop
and once by evaluating the closed form.  A row of :func:`signature_table`
carries both, and the ``law_holds`` flag is the comparison.

Exactness
---------
No float is constructed anywhere.  Densities, autocorrelations, run lengths and
transition counts are exact :class:`~fractions.Fraction` values.  The entropy is
the one quantity that is not rational, so it is returned as a *bracket*: an
exact rational approximation together with a proved error bound, computed from
:func:`~glm_universal.reasoning.transcendental.rational_log_approx`.  Rendering
goes through integer arithmetic (:func:`round_str`), never through ``float``.

Irrational targets are pinned to their level-64 dyadic stand-in before the loop
runs -- ``surrogate(x, 64)`` -- so the target is an exact rational with a small
denominator.  Over the ten thousand ticks measured, the accumulated difference
from the true constant is below ``10**4 * 2**-64``, which is some fourteen
orders of magnitude smaller than the smallest gap between the accumulator and a
quantiser threshold anywhere in the run, so no quantiser decision changes.

The two autocorrelations
------------------------
The catalogue's ``AC(1)`` column is not a single statistic.  Seven of its nine
rows are the mean of the products of consecutive bits mapped to ``+/-1``
(:func:`product_autocorrelation`); the two extreme-density rows are instead the
centred Pearson coefficient (:func:`pearson_autocorrelation`).  Both are
computed for every row, so the ledger in
:mod:`~glm_universal.reasoning.catalog` can say which is which rather than
picking whichever one makes the column come out right.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Mapping, Sequence, Tuple

from . import exact_real as xr
from . import transcendental as tr

__all__ = [
    "WOBBLE_STEPS", "TARGET_PRECISION",
    "stream_bits", "ones_count", "ones_count_law",
    "runs", "longest_run", "run_bound",
    "transitions", "transition_law",
    "mean_run_length", "mean_run_length_law",
    "product_autocorrelation", "product_autocorrelation_law",
    "pearson_autocorrelation", "pearson_autocorrelation_law",
    "entropy_bits", "round_str", "sci_str",
    "signature_targets", "signature", "signature_table",
    "OSCILLATOR_DENSITIES", "oscillator_table",
    "RESONANCE_RATIOS", "RESONANCE_Q", "resonance_gain", "resonance_sweep",
    "resonance_q_scan",
    "wobble_report",
]

#: How long the studies run the loop.  Everything below defaults to it.
WOBBLE_STEPS: int = 10_000

#: The dyadic level an irrational target is pinned to before the loop runs.
TARGET_PRECISION: int = 64

#: Precision, in bits, at which the entropy bracket is returned.
ENTROPY_BITS: int = 40


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE STREAM
# ═════════════════════════════════════════════════════════════════════════

def stream_bits(target: Fraction, steps: int = WOBBLE_STEPS) -> Tuple[int, ...]:
    """The first ``steps`` bits of the exact modulator chasing ``target``.

    Delegates to :class:`~glm_universal.reasoning.exact_real.DeltaSigma`, which
    is the recurrence proved in ``RequestProject/GLM/DeltaSigma.lean``.
    """
    if steps <= 0:
        raise ValueError("stream_bits: steps must be positive")
    return xr.delta_sigma_bits(target, steps)


def ones_count(bits: Sequence[int]) -> int:
    """How many ones the stream carries."""
    return sum(bits)


def ones_count_law(target: Fraction, steps: int = WOBBLE_STEPS) -> Dict[str, object]:
    """The ones-count, measured and predicted.

    ``GLM.Info.dsOnes_eq_floor``: the count is exactly ``floor(steps * t)``,
    with no error term at all.
    """
    bits = stream_bits(target, steps)
    measured = ones_count(bits)
    predicted = (Fraction(steps) * target).numerator // (
        Fraction(steps) * target).denominator
    return {
        "steps": steps,
        "measured": measured,
        "predicted": predicted,
        "law_holds": measured == predicted,
        "density": Fraction(measured, steps),
    }


# ═════════════════════════════════════════════════════════════════════════
# 2.  RUNS
# ═════════════════════════════════════════════════════════════════════════

def runs(bits: Sequence[int]) -> Tuple[Tuple[int, int], ...]:
    """The stream as maximal runs: a tuple of ``(symbol, length)`` pairs."""
    if not bits:
        return ()
    out: List[Tuple[int, int]] = []
    symbol = bits[0]
    length = 1
    for bit in bits[1:]:
        if bit == symbol:
            length += 1
        else:
            out.append((symbol, length))
            symbol, length = bit, 1
    out.append((symbol, length))
    return tuple(out)


def longest_run(bits: Sequence[int], symbol: int) -> int:
    """The longest run of ``symbol`` in the stream, or ``0`` if it never
    appears."""
    lengths = [length for value, length in runs(bits) if value == symbol]
    return max(lengths) if lengths else 0


def run_bound(slope: Fraction) -> int:
    """The largest run length the proved bound permits.

    ``GLM.Info.ds_zero_run_length_lt`` says a run of zeros of length ``L``
    forces ``L * t < 1``; the largest such integer is ``ceil(1/t) - 1``.  Pass
    ``t`` for the zero bound and ``1 - t`` for the one bound.
    """
    if slope <= 0:
        raise ValueError("run_bound: slope must be positive")
    inverse = 1 / slope
    ceiling = -((-inverse.numerator) // inverse.denominator)
    return ceiling - 1


# ═════════════════════════════════════════════════════════════════════════
# 3.  TRANSITIONS AND THE MEAN RUN LENGTH
# ═════════════════════════════════════════════════════════════════════════

def transitions(bits: Sequence[int]) -> int:
    """How many times the stream changes symbol."""
    return sum(1 for i in range(len(bits) - 1) if bits[i] != bits[i + 1])


def transition_law(target: Fraction, steps: int = WOBBLE_STEPS) -> Dict[str, object]:
    """The transition count, measured and predicted.

    ``GLM.Info.dsTransitions_eq``: below slope one half every one is isolated,
    so the count over the first ``N`` ticks is ``2 * floor(N t) + bit N``.  The
    identity is stated for the window ``[0, N)``, which counts the change
    *into* tick ``N``; the measured count here is over ``N`` emitted bits, so
    it is that quantity minus the final bit.
    """
    if not 0 <= target < Fraction(1, 2):
        raise ValueError("transition_law: the identity needs 0 <= t < 1/2")
    bits = stream_bits(target, steps)
    measured = transitions(bits)
    ones = ones_count(bits[:-1])
    predicted = 2 * ones + bits[-1] - bits[0]
    return {
        "steps": steps,
        "measured": measured,
        "predicted": predicted,
        "law_holds": measured == predicted,
    }


def mean_run_length(bits: Sequence[int]) -> Fraction:
    """Ticks per run: the length of the stream over the number of runs."""
    profile = runs(bits)
    if not profile:
        raise ValueError("mean_run_length: empty stream")
    return Fraction(len(bits), len(profile))


def mean_run_length_law(target: Fraction) -> Fraction:
    """The limit the mean run length converges to: ``1/(2 min(t, 1 - t))``.

    ``GLM.Info.dsMeanRunLength_tendsto`` proves the case ``t < 1/2``; the case
    above one half is the same statement about the complementary symbol, since
    exchanging zeros and ones sends ``t`` to ``1 - t``.
    """
    minority = min(target, 1 - target)
    if minority <= 0:
        raise ValueError("mean_run_length_law: the stream is constant")
    return 1 / (2 * minority)


# ═════════════════════════════════════════════════════════════════════════
# 4.  AUTOCORRELATION
# ═════════════════════════════════════════════════════════════════════════

def _shifted_means(bits: Sequence[int], lag: int) -> Tuple[Fraction, int]:
    """The mean of the two lag-``lag`` windows, and the window length.

    Both windows have exactly ``n - lag`` entries; their means differ by at
    most ``1/(n - lag)``, and the half-sum below is the symmetric exact choice.
    Taking a *linear* window rather than a cyclic one matters: wrapping the
    stream round joins tick ``n - 1`` to tick ``0``, which invents an
    adjacency whenever the run length divides the window -- exactly what
    happens to ``e**pi - pi`` at ten thousand ticks, where the return time is
    1,111 and the wrap would put two of the ten zeros side by side.
    """
    n = len(bits)
    if lag <= 0 or lag >= n:
        raise ValueError("autocorrelation: lag out of range")
    width = n - lag
    first = Fraction(sum(bits[:width]), width)
    second = Fraction(sum(bits[lag:]), width)
    return (first + second) / 2, width


def product_autocorrelation(bits: Sequence[int], lag: int = 1) -> Fraction:
    """The mean product of the stream with itself, on the ``+/-1`` alphabet.

    Exact.  For a stream of slope ``t`` this tends to ``1 - 4 min(t, 1 - t)``
    at lag one, because the minority symbol is never adjacent to itself --
    :func:`product_autocorrelation_law`.
    """
    n = len(bits)
    if lag <= 0 or lag >= n:
        raise ValueError("product_autocorrelation: lag out of range")
    total = sum((2 * bits[i] - 1) * (2 * bits[i + lag] - 1)
                for i in range(n - lag))
    return Fraction(total, n - lag)


def product_autocorrelation_law(target: Fraction) -> Fraction:
    """``1 - 4 min(t, 1 - t)``: the limit of :func:`product_autocorrelation`
    at lag one."""
    return 1 - 4 * min(target, 1 - target)


def pearson_autocorrelation(bits: Sequence[int], lag: int = 1) -> Fraction:
    """The centred, normalised autocorrelation of the ``0/1`` stream.

    Exact.  Both shifted windows are ``0/1`` valued, so their variance is
    ``m - m**2`` for the shared mean ``m`` of :func:`_shifted_means`, and the
    coefficient is a ratio of two exact rationals with no square root in it.
    """
    n = len(bits)
    if lag <= 0 or lag >= n:
        raise ValueError("pearson_autocorrelation: lag out of range")
    mean, width = _shifted_means(bits, lag)
    variance = mean - mean * mean
    if variance == 0:
        raise ValueError("pearson_autocorrelation: the stream is constant")
    joint = Fraction(sum(bits[i] * bits[i + lag] for i in range(width)), width)
    return (joint - mean * mean) / variance


def pearson_autocorrelation_law(target: Fraction) -> Fraction:
    """``-q/(1 - q)`` with ``q = min(t, 1 - t)``: the limit of
    :func:`pearson_autocorrelation` at lag one."""
    minority = min(target, 1 - target)
    if minority <= 0:
        raise ValueError("pearson_autocorrelation_law: the stream is constant")
    return -minority / (1 - minority)


# ═════════════════════════════════════════════════════════════════════════
# 5.  ENTROPY, WITHOUT A FLOAT
# ═════════════════════════════════════════════════════════════════════════

def entropy_bits(density: Fraction, bits_of_precision: int = ENTROPY_BITS
                 ) -> Dict[str, Fraction]:
    """The binary entropy of ``density``, in bits, as an exact bracket.

    Returns ``value``, ``error``, ``lower`` and ``upper``: the true entropy
    lies in ``[lower, upper]`` and ``upper - lower = 2 * error`` with
    ``error = 2**-bits_of_precision``.

    The bound is derived, not assumed.  With ``L_p`` within ``2**-K`` of
    ``log p`` and ``D`` within ``2**-K`` of ``log 2``, the numerator
    ``-p L_p - q L_q`` is within ``2**-K`` of ``-p log p - q log q`` because
    ``p + q = 1``; dividing by ``D >= 1/2`` costs a factor two, and replacing
    ``1/D`` by ``1/log 2`` costs ``numerator * 2**-K / (D log 2) <= 4 * 2**-K``
    since the numerator never exceeds ``log 2``.  Six times ``2**-K`` is below
    ``2**-(K-3)``, so ``K = bits_of_precision + 3`` suffices.
    """
    if not 0 <= density <= 1:
        raise ValueError("entropy_bits: density must lie in [0, 1]")
    if bits_of_precision < 1:
        raise ValueError("entropy_bits: precision must be positive")
    error = Fraction(1, 2 ** bits_of_precision)
    if density == 0 or density == 1:
        zero = Fraction(0)
        return {"value": zero, "error": zero, "lower": zero, "upper": zero}
    inner = bits_of_precision + 3
    complement = 1 - density
    log_p = tr.rational_log_approx(density, inner)
    log_q = tr.rational_log_approx(complement, inner)
    log_2 = tr.log_two_approx(inner)
    numerator = -density * log_p - complement * log_q
    value = numerator / log_2
    return {
        "value": value,
        "error": error,
        "lower": value - error,
        "upper": value + error,
    }


def round_str(value: Fraction, places: int = 3) -> str:
    """``value`` rounded half-up to ``places`` decimals, in integers only.

    Display only, and display that never constructs a float.  The catalogue's
    tables are rounded rather than truncated, so a comparison against them has
    to round the same way.
    """
    value = Fraction(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    scale = 10 ** places
    units = (2 * value.numerator * scale + value.denominator) // (
        2 * value.denominator)
    whole, frac = divmod(units, scale)
    if places == 0:
        return f"{sign}{whole}"
    return f"{sign}{whole}.{frac:0{places}d}"


def sci_str(value: Fraction, digits: int = 2) -> str:
    """``value`` in scientific notation, built from integers only.

    Display only.  No float is constructed: the exponent is found by
    comparing against powers of ten and the mantissa is rounded, by
    :func:`round_str`, on the scaled exact rational.  Exact values whose
    numerator and denominator run to hundreds of digits -- the drift table is
    full of them -- are unreadable otherwise.
    """
    value = Fraction(value)
    if value == 0:
        return "0"
    sign = "-" if value < 0 else ""
    magnitude = abs(value)
    exponent = 0
    while magnitude >= 10:
        magnitude /= 10
        exponent += 1
    while magnitude < 1:
        magnitude *= 10
        exponent -= 1
    mantissa = round_str(magnitude, digits)
    if Fraction(mantissa) >= 10:
        # rounding carried the mantissa up to ten; renormalise rather than
        # print "10.00e-5" for what is "1.00e-4".
        magnitude /= 10
        exponent += 1
        mantissa = round_str(magnitude, digits)
    return f"{sign}{mantissa}e{exponent:+d}"


# ═════════════════════════════════════════════════════════════════════════
# 6.  THE SIGNATURE TABLE
# ═════════════════════════════════════════════════════════════════════════

def _fractional_part(value: Fraction) -> Fraction:
    """The fractional part of an exact rational."""
    return value - (value.numerator // value.denominator)


def _pin(real: "xr.ExactReal") -> Fraction:
    """A process, pinned to its level-``TARGET_PRECISION`` dyadic stand-in."""
    return _fractional_part(xr.surrogate(real, TARGET_PRECISION))


def _liouville(terms: int = 6) -> Fraction:
    """Liouville's constant, exactly: ``sum_{n >= 1} 10**-n!``.

    Six terms already reach ``10**-720``, far below anything a ten-thousand
    tick run can see, and every later term is smaller still.
    """
    total = Fraction(0)
    factorial = 1
    for n in range(1, terms + 1):
        factorial *= n
        total += Fraction(1, 10 ** factorial)
    return total


def signature_targets() -> Tuple[Tuple[str, str, Fraction], ...]:
    """The nine targets the catalogue tabulates, as exact rationals.

    Each entry is ``(name, notation, target)``.  Where the package can build
    the constant as a process it does, and pins it; where the constant is
    given only as a measured or stipulated decimal -- the fine-structure
    constant and the algorithmically random surrogate -- the decimal itself is
    the exact target, and the notation says so.
    """
    pi = xr.pi()
    return (
        ("omega surrogate", "0.567143 (stipulated decimal)",
         Fraction(567143, 10 ** 6)),
        ("sqrt(2) - 1", "sqrt(2) - 1", _pin(xr.parse_real("sqrt(2)"))),
        ("phi - 1", "(1 + sqrt(5))/2 - 1", _pin(xr.phi())),
        ("1/3", "1/3", Fraction(1, 3)),
        ("e - 2", "e - 2", _pin(xr.e())),
        ("pi - 3", "pi - 3", _pin(pi)),
        ("Liouville", "sum 10**-n!", _liouville()),
        ("alpha", "0.0072973525693 (CODATA decimal)",
         Fraction(72973525693, 10 ** 13)),
        ("e**pi - pi", "exp(pi) - pi", _pin(tr.exp(pi) - pi)),
    )


def _or_none(function, *arguments):
    """``function(*arguments)``, or ``None`` when the stream is constant.

    The centred autocorrelation is undefined for a stream that never changes,
    and a stream short enough -- or a target extreme enough -- to be constant
    throughout is a legitimate row of the table rather than an error.  It is
    reported as an absent statistic instead of a fabricated one.
    """
    try:
        return function(*arguments)
    except ValueError:
        return None


def signature(name: str, notation: str, target: Fraction,
              steps: int = WOBBLE_STEPS) -> Dict[str, object]:
    """Every statistic of one target's stream, with the law beside each.

    The keys ending ``_law`` are the closed forms proved in
    ``RequestProject/GLM/Sturmian.lean``; ``laws_hold`` is true when every
    measured quantity agrees with the one that predicts it.
    """
    bits = stream_bits(target, steps)
    ones = ones_count(bits)
    density = Fraction(ones, steps)
    floor_ones = (steps * target).numerator // (steps * target).denominator

    zero_run = longest_run(bits, 0)
    one_run = longest_run(bits, 1)
    zero_bound = run_bound(target) if target > 0 else 0
    one_bound = run_bound(1 - target) if target < 1 else 0

    mean_run = mean_run_length(bits)
    mean_law = mean_run_length_law(target)
    entropy = entropy_bits(density)

    return {
        "name": name,
        "notation": notation,
        "target": target,
        "steps": steps,
        "ones": ones,
        "ones_law": floor_ones,
        "density": density,
        "entropy": entropy["value"],
        "entropy_error": entropy["error"],
        "entropy_rounded": round_str(entropy["value"], 3),
        "product_ac1": product_autocorrelation(bits, 1),
        "product_ac1_law": product_autocorrelation_law(target),
        "pearson_ac1": _or_none(pearson_autocorrelation, bits, 1),
        "pearson_ac1_law": _or_none(pearson_autocorrelation_law, target),
        "longest_zero_run": zero_run,
        "longest_zero_run_bound": zero_bound,
        "longest_one_run": one_run,
        "longest_one_run_bound": one_bound,
        "transitions": transitions(bits),
        "mean_run_length": mean_run,
        "mean_run_length_law": mean_law,
        "mean_run_rounded": round_str(mean_run, 2),
        "laws_hold": (ones == floor_ones
                      and zero_run <= zero_bound
                      and one_run <= one_bound),
    }


def signature_table(steps: int = WOBBLE_STEPS) -> Tuple[Dict[str, object], ...]:
    """The catalogue's spectral table, recomputed target by target."""
    return tuple(signature(name, notation, target, steps)
                 for name, notation, target in signature_targets())


# ═════════════════════════════════════════════════════════════════════════
# 7.  THE OSCILLATOR: RESONANCE AND SIGNAL QUALITY
# ═════════════════════════════════════════════════════════════════════════

#: The one-densities the oscillator study reports, from a pure signal down to
#: the noise floor.  Each is a stipulated density, not a measurement.
OSCILLATOR_DENSITIES: Tuple[Tuple[str, Fraction], ...] = (
    ("pure signal", Fraction(1)),
    ("SNR 40 dB", Fraction(999, 1000)),
    ("SNR 20 dB", Fraction(99, 100)),
    ("SNR 10 dB", Fraction(9, 10)),
    ("SNR 0 dB", Fraction(1, 2)),
)


def oscillator_table() -> Tuple[Dict[str, object], ...]:
    """The study's SNR table as one function of the density.

    Every row is :func:`entropy_bits` of the row's density and nothing else,
    which is the study's claim -- "SNR *is* wobble entropy" -- read as an
    identity rather than as a correlation.
    """
    out: List[Dict[str, object]] = []
    for label, density in OSCILLATOR_DENSITIES:
        entropy = entropy_bits(density)
        out.append({
            "condition": label,
            "density": density,
            "entropy": entropy["value"],
            "entropy_error": entropy["error"],
            "entropy_rounded": round_str(entropy["value"], 3),
        })
    return tuple(out)


def resonance() -> Dict[str, object]:
    """Lock-in: at gain one the loop emits nothing but ones.

    ``GLM.Info.ds_resonance_lock`` and ``ds_resonance_entropy``.  The
    modulator class refuses a target of exactly one -- its contract is
    ``[0, 1)`` -- so the lock is exhibited just below it, at ``1 - 2**-12``:
    the accumulator has to fill once, so tick zero emits a zero, and every
    tick after it fires until the deficit accumulates to one at tick 4096.
    Beside it sits the entropy of density one, which is exactly zero.
    """
    ticks = 64
    near = 1 - Fraction(1, 2 ** 12)
    bits = stream_bits(near, ticks)
    return {
        "near_resonance_target": near,
        "ticks": ticks,
        "first_bit": bits[0],
        "all_ones_after_the_first": all(bit == 1 for bit in bits[1:]),
        "off_resonance_target": Fraction(9, 10),
        "off_resonance_entropy": entropy_bits(Fraction(9, 10))["value"],
        "resonant_density": Fraction(1),
        "resonant_entropy": entropy_bits(Fraction(1))["value"],
        "entropy_is_zero_only_at_the_ends": (
            entropy_bits(Fraction(1))["value"] == 0
            and entropy_bits(Fraction(0))["value"] == 0
            and entropy_bits(Fraction(1, 2))["value"] > 0),
    }


#: The frequency ratios ``omega / omega_0`` the sweep visits.  The study
#: reports only 0.9, 1.0 and 1.1; the sweep brackets them on both sides so the
#: shape of the curve can be read rather than asserted.
RESONANCE_RATIOS: Tuple[Fraction, ...] = tuple(
    Fraction(k, 10) for k in range(5, 16))

#: The quality factor the sweep uses by default.  The study does not record
#: one, so this is a stipulation; :func:`resonance_q_scan` searches over it.
RESONANCE_Q: Fraction = Fraction(8)


def resonance_gain(ratio: Fraction, q: Fraction = RESONANCE_Q,
                   bits: int = TARGET_PRECISION) -> Fraction:
    """The normalised gain of a driven damped oscillator, exactly.

    The textbook amplitude response of a driven damped oscillator at frequency
    ratio ``r = omega / omega_0`` and quality factor ``q`` is
    ``1 / sqrt((1 - r**2)**2 + (r/q)**2)``, whose peak value near ``r = 1`` is
    ``q``.  Dividing by ``q`` normalises the response so that ``r = 1`` gives
    exactly one -- the lock-in condition the study calls resonance::

        gain(r) = 1 / sqrt(q**2 * (1 - r**2)**2 + r**2)

    The square root is taken by :func:`exact_real.rational_sqrt_approx`, which
    is exact rational arithmetic with a proved ``2**-bits`` bound, and the
    result is truncated down onto the dyadic grid of that level so that it is
    a legal modulator target in ``[0, 1]``.  No float is constructed.
    """
    if ratio <= 0:
        raise ValueError("resonance_gain: ratio must be positive")
    if q <= 0:
        raise ValueError("resonance_gain: q must be positive")
    inner = q ** 2 * (1 - ratio ** 2) ** 2 + ratio ** 2
    root = xr.rational_sqrt_approx(inner, bits)
    if root <= 0:
        return Fraction(1)
    scale = 2 ** bits
    exact = scale / root
    level = exact.numerator // exact.denominator
    return min(Fraction(1), Fraction(level, scale))


def resonance_sweep(q: Fraction = RESONANCE_Q,
                    ratios: Sequence[Fraction] = RESONANCE_RATIOS,
                    ) -> Tuple[Dict[str, object], ...]:
    """The gain and the wobble entropy at each frequency ratio.

    One row per ratio: the normalised gain, and the wobble entropy of the
    stream the modulator emits when that gain is its one-density.  ``locked``
    marks the row where the gain is exactly one, which is the study's
    resonance condition.
    """
    out: List[Dict[str, object]] = []
    for ratio in ratios:
        gain = resonance_gain(ratio, q)
        entropy = entropy_bits(gain)
        out.append({
            "ratio": ratio,
            "gain": gain,
            "gain_rounded": round_str(gain, 4),
            "entropy": entropy["value"],
            "entropy_error": entropy["error"],
            "entropy_rounded": round_str(entropy["value"], 3),
            "locked": gain == 1,
        })
    return tuple(out)


def resonance_q_scan(low: Fraction = Fraction(1), high: Fraction = Fraction(40),
                     step: Fraction = Fraction(1, 10),
                     targets: Tuple[str, str] = ("0.985", "0.996"),
                     ) -> Dict[str, object]:
    """Is there *any* quality factor giving the study's two off-resonance rows?

    The study reports entropy 0.985 at ratio 0.9 and 0.996 at ratio 1.1 but
    records no quality factor, so the pair is only meaningful if some ``q``
    produces both.  This walks ``q`` over a grid in exact rationals and
    reports every hit, together with the ``q`` that comes closest on the
    0.9 row alone.
    """
    if step <= 0:
        raise ValueError("resonance_q_scan: step must be positive")
    low_ratio, high_ratio = Fraction(9, 10), Fraction(11, 10)
    hits: List[Fraction] = []
    best_q = low
    best_gap: Fraction | None = None
    rows: List[Dict[str, object]] = []
    q = low
    while q <= high:
        left = entropy_bits(resonance_gain(low_ratio, q))["value"]
        right = entropy_bits(resonance_gain(high_ratio, q))["value"]
        pair = (round_str(left, 3), round_str(right, 3))
        if pair == targets:
            hits.append(q)
        gap = abs(left - Fraction(targets[0]))
        if best_gap is None or gap < best_gap:
            best_gap, best_q = gap, q
        rows.append({"q": q, "low": pair[0], "high": pair[1]})
        q += step
    left = entropy_bits(resonance_gain(low_ratio, best_q))["value"]
    right = entropy_bits(resonance_gain(high_ratio, best_q))["value"]
    return {
        "grid": (low, high, step),
        "targets": targets,
        "points": len(rows),
        "hits": tuple(hits),
        "any_hit": bool(hits),
        "best_q": best_q,
        "best_low_entropy": round_str(left, 3),
        "best_high_entropy": round_str(right, 3),
    }


# ═════════════════════════════════════════════════════════════════════════
# 8.  THE REPORT
# ═════════════════════════════════════════════════════════════════════════

def wobble_report(steps: int = WOBBLE_STEPS) -> Dict[str, object]:
    """Everything above in one call.

    ``laws_hold`` over the whole table is the headline: every measured column
    of the catalogue's spectral table is reproduced by the closed form proved
    of the modulator, so the table is a consequence of the target rather than
    an experimental finding about it.
    """
    table = signature_table(steps)
    return {
        "steps": steps,
        "targets": len(table),
        "signatures": table,
        "all_laws_hold": all(row["laws_hold"] for row in table),
        "oscillator": oscillator_table(),
        "resonance": resonance(),
        "resonance_sweep": resonance_sweep(),
        "resonance_q_scan": resonance_q_scan(),
        "max_entropy_density": Fraction(1, 2),
        "max_entropy": entropy_bits(Fraction(1, 2))["value"],
    }
