"""Transfer candidates for the Cent transfer compiler.

A transfer candidate connects an operation contract, a mechanism card and a
target context.  It records the mapping steps, what is preserved or relaxed,
and the evidence still required.  A candidate is not a validated transfer until
it has a target artifact and target tests.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from .mechanisms import MechanismCard

SCHEMA = "cent-transfer/1"
TARGET_SCHEMA = "cent-target/1"

STATUSES = frozenset({"candidate", "validated", "rejected"})
EVIDENCE_LEVELS = (
    "proposed",
    "structural",
    "admissible",
    "source-simulated",
    "target-simulated",
    "target-integrated",
)
from .mapping import MAPPING_KINDS
TARGET_KINDS = frozenset({"software", "physical", "information", "mixed"})
RELAXATION_SCHEMA = "cent-relaxation/1"
RELAXATION_CLASSES = frozenset(
    {"exact", "asymptotic", "parameter-dependent", "unclassified"}
)
RELAXATION_EVIDENCE_LEVELS = frozenset({"none", *EVIDENCE_LEVELS})
TARGET_RELAXATION_EVIDENCE = frozenset({"target-simulated", "target-integrated"})
DEFAULT_RELAXATION_BASIS = "no target-level relaxation evidence; candidate-only"

_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")


def _text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty text")
    return text


def _identifier(value: Any, field_name: str) -> str:
    text = _text(value, field_name)
    if not _ID_RE.fullmatch(text):
        raise ValueError(f"{field_name} must match {_ID_RE.pattern!s}: {text!r}")
    return text


def _text_tuple(value: Any, field_name: str, *, allow_empty: bool = False) -> tuple[str, ...]:
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


@dataclass(frozen=True)
class MappingStep:
    """One declared correspondence in a transfer mapping."""

    source: str
    target: str
    law: str
    kind: str = "correspondence"
    provenance: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()

    def validate(self) -> None:
        _text(self.source, "mapping.source")
        _text(self.target, "mapping.target")
        _text(self.law, "mapping.law")
        if self.kind not in MAPPING_KINDS:
            raise ValueError(
                f"mapping.kind must be one of {sorted(MAPPING_KINDS)}: {self.kind!r}"
            )
        _text_tuple(self.provenance, "mapping.provenance")
        _text_tuple(self.gaps, "mapping.gaps", allow_empty=True)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "law": self.law,
            "kind": self.kind,
            "provenance": list(self.provenance),
            "gaps": list(self.gaps),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MappingStep":
        if not isinstance(data, Mapping):
            raise ValueError("mapping step must be a mapping")
        return cls(
            source=str(data.get("source", "")),
            target=str(data.get("target", "")),
            law=str(data.get("law", "")),
            kind=str(data.get("kind", "correspondence")),
            provenance=_text_tuple(
                data.get("provenance", ()), "mapping.provenance"
            ),
            gaps=_text_tuple(data.get("gaps", ()), "mapping.gaps", allow_empty=True),
        )


@dataclass(frozen=True)
class TargetProfile:
    """A target context and its declared validation contract."""

    id: str
    kind: str
    description: str
    interface: Mapping[str, Any]
    constraints: Mapping[str, Any]
    evidence_required: tuple[str, ...]
    provenance: tuple[str, ...]
    gaps: tuple[str, ...] = ()
    schema: str = TARGET_SCHEMA

    def validate(self) -> None:
        if self.schema != TARGET_SCHEMA:
            raise ValueError(f"target.schema must be {TARGET_SCHEMA!r}: {self.schema!r}")
        _identifier(self.id, "target.id")
        if self.kind not in TARGET_KINDS:
            raise ValueError(
                f"target.kind must be one of {sorted(TARGET_KINDS)}: {self.kind!r}"
            )
        _text(self.description, "target.description")
        if not isinstance(self.interface, Mapping):
            raise ValueError("target.interface must be a mapping")
        if not isinstance(self.constraints, Mapping):
            raise ValueError("target.constraints must be a mapping")
        _text_tuple(self.evidence_required, "target.evidence_required")
        _text_tuple(self.provenance, "target.provenance")
        _text_tuple(self.gaps, "target.gaps", allow_empty=True)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "id": self.id,
            "kind": self.kind,
            "description": self.description,
            "interface": dict(self.interface),
            "constraints": dict(self.constraints),
            "evidence_required": list(self.evidence_required),
            "provenance": list(self.provenance),
            "gaps": list(self.gaps),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TargetProfile":
        if not isinstance(data, Mapping):
            raise ValueError("target profile must be a mapping")
        return cls(
            id=str(data.get("id", "")),
            kind=str(data.get("kind", "")),
            description=str(data.get("description", "")),
            interface=data.get("interface", {}),
            constraints=data.get("constraints", {}),
            evidence_required=_text_tuple(
                data.get("evidence_required", ()), "target.evidence_required"
            ),
            provenance=_text_tuple(
                data.get("provenance", ()), "target.provenance"
            ),
            gaps=_text_tuple(data.get("gaps", ()), "target.gaps", allow_empty=True),
            schema=str(data.get("schema", TARGET_SCHEMA)),
        )


@dataclass(frozen=True)
class RelaxationRecord:
    """Declared loss class for a transfer mapping.

    ``unclassified`` is the honest default: retrieval has no target artifact or
    target test, so no stronger class may be inferred from a structural match.
    A classified record needs a basis, a matching target, target-level evidence,
    a target artifact and at least one target test.
    """

    classification: str = "unclassified"
    basis: str = DEFAULT_RELAXATION_BASIS
    evidence_level: str = "none"
    target: str = ""
    schema: str = RELAXATION_SCHEMA

    def validate(
        self,
        *,
        candidate_target: str | None = None,
        artifact: Mapping[str, Any] | None = None,
        tests: tuple[str, ...] = (),
    ) -> None:
        if self.schema != RELAXATION_SCHEMA:
            raise ValueError(
                f"relaxation.schema must be {RELAXATION_SCHEMA!r}: {self.schema!r}"
            )
        if self.classification not in RELAXATION_CLASSES:
            raise ValueError(
                "relaxation.classification must be one of "
                f"{sorted(RELAXATION_CLASSES)}: {self.classification!r}"
            )
        _text(self.basis, "relaxation.basis")
        if self.evidence_level not in RELAXATION_EVIDENCE_LEVELS:
            raise ValueError(
                "relaxation.evidence_level must be one of "
                f"{sorted(RELAXATION_EVIDENCE_LEVELS)}: {self.evidence_level!r}"
            )
        if self.classification == "unclassified":
            if (
                self.evidence_level in TARGET_RELAXATION_EVIDENCE
                and not self.target
            ):
                raise ValueError(
                    "target-level relaxation evidence requires relaxation.target"
                )
            return
        if self.evidence_level not in TARGET_RELAXATION_EVIDENCE:
            raise ValueError(
                "a classified relaxation requires target-simulated or "
                "target-integrated evidence"
            )
        if not self.target:
            raise ValueError(
                "a classified relaxation requires a declared relaxation.target"
            )
        if candidate_target is not None and self.target != candidate_target:
            raise ValueError(
                f"relaxation.target {self.target!r} does not match transfer.target "
                f"{candidate_target!r}"
            )
        if artifact is None or not tests:
            raise ValueError(
                "a classified relaxation requires a target artifact and at "
                "least one target test"
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "classification": self.classification,
            "basis": self.basis,
            "evidence_level": self.evidence_level,
            "target": self.target,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RelaxationRecord":
        if not isinstance(data, Mapping):
            raise ValueError("relaxation record must be a mapping")
        return cls(
            classification=str(data.get("classification", "unclassified")),
            basis=str(data.get("basis", DEFAULT_RELAXATION_BASIS)),
            evidence_level=str(data.get("evidence_level", "none")),
            target=str(data.get("target", "")),
            schema=str(data.get("schema", RELAXATION_SCHEMA)),
        )


@dataclass(frozen=True)
class TransferCandidate:
    """A proposed operation → mechanism → target mapping."""

    id: str
    operation: str
    mechanism: str
    source_domain: str
    target: str
    mapping: tuple[MappingStep, ...]
    preserved: tuple[str, ...]
    relaxed: tuple[str, ...]
    validity: tuple[str, ...]
    evidence_level: str
    tests: tuple[str, ...] = ()
    artifact: Mapping[str, Any] | None = None
    gaps: tuple[str, ...] = ()
    status: str = "candidate"
    provenance: tuple[str, ...] = ()
    rank: int | None = None
    relaxation: RelaxationRecord = field(default_factory=RelaxationRecord)
    schema: str = SCHEMA

    def validate(
        self,
        mechanism: MechanismCard | None = None,
        *,
        allow_undeclared: bool = False,
    ) -> None:
        if self.schema != SCHEMA:
            raise ValueError(f"transfer.schema must be {SCHEMA!r}: {self.schema!r}")
        _identifier(self.id, "transfer.id")
        _identifier(self.operation, "transfer.operation")
        _identifier(self.mechanism, "transfer.mechanism")
        _text(self.source_domain, "transfer.source_domain")
        _text(self.target, "transfer.target")
        if not self.mapping:
            raise ValueError("transfer.mapping must contain at least one step")
        for step in self.mapping:
            step.validate()
        _text_tuple(self.preserved, "transfer.preserved")
        _text_tuple(self.relaxed, "transfer.relaxed", allow_empty=True)
        _text_tuple(self.validity, "transfer.validity")
        if self.evidence_level not in EVIDENCE_LEVELS:
            raise ValueError(
                f"transfer.evidence_level must be one of {list(EVIDENCE_LEVELS)}: "
                f"{self.evidence_level!r}"
            )
        if self.status not in STATUSES:
            raise ValueError(
                f"transfer.status must be one of {sorted(STATUSES)}: {self.status!r}"
            )
        _text_tuple(self.tests, "transfer.tests", allow_empty=True)
        _text_tuple(self.gaps, "transfer.gaps", allow_empty=True)
        _text_tuple(self.provenance, "transfer.provenance")
        if self.rank is not None and (not isinstance(self.rank, int) or self.rank < 0):
            raise ValueError("transfer.rank must be a nonnegative integer or null")
        if self.artifact is not None:
            if not isinstance(self.artifact, Mapping):
                raise ValueError("transfer.artifact must be a mapping or null")
            _text(self.artifact.get("kind"), "transfer.artifact.kind")
            if not (self.artifact.get("path") or self.artifact.get("description")):
                raise ValueError(
                    "transfer.artifact needs a path or description"
                )
        self.relaxation.validate(
            candidate_target=self.target,
            artifact=self.artifact,
            tests=self.tests,
        )
        requires_target_evidence = (
            self.status == "validated"
            or self.evidence_level in ("target-simulated", "target-integrated")
        )
        if requires_target_evidence and (self.artifact is None or not self.tests):
            raise ValueError(
                "target evidence requires a transfer artifact and at least one test"
            )
        if mechanism is not None:
            mechanism.validate()
            if mechanism.id != self.mechanism:
                raise ValueError(
                    f"transfer.mechanism {self.mechanism!r} does not match "
                    f"mechanism.id {mechanism.id!r}"
                )
            if (
                not allow_undeclared
                and self.operation not in mechanism.supported_operations
            ):
                raise ValueError(
                    f"mechanism {mechanism.id!r} does not support operation "
                    f"{self.operation!r}"
                )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "id": self.id,
            "operation": self.operation,
            "mechanism": self.mechanism,
            "source_domain": self.source_domain,
            "target": self.target,
            "mapping": [step.as_dict() for step in self.mapping],
            "preserved": list(self.preserved),
            "relaxed": list(self.relaxed),
            "relaxation": self.relaxation.as_dict(),
            "validity": list(self.validity),
            "evidence_level": self.evidence_level,
            "tests": list(self.tests),
            "artifact": dict(self.artifact) if self.artifact is not None else None,
            "gaps": list(self.gaps),
            "status": self.status,
            "provenance": list(self.provenance),
            "rank": self.rank,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TransferCandidate":
        if not isinstance(data, Mapping):
            raise ValueError("transfer candidate must be a mapping")
        mapping = tuple(
            MappingStep.from_dict(item) for item in data.get("mapping", ())
        )
        return cls(
            id=str(data.get("id", "")),
            operation=str(data.get("operation", "")),
            mechanism=str(data.get("mechanism", "")),
            source_domain=str(data.get("source_domain", "")),
            target=str(data.get("target", "")),
            mapping=mapping,
            preserved=_text_tuple(data.get("preserved", ()), "transfer.preserved"),
            relaxed=_text_tuple(
                data.get("relaxed", ()), "transfer.relaxed", allow_empty=True
            ),
            relaxation=RelaxationRecord.from_dict(data.get("relaxation", {})),
            validity=_text_tuple(data.get("validity", ()), "transfer.validity"),
            evidence_level=str(data.get("evidence_level", "")),
            tests=_text_tuple(data.get("tests", ()), "transfer.tests", allow_empty=True),
            artifact=data.get("artifact"),
            gaps=_text_tuple(data.get("gaps", ()), "transfer.gaps", allow_empty=True),
            status=str(data.get("status", "candidate")),
            provenance=_text_tuple(
                data.get("provenance", ()), "transfer.provenance"
            ),
            rank=data.get("rank"),
            schema=str(data.get("schema", SCHEMA)),
        )
