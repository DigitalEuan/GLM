"""Computational side-loop for reviewable cross-domain proposals.

A proposal is a reviewable analogy and test plan.  This module runs its declared
target adapter over the adapter's fixed vectors so a reviewer can see what the
proposal actually does before accepting or rejecting it.  A trial is
target-simulated evidence over those fixed vectors; it is not a proof of the
analogy, a general capability result or a measured-device claim.
"""
from __future__ import annotations

import json
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any, Mapping

from . import transfer_validation
from .exact import CentError

TRIAL_SCHEMA = "cent-proposal-trial/1"
BUNDLE_SCHEMA = "cent-proposal-trial-bundle/1"
WHEEL_SCHEMA = "cent-proposal-trial-wheel/1"
PROPOSAL_SCHEMA = "cent-proposal/1"
INDEX_SCHEMA = "cent-proposal-index/1"
CLAIM = (
    "A trial executes only the declared target adapter over its fixed vectors. "
    "It does not prove the behavioral analogy, establish a general capability, "
    "or measure a physical device."
)
WHEEL_CLAIM = (
    "The operation wheel enumerates only the declared operation contracts and "
    "their executable adapters. It is not an exhaustive search over all "
    "computational operations, and an untestable row is a declared gap rather "
    "than a negative capability result."
)


