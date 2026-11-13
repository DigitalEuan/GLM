"""Declared fabrication geometry from a reference physical plan.

This layer takes the *reference topology* emitted by :mod:`cent_compiler.physical`
and derives a declared, millimetre-scale geometry: a package footprint per part,
a four-layer stackup, a deterministic two-layer escape/bus router, lumped
parasitic estimates, a single-node junction-temperature model and an independent
design-rule check over that geometry.

Every number is an exact rational.  The layer is deliberately narrow:

* footprints are declared generic land patterns, not vendor drawings;
* the router is a fixed orthogonal escape/bus scheme, not a placement or
  routing optimiser;
* parasitics are lumped first-order formulas from declared resistivity and
  permittivity, without field solving, fringing, skin effect or coupling;
* the thermal model is a single-node junction-to-ambient rise;
* the DRC checks the declared rules against the generated geometry and is not a
  fabrication sign-off.

The remaining physical claims stay explicit gaps.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping

from . import physical
from .exact import CentError, ErrorCode, Q, q_to_json

SCHEMA = "cent-fabrication/1"
UNITS = "mm"

#: Declared material constants.  These are nominal values, not measurements.
EPSILON_0 = Fraction("8.8541878128e-12")   # F/m, truncated CODATA value
COPPER_RESISTIVITY = Fraction("1.68e-8")    # ohm m at 20 C
RELATIVE_PERMITTIVITY = Fraction(22, 5)     # declared FR-4 nominal
COPPER_THICKNESS = Fraction(35, 1000)       # 1 oz copper, mm
DIELECTRIC_THICKNESS = Fraction(36, 100)    # declared prepreg/core, mm
PER_MM_INDUCTANCE = Fraction(1, 10 ** 9)    # declared 1 nH/mm, H/mm

#: Parts whose declared law is temperature-sensitive: exponential junctions and
#: the analog multiplier.  They are placed in a quiet row away from dissipators.
SENSITIVE_REFS = frozenset({"BLOG", "BANTI", "EMULT"})

ROW_GAP = Fraction(3)
COURTYARD_MARGIN = Fraction(1, 2)
PART_GAP = Fraction(3, 2)
QUIET_X_SHIFT = Fraction(2)
CHANNEL_GAP = Fraction(2)
PLANE_LAYER = "bottom"
GROUND_NET = "0"


def _json(value: Any) -> Any:
    if isinstance(value, Fraction):
        return q_to_json(value)
    if isinstance(value, Mapping):
        return {str(key): _json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json(item) for item in value]
    return value


def _decimal(value: Q, places: int = 12) -> str:
    """Render a rational as a deterministic decimal using integer arithmetic."""
    sign = "-" if value < 0 else ""
    value = abs(value)
    scale = 10 ** places
    scaled = value.numerator * scale // value.denominator
    whole, fraction = divmod(scaled, scale)
    text = f"{fraction:0{places}d}".rstrip("0")
    return sign + str(whole) + (f".{text}" if text else "")


@dataclass(frozen=True)
class DRCRules:
    """Declared manufacturing rules and model constants, all in mm or K."""

    min_clearance: Q = Fraction(1, 5)
    min_width: Q = Fraction(1, 4)
    trace_width: Q = Fraction(1, 4)
    edge_margin: Q = Fraction(1)
    bus_pitch: Q = Fraction(1)
    thermal_keepout: Q = Fraction(5)
    quiet_row_offset: Q = Fraction(8)
    ambient_temperature: Q = Fraction(298)
    max_junction_temperature: Q = Fraction(398)
    drill: Q = Fraction(3, 10)
    via_pad: Q = Fraction(3, 5)
    min_annular_ring: Q = Fraction(3, 20)

    def __post_init__(self) -> None:
        for name in (
            "min_clearance",
            "min_width",
            "trace_width",
            "edge_margin",
            "bus_pitch",
            "thermal_keepout",
            "quiet_row_offset",
            "ambient_temperature",
            "max_junction_temperature",
            "drill",
            "via_pad",
            "min_annular_ring",
        ):
            value = getattr(self, name)
            if not isinstance(value, Fraction) or value <= 0:
                raise CentError(
                    ErrorCode.DOMAIN_ERROR,
                    f"DRC rule {name} must be a positive exact rational",
                )
        if self.trace_width < self.min_width:
            raise CentError(
                ErrorCode.DOMAIN_ERROR,
                "declared trace width must not be below the minimum width rule",
            )
        if self.drill >= self.via_pad:
            raise CentError(
                ErrorCode.DOMAIN_ERROR,
                "via drill must be smaller than the via pad",
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "units": UNITS,
            "min_clearance": q_to_json(self.min_clearance),
            "min_width": q_to_json(self.min_width),
            "trace_width": q_to_json(self.trace_width),
            "edge_margin": q_to_json(self.edge_margin),
            "bus_pitch": q_to_json(self.bus_pitch),
            "thermal_keepout": q_to_json(self.thermal_keepout),
            "quiet_row_offset": q_to_json(self.quiet_row_offset),
            "ambient_temperature": q_to_json(self.ambient_temperature),
            "max_junction_temperature": q_to_json(self.max_junction_temperature),
            "drill": q_to_json(self.drill),
            "via_pad": q_to_json(self.via_pad),
            "min_annular_ring": q_to_json(self.min_annular_ring),
        }


@dataclass(frozen=True)
class Package:
    """A declared generic land pattern."""

    name: str
    body_width: Q
    body_height: Q
    pad_width: Q
    pad_height: Q
    pad_pitch: Q
    pad_count: int
    theta_ja: Q
    note: str

    @property
    def courtyard_width(self) -> Q:
        return self.body_width + 2 * COURTYARD_MARGIN

    @property
    def courtyard_height(self) -> Q:
        return self.body_height + 2 * COURTYARD_MARGIN

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "body_width": q_to_json(self.body_width),
            "body_height": q_to_json(self.body_height),
            "pad_width": q_to_json(self.pad_width),
            "pad_height": q_to_json(self.pad_height),
            "pad_pitch": q_to_json(self.pad_pitch),
            "pad_count": self.pad_count,
            "theta_ja": q_to_json(self.theta_ja),
            "courtyard_width": q_to_json(self.courtyard_width),
            "courtyard_height": q_to_json(self.courtyard_height),
            "note": self.note,
        }


PACKAGES: Mapping[str, Package] = {
    "test-point-2": Package(
        "test-point-2", Fraction(2), Fraction(6, 5), Fraction(3, 5),
        Fraction(3, 5), Fraction(4, 5), 2, Fraction(120),
        "declared two-pad test-point land pattern; not a vendor drawing",
    ),
    "chip-0603": Package(
        "chip-0603", Fraction(8, 5), Fraction(4, 5), Fraction(3, 5),
        Fraction(3, 5), Fraction(4, 5), 2, Fraction(200),
        "declared 0603-style two-pad chip land pattern; not a vendor drawing",
    ),
    "module-2": Package(
        "module-2", Fraction(6), Fraction(4), Fraction(9, 10),
        Fraction(9, 10), Fraction(8, 5), 2, Fraction(120),
        "declared two-pad behavioral-module footprint; no vendor package",
    ),
    "module-4": Package(
        "module-4", Fraction(9), Fraction(5), Fraction(9, 10),
        Fraction(9, 10), Fraction(8, 5), 4, Fraction(120),
        "declared four-pad behavioral-module footprint; no vendor package",
    ),
}

PACKAGE_BY_KIND: Mapping[str, str] = {
    "voltage-source": "test-point-2",
    "resistor": "chip-0603",
    "capacitor": "chip-0603",
    "vcvs": "module-4",
    "behavioral-voltage": "module-2",
    "behavioral-current": "module-2",
}


@dataclass(frozen=True)
class Layer:
    """One declared copper layer."""

    name: str
    kind: str
    copper_thickness: Q
    dielectric_below: Q
    note: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "copper_thickness": q_to_json(self.copper_thickness),
            "dielectric_below": q_to_json(self.dielectric_below),
            "note": self.note,
        }


@dataclass(frozen=True)
class Stackup:
    """The declared four-layer stackup."""

    layers: tuple[Layer, ...]
    relative_permittivity: Q

    @property
    def total_thickness(self) -> Q:
        copper = sum(
            (layer.copper_thickness for layer in self.layers), Fraction(0)
        )
        dielectric = sum(
            (layer.dielectric_below for layer in self.layers), Fraction(0)
        )
        return copper + dielectric

    def as_dict(self) -> dict[str, Any]:
        return {
            "layers": [layer.as_dict() for layer in self.layers],
            "relative_permittivity": q_to_json(self.relative_permittivity),
            "total_thickness": q_to_json(self.total_thickness),
            "note": (
                "declared nominal 4-layer FR-4-style stackup; no impedance "
                "control, tolerance or manufacturer stackup is implied"
            ),
        }


def _stackup() -> Stackup:
    return Stackup(
        layers=(
            Layer("top", "signal", COPPER_THICKNESS, DIELECTRIC_THICKNESS,
                  "component side: pads and part bodies"),
            Layer("in1", "signal", COPPER_THICKNESS, DIELECTRIC_THICKNESS,
                  "vertical pad escapes"),
            Layer("in2", "signal", COPPER_THICKNESS, DIELECTRIC_THICKNESS,
                  "horizontal per-net buses"),
            Layer(PLANE_LAYER, "plane", COPPER_THICKNESS, Fraction(0),
                  "inset ground plane"),
        ),
        relative_permittivity=RELATIVE_PERMITTIVITY,
    )


@dataclass(frozen=True)
class Pad:
    """One footprint pad at an exact millimetre coordinate."""

    pin: int
    net: str
    x: Q
    y: Q
    width: Q
    height: Q

    @property
    def rect(self) -> tuple[Q, Q, Q, Q]:
        return (
            self.x - self.width / 2,
            self.y - self.height / 2,
            self.x + self.width / 2,
            self.y + self.height / 2,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "pin": self.pin,
            "net": self.net,
            "x": q_to_json(self.x),
            "y": q_to_json(self.y),
            "width": q_to_json(self.width),
            "height": q_to_json(self.height),
        }


@dataclass(frozen=True)
class Row:
    """A declared placement row: one stage or the quiet row."""

    stage: str
    kind: str
    y: Q
    height: Q

    def as_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "kind": self.kind,
            "y": q_to_json(self.y),
            "height": q_to_json(self.height),
        }


@dataclass(frozen=True)
class Footprint:
    """One placed part with its land pattern and thermal declaration."""

    ref: str
    role: str
    package: Package
    stage: str
    row: str
    x: Q
    y: Q
    pads: tuple[Pad, ...]
    dissipation: Q
    dissipation_source: str
    junction_temperature: Q
    note: str

    @property
    def courtyard(self) -> tuple[Q, Q, Q, Q]:
        return (
            self.x - self.package.courtyard_width / 2,
            self.y - self.package.courtyard_height / 2,
            self.x + self.package.courtyard_width / 2,
            self.y + self.package.courtyard_height / 2,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "ref": self.ref,
            "role": self.role,
            "package": self.package.name,
            "stage": self.stage,
            "row": self.row,
            "x": q_to_json(self.x),
            "y": q_to_json(self.y),
            "courtyard": [q_to_json(item) for item in self.courtyard],
            "pads": [pad.as_dict() for pad in self.pads],
            "dissipation": q_to_json(self.dissipation),
            "dissipation_source": self.dissipation_source,
            "junction_temperature": q_to_json(self.junction_temperature),
            "note": self.note,
        }


@dataclass(frozen=True)
class TraceSegment:
    """One axis-aligned copper segment on a declared layer."""

    net: str
    layer: str
    start: tuple[Q, Q]
    end: tuple[Q, Q]
    width: Q

    @property
    def length(self) -> Q:
        return abs(self.end[0] - self.start[0]) + abs(self.end[1] - self.start[1])

    @property
    def rect(self) -> tuple[Q, Q, Q, Q]:
        x0 = min(self.start[0], self.end[0]) - self.width / 2
        x1 = max(self.start[0], self.end[0]) + self.width / 2
        y0 = min(self.start[1], self.end[1]) - self.width / 2
        y1 = max(self.start[1], self.end[1]) + self.width / 2
        return (x0, y0, x1, y1)

    def as_dict(self) -> dict[str, Any]:
        return {
            "net": self.net,
            "layer": self.layer,
            "start": [q_to_json(item) for item in self.start],
            "end": [q_to_json(item) for item in self.end],
            "width": q_to_json(self.width),
            "length": q_to_json(self.length),
        }


@dataclass(frozen=True)
class Via:
    """One declared through via with an exact annular ring."""

    net: str
    x: Q
    y: Q
    span: str
    pad_diameter: Q
    drill: Q

    @property
    def annular_ring(self) -> Q:
        return (self.pad_diameter - self.drill) / 2

    @property
    def rect(self) -> tuple[Q, Q, Q, Q]:
        half = self.pad_diameter / 2
        return (self.x - half, self.y - half, self.x + half, self.y + half)

    def as_dict(self) -> dict[str, Any]:
        return {
            "net": self.net,
            "x": q_to_json(self.x),
            "y": q_to_json(self.y),
            "span": self.span,
            "pad_diameter": q_to_json(self.pad_diameter),
            "drill": q_to_json(self.drill),
            "annular_ring": q_to_json(self.annular_ring),
        }


@dataclass(frozen=True)
class NetParasitics:
    """Lumped first-order parasitic estimates for one routed net."""

    net: str
    length: Q
    resistance: Q
    capacitance: Q
    inductance: Q
    rule: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "net": self.net,
            "length": q_to_json(self.length),
            "resistance": q_to_json(self.resistance),
            "capacitance": q_to_json(self.capacitance),
            "inductance": q_to_json(self.inductance),
            "rule": self.rule,
        }


@dataclass(frozen=True)
class ThermalPart:
    """One declared junction-temperature row."""

    ref: str
    stage: str
    dissipation: Q
    theta_ja: Q
    ambient: Q
    junction: Q
    sensitive: bool
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "ref": self.ref,
            "stage": self.stage,
            "dissipation": q_to_json(self.dissipation),
            "theta_ja": q_to_json(self.theta_ja),
            "ambient": q_to_json(self.ambient),
            "junction_temperature": q_to_json(self.junction),
            "sensitive": self.sensitive,
            "source": self.source,
        }


@dataclass(frozen=True)
class FabricationCheck:
    """One independent design-rule result with exact compared values."""

    name: str
    status: str
    rule: str
    value: Any
    limit: Any
    detail: str

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "passed": self.passed,
            "rule": self.rule,
            "value": _json(self.value),
            "limit": _json(self.limit),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class FabricationPlan:
    """Declared geometry, parasitics, thermal placement and DRC for one route."""

    physical: physical.PhysicalPlan
    rules: DRCRules
    stackup: Stackup
    width: Q
    height: Q
    rows: tuple[Row, ...]
    footprints: tuple[Footprint, ...]
    traces: tuple[TraceSegment, ...]
    vias: tuple[Via, ...]
    unrouted: tuple[str, ...]
    parasitics: tuple[NetParasitics, ...]
    thermal: tuple[ThermalPart, ...]
    ground_plane: tuple[Q, Q, Q, Q]
    checks: tuple[FabricationCheck, ...]
    gaps: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def status(self) -> str:
        return "drc-pass" if self.passed else "drc-gap"

    def as_dict(self) -> dict[str, Any]:
        selected = self.physical.selected
        assert selected is not None
        return {
            "schema": SCHEMA,
            "units": UNITS,
            "status": self.status,
            "claim": (
                "declared geometry checked against declared rules; "
                "not a fabricated, DRC-signed-off or measured board"
            ),
            "route": self.physical.route_id,
            "route_key": self.physical.route_key,
            "route_name": self.physical.route_name,
            "selected": {
                "option": selected.option.name,
                "parameters": _json(dict(selected.option.parameters)),
            },
            "rules": self.rules.as_dict(),
            "stackup": self.stackup.as_dict(),
            "board": {
                "width": q_to_json(self.width),
                "height": q_to_json(self.height),
                "units": UNITS,
                "ground_plane": [q_to_json(item) for item in self.ground_plane],
            },
            "rows": [row.as_dict() for row in self.rows],
            "footprints": [item.as_dict() for item in self.footprints],
            "traces": [item.as_dict() for item in self.traces],
            "vias": [item.as_dict() for item in self.vias],
            "unrouted_nets": list(self.unrouted),
            "parasitics": [item.as_dict() for item in self.parasitics],
            "thermal": [item.as_dict() for item in self.thermal],
            "checks": [item.as_dict() for item in self.checks],
            "passed": self.passed,
            "gaps": list(self.gaps),
        }

    def render_text(self) -> str:
        lines = [
            "=" * 78,
            "DECLARED FABRICATION GEOMETRY",
            "=" * 78,
            f"Route: {self.physical.route_name} ({self.physical.route_key})",
            "Status: declared geometry checked against declared rules; not fabricated",
            f"Board: {_decimal(self.width)} x {_decimal(self.height)} {UNITS}",
            "",
            "Stackup",
        ]
        for layer in self.stackup.layers:
            lines.append(
                f"  {layer.name:<7} {layer.kind:<7} copper {_decimal(layer.copper_thickness)} mm "
                f"dielectric {_decimal(layer.dielectric_below)} mm  {layer.note}"
            )
        lines.append(
            f"  total thickness {_decimal(self.stackup.total_thickness)} mm, "
            f"epsilon_r {_decimal(self.stackup.relative_permittivity)}"
        )
        lines.extend(("", "Footprints"))
        for item in self.footprints:
            lines.append(
                f"  {item.ref:<6} {item.package.name:<13} {item.stage:<12} "
                f"row={item.row:<8} x={_decimal(item.x)} y={_decimal(item.y)}  "
                f"P={_decimal(item.dissipation, 15)} W  Tj={_decimal(item.junction_temperature)} K"
            )
        lines.extend(("", "Parasitics"))
        for item in self.parasitics:
            lines.append(
                f"  {item.net:<10} len={_decimal(item.length)} mm  "
                f"R={_decimal(item.resistance, 15)} ohm  "
                f"C={_decimal(item.capacitance, 18)} F  "
                f"L={_decimal(item.inductance, 15)} H"
            )
        lines.append(f"  vias: {len(self.vias)}")
        if self.unrouted:
            lines.append(
                f"  unrouted control net(s): {', '.join(self.unrouted)}"
            )
        lines.extend(("", "Thermal"))
        for item in self.thermal:
            mark = "sensitive" if item.sensitive else "normal"
            lines.append(
                f"  {item.ref:<6} {mark:<9} P={_decimal(item.dissipation, 15)} W  "
                f"theta_ja={_decimal(item.theta_ja)} K/W  "
                f"Tj={_decimal(item.junction)} K"
            )
        lines.extend(("", "Design-rule checks"))
        for check in self.checks:
            value = "-" if check.value is None else _decimal(check.value)
            limit = "-" if check.limit is None else _decimal(check.limit)
            lines.append(
                f"  [{check.status:<4}] {check.name:<26} "
                f"value={value:<14} limit={limit:<10} {check.detail}"
            )
        lines.extend(("", "Remaining gaps"))
        for gap in self.gaps:
            lines.append(f"  - {gap}")
        return "\n".join(lines)


def _rect_gap(
    left: tuple[Q, Q, Q, Q], right: tuple[Q, Q, Q, Q]
) -> Q:
    """Exact axis-aligned (Chebyshev) free distance between rectangles."""
    dx = max(left[0] - right[2], right[0] - left[2])
    dy = max(left[1] - right[3], right[1] - left[3])
    return max(Fraction(0), dx, dy)


def _package(part: physical.PhysicalPart) -> Package:
    name = PACKAGE_BY_KIND.get(part.kind)
    if name is None:
        raise CentError(
            ErrorCode.UNSUPPORTED,
            f"no declared footprint for part {part.ref!r} kind {part.kind!r}",
        )
    package = PACKAGES[name]
    if len(part.nodes) != package.pad_count:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            f"part {part.ref!r} has {len(part.nodes)} nodes but its declared "
            f"footprint has {package.pad_count} pads",
        )
    return package


def _part_value(parts: tuple[physical.PhysicalPart, ...], ref: str) -> Q:
    for part in parts:
        if part.ref == ref and isinstance(part.value, Fraction):
            return part.value
    raise CentError(
        ErrorCode.UNSUPPORTED,
        f"part {ref!r} has no exact scalar value for the thermal model",
    )


def _binding_bound(
    plan: physical.PhysicalPlan, symbol: str
) -> Q | None:
    """Return a scalar or a certified magnitude bound for one binding quantity."""
    selected = plan.design.selected
    if selected is None or selected.binding is None:
        return None
    for item in selected.binding.quantities:
        if item.symbol != symbol:
            continue
        if isinstance(item.value, Fraction):
            return item.value
        lo = getattr(item.value, "lo", None)
        hi = getattr(item.value, "hi", None)
        if isinstance(lo, Fraction) and isinstance(hi, Fraction):
            return max(abs(lo), abs(hi))
    return None


def _dissipation(
    plan: physical.PhysicalPlan,
) -> dict[str, tuple[Q, str]]:
    """Declared worst-case or simulated dissipation per part.

    No value is invented: each entry is either an exact worst-case bound from
    the emitted source and resistance values, or a simulated binding current
    squared times a declared resistance.
    """
    parts = plan.parts
    result: dict[str, tuple[Q, str]] = {}
    if plan.route_key == "delta-sigma":
        vin = _part_value(parts, "VIN")
        vref = _part_value(parts, "VREF")
        rin = _part_value(parts, "RIN")
        result["RIN"] = (
            vin * vin / rin,
            "declared worst case V_in^2/R_in; no temperature coefficient",
        )
        result["RFB"] = (
            vref * vref / rin,
            "declared worst case V_ref^2/R_in; no temperature coefficient",
        )
    elif plan.route_key == "sqrt-log":
        vin = _part_value(parts, "VIN")
        rin = _part_value(parts, "RIN")
        r_out = _part_value(parts, "ROUT")
        current = _binding_bound(plan, "I_out")
        if current is None:
            raise CentError(
                ErrorCode.UNSUPPORTED,
                "the log-domain binding does not declare the simulated output current",
            )
        result["RIN"] = (
            vin * vin / rin,
            "declared V_in^2/R_in from the exact input current; no temperature coefficient",
        )
        result["ROUT"] = (
            current * current * r_out,
            "certified |I_out| upper bound squared times the declared R_out",
        )
    elif plan.route_key == "sqrt-feedback":
        pass
    return result


def _place(
    parts: tuple[physical.PhysicalPart, ...],
    stage_order: tuple[str, ...],
    rules: DRCRules,
) -> tuple[dict[str, tuple[Q, Q, Package, str, str]], tuple[Row, ...], Q]:
    """Pack parts into one row per stage plus one quiet row for sensitive parts."""
    placement: dict[str, tuple[Q, Q, Package, str, str]] = {}
    rows: list[Row] = []
    sensitive = {part.ref for part in parts if part.ref in SENSITIVE_REFS}
    cursor = rules.edge_margin + CHANNEL_GAP

    occupied: list[Q] = []
    min_dx = (
        max(package.pad_width for package in PACKAGES.values())
        + rules.min_clearance
        + Fraction(1, 20)
    )

    def place_row(
        row_parts: list[physical.PhysicalPart],
        stage: str,
        row_kind: str,
        y: Q,
        x_offset: Q,
    ) -> None:
        x_cursor = rules.edge_margin + CHANNEL_GAP + x_offset
        for part in row_parts:
            package = _package(part)
            offsets = _pad_offsets(part, package)
            x = x_cursor + package.courtyard_width / 2
            for _ in range(400):
                xs = [x + offset for offset in offsets]
                if all(
                    abs(candidate - used) >= min_dx
                    for candidate in xs
                    for used in occupied
                ):
                    break
                x += Fraction(1, 2)
            else:  # pragma: no cover - the board is always wide enough
                raise CentError(
                    ErrorCode.DOMAIN_ERROR,
                    f"could not assign distinct pad columns to {part.ref!r}",
                )
            occupied.extend(xs)
            placement[part.ref] = (x, y, package, stage, row_kind)
            x_cursor = max(
                x_cursor, x + package.courtyard_width / 2 + PART_GAP
            )

    for stage in stage_order:
        row_parts = [
            part for part in parts
            if part.role == stage and part.ref not in sensitive
        ]
        if not row_parts:
            continue
        height = max(_package(part).courtyard_height for part in row_parts)
        y = cursor + height / 2
        place_row(row_parts, stage, stage, y, Fraction(0))
        rows.append(Row(stage, stage, y, height))
        cursor = y + height / 2 + ROW_GAP

    quiet_parts = [part for part in parts if part.ref in sensitive]
    if quiet_parts:
        height = max(_package(part).courtyard_height for part in quiet_parts)
        y = cursor + rules.quiet_row_offset + height / 2
        place_row(quiet_parts, "quiet", "quiet", y, QUIET_X_SHIFT)
        rows.append(Row("quiet", "quiet", y, height))
        cursor = y + height / 2

    return placement, tuple(rows), cursor


def _pad_offsets(
    part: physical.PhysicalPart, package: Package
) -> tuple[Q, ...]:
    count = len(part.nodes)
    pitch = package.pad_pitch
    if count > 1:
        pitch = min(pitch, (package.body_width - Fraction(4, 5)) / (count - 1))
    return tuple(
        (Fraction(index) - Fraction(count - 1, 2)) * pitch
        for index in range(count)
    )


def _pads(
    part: physical.PhysicalPart, package: Package, x: Q, y: Q
) -> tuple[Pad, ...]:
    return tuple(
        Pad(
            pin=index + 1,
            net=net,
            x=x + offset,
            y=y,
            width=package.pad_width,
            height=package.pad_height,
        )
        for index, (net, offset) in enumerate(
            zip(part.nodes, _pad_offsets(part, package))
        )
    )


def _route(
    plan: physical.PhysicalPlan,
    footprints: tuple[Footprint, ...],
    rules: DRCRules,
    channel_start: Q,
) -> tuple[
    tuple[TraceSegment, ...],
    tuple[Via, ...],
    tuple[NetParasitics, ...],
    Q,
    tuple[str, ...],
]:
    nets = [net.name for net in plan.nets if net.name != GROUND_NET]
    traces: list[TraceSegment] = []
    vias: list[Via] = []
    parasitics: list[NetParasitics] = []
    unrouted: list[str] = []
    last_y = channel_start

    pad_lookup: dict[str, list[Pad]] = {}
    for footprint in footprints:
        for pad in footprint.pads:
            pad_lookup.setdefault(pad.net, []).append(pad)

    for index, net in enumerate(nets):
        bus_y = channel_start + (index + 1) * rules.bus_pitch
        last_y = max(last_y, bus_y)
        pads = sorted(pad_lookup.get(net, []), key=lambda item: (item.x, item.y))
        if len(pads) < 2:
            # A single-pin net is a declared control label read by an ideal
            # behavioral block; no copper route is invented for it.
            unrouted.append(net)
            continue
        length = Fraction(0)
        copper_length = Fraction(0)
        for pad in pads:
            segment = TraceSegment(
                net, "in1", (pad.x, pad.y), (pad.x, bus_y), rules.trace_width
            )
            traces.append(segment)
            length += segment.length
            copper_length += segment.length
            vias.append(
                Via(net, pad.x, pad.y, "top-in1", rules.via_pad, rules.drill)
            )
            vias.append(
                Via(net, pad.x, bus_y, "in1-in2", rules.via_pad, rules.drill)
            )
        bus = TraceSegment(
            net, "in2", (pads[0].x, bus_y), (pads[-1].x, bus_y), rules.trace_width
        )
        traces.append(bus)
        length += bus.length
        copper_length += bus.length
        resistance = (
            COPPER_RESISTIVITY * length / (rules.trace_width * COPPER_THICKNESS)
        )
        capacitance = (
            EPSILON_0
            * RELATIVE_PERMITTIVITY
            * rules.trace_width
            * copper_length
            / (1000 * DIELECTRIC_THICKNESS)
        )
        parasitics.append(
            NetParasitics(
                net=net,
                length=length,
                resistance=resistance,
                capacitance=capacitance,
                inductance=PER_MM_INDUCTANCE * copper_length,
                rule=(
                    "R = rho*L/(w*t) with declared rho; C = eps0*eps_r*w*L/h "
                    "parallel-plate lumped estimate; L = declared 1 nH/mm; "
                    "no field solve, fringing, skin effect or coupling"
                ),
            )
        )

    for footprint in footprints:
        for pad in footprint.pads:
            if pad.net != GROUND_NET:
                continue
            vias.append(
                Via(GROUND_NET, pad.x, pad.y, "top-plane", rules.via_pad, rules.drill)
            )

    return tuple(traces), tuple(vias), tuple(parasitics), last_y, tuple(unrouted)


def _check(
    name: str,
    rule: str,
    value: Any,
    limit: Any,
    passed: bool,
    detail: str,
) -> FabricationCheck:
    return FabricationCheck(
        name=name,
        status="pass" if passed else "gap",
        rule=rule,
        value=value,
        limit=limit,
        detail=detail,
    )


def _drc(
    plan: physical.PhysicalPlan,
    footprints: tuple[Footprint, ...],
    traces: tuple[TraceSegment, ...],
    vias: tuple[Via, ...],
    unrouted: tuple[str, ...],
    width: Q,
    height: Q,
    rules: DRCRules,
) -> tuple[FabricationCheck, ...]:
    # -- reference coverage -------------------------------------------------
    reference_nets = {net.name for net in plan.nets}
    routed_nets = {pad.net for item in footprints for pad in item.pads}
    missing = sorted(reference_nets - routed_nets)
    extra = sorted(routed_nets - reference_nets)
    coverage_ok = not missing and not extra
    pad_counts: dict[str, int] = {}
    for item in footprints:
        for pad in item.pads:
            pad_counts[pad.net] = pad_counts.get(pad.net, 0) + 1
    expected_multi = sum(
        1
        for net in reference_nets
        if net != GROUND_NET and pad_counts.get(net, 0) >= 2
    )
    routed_multi = len(
        {trace.net for trace in traces if trace.net != GROUND_NET}
    )
    coverage_detail = (
        "every reference net and pad appears in the corresponding geometry"
        if coverage_ok
        else f"missing={missing or 'none'}, extra={extra or 'none'}"
    )

    # -- copper clearance ---------------------------------------------------
    def min_spacing(
        items: list[tuple[str, tuple[Q, Q, Q, Q]]],
    ) -> tuple[Q | None, str]:
        worst: Q | None = None
        pair = "none"
        for left in range(len(items)):
            for right in range(left + 1, len(items)):
                if items[left][0] == items[right][0]:
                    continue
                gap = _rect_gap(items[left][1], items[right][1])
                if worst is None or gap < worst:
                    worst = gap
                    pair = f"{items[left][0]}/{items[right][0]}"
        return worst, pair

    pad_items = [
        (pad.net, pad.rect) for item in footprints for pad in item.pads
    ]
    pad_gap, pad_pair = min_spacing(pad_items)
    trace_gaps: list[tuple[Q, str]] = []
    for layer in ("top", "in1", "in2", PLANE_LAYER):
        items = [(trace.net, trace.rect) for trace in traces if trace.layer == layer]
        gap, pair = min_spacing(items)
        if gap is not None:
            trace_gaps.append((gap, f"{layer}:{pair}"))
    via_gap, via_pair = min_spacing([(via.net, via.rect) for via in vias])
    candidates: list[tuple[Q, str]] = []
    if pad_gap is not None:
        candidates.append((pad_gap, f"pads:{pad_pair}"))
    if via_gap is not None:
        candidates.append((via_gap, f"vias:{via_pair}"))
    candidates.extend(
        (gap, f"{layer}:{pair}") for gap, pair in trace_gaps
    )
    if candidates:
        clearance, clearance_pair = min(candidates, key=lambda entry: entry[0])
    else:
        clearance, clearance_pair = None, "none"

    courtyard_gap, courtyard_pair = min_spacing(
        [(item.ref, item.courtyard) for item in footprints]
    )

    # -- board edge ---------------------------------------------------------
    def min_edge(
        rects: list[tuple[Q, Q, Q, Q]],
    ) -> Q | None:
        margins: list[Q] = []
        for x0, y0, x1, y1 in rects:
            margins.extend((x0, y0, width - x1, height - y1))
        return min(margins) if margins else None

    copper_rects = [pad.rect for item in footprints for pad in item.pads]
    copper_rects.extend(trace.rect for trace in traces)
    copper_rects.extend(via.rect for via in vias)
    edge = min_edge(copper_rects)

    # -- trace width --------------------------------------------------------
    widths = [trace.width for trace in traces]
    narrowest = min(widths) if widths else rules.trace_width

    # -- via annular ring ---------------------------------------------------
    rings = [via.annular_ring for via in vias]
    narrow_ring = min(rings) if rings else None

    # -- thermal keep-out ---------------------------------------------------
    sensitive = [item for item in footprints if item.ref in SENSITIVE_REFS]
    dissipators = [item for item in footprints if item.dissipation > 0]
    thermal_gap: Q | None = None
    thermal_pair = "none"
    for left in sensitive:
        for right in dissipators:
            gap = _rect_gap(left.courtyard, right.courtyard)
            if thermal_gap is None or gap < thermal_gap:
                thermal_gap = gap
                thermal_pair = f"{left.ref}/{right.ref}"

    hottest = max(
        (item.junction_temperature for item in footprints), default=rules.ambient_temperature
    )

    checks = (
        _check(
            "Reference coverage",
            "every reference net and pad appears exactly once in the geometry",
            len(routed_nets),
            len(reference_nets),
            coverage_ok,
            coverage_detail,
        ),
        _check(
            "Net routability",
            "every non-ground net with at least two pads is routed",
            routed_multi,
            expected_multi,
            routed_multi == expected_multi,
            "all multi-pin nets are routed"
            + (
                f"; declared single-pin behavioral control label(s) "
                f"{', '.join(unrouted)} are not copper-routed"
                if unrouted
                else ""
            ),
        ),
        _check(
            "Board edge",
            "all copper lies at least the declared edge margin inside the board",
            edge,
            rules.edge_margin,
            edge is not None and edge >= rules.edge_margin,
            "generated copper respects the board outline"
            if edge is not None and edge >= rules.edge_margin
            else "copper violates the declared board edge margin",
        ),
        _check(
            "Trace width",
            "every trace is at least the declared minimum width",
            narrowest,
            rules.min_width,
            narrowest >= rules.min_width,
            "all routed segments satisfy the declared width rule"
            if narrowest >= rules.min_width
            else "a routed segment is narrower than the declared minimum",
        ),
        _check(
            "Footprint courtyards",
            "placed footprint courtyards do not overlap",
            courtyard_gap,
            Fraction(0),
            courtyard_gap is None or courtyard_gap >= 0,
            "no two placed footprints overlap"
            if courtyard_gap is None or courtyard_gap >= 0
            else f"courtyard overlap between {courtyard_pair}",
        ),
        _check(
            "Copper clearance",
            "different nets keep at least the declared same-layer clearance",
            clearance,
            rules.min_clearance,
            clearance is not None and clearance >= rules.min_clearance,
            f"closest same-layer pair: {clearance_pair}"
            if clearance is not None and clearance >= rules.min_clearance
            else f"clearance violation at {clearance_pair}",
        ),
        _check(
            "Via annular ring",
            "(via pad - drill)/2 is at least the declared annular ring",
            narrow_ring,
            rules.min_annular_ring,
            narrow_ring is not None and narrow_ring >= rules.min_annular_ring,
            "every via meets the declared annular ring"
            if narrow_ring is not None and narrow_ring >= rules.min_annular_ring
            else "a via has too little copper around the drill",
        ),
        _check(
            "Thermal keep-out",
            "temperature-sensitive parts keep the declared distance from dissipators",
            thermal_gap,
            rules.thermal_keepout,
            thermal_gap is None or thermal_gap >= rules.thermal_keepout,
            "no declared sensitive/dissipator pair is present"
            if thermal_gap is None
            else (
                f"closest sensitive/dissipator pair: {thermal_pair}"
                if thermal_gap >= rules.thermal_keepout
                else f"thermal keep-out violation at {thermal_pair}"
            ),
        ),
        _check(
            "Junction temperature",
            "ambient plus declared dissipation times theta_ja stays below the limit",
            hottest,
            rules.max_junction_temperature,
            hottest <= rules.max_junction_temperature,
            "every declared junction stays below the temperature limit"
            if hottest <= rules.max_junction_temperature
            else "a declared junction exceeds the temperature limit",
        ),
        _check(
            "Stackup",
            "four declared copper layers with positive thickness and a dielectric",
            len(_stackup().layers),
            4,
            len(_stackup().layers) == 4
            and _stackup().total_thickness > 0
            and _stackup().relative_permittivity > 1,
            "declared stackup is structurally consistent",
        ),
    )
    return checks


def build_fabrication(
    plan: physical.PhysicalPlan,
    rules: DRCRules | None = None,
) -> FabricationPlan:
    """Derive declared geometry, DRC, parasitics and thermal rows from a plan."""
    rules = rules or DRCRules()
    if plan.selected is None or plan.selected.binding is None:
        raise CentError(
            ErrorCode.DOMAIN_ERROR,
            "no selected reference design; no fabrication geometry can be derived",
        )
    stage_order = tuple(block.stage for block in plan.layout.blocks)
    placement, rows, cursor = _place(plan.parts, stage_order, rules)

    dissipation = _dissipation(plan)
    footprints: list[Footprint] = []
    for part in plan.parts:
        if part.ref not in placement:
            raise CentError(
                ErrorCode.DOMAIN_ERROR,
                f"part {part.ref!r} was not placed in any declared row",
            )
        x, y, package, stage, row = placement[part.ref]
        power, source = dissipation.get(
            part.ref,
            (
                Fraction(0),
                "no dissipation declared for this ideal or passive component",
            ),
        )
        junction = rules.ambient_temperature + power * package.theta_ja
        footprints.append(
            Footprint(
                ref=part.ref,
                role=part.role,
                package=package,
                stage=stage,
                row=row,
                x=x,
                y=y,
                pads=_pads(part, package, x, y),
                dissipation=power,
                dissipation_source=source,
                junction_temperature=junction,
                note=package.note,
            )
        )

    placement_bottom = cursor
    channel_start = placement_bottom + CHANNEL_GAP
    traces, vias, parasitics, last_y, unrouted = _route(
        plan, tuple(footprints), rules, channel_start
    )

    max_x = max(
        [pad.x + pad.width / 2 for item in footprints for pad in item.pads]
        + [trace.rect[2] for trace in traces]
        + [via.x + via.pad_diameter / 2 for via in vias]
        + [rules.edge_margin + 4]
    )
    width = max_x + rules.edge_margin + CHANNEL_GAP
    height = max(last_y, placement_bottom) + rules.edge_margin + CHANNEL_GAP

    ground_plane = (
        rules.edge_margin,
        rules.edge_margin,
        width - rules.edge_margin,
        height - rules.edge_margin,
    )

    checks = _drc(
        plan,
        tuple(footprints),
        traces,
        vias,
        unrouted,
        width,
        height,
        rules,
    )

    thermal = tuple(
        ThermalPart(
            ref=item.ref,
            stage=item.stage,
            dissipation=item.dissipation,
            theta_ja=item.package.theta_ja,
            ambient=rules.ambient_temperature,
            junction=item.junction_temperature,
            sensitive=item.ref in SENSITIVE_REFS,
            source=item.dissipation_source,
        )
        for item in footprints
    )

    gaps = (
        "Footprints are declared generic land patterns, not manufacturer drawings or vendor land patterns; pad, solder-mask and paste geometry are not DFM-verified.",
        "The router is a fixed orthogonal escape/bus scheme on two signal layers with an inset ground plane; it is not a placement or routing optimiser and has not been manufactured.",
        "DRC checks the generated copper against only the declared clearance, width, edge, annular-ring, keep-out and junction-temperature rules.",
        "Parasitics are lumped first-order R/C estimates from declared resistivity and permittivity, plus a declared per-unit-length inductance; there is no field solve, fringing, skin effect, temperature coefficient or mutual coupling.",
        "The thermal model is a single-node junction-to-ambient rise from declared dissipation and theta_ja; there is no thermal spreading, package coupling, transient heating or measured thermal resistance.",
        "Ideal behavioral blocks declare zero dissipation and have no vendor package, bond wire, solder joint, ESD, reliability or assembly model.",
        "No panelisation, impedance control, stackup tolerance, yield analysis, EMC, safety or fabrication sign-off is claimed.",
    )

    return FabricationPlan(
        physical=plan,
        rules=rules,
        stackup=_stackup(),
        width=width,
        height=height,
        rows=rows,
        footprints=tuple(footprints),
        traces=traces,
        vias=vias,
        unrouted=unrouted,
        parasitics=parasitics,
        thermal=thermal,
        ground_plane=ground_plane,
        checks=checks,
        gaps=gaps,
    )


def emit_fabrication(
    route_name: str,
    *,
    input_value: Any | None = None,
    input_min: Any | None = None,
    input_max: Any | None = None,
    accuracy: Any = "1/100",
    max_cost: Any | None = None,
    min_bandwidth: Any | None = None,
    rules: DRCRules | None = None,
) -> FabricationPlan:
    """Solve the declared design, emit its reference topology, then its geometry."""
    plan = physical.emit_physical(
        route_name,
        input_value=input_value,
        input_min=input_min,
        input_max=input_max,
        accuracy=accuracy,
        max_cost=max_cost,
        min_bandwidth=min_bandwidth,
    )
    return build_fabrication(plan, rules)


__all__ = [
    "COPPER_RESISTIVITY",
    "COPPER_THICKNESS",
    "DIELECTRIC_THICKNESS",
    "DRCRules",
    "EPSILON_0",
    "FabricationCheck",
    "FabricationPlan",
    "Footprint",
    "Layer",
    "NetParasitics",
    "PACKAGES",
    "Package",
    "Pad",
    "RELATIVE_PERMITTIVITY",
    "Row",
    "SCHEMA",
    "SENSITIVE_REFS",
    "Stackup",
    "ThermalPart",
    "TraceSegment",
    "UNITS",
    "Via",
    "build_fabrication",
    "emit_fabrication",
]
