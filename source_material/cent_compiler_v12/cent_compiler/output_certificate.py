"""Uniform certificate-or-gap blocks for public compiler payloads.

The certificate is deliberately modest: it summarizes only the declared checks
already present in a payload (exact algebra, structural audits, design plans,
DRC checks or regression counts).  It is not a physical proof, a measured-device
report, a fabrication sign-off or a replacement for the payload's own gaps.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

CERTIFICATE_SCHEMA = "cent-output-certificate/1"
DEFAULT_CLAIM = (
    "This certificate covers only the declared exact/structural checks in this "
    "payload; it is not measured-device, fabrication, physical-proof or "
    "manufacturing evidence."
)

_PASS_STATUSES = {
    "pass",
    "ok",
    "complete",
    "derived",
    "solved",
    "drc-pass",
    "certified",
    "declared",
}
_GAP_STATUSES = {
    "gap",
    "fail",
    "failed",
    "stop",
    "partial",
    "not-run",
    "unknown",
}


def _status(value: Any) -> str:
    """Normalize a declared check status to ``pass`` or ``gap``."""
    text = str(value or "gap").strip().lower()
    if text in _PASS_STATUSES:
        return "pass"
    if text in _GAP_STATUSES:
        return "gap"
    return "gap"


def _check(name: Any, passed: bool, detail: Any = "") -> dict[str, str]:
    return {
        "name": str(name or "declared check"),
        "status": "pass" if passed else "gap",
        "detail": str(detail or ""),
    }


def _template_decision(spice: Any) -> tuple[bool, str]:
    """Check the explicit structural/no-filtering template contract."""
    if not isinstance(spice, Mapping):
        return False, "no structural template decision"
    decision = spice.get("decision")
    if not isinstance(decision, Mapping):
        return False, "no structural template decision"
    passed = (
        decision.get("structural") is True
        and decision.get("basis") == "complete ¢ operation set"
        and decision.get("proposal_effect") == "none"
    )
    return passed, (
        f"structural={decision.get('structural')!r}, "
        f"basis={decision.get('basis')!r}, "
        f"proposal_effect={decision.get('proposal_effect')!r}"
    )


def _checks(items: Any) -> list[dict[str, str]]:
    """Normalize an iterable of declared check/step/stage mappings."""
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        return []
    rows: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        name = (
            item.get("name")
            or item.get("label")
            or item.get("stage")
            or item.get("route")
            or "declared check"
        )
        rows.append(
            {
                "name": str(name),
                "status": _status(item.get("status")),
                "detail": str(
                    item.get("detail")
                    or item.get("detail_text")
                    or item.get("failure")
                    or ""
                ),
            }
        )
    return rows


def _gaps(value: Any) -> list[Any]:
    """Normalize a gap field while preserving structured gap records."""
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, (str, bytes)):
        return [str(value)]
    if isinstance(value, Sequence):
        return list(value)
    return [str(value)]


def _subject(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """Find the most specific nested compiler payload, if present."""
    for key in (
        "material",
        "route",
        "graph",
        "derivation",
        "report",
        "binding",
        "design",
        "comparison",
        "physical",
        "fabrication",
        "dynamics",
    ):
        candidate = payload.get(key)
        if isinstance(candidate, Mapping) and candidate.get("schema"):
            return candidate
    return payload


def _certificate_for(schema: str, subject: Mapping[str, Any]) -> dict[str, Any]:
    """Build a certificate from the subject's own declared evidence."""
    existing = subject.get("output_certificate")
    if isinstance(existing, Mapping) and existing.get("schema") == CERTIFICATE_SCHEMA:
        return dict(existing)

    checks: list[dict[str, str]] = []
    gaps: list[Any] = []

    if schema == "cent-compile/1":
        summary = subject.get("summary") or {}
        proposals = subject.get("proposals") or []
        spice = subject.get("spice") or {}
        boundary = subject.get("boundary") or {}
        decision_ok, decision_detail = _template_decision(spice)
        checks = [
            _check(
                "£ decomposition",
                bool(subject.get("dag")),
                f"{len(subject.get('dag') or [])} primitive(s)",
            ),
            _check(
                "∆ enumeration",
                bool(summary.get("implementations")),
                f"{summary.get('implementations', 0)} declared candidate(s)",
            ),
            _check(
                "ranked proposal",
                bool(proposals),
                f"{len(proposals)} ranked proposal(s)",
            ),
            _check(
                "structural SPICE template",
                bool(spice.get("template")) if isinstance(spice, Mapping) else False,
                (spice.get("detail") or "no structural template")
                if isinstance(spice, Mapping)
                else "no structural template",
            ),
            _check(
                "structural template decision",
                decision_ok,
                decision_detail,
            ),
            _check(
                "fabrication boundary",
                boundary.get("status") == "not-fabricated",
                boundary.get("claim") or "no proposal boundary was supplied",
            ),
        ]
        transfer = subject.get("transfer")
        if isinstance(transfer, Mapping):
            transfer_status = transfer.get("status")
            composition = transfer.get("composition") or {}
            if transfer_status == "certified":
                metrics = composition.get("metrics") or {}
                detail = (
                    f"composed {composition.get('chain')}: "
                    f"{metrics.get('passed', 0)}/{metrics.get('vectors', 0)} "
                    "fixed vector(s)"
                )
            elif transfer_status == "pass":
                metrics = transfer.get("metrics") or {}
                detail = (
                    f"{transfer.get('operation')} via "
                    f"{transfer.get('mechanism')} -> {transfer.get('target')}: "
                    f"{metrics.get('passed', 0)}/{metrics.get('vectors', 0)} "
                    "fixed vector(s)"
                )
            else:
                detail = transfer.get("reason") or "no composed transfer handoff"
            checks.append(
                _check(
                    "validated transfer handoff",
                    transfer_status in {"pass", "certified"},
                    detail,
                )
            )
            if isinstance(composition, Mapping):
                boundaries = composition.get("boundaries") or []
                if isinstance(boundaries, Sequence) and boundaries:
                    compatible = sum(
                        1
                        for boundary in boundaries
                        if isinstance(boundary, Mapping)
                        and boundary.get("status") == "compatible"
                    )
                    checks.append(
                        _check(
                            "stage boundary contracts",
                            compatible == len(boundaries),
                            f"{compatible}/{len(boundaries)} typed stage "
                            "boundary(ies) compatible",
                        )
                    )
        gaps = _gaps(subject.get("notes"))
        gaps.append(
            "compile JSON is a relation/proposal view, not a fabricated or measured device"
        )
    elif schema == "cent-material/1":
        program = subject.get("program")
        spice = subject.get("spice") or {}
        decision_ok, decision_detail = _template_decision(spice)
        checks = [
            _check(
                "exact program",
                program is not None,
                "cent-program/1 is present" if program else "no exact program was generated",
            ),
            _check(
                "SPICE template",
                bool(spice.get("template")) if isinstance(spice, Mapping) else False,
                (spice.get("detail") or "no structural template")
                if isinstance(spice, Mapping)
                else "no structural template",
            ),
            _check(
                "structural template decision",
                decision_ok,
                decision_detail,
            ),
        ]
        gaps = _gaps(subject.get("notes"))
        gaps.append("compile material is a relation artifact, not a physical route")
    elif schema == "cent-discovery/1":
        checks = _checks(subject.get("pipeline"))
        if not checks:
            checks = [
                _check(
                    "problem interpretation",
                    bool(subject.get("matched")),
                    "behaviour/object pair recognized"
                    if subject.get("matched")
                    else "no recognized behaviour/object pair",
                )
            ]
        gaps = _gaps(subject.get("gaps"))
    elif schema == "cent-operation-matrix/1":
        rows = subject.get("rows") or []
        groups = subject.get("groups") or []
        checks = [
            _check(
                "declared evidence classes",
                bool(rows) and all(row.get("evidence") for row in rows),
                f"{len(rows)} row(s) with an evidence class",
            ),
            _check(
                "row evidence fields",
                bool(rows) and all(
                    row.get("domain") and row.get("carrier") and row.get("first_gap")
                    for row in rows
                ),
                "every row carries domain, carrier and a first gap",
            ),
            _check(
                "compute/carry/grounding separation",
                bool(groups) and all(
                    all(row.get("role") == group.get("role") for row in group.get("rows") or ())
                    for group in groups
                ),
                f"{len(groups)} role-specific group(s)",
            ),
        ]
        gaps = _gaps(subject.get("gaps"))
    elif schema == "cent-route/1":
        topology = subject.get("topology_audit") or {}
        checks = _checks(topology.get("checks"))
        if not checks:
            checks = [
                _check(
                    "route topology",
                    topology.get("status") == "pass",
                    topology.get("detail") or "no topology audit",
                )
            ]
        gaps = _gaps(subject.get("gaps"))
    elif schema == "cent-axiom-graph/1":
        counts = subject.get("counts") or {}
        checks = [
            _check(
                "declared graph projection",
                bool(counts),
                f"{counts.get('wheels', 0)} wheels, {counts.get('axioms', 0)} axioms, "
                f"{counts.get('quantities', 0)} quantities"
                if counts
                else "no graph counts",
            ),
            _check(
                "endpoint resolution",
                not subject.get("gaps"),
                "all declared junctions and non-identities resolve"
                if not subject.get("gaps")
                else f"{len(subject.get('gaps') or [])} endpoint record(s) remain gaps",
            ),
        ]
        gaps = _gaps(subject.get("gaps"))
    elif schema == "cent-derivation/1":
        derived = subject.get("status") == "derived"
        checks = [
            _check(
                "exact relation derivation",
                derived,
                subject.get("formula") or "no exact relation was derived",
            )
        ]
        gaps = _gaps(subject.get("gaps"))
    elif schema == "cent-spoke-regression/1":
        total = subject.get("total_spokes", 0)
        derived = subject.get("derived", 0)
        matches = subject.get("formula_matches", 0)
        checks = [
            _check(
                "spoke derivation",
                bool(total) and derived == total,
                f"{derived}/{total} spokes derived",
            ),
            _check(
                "formula equality",
                bool(total) and matches == total,
                f"{matches}/{total} formulas match the legacy corpus",
            ),
        ]
        gaps = _gaps(subject.get("gaps")) + _gaps(subject.get("mismatches"))
    elif schema == "cent-case-regression/1":
        cases = subject.get("cases", 0)
        dim = subject.get("dimensional_agreement", 0)
        der = subject.get("derivability_agreement", 0)
        checks = [
            _check(
                "dimensional agreement",
                bool(cases) and dim == cases and subject.get("dimensional_unknown", 0) == 0,
                f"{dim}/{cases} exact dimension checks agree",
            ),
            _check(
                "derivability agreement",
                bool(cases) and der == cases,
                f"{der}/{cases} exact derivability checks agree",
            ),
        ]
        gaps = _gaps(subject.get("dimensional_mismatches")) + _gaps(
            subject.get("derivability_mismatches")
        )
    elif schema == "cent-move-corpus-report/1":
        counts = subject.get("counts") or {}
        checks = [
            _check(
                "corpus transitions",
                bool(counts.get("transitions")),
                f"{counts.get('transitions', 0)} adjacent transitions",
            ),
            _check(
                "return statistics",
                subject.get("return_stats") is not None,
                "declared integer-vector return statistics were computed",
            ),
        ]
        gaps = _gaps(subject.get("gaps"))
    elif schema in {"cent-leech-class/1", "cent-envelope/1"}:
        checks = _checks(subject.get("checks"))
        gaps = _gaps(subject.get("gaps"))
    elif schema == "cent-device/1":
        checks = _checks(subject.get("checks"))
        gaps = _gaps(subject.get("gaps"))
    elif schema == "cent-design/1":
        plan = _checks(subject.get("verification_plan"))
        if plan:
            checks = plan
        elif subject.get("spaces"):
            checks = [
                _check(
                    "declared design catalog",
                    bool(subject.get("spaces")),
                    f"{len(subject.get('spaces') or [])} declared design space(s)",
                )
            ]
            gaps = ["catalog only; no design has been solved"]
        else:
            checks = [
                _check(
                    "declared design",
                    subject.get("status") == "solved",
                    subject.get("status") or "no design status",
                )
            ]
        gaps = _gaps(subject.get("gaps")) + gaps
    elif schema == "cent-comparison/1":
        rows = subject.get("rows") or []
        checks = _checks(rows)
        if not checks:
            checks = [
                _check(
                    "route comparison",
                    bool(subject.get("results")),
                    f"{subject.get('solved_count', 0)} solved route(s)",
                )
            ]
        gaps = _gaps(subject.get("gaps"))
    elif schema in {"cent-physical/1", "cent-fabrication/1", "cent-dynamics/1"}:
        checks = _checks(subject.get("checks"))
        gaps = _gaps(subject.get("gaps"))
    elif schema == "cent-typed-graph/1":
        summary = subject.get("summary") or {}
        checks = [
            _check(
                "typed graph declaration",
                bool(subject.get("nodes")),
                f"{summary.get('node_count', len(subject.get('nodes') or []))} typed node(s), "
                f"{summary.get('feedback_edges', 0)} feedback edge(s)",
            )
        ]
        gaps = _gaps(subject.get("gaps"))
    else:
        checks = _checks(subject.get("checks"))
        if not checks and subject.get("status") is not None:
            checks = [
                _check(
                    "declared output status",
                    _status(subject.get("status")) == "pass",
                    subject.get("status"),
                )
            ]
        gaps = _gaps(subject.get("gaps"))

    if not checks:
        checks = [_check("declared checks", False, "no declared check was supplied")]
    passes = sum(1 for item in checks if item["status"] == "pass")
    status = "certified" if not gaps and passes == len(checks) else (
        "partial" if passes else "gap"
    )
    return {
        "schema": CERTIFICATE_SCHEMA,
        "subject_schema": schema,
        "status": status,
        "checks": checks,
        "gaps": gaps,
        "claim": DEFAULT_CLAIM,
    }


def attach_certificate(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of ``payload`` with one ``output_certificate`` block.

    If the payload is already a certificate-bearing nested artifact (for
    example a saved material bundle), the existing certificate is copied rather
    than re-derived.  This keeps the CLI/API envelope and the saved artifact in
    agreement without mutating either object.
    """
    if "output_certificate" in payload:
        return dict(payload)
    subject = _subject(payload)
    schema = str(subject.get("schema") or payload.get("schema") or "cent-output/1")
    result = dict(payload)
    result["output_certificate"] = _certificate_for(schema, subject)
    return result


__all__ = [
    "CERTIFICATE_SCHEMA",
    "DEFAULT_CLAIM",
    "attach_certificate",
]
