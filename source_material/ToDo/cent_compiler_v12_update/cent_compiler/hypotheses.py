"""Pre-admission structural hypotheses.

The transfer engine deliberately retrieves only mechanism cards that name an
operation in ``supported_operations``.  That gate is correct, but it leaves
useful structural leads invisible until a full mechanism card, operation
contract and test already exist.

This module is the missing pre-admission view.  It:

* compares operation behavior with every declared mechanism card, including
  cards that do not support the operation yet;
* carries user-supplied leads separately from mechanism cards;
* records each lead in the existing ``CentWheel`` knowledge-state machinery;
* never adds the operation to a card's ``supported_operations``;
* never creates a transfer candidate or claims target validation.

The default lead states are ``DOESNT_KNOW``.  A lead may become
``THINKS_TRUE`` only after a declared simulation, and ``KNOWS`` only after the
existing verification/fabrication gate.  The wheel's promotion rules are not
bypassed here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .hypothesis_bridge import CentEntry, CentWheel, KnowledgeState
from .mechanisms import MECHANISM_CARDS
from .transfer_engine import (
    BehaviorSignature,
    MECHANISM_BEHAVIORS,
    OPERATION_BEHAVIORS,
)

SCHEMA = "cent-hypothesis/1"
RESOLUTION_SCHEMA = "cent-hypothesis-resolution/1"
MIN_STRUCTURAL_SCORE = 6

_PROMOTION_REQUIRES = (
    "declared mechanism card with an explicit supported operation",
    "operation semantics and at least one fixed reference test",
    "exact probe or target adapter evidence",
    "reviewed promotion; no automatic supported_operations change",
)


@dataclass(frozen=True)
class HypothesisLead:
    """A lead that is visible before it is a mechanism card."""

    id: str
    operation: str
    title: str
    statement: str
    candidate_chain: tuple[str, ...]
    source: str
    status: KnowledgeState
    needs: tuple[str, ...]
    gaps: tuple[str, ...] = ()

    @property
    def behavior(self) -> BehaviorSignature:
        return BehaviorSignature(
            primitive_chain=self.candidate_chain,
            stateful="accum" in self.candidate_chain,
            feedback=False,
            conserved_quantities=(),
            nonlinearity="candidate correspondence",
            encoding="candidate",
            precision="unverified",
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "operation": self.operation,
            "title": self.title,
            "statement": self.statement,
            "candidate_chain": list(self.candidate_chain),
            "source": self.source,
            "status": self.status.value,
            "needs": list(self.needs),
            "gaps": list(self.gaps),
            "admitted": False,
            "promotion_requires": list(_PROMOTION_REQUIRES),
            "supported_operations_changed": False,
        }


LEADS: tuple[HypothesisLead, ...] = (
    HypothesisLead(
        id="nematic-q-tensor-bounding-box",
        operation="bounding_box",
        title="Nematic Q-tensor orientation envelope",
        statement=(
            "A nematic director/Q-tensor may provide an orientation-family "
            "representation for the finite-direction minimum-area envelope. "
            "No Q-tensor-to-projection map or equivalence is declared."
        ),
        candidate_chain=("spatial",),
        source="user-supplied review lead (2026-11-11)",
        status=KnowledgeState.DOESNT_KNOW,
        needs=(
            "proof:map Q-tensor invariants to the envelope's finite-direction projections",
            "test:compare exact corners and area over declared point sets",
            "definition:director/Q-tensor normalization and boundary conditions",
        ),
        gaps=(
            "no Q-tensor contract, map or exact probe",
            "no claim that a physical liquid-crystal state exists",
        ),
    ),
    HypothesisLead(
        id="bresenham-quantized-carry",
        operation="quantized_carry",
        title="Bresenham error-accumulator carry",
        statement=(
            "A Bresenham line walk and the delta-sigma error-feedback loop both "
            "carry a residual.  A structural correspondence is a lead only; no "
            "equivalence, reconstruction error bound or target adapter is declared."
        ),
        candidate_chain=("quantize", "accum", "delay"),
        source="user-supplied review lead (2026-11-11)",
        status=KnowledgeState.DOESNT_KNOW,
        needs=(
            "proof:state and update equivalence between Bresenham and first-order delta-sigma",
            "test:line-walk code against the declared delta-sigma reconstruction",
            "negative-control:a non-error-feedback raster walk that should not match",
        ),
        gaps=(
            "no Bresenham contract, exact implementation or target vector",
            "no quantization law or reconstruction claim",
        ),
    ),
)

LEAD_BY_ID = {lead.id: lead for lead in LEADS}
if len(LEAD_BY_ID) != len(LEADS):
    raise RuntimeError("hypothesis lead registry contains duplicate ids")

BOUNDING_BOX_BEHAVIOR = BehaviorSignature(
    primitive_chain=("spatial",),
    stateful=False,
    feedback=False,
    conserved_quantities=("extent",),
    nonlinearity="minimax orientation",
    encoding="geometry",
    precision="exact rational",
)

_OPERATION_BEHAVIORS = {
    **OPERATION_BEHAVIORS,
    "bounding_box": BOUNDING_BOX_BEHAVIOR,
}


def _tokens(value: str) -> set[str]:
    return set(str(value).lower().replace("/", " ").replace("_", " ").split())


def _overlap(left: str, right: str) -> bool:
    return bool(_tokens(left) & _tokens(right))


def _score(operation: BehaviorSignature, candidate: BehaviorSignature) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    overlap = set(operation.primitive_chain) & set(candidate.primitive_chain)
    if overlap:
        score += 2 * len(overlap)
        reasons.append("primitive overlap: " + ", ".join(sorted(overlap)))
    if operation.stateful == candidate.stateful:
        score += 3
        reasons.append(f"stateful {str(operation.stateful).lower()} match")
    if operation.feedback == candidate.feedback:
        score += 3
        reasons.append(f"feedback {str(operation.feedback).lower()} match")
    if _overlap(operation.encoding, candidate.encoding):
        score += 1
        reasons.append("encoding overlap")
    if _overlap(operation.nonlinearity, candidate.nonlinearity):
        score += 1
        reasons.append("nonlinearity overlap")
    if _overlap(operation.precision, candidate.precision):
        score += 1
        reasons.append("precision overlap")
    if set(operation.conserved_quantities) & set(candidate.conserved_quantities):
        score += 2
        reasons.append("conserved-quantity overlap")
    return score, reasons


def _lead(lead_id: str) -> HypothesisLead:
    key = str(lead_id or "").strip()
    try:
        return LEAD_BY_ID[key]
    except KeyError as exc:
        known = ", ".join(sorted(LEAD_BY_ID))
        raise ValueError(f"unknown hypothesis lead: {key!r}; known: {known}") from exc


_NEED_PROMPTS = {
    "proof": "Provide the exact proof or derivation, or a path to it, for",
    "test": "Provide the test, vector set or result, or a path to it, for",
    "negative-control": "Provide the negative-control result or path for",
    "definition": "Provide the declared definition or source for",
}


def questions_for(lead_id: str) -> tuple[dict[str, Any], ...]:
    """Turn every declared need into one explicit resolution question."""
    lead = _lead(lead_id)
    questions = []
    for index, need in enumerate(lead.needs, start=1):
        kind, separator, detail = need.partition(":")
        prompt_prefix = _NEED_PROMPTS.get(
            kind, "Provide evidence for"
        )
        detail = detail.strip() if separator else need
        questions.append({
            "id": f"q{index}",
            "need": need,
            "kind": kind if separator else "evidence",
            "prompt": f"{prompt_prefix}: {detail}",
        })
    return tuple(questions)


def resolve_lead(
    lead_id: str,
    answers: Mapping[str, str] | None = None,
    decision: str | None = None,
    decision_note: str = "",
) -> dict[str, Any]:
    """Ask only for missing needs, then record a keep/retire decision.

    This is a small state machine, not a proof checker.  A supplied answer is
    retained as supplied evidence; it is never treated as technical validation
    and it never changes ``supported_operations``.
    """
    lead = _lead(lead_id)
    supplied = {
        str(key): str(value).strip()
        for key, value in (answers or {}).items()
        if str(value).strip()
    }
    questions = questions_for(lead.id)
    known_ids = {question["id"] for question in questions}
    unknown = sorted(set(supplied) - known_ids)
    if unknown:
        raise ValueError(
            f"unknown answer id(s): {', '.join(unknown)}; expected {', '.join(sorted(known_ids))}"
        )
    for question in questions:
        question["answered"] = question["id"] in supplied
        question["answer"] = supplied.get(question["id"])

    answered = sum(1 for question in questions if question["answered"])
    missing = [question for question in questions if not question["answered"]]
    decision = str(decision or "").strip() or None
    if decision not in {None, "keep", "retire"}:
        raise ValueError("decision must be 'keep', 'retire' or omitted")
    note = str(decision_note or "").strip()

    if missing:
        status = "needs_input"
        next_question = missing[0]
        active = None
    elif decision is None:
        status = "ready_for_decision"
        next_question = {
            "id": "decision",
            "need": "decision:keep-or-retire",
            "kind": "decision",
            "prompt": "Decide whether to keep this lead active or retire it.",
            "options": ["keep", "retire"],
        }
        active = None
    elif decision == "retire" and not note:
        status = "needs_note"
        next_question = {
            "id": "decision_note",
            "need": "decision:retirement-note",
            "kind": "decision",
            "prompt": "Retirement requires a reason. Record why this lead is being retired.",
        }
        active = None
    elif decision == "keep":
        status = "retained"
        next_question = None
        active = True
    else:
        status = "retired"
        next_question = None
        active = False

    return {
        "ok": True,
        "schema": RESOLUTION_SCHEMA,
        "lead": lead.as_dict(),
        "questions": questions,
        "answers": supplied,
        "answered": answered,
        "total": len(questions),
        "status": status,
        "active": active,
        "next_question": next_question,
        "decision": decision,
        "decision_note": note,
        "knowledge_state": lead.status.value,
        "technical_validation": "not performed; answers are retained as supplied evidence",
        "supported_operations_changed": False,
        "checks": [
            {
                "name": "need coverage",
                "status": "pass" if not missing else "gap",
                "detail": f"{answered}/{len(questions)} declared needs answered",
            },
            {
                "name": "admission gate",
                "status": "pass",
                "detail": "supported_operations is unchanged; no promotion occurs",
            },
            {
                "name": "retirement note",
                "status": "pass" if decision != "retire" or bool(note) else "gap",
                "detail": "a retire decision has a recorded reason" if note else "no retirement note required",
            },
        ],
        "gaps": [
            "supplied answers are not automatically verified as proofs or tests",
            "keeping a lead does not promote it to a mechanism card or supported operation",
            "retirement is recorded, not erased from the pre-admission registry",
        ],
        "headline": (
            f"{lead.id}: {status} ({answered}/{len(questions)} needs answered)"
        ),
    }


def render_resolution(payload: Mapping[str, Any]) -> str:
    """Render the ask/retry/keep-or-retire loop."""
    lead = payload.get("lead") or {}
    lines = ["=" * 78, "HYPOTHESIS RESOLUTION", "=" * 78]
    lines.append(f"lead: {lead.get('id')}")
    lines.append(f"operation: {lead.get('operation')}")
    lines.append(f"status: {payload.get('status')}")
    lines.append(f"knowledge state: {payload.get('knowledge_state')}")
    lines.append("")
    lines.append("Needs")
    for question in payload.get("questions", ()):
        flag = "x" if question.get("answered") else " "
        lines.append(f"  [{flag}] {question.get('id')}: {question.get('need')}")
        if question.get("answer"):
            lines.append(f"      supplied: {question['answer']}")
    lines.append("")
    next_question = payload.get("next_question")
    if next_question:
        lines.append(f"next question: {next_question.get('prompt')}")
        if next_question.get("id") != "decision":
            lines.append(f"  answer id: {next_question.get('id')}")
    if payload.get("decision"):
        lines.append(f"decision: {payload['decision']}")
    if payload.get("decision_note"):
        lines.append(f"note: {payload['decision_note']}")
    lines.append("")
    lines.append(str(payload.get("technical_validation", "")))
    lines.append("supported_operations_changed: false")
    return "\n".join(lines)


def lead_wheel() -> CentWheel:
    """Return the leads in the existing knowledge-state wheel."""
    wheel = CentWheel()
    for lead in LEADS:
        wheel.entries.append(
            CentEntry(
                entry_id=lead.id,
                pound=f"operation:{lead.operation}",
                delta_description=lead.title,
                substrate_domain="undetermined",
                carrier_type="undetermined",
                is_delta_sigma=False,
                status=lead.status,
                params={},
                backing=[lead.source],
                needs=list(lead.needs),
            )
        )
    return wheel


def _wheel_payload(wheel: CentWheel) -> dict[str, Any]:
    summary = wheel.summary()
    return {
        "summary": summary,
        "rings": {
            state.value: [entry.entry_id for entry in wheel.ring(state)]
            for state in KnowledgeState
        },
        "claim": "knowledge-state labels describe evidence status, not implementation support",
    }


def _lead_matches(operation: str, behavior: BehaviorSignature) -> list[dict[str, Any]]:
    matches = []
    for lead in LEADS:
        if lead.operation != operation:
            continue
        score, reasons = _score(behavior, lead.behavior)
        matches.append({
            **lead.as_dict(),
            "score": score,
            "structural_overlap": sorted(
                set(behavior.primitive_chain) & set(lead.behavior.primitive_chain)
            ),
            "reasons": reasons,
            "admission": "pre_admission_lead",
        })
    return matches


def _card_matches(operation: str, behavior: BehaviorSignature) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    admitted = []
    pre_admission = []
    for card in MECHANISM_CARDS:
        candidate_behavior = MECHANISM_BEHAVIORS[card.id]
        score, reasons = _score(behavior, candidate_behavior)
        structural_overlap = sorted(
            set(behavior.primitive_chain) & set(candidate_behavior.primitive_chain)
        )
        if operation in card.supported_operations:
            admitted.append({
                "mechanism": card.id,
                "name": card.name,
                "evidence_level": card.evidence_level,
                "score": score,
                "reasons": reasons,
                "admission": "supported_operation",
                "supported_operations_changed": False,
            })
        elif score >= MIN_STRUCTURAL_SCORE and structural_overlap:
            pre_admission.append({
                "mechanism": card.id,
                "name": card.name,
                "evidence_level": card.evidence_level,
                "score": score,
                "structural_overlap": structural_overlap,
                "reasons": reasons,
                "admission": "pre_admission_card",
                "status": KnowledgeState.DOESNT_KNOW.value,
                "needs": [
                    "proof:operation-specific behavior equivalence",
                    "test:declared operation reference and negative control",
                ],
                "supported_operations_changed": False,
            })
    admitted.sort(key=lambda item: (-item["score"], item["mechanism"]))
    pre_admission.sort(key=lambda item: (-item["score"], item["mechanism"]))
    return admitted, pre_admission


def list_payload() -> dict[str, Any]:
    """List all pre-admission leads and their wheel state."""
    wheel = lead_wheel()
    return {
        "ok": True,
        "schema": SCHEMA,
        "mode": "list",
        "leads": [lead.as_dict() for lead in LEADS],
        "wheel": _wheel_payload(wheel),
        "summary": {
            "leads": len(LEADS),
            "operations": sorted({lead.operation for lead in LEADS}),
            "known": len(wheel.ring(KnowledgeState.KNOWS)),
            "thinks_true": len(wheel.ring(KnowledgeState.THINKS_TRUE)),
            "doesnt_know": len(wheel.ring(KnowledgeState.DOESNT_KNOW)),
            "needs": len(wheel.ring(KnowledgeState.NEEDS)),
        },
        "gaps": [
            "leads are not mechanism cards, operation contracts or transfer candidates",
            "no lead changes any mechanism's supported_operations",
            "no lead is validated or admitted by this view",
        ],
        "headline": (
            f"{len(LEADS)} pre-admission lead(s) across "
            f"{len({lead.operation for lead in LEADS})} operation(s); "
            "none is admitted."
        ),
    }


def match_operation(operation: str) -> dict[str, Any]:
    """Score an operation against admitted cards, unadmitted cards and leads."""
    key = str(operation or "").strip()
    if key not in _OPERATION_BEHAVIORS:
        known = ", ".join(sorted(_OPERATION_BEHAVIORS))
        raise ValueError(f"unknown hypothesis operation: {key!r}; known: {known}")
    behavior = _OPERATION_BEHAVIORS[key]
    admitted, pre_admission = _card_matches(key, behavior)
    leads = _lead_matches(key, behavior)
    wheel = lead_wheel()
    return {
        "ok": True,
        "schema": SCHEMA,
        "mode": "match",
        "operation": key,
        "behavior": behavior.as_dict(),
        "admitted": admitted,
        "pre_admission": pre_admission,
        "leads": leads,
        "wheel": _wheel_payload(wheel),
        "summary": {
            "admitted": len(admitted),
            "pre_admission": len(pre_admission),
            "leads": len(leads),
            "supported_operations_changed": False,
        },
        "checks": [
            {
                "name": "admission gate",
                "status": "pass",
                "detail": "supported_operations is unchanged; matches are pre-admission",
            },
            {
                "name": "knowledge state",
                "status": "pass",
                "detail": "leads carry explicit DOESN'T-KNOW or NEEDS state and needs",
            },
        ],
        "gaps": [
            "pre-admission cards require a primitive-chain overlap and a declared threshold; they are not operation contracts",
            "leads require a separate mechanism card, reference test and review",
            "no transfer candidate or target artifact is created",
        ],
        "headline": (
            f"{len(admitted)} supported card(s), {len(pre_admission)} pre-admission "
            f"card(s), {len(leads)} lead(s) for {key}; no promotion."
        ),
    }


def render_text(payload: Mapping[str, Any]) -> str:
    lines = ["=" * 78, "PRE-ADMISSION HYPOTHESES", "=" * 78]
    lines.append(str(payload.get("headline", "")))
    if payload.get("mode") == "match":
        lines.append(f"operation: {payload['operation']}")
        lines.append("")
        if payload.get("admitted"):
            lines.append("Supported mechanisms (unchanged)")
            for item in payload["admitted"]:
                lines.append(f"  {item['mechanism']}: {item['evidence_level']}")
        if payload.get("pre_admission"):
            lines.append("Pre-admission card matches")
            for item in payload["pre_admission"]:
                lines.append(
                    f"  {item['mechanism']} score={item['score']} "
                    f"[{item['status']}]"
                )
                lines.append("    needs: " + "; ".join(item["needs"]))
        if payload.get("leads"):
            lines.append("Leads")
            for item in payload["leads"]:
                lines.append(f"  {item['id']} [{item['status']}]")
                lines.append(f"    {item['title']}")
                lines.append("    needs: " + "; ".join(item["needs"]))
    else:
        for item in payload.get("leads", ()):
            lines.append(f"  {item['id']} [{item['status']}] -> {item['operation']}")
            lines.append(f"    {item['title']}")
            lines.append("    needs: " + "; ".join(item["needs"]))
    wheel = payload.get("wheel", {})
    rings = wheel.get("summary", {}).get("rings", {})
    lines.append("")
    lines.append(
        "wheel: "
        + ", ".join(f"{key}={value}" for key, value in rings.items())
    )
    lines.append("No lead was promoted; supported_operations is unchanged.")
    return "\n".join(lines)


__all__ = [
    "SCHEMA", "RESOLUTION_SCHEMA", "HypothesisLead", "LEADS", "LEAD_BY_ID",
    "lead_wheel", "list_payload", "match_operation", "render_text",
    "questions_for", "resolve_lead", "render_resolution",
]
