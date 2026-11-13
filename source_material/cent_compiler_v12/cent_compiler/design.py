"""Constrained selection over declared device-design alternatives.

This layer does not invent component values.  It searches a small, explicit
list of declared design alternatives for each bound route, evaluates every
alternative through the real device binding, and selects the cheapest
alternative that satisfies the requested accuracy, cost and input-range
constraints.

The result is a design point plus a verification plan.  It is still not a
netlist, a geometry, a measured-device model or a fabrication claim.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Any, Callable, Mapping

from .device import (
    DEFAULT_ERROR_LIMIT,
    DeviceBinding,
    bind_delta_sigma,
    bind_feedback_sqrt,
    bind_log_domain_sqrt,
)
from .exact import CentError, ErrorCode, Q, q, q_to_json
from .interval import pi_interval

SCHEMA = "cent-design/1"
COMPARISON_SCHEMA = "cent-comparison/1"
FABRICATION_AUDIT_SCHEMA = "cent-fabrication-audit/1"

# Certified rational bounds on pi, used only to bracket the pole bandwidth.
PI_BOUNDS = pi_interval(160)


def _exact(value: Any, name: str) -> Q:
    """Parse a fraction, exact decimal or rational without accepting floats."""
    if isinstance(value, bool):
        raise CentError(ErrorCode.TYPE_ERROR, f"{name}: bool is not a quantity")
    if isinstance(value, str) and "/" in value:
        try:
            return Fraction(value.strip())
        except (ValueError, ZeroDivisionError) as exc:
            raise CentError(
                ErrorCode.INVALID_INPUT,
                f"{name}: not an exact fraction: {value!r}",
            ) from exc
    try:
        return q(value, name)
    except CentError:
        raise
    except (TypeError, ValueError) as exc:  # pragma: no cover - q normalises this
        raise CentError(
            ErrorCode.TYPE_ERROR, f"{name}: expected an exact rational"
        ) from exc


def _positive(value: Any, name: str) -> Q:
    result = _exact(value, name)
    if result <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, f"{name} must be positive")
    return result


def _json(value: Any) -> Any:
    if isinstance(value, Fraction):
        return q_to_json(value)
    if isinstance(value, Mapping):
        return {str(key): _json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json(item) for item in value]
    return value


def _decimal(value: Q, places: int = 10) -> str:
    """Deterministic decimal truncation using integer arithmetic only."""
    sign = "-" if value < 0 else ""
    value = abs(value)
    scale = 10 ** places
    scaled = value.numerator * scale // value.denominator
    return f"{sign}{scaled // scale}.{scaled % scale:0{places}d}"


def _q_text(value: Any) -> str | None:
    """Render an exact JSON quantity for a text/markdown export."""
    if value is None:
        return None
    if isinstance(value, Mapping) and "num" in value and "den" in value:
        return f"{value['num']}/{value['den']}"
    return str(value)


@dataclass(frozen=True)
class PoleBandwidth:
    """Certified bandwidth bracket for one declared pole."""

    name: str
    symbol: str
    time_constant: Q
    lower_hz: Q
    upper_hz: Q
    status: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "symbol": self.symbol,
            "time_constant": q_to_json(self.time_constant),
            "lower_hz": q_to_json(self.lower_hz),
            "upper_hz": q_to_json(self.upper_hz),
            "status": self.status,
        }


@dataclass(frozen=True)
class BandwidthResult:
    """Bandwidth classification over all declared small-signal poles."""

    requested_hz: Q
    poles: tuple[PoleBandwidth, ...]
    slowest: PoleBandwidth | None
    status: str

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    @property
    def detail(self) -> str:
        if self.slowest is None:
            return (
                "the binding declares no small-signal poles; bandwidth cannot be certified"
            )
        pole = self.slowest
        bounds = (
            f"[{_decimal(pole.lower_hz)} , {_decimal(pole.upper_hz)}] Hz"
        )
        if self.status == "pass":
            return (
                f"slowest pole {pole.name} ({pole.symbol}) has certified bandwidth "
                f"{bounds}; minimum {_decimal(self.requested_hz)} Hz is covered"
            )
        if self.status == "fail":
            return (
                f"slowest pole {pole.name} ({pole.symbol}) has certified bandwidth "
                f"{bounds}; upper bound is below minimum {_decimal(self.requested_hz)} Hz"
            )
        return (
            f"slowest pole {pole.name} ({pole.symbol}) has certified bandwidth "
            f"{bounds}; the interval straddles minimum {_decimal(self.requested_hz)} Hz"
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "requested_hz": q_to_json(self.requested_hz),
            "status": self.status,
            "slowest": self.slowest.as_dict() if self.slowest is not None else None,
            "poles": [item.as_dict() for item in self.poles],
            "detail": self.detail,
        }


@dataclass(frozen=True)
class RangeCertificate:
    """Continuous-range evidence assembled from declared monotone budgets."""

    status: str
    method: str
    low: Q
    high: Q
    max_error: Q | None
    max_error_at: Q | None
    error_direction: str
    bandwidth_direction: str
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "method": self.method,
            "range": {
                "min": q_to_json(self.low),
                "max": q_to_json(self.high),
            },
            "max_relative_error": (
                q_to_json(self.max_error) if self.max_error is not None else None
            ),
            "max_error_at": (
                q_to_json(self.max_error_at)
                if self.max_error_at is not None
                else None
            ),
            "error_direction": self.error_direction,
            "bandwidth_direction": self.bandwidth_direction,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class DesignOption:
    """One declared alternative in a route's finite design space."""

    name: str
    cost: Q
    parameters: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "cost": q_to_json(self.cost),
            "parameters": _json(dict(self.parameters)),
        }


RANKING_PROFILES = ("exact-static", "dynamic-aware")


@dataclass(frozen=True)
class RankingObjectiveSpec:
    """One declared objective used by the exact Pareto ranking."""

    name: str
    direction: str
    source: str

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "direction": self.direction,
            "source": self.source,
        }


@dataclass(frozen=True)
class DesignObjective:
    """One exact objective value attached to a ranked candidate."""

    name: str
    direction: str
    value: Q
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "direction": self.direction,
            "value": q_to_json(self.value),
            "source": self.source,
        }


@dataclass(frozen=True)
class DesignRanking:
    """Exact Pareto layers plus the declared tie-break that picks a point."""

    profile: str
    objectives: tuple[RankingObjectiveSpec, ...]
    front: tuple[str, ...]
    layers: tuple[tuple[str, ...], ...]
    unranked: tuple[str, ...]
    excluded: tuple[str, ...]
    selected: str | None
    rule: str
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "objectives": [item.as_dict() for item in self.objectives],
            "front": list(self.front),
            "layers": [list(layer) for layer in self.layers],
            "unranked": list(self.unranked),
            "excluded": list(self.excluded),
            "selected": self.selected,
            "rule": self.rule,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class DesignSpace:
    """The declared alternatives for one route and its binding function."""

    name: str
    route_id: str
    input_domain: str
    default_input: Q
    options: tuple[DesignOption, ...]
    binding: Callable[..., DeviceBinding]
    range_error_direction: str = "constant"
    range_bandwidth_direction: str = "constant"


