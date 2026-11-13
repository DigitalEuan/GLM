"""Declared port contracts for the addition/subtraction methods.

The six laboratory methods are not six unrelated physical domains.  Each is a
realization of one of the two exact power-conjugate junction laws already
implemented in :mod:`cent_compiler.port`:

* ``1-junction``: common effort, flows sum.
* ``0-junction``: common flow, efforts sum.

This module adds the *contract* layer: named effort/flow quantities, sign and
reference conventions, transfer law, required parameters and nonideality gaps.
It validates each contract against the exact ``junction_0``/``junction_1``
implementation.  It does not claim a device, calibration or measurement.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from .exact import Q
from .port import PhysicalPort, junction_0, junction_1

SCHEMA = "cent-port-contract/1"
JUNCTIONS = frozenset({"0-junction", "1-junction"})
EVIDENCE_TIER = "computational"


@dataclass(frozen=True)
class PortContract:
    """One declared effort/flow junction contract."""

    id: str
    name: str
    junction: str
    effort: str
    flow: str
    sign_convention: str
    reference: str
    transfer_law: str
    required_parameters: tuple[str, ...]
    nonidealities: tuple[str, ...]
    evidence_tier: str = EVIDENCE_TIER

    def validate(self) -> None:
        if not self.id or not self.name:
            raise ValueError("port contract id and name must be non-empty")
        if self.junction not in JUNCTIONS:
            raise ValueError(f"unknown junction {self.junction!r} for {self.id!r}")
        for field_name, value in (
            ("effort", self.effort),
            ("flow", self.flow),
            ("sign_convention", self.sign_convention),
            ("reference", self.reference),
            ("transfer_law", self.transfer_law),
        ):
            if not value:
                raise ValueError(f"{self.id}: {field_name} must be non-empty")
        if not self.required_parameters:
            raise ValueError(f"{self.id}: required_parameters must not be empty")
        if self.evidence_tier != EVIDENCE_TIER:
            raise ValueError(f"{self.id}: evidence_tier must be {EVIDENCE_TIER!r}")
        _check_junction_power(self)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "id": self.id,
            "name": self.name,
            "junction": self.junction,
            "effort": self.effort,
            "flow": self.flow,
            "sign_convention": self.sign_convention,
            "reference": self.reference,
            "transfer_law": self.transfer_law,
            "required_parameters": list(self.required_parameters),
            "nonidealities": list(self.nonidealities),
            "evidence_tier": self.evidence_tier,
        }


def _q(value: Any) -> Q:
    if isinstance(value, Fraction):
        return value
    return Fraction(str(value))


def _check_junction_power(contract: PortContract) -> None:
    """Exercise the declared junction on exact two-port sample values.

    The check is intentionally independent of the method algebra: it proves
    that the named junction type is the one the port layer actually implements
    and that the sample ports satisfy ``Σ e·f = 0``.
    """
    if contract.junction == "1-junction":
        ports = (
            PhysicalPort(_q("1"), _q("1/2")),
            PhysicalPort(_q("1"), _q("1/3")),
        )
        junction_1(ports)
    else:
        ports = (
            PhysicalPort(_q("1/2"), _q("1")),
            PhysicalPort(_q("1/3"), _q("1")),
        )
        junction_0(ports)


PORT_CONTRACTS: tuple[PortContract, ...] = (
    PortContract(
        id="kcl-node",
        name="KCL node port contract",
        junction="1-junction",
        effort="voltage",
        flow="current",
        sign_convention="positive current into the declared node",
        reference="declared node-voltage reference",
        transfer_law="common node voltage; signed currents sum at the node",
        required_parameters=("source_impedance", "reference"),
        nonidealities=("floating node", "source loading", "compliance", "parasitic loading"),
    ),
    PortContract(
        id="opamp-summing",
        name="op-amp summing amplifier port contract",
        junction="1-junction",
        effort="voltage",
        flow="current",
        sign_convention="positive current into the virtual summing node",
        reference="declared virtual-ground voltage",
        transfer_law="common voltage; input currents sum at the virtual node",
        required_parameters=("r_in", "r_f", "supply"),
        nonidealities=("offset", "bias current", "finite gain", "bandwidth", "slew", "supply rails"),
    ),
    PortContract(
        id="kvl-series",
        name="series voltage-source port contract",
        junction="0-junction",
        effort="voltage",
        flow="current",
        sign_convention="declared source polarity around the series loop",
        reference="declared floating/loop reference",
        transfer_law="common current; source voltages sum around the loop",
        required_parameters=("source_impedance", "source_polarity"),
        nonidealities=("source impedance", "compliance", "loop parasitics", "ground placement"),
    ),
    PortContract(
        id="switched-capacitor",
        name="switched-capacitor charge port contract",
        junction="1-junction",
        effort="voltage",
        flow="current",
        sign_convention="declared non-overlapping charge phases",
        reference="declared capacitor bottom-plate reference",
        transfer_law="common potential; charge/current packets sum on the declared phase",
        required_parameters=("c_a", "c_b", "c_f", "clock_phase"),
        nonidealities=("charge injection", "clock feedthrough", "finite settling", "bottom-plate parasitics"),
    ),
    PortContract(
        id="current-mode",
        name="current-conveyor port contract",
        junction="1-junction",
        effort="voltage",
        flow="current",
        sign_convention="positive current into the low-impedance input node",
        reference="declared conveyor reference",
        transfer_law="common input potential; currents sum and are converted by the transimpedance output",
        required_parameters=("r_f", "input_impedance", "output_impedance"),
        nonidealities=("input/output impedance", "conveyor gain", "offset", "compliance", "noise"),
    ),
    PortContract(
        id="mechanical-force",
        name="force-summing junction port contract",
        junction="0-junction",
        effort="force",
        flow="velocity",
        sign_convention="positive force into the declared junction",
        reference="declared inertial/ground reference",
        transfer_law="common velocity; forces sum at the declared junction",
        required_parameters=("mass", "constraint"),
        nonidealities=("inertia", "compliance", "friction", "load", "geometry"),
    ),
    PortContract(
        id="fluid-reversed",
        name="reversed-flow pipe-junction port contract",
        junction="1-junction",
        effort="pressure",
        flow="volume_flow_rate",
        sign_convention="positive flow into the junction; the B port is declared outflow for subtraction",
        reference="declared downstream/reference pressure",
        transfer_law="common pressure; volumetric flows sum at the junction",
        required_parameters=("pressure_drop", "leakage", "port_direction"),
        nonidealities=("leakage", "compressibility", "junction loss", "pressure/flow scaling", "finite response"),
    ),
    PortContract(
        id="rotational-torque",
        name="rotational torque-summing port contract",
        junction="0-junction",
        effort="torque",
        flow="angular_velocity",
        sign_convention="positive torque into the declared rotor junction",
        reference="declared rotational/inertial reference",
        transfer_law="common angular velocity; torques sum at the declared rotor junction",
        required_parameters=("inertia", "constraint"),
        nonidealities=("inertia", "bearing friction", "torsional compliance", "load", "geometry"),
    ),
)

PORT_CONTRACT_BY_ID = {contract.id: contract for contract in PORT_CONTRACTS}


def validate_port_contracts(
    contracts: tuple[PortContract, ...] = PORT_CONTRACTS,
) -> None:
    """Validate the registry, uniqueness and exact junction sample."""
    ids = [contract.id for contract in contracts]
    if len(set(ids)) != len(ids):
        raise ValueError("port contract ids must be unique")
    for contract in contracts:
        contract.validate()


def get_port_contract(contract_id: str) -> PortContract:
    try:
        return PORT_CONTRACT_BY_ID[str(contract_id)]
    except KeyError as exc:
        known = ", ".join(sorted(PORT_CONTRACT_BY_ID))
        raise KeyError(f"unknown port contract {contract_id!r}; known: {known}") from exc


def coverage_report(method_ids: tuple[str, ...]) -> dict[str, Any]:
    """Report contract coverage for a declared method-id set."""
    missing = [method_id for method_id in method_ids if method_id not in PORT_CONTRACT_BY_ID]
    extra = [contract_id for contract_id in PORT_CONTRACT_BY_ID if contract_id not in method_ids]
    return {
        "schema": "cent-port-coverage/1",
        "method_ids": list(method_ids),
        "contracts": len(PORT_CONTRACTS),
        "missing": missing,
        "extra": extra,
        "complete": not missing,
        "junctions": {
            contract.id: contract.junction for contract in PORT_CONTRACTS
        },
    }


validate_port_contracts()

__all__ = [
    "EVIDENCE_TIER",
    "JUNCTIONS",
    "PORT_CONTRACTS",
    "PORT_CONTRACT_BY_ID",
    "SCHEMA",
    "PortContract",
    "coverage_report",
    "get_port_contract",
    "validate_port_contracts",
]
