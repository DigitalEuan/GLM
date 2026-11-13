"""Conjugate physical ports and conservative bond-graph junctions.

A port carries an effort/flow pair ``(e, f)`` — voltage/current,
pressure/volume-flow, force/velocity, temperature/entropy-flow.  Instantaneous
exact power is ``e·f``.

Sign conventions are fixed here and checked exactly:

* **0-junction** (common flow): every port shares one flow; the efforts sum to
  zero.  Mechanical series / electrical loop (KVL).
* **1-junction** (common effort): every port shares one effort; the flows sum
  to zero.  Electrical node (KCL) / parallel manifold.
* **gyrator**: ``(e, f) ↦ (r·f, −e/r)``.  Note the minus sign: the widely
  quoted pair ``e₁ = r f₂, e₂ = r f₁`` is *not* power conserving
  (``P₁ + P₂ = 2 r f₁ f₂``).  The power-preserving convention is used here and
  documented in ``docs/semantics.md``.
* **transformer**: ``(e, f) ↦ (e/n, −n·f)``.

Junctions and two-ports raise a structured error if the supplied ports violate
their constitutive constraint instead of silently averaging inconsistent data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from .exact import CentError, ErrorCode, Q, div, format_q, q, sign


@dataclass(frozen=True)
class PhysicalPort:
    """Exact conjugate effort/flow pair."""

    effort: Q
    flow: Q

    def __post_init__(self) -> None:
        object.__setattr__(self, "effort", q(self.effort))
        object.__setattr__(self, "flow", q(self.flow))

    @property
    def power(self) -> Q:
        """Instantaneous exact power ``e·f`` (positive = delivered)."""
        return self.effort * self.flow

    def scaled(self, k: Any) -> "PhysicalPort":
        k = q(k)
        return PhysicalPort(self.effort * k, self.flow * k)

    def reversed(self) -> "PhysicalPort":
        return PhysicalPort(-self.effort, -self.flow)

    def as_dict(self) -> dict[str, str]:
        return {"effort": str(self.effort), "flow": str(self.flow)}


@dataclass(frozen=True)
class Transformer:
    ratio: Q

    def __post_init__(self) -> None:
        object.__setattr__(self, "ratio", q(self.ratio))
        if self.ratio == 0:
            raise CentError(ErrorCode.DOMAIN_ERROR, "transformer ratio must be nonzero")

    def apply(self, p: PhysicalPort) -> PhysicalPort:
        return PhysicalPort(div(p.effort, self.ratio), -self.ratio * p.flow)


@dataclass(frozen=True)
class Gyrator:
    resistance: Q

    def __post_init__(self) -> None:
        object.__setattr__(self, "resistance", q(self.resistance))
        if self.resistance == 0:
            raise CentError(ErrorCode.DOMAIN_ERROR, "gyrator resistance must be nonzero")

    def apply(self, p: PhysicalPort) -> PhysicalPort:
        r = self.resistance
        # (e, f) -> (r f, -e / r); power is exactly negated.
        return PhysicalPort(r * p.flow, div(-p.effort, r))


def total_power(ports: Iterable[PhysicalPort]) -> Q:
    return sum((p.power for p in ports), q(0))


def require_power_balance(ports: Sequence[PhysicalPort], where: str | None = None) -> None:
    """Check Tellegen's power balance ``Σ P_i = 0`` exactly."""
    p = total_power(ports)
    if p != 0:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "port set violates power conservation",
            where,
            {"total_power": format_q(p), "ports": [x.as_dict() for x in ports]},
        )