DESIGN_SPACES: dict[str, DesignSpace] = {
    "delta-sigma": DesignSpace(
        name="First-order delta-sigma carry route",
        route_id="delta-sigma-first-order",
        input_domain="[0, 1]",
        default_input=Fraction(1, 2),
        binding=bind_delta_sigma,
        range_error_direction="constant",
        range_bandwidth_direction="constant",
        options=(
            DesignOption(
                "offset-1/200",
                Fraction(1),
                {"offset_ratio": Fraction(1, 200)},
            ),
            DesignOption(
                "offset-1/500",
                Fraction(2),
                {"offset_ratio": Fraction(1, 500)},
            ),
            DesignOption(
                "offset-1/1000",
                Fraction(3),
                {"offset_ratio": Fraction(1, 1000)},
            ),
            DesignOption(
                "offset-1/2000",
                Fraction(4),
                {"offset_ratio": Fraction(1, 2000)},
            ),
        ),
    ),
    "sqrt-log": DesignSpace(
        name="Log-domain square-root compute route",
        route_id="sqrt-log-domain",
        input_domain="(0, 1]",
        default_input=Fraction(1),
        binding=bind_log_domain_sqrt,
        range_error_direction="decreasing",
        range_bandwidth_direction="increasing",
        options=(
            DesignOption("precision-8", Fraction(1), {"precision": 8}),
            DesignOption("precision-20", Fraction(2), {"precision": 20}),
            DesignOption("precision-32", Fraction(3), {"precision": 32}),
            DesignOption("precision-64", Fraction(4), {"precision": 64}),
        ),
    ),
    "sqrt-feedback": DesignSpace(
        name="Op-amp + multiplier square-root compute route",
        route_id="sqrt-opamp-multiplier",
        input_domain="(0, 4]",
        default_input=Fraction(2),
        binding=bind_feedback_sqrt,
        range_error_direction="decreasing",
        range_bandwidth_direction="constant",
        options=(
            DesignOption(
                "gain-100000",
                Fraction(1),
                {"amplifier_gain": Fraction(100_000)},
            ),
            DesignOption(
                "gain-1000000",
                Fraction(2),
                {"amplifier_gain": Fraction(1_000_000)},
            ),
            DesignOption(
                "gain-10000000",
                Fraction(3),
                {"amplifier_gain": Fraction(10_000_000)},
            ),
        ),
    ),
}


@dataclass(frozen=True)
class DesignConstraints:
    """The requested operating point and explicit constraints."""

    input_value: Q
    input_min: Q
    input_max: Q
    accuracy: Q
    max_cost: Q | None
    min_bandwidth: Q | None = None

    @property
    def probes(self) -> tuple[Q, ...]:
        return tuple(sorted({self.input_min, self.input_value, self.input_max}))

    def as_dict(self) -> dict[str, Any]:
        return {
            "input": q_to_json(self.input_value),
            "input_range": {
                "min": q_to_json(self.input_min),
                "max": q_to_json(self.input_max),
            },
            "probe_points": [q_to_json(item) for item in self.probes],
            "accuracy": q_to_json(self.accuracy),
            "max_cost": q_to_json(self.max_cost) if self.max_cost is not None else None,
            "min_bandwidth": (
                q_to_json(self.min_bandwidth)
                if self.min_bandwidth is not None
                else None
            ),
        }


@dataclass(frozen=True)
class ProbeResult:
    """The exact binding result at one declared input."""

    input_value: Q
    passed: bool
    total_error: Q | None
    checks_passed: int
    checks_total: int
    failures: tuple[str, ...]
    bandwidth: BandwidthResult | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "input": q_to_json(self.input_value),
            "status": "pass" if self.passed else "gap",
            "total_relative_error": (
                q_to_json(self.total_error) if self.total_error is not None else None
            ),
            "checks_passed": self.checks_passed,
            "checks_total": self.checks_total,
            "failures": list(self.failures),
            "bandwidth": (
                self.bandwidth.as_dict() if self.bandwidth is not None else None
            ),
        }


@dataclass(frozen=True)
class DesignCandidate:
    """One evaluated alternative, including its exact binding at the main input."""

    option: DesignOption
    binding: DeviceBinding | None
    probes: tuple[ProbeResult, ...]
    passed: bool
    failures: tuple[str, ...]
    max_error: Q | None
    bandwidth: BandwidthResult | None = None
    range_certificate: RangeCertificate | None = None
    objectives: tuple[DesignObjective, ...] = ()
    pareto_rank: int | None = None
    dominated_by: tuple[str, ...] = ()

    def as_dict(self, include_binding: bool = False) -> dict[str, Any]:
        result = {
            "option": self.option.as_dict(),
            "status": "pass" if self.passed else "gap",
            "probes": [item.as_dict() for item in self.probes],
            "max_relative_error": (
                q_to_json(self.max_error) if self.max_error is not None else None
            ),
            "failures": list(self.failures),
            "objectives": [item.as_dict() for item in self.objectives],
            "pareto_rank": self.pareto_rank,
            "dominated_by": list(self.dominated_by),
            "bandwidth": (
                self.bandwidth.as_dict() if self.bandwidth is not None else None
            ),
            "range_certificate": (
                self.range_certificate.as_dict()
                if self.range_certificate is not None
                else None
            ),
        }
        if include_binding and self.binding is not None:
            result["binding"] = self.binding.as_dict()
        return result


@dataclass(frozen=True)
class DesignStep:
    """One entry in the verification plan."""

    name: str
    status: str
    detail: str
    command: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
            "command": self.command,
        }


