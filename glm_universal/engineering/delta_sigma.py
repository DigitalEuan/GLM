"""``glm_universal.engineering.delta_sigma`` -- noise shaping, exactly.

What was already here
---------------------
The first-order one-bit loop is the GLM's *dynamic carrier*
(:class:`glm_universal.reasoning.exact_real.DeltaSigma`), with its bounds
proved in ``RequestProject/GLM/DeltaSigma.lean``: the state stays in
``[0, 1)``, the average after ``N`` ticks is within ``1/N`` of the target,
and the trajectory determines the target.

What this module adds
---------------------
The audio-engineering reading the session record asked for, with no float
anywhere:

* **periodicity, decided.**  A rational DC input ``p/q`` (lowest terms)
  gives a bitstream of period exactly ``q``; an irrational input gives a
  bitstream that is never periodic.  Both are *theorems*
  (``GLM.Engineering.ds_rational_period_iff``, ``ds_irrational_aperiodic`` in
  ``RequestProject/GLM/EngineeringWheels.lean``), so the question surface
  answers them by proof, and :func:`detect_period` is only the executable
  control.
* **an irrational input, exactly.**  ``sqrt(2) - 1`` is run through the loop
  with integer arithmetic only: the ``n``-th count of ones is
  ``floor(n*t) = isqrt(2 n^2) - n``.
* **noise shaping, measured exactly.**  First-order and second-order
  bipolar loops and a memoryless one-bit baseline are run on the same
  rational stimuli; the output and the input are both passed through the
  same ``sinc^3`` decimation filter (three cascaded length-``OSR`` moving
  sums), and the in-band error energy is an exact ``Fraction``.  Ratios are
  reported exactly and in whole decibels by an exact comparison
  (``r^10 >= 10^k``), never by a logarithm.
* **dither**, from a deterministic integer generator, triangular in shape,
  added at the quantiser only.

The six preregistered checks of the record are :data:`CHECKS`, declared here
before :func:`delta_sigma_report` computes them.

Limits
------
Idealised loops: no analogue noise, clock jitter, DAC mismatch or circuit
non-linearity.  The coherent tone is a triangle wave (an exact rational
periodic sequence); the incommensurate tone is an exact rational rotation by
an angle whose cosine is rational and which is therefore not a rational
multiple of pi (Niven), rounded to a ``2^-20`` grid.
"""

from __future__ import annotations

from fractions import Fraction
from math import isqrt
from typing import Dict, List, Optional, Sequence, Tuple

from ..reasoning.exact_real import delta_sigma_average, delta_sigma_bits

__all__ = [
    "CHECKS", "rational_period", "sqrt2_minus_1_bits", "detect_period",
    "first_order_bits", "dithered_bits", "first_order_bipolar",
    "second_order_bipolar", "memoryless", "sinc3", "inband_error",
    "db_floor", "triangle_tone", "rotation_tone", "delta_sigma_report",
    "delta_sigma_bits", "delta_sigma_average",
]

#: The six checks, declared before any figure is computed.
CHECKS: Tuple[str, ...] = (
    "rational DC 1/16 gives a first-order bitstream of period 16",
    "triangular dither breaks that period within the window",
    "the incommensurate DC input sqrt(2) - 1 shows no period within the "
    "window",
    "second order has less in-band error than first order on the tone",
    "both noise-shaping loops beat the memoryless one-bit baseline",
    "every second-order state stays within |x| <= 8 on the tone",
)

OSR = 64
WINDOW = 64 * OSR


def rational_period(t: Fraction) -> int:
    """The period of the first-order bitstream of ``t`` in ``[0, 1)``:
    the denominator of ``t`` in lowest terms (the theorem's statement)."""
    t = Fraction(t)
    if not 0 <= t < 1:
        raise ValueError("the one-bit loop is declared on [0, 1)")
    return t.denominator


