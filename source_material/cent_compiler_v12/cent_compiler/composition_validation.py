"""Executable validation for declared composed transfer chains.

The single-operation transfer validator is intentionally operation-local.  This
module owns the small declared registry of composed chains.  Each chain has a
source route, an independent target adapter and fixed exact-rational vectors.
The certificate covers only those vectors and never claims a measured device.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Callable

from . import assembly
from .exact import q_to_json
from .targets import glm

CHAIN_SCHEMA = "cent-transfer-composition/1"
CERTIFICATE_SCHEMA = "cent-transfer-composition-certificate/1"
INTERFACE_SCHEMA = "cent-stage-interface/1"
BOUNDARY_SCHEMA = "cent-stage-boundary/1"
MULT_DIV_CHAIN = "mult-div"
MULT_RECIPROCAL_CHAIN = "mult-reciprocal"
DIV_MULT_CHAIN = "div-mult"
CLAIM = (
    "This certificate covers only declared composed log-domain reference "
    "routes and glm-reference adapters over fixed exact rational vectors. It "
    "is not a measured junction, a composed device, a real GLM interface or an "
    "end-to-end performance result."
)


@dataclass(frozen=True)
class InterfacePort:
    """A declared stage port kind, domain and wire representation."""

    name: str
    kind: str
    domain: str
    representation: str
    accepts: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "domain": self.domain,
            "representation": self.representation,
            "accepts": list(self.accepts),
        }


@dataclass(frozen=True)
class StageInterface:
    """The typed input/output interface of one transfer operation."""

    operation: str
    inputs: tuple[InterfacePort, ...]
    output: InterfacePort

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": INTERFACE_SCHEMA,
            "operation": self.operation,
            "inputs": [port.as_dict() for port in self.inputs],
            "output": self.output.as_dict(),
        }


_POSITIVE_INPUT = "positive-normalized"
_LOG_DOMAIN = "log-domain-normalized"
_VALUE_KIND = "normalized-value"
_INTERVAL_KIND = "certified-interval"
_ACCEPTS = ("exact-rational", _INTERVAL_KIND)


def _input_port(name: str, domain: str) -> InterfacePort:
    return InterfacePort(
        name=name,
        kind=_VALUE_KIND,
        domain=domain,
        representation="exact-rational-or-endpoints",
        accepts=_ACCEPTS,
    )


def _output_port(domain: str) -> InterfacePort:
    return InterfacePort(
        name="value",
        kind=_INTERVAL_KIND,
        domain=domain,
        representation="exact-rational-endpoints",
    )


STAGE_INTERFACES: dict[str, StageInterface] = {
    "log": StageInterface(
        operation="log",
        inputs=(_input_port("x", _POSITIVE_INPUT),),
        output=_output_port(_LOG_DOMAIN),
    ),
    "exp": StageInterface(
        operation="exp",
        inputs=(_input_port("x", _LOG_DOMAIN),),
        output=_output_port(_POSITIVE_INPUT),
    ),
    "mult": StageInterface(
        operation="mult",
        inputs=(_input_port("a", _POSITIVE_INPUT),
                _input_port("b", _POSITIVE_INPUT)),
        output=_output_port(_POSITIVE_INPUT),
    ),
    "div": StageInterface(
        operation="div",
        inputs=(_input_port("a", _POSITIVE_INPUT),
                _input_port("b", _POSITIVE_INPUT)),
        output=_output_port(_POSITIVE_INPUT),
    ),
    "reciprocal": StageInterface(
        operation="reciprocal",
        inputs=(_input_port("x", _POSITIVE_INPUT),),
        output=_output_port(_POSITIVE_INPUT),
    ),
}


@dataclass(frozen=True)
class ChainSpec:
    """One declared composed chain and its independent target adapter."""

    id: str
    name: str
    stages: tuple[str, ...]
    input_names: tuple[str, ...]
    first_op: str
    terminal_op: str
    terminal_slot: int
    constant_slot: int | None
    constant_value: Fraction | None
    stage_boundary_slots: tuple[int, ...]
    stage_boundary_wires: tuple[str, ...]
    source_route: Callable[..., assembly.ArithmeticRoute]
    target_adapter: glm.AdapterSpec
    vectors: tuple[glm.ArithmeticVector, ...]
    gaps: tuple[str, ...]


CHAIN_REGISTRY: dict[str, ChainSpec] = {
    MULT_DIV_CHAIN: ChainSpec(
        id=MULT_DIV_CHAIN,
        name="log-domain mult -> div",
        stages=("mult", "div"),
        input_names=("a", "b", "c"),
        first_op="mult",
        terminal_op="div",
        terminal_slot=0,
        constant_slot=None,
        constant_value=None,
        stage_boundary_slots=(0,),
        stage_boundary_wires=("_mult1",),
        source_route=assembly.log_domain_mult_div_route,
        target_adapter=glm.MULT_DIV_ADAPTER,
        vectors=glm.MULT_DIV_VECTORS,
        gaps=(
            "software target simulation only; no measured junction or composed device",
            "no real GLM interface, model call or runtime integration",
            "positive normalized inputs only",
            "only declared registry chains are certified; other compositions remain per-stage",
        ),
    ),
    MULT_RECIPROCAL_CHAIN: ChainSpec(
        id=MULT_RECIPROCAL_CHAIN,
        name="log-domain mult -> reciprocal",
        stages=("mult", "reciprocal"),
        input_names=("a", "b"),
        first_op="mult",
        terminal_op="div",
        terminal_slot=1,
        constant_slot=0,
        constant_value=Fraction(1),
        stage_boundary_slots=(0,),
        stage_boundary_wires=("_mult1",),
        source_route=assembly.log_domain_mult_reciprocal_route,
        target_adapter=glm.MULT_RECIPROCAL_ADAPTER,
        vectors=glm.MULT_RECIPROCAL_VECTORS,
        gaps=(
            "software target simulation only; no measured junction or composed device",
            "no real GLM interface, model call or runtime integration",
            "positive normalized inputs only",
            "only declared registry chains are certified; other compositions remain per-stage",
        ),
    ),
    DIV_MULT_CHAIN: ChainSpec(
        id=DIV_MULT_CHAIN,
        name="log-domain div -> mult",
        stages=("div", "mult"),
        input_names=("a", "b", "c"),
        first_op="div",
        terminal_op="mult",
        terminal_slot=0,
        constant_slot=None,
        constant_value=None,
        stage_boundary_slots=(0,),
        stage_boundary_wires=("_div1",),
        source_route=assembly.log_domain_div_mult_route,
        target_adapter=glm.DIV_MULT_ADAPTER,
        vectors=glm.DIV_MULT_VECTORS,
        gaps=(
            "software target simulation only; no measured junction or composed device",
            "no real GLM interface, model call or runtime integration",
            "positive normalized inputs only",
            "only declared registry chains are certified; other compositions remain per-stage",
        ),
    ),
}


def _check(name: str, passed: bool, detail: str = "") -> dict[str, str]:
    return {
        "name": name,
        "status": "pass" if passed else "gap",
        "detail": detail,
    }


def _interval(value: Any) -> dict[str, Any]:
    return {
        "lo": q_to_json(value.lo),
        "hi": q_to_json(value.hi),
        "width": q_to_json(value.width),
    }


def _constant_wire_value(wire: str) -> Fraction | None:
    if not isinstance(wire, str) or not wire.startswith("const:"):
        return None
    try:
        return Fraction(wire[len("const:"):])
    except (ValueError, ZeroDivisionError):
        return None


def _semantic_consumer_slot(operation: str | None, raw_slot: int) -> int:
    """Map a DAG input slot to the operation's declared input port."""
    if operation in {"log", "exp", "reciprocal"}:
        return 0
    return raw_slot