@dataclass(frozen=True)
class DesignResult:
    """A selected design or an explicit no-solution result."""

    route_name: str
    space: DesignSpace
    constraints: DesignConstraints
    candidates: tuple[DesignCandidate, ...]
    selected: DesignCandidate | None
    verification_plan: tuple[DesignStep, ...]
    ranking: DesignRanking | None = None
    gaps: tuple[str, ...] = ()

    @property
    def status(self) -> str:
        return "solved" if self.selected is not None else "gap"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "route": self.space.route_id,
            "route_name": self.space.name,
            "status": self.status,
            "input_domain": self.space.input_domain,
            "constraints": self.constraints.as_dict(),
            "candidates": [item.as_dict() for item in self.candidates],
            "selected": (
                self.selected.as_dict(include_binding=True)
                if self.selected is not None
                else None
            ),
            "verification_plan": [item.as_dict() for item in self.verification_plan],
            "fabrication_audit": fabrication_audit(self),
            "ranking": (
                self.ranking.as_dict() if self.ranking is not None else None
            ),
            "range_certificate": (
                self.selected.range_certificate.as_dict()
                if self.selected is not None
                and self.selected.range_certificate is not None
                else None
            ),
            "gaps": list(self.gaps),
        }

    def render_text(self) -> str:
        bandwidth_text = (
            f"{_decimal(self.constraints.min_bandwidth)} Hz"
            if self.constraints.min_bandwidth is not None
            else "none"
        )
        lines = [
            "=" * 78,
            "CONSTRAINED DESIGN",
            "=" * 78,
            f"Route: {self.space.name}",
            f"Status: {self.status}",
            f"Input domain: {self.space.input_domain}",
            "",
            "Constraints",
            f"  input            {self.constraints.input_value}",
            f"  input range      [{self.constraints.input_min}, {self.constraints.input_max}]",
            f"  accuracy         {self.constraints.accuracy}",
            f"  maximum cost     {self.constraints.max_cost if self.constraints.max_cost is not None else 'none'}",
            f"  minimum bandwidth {bandwidth_text}",
            "",
            "Declared candidates",
        ]
        if self.ranking is not None:
            objective_text = ", ".join(
                f"{item.name} ({item.direction})" for item in self.ranking.objectives
            )
            lines.extend(("", "Pareto ranking"))
            lines.append(f"  profile          {self.ranking.profile}")
            lines.append(f"  objectives       {objective_text}")
            lines.append(
                f"  front            {', '.join(self.ranking.front) or 'none'}"
            )
            for index, layer in enumerate(self.ranking.layers, start=1):
                lines.append(f"  rank {index:<11} {', '.join(layer)}")
            lines.append(f"  rule             {self.ranking.rule}")
            lines.append(
                f"  excluded         {', '.join(self.ranking.excluded) or 'none'}"
            )
        for item in self.candidates:
            status = "pass" if item.passed else "gap "
            error = (
                _decimal(item.max_error)
                if item.max_error is not None
                else "n/a"
            )
            rank = str(item.pareto_rank) if item.pareto_rank is not None else "n/a"
            lines.append(
                f"  [{status}] {item.option.name:<18} cost={str(item.option.cost):<3} "
                f"rank={rank:<4} max_error={error}"
            )
            if item.dominated_by:
                lines.append(
                    f"        dominated by: {', '.join(item.dominated_by)}"
                )
            for failure in item.failures:
                lines.append(f"        {failure}")
        lines.append("")
        if self.selected is None:
            lines.append("No declared candidate satisfies the constraints.")
        else:
            binding = self.selected.binding
            assert binding is not None
            lines.append("Selected design")
            lines.append(f"  option           {self.selected.option.name}")
            lines.append(f"  cost             {self.selected.option.cost}")
            parameters = ", ".join(
                f"{name}={value}"
                for name, value in self.selected.option.parameters.items()
            )
            lines.append(f"  parameters       {parameters}")
            lines.append(
                f"  max error        {_decimal(self.selected.max_error)}"
                f"  (limit {self.constraints.accuracy}; exact value in JSON)"
            )
            lines.append(
                f"  device checks    {sum(1 for item in binding.checks if item.passed)}"
                f"/{len(binding.checks)} passed"
            )
        lines.append("")
        lines.append("Fabrication audit (advisory)")
        audit = fabrication_audit(self)
        lines.append(f"  status           {audit['status']}")
        if audit.get("check_count"):
            lines.append(
                f"  checks           {audit['checks_passed']}/{audit['check_count']} passed"
            )
            if audit.get("failed_checks"):
                lines.append(
                    f"  failed           {', '.join(audit['failed_checks'])}"
                )
            thermal = audit.get("thermal") or {}
            if thermal.get("max_junction") is not None:
                lines.append(
                    f"  max junction     {_q_text(thermal['max_junction'])} K "
                    f"(limit {_q_text(thermal['limit'])} K)"
                )
        else:
            reason = (audit.get("gaps") or ["no fabrication audit was derived"])[0]
            lines.append(f"  reason           {reason}")
        lines.append(f"  command          {audit['command']}")
        lines.append("")
        lines.append("Verification plan")
        for step in self.verification_plan:
            lines.append(f"  [{step.status:<4}] {step.name}: {step.detail}")
            if step.command:
                lines.append(f"         {step.command}")
        lines.append("")
        lines.append("Remaining gaps")
        for item in self.gaps:
            lines.append(f"  - {item}")
        return "\n".join(lines)


def fabrication_audit(
    result: "DesignResult", rules: Any = None
) -> dict[str, Any]:
    """Audit a solved design against the declared fabrication checks.

    This is deliberately advisory: it never changes candidate selection, and
    the DRC/thermal result is not a manufacturing sign-off.  The full geometry
    remains available through ``cent fabricate``.
    """
    command = f"python3 cent fabricate {result.route_name}"
    payload: dict[str, Any] = {
        "schema": FABRICATION_AUDIT_SCHEMA,
        "advisory": True,
        "claim": (
            "advisory declared-geometry audit; it does not filter the design "
            "or claim a fabricated, DRC-signed-off or measured board"
        ),
        "command": command,
        "status": "not-run",
        "passed": None,
        "selected_option": (
            result.selected.option.name if result.selected is not None else None
        ),
        "check_count": 0,
        "checks_passed": 0,
        "failed_checks": [],
        "checks": [],
        "thermal": None,
        "parasitic_count": 0,
        "parasitics": [],
        "unrouted_nets": [],
        "gaps": [],
    }
    if result.selected is None or result.selected.binding is None:
        payload["gaps"] = [
            "no declared design is selected; no fabrication geometry can be audited"
        ]
        return payload
    try:
        # Local imports avoid a design -> physical -> design import cycle.
        from .fabrication import build_fabrication
        from .physical import build_physical

        plan = build_fabrication(build_physical(result), rules)
    except CentError as exc:
        payload["status"] = "gap"
        payload["passed"] = False
        payload["gaps"] = [str(exc)]
        return payload

    thermal_max = max(
        (item.junction for item in plan.thermal), default=None
    )
    checks = [item.as_dict() for item in plan.checks]
    payload.update(
        {
            "status": plan.status,
            "passed": plan.passed,
            "check_count": len(plan.checks),
            "checks_passed": sum(1 for item in plan.checks if item.passed),
            "failed_checks": [
                item.name for item in plan.checks if not item.passed
            ],
            "checks": checks,
            "thermal": {
                "ambient": q_to_json(plan.rules.ambient_temperature),
                "limit": q_to_json(plan.rules.max_junction_temperature),
                "max_junction": (
                    q_to_json(thermal_max) if thermal_max is not None else None
                ),
                "sensitive_refs": [
                    item.ref for item in plan.thermal if item.sensitive
                ],
            },
            "parasitic_count": len(plan.parasitics),
            "parasitics": [item.as_dict() for item in plan.parasitics],
            "unrouted_nets": list(plan.unrouted),
            "gaps": list(plan.gaps),
        }
    )
    return payload


COMPARISON_NOTE = (
    "Each route is solved independently under the same requested constraints; "
    "when no input is supplied, the route's declared default input is used. "
    "Cost is each route's exact declared complexity unit, and Pareto ranks are "
    "within a route. This report does not collapse the routes into a "
    "cross-route scalar score or claim a measured physical preference."
)


