"""Executable mapping operators for the Cent transfer compiler.

An operator is the ``Τ`` part of the R2 split: it is not another mechanism card
and it does not claim a target result.  Each operator declares a precondition,
a law, and a concrete ``check``/``apply`` pair over a small mapping model.  The
model is deliberately substrate-neutral so a mechanism card can be derived from
a shared principle without importing a target adapter.

``apply`` is total only where ``check`` is true.  Calling it on an unsupported
model raises ``ValueError`` instead of silently preserving an undeclared step.
"""
from __future__ import annotations

import numbers
from dataclasses import dataclass
from typing import Any, Mapping

MAPPING_KINDS = frozenset(
    {
        "variable",
        "scale",
        "duality",
        "state",
        "sampling",
        "quantization",
        "feedback",
        "composition",
        "correspondence",
    }
)


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


def _number(value: Any) -> bool:
    return isinstance(value, numbers.Number) and not isinstance(value, bool)


@dataclass(frozen=True)
class MappingOperator:
    """One declared, executable transfer-mapping step."""

    id: str
    precondition: str
    law: str
    kind: str
    gaps: tuple[str, ...] = ()

    def validate(self) -> None:
        _text(self.id, "operator.id")
        _text(self.precondition, "operator.precondition")
        _text(self.law, "operator.law")
        if self.kind not in MAPPING_KINDS:
            raise ValueError(f"operator.kind must be one of {sorted(MAPPING_KINDS)}")
        _texts(self.gaps, "operator.gaps", allow_empty=True)

    def check(self, model: Mapping[str, Any]) -> bool:
        """Return whether this operator can legally act on ``model``."""
        if not isinstance(model, Mapping):
            return False
        if self.id == "identity":
            return bool(str(model.get("operation") or "").strip())
        if self.id == "scale-offset":
            return (
                _number(model.get("scale"))
                and _number(model.get("offset"))
                and bool(str(model.get("target_units") or "").strip())
            )
        if self.id == "effort-flow-duality":
            dual = model.get("duality")
            return (
                isinstance(dual, Mapping)
                and all(
                    bool(str(dual.get(key) or "").strip())
                    for key in (
                        "source_effort",
                        "source_flow",
                        "target_effort",
                        "target_flow",
                    )
                )
                and bool(str(model.get("target_domain") or "").strip())
                and bool(str(model.get("target_carrier") or "").strip())
            )
        if self.id == "state-transform":
            return model.get("stateful") is True and "state" in model
        if self.id == "sampling-quantization":
            chain = tuple(model.get("primitive_chain") or ())
            levels = model.get("levels")
            return "quantize" in chain and isinstance(levels, int) and levels > 1
        if self.id == "feedback-equivalence":
            return model.get("feedback") is True
        if self.id == "composition":
            chain = tuple(model.get("primitive_chain") or ())
            return len(chain) > 1
        return False

    def apply(self, model: Mapping[str, Any]) -> dict[str, Any]:
        """Apply the operator, or raise if its precondition is not met."""
        if not isinstance(model, Mapping):
            raise ValueError("operator model must be a mapping")
        if not self.check(model):
            raise ValueError(
                f"operator {self.id!r} precondition is not met: {self.precondition}"
            )
        out = dict(model)
        if self.id == "identity":
            out["identity_applied"] = True
        elif self.id == "scale-offset":
            out["scaled"] = True
            out["carrier"] = model["target_carrier"]
            out["applied_scale"] = model["scale"]
            out["applied_offset"] = model["offset"]
        elif self.id == "effort-flow-duality":
            dual = model["duality"]
            out["domain"] = model["target_domain"]
            out["carrier"] = model["target_carrier"]
            out["effort"] = dual["target_effort"]
            out["flow"] = dual["target_flow"]
            out["duality_applied"] = True
        elif self.id == "state-transform":
            transform = model.get("state_transform")
            state = model["state"]
            out["target_state"] = transform(state) if callable(transform) else state
        elif self.id == "sampling-quantization":
            levels = model["levels"]
            out["code_width"] = max(1, (levels - 1).bit_length())
            out["quantization_applied"] = True
        elif self.id == "feedback-equivalence":
            out["feedback_preserved"] = True
        elif self.id == "composition":
            out["composition"] = tuple(model["primitive_chain"])
            out["composition_applied"] = True
        return out

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "precondition": self.precondition,
            "law": self.law,
            "kind": self.kind,
            "gaps": list(self.gaps),
            "executable": True,
        }


MAPPING_OPERATORS = (
    MappingOperator(
        "identity",
        "a typed operation contract and target profile are declared",
        "preserve the typed operation semantics; execution evidence is recorded separately",
        "correspondence",
        ("target execution is not established by retrieval alone",),
    ),
    MappingOperator(
        "scale-offset",
        "the target declares physical units, scale and offset",
        "apply the declared target scale and offset",
        "scale",
        ("target units and offset are not declared",),
    ),
    MappingOperator(
        "effort-flow-duality",
        "the target declares an effort/flow pair and a power-conjugate map",
        "map source effort/flow quantities through the declared dual pair",
        "duality",
        ("target effort/flow pair is not declared",),
    ),
    MappingOperator(
        "state-transform",
        "the seeded mechanism is stateful",
        "carry the mechanism state through an explicit target state transform",
        "state",
        ("target state representation is not declared",),
    ),
    MappingOperator(
        "sampling-quantization",
        "the mechanism contains a quantize primitive",
        "preserve the declared quantization law and code reconstruction",
        "quantization",
        ("target code width and reconstruction are not declared",),
    ),
    MappingOperator(
        "feedback-equivalence",
        "the mechanism declares feedback",
        "preserve the feedback topology; target loop dynamics remain undeclared",
        "feedback",
        ("target loop dynamics and stability are not declared",),
    ),
    MappingOperator(
        "composition",
        "the mechanism primitive chain has more than one step",
        "preserve the declared primitive composition order",
        "composition",
        ("target composition semantics are not declared",),
    ),
)

OPERATOR_BY_ID = {operator.id: operator for operator in MAPPING_OPERATORS}
if len(OPERATOR_BY_ID) != len(MAPPING_OPERATORS):
    raise RuntimeError("mapping operator table contains duplicate ids")
for _operator in MAPPING_OPERATORS:
    _operator.validate()