def check_stage_boundary(
    producer_operation: str | None,
    consumer_operation: str | None,
    *,
    consumer_port_index: int = 0,
    wire: str | None = None,
    from_stage: int = 1,
    to_stage: int = 2,
    producer_label: str | None = None,
    consumer_label: str | None = None,
) -> dict[str, Any]:
    """Check one stage boundary against declared domain/interface contracts."""
    producer_interface = STAGE_INTERFACES.get(str(producer_operation))
    consumer_interface = STAGE_INTERFACES.get(str(consumer_operation))
    record: dict[str, Any] = {
        "schema": BOUNDARY_SCHEMA,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "wire": wire,
        "producer": {
            "stage": from_stage,
            "operation": producer_operation,
            "port": None,
            "kind": None,
            "domain": None,
            "representation": None,
        },
        "consumer": {
            "stage": to_stage,
            "operation": consumer_operation,
            "port": None,
            "kind": None,
            "domain": None,
            "accepts": [],
        },
        "checks": {
            "topology": wire is not None,
            "operation_contracts": False,
            "domain_compatible": False,
            "interface_compatible": False,
        },
        "status": "unresolved",
        "validated": False,
        "execution": "not-run",
        "reason": "no declared stage interface for this boundary",
    }
    if producer_interface is None or consumer_interface is None:
        missing = [
            label
            for label, interface in (
                (producer_label or str(producer_operation), producer_interface),
                (consumer_label or str(consumer_operation), consumer_interface),
            )
            if interface is None
        ]
        record["reason"] = (
            "no declared stage interface for "
            + ", ".join(str(item) for item in missing)
        )
        return record

    producer_port = producer_interface.output
    record["producer"] = {
        "stage": from_stage,
        "operation": producer_interface.operation,
        "port": producer_port.name,
        "kind": producer_port.kind,
        "domain": producer_port.domain,
        "representation": producer_port.representation,
    }
    if not 0 <= consumer_port_index < len(consumer_interface.inputs):
        record["reason"] = (
            f"consumer {consumer_interface.operation} has no declared input "
            f"port at slot {consumer_port_index}"
        )
        return record

    consumer_port = consumer_interface.inputs[consumer_port_index]
    record["consumer"] = {
        "stage": to_stage,
        "operation": consumer_interface.operation,
        "port": consumer_port.name,
        "kind": consumer_port.kind,
        "domain": consumer_port.domain,
        "accepts": list(consumer_port.accepts),
    }
    domain_compatible = producer_port.domain == consumer_port.domain
    interface_compatible = producer_port.kind in consumer_port.accepts
    contract_ok = domain_compatible and interface_compatible
    record["checks"].update({
        "operation_contracts": True,
        "domain_compatible": domain_compatible,
        "interface_compatible": interface_compatible,
    })
    record["status"] = "compatible" if contract_ok else "incompatible"
    if contract_ok:
        record["reason"] = (
            "typed stage interface compatible; stage-to-stage target execution "
            "not run"
        )
    elif not domain_compatible:
        record["reason"] = (
            f"domain mismatch: producer {producer_port.domain!r} -> consumer "
            f"{consumer_port.domain!r}"
        )
    else:
        record["reason"] = (
            f"interface mismatch: consumer does not accept {producer_port.kind!r}"
        )
    return record