@dataclass(frozen=True)
class MethodComparison:
    """Independent exact design solves, with exportable per-route rows."""

    routes: tuple[str, ...]
    results: tuple[DesignResult, ...]
    note: str = COMPARISON_NOTE

    @property
    def solved_count(self) -> int:
        return sum(1 for result in self.results if result.selected is not None)

    @property
    def profile(self) -> str:
        ranking = self.results[0].ranking if self.results else None
        return ranking.profile if ranking is not None else "none"

    def rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for result in self.results:
            selected = result.selected
            rows.append(
                {
                    "route": result.route_name,
                    "route_name": result.space.name,
                    "status": result.status,
                    "selected_option": (
                        selected.option.name if selected is not None else None
                    ),
                    "selected_cost": (
                        q_to_json(selected.option.cost)
                        if selected is not None
                        else None
                    ),
                    "selected_cost_text": (
                        str(selected.option.cost)
                        if selected is not None
                        else None
                    ),
                    "max_relative_error": (
                        q_to_json(selected.max_error)
                        if selected is not None and selected.max_error is not None
                        else None
                    ),
                    "max_relative_error_text": (
                        _decimal(selected.max_error)
                        if selected is not None and selected.max_error is not None
                        else None
                    ),
                    "pareto_rank": (
                        selected.pareto_rank if selected is not None else None
                    ),
                    "front": (
                        list(result.ranking.front)
                        if result.ranking is not None
                        else []
                    ),
                    "profile": (
                        result.ranking.profile
                        if result.ranking is not None
                        else None
                    ),
                    "constraints": result.constraints.as_dict(),
                    "gaps": list(result.gaps),
                }
            )
        return rows

    def as_dict(self) -> dict[str, Any]:
        rows = self.rows()
        gaps = tuple(
            sorted({gap for result in self.results for gap in result.gaps})
        )
        return {
            "schema": COMPARISON_SCHEMA,
            "routes": list(self.routes),
            "profile": self.profile,
            "solved_count": self.solved_count,
            "rows": rows,
            "results": {
                result.route_name: result.as_dict() for result in self.results
            },
            "note": self.note,
            "markdown": self.render_markdown(),
            "gaps": list(gaps),
        }

    def render_text(self) -> str:
        lines = [
            "=" * 78,
            "METHOD COMPARISON",
            "=" * 78,
            f"Routes: {', '.join(self.routes)}",
            f"Profile: {self.profile}",
            f"Solved: {self.solved_count}/{len(self.results)}",
            "",
            "Per-route selection",
        ]
        for row in self.rows():
            selected = row["selected_option"] or "none"
            cost = row["selected_cost_text"] or "n/a"
            error = row["max_relative_error_text"] or "n/a"
            rank = (
                str(row["pareto_rank"])
                if row["pareto_rank"] is not None
                else "n/a"
            )
            lines.append(
                f"  {row['route']:<14} [{row['status']:<5}] {selected:<18} "
                f"cost={cost:<3} error={error:<12} rank={rank}"
            )
            if row["front"]:
                lines.append(f"        front: {', '.join(row['front'])}")
        lines.extend(("", "Note", f"  {self.note}", "", "Remaining gaps"))
        for gap in sorted({gap for row in self.rows() for gap in row["gaps"]}):
            lines.append(f"  - {gap}")
        return "\n".join(lines)

    def render_markdown(self) -> str:
        def cell(value: Any) -> str:
            if value is None or value == "":
                return "none"
            return str(value).replace("|", "\\|")

        lines = [
            "# Method comparison",
            "",
            f"**Routes:** {', '.join(self.routes)}  ",
            f"**Ranking profile:** `{self.profile}`  ",
            f"**Solved:** {self.solved_count}/{len(self.results)}",
            "",
            "| Route | Status | Selected | Cost | Max relative error | Pareto rank | Front |",
            "|---|---|---|---|---|---|---|",
        ]
        for row in self.rows():
            lines.append(
                "| "
                + " | ".join(
                    cell(value)
                    for value in (
                        row["route"],
                        row["status"],
                        row["selected_option"],
                        row["selected_cost_text"],
                        row["max_relative_error_text"],
                        row["pareto_rank"],
                        ", ".join(row["front"]) or None,
                    )
                )
                + " |"
            )
        lines.extend(
            (
                "",
                "## Requested constraints",
                "",
                "| Route | Input | Range | Accuracy | Max cost | Min bandwidth |",
                "|---|---|---|---|---|---|",
            )
        )
        for row in self.rows():
            constraints = row["constraints"]
            input_range = constraints["input_range"]
            lines.append(
                "| "
                + " | ".join(
                    cell(value)
                    for value in (
                        row["route"],
                        _q_text(constraints["input"]),
                        f"{_q_text(input_range['min'])}:{_q_text(input_range['max'])}",
                        _q_text(constraints["accuracy"]),
                        _q_text(constraints["max_cost"]),
                        _q_text(constraints["min_bandwidth"]),
                    )
                )
                + " |"
            )
        lines.extend(("", "## Note", "", self.note))
        return "\n".join(lines)


BASE_GAPS = (
    "The search covers only the declared design alternatives; arbitrary component synthesis is not performed.",
    "The continuous-range certificate uses declared monotone error/bandwidth directions and endpoint stress; undeclared non-monotone terms still require a separate proof.",
    "Cost is an exact declared complexity unit, not currency, BOM cost or yield.",
    "Ranking is exact Pareto dominance over the declared objectives; the exact-static profile has no noise model and no weighted scalar score is hidden in the selection tie-break.",
    "Only declared dynamic models are run: an exact sampled RC/clock loop and adaptive step-doubling nonlinear compute-route transients with continuous bounded-state, monotone-stability and certified local-truncation error certificates; noise, drift and measured parasitics remain gaps. Bandwidth is checked only over the declared small-signal poles at the range endpoints.",
    "Only a reference topology and schematic floorplan can be emitted; no fabrication-ready netlist, manufacturing geometry, measured-device evidence or calibration plan is produced.",
)


def _make_constraints(
    *,
    input_value: Any | None,
    input_min: Any | None,
    input_max: Any | None,
    accuracy: Any,
    max_cost: Any | None,
    min_bandwidth: Any | None,
    space: DesignSpace,
) -> DesignConstraints:
    value = _exact(
        space.default_input if input_value is None else input_value, "input_value"
    )
    low = _exact(value if input_min is None else input_min, "input_min")
    high = _exact(value if input_max is None else input_max, "input_max")
    acc = _positive(accuracy, "accuracy")
    if low > high:
        raise CentError(ErrorCode.INVALID_INPUT, "input_min must be <= input_max")
    if not (low <= value <= high):
        raise CentError(
            ErrorCode.INVALID_INPUT, "input_value must lie inside the declared input range"
        )
    ceiling = None
    if max_cost is not None:
        ceiling = _exact(max_cost, "max_cost")
        if ceiling < 0:
            raise CentError(ErrorCode.DOMAIN_ERROR, "max_cost must be nonnegative")
    bandwidth = None
    if min_bandwidth is not None:
        bandwidth = _positive(min_bandwidth, "min_bandwidth")
    return DesignConstraints(
        input_value=value,
        input_min=low,
        input_max=high,
        accuracy=acc,
        max_cost=ceiling,
        min_bandwidth=bandwidth,
    )


