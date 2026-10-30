"""``glm_universal.reasoning.wobble_landscape`` -- is alpha distinctive?

What this module is
-------------------
The measurement half of ``studies/WOBBLE_LANDSCAPE_STUDY.md``, which was
written and committed **before** this file existed.  The study asks one
pre-registered question -- is the fine-structure constant's *gap-structure*
signature unusual against a stated magnitude-matched null? -- and answers it
with one number, the bit score

    B = log2(1 / p_tail) - log2(m)

with ``m`` the number of statistics that could have been reported as the
primary one.  ``B < 1`` is "not evidence", and is a result rather than a
failure.

**This module does not derive alpha and nothing in it should be read as
deriving alpha.**

What is a theorem here and what is a measurement
------------------------------------------------
The stream is not simulated where its structure is known in closed form.  The
delta-sigma modulator chasing ``t`` emits the Sturmian word of slope ``t``
(``GLM.Info.dsBit_eq_floor_diff``), the ``j``-th one sits at
``ceil(j/t) - 1``, and therefore, with ``s = 1/t``,

    gap_j = ceil((j+1) s) - ceil(j s)   in   {floor(s), floor(s) + 1}

-- at most two distinct gap lengths, which is the two-distance form of the
Three-Distance Theorem for the first-return map (``GLM.Landscape.gap_mem_pair``
in ``RequestProject/GLM/WobbleLandscape.lean``).  Writing ``a_0 = floor(s)``
and ``t_1 = s - a_0``, the number of long gaps among the first ``K`` is exactly

    long(K) = ceil((K + 1) * t_1) - 1                    (:func:`long_gap_count`)

so the long-gap frequency is ``t_1 = frac(1/t)`` and the sequence of gap
*types* is itself Sturmian of slope ``t_1``.  Iterating that is the Gauss map,
so the ladder of gap spectra is the continued fraction of ``s`` stage by stage
-- Ostrowski numeration (:func:`ostrowski_ladder`).

:func:`gap_spectrum_check` runs the loop for a finite depth and compares.  A
disagreement is a bug, and ``tests/test_wobble_landscape.py`` perturbs the
closed form to check that the comparison would catch one.

The pre-registered test
-----------------------
======================  ====================================================
what                    fixed as
======================  ====================================================
target                  ``alpha = 7.2973525643e-3`` (CODATA 2022), exact
primary statistic       ``S(x) = frac(1 / frac(x))`` -- the stage-0 long-gap
                        frequency, i.e. the frequency of the longer of the two
                        gap lengths.  **Not** the bit entropy, which is
                        ``H2(t)`` and carries only the magnitude of ``t``.
tail                    two-sided about ``1/2``:
                        ``Pr[|S - 1/2| >= |S(alpha) - 1/2|]``
null B (primary)        every ``j / 10**7`` strictly inside
                        ``(1/138, 1/136)``; exhaustive, exact
null A (secondary)      ``1 / (137 + 1/k)`` for ``k = 1 .. 100``; exhaustive
correction              ``m = 4`` statistics tried
gate                    ``B < 1`` not evidence; ``1 <= B < 3`` weak; ``B >= 3``
                        continue to the landscape enumeration
======================  ====================================================

Chance is a count over a count in both nulls.  Nothing is sampled and no seed
is used anywhere in this module.

The Golay null, exactly
-----------------------
The binary Golay code has 4096 codewords and minimum distance 8, so the balls
of radius 3 about them are disjoint and cover
``4096 * (1 + 24 + 276 + 2024) = 9,523,200`` of ``2**24`` words: ``d_min <= 3``
has probability ``2325/4096`` exactly, under a *uniform* word.  That is the
majority case, worth about 0.82 bits -- not a structural coincidence.
:func:`golay_null` recomputes the whole coset-weight distribution from the code
itself rather than quoting it.

Exactness
---------
No float is constructed anywhere.  Slopes, frequencies and tail probabilities
are exact :class:`~fractions.Fraction` values; ``log2`` is an exact rational
bracket with a derived error bound (:func:`log2_bracket`); rendering goes
through integer arithmetic.  Directive D7.

The cache
---------
:func:`measure` is a few seconds of work, and the study's tables are emitted
from it rather than from a fresh run at rendering time.  It is stored beside
the digest of the sources it was taken from (:func:`module_digest`), so a
change to this module makes the cache *stale* and the generated blocks say so
(D4).  Re-take it with::

    cd overlay
    PYTHONPATH=. python3 -m glm_universal.tools landscape --write

The command line lives in :mod:`glm_universal.tools`, one module above the core, because the six
core sub-packages are libraries and not programs.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from ..substrate import golay_decode as gd
from . import coherence as coh
from . import exact_real as xr
from . import transcendental as tr
from . import wobble as wbl

__all__ = [
    "ALPHA", "STRIDE", "NULL_LOW", "NULL_HIGH", "K_SWEEP",
    "STATISTICS_TRIED", "PRIMARY_GAPS", "DEPTH_SWEEP", "GOLAY_DEPTHS",
    "GATE_WEAK", "GATE_CONTINUE", "LADDER_STAGES", "CF_DEPTH",
    "fractional", "continued_fraction", "slope", "statistic", "deviation",
    "gap_spectrum", "long_gap_count", "ostrowski_ladder",
    "simulated_gaps", "gap_spectrum_check", "depth_profile",
    "log2_bracket", "bit_score",
    "stride_null", "k_sweep_null", "null_tail", "primary_test",
    "golay_null", "golay_words", "golay_profile", "golay_table",
    "golay_magnitude_null",
    "targets", "comparison_table", "gate_decision", "landscape_report",
    "module_digest", "measure", "write_measurements", "measurements",
    "state", "current", "DATA_PATH",
]


# ═════════════════════════════════════════════════════════════════════════
# 1.  THE PRE-REGISTERED CONSTANTS
# ═════════════════════════════════════════════════════════════════════════

#: The fine-structure constant, CODATA 2022, as an exact rational.
ALPHA: Fraction = Fraction(72973525643, 10 ** 13)

#: The stride of the primary null: every ``j / STRIDE`` in the interval.
STRIDE: int = 10 ** 7

#: The magnitude-matched interval, ``(1/138, 1/136)``.
NULL_LOW: Fraction = Fraction(1, 138)
NULL_HIGH: Fraction = Fraction(1, 136)

#: The secondary null sweeps ``[137; k]`` for ``k = 1 .. K_SWEEP``.
K_SWEEP: int = 100

#: The multiplicity correction: how many statistics this study tried.
STATISTICS_TRIED: int = 4

#: The depth at which the empirical estimate of the statistic is quoted.
PRIMARY_GAPS: int = 100

#: The exploratory stability sweep, in gaps.
DEPTH_SWEEP: Tuple[int, ...] = (10, 20, 50, 100, 500)

#: The bit depths at which the Golay statistic is taken.
GOLAY_DEPTHS: Tuple[int, ...] = (24, 48, 72)

#: The decision tree of the study, in bits.
GATE_WEAK: int = 1
GATE_CONTINUE: int = 3

#: How many Ostrowski stages the ladder reports, and how far the continued
#: fraction is printed.
LADDER_STAGES: int = 6
CF_DEPTH: int = 10

#: Bits of precision in every ``log2`` bracket.
LOG_BITS: int = 40

#: The dyadic level irrational targets are pinned to before use, matching
#: :mod:`~glm_universal.reasoning.wobble`.
TARGET_PRECISION: int = wbl.TARGET_PRECISION


# ═════════════════════════════════════════════════════════════════════════
# 2.  CONTINUED FRACTIONS AND THE GAP SPECTRUM
# ═════════════════════════════════════════════════════════════════════════

def fractional(value: Fraction) -> Fraction:
    """The fractional part of an exact rational, in ``[0, 1)``."""
    value = Fraction(value)
    return value - (value.numerator // value.denominator)


def continued_fraction(value: Fraction, depth: int = CF_DEPTH) -> Tuple[int, ...]:
    """The first ``depth`` partial quotients of an exact rational.

    Terminates early when the expansion does.  Exact integer arithmetic
    throughout: this is the Euclidean algorithm.
    """
    if depth <= 0:
        raise ValueError("continued_fraction: depth must be positive")
    out: List[int] = []
    x = Fraction(value)
    for _ in range(depth):
        whole = x.numerator // x.denominator
        out.append(whole)
        x = x - whole
        if x == 0:
            break
        x = 1 / x
    return tuple(out)


def slope(value: Fraction) -> Fraction:
    """The Sturmian slope a target is read at: its fractional part."""
    return fractional(value)


def statistic(value: Fraction) -> Fraction:
    """The pre-registered primary statistic: the stage-0 long-gap frequency.

    ``S(x) = frac(1 / frac(x))``.  By the closed form of :func:`long_gap_count`
    this is exactly the limiting frequency of the longer of the two gap lengths
    in the Sturmian word of slope ``frac(x)``.
    """
    t = slope(value)
    if t == 0:
        raise ValueError("statistic: the slope of an integer is zero")
    return fractional(1 / t)


def deviation(value: Fraction) -> Fraction:
    """How far the statistic sits from a balanced two-gap mixture."""
    return abs(statistic(value) - Fraction(1, 2))


def gap_spectrum(t: Fraction) -> Dict[str, object]:
    """The closed-form gap spectrum of the Sturmian word of slope ``t``.

    Two gap lengths, ``floor(1/t)`` and ``floor(1/t) + 1``, with frequencies
    ``1 - frac(1/t)`` and ``frac(1/t)``, and a mean gap of exactly ``1/t``.
    """
    if not 0 < t < 1:
        raise ValueError("gap_spectrum: the slope must lie strictly in (0, 1)")
    reciprocal = 1 / t
    short = reciprocal.numerator // reciprocal.denominator
    long_frequency = reciprocal - short
    return {
        "slope": t,
        "short_gap": short,
        "long_gap": short + 1,
        "long_frequency": long_frequency,
        "short_frequency": 1 - long_frequency,
        "mean_gap": reciprocal,
        "degenerate": long_frequency == 0,
    }


def long_gap_count(t: Fraction, gaps: int) -> int:
    """How many of the first ``gaps`` gaps are long -- in closed form.

    ``ceil((K + 1) * t_1) - 1`` with ``t_1 = frac(1/t)``, derived by summing
    the telescoping ``ceil((j+1)s) - ceil(js)`` and subtracting ``K floor(s)``.

    The degenerate case is real and is handled rather than excluded: when
    ``1/t`` is an integer the word is periodic, there is only one gap length,
    and the count of long gaps is zero.
    """
    if gaps < 0:
        raise ValueError("long_gap_count: gaps must not be negative")
    t1 = gap_spectrum(t)["long_frequency"]
    if t1 == 0:
        return 0
    product = (gaps + 1) * t1
    ceiling = -((-product.numerator) // product.denominator)
    return ceiling - 1


def ostrowski_ladder(t: Fraction, stages: int = LADDER_STAGES
                     ) -> Tuple[Dict[str, object], ...]:
    """The gap spectrum at each Ostrowski stage: the continued fraction, read.

    Stage 0 is the bit stream itself; stage ``j+1`` is the word whose letters
    are the *types* of stage ``j``'s gaps, whose slope is ``frac(1/t_j)``.  The
    short gap at stage ``j`` is the partial quotient ``a_j``.
    """
    out: List[Dict[str, object]] = []
    current_slope = Fraction(t)
    for stage in range(stages):
        if current_slope == 0:
            break
        row = dict(gap_spectrum(current_slope))
        row["stage"] = stage
        out.append(row)
        current_slope = row["long_frequency"]
    return tuple(out)


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE SIMULATION THE CLOSED FORM IS CHECKED AGAINST
# ═════════════════════════════════════════════════════════════════════════

def simulated_gaps(t: Fraction, steps: int) -> Tuple[int, ...]:
    """The gaps between consecutive ones in a finite run of the modulator.

    The truncated leading and trailing stretches are not gaps and are dropped:
    a gap is a difference of two observed one-positions.
    """
    bits = wbl.stream_bits(t, steps)
    positions = [index for index, bit in enumerate(bits) if bit == 1]
    return tuple(second - first
                 for first, second in zip(positions, positions[1:]))


def gap_spectrum_check(t: Fraction, steps: int) -> Dict[str, object]:
    """The closed form against the run: lengths, and the long-gap count.

    Both halves are exact.  ``lengths_hold`` is the two-distance bound -- every
    observed gap is ``a_0`` or ``a_0 + 1`` -- and ``count_holds`` is the closed
    form :func:`long_gap_count` against the count in the run.
    """
    spectrum = gap_spectrum(slope(t))
    short = spectrum["short_gap"]
    observed = simulated_gaps(slope(t), steps)
    gaps = len(observed)
    long_observed = sum(1 for gap in observed if gap == short + 1)
    predicted = long_gap_count(slope(t), gaps)
    return {
        "slope": slope(t),
        "steps": steps,
        "gaps": gaps,
        "short_gap": short,
        "long_gap": short + 1,
        "distinct_lengths": tuple(sorted(set(observed))),
        "lengths_hold": all(gap in (short, short + 1) for gap in observed),
        "long_observed": long_observed,
        "long_closed_form": predicted,
        "count_holds": long_observed == predicted,
        "holds": (all(gap in (short, short + 1) for gap in observed)
                  and long_observed == predicted),
    }


def depth_profile(t: Fraction, depths: Sequence[int] = DEPTH_SWEEP
                  ) -> Tuple[Dict[str, object], ...]:
    """How fast the finite-depth estimate of the statistic settles.

    Exploratory.  The closed-form statistic is depth-free; this is the
    stability check, and the estimate at ``K`` gaps is
    ``long_gap_count(t, K) / K``, which is exact.
    """
    exact = statistic(t)
    out: List[Dict[str, object]] = []
    for gaps in depths:
        estimate = Fraction(long_gap_count(slope(t), gaps), gaps)
        out.append({
            "gaps": gaps,
            "bits_needed": gaps * gap_spectrum(slope(t))["long_gap"],
            "estimate": estimate,
            "exact": exact,
            "error": abs(estimate - exact),
        })
    return tuple(out)


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE BIT SCORE
# ═════════════════════════════════════════════════════════════════════════

def log2_bracket(value: Fraction, bits: int = LOG_BITS) -> Dict[str, Fraction]:
    """``log2(value)`` as an exact rational bracket, for ``value > 0``.

    Returns ``value``, ``error``, ``lower`` and ``upper``; the true logarithm
    lies in ``[lower, upper]`` and ``upper - lower = 2 * error`` with
    ``error = 2**-bits``.

    *The bound.*  With ``L`` within ``2**-K`` of ``ln x`` and ``D`` within
    ``2**-K`` of ``ln 2 >= 1/2``,

        |L/D - ln x / ln 2| <= |L - ln x| / D + |ln x| * |1/D - 1/ln 2|
                            <= 2 * 2**-K + 4 * |ln x| * 2**-K,

    and ``|ln x| <= magnitude`` where ``magnitude`` is one more than the larger
    bit length of numerator and denominator, since ``ln x <= magnitude * ln 2``.
    So a factor ``2 + 4 * magnitude <= 8 * magnitude`` is lost, and ``K`` is
    raised by its bit length.
    """
    value = Fraction(value)
    if value <= 0:
        raise ValueError("log2_bracket: the argument must be positive")
    if bits < 1:
        raise ValueError("log2_bracket: precision must be positive")
    magnitude = 1 + max(value.numerator.bit_length(),
                        value.denominator.bit_length())
    inner = bits + (8 * magnitude).bit_length()
    quotient = (tr.rational_log_approx(value, inner)
                / tr.log_two_approx(inner))
    error = Fraction(1, 2 ** bits)
    return {"value": quotient, "error": error,
            "lower": quotient - error, "upper": quotient + error}


def bit_score(tail: Fraction, statistics: int = STATISTICS_TRIED
              ) -> Dict[str, object]:
    """``B = log2(1 / p_tail) - log2(m)``, as an exact bracket.

    A tail of 1 scores exactly 0 before the correction, and the correction is
    applied whatever the outcome.  ``B`` is *antitone* in the tail probability
    -- a larger ``p`` can only score lower -- which is
    ``GLM.Landscape.bitScore_antitone``.
    """
    tail = Fraction(tail)
    if not 0 < tail <= 1:
        raise ValueError("bit_score: the tail probability must lie in (0, 1]")
    if statistics < 1:
        raise ValueError("bit_score: the number of statistics must be >= 1")
    raw = log2_bracket(1 / tail)
    penalty = log2_bracket(Fraction(statistics))
    corrected = raw["value"] - penalty["value"]
    error = raw["error"] + penalty["error"]
    return {
        "tail": tail,
        "statistics": statistics,
        "raw": raw["value"],
        "raw_error": raw["error"],
        "raw_rounded": wbl.round_str(raw["value"], 2),
        "penalty": penalty["value"],
        "corrected": corrected,
        "corrected_error": error,
        "corrected_rounded": wbl.round_str(corrected, 2),
    }


# ═════════════════════════════════════════════════════════════════════════
# 5.  THE NULLS
# ═════════════════════════════════════════════════════════════════════════

def stride_null(stride: int = STRIDE) -> Tuple[Fraction, ...]:
    """Null B: every ``j / stride`` strictly inside ``(1/138, 1/136)``.

    Exhaustive, so the chance it defines is a count over a count rather than
    an estimate.
    """
    if stride <= 0:
        raise ValueError("stride_null: the stride must be positive")
    low = stride * NULL_LOW
    high = stride * NULL_HIGH
    first = low.numerator // low.denominator + 1
    last = -((-high.numerator) // high.denominator) - 1
    return tuple(Fraction(j, stride) for j in range(first, last + 1)
                 if NULL_LOW < Fraction(j, stride) < NULL_HIGH)


def k_sweep_null(sweep: int = K_SWEEP) -> Tuple[Fraction, ...]:
    """Null A: ``1 / (137 + 1/k)`` for ``k = 1 .. sweep``.

    Secondary by design.  Its answer is a function of the measure placed on
    ``k``, and a uniform sweep is a choice rather than a fact; the study says
    so before measuring.
    """
    if sweep <= 0:
        raise ValueError("k_sweep_null: the sweep must be positive")
    return tuple(1 / (Fraction(137) + Fraction(1, k))
                 for k in range(1, sweep + 1))


def null_tail(members: Sequence[Fraction], observed: Fraction
              ) -> Dict[str, object]:
    """How many members of a null are at least as extreme as ``observed``.

    ``observed`` is a deviation ``|S - 1/2|``; the tail is two-sided by
    construction, because the deviation folds both sides together.
    """
    total = len(members)
    if total == 0:
        raise ValueError("null_tail: the null is empty")
    at_least = sum(1 for member in members if deviation(member) >= observed)
    return {
        "members": total,
        "at_least_as_extreme": at_least,
        "tail": Fraction(at_least, total),
    }


def primary_test(stride: int = STRIDE, sweep: int = K_SWEEP
                 ) -> Dict[str, object]:
    """The phase-2 decision: alpha's statistic against both nulls."""
    observed = statistic(ALPHA)
    spread = deviation(ALPHA)
    primary_members = stride_null(stride)
    secondary_members = k_sweep_null(sweep)
    primary = null_tail(primary_members, spread)
    secondary = null_tail(secondary_members, spread)
    return {
        "target": ALPHA,
        "statistic": observed,
        "statistic_rounded": wbl.round_str(observed, 6),
        "deviation": spread,
        "spectrum": gap_spectrum(slope(ALPHA)),
        "primary_null": {
            "name": f"stride {stride} rationals in (1/138, 1/136)",
            "stride": stride,
            **primary,
            "score": bit_score(primary["tail"]),
        },
        "secondary_null": {
            "name": f"reciprocal [137; k], k = 1 .. {sweep}",
            "sweep": sweep,
            **secondary,
            "score": bit_score(secondary["tail"]),
        },
        "empirical": {
            "gaps": PRIMARY_GAPS,
            "estimate": Fraction(long_gap_count(slope(ALPHA), PRIMARY_GAPS),
                                 PRIMARY_GAPS),
        },
    }