def stage_boundaries(stages: Any) -> list[dict[str, Any]]:
    """Build typed boundaries for a compiled multi-stage DAG."""
    producers: dict[str, dict[str, Any]] = {}
    boundaries: list[dict[str, Any]] = []
    for position, stage in enumerate(stages, 1):
        index = int(stage.get("index") or position)
        operation = stage.get("operation")
        inputs = tuple(stage.get("inputs") or ())
        for raw_slot, wire in enumerate(inputs):
            source = producers.get(wire)
            if source is None:
                continue
            boundaries.append(
                check_stage_boundary(
                    source.get("operation"),
                    operation,
                    consumer_port_index=(
                        _semantic_consumer_slot(operation, raw_slot)
                        if operation is not None
                        else 0
                    ),
                    wire=wire,
                    from_stage=source["index"],
                    to_stage=index,
                    producer_label=source.get("primitive"),
                    consumer_label=stage.get("primitive"),
                )
            )
        producers[str(stage.get("output"))] = {
            "index": index,
            "operation": operation,
            "primitive": stage.get("primitive"),
        }
    return boundaries


def boundary_summary(boundaries: Any) -> dict[str, int]:
    """Summarize typed boundary counts for payloads and rendering."""
    rows = [row for row in boundaries if isinstance(row, dict)]
    return {
        "boundaries": len(rows),
        "compatible": sum(1 for row in rows if row.get("status") == "compatible"),
        "incompatible": sum(
            1 for row in rows if row.get("status") == "incompatible"
        ),
        "unresolved": sum(1 for row in rows if row.get("status") == "unresolved"),
        "domain_compatible": sum(
            1 for row in rows if (row.get("checks") or {}).get("domain_compatible")
        ),
        "interface_compatible": sum(
            1 for row in rows if (row.get("checks") or {}).get("interface_compatible")
        ),
    }