def _bandwidth_result(binding: DeviceBinding, requested: Q) -> BandwidthResult:
    """Classify every declared pole against a requested minimum bandwidth.

    The exact frequency is ``1 / (2*pi*tau)``.  ``pi`` is irrational, so the
    check uses a certified rational enclosure: the lower endpoint divides by
    the upper bound on pi and the upper endpoint by the lower bound.  A target
    is accepted only when the certified lower endpoint meets it; a target is
    rejected only when the certified upper endpoint misses it; the narrow
    band between those outcomes is reported as a gap rather than guessed.
    """
    poles: list[PoleBandwidth] = []
    for pole in binding.poles:
        tau = pole.time_constant
        if tau <= 0:
            raise CentError(
                ErrorCode.DOMAIN_ERROR,
                f"pole {pole.name!r} must have a positive time constant",
            )
        lower = 1 / (2 * PI_BOUNDS.hi * tau)
        upper = 1 / (2 * PI_BOUNDS.lo * tau)
        if lower >= requested:
            status = "pass"
        elif upper < requested:
            status = "fail"
        else:
            status = "gap"
        poles.append(
            PoleBandwidth(
                name=pole.name,
                symbol=pole.symbol,
                time_constant=tau,
                lower_hz=lower,
                upper_hz=upper,
                status=status,
            )
        )
    slowest = max(poles, key=lambda item: (item.time_constant, item.name), default=None)
    return BandwidthResult(
        requested_hz=requested,
        poles=tuple(poles),
        slowest=slowest,
        status="gap" if slowest is None else slowest.status,
    )


def _continuous_range_certificate(
    space: DesignSpace,
    constraints: DesignConstraints,
    probes: tuple[ProbeResult, ...],
) -> RangeCertificate:
    """Assemble an explicit continuous-range certificate.

    The certificate uses the declared monotone direction of the route's exact
    error budget, checks the endpoint with the worst declared stress, and
    compares the certified bandwidth brackets.  It is deliberately declared
    evidence, not a numerical sampling claim: an unknown direction or a
    non-monotone endpoint pair returns ``gap``.
    """
    low = constraints.input_min
    high = constraints.input_max
    by_value = {probe.input_value: probe for probe in probes}
    low_probe = by_value.get(low)
    high_probe = by_value.get(high)
    if low == high:
        probe = low_probe
        if probe is None:
            return RangeCertificate(
                "gap",
                "single-point range",
                low,
                high,
                None,
                None,
                space.range_error_direction,
                space.range_bandwidth_direction,
                "the declared single input point has no probe result",
            )
        return RangeCertificate(
            "pass" if probe.passed else "gap",
            "single declared input point",
            low,
            high,
            probe.total_error,
            low,
            space.range_error_direction,
            space.range_bandwidth_direction,
            (
                "single-point range: the exact binding at the operating point "
                "passes all declared checks"
                if probe.passed
                else "the single declared input point does not pass its binding"
            ),
        )

    if low_probe is None or high_probe is None:
        return RangeCertificate(
            "gap",
            "declared monotone budget",
            low,
            high,
            None,
            None,
            space.range_error_direction,
            space.range_bandwidth_direction,
            "the declared range does not have both endpoint probes",
        )

    errors = [
        probe.total_error for probe in probes if probe.total_error is not None
    ]
    if len(errors) != len(probes):
        return RangeCertificate(
            "gap",
            "declared monotone budget",
            low,
            high,
            None,
            None,
            space.range_error_direction,
            space.range_bandwidth_direction,
            "one or more probes has no exact error budget",
        )

    max_error = max(errors)
    max_probe = max(probes, key=lambda probe: probe.total_error or Fraction(0))
    direction = space.range_error_direction
    if direction == "decreasing":
        error_ok = (
            low_probe.total_error is not None
            and high_probe.total_error is not None
            and low_probe.total_error >= high_probe.total_error
            and max_error == low_probe.total_error
        )
        max_error_at = low
    elif direction == "increasing":
        error_ok = (
            low_probe.total_error is not None
            and high_probe.total_error is not None
            and high_probe.total_error >= low_probe.total_error
            and max_error == high_probe.total_error
        )
        max_error_at = high
    elif direction == "constant":
        error_ok = all(value == errors[0] for value in errors[1:])
        max_error_at = max_probe.input_value
    else:
        error_ok = False
        max_error_at = None

    bandwidth_ok = True
    if constraints.min_bandwidth is not None:
        low_bandwidth = low_probe.bandwidth
        high_bandwidth = high_probe.bandwidth
        if low_bandwidth is None or high_bandwidth is None:
            bandwidth_ok = False
        elif space.range_bandwidth_direction == "increasing":
            low_pole = low_bandwidth.slowest
            high_pole = high_bandwidth.slowest
            bandwidth_ok = (
                low_bandwidth.passed
                and high_bandwidth.passed
                and low_pole is not None
                and high_pole is not None
                and low_pole.lower_hz <= high_pole.lower_hz
            )
        elif space.range_bandwidth_direction == "constant":
            low_pole = low_bandwidth.slowest
            high_pole = high_bandwidth.slowest
            bandwidth_ok = (
                low_bandwidth.passed
                and high_bandwidth.passed
                and low_pole is not None
                and high_pole is not None
                and low_pole.lower_hz == high_pole.lower_hz
            )
        else:
            bandwidth_ok = False

    endpoint_pass = all(probe.passed for probe in probes)
    proof = error_ok and max_error <= constraints.accuracy and bandwidth_ok and endpoint_pass
    if proof:
        detail = (
            f"continuous range [{low}, {high}] uses the declared "
            f"{direction} exact error budget and endpoint stress; max error "
            f"{_decimal(max_error)} at {max_error_at}; all endpoint checks pass"
        )
    else:
        reasons: list[str] = []
        if not error_ok:
            reasons.append(
                f"the endpoint errors are not consistent with the declared "
                f"{direction} direction"
            )
        if max_error > constraints.accuracy:
            reasons.append(
                f"max error {_decimal(max_error)} exceeds {_decimal(constraints.accuracy)}"
            )
        if not bandwidth_ok:
            reasons.append("the certified bandwidth brackets do not cover the range")
        if not endpoint_pass:
            reasons.append("at least one endpoint probe fails")
        detail = "range certificate gap: " + "; ".join(reasons)
    return RangeCertificate(
        "pass" if proof else "gap",
        "declared monotone error budget + endpoint stress",
        low,
        high,
        max_error,
        max_error_at,
        direction,
        space.range_bandwidth_direction,
        detail,
    )


