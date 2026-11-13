"""Micro-pipeline decomposition for assembled exact routes.

A pipeline is derived from a route's actual ``cent-program/1`` instructions,
not from a prose description.  Each instruction becomes one stage; each named
wire becomes an edge from its producer to its consumer.  A producer that appears
later than its consumer is a feedback handoff.

This is a structural decomposition.  It does not execute a new route or add a
target adapter.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Iterable, Mapping

from . import assembly
from .exact import q_to_json

SCHEMA = "cent-pipeline/1"

ROUTES: dict[str, tuple[str, str]] = {
    "sqrt": ("log-domain-sqrt", "log_domain_sqrt_route"),
    "sum": ("kcl-conservation", "kcl_sum_route"),
    "difference": ("kcl-conservation", "kcl_sum_route"),
    "quantized_carry": ("delta-sigma-error-feedback", "delta_sigma_route"),
}
MECHANISMS: dict[str, tuple[str, ...]] = {
    "sqrt": ("log-domain-sqrt", "sqrt-feedback"),
    "sum": ("kcl-conservation", "fluid-continuity", "opamp-summing"),
    "difference": ("kcl-conservation", "fluid-continuity", "opamp-summing"),
    "quantized_carry": ("delta-sigma-error-feedback",),
}


def _json_value(value: Any) -> Any:
    if isinstance(value, Fraction):
        return q_to_json(value)
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _route(operation: str, mechanism: str | None):
    if operation not in ROUTES:
        raise ValueError(
            f"unknown pipeline operation: {operation!r}; "
            f"choose from {', '.join(sorted(ROUTES))}"
        )
    allowed = MECHANISMS[operation]
    selected = mechanism or allowed[0]
    if selected not in allowed:
        raise ValueError(
            f"mechanism {selected!r} does not declare {operation!r}; "
            f"choose from {', '.join(allowed)}"
        )
    if operation == "sqrt":
        if selected == "sqrt-feedback":
            return assembly.opamp_multiplier_sqrt_route(), selected
        return assembly.log_domain_sqrt_route(), selected
    if operation == "difference":
        if selected == "fluid-continuity":
            return assembly.fluid_sum_route(operation="difference"), selected
        if selected == "opamp-summing":
            return assembly.opamp_sum_route(operation="difference"), selected
        return assembly.kcl_sum_route(operation="difference"), selected
    if selected == "fluid-continuity":
        return assembly.fluid_sum_route(), selected
    if selected == "opamp-summing":
        return assembly.opamp_sum_route(), selected
    if operation == "sum":
        return assembly.kcl_sum_route(operation="sum"), selected
    return assembly.delta_sigma_route(), selected


_GLUE_LAWS = {
    "neg": "out = -input (exact program negation)",
    "sum": "out = sum of declared inputs (exact program addition)",
    "sat": "out = input clamped to the declared saturation bounds",
}


def build_pipeline(operation: str, mechanism: str | None = None) -> dict[str, Any]:
    """Build a stage/handoff view from a declared route's exact program."""
    route, selected = _route(operation, mechanism)
    program = getattr(route, "program", None)
    if program is None:
        return {
            "ok": False,
            "schema": SCHEMA,
            "operation": operation,
            "mechanism": selected,
            "route": route.id,
            "route_name": route.name,
            "inputs": {},
            "outputs": {},
            "stages": [],
            "handoffs": [],
            "unresolved": [],
            "summary": {
                "stages": 0,
                "handoffs": 0,
                "feedback_handoffs": 0,
                "route_inputs": 0,
                "route_outputs": 0,
                "operations": [],
            },
            "checks": [
                {
                    "name": "route program",
                    "status": "gap",
                    "detail": (
                        f"{route.id} is a declared algebraic route, not a "
                        "cent-program/1 pipeline"
                    ),
                }
            ],
            "passed": False,
            "gaps": [
                *list(route.gaps),
                "the selected route has no exact instruction program; "
                "stage decomposition is not available",
            ],
            "claim": (
                "No pipeline was inferred for a route without a declared "
                "cent-program/1 instruction list."
            ),
        }
    component_by_op = {}
    for component in route.components:
        component_by_op.setdefault(component.op, component)
    anchor = route.components[0].contract if route.components else None

    stages: list[dict[str, Any]] = []
    producers: dict[str, int] = {}
    for index, instruction in enumerate(program.instructions, start=1):
        component = component_by_op.get(instruction.op)
        if component is not None:
            contract = component.contract
            role = component.role
            law = contract.law
            domain = contract.domain
            carrier = contract.carrier
            material = contract.material
            source = contract.source
            failure_modes = list(contract.failure_modes)
        else:
            role = "exact-core"
            law = _GLUE_LAWS.get(instruction.op)
            if law is None:
                raise ValueError(
                    f"no typed route contract or declared glue law for {instruction.op!r}"
                )
            domain = anchor.domain if anchor is not None else "exact program"
            carrier = anchor.carrier if anchor is not None else "named wires"
            material = "exact program glue"
            source = "cent-program/1 instruction"
            failure_modes = []
        stages.append({
            "index": index,
            "role": role,
            "op": instruction.op,
            "inputs": list(instruction.inputs),
            "output": instruction.out,
            "parameters": _json_value(dict(instruction.params)),
            "law": law,
            "domain": domain,
            "carrier": carrier,
            "material": material,
            "source": source,
            "failure_modes": failure_modes,
        })
        producers[instruction.out] = index

    handoffs: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for stage in stages:
        for wire in stage["inputs"]:
            if wire in producers:
                source = producers[wire]
                handoffs.append({
                    "from_stage": source,
                    "to_stage": stage["index"],
                    "wire": wire,
                    "kind": "feedback" if source >= stage["index"] else "stage",
                })
            elif wire in program.inputs:
                handoffs.append({
                    "from_stage": 0,
                    "to_stage": stage["index"],
                    "wire": wire,
                    "kind": "route-input",
                })
            else:
                unresolved.append({
                    "stage": stage["index"],
                    "wire": wire,
                    "reason": "wire has no producer and is not a route input",
                })

    feedback = [item for item in handoffs if item["kind"] == "feedback"]
    checks = [
        {
            "name": "route program",
            "status": "pass" if stages else "gap",
            "detail": f"{len(stages)} exact instruction(s) from {route.id}",
        },
        {
            "name": "stage handoffs",
            "status": "pass" if not unresolved else "gap",
            "detail": (
                f"{len(handoffs)} handoff(s), {len(feedback)} feedback edge(s)"
                if not unresolved
                else f"{len(unresolved)} unresolved wire(s)"
            ),
        },
        {
            "name": "stage order",
            "status": "pass" if all(
                item["from_stage"] == 0 or item["from_stage"] < item["to_stage"]
                for item in handoffs if item["kind"] == "stage"
            ) else "gap",
            "detail": "every non-feedback handoff points to an earlier stage",
        },
    ]
    gaps = list(route.gaps)
    gaps.extend(
        f"unresolved stage input {item['stage']}:{item['wire']}" for item in unresolved
    )
    gaps.append("structural decomposition only; no target adapter or physical validation is implied")
    return {
        "ok": True,
        "schema": SCHEMA,
        "operation": operation,
        "mechanism": selected,
        "route": route.id,
        "route_name": route.name,
        "inputs": dict(program.inputs),
        "outputs": dict(program.outputs),
        "stages": stages,
        "handoffs": handoffs,
        "unresolved": unresolved,
        "summary": {
            "stages": len(stages),
            "handoffs": len(handoffs),
            "feedback_handoffs": len(feedback),
            "route_inputs": len(program.inputs),
            "route_outputs": len(program.outputs),
            "operations": [stage["op"] for stage in stages],
        },
        "checks": checks,
        "passed": all(check["status"] == "pass" for check in checks),
        "gaps": list(dict.fromkeys(gaps)),
        "claim": (
            "Micro-pipeline derived from a declared exact route program; "
            "stage boundaries and handoffs are structural, not a new validation."
        ),
    }


