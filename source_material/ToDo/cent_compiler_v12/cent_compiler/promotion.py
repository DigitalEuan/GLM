"""Hypothesis-to-mechanism promotion gate.

A pre-admission lead is not a mechanism card, an operation contract or a
transfer proposal.  This module is the explicit gate between those states.  It
admits a lead to the proposal stage only when all of the following are already
declared and independently inspectable:

* the lead exists in the pre-admission registry;
* the operation has a production contract with at least one reference test;
* the selected mechanism card is declared and supports that operation;
* the lead's candidate chain structurally overlaps the card's primitive chain;
* an executable target adapter has fixed vectors for that operation/mechanism;
* a passing ``cent-transfer-validation/1`` certificate matches the operation,
  target, mechanism and fixed vectors;
* a separate promotion review accepts the lead/card/operation/target and pins
  the certificate digest.

The gate creates a proposal bundle only after those checks pass.  It does not
add the operation to ``supported_operations``, validate a physical device, or
claim an exact isomorphism.  The resulting proposal remains an unvalidated
plan; the normal proposal review and target-test path continues from there.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from . import proposals
from .hypotheses import LEAD_BY_ID
from .mechanisms import MECHANISM_BY_ID
from .targets import glm, glm_live
from .transfer_engine import get_operation, get_target_profile
from .transfer_validation import CERTIFICATE_SCHEMA, VALIDATION_SCHEMA

SCHEMA = "cent-hypothesis-promotion/1"
REVIEW_SCHEMA = "cent-hypothesis-promotion-review/1"
EVIDENCE_LIMIT = 4 * 1024 * 1024
REVIEW_STATES = frozenset({"accepted"})


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _read_json(path: str | Path, label: str) -> tuple[dict[str, Any], bytes, str]:
    source = Path(path)
    if not source.is_file():
        raise ValueError(f"{label} does not exist: {source}")
    raw = source.read_bytes()
    if len(raw) > EVIDENCE_LIMIT:
        raise ValueError(f"{label} is larger than {EVIDENCE_LIMIT} bytes")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(document, Mapping):
        raise ValueError(f"{label} JSON must be an object")
    return dict(document), raw, hashlib.sha256(raw).hexdigest()


def _text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _adapter(target_id: str, operation: str, mechanism: str) -> Any:
    try:
        if target_id == glm.TARGET_ID:
            return glm.get_adapter(operation, mechanism)
        if target_id == glm_live.TARGET_ID:
            return glm_live.get_adapter(operation, mechanism)
    except (KeyError, ValueError) as exc:
        raise ValueError(str(exc)) from exc
    raise ValueError(
        f"no executable target adapter declared for target {target_id!r}"
    )


def _target_test(
    certificate_path: str | Path,
    *,
    operation: str,
    target_id: str,
    mechanism: str,
    adapter: Any,
) -> dict[str, Any]:
    document, _raw, digest = _read_json(certificate_path, "target certificate")
    if document.get("schema") != VALIDATION_SCHEMA:
        raise ValueError(
            f"target certificate must have schema {VALIDATION_SCHEMA!r}"
        )
    if document.get("status") != "pass":
        raise ValueError("target certificate status must be 'pass'")
    certificate = document.get("certificate")
    if (
        not isinstance(certificate, Mapping)
        or certificate.get("schema") != CERTIFICATE_SCHEMA
        or certificate.get("status") != "pass"
    ):
        raise ValueError(
            f"target certificate must contain a passing {CERTIFICATE_SCHEMA!r}"
        )
    operation_document = document.get("operation")
    if not isinstance(operation_document, Mapping):
        raise ValueError("target certificate has no operation document")
    if str(operation_document.get("id")) != operation:
        raise ValueError(
            f"target certificate operation {operation_document.get('id')!r} "
            f"does not match {operation!r}"
        )
    target_document = document.get("target")
    if not isinstance(target_document, Mapping):
        raise ValueError("target certificate has no target document")
    if str(target_document.get("id")) != target_id:
        raise ValueError(
            f"target certificate target {target_document.get('id')!r} "
            f"does not match {target_id!r}"
        )
    validated = document.get("validated_candidate")
    if not isinstance(validated, Mapping):
        raise ValueError("target certificate has no validated_candidate")
    if str(validated.get("mechanism")) != mechanism:
        raise ValueError(
            f"target certificate mechanism {validated.get('mechanism')!r} "
            f"does not match {mechanism!r}"
        )
    if validated.get("status") != "validated":
        raise ValueError("target certificate candidate is not validated")
    evidence_level = str(certificate.get("evidence_level") or "")
    if evidence_level not in {"target-simulated", "target-integrated"}:
        raise ValueError(
            f"target certificate has no executable evidence level: {evidence_level!r}"
        )
    vectors = document.get("vectors")
    if not isinstance(vectors, list) or not vectors:
        raise ValueError("target certificate has no fixed vectors")
    vector_ids = [str(item.get("id")) for item in vectors if isinstance(item, Mapping)]
    if len(vector_ids) != len(vectors) or any(not item for item in vector_ids):
        raise ValueError("target certificate has malformed fixed vectors")
    expected_vectors = [str(vector.id) for vector in adapter.vectors]
    if vector_ids != expected_vectors:
        raise ValueError(
            "target certificate vectors do not match the declared adapter vectors"
        )
    tested = validated.get("tests")
    if not isinstance(tested, list) or [str(item) for item in tested] != expected_vectors:
        raise ValueError(
            "target certificate does not attest every declared fixed vector"
        )
    checks = certificate.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("target certificate has no checks")
    if any(
        not isinstance(check, Mapping) or check.get("status") != "pass"
        for check in checks
    ):
        raise ValueError("target certificate contains a non-passing check")
    return {
        "schema": CERTIFICATE_SCHEMA,
        "status": "pass",
        "evidence_level": evidence_level,
        "scope": certificate.get("scope"),
        "path": str(Path(certificate_path)),
        "sha256": digest,
        "vectors": vector_ids,
    }


def _review(
    review_path: str | Path,
    *,
    lead_id: str,
    operation: str,
    mechanism: str,
    target_id: str,
    certificate_sha256: str,
) -> dict[str, Any]:
    document, _raw, digest = _read_json(review_path, "promotion review")
    if document.get("schema") != REVIEW_SCHEMA:
        raise ValueError(f"promotion review must have schema {REVIEW_SCHEMA!r}")
    if document.get("state") not in REVIEW_STATES:
        raise ValueError(
            f"promotion review state must be one of {sorted(REVIEW_STATES)}"
        )
    expected = {
        "lead_id": lead_id,
        "operation": operation,
        "mechanism": mechanism,
        "target": target_id,
    }
    for key, value in expected.items():
        if str(document.get(key)) != value:
            raise ValueError(
                f"promotion review {key} {document.get(key)!r} does not match {value!r}"
            )
    if str(document.get("certificate_sha256")) != certificate_sha256:
        raise ValueError(
            "promotion review certificate_sha256 does not match the target certificate"
        )
    reviewer = _text(document.get("reviewer"), "promotion review reviewer")
    note = _text(document.get("note"), "promotion review note")
    reviewed_at = _text(document.get("reviewed_at"), "promotion review reviewed_at")
    return {
        "schema": REVIEW_SCHEMA,
        "state": document["state"],
        "reviewer": reviewer,
        "note": note,
        "reviewed_at": reviewed_at,
        "path": str(Path(review_path)),
        "sha256": digest,
        "certificate_sha256": certificate_sha256,
    }


def build_promotion(
    lead_id: str,
    mechanism_id: str,
    certificate_path: str | Path,
    review_path: str | Path,
    *,
    target_id: str = glm.TARGET_ID,
) -> dict[str, Any]:
    """Validate a lead/card/contract/test/review and create a proposal bundle.

    All checks are completed before ``proposals.build_bundle`` is called.  A
    failed check raises ``ValueError`` and creates no proposal.
    """
    lead_key = _text(lead_id, "lead_id")
    lead = LEAD_BY_ID.get(lead_key)
    if lead is None:
        known = ", ".join(sorted(LEAD_BY_ID))
        raise ValueError(f"unknown hypothesis lead {lead_key!r}; known: {known}")
    mechanism_key = _text(mechanism_id, "mechanism_id")
    card = MECHANISM_BY_ID.get(mechanism_key)
    if card is None:
        known = ", ".join(sorted(MECHANISM_BY_ID))
        raise ValueError(
            f"mechanism {mechanism_key!r} is not declared; known: {known}"
        )
    try:
        contract = get_operation(lead.operation)
    except KeyError as exc:
        raise ValueError(str(exc)) from exc
    if contract.id != lead.operation:
        raise ValueError(
            f"lead operation {lead.operation!r} has no matching operation contract"
        )
    if not contract.tests:
        raise ValueError(
            f"operation contract {contract.id!r} has no reference test"
        )
    if contract.id not in card.supported_operations:
        raise ValueError(
            f"mechanism {card.id!r} does not declare support for {contract.id!r}"
        )
    overlap = sorted(set(lead.candidate_chain) & set(card.primitive_chain))
    if not overlap:
        raise ValueError(
            f"lead {lead.id!r} and mechanism {card.id!r} have no primitive-chain overlap"
        )
    try:
        target = get_target_profile(target_id)
    except KeyError as exc:
        raise ValueError(str(exc)) from exc
    adapter = _adapter(target.id, contract.id, card.id)
    if not adapter.vectors:
        raise ValueError(
            f"target adapter {card.id!r} has no fixed vectors for {contract.id!r}"
        )
    target_test = _target_test(
        certificate_path,
        operation=contract.id,
        target_id=target.id,
        mechanism=card.id,
        adapter=adapter,
    )
    review = _review(
        review_path,
        lead_id=lead.id,
        operation=contract.id,
        mechanism=card.id,
        target_id=target.id,
        certificate_sha256=target_test["sha256"],
    )
    checks = [
        {
            "name": "declared mechanism card",
            "status": "pass",
            "detail": f"{card.id}: {card.evidence_level}",
        },
        {
            "name": "operation contract",
            "status": "pass",
            "detail": (
                f"{contract.id}: {len(contract.tests)} reference test(s), "
                f"tolerance {contract.tolerance}"
            ),
        },
        {
            "name": "structural overlap",
            "status": "pass",
            "detail": "overlap: " + ", ".join(overlap),
        },
        {
            "name": "target adapter and fixed vectors",
            "status": "pass",
            "detail": f"{adapter.path}:{adapter.entrypoint}; "
                      f"{len(adapter.vectors)} vector(s)",
        },
        {
            "name": "passing target test",
            "status": "pass",
            "detail": (
                f"{target_test['evidence_level']}; "
                f"sha256 {target_test['sha256'][:12]}…"
            ),
        },
        {
            "name": "promotion review",
            "status": "pass",
            "detail": (
                f"{review['reviewer']} accepted at {review['reviewed_at']}; "
                f"sha256 {review['sha256'][:12]}…"
            ),
        },
    ]
    promotion = {
        "schema": SCHEMA,
        "status": "pass",
        "gate": "pass",
        "created_at": _now(),
        "lead": lead.as_dict(),
        "operation": {
            "id": contract.id,
            "name": contract.name,
            "tests": [test.id for test in contract.tests],
            "tolerance": contract.tolerance,
        },
        "mechanism": {
            "id": card.id,
            "name": card.name,
            "evidence_level": card.evidence_level,
            "primitive_chain": list(card.primitive_chain),
            "overlap": overlap,
        },
        "target": {
            "id": target.id,
            "kind": target.kind,
        },
        "target_test": target_test,
        "review": review,
        "checks": checks,
        "gaps": [
            "promotion is an admission gate, not a physical-device validation",
            "the target certificate is a declared reference-target simulation",
            "the promotion review artifact does not authenticate reviewer identity",
            "the proposal remains unvalidated and no exact isomorphism is claimed",
            "supported_operations is unchanged",
        ],
        "claim": (
            "A promoted lead is admitted to the proposal stage after a declared "
            "card, operation contract, passing reference target test and review. "
            "No physical fabrication, measurement or target integration is claimed."
        ),
    }
    bundle = proposals.build_bundle(
        contract.id,
        target_id=target.id,
        limit=max(len(MECHANISM_BY_ID), 1),
        mechanism_ids=(card.id,),
        promotion=promotion,
    )
    if not bundle.get("proposals"):
        raise ValueError(
            f"no proposal was created for {contract.id!r} via {card.id!r}"
        )
    promotion["proposal_ids"] = [
        str(proposal["id"]) for proposal in bundle["proposals"]
    ]
    for proposal in bundle["proposals"]:
        proposal["promotion"] = promotion
    bundle["promotion"] = promotion
    return {
        "ok": True,
        "schema": SCHEMA,
        "status": "pass",
        "gate": "pass",
        "lead": promotion["lead"],
        "operation": promotion["operation"],
        "mechanism": promotion["mechanism"],
        "target": promotion["target"],
        "target_test": target_test,
        "review": review,
        "checks": checks,
        "gaps": promotion["gaps"],
        "claim": promotion["claim"],
        "proposal_bundle": bundle,
        "proposal_ids": promotion["proposal_ids"],
        "headline": (
            f"{lead.id} -> {card.id} -> {contract.id}: promotion gate passed; "
            f"{len(bundle['proposals'])} proposal(s) created."
        ),
        "artifacts": {},
    }


def render_promotion(payload: Mapping[str, Any]) -> str:
    """Render a promotion gate result for the terminal."""
    lines = ["=" * 78, "HYPOTHESIS PROMOTION GATE", "=" * 78]
    lines.append(str(payload.get("headline") or ""))
    lead = payload.get("lead") or {}
    mechanism = payload.get("mechanism") or {}
    operation = payload.get("operation") or {}
    lines.append(f"lead: {lead.get('id')}")
    lines.append(f"operation: {operation.get('id')}")
    lines.append(f"mechanism: {mechanism.get('id')}")
    lines.append(f"target: {(payload.get('target') or {}).get('id')}")
    lines.append("")
    lines.append("Checks")
    for check in payload.get("checks") or ():
        lines.append(f"  [{check.get('status')}] {check.get('name')}: {check.get('detail')}")
    lines.append("")
    lines.append("Proposals")
    for proposal_id in payload.get("proposal_ids") or ():
        lines.append(f"  {proposal_id}")
    lines.append("")
    lines.append("Gaps")
    for gap in payload.get("gaps") or ():
        lines.append(f"  - {gap}")
    lines.append("")
    lines.append(str(payload.get("claim") or ""))
    return "\n".join(lines)


def write_promotion(payload: dict[str, Any], directory: str | Path) -> list[Path]:
    """Write the promotion manifest and the proposal bundle it admitted."""
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    bundle = payload.get("proposal_bundle")
    if not isinstance(bundle, dict):
        raise ValueError("promotion has no proposal bundle")
    written = proposals.write_bundle(bundle, root / "proposals")
    paths: dict[str, str] = {"proposals": "proposals/"}
    payload = dict(payload)
    payload["artifacts"] = paths
    manifest = root / "promotion.json"
    manifest.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    written.append(manifest)
    markdown = root / "promotion.md"
    markdown.write_text(
        "# Hypothesis promotion\n\n```text\n"
        + render_promotion(payload)
        + "\n```\n",
        encoding="utf-8",
    )
    written.append(markdown)
    paths["promotion.json"] = "promotion.json"
    paths["promotion.md"] = "promotion.md"
    manifest.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return written


__all__ = [
    "SCHEMA",
    "REVIEW_SCHEMA",
    "build_promotion",
    "render_promotion",
    "write_promotion",
]
