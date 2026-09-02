"""``glm_universal.reasoning.noise_lab`` -- noise as a computation, measured.

What this module is for
-----------------------
``source_material/DYNAMIC_CARRIER_STUDY.md`` and :mod:`glm_universal.reasoning.exact_real` use
the delta-sigma loop to *represent* a value: a target in ``[0, 1)`` is chased by
a one-bit quantiser and the time average of the bits converges to it at rate
``1/N``.  The to-do list asks for the next thing -- to stop treating the wobble
as a representation and start using it as the computation: cascaded loops,
error feedback, dither, and interacting tones whose frequencies and amplitudes
are the input.

This module is that laboratory.  Five experiments, each of which recomputes
itself and each of which is checked against a theorem rather than against an
expectation:

1. **A loop that chases a signal.**  Everything previously proved about the
   modulator was stated for a *constant* target.  :func:`run_signal` drives the
   same quantiser with a periodic exact-rational signal -- one tone, or several
   added together -- and measures that the emitted bits still track the input's
   running mean to within ``1/N``.  The theorem is
   ``GLM.Info.mAverage_error_le``.

2. **When the wobble closes its orbit.**  A periodic input whose sum over one
   period is an *integer* returns the accumulator to zero at the end of every
   period, so the trajectory is exactly periodic and the "noise" is a closed
   orbit; when the period sum is not an integer the orbit never closes.
   :func:`orbit_closure` measures both cases.  The theorem is
   ``GLM.Info.mState_periodic``.

3. **What a second loop buys.**  :func:`cascade_run` builds the MASH 1-1
   cascade -- stage two modulates stage one's error, and the outputs recombine
   as ``y n = b₁ n + b₂ (n+1) − b₂ n`` -- and checks, tick by tick, the
   identity that makes cascading worth anything:
   ``t − y n = Δ² s₂ n``.  Because the error is a *second* difference, reading
   the output through a triangular window converges as ``O(1/M²)`` where a
   single loop is stuck at ``O(1/M)``.  :func:`convergence_table` measures both
   against their proved bounds.  The theorems are ``GLM.Info.casOut_error``,
   ``GLM.Info.casDouble_sum``, ``GLM.Info.casTriangular_error_lt`` and
   ``GLM.Info.firstOrder_triangular_error_ge``.

4. **Idle tones, and what dither costs.**  A rational target makes the loop
   periodic, and a periodic bit stream is a line in the spectrum -- an idle
   tone.  :func:`tone_strength` measures it exactly, by Walsh-Hadamard
   transforming the ±1 output over a power-of-two window (the transform is the
   package's own exact :func:`~glm_universal.reasoning.fwht.fwht`).
   :func:`dither_experiment` then adds subtractive dither drawn from an
   equidistributed sequence and measures the trade: the tone drops, and the
   bias the dither introduces is stated exactly rather than assumed to vanish.

5. **Error feedback, and the symmetry it respects.**  Everything above
   quantises one number.  :func:`feedback_run` quantises a whole vector at
   once and feeds the past error back through a rational matrix ``A``.  With
   ``A`` the identity every coordinate tracks its own input to within
   ``1/(2N)``; with ``A`` a contraction the quantiser can stop firing
   altogether (:func:`dead_zone`); and when ``A`` is invariant under a
   permutation of the coordinates the whole trajectory is equivariant under
   it (:func:`equivariance_check`), which is what lets a loop be run on a
   carrier without breaking the carrier's symmetry.  The theorems are
   ``GLM.Feedback.efAverage_error_le_identity``,
   ``GLM.Feedback.halfFeedback_dead_zone`` and
   ``GLM.Feedback.efOut_equivariant``.

Exactness
---------
Every quantity here is an ``int`` or a :class:`fractions.Fraction`.  No float
is constructed anywhere, and no random number is drawn: "noise" throughout
means a deterministic trajectory whose statistics are computed, not sampled.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import gcd
from typing import Dict, List, Optional, Sequence, Tuple

from .fwht import fwht

__all__ = [
    "Signal",
    "constant_signal",
    "square_tone",
    "triangle_tone",
    "mix_tones",
    "ModulatorRun",
    "run_signal",
    "orbit_closure",
    "CascadeRun",
    "cascade_run",
    "first_order_triangular",
    "cascade_bound",
    "first_order_bound",
    "convergence_table",
    "walsh_spectrum",
    "tone_strength",
    "equidistributed",
    "dither_experiment",
    "DITHER_AMPLITUDES",
    "dither_sweep",
    "quantise",
    "identity_matrix",
    "scaled_matrix",
    "FeedbackRun",
    "feedback_run",
    "feedback_tracking",
    "equivariance_check",
    "dead_zone",
    "feedback_experiment",
    "noise_report",
]


# ===========================================================================
# 0.  EXACTNESS GUARD
# ===========================================================================

def _exact(value, where: str) -> Fraction:
    """Accept an ``int`` or a ``Fraction``; refuse anything approximate."""
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError(f"{where}: refusing an inexact value {value!r}")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    raise TypeError(f"{where}: expected int or Fraction, got {type(value)}")


def _lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)


# ===========================================================================
# 1.  SIGNALS
# ===========================================================================

@dataclass(frozen=True)
class Signal:
    """A periodic exact-rational signal, one period long.

    ``values`` holds one full period; ``at(n)`` reads it cyclically.  Keeping
    the period explicit is what makes every statistic below exact: the mean
    over a period is a rational with a known denominator, and the question of
    whether the period sum is an integer -- which decides whether the
    modulator's orbit closes -- is decided, not estimated.
    """

    name: str
    values: Tuple[Fraction, ...]

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("Signal: a signal needs at least one sample")
        for value in self.values:
            _exact(value, "Signal")

    @property
    def period(self) -> int:
        return len(self.values)

    def at(self, n: int) -> Fraction:
        return self.values[n % self.period]

    @property
    def period_sum(self) -> Fraction:
        return sum(self.values, Fraction(0))

    @property
    def mean(self) -> Fraction:
        """The exact mean over one period."""
        return self.period_sum / self.period

    @property
    def in_unit_interval(self) -> bool:
        """Whether every sample lies in ``[0, 1)``, as the loop requires."""
        return all(0 <= v < 1 for v in self.values)

    @property
    def closes_orbit(self) -> bool:
        """Whether the period sum is an integer.

        This is the exact condition under which the accumulator returns to
        zero at the end of every period (``GLM.Info.mState_periodic``).
        """
        return self.period_sum.denominator == 1


def constant_signal(target, name: str = "constant") -> Signal:
    """The constant signal: the classical delta-sigma target."""
    return Signal(name, (_exact(target, "constant_signal"),))


def square_tone(period: int, amplitude, offset=Fraction(1, 2),
                name: Optional[str] = None) -> Signal:
    """A square wave of the given period: ``offset ± amplitude``.

    The period must be even, so that the two halves are equal and the mean is
    exactly ``offset``.
    """
    if period < 2 or period % 2 != 0:
        raise ValueError("square_tone: period must be an even number >= 2")
    amp = _exact(amplitude, "square_tone")
    off = _exact(offset, "square_tone")
    half = period // 2
    values = tuple([off + amp] * half + [off - amp] * half)
    return Signal(name or f"square({period}, {amp})", values)


def triangle_tone(period: int, amplitude, offset=Fraction(1, 2),
                  name: Optional[str] = None) -> Signal:
    """A triangle wave of the given period, rising then falling.

    The period must be even.  The samples run over the ``period`` equally
    spaced points of one cycle, so the mean is exactly ``offset``.
    """
    if period < 2 or period % 2 != 0:
        raise ValueError("triangle_tone: period must be an even number >= 2")
    amp = _exact(amplitude, "triangle_tone")
    off = _exact(offset, "triangle_tone")
    half = period // 2
    rise = [off - amp + 2 * amp * Fraction(i, half) for i in range(half)]
    fall = [off + amp - 2 * amp * Fraction(i, half) for i in range(half)]
    return Signal(name or f"triangle({period}, {amp})", tuple(rise + fall))


def mix_tones(base, tones: Sequence[Signal],
              name: str = "mix") -> Signal:
    """Add several tones to a constant base, exactly.

    The mixed signal's period is the least common multiple of the periods it
    is built from -- the beat period -- and every sample is the exact sum.
    Each tone is taken as a deviation about zero, so a tone built by
    :func:`square_tone` should be given ``offset=0``.
    """
    if not tones:
        raise ValueError("mix_tones: nothing to mix")
    base_value = _exact(base, "mix_tones")
    period = 1
    for tone in tones:
        period = _lcm(period, tone.period)
    values = tuple(
        base_value + sum((tone.at(n) for tone in tones), Fraction(0))
        for n in range(period))
    return Signal(name, values)


# ===========================================================================
# 2.  THE LOOP, DRIVEN BY A SIGNAL
# ===========================================================================

@dataclass(frozen=True)
class ModulatorRun:
    """What one run of the signal-driven quantiser produced."""

    signal: str
    ticks: int
    bits: Tuple[int, ...]
    states: Tuple[Fraction, ...]
    input_mean: Fraction
    bit_mean: Fraction
    error: Fraction
    bound: Fraction
    within_bound: bool
    max_state: Fraction
    state_stayed_in_range: bool


def run_signal(signal: Signal, ticks: int) -> ModulatorRun:
    """Drive the one-bit quantiser with ``signal`` for ``ticks`` steps.

    The recurrence is the one proved in ``RequestProject/GLM/Cascade.lean``::

        state_0     = 0
        bit_n       = 1 if 1 <= state_n + u_n else 0
        state_(n+1) = state_n + u_n - bit_n

    with ``u`` the signal rather than a constant.  The measured claim is
    ``GLM.Info.mAverage_error_le``: the mean of the bits is within ``1/N`` of
    the mean of the inputs, whatever the signal does.
    """
    if ticks <= 0:
        raise ValueError("run_signal: ticks must be positive")
    if not signal.in_unit_interval:
        raise ValueError(
            f"run_signal: {signal.name} leaves [0, 1); the loop's bound is "
            f"stated for inputs in [0, 1)")
    state = Fraction(0)
    bits: List[int] = []
    states: List[Fraction] = [state]
    total_in = Fraction(0)
    for n in range(ticks):
        u = signal.at(n)
        total_in += u
        bit = 1 if state + u >= 1 else 0
        state = state + u - bit
        bits.append(bit)
        states.append(state)
    input_mean = total_in / ticks
    bit_mean = Fraction(sum(bits), ticks)
    error = abs(bit_mean - input_mean)
    bound = Fraction(1, ticks)
    return ModulatorRun(
        signal=signal.name, ticks=ticks, bits=tuple(bits),
        states=tuple(states), input_mean=input_mean, bit_mean=bit_mean,
        error=error, bound=bound, within_bound=error <= bound,
        max_state=max(states),
        state_stayed_in_range=all(0 <= s < 1 for s in states))


def orbit_closure(signal: Signal, periods: int = 4) -> Dict[str, object]:
    """Does the wobble close its orbit?

    Runs the loop for ``periods`` whole periods of the signal and reports
    whether the accumulator is back at zero at the end of each one, alongside
    the exact criterion ``signal.closes_orbit`` (the period sum is an integer)
    that ``GLM.Info.mState_periodic`` proves is sufficient.
    """
    if periods < 1:
        raise ValueError("orbit_closure: periods must be at least 1")
    run = run_signal(signal, signal.period * periods)
    at_period_ends = tuple(run.states[signal.period * k]
                           for k in range(1, periods + 1))
    closed = all(s == 0 for s in at_period_ends)
    repeats = all(
        run.bits[n] == run.bits[n % signal.period]
        for n in range(signal.period * periods))
    return {
        "signal": signal.name,
        "period": signal.period,
        "period_sum": signal.period_sum,
        "period_sum_is_integer": signal.closes_orbit,
        "state_at_period_ends": at_period_ends,
        "orbit_closed": closed,
        "bits_repeat_with_the_period": repeats,
        "criterion_agrees": closed == signal.closes_orbit,
    }


# ===========================================================================
# 3.  THE CASCADE
# ===========================================================================

@dataclass(frozen=True)
class CascadeRun:
    """One run of the MASH 1-1 cascade, with its identities checked."""

    target: Fraction
    ticks: int
    stage1_bits: Tuple[int, ...]
    stage2_bits: Tuple[int, ...]
    output: Tuple[int, ...]
    alphabet: Tuple[int, ...]
    second_difference_holds: bool
    double_sum: Fraction
    double_sum_equals_state: bool
    plain_error: Fraction
    triangular_error: Fraction
    triangular_bound: Fraction
    within_bound: bool


def cascade_run(target, ticks: int) -> CascadeRun:
    """Run the cascade: stage two modulates stage one's error.

    ``output[n] = b1[n] + b2[n+1] - b2[n]``, so one extra stage-two bit is
    computed beyond the window.  Two identities are checked here rather than
    assumed:

    * ``target - output[n] == s2[n+2] - 2*s2[n+1] + s2[n]`` at every tick
      (``GLM.Info.casOut_error``) -- the error is a second difference;
    * the doubly accumulated error equals ``s2[M]``
      (``GLM.Info.casDouble_sum``) -- so it is bounded by 1 for all time.
    """
    t = _exact(target, "cascade_run")
    if not 0 <= t < 1:
        raise ValueError("cascade_run: target must lie in [0, 1)")
    if ticks < 2:
        raise ValueError("cascade_run: ticks must be at least 2")

    # Stage one, and its error sequence.
    s1 = Fraction(0)
    err: List[Fraction] = []          # err[n] = s1[n], stage two's input
    b1: List[int] = []
    for _ in range(ticks + 3):
        err.append(s1)
        bit = 1 if s1 + t >= 1 else 0
        b1.append(bit)
        s1 = s1 + t - bit

    # Stage two, driven by stage one's error.
    s2_states: List[Fraction] = [Fraction(0)]
    b2: List[int] = []
    s2 = Fraction(0)
    for n in range(ticks + 3):
        u = err[n]
        bit = 1 if s2 + u >= 1 else 0
        b2.append(bit)
        s2 = s2 + u - bit
        s2_states.append(s2)

    output = tuple(b1[n] + b2[n + 1] - b2[n] for n in range(ticks))

    second_difference = all(
        t - output[n] == s2_states[n + 2] - 2 * s2_states[n + 1] + s2_states[n]
        for n in range(ticks))

    running = Fraction(0)
    double = Fraction(0)
    for n in range(ticks):
        double += running
        running += t - output[n]
    double_ok = double == s2_states[ticks]

    plain = abs(Fraction(sum(output), ticks) - t)
    triangular = abs(_triangular_average(output, ticks) - t)
    bound = cascade_bound(ticks)

    return CascadeRun(
        target=t, ticks=ticks, stage1_bits=tuple(b1[:ticks]),
        stage2_bits=tuple(b2[:ticks]), output=output,
        alphabet=tuple(sorted(set(output))),
        second_difference_holds=second_difference,
        double_sum=double, double_sum_equals_state=double_ok,
        plain_error=plain, triangular_error=triangular,
        triangular_bound=bound, within_bound=triangular < bound)


def _triangular_average(symbols: Sequence[int], window: int) -> Fraction:
    """The Bartlett-windowed average: weight ``i`` by ``window - 1 - i``."""
    if window < 2:
        raise ValueError("_triangular_average: window must be at least 2")
    total = sum(Fraction(window - 1 - i) * symbols[i] for i in range(window))
    return total / (Fraction(window * (window - 1), 2))


def first_order_triangular(target, ticks: int) -> Fraction:
    """The same window over a single first-order loop's bits."""
    t = _exact(target, "first_order_triangular")
    state = Fraction(0)
    bits: List[int] = []
    for _ in range(ticks):
        bit = 1 if state + t >= 1 else 0
        bits.append(bit)
        state = state + t - bit
    return _triangular_average(bits, ticks)


