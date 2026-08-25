"""``glm_universal.reasoning.exact_real`` -- irrational targets, exactly.

What this module is
-------------------
Every carrier in the GLM is a 24-tuple of exact rationals, and no tuple of
rationals is ``sqrt(2)``.  That is not a defect of the encoding; it is a
theorem about countable representations, machine-checked in this repository as
``GLM.Info.no_countable_layer_lossless`` (``RequestProject/GLM/Irrational.lean``).
Any view space the machine can hold -- a carrier, a digit stack of any depth, a
trajectory of any fixed length -- conflates uncountably many real targets.

The way through is not a bigger carrier but a **process**.  A real number is
represented here by a function that produces, for each requested precision
``k``, a rational within ``2**-k`` of it:

    x : k |-> Fraction with |x(k) - x| <= 2**-k

That is the whole representation.  Addition, subtraction, multiplication,
reciprocal and square root of such processes are again such processes, and the
precision bookkeeping is carried out exactly, so no float is constructed
anywhere in this module and no result is ever "about right".

Two operational bridges to the rest of the GLM
----------------------------------------------
``surrogate(x, n)``
    the target seen at dyadic level ``n``: ``floor(x * 2**n) / 2**n``.  This is
    the rational carrier that level ``n`` of the tower actually holds -- the
    machine-checked ``GLM.Info.surrogate``.  Every level is *true of the
    surrogate*, and every surrogate is exposed by some higher level.
``DeltaSigma``
    the dynamic carrier of the study: a one-bit quantiser with an exact error
    accumulator, whose time average after ``N`` ticks is a rational ``k/N``
    within ``1/N`` of the target (``GLM.Info.dsAverage_error_le``), and whose
    infinite trajectory determines the target uniquely
    (``GLM.Info.ds_target_unique``).  Both statements are proved, not sampled;
    this module is their executable side.

Where it breaks, stated plainly
-------------------------------
* **Equality of two processes is undecidable.**  :func:`compare` returns
  ``0`` for "indistinguishable at the precision asked for", never for "equal".
  :func:`decide_equal` returns ``None`` in that case rather than guessing.
  This is the one capability the representation genuinely does not have, and
  the capability probes record it as a boundary rather than hiding it.
* **Reciprocal needs a witness.**  ``1/x`` is computable only from a proof
  that ``x`` is bounded away from zero; the caller supplies the exponent, and
  a wrong witness raises rather than silently returning nonsense.
* **A trajectory of length N carries log2(N+1) bits and no more.**  The
  resolution grows with time, and the growth is bounded exactly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from ..substrate import golay_decode
from ..substrate.mog import GOLAY_MASKS

__all__ = [
    "ExactReal", "PrecisionError",
    "from_fraction", "parse_real", "KNOWN_NOTATIONS", "sqrt", "rational_sqrt_approx", "pi", "e", "phi",
    "compare", "decide_equal", "sign",
    "surrogate", "rational_surrogate", "surrogate_sequence", "continued_fraction", "convergents",
    "DeltaSigma", "real_delta_sigma_average", "mask_target", "delta_sigma_bits", "delta_sigma_average",
    "delta_sigma_error", "golay_delta_sigma", "trajectory_stats",
    "real_carrier", "exact_real_report",
]


class PrecisionError(ValueError):
    """Raised when a request cannot be met exactly at the precision asked."""


def _check_exact(value, where: str) -> Fraction:
    """Refuse a float outright; coerce ints and Fractions."""
    if isinstance(value, float):
        raise TypeError(f"{where}: float is not an exact value")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    raise TypeError(f"{where}: expected int or Fraction, got {type(value)!r}")


def _ceil_log2(value: Fraction) -> int:
    """The least ``j >= 0`` with ``2**j >= value``.  Integer arithmetic only."""
    j = 0
    while Fraction(2 ** j) < value:
        j += 1
    return j


def _eps(k: int) -> Fraction:
    """``2**-k`` as an exact Fraction, for any integer ``k``."""
    return Fraction(1, 2 ** k) if k >= 0 else Fraction(2 ** (-k))


# ===========================================================================
# 1.  THE REPRESENTATION
# ===========================================================================

@dataclass(frozen=True)
class ExactReal:
    """A real number as a convergent process of exact rationals.

    ``approx(k)`` must return a :class:`~fractions.Fraction` within ``2**-k``
    of the represented value, for every ``k >= 0``.  Nothing else is stored:
    the value itself is never held, because in general it cannot be.
    """

    approx: Callable[[int], Fraction]
    name: str = "x"
    #: Set when the process is a rational known exactly, which lets the tower
    #: read its grid position without an interval argument.
    exact: Optional[Fraction] = None

    # -- evaluation --------------------------------------------------------

    def at(self, k: int) -> Fraction:
        """The rational approximation guaranteed within ``2**-k``."""
        if not isinstance(k, int) or isinstance(k, bool):
            raise TypeError("ExactReal.at: precision must be an int")
        if k < 0:
            raise PrecisionError("ExactReal.at: precision must be >= 0")
        value = self.approx(k)
        if isinstance(value, int):
            value = Fraction(value)
        if not isinstance(value, Fraction):
            raise TypeError(
                f"ExactReal.at: {self.name} produced {type(value)!r}, "
                f"not a Fraction")
        return value

    def bound(self) -> Fraction:
        """An exact upper bound for ``|x|``."""
        return abs(self.at(0)) + 1

    # -- arithmetic --------------------------------------------------------

    def __add__(self, other: "ExactReal") -> "ExactReal":
        other = _as_real(other)
        combined = (None if self.exact is None or other.exact is None
                    else self.exact + other.exact)
        return ExactReal(lambda k: self.at(k + 1) + other.at(k + 1),
                         f"({self.name} + {other.name})", combined)

    __radd__ = __add__

    def __neg__(self) -> "ExactReal":
        return ExactReal(lambda k: -self.at(k), f"(-{self.name})",
                         None if self.exact is None else -self.exact)

    def __sub__(self, other: "ExactReal") -> "ExactReal":
        return self + (-_as_real(other))

    def __rsub__(self, other) -> "ExactReal":
        return _as_real(other) + (-self)

    def __mul__(self, other: "ExactReal") -> "ExactReal":
        other = _as_real(other)

        def approx(k: int) -> Fraction:
            # |ab - a'b'| <= |a||b - b'| + |b'||a - a'|, and both errors are
            # taken below 2**-(k+1+j) with 2**j >= |a| + |b| + 1.
            scale = self.bound() + other.bound() + 1
            inner = k + 1 + _ceil_log2(scale)
            return self.at(inner) * other.at(inner)

        combined = (None if self.exact is None or other.exact is None
                    else self.exact * other.exact)
        return ExactReal(approx, f"({self.name} * {other.name})", combined)

    __rmul__ = __mul__

    def reciprocal(self, nonzero_exponent: int) -> "ExactReal":
        """``1/x``, given a witness ``m`` with ``|x| >= 2**-m``.

        The witness is checked as far as it can be: if the approximations
        contradict it, :class:`PrecisionError` is raised rather than a wrong
        answer returned.
        """
        m = int(nonzero_exponent)
        if m < 0:
            raise PrecisionError("reciprocal: witness exponent must be >= 0")

        def approx(k: int) -> Fraction:
            inner = k + 2 * m + 2
            a = self.at(inner)
            if abs(a) <= _eps(m) / 2:
                raise PrecisionError(
                    f"reciprocal: |{self.name}| >= 2**-{m} is contradicted "
                    f"by the approximation {a}")
            return 1 / a

        return ExactReal(approx, f"(1/{self.name})",
                         None if not self.exact else 1 / self.exact)

    def __truediv__(self, other) -> "ExactReal":
        if isinstance(other, (int, Fraction)):
            q = _check_exact(other, "ExactReal.__truediv__")
            if q == 0:
                raise ZeroDivisionError("ExactReal.__truediv__: division by 0")
            shift = _ceil_log2(abs(1 / q))
            return ExactReal(lambda k: self.at(k + shift) / q,
                             f"({self.name}/{q})",
                             None if self.exact is None else self.exact / q)
        raise TypeError("ExactReal.__truediv__: use reciprocal() with a "
                        "nonzero witness to divide by a process")

    # -- readouts ----------------------------------------------------------

    def decimal(self, places: int) -> str:
        """A decimal string, correctly truncated -- never rounded by float."""
        if places < 0:
            raise PrecisionError("ExactReal.decimal: places must be >= 0")
        # 2**-k <= 10**-(places+2) guarantees the digits shown are settled to
        # within one unit in the last place printed.  The exponent is found by
        # a bit-length, so no float is constructed.
        k = (10 ** (places + 2)).bit_length() + 1
        value = self.at(k)
        scaled = value * 10 ** places
        whole = scaled.numerator // scaled.denominator
        sign_str = "-" if whole < 0 else ""
        digits = str(abs(whole)).rjust(places + 1, "0")
        if places == 0:
            return sign_str + digits
        return f"{sign_str}{digits[:-places]}.{digits[-places:]}"

    def __repr__(self) -> str:  # pragma: no cover - display only
        return f"ExactReal({self.name})"


def _as_real(value) -> ExactReal:
    if isinstance(value, ExactReal):
        return value
    return from_fraction(_check_exact(value, "ExactReal"))


# ===========================================================================
# 2.  CONSTRUCTORS
# ===========================================================================

def from_fraction(q) -> ExactReal:
    """A rational, as a (constant) process.  Exact at every precision."""
    value = _check_exact(q, "from_fraction")
    return ExactReal(lambda _k: value, str(value), value)


def rational_sqrt_approx(q: Fraction, k: int) -> Fraction:
    """A rational within ``2**-k`` of ``sqrt(q)`` for ``q >= 0``.

    Uses integer square roots only: ``isqrt(floor(q * 4**k)) / 2**k``.  No
    float and no iteration limit.
    """
    q = _check_exact(q, "rational_sqrt_approx")
    if q < 0:
        raise ValueError("rational_sqrt_approx: negative radicand")
    if k < 0:
        raise PrecisionError("rational_sqrt_approx: precision must be >= 0")
    scaled = q * 4 ** k
    floor_scaled = scaled.numerator // scaled.denominator
    return Fraction(math.isqrt(floor_scaled), 2 ** k)


def sqrt(value) -> ExactReal:
    """The square root of a non-negative rational or process."""
    if isinstance(value, ExactReal):
        def approx(k: int) -> Fraction:
            # |sqrt(x) - sqrt(a)| <= sqrt(|x - a|); take |x - a| <= 2**-(2k+2).
            a = value.at(2 * k + 2)
            if a < 0:
                a = Fraction(0)
            return rational_sqrt_approx(a, k + 1)
        return ExactReal(approx, f"sqrt({value.name})")
    q = _check_exact(value, "sqrt")
    if q < 0:
        raise ValueError(f"sqrt: negative radicand {q}")
    return ExactReal(lambda k: rational_sqrt_approx(q, k), f"sqrt({q})")


def _iroot(value: int, degree: int) -> int:
    """``floor(value ** (1/degree))`` for ``value >= 0``, in integers only."""
    if value < 0:
        raise ValueError("_iroot: negative radicand")
    if degree < 1:
        raise ValueError("_iroot: degree must be >= 1")
    if degree == 1 or value < 2:
        return value
    if degree == 2:
        return math.isqrt(value)
    # Newton on integers, started above the root so the iteration decreases.
    guess = 1 << (value.bit_length() // degree + 1)
    while True:
        nxt = ((degree - 1) * guess + value // guess ** (degree - 1)) // degree
        if nxt >= guess:
            break
        guess = nxt
    while guess ** degree > value:
        guess -= 1
    while (guess + 1) ** degree <= value:
        guess += 1
    return guess


def rational_nth_root_approx(q: Fraction, degree: int, k: int) -> Fraction:
    """A rational within ``2**-k`` of ``q ** (1/degree)`` for ``q >= 0``.

    Integer roots only -- ``_iroot(floor(q * 2**(degree*k)), degree) / 2**k``,
    which is below the true root by less than one unit in the last place.
    """
    q = _check_exact(q, "rational_nth_root_approx")
    if q < 0:
        raise ValueError("rational_nth_root_approx: negative radicand")
    if degree < 1:
        raise ValueError("rational_nth_root_approx: degree must be >= 1")
    if k < 0:
        raise PrecisionError("rational_nth_root_approx: precision must be >= 0")
    scaled = q * 2 ** (degree * k)
    return Fraction(_iroot(scaled.numerator // scaled.denominator, degree),
                    2 ** k)


def nth_root(value, degree: int) -> ExactReal:
    """The ``degree``-th root of a non-negative rational or process.

    ``|x**(1/n) - a**(1/n)| <= |x - a|**(1/n)`` for non-negative ``x`` and
    ``a``, so an approximation of the radicand within ``2**-n(k+1)`` gives the
    root within ``2**-(k+1)``; one more bit covers the truncation of the
    integer root itself.
    """
    degree = int(degree)
    if degree < 1:
        raise ValueError("nth_root: degree must be >= 1")
    if degree == 2:
        return sqrt(value)
    if isinstance(value, ExactReal):
        def approx(k: int) -> Fraction:
            a = value.at(degree * (k + 2))
            if a < 0:
                a = Fraction(0)
            return rational_nth_root_approx(a, degree, k + 2)
        return ExactReal(approx, f"root({degree}, {value.name})")
    q = _check_exact(value, "nth_root")
    if q < 0:
        raise ValueError("nth_root: negative radicand")
    return ExactReal(lambda k: rational_nth_root_approx(q, degree, k + 1),
                     f"root({degree}, {q})")


def nonzero_witness(x: ExactReal, max_exponent: int = 96) -> Optional[int]:
    """An exponent ``m`` with ``|x| >= 2**-m``, or ``None`` if none is found.

    ``None`` is the honest answer at a value the process has not yet moved
    away from zero: it may be zero, and no finite amount of refinement can
    settle that.  The caller is expected to say so rather than divide.
    """
    for m in range(0, int(max_exponent) + 1):
        a = abs(x.at(m + 2))
        if a > _eps(m) + _eps(m + 2):
            return m
    return None


#: The notations :func:`parse_real` understands, for the runtime's help text.
KNOWN_NOTATIONS: Tuple[str, ...] = (
    "sqrt(<rational>)", "pi", "e", "phi", "<integer>", "<numerator>/<denominator>",
    "and any arithmetic combination of those, e.g. (1+sqrt(5))/2 or pi/4",
)


def parse_real(notation: str) -> ExactReal:
    """Turn a written notation into a process.

    Understands ``sqrt(2)``, ``sqrt(7/3)``, ``pi``, ``e``, ``phi`` and any
    rational literal.  Anything else raises :class:`ValueError` naming what is
    understood -- a notation is never quietly reinterpreted as something else.
    """
    text = str(notation).strip().lower().replace(" ", "")
    if text in ("pi", "π"):
        return pi()
    if text in ("e", "euler"):
        return e()
    if text in ("phi", "golden", "goldenratio", "φ"):
        return phi()
    if text.startswith("sqrt(") and text.endswith(")"):
        inner = text[5:-1]
        try:
            radicand = Fraction(inner)
        except (ValueError, ZeroDivisionError):
            radicand = None          # not a bare radicand: try the grammar
        if radicand is not None:
            if radicand < 0:
                raise ValueError(
                    f"parse_real: {notation!r} has a negative radicand")
            return sqrt(radicand)
    try:
        return from_fraction(Fraction(text))
    except (ValueError, ZeroDivisionError):
        pass
    # Anything else is handed to the expression grammar, which reads written
    # arithmetic over these same processes.  Its refusals are more specific
    # than the one below, so they are passed straight back to the caller.
    from . import real_expr
    try:
        return real_expr.parse_expression(str(notation))
    except real_expr.ExpressionError as error:
        raise ValueError(
            f"parse_real: {notation!r} is not a notation this module reads; "
            f"it understands {', '.join(KNOWN_NOTATIONS)}.  The expression "
            f"grammar stopped with: {error}") from None


def _arctan_unit(n: int, k: int) -> Fraction:
    """``arctan(1/n)`` within ``2**-k``, by its alternating series."""
    total = Fraction(0)
    term_index = 0
    limit = _eps(k)
    while True:
        power = 2 * term_index + 1
        term = Fraction(1, n ** power * power)
        if term <= limit:            # alternating series: tail <= first term
            break
        total += term if term_index % 2 == 0 else -term
        term_index += 1
    return total


def pi(name: str = "pi") -> ExactReal:
    """``pi`` by Machin's formula, in exact rational arithmetic."""
    def approx(k: int) -> Fraction:
        inner = k + 6                # 16 + 4 = 20 < 2**5 of error inflation
        return 16 * _arctan_unit(5, inner) - 4 * _arctan_unit(239, inner)
    return ExactReal(approx, name)


