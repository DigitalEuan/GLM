"""``glm_universal.reasoning.drift`` -- the prime-iteration stress test.

What this module is
-------------------
The first study in ``source_material/glm_study_findings_catalog.md`` asks the question the
Universal Binary Principle exists to answer: *does refusing floating point
actually matter, or is it a stylistic preference?*  Its instrument is a family
of rational recurrences over the odd primes,

    contractive   X_{n+1} = ((p - 1)/p) X_n - 1/p     fixed point  -1
    accumulative  X_{n+1} = ((p + 1)/p) X_n - 1/p     fixed point  +1

started at ``X_0 = 1/p``, iterated 200 steps, and run in three regimes: exact
rational arithmetic, IEEE-754 binary64, and binary64 truncated to a fixed
number of *significant decimal digits* at every step -- the study's model of an
agent-tool-memory handoff, where a number leaves the machine as printed text
and comes back parsed.

This module runs all three, and it runs them **without ever constructing a
float**.  Binary64 is modelled exactly by
:func:`~glm_universal.reasoning.mantissa.to_double` -- round to nearest, ties
to even, 53 significant bits -- so every figure below is a property of the
IEEE-754 format rather than a measurement of the interpreter that happens to be
running.  The display truncation is likewise exact: :func:`significant_round`
rounds a rational to ``d`` significant decimal digits in integer arithmetic.

What it finds
-------------
* **The contractive rule is safe and the accumulative rule is not.**  Under
  contraction the map damps each step's rounding error, so the drift never
  exceeds the regime's own truncation ceiling.  Under expansion the *first*
  rounding -- the one that stores ``1/p``, which has no finite binary
  expansion for any odd prime -- is amplified by ``((p+1)/p)**n``, and by step
  200 the double has lost every significant digit it started with.
* **Display truncation is catastrophically worse than the hardware.**  Not by
  the ratio of the truncation widths, but by that ratio *amplified*: at
  ``p = 3`` the six-digit regime ends nine orders of magnitude further from the
  truth than the lossless one.
* **Divergence is immediate under truncation.**  :func:`divergence_onset`
  locates the first step at which the drift exceeds a threshold; for the
  display regimes it is step 1 or 2 for every prime, while the lossless regime
  survives until step 46 at ``p = 3`` and never diverges at all for the larger
  primes within 200 steps.

The Lean counterpart is ``RequestProject/GLM/Mantissa.lean``: a float's orbit
under the doubling map always collapses to a fixed point, while the exact orbit
of ``1/p`` is periodic with period ``ord_2(p)`` and never does.  That is the
same loss located at its source, one step earlier than this module measures it.

Reachable from the runtime as part of ``report catalog``.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from . import mantissa as mt
from . import wobble as wb

__all__ = [
    "ODD_PRIMES", "RULES", "STEPS", "DIVERGENCE_THRESHOLD",
    "significant_round", "step_exact", "step_double",
    "closed_form", "fixed_point", "perturbation_after",
    "orbit", "final_values", "drift_row", "drift_table",
    "divergence_onset", "onset_table", "drift_report",
]

#: The primes the study iterates over.
ODD_PRIMES: Tuple[int, ...] = (3, 5, 7, 11, 13, 17, 23)

#: The two rules, by name.
RULES: Tuple[str, ...] = ("contractive", "accumulative")

#: How many steps the study runs.
STEPS: int = 200

#: The threshold at which the study calls the drift meaningful.
DIVERGENCE_THRESHOLD: Fraction = Fraction(1, 10 ** 9)


# ═════════════════════════════════════════════════════════════════════════
# 1.  DISPLAY TRUNCATION, EXACTLY
# ═════════════════════════════════════════════════════════════════════════

def significant_round(value: Fraction, digits: int) -> Fraction:
    """``value`` rounded to ``digits`` significant decimal digits, exactly.

    Integer arithmetic only: the decimal exponent is found by comparing
    against powers of ten, and the rounding is half-up on the scaled integer.
    This is what a number looks like after it has been *printed* at a fixed
    width and parsed back -- the loss the study attributes to a tool loop.
    """
    if digits < 1:
        raise ValueError("significant_round: digits must be positive")
    value = Fraction(value)
    if value == 0:
        return Fraction(0)
    sign = -1 if value < 0 else 1
    magnitude = abs(value)
    low = Fraction(10) ** (digits - 1)
    high = Fraction(10) ** digits
    shift = 0
    while magnitude * Fraction(10) ** shift < low:
        shift += 1
    while magnitude * Fraction(10) ** shift >= high:
        shift -= 1
    scaled = magnitude * Fraction(10) ** shift
    units = (2 * scaled.numerator + scaled.denominator) // (
        2 * scaled.denominator)
    return sign * Fraction(units) / Fraction(10) ** shift


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE RECURRENCE, IN THREE REGIMES
# ═════════════════════════════════════════════════════════════════════════

def _ratio(prime: int, rule: str) -> Fraction:
    if prime < 3 or prime % 2 == 0:
        raise ValueError(f"drift: {prime} is not an odd prime > 2")
    if rule == "contractive":
        return Fraction(prime - 1, prime)
    if rule == "accumulative":
        return Fraction(prime + 1, prime)
    raise ValueError(f"drift: unknown rule {rule!r}")


def step_exact(value: Fraction, prime: int, rule: str) -> Fraction:
    """One step of the recurrence, in exact rational arithmetic."""
    return _ratio(prime, rule) * value - Fraction(1, prime)


def step_double(value: Fraction, prime: int, rule: str) -> Fraction:
    """One step of the recurrence, with every operation rounded to binary64.

    The multiplication and the subtraction each round, which is what the
    hardware does; the operands are the doubles nearest ``(p +/- 1)/p`` and
    ``1/p``, which is what a program that writes the constants in source gets.
    """
    ratio = mt.to_double(_ratio(prime, rule))
    offset = mt.to_double(Fraction(1, prime))
    return mt.to_double(mt.to_double(ratio * value) - offset)


def closed_form(prime: int, rule: str, step: int) -> Fraction:
    """``X_n`` in closed form, without iterating.

    Both rules are affine, ``X_(n+1) = a X_n + b`` with ``b = -1/p``, so both
    solve exactly.  With ``a = (p-1)/p`` the fixed point is ``-1`` and

        ``X_n = -1 + ((p+1)/p) ((p-1)/p)**n``;

    with ``a = (p+1)/p`` the fixed point is ``+1`` and

        ``X_n = 1 - ((p-1)/p) ((p+1)/p)**n``.

    The accumulative form is worth reading carefully: the subtracted term
    grows without bound, so ``X_n -> -infinity``, not ``+infinity``.
    """
    if step < 0:
        raise ValueError("closed_form: step must be non-negative")
    ratio = _ratio(prime, rule)
    if rule == "contractive":
        return -1 + Fraction(prime + 1, prime) * ratio ** step
    return 1 - Fraction(prime - 1, prime) * ratio ** step


def fixed_point(prime: int, rule: str) -> Fraction:
    """The fixed point ``b / (1 - a)`` of the rule: ``-1``, or ``+1``."""
    return Fraction(-1, prime) / (1 - _ratio(prime, rule))


def perturbation_after(prime: int, rule: str, step: int,
                       offset: Fraction) -> Fraction:
    """How a perturbation of the start value shows up at step ``n``.

    The map is affine, so the difference of two trajectories obeys the
    *linear* part alone: perturbing ``X_0`` by ``d`` moves ``X_n`` by exactly
    ``a**n d``, with no cross terms and no approximation.  That is why the
    accumulative rule cannot be rescued by more precision -- it multiplies
    whatever error it is handed by ``((p+1)/p)**n``.
    """
    if step < 0:
        raise ValueError("perturbation_after: step must be non-negative")
    return _ratio(prime, rule) ** step * Fraction(offset)


def orbit(prime: int, rule: str, steps: int = STEPS, *,
          regime: str = "exact", digits: Optional[int] = None
          ) -> Tuple[Fraction, ...]:
    """The whole trajectory, ``steps + 1`` values starting at ``X_0 = 1/p``.

    ``regime`` is ``"exact"`` or ``"double"``; ``digits``, when given, applies
    :func:`significant_round` after every double step, which is the display
    regime.
    """
    if steps < 0:
        raise ValueError("orbit: steps must be non-negative")
    if regime not in ("exact", "double"):
        raise ValueError(f"orbit: unknown regime {regime!r}")
    if regime == "exact" and digits is not None:
        raise ValueError("orbit: exact arithmetic does not truncate")
    start = Fraction(1, prime)
    value = start if regime == "exact" else mt.to_double(start)
    out: List[Fraction] = [value]
    for _ in range(steps):
        if regime == "exact":
            value = step_exact(value, prime, rule)
        else:
            value = step_double(value, prime, rule)
            if digits is not None:
                value = mt.to_double(significant_round(value, digits))
        out.append(value)
    return tuple(out)


#: The regimes the study compares, as ``(label, digits)``.
_REGIMES: Tuple[Tuple[str, Optional[int]], ...] = (
    ("lossless", None), ("display6", 6), ("display4", 4))


def final_values(prime: int, rule: str, steps: int = STEPS
                 ) -> Dict[str, Fraction]:
    """The value each regime ends on after ``steps`` steps."""
    out: Dict[str, Fraction] = {
        "exact": orbit(prime, rule, steps)[-1]}
    for label, digits in _REGIMES:
        out[label] = orbit(prime, rule, steps, regime="double",
                           digits=digits)[-1]
    return out


def drift_row(prime: int, rule: str, steps: int = STEPS) -> Dict[str, object]:
    """One row of the study's drift table: the exact value and three drifts."""
    values = final_values(prime, rule, steps)
    exact = values["exact"]
    row: Dict[str, object] = {
        "prime": prime,
        "rule": rule,
        "steps": steps,
        "exact_final": exact,
    }
    row["exact_final_sci"] = wb.sci_str(exact)
    for label, _ in _REGIMES:
        row[f"{label}_final"] = values[label]
        row[f"{label}_drift"] = abs(values[label] - exact)
        row[f"{label}_drift_sci"] = wb.sci_str(abs(values[label] - exact))
    row["truncation_beats_hardware"] = (
        row["display6_drift"] >= row["lossless_drift"]        # type: ignore
        and row["display4_drift"] >= row["display6_drift"])   # type: ignore
    return row