def sqrt2_minus_1_bits(steps: int) -> Tuple[int, ...]:
    """The first-order bits of ``sqrt(2) - 1``, by integer arithmetic only."""
    out: List[int] = []
    prev = 0
    for n in range(1, steps + 1):
        ones = isqrt(2 * n * n) - n
        out.append(ones - prev)
        prev = ones
    return tuple(out)


def detect_period(bits: Sequence[int], max_period: int) -> Optional[int]:
    """The least ``p <= max_period`` with ``bits[i] == bits[i + p]`` over the
    second half of the window, or ``None``."""
    half = len(bits) // 2
    for p in range(1, max_period + 1):
        if half + p > len(bits):
            break
        if all(bits[i] == bits[i + p] for i in range(half, len(bits) - p)):
            return p
    return None


def first_order_bits(t: Fraction, steps: int) -> Tuple[int, ...]:
    return delta_sigma_bits(Fraction(t), steps)


def _lcg(seed: int):
    state = seed
    while True:
        state = (state * 6364136223846793005 + 1442695040888963407) % 2 ** 64
        yield state >> 48          # 16 bits


def dithered_bits(t: Fraction, steps: int, amplitude: Fraction,
                  seed: int = 2026) -> Tuple[int, ...]:
    """The first-order loop with triangular dither of peak ``amplitude``
    added at the quantiser decision only."""
    gen = _lcg(seed)
    s = Fraction(0)
    out: List[int] = []
    for _ in range(steps):
        d = (Fraction(next(gen) + next(gen), 2 ** 16) - 1) * amplitude
        bit = 1 if s + t + d >= 1 else 0
        s = s + t - bit
        out.append(bit)
    return tuple(out)


def _sgn(x: Fraction) -> int:
    return 1 if x >= 0 else -1


def first_order_bipolar(u: Sequence[Fraction]) -> Tuple[List[int], Fraction]:
    x = Fraction(0)
    ys: List[int] = []
    peak = Fraction(0)
    for v in u:
        y = _sgn(x)
        x = x + v - y
        peak = max(peak, abs(x))
        ys.append(y)
    return ys, peak


def second_order_bipolar(u: Sequence[Fraction]) -> Tuple[List[int], Fraction]:
    """The second-order loop with delaying integrators,
    ``x2' = x2 + x1 - 2y`` and ``x1' = x1 + u - y`` from the *old* states;
    signal transfer ``z^-2``, noise transfer ``(1 - z^-1)^2``."""
    x1 = Fraction(0)
    x2 = Fraction(0)
    ys: List[int] = []
    peak = Fraction(0)
    for v in u:
        y = _sgn(x2)
        x1, x2 = x1 + v - y, x2 + x1 - 2 * y
        peak = max(peak, abs(x1), abs(x2))
        ys.append(y)
    return ys, peak


def memoryless(u: Sequence[Fraction]) -> Tuple[List[int], Fraction]:
    return [_sgn(v) for v in u], Fraction(0)


def sinc3(xs: Sequence[Fraction], length: int = OSR) -> List[Fraction]:
    """Three cascaded moving sums of ``length``, normalised to unit DC gain."""
    cur = [Fraction(x) for x in xs]
    for _ in range(3):
        acc = Fraction(0)
        nxt: List[Fraction] = []
        for i, x in enumerate(cur):
            acc += x
            if i >= length:
                acc -= cur[i - length]
            nxt.append(acc)
        cur = nxt
    scale = Fraction(1, length ** 3)
    return [x * scale for x in cur]


def inband_error(u: Sequence[Fraction], y: Sequence[int],
                 delay: int = 0) -> Fraction:
    """In-band error energy per decimated sample after the settle-in.

    ``delay`` is the loop's signal delay (its signal transfer is
    ``z^-delay``): the output at ``n`` is compared with the input at
    ``n - delay``, so a pure delay is never scored as error.
    """
    shifted = [Fraction(0)] * delay + list(u[:len(u) - delay])
    fu, fy = sinc3(shifted), sinc3([Fraction(v) for v in y])
    start = 3 * OSR + len(u) // 4
    picks = range(start, len(u), OSR)
    total = sum(((a - b) ** 2 for a, b in
                 ((fu[i], fy[i]) for i in picks)), Fraction(0))
    return total / len(picks)