def cascade_bound(ticks: int) -> Fraction:
    """``2 / (M (M - 1))`` -- the proved cascade bound."""
    return Fraction(2, ticks * (ticks - 1))


def first_order_bound(ticks: int) -> Fraction:
    """``1 / (2M)`` -- the proved *lower* bound for a single loop on 1/2."""
    return Fraction(1, 2 * ticks)


def convergence_table(target=Fraction(1, 2),
                      windows: Sequence[int] = (8, 16, 32, 64, 128)
                      ) -> Tuple[Dict[str, object], ...]:
    """Measure both readings against their proved bounds, window by window.

    For each window ``M``: the triangular-window error of the cascade against
    ``2/(M(M-1))``, and the triangular-window error of a single first-order
    loop against ``1/(2M)``.  On the target ``1/2`` the second bound is a
    *lower* bound, which is the point: the single loop cannot reach the rate
    the cascade attains.
    """
    t = _exact(target, "convergence_table")
    rows: List[Dict[str, object]] = []
    for window in windows:
        run = cascade_run(t, window)
        single = abs(first_order_triangular(t, window) - t)
        rows.append({
            "window": window,
            "cascade_error": run.triangular_error,
            "cascade_bound": run.triangular_bound,
            "cascade_within_bound": run.within_bound,
            "single_loop_error": single,
            "single_loop_floor": first_order_bound(window),
            "single_loop_above_floor": (
                single >= first_order_bound(window) if t == Fraction(1, 2)
                else None),
            "ratio_single_to_cascade": (
                single / run.triangular_error
                if run.triangular_error != 0 else None),
        })
    return tuple(rows)