def gate_decision(score: Fraction) -> Dict[str, object]:
    """The pre-registered decision tree, applied to a bit score."""
    if score < GATE_WEAK:
        verdict, action = "not evidence", "stop; record the null result"
    elif score < GATE_CONTINUE:
        verdict, action = "weak", "stop; record it as weak"
    else:
        verdict, action = "worth spending on", "run the landscape enumeration"
    return {
        "score": score,
        "score_rounded": wbl.round_str(score, 2),
        "verdict": verdict,
        "action": action,
        "enumerate": score >= GATE_CONTINUE,
        "weak_gate": GATE_WEAK,
        "continue_gate": GATE_CONTINUE,
    }


# ═════════════════════════════════════════════════════════════════════════
# 6.  THE GOLAY QUESTION
# ═════════════════════════════════════════════════════════════════════════

def golay_null() -> Dict[str, object]:
    """The exact null for "how close is a 24-bit word to the code?"

    Recomputed from the code's own coset table rather than quoted: the number
    of cosets of each weight is the number of words at that distance from the
    code, divided by 4096.  The radius-3 count is the sphere identity
    ``4096 * (1 + 24 + 276 + 2024) = 9,523,200``.
    """
    census = gd.coset_census()
    by_weight = dict(census["cosets_by_leader_weight"])
    space = 2 ** 24
    codewords = 4096
    spheres = tuple(_binomial(24, i) for i in range(4))
    within_three = codewords * sum(spheres)
    cumulative: Dict[int, Fraction] = {}
    running = 0
    for weight in sorted(by_weight):
        running += by_weight[weight]
        cumulative[weight] = Fraction(running, codewords)
    return {
        "space": space,
        "codewords": codewords,
        "sphere_terms": spheres,
        "sphere_size": sum(spheres),
        "within_three": within_three,
        "within_three_probability": Fraction(within_three, space),
        "within_three_bits": bit_score(Fraction(within_three, space),
                                       statistics=1)["raw"],
        "cosets_by_weight": {weight: by_weight[weight]
                             for weight in sorted(by_weight)},
        "probability_by_weight": {weight: Fraction(by_weight[weight],
                                                   codewords)
                                  for weight in sorted(by_weight)},
        "cumulative": cumulative,
    }