def e(name: str = "e") -> ExactReal:
    """Euler's number, by the exponential series."""
    def approx(k: int) -> Fraction:
        total = Fraction(0)
        term = Fraction(1)
        index = 0
        limit = _eps(k + 1)
        while True:
            total += term
            index += 1
            term = term / index
            # The tail of sum 1/n! from index on is below 2 * term.
            if 2 * term <= limit:
                break
        return total
    return ExactReal(approx, name)


def phi(name: str = "phi") -> ExactReal:
    """The golden ratio ``(1 + sqrt 5)/2``."""
    root = sqrt(Fraction(5))
    return ExactReal(lambda k: (1 + root.at(k + 1)) / 2, name)


# ===========================================================================
# 3.  COMPARISON -- AND THE BOUNDARY IT MEETS
# ===========================================================================

def compare(a: ExactReal, b: ExactReal, k: int) -> int:
    """``-1``, ``0`` or ``+1``: the order of ``a`` and ``b`` at precision ``k``.

    ``0`` means **undecided at this precision**, not "equal".  Two distinct
    processes always separate at some finite ``k`` (this is the executable
    side of ``GLM.Info.dyadicR_separates``), but no ``k`` is known in advance,
    and for equal processes none exists.
    """
    left, right = a.at(k + 1), b.at(k + 1)
    slack = _eps(k)
    if left - right > slack:
        return 1
    if right - left > slack:
        return -1
    return 0