# ===========================================================================
# 4.  IDLE TONES AND DITHER
# ===========================================================================

def walsh_spectrum(bits: Sequence[int]) -> Tuple[int, ...]:
    """The exact Walsh-Hadamard spectrum of a bit stream read as ±1.

    The length must be a power of two.  The transform is the package's own
    exact :func:`~glm_universal.reasoning.fwht.fwht`, so every coefficient is
    an integer.
    """
    n = len(bits)
    if n == 0 or n & (n - 1) != 0:
        raise ValueError("walsh_spectrum: length must be a power of 2")
    signs = [2 * int(b) - 1 for b in bits]
    return tuple(int(c) for c in fwht(signs))


def tone_strength(bits: Sequence[int]) -> Dict[str, object]:
    """How concentrated a bit stream is on a single Walsh line.

    A periodic output -- an *idle tone* -- puts most of its energy on one
    coefficient.  The measure returned is the largest absolute coefficient
    away from DC, as an exact fraction of the window length, together with the
    index it sits on.  Larger means a stronger tone.
    """
    spectrum = walsh_spectrum(bits)
    n = len(spectrum)
    peak_index = max(range(1, n), key=lambda i: abs(spectrum[i]))
    peak = abs(spectrum[peak_index])
    return {
        "window": n,
        "dc": spectrum[0],
        "peak_index": peak_index,
        "peak": peak,
        "peak_fraction": Fraction(peak, n),
        "energy": sum(c * c for c in spectrum),
    }