def _binomial(n: int, k: int) -> int:
    """``n choose k`` by exact integer arithmetic."""
    if k < 0 or k > n:
        return 0
    out = 1
    for step in range(k):
        out = out * (n - step) // (step + 1)
    return out


def golay_words(t: Fraction, depth: int) -> Tuple[int, ...]:
    """The first ``depth`` bits of the stream, cut into 24-bit words."""
    if depth <= 0 or depth % 24 != 0:
        raise ValueError("golay_words: the depth must be a positive multiple "
                         "of 24")
    bits = wbl.stream_bits(slope(t), depth)
    out: List[int] = []
    for start in range(0, depth, 24):
        mask = 0
        for offset in range(24):
            if bits[start + offset]:
                mask |= 1 << offset
        out.append(mask)
    return tuple(out)


def golay_profile(t: Fraction, depths: Sequence[int] = GOLAY_DEPTHS
                  ) -> Tuple[Dict[str, object], ...]:
    """The distance to the code at each depth, with the exact tail beside it."""
    null = golay_null()
    cumulative = null["cumulative"]
    out: List[Dict[str, object]] = []
    for depth in depths:
        words = golay_words(t, depth)
        weights = tuple(gd.coset_weight(word) for word in words)
        smallest = min(weights)
        out.append({
            "depth": depth,
            "words": words,
            "weights": weights,
            "d_min": smallest,
            "all_zero": all(word == 0 for word in words),
            "tail": cumulative[smallest],
            "bits": bit_score(cumulative[smallest], statistics=1)["raw"],
        })
    return tuple(out)