def _evaluate_option(
    space: DesignSpace,
    option: DesignOption,
    constraints: DesignConstraints,
) -> DesignCandidate:
    kwargs = dict(option.parameters)
    probes: list[ProbeResult] = []
    failures: list[str] = []
    primary: DeviceBinding | None = None
    primary_bandwidth: BandwidthResult | None = None
    max_error: Q | None = None

    for value in constraints.probes:
        bandwidth: BandwidthResult | None = None
        try:
            binding = space.binding(
                input_value=value,
                error_limit=constraints.accuracy,
                **kwargs,
            )
        except CentError as exc:
            message = str(exc)
            probes.append(
                ProbeResult(
                    input_value=value,
                    passed=False,
                    total_error=None,
                    checks_passed=0,
                    checks_total=0,
                    failures=(message,),
                )
            )
            failures.append(f"{value}: {message}")
            continue

        total = binding.total_error
        if max_error is None or total > max_error:
            max_error = total
        failures_at_probe: list[str] = []
        if constraints.min_bandwidth is not None:
            bandwidth = _bandwidth_result(binding, constraints.min_bandwidth)
            if not bandwidth.passed:
                failures_at_probe.append(f"bandwidth: {bandwidth.detail}")
        if not binding.passed:
            failed = [item.name for item in binding.checks if not item.passed]
            if total > constraints.accuracy:
                failures_at_probe.append(
                    f"relative error {total} exceeds {constraints.accuracy}"
                )
            if failed:
                failures_at_probe.append("failed checks: " + ", ".join(failed))
            if not failures_at_probe:
                failures_at_probe.append("device binding did not pass")
        passed = not failures_at_probe
        probes.append(
            ProbeResult(
                input_value=value,
                passed=passed,
                total_error=total,
                checks_passed=sum(1 for item in binding.checks if item.passed),
                checks_total=len(binding.checks),
                failures=tuple(failures_at_probe),
                bandwidth=bandwidth,
            )
        )
        if value == constraints.input_value:
            primary = binding
            primary_bandwidth = bandwidth
        if failures_at_probe:
            failures.extend(f"{value}: {item}" for item in failures_at_probe)

    cost_exceeded = (
        constraints.max_cost is not None and option.cost > constraints.max_cost
    )
    if cost_exceeded:
        failures.append(
            f"cost {option.cost} exceeds declared maximum {constraints.max_cost}"
        )
    range_certificate = _continuous_range_certificate(
        space, constraints, tuple(probes)
    )
    if range_certificate.status != "pass":
        failures.append(f"continuous range: {range_certificate.detail}")
    passed = (
        bool(probes)
        and all(item.passed for item in probes)
        and not cost_exceeded
        and range_certificate.status == "pass"
    )
    return DesignCandidate(
        option=option,
        binding=primary,
        probes=tuple(probes),
        passed=passed,
        failures=tuple(failures),
        max_error=max_error,
        bandwidth=primary_bandwidth,
        range_certificate=range_certificate,
    )


def _dominates(
    left: tuple[Q, ...], right: tuple[Q, ...], directions: tuple[str, ...]
) -> bool:
    """Whether the left objective vector strictly Pareto-dominates the right."""
    better = False
    for a, b, direction in zip(left, right, directions):
        if direction == "min":
            if a > b:
                return False
            better = better or a < b
        elif direction == "max":
            if a < b:
                return False
            better = better or a > b
        else:  # pragma: no cover - profile construction is closed
            raise CentError(
                ErrorCode.DOMAIN_ERROR, f"unknown ranking direction {direction!r}"
            )
    return better


def _pareto_layers(
    values: Mapping[str, tuple[Q, ...]], directions: tuple[str, ...]
) -> tuple[tuple[str, ...], ...]:
    """Exact non-dominated sorting; rank 1 is the Pareto front."""
    remaining = list(values)
    layers: list[tuple[str, ...]] = []
    while remaining:
        layer = tuple(
            name
            for name in remaining
            if not any(
                _dominates(values[other], values[name], directions)
                for other in remaining
                if other != name
            )
        )
        if not layer:  # pragma: no cover - dominance is a strict partial order
            raise CentError(ErrorCode.DOMAIN_ERROR, "Pareto ranking did not converge")
        layers.append(layer)
        remaining = [name for name in remaining if name not in layer]
    return tuple(layers)


def _resolve_ranking(requested: str, constraints: DesignConstraints) -> str:
    if requested == "auto":
        return (
            "dynamic-aware"
            if constraints.min_bandwidth is not None
            else "exact-static"
        )
    if requested not in RANKING_PROFILES:
        raise CentError(
            ErrorCode.INVALID_INPUT,
            f"unknown ranking profile {requested!r}; expected auto, "
            + ", ".join(RANKING_PROFILES),
        )
    if requested == "dynamic-aware" and constraints.min_bandwidth is None:
        raise CentError(
            ErrorCode.INVALID_INPUT,
            "dynamic-aware ranking requires a declared minimum bandwidth",
        )
    return requested


def _ranking_specs(profile: str) -> tuple[RankingObjectiveSpec, ...]:
    specs = [
        RankingObjectiveSpec("cost", "min", "declared complexity unit"),
        RankingObjectiveSpec(
            "max_relative_error", "min", "exact worst-probe relative error"
        ),
    ]
    if profile == "dynamic-aware":
        specs.append(
            RankingObjectiveSpec(
                "certified_bandwidth",
                "max",
                "certified lower bound on the slowest declared pole bandwidth",
            )
        )
    return tuple(specs)


def _rank_candidates(
    candidates: tuple[DesignCandidate, ...],
    constraints: DesignConstraints,
    profile: str,
) -> tuple[tuple[DesignCandidate, ...], DesignRanking]:
    """Filter by hard constraints, sort the feasible set into exact layers."""
    specs = _ranking_specs(profile)
    directions = tuple(item.direction for item in specs)
    feasible = {item.option.name: item for item in candidates if item.passed}
    values: dict[str, tuple[Q, ...]] = {}
    unranked: list[str] = []
    for name, candidate in feasible.items():
        numbers = [candidate.option.cost]
        if candidate.max_error is None:
            unranked.append(name)
            continue
        numbers.append(candidate.max_error)
        if profile == "dynamic-aware":
            lower = (
                candidate.bandwidth.slowest.lower_hz
                if candidate.bandwidth is not None
                and candidate.bandwidth.slowest is not None
                else None
            )
            if lower is None:
                unranked.append(name)
                continue
            numbers.append(lower)
        values[name] = tuple(numbers)

    layers = _pareto_layers(values, directions) if values else ()
    ranks = {
        name: index
        for index, layer in enumerate(layers, start=1)
        for name in layer
    }
    dominated = {
        name: tuple(
            sorted(
                other
                for other in values
                if other != name
                and _dominates(values[other], values[name], directions)
            )
        )
        for name in values
    }
    front = layers[0] if layers else ()
    selected = min(
        [feasible[name] for name in front],
        key=lambda item: (
            item.option.cost,
            item.max_error if item.max_error is not None else Fraction(0),
            item.option.name,
        ),
        default=None,
    )

    def objectives_for(
        candidate: DesignCandidate,
    ) -> tuple[DesignObjective, ...]:
        numbers = values.get(candidate.option.name)
        if numbers is None:
            return ()
        return tuple(
            DesignObjective(spec.name, spec.direction, value, spec.source)
            for spec, value in zip(specs, numbers)
        )

    updated = tuple(
        replace(
            item,
            objectives=objectives_for(item),
            pareto_rank=ranks.get(item.option.name),
            dominated_by=dominated.get(item.option.name, ()),
        )
        for item in candidates
    )
    excluded = tuple(
        sorted(item.option.name for item in candidates if not item.passed)
    )
    detail = (
        "dynamic-aware Pareto front over exact cost, worst-probe relative error "
        "and the certified lower bound of the slowest declared pole; no noise "
        "model is declared, so no stochastic or SNR objective is invented"
        if profile == "dynamic-aware"
        else (
            "exact-static Pareto front over exact cost and worst-probe relative "
            "error; no noise model is declared, so no stochastic or SNR objective "
            "is invented"
        )
    )
    ranking = DesignRanking(
        profile=profile,
        objectives=specs,
        front=front,
        layers=layers,
        unranked=tuple(sorted(unranked)),
        excluded=excluded,
        selected=selected.option.name if selected is not None else None,
        rule=(
            "lowest declared cost within the Pareto front; lowest max relative "
            "error, then option name break exact ties"
        ),
        detail=detail,
    )
    return updated, ranking


