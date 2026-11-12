"""Executable target validation for transfer candidates.

This module validates one declared candidate against an executable target
adapter and a fixed vector set.  It records exact source/target comparisons, a
uniform-quantizer baseline, bounded-state checks and every remaining boundary in
a ``cent-transfer-certificate/1`` block.

Passing the reference target means *target-simulated*.  Passing the separate
``glm-live`` target means *target-integrated*: the real external GLM CLI ran.  It
does not mean a GLM score, a measured device, a latency or bit-budget result, or
a physical fabrication claim.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

from . import assembly
from .exact import q_from_json, q_to_json
from .mechanisms import MECHANISM_BY_ID
from .targets import glm, glm_live
from .transfer import RelaxationRecord
from .transfer_engine import retrieve

VALIDATION_SCHEMA = "cent-transfer-validation/1"
CERTIFICATE_SCHEMA = "cent-transfer-certificate/1"
ROOT = Path(__file__).resolve().parents[1]

CLAIM = (
    "This certificate covers only the declared exact-rational "
    "glm-reference adapters, fixed vectors, reference-operation budgets and "
    "checks. It is not a real GLM integration, a model score or a "
    "measured-performance result."
)
LIVE_CLAIM = (
    "This certificate records real subprocess executions of the external GLM "
    "CLI for fixed KCL sum/difference vectors. It is not a model score, a "
    "latency or bit-budget measurement, or a general GLM capability claim."
)


def _check(name: str, passed: bool, detail: str = "") -> dict[str, str]:
    return {
        "name": name,
        "status": "pass" if passed else "gap",
        "detail": detail,
    }


def _no_floats(value: Any) -> bool:
    if isinstance(value, float):
        return False
    if isinstance(value, Mapping):
        return all(_no_floats(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_no_floats(item) for item in value)
    return True


def _quantized_vector_result(
    adapter: glm.AdapterSpec,
    vector: glm.GlmVector,
) -> dict[str, Any]:
    route = assembly.delta_sigma_route(
        quantum=vector.quantum,
        full_scale=vector.full_scale,
        integrator_limit=vector.integrator_limit,
    )
    source = route.simulate(vector.x, samples=vector.samples)
    source_code = tuple(
        int(item["level"] / vector.quantum) for item in source.trace
    )
    target = adapter.function(
        vector.x,
        samples=vector.samples,
        quantum=vector.quantum,
        full_scale=vector.full_scale,
        integrator_limit=vector.integrator_limit,
    )
    baseline = glm.uniform_quantizer_carry(
        vector.x,
        samples=vector.samples,
        quantum=vector.quantum,
        full_scale=vector.full_scale,
    )

    source_matches = (
        source_code == vector.expected_code
        and source.mean == vector.expected_mean
        and source.passed
    )
    target_matches = (
        target.code == source_code
        and target.mean == source.mean
        and target.error == source.error
    )
    reconstruction = abs(target.error) <= vector.quantum
    baseline_beats = abs(baseline.error) > abs(target.error)
    bounded = target.bounded and source.range_ok
    levels = int(vector.full_scale / vector.quantum) + 1
    code_width = max(1, (levels - 1).bit_length())
    latency_ok = len(target.code) == vector.samples
    bit_budget_ok = all(0 <= item < levels for item in target.code)
    return {
        "id": vector.id,
        "input": glm.q_to_json(vector.x),
        "samples": vector.samples,
        "quantum": glm.q_to_json(vector.quantum),
        "expected_code": list(vector.expected_code),
        "expected_mean": glm.q_to_json(vector.expected_mean),
        "source": {
            "code": list(source_code),
            "mean": glm.q_to_json(source.mean),
            "error": glm.q_to_json(source.error),
            "peak_state": glm.q_to_json(source.peak_integrator),
            "bounded": source.range_ok,
            "passed": source.passed,
        },
        "target": target.as_dict(),
        "baseline": baseline.as_dict(),
        "budget": {
            "latency_steps": vector.samples,
            "latency_ok": latency_ok,
            "code_levels": levels,
            "code_width_bits": code_width,
            "bit_budget_ok": bit_budget_ok,
            "declared_latency": "samples ticks",
            "declared_bit_budget": "ceil(log2(levels)) bits per code",
        },
        "checks": {
            "source_matches_declared_vector": source_matches,
            "target_matches_source": target_matches,
            "bounded_state": bounded,
            "reconstruction_within_quantum": reconstruction,
            "uniform_quantizer_baseline_is_worse": baseline_beats,
            "latency_within_declared_budget": latency_ok,
            "code_within_declared_bit_budget": bit_budget_ok,
        },
        "margin_over_baseline": glm.q_to_json(
            abs(baseline.error) - abs(target.error)
        ),
        "passed": all(
            (
                source_matches,
                target_matches,
                bounded,
                reconstruction,
                baseline_beats,
                latency_ok,
                bit_budget_ok,
            )
        ),
    }


def _sum_vector_result(
    adapter: glm.AdapterSpec,
    vector: glm.KclVector | glm.FluidVector,
    *,
    fluid: bool = False,
) -> dict[str, Any]:
    if adapter.mechanism == "opamp-summing":
        route = assembly.opamp_sum_route(operation="sum")
    elif fluid:
        route = assembly.fluid_sum_route()
    else:
        route = assembly.kcl_sum_route(operation="sum")
    source = route.simulate(vector.a, vector.b)
    target = adapter.function(vector.a, vector.b)
    swapped = adapter.function(vector.b, vector.a)
    source_matches = source.result == vector.expected and source.passed
    target_matches = (
        target.result == source.result == vector.expected and target.passed
    )
    commutative = swapped.result == target.result and swapped.passed
    return {
        "id": vector.id,
        "a": q_to_json(vector.a),
        "b": q_to_json(vector.b),
        "expected": q_to_json(vector.expected),
        "budget": {
            "latency_steps": 1,
            "latency_ok": True,
            "bit_budget": "exact rational result; no fixed-width limit",
            "bit_budget_declared": True,
        },
        "source": {
            "result": q_to_json(source.result),
            "expected": q_to_json(source.expected),
            "passed": source.passed,
        },
        "target": target.as_dict(),
        "residual": q_to_json(abs(target.result - vector.expected)),
        "checks": {
            "source_matches_declared_vector": source_matches,
            "target_matches_source": target_matches,
            "sum_commutative": commutative,
            "latency_within_declared_budget": True,
            "bit_budget_declared": True,
        },
        "passed": all(
            (source_matches, target_matches, commutative, True, True)
        ),
    }


def _difference_vector_result(
    adapter: glm.AdapterSpec,
    vector: glm.KclVector | glm.FluidVector,
    *,
    fluid: bool = False,
) -> dict[str, Any]:
    if adapter.mechanism == "opamp-summing":
        route = assembly.opamp_sum_route(operation="difference")
    elif fluid:
        route = assembly.fluid_sum_route(operation="difference")
    else:
        route = assembly.kcl_sum_route(operation="difference")
    source = route.simulate(vector.a, vector.b)
    target = adapter.function(vector.a, vector.b)
    swapped = adapter.function(vector.b, vector.a)
    source_matches = source.result == vector.expected and source.passed
    target_matches = (
        target.result == source.result == vector.expected and target.passed
    )
    antisymmetric = swapped.result == -target.result and swapped.passed
    noncommutative = target.result != swapped.result
    return {
        "id": vector.id,
        "a": q_to_json(vector.a),
        "b": q_to_json(vector.b),
        "expected": q_to_json(vector.expected),
        "budget": {
            "latency_steps": 1,
            "latency_ok": True,
            "bit_budget": "exact rational result; no fixed-width limit",
            "bit_budget_declared": True,
        },
        "source": {
            "result": q_to_json(source.result),
            "expected": q_to_json(source.expected),
            "passed": source.passed,
        },
        "target": target.as_dict(),
        "residual": q_to_json(abs(target.result - vector.expected)),
        "checks": {
            "source_matches_declared_vector": source_matches,
            "target_matches_source": target_matches,
            "difference_antisymmetric": antisymmetric,
            "difference_noncommutative": noncommutative,
            "latency_within_declared_budget": True,
            "bit_budget_declared": True,
        },
        "passed": all(
            (
                source_matches,
                target_matches,
                antisymmetric,
                noncommutative,
                True,
                True,
            )
        ),
    }


def _sqrt_vector_result(
    adapter: glm.AdapterSpec,
    vector: glm.SqrtVector,
) -> dict[str, Any]:
    route = assembly.log_domain_sqrt_route(
        precision=vector.precision, tolerance=vector.tolerance
    )
    source = route.simulate(vector.x)
    target = adapter.function(
        vector.x, precision=vector.precision, tolerance=vector.tolerance
    )
    overlap_lo = max(source.root.lo, target.root.lo)
    overlap_hi = min(source.root.hi, target.root.hi)
    overlap = (
        {"lo": q_to_json(overlap_lo), "hi": q_to_json(overlap_hi)}
        if overlap_lo <= overlap_hi
        else None
    )
    checker_lo = max(target.root.lo, target.checker.lo)
    checker_hi = min(target.root.hi, target.checker.hi)
    source_matches = source.passed
    target_matches = target.passed and checker_lo <= checker_hi
    source_target_overlap = overlap is not None
    within_tolerance = target.root.width <= vector.tolerance
    latency_ok = True
    bit_budget_ok = target.precision == vector.precision
    return {
        "id": vector.id,
        "input": q_to_json(vector.x),
        "precision": vector.precision,
        "tolerance": q_to_json(vector.tolerance),
        "budget": {
            "latency_steps": 1,
            "latency_ok": latency_ok,
            "bit_budget": f"{vector.precision} precision bits per enclosure",
            "bit_budget_ok": bit_budget_ok,
            "declared_latency": "1 route evaluation",
            "declared_bit_budget": "precision bits per enclosure",
        },
        "source": {
            "root": glm._json_value(source.root),
            "checker": glm._json_value(source.checker),
            "width": q_to_json(source.root.width),
            "passed": source.passed,
        },
        "target": target.as_dict(),
        "root": glm._json_value(target.root),
        "overlap": overlap,
        "checks": {
            "source_matches_declared_route": source_matches,
            "target_matches_source": target_matches,
            "source_target_enclosures_overlap": source_target_overlap,
            "target_within_declared_tolerance": within_tolerance,
            "latency_within_declared_budget": latency_ok,
            "bit_budget_declared": bit_budget_ok,
        },
        "passed": all(
            (
                source_matches,
                target_matches,
                source_target_overlap,
                within_tolerance,
                latency_ok,
                bit_budget_ok,
            )
        ),
    }


def _live_vector_result(
    adapter: glm_live.LiveAdapterSpec,
    vector: glm.KclVector,
) -> dict[str, Any]:
    route = assembly.kcl_sum_route(operation=adapter.operation)
    source = route.simulate(vector.a, vector.b)
    target = adapter.function(vector.a, vector.b)
    source_matches = source.result == vector.expected and source.passed
    answered = target.returncode == 0 and target.passed
    target_matches = target.value == source.result == vector.expected
    exact = target.value.denominator > 0
    return {
        "id": vector.id,
        "a": glm.q_to_json(vector.a),
        "b": glm.q_to_json(vector.b),
        "expected": glm.q_to_json(vector.expected),
        "transport": {
            "kind": "glm-cli-subprocess",
            "cli": target.cli,
            "query": target.query,
            "returncode": target.returncode,
        },
        "source": {
            "result": glm.q_to_json(source.result),
            "expected": glm.q_to_json(source.expected),
            "passed": source.passed,
        },
        "target": target.as_dict(),
        "residual": glm.q_to_json(abs(target.value - vector.expected)),
        "checks": {
            "source_matches_declared_vector": source_matches,
            "glm_answered": answered,
            "target_matches_source": target_matches,
            "exact_rational_result": exact,
        },
        "passed": all((source_matches, answered, target_matches, exact)),
    }


def _vector_result(adapter: Any, vector: Any) -> dict[str, Any]:
    if isinstance(adapter, glm_live.LiveAdapterSpec):
        return _live_vector_result(adapter, vector)
    if adapter.operation == "sum":
        return _sum_vector_result(
            adapter, vector, fluid=adapter.kind == "fluid_sum"
        )
    if adapter.operation == "difference":
        return _difference_vector_result(
            adapter, vector, fluid=adapter.kind == "fluid_difference"
        )
    if adapter.operation == "sqrt":
        return _sqrt_vector_result(adapter, vector)
    return _quantized_vector_result(adapter, vector)


def _reviewed_candidate(
    candidate,
    adapter: Any,
    *,
    gaps: tuple[str, ...],
    passed: bool,
    evidence_level: str = "target-simulated",
):
    base_gaps = tuple(
        gap for gap in candidate.gaps if "not implemented" not in gap
    )
    tests = tuple(vector.id for vector in adapter.vectors) if passed else ()
    if passed and candidate.operation in {"sum", "difference"}:
        relaxation = RelaxationRecord(
            classification="exact",
            basis=(
                "exact rational target arithmetic; source and target agree "
                "on the declared normalized domain"
            ),
            evidence_level=evidence_level,
            target=candidate.target,
        )
    elif passed:
        relaxation = RelaxationRecord(
            classification="unclassified",
            basis=(
                "target certificate passes the declared fixed vectors; no "
                "general relaxation class is established"
            ),
            evidence_level=evidence_level,
            target=candidate.target,
        )
    else:
        relaxation = candidate.relaxation
    reviewed = replace(
        candidate,
        status="validated" if passed else "candidate",
        evidence_level=evidence_level if passed else candidate.evidence_level,
        tests=tests,
        artifact=adapter.as_dict() if passed else None,
        gaps=tuple(dict.fromkeys((*base_gaps, *gaps))),
        relaxation=relaxation,
    )
    reviewed.validate(mechanism=MECHANISM_BY_ID[reviewed.mechanism])
    return reviewed


def validate_transfer(
    operation_id: str,
    *,
    target_id: str = glm.TARGET_ID,
    limit: int = 12,
    mechanism_id: str | None = None,
) -> dict[str, Any]:
    """Execute a declared target adapter and emit a pass/fail certificate.

    When ``mechanism_id`` is omitted, the first retrieved candidate with an
    executable adapter is selected.  Retrieval itself remains behavior-ranked;
    this only prevents an unadapted candidate from masking an executable one.
    """
    if target_id not in {glm.TARGET_ID, glm_live.TARGET_ID}:
        raise ValueError(
            f"no executable adapter for target {target_id!r}; "
            f"declared: {glm.TARGET_ID!r}, {glm_live.TARGET_ID!r}"
        )
    operation, target, candidates, _matches = retrieve(
        operation_id, target_id=target_id, limit=limit
    )
    if not candidates:
        raise ValueError(
            f"no retrieved candidate for {operation.id!r} on {target.id!r}"
        )
    def resolve_adapter(candidate):
        if target.id == glm.TARGET_ID:
            return glm.get_adapter(operation.id, candidate.mechanism)
        return glm_live.get_adapter(operation.id, candidate.mechanism)

    if mechanism_id is not None:
        selected = [
            candidate for candidate in candidates
            if candidate.mechanism == mechanism_id
        ]
        if not selected:
            raise ValueError(
                f"candidate {operation.id!r} via {mechanism_id!r} was not retrieved"
            )
        candidate = selected[0]
        try:
            adapter = resolve_adapter(candidate)
        except KeyError as exc:
            raise ValueError(
                f"no executable target adapter for {operation.id!r} via "
                f"{candidate.mechanism!r} on {target.id!r}"
            ) from exc
    else:
        executable = []
        for candidate in candidates:
            try:
                adapter = resolve_adapter(candidate)
            except KeyError:
                continue
            executable.append((candidate, adapter))
        if not executable:
            mechanisms = ", ".join(
                sorted(candidate.mechanism for candidate in candidates)
            )
            raise ValueError(
                f"no executable target adapter for {operation.id!r} on "
                f"{target.id!r}; retrieved mechanisms: {mechanisms}"
            )
        candidate, adapter = executable[0]

    vectors = tuple(_vector_result(adapter, vector) for vector in adapter.vectors)
    all_vectors = all(item["passed"] for item in vectors)
    artifact_path = ROOT / adapter.path
    artifact_ok = artifact_path.exists() and callable(adapter.function)
    operations = set(target.interface.get("operations") or ())
    latency_budget = target.interface.get("latency")
    bit_budget = target.interface.get("bit_budget")
    budgets_declared = (
        isinstance(latency_budget, Mapping)
        and isinstance(bit_budget, Mapping)
        and target.constraints.get("reference_budgets_declared") is True
    )
    live = target.id == glm_live.TARGET_ID
    if live:
        profile_ok = (
            adapter.operation in operations
            and target.constraints.get("real_glm_interface") is True
            and target.constraints.get("subprocess_transport") is True
        )
        contract_detail = (
            "declared live GLM subprocess, exact-rational interface and "
            "unmeasured performance boundary"
        )
    else:
        profile_ok = (
            adapter.operation in operations
            and budgets_declared
            and target.constraints.get("no_real_glm_interface") is True
            and target.constraints.get("no_binary_float") is True
        )
        contract_detail = (
            "declared operations, exact-rational interface, reference budgets "
            "and no-real-GLM boundary"
        )
    exact_json = _no_floats(vectors)
    checks = [
        _check(
            "target contract",
            profile_ok,
            contract_detail,
        ),
        _check(
            "executable adapter",
            artifact_ok,
            f"{adapter.path}:{adapter.entrypoint}",
        ),
    ]
    check_names = tuple(vectors[0]["checks"]) if vectors else ()
    for name in check_names:
        count = sum(1 for item in vectors if item["checks"].get(name))
        checks.append(
            _check(
                name.replace("_", " "),
                count == len(vectors),
                f"{count}/{len(vectors)} fixed vector(s) pass",
            )
        )
    checks.append(
        _check(
            "exact JSON representation",
            exact_json,
            "no binary float appears in the fixed-vector evidence",
        )
    )
    passed = all_vectors and all(item["status"] == "pass" for item in checks)
    if live:
        extra_gaps = (
            "no GLM performance, latency or bit-budget measurement is claimed",
            "only exact KCL sum and difference are wired to the live interface",
            "no general GLM capability or model score is claimed",
        )
    else:
        extra_gaps = (
            "no real GLM interface, model call or runtime integration",
            "reference budgets are operation-local; no external GLM, numerical-backend or hardware budget is connected",
            "no GLM performance improvement or measured target result is claimed",
        )
    gaps = tuple(dict.fromkeys((*target.gaps, *extra_gaps)))
    evidence_level = "target-integrated" if live and passed else "target-simulated"
    reviewed = _reviewed_candidate(
        candidate,
        adapter,
        gaps=gaps,
        passed=passed,
        evidence_level=evidence_level,
    )
    # Keep the metrics exact; the vector rows already carry serialized values.
    metrics = {
        "vectors": len(vectors),
        "passed": sum(1 for item in vectors if item["passed"]),
    }
    if adapter.operation == "quantized_carry":
        metrics.update(
            {
                "max_abs_error": _max_exact(
                    item["target"]["error"] for item in vectors
                ),
                "min_baseline_margin": _min_exact(
                    item["margin_over_baseline"] for item in vectors
                ),
                "max_peak_state": _max_exact(
                    item["target"]["peak_state"] for item in vectors
                ),
            }
        )
    elif adapter.operation in {"sum", "difference"}:
        metrics["max_abs_residual"] = _max_exact(
            item["residual"] for item in vectors
        )
        if live:
            metrics["transport"] = "glm-cli-subprocess"
            metrics["latency"] = "not measured"
            metrics["bit_budget"] = "not measured"
        else:
            metrics["latency_steps"] = 1
            metrics["bit_budget"] = "exact rational; no fixed-width limit"
    elif adapter.operation == "sqrt":
        metrics["max_root_width"] = _max_exact(
            item["target"]["root_width"] for item in vectors
        )
        metrics["max_source_width"] = _max_exact(
            item["source"]["width"] for item in vectors
        )
        metrics["latency_steps"] = 1
        metrics["bit_budget"] = "precision bits per enclosure; exact endpoint rationals"
    certificate = {
        "schema": CERTIFICATE_SCHEMA,
        "subject_schema": VALIDATION_SCHEMA,
        "status": "pass" if passed else "fail",
        "evidence_level": evidence_level if passed else "not established",
        "relaxation": reviewed.relaxation.as_dict(),
        "scope": (
            "live external GLM subprocess execution"
            if live
            else "glm-reference software target simulation"
        ),
        "checks": checks,
        "gaps": list(gaps),
        "claim": LIVE_CLAIM if live else CLAIM,
    }
    return {
        "ok": passed,
        "status": "pass" if passed else "fail",
        "schema": VALIDATION_SCHEMA,
        "operation": operation.as_dict(),
        "target": target.as_dict(),
        "candidate": candidate.as_dict(),
        "validated_candidate": reviewed.as_dict(),
        "artifact": adapter.as_dict(),
        "vectors": vectors,
        "metrics": metrics,
        "checks": checks,
        "gaps": list(gaps),
        "certificate": certificate,
        "headline": (
            f"{adapter.mechanism} -> {target.id}: "
            f"{sum(1 for item in vectors if item['passed'])}/{len(vectors)} "
            f"fixed vectors pass; {evidence_level}."
        ),
    }


def _max_exact(values) -> dict[str, str]:
    parsed = [q_from_json(value) for value in values]
    return q_to_json(max(parsed) if parsed else 0)


def _min_exact(values) -> dict[str, str]:
    parsed = [q_from_json(value) for value in values]
    return q_to_json(min(parsed) if parsed else 0)


def _exact_text(value: Any) -> str:
    try:
        parsed = q_from_json(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{parsed.numerator}/{parsed.denominator}"


def render_validation(payload: Mapping[str, Any]) -> str:
    """Render a transfer validation certificate for the terminal."""
    certificate = payload.get("certificate") or {}
    lines = [
        "=" * 78,
        "TRANSFER TARGET VALIDATION",
        "=" * 78,
        str(payload.get("headline") or ""),
        f"operation: {(payload.get('operation') or {}).get('id')} · "
        f"target: {(payload.get('target') or {}).get('id')}",
        f"artifact: {(payload.get('artifact') or {}).get('path')}:"
        f"{(payload.get('artifact') or {}).get('entrypoint')}",
        f"certificate: {certificate.get('status')} "
        f"({certificate.get('evidence_level')})",
    ]
    interface = (payload.get("target") or {}).get("interface") or {}
    latency = interface.get("latency")
    bit_budget = interface.get("bit_budget")
    if isinstance(latency, Mapping):
        lines.append(
            "latency budget: "
            + "; ".join(f"{key}={value}" for key, value in latency.items())
        )
    if isinstance(bit_budget, Mapping):
        lines.append(
            "bit budget: "
            + "; ".join(f"{key}={value}" for key, value in bit_budget.items())
        )
    lines.extend(("", "Fixed vectors"))
    for item in payload.get("vectors") or ():
        if "a" in item:
            lines.append(
                f"  {item.get('id')}: a={_exact_text(item.get('a'))} "
                f"b={_exact_text(item.get('b'))} "
                f"target_result={_exact_text((item.get('target') or {}).get('result'))} "
                f"residual={_exact_text(item.get('residual'))} "
                f"latency_steps={((item.get('budget') or {}).get('latency_steps'))} "
                f"passed={item.get('passed')}"
            )
        elif "root" in item:
            target_root = (item.get("target") or {}).get("root") or {}
            source_root = (item.get("source") or {}).get("root") or {}
            lines.append(
                f"  {item.get('id')}: x={_exact_text(item.get('input'))} "
                f"source_root=[{_exact_text(source_root.get('lo'))}, "
                f"{_exact_text(source_root.get('hi'))}] "
                f"target_root=[{_exact_text(target_root.get('lo'))}, "
                f"{_exact_text(target_root.get('hi'))}] "
                f"width={_exact_text((item.get('target') or {}).get('root_width'))} "
                f"passed={item.get('passed')}"
            )
        else:
            lines.append(
                f"  {item.get('id')}: x={_exact_text(item.get('input'))} "
                f"samples={item.get('samples')} "
                f"target_mean={_exact_text((item.get('target') or {}).get('mean'))} "
                f"target_error={_exact_text((item.get('target') or {}).get('error'))} "
                f"baseline_error={_exact_text((item.get('baseline') or {}).get('error'))} "
                f"latency_steps={((item.get('budget') or {}).get('latency_steps'))} "
                f"code_width_bits={((item.get('budget') or {}).get('code_width_bits'))} "
                f"passed={item.get('passed')}"
            )
    lines.append("")
    lines.append("Checks")
    for check in payload.get("checks") or ():
        lines.append(f"  [{check.get('status')}] {check.get('name')}: {check.get('detail')}")
    lines.append("")
    lines.append("Remaining gaps")
    for gap in payload.get("gaps") or ():
        lines.append(f"  - {gap}")
    lines.append("")
    lines.append("This is a reference-target certificate, not a GLM integration.")
    return "\n".join(lines)


__all__ = [
    "CERTIFICATE_SCHEMA",
    "VALIDATION_SCHEMA",
    "render_validation",
    "validate_transfer",
]