def match_chain(ops: Any) -> str | None:
    """Return the declared chain id matching this two-primitive DAG shape."""
    if len(ops) != 2:
        return None
    first, second = ops
    for spec in CHAIN_REGISTRY.values():
        if first.op != spec.first_op or second.op != spec.terminal_op:
            continue
        if len(second.inputs) <= spec.terminal_slot:
            continue
        if second.inputs[spec.terminal_slot] != first.output:
            continue
        if spec.constant_slot is not None:
            if len(second.inputs) <= spec.constant_slot:
                continue
            if (
                _constant_wire_value(second.inputs[spec.constant_slot])
                != spec.constant_value
            ):
                continue
        return spec.id
    return None


def validate_chain(chain: str) -> dict[str, Any]:
    """Validate one declared composed chain over its fixed vectors."""
    spec = CHAIN_REGISTRY.get(chain)
    if spec is None:
        raise ValueError(
            f"no composed target validator for chain {chain!r}; "
            f"declared: {', '.join(sorted(CHAIN_REGISTRY))}"
        )
    return _validate_spec(spec)


def _validate_spec(spec: ChainSpec) -> dict[str, Any]:
    boundaries = [
        check_stage_boundary(
            spec.stages[index],
            spec.stages[index + 1],
            consumer_port_index=spec.stage_boundary_slots[index],
            wire=spec.stage_boundary_wires[index],
            from_stage=index + 1,
            to_stage=index + 2,
        )
        for index in range(len(spec.stages) - 1)
    ]
    boundary_checks = boundary_summary(boundaries)
    boundary_ok = (
        boundary_checks["boundaries"] == len(spec.stages) - 1
        and boundary_checks["compatible"] == boundary_checks["boundaries"]
    )
    rows = []
    routes = []
    source_widths = []
    target_widths = []
    for vector in spec.vectors:
        route = spec.source_route(
            precision=vector.precision,
            tolerance=vector.tolerance,
        )
        input_values = {
            name: getattr(vector, name) for name in spec.input_names
        }
        source = route.simulate(**input_values)
        target = spec.target_adapter.function(
            *[input_values[name] for name in spec.input_names],
            precision=vector.precision,
            tolerance=vector.tolerance,
        )
        overlap = (
            max(source.result.lo, target.result.lo)
            <= min(source.result.hi, target.result.hi)
        )
        passed = bool(source.passed and target.passed and overlap)
        rows.append({
            "id": vector.id,
            "inputs": {
                name: q_to_json(value) for name, value in input_values.items()
            },
            "source": {
                "route": source.route_id,
                "operation": source.operation,
                "result": _interval(source.result),
                "checker": _interval(source.checker),
                "passed": source.passed,
            },
            "target": target.as_dict(),
            "overlap": overlap,
            "passed": passed,
        })
        routes.append(route)
        source_widths.append(source.result.width)
        target_widths.append(target.result.width)

    passed_count = sum(1 for row in rows if row["passed"])
    passed = bool(rows) and passed_count == len(rows) and boundary_ok
    try:
        json.dumps(rows)
        serialisable = True
    except (TypeError, ValueError):
        serialisable = False
    checks = [
        _check(
            "composed target adapter",
            callable(spec.target_adapter.function),
            f"{spec.target_adapter.path}:{spec.target_adapter.entrypoint}",
        ),
        _check(
            "fixed vectors",
            passed,
            f"{passed_count}/{len(rows)} fixed vector(s) pass",
        ),
        _check(
            "source target overlap",
            all(row["overlap"] for row in rows),
            f"{sum(1 for row in rows if row['overlap'])}/{len(rows)} overlap",
        ),
        _check(
            "stage interface contracts",
            boundary_ok,
            f"{boundary_checks['compatible']}/{boundary_checks['boundaries']} "
            "typed stage boundary(ies) compatible",
        ),
        _check(
            "boundary domain compatibility",
            boundary_checks["domain_compatible"] == boundary_checks["boundaries"],
            f"{boundary_checks['domain_compatible']}/"
            f"{boundary_checks['boundaries']} domain-compatible",
        ),
        _check(
            "boundary interface compatibility",
            boundary_checks["interface_compatible"] == boundary_checks["boundaries"],
            f"{boundary_checks['interface_compatible']}/"
            f"{boundary_checks['boundaries']} interface-compatible",
        ),
        _check(
            "exact JSON representation",
            serialisable,
            "all fixed-vector values are JSON-safe exact rational strings",
        ),
    ]
    metrics = {
        "vectors": len(rows),
        "passed": passed_count,
        "max_source_width": q_to_json(
            max(source_widths) if source_widths else Fraction(0)
        ),
        "max_target_width": q_to_json(
            max(target_widths) if target_widths else Fraction(0)
        ),
        "boundaries": boundary_checks["boundaries"],
        "compatible_boundaries": boundary_checks["compatible"],
    }
    certificate = {
        "schema": CERTIFICATE_SCHEMA,
        "subject_schema": CHAIN_SCHEMA,
        "chain": spec.id,
        "stages": list(spec.stages),
        "status": "pass" if passed else "fail",
        "evidence_level": "target-simulated",
        "scope": "composed glm-reference software target over fixed vectors",
        "checks": checks,
        "metrics": dict(metrics),
        "gaps": list(spec.gaps),
        "claim": CLAIM,
    }
    return {
        "ok": passed,
        "status": "pass" if passed else "fail",
        "schema": CHAIN_SCHEMA,
        "chain": spec.id,
        "name": spec.name,
        "stages": list(spec.stages),
        "source_route": {
            "id": routes[0].id if routes else spec.id,
            "operation": spec.id,
            "program": routes[0].program.as_dict() if routes else None,
        },
        "target": spec.target_adapter.as_dict(),
        "vectors": rows,
        "boundaries": boundaries,
        "boundary_metrics": boundary_checks,
        "metrics": metrics,
        "checks": checks,
        "gaps": list(spec.gaps),
        "certificate": certificate,
        "claim": CLAIM,
    }


__all__ = [
    "CERTIFICATE_SCHEMA",
    "CHAIN_REGISTRY",
    "BOUNDARY_SCHEMA",
    "CHAIN_SCHEMA",
    "CLAIM",
    "ChainSpec",
    "DIV_MULT_CHAIN",
    "INTERFACE_SCHEMA",
    "MULT_DIV_CHAIN",
    "MULT_RECIPROCAL_CHAIN",
    "STAGE_INTERFACES",
    "StageInterface",
    "boundary_summary",
    "check_stage_boundary",
    "match_chain",
    "stage_boundaries",
    "validate_chain",
]
