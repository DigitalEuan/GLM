"""Reviewable cross-domain transfer proposals.

A proposal is the handoff between retrieval and validation.  It keeps the
operation, mechanism, target, mapping, analogy basis, source tests and target
adapter together, then names exactly what a reviewer can run next.

This module does not validate a target and never claims an isomorphism.  It
classifies the analogy and exposes the first concrete action; the existing
``cent transfer ... --validate`` path remains the only executable certificate.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .mechanisms import MECHANISM_BY_ID
from .targets import glm, glm_live
from .transfer_engine import get_target_profile, retrieve

PROPOSAL_SCHEMA = "cent-proposal/1"
BUNDLE_SCHEMA = "cent-proposal-bundle/1"
INDEX_SCHEMA = "cent-proposal-index/1"
READINESS = frozenset(
    {
        "ready-for-execution",
        "needs-target-adapter",
        "needs-target-vectors",
        "needs-environment",
    }
)
REVIEW_STATE_SCHEMA = "cent-proposal-review-state/1"
REVIEW_EVENT_SCHEMA = "cent-proposal-review-event/1"
REVIEW_LEDGER_SCHEMA = "cent-proposal-review-ledger/1"
REVIEW_SUMMARY_SCHEMA = "cent-proposal-review-summary/1"
REVIEW_LEDGER_FILENAME = "reviews.json"
REVIEW_STATES = frozenset({"accepted", "rejected", "tested"})
REVIEW_CERTIFICATE_BYTES = 1_048_576


def _adapter(target_id: str, operation: str, mechanism: str) -> Any | None:
    try:
        if target_id == glm.TARGET_ID:
            return glm.get_adapter(operation, mechanism)
        if target_id == glm_live.TARGET_ID:
            return glm_live.get_adapter(operation, mechanism)
    except (KeyError, ValueError):
        return None
    return None


def _environment(target_id: str) -> dict[str, Any]:
    if target_id != glm_live.TARGET_ID:
        return {"kind": "in-process", "available": True}
    try:
        path = glm_live.glm_cli_path()
    except glm_live.GLMLiveError as exc:
        return {
            "kind": "external-subprocess",
            "available": False,
            "detail": str(exc),
            "env_var": glm_live.ENV_VAR,
        }
    return {
        "kind": "external-subprocess",
        "available": True,
        "cli": str(path),
        "env_var": glm_live.ENV_VAR,
    }


def _default_review() -> dict[str, Any]:
    return {
        "schema": REVIEW_STATE_SCHEMA,
        "state": "unreviewed",
        "history": [],
    }


def _review_history(events: Any, proposal_id: str) -> list[dict[str, Any]]:
    return [
        dict(event)
        for event in events or ()
        if isinstance(event, Mapping)
        and event.get("proposal_id") == proposal_id
    ]


def _review_block(events: Any, proposal_id: str) -> dict[str, Any]:
    history = _review_history(events, proposal_id)
    return {
        "schema": REVIEW_STATE_SCHEMA,
        "state": history[-1]["state"] if history else "unreviewed",
        "history": history,
    }


def _review_state(ledger: Mapping[str, Any], proposal_id: str) -> str:
    history = _review_history(ledger.get("events"), proposal_id)
    return history[-1]["state"] if history else "unreviewed"


def _review_summary(
    ledger: Mapping[str, Any], proposal_ids: Any = None
) -> dict[str, Any]:
    events = list(ledger.get("events") or ())
    latest: dict[str, str] = {}
    for event in events:
        if isinstance(event, Mapping) and event.get("proposal_id"):
            latest[str(event["proposal_id"])] = str(event.get("state"))
    counts = {state: 0 for state in ("unreviewed", *sorted(REVIEW_STATES))}
    decisions = {state: 0 for state in sorted(REVIEW_STATES)}
    for event in events:
        if isinstance(event, Mapping) and event.get("state") in decisions:
            decisions[str(event["state"])] += 1
    for state in latest.values():
        counts[state] = counts.get(state, 0) + 1
    ids = list(proposal_ids) if proposal_ids is not None else list(latest)
    if proposal_ids is not None:
        counts["unreviewed"] = sum(1 for proposal_id in ids if proposal_id not in latest)
    return {
        "schema": REVIEW_SUMMARY_SCHEMA,
        "events": len(events),
        "states": latest,
        "counts": counts,
        "decisions": decisions,
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_bytes(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_bytes(payload)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _review_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _test_payload(test: Any) -> dict[str, Any]:
    if hasattr(test, "as_dict"):
        return test.as_dict()
    return {
        "id": getattr(test, "id", ""),
        "kind": getattr(test, "kind", ""),
        "inputs": dict(getattr(test, "inputs", {}) or {}),
        "expected": getattr(test, "expected", ""),
        "tolerance": getattr(test, "tolerance", ""),
        "provenance": list(getattr(test, "provenance", ()) or ()),
    }


def _handoff(
    operation: str,
    target_id: str,
    adapter: Any | None,
    environment: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    if adapter is None:
        return (
            "needs-target-adapter",
            {
                "command": None,
                "fixed_vectors": [],
                "next_action": (
                    "Declare a target adapter and fixed vectors for this "
                    "operation and mechanism, then run the target certificate."
                ),
            },
        )
    if not adapter.vectors:
        return (
            "needs-target-vectors",
            {
                "command": None,
                "fixed_vectors": [],
                "next_action": "Declare fixed target vectors before execution.",
            },
        )
    if not environment.get("available", False):
        return (
            "needs-environment",
            {
                "command": (
                    f'python3 cent transfer "{operation}" --target "{target_id}" '
                    f'--mechanism "{adapter.mechanism}" --validate --json'
                ),
                "fixed_vectors": [vector.id for vector in adapter.vectors],
                "next_action": (
                    f"Set {environment.get('env_var', 'the target environment')} "
                    "to a runnable target, then execute the handoff command."
                ),
            },
        )
    return (
        "ready-for-execution",
        {
            "command": (
                f'python3 cent transfer "{operation}" --target "{target_id}" '
                f'--mechanism "{adapter.mechanism}" --validate --json'
            ),
            "fixed_vectors": [vector.id for vector in adapter.vectors],
            "next_action": "Run the handoff command and attach its certificate.",
        },
    )


def _proposal(
    operation,
    target,
    card,
    candidate,
    match: Mapping[str, Any],
    adapter: Any | None,
) -> dict[str, Any]:
    environment = _environment(target.id)
    readiness, handoff = _handoff(operation.id, target.id, adapter, environment)
    if readiness not in READINESS:
        raise ValueError(f"unknown proposal readiness: {readiness!r}")
    source_interface = operation.reference if isinstance(operation.reference, Mapping) else {}
    target_interface = (
        (target.interface.get("interfaces") or {}).get(operation.id) or {}
    )
    mapping = [step.as_dict() for step in candidate.mapping]
    gaps = list(
        dict.fromkeys(
            (
                *candidate.gaps,
                "proposal is a plan, not a target validation",
                "no exact structure-preserving isomorphism is claimed",
            )
        )
    )
    checks = [
        {
            "name": "mechanism support",
            "status": "pass",
            "detail": f"{card.id} declares support for {operation.id}",
        },
        {
            "name": "mapping declared",
            "status": "pass" if mapping else "gap",
            "detail": f"{len(mapping)} mapping step(s)",
        },
        {
            "name": "target adapter",
            "status": "pass" if adapter is not None else "gap",
            "detail": (
                f"{adapter.path}:{adapter.entrypoint}"
                if adapter is not None
                else "no executable adapter for this operation/mechanism"
            ),
        },
        {
            "name": "isomorphism",
            "status": "gap",
            "detail": "analogy only; no exact isomorphism is declared",
        },
    ]
    return {
        "schema": PROPOSAL_SCHEMA,
        "id": f"proposal-{candidate.id}",
        "status": "unvalidated",
        "review": _default_review(),
        "rank": candidate.rank,
        "score": match.get("score"),
        "match_reasons": list(match.get("reasons") or ()),
        "operation": {
            "id": operation.id,
            "name": operation.name,
            "semantics": operation.semantics,
            "reference": dict(source_interface),
            "source_tests": [_test_payload(test) for test in operation.tests],
        },
        "target": {
            "id": target.id,
            "kind": target.kind,
            "interface": dict(target_interface),
            "adapter": adapter.as_dict() if adapter is not None else None,
        },
        "mechanism": {
            "id": card.id,
            "name": card.name,
            "principle": card.principle,
            "source_domains": list(card.source_domains),
            "primitive_chain": list(card.primitive_chain),
            "carrier": card.carrier,
            "laws": list(card.laws),
            "invariants": list(card.invariants),
            "failure_modes": list(card.failure_modes),
            "evidence_level": card.evidence_level,
        },
        "analogy": {
            "kind": "behavioral-analogy",
            "isomorphism_claimed": False,
            "isomorphism_gap": "no exact structure-preserving mapping is declared",
            "basis": list(match.get("reasons") or ()),
            "source_law": list(card.laws),
            "target_semantics": operation.semantics,
            "preserved": list(candidate.preserved),
            "relaxed": list(candidate.relaxed),
            "validity": list(candidate.validity),
        },
        "relaxation": candidate.relaxation.as_dict(),
        "mapping": mapping,
        "handoff": {
            "readiness": readiness,
            "environment": dict(environment),
            **handoff,
        },
        "evidence": {
            "candidate_level": candidate.evidence_level,
            "mechanism_level": card.evidence_level,
            "target_level": "not-executed" if adapter is None else "adapter-declared",
            "proposal_level": "unvalidated",
        },
        "checks": checks,
        "gaps": gaps,
        "provenance": list(
            dict.fromkeys((*candidate.provenance, *target.provenance))
        ),
    }


def build_bundle(
    operation_id: str,
    *,
    target_id: str = glm.TARGET_ID,
    limit: int = 12,
) -> dict[str, Any]:
    """Build a reviewable proposal bundle without executing a target."""
    operation, target, candidates, matches = retrieve(
        operation_id, target_id=target_id, limit=limit
    )
    proposals = []
    for candidate in candidates:
        card = MECHANISM_BY_ID[candidate.mechanism]
        adapter = _adapter(target.id, operation.id, candidate.mechanism)
        proposals.append(
            _proposal(
                operation,
                target,
                card,
                candidate,
                matches.get(candidate.id, {}),
                adapter,
            )
        )
    readiness_counts: dict[str, int] = {}
    for proposal in proposals:
        key = proposal["handoff"]["readiness"]
        readiness_counts[key] = readiness_counts.get(key, 0) + 1
    checks = [
        {
            "name": "candidate retrieval",
            "status": "pass" if proposals else "gap",
            "detail": f"{len(proposals)} proposal(s)",
        },
        {
            "name": "proposal boundary",
            "status": "pass",
            "detail": "proposals are unvalidated plans; no isomorphism is claimed",
        },
    ]
    gaps = [
        "proposals are unvalidated; run a handoff command to obtain a certificate",
        "no exact isomorphism is claimed for any proposal",
        "a ready-for-execution proposal still depends on its declared target environment",
    ]
    return {
        "ok": bool(proposals),
        "schema": BUNDLE_SCHEMA,
        "operation": operation.as_dict(),
        "target": target.as_dict(),
        "summary": {
            "proposals": len(proposals),
            "ready_for_execution": readiness_counts.get("ready-for-execution", 0),
            "needs_target_adapter": readiness_counts.get("needs-target-adapter", 0),
            "needs_target_vectors": readiness_counts.get("needs-target-vectors", 0),
            "needs_environment": readiness_counts.get("needs-environment", 0),
            "review_counts": {"unreviewed": len(proposals)},
            "mechanisms": [proposal["mechanism"]["id"] for proposal in proposals],
            "domains": sorted(
                {proposal["mechanism"]["source_domains"][0] for proposal in proposals}
            ),
        },
        "proposals": proposals,
        "checks": checks,
        "gaps": gaps,
        "headline": (
            f"{len(proposals)} cross-domain proposal(s) for {operation.id} "
            f"on {target.id}; "
            f"{readiness_counts.get('ready-for-execution', 0)} ready to execute."
        ),
    }


def render_bundle(payload: Mapping[str, Any]) -> str:
    """Render a proposal bundle for review."""
    lines = ["=" * 78, "CROSS-DOMAIN TRANSFER PROPOSALS", "=" * 78]
    lines.append(str(payload.get("headline") or ""))
    lines.append(
        f"operation: {(payload.get('operation') or {}).get('id')} · "
        f"target: {(payload.get('target') or {}).get('id')}"
    )
    lines.append("")
    for proposal in payload.get("proposals") or ():
        handoff = proposal.get("handoff") or {}
        lines.append(
            f"{proposal.get('rank')}. {proposal.get('mechanism', {}).get('id')} "
            f"[{handoff.get('readiness')}] score={proposal.get('score')}"
        )
        lines.append(
            "  analogy: "
            + "; ".join(proposal.get("analogy", {}).get("basis") or ())
        )
        review = proposal.get("review") or {}
        lines.append(f"  review: {review.get('state', 'unreviewed')}")
        first_gap = (proposal.get("gaps") or ["no gap declared"])[0]
        lines.append(f"  first gap: {first_gap}")
        command = handoff.get("command")
        if command:
            lines.append(f"  handoff: {command}")
        else:
            lines.append(f"  next: {handoff.get('next_action')}")
        lines.append("")
    if not payload.get("proposals"):
        lines.append("No mechanism card declares support for this operation.")
        lines.append("")
    lines.append(
        "A proposal is a reviewable analogy and test plan, not a validated transfer."
    )
    return "\n".join(lines)


def load_review_ledger(directory: str | Path) -> dict[str, Any]:
    """Load the append-only review ledger, or return an empty ledger."""
    path = Path(directory) / REVIEW_LEDGER_FILENAME
    if not path.exists():
        return {
            "schema": REVIEW_LEDGER_SCHEMA,
            "operation": None,
            "target": None,
            "events": [],
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid proposal review ledger: {exc}") from exc
    if not isinstance(payload, Mapping) or payload.get("schema") != REVIEW_LEDGER_SCHEMA:
        raise ValueError("invalid proposal review ledger schema")
    events = payload.get("events")
    if not isinstance(events, list):
        raise ValueError("proposal review ledger events must be a list")
    for event in events:
        if not isinstance(event, Mapping) or event.get("schema") != REVIEW_EVENT_SCHEMA:
            raise ValueError("invalid proposal review event")
    return {
        "schema": REVIEW_LEDGER_SCHEMA,
        "operation": payload.get("operation"),
        "target": payload.get("target"),
        "events": [dict(event) for event in events],
    }


def _certificate_evidence(
    root: Path,
    certificate_path: str | Path,
    operation: str,
    target: str,
) -> dict[str, Any]:
    path = Path(certificate_path)
    if not path.is_file():
        raise ValueError(f"certificate file does not exist: {path}")
    raw = path.read_bytes()
    if len(raw) > REVIEW_CERTIFICATE_BYTES:
        raise ValueError(
            f"certificate file is larger than {REVIEW_CERTIFICATE_BYTES} bytes"
        )
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"certificate is not valid JSON: {exc}") from exc
    if not isinstance(document, Mapping):
        raise ValueError("certificate JSON must be an object")
    candidate = document.get("certificate")
    certificate = candidate if isinstance(candidate, Mapping) else document
    if certificate.get("schema") != "cent-transfer-certificate/1":
        raise ValueError("evidence is not a cent-transfer-certificate/1 document")
    if certificate.get("status") != "pass":
        raise ValueError("tested evidence must be a passing certificate")
    operation_document = document.get("operation")
    if isinstance(operation_document, Mapping):
        operation_id = operation_document.get("id")
        if operation_id is not None and str(operation_id) != operation:
            raise ValueError(
                f"certificate operation {operation_id!r} does not match {operation!r}"
            )
    target_document = document.get("target")
    if isinstance(target_document, Mapping):
        target_id = target_document.get("id")
        if target_id is not None and str(target_id) != target:
            raise ValueError(
                f"certificate target {target_id!r} does not match {target!r}"
            )
    digest = hashlib.sha256(raw).hexdigest()
    evidence_dir = root / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / f"{digest}.json"
    if not evidence_path.exists():
        _write_bytes(evidence_path, raw)
    return {
        "schema": "cent-transfer-certificate/1",
        "status": "pass",
        "evidence_level": certificate.get("evidence_level"),
        "scope": certificate.get("scope"),
        "path": evidence_path.relative_to(root).as_posix(),
        "sha256": digest,
        "source_name": path.name,
    }


def record_review(
    directory: str | Path,
    proposal_id: str,
    *,
    state: str,
    reviewer: str,
    note: str,
    certificate_path: str | Path | None = None,
) -> dict[str, Any]:
    """Append one review decision to the durable proposal ledger."""
    root = Path(directory)
    index_path = root / "index.json"
    if not index_path.is_file():
        raise ValueError(f"proposal bundle has no index.json: {root}")
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid proposal index: {exc}") from exc
    if not isinstance(index, Mapping) or index.get("schema") != INDEX_SCHEMA:
        raise ValueError("invalid proposal index schema")
    state = str(state or "").strip()
    if state not in REVIEW_STATES:
        raise ValueError(
            f"unknown review state {state!r}; expected one of "
            f"{', '.join(sorted(REVIEW_STATES))}"
        )
    reviewer = str(reviewer or "").strip()
    if not reviewer:
        raise ValueError("reviewer is required")
    note = str(note or "").strip()
    if not note:
        raise ValueError("review note is required")
    proposal_id = str(proposal_id or "").strip()
    rows = index.get("proposals")
    if not isinstance(rows, list):
        raise ValueError("proposal index has no proposal rows")
    row = next(
        (item for item in rows if isinstance(item, Mapping) and item.get("id") == proposal_id),
        None,
    )
    if row is None:
        known = ", ".join(str(item.get("id")) for item in rows if isinstance(item, Mapping))
        raise ValueError(f"unknown proposal {proposal_id!r}; known: {known}")
    file_name = row.get("file")
    if not isinstance(file_name, str) or not file_name:
        raise ValueError("proposal index row has no file")
    proposal_path = root / Path(file_name).name
    if not proposal_path.is_file():
        raise ValueError(f"proposal file does not exist: {proposal_path}")
    try:
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid proposal file: {exc}") from exc
    if not isinstance(proposal, Mapping) or proposal.get("schema") != PROPOSAL_SCHEMA:
        raise ValueError("invalid proposal schema")
    operation = str(index.get("operation") or (proposal.get("operation") or {}).get("id"))
    target = str(index.get("target") or (proposal.get("target") or {}).get("id"))
    mechanism = str((proposal.get("mechanism") or {}).get("id") or "")
    ledger = load_review_ledger(root)
    if ledger.get("operation") not in {None, operation}:
        raise ValueError("review ledger operation does not match the bundle")
    if ledger.get("target") not in {None, target}:
        raise ValueError("review ledger target does not match the bundle")
    evidence = None
    if state == "tested":
        if certificate_path is None:
            raise ValueError("tested review requires --certificate")
        evidence = _certificate_evidence(root, certificate_path, operation, target)
    elif certificate_path is not None:
        raise ValueError("only a tested review accepts --certificate")
    prior_state = _review_state(ledger, proposal_id)
    ledger["operation"] = operation
    ledger["target"] = target
    events = ledger["events"]
    event = {
        "schema": REVIEW_EVENT_SCHEMA,
        "sequence": len(events) + 1,
        "proposal_id": proposal_id,
        "operation": operation,
        "target": target,
        "mechanism": mechanism,
        "prior_state": prior_state,
        "state": state,
        "reviewer": reviewer,
        "note": note,
        "recorded_at": _review_now(),
        "evidence": evidence,
    }
    events.append(event)
    ledger_path = root / REVIEW_LEDGER_FILENAME
    _write_json(ledger_path, ledger)
    proposal = dict(proposal)
    proposal["review"] = _review_block(events, proposal_id)
    _write_json(proposal_path, proposal)
    updated_rows = []
    for item in rows:
        if not isinstance(item, Mapping):
            updated_rows.append(item)
            continue
        updated = dict(item)
        if updated.get("id") == proposal_id:
            updated["review_state"] = state
        updated_rows.append(updated)
    index = dict(index)
    index["proposals"] = updated_rows
    index["review"] = _review_summary(
        ledger,
        [
            str(item.get("id"))
            for item in updated_rows
            if isinstance(item, Mapping)
        ],
    )
    index["review_ledger"] = REVIEW_LEDGER_FILENAME
    _write_json(index_path, index)
    _write_index_markdown(root / "index.md", index)
    return {
        "ok": True,
        "schema": REVIEW_EVENT_SCHEMA,
        "proposal_id": proposal_id,
        "prior_state": prior_state,
        "state": state,
        "event": event,
        "review": proposal["review"],
        "ledger": str(ledger_path),
        "summary": index["review"],
    }


def render_review_event(payload: Mapping[str, Any]) -> str:
    """Render one recorded review decision."""
    event = payload.get("event") or {}
    evidence = event.get("evidence") or {}
    lines = [
        "=" * 78,
        "PROPOSAL REVIEW RECORDED",
        "=" * 78,
        f"proposal: {payload.get('proposal_id')}",
        f"state: {payload.get('prior_state')} -> {payload.get('state')}",
        f"reviewer: {event.get('reviewer')}",
        f"note: {event.get('note')}",
        f"recorded: {event.get('recorded_at')}",
        f"ledger: {payload.get('ledger')}",
    ]
    if evidence:
        lines.append(
            f"evidence: {evidence.get('path')} "
            f"(sha256 {evidence.get('sha256')}, {evidence.get('evidence_level')})"
        )
    return "\n".join(lines)


def render_review(ledger: Mapping[str, Any]) -> str:
    """Render the durable review ledger."""
    summary = _review_summary(ledger)
    lines = ["=" * 78, "PROPOSAL REVIEW LEDGER", "=" * 78]
    decisions = summary["decisions"]
    lines.append(
        f"events: {summary['events']} · "
        f"decisions: accepted {decisions.get('accepted', 0)}, "
        f"rejected {decisions.get('rejected', 0)}, "
        f"tested {decisions.get('tested', 0)}"
    )
    events = ledger.get("events") or ()
    if not events:
        lines.append("No reviews recorded.")
    for event in events:
        evidence = event.get("evidence") or {}
        lines.append(
            f"{event.get('sequence')}. {event.get('proposal_id')} "
            f"[{event.get('prior_state')} -> {event.get('state')}] "
            f"by {event.get('reviewer')} at {event.get('recorded_at')}"
        )
        lines.append(f"   note: {event.get('note')}")
        if evidence:
            lines.append(
                f"   evidence: {evidence.get('path')} "
                f"(sha256 {evidence.get('sha256')}, {evidence.get('evidence_level')})"
            )
    lines.append("")
    lines.append("A review decision is an audit record, not a target certificate.")
    return "\n".join(lines)


def _write_index_markdown(path: Path, index: Mapping[str, Any]) -> None:
    markdown = ["# Cross-domain transfer proposals", ""]
    markdown.append(
        f"Operation `{index.get('operation')}` · target `{index.get('target')}`"
    )
    markdown.append("")
    markdown.append(
        "A proposal is a reviewable analogy and test plan, not a validated transfer."
    )
    markdown.append("")
    markdown.append("| Rank | Mechanism | Readiness | Review | Handoff |")
    markdown.append("|---|---|---|---|---|")
    for row in index.get("proposals") or ():
        command = f"`{row['handoff']}`" if row.get("handoff") else "—"
        markdown.append(
            f"| {row.get('rank')} | `{row.get('mechanism')}` | "
            f"{row.get('readiness')} | {row.get('review_state', 'unreviewed')} | "
            f"{command} |"
        )
    if index.get("review_ledger"):
        markdown.append("")
        markdown.append(f"Review ledger: `{index['review_ledger']}`")
    markdown.append("")
    _write_bytes(path, ("\n".join(markdown) + "\n").encode("utf-8"))


def write_bundle(payload: Mapping[str, Any], directory: str | Path) -> list[Path]:
    """Write a portable proposal bundle and preserve any existing reviews."""
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    ledger = load_review_ledger(root)
    paths: list[Path] = []
    index_rows = []
    proposals = []
    for proposal in payload.get("proposals") or ():
        proposal = dict(proposal)
        proposal["review"] = _review_block(ledger["events"], str(proposal["id"]))
        proposals.append(proposal)
        safe = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(proposal["id"]))
        path = root / f"{safe}.json"
        _write_json(path, proposal)
        paths.append(path)
        index_rows.append(
            {
                "id": proposal["id"],
                "rank": proposal["rank"],
                "mechanism": proposal["mechanism"]["id"],
                "readiness": proposal["handoff"]["readiness"],
                "review_state": proposal["review"]["state"],
                "file": path.name,
                "handoff": proposal["handoff"].get("command"),
            }
        )
    proposal_ids = [str(proposal["id"]) for proposal in proposals]
    index = {
        "schema": INDEX_SCHEMA,
        "operation": payload.get("operation", {}).get("id"),
        "target": payload.get("target", {}).get("id"),
        "summary": payload.get("summary", {}),
        "review": _review_summary(ledger, proposal_ids),
        "review_ledger": (
            REVIEW_LEDGER_FILENAME
            if (root / REVIEW_LEDGER_FILENAME).exists()
            else None
        ),
        "proposals": index_rows,
    }
    index_path = root / "index.json"
    _write_json(index_path, index)
    paths.append(index_path)
    _write_index_markdown(root / "index.md", index)
    paths.append(root / "index.md")
    return paths