def equidistributed(alpha, ticks: int) -> Tuple[Fraction, ...]:
    """The sequence ``frac(n * alpha)`` -- exact, and equidistributed.

    With ``alpha`` a rational of large denominator this is the standard
    low-discrepancy sequence used as dither.  Nothing random is involved: the
    sequence is a function of ``alpha``.
    """
    a = _exact(alpha, "equidistributed")
    out: List[Fraction] = []
    for n in range(ticks):
        value = a * n
        out.append(value - (value.numerator // value.denominator))
    return tuple(out)


#: The dither sequence's slope: a ratio of consecutive Fibonacci numbers, the
#: worst-approximable direction available at this denominator, so the dither
#: visits the interval as evenly as a rational can.
DITHER_ALPHA: Fraction = Fraction(4181, 6765)


def dither_experiment(target=Fraction(1, 2), ticks: int = 256,
                      amplitude=Fraction(1, 4),
                      alpha: Fraction = DITHER_ALPHA) -> Dict[str, object]:
    """Trade an idle tone for a stated bias.

    A rational target drives the loop into a cycle, and a cyclic bit stream is
    a line in the spectrum.  Adding subtractive dither -- here
    ``amplitude * (frac(n·alpha) - 1/2)``, an equidistributed deviation about
    zero -- breaks the cycle.  What it costs is a bias equal to ``amplitude``
    times the dither's own mean deviation, which is computed here exactly
    rather than assumed to be zero.
    """
    t = _exact(target, "dither_experiment")
    amp = _exact(amplitude, "dither_experiment")
    if ticks & (ticks - 1) != 0:
        raise ValueError("dither_experiment: ticks must be a power of 2")

    plain = run_signal(constant_signal(t, "constant"), ticks)
    plain_tone = tone_strength(plain.bits)

    dither = equidistributed(alpha, ticks)
    samples = tuple(t + amp * (d - Fraction(1, 2)) for d in dither)
    if not all(0 <= s < 1 for s in samples):
        raise ValueError("dither_experiment: the dithered signal leaves [0, 1)")
    dithered_signal = Signal(f"dithered({t}, {amp})", samples)
    dithered = run_signal(dithered_signal, ticks)
    dithered_tone = tone_strength(dithered.bits)

    dither_mean = sum(dither, Fraction(0)) / ticks
    bias = amp * (dither_mean - Fraction(1, 2))

    return {
        "target": t,
        "ticks": ticks,
        "amplitude": amp,
        "alpha": alpha,
        "plain_peak_fraction": plain_tone["peak_fraction"],
        "plain_peak_index": plain_tone["peak_index"],
        "dithered_peak_fraction": dithered_tone["peak_fraction"],
        "dithered_peak_index": dithered_tone["peak_index"],
        "tone_reduced": (dithered_tone["peak_fraction"]
                         < plain_tone["peak_fraction"]),
        "dither_mean": dither_mean,
        "bias": bias,
        "plain_error": plain.error,
        "dithered_error_against_target": abs(dithered.bit_mean - t),
        "dithered_error_against_input_mean": dithered.error,
        "dithered_within_1_over_N": dithered.within_bound,
    }


#: The amplitudes the dither sweep walks, smallest first.
DITHER_AMPLITUDES: Tuple[Fraction, ...] = (
    Fraction(1, 16), Fraction(1, 8), Fraction(1, 4), Fraction(1, 2),
    Fraction(3, 4), Fraction(9, 10))


def dither_sweep(target=Fraction(1, 2), ticks: int = 256,
                 amplitudes: Sequence[Fraction] = DITHER_AMPLITUDES
                 ) -> Dict[str, object]:
    """Turn the dither amplitude up, and measure what happens to the tone.

    This is the amplitude half of the experiment the to-do list asks for: the
    same target, the same equidistributed sequence, and nothing changing but
    how hard the dither is driven.  Each row records the exact Walsh peak of
    the dithered output and the exact bias the dither leaves behind, so the
    trade between the two is read off rather than argued.
    """
    rows: List[Dict[str, object]] = []
    plain = run_signal(constant_signal(_exact(target, "dither_sweep")), ticks)
    plain_tone = tone_strength(plain.bits)
    for amplitude in amplitudes:
        run = dither_experiment(target, ticks, amplitude)
        rows.append({
            "amplitude": amplitude,
            "peak_fraction": run["dithered_peak_fraction"],
            "bias": run["bias"],
            "error_against_target": run["dithered_error_against_target"],
            "tone_reduced": run["tone_reduced"],
        })
    reduced = [row for row in rows if row["tone_reduced"]]
    return {
        "target": _exact(target, "dither_sweep"),
        "ticks": ticks,
        "undithered_peak_fraction": plain_tone["peak_fraction"],
        "rows": tuple(rows),
        "amplitudes_that_reduce_the_tone": len(reduced),
        "amplitudes_tried": len(rows),
        "monotone_in_amplitude": all(
            rows[i]["peak_fraction"] >= rows[i + 1]["peak_fraction"]
            for i in range(len(rows) - 1)),
        "lowest_peak_fraction": min(row["peak_fraction"] for row in rows),
    }


# ===========================================================================
# 5.  ERROR FEEDBACK THROUGH A MATRIX, AND THE SYMMETRY IT RESPECTS
# ===========================================================================
#
# Everything above quantises one coordinate.  The to-do list asks for the
# vector case: several coordinates modulated at once, with the past
# quantisation error fed back through a rational matrix `A` chosen to commute
# with a symmetry of the carrier.  ``RequestProject/GLM/Feedback.lean`` proves
# the three statements measured here.


def quantise(value) -> int:
    """Nearest integer, ties resolved upward -- ``GLM.Feedback.quant``."""
    x = _exact(value, "quantise")
    return (x + Fraction(1, 2)).__floor__()


def identity_matrix(dim: int) -> Tuple[Tuple[Fraction, ...], ...]:
    """``GLM.Feedback.idMat``: the only feedback that tracks the input."""
    if dim <= 0:
        raise ValueError("identity_matrix: dim must be positive")
    return tuple(tuple(Fraction(1) if i == j else Fraction(0)
                       for j in range(dim)) for i in range(dim))


def scaled_matrix(dim: int, factor) -> Tuple[Tuple[Fraction, ...], ...]:
    """A multiple of the identity -- the contracting feedback of the dead zone."""
    a = _exact(factor, "scaled_matrix")
    if dim <= 0:
        raise ValueError("scaled_matrix: dim must be positive")
    return tuple(tuple(a if i == j else Fraction(0)
                       for j in range(dim)) for i in range(dim))


@dataclass(frozen=True)
class FeedbackRun:
    """What one run of the vector error-feedback loop produced."""

    dim: int
    ticks: int
    outputs: Tuple[Tuple[int, ...], ...]
    errors: Tuple[Tuple[Fraction, ...], ...]
    states: Tuple[Tuple[Fraction, ...], ...]
    input_means: Tuple[Fraction, ...]
    output_means: Tuple[Fraction, ...]
    coordinate_errors: Tuple[Fraction, ...]
    bound: Fraction
    within_bound: bool
    errors_bounded: bool
    identity_feedback: bool


def feedback_run(matrix: Sequence[Sequence[Fraction]],
                 inputs: Sequence[Sequence[Fraction]]) -> FeedbackRun:
    """Run the loop of ``GLM.Feedback.efState`` on an explicit input.

    ``inputs[k][i]`` is coordinate ``i`` of the input at tick ``k``::

        s_0     = 0
        v_k     = u_k + s_k
        y_k     = quantise(v_k)      (coordinatewise)
        e_k     = v_k - y_k
        s_(k+1) = A e_k

    The reported ``bound`` is the ``1/(2N)`` of
    ``GLM.Feedback.efAverage_error_le_identity``, which is a *theorem* only
    when ``A`` is the identity; for any other matrix it is quoted so that the
    comparison can be seen to fail.
    """
    dim = len(matrix)
    if dim == 0:
        raise ValueError("feedback_run: the matrix is empty")
    for row in matrix:
        if len(row) != dim:
            raise ValueError("feedback_run: the matrix is not square")
    ticks = len(inputs)
    if ticks == 0:
        raise ValueError("feedback_run: no input")
    grid = tuple(tuple(_exact(x, "feedback_run") for x in row)
                 for row in matrix)
    state = tuple(Fraction(0) for _ in range(dim))
    states: List[Tuple[Fraction, ...]] = [state]
    outs: List[Tuple[int, ...]] = []
    errs: List[Tuple[Fraction, ...]] = []
    totals = [Fraction(0)] * dim
    for k in range(ticks):
        u = tuple(_exact(x, "feedback_run") for x in inputs[k])
        if len(u) != dim:
            raise ValueError("feedback_run: an input row has the wrong width")
        for i in range(dim):
            totals[i] += u[i]
        v = tuple(u[i] + state[i] for i in range(dim))
        y = tuple(quantise(v[i]) for i in range(dim))
        e = tuple(v[i] - y[i] for i in range(dim))
        state = tuple(sum((grid[i][j] * e[j] for j in range(dim)),
                          Fraction(0)) for i in range(dim))
        outs.append(y)
        errs.append(e)
        states.append(state)
    input_means = tuple(totals[i] / ticks for i in range(dim))
    output_means = tuple(Fraction(sum(row[i] for row in outs), ticks)
                         for i in range(dim))
    coord_err = tuple(abs(output_means[i] - input_means[i])
                      for i in range(dim))
    bound = Fraction(1, 2 * ticks)
    return FeedbackRun(
        dim=dim, ticks=ticks, outputs=tuple(outs), errors=tuple(errs),
        states=tuple(states), input_means=input_means,
        output_means=output_means, coordinate_errors=coord_err,
        bound=bound, within_bound=all(x <= bound for x in coord_err),
        errors_bounded=all(abs(x) <= Fraction(1, 2)
                           for row in errs for x in row),
        identity_feedback=grid == identity_matrix(dim))


def feedback_tracking(targets: Sequence[Fraction],
                      ticks: int = 64) -> FeedbackRun:
    """Identity feedback on a constant vector target -- the `1/(2N)` law."""
    dim = len(targets)
    if dim == 0:
        raise ValueError("feedback_tracking: no targets")
    row = tuple(_exact(x, "feedback_tracking") for x in targets)
    return feedback_run(identity_matrix(dim), [row] * ticks)


def equivariance_check(matrix: Sequence[Sequence[Fraction]],
                       inputs: Sequence[Sequence[Fraction]],
                       permutation: Sequence[int]) -> Dict[str, object]:
    """Does permuting the coordinates permute the whole trajectory?

    ``GLM.Feedback.efOut_equivariant`` says it does, tick for tick, whenever
    the permutation leaves the feedback matrix invariant.  Both halves are
    measured here: whether the matrix is invariant, and whether the outputs
    actually permute.  A matrix that is *not* invariant is run as well, so the
    hypothesis is seen to be doing work.
    """
    dim = len(matrix)
    if sorted(permutation) != list(range(dim)):
        raise ValueError("equivariance_check: not a permutation of the "
                         "coordinates")
    sigma = tuple(permutation)
    invariant = all(matrix[sigma[i]][sigma[j]] == matrix[i][j]
                    for i in range(dim) for j in range(dim))
    plain = feedback_run(matrix, inputs)
    permuted_inputs = [tuple(row[sigma[i]] for i in range(dim))
                       for row in inputs]
    permuted = feedback_run(matrix, permuted_inputs)
    agrees = all(permuted.outputs[k][i] == plain.outputs[k][sigma[i]]
                 for k in range(plain.ticks) for i in range(dim))
    return {
        "dim": dim,
        "permutation": sigma,
        "matrix_invariant": invariant,
        "outputs_permute": agrees,
        "ticks": plain.ticks,
        "theorem_applies": invariant,
        "theorem_conclusion_holds": agrees,
    }


def dead_zone(ticks: int = 64) -> Dict[str, object]:
    """Contracting feedback does not slow the loop down; it stops it.

    ``GLM.Feedback.halfFeedback_dead_zone``: with ``A = 1/2`` and the constant
    input ``1/4`` the quantiser never fires, so the average error is exactly
    ``1/4`` however long the loop runs.  The identity loop on the same input
    is run beside it for contrast.
    """
    if ticks <= 0:
        raise ValueError("dead_zone: ticks must be positive")
    target = Fraction(1, 4)
    rows = [(target,)] * ticks
    contracting = feedback_run(scaled_matrix(1, Fraction(1, 2)), rows)
    tracking = feedback_run(identity_matrix(1), rows)
    return {
        "target": target,
        "ticks": ticks,
        "contracting_outputs_all_zero": all(
            y[0] == 0 for y in contracting.outputs),
        "contracting_error": contracting.coordinate_errors[0],
        "contracting_within_bound": contracting.within_bound,
        "identity_error": tracking.coordinate_errors[0],
        "identity_bound": tracking.bound,
        "identity_within_bound": tracking.within_bound,
        "identity_fires": any(y[0] != 0 for y in tracking.outputs),
    }


def feedback_experiment(ticks: int = 64) -> Dict[str, object]:
    """The whole error-feedback section, recomputed."""
    targets = (Fraction(1, 3), Fraction(2, 5), Fraction(3, 4),
               Fraction(1, 8))
    tracking = feedback_tracking(targets, ticks)
    permutation = (1, 2, 3, 0)
    symmetric = identity_matrix(4)
    asymmetric = [[Fraction(1) if i == j else Fraction(0)
                   for j in range(4)] for i in range(4)]
    asymmetric[0][1] = Fraction(1, 2)
    inputs = [tuple(targets) for _ in range(ticks)]
    return {
        "tracking": {
            "dim": tracking.dim,
            "ticks": tracking.ticks,
            "input_means": tracking.input_means,
            "output_means": tracking.output_means,
            "coordinate_errors": tracking.coordinate_errors,
            "bound": tracking.bound,
            "within_bound": tracking.within_bound,
            "errors_bounded": tracking.errors_bounded,
        },
        "equivariant": equivariance_check(symmetric, inputs, permutation),
        "not_equivariant": equivariance_check(asymmetric, inputs, permutation),
        "dead_zone": dead_zone(ticks),
    }


# ===========================================================================
# 6.  THE REPORT
# ===========================================================================


def demonstration_mix() -> Signal:
    """The interacting-tone signal the report drives the loop with.

    A base of 1/2 with a square wave of period 4 and a triangle of period 6
    added, so the beat period is 12.
    """
    return mix_tones(
        Fraction(1, 2),
        (square_tone(4, Fraction(1, 8), offset=Fraction(0)),
         triangle_tone(6, Fraction(1, 6), offset=Fraction(0))),
        name="square(4, 1/8) + triangle(6, 1/6) about 1/2")


def noise_report(ticks: int = 128) -> Dict[str, object]:
    """Recompute the whole laboratory on demand.

    Every figure below is produced by the call beside it; nothing is quoted.
    """
    if ticks < 8:
        raise ValueError("noise_report: ticks must be at least 8")

    mix = demonstration_mix()
    signal_run = run_signal(mix, ticks)

    closing = orbit_closure(
        mix_tones(Fraction(1, 2), (square_tone(4, Fraction(1, 4),
                                               offset=Fraction(0)),),
                  name="square(4, 1/4) about 1/2"), periods=4)
    not_closing = orbit_closure(
        mix_tones(Fraction(1, 3), (square_tone(4, Fraction(1, 8),
                                               offset=Fraction(0)),),
                  name="square(4, 1/8) about 1/3"), periods=4)

    cascade = cascade_run(Fraction(1, 3), ticks)
    table_half = convergence_table(Fraction(1, 2), (8, 16, 32, 64, 128))
    table_third = convergence_table(Fraction(1, 3), (8, 16, 32, 64, 128))
    dither = dither_experiment(Fraction(1, 2), 256, Fraction(1, 4))
    sweep = dither_sweep(Fraction(1, 2), 256)
    feedback = feedback_experiment(ticks)

    return {
        "signal_tracking": {
            "signal": mix.name,
            "period": mix.period,
            "input_mean": signal_run.input_mean,
            "bit_mean": signal_run.bit_mean,
            "error": signal_run.error,
            "bound": signal_run.bound,
            "within_bound": signal_run.within_bound,
            "state_stayed_in_range": signal_run.state_stayed_in_range,
            "ticks": ticks,
        },
        "orbit_closure": {
            "closing": closing,
            "not_closing": not_closing,
        },
        "cascade": {
            "target": cascade.target,
            "ticks": cascade.ticks,
            "alphabet": cascade.alphabet,
            "second_difference_holds": cascade.second_difference_holds,
            "double_sum": cascade.double_sum,
            "double_sum_equals_state": cascade.double_sum_equals_state,
            "plain_error": cascade.plain_error,
            "triangular_error": cascade.triangular_error,
            "triangular_bound": cascade.triangular_bound,
            "within_bound": cascade.within_bound,
        },
        "convergence_half": table_half,
        "convergence_third": table_third,
        "dither": dither,
        "dither_sweep": sweep,
        "feedback": feedback,
        "theorems": {
            "signal tracking": "GLM.Info.mAverage_error_le",
            "closed orbit": "GLM.Info.mState_periodic",
            "second difference": "GLM.Info.casOut_error",
            "doubly accumulated error": "GLM.Info.casDouble_sum",
            "cascade rate": "GLM.Info.casTriangular_error_lt",
            "single-loop floor": "GLM.Info.firstOrder_triangular_error_ge",
            "vector feedback rate":
                "GLM.Feedback.efAverage_error_le_identity",
            "bounded quantisation error": "GLM.Feedback.efErr_abs_le_half",
            "contracted feedback dies": "GLM.Feedback.halfFeedback_dead_zone",
            "equivariance": "GLM.Feedback.efOut_equivariant",
        },
    }
