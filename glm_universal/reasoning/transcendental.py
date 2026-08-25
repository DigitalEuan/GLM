"""``glm_universal.reasoning.transcendental`` -- exp, log, sin, cos, and ``x^y``.

What this module closes
-----------------------
:mod:`~glm_universal.reasoning.exact_real` holds a real as a *process*: a rule
that returns, for any precision ``k``, an exact ``Fraction`` within ``2**-k``
of the value.  Until this module, that layer reached exactly as far as
``+ - * /``, integer powers, roots of any degree, and the three named
constants ``pi``, ``e`` and ``phi``.  ``sin(1)``, ``log(2)``, ``exp(1)`` and a
non-integer exponent such as ``2^pi`` were refused *by name*, and
``INFINITE_VALUES_STUDY.md`` recorded that as the largest single gap in the
value layer.

This module builds them, to the same standard as the rest: every function is a
process, every error bound is stated and paid for in exact rational
arithmetic, and **no float is constructed anywhere**.

How each bound is obtained
--------------------------
Two things are needed for each function ``f``: a way to evaluate ``f`` at a
*rational* point to any precision, and a Lipschitz-style bound that says how
precisely the argument must be known.

``exp``
    Evaluation: halve the argument until ``|b| <= 1/2``, sum the exponential
    series there (the terms fall by a factor of at least two, so the tail is
    below twice the first omitted term), then square back up.  Squaring
    multiplies the error by at most ``2M + 1`` where ``M`` bounds the values,
    and the budget is divided accordingly, so the returned bound is honest
    rather than asymptotic.
    Argument precision: ``|exp x - exp a| <= exp(max(x, a)) * |x - a|``.
``log``
    Evaluation: write ``a = f * 2**s`` with ``f`` in ``[1, 2)``; then
    ``log a = log f + s * log 2``, and both logarithms come from the ``atanh``
    series at ``t = (f - 1)/(f + 1) <= 1/3``, whose tail after ``n`` terms is
    below ``3 * t**(2n+1)``.
    Argument precision: ``|log x - log a| <= |x - a| / min(x, a)``, which needs
    a **positivity witness** ``x >= 2**-m`` -- exactly the situation division
    is in, and refused the same way when no witness is found.
``sin``, ``cos``
    Evaluation: the Taylor series at 0, whose terms alternate and eventually
    decrease, so the error is below the first omitted term.
    Argument precision: both functions are 1-Lipschitz, so one extra bit
    suffices.
``x ** y``
    ``exp(y * log x)`` for ``x > 0``.  It therefore inherits the positivity
    witness: ``2^pi`` is computable, ``0^pi`` is refused, and a negative base
    with a non-integer exponent has no real value and is refused by name.

Where it still stops
--------------------
* **A positivity witness is required for ``log`` and for a non-integer
  power.**  This is not a defect of the search: producing the witness for an
  arbitrary process would decide whether the process is zero.
* **The inverse trigonometric and inverse hyperbolic functions are not
  built** -- ``asin``, ``acos``, ``atan``, ``asinh`` and the rest are refused
  by name, exactly as the direct functions used to be.  Each needs its own
  convergent process with a stated error bound; the three above are the
  pattern to follow.
* **Cost grows with the argument.**  ``exp`` halves its argument
  ``ceil(log2 |x|)`` times and pays for each squaring, and ``sin`` of a large
  argument sums a long series in exact arithmetic.  Nothing is wrong at large
  arguments; it is simply slower, and no reduction modulo ``pi`` is attempted,
  because that reduction would itself need ``pi`` to a precision that depends
  on the argument.

The machine-checked counterparts are in
``RequestProject/GLM/Transcendental.lean``: the Lipschitz bounds this module
budgets against, the positivity witness as an equivalence, and the identity
``x ** y = exp (y * log x)`` that the power route is built on.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, Optional

from .exact_real import ExactReal, PrecisionError, _ceil_log2, _eps, from_fraction

__all__ = [
    "rational_exp_approx", "rational_log_approx", "rational_sin_approx",
    "rational_cos_approx", "log_two_approx",
    "exp", "log", "ln", "sin", "cos", "tan", "rpow",
    "positive_witness", "POSITIVE_WITNESS_DEPTH",
    "transcendental_report",
]


#: How far a value is refined in the search for a positivity witness before
#: ``log`` (and a non-integer power) is refused.  The same discipline as the
#: nonzero witness a division needs, and refused the same way.
POSITIVE_WITNESS_DEPTH: int = 96


def _ceil_int(value: Fraction) -> int:
    """``ceil(value)`` for an exact Fraction, in integer arithmetic only."""
    return -((-value.numerator) // value.denominator)


# ===========================================================================
# 1.  EVALUATION AT A RATIONAL POINT
# ===========================================================================

def _exp_small(b: Fraction, error: Fraction) -> Fraction:
    """``exp(b)`` within ``error`` for ``|b| <= 1/2``, by the series.

    With ``|b| <= 1/2`` each term is at most half the one before it, so the
    tail from any point on is below twice the first term omitted.
    """
    total = Fraction(0)
    term = Fraction(1)
    index = 0
    while True:
        total += term
        index += 1
        term = term * b / index
        if 2 * abs(term) <= error:
            return total


def rational_exp_approx(a: Fraction, k: int) -> Fraction:
    """A rational within ``2**-k`` of ``exp(a)``, for a rational ``a``.

    The argument is halved until it is at most ``1/2`` in absolute value, the
    series is summed there, and the result squared back up.  Each squaring can
    multiply the error by at most ``2M + 1``, where ``M`` bounds every value on
    the way, so the series is asked for ``2**-k / (2M + 1)**r`` and the final
    bound is met exactly.
    """
    if not isinstance(a, Fraction):
        raise TypeError("rational_exp_approx: the argument must be a Fraction")
    if k < 0:
        raise PrecisionError("rational_exp_approx: precision must be >= 0")
    eps = _eps(k)

    reduced = a
    halvings = 0
    while abs(reduced) > Fraction(1, 2):
        reduced = reduced / 2
        halvings += 1

    # ``M`` bounds exp at every stage, since |a/2**j| <= |a| and e < 3.
    bound = 3 ** (_ceil_int(abs(a)) + 1)
    budget = eps / (2 * bound + 1) ** halvings
    value = _exp_small(reduced, budget)
    for _ in range(halvings):
        value = value * value
    return value


def log_two_approx(k: int) -> Fraction:
    """A rational within ``2**-k`` of ``log 2``, by ``2 * atanh(1/3)``."""
    return _atanh_series(Fraction(1, 3), _eps(k))


def _atanh_series(t: Fraction, error: Fraction) -> Fraction:
    """``2 * atanh(t)`` within ``error``, for ``0 <= t <= 1/3``.

    The tail after ``n`` terms is ``2 * sum_{j >= n} t**(2j+1)/(2j+1)``, which
    is below ``2 * t**(2n+1) / (1 - t**2) <= 3 * t**(2n+1)`` at ``t <= 1/3``.
    """
    if not 0 <= t <= Fraction(1, 3):
        raise ValueError("_atanh_series: t must lie in [0, 1/3]")
    total = Fraction(0)
    index = 0
    while True:
        power = 2 * index + 1
        if 3 * t ** power <= error:
            return 2 * total
        total += t ** power / power
        index += 1


def rational_log_approx(a: Fraction, k: int) -> Fraction:
    """A rational within ``2**-k`` of ``log a``, for a rational ``a > 0``."""
    if not isinstance(a, Fraction):
        raise TypeError("rational_log_approx: the argument must be a Fraction")
    if a <= 0:
        raise ValueError(f"rational_log_approx: log of {a}, which is not "
                         f"positive")
    if k < 0:
        raise PrecisionError("rational_log_approx: precision must be >= 0")
    eps = _eps(k)

    # a = mantissa * 2**shift with 1 <= mantissa < 2, by bit lengths.
    shift = a.numerator.bit_length() - a.denominator.bit_length()
    mantissa = a / Fraction(2) ** shift
    while mantissa >= 2:
        mantissa /= 2
        shift += 1
    while mantissa < 1:
        mantissa *= 2
        shift -= 1

    t = (mantissa - 1) / (mantissa + 1)          # in [0, 1/3]
    log_mantissa = _atanh_series(t, eps / 2)
    if shift == 0:
        return log_mantissa
    log_two = _atanh_series(Fraction(1, 3), eps / (2 * abs(shift)))
    return log_mantissa + shift * log_two


def _sin_cos_series(a: Fraction, error: Fraction, *, cosine: bool) -> Fraction:
    """``sin a`` or ``cos a`` within ``error``, by the alternating Taylor series.

    The bound "error below the first omitted term" holds once the terms are
    decreasing, which is why the loop checks that condition before it stops.
    """
    total = Fraction(0)
    term = Fraction(1) if cosine else a
    index = 0
    while True:
        # The next term multiplies by -a**2 / ((p+1)(p+2)) where p is the
        # current power; terms decrease once that factor is below 1.
        power = 2 * index + (0 if cosine else 1)
        factor = a * a / ((power + 1) * (power + 2))
        if abs(term) <= error and abs(factor) <= 1:
            return total
        total += term if index % 2 == 0 else -term
        term = term * factor
        index += 1


def rational_sin_approx(a: Fraction, k: int) -> Fraction:
    """A rational within ``2**-k`` of ``sin a``, for a rational ``a``."""
    if not isinstance(a, Fraction):
        raise TypeError("rational_sin_approx: the argument must be a Fraction")
    if k < 0:
        raise PrecisionError("rational_sin_approx: precision must be >= 0")
    return _sin_cos_series(a, _eps(k), cosine=False)


def rational_cos_approx(a: Fraction, k: int) -> Fraction:
    """A rational within ``2**-k`` of ``cos a``, for a rational ``a``."""
    if not isinstance(a, Fraction):
        raise TypeError("rational_cos_approx: the argument must be a Fraction")
    if k < 0:
        raise PrecisionError("rational_cos_approx: precision must be >= 0")
    return _sin_cos_series(a, _eps(k), cosine=True)


# ===========================================================================
# 2.  THE PROCESSES
# ===========================================================================

def exp(x: ExactReal) -> ExactReal:
    """``exp(x)`` as a process.

    ``|exp x - exp a| <= exp(max(x, a)) * |x - a|``, so the argument is asked
    for enough extra bits to absorb that factor, and the rational evaluation
    is asked for the remaining half of the budget.
    """
    if not isinstance(x, ExactReal):
        raise TypeError("exp: the argument must be an ExactReal")

    def approx(k: int) -> Fraction:
        # exp(|x| + 1) <= 3 ** (ceil(|x|) + 1) bounds the derivative on the
        # whole interval the approximation can lie in.
        lipschitz = Fraction(3) ** (_ceil_int(x.bound()) + 1)
        inner = k + 1 + _ceil_log2(lipschitz)
        return rational_exp_approx(x.at(inner), k + 1)

    return ExactReal(approx, f"exp({x.name})")


def positive_witness(x: ExactReal,
                     max_exponent: int = POSITIVE_WITNESS_DEPTH
                     ) -> Optional[int]:
    """An exponent ``m`` with ``x >= 2**-m``, or ``None`` if none is found.

    ``None`` is the honest answer at a value the process has not yet moved
    above zero: it may be zero or negative, and no finite refinement settles
    that.  The caller is expected to refuse rather than take a logarithm.
    """
    for m in range(0, int(max_exponent) + 1):
        a = x.at(m + 2)
        if a > _eps(m) + _eps(m + 2):
            return m
    return None


def log(x: ExactReal, positive_exponent: Optional[int] = None,
        depth: int = POSITIVE_WITNESS_DEPTH) -> ExactReal:
    """``log(x)`` (natural logarithm) as a process, for ``x > 0``.

    A witness ``m`` with ``x >= 2**-m`` is required.  If none is supplied one
    is searched for to ``depth``; if the value has not moved above zero by
    then, the logarithm is refused with the depth named -- the argument may be
    zero, and no finite refinement decides that.
    """
    if not isinstance(x, ExactReal):
        raise TypeError("log: the argument must be an ExactReal")
    if x.exact is not None and x.exact <= 0:
        raise ValueError(f"log: log of {x.exact}, which is not positive")
    if positive_exponent is None:
        positive_exponent = positive_witness(x, depth)
    if positive_exponent is None:
        raise PrecisionError(
            f"log: {x.name} has not moved above zero by 2**-{depth}, so "
            f"log({x.name}) cannot be computed -- the argument may be zero or "
            f"negative, and no finite refinement decides that")
    m = int(positive_exponent)
    if m < 0:
        raise PrecisionError("log: witness exponent must be >= 0")

    def approx(k: int) -> Fraction:
        inner = k + m + 2
        a = x.at(inner)
        if a <= _eps(m) / 2:
            raise PrecisionError(
                f"log: {x.name} >= 2**-{m} is contradicted by the "
                f"approximation {a}")
        return rational_log_approx(a, k + 1)

    return ExactReal(approx, f"log({x.name})")


#: ``ln`` is the same function; both spellings are the natural logarithm.
ln = log


def sin(x: ExactReal) -> ExactReal:
    """``sin(x)`` as a process.  ``sin`` is 1-Lipschitz, so one extra bit."""
    if not isinstance(x, ExactReal):
        raise TypeError("sin: the argument must be an ExactReal")
    return ExactReal(lambda k: rational_sin_approx(x.at(k + 1), k + 1),
                     f"sin({x.name})")


def cos(x: ExactReal) -> ExactReal:
    """``cos(x)`` as a process.  ``cos`` is 1-Lipschitz, so one extra bit."""
    if not isinstance(x, ExactReal):
        raise TypeError("cos: the argument must be an ExactReal")
    return ExactReal(lambda k: rational_cos_approx(x.at(k + 1), k + 1),
                     f"cos({x.name})")


def tan(x: ExactReal, depth: int = POSITIVE_WITNESS_DEPTH) -> ExactReal:
    """``tan(x) = sin(x)/cos(x)``, refused where the cosine has not left zero.

    The refusal is the division's, not a special case: near an odd multiple of
    ``pi/2`` no finite refinement shows the cosine is nonzero.
    """
    from .exact_real import nonzero_witness

    numerator, denominator = sin(x), cos(x)
    witness = nonzero_witness(denominator, depth)
    if witness is None:
        raise PrecisionError(
            f"tan: cos({x.name}) has not moved away from zero by "
            f"2**-{depth}, so tan({x.name}) cannot be computed -- the "
            f"argument may be an odd multiple of pi/2")
    return ExactReal((numerator * denominator.reciprocal(witness)).approx,
                     f"tan({x.name})")


def rpow(base: ExactReal, exponent: ExactReal,
         depth: int = POSITIVE_WITNESS_DEPTH) -> ExactReal:
    """``base ** exponent`` for a positive base and any real exponent.

    Computed as ``exp(exponent * log base)``, which is what the power *is* for
    a positive base -- machine-checked as ``Real.rpow_def_of_pos``.  A base
    that has not moved above zero is refused, with the depth named.
    """
    if not isinstance(base, ExactReal) or not isinstance(exponent, ExactReal):
        raise TypeError("rpow: both arguments must be ExactReal")
    if base.exact is not None and base.exact == 1:
        return from_fraction(Fraction(1))
    return exp(exponent * log(base, None, depth))


# ===========================================================================
# 3.  THE REPORT
# ===========================================================================

def transcendental_report() -> Dict[str, object]:
    """Recompute everything this module claims, on demand.

    Each value is checked against an identity it must satisfy, so the report
    is a test of the implementation and not a printout of it.
    """
    from . import real_expr

    one = from_fraction(Fraction(1))
    two = from_fraction(Fraction(2))
    half = from_fraction(Fraction(1, 2))

    exp_one = exp(one)
    log_two = log(two)
    sin_one, cos_one = sin(one), cos(one)

    # exp(1) is e, log(2) inverts exp, sin^2 + cos^2 = 1, and 2**pi is the
    # power route: each is checked, not asserted.
    from .exact_real import e as euler, pi as pi_const
    e_gap = abs(exp_one.at(80) - euler().at(80))
    log_round_trip = abs(exp(log_two).at(60) - 2)
    pythagoras = abs((sin_one * sin_one + cos_one * cos_one).at(60) - 1)
    two_to_pi = rpow(two, pi_const())
    # 2**pi = exp(pi log 2), so it must agree with the same value written
    # through the grammar.
    grammar_two_to_pi = real_expr.parse_expression("2^pi")
    power_agreement = abs(two_to_pi.at(60) - grammar_two_to_pi.at(60))
    cube_root_two_ways = abs(real_expr.parse_expression("2^(1/3)").at(60)
                             - real_expr.parse_expression("root(3, 2)").at(60))

    refusals = {}
    for text in ("log(0)", "log(1-1)", "asin(1)", "atan(1)", "0^pi",
                 "(0-1)^pi"):
        try:
            real_expr.parse_expression(text, depth=24).at(16)
            refusals[text] = "accepted"
        except (real_expr.ExpressionError, PrecisionError, ValueError,
                ZeroDivisionError) as error:
            refusals[text] = type(error).__name__

    return {
        "exp_1_decimal_20": exp_one.decimal(20),
        "exp_1_is_e": e_gap <= Fraction(1, 2 ** 78),
        "log_2_decimal_20": log_two.decimal(20),
        "log_inverts_exp": log_round_trip <= Fraction(1, 2 ** 58),
        "sin_1_decimal_20": sin_one.decimal(20),
        "cos_1_decimal_20": cos_one.decimal(20),
        "tan_1_decimal_20": tan(one).decimal(20),
        "pythagorean_identity": pythagoras <= Fraction(1, 2 ** 58),
        "sin_half_below_half": sin(half).at(40) < Fraction(1, 2),
        "two_to_the_pi_decimal_20": two_to_pi.decimal(20),
        "power_agrees_with_grammar": power_agreement <= Fraction(1, 2 ** 58),
        "fractional_power_is_the_root": cube_root_two_ways <= Fraction(1, 2 ** 58),
        "positive_witness_depth": POSITIVE_WITNESS_DEPTH,
        "witness_for_2": positive_witness(two),
        "witness_for_a_difference_that_is_zero": positive_witness(
            two - two, 24),
        "refusals": refusals,
    }