def drift_table(primes: Sequence[int] = ODD_PRIMES, steps: int = STEPS
                ) -> Tuple[Dict[str, object], ...]:
    """The whole table: every prime, both rules, three regimes."""
    return tuple(drift_row(prime, rule, steps)
                 for prime in primes for rule in RULES)


# ═════════════════════════════════════════════════════════════════════════
# 3.  WHEN THE DRIFT BECOMES MEANINGFUL
# ═════════════════════════════════════════════════════════════════════════

def divergence_onset(prime: int, rule: str, regime_digits: Optional[int],
                     steps: int = STEPS,
                     threshold: Fraction = DIVERGENCE_THRESHOLD
                     ) -> Optional[int]:
    """The first step at which the drift exceeds ``threshold``.

    ``None`` means the regime never diverges within ``steps`` -- which is the
    honest answer for the lossless regime on the larger primes, and is
    reported as such rather than as a large number.
    """
    exact = orbit(prime, rule, steps)
    approx = orbit(prime, rule, steps, regime="double", digits=regime_digits)
    for index, (a, b) in enumerate(zip(exact, approx)):
        if abs(a - b) > threshold:
            return index
    return None


def onset_table(primes: Sequence[int] = ODD_PRIMES, steps: int = STEPS
                ) -> Tuple[Dict[str, object], ...]:
    """The onset step for every prime, rule and regime."""
    out: List[Dict[str, object]] = []
    for prime in primes:
        for rule in RULES:
            row: Dict[str, object] = {"prime": prime, "rule": rule}
            for label, digits in _REGIMES:
                row[label] = divergence_onset(prime, rule, digits, steps)
            out.append(row)
    return tuple(out)


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE REPORT
# ═════════════════════════════════════════════════════════════════════════

