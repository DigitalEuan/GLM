"""Stage-preserving orchestration for the transfer compiler.

This module deliberately does not invent a new synthesis step.  It carries
existing, evidence-labelled results from one stage to the next and records
which stages ran, which produced artifacts, and which are explicit gaps.

A workflow can start from a problem statement, a discovered method id, a
production operation id, or a compiled formula.  Proposal selection still uses
the declared operation contract and mechanism registry; pipeline and machine
stages are selected only when the discovered method has a matching declared
pipeline or route wrapper.  Unsupported stages remain visible gaps rather than
being silently skipped.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import discovery, hypotheses, machine, pipeline, proposal_trial, proposals
from .exact import CentError

SCHEMA = "cent-workflow/1"
MACHINE_ROUTES: dict[str, str] = {
    "sqrt": "sqrt-log",
    "sum": "sum-kcl",
    "quantized_carry": "delta-sigma",
}
_PRIMITIVE_OPERATIONS: dict[str, str] = {
    "sqrt": "sqrt",
    "sum": "sum",
    "mult": "mult",
    "div": "div",
    "exp": "exp",
    "log": "log",
    "recip": "reciprocal",
    "reciprocal": "reciprocal",
}


def _stage(status: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {"status": status, "detail": detail, **extra}


def _method_choice(
    payload: Mapping[str, Any],
    *,
    method_id: str | None,
    operation: str | None,
) -> tuple[dict[str, Any] | None, str]:
    methods = [
        method for method in (payload.get("methods") or ())
        if isinstance(method, Mapping)
    ]
    if method_id:
        selected = next(
            (method for method in methods if method.get("id") == method_id),
            None,
        )
        if selected is None:
            raise ValueError(
                f"method {method_id!r} was not returned by discovery; "
                f"use a method id from the discovery payload"
            )
        if operation and selected.get("primitive") != operation:
            raise ValueError(
                f"method {method_id!r} is for {selected.get('primitive')!r}, "
                f"not {operation!r}"
            )
        return dict(selected), "explicit method id"

    candidates = [
        method for method in methods
        if operation is None or method.get("primitive") == operation
    ]
    if not candidates:
        return None, "no method with a declared operation contract"
    preferred = next(
        (
            method for method in candidates
            if (method.get("route_simulation") or {}).get("passed") is True
        ),
        candidates[0],
    )
    return dict(preferred), "first method with a passing route, else first declared method"


def _operation_from_compile(payload: Mapping[str, Any]) -> str | None:
    transfer = payload.get("transfer")
    if isinstance(transfer, Mapping) and transfer.get("operation"):
        return str(transfer["operation"])
    primitives = {
        str(key)
        for key in ((payload.get("summary") or {}).get("primitives") or {})
    }
    if {"neg", "sum"} <= primitives:
        return "difference"
    for primitive in ("sqrt", "sum", "mult", "div", "exp", "log", "recip", "reciprocal"):
        if primitives == {primitive}:
            return _PRIMITIVE_OPERATIONS[primitive]
    return None


def _pipeline_choice(
    operation: str | None,
    selected_method: Mapping[str, Any] | None,
) -> str | None:
    """Select only a declared exact pipeline that matches the method."""
    if operation is None:
        return None
    method_id = str((selected_method or {}).get("id") or "").lower()
    if method_id:
        if operation == "sqrt":
            if "analog-feedback" in method_id:
                return "sqrt-feedback"
            if "diode" in method_id or "log/antilog" in method_id:
                return "log-domain-sqrt"
            return None
        if operation == "sum":
            if "kcl" in method_id:
                return "sum-kcl"
            if "pipe" in method_id or "fluidic" in method_id:
                return "sum-fluid"
            if "kvl" in method_id or "opamp" in method_id:
                return "sum-opamp"
            return None
    return None


def _machine_choice(
    operation: str | None,
    selected_method: Mapping[str, Any] | None,
) -> str | None:
    """Select only a machine wrapper that matches the discovered method."""
    if operation is None:
        return None
    method_id = str((selected_method or {}).get("id") or "").lower()
    if method_id:
        if operation == "sqrt":
            if "analog-feedback" in method_id:
                return "sqrt-feedback"
            if "diode" in method_id or "log/antilog" in method_id:
                return "sqrt-log"
            return None
        if operation == "sum":
            if "kcl" in method_id:
                return "sum-kcl"
            if "pipe" in method_id or "fluidic" in method_id:
                return "sum-fluid"
            if "kvl" in method_id or "opamp" in method_id:
                return "sum-opamp"
            return None
    return MACHINE_ROUTES.get(str(operation))


def _compile_formula(formula: str, top_n: int) -> dict[str, Any]:
    # Imported lazily: ui imports the report and transfer layers, while the
    # workflow is imported by the CLI after those modules are initialized.
    from . import ui
    return ui.compile_payload(formula, top_n=top_n)


def build_workflow(
    request: str | None = None,
    *,
    formula: str | None = None,
    method_id: str | None = None,
    operation: str | None = None,
    target: str = "glm-reference",
    limit: int = 3,
    top_n: int = 6,
) -> dict[str, Any]:
    """Run the declared stage chain and return a manifest.

    ``method_id`` is only meaningful with a problem request.  ``operation``
    overrides operation inference.  ``formula`` uses ``cent compile`` as the
    front end and therefore also closes the compile-to-proposal handoff.
    """
    if request and formula:
        raise ValueError("provide a problem request or --formula, not both")
    if method_id and formula:
        raise ValueError("--method cannot be combined with --formula")
    if method_id and not request:
        raise ValueError("--method requires a problem request")
    if not request and not formula and not operation:
        raise ValueError("provide a problem request, --formula or --operation")

    discovery_payload: dict[str, Any] | None = None
    compile_payload: dict[str, Any] | None = None
    selected_method: dict[str, Any] | None = None
    selection_reason = "operation supplied directly"

    if formula:
        compile_payload = _compile_formula(formula, top_n)
        operation = operation or _operation_from_compile(compile_payload)
        selection_reason = "operation inferred from compiled formula"
    elif request:
        discovery_payload = discovery.discover(request, limit=max(limit, 20))
        selected_method, selection_reason = _method_choice(
            discovery_payload,
            method_id=method_id,
            operation=operation,
        )
        if operation is None and selected_method is not None:
            operation = selected_method.get("primitive")

    stages: dict[str, dict[str, Any]] = {}
    if discovery_payload is None:
        stages["discover"] = _stage(
            "skip",
            "no problem request was supplied",
        )
    elif discovery_payload.get("matched"):
        stages["discover"] = _stage(
            "pass",
            f"{len(discovery_payload.get('methods') or ())} declared method(s)",
            method_count=len(discovery_payload.get("methods") or ()),
        )
    else:
        stages["discover"] = _stage(
            "gap",
            "the problem statement did not match a declared goal",
        )

    if compile_payload is None:
        stages["compile"] = _stage("skip", "no formula was supplied")
    else:
        stages["compile"] = _stage(
            "pass" if compile_payload.get("ok") else "gap",
            f"compiled {compile_payload.get('relation', formula)}",
            primitives=(compile_payload.get("summary") or {}).get("primitives") or {},
        )

    hypotheses_payload: dict[str, Any] | None = None
    if operation is None:
        stages["hypotheses"] = _stage("skip", "no operation selected")
    else:
        try:
            hypotheses_payload = hypotheses.match_operation(str(operation))
            summary = hypotheses_payload.get("summary") or {}
            leads = int(summary.get("leads", 0))
            pre_admission = int(summary.get("pre_admission", 0))
            stages["hypotheses"] = _stage(
                "gap" if leads or pre_admission else "pass",
                (
                    f"{leads} lead(s), {pre_admission} pre-admission card(s); "
                    "no automatic promotion"
                ),
                leads=leads,
                pre_admission=pre_admission,
                admitted=int(summary.get("admitted", 0)),
            )
        except (KeyError, ValueError) as exc:
            stages["hypotheses"] = _stage("gap", str(exc))

    proposal_payload: dict[str, Any] | None = None
    if operation is None:
        stages["propose"] = _stage(
            "gap",
            "no production operation could be selected",
        )
    else:
        try:
            proposal_payload = proposals.build_bundle(
                str(operation),
                target_id=target,
                limit=limit,
            )
            proposal_payload = proposal_trial.attach_trials(proposal_payload)
            summary = proposal_payload.get("summary") or {}
            trial_summary = proposal_payload.get("trial_summary") or {}
            stages["propose"] = _stage(
                "pass" if proposal_payload.get("ok") else "gap",
                (
                    f"{summary.get('proposals', 0)} proposal(s), "
                    f"{summary.get('ready_for_execution', 0)} ready; "
                    f"trial {trial_summary.get('passed', 0)} passed, "
                    f"{trial_summary.get('not_run', 0)} not run"
                ),
                proposal_count=summary.get("proposals", 0),
                trial=trial_summary,
            )
        except (KeyError, ValueError, CentError) as exc:
            stages["propose"] = _stage("gap", str(exc))

    pipeline_payload: dict[str, Any] | None = None
    pipeline_mechanism = _pipeline_choice(operation, selected_method)
    if operation is None:
        stages["pipeline"] = _stage("skip", "no operation selected")
    elif str(operation) not in pipeline.ROUTES:
        stages["pipeline"] = _stage(
            "gap",
            f"no exact pipeline is declared for {operation!r}",
        )
    elif selected_method and pipeline_mechanism is None:
        stages["pipeline"] = _stage(
            "gap",
            f"no exact pipeline is declared for method {(selected_method or {}).get('id')!r}",
        )
    else:
        try:
            pipeline_payload = pipeline.build_pipeline(
                str(operation), pipeline_mechanism
            )
            stages["pipeline"] = _stage(
                "pass" if pipeline_payload.get("ok") else "gap",
                (
                    f"{len(pipeline_payload.get('stages') or ())} stage(s), "
                    f"{len(pipeline_payload.get('handoffs') or ())} handoff(s)"
                ),
                stage_count=len(pipeline_payload.get("stages") or ()),
                handoff_count=len(pipeline_payload.get("handoffs") or ()),
            )
        except (ValueError, ZeroDivisionError, CentError) as exc:
            stages["pipeline"] = _stage("gap", str(exc))

    machine_payload: dict[str, Any] | None = None
    machine_id = _machine_choice(operation, selected_method)
    if machine_id is None:
        stages["machine"] = _stage(
            "gap",
            (
                f"no declared machine wrapper for {operation!r}"
                + (
                    f" via method {(selected_method or {}).get('id')!r}"
                    if selected_method
                    else ""
                )
            ),
        )
    else:
        try:
            machine_payload = machine.build_machine(
                machine_id,
                target_id=target,
                limit=limit,
            )
            stages["machine"] = _stage(
                "pass" if machine_payload.get("ok") else "gap",
                (
                    f"{machine_id}: "
                    f"{(machine_payload.get('coverage') or {}).get('present_roles', 0)}/"
                    f"{(machine_payload.get('coverage') or {}).get('required_roles', 0)} "
                    "roles; declared branch executed"
                ),
                machine_id=machine_id,
            )
        except (KeyError, ValueError, CentError) as exc:
            stages["machine"] = _stage("gap", str(exc))

    gaps: list[str] = []
    for name, payload in (
        ("discovery", discovery_payload),
        ("compile", compile_payload),
        ("hypotheses", hypotheses_payload),
        ("proposal", proposal_payload),
        ("pipeline", pipeline_payload),
        ("machine", machine_payload),
    ):
        if not payload:
            continue
        for gap in payload.get("gaps") or ():
            text = f"{name}: {gap}"
            if text not in gaps:
                gaps.append(text)
    for name, stage in stages.items():
        if stage["status"] == "gap":
            text = f"{name}: {stage['detail']}"
            if text not in gaps:
                gaps.append(text)

    ok = operation is not None and proposal_payload is not None and bool(
        proposal_payload.get("ok")
    )
    status = "pass" if all(
        stage.get("status") in {"pass", "skip"} for stage in stages.values()
    ) else "partial"
    trial_summary = (proposal_payload or {}).get("trial_summary") or {}
    headline = (
        f"{operation or 'no operation'}; "
        f"{len((proposal_payload or {}).get('proposals') or ())} proposal(s); "
        f"trial {trial_summary.get('passed', 0)} passed; "
        f"machine {machine_id or 'not declared'}."
    )
    return {
        "ok": ok,
        "status": status,
        "schema": SCHEMA,
        "request": request,
        "formula": formula,
        "selection": {
            "operation": operation,
            "method_id": (selected_method or {}).get("id"),
            "method": selected_method,
            "reason": selection_reason,
            "target": target,
        },
        "stages": stages,
        "discovery": discovery_payload,
        "compile": compile_payload,
        "hypotheses": hypotheses_payload,
        "proposal": proposal_payload,
        "pipeline": pipeline_payload,
        "machine": machine_payload,
        "gaps": gaps,
        "headline": headline,
        "claim": (
            "Workflow orchestration preserves declared evidence levels. "
            "Hypothesis leads stay pre-admission; proposals come from the "
            "declared mechanism registry. A passing stage is not a fabricated, "
            "measured or independently validated device; gaps remain gaps."
        ),
        "artifacts": {},
    }


def render_workflow(payload: Mapping[str, Any]) -> str:
    lines = ["=" * 78, "CENT WORKFLOW", "=" * 78]
    lines.append(f"status: {payload.get('status', '?')} · " + str(payload.get("headline") or ""))
    selection = payload.get("selection") or {}
    lines.append(
        f"operation: {selection.get('operation') or 'none'} · "
        f"target: {selection.get('target')} · "
        f"method: {selection.get('method_id') or 'direct operation'}"
    )
    lines.append("")
    lines.append("STAGES")
    for name, stage in (payload.get("stages") or {}).items():
        lines.append(f"  [{stage.get('status', '?'):<4}] {name}: {stage.get('detail', '')}")
    if payload.get("artifacts"):
        lines.append("")
        lines.append("ARTIFACTS")
        for name, path in (payload.get("artifacts") or {}).items():
            lines.append(f"  {name}: {path}")
    lines.append("")
    lines.append("GAPS")
    for gap in payload.get("gaps") or ():
        lines.append(f"  - {gap}")
    lines.append("")
    lines.append(str(payload.get("claim") or ""))
    return "\n".join(lines)


def write_workflow(payload: dict[str, Any], directory: str | Path) -> list[Path]:
    """Write the workflow manifest and every stage artifact it produced."""
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    def write_json(name: str, value: Mapping[str, Any]) -> Path:
        path = root / name
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        paths[name] = name
        return path

    written: list[Path] = []
    if payload.get("discovery") is not None:
        written.append(write_json("discovery.json", payload["discovery"]))
    if payload.get("compile") is not None:
        written.append(write_json("compile.json", payload["compile"]))
    if payload.get("hypotheses") is not None:
        written.append(write_json("hypotheses.json", payload["hypotheses"]))
    if payload.get("pipeline") is not None:
        written.append(write_json("pipeline.json", payload["pipeline"]))
    if payload.get("proposal") is not None:
        proposal_paths = proposals.write_bundle(payload["proposal"], root / "proposals")
        paths["proposals"] = "proposals/"
        written.extend(proposal_paths)
    if payload.get("machine") is not None:
        machine_paths = machine.write_machine(payload["machine"], root / "machine")
        paths["machine"] = "machine/"
        written.extend(machine_paths)

    paths["workflow.json"] = "workflow.json"
    paths["workflow.md"] = "workflow.md"
    payload["artifacts"] = paths
    manifest = write_json("workflow.json", payload)
    written.append(manifest)
    markdown = root / "workflow.md"
    markdown.write_text(
        "# Cent workflow\n\n```text\n" + render_workflow(payload) + "\n```\n",
        encoding="utf-8",
    )
    written.append(markdown)
    return written


__all__ = [
    "SCHEMA",
    "MACHINE_ROUTES",
    "build_workflow",
    "render_workflow",
    "write_workflow",
]
