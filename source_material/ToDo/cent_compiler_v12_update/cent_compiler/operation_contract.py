"""Typed operation contracts for the Cent transfer compiler.

An operation contract is deliberately more than a formula string.  It records
the signature, reference semantics, tolerance, test vectors and target
constraints so that a transfer candidate has a declared thing to validate.

This module defines the ``cent-operation/1`` record only.  It does not claim
that every operation can be parsed or transferred.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping

SCHEMA = "cent-operation/1"

TEST_KINDS = frozenset({"exact", "interval", "numerical", "property"})
_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")


def _text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty text")
    return text


def _identifier(value: Any, field_name: str) -> str:
    text = _text(value, field_name)
    if not _ID_RE.fullmatch(text):
        raise ValueError(
            f"{field_name} must match {_ID_RE.pattern!s}: {text!r}"
        )
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


def _mapping(value: Any, field_name: str, *, allow_empty: bool = True) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    result = {str(key): item for key, item in value.items()}
    if not result and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return result


@dataclass(frozen=True)
class OperationTest:
    """One declared reference test for an operation contract."""

    id: str
    kind: str
    inputs: Mapping[str, Any]
    expected: Any
    tolerance: str = "0"
    provenance: tuple[str, ...] = ()
    note: str = ""

    def validate(self) -> None:
        _identifier(self.id, "test.id")
        if self.kind not in TEST_KINDS:
            raise ValueError(
                f"test.kind must be one of {sorted(TEST_KINDS)}: {self.kind!r}"
            )
        _mapping(self.inputs, "test.inputs")
        _text(self.tolerance, "test.tolerance")
        _text_tuple(self.provenance, "test.provenance")
        if not isinstance(self.expected, (str, int, bool, list, dict)):
            raise ValueError(
                "test.expected must be a JSON scalar, list or mapping; "
                "binary floats are not part of the schema"
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "inputs": dict(self.inputs),
            "expected": self.expected,
            "tolerance": self.tolerance,
            "provenance": list(self.provenance),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OperationTest":
        if not isinstance(data, Mapping):
            raise ValueError("operation test must be a mapping")
        if "expected" not in data:
            raise ValueError("operation test.expected is required")
        return cls(
            id=str(data.get("id", "")),
            kind=str(data.get("kind", "")),
            inputs=_mapping(data.get("inputs"), "test.inputs"),
            expected=data["expected"],
            tolerance=str(data.get("tolerance", "0")),
            provenance=_text_tuple(data.get("provenance", ()), "test.provenance"),
            note=str(data.get("note", "")),
        )


@dataclass(frozen=True)
class OperationContract:
    """A typed computational operation and its reference validation surface."""

    id: str
    name: str
    signature: Mapping[str, Any]
    semantics: str
    reference: Mapping[str, Any]
    tolerance: str
    tests: tuple[OperationTest, ...]
    target_constraints: Mapping[str, Any] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()
    schema: str = SCHEMA

    def validate(self) -> None:
        if self.schema != SCHEMA:
            raise ValueError(f"operation.schema must be {SCHEMA!r}: {self.schema!r}")
        _identifier(self.id, "operation.id")
        _text(self.name, "operation.name")
        signature = _mapping(self.signature, "operation.signature", allow_empty=False)
        for key in ("inputs", "outputs"):
            _mapping(signature.get(key), f"operation.signature.{key}", allow_empty=False)
        _text(self.semantics, "operation.semantics")
        reference = _mapping(self.reference, "operation.reference", allow_empty=False)
        _text(reference.get("kind"), "operation.reference.kind")
        if not any(reference.get(key) for key in ("expression", "description", "path")):
            raise ValueError(
                "operation.reference needs an expression, description or path"
            )
        _text(self.tolerance, "operation.tolerance")
        if not self.tests:
            raise ValueError("operation.tests must contain at least one test")
        if len({test.id for test in self.tests}) != len(self.tests):
            raise ValueError("operation.tests must have unique ids")
        for test in self.tests:
            test.validate()
        _mapping(self.target_constraints, "operation.target_constraints")
        _text_tuple(self.provenance, "operation.provenance")
        _text_tuple(self.gaps, "operation.gaps", allow_empty=True)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "id": self.id,
            "name": self.name,
            "signature": dict(self.signature),
            "semantics": self.semantics,
            "reference": dict(self.reference),
            "tolerance": self.tolerance,
            "tests": [test.as_dict() for test in self.tests],
            "target_constraints": dict(self.target_constraints),
            "provenance": list(self.provenance),
            "gaps": list(self.gaps),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "OperationContract":
        if not isinstance(data, Mapping):
            raise ValueError("operation contract must be a mapping")
        tests = tuple(
            OperationTest.from_dict(item)
            for item in data.get("tests", ())
        )
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            signature=_mapping(data.get("signature"), "operation.signature"),
            semantics=str(data.get("semantics", "")),
            reference=_mapping(data.get("reference"), "operation.reference"),
            tolerance=str(data.get("tolerance", "")),
            tests=tests,
            target_constraints=_mapping(
                data.get("target_constraints", {}),
                "operation.target_constraints",
            ),
            provenance=_text_tuple(
                data.get("provenance", ()), "operation.provenance"
            ),
            gaps=_text_tuple(data.get("gaps", ()), "operation.gaps", allow_empty=True),
            schema=str(data.get("schema", SCHEMA)),
        )

    @classmethod
    def from_json(cls, text: str) -> "OperationContract":
        return cls.from_dict(json.loads(text))

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True)