def db_floor(ratio: Fraction) -> int:
    """The largest integer ``k`` with ``10 log10(ratio) >= k``, exactly."""
    if ratio <= 0:
        raise ValueError("a decibel figure needs a positive ratio")
    r10 = Fraction(ratio) ** 10
    k = 0
    while r10 >= Fraction(10) ** (k + 1):
        k += 1
    while r10 < Fraction(10) ** k:
        k -= 1
    return k


def triangle_tone(n: int, period: int, amplitude: Fraction
                  ) -> List[Fraction]:
    """An exact rational triangle wave: the coherent periodic stimulus."""
    out = []
    for i in range(n):
        ph = Fraction(i % period, period)
        tri = 4 * ph - 1 if ph < Fraction(1, 2) else 3 - 4 * ph
        out.append(amplitude * tri)
    return out


def rotation_tone(n: int, m: int, amplitude: Fraction,
                  grid: int = 2 ** 20) -> List[Fraction]:
    """Rotation by the angle with cosine ``(m^2 - 1)/(m^2 + 1)`` on an
    integer grid: an incommensurate stimulus, exactly reproducible."""
    a, b, c = m * m - 1, 2 * m, m * m + 1
    x, y = grid, 0
    out = []
    for _ in range(n):
        out.append(amplitude * Fraction(x, grid))
        x, y = (a * x - b * y + c // 2) // c, (b * x + a * y + c // 2) // c
    return out


def delta_sigma_report() -> Dict[str, object]:
    """The six checks and the figures behind them."""
    rat = first_order_bits(Fraction(1, 16), WINDOW)
    p_rat = detect_period(rat, 1024)
    dith = dithered_bits(Fraction(1, 16), WINDOW, Fraction(1, 8))
    p_dith = detect_period(dith, 1024)
    irr = sqrt2_minus_1_bits(WINDOW)
    p_irr = detect_period(irr, 1024)
    stimuli = {
        "triangle": triangle_tone(WINDOW, 1024, Fraction(1, 2)),
        "rotation": rotation_tone(WINDOW, 200, Fraction(1, 2)),
    }
    loops = {"first": (first_order_bipolar, 1),
             "second": (second_order_bipolar, 2),
             "memoryless": (memoryless, 0)}
    errors: Dict[str, Dict[str, Fraction]] = {}
    peaks: Dict[str, Fraction] = {}
    for sname, u in stimuli.items():
        errors[sname] = {}
        for lname, (loop, delay) in loops.items():
            ys, peak = loop(u)
            errors[sname][lname] = inband_error(u, ys, delay)
            if lname == "second":
                peaks[sname] = peak
    tri = errors["triangle"]
    results = (
        p_rat == 16,
        p_dith is None,
        p_irr is None,
        tri["second"] < tri["first"],
        tri["second"] < tri["memoryless"] and tri["first"] < tri["memoryless"],
        all(p <= 8 for p in peaks.values()),
    )
    gains = {s: {"first_over_second_db": db_floor(e["first"] / e["second"]),
                 "memoryless_over_first_db": db_floor(e["memoryless"]
                                                      / e["first"])}
             for s, e in errors.items()}
    return {
        "checks": list(zip(CHECKS, results)),
        "passed": sum(results),
        "periods": {"rational_1_16": p_rat, "dithered": p_dith,
                    "sqrt2_minus_1": p_irr},
        "gains_db_floor": gains,
        "second_order_peak_state": {k: str(v) for k, v in peaks.items()},
        "window": WINDOW, "osr": OSR,
    }