def junction_0(ports: Sequence[PhysicalPort], resolved: int | None = None,
               where: str | None = None) -> tuple[PhysicalPort, ...]:
    """Common-flow junction: solve the effort that makes ``Σ e_i f = 0``.

    All supplied flows must be identical (that *is* the junction constraint).
    One port (default: the last) is the resolved branch; its effort is the
    negative sum of the others, so power balance holds by construction.
    """
    pts = list(ports)
    if len(pts) < 2:
        raise CentError(ErrorCode.INVALID_INPUT, "a junction needs at least two ports", where)
    flows = {p.flow for p in pts}
    if len(flows) != 1:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "0-junction requires a common flow",
            where,
            {"flows": [format_q(f) for f in sorted(flows)]},
        )
    idx = len(pts) - 1 if resolved is None else resolved
    if not 0 <= idx < len(pts):
        raise CentError(ErrorCode.INVALID_INPUT, "resolved port index out of range", where)

    common_flow = pts[0].flow
    effort_sum = sum((p.effort for i, p in enumerate(pts) if i != idx), q(0))
    resolved_port = PhysicalPort(-effort_sum, common_flow)
    out = list(pts)
    out[idx] = resolved_port
    require_power_balance(out, where)
    return tuple(out)


def junction_1(ports: Sequence[PhysicalPort], resolved: int | None = None,
               where: str | None = None) -> tuple[PhysicalPort, ...]:
    """Common-effort junction: solve the flow that makes ``Σ e f = 0``."""
    pts = list(ports)
    if len(pts) < 2:
        raise CentError(ErrorCode.INVALID_INPUT, "a junction needs at least two ports", where)
    efforts = {p.effort for p in pts}
    if len(efforts) != 1:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "1-junction requires a common effort",
            where,
            {"efforts": [format_q(e) for e in sorted(efforts)]},
        )
    idx = len(pts) - 1 if resolved is None else resolved
    if not 0 <= idx < len(pts):
        raise CentError(ErrorCode.INVALID_INPUT, "resolved port index out of range", where)

    common_effort = pts[0].effort
    flow_sum = sum((p.flow for i, p in enumerate(pts) if i != idx), q(0))
    resolved_port = PhysicalPort(common_effort, -flow_sum)
    out = list(pts)
    out[idx] = resolved_port
    require_power_balance(out, where)
    return tuple(out)


def dissipator(resistance: Any, effort: Any, temperature: Any = 1) -> tuple[PhysicalPort, Q]:
    """Linear dissipator: ``f = e/R``; returns ``(port, entropy_rate)``.

    Power ``e²/R >= 0``; entropy generation is ``P/T`` and requires ``T > 0``.
    """
    r, e, temp = q(resistance), q(effort), q(temperature)
    if r <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "resistance must be strictly positive")
    if temp <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "temperature must be strictly positive")
    flow = div(e, r)
    power = e * flow
    return PhysicalPort(e, flow), power / temp


def potential_store(capacitance: Any, charge: Any, flow: Any) -> tuple[PhysicalPort, Q]:
    """Potential store (capacitor/spring): ``e = q/C``, energy ``q²/(2C)``."""
    c, charge_q, f = q(capacitance), q(charge), q(flow)
    if c <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "capacitance must be strictly positive")
    return PhysicalPort(charge_q / c, f), charge_q * charge_q / (2 * c)


def kinetic_store(inductance: Any, flux: Any, effort: Any) -> tuple[PhysicalPort, Q]:
    """Kinetic store (inductor/mass): ``f = Φ/L``, energy ``Φ²/(2L)``."""
    l, phi, e = q(inductance), q(flux), q(effort)
    if l <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "inductance must be strictly positive")
    return PhysicalPort(e, phi / l), phi * phi / (2 * l)


def ideal_transducer(ratio: Any, p: PhysicalPort, efficiency: Any = 1) -> tuple[PhysicalPort, Q]:
    """Ideal two-port transducer with optional efficiency ``η ∈ (0,1]``.

    ``(e, f) ↦ (k·e, −η·f/k)``.  For ``η = 1`` power is exactly conserved; for
    ``η < 1`` the difference is the dissipated power and must be nonnegative.
    """
    k, eta = q(ratio), q(efficiency)
    if k == 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "transducer ratio must be nonzero")
    if not 0 < eta <= 1:
        raise CentError(ErrorCode.DOMAIN_ERROR, "transducer efficiency must lie in (0,1]")
    out = PhysicalPort(k * p.effort, -eta * p.flow / k)
    loss = p.power + out.power
    if loss < 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "transducer would create power")
    return out, loss


def sign_of_power(p: PhysicalPort) -> int:
    return sign(p.power)