def drift_report(primes: Sequence[int] = ODD_PRIMES, steps: int = STEPS
                 ) -> Dict[str, object]:
    """Everything above in one call, with the two headline conclusions."""
    table = drift_table(primes, steps)
    onsets = onset_table(primes, steps)

    contractive = [row for row in table if row["rule"] == "contractive"]
    accumulative = [row for row in table if row["rule"] == "accumulative"]

    ceiling_holds = all(
        row["lossless_drift"] < Fraction(1, 10 ** 12)        # type: ignore
        and row["display6_drift"] < Fraction(1, 10 ** 5)     # type: ignore
        and row["display4_drift"] < Fraction(1, 10 ** 3)     # type: ignore
        for row in contractive)

    relative = []
    for row in accumulative:
        exact = row["exact_final"]
        if exact != 0:
            relative.append({
                "prime": row["prime"],
                "lossless_relative": abs(row["lossless_drift"] / exact),
            })

    display_immediate = all(
        row["display6"] is not None and row["display6"] <= 2
        and row["display4"] is not None and row["display4"] <= 2
        for row in onsets)
    display_exceptions = tuple(
        {"prime": row["prime"], "rule": row["rule"],
         "display6": row["display6"], "display4": row["display4"]}
        for row in onsets
        if not (row["display6"] is not None and row["display6"] <= 2
                and row["display4"] is not None and row["display4"] <= 2))

    return {
        "steps": steps,
        "primes": tuple(primes),
        "table": table,
        "onsets": onsets,
        "contractive_stays_under_its_ceiling": ceiling_holds,
        "truncation_never_helps": all(
            row["truncation_beats_hardware"] for row in table),
        "accumulative_relative_error": tuple(relative),
        "display_diverges_by_step_two": display_immediate,
        "display_onset_exceptions": display_exceptions,
        "lossless_onset_at_three": divergence_onset(3, "accumulative", None,
                                                    steps),
    }