def _binding_command(
    route_name: str,
    constraints: DesignConstraints,
    option: DesignOption,
) -> str:
    flags = {
        "offset_ratio": "--offset-ratio",
        "precision": "--precision",
        "amplifier_gain": "--amplifier-gain",
    }
    parts = [
        "python3",
        "cent",
        "bind",
        route_name,
        "--input",
        str(constraints.input_value),
        "--error-limit",
        str(constraints.accuracy),
    ]
    for name, value in option.parameters.items():
        flag = flags.get(name)
        if flag:
            parts.extend((flag, str(value)))
    return " ".join(parts)


def _physical_command(route_name: str, constraints: DesignConstraints) -> str:
    """Executable command for the selected design's reference artifacts."""
    parts = [
        "python3",
        "cent",
        "physical",
        route_name,
        "--input",
        str(constraints.input_value),
        "--accuracy",
        str(constraints.accuracy),
    ]
    if (
        constraints.input_min != constraints.input_value
        or constraints.input_max != constraints.input_value
    ):
        parts.extend(("--range", f"{constraints.input_min}:{constraints.input_max}"))
    if constraints.max_cost is not None:
        parts.extend(("--max-cost", str(constraints.max_cost)))
    if constraints.min_bandwidth is not None:
        parts.extend(("--min-bandwidth", str(constraints.min_bandwidth)))
    return " ".join(parts)


def _dynamics_command(route_name: str, constraints: DesignConstraints) -> str:
    """Executable command for the selected design's sampled-data check."""
    parts = [
        "python3",
        "cent",
        "dynamics",
        route_name,
        "--input",
        str(constraints.input_value),
        "--accuracy",
        str(constraints.accuracy),
        "--samples",
        "64",
    ]
    if (
        constraints.input_min != constraints.input_value
        or constraints.input_max != constraints.input_value
    ):
        parts.extend(("--range", f"{constraints.input_min}:{constraints.input_max}"))
    if constraints.max_cost is not None:
        parts.extend(("--max-cost", str(constraints.max_cost)))
    if constraints.min_bandwidth is not None:
        parts.extend(("--min-bandwidth", str(constraints.min_bandwidth)))
    return " ".join(parts)


def _solve_command(
    route_name: str,
    constraints: DesignConstraints,
    ranking_profile: str = "auto",
) -> str:
    """Executable command for the exact solver constraints."""
    parts = [
        "python3",
        "cent",
        "solve",
        route_name,
        "--input",
        str(constraints.input_value),
        "--accuracy",
        str(constraints.accuracy),
    ]
    if (
        constraints.input_min != constraints.input_value
        or constraints.input_max != constraints.input_value
    ):
        parts.extend(("--range", f"{constraints.input_min}:{constraints.input_max}"))
    if constraints.max_cost is not None:
        parts.extend(("--max-cost", str(constraints.max_cost)))
    if constraints.min_bandwidth is not None:
        parts.extend(("--min-bandwidth", str(constraints.min_bandwidth)))
    if ranking_profile != "auto":
        parts.extend(("--ranking", ranking_profile))
    return " ".join(parts)


def _plan(
    route_name: str,
    constraints: DesignConstraints,
    selected: DesignCandidate | None,
    candidate_count: int,
    ranking: DesignRanking,
) -> tuple[DesignStep, ...]:
    steps: list[DesignStep] = []
    if selected is not None and selected.binding is not None:
        binding = selected.binding
        steps.append(
            DesignStep(
                "Declared exact binding",
                "pass",
                f"{sum(1 for item in binding.checks if item.passed)}/{len(binding.checks)} "
                "device-law checks pass at the declared input",
                _binding_command(route_name, constraints, selected.option),
            )
        )
        steps.append(
            DesignStep(
                "Accuracy and cost",
                "pass",
                f"max relative error {_decimal(selected.max_error)} <= {constraints.accuracy}; "
                f"cost {selected.option.cost}"
                + (
                    f" <= {constraints.max_cost}"
                    if constraints.max_cost is not None
                    else " with no cost ceiling"
                ),
                None,
            )
        )
        steps.append(
            DesignStep(
                "Pareto ranking",
                "pass" if ranking.front else "gap",
                f"profile {ranking.profile}; front "
                f"{', '.join(ranking.front) or 'none'}; {ranking.rule}",
                _solve_command(route_name, constraints, ranking.profile),
            )
        )
        if constraints.min_bandwidth is not None and selected.bandwidth is not None:
            steps.append(
                DesignStep(
                    "Declared-pole bandwidth",
                    "pass" if selected.bandwidth.passed else "gap",
                    selected.bandwidth.detail,
                    _solve_command(route_name, constraints, ranking.profile),
                )
            )
        range_certificate = selected.range_certificate
        steps.append(
            DesignStep(
                "Continuous range certificate",
                (
                    range_certificate.status
                    if range_certificate is not None
                    else "gap"
                ),
                (
                    range_certificate.detail
                    if range_certificate is not None
                    else "no range certificate was assembled"
                ),
                None,
            )
        )
        steps.append(
            DesignStep(
                "Reference netlist / floorplan",
                "pass",
                "topology-derived reference netlist, schematic stage floorplan and declared fabrication geometry are available; a manufactured board remains a gap",
                _physical_command(route_name, constraints),
            )
        )
    else:
        steps.append(
            DesignStep(
                "Declared exact binding",
                "gap",
                f"{candidate_count} declared candidate(s) evaluated; none satisfies all constraints",
                None,
            )
        )
        steps.append(
            DesignStep(
                "Pareto ranking",
                "gap" if not ranking.front else "pass",
                f"profile {ranking.profile}; "
                f"{len(ranking.front)} feasible front candidate(s)",
                _solve_command(route_name, constraints, ranking.profile),
            )
        )
        steps.append(
            DesignStep(
                "Reference netlist / floorplan",
                "gap",
                "no selected design; no reference artifacts were emitted",
                None,
            )
        )
        if constraints.min_bandwidth is not None:
            steps.append(
                DesignStep(
                    "Declared-pole bandwidth",
                    "gap",
                    "no selected design; the requested minimum bandwidth was not met",
                    _solve_command(route_name, constraints, ranking.profile),
                )
            )
    if selected is not None and selected.binding is not None:
        dynamic_status = "partial"
        if route_name == "delta-sigma":
            dynamic_detail = (
                "exact sampled RC/clock check exposes the finite one-tick gain; "
                "large-signal stability, noise, drift and fabrication remain gaps"
            )
        elif route_name == "sqrt-log":
            dynamic_detail = (
                "declared adaptive nonlinear large-signal diode/load transient "
                "with bounded-state, monotone-stability and certified "
                "local-truncation certificates; the global bound still exceeds "
                "the 1e-3 V target, and buffer pole and measured parasitics remain gaps"
            )
        else:
            dynamic_detail = (
                "declared adaptive slope-normalized nonlinear closed-loop transient "
                "with bounded-state, scalar-stability and certified "
                "local-truncation certificates; the global bound still exceeds "
                "the 1e-3 V target, and slew and measured poles remain gaps"
            )
        dynamic_command = _dynamics_command(route_name, constraints)
    else:
        dynamic_status = "gap"
        dynamic_detail = "no selected design; no dynamic model was run"
        dynamic_command = None
    steps.extend(
        (
            DesignStep(
                "Measured device evidence",
                "gap",
                "no datasheet, measurement or calibration data is attached",
                None,
            ),
            DesignStep(
                "Dynamic behavior",
                dynamic_status,
                dynamic_detail,
                dynamic_command,
            ),
            DesignStep(
                "Fabrication / yield",
                "gap",
                "no fabrication process, tolerance yield or test plan is modeled",
                None,
            ),
        )
    )
    return tuple(steps)