def golay_magnitude_null(depth: int = 72, stride: int = STRIDE
                         ) -> Dict[str, object]:
    """The Golay statistic over the *magnitude-matched* null, exhaustively.

    The uniform-word null of :func:`golay_null` is the wrong null for a
    stream: a slope below ``1/depth`` emits no one at all in ``depth`` bits, so
    its word is all zeros, which is a codeword, and ``d_min = 0`` follows from
    the magnitude alone.  Every member of the stride null shares alpha's
    magnitude, so this measures how much of the apparent signal survives that
    control.  Exhaustive: a count over a count.
    """
    members = stride_null(stride)
    observed = min(row["d_min"] for row in golay_profile(ALPHA, (depth,)))
    counts: Dict[int, int] = {}
    for member in members:
        smallest = min(gd.coset_weight(word)
                       for word in golay_words(member, depth))
        counts[smallest] = counts.get(smallest, 0) + 1
    at_least = sum(count for weight, count in counts.items()
                   if weight <= observed)
    tail = Fraction(at_least, len(members))
    return {
        "depth": depth,
        "members": len(members),
        "observed": observed,
        "by_distance": {weight: counts[weight] for weight in sorted(counts)},
        "at_least_as_close": at_least,
        "tail": tail,
        "score": bit_score(tail),
    }


