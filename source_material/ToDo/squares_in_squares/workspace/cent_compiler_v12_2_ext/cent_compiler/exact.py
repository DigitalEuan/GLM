"""Exact signed rational arithmetic for the ¢ core (CentCalculus2, domain 1).

Every numeric operation in the trusted execution core is performed on
``fractions.Fraction``.  There is no floating point anywhere in this module:
binary floats are only accepted through :func:`from_float_exact`, which
converts the *stored binary value* into the rational it actually denotes.

Structured errors
-----------------
Failures are raised as :class:`CentError` with a machine-readable ``code``.
Callers must not catch and silently substitute a value; the escalation
controller in :mod:`cent_compiler.resolution` turns a failure into an
explicit, structured outcome instead.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from fractions import Fraction
from typing import Any, Iterable, Optional

Q = Fraction
"""The exact scalar type of the ¢ core."""

MAX_BITS = 1 << 20
"""Default bit-length guard for user-supplied integers."""


class ErrorCode(str, Enum):
    """Machine-readable error taxonomy (stable strings)."""

    DIVISION_BY_ZERO = "division_by_zero"
    DOMAIN_ERROR = "domain_error"
    INVALID_INPUT = "invalid_input"
    UNSUPPORTED = "unsupported"
    BUDGET_EXHAUSTED = "resource_budget_exhausted"
    VALIDATION_ERROR = "validation_error"
    TYPE_ERROR = "type_error"
    CYCLE_DETECTED = "cycle_detected"
    APPROXIMATION_UNPROVED = "approximation_unproved"


@dataclass
class CentError(Exception):
    """A structured, located compiler/runtime error.

    ``where`` is an instruction, wire or resource location.  ``detail`` holds
    non-numeric diagnostics only; it must never contain secret material.
    """

    code: ErrorCode | str
    message: str
    where: Optional[str] = None
    detail: Optional[dict[str, Any]] = None

    def __str__(self) -> str:  # pragma: no cover - formatting only
        loc = f" [{self.where}]" if self.where else ""
        return f"{_code_str(self.code)}{loc}: {self.message}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": _code_str(self.code),
            "message": self.message,
            "where": self.where,
            "detail": self.detail or {},
        }


def _code_str(code: ErrorCode | str) -> str:
    """Stable machine-readable code string (the enum value, not its repr)."""
    return code.value if isinstance(code, ErrorCode) else str(code)


def _where(where: Optional[str]) -> str:
    return where or "<unknown>"


def q(value: Any, where: Optional[str] = None) -> Q:
    """Coerce an exact numeric value to :class:`Fraction`.

    Accepts ``int``, ``Fraction``, and decimal/exponent *strings*.  Floats are
    rejected on purpose: pass them through :func:`from_float_exact` so the
    conversion policy is explicit.

    >>> q("0.1")
    Fraction(1, 10)
    """
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        return Fraction(int(value))
    if isinstance(value, int):
        _check_bits(value, where)
        return Fraction(value)
    if isinstance(value, str):
        try:
            return Fraction(Decimal(value.strip()))
        except (InvalidOperation, ValueError, ZeroDivisionError) as exc:
            raise CentError(
                ErrorCode.INVALID_INPUT, f"not an exact decimal: {value!r}", where
            ) from exc
    raise CentError(
        ErrorCode.TYPE_ERROR,
        f"expected exact rational (int/Fraction/decimal string), got {type(value).__name__}",
        where,
    )


def _check_bits(value: int, where: Optional[str], max_bits: int = MAX_BITS) -> None:
    if value.bit_length() > max_bits:
        raise CentError(
            ErrorCode.BUDGET_EXHAUSTED,
            f"integer exceeds {max_bits} bits",
            where,
            {"bits": value.bit_length()},
        )


def from_float_exact(value: float, where: Optional[str] = None) -> Q:
    """Exact rational for the *stored binary value* of an IEEE-754 double.

    Every finite float is a dyadic rational and converts losslessly, including
    subnormals.  ``-0.0`` collapses to ``0`` (recorded by the caller, see
    :mod:`cent_compiler.resources`).  NaN and infinities are rejected: they are
    not rational and this core has no non-rational scalar type.
    """
    if isinstance(value, bool):
        raise CentError(ErrorCode.TYPE_ERROR, "bool is not a float", where)
    if not isinstance(value, float):
        raise CentError(ErrorCode.TYPE_ERROR, f"expected float, got {type(value).__name__}", where)
    if math.isnan(value):
        raise CentError(ErrorCode.DOMAIN_ERROR, "NaN has no rational value", where)
    if math.isinf(value):
        raise CentError(ErrorCode.DOMAIN_ERROR, "infinity has no rational value", where)
    return Fraction(*value.as_integer_ratio())


def add(*values: Q, where: Optional[str] = None) -> Q:
    total = Fraction(0)
    for v in values:
        total += q(v, where)
    return total


def mul(*values: Q, where: Optional[str] = None) -> Q:
    total = Fraction(1)
    for v in values:
        total *= q(v, where)
    return total


def div(numerator: Q, denominator: Q, where: Optional[str] = None) -> Q:
    """Exact division; division by zero is an explicit error, never a value."""
    numerator, denominator = q(numerator, where), q(denominator, where)
    if denominator == 0:
        raise CentError(
            ErrorCode.DIVISION_BY_ZERO, "division by exact zero", where
        )
    return numerator / denominator


def reciprocal(x: Q, where: Optional[str] = None) -> Q:
    return div(Fraction(1), x, where)


def sign(x: Q) -> int:
    return (x > 0) - (x < 0)


def is_zero(x: Q) -> bool:
    return q(x) == 0


def clamp(x: Q, lo: Q, hi: Q, where: Optional[str] = None) -> Q:
    """Clamp to the closed interval ``[lo, hi]``; requires ``lo <= hi``."""
    x, lo, hi = q(x, where), q(lo, where), q(hi, where)
    if lo > hi:
        raise CentError(
            ErrorCode.DOMAIN_ERROR, "clamp bounds are not ordered", where, {"lo": str(lo), "hi": str(hi)}
        )
    return lo if x < lo else hi if x > hi else x


def wrap_periodic(x: Q, period: Q, where: Optional[str] = None) -> Q:
    """Wrap into the half-open interval ``[0, period)``; requires ``period > 0``."""
    x, period = q(x, where), q(period, where)
    if period <= 0:
        raise CentError(
            ErrorCode.DOMAIN_ERROR, "wrap period must be strictly positive", where
        )
    return x % period


def format_q(x: Q) -> str:
    """Human-readable exact form (``num/den`` only when needed)."""
    x = q(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def q_to_json(x: Q) -> dict[str, str]:
    """Portable exact encoding: separate decimal strings for num/den."""
    x = q(x)
    return {"num": str(x.numerator), "den": str(x.denominator)}


def q_from_json(obj: Any, where: Optional[str] = None) -> Q:
    """Decode ``{"num": ..., "den": ...}`` or a decimal string."""
    if isinstance(obj, dict):
        if set(obj) != {"num", "den"}:
            raise CentError(ErrorCode.VALIDATION_ERROR, "rational needs exactly num/den", where)
        num = int(obj["num"], 10)
        den = int(obj["den"], 10)
        if den == 0:
            raise CentError(ErrorCode.VALIDATION_ERROR, "zero denominator", where)
        _check_bits(num, where)
        _check_bits(den, where)
        return Fraction(num, den)
    return q(obj, where)


def all_zero(values: Iterable[Q]) -> bool:
    return all(q(v) == 0 for v in values)
