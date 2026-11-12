"""Typed ¢ graphs and component/port lowerings for assembled routes.

A typed graph is a view over an existing exact route, not a second simulator.
Each node preserves the route's primitive instruction, wire bindings and
parameters.  Physical nodes lower to their existing :class:`ComponentContract`;
arithmetic/control glue lowers to the exact core with no physical-device claim.
The feedback route has no program, so its graph is derived from its declared
multiplier/amplifier components plus the residual arithmetic.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping

from .exact import q_to_json
from .vocabulary import CONTRACTS

SCHEMA = "cent-typed-graph/1"

_GLUE_OPS = frozenset({"neg", "sum", "sat"})
_GLUE_LAWS = {
    "neg": "exact negation of a rational or certified interval",
    "sum": "exact addition of rationals or certified intervals",
    "sat": "clamp(x, lo, hi) with declared exact rails",
}


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "component"


def _json(value: Any) -> Any:
    if isinstance(value, Fraction):
        return q_to_json(value)
    if isinstance(value, Mapping):
        return {str(key): _json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json(item) for item in value]
    return value


@dataclass(frozen=True)
class GraphPort:
    """A route-level typed port and the wire it exposes."""

    name: str
    direction: str
    kind: str
    domain: str
    wire: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "direction": self.direction,
            "kind": self.kind,
            "domain": self.domain,
            "wire": self.wire,
        }


@dataclass(frozen=True)
class GraphBinding:
    """One node port bound to a named wire."""

    port: str
    wire: str
    kind: str
    domain: str

    def as_dict(self) -> dict[str, str]:
        return {
            "port": self.port,
            "wire": self.wire,
            "kind": self.kind,
            "domain": self.domain,
        }


@dataclass(frozen=True)
class GraphNode:
    """One primitive node with explicit input/output bindings and a lowering."""

    id: str
    op: str
    inputs: tuple[GraphBinding, ...]
    outputs: tuple[GraphBinding, ...]
    parameters: Mapping[str, Any]
    role: str | None
    lowering: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "op": self.op,
            "inputs": [item.as_dict() for item in self.inputs],
            "outputs": [item.as_dict() for item in self.outputs],
            "parameters": _json(dict(self.parameters)),
            "role": self.role,
            "lowering": _json(dict(self.lowering)),
        }


@dataclass(frozen=True)
class TypedGraph:
    """A graph, its route ports, edges and lowering summary."""

    route_id: str
    name: str
    nodes: tuple[GraphNode, ...]
    ports: tuple[GraphPort, ...]
    edges: tuple[Mapping[str, Any], ...]
    feedback_edges: tuple[Mapping[str, Any], ...]
    loop: str
    gaps: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        component_nodes = sum(
            1 for node in self.nodes if node.lowering.get("kind") == "component"
        )
        exact_nodes = sum(
            1 for node in self.nodes if node.lowering.get("kind") == "exact-core"
        )
        return {
            "schema": SCHEMA,
            "route": self.route_id,
            "name": self.name,
            "nodes": [node.as_dict() for node in self.nodes],
            "ports": [port.as_dict() for port in self.ports],
            "edges": [_json(edge) for edge in self.edges],
            "feedback_edges": [_json(edge) for edge in self.feedback_edges],
            "summary": {
                "node_count": len(self.nodes),
                "component_nodes": component_nodes,
                "exact_core_nodes": exact_nodes,
                "port_count": len(self.ports),
                "feedback_edges": len(self.feedback_edges),
                "loop": self.loop,
            },
            "gaps": list(self.gaps),
        }

    def render_text(self) -> str:
        lines = [
            "=" * 78,
            "TYPED ¢ GRAPH",
            "=" * 78,
            f"Route: {self.name}",
            f"Loop: {self.loop}",
            "",
            "Nodes",
        ]
        for node in self.nodes:
            kind = node.lowering.get("kind", "unknown")
            role = f" role={node.role}" if node.role else ""
            lines.append(f"  {node.id:<3} ¢_{node.op:<9} [{kind}]{role}")
            lines.append(
                "       in:  "
                + ", ".join(f"{item.port}={item.wire}" for item in node.inputs)
            )
            lines.append(
                "       out: "
                + ", ".join(f"{item.port}={item.wire}" for item in node.outputs)
            )
            contract = node.lowering.get("component_key")
            if contract:
                lines.append(f"       component: {contract}")
        lines.append("")
        lines.append("Route ports")
        for port in self.ports:
            lines.append(
                f"  {port.direction:<6} {port.name:<8} {port.kind:<18} "
                f"wire={port.wire or 'unbound'}"
            )
        lines.append("")
        lines.append("Feedback edges")
        if self.feedback_edges:
            for edge in self.feedback_edges:
                lines.append(
                    f"  {edge.get('from')} -> {edge.get('to')} "
                    f"on {edge.get('wire')}"
                )
        else:
            lines.append("  none")
        lines.append("")
        lines.append("Declared graph gaps")
        for gap in self.gaps:
            lines.append(f"  - {gap}")
        return "\n".join(lines)


def _glue_bindings(
    op: str, inputs: tuple[str, ...], out: str
) -> tuple[tuple[GraphBinding, ...], tuple[GraphBinding, ...]]:
    if op == "sum":
        names = tuple(f"x{index}" for index in range(1, len(inputs) + 1))
        output_name = "sum"
    elif op == "neg":
        names = ("x",)
        output_name = "y"
    elif op == "sat":
        names = ("x",)
        output_name = "y"
    else:
        names = tuple(f"x{index}" for index in range(1, len(inputs) + 1))
        output_name = "y"
    in_bindings = tuple(
        GraphBinding(name, wire, "numeric or interval", "exact core")
        for name, wire in zip(names, inputs)
    )
    return in_bindings, (
        GraphBinding(output_name, out, "numeric or interval", "exact core"),
    )


def _exact_lowering(
    op: str,
    inputs: tuple[GraphBinding, ...],
    outputs: tuple[GraphBinding, ...],
) -> dict[str, Any]:
    law = _GLUE_LAWS.get(op)
    if law is None:
        contract = CONTRACTS.get(op)
        law = (
            contract.notes
            if contract is not None and contract.notes
            else "exact-core primitive; no physical component is claimed"
        )
    return {
        "kind": "exact-core",
        "component_key": None,
        "contract": None,
        "operation": op,
        "law": law,
        "port_map": [
            {
                "contract_port": item.port,
                "direction": "input",
                "wire": item.wire,
                "kind": item.kind,
            }
            for item in inputs
        ]
        + [
            {
                "contract_port": item.port,
                "direction": "output",
                "wire": item.wire,
                "kind": item.kind,
            }
            for item in outputs
        ],
        "gaps": ["exact-core glue; no physical material is claimed"],
    }


def _component_lowering(
    component: Any,
    inputs: tuple[GraphBinding, ...],
    outputs: tuple[GraphBinding, ...],
) -> tuple[dict[str, Any], tuple[GraphBinding, ...], tuple[GraphBinding, ...]]:
    inputs = tuple(inputs)
    outputs = tuple(outputs)
    contract = component.contract
    contract_inputs = tuple(
        port for port in contract.ports if port.direction == "input"
    )
    contract_outputs = tuple(
        port for port in contract.ports if port.direction == "output"
    )
    lowered_inputs = tuple(
        GraphBinding(port.name, binding.wire, port.kind, port.domain)
        for port, binding in zip(contract_inputs, inputs)
    )
    lowered_outputs = tuple(
        GraphBinding(port.name, binding.wire, port.kind, port.domain)
        for port, binding in zip(contract_outputs, outputs)
    )
    gaps: list[str] = []
    if len(contract_inputs) != len(inputs) or len(contract_outputs) != len(outputs):
        gaps.append(
            f"component {component.role} port arity does not match its typed contract"
        )
    component_outputs = tuple(str(item) for item in component.outputs)
    for binding, declared in zip(lowered_outputs, component_outputs):
        if binding.wire != declared:
            gaps.append(
                f"component {component.role} declares output {declared!r} but the "
                f"graph binds contract port {binding.port!r} to {binding.wire!r}"
            )
    port_map = [
        {
            "contract_port": port.name,
            "direction": port.direction,
            "wire": binding.wire,
            "kind": port.kind,
            "domain": port.domain,
            "component_wire": declared,
        }
        for port, binding, declared in zip(
            contract_inputs,
            lowered_inputs,
            tuple(str(item) for item in component.inputs),
        )
    ] + [
        {
            "contract_port": port.name,
            "direction": port.direction,
            "wire": binding.wire,
            "kind": port.kind,
            "domain": port.domain,
            "component_wire": declared,
        }
        for port, binding, declared in zip(
            contract_outputs, lowered_outputs, component_outputs
        )
    ]
    lowering = {
        "kind": "component",
        "component_key": f"component:{contract.op}:{_slug(contract.domain)}",
        "contract": contract.as_dict(),
        "component": component.contract.material,
        "component_role": component.role,
        "port_map": port_map,
        "gaps": gaps,
    }
    return lowering, lowered_inputs, lowered_outputs


def _component_for(
    components_by_op: dict[str, list[Any]], op: str
) -> Any | None:
    candidates = components_by_op.get(op)
    if not candidates:
        return None
    return candidates.pop(0)


def _graph_port_wire(route: Any, port: Any, program: Any) -> str | None:
    if port.direction == "input":
        return port.name if port.name in program.inputs else None
    return program.outputs.get(port.name, port.name)


def _program_graph(route: Any) -> TypedGraph:
    program = route.program
    components_by_op: dict[str, list[Any]] = {}
    for component in route.components:
        components_by_op.setdefault(component.op, []).append(component)

    nodes: list[GraphNode] = []
    producer: dict[str, str] = {}
    node_index: dict[str, int] = {}
    lowering_gaps: list[str] = []
    for index, instruction in enumerate(program.instructions, start=1):
        node_id = f"n{index}"
        component = _component_for(components_by_op, instruction.op)
        if component is not None:
            lowering, inputs, outputs = _component_lowering(
                component,
                tuple(
                    GraphBinding(f"x{position}", wire, "numeric", "exact rational")
                    for position, wire in enumerate(instruction.inputs, start=1)
                ),
                tuple(
                    GraphBinding(
                        f"y{position}", wire, "numeric", "exact rational"
                    )
                    for position, wire in enumerate((instruction.out,), start=1)
                ),
            )
        else:
            component = None
            inputs, outputs = _glue_bindings(
                instruction.op, instruction.inputs, instruction.out
            )
            lowering = _exact_lowering(instruction.op, inputs, outputs)
        lowering_gaps.extend(
            f"{node_id}: {gap}" for gap in lowering.get("gaps", ())
        )
        node = GraphNode(
            id=node_id,
            op=instruction.op,
            inputs=inputs,
            outputs=outputs,
            parameters=instruction.params,
            role=component.role if component is not None else None,
            lowering=lowering,
        )
        nodes.append(node)
        producer[instruction.out] = node_id
        node_index[node_id] = index

    edges: list[dict[str, Any]] = []
    for node in nodes:
        for binding in node.inputs:
            source = producer.get(binding.wire)
            if source is None and binding.wire in program.inputs:
                source = f"input:{binding.wire}"
            if source is None:
                lowering_gaps.append(
                    f"{node.id}: input wire {binding.wire!r} has no producer"
                )
                continue
            feedback = (
                source in node_index and node_index[source] > node_index[node.id]
            )
            edges.append(
                {
                    "from": source,
                    "to": node.id,
                    "wire": binding.wire,
                    "feedback": feedback,
                }
            )
    ports = tuple(
        GraphPort(
            port.name,
            port.direction,
            port.kind,
            port.domain,
            _graph_port_wire(route, port, program),
        )
        for port in route.ports
    )
    for port in ports:
        if port.direction != "output" or port.wire is None:
            continue
        source = producer.get(port.wire)
        if source is not None:
            edges.append(
                {
                    "from": source,
                    "to": f"output:{port.name}",
                    "wire": port.wire,
                    "feedback": False,
                }
            )
    feedback_edges = tuple(edge for edge in edges if edge["feedback"])
    return TypedGraph(
        route_id=route.id,
        name=route.name,
        nodes=tuple(nodes),
        ports=ports,
        edges=tuple(edges),
        feedback_edges=feedback_edges,
        loop="stateful" if feedback_edges else "none",
        gaps=tuple(dict.fromkeys(list(route.gaps) + lowering_gaps)),
    )


def _feedback_graph(route: Any) -> TypedGraph:
    components = {component.op: component for component in route.components}
    amp = components.get("amp")
    mult = components.get("mult")
    if amp is None or mult is None:
        return _component_graph(
            route,
            "feedback route lacks its declared amp/multiplier components",
        )

    negative_inputs, negative_outputs = _glue_bindings(
        "neg", ("square",), "neg_square"
    )
    negative = GraphNode(
        "n1",
        "neg",
        negative_inputs,
        negative_outputs,
        {},
        None,
        _exact_lowering("neg", negative_inputs, negative_outputs),
    )
    sum_inputs = (
        GraphBinding("x1", "x", "numeric or interval", "exact core"),
        GraphBinding("x2", "neg_square", "numeric or interval", "exact core"),
    )
    sum_outputs = (
        GraphBinding("sum", "error", "numeric or interval", "exact core"),
    )
    residual = GraphNode(
        "n2",
        "sum",
        sum_inputs,
        sum_outputs,
        {},
        None,
        _exact_lowering("sum", sum_inputs, sum_outputs),
    )
    amp_lowering, amp_inputs, amp_outputs = _component_lowering(
        amp,
        (GraphBinding("error", "error", "numeric", "exact rational"),),
        (GraphBinding("drive", "drive", "numeric", "exact rational"),),
    )
    amp_node = GraphNode(
        "n3",
        "amp",
        amp_inputs,
        amp_outputs,
        amp.parameters,
        amp.role,
        amp_lowering,
    )
    mult_lowering, mult_inputs, mult_outputs = _component_lowering(
        mult,
        (
            GraphBinding("a", "drive", "numeric", "exact rational"),
            GraphBinding("b", "drive", "numeric", "exact rational"),
        ),
        (GraphBinding("product", "square", "numeric", "exact rational"),),
    )
    mult_node = GraphNode(
        "n4",
        "mult",
        mult_inputs,
        mult_outputs,
        mult.parameters,
        mult.role,
        mult_lowering,
    )
    nodes = (negative, residual, amp_node, mult_node)
    edges = (
        {"from": "input:x", "to": "n2", "wire": "x", "feedback": False},
        {"from": "n1", "to": "n2", "wire": "neg_square", "feedback": False},
        {"from": "n2", "to": "n3", "wire": "error", "feedback": False},
        {"from": "n3", "to": "n4", "wire": "drive", "feedback": False},
        {"from": "n3", "to": "n4", "wire": "drive", "feedback": False},
        {"from": "n4", "to": "n1", "wire": "square", "feedback": True},
        {"from": "n3", "to": "output:root", "wire": "drive", "feedback": False},
    )
    feedback_edges = tuple(edge for edge in edges if edge["feedback"])
    ports = (
        GraphPort("x", "input", "numeric", "x > 0", "x"),
        GraphPort(
            "root",
            "output",
            "interval",
            "certified enclosure of the finite-gain equilibrium",
            "drive",
        ),
    )
    gaps = list(route.gaps)
    gaps.append(
        "the feedback graph is an algebraic loop; it is not a stateful sampled-data graph"
    )
    for node in nodes:
        gaps.extend(
            f"{node.id}: {gap}" for gap in node.lowering.get("gaps", ())
        )
    return TypedGraph(
        route_id=route.id,
        name=route.name,
        nodes=nodes,
        ports=ports,
        edges=edges,
        feedback_edges=feedback_edges,
        loop="algebraic",
        gaps=tuple(dict.fromkeys(gaps)),
    )


def _component_graph(route: Any, reason: str) -> TypedGraph:
    nodes = tuple(
        GraphNode(
            f"n{index}",
            component.op,
            tuple(
                GraphBinding(f"x{position}", wire, "numeric", "exact rational")
                for position, wire in enumerate(component.inputs, start=1)
            ),
            tuple(
                GraphBinding(f"y{position}", wire, "numeric", "exact rational")
                for position, wire in enumerate(component.outputs, start=1)
            ),
            component.parameters,
            component.role,
            _component_lowering(
                component,
                tuple(
                    GraphBinding(f"x{position}", wire, "numeric", "exact rational")
                    for position, wire in enumerate(component.inputs, start=1)
                ),
                tuple(
                    GraphBinding(f"y{position}", wire, "numeric", "exact rational")
                    for position, wire in enumerate(component.outputs, start=1)
                ),
            )[0],
        )
        for index, component in enumerate(route.components, start=1)
    )
    ports = tuple(
        GraphPort(port.name, port.direction, port.kind, port.domain, port.name)
        for port in route.ports
    )
    return TypedGraph(
        route_id=route.id,
        name=route.name,
        nodes=nodes,
        ports=ports,
        edges=(),
        feedback_edges=(),
        loop="none",
        gaps=tuple(dict.fromkeys(list(route.gaps) + [reason])),
    )


def typed_graph(route: Any) -> TypedGraph:
    """Build the typed graph view for one assembled route.

    The graph is derived from the exact program when present, otherwise from
    the declared components.  It does not add a simulation or a physical claim.
    """
    if getattr(route, "program", None) is not None:
        return _program_graph(route)
    if getattr(route, "id", "") == "sqrt-opamp-multiplier":
        return _feedback_graph(route)
    return _component_graph(
        route,
        "route has no exact-core program; component-level graph only",
    )


__all__ = [
    "SCHEMA",
    "GraphBinding",
    "GraphNode",
    "GraphPort",
    "TypedGraph",
    "typed_graph",
]