def golay_table() -> Tuple[Dict[str, object], ...]:
    """The Golay statistic for every comparison target."""
    out: List[Dict[str, object]] = []
    for name, notation, value in targets():
        profile = golay_profile(value)
        out.append({
            "name": name,
            "notation": notation,
            "slope": slope(value),
            "rows": profile,
            "d_min": min(row["d_min"] for row in profile),
            "all_zero": all(row["all_zero"] for row in profile),
        })
    return tuple(out)


# ═════════════════════════════════════════════════════════════════════════
# 7.  THE COMPARISON ROWS
# ═════════════════════════════════════════════════════════════════════════

def _pin(real: "xr.ExactReal") -> Fraction:
    """A process, pinned to its level-``TARGET_PRECISION`` dyadic stand-in."""
    return xr.surrogate(real, TARGET_PRECISION)


def targets() -> Tuple[Tuple[str, str, Fraction], ...]:
    """Every row of the comparison table, as ``(name, notation, value)``.

    Three families, and the study reads all three at the same resolution:

    * the target -- alpha, exactly, from CODATA 2022;
    * the other dimensionless constants of physics, each an exact rational
      built from its measured decimal, with the source named in the notation;
    * the substrate's own constants -- ``pi``, ``e``, ``phi``, the read quantum
      ``Y``, the activation quantum ``Q`` and ``MONAD = pi * phi * e`` -- which
      are what the machine would be reaching for if it were reaching for
      anything.

    Every value is exact.  The irrational ones are pinned to their level-64
    dyadic stand-in first, which is the same convention
    :mod:`~glm_universal.reasoning.wobble` uses.
    """
    pi = xr.pi()
    phi = xr.phi()
    e = xr.e()
    return (
        ("alpha", "7.2973525643e-3 (CODATA 2022)", ALPHA),
        ("m_p/m_e", "1836.152673426 (CODATA 2022)",
         Fraction(1836152673426, 10 ** 9)),
        ("sin^2 theta_W", "0.23122 (PDG, MS-bar)", Fraction(23122, 10 ** 5)),
        ("alpha_s(M_Z)", "0.1180 (PDG)", Fraction(1180, 10 ** 4)),
        ("(g-2)/2", "0.00115965218059 (electron anomaly)",
         Fraction(115965218059, 10 ** 14)),
        ("pi", "pi", _pin(pi)),
        ("e", "e", _pin(e)),
        ("phi", "(1 + sqrt(5))/2", _pin(phi)),
        ("Y", "1/(pi + 2/pi), as carried", coh.Y),
        ("Q", "Y + 1/8", coh.Q),
        ("MONAD", "pi * phi * e", _pin(pi * phi * e)),
    )


