"""Pulse-density channels (CentCalculus2, domain 1).

Unit density is a *constrained channel type*, not the universal numeric type.
Addition may leave ``[0,1]``; the caller must choose a policy explicitly:

* ``REJECT`` — raise ``domain_error`` (the default: silent saturation hides bugs)
* ``CLAMP``  — saturation onto the closed unit interval
* ``WIDEN``  — keep the exact value (an explicitly unbounded channel)

``neg`` in the arithmetic vocabulary is signed negation.  Unit *complement*
is the separate operation implemented here as :meth:`UnitDensity.complement`,
so the two cannot be confused.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .exact import CentError, ErrorCode, Q, clamp, q, wrap_periodic


class DensityPolicy(str, Enum):
    REJECT = "reject"
    CLAMP = "clamp"
    WIDEN = "widen"


@dataclass(frozen=True)
class UnitDensity:
    """An exact rational density constrained to ``[lo, hi]`` (default ``[0,1]``)."""

    value: Q

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", q(self.value))

    # -- construction -----------------------------------------------------
    @staticmethod
    def of(value: Any, policy: DensityPolicy | str = DensityPolicy.REJECT,
           lo: Any = 0, hi: Any = 1, where: str | None = None) -> "UnitDensity":
        v = q(value, where)
        policy = DensityPolicy(policy)
        lo_q, hi_q = q(lo), q(hi)
        if lo_q > hi_q:
            raise CentError(ErrorCode.DOMAIN_ERROR, "density bounds are not ordered", where)
        if lo_q <= v <= hi_q:
            return UnitDensity(v)
        if policy is DensityPolicy.CLAMP:
            return UnitDensity(clamp(v, lo_q, hi_q, where))
        if policy is DensityPolicy.WIDEN:
            return UnitDensity(v)
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "value outside the declared density channel",
            where,
            {"value": str(v), "lo": str(lo_q), "hi": str(hi_q)},
        )

    @staticmethod
    def zero() -> "UnitDensity":
        return UnitDensity(q(0))

    @staticmethod
    def unit() -> "UnitDensity":
        return UnitDensity(q(1))

    # -- observations -----------------------------------------------------
    @property
    def is_unit(self) -> bool:
        return 0 <= self.value <= 1

    def in_range(self, lo: Any = 0, hi: Any = 1) -> bool:
        return q(lo) <= self.value <= q(hi)

    # -- operations -------------------------------------------------------
    def complement(self) -> "UnitDensity":
        """Unit complement ``1 - x``; requires the channel value in ``[0,1]``."""
        if not self.is_unit:
            raise CentError(
                ErrorCode.DOMAIN_ERROR, "unit complement requires a value in [0,1]",
                detail={"value": str(self.value)},
            )
        return UnitDensity(1 - self.value)

    def signed(self) -> Q:
        """View the density as a signed exact signal."""
        return self.value

    def saturate(self) -> "UnitDensity":
        return UnitDensity(clamp(self.value, 0, 1))

    def wrap(self, period: Any = 1) -> "UnitDensity":
        return UnitDensity(wrap_periodic(self.value, period))

    def __str__(self) -> str:  # pragma: no cover - formatting
        return f"UnitDensity({self.value})"


def saturate(value: Any, lo: Any, hi: Any) -> Q:
    """Exact clamp with explicit ordered bounds (idempotent by construction)."""
    return clamp(q(value), q(lo), q(hi))


def unit_complement(value: Any) -> Q:
    """``1 - x`` on ``[0,1]``; separate from arithmetic negation."""
    return UnitDensity.of(value).complement().value


def wrap_to_unit(value: Any) -> Q:
    return wrap_periodic(q(value), 1)
