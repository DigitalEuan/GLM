"""Declared typed bridges from method ports to wheel quantities.

A text match in ``wheels/*.json`` is only a candidate for grounding.  This
module turns a match into a *declared* mapping only when a bridge law exists and
the wheels' SI dimension vectors agree with the bridge's expected dimensions.

The bridge is deliberately not an axiom proof, a semantic identity or a
fabrication netlist.  It records the port/quantity correspondence, the exact
dimension residual and the remaining limits so discovery can keep those claims
separate from evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping

AXES = ("L", "M", "T", "I", "H", "N", "J", "A")


def _dimension(**exponents: int) -> tuple[Fraction, ...]:
    return tuple(Fraction(exponents.get(axis, 0)) for axis in AXES)


CURRENT = _dimension(I=1)
VOLTAGE = _dimension(L=2, M=1, T=-3, I=-1)


@dataclass(frozen=True)
class PortBridge:
    """A route port mapped through a device quantity to a wheel quantity."""

    method_port: str
    device_symbol: str
    wheel_quantity: str
    unit: str
    expected_dimension: tuple[Fraction, ...]
    note: str


@dataclass(frozen=True)
class QuantityBridge:
    """A declared device quantity used by a bridge but not a route port."""

    device_symbol: str
    wheel_quantity: str
    unit: str
    expected_dimension: tuple[Fraction, ...]
    note: str


@dataclass(frozen=True)
class WheelBridgeSpec:
    """A declared bridge law for one primitive/route family and wheel."""

    id: str
    primitive: str
    wheel: str
    route_kind: str | None
    name: str
    law: str
    ports: tuple[PortBridge, ...]
    quantities: tuple[QuantityBridge, ...]
    notes: tuple[str, ...]


# The first bridge is intentionally narrow: the log-domain square root is a
# diode law, and W24 supplies the exact semiconductor quantities.  A bridge
# that merely shares a word or a dimension is not added here.
WHEEL_BRIDGES: tuple[WheelBridgeSpec, ...] = (
    WheelBridgeSpec(
        id="log-domain-diode-w24",
        primitive="sqrt",
        wheel="W24",
        route_kind="certified-enclosure",
        name="Log-domain square root ↔ semiconductor diode wheel",
        law=(
            "I_in = I_ref*x; I_out = I_s*root; "
            "V_T = k_B*T/q; I_out = I_s*exp((1/2)*ln(I_in/I_s)); "
            "V_out = R_out*I_out"
        ),
        ports=(
            PortBridge(
                "x",
                "I_in",
                "current",
                "A",
                CURRENT,
                "normalized input maps to the diode input current I_in = I_ref*x",
            ),
            PortBridge(
                "root",
                "I_out",
                "current",
                "A",
                CURRENT,
                "normalized root maps to the antilog current I_out = I_s*root",
            ),
        ),
        quantities=(
            QuantityBridge(
                "V_T",
                "thermal_voltage",
                "V",
                VOLTAGE,
                "thermal voltage sets the diode slope",
            ),
            QuantityBridge(
                "I_s",
                "saturation_current",
                "A",
                CURRENT,
                "saturation current sets the antilog scale",
            ),
        ),
        notes=(
            "The bridge is dimensional and semantic for the declared diode law; it is not an axiom proof.",
            "The route's physical output voltage V_out = R_out*I_out is a derived quantity, not a separate W24 quantity.",
        ),
    ),
)


def _dimension_json(dimension: tuple[Fraction, ...]) -> dict[str, str]:
    return {
        axis: str(value)
        for axis, value in zip(AXES, dimension)
        if value != 0
    }


def _dimension_text(dimension: tuple[Fraction, ...]) -> str:
    parts = [
        axis if value == 1 else f"{axis}^{value}"
        for axis, value in zip(AXES, dimension)
        if value != 0
    ]
    return " ".join(parts) if parts else "1"


def _wheel_dimension(
    wheel_doc: Mapping[str, Any], quantity: str
) -> tuple[Fraction, ...] | None:
    item = (wheel_doc.get("dimensions") or {}).get(quantity)
    if not isinstance(item, Mapping):
        return None
    axes = tuple(item.get("axes") or ())
    exponents = item.get("exponents")
    if axes != AXES or not isinstance(exponents, list) or len(exponents) != len(AXES):
        return None
    try:
        return tuple(Fraction(value) for value in exponents)
    except (TypeError, ValueError):
        return None


def _residual(
    actual: tuple[Fraction, ...], expected: tuple[Fraction, ...]
) -> list[dict[str, str]]:
    if len(actual) != len(expected):
        return [{"axis": "*", "wheel": "?", "expected": "?", "residual": "?"}]
    return [
        {
            "axis": axis,
            "wheel": str(wheel),
            "expected": str(want),
            "residual": str(wheel - want),
        }
        for axis, wheel, want in zip(AXES, actual, expected)
        if wheel != want
    ]


def _require_mapping(method: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    route = method.get("route_model") or {}
    binding = method.get("device_binding") or {}
    ports = {str(item.get("name")): item for item in route.get("ports", ())}
    quantities = {
        str(item.get("symbol")): item
        for item in binding.get("quantities", ())
        if isinstance(item, Mapping)
    }
    return route, ports, quantities


def evaluate_bridge(
    method: Mapping[str, Any],
    bridge: WheelBridgeSpec,
    wheel_doc: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate one declared bridge against a method and a wheel document.

    The residual is computed from the wheel's own SI exponent vector and the
    bridge's independently declared expectation.  A missing route port, device
    quantity, unit or wheel dimension is a gap, never an inferred pass.
    """
    route, route_ports, device_quantities = _require_mapping(method)
    route_kind = str(route.get("kind") or "")
    problems: list[str] = []
    if route_kind != bridge.route_kind:
        problems.append(
            f"route kind {route_kind or '(none)'} does not match declared {bridge.route_kind}"
        )

    port_rows: list[dict[str, Any]] = []
    residuals: list[dict[str, str]] = []
    for mapping in bridge.ports:
        route_port = route_ports.get(mapping.method_port)
        device = device_quantities.get(mapping.device_symbol)
        wheel_dim = _wheel_dimension(wheel_doc, mapping.wheel_quantity)
        row_problems: list[str] = []
        if route_port is None:
            row_problems.append(f"route has no port {mapping.method_port!r}")
        if device is None:
            row_problems.append(f"device binding has no quantity {mapping.device_symbol!r}")
        if wheel_dim is None:
            row_problems.append(
                f"wheel {bridge.wheel} has no usable dimension for {mapping.wheel_quantity!r}"
            )
        if device is not None and str(device.get("unit")) != mapping.unit:
            row_problems.append(
                f"{mapping.device_symbol} unit {device.get('unit')!r} != {mapping.unit!r}"
            )
        row_residual = (
            _residual(wheel_dim, mapping.expected_dimension)
            if wheel_dim is not None
            else []
        )
        if row_residual:
            row_problems.append(
                f"dimension residual for {mapping.wheel_quantity}: {row_residual}"
            )
        if row_problems:
            problems.extend(row_problems)
        residuals.extend(row_residual)
        port_rows.append(
            {
                "status": "pass" if not row_problems else "gap",
                "method_port": mapping.method_port,
                "direction": route_port.get("direction") if route_port else None,
                "device_symbol": mapping.device_symbol,
                "wheel_quantity": mapping.wheel_quantity,
                "unit": mapping.unit,
                "wheel_dimension": _dimension_json(wheel_dim) if wheel_dim else None,
                "expected_dimension": _dimension_json(mapping.expected_dimension),
                "residual": row_residual,
                "note": mapping.note,
                "problems": row_problems,
            }
        )

    quantity_rows: list[dict[str, Any]] = []
    for mapping in bridge.quantities:
        device = device_quantities.get(mapping.device_symbol)
        wheel_dim = _wheel_dimension(wheel_doc, mapping.wheel_quantity)
        row_problems: list[str] = []
        if device is None:
            row_problems.append(f"device binding has no quantity {mapping.device_symbol!r}")
        if wheel_dim is None:
            row_problems.append(
                f"wheel {bridge.wheel} has no usable dimension for {mapping.wheel_quantity!r}"
            )
        if device is not None and str(device.get("unit")) != mapping.unit:
            row_problems.append(
                f"{mapping.device_symbol} unit {device.get('unit')!r} != {mapping.unit!r}"
            )
        row_residual = (
            _residual(wheel_dim, mapping.expected_dimension)
            if wheel_dim is not None
            else []
        )
        if row_residual:
            row_problems.append(
                f"dimension residual for {mapping.wheel_quantity}: {row_residual}"
            )
        if row_problems:
            problems.extend(row_problems)
        residuals.extend(row_residual)
        quantity_rows.append(
            {
                "status": "pass" if not row_problems else "gap",
                "device_symbol": mapping.device_symbol,
                "wheel_quantity": mapping.wheel_quantity,
                "unit": mapping.unit,
                "wheel_dimension": _dimension_json(wheel_dim) if wheel_dim else None,
                "expected_dimension": _dimension_json(mapping.expected_dimension),
                "residual": row_residual,
                "note": mapping.note,
                "problems": row_problems,
            }
        )

    declared = not problems and bool(bridge.law.strip())
    return {
        "wheel": bridge.wheel,
        "title": str(wheel_doc.get("title", bridge.wheel)),
        "status": "declared" if declared else "gap",
        "bridge_id": bridge.id,
        "name": bridge.name,
        "bridge_law": bridge.law,
        "ports": port_rows,
        "quantities": quantity_rows,
        "residual": residuals,
        "residual_empty": not residuals,
        "dimension_text": {
            row["method_port"]: _dimension_text(
                tuple(Fraction(str(row["expected_dimension"].get(axis, 0))) for axis in AXES)
            )
            for row in port_rows
        },
        "source": f"declared bridge table; dimensions from wheels/{bridge.wheel}.json",
        "claim": "declared dimensional bridge; not an axiom proof, semantic identity or fabrication netlist",
        "gaps": problems + list(bridge.notes),
    }


def mapping_for_match(
    method: Mapping[str, Any],
    wheel_id: str,
    wheel_doc: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a declared mapping or an explicit gap for one wheel match."""
    route = method.get("route_model") or {}
    route_kind = route.get("kind")
    bridge = next(
        (
            item
            for item in WHEEL_BRIDGES
            if item.primitive == method.get("primitive")
            and item.wheel == wheel_id
            and item.route_kind == route_kind
        ),
        None,
    )
    if bridge is None:
        return {
            "wheel": wheel_id,
            "title": str(wheel_doc.get("title", wheel_id)),
            "status": "gap",
            "bridge_id": None,
            "name": None,
            "bridge_law": None,
            "ports": [],
            "quantities": [],
            "residual": [],
            "residual_empty": True,
            "source": "declared bridge table",
            "claim": "text-level wheel match only; no declared typed bridge",
            "gaps": [
                "no declared bridge law for this primitive/route/wheel combination"
            ],
        }
    return evaluate_bridge(method, bridge, wheel_doc)


__all__ = [
    "AXES",
    "CURRENT",
    "VOLTAGE",
    "PortBridge",
    "QuantityBridge",
    "WheelBridgeSpec",
    "WHEEL_BRIDGES",
    "evaluate_bridge",
    "mapping_for_match",
]