def comparison_table(stride: int = STRIDE) -> Tuple[Dict[str, object], ...]:
    """The primary statistic for every target, with alpha's null beside it.

    The tail column is *alpha's* null -- the stride-selected rationals of
    ``(1/138, 1/136)`` -- applied to each row's own deviation, so the column
    answers "how unusual would this row's signature be if it had alpha's
    magnitude".  It is a comparison, not a claim that the other constants live
    in that interval.
    """
    members = stride_null(stride)
    spreads = tuple(deviation(member) for member in members)
    out: List[Dict[str, object]] = []
    for name, notation, value in targets():
        t = slope(value)
        spectrum = gap_spectrum(t)
        spread = deviation(value)
        at_least = sum(1 for other in spreads if other >= spread)
        tail = Fraction(max(at_least, 1), len(members))
        out.append({
            "name": name,
            "notation": notation,
            "value": value,
            "slope": t,
            "reciprocal_cf": continued_fraction(1 / t, CF_DEPTH),
            "short_gap": spectrum["short_gap"],
            "long_gap": spectrum["long_gap"],
            "statistic": spectrum["long_frequency"],
            "statistic_rounded": wbl.round_str(spectrum["long_frequency"], 6),
            "deviation": spread,
            "tail": tail,
            "bits": bit_score(tail)["corrected"],
            "bits_rounded": bit_score(tail)["corrected_rounded"],
            "ladder": tuple(row["short_gap"]
                            for row in ostrowski_ladder(t, LADDER_STAGES)),
        })
    out.sort(key=lambda row: (-row["deviation"], row["name"]))
    for rank, row in enumerate(out, start=1):
        row["rank"] = rank
    return tuple(out)