def solve_route(
    route_name: str,
    *,
    input_value: Any | None = None,
    input_min: Any | None = None,
    input_max: Any | None = None,
    accuracy: Any = DEFAULT_ERROR_LIMIT,
    max_cost: Any | None = None,
    min_bandwidth: Any | None = None,
    ranking: str = "auto",
) -> DesignResult:
    """Select the cheapest candidate on the exact declared Pareto front.

    All numeric inputs are exact rationals.  The declared input range is checked
    at its endpoints and at the requested operating point, then combined with
    the route's declared monotone error/bandwidth directions into a continuous
    range certificate; an undeclared or non-monotone case remains a gap.  A
    requested minimum bandwidth is checked against every declared small-signal
    pole at each probe with a certified pi enclosure; it is not a large-signal
    stability claim.
    """
    space = DESIGN_SPACES.get(route_name)
    if space is None:
        raise CentError(
            ErrorCode.UNSUPPORTED,
            f"no declared design space for route {route_name!r}",
        )
    constraints = _make_constraints(
        input_value=input_value,
        input_min=input_min,
        input_max=input_max,
        accuracy=accuracy,
        max_cost=max_cost,
        min_bandwidth=min_bandwidth,
        space=space,
    )
    candidates = tuple(
        _evaluate_option(space, option, constraints) for option in space.options
    )
    profile = _resolve_ranking(ranking, constraints)
    candidates, ranking_result = _rank_candidates(
        candidates, constraints, profile
    )
    selected = next(
        (
            item
            for item in candidates
            if item.option.name == ranking_result.selected
        ),
        None,
    )
    gaps = list(BASE_GAPS)
    if selected is None:
        gaps.append("No declared design alternative satisfies the requested constraints.")
    elif selected.binding is not None:
        gaps.extend(selected.binding.gaps)
    return DesignResult(
        route_name=route_name,
        space=space,
        constraints=constraints,
        candidates=candidates,
        selected=selected,
        verification_plan=_plan(
            route_name, constraints, selected, len(candidates), ranking_result
        ),
        ranking=ranking_result,
        gaps=tuple(gaps),
    )


def _comparison_route_names(routes: Any | None) -> tuple[str, ...]:
    """Validate and de-duplicate a declared-route selection."""
    if routes is None:
        return tuple(DESIGN_SPACES)
    if isinstance(routes, str):
        raw: list[Any] = routes.split(",")
    else:
        try:
            raw = list(routes)
        except TypeError as exc:
            raise CentError(
                ErrorCode.TYPE_ERROR, "routes must be a list of declared route names"
            ) from exc
    names: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            raise CentError(
                ErrorCode.TYPE_ERROR, "routes must contain declared route names"
            )
        name = item.strip()
        if not name:
            continue
        if name not in DESIGN_SPACES:
            raise CentError(
                ErrorCode.UNSUPPORTED,
                f"no declared design space for route {name!r}",
            )
        if name not in names:
            names.append(name)
    if not names:
        raise CentError(
            ErrorCode.INVALID_INPUT, "compare needs at least one declared route"
        )
    return tuple(names)


def compare_routes(
    routes: Any | None = None,
    *,
    input_value: Any | None = None,
    input_min: Any | None = None,
    input_max: Any | None = None,
    accuracy: Any = DEFAULT_ERROR_LIMIT,
    max_cost: Any | None = None,
    min_bandwidth: Any | None = None,
    ranking: str = "auto",
) -> MethodComparison:
    """Solve several declared routes independently for a comparison report.

    The constraints are shared when supplied.  A missing input keeps each
    route's own declared default input, which avoids pretending that the three
    routes have the same operating domain.  No cross-route scalar score is
    computed; each route retains its own exact Pareto result.
    """
    names = _comparison_route_names(routes)
    results = tuple(
        solve_route(
            name,
            input_value=input_value,
            input_min=input_min,
            input_max=input_max,
            accuracy=accuracy,
            max_cost=max_cost,
            min_bandwidth=min_bandwidth,
            ranking=ranking,
        )
        for name in names
    )
    return MethodComparison(routes=names, results=results)


def design_space_catalog() -> dict[str, Any]:
    """Return the declared design spaces without running a binding.

    This is the UI/API index: it exposes only names, exact defaults and the
    declared alternatives.  The actual checks are still performed by
    :func:`solve_route`.
    """
    return {
        "schema": SCHEMA,
        "ranking_profiles": list(RANKING_PROFILES),
        "default_ranking": "auto",
        "spaces": [
            {
                "route": route,
                "name": space.name,
                "input_domain": space.input_domain,
                "default_input": str(space.default_input),
                "default_accuracy": str(DEFAULT_ERROR_LIMIT),
                "options": [
                    {
                        "name": option.name,
                        "cost": str(option.cost),
                        "parameters": {
                            key: str(value)
                            for key, value in option.parameters.items()
                        },
                    }
                    for option in space.options
                ],
            }
            for route, space in DESIGN_SPACES.items()
        ],
    }


__all__ = [
    "BASE_GAPS",
    "BandwidthResult",
    "COMPARISON_SCHEMA",
    "DESIGN_SPACES",
    "FABRICATION_AUDIT_SCHEMA",
    "MethodComparison",
    "DesignCandidate",
    "DesignConstraints",
    "DesignObjective",
    "DesignOption",
    "DesignRanking",
    "DesignResult",
    "DesignSpace",
    "DesignStep",
    "PI_BOUNDS",
    "RANKING_PROFILES",
    "RankingObjectiveSpec",
    "PoleBandwidth",
    "ProbeResult",
    "RangeCertificate",
    "SCHEMA",
    "compare_routes",
    "design_space_catalog",
    "fabrication_audit",
    "solve_route",
]