def decide_equal(a: ExactReal, b: ExactReal, k: int) -> Optional[bool]:
    """``False`` when the two are known apart by precision ``k``; else ``None``.

    Never returns ``True``: equality of processes is not decidable, and the
    honest answer at any finite precision is "not yet distinguished".
    """
    return False if compare(a, b, k) != 0 else None


def sign(x: ExactReal, k: int) -> int:
    """The sign of ``x`` at precision ``k``; ``0`` means undecided."""
    return compare(x, from_fraction(Fraction(0)), k)


# ===========================================================================
# 4.  THE DYADIC TOWER, OPERATIONALLY
# ===========================================================================

def surrogate(x: ExactReal, n: int) -> Fraction:
    """The rational carrier level ``n`` of the tower holds for ``x``.

    ``floor(x * 2**n) / 2**n``, computed from an approximation fine enough
    that the floor is settled.  Raises rather than guessing when the target
    sits exactly on a level-``n`` grid point and no finite approximation can
    settle which side of it the value lies.
    """
    if n < 0:
        raise PrecisionError("surrogate: level must be >= 0")
    if x.exact is not None:
        return rational_surrogate(x.exact, n)
    for extra in range(2, 64):
        k = n + extra
        a = x.at(k)
        lo, hi = a - _eps(k), a + _eps(k)
        lo_floor = (lo * 2 ** n).numerator // (lo * 2 ** n).denominator
        hi_floor = (hi * 2 ** n).numerator // (hi * 2 ** n).denominator
        if lo_floor == hi_floor:
            return Fraction(lo_floor, 2 ** n)
    raise PrecisionError(
        f"surrogate: level {n} of {x.name} is not settled after 64 "
        f"refinements -- the target is on, or indistinguishably near, a grid "
        f"point")


