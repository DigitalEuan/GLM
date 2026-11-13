"""Topology-derived reference netlists and schematic floorplans.

This is deliberately not a fabrication flow.  It takes a *selected* design from
:mod:`cent_compiler.design`, maps the exact device quantities onto a declared
reference topology, emits a SPICE-shaped deck and lays out the route's stages on
a declared schematic grid.  The exact rational values remain in the JSON; SPICE
fields are decimal representations because SPICE has no exact rational literal.

The output therefore adds two concrete artifacts while keeping the remaining
physical claims visible as gaps: a reference netlist and a stage floorplan, not
a package, footprint, PCB, DRC-clean layout or measured device.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations
from typing import Any, Mapping

from . import assembly
from .design import DesignResult, solve_route
from .device import DeviceBinding
from .exact import CentError, ErrorCode, Q, q_to_json

SCHEMA = "cent-physical/1"
LAYOUT_SCHEMA = "cent-floorplan/1"
IDEAL_OPAMP_GAIN = Fraction(1_000_000)


def _json(value: Any) -> Any:
    if isinstance(value, Fraction):
        return q_to_json(value)
    if isinstance(value, Mapping):
        return {str(key): _json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json(item) for item in value]
    return value


def _decimal(value: Q, places: int = 15) -> str:
    """Render a rational as a deterministic decimal using integer arithmetic."""
    sign = "-" if value < 0 else ""
    value = abs(value)
    scale = 10 ** places
    scaled = value.numerator * scale // value.denominator
    whole, fraction = divmod(scaled, scale)
    fraction_text = f"{fraction:0{places}d}".rstrip("0")
    return sign + str(whole) + (f".{fraction_text}" if fraction_text else "")


def _quantity(binding: DeviceBinding, symbol: str) -> Q:
    """Fetch one exact scalar quantity from a binding."""
    for item in binding.quantities:
        if item.symbol == symbol:
            if not isinstance(item.value, Fraction):
                raise CentError(
                    ErrorCode.UNSUPPORTED,
                    f"quantity {symbol} is not a scalar and cannot be emitted as a part value",
                )
            return item.value
    raise CentError(
        ErrorCode.UNSUPPORTED,
        f"binding does not declare quantity {symbol!r}",
    )


@dataclass(frozen=True)
class PhysicalPart:
    """One emitted reference component or ideal behavioral block."""

    ref: str
    kind: str
    nodes: tuple[str, ...]
    role: str
    value: Q | None = None
    unit: str = ""
    expression: str | None = None
    parameters: Mapping[str, Any] = field(default_factory=dict)
    note: str = ""

    @property
    def spice_value(self) -> str | None:
        return None if self.value is None else _decimal(self.value)

    def spice_line(self) -> str:
        if not self.ref or not self.ref[0].isalpha():
            raise CentError(ErrorCode.INVALID_INPUT, f"invalid SPICE reference {self.ref!r}")
        if self.kind == "voltage-source" and len(self.nodes) == 2 and self.value is not None:
            return f"{self.ref} {self.nodes[0]} {self.nodes[1]} DC {self.spice_value}"
        if self.kind in ("resistor", "capacitor") and len(self.nodes) == 2 and self.value is not None:
            return f"{self.ref} {self.nodes[0]} {self.nodes[1]} {self.spice_value}"
        if self.kind == "vcvs" and len(self.nodes) == 4 and self.value is not None:
            return (
                f"{self.ref} {self.nodes[0]} {self.nodes[1]} "
                f"{self.nodes[2]} {self.nodes[3]} {self.spice_value}"
            )
        if self.kind == "behavioral-voltage" and len(self.nodes) == 2 and self.expression:
            return f"{self.ref} {self.nodes[0]} {self.nodes[1]} V={self.expression}"
        if self.kind == "behavioral-current" and len(self.nodes) == 2 and self.expression:
            return f"{self.ref} {self.nodes[0]} {self.nodes[1]} I={self.expression}"
        raise CentError(
            ErrorCode.UNSUPPORTED,
            f"cannot emit part {self.ref!r} ({self.kind})",
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "ref": self.ref,
            "kind": self.kind,
            "role": self.role,
            "nodes": list(self.nodes),
            "value": q_to_json(self.value) if self.value is not None else None,
            "value_text": self.spice_value,
            "unit": self.unit,
            "expression": self.expression,
            "parameters": _json(dict(self.parameters)),
            "note": self.note,
            "spice_line": self.spice_line(),
        }


@dataclass(frozen=True)
class PhysicalNet:
    """A net with explicit component-pin connections."""

    name: str
    kind: str
    connections: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "connections": list(self.connections),
        }


@dataclass(frozen=True)
class LayoutBlock:
    """A stage rectangle in declared schematic grid units."""

    stage: str
    role: str
    x: int
    y: int
    width: int
    height: int
    parts: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "role": self.role,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "parts": list(self.parts),
        }


@dataclass(frozen=True)
class LayoutLink:
    """One signal link between schematic stages."""

    net: str
    from_stage: str
    to_stage: str

    def as_dict(self) -> dict[str, str]:
        return {
            "net": self.net,
            "from": self.from_stage,
            "to": self.to_stage,
        }


@dataclass(frozen=True)
class LayoutPlan:
    """A coarse schematic floorplan, not physical PCB geometry."""

    coordinate_unit: str
    canvas_width: int
    canvas_height: int
    blocks: tuple[LayoutBlock, ...]
    links: tuple[LayoutLink, ...]
    gaps: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": LAYOUT_SCHEMA,
            "coordinate_unit": self.coordinate_unit,
            "canvas": {
                "width": self.canvas_width,
                "height": self.canvas_height,
                "unit": self.coordinate_unit,
            },
            "blocks": [block.as_dict() for block in self.blocks],
            "links": [link.as_dict() for link in self.links],
            "gaps": list(self.gaps),
        }

    def render_text(self) -> str:
        lines = [
            "Schematic floorplan (declared grid units, not millimetres)",
            f"  canvas {self.canvas_width} x {self.canvas_height}",
        ]
        for block in self.blocks:
            lines.append(
                f"  {block.stage:<14} x={block.x:<4} y={block.y:<4} "
                f"{block.width}x{block.height}  parts={', '.join(block.parts) or '(none)'}"
            )
        for link in self.links:
            lines.append(
                f"  link {link.net}: {link.from_stage} -> {link.to_stage}"
            )
        return "\n".join(lines)


@dataclass(frozen=True)
class PhysicalCheck:
    """One status row for the emitted reference artifacts."""

    name: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class PhysicalPlan:
    """A reference netlist, net graph and floorplan for one selected design."""

    design: DesignResult
    route_key: str
    route_id: str
    route_name: str
    topology: str
    source_roles: tuple[str, ...]
    parts: tuple[PhysicalPart, ...]
    nets: tuple[PhysicalNet, ...]
    spice: str
    layout: LayoutPlan
    checks: tuple[PhysicalCheck, ...]
    gaps: tuple[str, ...]

    @property
    def selected(self):
        return self.design.selected

    def as_dict(self) -> dict[str, Any]:
        selected = self.design.selected
        assert selected is not None
        return {
            "schema": SCHEMA,
            "status": "reference topology; not fabrication-ready",
            "route": self.route_id,
            "route_key": self.route_key,
            "route_name": self.route_name,
            "topology": self.topology,
            "source_roles": list(self.source_roles),
            "selected": {
                "option": selected.option.name,
                "parameters": _json(dict(selected.option.parameters)),
                "cost": q_to_json(selected.option.cost),
                "input": q_to_json(selected.binding.input_value)
                if selected.binding is not None
                else None,
                "max_relative_error": q_to_json(selected.max_error)
                if selected.max_error is not None
                else None,
            },
            "constraints": self.design.constraints.as_dict(),
            "parts": [part.as_dict() for part in self.parts],
            "nets": [net.as_dict() for net in self.nets],
            "spice": self.spice,
            "layout": self.layout.as_dict(),
            "checks": [check.as_dict() for check in self.checks],
            "gaps": list(self.gaps),
        }

    def render_text(self) -> str:
        selected = self.design.selected
        assert selected is not None
        lines = [
            "=" * 78,
            "REFERENCE NETLIST AND FLOORPLAN",
            "=" * 78,
            f"Route: {self.route_name} ({self.route_key})",
            f"Status: reference topology; not fabrication-ready",
            f"Selected: {selected.option.name} (cost {selected.option.cost})",
            f"Topology: {self.topology}",
            "",
            "Parts",
        ]
        for part in self.parts:
            value = part.expression or part.spice_value or "-"
            lines.append(
                f"  {part.ref:<6} {part.role:<13} {part.kind:<20} "
                f"{value:>24} {part.unit:<7} {'/'.join(part.nodes)}"
            )
            if part.note:
                lines.append(f"         {part.note}")
        lines.extend(("", "Nets"))
        for net in self.nets:
            lines.append(
                f"  {net.name:<12} {net.kind:<8} {', '.join(net.connections)}"
            )
        lines.extend(("", "Reference SPICE deck", self.spice.rstrip()))
        lines.extend(("", self.layout.render_text()))
        lines.extend(("", "Checks"))
        for check in self.checks:
            lines.append(f"  [{check.status:<4}] {check.name}: {check.detail}")
        lines.extend(("", "Remaining gaps"))
        for gap in self.gaps:
            lines.append(f"  - {gap}")
        return "\n".join(lines)


def _build_nets(parts: tuple[PhysicalPart, ...]) -> tuple[PhysicalNet, ...]:
    connections: dict[str, list[str]] = {}
    for part in parts:
        for index, node in enumerate(part.nodes, start=1):
            connections.setdefault(node, []).append(f"{part.ref}.{index}")
    nets: list[PhysicalNet] = []
    for name in sorted(connections, key=lambda item: (item != "0", item)):
        kind = "ground" if name == "0" else "digital" if name == "level" else "analog"
        nets.append(PhysicalNet(name, kind, tuple(connections[name])))
    return tuple(nets)


def _build_layout(
    stage_order: tuple[str, ...],
    parts: tuple[PhysicalPart, ...],
    nets: tuple[PhysicalNet, ...],
) -> LayoutPlan:
    blocks: list[LayoutBlock] = []
    for index, stage in enumerate(stage_order):
        assigned = tuple(
            sorted(part.ref for part in parts if part.role == stage)
        )
        blocks.append(
            LayoutBlock(
                stage=stage,
                role=stage,
                x=20 + index * 180,
                y=20,
                width=160,
                height=80,
                parts=assigned,
            )
        )
    links: list[LayoutLink] = []
    seen: set[tuple[str, str, str]] = set()
    for net in nets:
        if net.name == "0":
            continue
        stages: list[str] = []
        for part in parts:
            if net.name not in part.nodes:
                continue
            if part.role not in stages:
                stages.append(part.role)
        for left, right in zip(stages, stages[1:]):
            key = (net.name, left, right)
            if left != right and key not in seen:
                seen.add(key)
                links.append(LayoutLink(net.name, left, right))
    gaps = (
        "Coordinates are declared schematic grid units, not millimetres or PCB dimensions.",
        "No footprints, package parasitics, keep-outs, DRC or thermal placement are modeled.",
        "The floorplan is a stage-level intent only; it is not a placed or routed board.",
    )
    return LayoutPlan(
        coordinate_unit="declared schematic grid unit; not mm",
        canvas_width=40 + len(stage_order) * 180,
        canvas_height=120,
        blocks=tuple(blocks),
        links=tuple(links),
        gaps=gaps,
    )


def _check(
    parts: tuple[PhysicalPart, ...],
    stage_order: tuple[str, ...],
    layout: LayoutPlan,
    spice: str,
    source_roles: tuple[str, ...],
) -> tuple[PhysicalCheck, ...]:
    refs = [part.ref for part in parts]
    duplicate_refs = len(refs) != len(set(refs))
    missing_nodes = [part.ref for part in parts if not part.nodes]
    missing_role = [part.ref for part in parts if part.role not in stage_order]
    assigned = {ref for block in layout.blocks for ref in block.parts}
    unassigned = sorted(set(refs) - assigned)
    overlaps = []
    for left, right in combinations(layout.blocks, 2):
        if (
            left.x < right.x + right.width
            and right.x < left.x + left.width
            and left.y < right.y + right.height
            and right.y < left.y + left.height
        ):
            overlaps.append(f"{left.stage}/{right.stage}")
    return (
        PhysicalCheck(
            "Selected design",
            "pass",
            "a passing declared design is available",
        ),
        PhysicalCheck(
            "Exact part values",
            "pass",
            f"{len(parts)} parts carry exact values or declared behavioral expressions",
        ),
        PhysicalCheck(
            "Net and reference structure",
            "pass" if not duplicate_refs and not missing_nodes and not missing_role else "gap",
            "unique references, non-empty nodes and every part has a stage role"
            if not duplicate_refs and not missing_nodes and not missing_role
            else "duplicate references, missing nodes or an unknown stage role",
        ),
        PhysicalCheck(
            "Floorplan assignment",
            "pass" if not unassigned and not overlaps else "gap",
            "every part is assigned to one stage and stage rectangles do not overlap"
            if not unassigned and not overlaps
            else f"unassigned={unassigned or 'none'}, overlaps={overlaps or 'none'}",
        ),
        PhysicalCheck(
            "Route roles",
            "pass" if set(source_roles).issubset(set(stage_order)) else "gap",
            "all route roles are represented in the stage floorplan"
            if set(source_roles).issubset(set(stage_order))
            else "a route role has no stage block",
        ),
        PhysicalCheck(
            "SPICE emission",
            "pass" if ".END" in spice else "gap",
            "a SPICE-shaped reference deck was emitted; it has not been simulator-validated",
        ),
        PhysicalCheck(
            "Fabrication geometry",
            "gap",
            "no footprints, copper geometry, DRC, stackup or physical dimensions in this netlist payload; cent fabricate derives declared geometry separately",
        ),
    )


def _spice_deck(
    route_name: str,
    route_id: str,
    option_name: str,
    parts: tuple[PhysicalPart, ...],
) -> str:
    lines = [
        "* ============================================================",
        "* cent physical compiler - reference topology netlist",
        "* NOT A FABRICATION NETLIST",
        f"* route: {route_id}",
        f"* selected declared option: {option_name}",
        "* exact rational values are retained in the JSON payload;",
        "* SPICE numeric fields are deterministic decimal representations.",
        "* ============================================================",
        "",
    ]
    lines.extend(part.spice_line() for part in parts)
    lines.append("")
    if route_name == "delta-sigma":
        lines.extend((
            ".OP",
            ".TRAN 1e-4 1e-3",
            ".PRINT TRAN V(level)",
        ))
    else:
        lines.extend((
            ".OP",
            ".PRINT DC V(out)",
        ))
    lines.append(".END")
    return "\n".join(lines) + "\n"


def _delta_parts(binding: DeviceBinding) -> tuple[PhysicalPart, ...]:
    v_ref = _quantity(binding, "V_ref")
    r_in = _quantity(binding, "R_in")
    c_int = _quantity(binding, "C_int")
    v_lsb = _quantity(binding, "V_lsb")
    v_threshold = _quantity(binding, "V_threshold")
    v_offset = _quantity(binding, "V_offset")
    vin = v_ref * binding.input_value
    return (
        PhysicalPart(
            "VIN", "voltage-source", ("in", "0"), "input", vin, "V",
            note="declared input value V_ref*x",
        ),
        PhysicalPart("RIN", "resistor", ("in", "sum"), "integrator", r_in, "ohm"),
        PhysicalPart("CINT", "capacitor", ("sum", "int"), "integrator", c_int, "F"),
        PhysicalPart(
            "EINT", "vcvs", ("int", "0", "sum", "0"), "integrator",
            IDEAL_OPAMP_GAIN, "V/V",
            note="ideal integrating amplifier block; gain is a declared behavioral value",
        ),
        PhysicalPart("VTH", "voltage-source", ("thr", "0"), "quantizer", v_threshold, "V"),
        PhysicalPart("VOFF", "voltage-source", ("off", "0"), "quantizer", v_offset, "V"),
        PhysicalPart(
            "BQ", "behavioral-voltage", ("level", "0"), "quantizer",
            expression="IF(V(int)>=V(thr)+V(off),1,0)",
            note="ideal comparator; clock, metastability and jitter are not modeled",
        ),
        PhysicalPart("VREF", "voltage-source", ("ref", "0"), "feedback", v_ref, "V"),
        PhysicalPart("RFB", "resistor", ("fb", "sum"), "feedback", r_in, "ohm"),
        PhysicalPart(
            "BFB", "behavioral-voltage", ("fb", "0"), "feedback",
            expression="IF(V(level)>0.5,V(ref),0)",
            note="ideal one-bit feedback; switch resistance and charge injection are not modeled",
        ),
    )


def _log_parts(binding: DeviceBinding) -> tuple[PhysicalPart, ...]:
    v_in = _quantity(binding, "V_in")
    r_in = _quantity(binding, "R_in")
    i_s = _quantity(binding, "I_s")
    v_t = _quantity(binding, "V_T")
    r_out = _quantity(binding, "R_out")
    vt = _decimal(v_t, 18)
    is_text = _decimal(i_s, 18)
    return (
        PhysicalPart(
            "VIN", "voltage-source", ("in", "0"), "input", v_in, "V",
            note="declared input voltage V_ref*x",
        ),
        PhysicalPart("RIN", "resistor", ("in", "log"), "logger", r_in, "ohm"),
        PhysicalPart(
            "BLOG", "behavioral-current", ("log", "0"), "logger",
            expression=f"{is_text}*exp(V(log)/{vt})",
            parameters={"V_T": v_t, "I_s": i_s},
            note="ideal exponential junction I=I_s*exp(V/V_T); no series resistance or bias current",
        ),
        PhysicalPart(
            "EDIV", "vcvs", ("half", "0", "log", "0"), "half_gain",
            Fraction(1, 2), "V/V",
            note="ideal unity-buffered equal-resistor divider",
        ),
        PhysicalPart(
            "BANTI", "behavioral-current", ("0", "out"), "antilog",
            expression=f"{is_text}*exp(V(half)/{vt})",
            parameters={"V_T": v_t, "I_s": i_s},
            note="ideal diode-law antilog junction; no saturation or thermal coupling",
        ),
        PhysicalPart("ROUT", "resistor", ("out", "0"), "antilog", r_out, "ohm"),
    )


def _feedback_parts(binding: DeviceBinding) -> tuple[PhysicalPart, ...]:
    v_ref = _quantity(binding, "V_ref")
    v_in = _quantity(binding, "V_in")
    gain = _quantity(binding, "A")
    multiplier = _quantity(binding, "k")
    return (
        PhysicalPart(
            "VIN", "voltage-source", ("in", "0"), "input", v_in, "V",
            note="declared input voltage V_ref*x",
        ),
        PhysicalPart("VREF", "voltage-source", ("ref", "0"), "input", v_ref, "V"),
        PhysicalPart(
            "EOUT", "vcvs", ("out", "0", "in", "fb"), "error_amp",
            gain, "V/V",
            note="ideal finite-gain error amplifier; no slew, rails or output impedance",
        ),
        PhysicalPart(
            "EMULT", "behavioral-voltage", ("fb", "0"), "multiplier",
            expression=f"{_decimal(multiplier, 18)}*V(out)*V(out)/V(ref)",
            parameters={"k": multiplier},
            note="ideal multiplier feedback; no AD633 /10 scaling, nonlinearity or offset",
        ),
    )


def _route_roles(route_name: str) -> tuple[str, ...]:
    if route_name == "delta-sigma":
        route = assembly.delta_sigma_route()
    elif route_name == "sqrt-log":
        route = assembly.log_domain_sqrt_route()
    elif route_name == "sqrt-feedback":
        route = assembly.opamp_multiplier_sqrt_route()
    else:  # pragma: no cover - solve_route validates first
        raise CentError(ErrorCode.UNSUPPORTED, f"no physical route {route_name!r}")
    return tuple(component.role for component in route.components)


def build_physical(result: DesignResult) -> PhysicalPlan:
    """Emit a reference netlist and floorplan from a selected design."""
    if result.selected is None or result.selected.binding is None:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "no declared design is selected; no physical reference can be emitted",
        )
    binding = result.selected.binding
    route_key = result.route_name
    if route_key == "delta-sigma":
        stage_order = ("input", "integrator", "quantizer", "feedback")
        parts = _delta_parts(binding)
    elif route_key == "sqrt-log":
        stage_order = ("input", "logger", "half_gain", "antilog")
        parts = _log_parts(binding)
    elif route_key == "sqrt-feedback":
        stage_order = ("input", "error_amp", "multiplier")
        parts = _feedback_parts(binding)
    else:  # pragma: no cover - solve_route validates first
        raise CentError(
            ErrorCode.UNSUPPORTED,
            f"no physical emitter for route {route_key!r}",
        )

    nets = _build_nets(parts)
    layout = _build_layout(stage_order, parts, nets)
    spice = _spice_deck(route_key, binding.route_id, result.selected.option.name, parts)
    source_roles = _route_roles(route_key)
    checks = _check(parts, stage_order, layout, spice, source_roles)

    gaps = [
        "The SPICE deck is a reference topology with ideal behavioral blocks; it has not been simulator-validated or compared to a transistor-level model.",
        "No footprints, package parasitics, PCB geometry, stackup, DRC, thermal placement or assembly constraints are emitted by this netlist payload; cent fabricate derives a declared prototype geometry, still not a manufactured or DRC-signoff board.",
        "The floorplan uses declared schematic grid units, not millimetres or manufacturing coordinates.",
        "No BOM, supplier part, tolerance distribution, yield, measurement or calibration procedure is attached.",
        "No dynamic bandwidth, stability, noise, settling, clock jitter or thermal drift analysis is included.",
        "Ideal behavioral blocks in this deck (EINT, BQ, BFB, BLOG, BANTI, EOUT, EMULT) are not vendor models.",
    ]
    if route_key == "delta-sigma":
        gaps.append(
            "The ideal integrator gain and behavioral comparator/feedback blocks are not device parameters; the exact route loop remains the source of the normalized check."
        )
    return PhysicalPlan(
        design=result,
        route_key=route_key,
        route_id=binding.route_id,
        route_name=result.space.name,
        topology=binding.topology,
        source_roles=source_roles,
        parts=parts,
        nets=nets,
        spice=spice,
        layout=layout,
        checks=checks,
        gaps=tuple(gaps),
    )


def emit_physical(
    route_name: str,
    *,
    input_value: Any | None = None,
    input_min: Any | None = None,
    input_max: Any | None = None,
    accuracy: Any = "1/100",
    max_cost: Any | None = None,
    min_bandwidth: Any | None = None,
) -> PhysicalPlan:
    """Solve the declared design and emit its reference physical artifacts."""
    result = solve_route(
        route_name,
        input_value=input_value,
        input_min=input_min,
        input_max=input_max,
        accuracy=accuracy,
        max_cost=max_cost,
        min_bandwidth=min_bandwidth,
    )
    if result.selected is None:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "no declared design satisfies the constraints; no physical reference was emitted",
        )
    return build_physical(result)


__all__ = [
    "IDEAL_OPAMP_GAIN",
    "LAYOUT_SCHEMA",
    "LayoutBlock",
    "LayoutLink",
    "LayoutPlan",
    "PhysicalCheck",
    "PhysicalNet",
    "PhysicalPart",
    "PhysicalPlan",
    "SCHEMA",
    "build_physical",
    "emit_physical",
]
