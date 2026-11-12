"""Declared G5b retrieval evaluation for the transfer compiler.

The corpus is deliberately small and explicit.  ``known-valid`` means a
production mechanism card declares support for the operation; it does not mean
the transfer is target-validated.  ``known-invalid`` cases are negative controls
where a shared primitive or structure must not create a candidate.
``unadapted`` operations have no declared mechanism at all, and ``refused``
operations have no production operation contract.

Target pass rate covers only the declared executable ``glm-reference`` adapter
pairs.  Everything else remains an explicit gap, not a failed measurement.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .mechanisms import MECHANISM_BY_ID
from .targets import glm
from .transfer_engine import OPERATION_BY_ID, retrieve
from .transfer_validation import validate_transfer

EVALUATION_SCHEMA = "cent-transfer-evaluation/1"
ALGORITHM = "declared-mechanism-corpus/1"


def _text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty text")
    return text


def _texts(value: Any, field_name: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if isinstance(value, str):
        value = (value,)
    if value is None:
        raise ValueError(f"{field_name} must be a sequence of strings")
    try:
        items = tuple(_text(item, field_name) for item in value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a sequence of strings") from exc
    if not items and not allow_empty:
        raise ValueError(f"{field_name} must contain at least one entry")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    return items


def _ratio(numerator: int, denominator: int) -> str:
    return f"{numerator}/{denominator}"


@dataclass(frozen=True)
class PositiveCase:
    id: str
    operation: str
    expected_mechanisms: tuple[str, ...]
    rationale: str
    provenance: tuple[str, ...]

    def validate(self) -> None:
        _text(self.id, "evaluation.case.id")
        _text(self.operation, "evaluation.case.operation")
        _texts(self.expected_mechanisms, "evaluation.case.expected_mechanisms")
        _text(self.rationale, "evaluation.case.rationale")
        _texts(self.provenance, "evaluation.case.provenance")
        if self.operation not in OPERATION_BY_ID:
            raise ValueError(f"evaluation case has unknown operation {self.operation!r}")
        for mechanism_id in self.expected_mechanisms:
            card = MECHANISM_BY_ID.get(mechanism_id)
            if card is None:
                raise ValueError(
                    f"evaluation case names unknown mechanism {mechanism_id!r}"
                )
            if self.operation not in card.supported_operations:
                raise ValueError(
                    f"mechanism {mechanism_id!r} does not declare "
                    f"support for {self.operation!r}"
                )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": "known-valid",
            "operation": self.operation,
            "expected_mechanisms": list(self.expected_mechanisms),
            "rationale": self.rationale,
            "provenance": list(self.provenance),
        }


@dataclass(frozen=True)
class NegativeControl:
    id: str
    operation: str
    forbidden_mechanisms: tuple[str, ...]
    rationale: str
    provenance: tuple[str, ...]

    def validate(self) -> None:
        _text(self.id, "evaluation.negative.id")
        _text(self.operation, "evaluation.negative.operation")
        _texts(
            self.forbidden_mechanisms,
            "evaluation.negative.forbidden_mechanisms",
        )
        _text(self.rationale, "evaluation.negative.rationale")
        _texts(self.provenance, "evaluation.negative.provenance")
        if self.operation not in OPERATION_BY_ID:
            raise ValueError(
                f"negative control has unknown operation {self.operation!r}"
            )
        for mechanism_id in self.forbidden_mechanisms:
            card = MECHANISM_BY_ID.get(mechanism_id)
            if card is None:
                raise ValueError(
                    f"negative control names unknown mechanism {mechanism_id!r}"
                )
            if self.operation in card.supported_operations:
                raise ValueError(
                    f"negative control forbids a declared support: "
                    f"{mechanism_id!r} supports {self.operation!r}"
                )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": "known-invalid",
            "operation": self.operation,
            "forbidden_mechanisms": list(self.forbidden_mechanisms),
            "rationale": self.rationale,
            "provenance": list(self.provenance),
        }


@dataclass(frozen=True)
class UnadaptedCase:
    id: str
    operation: str
    rationale: str
    provenance: tuple[str, ...]

    def validate(self) -> None:
        _text(self.id, "evaluation.unadapted.id")
        _text(self.operation, "evaluation.unadapted.operation")
        _text(self.rationale, "evaluation.unadapted.rationale")
        _texts(self.provenance, "evaluation.unadapted.provenance")
        if self.operation not in OPERATION_BY_ID:
            raise ValueError(
                f"unadapted case has unknown operation {self.operation!r}"
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": "unadapted",
            "operation": self.operation,
            "expected_mechanisms": [],
            "rationale": self.rationale,
            "provenance": list(self.provenance),
        }


@dataclass(frozen=True)
class UnadaptedRefusal:
    """A supported candidate that T1 refuses to adapt without inventing a law."""

    id: str
    operation: str
    mechanism: str
    rationale: str
    required_evidence: tuple[str, ...]
    provenance: tuple[str, ...]

    def validate(self) -> None:
        _text(self.id, "evaluation.refusal.id")
        _text(self.operation, "evaluation.refusal.operation")
        _text(self.mechanism, "evaluation.refusal.mechanism")
        _text(self.rationale, "evaluation.refusal.rationale")
        _texts(self.required_evidence, "evaluation.refusal.required_evidence")
        _texts(self.provenance, "evaluation.refusal.provenance")
        if self.operation not in OPERATION_BY_ID:
            raise ValueError(
                f"refusal has unknown operation {self.operation!r}"
            )
        card = MECHANISM_BY_ID.get(self.mechanism)
        if card is None:
            raise ValueError(
                f"refusal names unknown mechanism {self.mechanism!r}"
            )
        if self.operation not in card.supported_operations:
            raise ValueError(
                f"mechanism {self.mechanism!r} does not declare "
                f"support for {self.operation!r}"
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": "unadapted-refusal",
            "operation": self.operation,
            "mechanism": self.mechanism,
            "rationale": self.rationale,
            "required_evidence": list(self.required_evidence),
            "provenance": list(self.provenance),
        }


@dataclass(frozen=True)
class RefusedCase:
    id: str
    operation: str
    rationale: str
    provenance: tuple[str, ...]

    def validate(self) -> None:
        _text(self.id, "evaluation.refused.id")
        _text(self.operation, "evaluation.refused.operation")
        _text(self.rationale, "evaluation.refused.rationale")
        _texts(self.provenance, "evaluation.refused.provenance")
        if self.operation in OPERATION_BY_ID:
            raise ValueError(
                f"refused case names a production operation: {self.operation!r}"
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": "refused",
            "operation": self.operation,
            "expected_mechanisms": [],
            "rationale": self.rationale,
            "provenance": list(self.provenance),
        }


POSITIVE_CASES: tuple[PositiveCase, ...] = (
    PositiveCase(
        id="sqrt-declared-mechanisms",
        operation="sqrt",
        expected_mechanisms=(
            "cam-profile",
            "log-domain-sqrt",
            "orifice-pressure-flow",
        ),
        rationale=(
            "Three cards explicitly declare sqrt support; one is source-simulated "
            "and two are structural."
        ),
        provenance=("cent_compiler/mechanisms.py",),
    ),
    PositiveCase(
        id="sum-declared-mechanisms",
        operation="sum",
        expected_mechanisms=(
            "fluid-continuity", "kcl-conservation", "opamp-summing"
        ),
        rationale=(
            "The KCL, fluid and op-amp cards explicitly declare exact-sum support."
        ),
        provenance=("cent_compiler/mechanisms.py",),
    ),
    PositiveCase(
        id="difference-declared-mechanisms",
        operation="difference",
        expected_mechanisms=(
            "fluid-continuity", "kcl-conservation", "opamp-summing"
        ),
        rationale=(
            "The KCL, fluid and op-amp cards explicitly declare exact-difference support."
        ),
        provenance=("cent_compiler/mechanisms.py",),
    ),
    PositiveCase(
        id="quantized-carry-declared-mechanism",
        operation="quantized_carry",
        expected_mechanisms=("delta-sigma-error-feedback",),
        rationale="The delta-sigma card explicitly declares quantized-carry support.",
        provenance=("cent_compiler/mechanisms.py",),
    ),
)

NEGATIVE_CONTROLS: tuple[NegativeControl, ...] = (
    NegativeControl(
        id="mult-not-orifice",
        operation="mult",
        forbidden_mechanisms=("orifice-pressure-flow",),
        rationale=(
            "The orifice card contains a mult primitive but declares only sqrt "
            "support; primitive overlap must not create a transfer."
        ),
        provenance=("cent_compiler/mechanisms.py",),
    ),
    NegativeControl(
        id="log-not-log-domain-sqrt",
        operation="log",
        forbidden_mechanisms=("log-domain-sqrt",),
        rationale=(
            "The log-domain card contains log and exp primitives but declares "
            "only sqrt support."
        ),
        provenance=("cent_compiler/mechanisms.py",),
    ),
    NegativeControl(
        id="exp-not-log-domain-sqrt",
        operation="exp",
        forbidden_mechanisms=("log-domain-sqrt",),
        rationale=(
            "The log-domain card contains an exp primitive but declares only "
            "sqrt support."
        ),
        provenance=("cent_compiler/mechanisms.py",),
    ),
    NegativeControl(
        id="sqrt-not-delta-sigma",
        operation="sqrt",
        forbidden_mechanisms=("delta-sigma-error-feedback",),
        rationale=(
            "Delta-sigma is a quantized-carry mechanism; it must not appear for "
            "sqrt merely because both are nonlinear operations."
        ),
        provenance=("cent_compiler/mechanisms.py",),
    ),
    NegativeControl(
        id="quantized-carry-not-pll",
        operation="quantized_carry",
        forbidden_mechanisms=("pll-phase-tracking",),
        rationale=(
            "The PLL card is stateful and feedback-based but supports phase and "
            "frequency operations, not quantized carry."
        ),
        provenance=("cent_compiler/mechanisms.py",),
    ),
)

UNADAPTED_CASES: tuple[UnadaptedCase, ...] = (
    UnadaptedCase(
        id="mult-no-declared-mechanism",
        operation="mult",
        rationale="No production mechanism card declares mult support.",
        provenance=("cent_compiler/mechanisms.py",),
    ),
    UnadaptedCase(
        id="div-no-declared-mechanism",
        operation="div",
        rationale="No production mechanism card declares div support.",
        provenance=("cent_compiler/mechanisms.py",),
    ),
    UnadaptedCase(
        id="exp-no-declared-mechanism",
        operation="exp",
        rationale="No production mechanism card declares exp support.",
        provenance=("cent_compiler/mechanisms.py",),
    ),
    UnadaptedCase(
        id="log-no-declared-mechanism",
        operation="log",
        rationale="No production mechanism card declares log support.",
        provenance=("cent_compiler/mechanisms.py",),
    ),
    UnadaptedCase(
        id="reciprocal-no-declared-mechanism",
        operation="reciprocal",
        rationale="No production mechanism card declares reciprocal support.",
        provenance=("cent_compiler/mechanisms.py",),
    ),
    UnadaptedCase(
        id="sign-no-declared-mechanism",
        operation="sign",
        rationale="No production mechanism card declares sign support.",
        provenance=("cent_compiler/mechanisms.py",),
    ),
)

UNADAPTED_REFUSALS: tuple[UnadaptedRefusal, ...] = (
    UnadaptedRefusal(
        id="cam-profile-refusal",
        operation="sqrt",
        mechanism="cam-profile",
        rationale=(
            "No exact cam profile law, fixed profile or displacement range is "
            "declared. A target adapter would invent the geometry, so T1 records "
            "a refusal instead of fabricating one."
        ),
        required_evidence=(
            "an exact cam profile law and declared displacement range",
            "fixed input/output vectors derived from that profile",
            "an independent target implementation with a passing certificate",
        ),
        provenance=(
            "cent_compiler/mechanisms.py",
            "tests/test_transfer_contracts.py",
        ),
    ),
    UnadaptedRefusal(
        id="orifice-pressure-flow-refusal",
        operation="sqrt",
        mechanism="orifice-pressure-flow",
        rationale=(
            "No exact pressure-flow restriction law, calibrated geometry or "
            "fluid properties are declared. A target adapter would invent the "
            "calibration, so T1 records a refusal instead of fabricating one."
        ),
        required_evidence=(
            "an exact pressure-flow restriction law with declared fluid properties",
            "fixed pressure/flow vectors from that calibration",
            "an independent target implementation with a passing certificate",
        ),
        provenance=(
            "cent_compiler/mechanisms.py",
            "tests/test_transfer_contracts.py",
        ),
    ),
)

REFUSED_CASES: tuple[RefusedCase, ...] = (
    RefusedCase(
        id="griess-product-refused",
        operation="griess_product",
        rationale=(
            "The negative-control name from the transfer specification has no "
            "production operation contract."
        ),
        provenance=("tests/test_transfer_contracts.py",),
    ),
    RefusedCase(
        id="matrix-vector-refused",
        operation="matrix_vector_product",
        rationale=(
            "A generic multiplier must not be accepted as a matrix-vector "
            "transfer; this name has no production contract."
        ),
        provenance=("tests/test_transfer_contracts.py",),
    ),
    RefusedCase(
        id="track-phase-refused",
        operation="track_phase",
        rationale=(
            "The PLL card declares this source operation, but no production "
            "operation contract or target adapter exists, so retrieval refuses it."
        ),
        provenance=("cent_compiler/mechanisms.py", "cent_compiler/transfer_engine.py"),
    ),
)


def validate_corpus() -> None:
    """Validate every declared corpus label against the production registries."""
    ids: list[str] = []
    positive_operations: list[str] = []
    for case in POSITIVE_CASES:
        case.validate()
        ids.append(case.id)
        positive_operations.append(case.operation)
        for mechanism_id in case.expected_mechanisms:
            if case.operation not in MECHANISM_BY_ID[mechanism_id].supported_operations:
                raise ValueError(f"positive case support mismatch: {case.id}")
    for case in NEGATIVE_CONTROLS:
        case.validate()
        ids.append(case.id)
    for case in UNADAPTED_CASES:
        case.validate()
        ids.append(case.id)
        if case.operation in positive_operations:
            raise ValueError(
                f"operation {case.operation!r} cannot be both known-valid and unadapted"
            )
    refusal_keys: set[tuple[str, str]] = set()
    for refusal in UNADAPTED_REFUSALS:
        refusal.validate()
        ids.append(refusal.id)
        key = (refusal.operation, refusal.mechanism)
        if key in refusal_keys:
            raise ValueError(
                f"duplicate unadapted refusal for {refusal.operation}/{refusal.mechanism}"
            )
        refusal_keys.add(key)
        if refusal.operation not in positive_operations:
            raise ValueError(
                f"refusal operation {refusal.operation!r} is not a known-valid case"
            )
    for case in REFUSED_CASES:
        case.validate()
        ids.append(case.id)
    if len(ids) != len(set(ids)):
        raise ValueError("transfer evaluation corpus contains duplicate case ids")
    if len(positive_operations) != len(set(positive_operations)):
        raise ValueError("transfer evaluation has duplicate positive operations")


validate_corpus()


def _complete_retrieval_evidence(candidate: Any) -> bool:
    return bool(
        candidate.evidence_level
        and candidate.mapping
        and candidate.gaps
        and candidate.provenance
        and candidate.relaxation
        and candidate.source_domain
        and candidate.target
    )


def _adapter(operation: str, mechanism: str):
    try:
        return glm.get_adapter(operation, mechanism)
    except (KeyError, ValueError):
        return None


def _positive_result(case: PositiveCase) -> dict[str, Any]:
    operation, _target, candidates, _matches = retrieve(case.operation)
    by_mechanism = {candidate.mechanism: candidate for candidate in candidates}
    retrieved = sorted(by_mechanism)
    expected = sorted(case.expected_mechanisms)
    missing = sorted(set(expected) - set(retrieved))
    unexpected = sorted(set(retrieved) - set(expected))
    evidence_total = len(expected)
    evidence_complete = sum(
        1
        for mechanism_id in expected
        if mechanism_id in by_mechanism
        and _complete_retrieval_evidence(by_mechanism[mechanism_id])
    )
    return {
        "id": case.id,
        "kind": "known-valid",
        "operation": case.operation,
        "expected": expected,
        "retrieved": retrieved,
        "missing": missing,
        "unexpected": unexpected,
        "passed": not missing and not unexpected,
        "evidence_total": evidence_total,
        "evidence_complete": evidence_complete,
        "adapter_available": [
            mechanism_id
            for mechanism_id in expected
            if _adapter(case.operation, mechanism_id) is not None
        ],
        "unadapted": [
            mechanism_id
            for mechanism_id in expected
            if _adapter(case.operation, mechanism_id) is None
        ],
        "candidates": [
            {
                "mechanism": mechanism_id,
                "evidence_level": by_mechanism[mechanism_id].evidence_level,
                "tests": list(by_mechanism[mechanism_id].tests),
                "artifact": by_mechanism[mechanism_id].artifact is not None,
                "gaps": list(by_mechanism[mechanism_id].gaps),
            }
            for mechanism_id in expected
            if mechanism_id in by_mechanism
        ],
        "rationale": case.rationale,
        "provenance": list(case.provenance),
    }


def _negative_result(
    case: NegativeControl,
    allowed_by_operation: Mapping[str, set[str]],
) -> dict[str, Any]:
    _operation, _target, candidates, _matches = retrieve(case.operation)
    retrieved = sorted(candidate.mechanism for candidate in candidates)
    forbidden = sorted(set(retrieved) & set(case.forbidden_mechanisms))
    allowed = allowed_by_operation.get(case.operation, set())
    unexpected = sorted(set(retrieved) - allowed)
    return {
        "id": case.id,
        "kind": "known-invalid",
        "operation": case.operation,
        "forbidden": sorted(case.forbidden_mechanisms),
        "retrieved": retrieved,
        "forbidden_hits": forbidden,
        "unexpected": unexpected,
        "passed": not forbidden and not unexpected,
        "rationale": case.rationale,
        "provenance": list(case.provenance),
    }


def _unadapted_result(case: UnadaptedCase) -> dict[str, Any]:
    _operation, _target, candidates, _matches = retrieve(case.operation)
    retrieved = sorted(candidate.mechanism for candidate in candidates)
    return {
        "id": case.id,
        "kind": "unadapted",
        "operation": case.operation,
        "expected": [],
        "retrieved": retrieved,
        "passed": not retrieved,
        "rationale": case.rationale,
        "provenance": list(case.provenance),
    }


def _refused_result(case: RefusedCase) -> dict[str, Any]:
    try:
        retrieve(case.operation)
    except KeyError as exc:
        return {
            "id": case.id,
            "kind": "refused",
            "operation": case.operation,
            "passed": "unknown operation contract" in str(exc),
            "detail": str(exc),
            "rationale": case.rationale,
            "provenance": list(case.provenance),
        }
    return {
        "id": case.id,
        "kind": "refused",
        "operation": case.operation,
        "passed": False,
        "detail": "operation was accepted by the production registry",
        "rationale": case.rationale,
        "provenance": list(case.provenance),
    }


def _target_results(positive: tuple[dict[str, Any], ...]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    unadapted: list[dict[str, Any]] = []
    for case in positive:
        for mechanism_id in case["adapter_available"]:
            try:
                payload = validate_transfer(
                    case["operation"],
                    mechanism_id=mechanism_id,
                )
                certificate = payload.get("certificate") or {}
                validated = payload.get("validated_candidate") or {}
                passed = (
                    payload.get("ok") is True
                    and certificate.get("status") == "pass"
                )
                rows.append(
                    {
                        "operation": case["operation"],
                        "mechanism": mechanism_id,
                        "status": "pass" if passed else "fail",
                        "certificate": certificate.get("status"),
                        "evidence_level": certificate.get("evidence_level"),
                        "tests": list(validated.get("tests") or ()),
                        "artifact": validated.get("artifact") is not None,
                        "vectors": (payload.get("metrics") or {}).get("vectors", 0),
                    }
                )
            except (KeyError, ValueError) as exc:
                rows.append(
                    {
                        "operation": case["operation"],
                        "mechanism": mechanism_id,
                        "status": "fail",
                        "certificate": "fail",
                        "evidence_level": "not established",
                        "tests": [],
                        "artifact": False,
                        "vectors": 0,
                        "detail": str(exc),
                    }
                )
        for mechanism_id in case["unadapted"]:
            candidate = next(
                item
                for item in case["candidates"]
                if item["mechanism"] == mechanism_id
            )
            unadapted.append(
                {
                    "operation": case["operation"],
                    "mechanism": mechanism_id,
                    "gaps": candidate["gaps"],
                }
            )
    return rows, unadapted


def evaluate_corpus() -> dict[str, Any]:
    """Measure the declared retrieval corpus and executable target pairs."""
    positive_rows = tuple(_positive_result(case) for case in POSITIVE_CASES)
    allowed_by_operation: dict[str, set[str]] = {}
    for case in POSITIVE_CASES:
        allowed_by_operation.setdefault(case.operation, set()).update(
            case.expected_mechanisms
        )
    negative_rows = tuple(
        _negative_result(case, allowed_by_operation) for case in NEGATIVE_CONTROLS
    )
    unadapted_rows = tuple(_unadapted_result(case) for case in UNADAPTED_CASES)
    refused_rows = tuple(_refused_result(case) for case in REFUSED_CASES)
    target_rows, unadapted_candidates = _target_results(positive_rows)
    unadapted_keys = {
        (row["operation"], row["mechanism"])
        for row in unadapted_candidates
    }
    refusal_keys = {
        (refusal.operation, refusal.mechanism)
        for refusal in UNADAPTED_REFUSALS
    }
    refusal_missing = sorted(unadapted_keys - refusal_keys)
    refusal_stale = sorted(refusal_keys - unadapted_keys)
    refusal_failures = [
        f"{operation}/{mechanism}"
        for operation, mechanism in (*refusal_missing, *refusal_stale)
    ]

    expected_total = sum(len(case["expected"]) for case in positive_rows)
    retrieved_expected = sum(
        len(set(case["expected"]) & set(case["retrieved"]))
        for case in positive_rows
    )
    case_passed = sum(1 for case in positive_rows if case["passed"])
    missing = [
        f"{case['operation']}/{mechanism_id}"
        for case in positive_rows
        for mechanism_id in case["missing"]
    ]
    unlabelled = [
        f"{case['operation']}/{mechanism_id}"
        for case in positive_rows
        for mechanism_id in case["unexpected"]
    ]
    negative_failures = [case["id"] for case in negative_rows if not case["passed"]]
    negative_false_positives = [
        f"{case['operation']}/{mechanism_id}"
        for case in negative_rows
        for mechanism_id in sorted(
            set(case["forbidden_hits"]) | set(case["unexpected"])
        )
    ]
    unadapted_failures = [case["id"] for case in unadapted_rows if not case["passed"]]
    refused_failures = [case["id"] for case in refused_rows if not case["passed"]]

    target_passed = sum(1 for row in target_rows if row["status"] == "pass")
    target_failed = len(target_rows) - target_passed
    artifacts = sum(1 for row in target_rows if row["artifact"])
    retrieval_evidence_complete = sum(
        case["evidence_complete"] for case in positive_rows
    )
    target_evidence_complete = sum(
        1
        for row in target_rows
        if row["status"] == "pass" and row["tests"] and row["artifact"]
    )
    unadapted_count = len(unadapted_candidates)
    false_positive_candidates = sorted(
        set(unlabelled) | set(negative_false_positives)
    )

    checks = [
        {
            "name": "known-valid candidate recall",
            "status": "pass" if retrieved_expected == expected_total else "gap",
            "detail": f"{retrieved_expected}/{expected_total} expected candidate(s) retrieved",
        },
        {
            "name": "known-valid case recall",
            "status": "pass" if case_passed == len(positive_rows) else "gap",
            "detail": f"{case_passed}/{len(positive_rows)} case(s) complete",
        },
        {
            "name": "negative controls",
            "status": "pass" if not negative_failures else "gap",
            "detail": (
                f"{len(negative_rows) - len(negative_failures)}/{len(negative_rows)} "
                "control(s) passed"
            ),
        },
        {
            "name": "unadapted operations",
            "status": "pass" if not unadapted_failures else "gap",
            "detail": (
                f"{len(unadapted_rows) - len(unadapted_failures)}/{len(unadapted_rows)} "
                "operation(s) remain unretrieved"
            ),
        },
        {
            "name": "refused operations",
            "status": "pass" if not refused_failures else "gap",
            "detail": (
                f"{len(refused_rows) - len(refused_failures)}/{len(refused_rows)} "
                "unknown operation(s) refused"
            ),
        },
        {
            "name": "target pass rate",
            "status": "pass" if target_failed == 0 else "gap",
            "detail": f"{target_passed}/{len(target_rows)} executable pair(s) passed",
        },
        {
            "name": "retrieval evidence completeness",
            "status": (
                "pass" if retrieval_evidence_complete == expected_total else "gap"
            ),
            "detail": (
                f"{retrieval_evidence_complete}/{expected_total} expected "
                "candidate(s) carry complete retrieval evidence"
            ),
        },
        {
            "name": "target evidence completeness",
            "status": (
                "pass" if target_evidence_complete == len(target_rows) else "gap"
            ),
            "detail": (
                f"{target_evidence_complete}/{len(target_rows)} target row(s) "
                "carry tests and an artifact"
            ),
        },
        {
            "name": "no unlabelled false positives",
            "status": "pass" if not false_positive_candidates else "gap",
            "detail": (
                f"{len(false_positive_candidates)} unlabelled candidate(s)"
            ),
        },
        {
            "name": "unadapted candidate refusals",
            "status": "pass" if not refusal_failures else "gap",
            "detail": (
                f"{len(UNADAPTED_REFUSALS)} refusal record(s); "
                f"missing={len(refusal_missing)}, stale={len(refusal_stale)}"
            ),
        },
    ]
    gaps = [
        (
            "known-valid is declared mechanism support, not independent external "
            "ground truth; the corpus cannot establish a mechanism that no card declares"
        ),
        (
            "the six zero-mechanism operations are valid operation contracts with no "
            "declared transfer, not invalid operations"
        ),
        (
            "target pass rate covers only the five glm-reference adapter pairs; no "
            "live GLM, physical or measured target is exercised"
        ),
        (
            "the corpus is fixed and small; it reports regression and false-positive "
            "control, not general retrieval quality"
        ),
        (
            "the two remaining supported candidates carry T1 refusal records, not "
            "evidence that their mechanisms are impossible; new exact laws reopen them"
        ),
    ]
    ok = all(check["status"] == "pass" for check in checks)
    return {
        "ok": ok,
        "schema": EVALUATION_SCHEMA,
        "algorithm": ALGORITHM,
        "target": glm.GLM_REFERENCE_TARGET.as_dict(),
        "corpus": {
            "known_valid": [case.as_dict() for case in POSITIVE_CASES],
            "known_invalid": [case.as_dict() for case in NEGATIVE_CONTROLS],
            "unadapted": [case.as_dict() for case in UNADAPTED_CASES],
            "refused": [case.as_dict() for case in REFUSED_CASES],
        },
        "known_valid": list(positive_rows),
        "known_invalid": list(negative_rows),
        "unadapted": list(unadapted_rows),
        "refused": list(refused_rows),
        "targets": target_rows,
        "unadapted_candidates": unadapted_candidates,
        "unadapted_refusals": [
            refusal.as_dict() for refusal in UNADAPTED_REFUSALS
        ],
        "metrics": {
            "expected_candidates": expected_total,
            "retrieved_expected_candidates": retrieved_expected,
            "candidate_recall": _ratio(retrieved_expected, expected_total),
            "case_recall": _ratio(case_passed, len(positive_rows)),
            "missing_candidates": missing,
            "unlabelled_candidates": unlabelled,
            "negative_control_failures": len(negative_failures),
            "negative_control_pass_rate": _ratio(
                len(negative_rows) - len(negative_failures), len(negative_rows)
            ),
            "false_positive_candidates": false_positive_candidates,
            "false_positive_rate": _ratio(
                len(negative_failures), len(negative_rows)
            ),
            "unadapted_operations": len(unadapted_rows),
            "unadapted_retrievals": len(unadapted_failures),
            "unadapted_candidates": unadapted_count,
            "unadapted_refusals": len(UNADAPTED_REFUSALS),
            "unadapted_refusal_failures": refusal_failures,
            "target_testable": len(target_rows),
            "target_passed": target_passed,
            "target_failed": target_failed,
            "target_pass_rate": _ratio(target_passed, len(target_rows)),
            "artifact_count": artifacts,
            "retrieval_evidence_complete": retrieval_evidence_complete,
            "retrieval_evidence_total": expected_total,
            "retrieval_evidence_completeness": _ratio(
                retrieval_evidence_complete, expected_total
            ),
            "target_evidence_complete": target_evidence_complete,
            "target_evidence_total": len(target_rows),
            "target_evidence_completeness": _ratio(
                target_evidence_complete, len(target_rows)
            ),
        },
        "checks": checks,
        "gaps": gaps,
        "headline": (
            f"{retrieved_expected}/{expected_total} expected candidates retrieved; "
            f"{len(negative_rows) - len(negative_failures)}/{len(negative_rows)} "
            f"negative controls passed; {target_passed}/{len(target_rows)} target "
            "pairs passed."
        ),
    }


def render_evaluation(payload: Mapping[str, Any]) -> str:
    """Render the evaluation as a compact terminal report."""
    metrics = payload.get("metrics") or {}
    lines = [
        "=" * 78,
        "TRANSFER RETRIEVAL EVALUATION",
        "=" * 78,
        str(payload.get("headline") or ""),
        f"algorithm: {payload.get('algorithm')} · target: {(payload.get('target') or {}).get('id')}",
        "",
        "Known-valid cases",
    ]
    for case in payload.get("known_valid") or ():
        lines.append(
            f"  [{ 'pass' if case.get('passed') else 'gap' }] {case.get('operation')}: "
            f"{len(set(case.get('expected') or ()) & set(case.get('retrieved') or ()))}"
            f"/{len(case.get('expected') or ())} expected; "
            f"retrieved={','.join(case.get('retrieved') or ()) or 'none'}"
        )
        if case.get("missing"):
            lines.append("    missing: " + ", ".join(case["missing"]))
        if case.get("unexpected"):
            lines.append("    unexpected: " + ", ".join(case["unexpected"]))
    lines.append("")
    lines.append("Negative controls")
    for case in payload.get("known_invalid") or ():
        lines.append(
            f"  [{ 'pass' if case.get('passed') else 'gap' }] {case.get('operation')}: "
            f"forbidden={','.join(case.get('forbidden') or ())} "
            f"retrieved={','.join(case.get('retrieved') or ()) or 'none'}"
        )
    lines.append("")
    lines.append("Unadapted operations")
    for case in payload.get("unadapted") or ():
        lines.append(
            f"  [{ 'pass' if case.get('passed') else 'gap' }] {case.get('operation')}: "
            f"retrieved={','.join(case.get('retrieved') or ()) or 'none'}"
        )
    lines.append("")
    lines.append("Unadapted candidate refusals")
    for refusal in payload.get("unadapted_refusals") or ():
        lines.append(
            f"  [refused] {refusal.get('operation')}/{refusal.get('mechanism')}: "
            f"{refusal.get('rationale')}"
        )
        lines.append(
            "    required: " + "; ".join(refusal.get("required_evidence") or ())
        )
    lines.append("")
    lines.append("Metrics")
    for key in (
        "candidate_recall",
        "case_recall",
        "false_positive_rate",
        "target_pass_rate",
        "retrieval_evidence_completeness",
        "target_evidence_completeness",
        "artifact_count",
        "unadapted_candidates",
    ):
        lines.append(f"  {key}: {metrics.get(key)}")
    lines.append("")
    lines.append("Checks")
    for check in payload.get("checks") or ():
        lines.append(f"  [{check.get('status')}] {check.get('name')}: {check.get('detail')}")
    lines.append("")
    lines.append("Remaining gaps")
    for gap in payload.get("gaps") or ():
        lines.append(f"  - {gap}")
    return "\n".join(lines)


__all__ = [
    "ALGORITHM",
    "EVALUATION_SCHEMA",
    "NEGATIVE_CONTROLS",
    "POSITIVE_CASES",
    "REFUSED_CASES",
    "UNADAPTED_CASES",
    "UNADAPTED_REFUSALS",
    "UnadaptedRefusal",
    "evaluate_corpus",
    "render_evaluation",
    "validate_corpus",
]