def rational_surrogate(q: Fraction, n: int) -> Fraction:
    """The level-``n`` stand-in for a rational: ``floor(q * 2**n)/2**n``."""
    q = _check_exact(q, "rational_surrogate")
    scaled = q * 2 ** n
    return Fraction(scaled.numerator // scaled.denominator, 2 ** n)


def surrogate_sequence(x: ExactReal, levels: int) -> Tuple[Fraction, ...]:
    """The tower's stand-ins for ``x`` at levels ``0 .. levels - 1``."""
    return tuple(surrogate(x, n) for n in range(levels))


def continued_fraction(q: Fraction, depth: int) -> Tuple[int, ...]:
    """The (finite) continued-fraction expansion of a rational, truncated."""
    q = _check_exact(q, "continued_fraction")
    terms: List[int] = []
    for _ in range(depth):
        whole = q.numerator // q.denominator
        terms.append(whole)
        rest = q - whole
        if rest == 0:
            break
        q = 1 / rest
    return tuple(terms)


def convergents(terms: Sequence[int]) -> Tuple[Fraction, ...]:
    """The convergents of a continued fraction, exactly."""
    out: List[Fraction] = []
    p_prev, p = 0, 1
    q_prev, q = 1, 0
    for a in terms:
        p_prev, p = p, a * p + p_prev
        q_prev, q = q, a * q + q_prev
        out.append(Fraction(p, q))
    return tuple(out)


# ===========================================================================
# 5.  THE DYNAMIC CARRIER
# ===========================================================================

@dataclass
class DeltaSigma:
    """A first-order delta-sigma modulator, in exact arithmetic.

    The recurrence is the one proved in ``RequestProject/GLM/DeltaSigma.lean``::

        state_0     = 0
        bit_n       = 1 if 1 <= state_n + target else 0
        state_(n+1) = state_n + target - bit_n

    with ``target`` in ``[0, 1)``.  Nothing is random: the whole trajectory is
    a function of the target.  The state never leaves ``[0, 1)``
    (``GLM.Info.dsState_mem_Ico``), so the running average of the bits is
    within ``1/N`` of the target after ``N`` ticks
    (``GLM.Info.dsAverage_error_le``).
    """

    target: Fraction
    state: Fraction = Fraction(0)
    ticks: int = 0
    emitted: int = 0

    def __post_init__(self) -> None:
        self.target = _check_exact(self.target, "DeltaSigma")
        if not (0 <= self.target < 1):
            raise ValueError("DeltaSigma: target must lie in [0, 1)")

    def tick(self) -> int:
        """Emit one bit and update the accumulator."""
        bit = 1 if self.state + self.target >= 1 else 0
        self.state = self.state + self.target - bit
        self.ticks += 1
        self.emitted += bit
        return bit

    def run(self, steps: int) -> Tuple[int, ...]:
        return tuple(self.tick() for _ in range(steps))

    @property
    def average(self) -> Fraction:
        if self.ticks == 0:
            raise PrecisionError("DeltaSigma.average: no ticks yet")
        return Fraction(self.emitted, self.ticks)

    @property
    def error(self) -> Fraction:
        return abs(self.average - self.target)


def delta_sigma_bits(target, steps: int) -> Tuple[int, ...]:
    """The first ``steps`` bits of the modulator chasing ``target``."""
    return DeltaSigma(_check_exact(target, "delta_sigma_bits")).run(steps)


def delta_sigma_average(target, steps: int) -> Fraction:
    """The time average after ``steps`` ticks: an exact rational ``k/steps``."""
    modulator = DeltaSigma(_check_exact(target, "delta_sigma_average"))
    modulator.run(steps)
    return modulator.average


def delta_sigma_error(target, steps: int) -> Fraction:
    """``|average - target|``, exactly.  Bounded by ``1/steps``."""
    modulator = DeltaSigma(_check_exact(target, "delta_sigma_error"))
    modulator.run(steps)
    return modulator.error


def real_delta_sigma_average(x: ExactReal, steps: int) -> Fraction:
    """Run the modulator on a *process* rather than on a rational target.

    The target is pinned to a rational fine enough that the whole run is
    unaffected: ``2**-k`` below ``1/(2 * steps)`` cannot change any of the
    ``steps`` quantiser decisions by more than the final ``1/steps`` bound.
    """
    if steps <= 0:
        raise PrecisionError("real_delta_sigma_average: steps must be > 0")
    k = 2 * steps.bit_length() + 4
    target = x.at(k)
    if not (0 <= target < 1):
        raise ValueError("real_delta_sigma_average: target must lie in [0, 1)")
    return delta_sigma_average(target, steps)


# -- the 24-dimensional modulator, on the real Golay code -------------------

def _mask_of(bits: Sequence[int]) -> int:
    mask = 0
    for index, bit in enumerate(bits):
        if bit:
            mask |= 1 << (23 - index)
    return mask


def _bits_of(mask: int) -> Tuple[int, ...]:
    return tuple((mask >> (23 - index)) & 1 for index in range(24))


def mask_target(mask: int) -> Tuple[Fraction, ...]:
    """A 24-bit word as a target vector of exact 0/1 coordinates."""
    return tuple(Fraction(bit) for bit in _bits_of(mask))


def _check_target(target: Sequence) -> Tuple[Fraction, ...]:
    coords = tuple(_check_exact(value, "golay_delta_sigma") for value in target)
    if len(coords) != 24:
        raise ValueError("golay_delta_sigma: target must have 24 coordinates")
    if any(value < 0 or value > 1 for value in coords):
        raise ValueError("golay_delta_sigma: coordinates must lie in [0, 1]")
    return coords


#: Every codeword as the tuple of coordinates it sets.  Built once.
_CODEWORD_SUPPORTS: Tuple[Tuple[int, ...], ...] = tuple(
    tuple(i for i in range(24) if (mask >> (23 - i)) & 1) for mask in GOLAY_MASKS)

#: Every codeword split into its first and last twelve coordinates, so that a
#: score over all 4,096 of them can be read off two tables of partial sums
#: instead of re-added coordinate by coordinate.  Exactness is untouched: the
#: two halves of a support are disjoint, so the split sum is the same sum.
_CODEWORD_HALVES: Tuple[Tuple[int, int], ...] = tuple(
    (mask >> 12, mask & 0xFFF) for mask in GOLAY_MASKS)


def _subset_sums(values: Sequence[int]) -> List[int]:
    """``out[v] = sum of values[j] over the bits j set in v``, for 12-bit ``v``.

    Built by dynamic programming in one pass, in integers only.
    """
    out = [0] * 4096
    for v in range(1, 4096):
        low = v & -v
        out[v] = out[v ^ low] + values[low.bit_length() - 1]
    return out


def _quantise(driven: Sequence[Fraction], rule: str) -> Tuple[int, bool]:
    """Choose the codeword to emit.  Returns ``(codeword, ambiguous)``.

    ``"nearest"`` thresholds the driven vector and hands the word to the
    complete syndrome decoder, which reports a tie rather than breaking one.
    ``"minnorm"`` picks the codeword closest to the driven vector in exact
    squared distance -- the rule a controller would use, and the one that
    makes the reachable set, rather than the decoder, the binding constraint.
    """
    if rule == "nearest":
        received = _mask_of([1 if value >= Fraction(1, 2) else 0
                             for value in driven])
        decoding = golay_decode.decode_complete(received)
        if decoding.corrected is None:
            return received, True
        return decoding.corrected, False
    if rule == "minnorm":
        # ||d - w||^2 = ||d||^2 - sum_{i in supp w} (2 d_i - 1), so minimising
        # the distance is maximising that sum over the 4,096 codewords.  The
        # weights are put over their common denominator first, so the whole
        # comparison runs in integers -- exactly the same ordering, since a
        # positive common factor cannot reorder anything.
        weights = [2 * value - 1 for value in driven]
        denominator = 1
        for value in weights:
            denominator = (denominator * value.denominator
                           // math.gcd(denominator, value.denominator))
        scaled = [int(value * denominator) for value in weights]
        # Bit j of the high half is coordinate 11 - j; of the low half, 23 - j.
        high = _subset_sums([scaled[11 - j] for j in range(12)])
        low = _subset_sums([scaled[23 - j] for j in range(12)])
        best_index, best_score = 0, None
        for index, (top, bottom) in enumerate(_CODEWORD_HALVES):
            score = high[top] + low[bottom]
            if best_score is None or score > best_score:
                best_index, best_score = index, score
        return GOLAY_MASKS[best_index], False
    raise ValueError(f"golay_delta_sigma: unknown rule {rule!r}")


def golay_delta_sigma(target: Sequence, steps: int,
                      rule: str = "nearest") -> Dict[str, object]:
    """The 24-D dynamic carrier: quantise to the Golay code, feed the error back.

    ``target`` is 24 exact coordinates in ``[0, 1]`` -- in general **not** a
    codeword, and not even a lattice point.  Each coordinate carries an exact
    error accumulator.  At every tick the accumulated vector is thresholded to
    a 24-bit word, that word is decoded by the package's *complete* syndrome
    decoder -- so a tie is reported, never broken silently -- and the
    difference between what was wanted and the codeword actually emitted is
    fed back.

    The return value is the whole experiment: the trajectory, the exact
    per-coordinate time average, the largest error the accumulator reached,
    and how many ticks the decoder had to declare ambiguous.  Whether the
    average converges is *measured here*, not assumed: the one-dimensional
    ``1/N`` bound is a theorem (``GLM.Info.dsAverage_error_le``), but nothing
    proves it survives a nearest-codeword repair that can move four
    coordinates at once.
    """
    coords = _check_target(target)
    if steps <= 0:
        raise PrecisionError("golay_delta_sigma: steps must be > 0")
    accumulator = [Fraction(0) for _ in range(24)]
    totals = [0 for _ in range(24)]
    trajectory: List[Tuple[int, Fraction]] = []
    visits: Dict[int, int] = {}
    ambiguous = 0
    excursion = Fraction(0)
    for _ in range(steps):
        driven = [accumulator[i] + coords[i] for i in range(24)]
        codeword, tie = _quantise(driven, rule)
        if tie:
            ambiguous += 1
        emitted = _bits_of(codeword)
        accumulator = [driven[i] - emitted[i] for i in range(24)]
        excursion = max(excursion, max(abs(value) for value in accumulator))
        for i in range(24):
            totals[i] += emitted[i]
        distance = sum(abs(Fraction(emitted[i]) - coords[i]) for i in range(24))
        trajectory.append((codeword, distance))
        visits[codeword] = visits.get(codeword, 0) + 1

    average = tuple(Fraction(total, steps) for total in totals)
    deviation = max(abs(average[i] - coords[i]) for i in range(24))
    return {
        "steps": steps,
        "rule": rule,
        "trajectory": tuple(trajectory),
        "final_accumulator": tuple(accumulator),
        "average": average,
        "max_coordinate_deviation": deviation,
        "within_one_over_n": deviation <= Fraction(1, steps),
        "max_accumulator": excursion,
        "ambiguous_ticks": ambiguous,
        "unique_codewords": len(visits),
        "most_visited_share": Fraction(max(visits.values()), steps),
        "mean_distance": Fraction(
            sum(d for _c, d in trajectory).numerator,
            sum(d for _c, d in trajectory).denominator * steps)
        if sum(d for _c, d in trajectory) != 0 else Fraction(0),
    }


def hull_certificate(target: Sequence, steps: int = 400) -> Dict[str, object]:
    """Decide, with an exact certificate, whether a target is reachable at all.

    Every state the 24-D dynamic carrier can emit is a codeword, so any limit
    of its time averages lies in the **convex hull of the 4,096 codewords**.
    A target outside that hull is therefore unreachable by *any* quantiser
    rule, however clever -- the drift is forced, not a defect of the decoder.

    This function looks for the witness of that.  It runs the minimum-norm
    quantiser, takes the direction the error accumulator drifts in as a
    candidate functional ``c``, and then *verifies* the separation exactly
    against all 4,096 codewords: if ``<c, target>`` exceeds ``<c, w>`` for
    every codeword ``w``, the target provably cannot be reached.  A failure to
    find the witness is reported as such and proves nothing either way.

    The machine-checked counterpart is
    ``GLM.Info.not_tendsto_avg_of_separating`` in
    ``RequestProject/GLM/Reachable.lean``.
    """
    coords = _check_target(target)
    run = golay_delta_sigma(coords, steps, rule="minnorm")
    drift = tuple(value / steps for value in run["final_accumulator"])
    at_target = sum(drift[i] * coords[i] for i in range(24))
    best = max(sum(drift[i] for i in support)
               for support in _CODEWORD_SUPPORTS)
    return {
        "steps": steps,
        "functional": drift,
        "value_at_target": at_target,
        "max_over_codewords": best,
        "separates": at_target > best,
        "gap": at_target - best,
        "codewords_checked": len(_CODEWORD_SUPPORTS),
    }


def trajectory_stats(trajectory: Sequence[Tuple[int, object]]) -> Dict[str, object]:
    """Exact statistics of a 24-D trajectory: no float anywhere."""
    if not trajectory:
        raise PrecisionError("trajectory_stats: empty trajectory")
    distances: Dict[str, int] = {}
    visits: Dict[int, int] = {}
    total = Fraction(0)
    for codeword, distance in trajectory:
        key = str(distance)
        distances[key] = distances.get(key, 0) + 1
        visits[codeword] = visits.get(codeword, 0) + 1
        total += Fraction(distance)
    most = max(visits.values())
    return {
        "steps": len(trajectory),
        "distance_distribution": dict(sorted(distances.items())),
        "mean_distance": total / len(trajectory),
        "unique_codewords": len(visits),
        "most_visited_share": Fraction(most, len(trajectory)),
    }


# ===========================================================================
# 6.  BRIDGE TO THE CARRIER LAYER
# ===========================================================================

def real_carrier(targets: Sequence[ExactReal], level: int) -> Tuple[Fraction, ...]:
    """The 24-coordinate carrier the tower holds for a vector of processes.

    Coordinates beyond the ones supplied are zero.  The result is an ordinary
    exact carrier: it can be handed to
    :class:`~glm_universal.data_objects.base.DataObject`, stacked, decoded and
    measured like any other.  What it is *not* is the target -- it is the
    target's stand-in at this level, and a higher level will hold a different
    one.
    """
    if len(targets) > 24:
        raise ValueError("real_carrier: at most 24 coordinates")
    coordinates = [surrogate(x, level) for x in targets]
    coordinates.extend(Fraction(0) for _ in range(24 - len(coordinates)))
    return tuple(coordinates)


# ===========================================================================
# 7.  THE REPORT
# ===========================================================================

def exact_real_report() -> Dict[str, object]:
    """Recompute everything this module claims, on demand.

    Every number below is produced by running the code, not by quoting it.
    """
    root2 = sqrt(Fraction(2))
    root2_at_40 = root2.at(40)

    # The tower's stand-ins for sqrt(2), and the fact that none of them is it.
    levels = 8
    stand_ins = surrogate_sequence(root2, levels)
    stand_in_gap = tuple(
        (n, stand_ins[n], abs(stand_ins[n] ** 2 - 2) > 0) for n in range(levels))

    # The exposure of a stand-in: the level at which the tower splits it from
    # the target.  Level n's stand-in survives to level n and no further.
    exposure = []
    for n in range(4):
        found = None
        for m in range(n, n + 8):
            if surrogate(root2, m) != rational_surrogate(stand_ins[n], m):
                found = m
                break
        exposure.append((n, found))

    # The delta-sigma law, at three run lengths.
    target = root2.at(60) - 1          # sqrt(2) - 1, to 2**-60
    runs = []
    for steps in (10, 100, 1000):
        error = delta_sigma_error(target, steps)
        runs.append((steps, error, error <= Fraction(1, steps)))

    # Determinism: the same target twice gives the same bits.
    first = delta_sigma_bits(Fraction(3, 7), 64)
    second = delta_sigma_bits(Fraction(3, 7), 64)

    # The 24-D modulator, on a reachable target and on an unreachable one.
    half = tuple(Fraction(1, 2) for _ in range(24))
    reachable_run = golay_delta_sigma(half, 100)
    ramp = tuple(Fraction(i, 24) for i in range(24))
    golay_run = golay_delta_sigma(ramp, 200)
    stats = trajectory_stats(golay_run["trajectory"])
    certificate = hull_certificate(ramp, 400)

    # The boundary: equality of processes is undecidable.
    same_value_two_ways = sqrt(Fraction(2)) * sqrt(Fraction(2))
    undecided = decide_equal(same_value_two_ways, from_fraction(Fraction(2)), 40)
    distinguishable = decide_equal(root2, from_fraction(Fraction(3, 2)), 4)

    return {
        "sqrt2_at_40": root2_at_40,
        "sqrt2_decimal_20": root2.decimal(20),
        "sqrt2_error_below": Fraction(1, 2 ** 40),
        "sqrt2_squared_error": abs(root2_at_40 ** 2 - 2),
        "pi_decimal_20": pi().decimal(20),
        "e_decimal_20": e().decimal(20),
        "phi_decimal_20": phi().decimal(20),
        "levels": levels,
        "stand_ins": tuple(str(s) for s in stand_ins),
        "no_stand_in_is_the_target": all(flag for _n, _s, flag in stand_in_gap),
        "stand_in_exposed_at": tuple(exposure),
        "delta_sigma_runs": tuple(runs),
        "delta_sigma_law_holds": all(flag for _s, _e, flag in runs),
        "delta_sigma_deterministic": first == second,
        "delta_sigma_average_3_7": str(delta_sigma_average(Fraction(3, 7), 10000)),
        "golay_trajectory": stats,
        "golay_average_deviation": golay_run["max_coordinate_deviation"],
        "golay_within_one_over_n": golay_run["within_one_over_n"],
        "golay_max_accumulator": golay_run["max_accumulator"],
        "golay_ambiguous_ticks": golay_run["ambiguous_ticks"],
        "golay_reachable_deviation": reachable_run["max_coordinate_deviation"],
        "golay_reachable_accumulator": reachable_run["max_accumulator"],
        "golay_unreachable_certified": certificate["separates"],
        "golay_certificate_gap": certificate["gap"],
        "equality_undecided": undecided is None,
        "inequality_decided": distinguishable is False,
        "cf_sqrt2_convergent_30": str(
            convergents(continued_fraction(root2.at(80), 30))[-1]),
    }
