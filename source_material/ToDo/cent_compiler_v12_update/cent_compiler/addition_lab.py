"""Ideal-law laboratory for alternative addition and subtraction methods.

This module is deliberately separate from the production route and mechanism
registries.  Each method is represented by an exact ``cent-program/1`` model of
its declared ideal law, plus fixed rational vectors and explicit physical gaps.
Passing a vector here means the ideal algebra is internally consistent; it is
not a device, parameter, geometry or measurement result.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping

from .evaluator import run_program
from .exact import q_to_json
from .port_contracts import PORT_CONTRACTS, PORT_CONTRACT_BY_ID, coverage_report
from .program import Instruction, Program, analyse
from .vocabulary import NUMERIC

SCHEMA = "cent-addition-lab/1"
ROUTE_SCHEMA = "cent-addition-lab-route/1"
GLM_EVIDENCE_SCHEMA = "cent-computational-evidence/1"

SUM_VECTORS = (
    (Fraction(1, 2), Fraction(1, 3), Fraction(5, 6)),
    (Fraction(-1, 4), Fraction(1, 6), Fraction(-1, 12)),
    (Fraction(0), Fraction(0), Fraction(0)),
)
DIFFERENCE_VECTORS = (
    (Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)),
    (Fraction(1, 6), Fraction(1, 2), Fraction(-1, 3)),
    (Fraction(0), Fraction(0), Fraction(0)),
)


@dataclass(frozen=True)
class Stage:
    """One declared ideal stage in a laboratory route."""

    role: str
    op: str
    material: str
    law: str
    inputs: tuple[str, ...]
    output: str
    failure_modes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "op": self.op,
            "material": self.material,
            "law": self.law,
            "inputs": list(self.inputs),
            "output": self.output,
            "failure_modes": list(self.failure_modes),
        }


@dataclass(frozen=True)
class MethodSpec:
    """Declared ideal method and the compiler gates it has not passed."""

    id: str
    name: str
    domain: str
    carrier: str
    sum_material: str
    sum_law: str
    neg_material: str
    neg_law: str
    gaps: tuple[str, ...]
    substrate_status: str
    notes: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain,
            "carrier": self.carrier,
            "substrate_status": self.substrate_status,
            "notes": self.notes,
        }


METHOD_SPECS: tuple[MethodSpec, ...] = (
    MethodSpec(
        id="opamp-summing",
        name="ideal op-amp summing amplifier",
        domain="electrical",
        carrier="voltage",
        sum_material="op-amp summing amplifier with a matched input network",
        sum_law="total = a + b with the declared matched input network and gain",
        neg_material="inverting input network",
        neg_law="neg_b = -b with the declared matched input network",
        gaps=(
            "ideal op-amp and exact resistor ratios only",
            "offset, bias current, finite gain, bandwidth, slew and supply rails are not modeled",
            "no resistor values, source loading, netlist or measured device",
        ),
        substrate_status="absent from DELTA_SUBSTRATE",
        notes=(
            "The sum uses a non-inverting summing amplifier; an inverting summer "
            "plus a unity inverter is an equivalent two-op-amp variant. The "
            "difference form is an inverting input plus summer."
        ),
    ),
    MethodSpec(
        id="kvl-series",
        name="series voltage-source sum",
        domain="electrical",
        carrier="voltage",
        sum_material="series voltage sources in a declared loop",
        sum_law="v_total = v_a + v_b around the declared series loop",
        neg_material="reversed source polarity",
        neg_law="v_neg = -v_b by reversing the declared source polarity",
        gaps=(
            "ideal floating sources and a reference/common-mode convention are not declared",
            "source impedance, compliance, loop parasitics and ground placement are not modeled",
            "no netlist or measured device",
        ),
        substrate_status="DELTA_SUBSTRATE has a generic KVL-loop row, not this route",
        notes="The existing KVL row names a loop and an op-amp summing junction; it is not an assembled route.",
    ),
    MethodSpec(
        id="switched-capacitor",
        name="switched-capacitor charge summer",
        domain="electrical",
        carrier="charge / clocked",
        sum_material="two-phase charge summer",
        sum_law=(
            "total = (Ca*a + Cb*b) / Cf on the declared phase; "
            "Ca = Cb = Cf = 1"
        ),
        neg_material="reversed charge phase",
        neg_law="neg_b = -b by reversing the declared input-capacitor phase",
        gaps=(
            "clock phases, charge injection, feedthrough, finite settling and bottom-plate parasitics are not modeled",
            "capacitor matching, reference and output loading are not declared",
            "no netlist or measured switched-capacitor device",
        ),
        substrate_status="absent from DELTA_SUBSTRATE",
        notes="A charge-domain method; the exact model assumes ideal charge transfer.",
    ),
    MethodSpec(
        id="current-mode",
        name="current-conveyor summing node",
        domain="electrical",
        carrier="current",
        sum_material="low-impedance current-summing node + transimpedance output",
        sum_law="total = Rf*(i_a + i_b) with Rf = 1",
        neg_material="reversed current input",
        neg_law="neg_b = -i_b by reversing the declared input-current direction",
        gaps=(
            "input/output impedance, current-conveyor gain and device offset are not modeled",
            "compliance, bandwidth, noise and source loading are not declared",
            "no netlist or measured device",
        ),
        substrate_status="absent from DELTA_SUBSTRATE",
        notes="Uses KCL but a different device boundary from the existing KCL node route.",
    ),
    MethodSpec(
        id="mechanical-force",
        name="force-summing junction",
        domain="mechanical",
        carrier="force",
        sum_material="declared force-summing junction",
        sum_law="F_total = F_a + F_b at the declared massless/constrained junction",
        neg_material="opposed force input",
        neg_law="F_neg = -F_b by reversing the declared force direction",
        gaps=(
            "the massless/constrained junction is an idealization; mass, inertia, compliance, friction and load are not modeled",
            "force and displacement units, geometry and a mechanical reference are not declared",
            "no fabricated or measured mechanism",
        ),
        substrate_status="DELTA_SUBSTRATE has a rigid-body row, not a force-summing route",
        notes="A rigid body obeys sum(F)=m*a; a force output needs a declared constraint or unit-mass convention.",
    ),
    MethodSpec(
        id="fluid-reversed",
        name="pipe junction with reversed flow port",
        domain="fluidic",
        carrier="normalized volumetric flow",
        sum_material="fluid pipe junction",
        sum_law="q_total = q_a + q_b at the declared flow-conservation junction",
        neg_material="reversed flow port",
        neg_law="q_neg = -q_b by declaring the second port as outflow",
        gaps=(
            "signed-flow and port-direction convention are declared only in the lab",
            "leakage, compressibility, junction loss, pressure/flow scaling and finite response are not modeled",
            "no device binding, netlist or measured flow",
        ),
        substrate_status="DELTA_SUBSTRATE has sum / pipe junction; difference is not declared",
        notes="This is the natural second-domain subtraction candidate: reverse one port, then conserve flow.",
    ),
)

METHOD_BY_ID = {spec.id: spec for spec in METHOD_SPECS}


@dataclass(frozen=True)
class LabRoute:
    """One exact ideal route and its fixed-vector evaluation."""

    id: str
    method: str
    operation: str
    name: str
    domain: str
    carrier: str
    stages: tuple[Stage, ...]
    program: Program
    gaps: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": ROUTE_SCHEMA,
            "id": self.id,
            "method": self.method,
            "operation": self.operation,
            "name": self.name,
            "domain": self.domain,
            "carrier": self.carrier,
            "stages": [stage.as_dict() for stage in self.stages],
            "program": self.program.as_dict(),
            "gaps": list(self.gaps),
        }

    def evaluate(self, a: Fraction, b: Fraction) -> Fraction:
        """Return the exact normalized result of the laboratory program."""
        values = run_program(self.program, [{"a": a, "b": b}])[0]
        return values["total"]

    def simulate(self, a: Fraction, b: Fraction) -> dict[str, Any]:
        result = self.evaluate(a, b)
        expected = a + b if self.operation == "sum" else a - b
        return {
            "a": q_to_json(a),
            "b": q_to_json(b),
            "result": q_to_json(result),
            "expected": q_to_json(expected),
            "passed": result == expected,
        }


def _program(name: str, stages: tuple[Stage, ...]) -> Program:
    instructions = tuple(
        Instruction(stage.op, stage.inputs, stage.output) for stage in stages
    )
    program = Program(
        name=name,
        inputs={"a": NUMERIC, "b": NUMERIC},
        instructions=instructions,
        outputs={"total": "total"},
    )
    analyse(program)
    return program


def _build_route(spec: MethodSpec, operation: str) -> LabRoute:
    if operation == "sum":
        stages = (
            Stage(
                "summer",
                "sum",
                spec.sum_material,
                spec.sum_law,
                ("a", "b"),
                "total",
                ("ideal-law only", "no parameter range declared"),
            ),
        )
    elif operation == "difference":
        stages = (
            Stage(
                "negate",
                "neg",
                spec.neg_material,
                spec.neg_law,
                ("b",),
                "neg_b",
                ("reversal convention only", "no device model"),
            ),
            Stage(
                "summer",
                "sum",
                spec.sum_material,
                f"{spec.sum_law}; total = a + neg_b",
                ("a", "neg_b"),
                "total",
                ("ideal-law only", "no parameter range declared"),
            ),
        )
    else:
        raise ValueError(f"unknown laboratory operation: {operation!r}")

    gaps = (
        *spec.gaps,
        "laboratory route only; not registered in discovery, the operation matrix, transfer or proposals",
        "fixed rational vectors test ideal algebra, not a physical device",
    )
    return LabRoute(
        id=f"{spec.id}-{operation}",
        method=spec.id,
        operation=operation,
        name=f"{spec.name} — {operation}",
        domain=spec.domain,
        carrier=spec.carrier,
        stages=stages,
        program=_program(f"{spec.id}-{operation}", stages),
        gaps=tuple(dict.fromkeys(gaps)),
    )


PROFILE_SCHEMA = "cent-addition-declarations/1"
PROFILE_COMMON_FIELDS = (
    "units",
    "sign_convention",
    "reference",
    "input_range",
    "resolution",
    "source_impedance",
    "load_impedance",
)
PROFILE_METHOD_FIELDS: dict[str, tuple[str, ...]] = {
    "opamp-summing": ("r_in", "r_f", "supply"),
    "kvl-series": ("source_impedance",),
    "switched-capacitor": ("c_a", "c_b", "c_f", "clock_phase"),
    "current-mode": ("r_f", "input_impedance", "output_impedance"),
    "mechanical-force": ("mass", "constraint"),
    "fluid-reversed": ("pressure_drop", "leakage", "port_direction"),
}
EXPECTED_JUNCTION: dict[str, str] = {
    contract.id: contract.junction for contract in PORT_CONTRACTS
}


def _fraction(value: Any, field: str) -> Fraction:
    if isinstance(value, float):
        raise ValueError(f"{field}: use an exact string, not a binary float")
    try:
        return Fraction(str(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{field}: not an exact rational: {value!r}") from exc


def _range(profile: Mapping[str, Any]) -> tuple[Fraction, Fraction]:
    value = profile.get("input_range")
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError("input_range must be an exact [lo, hi] pair")
    lo = _fraction(value[0], "input_range[0]")
    hi = _fraction(value[1], "input_range[1]")
    if lo > hi:
        raise ValueError("input_range must satisfy lo <= hi")
    return lo, hi


def _declared_result(spec: MethodSpec, profile: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one method declaration and run its declared transfer exactly."""
    common_missing = [field for field in PROFILE_COMMON_FIELDS if field not in profile]
    common_errors = []
    try:
        lo, hi = _range(profile)
    except ValueError as exc:
        lo, hi = Fraction(-1), Fraction(1)
        common_errors.append(str(exc))

    cfg = (profile.get("methods") or {}).get(spec.id)
    if not isinstance(cfg, Mapping):
        return {
            "method": spec.id,
            "status": "incomplete-declaration",
            "missing": list(PROFILE_METHOD_FIELDS[spec.id]),
            "common_errors": common_errors,
            "checks": [],
            "gaps": ["no method declaration supplied"],
        }

    missing = [field for field in ("junction", "effort", "flow", "gain", "offset", *PROFILE_METHOD_FIELDS[spec.id]) if field not in cfg]
    checks: list[dict[str, Any]] = []
    gaps: list[str] = []
    checks.append({
        "name": "declaration completeness",
        "status": "pass" if not missing and not common_missing else "gap",
        "detail": "all required fields present" if not missing and not common_missing else "missing: " + ", ".join([*common_missing, *missing]),
    })
    if common_missing or missing:
        gaps.append("declaration is incomplete")

    try:
        gain = _fraction(cfg.get("gain"), "gain")
        offset = _fraction(cfg.get("offset"), "offset")
    except ValueError as exc:
        gain, offset = Fraction(0), Fraction(0)
        checks.append({"name": "exact gain/offset", "status": "gap", "detail": str(exc)})
        gaps.append(str(exc))
    else:
        checks.append({"name": "exact gain/offset", "status": "pass", "detail": f"gain={gain}, offset={offset}"})

    junction = cfg.get("junction")
    expected_junction = EXPECTED_JUNCTION[spec.id]
    checks.append({
        "name": "junction convention",
        "status": "pass" if junction == expected_junction else "gap",
        "detail": f"declared={junction!r}, expected={expected_junction!r}",
    })
    if junction != expected_junction:
        gaps.append(f"{spec.id} must use {expected_junction}")

    exact_operation = gain == 1 and offset == 0
    checks.append({
        "name": "exact addition/subtraction",
        "status": "pass" if exact_operation else "gap",
        "detail": "gain=1 and offset=0" if exact_operation else "declared transfer scales or offsets the operation",
    })
    if not exact_operation:
        gaps.append("declared gain/offset does not realize exact sum or difference")

    all_runs = []
    in_range = True
    vectors_passed = 0
    for operation, vectors in (("sum", SUM_VECTORS), ("difference", DIFFERENCE_VECTORS)):
        route = _build_route(spec, operation)
        for a, b, _ in vectors:
            if not (lo <= a <= hi and lo <= b <= hi):
                in_range = False
            normalized = route.evaluate(a, b)
            result = gain * normalized + offset
            expected = gain * (a + b if operation == "sum" else a - b) + offset
            passed = result == expected
            vectors_passed += int(passed)
            all_runs.append({
                "operation": operation,
                "a": q_to_json(a),
                "b": q_to_json(b),
                "normalized": q_to_json(normalized),
                "result": q_to_json(result),
                "expected": q_to_json(expected),
                "passed": passed,
            })

    checks.append({
        "name": "fixed vectors",
        "status": "pass" if vectors_passed == len(all_runs) else "gap",
        "detail": f"{vectors_passed}/{len(all_runs)} exact declared vectors pass",
    })
    if vectors_passed != len(all_runs):
        gaps.append("one or more declared vectors failed")
    checks.append({
        "name": "input range",
        "status": "pass" if in_range else "gap",
        "detail": f"declared range [{lo}, {hi}]; test vectors {'inside' if in_range else 'outside'}",
    })
    if not in_range:
        gaps.append("test vector outside the declared input range")

    status = "computational-pass" if not gaps and not common_errors else "declared-gap"
    if common_missing or missing:
        status = "incomplete-declaration"
    return {
        "method": spec.id,
        "status": status,
        "junction": junction,
        "effort": cfg.get("effort"),
        "flow": cfg.get("flow"),
        "gain": str(gain),
        "offset": str(offset),
        "missing": [*common_missing, *missing],
        "common_errors": common_errors,
        "checks": checks,
        "vectors": all_runs,
        "gaps": gaps,
    }