# ═════════════════════════════════════════════════════════════════════════
# 8.  THE REPORT
# ═════════════════════════════════════════════════════════════════════════

def landscape_report() -> Dict[str, object]:
    """Every figure the study quotes, recomputed from the sources."""
    test = primary_test()
    primary = test["primary_null"]
    gate = gate_decision(primary["score"]["corrected"])
    check = gap_spectrum_check(ALPHA, 20_000)
    entropy = wbl.entropy_bits(slope(ALPHA))
    return {
        "target": ALPHA,
        "reciprocal": 1 / ALPHA,
        "reciprocal_cf": continued_fraction(1 / ALPHA, CF_DEPTH),
        "run_length": gap_spectrum(slope(ALPHA))["short_gap"],
        "entropy": entropy["value"],
        "entropy_rounded": wbl.round_str(entropy["value"], 3),
        "ladder": ostrowski_ladder(slope(ALPHA), LADDER_STAGES),
        "closed_form_check": check,
        "depth_profile": depth_profile(ALPHA),
        "primary": test,
        "gate": gate,
        "golay_null": golay_null(),
        "golay_magnitude": golay_magnitude_null(),
        "golay": golay_table(),
        "comparison": comparison_table(),
        "statistics_tried": STATISTICS_TRIED,
    }