def render_text(payload: Mapping[str, Any]) -> str:
    """Render a pipeline for the terminal."""
    lines = [
        "=" * 78,
        "MICRO-PIPELINE",
        "=" * 78,
        f"operation    {payload['operation']}",
        f"mechanism    {payload['mechanism']}",
        f"route        {payload['route']}",
        f"stages       {payload['summary']['stages']}",
        f"handoffs     {payload['summary']['handoffs']} "
        f"({payload['summary']['feedback_handoffs']} feedback)",
        "",
        "Stages",
    ]
    for stage in payload["stages"]:
        inputs = ", ".join(stage["inputs"]) or "—"
        lines.append(
            f"  {stage['index']:>2}. {stage['op']:<9} "
            f"{inputs} -> {stage['output']}"
        )
        lines.append(f"      law: {stage['law']}")
    lines.append("")
    lines.append("Handoffs")
    for handoff in payload["handoffs"]:
        lines.append(
            f"  {handoff['from_stage']:>2} -> {handoff['to_stage']:<2} "
            f"{handoff['wire']:<12} [{handoff['kind']}]"
        )
    lines.append("")
    lines.append("Gaps")
    for gap in payload["gaps"]:
        lines.append(f"  - {gap}")
    return "\n".join(lines)


__all__ = ["SCHEMA", "ROUTES", "MECHANISMS", "build_pipeline", "render_text"]