def _first(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def _operation(proposal: Mapping[str, Any]) -> dict[str, Any]:
    value = proposal.get("operation")
    return dict(value) if isinstance(value, Mapping) else {}


def _target(proposal: Mapping[str, Any]) -> dict[str, Any]:
    value = proposal.get("target")
    return dict(value) if isinstance(value, Mapping) else {}


def _mechanism(proposal: Mapping[str, Any]) -> dict[str, Any]:
    value = proposal.get("mechanism")
    return dict(value) if isinstance(value, Mapping) else {}


def _handoff(proposal: Mapping[str, Any]) -> dict[str, Any]:
    value = proposal.get("handoff")
    return dict(value) if isinstance(value, Mapping) else {}


def _proposal_summary(proposal: Mapping[str, Any]) -> dict[str, Any]:
    """State what the proposal applies, where, and which vectors it uses."""
    operation = _operation(proposal)
    target = _target(proposal)
    mechanism = _mechanism(proposal)
    adapter = target.get("adapter")
    adapter_map = adapter if isinstance(adapter, Mapping) else {}
    analogy = proposal.get("analogy")
    analogy_map = analogy if isinstance(analogy, Mapping) else {}
    handoff = _handoff(proposal)
    mapping = [
        str(step.get("law"))
        for step in proposal.get("mapping") or ()
        if isinstance(step, Mapping) and step.get("law")
    ]
    return {
        "operation": operation.get("name") or operation.get("id"),
        "operation_id": operation.get("id"),
        "semantics": operation.get("semantics"),
        "mechanism": mechanism.get("name") or mechanism.get("id"),
        "mechanism_id": mechanism.get("id"),
        "principle": mechanism.get("principle"),
        "source_domains": list(mechanism.get("source_domains") or ()),
        "analogy_basis": list(analogy_map.get("basis") or ()),
        "mapping_laws": mapping,
        "target": target.get("id"),
        "target_adapter": adapter_map.get("invocation"),
        "target_description": adapter_map.get("description"),
        "fixed_vectors": list(handoff.get("fixed_vectors") or ()),
    }


def _what_trial_does(summary: Mapping[str, Any]) -> str:
    return (
        f"Apply {summary.get('mechanism') or 'the selected mechanism'} to "
        f"{summary.get('operation') or 'the selected operation'} on "
        f"{summary.get('target') or 'the target'}; execute "
        f"{len(summary.get('fixed_vectors') or ())} declared fixed "
        "vector(s) and compare the adapter output with the reference result."
    )


def _vector_inputs(row: Mapping[str, Any]) -> dict[str, Any]:
    inputs = row.get("inputs")
    if isinstance(inputs, Mapping):
        return dict(inputs)
    values = {}
    for key in ("x", "input", "a", "b"):
        if key in row:
            values[key] = row[key]
    return values


def _compact_vector(row: Mapping[str, Any]) -> dict[str, Any]:
    target = row.get("target")
    target_map = target if isinstance(target, Mapping) else {}
    source = row.get("source")
    source_map = source if isinstance(source, Mapping) else {}
    source_value = _first(
        source_map, ("result", "root", "mean", "code")
    )
    target_value = _first(
        target_map, ("result", "root", "mean", "code")
    )
    compact = {
        "id": row.get("id"),
        "inputs": _vector_inputs(row),
        "expected": row.get("expected", source_value),
        "actual": target_value,
        "passed": bool(row.get("passed")),
        "checks": dict(row.get("checks") or {}),
    }
    residual = row.get("residual")
    if residual is not None:
        compact["residual"] = residual
    if "code" in target_map:
        compact["actual_code"] = target_map.get("code")
    return compact


def _failed_checks(checks: Any) -> list[str]:
    return [
        str(check.get("name"))
        for check in checks or ()
        if isinstance(check, Mapping) and check.get("status") != "pass"
    ]


def run_trial(proposal: Mapping[str, Any]) -> dict[str, Any]:
    """Execute one proposal's target adapter over its fixed vectors."""
    operation = _operation(proposal)
    target = _target(proposal)
    mechanism = _mechanism(proposal)
    handoff = _handoff(proposal)
    proposal_id = str(proposal.get("id") or "")
    readiness = str(handoff.get("readiness") or "unknown")
    summary = _proposal_summary(proposal)
    base = {
        "schema": TRIAL_SCHEMA,
        "proposal_id": proposal_id,
        "operation": operation.get("id"),
        "target": target.get("id"),
        "mechanism": mechanism.get("id"),
        "readiness": readiness,
        "proposal_summary": summary,
        "what": _what_trial_does(summary),
        "claim": CLAIM,
    }
    if readiness != "ready-for-execution":
        reason = (
            f"proposal is {readiness}; "
            f"{handoff.get('next_action') or 'no executable handoff is declared'}"
        )
        return {
            **base,
            "status": "not-run",
            "reason": reason,
            "verdict": "not executable yet",
            "adjustment": handoff.get("next_action") or reason,
            "metrics": {},
            "vectors": [],
            "checks": [],
            "failed_checks": [],
            "certificate": None,
            "gaps": list(proposal.get("gaps") or ()),
        }

    try:
        validation = transfer_validation.validate_transfer(
            str(operation.get("id") or ""),
            target_id=str(target.get("id") or ""),
            limit=100,
            mechanism_id=str(mechanism.get("id") or ""),
        )
    except (KeyError, ValueError, TypeError, ZeroDivisionError, CentError, OSError) as exc:
        reason = f"trial could not execute: {type(exc).__name__}: {exc}"
        return {
            **base,
            "status": "error",
            "reason": reason,
            "verdict": "trial did not execute",
            "adjustment": "Inspect the target adapter and declared vectors.",
            "metrics": {},
            "vectors": [],
            "checks": [],
            "failed_checks": [],
            "certificate": None,
            "gaps": list(proposal.get("gaps") or ()),
        }

    vectors = [
        _compact_vector(row)
        for row in validation.get("vectors") or ()
        if isinstance(row, Mapping)
    ]
    metrics = dict(validation.get("metrics") or {})
    checks = list(validation.get("checks") or ())
    failed = _failed_checks(checks)
    passed = validation.get("ok") is True
    status = "pass" if passed else "fail"
    if passed:
        verdict = (
            "works on the declared fixed vectors; target-simulated evidence only"
        )
        adjustment = (
            "No adjustment is indicated by these fixed vectors. Keep the "
            "declared target boundary."
        )
    else:
        verdict = "does not meet every declared fixed-vector check"
        adjustment = (
            "Inspect failed checks before adjusting the mapping or adapter: "
            + (", ".join(failed) if failed else "no named failing check")
        )
    return {
        **base,
        "status": status,
        "reason": None if passed else "; ".join(failed) or "trial failed",
        "verdict": verdict,
        "adjustment": adjustment,
        "metrics": metrics,
        "vectors": vectors,
        "checks": checks,
        "failed_checks": failed,
        "certificate": validation.get("certificate"),
        "gaps": list(validation.get("gaps") or ()),
        "evidence_level": (validation.get("certificate") or {}).get(
            "evidence_level"
        ),
    }


def _summarize(trials: list[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "attempted": len(trials),
        "passed": sum(1 for trial in trials if trial.get("status") == "pass"),
        "failed": sum(1 for trial in trials if trial.get("status") == "fail"),
        "not_run": sum(1 for trial in trials if trial.get("status") == "not-run"),
        "errors": sum(1 for trial in trials if trial.get("status") == "error"),
    }


def run_bundle(
    proposals: list[Mapping[str, Any]],
    *,
    proposal_id: str | None = None,
) -> dict[str, Any]:
    """Trial all proposals, or exactly one proposal id, in a bundle."""
    selected = list(proposals)
    if proposal_id is not None:
        selected = [
            proposal for proposal in proposals
            if str(proposal.get("id")) == proposal_id
        ]
        if not selected:
            known = ", ".join(str(proposal.get("id")) for proposal in proposals)
            raise ValueError(
                f"unknown proposal {proposal_id!r}; known: {known}"
            )
    trials = [run_trial(proposal) for proposal in selected]
    summary = _summarize(trials)
    ok = (
        bool(trials)
        and summary["passed"] > 0
        and summary["failed"] == 0
        and summary["errors"] == 0
    )
    return {
        "ok": ok,
        "schema": BUNDLE_SCHEMA,
        "proposal_id": proposal_id,
        "summary": summary,
        "trials": trials,
        "checks": [
            {
                "name": "computational proposal trial",
                "status": "pass" if ok else "gap",
                "detail": (
                    f"{summary['passed']}/{summary['attempted']} selected "
                    "proposal trial(s) pass; no failed or errored trial"
                    if ok
                    else f"{summary['passed']}/{summary['attempted']} "
                    "proposal trial(s) pass"
                ),
            }
        ],
        "headline": (
            f"{summary['passed']}/{summary['attempted']} selected proposal "
            f"trial(s) pass; {summary['failed']} failed, "
            f"{summary['not_run']} not run, {summary['errors']} error(s)."
        ),
        "claim": CLAIM,
    }


def run_wheel(
    *,
    target_id: str = "glm-reference",
    limit: int = 3,
) -> dict[str, Any]:
    """Spin through every declared operation and trial its executable proposals."""
    from . import proposals
    from .transfer_engine import OPERATION_CONTRACTS

    rows = []
    errors = 0
    for contract in OPERATION_CONTRACTS:
        try:
            bundle = proposals.build_bundle(
                contract.id, target_id=target_id, limit=limit
            )
            trial_payload = run_bundle(bundle.get("proposals") or ())
            trials = list(trial_payload.get("trials") or ())
            summary = dict(trial_payload.get("summary") or _summarize(trials))
            reason = None
        except (KeyError, ValueError, TypeError, CentError) as exc:
            trials = []
            summary = _summarize(trials)
            reason = f"{type(exc).__name__}: {exc}"
            errors += 1
        passing = [
            trial for trial in trials if trial.get("status") == "pass"
        ]
        rows.append({
            "operation": contract.id,
            "name": contract.name,
            "semantics": contract.semantics,
            "target": target_id,
            "summary": summary,
            "testable": bool(passing),
            "passing_mechanisms": [
                trial.get("mechanism") for trial in passing
            ],
            "trials": trials,
            "reason": reason,
        })

    all_trials = [trial for row in rows for trial in row["trials"]]
    totals = _summarize(all_trials)
    testable = sum(1 for row in rows if row["testable"])
    untestable = len(rows) - testable
    totals.update({
        "operations": len(rows),
        "testable_operations": testable,
        "untestable_operations": untestable,
        "operation_errors": errors,
    })
    ok = testable > 0 and errors == 0
    return {
        "ok": ok,
        "schema": WHEEL_SCHEMA,
        "target": target_id,
        "limit": limit,
        "summary": totals,
        "operations": rows,
        "checks": [
            {
                "name": "operation wheel coverage",
                "status": "pass" if ok else "gap",
                "detail": (
                    f"{testable}/{len(rows)} declared operation(s) have at "
                    "least one passing adapter trial"
                ),
            }
        ],
        "headline": (
            f"{testable}/{len(rows)} declared operation(s) have at least one "
            f"passing adapter trial; {untestable} have no executable proposal. "
            f"{totals['passed']}/{totals['attempted']} proposal trials pass."
        ),
        "claim": WHEEL_CLAIM,
    }


def _representative(row: Mapping[str, Any]) -> str | None:
    for trial in row.get("trials") or ():
        if trial.get("status") != "pass":
            continue
        vector = next(
            (
                item for item in trial.get("vectors") or ()
                if item.get("passed")
            ),
            None,
        )
        if vector is None:
            continue
        inputs = ", ".join(
            f"{name}={_short(value)}"
            for name, value in (vector.get("inputs") or {}).items()
        )
        return (
            f"{trial.get('mechanism')}: {vector.get('id')} "
            f"{inputs} -> {_short(vector.get('actual'))}"
        )
    return None


def render_wheel(payload: Mapping[str, Any]) -> str:
    """Render the declared-operation trial wheel."""
    summary = payload.get("summary") or {}
    lines = [
        "=" * 78,
        "OPERATION TRIAL WHEEL",
        "=" * 78,
        str(payload.get("headline") or ""),
        "",
    ]
    for row in payload.get("operations") or ():
        row_summary = row.get("summary") or {}
        status = "TESTABLE" if row.get("testable") else "NO ADAPTER"
        lines.append(
            f"{row.get('operation'):<16} {status:<10} "
            f"{row_summary.get('passed', 0)}/{row_summary.get('attempted', 0)} "
            "proposal trial(s) pass"
        )
        if row.get("passing_mechanisms"):
            lines.append(
                "  passing: " + ", ".join(row["passing_mechanisms"])
            )
        representative = _representative(row)
        if representative:
            lines.append(f"  result: {representative}")
        if row.get("reason"):
            lines.append(f"  error: {row['reason']}")
        elif not row.get("testable"):
            reason = next(
                (
                    trial.get("reason")
                    for trial in row.get("trials") or ()
                    if trial.get("reason")
                ),
                "no executable proposal in the retrieved set",
            )
            lines.append(f"  gap: {reason}")
    lines.append("")
    lines.append(
        f"summary: {summary.get('testable_operations', 0)} testable, "
        f"{summary.get('untestable_operations', 0)} without an adapter; "
        f"{summary.get('passed', 0)} passed, {summary.get('failed', 0)} failed, "
        f"{summary.get('not_run', 0)} not run, {summary.get('errors', 0)} error(s)"
    )
    lines.append(str(payload.get("claim") or WHEEL_CLAIM))
    return "\n".join(lines)


def load_bundle(directory: str | Path) -> dict[str, Any]:
    """Load the proposal records named by a saved bundle index."""
    root = Path(directory)
    index_path = root / "index.json"
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read proposal index {index_path}: {exc}") from exc
    if not isinstance(index, Mapping) or index.get("schema") != INDEX_SCHEMA:
        raise ValueError("proposal bundle index has the wrong schema")
    rows = index.get("proposals")
    if not isinstance(rows, list):
        raise ValueError("proposal bundle index has no proposal rows")
    proposals = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("proposal bundle index contains a non-object row")
        file_name = row.get("file")
        if not isinstance(file_name, str) or not file_name:
            raise ValueError("proposal bundle index row has no file")
        path = root / Path(file_name).name
        try:
            proposal = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read proposal {path}: {exc}") from exc
        if not isinstance(proposal, Mapping) or proposal.get("schema") != PROPOSAL_SCHEMA:
            raise ValueError(f"proposal file has the wrong schema: {path}")
        proposals.append(dict(proposal))
    return {
        "operation": index.get("operation"),
        "target": index.get("target"),
        "proposals": proposals,
    }


def run_directory(
    directory: str | Path,
    *,
    proposal_id: str | None = None,
) -> dict[str, Any]:
    """Load a saved bundle and run its computational trial side-loop."""
    bundle = load_bundle(directory)
    payload = run_bundle(bundle["proposals"], proposal_id=proposal_id)
    payload["directory"] = str(directory)
    payload["operation"] = bundle.get("operation")
    payload["target"] = bundle.get("target")
    return payload


def attach_trials(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Attach a trial block to every proposal in a freshly built bundle."""
    payload = dict(bundle)
    proposals = []
    for proposal in bundle.get("proposals") or ():
        row = dict(proposal)
        row["trial"] = run_trial(row)
        proposals.append(row)
    trials = [row["trial"] for row in proposals]
    summary = _summarize(trials)
    trial_ok = (
        summary["attempted"] > 0
        and summary["passed"] > 0
        and summary["failed"] == 0
        and summary["errors"] == 0
    )
    payload["proposals"] = proposals
    payload["trial_summary"] = summary
    payload["checks"] = [
        *(bundle.get("checks") or ()),
        {
            "name": "computational proposal trial",
            "status": "pass" if trial_ok else "gap",
            "detail": (
                f"{summary['passed']}/{summary['attempted']} proposal trial(s) "
                f"pass; {summary['not_run']} not run, "
                f"{summary['failed']} failed, {summary['errors']} error(s)"
            ),
        },
    ]
    return payload


def _short(value: Any) -> str:
    if isinstance(value, Mapping):
        if "num" in value and "den" in value:
            numerator, denominator = str(value["num"]), str(value["den"])
            if len(numerator) <= 18 and len(denominator) <= 18:
                return f"{numerator}/{denominator}"
            try:
                with localcontext() as context:
                    context.prec = 10
                    decimal = Decimal(int(numerator)) / Decimal(int(denominator))
                return f"~{decimal:.8g}"
            except (ArithmeticError, ValueError):
                return f"{numerator[:8]}.../{denominator[:8]}..."
        if "lo" in value and "hi" in value:
            return f"[{_short(value['lo'])}, {_short(value['hi'])}]"
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, (list, tuple)):
        text = ", ".join(_short(item) for item in value)
        return f"[{text}]"
    return str(value)


def render_trial(trial: Mapping[str, Any], prefix: str = "  ") -> list[str]:
    """Render one proposal trial with concrete vector results."""
    status = trial.get("status")
    metrics = trial.get("metrics") or {}
    if status == "not-run":
        lines = [f"{prefix}trial: not-run"]
    else:
        lines = [
            f"{prefix}trial: {status}; "
            f"{metrics.get('passed', 0)}/{metrics.get('vectors', 0)} "
            f"fixed vector(s) pass"
        ]
    summary = trial.get("proposal_summary") or {}
    if summary:
        lines.append(
            f"{prefix}proposal: {summary.get('operation')} — "
            f"{summary.get('semantics')}"
        )
        domains = ", ".join(summary.get("source_domains") or ())
        lines.append(
            f"{prefix}mechanism: {summary.get('mechanism')}"
            + (f" [{summary.get('principle')}]" if summary.get("principle") else "")
            + (f" from {domains}" if domains else "")
        )
        if summary.get("analogy_basis"):
            lines.append(
                f"{prefix}analogy: " + "; ".join(summary["analogy_basis"])
            )
        target_text = f"{prefix}target: {summary.get('target')}"
        if summary.get("target_adapter"):
            target_text += f" — {summary['target_adapter']}"
        lines.append(target_text)
        if trial.get("what"):
            lines.append(f"{prefix}what: {trial['what']}")
    if trial.get("verdict"):
        lines.append(f"{prefix}verdict: {trial['verdict']}")
    if trial.get("adjustment"):
        lines.append(f"{prefix}adjustment: {trial['adjustment']}")
    for vector in trial.get("vectors") or ():
        inputs = vector.get("inputs") or {}
        input_text = ", ".join(
            f"{name}={_short(value)}" for name, value in inputs.items()
        )
        expected = vector.get("expected")
        actual = vector.get("actual")
        line = (
            f"{prefix}  {vector.get('id')}: "
            f"{input_text or 'no declared input'} "
            f"expected={_short(expected)} actual={_short(actual)} "
            f"passed={vector.get('passed')}"
        )
        lines.append(line)
        if vector.get("actual_code") is not None:
            lines.append(
                f"{prefix}    target code: {_short(vector['actual_code'])}"
            )
    if trial.get("failed_checks"):
        lines.append(
            f"{prefix}failed checks: {', '.join(trial['failed_checks'])}"
        )
    return lines


def render_trial_bundle(payload: Mapping[str, Any]) -> str:
    """Render a proposal trial bundle for the terminal."""
    summary = payload.get("summary") or {}
    lines = [
        "=" * 78,
        "COMPUTATIONAL PROPOSAL TRIAL",
        "=" * 78,
        str(payload.get("headline") or ""),
    ]
    for index, trial in enumerate(payload.get("trials") or (), 1):
        lines.append("")
        lines.append(
            f"{index}. {trial.get('proposal_id')} "
            f"[{trial.get('mechanism')} -> {trial.get('target')}]"
        )
        lines.extend(render_trial(trial, prefix="   "))
    lines.append("")
    lines.append(
        f"summary: {summary.get('passed', 0)} passed, "
        f"{summary.get('failed', 0)} failed, "
        f"{summary.get('not_run', 0)} not run, "
        f"{summary.get('errors', 0)} error(s)"
    )
    lines.append(str(payload.get("claim") or CLAIM))
    return "\n".join(lines)


def render_attached_trials(payload: Mapping[str, Any]) -> str:
    """Render trial blocks attached by ``cent propose --trial``."""
    trials = [
        proposal.get("trial")
        for proposal in payload.get("proposals") or ()
        if isinstance(proposal.get("trial"), Mapping)
    ]
    summary = payload.get("trial_summary") or _summarize(trials)
    return render_trial_bundle({
        "headline": (
            f"{summary.get('passed', 0)}/{summary.get('attempted', 0)} "
            f"proposal trial(s) pass; {summary.get('failed', 0)} failed, "
            f"{summary.get('not_run', 0)} not run, "
            f"{summary.get('errors', 0)} error(s)."
        ),
        "summary": summary,
        "trials": trials,
        "claim": CLAIM,
    })


__all__ = [
    "BUNDLE_SCHEMA",
    "CLAIM",
    "TRIAL_SCHEMA",
    "WHEEL_CLAIM",
    "WHEEL_SCHEMA",
    "attach_trials",
    "load_bundle",
    "render_attached_trials",
    "render_trial",
    "render_trial_bundle",
    "render_wheel",
    "run_bundle",
    "run_directory",
    "run_trial",
    "run_wheel",
]