# ═════════════════════════════════════════════════════════════════════════
# 9.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH = Path(__file__).resolve().parent / "_data" / "wobble_landscape.json"

#: The sources the measurement is taken from.  A change to any of them makes
#: the cache stale, which is D4: a stored result is reused only against a
#: recorded digest of everything it depended on.
_SOURCES: Tuple[str, ...] = (
    "reasoning/wobble_landscape.py",
    "reasoning/wobble.py",
    "reasoning/exact_real.py",
    "reasoning/transcendental.py",
    "reasoning/coherence.py",
    "substrate/golay_decode.py",
)


def module_digest() -> str:
    """One digest over the sources this measurement is taken from."""
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / name for name in _SOURCES], root)


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return {"__fraction__": f"{value.numerator}/{value.denominator}"}
    if isinstance(value, dict):
        return {str(key): _freeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(item) for item in value]
    return value


def _thaw(value: object) -> object:
    if isinstance(value, dict):
        text = value.get("__fraction__")
        if isinstance(text, str) and len(value) == 1:
            return Fraction(text)
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_thaw(item) for item in value]
    return value


def measure() -> Dict[str, object]:
    """The report, with the digest of what it was taken from beside it."""
    payload = dict(landscape_report())
    payload["source_digest"] = module_digest()
    return payload


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the measurements and store them beside their digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_freeze(measure()), indent=1, sort_keys=True,
                   ensure_ascii=False) + "\n",
        encoding="utf-8")
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """What is stored, whether or not it is still current."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = _thaw(json.loads(DATA_PATH.read_text(encoding="utf-8")))
    _cache = loaded if isinstance(loaded, dict) else None
    return _cache


def state() -> Dict[str, object]:
    """Present, and taken from the sources as they stand?"""
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "live_digest": live,
                "stored_digest": None, "verdict": "absent"}
    same = stored.get("source_digest") == live
    return {"present": True, "fresh": same, "live_digest": live,
            "stored_digest": stored.get("source_digest"),
            "verdict": "fresh" if same else "stale"}


def current() -> Optional[Dict[str, object]]:
    """The measurements if they still describe the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored
