"""Typed contracts for the declared physical-material rows.

The legacy ``EXPANSIONS`` and ``DELTA_SUBSTRATE`` tables remain as compact
indexes for discovery.  Every row resolves through one of these contracts so
graph and proof layers can consume typed ports, parameters, laws and explicit
failure modes instead of parsing prose.  The contracts do not add measured
behavior: ranges and failures describe the declared material model only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

SCHEMA = "cent-material-contract/1"


@dataclass(frozen=True)
class MaterialPort:
    """One typed port on a material implementation."""

    name: str
    direction: str
    kind: str
    domain: str
    description: str

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "direction": self.direction,
            "kind": self.kind,
            "domain": self.domain,
            "description": self.description,
        }


@dataclass(frozen=True)
class MaterialParameter:
    """A declared material parameter, without inventing a measured value."""

    name: str
    kind: str
    operating_range: str
    description: str

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "kind": self.kind,
            "operating_range": self.operating_range,
            "description": self.description,
        }


@dataclass(frozen=True)
class MaterialContract:
    """A typed view of one expansion or substrate material row."""

    key: str
    kind: str
    primitive: str
    component: str
    domain: str
    carrier: str
    ports: tuple[MaterialPort, ...]
    parameters: tuple[MaterialParameter, ...]
    law: str
    operating_range: str
    failure_modes: tuple[str, ...]
    description: str
    source: str
    expands_to: tuple[str, ...] = ()
    delta_sigma: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "key": self.key,
            "kind": self.kind,
            "primitive": self.primitive,
            "component": self.component,
            "domain": self.domain,
            "carrier": self.carrier,
            "ports": [port.as_dict() for port in self.ports],
            "parameters": [parameter.as_dict() for parameter in self.parameters],
            "law": self.law,
            "operating_range": self.operating_range,
            "failure_modes": list(self.failure_modes),
            "description": self.description,
            "source": self.source,
            "expands_to": list(self.expands_to),
            "delta_sigma": self.delta_sigma,
        }


@dataclass(frozen=True)
class _Interface:
    ports: tuple[MaterialPort, ...]
    parameters: tuple[MaterialParameter, ...]
    operating_range: str
    failure_modes: tuple[str, ...]


def _port(
    name: str,
    direction: str,
    kind: str = "numeric or interval",
    domain: str = "exact rational",
    description: str = "",
) -> MaterialPort:
    return MaterialPort(name, direction, kind, domain, description)


def _param(
    name: str,
    kind: str,
    operating_range: str,
    description: str,
) -> MaterialParameter:
    return MaterialParameter(name, kind, operating_range, description)


def _interface(
    ports: tuple[MaterialPort, ...],
    *,
    parameters: tuple[MaterialParameter, ...] = (),
    operating_range: str,
    failure_modes: tuple[str, ...],
) -> _Interface:
    return _Interface(ports, parameters, operating_range, failure_modes)


_INTERFACES: dict[str, _Interface] = {
    "sum": _interface(
        (_port("a", "input"), _port("b", "input"), _port("sum", "output")),
        operating_range="exact rational or certified interval; at least one input",
        failure_modes=("floating node", "source loading", "compliance limit"),
    ),
    "mult": _interface(
        (
            _port("a", "input"),
            _port("b", "input"),
            _port("product", "output"),
        ),
        parameters=(
            _param("gain", "rational", "any exact rational", "declared multiplier gain"),
        ),
        operating_range="both inputs inside the declared linear multiplication range",
        failure_modes=("nonlinearity", "input offset", "feedthrough", "finite bandwidth"),
    ),
    "scale": _interface(
        (_port("x", "input"), _port("y", "output")),
        parameters=(
            _param("factor", "rational", "any exact rational", "fixed declared gain"),
        ),
        operating_range="exact rational or certified interval input",
        failure_modes=("gain error", "input offset", "finite gain-bandwidth"),
    ),
    "accum": _interface(
        (_port("x", "input"), _port("y", "output")),
        operating_range="exact rational or interval input; state bound declared by the route",
        failure_modes=("leakage", "offset accumulation", "state saturation"),
    ),
    "rate": _interface(
        (_port("x", "input"), _port("y", "output")),
        parameters=(
            _param("dt", "rational", "dt > 0", "declared sampling interval"),
        ),
        operating_range="dt > 0; exact rational input samples",
        failure_modes=("noise amplification", "finite bandwidth", "sampling skew"),
    ),
    "wrap": _interface(
        (_port("x", "input"), _port("y", "output")),
        parameters=(
            _param("period", "rational", "period > 0", "declared wrap period"),
        ),
        operating_range="period > 0; exact scalar input inside the declared phase range",
        failure_modes=("phase ambiguity", "wrap discontinuity", "calibration drift"),
    ),
    "spatial": _interface(
        (_port("x", "input"), _port("y", "output")),
        operating_range="declared spatial carrier; measured geometry is not attached",
        failure_modes=("boundary effects", "geometry tolerance", "calibration drift"),
    ),
    "sqrt": _interface(
        (_port("x", "input"), _port("root", "output")),
        operating_range="declared real square-root domain; branch choice remains explicit",
        failure_modes=("domain error", "branch ambiguity", "nonlinearity"),
    ),
    "eq": _interface(
        (_port("residual", "input"), _port("root", "output")),
        operating_range="declared monotone bracket or stable equilibrium region",
        failure_modes=("false equilibrium", "instability", "offset"),
    ),
    "quantize": _interface(
        (_port("signal", "input"), _port("level", "output")),
        parameters=(
            _param("quantum", "rational", "quantum > 0", "distance between levels"),
            _param(
                "full_scale",
                "rational",
                "full_scale >= quantum",
                "largest declared output level",
            ),
        ),
        operating_range="quantum > 0 and full_scale >= quantum",
        failure_modes=("comparator offset", "metastability", "reference-ladder mismatch"),
    ),
    "delay": _interface(
        (_port("x", "input"), _port("y", "output")),
        parameters=(
            _param("ticks", "integer", "ticks >= 1", "delay length in ticks"),
            _param("initial", "rational", "any exact rational", "first-tick output"),
        ),
        operating_range="ticks >= 1; exact rational samples",
        failure_modes=("clock feedthrough", "aperture jitter", "metastability"),
    ),
    "div": _interface(
        (
            _port("a", "input"),
            _port("b", "input", description="denominator"),
            _port("quotient", "output"),
        ),
        operating_range="denominator non-zero; declared operating region",
        failure_modes=("divide-by-zero", "nonlinearity", "input offset"),
    ),
    "recip": _interface(
        (_port("x", "input"), _port("reciprocal", "output")),
        operating_range="x non-zero; declared operating region",
        failure_modes=("zero crossing", "nonlinearity", "finite gain"),
    ),
    "exp": _interface(
        (_port("x", "input"), _port("y", "output")),
        operating_range="declared exponential region; result must stay finite",
        failure_modes=("thermal drift", "junction ideality", "saturation"),
    ),
    "log": _interface(
        (_port("x", "input"), _port("y", "output")),
        operating_range="x > 0; declared logarithmic region",
        failure_modes=("thermal drift", "junction ideality", "offset"),
    ),
    "sat": _interface(
        (_port("x", "input"), _port("y", "output")),
        operating_range="declared input and output rails",
        failure_modes=("rail sticking", "recovery delay", "threshold drift"),
    ),
    "hysteresis": _interface(
        (_port("x", "input"), _port("y", "output")),
        operating_range="declared thresholds and retained state",
        failure_modes=("threshold drift", "state loss", "switching variability"),
    ),
    "grad": _interface(
        (_port("field", "input"), _port("gradient", "output")),
        operating_range="declared field domain and spacing",
        failure_modes=("discretization error", "boundary effect", "sensor offset"),
    ),
    "translinear": _interface(
        (
            _port("a", "input"),
            _port("b", "input"),
            _port("power", "output"),
        ),
        operating_range="declared translinear operating region",
        failure_modes=("thermal drift", "device mismatch", "range limitation"),
    ),
}

_FALLBACK = _interface(
    (_port("x", "input"), _port("y", "output")),
    operating_range="declared material behavior only; no measured range is attached",
    failure_modes=("not characterized", "measurement gap"),
)

_DOMAIN_FAILURES: dict[str, tuple[str, ...]] = {
    "electrical": ("parasitic loading", "thermal drift"),
    "electromechanical": ("back-EMF", "commutation loss"),
    "mechanical": ("friction and backlash", "elastic deformation"),
    "rotational": ("bearing friction", "unbalance"),
    "fluid": ("leakage", "viscous loss"),
    "fluidic": ("leakage", "viscous loss"),
    "thermal": ("thermal lag", "convection uncertainty"),
    "optical": ("alignment drift", "dispersion"),
    "digital": ("clock jitter", "metastability"),
    "bio-chemical": ("temperature sensitivity", "reagent drift"),
    "spintronics": ("switching variability", "thermal stability"),
    "mixed-signal": ("clock feedthrough", "supply coupling"),
}


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "material"


def material_contract(
    *,
    kind: str,
    primitive: str,
    component: str,
    domain: str,
    carrier: str,
    law: str,
    description: str,
    source: str,
    expands_to: tuple[str, ...] = (),
    delta_sigma: bool = False,
) -> MaterialContract:
    """Build the typed contract for one legacy material row.

    ``law`` is the row's declared governing law for a substrate, or its declared
    behavior statement for an expansion.  It is not a measured transfer
    function.  Missing characterisation stays in ``failure_modes`` and the
    operating range rather than being filled with invented numbers.
    """
    if kind not in ("expansion", "substrate"):
        raise ValueError(f"unknown material contract kind {kind!r}")
    interface = _INTERFACES.get(primitive, _FALLBACK)
    failures = tuple(
        dict.fromkeys(interface.failure_modes + _DOMAIN_FAILURES.get(domain, ()))
    )
    return MaterialContract(
        key=f"{kind}:{primitive}:{_slug(domain)}:{_slug(component)}",
        kind=kind,
        primitive=primitive,
        component=component,
        domain=domain,
        carrier=carrier,
        ports=interface.ports,
        parameters=interface.parameters,
        law=law,
        operating_range=interface.operating_range,
        failure_modes=failures,
        description=description,
        source=source,
        expands_to=expands_to,
        delta_sigma=delta_sigma,
    )


__all__ = [
    "SCHEMA",
    "MaterialContract",
    "MaterialParameter",
    "MaterialPort",
    "material_contract",
]