def _declared_payload(profile: Mapping[str, Any]) -> dict[str, Any]:
    schema = profile.get("schema")
    schema_error = None if schema == PROFILE_SCHEMA else f"expected schema {PROFILE_SCHEMA!r}, got {schema!r}"
    results = [_declared_result(spec, profile) for spec in METHOD_SPECS]
    return {
        "provided": True,
        "schema": schema,
        "schema_error": schema_error,
        "common_fields": list(PROFILE_COMMON_FIELDS),
        "methods_declared": sum(1 for result in results if result["status"] != "incomplete-declaration"),
        "methods_passed": sum(1 for result in results if result["status"] == "computational-pass"),
        "methods_incomplete": sum(1 for result in results if result["status"] == "incomplete-declaration"),
        "results": results,
    }


def _promotion_gates(spec: MethodSpec) -> list[dict[str, str]]:
    return [
        {"gate": "discovery material row", "status": spec.substrate_status},
        {"gate": "exact route constructor", "status": "laboratory-only"},
        {"gate": "mechanism card", "status": "absent"},
        {"gate": "target adapter / fixed target vectors", "status": "absent"},
    ]


def build_payload(profile: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Run all laboratory routes against their fixed exact vectors.

    ``profile`` is an optional ``cent-addition-declarations/1`` mapping.  It is
    validated and evaluated separately; it never changes the normalized ideal
    routes or promotes a method into the production registries.
    """
    methods = []
    route_count = 0
    vector_count = 0
    routes_passed = 0
    vectors_passed = 0
    for spec in METHOD_SPECS:
        routes = []
        for operation, vectors in (
            ("sum", SUM_VECTORS),
            ("difference", DIFFERENCE_VECTORS),
        ):
            route = _build_route(spec, operation)
            runs = [route.simulate(a, b) for a, b, _ in vectors]
            route_passed = all(run["passed"] for run in runs)
            route_count += 1
            vector_count += len(runs)
            routes_passed += int(route_passed)
            vectors_passed += sum(1 for run in runs if run["passed"])
            routes.append({
                "route": route.as_dict(),
                "vectors": runs,
                "summary": {
                    "vectors": len(runs),
                    "passed": sum(1 for run in runs if run["passed"]),
                    "all_passed": route_passed,
                },
            })
        methods.append({
            **spec.as_dict(),
            "port_contract": PORT_CONTRACT_BY_ID[spec.id].as_dict(),
            "port_model": {
                "junction": EXPECTED_JUNCTION[spec.id],
                "meaning": (
                    "common effort; flows sum"
                    if EXPECTED_JUNCTION[spec.id] == "1-junction"
                    else "common flow; efforts sum"
                ),
            },
            "promotion_gates": _promotion_gates(spec),
            "gaps": list(spec.gaps),
            "routes": routes,
        })

    return {
        "schema": SCHEMA,
        "methods": methods,
        "summary": {
            "methods": len(methods),
            "routes": route_count,
            "vectors": vector_count,
            "routes_passed": routes_passed,
            "vectors_passed": vectors_passed,
            "all_exact_vectors_passed": routes_passed == route_count,
            "port_contracts": len(PORT_CONTRACTS),
            "port_coverage": coverage_report(tuple(spec.id for spec in METHOD_SPECS)),
        },
        "claim": (
            "Ideal exact-law laboratory only. A pass means the declared algebra "
            "matches fixed rational vectors; it is not a device, parameter, "
            "fabrication or measurement result."
        ),
        "compiler_boundary": (
            "These methods are not in DELTA_SUBSTRATE, the operation matrix, the "
            "mechanism registry, transfer retrieval or proposals. Promote one "
            "method at a time after declaring its route and target evidence."
        ),
        "why_not_in_compiler": [
            "discover seeds only DELTA_SUBSTRATE and EXPANSIONS; a method without a material row is never expanded",
            "the operation matrix uses a closed tuple of exact route constructors; a material row alone is not a route",
            "pipeline and transfer dispatch use closed mechanism maps; without a card there is no candidate or proposal",
            "none of these methods has a declared target adapter or fixed target vectors",
        ],
        "declarations": (
            _declared_payload(profile) if profile is not None else {"provided": False}
        ),
    }


def glm_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Wrap a laboratory result as computational evidence for GLM.

    This is deliberately not a target adapter, a GLM call, a model score or a
    physical-transfer candidate.  It exposes only the declared computational
    checks so GLM can consume them without inheriting a physical claim.
    """
    declarations = payload.get("declarations") or {}
    declared_results = declarations.get("results") or []
    methods = []
    if declared_results:
        for result in declared_results:
            methods.append({
                "method": result["method"],
                "status": result["status"],
                "junction": result.get("junction"),
                "effort": result.get("effort"),
                "flow": result.get("flow"),
                "checks": [
                    {"name": check["name"], "status": check["status"]}
                    for check in result.get("checks", ())
                ],
                "gaps": list(result.get("gaps") or ()),
            })
        passed = declarations.get("methods_passed", 0)
    else:
        for method in payload.get("methods", ()):
            methods.append({
                "method": method["id"],
                "status": "computational-pass",
                "junction": (method.get("port_model") or {}).get("junction"),
                "effort": (method.get("port_contract") or {}).get("effort"),
                "flow": (method.get("port_contract") or {}).get("flow"),
                "checks": [],
                "gaps": list(method.get("gaps") or ()),
            })
        passed = len(methods)
    return {
        "schema": GLM_EVIDENCE_SCHEMA,
        "target": "glm",
        "evidence_tier": "computational",
        "physical_transfer": False,
        "glm_call": False,
        "model_score": False,
        "lab_schema": payload.get("schema"),
        "profile_schema": declarations.get("schema"),
        "declared_profile": declarations.get("provided", False),
        "summary": {
            "methods": len(methods),
            "methods_passed": passed,
            "port_contracts": (payload.get("summary") or {}).get("port_contracts", 0),
            "coverage_complete": ((payload.get("summary") or {}).get("port_coverage") or {}).get("complete", False),
        },
        "methods": methods,
        "claim": (
            "Computational evidence only. This is not a GLM call, model score, "
            "target integration, physical transfer, fabrication or measurement."
        ),
    }


def render_glm_evidence(payload: Mapping[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "=" * 78,
        "GLM COMPUTATIONAL EVIDENCE",
        "=" * 78,
        f"schema       {payload['schema']}",
        f"tier         {payload['evidence_tier']}",
        f"physical     {payload['physical_transfer']}",
        f"methods      {summary['methods_passed']}/{summary['methods']}",
        f"contracts    {summary['port_contracts']} (coverage complete: {summary['coverage_complete']})",
        "",
        "This is not a GLM call, model score or physical-transfer claim.",
    ]
    for method in payload["methods"]:
        lines.append(
            f"  {method['method']}: {method['status']} ({method.get('junction', 'no junction')})"
        )
    return "\n".join(lines)


def render_text(payload: Mapping[str, Any]) -> str:
    """Render the laboratory summary for the terminal."""
    summary = payload["summary"]
    lines = [
        "=" * 78,
        "ADDITION / SUBTRACTION METHOD LAB",
        "=" * 78,
        f"{summary['methods']} ideal methods, {summary['routes']} routes, "
        f"{summary['vectors']} exact vectors, {summary['vectors_passed']} passed",
        "",
        "Boundary: ideal algebra only; no device, parameter or measurement claim.",
        "",
    ]
    for method in payload["methods"]:
        port_model = method.get("port_model") or {}
        lines.append(
            f"{method['name']} [{method['domain']}] "
            f"({port_model.get('junction', 'unclassified')}: {port_model.get('meaning', '')})"
        )
        for item in method["routes"]:
            route = item["route"]
            lines.append(
                f"  {route['operation']:<10} {item['summary']['passed']}/"
                f"{item['summary']['vectors']} vectors  "
                f"{'PASS' if item['summary']['all_passed'] else 'FAIL'}  "
                f"{route['id']}"
            )
        lines.append("  promotion gates:")
        for gate in method["promotion_gates"]:
            lines.append(f"    - {gate['gate']}: {gate['status']}")
        lines.append("  first gap: " + method["gaps"][0])
        lines.append("")
    declarations = payload.get("declarations") or {}
    if declarations.get("provided"):
        lines.append("Declared profile")
        lines.append(
            f"  schema: {declarations.get('schema')}  "
            f"declared: {declarations.get('methods_declared')}  "
            f"computational-pass: {declarations.get('methods_passed')}  "
            f"incomplete: {declarations.get('methods_incomplete')}"
        )
        if declarations.get("schema_error"):
            lines.append(f"  schema gap: {declarations['schema_error']}")
        for result in declarations.get("results", ()):
            lines.append(f"  {result['method']}: {result['status']}")
            for check in result.get("checks", ()):
                lines.append(f"    [{check['status']}] {check['name']}: {check['detail']}")
        lines.append("")
    lines.append("Why these are not proposed yet:")
    for reason in payload["why_not_in_compiler"]:
        lines.append(f"  - {reason}")
    lines.append("Nothing above is registered in `cent discover`, `cent matrix` or `cent transfer`.")
    return "\n".join(lines)


__all__ = [
    "DIFFERENCE_VECTORS",
    "GLM_EVIDENCE_SCHEMA",
    "METHOD_BY_ID",
    "METHOD_SPECS",
    "EXPECTED_JUNCTION",
    "PROFILE_SCHEMA",
    "ROUTE_SCHEMA",
    "SCHEMA",
    "SUM_VECTORS",
    "Stage",
    "build_payload",
    "glm_evidence",
    "render_glm_evidence",
    "render_text",
]
